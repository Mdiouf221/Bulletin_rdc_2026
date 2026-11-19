"""
assembler_markdown.py
---------------------
Assemble les fichiers Markdown du bulletin selon l'ordre défini dans build_config.yml.

Produit deux fichiers dans 10_output/ :
  - bulletin_complet_travail.md      : version conservant les notes internes
  - bulletin_complet_publication.md  : version sans les blocs NOTE_INTERNE

Usage :
    python 09_scripts/assembler_markdown.py

Dépendances :
    PyYAML  — installer avec : pip install pyyaml
"""

import re
import sys
import pathlib
from html import escape

# --- Vérification de PyYAML ------------------------------------------------
try:
    import yaml
except ImportError:
    print(
        "[ERREUR] Le module 'PyYAML' est requis mais n'est pas installé.\n"
        "         Installez-le avec : pip install pyyaml\n"
        "         Puis relancez ce script."
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent
CONFIG_FILE = WORKSPACE_DIR / "build_config.yml"

# ---------------------------------------------------------------------------
# Lecture de la configuration
# ---------------------------------------------------------------------------
if not CONFIG_FILE.exists():
    print(f"[ERREUR] Fichier de configuration introuvable : {CONFIG_FILE}")
    sys.exit(1)

with CONFIG_FILE.open(encoding="utf-8-sig") as f:
    config = yaml.safe_load(f)

if not config or not isinstance(config, dict):
    print(f"[ERREUR] build_config.yml est vide ou mal formé : {CONFIG_FILE}")
    sys.exit(1)

output_dir = WORKSPACE_DIR / config.get("project", {}).get("output_dir", "10_output")
output_dir.mkdir(parents=True, exist_ok=True)

path_travail = WORKSPACE_DIR / config["outputs"]["working_markdown"]
path_publication = WORKSPACE_DIR / config["outputs"]["publication_markdown"]

# ---------------------------------------------------------------------------
# Contenus réservés à la version de travail
# ---------------------------------------------------------------------------
HTML_COMMENT_RE = re.compile(
    r"<!--(?!\s*MANUEL_EDIT:(?:DEBUT|FIN)\s*-->).*?-->",
    re.DOTALL,
)
INTERNAL_PARAGRAPH_RE = re.compile(
    r'<p\b[^>]*class="[^"]*\b(?:dev-note|a-rediger)\b[^"]*"[^>]*>.*?</p>',
    re.DOTALL | re.IGNORECASE,
)
VALIDATION_BADGE_RE = re.compile(
    r'<span\b[^>]*class="[^"]*\bvalid-badge\b[^"]*"[^>]*>.*?</span>',
    re.DOTALL | re.IGNORECASE,
)
SOURCE_MARKER_LINK_RE = re.compile(
    r'<a\b[^>]*>\s*\[src\]\s*</a>',
    re.DOTALL | re.IGNORECASE,
)
EDITORIAL_PLACEHOLDER_LINE_RE = re.compile(
    r'(?im)^\s*(?:[*_]\s*)?\[(?:à rédiger|à définir|à compléter)(?:[^\]]*)\]'
    r'(?:\s*[*_])?\s*$'
)


def remove_notes_internes(text: str) -> str:
    """Supprime les commentaires et paragraphes réservés au travail interne."""
    cleaned = HTML_COMMENT_RE.sub("", text)
    cleaned = INTERNAL_PARAGRAPH_RE.sub("", cleaned)
    cleaned = VALIDATION_BADGE_RE.sub("", cleaned)
    cleaned = SOURCE_MARKER_LINK_RE.sub("", cleaned)
    cleaned = re.sub(r'(?im)(?<!\w)\[src\](?!\w)', "", cleaned)
    cleaned = EDITORIAL_PLACEHOLDER_LINE_RE.sub("", cleaned)
    # Nettoyer les lignes vides consécutives laissées par la suppression
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Assemblage
# ---------------------------------------------------------------------------
sections = config.get("sections", [])
fichiers_manquants = []
blocs_assembled = []
preview_markers = {}

for section in sections:
    section_title = section.get("title", "")
    files = section.get("files", [])

    if not files:
        continue

    # Séparateur de section
    blocs_assembled.append(f"\n\n---\n\n<!-- SECTION : {section_title} -->\n\n")

    for rel_path in files:
        abs_path = WORKSPACE_DIR / rel_path
        if not abs_path.exists():
            print(f"[AVERTISSEMENT] Fichier manquant : {rel_path}")
            fichiers_manquants.append(rel_path)
            blocs_assembled.append(
                f"\n<!-- FICHIER MANQUANT : {rel_path} -->\n"
            )
            continue

        content = abs_path.read_text(encoding="utf-8-sig").strip()
        preview_markers[len(blocs_assembled)] = (
            f'\n\n<div hidden data-preview-file="{escape(rel_path, quote=True)}"></div>\n\n'
        )
        blocs_assembled.append(f"\n\n{content}\n\n")
        blocs_assembled.append("<!-- FIN FICHIER -->\n")

# ---------------------------------------------------------------------------
# Écriture des deux versions
# ---------------------------------------------------------------------------
full_text = "".join(blocs_assembled)

# Version travail — notes internes conservées
header_travail = (
    f"<!-- VERSION TRAVAIL — notes internes conservées -->\n"
    f"<!-- Généré automatiquement par assembler_markdown.py -->\n\n"
    f"# {config['project']['title']}\n\n"
)
path_travail.write_text(header_travail + full_text, encoding="utf-8")
print(f"[OK] Version travail écrite : {path_travail.relative_to(WORKSPACE_DIR)}")

# Version publication — notes internes supprimées
header_publication = (
    f"# {config['project']['title']}\n\n"
)
def publication(text):
    cleaned = remove_notes_internes(text)
    return header_publication + "\n".join(line.rstrip() for line in cleaned.splitlines())


path_publication.write_text(publication(full_text), encoding="utf-8")
if len(sys.argv) == 3 and sys.argv[1] == "--preview-markdown":
    marked = "".join(preview_markers.get(i, "") + block for i, block in enumerate(blocs_assembled))
    pathlib.Path(sys.argv[2]).write_text(publication(marked), encoding="utf-8")
print(f"[OK] Version publication écrite : {path_publication.relative_to(WORKSPACE_DIR)}")

# ---------------------------------------------------------------------------
# Bilan
# ---------------------------------------------------------------------------
if fichiers_manquants:
    print(f"\n[BILAN] {len(fichiers_manquants)} fichier(s) manquant(s) :")
    for f in fichiers_manquants:
        print(f"        - {f}")
else:
    print("\n[BILAN] Tous les fichiers référencés ont été trouvés.")
