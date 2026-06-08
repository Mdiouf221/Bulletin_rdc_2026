# PROC-001 — Recherche internet chiffrée

<!-- NOTE_INTERNE
Objet du fichier :
Décrire le processus complet à suivre lorsqu'une demande de recherche internet portant sur des données,
statistiques ou informations factuelles est formulée pour alimenter le bulletin.

Ce processus garantit :
- que les sources retenues sont hiérarchisées par niveau d'institutionnalité ;
- que l'utilisateur valide les résultats avant toute intégration ;
- que les sources sont correctement archivées, référencées et tracées dans le projet.

Statut : actif
Version : 1.0
Date : 2026-06-08
-->

---

## Déclencheur

Ce processus est activé lorsque l'utilisateur formule une demande du type :
- « Cherche des données sur… »
- « Trouve des statistiques récentes sur… »
- « Quelle est la couverture de… selon les sources disponibles ? »
- « Fais une recherche internet chiffrée sur… »

---

## Étape 1 — Analyse de la demande

Avant toute recherche, clarifier les éléments suivants :

| Élément | Questions à résoudre |
|---------|---------------------|
| **Sujet** | Quel indicateur, institution, programme ou phénomène est visé ? |
| **Périmètre géographique** | RDC uniquement ? Comparaison régionale ou internationale ? |
| **Période** | Quelle année ou plage temporelle est attendue ? |
| **Précision** | Ordre de grandeur suffit-il, ou faut-il des données exactes ? |
| **Usage prévu** | Texte narratif ? Tableau ? Note de bas de page ? Indicateur synthétique ? |

Si des éléments manquent, les demander à l'utilisateur avant de lancer la recherche.

---

## Étape 2 — Recherche par ordre d'institutionnalité

La recherche s'effectue **dans l'ordre suivant**, du plus fiable au moins fiable.
Toujours épuiser un niveau avant de passer au suivant.

### Niveau 1 — Organisations internationales de référence *(source prioritaire)*

Consulter en premier :
- **OIT / BIT** : ILOSTAT, rapports mondiaux sur la protection sociale, bases de données SSPTW
- **Banque mondiale** : World Development Indicators (WDI), rapports pays
- **OMS / WHO** : Global Health Expenditure Database, Observatory
- **UNICEF** : bases de données sur la protection sociale de l'enfant
- **PNUD / UNDP** : Human Development Reports, données IDH
- **Nations Unies / UN** : SDG indicators database (ODD 1.3.1)
- **FMI** : Government Finance Statistics, Article IV RDC

> Dossier de stockage : `06_donnees/officielles_web/`

### Niveau 2 — Sources nationales officielles RDC *(source prioritaire si disponible)*

Consulter ensuite :
- **Institut National de la Statistique (INS-RDC)** : rapports, annuaires statistiques
- **Ministère de la Santé** : rapports annuels, PNDS
- **Ministère des Affaires sociales** : rapports, stratégies
- **Ministère du Budget / Finances** : lois de finances, rapports d'exécution budgétaire
- **Journal officiel de la RDC** : lois, décrets, ordonnances

> Dossier de stockage : `06_donnees/officielles_web/` (si en ligne) ou `06_donnees/institutions/` (si transmis directement)

### Niveau 3 — Organisations régionales africaines *(source secondaire acceptable)*

Consulter si les niveaux 1 et 2 n'ont pas fourni de données suffisantes :
- **Union Africaine (UA)** : rapports sur la protection sociale
- **CIPRES** (Conférence Interafricaine de la Prévoyance Sociale) : données comparatives
- **SADC** : rapports régionaux si pertinents
- **COMESA** : idem

> Dossier de stockage : `06_donnees/officielles_web/`

### Niveau 4 — Institutions académiques et centres de recherche *(source secondaire à qualifier)*

En dernier recours parmi les sources fiables :
- Universités reconnues, think tanks (ODI, CGD, IFPRI…)
- Publications dans des revues scientifiques indexées
- Évaluations indépendantes commanditées par des organisations internationales

> Dossier de stockage : `06_donnees/officielles_web/`

### Niveau 5 — Presse spécialisée et rapports d'ONG *(source à traiter avec prudence)*

À n'utiliser qu'à titre indicatif, avec réserve explicite :
- Articles de presse (RFI, Reuters, AFP, presse nationale congolaise)
- Rapports d'ONG (Oxfam, Save the Children, IRC…)
- Blogs institutionnels, posts LinkedIn de fonctionnaires

> Dossier de stockage : `06_donnees/sources_incertaines/`

---

## Étape 3 — Présentation des résultats à l'utilisateur

Après la recherche, présenter les résultats dans un tableau structuré :

```
## Résultats de la recherche — [Sujet]

| # | Source | Niveau | Donnée trouvée | Période | URL / Référence | Fiabilité |
|---|--------|--------|----------------|---------|-----------------|-----------|
| 1 | OIT/ILOSTAT | Niveau 1 | XX% de couverture | 2022 | https://… | ✅ Haute |
| 2 | INS-RDC | Niveau 2 | XX millions affiliés | 2021 | Rapport annuel p.X | ✅ Haute |
| 3 | Article presse | Niveau 5 | Estimation ~XX% | 2023 | https://… | ⚠️ À confirmer |

**Recommandation :** Retenir les résultats 1 et 2 pour le bulletin. Le résultat 3 peut être cité avec réserve.
```

Indiquer clairement :
- quelles sources sont recommandées pour le bulletin ;
- lesquelles nécessitent une réserve ;
- si aucune source fiable n'a été trouvée (signalement explicite).

---

## Étape 4 — Validation par l'utilisateur

Attendre la validation explicite de l'utilisateur avant toute intégration.

**Si l'utilisateur accepte tout ou partie des résultats → passer à l'Étape 5.**  
**Si l'utilisateur rejette les résultats → reprendre à l'Étape 2 ou clore le processus.**

---

## Étape 5 — Intégration dans le bulletin

Lorsque les résultats sont validés, effectuer **dans cet ordre** les actions suivantes :

### 5a — Renseigner la section du bulletin

- Ouvrir le fichier Markdown de la section concernée.
- Insérer les données dans le bloc `## Texte rédigé` ou dans la NOTE_INTERNE selon le statut de la section.
- Utiliser la formulation appropriée selon le niveau de fiabilité :
  - Niveau 1-2 : citation directe avec référence entre parenthèses `(OIT, 2022)` ou en note de bas de page.
  - Niveau 3-4 : `Selon [organisation] ([année])…`
  - Niveau 5 : `D'après une source à confirmer…` ou `Selon une estimation non officielle…`

**Convention d'annotation visuelle des données sourçées (validation interactive) :**

Pour que les données issues d'une recherche internet apparaissent avec un soulignement coloré dans la prévisualisation (avec popup de changement de statut au clic), utiliser l'une des deux formes suivantes directement dans le Markdown :

**Forme 1 — avec lien vers le fichier source (recommandée) :**
```html
<a href="/files/06_donnees/officielles_web/NOM_FICHIER.pdf"
   title="Source : [Organisation] ([Année]) — [Titre du document], p. X"
   class="source-ref"
   data-val-id="[id-unique]"
   data-val-status="à valider"
   data-val-file="[chemin/vers/section.md]">donnée chiffrée</a>
```

**Forme 2 — span sans lien (pour citations et reformulations) :**
```html
<!-- Donnée -->
<span class="val" data-val-id="[id]" data-val-status="à valider"
      data-val-file="[chemin/section.md]">34 %</span>

<!-- Citation -->
<span class="val-cite" data-val-id="[id]" data-val-status="à valider"
      data-val-file="[chemin/section.md]">«texte cité»</span>

<!-- Reformulation -->
<span class="val-para" data-val-id="[id]" data-val-status="à valider"
      data-val-file="[chemin/section.md]">texte reformulé</span>
```

Convention pour `data-val-id` : `s<n°section>-p<n°paragraphe>-<type><n°>`  
Types : `d` = donnée, `c` = citation, `r` = reformulation  
Exemple : `s3-p1-d1`, `s3-p2-c1`, `s3-p3-r1`

Exemple complet dans une phrase :

```markdown
En 2020, <a href="/files/06_donnees/officielles_web/BM_WDI_RDC_2024.txt"
title="Source : Banque mondiale (2024) — World Development Indicators"
class="source-ref" data-val-id="s3-p1-d1" data-val-status="à valider"
data-val-file="02_introduction_generale/0_3_strategie_donnees_statistiques.md"
>85,3 % de la population</a> vivait sous le seuil de pauvreté.
```

> Cette annotation est uniquement pour la version travail (prévisualisation navigateur). Elle reste invisible dans la version publication car le texte HTML est rendu normalement à l'export.

### 5b — Archiver la source dans le projet

Enregistrer une copie de la source (de préférence en PDF, sinon en `.txt` ou `.html`) dans le dossier approprié :

| Niveau de fiabilité | Dossier de dépôt |
|--------------------|--------------------|
| Niveaux 1 à 4 | `06_donnees/officielles_web/` |
| Niveau 5 | `06_donnees/sources_incertaines/` |
| Document transmis par institution | `06_donnees/institutions/` |

Nommer le fichier selon la convention : `[Organisation]_[Sujet]_[Année].[extension]`  
Exemple : `OIT_protection_sociale_RDC_2022.pdf`

> **⚠️ Règle critique pour la prévisualisation :**  
> Le fichier PDF **doit avoir exactement le même nom de base** que le fichier `.txt` de métadonnées correspondant.  
> Exemple : si les métadonnées sont dans `ONU_WPP_2024_RDC_population.txt`, le PDF doit s'appeler `ONU_WPP_2024_RDC_population.pdf` et être déposé dans le même dossier.  
> Le serveur de prévisualisation détecte automatiquement ce PDF et propose "📄 Ouvrir le PDF local" à la place du lien web.  
> Si le PDF n'est pas disponible localement, le bouton renvoie vers l'URL web définie dans le champ `URL :` du fichier `.txt`.

### 5c — Mettre à jour le registre des données

Ouvrir `06_donnees/registre_donnees.md` et ajouter une ligne dans le tableau du sous-dossier concerné :

| Fichier | Source | Type | Description | Lien d'origine | Période | Converti | Statut |
|---------|--------|------|-------------|----------------|---------|---------|--------|
| `OIT_protection_sociale_RDC_2022.pdf` | OIT/ILOSTAT | Base de données | Taux de couverture sociale RDC | https://… | 2022 | Non | À convertir |

### 5d — Ajouter la note de bas de page dans la section

Dans le fichier de section, ajouter la référence bibliographique complète selon le format :
```
[^1]: Organisation Internationale du Travail (OIT). *World Social Protection Report 2022–24*. Genève : BIT, 2022. Disponible en ligne : https://…
```

### 5e — Mettre à jour la bibliographie du bulletin

Si le bulletin dispose d'une section `05_references/bibliographie.md` (ou équivalent), y ajouter la référence.

### 5f — Journaliser la modification

Proposer une ligne à ajouter dans `00_pilotage/journal_modifications.md` :
```
| [Date] | PROC-001 | Intégration de données [sujet] issues de [source] dans [section] |
```

---

## Livrables attendus à la fin du processus

- [ ] Tableau de résultats présenté à l'utilisateur
- [ ] Validation de l'utilisateur obtenue
- [ ] Section du bulletin mise à jour
- [ ] Source archivée dans `06_donnees/`
- [ ] Registre des données mis à jour (`registre_donnees.md`)
- [ ] Note de bas de page ajoutée dans la section
- [ ] Bibliographie mise à jour (si applicable)
- [ ] Ligne proposée pour `journal_modifications.md`

---

## Règles transversales

- Ne jamais intégrer une donnée sans validation préalable de l'utilisateur.
- Ne jamais inventer une URL ou une référence bibliographique.
- Si une information ne peut être trouvée sur aucun niveau : le signaler explicitement avec la mention `[DONNÉE MANQUANTE — recherche infructueuse]`.
- Conserver toujours la hiérarchie des niveaux : une donnée de niveau 5 ne peut jamais se substituer à une absence de donnée de niveau 1 sans réserve explicite.
