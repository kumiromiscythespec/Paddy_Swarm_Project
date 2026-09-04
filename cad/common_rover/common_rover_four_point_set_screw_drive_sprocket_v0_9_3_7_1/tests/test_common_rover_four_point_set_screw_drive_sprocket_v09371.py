#!/usr/bin/env python3
"""Contract tests for Common Rover H2 v0.9.3.7.1."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import unittest
import zipfile
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))
import build_common_rover_four_point_set_screw_drive_sprocket_v09371 as b  # noqa: E402


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((LANE / "geometry_manifest.json").read_text(encoding="utf-8"))
        cls.validation = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.analysis = cls.manifest["analysis"]
        cls.docs = {path: (LANE / path).read_text(encoding="utf-8") for path in b.ROOT_FILES if path.endswith(".md")}

    def test_001_exact_formal_paths(self) -> None:
        self.assertEqual(44, len(b.PACKAGE_PATHS))
        self.assertEqual(44, len(set(b.PACKAGE_PATHS)))
        self.assertEqual(sorted(b.PACKAGE_PATHS), b.lane_files())

    def test_002_repository_guard(self) -> None:
        self.assertEqual("PASS", b.repository_audit(True)["status"])

    def test_003_parent_lane_byte_protection(self) -> None:
        result = b.parent_audit()
        self.assertEqual("PASS", result["status"])
        self.assertEqual(b.PARENT_SNAPSHOT[1], result.get("ledger_sha256", b.PARENT_SNAPSHOT[1]))

    def test_004_authority_protection(self) -> None:
        self.assertEqual("PASS", b.authority_audit()["status"])
        self.assertFalse(self.manifest["authority_files_changed"])

    def test_005_parent_and_source_trace(self) -> None:
        trace = self.docs["SOURCE_TRACE.md"]
        self.assertEqual(b.PARENT_REL, self.manifest["parent_lane"])
        self.assertIn(b.PARENT_SNAPSHOT[1], trace)
        self.assertIn(b.SOURCE_SHA256, trace)

    def test_006_h0_physical_failure_is_recorded(self) -> None:
        self.assertEqual("USER_REPORTED", self.manifest["physical_failure"]["classification"])
        self.assertEqual("PHYSICAL_FAIL_SLIP", self.manifest["physical_failure"]["result"])
        self.assertEqual("REJECT_TORQUE_TRANSMISSION", self.manifest["h0_status"])

    def test_007_h2_has_no_physical_pass(self) -> None:
        self.assertEqual("PHYSICAL_TEST_REQUIRED", self.manifest["h2_status"])
        self.assertEqual("REQUIRED", self.manifest["physical_test_status"])
        self.assertNotIn("PHYSICAL_PASS", json.dumps(self.manifest))

    def test_008_tooth_count_phase_spacing(self) -> None:
        self.assertEqual(12, self.manifest["tooth_count"])
        self.assertEqual(15.0, self.manifest["phase_degrees"])
        self.assertEqual(30.0, self.manifest["tooth_spacing_degrees"])
        self.assertEqual([15.0 + 30.0 * i for i in range(12)], self.analysis["tooth"]["angles_deg"])

    def test_009_tooth_dimensions_preserved(self) -> None:
        self.assertEqual(33.07, self.manifest["tooth_tip_radius"])
        self.assertEqual(29.47, self.manifest["tooth_root_radius"])
        self.assertEqual(7.5, self.manifest["tooth_tip_width"])
        self.assertEqual(9.5, self.manifest["tooth_root_width"])
        self.assertEqual(44.0, self.manifest["tooth_axial_width"])
        self.assertEqual(76.3943726841, self.manifest["pitch_diameter_record"])

    def test_010_positive_root_union_preserved(self) -> None:
        self.assertGreaterEqual(self.analysis["tooth"]["positive_root_intersection_mm3"], 100.0)

    def test_011_external_geometry_difference_zero(self) -> None:
        self.assertFalse(self.manifest["external_tooth_geometry_changed"])
        for row in self.analysis["variants"].values():
            self.assertLessEqual(row["parent_minus_final_external_mm3"], 1e-6)
            self.assertLessEqual(row["final_minus_parent_external_mm3"], 1e-6)

    def test_012_external_bounding_box_preserved(self) -> None:
        self.assertEqual(self.manifest["parent_external_bbox"], self.manifest["final_external_bbox"])
        for row in self.analysis["variants"].values():
            self.assertEqual(self.analysis["parent"]["bounds_mm"], row["bounds_mm"])

    def test_013_three_bore_variants(self) -> None:
        self.assertEqual({"H2-B101": 10.1, "H2-B102": 10.2, "H2-B103": 10.3}, self.manifest["bore_variants"])
        self.assertEqual(set(self.manifest["bore_variants"]), set(self.analysis["variants"]))

    def test_014_all_sprockets_are_one_valid_solid(self) -> None:
        for row in self.analysis["variants"].values():
            self.assertEqual(1, row["solid_count"])
            self.assertTrue(row["valid"])
            self.assertGreater(row["volume_mm3"], 0.0)

    def test_015_four_high_nuts_cardinal_axes(self) -> None:
        self.assertEqual("M3", self.manifest["high_nut_thread"])
        self.assertEqual(4, self.manifest["high_nut_count"])
        self.assertEqual([0.0, 90.0, 180.0, 270.0], self.manifest["high_nut_axes_degrees"])
        self.assertEqual(4, self.analysis["high_nut"]["count"])

    def test_016_all_high_nuts_share_axial_plane(self) -> None:
        self.assertEqual(18.9, self.analysis["high_nut"]["center_z_mm"])

    def test_017_opposing_pairs_and_symmetry(self) -> None:
        axes = self.manifest["high_nut_axes_degrees"]
        self.assertEqual(180.0, axes[2] - axes[0])
        self.assertEqual(180.0, axes[3] - axes[1])
        self.assertEqual(90.0, axes[1] - axes[0])

    def test_018_high_nut_dimensions_remain_unconfirmed(self) -> None:
        self.assertEqual(5.2, self.manifest["high_nut_af_default"])
        self.assertEqual(9.8, self.manifest["high_nut_length_default"])
        self.assertEqual("USER_REPORTED_UNCONFIRMED_DIMENSION", self.manifest["high_nut_af_status"])
        self.assertEqual("USER_REPORTED_UNCONFIRMED_DIMENSION", self.manifest["high_nut_length_status"])

    def test_019_six_pocket_coupon_candidates(self) -> None:
        expected = [5.1, 5.15, 5.2, 5.25, 5.3, 5.35]
        self.assertEqual(expected, self.manifest["high_nut_af_candidates"])
        self.assertEqual(expected, self.analysis["coupon"]["af_candidates_mm"])
        self.assertEqual(1, self.analysis["coupon"]["solid_count"])
        self.assertTrue(self.analysis["coupon"]["valid"])

    def test_020_coupon_loading_pushout_and_m3_access(self) -> None:
        coupon = self.analysis["coupon"]
        self.assertTrue(coupon["same_axial_loading_direction"])
        self.assertEqual(6, coupon["pushout_access_count"])
        self.assertEqual(6, coupon["m3_access_count"])
        self.assertEqual(["AF5.10", "AF5.15", "AF5.20", "AF5.25", "AF5.30", "AF5.35"], coupon["engraved_markings"])

    def test_021_pocket_selection_is_physical_hold(self) -> None:
        self.assertEqual(5.25, self.analysis["high_nut"]["selected_pocket_af_mm"])
        self.assertEqual("PHYSICAL_COUPON_REQUIRED", self.analysis["high_nut"]["selected_status"])

    def test_022_high_nuts_and_pockets_do_not_intersect_each_other(self) -> None:
        high = self.analysis["high_nut"]
        self.assertLessEqual(high["pairwise_max_intersection_mm3"], 1e-6)
        self.assertLessEqual(high["pocket_pairwise_max_intersection_mm3"], 1e-6)

    def test_023_high_nuts_fit_pockets(self) -> None:
        self.assertLessEqual(self.analysis["high_nut"]["nut_to_h2_body_mm3"], 1e-6)

    def test_024_pockets_clear_m4_holes(self) -> None:
        self.assertLessEqual(self.analysis["high_nut"]["pocket_to_m4_hole_mm3"], 1e-6)

    def test_025_minimum_reaction_walls(self) -> None:
        high = self.analysis["high_nut"]
        self.assertGreaterEqual(high["outer_wall_min_mm"], 3.0)
        self.assertGreaterEqual(high["adjacent_pocket_wall_min_mm"], 3.0)
        self.assertGreaterEqual(high["m4_hole_wall_min_mm"], 3.0)

    def test_026_m3x16_contract(self) -> None:
        self.assertEqual("M3", self.manifest["set_screw_size"])
        self.assertEqual(4, self.manifest["set_screw_count"])
        self.assertEqual(16.0, self.manifest["set_screw_length"])
        self.assertIn("CUP_POINT", self.manifest["set_screw_tip_type"])

    def test_027_retracted_screws_clear_shaft(self) -> None:
        self.assertLessEqual(self.analysis["set_screw"]["RETRACTED"]["shaft_intersection_mm3"], 1e-6)
        self.assertGreater(self.analysis["set_screw"]["RETRACTED"]["tip_radius_mm"], 5.0)

    def test_028_initial_and_nominal_reach_shaft_surface(self) -> None:
        self.assertEqual(5.0, self.analysis["set_screw"]["INITIAL_CONTACT"]["tip_radius_mm"])
        self.assertEqual(4.9375, self.analysis["set_screw"]["NOMINAL_CLAMPED"]["tip_radius_mm"])
        self.assertEqual(0.0625, self.analysis["set_screw_state_contract"]["nominal_preload_travel_mm"])
        self.assertGreater(self.analysis["set_screw"]["NOMINAL_CLAMPED"]["shaft_intersection_mm3"], 0.0)
        self.assertIn("CONCEPTUAL", self.analysis["set_screw_state_contract"]["classification"])

    def test_029_set_screws_pass_body_and_nuts(self) -> None:
        for row in self.analysis["set_screw"].values():
            self.assertLessEqual(row["h2_body_intersection_mm3"], 1e-6)
            self.assertLessEqual(row["nut_intersection_mm3"], 1e-6)

    def test_030_set_screws_clear_link_guide_bearing(self) -> None:
        for row in self.analysis["set_screw"].values():
            self.assertLessEqual(row["link_intersection_mm3"], 1e-6)
            self.assertLessEqual(row["guide_intersection_mm3"], 1e-6)
            self.assertLessEqual(row["bearing_intersection_mm3"], 1e-6)

    def test_031_four_tool_envelopes_clear_local_geometry(self) -> None:
        tool = self.analysis["tool"]
        self.assertEqual(4, tool["count"])
        for key, value in tool.items():
            if key.endswith("_mm3"):
                self.assertLessEqual(value, 1e-6, key)

    def test_032_installed_frame_tool_access_is_not_falsely_passed(self) -> None:
        self.assertEqual("HOLD_INSTALLED_FRAME_TOOL_ENVELOPE_REGISTRATION_REQUIRED", self.analysis["tool"]["frame_status"])

    def test_033_retainer_interface_contract(self) -> None:
        self.assertEqual(4, self.manifest["retainer_fastener_count"])
        self.assertEqual("M4", self.manifest["retainer_fastener_size"])
        self.assertEqual(24.0, self.manifest["retainer_pcd"])
        self.assertEqual([2.5, 3.0], self.manifest["retainer_plate_thickness_candidates"])

    def test_034_retainer_solids_valid_and_nonintersecting(self) -> None:
        row = self.analysis["retainer"]
        self.assertEqual(1, row["t2p5_solid_count"])
        self.assertEqual(1, row["t3p0_solid_count"])
        self.assertTrue(row["t2p5_valid"] and row["t3p0_valid"])
        self.assertLessEqual(row["h2_intersection_mm3"], 1e-6)
        self.assertLessEqual(row["nut_intersection_mm3"], 1e-6)

    def test_035_retainer_drainage_and_coverage(self) -> None:
        row = self.analysis["retainer"]
        self.assertEqual(4, row["drain_count"])
        self.assertLessEqual(row["covers_radial_interval_mm"][0], b.HIGH_NUT_RADIAL_INNER_MM)
        self.assertGreaterEqual(row["covers_radial_interval_mm"][1], b.HIGH_NUT_RADIAL_INNER_MM + b.HIGH_NUT_LENGTH_USER_REPORTED_MM)
        self.assertEqual(["H2-4P", "A1", "V09371", "P14FB", "L/R"], row["engraved_markings"])

    def test_036_bearing_link_and_guide_envelopes_clear(self) -> None:
        for key, value in self.analysis["envelopes"].items():
            if key.endswith("_mm3"):
                self.assertLessEqual(value, 1e-6, key)

    def test_037_no_irreversible_shaft_machining(self) -> None:
        self.assertFalse(self.manifest["shaft_irreversible_machining_required"])
        combined = "\n".join(self.docs.values())
        self.assertIn("unmodified round shaft", combined)

    def test_038_no_single_manufacturer_dependency(self) -> None:
        self.assertFalse(self.manifest["single_manufacturer_dependency"])
        self.assertIn("generic", self.docs["HARDWARE_BOM.md"].lower())

    def test_039_assembly_sequence_is_exact(self) -> None:
        text = self.docs["ASSEMBLY_INSTRUCTIONS.md"]
        positions = [text.index(value) for value in ("Bring A1", "Bring A2", "Bring B1", "Bring B2", "Turn A1, A2, B1, B2")]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("1/8 turn", text)

    def test_040_petg_spare_rule(self) -> None:
        self.assertEqual(100, self.manifest["petg_spare_rate_percent"])
        text = self.docs["PETG_SPARE_PART_RULE.md"]
        self.assertIn("REQUIRED", text)
        self.assertIn("four H2 sprockets and four retainers", text)

    def test_041_metal_migration_interface(self) -> None:
        text = self.docs["METAL_MIGRATION_INTERFACE.md"]
        for value in ("M3x16", "0/90/180/270", "A1/A2/B1/B2", "unmodified shaft", "4xM4 PCD24"):
            self.assertIn(value, text)
        self.assertIn("No metal material", text)

    def test_042_release_states(self) -> None:
        release = self.manifest["release"]
        self.assertEqual("HOLD", release["GITHUB_EXECUTABLE_CAD_RELEASE"])
        self.assertEqual("HOLD", release["GITHUB_MANUFACTURING_RELEASE"])
        self.assertEqual("PHYSICAL_FAIL", release["H0_TORQUE_TRANSMISSION"])
        self.assertEqual("REQUIRED", release["H2_PHYSICAL_FIT"])
        self.assertEqual("NOT_TESTED", release["H2_TORQUE_CAPACITY"])
        self.assertEqual("NOT_APPROVED", self.manifest["powered_rotation_status"])
        self.assertEqual("NOT_APPROVED", self.manifest["field_deployment_status"])

    def test_043_all_steps_reload(self) -> None:
        result = b.verify_steps()
        self.assertEqual(11, result["count"])
        self.assertEqual(11, result["pass_count"])
        self.assertEqual("PASS", result["status"])

    def test_044_all_stls_are_single_watertight_components(self) -> None:
        result = b.verify_stls()
        self.assertEqual(6, result["count"])
        self.assertEqual(6, result["pass_count"])
        for row in result["rows"]:
            self.assertTrue(row["watertight"])
            self.assertEqual(1, row["components"])
            self.assertEqual(0, row["degenerate_triangles"])

    def test_045_svgs_parse(self) -> None:
        result = b.verify_svgs()
        self.assertEqual(4, result["count"])
        self.assertEqual(4, result["pass_count"])

    def test_046_validation_is_cad_pass_only(self) -> None:
        self.assertEqual("PASS", self.validation["status"])
        self.assertEqual("REQUIRED", self.validation["physical_fit"])
        self.assertEqual("NOT_TESTED", self.validation["torque_capacity"])
        self.assertEqual("NOT_APPROVED", self.validation["powered_rotation"])

    def test_047_manifest_and_hash_ledgers(self) -> None:
        manifest = b.verify_manifest(); hashes = b.verify_hashes()
        self.assertEqual(44, manifest["entry_count"])
        self.assertTrue(manifest["exact_order"])
        self.assertEqual(43, hashes["verified"])
        self.assertEqual([], hashes["mismatches"])

    def test_048_commit_paths_are_exact_new_lane_only(self) -> None:
        actual = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
        expected = [f"{b.LANE_REL}/{path}" for path in b.PACKAGE_PATHS]
        self.assertEqual(expected, actual)
        self.assertFalse(any(b.PARENT_REL in path for path in actual))

    def test_049_optional_handoff_zip(self) -> None:
        value = os.environ.get("V09371_TEST_ZIP")
        if not value:
            self.skipTest("V09371_TEST_ZIP not provided")
        path = Path(value)
        self.assertTrue(path.is_file())
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(list(b.PACKAGE_PATHS), archive.namelist())
            values = {}
            for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
                digest, rel = line.split("  ", 1); values[rel] = digest
            for rel, expected in values.items():
                self.assertEqual(expected, hashlib.sha256(archive.read(rel)).hexdigest(), rel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
