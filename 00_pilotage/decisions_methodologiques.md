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

## Décisions en discussion

_Aucune décision en discussion à ce stade._

## Décisions abandonnées

_Aucune décision abandonnée à ce stade._