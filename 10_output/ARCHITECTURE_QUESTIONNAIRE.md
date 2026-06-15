# Architecture : Intégration Questionnaire ↔ Dropdown ↔ Graphiques

## Vue d'ensemble

```
┌───────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1 : Sélection rapide (Dropdown)                             │
├───────────────────────────────────────────────────────────────────┤
│ Utilisateur choisit :                                              │
│ • Institution : CNSS / CNSSAP                                     │
│ • Régime : all / CNSS_R1 / CNSS_R2 ...                           │
│                                                                    │
│ → Graphiques rendus (Plotly pré-calculé depuis CHARTS_INST)       │
└───────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────┐
│ ÉTAPE 2 : Qualification (Questionnaire Modal)                     │
├───────────────────────────────────────────────────────────────────┤
│ Utilisateur clique ⚙️ Paramètres → Modal pop-up                   │
│                                                                    │
│ Q1 — Affiliation aux régimes                                      │
│     "Prestations familiales" partage cotisants avec               │
│     "Risques professionnels" ?  ☐ Oui  ☐ Non                    │
│     "Prestations familiales" partage cotisants avec               │
│     "Pension" ?                  ☐ Oui  ☐ Non                    │
│     etc.                                                           │
│                                                                    │
│ Q2 — Agrégation des recettes/dépenses (non appliquée au graph)   │
│ Q4 — Unité des bénéficiaires (conversion de chiffres)            │
│                                                                    │
│ [Annuler] [Sauvegarder]                                           │
│                                                                    │
│ → Réponses persistées en JSON (questionnaire_data.json)           │
└───────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────┐
│ ÉTAPE 3 : Réapplication des graphiques                            │
├───────────────────────────────────────────────────────────────────┤
│ Event 'questionnaire-saved' déclenché                             │
│                                                                    │
│ Module BranchFusion :                                             │
│ 1. Charge les réponses Q1 depuis questionnaire_data.json          │
│ 2. Identifie les groupes de branches à fusionner                  │
│    • Si "Prestations familiales" et "Risques prof" : "Oui"       │
│      → Les fusionner en une seule courbe/aire                     │
│ 3. Re-calcule les traces Plotly :                                 │
│    • Additionne les valeurs y des branches du même groupe         │
│    • Met à jour légende : "Pension + Risques professionnels"      │
│ 4. Re-rend le graphique avec Plotly.react()                       │
│                                                                    │
│ Résultat :                                                         │
│ ✓ Les branches doublons sont visuellement fusionnées              │
│ ✓ Graphique mis à jour en temps réel                              │
│ ✓ Pas de rechargement page, pas de perte de données               │
└───────────────────────────────────────────────────────────────────┘
```

---

## Fichiers créés

### 1. **questionnaire_modal.js** (déjà créé)
- Gère l'UI du modal (Q1, Q2, Q4)
- Persistance JSON dans `questionnaire_data.json`
- Émet l'événement `questionnaire-saved` après save

### 2. **questionnaire_modal.css** (déjà créé)
- Styles du modal, matrices, radio buttons

### 3. **branch_fusion.js** (nouveau)
- Classe `BranchFusion` : gère la fusion de traces Plotly
- Écoute l'événement `questionnaire-saved`
- Re-calcule et re-rend les graphiques

### 4. **questionnaire_data.json** (déjà créé)
- Stockage des réponses Q1/Q2/Q4 par institution
```json
{
  "CNSS": {
    "Q1": {
      "CNSS_R1__CNSS_R2": "true",  // Prestations familiales = Risques prof
      "CNSS_R1__CNSS_R3": "false", // Prestations familiales ≠ Pension
      ...
    },
    "Q2": { ... },
    "Q4": { ... }
  }
}
```

---

## Intégration dans dashboard_regimes.html

### À ajouter dans `<head>`

```html
<!-- CSS -->
<link rel="stylesheet" href="questionnaire_modal.css">

<!-- JS -->
<script src="questionnaire_modal.js"></script>
<script src="branch_fusion.js"></script>
```

### À modifier dans le dropdown

Exemple (à adapter selon structure actuelle) :

```javascript
// Avant : dropdown change listener
document.getElementById('regime-select').addEventListener('change', (e) => {
  const regime = e.target.value;
  renderGraphs(regime);
});

// Après : ajouter bouton Paramètres
const regimeSelectContainer = document.getElementById('regime-select-container');
const parametersBtn = document.createElement('button');
parametersBtn.id = 'questionnaire-btn';
parametersBtn.textContent = '⚙️ Paramètres';
parametersBtn.className = 'questionnaire-btn';
parametersBtn.onclick = () => {
  const institution = document.getElementById('institution-select').value;
  const regimes = ['CNSS_R1', 'CNSS_R2', 'CNSS_R3', 'CNSS_R4']; // À extraire dynamiquement
  window.questionnaire.openModal(institution, regimes);
};
regimeSelectContainer.appendChild(parametersBtn);
```

---

## Flow de données (détaillé)

### 1. Utilisateur change le régime
```
Dropdown change
  → renderGraphs(regime)
    → Plotly.newPlot() avec CHARTS_INST[institution][regime]
    → Graphiques affichés (sans fusion)
```

### 2. Utilisateur clique ⚙️ Paramètres
```
Click ⚙️
  → questionnaire_modal.js : openModal(institution, regimes)
    → Charge questionnaire_data.json
    → Pré-remplit Q1/Q2/Q4 si réponses existantes
    → Affiche le modal
```

### 3. Utilisateur remplit Q1 et clique "Sauvegarder"
```
Click "Sauvegarder"
  → questionnaire_modal.js : saveData(institution)
    → Collecte réponses Q1/Q2/Q4 du DOM
    → Sérialise en JSON
    → PUT questionnaire_data.json
    → window.dispatchEvent('questionnaire-saved')
```

### 4. Fusion de branches appliquée
```
Event 'questionnaire-saved'
  → branch_fusion.js listener
    → Charge Q1 data depuis questionnaire_data.json
    → identifyFusionGroups(q1Data, branchMapping)
      • Lit Q1 : "CNSS_R1__CNSS_R2" : "true"
      • → Ajoute R1 et R2 au même groupe
    → mergeTraces(traces, fusionGroups)
      • Pour chaque groupe :
        - Additionne y : [v1+v2, v2+v2, ...]
        - Combine names : "Prestations familiales + Risques prof"
    → Plotly.react(graphId, newData) pour chaque graphique
    → Graphiques mis à jour en temps réel ✓
```

---

## Mapping branche → régimes

À extraire des ESS ou hardcoder selon institution :

```javascript
// CNSS (4 branches)
{
  "Prestations familiales": ["CNSS_R1"],
  "Risques professionnels": ["CNSS_R2"],
  "Pension": ["CNSS_R3"],
  "Action sociale et sanitaire": ["CNSS_R4"]
}

// CNSSAP (2 régimes)
{
  "Régime de base contributif": ["CNSSAP_R1"],
  "Réforme du transfert non-contributif": ["CNSSAP_R2"]
}
```

---

## À vérifier / À adapter

1. **Structure du dropdown**
   - Quel est l'ID/classe du dropdown d'institution ?
   - Quel est l'ID/classe du dropdown de régime ?
   - Comment les regimes sont-ils actuellement passés aux graphiques ?

2. **Extraction des régimes/branches**
   - Actuellement hardcodé dans `branch_fusion.js`
   - Préférable : extraire dynamiquement des ESS via un endpoint

3. **Persistance côté serveur**
   - Actuellement : PUT sur `questionnaire_data.json` local
   - À adapter : endpoint backend pour persistance en base de données

4. **Q2 / Q4 dans les graphiques**
   - Q1 → fusion de branches ✓
   - Q2 → annotation recettes/dépenses combinées (à implémenter)
   - Q4 → conversion unité bénéficiaires (à implémenter)

---

## Exemple concret : CNSS 2022

### Données brutes (CHARTS_INST)
```
Prestations familiales : 613,761 cotisants
Risques professionnels : 613,761 cotisants ← IDENTIQUE
Pension : 613,761 cotisants ← IDENTIQUE
Action sociale : null
```

### Q1 Réponse utilisateur
```
"CNSS_R1__CNSS_R2": "true"   // Prest fam = Risques prof
"CNSS_R1__CNSS_R3": "true"   // Prest fam = Pension
"CNSS_R2__CNSS_R3": "true"   // Risques prof = Pension
```

### Résultat graphique
```
Au lieu de :
  ├─ Prestations familiales : 613,761
  ├─ Risques prof : 613,761 (doublonné !)
  ├─ Pension : 613,761 (doublonné !)
  └─ Action soc : (vide)

On obtient :
  ├─ Prestations familiales + Risques prof + Pension : 613,761
  └─ Action soc : (vide)
```

Le graphique affiche maintenant la réalité : une seule population de 613,761 cotisants couverts par 3 branches.

---

## Notes techniques

- **Plotly.react()** : Redessine un graphique tout en préservant interactions/zoom
- **legendgroup** : Attribut Plotly permettant de grouper visuellement des traces
- **stackgroup** : Attribut Plotly pour empiler les traces (utilisé pour les aires)
- **JSON persistence** : Pas de versioning ; chaque save écrase complètement
