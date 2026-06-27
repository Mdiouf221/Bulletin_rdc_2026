"""
annoter_tableaux_ch4.py — Annotation automatique des chiffres dans les tableaux du Chapitre 4
===============================================================================================
Pour chaque tableau Markdown sans data-val-id :
  1. Ajoute un lien source-ref dans la légende du tableau (source ESS par institution/année)
  2. Wraps chaque valeur numérique dans <span class="val" data-val-id="...">

Convention data-val-id : s<section>-t<table_num>-d<seq>
Exemple : s42-t1-d1 = section 4.2, tableau 1, donnée 1

Usage : py -3 09_scripts/annoter_tableaux_ch4.py
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Fichiers cibles avec leur préfixe de section
TARGETS = [
    ("03_chapitres/chapitre_4/4.2_vieillesse.md",       "s42"),
    ("03_chapitres/chapitre_4/4.3_age_actif.md",         "s43"),
    ("03_chapitres/chapitre_4/4.4_enfants_familles.md",  "s44"),
    ("03_chapitres/chapitre_4/4.5_invalidite.md",        "s45"),
    ("03_chapitres/chapitre_4/4.6_deces_survie.md",      "s46"),
    ("03_chapitres/chapitre_4/4.8_depenses_financement.md", "s48"),
    ("03_chapitres/chapitre_5/00_plan_chapitre_5.md",    "s5"),
]

# ─── Mapping institution × année → fichier TXT source ────────────────────────

ESS_SOURCES = {
    ("CNSS",   2019): "06_sources/ESS/ESS_CNSS/_texte/ESS_CNSS_2019.txt",
    ("CNSS",   2020): "06_sources/ESS/ESS_CNSS/_texte/ESS_CNSS_2020.txt",
    ("CNSS",   2021): "06_sources/ESS/ESS_CNSS/_texte/ESS_CNSS_2021.txt",
    ("CNSS",   2022): "06_sources/ESS/ESS_CNSS/_texte/ESS_CNSS_2022.txt",
    ("CNSSAP", 2020): "06_sources/ESS/ESS_CNSSAP/_texte/ESS_CNSSAP_2020.txt",
    ("CNSSAP", 2021): "06_sources/ESS/ESS_CNSSAP/_texte/ESS_CNSSAP_2021.txt",
    ("CNSSAP", 2022): "06_sources/ESS/ESS_CNSSAP/_texte/ESS_CNSSAP_2022.txt",
}

# Source par défaut (ESS multi-régimes) pour les tableaux sans institution claire
ESS_DEFAULT = "06_sources/ESS/ESS_RDC_tous_regimes/_texte/ESS_RDC_tous_regimes.txt"

# ─── Regex ───────────────────────────────────────────────────────────────────

RE_TABLE_ROW = re.compile(r'^\s*\|[^|]+\|')
RE_TABLE_SEP = re.compile(r'^\s*\|[\s\-:|]+\|')
RE_VAL_ID    = re.compile(r'data-val-id=')
RE_CAPTION   = re.compile(r'<p class="table-caption"><strong>(Tableau\s*[\d\.]+)</strong>')

# Détecte les nombres à annoter dans une cellule
# Exclut : [N/D], [ESS XXXX], [contexte_macro], zéro seul (sauf contexte spécifique)
RE_NUMBER_IN_CELL = re.compile(
    r'(?<!\w)(?<!\[)'
    r'('
    r'\d{1,3}(?:[\s\u00a0]\d{3})+'   # grand nombre avec séparateur espace
    r'|'
    r'\d+[,\.]\d+(?:\s*(?:Mds\s+)?CDF|%)?'  # décimal / montant / pourcentage
    r'|'
    r'\d{3,}(?!\d)'                   # 3+ chiffres contigus (pas 1 ou 2 seuls)
    r')'
    r'(?!\d)(?!\])'
)


def is_placeholder(cell: str) -> bool:
    """Retourne True si la cellule est un placeholder à ne pas annoter."""
    stripped = cell.strip()
    placeholders = {'[N/D]', 'N/D', '—', '–', '', '---', '...',
                    '[contexte_macro]', '[EST.]', '[WSPR]'}
    if stripped in placeholders:
        return True
    if stripped.startswith('[') and stripped.endswith(']'):
        return True
    return False


def detect_institution(row_cells: list) -> str:
    """Devine l'institution à partir de la première cellule de la ligne."""
    first = row_cells[0].lower() if row_cells else ''
    if 'cnssap' in first:
        return 'CNSSAP'
    if 'cnss' in first:
        return 'CNSS'
    if any(k in first for k in ('fss', 'mesp', 'minas', 'mepst')):
        return 'FSS'
    # Regarder aussi la deuxième cellule
    second = row_cells[1].lower() if len(row_cells) > 1 else ''
    if 'cnssap' in second:
        return 'CNSSAP'
    if 'cnss' in second:
        return 'CNSS'
    return 'CNSS'  # défaut


def get_ess_source(institution: str, year: int) -> str:
    """Retourne le chemin du fichier source ESS pour institution × année."""
    return ESS_SOURCES.get((institution, year), ESS_DEFAULT)


def make_source_link(href: str, title: str, val_id: str, rel_file: str) -> str:
    return (
        f'<a href="/files/{href}" title="{title}" '
        f'class="source-ref source-ref-text nv" '
        f'data-val-id="{val_id}" data-val-status="\u00e0 valider" '
        f'data-val-file="{rel_file}">[src]</a>'
    )


def annotate_number(number: str, val_id: str, rel_file: str) -> str:
    return (
        f'<span class="val" '
        f'data-val-id="{val_id}" data-val-status="\u00e0 valider" '
        f'data-val-file="{rel_file}">{number}</span>'
    )


def annotate_table_block(
    table_lines: list,
    caption_index: int,  # index dans lines[] de la ligne de légende
    section_prefix: str,
    table_seq: int,      # numéro séquentiel du tableau dans la section
    data_counter: list,  # [int] — compteur partagé de données (mutable)
    rel_file: str,
    result_lines: list,  # liste de lignes du fichier à modifier
):
    """
    Annote un bloc de tableau (table_lines = liste de (abs_index, text)).
    Modifie result_lines en place.
    """
    if not table_lines:
        return

    # ── Vérifier si déjà annoté ──────────────────────────────────────────────
    full_block = '\n'.join(t for _, t in table_lines)
    if RE_VAL_ID.search(full_block):
        return  # déjà annoté — sauter

    # ── Extraire la ligne d'en-tête pour détecter les colonnes année ─────────
    header_row = None
    sep_row = None
    year_cols = {}  # col_index → year (int)

    for i, (_, line) in enumerate(table_lines):
        if RE_TABLE_SEP.match(line):
            sep_row = i
        elif header_row is None and RE_TABLE_ROW.match(line):
            header_row = i
            # Extraire les colonnes
            cells = [c.strip() for c in line.split('|')]
            cells = [c for c in cells if c != '']  # retirer les vides de début/fin
            for ci, cell in enumerate(cells):
                m = re.search(r'\b(20\d{2})\b', cell)
                if m:
                    year_cols[ci] = int(m.group(1))
            break

    # ── Ajouter source-ref dans la légende du tableau ─────────────────────────
    if caption_index is not None and caption_index < len(result_lines):
        caption_line = result_lines[caption_index]
        if '[src]' not in caption_line and 'source-ref' not in caption_line:
            # Déterminer la source principale : ESS CNSS 2022 par défaut
            href = get_ess_source('CNSS', 2022)
            src_link = make_source_link(
                href,
                "Source : ESS OIT — tableaux statistiques standardises",
                f"{section_prefix}-t{table_seq}-src",
                rel_file
            )
            # Insérer le lien avant la fermeture </p>
            result_lines[caption_index] = caption_line.replace('</p>', f' {src_link}</p>')

    # ── Annoter les cellules ─────────────────────────────────────────────────
    for abs_idx, line in table_lines:
        if RE_TABLE_SEP.match(line):
            continue  # ligne de séparation — ignorer
        if header_row is not None and line == table_lines[header_row][1]:
            continue  # ligne d'en-tête — ignorer

        # Découper la ligne en cellules
        parts = line.split('|')
        # parts[0] = texte avant le premier |, parts[-1] = texte après le dernier |
        # Les cellules effectives sont parts[1:-1]
        cells = parts[1:-1]
        if not cells:
            continue

        # Détecter l'institution depuis cette ligne
        row_cells = [c.strip() for c in cells]
        institution = detect_institution(row_cells)

        # Trouver les colonnes année pour cette ligne
        # L'index de colonne dans row_cells commence à 0
        # Correspondance : ci (dans year_cols) → ci dans row_cells
        annotated_cells = []
        for ci, cell in enumerate(cells):
            cell_stripped = cell.strip()
            if is_placeholder(cell_stripped):
                annotated_cells.append(cell)
                continue

            # Détecter si c'est une colonne année
            year = year_cols.get(ci)  # None si pas une colonne année

            # Chercher des nombres à annoter dans la cellule
            def replace_number(m):
                number = m.group(1) or m.group(0)
                # Ignorer les années seules (ex : 2019, 2020...)
                try:
                    val = int(number.replace(' ', '').replace('\u00a0', '').replace(',', '').replace('.', ''))
                    if 2000 <= val <= 2030:
                        return m.group(0)
                except (ValueError, AttributeError):
                    pass
                # Générer l'ID
                data_counter[0] += 1
                val_id = f"{section_prefix}-t{table_seq}-d{data_counter[0]}"
                return annotate_number(m.group(0), val_id, rel_file)

            new_cell = RE_NUMBER_IN_CELL.sub(replace_number, cell)
            annotated_cells.append(new_cell)

        # Reconstruire la ligne
        new_line = '|' + '|'.join(annotated_cells) + '|'
        # Préserver l'indentation initiale
        leading = line[:len(line) - len(line.lstrip())]
        if line.lstrip().startswith('|'):
            result_lines[abs_idx] = leading + new_line
        else:
            result_lines[abs_idx] = new_line


# ─── Traitement principal ─────────────────────────────────────────────────────

def process_file(rel_path: str, section_prefix: str):
    filepath = BASE_DIR / rel_path
    if not filepath.exists():
        print(f"  [SKIP] Fichier introuvable : {rel_path}")
        return 0

    content = filepath.read_text(encoding='utf-8-sig')
    lines = content.split('\n')
    result_lines = list(lines)

    # État du parseur
    in_table = False
    table_buffer = []  # list of (abs_index, text)
    last_caption_idx = None  # index de la dernière légende de tableau vue
    table_seq = 0
    data_counter = [0]
    annotations_added = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Détecter une légende de tableau
        if RE_CAPTION.search(line):
            last_caption_idx = i

        # Détecter les lignes de tableau
        if RE_TABLE_ROW.match(line):
            table_buffer.append((i, line))
            in_table = True
        else:
            if in_table and table_buffer:
                # Fin du bloc de tableau
                table_seq += 1
                # Sauvegarder le compte avant
                before = data_counter[0]
                annotate_table_block(
                    table_buffer,
                    last_caption_idx,
                    section_prefix,
                    table_seq,
                    data_counter,
                    rel_path,
                    result_lines,
                )
                annotations_added += data_counter[0] - before
                table_buffer = []
                in_table = False
                last_caption_idx = None  # reset après utilisation
        i += 1

    # Flush final
    if in_table and table_buffer:
        table_seq += 1
        before = data_counter[0]
        annotate_table_block(
            table_buffer, last_caption_idx, section_prefix, table_seq,
            data_counter, rel_path, result_lines,
        )
        annotations_added += data_counter[0] - before

    # Écrire le fichier modifié (seulement si des changements ont été faits)
    new_content = '\n'.join(result_lines)
    if new_content != content:
        filepath.write_text(new_content, encoding='utf-8-sig')
        print(f"  [OK] {rel_path} — {annotations_added} annotation(s) ajoutee(s)")
    else:
        print(f"  [--] {rel_path} — aucun changement")

    return annotations_added


def main():
    print("=" * 60)
    print("ANNOTATION CH4 - Bulletin statistique RDC")
    print("=" * 60)
    total = 0
    for rel_path, prefix in TARGETS:
        print(f"\n-> {rel_path}")
        total += process_file(rel_path, prefix)
    print(f"\nTotal : {total} annotation(s) ajoutee(s)")
    print("=" * 60)
    print("Relancer audit_phase1.py pour verifier le resultat.")


if __name__ == "__main__":
    main()
