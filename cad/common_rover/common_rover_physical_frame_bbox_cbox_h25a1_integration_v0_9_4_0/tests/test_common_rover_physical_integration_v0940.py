#!/usr/bin/env python3
"""Contract tests for v0.9.4.0 physical integration reference."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
ROOT = Path(r"D:\Paddy_Swarm_Project")
sys.path.insert(0, str(LANE))
import build_common_rover_physical_integration_v0940 as B


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = json.loads((LANE/"geometry_manifest.json").read_text(encoding="utf-8"))
        cls.v = json.loads((LANE/"validation_report.json").read_text(encoding="utf-8"))

    def test_001_package_and_hash_contract(self): self.assertEqual(B.verify_files()["status"], "CAD_PASS")
    def test_002_frame_outer(self):
        self.assertAlmostEqual(self.g["frame"]["upper_outer_x"],540,delta=1); self.assertAlmostEqual(self.g["frame"]["upper_outer_y"],181,delta=1)
        self.assertAlmostEqual(self.g["frame"]["lower_outer_x"],442,delta=1); self.assertAlmostEqual(self.g["frame"]["lower_outer_y"],181,delta=1)
    def test_003_frame_clear_and_height(self):
        self.assertAlmostEqual(self.g["frame"]["upper_clear_x"],500,delta=1); self.assertAlmostEqual(self.g["frame"]["upper_clear_y"],100,delta=1)
        self.assertAlmostEqual(self.g["frame"]["lower_clear_x"],400,delta=1); self.assertAlmostEqual(self.g["frame"]["lower_clear_y"],140,delta=1); self.assertAlmostEqual(self.g["frame"]["height"],150,delta=1)
    def test_004_z_datums(self): self.assertEqual((self.g["frame"]["bottom_z"],self.g["frame"]["top_z"],self.g["frame"]["waterline_z"]),(68.0,218.0,150.0))
    def test_004b_frame_cad_bounds(self):
        b=self.g["frame_cad_bounds"]; self.assertAlmostEqual(b["x"],540,delta=1); self.assertAlmostEqual(b["y"],181,delta=1); self.assertAlmostEqual(b["z"],150,delta=1); self.assertAlmostEqual(b["zmin"],68,delta=.01); self.assertAlmostEqual(b["zmax"],218,delta=.01)
    def test_005_pto_ratio(self): self.assertEqual((self.g["pto"]["driver_teeth"],self.g["pto"]["driven_teeth"],self.g["pto"]["ratio"]),(20,20,1.0))
    def test_006_bearing_update(self): self.assertEqual(self.g["crawler"]["bearing"],{"od_measured":25.9,"seat_trial":26.0,"central_clearance":12.0})
    def test_007_collar(self): self.assertEqual(self.g["h25a1"]["collar"],{"od":15.9,"bore":10.1,"width":3.0,"apparent_threaded_hole":3.7})
    def test_008_protected_12t(self):
        s=self.g["h25a1"]["external_12t"]; self.assertEqual((s["tooth_count"],s["phase"],s["tip_radius"],s["root_radius"],s["axial_width"]),(12,15.0,33.07,29.47,44.0)); self.assertAlmostEqual(self.g["h25a1"]["outer_volume_delta_mm3"],0,places=6)
    def test_009_no_radial_access(self): self.assertFalse(self.g["h25a1"]["radial_tooth_root_access_hole"])
    def test_010_box_contracts(self):
        self.assertEqual(self.g["boxes"]["bbox"]["axis"],"X"); self.assertFalse(self.g["boxes"]["bbox"]["normal_swap_lid_open"]); self.assertFalse(self.g["boxes"]["bbox"]["blind_mate"]); self.assertIn("INDEPENDENT",self.g["boxes"]["cbox"]["architecture"])
    def test_011_release_fail_closed(self): self.assertFalse(self.v["powered_rotation_approved"] or self.v["field_deployment_approved"] or self.v["physical_pass"])
    def test_012_missing_measurements_not_zeroed(self):
        for name in ("BATTERY_X","BATTERY_Y","BATTERY_Z","BATTERY_MASS","VERTICAL_INTERNAL_CLEARANCE","COLLAR_THREAD_NOMINAL","SET_SCREW_PROJECTION","PTO_TRANSFORM"): self.assertIn(name,self.v["missing_measurements"])
    def test_013_authority_unchanged(self):
        for rel,digest in B.AUTHORITY_HASHES.items(): self.assertEqual(B.sha(ROOT/rel),digest)
    def test_014_git_staged_zero(self): self.assertEqual(subprocess.check_output(["git","diff","--cached","--name-only"],cwd=ROOT,text=True).strip(),"")
    def test_015_commit_paths_exact(self): self.assertEqual((LANE/"COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines(),[f"{B.LANE_REL}/{p}" for p in B.PACKAGE_PATHS])
    def test_016_standalone_cad_rebuild(self): self.assertEqual(B.standalone_rebuild()["status"],"CAD_PASS")


if __name__ == "__main__": unittest.main(verbosity=2)
