from __future__ import annotations

import math
import unittest

from drive_pto_contract import (
    B10_BORE_COMPENSATION_MM,
    D6_BORE_COMPENSATION_MM,
    PITCH_MM,
    TOOTH_COMPENSATION_MM,
    belt_tooth_count,
    pitch_diameter_mm,
    require_confirmed_pto_belt,
    require_powered_approval,
)
from part_number_registry import ALL_PARTS, validate_registry


class ContractTests(unittest.TestCase):
    def test_20t_pitch_diameter(self) -> None:
        self.assertTrue(
            math.isclose(
                pitch_diameter_mm(20),
                31.830988618379067,
                abs_tol=1.0e-12,
                rel_tol=0.0,
            )
        )

    def test_60t_pitch_diameter(self) -> None:
        self.assertTrue(
            math.isclose(
                pitch_diameter_mm(60),
                95.4929658551372,
                abs_tol=1.0e-12,
                rel_tol=0.0,
            )
        )

    def test_three_to_one_ratio(self) -> None:
        self.assertEqual(60 / 20, 3.0)

    def test_450mm_is_90_teeth(self) -> None:
        self.assertEqual(belt_tooth_count(450.0, PITCH_MM), 90)

    def test_non_integer_belt_pitch_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "NOT_INTEGER_PITCH"):
            belt_tooth_count(451.0, PITCH_MM)

    def test_d6_candidate_order(self) -> None:
        self.assertEqual(tuple(sorted(D6_BORE_COMPENSATION_MM)), D6_BORE_COMPENSATION_MM)
        self.assertEqual(len(set(D6_BORE_COMPENSATION_MM)), 3)

    def test_b10_candidate_order(self) -> None:
        self.assertEqual(tuple(sorted(B10_BORE_COMPENSATION_MM)), B10_BORE_COMPENSATION_MM)
        self.assertEqual(len(set(B10_BORE_COMPENSATION_MM)), 3)

    def test_abc_tooth_compensation_unique(self) -> None:
        self.assertEqual(len(set(TOOTH_COMPENSATION_MM)), 3)

    def test_physical_part_numbers_unique(self) -> None:
        report = validate_registry()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["unique_part_number_count"], len(ALL_PARTS))

    def test_generic_unknown_pto_length_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "UNKNOWN_PTO_BELT_LENGTH"):
            require_confirmed_pto_belt("PTO-A", None, None, None)

    def test_generic_unknown_pto_path_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "GENERIC_UNKNOWN_PTO_PATH"):
            require_confirmed_pto_belt("PTO-X", 100.0, 20.0, 10.0)

    def test_powered_approval_without_coupon_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "WITHOUT_COUPON_PASS"):
            require_powered_approval(
                belt_kind="CONTINUOUS",
                coupon_result=None,
                requested_stage="POWERED_NO_LOAD",
            )

    def test_joiner_powered_approval_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "JOINER_BELT_POWERED"):
            require_powered_approval(
                belt_kind="JOINER-FIT",
                coupon_result="PASS",
                requested_stage="POWERED_NO_LOAD",
            )

    def test_powered_loaded_remains_hold(self) -> None:
        with self.assertRaisesRegex(ValueError, "POWERED_LOADED_HOLD"):
            require_powered_approval(
                belt_kind="CONTINUOUS",
                coupon_result="PASS",
                requested_stage="POWERED_LOADED",
            )


if __name__ == "__main__":
    unittest.main()
