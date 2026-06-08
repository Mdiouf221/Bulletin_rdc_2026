# Registre des figures, graphiques et encadrés

<!-- NOTE_INTERNE
Objet du fichier :
Centraliser la liste des figures, graphiques, schémas, cartes et encadrés prévus, en cours de préparation ou finalisés pour le bulletin.

Règle de travail :
Toute figure, graphique, carte, schéma ou encadré mentionné dans un chapitre, une annexe ou une note méthodologique doit être ajouté à ce registre.

Utilisation par les agents :
Les agents doivent mettre à jour ce registre lorsqu'une figure, un graphique, une carte, un schéma ou un encadré est créé, renommé, déplacé, supprimé ou cité dans le texte.
-->

## Statuts possibles

- à prévoir
- en préparation
- à vérifier
- finalisé
- retiré

## Registre

| Numéro | Type | Titre | Chapitre / section | Fichier données | Script génération | Fichier export | Source des données | Note méthodologique | Statut |
|---|---|---|---|---|---|---|---|---|---|
| Figure 1.1 | Schéma | Schéma de lecture du périmètre statistique du bulletin | Chapitre 1 — Cadre conceptuel | à créer | à créer | à créer | Cadre méthodologique | Peut illustrer dispositifs inclus, traités séparément ou mentionnés | à prévoir |
| Figure 2.1 | Schéma | Cartographie simplifiée des acteurs de la protection sociale en RDC | Chapitre 2 — Cartographie institutionnelle | à créer | à créer | à créer | Données institutionnelles / collecte bulletin | Doit distinguer institutions, régimes, programmes et fonctions | à prévoir |
| Figure 3.1 | Graphique | Couverture effective agrégée selon l'ODD 1.3.1 | Chapitre 3 — ODD 1.3.1 | à créer | à créer | à créer | Données administratives / calculs bulletin | À produire seulement lorsque les données sont validées | à prévoir |
| Encadré 3.1 | Encadré méthodologique | Lecture des numérateurs et dénominateurs des indicateurs de couverture | Chapitre 3 — ODD 1.3.1 | à créer | à créer | à créer | Cadre méthodologique | Peut reprendre les principes du chapitre 1 | à prévoir |
| Figure 6.1 | Graphique | Répartition des dépenses de protection sociale par institution ou régime | Chapitre 6 — Dépenses et financement | à créer | à créer | à créer | Données administratives | Distinguer dépenses de prestations et dépenses administratives si possible | à prévoir |
| Figure intro.1 | Graphique | Évolution de la population totale, urbaine et rurale de la RDC (1950–2025) | Introduction — 1. Contexte démographique | à créer | à créer | à créer | Division de la population des Nations Unies, WPP 2024 | [FIG_1] dans le texte | à prévoir |
| Figure intro.2 | Graphique | Structure de la population par grand groupe d'âge, RDC (2025) | Introduction — 1. Contexte démographique | à créer | à créer | à créer | Division de la population des Nations Unies, WPP 2024 / UNFPA | [FIG_2] dans le texte | à prévoir |
| Figure intro.3 | Carte | Densité de population par province, RDC | Introduction — 1. Contexte démographique | à créer | à créer | à créer | INS RDC / Division de la population des Nations Unies | [FIG_3] dans le texte | à prévoir |
| Figure intro.4 | Graphique | Évolution du taux de croissance annuel du PIB en RDC (2000–2023) | Introduction — 2. Contexte économique | à créer | à créer | à créer | Division des statistiques des Nations Unies / Banque mondiale | [FIG_4] dans le texte | à prévoir |
| Figure intro.5 | Graphique | Taux d'emploi informel par sexe et par statut dans l'emploi, RDC | Introduction — 2. Contexte économique | à créer | à créer | à créer | OIT, ILOSTAT — estimations modélisées | [FIG_5] dans le texte | à prévoir |
| Figure intro.6 | Graphique | Structure de l'emploi par grand secteur d'activité, RDC | Introduction — 2. Contexte économique | à créer | à créer | à créer | OIT, ILOSTAT / INS RDC | [FIG_6] dans le texte | à prévoir |

## Notes de gestion

- Les figures doivent être numérotées par chapitre (ex : Figure 2.1).
- Les encadrés méthodologiques peuvent être suivis dans ce registre.
- Chaque figure citée dans le texte doit apparaître dans ce registre.
- Chaque figure finalisée doit avoir une source et, si nécessaire, une note méthodologique.
- Les fichiers de **données** (CSV, XLSX) sont archivés dans `08_figures/donnees/` — **séparément des données de tableaux** (`07_tableaux/sources/`).
- Les **scripts de génération** (Python, R…) sont archivés dans `08_figures/scripts/`.
- Les **images finales** (PNG, SVG, PDF) sont exportées dans `08_figures/exports/`.
- Convention de nommage : `fig_<numero>_<titre_court>` (ex : `fig_1_1_population_rdc.csv`).

## Utiliser le gestionnaire d'archivage

```bash
# Créer une nouvelle figure (interactif)
python 09_scripts/archiver_figure.py creer

# Vérifier la cohérence registre ↔ fichiers
python 09_scripts/archiver_figure.py verifier

# Lister toutes les figures et leur statut
python 09_scripts/archiver_figure.py lister
```
