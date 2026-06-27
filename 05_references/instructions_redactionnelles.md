# Instructions rédactionnelles

<!-- NOTE_INTERNE
Objet du fichier :
Définir les principes rédactionnels applicables à l’ensemble du bulletin.

Utilisation par les agents :
Les agents doivent consulter ce fichier lorsqu’ils rédigent, révisent ou harmonisent une section du bulletin.
-->

## Style général

Le bulletin doit adopter un style institutionnel, clair, analytique et prudent. Il doit être compréhensible pour des décideurs publics, des institutions contributrices, des partenaires techniques et des lecteurs spécialisés en protection sociale.

## Principes de rédaction

- Commencer les sections par l’idée principale.
- Éviter les phrases inutilement longues.
- Éviter les répétitions entre chapitres.
- Ne pas surinterpréter les données disponibles.
- Distinguer les constats statistiques, les limites méthodologiques et les orientations de politique publique.
- Employer les termes techniques de manière stable.
- Privilégier les formulations qui reflètent la disponibilité réelle des données.
- Signaler les limites sans affaiblir inutilement la portée du bulletin.

## Ton attendu

- Institutionnel.
- Neutre.
- Diplomatique.
- Méthodologiquement prudent.
- Orienté vers la consolidation progressive du système statistique de protection sociale.

## Formulations à privilégier

- « Les données disponibles permettent de documenter… »
- « Les informations transmises indiquent… »
- « Sous réserve des limites de disponibilité et de désagrégation des données… »
- « Cette distinction est importante pour interpréter correctement les indicateurs… »
- « Le bulletin vise à consolider les informations disponibles plutôt qu’à se substituer aux systèmes d’information des institutions. »
- « Les résultats doivent être interprétés au regard du périmètre institutionnel et statistique couvert par les données disponibles. »
- « Cette lecture permet d’identifier les avancées documentées ainsi que les domaines nécessitant une amélioration de la disponibilité des données. »

## Formulations à éviter

- « Les données prouvent que… »
- « Le système est défaillant… »
- « Il est évident que… »
- « Toutes les institutions… »
- « Les chiffres démontrent définitivement… »
- « L’absence de données signifie l’absence de couverture… »
- « Les institutions ne disposent pas de données fiables… » sauf si cela est explicitement documenté et validé.

## Règles spécifiques au bulletin

- Ne pas réduire la protection sociale à l’assistance sociale.
- Ne pas confondre couverture légale, affiliation, cotisation active, bénéfice d’une prestation et couverture effective.
- Ne pas présenter les ménages bénéficiaires comme des individus couverts sans hypothèse explicite.
- Ne pas convertir des prestations servies en bénéficiaires uniques sans information méthodologique.
- Distinguer les données observées, les estimations, les hypothèses et les commentaires méthodologiques.

## Conventions visuelles — Figures et tableaux

### Figures

Les figures (graphiques, cartes, schémas) sont insérées avec la légende immédiatement avant l'image, en utilisant `<p class="fig-caption">` :

```markdown
<p class="fig-caption"><strong>Figure 2.1</strong> — Titre de la figure</p>

![Texte alternatif](/files/08_figures/exports/FIG_xxx.png)

*Source : Organisation (Année).*
```

### Tableaux

Les tableaux doivent porter un titre qui apparaît **immédiatement avant le tableau**, sous la forme :

```html
<p class="table-caption"><strong>Tableau X.Y</strong> — Titre du tableau</p>
```

**Convention de numérotation :** `Tableau <chapitre>.<numéro-séquentiel>` (ex. : Tableau 4.3 = troisième tableau du chapitre 4).

**Règles :**
- Le titre doit être concis, précis et indiquer l'objet du tableau (institutions, indicateurs) et le périmètre temporel si applicable.
- Le `<p class="table-caption">` se place directement avant la première ligne `|` du tableau markdown, sans ligne vide entre les deux.
- Les `###` de section peuvent précéder le paragraphe d'introduction, mais la caption est toujours juste avant le tableau.
- Chaque tableau nommé doit être enregistré dans `07_tableaux/registre_tableaux.md`.

**Exemple complet :**

```markdown
### Bénéficiaires de pensions de vieillesse

La branche vieillesse couvre les travailleurs via la CNSS et la CNSSAP...

<p class="table-caption"><strong>Tableau 4.1</strong> — Bénéficiaires de pensions de vieillesse, CNSS et CNSSAP (2019–2025)</p>

| Institution | Prestation | 2019 | 2020 | … |
|---|---|---|---|---|
| CNSS | Pension de retraite | … | … | … |
```