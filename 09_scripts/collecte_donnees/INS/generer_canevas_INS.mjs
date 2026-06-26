import ExcelJS from "exceljs";
import { writeFileSync } from "fs";

const wb = new ExcelJS.Workbook();
wb.creator = "Bulletin PS RDC";
wb.created = new Date();

// ── Couleurs ──────────────────────────────────────────────────────────────────
const BLEU       = "1F3864";
const BLEU_CLAIR = "D6E4F0";
const GRIS_CLAIR = "EEF2F8";
const ROUGE      = "C00000";
const ORANGE     = "E07820";
const VERT       = "375623";
const JAUNE_NOTE = "FFF2CC";
const BLANC      = "FFFFFF";

// ── Helpers ───────────────────────────────────────────────────────────────────
function headerStyle(couleur = BLEU) {
  return {
    font:      { name: "Calibri", bold: true, color: { argb: "FF" + BLANC }, size: 11 },
    fill:      { type: "pattern", pattern: "solid", fgColor: { argb: "FF" + couleur } },
    alignment: { vertical: "middle", horizontal: "left", wrapText: true },
    border:    thinBorder()
  };
}

function cellStyle(bg = null, bold = false, color = "000000") {
  return {
    font:      { name: "Calibri", size: 10, bold, color: { argb: "FF" + color } },
    fill:      bg ? { type: "pattern", pattern: "solid", fgColor: { argb: "FF" + bg } } : { type: "pattern", pattern: "none" },
    alignment: { vertical: "top", horizontal: "left", wrapText: true },
    border:    thinBorder()
  };
}

function inputStyle() {
  return {
    font:      { name: "Calibri", size: 10 },
    fill:      { type: "pattern", pattern: "solid", fgColor: { argb: "FFFFFFCC" } },  // jaune très clair
    alignment: { vertical: "top", horizontal: "left", wrapText: true },
    border:    {
      top:    { style: "thin", color: { argb: "FF999999" } },
      bottom: { style: "dashed", color: { argb: "FF999999" } },
      left:   { style: "thin", color: { argb: "FF999999" } },
      right:  { style: "thin", color: { argb: "FF999999" } }
    }
  };
}

function thinBorder() {
  const b = { style: "thin", color: { argb: "FFAAAAAA" } };
  return { top: b, bottom: b, left: b, right: b };
}

function applyStyle(cell, style) {
  Object.assign(cell, style);
}

// Ajouter une ligne titre de section (fusionnée sur toute la largeur)
function addSectionHeader(ws, texte, couleur, nbCols) {
  const row = ws.addRow([texte]);
  ws.mergeCells(row.number, 1, row.number, nbCols);
  const cell = row.getCell(1);
  cell.font      = { name: "Calibri", bold: true, color: { argb: "FF" + BLANC }, size: 12 };
  cell.fill      = { type: "pattern", pattern: "solid", fgColor: { argb: "FF" + couleur } };
  cell.alignment = { vertical: "middle", horizontal: "left" };
  row.height = 22;
  return row;
}

// Ajouter une ligne d'en-tête de colonnes
function addColHeader(ws, labels, couleur = BLEU) {
  const row = ws.addRow(labels);
  row.eachCell(cell => applyStyle(cell, headerStyle(couleur)));
  row.height = 30;
  return row;
}

// Ajouter une ligne de données (colonnes fixes + colonnes de saisie)
function addDataRow(ws, fixedCols, inputCount, pair) {
  const values = [...fixedCols, ...Array(inputCount).fill("")];
  const row = ws.addRow(values);
  const bg = pair ? GRIS_CLAIR : null;

  // Colonnes fixes
  fixedCols.forEach((_, i) => {
    const cell = row.getCell(i + 1);
    applyStyle(cell, cellStyle(bg, i === 1)); // col 2 = gras (nom de la donnée)
  });
  // Colonnes de saisie
  for (let i = fixedCols.length + 1; i <= fixedCols.length + inputCount; i++) {
    applyStyle(row.getCell(i), inputStyle());
  }
  row.height = 40;
  return row;
}

function addEmptyRow(ws) {
  ws.addRow([]);
}

// ── Feuille 1 : CANEVAS DE SAISIE ────────────────────────────────────────────
const ws = wb.addWorksheet("Canevas de saisie", {
  pageSetup: {
    orientation: "landscape",
    paperSize: 9,
    fitToPage: true,
    fitToWidth: 1,
    fitToHeight: 0,
    margins: { left: 0.5, right: 0.5, top: 0.75, bottom: 0.75, header: 0.3, footer: 0.3 }
  }
});

// Largeurs des colonnes
// #(5) | Donnée(30) | Usage(35) | Désagrég.(12) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | Source | Commentaires
ws.columns = [
  { width: 5  },  // #
  { width: 32 },  // Donnée
  { width: 36 },  // Usage
  { width: 13 },  // Désagrégation
  { width: 10 },  // 2019
  { width: 10 },  // 2020
  { width: 10 },  // 2021
  { width: 10 },  // 2022
  { width: 10 },  // 2023
  { width: 10 },  // 2024
  { width: 22 },  // Source / enquête
  { width: 24 },  // Commentaires INS
];

const NB_COLS = 12;
const FIXED = 4;   // colonnes non saisies
const INPUT = 8;   // colonnes de saisie (2019-2024 + source + commentaires)

// ── Titre du document ──
ws.mergeCells(1, 1, 1, NB_COLS);
const titleCell = ws.getCell("A1");
titleCell.value = "CANEVAS DE COLLECTE DE DONNÉES — INS RDC\nDeuxième Bulletin statistique sur la protection sociale en RDC";
titleCell.font      = { name: "Calibri", bold: true, size: 14, color: { argb: "FF" + BLANC } };
titleCell.fill      = { type: "pattern", pattern: "solid", fgColor: { argb: "FF" + BLEU } };
titleCell.alignment = { vertical: "middle", horizontal: "center", wrapText: true };
ws.getRow(1).height = 48;

// ── Ligne info ──
ws.mergeCells(2, 1, 2, NB_COLS);
const infoCell = ws.getCell("A2");
infoCell.value = "Les cellules en jaune sont à remplir par l'INS.  Merci d'indiquer la source et l'année de référence pour chaque valeur saisie.  Années souhaitées : 2019–2024.";
infoCell.font      = { name: "Calibri", italic: true, size: 10, color: { argb: "FF7F6000" } };
infoCell.fill      = { type: "pattern", pattern: "solid", fgColor: { argb: "FF" + JAUNE_NOTE } };
infoCell.alignment = { vertical: "middle", horizontal: "left", wrapText: true };
ws.getRow(2).height = 28;

addEmptyRow(ws);

// ─────────────────────────────────────────────────────────────────────────────
// Section A
// ─────────────────────────────────────────────────────────────────────────────
addSectionHeader(ws, "A — Dénominateurs pour le calcul des indicateurs ODD 1.3.1   [PRIORITÉ CRITIQUE]", ROUGE, NB_COLS);
addColHeader(ws, ["#", "Donnée demandée", "Usage dans le bulletin", "Désagrégation", "2019", "2020", "2021", "2022", "2023", "2024", "Source / enquête", "Commentaires INS"]);

const dataA = [
  ["A1", "Population totale",                                    "Dénominateur indicateur global ODD 1.3.1",                                              "Par sexe"],
  ["A2", "Population 0–14 ans",                                  "Dénominateur sous-indicateur enfants (ODD 1.3.1)",                                      "Par sexe"],
  ["A3", "Population 0–17 ans",                                  "Variante dénominateur enfants selon définition OIT retenue",                            "Par sexe"],
  ["A4", "Nombre de naissances vivantes",                        "Dénominateur sous-indicateur maternité (ODD 1.3.1)",                                    "—"],
  ["A5", "Population 60 ans et plus",                            "Dénominateur vieillesse — âge légal CNSSAP (60 ans)",                                   "Par sexe"],
  ["A5b","Population 65 ans et plus",                            "Dénominateur vieillesse — âge légal CNSS hommes (65 ans)",                              "Par sexe"],
  ["A6", "Population active (15 ans et plus)",                   "Dénominateur sous-indicateurs AT/MP et cotisants retraite",                             "Par sexe"],
  ["A7", "Nombre de chômeurs (définition BIT)",                  "Dénominateur sous-indicateur chômage — attendu à 0 % (pas de régime d'assurance chômage)", "Par sexe"],
  ["A8", "Population en situation de handicap grave",            "Dénominateur sous-indicateur invalidité (ODD 1.3.1)",                                   "Par sexe"],
];
dataA.forEach((r, i) => addDataRow(ws, r, INPUT, i % 2 === 1));
addEmptyRow(ws);

// ─────────────────────────────────────────────────────────────────────────────
// Section B
// ─────────────────────────────────────────────────────────────────────────────
addSectionHeader(ws, "B — Seuils de référence pour l'adéquation des prestations   [PRIORITÉ CRITIQUE]", ROUGE, NB_COLS);
addColHeader(ws, ["#", "Donnée demandée", "Usage dans le bulletin", "Désagrégation", "2019", "2020", "2021", "2022", "2023", "2024", "Source / enquête", "Commentaires INS"]);

const dataB = [
  ["B1", "Seuil national de pauvreté (CDF/personne/mois)",       "Adéquation des pensions et allocations — comparé aux montants unitaires CNSS/CNSSAP",    "—"],
  ["B2", "SMIG — Salaire minimum (CDF/mois)",                    "Ratio pension moyenne / SMIG — adéquation des pensions de retraite",                     "—"],
  ["B3", "Indice des prix à la consommation (IPC)",              "Déflateur pour exprimer les prestations en termes réels",                                 "—"],
];
dataB.forEach((r, i) => addDataRow(ws, r, INPUT, i % 2 === 1));
addEmptyRow(ws);

// ─────────────────────────────────────────────────────────────────────────────
// Section C
// ─────────────────────────────────────────────────────────────────────────────
addSectionHeader(ws, "C — Structure du marché du travail   [PRIORITÉ IMPORTANTE]", ORANGE, NB_COLS);
addColHeader(ws, ["#", "Donnée demandée", "Usage dans le bulletin", "Désagrégation", "2019", "2020", "2021", "2022", "2023", "2024", "Source / enquête", "Commentaires INS"]);

const dataC = [
  ["C1", "Taux d'emploi informel (%)",                           "Confirmer / nuancer la valeur OIT utilisée (~96 % selon ILOEST 2020)",                   "Par sexe"],
  ["C2", "Structure emploi par secteur (agri / indus / services)","Figure contexte économique — part de chaque secteur en % de l'emploi total",             "Par sexe"],
  ["C3", "Effectif des agents de la fonction publique",          "Dénominateur légal CNSSAP — mesure du gap couverture légale / effective",                 "Par sexe"],
  ["C4", "Nombre de salariés du secteur privé formel",           "Dénominateur légal CNSS — estimation du taux de couverture",                             "Par sexe"],
];
dataC.forEach((r, i) => addDataRow(ws, r, INPUT, i % 2 === 1));
addEmptyRow(ws);

// ─────────────────────────────────────────────────────────────────────────────
// Section D
// ─────────────────────────────────────────────────────────────────────────────
addSectionHeader(ws, "D — Données démographiques   [PRIORITÉ COMPLÉMENTAIRE]", "375623", NB_COLS);
addColHeader(ws, ["#", "Donnée demandée", "Usage dans le bulletin", "Désagrégation", "2019", "2020", "2021", "2022", "2023", "2024", "Source / enquête", "Commentaires INS"]);

const dataD = [
  ["D1", "Espérance de vie à la naissance",                      "Durée moyenne de perception des pensions après l'âge légal de la retraite",              "Par sexe"],
  ["D2", "Nombre moyen d'enfants par foyer",                     "Facteur de conversion foyers / enfants — paramètre clé pour les allocations familiales CNSS", "—"],
  ["D3", "Taille moyenne des ménages",                           "Conversion entre effectifs ménages et individus couverts",                               "—"],
  ["D4", "Pyramide des âges (population par tranche quinquennale)","Figure de contexte démographique — calcul des dénominateurs par groupe d'âge",           "Par sexe"],
];
dataD.forEach((r, i) => addDataRow(ws, r, INPUT, i % 2 === 1));
addEmptyRow(ws);

// ─────────────────────────────────────────────────────────────────────────────
// Section E
// ─────────────────────────────────────────────────────────────────────────────
addSectionHeader(ws, "E — Données économiques nationales   [PRIORITÉ COMPLÉMENTAIRE]", "375623", NB_COLS);
addColHeader(ws, ["#", "Donnée demandée", "Usage dans le bulletin", "Désagrégation", "2019", "2020", "2021", "2022", "2023", "2024", "Source / enquête", "Commentaires INS"]);

const dataE = [
  ["E1", "PIB nominal en CDF courants",                          "Calcul du ratio dépenses de protection sociale / PIB",                                   "—"],
  ["E2", "Taux de pauvreté national (%)",                        "Contexte économique — confirmation directe de la valeur INS 2024 (69 %)",                "—"],
  ["E3", "Indice de Gini",                                       "Contexte inégalités — confirmation valeur INS 2024 (0,381)",                             "—"],
];
dataE.forEach((r, i) => addDataRow(ws, r, INPUT, i % 2 === 1));
addEmptyRow(ws);

// ─────────────────────────────────────────────────────────────────────────────
// Gel des volets (figer les 4 premières colonnes + 2 premières lignes)
// ─────────────────────────────────────────────────────────────────────────────
ws.views = [{ state: "frozen", xSplit: 4, ySplit: 3, activeCell: "E4" }];

// ── Feuille 2 : MODE D'EMPLOI ─────────────────────────────────────────────────
const ws2 = wb.addWorksheet("Mode d'emploi");
ws2.columns = [{ width: 20 }, { width: 80 }];

function addGuideRow(ws, label, texte, bold = false, bg = null) {
  const row = ws.addRow([label, texte]);
  row.getCell(1).font = { name: "Calibri", bold: true, size: 10, color: { argb: "FF" + BLEU } };
  row.getCell(2).font = { name: "Calibri", bold, size: 10 };
  row.getCell(2).alignment = { wrapText: true, vertical: "top" };
  if (bg) {
    [1,2].forEach(c => {
      row.getCell(c).fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FF" + bg } };
    });
  }
  row.height = 22;
}

ws2.mergeCells(1, 1, 1, 2);
const g1 = ws2.getCell("A1");
g1.value = "MODE D'EMPLOI — Canevas de collecte de données INS";
g1.font  = { name: "Calibri", bold: true, size: 13, color: { argb: "FF" + BLANC } };
g1.fill  = { type: "pattern", pattern: "solid", fgColor: { argb: "FF" + BLEU } };
g1.alignment = { horizontal: "center", vertical: "middle" };
ws2.getRow(1).height = 30;

ws2.addRow([]);
addGuideRow(ws2, "Objet",           "Ce fichier est un canevas de collecte préparé par l'équipe du Bulletin statistique sur la protection sociale en RDC (OIT / Gouvernement RDC). Il liste les données statistiques dont l'équipe a besoin pour calculer les indicateurs de couverture (ODD 1.3.1) et produire les sections de contexte du bulletin.", true);
ws2.addRow([]);
addGuideRow(ws2, "Comment remplir", "Rendez-vous dans l'onglet « Canevas de saisie ». Les cellules en jaune sont à remplir. Pour chaque donnée, saisissez la valeur correspondant à chaque année disponible, indiquez la source (nom de l'enquête ou du document) et ajoutez un commentaire si nécessaire (notes méthodologiques, marges d'erreur, couverture géographique).");
ws2.addRow([]);
addGuideRow(ws2, "Données manquantes", "Si une valeur n'est pas disponible pour une année donnée, laissez la cellule vide ou écrivez « N/D ». Si la donnée n'existe pas du tout, indiquez « non produit » dans la colonne Commentaires.");
ws2.addRow([]);
addGuideRow(ws2, "Format des valeurs", "• Population : nombre entier (ex. 112 000 000)\n• Taux / pourcentages : valeur décimale (ex. 0,96 ou 96 %)\n• Montants en CDF : entier sans séparateur de milliers\n• IPC : indice (base 100 = année de référence à préciser)\n• Pyramide des âges : un onglet séparé peut être fourni");
ws2.addRow([]);
addGuideRow(ws2, "Priorités",        "🔴 Critique (A, B) : données indispensables au calcul des indicateurs ODD 1.3.1.\n🟠 Importante (C) : améliorent la rigueur du bulletin.\n🟡 Complémentaire (D, E) : enrichissent le contexte. À fournir si disponibles.");
ws2.addRow([]);
addGuideRow(ws2, "Contact",          "[À compléter — nom, email, téléphone de l'interlocuteur de l'équipe bulletin]", false, JAUNE_NOTE);
ws2.addRow([]);
addGuideRow(ws2, "Date de retour souhaitée", "[À compléter]", false, JAUNE_NOTE);

await wb.xlsx.writeFile("C:/Users/M.Diouf/.copilot/session-state/88a7b822-78e5-45cc-aee2-84b3b4aa94bd/files/Canevas_donnees_INS_Bulletin_PS_RDC.xlsx");
console.log("✅ Fichier Excel généré : Canevas_donnees_INS_Bulletin_PS_RDC.xlsx");
