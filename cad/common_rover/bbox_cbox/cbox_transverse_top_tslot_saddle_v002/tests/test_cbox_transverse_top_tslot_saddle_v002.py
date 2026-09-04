"""Fail-closed contract for CBOX top-T-slot saddle V002."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest

LANE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cbox_top_tslot_builder", LANE / "build_cbox_transverse_top_tslot_saddle_v002.py")
b = importlib.util.module_from_spec(spec); sys.modules[spec.name] = b; spec.loader.exec_module(b)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = b.audit(); cls.q = b.inspect(LANE)
        cls.p = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
        cls.v = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.s = json.loads((LANE / "source_authority_audit.json").read_text(encoding="utf-8"))
        cls.d = json.loads((LANE / "geometry_diff_report.json").read_text(encoding="utf-8"))

    def test_001_repository(self): self.assertEqual(Path(self.audit["repository"]), b.ROOT)
    def test_002_branch(self): self.assertEqual(self.audit["branch"], b.BRANCH)
    def test_003_head(self): self.assertEqual(self.audit["head"], b.HEAD)
    def test_004_staged(self): self.assertEqual(self.audit["staged_count"], 0)
    def test_005_dirty_preserved(self): self.assertEqual(self.audit["tracked_dirty_count"], 4)
    def test_006_outside_untracked(self): self.assertEqual(self.audit["outside_untracked_count"], 4442)
    def test_007_protected(self): self.assertEqual(self.audit["protected_source_changed_count"], 0)
    def test_008_parent(self): self.assertIn(b.PARENT_REL, self.audit["protected"])
    def test_009_parent_files(self): self.assertEqual(self.audit["protected"][b.PARENT_REL]["files"], 45)
    def test_010_paths(self):
        current = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
        final = {"COMMIT_PATHS.txt", "SHA256SUMS.txt", "contract_test_report.json", "repository_audit.json", "manifest.json"}
        self.assertIn(current, [b.EXPECTED, sorted(set(b.EXPECTED) - final)])
    def test_011_path_count(self): self.assertEqual(len(b.EXPECTED), 47)
    def test_012_v001_failure(self): self.assertEqual(self.s["v001"]["rail_interface"], "PHYSICAL_FIT_FAIL")
    def test_013_v001_cbox_not_rejected(self): self.assertEqual(self.s["v001"]["cbox_side_geometry"], "NOT_YET_REJECTED")
    def test_014_width(self): self.assertEqual(self.s["current_upper_rail"]["top_face_width_mm"], 20.0)
    def test_015_width_class(self): self.assertIn("PHYSICAL_DERIVED", self.s["current_upper_rail"]["top_face_width_class"])
    def test_016_height(self): self.assertEqual(self.s["current_upper_rail"]["height_mm"], 20.0)
    def test_017_profile_pending(self): self.assertEqual(self.s["current_upper_rail"]["complete_profile"], "PENDING")
    def test_018_top_slot_count(self): self.assertEqual(self.s["current_upper_rail"]["top_slot_count"], 1)
    def test_019_center_pending(self): self.assertIn("PENDING", self.s["current_upper_rail"]["top_slot_center_class"])
    def test_020_entrance(self): self.assertEqual(self.s["slot"]["entrance_mm"], 6.4)
    def test_021_internal(self): self.assertEqual(self.s["slot"]["internal_max_mm"], 10.8)
    def test_022_depth(self): self.assertEqual(self.s["slot"]["depth_mm"], 6.4)
    def test_023_lip_partial(self): self.assertEqual(self.s["slot"]["lip_profile"], "PHYSICAL_PARTIAL")
    def test_024_top_architecture(self): self.assertTrue(self.p["architecture"]["top_vertical_m5"])
    def test_025_top_two(self): self.assertEqual(self.p["architecture"]["top_vertical_m5_per_saddle"], 2)
    def test_026_no_side_holes(self): self.assertEqual(self.p["architecture"]["side_m5_hole_count"], 0)
    def test_027_independent(self): self.assertTrue(self.p["architecture"]["left_right_independent"])
    def test_028_no_bridge(self): self.assertFalse(self.p["architecture"]["fixed_cross_rail_bridge"])
    def test_029_no_bbox_load(self): self.assertFalse(self.p["architecture"]["bbox_load_bearing"])
    def test_030_no_head_load(self): self.assertFalse(self.p["architecture"]["cbox_load_on_m5_head"])
    def test_031_length(self): self.assertAlmostEqual(self.q["actual_geometry"]["left_length_mm"], 140.0, 6)
    def test_032_right_length(self): self.assertAlmostEqual(self.q["actual_geometry"]["right_length_mm"], 140.0, 6)
    def test_033_contact_width(self): self.assertAlmostEqual(self.q["actual_geometry"]["rail_contact_width_mm"], 20.0, 6)
    def test_034_support_rise(self): self.assertAlmostEqual(self.q["actual_geometry"]["cbox_support_plane_z_mm"], 8.0, 6)
    def test_035_m5_pitch(self): self.assertAlmostEqual(self.q["actual_geometry"]["m5_pitch_mm"], 100.0, 6)
    def test_036_through_x(self): self.assertAlmostEqual(self.q["actual_geometry"]["m5_through_left"]["x_width_mm"], 5.8, 6)
    def test_037_through_y(self): self.assertAlmostEqual(self.q["actual_geometry"]["m5_through_left"]["y_width_mm"], 8.8, 6)
    def test_038_pocket_x(self): self.assertAlmostEqual(self.q["actual_geometry"]["m5_pocket_left"]["x_width_mm"], 12.0, 6)
    def test_039_pocket_y(self): self.assertAlmostEqual(self.q["actual_geometry"]["m5_pocket_left"]["y_width_mm"], 15.0, 6)
    def test_040_coupon_match(self): self.assertLessEqual(self.q["actual_geometry"]["coupon_full_interface_symmetric_difference_mm3"], 1e-5)
    def test_041_shim05(self): self.assertAlmostEqual(self.q["actual_geometry"]["shim_0p5_actual_thickness_mm"], 0.5, 6)
    def test_042_shim10(self): self.assertAlmostEqual(self.q["actual_geometry"]["shim_1p0_actual_thickness_mm"], 1.0, 6)
    def test_043_cbox_bbox_zero(self): self.assertLessEqual(self.p["clearance"]["cbox_to_bbox_intersection_mm3"], 1e-6)
    def test_044_saddle_bbox_zero(self): self.assertLessEqual(self.p["clearance"]["saddle_to_bbox_intersection_mm3"], 1e-6)
    def test_045_saddle_chimney_zero(self): self.assertLessEqual(self.p["clearance"]["saddle_to_chimney_intersection_mm3"], 1e-6)
    def test_046_cbox_chimney_zero(self): self.assertLessEqual(self.p["clearance"]["cbox_to_chimney_intersection_mm3"], 1e-6)
    def test_047_saddle_crawler_zero(self): self.assertLessEqual(self.p["clearance"]["saddle_to_crawler_intersection_mm3"], 1e-6)
    def test_048_removal_zero(self): self.assertTrue(all(v <= 1e-6 for v in self.p["clearance"]["cbox_removal_sweep_intersections_mm3"]))
    def test_048a_bbox_driver_zero(self): self.assertLessEqual(self.p["clearance"]["bbox_driver_path_saddle_intersection_mm3"], 1e-6)
    def test_049_bbox_clearance(self): self.assertAlmostEqual(self.p["clearance"]["bbox_minimum_vertical_clearance_mm"], 7.869, 3)
    def test_049a_numerical_separation(self): self.assertEqual(self.p["clearance"]["cbox_assembly_reference_separation_mm"], 0.02)
    def test_050_left_crawler(self): self.assertEqual(self.p["clearance"]["left_local_saddle_to_crawler_static_clearance_mm"], 74.0)
    def test_051_right_crawler(self): self.assertEqual(self.p["clearance"]["right_local_saddle_to_crawler_static_clearance_mm"], 74.0)
    def test_052_dynamic_pending(self): self.assertEqual(self.p["clearance"]["crawler_dynamic_clearance"], "PHYSICAL_PENDING")
    def test_053_bbox_mod_zero(self): self.assertEqual(self.p["clearance"]["bbox_modification_count"], 0)
    def test_054_removal_pass(self): self.assertIn("PASS", self.p["clearance"]["cbox_removal_path"])
    def test_055_v001_bounds(self): self.assertEqual([round(x, 1) for x in self.d["v001_bounds_mm"]], [140.0, 31.3, 19.0])
    def test_056_diff_support(self): self.assertIn("MINIMAL", self.d["cbox_support_interface_diff"])
    def test_057_diff_rail(self): self.assertEqual(self.d["rail_interface_diff"], "INTENTIONAL_SIDE_FLANGE_REMOVED_TOP_FOOT_ADDED")
    def test_058_diff_fastener(self): self.assertIn("INTENTIONAL", self.d["fastener_interface_diff"])
    def test_059_m5_unknown(self): self.assertEqual(self.s["hardware"]["head_and_tnut_dimensions"], "PHYSICAL_MEASUREMENT_PENDING")
    def test_060_no_tnut_step(self): self.assertFalse(self.s["hardware"]["tnut_reference_step_generated"])
    def test_061_first_print(self): self.assertEqual(self.p["print"]["first_print"], "artifacts/cbox_top_tslot_mount_coupon_v002.stl")
    def test_062_support_off(self): self.assertEqual(self.p["print"]["support"], "OFF")
    def test_063_petg(self): self.assertEqual(self.p["saddle"]["material"], "PETG")
    def test_064_full_hold(self): self.assertIn("HOLD", self.p["saddle"]["full_print"])
    def test_065_rise_study(self): self.assertEqual([r["rise_mm"] for r in self.p["rise_study"]], [4.0, 6.0, 8.0])
    def test_066_rise_selected(self): self.assertIn("SELECTED", self.p["rise_study"][2]["status"])
    def test_067_regression(self): self.assertTrue(self.v["regression"]["requested_0p5_actual_0p6_rejected"])
    def test_068_cad_repro(self): self.assertTrue(self.v["cad_reproducibility"]["pass"])
    def test_069_cad_repro_count(self): self.assertEqual(self.v["cad_reproducibility"]["count"], 24)
    def test_070_step_count(self): self.assertEqual(len(self.q["step"]), 9)
    def test_071_stl_count(self): self.assertEqual(len(self.q["stl"]), 5)
    def test_072_svg_count(self): self.assertEqual(len(b.SVGS), 10)
    def test_072a_left_support_tilt(self): self.assertAlmostEqual(self.q["actual_geometry"]["left_cbox_contact_actual"]["tilt_deg"], b.CBOX_TILT_DEG, 5)
    def test_072b_right_support_tilt(self): self.assertAlmostEqual(self.q["actual_geometry"]["right_cbox_contact_actual"]["tilt_deg"], b.CBOX_TILT_DEG, 5)


def make_step(path):
    def test(self): self.assertEqual(self.q["step"][path]["reload"], "PASS")
    return test


counter = 73
for path in b.STEPS:
    setattr(Contract, f"test_{counter:03d}_step_{Path(path).stem}", make_step(path)); counter += 1


def make_stl(path, field):
    def test(self): self.assertTrue(self.q["stl"][path][field])
    return test


for path in b.STLS:
    for field in ("watertight", "manifold", "pass"):
        setattr(Contract, f"test_{counter:03d}_{Path(path).stem}_{field}", make_stl(path, field)); counter += 1


if __name__ == "__main__":
    started = time.perf_counter(); suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"pass": result.wasSuccessful(), "tests_run": result.testsRun,
              "failures": len(result.failures), "errors": len(result.errors),
              "skipped": len(result.skipped), "duration_seconds": round(time.perf_counter() - started, 3),
              "status": b.STATUS if result.wasSuccessful() else "CONTRACT_FAIL"}
    print(json.dumps(report, indent=2))
    if result.wasSuccessful(): b.finalize(report)
    raise SystemExit(0 if result.wasSuccessful() else 1)
