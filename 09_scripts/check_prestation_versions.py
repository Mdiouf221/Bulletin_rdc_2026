import sqlite3
from pathlib import Path

db_path = Path("06_donnees/protection_sociale_rdc.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Vérifier combien de versions par prestation
query = """
SELECT institution, regime_code, nom_fr, 
       COUNT(DISTINCT annee) as nb_annees,
       GROUP_CONCAT(DISTINCT annee) as annees,
       COUNT(DISTINCT fonction_oit || '|' || type_paiement || '|' || periodicite) as nb_variations
FROM prestations_historique
GROUP BY institution, regime_code, nom_fr
HAVING nb_variations > 1 OR nb_annees > 1
ORDER BY institution, regime_code, nom_fr
LIMIT 10
"""

print("=== Prestations avec variations métadonnées ou plusieurs années ===")
for row in conn.execute(query):
    print(f"{row['institution']} / {row['regime_code']} / {row['nom_fr']}")
    print(f"  → {row['nb_annees']} années: {row['annees']}")
    print(f"  → {row['nb_variations']} variations métadonnées")
    print()

# Vérifier un exemple concret
print("=== Détail pour 'pension de vieillesse' (CNSS_R1) ===")
query2 = """
SELECT annee, fonction_oit, type_paiement, periodicite, 
       groupe_population, zone_geo, critere_eligibilite
FROM prestations_historique
WHERE institution='CNSS' AND regime_code='CNSS_R1' 
  AND nom_fr='pension de vieillesse'
ORDER BY annee
"""
for row in conn.execute(query2):
    print(f"Année {row['annee']}:")
    print(f"  Fonction OIT: {row['fonction_oit']}")
    print(f"  Type paiement: {row['type_paiement']}")
    print(f"  Périodicité: {row['periodicite']}")
    print(f"  Groupe pop: {row['groupe_population']}")
    print(f"  Zone: {row['zone_geo']}")
    print(f"  Critère: {row['critere_eligibilite']}")
    print()

conn.close()
