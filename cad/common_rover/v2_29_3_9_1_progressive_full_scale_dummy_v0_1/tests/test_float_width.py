from __future__ import annotations

import unittest

from float_width_audit import (
    build_float_width_audit,
    reject_unqualified_width,
)


class FloatWidthTests(unittest.TestCase):
    def test_width_categories_are_distinct(self):
        audit = build_float_width_audit()
        authority = audit["authority"]
        self.assertEqual(authority["bare_frame_width_mm"], 178.0)
        self.assertEqual(
            authority["registered_maximum_interface_width_mm"], 286.0
        )
        self.assertEqual(authority["operational_hard_limit_mm"], 300.0)
        self.assertFalse(authority["registered_is_hard_limit"])
        self.assertFalse(authority["hard_limit_is_registered_width"])

    def test_direct_side_float_is_rejected(self):
        option = build_float_width_audit()["options"]["FLOAT-1"]
        self.assertGreater(option["audited_width_mm"], 300.0)
        self.assertEqual(option["status"], "REJECT")

    def test_visual_overlap_is_selected_but_held(self):
        audit = build_float_width_audit()
        option = audit["options"]["FLOAT-2"]
        self.assertLess(option["nominal_assembled_width_mm"], 286.0)
        self.assertGreater(option["audited_width_mm"], 286.0)
        self.assertLess(option["audited_width_mm"], 300.0)
        self.assertEqual(audit["FLOAT_WIDTH_STATUS"], "HOLD")
        self.assertEqual(audit["FLOAT_FULL_SCALE_PRINT"], "HOLD")

    def test_290_nominal_without_bracket_audit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNAUDITED_290"):
            reject_unqualified_width(
                nominal_mm=290.0,
                bracket_audited=False,
            )


if __name__ == "__main__":
    unittest.main()
