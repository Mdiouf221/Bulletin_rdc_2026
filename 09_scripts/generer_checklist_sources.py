"""
generer_checklist_sources.py
----------------------------
1. Enrichit les fichiers _metadata.txt en ajoutant un champ "LIEN SOURCE"
   explicite (URL web + chemin disque) si absent.
2. Genere 10_output/CHECKLIST_verification_sources.html :
   checklist interactive (localStorage) pour l'auditeur humain.

Usage : py -3 09_scripts/generer_checklist_sources.py
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from html import escape as esc

BASE_DIR = Path(__file__).resolve().parent.parent
REGISTRE = BASE_DIR / "06_sources" / "registre_sources.json"
OUTPUT   = BASE_DIR / "10_output" / "CHECKLIST_verification_sources.html"

# ── Helpers ──────────────────────────────────────────────────────────────────

def lire_registre():
    with open(REGISTRE, encoding="utf-8-sig") as f:
        data = json.load(f)
    return data["sources"]

def lien_disque(chemin_relatif):
    """Construit un lien file:// depuis un chemin relatif au projet."""
    if not chemin_relatif:
        return None
    p = BASE_DIR / chemin_relatif
    return p.as_uri()  # file:///C:/...

def pdf_principal(src):
    """Retourne le chemin relatif du PDF principal d'une source (ou None)."""
    for champ in ("fichier_pdf", "fichier_source"):
        v = src.get(champ)
        if v and v.endswith(".pdf"):
            return v
    return None

def xlsx_principal(src):
    """Retourne le chemin relatif du fichier Excel d'une source (ou None)."""
    for champ in ("fichier_source",):
        v = src.get(champ)
        if v and (v.endswith(".xlsm") or v.endswith(".xlsx")):
            return v
    return None

def urls_source(src):
    """Retourne la liste des URLs web associées à une source."""
    urls = []
    for champ in ("url_source", "url_pdf_direct", "url_api", "url_country_brief"):
        v = src.get(champ)
        if v:
            urls.append((champ, v))
    return urls

# ── Étape 1 : Enrichir les fichiers metadata ─────────────────────────────────

LIEN_MARKER = "LIEN SOURCE"

def enrichir_metadata(sources):
    modifies = 0
    for src in sources:
        meta_path_rel = src.get("fichier_metadata")
        if not meta_path_rel:
            continue
        meta_path = BASE_DIR / meta_path_rel
        if not meta_path.exists():
            continue

        contenu = meta_path.read_text(encoding="utf-8-sig")

        # Deja enrichi ?
        if LIEN_MARKER in contenu:
            continue

        # Construire les lignes a ajouter
        lignes_lien = []

        # URL(s) web
        for champ, url in urls_source(src):
            label = {
                "url_source": "URL source officielle",
                "url_pdf_direct": "URL PDF direct",
                "url_api": "URL API",
                "url_country_brief": "URL Country Brief",
            }.get(champ, champ)
            lignes_lien.append(f"{LIEN_MARKER} — {label} : {url}")

        # PDF local
        pdf_rel = pdf_principal(src)
        if pdf_rel:
            pdf_abs = BASE_DIR / pdf_rel
            statut = "present" if pdf_abs.exists() else "ABSENT"
            lignes_lien.append(f"LIEN SOURCE — PDF local ({statut}) : {pdf_rel}")

        # Excel/XLSM
        xlsx_rel = xlsx_principal(src)
        if xlsx_rel:
            xlsx_abs = BASE_DIR / xlsx_rel
            statut = "present" if xlsx_abs.exists() else "ABSENT"
            lignes_lien.append(f"LIEN SOURCE — Fichier source Excel ({statut}) : {xlsx_rel}")

        # Source sans lien
        if not lignes_lien:
            if src.get("statut_pdf", "").startswith("non"):
                lignes_lien.append(f"LIEN SOURCE : source non disponible publiquement — fiche metadata fait office de source")
            else:
                lignes_lien.append(f"LIEN SOURCE : non renseigne")

        bloc = "\n".join(lignes_lien)

        # Inserer apres la ligne FICHIER : (ou apres NIVEAU FIABILITE :)
        # On cherche la derniere ligne de "header" (avant ---) et on insere apres
        lines = contenu.split("\n")
        insert_after = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("FICHIER :") or line.strip().startswith("NIVEAU FIABILITE"):
                insert_after = i

        if insert_after >= 0:
            lines.insert(insert_after + 1, bloc)
            nouveau = "\n".join(lines)
        else:
            # Inserer au tout debut
            nouveau = bloc + "\n" + contenu

        meta_path.write_text(nouveau, encoding="utf-8")
        modifies += 1
        print(f"  [ENRICHI] {meta_path_rel}")

    print(f"\n[INFO] {modifies} fichier(s) metadata enrichi(s) avec LIEN SOURCE.")
    return modifies

# ── Étape 2 : Générer la checklist HTML ──────────────────────────────────────

def badge_fiabilite(n):
    labels = {1: ("niv1", "Niveau 1 — Source primaire"),
              2: ("niv2", "Niveau 2 — Source secondaire acceptable"),
              3: ("niv3", "Niveau 3 — Source regionale"),
              4: ("niv4", "Niveau 4 — Academique"),
              5: ("niv5", "Niveau 5 — A traiter avec prudence")}
    css, title = labels.get(n, ("niv0", f"Niveau {n}"))
    return f'<span class="badge-niv {css}" title="{esc(title)}">N{n}</span>'

def badge_type(src):
    """Retourne un badge selon le type de source."""
    if src.get("statut_verification") in ("reference normative", "reference validee"):
        return '<span class="badge-type ref">REF</span>'
    pdf = pdf_principal(src)
    urls = urls_source(src)
    if pdf and urls:
        return '<span class="badge-type mixte">PDF+WEB</span>'
    if pdf:
        return '<span class="badge-type pdf">PDF</span>'
    if urls:
        return '<span class="badge-type web">WEB</span>'
    xlsx = xlsx_principal(src)
    if xlsx:
        return '<span class="badge-type excel">EXCEL</span>'
    return '<span class="badge-type meta">META</span>'

def icone_statut_verif(src):
    sv = src.get("statut_verification", "")
    if "reference" in sv:
        return "✅"
    if "en attente" in sv:
        return "⏳"
    return "❓"

def generer_html(sources):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    total = len(sources)

    # Grouper par categorie
    categories = {
        "ESS — Enquetes institutionnelles (CNSS / CNSSAP)": [],
        "Sources nationales RDC": [],
        "Sources internationales — rapports et statistiques": [],
        "Normes OIT": [],
        "Bulletins de comparaison": [],
        "Atelier de lancement": [],
        "Autres": [],
    }

    def categorie(src):
        sid = src.get("id", "")
        if sid.startswith("ESS-"):
            return "ESS — Enquetes institutionnelles (CNSS / CNSSAP)"
        if sid.startswith("OIT-"):
            return "Normes OIT"
        if sid.startswith("BULLETIN-") and "RDC" not in sid:
            return "Bulletins de comparaison"
        if sid == "BULLETIN-RDC-1":
            return "Sources nationales RDC"
        if sid.startswith("RDC-") or sid in ("CNSS-RDC", "CNSSAP-RDC", "FSS-RDC"):
            return "Sources nationales RDC"
        if sid.startswith("ATELIER-"):
            return "Atelier de lancement"
        if sid.startswith(("BIT-", "ONU-", "UNFPA-", "BM-", "FAO-", "PAM-", "UNICEF-", "BM-")):
            return "Sources internationales — rapports et statistiques"
        return "Autres"

    for src in sources:
        categories[categorie(src)].append(src)

    parts = []
    parts.append(f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Checklist de verification des sources — Bulletin PS RDC</title>
<style>
:root {{
  --ok: #2a7a2a; --warn: #d4820a; --err: #c0392b; --info: #2563a8;
  --bg: #f8f9fa; --card: #ffffff; --border: #dce3ea;
  --font: 'Segoe UI', system-ui, sans-serif;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: var(--font); background: var(--bg); color: #222; font-size: 14px; }}
header {{
  background: #1a3a5c; color: white; padding: 20px 32px;
  position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 8px rgba(0,0,0,.3);
}}
header h1 {{ font-size: 1.2rem; margin-bottom: 4px; }}
header p {{ font-size: .8rem; opacity: .8; }}
.progress-bar-wrap {{ background: #0d2540; border-radius: 4px; margin-top: 10px; height: 8px; }}
.progress-bar {{ background: #4caf50; height: 8px; border-radius: 4px; transition: width .3s; }}
.progress-label {{ font-size:.75rem; opacity:.8; margin-top:3px; }}

.container {{ max-width: 1200px; margin: 24px auto; padding: 0 20px; }}
.stats-row {{ display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap; }}
.stat-card {{
  background: var(--card); border: 1px solid var(--border); border-radius: 8px;
  padding: 12px 20px; min-width: 140px; text-align: center;
}}
.stat-card .n {{ font-size: 1.6rem; font-weight: bold; color: var(--info); }}
.stat-card .l {{ font-size: .75rem; color: #666; margin-top: 2px; }}

.section-title {{
  font-size: 1rem; font-weight: 600; color: #1a3a5c;
  border-bottom: 2px solid #1a3a5c; padding-bottom: 6px; margin: 28px 0 12px;
  display: flex; align-items: center; gap: 8px;
}}
.section-title .count {{
  background: #1a3a5c; color: white; border-radius: 10px;
  font-size: .72rem; padding: 2px 8px; font-weight: 400;
}}

.source-card {{
  background: var(--card); border: 1px solid var(--border);
  border-radius: 8px; margin-bottom: 10px; overflow: hidden;
}}
.source-header {{
  display: grid;
  grid-template-columns: 36px 1fr auto;
  gap: 12px; align-items: start;
  padding: 12px 16px; cursor: pointer;
  transition: background .15s;
}}
.source-header:hover {{ background: #f0f4f8; }}
.source-header.verified {{ border-left: 4px solid var(--ok); }}
.source-header.issue    {{ border-left: 4px solid var(--err); }}

.cb-wrap {{ display:flex; align-items:center; justify-content:center; padding-top:2px; }}
input[type=checkbox] {{ width:18px; height:18px; cursor:pointer; accent-color: var(--ok); }}

.src-title {{ font-weight: 600; font-size: .9rem; color: #1a3a5c; }}
.src-meta  {{ font-size: .78rem; color: #555; margin-top: 3px; }}
.src-meta span {{ margin-right: 10px; }}

.badges {{ display:flex; gap:6px; align-items:flex-start; flex-wrap:wrap; padding-top:2px; }}
.badge-niv {{
  border-radius: 4px; font-size: .68rem; font-weight: bold; padding: 2px 6px;
}}
.niv1 {{ background:#e8f5e9; color:#2a7a2a; border:1px solid #a5d6a7; }}
.niv2 {{ background:#e3f2fd; color:#1565c0; border:1px solid #90caf9; }}
.niv3 {{ background:#fff3e0; color:#e65100; border:1px solid #ffcc80; }}
.niv4 {{ background:#f3e5f5; color:#6a1b9a; border:1px solid #ce93d8; }}
.niv5 {{ background:#ffebee; color:#b71c1c; border:1px solid #ef9a9a; }}
.badge-type {{
  border-radius: 4px; font-size: .68rem; font-weight: bold; padding: 2px 6px;
}}
.pdf   {{ background:#fff3e0; color:#e65100; border:1px solid #ffb74d; }}
.web   {{ background:#e3f2fd; color:#1565c0; border:1px solid #64b5f6; }}
.excel {{ background:#e8f5e9; color:#2a7a2a; border:1px solid #81c784; }}
.mixte {{ background:#f3e5f5; color:#6a1b9a; border:1px solid #ce93d8; }}
.meta  {{ background:#eceff1; color:#546e7a; border:1px solid #b0bec5; }}
.ref   {{ background:#e8f5e9; color:#1b5e20; border:1px solid #a5d6a7; font-style:italic; }}

.source-body {{
  padding: 0 16px 16px 16px; border-top: 1px solid #f0f0f0; display: none;
}}
.source-body.open {{ display: block; }}

.liens-row {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 12px 0 10px; }}
.lien-btn {{
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 12px; border-radius: 5px; font-size: .8rem;
  text-decoration: none; font-weight: 500; border: 1px solid;
  transition: background .15s;
}}
.lien-btn.pdf-btn  {{ background:#fff3e0; color:#e65100; border-color:#ffb74d; }}
.lien-btn.web-btn  {{ background:#e3f2fd; color:#1565c0; border-color:#64b5f6; }}
.lien-btn.xlsx-btn {{ background:#e8f5e9; color:#2a7a2a; border-color:#81c784; }}
.lien-btn.meta-btn {{ background:#eceff1; color:#546e7a; border-color:#b0bec5; }}
.lien-btn:hover {{ filter: brightness(.93); }}
.lien-btn.absent {{ opacity:.5; cursor:not-allowed; text-decoration:line-through; }}

.dk-list {{ margin: 8px 0; padding-left: 0; list-style: none; }}
.dk-list li {{
  padding: 5px 10px; border-left: 3px solid #dce3ea;
  margin-bottom: 4px; font-size: .82rem; color: #333;
  background: #fafafa; border-radius: 0 4px 4px 0;
}}
.dk-list li.online {{ border-left-color: #64b5f6; background: #f0f7ff; }}
.dk-list li.derive {{ border-left-color: #ce93d8; background: #fdf4ff; }}
.dk-list li.attente{{ border-left-color: #ffb74d; background: #fffbf0; }}

.note-box {{
  background: #fff8e1; border: 1px solid #ffe082; border-radius: 5px;
  padding: 8px 12px; font-size: .8rem; color: #555; margin-top: 8px;
}}

.statut-verif-badge {{
  display: inline-block; border-radius: 4px; padding: 2px 8px;
  font-size: .72rem; font-weight: bold;
}}
.sv-ok    {{ background:#e8f5e9; color:#2a7a2a; }}
.sv-warn  {{ background:#fff3e0; color:#e65100; }}
.sv-wait  {{ background:#eceff1; color:#546e7a; }}

.filter-bar {{
  display: flex; gap: 10px; margin-bottom: 18px; flex-wrap: wrap; align-items: center;
}}
.filter-bar label {{ font-size: .82rem; color: #555; margin-right: -4px; }}
.filter-bar select, .filter-bar input {{
  border: 1px solid var(--border); border-radius: 5px; padding: 5px 10px; font-size: .82rem;
}}
.reset-btn {{
  background: #1a3a5c; color: white; border: none; border-radius: 5px;
  padding: 5px 14px; font-size: .82rem; cursor: pointer;
}}
.reset-btn:hover {{ background: #2a5080; }}
.export-btn {{
  background: #2a7a2a; color: white; border: none; border-radius: 5px;
  padding: 5px 14px; font-size: .82rem; cursor: pointer; margin-left: auto;
}}
.export-btn:hover {{ background: #3a9a3a; }}

.hidden {{ display: none !important; }}

@media print {{
  header {{ position: static; }}
  .source-body {{ display: block !important; }}
  .filter-bar, .export-btn, .reset-btn {{ display: none; }}
}}
</style>
</head>
<body>
<header>
  <h1>&#128270; Checklist de verification des sources — Bulletin statistique de la protection sociale en RDC</h1>
  <p>Genere le {now} &middot; {total} sources a verifier</p>
  <div class="progress-bar-wrap"><div class="progress-bar" id="pbar" style="width:0%"></div></div>
  <div class="progress-label" id="plabel">0 / {total} verifiees</div>
</header>
<div class="container">
""")

    # Stats globales
    n_pdf    = sum(1 for s in sources if pdf_principal(s) and (BASE_DIR / pdf_principal(s)).exists())
    n_web    = sum(1 for s in sources if urls_source(s))
    n_online = sum(1 for s in sources for d in s.get("donnees_cles", []) if "[SOURCE_ONLINE" in d)
    n_refval = sum(1 for s in sources if "reference" in s.get("statut_verification", ""))

    parts.append(f"""<div class="stats-row">
  <div class="stat-card"><div class="n">{total}</div><div class="l">sources totales</div></div>
  <div class="stat-card"><div class="n">{n_pdf}</div><div class="l">PDF sur disque</div></div>
  <div class="stat-card"><div class="n">{n_web}</div><div class="l">avec URL web</div></div>
  <div class="stat-card"><div class="n" style="color:#d4820a">{n_online}</div><div class="l">donnees en ligne a verifier</div></div>
  <div class="stat-card"><div class="n" style="color:var(--ok)">{n_refval}</div><div class="l">references validees</div></div>
</div>""")

    # Barre de filtres
    parts.append("""<div class="filter-bar">
  <label>Filtrer :</label>
  <select id="filter-cat" onchange="filtrer()">
    <option value="">Toutes les categories</option>
    <option value="ESS">ESS</option>
    <option value="nationales">Sources nationales</option>
    <option value="internationales">Sources internationales</option>
    <option value="normes">Normes OIT</option>
    <option value="bulletins">Bulletins comparaison</option>
    <option value="atelier">Atelier</option>
  </select>
  <select id="filter-statut" onchange="filtrer()">
    <option value="">Tous les statuts</option>
    <option value="non-verifiee">Non verifiees seulement</option>
    <option value="verifiee">Verifiees seulement</option>
  </select>
  <input id="filter-search" type="text" placeholder="Rechercher..." oninput="filtrer()">
  <button class="reset-btn" onclick="resetFiltres()">Reinitialiser</button>
  <button class="export-btn" onclick="exporterCSV()">Exporter CSV</button>
</div>""")

    # Cartes sources par categorie
    for cat_name, cat_sources in categories.items():
        if not cat_sources:
            continue
        cat_key = {
            "ESS — Enquetes institutionnelles (CNSS / CNSSAP)": "ESS",
            "Sources nationales RDC": "nationales",
            "Sources internationales — rapports et statistiques": "internationales",
            "Normes OIT": "normes",
            "Bulletins de comparaison": "bulletins",
            "Atelier de lancement": "atelier",
        }.get(cat_name, "autres")

        parts.append(f'<div class="section-title" data-cat="{cat_key}">'
                     f'{esc(cat_name)}'
                     f'<span class="count">{len(cat_sources)}</span></div>')

        for src in cat_sources:
            sid = src.get("id", "")
            titre = src.get("titre", sid)
            org   = src.get("organisation", "")
            annee = src.get("annee", "")
            niv   = src.get("niveau_fiabilite", 0)
            sv    = src.get("statut_verification", "a valider")
            dk    = src.get("donnees_cles", [])
            notes = [src.get("note", ""), src.get("note_conflit", ""),
                     src.get("note_source_donnees_cles", "")]
            notes = [n for n in notes if n]

            # Badge statut verification
            if "reference" in sv:
                sv_css, sv_label = "sv-ok", "Reference validee"
            elif "en attente" in sv:
                sv_css, sv_label = "sv-wait", "En attente"
            else:
                sv_css, sv_label = "sv-warn", "A valider"

            # Liens
            pdf_rel  = pdf_principal(src)
            xlsx_rel = xlsx_principal(src)
            meta_rel = src.get("fichier_metadata") or src.get("fichier_texte_extrait")
            txt_rel  = src.get("fichier_texte_extrait")
            web_urls = urls_source(src)

            liens_html = '<div class="liens-row">'
            # PDF
            if pdf_rel:
                pdf_abs = BASE_DIR / pdf_rel
                if pdf_abs.exists():
                    liens_html += (f'<a href="{pdf_abs.as_uri()}" class="lien-btn pdf-btn" target="_blank">'
                                   f'&#128196; Ouvrir PDF</a>')
                else:
                    liens_html += (f'<span class="lien-btn pdf-btn absent">'
                                   f'&#128196; PDF absent : {esc(Path(pdf_rel).name)}</span>')
            # Excel
            if xlsx_rel:
                xlsx_abs = BASE_DIR / xlsx_rel
                if xlsx_abs.exists():
                    liens_html += (f'<a href="{xlsx_abs.as_uri()}" class="lien-btn xlsx-btn" target="_blank">'
                                   f'&#128202; Ouvrir Excel (ESS)</a>')
            # URLs web
            for champ, url in web_urls:
                label = {"url_source": "Site source", "url_pdf_direct": "PDF direct",
                         "url_api": "API WDI", "url_country_brief": "Country Brief"}.get(champ, champ)
                liens_html += (f'<a href="{esc(url)}" class="lien-btn web-btn" target="_blank">'
                               f'&#127760; {esc(label)}</a>')
            # Metadata txt
            if meta_rel:
                meta_abs = BASE_DIR / meta_rel
                if meta_abs.exists():
                    liens_html += (f'<a href="{meta_abs.as_uri()}" class="lien-btn meta-btn" target="_blank">'
                                   f'&#128203; Metadata .txt</a>')
            # TXT extrait
            if txt_rel and txt_rel != meta_rel:
                txt_abs = BASE_DIR / txt_rel
                if txt_abs.exists():
                    liens_html += (f'<a href="{txt_abs.as_uri()}" class="lien-btn meta-btn" target="_blank">'
                                   f'&#128202; TXT extrait</a>')
            liens_html += '</div>'

            # Donnees cles
            dk_html = ""
            if dk:
                dk_html = '<ul class="dk-list">'
                for d in dk:
                    css = ""
                    if "[SOURCE_ONLINE" in d:
                        css = "online"
                    elif "[DERIVE" in d:
                        css = "derive"
                    elif "[N/D]" in d or "N/D" == d.strip():
                        css = "attente"
                    dk_html += f'<li class="{css}">{esc(d)}</li>'
                dk_html += "</ul>"

            # Notes
            notes_html = ""
            for n in notes:
                if n:
                    notes_html += f'<div class="note-box">&#9888; {esc(n)}</div>'

            # Construire la carte
            parts.append(f"""
<div class="source-card" id="card-{esc(sid)}" data-cat="{cat_key}" data-id="{esc(sid)}"
     data-titre="{esc(titre.lower())}">
  <div class="source-header" onclick="toggleCard('{esc(sid)}')">
    <div class="cb-wrap">
      <input type="checkbox" id="cb-{esc(sid)}"
             onchange="sauvegarder('{esc(sid)}')"
             onclick="event.stopPropagation()"
             title="Marquer comme verifie">
    </div>
    <div>
      <div class="src-title">{esc(titre)}</div>
      <div class="src-meta">
        <span>&#127970; {esc(org)}</span>
        {'<span>&#128197; ' + str(annee) + '</span>' if annee else ''}
        <span class="statut-verif-badge {sv_css}">{esc(sv_label)}</span>
      </div>
    </div>
    <div class="badges">
      {badge_fiabilite(niv)}
      {badge_type(src)}
    </div>
  </div>
  <div class="source-body" id="body-{esc(sid)}">
    {liens_html}
    {'<p style="font-size:.78rem;color:#888;margin:6px 0 4px"><b>Donnees cles a verifier :</b></p>' + dk_html if dk_html else ''}
    {notes_html}
  </div>
</div>""")

    # JS
    parts.append(f"""
<script>
const TOTAL = {total};

// ── Persistence checkboxes ──────────────────────────────────────────────────
function sauvegarder(id) {{
  const cb = document.getElementById('cb-' + id);
  const card = document.getElementById('card-' + id);
  if (cb.checked) {{
    localStorage.setItem('verif-' + id, '1');
    card.querySelector('.source-header').classList.add('verified');
  }} else {{
    localStorage.removeItem('verif-' + id);
    card.querySelector('.source-header').classList.remove('verified');
  }}
  mettreAJourProgres();
}}

function chargerEtat() {{
  document.querySelectorAll('input[type=checkbox]').forEach(cb => {{
    const id = cb.id.replace('cb-', '');
    if (localStorage.getItem('verif-' + id)) {{
      cb.checked = true;
      const card = document.getElementById('card-' + id);
      if (card) card.querySelector('.source-header').classList.add('verified');
    }}
  }});
  mettreAJourProgres();
}}

function mettreAJourProgres() {{
  const n = document.querySelectorAll('input[type=checkbox]:checked').length;
  const pct = Math.round(n / TOTAL * 100);
  document.getElementById('pbar').style.width = pct + '%';
  document.getElementById('plabel').textContent = n + ' / ' + TOTAL + ' verifiees (' + pct + ' %)';
}}

// ── Toggle body ─────────────────────────────────────────────────────────────
function toggleCard(id) {{
  const body = document.getElementById('body-' + id);
  body.classList.toggle('open');
}}

// ── Filtres ─────────────────────────────────────────────────────────────────
function filtrer() {{
  const cat    = document.getElementById('filter-cat').value;
  const statut = document.getElementById('filter-statut').value;
  const search = document.getElementById('filter-search').value.toLowerCase();

  document.querySelectorAll('.source-card').forEach(card => {{
    const cardCat   = card.dataset.cat || '';
    const cardTitre = card.dataset.titre || '';
    const cardId    = card.dataset.id || '';
    const cb = document.getElementById('cb-' + cardId);
    const isVerif = cb && cb.checked;

    const okCat    = !cat    || cardCat === cat;
    const okStatut = !statut || (statut === 'verifiee' ? isVerif : !isVerif);
    const okSearch = !search || cardTitre.includes(search) || cardId.toLowerCase().includes(search);

    card.classList.toggle('hidden', !(okCat && okStatut && okSearch));
  }});
}}

function resetFiltres() {{
  document.getElementById('filter-cat').value = '';
  document.getElementById('filter-statut').value = '';
  document.getElementById('filter-search').value = '';
  filtrer();
}}

// ── Export CSV ──────────────────────────────────────────────────────────────
function exporterCSV() {{
  const rows = [['ID', 'Titre', 'Organisation', 'Verifie', 'PDF', 'URL']];
  document.querySelectorAll('.source-card').forEach(card => {{
    const id = card.dataset.id;
    const titre = card.dataset.titre;
    const cb = document.getElementById('cb-' + id);
    rows.push([id, titre, '', cb && cb.checked ? 'oui' : 'non', '', '']);
  }});
  const csv = rows.map(r => r.map(c => '"' + String(c).replace(/"/g,'""') + '"').join(',')).join('\\n');
  const blob = new Blob([csv], {{type:'text/csv;charset=utf-8'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'checklist_sources_' + new Date().toISOString().slice(0,10) + '.csv';
  a.click();
}}

// ── Init ─────────────────────────────────────────────────────────────────────
window.addEventListener('load', chargerEtat);
</script>
</div></body></html>""")

    html = "\n".join(parts)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"\n[OK] Checklist generee : {OUTPUT}")
    return OUTPUT

# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sources = lire_registre()
    print(f"[INFO] {len(sources)} sources chargees depuis le registre.\n")

    print("[ETAPE 1] Enrichissement des fichiers metadata...")
    enrichir_metadata(sources)

    print("\n[ETAPE 2] Generation de la checklist HTML...")
    generer_html(sources)
