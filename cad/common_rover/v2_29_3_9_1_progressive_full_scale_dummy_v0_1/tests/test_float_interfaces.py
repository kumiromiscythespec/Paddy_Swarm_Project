from __future__ import annotations

import unittest

from float_interface_geometry import (
    build_float_slide_receiver_left,
    build_float_slide_receiver_right,
    build_lower_float_adapter_left,
    build_lower_float_adapter_right,
    build_pin_retainer_cover,
)


class FloatInterfaceTests(unittest.TestCase):
    def test_lower_adapters_stay_on_bottom_slot(self):
        left = build_lower_float_adapter_left()
        right = build_lower_float_adapter_right()
        for geometry, side in ((left, "LEFT"), (right, "RIGHT")):
            self.assertEqual(geometry.design_metadata["side"], side)
            self.assertEqual(geometry.design_metadata["host_slot"], "BOTTOM_SLOT")
            self.assertEqual(
                geometry.design_metadata["authority_zone_interval_y_mm"],
                [-125, -95],
            )
            self.assertFalse(geometry.design_metadata["direct_rail_holes"])
            self.assertFalse(
                geometry.design_metadata["inferred_supplier_slot_geometry"]
            )
        self.assertEqual(
            (round(left.BoundingBox().xlen, 5), round(left.BoundingBox().ylen, 5)),
            (round(right.BoundingBox().xlen, 5), round(right.BoundingBox().ylen, 5)),
        )

    def test_receivers_have_stops_pin_windows_and_side_keys(self):
        left = build_float_slide_receiver_left()
        right = build_float_slide_receiver_right()
        for geometry, side in ((left, "LEFT"), (right, "RIGHT")):
            self.assertEqual(geometry.design_metadata["side"], side)
            self.assertEqual(
                geometry.design_metadata["positive_stop"],
                "INTEGRAL_REAR_STOP",
            )
            self.assertTrue(geometry.design_metadata["pin_alignment_window"])
            self.assertIn(
                side,
                geometry.design_metadata["reversed_insertion_rejection"],
            )
            self.assertIn("OPEN_TOP", geometry.design_metadata["glove_access"])
            self.assertFalse(geometry.design_metadata["structural_claim"])

    def test_retainer_cover_is_secondary_only(self):
        geometry = build_pin_retainer_cover()
        self.assertEqual(geometry.design_metadata["classification"], "SECONDARY_ONLY")
        self.assertFalse(geometry.design_metadata["primary_lock"])
        self.assertFalse(geometry.design_metadata["thumb_latch_primary"])
        self.assertTrue(
            geometry.design_metadata["primary_metal_pin_remains_visible"]
        )


if __name__ == "__main__":
    unittest.main()
