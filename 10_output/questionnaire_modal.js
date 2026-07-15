/**
 * Questionnaire Modal — Qualification des régimes
 * Gère les 3 questions (Q1, Q2, Q4) pour chaque institution/régime
 * Persistance via questionnaire_data.json
 */

class QuestionnaireModal {
  // apiUrl : endpoint serveur pour lire/écrire questionnaire_data.json
  constructor(apiUrl = '/api/questionnaire-data') {
    this.apiUrl = apiUrl;
    this.data = {};
    this.currentInstitution = null;
    this.loadPromise = null;
    this.isOpening = false;
  }

  /**
   * Charge les données depuis l'API serveur
   */
  async loadData() {
    if (this.loadPromise) return this.loadPromise;

    this.loadPromise = (async () => {
      const response = await fetch(this.apiUrl, { cache: 'no-store' });
      if (!response.ok) {
        throw new Error(`Erreur serveur : ${response.status}`);
      }

      const data = await response.json();
      if (!data || typeof data !== 'object' || Array.isArray(data)) {
        throw new Error('Format de questionnaire invalide');
      }

      this.data = data;
      return data;
    })();

    try {
      return await this.loadPromise;
    } finally {
      this.loadPromise = null;
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
  async openModal(institution, regimes) {
    if (this.isOpening || document.querySelector('.questionnaire-backdrop')) return;

    this.isOpening = true;
    try {
      await this.loadData();
    } catch (e) {
      console.error('Questionnaire : impossible de charger les données', e);
      this.showToast('⚠ Impossible de charger les paramètres', 'error');
      return;
    } finally {
      this.isOpening = false;
    }

    if (document.querySelector('.questionnaire-backdrop')) return;

    this.currentInstitution = institution;
    this.currentRegimes = regimes;
    // S'assurer que les données de cette institution existent en mémoire
    if (!this.data[institution]) {
      this.data[institution] = { Q1: {}, Q1b: {}, Q2: {}, Q4: {}, Q4_coefficients: {} };
    }
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
    
    // Q1 — Affiliation aux régimes (cotisants)
    content.appendChild(this.buildQ1(institution, regimes));

    // Q1b — Affiliation aux régimes (bénéficiaires)
    content.appendChild(this.buildQ1b(institution, regimes));
    
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
        // Utiliser data-attributes pour stocker les régimes sans dépendre du parsing du name
        checkbox.name = `q1_pair`;
        checkbox.id = `q1_${regime1}__${regime2}`;
        checkbox.dataset.regime1 = regime1;
        checkbox.dataset.regime2 = regime2;

        // Charge l'état sauvegardé si disponible
        const stored = this.getStoredValue(institution, 'Q1', `${regime1}__${regime2}`);
        if (stored) checkbox.checked = stored === 'true';

        // Symétrie : cocher/décocher automatiquement la case miroir
        checkbox.addEventListener('change', () => {
          const mirror = document.getElementById(`q1_${regime2}__${regime1}`);
          if (mirror) mirror.checked = checkbox.checked;
        });

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
   * Q1b — Affiliation aux régimes (bénéficiaires)
   * Même matrice que Q1 mais pour les bénéficiaires.
   * Persistée sous data[institution].Q1b
   */
  buildQ1b(institution, regimes) {
    const section = document.createElement('fieldset');
    section.className = 'questionnaire-section';
    section.innerHTML = `<legend>Q1b — Partage des bénéficiaires entre régimes</legend>`;

    const desc = document.createElement('p');
    desc.textContent = 'Pour chaque régime, indiquer s\'il couvre les mêmes bénéficiaires que les autres régimes (ex. même enfant déclaré dans plusieurs branches)';
    section.appendChild(desc);

    const table = document.createElement('table');
    table.className = 'questionnaire-matrix';

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
          checkbox.name = 'q1b_pair';
          checkbox.id = `q1b_${regime1}__${regime2}`;
          checkbox.dataset.regime1 = regime1;
          checkbox.dataset.regime2 = regime2;

          const stored = this.getStoredValue(institution, 'Q1b', `${regime1}__${regime2}`);
          if (stored) checkbox.checked = stored === 'true';

          // Symétrie automatique
          checkbox.addEventListener('change', () => {
            const mirror = document.getElementById(`q1b_${regime2}__${regime1}`);
            if (mirror) mirror.checked = checkbox.checked;
          });

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
      // REGIME_META est structuré par institution : REGIME_META[institution][regime]
      if (!window.REGIME_META) return true; // pas de méta → montrer tous les régimes
      // Trouver l'institution du régime (le code commence par "CNSS_" ou "CNSSAP_" etc.)
      const instKey = Object.keys(window.REGIME_META).find(inst =>
        window.REGIME_META[inst] && window.REGIME_META[inst][regime]
      );
      if (!instKey) return true; // régime non trouvé → inclure par défaut
      const meta = window.REGIME_META[instKey][regime];
      if (!meta || !meta.versions || !meta.versions.length) return true;
      const latestVersion = meta.versions[meta.versions.length - 1];
      if (!latestVersion) return true;
      const fonctions = latestVersion.fonctions_oit || [];
      if (!Array.isArray(fonctions) || fonctions.length === 0) return true;
      // Vérifier si au moins une fonction contient "enfants", "famille", "maternité" ou "paternité"
      return fonctions.some((f) => /enfants|famille|maternit|paternit/i.test(String(f || '')));
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
        
        // Événement pour afficher/cacher le tableau de coefficients
        radio.addEventListener('change', () => {
          const coefSection = document.getElementById(`q4_coef_${regime}`);
          if (coefSection) {
            coefSection.style.display = (radio.value !== 'enfant') ? 'block' : 'none';
          }
        });
        
        radioLabel.appendChild(radio);
        radioLabel.appendChild(document.createTextNode(opt));
        group.appendChild(radioLabel);
      });

      // Tableau de coefficients (conditionnel)
      const coefSection = this.buildQ4Coefficients(institution, regime);
      coefSection.id = `q4_coef_${regime}`;
      const storedUnit = this.getStoredValue(institution, 'Q4', regime);
      coefSection.style.display = (storedUnit && storedUnit !== 'enfant') ? 'block' : 'none';
      group.appendChild(coefSection);

      container.appendChild(group);
    });

    section.appendChild(container);
    return section;
  }

  /**
   * Q4 Coefficients — Tableau de conversion par année
   */
  buildQ4Coefficients(institution, regime) {
    const section = document.createElement('div');
    section.className = 'questionnaire-q4-coefficients';
    
    const helpText = document.createElement('p');
    helpText.className = 'questionnaire-help-text';
    helpText.textContent = 'Si l\'unité n\'est pas "Enfant", définir les coefficients de conversion (vers Enfant) pour chaque année :';
    section.appendChild(helpText);
    
    // Récupérer les années ESS disponibles pour ce régime
    const years = this.getRegimeYears(regime);
    
    // Tableau HTML
    const table = document.createElement('table');
    table.className = 'questionnaire-coef-table';
    
    // En-tête
    const thead = document.createElement('thead');
    thead.innerHTML = `
      <tr>
        <th>Année</th>
        <th>Coefficient (→ Enfant)</th>
        <th>Source / Commentaire</th>
      </tr>
    `;
    table.appendChild(thead);
    
    // Corps
    const tbody = document.createElement('tbody');
    tbody.id = `q4_coef_tbody_${regime}`;
    
    if (years.length === 0) {
      // Pas d'années → ligne par défaut
      tbody.appendChild(this.buildCoefRow(institution, regime, 'default'));
    } else {
      // Lignes par année
      years.forEach(year => {
        tbody.appendChild(this.buildCoefRow(institution, regime, year));
      });
    }
    
    table.appendChild(tbody);
    section.appendChild(table);
    
    return section;
  }

  /**
   * Construit une ligne du tableau de coefficients
   */
  buildCoefRow(institution, regime, year) {
    const row = document.createElement('tr');
    
    // Colonne année
    const yearCell = document.createElement('td');
    yearCell.textContent = year === 'default' ? 'Par défaut' : year;
    yearCell.style.fontWeight = 'bold';
    row.appendChild(yearCell);
    
    // Colonne coefficient
    const coefCell = document.createElement('td');
    const coefInput = document.createElement('input');
    coefInput.type = 'number';
    coefInput.step = '0.1';
    coefInput.min = '0';
    coefInput.name = `q4_coef_${regime}_${year}`;
    coefInput.id = `q4_coef_${regime}_${year}`;
    coefInput.placeholder = '2.5';
    
    // Charger valeur sauvegardée
    const storedCoef = this.data[institution]?.Q4_coefficients?.[regime]?.[year];
    if (storedCoef && storedCoef.value !== undefined) {
      coefInput.value = storedCoef.value;
    }
    
    coefCell.appendChild(coefInput);
    row.appendChild(coefCell);
    
    // Colonne source
    const sourceCell = document.createElement('td');
    const sourceInput = document.createElement('input');
    sourceInput.type = 'text';
    sourceInput.name = `q4_source_${regime}_${year}`;
    sourceInput.id = `q4_source_${regime}_${year}`;
    sourceInput.placeholder = 'INS DRC 2021';
    
    // Charger source sauvegardée
    if (storedCoef && storedCoef.source !== undefined) {
      sourceInput.value = storedCoef.source;
    }
    
    sourceCell.appendChild(sourceInput);
    row.appendChild(sourceCell);
    
    return row;
  }

  /**
   * Récupère les années ESS disponibles pour un régime
   */
  getRegimeYears(regime) {
    if (!window.REGIME_META) return [];
    
    // Chercher le régime dans toutes les institutions
    for (const inst in window.REGIME_META) {
      if (window.REGIME_META[inst][regime]) {
        const meta = window.REGIME_META[inst][regime];
        return meta.ess_years || [];
      }
    }
    
    return [];
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

      // Charge l'état sauvegardé : Q2 stocke { "Q2_R1_recettes": ["R2", "R3"] }
      const storedList = this.data[institution]?.Q2?.[fieldName] || [];
      if (storedList.includes(regime)) checkbox.checked = true;

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

    // Q1 — Affiliation : utilise data-regime1 / data-regime2 pour éviter
    // le parsing du name (les codes régimes contiennent des underscores)
    this.data[institution].Q1 = {};
    document.querySelectorAll('input[name="q1_pair"]').forEach((cb) => {
      const regime1 = cb.dataset.regime1;
      const regime2 = cb.dataset.regime2;
      if (regime1 && regime2) {
        this.data[institution].Q1[`${regime1}__${regime2}`] = cb.checked ? 'true' : 'false';
      }
    });

    // Q1b — Partage des bénéficiaires (même logique que Q1)
    this.data[institution].Q1b = {};
    document.querySelectorAll('input[name="q1b_pair"]').forEach((cb) => {
      const regime1 = cb.dataset.regime1;
      const regime2 = cb.dataset.regime2;
      if (regime1 && regime2) {
        this.data[institution].Q1b[`${regime1}__${regime2}`] = cb.checked ? 'true' : 'false';
      }
    });

    // Q2 — Agrégation financière
    this.data[institution].Q2 = {};
    document.querySelectorAll('input[name^="Q2_"]').forEach((cb) => {
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

    // Q4 Coefficients
    this.data[institution].Q4_coefficients = {};
    document.querySelectorAll('input[name^="q4_coef_"]').forEach((input) => {
      const parts = input.name.replace('q4_coef_', '').split('_');
      const year = parts.pop(); // Dernier élément = année
      const regime = parts.join('_'); // Reste = code régime
      
      if (!this.data[institution].Q4_coefficients[regime]) {
        this.data[institution].Q4_coefficients[regime] = {};
      }
      
      const coefValue = parseFloat(input.value);
      const sourceInput = document.getElementById(`q4_source_${regime}_${year}`);
      const sourceValue = sourceInput ? sourceInput.value.trim() : '';
      
      if (!isNaN(coefValue) && coefValue > 0) {
        this.data[institution].Q4_coefficients[regime][year] = {
          value: coefValue,
          source: sourceValue
        };
      }
    });

    // Sauvegarde dans le fichier
    const persistOk = await this.persistData();
    
    if (!persistOk) {
      // Échec de persistance : arrêt du flux, pas d'event ni de fermeture
      return;
    }

    // Notifier le dashboard que les paramètres ont changé
    window.dispatchEvent(new CustomEvent('questionnaire-saved', {
      detail: { institution, regimes: this.currentRegimes }
    }));

    // Feedback
    this.showToast('✓ Questionnaire sauvegardé', 'success');
    this.closeModal();
  }

  /**
   * Sauvegarde les données dans le fichier JSON
   * @returns {boolean} true si sauvegarde OK, false sinon
   */
  async persistData() {
    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.data, null, 2)
      });
      if (!response.ok) {
        throw new Error(`Erreur serveur : ${response.status}`);
      }
      return true;
    } catch (e) {
      console.error('Erreur de persistance questionnaire:', e);
      this.showToast('⚠ Erreur : données non sauvegardées', 'error');
      return false;
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

// Initialisation globale ; les données sont chargées au démarrage du tableau
// de bord puis actualisées avant chaque ouverture du questionnaire.
window.questionnaire = new QuestionnaireModal('/api/questionnaire-data');
