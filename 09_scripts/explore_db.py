"""
explore_db.py — Exploration de la base de données SQLite
=========================================================
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_schema import get_db, get_db_path
import json

dbPath = get_db_path()
conn = get_db(dbPath)
cursor = conn.cursor()

print("=" * 80)
print("EXPLORATION DE LA BASE DE DONNÉES PROTECTION SOCIALE RDC")
print("=" * 80)
print(f"Chemin: {dbPath}\n")

# 1. Lister toutes les tables
print("=== TABLES DISPONIBLES ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = [row[0] for row in cursor.fetchall()]
for table in tables:
    print(f"  - {table}")

# 2. Lister les vues
print("\n=== VUES DISPONIBLES ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name;")
views = [row[0] for row in cursor.fetchall()]
for view in views:
    print(f"  - {view}")

# 3. Compter les lignes dans chaque table
print("\n=== NOMBRE DE LIGNES PAR TABLE ===")
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table}: {count} lignes")

# 4. Afficher le schéma détaillé pour chaque table
print("\n=== SCHÉMA DÉTAILLÉ DES TABLES ===\n")
for table in tables:
    print(f"\n--- TABLE: {table} ---")
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    for col in columns:
        col_id, name, type_, notnull, dflt_value, pk = col
        null_info = "NOT NULL" if notnull else "NULL"
        pk_info = " (PRIMARY KEY)" if pk else ""
        print(f"  {name:30} {type_:15} {null_info:10}{pk_info}")

# 5. Aperçu des données
print("\n\n=== APERÇU DES DONNÉES ===\n")

print("\n--- sources_ingestion ---")
cursor.execute("""
    SELECT source_id, type_source, institution, annee_donnees, fiabilite 
    FROM sources_ingestion 
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row}")

print("\n--- indicateurs_regime (premiers) ---")
cursor.execute("""
    SELECT institution, regime_code, annee, cotisants_total, beneficiaires_total 
    FROM indicateurs_regime 
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row}")

print("\n--- prestations_historique (premiers) ---")
cursor.execute("""
    SELECT institution, regime_code, annee, prestation_num, nom_fr, beneficiaires_total 
    FROM prestations_historique 
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
print("\n✓ Exploration terminée")
