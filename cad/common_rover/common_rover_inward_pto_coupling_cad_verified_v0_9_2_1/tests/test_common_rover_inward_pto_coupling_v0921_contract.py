#!/usr/bin/env python3
"""Integrated v0.9.2.1 evidence and release-gate contract."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import unittest
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))

import build_common_rover_inward_pto_coupling_cad_verified_v0921 as build  # noqa: E402


def read_json(name: str):
    return json.loads((LANE / name).read_text(encoding="utf-8"))


def read_csv(name: str):
    with (LANE / name).open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class IntegratedContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.params = read_json(build.PARAMETERS_NAME)
        cls.validation = read_json(build.VALIDATION_NAME)
        cls.registry = read_json(build.REGISTRY_NAME)
        cls.report = read_json(build.INTERFERENCE_REPORT_NAME)
        cls.matrix = read_csv(build.CLEARANCE_MATRIX_NAME)
        cls.sweep = read_csv(build.SWEEP_NAME)

    def test_001_exact_55_paths(self) -> None:
        self.assertEqual(len(build.PACKAGE_PATHS), 55)
        self.assertEqual(build._lane_files(), sorted(build.PACKAGE_PATHS))

    def test_002_parent_protection(self) -> None:
        self.assertEqual(build.parent_protection_audit()["mismatches"], [])

    def test_003_parent_zip_sha(self) -> None:
        audit = build.parent_protection_audit()
        self.assertEqual(audit["v092_zip_sha256"], build.PARENT_ZIP_SHA256)

    def test_004_v092_baseline(self) -> None:
        self.assertEqual(build.verify_baseline_v092()["status"], "PASS")

    def test_005_named_shapes_unique(self) -> None:
        self.assertTrue(self.registry["names_unique"])

    def test_006_required_named_shapes(self) -> None:
        names = {row["shape_name"] for row in self.registry["entries"]}
        self.assertTrue(build.REQUIRED_SHAPE_NAMES <= names)

    def test_007_actual_boolean_api_recorded(self) -> None:
        self.assertTrue(all("Shape.intersect" in row["calculation_api"] for row in self.matrix))

    def test_008_actual_distance_api_recorded(self) -> None:
        self.assertTrue(all("BRepExtrema" in row["calculation_api"] for row in self.matrix))

    def test_009_no_fixed_intersection_count(self) -> None:
        source = (LANE / build.BUILDER_NAME).read_text(encoding="utf-8")
        self.assertNotIn('"intersection_count": 0', source)
        self.assertNotIn('"intersection_solid_count": 0', source)

    def test_010_no_fixed_minimum_distance_report(self) -> None:
        self.assertEqual(
            self.report["calculation_authority"],
            "ACTUAL_CAD_SHAPE_PAIR_RESULTS",
        )
        self.assertEqual(len(self.report["rows"]), len(self.matrix))

    def test_011_canaries(self) -> None:
        self.assertTrue(all(row["canary_pass"] for row in build.run_canary_tests()))

    def test_012_error_never_passes(self) -> None:
        import cad_clearance_engine_v0921 as engine
        row = engine.build_pair_result(
            "ERR", "A", None, "B", None, "TEST", 0.0, "error injection"
        )
        self.assertEqual(row["result"], "ERROR")

    def test_013_all_required_states(self) -> None:
        states = {row["coupling_state"] for row in self.matrix}
        self.assertTrue({"RETRACTED", "PARTIAL", "ENGAGED", "FULL_SWEEP"} <= states)

    def test_014_sample_interval(self) -> None:
        self.assertTrue(all(float(row["sampling_interval_mm"]) <= 0.5 for row in self.sweep))

    def test_015_central_no_fail_or_error(self) -> None:
        central = [
            row for row in self.matrix
            if row["coupling_state"] != "UPSTREAM_INHERITED_CONDITIONAL"
        ]
        self.assertFalse(any(row["result"] in {"FAIL", "ERROR"} for row in central))

    def test_016_coupling_pair_intersections_zero(self) -> None:
        rows = [row for row in self.matrix if "opposite" in row["note"]]
        self.assertTrue(rows)
        self.assertTrue(all(float(row["intersection_volume_mm3"]) <= 0.01 for row in rows))

    def test_017_frame_and_wiring_intersections_zero(self) -> None:
        rows = [
            row for row in self.matrix
            if "central frame" in row["note"] or "wiring" in row["note"]
        ]
        self.assertTrue(rows)
        self.assertTrue(all(float(row["intersection_volume_mm3"]) <= 0.01 for row in rows))

    def test_018_install_removal_intersections_zero(self) -> None:
        rows = [
            row for row in self.matrix
            if "installation" in row["note"] or "removal" in row["note"]
        ]
        self.assertTrue(rows)
        self.assertTrue(all(float(row["intersection_volume_mm3"]) <= 0.01 for row in rows))

    def test_019_full_sweep_no_fail_error(self) -> None:
        self.assertFalse(any(row["result"] in {"FAIL", "ERROR"} for row in self.sweep))

    def test_020_independent_power_graph(self) -> None:
        graph = read_json(build.POWER_GRAPH_NAME)
        self.assertTrue(graph["left_right_independent"])
        self.assertIn("COMMON_PTO_SHAFT", graph["prohibited_nodes"])

    def test_021_e2_signals_separate(self) -> None:
        graph = read_json(build.STATE_GRAPH_NAME)
        self.assertIn("UNIT_PRESENT", graph["signals"])
        self.assertIn("UNIT_ID", graph["signals"])
        self.assertIn("LEFT_PTO_COUPLING_ENGAGED", graph["signals"])
        self.assertIn("RIGHT_PTO_COUPLING_ENGAGED", graph["signals"])

    def test_022_architecture_counts(self) -> None:
        fixed = self.params["fixed_contract"]
        self.assertEqual(fixed["motor_count"], 2)
        self.assertEqual(fixed["pto_count"], 2)
        self.assertEqual(fixed["slide_clutch_count"], 2)
        self.assertEqual(fixed["total_belt_count"], 4)
        self.assertEqual(fixed["common_pto_shaft"], "PROHIBITED")

    def test_023_jig_dimensions(self) -> None:
        jig = self.params["dry_fit_jig"]
        coupling = self.params["central_coupling"]
        self.assertEqual(coupling["center_gap_mm"], 36.0)
        self.assertEqual(coupling["left_stub_length_mm"], 12.5)
        self.assertEqual(coupling["right_stub_length_mm"], 12.5)
        self.assertEqual(jig["test_shaft_count"], 2)
        self.assertFalse(jig["single_continuous_shaft_used"])

    def test_024_release_holds(self) -> None:
        gates = self.params["release_gates"]
        self.assertEqual(gates["physical_fit"], "HOLD")
        self.assertEqual(gates["load_capacity"], "HOLD")
        self.assertEqual(gates["shaft_cutting"], "HOLD")
        self.assertEqual(gates["manufacturing"], "HOLD")
        self.assertEqual(gates["powered_test"], "NOT_APPROVED")
        self.assertEqual(gates["field_deployment"], "NOT_APPROVED")

    def test_025_measurement_not_performed(self) -> None:
        rows = read_csv(build.MEASUREMENT_NAME)
        self.assertTrue(rows)
        self.assertTrue(all(row["status"] == "PHYSICAL_TEST_NOT_PERFORMED" for row in rows))

    def test_026_warning_labels(self) -> None:
        text = (LANE / build.NO_LOAD_NAME).read_text(encoding="utf-8")
        for warning in (
            "NO_LOAD_GEOMETRY_DUMMY", "LEFT_INDEPENDENT_PTO",
            "RIGHT_INDEPENDENT_PTO", "NO_COMMON_SHAFT", "NOT_FOR_TORQUE",
            "NOT_FOR_POWERED_ROTATION", "HAND_FIT_ONLY",
            "NOT_FOR_MANUFACTURING",
        ):
            self.assertIn(warning, text)

    def test_027_validation_gate(self) -> None:
        self.assertEqual(self.validation["status"], "PASS")
        self.assertEqual(self.validation["authority_update_gate"], "PASS")

    def test_028_manifest_and_hashes(self) -> None:
        self.assertEqual(build.verify_manifest()["manifest_path_count"], 55)
        self.assertEqual(build.verify_hashes()["mismatches"], [])

    def test_029_step_stl_semantics(self) -> None:
        results = build.verify_step_semantics()
        self.assertEqual(len(results), 20)
        self.assertTrue(all(row["pass"] for row in results))

    def test_030_svg_count(self) -> None:
        self.assertEqual(len(build.SVG_FILES), 7)
        self.assertTrue(all((LANE / rel).stat().st_size > 500 for rel in build.SVG_FILES))

    def test_031_zip_exists_and_exact(self) -> None:
        path = build.latest_handoff_zip()
        self.assertIsNotNone(path)
        self.assertTrue(build.verify_zip(path)["exact_scope"])

    def test_032_authority_not_updated_on_failed_gate(self) -> None:
        repo = build.repository_audit()
        if repo["pointer_authority"] == "V0921":
            self.assertEqual(self.validation["authority_update_gate"], "PASS")

    def test_033_sha256sums_has_54_rows(self) -> None:
        self.assertEqual(len(build._parse_sha256sums()), 54)

    def test_034_no_cache_or_forbidden_package_files(self) -> None:
        paths = build._lane_files()
        self.assertFalse(any("__pycache__" in path or path.endswith(".pyc") for path in paths))
        self.assertFalse(any(path.endswith((".dxf", ".dwg", ".fcstd")) for path in paths))

    def test_035_upstream_scope_not_overclaimed(self) -> None:
        self.assertEqual(
            self.params["authority_scope"]["upstream_powertrain"],
            "INHERITED_CONDITIONAL_PARAMETRIC_SHAPE_RECONSTRUCTION",
        )
        self.assertFalse(
            self.params["authority_scope"]["actual_cad_full_system_verified"]
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
