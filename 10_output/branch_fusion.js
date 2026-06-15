/**
 * Branch Fusion Module
 * 
 * Fusionne les courbes Plotly de branches qui partagent la même population,
 * selon les réponses du questionnaire Q1.
 * 
 * Flux:
 * 1. L'utilisateur sélectionne un régime via le dropdown
 * 2. Le questionnaire Q1 déclare si les branches sont empilables
 * 3. Ce module reprocess les données Plotly pour fusionner les branches identiques
 */

class BranchFusion {
  constructor(plotlyGlobalState = Plotly) {
    this.Plotly = plotlyGlobalState;
    this.traces = {};      // Cache des traces originales par graphID
    this.mergedTraces = {}; // Traces fusionnées par graphID
  }

  /**
   * Applique la fusion de branches à un graphique Plotly
   * @param {string} graphId - ID du div Plotly (ex: "7d4cf561-e2cc-47f3-afab-9acfd952d0ad")
   * @param {object} q1Data - Réponses Q1 du questionnaire
   *   Format: { "regime1__regime2": "true/false", ... }
   * @param {object} branchMapping - Mapping branche → liste de régimes
   *   Ex: { "Prestations familiales": ["CNSS_R1", "CNSS_R4"], ... }
   */
  applyBranchFusion(graphId, q1Data, branchMapping) {
    const plotDiv = document.getElementById(graphId);
    if (!plotDiv || !plotDiv.data) {
      console.warn(`[BranchFusion] Graphique ${graphId} non trouvé ou non chargé`);
      return;
    }

    // Charge ou cache les traces originales
    if (!this.traces[graphId]) {
      this.traces[graphId] = JSON.parse(JSON.stringify(plotDiv.data));
    }

    // Identifie les branches à fusionner
    const fusionGroups = this.identifyFusionGroups(q1Data, branchMapping);
    
    if (Object.keys(fusionGroups).length === 0) {
      // Pas de fusion nécessaire
      return;
    }

    // Fusionne les traces selon les groupes identifiés
    const newData = this.mergeTraces(this.traces[graphId], fusionGroups);
    
    // Redessine le graphique avec les données fusionnées
    this.Plotly.react(graphId, newData, plotDiv.layout, { responsive: true });
  }

  /**
   * Identifie les groupes de branches à fusionner basés sur Q1
   * @returns {object} ex: { "Prestations familiales + Risques prof": ["CNSS_R1", "CNSS_R2"], ... }
   */
  identifyFusionGroups(q1Data, branchMapping) {
    const groups = {};
    const processed = new Set();

    Object.entries(branchMapping).forEach(([branche, regimes]) => {
      if (processed.has(branche)) return;

      const fusionPartners = [];
      
      regimes.forEach((regime1) => {
        regimes.forEach((regime2) => {
          if (regime1 === regime2) return;
          
          // Vérifie Q1 : ces deux régimes partagent-ils la même population ?
          const key1 = `${regime1}__${regime2}`;
          const key2 = `${regime2}__${regime1}`;
          const shouldFuse = q1Data[key1] === 'true' || q1Data[key2] === 'true';
          
          if (shouldFuse && !fusionPartners.includes(regime2)) {
            fusionPartners.push(regime2);
          }
        });
      });

      if (fusionPartners.length > 0) {
        // Crée un groupe de fusion
        const groupKey = [branche, ...fusionPartners.map(r => 
          Object.keys(branchMapping).find(b => branchMapping[b].includes(r))
        )].join(' + ');
        
        groups[groupKey] = regimes.concat(fusionPartners);
        processed.add(branche);
        fusionPartners.forEach(p => {
          Object.entries(branchMapping).forEach(([k, v]) => {
            if (v.includes(p)) processed.add(k);
          });
        });
      }
    });

    return groups;
  }

  /**
   * Fusionne les traces Plotly selon les groupes identifiés
   * 
   * Stratégie:
   * - Les traces avec le même stackgroup et xaxis/yaxis sont **additionnées**
   * - La légende devient "Branche1 + Branche2"
   * - Les données (y) sont **sommées** année par année
   */
  mergeTraces(originalTraces, fusionGroups) {
    const newTraces = [];
    const processed = new Set();

    originalTraces.forEach((trace, idx) => {
      // Identifie le groupe de fusion de cette trace
      let traceGroup = null;
      for (const [groupKey, regimes] of Object.entries(fusionGroups)) {
        if (this.traceMatchesRegimes(trace, regimes)) {
          traceGroup = groupKey;
          break;
        }
      }

      if (!traceGroup) {
        // Pas de fusion pour cette trace
        newTraces.push(JSON.parse(JSON.stringify(trace)));
        return;
      }

      // Evite de traiter deux fois le même groupe
      if (processed.has(traceGroup)) {
        return;
      }

      // Trouve toutes les traces du même groupe
      const tracesInGroup = originalTraces.filter(t => 
        this.traceMatchesRegimes(t, fusionGroups[traceGroup]) &&
        t.xaxis === trace.xaxis && 
        t.yaxis === trace.yaxis &&
        t.stackgroup === (trace.stackgroup || undefined)
      );

      if (tracesInGroup.length === 0) return;

      // Fusionne les traces du groupe
      const mergedTrace = this.mergeTracesInGroup(tracesInGroup, traceGroup);
      newTraces.push(mergedTrace);
      
      processed.add(traceGroup);
    });

    return newTraces;
  }

  /**
   * Fusionne plusieurs traces en une seule
   * Additionne les valeurs y et crée une légende combinée
   */
  mergeTracesInGroup(tracesInGroup, groupLabel) {
    if (tracesInGroup.length === 0) return null;

    const firstTrace = JSON.parse(JSON.stringify(tracesInGroup[0]));
    
    // Fusion des labels
    const names = tracesInGroup
      .map(t => t.name)
      .filter((v, i, a) => a.indexOf(v) === i); // unique
    firstTrace.name = names.join(' + ');
    
    // Fusion des données (y)
    const merged_y = firstTrace.y.map((_, i) => {
      return tracesInGroup.reduce((sum, trace) => {
        const val = trace.y ? trace.y[i] : 0;
        return sum + (val || 0);
      }, 0);
    });
    firstTrace.y = merged_y;

    // Met à jour le hover template
    if (firstTrace.hovertemplate) {
      firstTrace.hovertemplate = firstTrace.hovertemplate.replace(
        tracesInGroup[0].name,
        firstTrace.name
      );
    }

    return firstTrace;
  }

  /**
   * Vérifie si une trace correspond aux régimes donnés
   */
  traceMatchesRegimes(trace, regimes) {
    const legendGroup = trace.legendgroup || '';
    return regimes.some(regime => legendGroup.includes(regime));
  }

  /**
   * Réinitialise un graphique à son état original
   */
  resetGraph(graphId) {
    const plotDiv = document.getElementById(graphId);
    if (!plotDiv || !this.traces[graphId]) return;
    
    this.Plotly.react(graphId, this.traces[graphId], plotDiv.layout, { responsive: true });
  }
}

// Instance globale
window.branchFusion = new BranchFusion(window.Plotly);

/**
 * Hook pour le questionnaire
 * À appeler après que l'utilisateur sauvegarde Q1
 */
window.addEventListener('questionnaire-saved', async (e) => {
  const { institution, regimes } = e.detail;
  
  // Charge les réponses Q1
  const q1Data = window.questionnaire.data[institution]?.Q1 || {};
  
  // Construit le mapping branche → régimes
  // ⚠️ À adapter selon comment les branches sont nommées dans CHARTS_INST
  const branchMapping = buildBranchMapping(institution, regimes);
  
  // Applique la fusion à tous les graphiques visibles
  document.querySelectorAll('.plotly-graph-div').forEach(div => {
    if (div.id) {
      window.branchFusion.applyBranchFusion(div.id, q1Data, branchMapping);
    }
  });
  
  console.log('✓ Fusion de branches appliquée');
});

/**
 * Construit le mapping branche → régimes à partir des données globales du dashboard
 * 
 * Utilise les données disponibles :
 * - REGIMES_PAR_INST : regimes par institution (depuis visualiser_regimes.py)
 * - NOM_COURT : mapping régime code → nom court (depuis visualiser_regimes.py)
 */
function buildBranchMapping(institution, regimes) {
  // Fallback mappings (pour le cas où NOM_COURT n'est pas disponible)
  const fallbackMappings = {
    'CNSS': {
      'Prestations familiales': ['CNSS_R1'],
      'Risques professionnels': ['CNSS_R2'],
      'Pension': ['CNSS_R3'],
      'Action sociale et sanitaire': ['CNSS_R4']
    },
    'CNSSAP': {
      'Régime de base': ['CNSSAP_R1'],
      'Réforme du transfert': ['CNSSAP_R2']
    }
  };
  
  // Essaie d'utiliser NOM_COURT si disponible (depuis visualiser_regimes.py)
  if (typeof window.NOM_COURT !== 'undefined') {
    const mapping = {};
    regimes.forEach((regime) => {
      const nomCourt = window.NOM_COURT[regime] || regime;
      if (!mapping[nomCourt]) {
        mapping[nomCourt] = [];
      }
      mapping[nomCourt].push(regime);
    });
    
    if (Object.keys(mapping).length > 0) {
      return mapping;
    }
  }
  
  return fallbackMappings[institution] || {};
}
