"""
generer_annexe_c_classeur.py
============================
Génère un classeur Excel natif pour l'annexe C avec :
  - un onglet index ;
  - un onglet par indicateur ODD 1.3.1 ;
  - les tableaux annuels (indicateur/numérateur/dénominateur) ;
  - le détail des composantes du numérateur ;
  - deux graphiques Excel par indicateur calculable.

Le script réutilise les mêmes sources de calcul que generer_annexe_c_visuels.py
(base ESS, décisions ODD, constructions de dénominateurs) et n'analyse pas
les valeurs formatées du Markdown.

Usage :
    py 09_scripts/generer_annexe_c_classeur.py
    py 09_scripts/generer_annexe_c_classeur.py --output 10_output/annexe_C_test.xlsx
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, LineChart, Reference
    from openpyxl.chart.label import DataLabelList
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
except ImportError:
    sys.exit("openpyxl requis : py -m pip install openpyxl")

from visualiser_regimes import (  # noqa: E402
    DB_PATH,
    ODD_INDICATORS,
    build_indicateurs_payload,
    build_odd_programmes_payload,
    load_all,
)
from integrer_dashboard_bulletin import (  # noqa: E402
    DENOM_DB_PATH,
    METRIC_BY_INDICATOR,
    SETTINGS_PATH,
    compute_numerator,
    compute_numerator_breakdown,
    get_denominator_value,
)

WORKSPACE = SCRIPT_DIR.parent
ANNEXE_C_XLSX_FILE = WORKSPACE / "10_output" / "annexe_C_graphiques_par_indicateur.xlsx"
START_YEAR = 2019

EXCEL_CHART_STYLE_ID = 10
COLOR_TITLE = "2C5282"
COLOR_ACCENT = "2E78C8"
COLOR_HEADER_TEXT = "FFFFFF"
COLOR_HEADER_LIGHT = "E8F0FA"
SERIES_COLORS = ("2C5282", "2E78C8", "4A5568", "38A169", "DD6B20")

THIN_BORDER = Border(
    left=Side(style="thin", color="D1D5DB"),
    right=Side(style="thin", color="D1D5DB"),
    top=Side(style="thin", color="D1D5DB"),
    bottom=Side(style="thin", color="D1D5DB"),
)

ODD_METHODOLOGY_SPECS = {
    "global_131": {
        "definition": "Proportion de la population couverte par au moins une prestation en espèces de protection sociale ou cotisant activement à au moins un régime de sécurité sociale.",
        "numerator": "Nombre de personnes recevant au moins une prestation en espèces de protection sociale, hors soins de santé et indemnités journalières de maladie ou de maternité, ou cotisant activement à au moins un régime de sécurité sociale, sans double comptage.",
        "denominator": "Population totale.",
        "formula": "Population couverte par au moins une prestation ou cotisant activement ÷ population totale × 100.",
    },
    "ind_22_enfants": {
        "definition": "Proportion d'enfants bénéficiant d'au moins une prestation en espèces de protection sociale destinée aux enfants ou aux familles.",
        "numerator": "Nombre d'enfants recevant au moins une prestation en espèces pour enfants ou famille, hors indemnités journalières de maladie ou de maternité.",
        "denominator": "Population totale des enfants dans la tranche d'âge retenue.",
        "formula": "Enfants bénéficiaires ÷ population totale des enfants × 100.",
    },
    "ind_23_maternite": {
        "definition": "Proportion de femmes ayant accouché qui reçoivent une prestation en espèces de maternité.",
        "numerator": "Nombre de bénéficiaires de l'allocation de maternité de la CNSS. Les indemnités journalières de maternité sont exclues.",
        "denominator": "Nombre total de femmes ayant accouché au cours de la même année, estimé directement ou à partir des naissances vivantes corrigées des naissances multiples.",
        "formula": "Femmes bénéficiaires d'une prestation de maternité ÷ femmes ayant accouché × 100.",
    },
    "ind_24_handicap": {
        "definition": "Proportion de personnes en situation de handicap grave qui reçoivent une prestation en espèces d'invalidité.",
        "numerator": "Nombre de personnes en situation de handicap grave percevant une prestation en espèces d'invalidité.",
        "denominator": "Population estimée de personnes en situation de handicap grave.",
        "formula": "Bénéficiaires de prestations d'invalidité ÷ population en situation de handicap grave × 100.",
    },
    "ind_25_atmp": {
        "definition": "Proportion de la main-d'œuvre couverte par un régime assurant une protection en cas d'accident du travail ou de maladie professionnelle.",
        "numerator": "Nombre de personnes appartenant à la main-d'œuvre et couvertes en cas d'accident du travail ou de maladie professionnelle.",
        "denominator": "Main-d'œuvre totale, composée des personnes en emploi et des personnes au chômage.",
        "formula": "Main-d'œuvre couverte contre les accidents du travail et maladies professionnelles ÷ main-d'œuvre totale × 100.",
    },
    "ind_26_chomage": {
        "definition": "Proportion de personnes au chômage qui reçoivent une prestation en espèces de chômage.",
        "numerator": "Nombre de personnes au chômage percevant effectivement une allocation de chômage en espèces.",
        "denominator": "Nombre total de personnes au chômage selon la définition du BIT.",
        "formula": "Chômeurs indemnisés ÷ nombre total de chômeurs × 100.",
    },
    "ind_27_vieillesse": {
        "definition": "Proportion de personnes ayant atteint l'âge légal de la retraite qui reçoivent une prestation de vieillesse contributive ou non contributive.",
        "numerator": "Nombre de bénéficiaires d'une pension de vieillesse, y compris les pensions de retraite anticipée. Ces dernières peuvent concerner des personnes âgées de moins de 60 ans.",
        "denominator": "Population totale âgée de 60 ans et plus. Ce seuil unique correspond à l'âge d'ouverture du droit à pension CNSS ; la mise à la retraite d'office intervient à 65 ans.",
        "formula": "Bénéficiaires de prestations de vieillesse ÷ population ayant atteint l'âge légal de la retraite × 100.",
    },
    "ind_28_vulnerables": {
        "definition": "Proportion de personnes vulnérables qui reçoivent une prestation d'assistance sociale en espèces.",
        "numerator": "Nombre d'enfants bénéficiaires de prestations familiales, dont les allocations familiales CNSS.",
        "denominator": "Population vulnérable, obtenue en retranchant de la population totale les personnes en âge de travailler cotisant à une assurance sociale ou percevant une prestation contributive, ainsi que les personnes d'âge légal de la retraite percevant une prestation contributive.",
        "formula": "Enfants bénéficiaires de prestations familiales ÷ population vulnérable × 100.",
    },
    "ind_29_cotisants": {
        "definition": "Proportion de la population en âge de travailler qui cotise activement à un régime de retraite contributif.",
        "numerator": "Nombre de personnes cotisant activement à un régime de retraite contributif.",
        "denominator": "Population en âge de travailler (15-64 ans, Banque mondiale SP.POP.1564.TO).",
        "formula": "Cotisants actifs à un régime de retraite ÷ population en âge de travailler (15-64 ans) × 100.",
    },
}

NON_CALCULABLE_NOTE = {
    "ind_26_chomage": "N/A — aucun régime d'assurance chômage n'existe dans le périmètre du bulletin. Aucune allocation de chômage ne peut donc être mesurée.",
}


def _sanitize_sheet_name(name: str) -> str:
    invalid = "[]*?:/\\"
    cleaned = "".join("_" if char in invalid else char for char in (name or ""))
    cleaned = "_".join(part for part in cleaned.replace("-", "_").split() if part)
    return (cleaned[:31] or "Feuille")


def _unique_sheet_name(base: str, used: set[str]) -> str:
    candidate = _sanitize_sheet_name(base)
    if candidate not in used:
        used.add(candidate)
        return candidate
    index = 2
    while True:
        suffix = f"_{index}"
        trimmed = _sanitize_sheet_name(candidate[: 31 - len(suffix)] + suffix)
        if trimmed not in used:
            used.add(trimmed)
            return trimmed
        index += 1


def _apply_header_style(cell, *, primary: bool = True) -> None:
    cell.fill = PatternFill(fill_type="solid", fgColor=(COLOR_TITLE if primary else COLOR_HEADER_LIGHT))
    cell.font = Font(bold=True, color=(COLOR_HEADER_TEXT if primary else COLOR_TITLE))
    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    cell.border = THIN_BORDER


def _apply_data_cell_style(cell) -> None:
    cell.alignment = Alignment(vertical="top", wrap_text=True)
    cell.border = THIN_BORDER


def _strip_trailing_year(meta: str, year: int) -> str:
    suffix = f"({year})"
    text = (meta or "").strip()
    if text.endswith(suffix):
        return text[: -len(suffix)].strip()
    return text


def _build_denominator_note(indicator_key: str, years: list[int], constructions: dict) -> str:
    if indicator_key == "ind_28_vulnerables":
        return (
            "Dénominateur : population totale moins les cotisants actifs dédupliqués, "
            "TRESOR inclus, et les bénéficiaires de pensions de vieillesse."
        )
    meta_by_year: dict[int, str] = {}
    for year in years:
        construction = constructions.get(f"{indicator_key}::{year}") or {}
        meta = _strip_trailing_year(str(construction.get("meta") or ""), year)
        if meta:
            meta_by_year[year] = meta

    if not meta_by_year:
        return "Construction détaillée disponible dans les paramètres de dénominateur du tableau de bord."

    ordered = sorted(meta_by_year)
    parts: list[str] = []
    cursor = 0
    while cursor < len(ordered):
        start_year = ordered[cursor]
        end_index = cursor
        while (
            end_index + 1 < len(ordered)
            and ordered[end_index + 1] == ordered[end_index] + 1
            and meta_by_year[ordered[end_index + 1]] == meta_by_year[start_year]
        ):
            end_index += 1
        end_year = ordered[end_index]
        year_label = str(start_year) if start_year == end_year else f"{start_year}-{end_year}"
        parts.append(f"{year_label} : {meta_by_year[start_year]}")
        cursor = end_index + 1
    return "Sources du dénominateur — " + " ; ".join(parts) + "."


def _open_denominator_cursor() -> tuple[sqlite3.Connection | None, sqlite3.Cursor | None]:
    if not DENOM_DB_PATH.exists():
        return None, None
    conn = sqlite3.connect(DENOM_DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='denominateurs_ref' LIMIT 1")
        if not cursor.fetchone():
            cursor.close()
            return conn, None
        return conn, cursor
    except sqlite3.Error:
        return conn, None


def _resolve_series_color(index: int) -> str:
    return SERIES_COLORS[index % len(SERIES_COLORS)]


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _build_indicator_payload(
    *,
    section_no: int,
    indicator_key: str,
    label: str,
    years: list[int],
    years_available: set[int],
    regime_rows: list[dict],
    prestation_rows: list[dict],
    odd_nodes: list[dict],
    decisions: dict[str, str],
    denom_constructions: dict,
    denom_settings: dict,
    denom_cursor: sqlite3.Cursor | None,
) -> dict:
    calculable = indicator_key in METRIC_BY_INDICATOR

    annual_rows: list[list[Any]] = []
    components_map: dict[str, dict] = {}

    for year in years:
        ratio_value = None
        numerator_value = None
        denominator_value = None
        if calculable and year in years_available:
            numerator_value = _safe_float(
                compute_numerator(indicator_key, year, regime_rows, prestation_rows, odd_nodes, decisions)
            )
            denominator_value = _safe_float(
                get_denominator_value(
                    indicator_key,
                    year,
                    denom_constructions,
                    denom_settings,
                    denom_cursor,
                    regime_rows,
                    prestation_rows,
                    odd_nodes,
                    decisions,
                )
            )
            if (
                numerator_value is not None
                and denominator_value is not None
                and denominator_value > 0
            ):
                ratio_value = numerator_value / denominator_value * 100.0

            for component in compute_numerator_breakdown(
                indicator_key, year, regime_rows, prestation_rows, odd_nodes, decisions
            ):
                component_id = str(component.get("id") or "")
                if not component_id:
                    continue
                item = components_map.setdefault(
                    component_id,
                    {
                        "type": "Régime" if component.get("kind") == "regime" else "Prestation",
                        "institution": component.get("institution"),
                        "regime_code": component.get("regime_code"),
                        "label": component.get("label") or component_id,
                        "metric": component.get("metric"),
                        "values": {},
                        "kind_rank": 0 if component.get("kind") == "regime" else 1,
                    },
                )
                item["values"][year] = _safe_float(component.get("value"))
        annual_rows.append([year, ratio_value, numerator_value, denominator_value])

    components = sorted(
        components_map.values(),
        key=lambda item: (
            str(item.get("institution") or ""),
            str(item.get("regime_code") or ""),
            int(item.get("kind_rank") or 0),
            str(item.get("label") or ""),
        ),
    )

    spec = ODD_METHODOLOGY_SPECS.get(indicator_key, ODD_METHODOLOGY_SPECS["global_131"])
    denominator_note = _build_denominator_note(indicator_key, years, denom_constructions)
    notes = denominator_note
    if indicator_key == "ind_22_enfants":
        notes += (
            " Estimation CNSS enfants : titulaires d'allocations familiales × 3,17 "
            "(UN HH Size and Composition 2019)."
        )
    if indicator_key == "ind_28_vulnerables":
        notes += (
            " Numérateur : enfants bénéficiaires de prestations familiales, dont les "
            "allocations familiales CNSS déjà estimées à 3,17 enfants par titulaire. "
            "Dénominateur : population totale moins cotisants actifs dédupliqués, "
            "TRESOR inclus, et pensionnés de vieillesse."
        )
    if not calculable:
        notes = NON_CALCULABLE_NOTE.get(indicator_key, "Indicateur non calculable avec les données actuelles.")

    return {
        "section": f"C.{section_no}",
        "indicator_key": indicator_key,
        "label": label,
        "calculable": calculable,
        "status": "calculable" if calculable else "non calculable",
        "definition": spec["definition"],
        "numerator_def": spec["numerator"],
        "denominator_def": spec["denominator"],
        "formula": spec["formula"],
        "period": f"{years[0]}-{years[-1]}",
        "notes": notes,
        "annual_rows": annual_rows,
        "components": components,
        "chart_count": 2 if calculable else 0,
    }


def _write_metadata(ws, payload: dict) -> int:
    ws.merge_cells("A1:D1")
    title_cell = ws["A1"]
    title_cell.value = f"Annexe C — {payload['section']} — {payload['label']}"
    title_cell.fill = PatternFill(fill_type="solid", fgColor=COLOR_TITLE)
    title_cell.font = Font(bold=True, color=COLOR_HEADER_TEXT, size=13)
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    title_cell.border = THIN_BORDER

    metadata_rows = [
        ("Section", payload["section"]),
        ("Indicateur", payload["label"]),
        ("Clé", payload["indicator_key"]),
        ("Statut", payload["status"]),
        ("Définition", payload["definition"]),
        ("Numérateur", payload["numerator_def"]),
        ("Dénominateur", payload["denominator_def"]),
        ("Formule", payload["formula"]),
        ("Période", payload["period"]),
        ("Sources / notes", payload["notes"]),
    ]

    start_row = 3
    for index, (field_name, field_value) in enumerate(metadata_rows):
        row = start_row + index
        label_cell = ws.cell(row=row, column=1, value=field_name)
        value_cell = ws.cell(row=row, column=2, value=field_value)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
        _apply_header_style(label_cell, primary=False)
        _apply_data_cell_style(value_cell)
    return start_row + len(metadata_rows) - 1


def _write_annual_table(ws, payload: dict, years: list[int], start_row: int) -> tuple[int, int]:
    header_row = start_row
    headers = ["Année", "Indicateur (%)", "Numérateur", "Dénominateur"]
    for col_index, header in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_index, value=header)
        _apply_header_style(cell)

    data_start = header_row + 1
    for offset, (year, ratio_value, num_value, den_value) in enumerate(payload["annual_rows"]):
        row = data_start + offset
        year_cell = ws.cell(row=row, column=1, value=year)
        ratio_cell = ws.cell(row=row, column=2, value=ratio_value)
        numerator_cell = ws.cell(row=row, column=3, value=num_value)
        denominator_cell = ws.cell(row=row, column=4, value=den_value)
        year_cell.number_format = "0"
        ratio_cell.number_format = '0.0"%"'
        numerator_cell.number_format = "#,##0.00"
        denominator_cell.number_format = "#,##0.00"
        for cell in (year_cell, ratio_cell, numerator_cell, denominator_cell):
            _apply_data_cell_style(cell)

    table_end_row = data_start + len(years) - 1
    return header_row, table_end_row


def _write_components_table(ws, payload: dict, years: list[int], start_row: int) -> int:
    ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=5 + len(years))
    title_cell = ws.cell(row=start_row, column=1, value="Détail des composantes du numérateur")
    _apply_header_style(title_cell, primary=False)

    header_row = start_row + 1
    headers = ["Type", "Institution", "Régime", "Composante", "Unité", *years]
    for col_index, header in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_index, value=header)
        _apply_header_style(cell)

    current_row = header_row + 1
    components = payload["components"]
    if not components:
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=5 + len(years))
        cell = ws.cell(row=current_row, column=1, value="Aucune composante disponible.")
        _apply_data_cell_style(cell)
        return current_row

    for item in components:
        base_values = [
            item.get("type"),
            item.get("institution"),
            item.get("regime_code"),
            item.get("label"),
            item.get("metric"),
        ]
        yearly_values = [item.get("values", {}).get(year) for year in years]
        row_values = [*base_values, *yearly_values]
        for col_index, value in enumerate(row_values, start=1):
            cell = ws.cell(row=current_row, column=col_index, value=value)
            _apply_data_cell_style(cell)
            if col_index >= 6:
                cell.number_format = "#,##0.00"
        current_row += 1
    return current_row - 1


def _style_chart_axes(chart, *, y_title: str, y_percent: bool = False) -> None:
    chart.style = EXCEL_CHART_STYLE_ID
    chart.legend.position = "b"
    chart.x_axis.title = "Année"
    chart.x_axis.number_format = "0"
    chart.x_axis.tickLblSkip = 1
    chart.x_axis.tickMarkSkip = 1
    chart.y_axis.title = y_title
    if y_percent:
        chart.y_axis.number_format = '0.0"%"'


def _colorize_series(chart) -> None:
    for idx, series in enumerate(chart.series):
        color = _resolve_series_color(idx)
        series.graphicalProperties.solidFill = color
        series.graphicalProperties.line.solidFill = color


def _add_indicator_charts(ws, payload: dict, header_row: int, table_end_row: int, anchor_row: int) -> int:
    categories = Reference(ws, min_col=1, min_row=header_row + 1, max_row=table_end_row)

    ratio_chart = LineChart()
    ratio_chart.grouping = "standard"
    ratio_chart.title = f"{payload['label']} — Indicateur de couverture (%)"
    ratio_chart.height = 7.2
    ratio_chart.width = 11.0
    ratio_data = Reference(ws, min_col=2, min_row=header_row, max_row=table_end_row)
    ratio_chart.add_data(ratio_data, titles_from_data=True)
    ratio_chart.set_categories(categories)
    _style_chart_axes(ratio_chart, y_title="Indicateur (%)", y_percent=True)
    ratio_chart.smooth = False
    _colorize_series(ratio_chart)
    for series in ratio_chart.series:
        series.smooth = False
        series.marker.symbol = "circle"
        series.marker.size = 6
    ws.add_chart(ratio_chart, f"A{anchor_row}")

    numerator_chart = BarChart()
    numerator_chart.type = "col"
    numerator_chart.grouping = "clustered"
    numerator_chart.gapWidth = 90
    numerator_chart.title = f"{payload['label']} — Numérateur (nombre de personnes)"
    numerator_chart.height = 7.2
    numerator_chart.width = 11.0
    numerator_data = Reference(ws, min_col=3, min_row=header_row, max_row=table_end_row)
    numerator_chart.add_data(numerator_data, titles_from_data=True)
    numerator_chart.set_categories(categories)
    _style_chart_axes(numerator_chart, y_title="Personnes", y_percent=False)
    labels = DataLabelList()
    labels.showVal = True
    labels.position = "outEnd"
    numerator_chart.dataLabels = labels
    _colorize_series(numerator_chart)
    ws.add_chart(numerator_chart, f"I{anchor_row}")
    return 2


def _prepare_workbook_layout(ws) -> None:
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 34
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 20
    ws.column_dimensions["E"].width = 18
    for column in "FGHIJKLMNOPQRSTUVWXYZ":
        ws.column_dimensions[column].width = 14


def _write_indicator_sheet(ws, payload: dict, years: list[int]) -> int:
    _prepare_workbook_layout(ws)
    metadata_end_row = _write_metadata(ws, payload)
    annual_header_row, annual_end_row = _write_annual_table(ws, payload, years, metadata_end_row + 2)
    components_end_row = _write_components_table(ws, payload, years, annual_end_row + 2)
    ws.freeze_panes = f"A{annual_header_row + 1}"
    if payload["calculable"]:
        return _add_indicator_charts(ws, payload, annual_header_row, annual_end_row, components_end_row + 2)
    return 0


def _write_index_sheet(index_ws, entries: list[dict]) -> None:
    index_ws.merge_cells("A1:H1")
    title_cell = index_ws["A1"]
    title_cell.value = "Annexe C — Index des indicateurs et graphiques"
    title_cell.fill = PatternFill(fill_type="solid", fgColor=COLOR_TITLE)
    title_cell.font = Font(bold=True, color=COLOR_HEADER_TEXT, size=13)
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    title_cell.border = THIN_BORDER

    headers = ["Section", "Indicateur", "Clé", "Statut", "Onglet", "Graphiques", "Période", "Notes"]
    for col_index, header in enumerate(headers, start=1):
        cell = index_ws.cell(row=3, column=col_index, value=header)
        _apply_header_style(cell)

    for row_index, entry in enumerate(entries, start=4):
        values = [
            entry["section"],
            entry["label"],
            entry["indicator_key"],
            entry["status"],
            entry["sheet_name"],
            entry["chart_count"],
            entry["period"],
            entry["notes"],
        ]
        for col_index, value in enumerate(values, start=1):
            cell = index_ws.cell(row=row_index, column=col_index, value=value)
            _apply_data_cell_style(cell)
        sheet_cell = index_ws.cell(row=row_index, column=5)
        sheet_cell.hyperlink = f"#{entry['sheet_name']}!A1"
        sheet_cell.style = "Hyperlink"

    index_ws.column_dimensions["A"].width = 10
    index_ws.column_dimensions["B"].width = 34
    index_ws.column_dimensions["C"].width = 22
    index_ws.column_dimensions["D"].width = 16
    index_ws.column_dimensions["E"].width = 22
    index_ws.column_dimensions["F"].width = 12
    index_ws.column_dimensions["G"].width = 12
    index_ws.column_dimensions["H"].width = 84
    index_ws.freeze_panes = "A4"


def generate_annexe_c_workbook(output_path: Path = ANNEXE_C_XLSX_FILE) -> dict:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Base ESS introuvable : {DB_PATH}")

    regimes, prestations, regime_meta, prestation_meta = load_all(DB_PATH)
    indicateurs = build_indicateurs_payload(regimes, prestations)
    odd_nodes = build_odd_programmes_payload(regimes, prestations, regime_meta, prestation_meta)
    regime_rows = indicateurs.get("rows_regimes") or []
    prestation_rows = indicateurs.get("rows_prestations") or []

    years_available = {
        int(year)
        for year in (indicateurs.get("years_numerator") or indicateurs.get("years") or [])
        if isinstance(year, int) or (isinstance(year, float) and year.is_integer())
    }
    max_year = max(years_available) if years_available else START_YEAR
    years = list(range(START_YEAR, max_year + 1))

    settings = {}
    if SETTINGS_PATH.exists():
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    decisions = settings.get("oddDecisions") or {}
    denom_settings = settings.get("denomSettings") or {}
    denom_constructions = denom_settings.get("denominatorConstructions") or {}

    denom_conn, denom_cursor = _open_denominator_cursor()

    workbook = Workbook()
    index_ws = workbook.active
    index_ws.title = "index"

    used_sheet_names = {"index"}
    entries: list[dict] = []
    total_charts = 0
    try:
        for section_no, indicator in enumerate(ODD_INDICATORS, start=1):
            indicator_key = indicator["key"]
            label = indicator["label"]
            payload = _build_indicator_payload(
                section_no=section_no,
                indicator_key=indicator_key,
                label=label,
                years=years,
                years_available=years_available,
                regime_rows=regime_rows,
                prestation_rows=prestation_rows,
                odd_nodes=odd_nodes,
                decisions=decisions,
                denom_constructions=denom_constructions,
                denom_settings=denom_settings,
                denom_cursor=denom_cursor,
            )

            sheet_name = _unique_sheet_name(f"C{section_no}_{indicator_key}", used_sheet_names)
            payload["sheet_name"] = sheet_name
            ws = workbook.create_sheet(sheet_name)
            chart_count = _write_indicator_sheet(ws, payload, years)
            payload["chart_count"] = chart_count
            total_charts += chart_count
            entries.append(payload)
    finally:
        if denom_conn is not None:
            denom_conn.close()

    _write_index_sheet(index_ws, entries)
    output_path = Path(output_path)
    if not output_path.is_absolute():
        output_path = WORKSPACE / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)

    return {
        "output_path": str(output_path),
        "entries": entries,
        "years": years,
        "sheet_count": len(workbook.sheetnames),
        "total_charts": total_charts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Génère le classeur Excel de l'annexe C.")
    parser.add_argument(
        "--output",
        default=str(ANNEXE_C_XLSX_FILE),
        help="Chemin de sortie du classeur XLSX (défaut: 10_output/annexe_C_graphiques_par_indicateur.xlsx).",
    )
    args = parser.parse_args(argv)

    summary = generate_annexe_c_workbook(Path(args.output))
    output_path = Path(summary["output_path"])
    try:
        output_display = output_path.relative_to(WORKSPACE)
    except ValueError:
        output_display = output_path
    print(f"Classeur généré : {output_display}")
    print(f"Feuilles : {summary['sheet_count']} | Graphiques : {summary['total_charts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
