#!/usr/bin/env python3
"""Contract tests for Front Interface Authority V001."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_front_interface_dual_pto_20t_v001.py"
spec = importlib.util.spec_from_file_location("front_interface_builder", BUILDER)
assert spec and spec.loader
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)


class FrontInterfaceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.p = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
        cls.v = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.c = json.loads((LANE / "collision_report.json").read_text(encoding="utf-8"))

    def test_001_repository_guard(self): b.repository_guard()
    def test_002_physical_datum(self): self.assertEqual((self.p["drive_axis"]["left_measured_z_mm"], self.p["drive_axis"]["right_measured_z_mm"], self.p["drive_axis"]["physical_nominal_z_mm"]), (122.0, 123.0, 122.5))
    def test_003_historical_values_demoted(self): self.assertEqual((self.p["drive_axis"]["historical_178_mm"], self.p["drive_axis"]["historical_175_mm"]), ("PROVISIONAL_OBSOLETE", "CAD_ONLY_NOT_PHYSICAL_AUTHORITY"))
    def test_004_pto_z_exact(self): self.assertEqual(self.p["pto"]["axis_z_difference_from_drive_mm"], 0.0)
    def test_005_independent_shafts(self): self.assertTrue(self.p["pto"]["left_right_independent"]); self.assertFalse(self.p["pto"]["continuous_cross_shaft"]); self.assertGreater(self.p["pto"]["center_gap_mm"], 0)
    def test_006_kp000_count(self): self.assertEqual((self.p["kp000"]["quantity_total"], self.p["kp000"]["quantity_per_pto"]), (4, 2))
    def test_007_kp000_physical_envelope(self): self.assertEqual(self.p["kp000"]["housing_envelope_mm"], [67.0, 17.0, 35.0]); self.assertEqual(self.p["kp000"]["mount_hole_center_mm"], 53.0)
    def test_008_kp000_spacing(self): self.assertEqual(self.p["kp000"]["pair_spacing_mm"], 50.0)
    def test_009_20t_htd5m(self): self.assertEqual((self.p["pulley"]["teeth"], self.p["pulley"]["pitch_mm"]), (20, 5.0))
    def test_010_pulley_honest_hold(self): self.assertEqual(self.p["pulley"]["status"], "PTO_20T_GEOMETRY_AUTHORITY_PENDING"); self.assertIn("6.1", self.p["pulley"]["legacy_step_bore_conflict"])
    def test_011_no_60t(self): self.assertEqual(self.p["pulley"]["old_60t_architecture"], "ABSENT"); self.assertNotIn("60T", json.dumps(self.p["keepouts"]))
    def test_012_overhang(self): self.assertEqual(self.p["pulley"]["axial_overhang_from_outer_bearing_plane_mm"], 30.0); self.assertGreaterEqual(self.p["pulley"]["housing_to_pulley_actual_gap_mm"], 5.0)
    def test_013_torque_role(self): self.assertEqual(self.p["pto"]["load_role"], "ROTATIONAL_TORQUE_ONLY")
    def test_014_unit_mount_role(self): self.assertEqual(self.p["unit_mount"]["point_count"], 4); self.assertIn("WORK_REACTION", self.p["unit_mount"]["load_role"])
    def test_015_fixed_unit_local_adjustment(self): self.assertEqual(self.p["unit_mount"]["unit_position"], "FIXED"); self.assertEqual(self.p["keepouts"]["local_adjustment_range_mm"], [10.0, 20.0])
    def test_016_keepouts(self): self.assertEqual((self.p["keepouts"]["pulley_rotation_radius_mm"], self.p["keepouts"]["belt_corridor_width_y_mm"], self.p["keepouts"]["unit_input_radius_mm"]), (22.5, 25.0, 30.0))
    def test_017_400_beam(self): self.assertEqual(self.p["beam"]["length_mm"], 400.0); self.assertIn("PHYSICAL_STOCK", self.p["beam"]["source_status"])
    def test_018_500_candidate(self): self.assertIn("DESIGN_CANDIDATE", self.p["frame_500_reference"]["status"]); self.assertEqual(self.p["frame_500_reference"]["length_each_mm"], 500.0)
    def test_019_no_diagonal(self): self.assertEqual(self.p["frame_500_reference"]["diagonal_braces"], 0)
    def test_020_shear_not_bbox(self): self.assertTrue(self.p["unit_mount"]["shear_panel_attachment_provision"]); self.assertFalse(self.p["unit_mount"]["bbox_as_structural_brace"])
    def test_021_crawler_sources(self): self.assertIn("Candidate C", self.p["crawler"]["driven"]); self.assertIn("Candidate C", self.p["crawler"]["idler"])
    def test_022_crawler_intersections(self):
        for name in ("PTO_BEAM_TO_CRAWLER", "KP000_ALL_TO_CRAWLER", "UNIT_MOUNT_TO_CRAWLER", "PTO_PULLEY_ALL_TO_CRAWLER"):
            self.assertEqual(self.c["checks"][name]["intersection_mm3"], 0.0, name)
    def test_023_mount_keepout_intersections(self):
        self.assertEqual(self.c["checks"]["UNIT_MOUNT_TO_PULLEY_KEEPOUT_ALL"]["intersection_mm3"], 0.0)
        self.assertEqual(self.c["checks"]["UNIT_MOUNT_TO_BELT_KEEPOUT_ALL"]["intersection_mm3"], 0.0)
    def test_024_named_datums(self): self.assertEqual(len(json.loads((LANE / "named_datums.json").read_text())["FRONT_INTERFACE_ORIGIN"]), 3)
    def test_025_source_audit(self): self.assertTrue(json.loads((LANE / "source_authority_audit.json").read_text())["all_pass"])
    def test_026_contract_checks(self): self.assertEqual((self.v["check_count"], self.v["pass_count"], self.v["fail_count"]), (len(self.v["checks"]), len(self.v["checks"]), 0))
    def test_027_step_reload_and_stl(self):
        result = b.verify_artifacts(); self.assertEqual(result["contract"]["count"], result["contract"]["pass"]); self.assertTrue(result["stl"]["watertight"]); self.assertEqual(result["stl"]["degenerate_triangles"], 0)
    def test_028_exact_manifest(self):
        actual = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        self.assertEqual(actual, b.ALL_PATHS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
