"""Fail-closed contract for BBOX four-point lower cradle V001."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest

LANE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "bbox_4point_cradle_builder", LANE / "build_bbox_4point_lower_cradle_v001.py")
b = importlib.util.module_from_spec(spec); sys.modules[spec.name] = b; spec.loader.exec_module(b)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = b.audit(); cls.q = b.inspect(LANE)
        cls.p = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
        cls.v = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.s = json.loads((LANE / "source_authority_audit.json").read_text(encoding="utf-8"))
        cls.i = json.loads((LANE / "intersection_report.json").read_text(encoding="utf-8"))
        cls.g = json.loads((LANE / "bbox_body_geometry_audit.json").read_text(encoding="utf-8"))

    def zero(self, value): self.assertLessEqual(value, b.TOL)

    def test_001_repository(self): self.assertEqual(Path(self.audit["repository"]), b.ROOT)
    def test_002_branch(self): self.assertEqual(self.audit["branch"], b.BRANCH)
    def test_003_head(self): self.assertEqual(self.audit["head"], b.HEAD)
    def test_004_staged(self): self.assertEqual(self.audit["staged_count"], 0)
    def test_005_dirty_preserved(self): self.assertEqual(self.audit["tracked_dirty_count"], 4)
    def test_006_outside_untracked(self): self.assertEqual(self.audit["outside_untracked_count"], 4489)
    def test_007_protected_count(self): self.assertEqual(len(self.audit["protected"]), 11)
    def test_008_protected_unchanged(self): self.assertEqual(self.audit["protected_source_changed_count"], 0)
    def test_009_bbox_protected(self): self.assertIn(b.BBOX_REL, self.audit["protected"])
    def test_010_cbox_v2_protected(self): self.assertIn(b.CBOX_V2_REL, self.audit["protected"])
    def test_011_path_contract(self):
        current = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
        final = {"COMMIT_PATHS.txt", "SHA256SUMS.txt", "contract_test_report.json", "repository_audit.json", "manifest.json"}
        self.assertIn(current, [b.EXPECTED, sorted(set(b.EXPECTED) - final)])
    def test_012_exact_path_count(self): self.assertEqual(len(b.EXPECTED), 61)
    def test_013_body_source(self): self.assertEqual(self.g["source"], b.BBOX_REL + "/artifacts/compact_field_bbox_v004_g065_body.step")
    def test_014_body_bounds(self): self.assertEqual([round(x, 3) for x in self.g["body_bounds_mm"]], [180.0, 96.0, 114.395])
    def test_015_lower_footprint(self): self.assertEqual([round(x, 3) for x in self.g["lower_body_core_footprint_mm"]], [162.0, 76.0])
    def test_016_bottom_z(self): self.assertEqual(self.g["bottom_z_mm"], 0.0)
    def test_017_bottom_area(self): self.assertAlmostEqual(self.g["bottom_face_area_mm2"], 12312.0, 6)
    def test_018_lower_corner(self): self.assertEqual(self.g["lower_corner_radius_mm"], 0.0)
    def test_019_no_taper(self): self.assertEqual(self.g["lower_taper"], "NONE")
    def test_020_wall(self): self.assertEqual(self.g["wall_mm"], 3.5)
    def test_021_floor(self): self.assertEqual(self.g["floor_mm"], 3.5)
    def test_022_tower_envelope(self): self.assertEqual([round(x, 3) for x in self.g["top_m4_tower_envelope_xy_mm"]], [180.0, 96.0])
    def test_023_tower_count(self): self.assertEqual(self.g["m4_tower_count"], 8)
    def test_024_mechanical_fit_only(self): self.assertEqual(self.g["body_geometry_reference"], "VALID_FOR_MECHANICAL_FIT_STUDY")
    def test_025_water_separate(self): self.assertEqual(self.g["waterproof_authority"], "SEPARATE_NOT_PROMOTED")
    def test_026_dummy_pass(self): self.assertEqual(self.g["small_g065_dummy_water"], "PASS")
    def test_027_full_water_fail(self): self.assertIn("FAIL", self.g["full_v004_60_min_water"])
    def test_028_battery(self): self.assertEqual(self.s["battery"]["plan_mm"], [150.9, 65.5])
    def test_029_battery_height(self): self.assertEqual(self.s["battery"]["terminal_inclusive_height_mm"], 99.4)
    def test_030_battery_mass(self): self.assertEqual(self.s["battery"]["mass_kg"], 1.2)
    def test_031_full_mass_pending(self): self.assertEqual(self.s["battery"]["full_assembly_mass"], "PHYSICAL_PENDING")
    def test_032_cbox_interface_pass(self): self.assertIn("PHYSICAL_FIT_PASS", self.s["cbox_v002_interface"]["physical_result"])
    def test_033_cbox_exact_reuse(self): self.assertEqual(self.s["cbox_v002_interface"]["reused"], "EXACT_BREP_SUBSET")
    def test_034_slot_entrance(self): self.assertEqual(self.s["rail"]["slot_entrance_mm"], 6.4)
    def test_035_slot_internal(self): self.assertEqual(self.s["rail"]["slot_internal_max_mm"], 10.8)
    def test_036_slot_depth(self): self.assertEqual(self.s["rail"]["slot_depth_mm"], 6.4)
    def test_037_rail_width(self): self.assertEqual(self.s["rail"]["top_face_width_mm"], 20)
    def test_038_xy_pending(self): self.assertIn("PENDING", self.s["registration"]["bbox_xy"])
    def test_039_z_conflict(self): self.assertIn("UNRESOLVED", self.s["registration"]["v004_exact_top_vs_physical_z254"])
    def test_040_four_shoes(self): self.assertEqual(self.p["architecture"]["shoe_count"], 4)
    def test_041_one_m5(self): self.assertEqual(self.p["architecture"]["m5_per_shoe"], 1)
    def test_042_four_m5(self): self.assertEqual(self.p["architecture"]["total_m5"], 4)
    def test_043_independent(self): self.assertTrue(self.p["architecture"]["independent_shoes"])
    def test_044_no_bridge(self): self.assertFalse(self.p["architecture"]["fixed_left_right_bridge"])
    def test_045_no_lid_mount(self): self.assertFalse(self.p["architecture"]["bbox_lid_is_structural_mount"])
    def test_046_no_lid_m4_mount(self): self.assertFalse(self.p["architecture"]["bbox_lid_m4_used_for_frame_mount"])
    def test_047_no_bbox_mod(self): self.assertEqual(self.p["architecture"]["bbox_modification_count"], 0)
    def test_048_no_new_holes(self): self.assertEqual(self.p["architecture"]["new_bbox_holes"], 0)
    def test_049_c03_actual(self): self.assertAlmostEqual(self.q["actual_geometry"]["clearance_c03_mm"], 0.3, 6)
    def test_050_c05_actual(self): self.assertAlmostEqual(self.q["actual_geometry"]["clearance_c05_mm"], 0.5, 6)
    def test_051_c08_actual(self): self.assertAlmostEqual(self.q["actual_geometry"]["clearance_c08_mm"], 0.8, 6)
    def test_052_ledge_actual(self): self.assertAlmostEqual(self.q["actual_geometry"]["support_ledge_depth_mm"], 10.0, 6)
    def test_053_lip_actual(self): self.assertAlmostEqual(self.q["actual_geometry"]["vertical_lip_height_mm"], 12.0, 6)
    def test_054_tpu_actual(self): self.assertEqual([round(x, 6) for x in self.q["actual_geometry"]["tpu_pad_bounds_mm"]], [30.0, 10.0, 1.0])
    def test_055_shim05(self): self.assertEqual([round(x, 6) for x in self.q["actual_geometry"]["shim_0p5_bounds_mm"]], [30.0, 10.0, 0.5])
    def test_056_shim10(self): self.assertEqual([round(x, 6) for x in self.q["actual_geometry"]["shim_1p0_bounds_mm"]], [30.0, 10.0, 1.0])
    def test_057_m5_through_x(self): self.assertAlmostEqual(self.q["actual_geometry"]["m5_through_actual"]["x_width_mm"], 5.8, 6)
    def test_058_m5_through_y(self): self.assertAlmostEqual(self.q["actual_geometry"]["m5_through_actual"]["y_width_mm"], 8.8, 6)
    def test_059_m5_pocket_x(self): self.assertAlmostEqual(self.q["actual_geometry"]["m5_pocket_actual"]["x_width_mm"], 12.0, 6)
    def test_060_m5_pocket_y(self): self.assertAlmostEqual(self.q["actual_geometry"]["m5_pocket_actual"]["y_width_mm"], 15.0, 6)
    def test_061_interface_zero_diff(self): self.zero(self.q["actual_geometry"]["proven_interface_symmetric_difference_mm3"])
    def test_062_contact_each(self):
        values = self.q["actual_geometry"]["contact_area_per_shoe_mm2"]
        self.assertTrue(all(value >= 300.0 - 1e-4 for value in values))
        self.assertAlmostEqual(values[0], values[1], 4); self.assertAlmostEqual(values[2], values[3], 4)
    def test_063_contact_total(self): self.assertAlmostEqual(self.q["actual_geometry"]["total_contact_area_mm2"], sum(self.q["actual_geometry"]["contact_area_per_shoe_mm2"]), 6)
    def test_064_support_spacing_x(self): self.assertEqual(self.q["actual_geometry"]["front_rear_support_center_spacing_mm"], 120.0)
    def test_065_support_spacing_y(self): self.assertEqual(self.q["actual_geometry"]["left_right_effective_support_spacing_mm"], 66.0)
    def test_066_fastener_spacing(self): self.assertEqual(self.q["actual_geometry"]["front_rear_rail_fastener_spacing_mm"], 74.0)
    def test_067_body_zero(self): self.zero(self.i["cradle_to_bbox_body_mm3"])
    def test_068_lid_zero(self): self.zero(self.i["cradle_to_bbox_lid_mm3"])
    def test_069_gasket_zero(self): self.zero(self.i["cradle_to_gasket_mm3"])
    def test_070_chimney_zero(self): self.zero(self.i["cradle_to_chimney_mm3"])
    def test_071_ears_zero(self): self.zero(self.i["cradle_to_lid_m4_ears_mm3"])
    def test_072_cbox_saddle_zero(self): self.zero(self.i["cradle_to_cbox_saddle_mm3"])
    def test_073_crawler_zero(self): self.zero(self.i["cradle_to_crawler_static_mm3"])
    def test_074_tool_zero(self): self.zero(self.i["bbox_lid_m4_tool_path_mm3"])
    def test_075_battery_sweep_zero(self): self.zero(self.i["battery_vertical_removal_to_cradle_mm3"])
    def test_076_lid_sweep_zero(self): self.assertTrue(all(v <= b.TOL for v in self.i["bbox_lid_removal_sweep_mm3"]))
    def test_077_body_sweep_zero(self): self.assertTrue(all(v <= b.TOL for v in self.i["bbox_body_removal_sweep_mm3"]))
    def test_078_cbox_sweep_zero(self): self.assertTrue(all(v <= b.TOL for v in self.i["cbox_removal_sweep_mm3"]))
    def test_079_lid_service(self): self.assertIn("PASS", self.i["bbox_lid_removal"])
    def test_080_battery_service(self): self.assertIn("PASS", self.i["battery_vertical_removal"])
    def test_081_tool_service(self): self.assertIn("PASS", self.i["lid_m4_tool_access"])
    def test_082_body_service(self): self.assertIn("PASS", self.i["bbox_body_removal"])
    def test_083_cbox_service(self): self.assertIn("PASS", self.i["cbox_service_path"])
    def test_084_dynamic_pending(self): self.assertEqual(self.i["crawler_dynamic_clearance"], "PHYSICAL_PENDING")
    def test_085_uplift(self): self.assertEqual(self.p["retention"]["vertical_uplift"], "FUTURE_CLIP_REQUIRED")
    def test_086_rollover(self): self.assertEqual(self.p["retention"]["rollover"], "PENDING")
    def test_087_first_print(self): self.assertEqual(self.p["print"]["first_print"], "artifacts/bbox_lower_cradle_fit_coupon_c03.stl")
    def test_088_petg(self): self.assertEqual(self.p["print"]["shoe_material"], "PETG")
    def test_089_support(self): self.assertIn("OFF", self.p["print"]["support"])
    def test_090_full_hold(self): self.assertIn("HOLD", self.p["shoe"]["full_print"])
    def test_091_regression(self): self.assertTrue(self.v["regression"]["requested_c05_actual_c06_rejected"])
    def test_092_cad_repro(self): self.assertTrue(self.v["cad_reproducibility"]["pass"])
    def test_093_cad_repro_count(self): self.assertEqual(self.v["cad_reproducibility"]["count"], 36)
    def test_094_step_count(self): self.assertEqual(len(self.q["step"]), 15)
    def test_095_stl_count(self): self.assertEqual(len(self.q["stl"]), 10)
    def test_096_svg_count(self): self.assertEqual(len(b.SVGS), 11)


def make_step(path):
    def test(self): self.assertEqual(self.q["step"][path]["reload"], "PASS")
    return test


counter = 97
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
