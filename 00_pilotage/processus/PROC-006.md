# PROC-006 — Créer, déplacer ou restructurer un chapitre ou une annexe

<!-- NOTE_INTERNE
Objet du fichier :
Décrire le processus complet à suivre lorsqu'un nouveau chapitre ou une nouvelle annexe doit être créé(e), déplacé(e) ou renommé(e) dans le bulletin.

Ce processus garantit :
- qu'aucun fichier n'est perdu lors d'une restructuration ;
- que build_config.yml, architecture_rapport.md et journal_modifications.md sont toujours cohérents avec les fichiers réels ;
- que les nouveaux chapitres suivent les conventions de nommage et de structure établies.

Statut : actif
Version : 1.0
Date : 2026-06-08
-->

---

## Déclencheur

Ce processus est activé lorsque l'utilisateur formule une demande du type :
- « Crée un nouveau chapitre sur… »
- « Déplace le chapitre X dans… »
- « Renomme l'annexe X en… »
- « Restructure les chapitres selon ce nouveau plan »
- « Ajoute une section à… »

---

## Règle d'or : ne jamais perdre de fichier

> Avant toute opération de déplacement ou de renommage :
> 1. Vérifier que le fichier assemblé `10_output/bulletin_complet_travail.md` est à jour (relancer l'assembleur si nécessaire).
> 2. Ce fichier sert de sauvegarde de dernier recours pour tout contenu perdu.
> 3. Ne jamais utiliser `Move-Item` avec une destination sans barre oblique finale `\` si la destination peut être confondue avec un nom de fichier.

---

## Étape 1 — Inventaire avant modification

Avant toute action, établir la liste exacte des fichiers concernés :

```powershell
# Lister les fichiers du dossier concerné
Get-ChildItem "03_chapitres\<dossier>" -Recurse | Select-Object FullName, Length
```

Vérifier que chaque fichier listé est bien présent et non vide.

---

## Étape 2 — Mise à jour du fichier assemblé (sauvegarde)

Relancer l'assembleur pour s'assurer que la sauvegarde est fraîche :

```bash
py 09_scripts/assembler_markdown.py
```

---

## Cas A — Créer un nouveau chapitre

### A1 — Créer le dossier

```
03_chapitres/
  chapitre_X/          ← nouveau dossier
    00_plan_chapitreX.md
```

Convention de nommage du dossier : `chapitre_<numero>` (ex: `chapitre_3`)

### A2 — Créer le fichier de plan

Le fichier `00_plan_chapitreX.md` doit suivre ce modèle :

```markdown
# Plan du Chapitre X — [Titre]

<!-- NOTE_INTERNE
Objectif du chapitre :
[Description de l'objectif en 2-3 phrases]

Structure provisoire :
X.1 [Titre de la section]
X.2 [Titre de la section]
...

Logique rédactionnelle :
[Comment les sections s'enchaînent]

Statut : structure initiale
-->
```

### A3 — Créer les fichiers de sections

Pour chaque section, créer un fichier selon la convention :
`X_<num>_<titre_court>.md`

Exemple : `3_1_vieillesse_pensions.md`

Chaque fichier doit suivre le modèle standard des sections (voir `AGENTS.md`).

### A4 — Ajouter dans build_config.yml

Dans la section `sections:` du `build_config.yml`, ajouter le nouveau chapitre **en respectant l'ordre** :

```yaml
- id: "chapitre_X"
  title: "Chapitre X — [Titre]"
  files:
    - "03_chapitres/chapitre_X/X_1_[titre].md"
    - "03_chapitres/chapitre_X/X_2_[titre].md"
```

### A5 — Mettre à jour architecture_rapport.md

Ajouter la section correspondante dans `00_pilotage/architecture_rapport.md`.

---

## Cas B — Déplacer des fichiers existants vers un nouveau dossier

### B1 — Créer d'abord le dossier de destination

```powershell
New-Item -ItemType Directory -Path "03_chapitres\chapitre_X" -Force
```

### B2 — Copier les fichiers (pas Move-Item direct)

**Ne jamais utiliser `Move-Item $src $dest` sans barre oblique finale.**

Utiliser systématiquement :
```powershell
Copy-Item $src "$dest\" -Force     # copier d'abord
# Vérifier que la copie est réussie
if (Test-Path "$dest\$(Split-Path $src -Leaf)") {
    Remove-Item $src -Force        # puis supprimer la source
}
```

### B3 — Vérifier l'intégrité après déplacement

```powershell
# Comparer le nombre de lignes source/destination
$original = (Get-Content $src -Raw).Length
$copy = (Get-Content $destFull -Raw).Length
if ($original -eq $copy) { Write-Host "[OK]" } else { Write-Host "[ERREUR]" }
```

### B4 — Mettre à jour build_config.yml

Modifier les chemins dans `build_config.yml` pour pointer vers le nouveau dossier.

---

## Cas C — Renommer une annexe

### C1 — Renommer le fichier

```powershell
Rename-Item "04_annexes\ancien_nom.md" "nouveau_nom.md"
```

### C2 — Mettre à jour build_config.yml

Modifier l'entrée dans la section `annexes:`.

### C3 — Mettre à jour architecture_rapport.md

Modifier la liste des annexes.

---

## Étape finale — Journaliser et vérifier

### Journalisation

Proposer une ligne dans `00_pilotage/journal_modifications.md` :

```
| [Date] | PROC-006 | [Description : créé/déplacé/renommé quoi, vers où] |
```

### Vérification finale

Relancer l'assembleur et vérifier qu'il ne signale aucun fichier manquant :

```bash
py 09_scripts/assembler_markdown.py
```

---

## Livrables attendus à la fin du processus

- [ ] Dossier(s) créé(s) avec la convention de nommage correcte
- [ ] Fichier(s) de plan créé(s) avec NOTE_INTERNE complète
- [ ] Fichiers de sections créés ou déplacés sans perte
- [ ] `build_config.yml` mis à jour
- [ ] `00_pilotage/architecture_rapport.md` mis à jour
- [ ] Assembleur relancé sans erreur
- [ ] Ligne proposée pour `journal_modifications.md`

---

## Règles transversales

- Ne jamais utiliser `Move-Item $src $dest -Force` si `$dest` est un dossier sans `\` finale.
- Toujours vérifier l'existence du fichier source avant de le déplacer (`Test-Path`).
- En cas de doute sur l'intégrité d'un fichier déplacé, récupérer depuis `10_output/bulletin_complet_travail.md`.
- Un chapitre vide (`files: []`) dans `build_config.yml` est acceptable — ne pas mettre de faux fichiers.
