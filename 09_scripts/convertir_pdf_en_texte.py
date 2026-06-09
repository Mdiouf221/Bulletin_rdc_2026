"""
convertir_pdf_en_texte.py
--------------------------
Convertit tous les fichiers PDF des dossiers sources
en fichiers texte (.txt) lisibles par les agents.

Dossiers traités :
  - 06_sources/bulletins_rdc/
  - 06_sources/bulletins_comparaison/
  - 06_sources/normes_oit/
  - 06_sources/institutions/
  - 06_sources/officielles_web/
  - 06_sources/sources_incertaines/
  - 06_sources/atelier_lancement/presentations/

Pour chaque PDF, crée un fichier .txt dans un sous-dossier _texte/
au même niveau que le PDF source.

Usage :
    python 09_scripts/convertir_pdf_en_texte.py

Dépendances :
    pdfplumber — installer avec : pip install pdfplumber
"""

import pathlib
import sys

try:
    import pdfplumber
except ImportError:
    print(
        "[ERREUR] Le module 'pdfplumber' est requis.\n"
        "         Installez-le avec : pip install pdfplumber"
    )
    sys.exit(1)

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent
SOURCES_DIR = WORKSPACE_DIR / "06_sources"

DOSSIERS = [
    SOURCES_DIR / "bulletins_rdc",
    SOURCES_DIR / "bulletins_comparaison",
    SOURCES_DIR / "normes_oit",
    SOURCES_DIR / "institutions",
    SOURCES_DIR / "officielles_web",
    SOURCES_DIR / "sources_incertaines",
    SOURCES_DIR / "atelier_lancement" / "presentations",
]

# ---------------------------------------------------------------------------

def convertir_pdf(pdf_path: pathlib.Path, output_dir: pathlib.Path) -> bool:
    """Extrait le texte d'un PDF et l'écrit dans un fichier .txt."""
    output_dir.mkdir(parents=True, exist_ok=True)
    txt_path = output_dir / (pdf_path.stem + ".txt")

    # Ne pas reconvertir si le fichier texte existe déjà
    if txt_path.exists():
        print(f"  [DÉJÀ CONVERTI] {pdf_path.name}")
        return True

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            pages_text = [f"[DOCUMENT : {pdf_path.name} — {total_pages} pages]\n"]
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    pages_text.append(f"--- Page {i} ---\n{text}")
                else:
                    pages_text.append(f"--- Page {i} --- [pas de texte extractible]")

        full_text = "\n\n".join(pages_text)
        txt_path.write_text(full_text, encoding="utf-8")
        print(f"  [OK] {pdf_path.name} → {txt_path.relative_to(WORKSPACE_DIR)}")
        return True

    except Exception as e:
        print(f"  [ERREUR] {pdf_path.name} : {e}")
        return False


# ---------------------------------------------------------------------------

total_ok = 0
total_erreur = 0
total_vide = 0

for dossier in DOSSIERS:
    pdfs = sorted(dossier.glob("*.pdf"))
    if not pdfs:
        print(f"\n[{dossier.name}/] — aucun PDF trouvé")
        continue

    print(f"\n[{dossier.name}/] — {len(pdfs)} PDF(s)")
    output_dir = dossier / "_texte"

    for pdf_path in pdfs:
        ok = convertir_pdf(pdf_path, output_dir)
        if ok:
            total_ok += 1
        else:
            total_erreur += 1

# ---------------------------------------------------------------------------
print(f"\n[BILAN] {total_ok} converti(s), {total_erreur} erreur(s)")
print(f"        Les fichiers .txt sont dans les sous-dossiers _texte/")
