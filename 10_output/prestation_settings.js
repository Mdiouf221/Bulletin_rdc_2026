/**
 * Prestation Settings Modal — Qualification des prestations
 * Version 2 — déduplication séparée cotisants (A1) / bénéficiaires (A2)
 *
 * Équivalent, au niveau prestation, du bouton « Paramètres » de l'onglet
 * « Par institution » (questionnaire_modal.js). Gère trois familles de
 * corrections d'affichage, sans modifier les données ESS sources :
 *
 *   A — Déduplication des bénéficiaires entre prestations d'un même régime
 *       (prestations qui couvrent la même population : évite le double comptage).
 *   B — Unité de compte des bénéficiaires par prestation + coefficients de
 *       conversion (vers « enfant ») par année.
 *   C — Inclusion / exclusion d'une prestation de l'affichage et des agrégats.
 *
 * Persistance via /api/prestation-settings → 10_output/prestation_settings.json
 * Structure : { INSTITUTION: { REGIME: { dedup:{}, unit:{}, coefficients:{}, exclude:{} } } }
 */

class PrestationSettings {
  constructor(apiUrl = '/api/prestation-settings') {
    this.apiUrl = apiUrl;
    this.data = {};
    this.currentInstitution = null;
    this.currentRegime = null;
    this.currentPrestations = [];
    this.loadData();
  }

  /** Charge les données depuis l'API serveur. */
  async loadData() {
    try {
      const response = await fetch(this.apiUrl);
      if (response.ok) {
        this.data = await response.json();
      }
    } catch (e) {
      console.log('Prestation settings : impossible de charger les données', e);
      this.data = {};
    }
  }

  /** Garantit l'existence de la structure data[inst][regime]. */
  ensureNode(inst, regime) {
    if (!this.data[inst]) this.data[inst] = {};
    if (!this.data[inst][regime]) {
      this.data[inst][regime] = {
        dedup_cotisants: {}, dedup_beneficiaires: {},
        finance_recettes: {}, finance_depenses: {},
        unit: {}, coefficients: {}, exclude: {}
      };
    }
    const node = this.data[inst][regime];
    // Migration douce : ancien champ unique `dedup` = bénéficiaires partagés.
    if (node.dedup && !node.dedup_beneficiaires) {
      node.dedup_beneficiaires = node.dedup;
    }
    delete node.dedup;
    node.dedup_cotisants = node.dedup_cotisants || {};
    node.dedup_beneficiaires = node.dedup_beneficiaires || {};
    node.finance_recettes = node.finance_recettes || {};
    node.finance_depenses = node.finance_depenses || {};
    node.unit = node.unit || {};
    node.coefficients = node.coefficients || {};
    node.exclude = node.exclude || {};
    return node;
  }

  /** Libellé court éventuel d'un régime. */
  regimeLabel(regime) {
    return window.NOM_COURT ? (window.NOM_COURT[regime] || regime) : regime;
  }

  /** Récupère les années ESS disponibles pour une prestation. */
  getPrestationYears(inst, regime, prest) {
    try {
      const meta = window.PRESTATION_META
        && window.PRESTATION_META[inst]
        && window.PRESTATION_META[inst][regime]
        && window.PRESTATION_META[inst][regime][prest];
      if (meta && Array.isArray(meta.ess_years)) return meta.ess_years;
    } catch (e) { /* ignore */ }
    return [];
  }

  /** Ouvre le modal avec les 3 sections (A, B, C). */
  openModal(inst, regime, prestations) {
    this.currentInstitution = inst;
    this.currentRegime = regime;
    this.currentPrestations = Array.isArray(prestations) ? prestations.slice() : [];
    this.ensureNode(inst, regime);

    const backdrop = document.createElement('div');
    backdrop.className = 'questionnaire-backdrop';
    backdrop.onclick = () => this.closeModal();

    const modal = document.createElement('div');
    modal.className = 'questionnaire-modal';
    modal.onclick = (e) => e.stopPropagation();

    const header = document.createElement('div');
    header.className = 'questionnaire-header';
    header.innerHTML = `
      <h2>Paramètres des prestations — ${inst} / ${this.regimeLabel(regime)}</h2>
      <button class="questionnaire-close" onclick="document.querySelector('.questionnaire-backdrop').remove()">×</button>
    `;

    const content = document.createElement('div');
    content.className = 'questionnaire-content';

    if (this.currentPrestations.length === 0) {
      const empty = document.createElement('p');
      empty.textContent = 'Aucune prestation disponible pour ce régime.';
      content.appendChild(empty);
    } else {
      content.appendChild(this.buildDedupSection(inst, regime, this.currentPrestations, 'cotisants'));
      content.appendChild(this.buildDedupSection(inst, regime, this.currentPrestations, 'beneficiaires'));
      content.appendChild(this.buildFinanceSection(inst, regime, this.currentPrestations));
      content.appendChild(this.buildUnitSection(inst, regime, this.currentPrestations));
      content.appendChild(this.buildExclusionSection(inst, regime, this.currentPrestations));
    }

    const footer = document.createElement('div');
    footer.className = 'questionnaire-footer';

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn-cancel';
    cancelBtn.textContent = 'Annuler';
    cancelBtn.addEventListener('click', () => this.closeModal());

    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn-save';
    saveBtn.textContent = 'Sauvegarder';
    saveBtn.addEventListener('click', () => this.saveData(inst, regime));

    footer.appendChild(cancelBtn);
    footer.appendChild(saveBtn);

    modal.appendChild(header);
    modal.appendChild(content);
    modal.appendChild(footer);
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
  }

  /**
   * Section A — Déduplication d'une population entre prestations.
   * `kind` = 'cotisants' ou 'beneficiaires'. Matrice symétrique : cocher
   * (P1, P2) déclare qu'elles partagent la même population.
   */
  buildDedupSection(inst, regime, prestations, kind) {
    const isCot = kind === 'cotisants';
    const nodeKey = isCot ? 'dedup_cotisants' : 'dedup_beneficiaires';
    const cbName = isCot ? 'ps_dedup_cot_pair' : 'ps_dedup_ben_pair';
    const idPrefix = isCot ? 'ps_dedupcot' : 'ps_dedupben';
    const legendTxt = isCot
      ? 'A1 — Cotisants partagés entre prestations'
      : 'A2 — Bénéficiaires partagés entre prestations';
    const descTxt = isCot
      ? "Cocher les couples de prestations alimentées par les mêmes cotisants actifs (une même personne cotise pour plusieurs prestations). Les cotisants seront dédupliqués dans le graphique « Cotisants actifs »."
      : "Cocher les couples de prestations qui servent les mêmes bénéficiaires (une même personne perçoit plusieurs prestations). Les bénéficiaires seront dédupliqués dans le graphique « Bénéficiaires ».";

    const node = this.ensureNode(inst, regime);
    const matrix = node[nodeKey] || {};
    const section = document.createElement('fieldset');
    section.className = 'questionnaire-section';
    section.innerHTML = `<legend>${legendTxt}</legend>`;

    const desc = document.createElement('p');
    desc.textContent = descTxt;
    section.appendChild(desc);

    const wrap = document.createElement('div');
    wrap.style.overflowX = 'auto';

    const table = document.createElement('table');
    table.className = 'questionnaire-matrix';

    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = '<th></th>';
    prestations.forEach(p => {
      const th = document.createElement('th');
      th.textContent = p;
      th.title = p;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    prestations.forEach((p1, i) => {
      const row = document.createElement('tr');
      const rowHeader = document.createElement('th');
      rowHeader.textContent = p1;
      rowHeader.title = p1;
      row.appendChild(rowHeader);

      prestations.forEach((p2, j) => {
        const td = document.createElement('td');
        if (i === j) {
          td.textContent = '—';
          td.style.backgroundColor = '#f0f0f0';
        } else {
          const checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.name = cbName;
          checkbox.id = `${idPrefix}_${i}__${j}`;
          checkbox.dataset.prest1 = p1;
          checkbox.dataset.prest2 = p2;

          const stored = matrix[`${p1}__${p2}`];
          if (stored) checkbox.checked = stored === 'true';

          checkbox.addEventListener('change', () => {
            const mirror = document.getElementById(`${idPrefix}_${j}__${i}`);
            if (mirror) mirror.checked = checkbox.checked;
          });

          td.appendChild(checkbox);
        }
        row.appendChild(td);
      });
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    section.appendChild(wrap);
    return section;
  }

  /**
   * Section D — Agrégation des recettes/dépenses entre prestations.
   * Réplique la logique de la question Q2 de l'onglet « Par institution ».
   * Pour chaque prestation, déclarer avec quelles autres prestations ses
   * recettes et/ou ses dépenses ont été combinées (même montant reporté).
   * Les dépenses ainsi combinées sont fusionnées dans le graphique
   * « Dépenses par prestation » (évite l'empilement du même montant régime).
   * Les recettes sont stockées (pas de graphique recettes par prestation
   * pour l'instant).
   */
  buildFinanceSection(inst, regime, prestations) {
    const node = this.ensureNode(inst, regime);
    const section = document.createElement('fieldset');
    section.className = 'questionnaire-section';
    section.innerHTML = '<legend>D — Agrégation des recettes/dépenses</legend>';

    const desc = document.createElement('p');
    desc.textContent = "Pour chaque prestation, indiquer si ses recettes et/ou ses dépenses ont été combinées avec d'autres prestations (même montant reporté). Les dépenses combinées sont fusionnées dans le graphique « Dépenses par prestation » (montant affiché une seule fois, la légende indiquant les prestations regroupées). Les recettes combinées sont enregistrées mais restent sans effet visuel : aucun graphique de recettes par prestation n'existe pour l'instant.";
    section.appendChild(desc);

    const wrap = document.createElement('div');
    wrap.style.overflowX = 'auto';

    const table = document.createElement('table');
    table.className = 'questionnaire-table';

    const thead = document.createElement('thead');
    thead.innerHTML = `
      <tr>
        <th>Prestation</th>
        <th>Recettes combinées avec</th>
        <th>Dépenses combinées avec</th>
      </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    prestations.forEach((prest, idx) => {
      const row = document.createElement('tr');

      const nameCell = document.createElement('td');
      nameCell.textContent = prest;
      nameCell.title = prest;
      nameCell.style.fontWeight = 'bold';
      row.appendChild(nameCell);

      const recCell = document.createElement('td');
      recCell.appendChild(this.buildFinanceMultiCheckbox(
        prestations, prest, idx, 'recettes', node.finance_recettes || {}));
      row.appendChild(recCell);

      const depCell = document.createElement('td');
      depCell.appendChild(this.buildFinanceMultiCheckbox(
        prestations, prest, idx, 'depenses', node.finance_depenses || {}));
      row.appendChild(depCell);

      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);
    section.appendChild(wrap);
    return section;
  }

  /**
   * Groupe de cases à cocher multi-sélection pour la section D.
   * `kind` = 'recettes' ou 'depenses'. `stored` = { prest: [autres...] }.
   */
  buildFinanceMultiCheckbox(prestations, currentPrest, idx, kind, stored) {
    const container = document.createElement('div');
    container.className = 'questionnaire-multi-checkbox';
    const cbName = `ps_fin_${kind}_${idx}`;
    const storedList = stored[currentPrest] || [];

    prestations.forEach((other) => {
      if (other === currentPrest) return;
      const label = document.createElement('label');
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.name = cbName;
      checkbox.value = other;
      checkbox.dataset.prest = currentPrest;
      checkbox.dataset.kind = kind;
      if (storedList.indexOf(other) !== -1) checkbox.checked = true;

      label.appendChild(checkbox);
      label.appendChild(document.createTextNode(other));
      container.appendChild(label);
    });

    return container;
  }

  /**
   * Section B — Unité de compte des bénéficiaires par prestation
   * + coefficients de conversion (vers « enfant ») par année.
   */
  buildUnitSection(inst, regime, prestations) {
    const node = this.ensureNode(inst, regime);
    const section = document.createElement('fieldset');
    section.className = 'questionnaire-section';
    section.innerHTML = '<legend>B — Unité de compte des bénéficiaires</legend>';

    const desc = document.createElement('p');
    desc.textContent = "Pour chaque prestation, indiquer l'unité de compte des bénéficiaires. Si l'unité n'est pas « Enfant », renseigner les coefficients de conversion par année.";
    section.appendChild(desc);

    const container = document.createElement('div');
    container.className = 'questionnaire-q4-container';

    prestations.forEach((prest, idx) => {
      const group = document.createElement('div');
      group.className = 'questionnaire-q4-group';

      const label = document.createElement('label');
      label.innerHTML = `<strong>${this.escapeHtml(prest)}</strong>`;
      group.appendChild(label);

      const options = ['Enfant', 'Ménage', 'Personne', 'Autre'];
      const storedUnit = node.unit[prest];
      options.forEach((opt) => {
        const radioLabel = document.createElement('label');
        radioLabel.className = 'questionnaire-radio';

        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = `ps_unit_${idx}`;
        radio.value = opt.toLowerCase();
        radio.dataset.prest = prest;
        if (storedUnit === opt.toLowerCase()) radio.checked = true;

        radio.addEventListener('change', () => {
          const coefSection = document.getElementById(`ps_coef_section_${idx}`);
          if (coefSection) {
            coefSection.style.display = (radio.value !== 'enfant') ? 'block' : 'none';
          }
        });

        radioLabel.appendChild(radio);
        radioLabel.appendChild(document.createTextNode(opt));
        group.appendChild(radioLabel);
      });

      const coefSection = this.buildCoefficients(inst, regime, prest, idx);
      coefSection.id = `ps_coef_section_${idx}`;
      coefSection.style.display = (storedUnit && storedUnit !== 'enfant') ? 'block' : 'none';
      group.appendChild(coefSection);

      container.appendChild(group);
    });

    section.appendChild(container);
    return section;
  }

  /** Tableau de coefficients de conversion par année pour une prestation. */
  buildCoefficients(inst, regime, prest, idx) {
    const node = this.ensureNode(inst, regime);
    const section = document.createElement('div');
    section.className = 'questionnaire-q4-coefficients';

    const helpText = document.createElement('p');
    helpText.className = 'questionnaire-help-text';
    helpText.textContent = "Coefficients de conversion (→ Enfant) pour chaque année :";
    section.appendChild(helpText);

    const years = this.getPrestationYears(inst, regime, prest);

    const table = document.createElement('table');
    table.className = 'questionnaire-coef-table';
    const thead = document.createElement('thead');
    thead.innerHTML = `
      <tr>
        <th>Année</th>
        <th>Coefficient (→ Enfant)</th>
        <th>Source / Commentaire</th>
      </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    const rowsYears = years.length ? years : ['default'];
    rowsYears.forEach(year => {
      tbody.appendChild(this.buildCoefRow(node, prest, idx, year));
    });
    table.appendChild(tbody);
    section.appendChild(table);
    return section;
  }

  buildCoefRow(node, prest, idx, year) {
    const row = document.createElement('tr');

    const yearCell = document.createElement('td');
    yearCell.textContent = year === 'default' ? 'Par défaut' : year;
    yearCell.style.fontWeight = 'bold';
    row.appendChild(yearCell);

    const stored = node.coefficients?.[prest]?.[year];

    const coefCell = document.createElement('td');
    const coefInput = document.createElement('input');
    coefInput.type = 'number';
    coefInput.step = '0.1';
    coefInput.min = '0';
    coefInput.name = `ps_coef_${idx}`;
    coefInput.id = `ps_coef_${idx}_${year}`;
    coefInput.placeholder = '2.5';
    coefInput.dataset.prest = prest;
    coefInput.dataset.year = year;
    if (stored && stored.value !== undefined) coefInput.value = stored.value;
    coefCell.appendChild(coefInput);
    row.appendChild(coefCell);

    const sourceCell = document.createElement('td');
    const sourceInput = document.createElement('input');
    sourceInput.type = 'text';
    sourceInput.id = `ps_src_${idx}_${year}`;
    sourceInput.placeholder = 'INS DRC 2021';
    if (stored && stored.source !== undefined) sourceInput.value = stored.source;
    sourceCell.appendChild(sourceInput);
    row.appendChild(sourceCell);

    return row;
  }

  /** Section C — Inclusion / exclusion d'une prestation. */
  buildExclusionSection(inst, regime, prestations) {
    const node = this.ensureNode(inst, regime);
    const section = document.createElement('fieldset');
    section.className = 'questionnaire-section';
    section.innerHTML = '<legend>C — Inclusion / exclusion de prestations</legend>';

    const desc = document.createElement('p');
    desc.textContent = "Cocher les prestations à exclure de l'affichage (graphique et tableau) et des agrégats (ligne ESS erronée, doublon, hors périmètre).";
    section.appendChild(desc);

    const container = document.createElement('div');
    container.className = 'questionnaire-q4-container';

    prestations.forEach((prest, idx) => {
      const line = document.createElement('label');
      line.className = 'questionnaire-radio';
      line.style.display = 'flex';
      line.style.alignItems = 'center';
      line.style.gap = '8px';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.name = 'ps_exclude';
      checkbox.id = `ps_excl_${idx}`;
      checkbox.dataset.prest = prest;
      if (node.exclude[prest]) checkbox.checked = true;

      line.appendChild(checkbox);
      line.appendChild(document.createTextNode(prest));
      container.appendChild(line);
    });

    section.appendChild(container);
    return section;
  }

  /** Sauvegarde les réglages du couple institution/régime courant. */
  async saveData(inst, regime) {
    const node = this.ensureNode(inst, regime);

    // A1 — déduplication cotisants
    node.dedup_cotisants = {};
    document.querySelectorAll('input[name="ps_dedup_cot_pair"]').forEach((cb) => {
      const p1 = cb.dataset.prest1;
      const p2 = cb.dataset.prest2;
      if (p1 && p2) node.dedup_cotisants[`${p1}__${p2}`] = cb.checked ? 'true' : 'false';
    });

    // A2 — déduplication bénéficiaires
    node.dedup_beneficiaires = {};
    document.querySelectorAll('input[name="ps_dedup_ben_pair"]').forEach((cb) => {
      const p1 = cb.dataset.prest1;
      const p2 = cb.dataset.prest2;
      if (p1 && p2) node.dedup_beneficiaires[`${p1}__${p2}`] = cb.checked ? 'true' : 'false';
    });

    // D — agrégation recettes/dépenses (adjacence par prestation)
    node.finance_recettes = {};
    document.querySelectorAll('input[name^="ps_fin_recettes_"]:checked').forEach((cb) => {
      const prest = cb.dataset.prest;
      if (!prest) return;
      if (!node.finance_recettes[prest]) node.finance_recettes[prest] = [];
      node.finance_recettes[prest].push(cb.value);
    });

    node.finance_depenses = {};
    document.querySelectorAll('input[name^="ps_fin_depenses_"]:checked').forEach((cb) => {
      const prest = cb.dataset.prest;
      if (!prest) return;
      if (!node.finance_depenses[prest]) node.finance_depenses[prest] = [];
      node.finance_depenses[prest].push(cb.value);
    });

    // B — unité + coefficients
    node.unit = {};
    document.querySelectorAll('input[name^="ps_unit_"]:checked').forEach((radio) => {
      const prest = radio.dataset.prest;
      if (prest) node.unit[prest] = radio.value;
    });

    node.coefficients = {};
    document.querySelectorAll('input[name^="ps_coef_"]').forEach((input) => {
      const prest = input.dataset.prest;
      const year = input.dataset.year;
      if (!prest || year === undefined) return;
      const coefValue = parseFloat(input.value);
      if (isNaN(coefValue) || coefValue <= 0) return;
      const srcInput = document.getElementById(input.id.replace('ps_coef_', 'ps_src_'));
      const sourceValue = srcInput ? srcInput.value.trim() : '';
      if (!node.coefficients[prest]) node.coefficients[prest] = {};
      node.coefficients[prest][year] = { value: coefValue, source: sourceValue };
    });

    // C — exclusion
    node.exclude = {};
    document.querySelectorAll('input[name="ps_exclude"]:checked').forEach((cb) => {
      const prest = cb.dataset.prest;
      if (prest) node.exclude[prest] = true;
    });

    const persistOk = await this.persistData();
    if (!persistOk) return;

    window.dispatchEvent(new CustomEvent('prestation-settings-saved', {
      detail: { institution: inst, regime, prestations: this.currentPrestations }
    }));

    this.showToast('✓ Paramètres des prestations sauvegardés', 'success');
    this.closeModal();
  }

  async persistData() {
    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.data, null, 2)
      });
      if (!response.ok) throw new Error(`Erreur serveur : ${response.status}`);
      return true;
    } catch (e) {
      console.error('Erreur de persistance prestation settings:', e);
      this.showToast('⚠ Erreur : données non sauvegardées', 'error');
      return false;
    }
  }

  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `questionnaire-toast questionnaire-toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  closeModal() {
    const backdrop = document.querySelector('.questionnaire-backdrop');
    if (backdrop) backdrop.remove();
  }

  escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
}

// Initialisation globale
window.prestationSettings = null;
console.info('[PrestationSettings] module v2 chargé — A1 cotisants / A2 bénéficiaires');

document.addEventListener('DOMContentLoaded', async () => {
  window.prestationSettings = new PrestationSettings('/api/prestation-settings');
  await window.prestationSettings.loadData();
});
