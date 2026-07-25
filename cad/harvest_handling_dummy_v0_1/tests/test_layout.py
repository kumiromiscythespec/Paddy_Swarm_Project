"""Authoritative fixed-layout count, spacing, and asymmetry tests."""

from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

CAD_ROOT = Path(__file__).resolve().parents[2]
if str(CAD_ROOT) not in sys.path:
    sys.path.insert(0, str(CAD_ROOT))

from harvest_handling_dummy_v0_1.presets.layout_standard_v001 import (
    LAYOUT_STANDARD_V001,
    coordinate_set,
    maximum_radial_diameter,
    minimum_center_spacing,
    radial_band_counts,
    symmetry_matches,
    validate_layout,
)


class FixedLayoutTests(unittest.TestCase):
    """The 24-row layout must remain deterministic and pseudo-irregular."""

    def test_standard_layout_validates_and_is_unique(self) -> None:
        validate_layout()
        self.assertEqual(
            [entry.socket_id for entry in LAYOUT_STANDARD_V001],
            [f"S{index:02d}" for index in range(1, 25)],
        )
        self.assertEqual(len(coordinate_set()), 24)

    def test_six_rows_per_module(self) -> None:
        self.assertEqual(
            Counter(entry.base_module for entry in LAYOUT_STANDARD_V001),
            Counter({"A": 6, "B": 6, "C": 6, "D": 6}),
        )

    def test_spacing_diameter_bands_and_asymmetry(self) -> None:
        self.assertGreaterEqual(minimum_center_spacing(), 21.0)
        self.assertLessEqual(maximum_radial_diameter(), 150.0)
        self.assertEqual(
            radial_band_counts(),
            {
                "CENTER_LE_45": 10,
                "MID_45_TO_60": 9,
                "OUTER_60_TO_75": 5,
            },
        )
        self.assertEqual(
            symmetry_matches(),
            {"x_axis": False, "y_axis": False, "rotation_180": False},
        )

    def test_tilt_direction_and_height_quantities(self) -> None:
        self.assertEqual(
            Counter(entry.tilt_angle_deg for entry in LAYOUT_STANDARD_V001),
            Counter({0.0: 8, 10.0: 8, 20.0: 6, 30.0: 2}),
        )
        self.assertEqual(
            Counter(entry.tilt_direction_deg for entry in LAYOUT_STANDARD_V001),
            Counter({float(direction): 3 for direction in range(0, 360, 45)}),
        )
        self.assertEqual(
            Counter(entry.height_class for entry in LAYOUT_STANDARD_V001),
            Counter({"LOW": 8, "STANDARD": 10, "HIGH": 6}),
        )

    def test_v010_state_columns_remain_fixed(self) -> None:
        for entry in LAYOUT_STANDARD_V001:
            self.assertEqual(entry.stem_class, "UNASSIGNED")
            self.assertEqual(entry.pre_bend_code, "NONE")
            self.assertEqual(entry.panicle_class, "NONE")
            self.assertEqual(entry.leaf_state, "NONE")
            self.assertEqual(entry.release_group, "FIXED")


if __name__ == "__main__":
    unittest.main()
