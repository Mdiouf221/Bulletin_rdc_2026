# PROC-002 — Intégration d'une donnée institutionnelle

<!-- NOTE_INTERNE
Objet du fichier :
Décrire le processus à suivre lorsqu'un document ou une donnée est transmis directement par une institution
nationale (CNSS, CNSSAP, FNPSS, SESOPA, ministères, INS…) et doit être intégré dans le bulletin.

Statut : actif
Version : 1.0
Date : 2026-06-08
-->

---

## Déclencheur

Ce processus est activé lorsque :
- Un document est transmis directement par une institution nationale.
- L'utilisateur dit : « J'ai reçu des données de la CNSS / du ministère / de l'INS… »
- Un fichier est déposé dans `06_sources/institutions/`.

---

## Étape 1 — Réception et qualification du document

Vérifier les éléments suivants avant tout traitement :

| Élément | Question |
|---------|----------|
| **Institution émettrice** | Quelle institution a transmis le document ? |
| **Type de document** | Rapport annuel ? Tableau statistique ? Décret ? Note interne ? |
| **Période couverte** | Quelle année ou période les données couvrent-elles ? |
| **Statut du document** | Officiel publié ? Document de travail ? Transmission informelle ? |
| **Données concernées** | Quels indicateurs, prestations, populations ou régimes sont couverts ? |

Si des éléments manquent, les demander à l'utilisateur.

---

## Étape 2 — Dépôt et archivage

1. Déposer le fichier original dans `06_sources/institutions/`.
2. Nommer le fichier selon la convention : `[Institution]_[Type]_[Année].[extension]`  
   Exemple : `CNSS_rapport_annuel_2022.pdf`
3. Si le fichier est un PDF : noter qu'une conversion `.txt` est nécessaire via `09_scripts/convertir_pdf_en_texte.py` pour le rendre lisible par les agents.
4. Mettre à jour `06_sources/registre_donnees.md` — tableau `institutions/` :

```
| CNSS_rapport_annuel_2022.pdf | CNSS | Rapport annuel | Effectifs affiliés, cotisations, prestations 2022 | — | Non | À convertir |
```

---

## Étape 3 — Vérification de cohérence

Avant intégration dans le bulletin, vérifier :

- [ ] Les données sont-elles cohérentes avec celles du premier bulletin (continuité temporelle) ?
- [ ] Y a-t-il des contradictions avec des données déjà intégrées dans une autre section ?
- [ ] Les définitions utilisées par l'institution correspondent-elles aux conventions du bulletin (DM-004) ?
- [ ] Le document distingue-t-il bien affiliés / cotisants actifs / bénéficiaires / prestations servies ?

Si des incohérences sont détectées : les signaler à l'utilisateur et attendre ses instructions.

---

## Étape 4 — Présentation synthétique à l'utilisateur

Présenter un résumé structuré des données disponibles dans le document :

```
## Données disponibles — [Institution] [Année]

**Source :** [Nom complet de l'institution], [Titre du document], [Année]
**Niveau de fiabilité :** Source primaire (transmission directe)

| Indicateur | Valeur | Unité | Page / Référence |
|------------|--------|-------|-----------------|
| Affiliés actifs | X XXX XXX | personnes | p. 12 |
| Cotisants actifs | X XXX XXX | personnes | p. 15 |
| Prestations versées | XXX XXX | USD | p. 22 |

**Observations :** [Signaler toute limite, lacune ou incohérence détectée]
```

---

## Étape 5 — Intégration dans le bulletin (après validation)

Attendre la validation de l'utilisateur, puis :

### 5a — Renseigner la section concernée
- Insérer les données dans le `## Texte rédigé` ou dans la NOTE_INTERNE selon le statut.
- Format de citation : `(CNSS, 2022)` ou note de bas de page.

### 5b — Ajouter la note de bas de page
```
[^X]: Caisse Nationale de Sécurité Sociale (CNSS). *Rapport annuel 2022*. Kinshasa : CNSS, 2023.
```

### 5c — Mettre à jour la bibliographie
Ajouter la référence dans `05_references/bibliographie.md` si ce fichier existe.

### 5d — Journaliser
Proposer une ligne pour `00_pilotage/journal_modifications.md`.

---

## Livrables attendus

- [ ] Fichier déposé dans `06_sources/institutions/`
- [ ] Registre mis à jour
- [ ] Incohérences vérifiées et signalées si besoin
- [ ] Résumé présenté et validé par l'utilisateur
- [ ] Section du bulletin mise à jour
- [ ] Note de bas de page ajoutée
- [ ] Bibliographie mise à jour
- [ ] Journal mis à jour
