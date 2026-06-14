# Scripts d'assemblage — Bulletin statistique de la protection sociale en RDC

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `assembler_markdown.py` | Assemble les fichiers Markdown du bulletin en deux versions de sortie |
| `convertir_pdf_en_texte.py` | Convertit tous les PDF des dossiers de références et de données en fichiers `.txt` lisibles par les agents |
| `extraire_ess.py` | Charge les fichiers ESS dans `06_donnees/protection_sociale_rdc.db` |
| `serveur_preview.py` | Serveur de prévisualisation — surveille les fichiers, relance l'assembleur et rafraîchit le navigateur automatiquement |
| `preview.css` | Feuille de style du rendu navigateur — modifier librement sans toucher aux `.md` |

---

## assembler_markdown.py

### Rôle

Ce script lit le fichier `build_config.yml` à la racine du workspace et assemble
tous les fichiers Markdown listés dans `sections.files` dans l'ordre défini.

Il produit deux fichiers dans le dossier `10_output/` :

| Fichier de sortie | Contenu |
|---|---|
| `bulletin_complet_travail.md` | Version de travail — les blocs `<!-- NOTE_INTERNE ... -->` sont **conservés** |
| `bulletin_complet_publication.md` | Version publication — les blocs `<!-- NOTE_INTERNE ... -->` sont **supprimés** |

Les fichiers sources ne sont jamais modifiés.

### Prérequis

Le script utilise la bibliothèque **PyYAML** pour lire `build_config.yml`.

Si elle n'est pas installée, exécuter dans le terminal :

```bash
pip install pyyaml
```

### Lancer le script depuis le terminal VS Code

Ouvrir un terminal dans VS Code (`Ctrl+ù` ou menu **Terminal > Nouveau terminal**),
puis exécuter depuis la racine du workspace :

```bash
python 09_scripts/assembler_markdown.py
```

### Comportement en cas de fichier manquant

Si un fichier listé dans `build_config.yml` est absent du workspace, le script :
- affiche un avertissement dans la console (sans s'arrêter) ;
- insère un commentaire de substitution dans les fichiers de sortie ;
- liste en fin d'exécution tous les fichiers manquants.

### Exemple de sortie console

```
[OK] Version travail écrite : 10_output/bulletin_complet_travail.md
[OK] Version publication écrite : 10_output/bulletin_complet_publication.md

[BILAN] 2 fichier(s) manquant(s) :
        - 03_chapitres/chapitre_2/...
        - 03_chapitres/chapitre_3/...
```

---

## convertir_pdf_en_texte.py

### Rôle

Convertit tous les fichiers PDF présents dans les dossiers de références externes et de données en fichiers `.txt` lisibles par les agents. Les fichiers déjà convertis sont ignorés (pas de reconversion inutile).

### Dossiers traités

| Dossier | Type |
|---|---|
| `06_sources/bulletins_rdc/` | Référence directe |
| `06_sources/bulletins_comparaison/` | Référence de style |
| `06_sources/references_oit_bit/` | Référence normative |
| `06_sources/institutions/` | Source primaire |
| `06_sources/officielles_web/` | Source secondaire officielle |
| `06_sources/sources_incertaines/` | Source à traiter avec prudence |

Pour chaque PDF, le fichier `.txt` est créé dans le sous-dossier `_texte/` au même niveau.

### Prérequis

```bash
pip install pdfplumber
```

### Lancer le script

```bash
python 09_scripts/convertir_pdf_en_texte.py
```

### Exemple de sortie console

```
[institutions/] — 3 PDF(s)
  [OK] CNSS_rapport_annuel_2023.pdf → 06_sources/institutions/_texte/...
  [DÉJÀ CONVERTI] ...

[BILAN] 5 converti(s), 0 erreur(s)
```

---

## extraire_ess.py

### Rôle

Charge les fichiers ESS dans la base SQLite `06_donnees/protection_sociale_rdc.db` via le schéma partagé `db_schema.py`. En mode normal, le script balaie automatiquement les fichiers présents dans `06_sources/ESS/`. Le dossier de réception unique `06_sources/_entrants/` reste disponible pour un flux d'arrivée progressif.

### Mode courant

```bash
python 09_scripts/extraire_ess.py
```

Le script scanne les sous-dossiers `ESS_*` sous `06_sources/ESS/`, déduit l'institution et l'année, puis ignore les doublons évidents (copies, variantes non canoniques) lorsqu'un autre fichier plus propre existe déjà pour le même couple institution/année.

### Mode import progressif

```bash
python 09_scripts/extraire_ess.py --inbox
```

Déposer un fichier ESS dans `06_sources/_entrants/`, puis lancer ce mode. Le script détecte l'institution (nom + contenu ESS), normalise le nom, enregistre la source en base, crée le sous-dossier `06_sources/ESS/ESS_<INSTITUTION>/` s'il n'existe pas, puis y déplace le fichier.

### Options utiles

```bash
python 09_scripts/extraire_ess.py --inbox --dry-run
python 09_scripts/extraire_ess.py --institution CNSS --annee 2022
python 09_scripts/extraire_ess.py --delete --institution CNSS --annee 2022 --dry-run
python 09_scripts/extraire_ess.py --delete --source-id 42 --force
python 09_scripts/validate_ess.py --annee 2022
```

---

## serveur_preview.py

### Rôle

Serveur de prévisualisation du bulletin dans le navigateur. Surveille en temps réel tous les fichiers `.md` et `.yml` du workspace. Dès qu'une modification est détectée :

1. L'assembleur est relancé automatiquement.
2. La page HTML est régénérée (avec table des matières cliquable).
3. Le navigateur est rafraîchi sans aucune action manuelle.

Le visuel (polices, couleurs, marges, tableaux) est contrôlé par `preview.css` — **sans jamais modifier les fichiers source `.md`**.

### Prérequis

```bash
pip install markdown watchdog
```

### Lancer le serveur

```bash
python 09_scripts/serveur_preview.py
```

Le navigateur s'ouvre automatiquement sur `http://localhost:8765`.
Arrêt : `Ctrl+C` dans le terminal.
Le bouton **🖨️ Export PDF** (en haut à droite) ouvre la boîte d'impression du navigateur pour enregistrer le rendu courant en PDF.

### Personnaliser le visuel

Modifier `09_scripts/preview.css` : polices, couleurs, taille des textes, style des tableaux, largeur de la sidebar. Ces changements n'affectent pas les `.md` ni le futur export Word.

---

## preview.css

Feuille de style indépendante pour la prévisualisation navigateur. Contient des variables CSS en haut du fichier (`--couleur-principale`, `--police-corps`, etc.) pour faciliter les ajustements rapides.

---

## Notes de gestion

- Ne pas modifier les fichiers sources après un assemblage sans relancer le script.
- La version publication ne doit jamais servir de source pour la rédaction.
- Les sorties dans `10_output/` sont régénérables à tout moment.
