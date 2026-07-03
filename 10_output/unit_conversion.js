/**
 * Unit Conversion Module
 * 
 * Convertit les valeurs de bénéficiaires selon les coefficients Q4
 * pour permettre la comparaison entre régimes utilisant différentes unités.
 * 
 * Exemple :
 * - CNSS R1 compte en "Enfants" → pas de conversion
 * - CNSS R4 compte en "Ménages" → multiplie par coefficient (ex: 2.5 enfants/ménage)
 * - CNSSAP R2 compte en "Personnes" → multiplie par coefficient (ex: 0.4 enfant/personne)
 */

class UnitConverter {
  constructor() {
    this.Plotly = window.Plotly || null;
    this.originalTraces = {}; // Cache des traces originales par graphId
  }

  /**
   * Applique la conversion Q4 à un graphique Plotly
   * 
   * @param {string} graphId - ID du div Plotly
   * @param {object} q4Data - Unités par régime {regime: "enfant|ménage|personne|autre"}
   * @param {object} q4Coefficients - Coefficients par régime et année
   *   Format: {regime: {year: {value: 2.5, source: "INS DRC 2021"}}}
   */
  applyConversion(graphId, q4Data, q4Coefficients) {
    if (!this.Plotly) {
      console.warn('[UnitConverter] Plotly non disponible');
      return;
    }

    const plotDiv = document.getElementById(graphId);
    if (!plotDiv || !plotDiv.data) {
      console.warn(`[UnitConverter] Graphique ${graphId} non trouvé`);
      return;
    }

    // Cache les traces originales
    if (!this.originalTraces[graphId]) {
      this.originalTraces[graphId] = JSON.parse(JSON.stringify(plotDiv.data));
    }

    // Identifier les traces à convertir
    const convertedData = this.convertTraces(
      this.originalTraces[graphId],
      q4Data,
      q4Coefficients
    );

    // Redessine le graphique
    this.Plotly.react(graphId, convertedData, plotDiv.layout, { responsive: true });
    
    console.log(`✓ Conversion Q4 appliquée au graphique ${graphId}`);
  }

  /**
   * Convertit les traces Plotly selon Q4
   * 
   * @param {array} traces - Traces Plotly originales
   * @param {object} q4Data - Unités par régime
   * @param {object} q4Coefficients - Coefficients de conversion
   * @returns {array} - Traces converties
   */
  convertTraces(traces, q4Data, q4Coefficients) {
    return traces.map(trace => {
      const traceCopy = JSON.parse(JSON.stringify(trace));
      
      // Identifier le régime de cette trace (via legendgroup ou name)
      const regime = this.extractRegimeFromTrace(trace);
      if (!regime) return traceCopy;

      // Récupérer l'unité du régime
      const unit = q4Data[regime];
      if (!unit || unit === 'enfant') {
        // Pas de conversion nécessaire
        return traceCopy;
      }

      // Récupérer les coefficients pour ce régime
      const coefficients = q4Coefficients[regime];
      if (!coefficients || Object.keys(coefficients).length === 0) {
        console.warn(`[UnitConverter] Pas de coefficients pour ${regime}`);
        return traceCopy;
      }

      // Convertir les valeurs y selon les années x
      if (traceCopy.x && traceCopy.y && Array.isArray(traceCopy.x) && Array.isArray(traceCopy.y)) {
        traceCopy.y = traceCopy.y.map((yValue, i) => {
          if (yValue === null || yValue === undefined) return yValue;
          
          const year = traceCopy.x[i];
          const coefData = coefficients[year] || coefficients['default'];
          
          if (!coefData || !coefData.value) {
            // Pas de coefficient pour cette année
            return yValue;
          }
          
          return yValue * coefData.value;
        });

        // Ajouter un indicateur dans le nom de la trace
        const unitIcon = this.getUnitIcon(unit);
        if (!traceCopy.name.includes(unitIcon)) {
          traceCopy.name = `${traceCopy.name} ${unitIcon}`;
        }

        // Ajouter info dans le hover
        if (traceCopy.hovertemplate) {
          traceCopy.hovertemplate = traceCopy.hovertemplate.replace(
            '</b>',
            ` (converti)<br><i>Unité: ${unit}</i></b>`
          );
        }
      }

      return traceCopy;
    });
  }

  /**
   * Extrait le code régime d'une trace Plotly
   * 
   * @param {object} trace - Trace Plotly
   * @returns {string|null} - Code régime (ex: "CNSS_R4")
   */
  extractRegimeFromTrace(trace) {
    // Essayer legendgroup (prioritaire)
    if (trace.legendgroup) {
      return trace.legendgroup;
    }

    // Essayer name (format: "Nom Régime — Branche")
    if (trace.name) {
      const match = trace.name.match(/^([A-Z_]+_R\d+)/);
      if (match) return match[1];
    }

    return null;
  }

  /**
   * Retourne l'icône correspondant à une unité
   * 
   * @param {string} unit - "enfant", "ménage", "personne", "autre"
   * @returns {string} - Icône emoji
   */
  getUnitIcon(unit) {
    const icons = {
      'enfant': '🧒',
      'ménage': '🏠',
      'menage': '🏠',
      'personne': '👤',
      'autre': '❓'
    };
    return icons[unit.toLowerCase()] || '📊';
  }

  /**
   * Convertit une valeur individuelle
   * (utile pour les tooltips ou calculs ponctuels)
   * 
   * @param {number} value - Valeur à convertir
   * @param {number} year - Année
   * @param {object} coefficients - Coefficients du régime {year: {value, source}}
   * @returns {number} - Valeur convertie
   */
  convertValue(value, year, coefficients) {
    if (!value || !coefficients) return value;
    
    const coefData = coefficients[year] || coefficients['default'];
    if (!coefData || !coefData.value) return value;
    
    return value * coefData.value;
  }

  /**
   * Réinitialise un graphique à ses valeurs originales
   * 
   * @param {string} graphId - ID du div Plotly
   */
  resetGraph(graphId) {
    if (!this.Plotly) return;

    const plotDiv = document.getElementById(graphId);
    if (!plotDiv) return;

    const originalData = this.originalTraces[graphId];
    if (!originalData) {
      console.warn(`[UnitConverter] Pas de données originales pour ${graphId}`);
      return;
    }

    this.Plotly.react(graphId, originalData, plotDiv.layout, { responsive: true });
    console.log(`✓ Graphique ${graphId} réinitialisé aux valeurs originales`);
  }

  /**
   * Vide le cache des traces originales
   */
  clearCache() {
    this.originalTraces = {};
    console.log('✓ Cache UnitConverter vidé');
  }
}

// Export global
window.UnitConverter = UnitConverter;
window.unitConverter = new UnitConverter();
