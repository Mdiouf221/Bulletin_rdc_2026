import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import plotly.graph_objects as go
from openpyxl import Workbook

import exporter
import exporter_word
import generer_annexe_b_visuels as annexe_b

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent
OUTPUT_DIR = WORKSPACE / "10_output"


class AnnexeBExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = OUTPUT_DIR / "test_exporter_word_excel"
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def _build_payload(self, chart_key: str, chart_type: str) -> dict:
        return {
            "institution": "CNSS",
            "chart_key": chart_key,
            "titre": "Titre test",
            "unite": "Unité test",
            "source": "Source test",
            "periode": "2019–2025",
            "type": chart_type,
            "notes": "",
            "regles": [],
            "columns": ["Année", "Série A", "Série B"],
            "rows": [
                [2019, 10, 5],
                [2020, 12, 8],
                [2021, 11, 9],
            ],
        }

    def test_annexe_scope_requires_both_auto_generated_markers(self):
        complete = "<!-- AUTO_GENERE:CNSS:DEBUT -->contenu<!-- AUTO_GENERE:CNSS:FIN -->"
        incomplete = "<!-- AUTO_GENERE:CNSS:DEBUT -->contenu"
        self.assertTrue(annexe_b.has_auto_generated_block(complete, "CNSS"))
        self.assertFalse(annexe_b.has_auto_generated_block(incomplete, "CNSS"))
        self.assertFalse(annexe_b.has_auto_generated_block(complete, "MEPST"))

    def test_figure_to_tabular_data_aligns_years(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(name="Série A", x=[2020, 2022], y=[10, 30]))
        columns, rows, years = annexe_b._figure_to_tabular_data(fig, [2019, 2020, 2021])
        self.assertEqual(columns, ["Année", "Série A"])
        self.assertEqual(years, [2019, 2020, 2021, 2022])
        self.assertEqual(rows[0], [2019, None])
        self.assertEqual(rows[-1], [2022, 30])

    def test_resolve_metadata_uses_questionnaire_and_q4_sources(self):
        settings = {
            "Q4": {"CNSS_R1": "menage"},
            "Q4_coefficients": {
                "CNSS_R1": {"2020": {"value": 3.17, "source": "UN HH Size 2019"}}
            },
            "graph_metadata": {
                "beneficiaires": {
                    "titre": "Titre personnalisé",
                    "source": "Source spécifique",
                }
            },
        }
        meta = annexe_b._resolve_chart_metadata(
            institution="CNSS",
            chart_key="beneficiaires",
            default_title="Titre défaut",
            settings=settings,
            years=[2019, 2020],
        )
        self.assertEqual(meta["titre"], "Titre personnalisé")
        self.assertEqual(meta["source"], "Source spécifique")
        self.assertIn("Q4", meta["regles"])
        self.assertIn("UN HH Size 2019", meta["notes"])

    def test_build_annexe_b_chart_sources_supports_multi_chart_sheet(self):
        word_data = {
            "charts": {
                "annexe_B_CNSS_sexe.png": {
                    "sheet_name": "CNSS_sexe",
                    "chart_key": "sexe",
                }
            }
        }
        with patch.object(exporter_word, "_load_workbook_chart_counts", return_value={"CNSS_sexe": 2}):
            sources = exporter_word._build_annexe_b_chart_sources(word_data, r"C:\fake\annexe_b.xlsx")

        self.assertIn("annexe_b_cnss_sexe.png", sources)
        self.assertEqual([item["chart_index"] for item in sources["annexe_b_cnss_sexe.png"]], [1, 2])

    def test_build_annexe_b_chart_sources_honors_chart_index_overrides(self):
        word_data = {
            "charts": {
                "annexe_B_CNSS_sexe.png": {
                    "sheet_name": "CNSS_sexe",
                    "chart_indices": [2, 1],
                },
                "annexe_B_CNSS_recettes.png": {
                    "sheet_name": "CNSS_recettes",
                    "chart_index": 1,
                },
            }
        }
        with patch.object(
            exporter_word,
            "_load_workbook_chart_counts",
            return_value={"CNSS_sexe": 2, "CNSS_recettes": 1},
        ):
            sources = exporter_word._build_annexe_b_chart_sources(word_data, r"C:\fake\annexe_b.xlsx")

        self.assertEqual(
            [item["chart_index"] for item in sources["annexe_b_cnss_sexe.png"]],
            [2, 1],
        )
        self.assertEqual(
            [item["chart_index"] for item in sources["annexe_b_cnss_recettes.png"]],
            [1],
        )

    def test_build_annexe_c_chart_sources_maps_indicator_and_numerator_indices(self):
        with patch.object(
            exporter_word,
            "_load_annexe_c_sheet_map",
            return_value={
                "global_131": {"sheet_name": "C1_global_131", "chart_count": 2},
                "ind_26_chomage": {"sheet_name": "C6_ind_26_chomage", "chart_count": 0},
            },
        ):
            sources, sheet_map = exporter_word._build_annexe_c_chart_sources(r"C:\fake\annexe_c.xlsx")

        self.assertIn("global_131", sheet_map)
        self.assertEqual(
            sources["annexe_c_global_131_indicateur.png"][0]["chart_index"],
            1,
        )
        self.assertEqual(
            sources["annexe_c_global_131_numerateur.png"][0]["chart_index"],
            2,
        )
        self.assertNotIn("annexe_c_ind_26_chomage_indicateur.png", sources)

    def test_replace_excel_images_with_markers_injects_annexe_b_and_c(self):
        html = (
            '<html><body>'
            '<img src="/files/04_annexes/illustrations/annexe_B_CNSS_sexe.png">'
            '<img src="/files/04_annexes/illustrations/annexe_C_global_131_indicateur.png">'
            '<img src="/files/04_annexes/illustrations/annexe_C_global_131_numerateur.png">'
            "</body></html>"
        )

        annexe_b_sources = {
            "annexe_b_cnss_sexe.png": [
                {"workbook_key": "annexe_b", "sheet_name": "CNSS_sexe", "chart_index": 1, "image_filename": "annexe_B_CNSS_sexe.png"},
                {"workbook_key": "annexe_b", "sheet_name": "CNSS_sexe", "chart_index": 2, "image_filename": "annexe_B_CNSS_sexe.png"},
            ]
        }
        annexe_c_sources = {
            "annexe_c_global_131_indicateur.png": [
                {"workbook_key": "annexe_c", "sheet_name": "C1_global_131", "chart_index": 1, "image_filename": "annexe_C_global_131_indicateur.png"},
            ],
            "annexe_c_global_131_numerateur.png": [
                {"workbook_key": "annexe_c", "sheet_name": "C1_global_131", "chart_index": 2, "image_filename": "annexe_C_global_131_numerateur.png"},
            ],
        }

        with patch.object(exporter_word, "_load_annexe_b_word_data", return_value={"charts": {"dummy": {}}}):
            with patch.object(exporter_word, "_resolve_annexe_b_workbook_path", return_value=r"C:\fake\annexe_b.xlsx"):
                with patch.object(exporter_word, "_build_annexe_b_chart_sources", return_value=annexe_b_sources):
                    with patch.object(exporter_word, "_resolve_annexe_c_workbook_path", return_value=r"C:\fake\annexe_c.xlsx"):
                        with patch.object(exporter_word, "_build_annexe_c_chart_sources", return_value=(annexe_c_sources, {"global_131": {"sheet_name": "C1_global_131", "chart_count": 2}})):
                            with patch.object(exporter_word.os.path, "isfile", side_effect=lambda p: p in {r"C:\fake\annexe_b.xlsx", r"C:\fake\annexe_c.xlsx"}):
                                updated, manifest = exporter_word._replace_excel_images_with_markers(html)

        self.assertIn("[[EXCEL_CHART:0001]]<br/>[[EXCEL_CHART:0002]]", updated)
        self.assertIn("[[EXCEL_CHART:0003]]", updated)
        self.assertIn("[[EXCEL_CHART:0004]]", updated)
        self.assertEqual(manifest["workbooks"]["annexe_b"], r"C:\fake\annexe_b.xlsx")
        self.assertEqual(manifest["workbooks"]["annexe_c"], r"C:\fake\annexe_c.xlsx")
        self.assertEqual(len(manifest["charts"]), 4)
        self.assertEqual(
            [entry["chart_index"] for entry in manifest["charts"]],
            [1, 2, 1, 2],
        )

    def test_append_chart_sheet_applies_uniform_excel_styles(self):
        wb = Workbook()
        ws_bar = wb.active
        annexe_b._append_chart_sheet(ws_bar, self._build_payload("depenses", "barres"))
        bar_chart = ws_bar._charts[0]
        self.assertEqual(bar_chart.style, annexe_b.EXCEL_CHART_STYLE_ID)
        self.assertEqual(bar_chart.x_axis.tickLblSkip, 1)
        self.assertEqual(bar_chart.x_axis.numFmt.formatCode, "0")
        self.assertIsNotNone(bar_chart.dataLabels)
        self.assertTrue(bar_chart.dataLabels.showVal)
        self.assertEqual(bar_chart.dataLabels.position, "outEnd")

        ws_line = wb.create_sheet("line")
        annexe_b._append_chart_sheet(ws_line, self._build_payload("cotisants", "courbe"))
        line_chart = ws_line._charts[0]
        self.assertEqual(line_chart.style, annexe_b.EXCEL_CHART_STYLE_ID)
        self.assertFalse(line_chart.smooth)
        self.assertEqual(line_chart.x_axis.tickLblSkip, 1)
        self.assertTrue(all(series.smooth is False for series in line_chart.series))

        ws_sex = wb.create_sheet("sexe")
        payload_sex = self._build_payload("sexe", "colonnes empilées (100%)")
        payload_sex["columns"] = [
            "Année",
            "Cotisants - Hommes",
            "Cotisants - Femmes",
            "Cotisants - Non identifié",
            "Bénéficiaires - Hommes",
            "Bénéficiaires - Femmes",
            "Bénéficiaires - Non identifié",
        ]
        payload_sex["rows"] = [
            [2019, 100, 80, 20, 60, 70, 10],
            [2020, 110, 90, 10, 65, 75, 10],
        ]
        annexe_b._append_chart_sheet(ws_sex, payload_sex)
        self.assertEqual(len(ws_sex._charts), 2)
        for chart in ws_sex._charts:
            self.assertEqual(chart.style, annexe_b.EXCEL_CHART_STYLE_ID)
            self.assertEqual(chart.x_axis.tickLblSkip, 1)
            self.assertTrue(chart.dataLabels.showVal)
            self.assertEqual(chart.dataLabels.position, "ctr")

    def test_resolve_excel_chart_mode_auto_fallback(self):
        mode, reason = exporter_word._resolve_excel_chart_mode(
            "auto",
            com_probe=lambda: False,
        )
        self.assertEqual(mode, "png")
        self.assertIn("COM Word/Excel indisponible", reason)

    def test_resolve_excel_chart_mode_auto_prefers_embedded(self):
        mode, reason = exporter_word._resolve_excel_chart_mode(
            "auto",
            com_probe=lambda: True,
        )
        self.assertEqual(mode, "embedded")
        self.assertIn("incorporee", reason)

    def test_apply_corrections_keeps_png_when_mode_png(self):
        html = '<html><body><img src="/files/04_annexes/illustrations/annexe_B_CNSS_cotisants.png"></body></html>'
        updated = exporter_word.apply_corrections(html, excel_chart_mode="png")
        self.assertIn(".png", updated)
        self.assertNotIn("[[EXCEL_CHART:", updated)

    def test_apply_corrections_embedded_raises_when_assets_missing(self):
        html = '<html><body><img src="/files/04_annexes/illustrations/annexe_B_CNSS_cotisants.png"></body></html>'
        with patch.object(
            exporter_word,
            "_replace_excel_images_with_markers",
            side_effect=exporter_word.ExcelChartPreparationError("assets manquants"),
        ):
            with self.assertRaises(exporter_word.ExcelChartPreparationError):
                exporter_word.apply_corrections(html, excel_chart_mode="embedded")

    def test_export_auto_falls_back_to_png_when_prepare_fails(self):
        html_path = self.tmp_dir / "bulletin_relecture_test.html"
        html_path.write_text("<html><body>TEST</body></html>", encoding="utf-8")
        out_suffix = "__unit"
        output_docx = OUTPUT_DIR / f"{html_path.stem}{out_suffix}.docx"
        if output_docx.exists():
            output_docx.unlink()

        seen_modes: list[str] = []

        def fake_apply_corrections(html: str, *, excel_chart_mode: str = "auto", annexe_b_chart_mode: str | None = None) -> str:
            mode = annexe_b_chart_mode if annexe_b_chart_mode is not None else excel_chart_mode
            seen_modes.append(mode)
            if mode == "embedded":
                raise exporter_word.ExcelChartPreparationError("actifs indisponibles")
            return html

        def fake_subprocess_run(cmd, **kwargs):  # noqa: ANN001
            if isinstance(cmd, list) and "--output" in cmd:
                out_path = Path(cmd[cmd.index("--output") + 1])
                out_path.write_bytes(b"DOCX")
            return SimpleNamespace(returncode=0, stderr="", stdout="")

        with patch.object(exporter_word, "_resolve_excel_chart_mode", side_effect=lambda mode: ("embedded", "auto->embedded") if mode == "auto" else ("png", "png")):
            with patch.object(exporter_word, "apply_corrections", side_effect=fake_apply_corrections):
                with patch.object(exporter_word, "generate_reference_docx", return_value=None):
                    with patch.object(exporter_word, "insert_page_breaks", return_value=None):
                        with patch.object(exporter_word, "insert_tof_fields", return_value=None):
                            with patch.object(exporter_word, "set_tables_autofit", return_value=None):
                                with patch.object(exporter_word.subprocess, "run", side_effect=fake_subprocess_run):
                                    exporter_word.export(str(html_path), out_suffix=out_suffix, excel_chart_mode="auto")

        self.assertEqual(seen_modes, ["embedded", "png"])
        self.assertTrue(output_docx.exists())
        self.assertFalse(Path(exporter_word._docx_lock_path(str(output_docx))).exists())
        output_docx.unlink()

    def test_cli_accepts_excel_charts_alias(self):
        with patch.dict(exporter_word.os.environ, {}, clear=True):
            parser = exporter_word.build_arg_parser()
            args_default = parser.parse_args([])
            args_alias = parser.parse_args(["--annexe-b-charts", "linked"])
            args_new = parser.parse_args(["--excel-charts", "embedded"])
        self.assertEqual(args_default.excel_charts, "embedded")
        self.assertEqual(args_alias.excel_charts, "linked")
        self.assertEqual(args_new.excel_charts, "embedded")

    def test_temp_artifact_paths_are_unique(self):
        path1 = exporter_word._build_temp_artifact_path("tmp_export_word_html", ".html")
        path2 = exporter_word._build_temp_artifact_path("tmp_export_word_html", ".html")
        self.assertNotEqual(path1, path2)
        self.assertFalse(Path(path1).exists())
        self.assertFalse(Path(path2).exists())

    def test_docx_lock_prevents_parallel_target_export(self):
        docx_path = self.tmp_dir / "lock_target.docx"
        docx_path.write_bytes(b"DOCX")

        lock_path = exporter_word._acquire_docx_lock(str(docx_path))
        try:
            with self.assertRaises(RuntimeError):
                exporter_word._acquire_docx_lock(str(docx_path))
        finally:
            exporter_word._release_docx_lock(lock_path)
        self.assertFalse(Path(lock_path).exists())

    def test_export_fails_fast_when_target_is_locked(self):
        html_path = self.tmp_dir / "bulletin_relecture_locked.html"
        html_path.write_text("<html><body>LOCKED</body></html>", encoding="utf-8")
        out_suffix = "__locked"
        output_docx = OUTPUT_DIR / f"{html_path.stem}{out_suffix}.docx"
        lock_path = exporter_word._acquire_docx_lock(str(output_docx))
        try:
            with self.assertRaises(RuntimeError):
                exporter_word.export(
                    str(html_path),
                    out_suffix=out_suffix,
                    excel_chart_mode="png",
                )
        finally:
            exporter_word._release_docx_lock(lock_path)

    def test_export_missing_html_does_not_leave_target_lock(self):
        missing_html = exporter_word.os.path.join(
            exporter_word.OUTPUT_DIR,
            "__missing_export_source__.html",
        )
        target = exporter_word.os.path.join(
            exporter_word.OUTPUT_DIR,
            "__missing_export_source__.docx",
        )
        lock_path = exporter_word._docx_lock_path(target)
        exporter_word._safe_unlink(lock_path)

        with self.assertRaises(FileNotFoundError):
            exporter_word.export(missing_html, excel_chart_mode="png")

        self.assertFalse(exporter_word.os.path.exists(lock_path))

    def test_helper_script_resets_cutcopymode_without_copy_wait_gate(self):
        helper_script = (SCRIPT_DIR / "lier_graphiques_annexe_b.ps1").read_text(encoding="utf-8")
        self.assertIn("$excel.CutCopyMode = 0", helper_script)
        self.assertNotIn("Wait-ExcelCopyReady", helper_script)


class ExporterRunAssemblerTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = OUTPUT_DIR / "test_exporter_run_assembler"
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_run_assembler_does_not_refresh_visuals_by_default(self):
        assembler_script = self.tmp_dir / "assembler_markdown.py"
        assembler_script.write_text("print('ok')", encoding="utf-8")
        calls: list[list[str]] = []

        def fake_run(cmd, capture_output=True, cwd=None, encoding=None, errors=None):  # noqa: ANN001
            calls.append(cmd)
            return SimpleNamespace(returncode=0, stderr="", stdout="")

        with patch.object(exporter, "ASSEMBLER", assembler_script):
            with patch.object(exporter.subprocess, "run", side_effect=fake_run):
                ok = exporter.run_assembler()

        self.assertTrue(ok)
        self.assertEqual(len(calls), 1)
        self.assertEqual(Path(calls[0][1]).name, "assembler_markdown.py")

    def test_run_assembler_refresh_visuals_opt_in(self):
        script_b = self.tmp_dir / "generer_annexe_b_visuels.py"
        script_c = self.tmp_dir / "generer_annexe_c_visuels.py"
        assembler_script = self.tmp_dir / "assembler_markdown.py"
        for script in (script_b, script_c, assembler_script):
            script.write_text("print('ok')", encoding="utf-8")

        calls: list[list[str]] = []

        def fake_run(cmd, capture_output=True, cwd=None, encoding=None, errors=None):  # noqa: ANN001
            calls.append(cmd)
            return SimpleNamespace(returncode=0, stderr="", stdout="")

        with patch.object(exporter, "ANNEXE_B_VISUELS", script_b):
            with patch.object(exporter, "ANNEXE_C_VISUELS", script_c):
                with patch.object(exporter, "ASSEMBLER", assembler_script):
                    with patch.object(exporter.subprocess, "run", side_effect=fake_run):
                        ok = exporter.run_assembler(refresh_visuals=True)

        self.assertTrue(ok)
        self.assertEqual(len(calls), 3)
        self.assertEqual(Path(calls[0][1]).name, "generer_annexe_b_visuels.py")
        self.assertEqual(Path(calls[1][1]).name, "generer_annexe_c_visuels.py")
        self.assertEqual(Path(calls[2][1]).name, "assembler_markdown.py")

    def test_export_word_annexe_b_mode_alias_overrides_excel_mode(self):
        stamp = "2099-01-01"
        html_source = self.tmp_dir / f"bulletin_relecture_{stamp}.html"
        html_source.write_text("<html><body>test</body></html>", encoding="utf-8")
        output_docx = self.tmp_dir / f"bulletin_relecture_{stamp}.docx"
        commands: list[list[str]] = []

        def fake_run(cmd, capture_output=True, cwd=None, encoding=None, errors=None):  # noqa: ANN001
            commands.append(cmd)
            output_docx.write_bytes(b"DOCX")
            return SimpleNamespace(returncode=0, stderr="", stdout="")

        with patch.object(exporter, "OUTPUT_DIR", self.tmp_dir):
            with patch.object(exporter, "STAMP", stamp):
                with patch.object(exporter.subprocess, "run", side_effect=fake_run):
                    result = exporter.export_word(
                        include_notes=False,
                        excel_chart_mode="png",
                        annexe_b_chart_mode="linked",
                        reuse_html=True,
                    )

        self.assertIsNotNone(result)
        self.assertEqual(len(commands), 1)
        self.assertIn("--excel-charts", commands[0])
        mode_index = commands[0].index("--excel-charts") + 1
        self.assertEqual(commands[0][mode_index], "linked")

    def test_export_word_regenerates_html_by_default(self):
        stamp = "2099-01-01"
        html_source = self.tmp_dir / f"bulletin_relecture_{stamp}.html"
        output_docx = self.tmp_dir / f"bulletin_relecture_{stamp}.docx"
        commands: list[list[str]] = []

        def fake_run(cmd, capture_output=True, cwd=None, encoding=None, errors=None):  # noqa: ANN001
            commands.append(cmd)
            output_docx.write_bytes(b"DOCX")
            return SimpleNamespace(returncode=0, stderr="", stdout="")

        with patch.object(exporter, "OUTPUT_DIR", self.tmp_dir):
            with patch.object(exporter, "STAMP", stamp):
                with patch.object(
                    exporter,
                    "export_html",
                    return_value=html_source,
                ) as export_html:
                    with patch.object(exporter.subprocess, "run", side_effect=fake_run):
                        result = exporter.export_word(
                            include_notes=False,
                            excel_chart_mode="png",
                        )

        self.assertEqual(result, output_docx)
        export_html.assert_called_once_with(
            include_notes=False,
            open_after=False,
            refresh_visuals=False,
        )
        self.assertEqual(len(commands), 1)

    def test_export_word_reuse_html_requires_existing_file(self):
        stamp = "2099-01-01"
        with patch.object(exporter, "OUTPUT_DIR", self.tmp_dir):
            with patch.object(exporter, "STAMP", stamp):
                with patch.object(exporter, "export_html") as export_html:
                    result = exporter.export_word(reuse_html=True)

        self.assertIsNone(result)
        export_html.assert_not_called()



if __name__ == "__main__":
    unittest.main()
