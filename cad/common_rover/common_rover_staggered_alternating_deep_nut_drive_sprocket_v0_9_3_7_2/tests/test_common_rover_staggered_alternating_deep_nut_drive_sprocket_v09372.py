#!/usr/bin/env python3
"""Contract tests for the H2.3 v0.9.3.7.2 correction handoff."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import unittest
import zipfile
from pathlib import Path, PurePosixPath

import cadquery as cq

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_common_rover_staggered_alternating_deep_nut_drive_sprocket_v09372.py"
SPEC = importlib.util.spec_from_file_location("h23_builder", BUILDER)
assert SPEC and SPEC.loader
B = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestH23Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.m = json.loads((LANE / "geometry_manifest.json").read_text(encoding="utf-8"))
        cls.v = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.steps = B.verify_steps(LANE)
        cls.stls = B.verify_stls(LANE)
        cls.svgs = B.verify_svgs(LANE)
        cls.ledgers = B.verify_ledgers(LANE)
        cls.docs = "\n".join((LANE / p).read_text(encoding="utf-8") for p in B.ROOT_FILES if p.endswith(".md"))

    def test_001_version(self): self.assertEqual(self.m["version"], "0.9.3.7.2")
    def test_002_mechanism(self): self.assertEqual(self.m["mechanism_name"], "H2.3_STAGGERED_ALTERNATING_DEEP_NUT_HEAD_CLAMP")
    def test_003_exact_70_formal_paths(self): self.assertEqual((len(B.PATHS), len(set(B.PATHS))), (70, 70))
    def test_004_exact_lane_files(self): self.assertEqual(B.files(LANE), sorted(B.PATHS))
    def test_005_source_count(self): self.assertEqual(len(B.SOURCE_FILES), 2)
    def test_006_step_count(self): self.assertEqual((self.steps["pass_count"], self.steps["count"]), (24, 24))
    def test_007_stl_count(self): self.assertEqual((self.stls["pass_count"], self.stls["count"]), (11, 11))
    def test_008_svg_count(self): self.assertEqual((self.svgs["pass_count"], self.svgs["count"]), (5, 5))
    def test_009_manifest_contract(self): self.assertEqual(self.ledgers["status"], "PASS")
    def test_010_manifest_count(self): self.assertEqual(self.ledgers["manifest_count"], 70)
    def test_011_hash_count(self): self.assertEqual(self.ledgers["hash_count"], 69)

    def test_012_parent_count(self): self.assertEqual(self.m["parent_audit"]["count"], 44)
    def test_013_parent_ledger(self): self.assertEqual(self.m["parent_ledger_sha256"], B.PARENT_LEDGER)
    def test_014_parent_zip(self): self.assertEqual(self.m["parent_zip_sha256"], B.PARENT_ZIP_SHA)
    def test_015_parent_lane(self): self.assertEqual(self.m["parent_lane"], B.PARENT_REL)
    def test_016_authority_unchanged(self): self.assertFalse(self.m["authority_files_changed"])

    def test_017_12t(self): self.assertEqual(self.m["tooth_count"], 12)
    def test_018_phase(self): self.assertEqual(self.m["phase_degrees"], 15.0)
    def test_019_spacing(self): self.assertEqual(self.m["tooth_spacing_degrees"], 30.0)
    def test_020_source_radii(self): self.assertEqual((self.m["tooth_tip_radius"], self.m["tooth_root_radius"]), (33.07, 29.47))
    def test_021_source_widths(self): self.assertEqual((self.m["tooth_tip_width"], self.m["tooth_root_width"], self.m["tooth_axial_width"]), (7.5, 9.5, 44.0))
    def test_022_external_flag(self): self.assertFalse(self.m["external_tooth_geometry_changed"])
    def test_023_external_diff(self): self.assertLessEqual(max(self.m["parent_minus_final_external_volume"], self.m["final_minus_parent_external_volume"]), 1e-6)
    def test_024_external_bbox(self): self.assertEqual(self.m["parent_external_bbox"], self.m["final_external_bbox"])
    def test_024a_raw_bbox_within_kernel_tolerance(self): self.assertLessEqual(self.m["bbox_boolean_rounding_delta_max_mm"], self.m["bbox_comparison_tolerance_mm"])
    def test_025_all_variants_valid_single_solid(self):
        self.assertTrue(all(x["valid"] and x["solid_count"] == 1 for x in self.m["analysis"]["variants"].values()))
    def test_026_all_variant_external_diffs_zero(self):
        self.assertTrue(all(max(x["parent_minus_external_mm3"], x["final_minus_external_mm3"]) <= 1e-6 for x in self.m["analysis"]["variants"].values()))

    def test_027_front_angles(self): self.assertEqual(self.m["front_insert_angles"], [0, 180])
    def test_028_rear_angles(self): self.assertEqual(self.m["rear_insert_angles"], [90, 270])
    def test_029_alternating(self): self.assertTrue(self.m["analysis"]["insertion"]["alternating"])
    def test_030_no_continuous_fracture(self): self.assertFalse(self.m["analysis"]["insertion"]["continuous_fracture"])
    def test_031_layouts(self): self.assertEqual(self.m["axial_layout_variants"], {"C0": 0.0, "C15": 1.5, "C30": 3.0})
    def test_032_c0_preferred(self): self.assertEqual(self.m["analysis"]["layouts"]["C0"]["selection"], "PREFERRED_GEOMETRY")
    def test_033_c0_common_plane(self): self.assertTrue(self.m["analysis"]["layouts"]["C0"]["same_contact_plane"])
    def test_034_c15_spread(self): self.assertEqual(self.m["analysis"]["layouts"]["C15"]["axial_contact_spread_mm"], 3.0)
    def test_035_c30_spread(self): self.assertEqual(self.m["analysis"]["layouts"]["C30"]["axial_contact_spread_mm"], 6.0)
    def test_036_pockets_do_not_intersect(self): self.assertTrue(all(x["pocket_pairwise_max_mm3"] <= 1e-6 for x in self.m["analysis"]["layouts"].values()))

    def test_037_measured_nut(self): self.assertEqual((self.m["high_nut_af_measured"], self.m["high_nut_length_measured"]), (5.2, 13.0))
    def test_038_nut_count(self): self.assertEqual(self.m["high_nut_count"], 4)
    def test_039_af_grid(self): self.assertEqual(self.m["high_nut_af_candidates"], [5.1, 5.15, 5.2, 5.25, 5.3, 5.35])
    def test_040_depth_grid(self): self.assertEqual(self.m["high_nut_length_clearance_candidates"], [13.1, 13.2, 13.3])
    def test_041_coupon_solids(self): self.assertEqual((self.m["analysis"]["coupons"]["front_solid_count"], self.m["analysis"]["coupons"]["rear_solid_count"], self.m["analysis"]["coupons"]["washer_solid_count"]), (1, 1, 1))

    def test_042_m3x25(self): self.assertEqual((self.m["screw_size"], self.m["screw_length"], self.m["screw_count"]), ("M3", 25.0, 4))
    def test_043_head_is_conservative_envelope(self): self.assertEqual(self.m["screw_type"], "HEADED_GENERIC_ENVELOPE")
    def test_044_washer_od(self): self.assertEqual(self.m["washer_outer_diameter_measured"], 6.8)
    def test_045_washer_unknowns_hold(self): self.assertTrue(self.m["washer_inner_diameter_status"].startswith("HOLD") and self.m["washer_thickness_status"].startswith("HOLD"))
    def test_046_seat_candidates(self): self.assertEqual(self.m["washer_seat_diameter_candidates"], [7.0, 7.2])
    def test_047_washer_exceeds_root_gap(self): self.assertGreater(6.8, self.m["analysis"]["washer"]["root_gap_width_mm"])
    def test_048_neither_seat_fits_gap(self): self.assertTrue(all(not x["fits_intertooth_root_gap"] for x in self.m["analysis"]["washer"]["seat_candidates"].values()))
    def test_049_no_full_washer_support(self): self.assertFalse(self.m["analysis"]["washer"]["full_support"])
    def test_050_washer_link_conflict_detected(self): self.assertGreater(self.m["analysis"]["washer"]["washer_to_link_mm3"], 0)
    def test_051_m3_reach_depends_on_thickness(self): self.assertAlmostEqual(self.m["analysis"]["screw"]["required_washer_thickness_for_contact_mm"], 0.53, places=6)
    def test_052_provisional_m3_is_short(self): self.assertGreater(self.m["analysis"]["screw"]["provisional_shaft_gap_mm"], 0)
    def test_053_head_path_blocked(self): self.assertGreater(self.m["analysis"]["screw"]["head_path_blocked_by_preserved_body_mm3"], 0)
    def test_054_functional_cut_rejected(self): self.assertEqual(self.m["analysis"]["functional_head_path"]["status"], "REJECT_EXTERNAL_GEOMETRY_CHANGE")

    def test_055_reaction_wall(self): self.assertGreaterEqual(self.m["minimum_reaction_wall"], 3.0)
    def test_056_adjacent_wall(self): self.assertGreaterEqual(self.m["minimum_adjacent_pocket_wall"], 3.0)
    def test_057_m4_wall(self): self.assertGreaterEqual(self.m["minimum_pocket_to_m4_wall"], 3.0)
    def test_058_bore_wall(self): self.assertGreaterEqual(self.m["minimum_pocket_to_bore_wall"], 3.0)
    def test_059_retainer_contract(self): self.assertEqual((self.m["front_retainer"], self.m["rear_retainer"], self.m["retainer_fastener_count"], self.m["retainer_fastener_size"], self.m["retainer_pcd"]), (True, True, 4, "M4", 24.0))
    def test_059a_body_markings_modeled(self): self.assertEqual((self.m["marking_status"], set(self.m["body_markings"])), ("CAD_MODELED", {"H2.3", "V09372", "A1", "F", "R", "L/R COMMON", "P3AF26C2D", "BORE_CANDIDATE", "AXIAL_LAYOUT_CANDIDATE"}))
    def test_059b_retainer_markings_modeled(self): self.assertEqual(set(self.m["retainer_markings"]), {"F", "R", "A1", "V09372", "L/R"})
    def test_060_shaft_unmodified(self): self.assertFalse(self.m["shaft_irreversible_machining_required"])
    def test_061_generic_hardware(self): self.assertFalse(self.m["single_manufacturer_dependency"])

    def test_062_design_failure_is_explicit(self): self.assertTrue(self.m["design_status"].startswith("FAIL_"))
    def test_063_artifact_contract_passes(self): self.assertEqual(self.v["artifact_contract"], "PASS")
    def test_064_sprocket_print_blocked(self): self.assertEqual(self.m["print_release"], "COUPONS_ONLY_SPROCKET_STL_NOT_APPROVED")
    def test_065_no_physical_pass(self): self.assertNotIn("H2.3_PHYSICAL_FIT = PASS", self.docs)
    def test_066_power_not_approved(self): self.assertEqual(self.m["powered_rotation_status"], "NOT_APPROVED")
    def test_067_field_not_approved(self): self.assertEqual(self.m["field_deployment_status"], "NOT_APPROVED")
    def test_068_torque_not_tested(self): self.assertEqual(self.m["torque_capacity_status"], "NOT_TESTED")
    def test_069_spare_rate(self): self.assertEqual(self.m["petg_spare_rate_percent"], 100)
    def test_070_release_holds(self): self.assertEqual(self.m["release"]["GITHUB_MANUFACTURING_RELEASE"], "HOLD")
    def test_071_reference_registration_holds(self): self.assertTrue(all(x.startswith("HOLD") for x in self.m["analysis"]["references"].values()))

    def test_072_commit_paths_exact(self):
        self.assertEqual((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines(), [f"{B.LANE_REL}/{p}" for p in B.PATHS])
    def test_073_commit_paths_lane_only(self): self.assertTrue(all(x.startswith(B.LANE_REL + "/") for x in (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()))
    def test_074_parent_not_in_commit_paths(self): self.assertNotIn(B.PARENT_REL, (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8"))
    def test_075_docs_record_failure(self): self.assertIn("FAIL/HOLD", self.docs)
    def test_076_docs_record_coupon_only(self): self.assertIn("Coupon", self.docs)
    def test_077_docs_record_no_power(self): self.assertIn("POWERED_ROTATION = NOT_APPROVED", self.docs)

    def test_078_runtime_repository_guard(self): self.assertEqual(B.repo_audit(True)["status"], "PASS")
    def test_079_runtime_parent_guard(self): self.assertEqual(B.parent_audit()["status"], "PASS")

    def test_080_optional_zip_contract(self):
        zp = os.environ.get("V09372_TEST_ZIP")
        if not zp:
            self.skipTest("V09372_TEST_ZIP not set")
        path = Path(zp)
        self.assertTrue(path.is_file())
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            self.assertEqual(names, list(B.PATHS))
            self.assertEqual(len(names), len(set(names)))
            self.assertFalse(any(PurePosixPath(x).is_absolute() or ".." in PurePosixPath(x).parts or "\\" in x for x in names))
            self.assertEqual(z.testzip(), None)
            self.assertTrue(all(hashlib.sha256(z.read(p)).hexdigest() == sha(LANE / p) for p in names))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestH23Contract)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
