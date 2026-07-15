/**
 * Branch Fusion Module
 * 
 * Fusionne les courbes Plotly de régimes qui portent sur les mêmes personnes,
 * selon les réponses Q1 (cotisants) et Q1b (bénéficiaires).
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
   * @param {object} branchMapping - Mapping libellé → liste de codes régimes
   */
  applyBranchFusion(graphId, q1Data, branchMapping, q1bData = {}) {
    const plotDiv = document.getElementById(graphId);
    if (!plotDiv || !plotDiv.data) {
      console.warn(`[BranchFusion] Graphique ${graphId} non trouvé ou non chargé`);
      return;
    }

    // Charge ou cache les traces originales
    if (!this.traces[graphId]) {
      this.traces[graphId] = JSON.parse(JSON.stringify(plotDiv.data));
    }

    const cotisantGroups = this.identifyFusionGroups(q1Data, branchMapping);
    const beneficiaireGroups = this.identifyFusionGroups(q1bData, branchMapping);
    let newData = JSON.parse(JSON.stringify(this.traces[graphId]));
    newData.forEach(trace => {
      const axis = trace.yaxis || 'y';
      if (axis === 'y' || axis === 'y2') {
        delete trace.stackgroup;
        trace.fill = 'none';
      }
    });
    newData = this.mergeTraces(newData, cotisantGroups, 'y');
    newData = this.mergeTraces(newData, beneficiaireGroups, 'y2');
    
    // Recalculer les axes à partir des seules séries visibles.
    const layout = JSON.parse(JSON.stringify(plotDiv.layout || {}));
    ['yaxis', 'yaxis2'].forEach(axis => {
      if (!layout[axis]) layout[axis] = {};
      delete layout[axis].range;
      layout[axis].autorange = true;
      layout[axis].rangemode = 'tozero';
    });
    this.Plotly.react(graphId, newData, layout, { responsive: true });
  }

  /**
   * Identifie les groupes de régimes à fusionner à partir de Q1.
   *
   * Les clés Q1 ont le format "<code1>__<code2>" : "true"|"false".
   * Les composantes connexes sont construites sans hypothèse sur les codes.
   *
   * @param {object} q1Data - Paires de codes régimes qualifiées
   * @param {object} branchMapping - Libellés dynamiques des régimes
   *   (utilisé uniquement pour construire le libellé du groupe)
   * @returns {object} { "label": ["code1", "code2"], ... }
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
  mergeTraces(originalTraces, fusionGroups, targetAxis) {
    if (Object.keys(fusionGroups).length === 0) {
      return JSON.parse(JSON.stringify(originalTraces));
    }

    const newTraces = [];
    const processed = new Set();

    originalTraces.forEach((trace) => {
      const traceAxis = trace.yaxis || 'y';
      if (traceAxis !== targetAxis) {
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

      // Trouve toutes les traces du même groupe sur le même sous-graphique.
      const tracesInGroup = originalTraces.filter(t => 
        (t.yaxis || 'y') === targetAxis &&
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
   * Les régimes cochés partagent les MÊMES personnes. On ne doit PAS additionner :
   * on prend la valeur représentative maximale pour chaque année.
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
    delete firstTrace.stackgroup;
    firstTrace.fill = 'none';

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
  const mapping = {};
  regimes.forEach((regime) => {
    const label = window.NOM_COURT?.[regime] || regime;
    if (!mapping[label]) {
      mapping[label] = [];
    }
    mapping[label].push(regime);
  });
  return mapping;
}
