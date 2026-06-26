import {
  Document, Packer, Paragraph, Table, TableRow, TableCell,
  TextRun, HeadingLevel, AlignmentType, WidthType, ShadingType,
  BorderStyle, TableLayoutType, VerticalAlign, PageOrientation
} from "docx";
import { writeFileSync } from "fs";

// ── Couleurs ──────────────────────────────────────────────────────────────────
const BLEU_TITRE  = "1F3864";
const BLEU_ENTETE = "1F3864";
const BLEU_CLAIR  = "D6E4F0";
const GRIS_PAIR   = "EEF2F8";
const ROUGE       = "C00000";
const ORANGE      = "E07820";
const JAUNE       = "7F7F00";
const JAUNE_NOTE  = "FFF8DC";
const BLANC       = "FFFFFF";

// ── Helpers ───────────────────────────────────────────────────────────────────
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const thinBorder = { style: BorderStyle.SINGLE, size: 4, color: "AAAAAA" };

function titreSection(texte) {
  return new Paragraph({
    text: texte,
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 80 },
    run: { color: BLEU_TITRE, bold: true }
  });
}

function paragraphe(runs, spacing = { before: 60, after: 80 }) {
  return new Paragraph({ children: runs, spacing });
}

function run(texte, opts = {}) {
  return new TextRun({ text: texte, font: "Calibri", size: 22, ...opts });
}

function runB(texte, opts = {}) {
  return run(texte, { bold: true, ...opts });
}

// Cellule d'en-tête de tableau
function cellHeader(texte, width) {
  return new TableCell({
    width: { size: width, type: WidthType.PERCENTAGE },
    shading: { type: ShadingType.SOLID, color: BLEU_ENTETE },
    verticalAlign: VerticalAlign.CENTER,
    borders: { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder },
    children: [new Paragraph({
      children: [new TextRun({ text: texte, bold: true, color: BLANC, font: "Calibri", size: 20 })],
      spacing: { before: 40, after: 40 }
    })]
  });
}

// Cellule de données
function cell(texte, width, pair = false, bold = false, color = null) {
  return new TableCell({
    width: { size: width, type: WidthType.PERCENTAGE },
    shading: pair ? { type: ShadingType.SOLID, color: GRIS_PAIR } : undefined,
    verticalAlign: VerticalAlign.TOP,
    borders: { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder },
    children: [new Paragraph({
      children: [new TextRun({ text: texte, bold, font: "Calibri", size: 20, color: color || "000000" })],
      spacing: { before: 40, after: 40 }
    })]
  });
}

// Ligne de tableau de données
function ligneData(cols, pair) {
  // cols = [{texte, width, bold, color}]
  return new TableRow({
    children: cols.map(c => cell(c.t, c.w, pair, c.b || false, c.c || null))
  });
}

// En-tête d'un tableau de section
function enteteTableau(cols) {
  return new TableRow({
    tableHeader: true,
    children: cols.map(c => cellHeader(c.t, c.w))
  });
}

function buildTable(header, rows) {
  return new Table({
    layout: TableLayoutType.FIXED,
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [
      enteteTableau(header),
      ...rows.map((r, i) => ligneData(r, i % 2 === 1))
    ]
  });
}

// Bloc note fond jaune
function noteBloc(lignes) {
  return new Table({
    layout: TableLayoutType.FIXED,
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [new TableRow({
      children: [new TableCell({
        shading: { type: ShadingType.SOLID, color: JAUNE_NOTE },
        borders: {
          top: { style: BorderStyle.SINGLE, size: 8, color: "C8A800" },
          bottom: { style: BorderStyle.SINGLE, size: 8, color: "C8A800" },
          right: { style: BorderStyle.SINGLE, size: 8, color: "C8A800" },
          left: { style: BorderStyle.THICK, size: 24, color: "C8A800" }
        },
        children: lignes.map(l => new Paragraph({
          children: [new TextRun({ text: l.texte, bold: l.bold || false, font: "Calibri", size: 20 })],
          spacing: { before: 30, after: 30 }
        }))
      })]
    })]
  });
}

// ── Données du document ───────────────────────────────────────────────────────
const COLS_MAIN = [
  { t: "#",             w: 5  },
  { t: "Donnée demandée", w: 35 },
  { t: "Usage dans le bulletin", w: 40 },
  { t: "Désagrégation", w: 10 },
  { t: "Années",        w: 10 },
];

const COLS_SYNTH = [
  { t: "Priorité", w: 18 },
  { t: "Données",  w: 27 },
  { t: "Raison",   w: 55 },
];

const rowsA = [
  [{ t:"A1",w:5 },{ t:"Population totale",w:35,b:true },{ t:"Dénominateur de l'indicateur global ODD 1.3.1 et du sous-indicateur assistance sociale",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024",w:10 }],
  [{ t:"A2",w:5 },{ t:"Population âgée de 0 à 14 ans",w:35,b:true },{ t:"Dénominateur sous-indicateur enfants — proportion d'enfants couverts par une prestation familiale",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024",w:10 }],
  [{ t:"A3",w:5 },{ t:"Population âgée de 0 à 17 ans",w:35,b:true },{ t:"Variante du dénominateur enfants (l'OIT utilise tantôt 0–15, tantôt 0–17 selon les pays)",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024",w:10 }],
  [{ t:"A4",w:5 },{ t:"Nombre de naissances vivantes",w:35,b:true },{ t:"Dénominateur sous-indicateur maternité — proportion de femmes ayant accouché couvertes par une prestation maternité",w:40 },{ t:"—",w:10 },{ t:"2019–2024",w:10 }],
  [{ t:"A5",w:5 },{ t:"Population âgée de 60 ans et plus / Population âgée de 65 ans et plus",w:35,b:true },{ t:"Dénominateur sous-indicateur vieillesse — les deux seuils correspondent aux âges légaux distincts (CNSSAP : 60 ans ; CNSS : 60 ans femmes / 65 ans hommes)",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024",w:10 }],
  [{ t:"A6",w:5 },{ t:"Population active (15 ans et plus)",w:35,b:true },{ t:"Dénominateur sous-indicateurs accidents du travail / maladies professionnelles et cotisants actifs à un régime de retraite",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024 ou dernière année disponible",w:10 }],
  [{ t:"A7",w:5 },{ t:"Nombre de personnes au chômage (définition BIT)",w:35,b:true },{ t:"Dénominateur sous-indicateur chômage — attendu à 0 % en RDC mais doit être documenté",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024 ou dernière année disponible",w:10 }],
  [{ t:"A8",w:5 },{ t:"Population en situation de handicap grave",w:35,b:true },{ t:"Dénominateur sous-indicateur invalidité — l'OIT utilise par défaut une estimation OMS (~3–4 % de la population)",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024 ou dernière année disponible",w:10 }],
];

const rowsB = [
  [{ t:"B1",w:5 },{ t:"Seuil national de pauvreté (CDF par personne et par mois)",w:35,b:true },{ t:"Comparé aux montants unitaires des pensions et des allocations familiales pour évaluer leur adéquation",w:40 },{ t:"—",w:10 },{ t:"2019–2024",w:10 }],
  [{ t:"B2",w:5 },{ t:"Salaire minimum interprofessionnel garanti (SMIG) en CDF par mois",w:35,b:true },{ t:"Ratio pension moyenne / SMIG — mesure de l'adéquation relative des pensions de retraite",w:40 },{ t:"—",w:10 },{ t:"2019–2024",w:10 }],
  [{ t:"B3",w:5 },{ t:"Indice des prix à la consommation (IPC)",w:35,b:true },{ t:"Déflateur pour exprimer les montants de prestations en termes réels dans les séries temporelles",w:40 },{ t:"—",w:10 },{ t:"2019–2024",w:10 }],
];

const rowsC = [
  [{ t:"C1",w:5 },{ t:"Taux d'emploi informel (%)",w:35,b:true },{ t:"Section contexte économique — confirmer ou nuancer la valeur utilisée (~96 % selon estimations modélisées OIT 2020)",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024 ou dernière année disponible",w:10 }],
  [{ t:"C2",w:5 },{ t:"Structure de l'emploi par secteur (agriculture, industrie, services)",w:35,b:true },{ t:"Figure sur la structure de l'emploi dans la section contexte économique",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024 ou dernière année disponible",w:10 }],
  [{ t:"C3",w:5 },{ t:"Effectif des agents de la fonction publique",w:35,b:true },{ t:"Dénominateur légal de la CNSSAP — mesure de l'écart entre agents légalement couverts et cotisants actifs réels (198 399 en 2022)",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024 ou dernière année disponible",w:10 }],
  [{ t:"C4",w:5 },{ t:"Nombre de travailleurs salariés du secteur privé formel",w:35,b:true },{ t:"Dénominateur légal de la CNSS — estimation du taux de couverture par rapport aux assujettis",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024 ou dernière année disponible",w:10 }],
];

const rowsD = [
  [{ t:"D1",w:5 },{ t:"Espérance de vie à la naissance",w:35,b:true },{ t:"Contexte protection vieillesse — durée moyenne de perception des pensions après l'âge légal de la retraite",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024 ou dernière année disponible",w:10 }],
  [{ t:"D2",w:5 },{ t:"Nombre moyen d'enfants par foyer",w:35,b:true },{ t:"Facteur de conversion foyers / enfants pour le calcul des bénéficiaires d'allocations familiales CNSS — paramètre clé du sous-indicateur ODD 1.3.1 enfants",w:40 },{ t:"—",w:10 },{ t:"2019–2024 ou dernière année disponible",w:10 }],
  [{ t:"D3",w:5 },{ t:"Taille moyenne des ménages",w:35,b:true },{ t:"Contexte démographique et calcul des indicateurs de couverture par ménage — conversion entre effectifs de ménages et individus couverts",w:40 },{ t:"—",w:10 },{ t:"2019–2024 ou dernière année disponible",w:10 }],
  [{ t:"D4",w:5 },{ t:"Pyramide des âges — population par tranche d'âge quinquennale",w:35,b:true },{ t:"Figure de contexte démographique et calcul des dénominateurs par groupe d'âge (enfants, actifs, personnes âgées) pour les indicateurs ODD 1.3.1",w:40 },{ t:"Par sexe",w:10 },{ t:"2019–2024 ou dernière année disponible",w:10 }],
];

const rowsE = [
  [{ t:"E1",w:5 },{ t:"PIB nominal en CDF courants",w:35,b:true },{ t:"Calcul du ratio dépenses de protection sociale / PIB",w:40 },{ t:"—",w:10 },{ t:"2019–2024",w:10 }],
  [{ t:"E2",w:5 },{ t:"Taux de pauvreté national (%)",w:35,b:true },{ t:"Contexte économique — confirmation directe INS de la valeur 2024 (69 % citée via la Banque mondiale)",w:40 },{ t:"—",w:10 },{ t:"Enquête 2024",w:10 }],
  [{ t:"E3",w:5 },{ t:"Indice de Gini",w:35,b:true },{ t:"Contexte inégalités — confirmation de la valeur INS 2024 (0,381), non encore intégrée dans les bases internationales",w:40 },{ t:"—",w:10 },{ t:"Enquête 2024",w:10 }],
];

const rowsSynth = [
  [{ t:"🔴 Critique",w:18,b:true,c:ROUGE   },{ t:"A1 à A8 — B1, B2, B3",w:27 },{ t:"Sans ces données, les indicateurs ODD 1.3.1 ne peuvent pas être calculés ou restent des estimations non vérifiables.",w:55 }],
  [{ t:"🟠 Importante",w:18,b:true,c:ORANGE },{ t:"C1 à C4",w:27 },{ t:"Améliorent la rigueur du bulletin en remplaçant les estimations modélisées extérieures par des données nationales directes.",w:55 }],
  [{ t:"🟡 Complémentaire",w:18,b:true,c:JAUNE  },{ t:"D1 à D3 — E1 à E3",w:27 },{ t:"Enrichissent le contexte et les analyses géographiques. Intégrées si disponibles dans les délais.",w:55 }],
];

// ── Construction du document ──────────────────────────────────────────────────
const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Calibri", size: 22 }
      }
    },
    paragraphStyles: [
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        run: { bold: true, color: BLEU_TITRE, size: 26, font: "Calibri" },
        paragraph: { spacing: { before: 280, after: 80 } }
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { orientation: PageOrientation.LANDSCAPE, width: 15840, height: 12240 },
        margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 }
      }
    },
    children: [

      // ── Titre ──
      new Paragraph({
        children: [
          runB("Demande de données statistiques", { color: BLEU_TITRE, size: 32 }),
          new TextRun({ text: "\nà l'Institut National de la Statistique (INS)", bold: true, color: BLEU_TITRE, size: 28, font: "Calibri", break: 0 })
        ],
        spacing: { before: 0, after: 200 }
      }),

      // ── Bloc objet ──
      new Table({
        layout: TableLayoutType.FIXED,
        width: { size: 100, type: WidthType.PERCENTAGE },
        rows: [new TableRow({
          children: [new TableCell({
            shading: { type: ShadingType.SOLID, color: "EBF3FB" },
            borders: { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder },
            children: [
              new Paragraph({ children: [runB("Objet : "), run("Données nécessaires à la préparation du deuxième Bulletin statistique sur la protection sociale en RDC")], spacing: { before: 40, after: 20 } }),
              new Paragraph({ children: [runB("Date : "), run("Juin 2026")], spacing: { before: 20, after: 20 } }),
              new Paragraph({ children: [runB("Demandeur : "), run("[À compléter]")], spacing: { before: 20, after: 20 } }),
              new Paragraph({ children: [runB("Contact INS : "), run("[À compléter]")], spacing: { before: 20, after: 40 } }),
            ]
          })]
        })]
      }),

      new Paragraph({ text: "", spacing: { before: 100, after: 0 } }),

      // ── Intro ──
      paragraphe([
        run("Dans le cadre de la préparation du deuxième Bulletin statistique sur la protection sociale en RDC, nous sollicitons auprès de l'INS un ensemble de données servant de "),
        runB("dénominateurs"),
        run(" pour le calcul des indicateurs ODD 1.3.1 (taux de couverture de la protection sociale) et de "),
        runB("données de contexte"),
        run(" pour les sections démographique et économique du bulletin.")
      ]),

      // ── Note ──
      noteBloc([
        { texte: "Précisions sur le format souhaité :", bold: true },
        { texte: "• Les données de population sont attendues en valeur annuelle (au 1er juillet ou au 31 décembre de chaque année)." },
        { texte: "• Pour les données issues d'enquêtes ménages, merci de joindre les éléments méthodologiques de base (enquête source, période de collecte, couverture géographique)." },
        { texte: "• Pour le seuil de pauvreté, la valeur souhaitée est exprimée par tête et par mois en CDF." },
        { texte: "• Années de référence souhaitées : 2019 à 2024 (et 2025 si disponible)." },
      ]),

      new Paragraph({ text: "", spacing: { before: 120, after: 0 } }),

      // ── Section A ──
      new Paragraph({ children: [runB("A — Dénominateurs pour le calcul des indicateurs ODD 1.3.1", { color: BLEU_TITRE, size: 26 })], spacing: { before: 200, after: 60 }, pageBreakBefore: true, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLEU_TITRE } } }),
      paragraphe([runB("Priorité critique", { color: ROUGE }), run(" — Ces données conditionnent directement le calcul des taux de couverture.")]),
      buildTable(COLS_MAIN, rowsA),

      // ── Section B ──
      new Paragraph({ children: [runB("B — Seuils de référence pour l'adéquation des prestations", { color: BLEU_TITRE, size: 26 })], spacing: { before: 200, after: 60 }, pageBreakBefore: true, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLEU_TITRE } } }),
      paragraphe([runB("Priorité critique", { color: ROUGE }), run(" — Ces données permettent de mesurer si les pensions et allocations couvrent les besoins de base.")]),
      buildTable(COLS_MAIN, rowsB),

      // ── Section C ──
      new Paragraph({ children: [runB("C — Structure du marché du travail", { color: BLEU_TITRE, size: 26 })], spacing: { before: 200, after: 60 }, pageBreakBefore: true, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLEU_TITRE } } }),
      paragraphe([runB("Priorité importante", { color: ORANGE }), run(" — Complètent les estimations modélisées de l'OIT avec des données nationales directes.")]),
      buildTable(COLS_MAIN, rowsC),

      // ── Section D ──
      new Paragraph({ children: [runB("D — Données démographiques et état civil", { color: BLEU_TITRE, size: 26 })], spacing: { before: 200, after: 60 }, pageBreakBefore: true, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLEU_TITRE } } }),
      paragraphe([runB("Priorité complémentaire", { color: "7F7F00" }), run(" — Utiles pour les analyses contextuelles et la vérification des dénominateurs.")]),
      buildTable(COLS_MAIN, rowsD),

      // ── Section E ──
      new Paragraph({ children: [runB("E — Données économiques nationales", { color: BLEU_TITRE, size: 26 })], spacing: { before: 200, after: 60 }, pageBreakBefore: true, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLEU_TITRE } } }),
      paragraphe([runB("Priorité complémentaire", { color: "7F7F00" }), run(" — Certaines de ces données peuvent relever de la BCC ou du Ministère des Finances.")]),
      buildTable(COLS_MAIN, rowsE),

      // ── Synthèse ──
      new Paragraph({ children: [runB("Synthèse des priorités", { color: BLEU_TITRE, size: 26 })], spacing: { before: 200, after: 60 }, pageBreakBefore: true, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLEU_TITRE } } }),
      buildTable(COLS_SYNTH, rowsSynth),

      // ── Pied de page ──
      new Paragraph({
        children: [run("Document préparé dans le cadre du deuxième Bulletin statistique sur la protection sociale en RDC — Juin 2026", { color: "666666", size: 18 })],
        spacing: { before: 240, after: 0 },
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC" } }
      }),
    ]
  }]
});

const buffer = await Packer.toBuffer(doc);
writeFileSync("Demande_donnees_INS_Bulletin_PS_RDC.docx", buffer);
console.log("✅ Fichier généré : Demande_donnees_INS_Bulletin_PS_RDC.docx");

