#!/usr/bin/env python3
"""Contract tests for the v0.9.2.1 actual Shape clearance engine."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import cadquery as cq


LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))

import cad_clearance_engine_v0921 as engine  # noqa: E402


class CadClearanceEngineContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.canaries = engine.run_canary_tests()

    def test_001_actual_boolean_overlap(self) -> None:
        self.assertEqual(self.canaries[0]["classification"], "INTERSECT")
        self.assertGreater(self.canaries[0]["intersection_volume_mm3"], 0.0)

    def test_002_actual_touch(self) -> None:
        self.assertEqual(self.canaries[1]["classification"], "CONTACT")
        self.assertEqual(self.canaries[1]["minimum_distance_mm"], 0.0)

    def test_003_known_gap_5(self) -> None:
        self.assertAlmostEqual(self.canaries[2]["minimum_distance_mm"], 5.0)

    def test_004_known_gap_10(self) -> None:
        self.assertAlmostEqual(self.canaries[3]["minimum_distance_mm"], 10.0)

    def test_005_coaxial_radial_gap(self) -> None:
        self.assertAlmostEqual(self.canaries[4]["minimum_distance_mm"], 1.0)
        self.assertEqual(self.canaries[4]["result"], "PASS")

    def test_006_sweep_collision_detected(self) -> None:
        self.assertTrue(self.canaries[5]["canary_pass"])
        self.assertEqual(self.canaries[5]["classification"], "INTERSECT")

    def test_007_all_canaries_pass(self) -> None:
        self.assertTrue(all(row["canary_pass"] for row in self.canaries))

    def test_008_error_never_returns_pass(self) -> None:
        result = engine.build_pair_result(
            "ERROR-CANARY", "INVALID_A", None, "INVALID_B", None,
            "CANARY", 0.0, "intentional type error",
        )
        self.assertEqual(result["classification"], "ERROR")
        self.assertEqual(result["result"], "ERROR")
        self.assertTrue(result["error"])

    def test_009_intersection_helper_returns_shape(self) -> None:
        a = cq.Workplane("XY").box(10, 10, 10).val()
        b = cq.Workplane("XY").box(10, 10, 10).translate((5, 0, 0)).val()
        common = engine.compute_intersection_shape(a, b)
        self.assertIsInstance(common, cq.Shape)
        self.assertGreater(common.Volume(), 0.0)

    def test_010_volume_helper_is_actual(self) -> None:
        a = cq.Workplane("XY").box(10, 10, 10).val()
        b = cq.Workplane("XY").box(10, 10, 10).translate((5, 0, 0)).val()
        self.assertAlmostEqual(engine.compute_intersection_volume(a, b), 500.0)

    def test_011_distance_helper_is_actual(self) -> None:
        a = cq.Workplane("XY").box(10, 10, 10).val()
        b = cq.Workplane("XY").box(10, 10, 10).translate((15, 0, 0)).val()
        self.assertAlmostEqual(engine.compute_minimum_distance(a, b), 5.0)

    def test_012_nearest_points_recorded(self) -> None:
        row = self.canaries[2]
        for suffix in ("a_x", "a_y", "a_z", "b_x", "b_y", "b_z"):
            self.assertIsNotNone(row[f"nearest_point_{suffix}"])

    def test_013_tolerances_are_explicit(self) -> None:
        self.assertEqual(engine.CAD_NUMERICAL_DISTANCE_TOLERANCE_MM, 0.05)
        self.assertEqual(engine.CAD_INTERSECTION_VOLUME_TOLERANCE_MM3, 0.01)

    def test_014_sampling_interval_is_half_mm(self) -> None:
        self.assertLessEqual(engine.FULL_SWEEP_SAMPLE_INTERVAL_MM, 0.5)

    def test_015_summary_does_not_hide_contact(self) -> None:
        summary = engine.summarize_pair_results(self.canaries[:5])
        self.assertGreaterEqual(summary["total_contact"], 1)
        self.assertGreaterEqual(summary["total_intersect"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
