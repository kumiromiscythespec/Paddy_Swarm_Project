"""Regression suite queries reloaded STEP geometry, including the former +0.10 error."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

LANE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('water_dummy',LANE/'build_water_dummy.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class WaterDummyContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models={v:b.importers.importStep(str(LANE/f'artifacts/water_dummy_{v.lower()}_body.step')) for v in b.VARIANTS}
        cls.lid=b.importers.importStep(str(LANE/'artifacts/water_dummy_common_lid.step'))
        cls.metrics=b.metrics()

    def test_01_source_coupon_a_actual_g055(self):self.assertAlmostEqual(b.source_coupon_depth('A'),.55,places=6)
    def test_02_source_coupon_b_actual_g065(self):self.assertAlmostEqual(b.source_coupon_depth('B'),.65,places=6)
    def test_03_source_full_body_still_g050(self):
        sh=b.source_body();rim=b.probe_surface_z(sh,40,39,110,114);bottom=b.probe_surface_z(sh,40,35.95,110,114)
        self.assertAlmostEqual(rim-bottom,.5,places=6)
    def test_04_exported_g055_depth(self):b.assert_depth(self.models['G055'],.55)
    def test_05_exported_g065_depth(self):b.assert_depth(self.models['G065'],.65)
    def test_06_old_centered_tool_error_rejected_after_step_reload(self):
        requested=.55
        # Old formula: requested+.2 cutter centered at rim-requested/2.
        old_bottom=b.RIM-requested-.1
        bad=b.body(requested).cut(b.ring(b.OUTER,b.GROOVE_INNER,requested+.2,old_bottom))
        with tempfile.TemporaryDirectory(prefix='paddy_negative_depth_') as td:
            path=Path(td)/'old_depth_bug.step';b.export_step(bad,path)
            reloaded=b.importers.importStep(str(path))
            self.assertAlmostEqual(b.measure_depth(reloaded)['actual_depth_mm'],.65,places=6)
            with self.assertRaisesRegex(AssertionError,'actual depth'):b.assert_depth(reloaded,requested)
    def test_07_groove_width_from_actual_floor_wires(self):
        for sh in self.models.values():
            face=next(f for f in b.planar_faces(sh) if abs(f.BoundingBox().xlen-60)<b.TOL and abs(f.BoundingBox().ylen-58)<b.TOL)
            lengths=sorted([(w.BoundingBox().xlen,w.BoundingBox().ylen) for w in face.Wires()])
            self.assertAlmostEqual((lengths[1][0]-lengths[0][0])/2,2.1,places=6)
            self.assertAlmostEqual((lengths[1][1]-lengths[0][1])/2,2.1,places=6)
    def test_08_radii_match_parent_actual_cylinders(self):
        parent_r=b.cylinder_radii(b.source_body())
        for r in (3.9,4.0,6.0,8.0):
            self.assertIn(r,parent_r)
            for sh in self.models.values():self.assertIn(r,b.cylinder_radii(sh))
    def test_09_actual_hard_stop_height(self):
        for sh in self.models.values():
            rim=b.measure_depth(sh)['rim_z_mm'];stop=b.probe_surface_z(sh,38,34,26,31)
            self.assertAlmostEqual(stop-rim,.895,places=6)
    def test_10_rigid_body_lid_closure(self):
        for sh in self.models.values():self.assertLess(b.common(sh,self.lid.translate((0,0,b.STOP_Z))),b.TOL)
    def test_11_four_through_holes_and_alignment(self):
        for sh in [*self.models.values(),self.lid]:
            cylinders=[f._geomAdaptor().Cylinder() for f in sh.faces().vals() if f.geomType()=='CYLINDER']
            points={(round(c.Location().X(),6),round(c.Location().Y(),6)) for c in cylinders if abs(c.Radius()-2.25)<b.TOL}
            self.assertEqual(points,set(b.M4))
        for x,y in b.M4:
            probe=b.cyl(4.4,40,(x,y,0))
            for sh in self.models.values():self.assertLess(b.common(sh,probe),b.TOL)
            self.assertLess(b.common(self.lid,probe),b.TOL)
    def test_12_tower_clear_of_groove(self):
        for m in self.metrics.values():self.assertGreater(m['tower_to_groove_mm'],2.8)
    def test_13_driver_access(self):
        # Above the lid, the vertical driver shaft is unobstructed; no chimney.
        for x,y in b.M4:
            tool=b.cyl(10,20,(x,y,b.STOP_Z+b.LID_T+0.01))
            self.assertLess(b.common(tool,b.closure_lid()),b.TOL)
    def test_14_parent_corner_cross_section_zero_delta(self):
        for depth in b.VARIANTS.values():self.assertTrue(all(x<b.TOL for x in b.corner_deltas(depth)))
    def test_15_parent_lid_corner_zero_delta(self):
        for sx in (-1,1):
            for sy in (-1,1):
                mask=b.box(12,12,8,(sx*34,sy*34,4))
                source=b.source_lid().translate((-sx*50,-sy*8,0)).intersect(mask)
                self.assertLess(b.delta(source,self.lid.intersect(mask)),b.TOL)
    def test_16_only_depth_differs(self):
        difference=self.models['G055'].cut(self.models['G065'])
        allowed=b.ring(b.OUTER,b.GROOVE_INNER,.1,b.RIM-.65)
        self.assertLess(b.delta(difference,allowed),b.TOL)
        self.assertLess(b.volume(self.models['G065'].cut(self.models['G055'])),b.TOL)
    def test_17_identical_external_envelopes(self):
        for sh in self.models.values():self.assertEqual(b.bbox(sh),[80.,80.,29.395])
        self.assertEqual(b.bbox(self.lid),[80.,80.,8.])
    def test_18_closed_gasket_four_corners(self):
        wire=b.centerline();self.assertTrue(wire.IsClosed())
        types=[e.geomType() for e in wire.Edges()]
        self.assertEqual(types.count('CIRCLE'),4);self.assertEqual(types.count('LINE'),4)
        self.assertAlmostEqual(wire.Length(),219.1017672705,places=6)
    def test_19_gasket_diameter(self):
        # Swept round cross-section area inferred from exact solid volume/length.
        for d in b.VARIANTS.values():
            area=b.volume(b.gasket(d))/b.centerline().Length()
            self.assertAlmostEqual(area,b.math.pi*.9*.9,places=5)
    def test_20_witness_cavity_is_closed_no_penetrations(self):
        for d in b.VARIANTS.values():self.assertAlmostEqual(b.dry_volume(d),75495.2022735,places=5)
    def test_21_witness_clearance(self):
        for sh in self.models.values():self.assertLess(b.common(sh,b.witness()),b.TOL)
        self.assertLess(b.bbox(b.witness())[0],b.INNER[0]);self.assertLess(b.bbox(b.witness())[1],b.INNER[1])
    def test_22_floor_and_wall_from_brep(self):
        for sh in self.models.values():
            self.assertAlmostEqual(b.probe_surface_z(sh,0,0,0,8),3.5,places=6)
            section=sh.intersect(b.box(15,.1,.1,(28,0,10)))
            self.assertAlmostEqual(section.val().BoundingBox().xlen,3.5,places=6)
    def test_23_stl_topology_and_winding(self):
        for p in b.STLS:self.assertTrue(b.stl_quality(LANE/p)['pass'])
    def test_24_brep_self_interference(self):
        for sh in [*self.models.values(),self.lid]:
            self.assertTrue(sh.val().isValid());self.assertEqual(len(sh.solids().vals()),1)
            self.assertFalse(b.self_interference(sh)['faulty'])
    def test_25_compression_calculated_not_physical(self):
        self.assertAlmostEqual(self.metrics['G055']['calculated_compression_mm'],.355,places=6)
        self.assertAlmostEqual(self.metrics['G065']['calculated_compression_mm'],.255,places=6)
        p=json.loads((LANE/'design_parameters.json').read_text())
        self.assertEqual(p['water_physical_test'],'PENDING');self.assertEqual(p['primary'],'G065')
    def test_26_a1_bounds(self):
        for sh in [*self.models.values(),self.lid]:self.assertLess(max(b.bbox(sh)),256)
    def test_27_parent_protection(self):self.assertTrue(b.audit()['pass'])
    def test_28_full_bbox_hold_not_released(self):
        p=json.loads((LANE/'design_parameters.json').read_text())
        self.assertEqual(p['full_bbox_print'],'HOLD');self.assertIn('FULL_BBOX_GROOVE_G050_UNVALIDATED',p['authority_status'])
        self.assertFalse(any('full_bbox_body.stl' in p for p in b.STLS))
    def test_29_byte_reproducibility_record(self):
        report=json.loads((LANE/'validation_report.json').read_text())['reproducibility']
        self.assertTrue(report['pass']);self.assertEqual(report['pass_count'],18)
    def test_30_no_hidden_depth_parameter_bias(self):
        for request in (.45,.50,.55,.60,.65):
            with self.subTest(request=request):b.assert_depth(b.body(request),request)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--report',action='store_true');args=parser.parse_args()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(WaterDummyContract)
    names=[test.id().split('.')[-1] for test in suite]
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'pass':result.wasSuccessful(),'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'test_names':names,'step_depth_tolerance_mm':b.TOL,'negative_plus_0p10_regression':'test_06_old_centered_tool_error_rejected_after_step_reload'}
    if args.report:b.write_json(LANE/'contract_test_report.json',report)
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
