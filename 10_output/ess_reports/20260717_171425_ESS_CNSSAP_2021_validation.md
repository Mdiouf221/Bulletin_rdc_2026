# ESS validation report

- Generated at: 2026-07-17T17:14:24
- File: ESS CNSSAP 2021.xlsm
- Source path: c:\Users\M.Diouf\OneDrive\Bureau\RDC Bulletin V1\Bulletin_rdc_2026_agents\06_sources\ESS\ESS_CNSSAP\ESS CNSSAP 2021.xlsm
- Mode: validation-only
- Detected institution: CNSSAP
- Detected year: 2021
- Verdict: warnings

## Summary
- Errors: 0
- Warnings: 5
- Infos: 2
- Regimes found: 1
- Prestations found: 3

## Sheets
- INSTRUCTIONS
- Inventaire des régimes
- CNSAP Régime de base
- ADDITIONAL statistics for SDGs
- CALCULATIONS

## Issues
| Severity | Code | Location | Message | Details |
|---|---|---|---|---|
| info | source_note | ESS CNSSAP 2021.xlsm | Note associée à la source | Date interne inventaire affiche 2022 — anomalie connue ; données retenues pour 2021 |
| info | archive_file_exists | c:\Users\M.Diouf\OneDrive\Bureau\RDC Bulletin V1\Bulletin_rdc_2026_agents\06_sources\ESS\ESS_CNSSAP\ESS CNSSAP 2021.xlsm | Un fichier portant ce nom existe déjà dans l'archive ESS | Même chemin |
| warning | db_source_exists | ESS CNSSAP 2021.xlsm | La même source ESS existe déjà en base | source_id=77, institution=CNSSAP, annee=2021, date_ingestion=2026-07-03 23:16:54 |
| warning | currency_fallback_risk | CNSAP Régime de base!Q5 | Montant présent en colonne USD mais absent en CDF | Le convertisseur actuel peut mal interpréter cette valeur. |
| warning | currency_fallback_risk | CNSAP Régime de base!Q6 | Montant présent en colonne USD mais absent en CDF | Le convertisseur actuel peut mal interpréter cette valeur. |
| warning | non_numeric_value | CNSAP Régime de base!R7 | Valeur non numérique pour montant_unitaire_usd | Contenu lu: '5\u202f876' |
| warning | currency_fallback_risk | CNSAP Régime de base!Q7 | Montant présent en colonne USD mais absent en CDF | Le convertisseur actuel peut mal interpréter cette valeur. |

## Checks performed
- File identity and accessibility
- Workbook loadability
- Detected institution and year
- Year consistency across filename, inventory and sheets
- Archive duplicate file detection
- Database source duplicate detection
- Inventory sheet presence
- Regime row detection and numbering
- Regime sheet title vs inventory match
- Prestation row detection and numbering
- Numeric cell parsing on key fields
- Currency fallback risk detection
- Cross-sheet regime consistency
