"""Graphiques Excel du corps du bulletin, sans Office.

Appeler ``preparer_graphiques(html_brut, chemin_xlsx)`` AVANT la réécriture
des chemins /files/ et des liens source. Fusionner les dictionnaires
``workbooks`` et ``source_map`` retournés avec ceux de l'exporteur, et
signaler les ``avertissements`` (les images non reconnues restent en PNG).
Les index de ChartObject sont en base 1. Pour des liens Word persistants,
choisir un chemin de classeur stable.

CLI : py 09_scripts\\graphiques_word_hors_annexes.py bulletin.html sortie.xlsx
"""
import csv
import json
import math
import os
from pathlib import Path
from uuid import uuid4

from lxml import html as lhtml
import xlsxwriter


ROOT = Path(__file__).resolve().parents[1]
DATA = Path("08_figures", "donnees")
KEY = "hors_annexes"
# Clés exactes : la numérotation éditoriale diverge des noms PNG après 1.2.
FIGURES = {
    "FIG_1_population_totale_urbaine_rurale_1950_2025.png": ("1",),
    "FIG_2_structure_age_2025.png": ("2",),
    "FIG_4_croissance_PIB_2000_2024.png": ("4",),
    "FIG_5_emploi_informel_par_sexe.png": ("5a", "5b"),
    "FIG_6_structure_emploi_secteurs.png": ("6",),
}
# Feuille, radical CSV, titre, unité, colonnes et libellés des séries.
PANELS = {
    "1": ("Fig 1.1", "population_totale_urbaine_rurale", "Population totale, urbaine et rurale (1950–2025)",
          "Millions de personnes", "annee population_totale_millions population_urbaine_millions population_rurale_millions",
          ("Année", "Totale", "Urbaine", "Rurale")),
    "2": ("Fig 1.2", "pyramide_ages_par_sexe", "Pyramide des âges (2025)",
          "Milliers de personnes", "tranche_age hommes_milliers femmes_milliers", ("Âge", "Hommes", "Femmes")),
    "4": ("Fig 1.3", "croissance_pib", "Croissance annuelle du PIB réel (2000–2024)",
          "%", "annee taux_croissance_pib_pct", ("Année", "Croissance")),
    "5a": ("Fig 1.4a", "taux_activite_par_sexe", "Taux d’activité et d’inactivité (2023)",
           "% de la population de 15 ans et plus", "categorie taux_activite_pct taux_inactivite_pct",
           ("Sexe", "Actifs", "Inactifs")),
    "5b": ("Fig 1.4b", "emploi_informel_par_sexe", "Emploi informel et formel (2020)",
           "% de l’emploi total", "categorie emploi_informel_pct emploi_formel_pct", ("Sexe", "Informel", "Formel")),
    "6": ("Fig 1.5", "structure_emploi_par_secteur", "Emploi par secteur (2024)",
          "% de l’emploi total", "secteur ensemble_pct femmes_pct hommes_pct", ("Secteur", "Ensemble", "Femmes", "Hommes")),
}


def _stem(panel):
    return f"fig_intro_{panel}_{PANELS[panel][1]}"


def _read_panel(panel, root):
    stem = _stem(panel)
    path = root / DATA / (stem + ".csv")
    metadata = path.with_name(stem + "_metadata.txt")
    if not metadata.is_file():
        raise ValueError(f"métadonnées absentes : {metadata}")
    columns = PANELS[panel][4].split()
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(line for line in f if not line.startswith("#"))
        if not set(columns) <= set(reader.fieldnames or ()):
            raise ValueError(f"{path.name} : colonnes attendues {columns}")
        rows = []
        seen = set()
        for row in reader:
            category = row[columns[0]]
            if not category or category in seen:
                raise ValueError(f"{path.name} : catégorie vide ou dupliquée ({category})")
            seen.add(category)
            numbers = [float(row[c]) for c in columns[1:]]
            if not all(map(math.isfinite, numbers)):
                raise ValueError(f"{path.name} : valeur non finie ({category})")
            rows.append([int(category) if columns[0] == "annee" else category, *numbers])
        if not rows:
            raise ValueError(f"{path.name} : série vide")
    return rows


def _write_panel(book, panel, rows, header):
    sheet, _, title, unit, _, labels = PANELS[panel]
    ws = book.add_worksheet(sheet)
    ws.write_row(0, 0, labels, header)
    ws.set_column(0, 4, 17)
    ws.freeze_panes(1, 1)
    for r, row in enumerate(rows, 1):
        ws.write_row(r, 0, row)
    n = len(rows)
    if panel == "2":
        # Conserver les effectifs bruts positifs ; seule la série graphique
        # des hommes est inversée. L'unité suit la légende publiée (milliers).
        ws.write(0, 3, "Hommes (axe gauche)", header)
        for r, row in enumerate(rows, 1):
            ws.write_formula(r, 3, f"=-B{r+1}", None, -row[1])
    ws.write(n+2, 0, "Données : " + (DATA / (_stem(panel) + ".csv")).as_posix())
    ws.write(n+3, 0, "Notice : " + (DATA / (_stem(panel) + "_metadata.txt")).as_posix())
    options = {"type": {"1": "line", "2": "bar"}.get(panel, "column")}
    if panel in ("2", "5a", "5b"):
        options["subtype"] = "stacked"
    chart = book.add_chart(options)
    chart.set_title({"name": title})
    chart.set_legend({"position": "bottom"})
    category_range = [sheet, 1, 0, n, 0]
    for col in range(1, len(labels)):
        series_col = 3 if panel == "2" and col == 1 else col
        chart.add_series({"name": [sheet, 0, col], "categories": category_range,
                          "values": [sheet, 1, series_col, n, series_col]})
    if panel == "2":
        chart.set_x_axis({"name": unit, "num_format": "#,##0;#,##0"})
        chart.set_y_axis({"label_position": "low"})
    else:
        chart.set_y_axis({"name": unit})
    if panel == "4":
        # Même convolution centrée et prolongement par zéro que le PNG.
        ws.write(0, 2, "Moyenne mobile 3 ans", header)
        for r in range(n):
            first, last = max(0, r-1), min(n-1, r+1)
            cached = sum(rows[i][1] for i in range(first, last+1)) / 3
            ws.write_formula(r+1, 2, f"=SUM(B{first+2}:B{last+2})/3", None, cached)
        line = book.add_chart({"type": "line"})
        line.add_series({"name": [sheet, 0, 2], "categories": category_range, "values": [sheet, 1, 2, n, 2]})
        chart.combine(line)
    ws.insert_chart("F2", chart)


def preparer_graphiques(html_brut: str, chemin_xlsx, *, root=ROOT) -> dict:
    """Générer seulement les panneaux reconnus. Aucun classeur si mapping vide."""
    doc = lhtml.fromstring(html_brut or "<html/>")
    root = Path(root)
    target = Path(chemin_xlsx).resolve()
    result = {"workbooks": {}, "source_map": {}, "avertissements": []}
    panels = {}
    seen = set()
    for img in doc.xpath(".//img[@src] | self::img[@src]"):
        src = img.get("src").replace("\\", "/")
        filename = src.rsplit("/", 1)[-1]
        if filename.lower().startswith(("annexe_b_", "annexe_c_")):
            continue
        if src in seen:
            continue
        seen.add(src)
        if filename not in FIGURES or src.lstrip("/") not in (
                f"files/08_figures/exports/{filename}", f"08_figures/exports/{filename}"):
            result["avertissements"].append(f"{src} : aucune correspondance sûre avec une source locale.")
            continue
        try:
            data = {p: _read_panel(p, root) for p in FIGURES[filename]}
        except (OSError, ValueError, TypeError, csv.Error) as exc:
            result["avertissements"].append(f"{filename} : graphique non produit ({exc}).")
            continue
        panels.update(data)
        result["source_map"][filename.lower()] = [
            {"workbook_key": KEY, "sheet_name": PANELS[p][0], "chart_index": 1, "image_filename": filename}
            for p in data
        ]
    # L'exporteur référence les images par nom seul : refuser toute collision.
    for name in list(result["source_map"]):
        if sum(src.rsplit("/", 1)[-1].lower() == name for src in seen) > 1:
            result["avertissements"].append(f"{name} : plusieurs chemins HTML, correspondance ambiguë.")
            del result["source_map"][name]
    if result["source_map"]:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            # Un export ne doit pas écraser les données corrigées dans Excel.
            from openpyxl import load_workbook
            wb = load_workbook(target)
            try:
                for entries in result["source_map"].values():
                    for entry in entries:
                        sheet = entry["sheet_name"]
                        if sheet not in wb or len(wb[sheet]._charts) != 1:
                            raise ValueError(f"{target.name} : graphique unique attendu sur {sheet}.")
            finally:
                wb.close()
            result["workbooks"][KEY] = str(target)
            return result
        stage = target.with_name(f".{target.stem}.{uuid4().hex}.xlsx")
        try:
            with xlsxwriter.Workbook(str(stage), {"in_memory": True, "strings_to_formulas": False,
                                                  "strings_to_urls": False}) as book:
                header = book.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#1A3A6B"})
                for filename, ids in FIGURES.items():
                    if filename.lower() in result["source_map"]:
                        for p in ids:
                            _write_panel(book, p, panels[p], header)
            os.replace(stage, target)
        finally:
            stage.unlink(missing_ok=True)
        result["workbooks"][KEY] = str(target)
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("xlsx", type=Path)
    args = parser.parse_args()
    print(json.dumps(preparer_graphiques(args.html.read_text(encoding="utf-8-sig"), args.xlsx),
                     indent=2, ensure_ascii=False))
