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
import unicodedata
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

ODD_INDICATORS = [
    {"key": "global_131", "label": "ODD 1.3.1 — Global", "branches": []},
    {"key": "ind_22_enfants", "label": "2.2 Enfants", "branches": ["enfants_famille"]},
    {"key": "ind_23_maternite", "label": "2.3 Maternité", "branches": ["maternite"]},
    {"key": "ind_24_handicap", "label": "2.4 Handicap / invalidité", "branches": ["invalidite"]},
    {"key": "ind_25_atmp", "label": "2.5 AT/MP", "branches": ["at_mp"]},
    {"key": "ind_26_chomage", "label": "2.6 Chômage", "branches": []},
    {"key": "ind_27_vieillesse", "label": "2.7 Vieillesse", "branches": ["vieillesse"]},
    {"key": "ind_28_vulnerables", "label": "2.8 Vulnérables / assistance", "branches": ["enfants_famille", "autres"]},
    {"key": "ind_29_cotisants", "label": "2.9 Cotisants actifs retraite", "branches": ["vieillesse", "invalidite", "survivants"]},
]
ODD_INDICATOR_KEYS = [item["key"] for item in ODD_INDICATORS]
def _propose_regime_status(regime_code: str, nom_regime: str, fonctions: list[str]) -> tuple[str, str]:
    text = " ".join([regime_code or "", nom_regime or "", " ".join(fonctions or [])]).lower()
    if "sanitaire" in text or "sante" in text:
        return (
            "exclu_nature",
            "Fonction principalement hors champ ODD 1.3.1 (composante sanitaire/non cash dominante).",
        )
    if regime_code == "CNSSAP_R2":
        return (
            "inclus_avec_reserve",
            "Régime public pertinent pour la vieillesse/survivants, mais transition institutionnelle à documenter.",
        )
    return (
        "inclus",
        "Régime statutaire CNSS/CNSSAP avec prestations en espèces alignées sur ODD 1.3.1.",
    )



def _supported_indicators_from_branches(branch_keys: list[str], has_cotisants: bool = False) -> set[str]:
    supported = {"global_131"}
    bset = set(branch_keys or [])
    if "enfants_famille" in bset:
        supported.add("ind_22_enfants")
    if "maternite" in bset:
        supported.add("ind_23_maternite")
    if "invalidite" in bset:
        supported.add("ind_24_handicap")
    if "at_mp" in bset:
        supported.add("ind_25_atmp")
    if "vieillesse" in bset:
        supported.add("ind_27_vieillesse")
    if "enfants_famille" in bset or "autres" in bset:
        supported.add("ind_28_vulnerables")
    if has_cotisants:
        supported.add("ind_29_cotisants")
    return supported


def _build_status_maps(supported: set[str], base_status: str, base_rationale: str, non_support_reason: str) -> tuple[dict, dict]:
    propositions = {}
    rationales = {}
    for indicator_key in ODD_INDICATOR_KEYS:
        if indicator_key in supported:
            propositions[indicator_key] = base_status
            rationales[indicator_key] = base_rationale
        elif indicator_key == "ind_26_chomage":
            propositions[indicator_key] = "exclu_hors_indicateur"
            rationales[indicator_key] = "Aucun régime d'assurance chômage opérationnel n'est identifié dans les ESS."
        else:
            propositions[indicator_key] = "exclu_hors_indicateur"
            rationales[indicator_key] = non_support_reason
    return propositions, rationales


def build_odd_programmes_payload(regimes: list[dict], prestations: list[dict], regime_meta: dict, prestation_meta: dict) -> list[dict]:
    records = []
    regime_seen = set()
    has_cotisants = {}
    regime_nodes = {}
    institution_nodes = {}
    prestation_nodes = []

    for row in regimes:
        inst = row.get("institution")
        rc = row.get("regime_code")
        if not inst or not rc:
            continue
        key = (inst, rc)
        has_cotisants[key] = has_cotisants.get(key, False) or float(row.get("cotisants_total") or 0) > 0

    for row in regimes:
        inst = row.get("institution")
        rc = row.get("regime_code")
        if not inst or not rc:
            continue
        key = (inst, rc)
        if key in regime_seen:
            continue
        regime_seen.add(key)

        meta = ((regime_meta.get(inst) or {}).get(rc) or {})
        versions = meta.get("versions") or []
        latest = versions[-1] if versions else {}
        nom_regime = latest.get("nom_regime") or row.get("nom_fr") or NOM_COURT.get(rc, rc)
        fonctions = latest.get("fonctions_oit") if isinstance(latest.get("fonctions_oit"), list) else []
        financement = (latest.get("type_financement") or "").strip()
        caractere = (latest.get("caractere") or "").strip()
        proposition, rationale = _propose_regime_status(rc, nom_regime, fonctions)
        c1 = "Partiel" if proposition == "exclu_nature" else "Oui"
        c4 = "Oui" if "obligatoire" in caractere.lower() else ("Partiel" if caractere else "Partiel")
        c5 = "Oui" if financement else "Partiel"
        branch_keys = sorted(set(_map_function_to_branch(f) for f in fonctions if f))
        supported = _supported_indicators_from_branches(branch_keys, has_cotisants=has_cotisants.get((inst, rc), False))
        propositions, rationales = _build_status_maps(
            supported=supported,
            base_status=proposition,
            base_rationale=rationale,
            non_support_reason="Régime non pertinent pour ce sous-indicateur.",
        )

        regime_id = f"regime::{inst}::{rc}"
        regime_node = {
            "id": regime_id,
            "parent_id": f"institution::{inst}",
            "type": "regime_ess",
            "programme": nom_regime,
            "institution": inst,
            "regime_code": rc,
            "proposition": propositions.get("global_131", proposition),
            "rationale": rationales.get("global_131", rationale),
            "propositions": propositions,
            "rationales": rationales,
            "impact_numerateur": True,
            "criteria": {
                "c1_cash": c1,
                "c2_statutaire": "Oui",
                "c3_etat": "Oui",
                "c4_permanent": c4,
                "c5_financement": c5,
            },
        }
        regime_nodes[(inst, rc)] = regime_node

    prestation_seen = set()
    for row in prestations:
        inst = row.get("institution")
        rc = row.get("regime_code")
        nom_prest = (row.get("nom_fr") or "").strip()
        if not inst or not rc or not nom_prest:
            continue
        pkey = (inst, rc, nom_prest)
        if pkey in prestation_seen:
            continue
        prestation_seen.add(pkey)

        pmeta = (((prestation_meta.get(inst) or {}).get(rc) or {}).get(nom_prest) or {})
        pversions = pmeta.get("versions") or []
        latest_p = pversions[-1] if pversions else {}
        fonction_candidates = []
        if latest_p.get("fonction_oit"):
            fonction_candidates.append(latest_p.get("fonction_oit"))
        if row.get("fonction_oit"):
            fonction_candidates.append(row.get("fonction_oit"))
        branch_keys = sorted(set(_map_function_to_branch(v) for v in fonction_candidates if v))
        if not branch_keys:
            regime_fonctions = (((regime_meta.get(inst) or {}).get(rc) or {}).get("versions") or [])
            if regime_fonctions:
                regime_latest = regime_fonctions[-1]
                branch_keys = sorted(set(_map_function_to_branch(v) for v in (regime_latest.get("fonctions_oit") or [])))
        if not branch_keys:
            branch_keys = ["autres"]

        raw_payment = str(latest_p.get("type_paiement") or row.get("type_paiement") or "").lower()
        is_cash = ("esp" in unicodedata.normalize("NFKD", raw_payment).encode("ascii", "ignore").decode("ascii")) or (raw_payment == "")
        if is_cash:
            base_status = "inclus"
            base_rationale = "Prestation en espèces potentiellement contributive au sous-indicateur ciblé."
        else:
            base_status = "exclu_nature"
            base_rationale = "Prestation principalement en nature : hors périmètre cash de l'indicateur."
        supported = _supported_indicators_from_branches(branch_keys, has_cotisants=False)
        propositions, rationales = _build_status_maps(
            supported=supported,
            base_status=base_status,
            base_rationale=base_rationale,
            non_support_reason="Prestation non pertinente pour ce sous-indicateur.",
        )

        prestation_nodes.append({
            "id": f"prestation::{inst}::{rc}::{nom_prest}",
            "parent_id": f"regime::{inst}::{rc}",
            "type": "prestation_ess",
            "programme": nom_prest,
            "institution": inst,
            "regime_code": rc,
            "proposition": propositions.get("global_131", base_status),
            "rationale": rationales.get("global_131", base_rationale),
            "propositions": propositions,
            "rationales": rationales,
            "impact_numerateur": True,
            "criteria": None,
        })

    for (inst, _rc), _node in regime_nodes.items():
        institution_nodes.setdefault(inst, [])
        institution_nodes[inst].append(_node)

    for inst, children in institution_nodes.items():
        supported = set()
        for child in children:
            for key, val in (child.get("propositions") or {}).items():
                if val in ("inclus", "inclus_avec_reserve"):
                    supported.add(key)
        inst_props, inst_rats = _build_status_maps(
            supported=supported or {"global_131"},
            base_status="inclus",
            base_rationale="Institution contributive via au moins un régime/prestation relevant du sous-indicateur.",
            non_support_reason="Aucune composante institutionnelle pertinente pour ce sous-indicateur.",
        )
        records.append({
            "id": f"institution::{inst}",
            "parent_id": None,
            "type": "institution_ess",
            "programme": NOM_INSTITUTION.get(inst, inst),
            "institution": inst,
            "regime_code": "",
            "proposition": inst_props.get("global_131", "inclus"),
            "rationale": inst_rats.get("global_131", ""),
            "propositions": inst_props,
            "rationales": inst_rats,
            "impact_numerateur": True,
            "criteria": None,
        })

    records.extend(sorted(regime_nodes.values(), key=lambda x: (x.get("institution", ""), x.get("regime_code", ""))))
    records.extend(sorted(prestation_nodes, key=lambda x: (x.get("institution", ""), x.get("regime_code", ""), x.get("programme", ""))))

    return records


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
    """Graphiques population pour une institution (cotisants/bénéficiaires)."""
    data = [r for r in rows if r["institution"] == institution]
    regimes_keys = sorted(set(r["regime_code"] for r in data))

    sex_mode = sex_mode if sex_mode in ("all", "hommes", "femmes") else "all"
    sexe_cap = "Hommes" if sex_mode == "hommes" else "Femmes"
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Cotisants actifs" if sex_mode == "all" else f"Cotisants {sexe_cap}",
            "Bénéficiaires" if sex_mode == "all" else f"Bénéficiaires {sexe_cap}",
        ),
        horizontal_spacing=0.12,
    )

    for key in regimes_keys:
        subset = [r for r in data if r["regime_code"] == key]
        subset.sort(key=lambda r: r["annee"])
        annees  = [r["annee"] for r in subset]
        color   = PALETTE_REGIME.get(key, "#666")
        label   = NOM_COURT.get(key, key)

        def trace(y_vals, row, col, fmt, unit, showleg=False):
            import re as _re
            # stackgroup unique par sous-graphique pour aires cumulées
            sg = f"stack_r{row}_c{col}"
            # Couleur de remplissage semi-transparente dérivée de la couleur de ligne
            hex_c = color.lstrip("#")
            if len(hex_c) == 6:
                r_int = int(hex_c[0:2], 16)
                g_int = int(hex_c[2:4], 16)
                b_int = int(hex_c[4:6], 16)
                fill_color = f"rgba({r_int},{g_int},{b_int},0.18)"
            else:
                fill_color = color
            fig.add_trace(go.Scatter(
                x=annees, y=y_vals,
                name=label, legendgroup=key,
                showlegend=showleg,
                mode="lines+markers",
                stackgroup=sg,
                line=dict(color=color, width=2.5),
                fillcolor=fill_color,
                marker=dict(size=8, color=color, line=dict(width=2, color='white')),
                hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:{fmt}}} {unit}<extra></extra>",
            ), row=row, col=col)

        if sex_mode == "all":
            trace([r["cotisants_total"] for r in subset], 1, 1, ",.0f", "cotisants", showleg=True)
            trace([r["beneficiaires_total"] for r in subset], 1, 2, ",.0f", "bénéf.")
        else:
            sex_suffix = "h" if sex_mode == "hommes" else "f"
            trace([r["cotisants_" + sex_suffix] for r in subset], 1, 1, ",.0f", "cotisants", showleg=True)
            trace([r["beneficiaires_" + sex_suffix] for r in subset], 1, 2, ",.0f", "bénéf.")

    fig.update_layout(
        title=dict(
            text=NOM_INSTITUTION.get(institution, institution) + (
                " — Effectifs agrégés" if sex_mode == "all" else " — Effectifs agrégés (" + ("Hommes" if sex_mode == "hommes" else "Femmes") + ")"
            ),
            font=dict(
                size=18,
                family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                color='#2c5282',
                weight=700
            ),
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        height=460,
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=-0.18,
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
        margin=dict(t=80, b=72, l=70, r=40),
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


def fig_institution_finances(rows: list[dict], institution: str) -> str:
    """Graphiques financiers agrégés (mode Tous) pour une institution."""
    data = [r for r in rows if r["institution"] == institution]
    regimes_keys = sorted(set(r["regime_code"] for r in data))
    if not regimes_keys:
        return "<p style='color:#888;padding:12px'>Aucune donnée financière disponible.</p>"

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Dépenses totales (Mds CDF)",
            "Dépense moyenne par bénéficiaire (k CDF)",
            "Recettes totales (Mds CDF)",
            "Contribution moyenne (k CDF / cotisant)",
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.10,
    )

    for key in regimes_keys:
        subset = [r for r in data if r["regime_code"] == key]
        subset.sort(key=lambda r: r["annee"])
        annees = [r["annee"] for r in subset]
        color = PALETTE_REGIME.get(key, "#666")
        label = NOM_COURT.get(key, key)

        dep_tot = [
            (r["depenses_prestations_cdf"] / 1e9) if r["depenses_prestations_cdf"] is not None else None
            for r in subset
        ]
        dep_moy = [
            (r["depense_moy_par_beneficiaire_cdf"] / 1e3) if r["depense_moy_par_beneficiaire_cdf"] is not None else None
            for r in subset
        ]
        rec_tot = [
            (r["recettes_cdf"] / 1e9) if r["recettes_cdf"] is not None else None
            for r in subset
        ]
        contrib_moy = [
            ((r["recettes_cdf"] / r["cotisants_total"]) / 1e3)
            if (r["recettes_cdf"] is not None and r["cotisants_total"] not in (None, 0))
            else None
            for r in subset
        ]

        fig.add_trace(go.Bar(
            x=annees, y=dep_tot,
            name=label, legendgroup=key, showlegend=True,
            marker=dict(color=color, line=dict(width=0)),
            opacity=0.85,
            hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:.2f}} Mds CDF<extra></extra>",
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=annees, y=dep_moy,
            name=label, legendgroup=key, showlegend=False,
            mode="lines+markers",
            line=dict(color=color, width=3),
            marker=dict(size=8, line=dict(width=1.5, color='white')),
            hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:,.0f}} k CDF<extra></extra>",
        ), row=1, col=2)

        fig.add_trace(go.Bar(
            x=annees, y=rec_tot,
            name=label, legendgroup=key, showlegend=False,
            marker=dict(color=color, line=dict(width=0)),
            opacity=0.85,
            hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:.2f}} Mds CDF<extra></extra>",
        ), row=2, col=1)

        fig.add_trace(go.Scatter(
            x=annees, y=contrib_moy,
            name=label, legendgroup=key, showlegend=False,
            mode="lines+markers",
            line=dict(color=color, width=3),
            marker=dict(size=8, line=dict(width=1.5, color='white')),
            hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:,.0f}} k CDF<extra></extra>",
        ), row=2, col=2)

    fig.update_layout(
        title=dict(
            text=NOM_INSTITUTION.get(institution, institution) + " — Finances agrégées",
            font=dict(size=18, family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color='#2c5282', weight=700),
            x=0.5, xanchor='center', y=0.98, yanchor='top'
        ),
        height=650,
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.16, xanchor="center", x=0.5,
            font=dict(size=12, family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color='#4a5568'),
            bgcolor='rgba(247, 250, 252, 0.8)', bordercolor='#e2e8f0', borderwidth=1
        ),
        hovermode="x unified",
        barmode="relative",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(t=70, b=120, l=70, r=40),
        font=dict(family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', size=13, color='#4a5568'),
    )
    fig.update_annotations(font=dict(size=13, family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color='#2c5282'))
    for rr in [1, 2]:
        for c in [1, 2]:
            fig.update_xaxes(tickformat="d", dtick=1, row=rr, col=c, showgrid=True, gridcolor='#f0f0f0', showline=True, linewidth=1, linecolor='#e2e8f0')
            fig.update_yaxes(row=rr, col=c, showgrid=True, gridcolor='#f0f0f0', showline=True, linewidth=1, linecolor='#e2e8f0', separatethousands=True)
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


def fig_prestations_by_institution(
    rows: list,
    institution: str,
    regime_code: str,
    sex_mode: str = "all",
    regime_rows: list = None,
) -> str:
    """Graphiques 100 % par prestation (stackés) pour un régime donné.

    Mode 'all'  → 4 sous-graphiques :
        Couverture effective (cotisants) | Bénéficiaires
        Dépenses (Mds CDF)               | Montant unitaire (CDF)
    Mode H/F    → 2 sous-graphiques :
        Couverture H/F | Bénéficiaires H/F

    Toutes les séries = une barre par prestation, stackées par année.
    """
    prest_data = [r for r in rows if r["institution"] == institution and r["regime_code"] == regime_code]
    sex_mode = sex_mode if sex_mode in ("all", "hommes", "femmes") else "all"

    if not prest_data:
        return "<p style='color:#888;padding:20px'>Aucune donnée de prestation disponible.</p>"

    prestations_list = sorted(set(r["nom_fr"] for r in prest_data if r["nom_fr"]))
    if not prestations_list:
        return "<p style='color:#888;padding:20px'>Aucune prestation trouvée.</p>"

    annees = sorted(set(r["annee"] for r in prest_data))

    palette = [
        "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
        "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf",
        "#aec7e8","#ffbb78","#98df8a",
    ]

    label_inst   = NOM_INSTITUTION.get(institution, institution)
    label_regime = NOM_COURT.get(regime_code, regime_code)

    COMMON_AXIS = dict(
        showgrid=True, gridcolor='#f0f0f0', gridwidth=1,
        showline=True, linewidth=1, linecolor='#e2e8f0',
        tickfont=dict(size=12, color='#4a5568'),
    )
    COMMON_LAYOUT = dict(
        hovermode="x unified",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        barmode="stack",
        font=dict(
            family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            size=13, color='#4a5568',
        ),
    )

    def _hex_to_fill(hex_c, alpha=0.18):
        """Convertit un code hex en rgba semi-transparent pour le fill."""
        h = hex_c.lstrip("#")
        if len(h) == 6:
            r_int, g_int, b_int = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f"rgba({r_int},{g_int},{b_int},{alpha})"
        return hex_c

    def stacked_areas(fig, field_key, fmt, unit, row, col, scale=1.0, showlegend=True):
        """Aires empilées par prestation (Scatter+stackgroup) — même style que l'onglet institution."""
        sg = f"stack_r{row}_c{col}"
        for i, prest in enumerate(prestations_list):
            color = palette[i % len(palette)]
            fill_color = _hex_to_fill(color)
            subset = {r["annee"]: r for r in prest_data if r["nom_fr"] == prest}
            raw = [subset.get(a, {}).get(field_key) for a in annees]
            y_vals = [(v / scale) if v is not None else None for v in raw]
            fig.add_trace(go.Scatter(
                x=annees, y=y_vals,
                name=prest,
                legendgroup=prest,
                showlegend=(showlegend and row == 1 and col == 1),
                mode="lines+markers",
                stackgroup=sg,
                line=dict(color=color, width=2.5),
                fillcolor=fill_color,
                marker=dict(size=7, color=color, line=dict(width=1.5, color='white')),
                hovertemplate=f"<b>{prest}</b><br>%{{x}}<br>%{{y:{fmt}}} {unit}<extra></extra>",
            ), row=row, col=col)

    def stacked_bars(fig, field_key, fmt, unit, row, col, scale=1.0, showlegend=False):
        """Barres empilées par prestation — pour les données financières."""
        for i, prest in enumerate(prestations_list):
            color = palette[i % len(palette)]
            subset = {r["annee"]: r for r in prest_data if r["nom_fr"] == prest}
            raw = [subset.get(a, {}).get(field_key) for a in annees]
            y_vals = [(v / scale) if v is not None else None for v in raw]
            fig.add_trace(go.Bar(
                x=annees, y=y_vals,
                name=prest,
                legendgroup=prest,
                showlegend=showlegend,
                marker=dict(color=color, line=dict(width=0)),
                opacity=0.88,
                hovertemplate=f"<b>{prest}</b><br>%{{x}}<br>%{{y:{fmt}}} {unit}<extra></extra>",
            ), row=row, col=col)

    def unit_amount_lines(fig, row, col):
        """Montant unitaire — une ligne par prestation (pas de stack)."""
        for i, prest in enumerate(prestations_list):
            color = palette[i % len(palette)]
            subset = {r["annee"]: r for r in prest_data if r["nom_fr"] == prest}
            y_vals = [subset.get(a, {}).get("montant_unitaire_cdf") for a in annees]
            fig.add_trace(go.Scatter(
                x=annees, y=y_vals,
                name=prest, legendgroup=prest,
                showlegend=False,
                mode="lines+markers",
                line=dict(color=color, width=2.5),
                marker=dict(size=7, line=dict(width=1.5, color='white')),
                hovertemplate=f"<b>{prest}</b><br>%{{x}}<br>%{{y:,.0f}} CDF<extra></extra>",
            ), row=row, col=col)

    # ── Mode 'all' : 4 graphiques ────────────────────────────────────────────
    if sex_mode == "all":
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Cotisants actifs par prestation",
                "Bénéficiaires par prestation",
                "Dépenses par prestation (Mds CDF)",
                "Montant unitaire par prestation (CDF)",
            ),
            vertical_spacing=0.14,
            horizontal_spacing=0.10,
        )
        stacked_areas(fig, "couverture_effective_total", ",.0f", "cotisants actifs", row=1, col=1)
        stacked_areas(fig, "beneficiaires_total",        ",.0f", "bénéf.",     row=1, col=2, showlegend=False)
        stacked_bars( fig, "depenses_regime_cdf",        ".2f",  "Mds CDF",    row=2, col=1, scale=1e9)
        unit_amount_lines(fig, row=2, col=2)

        num_rows, num_cols = 2, 2

    # ── Mode sexué : 2 graphiques ────────────────────────────────────────────
    else:
        sexe_cap    = "Hommes" if sex_mode == "hommes" else "Femmes"
        sex_suffix  = "h"      if sex_mode == "hommes" else "f"
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                f"Cotisants actifs {sexe_cap} par prestation",
                f"Bénéficiaires {sexe_cap} par prestation",
            ),
            horizontal_spacing=0.12,
        )
        stacked_areas(fig, f"couverture_{sex_suffix}",    ",.0f", f"cotisants actifs {sexe_cap.lower()}", row=1, col=1, showlegend=True)
        stacked_areas(fig, f"beneficiaires_{sex_suffix}", ",.0f", f"bénéf. {sexe_cap.lower()}",   row=1, col=2, showlegend=False)
        num_rows, num_cols = 1, 2

    # ── Mise en forme commune ────────────────────────────────────────────────
    title_text = f"{label_inst} — {label_regime}"
    if sex_mode != "all":
        title_text += f" ({sexe_cap})"

    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(
                size=20,
                family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                color='#2c5282', weight=700,
            ),
            x=0.5, xanchor='center', y=0.98, yanchor='top',
        ),
        height=800 if sex_mode == "all" else 480,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.10 if sex_mode == "all" else -0.30,
            xanchor="center", x=0.5,
            font=dict(size=11, color='#4a5568'),
            bgcolor='rgba(247,250,252,0.8)', bordercolor='#e2e8f0', borderwidth=1,
        ),
        showlegend=True,
        **COMMON_LAYOUT,
        margin=dict(t=80, b=100, l=70, r=40),
    )
    for ri in range(1, num_rows + 1):
        for ci in range(1, num_cols + 1):
            fig.update_xaxes(tickformat="d", dtick=1, row=ri, col=ci, **COMMON_AXIS)
            fig.update_yaxes(row=ri, col=ci, **COMMON_AXIS)

    fig.update_annotations(
        font=dict(
            size=14,
            family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            color='#2c5282', weight=600,
        )
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)
    prest_data = [r for r in rows if r["institution"] == institution and r["regime_code"] == regime_code]
    sex_mode = sex_mode if sex_mode in ("all", "hommes", "femmes") else "all"

    if not prest_data:
        return "<p style='color:#888;padding:20px'>Aucune donnée de prestation disponible.</p>"

    prestations_list = sorted(set(r["nom_fr"] for r in prest_data if r["nom_fr"]))
    if not prestations_list:
        return "<p style='color:#888;padding:20px'>Aucune prestation trouvée.</p>"

    # Données régime pour cotisants et finances
    reg_data = []
    if regime_rows:
        reg_data = [r for r in regime_rows if r["institution"] == institution and r["regime_code"] == regime_code]
        reg_data.sort(key=lambda r: r["annee"])

    # Palette par prestation
    palette = [
        "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
        "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf",
        "#aec7e8","#ffbb78","#98df8a",
    ]

    label_inst = NOM_INSTITUTION.get(institution, institution)
    label_regime = NOM_COURT.get(regime_code, regime_code)
    color_regime = PALETTE_REGIME.get(regime_code, "#2c5282")

    # ── Mise en page selon le mode ──────────────────────────────────────────
    COMMON_AXIS = dict(
        showgrid=True, gridcolor='#f0f0f0', gridwidth=1,
        showline=True, linewidth=1, linecolor='#e2e8f0',
        tickfont=dict(size=12, color='#4a5568'),
    )
    COMMON_LAYOUT = dict(
        hovermode="x unified",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        barmode="stack",
        font=dict(
            family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            size=13, color='#4a5568'
        ),
    )

    if sex_mode == "all":
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                "Cotisants actifs",
                "Bénéficiaires par prestation",
                "Dépenses totales (Mds CDF)",
                "Dépense moy. / bénéficiaire (k CDF)",
                "Recettes totales (Mds CDF)",
                "Contribution moy. (k CDF / cotisant)",
            ),
            vertical_spacing=0.11,
            horizontal_spacing=0.10,
        )

        # (1,1) Cotisants actifs — ligne unique (régime)
        if reg_data:
            reg_annees = [r["annee"] for r in reg_data]
            fig.add_trace(go.Scatter(
                x=reg_annees,
                y=[r["cotisants_total"] for r in reg_data],
                name=label_regime, showlegend=False,
                mode="lines+markers",
                line=dict(color=color_regime, width=3),
                marker=dict(size=9, line=dict(width=2, color='white')),
                hovertemplate=f"<b>{label_regime}</b><br>%{{x}}<br>%{{y:,.0f}} cotisants<extra></extra>",
            ), row=1, col=1)

        # (1,2) Bénéficiaires par prestation — barres stackées
        annees_prest = sorted(set(r["annee"] for r in prest_data))
        for i, prest in enumerate(prestations_list):
            color = palette[i % len(palette)]
            subset = {r["annee"]: r for r in prest_data if r["nom_fr"] == prest}
            y_vals = [subset.get(a, {}).get("beneficiaires_total") for a in annees_prest]
            fig.add_trace(go.Bar(
                x=annees_prest, y=y_vals,
                name=prest, legendgroup=prest,
                marker=dict(color=color),
                hovertemplate=f"<b>{prest}</b><br>%{{x}}<br>%{{y:,.0f}} bénéf.<extra></extra>",
            ), row=1, col=2)

        # (2,1) Dépenses totales
        if reg_data:
            fig.add_trace(go.Bar(
                x=reg_annees,
                y=[(r["depenses_prestations_cdf"] / 1e9) if r["depenses_prestations_cdf"] is not None else None for r in reg_data],
                name=label_regime, showlegend=False,
                marker=dict(color=color_regime, line=dict(width=0)), opacity=0.85,
                hovertemplate=f"<b>{label_regime}</b><br>%{{x}}<br>%{{y:.2f}} Mds CDF<extra></extra>",
            ), row=2, col=1)

        # (2,2) Dépense moy. / bénéf.
        if reg_data:
            dep_moy = [
                (r["depense_moy_par_beneficiaire_cdf"] / 1e3) if r["depense_moy_par_beneficiaire_cdf"] is not None else None
                for r in reg_data
            ]
            fig.add_trace(go.Scatter(
                x=reg_annees, y=dep_moy,
                name=label_regime, showlegend=False,
                mode="lines+markers",
                line=dict(color=color_regime, width=3),
                marker=dict(size=9, line=dict(width=2, color='white')),
                hovertemplate=f"<b>{label_regime}</b><br>%{{x}}<br>%{{y:,.1f}} k CDF<extra></extra>",
            ), row=2, col=2)

        # (3,1) Recettes totales
        if reg_data:
            fig.add_trace(go.Bar(
                x=reg_annees,
                y=[(r["recettes_cdf"] / 1e9) if r["recettes_cdf"] is not None else None for r in reg_data],
                name=label_regime, showlegend=False,
                marker=dict(color=color_regime, line=dict(width=0)), opacity=0.85,
                hovertemplate=f"<b>{label_regime}</b><br>%{{x}}<br>%{{y:.2f}} Mds CDF<extra></extra>",
            ), row=3, col=1)

        # (3,2) Contribution moy. / cotisant
        if reg_data:
            contrib_moy = [
                (r["recettes_cdf"] / r["cotisants_total"] / 1e3)
                if r["recettes_cdf"] is not None and r["cotisants_total"] and r["cotisants_total"] > 0
                else None
                for r in reg_data
            ]
            fig.add_trace(go.Scatter(
                x=reg_annees, y=contrib_moy,
                name=label_regime, showlegend=False,
                mode="lines+markers",
                line=dict(color=color_regime, width=3),
                marker=dict(size=9, line=dict(width=2, color='white')),
                hovertemplate=f"<b>{label_regime}</b><br>%{{x}}<br>%{{y:,.1f}} k CDF<extra></extra>",
            ), row=3, col=2)

        title_text = f"{label_inst} — {label_regime}"
        fig.update_layout(
            title=dict(
                text=title_text,
                font=dict(size=20, family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color='#2c5282', weight=700),
                x=0.5, xanchor='center', y=0.98, yanchor='top',
            ),
            height=950,
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.08,
                xanchor="center", x=0.5,
                font=dict(size=11, color='#4a5568'),
                bgcolor='rgba(247,250,252,0.8)', bordercolor='#e2e8f0', borderwidth=1,
            ),
            showlegend=True,
            **COMMON_LAYOUT,
            margin=dict(t=80, b=80, l=70, r=40),
        )
        for row_i in range(1, 4):
            for col_j in range(1, 3):
                fig.update_xaxes(tickformat="d", dtick=1, row=row_i, col=col_j, **COMMON_AXIS)
                fig.update_yaxes(row=row_i, col=col_j, **COMMON_AXIS)

    else:
        # Mode sexué : 2 graphiques — cotisants H/F | bénéficiaires H/F stackés
        sexe_cap = "Hommes" if sex_mode == "hommes" else "Femmes"
        sex_suffix = "h" if sex_mode == "hommes" else "f"
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(f"Cotisants {sexe_cap}", f"Bénéficiaires {sexe_cap} par prestation"),
            horizontal_spacing=0.12,
        )

        # (1,1) Cotisants H/F — ligne unique (régime)
        if reg_data:
            reg_annees = [r["annee"] for r in reg_data]
            fig.add_trace(go.Scatter(
                x=reg_annees,
                y=[r.get(f"cotisants_{sex_suffix}") for r in reg_data],
                name=label_regime, showlegend=False,
                mode="lines+markers",
                line=dict(color=color_regime, width=3),
                marker=dict(size=9, line=dict(width=2, color='white')),
                hovertemplate=f"<b>{label_regime}</b><br>%{{x}}<br>%{{y:,.0f}} cotisants {sexe_cap.lower()}<extra></extra>",
            ), row=1, col=1)

        # (1,2) Bénéficiaires H/F — barres stackées par prestation
        annees_prest = sorted(set(r["annee"] for r in prest_data))
        for i, prest in enumerate(prestations_list):
            color = palette[i % len(palette)]
            subset = {r["annee"]: r for r in prest_data if r["nom_fr"] == prest}
            y_vals = [subset.get(a, {}).get(f"beneficiaires_{sex_suffix}") for a in annees_prest]
            fig.add_trace(go.Bar(
                x=annees_prest, y=y_vals,
                name=prest, legendgroup=prest,
                marker=dict(color=color),
                hovertemplate=f"<b>{prest}</b><br>%{{x}}<br>%{{y:,.0f}} bénéf. {sexe_cap.lower()}<extra></extra>",
            ), row=1, col=2)

        title_text = f"{label_inst} — {label_regime} ({sexe_cap})"
        fig.update_layout(
            title=dict(
                text=title_text,
                font=dict(size=20, family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color='#2c5282', weight=700),
                x=0.5, xanchor='center', y=0.98, yanchor='top',
            ),
            height=500,
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.35,
                xanchor="center", x=0.5,
                font=dict(size=11, color='#4a5568'),
                bgcolor='rgba(247,250,252,0.8)', bordercolor='#e2e8f0', borderwidth=1,
            ),
            showlegend=True,
            **COMMON_LAYOUT,
            margin=dict(t=80, b=140, l=70, r=40),
        )
        for col_j in range(1, 3):
            fig.update_xaxes(tickformat="d", dtick=1, row=1, col=col_j, **COMMON_AXIS)
            fig.update_yaxes(row=1, col=col_j, **COMMON_AXIS)

    fig.update_annotations(
        font=dict(
            size=14,
            family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            color='#2c5282', weight=600,
        )
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
            "Cotisants actifs (régime)",
            "Bénéficiaires totaux",
            "Dépenses (Mds CDF)",
            "Montant unitaire (CDF)",
            "Type de paiement", "Périodicité",
        ]
    else:
        sexe_cap = "Hommes" if sex_mode == "hommes" else "Femmes"
        headers = [
            "Régime", "Prestation", "Année",
            f"Cotisants actifs {sexe_cap} (régime)",
            f"Bénéficiaires {sexe_cap}",
            "Montant unitaire (CDF)",
            "Type de paiement", "Périodicité",
        ]
    
    body_rows = []
    for r in data:
        regime_name = NOM_COURT.get(r["regime_code"], r["regime_code"])
        
        if sex_mode == "all":
            cotisants = _fmt_num(r.get("couverture_effective_total"))
            benef = _fmt_num(r["beneficiaires_total"])
            depenses = _fmt_num(r.get("depenses_regime_cdf"), digits=2, scale=1e9)
            row_data = [
                regime_name,
                r["nom_fr"] or "—",
                str(r["annee"]) if r["annee"] else "—",
                cotisants,
                benef,
                depenses,
                _fmt_num(r["montant_unitaire_cdf"]),
                r["type_paiement"] or "—",
                r["periodicite"] or "—",
            ]
        elif sex_mode == "hommes":
            cotisants = _fmt_num(r.get("couverture_h"))
            benef = _fmt_num(r["beneficiaires_h"])
            row_data = [
                regime_name,
                r["nom_fr"] or "—",
                str(r["annee"]) if r["annee"] else "—",
                cotisants,
                benef,
                _fmt_num(r["montant_unitaire_cdf"]),
                r["type_paiement"] or "—",
                r["periodicite"] or "—",
            ]
        else:
            cotisants = _fmt_num(r.get("couverture_f"))
            benef = _fmt_num(r["beneficiaires_f"])
            row_data = [
                regime_name,
                r["nom_fr"] or "—",
                str(r["annee"]) if r["annee"] else "—",
                cotisants,
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


def build_indicateurs_payload(regime_rows: list[dict], prestation_rows: list[dict]) -> dict:
    by_year = {}
    by_inst_year = {}
    regime_indicator_rows = []
    prestation_indicator_rows = []

    def add_value(container: dict, key: str, val):
        if val is None:
            return
        try:
            container[key] += float(val)
        except (TypeError, ValueError):
            return

    for r in regime_rows:
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

        regime_indicator_rows.append({
            "programme_id": f"regime::{inst}::{r.get('regime_code')}",
            "institution": inst,
            "regime_code": r.get("regime_code"),
            "nom_regime": r.get("nom_fr") or NOM_COURT.get(r.get("regime_code"), r.get("regime_code")),
            "annee": year,
            "cotisants": float(r.get("cotisants_total") or 0),
            "beneficiaires": float(r.get("beneficiaires_total") or 0),
            "depenses_cdf": float(r.get("depenses_prestations_cdf") or 0),
            "recettes_cdf": float(r.get("recettes_cdf") or 0),
        })

    for p in prestation_rows:
        year = p.get("annee")
        inst = p.get("institution")
        rc = p.get("regime_code")
        nom_prest = (p.get("nom_fr") or "").strip()
        if year is None or not inst or not rc or not nom_prest:
            continue
        prestation_indicator_rows.append({
            "programme_id": f"prestation::{inst}::{rc}::{nom_prest}",
            "parent_regime_id": f"regime::{inst}::{rc}",
            "institution": inst,
            "regime_code": rc,
            "nom_prestation": nom_prest,
            "annee": year,
            "beneficiaires": float(p.get("beneficiaires_total") or 0),
        })

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
            "rows_regimes": [],
            "rows_prestations": [],
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
        "rows_regimes": regime_indicator_rows,
        "rows_prestations": prestation_indicator_rows,
    }


def _parse_fonctions_oit(raw_value) -> list[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return [str(v).strip() for v in raw_value if str(v).strip()]
    txt = str(raw_value).strip()
    if not txt:
        return []
    try:
        parsed = json.loads(txt)
        if isinstance(parsed, list):
            return [str(v).strip() for v in parsed if str(v).strip()]
        if isinstance(parsed, str):
            return [parsed.strip()] if parsed.strip() else []
    except json.JSONDecodeError:
        pass
    return [txt]


def _map_function_to_branch(label: str) -> str:
    t = unicodedata.normalize("NFKD", (label or "").lower()).encode("ascii", "ignore").decode("ascii")
    if "enfant" in t or "famill" in t:
        return "enfants_famille"
    if "matern" in t or "patern" in t:
        return "maternite"
    if "accident" in t or "professionnelle" in t or "at/mp" in t:
        return "at_mp"
    if "vieill" in t:
        return "vieillesse"
    if "invalid" in t or "handicap" in t:
        return "invalidite"
    if "survivan" in t:
        return "survivants"
    return "autres"


def build_branches_ess_payload(prestations: list[dict]) -> dict:
    branch_labels = {
        "enfants_famille": "Enfants & famille",
        "maternite": "Maternité",
        "at_mp": "Accidents du travail / MP",
        "vieillesse": "Vieillesse",
        "invalidite": "Invalidité / handicap",
        "survivants": "Survivants",
        "autres": "Autres fonctions",
    }
    branch_order = [
        "enfants_famille",
        "maternite",
        "at_mp",
        "vieillesse",
        "invalidite",
        "survivants",
        "autres",
    ]
    detailed_rows = []
    provenance = {key: set() for key in branch_order}

    for r in prestations:
        year = r.get("annee")
        inst = r.get("institution")
        rc = r.get("regime_code")
        nom_prest = (r.get("nom_fr") or "").strip()
        if year is None or not inst or not rc:
            continue
        fonction = (r.get("fonction_oit") or "").strip()
        branch_keys = sorted(set(_map_function_to_branch(f) for f in [fonction] if f))
        if not branch_keys:
            branch_keys = ["autres"]
        share = 1.0 / len(branch_keys)
        benef = float(r.get("beneficiaires_total") or 0)
        cotis = 0.0
        for key in branch_keys:
            provenance.setdefault(key, set()).add(f"{inst}/{rc}/{nom_prest or '-'}")
            detailed_rows.append({
                "program_id": f"prestation::{inst}::{rc}::{nom_prest}",
                "institution": inst,
                "regime_code": rc,
                "prestation": nom_prest,
                "annee": int(year),
                "branche": key,
                "beneficiaires_estimes": benef * share,
                "cotisants_estimes": cotis * share,
                "couverts_bruts_estimes": (benef + cotis) * share,
            })

    return {
        "branch_labels": branch_labels,
        "branch_order": branch_order,
        "rows": detailed_rows,
        "provenance": {k: sorted(list(v)) for k, v in provenance.items()},
        "note_methodo": (
            "Cette vue est construite au niveau prestation (ESS). Les fonctions OIT servent à "
            "classer chaque prestation dans une branche thématique pour une lecture intuitive."
        ),
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
            "all": {
                "population": fig_institution(regimes, inst, "all"),
                "finances": fig_institution_finances(regimes, inst),
            },
            "hommes": {
                "population": fig_institution(regimes, inst, "hommes"),
                "finances": "",
            },
            "femmes": {
                "population": fig_institution(regimes, inst, "femmes"),
                "finances": "",
            },
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
    regime_sex_series = {}
    for row in regimes:
        inst = row.get("institution")
        rc = row.get("regime_code")
        year = row.get("annee")
        if not inst or not rc or year is None:
            continue
        regime_sex_series.setdefault(inst, {})
        regime_sex_series[inst].setdefault(rc, {})
        regime_sex_series[inst][rc][str(year)] = {
            "cotisants_total": row.get("cotisants_total"),
            "cotisants_h": row.get("cotisants_h"),
            "cotisants_f": row.get("cotisants_f"),
            "beneficiaires_total": row.get("beneficiaires_total"),
            "beneficiaires_h": row.get("beneficiaires_h"),
            "beneficiaires_f": row.get("beneficiaires_f"),
        }
    regime_sex_series_json = js_safe_json(regime_sex_series)
    prestation_meta_json = js_safe_json(prestation_meta)
    criteres_json = js_safe_json(CRITERIA_FIELDS)
    indicateurs_payload = build_indicateurs_payload(regimes, prestations)
    indicateurs_json = js_safe_json(indicateurs_payload)
    branches_ess_json = js_safe_json(build_branches_ess_payload(prestations))
    odd_programmes_json = js_safe_json(build_odd_programmes_payload(regimes, prestations, regime_meta, prestation_meta))
    odd_indicators_json = js_safe_json(ODD_INDICATORS)
    years_for_defaults = indicateurs_payload.get("years", [])
    year_start_default = min(years_for_defaults) if years_for_defaults else 2020
    year_end_default = max(years_for_defaults) if years_for_defaults else 2024
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
            "year_start_total": year_start_default,
            "year_end_total": year_end_default,
            "year_start_active": year_start_default,
            "year_end_active": year_end_default,
            "year_start_retraite": year_start_default,
            "year_end_retraite": year_end_default,
            "year_start_maternite": year_start_default,
            "year_end_maternite": year_end_default,
            "retirement_age_h": 65,
            "retirement_age_f": 65,
            "working_age_min": 15,
            "working_age_max": 64,
            "maternity_age_min": 15,
            "maternity_age_max": 49,
        },
        # Données pré-chargées BM/WPP pour la RDC (évite un écran vide au démarrage)
        # Sources : Banque mondiale SP.POP.TOTL, SP.POP.1564.TO, SP.POP.65UP.TO,
        #           SP.DYN.CBRT.IN — consultées juin 2025.
        # Naissances = proxy (CBR × pop totale / 1000).
        "static_rows": [
            {
                "year": 2019,
                "populationTotale": 86776688,
                "populationActive": 49876139,
                "populationRetraite": 1877054,
                "naissancesVivantes": 3704274,
                "femmesAyantAccouche": 3704274,
                "metaTotal": "BM SP.POP.TOTL 2019 (pré-chargé)",
                "metaActive": "BM SP.POP.1564.TO 2019 (pré-chargé)",
                "metaRetraite": "BM SP.POP.65UP.TO 2019 (pré-chargé)",
                "metaNaissances": "BM CBR×Pop 2019 (pré-chargé)",
                "metaFemmes": "BM CBR×Pop 2019 (pré-chargé)",
            },
            {
                "year": 2020,
                "populationTotale": 89561404,
                "populationActive": 51503261,
                "populationRetraite": 1937900,
                "naissancesVivantes": 3779491,
                "femmesAyantAccouche": 3779491,
                "metaTotal": "BM SP.POP.TOTL 2020 (pré-chargé)",
                "metaActive": "BM SP.POP.1564.TO 2020 (pré-chargé)",
                "metaRetraite": "BM SP.POP.65UP.TO 2020 (pré-chargé)",
                "metaNaissances": "BM CBR×Pop 2020 (pré-chargé)",
                "metaFemmes": "BM CBR×Pop 2020 (pré-chargé)",
            },
            {
                "year": 2021,
                "populationTotale": 92377993,
                "populationActive": 53154768,
                "populationRetraite": 2001345,
                "naissancesVivantes": 3852162,
                "femmesAyantAccouche": 3852162,
                "metaTotal": "BM SP.POP.TOTL 2021 (pré-chargé)",
                "metaActive": "BM SP.POP.1564.TO 2021 (pré-chargé)",
                "metaRetraite": "BM SP.POP.65UP.TO 2021 (pré-chargé)",
                "metaNaissances": "BM CBR×Pop 2021 (pré-chargé)",
                "metaFemmes": "BM CBR×Pop 2021 (pré-chargé)",
            },
            {
                "year": 2022,
                "populationTotale": 95240792,
                "populationActive": 54832901,
                "populationRetraite": 2067543,
                "naissancesVivantes": 3923921,
                "femmesAyantAccouche": 3923921,
                "metaTotal": "BM SP.POP.TOTL 2022 (pré-chargé)",
                "metaActive": "BM SP.POP.1564.TO 2022 (pré-chargé)",
                "metaRetraite": "BM SP.POP.65UP.TO 2022 (pré-chargé)",
                "metaNaissances": "BM CBR×Pop 2022 (pré-chargé)",
                "metaFemmes": "BM CBR×Pop 2022 (pré-chargé)",
            },
        ],
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
    .kpi-card-selected-year {{
      border-color: #2b6cb0;
      box-shadow: 0 0 0 3px rgba(43,108,176,0.18), 0 4px 12px rgba(44,82,130,0.12);
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
    .kpi-num-name {{
      margin-top: 6px;
      color: #2d3748;
      font-size: 0.84rem;
      font-weight: 700;
    }}
    .kpi-definition {{
      margin-top: 2px;
      color: #718096;
      font-size: 0.75rem;
      line-height: 1.35;
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
    .odd-global-actions {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-start;
      gap: 8px;
      margin: 8px 0 10px 0;
    }}
    .odd-global-actions label {{
      color: #1a365d;
      font-size: 0.9rem;
      font-weight: 700;
    }}
    .odd-global-actions select {{
      min-width: 520px;
      border: 2px solid #2c5282;
      border-radius: 10px;
      background: #fff;
      padding: 9px 12px;
      font-size: 0.95rem;
      font-weight: 700;
      color: #1a365d;
      box-shadow: 0 2px 10px rgba(44,82,130,0.14);
    }}
    .odd-indicator-context {{
      margin: 6px 0 10px 0;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid #d6e4ff;
      background: #edf4ff;
      color: #1a365d;
      font-size: 0.84rem;
      font-weight: 600;
      line-height: 1.4;
    }}
    .odd-view-btn {{
      border: 1px solid #cbd5e0;
      border-radius: 8px;
      background: #fff;
      color: #1a365d;
      padding: 6px 10px;
      font-size: 0.82rem;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
    }}
    .odd-decision-panel {{
      display: none;
      margin: 8px 12px 12px;
      border: 1px solid #d1e3ff;
      border-radius: 12px;
      background: #edf0f5;
      overflow: hidden;
    }}
    .odd-decision-panel.visible {{
      display: block;
    }}
    .odd-decision-panel-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      background: #e2e8f0;
      border-bottom: 1px solid #cbd5e0;
      font-weight: 700;
      color: #1a365d;
      font-size: 0.9rem;
    }}
    .odd-decision-content {{
      margin-top: 6px;
      padding: 0 12px 12px;
    }}
    .odd-edit-controls {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 0 auto;
      flex-wrap: nowrap;
    }}
    .odd-save-btn {{
      border: 1px solid #2c5282;
      border-radius: 8px;
      background: #2c5282;
      color: #fff;
      padding: 6px 10px;
      font-size: 0.82rem;
      font-weight: 700;
      cursor: pointer;
      display: none;
    }}
    .odd-save-btn[disabled] {{
      opacity: 0.6;
      cursor: not-allowed;
    }}
    .odd-visual-permanent {{
      margin-top: 12px;
    }}
    .odd-numerator-rule-text {{
      margin: 8px 0 4px 0;
      font-size: 0.82rem;
      color: #4a5568;
      font-style: italic;
      padding: 4px 8px;
      background: #f7fafc;
      border-left: 3px solid #bee3f8;
      border-radius: 4px;
    }}
    .odd-shared-legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 18px;
      margin: 6px 0 12px 0;
      padding: 6px 10px;
      background: #f7fafc;
      border-radius: 6px;
      font-size: 0.8rem;
      color: #2d3748;
    }}
    .odd-legend-item {{
      display: flex;
      align-items: center;
      gap: 5px;
      white-space: nowrap;
    }}
    .odd-legend-swatch {{
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 2px;
      flex-shrink: 0;
    }}
    .odd-breakdown-fold {{
      margin-top: 12px;
      border: 1px solid #d6e4ff;
      border-radius: 12px;
      background: #ffffff;
      overflow: hidden;
    }}
    .odd-breakdown-fold > summary {{
      cursor: pointer;
      list-style: none;
      font-weight: 700;
      color: #1a365d;
      padding: 10px 24px 10px 12px;
      background: #f0f4f8;
      border-bottom: 1px solid #dbe5f3;
      border-radius: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
      user-select: none;
    }}
    .odd-breakdown-fold[open] > summary {{
      border-radius: 8px 8px 0 0;
    }}
    .odd-breakdown-fold > summary::before {{
      content: none;
    }}
    .odd-breakdown-fold[open] > summary::before {{
      content: none;
    }}
    .odd-breakdown-fold > summary::-webkit-details-marker {{ display: none; }}
    .odd-year-aligned-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
      padding: 12px;
    }}
    .odd-year-block {{
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #fff;
      padding: 10px;
      min-height: 220px;
    }}
    .odd-year-block h5 {{
      margin: 0 0 8px 0;
      color: #1a365d;
      font-size: 0.92rem;
    }}
    .odd-year-total {{
      margin-bottom: 8px;
      color: #2d3748;
      font-size: 0.82rem;
      font-weight: 700;
    }}
    .odd-calc-rule {{
      margin-bottom: 8px;
      color: #4a5568;
      font-size: 0.76rem;
      font-style: italic;
    }}
    .odd-calc-line {{
      font-size: 0.8rem;
      color: #2d3748;
      margin: 4px 0;
      line-height: 1.35;
    }}
    .odd-calc-tree details {{
      margin: 4px 0 6px 0;
      border: 1px solid #edf2f7;
      border-radius: 8px;
      padding: 6px 8px;
      background: #f8fafc;
    }}
    .odd-calc-tree summary {{
      cursor: pointer;
      font-weight: 600;
      color: #2d3748;
      font-size: 0.79rem;
    }}
    .odd-calc-tree ul {{
      margin: 6px 0 0 16px;
      padding: 0;
    }}
    .odd-calc-tree li {{
      margin: 2px 0;
      font-size: 0.78rem;
      color: #4a5568;
    }}
    .odd-decision-toolbar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      margin: 10px 0 12px 0;
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid #dbe5f3;
      background: #ffffff;
    }}
    .odd-decision-mode {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }}
    .odd-mode-badge {{
      display: inline-flex;
      align-items: center;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid #cbd5e0;
      background: #f7fafc;
      color: #2d3748;
      font-size: 0.8rem;
      font-weight: 700;
    }}
    .odd-mode-badge.edit {{
      border-color: #2b6cb0;
      background: #ebf8ff;
      color: #1a365d;
    }}
    .odd-edit-btn {{
      border: 1px solid #cbd5e0;
      border-radius: 8px;
      background: #fff;
      padding: 5px 9px;
      cursor: pointer;
      font-size: 0.9rem;
      line-height: 1;
    }}
    .odd-decision-year {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-left: auto;
    }}
    .odd-decision-year label {{
      color: #2d3748;
      font-size: 0.84rem;
      font-weight: 600;
    }}
    .odd-decision-year select {{
      min-width: 120px;
      border: 1px solid #cbd5e0;
      border-radius: 8px;
      background: #fff;
      padding: 6px 10px;
      font-size: 0.84rem;
    }}
    #odd-decisions-reset {{
      border: 1px solid #cbd5e0;
      border-radius: 8px;
      background: #fff;
      padding: 6px 10px;
      cursor: pointer;
      font-size: 0.84rem;
    }}
    .odd-decision-summary {{
      font-size: 0.85rem;
      color: #4a5568;
      font-weight: 600;
      flex-basis: 100%;
    }}
    .odd-decision-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.86rem;
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      overflow: hidden;
    }}
    .odd-decision-table th, .odd-decision-table td {{
      border: 1px solid #e2e8f0;
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }}
    .odd-decision-table thead th {{
      background: #ebf4ff;
      color: #1a365d;
      font-weight: 700;
    }}
    .odd-decision-table select {{
      width: 100%;
      min-width: 180px;
      padding: 5px 8px;
      border: 1px solid #cbd5e0;
      border-radius: 6px;
      background: #fff;
    }}
    .odd-hierarchy {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .odd-node {{
      border: 1px solid #e2e8f0;
      border-left: 4px solid #e2e8f0;
      border-radius: 10px;
      background: #fff;
      padding: 10px 12px;
    }}
    .odd-node summary {{
      cursor: pointer;
      color: #2d3748;
      font-size: 0.8rem;
      font-weight: 600;
      margin: -2px 0 8px 0;
      padding-bottom: 5px;
      border-bottom: 1px dashed #e2e8f0;
    }}
    .odd-summary-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }}
    .odd-summary-title {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
    }}
    .odd-summary-bottom {{
      margin-top: 4px;
      margin-left: 18px;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .odd-summary-rationale {{
      font-size: 0.76rem;
      color: #4a5568;
      font-style: italic;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: min(100%, 760px);
    }}
    .odd-node-children {{
      margin-top: 8px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .odd-node-header {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }}
    .odd-node-main {{
      color: #1a365d;
      font-size: 0.9rem;
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      line-height: 1.35;
    }}
    .odd-node-controls {{
      min-width: 240px;
      max-width: 320px;
      width: 100%;
    }}
    .odd-node-controls select {{
      width: 100%;
      min-width: 200px;
      padding: 6px 8px;
      border: 1px solid #cbd5e0;
      border-radius: 6px;
      background: #fff;
      font-size: 0.82rem;
    }}
    .odd-node-controls select:disabled {{
      background: #edf2f7;
      color: #718096;
      border-color: #e2e8f0;
      cursor: not-allowed;
    }}
    .odd-node-meta {{
      margin-top: 8px;
      padding-top: 6px;
      border-top: 1px solid #edf2f7;
    }}
    .odd-node.level-0 {{
      margin-left: 0;
      background: #f7fbff;
      border-color: #90cdf4;
      border-left-color: #3182ce;
    }}
    .odd-node.level-1 {{
      margin-left: 22px;
      background: #ffffff;
      border-color: #c6d8f5;
      border-left-color: #4a90e2;
    }}
    .odd-node.level-2 {{
      margin-left: 44px;
      background: #f8fafc;
      border-color: #e2e8f0;
      border-left-color: #718096;
    }}
    .odd-node-title {{
      font-weight: 700;
      color: #1a365d;
    }}
    .odd-node-kind {{
      display: inline-flex;
      align-items: center;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      white-space: nowrap;
    }}
    .odd-node-kind.type-institution_ess {{ background: #dbeafe; color: #1e3a8a; }}
    .odd-node-kind.type-regime_ess {{ background: #e0f2fe; color: #0c4a6e; }}
    .odd-node-kind.type-prestation_ess {{ background: #f1f5f9; color: #334155; }}
    .odd-badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
      white-space: nowrap;
    }}
    .odd-badge.entierement_inclus {{ background: #e6fffa; color: #22543d; }}
    .odd-badge.inclus {{ background: #e6fffa; color: #22543d; }}
    .odd-badge.entierement_exclus {{ background: #fff5f5; color: #9b2c2c; }}
    .odd-badge.exclus {{ background: #fff5f5; color: #9b2c2c; }}
    .odd-badge.autres {{ background: #eaf4ff; color: #1e3a8a; }}
    .odd-badge.inclus_avec_reserve {{ background: #fff7e6; color: #9c4221; }}
    .odd-badge.exclu_nature, .odd-badge.exclu_non_statutaire, .odd-badge.exclu_hors_indicateur {{ background: #fff5f5; color: #9b2c2c; }}
    .odd-badge.indicateur_connexe {{ background: #ebf8ff; color: #2a4365; }}
    .odd-badge.en_discussion {{ background: #faf5ff; color: #553c9a; }}
    .odd-badge.odd-badge-proposal {{
      background: #f8fafc;
      color: #4a5568;
      border: 1px solid #d2dae3;
    }}
    .odd-impact {{
      font-size: 0.78rem;
      color: #4a5568;
      font-style: italic;
    }}
    .odd-branches-panel {{
      margin-top: 16px;
      padding: 14px;
      border: 1px solid #d6e4ff;
      border-radius: 12px;
      background: #ffffff;
    }}
    .odd-branches-controls {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
    }}
    .odd-branches-controls label {{
      color: #2d3748;
      font-weight: 600;
      font-size: 0.86rem;
    }}
    .odd-branches-mode {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      min-height: 32px;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid #cbd5e0;
      background: #f7fafc;
      color: #1a365d;
      font-size: 0.84rem;
      font-weight: 600;
    }}
    .odd-calc-details {{
      margin-bottom: 10px;
      padding: 8px 10px;
      border-radius: 8px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      font-size: 0.83rem;
      color: #2d3748;
      line-height: 1.45;
    }}
    .odd-calc-details strong {{
      color: #1a365d;
    }}
    .odd-global-actions select {{
      min-width: 280px;
      border: 1px solid #cbd5e0;
      border-radius: 7px;
      padding: 6px 9px;
      background: #fff;
      font-size: 0.86rem;
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
    .odd-indicator-grid {{
      grid-template-columns: minmax(0, 1fr);
      gap: 20px;
    }}
    .odd-indicator-grid .chart-block {{
      min-height: 540px;
    }}
    .denom-panel {{
      margin-top: 18px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #ffffff;
      padding: 14px 16px;
    }}
    .numerator-panel {{
      margin-top: 12px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #ffffff;
      padding: 14px 16px;
    }}
    .denom-active-context {{
      margin: 8px 0 10px 0;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid #dbe5f3;
      background: #f8fbff;
      color: #1a365d;
      font-size: 0.84rem;
      font-weight: 600;
      line-height: 1.4;
    }}
    .denom-api-wrap {{
      padding: 10px 12px 12px 12px;
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
      grid-template-columns: minmax(620px, 1.6fr) minmax(0, 3.4fr);
      gap: 24px;
      align-items: start;
      margin-top: 20px;
      width: 100%;
    }}
    .institution-main .chart-block {{ 
      margin-bottom: 0;
      height: auto;
      display: flex;
      flex-direction: column;
    }}
    .institution-main #block-desc-institution,
    .institution-main #block-charts-institution {{
      height: auto;
      width: 100%;
    }}
    .institution-main .chart-block > h3 {{
      flex-shrink: 0;
    }}
    .institution-main #block-desc-institution,
    .institution-main #block-desc-prestations {{
      overflow: hidden;
    }}
    .institution-main #block-desc-institution .regime-description,
    .institution-main #block-desc-prestations .regime-description {{
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      padding-right: 6px;
    }}
    .institution-main #charts-institution-pop,
    .institution-main #charts-institution-fin {{
      flex: none;
      overflow: visible;
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
      min-width: 0;
      overflow: hidden;
    }}
    .regime-card:hover {{
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
      transform: translateY(-2px);
    }}
    .regime-card-title {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 10px;
      margin: 0 0 10px;
      padding: 6px 12px;
      border-radius: 10px;
      background: linear-gradient(135deg, #e6f0ff 0%, #d9e9ff 100%);
      color: #2c5282;
      font-weight: 700;
      font-size: 0.9rem;
    }}
    .regime-card-title > span:first-child {{
      min-width: 0;
      overflow-wrap: anywhere;
      word-break: break-word;
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
      grid-template-columns: minmax(120px, 160px) minmax(0, 1fr);
      gap: 8px 14px;
      font-size: 0.95rem;
    }}
    .regime-grid .k {{ 
      color: #4a5568; 
      font-weight: 600; 
      min-width: 0;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    .regime-grid .v {{ 
      color: #2d3748; 
      min-width: 0;
      overflow-wrap: anywhere;
      word-break: break-word;
    }}
    .sex-pie-details {{
      margin-top: 4px;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #fff;
      overflow: hidden;
      flex-shrink: 0;
    }}
    .sex-pie-details > summary {{
      cursor: pointer;
      list-style: none;
      padding: 8px 12px;
      background: #f7fafc;
      color: #2c5282;
      font-weight: 700;
      font-size: 0.92rem;
      border-bottom: 1px solid transparent;
    }}
    .sex-pie-details > summary::-webkit-details-marker {{ display: none; }}
    .sex-pie-details[open] > summary {{
      border-bottom-color: #e2e8f0;
    }}
    .sex-pie-content {{
      padding: 10px;
    }}
    .sex-pie-section {{
      margin-top: 16px;
      border-top: 1px solid #e2e8f0;
      padding-top: 12px;
    }}
    .sex-pie-section:first-child {{
      margin-top: 0;
      border-top: none;
      padding-top: 0;
    }}
    .sex-pie-section h4 {{
      margin: 0 0 10px;
      font-size: 0.95rem;
      color: #2c5282;
      font-weight: 700;
    }}
    .sex-pie-grid {{
      width: 100%;
      min-height: 320px;
      height: 320px;
      border: 1px solid #edf2f7;
      border-radius: 10px;
      background: #fff;
      padding: 8px;
    }}
    .sex-pie-cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
      align-items: stretch;
    }}
    .sex-pie-card {{
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #fff;
      padding: 8px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      min-height: 220px;
    }}
    .sex-pie-year {{
      font-size: 0.84rem;
      font-weight: 700;
      color: #2c5282;
      margin: 0;
    }}
    .sex-pie-disc {{
      width: 132px;
      height: 132px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .sex-pie-disc svg {{
      width: 132px;
      height: 132px;
      overflow: visible;
    }}
    .sex-pie-legend {{
      width: 100%;
      display: grid;
      grid-template-columns: 1fr;
      gap: 6px;
      font-size: 0.86rem;
      color: #4a5568;
    }}
    .sex-pie-legend-item {{
      display: flex;
      align-items: center;
      gap: 4px;
      min-width: 0;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .sex-pie-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
    }}
    .sex-pie-grid.is-empty {{
      min-height: 320px;
      height: 320px;
      display: flex;
      align-items: center;
    }}
    .sex-pie-grid .empty {{
      margin: 0;
      color: #718096;
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
    <div class="odd-global-actions">
      <label for="odd-indicator-select">Indicateur actif :</label>
      <select id="odd-indicator-select"></select>
    </div>
    <div class="numerator-panel">
      <h4 class="numerateurs-title">Numérateur de l'indicateur</h4>
      <div id="odd-indicator-context" class="odd-indicator-context">Chargement…</div>
      <div id="ind-numerateurs" class="indicator-kpis indicator-kpis-numerateurs"></div>
      <div id="odd-numerator-rule" class="odd-numerator-rule-text"></div>
      <div id="odd-numerator-visual-grid" class="odd-year-aligned-grid odd-visual-permanent"></div>
      <div id="odd-numerator-legend" class="odd-shared-legend"></div>
      <details class="odd-breakdown-fold" open>
        <summary>
          <span>⚙ Construction des numérateurs</span>
          <span class="odd-edit-controls">
            <label for="odd-year-select" style="color:#2d3748;font-size:0.82rem;font-weight:600;white-space:nowrap;">Année :</label>
            <select id="odd-year-select" style="min-width:80px;border:1px solid #cbd5e0;border-radius:6px;background:#fff;padding:4px 8px;font-size:0.82rem;"></select>
            <button type="button" id="odd-decision-view-toggle" class="odd-view-btn" title="Consulter les décisions pour cette année">Consulter</button>
            <button type="button" id="odd-decision-edit-open" class="odd-view-btn" style="background:#2c5282;color:#fff;border-color:#2c5282;" title="Éditer les décisions pour cette année">Éditer</button>
          </span>
        </summary>
        <div id="odd-numerator-breakdown-grid" class="odd-year-aligned-grid"></div>
        <div id="odd-decision-panel" class="odd-decision-panel">
          <div class="odd-decision-panel-header">
            <span>Décisions d'inclusion/exclusion</span>
            <span class="odd-edit-controls">
              <span id="odd-decision-mode-badge" class="odd-mode-badge">Consultation</span>
              <button type="button" id="odd-decisions-save" class="odd-save-btn" title="Sauvegarder les modifications">Sauvegarder</button>
              <button type="button" id="odd-decision-close" class="odd-view-btn" title="Fermer">✕ Fermer</button>
            </span>
          </div>
          <div class="odd-decision-content">
          <div class="odd-decision-toolbar">
            <span id="odd-decision-summary" class="odd-decision-summary">Chargement…</span>
            <button type="button" id="odd-decisions-reset" style="margin-left:auto;">Réinitialiser</button>
          </div>
          <div id="odd-decision-table"></div>
          </div>
        </div>
      </details>
    </div>
    <div class="denom-panel">
      <h4 class="numerateurs-title">Dénominateur de l'indicateur</h4>
      <div id="denom-active-context" class="denom-active-context">Chargement…</div>
      <div id="denom-active-cards" class="indicator-kpis indicator-kpis-numerateurs"></div>
      <div id="denom-active-visual-grid" class="odd-year-aligned-grid odd-visual-permanent"></div>
      <details class="odd-breakdown-fold">
        <summary>
          <span>⚙ Construction des dénominateurs</span>
          <span class="odd-edit-controls">
            <button type="button" id="denom-btn-consulter" class="odd-view-btn" style="background:#2c5282;color:#fff;border-color:#2c5282;" title="Mode consultation (lecture seule)">Consulter</button>
            <button type="button" id="denom-btn-editer" class="odd-view-btn" title="Activer le mode édition des paramètres">Éditer</button>
            <button type="button" id="denom-save" class="odd-save-btn" title="Sauvegarder les paramètres du dénominateur">Sauvegarder</button>
          </span>
        </summary>
        <div class="denom-api-wrap">
      <div class="denom-actions">
        <button type="button" id="denom-refresh">Actualiser le dénominateur</button>
        <span id="denom-status" class="denom-status">Prêt.</span>
      </div>
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
        </div>
      </details>
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
        <div id="charts-institution-pop"></div>
        <details id="institution-sex-distributions" class="sex-pie-details">
          <summary>Distribution H/F (cotisants & bénéficiaires) par année</summary>
          <div class="sex-pie-content">
            <div class="sex-pie-section">
              <h4>Distribution des cotisants (H/F) par année</h4>
              <div id="chart-cotisants-sex-distrib" class="sex-pie-grid"></div>
            </div>
            <div class="sex-pie-section">
              <h4>Distribution des bénéficiaires (H/F) par année</h4>
              <div id="chart-beneficiaires-sex-distrib" class="sex-pie-grid"></div>
            </div>
          </div>
        </details>
        <div id="charts-institution-fin"></div>
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
const REGIME_SEX_SERIES = {regime_sex_series_json};
const PRESTATION_META = {prestation_meta_json};
const NOM_COURT    = {nom_court_json};
const CRITERIA_FIELDS = {criteres_json};
const INDICATEURS_DATA = {indicateurs_json};
const BRANCHES_ESS_DATA = {branches_ess_json};
const ODD_PROGRAMMES_DATA = {odd_programmes_json};
const ODD_INDICATORS = {odd_indicators_json};
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

function initGraphSeriesFilters(plotContainerId, filtersContainerId, label, onSelectionChange, onReady, extraContainerIds) {{
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
      // Propager le filtre aux graphiques secondaires (ex. finances agrégées)
      (extraContainerIds || []).forEach(extraId => {{
        const extraHost = document.getElementById(extraId);
        if (!extraHost) return;
        const extraPlotDiv = extraHost.querySelector('.plotly-graph-div');
        if (!extraPlotDiv || !extraPlotDiv.data) return;
        const extraVisible = extraPlotDiv.data.map(trace => {{
          const key = trace.legendgroup || trace.name;
          return selected.includes(key) ? true : 'legendonly';
        }});
        Plotly.restyle(extraPlotDiv, {{ visible: extraVisible }});
      }});
      if (onSelectionChange) onSelectionChange(selected);
    }};
    // Filtre piloté par liste externe (sélection rapide)
    filtersHost._applySeriesFilterWithSelection = (allowedKeys) => {{
      const activePlotDiv = getActivePlotDiv();
      if (!activePlotDiv || !activePlotDiv.data) return;
      const checkboxes = Array.from(filtersHost.querySelectorAll('input[type="checkbox"]'));
      if (!checkboxes.length) return;
      const normalizedAllowed = (allowedKeys || [])
        .map(k => String(k || '').trim().toLowerCase())
        .filter(Boolean);
      let matchedCount = 0;
      checkboxes.forEach(cb => {{
        if (!normalizedAllowed.length) {{
          cb.checked = true;
          matchedCount += 1;
          return;
        }}
        const key = String(cb.value || '').trim().toLowerCase();
        const isMatch = normalizedAllowed.some(k => key === k || key.startsWith(k) || k.startsWith(key));
        cb.checked = isMatch;
        if (isMatch) matchedCount += 1;
      }});
      // Si aucune série ne correspond aux clés demandées, ne masquer aucune trace.
      if (normalizedAllowed.length && matchedCount === 0) {{
        checkboxes.forEach(cb => cb.checked = true);
      }}
      applySeriesFilter();
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

const ODD_DECISION_OPTIONS_BY_TYPE = {{
  institution_ess: [
    {{ value: 'entierement_inclus', label: 'Entièrement inclus' }},
    {{ value: 'entierement_exclus', label: 'Entièrement exclus' }},
    {{ value: 'autres', label: 'Autres' }},
  ],
  regime_ess: [
    {{ value: 'entierement_inclus', label: 'Entièrement inclus' }},
    {{ value: 'entierement_exclus', label: 'Entièrement exclus' }},
    {{ value: 'autres', label: 'Autres' }},
  ],
  prestation_ess: [
    {{ value: 'inclus', label: 'Inclus' }},
    {{ value: 'exclus', label: 'Exclus' }},
  ],
}};
const ODD_DECISION_LABELS = {{
  entierement_inclus: 'Entièrement inclus',
  entierement_exclus: 'Entièrement exclus',
  autres: 'Autres',
  inclus: 'Inclus',
  exclus: 'Exclus',
  inclus_avec_reserve: 'Inclus avec réserve',
  exclu_nature: 'Exclu — prestation en nature',
  exclu_non_statutaire: 'Exclu — non statutaire/humanitaire',
  exclu_hors_indicateur: 'Exclu — hors indicateur',
  indicateur_connexe: 'Indicateur connexe',
  en_discussion: 'En discussion',
}};
const ODD_DECISIONS_STORAGE_KEY = 'rdc_odd131_decisions_v1';
const DASHBOARD_SETTINGS_API = '/api/dashboard-settings';
let CURRENT_ODD_DECISIONS = {{}};
let CURRENT_ODD_INDICATOR = 'global_131';
let CURRENT_ODD_YEAR = '';
let ODD_DECISION_EDIT_MODE = false;
let ODD_DECISIONS_DRAFT = {{}};
let CURRENT_DENOM_ROWS = [];
let DENOM_EDIT_MODE = false;
let DENOM_PENDING_CHANGES = false;
const ODD_INDICATOR_LABELS = Object.fromEntries((ODD_INDICATORS || []).map(item => [item.key, item.label]));
const DENOMINATOR_BY_INDICATOR = {{
  global_131: {{
    shortKey: 'total',
    rowField: 'populationTotale',
    label: 'Population totale',
    definition: 'Population totale nationale utilisée comme dénominateur global.',
  }},
  ind_22_enfants: {{
    shortKey: 'total',
    rowField: 'populationTotale',
    label: 'Population totale',
    definition: "Proxy disponible en l'absence de série annuelle harmonisée sur la population enfant.",
  }},
  ind_23_maternite: {{
    shortKey: 'mat',
    rowField: 'femmesAyantAccouche',
    label: 'Femmes ayant accouché (proxy)',
    definition: "Proxy démographique des femmes ayant accouché sur l'année.",
  }},
  ind_24_handicap: {{
    shortKey: 'total',
    rowField: 'populationTotale',
    label: 'Population totale',
    definition: 'Proxy démographique global pour la lecture de la couverture handicap.',
  }},
  ind_25_atmp: {{
    shortKey: 'active',
    rowField: 'populationActive',
    label: 'Population active',
    definition: 'Population en âge de travailler / active pour les risques liés au travail.',
  }},
  ind_26_chomage: {{
    shortKey: 'active',
    rowField: 'populationActive',
    label: 'Population active',
    definition: "Population active de référence pour l'indicateur chômage.",
  }},
  ind_27_vieillesse: {{
    shortKey: 'ret',
    rowField: 'populationRetraite',
    label: "Population au-delà de l'âge de retraite",
    definition: "Population d'âge retraite selon les paramètres retenus.",
  }},
  ind_28_vulnerables: {{
    shortKey: 'total',
    rowField: 'populationTotale',
    label: 'Population totale',
    definition: 'Proxy global pour la population potentiellement vulnérable.',
  }},
  ind_29_cotisants: {{
    shortKey: 'active',
    rowField: 'populationActive',
    label: 'Population active',
    definition: 'Population active de référence pour la lecture des cotisants.',
  }},
}};
const ODD_INDICATOR_NUMERATOR_SPECS = {{
  global_131: {{
    metricKey: 'couverts_bruts_estimes',
    metricLabel: 'Couverts bruts estimés',
    modeLabel: 'Cotisants + bénéficiaires',
    numeratorName: 'Couverts bruts estimés',
    numeratorDefinition: "Somme des cotisants actifs et des bénéficiaires de prestations inclus dans l'indicateur.",
  }},
  ind_22_enfants: {{
    metricKey: 'beneficiaires_estimes',
    metricLabel: 'Bénéficiaires estimés',
    modeLabel: 'Prestations classées Enfants & famille',
    numeratorName: 'Bénéficiaires estimés',
    numeratorDefinition: 'Personnes recevant des prestations rattachées à la branche Enfants et famille.',
  }},
  ind_23_maternite: {{
    metricKey: 'beneficiaires_estimes',
    metricLabel: 'Bénéficiaires estimés',
    modeLabel: 'Prestations classées Maternité',
    numeratorName: 'Bénéficiaires estimés',
    numeratorDefinition: 'Personnes recevant des prestations rattachées à la branche Maternité.',
  }},
  ind_24_handicap: {{
    metricKey: 'beneficiaires_estimes',
    metricLabel: 'Bénéficiaires estimés',
    modeLabel: 'Prestations classées Invalidité / handicap',
    numeratorName: 'Bénéficiaires estimés',
    numeratorDefinition: "Personnes recevant des prestations liées à l'invalidité ou au handicap.",
  }},
  ind_25_atmp: {{
    metricKey: 'couverts_bruts_estimes',
    metricLabel: 'Couverts bruts estimés',
    modeLabel: 'Cotisants des régimes parents + bénéficiaires des prestations incluses',
    numeratorName: 'Couverts bruts estimés',
    numeratorDefinition: "Somme des cotisants des régimes parents (comptés une seule fois par régime) et des bénéficiaires des prestations AT/MP incluses.",
  }},
  ind_26_chomage: {{
    metricKey: 'beneficiaires_estimes',
    metricLabel: 'Bénéficiaires estimés',
    modeLabel: 'Sous-indicateur chômage (aucun régime identifié dans les ESS)',
    numeratorName: 'Bénéficiaires estimés',
    numeratorDefinition: 'Personnes recevant des prestations chômage (aucune composante ESS opérationnelle identifiée à ce stade).',
  }},
  ind_27_vieillesse: {{
    metricKey: 'beneficiaires_estimes',
    metricLabel: 'Bénéficiaires estimés',
    modeLabel: 'Prestations classées Vieillesse',
    numeratorName: 'Bénéficiaires estimés',
    numeratorDefinition: 'Personnes recevant des prestations rattachées à la branche Vieillesse.',
  }},
  ind_28_vulnerables: {{
    metricKey: 'beneficiaires_estimes',
    metricLabel: 'Bénéficiaires estimés',
    modeLabel: 'Prestations classées Enfants/Famille et autres fonctions',
    numeratorName: 'Bénéficiaires estimés',
    numeratorDefinition: 'Personnes recevant des prestations ciblant les ménages vulnérables selon le périmètre retenu.',
  }},
  ind_29_cotisants: {{
    metricKey: 'cotisants_estimes',
    metricLabel: 'Cotisants estimés',
    modeLabel: 'Cotisants actifs associés aux branches retraite/invalidité/survivants',
    numeratorName: 'Cotisants estimés',
    numeratorDefinition: 'Cotisants actifs des composantes contributives retenues pour les branches retraite/invalidité/survivants.',
  }},
}};

function getOddIndicatorNumeratorSpec(indicatorKey) {{
  const key = indicatorKey || getCurrentOddIndicator();
  return ODD_INDICATOR_NUMERATOR_SPECS[key] || {{
    metricKey: 'beneficiaires_estimes',
    metricLabel: 'Bénéficiaires estimés',
    modeLabel: 'Calcul basé sur les prestations incluses',
    numeratorName: 'Bénéficiaires estimés',
    numeratorDefinition: "Personnes recevant des prestations incluses dans le périmètre de l'indicateur.",
  }};
}}

function getDecisionLabel(code, nodeType) {{
  if (code && ODD_DECISION_LABELS[code]) return ODD_DECISION_LABELS[code];
  if (nodeType === 'institution_ess') return ODD_DECISION_LABELS.autres;
  if (nodeType === 'regime_ess') return ODD_DECISION_LABELS.entierement_exclus;
  if (nodeType === 'prestation_ess') return ODD_DECISION_LABELS.exclus;
  return ODD_DECISION_LABELS.en_discussion;
}}

function readOddDecisionsFromLocalStorage() {{
  try {{
    const raw = localStorage.getItem(ODD_DECISIONS_STORAGE_KEY);
    if (!raw) return {{}};
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return {{}};
    return parsed;
  }} catch (err) {{
    console.warn('[ODD] Lecture localStorage impossible:', err);
    return {{}};
  }}
}}

function writeOddDecisionsToLocalStorage(decisions) {{
  try {{
    localStorage.setItem(ODD_DECISIONS_STORAGE_KEY, JSON.stringify(decisions || {{}}));
  }} catch (err) {{
    console.warn('[ODD] Ecriture localStorage impossible:', err);
  }}
}}

async function loadOddDecisions() {{
  const localDecisions = readOddDecisionsFromLocalStorage();
  try {{
    const res = await fetch(DASHBOARD_SETTINGS_API, {{ cache: 'no-store' }});
    if (!res.ok) return localDecisions;
    const payload = await res.json();
    const serverDecisions = (payload && typeof payload === 'object' && payload.oddDecisions && typeof payload.oddDecisions === 'object')
      ? payload.oddDecisions
      : {{}};
    const finalDecisions = Object.keys(serverDecisions).length ? serverDecisions : localDecisions;
    writeOddDecisionsToLocalStorage(finalDecisions);
    return finalDecisions;
  }} catch (err) {{
    return localDecisions;
  }}
}}

async function saveOddDecisions() {{
  const decisions = CURRENT_ODD_DECISIONS || {{}};
  writeOddDecisionsToLocalStorage(decisions);
  try {{
    const res = await fetch(DASHBOARD_SETTINGS_API, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ oddDecisions: decisions }}),
    }});
    if (!res.ok) {{
      console.warn('[ODD] Sauvegarde serveur non confirmee (HTTP ' + res.status + ').');
    }}
  }} catch (err) {{
    // Dashboard ouvert hors serveur preview : persistance locale maintenue.
  }}
}}

function getCurrentOddIndicator() {{
  const select = document.getElementById('odd-indicator-select');
  if (select && select.value) return select.value;
  return CURRENT_ODD_INDICATOR || 'global_131';
}}

function getOddAvailableYears() {{
  const years = ((INDICATEURS_DATA && INDICATEURS_DATA.years) || [])
    .map(y => Number(y))
    .filter(y => Number.isFinite(y))
    .sort((a, b) => a - b);
  return years;
}}

function getCurrentOddYear() {{
  const yearSelect = document.getElementById('odd-year-select');
  if (yearSelect && yearSelect.value) return String(yearSelect.value);
  if (CURRENT_ODD_YEAR) return String(CURRENT_ODD_YEAR);
  const years = getOddAvailableYears();
  if (!years.length) return '';
  return String(years[years.length - 1]);
}}

function getOddDecisionStorageKey(programId, indicatorKey, yearKey) {{
  const pid = String(programId || '');
  const indicator = String(indicatorKey || getCurrentOddIndicator() || 'global_131');
  const year = String(yearKey || getCurrentOddYear() || '');
  return pid + '::' + indicator + '::' + year;
}}

function cloneDecisionMap(map) {{
  try {{
    return JSON.parse(JSON.stringify(map || {{}}));
  }} catch (_err) {{
    return {{}};
  }}
}}

function getActiveOddDecisionMap() {{
  return ODD_DECISION_EDIT_MODE ? (ODD_DECISIONS_DRAFT || {{}}) : (CURRENT_ODD_DECISIONS || {{}});
}}

const ODD_INCLUDED_STATES = new Set(['entierement_inclus', 'inclus', 'inclus_avec_reserve']);
const ODD_EXCLUDED_STATES = new Set(['entierement_exclus', 'exclus', 'exclu_nature', 'exclu_non_statutaire', 'exclu_hors_indicateur']);

function isOddIncludedState(status) {{
  return ODD_INCLUDED_STATES.has(status);
}}

function normalizeDecisionForNode(node, rawDecision) {{
  const nodeType = (node && node.type) || '';
  const decision = rawDecision || '';
  if (nodeType === 'institution_ess') {{
    if (decision === 'entierement_inclus' || decision === 'inclus' || decision === 'inclus_avec_reserve') return 'entierement_inclus';
    if (decision === 'entierement_exclus' || decision === 'exclus' || ODD_EXCLUDED_STATES.has(decision)) return 'entierement_exclus';
    return 'autres';
  }}
  if (nodeType === 'regime_ess') {{
    if (decision === 'entierement_inclus' || decision === 'inclus' || decision === 'inclus_avec_reserve') return 'entierement_inclus';
    if (decision === 'entierement_exclus' || decision === 'exclus' || ODD_EXCLUDED_STATES.has(decision)) return 'entierement_exclus';
    return 'autres';
  }}
  if (nodeType === 'prestation_ess') {{
    if (decision === 'entierement_inclus' || decision === 'inclus' || decision === 'inclus_avec_reserve') return 'inclus';
    if (decision === 'entierement_exclus' || decision === 'exclus' || ODD_EXCLUDED_STATES.has(decision)) return 'exclus';
    return 'exclus';
  }}
  return decision || 'en_discussion';
}}

function getDecisionForProgram(program, indicatorKey, yearKey) {{
  if (!program) return 'en_discussion';
  const key = indicatorKey || getCurrentOddIndicator();
  const year = yearKey || getCurrentOddYear();
  const scopedKey = getOddDecisionStorageKey(program.id, key, year);
  const legacyKey = String(program.id || '') + '::' + key;
  const decisionMap = getActiveOddDecisionMap();
  if (decisionMap && decisionMap[scopedKey]) {{
    return normalizeDecisionForNode(program, decisionMap[scopedKey]);
  }}
  if (decisionMap && decisionMap[legacyKey]) {{
    return normalizeDecisionForNode(program, decisionMap[legacyKey]);
  }}
  const proposals = program.propositions || {{}};
  return normalizeDecisionForNode(program, proposals[key] || program.proposition || '');
}}

function getRationaleForProgram(program, indicatorKey) {{
  if (!program) return '';
  const key = indicatorKey || getCurrentOddIndicator();
  const rationales = program.rationales || {{}};
  return rationales[key] || program.rationale || '';
}}

function buildOddNodeMaps() {{
  const nodeMap = {{}};
  const childrenMap = {{}};
  (ODD_PROGRAMMES_DATA || []).forEach(node => {{
    if (!node || !node.id) return;
    nodeMap[node.id] = node;
    const parentId = node.parent_id || '';
    if (!childrenMap[parentId]) childrenMap[parentId] = [];
    childrenMap[parentId].push(node.id);
  }});
  return {{ nodeMap, childrenMap }};
}}

function getEffectiveDecisionById(nodeId, indicatorKey, yearKey, nodeMap, memo) {{
  if (!nodeId || !nodeMap[nodeId]) return 'en_discussion';
  const memoKey = String(nodeId) + '::' + String(yearKey || '');
  if (memo[memoKey]) return memo[memoKey];
  const node = nodeMap[nodeId];
  const own = normalizeDecisionForNode(node, getDecisionForProgram(node, indicatorKey, yearKey));
  const parentId = node.parent_id;
  if (!parentId || !nodeMap[parentId]) {{
    memo[memoKey] = own;
    return own;
  }}
  const parentEff = getEffectiveDecisionById(parentId, indicatorKey, yearKey, nodeMap, memo);
  if (parentEff === 'entierement_exclus' || parentEff === 'exclus') {{
    const forcedExcluded = node.type === 'prestation_ess' ? 'exclus' : 'entierement_exclus';
    memo[memoKey] = forcedExcluded;
    return forcedExcluded;
  }}
  if (parentEff === 'entierement_inclus' || parentEff === 'inclus') {{
    const forcedIncluded = node.type === 'prestation_ess' ? 'inclus' : 'entierement_inclus';
    memo[memoKey] = forcedIncluded;
    return forcedIncluded;
  }}
  memo[memoKey] = own;
  return own;
}}

function getIncludedRegimeIds(indicatorKey, yearKey) {{
  const key = indicatorKey || getCurrentOddIndicator();
  const year = yearKey || getCurrentOddYear();
  const maps = buildOddNodeMaps();
  const memo = {{}};
  return Object.keys(maps.nodeMap)
    .filter(id => maps.nodeMap[id] && maps.nodeMap[id].type === 'regime_ess')
    .filter(id => isOddIncludedState(getEffectiveDecisionById(id, key, year, maps.nodeMap, memo)));
}}

function getIncludedPrestationIds(indicatorKey, yearKey) {{
  const key = indicatorKey || getCurrentOddIndicator();
  const year = yearKey || getCurrentOddYear();
  const maps = buildOddNodeMaps();
  const memo = {{}};
  return Object.keys(maps.nodeMap)
    .filter(id => maps.nodeMap[id] && maps.nodeMap[id].type === 'prestation_ess')
    .filter(id => isOddIncludedState(getEffectiveDecisionById(id, key, year, maps.nodeMap, memo)));
}}

function aggregateIndicatorRows(regimeRows, prestationRows, includedRegimeSet, includedPrestationSet) {{
  const byYear = {{}};
  const byInstYear = {{}};
  (regimeRows || []).forEach(row => {{
    const year = Number(row.annee);
    const inst = row.institution;
    if (!Number.isFinite(year) || !inst) return;
    if (!includedRegimeSet.has(row.programme_id)) return;
    if (!byYear[year]) byYear[year] = {{ cotisants: 0, beneficiaires: 0, depenses_cdf: 0, recettes_cdf: 0 }};
    if (!byInstYear[inst]) byInstYear[inst] = {{}};
    if (!byInstYear[inst][year]) byInstYear[inst][year] = {{ cotisants: 0, beneficiaires: 0, depenses_cdf: 0, recettes_cdf: 0 }};
    byYear[year].cotisants += Number(row.cotisants || 0);
    byYear[year].depenses_cdf += Number(row.depenses_cdf || 0);
    byYear[year].recettes_cdf += Number(row.recettes_cdf || 0);
    byInstYear[inst][year].cotisants += Number(row.cotisants || 0);
    byInstYear[inst][year].depenses_cdf += Number(row.depenses_cdf || 0);
    byInstYear[inst][year].recettes_cdf += Number(row.recettes_cdf || 0);
  }});

  (prestationRows || []).forEach(row => {{
    const year = Number(row.annee);
    const inst = row.institution;
    if (!Number.isFinite(year) || !inst) return;
    if (!includedPrestationSet.has(row.programme_id)) return;
    if (!byYear[year]) byYear[year] = {{ cotisants: 0, beneficiaires: 0, depenses_cdf: 0, recettes_cdf: 0 }};
    if (!byInstYear[inst]) byInstYear[inst] = {{}};
    if (!byInstYear[inst][year]) byInstYear[inst][year] = {{ cotisants: 0, beneficiaires: 0, depenses_cdf: 0, recettes_cdf: 0 }};
    byYear[year].beneficiaires += Number(row.beneficiaires || 0);
    byInstYear[inst][year].beneficiaires += Number(row.beneficiaires || 0);
  }});

  const years = Object.keys(byYear).map(Number).sort((a, b) => a - b);
  if (!years.length) {{
    return {{
      years: [],
      totaux: {{ cotisants: [], beneficiaires: [], depenses_mds: [], recettes_mds: [] }},
      latest: null,
      institutions_latest: [],
    }};
  }}
  const latestYear = years[years.length - 1];
  const latestVals = byYear[latestYear];
  return {{
    years: years,
    totaux: {{
      cotisants: years.map(y => byYear[y].cotisants),
      beneficiaires: years.map(y => byYear[y].beneficiaires),
      depenses_mds: years.map(y => byYear[y].depenses_cdf / 1e9),
      recettes_mds: years.map(y => byYear[y].recettes_cdf / 1e9),
    }},
    latest: {{
      annee: latestYear,
      cotisants: latestVals.cotisants,
      beneficiaires: latestVals.beneficiaires,
      depenses_mds: latestVals.depenses_cdf / 1e9,
      recettes_mds: latestVals.recettes_cdf / 1e9,
      ratio_benef_cotis: latestVals.cotisants > 0 ? latestVals.beneficiaires / latestVals.cotisants : null,
      ratio_dep_rec: latestVals.recettes_cdf > 0 ? latestVals.depenses_cdf / latestVals.recettes_cdf : null,
    }},
    institutions_latest: Object.keys(byInstYear).sort().filter(inst => byInstYear[inst][latestYear]).map(inst => {{
      const vals = byInstYear[inst][latestYear];
      return {{
        institution: inst,
        cotisants: vals.cotisants,
        beneficiaires: vals.beneficiaires,
        depenses_mds: vals.depenses_cdf / 1e9,
        recettes_mds: vals.recettes_cdf / 1e9,
      }};
    }}),
  }};
}}

function buildNumeratorYearSummary(indicatorKey, yearValue, regimeRows, prestationRows, metricSpec) {{
  const yearNum = Number(yearValue);
  const yearKey = String(yearValue);
  const includeCotisants = metricSpec.metricKey === 'cotisants_estimes' || metricSpec.metricKey === 'couverts_bruts_estimes';
  const includeBeneficiaires = metricSpec.metricKey === 'beneficiaires_estimes' || metricSpec.metricKey === 'couverts_bruts_estimes';
  const includedRegimeSet = new Set(getIncludedRegimeIds(indicatorKey, yearKey));
  const includedPrestationSet = new Set(getIncludedPrestationIds(indicatorKey, yearKey));
  // AT/MP: when prestations are included, also consider their parent regimes for contributor-based numerator.
  if (indicatorKey === 'ind_25_atmp' && includeCotisants && includedPrestationSet.size) {{
    (prestationRows || []).forEach(row => {{
      if (!row || !includedPrestationSet.has(row.programme_id)) return;
      if (row.parent_regime_id) includedRegimeSet.add(row.parent_regime_id);
    }});
  }}
  const instMap = {{}};

  function ensureRegime(instEntry, regimeCode, regimeName) {{
    const key = String(regimeCode || '');
    if (!instEntry.regimes[key]) {{
      instEntry.regimes[key] = {{
        code: regimeCode || '',
        name: regimeName || regimeCode || '',
        cotisants: 0,
        beneficiaires: 0,
        prestations: {{}},
      }};
    }}
    return instEntry.regimes[key];
  }}

  function ensureInstitution(instCode) {{
    const key = String(instCode || '');
    if (!instMap[key]) {{
      instMap[key] = {{
        code: key,
        regimes: {{}},
      }};
    }}
    return instMap[key];
  }}

  if (includeCotisants) {{
    (regimeRows || []).forEach(row => {{
      if (Number(row.annee) !== yearNum) return;
      if (!includedRegimeSet.has(row.programme_id)) return;
      const value = Number(row.cotisants || 0);
      if (!Number.isFinite(value) || value <= 0) return;
      const instEntry = ensureInstitution(row.institution || '');
      const regime = ensureRegime(instEntry, row.regime_code, row.nom_regime || NOM_COURT[row.regime_code] || row.regime_code);
      regime.cotisants += value;
    }});
  }}

  if (includeBeneficiaires) {{
    (prestationRows || []).forEach(row => {{
      if (Number(row.annee) !== yearNum) return;
      if (!includedPrestationSet.has(row.programme_id)) return;
      const value = Number(row.beneficiaires || 0);
      if (!Number.isFinite(value) || value <= 0) return;
      const instEntry = ensureInstitution(row.institution || '');
      const regime = ensureRegime(instEntry, row.regime_code, NOM_COURT[row.regime_code] || row.regime_code);
      regime.beneficiaires += value;
      const pKey = String(row.nom_prestation || '');
      regime.prestations[pKey] = (regime.prestations[pKey] || 0) + value;
    }});
  }}

  const institutions = Object.values(instMap).map(inst => {{
    const regimes = Object.values(inst.regimes).map(reg => {{
      const total = (includeCotisants ? reg.cotisants : 0) + (includeBeneficiaires ? reg.beneficiaires : 0);
      const prestations = Object.keys(reg.prestations || {{}}).map(name => {{
        return {{ name: name, value: Number(reg.prestations[name] || 0) }};
      }}).sort((a, b) => (b.value - a.value) || String(a.name).localeCompare(String(b.name), 'fr', {{ sensitivity: 'base' }}));
      return {{
        code: reg.code,
        name: reg.name,
        cotisants: reg.cotisants,
        beneficiaires: reg.beneficiaires,
        total: total,
        prestations: prestations,
      }};
    }}).filter(r => r.total > 0)
      .sort((a, b) => (b.total - a.total) || String(a.name).localeCompare(String(b.name), 'fr', {{ sensitivity: 'base' }}));
    const total = regimes.reduce((acc, r) => acc + Number(r.total || 0), 0);
    return {{
      code: inst.code,
      total: total,
      regimes: regimes,
    }};
  }}).filter(i => i.total > 0)
    .sort((a, b) => (b.total - a.total) || String(a.code).localeCompare(String(b.code), 'fr', {{ sensitivity: 'base' }}));

  const total = institutions.reduce((acc, inst) => acc + Number(inst.total || 0), 0);
  let ruleText = 'Addition des bénéficiaires des prestations incluses.';
  if (metricSpec.metricKey === 'cotisants_estimes') {{
    ruleText = 'Addition des cotisants des régimes inclus.';
  }} else if (metricSpec.metricKey === 'couverts_bruts_estimes') {{
    ruleText = 'Addition des cotisants (régimes inclus) + bénéficiaires (prestations incluses).';
  }}

  return {{
    year: yearNum,
    total: total,
    institutions: institutions,
    includeCotisants: includeCotisants,
    includeBeneficiaires: includeBeneficiaires,
    includedRegimesCount: includedRegimeSet.size,
    includedPrestationsCount: includedPrestationSet.size,
    ruleText: ruleText,
  }};
}}

function getNumeratorYearSummaries(indicatorKey, regimeRows, prestationRows, metricSpec) {{
  const yearsAll = getOddAvailableYears();
  return yearsAll.map(y => buildNumeratorYearSummary(indicatorKey, y, regimeRows, prestationRows, metricSpec));
}}

function renderIndicateurs() {{
  const payload = INDICATEURS_DATA || {{}};
  const indicatorKey = getCurrentOddIndicator();
  const yearKey = getCurrentOddYear();
  const selectedYear = Number(yearKey);
  const indicatorLabel = ODD_INDICATOR_LABELS[indicatorKey] || indicatorKey;
  const metricSpec = getOddIndicatorNumeratorSpec(indicatorKey);
  const regimeRows = payload.rows_regimes || [];
  const prestationRows = payload.rows_prestations || [];

  const numHost = document.getElementById('ind-numerateurs');
  const contextHost = document.getElementById('odd-indicator-context');
  if (!numHost) return;

  const summaries = getNumeratorYearSummaries(indicatorKey, regimeRows, prestationRows, metricSpec);
  if (!summaries.length) {{
    numHost.innerHTML = '<p class="empty">Aucune donnée disponible.</p>';
    if (contextHost) contextHost.innerHTML = '<strong>Indicateur en cours :</strong> ' + escapeHtml(indicatorLabel);
    return;
  }}

  const yearsAll = summaries.map(s => s.year);
  const displayYear = yearsAll.includes(selectedYear) ? selectedYear : yearsAll[yearsAll.length - 1];
  if (contextHost) {{
    contextHost.innerHTML = '<strong>Indicateur en cours :</strong> ' + escapeHtml(indicatorLabel) +
      ' &nbsp;|&nbsp; <strong>Numérateur :</strong> ' + escapeHtml(metricSpec.numeratorName || metricSpec.metricLabel) +
      '<br><small>' + escapeHtml(metricSpec.numeratorDefinition || '') + '</small>';
  }}
  const numCards = summaries.map(summary => {{
    const instCount = (summary.institutions || []).length;
    const sublabelHtml =
      escapeHtml(instCount + ' institution' + (instCount > 1 ? 's' : '') + ' incluse' + (instCount > 1 ? 's' : '')) + '<br>' +
      escapeHtml(summary.includedRegimesCount + ' régime(s) inclus') + '<br>' +
      escapeHtml(summary.includedPrestationsCount + ' prestation(s) incluses');
    return {{
      year: summary.year,
      label: 'Année ' + summary.year,
      sublabelHtml: sublabelHtml,
      value: fmtInt(summary.total),
      icon: '🎯',
      selected: String(summary.year) === String(displayYear),
    }};
  }});
  numHost.innerHTML = numCards.map(card =>
    '<div class="kpi-card kpi-card-numerateur' + (card.selected ? ' kpi-card-selected-year' : '') + '">' +
      '<div class="kpi-icon">' + card.icon + '</div>' +
      '<div class="kpi-label">' + escapeHtml(card.label) + '</div>' +
      '<div class="kpi-value">' + escapeHtml(card.value) + '</div>' +
      '<div class="kpi-sublabel">' + card.sublabelHtml + '</div>' +
    '</div>'
  ).join('');
  renderActiveDenominatorViews();
}}

// Mise à jour en place du panneau après un changement de select — sans reconstruire le DOM
function _patchOddDecisionTable(changedNodeId, indicatorKey, yearKey) {{
  const host = document.getElementById('odd-decision-table');
  if (!host) return;
  const maps = buildOddNodeMaps();
  const nodeMap = maps.nodeMap || {{}};
  const memo = {{}};

  // 1. Mettre à jour chaque select : disabled + valeur sélectionnée
  host.querySelectorAll('select[data-odd-id]').forEach(function(sel) {{
    const nodeId = sel.getAttribute('data-odd-id');
    const node = nodeMap[nodeId];
    if (!node) return;
    const parentEff = node.parent_id ? getEffectiveDecisionById(node.parent_id, indicatorKey, yearKey, nodeMap, memo) : '';
    const isLockedByParent = parentEff === 'entierement_inclus' || parentEff === 'entierement_exclus' || parentEff === 'inclus' || parentEff === 'exclus';
    sel.disabled = isLockedByParent || !ODD_DECISION_EDIT_MODE;
    const decision = isLockedByParent
      ? getEffectiveDecisionById(nodeId, indicatorKey, yearKey, nodeMap, memo)
      : getDecisionForProgram(node, indicatorKey, yearKey);
    if (sel.value !== decision) sel.value = decision;
  }});

  // 2. Mettre à jour les badges "Appliqué" (data-badge-applied) et "Proposition" (data-badge-proposal)
  host.querySelectorAll('[data-badge-node]').forEach(function(badge) {{
    const nodeId = badge.getAttribute('data-badge-node');
    const btype = badge.getAttribute('data-badge-type');
    const node = nodeMap[nodeId];
    if (!node) return;
    let newVal, newLabel;
    if (btype === 'applied') {{
      newVal = getEffectiveDecisionById(nodeId, indicatorKey, yearKey, nodeMap, memo);
      newLabel = (typeof getDecisionLabel === 'function') ? getDecisionLabel(newVal, node.type) : newVal;
      badge.className = badge.className.replace(/\b(entierement_inclus|entierement_exclus|autres|inclus|exclus|inclus_avec_reserve|exclu_nature|exclu_non_statutaire|exclu_hors_indicateur|en_discussion)\b/g, '').trim() + ' odd-badge ' + newVal;
      badge.textContent = newLabel;
    }} else if (btype === 'proposal') {{
      const proposal = (node.propositions && node.propositions[indicatorKey]) || node.proposition || 'en_discussion';
      newVal = proposal;
      newLabel = (typeof getDecisionLabel === 'function') ? getDecisionLabel(newVal, node.type) : newVal;
      badge.className = badge.className.replace(/\b(entierement_inclus|entierement_exclus|autres|inclus|exclus|inclus_avec_reserve|exclu_nature|exclu_non_statutaire|exclu_hors_indicateur|en_discussion)\b/g, '').trim() + ' odd-badge odd-badge-proposal ' + newVal;
      badge.textContent = 'Proposition : ' + newLabel;
    }}
  }});

  // 3. Mettre à jour le verrouillage parent sur les labels
  host.querySelectorAll('[data-lock-node]').forEach(function(el) {{
    const nodeId = el.getAttribute('data-lock-node');
    const node = nodeMap[nodeId];
    if (!node) return;
    const parentEff = node.parent_id ? getEffectiveDecisionById(node.parent_id, indicatorKey, yearKey, nodeMap, memo) : '';
    const isLocked = parentEff === 'entierement_inclus' || parentEff === 'entierement_exclus' || parentEff === 'inclus' || parentEff === 'exclus';
    el.style.display = isLocked ? '' : 'none';
  }});

  // 4. Résumé
  const summaryEl = document.getElementById('odd-decision-summary');
  if (summaryEl) {{
    const includedReg = (typeof getIncludedRegimeIds === 'function') ? getIncludedRegimeIds(indicatorKey, yearKey).length : '?';
    const includedPrest = (typeof getIncludedPrestationIds === 'function') ? getIncludedPrestationIds(indicatorKey, yearKey).length : '?';
    const indicatorLabel = ODD_INDICATOR_LABELS[indicatorKey] || indicatorKey;
    summaryEl.textContent = indicatorLabel + ' · ' + yearKey + ' · édition : ' + includedReg + ' régime(s) inclus, ' + includedPrest + ' prestation(s) incluses.';
  }}
}}

function renderOddDecisionPanel() {{
  const host = document.getElementById('odd-decision-table');
  const summaryEl = document.getElementById('odd-decision-summary');
  const resetBtn = document.getElementById('odd-decisions-reset');
  const indicatorSelect = document.getElementById('odd-indicator-select');
  const yearSelect = document.getElementById('odd-year-select');
  const viewBtn = document.getElementById('odd-decision-view-toggle');
  const editOpenBtn = document.getElementById('odd-decision-edit-open');
  const closeBtn = document.getElementById('odd-decision-close');
  const decisionPanel = document.getElementById('odd-decision-panel');
  const modeBadge = document.getElementById('odd-decision-mode-badge');
  const saveBtn = document.getElementById('odd-decisions-save');
  if (!host) return;

  // ── Sélecteur indicateur ──────────────────────────────────────────────────
  if (indicatorSelect && !indicatorSelect.dataset.ready) {{
    indicatorSelect.innerHTML = (ODD_INDICATORS || []).map(item =>
      '<option value="' + escapeHtml(item.key) + '">' + escapeHtml(item.label) + '</option>'
    ).join('');
    indicatorSelect.value = CURRENT_ODD_INDICATOR;
    indicatorSelect.addEventListener('change', function() {{
      CURRENT_ODD_INDICATOR = this.value || 'global_131';
      // fermer le panneau + quitter édition si ouvert
      if (decisionPanel) decisionPanel.classList.remove('visible');
      ODD_DECISION_EDIT_MODE = false;
      ODD_DECISIONS_DRAFT = {{}};
      renderIndicateurs();
      renderOddBranchesVisual();
      renderOddDecisionPanel();
    }});
    indicatorSelect.dataset.ready = '1';
  }}
  if (indicatorSelect && indicatorSelect.value) {{
    CURRENT_ODD_INDICATOR = indicatorSelect.value;
  }}

  // ── Sélecteur année ───────────────────────────────────────────────────────
  const availableYears = getOddAvailableYears();
  if (yearSelect && !yearSelect.dataset.ready) {{
    yearSelect.innerHTML = availableYears.map(y =>
      '<option value="' + escapeHtml(String(y)) + '">' + escapeHtml(String(y)) + '</option>'
    ).join('');
    const defaultYear = getCurrentOddYear() || (availableYears.length ? String(availableYears[availableYears.length - 1]) : '');
    yearSelect.value = defaultYear;
    CURRENT_ODD_YEAR = yearSelect.value || defaultYear;
    yearSelect.addEventListener('change', function() {{
      const newYear = this.value || '';
      if (ODD_DECISION_EDIT_MODE) {{
        // bloquer le changement tant qu'on n'a pas sauvegardé ou annulé
        alert("Des modifications sont en cours. Veuillez sauvegarder ou annuler avant de changer d'annee.");
        this.value = CURRENT_ODD_YEAR; // remettre l'ancienne valeur
        return;
      }}
      CURRENT_ODD_YEAR = newYear;
      // fermer et rouvrir en vue si panneau ouvert
      if (decisionPanel && decisionPanel.classList.contains('visible')) {{
        decisionPanel.classList.remove('visible');
      }}
      renderIndicateurs();
      renderOddBranchesVisual();
      renderOddDecisionPanel();
    }});
    yearSelect.dataset.ready = '1';
  }}
  if (yearSelect && yearSelect.value) {{
    CURRENT_ODD_YEAR = yearSelect.value;
  }}

  // ── Bouton Consulter ──────────────────────────────────────────────────────
  if (viewBtn && !viewBtn.dataset.bound) {{
    viewBtn.addEventListener('click', function(evt) {{
      evt.preventDefault(); evt.stopPropagation();
      const details = viewBtn.closest('details');
      if (details) details.open = true;
      if (!decisionPanel) return;
      if (ODD_DECISION_EDIT_MODE) {{
        alert("Des modifications sont en cours. Veuillez sauvegarder ou fermer le panneau.");
        return;
      }}
      ODD_DECISION_EDIT_MODE = false;
      decisionPanel.classList.add('visible');
      renderOddDecisionPanel();
    }});
    viewBtn.dataset.bound = '1';
  }}

  // ── Bouton Éditer (ouvre directement en mode édition) ─────────────────────
  if (editOpenBtn && !editOpenBtn.dataset.bound) {{
    editOpenBtn.addEventListener('click', function(evt) {{
      evt.preventDefault(); evt.stopPropagation();
      const details = editOpenBtn.closest('details');
      if (details) details.open = true;
      if (decisionPanel.classList.contains('visible') && ODD_DECISION_EDIT_MODE) {{
        alert("Des modifications sont deja en cours. Sauvegardez ou fermez d'abord.");
        return;
      }}
      ODD_DECISIONS_DRAFT = cloneDecisionMap(CURRENT_ODD_DECISIONS);
      ODD_DECISION_EDIT_MODE = true;
      decisionPanel.classList.add('visible');
      renderOddDecisionPanel();
    }});
    editOpenBtn.dataset.bound = '1';
  }}

  // ── Bouton Fermer ─────────────────────────────────────────────────────────
  if (closeBtn && !closeBtn.dataset.bound) {{
    closeBtn.addEventListener('click', function(evt) {{
      evt.preventDefault(); evt.stopPropagation();
      if (ODD_DECISION_EDIT_MODE) {{
        if (!confirm("Des modifications non sauvegardees seront perdues. Fermer quand meme ?")) return;
      }}
      ODD_DECISION_EDIT_MODE = false;
      ODD_DECISIONS_DRAFT = {{}};
      if (decisionPanel) decisionPanel.classList.remove('visible');
      renderOddDecisionPanel();
    }});
    closeBtn.dataset.bound = '1';
  }}

  // ── Badge mode ────────────────────────────────────────────────────────────
  const panelVisible = decisionPanel && decisionPanel.classList.contains('visible');
  if (modeBadge) {{
    modeBadge.textContent = ODD_DECISION_EDIT_MODE ? 'Édition' : 'Consultation';
    modeBadge.classList.toggle('edit', ODD_DECISION_EDIT_MODE);
  }}

  // ── Bouton Sauvegarder ────────────────────────────────────────────────────
  if (saveBtn) {{
    saveBtn.style.display = (panelVisible && ODD_DECISION_EDIT_MODE) ? 'inline-flex' : 'none';
    saveBtn.disabled = !ODD_DECISION_EDIT_MODE;
    if (!saveBtn.dataset.bound) {{
      saveBtn.addEventListener('click', function(evt) {{
        evt.preventDefault(); evt.stopPropagation();
        if (!ODD_DECISION_EDIT_MODE) return;
        CURRENT_ODD_DECISIONS = cloneDecisionMap(ODD_DECISIONS_DRAFT);
        saveOddDecisions();
        ODD_DECISION_EDIT_MODE = false;
        ODD_DECISIONS_DRAFT = {{}};
        renderIndicateurs();
        renderOddBranchesVisual();
        renderOddDecisionPanel();
      }});
      saveBtn.dataset.bound = '1';
    }}
  }}

  // ── Bouton Réinitialiser ──────────────────────────────────────────────────
  if (resetBtn) {{
    resetBtn.disabled = !ODD_DECISION_EDIT_MODE;
  }}

  // ── Construction de la hiérarchie ─────────────────────────────────────────
  const indicatorKey = getCurrentOddIndicator();
  const yearKey = getCurrentOddYear();
  const indicatorLabel = ODD_INDICATOR_LABELS[indicatorKey] || indicatorKey;
  const maps = buildOddNodeMaps();
  const nodeMap = maps.nodeMap || {{}};
  const childrenMap = maps.childrenMap || {{}};
  const memo = {{}};
  const roots = Object.keys(nodeMap)
    .filter(id => nodeMap[id] && nodeMap[id].type === 'institution_ess')
    .sort((a, b) => String(nodeMap[a].programme || '').localeCompare(String(nodeMap[b].programme || ''), 'fr', {{ sensitivity: 'base' }}));

  // Mémoriser les nœuds actuellement ouverts avant de reconstruire le HTML
  const openNodeIds = new Set();
  host.querySelectorAll('details[data-node-id][open]').forEach(function(d) {{
    openNodeIds.add(d.getAttribute('data-node-id'));
  }});

  if (!roots.length) {{
    host.innerHTML = '<p class="empty">Aucun programme à instruire.</p>';
    return;
  }}

  function renderSelect(nodeId, isLocked, selectedDecision) {{
    const node = nodeMap[nodeId];
    const decision = selectedDecision || getDecisionForProgram(node, indicatorKey, yearKey);
    const options = ODD_DECISION_OPTIONS_BY_TYPE[node.type] || ODD_DECISION_OPTIONS_BY_TYPE.prestation_ess;
    const disabledAttr = (isLocked || !ODD_DECISION_EDIT_MODE) ? ' disabled' : '';
    return '<select data-odd-id="' + escapeHtml(nodeId) + '"' + disabledAttr + '>' +
      options.map(opt =>
        '<option value="' + escapeHtml(opt.value) + '"' + (opt.value === decision ? ' selected' : '') + '>' + escapeHtml(opt.label) + '</option>'
      ).join('') +
      '</select>';
  }}

  function renderNode(nodeId, level) {{
    const node = nodeMap[nodeId];
    if (!node) return '';
    const proposal = (node.propositions && node.propositions[indicatorKey]) || node.proposition || 'en_discussion';
    const rationale = getRationaleForProgram(node, indicatorKey);
    const effective = getEffectiveDecisionById(nodeId, indicatorKey, yearKey, nodeMap, memo);
    const parentEff = (node.parent_id && nodeMap[node.parent_id]) ? getEffectiveDecisionById(node.parent_id, indicatorKey, yearKey, nodeMap, memo) : '';
    const isLockedByParent = parentEff === 'entierement_inclus' || parentEff === 'entierement_exclus' || parentEff === 'inclus' || parentEff === 'exclus';
    const criteria = node.criteria
      ? 'C1 ' + escapeHtml(node.criteria.c1_cash || 'N/D') + ' · C2 ' + escapeHtml(node.criteria.c2_statutaire || 'N/D') + ' · C3 ' + escapeHtml(node.criteria.c3_etat || 'N/D') + ' · C4 ' + escapeHtml(node.criteria.c4_permanent || 'N/D') + ' · C5 ' + escapeHtml(node.criteria.c5_financement || 'N/D')
      : '';
    const children = (childrenMap[nodeId] || []).slice().sort((a, b) => {{
      const na = nodeMap[a] || {{}};
      const nb = nodeMap[b] || {{}};
      const order = {{ regime_ess: 1, prestation_ess: 2 }};
      const oa = order[na.type] || 9;
      const ob = order[nb.type] || 9;
      if (oa !== ob) return oa - ob;
      return String(na.programme || '').localeCompare(String(nb.programme || ''), 'fr', {{ sensitivity: 'base' }});
    }});
    const title = (node.type === 'institution_ess')
      ? (node.institution + ' — ' + (node.programme || node.institution))
      : ((node.type === 'regime_ess')
        ? ((NOM_COURT[node.regime_code] || node.regime_code || '') + ' — ' + (node.programme || ''))
        : (node.programme || 'Prestation'));
    const kindLabel = (node.type === 'institution_ess')
      ? 'Institution'
      : ((node.type === 'regime_ess') ? 'Régime' : 'Prestation');
    const hasChildren = children.length > 0;
    const headerMain = hasChildren
      ? ''
      : (
        '<div class="odd-node-main"><span class="odd-node-kind type-' + escapeHtml(node.type || '') + '">' + escapeHtml(kindLabel) + '</span><span class="odd-node-title">' + escapeHtml(title) + '</span>' +
          (node.type === 'prestation_ess' ? '<span class="odd-impact"> — ' + escapeHtml(node.institution || '') + ' / ' + escapeHtml(node.regime_code || '') + '</span>' : '') +
        '</div>'
      );
    const headerBadges = hasChildren
      ? ''
      : (
        '<span class="odd-badge odd-badge-proposal ' + escapeHtml(proposal) + '" data-badge-node="' + escapeHtml(nodeId) + '" data-badge-type="proposal">Proposition : ' + escapeHtml(getDecisionLabel(proposal, node.type)) + '</span> ' +
        '<span class="odd-badge ' + escapeHtml(effective) + '" data-badge-node="' + escapeHtml(nodeId) + '" data-badge-type="applied">Appliqué : ' + escapeHtml(getDecisionLabel(effective, node.type)) + '</span>'
      );

    const header =
      '<div class="odd-node-header level-' + level + '">' +
        headerMain +
        '<div class="odd-node-controls">' + renderSelect(nodeId, isLockedByParent, isLockedByParent ? effective : null) + '</div>' +
      '</div>' +
      '<div class="odd-node-meta">' +
        headerBadges +
        (isLockedByParent ? '<div class="odd-impact" data-lock-node="' + escapeHtml(nodeId) + '">Décision verrouillée par le niveau supérieur.</div>' : '<div class="odd-impact" data-lock-node="' + escapeHtml(nodeId) + '" style="display:none">Décision verrouillée par le niveau supérieur.</div>') +
        (rationale ? '<div class="odd-impact">' + escapeHtml(rationale) + '</div>' : '') +
        (criteria ? '<div class="odd-impact">' + criteria + '</div>' : '') +
      '</div>';
    const summary = '<summary>' +
      '<div class="odd-summary-top">' +
        '<span class="odd-summary-title"><span class="odd-node-kind type-' + escapeHtml(node.type || '') + '">' + escapeHtml(kindLabel) + '</span><span class="odd-node-title">' + escapeHtml(title) + '</span></span>' +
        '<span class="odd-badge ' + escapeHtml(effective) + '" data-badge-node="' + escapeHtml(nodeId) + '" data-badge-type="applied">' + escapeHtml(getDecisionLabel(effective, node.type)) + '</span>' +
      '</div>' +
      '<div class="odd-summary-bottom">' +
        '<span class="odd-badge odd-badge-proposal ' + escapeHtml(proposal) + '" data-badge-node="' + escapeHtml(nodeId) + '" data-badge-type="proposal">Proposition : ' + escapeHtml(getDecisionLabel(proposal, node.type)) + '</span>' +
        (rationale ? '<span class="odd-summary-rationale">' + escapeHtml(rationale) + '</span>' : '') +
      '</div>' +
    '</summary>';

    if (node.type === 'prestation_ess' && !children.length) {{
      return '<div class="odd-node level-' + level + ' type-' + escapeHtml(node.type || '') + '">' + header + '</div>';
    }}
    const openAttr = openNodeIds.has(nodeId) ? ' open' : '';
    return '<details class="odd-node level-' + level + ' type-' + escapeHtml(node.type || '') + '" data-node-id="' + escapeHtml(nodeId) + '"' + openAttr + '>' +
      summary +
      header +
      '<div class="odd-node-children">' + children.map(childId => renderNode(childId, level + 1)).join('') + '</div>' +
    '</details>';
  }}

  const hierarchyHtml = roots.map(id => renderNode(id, 0)).join('');
  host.innerHTML = '<div class="odd-hierarchy">' + hierarchyHtml + '</div>';
  // Forcer programmatiquement l'état ouvert (garantie fiable en plus de l'attribut open)
  openNodeIds.forEach(function(nid) {{
    const el = host.querySelector('details[data-node-id="' + nid.replace(/"/g, '\\"') + '"]');
    if (el) el.open = true;
  }});

  host.querySelectorAll('select[data-odd-id]').forEach(sel => {{
    sel.addEventListener('change', function() {{
      if (!ODD_DECISION_EDIT_MODE) return;
      const id = this.getAttribute('data-odd-id');
      if (!id) return;
      const decisionMap = getActiveOddDecisionMap();
      decisionMap[getOddDecisionStorageKey(id, indicatorKey, yearKey)] = this.value;
      // Mise à jour en place : ne pas reconstruire tout le panneau, juste patcher les éléments affectés
      _patchOddDecisionTable(id, indicatorKey, yearKey);
      renderIndicateurs();
      renderOddBranchesVisual();
      renderActiveDenominatorViews();
    }});
  }});

  if (summaryEl) {{
    const includedReg = getIncludedRegimeIds(indicatorKey, yearKey).length;
    const includedPrest = getIncludedPrestationIds(indicatorKey, yearKey).length;
    const modeLabel = ODD_DECISION_EDIT_MODE ? 'édition' : 'consultation';
    summaryEl.textContent = indicatorLabel + ' · ' + yearKey + ' · ' + modeLabel + ' : ' + includedReg + ' régime(s) inclus, ' + includedPrest + ' prestation(s) incluses.';
  }}
  if (resetBtn && !resetBtn.dataset.bound) {{
    resetBtn.addEventListener('click', function() {{
      if (!ODD_DECISION_EDIT_MODE) return;
      const activeKey = getCurrentOddIndicator();
      const activeYear = getCurrentOddYear();
      const decisionMap = getActiveOddDecisionMap();
      Object.keys(decisionMap || {{}}).forEach(k => {{
        if (k.endsWith('::' + activeKey + '::' + activeYear)) delete decisionMap[k];
      }});
      ODD_DECISIONS_DRAFT = cloneDecisionMap(decisionMap);
      renderIndicateurs();
      renderOddBranchesVisual();
      renderOddDecisionPanel();
    }});
    resetBtn.dataset.bound = '1';
  }}
}}

function renderOddBranchesVisual() {{
  const visualGrid = document.getElementById('odd-numerator-visual-grid');
  const breakdownGrid = document.getElementById('odd-numerator-breakdown-grid');
  const legendHost = document.getElementById('odd-numerator-legend');
  if (!visualGrid || !breakdownGrid) return;

  const indicatorKey = getCurrentOddIndicator();
  const metricSpec = getOddIndicatorNumeratorSpec(indicatorKey);
  const payload = INDICATEURS_DATA || {{}};
  const summaries = getNumeratorYearSummaries(
    indicatorKey,
    payload.rows_regimes || [],
    payload.rows_prestations || [],
    metricSpec
  );

  if (!summaries.length) {{
    visualGrid.innerHTML = '<p class="empty">Aucune donnée disponible.</p>';
    breakdownGrid.innerHTML = '<p class="empty">Aucune donnée disponible.</p>';
    return;
  }}

  // Afficher la règle une seule fois avant la grille
  const ruleHost = document.getElementById('odd-numerator-rule');
  if (ruleHost) {{
    const ruleText = summaries[0] && summaries[0].ruleText ? summaries[0].ruleText : '';
    ruleHost.textContent = ruleText;
    ruleHost.style.display = ruleText ? '' : 'none';
  }}

  // Construire la carte couleurs cohérente sur toutes les années
  const palette = ['#2c5282', '#2f855a', '#d69e2e', '#9f7aea', '#dd6b20', '#319795', '#718096'];
  const instCodes = [];
  summaries.forEach(s => {{
    (s.institutions || []).forEach(inst => {{
      if (inst.code && !instCodes.includes(inst.code)) instCodes.push(inst.code);
    }});
  }});
  const colorMap = {{}};
  instCodes.forEach((code, i) => {{ colorMap[code] = palette[i % palette.length]; }});

  // Construire les blocs-années : seulement le graphique (l'année est sur l'axe X)
  visualGrid.innerHTML = summaries.map(s =>
    '<div class="odd-year-block">' +
      '<div id="odd-year-chart-' + escapeHtml(String(s.year)) + '" style="height:240px;"></div>' +
    '</div>'
  ).join('');

  // Calculer l'échelle Y commune sur toutes les années
  const yMaxNum = summaries.reduce((m, s) => Math.max(m, s.total || 0), 0) * 1.08;

  summaries.forEach(summary => {{
    const chartId = 'odd-year-chart-' + String(summary.year);
    const insts = summary.institutions || [];
    if (!insts.length) {{
      const host = document.getElementById(chartId);
      if (host) host.innerHTML = '<p class="empty">Aucune composante incluse.</p>';
      return;
    }}
    const traces = insts.map(inst => {{
      const val = Number(inst.total || 0);
      return {{
        type: 'bar',
        name: inst.code || 'N/D',
        x: [String(summary.year)],
        y: [val],
        marker: {{ color: colorMap[inst.code] || '#718096' }},
        text: [fmtInt(val)],
        textposition: 'inside',
        insidetextanchor: 'middle',
        hovertemplate: '%{{fullData.name}}: %{{y:,}}<extra></extra>',
      }};
    }});
    Plotly.newPlot(chartId, traces, {{
      barmode: 'stack',
      margin: {{ t: 8, r: 8, b: 38, l: 50 }},
      yaxis: {{ separatethousands: true, range: [0, yMaxNum] }},
      xaxis: {{ type: 'category', automargin: true }},
      showlegend: false,
      paper_bgcolor: '#ffffff',
      plot_bgcolor: '#ffffff',
    }}, {{ responsive: true }});
  }});

  // Légende partagée unique sous la grille
  if (legendHost) {{
    legendHost.innerHTML = instCodes.map(code =>
      '<span class="odd-legend-item">' +
        '<span class="odd-legend-swatch" style="background:' + (colorMap[code] || '#718096') + '"></span>' +
        escapeHtml(code) +
      '</span>'
    ).join('');
  }}

  breakdownGrid.innerHTML = summaries.map(summary => {{
    const institutionBlocks = (summary.institutions || []).map(inst => {{
      const regimeBlocks = (inst.regimes || []).map(reg => {{
        const prestationList = (reg.prestations || []).map(p =>
          '<li>Prestation ' + escapeHtml(p.name) + ' = ' + escapeHtml(fmtInt(p.value)) + '</li>'
        ).join('');
        const cotLine = summary.includeCotisants
          ? '<div class="odd-calc-line">Cotisants régime = ' + escapeHtml(fmtInt(reg.cotisants)) + '</div>'
          : '';
        const benefLine = summary.includeBeneficiaires
          ? '<div class="odd-calc-line">Bénéficiaires régime = ' + escapeHtml(fmtInt(reg.beneficiaires)) + '</div>'
          : '';
        return '<details>' +
          '<summary>Régime ' + escapeHtml(reg.name || reg.code || 'N/D') + ' = ' + escapeHtml(fmtInt(reg.total)) + '</summary>' +
          cotLine + benefLine +
          (prestationList ? '<ul>' + prestationList + '</ul>' : '') +
        '</details>';
      }}).join('');
      return '<details open>' +
        '<summary>Institution ' + escapeHtml(inst.code || 'N/D') + ' = ' + escapeHtml(fmtInt(inst.total)) + '</summary>' +
        regimeBlocks +
      '</details>';
    }}).join('');

    return '<div class="odd-year-block">' +
      '<h5>Année ' + escapeHtml(String(summary.year)) + '</h5>' +
      '<div class="odd-year-total">Numérateur = ' + escapeHtml(fmtInt(summary.total)) + '</div>' +
      '<div class="odd-calc-rule">' + escapeHtml(summary.ruleText) + '</div>' +
      '<div class="odd-calc-tree">' + (institutionBlocks || '<p class="empty">Aucune composante incluse.</p>') + '</div>' +
    '</div>';
  }}).join('');
}}

function fmtPlain(value) {{
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "N/D";
  return Number(value).toLocaleString('fr-FR', {{ maximumFractionDigits: 0 }});
}}

function setDenomStatus(text) {{
  const el = document.getElementById('denom-status');
  if (el) el.textContent = text;
}}

function getActiveDenominatorSpec(indicatorKey) {{
  const key = indicatorKey || getCurrentOddIndicator();
  return DENOMINATOR_BY_INDICATOR[key] || DENOMINATOR_BY_INDICATOR.global_131;
}}

function getDenominatorValueFromRow(row, spec) {{
  if (!row || !spec) return null;
  const val = Number(row[spec.rowField]);
  return Number.isFinite(val) ? val : null;
}}

function setDenomEditMode(isEdit) {{
  DENOM_EDIT_MODE = !!isEdit;
  const btnConsulter = document.getElementById('denom-btn-consulter');
  const btnEditer = document.getElementById('denom-btn-editer');
  const refreshBtn = document.getElementById('denom-refresh');
  const saveBtn = document.getElementById('denom-save');
  // Consulter = bleu quand actif (mode consultation), Éditer = bleu quand actif (mode édition)
  if (btnConsulter) {{
    btnConsulter.style.background = DENOM_EDIT_MODE ? '' : '#2c5282';
    btnConsulter.style.color = DENOM_EDIT_MODE ? '' : '#fff';
    btnConsulter.style.borderColor = DENOM_EDIT_MODE ? '' : '#2c5282';
  }}
  if (btnEditer) {{
    btnEditer.style.background = DENOM_EDIT_MODE ? '#2c5282' : '';
    btnEditer.style.color = DENOM_EDIT_MODE ? '#fff' : '';
    btnEditer.style.borderColor = DENOM_EDIT_MODE ? '#2c5282' : '';
  }}
  if (refreshBtn) refreshBtn.disabled = false;
  if (saveBtn) {{
    saveBtn.style.display = DENOM_EDIT_MODE ? 'inline-flex' : 'none';
    saveBtn.disabled = !DENOM_EDIT_MODE;
  }}
  document.querySelectorAll('.denom-pack input[type="number"]').forEach(el => {{
    el.disabled = !DENOM_EDIT_MODE;
  }});
  document.querySelectorAll('.denom-pack input[type="radio"]').forEach(el => {{
    el.disabled = false;
  }});
  if (!DENOM_EDIT_MODE) DENOM_PENDING_CHANGES = false;
}}

function updateDenominatorPackVisibility(activeShortKey) {{
  const map = {{
    total: 'pack-total',
    active: 'pack-active',
    ret: 'pack-retraite',
    mat: 'pack-maternite',
  }};
  const activePackId = map[activeShortKey] || map.total;
  Object.values(map).forEach(id => {{
    const node = document.getElementById(id);
    if (!node) return;
    node.style.display = (id === activePackId) ? '' : 'none';
  }});
}}

function renderActiveDenominatorViews() {{
  const contextHost = document.getElementById('denom-active-context');
  const cardsHost = document.getElementById('denom-active-cards');
  const visualHost = document.getElementById('denom-active-visual-grid');
  if (!contextHost || !cardsHost || !visualHost) return;

  const indicatorKey = getCurrentOddIndicator();
  const indicatorLabel = ODD_INDICATOR_LABELS[indicatorKey] || indicatorKey;
  const spec = getActiveDenominatorSpec(indicatorKey);
  updateDenominatorPackVisibility(spec.shortKey);
  contextHost.innerHTML = '<strong>Indicateur en cours :</strong> ' + escapeHtml(indicatorLabel) +
    ' &nbsp;|&nbsp; <strong>Dénominateur :</strong> ' + escapeHtml(spec.label || '') +
    '<br><small>' + escapeHtml(spec.definition || '') + '</small>';

  const rows = (CURRENT_DENOM_ROWS || []).slice().sort((a, b) => Number(a.year) - Number(b.year));
  if (!rows.length) {{
    cardsHost.innerHTML = '<p class="empty">Aucun dénominateur calculé.</p>';
    visualHost.innerHTML = '<p class="empty">Aucun dénominateur calculé.</p>';
    return;
  }}

  cardsHost.innerHTML = rows.map(row => {{
    const value = getDenominatorValueFromRow(row, spec);
    return '<div class="kpi-card kpi-card-numerateur">' +
      '<div class="kpi-label">Année ' + escapeHtml(String(row.year)) + '</div>' +
      '<div class="kpi-value">' + escapeHtml(fmtPlain(value)) + '</div>' +
      '<div class="kpi-sublabel">' + escapeHtml(spec.label || '') + '</div>' +
    '</div>';
  }}).join('');

  visualHost.innerHTML = rows.map(row => {{
    return '<div class="odd-year-block">' +
      '<div id="denom-year-chart-' + escapeHtml(String(row.year)) + '" style="height:240px;"></div>' +
    '</div>';
  }}).join('');

  // Calculer l'échelle Y commune sur toutes les années
  const yMaxDenom = rows.reduce((m, row) => {{
    const v = getDenominatorValueFromRow(row, spec);
    return Math.max(m, v !== null ? Number(v) : 0);
  }}, 0) * 1.08;

  rows.forEach(row => {{
    const chartId = 'denom-year-chart-' + String(row.year);
    const value = getDenominatorValueFromRow(row, spec);
    const host = document.getElementById(chartId);
    if (!host) return;
    if (value === null) {{
      host.innerHTML = '<p class="empty">Valeur indisponible.</p>';
      return;
    }}
    Plotly.newPlot(chartId, [{{
      type: 'bar',
      x: [String(row.year)],
      y: [Number(value)],
      marker: {{ color: '#97266d' }},
      text: [fmtPlain(value)],
      textposition: 'inside',
      insidetextanchor: 'middle',
    }}], {{
      margin: {{ t: 8, r: 8, b: 38, l: 50 }},
      yaxis: {{ separatethousands: true, range: [0, yMaxDenom] }},
      xaxis: {{ type: 'category', automargin: true }},
      showlegend: false,
      paper_bgcolor: '#ffffff',
      plot_bgcolor: '#ffffff',
    }}, {{ responsive: true }});
  }});
}}

function canUseLocalDenomProxy() {{
  return typeof window !== 'undefined'
    && window.location
    && (window.location.protocol === 'http:' || window.location.protocol === 'https:');
}}

async function fetchTextWithFallback(directUrl, proxyPath) {{
  const attempts = [];
  if (proxyPath && canUseLocalDenomProxy()) attempts.push({{ url: proxyPath, label: 'proxy local' }});
  attempts.push({{ url: directUrl, label: 'source distante' }});
  let lastError = null;
  for (const attempt of attempts) {{
    try {{
      const res = await fetch(attempt.url);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const text = await res.text();
      return text;
    }} catch (err) {{
      lastError = new Error(attempt.label + ' : ' + String(err && err.message ? err.message : err));
    }}
  }}
  throw lastError || new Error('Impossible de récupérer la source');
}}

async function fetchJsonWithFallback(directUrl, proxyPath) {{
  const text = await fetchTextWithFallback(directUrl, proxyPath);
  const trimmed = (text || '').trim();
  if (!trimmed) throw new Error('Réponse vide');
  try {{
    return JSON.parse(trimmed);
  }} catch (_err) {{
    throw new Error('Réponse JSON invalide');
  }}
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
// API gratuite basée sur ONU WPP 2024, sans authentification.
// URL : https://www.populationpyramid.net/api/pp/180/{{YEAR}}/  (180 = M49 RDC)
// Réponses observées :
//  1) {{ females:[{{Age:"0-4",F:12345}}], males:[{{Age:"0-4",M:12345}}] }} (ancien format)
//  2) {{ female:[{{k:"0-4",v:9331.883}}], male:[{{k:"0-4",v:9421.39}}] }} (format compact, en milliers)
// Cache par année (une requête par année demandée).
window.__WPP_CACHE = window.__WPP_CACHE || {{}};

async function fetchWPPYear(year) {{
  const y = String(year);
  if (window.__WPP_CACHE[y]) return window.__WPP_CACHE[y];
  const url = 'https://www.populationpyramid.net/api/pp/180/' + y + '/';
  const proxy = '/api/denom/wpp?year=' + encodeURIComponent(y);
  const json = await fetchJsonWithFallback(url, proxy);
  const usesCompactSchema = Array.isArray(json.male) || Array.isArray(json.female);
  // Construire tableau : [{{ageStart, ageEnd, value}}]
  const parse = row => {{
    const label = String(row.Age || row.k || '').trim();
    if (label === '100+') return {{ ageStart: 100, ageEnd: 999 }};
    const parts = label.split('-');
    const ageStart = Number(parts[0]);
    const ageEnd = Number(parts[1] !== undefined ? parts[1] : parts[0]);
    return {{ ageStart, ageEnd }};
  }};
  const valueFor = (row, sex) => {{
    const rawSexValue = sex === 'M' ? row.M : row.F;
    if (rawSexValue !== undefined && rawSexValue !== null) return Number(rawSexValue) || 0;
    if (row.v !== undefined && row.v !== null) {{
      const raw = Number(row.v) || 0;
      return usesCompactSchema ? raw * 1000.0 : raw;
    }}
    return 0;
  }};
  const groups = [];
  const males   = Array.isArray(json.males)   ? json.males   : (Array.isArray(json.male) ? json.male : []);
  const females = Array.isArray(json.females) ? json.females : (Array.isArray(json.female) ? json.female : []);
  males.forEach(r => {{
    const ag = parse(r);
    if (!Number.isFinite(ag.ageStart) || !Number.isFinite(ag.ageEnd)) return;
    groups.push({{ ...ag, value: valueFor(r, 'M'), sex: 'M' }});
  }});
  females.forEach(r => {{
    const ag = parse(r);
    if (!Number.isFinite(ag.ageStart) || !Number.isFinite(ag.ageEnd)) return;
    groups.push({{ ...ag, value: valueFor(r, 'F'), sex: 'F' }});
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
  const text = await fetchTextWithFallback(url, '/api/denom/ilo');
  const trimmed = (text || '').trim();
  if (!trimmed) {{
    window.__ILO_CACHE = [];
    return window.__ILO_CACHE;
  }}
  let rows = [];
  try {{
    const json = JSON.parse(trimmed);
    rows = (Array.isArray(json.data) ? json.data : [])
      .filter(r => r.obs_value !== null && r.obs_value !== undefined)
      .map(r => ({{ year: Number(r.time), value: Number(r.obs_value) }}))
      .filter(r => Number.isFinite(r.year) && Number.isFinite(r.value));
  }} catch (_err) {{
    const parseCsvLine = (line) => (line.match(/("([^"]|"")*"|[^,]+)/g) || []).map(c => {{
      const v = String(c || '').trim();
      if (v.startsWith('"') && v.endsWith('"')) {{
        return v.slice(1, -1).replace(/""/g, '"');
      }}
      return v;
    }});
    const lines = trimmed.split(/\\r?\\n/).filter(Boolean);
    if (lines.length > 1) {{
      const header = parseCsvLine(lines[0]);
      const timeIdx = header.indexOf('time');
      const valIdx = header.indexOf('obs_value');
      if (timeIdx >= 0 && valIdx >= 0) {{
        rows = lines.slice(1)
          .map(parseCsvLine)
          .map(cols => ({{ year: Number(cols[timeIdx]), value: Number(cols[valIdx]) }}))
          .filter(r => Number.isFinite(r.year) && Number.isFinite(r.value));
      }}
    }}
  }}
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
  const safeMetricValue = async (sourceKey, metricKey, year, params) => {{
    try {{
      return await getMetricValue(sourceKey, metricKey, year, params, seriesCache);
    }} catch (err) {{
      const msg = String(err && err.message ? err.message : err);
      return {{ value: null, meta: 'Erreur API: ' + msg }};
    }}
  }};
  try {{
    for (let y = minYear; y <= maxYear; y += 1) {{
      const total = (y >= pTotal.yearStart && y <= pTotal.yearEnd)
        ? await safeMetricValue(srcTotal, 'population_totale', y, pTotal)
        : {{ value: null, meta: 'hors plage' }};
      const active = (y >= pActive.yearStart && y <= pActive.yearEnd)
        ? await safeMetricValue(srcActive, 'population_active', y, pActive)
        : {{ value: null, meta: 'hors plage' }};
      const retraite = (y >= pRet.yearStart && y <= pRet.yearEnd)
        ? await safeMetricValue(srcRet, 'population_retraite', y, pRet)
        : {{ value: null, meta: 'hors plage' }};
      const naissances = (y >= pMat.yearStart && y <= pMat.yearEnd)
        ? await safeMetricValue(srcMat, 'naissances', y, pMat)
        : {{ value: null, meta: 'hors plage' }};
      const femmes = (y >= pMat.yearStart && y <= pMat.yearEnd)
        ? await safeMetricValue(srcMat, 'femmes_accouche', y, pMat)
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
  CURRENT_DENOM_ROWS = outRows;
  renderActiveDenominatorViews();
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
  if (!document.getElementById('denom-active-cards')) return;

  // ── Chargement immédiat des données pré-calculées ─────────────────────────
  // Évite un écran vide au démarrage : CURRENT_DENOM_ROWS est rempli sans appel réseau.
  // Le bouton "Actualiser" mettra à jour depuis les API live.
  if (cfg.static_rows && cfg.static_rows.length) {{
    CURRENT_DENOM_ROWS = cfg.static_rows.slice();
    setDenomStatus('Données pré-chargées (BM 2019–2022). Cliquez sur Actualiser pour rafraîchir.');
  }}

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
  const btnConsulter = document.getElementById('denom-btn-consulter');
  const btnEditer = document.getElementById('denom-btn-editer');
  const saveBtn = document.getElementById('denom-save');
  if (btnConsulter && !btnConsulter.dataset.bound) {{
    btnConsulter.addEventListener('click', function(evt) {{
      evt.preventDefault(); evt.stopPropagation();
      const details = btnConsulter.closest('details');
      if (details) details.open = true;
      setDenomEditMode(false);
    }});
    btnConsulter.dataset.bound = '1';
  }}
  if (btnEditer && !btnEditer.dataset.bound) {{
    btnEditer.addEventListener('click', function(evt) {{
      evt.preventDefault(); evt.stopPropagation();
      const details = btnEditer.closest('details');
      if (details) details.open = true;
      setDenomEditMode(true);
    }});
    btnEditer.dataset.bound = '1';
  }}
  setDenomEditMode(false);
  if (saveBtn && !saveBtn.dataset.bound) {{
    saveBtn.addEventListener('click', function(evt) {{
      evt.preventDefault(); evt.stopPropagation();
      if (!DENOM_EDIT_MODE) return;
      DENOM_PENDING_CHANGES = false;
      computeDenominators();
    }});
    saveBtn.dataset.bound = '1';
  }}
  if (refreshBtn && !refreshBtn.dataset.bound) {{
    refreshBtn.addEventListener('click', function() {{
      computeDenominators();
    }});
    refreshBtn.dataset.bound = '1';
  }}

  document.querySelectorAll('.denom-pack input').forEach(el => {{
    el.addEventListener('change', () => {{
      // Les radios de source peuvent changer en mode vue (sélection visuelle)
      if (el.type === 'radio') {{
        applyAllConstraints();
        refreshMetricSources(sources);
        // En mode vue : actualisation automatique dès qu'on change la source
        if (!DENOM_EDIT_MODE) {{
          computeDenominators();
          return;
        }}
      }}
      if (!DENOM_EDIT_MODE) return;
      DENOM_PENDING_CHANGES = true;
      setDenomStatus('Modifications en attente — cliquez sur Sauvegarder.');
    }});
  }});

  // Afficher immédiatement les données statiques, puis ne pas lancer l'API au démarrage.
  // L'utilisateur clique "Actualiser" quand il veut les données live.
  renderActiveDenominatorViews();
}}

// ── Onglet institutions ────────────────────────────────────────────────────
function updateInstitution() {{
  const inst = document.getElementById('sel-institution').value;
  setChartSexMode(CURRENT_CHART_SEX_MODE, inst);
  setTableSexMode(CURRENT_TABLE_SEX_MODE, inst);
  renderCriteriaOptions(inst);
  const defaultSelected = Object.keys(REGIME_META[inst] || {{}});
  renderRegimeDescription(inst, defaultSelected);
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

function getChartPack(inst, mode) {{
  const data = CHARTS_INST[inst] || {{}};
  const pack = data[mode] || data.all || {{}};
  if (typeof pack === 'string') {{
    return {{
      population: pack || '<p style="color:#888;padding:10px">Aucune donnée graphique disponible.</p>',
      finances: ''
    }};
  }}
  return {{
    population: pack.population || '<p style="color:#888;padding:10px">Aucune donnée graphique disponible.</p>',
    finances: pack.finances || ''
  }};
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
  const pack = getChartPack(inst, modeValue);
  injectHtmlAndRunScripts('charts-institution-pop', pack.population);
  const finHost = document.getElementById('charts-institution-fin');
  if (finHost) {{
    if (pack.finances) {{
      finHost.style.display = '';
      injectHtmlAndRunScripts('charts-institution-fin', pack.finances);
    }} else {{
      finHost.style.display = 'none';
      finHost.innerHTML = '';
    }}
  }}
  syncChartModeButtons(modeValue);
  // Reconstruire les filtres de séries sur le nouveau graphique injecté
  initGraphSeriesFilters(
    'charts-institution-pop',
    'filters-institution',
    'Régimes',
    selected => {{
      const currentInst = document.getElementById('sel-institution').value || inst;
      renderRegimeDescription(currentInst, selected);
      renderInstitutionSexDistributions(currentInst, selected);
    }},
    () => applyRegimeQuickFilter(),
    ['charts-institution-fin']
  );
  const pieDetails = document.getElementById('institution-sex-distributions');
  if (pieDetails && pieDetails.dataset.bound !== '1') {{
    pieDetails.addEventListener('toggle', () => {{
      if (pieDetails.open) {{
        const currentInst = document.getElementById('sel-institution').value || inst;
        setTimeout(() => renderInstitutionSexDistributions(currentInst, getSelectedInstitutionRegimes()), 20);
        setTimeout(() => renderInstitutionSexDistributions(currentInst, getSelectedInstitutionRegimes()), 180);
      }} else {{
        adjustInstitutionChartHeights();
      }}
      window.dispatchEvent(new Event('resize'));
    }});
    pieDetails.dataset.bound = '1';
  }}
  if (!window.__instChartResizeBound) {{
    window.addEventListener('resize', adjustInstitutionChartHeights);
    window.__instChartResizeBound = true;
  }}
  setTimeout(adjustInstitutionChartHeights, 50);
  setTimeout(adjustInstitutionChartHeights, 250);
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

function getSelectedInstitutionRegimes() {{
  const filtersHost = document.getElementById('filters-institution');
  if (!filtersHost) return null;
  const checkboxes = Array.from(filtersHost.querySelectorAll('input[type="checkbox"]'));
  if (!checkboxes.length) return null;
  return checkboxes
    .filter(cb => cb.checked)
    .map(cb => cb.value)
    .filter(Boolean);
}}

function buildSexPieTraces(yearlyRows, colors) {{
  const n = yearlyRows.length;
  const cols = Math.min(4, Math.max(1, n));
  const rows = Math.ceil(n / cols);
  const traces = [];
  yearlyRows.forEach((item, idx) => {{
    const col = idx % cols;
    const row = Math.floor(idx / cols);
    const x0 = col / cols + 0.02;
    const x1 = (col + 1) / cols - 0.02;
    const yTop = 1 - (row / rows);
    const yBottom = 1 - ((row + 1) / rows);
    traces.push({{
      type: 'pie',
      labels: ['Hommes', 'Femmes'],
      values: [item.h, item.f],
      domain: {{ x: [x0, x1], y: [yBottom + 0.04, yTop - 0.04] }},
      hole: 0.42,
      sort: false,
      direction: 'clockwise',
      marker: {{ colors: colors }},
      textinfo: 'percent',
      hovertemplate: '<b>' + item.year + '</b><br>%{{label}}: %{{value:,.0f}} (%{{percent}})<extra></extra>',
      title: {{ text: String(item.year), font: {{ size: 12, color: '#2c5282' }} }},
      showlegend: idx === 0
    }});
  }});
  return {{ traces: traces, cols: cols, rows: rows }};
}}

function relayoutHostPlot(host, targetHeight) {{
  if (!host || !window.Plotly) return;
  const plotDiv = host.querySelector('.plotly-graph-div');
  if (!plotDiv) return;
  const h = Math.max(320, Math.floor(targetHeight) - 8);
  const w = Math.max(420, Math.floor(host.clientWidth) - 8);
  Plotly.relayout(plotDiv, {{ height: h, width: w, autosize: true }});
  Plotly.Plots.resize(plotDiv);
}}

function adjustInstitutionChartHeights() {{
  const popHost = document.getElementById('charts-institution-pop');
  const finHost = document.getElementById('charts-institution-fin');
  if (!popHost || !finHost) return;
  const hasFin = finHost.style.display !== 'none' && finHost.innerHTML.trim() !== '';
  // Resize Plotly to match the original Python figure heights (pop=460, fin=650)
  // relayoutHostPlot subtracts 8: pass height+8 to get exact target
  relayoutHostPlot(popHost, 468);  // → h = max(320, 460) = 460
  if (hasFin) {{
    relayoutHostPlot(finHost, 658);  // → h = max(320, 650) = 650
    finHost.style.display = '';
  }} else {{
    finHost.style.height = '0px';
  }}
}}

function renderSexPieCards(container, yearlyRows, colors) {{
  if (!container || !yearlyRows || !yearlyRows.length) return;
  const safePct = (value, total) => total > 0 ? Math.max(0, Math.min(100, (Number(value) || 0) * 100 / total)) : 0;
  const fmt = (value) => Number(value || 0).toLocaleString('fr-FR', {{ maximumFractionDigits: 0 }});
  const pieSvg = (hPct, fPct, uPct, total) => {{
    const radius = 46;
    const center = 66;
    const circumference = 2 * Math.PI * radius;
    const dashH = Math.max(0, Math.min(circumference, circumference * (hPct / 100)));
    const dashF = Math.max(0, Math.min(circumference - dashH, circumference * (fPct / 100)));
    const dashU = Math.max(0, circumference - dashH - dashF);
    return (
      '<svg viewBox="0 0 132 132" aria-label="Répartition H/F/non identifié">' +
        '<circle cx="' + center + '" cy="' + center + '" r="' + radius + '" fill="none" stroke="#edf2f7" stroke-width="22"></circle>' +
        '<circle cx="' + center + '" cy="' + center + '" r="' + radius + '" fill="none" stroke="' + colors[2] + '" stroke-width="22"></circle>' +
        '<circle cx="' + center + '" cy="' + center + '" r="' + radius + '" fill="none" stroke="' + colors[1] + '" stroke-width="22" stroke-dasharray="' + dashF.toFixed(2) + ' ' + (circumference - dashF).toFixed(2) + '" stroke-dashoffset="' + (-dashH).toFixed(2) + '" transform="rotate(-90 ' + center + ' ' + center + ')"></circle>' +
        '<circle cx="' + center + '" cy="' + center + '" r="' + radius + '" fill="none" stroke="' + colors[0] + '" stroke-width="22" stroke-dasharray="' + dashH.toFixed(2) + ' ' + (circumference - dashH).toFixed(2) + '" transform="rotate(-90 ' + center + ' ' + center + ')"></circle>' +
        '<text x="' + center + '" y="' + (center + 5) + '" text-anchor="middle" font-size="13" font-weight="700" fill="#2d3748">' + fmt(total) + '</text>' +
      '</svg>'
    );
  }};
  const html = yearlyRows.map(row => {{
    const knownHF = (Number(row.h) || 0) + (Number(row.f) || 0);
    const total = row.totalKnown ? Math.max(knownHF, Number(row.total) || 0) : knownHF;
    const unknown = row.totalKnown ? Math.max(0, total - knownHF) : 0;
    const hPct = safePct(row.h, total);
    const fPct = safePct(row.f, total);
    const uPct = Math.max(0, 100 - hPct - fPct);
    return (
      '<div class="sex-pie-card">' +
        '<p class="sex-pie-year">' + row.year + '</p>' +
        '<div class="sex-pie-disc">' + pieSvg(hPct, fPct, uPct, total) + '</div>' +
        '<div class="sex-pie-legend">' +
          '<div class="sex-pie-legend-item"><span class="sex-pie-dot" style="background:' + colors[0] + ';"></span>H: ' + fmt(row.h) + ' (' + hPct.toFixed(1).replace('.', ',') + '%)</div>' +
          '<div class="sex-pie-legend-item"><span class="sex-pie-dot" style="background:' + colors[1] + ';"></span>F: ' + fmt(row.f) + ' (' + fPct.toFixed(1).replace('.', ',') + '%)</div>' +
          '<div class="sex-pie-legend-item"><span class="sex-pie-dot" style="background:' + colors[2] + ';"></span>Non identifié: ' + fmt(unknown) + ' (' + uPct.toFixed(1).replace('.', ',') + '%)</div>' +
          (row.totalKnown ? '' : '<div class="sex-pie-legend-item"><em>Total indisponible</em></div>') +
        '</div>' +
      '</div>'
    );
  }}).join('');
  container.innerHTML = '<div class="sex-pie-cards">' + html + '</div>';
}}

function renderInstitutionSexDistributions(inst, selectedRegimes) {{
  const cotDiv = document.getElementById('chart-cotisants-sex-distrib');
  const benDiv = document.getElementById('chart-beneficiaires-sex-distrib');
  if (!cotDiv || !benDiv) return;
  const instData = REGIME_SEX_SERIES[inst] || {{}};
  const availableRegimes = Object.keys(instData);
  const normalizeKey = (value) => String(value || '').trim().toLowerCase();
  const requested = Array.isArray(selectedRegimes) ? selectedRegimes : availableRegimes;
  let selected = [];
  if (requested.length) {{
    const requestedNorm = requested.map(normalizeKey).filter(Boolean);
    selected = availableRegimes.filter(rc => {{
      const rcNorm = normalizeKey(rc);
      return requestedNorm.some(k => rcNorm === k || rcNorm.startsWith(k) || k.startsWith(rcNorm));
    }});
    if (!selected.length && requestedNorm.length) {{
      selected = availableRegimes.filter(rc => {{
        const rcNorm = normalizeKey(rc);
        return requestedNorm.some(k => rcNorm.includes(k) || k.includes(rcNorm));
      }});
    }}
    if (!selected.length && requestedNorm.length) {{
      selected = availableRegimes.slice();
    }}
  }}
  if (!selected.length) {{
    cotDiv.classList.add('is-empty');
    benDiv.classList.add('is-empty');
    cotDiv.style.height = '320px';
    benDiv.style.height = '320px';
    cotDiv.innerHTML = '<p class=\"empty\">Aucun régime sélectionné.</p>';
    benDiv.innerHTML = '<p class=\"empty\">Aucun régime sélectionné.</p>';
    adjustInstitutionChartHeights();
    return;
  }}

  const byYear = {{}};
  selected.forEach(rc => {{
    const series = instData[rc] || {{}};
    Object.keys(series).forEach(year => {{
      const row = series[year] || {{}};
      byYear[year] = byYear[year] || {{ cot_h: 0, cot_f: 0, cot_total: 0, cot_total_known: false, ben_h: 0, ben_f: 0, ben_total: 0, ben_total_known: false, hasCot: false, hasBen: false }};
      if (row.cotisants_total !== null && row.cotisants_total !== undefined) {{ byYear[year].cot_total += Number(row.cotisants_total) || 0; byYear[year].cot_total_known = true; byYear[year].hasCot = true; }}
      if (row.cotisants_h !== null && row.cotisants_h !== undefined) {{ byYear[year].cot_h += Number(row.cotisants_h) || 0; byYear[year].hasCot = true; }}
      if (row.cotisants_f !== null && row.cotisants_f !== undefined) {{ byYear[year].cot_f += Number(row.cotisants_f) || 0; byYear[year].hasCot = true; }}
      if (row.beneficiaires_total !== null && row.beneficiaires_total !== undefined) {{ byYear[year].ben_total += Number(row.beneficiaires_total) || 0; byYear[year].ben_total_known = true; byYear[year].hasBen = true; }}
      if (row.beneficiaires_h !== null && row.beneficiaires_h !== undefined) {{ byYear[year].ben_h += Number(row.beneficiaires_h) || 0; byYear[year].hasBen = true; }}
      if (row.beneficiaires_f !== null && row.beneficiaires_f !== undefined) {{ byYear[year].ben_f += Number(row.beneficiaires_f) || 0; byYear[year].hasBen = true; }}
    }});
  }});

  const years = Object.keys(byYear).map(Number).sort((a, b) => a - b);
  const cotRows = years
    .filter(y => byYear[String(y)].hasCot)
    .map(y => ({{ year: y, h: byYear[String(y)].cot_h, f: byYear[String(y)].cot_f, total: byYear[String(y)].cot_total, totalKnown: byYear[String(y)].cot_total_known }}))
    .filter(r => (r.h + r.f) > 0 || (r.totalKnown && r.total > 0));
  const benRows = years
    .filter(y => byYear[String(y)].hasBen)
    .map(y => ({{ year: y, h: byYear[String(y)].ben_h, f: byYear[String(y)].ben_f, total: byYear[String(y)].ben_total, totalKnown: byYear[String(y)].ben_total_known }}))
    .filter(r => (r.h + r.f) > 0 || (r.totalKnown && r.total > 0));

  if (!cotRows.length) {{
    cotDiv.classList.add('is-empty');
    cotDiv.style.height = '320px';
    cotDiv.innerHTML = '<p class=\"empty\">Aucune donnée sexuée cotisants pour les régimes sélectionnés.</p>';
  }} else {{
    cotDiv.classList.remove('is-empty');
    cotDiv.style.height = 'auto';
    renderSexPieCards(cotDiv, cotRows, ['#e53e3e', '#2b6cb0', '#a0aec0']);
  }}

  if (!benRows.length) {{
    benDiv.classList.add('is-empty');
    benDiv.style.height = '320px';
    benDiv.innerHTML = '<p class=\"empty\">Aucune donnée sexuée bénéficiaires pour les régimes sélectionnés.</p>';
  }} else {{
    benDiv.classList.remove('is-empty');
    benDiv.style.height = 'auto';
    renderSexPieCards(benDiv, benRows, ['#e53e3e', '#2b6cb0', '#a0aec0']);
  }}
  setTimeout(adjustInstitutionChartHeights, 30);
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
    renderInstitutionSexDistributions(inst, inputs.length ? inputs.map(cb => cb.value) : null);
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
  renderInstitutionSexDistributions(inst, selected);
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
  const rcData = instData[rc] || {{}};
  return rcData[mode] || rcData.all || '<p style="color:#888;padding:10px">Aucune donnée de prestation disponible.</p>';
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
(async function() {{
  CURRENT_ODD_DECISIONS = await loadOddDecisions();
  initDenominatorPanel();
  renderOddDecisionPanel();
  renderOddBranchesVisual();
  renderIndicateurs();
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
