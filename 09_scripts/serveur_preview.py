"""
serveur_preview.py
------------------
Serveur de prévisualisation du bulletin dans le navigateur.

Surveille tous les fichiers Markdown et YAML du workspace.
Dès qu'un fichier est modifié :
  1. L'assembleur est relancé automatiquement.
  2. La page HTML est régénérée.
  3. Le navigateur est rafraîchi sans intervention manuelle.

Usage :
    python 09_scripts/serveur_preview.py

Ouvrir ensuite dans le navigateur :
    http://localhost:8765

Arrêt : Ctrl+C dans le terminal.

Dépendances :
    pip install markdown watchdog
"""

import http.server
import threading
import subprocess
import pathlib
import queue
import json
import os
import re
import sys
import webbrowser
import time
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

try:
    import markdown
    from markdown.extensions.toc import TocExtension
except ImportError:
    print("[ERREUR] Module 'markdown' requis.\n"
          "         Installer avec : pip install markdown")
    sys.exit(1)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("[ERREUR] Module 'watchdog' requis.\n"
          "         Installer avec : pip install watchdog")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Chemins

SCRIPT_DIR    = pathlib.Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent
ASSEMBLED     = WORKSPACE_DIR / "10_output" / "bulletin_complet_travail.md"
CSS_FILE      = SCRIPT_DIR / "preview.css"
ASSEMBLER     = SCRIPT_DIR / "assembler_markdown.py"
REGIME_VISUALIZER = SCRIPT_DIR / "visualiser_regimes.py"
REGIME_DASHBOARD  = WORKSPACE_DIR / "10_output" / "dashboard_regimes.html"
DASHBOARD_SETTINGS_FILE = WORKSPACE_DIR / "10_output" / "dashboard_settings.json"
PORT          = 8765

# ---------------------------------------------------------------------------
# Cache partagé

_html_cache = "<p><em>Chargement en cours…</em></p>"
_html_lock  = threading.Lock()
_clients    = []
_clients_lock = threading.Lock()


def notify_clients():
    """Envoie un signal de rechargement à tous les navigateurs connectés."""
    with _clients_lock:
        for q in _clients:
            try:
                q.put_nowait("reload")
            except queue.Full:
                pass


def run_assembler():
    """Relance l'assembleur Markdown. Retourne True si succès."""
    result = subprocess.run(
        [sys.executable, str(ASSEMBLER)],
        capture_output=True,
        cwd=str(WORKSPACE_DIR),
        encoding="cp1252",
        errors="replace",
    )
    if result.returncode != 0:
        print(f"[ASSEMBLEUR] Erreur :\n{result.stderr.strip()}")
        return False
    print("[ASSEMBLEUR] OK")
    return True


def run_regime_dashboard():
    """Régénère le tableau de bord des régimes si le générateur est disponible."""
    if not REGIME_VISUALIZER.exists():
        return False
    result = subprocess.run(
        [sys.executable, str(REGIME_VISUALIZER)],
        capture_output=True,
        cwd=str(WORKSPACE_DIR),
        encoding="cp1252",
        errors="replace",
    )
    if result.returncode != 0:
        print(f"[DASHBOARD] Erreur :\n{result.stderr.strip()}")
        return False
    print("[DASHBOARD] OK")
    return True


# ---------------------------------------------------------------------------
# Indicateurs de statut — code couleur validation

STATUS_CLASSES = {
    'brouillon': ('status-brouillon', 'Brouillon'),
    'à revoir':  ('status-arevoir',   'À revoir'),
    'revu':      ('status-revu',      'Revu'),
    'validé':    ('status-valide',    'Validé'),
}


def build_status_map(md_text: str) -> dict:
    """Construit {texte_titre: (css_class, label)} en lisant les NOTE_INTERNE.

    Gère deux formats :
      Statut : brouillon      (valeur sur la même ligne)
      Statut :                (valeur sur la ligne suivante)
      à revoir
    """
    mapping = {}
    lines = md_text.split('\n')
    i = 0
    while i < len(lines):
        m = re.match(r'^#{1,6}\s+(.+)$', lines[i])
        if m:
            heading_text = m.group(1).strip()
            statut = None
            in_note = False
            for j in range(i + 1, min(i + 40, len(lines))):
                if '<!-- NOTE_INTERNE' in lines[j]:
                    in_note = True
                    continue
                if not in_note:
                    continue
                if '-->' in lines[j]:
                    break
                sm = re.search(r'[Ss]tatut\s*:\s*(.*)', lines[j])
                if sm:
                    raw = sm.group(1).strip()
                    raw = re.sub(r'\s*-->.*$', '', raw).strip()
                    raw = re.sub(r'[\[\]]', '', raw).strip()
                    if '|' in raw or raw == '':
                        # Valeur sur la ligne suivante
                        if j + 1 < len(lines):
                            nxt = lines[j + 1].strip()
                            nxt = re.sub(r'\s*-->.*$', '', nxt).strip()
                            if nxt and '|' not in nxt:
                                raw = nxt
                    if raw and '|' not in raw:
                        statut = raw.lower()
                    break
            if statut and statut in STATUS_CLASSES:
                mapping[heading_text] = STATUS_CLASSES[statut]
        i += 1
    return mapping


def inject_status_dots_html(html: str, status_map: dict) -> str:
    """Injecte un point coloré dans les balises de titre HTML correspondantes."""
    for heading_text, (cls, label) in status_map.items():
        dot = (f'<span class="status-dot {cls}" title="{label}">&#9679;</span> ')
        pattern = r'(<h[1-6][^>]*>)(' + re.escape(heading_text) + r')(</h[1-6]>)'
        html = re.sub(
            pattern,
            lambda mo: mo.group(1) + dot + mo.group(2) + mo.group(3),
            html,
        )
    return html


def preprocess_md(md_text: str) -> str:
    """Prépare le markdown pour la prévisualisation :
    - Supprime le H1 initial (titre du document) — déjà affiché dans la topbar
    - Supprime les titres '## Texte rédigé' (conserve le contenu dessous)
    - Si le contenu est vide ou placeholder, affiche un bloc 'Texte à rédiger'
    - Supprime les blocs NOTE_INTERNE (<!-- NOTE_INTERNE ... -->)
    """
    # 1. Supprimer les blocs NOTE_INTERNE
    md_text = re.sub(r'<!--\s*NOTE_INTERNE.*?-->', '', md_text, flags=re.DOTALL)

    # 2. Supprimer les commentaires de version (<!-- VERSION ... --> et <!-- Généré ... -->)
    md_text = re.sub(r'<!--[^>]*-->', '', md_text)

    # 3. Supprimer le premier H1 du document (titre du projet, déjà dans la topbar)
    md_text = re.sub(r'^\s*#\s+.+\n', '', md_text, count=1)

    # 4. Traiter les titres "## Texte rédigé"
    lines = md_text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^##\s+Texte\s+r[eé]dig[eé]\s*$', line, re.IGNORECASE):
            # Collecter le contenu jusqu'au prochain h1/h2
            i += 1
            content_lines = []
            while i < len(lines):
                if re.match(r'^#{1,2}\s+', lines[i]):
                    break
                content_lines.append(lines[i])
                i += 1
            # Vérifier si le contenu est vide ou placeholder
            content = '\n'.join(content_lines).strip()
            content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL).strip()
            is_empty = (
                not content_no_comments
                or len(content_no_comments) < 15
                or re.match(r'^[\[_*].*?(rédiger|à compléter|en cours).*?[\]_*]$',
                            content_no_comments, re.IGNORECASE)
            )
            if is_empty:
                result.append('\n<p class="a-rediger">&#9998; Texte à rédiger</p>\n')
            else:
                result.extend(content_lines)
            continue
        result.append(line)
        i += 1
    return '\n'.join(result)
    lines = md_text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^##\s+Texte\s+r[eé]dig[eé]\s*$', line, re.IGNORECASE):
            # Collecter le contenu jusqu'au prochain h1/h2
            i += 1
            content_lines = []
            while i < len(lines):
                if re.match(r'^#{1,2}\s+', lines[i]):
                    break
                content_lines.append(lines[i])
                i += 1
            # Vérifier si le contenu est vide ou placeholder
            content = '\n'.join(content_lines).strip()
            content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL).strip()
            is_empty = (
                not content_no_comments
                or len(content_no_comments) < 15
                or re.match(r'^[\[_*].*?(rédiger|à compléter|en cours).*?[\]_*]$',
                            content_no_comments, re.IGNORECASE)
            )
            if is_empty:
                result.append('\n<p class="a-rediger">&#9998; Texte à rédiger</p>\n')
            else:
                result.extend(content_lines)
            continue
        result.append(line)
        i += 1
    return '\n'.join(result)


def enrich_source_refs(html: str, md_text: str) -> str:
    """Pour chaque <a class="source-ref"> sans data-val-id,
    génère un id stable à partir du href et injecte data-val-id + data-val-file.
    Le val-file est déduit du fichier source Markdown via le href du lien.
    """
    import hashlib

    # Construire un mapping href -> fichier source MD
    # En cherchant chaque href dans les fichiers assemblés
    # On lit le build_config pour retrouver quel fichier contient chaque href
    href_to_file = {}
    try:
        import yaml
        cfg_path = WORKSPACE_DIR / "build_config.yml"
        if cfg_path.exists():
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8-sig"))
            for section in cfg.get("sections", []):
                for f in section.get("files", []):
                    fpath = WORKSPACE_DIR / f
                    if fpath.exists():
                        content = fpath.read_text(encoding="utf-8-sig")
                        for href in re.findall(r'href="(/files/[^"]+)"', content):
                            href_to_file.setdefault(href, f)
    except Exception:
        pass

    def add_val_attrs(m):
        tag = m.group(0)
        # Déjà enrichi
        if 'data-val-id' in tag:
            return tag
        # Extraire href
        href_m = re.search(r'href="([^"]+)"', tag)
        if not href_m:
            return tag
        href = href_m.group(1).split("?")[0]  # sans query string
        # Générer un id stable court
        val_id = "src-" + hashlib.md5(href.encode()).hexdigest()[:8]
        # Fichier source
        val_file = href_to_file.get(href, "")
        # Injecter avant la fermeture de la balise ouvrante
        inject = f' data-val-id="{val_id}" data-val-file="{val_file}" data-val-status="brouillon"'
        return tag[:-1] + inject + ">"

    return re.sub(r'<a\b[^>]*class="[^"]*source-ref[^"]*"[^>]*>', add_val_attrs, html)


def build_html() -> str:
    """Convertit le fichier assemblé en page HTML complète."""
    css = CSS_FILE.read_text(encoding="utf-8-sig") if CSS_FILE.exists() else ""

    if not ASSEMBLED.exists():
        md_text = (
            "# Fichier introuvable\n\n"
            "_Le fichier `10_output/bulletin_complet_travail.md` n'existe pas encore._\n\n"
            "Vérifiez que `build_config.yml` est correct et relancez l'assembleur."
        )
    else:
        md_text = ASSEMBLED.read_text(encoding="utf-8")

    status_map = build_status_map(md_text)
    md_preview = preprocess_md(md_text)
    md = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "md_in_html",
            TocExtension(title="", toc_depth=3),
        ]
    )
    body = md.convert(md_preview)
    toc  = md.toc  # HTML généré par l'extension toc
    body = inject_status_dots_html(body, status_map)
    body = enrich_source_refs(body, md_text)
    # Envelopper chaque <table> dans un div scrollable
    body = re.sub(r'(<table)', r'<div class="table-scroll">\1', body)
    body = re.sub(r'(</table>)', r'\1</div>', body)

    # Horodatage de la dernière mise à jour
    from datetime import datetime
    ts = datetime.now().strftime("%H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bulletin statistique RDC 2026 — Prévisualisation</title>
  <style>{css}</style>
</head>
<body class="with-topbar">

<div id="topbar">
  <div id="topbar-info">
    PRÉVISUALISATION — Deuxième Bulletin statistique de la protection sociale en RDC
    &nbsp;&nbsp;|&nbsp;&nbsp;
    Dernière mise à jour : {ts}
    &nbsp;&nbsp;|&nbsp;&nbsp;
    <span id="status">● En ligne</span>
  </div>
  <div id="topbar-actions">
    <a href="/dashboard" target="_blank" class="topbar-btn topbar-link"
       title="Ouvrir le tableau de bord interactif des régimes (ESS)">
      📊 Tableau de bord
    </a>
    <a href="/export" target="_blank" class="topbar-btn topbar-link"
       title="Générer et ouvrir un fichier HTML autonome pour relecture hors ligne">
      📤 Exporter HTML
    </a>
    <button type="button" id="export-pdf-btn" class="topbar-btn"
            title="Exporter la vue actuelle en PDF" onclick="exportPreviewPdf()">
      🖨️ Export PDF
    </button>
  </div>
</div>

<div id="sidebar">
  <div id="toc-header">Table des matières</div>
  {toc if toc else '<p style="padding:12px 18px;color:#667;font-size:12px;">Aucun titre détecté.</p>'}
</div>

<div id="main">
  <div id="content">
    {body}
  </div>
</div>

<div id="page-indicator">Page 1</div>

<script>
/* ------------------------------------------------------------------ */
/* 1. Auto-refresh via Server-Sent Events                              */
/* ------------------------------------------------------------------ */
const evtSource = new EventSource("/events");
evtSource.onmessage = function(e) {{
  if (e.data === "reload") window.location.reload();
}};
evtSource.onerror = function() {{
  const s = document.getElementById("status");
  if (s) {{ s.textContent = "● Déconnecté — relancer le serveur"; s.style.color = "#c00"; }}
}};

function exportPreviewPdf() {{
  const originalTitle = document.title;
  const now = new Date();
  const stamp = now.getFullYear()
    + "-" + String(now.getMonth() + 1).padStart(2, "0")
    + "-" + String(now.getDate()).padStart(2, "0");
  document.title = "bulletin_rdc_preview_" + stamp;
  window.print();
  setTimeout(function() {{ document.title = originalTitle; }}, 500);
}}

/* ------------------------------------------------------------------ */
/* 2. Sections repliables dans le contenu principal                    */
/*    Cliquer sur un titre replie/déplie tout son contenu.             */
/* ------------------------------------------------------------------ */
(function() {{
  function makeCollapsible(level) {{
    const content = document.getElementById("content");
    if (!content) return;
    Array.from(content.querySelectorAll("h" + level)).forEach(function(h) {{
      /* indicateur visuel */
      const tog = document.createElement("span");
      tog.className = "collapse-toggle";
      tog.innerHTML = "&#9660;";          /* ▼ */
      h.insertBefore(tog, h.firstChild);
      h.classList.add("collapsible-heading");

      /* collecter les éléments suivants jusqu'au prochain titre de niveau ≤ */
      const section = document.createElement("div");
      section.className = "collapsible-section";
      const toMove = [];
      let next = h.nextElementSibling;
      while (next) {{
        const tag = next.tagName || "";
        if (/^H[1-6]$/.test(tag) && parseInt(tag[1]) <= level) break;
        toMove.push(next);
        next = next.nextElementSibling;
      }}

      if (toMove.length > 0) {{
        h.parentNode.insertBefore(section, toMove[0]);
        toMove.forEach(function(el) {{ section.appendChild(el); }});
        h.addEventListener("click", function() {{
          const col = section.classList.toggle("collapsed");
          tog.innerHTML = col ? "&#9654;" : "&#9660;";  /* ▶ ou ▼ */
        }});
      }} else {{
        h.removeChild(tog);
        h.classList.remove("collapsible-heading");
      }}
    }});
  }}
  /* traiter du plus profond vers le plus haut pour respecter la hiérarchie */
  [4, 3, 2, 1].forEach(makeCollapsible);
}})();

/* ------------------------------------------------------------------ */
/* 3. TOC repliable dans la sidebar                                    */
/*    Cliquer sur la flèche replie/déplie les sous-entrées.            */
/* ------------------------------------------------------------------ */
(function() {{
  document.querySelectorAll("#sidebar .toc li").forEach(function(li) {{
    const sub  = li.querySelector(":scope > ul");
    if (!sub) return;
    const link = li.querySelector(":scope > a");
    if (!link) return;
    const tog = document.createElement("span");
    tog.className = "toc-toggle";
    tog.innerHTML = "&#9660;";           /* ▼ */
    link.insertBefore(tog, link.firstChild);
    tog.addEventListener("click", function(e) {{
      e.preventDefault();
      e.stopPropagation();
      const col = sub.classList.toggle("toc-collapsed");
      tog.innerHTML = col ? "&#9654;" : "&#9660;";
    }});
  }});
}})();

/* ------------------------------------------------------------------ */
/* 5. Numéro de page (simulé A4 ≈ 1123 px)                            */
/* ------------------------------------------------------------------ */
(function() {{
  const A4_PX   = 1123;   /* hauteur A4 à 96 dpi */
  const mainEl  = document.getElementById("main");
  const indic   = document.getElementById("page-indicator");
  if (!mainEl || !indic) return;

  function updatePage() {{
    const contentH = mainEl.scrollHeight;
    const total    = Math.max(1, Math.ceil(contentH / A4_PX));
    const current  = Math.min(total, Math.floor(mainEl.scrollTop / A4_PX) + 1);
    indic.textContent = "Page\u00a0" + current + "\u00a0/\u00a0" + total;
  }}

  mainEl.addEventListener("scroll", updatePage);
  updatePage();
}})();

/* ------------------------------------------------------------------ */
/* 4. Ancre active dans la sidebar au scroll                           */
/* ------------------------------------------------------------------ */
const allHeadings = document.querySelectorAll("h1[id], h2[id], h3[id]");
const tocLinks    = document.querySelectorAll("#sidebar .toc a");

function onScroll() {{
  let current = "";
  allHeadings.forEach(function(h) {{
    if (window.scrollY + 80 >= h.offsetTop) current = h.id;
  }});
  tocLinks.forEach(function(l) {{
    const active = l.getAttribute("href") === "#" + current;
    l.style.borderLeftColor = active ? "var(--couleur-accent)" : "transparent";
    l.style.color           = active ? "#fff" : "";
  }});
}}
document.getElementById("main").addEventListener("scroll", onScroll);

/* ------------------------------------------------------------------ */
/* 5. Tooltip flottant pour les annotations de source (.source-ref)   */
/* Délégation sur document pour survivre aux déplacements DOM         */
/* ------------------------------------------------------------------ */
(function() {{
  const tip = document.createElement("div");
  tip.id = "source-tooltip";
  tip.style.left = "-9999px";
  tip.style.top  = "-9999px";
  document.body.appendChild(tip);

  /* Ajouter target=_blank sur tous les liens source-ref
     et enrichir le href avec les paramètres de validation + contexte */
  document.querySelectorAll("a.source-ref").forEach(function(el) {{
    el.setAttribute("rel", "noopener noreferrer");
    const valId     = el.getAttribute("data-val-id");
    const valFile   = el.getAttribute("data-val-file");
    const valStatus = el.getAttribute("data-val-status") || "brouillon";

    /* Intercepter le clic pour enrichir l'URL avec contexte + val params */
    el.addEventListener("click", function(e) {{
      e.preventDefault();
      const href = (el.getAttribute("href") || "").split("?")[0];
      if (!href) return;

      /* Extraire la phrase complète du paragraphe parent */
      const para = el.closest("p, li, blockquote, td");
      const ctx     = para ? para.textContent.trim() : "";
      const anchor  = el.textContent.trim();  /* texte exact du lien */

      let params = "";
      if (valId)   params += "&val_id="     + encodeURIComponent(valId);
      if (valFile) params += "&val_file="   + encodeURIComponent(valFile);
      if (valStatus) params += "&val_status=" + encodeURIComponent(valStatus);
      if (ctx)     params += "&ctx="        + encodeURIComponent(ctx.substring(0, 400));
      if (anchor)  params += "&anchor="     + encodeURIComponent(anchor.substring(0, 200));

      window.open(href + "?" + params.replace(/^&/, ""), "_blank");
    }});
  }});

  var currentLink = null;

  document.addEventListener("mouseover", function(e) {{
    const el = e.target.closest("a.source-ref");
    if (!el) return;
    currentLink = el;
    const label = el.getAttribute("title") || "";
    if (!label) return;
    tip.textContent = label;
    tip.style.opacity = "1";
  }});

  document.addEventListener("mousemove", function(e) {{
    if (tip.style.opacity !== "1") return;
    let x = e.clientX + 14;
    let y = e.clientY + 18;
    if (x + 460 > window.innerWidth) x = e.clientX - 460;
    if (y + 80  > window.innerHeight) y = e.clientY - 50;
    tip.style.left = x + "px";
    tip.style.top  = y + "px";
  }});

  document.addEventListener("mouseout", function(e) {{
    /* Masquer seulement si on quitte vraiment le lien (pas vers un enfant) */
    const el = e.target.closest("a.source-ref");
    if (!el) return;
    const to = e.relatedTarget;
    if (to && el.contains(to)) return;
    tip.style.opacity = "0";
    currentLink = null;
  }});
}})();

/* ------------------------------------------------------------------ */
/* 6. Légende des statuts de validation                                */
/* ------------------------------------------------------------------ */
(function() {{
  const legend = document.createElement("div");
  legend.id = "status-legend";
  const items = [
    ["#d42b2b", "Structure initiale"],
    ["#e07820", "Notes développées"],
    ["#c8a800", "Rédigé"],
    ["#2e78c8", "Révisé"],
    ["#111111", "Validé"],
  ];
  let inner = '<div class="legend-title">Statut des sections</div>';
  items.forEach(function(item) {{
    inner += '<div>'
      + '<span class="l-dot" style="background:' + item[0] + '"></span>'
      + item[1]
      + '</div>';
  }});
  legend.innerHTML = inner;
  document.body.appendChild(legend);
}})();
/* ------------------------------------------------------------------ */
/* 7. Validation interactive des éléments inline (.val, .val-cite…)  */
/* ------------------------------------------------------------------ */
(function() {{
  const STATUS_ORDER  = [
    'brouillon', 'à revoir', 'revu', 'validé'
  ];
  const STATUS_COLORS = {{
    'brouillon': '#d42b2b', 'à revoir': '#e07820',
    'revu': '#2e78c8', 'validé': '#111111'
  }};
  const STATUS_DOT_CLASSES = {{
    'brouillon': 'status-brouillon', 'à revoir': 'status-arevoir',
    'revu': 'status-revu', 'validé': 'status-valide'
  }};

  function rankOf(status) {{
    const idx = STATUS_ORDER.indexOf(status);
    return idx === -1 ? 0 : idx;
  }}

  /* — Cascade : recalcule les dots des titres à partir des éléments [data-val-id] — */
  function updateCascade() {{
    const content = document.getElementById('content');
    if (!content) return;

    function minRankIn(container) {{
      const vals = container.querySelectorAll('[data-val-id]');
      if (!vals.length) return -1;
      let min = STATUS_ORDER.length - 1;
      vals.forEach(function(v) {{
        const s = v.getAttribute('data-val-status') || 'brouillon';
        const r = rankOf(s);
        if (r < min) min = r;
      }});
      return min;
    }}

    function updateDot(heading, rank) {{
      const dot = heading.querySelector('.status-dot');
      if (!dot) return;
      const newStatus = STATUS_ORDER[rank] || 'brouillon';
      Object.values(STATUS_DOT_CLASSES).forEach(function(cls) {{
        dot.classList.remove(cls);
      }});
      dot.classList.add(STATUS_DOT_CLASSES[newStatus] || 'status-brouillon');
      dot.setAttribute('title', newStatus);
    }}

    /* Pour chaque niveau de titre, chercher la section repliable suivante */
    [1, 2, 3, 4].forEach(function(level) {{
      content.querySelectorAll('h' + level).forEach(function(h) {{
        /* La section repliable créée par le JS collapse vient après le titre */
        let sec = h.nextElementSibling;
        while (sec && !sec.classList.contains('collapsible-section')) {{
          sec = sec.nextElementSibling;
        }}
        if (!sec) return;
        const rank = minRankIn(sec);
        if (rank >= 0) updateDot(h, rank);
      }});
    }});
  }}

  /* — Popup — */
  const popup = document.createElement('div');
  popup.id = 'val-popup';
  document.body.appendChild(popup);

  let currentEl      = null;
  let selectedStatus = null;
  let originalStatus = null;

  function openPopup(el, clientX, clientY) {{
    currentEl      = el;
    originalStatus = el.getAttribute('data-val-status') || 'brouillon';
    selectedStatus = originalStatus;
    const text = (el.textContent || '').trim().substring(0, 45);

    /* — Barre de segments toggle — */
    let segs = '';
    STATUS_ORDER.forEach(function(s) {{
      const col        = STATUS_COLORS[s] || '#999';
      const isCurrent  = s === originalStatus ? ' current' : '';
      const isActive   = s === originalStatus ? ' active'  : '';
      segs += '<button class="vp-seg' + isCurrent + isActive + '" data-status="' + s + '">'
        + '<span class="vp-seg-dot" style="background:' + col + '"></span>'
        + '<span class="vp-seg-label">' + s + '</span>'
        + '</button>';
    }});

    popup.innerHTML =
      '<div class="vp-title">Modifier le statut</div>'
      + '<div class="vp-label" title="' + text + '">' + (text || '(élément)') + '…</div>'
      + '<div class="vp-toggle-bar">' + segs + '</div>'
      + '<div class="vp-actions">'
      + '<button class="vp-btn cancel">Annuler</button>'
      + '<button class="vp-btn confirm" disabled>Enregistrer</button>'
      + '</div>';

    /* Positionnement */
    popup.classList.add('open');
    const pw = popup.offsetWidth  || 340;
    const ph = popup.offsetHeight || 160;
    let px = clientX + 12, py = clientY + 12;
    if (px + pw > window.innerWidth  - 8) px = clientX - pw - 12;
    if (py + ph > window.innerHeight - 8) py = clientY - ph - 12;
    popup.style.left = Math.max(8, px) + 'px';
    popup.style.top  = Math.max(8, py) + 'px';

    /* Clics sur les segments */
    const confirmBtn = popup.querySelector('.confirm');
    popup.querySelectorAll('.vp-seg').forEach(function(seg) {{
      seg.addEventListener('click', function() {{
        popup.querySelectorAll('.vp-seg').forEach(function(s) {{ s.classList.remove('active'); }});
        seg.classList.add('active');
        selectedStatus = seg.getAttribute('data-status');
        /* Activer Enregistrer uniquement si l'état a changé */
        confirmBtn.disabled = (selectedStatus === originalStatus);
      }});
    }});

    popup.querySelector('.cancel').addEventListener('click', closePopup);
    popup.querySelector('.confirm').addEventListener('click', function() {{
      if (!this.disabled) {{
        submitValidation(currentEl, selectedStatus);
      }}
    }});
  }}

  function closePopup() {{
    popup.classList.remove('open');
    currentEl = null;
  }}

  function submitValidation(el, newStatus) {{
    const file = el.getAttribute('data-val-file') || '';
    const id   = el.getAttribute('data-val-id')   || '';
    if (!file || !id) {{
      alert('Attributs data-val-file ou data-val-id manquants sur cet élément.');
      closePopup();
      return;
    }}
    fetch('/validate', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{file: file, id: id, status: newStatus}})
    }}).then(function(r) {{
      if (r.ok) {{
        el.setAttribute('data-val-status', newStatus);
        closePopup();
        updateCascade();
      }} else {{
        r.text().then(function(t) {{ alert('Erreur serveur : ' + t); }});
        closePopup();
      }}
    }}).catch(function() {{
      alert('Impossible de contacter le serveur de prévisualisation.');
      closePopup();
    }});
  }}

  /* Attacher les gestionnaires de clic droit à tous les éléments annotés */
  document.querySelectorAll('[data-val-id]').forEach(function(el) {{
    el.addEventListener('contextmenu', function(e) {{
      e.preventDefault();
      e.stopPropagation();
      openPopup(el, e.clientX, e.clientY);
    }});
  }});

  /* Fermer le popup si clic gauche en dehors */
  document.addEventListener('click', function(e) {{
    if (popup.classList.contains('open') && !popup.contains(e.target)) {{
      closePopup();
    }}
  }});

  /* Lancer la cascade initiale après que les sections repliables soient créées */
  setTimeout(updateCascade, 100);
}})();
</script>

</body>
</html>"""
    return html


def update_val_element_status(content: str, elem_id: str, new_status: str):
    """Met à jour data-val-status="..." pour l'élément avec data-val-id=elem_id.

    Retourne le contenu modifié, ou None si l'élément est introuvable.
    """
    # Trouver la balise ouvrante qui contient data-val-id="<elem_id>"
    tag_pattern = re.compile(
        r'<[a-zA-Z]+\b[^>]*\bdata-val-id="' + re.escape(elem_id) + r'"[^>]*>',
        re.DOTALL,
    )
    m = tag_pattern.search(content)
    if not m:
        return None

    old_tag = m.group(0)
    # Vérifier que l'attribut est présent avant de tenter le remplacement
    if 'data-val-status=' not in old_tag:
        return None  # Attribut absent dans la balise

    # Remplacer data-val-status dans la balise trouvée
    # Note : pas de \b car le nom d'attribut contient des tirets (non-word chars)
    new_tag = re.sub(
        r'data-val-status="[^"]*"',
        f'data-val-status="{new_status}"',
        old_tag,
    )
    # Retourner le contenu (même si la valeur est identique — no-op idempotent)
    return content[: m.start()] + new_tag + content[m.end() :]


# ---------------------------------------------------------------------------
# Gestion du démarrage : libération du port et contrôle du navigateur

def kill_port(port: int) -> bool:
    """Termine tout processus qui écoute sur le port donné.

    Retourne True si au moins un processus a été tué (= relance),
    False si le port était libre (= premier démarrage).
    """
    killed = False
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            encoding="cp1252",
            errors="replace",
        )
        my_pid = str(os.getpid())
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                pid = parts[-1]
                if pid.isdigit() and pid != my_pid:
                    subprocess.run(
                        ["taskkill", "/PID", pid, "/F"],
                        capture_output=True,
                    )
                    print(f"[INIT] Ancien processus {pid} sur le port {port} terminé.")
                    killed = True
    except Exception as exc:
        print(f"[INIT] Avertissement : impossible de vérifier le port {port} : {exc}")
    if killed:
        time.sleep(1)  # Laisser le port se libérer
    return killed


def rebuild(source: str = ""):
    """Reconstruit la page : assembleur + HTML + notification navigateurs."""
    global _html_cache
    if source:
        print(f"[WATCHER] Modification détectée : {source}")
    run_assembler()
    run_regime_dashboard()
    html = build_html()
    with _html_lock:
        _html_cache = html
    notify_clients()
    print("[PREVIEW] Page mise à jour")


# ---------------------------------------------------------------------------
# Watchdog — surveillance des fichiers

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self._timer = None
        self._lock  = threading.Lock()

    def on_modified(self, event):
        path = pathlib.Path(event.src_path)
        # Ignorer dossiers, fichiers de sortie et types non pertinents
        if event.is_directory:
            return
        if "10_output" in str(path):
            return
        if path.suffix not in (".md", ".yml", ".yaml", ".css", ".py"):
            return
        # Debounce : déclencher seulement si pas de modif depuis 1 s
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(1.0, rebuild, args=[path.name])
            self._timer.start()


# ---------------------------------------------------------------------------
# Serveur HTTP

class PreviewHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Silencer les logs HTTP

    def handle_error(self, request, client_address):
        pass  # Silencer les erreurs de connexion Windows (WinError 10053 etc.)

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError):
            pass

    def do_GET(self):
        if self.path == "/":
            self._serve_html()
        elif self.path == "/events":
            self._serve_sse()
        elif self.path == "/dashboard":
            self._serve_dashboard()
        elif self.path in ("/export", "/export-notes"):
            self._handle_export(include_notes=(self.path == "/export-notes"))
        elif self.path == "/api/dashboard-settings":
            self._serve_dashboard_settings()
        elif self.path.startswith("/api/denom/"):
            self._serve_denom_api()
        elif self.path.startswith("/files/"):
            self._serve_file()
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_dashboard_settings(self):
        payload = {"oddDecisions": {}}
        if DASHBOARD_SETTINGS_FILE.exists():
            try:
                raw = DASHBOARD_SETTINGS_FILE.read_text(encoding="utf-8")
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    odd = parsed.get("oddDecisions")
                    payload["oddDecisions"] = odd if isinstance(odd, dict) else {}
            except (OSError, json.JSONDecodeError):
                payload = {"oddDecisions": {}}

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_denom_api(self):
        parsed = urlparse(self.path)
        route = parsed.path
        qs = parse_qs(parsed.query)

        if route == "/api/denom/wpp":
            year = qs.get("year", [""])[0]
            if not re.fullmatch(r"\d{4}", year):
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(b'{"error":"Parametre year invalide"}')
                return
            target_url = f"https://www.populationpyramid.net/api/pp/180/{year}/"
        elif route == "/api/denom/ilo":
            target_url = (
                "https://rplumber.ilo.org/data/indicator/"
                "?id=EMP_TEMP_SEX_AGE_NB_A&ref_area=COD&sex=SEX_T"
                "&classif1=AGE_AGGREGATE_TOTAL&time_from=2000&time_to=2030"
                "&type=label&decimals=0"
            )
        else:
            self.send_response(404)
            self.end_headers()
            return

        req = Request(
            target_url,
            headers={
                "User-Agent": "RDC-Bulletin-Preview/1.0",
                "Accept": "application/json,text/plain,*/*",
            },
            method="GET",
        )
        try:
            with urlopen(req, timeout=25) as resp:
                body = resp.read()
                status = getattr(resp, "status", 200)
                content_type = resp.headers.get("Content-Type", "application/json")
        except HTTPError as err:
            status = err.code if err.code else 502
            body = err.read() if hasattr(err, "read") else b""
            if not body:
                body = json.dumps({"error": f"Upstream HTTP {status}"}).encode("utf-8")
            content_type = err.headers.get("Content-Type", "application/json") if err.headers else "application/json"
        except URLError as err:
            status = 502
            body = json.dumps({"error": f"Upstream indisponible: {err.reason}"}).encode("utf-8")
            content_type = "application/json"

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/validate":
            self._handle_validate()
        elif self.path == "/api/dashboard-settings":
            self._handle_dashboard_settings()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_dashboard_settings(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            try:
                body_str = body.decode("utf-8")
            except UnicodeDecodeError:
                body_str = body.decode("latin-1")
            data = json.loads(body_str)
            odd_decisions = data.get("oddDecisions", {})
            if not isinstance(odd_decisions, dict):
                raise ValueError("oddDecisions doit être un objet")
        except (json.JSONDecodeError, ValueError):
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Corps JSON invalide. Champ requis : oddDecisions (objet)")
            return

        DASHBOARD_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {"oddDecisions": odd_decisions}
        try:
            DASHBOARD_SETTINGS_FILE.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Impossible d'ecrire dashboard_settings.json")
            return

        response_body = json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(response_body)

    def _handle_validate(self):
        """Endpoint POST /validate — met à jour data-val-status dans le fichier source."""
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        try:
            # Décoder avec UTF-8, puis Latin-1 en repli (navigateurs Windows)
            try:
                body_str = body.decode("utf-8")
            except UnicodeDecodeError:
                body_str = body.decode("latin-1")
            data       = json.loads(body_str)
            file_rel   = data["file"]
            elem_id    = data["id"]
            new_status = data["status"]
        except (json.JSONDecodeError, KeyError):
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Corps JSON invalide. Champs requis : file, id, status")
            return

        # Contrôle de sécurité — interdire les traversées de répertoire
        try:
            target = (WORKSPACE_DIR / file_rel).resolve()
            if not str(target).startswith(str(WORKSPACE_DIR.resolve())):
                self.send_response(403)
                self.end_headers()
                return
            if not target.exists() or not target.is_file():
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Fichier source introuvable")
                return
        except Exception as exc:
            self.send_response(400)
            self.end_headers()
            return

        content     = target.read_text(encoding="utf-8")
        new_content = update_val_element_status(content, elem_id, new_status)
        if new_content is None:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                f"Élément data-val-id=\"{elem_id}\" introuvable dans {file_rel}".encode("utf-8")
            )
            return

        target.write_text(new_content, encoding="utf-8")
        response_body = json.dumps({"ok": True}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(response_body)
        print(f"[VALIDATE] {elem_id} → {new_status} ({file_rel})")

    def _handle_export(self, include_notes: bool = False):
        """GET /export ou /export-notes — Génère le HTML autonome et redirige vers lui."""
        from datetime import datetime as _dt
        exporter = SCRIPT_DIR / "exporter.py"
        stamp = _dt.now().strftime("%Y-%m-%d")
        label = "notes" if include_notes else "relecture"
        export_file = WORKSPACE_DIR / "10_output" / f"bulletin_{label}_{stamp}.html"

        if not exporter.exists():
            self.send_response(503)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"exporter.py introuvable dans 09_scripts/")
            return

        cmd = [sys.executable, str(exporter)]
        if include_notes:
            cmd.append("--notes")
        else:
            cmd.append("--html")

        result = subprocess.run(
            cmd,
            capture_output=True,
            cwd=str(WORKSPACE_DIR),
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0 or not export_file.exists():
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            err = (result.stderr or result.stdout or "Erreur inconnue")[:800]
            self.wfile.write(
                f"Erreur lors de la génération du fichier HTML :\n\n{err}".encode("utf-8")
            )
            return

        redirect_url = f"/files/10_output/bulletin_{label}_{stamp}.html"
        self.send_response(302)
        self.send_header("Location", redirect_url)
        self.end_headers()
        print(f"[EXPORT] Fichier généré : bulletin_{label}_{stamp}.html")

    def _serve_dashboard(self):
        """Sert le tableau de bord interactif depuis 10_output/dashboard_regimes.html."""
        dashboard = REGIME_DASHBOARD
        if REGIME_VISUALIZER.exists():
            try:
                if (not dashboard.exists() or REGIME_VISUALIZER.stat().st_mtime > dashboard.stat().st_mtime):
                    run_regime_dashboard()
            except OSError:
                pass
        if not dashboard.exists():
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<h2>Tableau de bord introuvable</h2>"
                b"<p>Lancer d'abord : <code>py 09_scripts/visualiser_regimes.py</code></p>"
            )
            return
        content = dashboard.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def _serve_file(self):
        """Sert un fichier du workspace via /files/<chemin_relatif>.

        Pour les fichiers .txt de sources (dans 06_sources/), génère une
        page HTML avec le contenu du fichier + liens vers la source web
        et vers le fichier local.
        """
        import mimetypes
        from urllib.parse import urlparse, parse_qs, unquote
        parsed   = urlparse(self.path)
        rel      = parsed.path[7:]  # retirer "/files/"
        qs       = parse_qs(parsed.query)
        val_id     = qs.get("val_id",     [""])[0]
        val_file   = qs.get("val_file",   [""])[0]
        val_status = qs.get("val_status", ["brouillon"])[0]
        ctx        = qs.get("ctx",        [""])[0]
        anchor     = qs.get("anchor",     [""])[0]
        try:
            target = (WORKSPACE_DIR / rel).resolve()
            if not str(target).startswith(str(WORKSPACE_DIR.resolve())):
                self.send_response(403)
                self.end_headers()
                return
            if not target.exists() or not target.is_file():
                self.send_response(404)
                self.end_headers()
                return

            # Fichiers .txt de sources → page HTML enrichie
            if target.suffix.lower() == ".txt" and "06_sources" in str(target):
                data = self._build_source_viewer(
                    target, rel, val_id, val_file, val_status, ctx, anchor
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
                return

            mime, _ = mimetypes.guess_type(str(target))
            mime = mime or "application/octet-stream"
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            if mime in ("application/pdf", "text/plain"):
                self.send_header("Content-Disposition", "inline")
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            print(f"[FICHIER] Erreur : {exc}")
            self.send_response(500)
            self.end_headers()

    @staticmethod
    def _build_source_viewer(path: pathlib.Path, rel: str,
                              val_id: str = "", val_file: str = "",
                              val_status: str = "brouillon",
                              ctx: str = "", anchor: str = "") -> str:
        """Génère une page HTML pour afficher un fichier source .txt."""
        content = path.read_text(encoding="utf-8-sig")

        # Extraire les métadonnées de l'en-tête
        meta = {}
        for line in content.splitlines():
            for key in ("SOURCE", "TITRE", "URL", "CONSULTÉ", "NIVEAU", "ÉDITEUR", "NOTE"):
                if line.startswith(key + " :") or line.startswith(key + ":"):
                    val = line.split(":", 1)[1].strip()
                    if val:
                        meta.setdefault(key, []).append(val)

        # Plusieurs URLs possibles (une par ligne "URL :")
        urls = meta.get("URL", [])
        source = meta.get("SOURCE", ["—"])[0]
        titre  = meta.get("TITRE",  ["—"])[0]
        niveau = meta.get("NIVEAU", ["—"])[0]
        consult = meta.get("CONSULTÉ", ["—"])[0]

        # Construire les badges de lien
        web_links = ""
        for url in urls:
            url = url.strip()
            if url.startswith("http"):
                web_links += (
                    f'<a href="{url}" target="_blank" rel="noopener" class="btn-link web">'
                    f'🌐 Ouvrir la source en ligne</a>\n'
                )

        # Chercher un PDF local du même nom que le .txt
        pdf_path = path.with_suffix(".pdf")
        pdf_rel  = rel.rsplit(".", 1)[0] + ".pdf"
        if pdf_path.exists():
            local_link = (
                f'<a href="/files/{pdf_rel}" target="_blank" class="btn-link local">'
                f'📄 Ouvrir le PDF local</a>'
            )
        elif urls:
            # Pas de PDF local → renvoyer vers l'URL web comme fallback
            first_url = next((u.strip() for u in urls if u.strip().startswith("http")), "")
            if first_url:
                local_link = (
                    f'<a href="{first_url}" target="_blank" rel="noopener" class="btn-link local">'
                    f'🔗 Accéder à la source (aucun PDF local)</a>'
                )
            else:
                local_link = ""
        else:
            local_link = (
                f'<span class="btn-link local" style="opacity:0.4;cursor:default">'
                f'📂 Aucun fichier local disponible</span>'
            )

        # Échapper le contenu texte pour HTML
        import html as html_lib
        content_escaped = html_lib.escape(content)

        # Bloc contexte (phrase source avec ancre surlignée)
        ctx_block = ""
        if ctx:
            # Surligner l'ancre dans le texte du contexte
            if anchor:
                import re as _re
                ctx_html = html_lib.escape(ctx)
                anchor_esc = html_lib.escape(anchor)
                # Remplacer la première occurrence (insensible à la casse)
                ctx_html = _re.sub(
                    '(' + _re.escape(anchor_esc) + ')',
                    r'<mark class="ctx-anchor">\1</mark>',
                    ctx_html, count=1, flags=_re.IGNORECASE
                )
            else:
                ctx_html = html_lib.escape(ctx)
            ctx_block = f"""
<div id="ctx-section">
  <div class="ctx-label">📝 Contexte d'utilisation dans le bulletin</div>
  <blockquote id="ctx-text">{ctx_html}</blockquote>
</div>"""

        # Bloc de validation (affiché seulement si val_id et val_file sont présents)
        STATUS_COLORS_PY = {
            "brouillon": "#d42b2b",
            "à revoir":  "#e07820",
            "revu":      "#2e78c8",
            "validé":    "#1a6e3c",
        }
        STATUS_ORDER_PY = ["brouillon", "à revoir", "revu", "validé"]

        val_block = ""
        if val_id and val_file:
            cur_col = STATUS_COLORS_PY.get(val_status, "#999")
            segs_html = ""
            for s in STATUS_ORDER_PY:
                col = STATUS_COLORS_PY.get(s, "#999")
                is_current = " current" if s == val_status else ""
                is_active  = " active"  if s == val_status else ""
                segs_html += (
                    f'<button class="vseg{is_current}{is_active}" data-status="{html_lib.escape(s)}">'
                    f'<span class="vseg-dot" style="background:{col}"></span>'
                    f'<span class="vseg-label">{html_lib.escape(s)}</span>'
                    f'</button>'
                )
            val_block = f"""
<div id="val-section">
  <div class="val-title">Statut de validation :
    <span id="val-current-badge" style="display:inline-block;padding:2px 10px;border-radius:10px;
                 background:{cur_col};color:#fff;font-size:11px;font-weight:700;
                 margin-left:6px;letter-spacing:0.5px">{html_lib.escape(val_status)}</span>
  </div>
  <div class="val-subtitle">Modifier le statut :</div>
  <div id="val-toggle-bar">{segs_html}</div>
  <div id="val-actions">
    <button id="val-save" onclick="saveValidation()" disabled>💾 Enregistrer</button>
    <span id="val-msg"></span>
  </div>
</div>
<script>
  var originalStatus = {json.dumps(val_status)};
  var selectedStatus = originalStatus;
  var saveBtn = document.getElementById('val-save');
  document.querySelectorAll('.vseg').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      document.querySelectorAll('.vseg').forEach(function(b) {{ b.classList.remove('active'); }});
      btn.classList.add('active');
      selectedStatus = btn.getAttribute('data-status');
      saveBtn.disabled = (selectedStatus === originalStatus);
    }});
  }});
  function saveValidation() {{
    if (saveBtn.disabled) return;
    var msg = document.getElementById('val-msg');
    msg.textContent = '…';
    fetch('/validate', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        file: {json.dumps(val_file)},
        id:   {json.dumps(val_id)},
        status: selectedStatus
      }})
    }})
    .then(function(r) {{ return r.text().then(function(t) {{ return {{ok: r.ok, text: t}}; }}); }})
    .then(function(res) {{
      if (res.ok) {{
        msg.style.color = '#1a6e3c';
        msg.textContent = '✓ Enregistré — ' + selectedStatus;
        originalStatus = selectedStatus;
        saveBtn.disabled = true;
        /* Mettre à jour le badge statut courant */
        var badge = document.getElementById('val-current-badge');
        if (badge) {{
          badge.textContent = selectedStatus;
        }}
        /* Marquer le segment comme état de référence */
        document.querySelectorAll('.vseg').forEach(function(b) {{ b.classList.remove('current'); }});
        document.querySelectorAll('.vseg').forEach(function(b) {{
          if (b.getAttribute('data-status') === selectedStatus) b.classList.add('current');
        }});
      }} else {{
        msg.style.color = '#d42b2b';
        msg.textContent = '✗ Erreur : ' + res.text;
      }}
    }})
    .catch(function(e) {{ msg.style.color='#d42b2b'; msg.textContent='✗ ' + e; }});
  }}
</script>"""

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_lib.escape(titre[:60])} — Source</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f2f1ec;
            color: #1c1c1c; min-height: 100vh; }}
    #header {{
      background: #1a3a6b; color: #fff; padding: 18px 32px;
      border-bottom: 3px solid #c8a951;
    }}
    #header .badge {{
      display: inline-block; background: #c8a951; color: #1a1a1a;
      font-size: 10px; font-weight: 700; padding: 2px 9px;
      border-radius: 10px; text-transform: uppercase; letter-spacing: 1px;
      margin-bottom: 8px;
    }}
    #header h1 {{ font-size: 17px; font-weight: 700; line-height: 1.4;
                  margin-bottom: 4px; }}
    #header .meta {{ font-size: 12px; color: #b8c4d4; margin-top: 6px; }}
    #header .meta span {{ margin-right: 18px; }}
    #links {{
      display: flex; gap: 12px; flex-wrap: wrap;
      padding: 14px 32px; background: #fff;
      border-bottom: 1px solid #d0cfc8;
    }}
    .btn-link {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 7px 16px; border-radius: 5px; font-size: 13px;
      font-weight: 600; text-decoration: none; transition: background 0.12s;
      border: 1px solid transparent;
    }}
    .btn-link.web {{ background: #1a3a6b; color: #fff; border-color: #1a3a6b; }}
    .btn-link.web:hover {{ background: #254a8e; }}
    .btn-link.local {{ background: #fff; color: #1a3a6b; border-color: #1a3a6b; }}
    .btn-link.local:hover {{ background: #eef2f9; }}
    /* Bloc contexte */
    #ctx-section {{
      max-width: 900px; margin: 20px auto 0;
      background: #fffdf5; border: 1px solid #e8d98a; border-radius: 6px;
      padding: 14px 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    .ctx-label {{
      font-size: 11px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 1px; color: #a08020; margin-bottom: 8px;
    }}
    #ctx-text {{
      font-size: 14px; line-height: 1.7; color: #333;
      border-left: 3px solid #c8a951; padding-left: 14px;
      font-style: italic;
    }}
    mark.ctx-anchor {{
      background: #fff0a0;
      color: #7a4f00;
      font-weight: 700;
      font-style: normal;
      border-radius: 3px;
      padding: 0 3px;
      box-shadow: 0 0 0 1px #c8a951;
    }}
    /* Bloc validation */
    #val-section {{
      max-width: 900px; margin: 20px auto 0;
      background: #fff; border: 1px solid #d0cfc8; border-radius: 6px;
      padding: 16px 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .val-title {{
      font-size: 13px; font-weight: 700; color: #333;
      margin-bottom: 14px; display: flex; align-items: center; gap: 8px;
    }}
    .val-subtitle {{
      font-size: 11px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 1px; color: #aaa; margin-bottom: 8px;
    }}
    /* — Toggle bar — */
    #val-toggle-bar {{
      display: flex; flex-direction: row;
      border: 1px solid #dde; border-radius: 6px;
      overflow: hidden; margin-bottom: 14px;
    }}
    .vseg {{
      flex: 1; display: flex; flex-direction: column;
      align-items: center; gap: 5px;
      padding: 9px 6px 8px;
      cursor: pointer; border: none; border-right: 1px solid #dde;
      background: #f8f8fb; font-size: 11px;
      font-family: 'Segoe UI', Arial, sans-serif;
      color: #99a; transition: background 0.12s, color 0.12s;
      position: relative; outline: none;
    }}
    .vseg:last-child {{ border-right: none; }}
    .vseg-dot {{
      width: 10px; height: 10px; border-radius: 50%;
      display: block; opacity: 0.28;
      transition: opacity 0.12s, transform 0.12s;
    }}
    .vseg.current::after {{
      content: ''; position: absolute; bottom: 3px; left: 50%;
      transform: translateX(-50%); width: 20px; height: 2px;
      border-radius: 1px; background: #b0b8c8;
    }}
    .vseg.active {{
      background: #fff; color: #223; font-weight: 700;
      box-shadow: inset 0 0 0 1px rgba(0,0,0,0.08);
    }}
    .vseg.active .vseg-dot {{ opacity: 1; transform: scale(1.2); }}
    .vseg:not(.active):hover {{ background: #eef0f8; color: #445; }}
    .vseg:not(.active):hover .vseg-dot {{ opacity: 0.65; }}
    #val-actions {{ display: flex; align-items: center; gap: 14px; }}
    #val-save {{
      padding: 7px 20px; background: #1a3a6b; color: #fff; border: none;
      border-radius: 5px; font-size: 13px; font-weight: 600; cursor: pointer;
      transition: background 0.12s;
    }}
    #val-save:hover:not(:disabled) {{ background: #254a8e; }}
    #val-save:disabled {{
      background: #c8cdd8; color: #e8eaf0; cursor: not-allowed; opacity: 0.75;
    }}
    #val-msg {{ font-size: 12px; font-style: italic; }}
    /* Contenu */
    #content {{
      max-width: 900px; margin: 20px auto; background: #fff;
      border: 1px solid #d0cfc8; border-radius: 6px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.07); overflow: hidden;
    }}
    #content-header {{
      background: #f4f3ee; border-bottom: 1px solid #d0cfc8;
      padding: 10px 20px; font-size: 11px; color: #888;
      font-family: monospace; letter-spacing: 0.3px;
    }}
    pre {{
      padding: 20px 24px; font-family: 'Courier New', monospace;
      font-size: 13px; line-height: 1.75; white-space: pre-wrap;
      word-break: break-word; color: #1c1c1c;
    }}
    .back-link {{
      display: block; text-align: center; padding: 18px;
      font-size: 12px; color: #667; text-decoration: none;
    }}
    .back-link:hover {{ color: #1a3a6b; }}
  </style>
</head>
<body>
<div id="header">
  <div class="badge">📄 Fiche source — Bulletin RDC 2026</div>
  <h1>{html_lib.escape(titre)}</h1>
  <div class="meta">
    <span>📚 {html_lib.escape(source)}</span>
    <span>🔍 Niveau {html_lib.escape(niveau)}</span>
    <span>📅 Consulté le {html_lib.escape(consult)}</span>
  </div>
</div>

<div id="links">
  {web_links}
  {local_link}
</div>

{ctx_block}

{val_block}

<div id="content">
  <div id="content-header">📁 {html_lib.escape(rel)}</div>
  <pre>{content_escaped}</pre>
</div>

<a class="back-link" href="javascript:window.close()">✕ Fermer cet onglet</a>
</body>
</html>"""

    def _serve_html(self):
        with _html_lock:
            data = _html_cache.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _serve_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        q = queue.Queue(maxsize=10)
        with _clients_lock:
            _clients.append(q)

        try:
            while True:
                try:
                    msg = q.get(timeout=25)
                    self.wfile.write(f"data: {msg}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    # Heartbeat pour maintenir la connexion
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            with _clients_lock:
                if q in _clients:
                    _clients.remove(q)


# ---------------------------------------------------------------------------
# Point d'entrée

if __name__ == "__main__":
    # Lire les arguments CLI
    no_browser = "--no-browser" in sys.argv

    print("=" * 60)
    print("  Serveur de prévisualisation — Bulletin RDC 2026")
    print("=" * 60)

    # Libérer le port (tuer les anciens processus)
    print(f"\n[INIT] Vérification du port {PORT}…")
    was_running = kill_port(PORT)
    if was_running:
        print(f"[INIT] Port {PORT} libéré. Redémarrage en cours…")
    else:
        print(f"[INIT] Port {PORT} libre.")

    # Premier build
    print("[INIT] Construction initiale de la page…")
    rebuild()

    # Watchdog
    observer = Observer()
    observer.schedule(ChangeHandler(), str(WORKSPACE_DIR), recursive=True)
    observer.start()
    print("[WATCHER] Surveillance des fichiers activée")

    # Serveur HTTP
    class RobustHTTPServer(http.server.ThreadingHTTPServer):
        """Serveur robuste aux erreurs de connexion Windows (WinError 10053 etc.)"""
        def handle_error(self, request, client_address):
            import sys
            exc = sys.exc_info()[1]
            if isinstance(exc, (ConnectionAbortedError, ConnectionResetError,
                                BrokenPipeError, OSError)):
                return  # Ignorer silencieusement les erreurs de connexion
            super().handle_error(request, client_address)

    server = RobustHTTPServer(("localhost", PORT), PreviewHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    url = f"http://localhost:{PORT}"
    print(f"\n[OK] Serveur demarre -> {url}")
    print("[OK] Ctrl+C pour arrêter\n")

    # Ouvrir le navigateur uniquement si :
    # - ce n'est pas une relance (port était libre)
    # - ET l'option --no-browser n'est pas passée
    if not was_running and not no_browser:
        print("[OK] Ouverture du navigateur…")
        threading.Timer(1.0, webbrowser.open, args=[url]).start()
    elif was_running:
        print("[OK] Relance détectée — la page existante se rafraîchit automatiquement.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[ARRÊT] Fermeture du serveur…")
        server.shutdown()
        observer.stop()
        observer.join()
        print("[ARRÊT] OK")
    except Exception as exc:
        print(f"\n[ERREUR] Exception inattendue dans la boucle principale : {exc}")
        import traceback; traceback.print_exc()
