# Scripts d'assemblage — Bulletin statistique de la protection sociale en RDC

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `assembler_markdown.py` | Assemble les fichiers Markdown du bulletin en deux versions de sortie |
| `convertir_pdf_en_texte.py` | Convertit tous les PDF des dossiers de références et de données en fichiers `.txt` lisibles par les agents |
| `extraire_ess.py` | Charge les fichiers ESS dans `06_donnees/protection_sociale_rdc.db` |
| `rafraichir_ess.py` | **Mise à jour complète** : purge les données ESS en base, réimporte le fichier modifié, régénère le dashboard — en une seule commande |
| `integrer_dashboard_bulletin.py` | Met à jour automatiquement le tableau 5.2 du chapitre 5 à partir des données et réglages du dashboard |
| `generer_annexe_b_visuels.py` | Génère les graphiques et tableaux statistiques de l'annexe B par institution, sans navigateur (kaleido) |
| `generer_annexe_c_visuels.py` | Génère les tableaux, graphiques et détail des numérateurs de l'annexe C par indicateur ODD 1.3.1, sans navigateur (kaleido) |
| `serveur_preview.py` | Serveur de prévisualisation — surveille les fichiers, relance l'assembleur et rafraîchit le navigateur automatiquement |
| `exporter.py` | Génère des versions exportables du bulletin (HTML, Word, PDF) pour relecture hors ligne |
| `preview.css` | Feuille de style du rendu navigateur — modifier librement sans toucher aux `.md` |
| `export_relecture.css` | Feuille de style des exports HTML de relecture (optimisée lecture + impression A4) |

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

## rafraichir_ess.py

### Rôle

Enchaîne en une seule commande les opérations nécessaires après modification d'un fichier ESS directement dans `06_sources/ESS/` :

1. **Purge** des données existantes en base pour la cible (via `extraire_ess.py --delete --force`)
2. **Réimport** du fichier mis à jour (via `extraire_ess.py`)
3. **Mise à jour chapitre 4** : remplissage automatique des marqueurs `[ESS YYYY]` dans les tableaux de `03_chapitres/chapitre_4/` (via `remplir_ch4.py`)
4. **Régénération** du tableau de bord (via `visualiser_regimes.py`)
5. **Intégration bulletin** : injection des valeurs ODD 1.3.1 dans `03_chapitres/chapitre_5/00_plan_chapitre_5.md` (via `integrer_dashboard_bulletin.py`)
6. **Visuels annexe B** : régénération des graphiques et tableaux statistiques par institution dans `04_annexes/annexe_B_fiches_institutionnelles.md` (via `generer_annexe_b_visuels.py`)

> Le serveur de prévisualisation (`serveur_preview.py`) ne surveille pas les fichiers `.xlsx` ni la base SQLite. Ce script comble ce chaînon manquant.

### Usage

```bash
# Cas standard — mettre à jour l'ESS CNSS 2022
py 09_scripts/rafraichir_ess.py --institution CNSS --annee 2022

# Simulation sans modification
py 09_scripts/rafraichir_ess.py --institution CNSSAP --annee 2021 --dry-run

# Sans régénération du dashboard (plus rapide)
py 09_scripts/rafraichir_ess.py --institution CNSS --annee 2022 --no-dashboard

# Ciblage par source_id (si institution/annee insuffisants)
py 09_scripts/rafraichir_ess.py --source-id 5 --annee 2022
```

### Après exécution

Si le serveur de prévisualisation est actif (`http://localhost:8765`), recharger manuellement le tableau de bord dans le navigateur (**F5**). Le dashboard HTML aura été régénéré.

### Options

| Option | Description |
|---|---|
| `--institution` | Institution cible (CNSS, CNSSAP, RDC…) |
| `--annee` | Année ESS cible |
| `--source-id` | Identifiant source_id précis |
| `--dry-run` | Simule toutes les étapes sans modifier la base ni le dashboard |
| `--no-dashboard` | Saute la régénération du tableau de bord |
| `--verbose` | Détail ligne par ligne lors du réimport |

---

## integrer_dashboard_bulletin.py

### Rôle

Met à jour automatiquement les valeurs du **Tableau 5.2** (chapitre 5) en s'appuyant sur :

- les données ESS présentes en base ;
- les décisions d'inclusion/exclusion enregistrées dans `10_output/dashboard_settings.json` ;
- les dénominateurs calculés/validés dans ce même fichier.

### Usage

```bash
py 09_scripts/integrer_dashboard_bulletin.py
```

### Résultat

- Met à jour les lignes chiffrées de l'ODD 1.3.1 dans `03_chapitres/chapitre_5/00_plan_chapitre_5.md`.
- Conserve `[N/D]` lorsque le numérateur ou le dénominateur est indisponible.

---

## generer_annexe_b_visuels.py

### Rôle

Génère les visuels statistiques statiques de l'**annexe B** (fiches institutionnelles) directement à partir des données ESS en base — **sans navigateur, sans simulation de clics**.

Pour chaque institution présente en base, régénère automatiquement, **dans cet ordre**, une sous-section « ### Régimes gérés » → « ### Aperçu graphique » → « ### Répartition par sexe » → « ### Données détaillées » de la section « ## Données de couverture » :

1. Un tableau Markdown natif **« Régimes gérés »** (description structurée par régime : type de financement, caractère, gestion, administrateur, fonctions couvertes, années ESS disponibles).
2. **6 graphiques** (cotisants, bénéficiaires, dépenses, dépense moyenne par bénéficiaire, recettes, contribution moyenne) exportés en PNG via **les mêmes fonctions Plotly** que le tableau de bord interactif (`build_fig_institution_*` dans `visualiser_regimes.py`). Aucune logique visuelle n'est dupliquée : un changement de style/type de graphique dans le dashboard se répercute automatiquement dans l'annexe.
3. Des **camemberts « Répartition par sexe »** (cotisants et bénéficiaires cumulés, tous régimes) — un **unique visuel compact en grille** par institution (3 années par ligne, 2 camemberts par année), exporté en un seul PNG via Plotly/kaleido. Les catégories à valeur nulle (ex. sexe non renseigné dans l'ESS) sont exclues du graphique pour éviter des étiquettes « 0 % » parasites. La légende des couleurs et la convention gauche/droite (cotisants/bénéficiaires) sont affichées une seule fois, en HTML, au-dessus de l'image — pas de titre ni de légende répétés par année, pour limiter l'espace vertical.
4. Un tableau Markdown natif **« Données détaillées »** (une ligne par régime et par année : cotisants, bénéficiaires, dépenses, recettes, dépense moyenne/bénéficiaire, recette moyenne/cotisant) — réutilise `build_institution_detail_table`, la même source de données que le tableau « Données détaillées » du dashboard interactif.

Par défaut, **tous les régimes** de chaque institution sont inclus (pas de filtre/sélection).

Les tableaux (description, données détaillées) sont volontairement du Markdown natif — et non des images — pour rester nets et exploitables lors des exports Word/PDF (texte sélectionnable, pas de flou à l'impression). Les graphiques de séries temporelles et les camemberts de répartition par sexe sont exportés en image.

### Couverture 2019-2025 et placeholders [N/D]

Le bulletin couvre les années **2019 à 2025**. Toute année de cette plage sans donnée ESS doit rester visible — jamais silencieusement omise, et jamais confondue avec une valeur nulle réelle (`0`). Le script applique cette règle à chaque élément auto-généré :

- **Données détaillées** : pour chaque régime connu (`regime_meta`), une ligne est générée pour chaque année 2019-2025 ; les combinaisons régime × année sans donnée ESS affichent `[N/D]` sur toutes les colonnes numériques. Les noms de régime sont alignés sur ceux du tableau « Régimes gérés » (source `regime_meta`), y compris pour les lignes réelles, afin d'éviter d'afficher un code brut (ex. `MESP_R1`) à un endroit et un nom lisible à un autre. Pour rester compact, les années **consécutives** sans aucune donnée sont fusionnées en une seule ligne « AAAA–AAAA » (ex. trois lignes 100 % `[N/D]` pour 2023, 2024 et 2025 deviennent une seule ligne « 2023–2025 ») plutôt que répétées une par une ; aucune information n'est perdue, seul le nombre de lignes entièrement vides est réduit — les années avec données réelles conservent chacune leur propre ligne.
- **Aperçu graphique** : l'axe des années est fixé sur toute la période 2019-2025 (étendue si des données réelles existent au-delà), afin qu'une période sans donnée apparaisse comme un espace vide sur la courbe plutôt que d'être masquée par le zoom automatique de Plotly. Si un graphique ne peut pas du tout être généré (donnée insuffisante), l'emplacement reste visible dans la grille avec un repère `[N/D]` au lieu de disparaître.
- **Répartition par sexe** : la grille de camemberts couvre systématiquement 2019-2025 (étendue aux années réelles hors plage) ; une année sans donnée de répartition par sexe affiche un camembert gris uniforme « Non disponible » plutôt que d'être omise.

### Emplacement dans la fiche institutionnelle

Chaque fiche institutionnelle standard (B.1, B.2, B.4, B.5, B.6) suit l'ordre : **Mission et branches couvertes → Cadre juridique et institutionnel → Données de couverture → Évolutions et réformes en cours**. Le contenu auto-généré (`### Régimes gérés`, `### Aperçu graphique`, `### Répartition par sexe`, `### Données détaillées`) constitue les sous-sections de « ## Données de couverture », après le tableau d'indicateurs rédigé à la main. B.3 (FNPSS, pas de données ESS) suit le même ordre de titres sans contenu auto-généré. B.7 (régimes spéciaux non contributifs) a une structure différente (Régimes identifiés / Données disponibles / Perspective de collecte) et n'est pas concerné par cet ordre.

### Mécanisme d'injection

Le contenu généré est inséré dans `04_annexes/annexe_B_fiches_institutionnelles.md` entre des marqueurs dédiés par institution :

```html
<!-- AUTO_GENERE:CNSS:DEBUT -->
...
<!-- AUTO_GENERE:CNSS:FIN -->
```

Seul le contenu entre ces marqueurs est remplacé à chaque exécution. Le texte rédigé manuellement autour (cadre juridique, évolutions/réformes, etc.) n'est jamais modifié.

### Prérequis

```bash
pip install kaleido
```

### Usage

```bash
py 09_scripts/generer_annexe_b_visuels.py
```

### Résultat

- Images PNG écrites dans `04_annexes/illustrations/annexe_B_<INSTITUTION>_<graphique>.png` (graphiques temporels) et `annexe_B_<INSTITUTION>_sexe.png` (grille compacte répartition par sexe, toutes années).
- Tableaux Markdown regénérés dans `04_annexes/annexe_B_fiches_institutionnelles.md`.
- Les institutions sans marqueur `AUTO_GENERE` correspondant (ex. `MEPST`, absent de l'annexe B en tant que fiche dédiée) sont ignorées et signalées en fin d'exécution.

---

## generer_annexe_c_visuels.py

### Rôle

Génère les visuels et tableaux statistiques statiques de l'**annexe C** (détail des indicateurs de couverture) directement à partir des données ESS en base et des décisions/dénominateurs du tableau de bord — **sans navigateur**. Reprend la structure de l'onglet « Indicateurs » du tableau de bord interactif, pour chacun des 9 indicateurs ODD 1.3.1/BIT (même liste que le sélecteur `ODD_INDICATORS`) :

1. Un **encadré méthodologique** (définition, numérateur, dénominateur, formule) — copie fidèle des textes `ODD_METHODOLOGY_SPECS` du tableau de bord (`visualiser_regimes.py`), pour ne jamais faire diverger les deux supports.
2. Un **tableau de synthèse unique 2019-2025** (inspiré du Tableau 14 du premier bulletin RDC), à colonnes années partagées :
   - la ligne **Indicateur de couverture (%)** ;
   - la ligne **Numérateur (nombre de personnes)**, immédiatement suivie de ses lignes de détail en italique, groupées par régime pour rester compactes et lisibles (`_build_breakdown_rows`) : un en-tête **« Dont [régime] (SIGLE, cotisants) »** par régime contributeur — l'institution étant désignée par son sigle brut (ex. `CNSS`, `CNSSAP`, `Trésor` pour `TRESOR` — cf. `ACRONYME_OVERRIDES`) plutôt que par sa dénomination complète, celle-ci restant disponible dans la Liste des sigles et acronymes — suivi de ses prestations en sous-lignes indentées **« ↳ [prestation] (bénéf.) »** qui ne répètent ni l'institution ni le régime déjà portés par la ligne d'en-tête juste au-dessus. Réutilise la logique d'inclusion/exclusion de `integrer_dashboard_bulletin.py` (`compute_numerator`, `get_denominator_value`) et sa nouvelle fonction `compute_numerator_breakdown` (détail ligne par ligne au lieu d'un simple total) ;
   - la ligne **Dénominateur (population de référence)**, dont le détail de construction par année (source retenue, cf. panneau « Construction des dénominateurs » du tableau de bord) est renvoyé en **note de bas de page** (`<span class="footnote">…</span>`, la même convention que celle utilisée pour les sources du bulletin — voir `09_scripts/footnotes.lua`) plutôt qu'affiché en clair dans le corps du tableau. Cette note est **factorisée par plage d'années consécutives partageant la même source** (`build_denominator_footnote`) — ex. « 2019–2024 : Base locale ONU WPP 2024 — population 0+ ; 2026 : Saisie manuelle » — plutôt que répétée une fois par année. Dans la prévisualisation HTML, ce marqueur s'affiche en petit texte italique discret (voir règle `.footnote` dans `preview.css`) ; à l'export Word, il devient une vraie note de bas de page.
3. **Deux graphiques PNG** (indicateur en %, numérateur en nombre de personnes) exportés via Plotly/kaleido, dans le même style que le tableau de bord et l'annexe B. **Aucun graphique pour le dénominateur** (non demandé).

Les sous-indicateurs 2.6 (chômage) et 2.8 (vulnérables) ne disposent d'aucune règle de calcul opérationnelle dans la base actuelle : seul l'encadré méthodologique est généré pour eux, avec une note explicite d'indisponibilité — jamais de valeur inventée.

### Mécanisme d'injection

Le contenu généré est inséré dans `04_annexes/annexe_C_detail_indicateurs.md` entre des marqueurs dédiés par indicateur :

```html
<!-- AUTO_GENERE:global_131:DEBUT -->
...
<!-- AUTO_GENERE:global_131:FIN -->
```

Seul le contenu entre ces marqueurs est remplacé à chaque exécution. Le texte d'introduction et la NOTE_INTERNE ne sont jamais modifiés.

### Prérequis

```bash
pip install kaleido
```

### Usage

```bash
py 09_scripts/generer_annexe_c_visuels.py
```

### Résultat

- Images PNG écrites dans `04_annexes/illustrations/annexe_C_<indicateur>_indicateur.png` et `annexe_C_<indicateur>_numerateur.png`.
- Tableaux et encadrés Markdown regénérés dans `04_annexes/annexe_C_detail_indicateurs.md`.

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

Boutons disponibles dans la barre d'en-tête :
- **📊 Tableau de bord** — ouvre le tableau de bord interactif des régimes (ESS)
- **📤 Exporter HTML** — génère un fichier HTML autonome pour relecture hors ligne et l'ouvre dans un nouvel onglet
- **🖨️ Export PDF** — ouvre la boîte d'impression du navigateur pour enregistrer le rendu courant en PDF

### Personnaliser le visuel

Modifier `09_scripts/preview.css` : polices, couleurs, taille des textes, style des tableaux, largeur de la sidebar. Ces changements n'affectent pas les `.md` ni le futur export Word.

---

## exporter.py

### Rôle

Génère des versions exportables du bulletin pour relecture et partage hors ligne. Produit les fichiers dans `10_output/` avec la date du jour dans le nom.

| Fichier produit | Contenu |
|---|---|
| `bulletin_relecture_YYYY-MM-DD.html` | Version relecture — HTML autonome, CSS intégrée, aucune dépendance serveur |
| `bulletin_notes_YYYY-MM-DD.html` | Version interne — idem avec les blocs `<!-- NOTE_INTERNE -->` visibles |
| `bulletin_relecture_YYYY-MM-DD.docx` | Version Word via pandoc (si installé) |
| `bulletin_relecture_YYYY-MM-DD.pdf` | Version PDF via weasyprint ou pandoc (si disponibles) |

### Prérequis

```bash
pip install markdown   # déjà requis par le serveur de prévisualisation

# Pour l'export Word :
# Installer pandoc : https://pandoc.org/installing.html

# Pour l'export PDF (option 1 — recommandé) :
pip install weasyprint

# Pour l'export PDF (option 2 — via pandoc) :
# Installer pandoc + une distribution LaTeX (MiKTeX ou TeX Live)
```

### Usages

```bash
python 09_scripts/exporter.py             # HTML relecture (défaut)
python 09_scripts/exporter.py --all       # tous les formats
python 09_scripts/exporter.py --word      # Word uniquement
python 09_scripts/exporter.py --pdf       # PDF uniquement
python 09_scripts/exporter.py --notes     # HTML version interne (avec notes)
python 09_scripts/exporter.py --open      # générer et ouvrir automatiquement
```

Le fichier HTML produit est **autonome** : CSS intégrée, aucune connexion réseau requise, partageable par email, clé USB ou OneDrive. Il contient la table des matières, les indicateurs de statut, un bouton d'impression, et les règles CSS A4.

### Depuis le serveur de prévisualisation

Le bouton **📤 Exporter HTML** dans la barre d'en-tête (`http://localhost:8765`) déclenche l'export automatiquement et ouvre le résultat dans un nouvel onglet.

---

## preview.css

Feuille de style indépendante pour la prévisualisation navigateur. Contient des variables CSS en haut du fichier (`--couleur-principale`, `--police-corps`, etc.) pour faciliter les ajustements rapides.

---

## export_relecture.css

Feuille de style des exports HTML de relecture. Optimisée pour la lecture sur écran (mise en page linéaire, TOC latérale) et l'impression A4 (marges, sauts de page, masquage des éléments non pertinents). Ne pas utiliser dans le serveur de prévisualisation.

---

## Notes de gestion

- Ne pas modifier les fichiers sources après un assemblage sans relancer le script.
- La version publication ne doit jamais servir de source pour la rédaction.
- Les sorties dans `10_output/` sont régénérables à tout moment.
