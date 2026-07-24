from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
import sys
import unittest


MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from authority_loader import COMPONENT_IDS, Envelope, load_authority
from inspectors import inspect_all_solids
from solid_builders import build_minimum_assembly
from validation import IDS, canonical_report_json, validate_seed


EXPECTED_BOUNDS = {
    IDS["left"]: (69.0, -232.0, 0.0, 89.0, 0.0, 20.0),
    IDS["right"]: (-89.0, -232.0, 0.0, -69.0, 0.0, 20.0),
    IDS["cross"]: (-69.0, -232.0, 0.0, 69.0, -212.0, 20.0),
    IDS["cbox"]: (-65.0, -140.0, 0.0, 65.0, 0.0, 105.0),
    IDS["bbox"]: (-75.0, 0.0, 0.0, 75.0, 220.0, 150.0),
    IDS["battery"]: (-62.5, 20.0, 15.0, 62.5, 200.0, 135.0),
}
EXPECTED_VOLUMES_MM3 = {
    IDS["left"]: 92800.0,
    IDS["right"]: 92800.0,
    IDS["cross"]: 55200.0,
    IDS["cbox"]: 1911000.0,
    IDS["bbox"]: 4950000.0,
    IDS["battery"]: 2700000.0,
}


class ExecutableSeedPositiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = load_authority()
        cls.solids = dict(build_minimum_assembly(cls.authority))
        cls.report = validate_seed(cls.authority, cls.authority)

    def test_authority_loader_returns_exact_six_component_registry_subset(self) -> None:
        self.assertEqual(
            tuple(component.component_id for component in self.authority.components),
            COMPONENT_IDS,
        )
        self.assertEqual(self.authority.units, "millimetres")
        self.assertEqual(
            self.authority.battery_placement_status,
            "PLACED_FROM_HARDWARE_ENVELOPE_REGISTRY",
        )
        self.assertEqual(len(self.authority.source_records), 7)

    def test_exact_authority_envelopes(self) -> None:
        for component_id, expected in EXPECTED_BOUNDS.items():
            with self.subTest(component_id=component_id):
                component = self.authority.component(component_id)
                self.assertEqual(
                    (*component.minimum, *component.maximum),
                    expected,
                )

    def test_six_valid_single_solids_with_exact_bounds_and_positive_volume(self) -> None:
        rows = inspect_all_solids(
            self.solids,
            self.authority.components,
            self.authority.linear_tolerance_mm,
        )
        self.assertEqual(len(rows), 6)
        for row in rows:
            with self.subTest(component_id=row["component_id"]):
                self.assertEqual(row["status"], "PASS")
                self.assertEqual(row["solid_count"], 1)
                self.assertTrue(row["valid"])
                self.assertGreater(row["volume_mm3"], 0.0)
                self.assertTrue(
                    math.isclose(
                        row["volume_mm3"],
                        EXPECTED_VOLUMES_MM3[row["component_id"]],
                        abs_tol=self.authority.intersection_volume_tolerance_mm3,
                        rel_tol=0.0,
                    )
                )
                self.assertEqual(row["blockers"], [])

    def test_validation_contract_and_width_classes(self) -> None:
        report = self.report
        self.assertEqual(report["EXECUTABLE_CAD_SEED_STATUS"], "PASS_WITH_HOLD")
        self.assertEqual(report["actual_solid_count"], 6)
        self.assertEqual(tuple(report["required_solid_ids"]), COMPONENT_IDS)
        self.assertEqual(set(report["actual_solid_ids"]), set(COMPONENT_IDS))
        self.assertEqual(report["missing_solid_ids"], [])
        self.assertEqual(report["extra_solid_ids"], [])
        self.assertEqual(report["solid_id_set_status"], "PASS")
        self.assertEqual(report["total_possible_pair_count"], 15)
        self.assertEqual(report["pair_policy_count"], 15)
        self.assertEqual(report["boolean_checked_pair_count"], 4)
        self.assertEqual(report["envelope_checked_pair_count"], 5)
        self.assertEqual(report["intended_containment_pair_count"], 1)
        self.assertEqual(report["unchecked_or_unauthorized_pair_count"], 10)
        self.assertEqual(report["pair_policy_status"], "PASS")
        self.assertEqual(
            report["battery_bbox_containment"]["classification"],
            "INTENDED_CONTAINMENT",
        )
        self.assertEqual(
            report["battery_bbox_containment"]["status"], "PASS"
        )
        self.assertEqual(report["intended_face_contact_count"], 2)
        self.assertEqual(report["unintended_volumetric_intersection_count"], 0)
        self.assertEqual(report["mirror_validation"]["status"], "PASS")
        self.assertEqual(
            report["battery_cassette"]["placement_source"],
            "rovers/common_rover/v2.29.3.9.1/hardware_envelope_registry.json",
        )
        self.assertFalse(report["battery_cassette"]["guessed_values_used"])
        self.assertEqual(
            report["width_authority"],
            {
                "actual_minimum_assembly_width_mm": 178.0,
                "bare_fpb_width_mm": 178.0,
                "registered_maximum_interface_width_mm": 286.0,
                "operational_hard_limit_mm": 300.0,
                "registered_interface_geometry_synthesized": False,
            },
        )
        self.assertEqual(report["blockers"], [])

    def test_report_serialization_is_deterministic(self) -> None:
        first = validate_seed(self.authority, self.authority)
        second = validate_seed(self.authority, self.authority)
        self.assertEqual(canonical_report_json(first), canonical_report_json(second))


class ExecutableSeedNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = load_authority()

    def assert_blocker(self, candidate, blocker: str) -> None:
        report = validate_seed(candidate, self.reference)
        self.assertEqual(report["EXECUTABLE_CAD_SEED_STATUS"], "FAIL")
        self.assertIn(blocker, report["blockers"])

    def test_negative_01_swapped_left_and_right_rails(self) -> None:
        left = self.reference.component(IDS["left"])
        right = self.reference.component(IDS["right"])
        candidate = self.reference.with_component(
            left.with_bounds(right.minimum, right.maximum)
        ).with_component(right.with_bounds(left.minimum, left.maximum))
        self.assert_blocker(candidate, "LEFT_ENVELOPE_MISMATCH")
        self.assert_blocker(candidate, "RIGHT_RAIL_CENTER_X_MISMATCH")

    def test_negative_02_shifted_left_rail_centerline(self) -> None:
        left = self.reference.component(IDS["left"]).translated((1.0, 0.0, 0.0))
        self.assert_blocker(
            self.reference.with_component(left), "LEFT_RAIL_CENTER_X_MISMATCH"
        )

    def test_negative_03_wrong_left_rail_width(self) -> None:
        left = self.reference.component(IDS["left"])
        left = left.with_bounds(maximum=(88.0, left.maximum[1], left.maximum[2]))
        self.assert_blocker(
            self.reference.with_component(left), "LEFT_RAIL_WIDTH_MISMATCH"
        )

    def test_negative_04_wrong_front_datum(self) -> None:
        left = self.reference.component(IDS["left"]).translated((0.0, 1.0, 0.0))
        self.assert_blocker(self.reference.with_component(left), "FRONT_DATUM_MISMATCH")

    def test_negative_05_wrong_crossmember_length(self) -> None:
        cross = self.reference.component(IDS["cross"])
        cross = cross.with_bounds(maximum=(68.0, *cross.maximum[1:]))
        self.assert_blocker(
            self.reference.with_component(cross), "CROSSMEMBER_LENGTH_MISMATCH"
        )

    def test_negative_06_wrong_crossmember_rear_face(self) -> None:
        cross = self.reference.component(IDS["cross"]).translated((0.0, 1.0, 0.0))
        self.assert_blocker(self.reference.with_component(cross), "CROSS_ENVELOPE_MISMATCH")

    def test_negative_07_gap_at_left_crossmember_joint(self) -> None:
        cross = self.reference.component(IDS["cross"])
        cross = cross.with_bounds(maximum=(68.0, *cross.maximum[1:]))
        self.assert_blocker(
            self.reference.with_component(cross),
            "LEFT_CROSSMEMBER_CONTACT_MISMATCH",
        )

    def test_negative_08_overlap_at_left_crossmember_joint(self) -> None:
        cross = self.reference.component(IDS["cross"])
        cross = cross.with_bounds(maximum=(70.0, *cross.maximum[1:]))
        self.assert_blocker(
            self.reference.with_component(cross),
            "UNINTENDED_VOLUMETRIC_INTERSECTION",
        )

    def test_negative_09_cbox_bbox_side_by_side_arrangement(self) -> None:
        bbox = self.reference.component(IDS["bbox"]).with_bounds(
            minimum=(65.0, -140.0, 0.0),
            maximum=(215.0, 80.0, 150.0),
        )
        self.assert_blocker(
            self.reference.with_component(bbox), "CBOX_BBOX_SIDE_BY_SIDE_FORBIDDEN"
        )

    def test_negative_10_reversed_cbox_bbox_longitudinal_order(self) -> None:
        cbox = self.reference.component(IDS["cbox"]).with_bounds(
            minimum=(-65.0, 0.0, 0.0),
            maximum=(65.0, 140.0, 105.0),
        )
        bbox = self.reference.component(IDS["bbox"]).with_bounds(
            minimum=(-75.0, -220.0, 0.0),
            maximum=(75.0, 0.0, 150.0),
        )
        candidate = self.reference.with_component(cbox).with_component(bbox)
        self.assert_blocker(candidate, "CBOX_BBOX_ORDER_MISMATCH")

    def test_negative_11_wrong_core_length_parameter(self) -> None:
        candidate = replace(self.reference, core_length_mm=359.0)
        self.assert_blocker(candidate, "CORE_LENGTH_MISMATCH")

    def test_negative_12_nan_parameter(self) -> None:
        left = self.reference.component(IDS["left"])
        left = left.with_bounds(minimum=(math.nan, *left.minimum[1:]))
        self.assert_blocker(
            self.reference.with_component(left),
            f"{IDS['left']}:NONFINITE_PARAMETER",
        )

    def test_negative_13_infinite_parameter(self) -> None:
        right = self.reference.component(IDS["right"])
        right = right.with_bounds(maximum=(math.inf, *right.maximum[1:]))
        self.assert_blocker(
            self.reference.with_component(right),
            f"{IDS['right']}:NONFINITE_PARAMETER",
        )

    def test_negative_14_negative_dimension(self) -> None:
        battery = self.reference.component(IDS["battery"])
        battery = battery.with_bounds(
            maximum=(battery.minimum[0] - 1.0, *battery.maximum[1:])
        )
        self.assert_blocker(
            self.reference.with_component(battery),
            f"{IDS['battery']}:NONPOSITIVE_DIMENSION",
        )

    def test_negative_15_zero_dimension(self) -> None:
        cbox = self.reference.component(IDS["cbox"])
        cbox = cbox.with_bounds(
            maximum=(cbox.minimum[0], *cbox.maximum[1:])
        )
        self.assert_blocker(
            self.reference.with_component(cbox),
            f"{IDS['cbox']}:NONPOSITIVE_DIMENSION",
        )


if __name__ == "__main__":
    unittest.main()
