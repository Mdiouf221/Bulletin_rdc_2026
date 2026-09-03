# Décisions méthodologiques

<!-- NOTE_INTERNE
Objet du fichier :
Conserver les décisions méthodologiques transversales prises pendant la préparation du bulletin.

Règle de travail :
Les décisions doivent être formulées clairement, avec leur statut : actée, à confirmer, en discussion ou abandonnée.
-->

## Décisions actées

### DM-001 — Couverture effective comme angle statistique principal

Le bulletin privilégie la couverture effective comme angle statistique principal. La couverture légale peut être présentée lorsque cela est utile, mais l’analyse statistique vise prioritairement les personnes effectivement couvertes, affiliées, cotisantes ou bénéficiaires selon les données disponibles.

**Statut :** actée  
**Impact :** chapitre 1, chapitre 3, chapitre 7

### DM-002 — Conservation des notes internes dans les fichiers Markdown

Les notes internes sont conservées dans les fichiers Markdown de travail, sous forme de commentaires `<!-- NOTE_INTERNE ... -->`.

Ces notes servent à guider la rédaction, les révisions et le travail des agents. Elles ne doivent pas apparaître dans la version finale destinée à publication.

**Statut :** actée  
**Impact :** tous les fichiers de rédaction

### DM-003 — Documentation des sources au niveau pertinent

Les sources spécifiques ne sont pas toutes présentées globalement dans le chapitre conceptuel. Elles doivent être documentées au niveau des institutions, indicateurs, tableaux ou annexes concernés.

**Statut :** actée  
**Impact :** chapitre 1, chapitre 2, chapitre 3, chapitre 7, annexes

### DM-004 — Distinction entre institution, régime, programme, branche et prestation

Le bulletin doit distinguer clairement :

- l’institution gestionnaire ;
- le régime ou programme ;
- la branche ou fonction couverte ;
- la prestation ;
- la population couverte ;
- les bénéficiaires ;
- les cotisants ;
- les dépenses.

**Statut :** actée  
**Impact :** chapitre 1, chapitre 2, chapitre 3, annexes

### DM-005 — Traitement prudent des dispositifs difficilement mesurables

Les services sociaux, gratuités, interventions d’urgence, programmes sectoriels ou mesures d’accompagnement social doivent être traités avec prudence lorsqu’ils ne donnent pas lieu à une prestation individualisable ou à des données permettant d’identifier des personnes couvertes, bénéficiaires, prestations servies ou dépenses.

**Statut :** actée  
**Impact :** chapitre 1, chapitre 2, chapitre 3, chapitre 7

## Décisions à confirmer

### DM-006 — Statut exact de la santé dans le bulletin

Le bulletin prévoit un chapitre spécifique sur la santé et la couverture sanitaire. Le statut méthodologique exact de la santé doit être clarifié, notamment concernant son articulation avec les indicateurs ODD 1.3.1 et les indicateurs agrégés.

**Statut :** à confirmer  
**Impact :** chapitre 1, chapitre 3, chapitre 4

### DM-007 — Liste finale des institutions contributrices

La liste finale des institutions contributrices devra être confirmée à partir des données effectivement reçues, des échanges avec les points focaux et des validations institutionnelles.

**Statut :** à confirmer  
**Impact :** chapitre 2, annexes

### DM-008 — Critères définitifs d’inclusion dans les indicateurs

Les critères d’inclusion dans les indicateurs devront être stabilisés à partir du cadre conceptuel, des données disponibles et des limites propres à chaque source.

**Statut :** à confirmer  
**Impact :** chapitre 1, chapitre 3, chapitre 7

### DM-009 — Niveau de détail des annexes statistiques

Le niveau de détail à inclure dans les annexes statistiques devra être fixé en fonction du volume de données disponibles et de la lisibilité du bulletin principal.

**Statut :** à confirmer  
**Impact :** annexes, chapitre 3, chapitre 6

### DM-019 — Rupture apparente des cotisants CNSSAP (régime de base) entre 2022 et 2023

**Constat (relecture du 2026-09-02) :** La base institutionnelle (`06_donnees/protection_sociale_rdc.db`, table `indicateurs_regime`) enregistre un bond des cotisants actifs CNSSAP (régime de base, CNSSAP_R1) de 198 399 en 2022 à 1 004 106 en 2023, soit une variation de +406 % — largement supérieure au seuil de 50 % que DM-010 (règle 5) définit comme alerte de rupture méthodologique. Le champ `couverture_effective_total` de la table `prestations_historique` montre par ailleurs une valeur quasi identique (≈1 003 277) répétée sur les trois prestations CNSSAP_R1 de 2023, ce qui suggère qu'il pourrait s'agir d'un effectif d'affiliés/éligibles (N3) plutôt que de cotisants actifs au sens strict (N4) — à confirmer.

**Hypothèse de travail, non confirmée :** ce changement pourrait refléter la réforme de transfèrement des agents publics vers la CNSSAP (mentionnée en section 3.1 du chapitre 3 et en 4.2/4.3), qui aurait fait basculer un grand nombre d'agents dans le périmètre CNSSAP en 2023. Cette hypothèse doit être vérifiée directement auprès de la CNSSAP avant toute utilisation de la donnée 2023 dans un tableau ou un indicateur.

**Précaution déjà appliquée :** le Tableau 4.3 (chapitre 4, section âge actif) affiche prudemment `[N/D]` pour les cotisants CNSSAP 2023-2025 plutôt que ce chiffre non vérifié. Cette prudence doit être maintenue tant que ce point n'est pas confirmé.

**Statut :** à confirmer  
**Impact :** chapitre 4 (sections 4.2, 4.3), chapitre 5 (sous-indicateur ODD 2.9), matrice de couverture CNSSAP, Annexe B  
**Référence :** DM-010, DM-012 ; à instruire auprès de la CNSSAP (donnée source ESS CNSSAP 2023)

### DM-020 — Nature des données SESOPA pour les exercices 2019–2026 (valeurs reconduites à l'identique)

**Constat (relecture du 2026-09-02, actualisé le 2026-09-03) :** Les valeurs SESOPA enregistrées dans `indicateurs_regime` (cotisants_total = 2 315, bénéficiaires_total = 1 959) sont strictement identiques pour les huit exercices 2019 à 2026, y compris pour 2026 — année non encore écoulée à la date de préparation du bulletin. Ceci pourrait indiquer une valeur de référence ponctuelle reconduite par défaut plutôt que des données annuelles réellement observées. L'alerte initiale concernant la MESP 2025 est levée : la dernière ESS intégrée renseigne 112 608 cotisants et 217 171 bénéficiaires en 2025, contre 96 538 et 196 574 en 2024.

**Statut :** à confirmer  
**Impact :** Annexe B (fiche SESOPA), tous les tableaux mentionnant SESOPA pour ces années  
**Référence :** à instruire auprès du SESOPA (toutes années 2019-2026) — vérifier si une ESS a été transmise chaque année ou si la dernière valeur connue a été reconduite par défaut

## Décisions actées (suite — issues de la session 2026-06-09)

### DM-010 — Règle de conversion foyers/bénéficiaires pour les prestations enfants et transferts familiaux

**Principe général :**
Lorsqu'une institution déclare ses données par **foyer bénéficiaire** ou par **récipiendaire principal** (et non par enfant ou par individu couvert), il est nécessaire d'appliquer un facteur multiplicateur pour estimer le nombre réel d'enfants ou de personnes couvertes.

**Règles opérationnelles :**

1. **Vérification préalable obligatoire** : pour chaque année et chaque régime, identifier explicitement si la donnée déclarée est exprimée en foyers, en récipiendaires principaux ou en individus/enfants. Cette vérification doit être documentée dans les métadonnées de l'ESS concernée.

2. **Conservation du multiplicateur historique** : le facteur 3,17 enfants/foyer utilisé dans le 1er bulletin est maintenu pour les années déjà traitées (2019–2022). Il ne doit pas être modifié rétrospectivement afin de préserver la cohérence de la série.

3. **Nouveau multiplicateur pour chaque nouvelle année** : lorsqu'une nouvelle année est intégrée et que l'institution déclare encore ses données par foyer, le facteur multiplicateur approprié doit être **recherché et discuté explicitement** avant d'être appliqué. Il ne peut pas être reconduit automatiquement d'une année à l'autre sans vérification.

4. **Règle générale pour tous les transferts familiaux** : cette règle s'applique à toutes les prestations enfants et à tous les transferts aux familles exprimés par foyer ou par récipiendaire principal, quelle que soit l'institution (CNSS, CNSSAP, PAM, MINAS, etc.).

5. **Alerte rupture méthodologique** : si entre deux déclarations successives une institution change sa manière de reporter (passage de foyers à individus, ou inversement), cela peut provoquer une variation spectaculaire apparente du nombre de bénéficiaires. Une telle rupture doit être :
   - détectée automatiquement (variation > 50 % d'une année sur l'autre sans justification programmatique) ;
   - signalée comme alerte dans les données ;
   - documentée explicitement dans le bulletin (encadré méthodologique ou note de bas de page).

**Statut :** actée  
**Impact :** sous-indicateur ODD 2.2 (enfants), sous-indicateur 2.8 (assistance/transferts), tous tableaux de couverture par branche famille

### DM-011 — Exclusion des programmes humanitaires externes et des prestations en nature de ODD 1.3.1

**Principe général :**
L'inclusion d'un programme ou régime dans les indicateurs ODD 1.3.1 n'est pas automatique. Elle doit être instruite selon PROC-009 (grille des 5 critères) et documentée dans le registre d'inclusion (`registre_inclusion_programmes.md`).

**Décisions actées sur des programmes spécifiques :**

1. **Transferts monétaires PAM** : exclus de ODD 1.3.1. Le seul critère favorable (prestation en espèces) est insuffisant pour compenser l'absence de cadre statutaire national, de responsabilité primaire étatique, de permanence et de financement national. Classé « Indicateur connexe » — présenté dans le tableau des programmes non statutaires.

2. **Repas scolaires PAM/MEPST** : exclus de ODD 1.3.1 par définition (prestation en nature ; ODD 1.3.1 = prestations en espèces uniquement selon WSPR 2024-26). Peut figurer dans des indicateurs connexes (alimentation, éducation).

**Règle générale :**
Tout programme présentant au moins une réponse négative parmi les critères C2–C5 (cadre statutaire, responsabilité État, permanence, financement) doit être instruit selon PROC-009 avant d'être inclus ou exclu. Cette instruction produit une fiche dans le registre. Le jugement motivé prime sur l'application mécanique des critères.

**Leçon de méthode :**
La décision d'inclusion est rarement binaire. Des programmes qui ressemblent à des programmes similaires déjà inclus peuvent en différer sur des critères essentiels. L'examen multi-critères protège à la fois contre l'inclusion abusive (gonflement artificiel des indicateurs) et contre l'exclusion injustifiée (sous-estimation de la couverture réelle).

**Statut :** actée  
**Impact :** tous les indicateurs ODD, tous les tableaux de couverture  
**Référence :** PROC-009, `registre_inclusion_programmes.md`

### DM-012 — Distinction des 5 niveaux de couverture par régime

**Principe :**
Pour chaque régime de protection sociale, le bulletin doit distinguer systématiquement cinq niveaux de population, dès lors que les données sont disponibles :

- **N1 — Population totale de référence** : population totale du secteur ou groupe démographique concerné (ex. : tous les travailleurs RDC, toute la population, tous les enfants 0–17 ans).
- **N2 — Population légalement couverte** : population que la loi ou le statut désigne comme devant être couverte. Ne présuppose pas l'affiliation effective.
- **N3 — Population affiliée / enregistrée** : personnes immatriculées auprès de l'institution, indépendamment de la cotisation active.
- **N4 — Cotisants actifs** : personnes pour lesquelles une cotisation est effectivement versée sur la période de référence. Pour les régimes non contributifs : personnes éligibles activement enregistrées dans le système de ciblage.
- **N5 — Bénéficiaires effectifs** : personnes ayant effectivement reçu au moins une prestation en espèces sur la période de référence.

**Règles d'application :**

1. **ODD 1.3.1** utilise uniquement N4 et N5 (couverture effective).
2. **Le gap N2 − (N4 + N5)** mesure le potentiel d'extension de couverture et doit être présenté et commenté dans le bulletin.
3. **Le gap N3 − N4** mesure la non-conformité des employeurs ou le sous-enregistrement.
4. Quand une donnée est absente, utiliser le placeholder **N/D** dans la matrice — ne pas omettre le niveau.
5. Distinguer systématiquement les données **administratives directes** (ESS) des **estimations** (ILOSTAT, ONU, INS).

**Cas CNSSAP illustratif :**
Le gap entre N2 (~1 623 000 fonctionnaires légalement couverts) et N4 (198 399 cotisants réels en 2022) illustre précisément la différence couverture légale / couverture effective. Ce gap s'explique par les agents non mécanisés (non mis sur liste de paie) et se résorbe progressivement via la réforme de basculement et les vagues de mécanisation (40 000 en 2021-2022, 101 000 en 2023).

**Leçon de méthode :**
Ces cinq niveaux permettent non seulement de calculer ODD 1.3.1, mais aussi de construire des indicateurs connexes sur les opportunités d'extension de couverture — angle stratégique central pour les politiques de protection sociale.

**Statut :** actée
**Impact :** tous les régimes, tous les tableaux de couverture, chapitre 3, annexes
**Référence :** `matrice_couverture_regimes.md`

### DM-013 — Versionnage des paramètres de calcul par année

**Principe :**
Certains paramètres de calcul des indicateurs peuvent évoluer d'une année à l'autre : âge légal de retraite, facteur de conversion foyers/enfants, seuil de pauvreté national, population de référence. Ces paramètres doivent être **renseignés et documentés pour chaque année** dans la matrice ou les outils de calcul.

**Règle de stabilité des séries publiées :**
Les paramètres utilisés dans le 1er bulletin sont **figés pour les années qu'il couvre**. Ils ne doivent pas être modifiés rétrospectivement, sauf en cas d'erreur manifeste nécessitant une correction documentée. L'objectif est de préserver la cohérence des séries temporelles publiées.

**Application pour l'âge légal de retraite :**
- CNSS : 65 ans (hommes) / 60 ans (femmes) selon le Code du travail
- CNSSAP : 60 ans pour les deux
- Ce paramètre peut évoluer si une réforme légale intervient
- Pour chaque nouvelle année intégrée, vérifier si l'âge légal a changé et le documenter explicitement
- En cas de changement, ne pas recalculer les années antérieures

**Portée générale :**
Cette règle s'applique à tout paramètre exogène entrant dans le calcul des indicateurs : facteur enfants/foyer (DM-010), âge légal de retraite, seuil de pauvreté, population de référence démographique, etc.

**Statut :** actée
**Impact :** tous les indicateurs, tous les tableaux, outils de calcul
**Référence :** `matrice_couverture_regimes.md`, `indicateurs_odd_regles_calcul.md`

### DM-014 — Indicateur 2.5 AT/MP : force de travail (labour force 15+) comme dénominateur

**Principe :**
Le sous-indicateur ODD 1.3.1 2.5 (protection contre les accidents du travail et maladies professionnelles) utilise la **force de travail (labour force 15+)** comme dénominateur. Cela correspond exactement à la définition ILOSTAT/SDG qui mesure la « *Labour force covered in the event of work injury* ».

**Définition OIT confirmée :**
Les données ILOSTAT SDG_0131_SEX_SOC_RT_A pour la RDC (2022) portent explicitement le libellé : « Function: Labour force covered in the event of work injury » → 1,8 %. La force de travail (labour force) = personnes en emploi + chômeurs (définition BIT).

**Calcul du dénominateur :**
- Force de travail = Population 15+ × Taux de participation à la force de travail
- Taux de participation RDC = **63,44 %** (ILOSTAT, enquête MICS 2020, stable depuis 2016)
- Population 15+ = Population totale − Population 0-14 ans (WPP)

**Vérification croisée (2022) :**
- Cotisants CNSS AT/MP : 613 761
- Force de travail calculée : 35 005 912 (Pop 15+ 55,2M × 63,44 %)
- Notre taux : 613 761 / 35 005 912 = **1,75 %**
- Taux OIT publié : **1,8 %** (concordance à l'arrondi près, l'OIT utilise ~34M)

**Sources de données :**
- Population 15+ : BM/WPP (dérivée de pop totale − pop 0-14)
- Taux de participation : ILOSTAT EAP_DWAP_SEX_AGE_RT_A (63,44 % MICS 2020)
- Cotisants AT/MP (numérateur) : CNSS ESS Régime 2 + CNSSAP ESS Régime AT/MP (à partir 2023)

**Statut :** actée (2026-07-04, révisée 2026-07-05)
**Impact :** sous-indicateur ODD 2.5 AT/MP, tous les tableaux de couverture professionnelle, chapitre 3, chapitre 4
**Référence :** `indicateurs_odd_regles_calcul.md` (section 5a), ILOSTAT SDG_0131_SEX_SOC_RT_A

### DM-015 — Actualisation des données démographiques pré-chargées du Dashboard (juillet 2026)

**Principe :**
Les données démographiques pré-chargées dans le Dashboard (fichier `visualiser_regimes.py`, section `static_rows`) utilisaient une révision obsolète des données BM/WPP. Un audit réalisé le 2026-07-04 a mis en évidence des écarts significatifs avec les données actuelles des API officielles.

**Écarts constatés (année 2022) :**

| Champ | Ancienne valeur | Nouvelle valeur | Écart |
|-------|----------------|-----------------|-------|
| Population totale | 95 240 792 | 102 396 968 | +7,5 % |
| Population active (15-64) | 54 832 901 | 52 040 020 | −5,1 % |
| Population retraite (65+) | 2 067 543 | 3 139 539 | +51,8 % |
| Population handicap (15%) | 14 286 119 | 15 359 545 | +7,5 % |
| Naissances vivantes | 3 923 921 | 4 262 069 | +8,6 % |

**Correction appliquée :**
Les `static_rows` pour 2019-2022 ont été remplacées par les valeurs issues des API BM (SP.POP.TOTL, SP.POP.1564.TO, SP.POP.65UP.TO, SP.DYN.CBRT.IN) et WPP 2024 (PopulationPyramid.net), consultées le 2026-07-04.

**Note sur la population enfants (0-14) :**
Les valeurs WPP pour les 0-14 ans étaient déjà correctes et n'ont pas changé.

**Note sur l'API OMS GHO :**
L'API GHO de l'OMS ne contient aucun indicateur de prévalence du handicap par pays. La fonction `fetchWHO_DisabilityPrevalence()` dans le Dashboard est effectivement du code mort — elle tombe toujours en fallback 15 %. Le taux de 15 % est justifié par le Rapport mondial sur le handicap (OMS, 2011 : 15,6 % prévalence globale).

**Statut :** actée (2026-07-04)
**Impact :** tous les sous-indicateurs ODD 1.3.1, Dashboard onglet Indicateurs
**Référence :** `visualiser_regimes.py` (section `static_rows`), API BM et WPP consultées le 2026-07-04

### DM-016 — Indicateur 2.9 : dénominateur = population 15-64 (BM) et non force de travail (ILOSTAT)

**Principe :**
Le sous-indicateur ODD 1.3.1 2.9 (cotisants actifs aux régimes de retraite) utilise comme dénominateur la **population en âge de travailler (15-64 ans)** issue de la Banque mondiale (SP.POP.1564.TO), et non la **force de travail 15+** (labour force) d'ILOSTAT.

**Justification :**
- La définition OIT stricte utilise la force de travail (employed + unemployed), soit ~35 M pour la RDC.
- La population 15-64 BM (~52 M en 2022) inclut aussi les personnes hors force de travail (étudiants, au foyer).
- Le choix de la population 15-64 est **plus conservateur** : il produit un taux plus bas (1,56 % vs ~2,3 %).
- Ce choix est documenté et transparent ; les deux valeurs peuvent être présentées en parallèle.

**Impact sur les calculs (2022) :**
- Cotisants CNSS R3 + CNSSAP R1 : 812 160
- Pop 15-64 (BM) : 52 040 020 → **taux = 1,56 %**
- Force de travail (ILOSTAT, estimation) : ~35 M → **taux ≈ 2,3 %**
- Estimation OIT WSPR : ~6,4 % (méthode et périmètre différents)

**Statut :** actée (2026-07-04)
**Impact :** sous-indicateur ODD 2.9, chapitre 4
**Référence :** `indicateurs_odd_regles_calcul.md`, `visualiser_regimes.py`

### DM-018 — Population totale et structure par âge : INS-RDC 2026 comme référence principale (2019-2024)

**Décision (session du 2026-09-02) :**
Entre l'estimation de la Division de la population des Nations Unies (ONU WPP 2024, révision de juillet 2024) et les projections démographiques nationales transmises par l'INS-RDC (canevas de collecte 2026), c'est la série **INS-RDC** qui est retenue comme **référence principale** du bulletin pour la population totale et sa structure par âge/sexe (agrégats 0+, 0-14, 0-17, 15+, 60+, 65+), sur la période où elle est disponible (2019-2024), **dans la base comme dans le texte du bulletin**. La série ONU WPP 2024 est conservée en comparaison et reste la seule source disponible pour : les projections au-delà de 2024 (dont 2025), l'âge médian, le ratio de dépendance détaillé (nécessite la tranche 15-64 ans, absente des données INS-RDC transmises), l'urbanisation, la ruralité et la densité de population — dimensions non couvertes par le canevas INS-RDC 2026.

**Cette décision remplace explicitement une décision antérieure prise le même jour (2026-09-02, session distincte — voir `00_pilotage/journal_modifications.md`, entrées relatives à la « Priorisation systématique du dénominateur INS/RDC » et à la « Synchronisation base SQLite ↔ Excel »).** Cette décision antérieure avait au contraire choisi de conserver l'ONU WPP/ILOSTAT comme référence prioritaire dans la base brute et dans le texte de la section 0.1, en réservant l'usage de l'INS-RDC aux seuls dénominateurs des indicateurs ODD 1.3.1 calculés par le tableau de bord (mécanisme `dashboard_settings.json` → `denomSettings.denominatorConstructions`, source manuelle). Sur confirmation explicite de l'utilisateur (session du 2026-09-02, après signalement du conflit), DM-018 prime désormais sur ce choix antérieur : l'INS-RDC devient la référence principale de façon généralisée, y compris dans la base brute et le texte narratif, et pas seulement pour les calculs d'indicateurs ODD.

**Justification :** source nationale directe, plus récente (transmise le 2026-09-01), et cohérente à l'arrondi près avec la série ONU WPP 2024 (écarts de l'ordre de 1 % selon les années et tranches d'âge).

**Mise en œuvre technique :** dans `protection_sociale_rdc.db` (racine), table `denominateurs_ref`, toutes les requêtes de résolution de dénominateur trient les lignes candidates par `ORDER BY priority DESC, id ASC` (la valeur de `priority` la plus **élevée** l'emporte ; à égalité, la ligne la plus anciennement insérée l'emporte). Les 108 lignes `source='src-ins-rdc-2026'` (var_code='var-c-popsx', COD, années 2019-2024) ont donc été passées à `priority=1` pour l'emporter effectivement, et les lignes `source='src-unwpp-2024jul-rev'` correspondant exactement aux mêmes combinaisons (année, sexe, âge) ont été ramenées à `priority=0`. *Point de vigilance corrigé en cours de session : une première tentative avait, par erreur d'interprétation du sens de `priority` (en supposant à tort que la valeur la plus **basse** l'emporte), fait l'inverse — INS à `priority=0`, WPP à `priority=1` — ce qui aurait fait gagner l'ONU WPP dans les requêtes réelles malgré l'intention contraire. Erreur détectée et corrigée avant régénération des sorties (tableau de bord, Annexe C, bulletin assemblé).* Les autres lignes ONU WPP (années hors 2019-2024, tranches d'âge non couvertes par l'INS) restent `priority=0`, faute d'alternative.

**Statut :** actée (2026-09-02)
**Impact :** section 0.1 (contexte démographique), tous les calculs utilisant la population totale ou la structure par âge/sexe 2019-2024 comme dénominateur, tableau de bord (`dashboard_regimes.html`), Annexe C
**Référence :** `02_introduction_generale/0_1_contexte_demographique.md`, `protection_sociale_rdc.db` (table `denominateurs_ref`)

## Décisions en discussion

### DM-021 — Anomalie des prestations AT/MP CNSS 2024 (valeur uniforme suspecte)

**Constat (relecture du 2026-09-02, mise à jour du chapitre 4 avec les données 2023-2024) :** Les 11 types de prestations de la branche Risques professionnels de la CNSS (Régime 2) pour l'exercice 2024 affichent tous exactement la même valeur de bénéficiaires (2 853), qu'il s'agisse d'une rente d'incapacité, de frais funéraires, de fourniture de lunettes ou de transport de la victime. Cette uniformité est statistiquement très improbable pour des prestations de nature aussi différente et contraste avec les années 2019-2023, où seules 2 des 11 prestations sont renseignées avec des valeurs distinctes et plausibles (ex. 2023 : incapacité = 1 020, survivants = 1 608).

**Hypothèse de travail, non confirmée :** erreur de saisie ou d'extraction de l'ESS CNSS 2024 — une valeur unique (peut-être un total de sinistres déclarés ou un total de bénéficiaires toutes prestations confondues) aurait été dupliquée par erreur sur l'ensemble des lignes de prestations lors de l'import.

**Précaution appliquée :** cette valeur n'est pas utilisée dans le détail par type de prestation AT/MP du Tableau 4.5 (chapitre 4.3) pour 2024, qui reste `[N/D]` avec une note signalant l'anomalie, en attendant vérification auprès de la CNSS ou nouvelle extraction du fichier source. Par ailleurs, le montant unitaire de la rente AT/MP déclaré pour 2023 (180 000 CDF) romprait la correspondance historique avec le montant de la pension de vieillesse de la même année (230 000 CDF, Tableau 4.2) ; cette valeur n'est pas non plus retenue dans les tableaux 4.5 et 4.13, dans l'attente de confirmation.

**Statut :** en discussion  
**Impact :** chapitre 4 (section 4.3, Tableau 4.5), Annexe B (fiche CNSS)  
**Référence :** à instruire auprès de la CNSS (fichier source ESS CNSS 2024, branche Risques professionnels)

### DM-017 — Traitement de la protection statutaire budgétaire des agents publics

Le bulletin distingue la couverture contributive observée par la CNSSAP de la protection statutaire non contributive directement financée par le budget de l’État. Cette seconde composante comprend les régimes spéciaux et, séparément, les agents publics hors CNSSAP dont la protection budgétaire effective peut être officiellement documentée.

Son inclusion dans le calcul national du sous-indicateur relatif aux actifs est subordonnée à cinq conditions : une base statutaire en vigueur, une population identifiable, des droits ou prestations identifiables, un financement budgétaire documenté et exécuté, et l’absence de double comptage dans le numérateur considéré.

L’écart entre l’effectif estimé de l’emploi public et les affiliés ou cotisants CNSSAP ne constitue pas une mesure suffisante de cette couverture. La mécanisation facilite la retenue des cotisations, mais ne doit pas être confondue avec l’immatriculation à la CNSSAP. Les composantes contributive et budgétaire sont présentées séparément avant toute consolidation.

Dans les fichiers de données et certaines sorties automatisées, le code technique `TRESOR` désigne cette composante budgétaire hors CNSSAP. Il ne correspond pas à une institution gestionnaire. À titre d’hypothèse de travail, les agents publics concernés sont considérés comme relevant d’un dispositif non contributif financé par allocation budgétaire. Leur effectif est estimé par différence à partir des effectifs globaux de la Fonction publique — 1 622 972 pour chacune des années 2019 à 2022, 1 425 000 en 2023 et 1 727 000 en 2024 — et des effectifs CNSSAP retenus dans la base. Les résultats ainsi obtenus sont des estimations de personnes potentiellement couvertes ; ils ne constituent ni un décompte de cotisants ni, à eux seuls, la preuve d’une couverture effective individuelle.

**Statut :** acté comme hypothèse de travail, à confirmer par des données administratives
**Impact :** cartographie institutionnelle, sections 4.2, 4.3 et 5.1, tableaux 2.2, 4.1, 4.3, 5.1 et 5.2, annexes B et C

## Décisions abandonnées

_Aucune décision abandonnée à ce stade._