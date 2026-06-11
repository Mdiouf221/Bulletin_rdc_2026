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

## Rôle de l'agent dans ce projet

Dans ce projet, l'agent Copilot joue le rôle d'**orchestrateur central**, tel que défini dans `00_pilotage/agents/agent_orchestrateur.md`.

**Modèle recommandé pour ce rôle :** `claude-sonnet-4.6` (raisonnement complexe, dispatch multi-agents, consolidation).

**À chaque nouvelle session :**
1. Lire `00_pilotage/agents/agent_orchestrateur.md` pour connaître les règles de dispatch.
2. Lire `00_pilotage/agents/README.md` pour connaître la liste des agents disponibles et leurs modèles.
3. Appliquer les règles de dispatch pour toute tâche reçue.

**Règle de proportionnalité (économie de tokens) :**

Avant de répondre, évaluer la complexité de la demande :

| Type de demande | Comportement attendu |
|----------------|----------------------|
| Question simple, conversationnelle (« merci », « qu'est-ce que X ? », « où est le fichier Y ? ») | Répondre **directement, en moins de 5 phrases**. Ne pas lire de fichiers. Ne pas lancer de sous-agent. |
| Modification mineure sur un seul fichier connu | Faire soi-même. Ne pas dispatcher. |
| Tâche complexe, multi-fichiers, rédaction longue | Dispatcher selon `agent_orchestrateur.md`. |

Ne jamais sur-instrumenter une réponse simple.

---

## Processus opérationnels

Un dossier `00_pilotage/processus/` contient les processus opérationnels standardisés à suivre pour les opérations récurrentes du projet.

> Consulter `00_pilotage/processus/index.md` pour la liste complète des processus disponibles.

**Règle :** Avant toute opération récurrente (recherche internet, intégration de données, révision…), vérifier si un processus existe dans ce dossier et le suivre intégralement.

Processus disponibles :
- **PROC-001** — Recherche internet chiffrée : hiérarchisation des sources, validation, archivage, notes de bas de page.
- **PROC-002** — Intégration d'une donnée institutionnelle : réception, dépôt, vérification de cohérence, intégration.
- **PROC-003** — Révision et validation d'une section : grille de contrôle fond/terminologie/style, rapport de révision.
- **PROC-004** — Vérification terminologique : consultation glossaire, conventions, références OIT, mise à jour si nouveau terme.
- **PROC-005** — Mise à jour du registre des sources : nommage, conversion .txt, enregistrement dans `registre_donnees.md` et `registre_sources.json`.
- **PROC-008** — Traitement d'une source entrante : dossier `06_sources/_entrants/` → classement, nommage, conversion, métadonnées, enregistrement.
- **PROC-010** — Suppression propre d'un import ESS en base : simulation, suppression sécurisée, traçabilité.

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
<a href="/files/06_sources/officielles_web/FICHIER.pdf"
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

## Documents de référence et sources

Toutes les sources — données, références normatives, bulletins comparatifs, documents institutionnels — sont regroupées dans un unique dossier **`06_sources/`**, organisé par nature :

| Sous-dossier | Nature | Niveau de fiabilité |
|---|---|---|
| `ESS/` | Tableaux ESS OIT (CNSS, CNSSAP, tous régimes) | **Source primaire** |
| `institutions/` | Documents transmis directement par les institutions nationales | **Source primaire** |
| `officielles_web/` | Publications officielles en ligne (OIT, Banque mondiale, INS…) | **Source secondaire acceptable** |
| `sources_incertaines/` | Estimations non documentées, presse, données à vérifier | **À utiliser avec prudence** |
| `normes_oit/` | Conventions, recommandations, guides méthodologiques OIT/BIT | **Référence normative** |
| `bulletins_rdc/` | Premier Bulletin statistique RDC | **Référence directe** |
| `bulletins_comparaison/` | Bulletins d'autres pays (Mozambique, Angola, Jordanie…) | **Référence de style** |
| `atelier_lancement/` | Documents et présentations de l'atelier de lancement | **Source primaire** |

Les fichiers `.txt` lisibles par les agents se trouvent dans les sous-dossiers `_texte/` de chaque dossier.
Le registre `06_sources/registre_donnees.md` inventorie tous les documents.
Le registre `06_sources/registre_sources.json` est le tableau de correspondance structuré de toutes les sources.

**Règle** : ne jamais citer une donnée sans indiquer sa source et son niveau de fiabilité.

**Workflow unifié pour toute source déposée dans `06_sources/` :**
1. Archiver le fichier original (PDF, XLSX…) dans le bon sous-dossier
2. Convertir en `.txt` lisible dans le sous-dossier `_texte/`
3. Créer un fichier de métadonnées `.txt` (résumé, données clés, citation recommandée)
4. Inscrire la source dans `registre_donnees.md` et `registre_sources.json`
5. Intégrer dans le bulletin si pertinent (avec mention de source et niveau de fiabilité)

**Dossier de réception `06_sources/_entrants/` :**
Toute source reçue par email ou téléchargée manuellement peut être déposée dans ce dossier transitoire.
L'agent applique ensuite **PROC-008** pour la traiter entièrement (classement, nommage, conversion, métadonnées, enregistrement).
Ce dossier doit être vide après traitement.

**Quand consulter ces documents :**
Ne pas relire ces documents systématiquement. Les consulter uniquement lorsque la tâche l'exige :
- la demande mentionne « en t'appuyant sur le premier bulletin » ;
- la demande porte sur la structure, la terminologie ou les formulations types ;
- une section porte sur des données ou institutions déjà traitées.

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