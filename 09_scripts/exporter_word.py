"""
exporter_word.py
----------------
Convertit le bulletin HTML en fichier Word (.docx) via Pandoc.

Usage :
    py 09_scripts/exporter_word.py
    py 09_scripts/exporter_word.py 10_output/bulletin_relecture_2026-06-26.html

Le fichier .docx est généré dans 10_output/ avec le même nom de base
que le fichier HTML source.

Ajustements appliqués avant conversion (corrections HTML) :
    [HR-001]  Suppression des balises <hr> (barres horizontales inter-chapitres)
    [NAV-001] Extraction du contenu div#content (supprime toc-panel, export-header, scripts JS)
    [IMG-001] Correction des chemins des images /files/08_figures/... → chemins absolus
    [LNK-001] Conversion des annotations source-ref en notes de bas de page
    [TAB-001] Bordures complètes sur tous les tableaux (via filtre Lua table_borders.lua)
    [TAB-002] Autofit to Window sur tous les tableaux (post-traitement python-docx)
    [STY-001] Suppression éléments UI, styles cellules tableau (via filtre Lua style_mapping.lua)
    [STY-002] Conversion blockquote.fig-block / p.fig-caption / p.fig-source
              / p.table-caption / p.table-source en custom-style Pandoc
    [STY-003] Style Body Text par défaut sur tous les paragraphes ordinaires
"""

import subprocess
import re
import os
import sys
import glob

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, "10_output")
FIG_DIR    = os.path.join(ROOT, "08_figures", "exports")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Template Word contenant tous les styles ILO/bulletin (généré depuis le fichier de référence)
REF_DOCX = os.path.join(SCRIPTS_DIR, "template_bulletin.docx")

LUA_FILTER      = os.path.join(SCRIPTS_DIR, "table_borders.lua")
LUA_FOOTNOTES   = os.path.join(SCRIPTS_DIR, "footnotes.lua")
LUA_STYLES      = os.path.join(SCRIPTS_DIR, "style_mapping.lua")

# Localiser pandoc (PATH ou emplacement connu sur Windows)
def _find_pandoc():
    import shutil
    found = shutil.which("pandoc")
    if found:
        return found
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Pandoc", "pandoc.exe"),
        r"C:\Program Files\Pandoc\pandoc.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    sys.exit("Pandoc introuvable. Installer depuis https://pandoc.org ou l'ajouter au PATH.")

PANDOC = _find_pandoc()


def find_latest_html():
    """Retourne le fichier HTML bulletin_relecture le plus récent dans 10_output."""
    pattern = os.path.join(OUTPUT_DIR, "bulletin_relecture_*.html")
    files = glob.glob(pattern)
    if not files:
        sys.exit("Aucun fichier bulletin_relecture_*.html trouvé dans 10_output/")
    return max(files, key=os.path.getmtime)


# ---------------------------------------------------------------------------
# Corrections HTML appliquées avant conversion
# ---------------------------------------------------------------------------

def apply_corrections(html: str) -> str:
    """
    Applique toutes les corrections HTML avant l'export Word.
    Ajouter ici les nouveaux correctifs au fil des retours.
    """

    # [HR-001] Suppression des barres horizontales inter-chapitres
    html = re.sub(r'<hr\s*/?>', '', html)

    # [NAV-001] Extraction du contenu utile uniquement (div#content)
    # Le HTML du serveur contient toc-panel, export-header, status-legend,
    # scripts JS, etc. On extrait uniquement le contenu de div#content
    # en comptant les imbrications de divs.
    m_start = re.search(r'<div\s+id="content">', html)
    if m_start:
        depth = 1
        pos = m_start.end()
        while pos < len(html) and depth > 0:
            next_open  = html.find('<div', pos)
            next_close = html.find('</div>', pos)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + 4
            else:
                depth -= 1
                if depth == 0:
                    html = '<html><body>' + html[m_start.end():next_close] + '</body></html>'
                    break
                pos = next_close + 6

    # [INT-001] Aucun commentaire HTML ni bloc interne ne doit être transmis
    # au document Word, même si l'export part d'une version de travail.
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    html = re.sub(
        r'<(?P<tag>p|div|span)\b[^>]*class="[^"]*\b(?:dev-note|a-rediger)\b[^"]*"[^>]*>'
        r'.*?</(?P=tag)>',
        '',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Supprimer les badges de validation (span.valid-badge) du texte des titres
    html = re.sub(r'<span[^>]*class="valid-badge[^"]*"[^>]*>.*?</span>', '', html, flags=re.DOTALL)

    # [IMG-001] Résoudre toutes les images servies par la route /files/.
    def fix_img(m):
        relative_path = m.group(1)[len("/files/"):].replace("/", os.sep)
        abs_path = os.path.abspath(os.path.join(ROOT, relative_path))
        if os.path.commonpath((ROOT, abs_path)) != ROOT:
            return m.group(0)
        abs_path = abs_path.replace("\\", "/")
        return m.group(0).replace(m.group(1), abs_path)
    html = re.sub(r'src="(/files/[^"]+)"', fix_img, html)

    # [LNK-001] Conversion des annotations source-ref en notes de bas de page
    # Structure HTML : <a href="#" data-offline="true" title="Source : ..." ...>texte</a>
    # Résultat Word  : texte[^n]  avec footnote = contenu du title
    # Pandoc reconnaît la syntaxe Markdown [texte]^[note] mais on travaille en HTML.
    # On utilise la syntaxe HTML footnote de Pandoc : <span class="footnote">note</span>
    # injectée juste après le texte de l'ancre.
    def source_ref_to_footnote(m):
        title = m.group(1).strip()
        text  = m.group(2).strip()
        # Nettoyer le texte de l'ancre des balises HTML internes éventuelles
        text_clean = re.sub(r'<[^>]+>', '', text)
        # Générer : texte + footnote inline Pandoc (format HTML → docx)
        return '{}<span class="footnote">{}</span>'.format(text_clean, title)

    html = re.sub(
        r'<a\s[^>]*data-offline="true"[^>]*title="([^"]*)"[^>]*>(.*?)</a>',
        source_ref_to_footnote,
        html,
        flags=re.DOTALL
    )

    # Supprimer les autres liens non-ancres (fichiers .md, chemins relatifs)
    # en gardant uniquement les vraies ancres internes (#section-id)
    def strip_non_anchor_link(m):
        href = m.group(1)
        text = m.group(2)
        if href.startswith('#') and len(href) > 1:
            return m.group(0)  # ancre TOC valide — on garde
        return text  # tout le reste — texte seul
    html = re.sub(
        r'<a\s[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        strip_non_anchor_link,
        html,
        flags=re.DOTALL
    )

    # [STY-002] Conversion des classes CSS en attributs custom-style Pandoc
    # Pandoc ignore les class= sur les <p> directement. On wrape chaque
    # élément stylé dans un <div custom-style="..."> que Pandoc respecte.

    # Titres de figure — convention historique (blockquote.fig-block → GraphicTitle)
    html = re.sub(
        r'<blockquote class="fig-block">(.*?)</blockquote>',
        r'<div custom-style="GraphicTitle">\1</div>',
        html, flags=re.DOTALL
    )

    # Titres de figure — convention courante (p.fig-caption → GraphicTitle)
    html = re.sub(
        r'<p class="fig-caption">(.*?)</p>',
        r'<div custom-style="GraphicTitle"><p>\1</p></div>',
        html, flags=re.DOTALL
    )

    # Source sous figure ou tableau (p.fig-source → Source - GraphicPicture)
    html = re.sub(
        r'<p class="fig-source">(.*?)</p>',
        r'<div custom-style="Source - GraphicPicture"><p>\1</p></div>',
        html, flags=re.DOTALL
    )

    # Légende de tableau (p.table-caption → TableTitle)
    html = re.sub(
        r'<p class="table-caption">(.*?)</p>',
        r'<div custom-style="TableTitle"><p>\1</p></div>',
        html, flags=re.DOTALL
    )

    # Source sous tableau (p.table-source → Source - GraphicPicture, même style que figures)
    html = re.sub(
        r'<p class="table-source">(.*?)</p>',
        r'<div custom-style="Source - GraphicPicture"><p>\1</p></div>',
        html, flags=re.DOTALL
    )

    # [STY-004] Légende inline de tableau (*Légende : ...* ou *Note : ...* juste sous un tableau)
    # En Markdown, une ligne *Légende...* produit <p><em>Légende...</em></p> sans classe.
    # On la détecte par son contenu et on applique TableNoteSource.
    html = re.sub(
        r'<p><em>((?:L[ée]gende|Note\b|Remarque\b|NB\b).*?)</em></p>',
        r'<div custom-style="TableNoteSource"><p><em>\1</em></p></div>',
        html, flags=re.DOTALL | re.IGNORECASE
    )

    # [STY-005] Bloc source/note de tableau (div.table-sources → TableNoteSource)
    # Le <small> wrapper est retiré car le style gère la taille de police.
    def _replace_table_sources(m):
        inner = m.group(1).strip()
        inner = re.sub(r'^\s*<small>(.*)</small>\s*$', r'\1', inner, flags=re.DOTALL)
        return '<div custom-style="TableNoteSource"><p>' + inner.strip() + '</p></div>'

    html = re.sub(
        r'<div[^>]+class="table-sources"[^>]*>(.*?)</div>',
        _replace_table_sources,
        html, flags=re.DOTALL
    )

    # Bloc "à rédiger" → supprimé à l'export
    html = re.sub(
        r'<p class="a-rediger">.*?</p>',
        '',
        html, flags=re.DOTALL
    )

    # [DEV-001] Notes techniques internes (mentions de génération automatique,
    # scripts, base ESS…) → utiles en prévisualisation, supprimées à l'export Word.
    html = re.sub(
        r'<p class="dev-note">.*?</p>',
        '',
        html, flags=re.DOTALL
    )

    # [TOF-001] Suppression des contenus statiques des listes (tableaux, graphiques, encadrés)
    # Ces sections seront remplacées par des champs TOF Word en post-traitement.
    for heading_text in ('Table des matières', 'Liste des tableaux', 'Liste des graphiques', 'Liste des encadrés'):
        html = re.sub(
            r'(<h\d[^>]*>' + re.escape(heading_text) + r'</h\d>)\s*(<p>.*?</p>\s*)*',
            r'\1\n',
            html, flags=re.DOTALL
        )

    # [STY-003] Style Body Text par défaut sur tous les paragraphes ordinaires
    # Stratégie : remplacer temporairement les <p> déjà à l'intérieur d'un
    # <div custom-style="..."> ou dans une cellule de tableau (<td>/<th>) par
    # un tag marqué, wrapper les <p> restants en Body Text, puis restaurer.
    html = re.sub(
        r'(custom-style="[^"]*">)\s*<p',
        r'\1<__STYLED_P',
        html
    )
    # Protéger les <p> à l'intérieur des cellules de tableau (td/th)
    # pour que le filtre Lua style_mapping.lua puisse y appliquer TableText/TableHeader.
    html = re.sub(
        r'(<t[dh][^>]*>)\s*<p',
        r'\1<__TABLE_P',
        html
    )
    html = re.sub(
        r'<p>(.*?)</p>',
        r'<div custom-style="Normal"><p>\1</p></div>',
        html, flags=re.DOTALL
    )
    html = html.replace('<__STYLED_P', '<p')
    html = html.replace('<__TABLE_P', '<p')

    return html


# ---------------------------------------------------------------------------
# Génération du template .docx de référence
# ---------------------------------------------------------------------------

def generate_reference_docx():
    """Vérifie que le template Word existe."""
    if not os.path.exists(REF_DOCX):
        sys.exit(
            "Template Word introuvable : {}\n"
            "Vérifier que le fichier 09_scripts/template_bulletin.docx est bien présent.".format(REF_DOCX)
        )


# ---------------------------------------------------------------------------
# Post-traitement : sauts de page avant les sections préliminaires
# ---------------------------------------------------------------------------

# Titres qui doivent commencer sur une nouvelle page.
# Le premier n'a pas de saut (c'est déjà le début du document).
_PAGE_BREAK_BEFORE = {
    'Avant-propos',
    'Remerciements',
    'Liste des sigles et acronymes',
    'Table des matières',
    'Listes des tableaux, graphiques et encadrés',
}

def insert_page_breaks(docx_path):
    """
    Ajoute la propriété Word 'saut de page avant' sur les titres
    des sections préliminaires listées dans _PAGE_BREAK_BEFORE.
    La propriété est posée via w:pPr/w:pageBreakBefore dans le XML
    du paragraphe — elle reste attachée au titre et n'introduit pas
    de paragraphe vide supplémentaire.
    """
    try:
        from docx import Document as _Doc
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        print("  [PBB] python-docx non disponible — sauts de page non insérés.")
        return

    doc = _Doc(docx_path)
    count = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        if text in _PAGE_BREAK_BEFORE:
            pPr = para._p.get_or_add_pPr()
            # Supprimer un éventuel pageBreakBefore déjà présent pour éviter les doublons
            for existing in pPr.findall(qn('w:pageBreakBefore')):
                pPr.remove(existing)
            pbr = OxmlElement('w:pageBreakBefore')
            pPr.append(pbr)
            count += 1
            print("  [PBB] Saut de page avant : «{}»".format(text))

    if count:
        doc.save(docx_path)
        print("  [PBB] {} saut(s) de page insérés.".format(count))
    else:
        print("  [PBB] Aucun titre préliminaire trouvé.")


# ---------------------------------------------------------------------------
# Post-traitement : champs TOF Word (Table of Figures)
# ---------------------------------------------------------------------------

# Correspondance : titre de section → instruction de champ Word
# \h  = liens hypertexte   \z = cacher les numéros de page en mode Web
# \t  = collecter les paragraphes du style nommé
_TOF_SECTIONS = {
    'Table des matières':    r' TOC \h \z \u ',
    'Liste des tableaux':    r' TOC \h \z \t "TableTitle,1" ',
    'Liste des graphiques':  r' TOC \h \z \t "GraphicTitle,1" ',
}

def _make_tof_paragraph(doc, field_instr):
    """
    Construit un paragraphe Word contenant un champ TOF (en XML OpenXML).
    Le champ est inséré en mode begin/separate/end avec un texte d'invite
    visible avant la première mise à jour.
    """
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    p = OxmlElement('w:p')

    def run_with(tag_type=None, text=None):
        r = OxmlElement('w:r')
        if tag_type:
            fc = OxmlElement('w:fldChar')
            fc.set(qn('w:fldCharType'), tag_type)
            r.append(fc)
        if text is not None:
            t = OxmlElement('w:instrText')
            t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
            t.text = text
            r.append(t)
        return r

    p.append(run_with('begin'))
    p.append(run_with(text=field_instr))
    p.append(run_with('separate'))

    # Texte d'invite visible avant mise à jour
    r_hint = OxmlElement('w:r')
    rpr = OxmlElement('w:rPr')
    color = OxmlElement('w:color')
    color.set(qn('w:val'), '808080')
    rpr.append(color)
    r_hint.append(rpr)
    t_hint = OxmlElement('w:t')
    t_hint.text = u'[Clic droit \u2192 Mettre \u00e0 jour les champs pour g\u00e9n\u00e9rer cette liste]'
    r_hint.append(t_hint)
    p.append(r_hint)

    p.append(run_with('end'))
    return p


def insert_tof_fields(docx_path):
    """
    Parcourt le document généré, trouve les titres de section des listes,
    et insère un champ TOF Word juste après chaque titre.
    """
    try:
        from docx import Document as _Doc
        from docx.oxml.ns import qn
    except ImportError:
        print("  [TOF] python-docx non disponible — champs TOF non insérés.")
        return

    doc = _Doc(docx_path)
    body = doc.element.body
    paragraphs = body.findall('.//' + qn('w:p'))

    inserted = 0
    for para in paragraphs:
        # Lire le texte brut du paragraphe
        texts = [node.text or '' for node in para.iter(qn('w:t'))]
        full_text = ''.join(texts).strip()

        if full_text in _TOF_SECTIONS:
            field_instr = _TOF_SECTIONS[full_text]
            tof_p = _make_tof_paragraph(doc, field_instr)
            para.addnext(tof_p)
            inserted += 1
            print("  [TOF] Champ inséré après : «{}»".format(full_text))

    if inserted:
        doc.save(docx_path)
        print("  [TOF] {} champ(s) TOF insérés et sauvegardés.".format(inserted))
    else:
        print("  [TOF] Aucune section de liste trouvée — vérifier les titres.")


# ---------------------------------------------------------------------------
# Post-traitement : Autofit to Window sur tous les tableaux
# ---------------------------------------------------------------------------

def set_tables_autofit(docx_path):
    """
    [TAB-002] Applique « Ajuster à la fenêtre » (AutoFit to Window) à tous les tableaux
    du document : largeur 100 % de la page, mise en page automatique.
    """
    try:
        from docx import Document as _Doc
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        print("  [TAB-002] python-docx absent — autofit ignoré.")
        return

    doc = _Doc(docx_path)
    count = 0
    for table in doc.tables:
        tbl = table._tbl
        tblPr = tbl.find(qn('w:tblPr'))
        if tblPr is None:
            tblPr = OxmlElement('w:tblPr')
            tbl.insert(0, tblPr)

        # Largeur : 100 % (5000 en cinquantièmes de pourcent)
        tblW = tblPr.find(qn('w:tblW'))
        if tblW is None:
            tblW = OxmlElement('w:tblW')
            tblPr.append(tblW)
        tblW.set(qn('w:w'), '5000')
        tblW.set(qn('w:type'), 'pct')

        # Mise en page automatique (supprime le mode fixe)
        tblLayout = tblPr.find(qn('w:tblLayout'))
        if tblLayout is None:
            tblLayout = OxmlElement('w:tblLayout')
            tblPr.append(tblLayout)
        tblLayout.set(qn('w:type'), 'autofit')

        count += 1

    doc.save(docx_path)
    print("  [TAB-002] {} tableau(x) mis en Autofit to Window.".format(count))


# ---------------------------------------------------------------------------
# Conversion principale
# ---------------------------------------------------------------------------

def export(html_path: str, out_suffix: str = ""):
    basename = os.path.splitext(os.path.basename(html_path))[0]
    docx_out = os.path.join(OUTPUT_DIR, basename + out_suffix + ".docx")
    tmp_html = os.path.join(OUTPUT_DIR, "_tmp_export_word.html")

    print("Source  : {}".format(os.path.basename(html_path)))
    print("Sortie  : {}".format(os.path.basename(docx_out)))

    # Lire le HTML source
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Appliquer les corrections
    html = apply_corrections(html)

    # Écrire le HTML corrigé dans un fichier temporaire
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html)

    # Générer le template Word de référence
    generate_reference_docx()

    # Lancer Pandoc
    cmd = [
        PANDOC, tmp_html,
        "--from", "html",
        "--to", "docx",
        "--reference-doc", REF_DOCX,
        "--output", docx_out,
        "--lua-filter", LUA_FILTER,
        "--lua-filter", LUA_FOOTNOTES,
        "--lua-filter", LUA_STYLES,
        "--wrap=none",
        "--metadata", "title=Deuxieme Bulletin statistique de la protection sociale en RDC",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)

    # Nettoyage du fichier temporaire
    if os.path.exists(tmp_html):
        os.remove(tmp_html)

    # Résultat
    if res.returncode != 0 or not os.path.exists(docx_out):
        print("ECHEC :\n" + res.stderr)
        sys.exit(1)

    if res.stderr:
        warnings = [l for l in res.stderr.splitlines() if "WARNING" in l]
        if warnings:
            print("Avertissements ({}) :".format(len(warnings)))
            for w in warnings[:5]:
                print("  " + w)

    size = os.path.getsize(docx_out) // 1024
    print("Succès : {} ({} KB)".format(os.path.basename(docx_out), size))

    # Post-traitement : sauts de page avant les sections préliminaires
    insert_page_breaks(docx_out)

    # Post-traitement : insertion des champs TOF Word
    insert_tof_fields(docx_out)

    # Post-traitement : ajustement automatique des tableaux à la largeur de la page
    set_tables_autofit(docx_out)

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    html_file = sys.argv[1] if len(sys.argv) > 1 else find_latest_html()
    export(html_file)
