"""
audit_phase1.py — Audit structurel Phase 1 du Bulletin statistique RDC
=======================================================================
Vérifie :
  1. Liens brisés (href="/files/06_sources/..." → fichier inexistant)
  2. data-val-id dupliqués dans l'ensemble du bulletin
  3. Chiffres dans tableaux Markdown sans annotation data-val-id
  4. Sources dans registre_sources.json avec fichiers manquants
  5. Sources avec sections_citantes vide
  6. Données-clés dans registre_sources.json non retrouvées dans le .txt source
  7. Statut de vérification des sources

Usage :
    python 09_scripts/audit_phase1.py
Produit :
    10_output/AUDIT_Phase1_rapport.html
"""

import os
import re
import json
import html
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ─── Configuration ───────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_JSON = BASE_DIR / "06_sources" / "registre_sources.json"
OUTPUT_REPORT = BASE_DIR / "10_output" / "AUDIT_Phase1_rapport.html"

# Dossiers à scanner pour les fichiers .md
SCAN_DIRS = [
    "00_pilotage",
    "01_pages_preliminaires",
    "02_introduction_generale",
    "03_chapitres",
    "04_annexes",
    "05_references",
    "07_tableaux",
]

# Mapping : /files/ → BASE_DIR (comme dans le serveur de prévisualisation)
FILES_PREFIX = "/files/"

# Regex pour détecter des nombres dans les cellules de tableaux Markdown
# Nombres français : 38 641 / 39 465 / 1 234 567 / 52,4 / 0,8 %
RE_FRENCH_NUMBER = re.compile(
    r'(?<!\w)'                          # pas précédé d'un caractère alphanum
    r'(\d{1,3}(?:[\s\u00a0]\d{3})+)'   # grand nombre avec séparateur espace
    r'|(\d+[,\.]\d+\s*%?)'             # décimal ou pourcentage
    r'|(?<![/\-\d])(\d{4,})(?!\d)'     # 4+ chiffres contigus (années exclues)
    r'(?<![/\-\d])'
)

# Regex pour détecter data-val-id dans du HTML inline
RE_VAL_ID = re.compile(r'data-val-id=["\']([^"\']+)["\']')

# Regex pour détecter href="/files/..."
RE_HREF_FILES = re.compile(r'href=["\'](' + re.escape(FILES_PREFIX) + r'[^"\']+)["\']')

# Regex pour les lignes de tableaux Markdown
RE_TABLE_ROW = re.compile(r'^\s*\|[^|]+\|')
RE_TABLE_SEP  = re.compile(r'^\s*\|[\s\-:|]+\|')

# ─── Collecte des fichiers MD ────────────────────────────────────────────────

def collect_md_files():
    files = []
    for d in SCAN_DIRS:
        scan_path = BASE_DIR / d
        if scan_path.exists():
            for f in scan_path.rglob("*.md"):
                files.append(f)
    return sorted(files)


# ─── Analyse d'un fichier MD ─────────────────────────────────────────────────

def analyze_file(filepath: Path):
    """
    Retourne un dictionnaire avec :
      - val_ids : list[(id, line_no)]
      - broken_links : list[(href, line_no)]
      - unannotated_numbers : list[(number, line_no, row_text)]
    """
    result = {
        "val_ids": [],
        "broken_links": [],
        "unannotated_numbers": [],
    }

    try:
        content = filepath.read_text(encoding="utf-8-sig")
    except Exception as e:
        result["read_error"] = str(e)
        return result

    lines = content.split("\n")
    relative_path = filepath.relative_to(BASE_DIR)

    # ── Analyse ligne par ligne ───────────────────────────────────────────────
    in_table = False
    table_buffer = []   # lignes accumulées pour le bloc de tableau courant

    def flush_table(table_lines, start_line_no):
        """
        Analyse un bloc de tableau accumulé :
        - Si aucune cellule n'a de data-val-id, signale tous les chiffres trouvés
        """
        full_block = "\n".join(t for _, t in table_lines)
        has_annotation = bool(RE_VAL_ID.search(full_block))

        if not has_annotation:
            for (lno, row) in table_lines:
                if RE_TABLE_SEP.match(row):
                    continue  # ligne de séparation --- ignorée
                # Extraire les cellules
                cells = [c.strip() for c in row.split("|") if c.strip()]
                for cell in cells:
                    # Ignorer les cellules qui sont des en-têtes évidents ou [N/D]
                    if cell in ("[N/D]", "N/D", "—", "–", "···", "...", "") :
                        continue
                    if cell.startswith("[") and cell.endswith("]"):
                        continue
                    for m in RE_FRENCH_NUMBER.finditer(cell):
                        num = m.group(0).strip()
                        # Ignorer les années seules (4 chiffres entre 2000 et 2030)
                        try:
                            val = int(num.replace(" ", "").replace("\u00a0", ""))
                            if 2000 <= val <= 2030:
                                continue
                        except ValueError:
                            pass
                        result["unannotated_numbers"].append({
                            "number": num,
                            "line": lno,
                            "row": row[:120],
                        })

    in_code_block = False  # ignorer les blocs de code (``` ... ```)

    for i, line in enumerate(lines, 1):
        # ── Gestion des blocs de code ────────────────────────────────────────
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue  # ignorer tout contenu dans un bloc de code

        # ── data-val-id ─────────────────────────────────────────────────────
        for m in RE_VAL_ID.finditer(line):
            result["val_ids"].append({"id": m.group(1), "line": i})

        # ── href="/files/..." ────────────────────────────────────────────────
        for m in RE_HREF_FILES.finditer(line):
            href = m.group(1)
            # Résoudre le chemin sur disque
            rel_path = href[len(FILES_PREFIX):]  # supprimer le préfixe /files/
            abs_path = BASE_DIR / rel_path
            if not abs_path.exists():
                result["broken_links"].append({
                    "href": href,
                    "expected_path": str(abs_path),
                    "line": i,
                })

        # ── Détection des tableaux Markdown ─────────────────────────────────
        is_table_line = RE_TABLE_ROW.match(line)
        if is_table_line:
            table_buffer.append((i, line))
            in_table = True
        else:
            if in_table and table_buffer:
                flush_table(table_buffer, table_buffer[0][0])
                table_buffer = []
                in_table = False

    # Flush final si le fichier se termine sur un tableau
    if in_table and table_buffer:
        flush_table(table_buffer, table_buffer[0][0])

    return result


# ─── Analyse du registre sources ─────────────────────────────────────────────

def analyze_sources_json():
    issues = {
        "missing_pdf": [],
        "missing_txt": [],
        "empty_sections_citantes": [],
        "a_valider": [],
        "donnees_cles_not_in_txt": [],
        "donnees_source_online": [],   # données sourcées en ligne, vérification manuelle
    }

    if not SOURCES_JSON.exists():
        return issues, []

    with open(SOURCES_JSON, encoding="utf-8") as f:
        data = json.load(f)

    sources = data.get("sources", [])

    for src in sources:
        sid = src.get("id", "?")
        titre = src.get("titre", "")[:80]

        # PDF manquant
        pdf = src.get("fichier_pdf")
        if pdf:
            pdf_path = BASE_DIR / pdf
            if not pdf_path.exists():
                issues["missing_pdf"].append({"id": sid, "titre": titre, "path": pdf})

        # Texte extrait manquant
        txt = src.get("fichier_texte_extrait")
        if txt:
            txt_path = BASE_DIR / txt
            if not txt_path.exists():
                issues["missing_txt"].append({"id": sid, "titre": titre, "path": txt})

        # sections_citantes vide
        sc = src.get("sections_citantes", [])
        if not sc:
            issues["empty_sections_citantes"].append({"id": sid, "titre": titre})

        # Statut à valider
        statut = src.get("statut_verification", "")
        if statut == "à valider":
            issues["a_valider"].append({"id": sid, "titre": titre})

        # Vérification donnees_cles dans le .txt source
        if txt:
            txt_path = BASE_DIR / txt
            if txt_path.exists():
                try:
                    txt_content = txt_path.read_text(encoding="utf-8-sig", errors="replace").lower()
                except Exception:
                    txt_content = ""
                donnees = src.get("donnees_cles", [])
                for dk in donnees:
                    # Collecter les données SOURCE_ONLINE pour rapport séparé
                    if "[SOURCE_ONLINE" in dk:
                        issues["donnees_source_online"].append({
                            "id": sid,
                            "donnee": dk[:120],
                            "url": src.get("url_source", ""),
                        })
                        continue
                    # Ignorer les données dérivées/calculées
                    if ("[DÉRIVÉ" in dk or "[derive" in dk.lower() or
                            "[calcul" in dk.lower()):
                        continue
                    # Extraire les chiffres de la donnée-clé en ignorant les années (2000-2030)
                    nums = re.findall(r'\b\d[\d\s,\.]+\b', dk)
                    # Filtrer : ignorer les nombres qui sont des années seules
                    significant_nums = []
                    for n in nums:
                        n_clean = n.replace(" ", "").replace(",", ".").strip(".")
                        try:
                            val = float(n_clean)
                            if 2000 <= val <= 2030 and "." not in n_clean:
                                continue  # c'est une année → ignorer
                        except (ValueError, TypeError):
                            pass
                        significant_nums.append(n_clean)
                    if not significant_nums:
                        continue
                    # Prendre le premier nombre significatif (non-année)
                    num_clean = significant_nums[0]
                    # Recherche dans le texte source (valeur exacte ou avec virgule/point)
                    if (num_clean and
                        num_clean not in txt_content and
                        num_clean.replace(".", ",") not in txt_content):
                        issues["donnees_cles_not_in_txt"].append({
                            "id": sid,
                            "donnee": dk[:100],
                            "nombre_recherche": num_clean,
                            "fichier_txt": txt,
                        })

    return issues, sources


# ─── Génération du rapport HTML ──────────────────────────────────────────────

def esc(s):
    return html.escape(str(s))

def make_badge(count, label, color):
    c = "🔴" if count > 0 else "🟢"
    return f'<span class="badge" style="background:{color}">{c} {count} {label}</span>'

def render_html(
    all_val_ids: dict,   # filepath → list of {id, line}
    broken_links: dict,  # filepath → list of {href, line}
    unannotated: dict,   # filepath → list of {number, line, row}
    src_issues: dict,
    sources: list,
    md_files: list,
):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Calculs globaux ───────────────────────────────────────────────────────
    # Doublons de data-val-id
    global_ids = defaultdict(list)
    for fp, ids in all_val_ids.items():
        for item in ids:
            global_ids[item["id"]].append({"file": fp, "line": item["line"]})
    duplicates = {k: v for k, v in global_ids.items() if len(v) > 1}

    total_val_ids = sum(len(v) for v in all_val_ids.values())
    total_broken = sum(len(v) for v in broken_links.values())
    total_unannotated = sum(len(v) for v in unannotated.values())
    total_dupes = len(duplicates)
    total_missing_pdf = len(src_issues["missing_pdf"])
    total_missing_txt = len(src_issues["missing_txt"])
    total_empty_sc = len(src_issues["empty_sections_citantes"])
    total_a_valider = len(src_issues["a_valider"])
    total_dk_issues = len(src_issues["donnees_cles_not_in_txt"])

    total_issues = total_broken + total_unannotated + total_dupes + total_missing_pdf + total_missing_txt + total_dk_issues

    # ── HTML ─────────────────────────────────────────────────────────────────
    parts = []
    parts.append(f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Audit Phase 1 — Bulletin RDC {now}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin:0; background:#f4f6f9; color:#222; }}
  header {{ background:#1a3a5c; color:#fff; padding:24px 40px; }}
  header h1 {{ margin:0; font-size:1.4rem; }}
  header p {{ margin:4px 0 0; opacity:.75; font-size:.9rem; }}
  .container {{ max-width:1100px; margin:0 auto; padding:32px 24px; }}
  .dashboard {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:16px; margin-bottom:40px; }}
  .card {{ background:#fff; border-radius:8px; padding:20px; box-shadow:0 1px 4px rgba(0,0,0,.08); text-align:center; }}
  .card .number {{ font-size:2.2rem; font-weight:700; margin:4px 0; }}
  .card .label {{ font-size:.8rem; color:#666; }}
  .card.ok .number {{ color:#1a7a3a; }}
  .card.warn .number {{ color:#d4820a; }}
  .card.err .number {{ color:#c0392b; }}
  .section {{ background:#fff; border-radius:8px; padding:24px; margin-bottom:28px; box-shadow:0 1px 4px rgba(0,0,0,.08); }}
  .section h2 {{ margin-top:0; font-size:1.1rem; border-bottom:2px solid #e8edf2; padding-bottom:8px; }}
  .section h2 .ico {{ margin-right:6px; }}
  table {{ width:100%; border-collapse:collapse; font-size:.85rem; }}
  th {{ background:#f0f4f8; text-align:left; padding:8px 10px; font-weight:600; }}
  td {{ padding:7px 10px; border-bottom:1px solid #eee; vertical-align:top; }}
  tr:hover td {{ background:#fafbfc; }}
  code {{ background:#f0f0f0; padding:1px 5px; border-radius:3px; font-size:.82rem; word-break:break-all; }}
  .badge-ok {{ color:#1a7a3a; font-weight:700; }}
  .badge-err {{ color:#c0392b; font-weight:700; }}
  .tag {{ display:inline-block; padding:2px 7px; border-radius:10px; font-size:.75rem; font-weight:600; }}
  .tag-err {{ background:#fde8e8; color:#c0392b; }}
  .tag-warn {{ background:#fef3e2; color:#d4820a; }}
  .tag-ok {{ background:#e8f5e9; color:#1a7a3a; }}
  .tag-info {{ background:#e3edf7; color:#1a3a5c; }}
  .summary-bar {{ background:#e8f0fa; border-left:4px solid #1a3a5c; padding:12px 16px; border-radius:4px; margin-bottom:24px; font-size:.95rem; }}
  .collapse-btn {{ cursor:pointer; color:#1a3a5c; text-decoration:underline; font-size:.85rem; }}
  details summary {{ cursor:pointer; padding:4px 0; color:#1a3a5c; font-weight:600; }}
</style>
</head>
<body>
<header>
  <h1>🔍 Audit Phase 1 — Bulletin statistique de la protection sociale en RDC</h1>
  <p>Rapport généré le {now} · {len(md_files)} fichiers .md analysés · {len(sources)} sources dans le registre</p>
</header>
<div class="container">
""")

    # ── Dashboard ──────────────────────────────────────────────────────────
    def card(number, label, kind):
        return f'<div class="card {kind}"><div class="number">{number}</div><div class="label">{label}</div></div>'

    parts.append('<div class="dashboard">')
    parts.append(card(
        f'{"✅" if total_issues==0 else "⚠️"} {total_issues}',
        "problèmes structurels",
        "err" if total_issues > 0 else "ok"
    ))
    parts.append(card(total_val_ids, "annotations data-val-id", "ok" if total_val_ids > 0 else "warn"))
    parts.append(card(total_dupes, "data-val-id dupliqués", "err" if total_dupes > 0 else "ok"))
    parts.append(card(total_broken, "liens brisés", "err" if total_broken > 0 else "ok"))
    parts.append(card(total_unannotated, "chiffres non annotés", "warn" if total_unannotated > 0 else "ok"))
    parts.append(card(total_missing_pdf, "PDF manquants", "err" if total_missing_pdf > 0 else "ok"))
    parts.append(card(total_missing_txt, "TXT manquants", "err" if total_missing_txt > 0 else "ok"))
    parts.append(card(total_empty_sc, "sources sans backlink", "warn"))
    parts.append(card(total_a_valider, "sources à valider (vérif. PDF)", "warn"))
    parts.append(card(total_dk_issues, "données-clés non vérifiables", "warn" if total_dk_issues > 0 else "ok"))
    total_online = len(src_issues.get("donnees_source_online", []))
    parts.append(card(total_online, "données à vérifier en ligne", "warn" if total_online > 0 else "ok"))
    parts.append('</div>')

    # ── Barre résumé ──────────────────────────────────────────────────────
    if total_issues == 0:
        parts.append('<div class="summary-bar">✅ <strong>Aucun problème structurel détecté.</strong> La chaîne de traçabilité est intacte.</div>')
    else:
        parts.append(f'<div class="summary-bar">⚠️ <strong>{total_issues} problèmes identifiés</strong> nécessitant attention avant publication. Détail ci-dessous.</div>')

    # ── Section 1 : Liens brisés ──────────────────────────────────────────
    parts.append('<div class="section"><h2><span class="ico">🔗</span> 1. Liens brisés (source-ref href introuvables sur disque)</h2>')
    if total_broken == 0:
        parts.append('<p class="badge-ok">✅ Aucun lien brisé détecté.</p>')
    else:
        parts.append(f'<p class="badge-err">⛔ {total_broken} lien(s) brisé(s)</p>')
        parts.append('<table><tr><th>Fichier .md</th><th>Ligne</th><th>Lien href</th><th>Chemin attendu</th></tr>')
        for fp, items in broken_links.items():
            for it in items:
                rel = Path(fp).relative_to(BASE_DIR)
                parts.append(f'<tr><td><code>{esc(rel)}</code></td><td>{it["line"]}</td>'
                             f'<td><code>{esc(it["href"])}</code></td>'
                             f'<td><code>{esc(it["expected_path"])}</code> <span class="tag tag-err">ABSENT</span></td></tr>')
        parts.append('</table>')
    parts.append('</div>')

    # ── Section 2 : data-val-id dupliqués ────────────────────────────────
    parts.append('<div class="section"><h2><span class="ico">🔁</span> 2. data-val-id dupliqués (unicité requise)</h2>')
    if total_dupes == 0:
        parts.append('<p class="badge-ok">✅ Tous les data-val-id sont uniques.</p>')
    else:
        parts.append(f'<p class="badge-err">⛔ {total_dupes} identifiant(s) dupliqué(s)</p>')
        parts.append('<table><tr><th>data-val-id</th><th>Occurrences</th></tr>')
        for vid, occurrences in sorted(duplicates.items()):
            locs = " · ".join(
                f'<code>{esc(Path(o["file"]).relative_to(BASE_DIR))}:{o["line"]}</code>'
                for o in occurrences
            )
            parts.append(f'<tr><td><code>{esc(vid)}</code></td><td>{locs}</td></tr>')
        parts.append('</table>')
    parts.append('</div>')

    # ── Section 3 : Chiffres non annotés ─────────────────────────────────
    parts.append('<div class="section"><h2><span class="ico">🔢</span> 3. Chiffres dans tableaux Markdown sans annotation data-val-id</h2>')
    parts.append('<p style="color:#666;font-size:.85rem">Un chiffre dans un tableau qui n\'est entouré d\'aucun <code>&lt;span class="val"&gt;</code> ou <code>&lt;a class="source-ref"&gt;</code> ne peut pas être tracé jusqu\'à sa source. Risque d\'hallucination non détectable.</p>')
    if total_unannotated == 0:
        parts.append('<p class="badge-ok">✅ Tous les chiffres dans les tableaux sont annotés.</p>')
    else:
        parts.append(f'<p class="badge-err">⚠️ {total_unannotated} chiffre(s) non annoté(s) dans des tableaux</p>')
        for fp, items in unannotated.items():
            if not items:
                continue
            rel = Path(fp).relative_to(BASE_DIR)
            parts.append(f'<details><summary>{esc(rel)} — {len(items)} chiffre(s)</summary>')
            parts.append('<table><tr><th>Ligne</th><th>Valeur</th><th>Extrait de la ligne</th></tr>')
            for it in items:
                parts.append(f'<tr><td>{it["line"]}</td><td><strong>{esc(it["number"])}</strong></td>'
                             f'<td><code>{esc(it["row"])}</code></td></tr>')
            parts.append('</table></details>')
    parts.append('</div>')

    # ── Section 4 : Sources — fichiers manquants ──────────────────────────
    parts.append('<div class="section"><h2><span class="ico">📄</span> 4. Fichiers sources manquants (PDF ou TXT)</h2>')
    if total_missing_pdf == 0 and total_missing_txt == 0:
        parts.append('<p class="badge-ok">✅ Tous les fichiers référencés dans le registre sont présents sur disque.</p>')
    else:
        if total_missing_pdf > 0:
            parts.append(f'<p class="badge-err">⛔ {total_missing_pdf} PDF manquant(s)</p>')
            parts.append('<table><tr><th>ID source</th><th>Titre</th><th>Chemin attendu</th></tr>')
            for s in src_issues["missing_pdf"]:
                parts.append(f'<tr><td><code>{esc(s["id"])}</code></td><td>{esc(s["titre"])}</td>'
                             f'<td><code>{esc(s["path"])}</code> <span class="tag tag-err">ABSENT</span></td></tr>')
            parts.append('</table>')
        if total_missing_txt > 0:
            parts.append(f'<p class="badge-err">⛔ {total_missing_txt} TXT manquant(s)</p>')
            parts.append('<table><tr><th>ID source</th><th>Titre</th><th>Chemin attendu</th></tr>')
            for s in src_issues["missing_txt"]:
                parts.append(f'<tr><td><code>{esc(s["id"])}</code></td><td>{esc(s["titre"])}</td>'
                             f'<td><code>{esc(s["path"])}</code> <span class="tag tag-err">ABSENT</span></td></tr>')
            parts.append('</table>')
    parts.append('</div>')

    # ── Section 5 : Sources sans backlink ─────────────────────────────────
    parts.append('<div class="section"><h2><span class="ico">🔀</span> 5. Sources sans sections_citantes (backlink manquant)</h2>')
    parts.append('<p style="color:#666;font-size:.85rem">Ces sources sont dans le registre mais aucun fichier de chapitre ne les référence explicitement dans le champ <code>sections_citantes</code>. Elles sont peut-être utilisées sans backlink, ou inutilisées.</p>')
    if total_empty_sc == 0:
        parts.append('<p class="badge-ok">✅ Toutes les sources ont au moins un backlink.</p>')
    else:
        parts.append(f'<p style="color:#d4820a">⚠️ {total_empty_sc} source(s) sans backlink</p>')
        parts.append('<table><tr><th>ID</th><th>Titre</th></tr>')
        for s in src_issues["empty_sections_citantes"]:
            parts.append(f'<tr><td><code>{esc(s["id"])}</code></td><td>{esc(s["titre"])}</td></tr>')
        parts.append('</table>')
    parts.append('</div>')

    # ── Section 6 : Données-clés non vérifiables ──────────────────────────
    parts.append('<div class="section"><h2><span class="ico">🔍</span> 6. Données-clés du registre non retrouvées dans le fichier TXT source</h2>')
    parts.append('<p style="color:#666;font-size:.85rem">Chaque <code>donnees_cles</code> du registre devrait contenir un chiffre retrouvable dans le fichier <code>.txt</code> extrait correspondant. Si ce n\'est pas le cas, la donnée-clé a peut-être été mal transcrite ou hallucin&eacute;e.</p>')
    if total_dk_issues == 0:
        parts.append('<p class="badge-ok">✅ Toutes les données-clés vérifiables ont été retrouvées dans leurs sources .txt.</p>')
    else:
        parts.append(f'<p class="badge-err">⚠️ {total_dk_issues} donnée(s)-clé(s) non retrouvée(s) dans le fichier TXT source</p>')
        parts.append('<table><tr><th>Source</th><th>Donnée-clé</th><th>Nombre cherché</th><th>Fichier TXT</th></tr>')
        for it in src_issues["donnees_cles_not_in_txt"]:
            parts.append(f'<tr><td><code>{esc(it["id"])}</code></td>'
                        f'<td>{esc(it["donnee"])}</td>'
                        f'<td><code>{esc(it["nombre_recherche"])}</code></td>'
                        f'<td><code>{esc(it["fichier_txt"])}</code></td></tr>')
        parts.append('</table>')
    parts.append('</div>')

    # ── Section 6b : Données sourcées en ligne (vérification manuelle) ────
    total_online = len(src_issues.get("donnees_source_online", []))
    parts.append('<div class="section"><h2><span class="ico">🌐</span> 6b. Données-clés sourcées en ligne (vérification manuelle requise)</h2>')
    parts.append('<p style="color:#666;font-size:.85rem">Ces données-clés sont marquées <code>[SOURCE_ONLINE]</code> : elles proviennent de bases de données en ligne (FAOSTAT, WPP portail, wfp.org…) et non d\'un PDF local. Le PDF associé dans le registre est un document de référence contextuel, pas la source directe du chiffre. <strong>Vérification humaine en ligne requise avant publication.</strong></p>')
    if total_online == 0:
        parts.append('<p class="badge-ok">✅ Aucune donnée-clé sourcée uniquement en ligne.</p>')
    else:
        parts.append(f'<p style="color:#d4820a">⚠️ {total_online} donnée(s)-clé(s) à vérifier directement en ligne</p>')
        parts.append('<table><tr><th>Source</th><th>Donnée-clé</th><th>URL à consulter</th></tr>')
        for it in src_issues["donnees_source_online"]:
            url = it.get("url", "")
            url_link = f'<a href="{esc(url)}" target="_blank">{esc(url[:60])}</a>' if url else "—"
            parts.append(f'<tr><td><code>{esc(it["id"])}</code></td>'
                        f'<td>{esc(it["donnee"][:100])}</td>'
                        f'<td>{url_link}</td></tr>')
        parts.append('</table>')
    parts.append('</div>')

    # ── Section 7 : Sources à valider ────────────────────────────────────
    parts.append('<div class="section"><h2><span class="ico">✔️</span> 7. Sources avec statut_verification "à valider"</h2>')
    parts.append(f'<p style="color:#d4820a">⚠️ {total_a_valider} source(s) sur {len(sources)} n\'ont pas encore été formellement vérifiées contre leur PDF d\'origine.</p>')
    parts.append('<table><tr><th>ID</th><th>Titre</th></tr>')
    for s in src_issues["a_valider"]:
        parts.append(f'<tr><td><code>{esc(s["id"])}</code></td><td>{esc(s["titre"])}</td></tr>')
    parts.append('</table>')
    parts.append('</div>')

    # ── Section 8 : Inventaire des annotations ────────────────────────────
    parts.append('<div class="section"><h2><span class="ico">📋</span> 8. Inventaire complet des annotations par fichier</h2>')
    parts.append('<table><tr><th>Fichier</th><th>data-val-id</th><th>Liens sources</th><th>Chiffres non annotés</th></tr>')
    for fp in sorted(all_val_ids.keys()):
        rel = Path(fp).relative_to(BASE_DIR)
        n_ids = len(all_val_ids.get(fp, []))
        n_links = sum(1 for _ in broken_links.get(fp, []))  # seulement les brisés — à améliorer
        # Compte total des liens (brisés + valides) : refaire la recherche
        try:
            txt = Path(fp).read_text(encoding="utf-8-sig")
            n_total_links = len(RE_HREF_FILES.findall(txt))
        except Exception:
            n_total_links = "?"
        n_unann = len(unannotated.get(fp, []))
        unann_tag = f'<span class="tag tag-err">{n_unann}</span>' if n_unann > 0 else '<span class="tag tag-ok">0</span>'
        parts.append(f'<tr><td><code>{esc(rel)}</code></td>'
                    f'<td>{n_ids}</td>'
                    f'<td>{n_total_links}</td>'
                    f'<td>{unann_tag}</td></tr>')
    parts.append('</table>')
    parts.append('</div>')

    # ── Pied de page ──────────────────────────────────────────────────────
    parts.append(f"""
<div style="text-align:center;color:#999;font-size:.8rem;margin-top:40px;padding-bottom:40px">
  Rapport généré automatiquement par <code>09_scripts/audit_phase1.py</code><br>
  Bulletin statistique de la protection sociale en RDC — {now}
</div>
</div></body></html>""")

    return "\n".join(parts)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("AUDIT PHASE 1 - Bulletin statistique RDC")
    print("=" * 60)

    # Collecter les fichiers
    md_files = collect_md_files()
    print(f"\n[INFO] {len(md_files)} fichiers .md trouves\n")

    all_val_ids = {}
    broken_links = {}
    unannotated = {}

    for fp in md_files:
        rel = fp.relative_to(BASE_DIR)
        print(f"  -> {rel}")
        result = analyze_file(fp)
        key = str(fp)
        all_val_ids[key] = result.get("val_ids", [])
        broken_links[key] = result.get("broken_links", [])
        unannotated[key] = result.get("unannotated_numbers", [])
        if result.get("read_error"):
            print(f"     [ERREUR] Lecture : {result['read_error']}")

    print(f"\n[INFO] Analyse du registre sources...")
    src_issues, sources = analyze_sources_json()

    print(f"\n[SYNTHESE]")
    total_val_ids = sum(len(v) for v in all_val_ids.values())
    total_broken = sum(len(v) for v in broken_links.values())
    total_unann = sum(len(v) for v in unannotated.values())

    # Doublons
    global_ids = defaultdict(list)
    for fp, ids in all_val_ids.items():
        for item in ids:
            global_ids[item["id"]].append(fp)
    duplicates = {k: v for k, v in global_ids.items() if len(v) > 1}

    print(f"   data-val-id annotes     : {total_val_ids}")
    print(f"   data-val-id dupliques   : {len(duplicates)}")
    print(f"   Liens brises            : {total_broken}")
    print(f"   Chiffres non annotes    : {total_unann}")
    print(f"   Sources (registre)      : {len(sources)}")
    print(f"   PDF manquants           : {len(src_issues['missing_pdf'])}")
    print(f"   TXT manquants           : {len(src_issues['missing_txt'])}")
    print(f"   Donnees-cles non verib. : {len(src_issues['donnees_cles_not_in_txt'])}")

    # Générer le rapport
    print(f"\n[INFO] Generation du rapport HTML...")
    report_html = render_html(all_val_ids, broken_links, unannotated, src_issues, sources, md_files)
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(report_html, encoding="utf-8")
    print(f"\n[OK] Rapport ecrit : {OUTPUT_REPORT}")
    print("=" * 60)


if __name__ == "__main__":
    main()
