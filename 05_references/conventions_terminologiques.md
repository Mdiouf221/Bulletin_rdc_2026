# Conventions terminologiques

<!-- NOTE_INTERNE
Objet du fichier :
Fixer les choix de vocabulaire afin d’éviter les incohérences dans le bulletin.

Utilisation par les agents :
Les agents doivent respecter ces conventions lorsqu’ils rédigent ou révisent les sections.
-->

## Termes à utiliser de manière stable

| Terme recommandé | À éviter ou à utiliser avec prudence | Commentaire |
|---|---|---|
| Protection sociale | Aide sociale généralisée | La protection sociale est plus large que l’assistance sociale. |
| Couverture effective | Couverture réelle, couverture pratique | Utiliser “couverture effective” pour cohérence avec l’approche statistique. |
| Personnes couvertes | Population protégée, bénéficiaires potentiels | À distinguer des bénéficiaires effectifs. |
| Bénéficiaires | Personnes couvertes | Un bénéficiaire reçoit une prestation ; une personne couverte peut ne pas recevoir de prestation pendant la période. |
| Cotisants actifs | Affiliés | Un affilié n’est pas nécessairement cotisant actif. |
| Prestations servies | Bénéficiaires | Une personne peut recevoir plusieurs prestations. |
| Dépenses de prestations | Dépenses sociales | Être précis sur le périmètre des dépenses. |
| Régime | Institution | Une institution peut gérer plusieurs régimes. |
| Programme | Régime | Un programme peut être moins structuré ou moins statutaire qu’un régime. |
| Branche | Risque | Les deux notions sont liées, mais “branche” est préférable pour la classification statistique. |
| Dispositif statutaire budgétaire | Régime spécial, couverture implicite | Un régime spécial n’en est qu’une forme. La couverture doit être documentée et ne peut pas être déduite du seul statut d’agent public. |
| Agent public hors CNSSAP effectivement couvert par le budget de l’État | Agent non mécanisé couvert, cotisant implicite | Ne pas assimiler automatiquement absence de mécanisation, absence d’affiliation et couverture budgétaire effective. |
| Mécanisation | Immatriculation, affiliation | La mécanisation concerne l’intégration dans la paie de l’État ; l’immatriculation et l’affiliation concernent l’enregistrement auprès d’un régime ou d’une institution. |

## Règles de numérotation

- Utiliser une numérotation stable pour les chapitres : Chapitre 1, Chapitre 2, etc.
- Utiliser une numérotation décimale pour les sections : 1.1, 1.2, 1.3.
- Nommer les fichiers sans accents, sans apostrophes et sans espaces.
- Utiliser des underscores `_` dans les noms de fichiers.

## Règles de nommage des fichiers

Exemples recommandés :

- `1_1_definitions_approches.md`
- `1_2_approche_bit_oit.md`
- `0_1_contexte_demographique.md`
- `registre_tableaux.md`
- `registre_figures.md`

## Règles relatives aux tableaux

- Les tableaux doivent être numérotés par chapitre.
- Exemple : Tableau 2.1, Tableau 2.2, Tableau 3.1.
- Chaque tableau doit avoir :
  - un numéro ;
  - un titre ;
  - une source ;
  - une note méthodologique si nécessaire ;
  - un statut.

## Règles relatives aux figures

- Les figures doivent être numérotées par chapitre.
- Exemple : Figure 2.1, Figure 3.1.
- Chaque figure doit avoir :
  - un numéro ;
  - un titre ;
  - une source ;
  - une note méthodologique si nécessaire ;
  - un statut.

## Règles relatives aux notes internes

Les notes internes doivent être placées dans des commentaires Markdown/HTML :

```markdown
<!-- NOTE_INTERNE
Objectif :

Points à couvrir :

Logique rédactionnelle :

Points de vigilance :

Formulation possible :

Statut :
-->