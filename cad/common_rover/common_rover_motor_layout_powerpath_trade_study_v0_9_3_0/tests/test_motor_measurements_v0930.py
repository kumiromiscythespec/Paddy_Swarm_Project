from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))
import build_motor_layout_powerpath_trade_study_v0930 as b


class MotorMeasurementContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads((LANE / "common_rover_jgb37_520_physical_measurements_v0930.json").read_text(encoding="utf-8"))
        cls.rows = {row["measurement_id"]: row for row in cls.payload["measurements"]}

    def test_001_all_user_values_exact(self) -> None:
        expected = {row[0]: row[3] for row in b.MEASUREMENTS}
        self.assertEqual({key: row["measured_value_mm"] for key, row in self.rows.items()}, expected)

    def test_002_k_fastener_is_3p4(self) -> None:
        self.assertEqual(self.rows["K"]["measured_value_mm"], 3.4)

    def test_003_slot_27p7_is_not_fastener(self) -> None:
        self.assertEqual(self.rows["SLOT_27P7"]["measured_value_mm"], 27.7)
        self.assertNotEqual(self.rows["SLOT_27P7"]["component"], self.rows["K"]["description"])
        self.assertEqual(self.rows["SLOT_27P7"]["status"], "MEASUREMENT_HOLD")

    def test_004_derived_fixed_envelope(self) -> None:
        self.assertEqual(self.payload["derived"]["MOTOR_BODY_AND_REAR_TERMINAL_FROM_FRONT_PLATE_MM"], 70.1)
        self.assertEqual(self.payload["derived"]["MOTOR_TOTAL_AXIAL_FIXED_ENVELOPE_MM"], 87.0)
        self.assertEqual(self.payload["derived"]["MOTOR_FRONT_PLATE_TO_SHAFT_TIP_MM"], 16.9)

    def test_005_uncertainty_not_fabricated(self) -> None:
        self.assertTrue(all(row["uncertainty"] == "USER_NOT_REPORTED" for row in self.rows.values()))

    def test_006_measurement_source(self) -> None:
        self.assertTrue(all(row["measurement_source"] == "USER_REPORTED_PHYSICAL_CALIPER_MEASUREMENT" for row in self.rows.values()))

    def test_007_no_manufacturing_authority(self) -> None:
        self.assertTrue(all(row["manufacturing_authority"] == "NOT_FOR_MANUFACTURING" for row in self.rows.values()))

    def test_008_independent_reference_shapes(self) -> None:
        names = b.motor_reference_shapes()
        required = {"MOTOR_CYLINDER", "REAR_TERMINAL_FIXED_ENVELOPE", "REAR_CABLE_SERVICE_ENVELOPE", "FRONT_PLATE", "OUTPUT_SHAFT", "SHAFT_ROOT_BOSS", "MOUNT_BRACKET", "M3_FASTENER_HOLE_CANDIDATES", "VERTICAL_SLOT_PLACEHOLDER", "MOTOR_GUARD_CANDIDATE_ENVELOPE", "MOTOR_REMOVAL_SWEEP"}
        self.assertTrue(required.issubset(names))

    def test_009_service_and_guard_series(self) -> None:
        self.assertEqual(b.SERVICE_REAR_EXTRA_MM, {"S0": 10.0, "S1": 15.0, "S2": 20.0, "S3": 25.0})
        self.assertEqual(b.GUARD_SIDE_MARGIN_MM, {"G0": 3.0, "G1": 5.0, "G2": 8.0, "G3": 10.0})

    def test_010_release_states(self) -> None:
        text = (LANE / "NO_MANUFACTURING_RELEASE.txt").read_text(encoding="utf-8")
        self.assertIn("MANUFACTURING_RELEASE=NOT_APPROVED", text)
        self.assertIn("POWERED_TEST=NOT_APPROVED", text)
        self.assertIn("FIELD_DEPLOYMENT=NOT_APPROVED", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
