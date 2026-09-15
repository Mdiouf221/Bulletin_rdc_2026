"""
exporter_word.py
----------------
Convertit le bulletin HTML en fichier Word (.docx) via Pandoc.

Usage :
    py 09_scripts/exporter_word.py
    py 09_scripts/exporter_word.py 10_output/bulletin_relecture_2026-06-26.html
    py 09_scripts/exporter_word.py --excel-charts embedded

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
    [EXCEL-CHARTS] Remplacement des PNG des annexes B et C par des graphiques Excel
              collés depuis Excel (liés ou incorporés), via COM Word/Excel
"""

import subprocess
import re
import os
import sys
import glob
import json
import argparse
import tempfile
from datetime import datetime
from typing import Any

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
ANNEXE_B_WORD_DATA = os.path.join(ROOT, "10_output", "annexe_B_graphiques_word.json")
ANNEXE_C_WORKBOOK = os.path.join(ROOT, "10_output", "annexe_C_graphiques_par_indicateur.xlsx")
EXCEL_CHART_LINK_SCRIPT = os.path.join(SCRIPTS_DIR, "lier_graphiques_annexe_b.ps1")
EXCEL_CHART_MODES = {"linked", "embedded", "png", "auto"}
ANNEXE_B_CHART_MODES = EXCEL_CHART_MODES  # Alias rétrocompatible

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
_EXCEL_CHART_LINK_STATE: dict[str, Any] = {"markers": 0, "manifest": None}


class ExcelChartPreparationError(RuntimeError):
    """Erreur de préparation des remplacements Excel (assets, mapping, préflight)."""


def _build_temp_artifact_path(prefix: str, suffix: str) -> str:
    safe_prefix = re.sub(r"[^A-Za-z0-9_.-]", "_", prefix).strip("_") or "tmp"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    token_prefix = "{}_{}_".format(safe_prefix, os.getpid())
    fd, path = tempfile.mkstemp(prefix=token_prefix, suffix=suffix, dir=OUTPUT_DIR)
    os.close(fd)
    os.remove(path)
    return path


def _safe_unlink(path: str | None) -> None:
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _docx_lock_path(docx_path: str) -> str:
    return docx_path + ".lock"


def _acquire_docx_lock(docx_path: str) -> str:
    lock_path = _docx_lock_path(docx_path)
    lock_dir = os.path.dirname(lock_path)
    if lock_dir:
        os.makedirs(lock_dir, exist_ok=True)
    payload = json.dumps(
        {
            "pid": os.getpid(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "docx": docx_path,
        },
        ensure_ascii=False,
    )
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        lock_owner = ""
        try:
            with open(lock_path, "r", encoding="utf-8") as f:
                lock_owner = f.read().strip()
        except OSError:
            lock_owner = ""
        owner_message = f" Détails: {lock_owner}" if lock_owner else ""
        raise RuntimeError(
            "Un export Word cible déjà ce fichier: {}. "
            "Attendre la fin de l'export en cours ou supprimer le verrou stale: {}{}".format(
                os.path.basename(docx_path),
                lock_path,
                owner_message,
            )
        ) from exc
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(payload)
    return lock_path


def _release_docx_lock(lock_path: str | None) -> None:
    if not lock_path:
        return
    try:
        os.remove(lock_path)
    except FileNotFoundError:
        return


def _normalize_excel_chart_mode(mode: str | None) -> str:
    value = (mode or "auto").strip().lower()
    if value not in EXCEL_CHART_MODES:
        raise ValueError(
            "Mode excel-charts invalide '{}'. Valeurs acceptées : {}.".format(
                mode, ", ".join(sorted(EXCEL_CHART_MODES))
            )
        )
    return value


def _normalize_annexe_b_chart_mode(mode: str | None) -> str:
    """Alias rétrocompatible."""
    return _normalize_excel_chart_mode(mode)


def _office_com_available() -> bool:
    command = (
        "$word = $null; $excel = $null; "
        "try { "
        "$word = New-Object -ComObject Word.Application; "
        "$excel = New-Object -ComObject Excel.Application; "
        "exit 0 "
        "} catch { "
        "exit 1 "
        "} finally { "
        "if ($word -ne $null) { try { $word.Quit() } catch {}; "
        "try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word) } catch {} } "
        "if ($excel -ne $null) { try { $excel.Quit() } catch {}; "
        "try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } catch {} } "
        "[GC]::Collect(); [GC]::WaitForPendingFinalizers(); "
        "}"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return result.returncode == 0


def _resolve_excel_chart_mode(
    requested_mode: str,
    *,
    com_probe=_office_com_available,
) -> tuple[str, str]:
    mode = _normalize_excel_chart_mode(requested_mode)
    if mode != "auto":
        return mode, f"mode explicite '{mode}'"
    if com_probe():
        return "embedded", "mode auto -> COM Word/Excel detecte, insertion Excel incorporee activee"
    return "png", "mode auto -> COM Word/Excel indisponible, conservation des PNG"


def _resolve_annexe_b_chart_mode(
    requested_mode: str,
    *,
    com_probe=_office_com_available,
) -> tuple[str, str]:
    """Alias rétrocompatible."""
    return _resolve_excel_chart_mode(requested_mode, com_probe=com_probe)


def find_latest_html():
    """Retourne le fichier HTML bulletin_relecture le plus récent dans 10_output."""
    pattern = os.path.join(OUTPUT_DIR, "bulletin_relecture_*.html")
    files = glob.glob(pattern)
    if not files:
        sys.exit("Aucun fichier bulletin_relecture_*.html trouvé dans 10_output/")
    return max(files, key=os.path.getmtime)


def _load_annexe_b_word_data():
    if not os.path.exists(ANNEXE_B_WORD_DATA):
        return {}
    try:
        with open(ANNEXE_B_WORD_DATA, "r", encoding="utf-8") as f:
            payload = json.load(f)
        charts = payload.get("charts") if isinstance(payload, dict) else {}
        if not isinstance(charts, dict):
            return {}
        payload.setdefault("xlsx", "10_output/annexe_B_graphiques_par_institution.xlsx")
        return payload
    except (OSError, json.JSONDecodeError):
        return {}


def _resolve_annexe_b_workbook_path(word_data: dict) -> str:
    workbook_rel = word_data.get("xlsx") if isinstance(word_data, dict) else None
    if not workbook_rel:
        return ""
    return os.path.abspath(os.path.join(ROOT, str(workbook_rel).replace("/", os.sep)))


def _resolve_annexe_c_workbook_path() -> str:
    return os.path.abspath(ANNEXE_C_WORKBOOK)


def _probe_excel_workbook_open_error(workbook_path: str) -> str | None:
    escaped_path = workbook_path.replace("'", "''")
    command = (
        "$excel = $null; $wb = $null; "
        "try { "
        "$excel = New-Object -ComObject Excel.Application; "
        "$excel.Visible = $false; "
        "$excel.DisplayAlerts = $false; "
        f"$wb = $excel.Workbooks.Open('{escaped_path}', 0, $true); "
        "if ($wb -ne $null) { $wb.Close($false) }; "
        "exit 0 "
        "} catch { "
        "Write-Output $_.Exception.Message; "
        "exit 1 "
        "} finally { "
        "if ($wb -ne $null) { try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($wb) } catch {} } "
        "if ($excel -ne $null) { try { $excel.Quit() } catch {}; "
        "try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } catch {} } "
        "[GC]::Collect(); [GC]::WaitForPendingFinalizers(); "
        "}"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode == 0:
        return None
    return (result.stdout or result.stderr or "Erreur inconnue d'ouverture Excel COM.").strip()


def _annexe_b_word_assets_ready(word_data: dict, *, require_com_compatible: bool = False) -> bool:
    charts = word_data.get("charts") if isinstance(word_data, dict) else {}
    if not isinstance(charts, dict) or not charts:
        return False
    workbook_path = _resolve_annexe_b_workbook_path(word_data)
    if not workbook_path or not os.path.isfile(workbook_path):
        return False
    if not require_com_compatible:
        return True
    return _probe_excel_workbook_open_error(workbook_path) is None


def _ensure_annexe_b_word_data(*, require_com_compatible: bool = False):
    # Rétrocompatibilité : ce helper ne régénère plus aucun actif.
    current = _load_annexe_b_word_data()
    if require_com_compatible and _annexe_b_word_assets_ready(current, require_com_compatible=True):
        return current
    return current


def _load_workbook_chart_counts(workbook_path: str) -> dict[str, int]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ExcelChartPreparationError(
            "openpyxl est requis pour lire les classeurs Excel d'annexe B/C."
        ) from exc

    try:
        workbook = load_workbook(workbook_path, data_only=True)
    except OSError as exc:
        raise ExcelChartPreparationError(
            f"Lecture impossible du classeur Excel : {workbook_path} ({exc})"
        ) from exc

    try:
        return {ws.title: len(getattr(ws, "_charts", [])) for ws in workbook.worksheets}
    finally:
        workbook.close()


def _coerce_int(value: Any, *, field_name: str, min_value: int = 0) -> int:
    if isinstance(value, bool):
        raise ExcelChartPreparationError(f"{field_name} invalide (bool interdit).")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, float) and value.is_integer():
        parsed = int(value)
    elif isinstance(value, str) and value.strip():
        try:
            parsed = int(value.strip())
        except ValueError as exc:
            raise ExcelChartPreparationError(
                f"{field_name} invalide ('{value}') : entier attendu."
            ) from exc
    else:
        raise ExcelChartPreparationError(f"{field_name} invalide : valeur absente.")

    if parsed < min_value:
        raise ExcelChartPreparationError(f"{field_name} invalide : minimum attendu = {min_value}.")
    return parsed


def _normalize_chart_indices(
    chart_meta: dict[str, Any],
    *,
    chart_count: int,
    image_name: str,
    sheet_name: str,
) -> list[int]:
    raw_indices = chart_meta.get("chart_indices")
    if raw_indices is None and "chart_index" in chart_meta:
        raw_indices = [chart_meta.get("chart_index")]

    if raw_indices is None:
        if chart_count <= 0:
            raise ExcelChartPreparationError(
                f"Image '{image_name}' (feuille '{sheet_name}') : aucun ChartObject disponible."
            )
        return list(range(1, chart_count + 1))

    if isinstance(raw_indices, (str, int, float)):
        raw_items: list[Any] = [raw_indices]
    elif isinstance(raw_indices, list):
        raw_items = raw_indices
    else:
        raise ExcelChartPreparationError(
            f"Image '{image_name}' : chart_indices doit être une liste d'entiers."
        )

    normalized: list[int] = []
    seen: set[int] = set()
    for raw_idx in raw_items:
        idx = _coerce_int(
            raw_idx,
            field_name=f"chart_index ({image_name}/{sheet_name})",
            min_value=1,
        )
        if idx > chart_count:
            raise ExcelChartPreparationError(
                f"Image '{image_name}' : chart_index {idx} hors plage pour '{sheet_name}' "
                f"({chart_count} graphique(s))."
            )
        if idx not in seen:
            normalized.append(idx)
            seen.add(idx)
    if not normalized:
        raise ExcelChartPreparationError(
            f"Image '{image_name}' : aucun chart_index exploitable."
        )
    return normalized


def _build_annexe_b_chart_sources(word_data: dict, workbook_path: str) -> dict[str, list[dict[str, Any]]]:
    charts = word_data.get("charts") if isinstance(word_data, dict) else {}
    if not isinstance(charts, dict) or not charts:
        raise ExcelChartPreparationError(
            f"Manifeste annexe B introuvable ou vide : {ANNEXE_B_WORD_DATA}"
        )

    chart_counts = _load_workbook_chart_counts(workbook_path)
    sources: dict[str, list[dict[str, Any]]] = {}

    for image_name, chart_meta in charts.items():
        if not isinstance(chart_meta, dict):
            continue
        sheet_name = str(chart_meta.get("sheet_name") or "").strip()
        if not sheet_name:
            continue
        if sheet_name not in chart_counts:
            raise ExcelChartPreparationError(
                f"Feuille annexe B introuvable dans le classeur : {sheet_name}"
            )
        chart_indices = _normalize_chart_indices(
            chart_meta,
            chart_count=chart_counts[sheet_name],
            image_name=str(image_name),
            sheet_name=sheet_name,
        )
        filename = os.path.basename(str(image_name).replace("\\", "/")).lower()
        sources[filename] = [
            {
                "workbook_key": "annexe_b",
                "sheet_name": sheet_name,
                "chart_index": idx,
                "image_filename": str(image_name),
            }
            for idx in chart_indices
        ]
    return sources


def _load_annexe_c_sheet_map(workbook_path: str) -> dict[str, dict[str, Any]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ExcelChartPreparationError(
            "openpyxl est requis pour lire les classeurs Excel d'annexe C."
        ) from exc

    try:
        workbook = load_workbook(workbook_path, data_only=True)
    except OSError as exc:
        raise ExcelChartPreparationError(
            f"Lecture impossible du classeur annexe C : {workbook_path} ({exc})"
        ) from exc

    mapping: dict[str, dict[str, Any]] = {}
    try:
        if "index" in workbook.sheetnames:
            ws = workbook["index"]
            for row in range(4, ws.max_row + 1):
                indicator_key = ws.cell(row=row, column=3).value
                sheet_name = ws.cell(row=row, column=5).value
                chart_count_raw = ws.cell(row=row, column=6).value
                if not indicator_key or not sheet_name:
                    continue
                indicator = str(indicator_key).strip()
                sheet = str(sheet_name).strip()
                chart_count = _coerce_int(
                    chart_count_raw if chart_count_raw is not None else 0,
                    field_name=f"chart_count (index annexe C, indicateur {indicator})",
                    min_value=0,
                )
                mapping[indicator] = {"sheet_name": sheet, "chart_count": chart_count}

        if mapping:
            return mapping

        # Fallback déterministe basé sur la convention C<section>_<indicator_key>.
        for ws in workbook.worksheets:
            if ws.title.lower() == "index":
                continue
            match = re.match(r"^C\d+_(.+)$", ws.title)
            if not match:
                continue
            indicator = match.group(1).strip()
            mapping[indicator] = {
                "sheet_name": ws.title,
                "chart_count": len(getattr(ws, "_charts", [])),
            }
        return mapping
    finally:
        workbook.close()


def _build_annexe_c_chart_sources(workbook_path: str) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    sheet_map = _load_annexe_c_sheet_map(workbook_path)
    if not sheet_map:
        raise ExcelChartPreparationError(
            f"Impossible de dériver la correspondance des feuilles annexe C depuis : {workbook_path}"
        )

    sources: dict[str, list[dict[str, Any]]] = {}
    for indicator_key, info in sorted(sheet_map.items()):
        sheet_name = str(info.get("sheet_name") or "").strip()
        chart_count = _coerce_int(
            info.get("chart_count", 0),
            field_name=f"chart_count annexe C ({indicator_key})",
            min_value=0,
        )
        if not sheet_name:
            continue
        if chart_count >= 1:
            sources[f"annexe_c_{indicator_key}_indicateur.png"] = [
                {
                    "workbook_key": "annexe_c",
                    "sheet_name": sheet_name,
                    "chart_index": 1,
                    "image_filename": f"annexe_C_{indicator_key}_indicateur.png",
                }
            ]
        if chart_count >= 2:
            sources[f"annexe_c_{indicator_key}_numerateur.png"] = [
                {
                    "workbook_key": "annexe_c",
                    "sheet_name": sheet_name,
                    "chart_index": 2,
                    "image_filename": f"annexe_C_{indicator_key}_numerateur.png",
                }
            ]
    return sources, sheet_map


def _replace_excel_images_with_markers(html: str) -> tuple[str, dict[str, Any]]:
    needs_annexe_b = bool(re.search(r'annexe_B_[^"]+\.png', html, flags=re.IGNORECASE))
    needs_annexe_c = bool(re.search(r'annexe_C_[^"]+\.png', html, flags=re.IGNORECASE))
    if not needs_annexe_b and not needs_annexe_c:
        return html, {"version": 1, "workbooks": {}, "charts": []}

    source_map: dict[str, list[dict[str, Any]]] = {}
    workbooks: dict[str, str] = {}
    annexe_c_sheet_map: dict[str, dict[str, Any]] = {}

    if needs_annexe_b:
        annexe_b_data = _load_annexe_b_word_data()
        workbook_b = _resolve_annexe_b_workbook_path(annexe_b_data)
        if not workbook_b or not os.path.isfile(workbook_b):
            raise ExcelChartPreparationError(
                f"Classeur annexe B introuvable : {workbook_b or 'valeur absente dans le manifeste'}"
            )
        source_map.update(_build_annexe_b_chart_sources(annexe_b_data, workbook_b))
        workbooks["annexe_b"] = workbook_b

    if needs_annexe_c:
        workbook_c = _resolve_annexe_c_workbook_path()
        if not os.path.isfile(workbook_c):
            raise ExcelChartPreparationError(f"Classeur annexe C introuvable : {workbook_c}")
        annexe_c_sources, annexe_c_sheet_map = _build_annexe_c_chart_sources(workbook_c)
        source_map.update(annexe_c_sources)
        workbooks["annexe_c"] = workbook_c

    planned_entries: list[dict[str, Any]] = []
    errors: list[str] = []
    marker_counter = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal marker_counter
        full = match.group(0)
        src = match.group(1)
        filename = os.path.basename(src.replace("\\", "/"))
        filename_lower = filename.lower()
        source_entries = source_map.get(filename_lower)

        if not source_entries:
            if filename_lower.startswith("annexe_b_"):
                errors.append(f"Image annexe B sans correspondance manifeste : {filename}")
            else:
                c_match = re.match(
                    r"^annexe_c_(.+)_(indicateur|numerateur)\.png$",
                    filename_lower,
                    flags=re.IGNORECASE,
                )
                if c_match:
                    indicator_key = c_match.group(1)
                    chart_kind = c_match.group(2)
                    required_index = 1 if chart_kind == "indicateur" else 2
                    details = annexe_c_sheet_map.get(indicator_key)
                    if details:
                        sheet_name = details.get("sheet_name")
                        count = details.get("chart_count")
                        errors.append(
                            "Image {} sans ChartObject compatible : feuille '{}', "
                            "{} graphique(s), index {} requis.".format(
                                filename, sheet_name, count, required_index
                            )
                        )
                    else:
                        errors.append(
                            f"Image annexe C sans indicateur correspondant dans le classeur : {filename}"
                        )
            return full

        markers: list[str] = []
        for source_entry in source_entries:
            marker_counter += 1
            marker = f"[[EXCEL_CHART:{marker_counter:04d}]]"
            markers.append(marker)
            planned_entries.append(
                {
                    "marker": marker,
                    "sequence": marker_counter,
                    "workbook_key": source_entry["workbook_key"],
                    "sheet_name": source_entry["sheet_name"],
                    "chart_index": source_entry["chart_index"],
                    "image_filename": filename,
                }
            )
        return "<br/>".join(markers)

    updated_html = re.sub(
        r'<img[^>]*src="([^"]+\.(?:png|PNG))"[^>]*>',
        _replace,
        html,
        flags=re.IGNORECASE,
    )

    if errors:
        bullet_list = "\n - ".join(errors)
        raise ExcelChartPreparationError(
            "Incohérences de mapping Excel détectées :\n - {}".format(bullet_list)
        )

    return updated_html, {"version": 1, "workbooks": workbooks, "charts": planned_entries}


def _inject_annexe_b_link_markers(html: str, word_data: dict) -> str:
    """
    Alias historique conservé pour les tests existants.
    Remplace uniquement les PNG annexe B en s'appuyant sur le mapping actuel.
    """
    workbook_path = _resolve_annexe_b_workbook_path(word_data)
    if not workbook_path or not os.path.isfile(workbook_path):
        return html

    source_map = _build_annexe_b_chart_sources(word_data, workbook_path)
    marker_counter = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal marker_counter
        src = match.group(1)
        filename = os.path.basename(src.replace("\\", "/")).lower()
        entries = source_map.get(filename)
        if not entries:
            return match.group(0)
        markers: list[str] = []
        single_chart = len(entries) == 1
        for _entry in entries:
            marker_counter += 1
            if single_chart:
                markers.append(f"[[ANNEXE_B_CHART:{_entry['sheet_name']}]]")
            else:
                markers.append(
                    f"[[ANNEXE_B_CHART:{_entry['sheet_name']}#{_entry['chart_index']}]]"
                )
        return "<br/>".join(markers)

    return re.sub(
        r'<img[^>]*src="([^"]*annexe_B_[^"]+\.png)"[^>]*>',
        _replace,
        html,
        flags=re.IGNORECASE,
    )


def _insert_excel_charts(docx_path: str, *, paste_mode: str):
    state = _EXCEL_CHART_LINK_STATE
    marker_count = int(state.get("markers") or 0)
    manifest = state.get("manifest")
    if marker_count == 0:
        return
    if not isinstance(manifest, dict) or not manifest.get("charts"):
        raise RuntimeError("Manifeste Excel absent alors que des marqueurs sont attendus.")
    if not os.path.isfile(EXCEL_CHART_LINK_SCRIPT):
        raise FileNotFoundError(f"Script de liaison Word/Excel introuvable : {EXCEL_CHART_LINK_SCRIPT}")

    manifest_tmp = _build_temp_artifact_path("tmp_export_word_excel_manifest", ".json")
    with open(manifest_tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", EXCEL_CHART_LINK_SCRIPT,
        "-DocxPath", os.path.abspath(docx_path),
        "-ManifestPath", os.path.abspath(manifest_tmp),
        "-ExpectedCount", str(marker_count),
        "-PasteMode", paste_mode,
    ]
    diagnostic_log_path = os.environ.get("EXCEL_CHART_HELPER_LOG_PATH", "").strip()
    if diagnostic_log_path:
        command.extend(["-LogPath", os.path.abspath(diagnostic_log_path)])
    timeout_seconds = max(120, min(1800, marker_count * 20))
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Timeout de l'insertion COM après {} s ({} graphique(s) attendu(s)).".format(
                timeout_seconds,
                marker_count,
            )
        ) from exc
    finally:
        _safe_unlink(manifest_tmp)

    if result.returncode != 0:
        details = (result.stderr or result.stdout or "Erreur COM non détaillée.").strip()
        raise RuntimeError(f"Échec de l'insertion des graphiques Excel dans Word :\n{details}")
    output = result.stdout.strip()
    if output:
        print(output)


def _insert_linked_annexe_b_charts(docx_path: str, word_data: dict, *, paste_mode: str):
    """Alias rétrocompatible."""
    del word_data
    _insert_excel_charts(docx_path, paste_mode=paste_mode)


# ---------------------------------------------------------------------------
# Corrections HTML appliquées avant conversion
# ---------------------------------------------------------------------------

def apply_corrections(
    html: str,
    *,
    excel_chart_mode: str = "auto",
    annexe_b_chart_mode: str | None = None,
) -> str:
    """
    Applique toutes les corrections HTML avant l'export Word.
    Ajouter ici les nouveaux correctifs au fil des retours.
    """
    requested_mode = annexe_b_chart_mode if annexe_b_chart_mode is not None else excel_chart_mode
    mode = _normalize_excel_chart_mode(requested_mode)
    _EXCEL_CHART_LINK_STATE["markers"] = 0
    _EXCEL_CHART_LINK_STATE["manifest"] = None

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

    if mode in {"linked", "embedded"}:
        # [EXCEL-CHARTS] Remplacer les PNG B/C par des marqueurs uniques.
        # Le collage OLE Word/Excel est fait après Pandoc via helper COM.
        html, manifest = _replace_excel_images_with_markers(html)
        _EXCEL_CHART_LINK_STATE["manifest"] = manifest
        _EXCEL_CHART_LINK_STATE["markers"] = len(manifest.get("charts") or [])

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

def _ensure_excel_workbooks_com_compatible(manifest: dict[str, Any]) -> None:
    workbooks = manifest.get("workbooks") if isinstance(manifest, dict) else {}
    if not isinstance(workbooks, dict):
        return

    errors: list[str] = []
    for workbook_key, workbook_path in sorted(workbooks.items()):
        if not workbook_path or not isinstance(workbook_path, str):
            errors.append(f"{workbook_key}: chemin de classeur absent.")
            continue
        if not os.path.isfile(workbook_path):
            errors.append(f"{workbook_key}: classeur introuvable ({workbook_path}).")
            continue
        open_error = _probe_excel_workbook_open_error(workbook_path)
        if open_error:
            errors.append(f"{workbook_key}: ouverture COM impossible ({open_error}).")

    if errors:
        raise ExcelChartPreparationError(
            "Préflight COM des classeurs Excel échoué :\n - " + "\n - ".join(errors)
        )


def export(
    html_path: str,
    out_suffix: str = "",
    excel_chart_mode: str = "embedded",
    annexe_b_chart_mode: str | None = None,
):
    requested_raw_mode = annexe_b_chart_mode if annexe_b_chart_mode is not None else excel_chart_mode
    requested_mode = _normalize_excel_chart_mode(requested_raw_mode)
    effective_mode, mode_reason = _resolve_excel_chart_mode(requested_mode)

    basename = os.path.splitext(os.path.basename(html_path))[0]
    docx_out_final = os.path.join(OUTPUT_DIR, basename + out_suffix + ".docx")

    print("Source  : {}".format(os.path.basename(html_path)))
    print("Sortie  : {}".format(os.path.basename(docx_out_final)))
    print("Graphiques Excel B/C : {} ({})".format(effective_mode, mode_reason))

    # Lire le HTML source
    with open(html_path, "r", encoding="utf-8") as f:
        source_html = f.read()

    attempt_modes = [effective_mode]
    if requested_mode == "auto" and effective_mode != "png":
        attempt_modes.append("png")

    generate_reference_docx()

    lock_path = _acquire_docx_lock(docx_out_final)
    try:
        for attempt_index, attempt_mode in enumerate(attempt_modes, start=1):
            use_excel_pipeline = attempt_mode in {"linked", "embedded"}
            if len(attempt_modes) > 1:
                print(
                    "  [EXCEL-CHARTS] Tentative {} / {} en mode '{}'.".format(
                        attempt_index, len(attempt_modes), attempt_mode
                    )
                )

            tmp_html = _build_temp_artifact_path("tmp_export_word_html", ".html")
            docx_out_work = _build_temp_artifact_path(
                f"tmp_export_word_docx_{basename}",
                ".docx",
            )

            try:
                try:
                    corrected_html = apply_corrections(source_html, excel_chart_mode=attempt_mode)
                    if use_excel_pipeline:
                        manifest = _EXCEL_CHART_LINK_STATE.get("manifest")
                        if isinstance(manifest, dict):
                            _ensure_excel_workbooks_com_compatible(manifest)
                except ExcelChartPreparationError as exc:
                    if requested_mode == "auto" and attempt_mode != "png":
                        print(
                            "  [EXCEL-CHARTS] Préparation Excel impossible en mode auto "
                            f"({exc}). Bascule PNG."
                        )
                        continue
                    raise

                with open(tmp_html, "w", encoding="utf-8") as f:
                    f.write(corrected_html)

                cmd = [
                    PANDOC,
                    tmp_html,
                    "--from",
                    "html",
                    "--to",
                    "docx",
                    "--reference-doc",
                    REF_DOCX,
                    "--output",
                    docx_out_work,
                    "--lua-filter",
                    LUA_FILTER,
                    "--lua-filter",
                    LUA_FOOTNOTES,
                    "--lua-filter",
                    LUA_STYLES,
                    "--wrap=none",
                    "--metadata",
                    "title=Deuxieme Bulletin statistique de la protection sociale en RDC",
                ]
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode != 0 or not os.path.exists(docx_out_work):
                    details = (res.stderr or res.stdout or "Erreur pandoc non détaillée.").strip()
                    _safe_unlink(docx_out_work)
                    print("ECHEC :\n" + details)
                    sys.exit(1)

                if res.stderr:
                    warnings = [l for l in res.stderr.splitlines() if "WARNING" in l]
                    if warnings:
                        print("Avertissements ({}) :".format(len(warnings)))
                        for w in warnings[:5]:
                            print("  " + w)

                insert_page_breaks(docx_out_work)
                insert_tof_fields(docx_out_work)
                set_tables_autofit(docx_out_work)

                if use_excel_pipeline:
                    try:
                        _insert_excel_charts(docx_out_work, paste_mode=attempt_mode)
                    except Exception as exc:
                        _safe_unlink(docx_out_work)
                        if requested_mode == "auto" and attempt_mode != "png":
                            print(
                                "  [EXCEL-CHARTS] Insertion Excel impossible en mode auto "
                                f"({exc}). Bascule PNG."
                            )
                            continue
                        raise
                else:
                    print("  [EXCEL-CHARTS] Mode PNG : conservation des images annexe B/C.")

                os.replace(docx_out_work, docx_out_final)
                size = os.path.getsize(docx_out_final) // 1024
                print("Succès : {} ({} KB)".format(os.path.basename(docx_out_final), size))
                return
            finally:
                _safe_unlink(tmp_html)
                _safe_unlink(docx_out_work)
    finally:
        _release_docx_lock(lock_path)

    raise RuntimeError("Échec de l'export Word : aucune tentative n'a abouti.")

# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exporte un HTML bulletin en DOCX (pandoc + post-traitements Word).",
    )
    parser.add_argument(
        "html_file",
        nargs="?",
        help="Chemin du fichier HTML source (défaut : dernier bulletin_relecture_*.html).",
    )
    parser.add_argument(
        "--excel-charts",
        "--annexe-b-charts",
        dest="excel_charts",
        choices=sorted(EXCEL_CHART_MODES),
        default=os.environ.get("EXCEL_CHART_MODE") or os.environ.get("ANNEXE_B_CHART_MODE", "embedded"),
        help=(
            "Mode de remplacement des PNG annexe B/C : "
            "linked (objets Excel liés), embedded (objets Excel incorporés), "
            "png (conserver les PNG), auto (embedded si COM disponible, sinon PNG). "
            "Alias historique accepté : --annexe-b-charts."
        ),
    )
    return parser


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()
    html_file = args.html_file or find_latest_html()
    export(html_file, excel_chart_mode=args.excel_charts)
