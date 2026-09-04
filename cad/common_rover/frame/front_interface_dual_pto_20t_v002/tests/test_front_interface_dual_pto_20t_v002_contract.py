#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json,sys,unittest
from pathlib import Path
LANE=Path(__file__).resolve().parents[1];P=LANE/"build_front_interface_dual_pto_20t_v002.py";S=importlib.util.spec_from_file_location("fiv2",P);assert S and S.loader;b=importlib.util.module_from_spec(S);sys.modules[S.name]=b;S.loader.exec_module(b)
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.p=json.loads((LANE/"design_parameters.json").read_text());c.v=json.loads((LANE/"validation_report.json").read_text());c.x=json.loads((LANE/"collision_report.json").read_text())["checks"]
 def test_001_guard(self):b.guard()
 def test_002_z(self):self.assertEqual((self.p["protected_v001"]["drive_axis_z_mm"],self.p["protected_v001"]["pto_axis_z_mm"]),(122.5,122.5))
 def test_003_v001_structure(self):self.assertEqual((self.p["protected_v001"]["beam_length_mm"],self.p["protected_v001"]["kp000_total"],self.p["protected_v001"]["kp000_pair_spacing_mm"]),(400.0,4,50.0))
 def test_004_independence(self):self.assertEqual(self.p["protected_v001"]["shaft_center_gap_mm"],60.0)
 def test_005_mount(self):self.assertEqual((self.p["protected_v001"]["unit_mount_y_mm"],self.p["protected_v001"]["unit_mount_z_mm"]),([-75.0,75.0],[55.0,185.0]))
 def test_006_no_diagonal(self):self.assertEqual(self.p["protected_v001"]["diagonal_brace_count"],0)
 def test_007_frame500_hold(self):self.assertIn("DESIGN_CANDIDATE",self.p["protected_v001"]["frame_500_status"])
 def test_008_physical_source(self):self.assertEqual(self.p["pulley"]["current_pto_pulley_source"],"PHYSICAL_ENVELOPE_2026_08_30")
 def test_009_physical_dimensions(self):self.assertEqual((self.p["pulley"]["flange_od_mm"],self.p["pulley"]["tooth_region_max_od_mm"],self.p["pulley"]["toothed_body_axial_width_mm"],self.p["pulley"]["flange_thickness_each_mm"]),(34.8,30.5,19.8,1.6))
 def test_010_bore(self):self.assertEqual((self.p["pulley"]["shaft_bore_measured_mm"],self.p["pulley"]["shaft_nominal_mm"]),(9.8,10.0))
 def test_011_old_absent(self):self.assertEqual(self.p["pulley"]["old_pto_bore_6p1_interface"],"ABSENT")
 def test_012_setscrews(self):self.assertEqual((self.p["setscrew"]["count"],self.p["setscrew"]["spacing_deg"],self.p["setscrew"]["thread_standard"]),(2,90.0,"PHYSICAL_PENDING"))
 def test_013_planes(self):self.assertEqual((self.p["pulley"]["near_face_abs_y_mm"],self.p["pulley"]["center_plane_abs_y_mm"],self.p["pulley"]["far_face_abs_y_mm"]),(118.5,130.0,141.5))
 def test_014_overhang(self):self.assertEqual((self.p["pulley"]["overhang_from_outer_kp000_plane_mm"],self.p["pulley"]["housing_to_near_face_mm"]),(30.0,10.0))
 def test_015_spacer(self):self.assertEqual(json.loads((LANE/"spacer_study.json").read_text())["recommended_first_physical_candidate_mm"],0.5)
 def test_016_belt_delta(self):self.assertEqual(self.p["keepouts"]["belt_corridor_delta_mm"],[0.0,0.0,0.0,0.0])
 def test_017_unit_input(self):self.assertEqual((self.p["keepouts"]["unit_input_envelope"],self.p["keepouts"]["unit_input_center_x_mm"]),([60.0,30.0],120.0))
 def test_018_intersections(self):
  for name,row in self.x.items():self.assertEqual(row["intersection_mm3"],0.0,name)
 def test_019_validation(self):self.assertEqual((self.v["pass_count"],self.v["fail_count"]),(self.v["check_count"],0))
 def test_020_quality_manifest(self):self.assertEqual(b.verify()["path_count"],len(b.ALL_PATHS))
if __name__=="__main__":unittest.main(verbosity=2)
