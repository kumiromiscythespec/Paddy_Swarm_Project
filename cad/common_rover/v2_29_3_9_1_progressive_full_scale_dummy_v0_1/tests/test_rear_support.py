from __future__ import annotations

import unittest

from authority_adapter import (
    rear_support_input_audit,
    validate_rear_support_audit,
)
from rear_support_model import (
    build_bbox_support_front,
    build_bbox_support_rear,
    build_rear_cradle_dummy_part_1,
    build_rear_cradle_dummy_part_2,
)


class RearSupportTests(unittest.TestCase):
    def test_audit_preserves_structural_unknowns(self):
        audit = rear_support_input_audit()
        validate_rear_support_audit(audit)
        self.assertEqual(audit["status"], "PASS_WITH_HOLD")
        self.assertEqual(len(audit["unresolved_fields"]), 6)
        self.assertFalse(audit["structural_claim"])
        self.assertFalse(audit["bbox_supported_only_by_cbox"])

    def test_front_and_rear_supports_show_independent_path(self):
        for geometry, position in (
            (build_bbox_support_front(), "FRONT"),
            (build_bbox_support_rear(), "REAR"),
        ):
            self.assertEqual(geometry.design_metadata["position"], position)
            self.assertTrue(
                geometry.design_metadata["independent_support_path_visible"]
            )
            self.assertFalse(
                geometry.design_metadata["bbox_supported_only_by_cbox"]
            )
            self.assertFalse(geometry.design_metadata["structural_claim"])
            self.assertIn(
                "NOT STRUCTURAL",
                geometry.marking.required_lines[-1],
            )

    def test_rear_cradle_halves_are_visual_only_mirrors(self):
        left = build_rear_cradle_dummy_part_1()
        right = build_rear_cradle_dummy_part_2()
        self.assertEqual(left.design_metadata["side"], "LEFT")
        self.assertEqual(right.design_metadata["side"], "RIGHT")
        self.assertEqual(
            (
                round(left.BoundingBox().xlen, 5),
                round(left.BoundingBox().ylen, 5),
                round(left.BoundingBox().zlen, 5),
            ),
            (
                round(right.BoundingBox().xlen, 5),
                round(right.BoundingBox().ylen, 5),
                round(right.BoundingBox().zlen, 5),
            ),
        )
        self.assertFalse(left.design_metadata["structural_claim"])
        self.assertFalse(right.design_metadata["structural_claim"])


if __name__ == "__main__":
    unittest.main()
