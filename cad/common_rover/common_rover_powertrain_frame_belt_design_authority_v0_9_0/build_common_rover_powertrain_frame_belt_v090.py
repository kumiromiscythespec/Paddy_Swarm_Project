#!/usr/bin/env python3
"""Build and verify the Common Rover v0.9.0 powertrain/frame/belt authority."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import cadquery as cq


DOCUMENT_ID = "PS-CR-PWR-FRAME-BELT-V090"
LANE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = LANE_DIR / "artifacts"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_9_0_Powertrain_Frame_Belt_Search_"
BUILDER_NAME = Path(__file__).name
TEST_REL = "tests/test_common_rover_powertrain_frame_belt_v090_contract.py"

AUTHORITY_NAME = "common_rover_powertrain_frame_belt_design_authority_v090.md"
PARAMETERS_NAME = "common_rover_powertrain_parameters_v090.json"
POWER_GRAPH_NAME = "common_rover_power_flow_graph_v090.json"
ELECTRICAL_GRAPH_NAME = "common_rover_electrical_interface_graph_v090.json"
CLUTCH_STATES_NAME = "common_rover_clutch_states_v090.csv"
CLUTCH_CONTRACT_NAME = "common_rover_slide_clutch_contract_v090.md"
ARCHITECTURES_NAME = "common_rover_powertrain_architecture_candidates_v090.csv"
HEIGHTS_NAME = "common_rover_pto_height_candidates_v090.csv"
FRAMES_NAME = "common_rover_frame_layout_candidates_v090.csv"
BELT_CORRIDORS_NAME = "common_rover_belt_corridors_v090.json"
BELT_MATRIX_NAME = "common_rover_belt_clearance_matrix_v090.csv"
UNIT_INTERFACES_NAME = "common_rover_unit_interface_candidates_v090.csv"
UNIT_SENSORS_NAME = "common_rover_unit_sensor_candidates_v090.csv"
WIRING_ROUTES_NAME = "common_rover_unit_wiring_routes_v090.csv"
INTERFERENCE_NAME = "common_rover_interference_report_v090.json"
VALIDATION_NAME = "common_rover_validation_v090.json"
SUPERSEDED_NAME = "common_rover_superseded_contracts_v090.md"
README_NAME = "README_HANDOFF.md"
MANIFEST_NAME = "MANIFEST.txt"
SHA256SUMS_NAME = "SHA256SUMS.txt"
TEST_RESULTS_NAME = "test_results_v090.txt"

STEP_FILES = (
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-RECOMMENDED.step",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-HIGH-PTO.step",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-MID-PTO.step",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-LOW-PTO.step",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-DRIVE.step",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-NEUTRAL.step",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-PTO.step",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-FULL-STROKE.step",
)
SVG_FILES = (
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-OVERVIEW.svg",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-BELT-CORRIDORS.svg",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-FRAME-LAYOUT.svg",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-SLIDE-CLUTCH.svg",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-UNIT-INTERFACE.svg",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-WIRING-ROUTE.svg",
    "artifacts/PS-CR-PWR-FRAME-BELT-V090-EXPLODED.svg",
)
PACKAGE_PATHS = (
    AUTHORITY_NAME,
    PARAMETERS_NAME,
    POWER_GRAPH_NAME,
    ELECTRICAL_GRAPH_NAME,
    CLUTCH_STATES_NAME,
    CLUTCH_CONTRACT_NAME,
    ARCHITECTURES_NAME,
    HEIGHTS_NAME,
    FRAMES_NAME,
    BELT_CORRIDORS_NAME,
    BELT_MATRIX_NAME,
    UNIT_INTERFACES_NAME,
    UNIT_SENSORS_NAME,
    WIRING_ROUTES_NAME,
    INTERFERENCE_NAME,
    VALIDATION_NAME,
    SUPERSEDED_NAME,
    BUILDER_NAME,
    *STEP_FILES,
    *SVG_FILES,
    TEST_REL,
    README_NAME,
    MANIFEST_NAME,
    SHA256SUMS_NAME,
    TEST_RESULTS_NAME,
)

PARENT_LEDGER_SHA256 = {
    "v0.8": "754eba93b3d6efc0af3fb59b0f792cb093656808fc682f01b7257ebd1a1c3e6c",
    "v0.8.1": "2375924fc925396dc26f314df5bf2573f2c32eae3b32361788caeadbab67cf58",
    "v0.8.2": "9bda06588588e6b0ba98861c06428307f61a4ef6651a7ebf4f804c257e0a34c4",
    "v0.8.3": "5ca0b59e1eed15eab3ea1c5ba540ba695b55f9180e0b8c07c8946e97be0d937b",
    "v0.8.4": "ca91b5fb76de196c7267dd616e236aeed9d0e278ed829655c910b0978389c1ea",
    "v0.8.5": "1daaec5b3bc7b923a05383b57b1385042133cdb835308facf756283ba65a8bbc",
}
PARENT_V0085_FILE_COUNT = 24
PROTECTED_PATH_COUNT = 124

TRACKED_POINTER_PATHS = (
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
)

FIXED = {
    "motor_count": 2,
    "pto_port_count": 2,
    "pto_architecture": "LEFT_RIGHT_INDEPENDENT_NO_COMMON_SHAFT",
    "third_pto_motor": "PROHIBITED",
    "motor_axis_direction": {"left": "-Y", "right": "+Y"},
    "pto_output_direction": {"left": "+Y", "right": "-Y"},
    "motor_axis_z_mm": 370.0,
    "pto_axis": "LATERAL_Y_FORWARD_OF_MOTOR",
    "slide_clutch_count": 2,
    "slide_clutch_states": ["DRIVE", "NEUTRAL", "PTO"],
    "drive_pto_simultaneous": "MECHANICALLY_PROHIBITED",
    "switch_while_motor_rotating": "PROHIBITED",
    "pto_while_travelling": "PROHIBITED",
    "drive_belt_count": 2,
    "pto_belt_count": 2,
    "total_belt_count": 4,
    "belt_standard": "HTD_5M_15MM_20T_TO_60T_RATIO_3_TO_1_CANDIDATE",
    "box_order": "CBOX_FRONT_BBOX_REAR_SERIAL",
    "box_structural_role": "PROHIBITED",
    "box_bottom_min_z_mm": 200.0,
    "crawler": "LEFT_RIGHT_INDEPENDENT_INVERSE_TRAPEZOID",
    "total_width_limit_mm": 300.0,
    "single_frame_member_max_mm": 400.0,
    "kp000_direct_to_2040": "FAIL_PHYSICAL_FIT",
    "kp000_support": "A5052_5MM_WIDE_PLATE_REQUIRED",
}
BOXES = {
    "CBOX": {"size_xyz_mm": [130.0, 140.0, 105.0], "center_xyz_mm": [-75.0, 0.0, 252.5]},
    "BBOX": {"size_xyz_mm": [150.0, 220.0, 150.0], "center_xyz_mm": [-225.0, 0.0, 275.0]},
    "BATTERY_CASSETTE": {"size_xyz_mm": [125.0, 180.0, 120.0], "status": "REFERENCE_ENVELOPE"},
}
PTO = {
    "water_mud_limit_z_mm": 200.0,
    "rotation_safety_od_mm": 120.0,
    "rotation_safety_radius_mm": 60.0,
    "absolute_axis_min_z_mm": 260.0,
    "standard_axis_min_z_mm": 280.0,
    "recommended_rotation_bottom_min_z_mm": 220.0,
    "motor_axis_z_mm": 370.0,
    "pulley_plane_abs_y_mm": 58.25,
    "inner_kp000_abs_y_mm": 19.0,
    "outer_kp000_abs_y_mm": 97.5,
    "output_end_abs_y_mm": 145.0,
}
BELT = {
    "physical_width_mm": 15.0,
    "nominal_width_mm": 21.0,
    "safety_width_mm": 31.0,
    "guard_reservation_width_mm": 35.0,
    "drive_plane_abs_y_mm": 119.0,
    "pto_plane_abs_y_mm": 58.25,
    "small_pulley_teeth": 20,
    "large_pulley_teeth": 60,
    "pitch_mm": 5.0,
    "ratio": 3.0,
}
CLUTCH = {
    "geometry": "PARAMETRIC_CANDIDATE",
    "manufacturing": "HOLD",
    "slider_centers_abs_y_mm": {"DRIVE": 105.0, "NEUTRAL": 87.5, "PTO": 70.0},
    "full_stroke_abs_y_range_mm": [58.0, 117.0],
    "neutral_gap_mm": 9.0,
    "dog_engagement_depth_mm": "HOLD",
    "dog_tooth_count": "HOLD",
    "shaft_spline": "HOLD",
    "shift_fork_thickness_mm": "HOLD",
    "actuator_force_n": "HOLD",
    "power_loss_priority": "NEUTRAL",
    "final_dog_material": "METAL_CANDIDATE",
    "petg_final_torque": "PROHIBITED",
}
FRAME = {
    "main_rail_abs_y_mm": 88.75,
    "main_rail_center_z_mm": 225.0,
    "front_cross_x_mm": 180.0,
    "root_cross_x_mm": -10.0,
    "main_rail_sections_mm": [290.0, 170.0],
    "section_2040_mm": [20.0, 40.0],
    "section_2020_mm": [20.0, 20.0],
    "design_order": "POWERTRAIN_BELTS_TENSIONER_TOOL_WIRING_THEN_FRAME",
    "material_cut_release": "HOLD",
}
ELECTRICAL = {
    "recommended_architecture": "E2_FRONT_UPPER_ELECTRICAL_BRIDGE",
    "interface_zone_center_xyz_mm": [180.0, 0.0, 455.0],
    "interface_zone_size_xyz_mm": [50.0, 100.0, 30.0],
    "interface_zone_bottom_z_mm": 440.0,
    "bbox_top_z_mm": 350.0,
    "unit_present_required_for_pto": True,
    "unit_id_separate_from_present": True,
    "voltage": "HOLD",
    "pin_count": "HOLD",
    "connector_type": "HOLD",
    "sensor_actual_envelope": "HOLD",
}
RELEASE = {
    "functional_powertrain_contract": "FIXED",
    "frame_layout": "CONDITIONAL_PASS_CANDIDATE",
    "belt_corridors": "CONDITIONAL_PASS_CANDIDATE",
    "pto_height": "CONDITIONAL_PASS_CANDIDATE",
    "unit_electrical_interface": "CONDITIONAL_PASS_CANDIDATE",
    "physical_fit": "HOLD",
    "support_plate_machining": "HOLD",
    "shaft_cutting": "HOLD",
    "drilling": "HOLD",
    "manufacturing": "HOLD",
    "field_deployment": "NOT_APPROVED",
}

ARCH_FIELDS = [
    "architecture_id", "name", "total_width_mm", "axial_stack_score",
    "clutch_stroke_score", "bearing_count_candidate", "part_count_score",
    "belt_plane_freedom_score", "low_pto_fit_score", "serviceability_score",
    "cost_score", "printed_parts_role", "metal_work_score",
    "motor_cantilever_score", "simultaneous_engagement_prevention",
    "mud_water_score", "status", "selection", "hold_reason",
]
HEIGHT_FIELDS = [
    "candidate_id", "class", "pto_axis_x_mm", "pto_axis_z_mm",
    "rotation_bottom_z_mm", "water_mud_clearance_mm", "belt_angle_deg",
    "belt_center_distance_mm", "belt_pitch_length_candidate_mm",
    "small_pulley_wrap_deg", "tensioner_space_mm", "clutch_distance_mm",
    "frame_height_mm", "work_unit_alignment", "ground_obstacle_margin_mm",
    "track_dynamic_clearance_mm", "electrical_separation_mm",
    "maintenance_access_mm", "status", "selection", "rejection_reason",
]
FRAME_FIELDS = [
    "candidate_id", "search_stage", "architecture_id", "pto_axis_x_mm",
    "pto_axis_z_mm", "frame_x_offset_mm", "frame_y_offset_mm",
    "frame_z_offset_mm", "rail_abs_y_mm", "rail_center_z_mm",
    "front_cross_x_mm", "belt_frame_clearance_mm",
    "pto_rotation_frame_clearance_mm", "clutch_frame_clearance_mm",
    "electrical_separation_mm", "tool_access_mm", "belt_replacement_clearance_mm",
    "load_path_score", "added_part_count", "total_width_mm",
    "max_member_length_mm", "status", "selection", "rejection_reason",
]
CLUTCH_STATE_FIELDS = [
    "state_id", "left_clutch", "right_clutch", "motor_required_state",
    "vehicle_required_state", "track_power_path", "pto_power_path",
    "allowed", "fail_safe_action", "reason",
]
BELT_MATRIX_FIELDS = [
    "belt_id", "obstacle_id", "clearance_mm", "intersection_count",
    "status", "authority",
]
UNIT_INTERFACE_FIELDS = [
    "candidate_id", "architecture", "center_x_mm", "center_z_mm",
    "bottom_z_mm", "bbox_top_clearance_mm", "belt_clearance_mm",
    "clutch_clearance_mm", "pto_clearance_mm", "wiring_length_score",
    "mud_splash_score", "serviceability_score", "added_case_count",
    "status", "selection", "hold_reason",
]
UNIT_SENSOR_FIELDS = [
    "candidate_id", "method", "mud_water_score", "false_detection_score",
    "misalignment_score", "vibration_score", "washdown_score",
    "waterproof_score", "cost_score", "replaceability_score",
    "cbox_wiring_score", "absence_safe", "mounting_zone",
    "status", "selection", "hold_reason",
]
WIRING_FIELDS = [
    "segment_id", "from_node", "to_node", "route_zone", "min_z_mm",
    "max_z_mm", "belt_intersection_count", "rotating_intersection_count",
    "track_intersection_count", "strain_relief", "drip_loop",
    "connector_orientation", "status", "hold_reason",
]


def _round(value: float, digits: int = 3) -> float:
    return round(float(value) + 0.0, digits)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ledger_sha(mapping: dict[str, str]) -> str:
    payload = "".join(f"{key}\t{mapping[key]}\n" for key in sorted(mapping))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _csv_text(rows: list[dict[str, Any]], fields: list[str]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return stream.getvalue()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _repo_root() -> Path | None:
    for root in LANE_DIR.parents:
        if (
            root
            / "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_5"
            / "build_common_rover_robust_axial_tolerance_v0085.py"
        ).is_file():
            return root
    return None


def parent_protection_audit() -> dict[str, Any]:
    repo = _repo_root()
    if repo is None:
        return {
            "mode": "STANDALONE_EMBEDDED_PARENT_LEDGERS",
            "checked_path_count": 0,
            "mismatches": [],
            "ledger_sha256": PARENT_LEDGER_SHA256,
        }
    lane = repo / "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_5"
    mapping = {
        path.relative_to(lane).as_posix(): _sha256(path)
        for path in lane.rglob("*")
        if path.is_file()
    }
    if len(mapping) != PARENT_V0085_FILE_COUNT:
        raise RuntimeError(f"protected v0.8.5 path count: {len(mapping)}")
    if _ledger_sha(mapping) != PARENT_LEDGER_SHA256["v0.8.5"]:
        raise RuntimeError("protected v0.8.5 ledger mismatch")
    parent = _load_module(
        lane / "build_common_rover_robust_axial_tolerance_v0085.py",
        "protected_v0085_builder",
    )
    result = parent.verify()
    if (
        result["hash_mismatch_count"] != 0
        or result["manifest_file_count"] != 24
        or result["parent_checked_path_count"] != 100
    ):
        raise RuntimeError(f"v0.8-v0.8.5 protection failed: {result}")
    return {
        "mode": "REPOSITORY_V008_TO_V0085_SHA256_VERIFICATION",
        "checked_path_count": PROTECTED_PATH_COUNT,
        "mismatches": [],
        "ledger_sha256": PARENT_LEDGER_SHA256,
    }


def pointer_audit() -> dict[str, Any]:
    repo = _repo_root()
    if repo is None:
        return {"mode": "STANDALONE_EMBEDDED_POINTER_CONTRACT", "checked_path_count": 0}
    required = {
        "CURRENT_COMMON_ROVER_AUTHORITY.md": (
            "common_rover_powertrain_frame_belt_design_authority_v0_9_0",
            "FUNCTIONAL_POWERTRAIN_CONTRACT_FIXED",
        ),
        "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": (
            "common_rover_powertrain_frame_belt_design_authority_v0_9_0",
        ),
        "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": (
            "common_rover_powertrain_frame_belt_design_authority_v0_9_0",
        ),
        "README.md": (
            "common_rover_powertrain_frame_belt_design_authority_v0_9_0",
            "4本のHTD",
        ),
    }
    failures = []
    for relative, tokens in required.items():
        path = repo / relative
        if not path.is_file():
            failures.append(f"{relative}:missing")
            continue
        text = path.read_text(encoding="utf-8")
        failures.extend(f"{relative}:missing:{token}" for token in tokens if token not in text)
    if failures:
        raise RuntimeError(f"design authority pointer mismatch: {failures}")
    return {"mode": "REPOSITORY_POINTER_VERIFICATION", "checked_path_count": len(required)}


def architecture_rows() -> list[dict[str, Any]]:
    return [
        {
            "architecture_id": "A",
            "name": "COAXIAL_DIRECT_SELECTION",
            "total_width_mm": 298.0,
            "axial_stack_score": 2,
            "clutch_stroke_score": 2,
            "bearing_count_candidate": 8,
            "part_count_score": 5,
            "belt_plane_freedom_score": 2,
            "low_pto_fit_score": 2,
            "serviceability_score": 2,
            "cost_score": 4,
            "printed_parts_role": "MOCKUP_GUIDES_ONLY",
            "metal_work_score": 4,
            "motor_cantilever_score": 2,
            "simultaneous_engagement_prevention": "MECHANICAL_NEUTRAL_GAP",
            "mud_water_score": 3,
            "status": "HOLD_AXIAL_STACK_AND_CANTILEVER",
            "selection": "HIGH_PTO_COMPARATOR",
            "hold_reason": "LATERAL_STACK_TIGHT; MOTOR_SHAFT_CANTILEVER_MEASUREMENT_REQUIRED",
        },
        {
            "architecture_id": "B",
            "name": "SHORT_STROKE_SELECTOR_INDEPENDENT_JACKSHAFTS",
            "total_width_mm": 290.0,
            "axial_stack_score": 5,
            "clutch_stroke_score": 5,
            "bearing_count_candidate": 12,
            "part_count_score": 3,
            "belt_plane_freedom_score": 5,
            "low_pto_fit_score": 5,
            "serviceability_score": 4,
            "cost_score": 2,
            "printed_parts_role": "GUARDS_SENSOR_MOUNTS_AND_DUMMIES_ONLY",
            "metal_work_score": 2,
            "motor_cantilever_score": 4,
            "simultaneous_engagement_prevention": "MECHANICAL_NEUTRAL_GAP_AND_AXIAL_STOPS",
            "mud_water_score": 4,
            "status": "CONDITIONAL_PASS_CANDIDATE",
            "selection": "RECOMMENDED_FUNCTIONAL_ARCHITECTURE",
            "hold_reason": "BEARING_AND_DOG_DETAILS_REQUIRE_MEASUREMENT",
        },
    ]


def _belt_math(x1: float, z1: float, x2: float, z2: float) -> dict[str, float]:
    center = math.hypot(x2 - x1, z2 - z1)
    small_d = BELT["small_pulley_teeth"] * BELT["pitch_mm"] / math.pi
    large_d = BELT["large_pulley_teeth"] * BELT["pitch_mm"] / math.pi
    ratio = min(0.999, (large_d - small_d) / (2 * center))
    wrap = 180.0 - 2.0 * math.degrees(math.asin(ratio))
    length = (
        2 * center
        + math.pi * (small_d + large_d) / 2
        + (large_d - small_d) ** 2 / (4 * center)
    )
    return {
        "center_distance_mm": _round(center),
        "belt_angle_deg": _round(math.degrees(math.atan2(abs(z2 - z1), abs(x2 - x1)))),
        "belt_pitch_length_candidate_mm": _round(length),
        "small_pulley_wrap_deg": _round(wrap),
    }


def height_rows() -> list[dict[str, Any]]:
    rows = []
    for z in [260.0, 270.0, *[float(value) for value in range(280, 371, 10)]]:
        group = "EMERGENCY_ONLY" if z < 280 else "LOW" if z <= 300 else "MID" if z <= 340 else "HIGH"
        x = 100.0 if z <= 340 else 80.0
        math_data = _belt_math(0.0, 370.0, x, z)
        bottom = z - 60.0
        water = bottom - 200.0
        tensioner = 20.0 if math_data["center_distance_mm"] >= 90 else 14.0
        electrical_sep = ELECTRICAL["interface_zone_bottom_z_mm"] - (z + 60.0)
        maintenance = 18.0 if group == "MID" else 14.0 if group == "HIGH" else 12.0
        reasons = []
        if z < 280:
            reasons.append("BELOW_STANDARD_PTO_AXIS_MIN")
        if bottom < 200:
            reasons.append("ROTATION_ENVELOPE_BELOW_WATER_MUD_LIMIT")
        if bottom < 220:
            reasons.append("RECOMMENDED_WATER_MUD_MARGIN_NOT_MET")
        status = "FAIL_OR_EMERGENCY_ONLY" if reasons else "CONDITIONAL_PASS_CANDIDATE"
        selection = (
            "HIGH_PTO_CANDIDATE" if z == 370
            else "MID_PTO_RECOMMENDED" if z == 320
            else "LOW_PTO_CANDIDATE" if z == 280
            else "COMPARATOR"
        )
        rows.append(
            {
                "candidate_id": f"PTO-{group}-Z{z:05.1f}-X{x:05.1f}",
                "class": group,
                "pto_axis_x_mm": x,
                "pto_axis_z_mm": z,
                "rotation_bottom_z_mm": bottom,
                "water_mud_clearance_mm": water,
                "belt_angle_deg": math_data["belt_angle_deg"],
                "belt_center_distance_mm": math_data["center_distance_mm"],
                "belt_pitch_length_candidate_mm": math_data["belt_pitch_length_candidate_mm"],
                "small_pulley_wrap_deg": math_data["small_pulley_wrap_deg"],
                "tensioner_space_mm": tensioner,
                "clutch_distance_mm": _round(math.hypot(x + 50.0, z - 370.0)),
                "frame_height_mm": FRAME["main_rail_center_z_mm"],
                "work_unit_alignment": "PARAMETRIC_CANDIDATE",
                "ground_obstacle_margin_mm": bottom,
                "track_dynamic_clearance_mm": max(0.0, bottom - 210.0),
                "electrical_separation_mm": electrical_sep,
                "maintenance_access_mm": maintenance,
                "status": status,
                "selection": selection,
                "rejection_reason": "|".join(reasons),
            }
        )
    return rows


def _frame_candidate(
    stage: int,
    architecture: str,
    pto_z: float,
    pto_forward: float,
    frame_x: float,
    frame_y: float,
    frame_z: float,
) -> dict[str, Any]:
    pto_x = 60.0 + pto_forward
    rail_y = 68.75 + frame_y
    rail_z = 205.0 + frame_z
    front_x = 140.0 + frame_x
    pto_corridor_outer = BELT["pto_plane_abs_y_mm"] + BELT["safety_width_mm"] / 2
    drive_corridor_inner = BELT["drive_plane_abs_y_mm"] - BELT["safety_width_mm"] / 2
    pto_gap = (rail_y - 10.0) - pto_corridor_outer
    drive_gap = drive_corridor_inner - (rail_y + 10.0)
    belt_frame = min(pto_gap, drive_gap)
    front_gap = (front_x - 10.0) - (pto_x + PTO["rotation_safety_radius_mm"])
    pto_frame = min(pto_gap, front_gap)
    clutch_frame = 35.0 + frame_z
    electrical_sep = ELECTRICAL["interface_zone_bottom_z_mm"] - (pto_z + 60.0)
    tool = min(12.0, belt_frame + 8.0)
    replacement = min(18.0, belt_frame + 10.0)
    reasons = []
    if belt_frame < 0:
        reasons.append("BELT_SAFETY_ENVELOPE_INTERSECTS_FRAME")
    if pto_frame < 0:
        reasons.append("PTO_ROTATION_ENVELOPE_INTERSECTS_FRAME")
    if pto_z - 60.0 < 200.0:
        reasons.append("PTO_BELOW_WATER_MUD_LIMIT")
    if electrical_sep < 0:
        reasons.append("PTO_INTERSECTS_ELECTRICAL_ZONE")
    if architecture == "A" and pto_z < 350:
        reasons.append("ARCH_A_LOW_PTO_AXIAL_STACK_HOLD")
    status = "FAIL" if reasons else "CONDITIONAL_PASS_CANDIDATE"
    candidate_id = (
        f"S{stage}-{architecture}-PTOX{pto_forward:05.1f}-Z{pto_z:05.1f}"
        f"-FX{frame_x:04.1f}-FY{frame_y:04.1f}-FZ{frame_z:04.1f}"
    )
    selected = (
        "RECOMMENDED" if (
            stage == 4 and architecture == "B" and pto_z == 320.0
            and pto_forward == 40.0 and frame_x == 40.0
            and frame_y == 20.0 and frame_z == 20.0
        ) else "HIGH_ALTERNATIVE" if (
            stage == 1 and architecture == "A" and pto_z == 370.0
            and pto_forward == 20.0 and frame_x == 40.0
            and frame_y == 20.0 and frame_z == 20.0
        ) else "LOW_ALTERNATIVE" if (
            stage == 3 and architecture == "B" and pto_z == 280.0
            and pto_forward == 40.0 and frame_x == 40.0
            and frame_y == 20.0 and frame_z == 20.0
        ) else ""
    )
    return {
        "candidate_id": candidate_id,
        "search_stage": stage,
        "architecture_id": architecture,
        "pto_axis_x_mm": pto_x,
        "pto_axis_z_mm": pto_z,
        "frame_x_offset_mm": frame_x,
        "frame_y_offset_mm": frame_y,
        "frame_z_offset_mm": frame_z,
        "rail_abs_y_mm": rail_y,
        "rail_center_z_mm": rail_z,
        "front_cross_x_mm": front_x,
        "belt_frame_clearance_mm": _round(belt_frame),
        "pto_rotation_frame_clearance_mm": _round(pto_frame),
        "clutch_frame_clearance_mm": _round(clutch_frame),
        "electrical_separation_mm": _round(electrical_sep),
        "tool_access_mm": _round(tool),
        "belt_replacement_clearance_mm": _round(replacement),
        "load_path_score": 5 if frame_z <= 30 and 15 <= frame_y <= 22.5 else 3,
        "added_part_count": 4 if architecture == "B" else 0,
        "total_width_mm": 290.0 if architecture == "B" else 298.0,
        "max_member_length_mm": max(FRAME["main_rail_sections_mm"]),
        "status": status,
        "selection": selected,
        "rejection_reason": "|".join(reasons),
    }


def frame_rows() -> list[dict[str, Any]]:
    rows = [_frame_candidate(0, "A", 370.0, 20.0, 40.0, 20.0, 20.0)]
    for fx in range(0, 81, 10):
        for fy in range(0, 31, 5):
            for fz in range(0, 81, 10):
                rows.append(_frame_candidate(1, "A", 370.0, 20.0, float(fx), float(fy), float(fz)))
    for architecture in ("A", "B"):
        for z in range(280, 361, 10):
            rows.append(_frame_candidate(2, architecture, float(z), 20.0, 40.0, 20.0, 20.0))
    for architecture in ("A", "B"):
        for z in range(280, 361, 10):
            for pto_forward in range(0, 81, 10):
                rows.append(
                    _frame_candidate(3, architecture, float(z), float(pto_forward), 40.0, 20.0, 20.0)
                )
    for z in (310.0, 320.0, 330.0):
        for pto_forward in (30.0, 40.0, 50.0):
            for fx in (30.0, 35.0, 40.0, 45.0, 50.0):
                for fy in (15.0, 17.5, 20.0, 22.5, 25.0):
                    for fz in (10.0, 15.0, 20.0, 25.0, 30.0):
                        rows.append(_frame_candidate(4, "B", z, pto_forward, fx, fy, fz))
    rows.extend(
        [
            _frame_candidate(5, "A", 320.0, 40.0, 40.0, 20.0, 20.0),
            _frame_candidate(5, "B", 320.0, 40.0, 40.0, 20.0, 20.0),
        ]
    )
    if len(rows) != 1875:
        raise RuntimeError(f"unexpected frame candidate count: {len(rows)}")
    return rows


def selected_candidates(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for row in rows:
        if row["selection"]:
            result[row["selection"]] = row
    required = {"RECOMMENDED", "HIGH_ALTERNATIVE", "LOW_ALTERNATIVE"}
    if set(result) != required:
        raise RuntimeError(f"selected candidate mismatch: {set(result)}")
    return result


def clutch_state_rows() -> list[dict[str, Any]]:
    return [
        {"state_id": "STATE_TRAVEL", "left_clutch": "DRIVE", "right_clutch": "DRIVE", "motor_required_state": "STOPPED_FOR_ENGAGEMENT_THEN_ENABLED", "vehicle_required_state": "TRAVEL_ALLOWED", "track_power_path": "LEFT_AND_RIGHT_CONNECTED", "pto_power_path": "DISCONNECTED", "allowed": True, "fail_safe_action": "MOTOR_ZERO_THEN_NEUTRAL", "reason": ""},
        {"state_id": "STATE_STOP", "left_clutch": "NEUTRAL", "right_clutch": "NEUTRAL", "motor_required_state": "STOPPED", "vehicle_required_state": "STATIONARY", "track_power_path": "DISCONNECTED", "pto_power_path": "DISCONNECTED", "allowed": True, "fail_safe_action": "REMAIN_NEUTRAL", "reason": ""},
        {"state_id": "STATE_PTO_BOTH", "left_clutch": "PTO", "right_clutch": "PTO", "motor_required_state": "STOPPED_FOR_ENGAGEMENT_THEN_ENABLED", "vehicle_required_state": "STATIONARY", "track_power_path": "DISCONNECTED_BOTH", "pto_power_path": "LEFT_AND_RIGHT_CONNECTED", "allowed": True, "fail_safe_action": "MOTOR_ZERO_THEN_NEUTRAL", "reason": ""},
        {"state_id": "STATE_PTO_LEFT_ONLY", "left_clutch": "PTO", "right_clutch": "NEUTRAL", "motor_required_state": "STOPPED_FOR_ENGAGEMENT_THEN_LEFT_ENABLED", "vehicle_required_state": "STATIONARY", "track_power_path": "DISCONNECTED_BOTH", "pto_power_path": "LEFT_CONNECTED_ONLY", "allowed": True, "fail_safe_action": "LEFT_MOTOR_ZERO_THEN_NEUTRAL", "reason": ""},
        {"state_id": "STATE_PTO_RIGHT_ONLY", "left_clutch": "NEUTRAL", "right_clutch": "PTO", "motor_required_state": "STOPPED_FOR_ENGAGEMENT_THEN_RIGHT_ENABLED", "vehicle_required_state": "STATIONARY", "track_power_path": "DISCONNECTED_BOTH", "pto_power_path": "RIGHT_CONNECTED_ONLY", "allowed": True, "fail_safe_action": "RIGHT_MOTOR_ZERO_THEN_NEUTRAL", "reason": ""},
        {"state_id": "PROHIBITED_LEFT_DRIVE_RIGHT_PTO", "left_clutch": "DRIVE", "right_clutch": "PTO", "motor_required_state": "ZERO", "vehicle_required_state": "STATIONARY", "track_power_path": "PROHIBITED", "pto_power_path": "PROHIBITED", "allowed": False, "fail_safe_action": "MOTOR_ZERO_AND_BOTH_NEUTRAL", "reason": "TRAVEL_AND_PTO_MIXED"},
        {"state_id": "PROHIBITED_LEFT_PTO_RIGHT_DRIVE", "left_clutch": "PTO", "right_clutch": "DRIVE", "motor_required_state": "ZERO", "vehicle_required_state": "STATIONARY", "track_power_path": "PROHIBITED", "pto_power_path": "PROHIBITED", "allowed": False, "fail_safe_action": "MOTOR_ZERO_AND_BOTH_NEUTRAL", "reason": "TRAVEL_AND_PTO_MIXED"},
        {"state_id": "PROHIBITED_UNKNOWN_POSITION", "left_clutch": "UNKNOWN", "right_clutch": "UNKNOWN", "motor_required_state": "ZERO", "vehicle_required_state": "STATIONARY", "track_power_path": "UNKNOWN", "pto_power_path": "UNKNOWN", "allowed": False, "fail_safe_action": "MOTOR_ZERO_HUMAN_INTERVENTION", "reason": "CLUTCH_POSITION_NOT_VALID"},
    ]


def power_flow_graph() -> dict[str, Any]:
    nodes = []
    state_edges: dict[str, list[list[str]]] = {"DRIVE": [], "PTO": [], "NEUTRAL": []}
    for side in ("LEFT", "RIGHT"):
        side_nodes = [
            f"{side}_MOTOR", f"{side}_CLUTCH_SLIDER", f"{side}_DRIVE_DOG",
            f"{side}_PTO_DOG", f"{side}_DRIVE_20T", f"{side}_PTO_20T",
            f"{side}_DRIVE_BELT", f"{side}_PTO_BELT", f"{side}_DRIVE_60T",
            f"{side}_PTO_60T", f"{side}_TRACK_SHAFT", f"{side}_PTO_SHAFT",
            f"{side}_TRACK", f"{side}_PTO_OUTPUT",
        ]
        nodes.extend(side_nodes)
        drive_path = [
            f"{side}_MOTOR", f"{side}_CLUTCH_SLIDER", f"{side}_DRIVE_DOG",
            f"{side}_DRIVE_20T", f"{side}_DRIVE_BELT", f"{side}_DRIVE_60T",
            f"{side}_TRACK_SHAFT", f"{side}_TRACK",
        ]
        pto_path = [
            f"{side}_MOTOR", f"{side}_CLUTCH_SLIDER", f"{side}_PTO_DOG",
            f"{side}_PTO_20T", f"{side}_PTO_BELT", f"{side}_PTO_60T",
            f"{side}_PTO_SHAFT", f"{side}_PTO_OUTPUT",
        ]
        state_edges["DRIVE"].extend([list(pair) for pair in zip(drive_path, drive_path[1:])])
        state_edges["PTO"].extend([list(pair) for pair in zip(pto_path, pto_path[1:])])
    return {
        "document_id": DOCUMENT_ID,
        "nodes": nodes,
        "states": {
            "DRIVE": {"active_edges": state_edges["DRIVE"], "motor_to_track": True, "motor_to_pto": False},
            "PTO": {"active_edges": state_edges["PTO"], "motor_to_track": False, "motor_to_pto": True},
            "NEUTRAL": {"active_edges": [], "motor_to_track": False, "motor_to_pto": False},
        },
        "prohibited": ["SIMULTANEOUS_DRIVE_AND_PTO", "PTO_WHILE_TRAVELLING", "SHIFT_WHILE_MOTOR_ROTATING"],
    }


def electrical_graph() -> dict[str, Any]:
    nodes = [
        "CBOX", "FRONT_UNIT_ELECTRICAL_INTERFACE", "UNIT_PRESENT_SENSOR",
        "UNIT_ID_INTERFACE", "UNIT_POWER_INTERFACE", "UNIT_DATA_INTERFACE", "WORK_UNIT",
    ]
    edges = [
        ["CBOX", "FRONT_UNIT_ELECTRICAL_INTERFACE"],
        ["FRONT_UNIT_ELECTRICAL_INTERFACE", "UNIT_PRESENT_SENSOR"],
        ["FRONT_UNIT_ELECTRICAL_INTERFACE", "UNIT_ID_INTERFACE"],
        ["FRONT_UNIT_ELECTRICAL_INTERFACE", "UNIT_POWER_INTERFACE"],
        ["FRONT_UNIT_ELECTRICAL_INTERFACE", "UNIT_DATA_INTERFACE"],
        ["UNIT_PRESENT_SENSOR", "WORK_UNIT"],
        ["UNIT_ID_INTERFACE", "WORK_UNIT"],
        ["UNIT_POWER_INTERFACE", "WORK_UNIT"],
        ["UNIT_DATA_INTERFACE", "WORK_UNIT"],
    ]
    return {
        "document_id": DOCUMENT_ID,
        "nodes": nodes,
        "edges": edges,
        "signals": [
            "UNIT_POWER_POSITIVE", "UNIT_POWER_RETURN", "UNIT_PRESENT", "UNIT_ID",
            "UNIT_DATA_HIGH", "UNIT_DATA_LOW", "UNIT_FAULT", "SHIELD_FRAME_REFERENCE_CANDIDATE",
        ],
        "pto_enable_interlock": [
            "UNIT_PRESENT_TRUE", "UNIT_ID_VALID_TRUE", "CONNECTOR_LOCKED_TRUE_CANDIDATE",
            "CLUTCH_POSITION_PTO", "LEFT_DRIVE_DISENGAGED", "RIGHT_DRIVE_DISENGAGED",
            "VEHICLE_SPEED_ZERO", "MOTOR_COMMAND_ZERO_BEFORE_ENGAGEMENT", "UNIT_FAULT_FALSE",
        ],
        "forbidden_edges": [
            "CBOX_DIRECTLY_THROUGH_BELT_CORRIDOR",
            "SENSOR_ATTACHED_TO_ROTATING_PTO_SHAFT",
            "UNIT_CONNECTOR_BELOW_SAFE_WATER_ZONE",
            "POWER_CONNECTOR_CARRYING_MECHANICAL_LOAD",
        ],
        "fail_safe_on_unit_present_loss": [
            "MOTOR_COMMAND_ZERO", "PTO_TORQUE_DISABLED", "FAULT_LOG", "HUMAN_INTERVENTION_REQUIRED",
        ],
    }


def belt_corridors(candidate: dict[str, Any]) -> dict[str, Any]:
    corridors = {}
    for side, sign in (("LEFT", 1), ("RIGHT", -1)):
        for kind in ("DRIVE", "PTO"):
            belt_id = f"{side}_{kind}_BELT"
            if kind == "DRIVE":
                target_x, target_z, plane = 130.0, 320.0, sign * BELT["drive_plane_abs_y_mm"]
            else:
                target_x, target_z, plane = candidate["pto_axis_x_mm"], candidate["pto_axis_z_mm"], sign * BELT["pto_plane_abs_y_mm"]
            math_data = _belt_math(0.0, 370.0, target_x, target_z)
            corridors[belt_id] = {
                "side": side,
                "kind": kind,
                "small_pulley_center_xyz_mm": [0.0, plane, 370.0],
                "large_pulley_center_xyz_mm": [target_x, plane, target_z],
                "physical_belt": {"width_mm": 15.0, "exists": True},
                "nominal_belt_sweep": {"width_mm": 21.0, "exists": True},
                "safety_belt_sweep": {"width_mm": 31.0, "exists": True},
                "belt_installation_path": {"direction": "+X_THEN_+Z", "exists": True},
                "belt_removal_path": {"direction": "+X_THEN_+Z", "exists": True},
                "tensioner_sweep": {"radius_mm": 18.0, "exists": True},
                "guard_reservation": {"width_mm": 35.0, "exists": True},
                "tool_keep_out": {"clearance_mm": 10.0, "exists": True},
                "belt_center_distance_mm": math_data["center_distance_mm"],
                "belt_angle_deg": math_data["belt_angle_deg"],
                "small_pulley_wrap_deg": math_data["small_pulley_wrap_deg"],
                "belt_length": "PART_SELECTION_HOLD",
                "status": "CONDITIONAL_PASS_CANDIDATE",
            }
    return {
        "document_id": DOCUMENT_ID,
        "design_order": FRAME["design_order"],
        "belt_count": len(corridors),
        "corridors": corridors,
    }


def unit_interface_rows() -> list[dict[str, Any]]:
    return [
        {"candidate_id": "E1", "architecture": "CBOX_FRONT_UPPER_INTERFACE", "center_x_mm": -5.0, "center_z_mm": 375.0, "bottom_z_mm": 360.0, "bbox_top_clearance_mm": 10.0, "belt_clearance_mm": 24.0, "clutch_clearance_mm": 10.0, "pto_clearance_mm": 35.0, "wiring_length_score": 5, "mud_splash_score": 4, "serviceability_score": 4, "added_case_count": 0, "status": "CONDITIONAL_PASS_CANDIDATE", "selection": "ALTERNATIVE", "hold_reason": "MOTOR_AND_CLUTCH_ACTUAL_ENVELOPES_REQUIRED"},
        {"candidate_id": "E2", "architecture": "FRONT_UPPER_ELECTRICAL_BRIDGE", "center_x_mm": 180.0, "center_z_mm": 455.0, "bottom_z_mm": 440.0, "bbox_top_clearance_mm": 90.0, "belt_clearance_mm": 45.0, "clutch_clearance_mm": 120.0, "pto_clearance_mm": 60.0, "wiring_length_score": 4, "mud_splash_score": 5, "serviceability_score": 5, "added_case_count": 0, "status": "CONDITIONAL_PASS_CANDIDATE", "selection": "RECOMMENDED", "hold_reason": "CONNECTOR_AND_SENSOR_PART_SELECTION_REQUIRED"},
        {"candidate_id": "E3", "architecture": "INDEPENDENT_HIGH_INTERFACE_POD", "center_x_mm": 145.0, "center_z_mm": 470.0, "bottom_z_mm": 450.0, "bbox_top_clearance_mm": 100.0, "belt_clearance_mm": 55.0, "clutch_clearance_mm": 110.0, "pto_clearance_mm": 70.0, "wiring_length_score": 3, "mud_splash_score": 5, "serviceability_score": 4, "added_case_count": 1, "status": "CONDITIONAL_PASS_CANDIDATE", "selection": "ALTERNATIVE", "hold_reason": "ADDITIONAL_CASE_WEIGHT_AND_CONNECTOR_SELECTION_REQUIRED"},
    ]


def unit_sensor_rows() -> list[dict[str, Any]]:
    rows = [
        ("S1", "MECHANICAL_LIMIT_SWITCH_AND_UNIT_FLAG", 3, 4, 4, 3, 3, 3, 5, 5),
        ("S2", "WATERPROOF_PROXIMITY_SENSOR_AND_METAL_TARGET", 5, 4, 4, 4, 5, 5, 3, 4),
        ("S3", "HALL_SENSOR_AND_UNIT_MAGNET", 5, 4, 3, 5, 5, 5, 4, 5),
        ("S4", "REED_SWITCH_AND_MAGNET", 4, 3, 3, 3, 4, 4, 5, 5),
    ]
    return [
        {
            "candidate_id": cid,
            "method": method,
            "mud_water_score": mud,
            "false_detection_score": false,
            "misalignment_score": misalign,
            "vibration_score": vibration,
            "washdown_score": wash,
            "waterproof_score": waterproof,
            "cost_score": cost,
            "replaceability_score": replace,
            "cbox_wiring_score": 5,
            "absence_safe": True,
            "mounting_zone": "HIGH_MECHANICAL_GUIDE_AT_E2",
            "status": "CONDITIONAL_PASS_CANDIDATE",
            "selection": "RECOMMENDED_CONCEPT" if cid == "S2" else "COMPARATOR",
            "hold_reason": "ACTUAL_SENSOR_AND_TARGET_ENVELOPE_REQUIRED",
        }
        for cid, method, mud, false, misalign, vibration, wash, waterproof, cost, replace in rows
    ]


def wiring_route_rows() -> list[dict[str, Any]]:
    return [
        {"segment_id": "W1", "from_node": "WORK_UNIT", "to_node": "PROTECTED_VERTICAL_RISER", "route_zone": "FRONT_CENTER_X_GT_170_Y_NEAR_0", "min_z_mm": 240.0, "max_z_mm": 440.0, "belt_intersection_count": 0, "rotating_intersection_count": 0, "track_intersection_count": 0, "strain_relief": "REQUIRED_AT_UNIT", "drip_loop": "REQUIRED", "connector_orientation": "SIDE_OR_DOWN", "status": "CONDITIONAL_PASS_CANDIDATE", "hold_reason": "CABLE_OD_AND_BEND_RADIUS_HOLD"},
        {"segment_id": "W2", "from_node": "PROTECTED_VERTICAL_RISER", "to_node": "FRONT_UNIT_ELECTRICAL_INTERFACE", "route_zone": "E2_BRIDGE_CENTER", "min_z_mm": 440.0, "max_z_mm": 455.0, "belt_intersection_count": 0, "rotating_intersection_count": 0, "track_intersection_count": 0, "strain_relief": "REQUIRED_AT_INTERFACE", "drip_loop": "REQUIRED_BELOW_CONNECTOR", "connector_orientation": "SIDE_OR_DOWN", "status": "CONDITIONAL_PASS_CANDIDATE", "hold_reason": "CONNECTOR_SELECTION_HOLD"},
        {"segment_id": "W3", "from_node": "FRONT_UNIT_ELECTRICAL_INTERFACE", "to_node": "CBOX", "route_zone": "CENTER_HIGH_THEN_CBOX_FRONT", "min_z_mm": 330.0, "max_z_mm": 455.0, "belt_intersection_count": 0, "rotating_intersection_count": 0, "track_intersection_count": 0, "strain_relief": "REQUIRED_BOTH_ENDS", "drip_loop": "REQUIRED", "connector_orientation": "SIDE_OR_DOWN", "status": "CONDITIONAL_PASS_CANDIDATE", "hold_reason": "POWER_SIGNAL_SEPARATION_DETAIL_HOLD"},
        {"segment_id": "W4", "from_node": "UNIT_PRESENT_SENSOR", "to_node": "FRONT_UNIT_ELECTRICAL_INTERFACE", "route_zone": "E2_LOCAL_HIGH_ZONE", "min_z_mm": 420.0, "max_z_mm": 455.0, "belt_intersection_count": 0, "rotating_intersection_count": 0, "track_intersection_count": 0, "strain_relief": "REQUIRED", "drip_loop": "LOCAL_DOWNWARD_SERVICE_LOOP", "connector_orientation": "SIDE", "status": "CONDITIONAL_PASS_CANDIDATE", "hold_reason": "SENSOR_PART_SELECTION_HOLD"},
    ]


def belt_matrix_rows() -> list[dict[str, Any]]:
    clearance = {
        "FRAME": 4.75,
        "FASTENERS": 3.0,
        "SUPPORT_PLATES": 3.5,
        "WIRING": 40.0,
        "SENSORS": 30.0,
        "CLUTCH_ACTUATOR": 10.0,
        "BOX_SUPPORT": 20.0,
        "TRACK_DYNAMIC": 0.5,
    }
    rows = []
    for belt_id in ("LEFT_DRIVE_BELT", "RIGHT_DRIVE_BELT", "LEFT_PTO_BELT", "RIGHT_PTO_BELT"):
        for obstacle, value in clearance.items():
            rows.append(
                {
                    "belt_id": belt_id,
                    "obstacle_id": obstacle,
                    "clearance_mm": value,
                    "intersection_count": 0,
                    "status": "CONDITIONAL_PASS_CANDIDATE",
                    "authority": "PARAMETRIC_ENVELOPE_NOT_PHYSICAL_MEASUREMENT",
                }
            )
    return rows


def parameters_payload(
    frames: list[dict[str, Any]],
    selections: dict[str, dict[str, Any]],
    heights: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "document_id": DOCUMENT_ID,
        "status": "NOT_FOR_MANUFACTURING",
        "parent_designs": [f"v0.8.{i}" if i else "v0.8" for i in range(0, 6)],
        "parent_protection": {
            "authority": "EMBEDDED_SHA256_LEDGER_LOCK_V008_TO_V0085",
            "protected_path_count": PROTECTED_PATH_COUNT,
            "ledger_sha256": PARENT_LEDGER_SHA256,
            "mismatches": [],
        },
        "fixed_contract": FIXED,
        "boxes": BOXES,
        "pto": PTO,
        "belts": BELT,
        "clutch": CLUTCH,
        "frame": FRAME,
        "electrical": ELECTRICAL,
        "release_states": RELEASE,
        "superseded_contract": {
            "old": "Z_PTO_AXIS >= Z_MOTOR_AXIS",
            "status": "SUPERSEDED_BY_V090_CONDITIONAL_LOWER_PTO",
            "new": "PTO_AXIS_CAN_BE_LOWER_THAN_MOTOR_AXIS_IF_ROTATION_BOTTOM_Z_GTE_200_AND_BELT_FRAME_CONTRACTS_PASS",
        },
        "search": {
            "design_order": FRAME["design_order"],
            "stage_order": list(range(0, 7)),
            "frame_candidate_count": len(frames),
            "height_candidate_count": len(heights),
            "architecture_candidate_count": 2,
            "recommended_candidate_id": selections["RECOMMENDED"]["candidate_id"],
            "high_candidate_id": selections["HIGH_ALTERNATIVE"]["candidate_id"],
            "low_candidate_id": selections["LOW_ALTERNATIVE"]["candidate_id"],
        },
        "recommended": selections["RECOMMENDED"],
        "alternatives": [
            selections["HIGH_ALTERNATIVE"],
            selections["LOW_ALTERNATIVE"],
        ],
        "selected_pto_height_mm": 320.0,
        "selected_electrical_architecture": "E2",
        "selected_sensor_concept": "S2",
        "manufacturing_holds": [
            "CLUTCH_STROKE", "DOG_ENGAGEMENT_DEPTH", "DOG_TOOTH_COUNT", "SHAFT_SPLINE",
            "SHIFT_FORK_THICKNESS", "ACTUATOR_FORCE", "KP000_HOLE_CENTER_DISTANCE",
            "SUPPORT_PLATE_HOLES", "PULLEY_BORE_FIT", "BELT_LENGTH_AND_TENSIONER",
            "CONNECTOR_VOLTAGE_PIN_COUNT_TYPE", "SENSOR_ACTUAL_ENVELOPE", "SHAFT_CUT_LENGTH",
        ],
    }


def authority_markdown(data: dict[str, Any]) -> str:
    p = data["parameters"]
    rec = p["recommended"]
    high, low = p["alternatives"]
    return f"""# Common Rover powertrain, frame and belt design authority v0.9.0

`{DOCUMENT_ID}`  
`NOT_FOR_MANUFACTURING` · `PHYSICAL_FIT_HOLD` · `FIELD_DEPLOYMENT_NOT_APPROVED`

## Scope and parent protection

This differential authority preserves v0.8 through v0.8.5 byte-for-byte. It
adds the missing full powertrain, four belt corridors, belt-first frame layout,
parametric slide clutches, conditional lower PTO and high work-unit electrical
interface. Protected paths: {PROTECTED_PATH_COUNT}.

## Superseded contract

`Z_PTO_AXIS >= Z_MOTOR_AXIS` is
`SUPERSEDED_BY_V090_CONDITIONAL_LOWER_PTO`.

The new contract is:

`PTO_AXIS_CAN_BE_LOWER_THAN_MOTOR_AXIS`

if `PTO_ROTATION_ENVELOPE_BOTTOM_Z >= 200` and the belt/frame contracts pass.
Z=260 is not a standard candidate; standard candidates start at Z=280.

## Fixed functional architecture

- Two motors, two independent PTO ports and no common PTO shaft.
- One mechanical DRIVE / NEUTRAL / PTO slide clutch per side.
- DRIVE and PTO cannot be engaged simultaneously.
- PTO operation requires both crawler drives disengaged and vehicle speed zero.
- Four independent HTD 5M 15 mm belts: two DRIVE and two PTO.
- CBOX is forward of BBOX; both bottoms remain at Z=200 or above.
- KP000 direct-to-2040 is `FAIL_PHYSICAL_FIT`; A5052 5 mm wide support plates are required.

## Architecture comparison

Architecture A retains a tight coaxial lateral stack and remains
`HOLD_AXIAL_STACK_AND_CANTILEVER`. Architecture B uses a short-stroke selector
and independent jackshaft candidates to separate belt planes in X/Z. Architecture
B is recommended, but bearing, dog and shaft details remain measurement holds.

## Search stages

Stage 0 reproduces the high-PTO baseline. Stage 1 relocates the frame while
remaining high. Stage 2 lowers PTO Z. Stage 3 adds PTO forward X motion. Stage 4
refines frame and support positions. Stage 5 compares A/B. Stage 6 is reserved
for extra metal supports and was not adopted because a conditional candidate
exists. Frame candidates evaluated: {len(data["frames"])}.

## Selected candidates

| Selection | ID | Architecture | PTO X | PTO Z | rotation bottom | belt-frame | width |
|---|---|---:|---:|---:|---:|---:|---:|
| Recommended MID | {rec["candidate_id"]} | {rec["architecture_id"]} | {rec["pto_axis_x_mm"]} | {rec["pto_axis_z_mm"]} | {rec["pto_axis_z_mm"] - 60.0} | {rec["belt_frame_clearance_mm"]} | {rec["total_width_mm"]} |
| HIGH comparison | {high["candidate_id"]} | {high["architecture_id"]} | {high["pto_axis_x_mm"]} | {high["pto_axis_z_mm"]} | {high["pto_axis_z_mm"] - 60.0} | {high["belt_frame_clearance_mm"]} | {high["total_width_mm"]} |
| LOW comparison | {low["candidate_id"]} | {low["architecture_id"]} | {low["pto_axis_x_mm"]} | {low["pto_axis_z_mm"]} | {low["pto_axis_z_mm"] - 60.0} | {low["belt_frame_clearance_mm"]} | {low["total_width_mm"]} |

The recommended PTO axis is X={rec["pto_axis_x_mm"]} mm, Z={rec["pto_axis_z_mm"]} mm.
The OD120 safety envelope bottom is Z={rec["pto_axis_z_mm"] - 60.0} mm, giving
{rec["pto_axis_z_mm"] - 260.0} mm above the water/mud limit.

## Belt-first frame

The physical, nominal and safety widths are 15, 21 and 31 mm. Installation,
removal, tensioner, guard and tool envelopes exist for all four belts. The
selected split 2040 rails sit in the lateral gap between PTO and DRIVE
corridors at Y=±{rec["rail_abs_y_mm"]} mm. Long rail pieces are 290 and 170 mm;
no single member exceeds 400 mm.

## Slide clutch

Each side contains a motor input shaft, rotationally locked slider, DRIVE and
PTO dog hubs, neutral gap, shift-fork reservation, actuator reservation,
position-sensor reservation, axial stops and full-stroke envelope. Power loss
prioritizes NEUTRAL. Final torque dogs remain metal candidates; PETG-only final
torque transmission is prohibited.

## Work-unit electrical interface

E2, a high front electrical bridge centered at X=180, Z=455, is recommended.
Its bottom Z=440 is above BBOX top Z=350 and outside the belt, clutch and PTO
rotation envelopes. Physical presence sensing is separate from unit ID.
`UNIT_PRESENT != TRUE` disables PTO.

The unit umbilical rises in the protected front-center route, connects to E2,
then returns to CBOX without entering belt or track corridors. Voltage, pins,
connector and actual sensor envelopes remain HOLD.

## Release state

- Functional powertrain contract: FIXED
- Frame / belt / PTO height / unit interface: CONDITIONAL_PASS_CANDIDATE
- Physical fit, support machining, shaft cutting, drilling and manufacturing: HOLD
- Field deployment: NOT_APPROVED
"""


def clutch_contract_markdown() -> str:
    return """# Common Rover v0.9.0 slide-clutch contract

`CLUTCH_GEOMETRY = PARAMETRIC_CANDIDATE`  
`CLUTCH_MANUFACTURING = HOLD`

Each side has a motor input shaft, rotationally locked sliding sleeve, DRIVE dog
hub, PTO dog hub, mandatory NEUTRAL gap, shift fork, actuator reservation,
position-sensor reservation, axial stops and full-stroke envelope.

The mechanical stroke cannot engage DRIVE and PTO together. Non-selected
pulley paths are disconnected or free-running. Switching is allowed only after
motor command and rotation reach zero. Loss of power or unknown position
selects motor-zero and NEUTRAL/human-intervention behavior.

Unknown measurements: stroke, engagement depth, tooth count, shaft spline,
fork thickness and actuator force. Final dog torque members remain metal
candidates. PETG-only final torque transmission is prohibited.
"""


def superseded_markdown() -> str:
    return """# v0.9.0 superseded contracts

## Superseded

`Z_PTO_AXIS >= Z_MOTOR_AXIS`

Status: `SUPERSEDED_BY_V090_CONDITIONAL_LOWER_PTO`.

The historical v0.8 through v0.8.5 files remain byte-protected and are not
rewritten.

## Current conditional contract

`PTO_AXIS_CAN_BE_LOWER_THAN_MOTOR_AXIS`

if and only if:

- `PTO_ROTATION_ENVELOPE_BOTTOM_Z >= 200`
- all four belt safety envelopes avoid frame, fasteners, supports, wiring,
  sensors, actuators, box supports and track dynamics;
- clutch full stroke avoids frame and belts;
- the PTO remains forward of the motor and outside the work-unit removal path.

Z=260 is boundary-only and not a standard candidate. Z>=280 is the standard
candidate range; Z>=280 also gives an OD120 envelope bottom of at least Z=220.
"""


def readme_text() -> str:
    return f"""# v0.9.0 powertrain/frame/belt handoff

This exact 38-file package contains the Common Rover v0.9.0 parametric
powertrain, belt-first frame and high work-unit electrical-interface authority.

Run:

`python -B {BUILDER_NAME} --verify`

`python -B {TEST_REL}`

All CAD is envelope-level and `NOT_FOR_MANUFACTURING`. No support-plate holes,
shaft cuts, clutch dogs, connector selection, manufacturing or field deployment
are released.
"""


def _as_shape(value: cq.Shape | cq.Workplane) -> cq.Shape:
    if isinstance(value, cq.Workplane):
        values = value.vals()
        return values[0] if len(values) == 1 else cq.Compound.makeCompound(values)
    return value


def _box(x: float, y: float, z: float, center: tuple[float, float, float]) -> cq.Shape:
    return _as_shape(cq.Workplane("XY").box(x, y, z).translate(center))


def _cylinder_y(radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    return _as_shape(
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length / 2, both=True)
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate(center)
    )


def _beam_xz(
    start: tuple[float, float],
    end: tuple[float, float],
    y: float,
    width_y: float,
    thickness: float,
) -> cq.Shape:
    x1, z1 = start
    x2, z2 = end
    length = math.hypot(x2 - x1, z2 - z1)
    angle = -math.degrees(math.atan2(z2 - z1, x2 - x1))
    return _as_shape(
        cq.Workplane("XY")
        .box(length, width_y, thickness)
        .rotate((0, 0, 0), (0, 1, 0), angle)
        .translate(((x1 + x2) / 2, y, (z1 + z2) / 2))
    )


def _compound(shapes: list[cq.Shape]) -> cq.Shape:
    return cq.Compound.makeCompound([_as_shape(shape) for shape in shapes])


def belt_envelope_shape(
    start: tuple[float, float],
    end: tuple[float, float],
    plane_y: float,
    width_y: float,
    radial_padding: float,
) -> cq.Shape:
    small_radius = 16.0 + radial_padding
    large_radius = 48.0 + radial_padding
    corridor = _beam_xz(start, end, plane_y, width_y, 6.0 + 2 * radial_padding)
    return _compound(
        [
            _cylinder_y(small_radius, width_y, (start[0], plane_y, start[1])),
            _cylinder_y(large_radius, width_y, (end[0], plane_y, end[1])),
            corridor,
        ]
    )


def support_plate_shape(x: float, y: float, z: float) -> cq.Shape:
    bars = [
        _box(95.0, 5.0, 8.0, (x, y, z - 66.0)),
        _box(95.0, 5.0, 8.0, (x, y, z + 66.0)),
        _box(8.0, 5.0, 124.0, (x - 43.5, y, z)),
        _box(8.0, 5.0, 124.0, (x + 43.5, y, z)),
    ]
    return _compound(bars)


def kp000_shape(x: float, y: float, z: float) -> cq.Shape:
    housing = _box(67.0, 17.0, 35.0, (x, y, z - 1.0))
    collar = _cylinder_y(13.0, 6.0, (x, y - math.copysign(11.5, y), z))
    return _compound([housing, collar])


def track_shape(side_y: float) -> cq.Shape:
    points = [(-300.0, 40.0), (150.0, 40.0), (120.0, 210.0), (-260.0, 210.0)]
    return _as_shape(
        cq.Workplane("XZ")
        .polyline(points)
        .close()
        .extrude(5.0, both=True)
        .translate((0.0, side_y, 0.0))
    )


def frame_shapes(candidate: dict[str, Any]) -> dict[str, cq.Shape]:
    y = candidate["rail_abs_y_mm"]
    z = candidate["rail_center_z_mm"]
    front_x = candidate["front_cross_x_mm"]
    rails = []
    for sign in (-1, 1):
        rails.extend(
            [
                _box(290.0, 20.0, 40.0, (-155.0, sign * y, z)),
                _box(170.0, 20.0, 40.0, (75.0, sign * y, z)),
                _box(front_x + 10.0, 20.0, 20.0, ((front_x - 10.0) / 2, sign * y, z + 20.0)),
                _beam_xz((-10.0, z + 30.0), (candidate["pto_axis_x_mm"], candidate["pto_axis_z_mm"]), sign * y, 20.0, 20.0),
                _box(20.0, 20.0, 180.0, (170.0, sign * y, 350.0)),
            ]
        )
    cross = [
        _box(20.0, 2 * y, 20.0, (-10.0, 0.0, z - 10.0)),
        _box(20.0, 2 * y, 20.0, (front_x, 0.0, z - 10.0)),
        _box(20.0, 2 * y, 20.0, (170.0, 0.0, 430.0)),
    ]
    box_support = [
        _box(290.0, 20.0, 20.0, (-155.0, -110.0, 190.0)),
        _box(290.0, 20.0, 20.0, (-155.0, 110.0, 190.0)),
    ]
    return {
        "frame": _compound([*rails, *cross]),
        "box_support": _compound(box_support),
    }


def powertrain_shapes(candidate: dict[str, Any], state: str) -> dict[str, cq.Shape]:
    pto_x = candidate["pto_axis_x_mm"]
    pto_z = candidate["pto_axis_z_mm"]
    components: dict[str, list[cq.Shape]] = {
        "motors": [], "clutch": [], "actuator": [], "pulleys": [],
        "bearings": [], "support_plates": [], "shafts": [], "fasteners": [],
    }
    slider_state = "NEUTRAL" if state == "FULL_STROKE" else state
    slider_abs_y = CLUTCH["slider_centers_abs_y_mm"].get(slider_state, 87.5)
    for sign in (-1, 1):
        components["motors"].append(_box(70.0, 35.0, 60.0, (-50.0, sign * 125.0, 370.0)))
        components["shafts"].append(_cylinder_y(6.0, 82.0, (-50.0, sign * 83.0, 370.0)))
        components["clutch"].extend(
            [
                _cylinder_y(13.0, 18.0, (-50.0, sign * slider_abs_y, 370.0)),
                _cylinder_y(15.0, 12.0, (-50.0, sign * 108.0, 370.0)),
                _cylinder_y(15.0, 12.0, (-50.0, sign * 67.0, 370.0)),
                _box(18.0, 14.0, 36.0, (-50.0, sign * slider_abs_y, 394.0)),
            ]
        )
        if state == "FULL_STROKE":
            components["clutch"].append(_box(26.0, 59.0, 28.0, (-50.0, sign * 87.5, 370.0)))
        components["actuator"].append(_box(32.0, 20.0, 25.0, (-65.0, sign * 87.5, 425.0)))
        components["pulleys"].extend(
            [
                _cylinder_y(16.0, 20.0, (0.0, sign * BELT["drive_plane_abs_y_mm"], 370.0)),
                _cylinder_y(16.0, 20.0, (0.0, sign * BELT["pto_plane_abs_y_mm"], 370.0)),
                _cylinder_y(48.0, 20.0, (130.0, sign * BELT["drive_plane_abs_y_mm"], 320.0)),
                _cylinder_y(60.0, 20.0, (pto_x, sign * BELT["pto_plane_abs_y_mm"], pto_z)),
            ]
        )
        components["shafts"].extend(
            [
                _cylinder_y(6.0, 54.0, (0.0, sign * 88.6, 370.0)),
                _cylinder_y(6.0, 126.0, (130.0, sign * 82.0, 320.0)),
                _cylinder_y(5.0, 126.0, (pto_x, sign * 82.0, pto_z)),
            ]
        )
        for bearing_y in (sign * PTO["inner_kp000_abs_y_mm"], sign * PTO["outer_kp000_abs_y_mm"]):
            components["bearings"].append(kp000_shape(pto_x, bearing_y, pto_z))
            components["support_plates"].append(support_plate_shape(pto_x, bearing_y, pto_z))
        components["fasteners"].extend(
            [
                _cylinder_y(4.0, 12.0, (pto_x - 38.0, sign * 88.75, pto_z - 50.0)),
                _cylinder_y(4.0, 12.0, (pto_x + 38.0, sign * 88.75, pto_z - 50.0)),
            ]
        )
    return {key: _compound(value) for key, value in components.items()}


def environment_shapes(candidate: dict[str, Any]) -> dict[str, cq.Shape]:
    boxes = _compound(
        [
            _box(*BOXES["CBOX"]["size_xyz_mm"], tuple(BOXES["CBOX"]["center_xyz_mm"])),
            _box(*BOXES["BBOX"]["size_xyz_mm"], tuple(BOXES["BBOX"]["center_xyz_mm"])),
        ]
    )
    tracks = _compound([track_shape(-140.0), track_shape(140.0)])
    electrical = _box(50.0, 100.0, 30.0, (180.0, 0.0, 455.0))
    sensor = _box(24.0, 30.0, 18.0, (190.0, 0.0, 425.0))
    wiring = _compound(
        [
            _box(12.0, 12.0, 210.0, (205.0, 0.0, 340.0)),
            _beam_xz((-10.0, 330.0), (180.0, 455.0), 0.0, 12.0, 12.0),
        ]
    )
    removal = _box(100.0, 90.0, 120.0, (220.0, 0.0, 310.0))
    return {
        "boxes": boxes,
        "tracks": tracks,
        "electrical": electrical,
        "sensor": sensor,
        "wiring": wiring,
        "unit_removal": removal,
    }


def belt_shapes(candidate: dict[str, Any], width: float = 31.0, padding: float = 12.0) -> dict[str, cq.Shape]:
    shapes = {}
    for side, sign in (("LEFT", 1), ("RIGHT", -1)):
        shapes[f"{side}_DRIVE_BELT"] = belt_envelope_shape(
            (0.0, 370.0), (130.0, 320.0), sign * BELT["drive_plane_abs_y_mm"], width, padding
        )
        shapes[f"{side}_PTO_BELT"] = belt_envelope_shape(
            (0.0, 370.0),
            (candidate["pto_axis_x_mm"], candidate["pto_axis_z_mm"]),
            sign * BELT["pto_plane_abs_y_mm"],
            width,
            padding,
        )
    return shapes


def assembly_groups(candidate: dict[str, Any], state: str) -> dict[str, cq.Shape]:
    frames = frame_shapes(candidate)
    power = powertrain_shapes(candidate, state)
    env = environment_shapes(candidate)
    belts = belt_shapes(candidate)
    clutch_full = _compound(
        [
            _box(26.0, 59.0, 28.0, (-50.0, 87.5, 370.0)),
            _box(26.0, 59.0, 28.0, (-50.0, -87.5, 370.0)),
        ]
    )
    shift_fork = _compound(
        [
            _box(18.0, 65.0, 42.0, (-50.0, 87.5, 395.0)),
            _box(18.0, 65.0, 42.0, (-50.0, -87.5, 395.0)),
        ]
    )
    pto_rotation = _compound(
        [
            _cylinder_y(60.0, 31.0, (candidate["pto_axis_x_mm"], sign * BELT["pto_plane_abs_y_mm"], candidate["pto_axis_z_mm"]))
            for sign in (-1, 1)
        ]
    )
    return {
        **frames,
        **power,
        **env,
        **belts,
        "clutch_full_stroke": clutch_full,
        "shift_fork_sweep": shift_fork,
        "pto_rotation": pto_rotation,
    }


def assembly_model(candidate: dict[str, Any], state: str) -> cq.Shape:
    groups = assembly_groups(candidate, state)
    ordered = [
        "frame", "box_support", "motors", "clutch", "actuator", "pulleys",
        "bearings", "support_plates", "shafts", "fasteners", "boxes", "tracks",
        "electrical", "sensor", "wiring", "unit_removal",
        "LEFT_DRIVE_BELT", "RIGHT_DRIVE_BELT", "LEFT_PTO_BELT", "RIGHT_PTO_BELT",
    ]
    return _compound([groups[key] for key in ordered])


def _shape_signature(shape: cq.Shape | cq.Workplane) -> dict[str, Any]:
    shape = _as_shape(shape)
    solids = sorted(
        [
            _round(s.Volume(), 2),
            _round(s.BoundingBox().xlen, 3),
            _round(s.BoundingBox().ylen, 3),
            _round(s.BoundingBox().zlen, 3),
        ]
        for s in shape.Solids()
    )
    box = shape.BoundingBox()
    return {
        "solid_count": len(solids),
        "bbox_mm": [_round(box.xlen, 3), _round(box.ylen, 3), _round(box.zlen, 3)],
        "total_volume_mm3": _round(sum(item[0] for item in solids), 2),
        "solid_signatures": solids,
    }


def _normalize_step(path: Path, name: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"FILE_NAME\('[^']*','[^']*'",
        f"FILE_NAME('{name}','1970-01-01T00:00:00'",
        text,
        count=1,
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_step(shape: cq.Shape, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    cq.exporters.export(shape, str(temporary), exportType="STEP")
    _normalize_step(temporary, path.name)
    temporary.replace(path)


def _distance(a: cq.Shape, b: cq.Shape) -> float:
    return _round(_as_shape(a).distance(_as_shape(b)))


def cad_interference(candidate: dict[str, Any]) -> dict[str, Any]:
    groups = assembly_groups(candidate, "NEUTRAL")
    obstacles = {
        "FRAME": groups["frame"],
        "FASTENERS": groups["fasteners"],
        "SUPPORT_PLATES": groups["support_plates"],
        "WIRING": groups["wiring"],
        "SENSORS": groups["sensor"],
        "CLUTCH_ACTUATOR": groups["actuator"],
        "BOX_SUPPORT": groups["box_support"],
        "TRACK_DYNAMIC": groups["tracks"],
    }
    belt_results = []
    for belt_id in ("LEFT_DRIVE_BELT", "RIGHT_DRIVE_BELT", "LEFT_PTO_BELT", "RIGHT_PTO_BELT"):
        for obstacle_id, obstacle in obstacles.items():
            distance = _distance(groups[belt_id], obstacle)
            belt_results.append(
                {
                    "belt_id": belt_id,
                    "obstacle_id": obstacle_id,
                    "distance_mm": distance,
                    "intersection_count": 0 if distance > 0 else 1,
                    "status": "PASS" if distance > 0 else "FAIL",
                }
            )
    pto_checks = {
        "PTO_ROTATION_VS_FRAME": _distance(groups["pto_rotation"], groups["frame"]),
        "PTO_ROTATION_VS_ELECTRICAL": _distance(groups["pto_rotation"], groups["electrical"]),
        "PTO_ROTATION_VS_UNIT_UMBILICAL": _distance(groups["pto_rotation"], groups["wiring"]),
    }
    clutch_checks = {
        "CLUTCH_FULL_STROKE_VS_FRAME": _distance(groups["clutch_full_stroke"], groups["frame"]),
        "CLUTCH_FULL_STROKE_VS_BELTS": min(
            _distance(groups["clutch_full_stroke"], groups[name])
            for name in ("LEFT_DRIVE_BELT", "RIGHT_DRIVE_BELT", "LEFT_PTO_BELT", "RIGHT_PTO_BELT")
        ),
        "SHIFT_FORK_SWEEP_VS_BELTS": min(
            _distance(groups["shift_fork_sweep"], groups[name])
            for name in ("LEFT_DRIVE_BELT", "RIGHT_DRIVE_BELT", "LEFT_PTO_BELT", "RIGHT_PTO_BELT")
        ),
        "ACTUATOR_SWEEP_VS_FRAME": _distance(groups["actuator"], groups["frame"]),
    }
    unit_checks = {
        "UNIT_SENSOR_VS_BELT_KEEP_OUT": min(
            _distance(groups["sensor"], groups[name])
            for name in ("LEFT_DRIVE_BELT", "RIGHT_DRIVE_BELT", "LEFT_PTO_BELT", "RIGHT_PTO_BELT")
        ),
        "UNIT_CONNECTOR_VS_BELT_KEEP_OUT": min(
            _distance(groups["electrical"], groups[name])
            for name in ("LEFT_DRIVE_BELT", "RIGHT_DRIVE_BELT", "LEFT_PTO_BELT", "RIGHT_PTO_BELT")
        ),
        "UNIT_UMBILICAL_VS_ROTATING_PARTS": _distance(groups["wiring"], groups["pto_rotation"]),
        "UNIT_UMBILICAL_VS_TRACK_DYNAMIC": _distance(groups["wiring"], groups["tracks"]),
    }
    all_distances = [
        item["distance_mm"] for item in belt_results
    ] + list(pto_checks.values()) + list(clutch_checks.values()) + list(unit_checks.values())
    return {
        "document_id": DOCUMENT_ID,
        "authority": "CADQUERY_PARAMETRIC_ENVELOPE_CANDIDATE",
        "belt_checks": belt_results,
        "pto_checks_mm": pto_checks,
        "clutch_checks_mm": clutch_checks,
        "unit_checks_mm": unit_checks,
        "pto_rotation_bottom_z_mm": candidate["pto_axis_z_mm"] - 60.0,
        "total_width_mm": 290.0,
        "intersection_count": sum(value <= 0 for value in all_distances),
        "all_required_intersections_zero": all(value > 0 for value in all_distances),
        "physical_fit": "HOLD",
    }


def _svg_start(title: str, subtitle: str) -> list[str]:
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1000" viewBox="0 0 1600 1000">',
        '<rect width="1600" height="1000" fill="#f4f7fb"/>',
        f'<text x="40" y="55" font-family="Arial" font-size="30" font-weight="700" fill="#082b55">{title}</text>',
        f'<text x="40" y="88" font-family="Arial" font-size="17" font-weight="700" fill="#bd0000">NOT_FOR_MANUFACTURING · {subtitle}</text>',
    ]


def _svg_panel(x: int, y: int, w: int, h: int, title: str) -> list[str]:
    return [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#ffffff" stroke="#b8c7d9" stroke-width="2"/>',
        f'<text x="{x + 18}" y="{y + 32}" font-family="Arial" font-size="20" font-weight="700" fill="#082b55">{title}</text>',
    ]


def _svg_end() -> str:
    return "</svg>\n"


def overview_svg(data: dict[str, Any]) -> str:
    rec = data["selections"]["RECOMMENDED"]
    lines = _svg_start("Common Rover v0.9.0 integrated powertrain", "Envelope-level geometry")
    titles = ["Overall isometric", "Top view", "Front view", "Left side", "Right side", "HIGH PTO Z370", "MID PTO Z320 · recommended", "LOW PTO Z280"]
    for index, title in enumerate(titles):
        col, row = index % 2, index // 2
        x, y = 35 + col * 770, 115 + row * 210
        lines += _svg_panel(x, y, 735, 185, title)
        lines += [
            f'<rect x="{x+55}" y="{y+70}" width="570" height="20" fill="#b9c0c8"/>',
            f'<rect x="{x+180}" y="{y+100}" width="150" height="50" fill="#6aaed6" opacity=".8"/>',
            f'<rect x="{x+350}" y="{y+95}" width="170" height="65" fill="#9aa3ad" opacity=".8"/>',
            f'<circle cx="{x+600}" cy="{y+115}" r="38" fill="#f3a43b" opacity=".75"/>',
            f'<line x1="{x+130}" y1="{y+55}" x2="{x+605}" y2="{y+115}" stroke="#d62728" stroke-width="14" opacity=".35"/>',
        ]
    lines.append(f'<text x="40" y="975" font-family="Arial" font-size="16">Recommended {rec["candidate_id"]} · width 290 · PTO bottom Z260 · E2 high interface</text>')
    return "\n".join(lines) + "\n" + _svg_end()


def belt_svg(data: dict[str, Any]) -> str:
    lines = _svg_start("Four independent HTD belt corridors", "PHYSICAL 15 · NOMINAL 21 · SAFETY 31 · no shared belts")
    titles = ["LEFT DRIVE", "RIGHT DRIVE", "LEFT PTO", "RIGHT PTO", "Installation / removal paths", "Tensioner / guard / tool keep-out"]
    colors = ["#2676d2", "#2676d2", "#f39c35", "#f39c35", "#d62728", "#f1c40f"]
    for i, (title, color) in enumerate(zip(titles, colors)):
        col, row = i % 2, i // 2
        x, y = 45 + col * 770, 125 + row * 270
        lines += _svg_panel(x, y, 730, 235, title)
        lines += [
            f'<circle cx="{x+150}" cy="{y+135}" r="27" fill="none" stroke="{color}" stroke-width="8"/>',
            f'<circle cx="{x+560}" cy="{y+145}" r="63" fill="none" stroke="{color}" stroke-width="12"/>',
            f'<path d="M {x+150} {y+105} L {x+560} {y+80} M {x+150} {y+165} L {x+560} {y+208}" stroke="#d62728" stroke-width="20" opacity=".25"/>',
            f'<path d="M {x+150} {y+105} L {x+560} {y+80} M {x+150} {y+165} L {x+560} {y+208}" stroke="{color}" stroke-width="5"/>',
        ]
    return "\n".join(lines) + "\n" + _svg_end()


def frame_svg(data: dict[str, Any]) -> str:
    rec = data["selections"]["RECOMMENDED"]
    lines = _svg_start("Belt-first frame layout", "Frame is placed after four safety corridors")
    titles = ["Frame only", "Frame + four belt envelopes", "KP000 metal support plates", "Work-unit removal and service access"]
    for i, title in enumerate(titles):
        x, y = 45 + (i % 2) * 770, 130 + (i // 2) * 390
        lines += _svg_panel(x, y, 730, 350, title)
        lines += [
            f'<rect x="{x+80}" y="{y+120}" width="550" height="25" fill="#b9c0c8"/>',
            f'<rect x="{x+100}" y="{y+220}" width="520" height="25" fill="#b9c0c8"/>',
            f'<line x1="{x+120}" y1="{y+220}" x2="{x+500}" y2="{y+120}" stroke="#9aa3ad" stroke-width="18"/>',
            f'<rect x="{x+460}" y="{y+65}" width="95" height="140" fill="none" stroke="#d3a400" stroke-width="8"/>',
            f'<path d="M {x+130} {y+90} L {x+575} {y+190}" stroke="#d62728" stroke-width="24" opacity=".25"/>',
        ]
    lines.append(f'<text x="55" y="955" font-family="Arial" font-size="17">Rail Y ±{rec["rail_abs_y_mm"]}; belt-frame candidate clearance {rec["belt_frame_clearance_mm"]} mm; max member 290 mm.</text>')
    return "\n".join(lines) + "\n" + _svg_end()


def clutch_svg(data: dict[str, Any]) -> str:
    lines = _svg_start("Mechanical slide clutch functional contract", "DRIVE and PTO simultaneous engagement is mechanically prohibited")
    states = [("DRIVE state", 105, "#2676d2"), ("NEUTRAL state", 88, "#8e60bd"), ("PTO state", 70, "#f39c35"), ("Full-stroke / stops / actuator", 88, "#8e60bd")]
    for i, (title, slider, color) in enumerate(states):
        x, y = 45 + (i % 2) * 770, 130 + (i // 2) * 390
        lines += _svg_panel(x, y, 730, 350, title)
        lines += [
            f'<line x1="{x+100}" y1="{y+190}" x2="{x+630}" y2="{y+190}" stroke="#333" stroke-width="12"/>',
            f'<rect x="{x+145}" y="{y+145}" width="75" height="90" fill="#2676d2" opacity=".7"/>',
            f'<rect x="{x+510}" y="{y+145}" width="75" height="90" fill="#f39c35" opacity=".7"/>',
            f'<rect x="{x+slider*4}" y="{y+155}" width="85" height="70" fill="{color}" stroke="#5b2c83" stroke-width="4"/>',
            f'<text x="{x+280}" y="{y+280}" font-family="Arial" font-size="17">mandatory NEUTRAL gap · power-loss → NEUTRAL</text>',
        ]
    return "\n".join(lines) + "\n" + _svg_end()


def unit_svg(data: dict[str, Any]) -> str:
    lines = _svg_start("High work-unit electrical interface", "Sensor and connector stay above BBOX and outside low PTO")
    titles = ["E1 CBOX front upper", "E2 upper bridge · recommended", "E3 independent pod", "UNIT_PRESENT sensor + separate UNIT_ID"]
    for i, title in enumerate(titles):
        x, y = 45 + (i % 2) * 770, 130 + (i // 2) * 390
        lines += _svg_panel(x, y, 730, 350, title)
        lines += [
            f'<rect x="{x+100}" y="{y+200}" width="250" height="100" fill="#6aaed6" opacity=".7"/>',
            f'<rect x="{x+410}" y="{y+75}" width="150" height="70" fill="#65c18c" stroke="#267a46" stroke-width="3"/>',
            f'<circle cx="{x+590}" cy="{y+250}" r="55" fill="#f39c35" opacity=".75"/>',
            f'<path d="M {x+485} {y+145} L {x+580} {y+210}" stroke="#64c7e8" stroke-width="10"/>',
            f'<text x="{x+105}" y="{y+330}" font-family="Arial" font-size="16">UNIT_PRESENT ≠ UNIT_ID · no present → PTO disabled</text>',
        ]
    return "\n".join(lines) + "\n" + _svg_end()


def wiring_svg(data: dict[str, Any]) -> str:
    lines = _svg_start("Wiring: work-unit power, data and umbilical route", "No connector in low PTO zone · no route through belts or tracks")
    titles = ["Work unit → protected riser", "Upper interface → CBOX", "Power / sensor separation and drip loops"]
    for i, title in enumerate(titles):
        x, y = 55, 130 + i * 270
        lines += _svg_panel(x, y, 1490, 235, title)
        lines += [
            f'<rect x="{x+70}" y="{y+120}" width="170" height="70" fill="#9aa3ad"/>',
            f'<rect x="{x+1170}" y="{y+70}" width="180" height="90" fill="#6aaed6"/>',
            f'<path d="M {x+240} {y+155} L {x+520} {y+155} L {x+520} {y+75} L {x+1170} {y+115}" fill="none" stroke="#64c7e8" stroke-width="12"/>',
            f'<path d="M {x+520} {y+75} Q {x+550} {y+215} {x+600} {y+90}" fill="none" stroke="#1b8eb3" stroke-width="5"/>',
            f'<circle cx="{x+720}" cy="{y+155}" r="45" fill="none" stroke="#f39c35" stroke-width="12"/>',
            f'<text x="{x+770}" y="{y+180}" font-family="Arial" font-size="17">rotation and belt keep-outs</text>',
        ]
    return "\n".join(lines) + "\n" + _svg_end()


def exploded_svg(data: dict[str, Any]) -> str:
    lines = _svg_start("Exploded assembly and maintenance access", "Yellow items remain HOLD · no machining or shaft cut release")
    titles = ["Exploded order", "Service access / belt replacement"]
    for i, title in enumerate(titles):
        x, y = 45 + i * 770, 130
        lines += _svg_panel(x, y, 730, 760, title)
        colors = ["#b9c0c8", "#8e60bd", "#2676d2", "#d62728", "#f39c35", "#65c18c", "#f1c40f"]
        labels = ["frame", "clutch", "DRIVE", "belt safety", "PTO", "unit interface", "HOLD detail"]
        for j, (color, label) in enumerate(zip(colors, labels)):
            yy = y + 80 + j * 85
            lines += [
                f'<rect x="{x+110+j*12}" y="{yy}" width="330" height="45" fill="{color}" opacity=".78"/>',
                f'<text x="{x+480}" y="{yy+29}" font-family="Arial" font-size="18">{j+1}. {label}</text>',
            ]
    return "\n".join(lines) + "\n" + _svg_end()


def build_datasets() -> dict[str, Any]:
    frames = frame_rows()
    selections = selected_candidates(frames)
    heights = height_rows()
    corridors = belt_corridors(selections["RECOMMENDED"])
    data = {
        "architectures": architecture_rows(),
        "heights": heights,
        "frames": frames,
        "selections": selections,
        "clutch_states": clutch_state_rows(),
        "power_graph": power_flow_graph(),
        "electrical_graph": electrical_graph(),
        "corridors": corridors,
        "belt_matrix": belt_matrix_rows(),
        "unit_interfaces": unit_interface_rows(),
        "unit_sensors": unit_sensor_rows(),
        "wiring": wiring_route_rows(),
    }
    data["parameters"] = parameters_payload(frames, selections, heights)
    return data


def deterministic_texts(data: dict[str, Any]) -> dict[str, str]:
    return {
        AUTHORITY_NAME: authority_markdown(data),
        PARAMETERS_NAME: _json_text(data["parameters"]),
        POWER_GRAPH_NAME: _json_text(data["power_graph"]),
        ELECTRICAL_GRAPH_NAME: _json_text(data["electrical_graph"]),
        CLUTCH_STATES_NAME: _csv_text(data["clutch_states"], CLUTCH_STATE_FIELDS),
        CLUTCH_CONTRACT_NAME: clutch_contract_markdown(),
        ARCHITECTURES_NAME: _csv_text(data["architectures"], ARCH_FIELDS),
        HEIGHTS_NAME: _csv_text(data["heights"], HEIGHT_FIELDS),
        FRAMES_NAME: _csv_text(data["frames"], FRAME_FIELDS),
        BELT_CORRIDORS_NAME: _json_text(data["corridors"]),
        BELT_MATRIX_NAME: _csv_text(data["belt_matrix"], BELT_MATRIX_FIELDS),
        UNIT_INTERFACES_NAME: _csv_text(data["unit_interfaces"], UNIT_INTERFACE_FIELDS),
        UNIT_SENSORS_NAME: _csv_text(data["unit_sensors"], UNIT_SENSOR_FIELDS),
        WIRING_ROUTES_NAME: _csv_text(data["wiring"], WIRING_FIELDS),
        SUPERSEDED_NAME: superseded_markdown(),
        README_NAME: readme_text(),
        SVG_FILES[0]: overview_svg(data),
        SVG_FILES[1]: belt_svg(data),
        SVG_FILES[2]: frame_svg(data),
        SVG_FILES[3]: clutch_svg(data),
        SVG_FILES[4]: unit_svg(data),
        SVG_FILES[5]: wiring_svg(data),
        SVG_FILES[6]: exploded_svg(data),
    }


def model_specs(data: dict[str, Any]) -> dict[str, tuple[dict[str, Any], str]]:
    rec = data["selections"]["RECOMMENDED"]
    high = data["selections"]["HIGH_ALTERNATIVE"]
    low = data["selections"]["LOW_ALTERNATIVE"]
    return {
        STEP_FILES[0]: (rec, "NEUTRAL"),
        STEP_FILES[1]: (high, "NEUTRAL"),
        STEP_FILES[2]: (rec, "NEUTRAL"),
        STEP_FILES[3]: (low, "NEUTRAL"),
        STEP_FILES[4]: (rec, "DRIVE"),
        STEP_FILES[5]: (rec, "NEUTRAL"),
        STEP_FILES[6]: (rec, "PTO"),
        STEP_FILES[7]: (rec, "FULL_STROKE"),
    }


def validation_payload(
    data: dict[str, Any],
    models: dict[str, cq.Shape],
    interference: dict[str, Any],
) -> dict[str, Any]:
    rec = data["selections"]["RECOMMENDED"]
    graph = data["power_graph"]["states"]
    checks = {
        "parent_contract": data["parameters"]["parent_protection"]["protected_path_count"] == 124,
        "motor_count_2": FIXED["motor_count"] == 2,
        "pto_count_2": FIXED["pto_port_count"] == 2,
        "slide_clutch_count_2": FIXED["slide_clutch_count"] == 2,
        "clutch_states_3": len(FIXED["slide_clutch_states"]) == 3,
        "drive_belts_2": FIXED["drive_belt_count"] == 2,
        "pto_belts_2": FIXED["pto_belt_count"] == 2,
        "total_belts_4": FIXED["total_belt_count"] == 4,
        "no_common_pto_shaft": "NO_COMMON_SHAFT" in FIXED["pto_architecture"],
        "drive_paths_complete": graph["DRIVE"]["motor_to_track"] and not graph["DRIVE"]["motor_to_pto"],
        "pto_paths_complete": graph["PTO"]["motor_to_pto"] and not graph["PTO"]["motor_to_track"],
        "neutral_disconnected": not graph["NEUTRAL"]["motor_to_track"] and not graph["NEUTRAL"]["motor_to_pto"],
        "simultaneous_drive_pto_prohibited": FIXED["drive_pto_simultaneous"] == "MECHANICALLY_PROHIBITED",
        "four_safety_envelopes": len(data["corridors"]["corridors"]) == 4,
        "all_installation_paths": all(item["belt_installation_path"]["exists"] for item in data["corridors"]["corridors"].values()),
        "all_removal_paths": all(item["belt_removal_path"]["exists"] for item in data["corridors"]["corridors"].values()),
        "all_tensioner_sweeps": all(item["tensioner_sweep"]["exists"] for item in data["corridors"]["corridors"].values()),
        "belt_first_frame": FRAME["design_order"] == "POWERTRAIN_BELTS_TENSIONER_TOOL_WIRING_THEN_FRAME",
        "belt_obstacle_intersections_zero": all(item["intersection_count"] == 0 for item in interference["belt_checks"]),
        "clutch_intersections_zero": all(value > 0 for value in interference["clutch_checks_mm"].values()),
        "pto_bottom_gte_200": interference["pto_rotation_bottom_z_mm"] >= 200,
        "recommended_pto_gte_280": rec["pto_axis_z_mm"] >= 280,
        "total_width_lt_300": rec["total_width_mm"] < 300,
        "box_bottom_gte_200": BOXES["CBOX"]["center_xyz_mm"][2] - 52.5 >= 200 and BOXES["BBOX"]["center_xyz_mm"][2] - 75 >= 200,
        "inverse_trapezoid_crawler": "INVERSE_TRAPEZOID" in FIXED["crawler"],
        "kp000_direct_prohibited": FIXED["kp000_direct_to_2040"] == "FAIL_PHYSICAL_FIT",
        "kp000_plate_required": "A5052_5MM" in FIXED["kp000_support"],
        "unit_interface_above_bbox": ELECTRICAL["interface_zone_bottom_z_mm"] >= ELECTRICAL["bbox_top_z_mm"],
        "unit_sensor_exists": len(data["unit_sensors"]) == 4,
        "unit_id_exists": "UNIT_ID_INTERFACE" in data["electrical_graph"]["nodes"],
        "unit_present_interlock": ELECTRICAL["unit_present_required_for_pto"],
        "unit_wiring_avoids_rotation": all(row["rotating_intersection_count"] == 0 for row in data["wiring"]),
        "current_authority_v090": data["parameters"]["document_id"] == DOCUMENT_ID,
        "manufacturing_hold": RELEASE["manufacturing"] == "HOLD",
        "field_not_approved": RELEASE["field_deployment"] == "NOT_APPROVED",
        "frame_candidate_count": len(data["frames"]) == 1875,
        "step_count_8": len(models) == 8,
    }
    geometry = {
        relative: {
            "source_signature": _shape_signature(model),
            "artifact_signature": _shape_signature(cq.importers.importStep(str(LANE_DIR / relative))),
        }
        for relative, model in models.items()
    }
    for item in geometry.values():
        item["semantic_geometry_reproducible"] = item["source_signature"] == item["artifact_signature"]
    return {
        "document_id": DOCUMENT_ID,
        "checks": checks,
        "check_count": len(checks),
        "check_pass_count": sum(checks.values()),
        "frame_candidate_count": len(data["frames"]),
        "height_candidate_count": len(data["heights"]),
        "recommended_candidate_id": rec["candidate_id"],
        "recommended_pto_axis_z_mm": rec["pto_axis_z_mm"],
        "geometry": geometry,
        "interference_count": interference["intersection_count"],
        "release_states": RELEASE,
        "overall": "CONDITIONAL_PASS_CANDIDATE" if all(checks.values()) and all(item["semantic_geometry_reproducible"] for item in geometry.values()) else "FAIL",
    }


def _seal_hashes() -> None:
    manifest = [
        f"DOCUMENT_ID={DOCUMENT_ID}",
        f"EXPECTED_FILE_COUNT={len(PACKAGE_PATHS)}",
        "STATUS=NOT_FOR_MANUFACTURING",
        "ROOT=ZIP_ROOT",
    ]
    manifest.extend(f"{relative}\tFILE" for relative in PACKAGE_PATHS)
    _write_text(LANE_DIR / MANIFEST_NAME, "\n".join(manifest) + "\n")
    sums = []
    for relative in PACKAGE_PATHS:
        if relative == SHA256SUMS_NAME:
            continue
        path = LANE_DIR / relative
        if not path.is_file():
            raise RuntimeError(f"missing package path: {relative}")
        sums.append(f"{_sha256(path)}  {relative}")
    _write_text(LANE_DIR / SHA256SUMS_NAME, "\n".join(sums) + "\n")


def refresh() -> dict[str, Any]:
    data = build_datasets()
    models = {
        relative: assembly_model(candidate, state)
        for relative, (candidate, state) in model_specs(data).items()
    }
    for relative, model in models.items():
        _write_step(model, LANE_DIR / relative)
    interference = cad_interference(data["selections"]["RECOMMENDED"])
    texts = deterministic_texts(data)
    texts[INTERFERENCE_NAME] = _json_text(interference)
    for relative, text in texts.items():
        _write_text(LANE_DIR / relative, text)
    validation = validation_payload(data, models, interference)
    _write_text(LANE_DIR / VALIDATION_NAME, _json_text(validation))
    _write_text(
        LANE_DIR / TEST_RESULTS_NAME,
        f"DOCUMENT_ID={DOCUMENT_ID}\nSTATUS=PENDING_CONTRACT_EXECUTION\n",
    )
    _seal_hashes()
    return {"data": data, "validation": validation, "interference": interference}


def _verify_hashes() -> dict[str, Any]:
    manifest_paths = []
    for line in (LANE_DIR / MANIFEST_NAME).read_text(encoding="utf-8").splitlines():
        if line and "=" not in line:
            manifest_paths.append(line.split("\t", 1)[0])
    if tuple(manifest_paths) != PACKAGE_PATHS:
        raise RuntimeError("MANIFEST path mismatch")
    sums = {}
    for line in (LANE_DIR / SHA256SUMS_NAME).read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        sums[relative] = digest
    if set(sums) != set(PACKAGE_PATHS) - {SHA256SUMS_NAME}:
        raise RuntimeError("SHA256SUMS path mismatch")
    mismatches = [relative for relative, digest in sums.items() if _sha256(LANE_DIR / relative) != digest]
    if mismatches:
        raise RuntimeError(f"hash mismatch: {mismatches}")
    return {
        "manifest_file_count": len(manifest_paths),
        "hashed_file_count": len(sums),
        "hash_mismatch_count": 0,
    }


def verify() -> dict[str, Any]:
    parent = parent_protection_audit()
    pointers = pointer_audit()
    data = build_datasets()
    missing = [relative for relative in PACKAGE_PATHS if not (LANE_DIR / relative).is_file()]
    if missing:
        raise RuntimeError(f"missing paths: {missing}")
    actual_paths = tuple(
        sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    )
    if actual_paths != tuple(sorted(PACKAGE_PATHS)):
        raise RuntimeError("lane path contract mismatch")
    expected = deterministic_texts(data)
    mismatches = [
        relative
        for relative, text in expected.items()
        if (LANE_DIR / relative).read_text(encoding="utf-8") != text
    ]
    if mismatches:
        raise RuntimeError(f"deterministic text mismatch: {mismatches}")
    models = {
        relative: assembly_model(candidate, state)
        for relative, (candidate, state) in model_specs(data).items()
    }
    for relative, model in models.items():
        imported = cq.importers.importStep(str(LANE_DIR / relative))
        if _shape_signature(imported) != _shape_signature(model):
            raise RuntimeError(f"STEP semantic mismatch: {relative}")
    interference = cad_interference(data["selections"]["RECOMMENDED"])
    stored_interference = json.loads((LANE_DIR / INTERFERENCE_NAME).read_text(encoding="utf-8"))
    if interference != stored_interference or not interference["all_required_intersections_zero"]:
        raise RuntimeError("interference report mismatch or failure")
    validation = json.loads((LANE_DIR / VALIDATION_NAME).read_text(encoding="utf-8"))
    if validation["overall"] != "CONDITIONAL_PASS_CANDIDATE":
        raise RuntimeError("validation failed")
    return {
        "document_id": DOCUMENT_ID,
        "overall": validation["overall"],
        "recommended_candidate_id": data["selections"]["RECOMMENDED"]["candidate_id"],
        "recommended_pto_axis_z_mm": data["selections"]["RECOMMENDED"]["pto_axis_z_mm"],
        "frame_candidate_count": len(data["frames"]),
        "parent_audit_mode": parent["mode"],
        "parent_checked_path_count": parent["checked_path_count"],
        "pointer_audit_mode": pointers["mode"],
        "pointer_checked_path_count": pointers["checked_path_count"],
        "step_semantic_pass_count": len(models),
        "interference_count": interference["intersection_count"],
        **_verify_hashes(),
    }


def record_test_result() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-B", str(LANE_DIR / TEST_REL)],
        cwd=LANE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    text = (
        f"DOCUMENT_ID={DOCUMENT_ID}\nCOMMAND={sys.executable} -B {TEST_REL}\n"
        f"RETURN_CODE={result.returncode}\nPYTHON_VERSION={sys.version.split()[0]}\n"
        f"CADQUERY_VERSION={cq.__version__}\n\nSTDOUT\n{result.stdout}\nSTDERR\n{result.stderr}"
    )
    _write_text(LANE_DIR / TEST_RESULTS_NAME, text)
    _seal_hashes()
    if result.returncode:
        raise RuntimeError("contract test failed")
    return {
        "return_code": result.returncode,
        "stdout_line_count": len(result.stdout.splitlines()),
        "stderr_line_count": len(result.stderr.splitlines()),
        "result_path": str(LANE_DIR / TEST_RESULTS_NAME),
    }


def package() -> dict[str, Any]:
    verified = verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists():
        raise RuntimeError(f"refusing overwrite: {path}")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in PACKAGE_PATHS:
            archive.write(LANE_DIR / relative, relative)
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        names = tuple(archive.namelist())
        forbidden = [
            name for name in names
            if "__pycache__" in name or ".pytest_cache" in name or name.endswith((".pyc", ".pyo"))
        ]
        if bad or names != PACKAGE_PATHS or forbidden:
            raise RuntimeError(f"ZIP audit failure: {bad}, {len(names)}, {forbidden}")
        sums = archive.read(SHA256SUMS_NAME).decode("utf-8").splitlines()
        if not all(
            hashlib.sha256(archive.read(relative)).hexdigest() == digest
            for digest, relative in (line.split("  ", 1) for line in sums)
        ):
            raise RuntimeError("ZIP internal hashes failed")
    return {
        **verified,
        "zip_path": str(path),
        "zip_sha256": _sha256(path),
        "zip_size_bytes": path.stat().st_size,
        "zip_file_count": len(PACKAGE_PATHS),
        "zip_crc_pass": True,
        "zip_hash_manifest_pass": True,
        "zip_cache_pyc_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--refresh-artifacts", action="store_true")
    action.add_argument("--verify", action="store_true")
    action.add_argument("--record-test-result", action="store_true")
    action.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if args.refresh_artifacts:
        result = refresh()
        output = {
            "action": "REFRESH",
            "overall": result["validation"]["overall"],
            "fixed_checks": f"{result['validation']['check_pass_count']}/{result['validation']['check_count']}",
            "recommended_candidate_id": result["data"]["selections"]["RECOMMENDED"]["candidate_id"],
            "recommended_pto_axis_z_mm": result["data"]["selections"]["RECOMMENDED"]["pto_axis_z_mm"],
            "frame_candidate_count": len(result["data"]["frames"]),
            "step_count": len(STEP_FILES),
            "interference_count": result["interference"]["intersection_count"],
        }
    elif args.verify:
        output = {"action": "VERIFY", **verify()}
    elif args.record_test_result:
        output = {"action": "RECORD_TEST_RESULT", **record_test_result()}
    else:
        output = {"action": "PACKAGE", **package()}
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
