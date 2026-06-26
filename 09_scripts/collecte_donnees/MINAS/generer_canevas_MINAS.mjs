/**
 * Génère le canevas Excel pour la collecte de données MINAS
 * Bulletin statistique de la protection sociale en RDC — 2e édition
 *
 * Usage : node generer_canevas_MINAS.mjs
 * Lancer APRÈS avoir validé le HTML (generer_html_MINAS.mjs)
 */

import path from 'path';
import { fileURLToPath } from 'url';
import ExcelJS from 'exceljs';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUTPUT_PATH = path.resolve(
  __dirname,
  '../../../10_output/collecte_donnees/MINAS/Canevas_donnees_MINAS_Bulletin_PS_RDC.xlsx'
);

const wb = new ExcelJS.Workbook();
wb.creator = 'METPS / BIT-OIT';
wb.created = new Date();

// ─── Palettes ─────────────────────────────────────────────────────────────────
const C = {
  bleu:       { argb: 'FF1F3864' },
  bleu2:      { argb: 'FF2E5E8E' },
  gris_s:     { argb: 'FFD9E1F2' },   // fond séparateur de groupe (neutre)
  gris_clair: { argb: 'FFF2F2F2' },   // cellules pré-remplies
  gris_en:    { argb: 'FFD9D9D9' },   // en-têtes colonnes
  jaune_inp:  { argb: 'FFFFFDE7' },   // cellules à saisir
  blanc:      { argb: 'FFFFFFFF' },
  noir:       { argb: 'FF000000' },
  bleu_txt:   { argb: 'FF1F3864' },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
function hdrTitle(cell, text) {
  cell.value = text;
  cell.fill  = { type: 'pattern', pattern: 'solid', fgColor: C.bleu };
  cell.font  = { bold: true, size: 12, color: C.blanc, name: 'Calibri' };
  cell.alignment = { horizontal: 'left', vertical: 'middle', wrapText: true };
  cell.border = { top: { style: 'thin' }, bottom: { style: 'thin' }, left: { style: 'thin' }, right: { style: 'thin' } };
}

function hdrNote(cell, text) {
  cell.value = text;
  cell.fill  = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFD6E4F0' } };
  cell.font  = { size: 9, italic: true, name: 'Calibri', color: C.noir };
  cell.alignment = { horizontal: 'left', vertical: 'middle', wrapText: true };
}

function hdrCol(cell, text) {
  cell.value = text;
  cell.fill  = { type: 'pattern', pattern: 'solid', fgColor: C.gris_en };
  cell.font  = { bold: true, size: 9, color: C.noir, name: 'Calibri' };
  cell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true };
  cell.border = { top: { style: 'thin' }, bottom: { style: 'thin' }, left: { style: 'thin' }, right: { style: 'thin' } };
}

function groupRow(ws, rowNum, text, nbCols, lastCol) {
  ws.mergeCells(`A${rowNum}:${lastCol}${rowNum}`);
  const cell = ws.getRow(rowNum).getCell(1);
  cell.value = text;
  cell.fill  = { type: 'pattern', pattern: 'solid', fgColor: C.gris_s };
  cell.font  = { bold: true, size: 10, color: C.bleu_txt, name: 'Calibri' };
  cell.alignment = { horizontal: 'left', vertical: 'middle', wrapText: true };
  cell.border = { top: { style: 'medium' }, bottom: { style: 'medium' }, left: { style: 'thin' }, right: { style: 'thin' } };
  ws.getRow(rowNum).height = 22;
}

function fixedCell(cell, text, bold = false) {
  cell.value = text;
  cell.fill  = { type: 'pattern', pattern: 'solid', fgColor: C.gris_clair };
  cell.font  = { size: 9, name: 'Calibri', bold, color: C.noir };
  cell.alignment = { horizontal: 'left', vertical: 'middle', wrapText: true };
  cell.border = { top: { style: 'thin', color: { argb: 'FFCCCCCC' } }, bottom: { style: 'thin', color: { argb: 'FFCCCCCC' } }, left: { style: 'thin', color: { argb: 'FFCCCCCC' } }, right: { style: 'thin', color: { argb: 'FFCCCCCC' } } };
}

function inputCell(cell, value = '') {
  cell.value = value;
  cell.fill  = { type: 'pattern', pattern: 'solid', fgColor: C.jaune_inp };
  cell.font  = { size: 9, name: 'Calibri', color: C.noir };
  cell.alignment = { horizontal: 'left', vertical: 'middle', wrapText: true };
  cell.border = { top: { style: 'thin', color: { argb: 'FFAAAAAA' } }, bottom: { style: 'thin', color: { argb: 'FFAAAAAA' } }, left: { style: 'thin', color: { argb: 'FFAAAAAA' } }, right: { style: 'thin', color: { argb: 'FFAAAAAA' } } };
}

// ═══════════════════════════════════════════════════════════════════════════════
// FEUILLE 1 — CARTOGRAPHIE DES PROGRAMMES (Section A)
// ═══════════════════════════════════════════════════════════════════════════════
const wsA = wb.addWorksheet('A - Cartographie', {
  views: [{ state: 'frozen', xSplit: 2, ySplit: 3 }],
  pageSetup: { orientation: 'landscape', fitToPage: true, fitToWidth: 1, fitToHeight: 0 },
});

wsA.columns = [
  { key: 'ref',    width: 8  },
  { key: 'nom',    width: 36 },
  { key: 'type',   width: 22 },
  { key: 'cible',  width: 28 },
  { key: 'fin',    width: 22 },
  { key: 'resp',   width: 24 },
  { key: 'debut',  width: 12 },
  { key: 'statut', width: 16 },
  { key: 'notes',  width: 30 },
];

wsA.mergeCells('A1:I1');
hdrTitle(wsA.getCell('A1'), 'CARTOGRAPHIE DES PROGRAMMES — MINAS  |  Bulletin Statistique Protection Sociale RDC – 2e édition');
wsA.getRow(1).height = 28;

wsA.mergeCells('A2:I2');
hdrNote(wsA.getCell('A2'), 'Veuillez lister TOUS les programmes d\'assistance sociale actifs ou récents (2019–2024), y compris les programmes en partenariat. Les lignes pré-renseignées sont indicatives — à corriger selon la réalité. Ajoutez des lignes si nécessaire.');
wsA.getRow(2).height = 30;

const hA = wsA.getRow(3);
hA.height = 36;
['Réf.', 'Nom officiel du programme', 'Type de prestation\n(Espèces / Nature / Mixte)', 'Population cible', 'Financement principal', 'Responsable mise en œuvre', 'Année\ndébut', 'Statut\n(Actif / Clôturé)', 'Notes / Commentaires']
  .forEach((h, i) => hdrCol(hA.getCell(i + 1), h));

const cartData = [
  { group: 'Programmes avec partenaires internationaux (PAM, UNICEF, Banque mondiale…)' },
  { ref: 'A1.1', nom: 'PAM — Transferts de ressources sans conditions (TRC)', type: 'Espèces et alimentaire', cible: 'Ménages en insécurité alimentaire, déplacés internes', fin: 'PAM / Donateurs int.', resp: 'PAM', debut: '~2000s', statut: 'Actif', notes: '' },
  { ref: 'A1.2', nom: 'PAM — Cantines scolaires', type: 'Nature (repas scolaires)', cible: 'Enfants scolarisés (écoles primaires publiques)', fin: 'PAM + MEPST', resp: 'PAM', debut: '2023 (pilote)', statut: 'Actif (pilote)', notes: 'Confirmer périmètre géographique' },
  { ref: 'A1.3', nom: 'UNICEF — Cash + Nutrition', type: 'Espèces + nutrition', cible: 'Enfants malnutris, ménages vulnérables', fin: 'UNICEF + donateurs', resp: 'UNICEF', debut: '~2021', statut: 'Actif (intermittent)', notes: 'Confirmer zones opérationnelles' },
  { ref: 'A1.4', nom: 'STEP / Banque mondiale (IDA)', type: 'Transferts conditionnels', cible: 'Ménages extrêmement pauvres (Kasaï, Lomami, Kwilu)', fin: 'Banque mondiale / IDA', resp: 'Banque mondiale', debut: '~2018', statut: 'Clôturé (fév. 2024)', notes: 'Confirmer données finales' },
  { ref: 'A1.5', nom: '', type: '', cible: '', fin: '', resp: '', debut: '', statut: '', notes: '' },
  { group: 'Programmes gouvernementaux MINAS' },
  { ref: 'A2.1', nom: '', type: '', cible: '', fin: 'Gouvernement RDC', resp: 'MINAS', debut: '', statut: '', notes: '' },
  { ref: 'A2.2', nom: '', type: '', cible: '', fin: 'Gouvernement RDC', resp: 'MINAS', debut: '', statut: '', notes: '' },
  { ref: 'A2.3', nom: '', type: '', cible: '', fin: 'Gouvernement RDC', resp: 'MINAS', debut: '', statut: '', notes: '' },
  { group: 'Programmes pour personnes handicapées' },
  { ref: 'A3.1', nom: '', type: '', cible: 'Personnes handicapées', fin: '', resp: '', debut: '', statut: '', notes: '' },
  { ref: 'A3.2', nom: '', type: '', cible: 'Personnes handicapées', fin: '', resp: '', debut: '', statut: '', notes: '' },
  { group: 'Programmes pour personnes âgées sans pension' },
  { ref: 'A4.1', nom: '', type: '', cible: 'Personnes âgées (≥ 60 ans)', fin: '', resp: '', debut: '', statut: '', notes: '' },
  { group: 'Autres programmes' },
  { ref: 'A5.1', nom: '', type: '', cible: '', fin: '', resp: '', debut: '', statut: '', notes: '' },
  { ref: 'A5.2', nom: '', type: '', cible: '', fin: '', resp: '', debut: '', statut: '', notes: '' },
];

let rA = 4;
cartData.forEach(d => {
  const row = wsA.getRow(rA);
  if (d.group) {
    groupRow(wsA, rA, d.group, 9, 'I');
  } else {
    row.height = 26;
    fixedCell(row.getCell(1), d.ref, true);
    // Nom : pré-rempli (gris) ou vide (jaune)
    if (d.nom) { fixedCell(row.getCell(2), d.nom, true); } else { inputCell(row.getCell(2)); }
    // Type, Cible
    if (d.type) { fixedCell(row.getCell(3), d.type); } else { inputCell(row.getCell(3)); }
    if (d.cible) { fixedCell(row.getCell(4), d.cible); } else { inputCell(row.getCell(4)); }
    // Financement, Responsable
    if (d.fin) { fixedCell(row.getCell(5), d.fin); } else { inputCell(row.getCell(5)); }
    if (d.resp) { fixedCell(row.getCell(6), d.resp); } else { inputCell(row.getCell(6)); }
    // Année, Statut
    if (d.debut) { fixedCell(row.getCell(7), d.debut); } else { inputCell(row.getCell(7)); }
    if (d.statut) { fixedCell(row.getCell(8), d.statut); } else { inputCell(row.getCell(8)); }
    // Notes toujours saisie
    inputCell(row.getCell(9), d.notes || '');
  }
  rA++;
});

// ═══════════════════════════════════════════════════════════════════════════════
// FEUILLE 2 — BÉNÉFICIAIRES ET DONNÉES FINANCIÈRES (Sections B et C)
// ═══════════════════════════════════════════════════════════════════════════════
const wsBC = wb.addWorksheet('B-C - Bénéficiaires et finances', {
  views: [{ state: 'frozen', xSplit: 4, ySplit: 3 }],
  pageSetup: { orientation: 'landscape', fitToPage: true, fitToWidth: 1, fitToHeight: 0 },
});

wsBC.columns = [
  { key: 'ref',   width: 8  },
  { key: 'prog',  width: 30 },
  { key: 'prest', width: 30 },
  { key: 'ind',   width: 36 },
  { key: 'y2019', width: 14 },
  { key: 'y2020', width: 14 },
  { key: 'y2021', width: 14 },
  { key: 'y2022', width: 14 },
  { key: 'y2023', width: 14 },
  { key: 'y2024', width: 14 },
  { key: 'source', width: 22 },
  { key: 'notes', width: 26 },
];

wsBC.mergeCells('A1:L1');
hdrTitle(wsBC.getCell('A1'), 'BÉNÉFICIAIRES ET DONNÉES FINANCIÈRES — MINAS  |  Bulletin Statistique Protection Sociale RDC – 2e édition');
wsBC.getRow(1).height = 28;

wsBC.mergeCells('A2:L2');
hdrNote(wsBC.getCell('A2'), 'Cellules en jaune = à renseigner. Cellules en gris = pré-remplies ou indicatives (à corriger si nécessaire). Unité monétaire pour la section C : CDF ou USD — préciser dans la colonne Notes. Pour les personnes : indiquer le nombre de personnes, pas de ménages, sauf mention contraire.');
wsBC.getRow(2).height = 32;

const hBC = wsBC.getRow(3);
hBC.height = 40;
['Réf.', 'Programme', 'Description de la prestation', 'Indicateur', '2019', '2020', '2021', '2022', '2023', '2024', 'Source', 'Notes / Commentaires']
  .forEach((h, i) => hdrCol(hBC.getCell(i + 1), h));

const bcData = [
  { group: 'B — BÉNÉFICIAIRES PAR PRESTATION' },
  { ref: 'B1.1', prog: 'PAM — TRC', prest: 'Espèces et alimentaire (inconditionnel)', ind: 'Bénéficiaires total (personnes)' },
  { ref: 'B1.1H', prog: 'PAM — TRC', prest: '', ind: '  dont : Hommes' },
  { ref: 'B1.1F', prog: 'PAM — TRC', prest: '', ind: '  dont : Femmes' },
  { ref: 'B1.2', prog: 'PAM — TRC', prest: 'Espèces et alimentaire (inconditionnel)', ind: 'Ménages bénéficiaires' },
  { ref: 'B1.3', prog: 'PAM — Cantines scolaires', prest: 'Repas scolaires (nature)', ind: 'Enfants bénéficiaires' },
  { ref: 'B1.3G', prog: 'PAM — Cantines scolaires', prest: '', ind: '  dont : Garçons' },
  { ref: 'B1.3F', prog: 'PAM — Cantines scolaires', prest: '', ind: '  dont : Filles' },
  { ref: 'B2.1', prog: 'UNICEF — Cash + Nutrition', prest: 'Espèces + soutien nutritionnel (mixte)', ind: 'Bénéficiaires total (personnes)' },
  { ref: 'B2.1H', prog: 'UNICEF — Cash + Nutrition', prest: '', ind: '  dont : Hommes' },
  { ref: 'B2.1F', prog: 'UNICEF — Cash + Nutrition', prest: '', ind: '  dont : Femmes' },
  { ref: 'B2.2', prog: 'UNICEF — Cash + Nutrition', prest: 'Espèces + soutien nutritionnel (mixte)', ind: 'Ménages bénéficiaires' },
  { ref: 'B3.1', prog: 'STEP / Banque mondiale', prest: 'Transferts monétaires conditionnels (espèces)', ind: 'Ménages bénéficiaires' },
  { ref: 'B3.2', prog: 'STEP / Banque mondiale', prest: 'Transferts monétaires conditionnels (espèces)', ind: 'Personnes couvertes (ménages × taille moyenne)' },
  { ref: 'B4.1', prog: '[Programme MINAS 1]', prest: '[À renseigner]', ind: 'Bénéficiaires (personnes)' },
  { ref: 'B4.1H', prog: '[Programme MINAS 1]', prest: '', ind: '  dont : Hommes' },
  { ref: 'B4.1F', prog: '[Programme MINAS 1]', prest: '', ind: '  dont : Femmes' },
  { ref: 'B4.2', prog: '[Programme MINAS 2]', prest: '[À renseigner]', ind: 'Bénéficiaires (personnes)' },
  { ref: 'B5.1', prog: '[Programme personnes handicapées]', prest: '[À renseigner]', ind: 'Bénéficiaires enregistrés' },
  { ref: 'B5.2', prog: '[Programme personnes handicapées]', prest: '[À renseigner]', ind: 'Bénéficiaires ayant reçu une prestation' },
  { ref: 'B6.1', prog: '[Programme personnes âgées]', prest: '[À renseigner]', ind: 'Bénéficiaires (pers. ≥ 60 ans)' },
  { group: 'C — DONNÉES FINANCIÈRES (CDF ou USD — préciser dans Notes)' },
  { ref: 'C1.1', prog: 'Tous programmes MINAS', prest: '—', ind: 'Dépenses totales de prestations en espèces' },
  { ref: 'C1.2', prog: 'Tous programmes MINAS', prest: '—', ind: 'Dépenses totales de prestations en nature (valeur estimée)' },
  { ref: 'C1.3', prog: 'PAM — TRC (via MINAS)', prest: '—', ind: 'Montant total des transferts PAM (si disponible)' },
  { ref: 'C2.1', prog: 'PAM — TRC', prest: '—', ind: 'Transfert moyen mensuel par ménage bénéficiaire' },
  { ref: 'C2.2', prog: 'STEP / Banque mondiale', prest: '—', ind: 'Transfert moyen mensuel par ménage bénéficiaire' },
  { ref: 'C2.3', prog: '[Programme gouvernemental MINAS]', prest: '[À renseigner]', ind: 'Prestation ou transfert moyen par bénéficiaire' },
];

let rBC = 4;
bcData.forEach(d => {
  const row = wsBC.getRow(rBC);
  if (d.group) {
    groupRow(wsBC, rBC, d.group, 12, 'L');
  } else {
    row.height = 22;
    fixedCell(row.getCell(1), d.ref, true);
    // Programme et prestation : pré-rempli si pas de crochet
    const isProg = d.prog && !d.prog.startsWith('[');
    const isPrest = d.prest && !d.prest.startsWith('[');
    if (isProg) { fixedCell(row.getCell(2), d.prog); } else { inputCell(row.getCell(2), d.prog || ''); }
    if (isPrest) { fixedCell(row.getCell(3), d.prest); } else { inputCell(row.getCell(3), d.prest || ''); }
    fixedCell(row.getCell(4), d.ind);
    for (let c = 5; c <= 12; c++) inputCell(row.getCell(c));
  }
  rBC++;
});

// ═══════════════════════════════════════════════════════════════════════════════
// FEUILLE 3 — MODE D'EMPLOI
// ═══════════════════════════════════════════════════════════════════════════════
const wsHelp = wb.addWorksheet("Mode d'emploi", {
  pageSetup: { orientation: 'portrait', fitToPage: true },
});

wsHelp.columns = [{ key: 'a', width: 28 }, { key: 'b', width: 72 }];

wsHelp.mergeCells('A1:B1');
hdrTitle(wsHelp.getCell('A1'), "MODE D'EMPLOI — Canevas MINAS  |  Bulletin Statistique Protection Sociale RDC – 2e édition");
wsHelp.getRow(1).height = 28;

const helpRows = [
  ['', ''],
  ['OBJECTIF DU CANEVAS', 'Ce fichier est la pièce jointe accompagnant la lettre de demande de données adressée au MINAS. Il est à compléter et retourner avant la date limite indiquée dans la lettre.'],
  ['', ''],
  ['STRUCTURE DU FICHIER', ''],
  ['Feuille 1 — A (Cartographie)', 'Liste de tous les programmes d\'assistance sociale actifs ou récents. Compléter ou corriger les lignes pré-renseignées. Ajouter des lignes si nécessaire.'],
  ['Feuille 2 — B-C (Bénéficiaires et finances)', 'Données chiffrées par programme et par année (2019–2024). Section B : bénéficiaires. Section C : données financières.'],
  ['', ''],
  ['CONVENTIONS DE COULEUR', ''],
  ['Cellule jaune', 'À renseigner par le MINAS.'],
  ['Cellule grise', 'Pré-remplie sur la base d\'informations partielles — à corriger ou confirmer.'],
  ['Séparateur bleu clair', 'Groupe de lignes (lecture seule).'],
  ['', ''],
  ['UNITÉS ET FORMAT', ''],
  ['Données de bénéficiaires', 'Nombre de personnes (individus), sauf mention contraire (ex. "ménages bénéficiaires").'],
  ['Données financières', 'Franc congolais (CDF) courant de préférence. Si USD, préciser dans la colonne Notes.'],
  ['Années', 'Au 31 décembre de chaque année ou à la date de fin de programme. Si donnée indisponible pour une année, laisser la cellule vide.'],
  ['', ''],
  ['CONTACT', 'Pour toute question : [Nom du point focal — METPS / BIT] — [email@exemple.org]'],
];

let rH = 2;
helpRows.forEach(([a, b]) => {
  const row = wsHelp.getRow(rH);
  row.height = 22;
  const cA = row.getCell(1);
  const cB = row.getCell(2);
  cA.value = a;
  cB.value = b;
  cA.font = { bold: !!a && a !== '', size: 10, name: 'Calibri' };
  cB.font = { size: 10, name: 'Calibri' };
  cA.alignment = { vertical: 'middle', wrapText: true };
  cB.alignment = { vertical: 'middle', wrapText: true };
  if (a && b === '' && a !== '') {
    cA.font = { bold: true, size: 11, name: 'Calibri', color: C.bleu };
  }
  rH++;
});

// ─── Sauvegarde ───────────────────────────────────────────────────────────────
fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });
await wb.xlsx.writeFile(OUTPUT_PATH);
console.log(`✅ Excel généré : ${OUTPUT_PATH}`);
