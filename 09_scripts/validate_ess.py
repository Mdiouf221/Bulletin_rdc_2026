"""
validate_ess.py
================
Validation et rapport de contrôle pour les fichiers ESS.

Usage :
    py validate_ess.py              # scanne 06_sources/ESS
    py validate_ess.py --institution CNSS --annee 2019
    py validate_ess.py --inbox
"""

import argparse
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)

from extraire_ess import (
    ESS_BASE_DIR,
    ESS_INBOX_DIR,
    ESS_REPORT_DIR,
    discover_ess_archive_files,
    discover_ess_inbox_files,
    validate_ess_workbook,
    _write_validation_report,
)


def main():
    parser = argparse.ArgumentParser(description="Valider les fichiers ESS et générer un rapport.")
    parser.add_argument("--annee", type=int, help="Valider seulement cette année")
    parser.add_argument("--institution", type=str, help="Valider seulement cette institution (CNSS, CNSSAP)")
    parser.add_argument("--inbox", action="store_true", help="Valider les fichiers déposés dans 06_sources/_entrants/")
    parser.add_argument("--inbox-dir", type=str, default=ESS_INBOX_DIR, help="Chemin du dossier de réception ESS")
    parser.add_argument("--report-dir", type=str, default=ESS_REPORT_DIR, help="Dossier de sortie des rapports")
    args = parser.parse_args()

    print("=" * 65)
    print("  Validation ESS — Protection sociale RDC")
    print("=" * 65)

    resultats = {"ok": 0, "erreur": 0}

    if args.inbox:
        inbox_files = discover_ess_inbox_files(args.inbox_dir)
        if not inbox_files:
            print(f"Aucun fichier ESS trouvé dans {args.inbox_dir}.")
        for filepath in inbox_files:
            report = validate_ess_workbook(filepath, source_mode="inbox")
            if args.institution and report.get("detected_institution") and report.get("detected_institution").upper() != args.institution.upper():
                continue
            if args.annee and report.get("detected_year") and report.get("detected_year") != args.annee:
                continue
            out_path = _write_validation_report(report, args.report_dir)
            print(f"  ↳ Rapport écrit : {out_path}")
            if report.get("verdict") == "blocked":
                resultats["erreur"] += 1
            else:
                resultats["ok"] += 1
    else:
        archive_entries, skipped_entries = discover_ess_archive_files(ESS_BASE_DIR)
        if args.annee:
            archive_entries = [entry for entry in archive_entries if entry.get("annee") == args.annee]
            skipped_entries = [entry for entry in skipped_entries if entry.get("annee") == args.annee]
        if args.institution:
            archive_entries = [
                entry for entry in archive_entries
                if (entry.get("institution") or "").upper() == args.institution.upper()
            ]
            skipped_entries = [
                entry for entry in skipped_entries
                if (entry.get("institution") or "").upper() == args.institution.upper()
            ]
        if skipped_entries:
            print("\n  Fichiers ESS archivés ignorés (doublons ou copies) :")
            for entry in skipped_entries:
                print(f"    - {entry['rel_path']} — {entry['skip_reason']}")
        if not archive_entries:
            print("Aucun fichier ESS correspondant aux critères dans 06_sources/ESS.")
            return
        for entry in archive_entries:
            report = validate_ess_workbook(
                entry["filepath"],
                institution=entry.get("institution"),
                annee=entry.get("annee"),
                note_anomalie=entry.get("note_anomalie"),
                source_mode="archive_scan",
            )
            out_path = _write_validation_report(report, args.report_dir)
            print(f"  ↳ Rapport écrit : {out_path}")
            if report.get("verdict") == "blocked":
                resultats["erreur"] += 1
            else:
                resultats["ok"] += 1

    print(f"\n{'='*65}")
    print(f"  Résumé : {resultats['ok']} rapport(s) généré(s), {resultats['erreur']} cas bloquant(s)")
    print()


if __name__ == "__main__":
    main()
