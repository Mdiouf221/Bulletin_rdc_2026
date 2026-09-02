# Annexe B — Fiches institutionnelles détaillées

<!-- NOTE_INTERNE
Objectif de l'annexe :
Présenter individuellement chaque institution de protection sociale en RDC avec ses données chiffrées détaillées. Cette annexe prolonge et améliore la logique du premier bulletin RDC, qui présentait les institutions une par une.

Le chapitre 2 (cartographie) décrit le système. Le chapitre 3 présente les agrégats. Cette annexe donne le détail institution par institution.

Structure par fiche :
Pour chaque institution :
- Statut juridique et date de création
- Base légale
- Régime(s) géré(s) et branche(s) couvertes
- Population affiliée (affiliés, cotisants actifs)
- Prestations servies (nombre, montant)
- Recettes et dépenses
- Source et période des données
- Limites et notes méthodologiques spécifiques

Institutions à couvrir (liste provisoire) :
- CNSS — Caisse Nationale de Sécurité Sociale (secteur privé)
- CNSSAP — Caisse Nationale de Sécurité Sociale des Agents Publics
- FNPSS — Fonds National de Promotion et de Service Social
- SESOPA — Service de Santé de la Police Nationale
- Autres régimes spéciaux identifiés lors de la collecte

Documents de référence :
- Premier bulletin RDC (édition 1/2023) : fiches institutionnelles à actualiser
- Données transmises directement par les institutions (06_sources/institutions/)

Fichiers associés :
- annexe_A1_institutions_contributrices.md : liste des institutions ayant contribué
- annexe_A2_correspondance_institutions_indicateurs.md : tableau de correspondance

Statut : structure initiale
-->

## Texte rédigé

<!-- NOTE_INTERNE
Structure commune appliquée à toutes les fiches.
Chaque fiche suit rigoureusement le même plan pour permettre la comparaison entre institutions.

Sections de chaque fiche :
1. Cadre juridique et institutionnel
2. Mission et branches couvertes
3. Financement
4. Données de couverture (tableau séries temporelles)
5. Données financières (tableau séries temporelles)
6. Évolutions et réformes en cours (narratif analytique)
7. Perspective de l'institution (1-2 paragraphes attribués à l'institution)
8. Source et limites des données

Règle rédactionnelle pour la section "Perspective de l'institution" :
- Ce texte est rédigé par ou en coordination étroite avec l'institution.
- Il est clairement attribué : introduit par "Selon la [institution]" ou présenté en encadré avec mention explicite.
- Il exprime les orientations stratégiques, priorités et engagements de l'institution  pas une appréciation externe.
- Il ne remplace pas l'analyse objective des sections précédentes.
-->

## Vue synthétique du tableau de bord (onglet « Par institution »)

Chaque fiche institutionnelle inclut, pour l'ensemble des régimes de l'institution : des graphiques d'évolution (cotisants, bénéficiaires, finances), un tableau descriptif des régimes gérés et un tableau de répartition par sexe. Ces éléments sont générés automatiquement à partir de la base ESS via `py 09_scripts/generer_annexe_b_visuels.py` — sans navigateur, sans capture d'écran — et se régénèrent à chaque rafraîchissement des données (`rafraichir_ess.py`).

Dans le tableau « Données détaillées », les institutions et régimes sont désignés par leur nom court ou leur sigle (voir la [Liste des sigles et acronymes](../01_pages_preliminaires/sigles_acronymes.md)) ; les années consécutives sans aucune donnée ESS sont regroupées en une seule ligne « AAAA–AAAA » plutôt que répétées une par une, afin de rester lisible sans perdre l'information d'absence de donnée.

---

# B.1 Caisse Nationale de Sécurité Sociale (CNSS)

## Mission et branches couvertes

La CNSS a pour mission de coordonner et d'administrer les prestations de sécurité sociale pour les travailleurs du secteur privé formel et leurs ayants droit.

<p class="table-caption"><strong>Tableau B.1.1</strong> — Branches de sécurité sociale couvertes, CNSS</p>

| Branche | Couverte ? | Note |
|---|---|---|
| Vieillesse, invalidité, décès |  | Pension de vieillesse normale, proportionnelle, anticipée, de survivant ; allocation de décès |
| Accidents du travail / maladies professionnelles (AT/MP) |  | Rentes d'incapacité, rentes de survivant |
| Prestations familiales |  | Allocations familiales |
| Maternité |  | Indemnités de maternité |
| Soins de santé |  | Non gérée directement par la CNSS |
| Chômage |  | Non couverte |

**Population assujettie :** travailleurs salariés du secteur privé (formel), congolais et étrangers, exerçant sur le territoire national.

## Cadre juridique et institutionnel

<p class="table-caption"><strong>Tableau B.1.2</strong> — Cadre juridique et institutionnel, CNSS</p>

| Élément | Détail |
|---|---|
| Texte fondateur | Décret-loi n° 87-021 du 5 août 1987 portant organisation de la sécurité sociale |
| Tutelle ministérielle | Ministère de la Santé Publique, Hygiène et Prévoyance Sociale |
| Statut juridique | Établissement public à caractère social |
| Année de création | 1987 (refonte du régime de sécurité sociale) |

## Données de couverture

<p class="table-caption"><strong>Tableau B.1.3</strong> — Données de couverture, CNSS (2019–2025)</p>

| Indicateur | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Affiliés enregistrés | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Cotisants actifs (contributeurs) | 676 179 | 508 708 | 591 130 | 613 761 | [N/D] | [N/D] | [N/D] |
| Bénéficiaires de pensions (vieillesse + invalidité) | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Bénéficiaires AT/MP (rentes d'incapacité) | 1 082 | 1 020 | 955 | 1 053 | [N/D] | [N/D] | [N/D] |
| Bénéficiaires AT/MP (rentes de survivant) | 1 476 | 1 608 | 1 845 | 1 781 | [N/D] | [N/D] | [N/D] |
| Bénéficiaires d'allocations familiales | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |

*Sources : premier Bulletin statistique RDC (2023) pour 20192022. Données 2023 à transmettre par la CNSS.*

<!-- AUTO_GENERE:CNSS:DEBUT -->

### Régimes gérés

<p class="table-caption"><strong>Tableau B.1.4</strong> — Régimes gérés, CNSS</p>

| Régime | Type de financement | Caractère | Gestion | Administrateur | Fonctions couvertes | Années ESS disponibles |
|---|---|---|---|---|---|---|
| Branche des Prestations aux familles | Contributif | Obligatoire | Publique | CNSS | Maternité / Paternité; Enfants | 2019, 2020, 2021, 2022 |
| Branche des Risques Professionnels | Contributif | Obligatoire | Publique | CNSS | Accident du travail | 2019, 2020, 2021, 2022 |
| Branche des Pensions | Contributif | Obligatoire | Publique | CNSS | Vieillesse; Invalidité / Handicap; Survivances | 2019, 2020, 2021, 2022 |
| Action sociale et sanitaire | — | — | — | CNSS | Autre soutien et assistance n.c.a. | 2019, 2020, 2021, 2022 |

### Aperçu graphique (tous régimes, toutes années)

<p class="fig-caption"><strong>Figure B.1.1</strong> — Évolution des cotisants, bénéficiaires, dépenses et recettes (tous régimes), CNSS (2019–2025)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSS_cotisants.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSS_beneficiaires.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSS_depenses.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSS_depense_par_beneficiaire.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSS_recettes.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSS_contribution.png" style="width:100%; height:auto;"></td></tr>
</table>

### Répartition par sexe (cotisants et bénéficiaires cumulés)

<p class="fig-caption"><strong>Figure B.1.2</strong> — Répartition par sexe des cotisants et bénéficiaires cumulés, CNSS (2019–2025)</p>

<p align="center" style="font-size:0.85em; color:#4a5568; margin-bottom:4px;"><em>Gauche : cotisants &middot; droite : bénéficiaires</em> &nbsp;&nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#2e78c8;margin-right:4px;"></span>Hommes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#d4487a;margin-right:4px;"></span>Femmes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#a9b4c0;margin-right:4px;"></span>Non identifié</p>
<p align="center"><img src="/files/04_annexes/illustrations/annexe_B_CNSS_sexe.png" style="width:100%; height:auto; max-width:620px;"></p>

### Données détaillées (par régime et année)

<p class="table-caption"><strong>Tableau B.1.5</strong> — Données détaillées par régime et année, CNSS (2019–2025)</p>

| Régime | Année | Cotisants totaux | Bénéficiaires totaux | Dépenses totales (Mds CDF) | Recettes totales (Mds CDF) | Dép. moy./bénéf. (k CDF) | Rec. moy./cotisant (k CDF) |
|---|---|---|---|---|---|---|---|
| Branche des Prestations aux familles | 2019 | 676,179 | 267,445 | 328.47 | 577.83 | 1,228 | 855 |
| Branche des Prestations aux familles | 2020 | 508,708 | 294,618 | 436.46 | 725.69 | 1,481 | 1,427 |
| Branche des Prestations aux familles | 2021 | 591,130 | 396,752 | 493.19 | 926.53 | 1,243 | 1,567 |
| Branche des Prestations aux familles | 2022 | 613,761 | 357,386 | 677.79 | 1,067.79 | 1,897 | 1,740 |
| Branche des Prestations aux familles | 2023–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Branche des Risques Professionnels | 2019 | 676,179 | 2,558 | 328.47 | 577.83 | 128,407 | 855 |
| Branche des Risques Professionnels | 2020 | 508,708 | 2,628 | 436.46 | 725.69 | 166,081 | 1,427 |
| Branche des Risques Professionnels | 2021 | 591,130 | 2,081 | 493.19 | 926.53 | 236,998 | 1,567 |
| Branche des Risques Professionnels | 2022 | 613,761 | 2,834 | 677.79 | 1,067.79 | 239,163 | 1,740 |
| Branche des Risques Professionnels | 2023–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Branche des Pensions | 2019 | 676,179 | 64,249 | 328.47 | 577.83 | 5,112 | 855 |
| Branche des Pensions | 2020 | 508,708 | 68,459 | 436.46 | 725.69 | 6,376 | 1,427 |
| Branche des Pensions | 2021 | 591,130 | 71,558 | 493.19 | 926.53 | 6,892 | 1,567 |
| Branche des Pensions | 2022 | 613,761 | 77,581 | 677.79 | 1,067.79 | 8,737 | 1,740 |
| Branche des Pensions | 2023–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Action sociale et sanitaire | 2019 | — | 1,766 | 0.83 | — | 469 | — |
| Action sociale et sanitaire | 2020 | — | 849 | 5.64 | — | 6,642 | — |
| Action sociale et sanitaire | 2021 | — | 849 | 19.95 | — | 23,492 | — |
| Action sociale et sanitaire | 2022 | — | 479 | 0.27 | — | 554 | — |
| Action sociale et sanitaire | 2023–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |

*Source : base ESS OIT/BIT (protection_sociale_rdc.db). Visuels et tableaux générés automatiquement, sans navigateur, via `py 09_scripts/generer_annexe_b_visuels.py`.*

<!-- AUTO_GENERE:CNSS:FIN -->

## Évolutions et réformes en cours

Le nombre de cotisants actifs à la CNSS a enregistré une baisse significative en 2020 (24,7 %), passant de 676 179 à 508 708, sous l'effet de la pandémie de COVID-19. Une reprise progressive a été observée dès 2021 (+16,2 %), puis en 2022 (+3,8 %), portant le total à 613 761 cotisants. La couverture n'a cependant pas encore retrouvé son niveau d'avant-crise.

*[À compléter : réformes législatives récentes, extension géographique, informatisation du registre, etc.]*

# B.2 Caisse Nationale de Sécurité Sociale des Agents Publics de l'État (CNSSAP)

## Mission et branches couvertes

La CNSSAP a pour mission de coordonner et d'administrer les prestations de sécurité sociale pour les agents publics de l'État et leurs ayants droit.

<p class="table-caption"><strong>Tableau B.2.1</strong> — Branches de sécurité sociale couvertes, CNSSAP</p>

| Branche | Couverte ? | Note |
|---|---|---|
| Vieillesse, invalidité, décès |  | En cours de déploiement |
| Accidents du travail / maladies professionnelles (AT/MP) |  | Branche officiellement lancée en mai 2023 |
| Prestations familiales |  |  |
| Maternité |  |  |
| Soins de santé |  | Non gérée directement |
| Chômage |  | Non couverte |

**Population assujettie :** agents de carrière des services publics de l'État, fonctionnaires contractuels, stagiaires et apprentis sous contrat. Les militaires et policiers relèvent de régimes spéciaux distincts.

## Cadre juridique et institutionnel

<p class="table-caption"><strong>Tableau B.2.2</strong> — Cadre juridique et institutionnel, CNSSAP</p>

| Élément | Détail |
|---|---|
| Texte fondateur | Décret n° 15/031 du 14 décembre 2015 |
| Tutelle ministérielle | Ministère de la Santé Publique, Hygiène et Prévoyance Sociale |
| Statut juridique | Établissement public à caractère administratif |
| Année de création | 2015 |

## Données de couverture

<p class="table-caption"><strong>Tableau B.2.3</strong> — Données de couverture, CNSSAP (2019–2025)</p>

| Indicateur | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Contributeurs actifs (total) | 172 204 | [N/D] | [N/D] | 198 399 | [N/D] | [N/D] | [N/D] |
| dont hommes | 110 912 | [N/D] | [N/D] | 138 443 | [N/D] | [N/D] | [N/D] |
| dont femmes | [N/D] | 65 624 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Bénéficiaires de pensions | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Bénéficiaires AT/MP | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |

*Sources : premier Bulletin statistique RDC (2023) pour 20192022. Données 2023 à transmettre par la CNSSAP.*

<!-- AUTO_GENERE:CNSSAP:DEBUT -->

### Régimes gérés

<p class="table-caption"><strong>Tableau B.2.4</strong> — Régimes gérés, CNSSAP</p>

| Régime | Type de financement | Caractère | Gestion | Administrateur | Fonctions couvertes | Années ESS disponibles |
|---|---|---|---|---|---|---|
| Régime de base | Contributif | Obligatoire | Publique | CNSSAP | Vieillesse; Survivances | 2020, 2021, 2022, 2023, 2024 |
| Reforme du transfert des assurés du sytème octroyé à la CNSSAP | Non-contributif | — | Publique | CNSSAP | Vieillesse; Survivances | 2022, 2023, 2024 |
| Risques professionnels | Non-contributif | — | Publique | CNSSAP | Maladie (en espèces); Accident du travail | 2023, 2024 |
| Régime Complémentaire | Contributif | Obligatoire | Publique | CNSSAP | — | 2023, 2024 |

### Aperçu graphique (tous régimes, toutes années)

<p class="fig-caption"><strong>Figure B.2.1</strong> — Évolution des cotisants, bénéficiaires, dépenses et recettes (tous régimes), CNSSAP (2019–2025)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSSAP_cotisants.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSSAP_beneficiaires.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSSAP_depenses.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSSAP_depense_par_beneficiaire.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSSAP_recettes.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_CNSSAP_contribution.png" style="width:100%; height:auto;"></td></tr>
</table>

### Répartition par sexe (cotisants et bénéficiaires cumulés)

<p class="fig-caption"><strong>Figure B.2.2</strong> — Répartition par sexe des cotisants et bénéficiaires cumulés, CNSSAP (2019–2025)</p>

<p align="center" style="font-size:0.85em; color:#4a5568; margin-bottom:4px;"><em>Gauche : cotisants &middot; droite : bénéficiaires</em> &nbsp;&nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#2e78c8;margin-right:4px;"></span>Hommes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#d4487a;margin-right:4px;"></span>Femmes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#a9b4c0;margin-right:4px;"></span>Non identifié</p>
<p align="center"><img src="/files/04_annexes/illustrations/annexe_B_CNSSAP_sexe.png" style="width:100%; height:auto; max-width:620px;"></p>

### Données détaillées (par régime et année)

<p class="table-caption"><strong>Tableau B.2.5</strong> — Données détaillées par régime et année, CNSSAP (2019–2025)</p>

| Régime | Année | Cotisants totaux | Bénéficiaires totaux | Dépenses totales (Mds CDF) | Recettes totales (Mds CDF) | Dép. moy./bénéf. (k CDF) | Rec. moy./cotisant (k CDF) |
|---|---|---|---|---|---|---|---|
| Régime de base | 2019 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Régime de base | 2020 | 172,304 | 814 | 7.20 | 40.50 | 8,845 | 235 |
| Régime de base | 2021 | 190,545 | 780 | 8.50 | 41.60 | 10,897 | 218 |
| Régime de base | 2022 | 198,399 | 1,329 | 34.40 | 52.40 | 25,884 | 264 |
| Régime de base | 2023 | 1,004,106 | 6,238 | 24.26 | 281.56 | 3,890 | 280 |
| Régime de base | 2024 | 1,013,104 | 10,485 | 29.74 | 460.33 | 2,836 | 454 |
| Régime de base | 2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Reforme du transfert des assurés du sytème octroyé à la CNSSAP | 2019–2021 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Reforme du transfert des assurés du sytème octroyé à la CNSSAP | 2022 | — | 3,653 | 34.40 | 9.80 | 9,417 | — |
| Reforme du transfert des assurés du sytème octroyé à la CNSSAP | 2023 | — | 4,522 | 8.56 | 19.62 | 1,892 | — |
| Reforme du transfert des assurés du sytème octroyé à la CNSSAP | 2024 | — | 2,510 | 19.62 | 19.62 | 7,817 | — |
| Reforme du transfert des assurés du sytème octroyé à la CNSSAP | 2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Risques professionnels | 2019–2022 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Risques professionnels | 2023 | — | 0 | 0.00 | 30.23 | — | — |
| Risques professionnels | 2024 | — | 2 | 1.96 | 33.90 | 981,796 | — |
| Risques professionnels | 2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Régime Complémentaire | 2019–2022 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Régime Complémentaire | 2023 | 218,899 | 0 | 0.00 | 22.35 | — | 102 |
| Régime Complémentaire | 2024 | 219,327 | 0 | 0.00 | 55.35 | — | 252 |
| Régime Complémentaire | 2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |

*Source : base ESS OIT/BIT (protection_sociale_rdc.db). Visuels et tableaux générés automatiquement, sans navigateur, via `py 09_scripts/generer_annexe_b_visuels.py`.*

<!-- AUTO_GENERE:CNSSAP:FIN -->

## Évolutions et réformes en cours

**Mécanisation des agents publics.** La RDC est confrontée depuis plusieurs décennies au problème des agents et fonctionnaires de l'État dits  non mécanisés  : des agents possédant un numéro de matricule mais n'apparaissant pas sur la liste de paie officielle, ne percevant donc aucune rémunération et ne bénéficiant d'aucune prestation sociale. Une politique d'inclusion salariale progressive  dite de  mécanisation   a été engagée pour régulariser leur situation. Entre octobre 2021 et décembre 2022, environ 40 000 agents ont été mécanisés, suivis de 101 000 agents supplémentaires.

**Mise à la retraite par vagues.** En 2022, le Vice-Premier Ministre en charge de la Fonction Publique a annoncé que 350 000 agents étaient éligibles à la retraite, dont certains âgés de plus de 90 ans. Des départs ont été organisés en vagues successives : 4 400 agents (septembre 2022), puis 6 369 agents (février 2023), avec une prévision de 50 000 départs supplémentaires en 2023. Ce processus représente un enjeu financier majeur pour la CNSSAP.

**Lancement de la branche AT/MP.** En mai 2023, la branche accidents du travail et maladies professionnelles a été officiellement lancée, étendant la couverture de la CNSSAP à l'ensemble de ses contributeurs.

*[À compléter : autres réformes en cours, extension aux enseignants, déploiement du système informatique, etc.]*

# B.3 Fonds National de Promotion et de Service Social (FNPSS)

*Capture non disponible à ce stade : l'institution FNPSS n'apparaît pas encore comme entrée dédiée dans l'onglet « Par institution » du tableau de bord.*

## Mission et branches couvertes

*[À rédiger à réception des informations du FNPSS.]*

<p class="table-caption"><strong>Tableau B.3.1</strong> — Branches de sécurité sociale couvertes, FNPSS</p>

| Branche | Couverte ? | Note |
|---|---|---|
| Vieillesse, invalidité, décès | *À confirmer* |  |
| AT/MP | *À confirmer* |  |
| Prestations familiales | *À confirmer* |  |
| Maternité | *À confirmer* |  |
| Soins de santé | *À confirmer* |  |

**Population assujettie :** *À préciser.*

## Cadre juridique et institutionnel

<p class="table-caption"><strong>Tableau B.3.2</strong> — Cadre juridique et institutionnel, FNPSS</p>

| Élément | Détail |
|---|---|
| Texte fondateur | *À préciser* |
| Tutelle ministérielle | *À préciser* |
| Statut juridique | *À préciser* |
| Année de création | *À préciser* |

## Données de couverture

<p class="table-caption"><strong>Tableau B.3.3</strong> — Données de couverture, FNPSS (2019–2025)</p>

| Indicateur | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Affiliés enregistrés | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Cotisants actifs | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Bénéficiaires | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |

## Évolutions et réformes en cours

*[À rédiger à réception des informations du FNPSS.]*

# B.4 Mutuelle de Santé des Enseignants de l'Enseignement Primaire, Secondaire et Professionnel (MESP)

## Mission et branches couvertes

La MESP est la seule mutuelle obligatoire et statutaire en RDC. Elle est une société d'assurance maladie obligatoire de type corporatif qui regroupe tous les enseignants du secteur public.

<p class="table-caption"><strong>Tableau B.4.1</strong> — Branches de sécurité sociale couvertes, MESP</p>

| Branche | Couverte ? | Note |
|---|---|---|
| Soins de santé (assurance maladie) |  | Paquet étendu : soins ambulatoires, spécialisés, hospitaliers, médicaments, examens |
| Maternité |  | Incluse dans le paquet de soins |
| Vieillesse / pensions |  | Non couverte |
| AT/MP |  | Non couverte |
| Prestations familiales |  | Non couverte |

**Population assujettie :** enseignants du secteur public de l'enseignement primaire, secondaire et technique, ainsi que leur conjoint et un maximum de 3 enfants de moins de 18 ans (ou encore étudiants ; 5 enfants si les deux conjoints sont enseignants). L'affiliation est conditionnée à la détention d'une carte MESP.

## Cadre juridique et institutionnel

<p class="table-caption"><strong>Tableau B.4.2</strong> — Cadre juridique et institutionnel, MESP</p>

| Élément | Détail |
|---|---|
| Texte fondateur | Arrêté n° 027/CAB/MINETAT/MTEPS/01/2019 (agrément) ; Arrêté n° 042/CAB/MIN/JGSDH/2015 (reconnaissance) |
| Tutelle ministérielle | Ministère de l'Enseignement Primaire, Secondaire et Technique (MEPST) |
| Statut juridique | Mutuelle de santé agréée, obligatoire et statutaire |
| Année de création / agrément | 2015 (reconnaissance) ; 2019 (agrément) |

## Données de couverture

<p class="table-caption"><strong>Tableau B.4.3</strong> — Données de couverture, MESP (2019–2025)</p>

| Indicateur | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Contributeurs (titulaires enseignants) | 50 256 | 54 383 | 60 745 | 80 041 | [N/D] | [N/D] | [N/D] |
| Membres de famille à charge | 72 291 | 76 578 | 81 081 | 84 836 | [N/D] | [N/D] | [N/D] |
| **Total couvert** | **122 547** | **130 961** | **141 826** | **164 877** | **[N/D]** | **[N/D]** | **[N/D]** |

*Source : données transmises par le MEPST (2023), reprises dans le premier Bulletin statistique RDC N°1/2023.*

<!-- AUTO_GENERE:MESP:DEBUT -->

### Régimes gérés

<p class="table-caption"><strong>Tableau B.4.4</strong> — Régimes gérés, MESP</p>

| Régime | Type de financement | Caractère | Gestion | Administrateur | Fonctions couvertes | Années ESS disponibles |
|---|---|---|---|---|---|---|
| MESP-Couverture Santé des enseignants du secteur public de la République Démocratique du Congo | Contributif | Obligatoire | Privée | MESP | Soins de santé | 2019, 2020, 2021, 2022 |

### Aperçu graphique (tous régimes, toutes années)

<p class="fig-caption"><strong>Figure B.4.1</strong> — Évolution des cotisants, bénéficiaires, dépenses et recettes (tous régimes), MESP (2019–2025)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_MESP_cotisants.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_MESP_beneficiaires.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_MESP_depenses.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_MESP_depense_par_beneficiaire.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_MESP_recettes.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_MESP_contribution.png" style="width:100%; height:auto;"></td></tr>
</table>

### Répartition par sexe (cotisants et bénéficiaires cumulés)

<p class="fig-caption"><strong>Figure B.4.2</strong> — Répartition par sexe des cotisants et bénéficiaires cumulés, MESP (2019–2025)</p>

<p align="center" style="font-size:0.85em; color:#4a5568; margin-bottom:4px;"><em>Gauche : cotisants &middot; droite : bénéficiaires</em> &nbsp;&nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#2e78c8;margin-right:4px;"></span>Hommes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#d4487a;margin-right:4px;"></span>Femmes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#a9b4c0;margin-right:4px;"></span>Non identifié</p>
<p align="center"><img src="/files/04_annexes/illustrations/annexe_B_MESP_sexe.png" style="width:100%; height:auto; max-width:620px;"></p>

### Données détaillées (par régime et année)

<p class="table-caption"><strong>Tableau B.4.5</strong> — Données détaillées par régime et année, MESP (2019–2025)</p>

| Régime | Année | Cotisants totaux | Bénéficiaires totaux | Dépenses totales (Mds CDF) | Recettes totales (Mds CDF) | Dép. moy./bénéf. (k CDF) | Rec. moy./cotisant (k CDF) |
|---|---|---|---|---|---|---|---|
| MESP-Couverture Santé des enseignants du secteur public de la République Démocratique du Congo | 2019 | 50,256 | 122,547 | — | — | — | — |
| MESP-Couverture Santé des enseignants du secteur public de la République Démocratique du Congo | 2020 | 54,383 | 130,961 | — | — | — | — |
| MESP-Couverture Santé des enseignants du secteur public de la République Démocratique du Congo | 2021 | 60,745 | 141,826 | — | — | — | — |
| MESP-Couverture Santé des enseignants du secteur public de la République Démocratique du Congo | 2022 | 80,041 | 164,877 | — | — | — | — |
| MESP-Couverture Santé des enseignants du secteur public de la République Démocratique du Congo | 2023–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |

*Source : base ESS OIT/BIT (protection_sociale_rdc.db). Visuels et tableaux générés automatiquement, sans navigateur, via `py 09_scripts/generer_annexe_b_visuels.py`.*

<!-- AUTO_GENERE:MESP:FIN -->

## Évolutions et réformes en cours

Entre 2019 et 2022, le nombre de contributeurs à la MESP a progressé de **59,3 %**, passant de 50 256 à 80 041. Le nombre de personnes à charge a également augmenté, atteignant 84 836 en 2022, pour un total couvert de 164 877 personnes.

Cette dynamique reste cependant très en deçà du potentiel : si chaque enseignant détenait une carte MESP, la mutuelle compterait plus de 700 000 titulaires et potentiellement 2 800 000 bénéficiaires au total. À fin 2022, la MESP n'était opérationnelle que dans 7 des 26 provinces (Kinshasa, Haut-Katanga, Équateur, Kasaï-Oriental, Kasaï, Tshopo et Nord-Kivu), laissant 19 provinces sans couverture effective.

L'extension géographique progressive constitue le principal enjeu stratégique de la MESP pour les années à venir.

# B.5 Fonds de Solidarité de Santé (FSS)

## Mission et branches couvertes

Le FSS est l'instrument central de la mise en œuvre de la Couverture Santé Universelle (CSU) en RDC. Il est chargé d'organiser la solidarité financière des cotisants de la CSU, de collecter les fonds, de contractualiser avec les établissements de santé et pharmaceutiques, et d'assurer un financement équitable des soins pour tous.

Le FSS a vocation à regrouper, à terme, plusieurs régimes :

<p class="table-caption"><strong>Tableau B.5.1</strong> — Régimes prévus au sein du FSS et état d'opérationnalisation</p>

| Régime | Statut |
|---|---|
| Assurance maladie obligatoire pour les agents publics actifs et retraités | En cours d'opérationnalisation |
| Assurance maladie obligatoire pour les travailleurs du secteur privé | En cours |
| Assurance maladie obligatoire scolaire et estudiantine | En cours |
| Assurance maladie du secteur informel | En cours |
| Assistance médicale aux personnes vulnérables (non contributif) | En cours |
| Régime spécial sur la gratuité de la maternité | **Opérationnel depuis septembre 2023** (Kinshasa) |
| Assurance maladie complémentaire | En cours |

## Cadre juridique et institutionnel

<p class="table-caption"><strong>Tableau B.5.2</strong> — Cadre juridique et institutionnel, FSS</p>

| Élément | Détail |
|---|---|
| Texte fondateur | Loi n° 18/035 du 13 décembre 2018 fixant les principes fondamentaux relatifs à l'organisation de la santé publique |
| Décret d'organisation | Décret n° 22/13 du 09 avril 2022 |
| Tutelle ministérielle | Ministère de la Santé Publique, Hygiène et Prévoyance Sociale |
| Statut juridique | Établissement public à caractère administratif, doté de la personnalité juridique et de l'autonomie de gestion |
| Année de création | 2018 (loi) ; organisation précisée en 2022 |

## Données de couverture

<p class="table-caption"><strong>Tableau B.5.3</strong> — Données de couverture, FSS (2019–2025)</p>

| Indicateur | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Note |
|---|---|---|---|---|---|---|---|---|
| Bénéficiaires de la gratuité de la maternité | [N/D] | [N/D] | [N/D] | [N/D] | *En cours de déploiement* | [N/D] | [N/D] | Lancé en septembre 2023 à Kinshasa |
| Population cible (ville-province de Kinshasa) | [N/D] | [N/D] | [N/D] | [N/D] | 1618 millions | [N/D] | [N/D] | Première phase |
| Contributeurs actifs | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | Contributions non encore prélevées |

*À compléter à réception des données du FSS.*

<!-- AUTO_GENERE:FSS:DEBUT -->

### Régimes gérés

<p class="table-caption"><strong>Tableau B.5.4</strong> — Régimes gérés, FSS</p>

| Régime | Type de financement | Caractère | Gestion | Administrateur | Fonctions couvertes | Années ESS disponibles |
|---|---|---|---|---|---|---|
| FSS-Assurance maladie du secteur informel | Contributif | Obligatoire | Publique | FSS - Fond de Solidarité Santé | Soins de santé | 2022 |
| FSS-Assurance maladie obligatoire pour les agents de carrière des Services publics de l'Etat, actifs et retraités | Contributif | Obligatoire | Publique | FSS - Fond de Solidarité Santé | Soins de santé | 2022 |
| FSS-Assurance maladie obligatoire des travailleurs régis par le Code du travail, retraités et actifs | Contributif | Obligatoire | Publique | FSS - Fond de Solidarité Santé | Soins de santé | 2022 |
| FSS-Assurance maladie obligatoire pour élèves et étudiants | Contributif | Obligatoire | Publique | FSS - Fond de Solidarité Santé | Soins de santé | 2022 |
| FSS-Assurance médicale de l’Etat aux personnes vulnérables | Non-contributif | — | Publique | FSS - Fond de Solidarité Santé | Soins de santé | 2022 |

### Aperçu graphique (tous régimes, toutes années)

<p class="fig-caption"><strong>Figure B.5.1</strong> — Évolution des cotisants, bénéficiaires, dépenses et recettes (tous régimes), FSS (2019–2025)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_FSS_cotisants.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_FSS_beneficiaires.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_FSS_depenses.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_FSS_depense_par_beneficiaire.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_FSS_recettes.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_FSS_contribution.png" style="width:100%; height:auto;"></td></tr>
</table>

### Répartition par sexe (cotisants et bénéficiaires cumulés)

<p class="fig-caption"><strong>Figure B.5.2</strong> — Répartition par sexe des cotisants et bénéficiaires cumulés, FSS (2019–2025)</p>

<p align="center" style="font-size:0.85em; color:#4a5568; margin-bottom:4px;"><em>Gauche : cotisants &middot; droite : bénéficiaires</em> &nbsp;&nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#2e78c8;margin-right:4px;"></span>Hommes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#d4487a;margin-right:4px;"></span>Femmes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#a9b4c0;margin-right:4px;"></span>Non identifié</p>
<p align="center"><img src="/files/04_annexes/illustrations/annexe_B_FSS_sexe.png" style="width:100%; height:auto; max-width:620px;"></p>

### Données détaillées (par régime et année)

<p class="table-caption"><strong>Tableau B.5.5</strong> — Données détaillées par régime et année, FSS (2019–2025)</p>

| Régime | Année | Cotisants totaux | Bénéficiaires totaux | Dépenses totales (Mds CDF) | Recettes totales (Mds CDF) | Dép. moy./bénéf. (k CDF) | Rec. moy./cotisant (k CDF) |
|---|---|---|---|---|---|---|---|
| FSS-Assurance maladie du secteur informel | 2019–2021 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| FSS-Assurance maladie du secteur informel | 2022 | — | — | — | — | — | — |
| FSS-Assurance maladie du secteur informel | 2023–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| FSS-Assurance maladie obligatoire pour les agents de carrière des Services publics de l'Etat, actifs et retraités | 2019–2021 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| FSS-Assurance maladie obligatoire pour les agents de carrière des Services publics de l'Etat, actifs et retraités | 2022 | — | — | — | — | — | — |
| FSS-Assurance maladie obligatoire pour les agents de carrière des Services publics de l'Etat, actifs et retraités | 2023–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| FSS-Assurance maladie obligatoire des travailleurs régis par le Code du travail, retraités et actifs | 2019–2021 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| FSS-Assurance maladie obligatoire des travailleurs régis par le Code du travail, retraités et actifs | 2022 | — | — | — | — | — | — |
| FSS-Assurance maladie obligatoire des travailleurs régis par le Code du travail, retraités et actifs | 2023–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| FSS-Assurance maladie obligatoire pour élèves et étudiants | 2019–2021 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| FSS-Assurance maladie obligatoire pour élèves et étudiants | 2022 | — | — | — | — | — | — |
| FSS-Assurance maladie obligatoire pour élèves et étudiants | 2023–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| FSS-Assurance médicale de l’Etat aux personnes vulnérables | 2019–2021 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| FSS-Assurance médicale de l’Etat aux personnes vulnérables | 2022 | — | — | — | — | — | — |
| FSS-Assurance médicale de l’Etat aux personnes vulnérables | 2023–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |

*Source : base ESS OIT/BIT (protection_sociale_rdc.db). Visuels et tableaux générés automatiquement, sans navigateur, via `py 09_scripts/generer_annexe_b_visuels.py`.*

<!-- AUTO_GENERE:FSS:FIN -->

## Évolutions et réformes en cours

Le FSS représente l'architecture institutionnelle centrale de la CSU en RDC, mais son déploiement effectif est progressif. En septembre 2023, la politique de gratuité des accouchements et des soins néonatals a été lancée dans la ville-province de Kinshasa. Ce paquet couvre les consultations prénatales, l'échographie obstétricale, les accouchements simples et par césarienne, les soins du nouveau-né, la vaccination, les consultations post-natales et l'accès aux médicaments essentiels.

L'extension est prévue vers le Sud-Kivu, le Kasaï-Oriental et le Kongo-Central, avant une généralisation progressive à l'ensemble du territoire national. La vocation du FSS est à terme de remplacer tous les régimes particuliers de financement des soins médicaux existants pour assurer une couverture universelle.

# B.6 Service Autonome de Sécurité Sociale des Parlementaires (SESOPA)

## Mission et branches couvertes

La SESOPA gère le régime de protection sociale des parlementaires nationaux.

<p class="table-caption"><strong>Tableau B.6.1</strong> — Branches de sécurité sociale couvertes, SESOPA</p>

| Branche | Couverte ? | Note |
|---|---|---|
| Vieillesse |  | Pension de retraite |
| Décès |  | Allocation aux ayants droit |
| Invalidité |  | Non mentionnée explicitement |
| Soins de santé |  | Non couverte par ce régime |
| AT/MP |  | Non couverte |

**Population assujettie :** parlementaires nationaux (Assemblée Nationale) et leurs ayants droit.

## Cadre juridique et institutionnel

<p class="table-caption"><strong>Tableau B.6.2</strong> — Cadre juridique et institutionnel, SESOPA</p>

| Élément | Détail |
|---|---|
| Texte fondateur | Loi n° 88-002 du 29 janvier 1988 |
| Autorité de tutelle | Assemblée Nationale |
| Statut juridique | Service autonome placé sous la responsabilité de l'Assemblée Nationale |
| Régime | Régime spécial contributif (partiellement) |

## Données de couverture

<p class="table-caption"><strong>Tableau B.6.3</strong> — Données de couverture, SESOPA (2019–2025)</p>

| Indicateur | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| Parlementaires affiliés | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Bénéficiaires de pensions | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |

*Données non disponibles au moment du premier bulletin. À transmettre par la SESOPA.*

<!-- AUTO_GENERE:SESOPA:DEBUT -->

### Régimes gérés

<p class="table-caption"><strong>Tableau B.6.4</strong> — Régimes gérés, SESOPA</p>

| Régime | Type de financement | Caractère | Gestion | Administrateur | Fonctions couvertes | Années ESS disponibles |
|---|---|---|---|---|---|---|
| Branche des pensions  de retraite et de réversion | Mixte | Obligatoire | Publique | SESOPA Assemblée nationale | Vieillesse; Survivances | 2026 |
| Assurance maladie des parlementaires | Non-contributif | — | Publique | SESOPA Assemblée nationale | Soins de santé | 2026 |
| Assurance décès -rente spéciale de survie | Non-contributif | — | Publique | SESOPA Assemblée nationale | Survivances | 2026 |
| Branche des risques liés à l'exercice du mandat parlementaire | Non-contributif | — | Publique | SESOPA Assemblée nationale | Invalidité / Handicap; Survivances; Accident du travail; Soins de santé | 2026 |
| Assurance maternité des parlementaires | Non-contributif | — | Publique | SESOPA Assemblée nationale | Maternité / Paternité; Soins de santé | 2026 |

### Aperçu graphique (tous régimes, toutes années)

<p class="fig-caption"><strong>Figure B.6.1</strong> — Évolution des cotisants, bénéficiaires, dépenses et recettes (tous régimes), SESOPA (2019–2025)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_SESOPA_cotisants.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_SESOPA_beneficiaires.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_SESOPA_depenses.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_SESOPA_depense_par_beneficiaire.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_SESOPA_recettes.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_SESOPA_contribution.png" style="width:100%; height:auto;"></td></tr>
</table>

### Répartition par sexe (cotisants et bénéficiaires cumulés)

<p class="fig-caption"><strong>Figure B.6.2</strong> — Répartition par sexe des cotisants et bénéficiaires cumulés, SESOPA (2019–2025)</p>

<p align="center" style="font-size:0.85em; color:#4a5568; margin-bottom:4px;"><em>Gauche : cotisants &middot; droite : bénéficiaires</em> &nbsp;&nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#2e78c8;margin-right:4px;"></span>Hommes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#d4487a;margin-right:4px;"></span>Femmes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#a9b4c0;margin-right:4px;"></span>Non identifié</p>
<p align="center"><img src="/files/04_annexes/illustrations/annexe_B_SESOPA_sexe.png" style="width:100%; height:auto; max-width:620px;"></p>

### Données détaillées (par régime et année)

<p class="table-caption"><strong>Tableau B.6.5</strong> — Données détaillées par régime et année, SESOPA (2019–2025)</p>

| Régime | Année | Cotisants totaux | Bénéficiaires totaux | Dépenses totales (Mds CDF) | Recettes totales (Mds CDF) | Dép. moy./bénéf. (k CDF) | Rec. moy./cotisant (k CDF) |
|---|---|---|---|---|---|---|---|
| Branche des pensions  de retraite et de réversion | 2019–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Branche des pensions  de retraite et de réversion | 2026 | 2,315 | 1,959 | — | — | — | — |
| Assurance maladie des parlementaires | 2019–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Assurance maladie des parlementaires | 2026 | — | — | — | — | — | — |
| Assurance décès -rente spéciale de survie | 2019–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Assurance décès -rente spéciale de survie | 2026 | — | — | — | — | — | — |
| Branche des risques liés à l'exercice du mandat parlementaire | 2019–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Branche des risques liés à l'exercice du mandat parlementaire | 2026 | — | — | — | — | — | — |
| Assurance maternité des parlementaires | 2019–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |
| Assurance maternité des parlementaires | 2026 | — | — | — | — | — | — |

*Source : base ESS OIT/BIT (protection_sociale_rdc.db). Visuels et tableaux générés automatiquement, sans navigateur, via `py 09_scripts/generer_annexe_b_visuels.py`.*

<!-- AUTO_GENERE:SESOPA:FIN -->

## Évolutions et réformes en cours

*[À compléter à réception des informations de la SESOPA.]*

# B.7 Régimes spéciaux non contributifs de la fonction publique

<!-- AUTO_GENERE:TRESOR:DEBUT -->

### Régimes gérés

<p class="table-caption"><strong>Tableau B.7.1</strong> — Régimes gérés, TRESOR</p>

| Régime | Type de financement | Caractère | Gestion | Administrateur | Fonctions couvertes | Années ESS disponibles |
|---|---|---|---|---|---|---|
| Pensions de retraite octroyé de la fonction publique | Non-contributif | Obligatoire | Publique | Trésor public | Vieillesse; Survivances | 2019, 2020, 2021, 2022 |

### Aperçu graphique (tous régimes, toutes années)

<p class="fig-caption"><strong>Figure B.7.1</strong> — Évolution des cotisants, bénéficiaires, dépenses et recettes (tous régimes), TRESOR (2019–2025)</p>

<table style="width:100%; border-collapse:collapse;">
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_TRESOR_cotisants.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_TRESOR_beneficiaires.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_TRESOR_depenses.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_TRESOR_depense_par_beneficiaire.png" style="width:100%; height:auto;"></td></tr>
<tr><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_TRESOR_recettes.png" style="width:100%; height:auto;"></td><td style="width:50%; padding:4px;"><img src="/files/04_annexes/illustrations/annexe_B_TRESOR_contribution.png" style="width:100%; height:auto;"></td></tr>
</table>

### Répartition par sexe (cotisants et bénéficiaires cumulés)

<p class="fig-caption"><strong>Figure B.7.2</strong> — Répartition par sexe des cotisants et bénéficiaires cumulés, TRESOR (2019–2025)</p>

<p align="center" style="font-size:0.85em; color:#4a5568; margin-bottom:4px;"><em>Gauche : cotisants &middot; droite : bénéficiaires</em> &nbsp;&nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#2e78c8;margin-right:4px;"></span>Hommes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#d4487a;margin-right:4px;"></span>Femmes &nbsp;&nbsp; <span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:#a9b4c0;margin-right:4px;"></span>Non identifié</p>
<p align="center"><img src="/files/04_annexes/illustrations/annexe_B_TRESOR_sexe.png" style="width:100%; height:auto; max-width:620px;"></p>

### Données détaillées (par régime et année)

<p class="table-caption"><strong>Tableau B.7.2</strong> — Données détaillées par régime et année, TRESOR (2019–2025)</p>

| Régime | Année | Cotisants totaux | Bénéficiaires totaux | Dépenses totales (Mds CDF) | Recettes totales (Mds CDF) | Dép. moy./bénéf. (k CDF) | Rec. moy./cotisant (k CDF) |
|---|---|---|---|---|---|---|---|
| Pensions de retraite octroyé de la fonction publique | 2019 | 1,450,668 | — | — | — | — | — |
| Pensions de retraite octroyé de la fonction publique | 2020 | 1,450,668 | — | — | — | — | — |
| Pensions de retraite octroyé de la fonction publique | 2021 | 1,432,427 | — | — | — | — | — |
| Pensions de retraite octroyé de la fonction publique | 2022 | 1,424,573 | — | — | — | — | — |
| Pensions de retraite octroyé de la fonction publique | 2023–2025 | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] | [N/D] |

*Source : base ESS OIT/BIT (protection_sociale_rdc.db). Visuels et tableaux générés automatiquement, sans navigateur, via `py 09_scripts/generer_annexe_b_visuels.py`.*

<!-- AUTO_GENERE:TRESOR:FIN -->

*Note : la vue « TRESOR » est utilisée ici comme proxy opérationnel des régimes spéciaux non contributifs financés par le Trésor public.*

*Ces régimes sont financés par le Trésor public et destinés à des catégories spécifiques d'agents de l'État. Leur identification exhaustive est difficile : le premier bulletin note explicitement qu'il a été impossible d'en obtenir une liste complète et des données détaillées.*

## Régimes identifiés

| Régime | Autorité en charge | Texte juridique | Population protégée | Financement | Branches couvertes |
|---|---|---|---|---|---|
| Régime de la Présidence et Primature | Présidence de la République et Primature | Ordonnance n° 82-046 du 31 mars 1982 | Agents publics de l'État et leurs ayants droit | Trésor public | Soins médicaux, indemnité de cessation de mandat, vieillesse, décès, invalidité |
| Régime militaire | Ministère de la Défense et des Anciens Combattants | N/A (non précisé) | Militaires et leurs ayants droit | Trésor public | Vieillesse, décès, invalidité |
| Régime des magistrats | Ministère de la Justice | Ordonnance-Loi n° 88-056 du 29 septembre 1988 | Magistrats civils et militaires de l'ordre de justice et leurs ayants droit | Trésor public | Vieillesse, décès, invalidité |

## Données disponibles

Aucune donnée statistique détaillée n'a pu être obtenue pour ces régimes lors de la préparation du premier bulletin. L'obtention de données auprès des ministères de tutelle constitue un objectif prioritaire pour le présent bulletin.

## Perspective de collecte

*[À compléter selon les données reçues des ministères concernés : Présidence / Primature, Défense, Justice.]*