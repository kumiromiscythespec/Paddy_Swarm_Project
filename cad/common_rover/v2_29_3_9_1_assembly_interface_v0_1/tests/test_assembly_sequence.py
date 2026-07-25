from __future__ import annotations

import unittest

from assembly_sequence import (
    BATTERY_SEQUENCE,
    battery_reservation,
    build_assembly_steps,
    build_disassembly_steps,
)


class AssemblySequenceTests(unittest.TestCase):
    def test_sequence_is_twelve_ordered_steps(self):
        steps = build_assembly_steps()
        self.assertEqual(12, len(steps))
        self.assertEqual(list(range(1, 13)), [row["step"] for row in steps])

    def test_operations_are_explicit_and_ordered(self):
        actions = [row["action"] for row in build_assembly_steps()]
        positions = {
            name: next(index for index, value in enumerate(actions) if name in value)
            for name in ("INSERT", "SLIDE", "LOCK", "VERIFY")
        }
        self.assertLess(positions["INSERT"], positions["SLIDE"])
        self.assertLess(positions["SLIDE"], positions["LOCK"])
        self.assertLess(positions["LOCK"], positions["VERIFY"])

    def test_disassembly_reverses_assembly(self):
        assembly = build_assembly_steps()
        disassembly = build_disassembly_steps()
        self.assertEqual(12, len(disassembly))
        for row, source in zip(disassembly, reversed(assembly)):
            self.assertIn(f"step {source['step']}", row["action"])

    def test_battery_sequence_is_exact_and_nonstructural(self):
        reservation = battery_reservation()
        self.assertEqual(BATTERY_SEQUENCE, tuple(reservation["sequence"]))
        self.assertFalse(reservation["connector_structural_load"])
        self.assertFalse(reservation["manufacturing_geometry"])
        self.assertIsNone(reservation["selected_shuttle"])
