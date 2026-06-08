# Scripts de génération des figures

Ce dossier contient les scripts (Python, R, etc.) utilisés pour produire
les figures à partir des données archivées dans `08_figures/donnees/`.

## Convention de nommage

    fig_<numéro>_<titre_court>.<extension>

Exemples :
    fig_1_1_population_totale_rdc.py
    fig_3_1_couverture_odd131.py

## Règles

- Un script par figure (ou par groupe de figures étroitement liées).
- Chaque script lit ses données depuis `08_figures/donnees/` et exporte le résultat dans `08_figures/exports/`.
- Ne pas coder les chemins en dur : utiliser des chemins relatifs depuis la racine du workspace.
- Chaque script doit pouvoir être relancé de façon reproductible.

## Template minimal recommandé

```python
"""
fig_X_X_<titre>.py
-------------------
Génère la figure X.X du bulletin.
Source des données : 08_figures/donnees/fig_X_X_<titre>.csv
Export             : 08_figures/exports/fig_X_X_<titre>.png
"""
import pathlib
import csv
# import matplotlib.pyplot as plt  # décommenter selon besoin

WORKSPACE = pathlib.Path(__file__).resolve().parents[2]
DONNEES   = WORKSPACE / "08_figures" / "donnees" / "fig_X_X_<titre>.csv"
EXPORT    = WORKSPACE / "08_figures" / "exports"  / "fig_X_X_<titre>.png"

# --- Lecture des données ---
# --- Création du graphique ---
# --- Export ---
# plt.savefig(EXPORT, dpi=150, bbox_inches="tight")
print(f"[OK] Figure exportée : {EXPORT}")
```
