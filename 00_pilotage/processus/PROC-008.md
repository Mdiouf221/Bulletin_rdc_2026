# PROC-008 — Traitement d'une source entrante (_entrants)

<!-- NOTE_INTERNE
Objet du fichier :
Décrire le processus complet de traitement d'un fichier déposé manuellement dans 06_sources/_entrants/.
Ce processus est conçu pour que l'utilisateur n'ait qu'à déposer le fichier et à signaler son arrivée.
L'agent se charge du reste : identification, nommage, classement, conversion, métadonnées, enregistrement.

Statut : actif
Version : 1.0
Date : 2026-06-09
-->

---

## Déclencheur

Ce processus est activé lorsque :
- L'utilisateur dit : *« J'ai déposé un fichier dans _entrants »* ou *« Traite le fichier entrant »*
- L'utilisateur signale avoir reçu un document (email, téléchargement, transmission) qu'il vient de déposer
- L'agent détecte un fichier dans `06_sources/_entrants/` (hors `README.md`)

---

## Étape 1 — Inventaire des fichiers présents

Lister le contenu de `06_sources/_entrants/` (hors `README.md`).

Pour chaque fichier, collecter ou demander à l'utilisateur :

| Information | À collecter |
|---|---|
| **Nom du fichier** | Tel que déposé |
| **Nature du document** | Rapport, données, présentation, loi, bulletin, convention… |
| **Source / émetteur** | Institution, organisation, auteur |
| **Année / période** | Année de publication ou période couverte |
| **Contexte de réception** | Email, téléchargement web, transmission directe institution |
| **Lien d'origine** | URL si disponible |

Si l'utilisateur ne fournit pas ces informations spontanément, les demander avant de continuer.

---

## Étape 2 — Détermination du sous-dossier de destination

Selon la nature du document, orienter vers :

| Nature | Sous-dossier de destination |
|---|---|
| Transmis directement par une institution nationale (CNSS, CNSSAP, ministère…) | `institutions/` |
| Publication officielle web (OIT, BM, Nations Unies, gouvernement…) | `officielles_web/` |
| Convention, recommandation, guide normatif OIT/BIT | `normes_oit/` |
| Bulletin statistique PS d'un autre pays | `bulletins_comparaison/` |
| Bulletin statistique PS RDC (éditions précédentes) | `bulletins_rdc/` |
| Tableau ESS OIT (CNSS, CNSSAP, ou consolidé) | `ESS/ESS_CNSS/`, `ESS/ESS_CNSSAP/` ou `ESS/ESS_RDC_tous_regimes/` |
| Document de l'atelier de lancement | `atelier_lancement/presentations/`, `compte_rendus/` ou `listes_participants/` |
| Source incertaine, non vérifiée ou à vérifier | `sources_incertaines/` |

En cas de doute, proposer deux options à l'utilisateur et attendre sa validation.

---

## Étape 3 — Nommage normalisé

Vérifier que le nom du fichier suit la convention :
```
[Organisation]_[Sujet]_[Année].[extension]
```

Exemples :
- `CNSS_rapport_annuel_2023.pdf` ✅
- `OIT_R202_socles_protection_sociale_2012.pdf` ✅
- `rapport final version 3 (2).pdf` ❌ → proposer un renommage

Si le nom n'est pas conforme, proposer un nom normalisé à l'utilisateur. Ne pas renommer sans accord explicite.

---

## Étape 4 — Déplacement vers le sous-dossier de destination

Une fois le sous-dossier et le nom validés :
- Déplacer le fichier de `_entrants/` vers le sous-dossier cible
- Si le fichier doit être renommé, créer la copie renommée dans la destination et signaler que l'original peut être supprimé de `_entrants/`

---

## Étape 5 — Conversion en texte lisible (fichiers PDF)

Si le fichier est un **PDF** :
- Vérifier si un fichier `.txt` existe déjà dans le sous-dossier `_texte/` correspondant
- Si non : lancer `09_scripts/convertir_pdf_en_texte.py` ou extraire manuellement le texte
- Déposer le `.txt` dans `[sous-dossier]/_texte/`

Si le fichier est un **XLSX / XLSM** (tableau de données) :
- Lire les feuilles principales (inventaire, données clés)
- Créer directement un fichier de métadonnées `.txt` (voir Étape 6)

Si le fichier est un **PPTX / DOCX** :
- Extraire les points clés manuellement et créer un fichier de métadonnées

---

## Étape 6 — Création de la fiche de métadonnées

Créer un fichier `.txt` dans `[sous-dossier]/_texte/` avec la structure suivante :

```
TITRE : [Titre complet du document]
SOURCE : [Organisation / Institution]
CONTACT : [si disponible]
PÉRIODE : [Année ou plage]
URL : [si disponible]
NIVEAU : [Source primaire / Source secondaire / Référence normative / À vérifier]

---

CONTENU

[Résumé du contenu : objectif du document, données clés, indicateurs, institutions concernées]

---

OBSERVATIONS MÉTHODOLOGIQUES

[Points d'attention, anomalies, limites d'utilisation]

---

CITATION RECOMMANDÉE

[Organisation] ([Année]), [Titre], [Lieu d'édition].
```

---

## Étape 7 — Enregistrement dans les registres

### Dans `registre_donnees.md`
Ajouter une ligne dans le tableau du sous-dossier correspondant.

### Dans `registre_sources.json`
Ajouter une entrée avec au minimum :
```json
{
  "id": "[CODE-COURT]",
  "titre": "[Titre]",
  "organisation": "[Organisation]",
  "annee": [Année],
  "niveau_fiabilite": [1-5],
  "sous_dossier": "[sous-dossier]",
  "fichier_source": "06_sources/[sous-dossier]/[fichier]",
  "fichier_texte_extrait": "06_sources/[sous-dossier]/_texte/[fichier].txt",
  "statut_pdf": "présent",
  "statut_texte": "converti",
  "statut_verification": "à valider",
  "note": "[Description courte]",
  "citation_recommandee": "[Citation]",
  "sections_citantes": []
}
```

---

## Étape 8 — Vérification que `_entrants/` est vide

Confirmer qu'il ne reste aucun fichier non traité dans `06_sources/_entrants/` (hors `README.md`).

---

## Étape 9 — Confirmation à l'utilisateur

Fournir un résumé :
```
✓ Fichier traité : [nom du fichier]
✓ Déplacé vers : 06_sources/[sous-dossier]/
✓ Converti en .txt : [oui / non / type non PDF]
✓ Fiche de métadonnées : 06_sources/[sous-dossier]/_texte/[fichier].txt
✓ Enregistré dans : registre_donnees.md + registre_sources.json
```

Proposer une ligne pour `00_pilotage/journal_modifications.md` :
```
| [Date] | PROC-008 | Intégration de [fichier] → 06_sources/[sous-dossier]/ | [utilisateur] |
```

---

## Livrables attendus

- [ ] Fichier déplacé dans le bon sous-dossier
- [ ] Fichier renommé si nécessaire (avec accord utilisateur)
- [ ] Version `.txt` disponible dans `_texte/`
- [ ] Fiche de métadonnées créée
- [ ] Ligne ajoutée dans `registre_donnees.md`
- [ ] Entrée ajoutée dans `registre_sources.json`
- [ ] `_entrants/` vide (hors README)
- [ ] Utilisateur informé
