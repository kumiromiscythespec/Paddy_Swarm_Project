#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, sys, unittest
from pathlib import Path

LANE=Path(__file__).resolve().parents[1]; P=LANE/"build_pto_20t_od10_physical_envelope_v001.py"
S=importlib.util.spec_from_file_location("pto20",P); assert S and S.loader; b=importlib.util.module_from_spec(S);sys.modules[S.name]=b;S.loader.exec_module(b)

class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(c): c.m=json.loads((LANE/"physical_measurements.json").read_text()); c.v=json.loads((LANE/"validation_report.json").read_text())
 def test_001_guard(self): b.repository_guard()
 def test_002_flange(self): self.assertEqual(self.m["flange_od_mm"],34.8)
 def test_003_tooth_region(self): self.assertEqual(self.m["tooth_region_max_od_mm"],30.5)
 def test_004_widths(self): self.assertEqual((self.m["toothed_body_axial_width_mm"],self.m["flange_thickness_each_mm"],self.m["derived_overall_axial_width_mm"]),(19.8,1.6,23.0))
 def test_005_tooth_width(self): self.assertEqual(self.m["individual_tooth_width_mm"],1.5)
 def test_006_bore(self): self.assertEqual((self.m["shaft_bore_measured_mm"],self.m["shaft_nominal_mm"]),(9.8,10.0))
 def test_007_keyway(self): self.assertEqual(self.m["keyway"],"ABSENT")
 def test_008_setscrews(self): self.assertEqual((self.m["setscrew_count"],self.m["setscrew_angular_spacing_deg"],self.m["setscrew_hole_measured_approx_mm"]),(2,90.0,4.4))
 def test_009_setscrew_plane(self): self.assertEqual(self.m["setscrew_center_from_selected_end_face_mm"],15.1)
 def test_010_thread_pending(self): self.assertEqual(self.m["setscrew_thread_standard"],"PHYSICAL_PENDING")
 def test_011_static_zero(self): self.assertEqual(self.m["static_geometric_min_spacer_from_kp000_mm"],0.0)
 def test_012_old_center_absent(self): self.assertTrue(self.m["old_pto_bore_6p1_interface"].startswith("ABSENT"))
 def test_013_source(self): self.assertEqual(self.m["current_pto_pulley_source"],"PHYSICAL_ENVELOPE_2026_08_30")
 def test_014_not_exact_teeth(self): self.assertIn("NOT_EXACT",self.m["tooth_geometry_class"])
 def test_015_torque_pending(self): self.assertEqual(self.m["pto_setscrew_torque_capacity"],"PHYSICAL_VALIDATION_PENDING")
 def test_016_spacers(self): self.assertEqual([x["spacer_mm"] for x in json.loads((LANE/"spacer_study.json").read_text())["candidates"]],[0.0,0.5,1.0])
 def test_017_validation(self): self.assertEqual((self.v["pass_count"],self.v["fail_count"]),(self.v["check_count"],0))
 def test_018_steps_and_manifest(self): self.assertEqual(b.verify()["path_count"],len(b.ALL_PATHS))

if __name__=="__main__": unittest.main(verbosity=2)
