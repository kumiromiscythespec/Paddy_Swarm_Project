"""Fail-closed contract for BBOX four-point lower cradle V002."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest

LANE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "bbox_4point_cradle_v002_builder", LANE / "build_bbox_4point_lower_cradle_v002.py")
b = importlib.util.module_from_spec(spec); sys.modules[spec.name] = b; spec.loader.exec_module(b)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = b.audit(); cls.q = b.inspect(LANE)
        cls.p = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
        cls.v = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.s = json.loads((LANE / "source_authority_audit.json").read_text(encoding="utf-8"))
        cls.d = json.loads((LANE / "v001_v002_geometry_diff.json").read_text(encoding="utf-8"))
        cls.i = json.loads((LANE / "insertion_sweep_audit.json").read_text(encoding="utf-8"))
        cls.x = json.loads((LANE / "intersection_report.json").read_text(encoding="utf-8"))

    def zero(self, value): self.assertLessEqual(value, b.TOL)

    def test_001_repository(self): self.assertEqual(Path(self.audit["repository"]), b.ROOT)
    def test_002_branch(self): self.assertEqual(self.audit["branch"], b.BRANCH)
    def test_003_head(self): self.assertEqual(self.audit["head"], b.HEAD)
    def test_004_staged(self): self.assertEqual(self.audit["staged_count"], 0)
    def test_005_dirty_preserved(self): self.assertEqual(self.audit["tracked_dirty_count"], 4)
    def test_006_outside_untracked(self): self.assertEqual(self.audit["outside_untracked_count"], 4550)
    def test_007_protected_count(self): self.assertEqual(len(self.audit["protected"]), 12)
    def test_008_protected_unchanged(self): self.assertEqual(self.audit["protected_source_changed_count"], 0)
    def test_009_v001_protected(self): self.assertIn(b.V1_REL, self.audit["protected"])
    def test_010_bbox_protected(self): self.assertIn(b.BBOX_REL, self.audit["protected"])
    def test_011_cbox_protected(self): self.assertIn(b.CBOX_V2_REL, self.audit["protected"])
    def test_012_p25_protected(self): self.assertIn(b.P25_REL, self.audit["protected"])
    def test_013_path_contract(self):
        current = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
        final = {"COMMIT_PATHS.txt", "SHA256SUMS.txt", "contract_test_report.json",
                 "repository_audit.json", "manifest.json"}
        self.assertIn(current, [b.EXPECTED, sorted(set(b.EXPECTED) - final)])
    def test_014_exact_path_count(self): self.assertEqual(len(b.EXPECTED), 66)
    def test_015_v001_rail_physical_pass(self): self.assertEqual(self.d["v001_rail_m5_fit"], "PHYSICAL_FIT_PASS")
    def test_016_v001_single_pass(self): self.assertEqual(self.d["v001_single_shoe_local_interface"], "PHYSICAL_FIT_PASS")
    def test_017_v001_four_fail(self): self.assertEqual(self.d["v001_four_shoe_bbox_insertion"], "PHYSICAL_FAIL")
    def test_018_failure_mode(self): self.assertEqual(self.d["failure_mode"], "FIXED_LOCATING_LIP_INSTALLATION_ENVELOPE_CONFLICT")
    def test_019_v001_source(self): self.assertEqual(self.d["v001_source"], b.V1_REL)
    def test_020_lip_removed(self): self.assertAlmostEqual(self.q["actual_geometry"]["permanent_lip_height_mm"], 0.0, 6)
    def test_021_removed_volume_positive(self): self.assertGreater(self.d["intentional_fixed_lip_removed_volume_mm3"], 0)
    def test_022_rail_zero_diff(self): self.zero(self.d["rail_interface_symmetric_difference_mm3"])
    def test_023_arm_zero_diff(self): self.zero(self.d["protected_arm_symmetric_difference_mm3"])
    def test_024_ledge_zero_diff(self): self.zero(self.d["support_ledge_symmetric_difference_mm3"])
    def test_025_ledge_actual(self): self.assertAlmostEqual(self.q["actual_geometry"]["support_ledge_depth_mm"], 10.0, 6)
    def test_026_four_shoes(self): self.assertEqual(self.p["permanent_shoes"]["count"], 4)
    def test_027_independent(self): self.assertTrue(self.p["permanent_shoes"]["independent"])
    def test_028_no_bridge(self): self.assertFalse(self.p["permanent_shoes"]["fixed_cross_bridge"])
    def test_029_four_rail_m5(self): self.assertEqual(self.p["permanent_shoes"]["rail_m5_count"], 4)
    def test_030_no_bbox_holes(self): self.assertEqual(self.p["permanent_shoes"]["bbox_new_holes"], 0)
    def test_031_two_clips(self): self.assertEqual(self.p["retention"]["count"], 2)
    def test_032_mirrored_clip_architecture(self): self.assertIn("LEFT_RIGHT_MIRRORED", self.p["retention"]["architecture"])
    def test_033_clip_after_seating(self): self.assertTrue(self.p["retention"]["install_after_bbox_seating"])
    def test_034_one_fastener_each(self): self.assertEqual(self.q["actual_geometry"]["retention_fastener_count"], 2)
    def test_035_m5_clip_hole(self): self.assertAlmostEqual(self.q["actual_geometry"]["retention_fastener_clearance_diameter_mm"], 5.5, 6)
    def test_036_metal_fastener(self): self.assertIn("METAL", self.p["retention"]["attachment"])
    def test_037_fastener_length_pending(self): self.assertIn("PENDING", self.p["retention"]["fastener_length"])
    def test_038_r05_actual(self): self.assertAlmostEqual(self.q["actual_geometry"]["r05_clearance_mm"], 0.5, 6)
    def test_039_r08_actual(self): self.assertAlmostEqual(self.q["actual_geometry"]["r08_clearance_mm"], 0.8, 6)
    def test_040_r10_actual(self): self.assertAlmostEqual(self.q["actual_geometry"]["r10_clearance_mm"], 1.0, 6)
    def test_041_selected_r08(self): self.assertAlmostEqual(self.p["retention"]["selected_provisional_clearance_mm"], 0.8, 6)
    def test_042_uplift_gap_actual(self): self.assertAlmostEqual(self.q["actual_geometry"]["selected_uplift_gap_mm"], 1.0, 6)
    def test_043_low_clip_zone(self): self.assertEqual(self.q["actual_geometry"]["clip_contact_zone_from_bbox_bottom_mm"], [1.0, 20.0])
    def test_044_uplift_pending(self): self.assertEqual(self.p["retention"]["positive_uplift_load_authority"], "PHYSICAL_PENDING")
    def test_045_rollover_pending(self): self.assertEqual(self.p["retention"]["rollover"], "PHYSICAL_PENDING")
    def test_046_v001_insertion_detected(self): self.assertGreater(self.i["v001_conservative_final_insertion_intersection_mm3"], 0)
    def test_047_v001_insertion_status(self): self.assertIn("FAIL", self.i["v001_four_shoe_vertical_insertion"])
    def test_048_v002_conservative_sweep(self): self.assertTrue(all(v <= b.TOL for v in self.i["v002_conservative_intersections_mm3"].values()))
    def test_049_v002_actual_sweep(self): self.assertTrue(all(v <= b.TOL for v in self.i["v002_actual_assembly_intersections_mm3"].values()))
    def test_050_sweep_offsets(self): self.assertEqual(self.i["sweep_offsets_mm"], [80, 60, 40, 20, 0])
    def test_051_v002_insertion_pass(self): self.assertEqual(self.i["v002_four_shoe_vertical_insertion"], "PASS_REFERENCE")
    def test_052_v002_removal_pass(self): self.assertEqual(self.i["bbox_removal_after_clip_removal"], "PASS_REFERENCE")
    def test_053_all_four_seated(self): self.assertTrue(self.i["all_four_seated"])
    def test_054_four_contact_areas(self): self.assertEqual(len(self.i["seated_contact_area_per_shoe_mm2"]), 4)
    def test_055_contact_area(self): self.assertTrue(all(v >= 300 - 1e-4 for v in self.i["seated_contact_area_per_shoe_mm2"]))
    def test_056_shoe_body_zero(self): self.zero(self.x["support_shoe_to_bbox_body_mm3"])
    def test_057_shoe_lid_zero(self): self.zero(self.x["support_shoe_to_lid_mm3"])
    def test_058_shoe_gasket_zero(self): self.zero(self.x["support_shoe_to_gasket_mm3"])
    def test_059_shoe_ear_zero(self): self.zero(self.x["support_shoe_to_lid_ear_mm3"])
    def test_060_clip_body_zero(self): self.zero(self.x["clip_to_bbox_body_mm3"])
    def test_061_clip_lid_zero(self): self.zero(self.x["clip_to_lid_mm3"])
    def test_062_clip_gasket_zero(self): self.zero(self.x["clip_to_gasket_mm3"])
    def test_063_clip_chimney_zero(self): self.zero(self.x["clip_to_chimney_mm3"])
    def test_064_clip_ear_zero(self): self.zero(self.x["clip_to_lid_ear_mm3"])
    def test_065_cbox_zero(self): self.zero(self.x["cradle_to_cbox_saddle_mm3"])
    def test_066_clip_cbox_zero(self): self.zero(self.x["retention_clip_to_cbox_mm3"])
    def test_067_crawler_zero(self): self.zero(self.x["cradle_to_crawler_static_mm3"])
    def test_068_clip_crawler_zero(self): self.zero(self.x["clip_to_crawler_static_mm3"])
    def test_069_tool_shoe_zero(self): self.zero(self.x["lid_m4_tool_path_to_shoes_mm3"])
    def test_070_tool_clip_zero(self): self.zero(self.x["lid_m4_tool_path_to_clips_mm3"])
    def test_071_battery_zero(self): self.zero(self.x["battery_vertical_removal_mm3"])
    def test_072_lid_sweep_zero(self): self.assertTrue(all(v <= b.TOL for v in self.x["lid_removal_sweep_mm3"]))
    def test_073_cbox_sweep_zero(self): self.assertTrue(all(v <= b.TOL for v in self.x["cbox_removal_sweep_mm3"]))
    def test_074_lid_service(self): self.assertEqual(self.x["lid_removal_with_clips_installed"], "PASS_REFERENCE")
    def test_075_battery_service(self): self.assertEqual(self.x["battery_vertical_removal"], "PASS_REFERENCE")
    def test_076_tool_service(self): self.assertEqual(self.x["lid_m4_tool_access"], "PASS_REFERENCE")
    def test_077_dynamic_pending(self): self.assertEqual(self.x["crawler_dynamic_clearance"], "PHYSICAL_PENDING")
    def test_078_no_clutch_invention(self): self.assertFalse(self.s["p25"]["clutch_geometry_invented"])
    def test_079_tpu_size(self): self.assertEqual([round(v, 6) for v in self.q["actual_geometry"]["tpu_pad_bounds_mm"]], [30.0, 10.0, 1.0])
    def test_080_tpu_nonstructural(self): self.assertFalse(self.p["tpu"]["structural"])
    def test_081_tpu_optional(self): self.assertFalse(self.p["tpu"]["required_for_geometric_fit"])
    def test_082_tpu_both_refs(self): self.assertEqual(self.p["tpu"]["references_tested"], ["WITHOUT_TPU", "WITH_1MM_TPU"])
    def test_083_rail_difference(self): self.assertEqual(self.p["rail_height"]["left_top_mm"] - self.p["rail_height"]["right_top_mm"], 1.0)
    def test_084_shims(self): self.assertEqual(self.p["rail_height"]["optional_shims_mm"], [0.5, 1.0])
    def test_085_petg(self): self.assertEqual(self.p["print"]["shoe_and_clip_material"], "PETG")
    def test_086_bambu(self): self.assertEqual(self.p["print"]["printer"], "BAMBU_A1")
    def test_087_support_off(self): self.assertIn("OFF", self.p["print"]["support"])
    def test_088_slicer_hold(self): self.assertIn("HOLD", self.p["print"]["slicer"])
    def test_089_first_print_four(self): self.assertEqual(len(self.p["print"]["first_print"]), 4)
    def test_090_first_print_coupon(self): self.assertIn("bbox_v002_support_clip_coupon.stl", self.p["print"]["first_print"][0])
    def test_091_full_hold(self): self.assertIn("HOLD", self.p["print"]["full_v002_cradle_print"])
    def test_092_bbox_dims(self): self.assertEqual(self.s["bbox"]["lower_body_mm"], [162.0, 76.0])
    def test_093_tower_dims(self): self.assertEqual(self.s["bbox"]["upper_tower_envelope_mm"], [180.0, 96.0])
    def test_094_battery_dims(self): self.assertEqual(self.s["battery"]["plan_mm"], [150.9, 65.5])
    def test_095_battery_mass(self): self.assertEqual(self.s["battery"]["mass_kg"], 1.2)
    def test_096_full_mass_pending(self): self.assertIn("PENDING", self.s["battery"]["full_loaded_bbox_mass"])
    def test_097_repro(self): self.assertTrue(self.v["cad_reproducibility"]["pass"])
    def test_098_repro_count(self): self.assertEqual(self.v["cad_reproducibility"]["count"], 40)
    def test_099_v001_regression(self): self.assertTrue(self.v["regression"]["v001_failure_detected"])
    def test_100_v002_regression(self): self.assertTrue(self.v["regression"]["v002_all_states_zero"])
    def test_101_step_count(self): self.assertEqual(len(self.q["step"]), 18)
    def test_102_stl_count(self): self.assertEqual(len(self.q["stl"]), 11)
    def test_103_svg_count(self): self.assertEqual(len(b.SVGS), 11)


def make_step(path):
    def test(self): self.assertEqual(self.q["step"][path]["reload"], "PASS")
    return test


counter = 104
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
