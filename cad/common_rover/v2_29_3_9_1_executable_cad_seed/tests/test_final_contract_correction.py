from __future__ import annotations

from dataclasses import replace
import math
from pathlib import Path
import sys
import unittest


MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from authority_loader import load_authority
from solid_builders import build_minimum_assembly
from validation import IDS, build_pair_policy, validate_seed


class FinalContractCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = load_authority()

    def assert_tolerance_failure(
        self,
        field: str,
        value: float,
        blocker: str,
    ) -> None:
        candidate = replace(self.reference, **{field: value})
        report = validate_seed(candidate, self.reference)
        self.assertEqual(report["FINAL_CONTRACT_CORRECTION_STATUS"], "FAIL")
        self.assertIn(blocker, report["blockers"])

    def test_contract_01_linear_tolerance_1_9e_6_fails(self) -> None:
        self.assert_tolerance_failure(
            "linear_tolerance_mm",
            1.9e-6,
            "LINEAR_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_02_linear_tolerance_2_0e_6_fails(self) -> None:
        self.assert_tolerance_failure(
            "linear_tolerance_mm",
            2.0e-6,
            "LINEAR_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_03_volume_tolerance_1_9e_9_fails(self) -> None:
        self.assert_tolerance_failure(
            "intersection_volume_tolerance_mm3",
            1.9e-9,
            "INTERSECTION_VOLUME_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_04_volume_tolerance_2_0e_9_fails(self) -> None:
        self.assert_tolerance_failure(
            "intersection_volume_tolerance_mm3",
            2.0e-9,
            "INTERSECTION_VOLUME_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_05_linear_tolerance_nan_fails(self) -> None:
        self.assert_tolerance_failure(
            "linear_tolerance_mm",
            math.nan,
            "LINEAR_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_06_linear_tolerance_infinity_fails(self) -> None:
        self.assert_tolerance_failure(
            "linear_tolerance_mm",
            math.inf,
            "LINEAR_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_07_linear_tolerance_zero_fails(self) -> None:
        self.assert_tolerance_failure(
            "linear_tolerance_mm",
            0.0,
            "LINEAR_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_08_linear_tolerance_negative_fails(self) -> None:
        self.assert_tolerance_failure(
            "linear_tolerance_mm",
            -1.0e-6,
            "LINEAR_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_09_volume_tolerance_nan_fails(self) -> None:
        self.assert_tolerance_failure(
            "intersection_volume_tolerance_mm3",
            math.nan,
            "INTERSECTION_VOLUME_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_10_volume_tolerance_infinity_fails(self) -> None:
        self.assert_tolerance_failure(
            "intersection_volume_tolerance_mm3",
            math.inf,
            "INTERSECTION_VOLUME_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_11_volume_tolerance_zero_fails(self) -> None:
        self.assert_tolerance_failure(
            "intersection_volume_tolerance_mm3",
            0.0,
            "INTERSECTION_VOLUME_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_12_volume_tolerance_negative_fails(self) -> None:
        self.assert_tolerance_failure(
            "intersection_volume_tolerance_mm3",
            -1.0e-9,
            "INTERSECTION_VOLUME_TOLERANCE_CONTRACT_MISMATCH",
        )

    def test_contract_13_extra_seventh_solid_id_fails(self) -> None:
        solids = dict(build_minimum_assembly(self.reference))
        solids["UNAUTHORIZED-SEVENTH-SOLID"] = solids[IDS["left"]]
        report = validate_seed(
            self.reference,
            self.reference,
            solids_override=solids,
        )
        self.assertEqual(report["solid_id_set_status"], "FAIL")
        self.assertIn(
            "SOLID_ID_EXTRA:UNAUTHORIZED-SEVENTH-SOLID",
            report["blockers"],
        )

    def test_contract_14_required_solid_id_missing_fails(self) -> None:
        solids = dict(build_minimum_assembly(self.reference))
        del solids[IDS["battery"]]
        report = validate_seed(
            self.reference,
            self.reference,
            solids_override=solids,
        )
        self.assertEqual(report["solid_id_set_status"], "FAIL")
        self.assertIn(
            f"SOLID_ID_MISSING:{IDS['battery']}",
            report["blockers"],
        )

    def test_contract_15_actual_non_null_solid_count_seven_fails(self) -> None:
        solids = dict(build_minimum_assembly(self.reference))
        solids["UNAUTHORIZED-SEVENTH-SOLID"] = solids[IDS["right"]]
        report = validate_seed(
            self.reference,
            self.reference,
            solids_override=solids,
        )
        self.assertEqual(report["actual_solid_count"], 7)
        self.assertIn("ACTUAL_SOLID_COUNT_MISMATCH:7", report["blockers"])

    def test_contract_16_battery_outside_bbox_fails(self) -> None:
        battery = self.reference.component(IDS["battery"])
        battery = battery.with_bounds(
            maximum=(76.0, *battery.maximum[1:])
        )
        report = validate_seed(
            self.reference.with_component(battery),
            self.reference,
        )
        self.assertEqual(
            report["battery_bbox_containment"]["status"], "FAIL"
        )
        self.assertIn(
            "BATTERY_BBOX_CONTAINMENT_MISMATCH",
            report["blockers"],
        )

    def test_contract_17_containment_source_untraceable_fails(self) -> None:
        battery = replace(
            self.reference.component(IDS["battery"]),
            source_path="",
        )
        report = validate_seed(
            self.reference.with_component(battery),
            self.reference,
        )
        self.assertEqual(
            report["battery_bbox_containment"]["status"], "FAIL"
        )
        self.assertIn(
            "BATTERY_BBOX_CONTAINMENT_SOURCE_INVALID",
            report["blockers"],
        )

    def test_contract_18_pair_policy_count_fourteen_fails(self) -> None:
        policy = build_pair_policy()[:-1]
        report = validate_seed(
            self.reference,
            self.reference,
            pair_policy_override=policy,
        )
        self.assertEqual(report["pair_policy_count"], 14)
        self.assertIn("PAIR_POLICY_COUNT_MISMATCH:14", report["blockers"])


if __name__ == "__main__":
    unittest.main()
