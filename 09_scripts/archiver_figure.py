"""
archiver_figure.py
------------------
Gestionnaire d'archivage des figures du bulletin.

Commandes disponibles :

  python 09_scripts/archiver_figure.py creer
      → Crée en mode interactif une nouvelle figure :
          - fichier de données (.csv) dans 08_figures/donnees/
          - script de génération (.py)  dans 08_figures/scripts/
          - réserve un emplacement       dans 08_figures/exports/
          - met à jour le registre       dans 08_figures/registre_figures.md

  python 09_scripts/archiver_figure.py verifier
      → Vérifie la cohérence entre le registre et les fichiers réels.
          Signale les fichiers déclarés mais absents, et les fichiers
          présents mais non enregistrés.

  python 09_scripts/archiver_figure.py lister
      → Affiche le registre des figures avec leur statut.

Usage :
    python 09_scripts/archiver_figure.py <commande>

Dépendances : aucune (bibliothèque standard Python uniquement)
"""

import pathlib
import sys
import re
from datetime import date

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
SCRIPT_DIR    = pathlib.Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent
FIGURES_DIR   = WORKSPACE_DIR / "08_figures"
DONNEES_DIR   = FIGURES_DIR / "donnees"
SCRIPTS_DIR   = FIGURES_DIR / "scripts"
EXPORTS_DIR   = FIGURES_DIR / "exports"
REGISTRE      = FIGURES_DIR / "registre_figures.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convertit un titre en identifiant de fichier safe."""
    text = text.lower().strip()
    text = re.sub(r"[àâä]", "a", text)
    text = re.sub(r"[éèêë]", "e", text)
    text = re.sub(r"[îï]",   "i", text)
    text = re.sub(r"[ôö]",   "o", text)
    text = re.sub(r"[ùûü]",  "u", text)
    text = re.sub(r"[ç]",    "c", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def ask(prompt: str, default: str = "") -> str:
    """Invite de saisie avec valeur par défaut."""
    if default:
        rep = input(f"  {prompt} [{default}] : ").strip()
        return rep if rep else default
    return input(f"  {prompt} : ").strip()


def lire_registre() -> list[str]:
    if not REGISTRE.exists():
        return []
    return REGISTRE.read_text(encoding="utf-8").splitlines()


def ecrire_registre(lignes: list[str]):
    REGISTRE.write_text("\n".join(lignes) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Commande : creer
# ---------------------------------------------------------------------------

def cmd_creer():
    print("\n" + "=" * 60)
    print("  Archiver une nouvelle figure")
    print("=" * 60)

    print("\n— Identification —")
    numero    = ask("Numéro de figure (ex: 1.1)", "")
    type_fig  = ask("Type (graphique / carte / schéma / encadré)", "graphique")
    titre     = ask("Titre de la figure", "")
    chapitre  = ask("Chapitre / section de référence", "")
    source    = ask("Source des données", "")
    note      = ask("Note méthodologique (optionnel)", "—")

    if not numero or not titre:
        print("[ERREUR] Le numéro et le titre sont obligatoires.")
        sys.exit(1)

    # Identifiant normalisé : fig_1_1_titre_court
    num_slug  = slugify(numero)           # "1_1"
    titre_slug = slugify(titre)[:40]      # max 40 chars
    base_name  = f"fig_{num_slug}_{titre_slug}"
    today      = date.today().isoformat()

    # ---- Fichier de données ----
    csv_path = DONNEES_DIR / f"{base_name}.csv"
    if not csv_path.exists():
        csv_path.write_text(
            f"# Source : {source}\n"
            f"# Figure : {base_name}\n"
            f"# Créé le : {today}\n"
            f"# Titre : {titre}\n"
            f"# Compléter les colonnes et les données ci-dessous\n"
            f"colonne_1,colonne_2,colonne_3\n",
            encoding="utf-8",
        )
        print(f"\n  [CRÉÉ] Données    : 08_figures/donnees/{csv_path.name}")
    else:
        print(f"\n  [EXISTE] Données  : 08_figures/donnees/{csv_path.name}")

    # ---- Script de génération ----
    py_path = SCRIPTS_DIR / f"{base_name}.py"
    if not py_path.exists():
        py_path.write_text(
            f'"""\n'
            f'{py_path.name}\n'
            f'{"—" * len(py_path.name)}\n'
            f'Figure {numero} — {titre}\n'
            f'\n'
            f'Source des données : 08_figures/donnees/{csv_path.name}\n'
            f'Export             : 08_figures/exports/{base_name}.png\n'
            f'Créé le            : {today}\n'
            f'"""\n\n'
            f'import pathlib\n'
            f'import csv\n'
            f'# import matplotlib.pyplot as plt\n\n'
            f'WORKSPACE = pathlib.Path(__file__).resolve().parents[2]\n'
            f'DONNEES   = WORKSPACE / "08_figures" / "donnees" / "{csv_path.name}"\n'
            f'EXPORT    = WORKSPACE / "08_figures" / "exports"  / "{base_name}.png"\n\n'
            f'# --- Lecture des données ---\n'
            f'# with open(DONNEES, newline="", encoding="utf-8") as f:\n'
            f'#     reader = csv.DictReader(row for row in f if not row.startswith("#"))\n'
            f'#     data = list(reader)\n\n'
            f'# --- Création du graphique ---\n\n'
            f'# --- Export ---\n'
            f'# EXPORT.parent.mkdir(parents=True, exist_ok=True)\n'
            f'# plt.savefig(EXPORT, dpi=150, bbox_inches="tight")\n'
            f'# print(f"[OK] Figure exportée : {{EXPORT}}")\n',
            encoding="utf-8",
        )
        print(f"  [CRÉÉ] Script     : 08_figures/scripts/{py_path.name}")
    else:
        print(f"  [EXISTE] Script   : 08_figures/scripts/{py_path.name}")

    # ---- Réserve dans exports ----
    placeholder = EXPORTS_DIR / f"{base_name}.png"
    if not placeholder.exists():
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        placeholder.write_text(
            f"# Emplacement réservé pour l'export de la figure {numero}\n"
            f"# Remplacer ce fichier par l'image PNG finale.\n",
            encoding="utf-8",
        )
        print(f"  [CRÉÉ] Réservation: 08_figures/exports/{placeholder.name}")

    # ---- Mise à jour du registre ----
    lignes = lire_registre()
    num_label = f"Figure {numero}"

    # Vérifier si déjà présent
    deja_present = any(num_label in l for l in lignes)

    if deja_present:
        print(f"\n  [INFO] {num_label} déjà présent dans le registre — non dupliqué.")
    else:
        nouvelle_ligne = (
            f"| {num_label} | {type_fig.capitalize()} | {titre} | {chapitre} "
            f"| `{csv_path.name}` | `{py_path.name}` | `{placeholder.name}` "
            f"| {source} | {note} | à prévoir |"
        )

        # Insérer avant la ligne "## Notes de gestion"
        notes_idx = next(
            (i for i, l in enumerate(lignes) if l.startswith("## Notes de gestion")),
            len(lignes),
        )
        lignes.insert(notes_idx, nouvelle_ligne)
        ecrire_registre(lignes)
        print(f"  [ENREGISTRÉ] {num_label} ajouté dans registre_figures.md")

    print("\n[OK] Archivage terminé.\n")


# ---------------------------------------------------------------------------
# Commande : verifier
# ---------------------------------------------------------------------------

def cmd_verifier():
    print("\n" + "=" * 60)
    print("  Vérification de cohérence — Figures")
    print("=" * 60)

    lignes = lire_registre()
    erreurs = 0

    # Extraire les lignes de données du tableau
    for ligne in lignes:
        if not ligne.startswith("| Figure"):
            continue
        cols = [c.strip() for c in ligne.split("|")]
        # cols : ['', 'Figure X.X', type, titre, chapitre, donnees, script, export, source, note, statut, '']
        if len(cols) < 11:
            continue
        num, _, titre, _, f_donnees, f_script, f_export = cols[1], cols[2], cols[3], cols[4], cols[5], cols[6], cols[7]

        def check_file(folder, fname, label):
            nonlocal erreurs
            fname = fname.strip("`").strip()
            if fname in ("à créer", "—", ""):
                return
            p = folder / fname
            if not p.exists():
                print(f"  [MANQUANT] {num} — {label} : {fname}")
                erreurs += 1

        check_file(DONNEES_DIR, f_donnees, "données")
        check_file(SCRIPTS_DIR, f_script,  "script")
        check_file(EXPORTS_DIR, f_export,  "export")

    # Fichiers présents mais non enregistrés
    nums_enregistres = set()
    for l in lignes:
        if l.startswith("| Figure"):
            m = re.match(r"\| Figure ([0-9.]+)", l)
            if m:
                nums_enregistres.add(m.group(1))

    for csv in sorted(DONNEES_DIR.glob("fig_*.csv")):
        m = re.match(r"fig_([0-9]+_[0-9]+)_", csv.name)
        if m:
            num = m.group(1).replace("_", ".")
            if num not in nums_enregistres:
                print(f"  [NON ENREGISTRÉ] Données présentes mais absentes du registre : {csv.name}")
                erreurs += 1

    if erreurs == 0:
        print("  Aucune anomalie détectée.")
    else:
        print(f"\n  {erreurs} anomalie(s) détectée(s).")
    print()


# ---------------------------------------------------------------------------
# Commande : lister
# ---------------------------------------------------------------------------

def cmd_lister():
    print("\n" + "=" * 60)
    print("  Registre des figures")
    print("=" * 60 + "\n")

    lignes = lire_registre()
    found = False
    for ligne in lignes:
        if not ligne.startswith("| Figure"):
            continue
        cols = [c.strip() for c in ligne.split("|")]
        if len(cols) < 11:
            continue
        num, type_f, titre, _, _, _, _, _, _, statut = (
            cols[1], cols[2], cols[3], cols[4], cols[5], cols[6], cols[7], cols[8], cols[9], cols[10]
        )
        print(f"  {num:15s}  [{statut:15s}]  {type_f:12s}  {titre}")
        found = True

    if not found:
        print("  Aucune figure enregistrée.")
    print()


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

COMMANDES = {
    "creer":    cmd_creer,
    "verifier": cmd_verifier,
    "lister":   cmd_lister,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDES:
        print(__doc__)
        print("Commandes disponibles :", ", ".join(COMMANDES))
        sys.exit(0)

    COMMANDES[sys.argv[1]]()
