"""Actual generated geometry and no-false-physical-authority contracts."""
import importlib.util
import json
from pathlib import Path
import unittest

LANE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pto_gauge',LANE/'build_pto_offset_spacer_test_v001.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=m.inspect(LANE);cls.g=m.geometry_metrics();cls.s=m.source_audit();cls.rows=m.candidate_records()
  cls.reg=m.regression()

 def zero(self,v):self.assertLessEqual(abs(v),m.TOL)

 def test_001_repository_protected(self):
  a=m.audit();self.assertTrue(a['pass']);self.assertEqual(a['protected_source_changed_count'],0)
  self.assertEqual(a['outside_untracked_count'],4355);self.assertEqual(a['staged_count'],0)

 def test_002_new_lane_only(self):
  self.assertEqual(m.LANE,m.ROOT/m.REL);self.assertEqual(len(m.EXPECTED),51)

 def test_003_interface_not_invented(self):
  self.assertFalse(self.s['interface_proven']);self.assertEqual(self.s['second_mounting_face'],'PHYSICAL_IDENTIFICATION_PENDING')

 def test_004_non_load_gauge(self):
  self.assertEqual(self.s['structural_load_authority'],'NOT_APPROVED')
  self.assertEqual(m.parameters()['part_class'],'NON_LOAD_BEARING_PLACEMENT_GAUGE')

 def test_005_l_bracket_rejected(self):
  self.assertEqual(self.s['front_l_bracket'],'REJECTED_FOR_CURRENT_PHYSICAL_ASSEMBLY')
  self.assertEqual(self.g['l_bracket_count'],0);self.assertEqual(self.g['triangular_joint_count'],0)

 def test_006_end_face_local_datum(self):
  r=m.cq.importers.importStep(str(LANE/'artifacts/current_frame_end_reference.step'))
  self.zero(m.bounds(r)[3]);self.assertEqual(m.size(r),[500,20,40])
  self.assertIn('NOT_PHYSICAL_AUTHORITY',self.s['frame_length_status'])
  self.assertFalse(m.parameters()['global_vehicle_x_used'])

 def test_007_kp_physical_exact(self):
  self.assertEqual(self.s['kp000']['physical_span_mm'],66.1)
  r=m.cq.importers.importStep(str(LANE/'artifacts/kp000_physical_reference.step'))
  self.assertAlmostEqual(m.size(r)[0],66.1,places=6)

 def test_008_kp_cad_discrepancy(self):
  r=m.cq.importers.importStep(str(LANE/'artifacts/kp000_existing_cad_reference.step'))
  self.assertAlmostEqual(m.size(r)[0],67,places=6)
  self.assertAlmostEqual(self.s['kp000']['cad_minus_physical_mm'],.9,places=6)

 def test_009_60t_physical_exact(self):
  r=m.cq.importers.importStep(str(LANE/'artifacts/60t_physical_envelope_reference.step'))
  self.assertAlmostEqual(m.size(r)[0],100.1,places=6);self.assertEqual(self.s['60t']['physical_max_mm'],100.1)

 def test_010_60t_cad_discrepancy(self):
  r=m.cq.importers.importStep(str(LANE/'artifacts/60t_existing_cad_reference.step'))
  self.assertAlmostEqual(m.size(r)[0],102,places=6);self.assertAlmostEqual(self.s['60t']['cad_minus_physical_mm'],1.9,places=6)

 def test_011_no_complete_sweep_claim(self):
  self.assertIn('NOT_PROVEN',self.s['60t']['installed_exact_source_identity'])
  self.assertIn('CAD_REFERENCE_ONLY',self.s['60t']['envelope'])

 def test_012_exact_derived_overhang(self):
  self.assertEqual(m.OVERHANG,17);self.assertEqual((100.1-66.1)/2,17)

 def test_013_no_fabricated_20t_od(self):
  self.assertIsNone(self.s['20t']['new_exact_od_inferred_from_observation'])
  self.assertFalse(self.s['20t']['interference_dominant'])
  self.assertAlmostEqual(self.s['20t']['cad_flange_actual_mm'],34.8,places=6)

 def test_014_old_axial_shim_distinct(self):
  self.assertEqual(self.s['old_shim']['thicknesses_mm'],[.5,1.0])
  self.assertEqual(self.s['old_shim']['cross_section_mm'],[10.2,13.8])
  self.assertIn('NOT evidence',self.s['old_shim']['function'])

 def test_015_p20_actual_step_stl(self):self.length('P20',20)
 def test_016_p22_actual_step_stl(self):self.length('P22',22)
 def test_017_p25_actual_step_stl(self):self.length('P25',25)

 def length(self,n,v):
  r=self.q['actual_working_dimensions'][n]
  self.assertAlmostEqual(r['length_mm'],v,places=6);self.assertAlmostEqual(r['stl_working_length_mm'],v,places=6)
  self.assertEqual(r['face_areas_mm2'],[144,144]);self.assertEqual(r['face_x_mm'],[0,v])

 def test_018_p20_residual_not_physical(self):self.residual('P20',3)
 def test_019_p22_residual_not_physical(self):self.residual('P22',5)
 def test_020_p25_residual_not_physical(self):self.residual('P25',8)

 def residual(self,n,v):
  row=next(r for r in self.rows if r['id']==n)
  self.assertEqual(row['nominal_residual_mm'],v);self.assertIn('NOT_PHYSICAL',row['residual_class'])
  self.assertNotIn('PASS',row['residual_class'])

 def test_021_all_required_installed_checks_present(self):
  for r in self.rows:self.assertEqual(set(r['interference_pairs']),set(m.PAIRS))

 def test_022_missing_registration_not_zero(self):
  for r in self.rows:
   self.assertIsNone(r['minimum_installed_static_clearance_mm'])
   for q in r['interference_pairs'].values():
    self.assertIsNone(q['intersection_mm3']);self.assertIsNone(q['minimum_mm']);self.assertIn('HOLD',q['status'])

 def test_023_axis_not_derived_from_gauge(self):
  for r in self.rows:self.assertIsNone(r['pto_axis_local_x_mm']);self.assertTrue(r['axis_status'].startswith('N/A'))

 def test_024_clutch_unknown_not_solid(self):
  self.assertEqual(self.g['clutch_solid_count'],0);self.assertFalse(self.s['slide_clutch']['solid_created'])
  self.assertFalse(any('clutch' in f for f in m.STEPS))

 def test_025_corridor_absolute_unknown(self):
  for r in self.rows:self.assertIsNone(r['available_clutch_corridor_mm']);self.assertIn('ONLY IF',r['corridor_condition'])

 def test_026_corridor_relative_conditional(self):
  self.assertEqual([r['conditional_corridor_change_vs_p20_mm'] for r in self.rows],[0,-2,-5])

 def test_027_tools_and_service_not_falsely_approved(self):
  for r in self.rows:
   self.assertEqual(set(r['tool_and_service']),set(m.ACCESS))
   self.assertTrue(all(v.startswith('HOLD') for v in r['tool_and_service'].values()))

 def test_028_no_shaft_or_mounting_bores(self):
  self.assertEqual(self.g['gauge_shaft_hole_count'],0);self.assertEqual(self.g['gauge_mounting_hole_count'],0)
  for v in m.CANDIDATES.values():self.assertAlmostEqual(m.common(m.gauge(v),m.box(1,1,1,(v/2,0,4))),1,places=6)

 def test_029_three_different_clear_labels(self):
  self.assertEqual(set(m.SEGMENTS),{'0','2','5'})
  for v in m.CANDIDATES.values():
   removed=m.box(v,18,8,(v/2,0,4)).cut(m.gauge(v));b=m.bounds(removed)
   self.assertGreater(m.volume(removed),20);self.assertGreaterEqual(b[0],4.5)
   self.assertLessEqual(b[3],v-4.5);self.assertGreaterEqual(b[2],7.4-1e-6)

 def test_030_measurement_patches_intact(self):
  for v in m.CANDIDATES.values():
   for x in (.05,v-.05):
    p=m.box(.1,10,4,(x,0,4));self.zero(m.volume(p.cut(m.gauge(v))))

 def test_031_broad_parallel_end_faces(self):
  for v in m.CANDIDATES.values():self.assertEqual(m.actual_working_length(m.gauge(v))['face_areas_mm2'],[144,144])

 def test_032_reference_source_shape_reuse(self):
  for n in m.SOURCE_STEP:
   imported=m.cq.importers.importStep(str(LANE/('artifacts/'+n+'.step')))
   src=m.source_shape(n)
   for a,b in zip(m.size(imported),m.size(src)):self.assertAlmostEqual(a,b,places=5)
   self.assertAlmostEqual(m.volume(imported),m.volume(src),delta=.001)
   self.assertEqual(len(imported.solids().vals()),len(src.solids().vals()))

 def test_033_local_frame_gauge_demo_only(self):
  for r in self.g['gauges'].values():
   self.zero(r['bench_frame_gauge_overlap_mm3']);self.zero(r['bench_frame_gauge_distance_mm'])
   self.assertIn('NOT_INSTALLATION',r['bench_contact_status'])

 def test_034_all_step_reload(self):
  self.assertEqual(len(self.q['step']),15)
  for r in self.q['step'].values():self.assertEqual(r['reload'],'PASS')

 def test_035_all_stl_topology(self):
  self.assertEqual(len(self.q['stl']),4)
  for r in self.q['stl'].values():
   self.assertTrue(r['pass']);self.assertTrue(r['watertight']);self.assertTrue(r['manifold'])
   for k in ('bad_edges','bad_vertex_links','degenerate_triangles','duplicate_triangles'):self.assertEqual(r[k],0)

 def test_036_individual_single_solid(self):
  for v in m.CANDIDATES.values():self.assertEqual(self.q['stl'][f'artifacts/pto_offset_spacer_{int(v)}.stl']['connected_components'],1)

 def test_037_triplet_separable(self):
  q=self.q['stl']['artifacts/pto_offset_gauge_triplet.stl'];self.assertEqual(q['connected_components'],3)
  self.assertEqual(sorted(b[0] for b in q['component_bounds_mm']),[20,22,25])

 def test_038_self_intersections_zero(self):
  for n in m.PRINTS:self.assertEqual(self.q['step']['artifacts/'+n+'.step']['self_intersections'],0)

 def test_039_exact_bounds_bed_fit(self):
  for v in m.CANDIDATES.values():self.assertEqual(self.q['step'][f'artifacts/pto_offset_spacer_{int(v)}.step']['bounds_mm'],[v,18,8])
  for n in m.PRINTS:self.assertTrue(all(0<d<256 for d in self.q['step']['artifacts/'+n+'.step']['bounds_mm']))

 def test_040_support_free_flat_base(self):
  for v in m.CANDIDATES.values():
   bottom=[f for f in m.gauge(v).faces().vals() if f.geomType()=='PLANE' and f.normalAt().z<-.999 and abs(f.Center().z)<m.TOL]
   self.assertEqual(len(bottom),1);self.assertAlmostEqual(bottom[0].Area(),v*18,places=6)
  self.assertEqual(self.g['material'],'PETG');self.assertEqual(self.g['support'],'OFF')

 def test_041_actual_regression_three_positive(self):
  self.assertEqual(len(self.reg),3)
  for r in self.reg:self.assertAlmostEqual(r['actual_mm'],r['requested_mm'],places=6)

 def test_042_all_plus010_regressions_rejected(self):
  for r in self.reg:self.assertTrue(r['plus010_rejected'])

 def test_043_arbitrary_size_not_released(self):
  for v in (0,19,20.1,30):
   with self.assertRaises(ValueError):m.gauge(v)

 def test_044_reproducibility_geometry_svg(self):
  r=m.reproduce();self.assertEqual(r['count'],28);self.assertEqual(r['pass_count'],28)

 def test_045_reproducibility_documents_bytes(self):
  self.assertEqual(len(m.documents()),10)
  for n,s in m.documents().items():self.assertEqual((LANE/n).read_bytes(),s.encode('utf-8'))

 def test_046_no_filled_physical_measurements(self):
  r=m.physical_template();self.assertIsNone(r['selected_shortest_candidate'])
  for row in r['candidates'].values():
   self.assertIsNone(row['printed_actual_length_mm']);self.assertIsNone(row['minimum_full_rotation_clearance_mm'])

 def test_047_no_automatic_winner(self):
  self.assertIsNone(m.parameters()['final_selected_length_mm'])
  for row in self.rows:self.assertEqual(row['physical_selection'],'PHYSICAL_TEST_PENDING')

 def test_048_remove_gauges_before_rotation(self):
  p=m.documents()['PHYSICAL_TEST_PLAN.md'];self.assertIn('REMOVE ALL',p)
  self.assertIn('GAUGES',p);self.assertIn('at least one complete revolution',p)
  self.assertIn('Do not use the gauge to carry',p);self.assertIn('Power disconnected',p)

 def test_049_reference_board_labeling(self):
  text=m.documents()['REFERENCE_ASSEMBLY_LIMITS.md']
  self.assertIn('exploded component boards',text);self.assertIn('NOT physical measurements',text)
  self.assertIn('no false zero clearances',json.loads((LANE/'collision_report.json').read_text())['scope'])

 def test_050_no_old_shaft_architecture_change(self):
  self.assertEqual(self.s['shaft_key']['drive_path'],'SHAFT_KEY_MISUMI_GROOVE1_CANDIDATE_C_UNCHANGED')
  self.assertFalse(self.s['shaft_key']['new_key_or_bore_geometry_created'])
  self.assertEqual(self.s['shaft_key']['cut_length'],'HOLD_NOT_RELEASED')

 def test_051_exact_paths_and_no_cache(self):
  files=[p.relative_to(LANE).as_posix() for p in LANE.rglob('*') if p.is_file()]
  self.assertTrue(set(files)<=set(m.EXPECTED));self.assertFalse(any('__pycache__' in p or p.endswith('.pyc') for p in files))
  self.assertEqual(len(m.EXPECTED),len(set(m.EXPECTED)))

 def test_052_status_scope(self):
  self.assertIn('PLACEMENT_GAUGE_PRINT_READY',m.STATUS);self.assertIn('STRUCTURAL_SPACER_INTERFACE_PENDING',m.STATUS)
  self.assertIn('PHYSICAL_CLEARANCE_TEST_PENDING',m.STATUS);self.assertIn('SLIDE_CLUTCH_FINAL_ENVELOPE_PENDING',m.STATUS)
  self.assertNotIn('STRUCTURAL_SPACER_PRINT_READY',m.STATUS)


if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
 report={'count':result.testsRun,'pass':result.wasSuccessful(),'failures':len(result.failures),'errors':len(result.errors),
  'skipped':len(result.skipped),'test_ids':unittest.defaultTestLoader.getTestCaseNames(Contract)}
 if result.wasSuccessful():m.finalize(report)
 print(json.dumps(report,indent=2))
 raise SystemExit(0 if result.wasSuccessful() else 1)
