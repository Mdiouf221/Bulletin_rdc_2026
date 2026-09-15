"""
sync_graphiques_word.py
=======================
Synchronise une copie DOCX avec une copie XLSX de graphiques, en conservant
strictement les maîtres intacts.

Principes :
  - le classeur le plus récent sert de modèle de présentation ;
  - les valeurs viennent d'une source indépendante et régénérable :
      * annexe B : payloads reconstruits depuis la base ESS + questionnaire ;
      * annexe C : classeur temporaire régénéré via generer_annexe_c_classeur.py ;
  - seules les cellules de données sont mises à jour ;
  - la sauvegarde du XLSX de sortie passe par Excel COM (préservation des graphiques).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent
OUTPUT_DIR = WORKSPACE / "10_output"
DEFAULT_MASTER_DOCX = OUTPUT_DIR / "bulletin_relecture_2026-09-03.docx"
COM_HELPER = SCRIPT_DIR / "sync_graphiques_word_com.ps1"

COPY_MARKER = "__sync_copy__"
TEMP_DATA_MARKER = "__sync_data__"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    size: int
    sha256: str
    mtime_ns: int


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_file(path: Path) -> FileSnapshot:
    st = path.stat()
    return FileSnapshot(path=path, size=st.st_size, sha256=_sha256(path), mtime_ns=st.st_mtime_ns)


def snapshots_equal(a: FileSnapshot, b: FileSnapshot) -> bool:
    return a.size == b.size and a.sha256 == b.sha256 and a.mtime_ns == b.mtime_ns


def _normalize_text(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip().lower().replace("\u00a0", " ")


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _equivalent(a: Any, b: Any) -> bool:
    if a is None and b is None:
        return True
    if _is_number(a) and _is_number(b):
        return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-9)
    return a == b


def _run(cmd: list[str], *, label: str) -> str:
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE),
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode != 0:
        details = (res.stderr or res.stdout or "Erreur non détaillée").strip()
        raise RuntimeError(f"[{label}] échec ({res.returncode}) :\n{details}")
    return (res.stdout or "").strip()


def _is_generated_copy(path: Path) -> bool:
    name = path.name.lower()
    return COPY_MARKER.lower() in name or TEMP_DATA_MARKER.lower() in name


def create_timestamped_copy(source: Path, output_dir: Path, stamp: str) -> Path:
    base = f"{source.stem}{COPY_MARKER}_{stamp}"
    candidate = output_dir / f"{base}{source.suffix}"
    i = 2
    while candidate.exists():
        candidate = output_dir / f"{base}_{i}{source.suffix}"
        i += 1
    shutil.copy2(source, candidate)
    return candidate


def discover_graph_workbooks(output_dir: Path) -> list[Path]:
    found = []
    for p in sorted(output_dir.glob("*graphiques*.xlsx")):
        if p.name.startswith("~$"):
            continue
        if _is_generated_copy(p):
            continue
        found.append(p)
    return found


def choose_latest_workbook(candidates: list[Path], linked_names: set[str]) -> Path:
    if not candidates:
        raise FileNotFoundError("Aucun classeur de graphiques (*.xlsx) trouvé.")
    linked = [p for p in candidates if p.name.lower() in linked_names]
    pool = linked or candidates
    pool.sort(key=lambda p: p.stat().st_mtime_ns, reverse=True)
    return pool[0]


def inspect_word_links(docx_path: Path) -> dict[str, Any]:
    escaped_docx = str(docx_path).replace("'", "''")
    ps = r"""
$ErrorActionPreference = "Stop"
$word = $null
$doc = $null
try {
  $DocxPath = '__DOCX_PATH__'
  $DocxPath = [System.IO.Path]::GetFullPath($DocxPath)
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.DisplayAlerts = 0
  $doc = $word.Documents.Open($DocxPath, $false, $true)

  $counts = @{}
  $linked = 0
  for ($i=1; $i -le $doc.InlineShapes.Count; $i++) {
    $s = $doc.InlineShapes.Item($i)
    try {
      $src = ""
      try { $src = [string]$s.LinkFormat.SourceName } catch {}
      if (-not [string]::IsNullOrWhiteSpace($src) -and $src.ToLowerInvariant() -ne "null") {
        $linked += 1
        $base = [System.IO.Path]::GetFileName($src).ToLowerInvariant()
        if ([string]::IsNullOrWhiteSpace($base)) { $base = $src.ToLowerInvariant() }
        if ($counts.ContainsKey($base)) { $counts[$base] += 1 } else { $counts[$base] = 1 }
      }
    } finally {
      try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($s) } catch {}
    }
  }
  [PSCustomObject]@{
    inline_total = [int]$doc.InlineShapes.Count
    linked_total = [int]$linked
    by_workbook = $counts
  } | ConvertTo-Json -Depth 6 -Compress
}
finally {
  if ($doc -ne $null) {
    try { $doc.Close($false) } catch {}
    try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($doc) } catch {}
  }
  if ($word -ne $null) {
    try { $word.Quit() } catch {}
    try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) } catch {}
  }
  [GC]::Collect()
  [GC]::WaitForPendingFinalizers()
}
""".replace("__DOCX_PATH__", escaped_docx)

    out = _run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        label="WORD_INSPECT",
    )
    data = json.loads(out or "{}")
    by = data.get("by_workbook")
    if isinstance(by, dict):
        data["by_workbook"] = {str(k).lower(): int(v) for k, v in by.items()}
    elif isinstance(by, list):
        mapped: dict[str, int] = {}
        for item in by:
            if isinstance(item, dict) and item.get("Key") is not None:
                mapped[str(item["Key"]).lower()] = int(item.get("Value") or 0)
        data["by_workbook"] = mapped
    else:
        data["by_workbook"] = {}
    return data


def _find_header_row(ws, expected_columns: list[str]) -> int:
    expected = [_normalize_text(c) for c in expected_columns]
    max_scan = min(ws.max_row, 300)
    width = len(expected_columns)
    for r in range(1, max_scan + 1):
        got = [_normalize_text(ws.cell(row=r, column=c).value) for c in range(1, width + 1)]
        if got == expected:
            return r
    raise ValueError(f"En-tête introuvable dans '{ws.title}' : {expected_columns}")


def _find_year_header_row(ws) -> int:
    max_scan = min(ws.max_row, 300)
    for r in range(1, max_scan + 1):
        if _normalize_text(ws.cell(row=r, column=1).value) == "année":
            return r
    raise ValueError(f"Ligne 'Année' introuvable dans '{ws.title}'.")


def _read_columns_from_row(ws, row: int) -> list[str]:
    cols = []
    c = 1
    while c <= ws.max_column:
        v = ws.cell(row=row, column=c).value
        if v is None or str(v).strip() == "":
            break
        cols.append(str(v))
        c += 1
    return cols


def _build_year_row_map(ws, header_row: int) -> dict[int, int]:
    year_map: dict[int, int] = {}
    row = header_row + 1
    empty = 0
    max_scan = max(ws.max_row + 50, header_row + 1)
    while row <= max_scan:
        raw = ws.cell(row=row, column=1).value
        if raw is None or str(raw).strip() == "":
            empty += 1
            if empty >= 3:
                break
            row += 1
            continue
        empty = 0
        if _is_number(raw):
            y = int(raw)
            if 1900 <= y <= 2200:
                if y in year_map:
                    raise ValueError(f"Année dupliquée {y} dans '{ws.title}'.")
                year_map[y] = row
        row += 1
    if not year_map:
        raise ValueError(f"Aucune année détectée dans '{ws.title}'.")
    return year_map


def _resolve_series_column_mapping(
    model_columns: list[str],
    source_columns: list[str],
    *,
    sheet_name: str,
) -> tuple[dict[int, int], list[dict[str, str]]]:
    if not model_columns or not source_columns:
        raise ValueError(f"Séries vides pour '{sheet_name}'.")
    if _normalize_text(model_columns[0]) != "année" or _normalize_text(source_columns[0]) != "année":
        raise ValueError(f"Colonne d'année absente/incompatible sur '{sheet_name}'.")

    model_series = model_columns[1:]
    source_series = source_columns[1:]
    if len(model_series) != len(source_series):
        raise ValueError(
            f"Nombre de séries incompatible sur '{sheet_name}' : "
            f"modèle={len(model_series)} source={len(source_series)}."
        )

    norm_to_model_indices: dict[str, list[int]] = {}
    for idx, name in enumerate(model_series, start=2):
        norm_to_model_indices.setdefault(_normalize_text(name), []).append(idx)

    mapping: dict[int, int] = {}
    used_model_indices: set[int] = set()
    for src_idx, src_name in enumerate(source_series, start=2):
        key = _normalize_text(src_name)
        model_candidates = [i for i in norm_to_model_indices.get(key, []) if i not in used_model_indices]
        if len(model_candidates) == 1:
            model_idx = model_candidates[0]
            mapping[src_idx] = model_idx
            used_model_indices.add(model_idx)

    aliases: list[dict[str, str]] = []
    unmatched_src = [i for i in range(2, len(source_columns) + 1) if i not in mapping]
    unmatched_model = [i for i in range(2, len(model_columns) + 1) if i not in used_model_indices]
    unmatched_model_set = set(unmatched_model)

    for src_idx in unmatched_src[:]:
        if src_idx in unmatched_model_set:
            mapping[src_idx] = src_idx
            used_model_indices.add(src_idx)
            unmatched_model_set.remove(src_idx)
            unmatched_src.remove(src_idx)
            aliases.append(
                {
                    "sheet": sheet_name,
                    "source_series": source_columns[src_idx - 1],
                    "model_series": model_columns[src_idx - 1],
                }
            )

    if unmatched_src or unmatched_model_set:
        raise ValueError(
            f"Séries incompatibles sur '{sheet_name}' : "
            f"source_non_mappées={unmatched_src}, modèle_non_mappées={sorted(unmatched_model_set)}."
        )
    return mapping, aliases


def _parse_workbook_kind(path: Path) -> str:
    lower = path.name.lower()
    if "annexe_b_graphiques_par_institution" in lower:
        return "annexe_b"
    if "annexe_c_graphiques_par_indicateur" in lower:
        return "annexe_c"
    # Heuristique
    wb = load_workbook(path, data_only=True)
    try:
        if "index" in wb.sheetnames:
            ws = wb["index"]
            a1 = _normalize_text(ws.cell(row=1, column=1).value)
            if a1 == "institution":
                return "annexe_b"
            c3 = _normalize_text(ws.cell(row=3, column=3).value)
            if c3 == "clé":
                return "annexe_c"
        raise ValueError(f"Type de classeur non reconnu : {path.name}")
    finally:
        wb.close()


def _extract_annexe_b_model_entries(model_wb_path: Path) -> list[dict[str, str]]:
    wb = load_workbook(model_wb_path, data_only=True)
    try:
        entries: list[dict[str, str]] = []
        if "index" in wb.sheetnames:
            idx = wb["index"]
            if _normalize_text(idx.cell(row=1, column=1).value) == "institution":
                row = 2
                while True:
                    inst = idx.cell(row=row, column=1).value
                    key = idx.cell(row=row, column=2).value
                    sheet_name = idx.cell(row=row, column=3).value
                    if not sheet_name:
                        break
                    entries.append(
                        {
                            "sheet_name": str(sheet_name).strip(),
                            "institution": str(inst or "").strip(),
                            "chart_key": str(key or "").strip(),
                        }
                    )
                    row += 1
        if entries:
            return entries

        # Fallback : métadonnées de feuille (B1/B2)
        for ws in wb.worksheets:
            if ws.title.lower() == "index":
                continue
            if len(getattr(ws, "_charts", [])) <= 0:
                continue
            entries.append(
                {
                    "sheet_name": ws.title,
                    "institution": str(ws["B1"].value or "").strip(),
                    "chart_key": str(ws["B2"].value or "").strip(),
                }
            )
        if not entries:
            raise ValueError("Aucune feuille de graphiques détectée pour l'annexe B.")
        return entries
    finally:
        wb.close()


def _derive_annexe_b_source_payloads(required_entries: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    import generer_annexe_b_visuels as annexe_b  # type: ignore
    from visualiser_regimes import DB_PATH, load_all  # type: ignore

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Base ESS introuvable : {DB_PATH}")

    required_institutions = sorted({e["institution"] for e in required_entries})
    if not required_institutions:
        raise ValueError("Aucune institution requise pour l'annexe B.")

    regimes, _prestations, _regime_meta, _prestation_meta = load_all(DB_PATH)
    questionnaire = annexe_b.load_questionnaire_data()

    by_key: dict[str, dict[str, Any]] = {}
    for inst in required_institutions:
        settings = questionnaire.get(inst) or {}
        _entries, payloads = annexe_b.generate_charts(regimes, inst, settings, export_images=False)
        _sex_files, sex_payload = annexe_b.generate_sex_pie_charts(regimes, inst, settings, export_images=False)
        for payload in [*payloads, sex_payload]:
            key = f"{payload.get('institution','').strip()}::{payload.get('chart_key','').strip()}"
            by_key[key] = payload
    return by_key


def build_annexe_b_update_plan(model_workbook_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    model_entries = _extract_annexe_b_model_entries(model_workbook_path)
    source_map = _derive_annexe_b_source_payloads(model_entries)

    wb = load_workbook(model_workbook_path, data_only=True)
    try:
        plan_sheets = []
        workbook_chart_count = 0
        cells_examined = 0
        cells_changed = 0
        cells_unchanged = 0
        series_aliases: list[dict[str, str]] = []

        required_keys = {f"{e['institution']}::{e['chart_key']}" for e in model_entries}
        missing = sorted(required_keys - set(source_map.keys()))
        if missing:
            raise ValueError(f"Sources annexe B manquantes : {', '.join(missing)}")

        for entry in model_entries:
            sheet_name = entry["sheet_name"]
            if sheet_name not in wb.sheetnames:
                raise ValueError(f"Feuille manquante dans modèle annexe B : {sheet_name}")
            ws = wb[sheet_name]
            actual_charts = len(getattr(ws, "_charts", []))
            workbook_chart_count += actual_charts

            source_key = f"{entry['institution']}::{entry['chart_key']}"
            source = source_map[source_key]
            source_columns = [str(c) for c in (source.get("columns") or [])]
            source_rows = source.get("rows") or []
            if len(source_columns) < 2:
                raise ValueError(f"Colonnes source invalides pour {source_key}.")
            if not isinstance(source_rows, list):
                raise ValueError(f"Lignes source invalides pour {source_key}.")

            expected_chart_count = 2 if entry["chart_key"] == "sexe" else 1
            if actual_charts != expected_chart_count:
                raise ValueError(
                    f"Feuille '{sheet_name}' : {actual_charts} graphique(s), {expected_chart_count} attendu(s)."
                )

            header_row = _find_year_header_row(ws)
            model_columns = _read_columns_from_row(ws, header_row)
            series_mapping, aliases = _resolve_series_column_mapping(
                model_columns=model_columns,
                source_columns=source_columns,
                sheet_name=sheet_name,
            )
            series_aliases.extend(aliases)

            year_map = _build_year_row_map(ws, header_row)
            updates = []
            years: list[int] = []
            for row_values in source_rows:
                if not isinstance(row_values, list) or len(row_values) != len(source_columns):
                    raise ValueError(f"Ligne source invalide ({source_key}).")
                if not _is_number(row_values[0]):
                    raise ValueError(f"Année source invalide ({source_key}) : {row_values[0]!r}")
                year = int(row_values[0])
                if year not in year_map:
                    raise ValueError(f"Année {year} absente de '{sheet_name}'.")
                years.append(year)
                model_row = year_map[year]
                for src_col in range(2, len(source_columns) + 1):
                    model_col = series_mapping[src_col]
                    new_val = row_values[src_col - 1]
                    old_val = ws.cell(row=model_row, column=model_col).value
                    changed = not _equivalent(new_val, old_val)
                    cells_examined += 1
                    if changed:
                        cells_changed += 1
                    else:
                        cells_unchanged += 1
                    updates.append(
                        {
                            "row": model_row,
                            "col": model_col,
                            "value": new_val,
                            "changed": changed,
                        }
                    )

            plan_sheets.append(
                {
                    "sheet_name": sheet_name,
                    "series": source_columns[1:],
                    "years": sorted(set(years)),
                    "expected_chart_count": expected_chart_count,
                    "updates": updates,
                }
            )

        plan = {"workbook_kind": "annexe_b", "sheets": plan_sheets}
        summary = {
            "mode": "annexe_b_db_questionnaire",
            "sheet_count": len(plan_sheets),
            "cells_examined": cells_examined,
            "cells_changed": cells_changed,
            "cells_unchanged": cells_unchanged,
            "series_alias_count": len(series_aliases),
            "series_aliases": series_aliases,
            "workbook_chart_count": workbook_chart_count,
        }
        return plan, summary
    finally:
        wb.close()


def _extract_annexe_c_source_from_workbook(path: Path) -> dict[str, dict[str, Any]]:
    wb = load_workbook(path, data_only=True)
    try:
        by_key: dict[str, dict[str, Any]] = {}
        for ws in wb.worksheets:
            if ws.title.lower() == "index":
                continue
            key = None
            for r in range(1, 40):
                if _normalize_text(ws.cell(row=r, column=1).value) == "clé":
                    key = str(ws.cell(row=r, column=2).value or "").strip()
                    break
            if not key:
                continue

            header_row = _find_header_row(ws, ["Année", "Indicateur (%)", "Numérateur", "Dénominateur"])
            year_map = _build_year_row_map(ws, header_row)
            years = sorted(year_map.keys())
            rows = []
            for y in years:
                rr = year_map[y]
                rows.append(
                    [
                        y,
                        ws.cell(row=rr, column=2).value,
                        ws.cell(row=rr, column=3).value,
                        ws.cell(row=rr, column=4).value,
                    ]
                )
            by_key[key] = {
                "sheet_name": ws.title,
                "columns": ["Année", "Indicateur (%)", "Numérateur", "Dénominateur"],
                "rows": rows,
                "chart_count": len(getattr(ws, "_charts", [])),
            }
        if not by_key:
            raise ValueError("Aucune feuille indicateur détectée dans la source annexe C temporaire.")
        return by_key
    finally:
        wb.close()


def _generate_annexe_c_temp_source(output_dir: Path) -> tuple[dict[str, dict[str, Any]], Path]:
    import generer_annexe_c_classeur as annexe_c  # type: ignore

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_path = output_dir / f"annexe_c_{TEMP_DATA_MARKER}_{stamp}.xlsx"
    summary = annexe_c.generate_annexe_c_workbook(tmp_path)
    src_path = Path(summary["output_path"])
    data = _extract_annexe_c_source_from_workbook(src_path)
    return data, src_path


def build_annexe_c_update_plan(model_workbook_path: Path, output_dir: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    source_map, temp_source = _generate_annexe_c_temp_source(output_dir)

    wb = load_workbook(model_workbook_path, data_only=True)
    try:
        plan_sheets = []
        workbook_chart_count = 0
        cells_examined = 0
        cells_changed = 0
        cells_unchanged = 0
        matched_keys: set[str] = set()

        for ws in wb.worksheets:
            if ws.title.lower() == "index":
                continue
            indicator_key = ""
            for r in range(1, 40):
                if _normalize_text(ws.cell(row=r, column=1).value) == "clé":
                    indicator_key = str(ws.cell(row=r, column=2).value or "").strip()
                    break
            if not indicator_key:
                continue
            if indicator_key not in source_map:
                raise ValueError(f"Source annexe C manquante pour l'indicateur '{indicator_key}'.")
            matched_keys.add(indicator_key)

            src = source_map[indicator_key]
            actual_charts = len(getattr(ws, "_charts", []))
            expected_charts = int(src["chart_count"])
            if actual_charts != expected_charts:
                raise ValueError(
                    f"Feuille '{ws.title}' ({indicator_key}) : {actual_charts} graphique(s), {expected_charts} attendu(s)."
                )
            workbook_chart_count += actual_charts

            header_row = _find_header_row(ws, src["columns"])
            year_map = _build_year_row_map(ws, header_row)
            src_rows = src["rows"]
            src_years = [int(r[0]) for r in src_rows]
            model_years = sorted(year_map.keys())
            if src_years != model_years:
                raise ValueError(
                    f"Années incompatibles sur '{ws.title}' ({indicator_key}) : "
                    f"modèle={model_years}, source={src_years}."
                )

            updates = []
            for src_row in src_rows:
                year = int(src_row[0])
                rr = year_map[year]
                for col in (2, 3, 4):
                    new_val = src_row[col - 1]
                    old_val = ws.cell(row=rr, column=col).value
                    changed = not _equivalent(new_val, old_val)
                    cells_examined += 1
                    if changed:
                        cells_changed += 1
                    else:
                        cells_unchanged += 1
                    updates.append({"row": rr, "col": col, "value": new_val, "changed": changed})

            plan_sheets.append(
                {
                    "sheet_name": ws.title,
                    "series": src["columns"][1:],
                    "years": model_years,
                    "expected_chart_count": expected_charts,
                    "updates": updates,
                }
            )

        missing_model_keys = sorted(set(source_map.keys()) - matched_keys)
        if missing_model_keys:
            raise ValueError(f"Indicateurs source absents du modèle annexe C : {', '.join(missing_model_keys)}")

        plan = {"workbook_kind": "annexe_c", "sheets": plan_sheets}
        summary = {
            "mode": "annexe_c_generated_temp",
            "sheet_count": len(plan_sheets),
            "cells_examined": cells_examined,
            "cells_changed": cells_changed,
            "cells_unchanged": cells_unchanged,
            "workbook_chart_count": workbook_chart_count,
        }
        return plan, summary, temp_source
    finally:
        wb.close()


def build_update_plan(model_workbook_path: Path, output_dir: Path) -> tuple[dict[str, Any], dict[str, Any], Path | None]:
    kind = _parse_workbook_kind(model_workbook_path)
    if kind == "annexe_b":
        plan, summary = build_annexe_b_update_plan(model_workbook_path)
        return plan, summary, None
    if kind == "annexe_c":
        plan, summary, temp_source = build_annexe_c_update_plan(model_workbook_path, output_dir)
        return plan, summary, temp_source
    raise ValueError(f"Type de classeur non supporté : {kind}")


def run_sync_with_com(
    *,
    workbook_copy: Path,
    word_copy: Path,
    source_workbook_name: str,
    update_plan_path: Path,
    word_mode: str,
    expected_word_target_count: int,
) -> dict[str, Any]:
    if not COM_HELPER.exists():
        raise FileNotFoundError(f"Script COM introuvable : {COM_HELPER}")
    out = _run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(COM_HELPER),
            "-WorkbookPath",
            str(workbook_copy),
            "-UpdatePlanPath",
            str(update_plan_path),
            "-DocxPath",
            str(word_copy),
            "-WorkbookSourceName",
            source_workbook_name,
            "-WordMode",
            word_mode,
            "-ExpectedWordTargetCount",
            str(expected_word_target_count),
        ],
        label="SYNC_COM",
    )
    return json.loads(out or "{}")


def apply_plan_with_openpyxl(workbook_path: Path, plan: dict[str, Any]) -> None:
    """
    Utilitaire de test (sans COM) :
    applique un plan en écrivant uniquement les cellules marquées changed=true.
    """
    wb = load_workbook(workbook_path)
    try:
        for sheet in plan.get("sheets", []):
            ws = wb[sheet["sheet_name"]]
            for u in sheet.get("updates", []):
                if not u.get("changed"):
                    continue
                ws.cell(row=int(u["row"]), column=int(u["col"])).value = u.get("value")
        wb.save(workbook_path)
    finally:
        wb.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Met à jour une copie DOCX/XLSX sur base de données régénérables, "
            "sans modifier les fichiers maîtres."
        )
    )
    parser.add_argument("--master-docx", default=str(DEFAULT_MASTER_DOCX), help="Chemin du Word maître.")
    parser.add_argument(
        "--workbook",
        default="",
        help="Classeur modèle explicite (sinon sélection automatique du plus récent pertinent).",
    )
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="Dossier de sortie des copies.")
    parser.add_argument("--word-mode", choices=("embedded", "linked"), default="embedded")
    parser.add_argument("--keep-plan", action="store_true", help="Conserve le plan JSON intermédiaire.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    master_docx = Path(args.master_docx).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not master_docx.exists():
        print(f"[ERREUR] Word maître introuvable : {master_docx}")
        return 1

    before_master = snapshot_file(master_docx)

    word_links = inspect_word_links(master_docx)
    linked_map = word_links.get("by_workbook") or {}
    linked_names = set(linked_map.keys())

    if args.workbook:
        source_workbook = Path(args.workbook).resolve()
        if not source_workbook.exists():
            print(f"[ERREUR] Classeur introuvable : {source_workbook}")
            return 1
        if _is_generated_copy(source_workbook):
            print(f"[ERREUR] Le classeur fourni est une copie/temporisation interdite : {source_workbook.name}")
            return 1
    else:
        candidates = discover_graph_workbooks(output_dir)
        source_workbook = choose_latest_workbook(candidates, linked_names)

    before_source = snapshot_file(source_workbook)

    source_name_lower = source_workbook.name.lower()
    expected_word_target_count = int(linked_map.get(source_name_lower, 0))
    if expected_word_target_count <= 0:
        raise RuntimeError(
            f"Aucun objet Word lié à '{source_workbook.name}' dans le document maître."
        )

    temp_source: Path | None = None
    try:
        plan, plan_summary, temp_source = build_update_plan(source_workbook, output_dir)
    finally:
        # Rien ici: suppression gérée plus bas après usage.
        pass

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workbook_copy = create_timestamped_copy(source_workbook, output_dir, stamp)
    word_copy = create_timestamped_copy(master_docx, output_dir, stamp)

    plan_path = output_dir / f"sync_plan{COPY_MARKER}_{stamp}.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        com_summary = run_sync_with_com(
            workbook_copy=workbook_copy,
            word_copy=word_copy,
            source_workbook_name=source_workbook.name,
            update_plan_path=plan_path,
            word_mode=args.word_mode,
            expected_word_target_count=expected_word_target_count,
        )
    finally:
        if not args.keep_plan and plan_path.exists():
            plan_path.unlink()
        if temp_source is not None and temp_source.exists():
            temp_source.unlink()

    after_master = snapshot_file(master_docx)
    after_source = snapshot_file(source_workbook)
    if not snapshots_equal(before_master, after_master):
        raise RuntimeError("Le Word maître a été modifié (interdit).")
    if not snapshots_equal(before_source, after_source):
        raise RuntimeError("Le classeur source a été modifié (interdit).")

    summary = {
        "master_docx": str(master_docx),
        "source_workbook": str(source_workbook),
        "word_copy": str(word_copy),
        "workbook_copy": str(workbook_copy),
        "selection": {
            "workbook_candidates": [p.name for p in discover_graph_workbooks(output_dir)],
            "linked_workbooks_in_word": linked_map,
            "selected_workbook": source_workbook.name,
            "selected_workbook_mtime": datetime.fromtimestamp(source_workbook.stat().st_mtime).isoformat(timespec="seconds"),
        },
        "plan": plan_summary,
        "word_targets_expected": expected_word_target_count,
        "word_vs_excel_gap": expected_word_target_count - int(plan_summary.get("workbook_chart_count") or 0),
        "com": com_summary,
        "copy_sizes": {
            "word_copy_bytes": word_copy.stat().st_size,
            "workbook_copy_bytes": workbook_copy.stat().st_size,
        },
        "sources_unchanged": {
            "master_docx": True,
            "source_workbook": True,
        },
        "temp_source_cleaned": (temp_source is None) or (not temp_source.exists()),
    }
    if summary["word_vs_excel_gap"] != 0:
        summary["word_vs_excel_gap_note"] = (
            "Le nombre d'objets Word liés au classeur peut différer du nombre de ChartObjects "
            "du classeur (objets dupliqués ou non-chart liés au même .xlsx)."
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
