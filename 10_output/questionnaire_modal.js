/**
 * Questionnaire Modal — Qualification des régimes
 * Gère les 3 questions (Q1, Q2, Q4) pour chaque institution/régime
 * Persistance via questionnaire_data.json
 */

class QuestionnaireModal {
  constructor(dataFile = 'questionnaire_data.json') {
    this.dataFile = dataFile;
    this.data = {};
    this.currentInstitution = null;
    this.loadData();
  }

  /**
   * Charge les données depuis le fichier JSON
   */
  async loadData() {
    try {
      const response = await fetch(this.dataFile);
      if (response.ok) {
        this.data = await response.json();
      }
    } catch (e) {
      console.log('Pas de fichier questionnaire existant, création en cours...');
      this.data = {};
    }
  }

  /**
   * Crée le bouton "Paramètres" à injecter dans l'UI
   */
  createParametersButton(institution, regimes) {
    const btn = document.createElement('button');
    btn.className = 'questionnaire-btn';
    btn.textContent = '⚙️ Paramètres';
    btn.title = 'Configurer les règles d\'affichage pour ' + institution;
    btn.onclick = () => this.openModal(institution, regimes);
    return btn;
  }

  /**
   * Ouvre le modal avec les 3 questionnaires
   */
  openModal(institution, regimes) {
    this.currentInstitution = institution;
    
    // Crée le backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'questionnaire-backdrop';
    backdrop.onclick = () => this.closeModal();

    // Crée le modal
    const modal = document.createElement('div');
    modal.className = 'questionnaire-modal';
    modal.onclick = (e) => e.stopPropagation();

    // En-tête
    const header = document.createElement('div');
    header.className = 'questionnaire-header';
    header.innerHTML = `
      <h2>Questionnaire de qualification — ${institution}</h2>
      <button class="questionnaire-close" onclick="document.querySelector('.questionnaire-backdrop').remove()">×</button>
    `;

    // Contenu
    const content = document.createElement('div');
    content.className = 'questionnaire-content';
    
    // Q1 — Affiliation aux régimes
    content.appendChild(this.buildQ1(institution, regimes));
    
    // Q2 — Agrégation des recettes/dépenses
    content.appendChild(this.buildQ2(institution, regimes));
    
    // Q4 — Unité des bénéficiaires
    content.appendChild(this.buildQ4(institution, regimes));

    // Pied de page
    const footer = document.createElement('div');
    footer.className = 'questionnaire-footer';
    footer.innerHTML = `
      <button class="btn-cancel" onclick="document.querySelector('.questionnaire-backdrop').remove()">Annuler</button>
      <button class="btn-save" onclick="window.questionnaire.saveData('${institution}')">Sauvegarder</button>
    `;

    modal.appendChild(header);
    modal.appendChild(content);
    modal.appendChild(footer);

    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
  }

  /**
   * Q1 — Affiliation aux régimes (matrice de recoupement)
   */
  buildQ1(institution, regimes) {
    const section = document.createElement('fieldset');
    section.className = 'questionnaire-section';
    section.innerHTML = `<legend>Q1 — Affiliation aux régimes</legend>`;
    
    const desc = document.createElement('p');
    desc.textContent = 'Pour chaque régime, indiquer s\'il partage la même population de cotisants avec les autres régimes';
    section.appendChild(desc);

    // Tableau
    const table = document.createElement('table');
    table.className = 'questionnaire-matrix';

    // En-tête
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = '<th></th>';
    regimes.forEach(r => {
      const th = document.createElement('th');
      th.textContent = window.NOM_COURT ? (window.NOM_COURT[r] || r) : r;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Lignes
    const tbody = document.createElement('tbody');
    regimes.forEach((regime1, i) => {
      const row = document.createElement('tr');
      const rowHeader = document.createElement('th');
      rowHeader.textContent = window.NOM_COURT ? (window.NOM_COURT[regime1] || regime1) : regime1;
      row.appendChild(rowHeader);

      regimes.forEach((regime2, j) => {
        const td = document.createElement('td');
        if (i === j) {
          td.textContent = '—';
          td.style.backgroundColor = '#f0f0f0';
        } else {
          const checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.name = `q1_${regime1}_${regime2}`;
          checkbox.id = `q1_${regime1}_${regime2}`;
          
          // Charge l'état sauvegardé si disponible
          const stored = this.getStoredValue(institution, 'Q1', `${regime1}__${regime2}`);
          if (stored) checkbox.checked = stored === 'true';
          
          td.appendChild(checkbox);
        }
        row.appendChild(td);
      });

      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    section.appendChild(table);

    return section;
  }

  /**
   * Q2 — Agrégation des recettes/dépenses
   */
  buildQ2(institution, regimes) {
    const section = document.createElement('fieldset');
    section.className = 'questionnaire-section';
    section.innerHTML = `<legend>Q2 — Agrégation des recettes/dépenses</legend>`;
    
    const desc = document.createElement('p');
    desc.textContent = 'Pour chaque régime, indiquer si recettes et dépenses ont été combinées avec d\'autres régimes';
    section.appendChild(desc);

    // Tableau
    const table = document.createElement('table');
    table.className = 'questionnaire-table';

    // En-tête
    const thead = document.createElement('thead');
    thead.innerHTML = `
      <tr>
        <th>Régime</th>
        <th>Recettes combinées avec</th>
        <th>Dépenses combinées avec</th>
      </tr>
    `;
    table.appendChild(thead);

    // Lignes
    const tbody = document.createElement('tbody');
    regimes.forEach((regime) => {
      const row = document.createElement('tr');
      const regimeCell = document.createElement('td');
      regimeCell.textContent = window.NOM_COURT ? (window.NOM_COURT[regime] || regime) : regime;
      regimeCell.style.fontWeight = 'bold';
      row.appendChild(regimeCell);

      // Recettes
      const receiptsCell = document.createElement('td');
      receiptsCell.appendChild(this.buildMultiCheckbox(institution, `Q2_${regime}_recettes`, regime, regimes));
      row.appendChild(receiptsCell);

      // Dépenses
      const expensesCell = document.createElement('td');
      expensesCell.appendChild(this.buildMultiCheckbox(institution, `Q2_${regime}_depenses`, regime, regimes));
      row.appendChild(expensesCell);

      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    section.appendChild(table);

    return section;
  }

  /**
   * Q4 — Unité des bénéficiaires (uniquement branches famille/enfants)
   */
  buildQ4(institution, regimes) {
    const section = document.createElement('fieldset');
    section.className = 'questionnaire-section';
    section.innerHTML = `<legend>Q4 — Unité des bénéficiaires</legend>`;
    
    const desc = document.createElement('p');
    desc.textContent = 'Pour les régimes couvrant Enfants ou Famille, indiquer l\'unité de compte des bénéficiaires';
    section.appendChild(desc);

    const container = document.createElement('div');
    container.className = 'questionnaire-q4-container';

    // Filtre : ne montrer que les régimes avec "Enfants" ou "Famille" dans les FONCTIONS OIT (métadonnées ESS)
    const familyRegimes = regimes.filter((regime) => {
      // Cherche dans les métadonnées du régime
      if (!window.REGIME_META || !window.REGIME_META[regime]) {
        return false;
      }
      
      const meta = window.REGIME_META[regime];
      if (!meta.versions || !meta.versions.length) {
        return false;
      }
      
      // Prendre la dernière version (la plus récente)
      const latestVersion = meta.versions[meta.versions.length - 1];
      if (!latestVersion) {
        return false;
      }
      
      // Chercher dans les fonctions OIT
      const fonctions = latestVersion.fonctions_oit || [];
      if (!Array.isArray(fonctions)) {
        return false;
      }
      
      // Vérifier si au moins une fonction contient "enfants", "famille", "maternité" ou "paternité"
      return fonctions.some((fonction) => {
        if (!fonction) return false;
        const funcLower = String(fonction).toLowerCase();
        return /enfants|famille|maternit|paternit/i.test(funcLower);
      });
    });

    familyRegimes.forEach((regime) => {
      const group = document.createElement('div');
      group.className = 'questionnaire-q4-group';
      
      const label = document.createElement('label');
      label.innerHTML = `<strong>${window.NOM_COURT ? (window.NOM_COURT[regime] || regime) : regime}</strong>`;
      group.appendChild(label);

      const options = ['Enfant', 'Ménage', 'Personne', 'Autre'];
      options.forEach((opt) => {
        const radioLabel = document.createElement('label');
        radioLabel.className = 'questionnaire-radio';
        
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = `q4_${regime}`;
        radio.value = opt.toLowerCase();
        radio.id = `q4_${regime}_${opt}`;
        
        // Charge l'état sauvegardé
        const stored = this.getStoredValue(institution, 'Q4', regime);
        if (stored === opt.toLowerCase()) radio.checked = true;
        
        radioLabel.appendChild(radio);
        radioLabel.appendChild(document.createTextNode(opt));
        group.appendChild(radioLabel);
      });

      container.appendChild(group);
    });

    section.appendChild(container);
    return section;
  }

  /**
   * Construit un groupe de checkboxes multi-sélection
   */
  buildMultiCheckbox(institution, fieldName, currentRegime, allRegimes) {
    const container = document.createElement('div');
    container.className = 'questionnaire-multi-checkbox';

    allRegimes.forEach((regime) => {
      if (regime === currentRegime) return;

      const label = document.createElement('label');
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.name = fieldName;
      checkbox.value = regime;
      checkbox.id = `${fieldName}_${regime}`;

      // Charge l'état sauvegardé
      const stored = this.getStoredValue(institution, fieldName.split('_')[0], `${currentRegime}__${regime}`);
      if (stored && stored.includes(regime)) checkbox.checked = true;

      label.appendChild(checkbox);
      label.appendChild(document.createTextNode(window.NOM_COURT ? (window.NOM_COURT[regime] || regime) : regime));
      container.appendChild(label);
    });

    return container;
  }

  /**
   * Récupère une valeur sauvegardée
   */
  getStoredValue(institution, question, key) {
    if (!this.data[institution]) return null;
    if (!this.data[institution][question]) return null;
    return this.data[institution][question][key] || null;
  }

  /**
   * Sauvegarde les données du questionnaire
   */
  async saveData(institution) {
    if (!this.data[institution]) {
      this.data[institution] = {};
    }

    // Q1 — Affiliation
    this.data[institution].Q1 = {};
    document.querySelectorAll('input[name^="q1_"]').forEach((cb) => {
      const parts = cb.name.replace('q1_', '').split('_');
      const regime1 = parts.slice(0, -1).join('_');
      const regime2 = parts[parts.length - 1];
      this.data[institution].Q1[`${regime1}__${regime2}`] = cb.checked ? 'true' : 'false';
    });

    // Q2 — Agrégation
    this.data[institution].Q2 = {};
    document.querySelectorAll('input[name^="q2_"]').forEach((cb) => {
      const name = cb.name;
      if (cb.checked) {
        if (!this.data[institution].Q2[name]) {
          this.data[institution].Q2[name] = [];
        }
        this.data[institution].Q2[name].push(cb.value);
      }
    });

    // Q4 — Unité
    this.data[institution].Q4 = {};
    document.querySelectorAll('input[name^="q4_"]:checked').forEach((radio) => {
      const regime = radio.name.replace('q4_', '');
      this.data[institution].Q4[regime] = radio.value;
    });

    // Sauvegarde dans le fichier
    await this.persistData();

    // Feedback
    this.showToast('✓ Questionnaire sauvegardé', 'success');
    this.closeModal();
  }

  /**
   * Sauvegarde les données dans le fichier JSON
   */
  async persistData() {
    try {
      const response = await fetch(this.dataFile, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.data, null, 2)
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la sauvegarde');
      }
    } catch (e) {
      console.error('Erreur de persistance:', e);
      this.showToast('⚠ Erreur : données non sauvegardées', 'error');
    }
  }

  /**
   * Affiche un message de confirmation
   */
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

  /**
   * Ferme le modal
   */
  closeModal() {
    const backdrop = document.querySelector('.questionnaire-backdrop');
    if (backdrop) backdrop.remove();
  }
}

// Initialisation globale
window.questionnaire = null;

document.addEventListener('DOMContentLoaded', async () => {
  window.questionnaire = new QuestionnaireModal('questionnaire_data.json');
  await window.questionnaire.loadData();
});
