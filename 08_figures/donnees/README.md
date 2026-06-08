# Données sources des figures

Ce dossier contient les fichiers de données brutes (CSV, XLSX, JSON)
utilisés pour produire les figures du bulletin.

## Convention de nommage

    fig_<numéro>_<titre_court>.<extension>

Exemples :
    fig_1_1_population_totale_rdc.csv
    fig_3_1_couverture_odd131.xlsx

## Règles

- Un fichier de données par figure (ou un fichier par série si la figure en regroupe plusieurs).
- Ne pas stocker ici les fichiers images (→ `exports/`).
- Ne pas stocker ici les tableaux du bulletin (→ `07_tableaux/sources/`).
- Chaque fichier doit être enregistré dans `registre_figures.md` (colonne *Fichier données*).
- Indiquer la source dans la première ligne du CSV (commentaire `#`) ou dans une feuille `Métadonnées` du classeur.

## Exemple d'en-tête CSV recommandé

```csv
# Source : Division de la population des Nations Unies — WPP 2024
# Figure : fig_1_1_population_totale_rdc
# Produit par : archiver_figure.py — 2026-06-08
annee,population_totale,population_urbaine,population_rurale
1950,...,...,...
