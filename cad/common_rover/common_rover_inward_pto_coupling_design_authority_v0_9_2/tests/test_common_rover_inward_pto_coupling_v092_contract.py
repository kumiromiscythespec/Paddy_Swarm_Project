#!/usr/bin/env python3
"""Contract tests for Common Rover inward PTO coupling v0.9.2."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_common_rover_inward_pto_coupling_v092.py"
SPEC = importlib.util.spec_from_file_location("v092_builder_contract", BUILDER)
assert SPEC and SPEC.loader
b = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(b)


def load_json(name: str):
    return json.loads((LANE / name).read_text(encoding="utf-8"))


def load_csv(name: str):
    with (LANE / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = load_json(b.PARAMETERS_NAME)
        cls.valid = load_json(b.VALIDATION_NAME)
        cls.baseline = load_json(b.BASELINE_NAME)
        cls.power = load_json(b.POWER_GRAPH_NAME)
        cls.states = load_json(b.STATE_GRAPH_NAME)
        cls.interference = load_json(b.INTERFERENCE_REPORT_NAME)
        cls.rec = cls.params["recommended"]

    def test_001_exact_45_paths(self):
        actual = sorted(
            path.relative_to(LANE).as_posix()
            for path in LANE.rglob("*") if path.is_file()
        )
        self.assertEqual(actual, sorted(b.PACKAGE_PATHS))

    def test_002_parent_protection(self):
        audit = b.parent_protection_audit()
        self.assertEqual(audit["mismatches"], [])
        self.assertEqual(audit["v091_ledger_sha256"], b.PARENT_LEDGER_SHA256)

    def test_003_v091_baseline(self):
        self.assertEqual(self.baseline["status"], "PASS")
        fact = self.baseline["baseline"]
        self.assertEqual(fact["geometric_center_gap_mm"], 60.0)
        self.assertEqual(fact["exposed_inward_stub_each_mm"], 0.5)

    def test_004_baseline_coupling_fail(self):
        self.assertEqual(
            self.baseline["baseline"]["usable_center_gap_for_coupling_mm"], 0.0
        )
        self.assertIn("FAIL", self.baseline["baseline"]["status"])

    def test_005_two_motors(self):
        self.assertEqual(self.params["fixed_architecture"]["motor_count"], 2)

    def test_006_two_pto_ports(self):
        self.assertEqual(self.params["fixed_architecture"]["pto_port_count"], 2)

    def test_007_independent_no_common_shaft(self):
        fixed = self.params["fixed_architecture"]
        self.assertIn("INDEPENDENT", fixed["pto_architecture"])
        self.assertEqual(fixed["common_pto_shaft"], "PROHIBITED")

    def test_008_no_third_motor(self):
        self.assertEqual(
            self.params["fixed_architecture"]["third_pto_motor"], "PROHIBITED"
        )

    def test_009_slide_clutch_contract(self):
        fixed = self.params["fixed_architecture"]
        self.assertEqual(fixed["slide_clutch_count"], 2)
        self.assertEqual(fixed["slide_clutch_states"], ["DRIVE", "NEUTRAL", "PTO"])

    def test_010_four_belts(self):
        self.assertEqual(self.params["fixed_architecture"]["total_belt_count"], 4)

    def test_011_nine_stub_candidates(self):
        self.assertEqual(len(self.params["candidate_ranges"]["stub_lengths_mm"]), 9)

    def test_012_seven_stack_shifts(self):
        shifts = self.params["candidate_ranges"]["stack_outward_shift_each_mm"]
        self.assertEqual(len(shifts), 7)

    def test_013_six_architectures(self):
        self.assertEqual(len(load_csv(b.ARCHITECTURE_NAME)), 6)

    def test_014_seven_shaft_ends(self):
        self.assertEqual(len(load_csv(b.SHAFT_END_NAME)), 7)

    def test_015_four_envelope_classes(self):
        self.assertEqual(
            len(self.params["candidate_ranges"]["coupling_envelopes"]), 4
        )

    def test_016_recommended_identity(self):
        self.assertEqual(
            self.rec["candidate_id"],
            "S12-C1-SMALL-STUB12.5-SHIFT00-GAP36-RES2-S1-E1",
        )

    def test_017_recommended_stub_formula(self):
        self.assertEqual(self.rec["left_shaft_end_y_mm"], 30.5 - 12.5)
        self.assertEqual(self.rec["right_shaft_end_y_mm"], -30.5 + 12.5)

    def test_018_center_gap_formula(self):
        self.assertEqual(self.rec["center_end_gap_mm"], 61.0 - 2.0 * 12.5)

    def test_019_engagement_margin_formula(self):
        margin = (
            self.rec["stub_length_mm"] - self.rec["required_engagement_mm"]
            - self.rec["axial_geometry_reserve_mm"]
        )
        self.assertEqual(margin, self.rec["engagement_margin_mm"])
        self.assertGreaterEqual(margin, 2.0)

    def test_020_body_gap_formula(self):
        self.assertEqual(
            self.rec["coupling_body_mutual_clearance_mm"], 61.0 - 2.0 * 25.0
        )

    def test_021_sweep_gap(self):
        self.assertGreaterEqual(
            self.rec["coupling_full_sweep_mutual_clearance_mm"], 8.0
        )

    def test_022_center_fixed_clearance(self):
        self.assertGreaterEqual(
            self.rec["coupling_to_central_fixed_clearance_mm"], 10.0
        )

    def test_023_wiring_clearance(self):
        self.assertGreaterEqual(self.rec["coupling_to_wiring_clearance_mm"], 10.0)

    def test_024_installation_path(self):
        self.assertGreaterEqual(
            self.rec["unit_installation_path_clearance_mm"], 5.0
        )

    def test_025_width_under_300(self):
        self.assertLess(self.rec["total_width_with_all_envelopes_mm"], 300.0)

    def test_026_width_non_regression(self):
        self.assertLessEqual(self.rec["total_width_with_all_envelopes_mm"], 290.0)

    def test_027_belt_non_regression(self):
        self.assertGreaterEqual(self.rec["belt_fixed_clearance_mm"], 11.5)

    def test_028_pto_non_regression(self):
        self.assertGreaterEqual(self.rec["pto_rotation_fixed_clearance_mm"], 10.0)

    def test_029_clutch_non_regression(self):
        self.assertGreaterEqual(self.rec["clutch_fixed_clearance_mm"], 12.0)
        self.assertGreaterEqual(self.rec["clutch_belt_clearance_mm"], 10.0)

    def test_030_vertical_non_regression(self):
        self.assertEqual(self.rec["pto_rotation_bottom_z_mm"], 260.0)
        self.assertGreaterEqual(self.rec["e2_bottom_z_mm"], 440.0)

    def test_031_center_candidates_1512(self):
        self.assertEqual(len(load_csv(b.CENTER_BAY_NAME)), 1512)

    def test_032_only_small_is_viable_at_width(self):
        rows = load_csv(b.ENVELOPE_NAME)
        viable = {
            row["coupling_envelope"] for row in rows
            if row["status"] in {"RECOMMENDED", "CONDITIONAL"}
        }
        self.assertEqual(viable, {"COUPLING_SMALL"})
        self.assertTrue(self.params["coupling_part_selection_critical"])

    def test_033_power_paths_independent(self):
        self.assertTrue(self.power["left_right_independent"])
        self.assertNotIn(
            ["LEFT_PTO_OUTPUT", "RIGHT_PTO_OUTPUT"], self.power["allowed_edges"]
        )

    def test_034_unit_present_id_separate(self):
        signals = self.states["signals"]
        self.assertNotEqual(signals["UNIT_PRESENT"], signals["UNIT_ID"])

    def test_035_engagement_feedback_separate(self):
        signals = self.states["signals"]
        self.assertIn("LEFT", signals["LEFT_COUPLING_ENGAGED"])
        self.assertIn("RIGHT", signals["RIGHT_COUPLING_ENGAGED"])

    def test_036_state_graph(self):
        self.assertEqual(len(self.states["states"]), 10)
        self.assertEqual(self.states["fault_transition"]["to"], "FAULT")

    def test_037_required_input_masks(self):
        mask = self.states["pto_enable_conditions"]["required_coupling_mask"]
        self.assertEqual(mask, "NONE_LEFT_ONLY_RIGHT_ONLY_BOTH")

    def test_038_intersections_zero(self):
        self.assertEqual(self.interference["intersection_count"], 0)
        self.assertTrue(self.interference["all_checks_pass"])

    def test_039_validation_pass(self):
        self.assertEqual(self.valid["status"], "PASS")
        self.assertEqual(self.valid["failed_count"], 0)

    def test_040_step_semantics(self):
        results = b.verify_step_semantics()
        self.assertEqual(len(results), 7)
        self.assertTrue(all(row["pass"] for row in results), results)

    def test_041_svg_contract(self):
        self.assertEqual(len(b.SVG_FILES), 7)
        for rel in b.SVG_FILES:
            text = (LANE / rel).read_text(encoding="utf-8")
            self.assertIn("<svg", text)
            self.assertIn("NOT_FOR_MANUFACTURING", text)

    def test_042_dummy_warnings(self):
        text = (LANE / b.NO_LOAD_NAME).read_text(encoding="utf-8")
        for token in (
            "NO_LOAD_GEOMETRY_DUMMY", "NOT_FOR_TORQUE",
            "NOT_FOR_POWERED_ROTATION", "NOT_FOR_MANUFACTURING",
            "HAND_FIT_ONLY",
        ):
            self.assertIn(token, text)
        self.assertTrue((LANE / b.STEP_FILES[6]).is_file())
        self.assertTrue((LANE / b.STL_FILE).is_file())

    def test_043_manifest_complete(self):
        result = b.verify_manifest()
        self.assertTrue(result["path_set_match"])
        self.assertEqual(result["manifest_path_count"], 45)

    def test_044_hashes_complete(self):
        result = b.verify_hashes()
        self.assertEqual(result["mismatches"], [])
        self.assertEqual(result["verified_path_count"], 44)

    def test_045_release_gates(self):
        gates = self.params["release_gates"]
        self.assertEqual(gates["physical_fit"], "HOLD")
        self.assertEqual(gates["shaft_cutting"], "HOLD")
        self.assertEqual(gates["powered_rotation"], "HOLD")
        self.assertEqual(gates["field_deployment"], "NOT_APPROVED")
        self.assertEqual(gates["manufacturing"], "NOT_FOR_MANUFACTURING")

    def test_046_repository_scope(self):
        audit = b.repository_audit()
        if audit["mode"] == "REPOSITORY":
            self.assertEqual(set(audit["tracked_diff"]), set(b.TRACKED_POINTER_PATHS))
            self.assertEqual(audit["staged_diff"], [])
            self.assertEqual(audit["lane_untracked_count"], 45)

    def test_047_zip_exists_and_is_exact(self):
        zips = sorted(b.DOWNLOAD_DIR.glob(b.ZIP_PREFIX + "*.zip"))
        self.assertTrue(zips)
        report = b.verify_zip(zips[-1])
        self.assertEqual(report["zip_path_count"], 45)
        self.assertEqual(report["mismatches"], [])

    def test_048_inward_directions(self):
        fixed = self.params["fixed_architecture"]
        self.assertEqual(fixed["motor_axis_direction"], {"left": "-Y", "right": "+Y"})
        self.assertEqual(fixed["pto_output_direction"], {"left": "-Y", "right": "+Y"})

    def test_049_architecture_b_and_bearing_support(self):
        fixed = self.params["fixed_architecture"]
        self.assertIn("B_SHORT_STROKE", fixed["architecture"])
        self.assertTrue(fixed["pto_60t_between_two_bearings"])

    def test_050_stack_shift_formula(self):
        rows = load_csv(b.SHIFT_NAME)
        for row in rows:
            shift = float(row["stack_outward_shift_each_mm"])
            self.assertEqual(float(row["face_span_mm"]), 61.0 + 2.0 * shift)

    def test_051_engaging_and_full_sweep_geometry(self):
        results = b.verify_step_semantics()
        engaged = next(row for row in results if row["state"] == "ENGAGED")
        sweep = next(row for row in results if row["state"] == "FULL_SWEEP")
        self.assertGreater(sweep["solid_count"], engaged["solid_count"])

    def test_052_install_and_removal_paths(self):
        rows = load_csv(b.INTERFERENCE_MATRIX_NAME)
        pairs = {(row["envelope_a"], row["envelope_b"]) for row in rows}
        self.assertIn(("WORK_UNIT_INSTALL_PATH", "ROVER_SHAFT_ENDS"), pairs)
        self.assertIn(("WORK_UNIT_REMOVAL_PATH", "ROVER_SHAFT_ENDS"), pairs)

    def test_053_authority_pointer_gate(self):
        audit = b.repository_audit()
        if audit["mode"] == "REPOSITORY":
            self.assertEqual(audit["pointer_authority"], "V092")

    def test_054_load_capacity_and_measurements_hold(self):
        self.assertEqual(self.params["release_gates"]["load_capacity"], "HOLD")
        rows = load_csv(b.MEASUREMENT_RECORD_NAME)
        self.assertGreaterEqual(len(rows), 30)
        self.assertTrue(all(row["measurement_status"] == "MEASUREMENT_REQUIRED" for row in rows))

    def test_055_inherited_bracket_clearances(self):
        rows = load_csv(b.INTERFERENCE_MATRIX_NAME)
        pairs = {(row["envelope_a"], row["envelope_b"]) for row in rows}
        self.assertIn(("LEFT_BELT_SAFETY", "LEFT_L_BRACKET_FASTENERS"), pairs)
        self.assertIn(("RIGHT_BELT_SAFETY", "RIGHT_L_BRACKET_FASTENERS"), pairs)
        self.assertIn(("LEFT_PTO_60T", "LEFT_L_BRACKET_FASTENERS"), pairs)
        self.assertIn(("RIGHT_PTO_60T", "RIGHT_L_BRACKET_FASTENERS"), pairs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
