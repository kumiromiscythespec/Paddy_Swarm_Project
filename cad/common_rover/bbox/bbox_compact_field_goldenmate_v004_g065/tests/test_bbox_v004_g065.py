"""Measured geometry contracts; no authority or Git mutation."""
import importlib.util
import json
from pathlib import Path
import unittest

LANE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v004',LANE/'build_bbox_v004_g065.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=m.metrics()
        cls.quality=m.inspect(LANE)
        cls.regression=m.regression()

    def zero(self,value):self.assertLessEqual(abs(value),m.TOL)

    def test_001_repository_and_protected(self):
        s=m.audit();self.assertTrue(s['pass_result']);self.assertEqual(s['protected_source_changed_count'],0)

    def test_002_user_water_result(self):
        r=m.physical_result()
        for k in ('upright_60_min','front_tilt_gt10_deg','rear_tilt_gt10_deg','left_tilt_gt10_deg','right_tilt_gt10_deg'):self.assertEqual(r[k],'PASS')
        self.assertEqual(r['witness'],'COMPLETELY_DRY')

    def test_003_paper_tear_not_water(self):
        self.assertEqual(m.physical_result()['witness_paper_tear'],'TEST_ARTIFACT_NOT_WATER_INGRESS')

    def test_004_no_full_box_water_promotion(self):
        self.assertEqual(m.physical_result()['full_v004_waterproof'],'PHYSICAL_PENDING')

    def test_005_source_g065_actual(self):self.assertAlmostEqual(self.g['source_g065']['actual_depth_mm'],.65,places=6)

    def test_006_source_g050_actual(self):self.assertAlmostEqual(self.g['source_g050']['actual_depth_mm'],.5,places=6)

    def test_007_full_step_actual(self):self.assertAlmostEqual(self.quality['step_depth']['actual_depth_mm'],.65,places=6)

    def test_008_full_stl_actual(self):self.assertAlmostEqual(self.quality['stl_depth']['actual_depth_mm'],.65,places=6)

    def test_009_depth_delta_is_015(self):
        self.assertAlmostEqual(self.quality['step_depth']['actual_depth_mm']-self.g['source_g050']['actual_depth_mm'],.15,places=6)

    def test_010_regression_three_real_step_depths(self):
        self.assertEqual([r['requested_mm'] for r in self.regression],[.5,.55,.65])
        for r in self.regression:self.assertAlmostEqual(r['step_actual_mm'],r['requested_mm'],places=6)

    def test_011_regression_three_real_stl_depths(self):
        for r in self.regression:self.assertAlmostEqual(r['stl_actual_mm'],r['requested_mm'],places=6)

    def test_012_plus010_negative_step_rejected(self):
        for r in self.regression:self.assertTrue(r['plus_010_negative_rejected'])

    def test_013_one_continuous_groove(self):self.assertEqual(self.quality['step_depth']['floor_wires'],2)

    def test_014_width_measured_from_actual_floor_wires(self):
        b=m.importers.importStep(str(LANE/m.STEPS[0]))
        floor=next(f for f in m.d.planar_faces(b) if abs(f.Center().z-112.85)<m.TOL)
        outer=floor.outerWire().BoundingBox()
        inner=next(w for w in floor.Wires() if w.BoundingBox().xlen<outer.xlen-m.TOL).BoundingBox()
        self.assertAlmostEqual((outer.xlen-inner.xlen)/2,2.1,places=6)
        self.assertAlmostEqual((outer.ylen-inner.ylen)/2,2.1,places=6)

    def test_015_radii_measured_actual_floor(self):
        floor=next(f for f in m.d.planar_faces(m.body()) if abs(f.Center().z-112.85)<m.TOL)
        radii={round(e.radius(),6) for e in floor.Edges() if e.geomType()=='CIRCLE'}
        self.assertEqual(radii,{3.9,6.0})
        self.assertEqual({round(e.radius(),6) for e in m.centerline(0).Edges() if e.geomType()=='CIRCLE'},{4.95})

    def test_016_actual_stop_height(self):
        z=m.d.probe_surface_z(m.body(),84,45,110,115)
        self.assertAlmostEqual(z-113.5,.895,places=6)

    def test_017_straight_section_zero_diff(self):self.zero(self.g['seal_straight_section_difference_mm3'])

    def test_018_all_corner_seal_wall_zero_diff(self):
        for v in self.g['seal_corner_differences_mm3']:self.zero(v)

    def test_019_full_lid_seal_land_present(self):self.zero(self.g['lid_missing_seal_land_mm3'])

    def test_020_parent_interruption_detected(self):self.assertAlmostEqual(self.g['parent_lid_missing_seal_land_mm3'],44.1,places=6)

    def test_021_parent_groove_roof_collision_detected(self):self.assertGreater(self.g['parent_naive_g065_gasket_overlap_mm3'],18)

    def test_022_gasket_body_intersection_zero(self):self.zero(self.g['gasket_to_body_mm3'])

    def test_023_m4_gasket_intersection_zero(self):self.zero(self.g['m4_to_gasket_mm3'])

    def test_024_eight_m4_positions_unchanged(self):
        self.assertEqual(self.g['m4_count'],8)
        for x,y in m.p.M4_POINTS:
            hole=m.p.cyl_z(4.5,8.895,(x,y,105.5))
            self.zero(m.common(hole,m.body()))
            self.zero(m.common(m.p.cyl_z(4.5,8,(x,y,0)),m.lid()))

    def test_025_m4_min_gasket_clearance(self):self.assertGreaterEqual(self.g['m4_hole_to_gasket_min_mm'],1.9-m.TOL)

    def test_026_rigid_lid_closure(self):self.zero(self.g['rigid_closure_mm3'])

    def test_027_body_delta_local_only(self):
        self.zero(self.g['body_outside_groove_difference_mm3']);self.zero(self.g['body_added_volume_mm3'])
        self.assertGreater(self.g['body_removed_volume_mm3'],0)

    def test_028_lid_delta_local_only(self):
        self.zero(self.g['lid_outside_local_bridge_difference_mm3']);self.zero(self.g['lid_removed_volume_mm3'])
        self.assertAlmostEqual(self.g['lid_added_volume_mm3'],3192,places=6)

    def test_029_upper_chimney_exact_reuse(self):self.zero(self.g['chimney_above_lid_difference_mm3'])

    def test_030_bridge_within_lid_and_outside_battery_cavity(self):
        b=m.seal_land_bridge().val().BoundingBox()
        self.assertGreaterEqual(b.zmin,-m.TOL);self.assertLessEqual(b.zmax,8+m.TOL)
        self.zero(m.common(m.seal_land_bridge(),m.box(155,69,10,(0,0,4))))

    def test_031_battery_correct_axis(self):
        self.assertEqual((m.p.BATTERY['long_mm'],m.p.BATTERY['width_mm']),(150.9,65.5))
        self.assertEqual(m.p.BATTERY['terminal_inclusive_height_mm'],99.4)

    def test_032_battery_body_no_intersection(self):self.zero(self.g['battery_to_body_mm3'])

    def test_033_battery_lid_no_intersection(self):self.zero(self.g['battery_to_lid_mm3'])

    def test_034_battery_chimney_no_intersection(self):self.zero(self.g['battery_to_chimney_mm3'])

    def test_035_battery_m4_no_intersection(self):self.zero(self.g['battery_to_m4_tower_mm3'])

    def test_036_vertical_removal_clear(self):self.zero(self.g['removal_fixed_body_mm3'])

    def test_037_actual_package_and_floor_preserved(self):
        lower=m.box(200,120,105,(0,0,52.5))
        self.zero(m.delta(m.body().intersect(lower),m.d.source_body().intersect(lower)))
        self.assertEqual(self.g['internal_mm'],[155,69,110])
        self.assertAlmostEqual(m.d.probe_surface_z(m.body(),0,0,0,5),3.5,places=6)

    def test_038_battery_clearance_and_terminal_lid(self):
        self.assertEqual(self.g['battery_clearance_total_xy_mm'],[4.1,3.5])
        self.assertAlmostEqual(self.g['terminal_to_lid_mm'],10.495,places=6)

    def test_039_tpu_exact_reuse(self):
        new=m.importers.importStep(str(LANE/'artifacts/tpu_runners.step')).translate((0,0,3.5))
        old=m.importers.importStep(str(m.PARENT/'artifacts/selected_tpu_pad.step'))
        self.zero(m.delta(new,old));self.assertEqual(len(new.solids().vals()),2)

    def test_040_no_new_shell_penetrations(self):
        self.zero(self.g['body_outside_groove_difference_mm3']);self.zero(self.g['lid_removed_volume_mm3'])

    def test_041_a1_dimensions(self):
        for k in ('body_bounds_mm','lid_bounds_mm','tpu_bounds_mm'):self.assertTrue(all(0<x<=256 for x in self.g[k]))

    def test_042_primary_brep_solids(self):
        self.assertTrue(self.g['body_valid']);self.assertTrue(self.g['lid_valid'])
        for s in (m.body(),m.lid()):self.assertEqual(len(s.solids().vals()),1)

    def test_043_step_reload_all(self):
        self.assertEqual(len(self.quality['step']),13)
        for r in self.quality['step'].values():self.assertTrue(r['valid'])

    def test_044_stl_all_manifold(self):
        self.assertEqual(len(self.quality['stl']),3)
        for r in self.quality['stl'].values():self.assertTrue(r['manifold']);self.assertTrue(r['watertight']);self.assertTrue(r['pass'])

    def test_045_body_lid_brep_self_interference(self):
        for f in m.STEPS[:2]:self.assertFalse(self.quality['step'][f]['self_interference']['faulty'])

    def test_046_artifact_reproducibility(self):
        result=m.reproduce();self.assertEqual(result['count'],24);self.assertEqual(result['pass_count'],24)

    def test_047_document_reproducibility(self):
        for f,text in m.documents(self.g).items():self.assertEqual((LANE/f).read_text(encoding='utf-8'),text.rstrip()+'\n',f)

    def test_048_status_boundaries(self):
        for s in ('FULL_BODY_PRINT_READY','FULL_LID_PRINT_READY','FULL_BBOX_WATERPROOF_PHYSICAL_PENDING','GLOBAL_VEHICLE_INTEGRATION_PHYSICAL_PENDING'):self.assertIn(s,m.STATUS)

    def test_049_required_paths_unique(self):
        self.assertEqual(len(m.EXPECTED),len(set(m.EXPECTED)))
        for f in [*m.STEPS,*m.STLS,*m.SVGS,*m.DOCS]:self.assertTrue((LANE/f).is_file(),f)

    def test_050_physical_plan_safe_order(self):
        text=(LANE/'FULL_BBOX_WATER_TEST_PLAN.md').read_text()
        self.assertIn('NO battery',text);self.assertIn('60 minutes upright',text);self.assertIn('greater than 10',text)
        self.assertIn('completely dry',(LANE/'BATTERY_FIT_AND_RESTRAINT_TEST_PLAN.md').read_text())


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'count':result.testsRun,'pass':result.wasSuccessful(),'failures':len(result.failures),
        'errors':len(result.errors),'skipped':len(result.skipped),
        'test_ids':unittest.defaultTestLoader.getTestCaseNames(Contract)}
    if result.wasSuccessful():m.finalize(report)
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
