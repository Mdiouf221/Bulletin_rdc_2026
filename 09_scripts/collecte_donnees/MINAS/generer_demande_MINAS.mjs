/**
 * Génère la lettre de demande de données au MINAS (Word .docx)
 * Bulletin statistique de la protection sociale en RDC — 2e édition
 *
 * Usage : node generer_demande_MINAS.mjs
 * Lancer APRÈS avoir validé le HTML (generer_html_MINAS.mjs)
 */

import path from 'path';
import { fileURLToPath } from 'url';
import {
  Document, Packer, Paragraph, Table, TableRow, TableCell,
  TextRun, AlignmentType, WidthType, BorderStyle,
  PageOrientation, ShadingType, VerticalAlign,
} from 'docx';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUTPUT_PATH = path.resolve(
  __dirname,
  '../../../10_output/collecte_donnees/MINAS/Demande_donnees_MINAS_Bulletin_PS_RDC.docx'
);

// ─── Couleurs ──────────────────────────────────────────────────────────────────
const BLEU    = '1F3864';
const BLEU_TH = '2E5E8E';
const GRIS_S  = 'D9E1F2';  // fond sous-titre de groupe (neutre)
const BLANC   = 'FFFFFF';

// ─── Helpers texte ─────────────────────────────────────────────────────────────
const bold   = (text, size = 20) => new TextRun({ text, bold: true,   size, font: 'Calibri' });
const normal = (text, size = 19) => new TextRun({ text,               size, font: 'Calibri' });
const italic = (text, size = 18) => new TextRun({ text, italics: true, size, font: 'Calibri', color: '595959' });

// ─── Helpers cellule ───────────────────────────────────────────────────────────
const thinBorder = { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' };

const cell = (text, opts = {}) =>
  new TableCell({
    children: [new Paragraph({
      children: [new TextRun({
        text,
        bold: opts.bold || false,
        italics: opts.italic || false,
        size: opts.size || 18,
        font: 'Calibri',
        color: opts.color || '000000',
      })],
      alignment: opts.align || AlignmentType.LEFT,
    })],
    shading: opts.bg ? { fill: opts.bg, type: ShadingType.CLEAR, color: 'auto' } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 55, bottom: 55, left: 100, right: 100 },
    columnSpan: opts.span || 1,
  });

// En-tête de tableau (fond bleu)
const th = (cols) =>
  new TableRow({
    tableHeader: true,
    children: cols.map(c => new TableCell({
      children: [new Paragraph({
        children: [new TextRun({ text: c, bold: true, size: 17, font: 'Calibri', color: BLANC })],
        alignment: AlignmentType.CENTER,
      })],
      shading: { fill: BLEU_TH, type: ShadingType.CLEAR, color: 'auto' },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 60, bottom: 60, left: 80, right: 80 },
    })),
  });

// Séparateur de groupe (fond gris neutre, sur toutes les colonnes)
const groupRow = (label, nbCols) =>
  new TableRow({
    children: [new TableCell({
      children: [new Paragraph({
        children: [new TextRun({ text: label, bold: true, size: 18, font: 'Calibri', color: BLEU })],
        alignment: AlignmentType.LEFT,
      })],
      shading: { fill: GRIS_S, type: ShadingType.CLEAR, color: 'auto' },
      columnSpan: nbCols,
      margins: { top: 70, bottom: 70, left: 120, right: 120 },
    })],
  });

// Ligne de données
const dr = (cells) =>
  new TableRow({
    children: cells.map(c => new TableCell({
      children: [new Paragraph({
        children: [new TextRun({
          text: c.text || '',
          bold: c.bold || false,
          italics: c.italic || false,
          size: 18,
          font: 'Calibri',
          color: c.color || '000000',
        })],
        alignment: c.align || AlignmentType.LEFT,
      })],
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 50, bottom: 50, left: 100, right: 100 },
      columnSpan: c.span || 1,
    })),
  });

const makeTable = (rows, widths) =>
  new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder, insideH: thinBorder, insideV: thinBorder },
    columnWidths: widths,
    rows,
  });

// ═══════════════════════════════════════════════════════════════════════════════
// DOCUMENT
// ═══════════════════════════════════════════════════════════════════════════════
const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { orientation: PageOrientation.LANDSCAPE, width: 15840, height: 12240 },
        margin: { top: 720, bottom: 720, left: 900, right: 900 },
      },
    },
    children: [

      // ── PAGE DE GARDE ──────────────────────────────────────────────────────────
      new Paragraph({ children: [bold('', 20)], spacing: { after: 400 } }),
      new Paragraph({
        children: [bold('MINISTÈRE DE L\'EMPLOI, TRAVAIL ET PRÉVOYANCE SOCIALE', 26)],
        alignment: AlignmentType.CENTER, spacing: { after: 60 },
      }),
      new Paragraph({
        children: [normal('Direction des Études et Planification', 20)],
        alignment: AlignmentType.CENTER, spacing: { after: 600 },
      }),
      new Paragraph({
        children: [bold('DEMANDE DE DONNÉES', 40)],
        alignment: AlignmentType.CENTER, spacing: { after: 160 },
      }),
      new Paragraph({
        children: [bold('Bulletin statistique de la protection sociale en RDC — 2e édition', 28)],
        alignment: AlignmentType.CENTER, spacing: { after: 80 },
      }),
      new Paragraph({
        children: [bold('Données relatives aux programmes d\'assistance sociale et transferts sociaux', 24)],
        alignment: AlignmentType.CENTER, spacing: { after: 80 },
      }),
      new Paragraph({
        children: [italic('À l\'attention du Ministère des Affaires Sociales, Action Humanitaire\net Solidarité Nationale (MINAS)', 22)],
        alignment: AlignmentType.CENTER, spacing: { after: 600 },
      }),
      new Paragraph({
        children: [normal('Période de référence : 2019–2024 (ou dernière année disponible)', 20)],
        alignment: AlignmentType.CENTER, spacing: { after: 80 },
      }),
      new Paragraph({
        children: [normal('Date d\'émission : juillet 2026', 20)],
        alignment: AlignmentType.CENTER, spacing: { after: 1000 },
      }),
      new Paragraph({
        children: [italic(
          'Ce document fait partie d\'une série de demandes de données adressées aux institutions partenaires\n' +
          'dans le cadre de la production du deuxième Bulletin statistique de la protection sociale en RDC.',
          18)],
        alignment: AlignmentType.CENTER, spacing: { after: 400 },
      }),

      // ── CONTEXTE ───────────────────────────────────────────────────────────────
      new Paragraph({
        children: [bold('1. CONTEXTE ET OBJET DE LA DEMANDE', 22)],
        pageBreakBefore: true, spacing: { after: 200 },
      }),
      new Paragraph({
        children: [normal(
          'Le Ministère de l\'Emploi, du Travail et de la Prévoyance Sociale (METPS), avec l\'appui du Bureau international du Travail (BIT/OIT), ' +
          'produit le deuxième Bulletin statistique de la protection sociale en République Démocratique du Congo. Ce bulletin documente l\'état de la couverture ' +
          'de protection sociale dans le pays, en référence aux indicateurs ODD 1.3.1 et aux conventions de l\'OIT.',
        )], spacing: { after: 160 },
      }),
      new Paragraph({
        children: [normal(
          'Le MINAS constitue une source de données indispensable pour renseigner la composante "protection sociale non contributive" du bulletin, ' +
          'et plus particulièrement les programmes bénéficiant aux ménages pauvres, aux enfants, aux personnes handicapées et aux personnes âgées sans pension. ' +
          'La présente demande vise à obtenir une cartographie officielle des programmes d\'assistance sociale et les données statistiques associées.',
        )], spacing: { after: 160 },
      }),
      new Paragraph({
        children: [italic(
          'Note : La distinction entre programmes gouvernementaux (financés sur ressources propres) et programmes mis en œuvre en partenariat avec des ' +
          'organisations internationales est importante pour le bulletin. Merci d\'indiquer clairement cette distinction pour chaque programme.',
        )], spacing: { after: 200 },
      }),

      // ── SECTION A ──────────────────────────────────────────────────────────────
      new Paragraph({
        children: [bold('SECTION A — CARTOGRAPHIE DES PROGRAMMES (Priorité haute)', 22)],
        pageBreakBefore: true, spacing: { after: 120 },
      }),
      new Paragraph({
        children: [italic(
          'Veuillez lister l\'ensemble des programmes d\'assistance sociale actifs ou récents (2019–2024), y compris ceux conduits en partenariat avec le PAM, l\'UNICEF, ' +
          'la Banque mondiale ou d\'autres organisations. Les lignes pré-renseignées sont indicatives — elles doivent être corrigées, complétées ou supprimées selon la réalité.',
        )], spacing: { after: 160 },
      }),
      makeTable([
        th(['Réf.', 'Nom officiel du programme', 'Type de prestation', 'Population cible', 'Financement principal', 'Responsable mise en œuvre', 'Année début', 'Statut']),
        groupRow('Programmes avec partenaires internationaux (PAM, UNICEF, Banque mondiale…)', 8),
        dr([{ text: 'A1.1' }, { text: 'PAM — Transferts de ressources sans conditions (TRC)', bold: true }, { text: 'Espèces et alimentaire' }, { text: 'Ménages en insécurité alimentaire, déplacés internes' }, { text: 'PAM / Donateurs internationaux' }, { text: 'PAM' }, { text: '~2000s' }, { text: 'Actif' }]),
        dr([{ text: 'A1.2' }, { text: 'PAM — Cantines scolaires', bold: true }, { text: 'Nature (repas scolaires)' }, { text: 'Enfants scolarisés (écoles primaires publiques)' }, { text: 'PAM + MEPST' }, { text: 'PAM' }, { text: '2023 (pilote)' }, { text: 'Actif (pilote)' }]),
        dr([{ text: 'A1.3' }, { text: 'UNICEF — Cash + Nutrition', bold: true }, { text: 'Espèces + nutrition' }, { text: 'Enfants malnutris, ménages vulnérables' }, { text: 'UNICEF + donateurs' }, { text: 'UNICEF' }, { text: '~2021' }, { text: 'Actif (intermittent)' }]),
        dr([{ text: 'A1.4' }, { text: 'STEP / Banque mondiale (IDA)', bold: true }, { text: 'Transferts conditionnels' }, { text: 'Ménages extrêmement pauvres (Kasaï, Lomami, Kwilu)' }, { text: 'Banque mondiale / IDA' }, { text: 'Banque mondiale' }, { text: '~2018' }, { text: 'Clôturé (fév. 2024)' }]),
        dr([{ text: 'A1.5' }, { text: '[À renseigner par le MINAS]', italic: true, color: '595959' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }]),
        groupRow('Programmes gouvernementaux MINAS', 8),
        dr([{ text: 'A2.1' }, { text: '[À renseigner par le MINAS]', italic: true, color: '595959' }, { text: '' }, { text: '' }, { text: 'Gouvernement RDC' }, { text: 'MINAS' }, { text: '' }, { text: '' }]),
        dr([{ text: 'A2.2' }, { text: '[À renseigner par le MINAS]', italic: true, color: '595959' }, { text: '' }, { text: '' }, { text: 'Gouvernement RDC' }, { text: 'MINAS' }, { text: '' }, { text: '' }]),
        dr([{ text: 'A2.3' }, { text: '[À renseigner par le MINAS]', italic: true, color: '595959' }, { text: '' }, { text: '' }, { text: 'Gouvernement RDC' }, { text: 'MINAS' }, { text: '' }, { text: '' }]),
        groupRow('Programmes pour personnes handicapées', 8),
        dr([{ text: 'A3.1' }, { text: '[À renseigner par le MINAS]', italic: true, color: '595959' }, { text: '' }, { text: 'Personnes handicapées' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }]),
        dr([{ text: 'A3.2' }, { text: '[À renseigner par le MINAS]', italic: true, color: '595959' }, { text: '' }, { text: 'Personnes handicapées' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }]),
        groupRow('Programmes pour personnes âgées sans pension', 8),
        dr([{ text: 'A4.1' }, { text: '[À renseigner par le MINAS]', italic: true, color: '595959' }, { text: '' }, { text: 'Personnes âgées (60 ans ou plus)' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }]),
        groupRow('Autres programmes', 8),
        dr([{ text: 'A5.1' }, { text: '[À renseigner par le MINAS]', italic: true, color: '595959' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }]),
        dr([{ text: 'A5.2' }, { text: '[À renseigner par le MINAS]', italic: true, color: '595959' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }, { text: '' }]),
      ], [700, 3200, 2000, 2800, 2200, 2200, 1200, 1300]),

      // ── SECTION B ──────────────────────────────────────────────────────────────
      new Paragraph({
        children: [bold('SECTION B — BÉNÉFICIAIRES PAR PRESTATION (Priorité haute)', 22)],
        pageBreakBefore: true, spacing: { after: 120 },
      }),
      new Paragraph({
        children: [italic(
          'Pour chaque programme identifié en Section A, veuillez indiquer le nombre de bénéficiaires effectifs (personnes ayant reçu une prestation au moins une fois dans l\'année), ' +
          'ventilé par sexe si disponible. Données demandées pour 2019–2024 ou la dernière année disponible.',
        )], spacing: { after: 160 },
      }),
      makeTable([
        th(['Réf.', 'Programme', 'Description de la prestation\n(espèces / nature / mixte)', 'Public cible', 'Indicateur', 'Désagrég.', 'Années disponibles']),
        dr([{ text: 'B1.1' }, { text: 'PAM — TRC' }, { text: 'Transferts en espèces et alimentaires inconditionnels' }, { text: 'Ménages en insécurité alimentaire, déplacés internes' }, { text: 'Nombre de bénéficiaires (personnes)' }, { text: 'Par sexe' }, { text: '2019–2024 ou dernière année disponible' }]),
        dr([{ text: 'B1.2' }, { text: 'PAM — TRC' }, { text: 'Transferts en espèces et alimentaires inconditionnels' }, { text: 'Ménages en insécurité alimentaire, déplacés internes' }, { text: 'Nombre de ménages bénéficiaires' }, { text: '—' }, { text: '2019–2024 ou dernière année disponible' }]),
        dr([{ text: 'B1.3' }, { text: 'PAM — Cantines scolaires' }, { text: 'Repas scolaires (nature)' }, { text: 'Enfants scolarisés (écoles primaires publiques)' }, { text: 'Nombre d\'enfants bénéficiaires' }, { text: 'Par sexe' }, { text: '2023–2024 (pilote)' }]),
        dr([{ text: 'B2.1' }, { text: 'UNICEF — Cash + Nutrition' }, { text: 'Transferts en espèces + soutien nutritionnel (mixte)' }, { text: 'Enfants malnutris, ménages vulnérables' }, { text: 'Nombre de bénéficiaires (personnes)' }, { text: 'Par sexe' }, { text: '2019–2024 ou dernière année disponible' }]),
        dr([{ text: 'B2.2' }, { text: 'UNICEF — Cash + Nutrition' }, { text: 'Transferts en espèces + soutien nutritionnel (mixte)' }, { text: 'Enfants malnutris, ménages vulnérables' }, { text: 'Nombre de ménages bénéficiaires' }, { text: '—' }, { text: '2019–2024 ou dernière année disponible' }]),
        dr([{ text: 'B3.1' }, { text: 'STEP / Banque mondiale' }, { text: 'Transferts monétaires conditionnels (espèces)' }, { text: 'Ménages extrêmement pauvres (Kasaï, Lomami, Kwilu)' }, { text: 'Ménages bénéficiaires' }, { text: '—' }, { text: '2019–2024 (selon disponibilité)' }]),
        dr([{ text: 'B3.2' }, { text: 'STEP / Banque mondiale' }, { text: 'Transferts monétaires conditionnels (espèces)' }, { text: 'Ménages extrêmement pauvres (Kasaï, Lomami, Kwilu)' }, { text: 'Personnes couvertes (ménages × taille moy.)' }, { text: 'Par sexe chef mén.' }, { text: '2019–2024 (selon disponibilité)' }]),
        dr([{ text: 'B4.1' }, { text: '[Programme MINAS 1]', italic: true, color: '595959' }, { text: '[À renseigner]', italic: true, color: '595959' }, { text: '[À renseigner]', italic: true, color: '595959' }, { text: 'Nombre de bénéficiaires (personnes)' }, { text: 'Par sexe' }, { text: '2019–2024 ou dernière année disponible' }]),
        dr([{ text: 'B4.2' }, { text: '[Programme MINAS 2]', italic: true, color: '595959' }, { text: '[À renseigner]', italic: true, color: '595959' }, { text: '[À renseigner]', italic: true, color: '595959' }, { text: 'Nombre de bénéficiaires (personnes)' }, { text: 'Par sexe' }, { text: '2019–2024 ou dernière année disponible' }]),
        dr([{ text: 'B5.1' }, { text: '[Programme personnes handicapées]', italic: true, color: '595959' }, { text: '[À renseigner]', italic: true, color: '595959' }, { text: 'Personnes handicapées' }, { text: 'Bénéficiaires enregistrés' }, { text: 'Par sexe' }, { text: '2019–2024 ou dernière année disponible' }]),
        dr([{ text: 'B5.2' }, { text: '[Programme personnes handicapées]', italic: true, color: '595959' }, { text: '[À renseigner]', italic: true, color: '595959' }, { text: 'Personnes handicapées' }, { text: 'Bénéficiaires ayant reçu une prestation' }, { text: 'Par sexe' }, { text: '2019–2024 ou dernière année disponible' }]),
        dr([{ text: 'B6.1' }, { text: '[Programme personnes âgées]', italic: true, color: '595959' }, { text: '[À renseigner]', italic: true, color: '595959' }, { text: 'Personnes âgées (60 ans et plus)' }, { text: 'Bénéficiaires (personnes 60 ans et plus)' }, { text: 'Par sexe' }, { text: '2019–2024 ou dernière année disponible' }]),
      ], [700, 2600, 2800, 2500, 2800, 1500, 2700]),

      // ── SECTION C ──────────────────────────────────────────────────────────────
      new Paragraph({
        children: [bold('SECTION C — DONNÉES FINANCIÈRES (Priorité haute)', 22)],
        pageBreakBefore: true, spacing: { after: 120 },
      }),
      new Paragraph({
        children: [italic(
          'Pour chaque programme, veuillez indiquer les dépenses de prestations (montants effectivement versés aux bénéficiaires) et les transferts moyens par bénéficiaire. ' +
          'L\'unité monétaire préférée est le franc congolais (CDF) courant.',
        )], spacing: { after: 160 },
      }),
      makeTable([
        th(['Réf.', 'Programme', 'Indicateur financier', 'Unité', 'Années disponibles', 'Notes']),
        groupRow('Dépenses totales de prestations', 6),
        dr([{ text: 'C1.1' }, { text: 'Tous programmes MINAS' }, { text: 'Total dépenses de prestations en espèces (versements directs)' }, { text: 'CDF ou USD' }, { text: '2019–2024' }, { text: '' }]),
        dr([{ text: 'C1.2' }, { text: 'Tous programmes MINAS' }, { text: 'Total dépenses de prestations en nature (valeur estimée)' }, { text: 'CDF ou USD' }, { text: '2019–2024' }, { text: '' }]),
        dr([{ text: 'C1.3' }, { text: 'PAM — TRC (via MINAS)' }, { text: 'Montant total des transferts (si disponible auprès du MINAS)' }, { text: 'USD' }, { text: '2019–2024' }, { text: 'À défaut : source directe PAM' }]),
        groupRow('Montant moyen par bénéficiaire', 6),
        dr([{ text: 'C2.1' }, { text: 'PAM — TRC' }, { text: 'Transfert moyen mensuel par ménage bénéficiaire' }, { text: 'USD ou CDF' }, { text: '2019–2024' }, { text: '' }]),
        dr([{ text: 'C2.2' }, { text: 'STEP / Banque mondiale' }, { text: 'Transfert moyen mensuel par ménage bénéficiaire' }, { text: 'USD ou CDF' }, { text: '2019–2024' }, { text: '' }]),
        dr([{ text: 'C2.3' }, { text: '[Programme gouvernemental MINAS]', italic: true, color: '595959' }, { text: 'Prestation ou transfert moyen par bénéficiaire' }, { text: 'CDF ou USD' }, { text: '2019–2024' }, { text: '' }]),
      ], [700, 3200, 4200, 1500, 2400, 2300]),

      // ── MODALITÉS DE RÉPONSE ───────────────────────────────────────────────────
      new Paragraph({
        children: [bold('2. MODALITÉS DE RÉPONSE', 22)],
        pageBreakBefore: true, spacing: { after: 160 },
      }),
      new Paragraph({
        children: [normal(
          'Nous vous remercions de bien vouloir compléter le canevas Excel joint à ce document et de le retourner à l\'adresse suivante avant le [date limite à préciser].',
        )], spacing: { after: 120 },
      }),
      new Paragraph({
        children: [bold('Contact principal : ', 20), normal('[Nom du point focal — METPS / BIT] — [email@exemple.org] — [Tél.]', 20)],
        spacing: { after: 120 },
      }),
      new Paragraph({
        children: [normal(
          'Pour toute question relative à cette demande ou aux modalités de transmission des données, veuillez contacter directement le point focal ci-dessus. ' +
          'Une réunion de clarification peut être organisée sur demande.',
        )], spacing: { after: 200 },
      }),
      new Paragraph({
        children: [italic(
          'Ce document a été produit dans le cadre du Programme BIT/OIT d\'appui au développement du système national de protection sociale en RDC.',
        )],
        alignment: AlignmentType.CENTER, spacing: { before: 400 },
      }),

    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });
  fs.writeFileSync(OUTPUT_PATH, buffer);
  console.log(`✅ Word généré : ${OUTPUT_PATH}`);
});
