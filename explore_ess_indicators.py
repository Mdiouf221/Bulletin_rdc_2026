"""
Exploration des données ESS pour indicateurs ODD 1.3.1
Protection sociale RDC
"""
import sqlite3
from pathlib import Path

db_path = Path("06_donnees/protection_sociale_rdc.db")
if not db_path.exists():
    # Essayer le chemin absolu
    db_path = Path("C:\\Users\\M.Diouf\\OneDrive\\Bureau\\RDC Bulletin V1\\Bulletin_rdc_2026_agents\\06_donnees\\protection_sociale_rdc.db")

print(f"✓ Connexion à: {db_path}")
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

print("\n" + "="*80)
print("EXPLORATION DES DONNÉES ESS POUR ODD 1.3.1")
print("="*80)

# 1. TABLES ET VUES
print("\n=== TABLES DISPONIBLES ===")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

print("\n=== VUES DISPONIBLES ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name;")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

# 2. NOMBRE DE LIGNES PAR TABLE
print("\n=== NOMBRE DE LIGNES PAR TABLE ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
for table_row in cursor.fetchall():
    table = table_row[0]
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table}: {count}")

# 3. SOURCES INGESTION
print("\n=== SOURCES INGESTION ===")
cursor.execute("""
    SELECT source_id, type_source, institution, annee_donnees, fiabilite, date_ingestion 
    FROM sources_ingestion 
    ORDER BY source_id DESC
    LIMIT 20
""")
for row in cursor.fetchall():
    print(f"  ID {row['source_id']}: {row['type_source']:20} | {row['institution']:10} | {row['annee_donnees']} | {row['fiabilite']}")

# 4. INDICATEURS REGIME DISPONIBLES
print("\n=== INDICATEURS RÉGIME (Premiers 20) ===")
cursor.execute("""
    SELECT institution, regime_code, annee, 
           cotisants_total, cotisants_h, cotisants_f,
           beneficiaires_total, beneficiaires_h, beneficiaires_f 
    FROM indicateurs_regime 
    ORDER BY institution, regime_code, annee DESC
    LIMIT 20
""")
print("  Institution | Régime    | Année | Cotisants Total | H | F | Bénéficiaires Total | H | F")
for row in cursor.fetchall():
    c_tot = row['cotisants_total'] or 0
    c_h = row['cotisants_h'] or 0
    c_f = row['cotisants_f'] or 0
    b_tot = row['beneficiaires_total'] or 0
    b_h = row['beneficiaires_h'] or 0
    b_f = row['beneficiaires_f'] or 0
    print(f"  {row['institution']:11} | {row['regime_code']:9} | {row['annee']} | {c_tot:15.0f} | {c_h:6.0f} | {c_f:6.0f} | {b_tot:19.0f} | {b_h:6.0f} | {b_f:6.0f}")

# 5. PRESTATIONS POUR CHAQUE INDICATEUR ODD
print("\n" + "="*80)
print("DONNÉES POUR CHAQUE INDICATEUR ODD 1.3.1")
print("="*80)

indicators = {
    "Ind. 2.2 (Enfants)": {
        "desc": "Allocations familiales - nombre de foyers bénéficiaires",
        "institution": "CNSS",
        "fonction": "%Allocations familiales%"
    },
    "Ind. 2.3 (Maternité)": {
        "desc": "Indemnités journalières maternité - nombre de bénéficiaires",
        "institution": "CNSS",
        "fonction": "%Maternité%"
    },
    "Ind. 2.4 (Handicap)": {
        "desc": "Pensions d'invalidité - nombre de bénéficiaires",
        "institution": "CNSS",
        "fonction": "%Invalidité%"
    },
    "Ind. 2.5 (AT/MP)": {
        "desc": "Cotisants AT/MP CNSS Régime 2",
        "institution": "CNSS",
        "regime": "CNSS_R2"
    },
    "Ind. 2.7 (Vieillesse)": {
        "desc": "Pensionnés vieillesse CNSS + CNSSAP",
        "institutions": ["CNSS", "CNSSAP"],
        "fonction": "%pension%vieillesse%"
    },
    "Ind. 2.9 (Cotisants retraite)": {
        "desc": "Cotisants actifs CNSS R3 + CNSSAP R1",
        "regimes": ["CNSS_R3", "CNSSAP_R1"]
    }
}

for ind_name, ind_config in indicators.items():
    print(f"\n--- {ind_name} ---")
    print(f"Description: {ind_config['desc']}")
    
    if "fonction" in ind_config:
        # Rechercher par fonction OIT
        func_pattern = ind_config["fonction"]
        inst = ind_config.get("institution", "")
        
        cursor.execute("""
            SELECT institution, regime_code, annee, nom_fr, beneficiaires_total, beneficiaires_h, beneficiaires_f 
            FROM prestations_historique 
            WHERE institution LIKE ? AND nom_fr LIKE ?
            ORDER BY institution, regime_code, annee DESC
        """, (inst if inst else "%", func_pattern))
        
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                b_tot = row['beneficiaires_total'] or 0
                b_h = row['beneficiaires_h'] or 0
                b_f = row['beneficiaires_f'] or 0
                print(f"  {row['annee']} | {row['institution']:10} | {row['regime_code']:10} | {row['nom_fr']:30} | Total: {b_tot:10.0f} | H: {b_h:8.0f} | F: {b_f:8.0f}")
        else:
            print("  ✗ Aucune donnée trouvée")
    
    elif "regime" in ind_config:
        # Rechercher par régime spécifique
        regime = ind_config["regime"]
        cursor.execute("""
            SELECT institution, regime_code, annee, cotisants_total, cotisants_h, cotisants_f 
            FROM indicateurs_regime 
            WHERE regime_code = ?
            ORDER BY annee DESC
        """, (regime,))
        
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                c_tot = row['cotisants_total'] or 0
                c_h = row['cotisants_h'] or 0
                c_f = row['cotisants_f'] or 0
                print(f"  {row['annee']} | {row['institution']:10} | {row['regime_code']:10} | Cotisants: {c_tot:10.0f} | H: {c_h:8.0f} | F: {c_f:8.0f}")
        else:
            print("  ✗ Aucune donnée trouvée")
    
    elif "regimes" in ind_config:
        # Chercher plusieurs régimes
        for regime in ind_config["regimes"]:
            cursor.execute("""
                SELECT institution, regime_code, annee, cotisants_total, cotisants_h, cotisants_f 
                FROM indicateurs_regime 
                WHERE regime_code = ?
                ORDER BY annee DESC
            """, (regime,))
            
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    c_tot = row['cotisants_total'] or 0
                    c_h = row['cotisants_h'] or 0
                    c_f = row['cotisants_f'] or 0
                    print(f"  {row['annee']} | {row['institution']:10} | {row['regime_code']:10} | Cotisants: {c_tot:10.0f} | H: {c_h:8.0f} | F: {c_f:8.0f}")
            else:
                print(f"  ✗ Aucune donnée pour {regime}")

print("\n✓ Exploration terminée")
conn.close()
