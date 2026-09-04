#!/usr/bin/env python3
"""Contract tests for BBOX/CBOX submerged power architecture v0.9.6.0."""
from __future__ import annotations
import json, math, sys, unittest
from pathlib import Path
sys.dont_write_bytecode=True
LANE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(LANE))
import build_bbox_cbox_submerged_power_architecture_v0960 as b

class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.report=b.verify_lane(repository=True,rebuild=False)
  cls.params=json.loads((LANE/'design_parameters.json').read_text(encoding='utf-8'))
  cls.state=json.loads((LANE/'architecture_state.json').read_text(encoding='utf-8'))
  cls.validation=json.loads((LANE/'validation_report.json').read_text(encoding='utf-8'))
 def test_001_version(self): self.assertEqual(self.params['version'],'0.9.6.0')
 def test_002_lane(self): self.assertEqual(LANE.name,'common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0')
 def test_003_classification(self): self.assertIn('EMPTY_WATERPROOF_PROTOTYPE',self.params['classification'])
 def test_004_parent(self): self.assertEqual(self.report['parent_audit'],'PASS')
 def test_005_authority(self): self.assertEqual(self.report['authority_audit'],'PASS')
 def test_006_v0953(self): self.assertTrue(self.report['repository_guard']['checks']['v0953_unchanged'])
 def test_007_manifest(self): self.assertEqual(self.report['manifest'],'PASS')
 def test_008_sha(self): self.assertEqual(self.report['sha256sums'],'PASS')
 def test_009_commit_paths(self): self.assertEqual(self.report['commit_paths'],'PASS')
 def test_010_no_cache(self): self.assertTrue(self.report['repository_guard']['checks']['cache_temp_zero'])
 def test_011_json(self): self.assertEqual(self.report['json_parse'],'PASS')
 def test_012_svg(self): self.assertEqual(self.report['svg_parse'],'PASS')
 def test_013_step(self): self.assertEqual(self.report['artifact_validation'],'PASS')
 def test_014_stl(self): self.assertEqual(self.report['artifact_validation'],'PASS')
 def test_015_battery(self): self.assertEqual(self.params['battery']['body_mm'],[150.9,99.4,92.5])
 def test_016_insertion(self): self.assertEqual(self.params['frame']['battery_insertion_height_mm'],108.0)
 def test_017_height_target(self): self.assertLessEqual(self.params['bbox']['installed_height_mm'],103.0)
 def test_018_absolute_height(self): self.assertLessEqual(self.validation['geometry']['assembly_bounds_mm'][2],108.0)
 def test_019_width(self): self.assertLessEqual(self.params['bbox']['flange_width_mm'],130.0)
 def test_020_gasket_continuous(self): self.assertEqual(self.validation['geometry']['gasket_path_solid_count'],1)
 def test_021_gasket_width(self): self.assertGreaterEqual(self.params['bbox']['seal_land_width_mm'],5.0)
 def test_022_gasket_nominal(self): self.assertEqual(self.params['bbox']['seal_land_width_mm'],6.0)
 def test_023_m4_outside(self): self.assertEqual(self.validation['geometry']['gasket_hole_common_volume_mm3'],0.0)
 def test_024_m4_count(self): self.assertEqual(self.params['bbox']['m4_count'],12)
 def test_025_lid_penetration(self): self.assertEqual(self.params['bbox']['lid_service_penetrations'],0)
 def test_026_seal_test_penetration(self): self.assertEqual(self.params['bbox']['seal_test_cable_penetrations'],0)
 def test_027_gland_land(self): self.assertEqual(self.params['bbox']['gland_land'],'BLANK / NO THROUGH-HOLE')
 def test_028_submerged_connector(self): self.assertEqual(self.params['bbox']['submerged_connector_count'],0)
 def test_029_terminal_cap(self): self.assertEqual(self.params['bbox']['external_terminal_cap_seam_count'],0)
 def test_030_integrated_flange(self): self.assertEqual(self.params['bbox']['body_to_service_ring_seam'],'ELIMINATED')
 def test_031_terminal_orientation(self): self.assertEqual(self.params['battery']['terminal_orientation'],'REARWARD / DOWNWARD')
 def test_032_battery_corridor(self): self.assertGreater(self.validation['geometry']['battery_top_throat_clearance_each_mm'],0)
 def test_033_idler(self): self.assertEqual(self.params['battery']['body_to_idler_clearance_mm_approx'],10.0)
 def test_034_powered(self): self.assertEqual(self.state['gates']['powered_drive'],'NOT_APPROVED')
 def test_035_battery_water(self): self.assertEqual(self.state['gates']['bbox_live_battery_water_test'],'NOT_APPROVED')
 def test_036_cbox_water(self): self.assertEqual(self.state['gates']['cbox_waterproof'],'NOT_TESTED')
 def test_037_hardware_cut(self): self.assertIn('HARDWARE_MASTER_DISCONNECT',self.state['power_topology'])
 def test_038_repro(self): self.assertEqual(json.loads((LANE/'reproducibility_report.json').read_text())['status'],'PASS')
 def test_039_staged_zero(self): self.assertEqual(self.report['repository_guard']['staged'],[])
 def test_040_final(self): self.assertEqual(self.report['final_status'],b.FINAL_STATUS)

if __name__=='__main__': unittest.main(verbosity=2)
