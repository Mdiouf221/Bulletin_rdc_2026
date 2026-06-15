# 📊 IMPLÉMENTATION QUESTIONNAIRE QUALIFICATION — SYNTHÈSE FINALE

## 🎯 Objectif

Permettre aux utilisateurs de **déclarer les relations entre branches** d'un régime de protection sociale (ex: si "Prestations familiales" et "Risques professionnels" partagent les mêmes cotisants), puis **fusionner automatiquement les courbes** dans les graphiques Plotly du dashboard.

---

## 📁 Fichiers créés

### **Core**
| Fichier | Rôle | État |
|---------|------|------|
| `questionnaire_modal.js` | UI du questionnaire modal (Q1, Q2, Q4) + persistance JSON | ✅ Créé |
| `questionnaire_modal.css` | Styles complets du modal | ✅ Créé |
| `branch_fusion.js` | Fusion des traces Plotly selon réponses Q1 | ✅ Créé |
| `questionnaire_data.json` | Stockage des réponses (Q1/Q2/Q4 par institution) | ✅ Créé |

### **Documentation**
| Fichier | Rôle |
|---------|------|
| `ARCHITECTURE_QUESTIONNAIRE.md` | Vue d'ensemble du flux (Dropdown → Questionnaire → Graphiques) |
| `INTEGRATION_INSTRUCTIONS.js` | Code à ajouter au dashboard_regimes.html (5 étapes) |
| `SYNTHESIS_FINAL.md` | Ce fichier — synthèse complète |

---

## 🔄 Flux d'utilisation

### **Étape 1 : Sélection rapide (Dropdown existant)**
```
Utilisateur sélectionne :
  Institution : [CNSS ▼]
  Régime : [all ▼]  ← Les graphiques se mettent à jour
```
- HTML: `#sel-institution` avec `onchange="updateInstitution()"`
- JS: Fonction `updateInstitution()` de visualiser_regimes.py
- Résultat: Graphiques pré-calculés injectés depuis `CHARTS_INST`

### **Étape 2 : Qualification (Nouveau bouton ⚙️)**
```
Utilisateur clique ⚙️ Paramètres
  → Modal pop-up s'ouvre avec les 3 questionnaires
```

**Q1 — Affiliation aux régimes**
```
Matrice de checkboxes :
  "Prestations familiales" partage cotisants avec :
    ☐ Risques professionnels
    ☐ Pension
    ☐ Action sociale
```

**Q2 — Agrégation des recettes/dépenses** (pour info future)
```
Tableau : Recettes/dépenses de chaque branche combinées avec quelles autres ?
```

**Q4 — Unité des bénéficiaires** (pour branches Enfants/Famille)
```
Radio buttons : Enfant / Ménage / Personne / Autre
```

### **Étape 3 : Sauvegarde et fusion**
```
Utilisateur clique [Sauvegarder]
  → Réponses persistées en questionnaire_data.json
  → Événement 'questionnaire-saved' déclenché
  → branch_fusion.js re-calcule les graphiques Plotly
  → Courbes doublons fusionnées ✓
```

---

## 🧮 Exemple concret : CNSS 2022

### **Données brutes (ESS)**
```
Prestations familiales : 613,761 cotisants
Risques professionnels : 613,761 cotisants  ← IDENTIQUE
Pension : 613,761 cotisants                 ← IDENTIQUE
Action sociale : null
```

### **Questionnaire Q1 rempli**
```
"CNSS_R1__CNSS_R2": "true"   // Prestations fam = Risques prof ✓
"CNSS_R1__CNSS_R3": "true"   // Prestations fam = Pension ✓
"CNSS_R2__CNSS_R3": "true"   // Risques prof = Pension ✓
```

### **Graphique avant fusion**
```
❌ Mauvaise représentation (données gonflées) :
   ├─ Prestations familiales : 613,761
   ├─ Risques prof : 613,761  (doublonné !)
   ├─ Pension : 613,761       (doublonné !)
   └─ Action soc : (vide)
   
   Total : 1,841,283 cotisants (faux !)
```

### **Graphique après fusion**
```
✓ Représentation correcte :
   ├─ Prestations fam + Risques prof + Pension : 613,761
   └─ Action soc : (vide)
   
   Total : 613,761 cotisants (juste !)
```

---

## ⚙️ Architecture technique

### **Données globales disponibles** (depuis visualiser_regimes.py)

```javascript
// 1. Regimes par institution
window.REGIMES_PAR_INST = {
  "CNSS": ["CNSS_R1", "CNSS_R2", "CNSS_R3", "CNSS_R4"],
  "CNSSAP": ["CNSSAP_R1", "CNSSAP_R2"]
}

// 2. Mapping code → nom
window.NOM_COURT = {
  "CNSS_R1": "Prestations familiales",
  "CNSS_R2": "Risques professionnels",
  "CNSS_R3": "Pension",
  "CNSS_R4": "Action sociale et sanitaire",
  "CNSSAP_R1": "Régime de base",
  "CNSSAP_R2": "Réforme du transfert"
}

// 3. Graphiques pré-calculés
window.CHARTS_INST = {
  "CNSS": {
    "all": "<div>...Plotly HTML...</div>",
    "hommes": "...",
    "femmes": "..."
  }
}
```

### **Classes JavaScript**

**QuestionnaireModal** (questionnaire_modal.js)
```javascript
- openModal(institution, regimes)    // Ouvre le modal
- saveData(institution)               // Sauvegarde Q1/Q2/Q4
- getStoredValue(inst, question, key) // Récupère une réponse
```

**BranchFusion** (branch_fusion.js)
```javascript
- applyBranchFusion(graphId, q1Data, branchMapping)
- identifyFusionGroups(q1Data, branchMapping)
- mergeTraces(originalTraces, fusionGroups)
```

---

## 🔌 Intégration au dashboard

### **1. Ajouter les fichiers dans `<head>`**
```html
<link rel="stylesheet" href="questionnaire_modal.css">
<script src="questionnaire_modal.js"></script>
<script src="branch_fusion.js"></script>
```

### **2. Ajouter le bouton ⚙️ après le dropdown institution**
```javascript
// Code fourni dans INTEGRATION_INSTRUCTIONS.js
// Crée un bouton "⚙️ Paramètres" avec onclick handler
```

### **3. Wrapper la fonction updateInstitution()**
```javascript
// Hook pour appliquer la fusion après rendu des graphiques
// Délai de 500ms pour que Plotly finisse
```

### **4. Écouter l'événement 'questionnaire-saved'**
```javascript
window.addEventListener('questionnaire-saved', (e) => {
  // Re-applique la fusion avec les nouvelles réponses
});
```

### **5. (Optional) Adapter la persistance**
- Actuellement: `PUT questionnaire_data.json` (local)
- À faire: Créer endpoint `/api/questionnaire` ou utiliser localStorage

---

## 📊 Flux des données

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Dropdown change                                               │
│    Institution: CNSS → updateInstitution()                      │
└────────────────────────────┬──────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Graphiques rendus (Plotly)                                   │
│    Injecte CHARTS_INST["CNSS"]["all"]                           │
└────────────────────────────┬──────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Optionnel : apply branch fusion                              │
│    Si questionnaire_data.json a des réponses Q1                 │
└────────────────────────────┬──────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. Utilisateur clique ⚙️ Paramètres                             │
│    → questionnaire_modal.openModal("CNSS", ["R1","R2","R3"])    │
└────────────────────────────┬──────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Modal s'affiche avec Q1/Q2/Q4 pré-remplis                    │
│    Charge réponses depuis questionnaire_data.json               │
└────────────────────────────┬──────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. Utilisateur clique [Sauvegarder]                             │
│    → saveData() → PUT questionnaire_data.json                   │
│    → dispatchEvent('questionnaire-saved')                       │
└────────────────────────────┬──────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. branch_fusion.js listener                                     │
│    Charge Q1 data                                                │
│    Fusionne traces Plotly                                        │
│    Redessine graphiques (Plotly.react())                         │
│    ✓ Courbes doublons maintenant fusionnées                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist d'intégration

- [ ] Copier les 4 fichiers creés dans `10_output/`
- [ ] Ajouter les liens CSS/JS dans `<head>` du dashboard_regimes.html
- [ ] Ajouter le bouton ⚙️ après le dropdown institution
- [ ] Wrapper la fonction `updateInstitution()`
- [ ] Ajouter listener sur `questionnaire-saved`
- [ ] Tester:
  - [ ] Dropdown change → graphiques se mettent à jour
  - [ ] Clique ⚙️ Paramètres → modal s'ouvre
  - [ ] Remplir Q1 → Sauvegarder
  - [ ] Graphiques se fusionnent ✓
  - [ ] Recharger page → réponses persisted ✓

---

## 🔧 Points à adapter / vérifier

| Point | État | Action |
|-------|------|--------|
| Extraction dynamique régimes | ✓ | Déjà utilisé `window.REGIMES_PAR_INST` |
| Mapping branche → régime | ✓ | Fallback hardcodé + utilise `window.NOM_COURT` |
| Persistance questionnaire | ⚠️ | Actuellement local JSON; à adapter si backend |
| Q2 intégration | 🔲 | Q2 sauvegardé mais non appliqué aux graphiques |
| Q4 intégration | 🔲 | Q4 sauvegardé mais non appliqué aux chiffres |

---

## 📝 Prochaines étapes (après intégration)

1. **Tester avec données réelles CNSS/CNSSAP**
   - Vérifier la fusion des branches doublons

2. **Implémenter Q2 dans les graphiques**
   - Annoter les recettes/dépenses combinées
   - Montrer visuellement qui est agrégé avec qui

3. **Implémenter Q4 dans les graphiques**
   - Convertir les chiffres de bénéficiaires (enfant → ménage par ex)
   - Adapter les hover templates

4. **Persistance backend**
   - Créer endpoint `/api/questionnaire` (GET/PUT)
   - Remplacer la persistance JSON locale

5. **Export des réponses**
   - Permettre d'exporter Q1/Q2/Q4 en CSV/JSON pour audit
