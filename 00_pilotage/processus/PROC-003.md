# PROC-003 — Révision et validation d'une section

<!-- NOTE_INTERNE
Objet du fichier :
Décrire le processus à suivre pour réviser une section rédigée du bulletin afin de la préparer
à la validation finale (statut "révisé" puis "validé").

Statut : actif
Version : 1.0
Date : 2026-06-08
-->

---

## Déclencheur

Ce processus est activé lorsque :
- Une section a le statut `rédigé` et doit passer à `révisé` ou `validé`.
- L'utilisateur dit : « Révise cette section », « Prépare cette section pour validation »,
  « Vérifie la cohérence de… »

---

## Étape 1 — Lecture critique du texte rédigé

Lire le `## Texte rédigé` et contrôler chaque point de la grille suivante :

### Grille de révision

**Fond (données et rigueur)**
- [ ] Toutes les données citées ont une source explicite.
- [ ] Aucune donnée inventée ou sans référence.
- [ ] La distinction institution / régime / programme / branche / prestation est respectée (DM-004).
- [ ] La couverture effective est distinguée de la couverture légale (DM-001).
- [ ] Les données incertaines sont signalées avec réserve.
- [ ] Aucune donnée ne contredit une autre section du bulletin.

**Terminologie**
- [ ] Les termes sont conformes au glossaire (`05_references/glossaire.md`).
- [ ] Les conventions terminologiques stables sont respectées (`05_references/conventions_terminologiques.md`).
- [ ] Pas de confusion entre affilié / cotisant actif / bénéficiaire / personne couverte.

**Style et langue**
- [ ] Français institutionnel, style analytique et prudent.
- [ ] Pas de formulations journalistiques ou promotionnelles.
- [ ] Phrases claires, sans ambiguïté statistique.
- [ ] Pas de répétitions avec d'autres sections connues.

**Structure**
- [ ] Le titre correspond au contenu.
- [ ] La numérotation des sections est respectée.
- [ ] La NOTE_INTERNE n'a pas été modifiée (DM-002).
- [ ] Les notes de bas de page sont bien formées.

---

## Étape 2 — Rapport de révision

Produire un rapport synthétique des observations :

```
## Rapport de révision — [Titre de la section]

**Statut actuel :** rédigé
**Révisé le :** [Date]

### Points conformes
- [Liste des points vérifiés et conformes]

### Points à corriger
| # | Nature | Localisation | Correction suggérée |
|---|--------|-------------|---------------------|
| 1 | Donnée sans source | §2, ligne 3 | Ajouter (CNSS, 2022) |
| 2 | Terme incorrect | §3 | Remplacer "bénéficiaire" par "affilié" |

### Points à confirmer par l'utilisateur
- [Éléments nécessitant une décision ou vérification externe]
```

---

## Étape 3 — Corrections (après validation du rapport)

Attendre que l'utilisateur confirme les corrections à apporter, puis :
- Effectuer les corrections dans `## Texte rédigé` uniquement.
- Ne pas modifier la NOTE_INTERNE.
- Mettre le statut à `révisé` dans la NOTE_INTERNE.

---

## Étape 4 — Validation finale

La validation (`validé`) ne peut être accordée que par l'utilisateur explicitement.
L'agent peut **proposer** le passage à `validé` mais ne peut pas le décider seul.

Une fois la validation accordée :
- Mettre le statut à `validé` dans la NOTE_INTERNE.
- Proposer une ligne pour `00_pilotage/journal_modifications.md`.

---

## Livrables attendus

- [ ] Grille de révision complétée
- [ ] Rapport de révision produit
- [ ] Corrections effectuées après validation utilisateur
- [ ] Statut mis à jour (`révisé` ou `validé`)
- [ ] Journal mis à jour
