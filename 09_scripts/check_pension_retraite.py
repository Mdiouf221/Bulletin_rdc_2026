import sqlite3
from pathlib import Path

db_path = Path("06_donnees/protection_sociale_rdc.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Vérifier le groupe_population pour pension de retraite
print("=== pension de retraite / CNSS - groupe_population par année ===")
query = """
SELECT annee, groupe_population, groupe_age, zone_geo, 
       type_financement, critere_eligibilite
FROM prestations_historique
WHERE institution='CNSS' 
  AND nom_fr LIKE '%pension%retraite%'
ORDER BY regime_code, annee
"""

for row in conn.execute(query):
    print(f"Année {row['annee']}:")
    print(f"  groupe_population: '{row['groupe_population']}'")
    print(f"  groupe_age: '{row['groupe_age']}'")
    print(f"  zone_geo: '{row['zone_geo']}'")
    print(f"  type_financement: '{row['type_financement']}'")
    print(f"  critere_eligibilite: '{row['critere_eligibilite']}'")
    print()

conn.close()
