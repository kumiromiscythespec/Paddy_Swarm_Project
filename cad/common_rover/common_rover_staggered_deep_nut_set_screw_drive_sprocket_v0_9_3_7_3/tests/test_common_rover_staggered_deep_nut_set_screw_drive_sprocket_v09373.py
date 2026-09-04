#!/usr/bin/env python3
"""Contract tests for Common Rover H2.4 v0.9.3.7.3."""
from __future__ import annotations

import hashlib, importlib.util, json, os, unittest, zipfile
from pathlib import Path, PurePosixPath

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_common_rover_staggered_deep_nut_set_screw_drive_sprocket_v09373.py"
SPEC = importlib.util.spec_from_file_location("h24_builder", BUILDER)
assert SPEC and SPEC.loader
B = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(B)

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

class TestH24Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.m = json.loads((LANE / "geometry_manifest.json").read_text(encoding="utf-8"))
        cls.v = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.steps, cls.stls, cls.svgs, cls.ledgers = B.verify_steps(LANE), B.verify_stls(LANE), B.verify_svgs(LANE), B.verify_ledgers(LANE)
        cls.docs = "\n".join((LANE / p).read_text(encoding="utf-8") for p in B.ROOT_FILES if p.endswith(".md"))

    def test_001_version(self): self.assertEqual(self.m["version"], "0.9.3.7.3")
    def test_002_mechanism(self): self.assertEqual(self.m["mechanism_name"], "H2.4_STAGGERED_DEEP_NUT_SET_SCREW_HUB")
    def test_003_exact_75_paths(self): self.assertEqual((len(B.PATHS), len(set(B.PATHS))), (75, 75))
    def test_004_exact_lane_files(self): self.assertEqual(B.files(LANE), sorted(B.PATHS))
    def test_005_source_count(self): self.assertEqual(len(B.SOURCE_FILES), 2)
    def test_006_step_count(self): self.assertEqual((self.steps["pass_count"], self.steps["count"]), (28, 28))
    def test_007_stl_count(self): self.assertEqual((self.stls["pass_count"], self.stls["count"]), (11, 11))
    def test_008_svg_count(self): self.assertEqual((self.svgs["pass_count"], self.svgs["count"]), (5, 5))
    def test_009_manifest_contract(self): self.assertEqual(self.ledgers["status"], "PASS")
    def test_010_manifest_count(self): self.assertEqual(self.ledgers["manifest_count"], 75)
    def test_011_hash_count(self): self.assertEqual(self.ledgers["hash_count"], 74)

    def test_012_parent_version(self): self.assertEqual(self.m["parent_version"], "0.9.3.7.2")
    def test_013_parent_count(self): self.assertEqual(self.m["parent_audit"]["count"], 70)
    def test_014_parent_ledger(self): self.assertEqual(self.m["parent_ledger_sha256"], B.PARENT_LEDGER)
    def test_015_parent_zip(self): self.assertEqual(self.m["parent_zip_sha256"], B.PARENT_ZIP_SHA)
    def test_016_parent_failure(self): self.assertEqual(self.m["parent_failure_mode"], "H2.3_HEADED_SCREW_WASHER_INTERFACE_FAIL")
    def test_017_authority_unchanged(self): self.assertFalse(self.m["authority_files_changed"])

    def test_018_tooth_count(self): self.assertEqual(self.m["tooth_count"], 12)
    def test_019_phase_spacing(self): self.assertEqual((self.m["phase_degrees"], self.m["tooth_spacing_degrees"]), (15.0, 30.0))
    def test_020_source_radii(self): self.assertEqual((self.m["tooth_tip_radius"], self.m["tooth_root_radius"]), (33.07, 29.47))
    def test_021_source_widths(self): self.assertEqual((self.m["tooth_tip_width"], self.m["tooth_root_width"], self.m["tooth_axial_width"]), (7.5, 9.5, 44.0))
    def test_022_external_conflict_flag(self): self.assertTrue(self.m["external_tooth_geometry_changed"])
    def test_023_external_conflict_volume(self): self.assertGreater(self.m["parent_minus_final_external_volume"], 0); self.assertLessEqual(self.m["final_minus_parent_external_volume"], 1e-6)
    def test_024_external_bbox(self): self.assertEqual(self.m["parent_external_bbox"], self.m["final_external_bbox"])
    def test_025_bbox_raw_tolerance(self): self.assertLessEqual(self.m["bbox_boolean_rounding_delta_max_mm"], self.m["bbox_comparison_tolerance_mm"])
    def test_026_all_variants_valid_single(self): self.assertTrue(all(x["valid"] and x["solid_count"] == 1 for x in self.m["analysis"]["variants"].values()))
    def test_027_all_variants_record_access_conflict(self): self.assertTrue(all(x["parent_minus_external_mm3"] > 0 and x["final_minus_external_mm3"] <= 1e-6 for x in self.m["analysis"]["variants"].values()))

    def test_028_front_angles(self): self.assertEqual(self.m["front_insert_angles"], [0, 180])
    def test_029_rear_angles(self): self.assertEqual(self.m["rear_insert_angles"], [90, 270])
    def test_030_layouts(self): self.assertEqual(self.m["axial_layout_variants"], {"C0": 0.0, "C15": 1.5, "C30": 3.0})
    def test_031_c0_preferred(self): self.assertEqual(self.m["analysis"]["layouts"]["C0"]["selection"], "PREFERRED_MINIMUM_AXIAL_COUPLE")
    def test_032_c0_spread(self): self.assertEqual(self.m["analysis"]["layouts"]["C0"]["axial_contact_spread_mm"], 0.0)
    def test_033_c15_spread(self): self.assertEqual(self.m["analysis"]["layouts"]["C15"]["axial_contact_spread_mm"], 3.0)
    def test_034_c30_spread(self): self.assertEqual(self.m["analysis"]["layouts"]["C30"]["axial_contact_spread_mm"], 6.0)
    def test_035_no_pocket_intersections(self): self.assertTrue(all(x["pocket_pairwise_max_mm3"] <= 1e-6 for x in self.m["analysis"]["layouts"].values()))

    def test_036_measured_high_nut(self): self.assertEqual((self.m["high_nut_af_measured"], self.m["high_nut_length_measured"], self.m["high_nut_count"]), (5.2, 13.0, 4))
    def test_037_af_candidates(self): self.assertEqual(self.m["high_nut_af_candidates"], [5.1, 5.15, 5.2, 5.25, 5.3, 5.35])
    def test_038_depth_candidates(self): self.assertEqual(self.m["high_nut_length_clearance_candidates"], [13.1, 13.2, 13.3])
    def test_039_coupon_solids(self): self.assertEqual((self.m["analysis"]["coupons"]["front_solid_count"], self.m["analysis"]["coupons"]["rear_solid_count"], self.m["analysis"]["coupons"]["access_solid_count"]), (1, 1, 1))

    def test_040_set_screw_contract(self): self.assertEqual((self.m["set_screw_size"], self.m["set_screw_length"], self.m["set_screw_count"]), ("M3", 25.0, 4))
    def test_041_tip_hold(self): self.assertTrue(self.m["set_screw_tip_status"].startswith("HOLD"))
    def test_042_no_headed_interface(self): self.assertNotIn("washer_outer_diameter_measured", self.m)
    def test_043_access_candidates(self): self.assertEqual(self.m["access_bore_candidates"], [3.5, 4.0, 4.5])
    def test_044_selected_access(self): self.assertEqual(self.m["selected_access_bore"], 3.5)
    def test_045_access_35_passes_wall(self): self.assertTrue(self.m["analysis"]["access_bores"]["3.5"]["passes_3mm_wall"])
    def test_046_access_40_fails_wall(self): self.assertFalse(self.m["analysis"]["access_bores"]["4.0"]["passes_3mm_wall"])
    def test_047_access_45_fails_wall(self): self.assertFalse(self.m["analysis"]["access_bores"]["4.5"]["passes_3mm_wall"])
    def test_048_selected_access_wall(self): self.assertGreaterEqual(self.m["minimum_access_bore_wall"], 3.0)
    def test_049_tool_measurement_hold(self): self.assertTrue(all(x["tool_physical_status"].startswith("HOLD") for x in self.m["analysis"]["access_bores"].values()))

    def test_050_recess_candidates(self): self.assertEqual(self.m["outer_end_recess_candidates"], [0.0, 0.5, 1.0, 1.5])
    def test_051_selected_recess(self): self.assertEqual(self.m["selected_outer_end_recess"], 1.0)
    def test_052_total_radial_path(self): self.assertEqual(self.m["analysis"]["reach"]["total_radial_path_mm"], 25.0)
    def test_053_nut_engagement(self): self.assertEqual(self.m["analysis"]["reach"]["high_nut_threaded_engagement_mm"], 13.0)
    def test_054_nut_to_shaft(self): self.assertAlmostEqual(self.m["analysis"]["reach"]["high_nut_inner_to_shaft_mm"], 3.3)
    def test_055_first_contact_protrusion(self): self.assertAlmostEqual(self.m["analysis"]["reach"]["first_contact_protrusion_beyond_root_mm"], 0.53)
    def test_056_selected_outer_radius(self): self.assertAlmostEqual(self.m["analysis"]["reach"]["selected_outer_radius_mm"], 28.47)
    def test_057_selected_penetration(self): self.assertAlmostEqual(self.m["analysis"]["reach"]["selected_shaft_envelope_penetration_mm"], 1.53)
    def test_058_recess_tip_holds(self): self.assertTrue(all(x["physical_tip_status"].startswith("HOLD") for x in self.m["analysis"]["recesses"].values()))
    def test_059_flush_conflicts_but_recesses_clear(self):
        rows = self.m["analysis"]["recesses"]
        self.assertGreater(rows["0.0"]["set_screw_to_link_mm3"], 0)
        self.assertTrue(all(rows[x]["set_screw_to_link_mm3"] <= 1e-6 for x in ("0.5", "1.0", "1.5")))

    def test_060_set_screw_link_zero(self): self.assertLessEqual(self.m["set_screw_to_link_intersection"], 1e-6)
    def test_061_access_link_conflict_detected(self): self.assertGreater(self.m["analysis"]["intersections"]["access_bore_to_link_mm3"], 0)
    def test_062_internal_tool_link_conflict_detected(self): self.assertGreater(self.m["tool_to_link_intersection"], 0)
    def test_063_set_screw_guide_zero(self): self.assertLessEqual(self.m["set_screw_to_guide_intersection"], 1e-6)
    def test_064_set_screw_bearing_zero(self): self.assertLessEqual(self.m["set_screw_to_bearing_intersection"], 1e-6)
    def test_065_set_screw_m4_zero(self): self.assertLessEqual(self.m["analysis"]["intersections"]["set_screw_to_m4_mm3"], 1e-6)
    def test_066_high_nut_pairs_zero(self): self.assertLessEqual(self.m["analysis"]["intersections"]["high_nut_pairwise_max_mm3"], 1e-6)
    def test_067_global_registration_hold(self): self.assertEqual(self.m["analysis"]["global_registration"]["status"], "HOLD")
    def test_068_actual_tool_hold(self): self.assertTrue(self.m["analysis"]["global_registration"]["actual_external_tool_handle"].startswith("HOLD"))

    def test_069_reaction_wall(self): self.assertGreaterEqual(self.m["minimum_reaction_wall"], 3.0)
    def test_070_adjacent_wall(self): self.assertGreaterEqual(self.m["minimum_adjacent_pocket_wall"], 3.0)
    def test_071_m4_wall(self): self.assertGreaterEqual(self.m["minimum_pocket_to_m4_wall"], 3.0)
    def test_072_bore_wall(self): self.assertGreaterEqual(self.m["minimum_pocket_to_bore_wall"], 3.0)
    def test_073_retainer_contract(self): self.assertEqual((self.m["retainer_fastener_count"], self.m["retainer_fastener_size"], self.m["retainer_pcd"]), (4, "M4", 24.0))
    def test_074_shaft_unmodified(self): self.assertFalse(self.m["shaft_irreversible_machining_required"])
    def test_075_no_vendor_dependency(self): self.assertFalse(self.m["single_manufacturer_dependency"])

    def test_076_design_failure_recorded(self): self.assertEqual(self.m["design_status"], "FAIL_ACCESS_BORE_EXTERNAL_ROOT_AND_LINK_CONTRACT")
    def test_077_artifact_pass(self): self.assertEqual(self.v["artifact_contract"], "PASS")
    def test_078_body_physical_blocked(self): self.assertEqual(self.m["physical_test_status"], "COUPONS_ONLY_BODY_BLOCKED")
    def test_079_no_physical_pass(self): self.assertNotIn("H24_PHYSICAL_FIT = PASS", self.docs)
    def test_080_power_not_approved(self): self.assertEqual(self.m["powered_rotation_status"], "NOT_APPROVED")
    def test_081_field_not_approved(self): self.assertEqual(self.m["field_deployment_status"], "NOT_APPROVED")
    def test_082_torque_not_tested(self): self.assertEqual(self.m["torque_capacity_status"], "NOT_TESTED")
    def test_083_creep_required(self): self.assertEqual(self.m["creep_status"], "REQUIRED")
    def test_084_spare_rate(self): self.assertEqual(self.m["petg_spare_rate_percent"], 100)
    def test_085_release_holds(self): self.assertEqual((self.m["release"]["GITHUB_MANUFACTURING_RELEASE"], self.m["release"]["GLOBAL_ASSEMBLY_INTERFERENCE"], self.m["release"]["H24_CAD"]), ("HOLD", "HOLD", "FAIL_ACCESS_BORE_LINK_CLEARANCE"))

    def test_086_commit_paths_exact(self): self.assertEqual((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines(), [f"{B.LANE_REL}/{p}" for p in B.PATHS])
    def test_087_commit_lane_only(self): self.assertTrue(all(x.startswith(B.LANE_REL + "/") for x in (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()))
    def test_088_parent_not_in_commit(self): self.assertNotIn(B.PARENT_REL, (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8"))
    def test_089_docs_remove_headed_hardware(self): self.assertIn("Headed M3, OD6.8 washer and M3 washer seat are not used", self.docs)
    def test_090_docs_require_link_removal_for_service(self): self.assertIn("Remove crawler links before tool service", self.docs)
    def test_091_runtime_repo_guard(self): self.assertEqual(B.repo_audit(True)["status"], "PASS")
    def test_092_runtime_parent_guard(self): self.assertEqual(B.parent_audit()["status"], "PASS")

    def test_093_optional_zip_contract(self):
        zp = os.environ.get("V09373_TEST_ZIP")
        if not zp: self.skipTest("V09373_TEST_ZIP not set")
        path = Path(zp); self.assertTrue(path.is_file())
        with zipfile.ZipFile(path) as z:
            names = z.namelist(); self.assertEqual(names, list(B.PATHS)); self.assertEqual(len(names), len(set(names)))
            self.assertFalse(any(PurePosixPath(x).is_absolute() or ".." in PurePosixPath(x).parts or "\\" in x for x in names))
            self.assertEqual(z.testzip(), None)
            self.assertTrue(all(hashlib.sha256(z.read(p)).hexdigest() == sha(LANE / p) for p in names))

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestH24Contract))
    raise SystemExit(0 if result.wasSuccessful() else 1)
