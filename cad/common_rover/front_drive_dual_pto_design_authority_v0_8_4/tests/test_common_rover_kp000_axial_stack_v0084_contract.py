from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import unittest
import zipfile
from pathlib import Path


sys.dont_write_bytecode = True
LANE_DIR = Path(__file__).resolve().parents[1]
BUILDER_PATH = LANE_DIR / "build_common_rover_kp000_axial_stack_v0084.py"
SPEC = importlib.util.spec_from_file_location("v0084_builder_contract", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import v0.8.4 builder")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def file_hashes() -> dict[str, str]:
    return {
        path.relative_to(LANE_DIR).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(LANE_DIR.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def read_csv(name: str) -> list[dict[str, str]]:
    with (LANE_DIR / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class CommonRoverV0084Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parameters = json.loads((LANE_DIR / builder.PARAMETERS_NAME).read_text(encoding="utf-8"))
        cls.validation = json.loads((LANE_DIR / builder.VALIDATION_NAME).read_text(encoding="utf-8"))
        cls.interference = json.loads((LANE_DIR / builder.INTERFERENCE_NAME).read_text(encoding="utf-8"))
        cls.orientation = read_csv(builder.ORIENTATION_NAME)
        cls.search = read_csv(builder.SEARCH_NAME)
        cls.ranking = read_csv(builder.RANKING_NAME)
        cls.sensitivity = read_csv(builder.SENSITIVITY_NAME)
        cls.stack = read_csv(builder.STACK_NAME)
        cls.matrix = read_csv(builder.MATRIX_NAME)

    def test_001_exact_twenty_four_package_paths(self) -> None:
        actual = {
            path.relative_to(LANE_DIR).as_posix()
            for path in LANE_DIR.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        self.assertEqual(actual, set(builder.PACKAGE_PATHS))
        self.assertEqual(len(actual), 24)

    def test_002_v008_to_v0083_parent_sha_protection(self) -> None:
        audit = builder.parent_protection_audit()
        self.assertEqual(audit["mismatches"], [])
        self.assertIn(audit["checked_path_count"], (0, 76))
        self.assertEqual(
            audit["ledger_sha256"]["v0.8.3"],
            "5ca0b59e1eed15eab3ea1c5ba540ba695b55f9180e0b8c07c8946e97be0d937b",
        )

    def test_003_v0083_baseline_reproduction(self) -> None:
        baseline = builder.baseline_reproduction()
        self.assertEqual(baseline["status"], "PASS")
        self.assertEqual(baseline["pulley_to_housing_mm"], 14.5)
        self.assertEqual(baseline["pulley_to_full_kp000_worst_mm"], 8.5)
        self.assertEqual(baseline["pto_belt_to_full_kp000_worst_residual_mm"], 3.0)
        self.assertEqual(baseline["pto_belt_to_frame_mm"], 15.0)
        self.assertEqual(baseline["drive_belt_to_frame_mm"], 15.5)
        self.assertEqual(baseline["total_width_mm"], 290.0)
        self.assertEqual(baseline["pto_ends_y_mm"], [-145.0, 145.0])

    def test_004_fixed_architecture(self) -> None:
        fixed = self.parameters["fixed_architecture"]
        self.assertEqual(fixed["motor_count"], 2)
        self.assertEqual(fixed["pto_port_count"], 2)
        self.assertIn("NO_COMMON_SHAFT", fixed["pto_shaft_architecture"])
        self.assertEqual(fixed["motor_axis_direction"], "BOTH_INWARD")
        self.assertEqual(fixed["slide_clutch_states"], ["DRIVE", "NEUTRAL", "PTO"])
        self.assertEqual(fixed["drive_pto_simultaneous_engagement"], "PROHIBITED")

    def test_005_kp000_measured_envelope_and_orientation_terms(self) -> None:
        kp = self.parameters["kp000"]
        self.assertEqual(
            [kp["mounting_width_x_mm"], kp["housing_depth_y_mm"], kp["height_z_mm"]],
            [67.0, 17.0, 35.0],
        )
        self.assertEqual(kp["collar_protrusion_mm"], 6.0)
        self.assertEqual(kp["opposite_protrusion_mm"], "PART_MEASUREMENT_REQUIRED")
        definitions = self.parameters["orientation_definitions"]
        self.assertIn("vehicle center", definitions["ORIENTATION_C"])
        self.assertIn("vehicle outside", definitions["ORIENTATION_O"])

    def test_006_stage_one_sixteen_orientation_combinations(self) -> None:
        self.assertEqual(len(self.orientation), 16)
        combinations = {
            (
                row["left_inner_orientation"],
                row["left_outer_orientation"],
                row["right_inner_orientation"],
                row["right_outer_orientation"],
            )
            for row in self.orientation
        }
        self.assertEqual(len(combinations), 16)

    def test_007_simple_dual_inward_flip_collision_detected(self) -> None:
        candidate = builder.evaluate_candidate(
            "S1-COLLISION", 1, ("C", "O", "C", "O"), 0.0, 0.0, 0.0
        )
        self.assertEqual(candidate["center_mutual_clearance_mm"], -1.0)
        self.assertEqual(candidate["status"], "FAIL")
        self.assertIn("CENTER_CLEARANCE_LT_1", candidate["rejection_reason"])

    def test_008_stage_order_and_candidate_counts(self) -> None:
        summary = {int(row["stage"]): row for row in self.parameters["search_stage_summary"]}
        expected = {0: 1, 1: 16, 2: 76, 3: 169, 4: 33, 5: 0, 6: 0}
        self.assertEqual({stage: row["candidate_count"] for stage, row in summary.items()}, expected)
        self.assertEqual(len(self.search), 295)
        self.assertFalse(summary[5]["executed"])
        self.assertFalse(summary[6]["executed"])

    def test_009_recommended_candidate_is_first_passing_stage(self) -> None:
        recommended = self.parameters["recommended"]
        self.assertEqual(recommended["candidate_id"], "S2-INCC-OUTOO-SHIFT01.00")
        self.assertEqual(recommended["search_stage"], 2)
        self.assertEqual(self.ranking[0]["selection"], "RECOMMENDED_MINIMUM_STAGE_CHANGE")
        self.assertEqual(self.ranking[0]["candidate_id"], recommended["candidate_id"])
        self.assertFalse(
            any(row["status"] == "CONDITIONAL_PASS_CANDIDATE" for row in self.orientation)
        )

    def test_010_recommended_orientations_and_positions(self) -> None:
        rec = self.parameters["recommended"]
        self.assertEqual(
            [
                rec["left_inner_orientation"],
                rec["left_outer_orientation"],
                rec["right_inner_orientation"],
                rec["right_outer_orientation"],
            ],
            ["C", "O", "C", "O"],
        )
        self.assertEqual([rec["left_inner_y_mm"], rec["right_inner_y_mm"]], [15.0, -15.0])
        self.assertEqual([rec["left_pulley_y_mm"], rec["right_pulley_y_mm"]], [47.0, -47.0])
        self.assertEqual([rec["left_outer_y_mm"], rec["right_outer_y_mm"]], [87.5, -87.5])

    def test_011_alternatives_limited_and_ordered(self) -> None:
        alternatives = self.parameters["alternatives"]
        self.assertEqual(len(alternatives), 2)
        self.assertEqual(alternatives[0]["search_stage"], 4)
        self.assertEqual(alternatives[0]["pulley_shift_mm"], 6.0)
        self.assertEqual(alternatives[0]["outer_shift_mm"], 3.5)
        self.assertEqual(alternatives[1]["search_stage"], 3)
        self.assertEqual(alternatives[1]["pulley_shift_mm"], 3.0)

    def test_012_four_bearing_belt_intersections_zero(self) -> None:
        candidate_id = self.parameters["recommended"]["candidate_id"]
        rows = [
            row
            for row in self.matrix
            if row["candidate_id"] == candidate_id
            and "PTO_BELT" in row["check_id"]
            and "KP000" in row["check_id"]
        ]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(int(row["intersection_count"]) == 0 for row in rows))

    def test_013_four_bearing_pulley_intersections_zero(self) -> None:
        candidate_id = self.parameters["recommended"]["candidate_id"]
        rows = [
            row
            for row in self.matrix
            if row["candidate_id"] == candidate_id and "PULLEY_120" in row["check_id"]
        ]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(int(row["intersection_count"]) == 0 for row in rows))

    def test_014_inner_mutual_and_support_intersections_zero(self) -> None:
        rec = self.parameters["recommended"]
        self.assertGreaterEqual(rec["center_mutual_clearance_mm"], 1.0)
        cad = self.validation["recommended_cad_clearances_mm"]
        self.assertEqual(cad["inner_kp000_mutual_mm"], 1.0)
        self.assertEqual(cad["support_plate_mutual_mm"], 25.0)
        candidate = next(
            row for row in self.interference["candidates"] if row["candidate_id"] == rec["candidate_id"]
        )
        self.assertEqual(candidate["intersection_count"], 0)

    def test_015_belt_nominal_and_residual_gates(self) -> None:
        rec = self.parameters["recommended"]
        belt = self.parameters["belt"]
        self.assertEqual(belt["nominal_width_mm"], 15.0)
        self.assertEqual(belt["nominal_sweep_envelope_width_mm"], 21.0)
        self.assertEqual(belt["safety_sweep_envelope_width_mm"], 31.0)
        self.assertGreaterEqual(rec["belt_to_inner_nominal_mm"], 13.0)
        self.assertGreaterEqual(rec["belt_to_inner_residual_mm"], 8.0)
        self.assertGreaterEqual(rec["belt_to_outer_nominal_mm"], 13.0)
        self.assertGreaterEqual(rec["belt_to_outer_residual_mm"], 8.0)
        cad = self.validation["recommended_cad_clearances_mm"]
        self.assertEqual(cad["belt_inner_nominal_mm"], rec["belt_to_inner_nominal_mm"])
        self.assertEqual(cad["belt_inner_safety_residual_mm"], rec["belt_to_inner_residual_mm"])

    def test_016_pulley_120_clearance_gate(self) -> None:
        rec = self.parameters["recommended"]
        self.assertEqual(self.parameters["pulley"]["rotation_safety_od_mm"], 120.0)
        self.assertGreaterEqual(rec["pulley_to_inner_nominal_mm"], 10.0)
        self.assertGreaterEqual(rec["pulley_to_outer_nominal_mm"], 10.0)
        self.assertGreaterEqual(rec["pulley_to_inner_residual_mm"], 10.0)
        self.assertGreaterEqual(rec["pulley_to_outer_residual_mm"], 10.0)
        cad = self.validation["recommended_cad_clearances_mm"]
        self.assertEqual(cad["pulley_inner_nominal_mm"], rec["pulley_to_inner_nominal_mm"])
        self.assertEqual(cad["pulley_outer_nominal_mm"], rec["pulley_to_outer_nominal_mm"])

    def test_017_total_width_and_pto_end_limits(self) -> None:
        rec = self.parameters["recommended"]
        self.assertLess(rec["total_width_mm"], 300.0)
        self.assertLessEqual(abs(rec["left_pto_end_y_mm"]), 145.0)
        self.assertLessEqual(abs(rec["right_pto_end_y_mm"]), 145.0)
        changes = self.parameters["required_changes"]
        self.assertEqual(changes["pto_end_exceedance_mm"], 0.0)

    def test_018_support_plate_non_regression_and_no_hole_release(self) -> None:
        plate = self.parameters["support_plate"]
        self.assertTrue(plate["left_right_independent"])
        self.assertEqual(plate["thickness_y_mm"], 5.0)
        self.assertEqual([plate["width_x_mm"], plate["height_z_mm"]], [95.0, 140.0])
        self.assertEqual(plate["hole_pattern"], "KP000_HOLE_CENTER_DISTANCE_REQUIRED")
        self.assertEqual(self.parameters["required_changes"]["support_plate_enlargement_mm"], 0.0)
        self.assertFalse(any(path.suffix.lower() == ".dxf" for path in LANE_DIR.rglob("*")))

    def test_019_tool_access_is_simplified_and_held(self) -> None:
        rec = self.parameters["recommended"]
        self.assertGreaterEqual(rec["tool_clearance_mm"], 10.0)
        self.assertIn("ACTUAL_TOOL_ENVELOPE_REQUIRED", self.interference["holds"])
        authority = (LANE_DIR / builder.AUTHORITY_NAME).read_text(encoding="utf-8")
        self.assertIn("HOLD_ACTUAL_TOOL_ENVELOPE_REQUIRED", authority)

    def test_020_axial_stack_seventeen_items_per_side(self) -> None:
        for side in ("LEFT", "RIGHT"):
            rows = [row for row in self.stack if row["side"] == side]
            self.assertEqual(len(rows), 17)
        classifications = {row["classification"] for row in self.stack}
        self.assertTrue({"MEASURED", "NOMINAL", "PROVISIONAL", "HOLD"} <= classifications)

    def test_021_shaft_length_range_and_stock_semantics(self) -> None:
        rec = self.parameters["recommended"]
        self.assertEqual(
            [rec["shaft_length_min_mm"], rec["shaft_length_max_mm"]],
            [138.5, 144.5],
        )
        stock = self.parameters["shaft_stock_candidate"]
        self.assertEqual(stock["300_mm_bar_candidate_yield"], 2)
        self.assertEqual(stock["400_mm_bar_candidate_yield"], 2)
        self.assertEqual(stock["cutting_release"], "HOLD")

    def test_022_robustness_full_factorial_and_classification(self) -> None:
        self.assertEqual(len(self.sensitivity), 7 * 4 * 3 * 3 * 3)
        robust = self.parameters["recommended_robustness"]
        self.assertEqual(robust["combination_count"], 756)
        self.assertEqual(robust["result"], "CONDITIONAL_PASS_AT_NOMINAL_ONLY")
        self.assertEqual(robust["max_opposite_protrusion_all_allowances_mm"], 0)
        self.assertEqual(robust["opposite_protrusion_release"], "PART_MEASUREMENT_REQUIRED")

    def test_023_robust_alternative_and_intermediate_limit(self) -> None:
        alt_a, alt_b = self.parameters["alternatives"]
        robust_a = builder.robustness_summary(alt_a)
        robust_b = builder.robustness_summary(alt_b)
        self.assertEqual(robust_a["result"], "ROBUST_CONDITIONAL_PASS")
        self.assertEqual(robust_a["pass_count"], 756)
        self.assertEqual(robust_a["max_opposite_protrusion_all_allowances_mm"], 6)
        self.assertEqual(robust_b["max_opposite_protrusion_all_allowances_mm"], 3)

    def test_024_step_semantic_geometry_three_of_three(self) -> None:
        for key, name in (
            ("recommended", builder.RECOMMENDED_STEP),
            ("alternative_a", builder.ALTERNATIVE_A_STEP),
            ("alternative_b", builder.ALTERNATIVE_B_STEP),
        ):
            candidate = (
                self.parameters["recommended"]
                if key == "recommended"
                else self.parameters["alternatives"][0 if key == "alternative_a" else 1]
            )
            source = builder.candidate_model(candidate)
            imported = builder.cq.importers.importStep(str(LANE_DIR / "artifacts" / name))
            self.assertEqual(builder._shape_signature(source), builder._shape_signature(imported))
            self.assertTrue(self.validation["geometry"][key]["semantic_geometry_reproducible"])

    def test_025_svg_warnings_and_key_values(self) -> None:
        for name in (builder.OVERVIEW_SVG, builder.SECTION_SVG, builder.CENTRAL_SVG):
            text = (LANE_DIR / "artifacts" / name).read_text(encoding="utf-8")
            self.assertIn("NOT_FOR_MANUFACTURING", text)
            self.assertIn("<svg", text)
        central = (LANE_DIR / "artifacts" / builder.CENTRAL_SVG).read_text(encoding="utf-8")
        self.assertIn("−1.0 mm", central)
        self.assertIn("1.0 mm nominal clearance", central)

    def test_026_manifest_sha_and_cache_contract(self) -> None:
        result = builder._verify_hashes()
        self.assertEqual(result["manifest_file_count"], 24)
        self.assertEqual(result["hashed_file_count"], 23)
        forbidden = [
            path
            for path in LANE_DIR.rglob("*")
            if path.is_file()
            and (
                "__pycache__" in path.parts
                or ".pytest_cache" in path.parts
                or path.suffix.lower() in {".pyc", ".stl", ".dxf", ".3mf", ".gcode"}
            )
        ]
        self.assertEqual(forbidden, [])

    def test_027_verify_is_read_only_and_release_states(self) -> None:
        before = file_hashes()
        result = builder.verify()
        after = file_hashes()
        self.assertEqual(before, after)
        self.assertEqual(result["overall"], "CONDITIONAL_PASS_CANDIDATE")
        states = self.parameters["release_states"]
        self.assertEqual(states["physical_fit"], "HOLD")
        self.assertEqual(states["pulley_bore_fit"], "FAIL_PROVISIONAL")
        self.assertEqual(states["shaft_cutting"], "HOLD")
        self.assertEqual(states["support_plate_machining"], "HOLD")
        self.assertEqual(states["drilling"], "HOLD")
        self.assertEqual(states["field_deployment"], "NOT_APPROVED")

    def test_028_download_zip_delivery_lifecycle(self) -> None:
        candidates = sorted(builder.DOWNLOAD_DIR.glob(f"{builder.ZIP_PREFIX}*.zip"))
        if not candidates:
            self.assertTrue(callable(builder.package))
            self.assertEqual(builder.DOWNLOAD_DIR, Path(r"D:\Downloads"))
            return
        latest = candidates[-1]
        with zipfile.ZipFile(latest) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(tuple(archive.namelist()), builder.PACKAGE_PATHS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
