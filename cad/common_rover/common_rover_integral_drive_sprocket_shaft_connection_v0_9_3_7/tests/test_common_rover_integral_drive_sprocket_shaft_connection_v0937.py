#!/usr/bin/env python3
"""Contract tests for Common Rover v0.9.3.7 S0/H0 shaft-connection baseline."""
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
import build_common_rover_integral_drive_sprocket_shaft_connection_v0937 as b  # noqa: E402


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((LANE / "geometry_manifest.json").read_text(encoding="utf-8"))
        cls.validation = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.analysis = cls.manifest["analysis"]
        cls.source_trace = (LANE / "SOURCE_TRACE.md").read_text(encoding="utf-8")
        cls.readme = (LANE / "README.md").read_text(encoding="utf-8")
        cls.spec = (LANE / "DESIGN_SPEC.md").read_text(encoding="utf-8")
        cls.review = (LANE / "DESIGN_REVIEW.md").read_text(encoding="utf-8")
        cls.trade = (LANE / "SHAFT_CONNECTION_TRADE_STUDY.md").read_text(encoding="utf-8")

    def test_001_exact_formal_path_contract(self) -> None:
        self.assertEqual(32, len(b.PACKAGE_PATHS))
        self.assertEqual(sorted(b.PACKAGE_PATHS), b.lane_files())

    def test_002_repository_fail_closed_guard(self) -> None:
        result = b.repository_audit(True)
        self.assertEqual("PASS", result["status"])

    def test_003_parent_lanes_protected(self) -> None:
        result = b.protected_audit()
        self.assertEqual("PASS", result["status"])
        self.assertEqual(set(b.PROTECTED_LANES), set(result["lanes"]))

    def test_004_selected_source_protected(self) -> None:
        result = b.source_audit()
        self.assertEqual("PASS", result["status"])
        self.assertEqual(b.SOURCE_SNAPSHOT[1], result.get("ledger_sha256", b.SOURCE_SNAPSHOT[1]))

    def test_005_current_source_is_tracked_v0131(self) -> None:
        self.assertIn("v0.13.1 integrated sprocket generator", self.source_trace)
        self.assertEqual(b.SOURCE_CODE_SHA256, "9a15fbd05f2972090faba594e010c55b16b2fb226b2a944b8962bc398dbc268e")

    def test_006_separate_tooth_history_is_not_invented(self) -> None:
        self.assertIn("USER_REPORTED", self.source_trace)
        self.assertIn("HOLD_HISTORICAL_GENERATOR_NOT_PRESENT", self.source_trace)
        self.assertIn("not reconstructed by inference", self.source_trace)

    def test_007_source_is_already_integral(self) -> None:
        self.assertTrue(self.manifest["buried_root_extension_used"])
        self.assertFalse(self.manifest["buried_root_extension_dimensions"]["new_extension_added_by_v0937"])
        self.assertEqual("SOURCE_V0131_POSITIVE_VOLUME_EMBEDDED_ROOT_BOOLEAN_UNION_THEN_CLEAN", self.manifest["union_method"])

    def test_008_tooth_count_preserved(self) -> None:
        self.assertEqual(12, self.manifest["source_tooth_count"])
        self.assertEqual(12, self.manifest["final_tooth_count"])
        self.assertEqual(12, self.analysis["tooth"]["count"])

    def test_009_tooth_angles_preserved(self) -> None:
        expected = [15.0 + 30.0 * index for index in range(12)]
        self.assertEqual(expected, self.analysis["tooth"]["angles_deg"])
        self.assertEqual(30.0, self.analysis["tooth"]["spacing_deg"])

    def test_010_pitch_and_contact_parameters_preserved(self) -> None:
        self.assertEqual(self.manifest["source_pitch_parameter"], self.manifest["final_pitch_parameter"])
        self.assertEqual(44.0, self.manifest["final_tooth_axial_width"])
        self.assertEqual(7.5, self.manifest["final_tooth_tip_width"])

    def test_011_external_tooth_envelope_unchanged(self) -> None:
        tooth = self.analysis["tooth"]
        self.assertLessEqual(tooth["external_source_minus_final_mm3"], 1e-6)
        self.assertLessEqual(tooth["external_final_minus_source_mm3"], 1e-6)
        self.assertEqual(self.analysis["source"]["bounds_mm"], self.analysis["final_sprocket"]["bounds_mm"])

    def test_012_integral_sprocket_is_one_valid_solid(self) -> None:
        final = self.analysis["final_sprocket"]
        self.assertEqual(1, final["solid_count"])
        self.assertTrue(final["valid"])
        self.assertGreater(final["volume_mm3"], 0.0)

    def test_013_each_tooth_has_positive_buried_root_intersection(self) -> None:
        tooth = self.analysis["tooth"]
        self.assertGreaterEqual(tooth["body_intersection_per_tooth_mm3"], tooth["minimum_required_mm3"])

    def test_014_source_and_final_bores_are_explicit(self) -> None:
        self.assertEqual({"drive_through_bore_mm": 10.3}, self.manifest["source_bore_dimensions"])
        self.assertEqual(10.3, self.manifest["final_bore_dimensions"]["sprocket_through_bore_mm"])
        self.assertEqual(10.1, self.manifest["final_bore_dimensions"]["h0_clamp_bore_mm"])

    def test_015_h0_has_two_independent_valid_halves(self) -> None:
        h0 = self.analysis["h0"]
        self.assertEqual(2, h0["solid_count"])
        self.assertEqual(1, h0["top_solid_count"])
        self.assertEqual(1, h0["bottom_solid_count"])
        self.assertTrue(h0["top_valid"] and h0["bottom_valid"])
        self.assertLessEqual(h0["half_intersection_mm3"], 1e-6)

    def test_016_h0_split_gap_and_shaft_clearance(self) -> None:
        h0 = self.analysis["h0"]
        self.assertEqual(0.6, h0["split_gap_mm"])
        self.assertLessEqual(h0["shaft_top_intersection_mm3"], 1e-6)
        self.assertLessEqual(h0["shaft_bottom_intersection_mm3"], 1e-6)

    def test_017_h0_pilot_interface_is_provisional(self) -> None:
        self.assertEqual(15.0, self.manifest["pilot_diameter"])
        self.assertAlmostEqual(0.2, self.manifest["pilot_clearance"]["diametral_mm"])
        self.assertIn("PHYSICAL_TEST_REQUIRED", self.manifest["pilot_clearance"]["status"])

    def test_018_h0_clamp_hardware_contract(self) -> None:
        self.assertEqual("H0_TWO_PIECE_SPLIT_CLAMP_FLANGE", self.manifest["clamp_type"])
        self.assertEqual(2, self.manifest["clamp_bolt_count"])
        self.assertEqual("M5", self.manifest["clamp_bolt_size"])

    def test_019_axial_hardware_contract(self) -> None:
        self.assertEqual(4, self.manifest["axial_fastener_count"])
        self.assertEqual("M4", self.manifest["axial_fastener_size"])
        self.assertEqual(24.0, self.manifest["source_hub_dimensions"]["bolt_pcd_mm"])

    def test_020_fastener_clearance(self) -> None:
        h0 = self.analysis["h0"]
        self.assertLessEqual(h0["m5_shank_clamp_intersection_mm3"], 1e-6)
        self.assertLessEqual(h0["m4_shank_sprocket_hub_intersection_mm3"], 1e-6)

    def test_021_no_petg_tap_or_set_screw(self) -> None:
        self.assertFalse(self.manifest["direct_petg_set_screw_used"])
        self.assertIn("do not tap PETG", (LANE / "ASSEMBLY_INSTRUCTIONS.md").read_text(encoding="utf-8"))

    def test_022_no_irreversible_shaft_work(self) -> None:
        self.assertFalse(self.manifest["shaft_irreversible_machining_required"])
        for forbidden in ("D-flat", "cross-hole", "keyway"):
            self.assertIn(forbidden, self.readme)

    def test_023_torque_and_axial_retention_are_separated(self) -> None:
        self.assertIn("Torque and axial retention are separated", self.trade)
        self.assertIn("inner race", self.trade)

    def test_024_bearing_shield_collar_and_link_envelopes_clear(self) -> None:
        envelope = self.analysis["envelopes"]
        for key, value in envelope.items():
            if key.endswith("_mm3"):
                self.assertLessEqual(value, 1e-6, key)

    def test_025_bearing_stack_remains_measurement_hold(self) -> None:
        envelope = self.analysis["envelopes"]
        self.assertIn("HOLD_ACTUAL_STACK_MEASUREMENT_REQUIRED", envelope["bearing_axial_position"])
        self.assertEqual("PROVISIONAL_MEASUREMENT_REQUIRED", envelope["shield_od_status"])

    def test_026_bore_coupon_candidates_and_markings(self) -> None:
        coupon = self.analysis["coupon"]
        self.assertEqual([10.0, 10.1, 10.2], coupon["bores_mm"])
        self.assertEqual(1, coupon["solid_count"])
        self.assertEqual(["10.0", "10.1", "10.2", "S0 SHAFT FIT ONLY NO POWER"], coupon["markings"])

    def test_027_h1_is_parameter_hold_only(self) -> None:
        h1 = self.manifest["h1_metal_hub"]
        self.assertFalse(h1["verified_dimensions_found"])
        self.assertIsNone(h1["pilot_diameter_mm"])
        self.assertEqual("HOLD", h1["bolt_pattern_final"])
        self.assertEqual("HOLD", h1["manufacturing_release"])

    def test_028_axes_remain_concentric(self) -> None:
        axis = self.analysis["axis"]
        self.assertEqual([0.0, 0.0], axis["source_center_xy_mm"])
        self.assertEqual(axis["source_center_xy_mm"], axis["final_center_xy_mm"])
        self.assertEqual(axis["source_center_xy_mm"], axis["h0_center_xy_mm"])

    def test_029_all_step_artifacts_reload(self) -> None:
        result = b.verify_steps()
        self.assertEqual(9, result["count"])
        self.assertEqual(9, result["pass_count"])
        self.assertEqual("PASS", result["status"])

    def test_030_all_stl_artifacts_are_single_watertight_components(self) -> None:
        result = b.verify_stls()
        self.assertEqual(4, result["count"])
        self.assertEqual(4, result["pass_count"])
        for row in result["rows"]:
            self.assertTrue(row["watertight"])
            self.assertEqual(1, row["components"])
            self.assertEqual(0, row["degenerate_triangles"])

    def test_031_svg_artifacts_parse(self) -> None:
        result = b.verify_svgs()
        self.assertEqual(2, result["pass_count"])
        self.assertEqual("PASS", result["status"])

    def test_032_validation_report_passes_cad_only(self) -> None:
        self.assertEqual("PASS", self.validation["status"])
        self.assertEqual("REQUIRED", self.validation["physical_fit"])
        self.assertEqual("NOT_TESTED", self.validation["durability"])
        self.assertEqual("NOT_APPROVED", self.validation["powered_rotation"])

    def test_033_physical_plan_is_no_power_and_bidirectional(self) -> None:
        text = (LANE / "PHYSICAL_TEST_PLAN.md").read_text(encoding="utf-8")
        self.assertIn("no power", text)
        self.assertIn("forward 10 turns", text)
        self.assertIn("reverse 10 turns", text)
        self.assertIn("28. Recheck axial movement.", text)
        self.assertIn("witness marks", text)

    def test_034_hardware_bom_keeps_lengths_on_hold(self) -> None:
        text = (LANE / "HARDWARE_BOM.md").read_text(encoding="utf-8")
        self.assertIn("CANDIDATE_LENGTH_HOLD", text)
        self.assertIn("STANDARD_LENGTH_SELECTION_HOLD", text)
        self.assertIn("PRODUCT_SELECTION_HOLD", text)

    def test_035_release_prohibitions_are_canonical(self) -> None:
        combined = self.readme + self.review + self.trade
        self.assertIn("Powered rotation", combined)
        self.assertIn("not approved", combined)
        self.assertIn("GITHUB_MANUFACTURING_RELEASE = HOLD", combined)
        self.assertIn("SHAFT_IRREVERSIBLE_MACHINING = NOT_APPROVED", combined)

    def test_036_manifest_exact_and_ordered(self) -> None:
        result = b.verify_manifest()
        self.assertEqual(32, result["entry_count"])
        self.assertTrue(result["exact_order"])

    def test_037_sha256_ledger_exact(self) -> None:
        result = b.verify_hashes()
        self.assertEqual(31, result["verified"])
        self.assertEqual([], result["mismatches"])
        self.assertEqual("PASS", result["status"])

    def test_038_commit_paths_are_exact_lane_scope(self) -> None:
        actual = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
        expected = [f"{b.LANE_REL}/{path}" for path in b.PACKAGE_PATHS]
        self.assertEqual(expected, actual)

    def test_039_no_authority_change_claim(self) -> None:
        self.assertFalse(self.manifest["authority_files_changed"])
        self.assertEqual("NOT_APPROVED", self.manifest["powered_rotation_status"])

    def test_040_optional_handoff_zip_contract(self) -> None:
        value = os.environ.get("V0937_TEST_ZIP")
        if not value:
            self.skipTest("V0937_TEST_ZIP not provided")
        path = Path(value)
        self.assertTrue(path.is_file())
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(list(b.PACKAGE_PATHS), archive.namelist())
            hashes = {}
            for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
                digest, rel = line.split("  ", 1)
                hashes[rel] = digest
            for rel, expected in hashes.items():
                self.assertEqual(expected, hashlib.sha256(archive.read(rel)).hexdigest(), rel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
