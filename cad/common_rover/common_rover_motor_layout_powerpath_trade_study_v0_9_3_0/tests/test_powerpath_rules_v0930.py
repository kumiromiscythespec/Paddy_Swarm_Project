from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))
import build_motor_layout_powerpath_trade_study_v0930 as b


class PowerpathRuleContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads((LANE / "common_rover_powerpath_candidate_parameters_v0930.json").read_text(encoding="utf-8"))
        cls.rules = cls.payload["global_rules"]

    def test_001_p1_through_p6_exist(self) -> None:
        self.assertEqual(set(self.payload["powerpaths"]), {f"P{i}" for i in range(1, 7)})

    def test_002_belt_never_turns_axis_90(self) -> None:
        self.assertEqual(self.rules["belt_90_degree_axis_change"], "PROHIBITED")

    def test_003_chain_never_turns_axis_90(self) -> None:
        self.assertEqual(self.rules["chain_90_degree_axis_change"], "PROHIBITED")

    def test_004_explicit_right_angle_devices(self) -> None:
        for pid in ("P3", "P4", "P5", "P6"):
            self.assertEqual(self.payload["powerpaths"][pid]["right_angle"], 1)
            self.assertGreaterEqual(self.payload["powerpaths"][pid]["gear_pairs"], 2)

    def test_005_dog_clutch_coaxial(self) -> None:
        self.assertEqual(self.rules["dog_clutch"], "COAXIAL_ONLY")

    def test_006_simultaneous_drive_pto_prohibited(self) -> None:
        self.assertEqual(self.rules["drive_pto_simultaneous"], "PROHIBITED")

    def test_007_left_right_independent(self) -> None:
        self.assertEqual(self.rules["left_right_common_shaft"], "PROHIBITED")
        self.assertEqual(self.rules["left_right_drive_independence"], "REQUIRED")

    def test_008_brake_required_during_pto(self) -> None:
        self.assertEqual(self.rules["brake_or_mechanical_lock_during_pto"], "REQUIRED")

    def test_009_p1_common_means_pattern_not_shaft(self) -> None:
        note = self.payload["powerpaths"]["P1"]["note"]
        self.assertIn("never a common physical left-right shaft", note)

    def test_010_p4_drive_only_right_angle(self) -> None:
        self.assertIn("DRIVE branch alone", self.payload["powerpaths"]["P4"]["note"])

    def test_011_s2_is_no_load_only(self) -> None:
        self.assertEqual(self.payload["S2_10P30"], "NO_LOAD_PRINTED_SLIDE_REFERENCE_ONLY")
        self.assertEqual(self.payload["METAL_TORQUE_CLUTCH_TOLERANCE"], "NOT_DERIVED_FROM_S2")

    def test_012_p6_purchase_hold(self) -> None:
        self.assertIn("PURCHASE_HOLD", self.payload["powerpaths"]["P6"]["note"])

    def test_013_unit_mass_not_shaft_supported(self) -> None:
        text = (LANE / "candidate_PTO_interface_report_v0930.md").read_text(encoding="utf-8")
        self.assertIn("not carried by PTO shaft or box walls", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
