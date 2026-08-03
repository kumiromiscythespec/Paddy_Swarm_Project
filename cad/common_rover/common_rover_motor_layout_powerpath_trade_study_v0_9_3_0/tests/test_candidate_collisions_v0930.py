from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))
import build_motor_layout_powerpath_trade_study_v0930 as b


class CandidateCollisionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (LANE / "candidate_trade_matrix_v0930.csv").open(encoding="utf-8", newline="") as stream:
            cls.trades = {row["candidate_id"]: row for row in csv.DictReader(stream)}
        with (LANE / "candidate_collision_matrix_v0930.csv").open(encoding="utf-8", newline="") as stream:
            cls.collisions = list(csv.DictReader(stream))

    def test_001_required_environment_checks(self) -> None:
        expected = {"CBOX", "BBOX", "FRAME", "TRACKS", "BATTERY_EXTRACTION_KEEP_OUT", "UNIT_MATING_KEEP_OUT", "DRAINAGE_KEEP_OUT"}
        for candidate_id in b.CANDIDATES:
            actual = {row["environment"] for row in self.collisions if row["candidate_id"] == candidate_id}
            self.assertEqual(actual, expected)

    def test_002_actual_common_volume_is_recorded(self) -> None:
        self.assertTrue(all(row["calculation"] == "CADQUERY_ACTUAL_SHAPE_COMMON_VOLUME" for row in self.collisions))
        self.assertTrue(all(float(row["intersection_volume_mm3"]) >= 0 for row in self.collisions))

    def test_003_candidate_a_hard_pass(self) -> None:
        self.assertEqual(self.trades["A_LATERAL_FRONT_DIRECT"]["hard_constraint_pass"], "YES")

    def test_004_candidate_c_track_fail(self) -> None:
        row = self.trades["C_LATERAL_FORE_AFT_STAGGERED"]
        self.assertEqual(row["hard_constraint_pass"], "NO")
        self.assertIn("TRACK", row["rejection_reason"])

    def test_005_candidate_g_axis_fail(self) -> None:
        report = json.loads((LANE / "artifacts/candidates/G_CURRENT_REPOSITORY_LAYOUT_REPRODUCTION/COLLISION_REPORT.json").read_text(encoding="utf-8"))
        self.assertFalse(report["registered_input_axis_coaxial"])
        self.assertAlmostEqual(report["registered_input_axis_perpendicular_mismatch_mm"], 19.235384, places=6)
        self.assertEqual(report["status"], "FAIL")

    def test_006_sealed_boxes_not_crossed_by_recommended_fixed_power(self) -> None:
        rows = [row for row in self.collisions if row["candidate_id"] == "A_LATERAL_FRONT_DIRECT" and row["shape_group"] in ("fixed_motor", "fixed_power") and row["environment"] in ("CBOX", "BBOX")]
        self.assertTrue(all(row["collision"] == "NO" for row in rows))

    def test_007_frame_and_track_checked(self) -> None:
        rank1 = self.trades["A_LATERAL_FRONT_DIRECT"]
        self.assertEqual(rank1["frame_collision"], "NO")
        self.assertEqual(rank1["track_collision"], "NO")

    def test_008_battery_unit_drain_checked(self) -> None:
        rank1 = self.trades["A_LATERAL_FRONT_DIRECT"]
        self.assertEqual(rank1["battery_service_collision"], "NO")
        self.assertEqual(rank1["unit_bay_collision"], "NO")
        self.assertEqual(rank1["drainage_collision"], "NO")

    def test_009_e_unit_overlap_is_authorized_interface_only(self) -> None:
        rows = [row for row in self.collisions if row["candidate_id"] == "E_LONGITUDINAL_FRONT_PTO" and row["environment"] == "UNIT_MATING_KEEP_OUT" and row["shape_group"] == "fixed_power"]
        self.assertEqual(len(rows), 1)
        if rows[0]["collision"] == "YES":
            self.assertEqual(rows[0]["authorization"], "AUTHORIZED_PTO_INTERFACE")
            self.assertEqual(rows[0]["hard_constraint_effect"], "PASS")

    def test_010_service_is_not_fixed_collision(self) -> None:
        a = json.loads((LANE / "artifacts/candidates/A_LATERAL_FRONT_DIRECT/DIMENSION_REPORT.json").read_text(encoding="utf-8"))
        self.assertGreater(a["service_width_mm"], a["complete_guarded_width_mm"])
        self.assertTrue(a["service_may_temporarily_exceed_290"])

    def test_011_recommended_reason_explicit(self) -> None:
        decision = json.loads((LANE / "recommended_layout_decision_v0930.json").read_text(encoding="utf-8"))
        self.assertEqual(decision["RECOMMENDED_LAYOUT_FOR_NEXT_CAD"], "A_LATERAL_FRONT_DIRECT")
        self.assertEqual(decision["DECISION_CLASS"], "TOP_2_CANDIDATES_PHYSICAL_MOCKUP_REQUIRED")

    def test_012_rejected_reasons_explicit(self) -> None:
        for candidate_id in ("C_LATERAL_FORE_AFT_STAGGERED", "G_CURRENT_REPOSITORY_LAYOUT_REPRODUCTION"):
            self.assertTrue(self.trades[candidate_id]["rejection_reason"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
