import sys
import unittest
from pathlib import Path

from openpyxl import load_workbook

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import generer_annexe_c_classeur as annexe_c


class AnnexeCWorkbookTests(unittest.TestCase):
    def setUp(self):
        self.workspace = SCRIPT_DIR.parent
        self.output_path = self.workspace / "10_output" / "annexe_C_graphiques_par_indicateur_test.xlsx"
        if self.output_path.exists():
            self.output_path.unlink()

    def tearDown(self):
        if self.output_path.exists():
            self.output_path.unlink()

    def _find_annual_header_row(self, ws) -> int:
        for row in range(1, 80):
            values = [ws.cell(row=row, column=col).value for col in range(1, 5)]
            if values == ["Année", "Indicateur (%)", "Numérateur", "Dénominateur"]:
                return row
        raise AssertionError(f"Entête annuel introuvable dans la feuille {ws.title}")

    def test_generate_annexe_c_workbook(self):
        summary = annexe_c.generate_annexe_c_workbook(self.output_path)
        self.assertTrue(self.output_path.exists())

        wb = load_workbook(self.output_path)
        self.assertEqual(len(wb.sheetnames), 10)  # index + 9 indicateurs
        self.assertIn("index", wb.sheetnames)

        total_charts = sum(len(ws._charts) for ws in wb.worksheets)
        self.assertEqual(total_charts, 14)

        years = summary["years"]
        self.assertEqual(years, list(range(2019, 2027)))

        non_calculables = {"ind_26_chomage", "ind_28_vulnerables"}
        for entry in summary["entries"]:
            ws = wb[entry["sheet_name"]]
            header_row = self._find_annual_header_row(ws)
            row_start = header_row + 1
            row_end = row_start + len(years) - 1

            read_years = [ws.cell(row=row, column=1).value for row in range(row_start, row_end + 1)]
            self.assertEqual(read_years, years)

            if entry["indicator_key"] in non_calculables:
                self.assertEqual(len(ws._charts), 0)
                for row in range(row_start, row_end + 1):
                    self.assertIsNone(ws.cell(row=row, column=2).value)
                    self.assertIsNone(ws.cell(row=row, column=3).value)
                    self.assertIsNone(ws.cell(row=row, column=4).value)
                continue

            self.assertEqual(len(ws._charts), 2)
            indicator_values = [ws.cell(row=row, column=2).value for row in range(row_start, row_end + 1)]
            numerator_values = [ws.cell(row=row, column=3).value for row in range(row_start, row_end + 1)]
            denominator_values = [ws.cell(row=row, column=4).value for row in range(row_start, row_end + 1)]

            self.assertTrue(any(isinstance(value, (int, float)) for value in indicator_values))
            self.assertTrue(any(isinstance(value, (int, float)) for value in numerator_values))
            self.assertTrue(any(isinstance(value, (int, float)) for value in denominator_values))


if __name__ == "__main__":
    unittest.main()
