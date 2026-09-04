#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys,unittest
from pathlib import Path
LANE=Path(__file__).resolve().parents[1];ROOT=Path(r"D:\Paddy_Swarm_Project");sys.path.insert(0,str(LANE))
import build_common_rover_physical_fit_closure_v0942 as B
class T(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.d=json.loads((LANE/"dimensions.json").read_text());c.m=json.loads((LANE/"measurement_ledger.json").read_text());c.g=json.loads((LANE/"geometry_manifest.json").read_text());c.v=json.loads((LANE/"validation_report.json").read_text())
 def test_001_package(self):self.assertEqual(B.verify_files()["status"],"CAD_PASS")
 def test_002_frame_outer(self):self.assertEqual((self.d["frame"]["upper_outer_x"],self.d["frame"]["upper_outer_y"],self.d["frame"]["lower_outer_x"],self.d["frame"]["lower_outer_y"]),(540.,181.,442.,181.))
 def test_003_frame_clear(self):self.assertEqual((self.d["frame"]["upper_clear_x"],self.d["frame"]["upper_clear_y"],self.d["frame"]["lower_clear_x"],self.d["frame"]["lower_clear_y"]),(500.,100.,400.,140.))
 def test_004_frame_height(self):self.assertEqual((self.d["frame"]["structural_height"],self.d["frame"]["vertical_2020"]),(150.,110.))
 def test_005_datums(self):self.assertEqual((self.d["z_record"]["previous_internal_z"],self.d["z_record"]["previous_internal_z_classification"],self.d["z_record"]["battery_insertion_clear_height"]),(90.7,"VALID_MEASUREMENT_DIFFERENT_DATUM",108.))
 def test_006_battery(self):self.assertEqual((self.d["battery"]["x"],self.d["battery"]["y"],self.d["battery"]["z"],self.d["battery"]["mass_kg"]),(150.9,99.4,92.5,1.2))
 def test_007_terminal_pass(self):self.assertEqual(self.d["battery"]["with_terminals_in_108_passage"],"PHYSICAL_PASS_USER_REPORTED")
 def test_008_dummy(self):self.assertEqual((self.d["bbox_dummy"]["x"],self.d["bbox_dummy"]["y"],self.d["bbox_dummy"]["z"]),(180.,114.,103.))
 def test_009_shims(self):self.assertEqual((self.d["bbox_dummy"]["shims"],self.d["bbox_dummy"]["test_heights"],self.d["bbox_dummy"]["nominal_clearances"]),([2.,4.],[103.,105.,107.],[5.,3.,1.]))
 def test_010_dummy_bounds(self):self.assertEqual(self.g["dummy_bounds"],{"x":180.,"y":114.,"z":103.})
 def test_010b_printability(self):self.assertEqual(self.g["coupon_bounds"],{"collar":[72,28,6.6],"reaction":[72,28,6.6]});self.assertTrue(self.g["printability"]["all_designated_print_files_fit"]);self.assertEqual(self.g["printability"]["monolithic_dummy_stl"],"REFERENCE_ONLY")
 def test_011_collar(self):self.assertEqual((self.d["collar"]["od"],self.d["collar"]["id"],self.d["collar"]["width"],self.d["collar"]["pockets"]),(15.9,10.1,3.,[16.,16.1,16.2]))
 def test_012_screws(self):self.assertEqual((self.d["set_screws"]["nominal"],self.d["set_screws"]["quantity"],self.d["set_screws"]["angle"],self.d["set_screws"]["length"],self.d["set_screws"]["projection"]),("M4",2,90.,4.,1.))
 def test_013_reaction(self):self.assertEqual((self.d["reaction"]["slots"],self.d["set_screws"]["radial_keepout"]),([4.1,4.2,4.3],8.95))
 def test_014_protected(self):self.assertEqual(self.d["protected_sprocket"]["external_difference"],0.);self.assertFalse(self.g["h25a1"]["radial_tooth_root_hole"])
 def test_015_bearing(self):self.assertEqual((self.d["bearing"]["od"],self.d["bearing"]["seat"],self.d["bearing"]["central_clearance"]),(25.9,26.,12.))
 def test_016_kp000(self):self.assertEqual(self.d["kp000"]["mount_hole_center"],53.)
 def test_017_release(self):self.assertFalse(self.v["powered_rotation_approved"] or self.v["field_approved"])
 def test_018_gate(self):self.assertEqual(self.v["checks"]["BBOX_103_DUMMY"],"PRINT_READY_CANDIDATE");self.assertEqual(self.v["checks"]["BBOX_103_PHYSICAL_FIT"],"PENDING_USER_TEST")
 def test_019_parents(self):
  if B.P1.exists():self.assertEqual(B.audit_dir(B.P1,68,B.P1_HASHES)["status"],"CAD_PASS");self.assertEqual(B.audit_dir(B.P0,43,B.P0_HASHES)["status"],"CAD_PASS")
 def test_020_authority(self):
  if (ROOT/".git").exists():self.assertEqual(B.authority_audit()["status"],"CAD_PASS")
 def test_021_staged(self):
  if (ROOT/".git").exists():self.assertEqual(subprocess.check_output(["git","diff","--cached","--name-only"],cwd=ROOT,text=True).strip(),"")
 def test_022_commit_paths(self):self.assertEqual((LANE/"COMMIT_PATHS.txt").read_text().splitlines(),[f"{B.LANE_REL}/{p}" for p in B.PACKAGE_PATHS])
 def test_023_standalone(self):self.assertEqual(B.standalone_rebuild()["status"],"CAD_PASS")
if __name__=="__main__":unittest.main(verbosity=2)
