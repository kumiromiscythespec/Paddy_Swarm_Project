from __future__ import annotations

import json
import math
from pathlib import Path
import sys
import unittest


MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from authority_loader import find_repository_root, load_authority
from inspectors import inspect_pair
from solid_builders import build_minimum_assembly
from validation import IDS, canonical_report_json, validate_seed


class _IntersectionResult:
    def __init__(self, volume: float) -> None:
        self._volume = volume

    def Volume(self) -> float:
        return self._volume


class _BooleanShape:
    def __init__(
        self,
        *,
        volume: float = 0.0,
        error_type: type[Exception] | None = None,
    ) -> None:
        self._volume = volume
        self._error_type = error_type

    def intersect(self, other):
        if self._error_type is not None:
            raise self._error_type(
                "environment-dependent message C:\\temporary\\must-not-leak.step"
            )
        return _IntersectionResult(self._volume)


class FailClosedCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reference = load_authority()
        cls.left = cls.reference.component(IDS["left"])
        cls.cross = cls.reference.component(IDS["cross"])
        registry_path = (
            find_repository_root()
            / "rovers/common_rover/v2.29.3.9.1/hardware_envelope_registry.json"
        )
        cls.hardware_records = json.loads(registry_path.read_text(encoding="utf-8"))

    def inspect_fake_boolean(
        self,
        first_shape,
        *,
        volume_tolerance_mm3: float | None = None,
    ) -> dict:
        return inspect_pair(
            self.left,
            self.cross,
            first_shape,
            object(),
            self.reference.linear_tolerance_mm,
            (
                self.reference.intersection_volume_tolerance_mm3
                if volume_tolerance_mm3 is None
                else volume_tolerance_mm3
            ),
            "FACE_CONTACT",
        )

    def assert_boolean_failure(self, row: dict, error_type: str) -> None:
        blocker = (
            f"INTERSECTION_BOOLEAN_FAILED:{IDS['left']}:{IDS['cross']}"
        )
        self.assertEqual(row["status"], "FAIL")
        self.assertEqual(row["intersection_operation_status"], "FAIL")
        self.assertEqual(row["intersection_error_type"], error_type)
        self.assertIsNone(row["actual_intersection_volume_mm3"])
        self.assertIn(blocker, row["blockers"])
        rendered = canonical_report_json(row)
        self.assertNotIn("temporary", rendered)
        self.assertNotIn("must-not-leak", rendered)

    def test_fail_closed_01_runtime_error_from_intersect(self) -> None:
        row = self.inspect_fake_boolean(
            _BooleanShape(error_type=RuntimeError)
        )
        self.assert_boolean_failure(row, "RuntimeError")

    def test_fail_closed_02_value_error_from_intersect(self) -> None:
        row = self.inspect_fake_boolean(_BooleanShape(error_type=ValueError))
        self.assert_boolean_failure(row, "ValueError")

    def test_fail_closed_03_nan_intersection_volume(self) -> None:
        row = self.inspect_fake_boolean(_BooleanShape(volume=math.nan))
        self.assert_boolean_failure(row, "NONFINITE_INTERSECTION_VOLUME")

    def test_fail_closed_04_infinite_intersection_volume(self) -> None:
        row = self.inspect_fake_boolean(_BooleanShape(volume=math.inf))
        self.assert_boolean_failure(row, "NONFINITE_INTERSECTION_VOLUME")

    def test_fail_closed_05_negative_intersection_volume(self) -> None:
        row = self.inspect_fake_boolean(_BooleanShape(volume=-1.0))
        blocker = (
            f"INTERSECTION_BOOLEAN_FAILED:{IDS['left']}:{IDS['cross']}"
        )
        self.assertEqual(row["status"], "FAIL")
        self.assertEqual(
            row["intersection_error_type"], "NEGATIVE_INTERSECTION_VOLUME"
        )
        self.assertEqual(row["actual_intersection_volume_mm3"], -1.0)
        self.assertIn(blocker, row["blockers"])

    def test_fail_closed_06_missing_shape_is_structured_failure(self) -> None:
        solids = dict(build_minimum_assembly(self.reference))
        solids[IDS["left"]] = None
        report = validate_seed(
            self.reference,
            self.reference,
            solids_override=solids,
        )
        left_row = next(
            row
            for row in report["solid_validation"]
            if row["component_id"] == IDS["left"]
        )
        self.assertEqual(report["EXECUTABLE_CAD_SEED_STATUS"], "FAIL")
        self.assertEqual(left_row["blockers"], ["OBJECT_MISSING"])
        self.assertIsNone(left_row["bounding_box_mm"])
        self.assertIsNone(left_row["volume_mm3"])

    def test_fail_closed_07_non_cadquery_object_is_structured_failure(self) -> None:
        solids = dict(build_minimum_assembly(self.reference))
        solids[IDS["left"]] = object()
        report = validate_seed(
            self.reference,
            self.reference,
            solids_override=solids,
        )
        left_row = next(
            row
            for row in report["solid_validation"]
            if row["component_id"] == IDS["left"]
        )
        self.assertEqual(report["EXECUTABLE_CAD_SEED_STATUS"], "FAIL")
        self.assertEqual(left_row["blockers"], ["NOT_CADQUERY_OCP_SHAPE"])
        self.assertIsNone(left_row["solid_count"])

    def test_fail_closed_08_duplicate_battery_authority_record(self) -> None:
        battery = next(
            record
            for record in self.hardware_records
            if record.get("canonical_component_id") == IDS["battery"]
        )
        records = [*self.hardware_records, dict(battery)]
        report = validate_seed(authority_hardware_records=records)
        blocker = (
            "AUTHORITY_COMPONENT_RECORD_COUNT_MISMATCH:"
            f"{IDS['battery']}:2"
        )
        self.assertEqual(report["EXECUTABLE_CAD_SEED_STATUS"], "FAIL")
        self.assertIn(blocker, report["blockers"])
        self.assertEqual(
            report["battery_cassette"]["placement_status"], "HOLD"
        )

    def test_fail_closed_09_missing_battery_authority_record(self) -> None:
        records = [
            record
            for record in self.hardware_records
            if record.get("canonical_component_id") != IDS["battery"]
        ]
        report = validate_seed(authority_hardware_records=records)
        blocker = (
            "AUTHORITY_COMPONENT_RECORD_COUNT_MISMATCH:"
            f"{IDS['battery']}:0"
        )
        self.assertEqual(report["EXECUTABLE_CAD_SEED_STATUS"], "FAIL")
        self.assertIn(blocker, report["blockers"])
        self.assertEqual(
            report["battery_cassette"]["placement_status"], "HOLD"
        )

    def test_fail_closed_10_duplicate_rail_authority_record(self) -> None:
        left = next(
            record
            for record in self.hardware_records
            if record.get("canonical_component_id") == IDS["left"]
        )
        report = validate_seed(
            authority_hardware_records=[*self.hardware_records, dict(left)]
        )
        blocker = (
            "AUTHORITY_COMPONENT_RECORD_COUNT_MISMATCH:"
            f"{IDS['left']}:2"
        )
        self.assertEqual(report["EXECUTABLE_CAD_SEED_STATUS"], "FAIL")
        self.assertIn(blocker, report["blockers"])

    def test_fail_closed_11_volume_at_tolerance_boundary_passes(self) -> None:
        tolerance = self.reference.intersection_volume_tolerance_mm3
        row = self.inspect_fake_boolean(
            _BooleanShape(volume=tolerance),
            volume_tolerance_mm3=tolerance,
        )
        self.assertEqual(row["intersection_operation_status"], "PASS")
        self.assertEqual(row["status"], "PASS")
        self.assertFalse(row["unintended_volumetric_intersection"])

    def test_fail_closed_12_volume_above_tolerance_boundary_fails(self) -> None:
        tolerance = self.reference.intersection_volume_tolerance_mm3
        row = self.inspect_fake_boolean(
            _BooleanShape(volume=math.nextafter(tolerance, math.inf)),
            volume_tolerance_mm3=tolerance,
        )
        blocker = (
            "UNINTENDED_VOLUMETRIC_INTERSECTION:"
            f"{IDS['left']}:{IDS['cross']}"
        )
        self.assertEqual(row["intersection_operation_status"], "PASS")
        self.assertEqual(row["status"], "FAIL")
        self.assertTrue(row["unintended_volumetric_intersection"])
        self.assertIn(blocker, row["blockers"])

    def test_fail_closed_13_step_roundtrip_validates_source_and_volume(self) -> None:
        report = validate_seed(
            self.reference,
            self.reference,
            include_step_roundtrip=True,
        )
        step = report["temporary_step_roundtrip"]
        self.assertEqual(step["status"], "PASS")
        self.assertTrue(step["source_valid"])
        self.assertTrue(step["roundtrip_valid"])
        self.assertGreater(step["source_volume_mm3"], 0.0)
        self.assertGreater(step["roundtrip_volume_mm3"], 0.0)
        self.assertLessEqual(
            step["volume_difference_mm3"],
            step["volume_tolerance_mm3"],
        )
        self.assertEqual(step["bounding_box_mismatch_fields"], [])
        self.assertTrue(step["temporary_step_deleted"])


if __name__ == "__main__":
    unittest.main()
