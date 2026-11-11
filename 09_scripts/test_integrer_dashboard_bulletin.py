import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from integrer_dashboard_bulletin import compute_numerator, get_denominator_value
from generer_annexe_c_visuels import _format_component_row
from visualiser_regimes import build_indicateurs_payload


class NumeratorDeduplicationTests(unittest.TestCase):
    def test_global_uses_q1_group_maximum_for_all_years(self):
        odd_nodes = [
            {"id": "institution::TEST", "type": "institution_ess"},
            {"id": "regime::TEST::R1", "type": "regime_ess", "parent_id": "institution::TEST"},
            {"id": "regime::TEST::R2", "type": "regime_ess", "parent_id": "institution::TEST"},
            {"id": "regime::TEST::R3", "type": "regime_ess", "parent_id": "institution::TEST"},
        ]
        regime_rows = [
            {"annee": 2020, "programme_id": "regime::TEST::R1", "institution": "TEST", "regime_code": "R1", "cotisants": 90},
            {"annee": 2020, "programme_id": "regime::TEST::R2", "institution": "TEST", "regime_code": "R2", "cotisants": 100},
            {"annee": 2020, "programme_id": "regime::TEST::R3", "institution": "TEST", "regime_code": "R3", "cotisants": 30},
            {"annee": 2021, "programme_id": "regime::TEST::R1", "institution": "TEST", "regime_code": "R1", "cotisants": 110},
            {"annee": 2021, "programme_id": "regime::TEST::R2", "institution": "TEST", "regime_code": "R2", "cotisants": 100},
            {"annee": 2021, "programme_id": "regime::TEST::R3", "institution": "TEST", "regime_code": "R3", "cotisants": 40},
        ]
        questionnaire_data = {
            "TEST": {
                "Q1": {
                    "R1__R2": "true",
                    "R2__R1": "true",
                    "R1__R3": "false",
                }
            }
        }
        decisions = {"institution::TEST::global_131": "entierement_inclus"}

        for year, expected in ((2020, 130), (2021, 150)):
            self.assertEqual(
                compute_numerator(
                    "global_131",
                    year,
                    regime_rows,
                    [],
                    odd_nodes,
                    decisions,
                    questionnaire_data,
                ),
                expected,
            )


class NumeratorAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.odd_nodes = [
            {"id": "institution::TEST", "type": "institution_ess"},
            {"id": "regime::TEST::R1", "type": "regime_ess", "parent_id": "institution::TEST"},
        ]
        self.decisions = {"institution::TEST::ind_24_handicap": "entierement_inclus"}

    def test_explicit_zero_is_preserved_as_observed_value(self):
        prestations = [
            {
                "annee": 2019,
                "programme_id": "prestation::TEST::R1::P1",
                "institution": "TEST",
                "regime_code": "R1",
                "beneficiaires": 0,
            }
        ]
        self.odd_nodes.append(
            {
                "id": "prestation::TEST::R1::P1",
                "type": "prestation_ess",
                "parent_id": "regime::TEST::R1",
            }
        )
        self.assertEqual(
            compute_numerator(
                "ind_24_handicap",
                2019,
                [],
                prestations,
                self.odd_nodes,
                self.decisions,
            ),
            0,
        )

    def test_null_is_unavailable_not_zero(self):
        prestations = [
            {
                "annee": 2025,
                "programme_id": "prestation::TEST::R1::P1",
                "institution": "TEST",
                "regime_code": "R1",
                "beneficiaires": None,
            }
        ]
        self.odd_nodes.append(
            {
                "id": "prestation::TEST::R1::P1",
                "type": "prestation_ess",
                "parent_id": "regime::TEST::R1",
            }
        )
        self.assertIsNone(
            compute_numerator(
                "ind_24_handicap",
                2025,
                [],
                prestations,
                self.odd_nodes,
                self.decisions,
            )
        )

    def test_payload_preserves_null_beneficiary_value(self):
        payload = build_indicateurs_payload(
            [],
            [{
                "annee": 2025,
                "institution": "TEST",
                "regime_code": "R1",
                "prestation_num": 1,
                "nom_fr": "Prestation test",
                "beneficiaires_total": None,
            }],
        )
        self.assertIsNone(payload["rows_prestations"][0]["beneficiaires"])

    def test_pre_implementation_component_is_na(self):
        row = _format_component_row(
            "Réforme de basculement",
            {
                "institution": "CNSSAP",
                "regime_code": "CNSSAP_R4",
                "values": {2022: 4038},
            },
            [2019, 2022],
            {2019, 2022},
            {"regime::CNSSAP::CNSSAP_R4": {"implemented_from": 2022}},
        )
        self.assertIn("*[N/A]*", row)
        self.assertIn("*4 038*", row)


class MaternityDenominatorTests(unittest.TestCase):
    def test_maternity_uses_explicit_birth_observations_without_wpp_fallback(self):
        constructions = {
            "ind_23_maternite::2020": {"value": 719335},
            "ind_23_maternite::2021": {"value": 4154340},
        }

        self.assertEqual(
            get_denominator_value("ind_23_maternite", 2020, constructions, {}, None),
            719335,
        )
        self.assertEqual(
            get_denominator_value("ind_23_maternite", 2021, constructions, {}, None),
            4154340,
        )
        self.assertIsNone(
            get_denominator_value("ind_23_maternite", 2022, constructions, {}, None)
        )


class DisabilityDenominatorTests(unittest.TestCase):
    def test_disability_uses_explicit_three_percent_severe_disability_estimate(self):
        constructions = {
            "ind_24_handicap::2022": {"value": 3071909},
        }

        self.assertEqual(
            get_denominator_value("ind_24_handicap", 2022, constructions, {}, None),
            3071909,
        )


class VulnerablePopulationTests(unittest.TestCase):
    def setUp(self):
        self.odd_nodes = [
            {"id": "regime::TEST::WORK", "type": "regime_ess"},
            {"id": "prestation::TEST::CHILD::P1", "type": "prestation_ess"},
            {"id": "prestation::TEST::PENSION::P1", "type": "prestation_ess"},
            {"id": "prestation::PAM::PAM_R1::num_1", "type": "prestation_ess"},
        ]
        self.regimes = [
            {
                "annee": 2022,
                "programme_id": "regime::TEST::WORK",
                "institution": "TEST",
                "regime_code": "WORK",
                "cotisants": 200,
            }
        ]
        self.prestations = [
            {
                "annee": 2022,
                "programme_id": "prestation::TEST::CHILD::P1",
                "institution": "TEST",
                "regime_code": "CHILD",
                "beneficiaires": 100,
            },
            {
                "annee": 2022,
                "programme_id": "prestation::TEST::PENSION::P1",
                "institution": "TEST",
                "regime_code": "PENSION",
                "beneficiaires": 50,
            },
            {
                "annee": 2022,
                "programme_id": "prestation::PAM::PAM_R1::num_1",
                "institution": "PAM",
                "regime_code": "PAM_R1",
                "beneficiaires": 40,
            },
        ]
        self.decisions = {
            "regime::TEST::WORK::ind_29_cotisants": "entierement_inclus",
            "prestation::TEST::CHILD::P1::ind_22_enfants": "inclus",
            "prestation::TEST::PENSION::P1::ind_27_vieillesse": "inclus",
            "prestation::PAM::PAM_R1::num_1::ind_28_vulnerables": "inclus",
        }

    def test_vulnerable_numerator_combines_children_and_targeted_assistance(self):
        self.assertEqual(
            compute_numerator(
                "ind_28_vulnerables",
                2022,
                self.regimes,
                self.prestations,
                self.odd_nodes,
                self.decisions,
            ),
            140,
        )

    def test_vulnerable_denominator_subtracts_contributors_and_pensioners(self):
        denominator = get_denominator_value(
            "ind_28_vulnerables",
            2022,
            {"global_131::2022": {"value": 1000}},
            {},
            None,
            self.regimes,
            self.prestations,
            self.odd_nodes,
            self.decisions,
        )
        self.assertEqual(denominator, 750)


if __name__ == "__main__":
    unittest.main()
