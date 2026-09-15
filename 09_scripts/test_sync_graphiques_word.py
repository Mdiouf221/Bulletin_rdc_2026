import os
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook, load_workbook
from openpyxl.chart import LineChart, Reference

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import sync_graphiques_word as sync_word


class SyncGraphiquesWordTests(unittest.TestCase):
    def setUp(self):
        self.workspace = SCRIPT_DIR.parent
        self.tmp_dir = self.workspace / "10_output" / "test_sync_graphiques_word"
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def _build_annexe_b_model_workbook(self, path: Path):
        wb = Workbook()
        index = wb.active
        index.title = "index"
        index["A1"] = "institution"
        index["B1"] = "chart_key"
        index["C1"] = "sheet_name"
        index["A2"] = "CNSS"
        index["B2"] = "cotisants"
        index["C2"] = "CNSS_cotisants"

        ws = wb.create_sheet("CNSS_cotisants")
        ws["A1"] = "Institution"
        ws["B1"] = "CNSS"
        ws["A2"] = "Graphique"
        ws["B2"] = "cotisants"
        ws["A11"] = "Année"
        ws["B11"] = "Série A"
        ws["C11"] = "Série B"
        ws["A12"] = 2019
        ws["B12"] = 10
        ws["C12"] = 4
        ws["A13"] = 2020
        ws["B13"] = 11
        ws["C13"] = 5

        chart = LineChart()
        data = Reference(ws, min_col=2, max_col=3, min_row=11, max_row=13)
        cats = Reference(ws, min_col=1, min_row=12, max_row=13)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        ws.add_chart(chart, "A15")
        wb.save(path)

    def test_discovery_excludes_generated_and_temp_files(self):
        a = self.tmp_dir / "annexe_A_graphiques.xlsx"
        b = self.tmp_dir / "annexe_B_graphiques.xlsx"
        c = self.tmp_dir / f"annexe_B_graphiques{sync_word.COPY_MARKER}_20260101_120000.xlsx"
        d = self.tmp_dir / f"annexe_B_graphiques{sync_word.TEMP_DATA_MARKER}_20260101_120000.xlsx"
        for file in (a, b, c, d):
            file.write_bytes(b"x")
        os.utime(a, (1_700_000_000, 1_700_000_000))
        os.utime(b, (1_700_000_100, 1_700_000_100))
        os.utime(c, (1_700_000_200, 1_700_000_200))
        os.utime(d, (1_700_000_300, 1_700_000_300))

        discovered = sync_word.discover_graph_workbooks(self.tmp_dir)
        self.assertEqual([p.name for p in discovered], [a.name, b.name])
        selected = sync_word.choose_latest_workbook(discovered, {a.name.lower(), b.name.lower()})
        self.assertEqual(selected.name, b.name)

    def test_annexe_b_plan_counts_changed_and_preserves_chart(self):
        workbook_path = self.tmp_dir / "annexe_B_graphiques_par_institution.xlsx"
        self._build_annexe_b_model_workbook(workbook_path)
        source_payloads = {
            "CNSS::cotisants": {
                "institution": "CNSS",
                "chart_key": "cotisants",
                "columns": ["Année", "Série A", "Série B"],
                "rows": [
                    [2019, 99, 4],  # valeur modifiée
                    [2020, 11, 5],  # inchangé
                ],
            }
        }

        with patch.object(sync_word, "_derive_annexe_b_source_payloads", return_value=source_payloads):
            plan, summary = sync_word.build_annexe_b_update_plan(workbook_path)

        self.assertEqual(summary["mode"], "annexe_b_db_questionnaire")
        self.assertEqual(summary["sheet_count"], 1)
        self.assertEqual(summary["cells_examined"], 4)
        self.assertEqual(summary["cells_changed"], 1)
        self.assertEqual(summary["cells_unchanged"], 3)
        self.assertEqual(summary["workbook_chart_count"], 1)

        copy_path = self.tmp_dir / "annexe_B_copy.xlsx"
        shutil.copy2(workbook_path, copy_path)
        sync_word.apply_plan_with_openpyxl(copy_path, plan)

        wb = load_workbook(copy_path, data_only=True)
        ws = wb["CNSS_cotisants"]
        self.assertEqual(ws["B12"].value, 99)
        self.assertEqual(ws["C12"].value, 4)
        self.assertEqual(len(ws._charts), 1)
        wb.close()

    def test_annexe_b_plan_raises_if_source_year_missing_in_model(self):
        workbook_path = self.tmp_dir / "annexe_B_graphiques_par_institution.xlsx"
        self._build_annexe_b_model_workbook(workbook_path)
        source_payloads = {
            "CNSS::cotisants": {
                "institution": "CNSS",
                "chart_key": "cotisants",
                "columns": ["Année", "Série A", "Série B"],
                "rows": [
                    [2021, 12, 6],
                ],
            }
        }
        with patch.object(sync_word, "_derive_annexe_b_source_payloads", return_value=source_payloads):
            with self.assertRaises(ValueError):
                sync_word.build_annexe_b_update_plan(workbook_path)


if __name__ == "__main__":
    unittest.main()
