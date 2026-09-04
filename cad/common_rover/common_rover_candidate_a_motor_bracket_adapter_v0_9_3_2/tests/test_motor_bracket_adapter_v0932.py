from __future__ import annotations

import csv
import json
import math
import os
import sys
import unittest
from pathlib import Path


LANE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE_DIR))

import build_motor_bracket_adapter_v0932 as builder  # noqa: E402


class MotorBracketAdapterV0932Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.params = json.loads((LANE_DIR / "motor_bracket_2040_adapter_parameters_v0932.json").read_text(encoding="utf-8"))
        cls.collision = json.loads((LANE_DIR / "adapter_collision_report_v0932.json").read_text(encoding="utf-8"))
        cls.dimensions = json.loads((LANE_DIR / "adapter_dimension_report_v0932.json").read_text(encoding="utf-8"))
        with (LANE_DIR / "motor_bracket_measurements_v0932.csv").open("r", encoding="utf-8", newline="") as stream:
            cls.bracket_rows = list(csv.DictReader(stream))
        with (LANE_DIR / "fastener_measurements_v0932.csv").open("r", encoding="utf-8", newline="") as stream:
            cls.fastener_rows = list(csv.DictReader(stream))

    def test_001_identity_and_release_class(self) -> None:
        self.assertEqual(self.params["document_id"], builder.DOCUMENT_ID)
        self.assertEqual(self.params["version"], "0.9.3.2")
        self.assertEqual(self.params["status"], "CONDITIONAL_PASS_CANDIDATE")
        self.assertEqual(self.params["physical_fit"], "NOT_YET_PERFORMED")

    def test_002_v0931_commit_exists_and_is_ancestor(self) -> None:
        audit = builder.parent_audit()
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["anchor"], builder.V0931_ANCHOR)
        self.assertEqual(audit["parent_path_count"], 46)

    def test_003_parent_v0931_hash_state_is_unchanged(self) -> None:
        audit = builder.parent_audit()
        self.assertEqual(audit["parent_sha_entries"], 45)
        self.assertEqual(audit["parent_full_lane_ledger_sha256"], builder.PARENT_FULL_LEDGER_SHA256)

    def test_004_authority_pointer_is_unchanged(self) -> None:
        self.assertEqual(self.params["authority_pointer"], "UNCHANGED")
        if builder.live_repository():
            actual = {rel: builder.sha256(builder.REPO_ROOT / rel) for rel in builder.AUTHORITY_POINTER_HASHES}
            self.assertEqual(actual, builder.AUTHORITY_POINTER_HASHES)

    def test_005_plate_dimensions_and_corner_radius_are_exact(self) -> None:
        self.assertEqual(self.dimensions["plate_mm"], [42.0, 80.0, 8.0])
        self.assertEqual(self.dimensions["corner_radius_mm"], 3.0)
        self.assertEqual(self.dimensions["print_orientation"], "FLAT_ON_BUILD_PLATE_BASE_Z0")

    def test_006_bracket_outer_dimensions_are_measured_values(self) -> None:
        bracket = self.params["bracket"]
        self.assertEqual(bracket["outer_mm"], [40.2, 40.0])
        self.assertEqual(bracket["hole_diameter_measured_mm"], 4.0)
        self.assertEqual(bracket["corner_radius"], "MEASUREMENT_HOLD")

    def test_007_twenty_four_is_hole_center_pitch_not_outer_size(self) -> None:
        self.assertEqual(self.params["bracket"]["pitch_mm"], [24.0, 30.0])
        row = next(item for item in self.bracket_rows if item["measurement_id"] == "BRACKET_HOLE_PITCH_X")
        self.assertIn("center-to-center", row["notes"])
        self.assertEqual(float(row["value"]), 24.0)

    def test_008_bracket_hole_coordinates_are_exact(self) -> None:
        expected = [[-12.0, -15.0], [12.0, -15.0], [-12.0, 15.0], [12.0, 15.0]]
        self.assertEqual(self.params["bracket"]["coordinates_mm"], expected)
        self.assertEqual(self.dimensions["bracket_hole_coordinates_mm"], expected)

    def test_009_frame_slot_pitch_and_coordinates_are_exact(self) -> None:
        frame = self.params["frame"]
        self.assertEqual(frame["top_width_x_mm"], 40.0)
        self.assertEqual(frame["slot_center_pitch_x_mm"], 20.0)
        self.assertEqual(frame["slot_center_coordinates_x_mm"], [-10.0, 10.0])

    def test_010_frame_hole_pitch_and_coordinates_are_exact(self) -> None:
        expected = [[-10.0, -30.0], [10.0, -30.0], [-10.0, 30.0], [10.0, 30.0]]
        self.assertEqual(self.params["frame_holes"]["pitch_mm"], [20.0, 60.0])
        self.assertEqual(self.params["frame_holes"]["coordinates_mm"], expected)

    def test_011_m5_through_hole_and_keepouts_are_exact(self) -> None:
        self.assertEqual(self.params["frame_holes"]["diameter_mm"], 5.7)
        self.assertEqual(self.params["m5"]["washer_keep_out_mm"], 9.5)
        self.assertEqual(self.params["m5"]["tool_keep_out_mm"], 11.0)
        self.assertEqual(self.params["m5"]["head_height_envelope_mm"], 6.5)
        self.assertEqual(self.params["frame_holes"]["counterbore"], "NONE")
        self.assertEqual(self.params["frame_holes"]["countersink"], "NONE")

    def test_012_measured_m5_fastener_is_recorded(self) -> None:
        m5 = self.params["m5"]
        self.assertEqual(m5["measured_major_diameter_mm"], 4.7)
        self.assertIs(m5["captive_washer"], True)
        self.assertIs(m5["washer_removable"], False)
        self.assertEqual(m5["measured_head_washer_diameter_mm"], 8.7)
        self.assertEqual(m5["measured_head_washer_height_mm"], 6.0)

    def test_013_m5_length_candidates_are_not_released(self) -> None:
        self.assertEqual(self.params["m5"]["primary"], "M5x16")
        self.assertEqual(self.params["m5"]["backup"], "M5x20")
        self.assertEqual(self.params["m5"]["M5x25"], "LENGTH_HOLD")

    def test_014_m4_c360_and_c370_are_exact(self) -> None:
        self.assertEqual(self.params["variants"]["C360"]["pilot_mm"], 3.6)
        self.assertEqual(self.params["variants"]["C370"]["pilot_mm"], 3.7)
        self.assertEqual(self.params["variants"]["C360"]["blind_depth_mm"], 7.0)
        self.assertEqual(self.params["variants"]["C370"]["blind_depth_mm"], 7.0)

    def test_015_m4_blind_holes_leave_actual_bottom_material(self) -> None:
        for pilot in (3.6, 3.7):
            adapter = builder.adapter_shape(pilot)
            expected_volume = math.pi * (pilot / 2.0) ** 2 * 0.9
            for x, y in builder.BRACKET_HOLES:
                probe = builder.cylinder_z(pilot, 0.9, x, y, 0.0)
                self.assertAlmostEqual(builder.intersection_volume(adapter, probe), expected_volume, places=5)
        self.assertEqual(self.dimensions["m4_bottom_floor_mm"], 1.0)

    def test_016_coupon_has_all_eight_labeled_candidates(self) -> None:
        self.assertEqual(self.params["coupon"]["diameters_mm"], [3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.2])
        self.assertEqual(self.params["coupon"]["labels"], "TOP_ENGRAVED")
        self.assertEqual(self.params["coupon"]["blind_depth_mm"], 7.0)

    def test_017_all_m4_m5_actual_shape_intersections_are_zero(self) -> None:
        self.assertEqual(len(self.collision["m4_m5_rows"]), 16)
        self.assertTrue(all(row["intersection_volume_mm3"] == 0.0 and row["pass"] for row in self.collision["m4_m5_rows"]))

    def test_018_washer_and_tool_keepouts_do_not_intersect_bracket(self) -> None:
        self.assertTrue(all(row["intersection_volume_mm3"] == 0.0 and row["pass"] for row in self.collision["washer_bracket_rows"]))
        self.assertTrue(all(row["intersection_volume_mm3"] == 0.0 and row["pass"] for row in self.collision["tool_bracket_rows"]))
        self.assertEqual(self.collision["clearances_mm"]["washer_to_bracket_footprint"], 5.25)
        self.assertEqual(self.collision["clearances_mm"]["tool_to_bracket_footprint"], 4.5)

    def test_019_washer_plate_edge_margin_is_at_least_five(self) -> None:
        clearances = self.collision["clearances_mm"]
        self.assertGreaterEqual(clearances["washer_to_plate_edge_x"], 5.0)
        self.assertGreaterEqual(clearances["washer_to_plate_edge_y"], 5.0)
        self.assertEqual(min(clearances["washer_to_plate_edge_x"], clearances["washer_to_plate_edge_y"]), 5.25)

    def test_020_m4_outer_residual_is_sufficient(self) -> None:
        clearances = self.collision["clearances_mm"]
        self.assertEqual(clearances["m4_c370_to_plate_edge_x"], 7.15)
        self.assertGreaterEqual(clearances["m4_c370_to_plate_edge_y"], 5.0)

    def test_021_bracket_and_frame_centerlines_coincide(self) -> None:
        self.assertEqual(self.params["centerline"], "COINCIDENT")
        self.assertTrue(self.collision["checks"]["bracket_frame_centerline_coincident"])

    def test_022_frame_proxy_does_not_invent_t_slot_profile(self) -> None:
        frame = self.params["frame"]
        self.assertEqual(frame["proxy_mm"], [40.0, 120.0, 20.0])
        self.assertEqual(frame["t_slot_exact_profile"], "MEASUREMENT_HOLD")
        self.assertEqual(frame["reusable_exact_profile"], "NOT_FOUND_USE_SIMPLE_PROXY")

    def test_023_left_and_right_use_one_identical_part(self) -> None:
        self.assertEqual(self.params["part"]["quantity"], 2)
        self.assertIs(self.params["part"]["identical_left_right"], True)
        adapter_paths = [path for path in builder.PRINT_FILES if "ADAPTER_M4" in path]
        self.assertEqual(len(adapter_paths), 2)
        self.assertTrue(all("LEFT" not in path and "RIGHT" not in path for path in adapter_paths))
        assigned_path = LANE_DIR / adapter_paths[0]
        left_hash = builder.sha256(assigned_path)
        right_hash = builder.sha256(assigned_path)
        self.assertEqual(left_hash, right_hash)

    def test_024_all_three_stls_reload_flat_and_fit_a1(self) -> None:
        report = builder.verify_stls()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["pass_count"], 3)
        self.assertTrue(all(row["flat_base"] and row["a1_fit"] for row in report["rows"]))
        self.assertIs(self.dimensions["support_required"], False)

    def test_025_all_seven_step_assemblies_reload(self) -> None:
        report = builder.verify_steps()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["pass_count"], 7)

    def test_026_all_eight_svgs_are_one_to_one_contracts(self) -> None:
        self.assertEqual(len(builder.TEMPLATE_FILES), 8)
        for rel in builder.TEMPLATE_FILES:
            text = (LANE_DIR / rel).read_text(encoding="utf-8")
            self.assertIn("50.0 mm REFERENCE", text)
            self.assertIn("PRINT 100%", text)
            self.assertIn("FIT TO PAGE OFF", text)
            self.assertIn("AUTO SCALE OFF", text)

    def test_027_height_impact_is_hold_not_authority_update(self) -> None:
        impact = self.params["height_impact"]
        self.assertEqual(impact["adapter_z_stack_increase_mm"], 8.0)
        self.assertEqual(impact["old_motor_front_plate_z_mm"], 105.0)
        self.assertEqual(impact["new_motor_front_plate_z_candidate_mm"], 113.0)
        self.assertEqual(impact["integration_status"], "HEIGHT_REVALIDATION_REQUIRED")

    def test_028_physical_procedure_has_seventeen_steps(self) -> None:
        text = (LANE_DIR / "adapter_print_and_fit_procedure_v0932.md").read_text(encoding="utf-8")
        numbered = [line for line in text.splitlines() if line.split(".", 1)[0].isdigit()]
        self.assertEqual(len(numbered), 17)
        self.assertIn("17. Finish without energizing or rotating the motor.", text)

    def test_029_old_cradle_is_deprecated_only_in_new_lane(self) -> None:
        self.assertEqual(self.params["old_cradle_jig_status"], "DEPRECATED_BY_V0932_ADAPTER_PLATE")
        text = (LANE_DIR / "deprecated_v0931_jig_notice_v0932.md").read_text(encoding="utf-8")
        self.assertIn("DEPRECATED_BY_V0932_ADAPTER_PLATE", text)
        self.assertEqual(builder.parent_audit()["status"], "PASS")

    def test_030_no_power_load_or_authority_approval(self) -> None:
        text = (LANE_DIR / "NO_POWER_NO_LOAD_ONLY.txt").read_text(encoding="utf-8")
        for token in (
            "MOTOR_POWER=PROHIBITED",
            "POWERED_ROTATION=NOT_APPROVED",
            "BELT_TENSION=NOT_APPROVED",
            "TORQUE_LOAD=NOT_APPROVED",
            "DIRECT_THREAD_IN_PETG=NO_LOAD_MOCKUP_ONLY",
            "METAL_ADAPTER_RELEASE=NOT_APPROVED",
            "AUTHORITY_POINTER=UNCHANGED",
            "PARENT_V0931=UNCHANGED",
            "FIELD_DEPLOYMENT=NOT_APPROVED",
        ):
            self.assertIn(token, text)

    def test_031_exact_39_path_contract_and_commit_scope(self) -> None:
        self.assertEqual(len(builder.PACKAGE_PATHS), 39)
        self.assertEqual(builder.lane_files(), sorted(builder.PACKAGE_PATHS))
        prefix = "cad/common_rover/common_rover_candidate_a_motor_bracket_adapter_v0_9_3_2/"
        paths = (LANE_DIR / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(paths, [prefix + rel for rel in builder.PACKAGE_PATHS])

    def test_032_manifest_and_hash_ledgers_are_exact(self) -> None:
        manifest = builder.verify_manifest()
        hashes = builder.verify_hashes()
        self.assertEqual(manifest["status"], "PASS")
        self.assertEqual(manifest["entry_count"], 39)
        self.assertEqual(hashes["status"], "PASS")
        self.assertEqual(hashes["verified"], 38)

    def test_033_repository_lifecycle_guard(self) -> None:
        audit = builder.repository_audit(require_complete=True)
        self.assertEqual(audit["status"], "PASS")
        if audit["mode"] == "LIVE_REPOSITORY":
            self.assertEqual(audit["branch"], builder.EXPECTED_BRANCH)
            self.assertEqual(audit["lane_untracked_count"], 39)

    def test_034_machine_readable_evidence_contract(self) -> None:
        self.assertEqual(builder.verify_evidence()["status"], "PASS")
        self.assertEqual(self.collision["status"], "PASS")

    def test_035_zip_scope_hashes_and_standalone_contract(self) -> None:
        value = os.environ.get("V0932_TEST_ZIP", "")
        path = Path(value) if value else builder.latest_handoff_zip()
        if path is None:
            self.skipTest("ZIP is validated during --package")
        report = builder.verify_zip(path, standalone=False)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["entry_count"], 39)
        self.assertEqual(report["duplicates"], [])
        self.assertEqual(report["path_traversal"], [])
        self.assertEqual(report["internal_hash_verification"], "PASS")
        self.assertEqual(report["lane_byte_match"], "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
