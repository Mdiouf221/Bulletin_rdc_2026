# PROC-005 — Mise à jour du registre des sources

<!-- NOTE_INTERNE
Objet du fichier :
Décrire le processus à suivre pour maintenir le registre des données à jour, que ce soit
après un dépôt de document, une recherche internet ou une intégration de source dans le bulletin.

Statut : actif
Version : 1.0
Date : 2026-06-08
-->

---

## Déclencheur

Ce processus est activé lorsque :
- Un nouveau document est déposé dans `06_sources/` (quel que soit le sous-dossier).
- Une source est citée dans le bulletin pour la première fois.
- L'utilisateur demande : « Mets à jour le registre », « Ajoute cette source au registre ».
- Un processus PROC-001 ou PROC-002 arrive à son Étape 5b.

---

## Étape 1 — Identification du document à enregistrer

Collecter les informations suivantes :

| Champ | Description |
|-------|-------------|
| **Nom du fichier** | Nom exact du fichier déposé dans `06_sources/` |
| **Sous-dossier** | `institutions/`, `officielles_web/` ou `sources_incertaines/` |
| **Source / Émetteur** | Organisation ou institution ayant produit le document |
| **Type** | Rapport, base de données, loi, décret, article, tableau, etc. |
| **Description courte** | Ce que le document contient (indicateurs, période, population…) |
| **Lien d'origine** | URL si disponible (source web) ou mention « transmission directe » |
| **Période couverte** | Année(s) ou plage temporelle des données |
| **Converti en .txt** | Oui / Non / À faire |
| **Statut** | Actif / À convertir / À vérifier |

---

## Étape 2 — Mise à jour de `registre_donnees.md`

Ouvrir `06_sources/registre_donnees.md` et ajouter la ligne dans le tableau du sous-dossier correspondant.

**Format pour `institutions/` :**
```
| [fichier] | [Institution] | [Type] | [Description] | [Période] | [Converti] | [Statut] |
```

**Format pour `officielles_web/` et `sources_incertaines/` :**
```
| [fichier] | [Source] | [Type] | [Description] | [Lien] | [Période] | [Converti] | [Statut] |
```

---

## Étape 3 — Vérification du nommage du fichier

S'assurer que le fichier respecte la convention de nommage :
```
[Organisation]_[Sujet]_[Année].[extension]
```
Exemples :
- `OIT_protection_sociale_RDC_2022.pdf` ✅
- `rapport final version 3 (2).pdf` ❌ → renommer

Si le fichier n'est pas correctement nommé, proposer un nom conforme à l'utilisateur.

---

## Étape 4 — Vérification de la conversion .txt

- Si le fichier est un PDF et n'a pas encore de version `.txt` :
  - Indiquer `Non` dans la colonne `Converti`.
  - Rappeler que la conversion se fait via `09_scripts/convertir_pdf_en_texte.py`.
  - Le fichier converti doit être déposé dans le sous-dossier `_texte/` correspondant.

---

## Étape 5 — Confirmation et journal

- Confirmer à l'utilisateur que le registre est mis à jour.
- Proposer une ligne pour `00_pilotage/journal_modifications.md` si la source est nouvelle :

```
| [Date] | PROC-005 | Enregistrement de [fichier] dans registre_donnees.md ([sous-dossier]) |
```

---

## Livrables attendus

- [ ] Informations du document collectées
- [ ] Ligne ajoutée dans le bon tableau de `registre_donnees.md`
- [ ] Nommage du fichier vérifié (et renommage proposé si nécessaire)
- [ ] Statut de conversion `.txt` indiqué
- [ ] Journal mis à jour
