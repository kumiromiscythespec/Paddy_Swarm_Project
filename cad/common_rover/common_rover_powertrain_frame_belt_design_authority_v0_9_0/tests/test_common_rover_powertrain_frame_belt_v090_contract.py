#!/usr/bin/env python3
"""Contract tests for the Common Rover v0.9.0 integrated authority."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path

import cadquery as cq


LANE_DIR = Path(__file__).resolve().parents[1]
BUILDER_PATH = LANE_DIR / "build_common_rover_powertrain_frame_belt_v090.py"
SPEC = importlib.util.spec_from_file_location("v090_builder", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load v0.9.0 builder")
B = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)


def read_json(name: str):
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def read_csv(name: str):
    with (LANE_DIR / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def reachable(edges: list[list[str]], start: str, goal: str) -> bool:
    adjacency: dict[str, set[str]] = {}
    for source, target in edges:
        adjacency.setdefault(source, set()).add(target)
    pending = [start]
    seen = set()
    while pending:
        node = pending.pop()
        if node == goal:
            return True
        if node in seen:
            continue
        seen.add(node)
        pending.extend(adjacency.get(node, ()))
    return False


class CommonRoverV090Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = B.build_datasets()
        cls.params = read_json(B.PARAMETERS_NAME)
        cls.validation = read_json(B.VALIDATION_NAME)
        cls.interference = read_json(B.INTERFERENCE_NAME)
        cls.frames = read_csv(B.FRAMES_NAME)
        cls.heights = read_csv(B.HEIGHTS_NAME)
        cls.belt_matrix = read_csv(B.BELT_MATRIX_NAME)

    def test_001_exact_thirty_eight_paths(self):
        actual = tuple(
            sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
        )
        self.assertEqual(actual, tuple(sorted(B.PACKAGE_PATHS)))
        self.assertEqual(len(actual), 38)

    def test_002_parent_v008_to_v0085_protection(self):
        audit = B.parent_protection_audit()
        self.assertEqual(audit["mismatches"], [])
        self.assertIn(audit["checked_path_count"], (0, 124))
        self.assertEqual(set(audit["ledger_sha256"]), {"v0.8", "v0.8.1", "v0.8.2", "v0.8.3", "v0.8.4", "v0.8.5"})

    def test_003_v0085_baseline_and_handoff_preserved(self):
        self.assertEqual(B.PARENT_LEDGER_SHA256["v0.8.5"], "1daaec5b3bc7b923a05383b57b1385042133cdb835308facf756283ba65a8bbc")
        self.assertEqual(B.PARENT_V0085_FILE_COUNT, 24)
        self.assertEqual(B.PROTECTED_PATH_COUNT, 124)

    def test_004_design_authority_pointers_and_git_scope(self):
        audit = B.pointer_audit()
        self.assertIn(audit["checked_path_count"], (0, 4))
        repo = B._repo_root()
        if repo is not None:
            tracked = set(
                subprocess.check_output(
                    ["git", "-C", str(repo), "diff", "--name-only"],
                    text=True,
                ).splitlines()
            )
            staged = subprocess.check_output(
                ["git", "-C", str(repo), "diff", "--cached", "--name-only"],
                text=True,
            ).splitlines()
            self.assertEqual(tracked, set(B.TRACKED_POINTER_PATHS))
            self.assertEqual(staged, [])

    def test_005_fixed_counts(self):
        fixed = self.params["fixed_contract"]
        self.assertEqual(fixed["motor_count"], 2)
        self.assertEqual(fixed["pto_port_count"], 2)
        self.assertEqual(fixed["slide_clutch_count"], 2)
        self.assertEqual(fixed["drive_belt_count"], 2)
        self.assertEqual(fixed["pto_belt_count"], 2)
        self.assertEqual(fixed["total_belt_count"], 4)

    def test_006_no_common_pto_shaft_and_no_third_motor(self):
        fixed = self.params["fixed_contract"]
        self.assertIn("NO_COMMON_SHAFT", fixed["pto_architecture"])
        self.assertEqual(fixed["third_pto_motor"], "PROHIBITED")

    def test_007_slide_clutch_minimum_components(self):
        text = (LANE_DIR / B.CLUTCH_CONTRACT_NAME).read_text(encoding="utf-8")
        for token in (
            "motor input shaft", "rotationally locked sliding sleeve", "DRIVE dog",
            "PTO dog", "NEUTRAL gap", "shift fork", "actuator reservation",
            "position-sensor reservation", "axial stops", "full-stroke envelope",
        ):
            self.assertIn(token, text)

    def test_008_clutch_states_and_allowed_operating_states(self):
        rows = read_csv(B.CLUTCH_STATES_NAME)
        self.assertEqual(self.params["fixed_contract"]["slide_clutch_states"], ["DRIVE", "NEUTRAL", "PTO"])
        allowed = {row["state_id"] for row in rows if row["allowed"] == "True"}
        self.assertEqual(
            allowed,
            {"STATE_TRAVEL", "STATE_STOP", "STATE_PTO_BOTH", "STATE_PTO_LEFT_ONLY", "STATE_PTO_RIGHT_ONLY"},
        )

    def test_009_prohibited_mixed_and_unknown_states(self):
        rows = read_csv(B.CLUTCH_STATES_NAME)
        prohibited = [row for row in rows if row["allowed"] == "False"]
        self.assertEqual(len(prohibited), 3)
        self.assertTrue(all("MOTOR_ZERO" in row["fail_safe_action"] for row in prohibited))

    def test_010_drive_power_graph_left_and_right(self):
        graph = read_json(B.POWER_GRAPH_NAME)
        edges = graph["states"]["DRIVE"]["active_edges"]
        for side in ("LEFT", "RIGHT"):
            self.assertTrue(reachable(edges, f"{side}_MOTOR", f"{side}_TRACK"))
            self.assertFalse(reachable(edges, f"{side}_MOTOR", f"{side}_PTO_OUTPUT"))

    def test_011_pto_power_graph_left_and_right(self):
        graph = read_json(B.POWER_GRAPH_NAME)
        edges = graph["states"]["PTO"]["active_edges"]
        for side in ("LEFT", "RIGHT"):
            self.assertTrue(reachable(edges, f"{side}_MOTOR", f"{side}_PTO_OUTPUT"))
            self.assertFalse(reachable(edges, f"{side}_MOTOR", f"{side}_TRACK"))

    def test_012_neutral_power_graph_disconnected(self):
        graph = read_json(B.POWER_GRAPH_NAME)
        self.assertEqual(graph["states"]["NEUTRAL"]["active_edges"], [])
        self.assertFalse(graph["states"]["NEUTRAL"]["motor_to_track"])
        self.assertFalse(graph["states"]["NEUTRAL"]["motor_to_pto"])

    def test_013_four_independent_belt_corridors(self):
        corridors = read_json(B.BELT_CORRIDORS_NAME)["corridors"]
        self.assertEqual(
            set(corridors),
            {"LEFT_DRIVE_BELT", "RIGHT_DRIVE_BELT", "LEFT_PTO_BELT", "RIGHT_PTO_BELT"},
        )
        self.assertEqual(len(corridors), 4)

    def test_014_physical_nominal_safety_and_guard_envelopes(self):
        corridors = read_json(B.BELT_CORRIDORS_NAME)["corridors"].values()
        for item in corridors:
            self.assertEqual(item["physical_belt"]["width_mm"], 15.0)
            self.assertEqual(item["nominal_belt_sweep"]["width_mm"], 21.0)
            self.assertEqual(item["safety_belt_sweep"]["width_mm"], 31.0)
            self.assertTrue(item["guard_reservation"]["exists"])
            self.assertTrue(item["tool_keep_out"]["exists"])

    def test_015_install_remove_tensioner_contracts(self):
        corridors = read_json(B.BELT_CORRIDORS_NAME)["corridors"].values()
        for item in corridors:
            self.assertTrue(item["belt_installation_path"]["exists"])
            self.assertTrue(item["belt_removal_path"]["exists"])
            self.assertTrue(item["tensioner_sweep"]["exists"])

    def test_016_belt_first_frame_order(self):
        self.assertEqual(
            self.params["frame"]["design_order"],
            "POWERTRAIN_BELTS_TENSIONER_TOOL_WIRING_THEN_FRAME",
        )

    def test_017_search_stages_and_candidate_count(self):
        self.assertEqual(len(self.frames), 1875)
        self.assertEqual({int(row["search_stage"]) for row in self.frames}, {0, 1, 2, 3, 4, 5})
        self.assertEqual(self.params["search"]["stage_order"], [0, 1, 2, 3, 4, 5, 6])

    def test_018_architecture_a_b_comparison(self):
        rows = read_csv(B.ARCHITECTURES_NAME)
        self.assertEqual({row["architecture_id"] for row in rows}, {"A", "B"})
        recommended = next(row for row in rows if row["selection"] == "RECOMMENDED_FUNCTIONAL_ARCHITECTURE")
        self.assertEqual(recommended["architecture_id"], "B")

    def test_019_high_mid_low_height_candidates(self):
        selection = {row["selection"]: row for row in self.heights}
        self.assertEqual(float(selection["HIGH_PTO_CANDIDATE"]["pto_axis_z_mm"]), 370.0)
        self.assertEqual(float(selection["MID_PTO_RECOMMENDED"]["pto_axis_z_mm"]), 320.0)
        self.assertEqual(float(selection["LOW_PTO_CANDIDATE"]["pto_axis_z_mm"]), 280.0)
        emergency = [row for row in self.heights if row["class"] == "EMERGENCY_ONLY"]
        self.assertEqual(len(emergency), 2)
        self.assertTrue(all(row["status"] == "FAIL_OR_EMERGENCY_ONLY" for row in emergency))

    def test_020_recommended_candidate_and_architecture(self):
        rec = self.params["recommended"]
        self.assertEqual(rec["architecture_id"], "B")
        self.assertEqual(rec["pto_axis_x_mm"], 100.0)
        self.assertEqual(rec["pto_axis_z_mm"], 320.0)
        self.assertEqual(rec["status"], "CONDITIONAL_PASS_CANDIDATE")

    def test_021_pto_water_mud_and_standard_height(self):
        rec = self.params["recommended"]
        self.assertGreaterEqual(rec["pto_axis_z_mm"], 280)
        self.assertGreaterEqual(rec["pto_axis_z_mm"] - 60.0, 220)
        self.assertGreaterEqual(self.interference["pto_rotation_bottom_z_mm"], 200)

    def test_022_total_width_under_300(self):
        self.assertLess(self.params["recommended"]["total_width_mm"], 300)
        self.assertEqual(self.interference["total_width_mm"], 290.0)

    def test_023_frame_member_limit_and_split_rails(self):
        self.assertLessEqual(max(self.params["frame"]["main_rail_sections_mm"]), 400)
        self.assertEqual(self.params["recommended"]["max_member_length_mm"], 290.0)

    def test_024_belt_obstacle_intersections_zero(self):
        self.assertEqual(len(self.interference["belt_checks"]), 32)
        self.assertTrue(all(row["intersection_count"] == 0 for row in self.interference["belt_checks"]))
        self.assertTrue(all(row["intersection_count"] == "0" for row in self.belt_matrix))

    def test_025_clutch_full_stroke_and_sweeps_clear(self):
        self.assertTrue(all(value > 0 for value in self.interference["clutch_checks_mm"].values()))

    def test_026_pto_rotation_electrical_and_umbilical_clear(self):
        self.assertTrue(all(value > 0 for value in self.interference["pto_checks_mm"].values()))
        self.assertTrue(all(value > 0 for value in self.interference["unit_checks_mm"].values()))

    def test_027_kp000_support_contract(self):
        fixed = self.params["fixed_contract"]
        self.assertEqual(fixed["kp000_direct_to_2040"], "FAIL_PHYSICAL_FIT")
        self.assertIn("A5052_5MM", fixed["kp000_support"])
        self.assertEqual(self.params["release_states"]["support_plate_machining"], "HOLD")
        self.assertIn("KP000_HOLE_CENTER_DISTANCE", self.params["manufacturing_holds"])

    def test_028_boxes_bottom_and_serial_order(self):
        self.assertEqual(self.params["fixed_contract"]["box_order"], "CBOX_FRONT_BBOX_REAR_SERIAL")
        for box in ("CBOX", "BBOX"):
            center_z = self.params["boxes"][box]["center_xyz_mm"][2]
            height = self.params["boxes"][box]["size_xyz_mm"][2]
            self.assertGreaterEqual(center_z - height / 2, 200)

    def test_029_inverse_trapezoid_crawler_retained(self):
        self.assertIn("INVERSE_TRAPEZOID", self.params["fixed_contract"]["crawler"])

    def test_030_high_electrical_interface(self):
        interfaces = read_csv(B.UNIT_INTERFACES_NAME)
        selected = next(row for row in interfaces if row["selection"] == "RECOMMENDED")
        self.assertEqual(selected["candidate_id"], "E2")
        self.assertGreaterEqual(float(selected["bottom_z_mm"]), 350)
        self.assertGreaterEqual(float(selected["bottom_z_mm"]), self.params["electrical"]["bbox_top_z_mm"])

    def test_031_presence_sensor_and_id_are_separate(self):
        graph = read_json(B.ELECTRICAL_GRAPH_NAME)
        self.assertIn("UNIT_PRESENT_SENSOR", graph["nodes"])
        self.assertIn("UNIT_ID_INTERFACE", graph["nodes"])
        self.assertNotEqual("UNIT_PRESENT_SENSOR", "UNIT_ID_INTERFACE")
        self.assertEqual(len(read_csv(B.UNIT_SENSORS_NAME)), 4)

    def test_032_pto_enable_requires_presence_and_safe_state(self):
        graph = read_json(B.ELECTRICAL_GRAPH_NAME)
        interlocks = set(graph["pto_enable_interlock"])
        self.assertIn("UNIT_PRESENT_TRUE", interlocks)
        self.assertIn("UNIT_ID_VALID_TRUE", interlocks)
        self.assertIn("VEHICLE_SPEED_ZERO", interlocks)
        self.assertIn("MOTOR_COMMAND_ZERO_BEFORE_ENGAGEMENT", interlocks)

    def test_033_wiring_avoids_belts_rotation_and_tracks(self):
        rows = read_csv(B.WIRING_ROUTES_NAME)
        self.assertGreaterEqual(len(rows), 4)
        for row in rows:
            self.assertEqual(row["belt_intersection_count"], "0")
            self.assertEqual(row["rotating_intersection_count"], "0")
            self.assertEqual(row["track_intersection_count"], "0")
            self.assertIn(row["connector_orientation"], ("SIDE", "SIDE_OR_DOWN"))

    def test_034_release_states(self):
        release = self.params["release_states"]
        self.assertEqual(release["functional_powertrain_contract"], "FIXED")
        self.assertEqual(release["physical_fit"], "HOLD")
        self.assertEqual(release["manufacturing"], "HOLD")
        self.assertEqual(release["field_deployment"], "NOT_APPROVED")

    def test_035_superseded_contract_recorded(self):
        text = (LANE_DIR / B.SUPERSEDED_NAME).read_text(encoding="utf-8")
        self.assertIn("Z_PTO_AXIS >= Z_MOTOR_AXIS", text)
        self.assertIn("SUPERSEDED_BY_V090_CONDITIONAL_LOWER_PTO", text)
        self.assertIn("PTO_AXIS_CAN_BE_LOWER_THAN_MOTOR_AXIS", text)

    def test_036_step_semantic_geometry_eight_of_eight(self):
        specs = B.model_specs(self.data)
        self.assertEqual(len(specs), 8)
        for relative, (candidate, state) in specs.items():
            source = B.assembly_model(candidate, state)
            artifact = cq.importers.importStep(str(LANE_DIR / relative))
            self.assertEqual(B._shape_signature(source), B._shape_signature(artifact), relative)

    def test_037_svg_contract_and_warning(self):
        self.assertEqual(len(B.SVG_FILES), 7)
        combined = ""
        for relative in B.SVG_FILES:
            text = (LANE_DIR / relative).read_text(encoding="utf-8")
            self.assertTrue(text.startswith("<svg"))
            self.assertIn("NOT_FOR_MANUFACTURING", text)
            combined += text
        for token in ("DRIVE", "PTO", "NEUTRAL", "belt", "Frame", "UNIT_PRESENT", "Wiring", "Exploded"):
            self.assertIn(token, combined)

    def test_038_manifest_hash_and_cache_contract(self):
        result = B._verify_hashes()
        self.assertEqual(result["manifest_file_count"], 38)
        self.assertEqual(result["hashed_file_count"], 37)
        forbidden = [
            path for path in LANE_DIR.rglob("*")
            if path.name in {"__pycache__", ".pytest_cache"} or path.suffix in {".pyc", ".pyo"}
        ]
        self.assertEqual(forbidden, [])

    def test_039_validation_all_fixed_checks_pass(self):
        self.assertEqual(self.validation["overall"], "CONDITIONAL_PASS_CANDIDATE")
        self.assertEqual(self.validation["check_count"], self.validation["check_pass_count"])
        self.assertEqual(self.validation["interference_count"], 0)
        self.assertTrue(all(item["semantic_geometry_reproducible"] for item in self.validation["geometry"].values()))

    def test_040_download_zip_delivery_lifecycle(self):
        zips = sorted(
            Path(r"D:\Downloads").glob("Paddy_Swarm_Common_Rover_v0_9_0_Powertrain_Frame_Belt_Search_*.zip")
        )
        if not zips:
            self.assertEqual(len(B.PACKAGE_PATHS), 38)
            return
        latest = zips[-1]
        with zipfile.ZipFile(latest) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(tuple(archive.namelist()), B.PACKAGE_PATHS)
            sums = archive.read(B.SHA256SUMS_NAME).decode("utf-8").splitlines()
            for line in sums:
                digest, relative = line.split("  ", 1)
                self.assertEqual(hashlib.sha256(archive.read(relative)).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
