/**
 * INTÉGRATION QUESTIONNAIRE — Instructions pour dashboard_regimes.html
 * 
 * Ce fichier contient les snippets de code à ajouter/modifier dans le dashboard.
 * 
 * PRÉREQUIS:
 * - questionnaire_modal.js doit être chargé
 * - questionnaire_modal.css doit être chargé
 * - branch_fusion.js doit être chargé
 * - Plotly doit être disponible (window.Plotly)
 */

// ─────────────────────────────────────────────────────────────────────────────
// 1️⃣  À AJOUTER DANS <head> du HTML
// ─────────────────────────────────────────────────────────────────────────────

/*
<link rel="stylesheet" href="questionnaire_modal.css">

<script src="questionnaire_modal.js"></script>
<script src="branch_fusion.js"></script>
*/

// ─────────────────────────────────────────────────────────────────────────────
// 2️⃣  MODIFICATION DU DROPDOWN INSTITUTION (Tab 2)
// ─────────────────────────────────────────────────────────────────────────────

/*
SITUATION ACTUELLE:
  <select id="sel-institution" onchange="updateInstitution()">
    <option value="CNSS">CNSS</option>
    <option value="CNSSAP">CNSSAP</option>
  </select>

À MODIFIER:
  Ajouter le bouton ⚙️ Paramètres juste après le dropdown
*/

// Code à ajouter après le dropdown institution:
function initQuestionnaireButton() {
  const institutionSelect = document.getElementById('sel-institution');
  
  // Crée le bouton Paramètres
  const parametersBtn = document.createElement('button');
  parametersBtn.id = 'questionnaire-btn-institution';
  parametersBtn.className = 'questionnaire-btn';
  parametersBtn.textContent = '⚙️ Paramètres';
  parametersBtn.title = 'Configurer les règles d\'affichage pour cette institution';
  
  // Handler du bouton
  parametersBtn.addEventListener('click', () => {
    const institution = institutionSelect.value;
    
    // Récupère les régimes de cette institution
    const regimes = window.REGIMES_PAR_INST ? 
      window.REGIMES_PAR_INST[institution] || [] 
      : [];
    
    if (regimes.length === 0) {
      alert('Aucun régime trouvé pour cette institution');
      return;
    }
    
    // Ouvre le questionnaire modal
    if (window.questionnaire) {
      window.questionnaire.openModal(institution, regimes);
    } else {
      alert('Module questionnaire non chargé');
    }
  });
  
  // Insère le bouton après le dropdown
  institutionSelect.parentNode.insertBefore(
    parametersBtn, 
    institutionSelect.nextSibling
  );
}

// Appeler au chargement de la page (après que tous les éléments DOM soient prêts)
document.addEventListener('DOMContentLoaded', initQuestionnaireButton);

// ─────────────────────────────────────────────────────────────────────────────
// 3️⃣  HOOK DE FUSION DE BRANCHES (après que les graphiques soient rendus)
// ─────────────────────────────────────────────────────────────────────────────

/*
Après que updateInstitution() change les graphiques, on doit appliquer la fusion.
*/

// Wrapper de updateInstitution() pour ajouter la fusion
const originalUpdateInstitution = window.updateInstitution || (() => {});

window.updateInstitution = function() {
  // Exécute la fonction originale pour mettre à jour les graphiques
  originalUpdateInstitution.apply(this, arguments);
  
  // Puis applique la fusion de branches (si questionnaire rempli)
  setTimeout(() => {
    applyBranchFusionAfterRender();
  }, 500); // Délai pour que Plotly finisse de rendre
};

/**
 * Applique la fusion de branches après que les graphiques aient été rendus
 */
function applyBranchFusionAfterRender() {
  if (!window.branchFusion || !window.questionnaire) {
    return;
  }
  
  const institution = document.getElementById('sel-institution').value;
  const q1Data = window.questionnaire.data[institution]?.Q1 || {};
  
  // Si aucune réponse Q1, pas de fusion à faire
  if (Object.keys(q1Data).length === 0) {
    return;
  }
  
  // Récupère les régimes de cette institution
  const regimes = window.REGIMES_PAR_INST 
    ? window.REGIMES_PAR_INST[institution] || []
    : [];
  
  const branchMapping = buildBranchMapping(institution, regimes);
  
  // Applique la fusion à tous les graphiques Plotly
  document.querySelectorAll('.plotly-graph-div').forEach(div => {
    if (div.id) {
      window.branchFusion.applyBranchFusion(div.id, q1Data, branchMapping);
    }
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// 4️⃣  HOOK POUR QUAND L'UTILISATEUR SAUVEGARDE LE QUESTIONNAIRE
// ─────────────────────────────────────────────────────────────────────────────

/*
Cet événement est déjà déclenché par questionnaire_modal.js,
donc on n'a qu'à l'écouter ici.
*/

window.addEventListener('questionnaire-saved', (e) => {
  const { institution } = e.detail;
  
  // Re-applique la fusion de branches
  const q1Data = window.questionnaire.data[institution]?.Q1 || {};
  const regimes = window.REGIMES_PAR_INST 
    ? window.REGIMES_PAR_INST[institution] || []
    : [];
  
  const branchMapping = buildBranchMapping(institution, regimes);
  
  document.querySelectorAll('.plotly-graph-div').forEach(div => {
    if (div.id) {
      window.branchFusion.applyBranchFusion(div.id, q1Data, branchMapping);
    }
  });
  
  console.log('✓ Fusion de branches appliquée après save');
});

// ─────────────────────────────────────────────────────────────────────────────
// 5️⃣  ADAPTATION DE LA PERSISTENCE (questionnaire_data.json)
// ─────────────────────────────────────────────────────────────────────────────

/*
ACTUELLEMENT: questionnaire_modal.js fait un PUT sur questionnaire_data.json local

À FAIRE: Adapter pour utiliser l'API existante du dashboard
- Utiliser le pattern /api/dashboard-* comme les ODD decisions
- Ou persister en localStorage en tant que fallback
*/

// Modifier dans questionnaire_modal.js la méthode persistData():

async function persistDataViaApi() {
  try {
    // Option 1: Si endpoint /api/questionnaire existe
    const response = await fetch('/api/questionnaire', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(this.data)
    });

    if (!response.ok) {
      // Fallback: localStorage
      localStorage.setItem('QUESTIONNAIRE_DATA', JSON.stringify(this.data));
      console.log('Données sauvegardées en localStorage');
    }
  } catch (e) {
    // Fallback: localStorage
    localStorage.setItem('QUESTIONNAIRE_DATA', JSON.stringify(this.data));
    console.log('Fallback: données sauvegardées en localStorage');
  }
}

// Modifier la méthode loadData() pour charger depuis localStorage en fallback:

async function loadDataWithFallback() {
  try {
    // Essaie l'API d'abord
    const response = await fetch('/api/questionnaire');
    if (response.ok) {
      this.data = await response.json();
      return;
    }
  } catch (e) {
    // Ignore les erreurs réseau
  }
  
  // Fallback: localStorage
  const stored = localStorage.getItem('QUESTIONNAIRE_DATA');
  if (stored) {
    this.data = JSON.parse(stored);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// RÉSUMÉ DES ÉTAPES D'INTÉGRATION
// ─────────────────────────────────────────────────────────────────────────────

/*
1. Ajouter dans <head> du dashboard_regimes.html:
   - Link vers questionnaire_modal.css
   - Script questionnaire_modal.js
   - Script branch_fusion.js

2. Ajouter après le dropdown #sel-institution:
   - Code d'initialisation du bouton ⚙️

3. Wrapper la fonction updateInstitution():
   - Appeler la fusion de branches après rendu

4. Ajouter listener sur l'événement 'questionnaire-saved':
   - Re-applique la fusion avec nouvelles réponses

5. (Optional) Adapter persistence:
   - Créer endpoint /api/questionnaire si backend disponible
   - Sinon utiliser localStorage

TEST:
- Charger le dashboard
- Cliquer sur ⚙️ Paramètres
- Remplir Q1 (ex: "Prestations familiales" + "Risques prof" = Oui)
- Sauvegarder
- Les graphiques doivent se fusionner
*/
