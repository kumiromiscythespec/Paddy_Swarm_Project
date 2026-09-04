#!/usr/bin/env python3
"""Contract tests for Common Rover v0.9.1."""

from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import cadquery as cq


LANE_DIR = Path(__file__).resolve().parents[1]
BUILDER_PATH = LANE_DIR / "build_common_rover_outboard_inward_pto_v091.py"
SPEC = importlib.util.spec_from_file_location("common_rover_v091_builder", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load v0.9.1 builder")
B = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)


def load_json(name: str):
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def load_csv(name: str):
    with (LANE_DIR / name).open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class CommonRoverV091Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parameters = load_json(B.PARAMETERS_NAME)
        cls.baseline = load_json(B.BASELINE_NAME)
        cls.graph = load_json(B.POWER_GRAPH_NAME)
        cls.report = load_json(B.INTERFERENCE_REPORT_NAME)
        cls.validation = load_json(B.VALIDATION_NAME)
        cls.candidates = load_csv(B.POD_CANDIDATES_NAME)

    def test_001_exact_thirty_seven_paths(self):
        actual = sorted(
            path.relative_to(LANE_DIR).as_posix()
            for path in LANE_DIR.rglob("*")
            if path.is_file()
        )
        self.assertEqual(sorted(B.PACKAGE_PATHS), actual)
        self.assertEqual(37, len(actual))

    def test_002_parent_v008_to_v090_protection(self):
        audit = B.parent_protection_audit()
        self.assertEqual([], audit["mismatches"])
        self.assertIn(audit["v008_to_v0085_checked_path_count"], (0, 124))
        self.assertIn(audit["v090_checked_path_count"], (0, 38))
        self.assertEqual(B.PARENT_V090_LEDGER_SHA256, audit["v090_ledger_sha256"])
        self.assertEqual(B.PARENT_ZIP_SHA256, audit["v090_zip_sha256"])

    def test_003_v090_baseline_reproduced(self):
        self.assertEqual("PASS", self.baseline["baseline_reproduction"])
        self.assertEqual(
            "S4-B-PTOX040.0-Z320.0-FX40.0-FY20.0-FZ20.0",
            self.baseline["recommended_candidate_id"],
        )
        self.assertEqual(320.0, self.baseline["pto_axis_z_mm"])
        self.assertEqual(290.0, self.baseline["total_width_mm"])
        self.assertEqual({"left": "+Y", "right": "-Y"}, self.baseline["pto_output_direction"])

    def test_004_repository_scope_and_pointer_gate(self):
        audit = B.repository_audit()
        if audit["mode"] == "REPOSITORY":
            self.assertEqual(set(B.TRACKED_POINTER_PATHS), set(audit["tracked_diff"]))
            self.assertEqual([], audit["staged_diff"])
            self.assertEqual(37, audit["lane_untracked_count"])
            self.assertEqual("V091", audit["pointer_authority"])
        else:
            self.assertEqual("EMBEDDED_V091", audit["pointer_authority"])

    def test_005_two_motors_and_inward_shafts(self):
        fixed = self.parameters["fixed_contract"]
        self.assertEqual(2, fixed["motor_count"])
        self.assertEqual({"left": "-Y", "right": "+Y"}, fixed["motor_axis_direction"])

    def test_006_two_inward_independent_ptos(self):
        fixed = self.parameters["fixed_contract"]
        self.assertEqual(2, fixed["pto_port_count"])
        self.assertEqual({"left": "-Y", "right": "+Y"}, fixed["pto_output_direction"])
        self.assertIn("INDEPENDENT", fixed["pto_architecture"])
        self.assertEqual("PROHIBITED", fixed["common_pto_shaft"])
        self.assertEqual("PROHIBITED", fixed["third_pto_motor"])

    def test_007_slide_clutch_contract(self):
        fixed = self.parameters["fixed_contract"]
        self.assertEqual(2, fixed["slide_clutch_count"])
        self.assertEqual(["DRIVE", "NEUTRAL", "PTO"], fixed["slide_clutch_states"])
        self.assertEqual("MECHANICALLY_PROHIBITED", fixed["drive_pto_simultaneous"])
        self.assertEqual("PROHIBITED", fixed["switch_while_motor_rotating"])

    def test_008_four_separate_belts(self):
        belt = self.parameters["belt"]
        self.assertEqual(2, belt["drive_count"])
        self.assertEqual(2, belt["pto_count"])
        self.assertEqual(4, belt["total_count"])
        self.assertEqual(0, belt["twist_count"])

    def test_009_architecture_b_retained(self):
        self.assertTrue(self.parameters["fixed_contract"]["architecture"].startswith("B_"))

    def test_010_pto_same_plane_and_x_separation(self):
        rec = self.parameters["recommended"]
        self.assertEqual(
            rec["pto_20t_center_xyz_mm"][1],
            rec["pto_60t_center_xyz_mm"][1],
        )
        self.assertGreaterEqual(rec["pto_x_offset_from_motor_mm"], 80.0)

    def test_011_power_graph_drive_left_and_right(self):
        edges = self.graph["states"]["DRIVE"]["edges"]
        self.assertIn(["LEFT_MOTOR", "LEFT_SLIDE_CLUTCH"], edges)
        self.assertIn(["LEFT_TRACK_SHAFT", "LEFT_TRACK"], edges)
        self.assertIn(["RIGHT_MOTOR", "RIGHT_SLIDE_CLUTCH"], edges)
        self.assertIn(["RIGHT_TRACK_SHAFT", "RIGHT_TRACK"], edges)
        self.assertFalse(self.graph["states"]["DRIVE"]["pto_output_reachable"])

    def test_012_power_graph_pto_left_and_right(self):
        edges = self.graph["states"]["PTO"]["edges"]
        self.assertIn(["LEFT_PTO_SHAFT", "LEFT_INWARD_PTO_OUTPUT"], edges)
        self.assertIn(["RIGHT_PTO_SHAFT", "RIGHT_INWARD_PTO_OUTPUT"], edges)
        self.assertFalse(self.graph["states"]["PTO"]["track_output_reachable"])

    def test_013_neutral_has_no_output(self):
        self.assertEqual([], self.graph["states"]["NEUTRAL"]["edges"])
        self.assertFalse(self.graph["states"]["NEUTRAL"]["pto_output_reachable"])
        self.assertFalse(self.graph["states"]["NEUTRAL"]["track_output_reachable"])

    def test_014_no_left_right_power_edge(self):
        pto_edges = self.graph["states"]["PTO"]["edges"]
        self.assertNotIn(["LEFT_INWARD_PTO_OUTPUT", "RIGHT_INWARD_PTO_OUTPUT"], pto_edges)
        self.assertNotIn(["RIGHT_INWARD_PTO_OUTPUT", "LEFT_INWARD_PTO_OUTPUT"], pto_edges)

    def test_015_search_stage_order_and_counts(self):
        counts = self.parameters["search"]["stage_counts"]
        for stage in range(0, 10):
            self.assertGreater(counts[f"stage_{stage}"], 0)
        self.assertEqual(0, counts["stage_10"])
        self.assertEqual(len(self.candidates), self.parameters["search"]["candidate_count"])

    def test_016_stage_one_simple_flip_rejected(self):
        row = next(row for row in self.candidates if row["candidate_id"] == "S1-V090-FLIP-INWARD-ONLY")
        self.assertEqual("FAIL_ENVELOPE_CONTRACT", row["status"])
        self.assertIn("CENTRAL_BAY_NOT_DEFINED", row["rejection_reason"])

    def test_017_recommended_candidate_present(self):
        rec = self.parameters["recommended"]
        self.assertEqual(B.RECOMMENDED["candidate_id"], rec["candidate_id"])
        matches = [
            row
            for row in self.candidates
            if row["candidate_id"] == B.RECOMMENDED["candidate_id"]
        ]
        self.assertEqual(1, len(matches))
        self.assertEqual("CONDITIONAL_PASS_CANDIDATE", matches[0]["status"])
        ids = {row["candidate_id"] for row in self.candidates}
        self.assertTrue(all(item["candidate_id"] in ids for item in B.ALTERNATIVES))

    def test_018_motor_sensitivity_all_three(self):
        rows = load_csv(B.MOTOR_SENSITIVITY_NAME)
        self.assertEqual(
            {"MOTOR_SMALL", "MOTOR_MEDIUM", "MOTOR_LARGE"},
            {row["motor_envelope"] for row in rows},
        )
        self.assertTrue(all(row["fits_under_300"] == "True" for row in rows))
        self.assertTrue(
            all(
                row["authority"] == "PARAMETRIC_ENVELOPE_NOT_PRODUCT_DIMENSION"
                for row in rows
            )
        )

    def test_019_frame_sections_real_dimensions(self):
        rows = load_csv(B.FRAME_SECTIONS_NAME)
        a = next(row for row in rows if row["candidate_id"] == "FRAME-E-F2040-A")
        b = next(row for row in rows if row["candidate_id"] == "FRAME-E-F2040-B")
        self.assertEqual(("20.0", "40.0"), (a["y_thickness_mm"], a["z_height_mm"]))
        self.assertEqual(("40.0", "20.0"), (b["y_thickness_mm"], b["z_height_mm"]))
        self.assertEqual("RECOMMENDED", a["selection"])
        self.assertEqual("FAIL_BELT_FIXED_CLEARANCE", b["status"])

    def test_020_l_bracket_full_envelopes(self):
        rows = load_csv(B.L_BRACKETS_NAME)
        self.assertEqual(12, len(rows))
        self.assertEqual({"L_SMALL", "L_MEDIUM", "L_LARGE"}, {row["bracket"] for row in rows})
        large = next(row for row in rows if row["candidate_id"] == "L_LARGE-FORE_AFT_X")
        self.assertEqual(("40.0", "40.0", "5.0"), (large["leg_length_mm"], large["width_mm"], large["thickness_mm"]))
        self.assertGreaterEqual(float(large["tool_rotation_radius_mm"]), 18.0)

    def test_021_belt_layouts_b1_to_b5(self):
        rows = load_csv(B.BELT_PLANES_NAME)
        self.assertEqual({"B1", "B2", "B3", "B4", "B5"}, {row["candidate_id"] for row in rows})
        b1 = next(row for row in rows if row["candidate_id"] == "B1")
        self.assertEqual("RECOMMENDED", b1["selection"])
        self.assertEqual("0", b1["intersection_count"])
        self.assertEqual("0", b1["twist_count"])

    def test_022_pto_height_range(self):
        rows = load_csv(B.PTO_HEIGHTS_NAME)
        self.assertEqual({280.0, 290.0, 300.0, 310.0, 320.0, 330.0, 350.0, 370.0}, {float(row["pto_axis_z_mm"]) for row in rows})
        self.assertTrue(all(float(row["rotation_bottom_z_mm"]) >= 200.0 for row in rows))
        rec = next(row for row in rows if row["selection"] == "RECOMMENDED")
        self.assertEqual(320.0, float(rec["pto_axis_z_mm"]))

    def test_023_sixty_tooth_axial_stack(self):
        rec = self.parameters["recommended"]
        self.assertEqual(20.0, rec["pto_60t_axial_width_mm"])
        self.assertEqual(120.0, rec["pto_60t_safety_od_mm"])
        self.assertGreaterEqual(rec["pto_60t_actual_side_clearance_each_mm"], 8.0)
        self.assertGreaterEqual(rec["pto_60t_safety_to_kp000_each_mm"], 8.0)
        self.assertLess(rec["inner_kp000_abs_y_mm"], rec["pto_belt_plane_abs_y_mm"])
        self.assertLess(rec["pto_belt_plane_abs_y_mm"], rec["outer_kp000_abs_y_mm"])

    def test_024_kp000_support_contract(self):
        kp = self.parameters["kp000"]
        self.assertEqual((67.0, 17.0), (kp["mounting_width_x_mm"], kp["housing_axial_depth_y_mm"]))
        self.assertEqual(6.0, kp["insert_protrusion_mm"])
        self.assertEqual(2, kp["mounting_ear_count"])
        self.assertEqual("PROHIBITED", kp["direct_to_2040"])
        self.assertEqual("HOLD", kp["hole_center_distance"])

    def test_025_y_stack_left_right_mirrored(self):
        rows = load_csv(B.Y_STACK_NAME)
        left = [row for row in rows if row["side"] == "LEFT"]
        right = [row for row in rows if row["side"] == "RIGHT"]
        self.assertEqual(len(left), len(right))
        self.assertEqual(15, len(left))
        self.assertTrue(all(row["manufacturing_release"] == "HOLD" for row in rows))

    def test_026_center_pto_end_gap_and_no_collision(self):
        bay = self.parameters["central_bay"]
        self.assertEqual(30.0, bay["left_end_y_mm"])
        self.assertEqual(-30.0, bay["right_end_y_mm"])
        self.assertEqual(60.0, bay["end_gap_mm"])
        self.assertEqual(0, bay["left_right_shaft_intersection_count"])
        self.assertEqual(0, bay["left_right_coupling_intersection_count"])

    def test_027_center_bay_candidates_and_c1(self):
        rows = load_csv(B.CENTER_BAY_NAME)
        self.assertEqual(30, len(rows))
        rec = next(row for row in rows if row["selection"] == "RECOMMENDED")
        self.assertEqual("C1", rec["coupling_candidate"])
        self.assertEqual("60.0", rec["center_pto_end_gap_mm"])
        self.assertEqual("True", rec["mechanical_only"])

    def test_028_coupling_measurements_hold(self):
        rows = load_csv(B.COUPLING_NAME)
        self.assertEqual(5, len(rows))
        self.assertTrue(all(row["independent_left_right"] == "True" for row in rows))
        self.assertTrue(all(row["rover_common_shaft"] == "False" for row in rows))
        self.assertTrue(all(row["outside_diameter_mm"] == "HOLD" for row in rows))
        self.assertTrue(all(row["axial_length_mm"] == "HOLD" for row in rows))

    def test_029_interference_matrix_zero(self):
        self.assertGreaterEqual(self.report["check_count"], 50)
        self.assertEqual(0, self.report["intersection_count"])
        self.assertEqual(0, self.report["failure_count"])
        self.assertTrue(all(row["status"] == "CONDITIONAL_PASS_CANDIDATE" for row in self.report["checks"]))

    def test_030_belt_clearances(self):
        rec = self.parameters["recommended"]
        self.assertGreaterEqual(rec["belt_to_fixed_clearance_mm"], 5.0)
        self.assertGreaterEqual(rec["belt_to_l_bracket_clearance_mm"], 5.0)
        self.assertGreaterEqual(rec["belt_to_fastener_clearance_mm"], 5.0)
        self.assertGreaterEqual(rec["drive_pto_belt_safety_gap_mm"], 0.0)

    def test_031_pto_rotation_clearances(self):
        rec = self.parameters["recommended"]
        self.assertGreaterEqual(rec["pto_rotation_to_fixed_clearance_mm"], 8.0)
        self.assertGreaterEqual(rec["pto_rotation_to_l_bracket_clearance_mm"], 8.0)
        self.assertGreaterEqual(rec["pto_rotation_to_fastener_clearance_mm"], 8.0)

    def test_032_clutch_clearances(self):
        rec = self.parameters["recommended"]
        self.assertGreaterEqual(rec["clutch_full_stroke_to_fixed_clearance_mm"], 5.0)
        self.assertGreaterEqual(rec["clutch_full_stroke_to_belt_clearance_mm"], 8.0)
        rows = [row for row in self.report["checks"] if row["category"] == "CLUTCH"]
        self.assertTrue(all(row["intersection_count"] == 0 for row in rows))

    def test_033_total_width_and_height(self):
        rec = self.parameters["recommended"]
        self.assertLess(rec["total_width_with_all_envelopes_mm"], 300.0)
        self.assertGreaterEqual(rec["pto_rotation_bottom_z_mm"], 200.0)
        self.assertGreaterEqual(rec["pto_axis_z_mm"], 280.0)

    def test_034_e2_high_electrical_non_regression(self):
        electrical = self.parameters["electrical"]
        self.assertEqual([180.0, 0.0, 455.0], electrical["center_xyz_mm"])
        self.assertEqual(440.0, electrical["bottom_z_mm"])
        self.assertEqual("PROHIBITED", electrical["central_bay_connector"])
        self.assertIn("UNIT_PRESENT_SENSOR", electrical["functions"])

    def test_035_parent_boxes_crawler_member_contract(self):
        fixed = self.parameters["fixed_contract"]
        self.assertEqual("CBOX_FRONT_BBOX_REAR_SERIAL", fixed["box_order"])
        self.assertEqual("PROHIBITED", fixed["box_structural_role"])
        self.assertGreaterEqual(fixed["box_bottom_min_z_mm"], 200.0)
        self.assertIn("INVERSE_TRAPEZOID", fixed["crawler"])
        self.assertLessEqual(self.parameters["recommended"]["max_member_length_mm"], 400.0)

    def test_036_release_states(self):
        release = self.parameters["release_states"]
        self.assertEqual("HOLD", release["physical_fit"])
        self.assertEqual("HOLD", release["support_plate_machining"])
        self.assertEqual("HOLD", release["shaft_cutting"])
        self.assertEqual("HOLD", release["manufacturing"])
        self.assertEqual("NOT_APPROVED", release["field_deployment"])

    def test_037_validation_all_pass_and_pointer_gate(self):
        self.assertEqual(0, self.validation["fail_count"])
        self.assertEqual(self.validation["check_count"], self.validation["pass_count"])
        self.assertTrue(self.validation["pointer_update_gate_pass"])
        self.assertEqual(
            "common_rover_outboard_inward_pto_design_authority_v0_9_1",
            self.validation["authority_pointer_target"],
        )

    def test_038_step_semantics_six_of_six(self):
        results = B.verify_step_semantics()
        self.assertEqual(6, len(results))
        self.assertTrue(all(result["pass"] for result in results))
        self.assertTrue(all(result["solid_count"] >= 40 for result in results))
        self.assertTrue(all(result["y_length_mm"] < 300.0 for result in results))

    def test_039_step_files_parse_independently(self):
        for rel in B.STEP_FILES:
            model = cq.importers.importStep(str(LANE_DIR / rel))
            self.assertGreaterEqual(model.solids().size(), 40)

    def test_040_svg_contract_seven_of_seven(self):
        required = (
            "NOT_FOR_MANUFACTURING",
            "HOLD",
        )
        for rel in B.SVG_FILES:
            text = (LANE_DIR / rel).read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            for token in required:
                self.assertIn(token, text)

    def test_041_manifest_hash_and_cache_contract(self):
        manifest = B.verify_manifest()
        hashes = B.verify_hashes()
        self.assertEqual(37, manifest["manifest_file_count"])
        self.assertTrue(manifest["path_set_match"])
        self.assertEqual(0, manifest["duplicate_count"])
        self.assertEqual(36, hashes["hashed_file_count"])
        self.assertEqual(0, hashes["hash_mismatch_count"])
        actual = B._lane_files()
        self.assertFalse(any("__pycache__" in rel or ".pytest_cache" in rel for rel in actual))
        self.assertFalse(any(rel.lower().endswith((".pyc", ".stl", ".dxf", ".3mf", ".gcode", ".fcstd")) for rel in actual))

    def test_042_authority_and_holds_documented(self):
        authority = (LANE_DIR / B.AUTHORITY_NAME).read_text(encoding="utf-8")
        superseded = (LANE_DIR / B.SUPERSEDED_NAME).read_text(encoding="utf-8")
        self.assertIn("left motor shaft -Y and left PTO output -Y", authority)
        self.assertIn("NOT_FOR_MANUFACTURING", authority)
        self.assertIn("FIELD_DEPLOYMENT = NOT_APPROVED", authority)
        self.assertIn("LEFT_PTO_OUTPUT_DIRECTION = -Y", superseded)
        self.assertIn("No protected parent byte is changed", superseded)

    def test_043_download_zip_exists_and_exact(self):
        candidates = sorted(
            B.DOWNLOAD_DIR.glob(f"{B.ZIP_PREFIX}*.zip"),
            key=lambda path: path.stat().st_mtime_ns,
        )
        self.assertTrue(candidates)
        latest = candidates[-1]
        result = B.verify_zip(latest)
        self.assertEqual(37, result["zip_path_count"])
        self.assertEqual(0, result["zip_mismatch_count"])
        self.assertEqual(0, result["zip_forbidden_count"])
        with zipfile.ZipFile(latest, "r") as archive:
            with tempfile.TemporaryDirectory() as temp:
                archive.extractall(temp)
                extracted = Path(temp)
                self.assertEqual(
                    sorted(B.PACKAGE_PATHS),
                    sorted(
                        path.relative_to(extracted).as_posix()
                        for path in extracted.rglob("*")
                        if path.is_file()
                    ),
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
