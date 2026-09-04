"""Contract tests for Common Rover belt-clearance authority v0.8.1."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

import cadquery as cq


LANE = Path(__file__).resolve().parents[1]
REPO_ROOT = LANE.parents[2]
BUILDER = LANE / "build_common_rover_front_drive_dual_pto_v0081.py"
PARAMETERS = LANE / "common_rover_front_drive_dual_pto_parameters_v0081.json"
BASELINE = LANE / "common_rover_front_drive_dual_pto_baseline_v0081.json"
SEARCH = LANE / "common_rover_front_drive_dual_pto_search_candidates_v0081.csv"
RANKING = LANE / "common_rover_front_drive_dual_pto_candidate_ranking_v0081.csv"
REPORT = LANE / "common_rover_front_drive_dual_pto_interference_report_v0081.json"
VALIDATION = LANE / "common_rover_front_drive_dual_pto_validation_v0081.json"
ALLOCATION = LANE / "common_rover_front_drive_dual_pto_aluminum_allocation_v0081.csv"
MANIFEST = LANE / "MANIFEST.txt"
SUMS = LANE / "SHA256SUMS.txt"
STEP = LANE / "artifacts" / "PS-CR-FRONT-DRIVE-DUAL-PTO-V0081-INSPECTION.step"


def _load_builder():
    spec = importlib.util.spec_from_file_location("common_rover_v0081_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("builder could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class CommonRoverV0081Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.b = _load_builder()
        cls.p = _json(PARAMETERS)
        cls.baseline = _json(BASELINE)
        cls.report = _json(REPORT)
        cls.validation = _json(VALIDATION)
        cls.search = _csv(SEARCH)
        cls.ranking = _csv(RANKING)
        cls.allocation = _csv(ALLOCATION)

    def test_001_exact_package_paths_exist(self) -> None:
        self.assertEqual(19, len(self.b.PACKAGE_PATHS))
        self.assertTrue(all((LANE / path).is_file() for path in self.b.PACKAGE_PATHS))

    def test_002_v008_baseline_reproduced_and_unchanged(self) -> None:
        self.assertTrue(self.baseline["baseline_reproduced"])
        self.assertEqual(0, self.baseline["v008_hash_mismatch_count"])
        repository_paths = [
            REPO_ROOT / relative
            for relative in self.baseline["v008_path_hashes"]
        ]
        existing_count = sum(path.is_file() for path in repository_paths)
        self.assertIn(existing_count, (0, len(repository_paths)))
        for relative, evidence in self.baseline["v008_path_hashes"].items():
            with self.subTest(relative=relative):
                self.assertTrue(evidence["match"])
                self.assertEqual(
                    evidence["expected_sha256"],
                    evidence["actual_sha256"],
                )
                if existing_count:
                    path = REPO_ROOT / relative
                    self.assertEqual(
                        evidence["expected_sha256"],
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                    )

    def test_003_baseline_numeric_contract(self) -> None:
        m = self.baseline["baseline_metrics"]
        self.assertAlmostEqual(15.5, m["drive_belt_to_frame_mm"], places=2)
        self.assertAlmostEqual(5.5, m["pto_belt_to_frame_mm"], places=2)
        self.assertAlmostEqual(25.5, m["drive_belt_to_root_2040_mm"], places=2)
        self.assertAlmostEqual(15.5, m["drive_belt_to_front_track_diagonal_mm"], places=2)
        self.assertAlmostEqual(70.0, m["pto_belt_to_2020_diagonal_mm"], places=2)
        self.assertAlmostEqual(71.53, m["pto_belt_to_front_crossbar_mm"], places=2)
        self.assertAlmostEqual(11.0, m["pto_60t_to_kp000_mm"], places=2)
        self.assertAlmostEqual(10.0, m["track_dynamic_to_upper_structure_mm"], places=2)
        self.assertAlmostEqual(290.0, m["step_width_mm"], places=2)

    def test_004_fixed_two_motor_two_independent_pto_architecture(self) -> None:
        fixed = self.p["fixed_v008_architecture"]
        self.assertEqual(2, fixed["motor_count"])
        self.assertEqual(2, fixed["pto_count"])
        self.assertEqual("PROHIBITED", fixed["common_pto_shaft"])
        self.assertEqual("-Y_INWARD", fixed["motor_shaft_directions"]["left"])
        self.assertEqual("+Y_INWARD", fixed["motor_shaft_directions"]["right"])

    def test_005_clutch_and_box_contract(self) -> None:
        fixed = self.p["fixed_v008_architecture"]
        self.assertEqual(["DRIVE", "NEUTRAL", "PTO"], fixed["clutch_states"])
        self.assertEqual("PROHIBITED", fixed["simultaneous_same_side_drive_pto"])
        self.assertEqual(
            "CBOX_FRONT_BBOX_REAR_SHORT_FACES_OPPOSED",
            fixed["box_arrangement"],
        )
        self.assertGreaterEqual(fixed["box_bottom_z_mm"], 200)
        self.assertEqual("PROHIBITED", fixed["box_structural_role"])

    def test_006_motor_height_definition_and_axis_relation(self) -> None:
        fixed = self.p["fixed_v008_architecture"]
        self.assertEqual("MOTOR_SHAFT_CENTER_HEIGHT", fixed["motor_height_meaning"])
        self.assertGreaterEqual(fixed["motor_axis_z_mm"], fixed["box_top_max_z_mm"])
        self.assertGreaterEqual(fixed["pto_axis_z_mm"], fixed["motor_axis_z_mm"])

    def test_007_inverted_trapezoid_crawler_non_regression(self) -> None:
        fixed = self.p["fixed_v008_architecture"]
        self.assertEqual("INVERTED_TRAPEZOID_TOP_LONGER", fixed["crawler_geometry"])
        self.assertEqual(1, fixed["crawler_each_side"]["front_upper_drive_wheel"])
        self.assertEqual(1, fixed["crawler_each_side"]["rear_upper_idler"])
        self.assertEqual([3, 4], fixed["crawler_each_side"]["lower_roller_candidates"])
        self.assertEqual(4, fixed["crawler_each_side"]["step_roller_count"])
        self.assertEqual(400.0, fixed["upper_2040_candidate_mm"])
        self.assertEqual(260.0, fixed["lower_2040_candidate_mm"])

    def test_008_stage_order_and_stop_condition(self) -> None:
        search = self.p["search"]
        self.assertEqual("FAIL_CANNOT_REACH_13_AND_8", search["stage_1_result"])
        self.assertEqual("CONDITIONAL_PASS", search["stage_2_result"])
        self.assertEqual(
            "NOT_EXECUTED_STAGE_2_SATISFIED_TARGET",
            search["stages_3_to_6"],
        )
        self.assertGreater(len(self.search), 1000)

    def test_009_recommended_clearances(self) -> None:
        r = self.p["recommended_candidate"]
        self.assertEqual(self.b.RECOMMENDED_ID, r["candidate_id"])
        self.assertGreaterEqual(r["pto_nominal_clearance_mm"], 15.0)
        self.assertGreaterEqual(r["pto_residual_clearance_mm"], 8.0)
        self.assertGreaterEqual(r["drive_nominal_clearance_mm"], 13.0)
        self.assertGreaterEqual(r["drive_residual_clearance_mm"], 8.0)
        self.assertGreaterEqual(r["pulley_60t_to_fixed_mm"], 10.0)
        self.assertGreaterEqual(r["belt_to_wiring_mm"], 15.0)
        self.assertEqual("CONDITIONAL_PASS", r["status"])

    def test_010_residual_formula(self) -> None:
        r = self.p["recommended_candidate"]
        allowances = self.p["allowances_mm"]
        expected = (
            r["pto_nominal_clearance_mm"]
            - allowances["assembly_tolerance_mm"]
            - allowances["frame_deflection_allowance_mm"]
            - allowances["belt_lateral_wander_allowance_mm"]
        )
        self.assertAlmostEqual(expected, r["pto_residual_clearance_mm"], places=4)

    def test_011_all_required_intersections_zero(self) -> None:
        summary = self.report["summary"]
        self.assertEqual(0, summary["fail_count"])
        self.assertTrue(summary["all_belt_frame_intersections_zero"])
        self.assertTrue(summary["all_belt_fastener_intersections_zero"])
        for check in self.report["checks"]:
            with self.subTest(check_id=check["check_id"]):
                self.assertEqual(0, check["metrics"]["intersection_count"])
                self.assertEqual("CONDITIONAL_PASS", check["classification"])

    def test_012_inner_fasteners_and_tool_access(self) -> None:
        by_id = {row["check_id"]: row for row in self.report["checks"]}
        self.assertEqual(
            0,
            by_id["LEFT_INNER_FASTENERS_VS_RIGHT_INNER_FASTENERS"]["metrics"][
                "intersection_count"
            ],
        )
        self.assertEqual(
            0,
            by_id["TOOL_ACCESS_LEFT_VS_OPPOSITE_SUPPORT"]["metrics"][
                "intersection_count"
            ],
        )
        self.assertEqual(
            0,
            by_id["TOOL_ACCESS_RIGHT_VS_OPPOSITE_SUPPORT"]["metrics"][
                "intersection_count"
            ],
        )
        self.assertEqual(
            "PART_MEASUREMENT_REQUIRED",
            self.report["unresolved_checks"]["actual_tool_access"],
        )

    def test_013_all_clutch_and_tensioner_states_registered(self) -> None:
        ids = {row["state_id"] for row in self.report["state_checks"]}
        for side in ("LEFT", "RIGHT"):
            for state in ("DRIVE", "NEUTRAL", "PTO", "FULL_STROKE"):
                self.assertIn(f"{side}_CLUTCH_{state}", ids)
            for tension in ("MINIMUM", "NOMINAL", "MAXIMUM"):
                self.assertIn(f"{side}_DRIVE_TENSIONER_{tension}", ids)
                self.assertIn(f"{side}_PTO_TENSIONER_{tension}", ids)

    def test_014_width_and_pto_end_contract(self) -> None:
        r = self.p["recommended_candidate"]
        self.assertLess(r["total_width_mm"], 300)
        self.assertLessEqual(abs(r["left_pto_outer_end_y_mm"]), 145)
        self.assertLessEqual(abs(r["right_pto_outer_end_y_mm"]), 145)
        imported = cq.importers.importStep(str(STEP)).val()
        self.assertTrue(imported.isValid())
        self.assertLess(imported.BoundingBox().ylen, 300.0)

    def test_015_track_clearance_non_regression_and_z210_reference(self) -> None:
        comparison = self.p["box_bottom_comparison"]
        self.assertEqual(10.0, comparison["z200"]["track_dynamic_clearance_mm"])
        self.assertEqual(20.0, comparison["z210_reference"]["track_dynamic_clearance_mm"])
        self.assertEqual("Z200_UNCHANGED", comparison["selected"])

    def test_016_aluminum_stock_and_member_length(self) -> None:
        r = self.p["recommended_candidate"]
        self.assertEqual(7, r["aluminum_2020_stock_used"])
        self.assertEqual(7, r["aluminum_2040_stock_used"])
        for row in self.allocation:
            values = []
            for value in row["length_each_mm"].split(";"):
                try:
                    values.append(float(value))
                except ValueError:
                    pass
            self.assertTrue(all(value <= 400.0 for value in values))
        plates = [
            row for row in self.allocation
            if row["profile"] == "NON_EXTRUSION_METAL_PLATE"
        ]
        self.assertEqual(1, len(plates))
        self.assertEqual("HOLD_STRUCTURAL_CALCULATION", plates[0]["status"])

    def test_017_ranking_contains_recommended_and_two_alternatives(self) -> None:
        overall = [row for row in self.ranking if row["rank_scope"] == "OVERALL"]
        roles = {row["selection_role"]: row["candidate_id"] for row in overall}
        self.assertEqual(self.b.RECOMMENDED_ID, roles["RECOMMENDED"])
        self.assertEqual(self.b.ALTERNATIVE_A_ID, roles["ALTERNATIVE_A_MINIMUM_CHANGE"])
        self.assertEqual(self.b.ALTERNATIVE_B_ID, roles["ALTERNATIVE_B_6MM_PLATE"])
        for scope in ("STAGE_1", "STAGE_2", "OVERALL"):
            scoped = [row for row in self.ranking if row["rank_scope"] == scope]
            self.assertEqual(10, len(scoped))

    def test_018_step_semantic_reproducibility(self) -> None:
        for key, geometry in self.validation["geometry"].items():
            with self.subTest(key=key):
                self.assertTrue(geometry["semantic_geometry_reproducible"])
                self.assertEqual(geometry["model_signature"], geometry["artifact_signature"])

    def test_019_manifest_and_sha256s_complete(self) -> None:
        manifest_paths = []
        for line in MANIFEST.read_text(encoding="utf-8").splitlines():
            if line and "=" not in line:
                manifest_paths.append(line.split("\t", 1)[0])
        self.assertEqual(list(self.b.PACKAGE_PATHS), manifest_paths)
        sums = {}
        for line in SUMS.read_text(encoding="utf-8").splitlines():
            digest, relative = line.split("  ", 1)
            sums[relative] = digest
        self.assertEqual(set(self.b.PACKAGE_PATHS) - {self.b.SHA256SUMS_NAME}, set(sums))
        for relative, expected in sums.items():
            with self.subTest(relative=relative):
                self.assertEqual(
                    expected,
                    hashlib.sha256((LANE / relative).read_bytes()).hexdigest(),
                )

    def test_020_no_cache_or_forbidden_large_package_file(self) -> None:
        forbidden = []
        for relative in self.b.PACKAGE_PATHS:
            path = LANE / relative
            if (
                "__pycache__" in relative
                or ".pytest_cache" in relative
                or path.suffix.lower() in {".pyc", ".pyo", ".gcode", ".3mf", ".zip"}
            ):
                forbidden.append(relative)
            self.assertLess(path.stat().st_size, 20_000_000)
        self.assertEqual([], forbidden)

    def test_021_builder_verify_is_read_only(self) -> None:
        before = {
            relative: hashlib.sha256((LANE / relative).read_bytes()).hexdigest()
            for relative in self.b.PACKAGE_PATHS
        }
        result = subprocess.run(
            [sys.executable, "-B", str(BUILDER), "--verify"],
            cwd=LANE,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        after = {
            relative: hashlib.sha256((LANE / relative).read_bytes()).hexdigest()
            for relative in self.b.PACKAGE_PATHS
        }
        self.assertEqual(before, after)

    def test_022_release_holds(self) -> None:
        self.assertEqual("HOLD", self.p["physical_fit"])
        self.assertEqual("HOLD", self.p["manufacturing_release"])
        self.assertEqual("NOT_APPROVED", self.p["field_deployment"])
        for key, value in self.p["final_gates"].items():
            if key == "field_deployment":
                self.assertEqual("NOT_APPROVED", value)
            else:
                self.assertEqual("HOLD", value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
