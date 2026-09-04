"""Contract tests for Common Rover v0.8.3 measurement integration."""

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
BUILDER = LANE / "build_common_rover_measurement_integration_v0083.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("common_rover_v0083_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("builder cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json(name: str) -> dict:
    return json.loads((LANE / name).read_text(encoding="utf-8"))


def _csv(name: str) -> list[dict[str, str]]:
    with (LANE / name).open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class CommonRoverV0083Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.b = _load_builder()
        cls.integration = _json(cls.b.INTEGRATION_NAME)
        cls.discrepancies = _json(cls.b.DISCREPANCY_NAME)
        cls.interference = _json(cls.b.INTERFERENCE_NAME)
        cls.validation = _json(cls.b.VALIDATION_NAME)
        cls.rechecks = _csv(cls.b.RECHECK_CSV_NAME)
        cls.fit = _csv(cls.b.FIT_NAME)
        cls.stack = _csv(cls.b.STACK_NAME)
        cls.fixation = _csv(cls.b.FIXATION_NAME)

    def test_001_exact_twenty_package_paths(self) -> None:
        self.assertEqual(20, len(self.b.PACKAGE_PATHS))
        self.assertEqual(20, len(set(self.b.PACKAGE_PATHS)))
        self.assertTrue(all((LANE / item).is_file() for item in self.b.PACKAGE_PATHS))

    def test_002_parent_hashes_protected(self) -> None:
        lanes = (
            ("v008", self.b.V008_HASHES),
            ("v0081", self.b.V0081_HASHES),
            ("v0082", self.b.V0082_HASHES),
        )
        combined = {**self.b.V008_HASHES, **self.b.V0081_HASHES, **self.b.V0082_HASHES}
        paths = [REPO_ROOT / relative for relative in combined]
        existing_count = sum(path.is_file() for path in paths)
        self.assertIn(existing_count, (0, len(paths)))
        self.assertEqual(56, len(combined))
        for key, hashes in lanes:
            evidence = self.integration["protected_parents"][key]
            self.assertEqual(len(hashes), evidence["path_count"])
            for relative, digest in hashes.items():
                self.assertEqual(digest, evidence["hashes"][relative]["actual_sha256"])
                if existing_count:
                    self.assertEqual(digest, hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest())

    def test_003_fixed_architecture_and_parent_candidates(self) -> None:
        fixed = self.integration["fixed_architecture"]
        self.assertEqual(2, fixed["motor_count"])
        self.assertEqual(2, fixed["pto_count"])
        self.assertEqual("PROHIBITED", fixed["common_pto_shaft"])
        self.assertEqual(["DRIVE", "NEUTRAL", "PTO"], fixed["clutch_states"])
        self.assertEqual("S2-REF-T5-BP2.00-OP5.50", fixed["v0081_candidate"])
        self.assertEqual("P3-A5052-T5", fixed["v0082_candidate"])

    def test_004_measurement_classifications(self) -> None:
        allowed = {
            "CONFIRMED_PROVISIONAL",
            "NOMINAL_PART_SIZE",
            "IMAGE_SUPPORTED",
            "REINTERPRETED",
            "SEMANTIC_CONFLICT",
            "MEASUREMENT_CONFLICT",
            "PART_MEASUREMENT_REQUIRED",
            "NOT_FOR_MANUFACTURING",
        }
        self.assertTrue(all(row["classification"] in allowed for row in self.integration["measurements"]))
        self.assertGreaterEqual(len(self.integration["measurements"]), 50)

    def test_005_forbidden_values_not_promoted(self) -> None:
        forbidden = self.discrepancies["forbidden_cad_promotions"]
        self.assertEqual(7, len(forbidden))
        kp = self.integration["kp000_cad"]
        self.assertEqual(10.0, kp["bore_used_for_cad_mm"])
        self.assertNotEqual(11.0, kp["bore_used_for_cad_mm"])
        self.assertEqual("INVENTORY_TOTAL_NOT_INSTALLED_SHAFT_LENGTH", self.integration["shaft"]["total_stock_semantics"])
        self.assertIsNone(self.integration["shaft"]["installed_length_left_mm"])

    def test_006_kp000_updated_envelope(self) -> None:
        kp = self.integration["kp000_cad"]
        self.assertEqual(67.0, kp["overall_width_mm"])
        self.assertEqual(35.0, kp["overall_height_mm"])
        self.assertEqual(17.0, kp["housing_depth_mm"])
        self.assertEqual(18.5, kp["shaft_center_height_mm"])
        self.assertEqual(2, kp["mount_hole_count"])
        self.assertEqual(8.0, kp["mount_hole_diameter_mm"])
        self.assertIsNone(kp["mount_hole_center_distance_mm"])
        self.assertIsNone(kp["total_axial_envelope_mm"])
        self.assertEqual("NONE", kp["grease_port"])

    def test_007_no_manufacturing_hole_geometry(self) -> None:
        kp = self.integration["kp000_cad"]
        self.assertIn("OMITTED", kp["hole_geometry_in_step"])
        support = self.integration["support_plate_non_regression"]
        self.assertFalse(support["mount_holes_in_geometry"])
        self.assertEqual("PART_MEASUREMENT_REQUIRED", support["hole_pattern"])

    def test_008_two_pulley_models_and_safety_authority(self) -> None:
        models = {row["model_id"]: row for row in self.integration["pulley_models"]}
        self.assertEqual(120.0, models["MODEL_A_CONSERVATIVE"]["rotation_envelope_od_mm"])
        self.assertTrue(models["MODEL_A_CONSERVATIVE"]["safety_authority"])
        measured = models["MODEL_B_MEASURED_PROVISIONAL"]
        self.assertEqual(100.0, measured["flange_max_od_mm"])
        self.assertEqual(96.0, measured["toothed_body_od_mm"])
        self.assertEqual(20.0, measured["axial_total_width_mm"])
        self.assertEqual(17.0, measured["tooth_face_width_mm"])
        self.assertEqual(1.0, measured["component_sum_conflict_mm"])

    def test_009_discrepancy_report(self) -> None:
        self.assertEqual(12, self.discrepancies["discrepancy_count"])
        topics = {row["topic"] for row in self.discrepancies["items"]}
        self.assertIn("KP000_BORE", topics)
        self.assertIn("PULLEY_BORE_VS_SHAFT", topics)
        self.assertIn("PTO_SHAFT_1400_MM", topics)
        self.assertIn("PULLEY_AXIAL_COMPONENT_SUM", topics)

    def test_010_shaft_bore_fit_audit(self) -> None:
        by_id = {row["audit_id"]: row for row in self.fit}
        self.assertEqual("0.0", by_id["A"]["diametral_clearance_mm"])
        self.assertEqual("1.0", by_id["B"]["diametral_clearance_mm"])
        self.assertEqual("0.5", by_id["B"]["max_radial_eccentricity_mm"])
        self.assertEqual("FAIL_PROVISIONAL_FOR_LOAD", by_id["B"]["disposition"])
        self.assertEqual({"PROTOTYPE_ONLY", "REBORE/BUSH_REQUIRED", "METAL_HUB_REQUIRED", "REPLACEMENT_REQUIRED"}, {by_id[key]["classification"] for key in ("B1", "B2", "B3", "B4")})

    def test_011_pulley_fixation_comparison(self) -> None:
        self.assertEqual({"F-P1", "F-P2", "F-P3", "F-P4", "F-P5", "F-P6"}, {row["method_id"] for row in self.fixation})
        by_id = {row["method_id"]: row for row in self.fixation}
        self.assertEqual("PROTOTYPE_ONLY", by_id["F-P1"]["status"])
        self.assertIn("RECOMMENDED_CONCEPT", by_id["F-P4"]["status"])
        self.assertIn("RECOMMENDED_CONCEPT", by_id["F-P6"]["status"])

    def test_012_critical_remeasurement_gate(self) -> None:
        critical = [row for row in self.rechecks if row["priority"] == "CRITICAL"]
        self.assertEqual(10, len(critical))
        self.assertTrue(all(row["status"] == "OPEN_REMEASUREMENT_GATE" for row in critical))
        hole = next(row for row in critical if row["measurement_id"] == "C01")
        self.assertIn("OUTER_EDGE_TO_OUTER_EDGE", hole["equation"])
        self.assertIn("INNER_EDGE_TO_INNER_EDGE", hole["equation"])

    def test_013_axial_stack_both_sides(self) -> None:
        self.assertEqual({"LEFT", "RIGHT"}, {row["side"] for row in self.stack})
        self.assertEqual(14, len([row for row in self.stack if row["side"] == "LEFT"]))
        self.assertEqual(14, len([row for row in self.stack if row["side"] == "RIGHT"]))
        self.assertTrue(any(row["hold_value"] == "YES" for row in self.stack))
        total = next(row for row in self.stack if row["side"] == "LEFT" and row["component"] == "60T_TOTAL_ENVELOPE")
        self.assertEqual("20.0", total["measured_mm"])

    def test_014_shaft_length_range_and_stock_semantics(self) -> None:
        axial = self.integration["axial_length"]
        self.assertEqual([139.5, 145.5], axial["preliminary_coverage_range_mm"])
        self.assertIsNone(axial["released_installed_length_range_mm"])
        stock = axial["stock_evaluation"]
        self.assertIn("CANDIDATE", stock["300_mm_stock"])
        self.assertEqual("HOLD", stock["cutting"])
        self.assertIn("NOT_INSTALLED", stock["total_1400_mm"])

    def test_015_support_plate_non_regression(self) -> None:
        support = self.integration["support_plate_non_regression"]
        self.assertEqual(95.0, support["width_mm"])
        self.assertEqual(140.0, support["height_mm"])
        self.assertEqual(5.0, support["thickness_mm"])
        self.assertEqual(22.0, support["kp000_width_increase_from_v0082_envelope_mm"])
        self.assertEqual(14.0, support["plate_side_margin_each_mm"])

    def test_016_intersections_and_clearance_holds(self) -> None:
        summary = self.interference["summary"]
        self.assertEqual(0, summary["intersection_count"])
        self.assertEqual(0, summary["four_belt_intersection_count"])
        self.assertEqual(3.0, summary["kp000_belt_worst_clearance_mm"])
        self.assertEqual(8.5, summary["pulley_kp000_worst_provisional_mm"])
        self.assertGreaterEqual(summary["fail_provisional_count"], 1)

    def test_017_width_and_pto_ends(self) -> None:
        summary = self.interference["summary"]
        self.assertLess(summary["candidate_total_width_mm"], 300.0)
        self.assertLessEqual(max(abs(value) for value in summary["pto_ends_y_mm"]), 145.0)
        self.assertIn("HOLD", summary["physical_total_width"])

    def test_018_step_semantic_geometry(self) -> None:
        for key, name in (("kp000", self.b.KP000_STEP), ("assembly", self.b.ASSEMBLY_STEP)):
            shape = cq.importers.importStep(str(LANE / "artifacts" / name))
            self.assertEqual(self.validation["geometry"][key]["artifact_signature"], self.b._shape_signature(shape))
            self.assertTrue(self.validation["geometry"][key]["semantic_geometry_reproducible"])

    def test_019_svg_warnings_and_critical_values(self) -> None:
        for name in (self.b.OVERVIEW_SVG, self.b.CRITICAL_SVG):
            text = (LANE / "artifacts" / name).read_text(encoding="utf-8")
            self.assertIn("NOT_FOR_MANUFACTURING", text)
            self.assertIn("PART_MEASUREMENT_REQUIRED", text)
        critical = (LANE / "artifacts" / self.b.CRITICAL_SVG).read_text(encoding="utf-8")
        self.assertIn("67.0 mm", critical)
        self.assertIn("18.5 +/-0.5", critical)

    def test_020_manifest_and_sha256s(self) -> None:
        result = self.b._verify_hashes()
        self.assertEqual(20, result["manifest_file_count"])
        self.assertEqual(19, result["hashed_file_count"])
        self.assertEqual(0, result["hash_mismatch_count"])

    def test_021_no_cache_or_large_forbidden_file(self) -> None:
        files = [path for path in LANE.rglob("*") if path.is_file()]
        names = [path.relative_to(LANE).as_posix() for path in files]
        self.assertFalse(any("__pycache__" in name or ".pytest_cache" in name or name.endswith(".pyc") for name in names))
        allowed = {f"artifacts/{self.b.KP000_STEP}", f"artifacts/{self.b.ASSEMBLY_STEP}"}
        self.assertFalse(any(path.stat().st_size > 15_000_000 and path.relative_to(LANE).as_posix() not in allowed for path in files))

    def test_022_builder_verify_read_only(self) -> None:
        before = {item: hashlib.sha256((LANE / item).read_bytes()).hexdigest() for item in self.b.PACKAGE_PATHS}
        result = subprocess.run([sys.executable, "-B", str(BUILDER), "--verify"], cwd=LANE, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, msg=result.stderr)
        after = {item: hashlib.sha256((LANE / item).read_bytes()).hexdigest() for item in self.b.PACKAGE_PATHS}
        self.assertEqual(before, after)

    def test_023_release_states(self) -> None:
        authority = self.integration["authority"]
        self.assertEqual("CONDITIONAL_PASS", authority["measurement_integration"])
        self.assertIn("CONDITIONAL_PASS", authority["envelope_geometry"])
        self.assertEqual("HOLD", authority["physical_fit"])
        self.assertEqual("FAIL_PROVISIONAL", authority["pulley_bore_fit"])
        self.assertEqual("PART_MEASUREMENT_REQUIRED", authority["hole_pattern"])
        self.assertEqual("HOLD", authority["machining"])
        self.assertEqual("NOT_APPROVED", authority["field_deployment"])

    def test_024_validation_contract(self) -> None:
        self.assertEqual("CONDITIONAL_PASS_MEASUREMENT_INTEGRATION", self.validation["overall"])
        self.assertEqual(self.validation["fixed_check_count"], self.validation["fixed_check_pass_count"])
        self.assertEqual("FAIL_PROVISIONAL", self.validation["pulley_bore_fit"])
        self.assertEqual("HOLD", self.validation["manufacturing_release"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
