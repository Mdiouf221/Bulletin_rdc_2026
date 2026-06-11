"""
extraire_ess.py — Extracteur spécifique aux fichiers ESS (format OIT/BIT)
=========================================================================
Lit les fichiers .xlsm "Enquête sur les Sources Statistiques" et peuple
la base protection_sociale_rdc.db via db_schema.py.

Ce script est propre au format ESS. D'autres scripts peuvent coexister pour
d'autres sources (rapport_annuel_cnss.py, publications_fss.py, etc.) en
utilisant les mêmes fonctions d'ingestion de db_schema.py.

Usage :
    py extraire_ess.py                    # traite tous les fichiers ESS connus
    py extraire_ess.py --annee 2022       # seulement l'année 2022
    py extraire_ess.py --institution CNSS # seulement la CNSS
    py extraire_ess.py --inbox            # traite les fichiers déposés dans 06_sources/_entrants/
    py extraire_ess.py --delete --source-id 42 --dry-run
    py extraire_ess.py --dry-run          # simule sans écrire dans la BDD
    py extraire_ess.py --verbose          # affiche le détail de chaque ligne

Structure du format ESS (gabarit OIT francophone) :
  Feuille "Inventaire des régimes" :
    - L1 : Pays, Contact
    - L2 : Période, E-mail
    - L4 : En-têtes colonnes (fonctions OIT, cotisants, bénéficiaires...)
    - L5 : Sous-en-têtes (Total/H/F, unités...)
    - L6+ : Un régime par ligne
  Feuilles de prestations ("Prestations aux familles", "Risques professionnels"...) :
    - L1 : Nom du régime, Année
    - L4 : En-têtes colonnes
    - L5+ : Une prestation par ligne (max 15)
    - L21 (env.) : Notes et Sources
"""

import os
import sys
import json
import argparse
import re
import shutil
import warnings
warnings.filterwarnings('ignore')  # Supprime les warnings openpyxl sur extensions VBA

import openpyxl

# Importation du module partagé (dans le même dossier)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_schema import (get_db, create_or_update_db, register_source,
                       upsert_regime, upsert_indicateurs, upsert_prestation,
                       to_float, to_str)

# ---------------------------------------------------------------------------
# Répertoire de base des fichiers ESS
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ESS_BASE_DIR = os.path.normpath(os.path.join(_SCRIPT_DIR, '..', '06_sources', 'ESS'))
ESS_INBOX_DIR = os.path.normpath(os.path.join(_SCRIPT_DIR, '..', '06_sources', '_entrants'))
ESS_DEST_DIRS = {
    'CNSS': os.path.normpath(os.path.join(ESS_BASE_DIR, 'ESS_CNSS')),
    'CNSSAP': os.path.normpath(os.path.join(ESS_BASE_DIR, 'ESS_CNSSAP')),
    'RDC': os.path.normpath(os.path.join(ESS_BASE_DIR, 'ESS_RDC_tous_regimes')),
}

# ---------------------------------------------------------------------------
# Catalogue des fichiers ESS connus
# Chaque entrée : (chemin_relatif_depuis_ESS_BASE_DIR, institution, annee_nominale, note_anomalie)
# annee_nominale = l'année que ce fichier est CENSÉ représenter
# ---------------------------------------------------------------------------
ESS_CATALOGUE = [
    ("ESS_CNSS/ESS CNSS 2019.xlsm",   "CNSS",   2019, None),
    ("ESS_CNSS/ESS CNSS 2020.xlsm",   "CNSS",   2020, None),
    ("ESS_CNSS/ESS CNSS 2021.xlsm",   "CNSS",   2021, None),
    ("ESS_CNSS/ESS CNSS 2022.xlsm",   "CNSS",   2022, None),
    ("ESS_CNSSAP/ESS CNSSAP 2020.xlsm", "CNSSAP", 2020,
        "Date interne inventaire affiche 2022 — anomalie connue ; données retenues pour 2020"),
    ("ESS_CNSSAP/ESS CNSSAP 2021.xlsm", "CNSSAP", 2021,
        "Date interne inventaire affiche 2022 — anomalie connue ; données retenues pour 2021"),
    ("ESS_CNSSAP/ESS CNSSAP 2022.xlsm", "CNSSAP", 2022, None),
]

# Fonctions OIT dans l'ordre des colonnes du gabarit ESS (colonnes 4 à 20 de l'inventaire)
# Source : gabarit OIT/BIT standard francophone
OIT_FONCTIONS = [
    "Vieillesse",
    "Invalidité / Handicap",
    "Survivances",
    "Maladie (en espèces)",
    "Maternité / Paternité",
    "Enfants",
    "Famille",
    "Accès à l'éducation",
    "Chômage",
    "Accident du travail",
    "Soins de santé",
    "Services d'assistance sociale",
    "Programmes de travaux publics",
    "Subventions au logement",
    "Alimentation / Nutrition",
    "Assistance sociale ciblée pour la réduction de la pauvreté",
    "Autre soutien et assistance n.c.a.",
]
OIT_FONCTIONS_START_COL = 4   # index 0-basé de la première colonne de fonction OIT

# Colonnes de l'inventaire (indices 0-basés, vérifiés empiriquement)
INV_COL = {
    'regime_label':      0,   # "Régime 1", "Régime 2"...
    'nom_original':      1,
    'nom_fr':            2,
    'administrateur':    3,
    # fonctions_oit :    4 à 20 (17 colonnes)
    'type_financement':  21,
    'caractere':         22,
    'cotisants_total':   23,
    'cotisants_h':       24,
    'cotisants_f':       25,
    'beneficiaires_total': 26,
    'beneficiaires_h':   27,
    'beneficiaires_f':   28,
    'gestion_admin':     29,
    'gestion_op':        30,
    'type_assurance':    31,
    # Finances (inventaire ESS) :
    # 32 = total des dépenses, 33 = dépenses administratives, 34 = total des recettes
    'depenses_cdf':      32,
    'depenses_admin_cdf': 33,
    'recettes_cdf':      34,
    # Colonne USD non utilisée ici (le gabarit ESS observé est en monnaie locale)
    'recettes_usd':      None,
}

# Colonnes des feuilles de prestation (indices 0-basés, vérifiés empiriquement)
PREST_COL = {
    'prestation_label':      0,   # "Prestation 1"...
    'nom_original':          1,
    'nom_fr':                2,
    'fonction_oit':          3,
    'groupe_population':     4,
    'groupe_age':            5,
    'zone_geo':              6,
    'type_financement':      7,
    'couverture_total':      8,
    'couverture_h':          9,
    'couverture_f':         10,
    'beneficiaires_total':  11,
    'beneficiaires_h':      12,
    'beneficiaires_f':      13,
    'type_paiement':        14,
    'periodicite':          15,
    'montant_unitaire_cdf': 16,   # parfois vide pour CNSSAP (utilise col 17)
    'montant_unitaire_usd': 17,
    'critere_eligibilite':  18,
    'duree_service':        19,
    'col_20':               20,
    'col_21':               21,
    'age_legal_h':          22,
    'age_legal_f':          23,
    'condition_compl':      24,   # ex: 'Carrière' (CNSSAP)
    'depenses_regime_cdf':  25,   # dépenses totales du régime (répétées sur chaque ligne)
}

# ---------------------------------------------------------------------------
# Correspondance nom de feuille → code régime stable
# ---------------------------------------------------------------------------
SHEET_TO_REGIME = {
    'Prestations aux familles': 'R1',
    'Risques professionnels':   'R2',
    'Pension':                  'R3',
    'Régime 4':                 'R4',
    'CNSAP Régime de base':     'R1',   # CNSSAP
    'Reforme du transfert':     'R2',   # CNSSAP 2022
}


# ---------------------------------------------------------------------------
# Détection et routage des fichiers ESS entrants
# ---------------------------------------------------------------------------

_ESS_EXTENSION_RE = re.compile(r'\.(xlsx|xlsm|xls)$', re.IGNORECASE)
_ESS_YEAR_RE = re.compile(r'(19|20)\d{2}')


def _safe_year(value):
    """Retourne une année entière si la valeur peut être interprétée comme telle."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    match = _ESS_YEAR_RE.search(str(value))
    if match:
        return int(match.group(0))
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _infer_ess_institution(name, workbook=None):
    """Déduit l'institution ESS à partir du nom du fichier puis, si besoin, du classeur."""
    if not name:
        return None

    lowered = name.lower()
    if 'cnssap' in lowered:
        return 'CNSSAP'
    if re.search(r'\bcnss\b', lowered):
        return 'CNSS'
    if 'tous regimes' in lowered or 'tous régimes' in lowered or 'rdc' in lowered:
        return 'RDC'

    if workbook is not None:
        sheetnames = set(workbook.sheetnames)
        if 'CNSAP Régime de base' in sheetnames or 'Reforme du transfert' in sheetnames:
            return 'CNSSAP'
        if {'Prestations aux familles', 'Risques professionnels', 'Pension'} & sheetnames:
            return 'CNSS'

    return None


def _infer_ess_year(filepath, ws=None):
    """Déduit l'année ESS à partir du nom du fichier puis de la feuille inventaire."""
    base = os.path.basename(filepath)
    year = _safe_year(base)
    if year:
        return year

    if ws is not None and 'Inventaire des régimes' in ws.parent.sheetnames:
        try:
            val = ws['B2'].value
            year = _safe_year(val)
            if year:
                return year
        except Exception:
            pass

    return None


def _ess_destination_dir(institution):
    return ESS_DEST_DIRS.get(institution)


def _ess_destination_name(filepath, institution, annee):
    """Normalise le nom cible d'un fichier ESS entrant."""
    base = os.path.basename(filepath)
    root, ext = os.path.splitext(base)
    lowered = root.lower()

    if institution == 'RDC' and re.search(r'^(ess\s+)?(rdc|ess rdc tous régimes)', lowered):
        return base

    if institution in ('CNSS', 'CNSSAP') and re.search(rf'^ess\s+{institution.lower()}\s+\d{{4}}', lowered):
        return base

    if institution == 'RDC':
        suffix = f" {annee}" if annee else ""
        return f"ESS RDC tous regimes{suffix}{ext}"

    if institution in ('CNSS', 'CNSSAP'):
        suffix = f" {annee}" if annee else ""
        return f"ESS {institution}{suffix}{ext}"

    return base


def discover_ess_inbox_files(inbox_dir):
    """Retourne les fichiers ESS déposés dans le dossier de réception unique."""
    if not os.path.isdir(inbox_dir):
        return []

    candidates = []
    for root, _dirs, files in os.walk(inbox_dir):
        for filename in files:
            if filename.lower() == 'readme.md' or filename.startswith('~$'):
                continue
            if not _ESS_EXTENSION_RE.search(filename):
                continue
            filepath = os.path.join(root, filename)
            candidates.append(filepath)

    return sorted(candidates)


# ---------------------------------------------------------------------------
# Fonctions de parsing
# ---------------------------------------------------------------------------

def _get_cell(row, idx, default=None):
    """Retourne la valeur d'une cellule par index, ou default si hors limites."""
    try:
        v = row[idx]
        if v is None:
            return default
        if isinstance(v, str) and v.strip() == '':
            return default
        return v
    except IndexError:
        return default


def _is_regime_row(row):
    """Vérifie qu'une ligne de l'inventaire est bien un régime déclaré (pas vide/gabarit)."""
    label = to_str(_get_cell(row, INV_COL['regime_label']))
    if not label or not label.startswith('Régime '):
        return False
    nom = to_str(_get_cell(row, INV_COL['nom_original']))
    if not nom or nom.startswith('Nom du régime'):
        return False
    return True


def _extract_regime_num(label):
    """Extrait le numéro du régime depuis 'Régime 3' → 3."""
    try:
        return int(label.replace('Régime', '').strip())
    except (ValueError, AttributeError):
        return None


def _extract_fonctions_oit(row):
    """Retourne la liste des fonctions OIT cochées (valeur 'X' ou 'x') dans la ligne."""
    fonctions = []
    for i, nom in enumerate(OIT_FONCTIONS):
        col = OIT_FONCTIONS_START_COL + i
        val = to_str(_get_cell(row, col))
        if val and val.upper() == 'X':
            fonctions.append(nom)
    return fonctions


def _detect_unite_monetaire(ws):
    """
    Détecte l'unité monétaire utilisée dans l'inventaire.
    CNSSAP utilise 'Milliards CDF', CNSS utilise 'CDF'.
    Lit la cellule à la position (ligne 5, col 33) dans la feuille inventaire.
    """
    try:
        rows = list(ws.iter_rows(min_row=5, max_row=5, values_only=True))
        if rows:
            val = to_str(_get_cell(rows[0], 32))
            if val and 'illiard' in val:
                return 'Milliards_CDF', 1e9
    except Exception:
        pass
    return 'CDF', 1.0


def parse_inventaire(ws, institution, annee, verbose=False):
    """
    Parse la feuille "Inventaire des régimes".
    Retourne une liste de dicts, un par régime déclaré.
    """
    unite_mon, facteur = _detect_unite_monetaire(ws)
    rows = list(ws.iter_rows(values_only=True))
    regimes = []

    for i, row in enumerate(rows):
        if not _is_regime_row(row):
            continue

        num = _extract_regime_num(to_str(_get_cell(row, 0)))
        if num is None:
            continue

        regime_code = f"{institution}_R{num}"
        fonctions = _extract_fonctions_oit(row)

        # Cotisants (nettoyage des espaces dans les nombres CNSSAP ex: "172 304")
        def parse_num(idx):
            return to_float(_get_cell(row, idx))

        depenses_raw = parse_num(INV_COL['depenses_cdf'])
        depenses_admin_raw = parse_num(INV_COL['depenses_admin_cdf'])
        recettes_raw = parse_num(INV_COL['recettes_cdf'])

        nom_original = to_str(_get_cell(row, INV_COL['nom_original']))
        nom_fr = to_str(_get_cell(row, INV_COL['nom_fr'])) or nom_original
        if institution == 'CNSS' and regime_code == 'CNSS_R4':
            nom_fr = "Action sociale et sanitaire"

        rec = {
            'institution':      institution,
            'regime_code':      regime_code,
            'regime_num':       num,
            'annee':            annee,
            'nom_original':     nom_original,
            'nom_fr':           nom_fr,
            'administrateur':   to_str(_get_cell(row, INV_COL['administrateur'])),
            'type_financement': to_str(_get_cell(row, INV_COL['type_financement'])),
            'caractere':        to_str(_get_cell(row, INV_COL['caractere'])),
            'type_assurance':   to_str(_get_cell(row, INV_COL['type_assurance'])),
            'gestion':          to_str(_get_cell(row, INV_COL['gestion_admin'])),
            'fonctions_oit':    json.dumps(fonctions, ensure_ascii=False),
            # Indicateurs quantitatifs
            'cotisants_total':  parse_num(INV_COL['cotisants_total']),
            'cotisants_h':      parse_num(INV_COL['cotisants_h']),
            'cotisants_f':      parse_num(INV_COL['cotisants_f']),
            'beneficiaires_total': parse_num(INV_COL['beneficiaires_total']),
            'beneficiaires_h':  parse_num(INV_COL['beneficiaires_h']),
            'beneficiaires_f':  parse_num(INV_COL['beneficiaires_f']),
            # Finances (converties en CDF si source en Milliards)
            'recettes_cdf':               recettes_raw * facteur if recettes_raw is not None else None,
            'recettes_usd':               parse_num(INV_COL['recettes_usd']) if INV_COL['recettes_usd'] is not None else None,
            # Le gabarit ESS fournit "Total des dépenses". Nous l'utilisons comme proxy
            # de dépense de prestation dans le schéma actuel.
            'depenses_prestations_cdf':   depenses_raw * facteur if depenses_raw is not None else None,
            'depenses_admin_cdf':         depenses_admin_raw * facteur if depenses_admin_raw is not None else None,
            'unite_monetaire_source': unite_mon,
        }

        if verbose:
            print(f"    Régime {num} ({regime_code}): {rec['nom_fr']} | "
                  f"cotisants={rec['cotisants_total']} | "
                  f"bénéf={rec['beneficiaires_total']} | "
                  f"fonctions={fonctions}")

        regimes.append(rec)

    return regimes


def purge_existing_ess_import(conn, institution, annee, nom_fichier):
    """Supprime un import ESS existant pour éviter les doublons et remplacer les valeurs."""
    source_rows = conn.execute(
        """SELECT source_id
           FROM sources_ingestion
           WHERE type_source = 'ESS'
             AND institution = ?
             AND annee_donnees = ?
             AND nom_fichier = ?""",
        (institution, annee, nom_fichier),
    ).fetchall()
    source_ids = [r[0] for r in source_rows]
    if not source_ids:
        return 0

    placeholders = ",".join(["?"] * len(source_ids))
    conn.execute(f"DELETE FROM prestations_historique WHERE source_id IN ({placeholders})", source_ids)
    conn.execute(f"DELETE FROM indicateurs_regime WHERE source_id IN ({placeholders})", source_ids)
    conn.execute(f"DELETE FROM regimes_historique WHERE source_id IN ({placeholders})", source_ids)
    conn.execute(f"DELETE FROM sources_ingestion WHERE source_id IN ({placeholders})", source_ids)
    conn.commit()
    return len(source_ids)


def find_ess_sources(conn, institution=None, annee=None, nom_fichier=None, source_id=None):
    """Retourne les sources ESS correspondant aux filtres."""
    where = ["type_source = 'ESS'"]
    params = []

    if source_id is not None:
        where.append("source_id = ?")
        params.append(source_id)
    if institution:
        where.append("UPPER(institution) = UPPER(?)")
        params.append(institution)
    if annee is not None:
        where.append("annee_donnees = ?")
        params.append(annee)
    if nom_fichier:
        where.append("nom_fichier = ?")
        params.append(nom_fichier)

    sql = f"""SELECT source_id, institution, annee_donnees, nom_fichier, chemin_fichier, date_ingestion
              FROM sources_ingestion
              WHERE {' AND '.join(where)}
              ORDER BY institution, annee_donnees, source_id"""
    return conn.execute(sql, params).fetchall()


def delete_ess_sources(conn, source_ids, dry_run=False):
    """Supprime proprement un ensemble de source_id ESS avec leurs données liées."""
    if not source_ids:
        return {'sources': 0, 'regimes': 0, 'indicateurs': 0, 'prestations': 0}

    placeholders = ",".join(["?"] * len(source_ids))
    counts = {
        'sources': conn.execute(
            f"SELECT COUNT(*) FROM sources_ingestion WHERE source_id IN ({placeholders})", source_ids
        ).fetchone()[0],
        'regimes': conn.execute(
            f"SELECT COUNT(*) FROM regimes_historique WHERE source_id IN ({placeholders})", source_ids
        ).fetchone()[0],
        'indicateurs': conn.execute(
            f"SELECT COUNT(*) FROM indicateurs_regime WHERE source_id IN ({placeholders})", source_ids
        ).fetchone()[0],
        'prestations': conn.execute(
            f"SELECT COUNT(*) FROM prestations_historique WHERE source_id IN ({placeholders})", source_ids
        ).fetchone()[0],
    }

    if dry_run:
        return counts

    conn.execute(f"DELETE FROM prestations_historique WHERE source_id IN ({placeholders})", source_ids)
    conn.execute(f"DELETE FROM indicateurs_regime WHERE source_id IN ({placeholders})", source_ids)
    conn.execute(f"DELETE FROM regimes_historique WHERE source_id IN ({placeholders})", source_ids)
    conn.execute(f"DELETE FROM sources_ingestion WHERE source_id IN ({placeholders})", source_ids)
    conn.commit()
    return counts


def parse_prestation_sheet(ws, institution, regime_code, annee, verbose=False):
    """
    Parse une feuille de prestation (ex: "Prestations aux familles").
    Retourne une liste de dicts, un par prestation déclarée (lignes non vides).
    """
    rows = list(ws.iter_rows(values_only=True))
    prestations = []

    for i, row in enumerate(rows):
        label = to_str(_get_cell(row, PREST_COL['prestation_label']))
        if not label or not label.startswith('Prestation '):
            continue

        num_str = label.replace('Prestation', '').strip()
        try:
            num = int(num_str)
        except ValueError:
            continue

        nom_fr = to_str(_get_cell(row, PREST_COL['nom_fr']))
        nom_orig = to_str(_get_cell(row, PREST_COL['nom_original']))

        # Ligne vide = fin des prestations déclarées
        if not nom_fr and not nom_orig:
            continue

        # Montant unitaire : col 16, fallback col 17 (certains fichiers ESS utilisent seulement la 2e colonne)
        montant_cdf = to_float(_get_cell(row, PREST_COL['montant_unitaire_cdf']))
        montant_cdf_alt = to_float(_get_cell(row, PREST_COL['montant_unitaire_usd']))
        if montant_cdf is None and montant_cdf_alt is not None:
            montant_cdf = montant_cdf_alt
        # Les fichiers ESS traités ici renseignent les montants en monnaie locale;
        # la colonne USD n'est donc pas alimentée à ce stade.
        montant_usd = None

        # Dépenses régime totales (répétées sur chaque ligne)
        dep_regime = to_float(_get_cell(row, PREST_COL['depenses_regime_cdf']))

        prest = {
            'institution':              institution,
            'regime_code':              regime_code,
            'annee':                    annee,
            'prestation_num':           num,
            'nom_original':             nom_orig,
            'nom_fr':                   nom_fr,
            'fonction_oit':             to_str(_get_cell(row, PREST_COL['fonction_oit'])),
            'groupe_population':        to_str(_get_cell(row, PREST_COL['groupe_population'])),
            'groupe_age':               to_str(_get_cell(row, PREST_COL['groupe_age'])),
            'zone_geo':                 to_str(_get_cell(row, PREST_COL['zone_geo'])),
            'type_financement':         to_str(_get_cell(row, PREST_COL['type_financement'])),
            'couverture_effective_total': to_float(_get_cell(row, PREST_COL['couverture_total'])),
            'couverture_h':             to_float(_get_cell(row, PREST_COL['couverture_h'])),
            'couverture_f':             to_float(_get_cell(row, PREST_COL['couverture_f'])),
            'beneficiaires_total':      to_float(_get_cell(row, PREST_COL['beneficiaires_total'])),
            'beneficiaires_h':          to_float(_get_cell(row, PREST_COL['beneficiaires_h'])),
            'beneficiaires_f':          to_float(_get_cell(row, PREST_COL['beneficiaires_f'])),
            'type_paiement':            to_str(_get_cell(row, PREST_COL['type_paiement'])),
            'periodicite':              to_str(_get_cell(row, PREST_COL['periodicite'])),
            'montant_unitaire_cdf':     montant_cdf,
            'montant_unitaire_usd':     montant_usd,
            'critere_eligibilite':      to_str(_get_cell(row, PREST_COL['critere_eligibilite'])),
            'duree_service_requise':    to_str(_get_cell(row, PREST_COL['duree_service'])),
            'age_legal_h':              to_str(_get_cell(row, PREST_COL['age_legal_h'])),
            'age_legal_f':              to_str(_get_cell(row, PREST_COL['age_legal_f'])),
            'condition_complementaire': to_str(_get_cell(row, PREST_COL['condition_compl'])),
            'depenses_regime_cdf':      dep_regime,
        }

        if verbose:
            print(f"      Prestation {num}: {nom_fr} | "
                  f"bénéf={prest['beneficiaires_total']} | "
                  f"montant={montant_cdf} CDF")

        prestations.append(prest)

    return prestations


# ---------------------------------------------------------------------------
# Traitement d'un fichier ESS
# ---------------------------------------------------------------------------

def process_ess_file(filepath, institution, annee, note_anomalie=None,
                     conn=None, dry_run=False, verbose=False,
                     nom_fichier_override=None, chemin_rel_override=None):
    """
    Traite un fichier ESS complet :
    1. Enregistre la source dans sources_ingestion
    2. Parse l'inventaire → regimes_historique + indicateurs_regime
    3. Parse chaque feuille de prestation → prestations_historique
    """
    nom_fichier = nom_fichier_override or os.path.basename(filepath)
    chemin_rel  = chemin_rel_override or os.path.relpath(filepath, start=os.path.normpath(
                      os.path.join(_SCRIPT_DIR, '..')))

    print(f"\n{'─'*65}")
    print(f"  {institution} {annee}  —  {nom_fichier}")
    if note_anomalie:
        print(f"  ⚠ {note_anomalie}")

    if not os.path.exists(filepath):
        print(f"  ✗ Fichier introuvable : {filepath}")
        return False

    # Charger le classeur (data_only=True : lit les valeurs calculées, pas les formules)
    wb = openpyxl.load_workbook(filepath, read_only=True, keep_vba=False, data_only=True)
    print(f"  Feuilles : {wb.sheetnames}")

    # ── 1. Enregistrement de la source ──────────────────────────────────────
    if not dry_run and conn:
        removed = purge_existing_ess_import(conn, institution, annee, nom_fichier)
        if removed:
            print(f"  ↺ Ancien import remplacé ({removed} source(s) supprimée(s))")
        source_id = register_source(
            conn,
            type_source      = 'ESS',
            nom_fichier      = nom_fichier,
            chemin_fichier   = chemin_rel,
            institution      = institution,
            annee_donnees    = annee,
            description      = f"ESS OIT/BIT — {institution} {annee}",
            fiabilite        = 'primaire',
            note_methodologique = note_anomalie
        )
    else:
        source_id = 0  # dry_run

    # ── 2. Parse de l'inventaire ─────────────────────────────────────────────
    INVENTAIRE_SHEET = 'Inventaire des régimes'
    if INVENTAIRE_SHEET not in wb.sheetnames:
        print(f"  ✗ Feuille '{INVENTAIRE_SHEET}' absente")
        return False

    ws_inv = wb[INVENTAIRE_SHEET]
    regimes = parse_inventaire(ws_inv, institution, annee, verbose=verbose)
    print(f"  Inventaire : {len(regimes)} régime(s) trouvé(s)")

    regime_map = {}  # num → code (ex: 1 → 'CNSS_R1')
    for r in regimes:
        regime_map[r['regime_num']] = r['regime_code']
        if not dry_run and conn:
            # regimes_historique
            upsert_regime(conn, r['institution'], r['regime_code'], r['annee'], source_id,
                nom_original    = r['nom_original'],
                nom_fr          = r['nom_fr'],
                administrateur  = r['administrateur'],
                type_financement= r['type_financement'],
                caractere       = r['caractere'],
                type_assurance  = r['type_assurance'],
                gestion         = r['gestion'],
                fonctions_oit   = r['fonctions_oit'],
                statut_regime   = 'transitoire' if 'reforme' in (r['nom_fr'] or '').lower()
                                  else 'actif',
            )
            # indicateurs_regime
            upsert_indicateurs(conn, r['institution'], r['regime_code'], r['annee'], source_id,
                cotisants_total          = r['cotisants_total'],
                cotisants_h              = r['cotisants_h'],
                cotisants_f              = r['cotisants_f'],
                beneficiaires_total      = r['beneficiaires_total'],
                beneficiaires_h          = r['beneficiaires_h'],
                beneficiaires_f          = r['beneficiaires_f'],
                recettes_cdf             = r['recettes_cdf'],
                recettes_usd             = r['recettes_usd'],
                depenses_prestations_cdf = r['depenses_prestations_cdf'],
                depenses_admin_cdf       = r['depenses_admin_cdf'],
                unite_monetaire_source   = r['unite_monetaire_source'],
            )

    # ── 3. Parse des feuilles de prestations ────────────────────────────────
    for sheet_name in wb.sheetnames:
        if sheet_name not in SHEET_TO_REGIME:
            continue

        # Résoudre le code régime pour cette feuille
        regime_suffix = SHEET_TO_REGIME[sheet_name]
        regime_code   = f"{institution}_{regime_suffix}"

        ws_p = wb[sheet_name]
        prestations = parse_prestation_sheet(ws_p, institution, regime_code, annee, verbose=verbose)

        if prestations:
            print(f"  [{sheet_name}] → {regime_code} : {len(prestations)} prestation(s)")
        if not dry_run and conn:
            for p in prestations:
                upsert_prestation(conn,
                    p['institution'], p['regime_code'], p['annee'], p['prestation_num'],
                    source_id,
                    nom_original             = p['nom_original'],
                    nom_fr                   = p['nom_fr'],
                    fonction_oit             = p['fonction_oit'],
                    groupe_population        = p['groupe_population'],
                    groupe_age               = p['groupe_age'],
                    zone_geo                 = p['zone_geo'],
                    type_financement         = p['type_financement'],
                    couverture_effective_total = p['couverture_effective_total'],
                    couverture_h             = p['couverture_h'],
                    couverture_f             = p['couverture_f'],
                    beneficiaires_total      = p['beneficiaires_total'],
                    beneficiaires_h          = p['beneficiaires_h'],
                    beneficiaires_f          = p['beneficiaires_f'],
                    type_paiement            = p['type_paiement'],
                    periodicite              = p['periodicite'],
                    montant_unitaire_cdf     = p['montant_unitaire_cdf'],
                    montant_unitaire_usd     = p['montant_unitaire_usd'],
                    critere_eligibilite      = p['critere_eligibilite'],
                    duree_service_requise    = p['duree_service_requise'],
                    age_legal_h              = p['age_legal_h'],
                    age_legal_f              = p['age_legal_f'],
                    condition_complementaire = p['condition_complementaire'],
                    depenses_regime_cdf      = p['depenses_regime_cdf'],
                )

    if not dry_run and conn:
        conn.commit()

    print(f"  ✓ Traitement terminé (source_id={source_id})")
    return True


def process_ess_inbox_file(filepath, conn=None, dry_run=False, verbose=False,
                           institution_filter=None, annee_filter=None):
    """
    Traite un fichier ESS déposé dans le dossier de réception unique.
    Le fichier est d'abord normalisé puis enregistré en base.
    """
    base = os.path.basename(filepath)
    try:
        wb = openpyxl.load_workbook(filepath, read_only=True, keep_vba=False, data_only=True)
    except Exception as exc:
        print(f"  ✗ Impossible d'ouvrir le classeur : {base} ({exc})")
        return False

    ws_inv = wb['Inventaire des régimes'] if 'Inventaire des régimes' in wb.sheetnames else None
    institution = _infer_ess_institution(base, wb)
    annee = _infer_ess_year(filepath, ws_inv)

    if institution_filter and institution and institution.upper() != institution_filter.upper():
        wb.close()
        return None
    if annee_filter and annee and annee != annee_filter:
        wb.close()
        return None

    if not institution or not annee:
        wb.close()
        print(f"  ✗ Métadonnées ESS insuffisantes pour {base} (institution={institution}, année={annee})")
        return False

    destination_dir = _ess_destination_dir(institution)
    if not destination_dir:
        wb.close()
        print(f"  ✗ Aucun sous-dossier de destination défini pour {institution}")
        return False

    destination_name = _ess_destination_name(filepath, institution, annee)
    destination_path = os.path.normpath(os.path.join(destination_dir, destination_name))
    destination_rel = os.path.relpath(destination_path, start=os.path.normpath(os.path.join(_SCRIPT_DIR, '..')))

    wb.close()
    os.makedirs(destination_dir, exist_ok=True)
    if os.path.exists(destination_path) and os.path.abspath(destination_path) != os.path.abspath(filepath):
        os.remove(destination_path)

    ok = process_ess_file(
        filepath,
        institution,
        annee,
        conn=conn,
        dry_run=dry_run,
        verbose=verbose,
        nom_fichier_override=destination_name,
        chemin_rel_override=destination_rel,
    )

    if not ok:
        return False

    if dry_run:
        return True

    if os.path.abspath(filepath) != os.path.abspath(destination_path):
        shutil.move(filepath, destination_path)
        print(f"  ↳ Déplacé vers {destination_rel}")

    return True


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Extraire les données ESS et les charger dans la base de données.')
    parser.add_argument('--annee',       type=int, help='Traiter seulement cette année')
    parser.add_argument('--institution', type=str, help='Traiter seulement cette institution (CNSS, CNSSAP)')
    parser.add_argument('--nom-fichier', type=str,
                        help='Filtrer sur un nom de fichier source ESS exact (pour suppression)')
    parser.add_argument('--source-id', type=int,
                        help='Identifiant source_id précis (pour suppression)')
    parser.add_argument('--delete', action='store_true',
                        help='Supprimer des imports ESS existants de la base')
    parser.add_argument('--all', action='store_true',
                        help='Autoriser la suppression de toutes les sources ESS (avec --delete)')
    parser.add_argument('--force', action='store_true',
                        help='Confirmer une suppression effective (sans --dry-run)')
    parser.add_argument('--inbox', action='store_true',
                        help='Traiter les fichiers ESS déposés dans 06_sources/_entrants/')
    parser.add_argument('--inbox-dir', type=str, default=ESS_INBOX_DIR,
                        help='Chemin du dossier de réception ESS')
    parser.add_argument('--dry-run',     action='store_true',
                        help='Simulation : parse les fichiers sans écrire dans la BDD')
    parser.add_argument('--verbose',     action='store_true',
                        help='Afficher le détail de chaque ligne parsée')
    args = parser.parse_args()

    print("=" * 65)
    print("  Extracteur ESS — Protection sociale RDC")
    print("=" * 65)
    if args.dry_run:
        print("  MODE DRY-RUN : aucune écriture en base")
    if args.delete:
        print("  MODE SUPPRESSION ESS")

    # Initialiser / ouvrir la base
    conn = None
    if (not args.dry_run) or args.delete:
        conn = create_or_update_db(verbose=True)

    if args.delete:
        has_filter = any([
            args.source_id is not None,
            bool(args.institution),
            args.annee is not None,
            bool(args.nom_fichier),
        ])
        if not has_filter and not args.all:
            print("✗ Suppression refusée : préciser au moins un filtre (--source-id, --institution, --annee, --nom-fichier) ou --all.")
            if conn:
                conn.close()
            return

        if not args.dry_run and not args.force:
            print("✗ Suppression bloquée : relancer avec --force (ou utiliser --dry-run pour simuler).")
            if conn:
                conn.close()
            return

        matches = find_ess_sources(
            conn,
            institution=args.institution,
            annee=args.annee,
            nom_fichier=args.nom_fichier,
            source_id=args.source_id,
        )
        if not matches:
            print("Aucune source ESS correspondant aux critères.")
            if conn:
                conn.close()
            return

        print(f"\n  Sources ESS ciblées ({len(matches)}) :")
        for row in matches:
            print(f"    - source_id={row['source_id']} | {row['institution']} {row['annee_donnees']} | {row['nom_fichier']}")

        source_ids = [row['source_id'] for row in matches]
        deleted = delete_ess_sources(conn, source_ids, dry_run=args.dry_run)

        action = "seraient supprimées" if args.dry_run else "supprimées"
        print(f"\n  ✓ Sources {action} : {deleted['sources']}")
        print(f"    - regimes_historique : {deleted['regimes']}")
        print(f"    - indicateurs_regime : {deleted['indicateurs']}")
        print(f"    - prestations_historique : {deleted['prestations']}")
        if conn:
            conn.close()
        return

    resultats = {'ok': 0, 'erreur': 0}

    if args.inbox:
        inbox_files = discover_ess_inbox_files(args.inbox_dir)
        if not inbox_files:
            print(f"Aucun fichier ESS trouvé dans {args.inbox_dir}.")
        for filepath in inbox_files:
            ok = process_ess_inbox_file(
                filepath,
                conn=conn,
                dry_run=args.dry_run,
                verbose=args.verbose,
                institution_filter=args.institution,
                annee_filter=args.annee,
            )
            if ok is True:
                resultats['ok'] += 1
            elif ok is False:
                resultats['erreur'] += 1
    else:
        # Filtrer le catalogue selon les arguments CLI
        catalogue = ESS_CATALOGUE
        if args.annee:
            catalogue = [(p, i, a, n) for p, i, a, n in catalogue if a == args.annee]
        if args.institution:
            catalogue = [(p, i, a, n) for p, i, a, n in catalogue
                         if i.upper() == args.institution.upper()]

        if not catalogue:
            print("Aucun fichier correspondant aux critères.")
            return

        for rel_path, institution, annee, note in catalogue:
            filepath = os.path.join(ESS_BASE_DIR, rel_path)
            ok = process_ess_file(filepath, institution, annee,
                                   note_anomalie=note,
                                   conn=conn, dry_run=args.dry_run,
                                   verbose=args.verbose)
            if ok is True:
                resultats['ok'] += 1
            elif ok is False:
                resultats['erreur'] += 1

    # ── Résumé final ─────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  Résumé : {resultats['ok']} fichier(s) traité(s), {resultats['erreur']} erreur(s)")

    if conn and not args.dry_run:
        # Afficher un aperçu de ce qui a été inséré
        print("\n  Contenu de la base après ingestion :")
        for table in ('sources_ingestion', 'regimes_historique',
                      'indicateurs_regime', 'prestations_historique'):
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"    {table:35s} : {n:4d} ligne(s)")
        conn.close()

    print()


if __name__ == '__main__':
    main()
