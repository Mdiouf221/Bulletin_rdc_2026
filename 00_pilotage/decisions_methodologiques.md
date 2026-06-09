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

## Décisions en discussion

_Aucune décision en discussion à ce stade._

## Décisions abandonnées

_Aucune décision abandonnée à ce stade._