"""Contract tests for Common Rover KP000 support-plate v0.8.2."""

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
import ezdxf


LANE = Path(__file__).resolve().parents[1]
REPO_ROOT = LANE.parents[2]
BUILDER = LANE / "build_common_rover_kp000_support_plate_v0082.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("common_rover_v0082_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("builder could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json(name: str) -> dict:
    return json.loads((LANE / name).read_text(encoding="utf-8"))


def _csv(name: str) -> list[dict[str, str]]:
    with (LANE / name).open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class CommonRoverV0082Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.b = _load_builder()
        cls.p = _json(cls.b.PARAMETERS_NAME)
        cls.strength = _json(cls.b.STRENGTH_NAME)
        cls.interference = _json(cls.b.INTERFERENCE_NAME)
        cls.validation = _json(cls.b.VALIDATION_NAME)
        cls.measurements = _csv(cls.b.MEASUREMENT_CSV_NAME)
        cls.candidates = _csv(cls.b.CANDIDATES_NAME)
        cls.ranking = _csv(cls.b.RANKING_NAME)
        cls.tools = _csv(cls.b.TOOLS_NAME)
        cls.fasteners = _csv(cls.b.FASTENERS_NAME)

    def test_001_exact_package_paths(self) -> None:
        self.assertEqual(27, len(self.b.PACKAGE_PATHS))
        self.assertEqual(27, len(set(self.b.PACKAGE_PATHS)))
        self.assertTrue(all((LANE / item).is_file() for item in self.b.PACKAGE_PATHS))

    def test_002_v008_and_v0081_protected_hashes(self) -> None:
        combined = {**self.b.V008_HASHES, **self.b.V0081_HASHES}
        paths = [REPO_ROOT / relative for relative in combined]
        existing_count = sum(path.is_file() for path in paths)
        self.assertIn(existing_count, (0, len(paths)))
        protected = self.p["protected_parents"]
        self.assertEqual(10, protected["v008"]["path_count"])
        self.assertEqual(19, protected["v0081"]["path_count"])
        for relative, expected in combined.items():
            lane_key = "v0081" if "v0_8_1" in relative else "v008"
            evidence = protected[lane_key]["hashes"][relative]
            self.assertEqual(expected, evidence["expected_sha256"])
            self.assertEqual(expected, evidence["actual_sha256"])
            self.assertTrue(evidence["match"])
            if existing_count:
                self.assertEqual(expected, hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest())

    def test_003_parent_candidate_and_fixed_coordinates(self) -> None:
        parent = self.p["v0081_fixed_candidate"]
        self.assertEqual("S2-REF-T5-BP2.00-OP5.50", parent["candidate_id"])
        self.assertEqual([-14.0, 14.0], parent["inner_kp000_axis_y_mm"])
        self.assertEqual([-47.0, 47.0], parent["pto_belt_plane_y_mm"])
        self.assertEqual([-87.5, 87.5], parent["outer_kp000_axis_y_mm"])
        self.assertEqual([-119.0, 119.0], parent["drive_belt_plane_y_mm"])

    def test_004_fixed_architecture(self) -> None:
        fixed = self.p["fixed_architecture"]
        self.assertEqual(2, fixed["motor_count"])
        self.assertEqual(2, fixed["pto_count"])
        self.assertEqual("TWO_INDEPENDENT_LATERAL_SHAFTS", fixed["pto_architecture"])
        self.assertEqual("PROHIBITED", fixed["common_pto_shaft"])
        self.assertEqual(["DRIVE", "NEUTRAL", "PTO"], fixed["clutch_states"])
        self.assertEqual("INVERTED_TRAPEZOID_INDEPENDENT_LEFT_RIGHT", fixed["crawler"])

    def test_005_independent_metal_plates_and_thickness(self) -> None:
        plate = self.p["plate_contract"]
        self.assertTrue(plate["left_right_independent"])
        self.assertEqual("PROHIBITED", plate["continuous_center_plate"])
        self.assertEqual("PROHIBITED", plate["load_bearing_printed_plate"])
        self.assertEqual(5.0, plate["thickness_mm"])
        self.assertIn("A5052", self.p["recommended_candidate"]["material"])

    def test_006_measurement_sheet_contract(self) -> None:
        self.assertGreaterEqual(len(self.measurements), 50)
        self.assertEqual(self.b.MEASUREMENT_FIELDS, list(self.measurements[0]))
        parts = {row["part"] for row in self.measurements}
        self.assertTrue({"KP000", "PTO_SHAFT", "PTO_60T_PULLEY", "FASTENER", "TOOL", "ALUMINUM_FRAME"}.issubset(parts))
        self.assertTrue(any(row["status"] == "PART_MEASUREMENT_REQUIRED" for row in self.measurements))

    def test_007_existing_values_not_promoted_to_measurements(self) -> None:
        evidence = self.p["existing_evidence"]
        self.assertEqual(102.0, evidence["user_reported_60t_max_dimension_mm"])
        self.assertEqual("CALIBRATION_PENDING", evidence["user_reported_60t_dimension_meaning"])
        self.assertEqual(120.0, evidence["60t_rotation_safety_envelope_diameter_mm"])
        self.assertIn("UNVERIFIED", evidence["kp000_existing_geometry"]["status"])
        self.assertFalse(evidence["actual_kp000_manufacturer_drawing_found"])

    def test_008_four_outlines_and_four_materials(self) -> None:
        self.assertEqual({"P1", "P2", "P3", "P4"}, set(self.b.OUTLINES))
        self.assertEqual({"A5052", "A6061", "STEEL3", "STEEL"}, set(self.b.MATERIALS))
        self.assertEqual(16, len(self.candidates))

    def test_009_recommended_and_alternatives(self) -> None:
        self.assertEqual("P3-A5052-T5", self.p["recommended_candidate"]["candidate_id"])
        self.assertEqual(["P2-A6061-T5", "P3-STEEL-T4.5"], self.p["alternative_ids"])
        roles = {row["selection_role"]: row["candidate_id"] for row in self.ranking if row["selection_role"]}
        self.assertEqual("P3-A5052-T5", roles["RECOMMENDED"])
        self.assertEqual("P2-A6061-T5", roles["ALTERNATIVE_A"])
        self.assertEqual("P3-STEEL-T4.5", roles["ALTERNATIVE_B"])

    def test_010_hole_patterns_not_for_manufacturing(self) -> None:
        plate = self.p["plate_contract"]
        self.assertIn("NOT_FOR_MANUFACTURING", plate["hole_geometry_status"])
        self.assertEqual("PART_MEASUREMENT_REQUIRED", self.p["authority"]["hole_pattern"])
        for row in self.candidates:
            self.assertEqual("PART_MEASUREMENT_REQUIRED", row["kp000_hole_pattern_status"])
            self.assertEqual("PART_MEASUREMENT_REQUIRED", row["frame_hole_pattern_status"])

    def test_011_v0081_clearance_non_regression(self) -> None:
        base = self.p["v0081_fixed_candidate"]
        self.assertGreaterEqual(base["pto_belt_frame_mm"], 15.0)
        self.assertGreaterEqual(base["pto_belt_fasteners_mm"], 20.0)
        self.assertGreaterEqual(base["pto_residual_mm"], 10.0)
        self.assertGreaterEqual(base["pto_60t_fixed_mm"], 13.0)
        self.assertGreaterEqual(base["track_dynamic_upper_mm"], 10.0)

    def test_012_intersections_zero(self) -> None:
        summary = self.interference["summary"]
        self.assertEqual(0, summary["intersection_count"])
        self.assertEqual(0, summary["belt_intersection_count"])
        self.assertEqual(0, summary["fastener_intersection_count"])
        self.assertEqual(0, summary["tool_intersection_count"])
        self.assertTrue(all(row["intersection_count"] == 0 for row in self.interference["checks"]))

    def test_013_width_and_pto_ends(self) -> None:
        summary = self.interference["summary"]
        self.assertLessEqual(summary["total_width_mm"], 290.0)
        self.assertLessEqual(max(abs(value) for value in summary["pto_ends_y_mm"]), 145.0)

    def test_014_tool_access_candidate_and_hold(self) -> None:
        self.assertTrue(all(float(row["tool_clearance_mm"]) >= 10.0 for row in self.tools))
        self.assertTrue(all(int(row["opposite_support_intersection_count"]) == 0 for row in self.tools))
        self.assertTrue(all("HOLD" in row["status"] for row in self.tools))
        self.assertEqual("ACTIVE_TOOL_INSERTION_ALONG_X", self.p["tool_access"]["strategy"])

    def test_015_fastener_comparison_and_hybrid(self) -> None:
        self.assertEqual({"F1", "F2", "F3", "F4", "F5"}, {row["fastener_id"] for row in self.fasteners})
        rec = self.p["fastener_recommendation"]
        self.assertTrue(rec["kp000_to_plate"].startswith("F2"))
        self.assertTrue(rec["plate_to_frame"].startswith("F5"))
        self.assertIn("HOLD", rec["final_selection"])

    def test_016_alignment_and_assembly(self) -> None:
        self.assertEqual(12, len(self.p["assembly_sequence"]))
        text = " ".join(self.p["assembly_sequence"]).lower()
        self.assertIn("rotate", text)
        self.assertIn("independent", text)
        self.assertEqual("ALIGNMENT_LIMIT_HOLD", self.p["plate_contract"]["shaft_alignment_limit"])

    def test_017_load_cases_and_required_parameters(self) -> None:
        self.assertEqual({"LC1", "LC2", "LC3", "LC4", "LC5"}, {row["load_case"] for row in self.strength["load_cases"]})
        self.assertEqual(10, len(self.strength["required_inputs"]))
        self.assertEqual("HYPOTHETICAL_COMPARISON_LOADS_ONLY", self.strength["load_authority"])

    def test_018_strength_is_analytical_only(self) -> None:
        self.assertEqual("CONDITIONAL_PASS_ANALYTICAL_ONLY", self.strength["status"])
        self.assertGreaterEqual(self.strength["recommended_minimum_safety_factor"], 2.0)
        self.assertIn("hole_bearing", self.strength["not_calculated_as_pass"])
        self.assertIn("T_NUT_SLIP_LIMIT", self.strength["release_blockers"])

    def test_019_deflection_clearance_coupling(self) -> None:
        self.assertGreaterEqual(self.strength["recommended_clearance_after_deflection_mm"], 8.0)
        self.assertGreaterEqual(self.strength["recommended_60t_clearance_after_deflection_mm"], 10.0)
        self.assertGreater(self.strength["recommended_deflection_mm"], 0.0)

    def test_020_dxf_and_svg_warnings(self) -> None:
        for name in (self.b.LEFT_DXF, self.b.RIGHT_DXF):
            path = LANE / "artifacts" / name
            text = path.read_text(encoding="utf-8")
            self.assertIn("NOT_FOR_MANUFACTURING", text)
            self.assertIn("PART_MEASUREMENT_REQUIRED", text)
            self.assertIn("REFERENCE_HOLES_NOT_FOR_MANUFACTURING", text)
            document = ezdxf.readfile(path)
            self.assertEqual(11, len(document.modelspace()))
        for name in (self.b.OVERVIEW_SVG, self.b.TOP_SVG, self.b.FRONT_SVG, self.b.SIDE_SVG, self.b.DIMENSIONS_SVG):
            text = (LANE / "artifacts" / name).read_text(encoding="utf-8")
            self.assertIn("NOT_FOR_MANUFACTURING", text)

    def test_021_step_semantic_geometry(self) -> None:
        for key, name in (("assembly", self.b.ASSEMBLY_STEP), ("left", self.b.LEFT_STEP), ("right", self.b.RIGHT_STEP)):
            shape = cq.importers.importStep(str(LANE / "artifacts" / name))
            self.assertEqual(
                self.validation["geometry"][key]["artifact_signature"],
                self.b._shape_signature(shape),
            )
            self.assertTrue(self.validation["geometry"][key]["semantic_geometry_reproducible"])

    def test_022_manifest_and_sha256s(self) -> None:
        result = self.b._verify_hashes()
        self.assertEqual(27, result["manifest_file_count"])
        self.assertEqual(26, result["hashed_file_count"])
        self.assertEqual(0, result["hash_mismatch_count"])

    def test_023_no_cache_or_forbidden_large_file(self) -> None:
        names = [path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file()]
        self.assertFalse(any("__pycache__" in name or ".pytest_cache" in name or name.endswith(".pyc") for name in names))
        allowed_large = {f"artifacts/{self.b.ASSEMBLY_STEP}", f"artifacts/{self.b.LEFT_STEP}", f"artifacts/{self.b.RIGHT_STEP}"}
        self.assertFalse(any((LANE / name).stat().st_size > 15_000_000 and name not in allowed_large for name in names))

    def test_024_builder_verify_is_read_only(self) -> None:
        before = {item: hashlib.sha256((LANE / item).read_bytes()).hexdigest() for item in self.b.PACKAGE_PATHS}
        result = subprocess.run([sys.executable, "-B", str(BUILDER), "--verify"], cwd=LANE, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, msg=result.stderr)
        after = {item: hashlib.sha256((LANE / item).read_bytes()).hexdigest() for item in self.b.PACKAGE_PATHS}
        self.assertEqual(before, after)

    def test_025_environment_and_release_holds(self) -> None:
        authority = self.p["authority"]
        self.assertEqual("HOLD", authority["physical_fit"])
        self.assertEqual("HOLD", authority["material_selection"])
        self.assertEqual("HOLD", authority["manufacturing"])
        self.assertEqual("NOT_APPROVED", authority["field_deployment"])
        env = self.p["environment"]
        self.assertTrue(env["drain_downward"])
        self.assertEqual("REQUIRED", env["galvanic_isolation"])

    def test_026_validation_contract(self) -> None:
        self.assertEqual("CONDITIONAL_PASS_ANALYTICAL_ONLY", self.validation["overall"])
        self.assertEqual(self.validation["fixed_check_count"], self.validation["fixed_check_pass_count"])
        self.assertEqual("HOLD", self.validation["manufacturing_release"])
        self.assertEqual("NOT_APPROVED", self.validation["field_deployment"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
