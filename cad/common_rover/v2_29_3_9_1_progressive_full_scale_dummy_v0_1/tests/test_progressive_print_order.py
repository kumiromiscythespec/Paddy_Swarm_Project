from __future__ import annotations

import unittest

from part_number_registry import PARTS
from progressive_print_plan import (
    MIRROR_GATE_PAIRS,
    PRINT_STEPS,
    progressive_print_markdown,
    quality_gate_rows,
    validate_print_order,
)


class ProgressivePrintOrderTests(unittest.TestCase):
    def test_every_step_is_one_final_use_part(self):
        report = validate_print_order()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["print_count"], len(PARTS))
        self.assertFalse(report["standalone_coupon_required"])
        self.assertFalse(report["all_parts_one_plate_recommended"])
        self.assertTrue(all(step.quantity == 1 for step in PRINT_STEPS))

    def test_mirror_parts_follow_first_side_pass_gate(self):
        positions = {
            step.part_key: index for index, step in enumerate(PRINT_STEPS)
        }
        for first, mirror in MIRROR_GATE_PAIRS:
            self.assertLess(positions[first], positions[mirror])
            mirror_step = PRINT_STEPS[positions[mirror]]
            self.assertIn(f"{first} PASS P0-P4", mirror_step.prerequisite)

    def test_all_five_gates_exist_for_every_part(self):
        rows = quality_gate_rows()
        self.assertEqual(len(rows), len(PARTS) * 5)
        for part in PARTS:
            gates = {
                row["gate"]
                for row in rows
                if row["part_number"] == part.part_number
            }
            self.assertEqual(gates, {"P0", "P1", "P2", "P3", "P4"})

    def test_markdown_forbids_one_plate(self):
        text = progressive_print_markdown()
        self.assertIn("Never place the complete kit on one print plate.", text)
        self.assertIn("PASS P0-P4", text)


if __name__ == "__main__":
    unittest.main()
