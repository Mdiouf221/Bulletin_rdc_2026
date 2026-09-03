import unittest

import plotly.graph_objects as go

import generer_annexe_b_visuels as annexe_b
import exporter_word


class AnnexeBExportTests(unittest.TestCase):
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

    def test_word_injection_replaces_annexe_b_png_with_link_marker(self):
        html = '<html><body><img src="C:/repo/04_annexes/illustrations/annexe_B_CNSS_cotisants.png"></body></html>'
        word_data = {
            "xlsx": "10_output/annexe_B_graphiques_par_institution.xlsx",
            "charts": {
                "annexe_B_CNSS_cotisants.png": {
                    "sheet_name": "CNSS_cotisants",
                    "titre": "CNSS — Cotisants",
                    "source": "Base ESS",
                    "periode": "2019–2025",
                    "notes": "Q1 appliquée",
                    "columns": ["Année", "Branche A"],
                    "rows": [[2019, 100], [2020, 120]],
                }
            },
        }
        updated = exporter_word._inject_annexe_b_link_markers(html, word_data)
        self.assertEqual(updated, "<html><body>[[ANNEXE_B_CHART:CNSS_cotisants]]</body></html>")
        self.assertNotIn(".png", updated)
        self.assertNotIn("<table", updated)


if __name__ == "__main__":
    unittest.main()
