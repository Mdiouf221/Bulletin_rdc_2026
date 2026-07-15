/**
 * Branch Fusion Module
 * 
 * Fusionne les courbes Plotly de branches qui partagent la même population,
 * selon les réponses du questionnaire Q1.
 * 
 * Flux:
 * 1. L'utilisateur sélectionne un régime via le dropdown
 * 2. Le questionnaire Q1 déclare si les branches portent sur les mêmes cotisants
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
      // Restaurer les traces d'origine si une fusion précédemment active a été retirée.
      this.Plotly.react(
        graphId,
        JSON.parse(JSON.stringify(this.traces[graphId])),
        plotDiv.layout,
        { responsive: true }
      );
      return;
    }

    // Fusionne les traces selon les groupes identifiés
    const newData = this.mergeTraces(this.traces[graphId], fusionGroups);
    
    // Redessine le graphique avec les données fusionnées
    this.Plotly.react(graphId, newData, plotDiv.layout, { responsive: true });
  }

  /**
   * Identifie les groupes de régimes à fusionner à partir de Q1.
   *
   * Les clés Q1 ont le format "CNSS_R1__CNSS_R2" : "true"|"false".
   * On construit les composantes connexes (union-find) : si R1↔R2 et R1↔R3
   * sont tous deux "true", alors {R1, R2, R3} forment un seul groupe.
   *
   * @param {object} q1Data   - { "CNSS_R1__CNSS_R2": "true", ... }
   * @param {object} branchMapping - { "Prestations familiales": ["CNSS_R1"], ... }
   *   (utilisé uniquement pour construire le libellé du groupe)
   * @returns {object} { "label": ["CNSS_R1", "CNSS_R2", "CNSS_R3"], ... }
   */
  identifyFusionGroups(q1Data, branchMapping) {
    // 1. Collecter toutes les paires cochées
    const edges = [];
    Object.entries(q1Data).forEach(([key, val]) => {
      if (val !== 'true') return;
      const parts = key.split('__');
      if (parts.length === 2) edges.push([parts[0], parts[1]]);
    });

    if (edges.length === 0) return {};

    // 2. Union-Find pour construire les composantes connexes
    const parent = {};
    const find = (x) => {
      if (parent[x] === undefined) parent[x] = x;
      if (parent[x] !== x) parent[x] = find(parent[x]);
      return parent[x];
    };
    const union = (a, b) => { parent[find(a)] = find(b); };

    edges.forEach(([a, b]) => union(a, b));

    // 3. Regrouper les régimes par composante
    const components = {};
    [...new Set(edges.flat())].forEach(regime => {
      const root = find(regime);
      if (!components[root]) components[root] = [];
      if (!components[root].includes(regime)) components[root].push(regime);
    });

    // 4. Ne garder que les composantes de taille > 1 (fusion réelle)
    const groups = {};
    Object.values(components).forEach(regimes => {
      if (regimes.length < 2) return;

      // Construire le libellé à partir de branchMapping ou NOM_COURT
      const nomMapping = window.NOM_COURT || {};
      const label = regimes
        .map(r => {
          // Chercher le nom de branche dans branchMapping
          const branch = Object.keys(branchMapping).find(b => branchMapping[b].includes(r));
          return branch || nomMapping[r] || r;
        })
        .join(' + ');

      groups[label] = regimes;
    });

    return groups;
  }

  /**
   * Fusionne les traces Plotly selon les groupes identifiés
   * 
   * Stratégie:
   * - Les traces avec le même stackgroup et xaxis/yaxis sont fusionnées
   * - La légende devient "Branche1 + Branche2"
   * - La valeur représentative est le maximum pour chaque année
   */
  mergeTraces(originalTraces, fusionGroups) {
    const newTraces = [];
    const processed = new Set();

    originalTraces.forEach((trace, idx) => {
      // Q1 ne s'applique qu'aux cotisants (col 1, yaxis par défaut).
      // Les traces bénéficiaires (col 2, yaxis="y2") sont laissées intactes.
      const isCotisantsAxis = !trace.yaxis || trace.yaxis === 'y';
      if (!isCotisantsAxis) {
        newTraces.push(JSON.parse(JSON.stringify(trace)));
        return;
      }

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

      // Trouve toutes les traces du même groupe (cotisants uniquement)
      const tracesInGroup = originalTraces.filter(t => 
        (!t.yaxis || t.yaxis === 'y') &&
        this.traceMatchesRegimes(t, fusionGroups[traceGroup]) &&
        t.xaxis === trace.xaxis && 
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
   * Fusionne plusieurs traces en une seule.
   *
   * Stratégie Q1 — population PARTAGÉE :
   * Les branches cochées partagent les MÊMES personnes (ex. CNSS : 613 761 cotisants
   * apparaissent dans 3 branches). On ne doit PAS additionner : on prend la valeur
   * représentative (max sur chaque point, qui correspond au chiffre réel).
   *
   * On désactive également stackgroup pour que la trace fusionnée ne s'empile pas
   * avec elle-même.
   */
  mergeTracesInGroup(tracesInGroup, groupLabel) {
    if (tracesInGroup.length === 0) return null;

    const firstTrace = JSON.parse(JSON.stringify(tracesInGroup[0]));

    // Fusion des labels (noms uniques)
    const names = tracesInGroup
      .map(t => t.name)
      .filter((v, i, a) => a.indexOf(v) === i);
    firstTrace.name = names.join(' + ');

    // Aligner les séries sur les années avant de prendre la valeur représentative.
    const allYears = [];
    tracesInGroup.forEach(trace => {
      (trace.x || []).forEach(year => {
        if (!allYears.includes(year)) allYears.push(year);
      });
    });
    allYears.sort((a, b) => String(a).localeCompare(String(b), undefined, { numeric: true }));
    firstTrace.x = allYears;
    firstTrace.y = allYears.map(year => {
      const vals = tracesInGroup
        .map(trace => {
          const index = (trace.x || []).indexOf(year);
          return index >= 0 && trace.y && trace.y[index] != null ? trace.y[index] : null;
        })
        .filter(value => value !== null);
      return vals.length > 0 ? Math.max(...vals) : null;
    });

    // Mettre à jour le hover template
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
    return regimes.includes(legendGroup);
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
