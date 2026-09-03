"""
generer_annexe_c_visuels.py
============================
Génère les visuels et tableaux statiques de l'annexe C (détail des indicateurs de
couverture) directement à partir de la base ESS et des décisions/dénominateurs du
tableau de bord — sans navigateur, sans capture d'écran.

Pour chaque indicateur ODD 1.3.1 / BIT (même liste que le sélecteur de l'onglet
« Indicateurs » du tableau de bord), régénère automatiquement un tableau unique
(inspiré du Tableau 14 du premier bulletin RDC), pensé pour rester lisible et
compact (institutions désignées par leur sigle, sources du dénominateur en note
de bas de page factorisée par plage d'années) :
  1. Un encadré méthodologique (définition, numérateur, dénominateur, formule).
  2. Un tableau de synthèse 2019-2025 à colonnes années partagées :
     - la ligne « Indicateur de couverture (%) » ;
     - la ligne « Numérateur », suivie immédiatement de ses lignes de détail en
       italique — un en-tête « Dont [régime] (SIGLE, cotisants) » par régime
       contributeur, puis ses prestations en sous-lignes indentées
       « ↳ [prestation] (bénéf.) » qui ne répètent ni l'institution (remplacée par
       son sigle — cf. Liste des sigles et acronymes) ni le régime, déjà portés
       par la ligne d'en-tête ;
     - la ligne « Dénominateur », dont le détail de construction est renvoyé en
       note de bas de page (`span.footnote`, convertie en vraie note Word à
       l'export) et factorisé par plage d'années consécutives partageant la même
       source (ex. « 2019–2024 : Base OIT ; 2026 : Saisie manuelle ») plutôt que
       répété une fois par année.
  3. Deux graphiques PNG (indicateur en %, numérateur en nombre de personnes) exportés
     via Plotly/kaleido, avec le même style que le tableau de bord et l'annexe B.
     Aucun graphique pour le dénominateur (non demandé).

Les indicateurs 2.6 (chômage) et 2.8 (vulnérables) ne disposent d'aucune règle de
calcul opérationnelle dans la base actuelle : seul l'encadré méthodologique est
généré pour eux, avec une note explicite d'indisponibilité — jamais de valeur
inventée.

Le contenu généré est injecté dans 04_annexes/annexe_C_detail_indicateurs.md entre
les marqueurs :
    <!-- AUTO_GENERE:<INDICATEUR>:DEBUT -->
    ...
    <!-- AUTO_GENERE:<INDICATEUR>:FIN -->
Le texte rédigé manuellement en dehors de ces marqueurs (introduction, NOTE_INTERNE)
n'est jamais modifié.

Usage :
    py 09_scripts/generer_annexe_c_visuels.py
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import plotly.graph_objects as go
except ImportError:
    sys.exit("Plotly requis : py -m pip install plotly")

try:
    import kaleido
except ImportError:
    kaleido = None

from visualiser_regimes import (  # noqa: E402
    DB_PATH,
    NOM_COURT,
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
ILLUSTRATIONS_DIR = WORKSPACE / "04_annexes" / "illustrations"
ANNEXE_C_MD = WORKSPACE / "04_annexes" / "annexe_C_detail_indicateurs.md"

CHART_WIDTH = 900
CHART_HEIGHT = 420
CHART_SCALE = 2

# Le bulletin couvre 2019-2025 : cf. generer_annexe_b_visuels.py — toute année de
# cette plage sans donnée apparaît explicitement comme [N/D], jamais omise.
BULLETIN_YEARS = list(range(2019, 2026))

COLOR_INDICATOR = "#2c5282"
COLOR_NUMERATOR = "#2e78c8"

# Reprend telles quelles les définitions BIT/OIT du tableau de bord
# (visualiser_regimes.py, ODD_METHODOLOGY_SPECS côté JavaScript) — source unique
# des libellés méthodologiques, pour ne jamais les faire diverger entre le
# tableau de bord interactif et le présent bulletin.
ODD_METHODOLOGY_SPECS = {
    "global_131": {
        "definition": "Proportion de la population couverte par au moins une prestation en espèces de protection sociale ou cotisant activement à au moins un régime de sécurité sociale.",
        "numerator": "Nombre de personnes recevant au moins une prestation en espèces de protection sociale, hors soins de santé, ou cotisant activement à au moins un régime de sécurité sociale, sans double comptage.",
        "denominator": "Population totale.",
        "formula": "Population couverte par au moins une prestation ou cotisant activement ÷ population totale × 100.",
    },
    "ind_22_enfants": {
        "definition": "Proportion d'enfants bénéficiant d'au moins une prestation en espèces de protection sociale destinée aux enfants ou aux familles.",
        "numerator": "Nombre d'enfants recevant au moins une prestation en espèces pour enfants ou famille.",
        "denominator": "Population totale des enfants dans la tranche d'âge retenue.",
        "formula": "Enfants bénéficiaires ÷ population totale des enfants × 100.",
    },
    "ind_23_maternite": {
        "definition": "Proportion de femmes ayant accouché qui reçoivent une prestation en espèces de maternité.",
        "numerator": "Nombre de femmes ayant accouché et percevant une indemnité ou une allocation de maternité en espèces.",
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
        "numerator": "Nombre de personnes ayant atteint l'âge légal de la retraite et percevant effectivement une pension ou une prestation de vieillesse.",
        "denominator": "Population totale ayant atteint l'âge légal de la retraite, lequel peut différer selon le sexe ou le régime.",
        "formula": "Bénéficiaires de prestations de vieillesse ÷ population ayant atteint l'âge légal de la retraite × 100.",
    },
    "ind_28_vulnerables": {
        "definition": "Proportion de personnes vulnérables qui reçoivent une prestation d'assistance sociale en espèces.",
        "numerator": "Nombre de personnes vulnérables percevant une prestation d'assistance sociale en espèces.",
        "denominator": "Population vulnérable, obtenue en retranchant de la population totale les personnes en âge de travailler cotisant à une assurance sociale ou percevant une prestation contributive, ainsi que les personnes d'âge légal de la retraite percevant une prestation contributive.",
        "formula": "Personnes vulnérables bénéficiaires d'une prestation d'assistance sociale ÷ population vulnérable × 100.",
    },
    "ind_29_cotisants": {
        "definition": "Proportion de la population en âge de travailler qui cotise activement à un régime de retraite contributif.",
        "numerator": "Nombre de personnes cotisant activement à un régime de retraite contributif.",
        "denominator": "Population en âge de travailler (15-64 ans, Banque mondiale SP.POP.1564.TO) — voir DM-016.",
        "formula": "Cotisants actifs à un régime de retraite ÷ population en âge de travailler (15-64 ans) × 100.",
    },
}

NON_CALCULABLE_NOTE = {
    "ind_26_chomage": "Aucun régime d'assurance chômage opérationnel n'est identifié dans les ESS disponibles : ni numérateur ni dénominateur ne peuvent être calculés à ce stade.",
    "ind_28_vulnerables": "La population vulnérable et ses bénéficiaires d'assistance sociale ne font l'objet d'aucune mesure individualisable dans les sources actuellement disponibles : cet indicateur n'est pas calculé dans la présente édition.",
}


def fmt_int(value: float | None) -> str:
    if value is None:
        return "[N/D]"
    return f"{value:,.0f}"


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "[N/D]"
    return f"{value:.1f}".replace(".", ",")


def _write_image_with_retry(fig, out_path: Path, *, width: int, height: int, scale: int,
                             retries: int = 2, delay: float = 1.5) -> bool:
    import time
    last_exc = None
    for attempt in range(retries + 1):
        try:
            fig.write_image(str(out_path), width=width, height=height, scale=scale)
            return True
        except Exception as exc:  # pragma: no cover - dépend de l'environnement kaleido
            last_exc = exc
            if attempt < retries:
                time.sleep(delay)
    print(f"    [AVERT] Export image '{out_path.name}' échoué après {retries + 1} tentative(s) : {last_exc}")
    return False


def build_fig_indicator_ratio(years: list[int], values: list[float | None], label: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years, y=values,
        mode="lines+markers",
        line=dict(color=COLOR_INDICATOR, width=2.5),
        marker=dict(size=7, color=COLOR_INDICATOR),
        connectgaps=False,
        hovertemplate="%{x}<br>%{y:.1f} %<extra></extra>",
    ))
    fig.update_layout(
        title=dict(
            text=f"{label} — Indicateur de couverture (%)",
            font=dict(size=13, family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color=COLOR_INDICATOR, weight=700),
            x=0.5, xanchor="center",
        ),
        height=CHART_HEIGHT,
        hovermode="x unified",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(t=55, b=45, l=60, r=30, autoexpand=False),
        font=dict(family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', size=12, color="#4a5568"),
        showlegend=False,
    )
    fig.update_xaxes(tickformat="d", dtick=1, showgrid=True, gridcolor="#f0f0f0", showline=True, linewidth=1, linecolor="#e2e8f0")
    fig.update_yaxes(ticksuffix=" %", showgrid=True, gridcolor="#f0f0f0", showline=True, linewidth=1, linecolor="#e2e8f0", rangemode="tozero")
    return fig


def build_fig_indicator_numerator(years: list[int], values: list[float | None], label: str):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=values,
        marker=dict(color=COLOR_NUMERATOR, line=dict(width=0)),
        opacity=0.85,
        hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(
            text=f"{label} — Numérateur (nombre de personnes)",
            font=dict(size=13, family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color=COLOR_INDICATOR, weight=700),
            x=0.5, xanchor="center",
        ),
        height=CHART_HEIGHT,
        hovermode="x unified",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(t=55, b=45, l=70, r=30, autoexpand=False),
        font=dict(family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', size=12, color="#4a5568"),
        showlegend=False,
    )
    fig.update_xaxes(tickformat="d", dtick=1, showgrid=True, gridcolor="#f0f0f0", showline=True, linewidth=1, linecolor="#e2e8f0")
    fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0", showline=True, linewidth=1, linecolor="#e2e8f0", separatethousands=True, rangemode="tozero")
    return fig


ACRONYME_OVERRIDES = {
    # TRESOR n'est pas un sigle institutionnel au sens strict (mécanisme budgétaire),
    # d'où une graphie capitalisée normale plutôt que tout-majuscules.
    "TRESOR": "proxy budgétaire hors CNSSAP",
}


def _institution_acronym(code: str | None) -> str:
    code = code or ""
    return ACRONYME_OVERRIDES.get(code, code)


def _sanitize_table_cell(text: str) -> str:
    """Neutralise les caractères qui casseraient la syntaxe de tableau Markdown."""
    return text.replace("|", "/").replace("\n", " ").strip()


def _format_component_row(label: str, item: dict, years: list[int], years_available: set[int]) -> str:
    cells = []
    for y in years:
        if y not in years_available:
            cells.append("[N/D]")
        elif y in item["values"]:
            cells.append(fmt_int(item["values"][y]))
        else:
            cells.append("—")
    sanitized = _sanitize_table_cell(label)
    return f"| *{sanitized}* | " + " | ".join(f"*{c}*" for c in cells) + " |"


def _build_breakdown_rows(components: dict[str, dict], years: list[int], years_available: set[int]) -> list[str]:
    """Regroupe les composantes du numérateur par régime pour éviter de répéter
    l'institution (remplacée par son sigle — cf. Liste des sigles et acronymes) et le
    régime sur chaque ligne : une ligne d'en-tête « Dont [régime/prestation] (SIGLE,
    métrique) » est suivie, le cas échéant, de ses prestations en sous-lignes
    « ↳ [prestation] (bénéf.) » qui ne répètent ni l'institution ni le régime, déjà
    portés par la ligne d'en-tête juste au-dessus."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for item in components.values():
        key = (item.get("institution") or "", item.get("regime_code") or "")
        groups.setdefault(key, []).append(item)

    def _group_sort_key(entry: tuple[tuple[str, str], list[dict]]):
        (inst, rc), _items = entry
        return (inst, rc)

    rows: list[str] = []
    for (inst, rc), items in sorted(groups.items(), key=_group_sort_key):
        acronym = _institution_acronym(inst)
        regime_item = next((it for it in items if it["kind"] == "regime"), None)
        prestation_items = sorted(
            (it for it in items if it["kind"] == "prestation"),
            key=lambda it: it.get("label") or "",
        )
        if regime_item is not None:
            header_item = regime_item
            metric = "personnes potentiellement couvertes estimées" if inst == "TRESOR" else "cotisants"
            header_label = f"Dont {header_item['label']} ({acronym}, {metric})"
            sub_items = prestation_items
        else:
            header_item = prestation_items[0]
            regime_label = NOM_COURT.get(rc, rc)
            header_label = f"Dont {header_item['label']} — {regime_label} ({acronym}, bénéf.)"
            sub_items = prestation_items[1:]
        rows.append(_format_component_row(header_label, header_item, years, years_available))
        for it in sub_items:
            sub_label = f"↳ {it['label']} (bénéf.)"
            rows.append(_format_component_row(sub_label, it, years, years_available))
    return rows


def build_methodology_box(indicator_key: str) -> str:
    # Paragraphes ordinaires (pas de blockquote) : même police/interligne que le
    # reste du texte, sans encadré — cohérent avec les autres paragraphes de
    # l'annexe (ex. « Lecture du numérateur et règle de dédoublonnage »).
    spec = ODD_METHODOLOGY_SPECS.get(indicator_key, ODD_METHODOLOGY_SPECS["global_131"])
    return (
        f"**Définition (BIT/OIT).** {spec['definition']}\n"
        f"\n"
        f"**Numérateur.** {spec['numerator']}\n"
        f"\n"
        f"**Dénominateur.** {spec['denominator']}\n"
        f"\n"
        f"**Formule.** {spec['formula']}\n"
    )


def build_synthesis_table(
    years: list[int],
    years_available: set[int],
    ratio: dict[int, float | None],
    numerator: dict[int, float | None],
    denominator: dict[int, float | None],
    components: dict[str, dict],
    denom_footnote: str,
    numerator_footnote: str = "",
) -> str:
    """Tableau unique : indicateur, numérateur (avec son détail en italique juste en
    dessous, à la manière du Tableau 14 du premier bulletin RDC — lignes « Dont … »
    indentées) puis dénominateur, dont le détail de construction est renvoyé en note
    de bas de page (span.footnote, converti en vraie note Word à l'export) plutôt
    qu'affiché en clair dans le corps du tableau."""
    header = "| | " + " | ".join(str(y) for y in years) + " |"
    sep = "|---|" + "|".join("---" for _ in years) + "|"
    row_ratio = "| **Indicateur de couverture (%)** | " + " | ".join(f"**{fmt_pct(ratio.get(y))}**" for y in years) + " |"
    numerator_footnote_html = (
        f'<span class="footnote">{_sanitize_table_cell(numerator_footnote)}</span>'
        if numerator_footnote else ""
    )
    row_num = (
        f"| **Numérateur (nombre de personnes)**{numerator_footnote_html} | "
        + " | ".join(f"**{fmt_int(numerator.get(y))}**" for y in years) + " |"
    )

    breakdown_rows = _build_breakdown_rows(components, years, years_available)

    footnote_html = f'<span class="footnote">{_sanitize_table_cell(denom_footnote)}</span>' if denom_footnote else ""
    row_den = (
        f"| Dénominateur (population de référence){footnote_html} | "
        + " | ".join(fmt_int(denominator.get(y)) for y in years) + " |"
    )

    lines = [header, sep, row_ratio, row_num, *breakdown_rows, row_den]
    return "\n".join(lines) + "\n"


def build_charts_markdown(ratio_file: str | None, numerator_file: str | None) -> str:
    def _cell(filename: str | None, label: str) -> str:
        if filename:
            return (
                '<td style="width:50%; padding:4px;">'
                f'<img src="/files/04_annexes/illustrations/{filename}" style="width:100%; height:auto;">'
                "</td>"
            )
        return (
            '<td style="width:50%; padding:4px;">'
            '<div style="min-height:160px; display:flex; align-items:center; justify-content:center; '
            'border:1px dashed #cbd5e0; border-radius:6px; color:#888; font-size:0.9em; text-align:center;">'
            f"[N/D] — {label}</div></td>"
        )
    return (
        '<table style="width:100%; border-collapse:collapse;">\n'
        f"<tr>{_cell(ratio_file, 'Indicateur')}{_cell(numerator_file, 'Numérateur')}</tr>\n"
        "</table>\n"
    )


def _strip_trailing_year(meta: str, year: int) -> str:
    """Retire un suffixe « (YYYY) » terminal correspondant à l'année en cours, afin de
    pouvoir comparer et regrouper le texte de source indépendamment de l'année."""
    return re.sub(rf"\s*\({year}\)\s*$", "", meta).strip()


def build_denominator_footnote(indicator_key: str, years: list[int], denom_constructions: dict) -> str:
    """Factorise, par plage d'années consécutives partageant la même source, le détail
    de construction du dénominateur — au lieu de répéter la même source une fois par
    année (ex. « 2019 : Base OIT (2019) ; 2020 : Base OIT (2020)… »), produit
    « 2019–2024 : Base OIT ; 2026 : Saisie manuelle (valeur manquante). »"""
    meta_by_year: dict[int, str] = {}
    for year in years:
        construction = denom_constructions.get(f"{indicator_key}::{year}") or {}
        meta = (construction.get("meta") or "").strip()
        if meta:
            meta_by_year[year] = _strip_trailing_year(meta, year)

    ordered_years = sorted(meta_by_year.keys())
    parts: list[str] = []
    i = 0
    n = len(ordered_years)
    while i < n:
        y0 = ordered_years[i]
        text0 = meta_by_year[y0]
        j = i
        while (
            j + 1 < n
            and ordered_years[j + 1] == ordered_years[j] + 1
            and meta_by_year[ordered_years[j + 1]] == text0
        ):
            j += 1
        y1 = ordered_years[j]
        year_label = str(y0) if y0 == y1 else f"{y0}–{y1}"
        parts.append(f"{year_label} : {text0}")
        i = j + 1

    if not parts:
        return (
            "Construction du dénominateur détaillée dans le tableau de bord (onglet "
            "« Indicateurs », panneau « Construction des dénominateurs »)."
        )
    return "Sources du dénominateur — " + " ; ".join(parts) + "."


def build_indicator_section(
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
) -> str:
    title = f"## C.{section_no} — {label}\n\n"
    methodology = build_methodology_box(indicator_key) + "\n"

    if indicator_key not in METRIC_BY_INDICATOR:
        note = NON_CALCULABLE_NOTE.get(
            indicator_key,
            "Cet indicateur n'est pas calculé dans la présente édition : données insuffisantes.",
        )
        return title + methodology + f"\n*{note}*\n"

    ratio: dict[int, float | None] = {}
    numerator: dict[int, float | None] = {}
    denominator: dict[int, float | None] = {}
    components: dict[str, dict] = {}

    for year in years:
        if year not in years_available:
            ratio[year] = None
            numerator[year] = None
            denominator[year] = None
            continue
        num_value = compute_numerator(indicator_key, year, regime_rows, prestation_rows, odd_nodes, decisions)
        den_value = get_denominator_value(indicator_key, year, denom_constructions, denom_settings, denom_cursor)
        numerator[year] = num_value
        denominator[year] = den_value
        ratio[year] = (num_value / den_value * 100.0) if (num_value is not None and den_value and den_value > 0) else None

        for item in compute_numerator_breakdown(indicator_key, year, regime_rows, prestation_rows, odd_nodes, decisions):
            comp = components.setdefault(item["id"], {
                "label": item["label"], "institution": item["institution"],
                "regime_code": item.get("regime_code"), "kind": item["kind"],
                "metric": item["metric"], "values": {},
            })
            comp["values"][year] = item["value"]

    denom_footnote = build_denominator_footnote(indicator_key, years, denom_constructions)
    numerator_footnote = (
        "Pour les allocations familiales de la CNSS, le nombre d'enfants bénéficiaires est estimé "
        "en multipliant par 3,17 le nombre de titulaires de prestations familiales communiqué par "
        "la CNSS. Ce facteur correspond au nombre moyen d'enfants de moins de 20 ans par foyer en "
        "RDC en 2013, d'après UN HH Size and Composition 2019. Il s'agit donc d'une estimation et "
        "non d'un décompte administratif direct d'enfants."
        if indicator_key == "ind_22_enfants" else ""
    )

    synthesis_md = build_synthesis_table(
        years,
        years_available,
        ratio,
        numerator,
        denominator,
        components,
        denom_footnote,
        numerator_footnote,
    )

    chart_years = [y for y in years if y in years_available]
    ratio_file = numerator_file = None
    if any(ratio.get(y) is not None for y in chart_years):
        fig = build_fig_indicator_ratio(years, [ratio.get(y) for y in years], label)
        fig.update_xaxes(range=[years[0] - 0.5, years[-1] + 0.5])
        ratio_file = f"annexe_C_{indicator_key}_indicateur.png"
        if not _write_image_with_retry(fig, ILLUSTRATIONS_DIR / ratio_file, width=CHART_WIDTH, height=CHART_HEIGHT, scale=CHART_SCALE):
            ratio_file = None
    if any(numerator.get(y) is not None for y in chart_years):
        fig = build_fig_indicator_numerator(years, [numerator.get(y) for y in years], label)
        fig.update_xaxes(range=[years[0] - 0.5, years[-1] + 0.5])
        numerator_file = f"annexe_C_{indicator_key}_numerateur.png"
        if not _write_image_with_retry(fig, ILLUSTRATIONS_DIR / numerator_file, width=CHART_WIDTH, height=CHART_HEIGHT, scale=CHART_SCALE):
            numerator_file = None
    charts_md = build_charts_markdown(ratio_file, numerator_file)

    inclusion_note = (
        "*Lignes « Dont … » / « ↳ … » : détail du numérateur — régimes (« Dont ») et prestations "
        "(« ↳ », sous le régime dont elles relèvent) classés « inclus » ou « inclus avec réserve » "
        "dans le module Décisions de l'onglet « Indicateurs » du tableau de bord, pour l'année et "
        "l'indicateur considérés. Institutions désignées par leur sigle (cf. Liste des sigles et "
        "acronymes). « — » : composante non incluse cette année-là (ou décision non encore "
        "documentée). « [N/D] » : aucune donnée ESS disponible cette année-là.*\n"
        if components else ""
    )

    return (
        title
        + methodology
        + f'\n<p class="table-caption"><strong>Tableau C.{section_no}</strong> — Indicateur de couverture, numérateur et dénominateur — {label} ({years[0]}–{years[-1]})</p>\n\n'
        + synthesis_md
        + "\n"
        + inclusion_note
        + "\n"
        + f'<p class="fig-caption"><strong>Figure C.{section_no}</strong> — Évolution de l\'indicateur de couverture (%) et du numérateur (effectifs) — {label} ({years[0]}–{years[-1]})</p>\n\n'
        + charts_md
    )


def inject_into_markdown(md_text: str, indicator_key: str, content: str) -> tuple[str, bool]:
    start_marker = f"<!-- AUTO_GENERE:{indicator_key}:DEBUT -->"
    end_marker = f"<!-- AUTO_GENERE:{indicator_key}:FIN -->"
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
    if not pattern.search(md_text):
        return md_text, False
    replacement = f"{start_marker}\n{content}\n{end_marker}"
    return pattern.sub(lambda _m: replacement, md_text, count=1), True


def main() -> int:
    if not DB_PATH.exists():
        print(f"  Base introuvable : {DB_PATH}")
        print("  Lancer d'abord : py 09_scripts/extraire_ess.py")
        return 1
    if not ANNEXE_C_MD.exists():
        print(f"  Fichier introuvable : {ANNEXE_C_MD}")
        return 1

    server_started = False
    if kaleido is not None:
        try:
            kaleido.start_sync_server(silence_warnings=True)
            server_started = True
        except Exception as exc:
            print(f"  [AVERT] Démarrage du serveur kaleido persistant impossible ({exc}) — poursuite en mode ponctuel.")

    print("  Lecture BDD…")
    regimes, prestations, regime_meta, prestation_meta = load_all(DB_PATH)
    indicateurs = build_indicateurs_payload(regimes, prestations)
    odd_nodes = build_odd_programmes_payload(regimes, prestations, regime_meta, prestation_meta)
    regime_rows = indicateurs.get("rows_regimes") or []
    prestation_rows = indicateurs.get("rows_prestations") or []
    years_available = {
        int(y) for y in (indicateurs.get("years_numerator") or indicateurs.get("years") or [])
        if isinstance(y, int) or (isinstance(y, float) and y.is_integer())
    }
    years = sorted(set(BULLETIN_YEARS) | years_available)

    settings = {}
    if SETTINGS_PATH.exists():
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    decisions = settings.get("oddDecisions") or {}
    denom_settings = settings.get("denomSettings") or {}
    denom_constructions = denom_settings.get("denominatorConstructions") or {}

    denom_conn = sqlite3.connect(DENOM_DB_PATH) if DENOM_DB_PATH.exists() else None
    denom_cursor = None
    if denom_conn is not None:
        try:
            test_cur = denom_conn.cursor()
            test_cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='denominateurs_ref' LIMIT 1"
            )
            if test_cur.fetchone():
                denom_cursor = test_cur
            else:
                test_cur.close()
        except sqlite3.Error:
            denom_cursor = None

    ILLUSTRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    md_text = ANNEXE_C_MD.read_text(encoding="utf-8-sig")
    total_updated = 0
    total_skipped = []

    try:
        for idx, item in enumerate(ODD_INDICATORS, start=1):
            indicator_key = item["key"]
            label = item["label"]
            print(f"  -> C.{idx} {indicator_key} ({label})")
            content = build_indicator_section(
                section_no=idx,
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
            md_text, updated = inject_into_markdown(md_text, indicator_key, content)
            if updated:
                total_updated += 1
            else:
                total_skipped.append(indicator_key)
    finally:
        if denom_conn is not None:
            denom_conn.close()

    ANNEXE_C_MD.write_text(md_text, encoding="utf-8-sig")

    if server_started:
        try:
            kaleido.stop_sync_server()
        except Exception:
            pass

    print(f"\n  {total_updated} section(s) mise(s) à jour dans {ANNEXE_C_MD.name}")
    if total_skipped:
        print(f"  {len(total_skipped)} indicateur(s) sans marqueur AUTO_GENERE (ignoré(s)) : {', '.join(total_skipped)}")
    return 0


if __name__ == "__main__":
    _exit_code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(_exit_code)
