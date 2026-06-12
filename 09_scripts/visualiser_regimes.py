"""
visualiser_regimes.py
Tableau de bord interactif — Protection sociale RDC
Structure : 3 onglets
  1. Indicateurs      — synthèse ESS (effectifs et finances agrégés)
  2. Par institution  — sélecteur CNSS / CNSSAP, puis régimes de l'institution
  3. Par prestation   — sélecteur institution → régime → liste des prestations

Usage :
  py 09_scripts/visualiser_regimes.py
  py 09_scripts/visualiser_regimes.py --out chemin/custom.html
"""

import argparse
import html
import json
import sqlite3
import sys
from pathlib import Path

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.io as pio
except ImportError:
    sys.exit("Plotly requis : py -m pip install plotly")

# ── Chemins ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "06_donnees" / "protection_sociale_rdc.db"
OUT_DIR  = BASE_DIR / "10_output"
OUT_DIR.mkdir(exist_ok=True)

# ── Constantes visuelles ──────────────────────────────────────────────────────
PALETTE_REGIME = {
    "CNSS_R1":   "#1f77b4",
    "CNSS_R2":   "#ff7f0e",
    "CNSS_R3":   "#2ca02c",
    "CNSS_R4":   "#9467bd",
    "CNSSAP_R1": "#d62728",
    "CNSSAP_R2": "#8c564b",
}
NOM_COURT = {
    "CNSS_R1":   "Prestations familiales",
    "CNSS_R2":   "Risques professionnels",
    "CNSS_R3":   "Pension",
    "CNSS_R4":   "Action sociale et sanitaire",
    "CNSSAP_R1": "Régime de base",
    "CNSSAP_R2": "Réforme du transfert",
}
NOM_INSTITUTION = {
    "CNSS":   "Caisse Nationale de Sécurité Sociale (CNSS)",
    "CNSSAP": "Caisse Nationale de Sécurité Sociale des Agents Publics (CNSSAP)",
}

CRITERIA_FIELDS = [
    {"key": "nom_regime", "label": "Nom du régime", "is_name_selector": True},
    {"key": "code_regime", "label": "Code régime", "is_multi": False},
    {"key": "type_financement", "label": "Type de financement", "is_multi": False},
    {"key": "caractere", "label": "Caractère", "is_multi": False},
    {"key": "type_assurance", "label": "Type d'assurance", "is_multi": False},
    {"key": "gestion", "label": "Gestion", "is_multi": False},
    {"key": "administrateur", "label": "Administrateur", "is_multi": False},
    {"key": "fonctions_oit", "label": "Fonctions couvertes", "is_multi": True, "is_list": True},
]


# ── Chargement données ────────────────────────────────────────────────────────
def load_all(db_path: Path) -> tuple[list[dict], list[dict], dict, dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    regimes = [dict(r) for r in conn.execute(
        "SELECT * FROM v_serie_temporelle_regimes ORDER BY institution, regime_code, annee"
    ).fetchall()]
    prestations = [dict(r) for r in conn.execute(
        "SELECT * FROM v_serie_temporelle_prestations ORDER BY institution, regime_code, nom_fr, annee"
    ).fetchall()]
    meta_rows = [dict(r) for r in conn.execute(
        """SELECT institution, regime_code, annee, nom_original, nom_fr, administrateur,
                  type_financement, caractere, type_assurance, gestion, fonctions_oit
           FROM regimes_historique
           ORDER BY institution, regime_code, annee ASC"""
    ).fetchall()]
    
    # Charger les métadonnées des prestations depuis prestations_historique
    prestation_meta_rows = [dict(r) for r in conn.execute(
        """SELECT institution, regime_code, nom_fr, annee,
                  fonction_oit, type_paiement, periodicite,
                  groupe_population, groupe_age, zone_geo,
                  type_financement, critere_eligibilite,
                  age_legal_h, age_legal_f, duree_service_requise
           FROM prestations_historique
           ORDER BY institution, regime_code, nom_fr, annee ASC"""
    ).fetchall()]
    
    conn.close()

    # Extraire les années ESS réelles depuis les données de séries temporelles
    ess_years_by_regime = {}
    for row in regimes:
        inst = row["institution"]
        rc = row["regime_code"]
        annee = row["annee"]
        key = (inst, rc)
        if key not in ess_years_by_regime:
            ess_years_by_regime[key] = []
        if annee is not None and annee not in ess_years_by_regime[key]:
            ess_years_by_regime[key].append(annee)
    
    # Trier les années
    for key in ess_years_by_regime:
        ess_years_by_regime[key].sort()

    # Extraire les années ESS par prestation
    ess_years_by_prestation = {}
    for row in prestations:
        inst = row["institution"]
        rc = row["regime_code"]
        prest_name = row["nom_fr"]
        annee = row["annee"]
        key = (inst, rc, prest_name)
        if key not in ess_years_by_prestation:
            ess_years_by_prestation[key] = []
        if annee is not None and annee not in ess_years_by_prestation[key]:
            ess_years_by_prestation[key].append(annee)
    
    # Trier les années prestations
    for key in ess_years_by_prestation:
        ess_years_by_prestation[key].sort()

    regime_meta = {}
    prestation_meta = {}
    for row in meta_rows:
        inst = row["institution"]
        rc = row["regime_code"]
        regime_meta.setdefault(inst, {})
        regime_meta[inst].setdefault(rc, [])

        fonctions = []
        raw_fonctions = row.get("fonctions_oit")
        if raw_fonctions:
            try:
                parsed = json.loads(raw_fonctions)
                if isinstance(parsed, list):
                    fonctions = [str(x) for x in parsed if x]
                elif isinstance(parsed, str):
                    fonctions = [parsed]
            except json.JSONDecodeError:
                fonctions = [str(raw_fonctions)]

        signature = json.dumps({
            "nom_original": row.get("nom_original"),
            "nom_regime": row.get("nom_fr") or row.get("nom_original") or NOM_COURT.get(rc, rc),
            "type_financement": row.get("type_financement"),
            "caractere": row.get("caractere"),
            "type_assurance": row.get("type_assurance"),
            "gestion": row.get("gestion"),
            "administrateur": row.get("administrateur"),
            "fonctions_oit": fonctions,
        }, ensure_ascii=False, sort_keys=True)

        regime_meta[inst][rc].append({
            "annee": row.get("annee"),
            "nom_original": row.get("nom_original"),
            "nom_regime": row.get("nom_fr") or row.get("nom_original") or NOM_COURT.get(rc, rc),
            "type_financement": row.get("type_financement"),
            "caractere": row.get("caractere"),
            "type_assurance": row.get("type_assurance"),
            "gestion": row.get("gestion"),
            "administrateur": row.get("administrateur"),
            "fonctions_oit": fonctions,
            "signature": signature,
        })

    for inst in regime_meta:
        for rc in regime_meta[inst]:
            versions = regime_meta[inst][rc]
            if not versions:
                continue

            selector_versions = []
            unique_sigs = []
            for item in versions:
                if item["signature"] not in unique_sigs:
                    unique_sigs.append(item["signature"])
            if len(unique_sigs) == 1:
                selector_versions = [versions[-1]]
            else:
                last_sig = None
                for item in versions:
                    if item["signature"] != last_sig:
                        selector_versions.append(item)
                        last_sig = item["signature"]

            variation_fields = []
            field_keys = ["nom_original", "nom_regime", "type_financement", "caractere", "type_assurance", "gestion", "administrateur", "fonctions_oit"]
            for key in field_keys:
                values = []
                for item in versions:
                    val = item[key]
                    if isinstance(val, list):
                        val = tuple(val)
                    values.append(json.dumps(val, ensure_ascii=False, sort_keys=True) if isinstance(val, (dict, list, tuple)) else str(val))
                if len(set(values)) > 1:
                    variation_fields.append(key)

            regime_meta[inst][rc] = {
                "versions": versions,
                "selector_versions": selector_versions,
                "reference_year": versions[0]["annee"],
                "latest_year": versions[-1]["annee"],
                "variation_fields": variation_fields,
                "ess_years": ess_years_by_regime.get((inst, rc), []),
            }

    # Construire prestation_meta avec versions par année (comme regime_meta)
    prestation_meta_raw = {}
    for row in prestation_meta_rows:
        inst = row["institution"]
        rc = row["regime_code"]
        prest_name = row["nom_fr"]
        annee = row["annee"]
        if not prest_name:
            continue
        
        key = (inst, rc, prest_name)
        if key not in prestation_meta_raw:
            prestation_meta_raw[key] = []
        
        prestation_meta_raw[key].append({
            "annee": annee,
            "nom_fr": prest_name,
            "fonction_oit": row.get("fonction_oit"),
            "type_paiement": row.get("type_paiement"),
            "periodicite": row.get("periodicite"),
            "groupe_population": row.get("groupe_population"),
            "groupe_age": row.get("groupe_age"),
            "zone_geo": row.get("zone_geo"),
            "type_financement": row.get("type_financement"),
            "critere_eligibilite": row.get("critere_eligibilite"),
            "age_legal_h": row.get("age_legal_h"),
            "age_legal_f": row.get("age_legal_f"),
            "duree_service_requise": row.get("duree_service_requise"),
        })
    
    # Créer le dictionnaire final avec sélecteur de versions
    for (inst, rc, prest_name), versions in prestation_meta_raw.items():
        prestation_meta.setdefault(inst, {})
        prestation_meta[inst].setdefault(rc, {})
        
        # Trier par année décroissante pour avoir la plus récente en premier
        versions.sort(key=lambda x: x["annee"] if x["annee"] else 0, reverse=True)
        
        # Identifier les champs qui varient
        field_keys = ["fonction_oit", "type_paiement", "periodicite", "groupe_population", 
                     "groupe_age", "zone_geo", "type_financement", "critere_eligibilite",
                     "age_legal_h", "age_legal_f", "duree_service_requise"]
        variation_fields = []
        for key in field_keys:
            values = set(str(v.get(key)) for v in versions)
            if len(values) > 1:
                variation_fields.append(key)
        
        # Créer les selector_versions (uniquement celles qui changent)
        selector_versions = []
        unique_sigs = []
        for item in versions:
            sig = json.dumps({k: item.get(k) for k in field_keys}, 
                           ensure_ascii=False, sort_keys=True)
            if sig not in unique_sigs:
                unique_sigs.append(sig)
                selector_versions.append(item)
        
        # Si toutes les versions sont identiques, ne garder que la plus récente
        if len(selector_versions) == 0:
            selector_versions = [versions[0]] if versions else []
        
        prestation_meta[inst][rc][prest_name] = {
            "versions": versions,
            "selector_versions": selector_versions,
            "reference_year": versions[0]["annee"] if versions else None,
            "latest_year": versions[0]["annee"] if versions else None,
            "variation_fields": variation_fields,
            "ess_years": ess_years_by_prestation.get((inst, rc, prest_name), []),
        }

    return regimes, prestations, regime_meta, prestation_meta


# ── Graphiques ────────────────────────────────────────────────────────────────
def fig_regime_single(rows: list[dict], institution: str, regime_code: str, sex_mode: str = "all") -> str:
    """Graphiques pour un régime spécifique (cotisants, bénéficiaires, finances).
    
    sex_mode = "all"    -> 6 graphiques agrégés
    sex_mode = "hommes" -> 2 graphiques sexués
    sex_mode = "femmes" -> 2 graphiques sexués
    """
    data = [r for r in rows if r["institution"] == institution and r["regime_code"] == regime_code]
    data.sort(key=lambda r: r["annee"])
    
    if not data:
        return "<p style='color:#888;padding:20px'>Aucune donnée de régime disponible.</p>"
    
    annees = [r["annee"] for r in data]
    color = PALETTE_REGIME.get(regime_code, "#2c5282")
    label = NOM_COURT.get(regime_code, regime_code)
    
    sex_mode = sex_mode if sex_mode in ("all", "hommes", "femmes") else "all"
    
    if sex_mode == "all":
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                "Cotisants actifs",
                "Bénéficiaires",
                "Dépenses totales (Mds CDF)",
                "Dépense moyenne par bénéficiaire (k CDF)",
                "Recettes totales (Mds CDF)",
                "Contribution moyenne (k CDF / cotisant)",
            ),
            vertical_spacing=0.11,
            horizontal_spacing=0.10,
        )
    else:
        sexe_cap = "Hommes" if sex_mode == "hommes" else "Femmes"
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                f"Cotisants {sexe_cap}",
                f"Bénéficiaires {sexe_cap}",
            ),
            horizontal_spacing=0.12,
        )
    
    def trace(y_vals, row, col, fmt, unit, trace_type="scatter"):
        if trace_type == "bar":
            fig.add_trace(go.Bar(
                x=annees, y=y_vals,
                name=label,
                showlegend=False,
                marker=dict(color=color, line=dict(width=0)),
                opacity=0.85,
                hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:{fmt}}} {unit}<extra></extra>",
            ), row=row, col=col)
            return
        fig.add_trace(go.Scatter(
            x=annees, y=y_vals,
            name=label,
            showlegend=False,
            mode="lines+markers",
            line=dict(color=color, width=3),
            marker=dict(size=9, line=dict(width=2, color='white')),
            hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:{fmt}}} {unit}<extra></extra>",
        ), row=row, col=col)
    
    if sex_mode == "all":
        trace([r["cotisants_total"] for r in data], 1, 1, ",.0f", "cotisants")
        trace([r["beneficiaires_total"] for r in data], 1, 2, ",.0f", "bénéf.")
        trace([
            (r["depenses_prestations_cdf"] / 1e9) if r["depenses_prestations_cdf"] is not None else None
            for r in data
        ], 2, 1, ".2f", "Mds CDF", trace_type="bar")
        dep_moy = [
            (r["depense_moy_par_beneficiaire_cdf"] / 1e3) if r["depense_moy_par_beneficiaire_cdf"] is not None else None
            for r in data
        ]
        trace(dep_moy, 2, 2, ",.1f", "k CDF")
        trace([
            (r["recettes_cdf"] / 1e9) if r["recettes_cdf"] is not None else None
            for r in data
        ], 3, 1, ".2f", "Mds CDF", trace_type="bar")
        contrib_moy = [
            (r["recettes_cdf"] / r["cotisants_total"] / 1e3)
            if r["recettes_cdf"] is not None and r["cotisants_total"] and r["cotisants_total"] > 0
            else None
            for r in data
        ]
        trace(contrib_moy, 3, 2, ",.1f", "k CDF")
    else:
        if sex_mode == "hommes":
            cotisants_vals = [r["cotisants_h"] for r in data]
            benef_vals = [r["beneficiaires_h"] for r in data]
        else:
            cotisants_vals = [r["cotisants_f"] for r in data]
            benef_vals = [r["beneficiaires_f"] for r in data]
        trace(cotisants_vals, 1, 1, ",.0f", "cotisants")
        trace(benef_vals, 1, 2, ",.0f", "bénéf.")
    
    title_text = NOM_INSTITUTION.get(institution, institution) + " — " + label
    if sex_mode != "all":
        title_text += " (" + ("Hommes" if sex_mode == "hommes" else "Femmes") + ")"
    
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(
                size=20,
                family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                color='#2c5282',
                weight=700
            ),
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        height=900 if sex_mode == "all" else 500,
        hovermode="x unified",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(t=80, b=60, l=60, r=40),
        showlegend=False,
        font=dict(
            family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            size=14,
            color='#4a5568'
        )
    )
    
    num_rows = 3 if sex_mode == "all" else 1
    num_cols = 2
    for r in range(1, num_rows + 1):
        for c in range(1, num_cols + 1):
            fig.update_xaxes(
                tickformat="d",
                dtick=1,
                row=r,
                col=c,
                showgrid=True,
                gridcolor='#f0f0f0',
                gridwidth=1,
                showline=True,
                linewidth=1,
                linecolor='#e2e8f0',
                tickfont=dict(size=12, color='#4a5568')
            )
            fig.update_yaxes(
                row=r,
                col=c,
                showgrid=True,
                gridcolor='#f0f0f0',
                gridwidth=1,
                showline=True,
                linewidth=1,
                linecolor='#e2e8f0',
                tickfont=dict(size=12, color='#4a5568')
            )
    
    for i, title in enumerate(fig.layout.annotations):
        title.font.update(
            size=14,
            family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            color='#2c5282',
            weight=600
        )
    
    return fig.to_html(full_html=False, include_plotlyjs=False)


def fig_institution(rows: list[dict], institution: str, sex_mode: str = "all") -> str:
    """Graphiques pour une institution.

    sex_mode = "all"    -> 6 graphiques agrégés
    sex_mode = "hommes" -> 2 graphiques sexués
    sex_mode = "femmes" -> 2 graphiques sexués
    """
    data = [r for r in rows if r["institution"] == institution]
    regimes_keys = sorted(set(r["regime_code"] for r in data))

    sex_mode = sex_mode if sex_mode in ("all", "hommes", "femmes") else "all"
    if sex_mode == "all":
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                "Cotisants actifs",
                "Bénéficiaires",
                "Dépenses totales (Mds CDF)",
                "Dépense moyenne par bénéficiaire (k CDF)",
                "Recettes totales (Mds CDF)",
                "Contribution moyenne (k CDF / cotisant)",
            ),
            vertical_spacing=0.11,
            horizontal_spacing=0.10,
        )
    else:
        sexe_cap = "Hommes" if sex_mode == "hommes" else "Femmes"
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                f"Cotisants {sexe_cap}",
                f"Bénéficiaires {sexe_cap}",
            ),
            horizontal_spacing=0.12,
        )

    for key in regimes_keys:
        subset = [r for r in data if r["regime_code"] == key]
        subset.sort(key=lambda r: r["annee"])
        annees  = [r["annee"] for r in subset]
        color   = PALETTE_REGIME.get(key, "#666")
        label   = NOM_COURT.get(key, key)

        def trace(y_vals, row, col, fmt, unit, showleg=False, trace_type="scatter"):
            if trace_type == "bar":
                fig.add_trace(go.Bar(
                    x=annees, y=y_vals,
                    name=label, legendgroup=key,
                    showlegend=showleg,
                    marker=dict(color=color, line=dict(width=0)),
                    opacity=0.85,
                    hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:{fmt}}} {unit}<extra></extra>",
                ), row=row, col=col)
                return
            if trace_type == "stack":
                fig.add_trace(go.Scatter(
                    x=annees, y=y_vals,
                    name=label, legendgroup=key,
                    showlegend=showleg,
                    mode="lines+markers",
                    stackgroup="g" + str(row) + str(col),
                    groupnorm="",
                    line=dict(color=color, width=2.8),
                    marker=dict(size=8, line=dict(width=1.5, color='white')),
                    hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:{fmt}}} {unit}<extra></extra>",
                ), row=row, col=col)
                return
            fig.add_trace(go.Scatter(
                x=annees, y=y_vals,
                name=label, legendgroup=key,
                showlegend=showleg,
                mode="lines+markers",
                line=dict(color=color, width=3),
                marker=dict(size=9, line=dict(width=2, color='white')),
                hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:{fmt}}} {unit}<extra></extra>",
            ), row=row, col=col)

        if sex_mode == "all":
            trace([r["cotisants_total"] for r in subset],                     1, 1, ",.0f", "cotisants", showleg=True, trace_type="stack")
            trace([r["beneficiaires_total"] for r in subset],                  1, 2, ",.0f", "bénéf.", trace_type="stack")
            trace([
                (r["depenses_prestations_cdf"] / 1e9) if r["depenses_prestations_cdf"] is not None else None
                for r in subset
            ],                                                                  2, 1, ".2f", "Mds CDF", trace_type="bar")
            dep_moy = [
                (r["depense_moy_par_beneficiaire_cdf"] / 1e3) if r["depense_moy_par_beneficiaire_cdf"] is not None else None
                for r in subset
            ]
            trace(dep_moy,                                                      2, 2, ",.0f", "k CDF")
            trace([
                (r["recettes_cdf"] / 1e9) if r["recettes_cdf"] is not None else None
                for r in subset
            ],                                                                  3, 1, ".2f", "Mds CDF", trace_type="bar")
            contrib_moy = [
                ((r["recettes_cdf"] / r["cotisants_total"]) / 1e3)
                if (r["recettes_cdf"] is not None and r["cotisants_total"] not in (None, 0))
                else None
                for r in subset
            ]
            trace(contrib_moy,                                                  3, 2, ",.0f", "k CDF")
        else:
            sex_suffix = "h" if sex_mode == "hommes" else "f"
            trace([r["cotisants_" + sex_suffix] for r in subset],               1, 1, ",.0f", "cotisants", showleg=True, trace_type="stack")
            trace([r["beneficiaires_" + sex_suffix] for r in subset],            1, 2, ",.0f", "bénéf.", trace_type="stack")

    fig.update_layout(
        title=dict(
            text=NOM_INSTITUTION.get(institution, institution) + (
                "" if sex_mode == "all" else " — " + ("Hommes" if sex_mode == "hommes" else "Femmes")
            ),
            font=dict(
                size=20, 
                family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                color='#2c5282',
                weight=700
            ), 
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        height=920 if sex_mode == "all" else 520,
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=-0.22 if sex_mode == "all" else -0.24,
            xanchor="center", 
            x=0.5, 
            font=dict(
                size=12,
                family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                color='#4a5568'
            ),
            bgcolor='rgba(247, 250, 252, 0.8)',
            bordercolor='#e2e8f0',
            borderwidth=1
        ),
        hovermode="x unified",
        barmode="relative",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(t=80, b=120 if sex_mode == "all" else 100, l=70, r=40),
        font=dict(
            family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            size=13,
            color='#4a5568'
        ),
    )
    
    # Style des titres de sous-graphiques
    fig.update_annotations(
        font=dict(
            size=14,
            family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            color='#2c5282',
            weight=600
        )
    )
    
    if sex_mode == "all":
        for c in [1, 2]:
            for rr in [1, 2, 3]:
                fig.update_xaxes(
                    tickformat="d", 
                    dtick=1, 
                    row=rr, 
                    col=c,
                    showgrid=True,
                    gridcolor='#f0f0f0',
                    gridwidth=1,
                    showline=True,
                    linewidth=1,
                    linecolor='#e2e8f0',
                    tickfont=dict(size=12, color='#4a5568')
                )
                fig.update_yaxes(
                    row=rr,
                    col=c,
                    showgrid=True,
                    gridcolor='#f0f0f0',
                    gridwidth=1,
                    showline=True,
                    linewidth=1,
                    linecolor='#e2e8f0',
                    tickfont=dict(size=12, color='#4a5568'),
                    separatethousands=True
                )
    else:
        for c in [1, 2]:
            fig.update_xaxes(
                tickformat="d", 
                dtick=1, 
                row=1, 
                col=c,
                showgrid=True,
                gridcolor='#f0f0f0',
                gridwidth=1,
                showline=True,
                linewidth=1,
                linecolor='#e2e8f0',
                tickfont=dict(size=12, color='#4a5568')
            )
            fig.update_yaxes(
                row=1,
                col=c,
                showgrid=True,
                gridcolor='#f0f0f0',
                gridwidth=1,
                showline=True,
                linewidth=1,
                linecolor='#e2e8f0',
                tickfont=dict(size=12, color='#4a5568'),
                separatethousands=True
            )

    return fig.to_html(full_html=False, include_plotlyjs=False)


def fig_prestation(rows: list[dict], institution: str, regime_code: str) -> str:
    """Graphique bénéficiaires + montant unitaire pour toutes les prestations d'un régime."""
    data = [r for r in rows
            if r["institution"] == institution and r["regime_code"] == regime_code]
    prestations_list = sorted(set(r["nom_fr"] for r in data if r["nom_fr"]))
    if not prestations_list:
        return "<p style='color:#888;padding:20px'>Aucune donnée de prestation disponible.</p>"

    annees_all = sorted(set(r["annee"] for r in data))
    n = len(prestations_list)

    # Palette de couleurs pour les prestations
    palette = [
        "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
        "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf",
        "#aec7e8","#ffbb78","#98df8a",
    ]

    # 2 sous-graphiques : bénéficiaires | montant unitaire
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Bénéficiaires par prestation", "Montant unitaire (CDF)"),
        horizontal_spacing=0.12,
    )

    for i, prest in enumerate(prestations_list):
        color = palette[i % len(palette)]
        subset = {r["annee"]: r for r in data if r["nom_fr"] == prest}
        y_benef  = [subset.get(a, {}).get("beneficiaires_total") for a in annees_all]
        y_montant= [subset.get(a, {}).get("montant_unitaire_cdf") for a in annees_all]

        common = dict(
            x=annees_all, name=prest, legendgroup=prest,
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=7),
        )
        fig.add_trace(go.Scatter(
            **common, y=y_benef, showlegend=True,
            hovertemplate=f"%{{x}} — {prest}<br>%{{y:,.0f}} bénéf.<extra></extra>",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            **common, y=y_montant, showlegend=False,
            hovertemplate=f"%{{x}} — {prest}<br>%{{y:,.0f}} CDF<extra></extra>",
        ), row=1, col=2)

    label_regime = NOM_COURT.get(regime_code, regime_code)
    fig.update_layout(
        title=dict(
            text=f"{NOM_INSTITUTION.get(institution, institution)} — {label_regime}",
            font=dict(size=14), x=0.5
        ),
        height=500,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.38,
            xanchor="center", x=0.5, font=dict(size=10),
        ),
        hovermode="x unified",
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
        margin=dict(t=60, b=160, l=55, r=30),
    )
    for c in [1, 2]:
        fig.update_xaxes(tickformat="d", dtick=1, row=1, col=c)

    return fig.to_html(full_html=False, include_plotlyjs=False)


def fig_prestations_by_institution(rows: list[dict], institution: str, regime_code: str, sex_mode: str = "all") -> str:
    """Graphiques pour toutes les prestations d'un régime d'une institution avec toggle sexe."""
    data = [r for r in rows if r["institution"] == institution and r["regime_code"] == regime_code]
    sex_mode = sex_mode if sex_mode in ("all", "hommes", "femmes") else "all"
    
    if not data:
        return "<p style='color:#888;padding:20px'>Aucune donnée de prestation disponible.</p>"
    
    prestations_list = sorted(set(r["nom_fr"] for r in data if r["nom_fr"]))
    if not prestations_list:
        return "<p style='color:#888;padding:20px'>Aucune prestation trouvée.</p>"
    
    # Palette de couleurs
    palette = [
        "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
        "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf",
    ]
    
    if sex_mode == "all":
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Bénéficiaires totaux", "Montant unitaire (CDF)"),
            horizontal_spacing=0.12,
        )
    else:
        sexe_cap = "Hommes" if sex_mode == "hommes" else "Femmes"
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(f"Bénéficiaires {sexe_cap}", f"Montant unitaire (CDF)"),
            horizontal_spacing=0.12,
        )
    
    for i, prest in enumerate(prestations_list):
        color = palette[i % len(palette)]
        subset = [r for r in data if r["nom_fr"] == prest]
        subset.sort(key=lambda r: r["annee"])
        annees = [r["annee"] for r in subset]
        
        if sex_mode == "all":
            y_benef = [r["beneficiaires_total"] for r in subset]
        elif sex_mode == "hommes":
            y_benef = [r["beneficiaires_h"] for r in subset]
        else:
            y_benef = [r["beneficiaires_f"] for r in subset]
        
        y_montant = [r["montant_unitaire_cdf"] for r in subset]
        
        common = dict(
            x=annees, name=prest, legendgroup=prest,
            mode="lines+markers",
            line=dict(color=color, width=2.8),
            marker=dict(size=8, line=dict(width=1.5, color='white')),
        )
        fig.add_trace(go.Scatter(
            **common, y=y_benef, showlegend=True,
            hovertemplate=f"<b>{prest}</b><br>%{{x}}<br>%{{y:,.0f}} bénéf.<extra></extra>",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            **common, y=y_montant, showlegend=False,
            hovertemplate=f"<b>{prest}</b><br>%{{x}}<br>%{{y:,.0f}} CDF<extra></extra>",
        ), row=1, col=2)
    
    title_text = NOM_INSTITUTION.get(institution, institution)
    if sex_mode != "all":
        title_text += " — " + ("Hommes" if sex_mode == "hommes" else "Femmes")
    
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(
                size=20,
                family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                color='#2c5282',
                weight=700
            ),
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.30,
            xanchor="center",
            x=0.5,
            font=dict(
                size=12,
                family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                color='#4a5568'
            ),
            bgcolor='rgba(247, 250, 252, 0.8)',
            bordercolor='#e2e8f0',
            borderwidth=1
        ),
        hovermode="x unified",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(t=80, b=140, l=70, r=40),
        font=dict(
            family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            size=13,
            color='#4a5568'
        ),
    )
    
    fig.update_annotations(
        font=dict(
            size=14,
            family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            color='#2c5282',
            weight=600
        )
    )
    
    for c in [1, 2]:
        fig.update_xaxes(
            tickformat="d",
            dtick=1,
            row=1,
            col=c,
            showgrid=True,
            gridcolor='#f0f0f0',
            gridwidth=1,
            showline=True,
            linewidth=1,
            linecolor='#e2e8f0',
            tickfont=dict(size=12, color='#4a5568')
        )
        fig.update_yaxes(
            row=1,
            col=c,
            showgrid=True,
            gridcolor='#f0f0f0',
            gridwidth=1,
            showline=True,
            linewidth=1,
            linecolor='#e2e8f0',
            tickfont=dict(size=12, color='#4a5568'),
            separatethousands=True
        )
    
    return fig.to_html(full_html=False, include_plotlyjs=False)


def fig_table_prestations(rows: list[dict], institution: str, regime_code: str, sex_mode: str = "all") -> str:
    """Tableau récapitulatif des prestations pour un régime."""
    data = [r for r in rows if r["institution"] == institution and r["regime_code"] == regime_code]
    sex_mode = sex_mode if sex_mode in ("all", "hommes", "femmes") else "all"
    
    if not data:
        return "<p style='color:#888;padding:10px'>Aucune donnée disponible.</p>"
    
    if sex_mode == "all":
        headers = [
            "Régime", "Prestation", "Année",
            "Bénéficiaires totaux",
            "Montant unitaire (CDF)",
            "Type de paiement", "Périodicité",
        ]
    else:
        sexe_cap = "Hommes" if sex_mode == "hommes" else "Femmes"
        headers = [
            "Régime", "Prestation", "Année",
            f"Bénéficiaires {sexe_cap}",
            "Montant unitaire (CDF)",
            "Type de paiement", "Périodicité",
        ]
    
    body_rows = []
    for r in data:
        regime_name = NOM_COURT.get(r["regime_code"], r["regime_code"])
        
        if sex_mode == "all":
            benef = _fmt_num(r["beneficiaires_total"])
        elif sex_mode == "hommes":
            benef = _fmt_num(r["beneficiaires_h"])
        else:
            benef = _fmt_num(r["beneficiaires_f"])
        
        row_data = [
            regime_name,
            r["nom_fr"] or "—",
            str(r["annee"]) if r["annee"] else "—",
            benef,
            _fmt_num(r["montant_unitaire_cdf"]),
            r["type_paiement"] or "—",
            r["periodicite"] or "—",
        ]
        body_rows.append(row_data)
    
    # Build table with filter-enabled structure
    thead_html = "<tr>"
    for h in headers:
        thead_html += f'<th><div class="th-content">{h}<span class="filter-icon">▼</span></div></th>'
    thead_html += "</tr>"
    
    rows_html = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row in body_rows
    )
    
    return f"""
<table class="data-table filterable-table">
  <thead>{thead_html}</thead>
  <tbody>{rows_html}</tbody>
</table>
"""


# ── Tableau récapitulatif ─────────────────────────────────────────────────────
def _fmt_num(val, digits: int = 0, scale: float = 1.0) -> str:
    if val is None:
        return "—"
    try:
        num = float(val) / scale
    except (TypeError, ValueError):
        return "—"
    if digits == 0:
        return f"{num:,.0f}"
    return f"{num:,.{digits}f}"


def fig_table_regime(rows: list[dict], institution: str, sex_mode: str = "all") -> str:
    data = [r for r in rows if r["institution"] == institution]
    sex_mode = sex_mode if sex_mode in ("all", "hommes", "femmes") else "all"

    if not data:
        return "<p style='color:#888;padding:10px'>Aucune donnée détaillée disponible.</p>"

    if sex_mode == "all":
        headers = [
            "Régime", "Année",
            "Cotisants totaux",
            "Bénéficiaires totaux",
            "Dépenses totales (Mds CDF)", "Recettes totales (Mds CDF)",
            "Dép. moy./bénéf. (k CDF)", "Rec. moy./cotisant (k CDF)",
        ]
    else:
        sexe_cap = "Hommes" if sex_mode == "hommes" else "Femmes"
        headers = [
            "Régime", "Année",
            f"Cotisants {sexe_cap}",
            f"Bénéficiaires {sexe_cap}",
        ]

    body_rows = []
    for r in data:
        if sex_mode == "all":
            rec_moy = None
            if r["recettes_cdf"] is not None and r["cotisants_total"] not in (None, 0):
                try:
                    rec_moy = float(r["recettes_cdf"]) / float(r["cotisants_total"])
                except (TypeError, ValueError, ZeroDivisionError):
                    rec_moy = None
            values = [
                NOM_COURT.get(r["regime_code"], r["regime_code"]),
                str(r["annee"]),
                _fmt_num(r["cotisants_total"]),
                _fmt_num(r["beneficiaires_total"]),
                _fmt_num(r["depenses_prestations_cdf"], 2, 1e9),
                _fmt_num(r["recettes_cdf"], 2, 1e9),
                _fmt_num(r["depense_moy_par_beneficiaire_cdf"], 0, 1e3),
                _fmt_num(rec_moy, 0, 1e3),
            ]
        else:
            sex_suffix = "h" if sex_mode == "hommes" else "f"
            values = [
                NOM_COURT.get(r["regime_code"], r["regime_code"]),
                str(r["annee"]),
                _fmt_num(r[f"cotisants_{sex_suffix}"]),
                _fmt_num(r[f"beneficiaires_{sex_suffix}"]),
            ]

        cells = "".join(f"<td>{html.escape(v)}</td>" for v in values)
        body_rows.append(f"<tr>{cells}</tr>")

    headers_html = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    filters_html = "".join(
        "<th><input class=\"col-filter\" type=\"text\" placeholder=\"Filtrer...\" aria-label=\"Filtrer la colonne\"></th>"
        for _ in headers
    )
    body_html = "".join(body_rows)
    return (
        "<div class=\"table-wrap\">"
        "<table class=\"filterable-table\">"
        f"<thead><tr>{headers_html}</tr><tr class=\"filter-row\">{filters_html}</tr></thead>"
        f"<tbody>{body_html}</tbody>"
        "</table>"
        "</div>"
    )


def build_indicateurs_payload(rows: list[dict]) -> dict:
    by_year = {}
    by_inst_year = {}

    def add_value(container: dict, key: str, val):
        if val is None:
            return
        try:
            container[key] += float(val)
        except (TypeError, ValueError):
            return

    for r in rows:
        year = r.get("annee")
        inst = r.get("institution")
        if year is None or not inst:
            continue

        by_year.setdefault(year, {
            "cotisants": 0.0,
            "beneficiaires": 0.0,
            "depenses_cdf": 0.0,
            "recettes_cdf": 0.0,
        })
        by_inst_year.setdefault(inst, {})
        by_inst_year[inst].setdefault(year, {
            "cotisants": 0.0,
            "beneficiaires": 0.0,
            "depenses_cdf": 0.0,
            "recettes_cdf": 0.0,
        })

        add_value(by_year[year], "cotisants", r.get("cotisants_total"))
        add_value(by_year[year], "beneficiaires", r.get("beneficiaires_total"))
        add_value(by_year[year], "depenses_cdf", r.get("depenses_prestations_cdf"))
        add_value(by_year[year], "recettes_cdf", r.get("recettes_cdf"))

        add_value(by_inst_year[inst][year], "cotisants", r.get("cotisants_total"))
        add_value(by_inst_year[inst][year], "beneficiaires", r.get("beneficiaires_total"))
        add_value(by_inst_year[inst][year], "depenses_cdf", r.get("depenses_prestations_cdf"))
        add_value(by_inst_year[inst][year], "recettes_cdf", r.get("recettes_cdf"))

    years = sorted(by_year.keys())
    if not years:
        return {
            "years": [],
            "totaux": {
                "cotisants": [],
                "beneficiaires": [],
                "depenses_mds": [],
                "recettes_mds": [],
            },
            "latest": None,
            "institutions_latest": [],
        }

    totaux = {
        "cotisants": [by_year[y]["cotisants"] for y in years],
        "beneficiaires": [by_year[y]["beneficiaires"] for y in years],
        "depenses_mds": [by_year[y]["depenses_cdf"] / 1e9 for y in years],
        "recettes_mds": [by_year[y]["recettes_cdf"] / 1e9 for y in years],
    }

    latest_year = years[-1]
    latest = by_year[latest_year]
    ratio_benef_cotis = (
        latest["beneficiaires"] / latest["cotisants"]
        if latest["cotisants"] > 0 else None
    )
    ratio_dep_rec = (
        latest["depenses_cdf"] / latest["recettes_cdf"]
        if latest["recettes_cdf"] > 0 else None
    )

    institutions_latest = []
    for inst in sorted(by_inst_year.keys()):
        if latest_year not in by_inst_year[inst]:
            continue
        vals = by_inst_year[inst][latest_year]
        institutions_latest.append({
            "institution": inst,
            "cotisants": vals["cotisants"],
            "beneficiaires": vals["beneficiaires"],
            "depenses_mds": vals["depenses_cdf"] / 1e9,
            "recettes_mds": vals["recettes_cdf"] / 1e9,
        })

    return {
        "years": years,
        "totaux": totaux,
        "latest": {
            "annee": latest_year,
            "cotisants": latest["cotisants"],
            "beneficiaires": latest["beneficiaires"],
            "depenses_mds": latest["depenses_cdf"] / 1e9,
            "recettes_mds": latest["recettes_cdf"] / 1e9,
            "ratio_benef_cotis": ratio_benef_cotis,
            "ratio_dep_rec": ratio_dep_rec,
        },
        "institutions_latest": institutions_latest,
    }


# ── Assemblage HTML final ─────────────────────────────────────────────────────
def build_html(regimes: list[dict], prestations: list[dict], regime_meta: dict, prestation_meta: dict) -> str:
    institutions = sorted(set(r["institution"] for r in regimes))

    # Pré-générer tous les blocs graphiques (évite le recalcul JS)
    charts_institution = {}
    tables_institution = {}
    charts_prestations = {}
    tables_prestations = {}

    for inst in institutions:
        charts_institution[inst] = {
            "all": fig_institution(regimes, inst, "all"),
            "hommes": fig_institution(regimes, inst, "hommes"),
            "femmes": fig_institution(regimes, inst, "femmes"),
        }
        tables_institution[inst] = {
            "all": fig_table_regime(regimes, inst, "all"),
            "hommes": fig_table_regime(regimes, inst, "hommes"),
            "femmes": fig_table_regime(regimes, inst, "femmes"),
        }
        
        # Graphiques et tableaux par prestation pour chaque institution et régime
        regimes_for_prest = sorted(set(r["regime_code"] for r in prestations if r["institution"] == inst))
        charts_prestations[inst] = {}
        tables_prestations[inst] = {}
        charts_regime_prest = {}  # Graphiques du régime (cotisants, finances)
        
        for rc in regimes_for_prest:
            # Graphiques du régime (cotisants, bénéficiaires, finances)
            charts_regime_prest[rc] = {
                "all": fig_regime_single(regimes, inst, rc, "all"),
                "hommes": fig_regime_single(regimes, inst, rc, "hommes"),
                "femmes": fig_regime_single(regimes, inst, rc, "femmes"),
            }
            
            # Graphiques des prestations détaillées
            charts_prestations[inst][rc] = {
                "all": fig_prestations_by_institution(prestations, inst, rc, "all"),
                "hommes": fig_prestations_by_institution(prestations, inst, rc, "hommes"),
                "femmes": fig_prestations_by_institution(prestations, inst, rc, "femmes"),
            }
            tables_prestations[inst][rc] = {
                "all": fig_table_prestations(prestations, inst, rc, "all"),
                "hommes": fig_table_prestations(prestations, inst, rc, "hommes"),
                "femmes": fig_table_prestations(prestations, inst, rc, "femmes"),
            }
        
        # Stocker les graphiques de régime par institution
        charts_prestations[inst]["_regime"] = charts_regime_prest

    # Sérialiser pour JS inline sans fermer accidentellement la balise <script>.
    # Le parseur HTML (mode raw text) ferme le script dès qu'il voit la séquence
    # littérale </script, même précédée d'un backslash (<\/script).
    # Remplacer </ par \u003c/ (escape JSON/JS pour <) rend la séquence opaque
    # au parseur HTML tout en étant correctement décodée par le moteur JS.
    def js_safe_json(data) -> str:
        return json.dumps(data).replace("</", "\\u003c/")

    charts_inst_json  = js_safe_json(charts_institution)
    tables_inst_json  = js_safe_json(tables_institution)
    charts_prest_json = js_safe_json(charts_prestations)
    tables_prest_json = js_safe_json(tables_prestations)
    regime_meta_json  = js_safe_json(regime_meta)
    prestation_meta_json = js_safe_json(prestation_meta)
    criteres_json     = js_safe_json(CRITERIA_FIELDS)
    indicateurs_json  = js_safe_json(build_indicateurs_payload(regimes))
    denominateurs_json = js_safe_json({
        "sources": {
            "bm_api": {
                "label": "Banque mondiale (live)",
                "description": "Population totale, 15-64, 65+, taux natalité — séries SP.POP.* depuis 1960",
            },
        "wpp_api": {
                "label": "ONU WPP via PopPyramid (live)",
                "description": "Pyramide des âges quinquennale RDC — données ONU WPP 2024, toutes tranches d'âge personnalisables, 1950–2100",
            },
            "ilostat_api": {
                "label": "ILOSTAT / OIT (live)",
                "description": "Population active employée — séries emploi OIT pour la RDC",
            },
        },
        "defaults": {
            "source_population_totale": "bm_api",
            "source_population_active": "wpp_api",
            "source_population_retraite": "wpp_api",
            "source_maternite": "bm_api",
            "year_start_total": min(build_indicateurs_payload(regimes).get("years", [2020])),
            "year_end_total": max(build_indicateurs_payload(regimes).get("years", [2024])),
            "year_start_active": min(build_indicateurs_payload(regimes).get("years", [2020])),
            "year_end_active": max(build_indicateurs_payload(regimes).get("years", [2024])),
            "year_start_retraite": min(build_indicateurs_payload(regimes).get("years", [2020])),
            "year_end_retraite": max(build_indicateurs_payload(regimes).get("years", [2024])),
            "year_start_maternite": min(build_indicateurs_payload(regimes).get("years", [2020])),
            "year_end_maternite": max(build_indicateurs_payload(regimes).get("years", [2024])),
            "retirement_age_h": 65,
            "retirement_age_f": 65,
            "working_age_min": 15,
            "working_age_max": 64,
            "maternity_age_min": 15,
            "maternity_age_max": 49,
        },
    })

    # Listes pour les sélecteurs
    inst_options = "".join(
        f'<option value="{i}">{i}</option>' for i in institutions
    )
    # Options régimes par institution (pour onglet prestations)
    regimes_par_inst = {}
    for inst in institutions:
        regimes_par_inst[inst] = sorted(set(
            r["regime_code"] for r in regimes if r["institution"] == inst
        ))
    regimes_par_inst_json = js_safe_json(regimes_par_inst)
    nom_court_json = js_safe_json(NOM_COURT)

    import plotly.offline as plo
    plotlyjs = f'<script>{plo.get_plotlyjs()}</script>'

    note_sources = """
    <p class="note-source">
      <strong>Source :</strong> Enquête sur la Sécurité Sociale (ESS) OIT/BIT —
      CNSS 2019–2022, CNSSAP 2020–2022.<br>
      Les montants CNSSAP sont convertis depuis les Milliards CDF de l'ESS.
      Les bénéficiaires sans cotisants signifient que la variable n'était pas renseignée dans l'ESS.<br>
      La contribution moyenne est un indicateur dérivé (recettes / cotisants), car elle n'est pas renseignée directement dans l'ESS.
    </p>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tableau de bord — Protection sociale RDC</title>
  {plotlyjs}
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body    {{ 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif; 
      margin: 0; 
      background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%); 
      color: #2d3748; 
      line-height: 1.6;
      font-size: 15px;
    }}
    header  {{ 
      background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); 
      color: #fff; 
      padding: 24px 40px; 
      box-shadow: 0 4px 12px rgba(0,0,0,0.12);
      position: relative;
    }}
    header h1 {{ 
      margin: 0; 
      font-size: 1.75rem; 
      font-weight: 700; 
      letter-spacing: -0.02em;
    }}
    header p  {{ 
      margin: 8px 0 0; 
      font-size: 0.95rem; 
      opacity: 0.9; 
      font-weight: 400;
    }}

    /* Onglets */
    .tab-bar  {{ 
      display: flex; 
      background: #fff; 
      border-bottom: 2px solid #e2e8f0;
      padding: 0 32px; 
      gap: 8px; 
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .tab-btn  {{ 
      padding: 16px 28px; 
      cursor: pointer; 
      border: none; 
      background: none;
      font-size: 1rem; 
      font-weight: 600; 
      color: #718096; 
      border-bottom: 3px solid transparent;
      margin-bottom: -2px; 
      transition: all 0.2s ease;
    }}
    .tab-btn:hover   {{ color: #2c5282; background: #f7fafc; }}
    .tab-btn.active  {{ color: #2c5282; border-bottom-color: #2c5282; }}
    .tab-panel {{ display: none; padding: 32px 40px; max-width: 1800px; margin: 0 auto; }}
    .tab-panel.active {{ display: block; }}

    .indicator-kpis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }}
    .indicator-kpis-numerateurs {{
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      margin-bottom: 0;
    }}
    .kpi-card {{
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 16px 18px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    .kpi-card-numerateur {{
      border-color: #2c5282;
      border-width: 2px;
      background: linear-gradient(135deg, #ebf4ff 0%, #ffffff 100%);
      box-shadow: 0 4px 12px rgba(44,82,130,0.12);
    }}
    .kpi-label {{
      color: #4a5568;
      font-size: 0.9rem;
      font-weight: 600;
      margin-bottom: 4px;
    }}
    .kpi-value {{
      color: #1a365d;
      font-size: 1.45rem;
      font-weight: 700;
      line-height: 1.25;
    }}
    .kpi-icon {{
      font-size: 1.6rem;
      margin-bottom: 6px;
    }}
    .kpi-sublabel {{
      color: #718096;
      font-size: 0.78rem;
      font-style: italic;
      margin-top: 4px;
    }}
    .numerateurs-title {{
      color: #2c5282;
      font-size: 1rem;
      font-weight: 700;
      margin: 12px 0 10px 0;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      border-left: 4px solid #2c5282;
      padding-left: 10px;
    }}
    .calc-details {{
      margin-top: 18px;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      overflow: hidden;
    }}
    .calc-details > summary {{
      cursor: pointer;
      padding: 11px 16px;
      background: #f7fafc;
      font-weight: 600;
      font-size: 0.92rem;
      color: #2d3748;
      user-select: none;
      list-style: none;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .calc-details > summary::before {{
      content: '▶';
      font-size: 0.75rem;
      transition: transform 0.2s;
    }}
    .calc-details[open] > summary::before {{
      transform: rotate(90deg);
    }}
    .calc-details > summary::-webkit-details-marker {{ display: none; }}
    .calc-details > :not(summary) {{
      padding: 16px;
    }}
    .indicator-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .denom-panel {{
      margin-top: 18px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #ffffff;
      padding: 14px 16px;
    }}
    .denom-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }}
    .denom-card {{
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 12px;
      background: #f8fafc;
    }}
    .denom-card .label {{
      color: #4a5568;
      font-size: 0.88rem;
      font-weight: 600;
      margin-bottom: 3px;
    }}
    .denom-card .value {{
      color: #1a365d;
      font-size: 1.2rem;
      font-weight: 700;
      line-height: 1.25;
    }}
    .denom-card .meta {{
      color: #718096;
      font-size: 0.8rem;
      margin-top: 4px;
    }}
    .denom-packs {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
      margin-top: 10px;
    }}
    .denom-pack {{
      border: 1px solid #dbe4f0;
      border-radius: 10px;
      background: #f8fafc;
      padding: 10px 12px;
    }}
    .denom-pack h4 {{
      margin: 0 0 8px;
      color: #1a365d;
      font-size: 0.95rem;
    }}
    .denom-pack-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px 10px;
    }}
    .denom-pack-grid .full {{
      grid-column: 1 / -1;
    }}
    .denom-control label {{
      display: block;
      font-size: 0.82rem;
      color: #4a5568;
      font-weight: 600;
      margin-bottom: 4px;
    }}
    .denom-control input,
    .denom-control select {{
      width: 100%;
      padding: 8px 10px;
      border: 1px solid #cbd5e0;
      border-radius: 8px;
      background: #fff;
      color: #2d3748;
    }}
    .denom-source-list {{
      display: grid;
      gap: 5px;
    }}
    /* Surcharge : les labels et inputs dans la source-list ne doivent PAS
       hériter des styles de .denom-control label / .denom-control input */
    .denom-source-list label.denom-source-item {{
      display: flex !important;
      align-items: center;
      gap: 8px;
      font-size: 0.84rem;
      font-weight: 500;
      color: #2d3748;
      cursor: pointer;
      margin-bottom: 0;
      padding: 4px 6px;
      border-radius: 6px;
      transition: background 0.15s;
    }}
    .denom-source-list label.denom-source-item:hover:not(.disabled) {{
      background: #edf2f7;
    }}
    .denom-source-list label.denom-source-item.disabled {{
      color: #a0aec0;
      cursor: not-allowed;
      opacity: 0.6;
    }}
    .denom-source-list input[type="radio"] {{
      width: auto !important;
      padding: 0 !important;
      border: none !important;
      background: none !important;
      border-radius: 0 !important;
      flex-shrink: 0;
      cursor: pointer;
      accent-color: #2c5282;
    }}
    .denom-params-separator {{
      border-top: 1px solid #dbe4f0;
      margin-top: 4px;
      padding-top: 6px;
    }}
    .denom-params-separator span {{
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #718096;
    }}
    .denom-control input.constrained {{
      background: #edf2f7;
      color: #718096;
      border-color: #e2e8f0;
      cursor: not-allowed;
    }}
    .denom-source-item {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.84rem;
      color: #2d3748;
    }}
    .denom-source-item.disabled {{
      color: #a0aec0;
    }}
    .denom-actions {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-top: 10px;
      flex-wrap: wrap;
    }}
    .denom-actions button {{
      border: none;
      border-radius: 8px;
      background: #2c5282;
      color: #fff;
      font-weight: 600;
      padding: 8px 14px;
      cursor: pointer;
    }}
    .denom-status {{
      color: #4a5568;
      font-size: 0.84rem;
    }}
    .denom-table-wrap {{
      margin-top: 12px;
      overflow-x: auto;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #fff;
    }}
    .denom-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      min-width: 980px;
    }}
    .denom-table th,
    .denom-table td {{
      border: 1px solid #e2e8f0;
      padding: 9px 10px;
      text-align: left;
      vertical-align: top;
    }}
    .denom-table th {{
      background: #edf2f7;
      color: #2d3748;
      font-weight: 700;
    }}
    .denom-table td small {{
      color: #718096;
      display: block;
      margin-top: 2px;
      font-size: 0.78rem;
    }}
    @media (max-width: 1100px) {{
      .indicator-grid {{ grid-template-columns: 1fr; }}
    }}

    /* Sélecteurs */
    .selector-bar {{ 
      display: flex; 
      align-items: center; 
      gap: 20px;
      background: #fff; 
      border-radius: 12px; 
      padding: 18px 24px;
      margin-bottom: 24px; 
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      border: 1px solid #e2e8f0;
    }}
    .selector-bar label {{ 
      font-weight: 600; 
      font-size: 0.95rem; 
      color: #2c5282; 
      white-space: nowrap; 
    }}
    .selector-bar select {{ 
      padding: 10px 16px; 
      border: 1px solid #cbd5e0; 
      border-radius: 8px;
      font-size: 0.95rem; 
      background: #f7fafc; 
      cursor: pointer;
      transition: all 0.2s ease;
      min-width: 200px;
    }}
    .selector-bar select:hover {{ 
      border-color: #2c5282; 
      background: #fff; 
    }}
    .selector-bar select:focus {{ 
      outline: none; 
      border-color: #2c5282; 
      box-shadow: 0 0 0 3px rgba(44,82,130,0.1);
    }}
    .selector-stack {{ align-items: flex-start; }}
    .table-mode-toggle {{
      display: inline-flex;
      gap: 8px;
      flex-wrap: wrap;
      background: #f7fafc;
      padding: 4px;
      border-radius: 999px;
      border: 1px solid #e2e8f0;
    }}
    .table-mode-btn {{
      border: none;
      background: transparent;
      color: #4a5568;
      border-radius: 999px;
      padding: 8px 18px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .table-mode-btn.active {{
      background: #2c5282;
      color: #fff;
      box-shadow: 0 2px 4px rgba(44,82,130,0.3);
    }}
    .table-mode-btn:hover:not(.active) {{ 
      background: #edf2f7; 
      color: #2c5282;
    }}
    .chart-mode-toggle {{
      display: inline-flex;
      gap: 8px;
      flex-wrap: wrap;
      background: #f7fafc;
      padding: 4px;
      border-radius: 999px;
      border: 1px solid #e2e8f0;
    }}
    .chart-mode-btn {{
      border: none;
      background: transparent;
      color: #4a5568;
      border-radius: 999px;
      padding: 8px 18px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .chart-mode-btn.active {{
      background: #2c5282;
      color: #fff;
      box-shadow: 0 2px 4px rgba(44,82,130,0.3);
    }}
    .chart-mode-btn:hover:not(.active) {{ 
      background: #edf2f7; 
      color: #2c5282;
    }}
    .criteria-panel {{
      flex: 1;
      min-width: 0;
      display: grid;
      gap: 12px;
    }}
    .criteria-dropdown {{
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #fff;
      box-shadow: 0 2px 6px rgba(0,0,0,0.04);
      overflow: hidden;
      transition: all 0.2s ease;
    }}
    .criteria-dropdown:hover {{
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}
    .criteria-dropdown summary {{
      list-style: none;
      cursor: pointer;
      padding: 12px 18px;
      background: #f7fafc;
      color: #2c5282;
      font-weight: 600;
      font-size: 0.95rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      transition: all 0.2s ease;
    }}
    .criteria-dropdown summary:hover {{
      background: #edf2f7;
    }}
    .criteria-dropdown summary::-webkit-details-marker {{ display: none; }}
    .criteria-dropdown summary::after {{
      content: "▾";
      color: #2c5282;
      font-size: 1rem;
      transition: transform 0.2s ease;
    }}
    .criteria-dropdown[open] summary::after {{ 
      transform: rotate(180deg);
    }}
    .criteria-options {{
      display: grid;
      gap: 16px;
      padding: 16px;
      background: #fff;
      border-top: 1px solid #e2e8f0;
      max-height: 60vh;
      overflow-y: auto;
    }}
    .criteria-section {{
      padding: 12px 0;
    }}
    .criteria-section:first-child {{
      padding-top: 0;
    }}
    .criteria-section-title {{
      font-size: 0.88rem;
      font-weight: 700;
      color: #2c5282;
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      border-bottom: 2px solid #2c5282;
      padding-bottom: 6px;
    }}
    .criteria-group {{
      padding: 14px;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #f7fafc;
    }}
    .criteria-group-title {{
      font-size: 0.85rem;
      font-weight: 700;
      color: #2c5282;
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .criteria-group-items {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 10px 14px;
    }}
    .criteria-option {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-size: 0.9rem;
      color: #4a5568;
      cursor: pointer;
      padding: 4px 0;
      transition: color 0.2s ease;
    }}
    .criteria-option:hover {{
      color: #2c5282;
    }}
    .criteria-option input {{ 
      margin: 0; 
      cursor: pointer;
      width: 18px;
      height: 18px;
      accent-color: #2c5282;
    }}
    .criteria-selection {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 0;
      min-height: 28px;
    }}
    .criteria-chip {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 14px;
      border-radius: 999px;
      background: #e6f0ff;
      color: #2c5282;
      border: 1px solid #cbd5e0;
      font-size: 0.85rem;
      font-weight: 600;
      transition: all 0.2s ease;
    }}
    .criteria-chip:hover {{
      background: #dde9ff;
      box-shadow: 0 2px 4px rgba(44,82,130,0.1);
    }}
    .criteria-chip.empty {{
      background: #f7fafc;
      color: #a0aec0;
    }}
    .criteria-chip .k {{
      color: inherit;
      opacity: 0.85;
      font-weight: 500;
    }}
    /* Placeholder */
    .placeholder {{ 
      background: #fff; 
      border-radius: 16px; 
      padding: 64px 40px; 
      text-align: center;
      box-shadow: 0 4px 12px rgba(0,0,0,0.06); 
      color: #718096; 
      border: 1px solid #e2e8f0;
    }}
    .placeholder .icon {{ 
      font-size: 4rem; 
      margin-bottom: 16px; 
    }}
    .placeholder h2 {{ 
      color: #2c5282; 
      margin: 0 0 12px; 
      font-size: 1.5rem;
      font-weight: 700;
    }}
    .placeholder p  {{ 
      max-width: 560px; 
      margin: 0 auto; 
      line-height: 1.7;
      font-size: 1rem;
    }}
    .badge-soon {{ 
      display: inline-block; 
      background: linear-gradient(135deg, #fff3cd 0%, #ffe8a8 100%); 
      color: #856404;
      border: 1px solid #ffc107; 
      border-radius: 999px; 
      padding: 6px 20px;
      font-size: 0.85rem; 
      font-weight: 600; 
      margin-top: 20px;
      box-shadow: 0 2px 4px rgba(133,100,4,0.15);
    }}

    /* Contenu graphiques */
    .chart-block {{ 
      background: #fff; 
      border-radius: 16px; 
      padding: 24px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
      margin-bottom: 24px;
      border: 1px solid #e2e8f0;
      transition: box-shadow 0.2s ease;
    }}
    .chart-block:hover {{
      box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }}
    .chart-block h3 {{ 
      margin: 0 0 16px; 
      font-size: 1.15rem; 
      color: #2c5282;
      border-left: 4px solid #2c5282; 
      padding-left: 14px;
      font-weight: 700;
      letter-spacing: -0.01em;
    }}
    .chart-filters {{ 
      display: flex; 
      flex-wrap: wrap; 
      gap: 12px 18px; 
      margin: 0 0 14px; 
    }}
    .chart-filter-title {{ 
      font-size: 0.9rem; 
      font-weight: 600; 
      color: #2c5282; 
      margin-right: 8px; 
    }}
    .chart-filter-item {{ 
      display: inline-flex; 
      align-items: center; 
      gap: 8px; 
      font-size: 0.9rem; 
      color: #4a5568;
      cursor: pointer;
    }}
    .chart-filter-item:hover {{
      color: #2c5282;
    }}
    .chart-filter-item input {{ 
      margin: 0;
      cursor: pointer;
      width: 18px;
      height: 18px;
      accent-color: #2c5282;
    }}
    .chart-filter-actions {{ 
      display: inline-flex; 
      gap: 8px; 
      margin-left: auto; 
    }}
    .chart-filter-actions button {{
      border: 1px solid #cbd5e0; 
      background: #f7fafc; 
      color: #2c5282;
      border-radius: 6px; 
      padding: 4px 12px; 
      font-size: 0.85rem; 
      cursor: pointer;
      font-weight: 600;
      transition: all 0.2s ease;
    }}
    .chart-filter-actions button:hover {{ 
      background: #2c5282;
      color: #fff;
      border-color: #2c5282;
    }}
    .note-source {{ 
      font-size: 0.85rem; 
      color: #718096; 
      margin-top: 16px;
      padding: 14px 18px; 
      background: #f7fafc; 
      border-radius: 10px;
      border-left: 4px solid #cbd5e0;
      line-height: 1.6;
    }}
    .note-source strong {{
      color: #2c5282;
    }}
    .institution-main {{
      display: grid;
      grid-template-columns: minmax(340px, 1fr) minmax(0, 2fr);
      gap: 24px;
      align-items: start;
      margin-top: 20px;
    }}
    .institution-main .chart-block {{ 
      margin-bottom: 0;
      height: 1400px;
      display: flex;
      flex-direction: column;
    }}
    .institution-main .chart-block > h3 {{
      flex-shrink: 0;
    }}
    .institution-main #block-desc-institution {{
      overflow: hidden;
    }}
    .institution-main #block-desc-institution .regime-description {{
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      padding-right: 6px;
    }}
    .institution-main #charts-institution {{
      flex: 1;
      min-height: 0;
      overflow-y: auto;
    }}
    .regime-description {{ 
      color: #4a5568; 
      font-size: 0.95rem; 
      line-height: 1.65;
    }}
    .regime-description .empty {{ 
      color: #a0aec0; 
      text-align: center;
      padding: 20px;
    }}
    .regime-description .note {{ 
      margin: 0 0 14px; 
      color: #856404; 
      background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%); 
      border: 1px solid #ffe08a; 
      border-radius: 10px; 
      padding: 10px 14px;
      font-size: 0.9rem;
    }}
    .regime-list {{
      display: grid;
      gap: 14px;
      align-content: start;
    }}
    .regime-list::-webkit-scrollbar {{
      width: 8px;
    }}
    .regime-list::-webkit-scrollbar-track {{
      background: #f7fafc;
      border-radius: 4px;
    }}
    .regime-list::-webkit-scrollbar-thumb {{
      background: #cbd5e0;
      border-radius: 4px;
    }}
    .regime-list::-webkit-scrollbar-thumb:hover {{
      background: #a0aec0;
    }}
    .regime-card {{
      border: 1px solid #e2e8f0;
      background: #f7fafc;
      border-radius: 12px;
      padding: 12px 14px;
      transition: all 0.2s ease;
    }}
    .regime-card:hover {{
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
      transform: translateY(-2px);
    }}
    .regime-card-title {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 0 0 10px;
      padding: 6px 12px;
      border-radius: 10px;
      background: linear-gradient(135deg, #e6f0ff 0%, #d9e9ff 100%);
      color: #2c5282;
      font-weight: 700;
      font-size: 0.9rem;
    }}
    .regime-version-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 8px 0 10px;
      align-items: center;
    }}
    .regime-version-row .k {{
      color: #4a5568;
      font-weight: 600;
      font-size: 0.88rem;
      white-space: nowrap;
    }}
    .regime-version-btn {{
      border: 1px solid #cbd5e0;
      background: #fff;
      color: #2c5282;
      border-radius: 999px;
      padding: 4px 12px;
      font-size: 0.85rem;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.2s ease;
    }}
    .regime-version-btn.active {{
      background: #2c5282;
      color: #fff;
      border-color: #2c5282;
      box-shadow: 0 2px 4px rgba(44,82,130,0.3);
    }}
    .regime-version-btn:hover:not(.active) {{
      background: #edf2f7;
      border-color: #2c5282;
    }}
    .chart-filters.locked {{
      opacity: 0.5;
      filter: grayscale(0.3);
      pointer-events: none;
    }}
    .regime-year-chip {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 999px;
      background: #edf2f7;
      color: #2c5282;
      font-size: 0.85rem;
      border: 1px solid #cbd5e0;
      font-weight: 600;
    }}
    .varied {{
      text-decoration: underline;
      text-decoration-color: #d42b2b;
      text-decoration-thickness: 2px;
      text-underline-offset: 3px;
    }}
    .regime-grid {{
      display: grid;
      grid-template-columns: 170px 1fr;
      gap: 8px 14px;
      font-size: 0.95rem;
    }}
    .regime-grid .k {{ 
      color: #4a5568; 
      font-weight: 600; 
    }}
    .regime-grid .v {{ 
      color: #2d3748; 
    }}
    @media (max-width: 1200px) {{
      .institution-main {{ grid-template-columns: 1fr; }}
    }}
    .table-wrap {{ 
      overflow-x: auto; 
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .filterable-table {{ 
      width: 100%; 
      border-collapse: collapse; 
      font-size: 0.95rem; 
    }}
    .filterable-table th, .filterable-table td {{ 
      border: 1px solid #e2e8f0; 
      padding: 12px 14px; 
      text-align: left; 
    }}
    .filterable-table thead tr:first-child th {{ 
      background: linear-gradient(135deg, #2c5282 0%, #1a365d 100%); 
      color: #fff; 
      font-weight: 700;
      font-size: 0.95rem;
      letter-spacing: 0.01em;
    }}
    .filterable-table tbody tr:nth-child(even) td {{ 
      background: #f7fafc; 
    }}
    .filterable-table tbody tr:hover td {{
      background: #edf2f7;
    }}
    .filterable-table .filter-row th {{ 
      background: #edf2f7; 
      padding: 10px 14px;
    }}
    .filterable-table .col-filter {{
      width: 100%;
      padding: 8px 12px;
      border: 1px solid #cbd5e0;
      border-radius: 6px;
      font-size: 0.9rem;
      background: #fff;
      transition: all 0.2s ease;
    }}
    .filterable-table .col-filter:focus {{
      outline: none;
      border-color: #2c5282;
      box-shadow: 0 0 0 3px rgba(44,82,130,0.1);
    }}
  </style>
</head>
<body>

<header>
  <h1>Tableau de bord — Protection sociale en RDC</h1>
  <p>CNSS (2019–2022) &nbsp;·&nbsp; CNSSAP (2020–2022) &nbsp;·&nbsp; Source : ESS OIT/BIT</p>
</header>

<!-- Barre d'onglets -->
<div class="tab-bar">
  <button class="tab-btn active" onclick="switchTab('indicateurs', this)">
    📊 Indicateurs
  </button>
  <button class="tab-btn" onclick="switchTab('institutions', this)">
    🏛 Par institution
  </button>
  <button class="tab-btn" onclick="switchTab('prestations', this)">
    📋 Par prestation
  </button>
</div>

<!-- ═══ ONGLET 1 : INDICATEURS ═══ -->
<div id="tab-indicateurs" class="tab-panel active">
  <div class="chart-block">
    <h3>Indicateurs ESS agrégés</h3>
    <p class="note-source">
      Cette vue présente des indicateurs agrégés issus des séries ESS (effectifs et finances).
      Elle ne constitue pas un taux de couverture effective au sens ODD 1.3.1, faute de dénominateurs démographiques intégrés à ce stade.
    </p>
    <h4 class="numerateurs-title">Numérateurs ODD 1.3.1 disponibles</h4>
    <div id="ind-numerateurs" class="indicator-kpis indicator-kpis-numerateurs"></div>
    <details class="calc-details">
      <summary>Détail du calcul et indicateurs financiers</summary>
      <div id="ind-kpis" class="indicator-kpis"></div>
      <div class="indicator-grid">
        <div id="ind-chart-pop" class="chart-block"></div>
        <div id="ind-chart-fin" class="chart-block"></div>
      </div>
      <div id="ind-chart-inst" class="chart-block" style="margin-top:16px;"></div>
    </details>
    <div class="denom-panel">
      <h3>Futurs dénominateurs ODD 1.3.1 (paramétrables)</h3>
      <p class="note-source">
        Référentiel ODD 1.3.1 (WSPR 2024-26) : population totale, population en âge de travailler, population au-delà de l'âge légal de retraite et femmes ayant accouché (proxy via naissances vivantes). Les valeurs ci-dessous sont des dénominateurs de travail et peuvent être directes, dérivées ou indisponibles selon la source.
      </p>
      <div class="denom-packs">
        <div class="denom-pack" id="pack-total">
          <h4>Population totale</h4>
          <div class="denom-pack-grid">
            <div class="denom-control full">
              <label>Source</label>
              <div id="denom-sources-total" class="denom-source-list"></div>
            </div>
            <div class="denom-control denom-params-separator full"><span>Paramètres</span></div>
            <div class="denom-control">
              <label for="denom-total-year-start">Année début</label>
              <input id="denom-total-year-start" type="number" min="2000" max="2100">
            </div>
            <div class="denom-control">
              <label for="denom-total-year-end">Année fin</label>
              <input id="denom-total-year-end" type="number" min="2000" max="2100">
            </div>
          </div>
        </div>
        <div class="denom-pack" id="pack-active">
          <h4>Population en âge de travailler</h4>
          <div class="denom-pack-grid">
            <div class="denom-control full">
              <label>Source</label>
              <div id="denom-sources-active" class="denom-source-list"></div>
            </div>
            <div class="denom-control denom-params-separator full"><span>Paramètres</span></div>
            <div class="denom-control">
              <label for="denom-active-age-min">Âge actif min</label>
              <input id="denom-active-age-min" type="number" min="10" max="40">
            </div>
            <div class="denom-control">
              <label for="denom-active-age-max">Âge actif max</label>
              <input id="denom-active-age-max" type="number" min="40" max="80">
            </div>
            <div class="denom-control">
              <label for="denom-active-year-start">Année début</label>
              <input id="denom-active-year-start" type="number" min="2000" max="2100">
            </div>
            <div class="denom-control">
              <label for="denom-active-year-end">Année fin</label>
              <input id="denom-active-year-end" type="number" min="2000" max="2100">
            </div>
          </div>
        </div>
        <div class="denom-pack" id="pack-retraite">
          <h4>Population au-delà de l'âge de retraite</h4>
          <div class="denom-pack-grid">
            <div class="denom-control full">
              <label>Source</label>
              <div id="denom-sources-ret" class="denom-source-list"></div>
            </div>
            <div class="denom-control denom-params-separator full"><span>Paramètres</span></div>
            <div class="denom-control">
              <label for="denom-ret-age-h">Âge retraite hommes</label>
              <input id="denom-ret-age-h" type="number" min="40" max="80">
            </div>
            <div class="denom-control">
              <label for="denom-ret-age-f">Âge retraite femmes</label>
              <input id="denom-ret-age-f" type="number" min="40" max="80">
            </div>
            <div class="denom-control">
              <label for="denom-ret-year-start">Année début</label>
              <input id="denom-ret-year-start" type="number" min="2000" max="2100">
            </div>
            <div class="denom-control">
              <label for="denom-ret-year-end">Année fin</label>
              <input id="denom-ret-year-end" type="number" min="2000" max="2100">
            </div>
          </div>
        </div>
        <div class="denom-pack" id="pack-maternite">
          <h4>Femmes ayant accouché (proxy naissances vivantes)</h4>
          <div class="denom-pack-grid">
            <div class="denom-control full">
              <label>Source</label>
              <div id="denom-sources-mat" class="denom-source-list"></div>
            </div>
            <div class="denom-control denom-params-separator full"><span>Paramètres</span></div>
            <div class="denom-control">
              <label for="denom-mat-age-min">Âge maternité min</label>
              <input id="denom-mat-age-min" type="number" min="12" max="30">
            </div>
            <div class="denom-control">
              <label for="denom-mat-age-max">Âge maternité max</label>
              <input id="denom-mat-age-max" type="number" min="30" max="55">
            </div>
            <div class="denom-control">
              <label for="denom-mat-year-start">Année début</label>
              <input id="denom-mat-year-start" type="number" min="2000" max="2100">
            </div>
            <div class="denom-control">
              <label for="denom-mat-year-end">Année fin</label>
              <input id="denom-mat-year-end" type="number" min="2000" max="2100">
            </div>
          </div>
        </div>
      </div>
      <div class="denom-actions">
        <button type="button" id="denom-refresh">Actualiser les dénominateurs</button>
        <span id="denom-status" class="denom-status">Prêt.</span>
      </div>
      <div id="denom-results" class="denom-table-wrap"></div>
    </div>
  </div>
  {note_sources}
</div>

<!-- ═══ ONGLET 2 : PAR INSTITUTION ═══ -->
<div id="tab-institutions" class="tab-panel">
  <div class="selector-bar">
    <label for="sel-institution">Institution :</label>
    <select id="sel-institution" onchange="updateInstitution()">
      {inst_options}
    </select>
  </div>
  <div class="chart-block">
    <h3>Sélection rapide</h3>
    <div class="selector-bar selector-stack" style="margin-bottom:10px;">
      <label for="criteria-dropdown">Critères :</label>
      <div class="criteria-panel">
        <details id="criteria-dropdown" class="criteria-dropdown">
          <summary id="criteria-summary">Aucun critère sélectionné</summary>
          <div id="criteria-options" class="criteria-options"></div>
        </details>
        <div id="criteria-selection" class="criteria-selection"></div>
      </div>
    </div>
    <div id="filters-institution" class="chart-filters" style="display: none;"></div>
    <div class="institution-main">
      <div id="block-desc-institution" class="chart-block">
        <h3 id="title-regime-meta">Description des Régimes sélectionnés</h3>
        <div id="regime-description" class="regime-description">
          <p class="empty">Cochez un régime pour afficher sa description.</p>
        </div>
      </div>
      <div id="block-charts-institution" class="chart-block">
        <h3 id="title-institution">Évolution par régime</h3>
        <div class="selector-bar selector-stack" style="margin-bottom:10px;">
          <label>Affichage :</label>
          <div id="chart-mode-toggle" class="chart-mode-toggle">
            <button type="button" class="chart-mode-btn active" data-sex-mode="all" onclick="setChartSexMode('all')">Tous</button>
            <button type="button" class="chart-mode-btn" data-sex-mode="hommes" onclick="setChartSexMode('hommes')">Hommes</button>
            <button type="button" class="chart-mode-btn" data-sex-mode="femmes" onclick="setChartSexMode('femmes')">Femmes</button>
          </div>
        </div>
        <div id="charts-institution"></div>
      </div>
    </div>
  </div>
  <div id="block-table-institution" class="chart-block">
    <h3>Données détaillées</h3>
    <div class="selector-bar selector-stack" style="margin-bottom:10px;">
      <label>Affichage :</label>
      <div id="table-mode-toggle" class="table-mode-toggle">
        <button type="button" class="table-mode-btn active" data-sex-mode="all" onclick="setTableSexMode('all')">Tous</button>
        <button type="button" class="table-mode-btn" data-sex-mode="hommes" onclick="setTableSexMode('hommes')">Hommes</button>
        <button type="button" class="table-mode-btn" data-sex-mode="femmes" onclick="setTableSexMode('femmes')">Femmes</button>
      </div>
    </div>
    <div id="table-institution"></div>
    {note_sources}
  </div>
</div>

<!-- ═══ ONGLET 3 : PAR PRESTATION ═══ -->
<div id="tab-prestations" class="tab-panel">
  <div class="selector-bar">
    <label for="sel-prest-inst">Institution :</label>
    <select id="sel-prest-inst" onchange="updatePrestationInstitution()">
      {inst_options}
    </select>
    <label for="sel-prest-regime">Régime :</label>
    <select id="sel-prest-regime" onchange="updatePrestationRegime()"></select>
  </div>
  
  <div class="chart-block">
    <h3>Sélection rapide</h3>
    <div class="selector-bar selector-stack" style="margin-bottom:10px;">
      <label for="criteria-prest-dropdown">Filtrer par :</label>
      <div class="criteria-panel">
        <details id="criteria-prest-dropdown" class="criteria-dropdown">
          <summary id="criteria-prest-summary">Toutes les prestations</summary>
          <div id="criteria-prest-options" class="criteria-options"></div>
        </details>
        <div id="criteria-prest-selection" class="criteria-selection"></div>
      </div>
    </div>
    
    <div class="institution-main">
      <div id="block-desc-prestations" class="chart-block">
        <h3>Description des Prestations sélectionnées</h3>
        <div id="prestation-description" class="regime-description">
          <p class="empty">Sélectionnez des prestations pour afficher leur description.</p>
        </div>
      </div>
      
      <div id="block-charts-prestations" class="chart-block">
        <h3 id="title-prestations-regime">Évolution du régime</h3>
        <div class="selector-bar selector-stack" style="margin-bottom:10px;">
          <label>Affichage :</label>
          <div id="chart-mode-regime-prest-toggle" class="chart-mode-toggle">
            <button type="button" class="chart-mode-btn active" data-sex-mode="all" onclick="setChartRegimePrestSexMode('all')">Tous</button>
            <button type="button" class="chart-mode-btn" data-sex-mode="hommes" onclick="setChartRegimePrestSexMode('hommes')">Hommes</button>
            <button type="button" class="chart-mode-btn" data-sex-mode="femmes" onclick="setChartRegimePrestSexMode('femmes')">Femmes</button>
          </div>
        </div>
        <div id="filters-regime-prestations" class="chart-filters" style="display: none;"></div>
        <div id="charts-regime-prestations"></div>
      </div>
    </div>
  </div>
  
  <div id="block-table-prestations" class="chart-block">
    <h3>Données détaillées</h3>
    <div class="selector-bar selector-stack" style="margin-bottom:10px;">
      <label>Affichage :</label>
      <div id="table-mode-prest-toggle" class="table-mode-toggle">
        <button type="button" class="table-mode-btn active" data-sex-mode="all" onclick="setTablePrestSexMode('all')">Tous</button>
        <button type="button" class="table-mode-btn" data-sex-mode="hommes" onclick="setTablePrestSexMode('hommes')">Hommes</button>
        <button type="button" class="table-mode-btn" data-sex-mode="femmes" onclick="setTablePrestSexMode('femmes')">Femmes</button>
      </div>
    </div>
    <div id="table-prestations"></div>
    {note_sources}
  </div>
</div>

<script>
// ── Données pré-calculées ──────────────────────────────────────────────────
const CHARTS_INST  = {charts_inst_json};
const TABLES_INST  = {tables_inst_json};
const CHARTS_PREST = {charts_prest_json};
const TABLES_PREST = {tables_prest_json};
const REGIME_META  = {regime_meta_json};
const PRESTATION_META = {prestation_meta_json};
const NOM_COURT    = {nom_court_json};
const CRITERIA_FIELDS = {criteres_json};
const INDICATEURS_DATA = {indicateurs_json};
const DENOMINATEURS_CONFIG = {denominateurs_json};

function escapeHtml(text) {{
  return String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}}

function injectHtmlAndRunScripts(targetId, html) {{
  const target = document.getElementById(targetId);
  target.innerHTML = html || '';
  target.querySelectorAll('script').forEach(oldScript => {{
    const newScript = document.createElement('script');
    if (oldScript.src) {{
      newScript.src = oldScript.src;
    }} else {{
      newScript.textContent = oldScript.textContent;
    }}
    oldScript.parentNode.replaceChild(newScript, oldScript);
  }});
}}

function initColumnFilters(containerId) {{
  const container = document.getElementById(containerId);
  if (!container) return;
  const table = container.querySelector('.filterable-table');
  if (!table) return;

  const filters = Array.from(table.querySelectorAll('.col-filter'));
  const rows = Array.from(table.querySelectorAll('tbody tr'));
  const applyFilters = () => {{
    const criteria = filters.map(input => input.value.trim().toLowerCase());
    rows.forEach(row => {{
      const cells = row.querySelectorAll('td');
      const visible = criteria.every((crit, idx) => {{
        if (!crit) return true;
        const text = ((cells[idx] && cells[idx].textContent) || '').toLowerCase();
        return text.includes(crit);
      }});
      row.style.display = visible ? '' : 'none';
    }});
  }};

  filters.forEach(input => input.addEventListener('input', applyFilters));
}}

function getRegimeMetaData(inst, rc) {{
  return ((REGIME_META[inst] || {{}})[rc]) || null;
}}

function getRegimeVersions(inst, rc) {{
  const data = getRegimeMetaData(inst, rc);
  return data ? (data.selector_versions || []) : [];
}}

function getLatestRegimeVersion(inst, rc) {{
  const data = getRegimeMetaData(inst, rc);
  if (!data || !data.versions || !data.versions.length) return null;
  return data.versions[data.versions.length - 1];
}}

function normalizeCriterionValue(value) {{
  return String(value === null || value === undefined ? '' : value).trim().toLowerCase();
}}

function getSelectedCriteriaMap() {{
  const host = document.getElementById('criteria-options');
  const selected = {{}};
  if (!host) return selected;
  
  // Collecter les checkboxes ET radio buttons
  Array.from(host.querySelectorAll('input[type="checkbox"]:checked, input[type="radio"]:checked'))
    .forEach(input => {{
      const field = input.getAttribute('data-field') || '';
      const value = input.getAttribute('data-value') || '';
      if (!field || !value) return;
      if (!selected[field]) selected[field] = [];
      selected[field].push(value);
    }});
  return selected;
}}

function formatCriterionChip(fieldLabel, value) {{
  return '<span class="criteria-chip"><span class="k">' + escapeHtml(fieldLabel) + ' :</span> ' + escapeHtml(value) + '</span>';
}}

function updateCriteriaSummary(selectedMap) {{
  const summary = document.getElementById('criteria-summary');
  const host = document.getElementById('criteria-selection');
  if (!summary || !host) return;

  const chips = [];
  let isNameSelection = false;
  
  Object.keys(selectedMap || {{}}).forEach(field => {{
    const fieldDef = CRITERIA_FIELDS.find(item => item.key === field);
    const fieldLabel = fieldDef ? fieldDef.label : field;
    
    if (field === 'nom_regime') {{
      isNameSelection = true;
    }}
    
    (selectedMap[field] || []).forEach(value => {{
      chips.push(formatCriterionChip(fieldLabel, value));
    }});
  }});

  if (isNameSelection) {{
    summary.textContent = 'Sélection directe : ' + (chips.length === 1 ? chips[0].replace(/<[^>]*>/g, '') : chips.length + ' régimes');
  }} else {{
    summary.textContent = chips.length
      ? (chips.length === 1 ? '1 critère sélectionné' : chips.length + ' critères sélectionnés')
      : 'Aucun critère sélectionné';
  }}

  if (!chips.length) {{
    host.innerHTML = '<span class="criteria-chip empty">Aucune sélection active</span>';
    return;
  }}

  host.innerHTML = chips.join('');
}}

function buildCriteriaCatalog(inst) {{
  const metaMap = REGIME_META[inst] || {{}};
  const nameValues = new Set();
  const criteriaGroups = [];
  
  // Collecter les valeurs pour chaque champ
  CRITERIA_FIELDS.forEach(field => {{
    const values = new Map();
    Object.keys(metaMap).forEach(rc => {{
      const regime = metaMap[rc];
      const versions = regime && regime.versions ? regime.versions : [];
      versions.forEach(meta => {{
        if (!meta) return;
        const raw = meta[field.key];
        const rawValues = field.is_list
          ? (Array.isArray(raw) ? raw : [])
          : [raw];
        rawValues.forEach(value => {{
          const text = String(value === null || value === undefined ? '' : value).trim();
          if (!text) return;
          const norm = normalizeCriterionValue(text);
          if (!values.has(norm)) values.set(norm, text);
        }});
      }});
    }});
    
    if (values.size) {{
      if (field.is_name_selector) {{
        // C'est la sélection par nom
        values.forEach(v => nameValues.add(v));
      }} else {{
        // C'est un critère de filtrage
        criteriaGroups.push({{
          key: field.key,
          label: field.label,
          is_multi: field.is_multi,
          is_list: !!field.is_list,
          values: Array.from(values.values()).sort((a, b) => a.localeCompare(b, 'fr', {{ sensitivity: 'base' }})),
        }});
      }}
    }}
  }});
  
  return {{
    names: Array.from(nameValues).sort((a, b) => a.localeCompare(b, 'fr', {{ sensitivity: 'base' }})),
    criteria: criteriaGroups
  }};
}}

function renderCriteriaOptions(inst) {{
  const host = document.getElementById('criteria-options');
  if (!host) return;
  const catalog = buildCriteriaCatalog(inst);
  
  // Section 1 : Sélection par nom
  const nameSection = catalog.names.length ? (
    '<div class="criteria-section">' +
      '<div class="criteria-section-title">Sélection directe</div>' +
      '<div class="criteria-group" data-section="name">' +
        '<div class="criteria-group-items">' +
          catalog.names.map(name => (
            '<label class="criteria-option">' +
              '<input type="checkbox" data-section="name" data-field="nom_regime" data-value="' + escapeHtml(name) + '" checked>' +
              '<span>' + escapeHtml(name) + '</span>' +
            '</label>'
          )).join('') +
        '</div>' +
      '</div>' +
    '</div>'
  ) : '';
  
  // Section 2 : Filtrage par critères
  const criteriaSection = catalog.criteria.length ? (
    '<div class="criteria-section">' +
      '<div class="criteria-section-title">Filtrage par critères</div>' +
      catalog.criteria.map(group => (
        '<div class="criteria-group" data-section="criteria" data-field="' + escapeHtml(group.key) + '">' +
          '<div class="criteria-group-title">' + escapeHtml(group.label) + '</div>' +
          '<div class="criteria-group-items">' +
            group.values.map(value => (
              '<label class="criteria-option">' +
                (group.is_multi 
                  ? '<input type="checkbox" data-field="' + escapeHtml(group.key) + '" data-value="' + escapeHtml(value) + '">'
                  : '<input type="radio" name="criteria-' + escapeHtml(group.key) + '" data-field="' + escapeHtml(group.key) + '" data-value="' + escapeHtml(value) + '">') +
                '<span>' + escapeHtml(value) + '</span>' +
              '</label>'
            )).join('') +
          '</div>' +
        '</div>'
      )).join('') +
    '</div>'
  ) : '';
  
  const resetBtn = (nameSection || criteriaSection) ? '<div style="text-align:right;margin-top:10px;"><button type="button" id="criteria-reset-btn" style="padding:4px 14px;font-size:0.82rem;border:1px solid #cbd5e0;border-radius:6px;background:#f7fafc;color:#4a5568;cursor:pointer;" title="Effacer tous les critères">✕ Réinitialiser</button></div>' : '';
  host.innerHTML = nameSection + (nameSection && criteriaSection ? '<hr style="margin: 16px 0; border: none; border-top: 2px solid #e2e8f0;">' : '') + criteriaSection + resetBtn;

  // Bouton réinitialiser
  const resetButton = host.querySelector('#criteria-reset-btn');
  if (resetButton) {{
    resetButton.addEventListener('click', function() {{
      host.querySelectorAll('input').forEach(inp => {{
        inp.checked = false;
        inp.disabled = false;
        inp.dataset.wasChecked = 'false';
      }});
      host.querySelectorAll('[data-section="name"] input[type="checkbox"]').forEach(cb => {{
        cb.checked = true;
      }});
      host.querySelectorAll('[data-section="criteria"] input').forEach(input => {{
        input.disabled = true;
      }});
      host.querySelectorAll('[data-section="criteria"], [data-section="name"]').forEach(el => {{
        el.style.opacity = '1';
        el.style.pointerEvents = 'auto';
      }});
      host.querySelectorAll('[data-section="criteria"]').forEach(el => {{
        el.style.opacity = '0.5';
        el.style.pointerEvents = 'none';
      }});
      updateCriteriaSummary(getSelectedCriteriaMap());
      applyRegimeQuickFilter();
    }});
  }}

  // Permettre la désélection des radios par double-clic
  host.querySelectorAll('input[type="radio"]').forEach(radio => {{
    radio.addEventListener('mousedown', function() {{
      this.dataset.wasChecked = this.checked ? 'true' : 'false';
    }});
    radio.addEventListener('click', function() {{
      if (this.dataset.wasChecked === 'true') {{
        this.checked = false;
        this.dataset.wasChecked = 'false';
        this.dispatchEvent(new Event('change', {{ bubbles: true }}));
      }}
    }});
  }});

  // Event handlers avec logique d'exclusion mutuelle
  host.querySelectorAll('[data-section="name"] input[type="checkbox"]').forEach(checkbox => {{
    checkbox.addEventListener('change', function() {{
      if (this.checked) {{
        // Désactiver et décocher tous les critères
        host.querySelectorAll('[data-section="criteria"] input').forEach(input => {{
          input.checked = false;
          input.disabled = true;
        }});
        host.querySelectorAll('[data-section="criteria"]').forEach(el => {{
          el.style.opacity = '0.5';
          el.style.pointerEvents = 'none';
        }});
      }} else {{
        // Si plus aucun nom n'est coché, réactiver les critères
        const anyNameChecked = Array.from(host.querySelectorAll('[data-section="name"] input[type="checkbox"]')).some(cb => cb.checked);
        if (!anyNameChecked) {{
          host.querySelectorAll('[data-section="criteria"] input').forEach(input => {{
            input.disabled = false;
          }});
          host.querySelectorAll('[data-section="criteria"]').forEach(el => {{
            el.style.opacity = '1';
            el.style.pointerEvents = 'auto';
          }});
        }}
      }}
      updateCriteriaSummary(getSelectedCriteriaMap());
      applyRegimeQuickFilter();
    }});
  }});

  host.querySelectorAll('[data-section="criteria"] input').forEach(input => {{
    input.addEventListener('change', function() {{
      if (this.checked) {{
        // Désactiver et décocher la sélection par nom
        host.querySelectorAll('[data-section="name"] input').forEach(checkbox => {{
          checkbox.checked = false;
          checkbox.disabled = true;
        }});
        host.querySelectorAll('[data-section="name"]').forEach(el => {{
          el.style.opacity = '0.5';
          el.style.pointerEvents = 'none';
        }});
      }} else {{
        // Si plus aucun critère n'est coché, réactiver les noms
        const anyCriteriaChecked = Array.from(host.querySelectorAll('[data-section="criteria"] input')).some(inp => inp.checked);
        if (!anyCriteriaChecked) {{
          host.querySelectorAll('[data-section="name"] input').forEach(checkbox => {{
            checkbox.disabled = false;
          }});
          host.querySelectorAll('[data-section="name"]').forEach(el => {{
            el.style.opacity = '1';
            el.style.pointerEvents = 'auto';
          }});
        }}
      }}
      updateCriteriaSummary(getSelectedCriteriaMap());
      applyRegimeQuickFilter();
    }});
  }});

  const dropdown = document.getElementById('criteria-dropdown');
  if (dropdown && dropdown.dataset.bound !== '1') {{
    dropdown.addEventListener('toggle', function() {{
      if (!dropdown.open) applyRegimeQuickFilter();
    }});
    dropdown.dataset.bound = '1';
  }}

  host.querySelectorAll('[data-section="name"] input[type="checkbox"]').forEach(cb => {{
    cb.checked = true;
  }});
  host.querySelectorAll('[data-section="criteria"] input').forEach(input => {{
    input.disabled = true;
  }});
  host.querySelectorAll('[data-section="criteria"]').forEach(el => {{
    el.style.opacity = '0.5';
    el.style.pointerEvents = 'none';
  }});

  updateCriteriaSummary(getSelectedCriteriaMap());
  applyRegimeQuickFilter();
}}

function regimeMatchesCriteria(meta, selectedMap) {{
  if (!meta) return false;
  const fields = Object.keys(selectedMap || {{}});
  if (!fields.length) return true;

  return fields.every(field => {{
    const wanted = selectedMap[field] || [];
    if (!wanted.length) return true;
    const raw = meta[field];
    const values = field === 'fonctions_oit'
      ? (Array.isArray(raw) ? raw : [])
      : [raw];
    const normalized = values.map(normalizeCriterionValue).filter(Boolean);
    return wanted.some(value => normalized.indexOf(normalizeCriterionValue(value)) !== -1);
  }});
}}

function makeRegimeCard(inst, rc, activeIndex) {{
  const data = getRegimeMetaData(inst, rc);
  const versions = data ? (data.selector_versions || []) : [];
  if (!versions.length) {{
    return '<div class="regime-card"><p class="regime-card-title">' + escapeHtml(rc) + '</p><p class="empty">Description indisponible pour ce régime.</p></div>';
  }}

  const idx = (activeIndex >= 0 && activeIndex < versions.length) ? activeIndex : 0;
  const meta = versions[idx];
  const varied = new Set((data && data.variation_fields) || []);
  const asText = (val) => (val === null || val === undefined || String(val).trim() === '')
    ? 'Non renseigné'
    : String(val);
  const fonctions = Array.isArray(meta.fonctions_oit) && meta.fonctions_oit.length
    ? meta.fonctions_oit.join('; ')
    : 'Non renseigné';
  
  // Utiliser les années ESS réelles au lieu des années de métadonnées
  const essYears = (data && data.ess_years) || [];
  const yearsDisplay = essYears.length ? essYears.join(', ') : 'Non renseigné';

  const otherButtons = versions.map((v, i) =>
    '<button type="button" class="regime-version-btn' + (i === idx ? ' active' : '') + '" onclick="switchRegimeVersion(' +
      JSON.stringify(inst) + ',' + JSON.stringify(rc) + ',' + i + ')">' + escapeHtml(asText(v.annee)) + '</button>'
  ).join('');

  const otherLine = versions.length > 1
    ? '<div class="regime-version-row"><span class="k">Années de référence</span>' + otherButtons + '</div>'
    : '';

  const field = (label, value, key) => (
    '<div class="k">' + escapeHtml(label) + '</div>' +
    '<div class="v' + (varied.has(key) ? ' varied' : '') + '">' + escapeHtml(asText(value)) + '</div>'
  );

  return (
    '<div class="regime-card" data-inst="' + escapeHtml(inst) + '" data-rc="' + escapeHtml(rc) + '" data-active-index="' + idx + '">' +
      '<p class="regime-card-title">' +
        '<span>' + escapeHtml(meta.nom_regime || NOM_COURT[rc] || rc) + '</span>' +
        '<span class="regime-year-chip">' + escapeHtml(asText(meta.annee)) + '</span>' +
      '</p>' +
      '<div class="regime-grid">' +
        field('Institution', inst, 'institution') +
        field('Nom original', meta.nom_original, 'nom_original') +
        field('Nom du régime', meta.nom_regime || NOM_COURT[rc] || rc, 'nom_regime') +
        field('Années disponibles', yearsDisplay, 'available_years') +
        field('Code régime', rc, 'regime_code') +
        field('Type de financement', meta.type_financement, 'type_financement') +
        field('Type d\\'assurance', meta.type_assurance, 'type_assurance') +
        field('Gestion', meta.gestion, 'gestion') +
        field('Caractère', meta.caractere, 'caractere') +
        field('Administrateur', meta.administrateur, 'administrateur') +
        field('Fonctions couvertes', fonctions, 'fonctions_oit') +
      '</div>' +
      otherLine +
    '</div>'
  );
}}

function switchRegimeVersion(inst, rc, idx) {{
  const container = document.getElementById('regime-description');
  if (!container) return;
  const card = container.querySelector('[data-inst="' + inst + '"][data-rc="' + rc + '"]');
  if (!card) return;
  card.outerHTML = makeRegimeCard(inst, rc, idx);
}}

function renderRegimeDescription(inst, selected) {{
  const host = document.getElementById('regime-description');
  if (!host) return;
  const selectedList = selected || [];
  if (!selectedList.length) {{
    host.innerHTML = '<p class="empty">Aucun régime coché.</p>';
    return;
  }}

  const cards = selectedList.map(rc => {{
    return makeRegimeCard(inst, rc, 0);
  }}).join('');

  host.innerHTML = '<div class="regime-list">' + cards + '</div>';
}}

function initGraphSeriesFilters(plotContainerId, filtersContainerId, label, onSelectionChange, onReady) {{
  const filtersHost = document.getElementById(filtersContainerId);
  if (!filtersHost) return;
  filtersHost.innerHTML = '';

  let tries = 0;
  const bindFilters = () => {{
    const plotContainer = document.getElementById(plotContainerId);
    const plotDiv = plotContainer ? plotContainer.querySelector('.plotly-graph-div') : null;
    if (!plotDiv || !plotDiv.data) {{
      tries += 1;
      if (tries < 20) setTimeout(bindFilters, 50);
      return;
    }}

    const groups = [];
    plotDiv.data.forEach(trace => {{
      const key = trace.legendgroup || trace.name;
      const text = trace.name || key;
      if (!key) return;
      if (!groups.some(g => g.key === key)) {{
        groups.push({{ key: key, label: text }});
      }}
    }});
    if (!groups.length) return;

    const title = document.createElement('span');
    title.className = 'chart-filter-title';
    title.textContent = label + ' :';
    filtersHost.appendChild(title);

    groups.forEach(group => {{
      const wrapper = document.createElement('label');
      wrapper.className = 'chart-filter-item';
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.value = group.key;
      input.checked = true;
      const text = document.createElement('span');
      text.textContent = group.label;
      wrapper.appendChild(input);
      wrapper.appendChild(text);
      filtersHost.appendChild(wrapper);
    }});

    const actions = document.createElement('div');
    actions.className = 'chart-filter-actions';
    actions.innerHTML = '<button type="button">Tout</button><button type="button">Aucun</button>';
    filtersHost.appendChild(actions);

    const getActivePlotDiv = () => {{
      const c = document.getElementById(plotContainerId);
      return c ? c.querySelector('.plotly-graph-div') : null;
    }};
    const applySeriesFilter = () => {{
      const activePlotDiv = getActivePlotDiv();
      if (!activePlotDiv || !activePlotDiv.data) return;
      const selected = Array.from(filtersHost.querySelectorAll('input[type="checkbox"]'))
        .filter(cb => cb.checked)
        .map(cb => cb.value);
      const visible = activePlotDiv.data.map(trace => {{
        const key = trace.legendgroup || trace.name;
        return selected.includes(key) ? true : 'legendonly';
      }});
      Plotly.restyle(activePlotDiv, {{ visible: visible }});
      if (onSelectionChange) onSelectionChange(selected);
    }};
    // Filtre piloté par liste externe (sélection rapide)
    filtersHost._applySeriesFilterWithSelection = (allowedKeys) => {{
      const activePlotDiv = getActivePlotDiv();
      if (!activePlotDiv || !activePlotDiv.data) return;
      filtersHost.querySelectorAll('input[type="checkbox"]').forEach(cb => {{
        cb.checked = !allowedKeys.length || allowedKeys.some(k => cb.value === k || cb.value.startsWith(k));
      }});
      const sel2 = Array.from(filtersHost.querySelectorAll('input[type="checkbox"]'))
        .filter(cb => cb.checked).map(cb => cb.value);
      const vis2 = activePlotDiv.data.map(trace => {{
        const key = trace.legendgroup || trace.name;
        return sel2.includes(key) ? true : 'legendonly';
      }});
      Plotly.restyle(activePlotDiv, {{ visible: vis2 }});
    }};

    filtersHost.querySelectorAll('input[type=\"checkbox\"]').forEach(cb => {{
      cb.addEventListener('change', applySeriesFilter);
    }});
    filtersHost._applySeriesFilter = applySeriesFilter;
    filtersHost._setLocked = (locked) => {{
      filtersHost.classList.toggle('locked', locked);
      filtersHost.querySelectorAll('input[type=\"checkbox\"]').forEach(cb => {{
        cb.disabled = locked;
      }});
    }};
    const buttons = actions.querySelectorAll('button');
    buttons[0].addEventListener('click', () => {{
      filtersHost.querySelectorAll('input[type=\"checkbox\"]').forEach(cb => cb.checked = true);
      if (filtersHost._setLocked) filtersHost._setLocked(false);
      applySeriesFilter();
    }});
    buttons[1].addEventListener('click', () => {{
      filtersHost.querySelectorAll('input[type=\"checkbox\"]').forEach(cb => cb.checked = false);
      if (filtersHost._setLocked) filtersHost._setLocked(false);
      applySeriesFilter();
    }});
    applySeriesFilter();
    
    // Appeler le callback onReady une fois que tout est initialisé
    if (onReady) onReady();
  }};

  bindFilters();
}}

// ── Navigation onglets ─────────────────────────────────────────────────────
function switchTab(name, btn) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  if (btn) btn.classList.add('active');
}}

// ── Onglet indicateurs ───────────────────────────────────────────────────────
function fmtInt(value) {{
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  return Number(value).toLocaleString('fr-FR', {{ maximumFractionDigits: 0 }});
}}

function fmtMds(value) {{
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  return Number(value).toLocaleString('fr-FR', {{ minimumFractionDigits: 1, maximumFractionDigits: 1 }}) + ' Mds CDF';
}}

function fmtPct(value) {{
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  return (Number(value) * 100).toLocaleString('fr-FR', {{ minimumFractionDigits: 1, maximumFractionDigits: 1 }}) + ' %';
}}

function renderIndicateurs() {{
  const payload = INDICATEURS_DATA || {{}};
  const latest = payload.latest || null;
  const years = payload.years || [];
  const totaux = payload.totaux || {{}};
  const byInst = payload.institutions_latest || [];

  const numHost = document.getElementById('ind-numerateurs');
  const kpiHost = document.getElementById('ind-kpis');
  if (!numHost || !kpiHost) return;

  if (!latest || !years.length) {{
    numHost.innerHTML = '<p class="empty">Aucune donnée disponible.</p>';
    kpiHost.innerHTML = '';
    return;
  }}

  // Numérateurs ODD 1.3.1 : effectifs couverts (affiché en premier, en évidence)
  const numCards = [
    {{
      label: 'Cotisants actifs (' + latest.annee + ')',
      sublabel: 'Proxy : population active couverte',
      value: fmtInt(latest.cotisants),
      icon: '👷'
    }},
    {{
      label: 'Bénéficiaires (' + latest.annee + ')',
      sublabel: 'Proxy : personnes recevant des prestations',
      value: fmtInt(latest.beneficiaires),
      icon: '🧾'
    }},
  ];
  numHost.innerHTML = numCards.map(card =>
    '<div class="kpi-card kpi-card-numerateur">' +
      '<div class="kpi-icon">' + card.icon + '</div>' +
      '<div class="kpi-label">' + escapeHtml(card.label) + '</div>' +
      '<div class="kpi-value">' + escapeHtml(card.value) + '</div>' +
      '<div class="kpi-sublabel">' + escapeHtml(card.sublabel) + '</div>' +
    '</div>'
  ).join('');

  // Détail du calcul : ratios et indicateurs financiers (dans le <details>)
  const detailCards = [
    {{ label: 'Bénéficiaires / Cotisants', value: fmtPct(latest.ratio_benef_cotis) }},
    {{ label: 'Dépenses de prestations', value: fmtMds(latest.depenses_mds) }},
    {{ label: 'Recettes', value: fmtMds(latest.recettes_mds) }},
    {{ label: 'Dépenses / Recettes', value: fmtPct(latest.ratio_dep_rec) }},
  ];
  kpiHost.innerHTML = detailCards.map(card =>
    '<div class="kpi-card"><div class="kpi-label">' + escapeHtml(card.label) + '</div><div class="kpi-value">' + escapeHtml(card.value) + '</div></div>'
  ).join('');

  Plotly.newPlot('ind-chart-pop', [
    {{
      x: years,
      y: totaux.cotisants || [],
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Cotisants',
      line: {{ color: '#2c5282', width: 3 }},
      marker: {{ size: 8 }},
    }},
    {{
      x: years,
      y: totaux.beneficiaires || [],
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Bénéficiaires',
      line: {{ color: '#dd6b20', width: 3 }},
      marker: {{ size: 8 }},
    }},
  ], {{
    title: 'Évolution des effectifs agrégés',
    margin: {{ t: 52, r: 24, b: 48, l: 68 }},
    hovermode: 'x unified',
    xaxis: {{ tickformat: 'd', dtick: 1 }},
    yaxis: {{ separatethousands: true }},
    legend: {{ orientation: 'h', y: -0.2 }},
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#ffffff',
  }}, {{ responsive: true }});

  Plotly.newPlot('ind-chart-fin', [
    {{
      x: years,
      y: totaux.depenses_mds || [],
      type: 'bar',
      name: 'Dépenses',
      marker: {{ color: '#805ad5' }},
    }},
    {{
      x: years,
      y: totaux.recettes_mds || [],
      type: 'bar',
      name: 'Recettes',
      marker: {{ color: '#38a169' }},
    }},
  ], {{
    title: 'Évolution financière agrégée (Mds CDF)',
    margin: {{ t: 52, r: 24, b: 48, l: 68 }},
    barmode: 'group',
    hovermode: 'x',
    xaxis: {{ tickformat: 'd', dtick: 1 }},
    legend: {{ orientation: 'h', y: -0.2 }},
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#ffffff',
  }}, {{ responsive: true }});

  Plotly.newPlot('ind-chart-inst', [
    {{
      x: byInst.map(r => r.institution),
      y: byInst.map(r => r.cotisants),
      type: 'bar',
      name: 'Cotisants',
      marker: {{ color: '#2c5282' }},
    }},
    {{
      x: byInst.map(r => r.institution),
      y: byInst.map(r => r.beneficiaires),
      type: 'bar',
      name: 'Bénéficiaires',
      marker: {{ color: '#dd6b20' }},
    }},
  ], {{
    title: 'Comparaison par institution (' + latest.annee + ')',
    margin: {{ t: 52, r: 24, b: 48, l: 68 }},
    barmode: 'group',
    yaxis: {{ separatethousands: true }},
    legend: {{ orientation: 'h', y: -0.2 }},
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#ffffff',
  }}, {{ responsive: true }});
}}

function fmtPlain(value) {{
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "N/D";
  return Number(value).toLocaleString('fr-FR', {{ maximumFractionDigits: 0 }});
}}

function setDenomStatus(text) {{
  const el = document.getElementById('denom-status');
  if (el) el.textContent = text;
}}


function renderDenominatorTable(rows) {{
  const host = document.getElementById('denom-results');
  if (!host) return;
  if (!rows || !rows.length) {{
    host.innerHTML = '<p class="empty">Aucun dénominateur disponible.</p>';
    return;
  }}
  const header = (
    '<table class="denom-table">' +
      '<thead><tr>' +
        '<th>Année</th>' +
        '<th>Population totale</th>' +
        '<th>Population active</th>' +
        '<th>Population retraite</th>' +
        '<th>Naissances vivantes (proxy)</th>' +
        '<th>Femmes ayant accouché (proxy)</th>' +
      '</tr></thead><tbody>'
  );
  const body = rows.map(row => (
    '<tr>' +
      '<td>' + escapeHtml(String(row.year)) + '</td>' +
      '<td>' + escapeHtml(fmtPlain(row.populationTotale)) + '<small>' + escapeHtml(row.metaTotal || '') + '</small></td>' +
      '<td>' + escapeHtml(fmtPlain(row.populationActive)) + '<small>' + escapeHtml(row.metaActive || '') + '</small></td>' +
      '<td>' + escapeHtml(fmtPlain(row.populationRetraite)) + '<small>' + escapeHtml(row.metaRetraite || '') + '</small></td>' +
      '<td>' + escapeHtml(fmtPlain(row.naissancesVivantes)) + '<small>' + escapeHtml(row.metaNaissances || '') + '</small></td>' +
      '<td>' + escapeHtml(fmtPlain(row.femmesAyantAccouche)) + '<small>' + escapeHtml(row.metaFemmes || '') + '</small></td>' +
    '</tr>'
  )).join('');
  host.innerHTML = header + body + '</tbody></table>';
}}

// ── Banque mondiale ────────────────────────────────────────────────────────
async function fetchWorldBankIndicator(indicatorCode) {{
  window.__WB_CACHE = window.__WB_CACHE || {{}};
  if (window.__WB_CACHE[indicatorCode]) return window.__WB_CACHE[indicatorCode];
  const url = 'https://api.worldbank.org/v2/country/CD/indicator/' + indicatorCode + '?format=json&per_page=200';
  const res = await fetch(url);
  if (!res.ok) throw new Error('Banque mondiale HTTP ' + res.status);
  const data = await res.json();
  const rows = Array.isArray(data) && Array.isArray(data[1]) ? data[1] : [];
  const parsed = rows
    .filter(r => r && r.value !== null && r.date)
    .map(r => ({{ year: Number(r.date), value: Number(r.value) }}))
    .filter(r => Number.isFinite(r.year) && Number.isFinite(r.value));
  window.__WB_CACHE[indicatorCode] = parsed;
  return parsed;
}}

// ── ONU WPP via PopulationPyramid.net ───────────────────────────────────────
// API gratuite basée sur ONU WPP 2024, sans authentification, CORS ouvert.
// URL : https://www.populationpyramid.net/api/pp/180/{{YEAR}}/  (180 = M49 RDC)
// Réponse : {{ females: [{{Age:"0-4", F:12345}}, ...], males: [{{Age:"0-4", M:12345}}, ...] }}
// Valeurs en personnes (pas en milliers).
// Cache par année (une requête par année demandée).
window.__WPP_CACHE = window.__WPP_CACHE || {{}};

async function fetchWPPYear(year) {{
  const y = String(year);
  if (window.__WPP_CACHE[y]) return window.__WPP_CACHE[y];
  const url = 'https://www.populationpyramid.net/api/pp/180/' + y + '/';
  const res = await fetch(url);
  if (!res.ok) throw new Error('WPP HTTP ' + res.status + ' pour ' + y);
  const json = await res.json();
  // Construire tableau : [{{ageStart, ageEnd, value}}]
  const parse = row => {{
    const label = (row.Age || '').trim();
    if (label === '100+') return {{ ageStart: 100, ageEnd: 999 }};
    const parts = label.split('-');
    return {{ ageStart: Number(parts[0]), ageEnd: Number(parts[1] !== undefined ? parts[1] : parts[0]) }};
  }};
  const groups = [];
  const males   = Array.isArray(json.males)   ? json.males   : [];
  const females = Array.isArray(json.females) ? json.females : [];
  males.forEach(r => {{
    const ag = parse(r);
    groups.push({{ ...ag, value: Number(r.M || 0), sex: 'M' }});
  }});
  females.forEach(r => {{
    const ag = parse(r);
    groups.push({{ ...ag, value: Number(r.F || 0), sex: 'F' }});
  }});
  window.__WPP_CACHE[y] = groups;
  return groups;
}}

// Somme la pyramide WPP pour une tranche [ageMin, ageMax] et une année donnée.
// Stratégie : groupes quinquennaux entièrement inclus dans la tranche.
async function sumWPPForAgeRange(year, ageMin, ageMax) {{
  const groups = await fetchWPPYear(year);
  return groups
    .filter(r => r.ageStart >= ageMin && r.ageEnd <= ageMax)
    .reduce((s, r) => s + r.value, 0) || null;
}}

// ── ILOSTAT / OIT ────────────────────────────────────────────────────────
// Retourne les actifs employés RDC : [{{year, value}}]
async function fetchILOSTATEmployment() {{
  if (window.__ILO_CACHE) return window.__ILO_CACHE;
  // API ILO REST publique — emploi total RDC, les deux sexes
  const url = 'https://rplumber.ilo.org/data/indicator/?id=EMP_TEMP_SEX_AGE_NB_A&ref_area=COD&sex=SEX_T&classif1=AGE_AGGREGATE_TOTAL&time_from=2000&time_to=2030&type=label&decimals=0';
  const res = await fetch(url);
  if (!res.ok) throw new Error('ILOSTAT HTTP ' + res.status);
  const json = await res.json();
  const rows = (Array.isArray(json.data) ? json.data : [])
    .filter(r => r.obs_value !== null && r.obs_value !== undefined)
    .map(r => ({{ year: Number(r.time), value: Number(r.obs_value) }}))
    .filter(r => Number.isFinite(r.year) && Number.isFinite(r.value));
  window.__ILO_CACHE = rows;
  return rows;
}}

function pickSeriesValue(series, year, useNearestPast) {{
  if (!Array.isArray(series) || !series.length) return null;
  const exact = series.find(r => r.year === year);
  if (exact) return exact.value;
  if (!useNearestPast) return null;
  const candidates = series.filter(r => r.year <= year).sort((a, b) => b.year - a.year);
  if (candidates.length) return candidates[0].value;
  const sorted = [...series].sort((a, b) => b.year - a.year);
  return sorted[0] ? sorted[0].value : null;
}}

function getNumInput(id) {{
  const el = document.getElementById(id);
  const val = el ? Number(el.value) : NaN;
  return Number.isFinite(val) ? val : null;
}}

function getMetricCardParams(metricKey) {{
  if (metricKey === 'population_totale') {{
    return {{
      yearStart: getNumInput('denom-total-year-start'),
      yearEnd: getNumInput('denom-total-year-end'),
    }};
  }}
  if (metricKey === 'population_active') {{
    return {{
      yearStart: getNumInput('denom-active-year-start'),
      yearEnd: getNumInput('denom-active-year-end'),
      workMin: getNumInput('denom-active-age-min'),
      workMax: getNumInput('denom-active-age-max'),
    }};
  }}
  if (metricKey === 'population_retraite') {{
    return {{
      yearStart: getNumInput('denom-ret-year-start'),
      yearEnd: getNumInput('denom-ret-year-end'),
      retirementH: getNumInput('denom-ret-age-h'),
      retirementF: getNumInput('denom-ret-age-f'),
    }};
  }}
  return {{
    yearStart: getNumInput('denom-mat-year-start'),
    yearEnd: getNumInput('denom-mat-year-end'),
    matMin: getNumInput('denom-mat-age-min'),
    matMax: getNumInput('denom-mat-age-max'),
  }};
}}

function getSelectedMetricSource(metricShortKey) {{
  const selected = document.querySelector('input[name="denom-source-' + metricShortKey + '"]:checked');
  return selected ? selected.value : '';
}}

function sourceIsAvailableForMetric(sourceKey, metricKey, params) {{
  if (!sourceKey || !params || !params.yearStart || !params.yearEnd || params.yearEnd < params.yearStart) return false;
  if (sourceKey === 'bm_api') {{
    // Banque mondiale : tranches fixes seulement
    if (metricKey === 'population_retraite') {{
      return params.retirementH === 65 && params.retirementF === 65;
    }}
    if (metricKey === 'population_active') {{
      return params.workMin === 15 && params.workMax === 64;
    }}
    return true; // totale, naissances : toujours dispo
  }}
  if (sourceKey === 'wpp_api') {{
    // WPP PopPyramid : pyramide quinquennale → toutes tranches d'âge possibles
    return true;
  }}
  if (sourceKey === 'ilostat_api') {{
    // ILOSTAT : uniquement population active (emploi total, pas de tranche custom)
    return metricKey === 'population_active';
  }}
  return false;
}}

function renderMetricSourceOptions(metricShortKey, metricKey, defaultSource, sources) {{
  const host = document.getElementById('denom-sources-' + metricShortKey);
  if (!host) return;
  const params = getMetricCardParams(metricKey);
  const keys = Object.keys(sources || {{}});
  const available = keys.filter(k => sourceIsAvailableForMetric(k, metricKey, params));
  const effective = available.includes(defaultSource) ? defaultSource : (available[0] || '');
  host.innerHTML = keys.map((k, idx) => {{
    const src = sources[k] || {{}};
    const ok = sourceIsAvailableForMetric(k, metricKey, params);
    const id = 'src-' + metricShortKey + '-' + idx;
    const checked = effective === k ? ' checked' : '';
    const disabled = ok ? '' : ' disabled';
    const cls = 'denom-source-item' + (ok ? '' : ' disabled');
    return (
      '<label class="' + cls + '" for="' + id + '">' +
      '<input type="radio" name="denom-source-' + metricShortKey + '" id="' + id + '" value="' + escapeHtml(k) + '"' + checked + disabled + '>' +
      '<span>' + escapeHtml(src.label || k) + '</span>' +
      '</label>'
    );
  }}).join('');
}}

function refreshMetricSources(sources) {{
  renderMetricSourceOptions('total', 'population_totale', getSelectedMetricSource('total'), sources);
  renderMetricSourceOptions('active', 'population_active', getSelectedMetricSource('active'), sources);
  renderMetricSourceOptions('ret', 'population_retraite', getSelectedMetricSource('ret'), sources);
  renderMetricSourceOptions('mat', 'naissances', getSelectedMetricSource('mat'), sources);
}}

async function getMetricValue(sourceKey, metricKey, year, params, seriesCache) {{
  if (!sourceKey) return {{ value: null, meta: 'Source non définie' }};

  // ── Banque mondiale ──────────────────────────────────────────────────────
  if (sourceKey === 'bm_api') {{
    if (metricKey === 'population_totale') {{
      seriesCache.bm_total = seriesCache.bm_total || await fetchWorldBankIndicator('SP.POP.TOTL');
      return {{ value: pickSeriesValue(seriesCache.bm_total, year, true), meta: 'BM (SP.POP.TOTL)' }};
    }}
    if (metricKey === 'population_active') {{
      if (params.workMin !== 15 || params.workMax !== 64) {{
        return {{ value: null, meta: 'BM : tranche 15-64 uniquement' }};
      }}
      seriesCache.bm_active = seriesCache.bm_active || await fetchWorldBankIndicator('SP.POP.1564.TO');
      return {{ value: pickSeriesValue(seriesCache.bm_active, year, true), meta: 'BM (SP.POP.1564.TO)' }};
    }}
    if (metricKey === 'population_retraite') {{
      if (params.retirementH !== 65 || params.retirementF !== 65) {{
        return {{ value: null, meta: 'BM : tranche 65+ uniquement' }};
      }}
      seriesCache.bm_old = seriesCache.bm_old || await fetchWorldBankIndicator('SP.POP.65UP.TO');
      return {{ value: pickSeriesValue(seriesCache.bm_old, year, true), meta: 'BM (SP.POP.65UP.TO)' }};
    }}
    if (metricKey === 'naissances' || metricKey === 'femmes_accouche') {{
      seriesCache.bm_total = seriesCache.bm_total || await fetchWorldBankIndicator('SP.POP.TOTL');
      seriesCache.bm_cbr   = seriesCache.bm_cbr   || await fetchWorldBankIndicator('SP.DYN.CBRT.IN');
      const pop = pickSeriesValue(seriesCache.bm_total, year, true);
      const cbr = pickSeriesValue(seriesCache.bm_cbr,   year, true);
      if (!pop || !cbr) return {{ value: null, meta: 'BM : données natalité incomplètes' }};
      return {{ value: (pop * cbr) / 1000.0, meta: 'BM (CBR × Pop totale)' }};
    }}
    return {{ value: null, meta: 'BM : métrique non gérée' }};
  }}

  // ── ONU WPP via PopulationPyramid.net ───────────────────────────────────
  if (sourceKey === 'wpp_api') {{
    if (metricKey === 'population_totale') {{
      const v = await sumWPPForAgeRange(year, 0, 999);
      return {{ value: v, meta: 'WPP (pyramide totale ' + year + ')' }};
    }}
    if (metricKey === 'population_active') {{
      const v = await sumWPPForAgeRange(year, params.workMin || 15, params.workMax || 64);
      return {{ value: v, meta: 'WPP (' + (params.workMin||15) + '-' + (params.workMax||64) + ', ' + year + ')' }};
    }}
    if (metricKey === 'population_retraite') {{
      const retMin = Math.min(params.retirementH || 65, params.retirementF || 65);
      const v = await sumWPPForAgeRange(year, retMin, 999);
      return {{ value: v, meta: 'WPP (' + retMin + '+, ' + year + ')' }};
    }}
    if (metricKey === 'naissances' || metricKey === 'femmes_accouche') {{
      // Proxy : on utilise taux brut BM × pop WPP totale
      seriesCache.bm_cbr = seriesCache.bm_cbr || await fetchWorldBankIndicator('SP.DYN.CBRT.IN');
      const pop = await sumWPPForAgeRange(year, 0, 999);
      const cbr = pickSeriesValue(seriesCache.bm_cbr, year, true);
      if (!pop || !cbr) return {{ value: null, meta: 'WPP+BM : données natalité incomplètes' }};
      return {{ value: (pop * cbr) / 1000.0, meta: 'WPP pop × BM CBR (proxy)' }};
    }}
    return {{ value: null, meta: 'WPP : métrique non gérée' }};
  }}

  // ── ILOSTAT / OIT ────────────────────────────────────────────────────────
  if (sourceKey === 'ilostat_api') {{
    if (metricKey !== 'population_active') {{
      return {{ value: null, meta: 'ILOSTAT : uniquement population active' }};
    }}
    seriesCache.ilo = seriesCache.ilo || await fetchILOSTATEmployment();
    const v = pickSeriesValue(seriesCache.ilo, year, true);
    return {{ value: v, meta: 'ILOSTAT (emploi total RDC)' }};
  }}

  return {{ value: null, meta: sourceKey + ' : source inconnue' }};
}}

async function computeDenominators() {{
  const pTotal = getMetricCardParams('population_totale');
  const pActive = getMetricCardParams('population_active');
  const pRet = getMetricCardParams('population_retraite');
  const pMat = getMetricCardParams('naissances');
  const srcTotal = getSelectedMetricSource('total');
  const srcActive = getSelectedMetricSource('active');
  const srcRet = getSelectedMetricSource('ret');
  const srcMat = getSelectedMetricSource('mat');

  const ranges = [pTotal, pActive, pRet, pMat]
    .filter(x => x && x.yearStart && x.yearEnd && x.yearEnd >= x.yearStart);
  if (!ranges.length) {{
    setDenomStatus('Paramètres années invalides.');
    return;
  }}
  const minYear = Math.min(...ranges.map(r => r.yearStart));
  const maxYear = Math.max(...ranges.map(r => r.yearEnd));

  setDenomStatus('Calcul multi-annuel en cours...');
  const seriesCache = {{}};
  const outRows = [];
  try {{
    for (let y = minYear; y <= maxYear; y += 1) {{
      const total = (y >= pTotal.yearStart && y <= pTotal.yearEnd)
        ? await getMetricValue(srcTotal, 'population_totale', y, pTotal, seriesCache)
        : {{ value: null, meta: 'hors plage' }};
      const active = (y >= pActive.yearStart && y <= pActive.yearEnd)
        ? await getMetricValue(srcActive, 'population_active', y, pActive, seriesCache)
        : {{ value: null, meta: 'hors plage' }};
      const retraite = (y >= pRet.yearStart && y <= pRet.yearEnd)
        ? await getMetricValue(srcRet, 'population_retraite', y, pRet, seriesCache)
        : {{ value: null, meta: 'hors plage' }};
      const naissances = (y >= pMat.yearStart && y <= pMat.yearEnd)
        ? await getMetricValue(srcMat, 'naissances', y, pMat, seriesCache)
        : {{ value: null, meta: 'hors plage' }};
      const femmes = (y >= pMat.yearStart && y <= pMat.yearEnd)
        ? await getMetricValue(srcMat, 'femmes_accouche', y, pMat, seriesCache)
        : {{ value: null, meta: 'hors plage' }};
      outRows.push({{
        year: y,
        populationTotale: total.value,
        populationActive: active.value,
        populationRetraite: retraite.value,
        naissancesVivantes: naissances.value,
        femmesAyantAccouche: femmes.value,
        metaTotal: total.meta,
        metaActive: active.meta,
        metaRetraite: retraite.meta,
        metaNaissances: naissances.meta,
        metaFemmes: femmes.meta,
      }});
    }}
  }} catch (err) {{
    setDenomStatus('Erreur source: ' + String(err && err.message ? err.message : err));
    return;
  }}
  renderDenominatorTable(outRows);
  setDenomStatus('Dénominateurs calculés pour ' + outRows.length + ' année(s).');
}}

// Contraintes de paramètres selon la source choisie.
// Quand BM est sélectionné : tranches d'âge fixes (15-64, 65+) → on verrouille les champs.
// Quand WPP est sélectionné : tranches libres → on déverrouille.
// Quand ILOSTAT : pas de tranche d'âge (emploi agrégé) → on masque/verrouille les champs d'âge.
const SOURCE_CONSTRAINTS = {{
  bm_api: {{
    population_active:  {{ workMin: 15, workMax: 64,  lock: ['denom-active-age-min', 'denom-active-age-max'] }},
    population_retraite: {{ retH: 65,    retF: 65,     lock: ['denom-ret-age-h', 'denom-ret-age-f'] }},
  }},
  wpp_api: {{
    population_active:   {{ lock: [] }},
    population_retraite: {{ lock: [] }},
    naissances:          {{ lock: [] }},
  }},
  ilostat_api: {{
    population_active: {{ lock: ['denom-active-age-min', 'denom-active-age-max'], note: "ILOSTAT : emploi total, tranche d'âge non personnalisable" }},
  }},
}};

function applySourceConstraints(metricShortKey, metricKey, sourceKey) {{
  const constraints = (SOURCE_CONSTRAINTS[sourceKey] || {{}})[metricKey] || {{}};
  const lockIds = constraints.lock || [];

  // Déterminer tous les champs de paramètre de ce paquet
  const allParamIds = {{
    population_active:   ['denom-active-age-min', 'denom-active-age-max'],
    population_retraite: ['denom-ret-age-h', 'denom-ret-age-f'],
    naissances:          ['denom-mat-age-min', 'denom-mat-age-max'],
    femmes_accouche:     ['denom-mat-age-min', 'denom-mat-age-max'],
  }}[metricKey] || [];

  // Déverrouiller tous, puis reverrouiller ceux qui doivent l'être
  allParamIds.forEach(id => {{
    const el = document.getElementById(id);
    if (!el) return;
    el.readOnly = false;
    el.classList.remove('constrained');
    el.title = '';
  }});

  // Pré-remplir les valeurs contraintes
  if (sourceKey === 'bm_api' && metricKey === 'population_active') {{
    const mn = document.getElementById('denom-active-age-min');
    const mx = document.getElementById('denom-active-age-max');
    if (mn) {{ mn.value = 15; mn.readOnly = true; mn.classList.add('constrained'); mn.title = 'Banque mondiale : tranche 15-64 uniquement'; }}
    if (mx) {{ mx.value = 64; mx.readOnly = true; mx.classList.add('constrained'); mx.title = 'Banque mondiale : tranche 15-64 uniquement'; }}
  }}
  if (sourceKey === 'bm_api' && metricKey === 'population_retraite') {{
    const h = document.getElementById('denom-ret-age-h');
    const f = document.getElementById('denom-ret-age-f');
    if (h) {{ h.value = 65; h.readOnly = true; h.classList.add('constrained'); h.title = 'Banque mondiale : tranche 65+ uniquement'; }}
    if (f) {{ f.value = 65; f.readOnly = true; f.classList.add('constrained'); f.title = 'Banque mondiale : tranche 65+ uniquement'; }}
  }}
  if (sourceKey === 'ilostat_api' && metricKey === 'population_active') {{
    const mn = document.getElementById('denom-active-age-min');
    const mx = document.getElementById('denom-active-age-max');
    const note = "ILOSTAT : emploi total, tranche d'âge non applicable";
    if (mn) {{ mn.readOnly = true; mn.classList.add('constrained'); mn.title = note; }}
    if (mx) {{ mx.readOnly = true; mx.classList.add('constrained'); mx.title = note; }}
  }}
}}

function applyAllConstraints() {{
  applySourceConstraints('active', 'population_active',   getSelectedMetricSource('active'));
  applySourceConstraints('ret',    'population_retraite',  getSelectedMetricSource('ret'));
  applySourceConstraints('mat',    'naissances',           getSelectedMetricSource('mat'));
}}

function initDenominatorPanel() {{
  const cfg = DENOMINATEURS_CONFIG || {{}};
  const sources = cfg.sources || {{}};
  const defaults = cfg.defaults || {{}};
  if (!document.getElementById('denom-results')) return;

  document.getElementById('denom-total-year-start').value = defaults.year_start_total || 2020;
  document.getElementById('denom-total-year-end').value = defaults.year_end_total || 2024;
  document.getElementById('denom-active-year-start').value = defaults.year_start_active || 2020;
  document.getElementById('denom-active-year-end').value = defaults.year_end_active || 2024;
  document.getElementById('denom-ret-year-start').value = defaults.year_start_retraite || 2020;
  document.getElementById('denom-ret-year-end').value = defaults.year_end_retraite || 2024;
  document.getElementById('denom-mat-year-start').value = defaults.year_start_maternite || 2020;
  document.getElementById('denom-mat-year-end').value = defaults.year_end_maternite || 2024;

  document.getElementById('denom-active-age-min').value = defaults.working_age_min || 15;
  document.getElementById('denom-active-age-max').value = defaults.working_age_max || 64;
  document.getElementById('denom-ret-age-h').value = defaults.retirement_age_h || 65;
  document.getElementById('denom-ret-age-f').value = defaults.retirement_age_f || 65;
  document.getElementById('denom-mat-age-min').value = defaults.maternity_age_min || 15;
  document.getElementById('denom-mat-age-max').value = defaults.maternity_age_max || 49;

  renderMetricSourceOptions('total', 'population_totale', defaults.source_population_totale, sources);
  renderMetricSourceOptions('active', 'population_active', defaults.source_population_active, sources);
  renderMetricSourceOptions('ret', 'population_retraite', defaults.source_population_retraite, sources);
  renderMetricSourceOptions('mat', 'naissances', defaults.source_maternite, sources);

  // Appliquer les contraintes initiales selon les sources par défaut
  applyAllConstraints();

  const refreshBtn = document.getElementById('denom-refresh');
  if (refreshBtn) {{
    refreshBtn.addEventListener('click', () => {{
      computeDenominators();
    }});
  }}

  document.querySelectorAll('.denom-pack input').forEach(el => {{
    el.addEventListener('change', () => {{
      // Si c'est un radio de source : appliquer les contraintes puis rafraîchir
      if (el.type === 'radio') {{
        applyAllConstraints();
        refreshMetricSources(sources);
      }}
      computeDenominators();
    }});
  }});

  computeDenominators();
}}

// ── Onglet institutions ────────────────────────────────────────────────────
function updateInstitution() {{
  const inst = document.getElementById('sel-institution').value;
  setChartSexMode(CURRENT_CHART_SEX_MODE, inst);
  setTableSexMode(CURRENT_TABLE_SEX_MODE, inst);
  renderCriteriaOptions(inst);
  renderRegimeDescription(inst, []);
  initGraphSeriesFilters(
    'charts-institution',
    'filters-institution',
    'Régimes',
    selected => renderRegimeDescription(inst, selected),
    () => applyRegimeQuickFilter()  // Appeler le filtre une fois les graphiques prêts
  );
  document.getElementById('title-institution').textContent =
    'Évolution par régime — ' + inst;
  // Relancer plotly sur les divs injectés
  window.dispatchEvent(new Event('resize'));
}}

let CURRENT_TABLE_SEX_MODE = 'all';
let CURRENT_CHART_SEX_MODE = 'all';

function getTableHtml(inst, mode) {{
  const data = TABLES_INST[inst] || {{}};
  return data[mode] || data.all || '<p style="color:#888;padding:10px">Aucune donnée détaillée disponible.</p>';
}}

function getChartHtml(inst, mode) {{
  const data = CHARTS_INST[inst] || {{}};
  return data[mode] || data.all || '<p style="color:#888;padding:10px">Aucune donnée graphique disponible.</p>';
}}

function syncChartModeButtons(mode) {{
  document.querySelectorAll('#chart-mode-toggle .chart-mode-btn').forEach(btn => {{
    btn.classList.toggle('active', btn.getAttribute('data-sex-mode') === mode);
  }});
}}

function syncTableModeButtons(mode) {{
  document.querySelectorAll('#table-mode-toggle .table-mode-btn').forEach(btn => {{
    btn.classList.toggle('active', btn.getAttribute('data-sex-mode') === mode);
  }});
}}

function setChartSexMode(mode, instOverride) {{
  const modeValue = (mode === 'hommes' || mode === 'femmes') ? mode : 'all';
  CURRENT_CHART_SEX_MODE = modeValue;
  const inst = instOverride || document.getElementById('sel-institution').value;
  injectHtmlAndRunScripts('charts-institution', getChartHtml(inst, modeValue));
  syncChartModeButtons(modeValue);
  // Reconstruire les filtres de séries sur le nouveau graphique injecté
  initGraphSeriesFilters(
    'charts-institution',
    'filters-institution',
    'Régimes',
    selected => renderRegimeDescription(inst, selected),
    () => applyRegimeQuickFilter()
  );
  window.dispatchEvent(new Event('resize'));
}}

function setTableSexMode(mode, instOverride) {{
  const modeValue = (mode === 'hommes' || mode === 'femmes') ? mode : 'all';
  CURRENT_TABLE_SEX_MODE = modeValue;
  const inst = instOverride || document.getElementById('sel-institution').value;
  injectHtmlAndRunScripts('table-institution', getTableHtml(inst, modeValue));
  initColumnFilters('table-institution');
  syncTableModeButtons(modeValue);
}}

function applyRegimeQuickFilter() {{
  const instSel = document.getElementById('sel-institution');
  const filtersHost = document.getElementById('filters-institution');
  const criteriaHost = document.getElementById('criteria-options');
  if (!instSel || !filtersHost || !criteriaHost) return;
  const inst = instSel.value;
  const selectedCriteria = getSelectedCriteriaMap();
  const inputs = Array.from(filtersHost.querySelectorAll('input[type=\"checkbox\"]'));
  const metaMap = REGIME_META[inst] || {{}};

  updateCriteriaSummary(selectedCriteria);

  if (!Object.keys(selectedCriteria).length) {{
    inputs.forEach(cb => {{
      cb.checked = true;
    }});
    if (filtersHost._setLocked) filtersHost._setLocked(false);
    if (filtersHost._applySeriesFilter) filtersHost._applySeriesFilter();
    return;
  }}

  const selected = [];
  Object.keys(metaMap).forEach(rc => {{
    const meta = getLatestRegimeVersion(inst, rc);
    const matched = regimeMatchesCriteria(meta, selectedCriteria);
    if (matched) selected.push(rc);
  }});

  inputs.forEach(cb => {{
    cb.checked = selected.indexOf(cb.value) !== -1;
  }});
  if (filtersHost._applySeriesFilter) filtersHost._applySeriesFilter();
}}

// ── Onglet prestations ─────────────────────────────────────────────────────
let CURRENT_TABLE_PREST_SEX_MODE = 'all';
let CURRENT_CHART_REGIME_PREST_SEX_MODE = 'all';
let CURRENT_PREST_REGIME = null;

function getPrestationMetaData(inst, rc, prest_name) {{
  const instData = PRESTATION_META[inst] || {{}};
  const rcData = instData[rc] || {{}};
  return rcData[prest_name] || null;
}}

function getChartRegimePrestHtml(inst, rc, mode) {{
  const instData = CHARTS_PREST[inst] || {{}};
  const regimeData = instData["_regime"] || {{}};
  const rcData = regimeData[rc] || {{}};
  return rcData[mode] || rcData.all || '<p style="color:#888;padding:10px">Aucune donnée de régime disponible.</p>';
}}

function getTablePrestHtml(inst, rc, mode) {{
  const instData = TABLES_PREST[inst] || {{}};
  const rcData = instData[rc] || {{}};
  return rcData[mode] || rcData.all || '<p style="color:#888;padding:10px">Aucune donnée détaillée disponible.</p>';
}}

function syncChartRegimePrestModeButtons(mode) {{
  document.querySelectorAll('#chart-mode-regime-prest-toggle .chart-mode-btn').forEach(btn => {{
    btn.classList.toggle('active', btn.getAttribute('data-sex-mode') === mode);
  }});
}}

function syncTablePrestModeButtons(mode) {{
  document.querySelectorAll('#table-mode-prest-toggle .table-mode-btn').forEach(btn => {{
    btn.classList.toggle('active', btn.getAttribute('data-sex-mode') === mode);
  }});
}}

function setChartRegimePrestSexMode(mode, instOverride, rcOverride) {{
  const modeValue = (mode === 'hommes' || mode === 'femmes') ? mode : 'all';
  CURRENT_CHART_REGIME_PREST_SEX_MODE = modeValue;
  const inst = instOverride || document.getElementById('sel-prest-inst').value;
  const rc = rcOverride || document.getElementById('sel-prest-regime').value;
  injectHtmlAndRunScripts('charts-regime-prestations', getChartRegimePrestHtml(inst, rc, modeValue));
  syncChartRegimePrestModeButtons(modeValue);
  // Connecter les filtres de séries au nouveau graphique prestation
  initGraphSeriesFilters(
    'charts-regime-prestations',
    'filters-regime-prestations',
    'Prestations',
    null,
    () => applyPrestationQuickFilter()
  );
  window.dispatchEvent(new Event('resize'));
}}

function setTablePrestSexMode(mode, instOverride, rcOverride) {{
  const modeValue = (mode === 'hommes' || mode === 'femmes') ? mode : 'all';
  CURRENT_TABLE_PREST_SEX_MODE = modeValue;
  const inst = instOverride || document.getElementById('sel-prest-inst').value;
  const rc = rcOverride || document.getElementById('sel-prest-regime').value;
  injectHtmlAndRunScripts('table-prestations', getTablePrestHtml(inst, rc, modeValue));
  initColumnFilters('table-prestations');
  syncTablePrestModeButtons(modeValue);
}}

function makePrestationCard(inst, rc, prest_name, activeIndex) {{
  const data = getPrestationMetaData(inst, rc, prest_name);
  const versions = data ? (data.selector_versions || []) : [];
  if (!versions.length) {{
    return '<div class="regime-card"><p class="regime-card-title">' + escapeHtml(prest_name) + '</p><p class="empty">Description indisponible.</p></div>';
  }}
  
  const idx = (activeIndex >= 0 && activeIndex < versions.length) ? activeIndex : 0;
  const meta = versions[idx];
  const varied = new Set((data && data.variation_fields) || []);
  const asText = (val) => (val === null || val === undefined || String(val).trim() === '' || String(val) === 'None')
    ? 'Non renseigné'
    : String(val);
  
  // Utiliser les années ESS réelles
  const essYears = (data && data.ess_years) || [];
  const yearsDisplay = essYears.length ? essYears.join(', ') : 'Non renseigné';
  
  const otherButtons = versions.map((v, i) =>
    '<button type="button" class="regime-version-btn' + (i === idx ? ' active' : '') + '" onclick="switchPrestationVersion(' +
      JSON.stringify(inst) + ',' + JSON.stringify(rc) + ',' + JSON.stringify(prest_name) + ',' + i + ')">' + escapeHtml(asText(v.annee)) + '</button>'
  ).join('');
  
  const otherLine = versions.length > 1
    ? '<div class="regime-version-row"><span class="k">Années de référence</span>' + otherButtons + '</div>'
    : '';
  
  const field = (label, value, key) => (
    '<div class="k">' + escapeHtml(label) + '</div>' +
    '<div class="v' + (varied.has(key) ? ' varied' : '') + '">' + escapeHtml(asText(value)) + '</div>'
  );
  
  return (
    '<div class="regime-card" data-inst="' + escapeHtml(inst) + '" data-rc="' + escapeHtml(rc) + '" data-prest="' + escapeHtml(prest_name) + '" data-active-index="' + idx + '">' +
      '<p class="regime-card-title">' +
        '<span>' + escapeHtml(prest_name) + '</span>' +
        '<span class="regime-year-chip">' + escapeHtml(asText(meta.annee)) + '</span>' +
      '</p>' +
      '<div class="regime-grid">' +
        field('Institution', inst, 'institution') +
        field('Régime', NOM_COURT[rc] || rc, 'regime') +
        field('Nom prestation', prest_name, 'nom_fr') +
        field('Années disponibles', yearsDisplay, 'available_years') +
        field('Fonction OIT', meta.fonction_oit, 'fonction_oit') +
        field('Type de paiement', meta.type_paiement, 'type_paiement') +
        field('Périodicité', meta.periodicite, 'periodicite') +
        field('Groupe de population', meta.groupe_population, 'groupe_population') +
        field('Groupe d\\'âge', meta.groupe_age, 'groupe_age') +
        field('Zone géographique', meta.zone_geo, 'zone_geo') +
        field('Type de financement', meta.type_financement, 'type_financement') +
        field('Critère d\\'éligibilité', meta.critere_eligibilite, 'critere_eligibilite') +
        field('Âge légal hommes', meta.age_legal_h, 'age_legal_h') +
        field('Âge légal femmes', meta.age_legal_f, 'age_legal_f') +
        field('Durée service requise', meta.duree_service_requise, 'duree_service_requise') +
      '</div>' +
      otherLine +
    '</div>'
  );
}}

function switchPrestationVersion(inst, rc, prest_name, idx) {{
  const container = document.getElementById('prestation-description');
  if (!container) return;
  const card = container.querySelector('[data-inst="' + inst + '"][data-rc="' + rc + '"][data-prest="' + prest_name + '"]');
  if (!card) return;
  card.outerHTML = makePrestationCard(inst, rc, prest_name, idx);
}}

function renderPrestationDescription(inst, rc, selected) {{
  const host = document.getElementById('prestation-description');
  if (!host) return;
  const selectedList = selected || [];
  if (!selectedList.length) {{
    host.innerHTML = '<p class="empty">Aucune prestation sélectionnée.</p>';
    return;
  }}
  
  const cards = [];
  const prestMetaInst = PRESTATION_META[inst] || {{}};
  const prestMap = prestMetaInst[rc] || {{}};
  
  // Itérer sur les prestations du régime sélectionné
  Object.keys(prestMap).forEach(prest_name => {{
    // Filtrer selon la sélection (si applicable)
    if (selectedList.includes(prest_name)) {{
      cards.push(makePrestationCard(inst, rc, prest_name, 0));
    }}
  }});
  
  host.innerHTML = '<div class="regime-list">' + cards.join('') + '</div>';
}}

function buildPrestationCatalog(inst, rc) {{
  const prestMetaInst = PRESTATION_META[inst] || {{}};
  const prestMap = prestMetaInst[rc] || {{}};
  
  const catalog = {{
    nom_prestation: [],
    fonction_oit: [],
    type_paiement: [],
    periodicite: [],
    groupe_population: [],
    groupe_age: [],
    zone_geo: [],
    type_financement: [],
    critere_eligibilite: []
  }};
  
  Object.keys(prestMap).forEach(prest_name => {{
    const data = prestMap[prest_name];
    const versions = (data && data.selector_versions) || [];
    if (!versions.length) return;
    
    // Utiliser la version la plus récente (dernière dans le tableau)
    const meta = versions[versions.length - 1];
    
    // Nom prestation
    if (prest_name && !catalog.nom_prestation.includes(prest_name)) {{
      catalog.nom_prestation.push(prest_name);
    }}
    
    // Fonction OIT
    const func = meta.fonction_oit;
    if (func && func !== 'None' && !catalog.fonction_oit.includes(func)) {{
      catalog.fonction_oit.push(func);
    }}
    
    // Type paiement
    const typePaie = meta.type_paiement;
    if (typePaie && typePaie !== 'None' && !catalog.type_paiement.includes(typePaie)) {{
      catalog.type_paiement.push(typePaie);
    }}
    
    // Périodicité
    const period = meta.periodicite;
    if (period && period !== 'None' && !catalog.periodicite.includes(period)) {{
      catalog.periodicite.push(period);
    }}
    
    // Groupe population
    const grpPop = meta.groupe_population;
    if (grpPop && grpPop !== 'None' && !catalog.groupe_population.includes(grpPop)) {{
      catalog.groupe_population.push(grpPop);
    }}
    
    // Groupe âge
    const grpAge = meta.groupe_age;
    if (grpAge && grpAge !== 'None' && !catalog.groupe_age.includes(grpAge)) {{
      catalog.groupe_age.push(grpAge);
    }}
    
    // Zone géo
    const zone = meta.zone_geo;
    if (zone && zone !== 'None' && !catalog.zone_geo.includes(zone)) {{
      catalog.zone_geo.push(zone);
    }}
    
    // Type financement
    const typeFin = meta.type_financement;
    if (typeFin && typeFin !== 'None' && !catalog.type_financement.includes(typeFin)) {{
      catalog.type_financement.push(typeFin);
    }}
    
    // Critère éligibilité
    const critElig = meta.critere_eligibilite;
    if (critElig && critElig !== 'None' && !catalog.critere_eligibilite.includes(critElig)) {{
      catalog.critere_eligibilite.push(critElig);
    }}
  }});
  
  // Trier tous les catalogues
  Object.keys(catalog).forEach(key => {{
    catalog[key].sort();
  }});
  
  return catalog;
}}

function renderPrestationCriteriaOptions(inst, rc) {{
  const host = document.getElementById('criteria-prest-options');
  if (!host) return;

  const catalog = buildPrestationCatalog(inst, rc);

  // Section 1 : Sélection directe par nom de prestation
  const nameSection = catalog.nom_prestation.length ? (
    '<div class="criteria-section">' +
      '<div class="criteria-section-title">Sélection directe</div>' +
      '<div class="criteria-group" data-section="name">' +
        '<div class="criteria-group-title">Nom de la prestation</div>' +
        '<div class="criteria-group-items">' +
          catalog.nom_prestation.map(name => (
            '<label class="criteria-option">' +
              '<input type="checkbox" data-section="name" data-field="nom_prestation" data-value="' + escapeHtml(name) + '" checked>' +
              '<span>' + escapeHtml(name) + '</span>' +
            '</label>'
          )).join('') +
        '</div>' +
      '</div>' +
    '</div>'
  ) : '';

  // Section 2 : Filtrage par critères
  const criteriaFields = [
    {{ key: 'fonction_oit',        label: 'Fonction OIT',            is_multi: true }},
    {{ key: 'type_paiement',       label: 'Type de paiement',        is_multi: false }},
    {{ key: 'periodicite',         label: 'Périodicité',             is_multi: false }},
    {{ key: 'groupe_population',   label: 'Groupe de population',    is_multi: false }},
    {{ key: 'groupe_age',          label: "Groupe d'âge",            is_multi: false }},
    {{ key: 'zone_geo',            label: 'Zone géographique',       is_multi: false }},
    {{ key: 'type_financement',    label: 'Type de financement',     is_multi: false }},
    {{ key: 'critere_eligibilite', label: "Critère d'éligibilité",   is_multi: false }},
  ];

  const criteriaGroups = criteriaFields
    .map(f => ({{ ...f, values: catalog[f.key] || [] }}))
    .filter(f => f.values.length > 0);

  const criteriaSection = criteriaGroups.length ? (
    '<div class="criteria-section">' +
      '<div class="criteria-section-title">Filtrage par critères</div>' +
      criteriaGroups.map(group => (
        '<div class="criteria-group" data-section="criteria" data-field="' + escapeHtml(group.key) + '">' +
          '<div class="criteria-group-title">' + escapeHtml(group.label) + '</div>' +
          '<div class="criteria-group-items">' +
            group.values.map(value => (
              '<label class="criteria-option">' +
                (group.is_multi
                  ? '<input type="checkbox" data-section="criteria" data-field="' + escapeHtml(group.key) + '" data-value="' + escapeHtml(value) + '">'
                  : '<input type="radio"    data-section="criteria" name="prest-criteria-' + escapeHtml(group.key) + '" data-field="' + escapeHtml(group.key) + '" data-value="' + escapeHtml(value) + '">') +
                '<span>' + escapeHtml(value) + '</span>' +
              '</label>'
            )).join('') +
          '</div>' +
        '</div>'
      )).join('') +
    '</div>'
  ) : '';

  const resetBtn = (nameSection || criteriaSection)
    ? '<div style="text-align:right;margin-top:10px;"><button type="button" id="criteria-prest-reset-btn" style="padding:4px 14px;font-size:0.82rem;border:1px solid #cbd5e0;border-radius:6px;background:#f7fafc;color:#4a5568;cursor:pointer;">&#x2715; Réinitialiser</button></div>'
    : '';

  host.innerHTML =
    nameSection +
    (nameSection && criteriaSection ? '<hr style="margin:16px 0;border:none;border-top:2px solid #e2e8f0;">' : '') +
    criteriaSection +
    resetBtn;

  // ── Logique d'exclusion mutuelle ──────────────────────────────────────────
  function enableSection(section, enabled) {{
    host.querySelectorAll('[data-section="' + section + '"] input').forEach(inp => {{
      inp.disabled = !enabled;
    }});
    host.querySelectorAll('[data-section="' + section + '"]').forEach(el => {{
      el.style.opacity = enabled ? '1' : '0.5';
      el.style.pointerEvents = enabled ? 'auto' : 'none';
    }});
  }}

  host.querySelectorAll('[data-section="name"] input[type="checkbox"]').forEach(cb => {{
    cb.addEventListener('change', function() {{
      const anyName = Array.from(host.querySelectorAll('[data-section="name"] input')).some(i => i.checked);
      if (anyName) {{
        host.querySelectorAll('[data-section="criteria"] input').forEach(i => {{ i.checked = false; }});
        enableSection('criteria', false);
      }} else {{
        enableSection('criteria', true);
      }}
      applyPrestationQuickFilter();
    }});
  }});

  host.querySelectorAll('[data-section="criteria"] input').forEach(inp => {{
    // Permettre la désélection des radios (re-clic)
    inp.addEventListener('mousedown', function() {{
      this.dataset.wasChecked = this.checked ? 'true' : 'false';
    }});
    inp.addEventListener('click', function() {{
      if (inp.type === 'radio' && this.dataset.wasChecked === 'true') {{
        this.checked = false;
        this.dataset.wasChecked = 'false';
        this.dispatchEvent(new Event('change', {{ bubbles: true }}));
      }}
    }});
    inp.addEventListener('change', function() {{
      const anyCriteria = Array.from(host.querySelectorAll('[data-section="criteria"] input')).some(i => i.checked);
      if (anyCriteria) {{
        host.querySelectorAll('[data-section="name"] input').forEach(i => {{ i.checked = false; }});
        enableSection('name', false);
      }} else {{
        enableSection('name', true);
      }}
      applyPrestationQuickFilter();
    }});
  }});

  // Bouton réinitialiser
  const resetButton = host.querySelector('#criteria-prest-reset-btn');
  if (resetButton) {{
    resetButton.addEventListener('click', function() {{
      host.querySelectorAll('input').forEach(inp => {{
        inp.checked = false;
        inp.disabled = false;
        inp.dataset.wasChecked = 'false';
      }});
      host.querySelectorAll('[data-section="name"] input[type="checkbox"]').forEach(cb => {{
        cb.checked = true;
      }});
      host.querySelectorAll('[data-section="criteria"] input').forEach(input => {{
        input.disabled = true;
      }});
      host.querySelectorAll('[data-section="name"], [data-section="criteria"]').forEach(el => {{
        el.style.opacity = '1';
        el.style.pointerEvents = 'auto';
      }});
      host.querySelectorAll('[data-section="criteria"]').forEach(el => {{
        el.style.opacity = '0.5';
        el.style.pointerEvents = 'none';
      }});
      applyPrestationQuickFilter();
    }});
  }}

  const dropdown = document.getElementById('criteria-prest-dropdown');
  if (dropdown && dropdown.dataset.bound !== '1') {{
    dropdown.addEventListener('toggle', function() {{
      if (!dropdown.open) applyPrestationQuickFilter();
    }});
    dropdown.dataset.bound = '1';
  }}

  host.querySelectorAll('[data-section="name"] input[type="checkbox"]').forEach(cb => {{
    cb.checked = true;
  }});
  host.querySelectorAll('[data-section="criteria"] input').forEach(input => {{
    input.disabled = true;
  }});
  host.querySelectorAll('[data-section="criteria"]').forEach(el => {{
    el.style.opacity = '0.5';
    el.style.pointerEvents = 'none';
  }});
  applyPrestationQuickFilter();
}}

function getSelectedPrestationCriteria() {{
  const host = document.getElementById('criteria-prest-options');
  if (!host) return {{}};

  const criteria = {{}};
  host.querySelectorAll('input:checked').forEach(input => {{
    const field = input.getAttribute('data-field');
    const value = input.getAttribute('data-value') || input.value;
    if (!field || !value) return;
    if (!criteria[field]) criteria[field] = [];
    criteria[field].push(value);
  }});

  return criteria;
}}

function prestationMatchesCriteria(inst, rc, prest_name, selectedCriteria) {{
  const data = getPrestationMetaData(inst, rc, prest_name);
  if (!data) return false;
  
  const fields = Object.keys(selectedCriteria || {{}});
  if (!fields.length) return true;
  
  // Utiliser la version la plus récente (dernière dans selector_versions)
  const versions = data.selector_versions || [];
  if (!versions.length) return false;
  const meta = versions[versions.length - 1];
  
  return fields.every(field => {{
    const wanted = selectedCriteria[field] || [];
    if (!wanted.length) return true;
    
    if (field === 'nom_prestation') {{
      return wanted.includes(prest_name);
    }} else {{
      const value = meta[field];
      return wanted.includes(value);
    }}
  }});
}}

function applyPrestationQuickFilter() {{
  const inst = document.getElementById('sel-prest-inst').value;
  const rc = document.getElementById('sel-prest-regime').value;
  const selectedCriteria = getSelectedPrestationCriteria();
  
  // Mettre à jour le résumé
  const summary = document.getElementById('criteria-prest-summary');
  if (summary) {{
    const count = Object.keys(selectedCriteria).reduce((sum, key) => sum + selectedCriteria[key].length, 0);
    if (count === 0) {{
      summary.textContent = 'Toutes les prestations';
    }} else {{
      summary.textContent = count + ' critère' + (count > 1 ? 's' : '') + ' sélectionné' + (count > 1 ? 's' : '');
    }}
  }}
  
  // Trouver les prestations qui correspondent aux critères
  const prestMetaInst = PRESTATION_META[inst] || {{}};
  const prestMap = prestMetaInst[rc] || {{}};
  const allPrestations = Object.keys(prestMap);
  const matched = !Object.keys(selectedCriteria).length
    ? allPrestations
    : allPrestations.filter(n => prestationMatchesCriteria(inst, rc, n, selectedCriteria));

  renderPrestationDescription(inst, rc, matched);

  // Synchroniser les séries Plotly avec la sélection
  const fpHost = document.getElementById('filters-regime-prestations');
  if (fpHost && fpHost._applySeriesFilterWithSelection) {{
    fpHost._applySeriesFilterWithSelection(matched);
  }}
}}

function updatePrestationRegimeOptions(inst) {{
  const sel = document.getElementById('sel-prest-regime');
  if (!sel) return;
  
  const prestMetaInst = PRESTATION_META[inst] || {{}};
  const regimes = Object.keys(prestMetaInst).sort();
  
  sel.innerHTML = regimes
    .map(rc => '<option value="' + rc + '">' + (NOM_COURT[rc] || rc) + '</option>')
    .join('');
  
  if (regimes.length > 0) {{
    sel.value = regimes[0];
    CURRENT_PREST_REGIME = regimes[0];
  }}
}}

function updatePrestationInstitution() {{
  const inst = document.getElementById('sel-prest-inst').value;
  updatePrestationRegimeOptions(inst);
  updatePrestationRegime();
}}

function updatePrestationRegime() {{
  const inst = document.getElementById('sel-prest-inst').value;
  const rc = document.getElementById('sel-prest-regime').value;
  CURRENT_PREST_REGIME = rc;
  
  setChartRegimePrestSexMode(CURRENT_CHART_REGIME_PREST_SEX_MODE, inst, rc);
  setTablePrestSexMode(CURRENT_TABLE_PREST_SEX_MODE, inst, rc);
  renderPrestationCriteriaOptions(inst, rc);
  applyPrestationQuickFilter();
  
  // Mettre à jour le titre
  document.getElementById('title-prestations-regime').textContent =
    'Évolution du régime — ' + inst + ' / ' + (NOM_COURT[rc] || rc);
  
  window.dispatchEvent(new Event('resize'));
}}

// ── Initialisation ─────────────────────────────────────────────────────────
(function() {{
  renderIndicateurs();
  initDenominatorPanel();
  updateInstitution();
  updatePrestationInstitution();
}})();
</script>

</body>
</html>"""


# ── Point d'entrée ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Tableau de bord protection sociale RDC")
    parser.add_argument("--out", help="Chemin HTML de sortie (défaut : 10_output/dashboard_regimes.html)")
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else OUT_DIR / "dashboard_regimes.html"

    if not DB_PATH.exists():
        sys.exit(f"Base introuvable : {DB_PATH}\nLancer d'abord : py 09_scripts/extraire_ess.py")

    print(f"  Lecture BDD : {DB_PATH.name}")
    regimes, prestations, regime_meta, prestation_meta = load_all(DB_PATH)
    print(f"  {len(regimes)} régimes × années | {len(prestations)} prestations × années")

    print("  Génération des graphiques…")
    html = build_html(regimes, prestations, regime_meta, prestation_meta)

    out_path.write_text(html, encoding="utf-8")
    size_kb = out_path.stat().st_size // 1024
    print(f"  OK Tableau de bord genere : {out_path}  ({size_kb} Ko)")
    print(f"    Navigateur : file:///{out_path.as_posix()}")
    print(f"    Serveur local : http://localhost:8765/dashboard")


if __name__ == "__main__":
    main()
