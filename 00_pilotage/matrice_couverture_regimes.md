# Matrice de couverture des régimes de protection sociale — RDC

<!-- NOTE_INTERNE
Objet du fichier :
Centraliser, par régime et par année, les 5 niveaux de population couverte définis en DM-012.
Cette matrice est la source de référence pour :
- le calcul des indicateurs ODD 1.3.1 (niveaux N4 et N5 uniquement)
- les indicateurs connexes de couverture (taux d'affiliation, taux de conformité, gap légal)
- l'analyse narrative sur les opportunités d'extension de couverture

Règle de travail :
- Renseigner N/D (non disponible) si la donnée est absente plutôt que de laisser vide.
- Distinguer les données administratives directes (source ESS) des estimations (source ILOSTAT, ONU, INS).
- Signaler tout changement de définition entre années (rupture de série).
- Cette matrice doit être mise à jour à chaque intégration d'une nouvelle ESS.
-->

---

## Définition des 5 niveaux de couverture

Ces niveaux s'appliquent à **tous les régimes**, contributifs et non contributifs.

| Niveau | Libellé | Définition | Pertinence |
|--------|---------|-----------|-----------|
| **N1** | **Population totale de référence** | Population totale du secteur ou du groupe démographique auquel le régime s'adresse en théorie (ex. : tous les travailleurs RDC, toute la population, tous les enfants 0–17 ans). | Dénominateur de base pour les taux de couverture légale et effective |
| **N2** | **Population légalement couverte** | Population que la loi, le décret ou le statut désigne comme devant être couverte par ce régime. Ne présuppose pas l'affiliation effective ni le paiement de cotisations. | Définit le gap légal vs effectif ; permet de parler des obligations non remplies |
| **N3** | **Population affiliée / enregistrée** | Personnes effectivement immatriculées ou enregistrées auprès de l'institution, indépendamment de la cotisation active ou de la réception d'une prestation. | Mesure le taux d'affiliation (N3/N2) ; gap affiliation/cotisation |
| **N4** | **Cotisants actifs** | Personnes pour lesquelles une cotisation est effectivement versée ou enregistrée sur la période de référence. Pour les régimes non contributifs : personnes éligibles activement enregistrées dans le système de ciblage. | **Numérateur ODD 1.3.1 (volet contributif)** |
| **N5** | **Bénéficiaires effectifs** | Personnes ayant effectivement reçu au moins une prestation en espèces au cours de la période de référence. | **Numérateur ODD 1.3.1 (volet prestataires)** |

> **ODD 1.3.1 = (N4 + N5 dédupliqués) / Dénominateur approprié**
>
> **Gap légal/effectif = N2 − (N4 + N5)** → espace d'extension de couverture
>
> **Gap affiliation/cotisation = N3 − N4** → sous-déclaration ou non-conformité employeurs
>
> **Taux de couverture légale = N2 / N1**
>
> **Taux de couverture effective = (N4 + N5) / N1**

---

## Matrice par régime

---

### CNSS — Branche des pensions (vieillesse, invalidité, survivants)

**Dénominateur ODD 1.3.1 :** Force de travail 15+ / Population au-delà âge légal retraite (selon sous-indicateur)

| Niveau | Description | 2019 | 2020 | 2021 | 2022 | 2023 | Source | Fiabilité |
|--------|-------------|------|------|------|------|------|--------|-----------|
| N1 | Travailleurs RDC (estimé) | N/D | ~19,5M | ~20M | ~20,5M | ~21M | ILOSTAT modelled | Estimée |
| N1b | Travailleurs secteur privé formel (estimé) | N/D | N/D | N/D | N/D | N/D | À rechercher | Absente |
| N2 | Travailleurs du secteur privé couverts légalement (CNSS obligatoire) | N/D | N/D | N/D | N/D | N/D | Loi CNSS | Juridique, pas statistique |
| N3 | Immatriculés CNSS (total cumulé ou actifs) | N/D | N/D | N/D | N/D | N/D | ESS CNSS | À vérifier |
| N4 | Cotisants actifs pensions | N/D | N/D | N/D | 613 761 | N/D | ESS CNSS 2022 | Robuste |
| N5 | Bénéficiaires pensions (vieillesse + invalidité + survie) | N/D | N/D | N/D | N/D | N/D | ESS CNSS | À extraire |

**Note :** Les données N4 et N5 par année sont à extraire directement des ESS CNSS (fichiers .xlsm). Les données 2020 sont manquantes (anomalie ESS CNSS 2020 — voir DM signalé).

---

### CNSS — Branche des risques professionnels (AT/MP)

**Dénominateur ODD 1.3.1 :** Force de travail totale

| Niveau | Description | 2019 | 2020 | 2021 | 2022 | 2023 | Source | Fiabilité |
|--------|-------------|------|------|------|------|------|--------|-----------|
| N1 | Force de travail RDC | N/D | ~19,5M | ~20M | ~20,5M | ~21M | ILOSTAT | Estimée |
| N2 | Travailleurs couverts légalement AT/MP (secteurs public + privé selon loi) | N/D | N/D | N/D | N/D | N/D | Loi CNSS | Juridique |
| N3 | N/D | N/D | N/D | N/D | N/D | N/D | — | — |
| N4 | Cotisants actifs AT/MP | N/D | N/D | N/D | N/D | N/D | ESS CNSS | À extraire |
| N5 | Bénéficiaires rentes AT/MP | N/D | N/D | N/D | N/D | N/D | ESS CNSS | À extraire |

---

### CNSS — Branche des prestations familiales (famille, maternité)

**Dénominateur ODD 1.3.1 :** Population 0–17 ans (enfants) / Naissances vivantes (maternité)

| Niveau | Description | 2019 | 2020 | 2021 | 2022 | 2023 | Source | Fiabilité |
|--------|-------------|------|------|------|------|------|--------|-----------|
| N1 enfants | Population 0–17 ans RDC | N/D | N/D | N/D | ~52,5M | N/D | ONU WPP 2024 | Bonne |
| N1 maternité | Naissances vivantes | N/D | N/D | N/D | N/D | N/D | INS RDC | À vérifier |
| N2 | Travailleurs du privé couverts légalement (allocations familiales obligatoires) | N/D | N/D | N/D | N/D | N/D | Loi CNSS | Juridique |
| N3 | Foyers immatriculés bénéficiaires | N/D | N/D | N/D | N/D | N/D | ESS CNSS | À extraire |
| N4 | Foyers cotisants actifs → enfants (× facteur DM-010) | N/D | N/D | N/D | N/D | N/D | ESS CNSS | Estimée |
| N5 | Enfants bénéficiaires allocations (foyers × facteur) | N/D | N/D | N/D | N/D | N/D | ESS CNSS | Estimée |
| N5b | Femmes bénéficiaires indemnités maternité | N/D | N/D | N/D | N/D | N/D | ESS CNSS | À extraire |

**Note DM-010 :** Le facteur de conversion foyers→enfants (3,17 pour 2019–2022) doit être documenté à chaque mise à jour. Voir `decisions_methodologiques.md`.

---

### CNSSAP — Régime de base (vieillesse, invalidité, survivants)

**Dénominateur ODD 1.3.1 :** Population au-delà âge légal retraite / Force de travail publique

| Niveau | Description | 2019 | 2020 | 2021 | 2022 | 2023 | Source | Fiabilité |
|--------|-------------|------|------|------|------|------|--------|-----------|
| N1 | Travailleurs secteur public RDC (estimé) | N/D | ~1,6M | N/D | N/D | N/D | ILOSTAT | Estimée |
| N1b | Travailleurs secteur public total (avec non-mécanisés) | N/D | ~2,4M | N/D | N/D | N/D | OIT/ILOSTAT | Estimée |
| N2 | Fonctionnaires légalement couverts CNSSAP | N/D | ~1,6M | N/D | N/D | N/D | ILOSTAT 2020 | Estimée |
| N3 | Agents immatriculés CNSSAP | N/D | N/D | N/D | N/D | N/D | CNSSAP | À vérifier |
| N4 | Cotisants actifs CNSSAP | N/D | 172 304 | 190 545 | 198 399 | N/D | ESS CNSSAP | Robuste |
| N5 | Bénéficiaires pensions CNSSAP (classique + réforme basculement) | 845 | 814 | 780 | 1 329 + 3 653 = ~4 982 | N/D | Bulletin RDC p.14-15 | Robuste |

**Note DM-012 :** Le gap N2/N4 (1,6M légaux vs 198 399 cotisants réels) est documenté. Ce gap s'explique par :
1. Agents non mécanisés (non mis sur liste de paie) — ~768 000 personnes
2. Agents mécanisés progressivement depuis 2021 (40 000 en 2021-2022, 101 000 en 2023)
3. Réforme de basculement des pensionnés (N5 en forte hausse 2022-2023)

---

### CNSSAP — Branches AT/MP et Allocations familiales

| Niveau | Description | 2019–2022 | 2023 | Source | Fiabilité |
|--------|-------------|-----------|------|--------|-----------|
| N2 | Fonctionnaires légalement couverts | Oui (légalement) | Oui | Loi CNSSAP | Juridique |
| N4 | Cotisants actifs | N/D — non opérationnel | À extraire | ESS 2023 | À vérifier |
| N5 | Bénéficiaires | N/D — non opérationnel | À extraire | ESS 2023 | À vérifier |

**Note :** Ces branches sont légalement fondées mais n'étaient pas opérationnelles avant 2023. L'absence de données 2019–2022 est documentée, pas manquante.

---

### MINAS — Programmes d'assistance sociale

**Dénominateur ODD 1.3.1 :** Population totale RDC

| Niveau | Description | 2022 | 2023 | Source | Fiabilité |
|--------|-------------|------|------|--------|-----------|
| N1 | Population totale RDC | ~99M | ~101M | ONU WPP | Bonne |
| N2 | Population éligible aux programmes MINAS (pauvres, vulnérables) | N/D | N/D | INS / enquêtes | Absente |
| N3 | Ménages enregistrés dans les bases MINAS | N/D | N/D | MINAS | À obtenir |
| N4 | N/A (programmes non contributifs — pas de cotisation) | — | — | — | — |
| N5 | Bénéficiaires effectifs prestations en espèces MINAS | N/D | N/D | ESS 2023 | Fragmentée |

---

### PAM — Transferts monétaires (programme humanitaire)

> ⚠️ **Exclu de ODD 1.3.1** (FICHE-001 registre_inclusion_programmes.md). Présenté ici pour information et indicateurs connexes uniquement.

| Niveau | Description | 2022 | 2023 | Source | Fiabilité |
|--------|-------------|------|------|--------|-----------|
| N5 (connexe) | Bénéficiaires transferts monétaires PAM | ~3 790 107 | N/D | ESS 2023 / PAM | Externe |
| N5b (connexe) | Bénéficiaires repas scolaires PAM | ~246 530 | N/D | ESS 2023 / PAM | Externe |

---

## Indicateurs dérivés à calculer (par régime, par année)

| Indicateur | Formule | Usage |
|-----------|---------|-------|
| **Taux de couverture légale** | N2 / N1 | Montre l'ambition du cadre légal |
| **Taux d'affiliation** | N3 / N2 | Mesure le respect de l'obligation d'affiliation |
| **Taux de cotisation active** | N4 / N3 | Mesure la régularité des cotisations |
| **Taux de couverture effective** | (N4 + N5) / N1 | **Numérateur ODD 1.3.1** |
| **Gap légal/effectif** | N2 − (N4 + N5) | Potentiel d'extension de couverture |
| **Gap affiliation/cotisation** | N3 − N4 | Sous-déclaration / non-conformité |

---

## Note méthodologique générale

Cette matrice est un **outil vivant**. Les niveaux N/D sont des placeholders intentionnels : ils signalent que la donnée est recherchée, pas qu'elle est ignorée. À chaque intégration d'une nouvelle ESS ou d'une nouvelle source institutionnelle, les cellules N/D doivent être complétées ou leur absence justifiée.

**Priorités de remplissage :**
1. N4 et N5 pour tous les régimes inclus dans ODD 1.3.1 → calcul des indicateurs
2. N2 pour les régimes principaux → calcul du gap légal/effectif
3. N3 pour CNSS et CNSSAP → mesure du taux d'affiliation

*Fichier créé le 2026-06-09. Référence : DM-012.*
