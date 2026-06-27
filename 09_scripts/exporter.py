"""
exporter.py
-----------
Génère une version exportable du bulletin pour relecture hors ligne.

Formats disponibles :
  --html  (défaut) — fichier HTML autonome, CSS intégré, aucune dépendance serveur
  --word           — document Word .docx via pandoc
  --pdf            — PDF via weasyprint (pip install weasyprint) ou pandoc
  --all            — HTML + Word + PDF

Options :
  --notes          — inclure les blocs NOTE_INTERNE (version interne de travail)
  --open           — ouvrir automatiquement le(s) fichier(s) produit(s)

Usage :
    python 09_scripts/exporter.py                  # HTML relecture
    python 09_scripts/exporter.py --all            # tous les formats
    python 09_scripts/exporter.py --word           # Word via pandoc
    python 09_scripts/exporter.py --notes --open   # HTML interne + ouverture auto
    python 09_scripts/exporter.py --pdf            # PDF via weasyprint ou pandoc
"""

import argparse
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Résolution de pandoc (PATH courant + emplacements connus Windows/Linux/macOS)

def _find_pandoc() -> str:
    """Retourne le chemin de l'exécutable pandoc, même si le PATH est obsolète."""
    import shutil
    found = shutil.which("pandoc")
    if found:
        return found
    candidates = [
        # Windows — installation utilisateur (winget / installeur officiel)
        pathlib.Path.home() / "AppData" / "Local" / "Pandoc" / "pandoc.exe",
        # Windows — installation système
        pathlib.Path("C:/Program Files/Pandoc/pandoc.exe"),
        # macOS Homebrew
        pathlib.Path("/opt/homebrew/bin/pandoc"),
        pathlib.Path("/usr/local/bin/pandoc"),
        # Linux
        pathlib.Path("/usr/bin/pandoc"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return "pandoc"  # fallback — laisse subprocess générer l'erreur habituelle

PANDOC = _find_pandoc()

# ---------------------------------------------------------------------------
# Chemins

SCRIPT_DIR    = pathlib.Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent
OUTPUT_DIR    = WORKSPACE_DIR / "10_output"
ASSEMBLER     = SCRIPT_DIR / "assembler_markdown.py"
EXPORT_CSS    = SCRIPT_DIR / "export_relecture.css"
PREVIEW_CSS   = SCRIPT_DIR / "preview.css"

MD_TRAVAIL     = OUTPUT_DIR / "bulletin_complet_travail.md"
MD_PUBLICATION = OUTPUT_DIR / "bulletin_complet_publication.md"

STAMP = datetime.now().strftime("%Y-%m-%d")

# ---------------------------------------------------------------------------
# Dépendance markdown (déjà requise par le serveur de prévisualisation)

try:
    import markdown
    from markdown.extensions.toc import TocExtension
except ImportError:
    print("[ERREUR] Module 'markdown' requis : pip install markdown")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Traitement Markdown — fonctions partagées avec le serveur de prévisualisation

# Correspondances statut texte → classe CSS + libellé affiché
STATUS_CLASSES = {
    'brouillon':            ('status-brouillon', 'Brouillon'),
    'structure initiale':   ('status-brouillon', 'Structure initiale'),
    'à revoir':             ('status-arevoir',   'À revoir'),
    'notes développées':    ('status-arevoir',   'Notes développées'),
    'rédigé':               ('status-redige',    'Rédigé'),
    'revu':                 ('status-revu',      'Revu'),
    'révisé':               ('status-revu',      'Révisé'),
    'validé':               ('status-valide',    'Validé'),
}


def build_status_map(md_text: str) -> dict:
    """Construit {texte_titre: (css_class, label)} en lisant les blocs NOTE_INTERNE."""
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
        dot = f'<span class="status-dot {cls}" title="{label}">&#9679;</span> '
        pattern = r'(<h[1-6][^>]*>)(' + re.escape(heading_text) + r')(</h[1-6]>)'
        html = re.sub(
            pattern,
            lambda mo: mo.group(1) + dot + mo.group(2) + mo.group(3),
            html,
        )
    return html


def preprocess_md(md_text: str, include_notes: bool = False) -> str:
    """Prépare le Markdown pour la conversion HTML.

    - Supprime (ou conserve) les blocs NOTE_INTERNE selon include_notes
    - Supprime les autres commentaires HTML
    - Retire le H1 initial (affiché dans le header de la page)
    - Traite les titres '## Texte rédigé'
    """
    if not include_notes:
        md_text = re.sub(r'<!--\s*NOTE_INTERNE.*?-->', '', md_text, flags=re.DOTALL)

    # Supprimer les commentaires restants (SECTION, VERSION, FIN FICHIER…)
    md_text = re.sub(r'<!--[^>]*-->', '', md_text)

    # Supprimer le premier H1 du document (affiché dans #export-title)
    md_text = re.sub(r'^\s*#\s+.+\n', '', md_text, count=1)

    # Traiter les titres "## Texte rédigé"
    lines = md_text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^##\s+Texte\s+r[eé]dig[eé]\s*$', line, re.IGNORECASE):
            i += 1
            content_lines = []
            while i < len(lines):
                if re.match(r'^#{1,2}\s+', lines[i]):
                    break
                content_lines.append(lines[i])
                i += 1
            content = '\n'.join(content_lines).strip()
            content_no_comments = re.sub(
                r'<!--.*?-->', '', content, flags=re.DOTALL
            ).strip()
            is_empty = (
                not content_no_comments
                or len(content_no_comments) < 15
                or re.match(
                    r'^[\[_*].*?(rédiger|à compléter|en cours).*?[\]_*]$',
                    content_no_comments,
                    re.IGNORECASE,
                )
            )
            if is_empty:
                result.append('\n<p class="a-rediger">&#9998; Texte à rédiger</p>\n')
            else:
                result.extend(content_lines)
            continue
        result.append(line)
        i += 1

    return '\n'.join(result)


def neutralize_server_links(html: str) -> str:
    """Convertit les liens /files/... en liens non-navigables.

    Ces liens pointent vers des fichiers servis uniquement par le serveur local.
    Dans un export autonome, ils sont remplacés par des liens annotés data-offline.
    """
    return re.sub(
        r'href="/files/([^"]*)"',
        r'href="#" data-offline="true" data-src="\1"',
        html,
    )


# ---------------------------------------------------------------------------
# Construction du HTML d'export

def _read_css() -> str:
    """Lit la CSS d'export. Repli sur preview.css si absente."""
    if EXPORT_CSS.exists():
        return EXPORT_CSS.read_text(encoding="utf-8-sig")
    if PREVIEW_CSS.exists():
        print("[AVERTISSEMENT] export_relecture.css introuvable, utilisation de preview.css")
        return PREVIEW_CSS.read_text(encoding="utf-8-sig")
    return ""


def build_export_html(md_file: pathlib.Path, include_notes: bool = False) -> str:
    """Génère un fichier HTML autonome (CSS intégrée) pour relecture hors ligne."""
    css = _read_css()

    if not md_file.exists():
        return (
            "<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
            "<title>Erreur</title></head><body>"
            "<p><em>Fichier Markdown source introuvable. "
            "Lancez d'abord l'assembleur.</em></p></body></html>"
        )

    md_text = md_file.read_text(encoding="utf-8")

    # Titre du document (premier H1)
    doc_title = "Deuxième Bulletin statistique de la protection sociale en RDC"
    m_title = re.search(r'^#\s+(.+)$', md_text, re.MULTILINE)
    if m_title:
        doc_title = m_title.group(1).strip()

    # Lire les statuts avant preprocessing (les NOTE_INTERNE sont encore présentes)
    status_map = build_status_map(md_text)

    # Préparer le Markdown
    md_preview = preprocess_md(md_text, include_notes=include_notes)

    # Convertir en HTML
    md_engine = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "md_in_html",
            TocExtension(title="", toc_depth=3),
        ]
    )
    body = md_engine.convert(md_preview)
    toc  = md_engine.toc

    # Enrichir le HTML
    body = inject_status_dots_html(body, status_map)
    body = neutralize_server_links(body)

    # Ajouter la classe "chapitre-titre" aux h1 qui commencent par "Chapitre" ou "Annexe"
    body = re.sub(
        r'<h1([^>]*)>((?:(?!</h1>).)*?(?:Chapitre\s+\d|Annexe\s+[A-Z]))',
        r'<h1\1 class="chapitre-titre">\2',
        body,
    )

    # Encadrer les tableaux pour le scroll horizontal
    body = re.sub(r'(<table)', r'<div class="table-scroll">\1', body)
    body = re.sub(r'(</table>)', r'\1</div>', body)

    # Ajouter la classe "fig-block" aux blockquotes contenant un intitulé de figure
    body = re.sub(
        r'<blockquote>\s*<p><strong>(Figure\s+\d)',
        r'<blockquote class="fig-block"><p><strong>\1',
        body,
    )

    # Ajouter la classe "table-caption" aux paragraphes de légende de tableau (**Tableau…**)
    body = re.sub(
        r'<p><strong>(Tableau\s+\d)',
        r'<p class="table-caption"><strong>\1',
        body,
    )

    # Ajouter la classe "fig-source" aux paragraphes de source (*Source :…*)
    body = re.sub(
        r'<p><em>(Source\s*:)',
        r'<p class="fig-source"><em>\1',
        body,
    )

    # Métadonnées d'export
    now              = datetime.now()
    export_date      = now.strftime("%d %B %Y à %H:%M")
    export_date_print = now.strftime("%d/%m/%Y  %H:%M")   # format compact pour le pied de page imprimé
    label_type  = "VERSION INTERNE — notes de travail incluses" if include_notes else "VERSION RELECTURE"

    toc_html = (
        toc if toc
        else '<p style="padding:12px;color:#667;font-size:12px;">Aucun titre détecté.</p>'
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{doc_title} — Relecture</title>
  <style>{css}</style>
</head>
<body>

<!-- Élément porteur de la date pour les pieds de page @page (impression) -->
<span id="print-date">{export_date_print}</span>

<div id="export-header">
  <div id="export-label">{label_type}</div>
  <h1 id="export-title">{doc_title}</h1>
  <div id="export-meta">Exporté le {export_date}</div>
  <div class="export-actions">
    <button class="export-btn" onclick="window.print()">🖨️ Imprimer / Enregistrer en PDF</button>
  </div>
</div>

<div id="wrapper">

  <nav id="toc-panel">
    <div id="toc-header">Table des matières</div>
    {toc_html}
  </nav>

  <div id="content">
    {body}
  </div>

</div>

<script>
/* Légende des statuts */
(function() {{
  var legend = document.createElement("div");
  legend.id = "status-legend";
  var items = [
    ["#d42b2b", "Brouillon / Structure initiale"],
    ["#e07820", "À revoir / Notes développées"],
    ["#c8a800", "Rédigé"],
    ["#2e78c8", "Revu / Révisé"],
    ["#111111", "Validé"],
  ];
  var inner = '<div class="legend-title">Statut des sections</div>';
  items.forEach(function(item) {{
    inner += '<div><span class="l-dot" style="background:' + item[0] + '"></span>' + item[1] + '</div>';
  }});
  legend.innerHTML = inner;
  document.body.appendChild(legend);
}})();

/* Highlight de la section active dans la TOC */
(function() {{
  var headings = document.querySelectorAll("h1[id], h2[id], h3[id]");
  var tocLinks = document.querySelectorAll("#toc-panel a");
  function onScroll() {{
    var current = "";
    headings.forEach(function(h) {{
      if (window.scrollY + 80 >= h.offsetTop) current = h.id;
    }});
    tocLinks.forEach(function(l) {{
      var active = l.getAttribute("href") === "#" + current;
      l.classList.toggle("active", active);
    }});
  }}
  window.addEventListener("scroll", onScroll);
  onScroll();
}})();

/* Tooltip sur les liens source hors ligne */
(function() {{
  var tip = document.createElement("div");
  tip.style.cssText = "position:fixed;background:#333;color:#fff;padding:6px 10px;border-radius:4px;"
    + "font-size:12px;font-family:sans-serif;pointer-events:none;z-index:999;"
    + "opacity:0;transition:opacity 0.15s;max-width:420px;line-height:1.4;";
  document.body.appendChild(tip);

  document.querySelectorAll("a[data-offline]").forEach(function(el) {{
    var src = el.getAttribute("data-src") || "";
    el.title = src ? "Source : " + src + " (disponible via le serveur de prévisualisation)" : "";
    el.addEventListener("mouseover", function(e) {{
      if (!el.title) return;
      tip.textContent = el.title;
      tip.style.opacity = "1";
    }});
    el.addEventListener("mousemove", function(e) {{
      tip.style.left = Math.min(e.clientX + 14, window.innerWidth - 440) + "px";
      tip.style.top  = (e.clientY + 20) + "px";
    }});
    el.addEventListener("mouseout", function() {{
      tip.style.opacity = "0";
    }});
    el.addEventListener("click", function(e) {{
      e.preventDefault();
      alert("Ce lien pointe vers un fichier source du bulletin (06_sources/...).\n"
          + "Il est accessible via le serveur de prévisualisation local (localhost:8765).\n\n"
          + "Fichier : " + (src || "(inconnu)"));
    }});
  }});
}})();
</script>

</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# Lancement de l'assembleur

def run_assembler() -> bool:
    """Relance l'assembleur pour s'assurer que les fichiers .md sont à jour."""
    print("[EXPORT] Assemblage du Markdown…")
    result = subprocess.run(
        [sys.executable, str(ASSEMBLER)],
        capture_output=True,
        cwd=str(WORKSPACE_DIR),
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        print(f"[AVERTISSEMENT] Erreur d'assemblage :\n{result.stderr.strip()}")
        return False
    return True


# ---------------------------------------------------------------------------
# Export HTML

def export_html(include_notes: bool = False, open_after: bool = False) -> "pathlib.Path | None":
    """Génère le fichier HTML autonome dans 10_output/."""
    label  = "notes" if include_notes else "relecture"
    source = MD_TRAVAIL if include_notes else MD_PUBLICATION
    output = OUTPUT_DIR / f"bulletin_{label}_{STAMP}.html"

    run_assembler()

    print("[EXPORT HTML] Génération du fichier HTML…")
    html = build_export_html(source, include_notes=include_notes)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")

    size_kb = output.stat().st_size // 1024
    print(f"[OK] HTML  : {output.relative_to(WORKSPACE_DIR)}  ({size_kb} Ko)")

    if open_after:
        import webbrowser
        webbrowser.open(output.as_uri())

    return output


# ---------------------------------------------------------------------------
# Export Word (via pandoc)

def export_word(include_notes: bool = False, open_after: bool = False) -> "pathlib.Path | None":
    """
    Délègue entièrement à exporter_word.py (pipeline complet : styles, sauts de
    page, TOF, autofit…).  Cette fonction reste le point d'entrée appelé par le
    serveur de prévisualisation et par --word / --all.
    """
    label = "notes" if include_notes else "relecture"
    stamp = STAMP
    html_source = OUTPUT_DIR / f"bulletin_{label}_{stamp}.html"

    # Générer le HTML source s'il est absent
    if not html_source.exists():
        subprocess.run(
            [sys.executable, str(pathlib.Path(__file__)),
             "--notes" if include_notes else "--html"],
            capture_output=True, cwd=str(WORKSPACE_DIR),
            encoding="utf-8", errors="replace",
        )
        if not html_source.exists():
            print(f"[EXPORT WORD] Fichier HTML source introuvable : {html_source.name}")
            print("              Lancez d'abord : python 09_scripts/exporter.py --html")
            return None

    # Déléguer au pipeline Word complet
    exporter_word_path = SCRIPT_DIR / "exporter_word.py"
    if not exporter_word_path.exists():
        print("[EXPORT WORD] exporter_word.py introuvable dans 09_scripts/")
        return None

    result = subprocess.run(
        [sys.executable, str(exporter_word_path), str(html_source)],
        capture_output=True, cwd=str(WORKSPACE_DIR),
        encoding="utf-8", errors="replace",
    )

    output = OUTPUT_DIR / f"bulletin_{label}_{stamp}.docx"
    if result.returncode != 0 or not output.exists():
        err = (result.stderr or result.stdout or "Erreur inconnue").strip()
        print(f"[ERREUR WORD] {err[:600]}")
        return None

    size_kb = output.stat().st_size // 1024
    print(f"[OK] Word  : {output.relative_to(WORKSPACE_DIR)}  ({size_kb} Ko)")

    if open_after:
        try:
            os.startfile(str(output))
        except AttributeError:
            subprocess.Popen(["xdg-open", str(output)])

    return output


# ---------------------------------------------------------------------------
# Export PDF

def export_pdf(include_notes: bool = False, open_after: bool = False) -> "pathlib.Path | None":
    """Génère un PDF.

    Stratégie (ordre de priorité) :
      1. weasyprint  — pip install weasyprint
      2. pandoc + xelatex
      3. Instructions pour impression navigateur
    """
    label  = "notes" if include_notes else "relecture"
    output = OUTPUT_DIR / f"bulletin_{label}_{STAMP}.pdf"

    # — Tentative 1 : weasyprint —
    try:
        import weasyprint  # type: ignore
        # Générer d'abord le HTML si nécessaire
        html_file = export_html(include_notes=include_notes)
        if html_file is None:
            return None
        print("[EXPORT PDF] Conversion weasyprint…")
        weasyprint.HTML(filename=str(html_file)).write_pdf(str(output))
        size_kb = output.stat().st_size // 1024
        print(f"[OK] PDF   : {output.relative_to(WORKSPACE_DIR)}  ({size_kb} Ko)")
        if open_after:
            try:
                os.startfile(str(output))
            except AttributeError:
                import subprocess as sp
                sp.Popen(["xdg-open", str(output)])
        return output
    except ImportError:
        pass
    except Exception as exc:
        print(f"[AVERTISSEMENT] weasyprint a échoué : {exc}")

    # — Tentative 2 : pandoc + xelatex —
    try:
        r = subprocess.run(
            [PANDOC, "--version"], capture_output=True, encoding="utf-8"
        )
        if r.returncode == 0:
            source = MD_TRAVAIL if include_notes else MD_PUBLICATION
            if not source.exists():
                print(f"[EXPORT PDF] Fichier source introuvable : {source.name}")
                return None
            cmd = [
                PANDOC, str(source),
                "--from",   "markdown+smart+raw_html",
                "--to",     "pdf",
                "--output", str(output),
                "--toc", "--toc-depth=3",
                "--pdf-engine=xelatex",
                "--strip-comments",
                "-V", "mainfont=DejaVu Serif",
                "-V", "geometry:margin=2.5cm",
                "-V", "lang=fr",
                "-V", "colorlinks=true",
            ]
            print("[EXPORT PDF] Conversion pandoc + xelatex…")
            result = subprocess.run(
                cmd, capture_output=True, encoding="utf-8", errors="replace"
            )
            if result.returncode == 0:
                size_kb = output.stat().st_size // 1024
                print(f"[OK] PDF   → {output.relative_to(WORKSPACE_DIR)}  ({size_kb} Ko)")
                if open_after:
                    try:
                        os.startfile(str(output))
                    except AttributeError:
                        import subprocess as sp
                        sp.Popen(["xdg-open", str(output)])
                return output
            else:
                print(f"[AVERTISSEMENT] pandoc PDF a échoué : {result.stderr.strip()[:300]}")
    except FileNotFoundError:
        pass

    # — Aucun moteur disponible —
    print()
    print("[EXPORT PDF] Aucun moteur PDF trouvé. Options disponibles :")
    print()
    print("  Option 1 — weasyprint (recommandé, fidèle au HTML) :")
    print("             pip install weasyprint")
    print()
    print("  Option 2 — pandoc + LaTeX :")
    print("             https://pandoc.org/installing.html")
    print("             + distribution LaTeX (MiKTeX, TeX Live…)")
    print()
    print("  Option 3 — Impression navigateur (sans installation) :")

    html_file = export_html(include_notes=include_notes)
    if html_file:
        print(f"             1. Ouvrir : {html_file}")
        print("             2. Ctrl+P > Enregistrer en PDF")
        print("                (cocher « Graphiques de fond » pour la couleur)")
    return None


# ---------------------------------------------------------------------------
# Point d'entrée

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exporte le bulletin en HTML, Word ou PDF pour relecture hors ligne.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemples :\n"
            "  python 09_scripts/exporter.py                  # HTML relecture\n"
            "  python 09_scripts/exporter.py --all            # tous les formats\n"
            "  python 09_scripts/exporter.py --word --open    # Word, ouvrir auto\n"
            "  python 09_scripts/exporter.py --notes          # HTML avec notes internes\n"
        ),
    )
    parser.add_argument("--html",  action="store_true",
                        help="Générer l'export HTML autonome (défaut si aucun format)")
    parser.add_argument("--word",  action="store_true",
                        help="Générer l'export Word (.docx) via pandoc")
    parser.add_argument("--pdf",   action="store_true",
                        help="Générer l'export PDF via weasyprint ou pandoc")
    parser.add_argument("--all",   action="store_true",
                        help="Générer tous les formats (HTML + Word + PDF)")
    parser.add_argument("--notes", action="store_true",
                        help="Inclure les notes internes (version de travail)")
    parser.add_argument("--open",  action="store_true",
                        help="Ouvrir automatiquement le(s) fichier(s) produit(s)")
    args = parser.parse_args()

    # HTML par défaut si aucun format précisé
    do_html = args.html or args.all or not any([args.word, args.pdf, args.all])
    do_word = args.word or args.all
    do_pdf  = args.pdf  or args.all

    produced = []

    if do_html:
        f = export_html(include_notes=args.notes, open_after=args.open)
        if f:
            produced.append(f)

    if do_word:
        f = export_word(include_notes=args.notes, open_after=args.open)
        if f:
            produced.append(f)

    if do_pdf:
        f = export_pdf(include_notes=args.notes, open_after=args.open)
        if f:
            produced.append(f)

    print()
    if produced:
        print(f"[OK] {len(produced)} fichier(s) dans 10_output/ :")
        for f in produced:
            print(f"     {f.name}")
    else:
        print("Aucun fichier produit.")


if __name__ == "__main__":
    main()
