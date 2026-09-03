# Feuille de route de rédaction

<!-- NOTE_INTERNE
Objet du fichier :
Piloter la préparation progressive du bulletin, suivre les grandes étapes de travail et identifier les prochaines actions.

Règle de travail :
Ce fichier peut être mis à jour régulièrement par l’utilisateur ou par un agent, mais les changements substantiels doivent rester cohérents avec l’architecture du rapport.
-->

## Phase 1 — Mise en place du workspace

**Objectif :** créer l’environnement de travail dans VS Code.

- [x] Créer le dossier principal `Bulletin_rdc_2026_agents`
- [x] Créer les dossiers principaux
- [x] Créer `README.md`
- [x] Créer `AGENTS.md`
- [x] Créer les fichiers de pilotage
- [x] Créer les fichiers de référence
- [x] Créer les premiers fichiers de rédaction à partir des plans existants

## Phase 2 — Structuration des pages préliminaires et de l’introduction

**Objectif :** transformer le plan des pages préliminaires et de l’introduction générale en fichiers Markdown de travail.

- [x] Créer `01_pages_preliminaires/00_plan_pages_preliminaires.md`
- [x] Créer `01_pages_preliminaires/avant_propos.md`
- [x] Créer `01_pages_preliminaires/remerciements.md`
- [x]  Créer `01_pages_preliminaires/sigles_acronymes.md`
- [x] Créer `01_pages_preliminaires/listes_tableaux_figures_encadres.md`
- [x] Créer `02_introduction_generale/00_plan_introduction.md`
- [x] Créer `02_introduction_generale/0_1_contexte_demographique.md`
- [x] Créer `02_introduction_generale/0_2_contexte_economique_emploi.md`
- [x] Créer `02_introduction_generale/0_3_strategie_donnees_statistiques.md`

## Phase 3 — Structuration du chapitre 1

**Objectif :** transformer le plan du chapitre 1 en fichiers Markdown de travail.

- [x] Créer `03_chapitres/chapitre_1_cadre_conceptuel/`
- [x] Créer `03_chapitres/chapitre_1_cadre_conceptuel/00_plan_chapitre_1.md`
- [x] Créer `03_chapitres/chapitre_1_cadre_conceptuel/1_1_definitions_approches.md`
- [x] Créer `03_chapitres/chapitre_1_cadre_conceptuel/1_2_approche_bit_oit.md`
- [x] Créer `03_chapitres/chapitre_1_cadre_conceptuel/1_3_champ_statistique.md`
- [x] Créer `03_chapitres/chapitre_1_cadre_conceptuel/1_4_classification_regimes.md`
- [x] Créer `03_chapitres/chapitre_1_cadre_conceptuel/1_5_lecture_indicateurs.md`
- [x] Créer `03_chapitres/chapitre_1_cadre_conceptuel/1_6_concepts_statistiques.md`
- [x] Créer `03_chapitres/chapitre_1_cadre_conceptuel/1_7_limites_methodologiques.md`

## Phase 3bis — Documents de référence externes

**Objectif :** déposer et référencer les documents externes servant de base de travail pour les agents.

- [x] Créer le dossier `06_sources/`
- [x] Déposer le premier Bulletin statistique RDC dans `06_sources/bulletins_rdc/`
- [x] Déposer les bulletins comparatifs pertinents dans `06_sources/bulletins_comparaison/`
- [x] Déposer les rapports OIT/BIT pertinents dans `06_sources/normes_oit/`
- [x] Convertir tous les PDF en fichiers texte lisibles par les agents (19 fichiers)
- [x] Mettre à jour le registre dans `06_sources/README_sources.md`

## Phase 4 — Rédaction assistée

**Objectif :** rédiger progressivement les sections à partir des notes internes.

- [ ] Rédiger l’avant-propos
- [ ] Rédiger l’introduction générale
- [ ] Rédiger le chapitre 1
- [ ] Vérifier la cohérence entre introduction et chapitre 1
- [ ] Préparer le plan détaillé du chapitre 2
- [ ] Préparer le plan détaillé du chapitre 3

## Phase 5 — Tableaux, figures et annexes

**Objectif :** intégrer progressivement les tableaux, figures, annexes et registres.

- [x] Créer le registre des tableaux
- [x] Créer le registre des figures
- [ ] Identifier les tableaux nécessaires par chapitre
- [ ] Identifier les figures nécessaires par chapitre
- [x] Préparer les annexes statistiques
- [x] Rafraîchir les tableaux et données depuis les bases SQL et le tableau de bord (2026-09-03)
- [x] Générer un classeur XLSX stable pour les graphiques de l’annexe B (données + métadonnées questionnaire + graphiques Excel) (2026-09-03)
- [ ] Réviser les textes d'accompagnement et contextuels à partir des séries actualisées

## Phase 6 — Assemblage et export

**Objectif :** produire une version assemblée du bulletin.

- [x] Créer `build_config.yml`
- [x] Créer le script d'assemblage Markdown
- [ ] Créer le script de nettoyage des notes internes
- [x] Créer une version de travail assemblée
- [x] Créer une version publication sans notes internes
- [x] Exporter une première version Word
- [x] Insérer dans Word les 42 graphiques de l’annexe B sous forme d’objets Excel liés, sans PNG ni tableaux de données ajoutés (2026-09-03)