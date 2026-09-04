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
BUILDER_PATH = LANE_DIR / "build_common_rover_robust_axial_tolerance_v0085.py"
SPEC = importlib.util.spec_from_file_location("v0085_builder_contract", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import v0.8.5 builder")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def read_csv(name: str) -> list[dict[str, str]]:
    with (LANE_DIR / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def tree_hashes() -> dict[str, str]:
    return {
        path.relative_to(LANE_DIR).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(LANE_DIR.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


class CommonRoverV0085Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.params = json.loads((LANE_DIR / builder.PARAMETERS_NAME).read_text(encoding="utf-8"))
        cls.validation = json.loads((LANE_DIR / builder.VALIDATION_NAME).read_text(encoding="utf-8"))
        cls.interference = json.loads((LANE_DIR / builder.INTERFERENCE_NAME).read_text(encoding="utf-8"))
        cls.search = read_csv(builder.SEARCH_NAME)
        cls.ranking = read_csv(builder.RANKING_NAME)
        cls.boundary = read_csv(builder.SENSITIVITY_NAME)
        cls.stack = read_csv(builder.STACK_NAME)
        cls.matrix = read_csv(builder.MATRIX_NAME)

    def test_001_exact_twenty_four_paths(self) -> None:
        actual = {
            path.relative_to(LANE_DIR).as_posix()
            for path in LANE_DIR.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        self.assertEqual(actual, set(builder.PACKAGE_PATHS))
        self.assertEqual(len(actual), 24)

    def test_002_parent_v008_to_v0084_protection(self) -> None:
        audit = builder.parent_protection_audit()
        self.assertEqual(audit["mismatches"], [])
        self.assertIn(audit["checked_path_count"], (0, 100))
        self.assertEqual(
            audit["ledger_sha256"]["v0.8.4"],
            "ca91b5fb76de196c7267dd616e236aeed9d0e278ed829655c910b0978389c1ea",
        )

    def test_003_v0084_baseline_reproduced_and_preserved(self) -> None:
        baseline = self.params["baseline_reproduction"]
        self.assertEqual(baseline["status"], "PASS")
        self.assertEqual(baseline["recommended_candidate_id"], "S2-INCC-OUTOO-SHIFT01.00")
        self.assertEqual(baseline["recommended_center_mm"], 1.0)
        self.assertEqual(baseline["recommended_robust_pass_count"], 276)
        self.assertEqual(baseline["recommended_robust_total_count"], 756)

    def test_004_fixed_architecture(self) -> None:
        fixed = self.params["fixed_architecture"]
        self.assertEqual(fixed["motor_count"], 2)
        self.assertEqual(fixed["pto_port_count"], 2)
        self.assertIn("NO_COMMON_SHAFT", fixed["pto_shaft_architecture"])
        self.assertEqual(fixed["slide_clutch_states"], ["DRIVE", "NEUTRAL", "PTO"])
        self.assertEqual(fixed["simultaneous_drive_pto"], "PROHIBITED")

    def test_005_old_shared_error_model_superseded(self) -> None:
        tolerance = self.params["tolerance_model"]
        self.assertEqual(tolerance["superseded_model"], "ONE_SHARED_ASSEMBLY_ERROR")
        self.assertEqual(self.params["v0084_stage_priority"], "SUPERSEDED")
        self.assertEqual(
            self.params["baseline_reproduction"]["new_bilateral_error_center_residual_mm"],
            -1.0,
        )
        correction = (LANE_DIR / builder.CORRECTION_NAME).read_text(encoding="utf-8")
        self.assertIn("zero central residual", correction)

    def test_006_independent_six_placement_errors(self) -> None:
        tolerance = self.params["tolerance_model"]
        self.assertEqual(
            tolerance["independent_variables_per_side"],
            ["inner_kp000_axial_error", "pulley_axial_error", "outer_kp000_axial_error"],
        )
        self.assertEqual(tolerance["center_bilateral_error_max_mm"], 2.0)
        self.assertEqual(tolerance["relative_component_error_max_mm"], 2.0)

    def test_007_search_count_and_ranges(self) -> None:
        self.assertEqual(len(self.search), 2108)
        grid = [row for row in self.search if int(row["search_stage"]) > 0]
        self.assertEqual(min(float(row["inner_shift_mm"]) for row in grid), 1.0)
        self.assertEqual(max(float(row["inner_shift_mm"]) for row in grid), 5.0)
        self.assertEqual(min(float(row["pulley_shift_mm"]) for row in grid), 5.0)
        self.assertEqual(max(float(row["pulley_shift_mm"]) for row in grid), 12.0)
        self.assertEqual(min(float(row["outer_shift_mm"]) for row in grid), 3.0)
        self.assertEqual(max(float(row["outer_shift_mm"]) for row in grid), 10.0)

    def test_008_required_r1_r2_r3_evaluated(self) -> None:
        focus = self.params["focus_candidates"]
        self.assertEqual(set(focus), {"R1", "R2", "R3"})
        self.assertEqual(focus["R1"]["center_nominal_mm"], 4.0)
        self.assertEqual(focus["R1"]["center_residual_mm"], 2.0)
        self.assertEqual(focus["R2"]["center_nominal_mm"], 5.0)
        self.assertEqual(focus["R3"]["belt_inner_residual_worst_mm"], 8.5)
        self.assertTrue(all(row["boundary_pass"] for row in focus.values()))

    def test_009_ranking_uses_robust_priority_not_stage(self) -> None:
        priority = self.params["selection_priority"]
        self.assertEqual(priority[0], "ALL_BOUNDARY_PASS")
        self.assertEqual(priority[1], "CENTER_RESIDUAL_MAX")
        self.assertEqual(priority[-1], "SEARCH_STAGE_LAST")
        self.assertEqual(self.ranking[0]["selection"], "RECOMMENDED_ROBUST_PRIORITY")

    def test_010_recommended_positions_and_orientations(self) -> None:
        rec = self.params["recommended"]
        self.assertEqual(rec["candidate_id"], "G-IN5.00-P11.25-OUT10.00")
        self.assertEqual(
            [rec["inner_shift_mm"], rec["pulley_shift_mm"], rec["outer_shift_mm"]],
            [5.0, 11.25, 10.0],
        )
        self.assertEqual(
            [rec["inner_y_mm"], rec["pulley_y_mm"], rec["outer_y_mm"]],
            [19.0, 58.25, 97.5],
        )
        self.assertEqual([rec["inner_orientation"], rec["outer_orientation"]], ["C/C", "O/O"])

    def test_011_alternatives_max_two_and_robust(self) -> None:
        alternatives = self.params["alternatives"]
        self.assertEqual(len(alternatives), 2)
        self.assertTrue(all(candidate["boundary_pass"] for candidate in alternatives))
        self.assertTrue(all(candidate["center_residual_mm"] >= 2 for candidate in alternatives))

    def test_012_center_nominal_and_bilateral_residual(self) -> None:
        rec = self.params["recommended"]
        self.assertGreaterEqual(rec["center_nominal_mm"], 4)
        self.assertGreaterEqual(rec["center_residual_mm"], 2)
        self.assertEqual(rec["center_nominal_mm"], 9.0)
        self.assertEqual(rec["center_residual_mm"], 7.0)
        center_rows = [row for row in self.boundary if row["analysis_scope"] == "CENTER_BILATERAL"]
        self.assertEqual(len(center_rows), 9)
        self.assertTrue(all(row["status"] == "PASS_BOUNDARY" for row in center_rows))

    def test_013_belt_nominal_and_independent_residual(self) -> None:
        rec = self.params["recommended"]
        self.assertGreaterEqual(rec["belt_inner_nominal_worst_mm"], 14)
        self.assertGreaterEqual(rec["belt_outer_nominal_worst_mm"], 14)
        self.assertGreaterEqual(rec["belt_inner_residual_worst_mm"], 8)
        self.assertGreaterEqual(rec["belt_outer_residual_worst_mm"], 8)
        self.assertEqual(builder.TOLERANCE["belt_total_worst_allowance_mm"], 6.0)

    def test_014_pulley_nominal_and_independent_residual(self) -> None:
        rec = self.params["recommended"]
        self.assertGreaterEqual(rec["pulley_inner_nominal_worst_mm"], 13.5)
        self.assertGreaterEqual(rec["pulley_outer_nominal_worst_mm"], 13.5)
        self.assertGreaterEqual(rec["pulley_inner_residual_worst_mm"], 10)
        self.assertGreaterEqual(rec["pulley_outer_residual_worst_mm"], 10)
        self.assertEqual(builder.TOLERANCE["pulley_total_worst_allowance_mm"], 3.5)

    def test_015_opposite_protrusion_zero_through_six_boundary_pass(self) -> None:
        values = {
            int(row["opposite_protrusion_mm"])
            for row in self.boundary
            if row["opposite_protrusion_mm"] != ""
        }
        self.assertEqual(values, set(range(7)))
        self.assertTrue(all(row["status"] == "PASS_BOUNDARY" for row in self.boundary))
        self.assertEqual(self.params["kp000"]["opposite_protrusion_status"], "PART_MEASUREMENT_REQUIRED")

    def test_016_boundary_decomposition_is_authoritative(self) -> None:
        boundary = self.params["boundary_analysis"]
        self.assertEqual(boundary["row_count"], 9081)
        self.assertEqual(len(self.boundary), 9081)
        self.assertEqual(boundary["fail_count"], 0)
        self.assertTrue(boundary["all_pass"])
        self.assertTrue(boundary["pass_authority"])

    def test_017_monte_carlo_not_pass_authority(self) -> None:
        monte = self.params["monte_carlo"]
        self.assertEqual(monte["seed"], 850)
        self.assertEqual(monte["sample_count"], 2000)
        self.assertFalse(monte["pass_authority"])
        self.assertEqual(monte["fail_count"], 0)

    def test_018_width_pto_ends_and_output_reserve(self) -> None:
        rec = self.params["recommended"]
        self.assertLess(rec["total_width_mm"], 300)
        self.assertEqual(rec["pto_ends_y_mm"], "-145.0|145.0")
        self.assertGreaterEqual(rec["output_reserve_mm"], 25)
        self.assertGreaterEqual(rec["output_reserve_mm"], 30)

    def test_019_support_plate_and_no_hole_release(self) -> None:
        plate = self.params["support_plate"]
        self.assertTrue(plate["left_right_independent"])
        self.assertEqual(plate["size_mm"], [95.0, 140.0, 5.0])
        self.assertEqual(plate["enlargement_required_mm"], 0.0)
        self.assertEqual(plate["hole_pattern"], "PART_MEASUREMENT_REQUIRED")
        self.assertFalse(any(path.suffix.lower() == ".dxf" for path in LANE_DIR.rglob("*")))

    def test_020_tool_frame_fastener_non_intersection(self) -> None:
        rec_id = self.params["recommended"]["candidate_id"]
        rows = [row for row in self.matrix if row["candidate_id"] == rec_id]
        self.assertTrue(all(int(row["intersection_count"]) == 0 for row in rows))
        ids = {row["check_id"] for row in rows}
        self.assertIn("LEFT_TOOL_VS_FRAME", ids)
        self.assertIn("PTO_BELTS_VS_FASTENERS", ids)

    def test_021_axial_stack_and_shaft_length_hold(self) -> None:
        for side in ("LEFT", "RIGHT"):
            self.assertEqual(len([row for row in self.stack if row["side"] == side]), 17)
        rec = self.params["recommended"]
        self.assertEqual(
            [rec["shaft_length_min_mm"], rec["shaft_length_max_mm"]],
            [134.5, 140.5],
        )
        self.assertEqual(self.params["shaft_stock"]["300_mm_bar_yield_candidate"], 2)
        self.assertEqual(self.params["shaft_stock"]["400_mm_bar_yield_candidate"], 2)
        self.assertEqual(self.params["shaft_stock"]["cutting"], "HOLD")

    def test_022_cad_envelope_distances_match_interval_nominals(self) -> None:
        rec = self.params["recommended"]
        cad = self.interference["cad_clearances_recommended_mm"]
        self.assertEqual(cad["center_nominal_mm"], rec["center_nominal_mm"])
        self.assertEqual(cad["belt_inner_nominal_mm"], rec["belt_inner_nominal_worst_mm"])
        self.assertEqual(cad["belt_inner_safety_mm"], rec["belt_inner_residual_worst_mm"])
        self.assertEqual(cad["pulley_inner_nominal_mm"], rec["pulley_inner_nominal_worst_mm"])

    def test_023_step_semantic_geometry_three_of_three(self) -> None:
        for key, filename, candidate in (
            ("recommended", builder.RECOMMENDED_STEP, self.params["recommended"]),
            ("alternative_a", builder.ALTERNATIVE_A_STEP, self.params["alternatives"][0]),
            ("alternative_b", builder.ALTERNATIVE_B_STEP, self.params["alternatives"][1]),
        ):
            source = builder.candidate_model(candidate)
            imported = builder.cq.importers.importStep(str(LANE_DIR / "artifacts" / filename))
            self.assertEqual(builder._shape_signature(source), builder._shape_signature(imported))
            self.assertTrue(self.validation["geometry"][key]["semantic_geometry_reproducible"])

    def test_024_svg_and_authority_warnings(self) -> None:
        for name in (builder.OVERVIEW_SVG, builder.TOLERANCE_SVG, builder.CENTER_SVG):
            text = (LANE_DIR / "artifacts" / name).read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            self.assertIn("NOT_FOR_MANUFACTURING", text)
        authority = (LANE_DIR / builder.AUTHORITY_NAME).read_text(encoding="utf-8")
        self.assertIn("ROBUST_CONDITIONAL_PASS", authority)
        self.assertIn("PART_MEASUREMENT_REQUIRED", authority)

    def test_025_manifest_hash_and_cache_contract(self) -> None:
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

    def test_026_verify_read_only_and_release_states(self) -> None:
        before = tree_hashes()
        result = builder.verify()
        after = tree_hashes()
        self.assertEqual(before, after)
        self.assertEqual(result["overall"], "CONDITIONAL_PASS_CANDIDATE")
        states = self.params["release_states"]
        self.assertEqual(states["tolerance_robustness"], "ROBUST_CONDITIONAL_PASS_CANDIDATE")
        self.assertEqual(states["pulley_bore_fit"], "FAIL_PROVISIONAL")
        self.assertEqual(states["physical_fit"], "HOLD")
        self.assertEqual(states["support_machining"], "HOLD")
        self.assertEqual(states["drilling"], "HOLD")
        self.assertEqual(states["shaft_cutting"], "HOLD")
        self.assertEqual(states["field_deployment"], "NOT_APPROVED")

    def test_027_validation_all_fixed_checks_pass(self) -> None:
        self.assertEqual(self.validation["overall"], "CONDITIONAL_PASS_CANDIDATE")
        self.assertEqual(
            self.validation["check_pass_count"],
            self.validation["check_count"],
        )
        self.assertEqual(self.validation["boundary_row_count"], 9081)

    def test_028_download_zip_delivery_lifecycle(self) -> None:
        candidates = sorted(builder.DOWNLOAD_DIR.glob(f"{builder.ZIP_PREFIX}*.zip"))
        if not candidates:
            self.assertTrue(callable(builder.package))
            self.assertEqual(builder.DOWNLOAD_DIR, Path(r"D:\Downloads"))
            return
        with zipfile.ZipFile(candidates[-1]) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(tuple(archive.namelist()), builder.PACKAGE_PATHS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
