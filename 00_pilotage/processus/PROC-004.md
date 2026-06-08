# PROC-004 — Vérification terminologique

<!-- NOTE_INTERNE
Objet du fichier :
Décrire le processus à suivre lorsqu'un terme, une définition ou une formulation doit être
vérifiée, clarifiée ou harmonisée avec les conventions du bulletin.

Statut : actif
Version : 1.0
Date : 2026-06-08
-->

---

## Déclencheur

Ce processus est activé lorsque :
- L'utilisateur demande : « Quel terme utiliser pour… ? », « Est-ce que "bénéficiaire" est correct ici ? »
- Un terme employé dans une section semble ambigu ou non conforme.
- Une nouvelle notion doit être introduite dans le bulletin.
- Une contradiction terminologique est détectée entre deux sections.

---

## Étape 1 — Identification du terme à vérifier

Préciser :
- Le terme en question.
- Le contexte d'usage (institution, régime, type de données, phrase concernée).
- La section où il apparaît ou doit apparaître.

---

## Étape 2 — Consultation des références internes

Consulter **dans cet ordre** :

1. **`05_references/conventions_terminologiques.md`** — Choix de vocabulaire stables et actés.
2. **`05_references/glossaire.md`** — Définitions de travail utilisées dans le bulletin.
3. **`00_pilotage/decisions_methodologiques.md`** — Décisions actées (notamment DM-004).

Si le terme est trouvé et clairement défini → appliquer la convention et passer à l'Étape 4.  
Si le terme n'est pas trouvé ou est ambigu → passer à l'Étape 3.

---

## Étape 3 — Consultation des références normatives externes

Si les références internes ne permettent pas de trancher, consulter :

1. **Glossaire OIT/BIT** — Documents de référence dans `11_references_externes/references_oit_bit/`
2. **SSPTW (Social Security Programs Throughout the World)** — définitions des branches
3. **Recommandation R.202 de l'OIT** — langage sur le socle de protection sociale
4. **Autres bulletins** — `11_references_externes/autres_bulletins/` (usage comparatif uniquement)

---

## Étape 4 — Présentation de la recommandation terminologique

Présenter à l'utilisateur :

```
## Vérification terminologique — « [Terme] »

**Contexte :** [Phrase ou section concernée]

**Terme actuel :** [ce qui est écrit]
**Terme recommandé :** [ce qui devrait être écrit]

**Justification :**
- Source interne : [référence dans glossaire.md ou conventions_terminologiques.md]
- Source externe : [si applicable]

**Formulation suggérée :**
> [Phrase réécrite avec le terme correct]

**Action requise :** [Corriger dans la section X / Ajouter au glossaire / Décision à prendre]
```

---

## Étape 5 — Mise à jour des références (si nouveau terme)

Si le terme n'était pas encore dans les références internes et que l'utilisateur valide une définition :

- Ajouter le terme dans `05_references/glossaire.md`.
- Ajouter la convention dans `05_references/conventions_terminologiques.md` si applicable.
- Proposer une ligne pour `00_pilotage/journal_modifications.md`.

---

## Livrables attendus

- [ ] Terme vérifié dans les références internes et externes
- [ ] Recommandation présentée à l'utilisateur
- [ ] Correction appliquée dans la section concernée (après validation)
- [ ] Glossaire et/ou conventions mis à jour si nouveau terme
- [ ] Journal mis à jour si modification substantielle
