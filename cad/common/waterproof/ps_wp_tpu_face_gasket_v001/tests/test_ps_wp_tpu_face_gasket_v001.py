"""Common-interface actual geometry and physical-status contracts."""
import importlib.util
import json
import math
from pathlib import Path
import unittest

LANE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pswp',LANE/'build_ps_wp_tpu_face_gasket_v001.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=m.geometry_metrics();cls.q=m.inspect(LANE);cls.reg=m.regression()

    def zero(self,x):self.assertLessEqual(abs(x),m.TOL)

    def test_001_repository_and_protected(self):
        a=m.audit();self.assertTrue(a['pass']);self.assertEqual(a['protected_source_changed_count'],0)

    def test_002_common_lane_only(self):
        self.assertEqual(m.REL,'cad/common/waterproof/ps_wp_tpu_face_gasket_v001')
        self.assertFalse(m.parameters(self.g)['metrics']['round_cord_geometry_dependency'])

    def test_003_round_cord_history_separate(self):
        h=m.parameters(self.g)['history']
        self.assertEqual(h['round_cord_small_dummy'],'PASS');self.assertEqual(h['round_cord_full_bbox_long_duration'],'FAIL')
        self.assertEqual(h['failure_mode'],'UNRESOLVED_SLOW_INGRESS')

    def test_004_old_diameter_not_current_tpu(self):
        h=m.parameters(self.g)['history'];self.assertEqual(h['old_rubber_nominal_diameter_mm'],3)
        self.assertEqual(h['old_rubber_light_caliper_approx_mm'],3.4)
        self.assertIn('NOT_CURRENT_PHYSICAL_AUTHORITY',h['old_1p8_label'])

    def test_005_no_invented_material(self):
        a=m.material_audit();self.assertEqual(a['product'],'PHYSICAL_PENDING');self.assertEqual(a['shore_hardness'],'PHYSICAL_PENDING')
        self.assertEqual(a['specimen'],'CURRENT_TPU_SPECIMEN')

    def test_006_g20_actual_step_stl(self):
        for q in self.q['actual_gaskets']['G20'].values():self.assertAlmostEqual(q['thickness_mm'],2,places=6)

    def test_007_g25_actual_step_stl(self):
        for q in self.q['actual_gaskets']['G25'].values():self.assertAlmostEqual(q['thickness_mm'],2.5,places=6)

    def test_008_g30_actual_step_stl(self):
        for q in self.q['actual_gaskets']['G30'].values():self.assertAlmostEqual(q['thickness_mm'],3,places=6)

    def test_009_all_actual_seal_widths(self):
        for g in self.q['actual_gaskets'].values():
            for q in g.values():self.assertAlmostEqual(q['width_mm'],5,places=6)

    def test_010_same_active_xy(self):
        for t in m.GASKETS.values():
            s=m.gasket(t).intersect(m.ring(5,t))
            self.assertAlmostEqual(m.bbox(s)[0],63,places=6);self.assertAlmostEqual(m.bbox(s)[1],63,places=6)
            self.zero(m.delta(s,m.ring(5,t)))

    def test_011_one_intended_gasket_solid(self):
        for t in m.GASKETS.values():self.assertEqual(len(m.gasket(t).solids().vals()),1)

    def test_012_active_band_continuous_annular_top_face(self):
        for t in m.GASKETS.values():
            faces=[f for f in m.gasket(t).faces().vals() if f.geomType()=='PLANE' and abs(f.Center().z-t)<m.TOL and f.normalAt().z>.99]
            self.assertEqual(len(faces),1);self.assertEqual(len(faces[0].Wires()),2)
            self.assertAlmostEqual(faces[0].Area(),self.g['gasket_centerline_perimeter_mm']*5,places=5)

    def test_013_gasket_corner_radii_actual(self):
        sh=m.importers.importStep(str(LANE/'artifacts/ps_wp_tpu_gasket_g25.step'))
        f=next(f for f in sh.faces().vals() if f.geomType()=='PLANE' and abs(f.Center().z-2.5)<m.TOL)
        radii={round(e.radius(),6) for e in f.Edges() if e.geomType()=='CIRCLE'}
        self.assertEqual(radii,{4.,9.});self.assertEqual((min(radii)+max(radii))/2,6.5)

    def test_014_no_joint_or_active_band_holes(self):
        for t in m.GASKETS.values():self.zero(m.volume(m.ring(5,t).cut(m.gasket(t))))
        self.assertEqual(m.parameters(self.g)['contract']['gasket_joint_count'],0)

    def test_015_no_narrow_body_groove(self):self.zero(self.g['seal_land_missing_body_mm3'])

    def test_016_flat_lid_land(self):self.zero(self.g['seal_land_missing_lid_mm3'])

    def test_017_actual_broad_seal_land(self):
        self.zero(m.volume(m.ring(10,.1,m.RIM-.1).cut(m.body())))
        self.assertGreaterEqual(self.g['seal_land_width_mm'],5.5)

    def test_018_four_corner_body_lid_solid(self):
        self.assertEqual(len(m.body().solids().vals()),1);self.assertEqual(len(m.lid().solids().vals()),1)
        self.assertTrue(m.body().val().isValid());self.assertTrue(m.lid().val().isValid())

    def test_019_body_wall_floor_package(self):
        cavity=m.body().intersect(m.box(40,40,30,(0,0,15)))
        self.assertAlmostEqual(m.bbox(cavity)[2],3.5,places=6)
        self.assertEqual(self.g['internal_cavity_mm'],[48,48,25])
        self.assertAlmostEqual(m.bbox(m.body())[2],28.5,places=6)

    def test_020_lid_thickness_and_stiffness_basis(self):
        self.assertEqual(m.bbox(m.lid())[2],6)
        rows=self.g['lid_stiffness_geometric_comparison']
        self.assertAlmostEqual(rows[-1]['section_I_mm4']/rows[0]['section_I_mm4'],3.375,places=6)

    def test_021_dry_closed_volume(self):
        self.assertGreaterEqual(self.g['dry_internal_volume_ml'],50);self.assertLessEqual(self.g['dry_internal_volume_ml'],100)

    def test_022_no_intentional_pressure_penetrations(self):
        for h in m.STOPS.values():self.assertGreater(m.dry_volume(h),50)
        self.assertEqual(self.g['external_penetration_count'],0)

    def test_023_m4_outside_active_seal(self):self.zero(self.g['m4_active_seal_intersection_mm3'])

    def test_024_stop_outside_active_seal(self):self.zero(self.g['stop_active_seal_intersection_mm3'])

    def test_025_m4_layout_and_actual_holes(self):
        self.assertEqual(len(m.M4),4)
        for xy in m.M4:
            self.zero(m.common(m.cyl(4.5,8,xy,m.RIM-8),m.body()))
            self.zero(m.common(m.cyl(4.5,6,xy,0),m.lid()))

    def test_026_two_and_four_locator_trade(self):
        for r in self.g['locators'].values():self.assertEqual(r['solids'],1);self.assertTrue(r['valid']);self.zero(r['active_band_difference_mm3'])
        self.assertIn('SELECTED_ROUND',self.g['locators']['TWO_POINT']['selection'])

    def test_027_locator_holes_outside_seal(self):
        for i,xy in enumerate(m.LOCATORS):self.zero(m.common(m.locator_hole(xy,i==1),m.ring(5,3)))

    def test_028_ears_register_without_stop_interference(self):
        self.zero(self.g['locating_stop_intersection_mm3']);self.assertAlmostEqual(self.g['locator_radial_clearance_mm'],.3,places=6)

    def test_029_tabs_not_in_compression_stack(self):
        self.zero(self.g['tab_lid_intersection_at_min_stop_mm3'])
        for t in m.GASKETS.values():
            ears=m.gasket(t).cut(m.ring(5,t))
            self.assertAlmostEqual(m.bbox(ears)[2],.8,places=6)
            self.zero(m.common(ears,m.lid().translate((0,0,1.6))))

    def test_030_rigid_closure_clear(self):self.zero(self.g['rigid_body_lid_intersection_mm3'])

    def test_031_s16_actual(self):self.check_stop('S16',1.6)
    def test_032_s18_actual(self):self.check_stop('S18',1.8)
    def test_033_s20_actual(self):self.check_stop('S20',2.0)
    def test_034_s22_actual(self):self.check_stop('S22',2.2)
    def test_035_s24_actual(self):self.check_stop('S24',2.4)

    def check_stop(self,name,h):
        r=self.q['actual_stops'][name]
        for actual in r['step_thicknesses_mm']:self.assertAlmostEqual(actual,h,places=6)
        self.assertAlmostEqual(r['stl_thickness_mm'],h,places=6)
        for b in self.q['stl'][f'artifacts/stop_{name.lower()}.stl']['component_bounds_mm']:self.assertAlmostEqual(b[2],h,places=6)

    def test_036_stop_working_faces_flat(self):
        for h in m.STOPS.values():
            s=m.stop(h);faces=[f for f in s.faces().vals() if f.geomType()=='PLANE']
            self.assertEqual(len(faces),2)
            for f in faces:self.assertAlmostEqual(f.Area(),math.pi*(4**2-2.25**2),places=6)

    def test_037_actual_primary_assembly_gap(self):self.assertAlmostEqual(self.q['actual_primary_assembly_gap_mm'],2,places=6)

    def test_038_gap_interchangeability(self):
        stops=[r for r in self.reg if r['part'].startswith('S')]
        self.assertEqual(len(stops),5)
        for r in stops:self.assertAlmostEqual(r['assembly_gap_mm'],r['requested_mm'],places=6)

    def test_039_no_integral_gap_stop(self):
        self.assertAlmostEqual(m.bounds(m.body())[5],m.RIM,places=6)
        self.zero(m.common(m.body(),m.lid().translate((0,0,m.RIM))))

    def test_040_body_lid_one_file_each(self):
        self.assertEqual(len([f for f in m.STLS if f.endswith('_body.stl')]),1)
        self.assertEqual(len([f for f in m.STLS if f.endswith('_lid.stl')]),1)
        self.assertFalse(m.parameters(self.g)['contract']['body_reprint_required_for_gasket_change'])

    def test_041_all_eight_positive_actual_regressions(self):
        self.assertEqual(len(self.reg),8)
        self.assertEqual({r['part'] for r in self.reg},set(m.GASKETS)|set(m.STOPS))

    def test_042_all_eight_plus010_rejected(self):
        for r in self.reg:self.assertTrue(r['plus010_rejected'])

    def test_043_nominal_primary_ratio_not_physical(self):
        row=next(r for r in self.g['compression_matrix'] if r['test_role']=='PRIMARY')
        self.assertAlmostEqual(row['nominal_ratio'],.2,places=6)
        self.assertEqual(row['classification'],'NOMINAL_DESIGN_REFERENCE')

    def test_044_full_positional_clearance_stack(self):
        self.assertAlmostEqual(m.POSITION_ALLOWANCE,(4.5-4)/2+(4.5-4)/2+(8.6-8)/2,places=6)

    def test_045_planned_lateral_support(self):
        self.assertEqual(len(self.g['planned_configuration_land_support']),5)
        for r in self.g['planned_configuration_land_support']:self.zero(r['max_unsupported_volume_mm3'])

    def test_046_extreme_combo_not_silently_approved(self):
        r=next(r for r in self.g['compression_matrix'] if r['gasket']=='G30' and r['stop']=='S16')
        self.assertLess(r['land_margin_after_080_position_error_mm'],0);self.assertEqual(r['warning'],'UNSUPPORTED_EXTREME_NOT_APPROVED')

    def test_047_measured_compression_range_synthetic(self):
        r=m.measured_compression([2.45,2.55,2.5,2.5,2.5,2.5,2.5,2.5],[1.99,2.01,2,2],[1.98,2.02,2,2])
        self.assertAlmostEqual(r['compression_min'],1-2.02/2.45,places=9)
        self.assertAlmostEqual(r['compression_nominal_estimate'],.2,places=9)
        self.assertAlmostEqual(r['compression_max'],1-1.98/2.55,places=9)
        self.assertFalse(r['automatic_water_promotion'])

    def test_048_missing_actual_gap_rejected(self):
        with self.assertRaises(ValueError):m.measured_compression([2.5]*8,[2]*4,[None]*4)

    def test_049_invalid_measurements_rejected(self):
        for bad in (0,-1,float('nan'),float('inf'),True):
            with self.assertRaises(ValueError):m.measured_compression([bad]+[2.5]*7,[2]*4,[2]*4)

    def test_050_physical_template_stays_blank(self):
        t=m.physical_template();self.assertEqual(t['T1_T8_free_thickness_mm'],[None]*8)
        self.assertEqual(t['G1_G4_measured_closed_gap_mm'],[None]*4);self.assertIsNone(t['actual_compression'])

    def test_051_eight_witness_zones_fit(self):
        self.assertEqual(len(m.witness().solids().vals()),8);self.zero(self.g['witness_body_intersection_mm3'])
        self.assertEqual(set(m.WITNESS),{'FRONT','REAR','LEFT','RIGHT','CORNER1','CORNER2','CORNER3','CORNER4'})

    def test_052_calibration_actual_three_heights(self):
        s=m.importers.importStep(str(LANE/'artifacts/ps_wp_tpu_thickness_calibration_coupon.step'))
        self.assertEqual(sorted(m.measure_thickness(s)),[2,2.5,3])

    def test_053_step_reload_all(self):
        self.assertEqual(len(self.q['step']),14)
        for r in self.q['step'].values():self.assertTrue(r['valid'])

    def test_054_stl_all_quality(self):
        self.assertEqual(len(self.q['stl']),11)
        for r in self.q['stl'].values():self.assertTrue(r['watertight']);self.assertTrue(r['manifold']);self.assertTrue(r['pass'])

    def test_055_stl_single_gasket_connectivity(self):
        for g in m.GASKETS:self.assertEqual(self.q['stl'][f'artifacts/ps_wp_tpu_gasket_{g.lower()}.stl']['connected_components'],1)

    def test_056_stl_four_stops_each(self):
        for s in m.STOPS:self.assertEqual(self.q['stl'][f'artifacts/stop_{s.lower()}.stl']['connected_components'],4)

    def test_057_brep_self_intersections(self):
        for r in self.q['step'].values():
            if 'self_interference' in r:self.assertFalse(r['self_interference']['faulty'])

    def test_058_a1_all_print_parts_fit(self):
        for f in m.PARTS:self.assertTrue(all(0<d<=256 for d in self.q['step'][f'artifacts/{f}.step']['bounds_mm']))

    def test_059_artifact_reproducibility(self):
        r=m.reproduce();self.assertEqual(r['count'],33);self.assertEqual(r['pass_count'],33)

    def test_060_document_reproducibility(self):
        for f,text in m.documents(self.g).items():self.assertEqual((LANE/f).read_text(encoding='utf-8'),text.rstrip()+'\n',f)

    def test_061_exact_inventory_unique(self):
        self.assertEqual(len(m.EXPECTED),55);self.assertEqual(len(m.EXPECTED),len(set(m.EXPECTED)))
        for f in [*m.STEPS,*m.STLS,*m.SVGS,*m.DOCS]:self.assertTrue((LANE/f).is_file(),f)

    def test_062_dry_before_water_protocol(self):
        t=(LANE/'WATER_TEST_PLAN.md').read_text(encoding='utf-8');self.assertIn('Only after DRY_MECHANICAL_PASS',t)
        self.assertIn('DO NOT OPEN',t);self.assertIn('no battery',t)

    def test_063_water_stage_duration_and_fields(self):
        t=(LANE/'WATER_TEST_PLAN.md').read_text(encoding='utf-8')
        self.assertIn('cumulative60 minutes',t);self.assertEqual(t.count('greater than10 degrees for10 minutes'),4)
        self.assertIn('first wet zone',t)

    def test_064_no_water_or_vehicle_promotion(self):
        self.assertIn('WATER_PHYSICAL_TEST_PENDING',m.STATUS);self.assertIn('BBOX_V005_PENDING',m.STATUS);self.assertIn('CBOX_FIELD_BOX_PENDING',m.STATUS)
        self.assertEqual(m.physical_template()['promotion'],'WATER_PHYSICAL_TEST_PENDING')

    def test_065_preview_axes_match_labels(self):
        for projection in ((0,0,1),(0,-1,0),(0,-1,1),(0,-1,.35)):
            direction=m.preview_frame(projection).toLocalCoords(m.cq.Vector(1,0,0))
            self.assertAlmostEqual(direction.x,1,places=6);self.zero(direction.y)
        for projection in ((0,-1,0),(1,0,0)):
            direction=m.preview_frame(projection).toLocalCoords(m.cq.Vector(0,0,1))
            self.assertAlmostEqual(direction.y,1,places=6);self.zero(direction.x)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
    report={'count':result.testsRun,'pass':result.wasSuccessful(),'failures':len(result.failures),'errors':len(result.errors),
        'skipped':len(result.skipped),'test_ids':unittest.defaultTestLoader.getTestCaseNames(Contract)}
    if result.wasSuccessful():m.finalize(report)
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
