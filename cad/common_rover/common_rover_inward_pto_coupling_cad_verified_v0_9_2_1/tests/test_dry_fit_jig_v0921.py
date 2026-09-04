#!/usr/bin/env python3
"""Contract tests for the independent-shaft v0.9.2.1 dry-fit jig."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))

import dry_fit_jig_builder_v0921 as jig  # noqa: E402


class DryFitJigContract(unittest.TestCase):
    def test_001_nine_states(self) -> None:
        self.assertEqual(len(jig.DRY_FIT_STATES), 9)

    def test_002_exact_df0_to_df8(self) -> None:
        self.assertEqual(
            [state.split("_", 1)[0] for state in jig.DRY_FIT_STATES],
            [f"DF{i}" for i in range(9)],
        )

    def test_003_two_independent_shafts(self) -> None:
        shapes = jig.assembly_named_shapes("DF1_SHAFTS_POSITIONED")
        self.assertIn("LEFT_TEST_SHAFT", shapes)
        self.assertIn("RIGHT_TEST_SHAFT", shapes)
        self.assertIsNot(shapes["LEFT_TEST_SHAFT"], shapes["RIGHT_TEST_SHAFT"])

    def test_004_no_center_crossing(self) -> None:
        shapes = jig.assembly_named_shapes("DF1_SHAFTS_POSITIONED")
        left = shapes["LEFT_TEST_SHAFT"].BoundingBox()
        right = shapes["RIGHT_TEST_SHAFT"].BoundingBox()
        self.assertGreaterEqual(left.ymin, 18.0)
        self.assertLessEqual(right.ymax, -18.0)

    def test_005_center_gap_36(self) -> None:
        shapes = jig.assembly_named_shapes("DF1_SHAFTS_POSITIONED")
        left = shapes["LEFT_TEST_SHAFT"].BoundingBox()
        right = shapes["RIGHT_TEST_SHAFT"].BoundingBox()
        self.assertAlmostEqual(left.ymin - right.ymax, 36.0)

    def test_006_left_end_plus_18(self) -> None:
        self.assertEqual(jig.test_shaft("LEFT").BoundingBox().ymin, 18.0)

    def test_007_right_end_minus_18(self) -> None:
        self.assertEqual(jig.test_shaft("RIGHT").BoundingBox().ymax, -18.0)

    def test_008_uncut_300_stock(self) -> None:
        self.assertEqual(jig.SHAFT_STOCK_LENGTH_MM, 300.0)
        self.assertAlmostEqual(jig.test_shaft("LEFT").BoundingBox().ylen, 300.0)
        self.assertAlmostEqual(jig.test_shaft("RIGHT").BoundingBox().ylen, 300.0)

    def test_009_stub_12p5(self) -> None:
        self.assertEqual(jig.LEFT_FACE_Y_MM - jig.LEFT_SHAFT_END_Y_MM, 12.5)
        self.assertEqual(jig.RIGHT_SHAFT_END_Y_MM - jig.RIGHT_FACE_Y_MM, 12.5)

    def test_010_sleeve_stroke_10(self) -> None:
        self.assertEqual(jig.SLEEVE_STROKE_MM, 10.0)

    def test_011_engagement_reference_8(self) -> None:
        self.assertEqual(jig.ENGAGEMENT_REFERENCE_MM, 8.0)

    def test_012_overlap_is_derived(self) -> None:
        self.assertEqual(jig.engagement_overlap_from_intervals(0.0), 0.0)
        self.assertEqual(jig.engagement_overlap_from_intervals(5.0), 5.0)
        self.assertEqual(jig.engagement_overlap_from_intervals(10.0), 10.0)

    def test_013_full_travel_satisfies_reference(self) -> None:
        self.assertGreaterEqual(
            jig.engagement_overlap_from_intervals(10.0),
            jig.ENGAGEMENT_REFERENCE_MM,
        )

    def test_014_independent_unit_inputs(self) -> None:
        shapes = jig.assembly_named_shapes("DF6_ENGAGED")
        left = shapes["LEFT_UNIT_INPUT_DUMMY"].BoundingBox()
        right = shapes["RIGHT_UNIT_INPUT_DUMMY"].BoundingBox()
        self.assertGreater(left.ymin, right.ymax)

    def test_015_front_insertion_shift(self) -> None:
        inserting = jig.assembly_named_shapes("DF3_UNIT_INSERTING")
        locked = jig.assembly_named_shapes("DF4_UNIT_LOCKED")
        self.assertGreater(
            inserting["LEFT_UNIT_INPUT_DUMMY"].BoundingBox().xmin,
            locked["LEFT_UNIT_INPUT_DUMMY"].BoundingBox().xmin,
        )

    def test_016_center_gap_gauge_36(self) -> None:
        self.assertAlmostEqual(jig.center_gap_gauge().BoundingBox().ylen, 36.0)

    def test_017_comparison_gauges(self) -> None:
        self.assertAlmostEqual(jig.center_gap_gauge(35).BoundingBox().ylen, 35)
        self.assertAlmostEqual(jig.center_gap_gauge(37).BoundingBox().ylen, 37)

    def test_018_stub_gauge_12p5(self) -> None:
        self.assertAlmostEqual(jig.stub_gauge().BoundingBox().ylen, 12.5)

    def test_019_print_plate_fits_a1_candidate(self) -> None:
        shapes = list(jig.print_plate_shapes().values())
        compound = __import__("cadquery").Compound.makeCompound(shapes)
        bounds = compound.BoundingBox()
        self.assertLessEqual(bounds.xlen, 256.0)
        self.assertLessEqual(bounds.ylen, 256.0)
        self.assertLessEqual(bounds.zlen, 256.0)

    def test_020_part_list_warns_no_load(self) -> None:
        warnings = " ".join(row["warning"] for row in jig.dry_fit_part_rows())
        self.assertIn("NO_LOAD", warnings)
        self.assertIn("NOT_A_MANUFACTURING_HOLE", warnings)
        self.assertIn("NOT_FOR_TORQUE", warnings)

    def test_021_dimensions_prohibit_continuous_shaft(self) -> None:
        row = next(
            row for row in jig.dry_fit_dimension_rows()
            if row["parameter"] == "SINGLE_CONTINUOUS_SHAFT_USED"
        )
        self.assertIs(row["value"], False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
