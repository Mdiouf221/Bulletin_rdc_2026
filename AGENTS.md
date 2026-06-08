# Instructions pour les agents — Deuxième Bulletin statistique de la protection sociale en RDC

## Rôle général

Aider à rédiger, structurer, réviser, harmoniser et assembler les fichiers Markdown du deuxième Bulletin statistique de la protection sociale en RDC.

## Langue et style

- Rédiger en français institutionnel.
- Employer un style clair, analytique, prudent et professionnel.
- Éviter les formulations trop journalistiques, militantes ou promotionnelles.
- Éviter les répétitions entre sections.
- Préserver la logique statistique et méthodologique du bulletin.

> Consulter `05_references/instructions_redactionnelles.md` pour les formulations recommandées, les formulations à éviter et les règles spécifiques au bulletin.

---

## Règles de fond

- Ne pas inventer de données.
- Ne pas créer de chiffres sans source.
- Signaler explicitement les informations manquantes ou incertaines.
- Distinguer clairement :
  - institution ;
  - régime ;
  - programme ;
  - branche ;
  - prestation ;
  - bénéficiaire ;
  - personne couverte ;
  - affilié ;
  - cotisant actif ;
  - prestation servie ;
  - dépense de prestation ;
  - dépense administrative.
- Ne pas réduire la protection sociale à l’assistance sociale.
- Garder une distinction claire entre couverture légale et couverture effective.
- Préserver l’ancrage BIT/OIT et la logique de couverture effective.> Consulter `05_references/glossaire.md` pour les définitions de travail.
> Consulter `05_references/conventions_terminologiques.md` pour les choix de vocabulaire stables.
> Consulter `00_pilotage/decisions_methodologiques.md` pour les décisions actées (DM-001 à DM-008) qui s'appliquent à toutes les sections.

---

## Règles d'édition des fichiers

- Ne jamais supprimer les blocs `<!-- NOTE_INTERNE ... -->` sauf demande explicite.
- Lorsque la demande porte sur la rédaction, modifier uniquement la section `## Texte rédigé`.
- Lorsque la demande porte sur la structure, modifier le plan ou les titres, mais préserver les notes internes.
- Conserver la numérotation des sections.
- Ne pas renommer les fichiers sans demande explicite.
- Lorsqu’une modification substantielle est faite, proposer une ligne à ajouter dans `00_pilotage/journal_modifications.md`.---

## Processus opérationnels

Un dossier `00_pilotage/processus/` contient les processus opérationnels standardisés à suivre pour les opérations récurrentes du projet.

> Consulter `00_pilotage/processus/index.md` pour la liste complète des processus disponibles.

**Règle :** Avant toute opération récurrente (recherche internet, intégration de données, révision…), vérifier si un processus existe dans ce dossier et le suivre intégralement.

Processus disponibles :
- **PROC-001** — Recherche internet chiffrée : hiérarchisation des sources, validation, archivage, notes de bas de page.
- **PROC-002** — Intégration d'une donnée institutionnelle : réception, dépôt, vérification de cohérence, intégration.
- **PROC-003** — Révision et validation d'une section : grille de contrôle fond/terminologie/style, rapport de révision.
- **PROC-004** — Vérification terminologique : consultation glossaire, conventions, références OIT, mise à jour si nouveau terme.
- **PROC-005** — Mise à jour du registre des sources : nommage, conversion .txt, enregistrement dans `registre_donnees.md`.

---

## Conventions visuelles de la prévisualisation

La prévisualisation navigateur (`python 09_scripts/serveur_preview.py`) affiche des indicateurs visuels.

### Code couleur des statuts de section

Un point coloré apparaît automatiquement à côté de chaque titre de section selon son statut `NOTE_INTERNE` :

| Couleur | Statut |
|---------|--------|
| 🔴 Rouge `#d42b2b` | `structure initiale` |
| 🟠 Orange `#e07820` | `notes développées` |
| 🟡 Jaune `#c8a800` | `rédigé` |
| 🔵 Bleu `#2e78c8` | `révisé` |
| ⚫ Noir `#111111` | `validé` |

Le point est injecté **automatiquement** par le serveur de prévisualisation en lisant la valeur `Statut :` dans le bloc `<!-- NOTE_INTERNE ... -->`. Aucune action n'est requise des agents.

### Annotation des données sourçées, citations et reformulations — convention interactive

Le système de validation inline utilise deux conventions complémentaires :

#### 1. Lien `source-ref` (données et citations avec lien fichier)

```html
<a href="/files/06_donnees/officielles_web/FICHIER.pdf"
   title="Source : [Organisation] ([Année]) — [Titre]"
   class="source-ref"
   data-val-id="s3-p1-d1"
   data-val-status="à valider"
   data-val-file="02_introduction_generale/section.md">texte, chiffre ou citation</a>
```

#### 2. Balise `<span>` (données, citations, reformulations sans lien direct)

```html
<!-- Donnée chiffrée -->
<span class="val"
      data-val-id="s3-p1-d1"
      data-val-status="à valider"
      data-val-file="02_introduction_generale/section.md">34 %</span>

<!-- Citation directe -->
<span class="val-cite"
      data-val-id="s3-p2-c1"
      data-val-status="à valider"
      data-val-file="02_introduction_generale/section.md">«texte cité»</span>

<!-- Reformulation / paraphrase -->
<span class="val-para"
      data-val-id="s3-p3-r1"
      data-val-status="à valider"
      data-val-file="02_introduction_generale/section.md">texte reformulé</span>
```

**Règles pour les agents :**

- `data-val-id` : identifiant unique dans tout le bulletin. Convention : `s<section>-p<paragraphe>-<type><numéro>` (ex. `s3-p1-d1` pour donnée 1 du paragraphe 1 de la section 3). Le type : `d` données, `c` citation, `r` reformulation.
- `data-val-status` : statut initial toujours `à valider` lors de la rédaction.
- `data-val-file` : chemin relatif (depuis la racine du workspace) vers le fichier `.md` source contenant cet élément.
- Ces attributs permettent de **changer le statut directement depuis la prévisualisation** en cliquant sur l'élément annoté.

**Palette de couleurs du soulignement selon le statut :**

| Statut `data-val-status` | Couleur du soulignement |
|--------------------------|------------------------|
| `à valider` / `à rédiger` / `structure initiale` | Rouge `#d42b2b` |
| `notes développées` | Orange `#e07820` |
| `rédigé` | Jaune `#c8a800` |
| `révisé` | Bleu `#2e78c8` |
| `validé` | Noir `#111111` |

Le soulignement est **toujours pointillé** (`dotted`), quelle que soit la nature du contenu annoté.

**Cascade de validation :**
Le point coloré de chaque titre (`h1`–`h4`) reflète le statut **minimum** de tous les éléments annotés dans la section. Cette cascade est calculée automatiquement par le JS de la prévisualisation.

Cette balise est transparente dans la version publication (le HTML est rendu normalement à l'export).

---

### Badges de validation par paragraphe

Chaque titre `###` (paragraphe d'une section) doit porter un badge de validation inline indiquant son stade de validation. Le badge est géré **manuellement** par les agents.

```html
### Titre du paragraphe <span class="valid-badge nv" title="Non validé — processus de validation non déclenché">non validé</span>
```

| Classe | Stade | Couleur |
|--------|-------|---------|
| `nv` | Non validé | Gris |
| `ec` | En cours | Orange |
| `v`  | Validé | Vert |
| `r`  | Rejeté / à corriger | Rouge |

**Règle :** tout paragraphe rédigé sans validation accordée porte le badge `nv`. Le passage à un autre stade suit le processus de validation (en cours de création).

---

## Workflow de rédaction d'une section

La rédaction d'une section se fait en trois passes successives. Ne pas sauter de passe.

**Passe 1 — Structure** *(si le fichier n'existe pas encore)*
Créer le fichier avec la NOTE_INTERNE complète : objectif, points à couvrir, logique rédactionnelle, formulations possibles. Statut : `structure initiale`.

**Passe 2 — Notes développées** *(si le plan est en place)*
Enrichir la NOTE_INTERNE avec des bullet points développés, des éléments factuels issus des sources disponibles ou des références pertinentes. Statut : `notes développées`.

**Passe 3 — Texte rédigé** *(si les notes sont validées)*
Rédiger le texte dans la section `## Texte rédigé`. Ne pas modifier la NOTE_INTERNE. Statut : `rédigé`.

---

## Documents de référence externes

Un dossier `11_references_externes/` est disponible dans le workspace. Il contient :

- `bulletins_rdc/` — le premier Bulletin statistique RDC (**référence directe** : c'est le bulletin que ce projet prolonge et améliore)
- `autres_bulletins/` — bulletins statistiques d'autres pays ou organisations (**référence de style** : structure, mise en forme, formulations)
- `references_oit_bit/` — conventions, recommandations, guides méthodologiques et métadonnées OIT/BIT (**référence normative** : définitions, cadres, indicateurs, R.202, ODD 1.3.1)

Les fichiers `.txt` lisibles par les agents se trouvent dans les sous-dossiers `_texte/` de chaque dossier.

---

## Données sources

Un dossier `06_donnees/` contient les documents et données utilisés pour la rédaction. Il est organisé par niveau de fiabilité :

- `institutions/` — documents transmis directement par les institutions nationales (CNSS, CNSSAP, FNPSS, ministères…). **Source primaire.** Citer sans réserve avec mention de l'institution et de l'année.
- `officielles_web/` — publications officielles trouvées en ligne : rapports d'organisations internationales, lois, décrets, journaux officiels, bases de données publiques. **Source secondaire acceptable.** Citer avec mention de l'organisation, de l'année et du lien si disponible.
- `sources_incertaines/` — sources moins fiables, estimations non documentées, articles de presse, données à vérifier. **Utiliser uniquement à titre indicatif**, avec réserve explicite dans le texte.

Les fichiers `.txt` lisibles par les agents se trouvent dans les sous-dossiers `_texte/` de chaque dossier.
Le registre `06_donnees/registre_donnees.md` inventorie tous les documents déposés.

**Règle** : ne jamais citer une donnée sans indiquer sa source et son niveau de fiabilité.

**Quand consulter ces documents :**
Ne pas relire ces documents systématiquement à chaque demande. Les consulter uniquement lorsque la tâche le requiert explicitement, par exemple :
- la demande mentionne « en t'appuyant sur le premier bulletin » ;
- la demande porte sur la structure, la terminologie ou les formulations types ;
- une section porte sur des données ou institutions déjà traitées dans le premier bulletin.

Règles d'utilisation :
- Le premier bulletin RDC est la référence principale de continuité : retenir la logique institutionnelle, améliorer la rigueur conceptuelle.
- Les autres bulletins sont des références secondaires : s'en inspirer pour la forme, pas pour le fond.
- Ne jamais reproduire de texte sans transformation.
- Signaler toute contradiction entre un document de référence et les conventions du présent bulletin.

---

## Structure attendue d'un fichier de section

Chaque fichier de section doit suivre ce modèle. Les noms de champs dans la NOTE_INTERNE peuvent varier selon le type de section (conceptuelle, contextuelle, statistique), mais `Logique rédactionnelle` et `Statut` sont toujours présents.

Les valeurs possibles de `Statut` sont : `structure initiale`, `notes développées`, `rédigé`, `révisé`, `validé`.

`````markdown
# Numéro et titre de la section

<!-- NOTE_INTERNE
Grand axe / Objectif :

Points à couvrir / Contenu à couvrir :

Logique rédactionnelle :

Formulation possible :

Statut : [structure initiale | notes développées | rédigé | révisé | validé]
-->

## Texte rédigé

[Texte destiné au rapport.]
```