"""
db_schema.py — Schéma et utilitaires partagés, base de données "Protection sociale RDC"
==========================================================================================
Ce module est le SEUL endroit où le schéma est défini.
Tous les scripts d'ingestion (ESS, rapports annuels, publications institutionnelles,
données manuelles, etc.) l'importent pour obtenir une connexion et enregistrer
leurs données avec traçabilité complète de l'origine.

Usage autonome (création/mise à jour du schéma) :
    py db_schema.py
    py db_schema.py --reset     # supprime et recrée la BDD (ATTENTION : perd les données)

Usage depuis un autre script d'ingestion :
    from db_schema import get_db, register_source, upsert_regime, ...
"""

import sqlite3
import os
import sys
import argparse
from datetime import datetime

# ---------------------------------------------------------------------------
# Chemin de la base (relatif à ce script)
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(_SCRIPT_DIR, '..', '06_donnees', 'protection_sociale_rdc.db'))

# ---------------------------------------------------------------------------
# Définition du schéma SQL
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
-- ========================================================================
-- TABLE: sources_ingestion
-- Registre de TOUTES les sources de données ayant alimenté la base.
-- CHAQUE ligne de données dans les autres tables référence un source_id.
-- C'est le mécanisme central de traçabilité multi-sources.
--
-- Exemples de type_source :
--   'ESS'                  — Enquête sur les Sources Statistiques (OIT/BIT)
--   'rapport_annuel'       — Rapport annuel publié par une institution
--   'publication_officielle' — Publication officielle (JO, décret, bulletin)
--   'communication_directe'  — Données transmises directement par l'institution
--   'estimation'           — Donnée estimée ou calculée
--   'manuel'               — Saisie manuelle (avec justification)
-- ========================================================================
CREATE TABLE IF NOT EXISTS sources_ingestion (
    source_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    type_source      TEXT NOT NULL,
    nom_fichier      TEXT,
    chemin_fichier   TEXT,
    institution      TEXT,
    annee_donnees    INTEGER,
    date_ingestion   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    description      TEXT,
    fiabilite        TEXT DEFAULT 'primaire'
        CHECK(fiabilite IN ('primaire', 'secondaire', 'estimee', 'incertaine')),
    url_source       TEXT,
    note_methodologique TEXT
);

-- ========================================================================
-- TABLE: regimes_historique
-- Description structurelle d'un régime pour une année donnée.
-- Une ligne par (institution, regime_code, annee).
-- Permet de détecter les changements de structure (création, suppression,
-- modification des fonctions couvertes, changement d'administrateur...).
-- ========================================================================
CREATE TABLE IF NOT EXISTS regimes_historique (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    institution      TEXT NOT NULL,
    regime_code      TEXT NOT NULL,   -- code stable ex: 'CNSS_R1', 'CNSSAP_R2'
    annee            INTEGER NOT NULL,
    nom_original     TEXT,
    nom_fr           TEXT,
    administrateur   TEXT,
    type_financement TEXT,            -- 'Contributif', 'Non-contributif', 'Mixte'
    caractere        TEXT,            -- 'Obligatoire', 'Volontaire'
    type_assurance   TEXT,            -- 'Assurance sociale', 'Assistance sociale'...
    gestion          TEXT,            -- 'Publique', 'Privée'
    fonctions_oit    TEXT,            -- JSON : liste des fonctions OIT couvertes
    statut_regime    TEXT DEFAULT 'actif'
        CHECK(statut_regime IN ('actif', 'transitoire', 'supprime', 'fusionne', 'inconnu')),
    note_methodologique TEXT,
    source_id        INTEGER REFERENCES sources_ingestion(source_id),
    UNIQUE(institution, regime_code, annee, source_id)
);

-- ========================================================================
-- TABLE: indicateurs_regime
-- Indicateurs quantitatifs agrégés au niveau du régime, par année.
-- Cotisants, bénéficiaires, recettes, dépenses — niveau régime.
-- ========================================================================
CREATE TABLE IF NOT EXISTS indicateurs_regime (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    institution               TEXT NOT NULL,
    regime_code               TEXT NOT NULL,
    annee                     INTEGER NOT NULL,
    -- Couverture
    cotisants_total           REAL,
    cotisants_h               REAL,
    cotisants_f               REAL,
    -- Bénéficiaires (total, tous types de prestations confondus)
    beneficiaires_total       REAL,
    beneficiaires_h           REAL,
    beneficiaires_f           REAL,
    -- Finances
    recettes_cdf              REAL,
    recettes_usd              REAL,
    depenses_prestations_cdf  REAL,
    depenses_prestations_usd  REAL,
    depenses_admin_cdf        REAL,
    -- Unité monétaire telle que déclarée dans la source (avant toute conversion)
    unite_monetaire_source    TEXT DEFAULT 'CDF',
    -- Qualité
    note_fiabilite            TEXT,
    source_id                 INTEGER REFERENCES sources_ingestion(source_id),
    UNIQUE(institution, regime_code, annee, source_id)
);

-- ========================================================================
-- TABLE: prestations_historique
-- Description et statistiques d'une prestation pour un régime et une année.
-- Une ligne par (institution, regime_code, prestation_num, annee).
-- C'est à ce niveau que l'on détecte les changements de dispositions légales :
-- apparition/disparition de prestations, changements de montants, d'âge légal,
-- de conditions d'éligibilité, etc.
-- ========================================================================
CREATE TABLE IF NOT EXISTS prestations_historique (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    institution                 TEXT NOT NULL,
    regime_code                 TEXT NOT NULL,
    annee                       INTEGER NOT NULL,
    prestation_num              INTEGER NOT NULL,
    -- Identification
    nom_original                TEXT,
    nom_fr                      TEXT,
    fonction_oit                TEXT,     -- ex: 'Vieillesse', 'Maternité', 'Risques professionnels'
    -- Eligibilité et couverture
    groupe_population           TEXT,
    groupe_age                  TEXT,
    zone_geo                    TEXT,
    type_financement            TEXT,
    -- Couverture effective (assurés actifs = cotisants du régime)
    couverture_effective_total  REAL,
    couverture_h                REAL,
    couverture_f                REAL,
    -- Bénéficiaires effectifs de CETTE prestation
    beneficiaires_total         REAL,
    beneficiaires_h             REAL,
    beneficiaires_f             REAL,
    -- Modalités de versement
    type_paiement               TEXT,     -- 'En espèces', 'En nature', 'Mixte'
    periodicite                 TEXT,     -- 'Périodique', 'Somme forfaitaire', 'Paiement unique'
    montant_unitaire_cdf        REAL,
    montant_unitaire_usd        REAL,
    -- Conditions légales (DIMENSION CLÉ pour le suivi des changements)
    critere_eligibilite         TEXT,
    duree_service_requise       TEXT,
    age_legal_h                 TEXT,
    age_legal_f                 TEXT,
    condition_complementaire    TEXT,     -- ex: 'Carrière' (CNSSAP)
    -- Dépenses totales du régime (répétées depuis l'inventaire)
    depenses_regime_cdf         REAL,
    -- Annotations
    note_changement_legal       TEXT,     -- à renseigner manuellement ou par script d'analyse
    source_id                   INTEGER REFERENCES sources_ingestion(source_id),
    UNIQUE(institution, regime_code, annee, prestation_num, source_id)
);

-- ========================================================================
-- TABLE: changements_detectes
-- Journal des évolutions institutionnelles détectées entre deux années.
-- Peut être alimenté automatiquement par un script d'analyse, ou manuellement.
-- ========================================================================
CREATE TABLE IF NOT EXISTS changements_detectes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    institution      TEXT NOT NULL,
    regime_code      TEXT NOT NULL,
    prestation_num   INTEGER,      -- NULL si changement au niveau du régime entier
    annee_avant      INTEGER,      -- NULL si apparition (première occurrence)
    annee_apres      INTEGER NOT NULL,
    type_changement  TEXT NOT NULL
        CHECK(type_changement IN ('apparition', 'disparition', 'modification',
                                  'fusion', 'scission', 'suspension', 'inconnu')),
    dimension        TEXT,         -- 'beneficiaires', 'montant_unitaire', 'age_legal',
                                   -- 'critere_eligibilite', 'nom', 'fonctions_oit',
                                   -- 'type_financement', 'regime_entier'
    valeur_avant     TEXT,
    valeur_apres     TEXT,
    variation_pct    REAL,         -- variation en % pour les valeurs numériques
    description      TEXT,
    detecte_auto     INTEGER DEFAULT 1,   -- 1=automatique, 0=manuel
    valide           INTEGER DEFAULT 0
        CHECK(valide IN (0, 1, 2)),       -- 0=à valider, 1=confirmé, 2=rejeté
    date_detection   TEXT DEFAULT (datetime('now', 'localtime'))
);

-- ========================================================================
-- VUES — pré-calculées pour faciliter les visualisations
-- ========================================================================

-- Série temporelle par régime avec indicateurs calculés
CREATE VIEW IF NOT EXISTS v_serie_temporelle_regimes AS
SELECT
    ir.institution,
    ir.regime_code,
    rh.nom_fr,
    rh.fonctions_oit,
    ir.annee,
    ir.cotisants_total,
    ir.cotisants_h,
    ir.cotisants_f,
    ir.beneficiaires_total,
    ir.beneficiaires_h,
    ir.beneficiaires_f,
    ir.recettes_cdf,
    ir.depenses_prestations_cdf,
    ir.depenses_admin_cdf,
    -- Indicateurs dérivés
    CASE WHEN ir.cotisants_total > 0
         THEN ROUND(ir.beneficiaires_total * 1.0 / ir.cotisants_total, 4)
         ELSE NULL END AS taux_couverture_effective,
    CASE WHEN ir.beneficiaires_total > 0
         THEN ROUND(ir.depenses_prestations_cdf / ir.beneficiaires_total, 0)
         ELSE NULL END AS depense_moy_par_beneficiaire_cdf,
    CASE WHEN ir.recettes_cdf > 0
         THEN ROUND(ir.depenses_prestations_cdf / ir.recettes_cdf, 4)
         ELSE NULL END AS ratio_depenses_recettes,
    -- Traçabilité
    si.type_source,
    si.nom_fichier,
    si.fiabilite,
    ir.note_fiabilite
FROM indicateurs_regime ir
LEFT JOIN regimes_historique rh
    ON ir.institution = rh.institution
    AND ir.regime_code = rh.regime_code
    AND ir.annee = rh.annee
LEFT JOIN sources_ingestion si ON ir.source_id = si.source_id;

-- Série temporelle par prestation
CREATE VIEW IF NOT EXISTS v_serie_temporelle_prestations AS
SELECT
    ph.institution,
    ph.regime_code,
    ph.prestation_num,
    ph.nom_fr,
    ph.fonction_oit,
    ph.annee,
    ph.beneficiaires_total,
    ph.beneficiaires_h,
    ph.beneficiaires_f,
    ph.montant_unitaire_cdf,
    ph.montant_unitaire_usd,
    ph.type_paiement,
    ph.periodicite,
    ph.age_legal_h,
    ph.age_legal_f,
    ph.duree_service_requise,
    ph.depenses_regime_cdf,
    -- Indicateur : dépense estimée par bénéficiaire de cette prestation
    CASE WHEN ph.beneficiaires_total > 0 AND ph.montant_unitaire_cdf > 0
         THEN ph.montant_unitaire_cdf   -- montant unitaire (pas agrégé)
         ELSE NULL END AS montant_unitaire_cdf_clean,
    ph.note_changement_legal,
    si.type_source,
    si.nom_fichier,
    si.fiabilite
FROM prestations_historique ph
LEFT JOIN sources_ingestion si ON ph.source_id = si.source_id
WHERE ph.nom_fr IS NOT NULL AND TRIM(ph.nom_fr) != '';

-- Vue de suivi des changements enrichie
CREATE VIEW IF NOT EXISTS v_changements_enrichis AS
SELECT
    cd.*,
    rh.nom_fr AS nom_regime
FROM changements_detectes cd
LEFT JOIN regimes_historique rh
    ON cd.institution = rh.institution
    AND cd.regime_code = rh.regime_code
    AND cd.annee_apres = rh.annee;
"""

# ---------------------------------------------------------------------------
# Fonctions utilitaires partagées
# ---------------------------------------------------------------------------

def get_db_path():
    """Retourne le chemin absolu de la base de données."""
    return DB_PATH


def get_db(path=None):
    """Retourne une connexion SQLite avec les foreign keys activées."""
    p = path or DB_PATH
    os.makedirs(os.path.dirname(p), exist_ok=True)
    conn = sqlite3.connect(p)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def create_or_update_db(path=None, verbose=True):
    """Crée ou met à jour le schéma de la base de données."""
    p = path or DB_PATH
    conn = get_db(p)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    if verbose:
        print(f"✓ Base de données prête : {p}")
    return conn


def register_source(conn, type_source, nom_fichier=None, chemin_fichier=None,
                    institution=None, annee_donnees=None, description=None,
                    fiabilite='primaire', url_source=None, note_methodologique=None):
    """
    Enregistre une source de données et retourne son source_id.
    À appeler en début de chaque script d'ingestion.

    Paramètres :
        type_source  — 'ESS', 'rapport_annuel', 'publication_officielle',
                       'communication_directe', 'estimation', 'manuel'
        nom_fichier  — nom du fichier source
        institution  — institution déclarante
        annee_donnees — année des données (pas nécessairement l'année du fichier)
        fiabilite    — 'primaire', 'secondaire', 'estimee', 'incertaine'

    Retourne :
        source_id (int)
    """
    cur = conn.execute(
        """INSERT INTO sources_ingestion
           (type_source, nom_fichier, chemin_fichier, institution, annee_donnees,
            description, fiabilite, url_source, note_methodologique)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (type_source, nom_fichier, chemin_fichier, institution, annee_donnees,
         description, fiabilite, url_source, note_methodologique)
    )
    conn.commit()
    return cur.lastrowid


def upsert_regime(conn, institution, regime_code, annee, source_id, **kwargs):
    """
    Insère ou met à jour une ligne dans regimes_historique.
    Utilise INSERT OR REPLACE (remplace si même contrainte UNIQUE).
    """
    fields = ['institution', 'regime_code', 'annee', 'source_id']
    values = [institution, regime_code, annee, source_id]
    for k, v in kwargs.items():
        fields.append(k)
        values.append(v)
    placeholders = ', '.join(['?'] * len(values))
    cols = ', '.join(fields)
    conn.execute(
        f"INSERT OR REPLACE INTO regimes_historique ({cols}) VALUES ({placeholders})",
        values
    )


def upsert_indicateurs(conn, institution, regime_code, annee, source_id, **kwargs):
    """Insère ou met à jour une ligne dans indicateurs_regime."""
    fields = ['institution', 'regime_code', 'annee', 'source_id']
    values = [institution, regime_code, annee, source_id]
    for k, v in kwargs.items():
        fields.append(k)
        values.append(v)
    placeholders = ', '.join(['?'] * len(values))
    cols = ', '.join(fields)
    conn.execute(
        f"INSERT OR REPLACE INTO indicateurs_regime ({cols}) VALUES ({placeholders})",
        values
    )


def upsert_prestation(conn, institution, regime_code, annee, prestation_num, source_id, **kwargs):
    """Insère ou met à jour une ligne dans prestations_historique."""
    fields = ['institution', 'regime_code', 'annee', 'prestation_num', 'source_id']
    values = [institution, regime_code, annee, prestation_num, source_id]
    for k, v in kwargs.items():
        fields.append(k)
        values.append(v)
    placeholders = ', '.join(['?'] * len(values))
    cols = ', '.join(fields)
    conn.execute(
        f"INSERT OR REPLACE INTO prestations_historique ({cols}) VALUES ({placeholders})",
        values
    )


def to_float(val):
    """Convertit une valeur de cellule en float, None si impossible."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace('\xa0', '').replace(' ', '').replace(',', '.')
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def to_str(val):
    """Convertit une valeur de cellule en str propre, None si vide."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


# ---------------------------------------------------------------------------
# Point d'entrée CLI
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crée ou met à jour la BDD Protection sociale RDC')
    parser.add_argument('--reset', action='store_true',
                        help='Supprime et recrée la base (ATTENTION : perte de données)')
    args = parser.parse_args()

    if args.reset:
        if os.path.exists(DB_PATH):
            resp = input(f"Supprimer {DB_PATH} ? (oui/non) : ")
            if resp.strip().lower() == 'oui':
                os.remove(DB_PATH)
                print("Base supprimée.")
            else:
                print("Annulé.")
                sys.exit(0)

    conn = create_or_update_db(verbose=True)
    # Afficher les tables créées
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    views  = conn.execute("SELECT name FROM sqlite_master WHERE type='view'  ORDER BY name").fetchall()
    print(f"  Tables : {', '.join(r['name'] for r in tables)}")
    print(f"  Vues   : {', '.join(r['name'] for r in views)}")
    conn.close()
