from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))
import build_motor_layout_powerpath_trade_study_v0930 as b


class MotorLayoutCandidateContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.params = json.loads((LANE / "common_rover_motor_candidate_parameters_v0930.json").read_text(encoding="utf-8"))
        with (LANE / "candidate_trade_matrix_v0930.csv").open(encoding="utf-8", newline="") as stream:
            cls.trades = list(csv.DictReader(stream))

    def test_001_candidates_a_through_g(self) -> None:
        self.assertEqual(set(self.params["candidates"]), set(b.CANDIDATES))
        self.assertEqual(len(self.trades), 7)

    def test_002_parameter_grid_not_single_point(self) -> None:
        searches = self.params["grid_searches"]
        self.assertGreater(sum(row["evaluated_count"] for row in searches.values()), 8000)
        self.assertTrue(all(row["selection_rule"] for row in searches.values()))

    def test_003_grid_spacing_contract(self) -> None:
        for candidate_id, search in self.params["grid_searches"].items():
            if candidate_id.startswith("G_"):
                continue
            grid = search["grid"]
            self.assertIn(grid["x"][2], (2, 5))
            self.assertEqual(grid["y"][2], 5)
            self.assertEqual(grid["z"][2], 5)

    def test_004_actual_shape_reports(self) -> None:
        for candidate_id in b.CANDIDATES:
            report = json.loads((LANE / "artifacts" / "candidates" / candidate_id / "COLLISION_REPORT.json").read_text(encoding="utf-8"))
            self.assertTrue(report["actual_shape_calculation"])
            self.assertTrue(all(row["calculation"] == "CADQUERY_ACTUAL_SHAPE_COMMON_VOLUME" for row in report["rows"]))

    def test_005_all_ten_states_for_all_candidates(self) -> None:
        for candidate_id in b.CANDIDATES:
            for name in b.CANDIDATE_STATE_STEPS:
                self.assertTrue((LANE / "artifacts" / "candidates" / candidate_id / name).is_file(), f"{candidate_id}/{name}")

    def test_006_all_views_and_reports(self) -> None:
        for candidate_id in b.CANDIDATES:
            for name in (*b.CANDIDATE_VISUALS, *b.CANDIDATE_REPORTS):
                self.assertTrue((LANE / "artifacts" / "candidates" / candidate_id / name).is_file())

    def test_007_fixed_guard_and_service_width_separate(self) -> None:
        for row in self.trades:
            self.assertIn("total_fixed_width_mm", row)
            self.assertIn("total_guarded_width_mm", row)
            report = json.loads((LANE / "artifacts" / "candidates" / row["candidate_id"] / "DIMENSION_REPORT.json").read_text(encoding="utf-8"))
            self.assertTrue(report["fixed_width_from_actual_solids"])
            self.assertTrue(report["guard_width_from_actual_solids"])
            self.assertTrue(report["service_width_from_actual_solids"])

    def test_008_target_and_absolute_widths(self) -> None:
        self.assertEqual(self.params["target_width_mm"], 290)
        self.assertEqual(self.params["absolute_width_rule"], "LESS_THAN_300_MM")
        ranked = next(row for row in self.trades if row["recommendation_rank"] == "1")
        self.assertLessEqual(float(ranked["total_guarded_width_mm"]), 290.0)
        self.assertLess(float(ranked["total_guarded_width_mm"]), 300.0)

    def test_009_candidate_a_exact_selected_position(self) -> None:
        data = self.params["candidates"]["A_LATERAL_FRONT_DIRECT"]
        self.assertEqual(data["front_left"], [68.0, -185.0, 105.0])
        self.assertEqual(data["front_right"], [-68.0, -185.0, 105.0])

    def test_010_candidate_g_uses_current_axis_line(self) -> None:
        data = self.params["candidates"]["G_CURRENT_REPOSITORY_LAYOUT_REPRODUCTION"]
        self.assertEqual(data["front_left"][0], 96.0)
        self.assertEqual(data["front_right"][0], -96.0)

    def test_011_top_candidate_hard_pass(self) -> None:
        rank1 = next(row for row in self.trades if row["recommendation_rank"] == "1")
        self.assertEqual(rank1["hard_constraint_pass"], "YES")

    def test_012_hard_failure_cannot_rank_first(self) -> None:
        for row in self.trades:
            if row["hard_constraint_pass"] == "NO":
                self.assertNotEqual(row["recommendation_rank"], "1")
                self.assertTrue(row["rejection_reason"])

    def test_013_comparison_svgs(self) -> None:
        for rel in b.COMPARISON_ARTIFACTS:
            self.assertGreater((LANE / rel).stat().st_size, 1000)

    def test_014_exact_package_contract(self) -> None:
        self.assertEqual(len(b.PACKAGE_PATHS), 151)
        self.assertEqual(set(b._lane_files()), set(b.PACKAGE_PATHS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
