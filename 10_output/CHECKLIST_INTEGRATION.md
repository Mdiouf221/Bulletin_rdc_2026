# ✅ CHECKLIST — Intégration Questionnaire Complète

## Étapes réalisées

### 1️⃣ Fichiers créés
- [x] `questionnaire_modal.js` (7.6 KB) — UI modal + persistance
- [x] `questionnaire_modal.css` (6.1 KB) — Styles complets
- [x] `branch_fusion.js` (8.5 KB) — Fusion des traces Plotly
- [x] `questionnaire_data.json` — Stockage des réponses
- [x] Documentation (`ARCHITECTURE_QUESTIONNAIRE.md`, `SYNTHESIS_FINAL.md`, `INTEGRATION_INSTRUCTIONS.js`)

**Localisation**: `10_output/`

### 2️⃣ Modifications du dashboard (visualiser_regimes.py)

**Ligne 3707-3708**: Ajout du CSS
```python
  <!-- Questionnaire Modal CSS -->
  <link rel="stylesheet" href="questionnaire_modal.css">
```

**Ligne 7409-7515**: Ajout des scripts JavaScript
```python
<!-- Questionnaire Modal Scripts -->
<script src="questionnaire_modal.js"></script>
<script src="branch_fusion.js"></script>

<!-- Integration Hooks -->
<script>
  // Initialisation du bouton ⚙️
  // Hook de fusion de branches
  // Listener pour 'questionnaire-saved'
</script>
```

---

## 🧪 Avant de tester

### Points de vérification

1. **Fichiers présents dans `10_output/`**
   ```
   ✓ questionnaire_modal.js
   ✓ questionnaire_modal.css
   ✓ branch_fusion.js
   ✓ questionnaire_data.json
   ```

2. **Serveur web configuré**
   - Les fichiers CSS/JS doivent être servis depuis `10_output/`
   - Path de base : `file:///10_output/` ou `http://localhost:8765/10_output/`

3. **Plotly.js disponible**
   - `window.Plotly` doit être défini (déjà in-lined dans le HTML)

4. **Objets globaux créés**
   - `window.REGIMES_PAR_INST` (depuis visualiser_regimes.py)
   - `window.NOM_COURT` (depuis visualiser_regimes.py)
   - `window.CHARTS_INST` (depuis visualiser_regimes.py)

---

## 🚀 Procédure de test

### Étape 1 : Régénérer le dashboard
```bash
cd 09_scripts
python visualiser_regimes.py
```
→ Génère `10_output/dashboard_regimes.html` avec intégration

### Étape 2 : Servir les fichiers
```bash
# Option A: Serveur local simple
cd 10_output
python -m http.server 8765

# Option B: Depuis la racine du projet
python 09_scripts/serveur_preview.py
```

### Étape 3 : Ouvrir le dashboard
```
http://localhost:8765/dashboard_regimes.html
```

### Étape 4 : Tester le workflow
1. **Sélectionner une institution** : CNSS
2. **Cliquer ⚙️ Paramètres** (à côté du dropdown)
   - Doit ouvrir le modal
   - Q1/Q2/Q4 doivent être vides (première visite)
3. **Remplir Q1** : Cocher "Prestations familiales partage cotisants avec Risques professionnels" = ✓
4. **Sauvegarder**
   - Message "✓ Questionnaire sauvegardé"
   - Modal se ferme
   - Graphiques se re-calculent
5. **Vérifier la fusion**
   - Graphique "Par institution" > cotisants
   - Les courbes "Prestations familiales" et "Risques professionnels" doivent être fusionnées
   - Légende devient "Prestations familiales + Risques professionnels"

---

## 🔧 Dépannage

### Problème : Bouton ⚙️ n'apparaît pas
**Solution**: 
- Vérifier que `#sel-institution` existe dans le HTML
- Vérifier que `questionnaire_modal.js` s'est chargé (Console → pas d'erreur)
- Vérifier que `initQuestionnaireButton()` a été appelé

### Problème : Modal n'ouvre pas au clic
**Solution**:
- Vérifier `window.questionnaire` existe (Console: `console.log(window.questionnaire)`)
- Vérifier `window.REGIMES_PAR_INST` rempli (Console: `console.log(window.REGIMES_PAR_INST)`)

### Problème : Graphiques ne se fusionnent pas après save
**Solution**:
- Vérifier que `branch_fusion.js` s'est chargé
- Vérifier que `window.branchFusion` existe
- Vérifier que `questionnaire_data.json` contient les réponses sauvegardées
- Vérifier que les `.plotly-graph-div` existent (Console: `document.querySelectorAll('.plotly-graph-div')`)

### Problème : Erreur "Q1 data undefined"
**Solution**:
- Vérifier que les réponses sont bien persistées dans `questionnaire_data.json`
- Vérifier que le mapping branche → régime est correct dans `buildBranchMapping()`

---

## 📊 Données de test (CNSS 2022)

Pour tester rapidement, utiliser ces paramètres Q1 :

```json
{
  "CNSS": {
    "Q1": {
      "CNSS_R1__CNSS_R2": "true",   // Prestations fam = Risques prof
      "CNSS_R1__CNSS_R3": "true",   // Prestations fam = Pension
      "CNSS_R2__CNSS_R3": "true"    // Risques prof = Pension
    }
  }
}
```

**Résultat attendu** : 
- Les 3 branches (R1, R2, R3) doivent être fusionnées en 1 courbe avec label « Prestations familiales + Risques professionnels + Pension »
- Valeur unique : 613,761 cotisants (au lieu de 1,841,283)

---

## 📝 Notes importantes

1. **Persistance des données**
   - Actuellement : `questionnaire_data.json` local
   - À adapter : Si backend disponible, créer endpoint `/api/questionnaire`

2. **Q2 et Q4 non appliquées**
   - Q1 ✓ Fusion des branches appliquée
   - Q2 🔲 Sauvegardé mais non appliqué aux graphiques (future phase)
   - Q4 🔲 Sauvegardé mais non appliqué (future phase)

3. **Performance**
   - Fusion re-calculée à chaque `updateInstitution()` change
   - Délai de 500ms pour que Plotly finisse de rendre
   - OK pour instances < 20 graphiques

4. **Navigateurs supportés**
   - Chrome/Edge/Firefox (ES6 minimal)
   - Safari (testé avec polyfill `??` optionnel )
   - IE 11 non supporté

---

## ✓ Sign-off

Intégration complète prête pour test.

**Créé** : 2026-06-15  
**Intégré dans** : `visualiser_regimes.py` (v1)  
**État** : ✅ Prêt pour test
