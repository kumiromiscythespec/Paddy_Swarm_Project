from __future__ import annotations

import unittest

from box_saddle_geometry import (
    build_anti_separation_lock_carrier,
    build_cbox_saddle_left,
    build_cbox_saddle_right,
    build_core_alignment_key,
)


class SaddleTests(unittest.TestCase):
    def test_cbox_first_side_and_mirror_are_keyed_final_parts(self):
        left = build_cbox_saddle_left()
        right = build_cbox_saddle_right()
        self.assertEqual(
            (round(left.BoundingBox().xlen, 5), round(left.BoundingBox().ylen, 5)),
            (round(right.BoundingBox().xlen, 5), round(right.BoundingBox().ylen, 5)),
        )
        self.assertEqual(left.design_metadata["side"], "LEFT")
        self.assertEqual(right.design_metadata["side"], "RIGHT")
        self.assertNotEqual(
            left.design_metadata["asymmetric_key"],
            right.design_metadata["asymmetric_key"],
        )
        for geometry in (left, right):
            self.assertEqual(
                geometry.design_metadata["positive_stop"],
                "INTEGRAL_FRONT_WALL",
            )
            self.assertTrue(
                geometry.design_metadata["visible_seated_indicator"]
            )
            self.assertFalse(
                geometry.design_metadata["printed_latch_primary"]
            )

    def test_core_alignment_key_rejects_reverse_insertion(self):
        geometry = build_core_alignment_key()
        self.assertEqual(
            geometry.design_metadata["reversed_insertion_rejection"],
            "OFFSET_RIGHT_KEY",
        )
        self.assertFalse(geometry.design_metadata["vertical_bbox_support"])

    def test_lock_carrier_uses_visible_metal_pin(self):
        geometry = build_anti_separation_lock_carrier()
        self.assertTrue(geometry.design_metadata["visible_lock_window"])
        self.assertEqual(
            geometry.design_metadata["primary_lock"],
            "REMOVABLE_METAL_PIN_CANDIDATE",
        )
        self.assertFalse(geometry.design_metadata["printed_latch_primary"])
        self.assertFalse(geometry.design_metadata["connector_structural_load"])


if __name__ == "__main__":
    unittest.main()
