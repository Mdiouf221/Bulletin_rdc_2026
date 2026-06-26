# Collecte de données — Demandes institutionnelles

Ce dossier contient les scripts et outils permettant de générer les demandes de données
et les canevas de collecte destinés aux institutions partenaires du bulletin.

## Structure

```
collecte_donnees/
  package.json          ← dépendances Node.js (docx, exceljs)
  node_modules/         ← packages installés
  INS/
    generer_html_INS.mjs      ← Étape 1 : prévisualisation HTML
    generer_demande_INS.mjs   ← Étape 2 : lettre Word
    generer_canevas_INS.mjs   ← Étape 3 : canevas Excel
  MINAS/
    generer_html_MINAS.mjs    ← Étape 1 : prévisualisation HTML
    generer_demande_MINAS.mjs ← Étape 2 : lettre Word
    generer_canevas_MINAS.mjs ← Étape 3 : canevas Excel
  CNSS/                 ← à créer
  CNSSAP/               ← à créer
  FSS/                  ← à créer
```

## Workflow obligatoire en 3 étapes

**Règle générale : toujours générer et réviser le HTML avant de produire le Word et l'Excel.**

```
Étape 1 — Prévisualisation HTML   →  réviser dans le navigateur
Étape 2 — Génération Word (.docx) →  après validation du contenu
Étape 3 — Génération Excel (.xlsx) → après validation du contenu
```

### Détail des scripts par institution

| Script | Étape | Description |
|--------|-------|-------------|
| `generer_html_XXX.mjs`     | **Étape 1** | Génère `preview_XXX.html` — à ouvrir dans un navigateur pour révision |
| `generer_demande_XXX.mjs`  | Étape 2 | Génère la lettre de demande au format `.docx` (Word) |
| `generer_canevas_XXX.mjs`  | Étape 3 | Génère le canevas de saisie au format `.xlsx` (Excel) |

Les fichiers produits sont enregistrés dans `10_output/collecte_donnees/XXX/`.

### Commandes (exemple INS)

```bash
cd 09_scripts/collecte_donnees

# Étape 1 : prévisualisation — ouvrir preview_INS.html dans le navigateur et corriger si nécessaire
node INS/generer_html_INS.mjs

# Étape 2 : Word — seulement après validation du HTML
node INS/generer_demande_INS.mjs

# Étape 3 : Excel — seulement après validation du HTML
node INS/generer_canevas_INS.mjs
```

## Institutions à couvrir

| Institution | Données principales demandées | Statut |
|-------------|-------------------------------|--------|
| **INS** | Dénominateurs ODD 1.3.1, seuils de pauvreté, marché du travail, démographie | ✅ Fait |
| **MINAS** | Cartographie des programmes, bénéficiaires, finances, couverture géographique, coordination | ✅ Fait |
| **CNSS** | Cotisants, pensionnés, bénéficiaires par branche, finances | ⏳ À faire |
| **CNSSAP** | Cotisants, pensionnés, agents publics couverts | ⏳ À faire |
| **FSS** | Affiliés, bénéficiaires Afia Bora / Kobota Ofele | ⏳ À faire |
| **MESP** | Affiliés, cotisants, bénéficiaires santé enseignants | ⏳ À faire |

## Dépendances

- **docx** (v9+) — génération des fichiers Word `.docx`
- **exceljs** (v4+) — génération des fichiers Excel `.xlsx`

Installer : `npm install` (depuis le dossier `collecte_donnees/`)
