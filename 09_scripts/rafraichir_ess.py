"""
rafraichir_ess.py — Mise à jour complète d'un fichier ESS en base + dashboard
==============================================================================
Chaîne complète en une commande :
  1. Purge les données existantes en base pour la cible (institution / année)
  2. Réimporte le fichier ESS mis à jour depuis 06_sources/ESS/
  3. Régénère le tableau de bord (visualiser_regimes.py)
  4. Notifie l'utilisateur du résultat

Usage :
    py 09_scripts/rafraichir_ess.py --institution CNSS --annee 2022
    py 09_scripts/rafraichir_ess.py --institution CNSSAP --annee 2021 --dry-run
    py 09_scripts/rafraichir_ess.py --institution CNSS --annee 2022 --no-dashboard
    py 09_scripts/rafraichir_ess.py --source-id 5 --annee 2022

Arguments :
    --institution   Institution cible (CNSS, CNSSAP, RDC…)
    --annee         Année ESS cible
    --source-id     Identifiant source_id précis (alternative à institution/annee)
    --dry-run       Simule toutes les étapes sans écrire ni supprimer
    --no-dashboard  Saute la régénération du tableau de bord
    --verbose       Affiche le détail de chaque ligne parsée lors de la réimportation
"""

import argparse
import subprocess
import os
import subprocess
import sys
import time
from pathlib import Path

# Forcer UTF-8 sur stdout/stderr (nécessaire sur Windows avec cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Environnement transmis aux sous-processus : forcer UTF-8
_ENV_UTF8 = {**os.environ, "PYTHONUTF8": "1"}

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).resolve().parent
WORKSPACE    = SCRIPT_DIR.parent
EXTRAIRE_ESS = SCRIPT_DIR / "extraire_ess.py"
VISUALISER   = SCRIPT_DIR / "visualiser_regimes.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list, label: str) -> tuple[bool, str]:
    """Lance un sous-processus, retourne (succès, sortie combinée)."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        cwd=str(WORKSPACE),
        encoding="utf-8",
        errors="replace",
        env=_ENV_UTF8,
    )
    output = (result.stdout or "") + (result.stderr or "")
    ok = result.returncode == 0
    if not ok:
        print(f"[{label}] ✗ Erreur (code {result.returncode}) :")
        for line in output.strip().splitlines():
            print(f"         {line}")
    return ok, output


def _print_step(n: int, total: int, title: str):
    print(f"\n{'─' * 60}")
    print(f"  Étape {n}/{total} — {title}")
    print(f"{'─' * 60}")


# ---------------------------------------------------------------------------
# Étapes
# ---------------------------------------------------------------------------

def etape_purge(institution: str | None, annee: int | None,
                source_id: int | None, dry_run: bool) -> bool:
    """Supprime les données ESS existantes pour la cible."""
    cmd = [sys.executable, str(EXTRAIRE_ESS), "--delete"]
    if institution:
        cmd += ["--institution", institution]
    if annee:
        cmd += ["--annee", str(annee)]
    if source_id is not None:
        cmd += ["--source-id", str(source_id)]
    if dry_run:
        cmd.append("--dry-run")
    else:
        cmd.append("--force")

    ok, output = _run(cmd, "PURGE")
    if ok:
        for line in output.strip().splitlines():
            print(f"  {line}")
    return ok


def etape_reimport(institution: str | None, annee: int | None,
                   dry_run: bool, verbose: bool) -> bool:
    """Réimporte les données ESS depuis 06_sources/ESS/."""
    cmd = [sys.executable, str(EXTRAIRE_ESS)]
    if institution:
        cmd += ["--institution", institution]
    if annee:
        cmd += ["--annee", str(annee)]
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--verbose")

    ok, output = _run(cmd, "IMPORT")
    if ok:
        for line in output.strip().splitlines():
            print(f"  {line}")
    return ok


def etape_dashboard(dry_run: bool) -> bool:
    """Régénère le tableau de bord des régimes."""
    if dry_run:
        print("  [DRY-RUN] Régénération du dashboard simulée — aucune action.")
        return True
    if not VISUALISER.exists():
        print(f"  ✗ Script introuvable : {VISUALISER}")
        return False

    ok, output = _run([sys.executable, str(VISUALISER)], "DASHBOARD")
    if ok:
        print("  ✓ Dashboard régénéré.")
    return ok


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Mise a jour complete d'un fichier ESS : purge -> reimport -> dashboard."
    )
    parser.add_argument("--institution", type=str,
                        help="Institution cible (CNSS, CNSSAP, RDC…)")
    parser.add_argument("--annee",       type=int,
                        help="Année ESS cible")
    parser.add_argument("--source-id",   type=int, dest="source_id",
                        help="Identifiant source_id précis (alternative à institution/annee)")
    parser.add_argument("--dry-run",     action="store_true",
                        help="Simule toutes les étapes sans modifier la base ni le dashboard")
    parser.add_argument("--no-dashboard", action="store_true",
                        help="Saute la régénération du tableau de bord")
    parser.add_argument("--verbose",     action="store_true",
                        help="Affiche le détail de chaque ligne parsée (étape réimport)")
    args = parser.parse_args()

    # Validation des arguments
    has_target = bool(args.institution) or args.annee or (args.source_id is not None)
    if not has_target:
        parser.error(
            "Préciser au moins un filtre : --institution, --annee ou --source-id.\n"
            "Exemple : py 09_scripts/rafraichir_ess.py --institution CNSS --annee 2022"
        )

    n_steps = 2 if args.no_dashboard else 3

    print("=" * 60)
    print("  Rafraîchissement ESS — Protection sociale RDC")
    print("=" * 60)
    if args.dry_run:
        print("  ⚠  MODE DRY-RUN : aucune écriture ni suppression effective")
    cible = " | ".join(filter(None, [
        f"institution={args.institution}" if args.institution else None,
        f"annee={args.annee}"             if args.annee       else None,
        f"source_id={args.source_id}"     if args.source_id is not None else None,
    ]))
    print(f"  Cible : {cible}")

    t0 = time.perf_counter()

    # --- Étape 1 : Purge ---
    _print_step(1, n_steps, "Purge des données ESS existantes")
    ok_purge = etape_purge(args.institution, args.annee, args.source_id, args.dry_run)
    if not ok_purge:
        print("\n  ✗ Purge échouée — opération interrompue.")
        sys.exit(1)

    # --- Étape 2 : Réimport ---
    _print_step(2, n_steps, "Réimportation du fichier ESS mis à jour")
    ok_import = etape_reimport(args.institution, args.annee, args.dry_run, args.verbose)
    if not ok_import:
        print("\n  ✗ Réimport échoué — vérifier le fichier source dans 06_sources/ESS/")
        sys.exit(1)

    # --- Étape 3 : Dashboard ---
    if not args.no_dashboard:
        _print_step(3, n_steps, "Régénération du tableau de bord")
        ok_dash = etape_dashboard(args.dry_run)
        if not ok_dash:
            print("  ⚠  Dashboard non régénéré — les données en base sont à jour.")

    elapsed = time.perf_counter() - t0
    print(f"\n{'=' * 60}")
    if args.dry_run:
        print(f"  ✓ Simulation terminée en {elapsed:.1f}s — aucune modification effectuée.")
    else:
        print(f"  ✓ Mise à jour terminée en {elapsed:.1f}s")
        print()
        print("  → Si le serveur de prévisualisation est actif,")
        print("     recharger le tableau de bord dans le navigateur (F5).")
    print()


if __name__ == "__main__":
    main()
