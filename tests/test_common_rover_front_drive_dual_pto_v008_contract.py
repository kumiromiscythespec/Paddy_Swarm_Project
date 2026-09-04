"""Contract tests for Common Rover front-drive dual-PTO authority v0.8."""

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


REPO_ROOT = Path(__file__).resolve().parents[1]
LANE = (
    REPO_ROOT
    / "cad"
    / "common_rover"
    / "front_drive_dual_pto_design_authority_v0_8"
)
BUILDER = LANE / "build_common_rover_front_drive_dual_pto_v008.py"
PARAMETERS = LANE / "common_rover_front_drive_dual_pto_parameters_v008.json"
AUTHORITY = LANE / "common_rover_front_drive_dual_pto_design_authority_v008.md"
REPORT = LANE / "common_rover_front_drive_dual_pto_interference_report_v008.json"
MATRIX = LANE / "common_rover_front_drive_dual_pto_interference_matrix_v008.csv"
ALLOCATION = (
    LANE / "common_rover_front_drive_dual_pto_aluminum_allocation_v008.csv"
)
VALIDATION = LANE / "common_rover_front_drive_dual_pto_validation_v008.json"
STEP = (
    LANE
    / "artifacts"
    / "PS-CR-FRONT-DRIVE-DUAL-PTO-V008-INSPECTION.step"
)
SVG = (
    LANE
    / "artifacts"
    / "PS-CR-FRONT-DRIVE-DUAL-PTO-V008-OVERVIEW.svg"
)


def _load_builder():
    spec = importlib.util.spec_from_file_location("common_rover_v008_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class CommonRoverFrontDriveDualPtoV008Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = _load_builder()
        cls.parameters = _json(PARAMETERS)
        cls.report = _json(REPORT)
        cls.validation = _json(VALIDATION)
        cls.matrix = _csv(MATRIX)
        cls.allocation = _csv(ALLOCATION)
        cls.authority_text = AUTHORITY.read_text(encoding="utf-8")

    def test_001_exact_ten_paths_exist(self) -> None:
        paths = [REPO_ROOT / path for path in self.builder.EXPECTED_PATHS]
        self.assertEqual(10, len(paths))
        self.assertTrue(all(path.is_file() for path in paths))

    def test_002_builder_verify_is_read_only_and_passes(self) -> None:
        before = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (PARAMETERS, AUTHORITY, REPORT, MATRIX, ALLOCATION, VALIDATION, STEP, SVG)
        }
        result = subprocess.run(
            [sys.executable, "-B", str(BUILDER), "--verify"],
            cwd=LANE,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("PASS_FOR_ENVELOPE_AUTHORITY_WITH_HOLDS", result.stdout)
        after = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in before
        }
        self.assertEqual(before, after)

    def test_003_coordinate_and_order(self) -> None:
        p = self.parameters
        self.assertEqual("ROVER_FRONT", p["coordinate_system"]["+X"])
        self.assertEqual("ROVER_LEFT_WHEN_FACING_FORWARD", p["coordinate_system"]["+Y"])
        self.assertEqual(0.0, p["coordinate_system"]["ground_z_mm"])
        self.assertEqual(
            "X_PTO > X_POWER_TRANSMISSION > X_MOTOR > X_CBOX > X_BBOX",
            p["layout_order_relation"],
        )

    def test_004_fixed_box_dimensions_and_orientation(self) -> None:
        boxes = self.parameters["boxes"]
        self.assertEqual({"x": 130.0, "y": 140.0, "z": 105.0}, boxes["cbox"]["external_size_mm"])
        self.assertEqual({"x": 150.0, "y": 220.0, "z": 150.0}, boxes["bbox"]["external_size_mm"])
        self.assertEqual("FRONT_OF_BBOX", boxes["cbox"]["position"])
        self.assertEqual("REAR_OF_CBOX", boxes["bbox"]["position"])
        self.assertEqual("PROHIBITED", boxes["cbox"]["structural_role"])
        self.assertEqual("PROHIBITED", boxes["bbox"]["structural_role"])

    def test_005_battery_cassette_fit_remains_hold(self) -> None:
        cassette = self.parameters["battery_cassette"]
        self.assertEqual({"x": 125.0, "y": 180.0, "z": 120.0}, cassette["external_size_mm"])
        self.assertEqual("FRONT_TOWARD_CBOX", cassette["contact_face"])
        self.assertEqual("FIELD_MEASUREMENT_REQUIRED", cassette["fit_status"])
        check = next(
            row
            for row in self.report["checks"]
            if row["check_id"] == "BBOX_EFFECTIVE_INTERIOR_VS_CASSETTE"
        )
        self.assertEqual("HOLD / FIELD_MEASUREMENT_REQUIRED", check["classification"])
        self.assertIsNone(check["metrics"]["actual_effective_interior_mm"])

    def test_006_height_contract(self) -> None:
        env = self.parameters["environment_and_height"]
        self.assertGreaterEqual(env["box_bottom_minimum_z_mm"], 200.0)
        self.assertEqual(350.0, env["box_top_maximum_z_mm"])
        self.assertGreaterEqual(env["candidate_motor_axis_z_mm"], 350.0)
        self.assertGreaterEqual(
            env["candidate_pto_axis_z_mm"],
            env["candidate_motor_axis_z_mm"],
        )

    def test_007_two_inward_motors_only(self) -> None:
        motors = self.parameters["motors"]
        self.assertEqual(2, motors["count"])
        self.assertEqual("PROHIBITED", motors["third_motor"])
        self.assertEqual("-Y_INWARD", motors["left"]["shaft_direction"])
        self.assertEqual("+Y_INWARD", motors["right"]["shaft_direction"])
        self.assertEqual("PROHIBITED", motors["box_mounting"])

    def test_008_slide_clutch_contract(self) -> None:
        clutch = self.parameters["slide_clutches"]
        self.assertEqual(2, clutch["count"])
        self.assertEqual(["DRIVE", "NEUTRAL", "PTO"], clutch["states"])
        self.assertEqual(
            "MECHANICALLY_PROHIBITED",
            clutch["rules"]["same_side_drive_and_pto_simultaneous_engagement"],
        )
        self.assertEqual(
            "DRIVE_TO_NEUTRAL_TO_PTO_AND_REVERSE",
            clutch["rules"]["state_transition"],
        )
        self.assertEqual("PART_MEASUREMENT_REQUIRED", clutch["detail_status"])

    def test_009_two_independent_pto_ports(self) -> None:
        pto = self.parameters["pto"]
        self.assertEqual(2, pto["count"])
        self.assertEqual("PROHIBITED", pto["common_axis"])
        self.assertEqual("+Y_OUTWARD", pto["left_output_direction"])
        self.assertEqual("-Y_OUTWARD", pto["right_output_direction"])
        self.assertEqual(4, pto["kp000_candidate_count"])
        self.assertTrue(pto["60t_between_two_bearings_each_side"])

    def test_010_belt_and_pulley_contract(self) -> None:
        belt = self.parameters["belt_and_pulley"]
        self.assertEqual("HTD_5M_STANDARD", belt["standard"])
        self.assertEqual(15.0, belt["belt_width_mm"])
        self.assertEqual(20, belt["driver_teeth"])
        self.assertEqual(60, belt["driven_teeth"])
        self.assertEqual(3.0, belt["reduction_ratio"])
        self.assertEqual(4, len(belt["independent_belt_runs"]))
        self.assertEqual(120.0, belt["60t_safety_envelope_diameter_mm"])
        self.assertEqual(102.0, belt["60t_reported_max_dimension_mm"])
        self.assertEqual("CALIBRATION_PENDING", belt["60t_reported_dimension_meaning"])

    def test_011_inverted_trapezoid_crawler_contract(self) -> None:
        crawler = self.parameters["crawler"]
        self.assertEqual("INVERTED_TRAPEZOID_TOP_LONGER_THAN_BOTTOM", crawler["geometry"])
        self.assertEqual(1, crawler["each_side"]["front_upper_drive_wheel_count"])
        self.assertEqual(1, crawler["each_side"]["rear_upper_idler_count"])
        self.assertEqual([3, 4], crawler["each_side"]["lower_roller_count_candidates"])
        self.assertEqual("PROHIBITED", crawler["common_drive_shaft"])
        self.assertEqual("PROHIBITED", crawler["rectangular_track"])

    def test_012_width_contract_is_hold_not_release(self) -> None:
        width = self.parameters["width"]
        self.assertEqual(299.0, width["hard_maximum_mm"])
        self.assertEqual([286.0, 290.0], width["target_range_mm"])
        self.assertEqual(55.0, width["track_width_each_mm"])
        self.assertLessEqual(width["central_lower_structure_maximum_width_mm"], 180.0)
        self.assertLessEqual(width["candidate_total_width_mm"], 290.0)
        self.assertEqual("PART_MEASUREMENT_REQUIRED", width["physical_release"])

    def test_013_required_candidate_intersections_are_zero_but_hold(self) -> None:
        required = (
            "LEFT_DRIVE_BELT_ENVELOPE_VS_FRAME",
            "RIGHT_DRIVE_BELT_ENVELOPE_VS_FRAME",
            "LEFT_PTO_BELT_ENVELOPE_VS_FRAME",
            "RIGHT_PTO_BELT_ENVELOPE_VS_FRAME",
            "LEFT_DRIVE_BELT_ENVELOPE_VS_FASTENERS",
            "RIGHT_DRIVE_BELT_ENVELOPE_VS_FASTENERS",
            "LEFT_PTO_BELT_ENVELOPE_VS_FASTENERS",
            "RIGHT_PTO_BELT_ENVELOPE_VS_FASTENERS",
            "LEFT_SLIDE_CLUTCH_FULL_STROKE_VS_FRAME",
            "RIGHT_SLIDE_CLUTCH_FULL_STROKE_VS_FRAME",
            "TRACK_LEFT_DYNAMIC_ENVELOPE_VS_UPPER_STRUCTURE",
            "TRACK_RIGHT_DYNAMIC_ENVELOPE_VS_UPPER_STRUCTURE",
        )
        by_id = {row["check_id"]: row for row in self.report["checks"]}
        for check_id in required:
            with self.subTest(check_id=check_id):
                self.assertEqual(0, by_id[check_id]["metrics"]["intersection_count"])
                self.assertTrue(by_id[check_id]["classification"].startswith("HOLD"))

    def test_014_all_clutch_states_and_tensioner_ranges_registered(self) -> None:
        ids = {row["check_id"] for row in self.report["checks"]}
        for side in ("LEFT", "RIGHT"):
            for state in ("DRIVE", "NEUTRAL", "PTO"):
                self.assertIn(f"{side}_CLUTCH_STATE_{state}", ids)
            for state in ("MINIMUM", "NOMINAL", "MAXIMUM"):
                self.assertIn(f"{side}_DRIVE_TENSIONER_{state}", ids)
                self.assertIn(f"{side}_PTO_TENSIONER_{state}", ids)

    def test_015_no_false_physical_pass(self) -> None:
        self.assertEqual(0, self.report["summary"]["fail_count"])
        self.assertGreater(self.report["summary"]["hold_count"], 0)
        self.assertEqual("NOT_APPROVED", self.report["summary"]["physical_release"])
        forbidden = {"PASS", "PASS_PHYSICAL", "PRODUCTION_READY"}
        for row in self.report["checks"]:
            self.assertNotIn(row["classification"], forbidden)

    def test_016_step_semantic_geometry_and_width(self) -> None:
        imported = cq.importers.importStep(str(STEP)).val()
        self.assertTrue(imported.isValid())
        box = imported.BoundingBox()
        self.assertGreater(len(imported.Solids()), 40)
        self.assertLessEqual(round(box.ylen, 3), 290.0)
        self.assertEqual(
            self.validation["geometry"]["model_semantic_signature"],
            self.validation["geometry"]["artifact_semantic_signature"],
        )
        self.assertTrue(self.validation["geometry"]["semantic_geometry_reproducible"])

    def test_017_material_allocation_is_within_declared_stock(self) -> None:
        validation = self.validation["material_allocation"]
        self.assertEqual(8, validation["2020_candidate_stock_used"])
        self.assertEqual(7, validation["2040_candidate_stock_used"])
        self.assertLessEqual(validation["2020_candidate_stock_used"], validation["2020_available"])
        self.assertLessEqual(validation["2040_candidate_stock_used"], validation["2040_available"])
        self.assertEqual(0, validation["member_over_400_count"])
        self.assertEqual("HOLD", validation["cutting_release"])
        self.assertEqual(
            "ADDITIONAL_PURCHASE_REQUIRED_COUNT_AND_SIZE_PENDING",
            validation["non_extrusion_connector_hardware"],
        )
        connector_rows = [
            row
            for row in self.allocation
            if row["profile"] == "NON_EXTRUSION_METAL_HARDWARE"
        ]
        self.assertEqual(1, len(connector_rows))
        self.assertEqual("ADDITIONAL_PURCHASE_REQUIRED", connector_rows[0]["status"])
        for row in self.allocation:
            values = [
                float(value)
                for value in row["required_length_each_mm"].split(";")
                if value and value != "0"
            ]
            self.assertTrue(all(value <= 400.0 for value in values))

    def test_018_superseded_and_holds_are_explicit(self) -> None:
        superseded = set(self.parameters["superseded"])
        self.assertIn("LEFT_RIGHT_PTO_COMMON_SHAFT", superseded)
        self.assertIn("BBOX_200_X_150_X_120_MM", superseded)
        self.assertIn("COMMON_SYNCHRONIZED_CLUTCH_SELECTOR", superseded)
        self.assertIn("PTO_60T_102MM_ONLY_ROTATION_ENVELOPE", superseded)
        holds = set(self.parameters["hold_items"])
        self.assertIn("ACTUAL_MOTOR_ENVELOPE", holds)
        self.assertIn("BBOX_EFFECTIVE_INTERIOR", holds)
        self.assertIn("TENSIONER_POSITION_AND_FULL_RANGE", holds)
        self.assertIn("TRACK_LATERAL_DYNAMIC_RUNOUT", holds)

    def test_019_final_gates(self) -> None:
        gates = self.parameters["final_gates"]
        for key, value in gates.items():
            if key == "FIELD_DEPLOYMENT":
                self.assertEqual("NOT_APPROVED", value)
            else:
                self.assertEqual("HOLD", value)

    def test_020_design_authority_contains_safety_language(self) -> None:
        text = self.authority_text
        self.assertIn("not manufacturing CAD", text)
        self.assertIn("Zero candidate intersections are not a physical PASS", text)
        self.assertIn("diameter 120", text)
        self.assertIn("field deployment is `NOT_APPROVED`", text)
        self.assertIn("400 mm", text)

    def test_021_machine_report_and_csv_agree(self) -> None:
        json_by_id = {row["check_id"]: row for row in self.report["checks"]}
        csv_by_id = {row["check_id"]: row for row in self.matrix}
        self.assertEqual(set(json_by_id), set(csv_by_id))
        for check_id, row in json_by_id.items():
            self.assertEqual(row["classification"], csv_by_id[check_id]["classification"])

    def test_022_measurement_evidence_is_narrowly_scoped(self) -> None:
        evidence = self.parameters["measurement_evidence"]
        self.assertEqual(0, evidence["actual_final_component_measurement_count"])
        self.assertFalse(evidence["htd5m_phase1"]["powered_or_field_authority"])
        self.assertEqual(
            "DATASHEET_OR_PRODUCT_DESCRIPTION_ONLY",
            evidence["uxcell_motor_bracket_product_description"]["status"],
        )
        self.assertFalse(
            evidence["uxcell_motor_bracket_product_description"][
                "actual_motor_envelope_authority"
            ]
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
