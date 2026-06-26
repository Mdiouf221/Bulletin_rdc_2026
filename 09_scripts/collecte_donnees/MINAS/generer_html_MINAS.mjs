/**
 * Génère la prévisualisation HTML de l'annexe de données MINAS
 * ÉTAPE 1 : Exécuter ce script d'abord, réviser le HTML, puis lancer generer_demande_MINAS.mjs et generer_canevas_MINAS.mjs
 *
 * Usage : node generer_html_MINAS.mjs
 * Ouvrir ensuite : 10_output/collecte_donnees/MINAS/preview_MINAS.html
 */

import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUTPUT_PATH = path.resolve(
  __dirname,
  '../../../10_output/collecte_donnees/MINAS/preview_MINAS.html'
);

const html = /* html */`<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Annexe données — MINAS | Bulletin PS RDC 2e édition</title>
<style>
  :root {
    --rouge:  #C00000;
    --orange: #E07820;
    --jaune:  #7F7F00;
    --bleu:   #1F3864;
    --bleu2:  #2E5E8E;
    --gris:   #EEF2F8;
    --jaune_fond: #FFF8DC;
  }
  * { box-sizing: border-box; }
  body {
    font-family: Calibri, 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #111;
    background: #f8f8f8;
    margin: 0;
    padding: 0;
  }

  /* Bandeau de prévisualisation */
  #preview-bar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: #1a1a2e;
    color: #fff;
    padding: 10px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-size: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }
  #preview-bar strong { font-size: 13px; color: #FFD700; }
  #preview-bar .hint { opacity: 0.75; font-style: italic; }
  #preview-bar .actions { display: flex; gap: 8px; }
  #preview-bar button {
    background: var(--bleu2);
    color: #fff;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    font-family: inherit;
  }
  #preview-bar button:hover { background: #1e4068; }
  #preview-bar button.print-btn { background: var(--rouge); }
  #preview-bar button.print-btn:hover { background: #8b0000; }

  /* Document */
  .document {
    max-width: 1100px;
    margin: 24px auto;
    background: #fff;
    box-shadow: 0 2px 16px rgba(0,0,0,0.12);
    padding: 48px 56px;
  }

  /* Titre */
  .doc-title { color: var(--bleu); font-size: 26px; font-weight: 900; margin: 0 0 6px; }
  .doc-subtitle { color: var(--bleu); font-size: 18px; font-weight: bold; margin: 0 0 24px; }

  /* Bloc objet */
  .bloc-objet {
    background: #EBF3FB;
    border: 1px solid #AACCEE;
    padding: 12px 16px;
    border-radius: 3px;
    margin-bottom: 24px;
    font-size: 13px;
  }
  .bloc-objet p { margin: 4px 0; }

  /* Note */
  .note {
    background: var(--jaune_fond);
    border-left: 5px solid #C8A800;
    padding: 10px 16px;
    margin: 16px 0;
    font-size: 12px;
    line-height: 1.6;
  }

  /* Sections */
  .section { margin-top: 40px; page-break-before: always; }
  .section-title {
    font-size: 15px;
    font-weight: bold;
    color: var(--bleu);
    border-bottom: 2px solid var(--bleu);
    padding-bottom: 6px;
    margin-bottom: 10px;
    text-transform: uppercase;
  }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: bold;
    color: #fff;
    margin-left: 8px;
    vertical-align: middle;
  }
  .badge.rouge  { background: var(--rouge); }
  .badge.orange { background: var(--orange); }
  .badge.jaune  { background: var(--jaune); }

  /* Tableaux */
  table { width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 12px; }
  th {
    background: var(--bleu);
    color: #fff;
    padding: 8px 10px;
    text-align: center;
    font-weight: bold;
    border: 1px solid #4a6b9a;
    vertical-align: middle;
    font-size: 11.5px;
  }
  td { padding: 7px 10px; border: 1px solid #ccc; vertical-align: top; }
  tr:nth-child(even) td { background: var(--gris); }
  tr:hover td { background: #eef4ff; }
  .ref { font-weight: bold; white-space: nowrap; color: #333; font-size: 11px; }

  /* Textes colorés (synthèse) */
  .rouge-text  { color: var(--rouge);  font-weight: bold; }
  .orange-text { color: var(--orange); font-weight: bold; }
  .jaune-text  { color: var(--jaune);  font-weight: bold; }

  /* Pied de page */
  .footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid #ddd; font-size: 11px; font-style: italic; color: #888; text-align: center; }

  /* Impression */
  @media print {
    #preview-bar { display: none !important; }
    body { background: #fff; }
    .document { box-shadow: none; margin: 0; padding: 20mm 18mm; max-width: none; }
    @page { size: A4 landscape; margin: 15mm; }
    .section { page-break-before: always; }
  }
</style>
</head>
<body>

<div id="preview-bar">
  <div>
    <strong>&#9888; PRÉVISUALISATION</strong>
    <span class="hint"> — Vérifiez le contenu ci-dessous avant de générer le Word et l'Excel</span>
  </div>
  <div class="actions">
    <button onclick="window.print()" class="print-btn">&#128424; Imprimer / Aperçu PDF</button>
    <button onclick="document.getElementById('preview-bar').style.display='none'">&#10005; Masquer la barre</button>
  </div>
</div>

<div class="document">

  <h1 class="doc-title">Annexe — Données demandées au MINAS</h1>
  <h2 class="doc-subtitle">Ministère des Affaires Sociales, Action Humanitaire et Solidarité Nationale</h2>

  <div class="bloc-objet">
    <p><strong>Objet :</strong> Données relatives aux programmes d'assistance sociale — 2<sup>e</sup> Bulletin statistique sur la protection sociale en RDC</p>
    <p><strong>Période :</strong> 2019–2024 ou dernière année disponible</p>
    <p><strong>Demandeur :</strong> [À compléter]</p>
    <p><strong>Contact MINAS :</strong> [À compléter]</p>
  </div>

  <div class="note">
    <strong>Précisions sur le format souhaité :</strong><br>
    • Pour chaque indicateur, renseigner la valeur annuelle (au 31 décembre ou à la date de fin de programme).<br>
    • Les données financières sont souhaitées en franc congolais (CDF) courants.<br>
    • En cas d'indisponibilité d'une donnée pour une année donnée, laisser la cellule vide et indiquer la dernière année disponible.<br>
    • <strong>Les lignes pré-renseignées sont des exemples indicatifs basés sur des informations partielles — elles doivent être corrigées, complétées ou supprimées selon la réalité.</strong>
  </div>

  <!-- SECTION A -->
  <div class="section" style="page-break-before:avoid">
    <div class="section-title">A — Cartographie des programmes <span class="badge rouge">Priorité haute</span></div>
    <table>
      <thead>
        <tr>
          <th style="width:5%">Réf.</th>
          <th style="width:22%">Nom officiel du programme</th>
          <th style="width:14%">Type de prestation<br><small>(espèces / nature / mixte)</small></th>
          <th style="width:17%">Population cible</th>
          <th style="width:13%">Financement principal</th>
          <th style="width:14%">Responsable mise en œuvre</th>
          <th style="width:8%">Année début</th>
          <th style="width:7%">Statut</th>
        </tr>
      </thead>
      <tbody>
        <tr><td class="ref">A1.1</td><td><strong>PAM — Transferts de ressources sans conditions (TRC)</strong></td><td>Espèces et alimentaire</td><td>Ménages en insécurité alimentaire, déplacés internes</td><td>PAM / Donateurs internationaux</td><td>PAM</td><td>~2000s</td><td>Actif</td></tr>
        <tr><td class="ref">A1.2</td><td><strong>PAM — Cantines scolaires</strong></td><td>Nature (repas scolaires)</td><td>Enfants scolarisés (écoles primaires publiques)</td><td>PAM + MEPST</td><td>PAM</td><td>2023 (pilote)</td><td>Actif (pilote)</td></tr>
        <tr><td class="ref">A1.3</td><td><strong>UNICEF — Cash + Nutrition</strong></td><td>Espèces + nutrition</td><td>Enfants malnutris, ménages vulnérables</td><td>UNICEF + donateurs</td><td>UNICEF</td><td>~2021</td><td>Actif (intermittent)</td></tr>
        <tr><td class="ref">A1.4</td><td><strong>STEP / Banque mondiale (IDA)</strong></td><td>Transferts conditionnels</td><td>Ménages extrêmement pauvres (Kasaï, Lomami, Kwilu)</td><td>Banque mondiale / IDA</td><td>Banque mondiale</td><td>~2018</td><td>Clôturé (fév. 2024)</td></tr>
        <tr><td class="ref">A2.1</td><td>[Programme gouvernemental MINAS — à renseigner]</td><td></td><td></td><td>Gouvernement RDC</td><td></td><td></td><td></td></tr>
        <tr><td class="ref">A2.2</td><td>[Programme gouvernemental MINAS — à renseigner]</td><td></td><td></td><td>Gouvernement RDC</td><td></td><td></td><td></td></tr>
        <tr><td class="ref">A2.3</td><td>[Programme gouvernemental MINAS — à renseigner]</td><td></td><td></td><td>Gouvernement RDC</td><td></td><td></td><td></td></tr>
        <tr><td class="ref">A3.1</td><td>[Programme personnes handicapées — à renseigner]</td><td></td><td>Personnes handicapées</td><td></td><td></td><td></td><td></td></tr>
        <tr><td class="ref">A3.2</td><td>[Programme personnes handicapées — à renseigner]</td><td></td><td>Personnes handicapées</td><td></td><td></td><td></td><td></td></tr>
        <tr><td class="ref">A4.1</td><td>[Programme personnes âgées sans pension — à renseigner]</td><td></td><td>Personnes âgées (60 ans ou plus)</td><td></td><td></td><td></td><td></td></tr>
        <tr><td class="ref">A5.1</td><td>[Autre programme — à renseigner]</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
        <tr><td class="ref">A5.2</td><td>[Autre programme — à renseigner]</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
      </tbody>
    </table>
  </div>

  <!-- SECTION B -->
  <div class="section">
    <div class="section-title">B — Bénéficiaires par prestation <span class="badge rouge">Priorité haute</span></div>
    <table>
      <thead>
        <tr>
          <th style="width:5%">Réf.</th>
          <th style="width:18%">Programme</th>
          <th style="width:20%">Description de la prestation<br><small>(espèces / nature / mixte)</small></th>
          <th style="width:18%">Public cible</th>
          <th style="width:20%">Indicateur</th>
          <th style="width:8%">Désagrég.</th>
          <th style="width:11%">Années disponibles</th>
        </tr>
      </thead>
      <tbody>
        <tr><td class="ref">B1.1</td><td>PAM — TRC</td><td>Transferts en espèces et alimentaires inconditionnels</td><td>Ménages en insécurité alimentaire, déplacés internes</td><td>Nombre de bénéficiaires (personnes)</td><td>Par sexe</td><td>2019–2024 ou dernière année disponible</td></tr>
        <tr><td class="ref">B1.2</td><td>PAM — TRC</td><td>Transferts en espèces et alimentaires inconditionnels</td><td>Ménages en insécurité alimentaire, déplacés internes</td><td>Nombre de ménages bénéficiaires</td><td>—</td><td>2019–2024 ou dernière année disponible</td></tr>
        <tr><td class="ref">B1.3</td><td>PAM — Cantines scolaires</td><td>Repas scolaires (nature)</td><td>Enfants scolarisés (écoles primaires publiques)</td><td>Nombre d'enfants bénéficiaires</td><td>Par sexe</td><td>2023–2024 (pilote)</td></tr>
        <tr><td class="ref">B2.1</td><td>UNICEF — Cash + Nutrition</td><td>Transferts en espèces + soutien nutritionnel (mixte)</td><td>Enfants malnutris, ménages vulnérables</td><td>Nombre de bénéficiaires (personnes)</td><td>Par sexe</td><td>2019–2024 ou dernière année disponible</td></tr>
        <tr><td class="ref">B2.2</td><td>UNICEF — Cash + Nutrition</td><td>Transferts en espèces + soutien nutritionnel (mixte)</td><td>Enfants malnutris, ménages vulnérables</td><td>Nombre de ménages bénéficiaires</td><td>—</td><td>2019–2024 ou dernière année disponible</td></tr>
        <tr><td class="ref">B3.1</td><td>STEP / Banque mondiale</td><td>Transferts monétaires conditionnels (espèces)</td><td>Ménages extrêmement pauvres (Kasaï, Lomami, Kwilu)</td><td>Ménages bénéficiaires</td><td>—</td><td>2019–2024 (selon disponibilité)</td></tr>
        <tr><td class="ref">B3.2</td><td>STEP / Banque mondiale</td><td>Transferts monétaires conditionnels (espèces)</td><td>Ménages extrêmement pauvres (Kasaï, Lomami, Kwilu)</td><td>Personnes couvertes (ménages × taille moyenne)</td><td>Par sexe chef ménage</td><td>2019–2024 (selon disponibilité)</td></tr>
        <tr><td class="ref">B4.1</td><td>[Programme MINAS 1]</td><td>[À renseigner]</td><td>[À renseigner]</td><td>Nombre de bénéficiaires (personnes)</td><td>Par sexe</td><td>2019–2024 ou dernière année disponible</td></tr>
        <tr><td class="ref">B4.2</td><td>[Programme MINAS 2]</td><td>[À renseigner]</td><td>[À renseigner]</td><td>Nombre de bénéficiaires (personnes)</td><td>Par sexe</td><td>2019–2024 ou dernière année disponible</td></tr>
        <tr><td class="ref">B5.1</td><td>[Programme personnes handicapées]</td><td>[À renseigner]</td><td>Personnes handicapées</td><td>Bénéficiaires enregistrés</td><td>Par sexe</td><td>2019–2024 ou dernière année disponible</td></tr>
        <tr><td class="ref">B5.2</td><td>[Programme personnes handicapées]</td><td>[À renseigner]</td><td>Personnes handicapées</td><td>Bénéficiaires ayant reçu une prestation</td><td>Par sexe</td><td>2019–2024 ou dernière année disponible</td></tr>
        <tr><td class="ref">B6.1</td><td>[Programme personnes âgées]</td><td>[À renseigner]</td><td>Personnes âgées (60 ans et plus)</td><td>Bénéficiaires (personnes 60 ans et plus)</td><td>Par sexe</td><td>2019–2024 ou dernière année disponible</td></tr>
      </tbody>
    </table>
  </div>

  <!-- SECTION C -->
  <div class="section">
    <div class="section-title">C — Données financières <span class="badge rouge">Priorité haute</span></div>
    <table>
      <thead>
        <tr>
          <th style="width:5%">Réf.</th>
          <th style="width:25%">Programme</th>
          <th style="width:40%">Indicateur</th>
          <th style="width:10%">Unité</th>
          <th style="width:15%">Années disponibles</th>
          <th style="width:5%">Notes</th>
        </tr>
      </thead>
      <tbody>
        <tr><td class="ref">C1.1</td><td>Tous programmes MINAS</td><td>Total dépenses de prestations en espèces (versements directs)</td><td>CDF ou USD</td><td>2019–2024</td><td></td></tr>
        <tr><td class="ref">C1.2</td><td>Tous programmes MINAS</td><td>Total dépenses de prestations en nature (valeur estimée)</td><td>CDF ou USD</td><td>2019–2024</td><td></td></tr>
        <tr><td class="ref">C1.3</td><td>PAM — TRC (via MINAS)</td><td>Montant total des transferts (si disponible auprès du MINAS)</td><td>USD</td><td>2019–2024</td><td>À défaut : source directe PAM</td></tr>
        <tr><td class="ref">C2.1</td><td>PAM — TRC</td><td>Transfert moyen mensuel par ménage bénéficiaire</td><td>USD ou CDF</td><td>2019–2024</td><td></td></tr>
        <tr><td class="ref">C2.2</td><td>STEP / Banque mondiale</td><td>Transfert moyen mensuel par ménage bénéficiaire</td><td>USD ou CDF</td><td>2019–2024</td><td></td></tr>
        <tr><td class="ref">C2.3</td><td>[Programme gouvernemental MINAS]</td><td>Prestation ou transfert moyen par bénéficiaire</td><td>CDF ou USD</td><td>2019–2024</td><td></td></tr>
      </tbody>
    </table>
  </div>

  <!-- SYNTHÈSE -->
  <div class="section">
    <div class="section-title">Synthèse par priorité</div>
    <table>
      <thead>
        <tr>
          <th style="width:18%">Priorité</th>
          <th style="width:27%">Données</th>
          <th style="width:55%">Raison</th>
        </tr>
      </thead>
      <tbody>
        <tr><td class="rouge-text">&#128308; Priorité haute</td><td>A, B, C</td><td>Sans ces données, la couverture des régimes non contributifs ne peut être calculée ni ventilée par programme. Les indicateurs ODD 1.3.1 pour l'assistance sociale restent non documentés.</td></tr>
      </tbody>
    </table>
  </div>

  <div class="footer">
    Le présent document a été produit dans le cadre du Programme BIT/OIT d'appui au développement du système national de protection sociale en RDC.
  </div>

</div>
</body>
</html>`;

fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });
fs.writeFileSync(OUTPUT_PATH, html, 'utf8');
console.log(`✅ Prévisualisation HTML générée : ${OUTPUT_PATH}`);
console.log(`   → Ouvrir dans un navigateur pour réviser avant de générer le Word et l'Excel.`);
