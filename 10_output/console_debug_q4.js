// 🔍 SCRIPT DE DIAGNOSTIC Q4 — À coller dans la console du dashboard

console.clear();
console.log('=== DIAGNOSTIC Q4 ===\n');

// Étape 1 : Vérifier questionnaire
console.log('1️⃣ window.questionnaire existe ?', !!window.questionnaire);
if (window.questionnaire) {
  console.log('   Données chargées :', Object.keys(window.questionnaire.data || {}));
  console.log('   Q4 CNSS :', window.questionnaire.data?.CNSS?.Q4);
  console.log('   Q4_coefficients CNSS :', window.questionnaire.data?.CNSS?.Q4_coefficients);
}

// Étape 2 : Vérifier unitConverter
console.log('\n2️⃣ window.unitConverter existe ?', !!window.unitConverter);

// Étape 3 : Vérifier Plotly
console.log('\n3️⃣ Plotly existe ?', !!window.Plotly);

// Étape 4 : Inspecter les graphiques
const popContainer = document.getElementById('charts-institution-pop');
console.log('\n4️⃣ Conteneur charts-institution-pop trouvé ?', !!popContainer);

if (popContainer) {
  const plotlyDivs = popContainer.querySelectorAll('.plotly-graph-div');
  console.log('   Nombre de graphiques Plotly :', plotlyDivs.length);
  
  if (plotlyDivs.length > 0) {
    const firstDiv = plotlyDivs[0];
    console.log('\n   🔍 Premier graphique :');
    console.log('   - ID :', firstDiv.id);
    console.log('   - Nombre de traces :', firstDiv.data?.length || 0);
    
    if (firstDiv.data) {
      firstDiv.data.forEach((trace, i) => {
        console.log(`   - Trace ${i}:`, {
          name: trace.name,
          legendgroup: trace.legendgroup,
          x: trace.x,
          y: trace.y
        });
      });
    }
  }
}

// Étape 5 : Tester manuellement la conversion
console.log('\n5️⃣ TEST MANUEL DE CONVERSION');
if (window.unitConverter && window.questionnaire) {
  const q4Data = window.questionnaire.data?.CNSS?.Q4 || {};
  const q4Coefs = window.questionnaire.data?.CNSS?.Q4_coefficients || {};
  
  console.log('   Q4 data :', q4Data);
  console.log('   Q4 coefficients :', q4Coefs);
  
  if (Object.keys(q4Data).length > 0 && popContainer) {
    const plotlyDivs = popContainer.querySelectorAll('.plotly-graph-div');
    if (plotlyDivs.length > 0) {
      const graphId = plotlyDivs[0].id;
      console.log('   Tentative d\'application sur graphique :', graphId);
      
      // Appliquer Q4
      try {
        window.unitConverter.applyConversion(graphId, q4Data, q4Coefs);
        console.log('   ✅ Conversion appliquée sans erreur');
        
        // Vérifier si les valeurs ont changé
        const divAfter = document.getElementById(graphId);
        console.log('   Traces après conversion :', divAfter.data.map(t => ({
          name: t.name,
          y: t.y
        })));
      } catch (e) {
        console.error('   ❌ Erreur lors de la conversion :', e);
      }
    }
  } else {
    console.log('   ⚠️ Pas de données Q4 ou pas de graphiques');
  }
}

console.log('\n=== FIN DIAGNOSTIC ===');
