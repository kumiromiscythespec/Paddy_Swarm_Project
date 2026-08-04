from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import re
import sys
import unittest
import zipfile
from pathlib import Path, PurePosixPath


LANE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v0934_builder", LANE / "build_powertrain_frame_joint_trade_study_v0934.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import v0.9.3.4 builder")
B = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = B
SPEC.loader.exec_module(B)


def rows(name: str) -> list[dict[str, str]]:
    with (LANE / name).open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class V0934Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.params = json.loads((LANE / "frame_joint_parameters_v0934.json").read_text(encoding="utf-8"))
        cls.collisions = rows("candidate_collision_matrix_v0934.csv")
        cls.dimensions = rows("candidate_dimension_report_v0934.csv")
        cls.sweep = rows("crossmember_y_sweep_v0934.csv")

    def test_001_identity(self) -> None:
        self.assertEqual(B.DOCUMENT_ID, "PS-CR-V0934-POWERTRAIN-FRAME-JOINT-TRADE-STUDY")
        self.assertEqual(B.VERSION, "0.9.3.4")

    def test_002_anchor_exists_and_is_ancestor(self) -> None:
        if not B.live_repository():
            self.skipTest("standalone embedded evidence")
        B.git("cat-file", "-e", f"{B.ANCHOR}^{{commit}}")
        self.assertEqual(B.run(["git", "merge-base", "--is-ancestor", B.ANCHOR, "HEAD"]).returncode, 0)

    def test_003_repository_guard(self) -> None:
        self.assertEqual(B.repository_audit(require_complete=True)["status"], "PASS")

    def test_004_parent_lanes_unchanged(self) -> None:
        audit = B.parent_audit()
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(set(audit["parents"]), {"v0.9.3.0", "v0.9.3.1", "v0.9.3.3"})

    def test_005_source_reference_hashes(self) -> None:
        audit = B.source_reference_audit()
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(len(audit["rows"]), 13)
        self.assertTrue(all(row["pass"] for row in audit["rows"]))

    def test_006_authority_unchanged(self) -> None:
        self.assertEqual(self.params["approval"]["authority_update"], "NOT_APPROVED")
        if B.live_repository():
            self.assertEqual({rel: B.sha256(B.REPO_ROOT / rel) for rel in B.AUTHORITY_POINTER_HASHES}, B.AUTHORITY_POINTER_HASHES)

    def test_007_reference_zip_sha256(self) -> None:
        audit = B.reference_zip_audit()
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["sha256"], "2832a60935e508f8287abf6d89576ae9f01a8e59926a242e599713cbba0e04a5")

    def test_008_motor_plate_physical_status(self) -> None:
        self.assertEqual(self.params["approval"]["motor_plate_v0933_print"], "LATEST_PHYSICAL_TEST_REPORTED")
        self.assertEqual(self.params["approval"]["motor_plate_physical_fit"], "PHYSICAL_PASS_NO_LOAD")
        self.assertEqual(self.params["approval"]["m5x16"], "PHYSICAL_PASS_NO_LOAD")
        self.assertEqual(self.params["approval"]["creep_test_24h"], "REQUIRED_BEFORE_BELT_TENSION")
        self.assertEqual(self.params["approval"]["powered_m5x16"], "NOT_APPROVED")

    def test_009_frame_width_exact(self) -> None:
        frame = self.params["frame"]
        self.assertEqual(frame["outer_width_x_mm"], 180.0)
        self.assertEqual(frame["outer_boundary_x_mm"], [-90.0, 90.0])

    def test_010_powertrain_clear_width_exact(self) -> None:
        self.assertEqual(self.params["frame"]["powertrain_clear_width_x_mm"], 100.0)
        self.assertEqual((self.params["frame"]["left_inner_face_x_mm"], self.params["frame"]["right_inner_face_x_mm"]), (-50.0, 50.0))

    def test_011_side_rail_positions_exact(self) -> None:
        frame = self.params["frame"]
        self.assertEqual((frame["left_rail_center_x_mm"], frame["right_rail_center_x_mm"]), (-70.0, 70.0))
        self.assertEqual(frame["side_rail_width_x_mm"], 40.0)

    def test_012_profile_is_conservative_proxy(self) -> None:
        frame = self.params["frame"]
        self.assertEqual(frame["profile_exact_section"], "MEASUREMENT_HOLD")
        self.assertEqual(frame["profile_orientation"], "PHYSICAL_CONFIRMATION_REQUIRED")

    def test_013_frame_proxy_bounds(self) -> None:
        shape = B.compound(B.frame_shapes())
        bounds = B.bounds(shape)
        self.assertEqual(bounds["xlen"], 180.0)
        self.assertEqual(bounds["ylen"], 240.0)
        self.assertEqual(bounds["zlen"], 20.0)

    def test_014_baseline_intrusion_and_remaining_width(self) -> None:
        baseline = self.params["baseline"]
        self.assertEqual(baseline["inner_corner_intrusion_per_side_mm"], 27.9)
        self.assertAlmostEqual(baseline["remaining_width_mm"], 44.2)
        self.assertEqual(baseline["status"], "REJECT_CANDIDATE_IN_POWERTRAIN_ZONE")

    def test_015_candidate_a_contract(self) -> None:
        a = self.params["candidate_a"]
        self.assertEqual(a["id"], "CROSSMEMBER_END_TAP_OUTBOARD_BOLT")
        self.assertFalse(a["inner_bracket"])
        self.assertEqual(a["central_intrusion_mm"], 0.0)
        self.assertEqual(a["crossmember_span_mm"], 100.0)

    def test_016_candidate_a_separated_envelopes(self) -> None:
        shapes = B.candidate_a_fastener_shapes()
        self.assertEqual(len(shapes), 16)
        self.assertEqual(self.params["candidate_a"]["end_tap_thread_size"], "MEASUREMENT_HOLD")

    def test_017_candidate_a_widths(self) -> None:
        a = self.params["candidate_a"]
        self.assertEqual(a["fixed_width_candidate_mm"], {"M5": 190.0, "M6": 192.0})
        self.assertEqual(a["temporary_tool_width_candidate_mm"], {"M5": 250.0, "M6": 252.0})
        self.assertLess(max(a["temporary_tool_width_candidate_mm"].values()), 290.0)

    def test_018_candidate_a_anti_rotation_hold(self) -> None:
        a = self.params["candidate_a"]
        self.assertEqual(a["one_bolt_anti_rotation"], "SECONDARY_MEASURE_REQUIRED")
        self.assertEqual(a["two_bolt_layout"], "PROFILE_MEASUREMENT_HOLD")

    def test_019_candidate_b_contract(self) -> None:
        b = self.params["candidate_b"]
        self.assertEqual(b["id"], "UNDERSIDE_3MM_FULL_WIDTH_TIE_PLATE")
        self.assertFalse(b["inner_bracket"])
        self.assertEqual(b["central_upper_intrusion_mm"], 0.0)
        self.assertEqual(b["crossmember_span_mm"], 100.0)
        self.assertEqual(b["plate_mm"], [180.0, 40.0, 3.0])

    def test_020_candidate_b_drop_hold(self) -> None:
        b = self.params["candidate_b"]
        self.assertEqual(b["plate_only_drop_mm"], 3.0)
        self.assertEqual(b["fastener_head_drop_mm"], "MEASUREMENT_HOLD")
        self.assertEqual(b["total_underside_drop"], "3.0_PLUS_FASTENER_HEAD_ENVELOPE")

    def test_021_tie_plate_geometry(self) -> None:
        for shape in B.tie_plate_shapes():
            bounds = B.bounds(shape)
            self.assertEqual((bounds["xlen"], bounds["ylen"], bounds["zlen"]), (180.0, 40.0, 3.0))
            self.assertEqual(bounds["zmin"], -3.0)

    def test_022_tie_plate_environment_collisions_zero(self) -> None:
        selected = [row for row in self.collisions if row["candidate"] == "B_TIE_PLATE" and row["target"] in ("CBOX", "BBOX", "TRACK")]
        self.assertEqual(len(selected), 3)
        self.assertTrue(all(float(row["intersection_volume_mm3"]) == 0.0 and row["status"] == "PASS" for row in selected))

    def test_023_mud_and_drainage_remain_hold(self) -> None:
        report = (LANE / "candidate_b_tie_plate_report_v0934.md").read_text(encoding="utf-8")
        self.assertIn("mud/straw retention", report)
        self.assertIn("drainage", report)
        self.assertIn("physical mockup", report)

    def test_024_actual_physical_dimensions(self) -> None:
        p = self.params["physical_result"]
        self.assertTrue(p["latest_physical_result"])
        self.assertEqual(p["petg_plate_thickness_mm"], 6.0)
        self.assertEqual((p["minimum_gap_mm"], p["maximum_gap_mm"], p["gap_range_mm"]), (4.3, 4.5, 0.2))
        self.assertEqual(p["derived_nominal_gap_mm"], 4.4)
        self.assertEqual((p["minimum_plate_top_height_mm"], p["maximum_plate_top_height_mm"], p["derived_nominal_plate_top_height_mm"]), (10.3, 10.5, 10.4))
        self.assertEqual(p["individual_corner_gaps_mm"], "NOT_REPORTED_IN_LATEST_OVERRIDE")

    def test_024a_latest_two_washer_one_nut_stack(self) -> None:
        p = self.params["physical_result"]
        self.assertEqual(p["additional_plain_washer_count_per_m5"], 2)
        self.assertEqual(p["height_adjustment_nut_count_per_m5"], 1)
        self.assertEqual(p["top_adjustment_nut"], "NOT_USED_IN_LATEST_STACK")
        self.assertEqual((p["top_plain_washer"], p["bottom_adjustment_nut"], p["bottom_plain_washer"]), ("USED", "USED", "USED"))
        self.assertEqual(p["direct_hex_nut_contact_to_aluminum"], "NOT_USED_IN_LATEST_STACK")
        self.assertEqual(len(p["actual_m5_stack_top_to_bottom"]), 8)

    def test_025_actual_fasteners_and_alignment(self) -> None:
        p = self.params["physical_result"]
        self.assertEqual((p["m3_fastener"], p["m5_fastener"]), ("M3x16", "M5x16"))
        self.assertEqual(p["height_adjustment_nut_count_per_m5"], 1)
        self.assertEqual(p["m3_hole_alignment"], "PHYSICAL_PASS")
        self.assertEqual(p["m5_hole_alignment"], "PHYSICAL_PASS")
        self.assertEqual(p["motor_bracket_alignment"], "PHYSICAL_PASS")
        self.assertEqual(p["motor_bracket_seating"], "PHYSICAL_PASS_NO_LOAD")

    def test_026_plate_damage_none(self) -> None:
        p = self.params["physical_result"]
        self.assertEqual({p["plate_rocking"], p["plate_visible_warp"], p["local_indentation"], p["m5_area_whitening"]}, {"NONE"})
        self.assertEqual(p["aluminum_frame_indentation"], "NONE")
        self.assertEqual(p["aluminum_protection_result"], "PASS")
        self.assertEqual(p["four_point_levelness"], "PHYSICAL_PASS_NO_LOAD")

    def test_027_m5_engagement_no_invented_mm(self) -> None:
        p = self.params["physical_result"]
        self.assertEqual(p["m5x16_thread_engagement"], "FULL_TNUT_THREAD_TRAVERSAL_USER_REPORTED")
        self.assertEqual(p["tnut_thread_traversal_result"], "PHYSICAL_PASS_USER_REPORTED")
        self.assertEqual(p["m5_thread_pitch"], "MEASUREMENT_HOLD")
        self.assertEqual(p["m5_engagement_length_mm"], "NOT_CALCULATED")
        text = (LANE / "actual_motor_plate_physical_result_v0934.md").read_text(encoding="utf-8")
        self.assertIn("engagement length in millimetres is `NOT_CALCULATED`", text)

    def test_028_height_cases_all_evaluated(self) -> None:
        values = rows("height_case_report_v0934.csv")
        self.assertEqual({row["height_case"] for row in values}, {B.ACTUAL_HEIGHT_CASE, B.PREVIOUS_HEIGHT_CASE, "H6", "H8", "H10"})
        actual = next(row for row in values if row["height_case"] == B.ACTUAL_HEIGHT_CASE)
        previous = next(row for row in values if row["height_case"] == B.PREVIOUS_HEIGHT_CASE)
        self.assertEqual((float(actual["motor_shaft_z_mm"]), float(actual["20T_pulley_z_mm"]), float(actual["60T_pulley_z_mm"])), (115.4, 115.4, 166.0))
        self.assertEqual(float(actual["vertical_center_difference_mm"]), 50.6)
        self.assertEqual(actual["physical_selection"], "PRIMARY_ACTUAL")
        self.assertEqual(previous["physical_selection"], "HISTORICAL_SUPERSEDED")

    def test_024_powertrain_motor_collision_zero(self) -> None:
        values = [row for row in self.collisions if row["target"] == "motor"]
        self.assertEqual(len(values), 2)
        self.assertTrue(all(float(row["intersection_volume_mm3"]) == 0.0 for row in values))

    def test_024b_actual_plate_fastener_spacer_collision_zero(self) -> None:
        values = [row for row in self.collisions if row["target"] in ("8hole_plate", "M3_fastener", "M5_fastener", "spacer_nut")]
        self.assertEqual(len(values), 8)
        self.assertTrue(all(row["height_case"] == B.ACTUAL_HEIGHT_CASE and float(row["intersection_volume_mm3"]) == 0.0 for row in values))

    def test_025_powertrain_pulley_collisions_zero(self) -> None:
        values = [row for row in self.collisions if row["target"] in ("20T_pulley", "60T_pulley")]
        self.assertEqual(len(values), 4)
        self.assertTrue(all(float(row["intersection_volume_mm3"]) == 0.0 for row in values))

    def test_026_powertrain_belt_collisions_zero(self) -> None:
        values = [row for row in self.collisions if row["target"] == "belt"]
        self.assertEqual(len(values), 2)
        self.assertTrue(all(float(row["intersection_volume_mm3"]) == 0.0 for row in values))

    def test_027_powertrain_guard_collisions_zero(self) -> None:
        values = [row for row in self.collisions if row["target"] == "fixed_guard"]
        self.assertEqual(len(values), 2)
        self.assertTrue(all(float(row["intersection_volume_mm3"]) == 0.0 for row in values))

    def test_028_service_sweep_is_separate(self) -> None:
        values = [row for row in self.collisions if row["target"] == "service_sweep"]
        self.assertEqual(len(values), 2)
        self.assertTrue(all(row["collision_class"] == "SERVICE" and row["fixed_clearance_mm"] == "SEPARATE" for row in values))

    def test_029_y_sweep_performed_at_5mm(self) -> None:
        self.assertEqual(len(self.sweep), 255)
        fronts = sorted({float(row["front_crossmember_center_y_mm"]) for row in self.sweep})
        self.assertTrue(all(round(fronts[i + 1] - fronts[i], 6) == 5.0 for i in range(len(fronts) - 1)))

    def test_030_minimum_viable_frame(self) -> None:
        row = next(row for row in self.sweep if row["status"] == "MINIMUM_VIABLE")
        self.assertEqual((float(row["front_crossmember_center_y_mm"]), float(row["rear_crossmember_center_y_mm"])), (-280.0, -90.0))
        self.assertEqual(float(row["frame_length_mm"]), 230.0)
        self.assertEqual(float(row["minimum_fixed_clearance_mm"]), 10.0)
        self.assertEqual(float(row["minimum_service_clearance_mm"]), 5.0)

    def test_031_target_frame(self) -> None:
        row = next(row for row in self.sweep if row["status"] == "TARGET")
        self.assertEqual((float(row["front_crossmember_center_y_mm"]), float(row["rear_crossmember_center_y_mm"])), (-285.0, -85.0))
        self.assertEqual(float(row["frame_length_mm"]), 240.0)
        self.assertEqual(float(row["minimum_fixed_clearance_mm"]), 15.0)
        self.assertEqual(float(row["minimum_service_clearance_mm"]), 10.0)

    def test_032_limiting_component_and_service(self) -> None:
        row = next(row for row in self.sweep if row["status"] == "TARGET")
        self.assertEqual(row["limiting_component"], "60T_FIXED_GUARD_PROXY")
        self.assertEqual(row["limiting_service_operation"], "BELT_REMOVAL_AND_GUARD_TOOL_SWEEP")
        self.assertEqual(row["extra_length_relative_to_current_mockup_mm"], "MEASUREMENT_HOLD")

    def test_033_repairability_scores(self) -> None:
        values = rows("repairability_score_v0934.csv")
        totals = {row["candidate"]: int(row["weighted_score"]) for row in values if row["criterion"] == "TOTAL"}
        self.assertEqual(totals, {candidate: sum(scores.values()) for candidate, scores in B.REPAIR_SCORES.items()})
        self.assertTrue(all(row["hard_fail_override"] == "NO_CURRENT_HARD_FAIL" for row in values))

    def test_034_trade_recommendation(self) -> None:
        self.assertEqual(self.params["recommendation"], "A_AND_B_PHYSICAL_MOCKUP_REQUIRED")
        trade = rows("candidate_trade_matrix_v0934.csv")
        self.assertEqual(len(trade), 2)
        self.assertTrue(all(row["hard_status"] == "CONDITIONAL_PASS" for row in trade))

    def test_035_fallback_not_modeled(self) -> None:
        self.assertEqual(self.params["fallback"]["status"], "NOT_MODELED_UNLESS_A_AND_B_HARD_FAIL")
        self.assertFalse(any("FALLBACK" in path for path in B.STEP_FILES))

    def test_036_left_right_independence(self) -> None:
        architecture = self.params["architecture"]
        self.assertTrue(architecture["left_right_independent_power"])
        self.assertFalse(architecture["common_left_right_shaft"])

    def test_037_exact_step_count_and_reload(self) -> None:
        self.assertEqual(len(B.STEP_FILES), 24)
        report = B.verify_steps()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["pass_count"], report["count"]), (24, 24))

    def test_038_exact_svg_count_and_validity(self) -> None:
        self.assertEqual(len(B.SVG_FILES), 19)
        report = B.verify_svgs()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["pass_count"], report["count"]), (19, 19))

    def test_039_actual_physical_artifacts_present(self) -> None:
        self.assertEqual(len(B.PHYSICAL_ACTUAL_FILES), 5)
        self.assertTrue(all((LANE / rel).is_file() for rel in B.PHYSICAL_ACTUAL_FILES))

    def test_039b_m5x16_m5x20_plan(self) -> None:
        comparison = self.params["m5_length_comparison"]
        self.assertEqual(comparison["M5x16"]["thread_engagement"], "FULL_TNUT_THREAD_TRAVERSAL_USER_REPORTED")
        self.assertEqual(comparison["M5x16"]["no_load_result"], "PHYSICAL_PASS")
        self.assertEqual(comparison["M5x16"]["engagement_length_mm"], "NOT_CALCULATED")
        self.assertEqual(comparison["M5x20"]["expected_engagement"], "MUST_NOT_BE_INVENTED")
        self.assertEqual(comparison["M5x20"]["priority"], "LOWERED_BUT_NOT_CANCELLED")
        self.assertEqual(comparison["M5x25"]["status"], "LENGTH_HOLD")

    def test_039c_previous_physical_result_preserved(self) -> None:
        history = self.params["physical_result"]["previous_physical_result"]
        self.assertEqual(history["status"], "HISTORICAL_PHYSICAL_RESULT")
        self.assertEqual(history["supersession"], "SUPERSEDED_BY_TWO_WASHER_ONE_NUT_STACK")
        self.assertEqual(history["gaps_mm"], {"left_front": 3.8, "right_front": 3.9, "left_rear": 3.9, "right_rear": 3.9})
        self.assertEqual(history["m5_engagement_turns_approx"], 2.5)

    def test_040_csv_parse_contract(self) -> None:
        self.assertEqual(len(B.CSV_FILES), 8)
        report = B.verify_csvs()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["pass_count"], report["count"]), (8, 8))

    def test_041_physical_mockup_steps(self) -> None:
        text = (LANE / "physical_mockup_plan_v0934.md").read_text(encoding="utf-8")
        a, remainder = text.split("## Candidate B", 1)
        b, remainder = remainder.split("## 24-hour creep check", 1)
        creep, _ = remainder.split("## M5×20 comparison", 1)
        self.assertEqual(len(re.findall(r"(?m)^\d+\. ", a)), 9)
        self.assertEqual(len(re.findall(r"(?m)^\d+\. ", b)), 10)
        self.assertEqual(len(re.findall(r"(?m)^\d+\. ", creep)), 10)
        self.assertEqual(text.count("Finish without applying power"), 3)
        self.assertIn("REQUIRED_BEFORE_BELT_TENSION", text)

    def test_042_no_release_or_power(self) -> None:
        approval = self.params["approval"]
        self.assertEqual(approval["frame_joint_cad"], "TRADE_STUDY_ONLY")
        self.assertEqual(approval["powered_rotation"], "NOT_APPROVED")
        self.assertEqual(approval["belt_tension"], "NOT_APPROVED")
        self.assertEqual(approval["torque_load"], "NOT_APPROVED")
        self.assertEqual(approval["field_deployment"], "NOT_APPROVED")
        self.assertEqual(approval["powered_m5x16"], "NOT_APPROVED")
        no_release = (LANE / "NO_MANUFACTURING_RELEASE.txt").read_text(encoding="utf-8")
        self.assertIn("PETG_PLATE_NO_LOAD_RESULT=PASS", no_release)
        self.assertIn("TWO_WASHER_ONE_NUT_STACK=PHYSICAL_PASS_NO_LOAD", no_release)
        self.assertIn("24H_CREEP_TEST=REQUIRED_BEFORE_BELT_TENSION", no_release)
        self.assertIn("POWERED_M5X16=NOT_APPROVED", no_release)

    def test_043_exact_69_package_paths(self) -> None:
        self.assertEqual(len(B.PACKAGE_PATHS), 69)
        self.assertEqual((len(B.STEP_FILES), len(B.SVG_FILES), len(B.CSV_FILES)), (24, 19, 8))
        expected = sorted(B.EXPECTED_LANE_PATHS) if B.live_repository() else sorted(B.PACKAGE_PATHS)
        self.assertEqual(B.lane_files(), expected)
        self.assertEqual(len(B.LEGACY_PRESERVED_PATHS), 17)

    def test_044_commit_paths_v0934_only(self) -> None:
        values = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
        prefix = "cad/common_rover/common_rover_powertrain_frame_joint_trade_study_v0_9_3_4/"
        self.assertEqual(len(values), 69)
        self.assertTrue(all(value.startswith(prefix) for value in values))
        self.assertEqual([value[len(prefix):] for value in values], list(B.PACKAGE_PATHS))

    def test_045_manifest_and_hashes(self) -> None:
        manifest = B.verify_manifest(); hashes = B.verify_hashes()
        self.assertEqual(manifest["status"], "PASS")
        self.assertEqual(manifest["entry_count"], 69)
        self.assertEqual(hashes["status"], "PASS")
        self.assertEqual(hashes["verified"], 68)

    def test_046_machine_evidence(self) -> None:
        self.assertEqual(B.verify_evidence()["status"], "PASS")

    def test_047_builder_verify(self) -> None:
        report = B.verify()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["exact_package_paths"], 69)

    def test_048_csv_artifact_tool_marker_in_package(self) -> None:
        if not os.environ.get("V0934_TEST_ZIP"):
            self.skipTest("package marker checked during ZIP verification")
        text = (LANE / "test_results_v0934.txt").read_text(encoding="utf-8")
        self.assertIn("csv_import_render=PASS_ARTIFACT_TOOL_8_OF_8", text)

    def test_049_zip_standalone_contract_when_requested(self) -> None:
        value = os.environ.get("V0934_TEST_ZIP")
        if not value:
            self.skipTest("V0934_TEST_ZIP not set")
        path = Path(value)
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            self.assertEqual(names, list(B.PACKAGE_PATHS))
            self.assertEqual(len(names), len(set(names)))
            self.assertFalse(any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name for name in names))
            hashes = {}
            for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
                if line.strip():
                    expected, rel = line.split("  ", 1); hashes[rel] = expected
            self.assertEqual(set(hashes), set(B.PACKAGE_PATHS) - {"SHA256SUMS.txt"})
            self.assertTrue(all(hashlib.sha256(archive.read(rel)).hexdigest() == expected for rel, expected in hashes.items()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
