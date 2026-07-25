from __future__ import annotations

import unittest

from dummy_component_registry import COMPONENTS, validate_component_registry
from part_number_registry import (
    GLOBAL_PART_NUMBER_RATIFICATION,
    PARTS,
    PART_NUMBER_PATTERN,
    validate_registry,
)


class PartNumberTests(unittest.TestCase):
    def test_all_parts_have_unique_repository_format_numbers(self):
        report = validate_registry()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["physically_marked_part_count"], 19)
        self.assertEqual(report["unique_part_number_count"], 19)
        self.assertEqual(len({part.filename for part in PARTS}), 19)
        self.assertTrue(
            all(PART_NUMBER_PATTERN.fullmatch(part.part_number) for part in PARTS)
        )

    def test_revision_orientation_interface_and_safety_are_marked(self):
        for part in PARTS:
            self.assertIn("R00", part.part_number)
            self.assertTrue(part.orientation_marking)
            self.assertTrue(part.interface_id)
            self.assertIn("NO LOAD", part.classification_marking)
            self.assertNotIn("BUILD-PLATE", part.marking_surface.upper())
            self.assertNotIn("SLIDING SURFACE", part.marking_surface.upper())

    def test_lane_local_serial_ratification_hold_is_explicit(self):
        self.assertEqual(GLOBAL_PART_NUMBER_RATIFICATION, "HOLD")

    def test_component_registry_matches_part_registry(self):
        report = validate_component_registry()
        self.assertEqual(report["component_count"], len(PARTS))
        self.assertEqual({item.key for item in COMPONENTS}, {p.key for p in PARTS})
        self.assertEqual(report["direct_rail_holes"], 0)


if __name__ == "__main__":
    unittest.main()
