"""
visualiser_regimes.py
Tableau de bord interactif — Protection sociale RDC
Structure : 3 onglets
  1. Indicateurs      — placeholder (données démographiques à venir)
  2. Par institution  — sélecteur CNSS / CNSSAP, puis régimes de l'institution
  3. Par prestation   — sélecteur institution → régime → liste des prestations

Usage :
  py 09_scripts/visualiser_regimes.py
  py 09_scripts/visualiser_regimes.py --out chemin/custom.html
"""

import argparse
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
    "CNSS_R4":   "Régime 4",
    "CNSSAP_R1": "Régime de base",
    "CNSSAP_R2": "Réforme du transfert",
}
NOM_INSTITUTION = {
    "CNSS":   "Caisse Nationale de Sécurité Sociale (CNSS)",
    "CNSSAP": "Caisse Nationale de Sécurité Sociale des Agents Publics (CNSSAP)",
}


# ── Chargement données ────────────────────────────────────────────────────────
def load_all(db_path: Path) -> tuple[list[dict], list[dict]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    regimes = [dict(r) for r in conn.execute(
        "SELECT * FROM v_serie_temporelle_regimes ORDER BY institution, regime_code, annee"
    ).fetchall()]
    prestations = [dict(r) for r in conn.execute(
        "SELECT * FROM v_serie_temporelle_prestations ORDER BY institution, regime_code, nom_fr, annee"
    ).fetchall()]
    conn.close()
    return regimes, prestations


# ── Graphiques ────────────────────────────────────────────────────────────────
def fig_institution(rows: list[dict], institution: str) -> str:
    """4 graphiques pour une institution (cotisants, bénéf, dépenses, dép.moy)."""
    data = [r for r in rows if r["institution"] == institution]
    regimes_keys = sorted(set(r["regime_code"] for r in data))

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Cotisants actifs",
            "Bénéficiaires",
            "Dépenses de prestations (Mds CDF)",
            "Dépense moyenne par bénéficiaire (k CDF)",
        ),
        vertical_spacing=0.18,
        horizontal_spacing=0.10,
    )

    for key in regimes_keys:
        subset = [r for r in data if r["regime_code"] == key]
        subset.sort(key=lambda r: r["annee"])
        annees  = [r["annee"] for r in subset]
        color   = PALETTE_REGIME.get(key, "#666")
        label   = NOM_COURT.get(key, key)

        def trace(y_vals, row, col, fmt, unit, showleg=False):
            fig.add_trace(go.Scatter(
                x=annees, y=y_vals,
                name=label, legendgroup=key,
                showlegend=showleg,
                mode="lines+markers",
                line=dict(color=color, width=2.5),
                marker=dict(size=8),
                hovertemplate=f"%{{x}} — {label}<br>%{{y:{fmt}}} {unit}<extra></extra>",
            ), row=row, col=col)

        trace([r["cotisants_total"] for r in subset],                    1, 1, ",.0f", "cotisants", showleg=True)
        trace([r["beneficiaires_total"] for r in subset],                 1, 2, ",.0f", "bénéf.")
        trace([(r["depenses_prestations_cdf"] or 0) / 1e9 or None
               for r in subset],                                          2, 1, ".2f",  "Mds CDF")
        dep_moy = [(r["depense_moy_par_beneficiaire_cdf"] or 0) / 1e3 or None
                   for r in subset]
        trace(dep_moy,                                                    2, 2, ",.0f", "k CDF")

    fig.update_layout(
        title=dict(
            text=NOM_INSTITUTION.get(institution, institution),
            font=dict(size=16), x=0.5
        ),
        height=640,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.28,
            xanchor="center", x=0.5, font=dict(size=11),
        ),
        hovermode="x unified",
        plot_bgcolor="#f8f9fa",
        paper_bgcolor="white",
        margin=dict(t=70, b=130, l=55, r=30),
    )
    for c in [1, 2]:
        for rr in [1, 2]:
            fig.update_xaxes(tickformat="d", dtick=1, row=rr, col=c)

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


# ── Tableau récapitulatif ─────────────────────────────────────────────────────
def fig_table_regime(rows: list[dict], institution: str) -> str:
    data = [r for r in rows if r["institution"] == institution]
    headers = ["Régime", "Année", "Cotisants", "Bénéficiaires",
               "Dép. prestations (Mds CDF)", "Dép. moy./bénéf. (k CDF)"]
    cols = {h: [] for h in headers}
    for r in data:
        cols["Régime"].append(NOM_COURT.get(r["regime_code"], r["regime_code"]))
        cols["Année"].append(r["annee"])
        cols["Cotisants"].append(f"{r['cotisants_total']:,.0f}" if r["cotisants_total"] else "—")
        cols["Bénéficiaires"].append(f"{r['beneficiaires_total']:,.0f}" if r["beneficiaires_total"] else "—")
        dep = r["depenses_prestations_cdf"]
        cols["Dép. prestations (Mds CDF)"].append(f"{dep/1e9:.2f}" if dep else "—")
        moy = r["depense_moy_par_beneficiaire_cdf"]
        cols["Dép. moy./bénéf. (k CDF)"].append(f"{moy/1e3:,.0f}" if moy else "—")

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[f"<b>{h}</b>" for h in headers],
            fill_color="#1f4e79", font=dict(color="white", size=12),
            align="left", height=30,
        ),
        cells=dict(
            values=[cols[h] for h in headers],
            fill_color=[["#f0f4f8" if i % 2 == 0 else "white" for i in range(len(data))]],
            align="left", font=dict(size=11), height=25,
        ),
    )])
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=max(200, 50 + 27 * len(data)),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


# ── Assemblage HTML final ─────────────────────────────────────────────────────
def build_html(regimes: list[dict], prestations: list[dict]) -> str:
    institutions = sorted(set(r["institution"] for r in regimes))

    # Pré-générer tous les blocs graphiques (évite le recalcul JS)
    charts_institution = {}
    tables_institution = {}
    charts_prestations = {}

    for inst in institutions:
        charts_institution[inst] = fig_institution(regimes, inst)
        tables_institution[inst] = fig_table_regime(regimes, inst)
        charts_prestations[inst] = {}
        regime_codes = sorted(set(r["regime_code"] for r in regimes if r["institution"] == inst))
        for rc in regime_codes:
            charts_prestations[inst][rc] = fig_prestation(prestations, inst, rc)

    # Sérialiser pour JS
    charts_inst_json  = json.dumps(charts_institution)
    tables_inst_json  = json.dumps(tables_institution)
    charts_prest_json = json.dumps(charts_prestations)

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
    regimes_par_inst_json = json.dumps(regimes_par_inst)
    nom_court_json = json.dumps(NOM_COURT)

    import plotly.offline as plo
    plotlyjs = f'<script>{plo.get_plotlyjs()}</script>'

    note_sources = """
    <p class="note-source">
      <strong>Source :</strong> Enquête sur la Sécurité Sociale (ESS) OIT/BIT —
      CNSS 2019–2022, CNSSAP 2020–2022.<br>
      Les montants CNSSAP sont convertis depuis les Milliards CDF de l'ESS.
      Les bénéficiaires sans cotisants signifient que la variable n'était pas renseignée dans l'ESS.
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
    body    {{ font-family: Arial, sans-serif; margin: 0; background: #f4f6f9; color: #222; }}
    header  {{ background: #1f4e79; color: #fff; padding: 14px 32px; }}
    header h1 {{ margin: 0; font-size: 1.25em; font-weight: 600; }}
    header p  {{ margin: 4px 0 0; font-size: 0.82em; opacity: 0.8; }}

    /* Onglets */
    .tab-bar  {{ display: flex; background: #fff; border-bottom: 3px solid #1f4e79;
                 padding: 0 24px; gap: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.07); }}
    .tab-btn  {{ padding: 12px 24px; cursor: pointer; border: none; background: none;
                 font-size: 0.95em; font-weight: 600; color: #555; border-bottom: 3px solid transparent;
                 margin-bottom: -3px; transition: color .2s, border-color .2s; }}
    .tab-btn:hover   {{ color: #1f4e79; }}
    .tab-btn.active  {{ color: #1f4e79; border-bottom-color: #1f4e79; }}
    .tab-btn.disabled{{ color: #bbb; cursor: default; }}
    .tab-panel {{ display: none; padding: 24px 32px; }}
    .tab-panel.active {{ display: block; }}

    /* Sélecteurs */
    .selector-bar {{ display: flex; align-items: center; gap: 16px;
                     background: #fff; border-radius: 8px; padding: 14px 20px;
                     margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
    .selector-bar label {{ font-weight: 600; font-size: 0.9em; color: #1f4e79; white-space: nowrap; }}
    .selector-bar select {{ padding: 6px 12px; border: 1px solid #c5d3e0; border-radius: 5px;
                            font-size: 0.92em; background: #f8fafc; cursor: pointer; }}

    /* Placeholder */
    .placeholder {{ background: #fff; border-radius: 10px; padding: 48px 32px; text-align: center;
                    box-shadow: 0 1px 4px rgba(0,0,0,0.07); color: #666; }}
    .placeholder .icon {{ font-size: 3em; margin-bottom: 12px; }}
    .placeholder h2 {{ color: #1f4e79; margin: 0 0 8px; }}
    .placeholder p  {{ max-width: 500px; margin: 0 auto; line-height: 1.6; }}
    .badge-soon {{ display: inline-block; background: #fff3cd; color: #856404;
                   border: 1px solid #ffc107; border-radius: 12px; padding: 3px 12px;
                   font-size: 0.8em; font-weight: 600; margin-top: 16px; }}

    /* Contenu graphiques */
    .chart-block {{ background: #fff; border-radius: 10px; padding: 16px;
                    box-shadow: 0 1px 4px rgba(0,0,0,0.07); margin-bottom: 20px; }}
    .chart-block h3 {{ margin: 0 0 12px; font-size: 1em; color: #1f4e79;
                       border-left: 4px solid #1f4e79; padding-left: 10px; }}
    .note-source {{ font-size: 0.8em; color: #777; margin-top: 12px;
                    padding: 10px 16px; background: #f8f9fa; border-radius: 6px;
                    border-left: 3px solid #c5d3e0; }}
  </style>
</head>
<body>

<header>
  <h1>Tableau de bord — Protection sociale en RDC</h1>
  <p>CNSS (2019–2022) &nbsp;·&nbsp; CNSSAP (2020–2022) &nbsp;·&nbsp; Source : ESS OIT/BIT</p>
</header>

<!-- Barre d'onglets -->
<div class="tab-bar">
  <button class="tab-btn disabled" title="En attente des données démographiques">
    📊 Indicateurs <span style="font-size:0.75em;color:#bbb">(à venir)</span>
  </button>
  <button class="tab-btn active" onclick="switchTab('institutions', this)">
    🏛 Par institution
  </button>
  <button class="tab-btn" onclick="switchTab('prestations', this)">
    📋 Par prestation
  </button>
</div>

<!-- ═══ ONGLET 1 : INDICATEURS (placeholder) ═══ -->
<div id="tab-indicateurs" class="tab-panel">
  <div class="placeholder">
    <div class="icon">📊</div>
    <h2>Indicateurs de couverture</h2>
    <p>
      Cet onglet affichera les indicateurs de couverture effective
      (taux de couverture par rapport à la population active, aux personnes âgées, etc.)
      dès que les données démographiques de référence seront intégrées.
    </p>
    <div class="badge-soon">En cours de préparation</div>
  </div>
</div>

<!-- ═══ ONGLET 2 : PAR INSTITUTION ═══ -->
<div id="tab-institutions" class="tab-panel active">
  <div class="selector-bar">
    <label for="sel-institution">Institution :</label>
    <select id="sel-institution" onchange="updateInstitution()">
      {inst_options}
    </select>
  </div>
  <div id="block-charts-institution" class="chart-block">
    <h3 id="title-institution">Évolution par régime</h3>
    <div id="charts-institution"></div>
  </div>
  <div id="block-table-institution" class="chart-block">
    <h3>Données détaillées</h3>
    <div id="table-institution"></div>
    {note_sources}
  </div>
</div>

<!-- ═══ ONGLET 3 : PAR PRESTATION ═══ -->
<div id="tab-prestations" class="tab-panel">
  <div class="selector-bar">
    <label for="sel-prest-inst">Institution :</label>
    <select id="sel-prest-inst" onchange="updateRegimeOptions()">
      {inst_options}
    </select>
    <label for="sel-prest-regime">Régime :</label>
    <select id="sel-prest-regime" onchange="updatePrestations()"></select>
  </div>
  <div id="block-charts-prestations" class="chart-block">
    <h3 id="title-prestations">Prestations</h3>
    <div id="charts-prestations"></div>
    {note_sources}
  </div>
</div>

<script>
// ── Données pré-calculées ──────────────────────────────────────────────────
const CHARTS_INST  = {charts_inst_json};
const TABLES_INST  = {tables_inst_json};
const CHARTS_PREST = {charts_prest_json};
const REGIMES_INST = {regimes_par_inst_json};
const NOM_COURT    = {nom_court_json};

// ── Navigation onglets ─────────────────────────────────────────────────────
function switchTab(name, btn) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn:not(.disabled)').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  if (btn) btn.classList.add('active');
}}

// ── Onglet institutions ────────────────────────────────────────────────────
function updateInstitution() {{
  const inst = document.getElementById('sel-institution').value;
  document.getElementById('charts-institution').innerHTML = CHARTS_INST[inst] || '';
  document.getElementById('table-institution').innerHTML  = TABLES_INST[inst] || '';
  document.getElementById('title-institution').textContent =
    'Évolution par régime — ' + inst;
  // Relancer plotly sur les divs injectés
  window.dispatchEvent(new Event('resize'));
}}

// ── Onglet prestations ─────────────────────────────────────────────────────
function updateRegimeOptions() {{
  const inst = document.getElementById('sel-prest-inst').value;
  const sel  = document.getElementById('sel-prest-regime');
  sel.innerHTML = (REGIMES_INST[inst] || [])
    .map(rc => `<option value="${{rc}}">${{NOM_COURT[rc] || rc}}</option>`)
    .join('');
  updatePrestations();
}}

function updatePrestations() {{
  const inst = document.getElementById('sel-prest-inst').value;
  const rc   = document.getElementById('sel-prest-regime').value;
  const html = (CHARTS_PREST[inst] || {{}})[rc] || '<p style="color:#888">Aucune donnée.</p>';
  document.getElementById('charts-prestations').innerHTML = html;
  document.getElementById('title-prestations').textContent =
    'Prestations — ' + inst + ' / ' + (NOM_COURT[rc] || rc);
  window.dispatchEvent(new Event('resize'));
}}

// ── Initialisation ─────────────────────────────────────────────────────────
(function() {{
  updateInstitution();
  updateRegimeOptions();
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
    regimes, prestations = load_all(DB_PATH)
    print(f"  {len(regimes)} régimes × années | {len(prestations)} prestations × années")

    print("  Génération des graphiques…")
    html = build_html(regimes, prestations)

    out_path.write_text(html, encoding="utf-8")
    size_kb = out_path.stat().st_size // 1024
    print(f"  ✓ Tableau de bord généré : {out_path}  ({size_kb} Ko)")
    print(f"    Navigateur : file:///{out_path.as_posix()}")
    print(f"    Serveur local : http://localhost:8765/dashboard")


if __name__ == "__main__":
    main()
