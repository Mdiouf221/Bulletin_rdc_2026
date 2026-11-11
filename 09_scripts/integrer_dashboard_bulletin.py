"""
integrer_dashboard_bulletin.py
------------------------------
Injecte automatiquement les valeurs ODD 1.3.1 du dashboard dans les tableaux
des chapitres 4 et 5, en réutilisant les décisions et dénominateurs persistés
dans 10_output/dashboard_settings.json.

Usage :
    py 09_scripts/integrer_dashboard_bulletin.py
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
import sys
from functools import lru_cache
from pathlib import Path

from visualiser_regimes import (  # type: ignore
    DB_PATH,
    build_indicateurs_payload,
    build_odd_programmes_payload,
    load_all,
)

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_PATH = BASE_DIR / "10_output" / "dashboard_settings.json"
QUESTIONNAIRE_PATH = BASE_DIR / "10_output" / "questionnaire_data.json"
TARGETS = (
    (
        BASE_DIR / "03_chapitres" / "chapitre_4" / "4.9_odd_131.md",
        {
            "Population totale (%)": "global_131",
            "Population 0–17 ans (%)": "ind_22_enfants",
            "Femmes ayant accouché — allocation de maternité CNSS (%)": "ind_23_maternite",
            "Personnes âgées — pension vieillesse (%)": "ind_27_vieillesse",
            "Actifs — cotisants à un régime contributif (%)": "ind_29_cotisants",
            "Personnes handicapées — invalidité (%)": "ind_24_handicap",
            "Force de travail — AT/MP (%)": "ind_25_atmp",
            "Personnes vulnérables — assistance sociale (%)": "ind_28_vulnerables",
        },
    ),
    (
        BASE_DIR / "03_chapitres" / "chapitre_5" / "00_plan_chapitre_5.md",
        {
            "Population totale (%)": "global_131",
            "Population 0–17 ans (%)": "ind_22_enfants",
            "Femmes ayant accouché — allocation de maternité CNSS (%)": "ind_23_maternite",
            "Personnes âgées — pension vieillesse (%)": "ind_27_vieillesse",
            "Actifs — cotisants à un régime contributif (%)": "ind_29_cotisants",
            "Personnes handicapées — invalidité (%)": "ind_24_handicap",
            "Force de travail — AT/MP (%)": "ind_25_atmp",
            "Personnes vulnérables — assistance sociale (%)": "ind_28_vulnerables",
        },
    ),
)
DENOM_DB_PATH = BASE_DIR / "protection_sociale_rdc.db"

INCLUDED_STATES = {"entierement_inclus", "inclus", "inclus_avec_reserve"}
EXCLUDED_STATES = {"entierement_exclus", "exclus", "exclu_nature", "exclu_non_statutaire", "exclu_hors_indicateur"}

METRIC_BY_INDICATOR = {
    "global_131": "couverts_bruts_estimes",
    "ind_22_enfants": "beneficiaires_estimes",
    "ind_23_maternite": "beneficiaires_estimes",
    "ind_24_handicap": "beneficiaires_estimes",
    "ind_25_atmp": "couverts_bruts_estimes",
    "ind_27_vieillesse": "beneficiaires_estimes",
    "ind_28_vulnerables": "beneficiaires_estimes",
    "ind_29_cotisants": "cotisants_estimes",
}

LOCAL_DENOM_MAP = {
    "global_131": ("var-c-popsx", "sex-t", "age-0+"),
    "ind_22_enfants": ("var-c-popsx", "sex-t", "age-0-17"),
    "ind_25_atmp": ("var-c-lf", "sex-t", "age-15+"),
    "ind_27_vieillesse": ("var-c-popsx", "sex-t", "age-60+"),
    "ind_29_cotisants": ("var-c-popsx", "sex-t", "age-15-64"),
}


def normalize_decision(node_type: str, raw_decision: str | None) -> str:
    decision = (raw_decision or "").strip()
    if node_type in {"institution_ess", "regime_ess"}:
        if decision in INCLUDED_STATES:
            return "entierement_inclus"
        if decision in EXCLUDED_STATES:
            return "entierement_exclus"
        return "autres"
    if node_type == "prestation_ess":
        if decision in INCLUDED_STATES:
            return "inclus"
        if decision in EXCLUDED_STATES:
            return "exclus"
        return "exclus"
    return decision or "en_discussion"


def default_decision(node_type: str) -> str:
    if node_type in {"institution_ess", "regime_ess"}:
        return "autres"
    if node_type == "prestation_ess":
        return "exclus"
    return "en_discussion"


def has_explicit_decision(
    program: dict,
    indicator_key: str,
    year_key: str,
    decisions: dict[str, str],
) -> bool:
    pid = str(program.get("id") or "")
    keys = [f"{pid}::{indicator_key}::{year_key}", f"{pid}::{indicator_key}"]
    keys.extend(
        key
        for alias in program.get("legacy_ids") or []
        for key in (
            f"{str(alias or '')}::{indicator_key}::{year_key}",
            f"{str(alias or '')}::{indicator_key}",
        )
    )
    return any(key in decisions for key in keys)


def decision_for_program(program: dict, indicator_key: str, year_key: str, decisions: dict[str, str]) -> str:
    node_type = str(program.get("type") or "")
    pid = str(program.get("id") or "")
    scoped_key = f"{pid}::{indicator_key}::{year_key}"
    legacy_key = f"{pid}::{indicator_key}"
    if scoped_key in decisions:
        return normalize_decision(node_type, decisions[scoped_key])
    if legacy_key in decisions:
        return normalize_decision(node_type, decisions[legacy_key])
    for alias in program.get("legacy_ids") or []:
        alias_id = str(alias or "")
        alias_scoped = f"{alias_id}::{indicator_key}::{year_key}"
        alias_legacy = f"{alias_id}::{indicator_key}"
        if alias_scoped in decisions:
            return normalize_decision(node_type, decisions[alias_scoped])
        if alias_legacy in decisions:
            return normalize_decision(node_type, decisions[alias_legacy])
    return normalize_decision(node_type, default_decision(node_type))


def effective_decision(
    node_id: str,
    indicator_key: str,
    year_key: str,
    node_map: dict[str, dict],
    decisions: dict[str, str],
    memo: dict[str, str],
) -> str:
    if node_id not in node_map:
        return "en_discussion"
    memo_key = f"{node_id}::{year_key}"
    if memo_key in memo:
        return memo[memo_key]
    node = node_map[node_id]
    own = decision_for_program(node, indicator_key, year_key, decisions)
    explicit = has_explicit_decision(node, indicator_key, year_key, decisions)
    parent_id = str(node.get("parent_id") or "")
    if not parent_id or parent_id not in node_map:
        memo[memo_key] = own
        return own
    parent_eff = effective_decision(parent_id, indicator_key, year_key, node_map, decisions, memo)
    if parent_eff in {"entierement_exclus", "exclus"}:
        forced = "exclus" if node.get("type") == "prestation_ess" else "entierement_exclus"
        memo[memo_key] = forced
        return forced
    if parent_eff in {"entierement_inclus", "inclus"}:
        if node.get("type") == "prestation_ess" and explicit and own == "exclus":
            memo[memo_key] = own
            return own
        forced = "inclus" if node.get("type") == "prestation_ess" else "entierement_inclus"
        memo[memo_key] = forced
        return forced
    memo[memo_key] = own
    return own


@lru_cache(maxsize=1)
def load_questionnaire_data() -> dict:
    if not QUESTIONNAIRE_PATH.exists():
        raise FileNotFoundError(f"Matrice Q1 introuvable : {QUESTIONNAIRE_PATH}")
    with QUESTIONNAIRE_PATH.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"Matrice Q1 invalide : {QUESTIONNAIRE_PATH}")
    return data


def build_q1_regime_groups(questionnaire_data: dict) -> dict[tuple[str, str], tuple[str, str]]:
    """Construit les groupes de régimes à ne compter qu'une fois selon Q1."""
    groups: dict[tuple[str, str], tuple[str, str]] = {}
    for institution, settings in questionnaire_data.items():
        if not isinstance(settings, dict):
            continue
        parent: dict[str, str] = {}

        def find(regime: str) -> str:
            if regime not in parent:
                parent[regime] = regime
            if parent[regime] != regime:
                parent[regime] = find(parent[regime])
            return parent[regime]

        for pair, value in (settings.get("Q1") or {}).items():
            if value != "true":
                continue
            regimes = str(pair).split("__")
            if len(regimes) != 2 or not all(regimes):
                continue
            parent[find(regimes[0])] = find(regimes[1])

        for regime in parent:
            groups[(str(institution), regime)] = (str(institution), find(regime))
    return groups


def compute_numerator(
    indicator_key: str,
    year: int,
    regime_rows: list[dict],
    prestation_rows: list[dict],
    odd_nodes: list[dict],
    decisions: dict[str, str],
    questionnaire_data: dict | None = None,
) -> float | None:
    if indicator_key == "ind_28_vulnerables":
        children = _compute_numerator_for_indicator(
            "ind_22_enfants",
            year,
            regime_rows,
            prestation_rows,
            odd_nodes,
            decisions,
            questionnaire_data,
        )
        assistance = _compute_numerator_for_indicator(
            "ind_28_vulnerables",
            year,
            regime_rows,
            prestation_rows,
            odd_nodes,
            decisions,
            questionnaire_data,
        )
        if children is None and assistance is None:
            return None
        return (children or 0.0) + (assistance or 0.0)

    return _compute_numerator_for_indicator(
        indicator_key,
        year,
        regime_rows,
        prestation_rows,
        odd_nodes,
        decisions,
        questionnaire_data,
    )


def _compute_numerator_for_indicator(
    indicator_key: str,
    year: int,
    regime_rows: list[dict],
    prestation_rows: list[dict],
    odd_nodes: list[dict],
    decisions: dict[str, str],
    questionnaire_data: dict | None = None,
) -> float | None:
    metric_key = METRIC_BY_INDICATOR[indicator_key]
    include_cotisants = metric_key in {"cotisants_estimes", "couverts_bruts_estimes"}
    include_beneficiaires = metric_key in {"beneficiaires_estimes", "couverts_bruts_estimes"}

    node_map = {str(node.get("id")): node for node in odd_nodes if node.get("id")}
    memo: dict[str, str] = {}
    year_key = str(year)
    included_regimes = {
        node_id
        for node_id, node in node_map.items()
        if node.get("type") == "regime_ess"
        and effective_decision(node_id, indicator_key, year_key, node_map, decisions, memo) in INCLUDED_STATES
    }
    included_prestations = {
        node_id
        for node_id, node in node_map.items()
        if node.get("type") == "prestation_ess"
        and effective_decision(node_id, indicator_key, year_key, node_map, decisions, memo) in INCLUDED_STATES
    }

    if include_cotisants and included_prestations:
        for prestation_id in tuple(included_prestations):
            parent = str((node_map.get(prestation_id) or {}).get("parent_id") or "")
            if parent:
                included_regimes.add(parent)

    total = 0.0
    found_observation = False
    if include_cotisants:
        q1_groups = build_q1_regime_groups(
            questionnaire_data if questionnaire_data is not None else load_questionnaire_data()
        )
        contributor_groups: dict[tuple[str, str], float] = {}
        for row in regime_rows:
            if int(row.get("annee") or -1) != year:
                continue
            if str(row.get("programme_id") or "") not in included_regimes:
                continue
            raw_value = row.get("cotisants")
            if raw_value is None:
                continue
            found_observation = True
            value = float(raw_value)
            if value > 0:
                group = q1_groups.get(
                    (str(row.get("institution") or ""), str(row.get("regime_code") or "")),
                    (str(row.get("institution") or ""), str(row.get("regime_code") or "")),
                )
                contributor_groups[group] = max(contributor_groups.get(group, 0.0), value)
        total += sum(contributor_groups.values())
    if include_beneficiaires:
        for row in prestation_rows:
            if int(row.get("annee") or -1) != year:
                continue
            if str(row.get("programme_id") or "") not in included_prestations:
                continue
            raw_value = row.get("beneficiaires")
            if raw_value is None:
                continue
            found_observation = True
            value = float(raw_value)
            if value > 0:
                total += value
    if not found_observation:
        # Aucune ligne ESS incluse pour cette année/cet indicateur : donnée absente,
        # à distinguer d'une couverture réellement nulle (voir constat de révision 2026-09-02).
        return None
    return total


def compute_numerator_breakdown(
    indicator_key: str,
    year: int,
    regime_rows: list[dict],
    prestation_rows: list[dict],
    odd_nodes: list[dict],
    decisions: dict[str, str],
) -> list[dict]:
    """Détail des régimes/prestations inclus dans le numérateur d'un indicateur, pour une
    année donnée — même logique d'inclusion/exclusion que `compute_numerator`, mais restituée
    ligne par ligne (au lieu d'un total) pour la traçabilité du calcul (Annexe C)."""
    if indicator_key == "ind_28_vulnerables":
        children = _compute_numerator_breakdown_for_indicator(
            "ind_22_enfants",
            year,
            regime_rows,
            prestation_rows,
            odd_nodes,
            decisions,
        )
        assistance = _compute_numerator_breakdown_for_indicator(
            "ind_28_vulnerables",
            year,
            regime_rows,
            prestation_rows,
            odd_nodes,
            decisions,
        )
        return children + assistance

    return _compute_numerator_breakdown_for_indicator(
        indicator_key,
        year,
        regime_rows,
        prestation_rows,
        odd_nodes,
        decisions,
    )


def _compute_numerator_breakdown_for_indicator(
    indicator_key: str,
    year: int,
    regime_rows: list[dict],
    prestation_rows: list[dict],
    odd_nodes: list[dict],
    decisions: dict[str, str],
) -> list[dict]:
    metric_key = METRIC_BY_INDICATOR[indicator_key]
    include_cotisants = metric_key in {"cotisants_estimes", "couverts_bruts_estimes"}
    include_beneficiaires = metric_key in {"beneficiaires_estimes", "couverts_bruts_estimes"}

    node_map = {str(node.get("id")): node for node in odd_nodes if node.get("id")}
    memo: dict[str, str] = {}
    year_key = str(year)
    included_regimes = {
        node_id
        for node_id, node in node_map.items()
        if node.get("type") == "regime_ess"
        and effective_decision(node_id, indicator_key, year_key, node_map, decisions, memo) in INCLUDED_STATES
    }
    included_prestations = {
        node_id
        for node_id, node in node_map.items()
        if node.get("type") == "prestation_ess"
        and effective_decision(node_id, indicator_key, year_key, node_map, decisions, memo) in INCLUDED_STATES
    }
    if include_cotisants and included_prestations:
        for prestation_id in tuple(included_prestations):
            parent = str((node_map.get(prestation_id) or {}).get("parent_id") or "")
            if parent:
                included_regimes.add(parent)

    items: list[dict] = []
    if include_cotisants:
        for row in regime_rows:
            if int(row.get("annee") or -1) != year:
                continue
            pid = str(row.get("programme_id") or "")
            if pid not in included_regimes:
                continue
            raw_value = row.get("cotisants")
            if raw_value is None:
                continue
            value = float(raw_value)
            node = node_map.get(pid) or {}
            items.append({
                "id": pid,
                "kind": "regime",
                "institution": row.get("institution"),
                "regime_code": row.get("regime_code"),
                "label": row.get("nom_regime") or node.get("programme") or pid,
                "metric": "cotisants",
                "value": value,
            })
    if include_beneficiaires:
        for row in prestation_rows:
            if int(row.get("annee") or -1) != year:
                continue
            pid = str(row.get("programme_id") or "")
            if pid not in included_prestations:
                continue
            raw_value = row.get("beneficiaires")
            if raw_value is None:
                continue
            value = float(raw_value)
            node = node_map.get(pid) or {}
            items.append({
                "id": pid,
                "kind": "prestation",
                "institution": row.get("institution"),
                "regime_code": row.get("regime_code"),
                "label": row.get("nom_prestation") or node.get("programme") or pid,
                "metric": "beneficiaires",
                "value": value,
            })
    return items


def fetch_local_denom(cursor: sqlite3.Cursor, key: str, year: int, denom_settings: dict) -> float | None:
    if key == "ind_24_handicap":
        cursor.execute(
            """
            SELECT val_n FROM denominateurs_ref
            WHERE iso3='COD' AND var_code='var-c-dirt' AND class_sex='sex-t' AND class_age='age-0+' AND year=?
            ORDER BY priority DESC, id ASC LIMIT 1
            """,
            (year,),
        )
        rate = cursor.fetchone()
        cursor.execute(
            """
            SELECT val_n FROM denominateurs_ref
            WHERE iso3='COD' AND var_code='var-c-popsx' AND class_sex='sex-t' AND class_age='age-0+' AND year=?
            ORDER BY priority DESC, id ASC LIMIT 1
            """,
            (year,),
        )
        pop = cursor.fetchone()
        if pop and rate:
            return float(pop[0]) * float(rate[0]) / 100.0
        if pop:
            prevalence = float(denom_settings.get("handicap_prevalence_percent") or 15)
            return float(pop[0]) * prevalence / 100.0
        return None

    mapping = LOCAL_DENOM_MAP.get(key)
    if not mapping:
        return None
    var_code, sex, age = mapping
    cursor.execute(
        """
        SELECT val_n FROM denominateurs_ref
        WHERE iso3='COD' AND var_code=? AND class_sex=? AND class_age=? AND year=?
        ORDER BY priority DESC, id ASC LIMIT 1
        """,
        (var_code, sex, age, year),
    )
    row = cursor.fetchone()
    return float(row[0]) if row and row[0] is not None else None


def get_denominator_value(
    indicator_key: str,
    year: int,
    denom_constructions: dict,
    denom_settings: dict,
    cursor: sqlite3.Cursor | None,
    regime_rows: list[dict] | None = None,
    prestation_rows: list[dict] | None = None,
    odd_nodes: list[dict] | None = None,
    decisions: dict[str, str] | None = None,
) -> float | None:
    if indicator_key == "ind_28_vulnerables":
        if not all(value is not None for value in (regime_rows, prestation_rows, odd_nodes, decisions)):
            return None
        population_total = get_denominator_value(
            "global_131",
            year,
            denom_constructions,
            denom_settings,
            cursor,
        )
        cotisants = compute_numerator(
            "ind_29_cotisants",
            year,
            regime_rows or [],
            prestation_rows or [],
            odd_nodes or [],
            decisions or {},
        )
        pensionnes = compute_numerator(
            "ind_27_vieillesse",
            year,
            regime_rows or [],
            prestation_rows or [],
            odd_nodes or [],
            decisions or {},
        )
        if population_total is None or cotisants is None or pensionnes is None:
            return None
        denominator = population_total - cotisants - pensionnes
        return denominator if denominator > 0 else None

    construction = denom_constructions.get(f"{indicator_key}::{year}") or {}
    value = construction.get("value")
    if value is not None:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            parsed = None
        if parsed is not None and math.isfinite(parsed) and parsed > 0:
            return parsed
    if cursor is None:
        return None
    return fetch_local_denom(cursor, indicator_key, year, denom_settings)


def format_pct(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "[N/D]"
    return f"{value:.1f}".replace(".", ",")


def replace_table_row(markdown_text: str, row_label: str, values: list[str], target_path: Path) -> str:
    escaped = re.escape(row_label)
    row_pattern = re.compile(rf"^\| {escaped} \|.*$", re.MULTILINE)
    replacement = f"| {row_label} | " + " | ".join(values) + " |"
    if not row_pattern.search(markdown_text):
        raise ValueError(f"Ligne introuvable dans {target_path} : {row_label}")
    return row_pattern.sub(replacement, markdown_text, count=1)


def parse_table_years(markdown_text: str) -> list[int]:
    years: list[int] = []
    for line in markdown_text.splitlines():
        if not line.startswith("| Sous-indicateur ODD 1.3.1 |"):
            continue
        candidate_years = [int(token) for token in re.findall(r"\b(19\d{2}|20\d{2}|21\d{2})\b", line)]
        if len(candidate_years) >= 2:
            years = candidate_years
            break
    if not years:
        raise ValueError("Aucune année détectée dans le tableau 5.2.")
    return years


def main() -> int:
    if not DB_PATH.exists():
        print(f"[ERREUR] Base introuvable : {DB_PATH}")
        return 1
    if not SETTINGS_PATH.exists():
        print(f"[ERREUR] Fichier introuvable : {SETTINGS_PATH}")
        return 1
    for target_path, _row_map in TARGETS:
        if not target_path.exists():
            print(f"[ERREUR] Fichier introuvable : {target_path}")
            return 1

    regimes, prestations, regime_meta, prestation_meta = load_all(DB_PATH)
    indicateurs = build_indicateurs_payload(regimes, prestations)
    odd_nodes = build_odd_programmes_payload(regimes, prestations, regime_meta, prestation_meta)
    regime_rows = indicateurs.get("rows_regimes") or []
    prestation_rows = indicateurs.get("rows_prestations") or []
    years_available = sorted(
        {
            int(y)
            for y in (indicateurs.get("years_numerator") or indicateurs.get("years") or [])
            if isinstance(y, int) or (isinstance(y, float) and y.is_integer())
        }
    )

    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    decisions = settings.get("oddDecisions") or {}
    denom_settings = settings.get("denomSettings") or {}
    denom_constructions = denom_settings.get("denominatorConstructions") or {}

    denom_conn = sqlite3.connect(DENOM_DB_PATH) if DENOM_DB_PATH.exists() else None
    cursor = None
    if denom_conn is not None:
        try:
            test_cur = denom_conn.cursor()
            test_cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='denominateurs_ref' LIMIT 1"
            )
            if test_cur.fetchone():
                cursor = test_cur
            else:
                test_cur.close()
        except sqlite3.Error:
            cursor = None
    try:
        updated_targets = []
        for target_path, row_map in TARGETS:
            chapter_text = target_path.read_text(encoding="utf-8-sig")
            table_years = parse_table_years(chapter_text)
            for row_label, indicator_key in row_map.items():
                values = []
                for year in table_years:
                    if year not in years_available:
                        values.append("[N/D]")
                        continue
                    numerator = compute_numerator(
                        indicator_key=indicator_key,
                        year=year,
                        regime_rows=regime_rows,
                        prestation_rows=prestation_rows,
                        odd_nodes=odd_nodes,
                        decisions=decisions,
                    )
                    denominator = get_denominator_value(
                        indicator_key=indicator_key,
                        year=year,
                        denom_constructions=denom_constructions,
                        denom_settings=denom_settings,
                        cursor=cursor,
                        regime_rows=regime_rows,
                        prestation_rows=prestation_rows,
                        odd_nodes=odd_nodes,
                        decisions=decisions,
                    )
                    ratio = (
                        (numerator / denominator * 100.0)
                        if (numerator is not None and denominator and denominator > 0)
                        else None
                    )
                    values.append(format_pct(ratio))
                chapter_text = replace_table_row(chapter_text, row_label, values, target_path)

            chapter_text = chapter_text.replace(
                "Les estimations [EST.] seront calculées par le script `generer_figures_ch4.py` depuis la base.",
                "Les valeurs du tableau sont générées automatiquement depuis le dashboard via le script `integrer_dashboard_bulletin.py`.",
            )
            target_path.write_text(chapter_text, encoding="utf-8-sig")
            updated_targets.append(target_path)
    finally:
        if denom_conn is not None:
            denom_conn.close()

    for target_path in updated_targets:
        print(f"[OK] Tableau ODD 1.3.1 mis à jour : {target_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
