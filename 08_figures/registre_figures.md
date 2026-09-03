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
| Figure intro.1 | Graphique | Évolution de la population totale, urbaine et rurale de la RDC (1950–2025) | Introduction — 1. Contexte démographique | `08_figures/donnees/fig_intro_1_population_totale_urbaine_rurale.csv` | `09_scripts/generer_figures_intro.py` | `08_figures/exports/FIG_1_population_totale_urbaine_rurale_1950_2025.png` | Division de la population des Nations Unies, WPP 2024 | Série 1950–2025, données codées en dur depuis tables WPP 2024 | finalisé |
| Figure intro.2 | Graphique | Pyramide des âges de la RDC (2025) : répartition par groupe d'âge quinquennal et par sexe | Introduction — 1. Contexte démographique | `08_figures/donnees/fig_intro_2_pyramide_ages_par_sexe.csv` | `09_scripts/generer_figures_intro.py` | `08_figures/exports/FIG_2_structure_age_2025.png` | Division de la population des Nations Unies, WPP 2024 / UNFPA | Effectifs par tranche quinquennale et par sexe approximés d'après tables WPP 2024 standard — cohérents avec 0–14 : 46,7 % / 15–64 : 50,7 % / 65+ : 2,6 % | finalisé |
| Figure intro.3 | Carte | Densité de population par province, RDC | Introduction — 1. Contexte démographique | — | `09_scripts/generer_figures_intro.py` | `08_figures/exports/FIG_3_placeholder_carte_densite_provinces.png` | INS RDC (données provinciales non disponibles localement) | Retiré du bulletin — données provinciales non disponibles | retiré |
| Figure intro.4 | Graphique | Évolution du taux de croissance annuel du PIB en RDC (2000–2024) | Introduction — 2. Contexte économique | `08_figures/donnees/fig_intro_4_croissance_pib.csv` | `09_scripts/generer_figures_intro.py` | `08_figures/exports/FIG_4_croissance_PIB_2000_2024.png` | FMI, WEO (juillet 2026) + consolidation interne bulletin | Valeurs 2021–2024 confirmées FMI ; série historique 2000–2020 conservée telle qu'archivée | finalisé |
| Figure intro.5 | Graphique | Marché du travail en RDC : taux d'activité (15+) et emploi informel par sexe | Introduction — 2. Contexte économique | `08_figures/donnees/fig_intro_5a_taux_activite_par_sexe.csv` + `fig_intro_5b_emploi_informel_par_sexe.csv` | `09_scripts/generer_figures_intro.py` | `08_figures/exports/FIG_5_emploi_informel_par_sexe.png` | OIT, ILOSTAT — estimations modélisées (ILOEST) 2020 et 2023 | Double panneau : LFPR 15+ (EAP_DWAP_SEX_AGE_RT_A, 2023) + Informalité (INF_2INF_NOC_RT_A, 2020) — Ensemble / Hommes / Femmes | finalisé |
| Figure intro.6 | Graphique | Structure de l'emploi par grand secteur d'activité, RDC | Introduction — 2. Contexte économique | `08_figures/donnees/fig_intro_6_structure_emploi_par_secteur.csv` | `09_scripts/generer_figures_intro.py` | `08_figures/exports/FIG_6_structure_emploi_secteurs.png` | OIT, ILOSTAT (ILOEST), 2024 | Agriculture : 59 % (F : 68 %, H : 50 %) ; industrie et services : parts résiduelles | finalisé |
| Figure B.1.1–B.1.2 … B.7.1–B.7.2 | Graphique (paires par institution ou dispositif) | Aperçu graphique (cotisants, bénéficiaires, finances) et répartition par sexe, par institution ; B.7 porte sur le dispositif budgétaire hors CNSSAP (proxy technique TRESOR) | Annexe B — Fiches institutionnelles | base ESS (`protection_sociale_rdc.db`) | `09_scripts/generer_annexe_b_visuels.py` | `04_annexes/illustrations/annexe_B_*.png` | Base ESS OIT/BIT | Une paire de figures par institution ou dispositif ; numérotation à trois niveaux B.N.k générée automatiquement | finalisé |
| Figure C.1–C.9 (hors C.6, C.8 non calculés) | Graphique | Évolution de l'indicateur de couverture (%) et du numérateur (effectifs), par indicateur ODD 1.3.1/BIT | Annexe C — Détail des indicateurs | base ESS + dénominateurs (`protection_sociale_rdc.db`) | `09_scripts/generer_annexe_c_visuels.py` | `04_annexes/illustrations/annexe_C_*.png` | Base ESS OIT/BIT + dénominateurs bulletin | Une figure par indicateur calculé (paire de graphiques indicateur/numérateur) | finalisé |

## Notes de gestion

- Les figures doivent être numérotées par chapitre (ex : Figure 2.1).
- Les encadrés méthodologiques peuvent être suivis dans ce registre.
- Chaque figure citée dans le texte doit apparaître dans ce registre.
- Chaque figure finalisée doit avoir une source et, si nécessaire, une note méthodologique.
- Les fichiers de **données** (CSV, XLSX) sont archivés dans `08_figures/donnees/` — **séparément des données de tableaux** (`07_tableaux/sources/`).
- Les **scripts de génération** (Python, R…) sont archivés dans `08_figures/scripts/`.
- Les **images finales** (PNG, SVG, PDF) sont exportées dans `08_figures/exports/`.
- Convention de nommage : `fig_<numero>_<titre_court>` (ex : `fig_1_1_population_rdc.csv`).
- Les figures des annexes B et C sont générées automatiquement (`09_scripts/generer_annexe_b_visuels.py`, `09_scripts/generer_annexe_c_visuels.py`) et exportées dans `04_annexes/illustrations/` (et non `08_figures/exports/`) ; leur légende `<p class="fig-caption">` est injectée par le script et ne doit pas être modifiée à la main dans les blocs `AUTO_GENERE`.

## Utiliser le gestionnaire d'archivage

```bash
# Créer une nouvelle figure (interactif)
python 09_scripts/archiver_figure.py creer

# Vérifier la cohérence registre ↔ fichiers
python 09_scripts/archiver_figure.py verifier

# Lister toutes les figures et leur statut
python 09_scripts/archiver_figure.py lister
```
