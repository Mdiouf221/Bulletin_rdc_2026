"""Rafraîchit les tableaux chiffrés du chapitre 4 depuis la base ESS.

Le script remplace les cellules des lignes connues, y compris après une
première exécution. Il préserve les balises de validation et les appels de
notes déjà présents dans le Markdown.

Usage :
    py 09_scripts/remplir_ch4.py
    py 09_scripts/remplir_ch4.py --check
"""

from __future__ import annotations

import argparse
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "06_donnees" / "protection_sociale_rdc.db"
CHAPTER_DIR = BASE_DIR / "03_chapitres" / "chapitre_4"
YEARS = tuple(range(2019, 2026))


def format_integer(value: float) -> str:
    return f"{round(value):,}".replace(",", " ")


def format_money(value: float) -> str:
    return format_integer(value)


def format_billions(value: float) -> str:
    return f"{value / 1_000_000_000:.1f}".replace(".", ",") + " Mds CDF"


def format_percent(value: float) -> str:
    return f"{value:.1f}".replace(".", ",")


@dataclass(frozen=True)
class Rule:
    file_name: str
    markers: tuple[str, ...]
    values: dict[int, float | None]
    formatter: Callable[[float], str]
    validation_prefix: str


def query_series(
    connection: sqlite3.Connection,
    sql: str,
    params: tuple[object, ...],
) -> dict[int, float | None]:
    values = {year: None for year in YEARS}
    for year, value in connection.execute(sql, params):
        if year in values:
            values[int(year)] = float(value) if value is not None else None
    return values


def prestation_series(
    connection: sqlite3.Connection,
    institution: str,
    regime_codes: tuple[str, ...],
    prestation_nums: tuple[int, ...],
    column: str,
    aggregate: str = "SUM",
) -> dict[int, float | None]:
    if column not in {"beneficiaires_total", "montant_unitaire_cdf"}:
        raise ValueError(f"Colonne de prestation non autorisée : {column}")
    if aggregate not in {"SUM", "MAX"}:
        raise ValueError(f"Agrégat non autorisé : {aggregate}")
    regime_placeholders = ",".join("?" for _ in regime_codes)
    prestation_placeholders = ",".join("?" for _ in prestation_nums)
    return query_series(
        connection,
        f"""
        SELECT annee, {aggregate}({column})
        FROM prestations_historique
        WHERE institution=?
          AND regime_code IN ({regime_placeholders})
          AND prestation_num IN ({prestation_placeholders})
        GROUP BY annee
        ORDER BY annee
        """,
        (institution, *regime_codes, *prestation_nums),
    )


def indicator_series(
    connection: sqlite3.Connection,
    institution: str,
    column: str,
    regime_code: str | None = None,
) -> dict[int, float | None]:
    if column not in {
        "cotisants_total",
        "beneficiaires_total",
        "recettes_cdf",
        "depenses_prestations_cdf",
        "depenses_admin_cdf",
    }:
        raise ValueError(f"Colonne d'indicateur non autorisée : {column}")
    regime_filter = " AND regime_code=?" if regime_code else ""
    params: tuple[object, ...] = (institution, regime_code) if regime_code else (institution,)
    return query_series(
        connection,
        f"""
        SELECT annee, MAX({column})
        FROM indicateurs_regime
        WHERE institution=?{regime_filter}
        GROUP BY annee
        ORDER BY annee
        """,
        params,
    )


def cnss_financial_series(
    connection: sqlite3.Connection,
    column: str,
) -> dict[int, float | None]:
    values = {year: None for year in YEARS}
    rows = connection.execute(
        f"""
        SELECT annee, {column}
        FROM indicateurs_regime
        WHERE institution='CNSS'
          AND regime_code IN ('CNSS_R1', 'CNSS_R2', 'CNSS_R3')
          AND {column} IS NOT NULL
        ORDER BY annee, regime_code
        """
    )
    grouped: dict[int, list[float]] = {}
    for year, value in rows:
        grouped.setdefault(int(year), []).append(float(value))
    for year, year_values in grouped.items():
        distinct = {round(value, 2) for value in year_values}
        values[year] = year_values[0] if len(distinct) == 1 else sum(year_values)
    return values


def ratio_series(
    numerator: dict[int, float | None],
    denominator_component: dict[int, float | None],
) -> dict[int, float | None]:
    values = {year: None for year in YEARS}
    for year in YEARS:
        num = numerator[year]
        component = denominator_component[year]
        denominator = (num + component) if num is not None and component is not None else None
        if denominator and denominator > 0:
            values[year] = num / denominator * 100
    return values


def build_rules(connection: sqlite3.Connection) -> list[Rule]:
    cnss_retirement = prestation_series(connection, "CNSS", ("CNSS_R3",), (1,), "beneficiaires_total")
    cnss_retirement_early = prestation_series(connection, "CNSS", ("CNSS_R3",), (6,), "beneficiaires_total")
    cnss_retirement_amount = prestation_series(
        connection, "CNSS", ("CNSS_R3",), (1,), "montant_unitaire_cdf", "MAX"
    )
    cnssap_retirement = prestation_series(
        connection, "CNSSAP", ("CNSSAP_R1", "CNSSAP_R2"), (1,), "beneficiaires_total"
    )
    sesopa_retirement = prestation_series(
        connection, "SESOPA", ("SESOPA_R1",), (1, 2), "beneficiaires_total"
    )

    cnss_cotisants = indicator_series(connection, "CNSS", "cotisants_total")
    cnssap_cotisants = indicator_series(connection, "CNSSAP", "cotisants_total", "CNSSAP_R1")
    # DM-019 : les valeurs 2023-2024 ne sont pas retenues comme cotisants actifs.
    cnssap_cotisants[2023] = None
    cnssap_cotisants[2024] = None

    maternity_daily = prestation_series(
        connection, "CNSS", ("CNSS_R1",), (4,), "beneficiaires_total"
    )
    maternity_allowance = prestation_series(
        connection, "CNSS", ("CNSS_R1",), (2,), "beneficiaires_total"
    )
    prenatal_allowance = prestation_series(
        connection, "CNSS", ("CNSS_R1",), (1,), "beneficiaires_total"
    )
    atmp_incapacity = prestation_series(
        connection, "CNSS", ("CNSS_R2",), (1,), "beneficiaires_total"
    )
    atmp_rehabilitation = prestation_series(
        connection, "CNSS", ("CNSS_R2",), (5,), "beneficiaires_total"
    )
    atmp_amount = prestation_series(
        connection, "CNSS", ("CNSS_R2",), (1,), "montant_unitaire_cdf", "MAX"
    )
    # DM-021 : détail 2024 et montant 2023-2024 non retenus avant vérification.
    atmp_incapacity[2024] = None
    atmp_rehabilitation[2024] = None
    atmp_amount[2023] = None
    atmp_amount[2024] = None

    family_children = prestation_series(
        connection, "CNSS", ("CNSS_R1",), (3,), "beneficiaires_total"
    )

    invalidity = prestation_series(
        connection, "CNSS", ("CNSS_R3",), (2,), "beneficiaires_total"
    )
    invalidity_amount = prestation_series(
        connection, "CNSS", ("CNSS_R3",), (2,), "montant_unitaire_cdf", "MAX"
    )

    survivor_pension = prestation_series(
        connection, "CNSS", ("CNSS_R3",), (3,), "beneficiaires_total"
    )
    survivor_atmp = prestation_series(
        connection, "CNSS", ("CNSS_R2",), (2,), "beneficiaires_total"
    )
    funeral_beneficiaries = prestation_series(
        connection, "CNSS", ("CNSS_R2",), (4,), "beneficiaires_total"
    )
    survivor_atmp[2024] = None
    funeral_beneficiaries[2024] = None
    cnssap_survivors = prestation_series(
        connection,
        "CNSSAP",
        ("CNSSAP_R1", "CNSSAP_R2"),
        (2, 3),
        "beneficiaires_total",
    )
    sesopa_survivors = prestation_series(
        connection, "SESOPA", ("SESOPA_R1",), (3,), "beneficiaires_total"
    )
    survivor_amount = prestation_series(
        connection, "CNSS", ("CNSS_R3",), (3,), "montant_unitaire_cdf", "MAX"
    )
    funeral_amount = prestation_series(
        connection, "CNSS", ("CNSS_R2",), (4,), "montant_unitaire_cdf", "MAX"
    )

    mesp_cotisants = indicator_series(connection, "MESP", "cotisants_total", "MESP_R1")
    mesp_beneficiaries = indicator_series(connection, "MESP", "beneficiaires_total", "MESP_R1")

    cnss_revenue = cnss_financial_series(connection, "recettes_cdf")
    cnss_benefit_expense = cnss_financial_series(connection, "depenses_prestations_cdf")
    cnss_admin_expense = cnss_financial_series(connection, "depenses_admin_cdf")
    cnssap_revenue = indicator_series(connection, "CNSSAP", "recettes_cdf", "CNSSAP_R1")
    cnssap_benefit_expense = indicator_series(
        connection, "CNSSAP", "depenses_prestations_cdf", "CNSSAP_R1"
    )
    cnssap_admin_expense = indicator_series(
        connection, "CNSSAP", "depenses_admin_cdf", "CNSSAP_R1"
    )
    cnss_ratio = ratio_series(cnss_admin_expense, cnss_benefit_expense)
    cnssap_ratio = ratio_series(cnssap_admin_expense, cnssap_benefit_expense)

    return [
        Rule("4.2_vieillesse.md", ("CNSS | Pension de retraite (bénéf.)",), cnss_retirement, format_integer, "s42-t1-d"),
        Rule("4.2_vieillesse.md", ("CNSS | Pension de retraite anticipée",), cnss_retirement_early, format_integer, "s42-t1-d4"),
        Rule("4.2_vieillesse.md", ("CNSSAP | Pension de vieillesse",), cnssap_retirement, format_integer, "s42-t1-d"),
        Rule("4.2_vieillesse.md", ("SESOPA", "Pension de vieillesse"), sesopa_retirement, format_integer, "s42-t1-d5"),
        Rule("4.2_vieillesse.md", ("Pension CNSS — montant unitaire",), cnss_retirement_amount, format_money, "s42-t2-d"),
        Rule("4.3_age_actif.md", ("CNSS | Régime contributif — secteur formel | Cotisants actifs",), cnss_cotisants, format_integer, "s43-t1-d"),
        Rule("4.3_age_actif.md", ("CNSSAP | Régime contributif — agents publics | Cotisants actifs",), cnssap_cotisants, format_integer, "s43-t1-d"),
        Rule("4.3_age_actif.md", ("indemnité journalière maternité",), maternity_daily, format_integer, "s43-t2-d"),
        Rule("4.3_age_actif.md", ("allocation de maternité",), maternity_allowance, format_integer, "s43-t2-d"),
        Rule("4.3_age_actif.md", ("allocations prénatales",), prenatal_allowance, format_integer, "s43-t2-d"),
        Rule("4.3_age_actif.md", ("Rentes/allocations incapacité AT/MP",), atmp_incapacity, format_integer, "s43-t3-d"),
        Rule("4.3_age_actif.md", ("Frais de réadaptation fonctionnelle",), atmp_rehabilitation, format_integer, "s43-t3-d"),
        Rule("4.3_age_actif.md", ("Montant unitaire rente AT/MP",), atmp_amount, format_money, "s43-t3-d"),
        Rule("4.4_enfants_familles.md", ("CNSS | Enfants couverts",), family_children, format_integer, "s44-t1-d"),
        Rule("4.5_invalidite.md", ("CNSS | Pensionnés invalidité",), invalidity, format_integer, "s45-t1-d"),
        Rule("4.5_invalidite.md", ("CNSS | Montant unitaire pension invalidité",), invalidity_amount, format_money, "s45-t1-d"),
        Rule("4.5_invalidite.md", ("Pension invalidité CNSS",), invalidity_amount, format_money, "s45-t2-d"),
        Rule("4.5_invalidite.md", ("Pension vieillesse CNSS",), cnss_retirement_amount, format_money, "s45-t2-d"),
        Rule("4.6_deces_survie.md", ("CNSS | Pension des survivants",), survivor_pension, format_integer, "s46-t1-d"),
        Rule("4.6_deces_survie.md", ("CNSS | Rentes de survivants AT/MP",), survivor_atmp, format_integer, "s46-t1-d"),
        Rule("4.6_deces_survie.md", ("CNSS | Allocation frais funéraires",), funeral_beneficiaries, format_integer, "s46-t1-d"),
        Rule("4.6_deces_survie.md", ("CNSSAP | Pension des survivants",), cnssap_survivors, format_integer, "s46-t1-d4"),
        Rule("4.6_deces_survie.md", ("SESOPA", "Pension de réversion"), sesopa_survivors, format_integer, "s46-t1-d5"),
        Rule("4.6_deces_survie.md", ("Pension survie CNSS",), survivor_amount, format_money, "s46-t2-d"),
        Rule("4.6_deces_survie.md", ("Pension vieillesse CNSS",), cnss_retirement_amount, format_money, "s46-t2-d"),
        Rule("4.6_deces_survie.md", ("Montant frais funéraires CNSS",), funeral_amount, format_money, "s46-t2-d"),
        Rule("4.7_sante.md", ("Cotisants actifs MESP",), mesp_cotisants, format_integer, "s47-t2-d1"),
        Rule("4.7_sante.md", ("Bénéficiaires couverts",), mesp_beneficiaries, format_integer, "s47-t2-d2"),
        Rule("4.8_depenses_financement.md", ("CNSS — recettes totales",), cnss_revenue, format_billions, "s48-t1-d"),
        Rule("4.8_depenses_financement.md", ("CNSSAP — recettes totales",), cnssap_revenue, format_billions, "s48-t1-d"),
        Rule("4.8_depenses_financement.md", ("CNSS — dépenses de prestations",), cnss_benefit_expense, format_billions, "s48-t2-d"),
        Rule("4.8_depenses_financement.md", ("CNSSAP — dépenses de prestations",), cnssap_benefit_expense, format_billions, "s48-t2-d"),
        Rule("4.8_depenses_financement.md", ("CNSS — dépenses administratives",), cnss_admin_expense, format_billions, "s48-t3-d"),
        Rule("4.8_depenses_financement.md", ("CNSS — ratio admin / dépenses totales",), cnss_ratio, format_percent, "s48-t3-d"),
        Rule("4.8_depenses_financement.md", ("CNSSAP — dépenses administratives",), cnssap_admin_expense, format_billions, "s48-t3-d"),
        Rule("4.8_depenses_financement.md", ("CNSSAP — ratio admin / dépenses totales",), cnssap_ratio, format_percent, "s48-t3-d"),
    ]


def render_cell(
    existing: str,
    value: float | None,
    formatter: Callable[[float], str],
    validation_id: str,
    relative_path: str,
) -> str:
    note_match = re.search(r"(<sup>.*?</sup>)", existing)
    note = note_match.group(1) if note_match else ""
    if value is None or not math.isfinite(value):
        if "[N/A]" in existing:
            return "[N/A]" + note
        return "[N/D]" + note

    rendered = formatter(value)
    if abs(value) < 0.0000001:
        return "0" + note

    span_pattern = re.compile(r'(<span class="val"[^>]*>).*?(</span>)')
    if span_pattern.search(existing):
        return span_pattern.sub(rf"\g<1>{rendered}\g<2>", existing, count=1)
    return (
        f'<span class="val" data-val-id="{validation_id}" '
        f'data-val-status="à valider" data-val-file="{relative_path}">{rendered}</span>{note}'
    )


def update_file(path: Path, rules: list[Rule], check_only: bool) -> tuple[int, bool]:
    original = path.read_text(encoding="utf-8-sig")
    lines = original.splitlines(keepends=True)
    current_years: list[int] = []
    replacements = 0

    for index, line in enumerate(lines):
        if line.startswith("|"):
            year_cells = [
                int(cell.strip())
                for cell in line.split("|")
                if re.fullmatch(r"(?:19|20)\d{2}", cell.strip())
            ]
            if len(year_cells) >= 2:
                current_years = year_cells
                continue
        if not current_years or not line.startswith("|"):
            continue

        matching = [rule for rule in rules if all(marker in line for marker in rule.markers)]
        if not matching:
            continue
        if len(matching) > 1:
            raise ValueError(f"Plusieurs règles correspondent à {path.name}: {line.strip()}")
        rule = matching[0]
        parts = line.rstrip("\r\n").split("|")
        if len(parts) < len(current_years) + 3:
            raise ValueError(f"Ligne de tableau mal formée dans {path.name}: {line.strip()}")
        first_value_index = len(parts) - 1 - len(current_years)
        relative_path = path.relative_to(BASE_DIR).as_posix()
        for offset, year in enumerate(current_years):
            cell_index = first_value_index + offset
            existing = parts[cell_index].strip()
            updated = render_cell(
                existing,
                rule.values.get(year),
                rule.formatter,
                f"{rule.validation_prefix}{year}",
                relative_path,
            )
            if updated != existing:
                parts[cell_index] = f" {updated} "
                replacements += 1
        newline = "\r\n" if line.endswith("\r\n") else "\n"
        lines[index] = "|".join(parts) + newline

    updated_text = "".join(lines)
    changed = updated_text != original
    if changed and not check_only:
        path.write_text(updated_text, encoding="utf-8-sig")
    return replacements, changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Signale les écarts sans modifier les fichiers.",
    )
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"[ERREUR] Base ESS introuvable : {DB_PATH}")
        return 1

    with sqlite3.connect(DB_PATH) as connection:
        rules = build_rules(connection)

    changed_files = 0
    total_replacements = 0
    for file_name in sorted({rule.file_name for rule in rules}):
        path = CHAPTER_DIR / file_name
        file_rules = [rule for rule in rules if rule.file_name == file_name]
        replacements, changed = update_file(path, file_rules, args.check)
        total_replacements += replacements
        changed_files += int(changed)
        status = "écart(s)" if args.check else "cellule(s) actualisée(s)"
        print(f"{file_name}: {replacements} {status}")

    if args.check and changed_files:
        print(f"[ECART] {changed_files} fichier(s) nécessitent un rafraîchissement.")
        return 1
    print(f"[OK] {total_replacements} cellule(s), {changed_files} fichier(s) modifié(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
