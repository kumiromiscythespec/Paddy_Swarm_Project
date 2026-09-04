#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys,unittest
from pathlib import Path
LANE=Path(__file__).resolve().parents[1]; ROOT=Path(r"D:\Paddy_Swarm_Project"); sys.path.insert(0,str(LANE))
import build_common_rover_190mm_integration_v0941 as B
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(c): c.d=json.loads((LANE/"dimensions.json").read_text(encoding="utf-8")); c.i=json.loads((LANE/"interfaces.json").read_text(encoding="utf-8")); c.g=json.loads((LANE/"geometry_manifest.json").read_text(encoding="utf-8")); c.v=json.loads((LANE/"validation_report.json").read_text(encoding="utf-8"))
 def test_001_package(self): self.assertEqual(B.verify_files()["status"],"CAD_PASS")
 def test_002_old_frame(self): self.assertEqual((self.d["old_frame"]["upper_outer_x"],self.d["old_frame"]["upper_outer_y"],self.d["old_frame"]["lower_outer_x"],self.d["old_frame"]["lower_outer_y"],self.d["old_frame"]["height"]),(540.0,181.0,442.0,181.0,150.0))
 def test_003_new_frame(self): self.assertEqual((self.d["new_frame"]["height"],self.d["new_frame"]["vertical_2020"],self.d["new_frame"]["increment"]),(190.0,150.0,40.0))
 def test_004_xy_unchanged(self): self.assertEqual({k:self.d["old_frame"][k] for k in ("upper_outer_x","upper_outer_y","lower_outer_x","lower_outer_y")},{k:self.d["new_frame"][k] for k in ("upper_outer_x","upper_outer_y","lower_outer_x","lower_outer_y")})
 def test_005_internal_z(self): self.assertEqual((self.d["old_frame"]["internal_effective_z"],self.d["new_frame"]["internal_effective_z"]),(90.7,130.7))
 def test_006_z_conflict(self): self.assertEqual(self.d["z_datum"]["new_top_range"],[252.0,258.0]); self.assertEqual(self.d["z_datum"]["absolute_new_top"],"HOLD")
 def test_007_waterline(self): self.assertEqual(self.d["z_datum"]["waterline"],150.0)
 def test_008_diagonal(self): self.assertAlmostEqual(self.d["diagonal"]["concept_center_distance"],213.784938665,places=6); self.assertIsNone(self.d["diagonal"]["final_cut_length"])
 def test_009_pto(self): self.assertEqual((self.i["pto"]["driver_teeth"],self.i["pto"]["driven_teeth"],self.i["pto"]["ratio"]),(20,20,1.0))
 def test_010_kp000(self): self.assertEqual((self.d["kp000"]["mount_hole_center"],self.d["kp000"]["total"]),(53.0,12))
 def test_011_bearing(self): self.assertEqual((self.d["bearing_6000"]["od"],self.d["bearing_6000"]["seat"],self.d["bearing_6000"]["central_clearance"]),(25.9,26.0,12.0))
 def test_012_collar(self): self.assertEqual((self.d["collar"]["od"],self.d["collar"]["id"],self.d["collar"]["width"]),(15.9,10.1,3.0))
 def test_013_two_screws(self): self.assertEqual((self.d["set_screws"]["nominal"],self.d["set_screws"]["quantity"],self.d["set_screws"]["angle"],self.d["set_screws"]["length"],self.d["set_screws"]["projection"]),("M4",2,90.0,4.0,1.0))
 def test_014_protected_12t(self): self.assertAlmostEqual(self.g["h25a1_2s"]["external_12t_volume_delta"],0,places=6); self.assertEqual(self.g["h25a1_2s"]["body_solid_count"],1); self.assertFalse(self.g["h25a1_2s"]["radial_tooth_root_access"])
 def test_015_battery(self): self.assertEqual((self.d["battery"]["x"],self.d["battery"]["y"],self.d["battery"]["body_z"],self.d["battery"]["mass_kg"]),(150.9,99.4,92.5,1.2))
 def test_016_bbox_contract(self): self.assertEqual(self.d["bbox"]["removal_axis"],"-X"); self.assertFalse(self.d["bbox"]["normal_swap_lid_open"] or self.d["bbox"]["blind_mate"] or self.d["bbox"]["idler_support"])
 def test_017_x_serial(self): self.assertTrue(self.d["layout"]["x_serial"]); self.assertFalse(self.d["layout"]["vertical_stacking"]); self.assertEqual(self.d["layout"]["selected"],"LAYOUT_A_BBOX_REAR_CBOX_FRONT")
 def test_018_top_reserved(self): self.assertEqual(self.v["checks"]["DRIVETRAIN_CLEARANCE"],"HOLD_EXACT_TRANSFORMS")
 def test_019_fail_closed(self): self.assertFalse(self.v["powered_rotation_approved"] or self.v["field_deployment_approved"] or self.v["physical_pass"])
 def test_020_parent(self):
  if B.PARENT.exists(): self.assertEqual(B.parent_audit()["status"],"CAD_PASS")
 def test_021_authority(self):
  if (ROOT/".git").exists(): self.assertEqual(B.authority_audit()["status"],"CAD_PASS")
 def test_022_staged_zero(self):
  if (ROOT/".git").exists(): self.assertEqual(subprocess.check_output(["git","diff","--cached","--name-only"],cwd=ROOT,text=True).strip(),"")
 def test_023_commit_paths(self): self.assertEqual((LANE/"COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines(),[f"{B.LANE_REL}/{p}" for p in B.PACKAGE_PATHS])
 def test_024_standalone_rebuild(self): self.assertEqual(B.standalone_rebuild()["status"],"CAD_PASS")
if __name__=="__main__": unittest.main(verbosity=2)
