#!/usr/bin/env python3
"""Contract tests for Common Rover physical follow-up measurement v0.9.5.3."""
from __future__ import annotations
import json
import math
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree

sys.dont_write_bytecode = True
LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))
import build_physical_followup_measurement_v0953 as b


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validation = b.verify_lane(repository=True, include_outside_content=False)
        cls.ledger = json.loads((LANE / "measurement_ledger.json").read_text(encoding="utf-8"))
        cls.h25 = json.loads((LANE / "h25a1_creep_measurements.json").read_text(encoding="utf-8"))
        cls.tensioner = json.loads((LANE / "drive_tensioner_measurements.json").read_text(encoding="utf-8"))

    def test_001_version(self): self.assertEqual(self.ledger["version"], "0.9.5.3")
    def test_002_lane_name(self): self.assertEqual(LANE.name, "common_rover_physical_followup_measurement_v0_9_5_3")
    def test_003_classification(self): self.assertEqual(self.ledger["classification"], "PHYSICAL_FOLLOWUP_MEASUREMENT_ONLY")
    def test_004_cad_artifact_zero(self): self.assertEqual(self.validation["cad_artifact_count"], 0)
    def test_005_parent_lanes(self): self.assertEqual(self.validation["parent_audit"], "PASS")
    def test_006_authority(self): self.assertEqual(self.validation["authority_audit"], "PASS")
    def test_007_head(self): self.assertEqual(self.validation["repository_guard"]["head"], b.EXPECTED_HEAD)
    def test_008_staged_zero(self): self.assertEqual(self.validation["repository_guard"]["staged"], [])
    def test_009_manifest_exact(self): self.assertEqual(self.validation["manifest"], "PASS")
    def test_010_sha_exact(self): self.assertEqual(self.validation["sha256sums"], "PASS")
    def test_011_commit_paths(self): self.assertEqual(self.validation["commit_paths"], "PASS")
    def test_012_json_parse(self): self.assertEqual(self.validation["json_parse"], "PASS")
    def test_013_svg_parse(self): self.assertEqual(self.validation["svg_parse"], "PASS")
    def test_014_classifications(self): self.assertTrue(all(r.get("classification") for r in self.ledger["records"]))
    def test_015_torque(self): self.assertAlmostEqual(self.h25["nominal_torque_reference"]["value_n_m"], 0.6864655, places=7)
    def test_016_not_measured_torque(self): self.assertEqual(self.h25["nominal_torque_reference"]["not_classified_as"], "PHYSICAL_MEASURED_TORQUE")
    def test_017_radius(self): self.assertAlmostEqual(self.tensioner["coordinate_reference"]["roller_radius_mm"]["value"], 12.95)
    def test_018_center_distance(self): self.assertEqual(self.tensioner["coordinate_reference"]["60t_center_mm"][0], 180.0)
    def test_019_tensioner_x(self): self.assertEqual(self.tensioner["coordinate_reference"]["tensioner_x_mm"]["value"], 71.0)
    def test_020_offset_approx(self): self.assertTrue(self.tensioner["coordinate_reference"]["tensioner_perpendicular_magnitude_mm"]["approximate"])
    def test_021_center_20(self): self.assertAlmostEqual(self.tensioner["derived_center_distances_mm"]["20t_to_tensioner"]["value"], math.hypot(71, 45))
    def test_022_center_60(self): self.assertAlmostEqual(self.tensioner["derived_center_distances_mm"]["60t_to_tensioner"]["value"], math.hypot(109, 45))
    def test_023_h25_result(self): self.assertEqual(self.h25["test"]["result"], "PHYSICAL_PASS_USER_REPORTED")
    def test_024_112_not_pass(self): self.assertIn("CONDITIONAL_FAIL_TOOTH_LIFT", (LANE / "DRIVE_112T_560_PHYSICAL_TEST.md").read_text(encoding="utf-8"))
    def test_025_113_pending(self): self.assertIn("NOT_TESTED_IN_THIS_LANE", (LANE / "DRIVE_BELT_TEST_MATRIX.md").read_text(encoding="utf-8"))
    def test_026_powered_not_approved(self): self.assertIn("POWERED_ROTATION | NOT_APPROVED", (LANE / "DESIGN_GATE_STATUS.md").read_text(encoding="utf-8"))
    def test_027_field_not_approved(self): self.assertIn("FIELD_DEPLOYMENT | NOT_APPROVED", (LANE / "DESIGN_GATE_STATUS.md").read_text(encoding="utf-8"))
    def test_028_no_forbidden_extensions(self): self.assertFalse(any(p.suffix.lower() in b.FORBIDDEN_EXTENSIONS for p in LANE.rglob("*") if p.is_file()))
    def test_029_no_cache(self): self.assertFalse(any(p.name in {"__pycache__", ".pytest_cache"} for p in LANE.rglob("*")))
    def test_030_final_status(self): self.assertEqual(self.validation["final_status"], b.FINAL_STATUS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
