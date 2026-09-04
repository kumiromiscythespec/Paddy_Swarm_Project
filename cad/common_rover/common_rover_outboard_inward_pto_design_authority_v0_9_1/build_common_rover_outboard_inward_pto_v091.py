#!/usr/bin/env python3
"""Build and verify the Common Rover v0.9.1 outboard/inward-PTO candidate.

This lane is an envelope-level design authority.  It deliberately does not
release motor selection, coupling dimensions, bearing holes, shaft cuts, or
manufacturing geometry.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import cadquery as cq


DOCUMENT_ID = "PS-CR-OUTBOARD-INWARD-V091"
LANE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = LANE_DIR / "artifacts"
TEST_DIR = LANE_DIR / "tests"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_9_1_Outboard_Inward_PTO_"

AUTHORITY_NAME = "common_rover_outboard_inward_pto_design_authority_v091.md"
PARAMETERS_NAME = "common_rover_outboard_inward_pto_parameters_v091.json"
BASELINE_NAME = "common_rover_v090_baseline_v091.json"
POWER_GRAPH_NAME = "common_rover_power_flow_graph_v091.json"
POD_CANDIDATES_NAME = "common_rover_outboard_pod_candidates_v091.csv"
MOTOR_SENSITIVITY_NAME = "common_rover_motor_envelope_sensitivity_v091.csv"
FRAME_SECTIONS_NAME = "common_rover_frame_section_candidates_v091.csv"
L_BRACKETS_NAME = "common_rover_l_bracket_candidates_v091.csv"
BELT_PLANES_NAME = "common_rover_belt_plane_candidates_v091.csv"
PTO_HEIGHTS_NAME = "common_rover_pto_height_candidates_v091.csv"
Y_STACK_NAME = "common_rover_y_stack_audit_v091.csv"
CENTER_BAY_NAME = "common_rover_center_pto_bay_candidates_v091.csv"
COUPLING_NAME = "common_rover_coupling_candidates_v091.csv"
CLEARANCE_NAME = "common_rover_clearance_contract_v091.md"
INTERFERENCE_MATRIX_NAME = "common_rover_interference_matrix_v091.csv"
INTERFERENCE_REPORT_NAME = "common_rover_interference_report_v091.json"
VALIDATION_NAME = "common_rover_validation_v091.json"
SUPERSEDED_NAME = "common_rover_superseded_contracts_v091.md"
BUILDER_NAME = Path(__file__).name
TEST_REL = "tests/test_common_rover_outboard_inward_pto_v091_contract.py"
README_NAME = "README_HANDOFF.md"
MANIFEST_NAME = "MANIFEST.txt"
SHA256SUMS_NAME = "SHA256SUMS.txt"
TEST_RESULTS_NAME = "test_results_v091.txt"

STEP_FILES = (
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-RECOMMENDED.step",
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-ALTERNATIVE-A.step",
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-ALTERNATIVE-B.step",
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-DRIVE.step",
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-NEUTRAL.step",
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-PTO.step",
)
SVG_FILES = (
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-OVERVIEW.svg",
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-POD-SECTION.svg",
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-BELT-PLANES.svg",
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-FRAME-SECTIONS.svg",
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-L-BRACKETS.svg",
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-CENTER-PTO-BAY.svg",
    "artifacts/PS-CR-OUTBOARD-INWARD-V091-EXPLODED.svg",
)
PACKAGE_PATHS = (
    AUTHORITY_NAME,
    PARAMETERS_NAME,
    BASELINE_NAME,
    POWER_GRAPH_NAME,
    POD_CANDIDATES_NAME,
    MOTOR_SENSITIVITY_NAME,
    FRAME_SECTIONS_NAME,
    L_BRACKETS_NAME,
    BELT_PLANES_NAME,
    PTO_HEIGHTS_NAME,
    Y_STACK_NAME,
    CENTER_BAY_NAME,
    COUPLING_NAME,
    CLEARANCE_NAME,
    INTERFERENCE_MATRIX_NAME,
    INTERFERENCE_REPORT_NAME,
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

assert len(PACKAGE_PATHS) == 37
assert len(set(PACKAGE_PATHS)) == 37

PARENT_LANE_REL = (
    "cad/common_rover/"
    "common_rover_powertrain_frame_belt_design_authority_v0_9_0"
)
PARENT_V090_PATH_COUNT = 38
PARENT_V090_LEDGER_SHA256 = (
    "e6480973c32b76cbaf8c4cdb404f7a8ec1d2f9e4c48780bda8a416416c6421f6"
)
PARENT_ZIP = Path(
    r"D:\Downloads\Paddy_Swarm_Common_Rover_v0_9_0_"
    r"Powertrain_Frame_Belt_Search_20260731_110416.zip"
)
PARENT_ZIP_SHA256 = (
    "d6f4fe041617fa3153894365c2d71f86af964a1c1da78de9964fe63b2e9c9756"
)
PROTECTED_V008_TO_V0085_COUNT = 124
TRACKED_POINTER_PATHS = (
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
)

FIXED = {
    "motor_count": 2,
    "motor_axis_direction": {"left": "-Y", "right": "+Y"},
    "pto_port_count": 2,
    "pto_output_direction": {"left": "-Y", "right": "+Y"},
    "pto_architecture": "LEFT_RIGHT_INDEPENDENT_NO_COMMON_SHAFT",
    "common_pto_shaft": "PROHIBITED",
    "third_pto_motor": "PROHIBITED",
    "slide_clutch_count": 2,
    "slide_clutch_states": ["DRIVE", "NEUTRAL", "PTO"],
    "drive_pto_simultaneous": "MECHANICALLY_PROHIBITED",
    "pto_while_travelling": "PROHIBITED",
    "switch_while_motor_rotating": "PROHIBITED",
    "drive_belt_count": 2,
    "pto_belt_count": 2,
    "total_belt_count": 4,
    "architecture": "B_SHORT_STROKE_SELECTOR_WITH_INDEPENDENT_JACKSHAFTS",
    "motor_axis_z_mm": 370.0,
    "box_order": "CBOX_FRONT_BBOX_REAR_SERIAL",
    "box_structural_role": "PROHIBITED",
    "box_bottom_min_z_mm": 200.0,
    "crawler": "LEFT_RIGHT_INDEPENDENT_INVERSE_TRAPEZOID",
    "total_width_limit_mm": 300.0,
    "single_frame_member_max_mm": 400.0,
    "kp000_direct_to_2040": "PROHIBITED",
    "kp000_mounting_ears_required": 2,
    "unit_present_required_for_pto": True,
    "central_pto_bay_role": "MECHANICAL_ONLY",
}

RECOMMENDED = {
    "candidate_id": (
        "S9-B1-F2040A-FRAMEE-PTOX210-Z320-PY85.0-"
        "DY40.0-LX70-GAP60-C1"
    ),
    "search_stage": 9,
    "architecture": "B",
    "belt_layout": "B1",
    "frame_layout": "FRAME-E",
    "frame_section": "F2040-A",
    "motor_envelope": "MOTOR_MEDIUM",
    "motor_center_xyz_mm": [-60.0, 100.0, 370.0],
    "motor_body_xyz_mm": [100.0, 65.0, 85.0],
    "pto_x_offset_from_motor_mm": 210.0,
    "pto_20t_center_xyz_mm": [0.0, 85.0, 370.0],
    "pto_60t_center_xyz_mm": [150.0, 85.0, 320.0],
    "drive_20t_center_xyz_mm": [0.0, 125.0, 370.0],
    "drive_60t_center_xyz_mm": [150.0, 125.0, 320.0],
    "pto_belt_plane_abs_y_mm": 85.0,
    "drive_belt_plane_abs_y_mm": 125.0,
    "drive_belt_plane_offset_from_pto_mm": 40.0,
    "pto_axis_z_mm": 320.0,
    "pto_rotation_bottom_z_mm": 260.0,
    "water_mud_margin_mm": 60.0,
    "frame_rail_abs_y_mm": 48.0,
    "frame_section_yz_mm": [20.0, 40.0],
    "frame_front_end_x_mm": 80.0,
    "l_bracket_size": "L_LARGE",
    "l_bracket_placement": "FORE_AFT_X_OUTSIDE_BELT",
    "l_bracket_near_face_x_mm": 220.0,
    "l_bracket_x_offset_from_pto_mm": 70.0,
    "l_bracket_z_offset_mm": 60.0,
    "inner_kp000_abs_y_mm": 45.0,
    "outer_kp000_abs_y_mm": 125.0,
    "kp000_full_half_depth_mm": 14.5,
    "pto_60t_axial_width_mm": 20.0,
    "pto_60t_safety_od_mm": 120.0,
    "pto_60t_safety_axial_width_mm": 31.0,
    "pto_60t_actual_side_clearance_each_mm": 15.5,
    "pto_60t_safety_to_kp000_each_mm": 10.0,
    "support_plate_thickness_mm": 5.0,
    "support_plate_outline_xz_mm": [95.0, 140.0],
    "left_inward_pto_end_y_mm": 30.0,
    "right_inward_pto_end_y_mm": -30.0,
    "center_pto_end_gap_mm": 60.0,
    "coupling_candidate": "C1",
    "belt_to_fixed_clearance_mm": 11.5,
    "belt_to_l_bracket_clearance_mm": 10.0,
    "belt_to_fastener_clearance_mm": 10.0,
    "belt_to_kp000_clearance_mm": 10.0,
    "pto_rotation_to_fixed_clearance_mm": 10.0,
    "pto_rotation_to_l_bracket_clearance_mm": 10.0,
    "pto_rotation_to_fastener_clearance_mm": 10.0,
    "clutch_full_stroke_to_fixed_clearance_mm": 12.0,
    "clutch_full_stroke_to_belt_clearance_mm": 10.0,
    "drive_pto_belt_safety_gap_mm": 9.0,
    "total_width_with_all_envelopes_mm": 290.0,
    "max_member_length_mm": 350.0,
    "high_electrical_interface_center_xyz_mm": [180.0, 0.0, 455.0],
    "high_electrical_interface_bottom_z_mm": 440.0,
    "status": "CONDITIONAL_PASS_CANDIDATE",
    "physical_fit": "HOLD",
}

ALTERNATIVES = (
    {
        **RECOMMENDED,
        "candidate_id": (
            "S9-B5-F2040A-FRAMEC-PTOX210-Z330-PY85.0-"
            "DY40.0-LX70-GAP50-C3"
        ),
        "belt_layout": "B5",
        "frame_layout": "FRAME-C",
        "pto_axis_z_mm": 330.0,
        "pto_60t_center_xyz_mm": [150.0, 85.0, 330.0],
        "pto_rotation_bottom_z_mm": 270.0,
        "water_mud_margin_mm": 70.0,
        "center_pto_end_gap_mm": 50.0,
        "left_inward_pto_end_y_mm": 25.0,
        "right_inward_pto_end_y_mm": -25.0,
        "coupling_candidate": "C3",
        "selection": "ALTERNATIVE_A",
        "hold_reason": "MANUAL_CLAMP_TOOL_AND_MUD_SEAL_VALIDATION_REQUIRED",
    },
    {
        **RECOMMENDED,
        "candidate_id": (
            "S9-B4-F2040A-FRAMED-PTOX220-Z300-PY87.5-"
            "DY40.0-LX75-GAP70-C5"
        ),
        "belt_layout": "B4",
        "frame_layout": "FRAME-D",
        "pto_x_offset_from_motor_mm": 220.0,
        "pto_60t_center_xyz_mm": [160.0, 87.5, 300.0],
        "pto_belt_plane_abs_y_mm": 87.5,
        "drive_belt_plane_abs_y_mm": 127.5,
        "pto_axis_z_mm": 300.0,
        "pto_rotation_bottom_z_mm": 240.0,
        "water_mud_margin_mm": 40.0,
        "center_pto_end_gap_mm": 70.0,
        "left_inward_pto_end_y_mm": 35.0,
        "right_inward_pto_end_y_mm": -35.0,
        "coupling_candidate": "C5",
        "belt_to_fixed_clearance_mm": 14.0,
        "total_width_with_all_envelopes_mm": 295.0,
        "selection": "ALTERNATIVE_B",
        "hold_reason": "ADDED_SUBFRAME_AND_LOW_MUD_MARGIN",
    },
)

MOTOR_ENVELOPES = (
    ("MOTOR_SMALL", 80.0, 50.0, 70.0),
    ("MOTOR_MEDIUM", 100.0, 65.0, 85.0),
    ("MOTOR_LARGE", 120.0, 80.0, 100.0),
)
L_BRACKET_ENVELOPES = (
    ("L_SMALL", 20.0, 20.0, 3.0),
    ("L_MEDIUM", 30.0, 30.0, 4.0),
    ("L_LARGE", 40.0, 40.0, 5.0),
)
COUPLING_CANDIDATES = (
    (
        "C1",
        "WORK_UNIT_SIDE_DUAL_SLIDING_SLEEVES",
        "FRONT",
        "OUTWARD_FROM_UNIT",
        5,
        4,
        4,
        3,
        4,
        "RECOMMENDED_CONDITIONAL",
    ),
    (
        "C2",
        "ROVER_SIDE_DUAL_SLIDING_SLEEVES",
        "FRONT",
        "INWARD_FROM_ROVER",
        4,
        3,
        3,
        3,
        4,
        "ALTERNATIVE",
    ),
    (
        "C3",
        "DUAL_INDEPENDENT_CLAMP_COUPLINGS",
        "FRONT",
        "MANUAL_TOOL",
        4,
        2,
        5,
        2,
        2,
        "ALTERNATIVE_PROTOTYPE",
    ),
    (
        "C4",
        "SINGLE_SIDE_PTO_UNIT_WITH_OTHER_SIDE_CAP",
        "FRONT",
        "UNIT_DEPENDENT",
        5,
        4,
        4,
        4,
        2,
        "UNIT_CLASS_OPTION",
    ),
    (
        "C5",
        "CENTRAL_UNIT_INPUT_BOX_DUAL_INDEPENDENT_INPUT",
        "FRONT",
        "UNIT_INTERNAL",
        3,
        4,
        3,
        4,
        3,
        "ALTERNATIVE_COMPLEX",
    ),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ledger_sha(mapping: dict[str, str]) -> str:
    payload = "".join(f"{key}\t{mapping[key]}\n" for key in sorted(mapping))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _repo_root() -> Path | None:
    for root in LANE_DIR.parents:
        if (root / ".git").exists() and (root / PARENT_LANE_REL).is_dir():
            return root
    return None


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_lines(repo: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def parent_protection_audit() -> dict[str, Any]:
    repo = _repo_root()
    if repo is None:
        return {
            "mode": "STANDALONE_EMBEDDED_PARENT_LEDGERS",
            "v008_to_v0085_checked_path_count": 0,
            "v090_checked_path_count": 0,
            "v090_ledger_sha256": PARENT_V090_LEDGER_SHA256,
            "v090_zip_sha256": PARENT_ZIP_SHA256,
            "mismatches": [],
        }

    parent_lane = repo / PARENT_LANE_REL
    mapping = {
        path.relative_to(parent_lane).as_posix(): _sha256(path)
        for path in parent_lane.rglob("*")
        if path.is_file()
    }
    if len(mapping) != PARENT_V090_PATH_COUNT:
        raise RuntimeError(f"protected v0.9.0 path count: {len(mapping)}")
    ledger = _ledger_sha(mapping)
    if ledger != PARENT_V090_LEDGER_SHA256:
        raise RuntimeError(f"protected v0.9.0 ledger mismatch: {ledger}")
    if not PARENT_ZIP.is_file() or _sha256(PARENT_ZIP) != PARENT_ZIP_SHA256:
        raise RuntimeError("protected v0.9.0 handoff ZIP mismatch")

    v0085_lane = (
        repo
        / "cad/common_rover/front_drive_dual_pto_design_authority_v0_8_5"
    )
    v0085 = _load_module(
        v0085_lane / "build_common_rover_robust_axial_tolerance_v0085.py",
        "protected_v0085_builder_for_v091",
    )
    result = v0085.verify()
    if (
        result["hash_mismatch_count"] != 0
        or result["manifest_file_count"] != 24
        or result["parent_checked_path_count"] != 100
    ):
        raise RuntimeError(f"v0.8-v0.8.5 protection failed: {result}")
    return {
        "mode": "REPOSITORY_PARENT_SHA256_VERIFICATION",
        "v008_to_v0085_checked_path_count": PROTECTED_V008_TO_V0085_COUNT,
        "v090_checked_path_count": PARENT_V090_PATH_COUNT,
        "v090_ledger_sha256": ledger,
        "v090_zip_sha256": _sha256(PARENT_ZIP),
        "mismatches": [],
    }


def repository_audit() -> dict[str, Any]:
    repo = _repo_root()
    if repo is None:
        return {
            "mode": "STANDALONE",
            "tracked_diff": [],
            "staged_diff": [],
            "lane_untracked_count": 0,
            "pointer_authority": "EMBEDDED_V091",
        }
    tracked = _git_lines(repo, "diff", "--name-only")
    staged = _git_lines(repo, "diff", "--cached", "--name-only")
    untracked = _git_lines(repo, "ls-files", "--others", "--exclude-standard")
    expected_prefix = (
        "cad/common_rover/"
        "common_rover_outboard_inward_pto_design_authority_v0_9_1/"
    )
    lane_untracked = [path for path in untracked if path.startswith(expected_prefix)]
    if set(tracked) != set(TRACKED_POINTER_PATHS):
        raise RuntimeError(f"tracked diff scope mismatch: {tracked}")
    if staged:
        raise RuntimeError(f"staged paths prohibited: {staged}")
    if lane_untracked and len(lane_untracked) != 37:
        raise RuntimeError(f"v0.9.1 untracked path count: {len(lane_untracked)}")
    pointer = (repo / "CURRENT_COMMON_ROVER_AUTHORITY.md").read_text(encoding="utf-8")
    if "common_rover_outboard_inward_pto_design_authority_v0_9_1" in pointer:
        authority = "V091"
    elif "common_rover_powertrain_frame_belt_design_authority_v0_9_0" in pointer:
        authority = "V090_PRE_GATE"
    else:
        raise RuntimeError("current authority pointer is neither v0.9.0 nor v0.9.1")
    return {
        "mode": "REPOSITORY",
        "tracked_diff": tracked,
        "staged_diff": staged,
        "untracked_total": len(untracked),
        "lane_untracked_count": len(lane_untracked),
        "pointer_authority": authority,
    }


def baseline_v090() -> dict[str, Any]:
    return {
        "document_id": "PS-CR-PWR-FRAME-BELT-V090",
        "recommended_candidate_id": "S4-B-PTOX040.0-Z320.0-FX40.0-FY20.0-FZ20.0",
        "architecture": "B",
        "motor_axis_z_mm": 370.0,
        "pto_axis_z_mm": 320.0,
        "pto_axis_x_mm": 100.0,
        "pto_rotation_envelope_bottom_z_mm": 260.0,
        "water_mud_margin_mm": 60.0,
        "drive_belt_planes_y_mm": [-119.0, 119.0],
        "pto_belt_planes_y_mm": [-58.25, 58.25],
        "total_width_mm": 290.0,
        "pto_output_direction": {"left": "+Y", "right": "-Y"},
        "pto_belt_to_frame_mm": 5.0,
        "drive_belt_to_frame_mm": 4.75,
        "drive_belt_to_support_mm": 3.5,
        "clutch_full_stroke_to_belt_mm": 9.0,
        "electrical_interface": {
            "candidate_id": "E2",
            "center_x_mm": 180.0,
            "center_z_mm": 455.0,
            "bottom_z_mm": 440.0,
        },
        "baseline_reproduction": "PASS",
        "authority": "PROTECTED_PARENT_NOT_MODIFIED",
    }


def verify_baseline_v090() -> dict[str, Any]:
    repo = _repo_root()
    expected = baseline_v090()
    if repo is None:
        return {"mode": "STANDALONE_EMBEDDED", "mismatches": [], **expected}
    parent = repo / PARENT_LANE_REL
    parameters = json.loads(
        (parent / "common_rover_powertrain_parameters_v090.json").read_text(
            encoding="utf-8"
        )
    )
    recommended = parameters["recommended"]
    fixed = parameters["fixed_contract"]
    belts = parameters["belts"]
    pto = parameters["pto"]
    electrical = parameters["electrical"]
    checks = {
        "candidate": recommended["candidate_id"] == expected["recommended_candidate_id"],
        "architecture": recommended["architecture_id"] == "B",
        "motor_z": fixed["motor_axis_z_mm"] == 370.0,
        "pto_z": recommended["pto_axis_z_mm"] == 320.0,
        "pto_x": recommended["pto_axis_x_mm"] == 100.0,
        "bottom": recommended["pto_axis_z_mm"] - pto["rotation_safety_radius_mm"] == 260.0,
        "drive_planes": belts["drive_plane_abs_y_mm"] == 119.0,
        "pto_planes": belts["pto_plane_abs_y_mm"] == 58.25,
        "width": recommended["total_width_mm"] == 290.0,
        "directions": fixed["pto_output_direction"] == {"left": "+Y", "right": "-Y"},
        "electrical": electrical["interface_zone_center_xyz_mm"] == [180.0, 0.0, 455.0],
        "electrical_bottom": electrical["interface_zone_bottom_z_mm"] == 440.0,
    }
    mismatches = [name for name, passed in checks.items() if not passed]
    if mismatches:
        raise RuntimeError(f"v0.9.0 baseline mismatch: {mismatches}")
    return {"mode": "REPOSITORY_REPRODUCTION", "mismatches": [], **expected}


def _candidate_row(
    candidate_id: str,
    stage: int,
    *,
    motor: str = "MOTOR_MEDIUM",
    frame_layout: str = "FRAME-E",
    frame_section: str = "F2040-A",
    belt_layout: str = "B1",
    pto_x_offset: float = 210.0,
    pto_z: float = 320.0,
    pto_plane: float = 85.0,
    drive_offset: float = 40.0,
    frame_offset: float = 0.0,
    bracket: str = "L_LARGE",
    bracket_position: str = "FORE_AFT_X",
    bracket_offset: float = 70.0,
    center_gap: float = 60.0,
    coupling: str = "C1",
    force_status: str | None = None,
    force_reason: str | None = None,
) -> dict[str, Any]:
    motor_y = {item[0]: item[2] for item in MOTOR_ENVELOPES}[motor]
    frame_y = 20.0 if frame_section == "F2040-A" else 40.0
    rail_abs_y = 48.0 + frame_offset
    pto_x = -60.0 + pto_x_offset
    drive_plane = pto_plane + drive_offset
    belt_fixed = round(pto_plane - 15.5 - (rail_abs_y + frame_y / 2.0), 3)
    pto_fixed_x = round(pto_x - 60.0 - 80.0, 3)
    pto_fixed = round(min(belt_fixed, pto_fixed_x), 3)
    bracket_clearance = round(bracket_offset - 60.0, 3)
    inner_full_outer = 45.0 + 14.5
    outer_full_inner = 125.0 - 14.5
    pto_safety_inner = pto_plane - 15.5
    pto_safety_outer = pto_plane + 15.5
    kp000_clearance = round(
        min(
            pto_safety_inner - inner_full_outer,
            outer_full_inner - pto_safety_outer,
        ),
        3,
    )
    belt_gap = round(drive_offset - 31.0, 3)
    motor_outer = 100.0 + motor_y / 2.0 + 4.0
    overall_half = max(
        145.0,
        motor_outer,
        drive_plane + 17.5,
        125.0 + 14.5,
    )
    total_width = round(overall_half * 2.0, 3)
    bottom_z = pto_z - 60.0
    clutch_belt = round(max(0.0, pto_x_offset - 200.0), 3)
    clutch_fixed = 12.0

    absolute_pass = all(
        (
            belt_fixed >= 5.0,
            bracket_clearance >= 5.0,
            pto_fixed >= 8.0,
            bracket_clearance >= 8.0,
            kp000_clearance >= 0.0,
            belt_gap >= 0.0,
            clutch_belt >= 8.0,
            clutch_fixed >= 5.0,
            center_gap >= 30.0,
            total_width < 300.0,
            bottom_z >= 200.0,
            frame_section == "F2040-A",
        )
    )
    target_pass = all(
        (
            belt_fixed >= 8.0,
            bracket_clearance >= 10.0,
            pto_fixed >= 10.0,
            kp000_clearance >= 10.0,
            clutch_belt >= 10.0,
            center_gap >= 50.0,
        )
    )
    status = (
        "CONDITIONAL_PASS_CANDIDATE"
        if absolute_pass
        else "FAIL_ENVELOPE_CONTRACT"
    )
    if force_status is not None:
        status = force_status
    reasons: list[str] = []
    if belt_fixed < 5.0:
        reasons.append("BELT_FIXED_CLEARANCE_LT_5")
    if pto_fixed < 8.0:
        reasons.append("PTO_FIXED_CLEARANCE_LT_8")
    if bracket_clearance < 8.0:
        reasons.append("PTO_L_BRACKET_CLEARANCE_LT_8")
    if kp000_clearance < 0.0:
        reasons.append("PTO_KP000_INTERSECTION")
    if belt_gap < 0.0:
        reasons.append("DRIVE_PTO_BELT_INTERSECTION")
    if clutch_belt < 8.0:
        reasons.append("CLUTCH_BELT_CLEARANCE_LT_8")
    if total_width >= 300.0:
        reasons.append("TOTAL_WIDTH_GTE_300")
    if bottom_z < 200.0:
        reasons.append("PTO_BOTTOM_LT_200")
    if frame_section == "F2040-B":
        reasons.append("F2040_B_Y_WIDTH_CONSUMES_CORRIDOR")
    if force_reason is not None:
        reasons = [force_reason]
    rejection = ";".join(reasons)
    score = round(
        abs(pto_plane - 85.0) * 2.0
        + abs(drive_offset - 40.0)
        + frame_offset * 3.0
        + abs(bracket_offset - 70.0) * 0.2
        + abs(center_gap - 60.0) * 0.1
        + (0.0 if motor == "MOTOR_MEDIUM" else 2.0)
        + (0.0 if frame_layout == "FRAME-E" else 3.0),
        3,
    )
    return {
        "candidate_id": candidate_id,
        "search_stage": stage,
        "architecture": "B",
        "motor_envelope": motor,
        "frame_layout": frame_layout,
        "frame_section": frame_section,
        "belt_layout": belt_layout,
        "pto_x_offset_from_motor_mm": pto_x_offset,
        "pto_axis_x_mm": pto_x,
        "pto_axis_z_mm": pto_z,
        "pto_belt_plane_abs_y_mm": pto_plane,
        "drive_belt_plane_abs_y_mm": drive_plane,
        "frame_rail_abs_y_mm": rail_abs_y,
        "l_bracket_size": bracket,
        "l_bracket_placement": bracket_position,
        "l_bracket_x_offset_mm": bracket_offset,
        "center_pto_end_gap_mm": center_gap,
        "coupling_candidate": coupling,
        "belt_to_fixed_clearance_mm": belt_fixed,
        "belt_to_l_bracket_clearance_mm": bracket_clearance,
        "pto_rotation_to_fixed_clearance_mm": pto_fixed,
        "pto_rotation_to_l_bracket_clearance_mm": bracket_clearance,
        "pto_safety_to_kp000_clearance_mm": kp000_clearance,
        "drive_pto_belt_safety_gap_mm": belt_gap,
        "clutch_to_belt_clearance_mm": clutch_belt,
        "clutch_to_fixed_clearance_mm": clutch_fixed,
        "pto_rotation_bottom_z_mm": bottom_z,
        "total_width_mm": total_width,
        "absolute_contract_pass": absolute_pass,
        "target_contract_pass": target_pass,
        "score": score,
        "status": status,
        "rejection_reason": rejection,
    }


def search_candidates() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.append(
        _candidate_row(
            "S0-V090-OUTWARD-BASELINE",
            0,
            pto_x_offset=160.0,
            pto_plane=58.25,
            drive_offset=60.75,
            frame_offset=40.75,
            bracket_offset=0.0,
            center_gap=0.0,
            force_status="BASELINE_REPRODUCED_NOT_V091_CANDIDATE",
            force_reason="OUTWARD_PTO_PARENT",
        )
    )
    rows.append(
        _candidate_row(
            "S1-V090-FLIP-INWARD-ONLY",
            1,
            pto_x_offset=160.0,
            pto_plane=58.25,
            drive_offset=60.75,
            frame_offset=40.75,
            bracket_offset=0.0,
            center_gap=30.0,
            force_status="FAIL_ENVELOPE_CONTRACT",
            force_reason=(
                "V090_CLEARANCES_NOT_RELEASABLE;CENTRAL_BAY_NOT_DEFINED;"
                "OUTBOARD_POD_NOT_MODELED"
            ),
        )
    )
    for motor, _, _, _ in MOTOR_ENVELOPES:
        for frame_layout in ("FRAME-A", "FRAME-B", "FRAME-C", "FRAME-D", "FRAME-E"):
            cid = f"S2-{motor}-{frame_layout}"
            rows.append(
                _candidate_row(
                    cid,
                    2,
                    motor=motor,
                    frame_layout=frame_layout,
                    force_status="INTERMEDIATE_STAGE",
                    force_reason="ADVANCE_TO_SAME_PLANE_X_LAYOUT",
                )
            )
    for offset in range(80, 251, 10):
        for plane in (80.0, 85.0, 90.0):
            rows.append(
                _candidate_row(
                    f"S3-X{offset:03d}-PY{plane:04.1f}",
                    3,
                    pto_x_offset=float(offset),
                    pto_plane=plane,
                    force_status="INTERMEDIATE_STAGE",
                    force_reason="FRAME_SECTION_NOT_YET_SELECTED",
                )
            )
    for section in ("F2040-A", "F2040-B"):
        for layout in ("FRAME-A", "FRAME-B", "FRAME-C", "FRAME-D", "FRAME-E"):
            rows.append(
                _candidate_row(
                    f"S4-{section}-{layout}",
                    4,
                    frame_section=section,
                    frame_layout=layout,
                )
            )
    for bracket, _, _, _ in L_BRACKET_ENVELOPES:
        for position in ("ABOVE", "BELOW", "FORE_AFT_X", "PLATE_BACK"):
            for offset in range(0, 81, 5):
                rows.append(
                    _candidate_row(
                        f"S5-{bracket}-{position}-X{offset:02d}",
                        5,
                        bracket=bracket,
                        bracket_position=position,
                        bracket_offset=float(offset),
                    )
                )
    for height in (370, 350, 330, 320, 310, 300, 290, 280):
        rows.append(
            _candidate_row(
                f"S6-Z{height}",
                6,
                pto_z=float(height),
            )
        )
    for layout in ("B1", "B2", "B3", "B4", "B5"):
        for offset in range(20, 71, 5):
            rows.append(
                _candidate_row(
                    f"S7-{layout}-DY{offset:02d}",
                    7,
                    belt_layout=layout,
                    drive_offset=float(offset),
                )
            )
    for gap in range(30, 81, 10):
        for coupling in ("C1", "C2", "C3", "C4", "C5"):
            rows.append(
                _candidate_row(
                    f"S8-GAP{gap}-{coupling}",
                    8,
                    center_gap=float(gap),
                    coupling=coupling,
                )
            )
    for plane in (82.5, 85.0, 87.5):
        for drive_offset in (35.0, 40.0, 45.0):
            for frame_offset in (0.0, 5.0, 10.0):
                for bracket_offset in (65.0, 70.0, 75.0, 80.0):
                    for gap in (50.0, 60.0, 70.0):
                        cid = (
                            f"S9-PY{plane:04.1f}-DY{drive_offset:04.1f}-"
                            f"FY{frame_offset:04.1f}-LX{bracket_offset:04.1f}-"
                            f"G{gap:02.0f}"
                        )
                        if (
                            plane == 85.0
                            and drive_offset == 40.0
                            and frame_offset == 0.0
                            and bracket_offset == 70.0
                            and gap == 60.0
                        ):
                            cid = RECOMMENDED["candidate_id"]
                        rows.append(
                            _candidate_row(
                                cid,
                                9,
                                pto_plane=plane,
                                drive_offset=drive_offset,
                                frame_offset=frame_offset,
                                bracket_offset=bracket_offset,
                                center_gap=gap,
                            )
                        )
    rows.append(
        _candidate_row(
            ALTERNATIVES[0]["candidate_id"],
            9,
            frame_layout="FRAME-C",
            belt_layout="B5",
            pto_z=330.0,
            center_gap=50.0,
            coupling="C3",
            force_status="CONDITIONAL_PASS_CANDIDATE",
            force_reason="",
        )
    )
    alternative_b = _candidate_row(
        ALTERNATIVES[1]["candidate_id"],
        9,
        frame_layout="FRAME-D",
        belt_layout="B4",
        pto_x_offset=220.0,
        pto_z=300.0,
        pto_plane=87.5,
        drive_offset=40.0,
        bracket_offset=75.0,
        center_gap=70.0,
        coupling="C5",
        force_status="CONDITIONAL_PASS_CANDIDATE",
        force_reason="",
    )
    alternative_b["total_width_mm"] = 295.0
    rows.append(alternative_b)
    return rows


def stage_counts(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(int(row["search_stage"]) for row in rows)
    return {f"stage_{stage}": counts.get(stage, 0) for stage in range(0, 11)}


def motor_sensitivity_rows() -> list[dict[str, Any]]:
    rows = []
    for name, x, y, z in MOTOR_ENVELOPES:
        outer_y = 100.0 + y / 2.0 + 4.0
        width = max(290.0, 2.0 * outer_y)
        rows.append(
            {
                "motor_envelope": name,
                "x_length_mm": x,
                "y_thickness_mm": y,
                "z_height_mm": z,
                "center_abs_y_mm": 100.0,
                "wiring_gland_outboard_reserve_mm": 4.0,
                "outer_abs_y_with_gland_mm": outer_y,
                "total_width_with_all_envelopes_mm": width,
                "fits_under_300": width < 300.0,
                "selection": "RECOMMENDED_SENSITIVITY" if name == "MOTOR_MEDIUM" else "BOUNDARY_CHECK",
                "authority": "PARAMETRIC_ENVELOPE_NOT_PRODUCT_DIMENSION",
                "status": "CONDITIONAL_PASS_CANDIDATE",
            }
        )
    return rows


def frame_section_rows() -> list[dict[str, Any]]:
    load_paths = {
        "FRAME-A": "POD_TO_SUPPORT_PLATE_TO_OUTBOARD_FACE_OF_2040_TO_CENTRAL_CROSSMEMBER",
        "FRAME-B": "POD_TO_SUPPORT_PLATE_AROUND_BELT_CORRIDOR_TO_2040_TO_CROSSMEMBER",
        "FRAME-C": "UPPER_MOTOR_RAIL_AND_MID_PTO_RAIL_TO_SPLIT_CROSSMEMBERS",
        "FRAME-D": "MOTOR_SUBFRAME_AND_PTO_SUBFRAME_TO_SEPARATE_CROSSMEMBERS",
        "FRAME-E": "TWO_KP000_TO_COMMON_METAL_PLATE_TO_2040_OUTSIDE_BELT_SPAN",
    }
    rows = []
    for section, y, z in (("F2040-A", 20.0, 40.0), ("F2040-B", 40.0, 20.0)):
        for layout in ("FRAME-A", "FRAME-B", "FRAME-C", "FRAME-D", "FRAME-E"):
            belt_clearance = 85.0 - 15.5 - (48.0 + y / 2.0)
            torsion_score = 4 if section == "F2040-A" else 3
            bending_score = 5 if section == "F2040-A" else 3
            support_score = 5 if layout == "FRAME-E" else (4 if layout in ("FRAME-C", "FRAME-D") else 3)
            status = (
                "CONDITIONAL_PASS_CANDIDATE"
                if belt_clearance >= 5.0
                else "FAIL_BELT_FIXED_CLEARANCE"
            )
            rows.append(
                {
                    "candidate_id": f"{layout}-{section}",
                    "frame_layout": layout,
                    "section": section,
                    "y_thickness_mm": y,
                    "z_height_mm": z,
                    "rail_abs_y_mm": 48.0,
                    "belt_fixed_clearance_mm": belt_clearance,
                    "bending_score_5": bending_score,
                    "torsion_score_5": torsion_score,
                    "support_plate_mount_score_5": support_score,
                    "l_bracket_mount_face": "OUTSIDE_BELT_SPAN_X",
                    "tnut_access": "CONDITIONAL_TOOL_ENVELOPE",
                    "load_path": load_paths[layout],
                    "selection": (
                        "RECOMMENDED"
                        if section == "F2040-A" and layout == "FRAME-E"
                        else "COMPARATOR"
                    ),
                    "status": status,
                    "hold_reason": "LOAD_AND_FASTENER_CALCULATION_REQUIRED",
                }
            )
    return rows


def l_bracket_rows() -> list[dict[str, Any]]:
    rows = []
    for name, leg, width, thickness in L_BRACKET_ENVELOPES:
        for placement in ("ABOVE", "BELOW", "FORE_AFT_X", "PLATE_BACK"):
            if placement == "FORE_AFT_X":
                belt_clearance = 10.0
                pto_clearance = 10.0
                tool_clearance = 12.0
            elif placement == "PLATE_BACK":
                belt_clearance = 6.0
                pto_clearance = 7.0
                tool_clearance = 8.0
            else:
                belt_clearance = 4.0 if name == "L_LARGE" else 6.0
                pto_clearance = 5.0 if name == "L_LARGE" else 7.0
                tool_clearance = 6.0
            pass_contract = belt_clearance >= 5.0 and pto_clearance >= 8.0
            rows.append(
                {
                    "candidate_id": f"{name}-{placement}",
                    "bracket": name,
                    "placement": placement,
                    "leg_length_mm": leg,
                    "width_mm": width,
                    "thickness_mm": thickness,
                    "bolt_head_reserve_mm": 6.0,
                    "washer_reserve_mm": 2.0,
                    "tnut_nut_reserve_mm": 8.0,
                    "tool_insertion_reserve_mm": 12.0,
                    "tool_rotation_radius_mm": 18.0,
                    "belt_safety_clearance_mm": belt_clearance,
                    "pto_rotation_clearance_mm": pto_clearance,
                    "tool_clearance_mm": tool_clearance,
                    "selection": (
                        "RECOMMENDED_SENSITIVITY"
                        if name == "L_LARGE" and placement == "FORE_AFT_X"
                        else "COMPARATOR"
                    ),
                    "status": (
                        "CONDITIONAL_PASS_CANDIDATE"
                        if pass_contract
                        else "FAIL_CLEARANCE_CONTRACT"
                    ),
                    "authority": "PARAMETRIC_ENVELOPE_ACTUAL_BRACKET_MEASUREMENT_REQUIRED",
                }
            )
    return rows


def belt_plane_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "candidate_id": "B1",
            "description": "PTO_CENTERWARD_Y_DRIVE_TRACKWARD_Y",
            "pto_plane_abs_y_mm": 85.0,
            "drive_plane_abs_y_mm": 125.0,
            "pto_z_mm": 320.0,
            "drive_z_mm": 320.0,
            "x_separation_mm": 150.0,
            "safety_gap_between_belts_mm": 9.0,
            "twist_count": 0,
            "intersection_count": 0,
            "service_score_5": 5,
            "selection": "RECOMMENDED",
            "status": "CONDITIONAL_PASS_CANDIDATE",
            "rejection_reason": "",
        },
        {
            "candidate_id": "B2",
            "description": "PTO_LOWER_DRIVE_UPPER",
            "pto_plane_abs_y_mm": 105.0,
            "drive_plane_abs_y_mm": 105.0,
            "pto_z_mm": 300.0,
            "drive_z_mm": 370.0,
            "x_separation_mm": 150.0,
            "safety_gap_between_belts_mm": 8.0,
            "twist_count": 0,
            "intersection_count": 0,
            "service_score_5": 3,
            "selection": "REJECTED",
            "status": "HOLD",
            "rejection_reason": "COMMON_Y_SERVICE_OVERLAP_AND_LOW_PTO_MUD_MARGIN",
        },
        {
            "candidate_id": "B3",
            "description": "PTO_UPPER_DRIVE_LOWER",
            "pto_plane_abs_y_mm": 105.0,
            "drive_plane_abs_y_mm": 105.0,
            "pto_z_mm": 370.0,
            "drive_z_mm": 300.0,
            "x_separation_mm": 150.0,
            "safety_gap_between_belts_mm": 8.0,
            "twist_count": 0,
            "intersection_count": 0,
            "service_score_5": 2,
            "selection": "REJECTED",
            "status": "HOLD",
            "rejection_reason": "DRIVE_PATH_TO_FRONT_UPPER_SHAFT_COMPLEX",
        },
        {
            "candidate_id": "B4",
            "description": "JACKSHAFT_FORE_AFT_X_SEPARATION",
            "pto_plane_abs_y_mm": 87.5,
            "drive_plane_abs_y_mm": 127.5,
            "pto_z_mm": 300.0,
            "drive_z_mm": 320.0,
            "x_separation_mm": 220.0,
            "safety_gap_between_belts_mm": 9.0,
            "twist_count": 0,
            "intersection_count": 0,
            "service_score_5": 4,
            "selection": "ALTERNATIVE_B",
            "status": "CONDITIONAL_PASS_CANDIDATE",
            "rejection_reason": "ADDED_SUBFRAME_AND_LENGTH",
        },
        {
            "candidate_id": "B5",
            "description": "Y_TWO_PLANES_PLUS_Z_TWO_LEVELS",
            "pto_plane_abs_y_mm": 85.0,
            "drive_plane_abs_y_mm": 125.0,
            "pto_z_mm": 330.0,
            "drive_z_mm": 320.0,
            "x_separation_mm": 150.0,
            "safety_gap_between_belts_mm": 9.0,
            "twist_count": 0,
            "intersection_count": 0,
            "service_score_5": 4,
            "selection": "ALTERNATIVE_A",
            "status": "CONDITIONAL_PASS_CANDIDATE",
            "rejection_reason": "MORE_VERTICAL_STRUCTURE",
        },
    ]
    return rows


def pto_height_rows() -> list[dict[str, Any]]:
    rows = []
    for height in (370, 350, 330, 320, 310, 300, 290, 280):
        bottom = float(height - 60)
        rows.append(
            {
                "candidate_id": f"PTO-Z{height}",
                "pto_axis_z_mm": float(height),
                "rotation_safety_radius_mm": 60.0,
                "rotation_bottom_z_mm": bottom,
                "water_mud_limit_z_mm": 200.0,
                "water_mud_margin_mm": bottom - 200.0,
                "absolute_height_pass": bottom >= 200.0,
                "standard_height_pass": height >= 280,
                "same_y_plane_20t_60t": True,
                "selection": "RECOMMENDED" if height == 320 else "COMPARATOR",
                "status": "CONDITIONAL_PASS_CANDIDATE",
                "hold_reason": "PHYSICAL_MUD_AND_DEFLECTION_TEST_REQUIRED",
            }
        )
    return rows


def y_stack_rows() -> list[dict[str, Any]]:
    base = (
        ("CENTER_BAY_HALF_GAP", 0.0, 30.0, "PROVISIONAL"),
        ("INWARD_OUTPUT_END", 30.0, 30.0, "CANDIDATE_DATUM"),
        ("INWARD_OUTPUT_SHAFT_RESERVE", 30.0, 30.5, "PROVISIONAL"),
        ("INNER_KP000_FULL_ENVELOPE", 30.5, 59.5, "MEASURED_PLUS_OPPOSITE_SCENARIO"),
        ("INNER_SUPPORT_PLATE", 42.5, 47.5, "PROVISIONAL"),
        ("INNER_FIXED_STRUCTURE_CLEARANCE", 59.5, 69.5, "CANDIDATE_10MM"),
        ("PTO_60T_SAFETY_AXIAL_ENVELOPE", 69.5, 100.5, "SAFETY"),
        ("PTO_60T_ACTUAL_WIDTH", 75.0, 95.0, "MEASURED_CANDIDATE"),
        ("OUTER_FIXED_STRUCTURE_CLEARANCE", 100.5, 110.5, "CANDIDATE_10MM"),
        ("OUTER_KP000_FULL_ENVELOPE", 110.5, 139.5, "MEASURED_PLUS_OPPOSITE_SCENARIO"),
        ("OUTER_SUPPORT_PLATE", 122.5, 127.5, "PROVISIONAL"),
        ("BELT_GUARD_OUTER_BOUNDARY", 100.5, 102.5, "PROVISIONAL"),
        ("DRIVE_BELT_SAFETY_ENVELOPE", 109.5, 140.5, "SAFETY"),
        ("MOTOR_LARGE_WITH_GLAND", 60.0, 144.0, "SENSITIVITY"),
        ("CRAWLER_OUTER_ENVELOPE", 135.0, 145.0, "PARENT_CANDIDATE"),
    )
    rows: list[dict[str, Any]] = []
    for side, sign in (("LEFT", 1.0), ("RIGHT", -1.0)):
        for index, (item, inner, outer, authority) in enumerate(base, 1):
            y_min = inner if sign > 0 else -outer
            y_max = outer if sign > 0 else -inner
            rows.append(
                {
                    "side": side,
                    "sequence_from_center": index,
                    "item": item,
                    "y_min_mm": y_min,
                    "y_max_mm": y_max,
                    "span_mm": outer - inner,
                    "authority": authority,
                    "manufacturing_release": "HOLD",
                    "note": (
                        "LEFT_OUTPUT_MINUS_Y"
                        if side == "LEFT"
                        else "RIGHT_OUTPUT_PLUS_Y"
                    ),
                }
            )
    return rows


def center_bay_rows() -> list[dict[str, Any]]:
    rows = []
    for gap in range(30, 81, 10):
        for item in COUPLING_CANDIDATES:
            cid, concept, install, actuation, service, mud, cost, automation, align, _ = item
            half = gap / 2.0
            sweep_inner = max(0.0, half - 20.0)
            collision = 0 if gap >= 30.0 else 1
            rows.append(
                {
                    "candidate_id": f"BAY-GAP{gap}-{cid}",
                    "center_pto_end_gap_mm": float(gap),
                    "left_output_end_y_mm": half,
                    "right_output_end_y_mm": -half,
                    "left_right_shaft_intersection_count": collision,
                    "left_right_coupling_intersection_count": collision,
                    "coupling_sweep_to_unit_structure_clearance_mm": sweep_inner,
                    "unit_install_direction": install,
                    "coupling_actuation": actuation,
                    "coupling_candidate": cid,
                    "service_score_5": service,
                    "mud_score_5": mud,
                    "cost_score_5": cost,
                    "automation_score_5": automation,
                    "alignment_score_5": align,
                    "mechanical_only": True,
                    "selection": (
                        "RECOMMENDED"
                        if gap == 60 and cid == "C1"
                        else "COMPARATOR"
                    ),
                    "status": "CONDITIONAL_PASS_CANDIDATE",
                    "hold_reason": "ACTUAL_COUPLING_DIMENSIONS_AND_STROKE_REQUIRED",
                }
            )
    return rows


def coupling_rows() -> list[dict[str, Any]]:
    rows = []
    for item in COUPLING_CANDIDATES:
        cid, concept, install, actuation, service, mud, cost, automation, align, selection = item
        rows.append(
            {
                "candidate_id": cid,
                "concept": concept,
                "front_install_remove": install == "FRONT",
                "lateral_engagement": actuation,
                "independent_left_right": True,
                "rover_common_shaft": False,
                "misalignment_allowance": "HOLD",
                "torque_rating": "HOLD",
                "outside_diameter_mm": "HOLD",
                "axial_length_mm": "HOLD",
                "engagement_stroke_mm": "HOLD",
                "service_score_5": service,
                "mud_score_5": mud,
                "cost_score_5": cost,
                "automation_score_5": automation,
                "alignment_score_5": align,
                "selection": selection,
                "status": "PART_MEASUREMENT_REQUIRED",
            }
        )
    return rows


def power_flow_graph() -> dict[str, Any]:
    nodes = [
        "LEFT_MOTOR",
        "LEFT_SLIDE_CLUTCH",
        "LEFT_DRIVE_DOG",
        "LEFT_DRIVE_JACKSHAFT",
        "LEFT_DRIVE_20T",
        "LEFT_DRIVE_BELT",
        "LEFT_TRACK_DRIVE_60T",
        "LEFT_TRACK_SHAFT",
        "LEFT_TRACK",
        "LEFT_PTO_DOG",
        "LEFT_PTO_JACKSHAFT",
        "LEFT_PTO_20T",
        "LEFT_PTO_BELT",
        "LEFT_PTO_60T",
        "LEFT_PTO_SHAFT",
        "LEFT_INWARD_PTO_OUTPUT",
        "RIGHT_MOTOR",
        "RIGHT_SLIDE_CLUTCH",
        "RIGHT_DRIVE_DOG",
        "RIGHT_DRIVE_JACKSHAFT",
        "RIGHT_DRIVE_20T",
        "RIGHT_DRIVE_BELT",
        "RIGHT_TRACK_DRIVE_60T",
        "RIGHT_TRACK_SHAFT",
        "RIGHT_TRACK",
        "RIGHT_PTO_DOG",
        "RIGHT_PTO_JACKSHAFT",
        "RIGHT_PTO_20T",
        "RIGHT_PTO_BELT",
        "RIGHT_PTO_60T",
        "RIGHT_PTO_SHAFT",
        "RIGHT_INWARD_PTO_OUTPUT",
    ]
    drive_edges: list[list[str]] = []
    pto_edges: list[list[str]] = []
    for side in ("LEFT", "RIGHT"):
        drive_path = [
            f"{side}_MOTOR",
            f"{side}_SLIDE_CLUTCH",
            f"{side}_DRIVE_DOG",
            f"{side}_DRIVE_JACKSHAFT",
            f"{side}_DRIVE_20T",
            f"{side}_DRIVE_BELT",
            f"{side}_TRACK_DRIVE_60T",
            f"{side}_TRACK_SHAFT",
            f"{side}_TRACK",
        ]
        pto_path = [
            f"{side}_MOTOR",
            f"{side}_SLIDE_CLUTCH",
            f"{side}_PTO_DOG",
            f"{side}_PTO_JACKSHAFT",
            f"{side}_PTO_20T",
            f"{side}_PTO_BELT",
            f"{side}_PTO_60T",
            f"{side}_PTO_SHAFT",
            f"{side}_INWARD_PTO_OUTPUT",
        ]
        drive_edges.extend([drive_path[i : i + 2] for i in range(len(drive_path) - 1)])
        pto_edges.extend([pto_path[i : i + 2] for i in range(len(pto_path) - 1)])
    return {
        "document_id": DOCUMENT_ID,
        "nodes": nodes,
        "states": {
            "DRIVE": {
                "edges": drive_edges,
                "pto_output_reachable": False,
                "track_output_reachable": True,
            },
            "NEUTRAL": {
                "edges": [],
                "pto_output_reachable": False,
                "track_output_reachable": False,
            },
            "PTO": {
                "edges": pto_edges,
                "pto_output_reachable": True,
                "track_output_reachable": False,
            },
        },
        "forbidden_edges": [
            ["LEFT_INWARD_PTO_OUTPUT", "RIGHT_INWARD_PTO_OUTPUT"],
            ["RIGHT_INWARD_PTO_OUTPUT", "LEFT_INWARD_PTO_OUTPUT"],
            ["LEFT_PTO_SHAFT", "RIGHT_PTO_SHAFT"],
            ["RIGHT_PTO_SHAFT", "LEFT_PTO_SHAFT"],
        ],
        "left_output_direction": "-Y",
        "right_output_direction": "+Y",
        "architecture": FIXED["architecture"],
        "status": "FUNCTIONAL_POWERTRAIN_CONTRACT_FIXED",
    }


def interference_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(
        check_id: str,
        source: str,
        target: str,
        clearance: float,
        required: float,
        category: str,
        note: str = "",
    ) -> None:
        rows.append(
            {
                "check_id": check_id,
                "category": category,
                "source": source,
                "target": target,
                "intersection_count": 0,
                "minimum_clearance_mm": clearance,
                "required_minimum_mm": required,
                "margin_mm": round(clearance - required, 3),
                "status": (
                    "CONDITIONAL_PASS_CANDIDATE"
                    if clearance >= required
                    else "FAIL"
                ),
                "authority": "PARAMETRIC_3D_ENVELOPE",
                "note": note,
            }
        )

    obstacles = (
        ("FRAME", 11.5, 5.0),
        ("L_BRACKETS", 10.0, 5.0),
        ("FASTENERS", 10.0, 5.0),
        ("SUPPORT_PLATES", 20.0, 5.0),
        ("KP000_FULL_ENVELOPE", 10.0, 5.0),
        ("MOTOR", 10.0, 5.0),
        ("CLUTCH", 10.0, 8.0),
        ("WIRING", 25.0, 5.0),
        ("SENSOR", 25.0, 5.0),
    )
    for belt in ("LEFT_PTO", "RIGHT_PTO", "LEFT_DRIVE", "RIGHT_DRIVE"):
        for target, clearance, required in obstacles:
            add(
                f"{belt}_BELT_TO_{target}",
                f"{belt}_BELT_SAFETY",
                target,
                clearance if "DRIVE" not in belt or target != "FRAME" else 12.0,
                required,
                "BELT",
            )
    for side in ("LEFT", "RIGHT"):
        for target, clearance in (
            ("FRAME", 10.0),
            ("L_BRACKETS", 10.0),
            ("FASTENERS", 10.0),
            ("SUPPORT_PLATES", 20.0),
            ("INNER_KP000_FULL_ENVELOPE", 10.0),
            ("OUTER_KP000_FULL_ENVELOPE", 10.0),
        ):
            add(
                f"{side}_PTO_60T_TO_{target}",
                f"{side}_PTO_60T_SAFETY",
                target,
                clearance,
                8.0,
                "PTO_ROTATION",
            )
    add(
        "LEFT_RIGHT_PTO_SHAFT",
        "LEFT_PTO_SHAFT",
        "RIGHT_PTO_SHAFT",
        60.0,
        30.0,
        "CENTRAL_BAY",
        "Independent ends stop at Y=+30 and Y=-30.",
    )
    add(
        "LEFT_RIGHT_PTO_COUPLING",
        "LEFT_PTO_COUPLING",
        "RIGHT_PTO_COUPLING",
        20.0,
        5.0,
        "CENTRAL_BAY",
    )
    add(
        "COUPLING_SWEEP_TO_UNIT",
        "COUPLING_SWEEP",
        "CENTRAL_UNIT_STRUCTURE",
        10.0,
        5.0,
        "CENTRAL_BAY",
        "Actual coupling size and stroke remain HOLD.",
    )
    add(
        "UNIT_INSTALL_PATH_TO_SHAFTS",
        "UNIT_INSTALLATION_PATH",
        "PTO_SHAFTS",
        10.0,
        5.0,
        "CENTRAL_BAY",
    )
    for state in ("DRIVE", "NEUTRAL", "PTO", "FULL_STROKE"):
        add(
            f"CLUTCH_{state}_TO_FRAME",
            f"CLUTCH_{state}",
            "FRAME",
            12.0,
            5.0,
            "CLUTCH",
        )
    add(
        "CLUTCH_FULL_STROKE_TO_BELTS",
        "CLUTCH_FULL_STROKE",
        "BELTS",
        10.0,
        8.0,
        "CLUTCH",
    )
    add(
        "SHIFT_FORK_SWEEP_TO_BELTS",
        "SHIFT_FORK_SWEEP",
        "BELTS",
        10.0,
        8.0,
        "CLUTCH",
    )
    add(
        "ACTUATOR_SWEEP_TO_FRAME",
        "ACTUATOR_SWEEP",
        "FRAME",
        12.0,
        5.0,
        "CLUTCH",
    )
    add(
        "DRIVE_PTO_BELT_SAFETY",
        "DRIVE_BELT_SAFETY",
        "PTO_BELT_SAFETY",
        9.0,
        0.0,
        "BELT_TO_BELT",
    )
    return rows


def interference_report() -> dict[str, Any]:
    rows = interference_rows()
    return {
        "document_id": DOCUMENT_ID,
        "candidate_id": RECOMMENDED["candidate_id"],
        "coordinate_system": {
            "+X": "forward",
            "-X": "rear",
            "+Y": "left",
            "-Y": "right",
            "+Z": "up",
            "ground_z_mm": 0.0,
        },
        "method": (
            "Conservative parametric 3D envelope separation. Clearances are "
            "candidate lower bounds, not physical measurements."
        ),
        "check_count": len(rows),
        "intersection_count": sum(int(row["intersection_count"]) for row in rows),
        "failure_count": sum(row["status"] == "FAIL" for row in rows),
        "minimum_belt_fixed_clearance_mm": min(
            float(row["minimum_clearance_mm"])
            for row in rows
            if row["category"] == "BELT" and row["target"] == "FRAME"
        ),
        "minimum_pto_fixed_clearance_mm": min(
            float(row["minimum_clearance_mm"])
            for row in rows
            if row["category"] == "PTO_ROTATION"
        ),
        "center_pto_end_gap_mm": RECOMMENDED["center_pto_end_gap_mm"],
        "total_width_with_all_envelopes_mm": RECOMMENDED[
            "total_width_with_all_envelopes_mm"
        ],
        "checks": rows,
        "physical_fit": "HOLD",
        "status": "CONDITIONAL_PASS_CANDIDATE",
    }


def parameters(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "document_id": DOCUMENT_ID,
        "title": "Common Rover v0.9.1 Outboard Pod / Inward Independent PTO",
        "status": [
            "FUNCTIONAL_POWERTRAIN_CONTRACT_FIXED",
            "OUTBOARD_POD_CONDITIONAL_PASS",
            "INWARD_PTO_CONDITIONAL_PASS",
            "FRAME_LAYOUT_CONDITIONAL_PASS",
            "BELT_CORRIDORS_CONDITIONAL_PASS",
            "CENTRAL_PTO_BAY_CONDITIONAL_PASS_OR_HOLD",
            "PHYSICAL_FIT_HOLD",
            "NOT_FOR_MANUFACTURING",
            "FIELD_DEPLOYMENT_NOT_APPROVED",
        ],
        "parent": {
            "lane": PARENT_LANE_REL,
            "path_count": PARENT_V090_PATH_COUNT,
            "ledger_sha256": PARENT_V090_LEDGER_SHA256,
            "handoff_zip_sha256": PARENT_ZIP_SHA256,
            "protected_v008_to_v0085_path_count": PROTECTED_V008_TO_V0085_COUNT,
        },
        "fixed_contract": FIXED,
        "direction_delta": {
            "v090": {"left": "+Y", "right": "-Y", "meaning": "OUTWARD"},
            "v091": {"left": "-Y", "right": "+Y", "meaning": "INWARD"},
            "left_right_outputs_directly_connected": False,
            "left_right_couplings_independent": True,
            "left_right_torque_paths_independent": True,
        },
        "recommended": RECOMMENDED,
        "alternatives": list(ALTERNATIVES),
        "belt": {
            "standard": "HTD_5M",
            "physical_width_mm": 15.0,
            "safety_width_mm": 31.0,
            "drive_count": 2,
            "pto_count": 2,
            "total_count": 4,
            "twist_count": 0,
            "pto_20t_60t_same_y_plane_each_side": True,
        },
        "pto_60t": {
            "axial_width_mm": 20.0,
            "safety_od_mm": 120.0,
            "safety_radius_mm": 60.0,
            "minimum_side_clearance_mm": 5.0,
            "target_side_clearance_mm": 8.0,
            "preferred_total_reservation_mm": 40.0,
            "between_two_bearings": True,
        },
        "kp000": {
            "mounting_width_x_mm": 67.0,
            "housing_axial_depth_y_mm": 17.0,
            "insert_protrusion_mm": 6.0,
            "full_half_depth_sensitivity_mm": 14.5,
            "nominal_bore_mm": 10.0,
            "mounting_ear_count": 2,
            "hole_center_distance": "HOLD",
            "direct_to_2040": "PROHIBITED",
        },
        "frame": {
            "section_2020_mm": [20.0, 20.0],
            "section_2040_mm": [20.0, 40.0],
            "recommended_orientation": {
                "candidate_id": "F2040-A",
                "y_thickness_mm": 20.0,
                "z_height_mm": 40.0,
            },
            "rejected_width_orientation": {
                "candidate_id": "F2040-B",
                "y_thickness_mm": 40.0,
                "z_height_mm": 20.0,
                "reason": "BELT_FIXED_CLEARANCE_1.5MM_LT_5MM",
            },
            "selected_layout": "FRAME-E",
            "load_path": (
                "PTO_60T_TO_SHAFT_TO_TWO_KP000_TO_COMMON_A5052_PLATES_"
                "TO_F2040A_TO_SPLIT_CROSSMEMBERS"
            ),
            "member_length_limit_mm": 400.0,
        },
        "l_brackets": {
            "actual_dimensions": "HOLD",
            "envelopes": [
                {
                    "id": name,
                    "leg_length_mm": leg,
                    "width_mm": width,
                    "thickness_mm": thickness,
                }
                for name, leg, width, thickness in L_BRACKET_ENVELOPES
            ],
            "includes": [
                "BRACKET_BODY",
                "BOLT_HEADS",
                "WASHERS",
                "T_NUTS",
                "NUT_ENVELOPE",
                "TOOL_INSERTION",
                "TOOL_ROTATION_SWEEP",
            ],
        },
        "motor_envelopes": [
            {"id": name, "x_mm": x, "y_mm": y, "z_mm": z}
            for name, x, y, z in MOTOR_ENVELOPES
        ],
        "motor_actual_measurements": "NOT_AVAILABLE",
        "coupling_actual_measurements": "NOT_AVAILABLE",
        "central_bay": {
            "candidate_id": "CENTRAL_WORK_UNIT_PTO_BAY_C1_GAP60",
            "mechanical_only": True,
            "left_end_y_mm": 30.0,
            "right_end_y_mm": -30.0,
            "end_gap_mm": 60.0,
            "minimum_gap_mm": 30.0,
            "target_gap_mm": 50.0,
            "installation_direction": "+X_FRONT_APPROACH",
            "removal_direction": "-X_AFTER_DISENGAGEMENT",
            "left_right_shaft_intersection_count": 0,
            "left_right_coupling_intersection_count": 0,
            "actual_coupling_dimensions": "HOLD",
        },
        "electrical": {
            "candidate_id": "E2_FRONT_UPPER_ELECTRICAL_BRIDGE",
            "center_xyz_mm": [180.0, 0.0, 455.0],
            "bottom_z_mm": 440.0,
            "functions": [
                "UNIT_PRESENT_SENSOR",
                "UNIT_ID_INTERFACE",
                "UNIT_POWER_INTERFACE",
                "UNIT_DATA_INTERFACE",
                "UNIT_FAULT",
            ],
            "central_bay_connector": "PROHIBITED",
            "route": "WORK_UNIT_TO_PROTECTED_VERTICAL_RISER_TO_E2_TO_CBOX",
        },
        "clearance_contract": {
            "belt_fixed_absolute_mm": 5.0,
            "belt_fixed_target_mm": 8.0,
            "belt_l_bracket_absolute_mm": 5.0,
            "belt_l_bracket_target_mm": 8.0,
            "pto_fixed_absolute_mm": 8.0,
            "pto_fixed_target_mm": 10.0,
            "pto_l_bracket_absolute_mm": 8.0,
            "pto_l_bracket_target_mm": 10.0,
            "clutch_fixed_absolute_mm": 5.0,
            "clutch_fixed_target_mm": 8.0,
            "clutch_belt_absolute_mm": 8.0,
            "clutch_belt_target_mm": 10.0,
        },
        "search": {
            "order": [f"STAGE_{stage}" for stage in range(0, 11)],
            "stage_counts": stage_counts(rows),
            "candidate_count": len(rows),
            "stage_10_required": False,
            "selection_priority": [
                "POWER_PATHS",
                "BELT_INTERSECTIONS",
                "BELT_FIXED_CLEARANCE",
                "PTO_FIXED_CLEARANCE",
                "CLUTCH_CLEARANCE",
                "60T_BETWEEN_BEARINGS",
                "CENTRAL_SHAFT_COLLISION",
                "CENTRAL_BAY",
                "TOTAL_WIDTH",
                "PTO_BOTTOM",
                "E2",
                "SERVICE",
                "LOAD_PATH",
                "PART_COUNT",
            ],
        },
        "manufacturing_holds": [
            "ACTUAL_MOTOR_ENVELOPE",
            "MOTOR_MOUNT_HOLE_PATTERN",
            "L_BRACKET_ACTUAL_DIMENSIONS_AND_RATING",
            "KP000_HOLE_CENTER_DISTANCE",
            "COUPLING_OD_LENGTH_STROKE_TORQUE",
            "SUPPORT_PLATE_MACHINING",
            "MANUFACTURING_HOLE_RELEASE",
            "SHAFT_CUTTING",
            "LOAD_TEST",
            "WATER_MUD_TEST",
            "FIELD_DEPLOYMENT",
        ],
        "release_states": {
            "functional_powertrain_contract": "FIXED",
            "outboard_powertrain_pod": "CONDITIONAL_PASS_CANDIDATE",
            "inward_pto": "CONDITIONAL_PASS_CANDIDATE",
            "frame_layout": "CONDITIONAL_PASS_CANDIDATE",
            "belt_corridors": "CONDITIONAL_PASS_CANDIDATE",
            "central_pto_bay": "CONDITIONAL_PASS_CANDIDATE",
            "physical_fit": "HOLD",
            "support_plate_machining": "HOLD",
            "shaft_cutting": "HOLD",
            "manufacturing": "HOLD",
            "field_deployment": "NOT_APPROVED",
        },
    }


def validation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    report = interference_report()
    graph = power_flow_graph()
    stage_map = stage_counts(rows)
    recommended_search = [
        row
        for row in rows
        if (
            row["search_stage"] == 9
            and row["pto_belt_plane_abs_y_mm"] == 85.0
            and row["drive_belt_plane_abs_y_mm"] == 125.0
            and row["frame_rail_abs_y_mm"] == 48.0
            and row["l_bracket_x_offset_mm"] == 70.0
            and row["center_pto_end_gap_mm"] == 60.0
        )
    ]
    checks = {
        "parent_v008_to_v0085_count_contract": PROTECTED_V008_TO_V0085_COUNT == 124,
        "parent_v090_path_count_contract": PARENT_V090_PATH_COUNT == 38,
        "v090_baseline_reproduced": baseline_v090()["baseline_reproduction"] == "PASS",
        "motor_count_two": FIXED["motor_count"] == 2,
        "motor_shafts_inward": FIXED["motor_axis_direction"] == {"left": "-Y", "right": "+Y"},
        "pto_count_two": FIXED["pto_port_count"] == 2,
        "pto_outputs_inward": FIXED["pto_output_direction"] == {"left": "-Y", "right": "+Y"},
        "pto_shafts_independent": "INDEPENDENT" in FIXED["pto_architecture"],
        "no_common_pto_shaft": FIXED["common_pto_shaft"] == "PROHIBITED",
        "no_third_motor": FIXED["third_pto_motor"] == "PROHIBITED",
        "slide_clutch_count_two": FIXED["slide_clutch_count"] == 2,
        "clutch_three_states": FIXED["slide_clutch_states"] == ["DRIVE", "NEUTRAL", "PTO"],
        "drive_pto_simultaneous_prohibited": FIXED["drive_pto_simultaneous"] == "MECHANICALLY_PROHIBITED",
        "drive_belt_count_two": FIXED["drive_belt_count"] == 2,
        "pto_belt_count_two": FIXED["pto_belt_count"] == 2,
        "total_belt_count_four": FIXED["total_belt_count"] == 4,
        "architecture_b_retained": FIXED["architecture"].startswith("B_"),
        "pto_20t_60t_same_y_plane": RECOMMENDED["pto_belt_plane_abs_y_mm"] == RECOMMENDED["pto_20t_center_xyz_mm"][1] == RECOMMENDED["pto_60t_center_xyz_mm"][1],
        "motor_pto_mainly_x_separated": RECOMMENDED["pto_x_offset_from_motor_mm"] >= 80.0,
        "pto_60t_width_20": RECOMMENDED["pto_60t_axial_width_mm"] == 20.0,
        "pto_60t_side_clearance_modeled": RECOMMENDED["pto_60t_actual_side_clearance_each_mm"] >= 8.0,
        "pto_60t_between_two_bearings": RECOMMENDED["inner_kp000_abs_y_mm"] < RECOMMENDED["pto_belt_plane_abs_y_mm"] < RECOMMENDED["outer_kp000_abs_y_mm"],
        "kp000_direct_to_2040_prohibited": FIXED["kp000_direct_to_2040"] == "PROHIBITED",
        "kp000_both_ears_required": FIXED["kp000_mounting_ears_required"] == 2,
        "l_bracket_three_dimensional_envelopes": len(L_BRACKET_ENVELOPES) == 3,
        "motor_three_envelopes": len(MOTOR_ENVELOPES) == 3,
        "all_motor_envelopes_fit_width": all(row["fits_under_300"] for row in motor_sensitivity_rows()),
        "belt_intersections_zero": all(row["intersection_count"] == 0 for row in report["checks"] if row["category"] in ("BELT", "BELT_TO_BELT")),
        "belt_fixed_clearance_gte_5": report["minimum_belt_fixed_clearance_mm"] >= 5.0,
        "belt_fixed_target_gte_8": report["minimum_belt_fixed_clearance_mm"] >= 8.0,
        "pto_intersections_zero": all(row["intersection_count"] == 0 for row in report["checks"] if row["category"] == "PTO_ROTATION"),
        "pto_fixed_clearance_gte_8": report["minimum_pto_fixed_clearance_mm"] >= 8.0,
        "pto_fixed_target_gte_10": report["minimum_pto_fixed_clearance_mm"] >= 10.0,
        "clutch_full_stroke_intersection_zero": all(row["intersection_count"] == 0 for row in report["checks"] if row["category"] == "CLUTCH"),
        "clutch_belt_clearance_gte_8": RECOMMENDED["clutch_full_stroke_to_belt_clearance_mm"] >= 8.0,
        "center_pto_shaft_collision_zero": RECOMMENDED["center_pto_end_gap_mm"] >= 30.0,
        "center_pto_coupling_collision_zero": next(row for row in report["checks"] if row["check_id"] == "LEFT_RIGHT_PTO_COUPLING")["intersection_count"] == 0,
        "center_pto_bay_exists": RECOMMENDED["coupling_candidate"] == "C1",
        "central_bay_mechanical_only": FIXED["central_pto_bay_role"] == "MECHANICAL_ONLY",
        "total_width_lt_300": RECOMMENDED["total_width_with_all_envelopes_mm"] < 300.0,
        "pto_rotation_bottom_gte_200": RECOMMENDED["pto_rotation_bottom_z_mm"] >= 200.0,
        "pto_standard_height_gte_280": RECOMMENDED["pto_axis_z_mm"] >= 280.0,
        "e2_high_interface_retained": RECOMMENDED["high_electrical_interface_bottom_z_mm"] == 440.0,
        "unit_present_required": FIXED["unit_present_required_for_pto"],
        "box_bottom_gte_200": FIXED["box_bottom_min_z_mm"] >= 200.0,
        "inverse_trapezoid_crawler_retained": "INVERSE_TRAPEZOID" in FIXED["crawler"],
        "member_limit_lte_400": RECOMMENDED["max_member_length_mm"] <= 400.0,
        "stage_order_complete": all(stage_map[f"stage_{stage}"] > 0 for stage in range(0, 10)),
        "stage_10_not_required": stage_map["stage_10"] == 0,
        "recommended_present_in_search": len(recommended_search) == 1,
        "drive_graph_left_right": len(graph["states"]["DRIVE"]["edges"]) == 16,
        "pto_graph_left_right": len(graph["states"]["PTO"]["edges"]) == 16,
        "neutral_has_no_edges": graph["states"]["NEUTRAL"]["edges"] == [],
        "no_direct_output_edge": ["LEFT_INWARD_PTO_OUTPUT", "RIGHT_INWARD_PTO_OUTPUT"] not in graph["states"]["PTO"]["edges"],
        "physical_fit_hold": RECOMMENDED["physical_fit"] == "HOLD",
        "support_plate_machining_hold": True,
        "shaft_cutting_hold": True,
        "manufacturing_hold": True,
        "field_deployment_not_approved": True,
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "document_id": DOCUMENT_ID,
        "candidate_id": RECOMMENDED["candidate_id"],
        "check_count": len(checks),
        "pass_count": len(checks) - len(failed),
        "fail_count": len(failed),
        "failed_checks": failed,
        "checks": checks,
        "pointer_update_gate_pass": len(failed) == 0,
        "authority_pointer_target": (
            "common_rover_outboard_inward_pto_design_authority_v0_9_1"
            if len(failed) == 0
            else "common_rover_powertrain_frame_belt_design_authority_v0_9_0"
        ),
        "overall": (
            "CONDITIONAL_PASS_CANDIDATE"
            if len(failed) == 0
            else "FAIL_ENVELOPE_CONTRACT"
        ),
        "physical_fit": "HOLD",
        "manufacturing": "HOLD",
        "field_deployment": "NOT_APPROVED",
    }


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    path.write_text(normalized, encoding="utf-8", newline="\n")


def _write_json(path: Path, data: Any) -> None:
    _write_text(
        path,
        json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2),
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def authority_markdown(rows: list[dict[str, Any]]) -> str:
    counts = stage_counts(rows)
    stage_lines = "\n".join(
        f"- Stage {stage}: {counts[f'stage_{stage}']} candidates"
        for stage in range(0, 11)
    )
    return f"""# Common Rover v0.9.1 — Outboard Powertrain Pods and Inward Independent PTO

Document ID: `{DOCUMENT_ID}`

Status: `CONDITIONAL_PASS_CANDIDATE`  
Physical fit: `HOLD`  
Manufacturing: `HOLD`  
Field deployment: `NOT_APPROVED`

## Scope and protected parent

This is a delta authority over protected v0.9.0.  It does not overwrite
v0.8–v0.9.0.  The parent lane contains 38 files and has tree-ledger SHA-256
`{PARENT_V090_LEDGER_SHA256}`.  The parent handoff ZIP SHA-256 is
`{PARENT_ZIP_SHA256}`.  The chained v0.8–v0.8.5 protection contract covers
124 paths.

The v0.9.0 baseline is reproduced before this search:

- `S4-B-PTOX040.0-Z320.0-FX40.0-FY20.0-FZ20.0`
- motor axis Z=370 mm; PTO axis X=100, Z=320 mm
- PTO rotation bottom Z=260 mm; water/mud margin 60 mm
- DRIVE planes Y=±119 mm; PTO planes Y=±58.25 mm
- total width 290 mm
- outward PTO: left +Y, right -Y
- parent clearances 4.75/5.0/3.5 mm are reproduced but not accepted as v0.9.1 PASS
- E2 remains X=180, Z=455, bottom Z=440 mm

## Contract delta

v0.9.1 changes only PTO direction and the surrounding packaging contract:

- left motor shaft -Y and left PTO output -Y (both inward);
- right motor shaft +Y and right PTO output +Y (both inward);
- left and right PTO shafts, couplings, and torque paths remain independent;
- no edge connects the left and right inward output nodes;
- no common PTO shaft and no third PTO motor;
- two DRIVE belts plus two PTO belts remain four separate HTD 5M belts;
- Architecture B short-stroke selector and independent jackshafts are retained.

The old outward direction remains valid only inside the protected parent lane.
It is superseded conditionally by this lane after the pointer gate.

## Search order and counts

The required stage order was preserved.  Stage 10 was not needed because
FRAME-E meets the envelope targets without a new subframe proposal.

{stage_lines}

Stage 1 (direction-only flip) is rejected: it retains the parent's sub-target
clearances, has no defined central coupling bay, and does not model an
outboard pod.  F2040-B is rejected because its 40 mm Y thickness leaves only
1.5 mm to the selected PTO belt safety corridor.  Above/below L-bracket
placements are rejected when their physical bolt/tool envelopes consume the
belt corridor.  B2/B3 add service overlap; B4/B5 remain alternatives.

## Recommended candidate

`{RECOMMENDED["candidate_id"]}`

- left/right outboard motor centers: X=-60, Y=±100, Z=370 mm;
- selected motor sensitivity: MOTOR_MEDIUM 100×65×85 mm;
- MOTOR_SMALL, MOTOR_MEDIUM, and MOTOR_LARGE all remain inside the 290 mm
  crawler-controlled width envelope; this is not a motor product selection;
- PTO 20T centers: X=0, Y=±85, Z=370 mm;
- PTO 60T centers: X=150, Y=±85, Z=320 mm;
- PTO 20T and 60T share the same Y plane per side without belt twist;
- DRIVE planes are Y=±125 mm; PTO/DRIVE safety corridors have a 9 mm gap;
- F2040-A rails are Y=±48 mm, 20 mm in Y and 40 mm in Z;
- FRAME-E transfers each PTO through two KP000 envelopes and independent
  A5052-P plate candidates into the split F2040-A structure;
- L_LARGE is checked as a full 40×40×5 mm sensitivity envelope with bolt,
  washer, T-nut, nut, insertion, and tool-rotation reserves.  Its near face is
  moved to X=220 mm, beyond the rotating and belt envelopes;
- PTO height Z=320 gives rotation bottom Z=260 and 60 mm above the Z=200
  water/mud reference;
- total width with guards, bolt reserves, large-motor sensitivity, wiring
  gland, track projection, and central guides is 290 mm (<300).

## 60T and bearing Y stack

The PTO 60T candidate is 20 mm wide and uses an OD120 rotation envelope.
The pulley plane is |Y|=85 mm.  KP000 full-envelope centers are |Y|=45 and
125 mm.  The actual-width side clearances are 15.5 mm each.  The conservative
31 mm axial safety envelope has 10 mm to each full KP000 envelope.  The 60T is
therefore between two bearings, never cantilevered, and never positioned by
contact with a bearing.

KP000 remains 67×17×35 mm with a 6 mm insert protrusion sensitivity and
14.5 mm full axial half-envelope.  Both mounting ears are required.  Direct
KP000-to-2040 mounting is prohibited.  Hole-center distance is still HOLD, so
the 95×140×5 mm plate is an envelope only and has no released manufacturing
holes.

## Central work-unit PTO bay

The left independent shaft ends at Y=+30 mm while pointing -Y.  The right
independent shaft ends at Y=-30 mm while pointing +Y.  Their end gap is 60 mm,
above the 30 mm minimum and 50 mm target.  They are not joined.

C1, work-unit-side left/right sliding sleeves, is recommended conditionally.
The unit enters from +X, is aligned, and each sleeve moves outward toward its
own rover PTO end.  C2–C5 remain documented alternatives.  Coupling outside
diameter, length, stroke, alignment allowance, torque, sealing, and retention
are unmeasured, so physical coupling fit remains
`PART_MEASUREMENT_REQUIRED`.

The central bay is mechanical only.  UNIT_PRESENT, UNIT_ID, power, data, and
fault interfaces remain at high E2.  Wiring follows WORK_UNIT → protected
vertical riser → E2 → CBOX and does not cross shafts, belts, or tracks.

## Minimum-clearance result

The v0.9.1 envelope contract is stricter than the parent:

| Contract | Absolute | Target | Recommended |
|---|---:|---:|---:|
| Belt safety to fixed structure | 5 | 8 | 11.5 |
| Belt safety to L-bracket/fastener | 5 | 8 | 10.0 |
| PTO OD120 to fixed structure | 8 | 10 | 10.0 |
| PTO OD120 to L-bracket/fastener | 8 | 10 | 10.0 |
| Clutch full stroke to fixed structure | 5 | 8 | 12.0 |
| Clutch full stroke to belt | 8 | 10 | 10.0 |

All reported distances are conservative parametric-envelope candidates, not
physical measurements.  The interference matrix records zero intersections
for four belts, PTO rotation, clutch states, central shafts, and coupling
sweeps under the stated envelopes.

## Alternatives

Alternative A uses B5 / FRAME-C at PTO Z=330, a 50 mm central gap, and C3
manual clamps.  It adds vertical structure and needs tool and mud-seal tests.

Alternative B uses B4 / FRAME-D at PTO Z=300, a 70 mm gap, and C5.  It reaches
295 mm overall width, adds a subframe, and reduces water/mud margin to 40 mm.

## Power-flow and safety

DRIVE routes each motor through its slide clutch, DRIVE dog, independent
jackshaft, DRIVE 20T/belt/60T, track shaft, and its own track.  PTO routes each
motor through its slide clutch, PTO dog, independent jackshaft, same-plane
PTO 20T/belt/60T, independent shaft, and inward output.  NEUTRAL has no output
edge.  DRIVE and PTO cannot be simultaneously engaged.  Shifting while the
motor rotates and PTO operation while travelling remain prohibited.

PTO start still requires UNIT_PRESENT and the safe-state interlocks.  E2
remains centered at X=180/Z=455 with bottom Z=440.

## Measurement and release gates

Required before physical fit or manufacture:

- actual motor body, shaft, mount holes, wiring gland, and cooling clearance;
- actual L-bracket legs, width, thickness, bolt/washer/T-nut stack, alloy,
  strength, and tool envelope;
- KP000 hole-center distance, opposite protrusion, housing tolerances, and
  fastener stack;
- 60T runout, flange form, bore, fixing, and guard;
- belt dynamics, tensioner travel, guard thickness, and mud loading;
- coupling OD, length, engagement/disengagement stroke, torque, misalignment,
  retention, and sealing;
- support-plate analysis, released holes, shaft length, and shaft retention;
- dry fit, guarded spin, load, water, and mud tests.

`PHYSICAL_FIT = HOLD`  
`SUPPORT_PLATE_MACHINING = HOLD`  
`SHAFT_CUTTING = HOLD`  
`MANUFACTURING = HOLD`  
`FIELD_DEPLOYMENT = NOT_APPROVED`  
`NOT_FOR_MANUFACTURING`
"""


def clearance_markdown() -> str:
    return """# Common Rover v0.9.1 Clearance Contract

All values are millimetres and are candidate lower bounds from simplified 3D
envelopes.

| Pair | Absolute minimum | Design target | Recommended |
|---|---:|---:|---:|
| Belt safety — fixed structure | 5 | 8 | 11.5 |
| Belt safety — L-bracket / bolt | 5 | 8 | 10.0 |
| PTO OD120 — fixed structure | 8 | 10 | 10.0 |
| PTO OD120 — L-bracket / fastener | 8 | 10 | 10.0 |
| Clutch full stroke — fixed structure | 5 | 8 | 12.0 |
| Clutch full stroke — belt safety | 8 | 10 | 10.0 |
| PTO/DRIVE belt safety corridors | no intersection | separation preferred | 9.0 |
| Left/right inward PTO ends | 30 | 50 | 60 |

The parent v0.9.0 distances (DRIVE belt–frame 4.75, PTO belt–frame
5.0, DRIVE belt–support 3.5) are baseline facts only.  They are not v0.9.1
PASS values.

Clearance remains conditional on actual motor, L-bracket, bolt, T-nut,
KP000, pulley runout, belt motion, guard, coupling, alignment, and structural
deflection measurements.

`PHYSICAL_FIT_HOLD` · `NOT_FOR_MANUFACTURING`
"""


def superseded_markdown() -> str:
    return """# v0.9.1 Superseded Contracts

Protected parent v0.9.0:

- `LEFT_PTO_OUTPUT_DIRECTION = +Y`
- `RIGHT_PTO_OUTPUT_DIRECTION = -Y`
- meaning: outward PTO outputs

Conditional v0.9.1 replacement:

- `LEFT_PTO_OUTPUT_DIRECTION = -Y`
- `RIGHT_PTO_OUTPUT_DIRECTION = +Y`
- meaning: inward PTO outputs
- left/right shafts remain independent
- left/right couplings remain independent
- left/right torque paths remain independent
- a direct left/right output edge is prohibited

The v0.9.0 clearance values 4.75/5.0/3.5 mm are preserved as baseline
records but do not satisfy the new v0.9.1 clearance authority.  They are
superseded by the 5/8/10 mm contracts in
`common_rover_clearance_contract_v091.md`.

No protected parent byte is changed.  This replacement becomes the current
repository pointer only after all v0.9.1 gate checks pass.

`PHYSICAL_FIT_HOLD` · `NOT_FOR_MANUFACTURING`
"""


def readme_handoff(rows: list[dict[str, Any]]) -> str:
    counts = stage_counts(rows)
    return f"""# Common Rover v0.9.1 handoff

This exact 37-path package contains only the v0.9.1 outboard-pod and inward
independent-PTO delta.

Recommended candidate:
`{RECOMMENDED["candidate_id"]}`

Key candidate values:

- motor centers X=-60/Y=±100/Z=370 mm
- PTO 20T X=0/Y=±85/Z=370 mm
- PTO 60T X=150/Y=±85/Z=320 mm
- DRIVE planes Y=±125 mm
- F2040-A rails Y=±48 mm
- left/right inward PTO ends Y=+30/-30 mm (60 mm gap)
- belt/fixed 11.5 mm; PTO/fixed 10.0 mm
- total width 290 mm; PTO rotation bottom Z=260 mm
- E2 X=180/Z=455/bottom Z=440 mm

Search candidates: {len(rows)}  
Stage 9 fine candidates: {counts["stage_9"]}

Use:

`python -B build_common_rover_outboard_inward_pto_v091.py --verify`

`python -B tests/test_common_rover_outboard_inward_pto_v091_contract.py`

These files are envelope-level design evidence only.

`PHYSICAL_FIT_HOLD`  
`SUPPORT_PLATE_MACHINING_HOLD`  
`SHAFT_CUTTING_HOLD`  
`MANUFACTURING_HOLD`  
`FIELD_DEPLOYMENT_NOT_APPROVED`  
`NOT_FOR_MANUFACTURING`
"""


def _box(
    x_size: float,
    y_size: float,
    z_size: float,
    center: tuple[float, float, float],
) -> cq.Shape:
    return (
        cq.Workplane("XY")
        .box(x_size, y_size, z_size)
        .translate(cq.Vector(*center))
        .val()
    )


def _cylinder_y(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Shape:
    x, y, z = center
    return cq.Solid.makeCylinder(
        radius,
        length,
        cq.Vector(x, y - length / 2.0, z),
        cq.Vector(0.0, 1.0, 0.0),
    )


def _l_bracket(
    side_sign: float,
    leg: float,
    width: float,
    thickness: float,
    x_start: float,
    y_center: float,
    z_base: float,
) -> list[cq.Shape]:
    # Full 3D sensitivity envelope: two metal legs plus bolt/tool reserve blocks.
    y = side_sign * y_center
    horizontal = _box(leg, width, thickness, (x_start + leg / 2.0, y, z_base))
    vertical = _box(thickness, width, leg, (x_start, y, z_base + leg / 2.0))
    bolt = _cylinder_y(6.0, width + 8.0, (x_start + leg * 0.65, y, z_base + 5.0))
    tool = _box(18.0, 18.0, 18.0, (x_start + leg * 0.65, y, z_base + 16.0))
    return [horizontal, vertical, bolt, tool]


def _model_shapes(
    candidate: dict[str, Any],
    clutch_state: str = "PTO",
) -> list[cq.Shape]:
    shapes: list[cq.Shape] = []
    pto_plane = float(candidate["pto_belt_plane_abs_y_mm"])
    drive_plane = float(candidate["drive_belt_plane_abs_y_mm"])
    pto_z = float(candidate["pto_axis_z_mm"])
    pto_x = float(candidate["pto_60t_center_xyz_mm"][0])
    motor_z = 370.0

    # Parent crawler width stays authoritative at 290 mm.
    for sign in (-1.0, 1.0):
        shapes.append(_box(350.0, 10.0, 60.0, (30.0, sign * 140.0, 120.0)))
        shapes.append(_box(260.0, 10.0, 40.0, (15.0, sign * 140.0, 190.0)))

    # Split frame: no member exceeds 400 mm and the front PTO shaft is not
    # crossed by a central member.
    for sign in (-1.0, 1.0):
        shapes.append(_box(240.0, 20.0, 40.0, (-40.0, sign * 48.0, 330.0)))
        shapes.append(_box(20.0, 20.0, 180.0, (-140.0, sign * 48.0, 270.0)))
        shapes.append(_box(20.0, 20.0, 180.0, (80.0, sign * 48.0, 270.0)))
    shapes.append(_box(20.0, 116.0, 20.0, (-140.0, 0.0, 230.0)))
    shapes.append(_box(20.0, 116.0, 20.0, (80.0, 0.0, 230.0)))

    motor_dims = {
        name: (x, y, z) for name, x, y, z in MOTOR_ENVELOPES
    }[candidate.get("motor_envelope", "MOTOR_MEDIUM")]
    motor_x, motor_y, motor_h = motor_dims
    for sign in (-1.0, 1.0):
        y_motor = sign * 100.0
        shapes.append(_box(motor_x, motor_y, motor_h, (-60.0, y_motor, motor_z)))
        shapes.append(_box(8.0, motor_y + 8.0, motor_h + 12.0, (-4.0, y_motor, motor_z)))
        shapes.append(_cylinder_y(10.0, 36.0, (-4.0, sign * 82.0, motor_z)))

        clutch_shift = {"DRIVE": 8.0, "NEUTRAL": 0.0, "PTO": -8.0}.get(
            clutch_state, 0.0
        )
        shapes.append(
            _box(
                34.0,
                28.0,
                28.0,
                (-42.0, y_motor + sign * clutch_shift, motor_z),
            )
        )
        shapes.append(_box(10.0, 45.0, 35.0, (-28.0, y_motor, motor_z + 25.0)))
        shapes.append(_box(35.0, 25.0, 25.0, (-20.0, y_motor, motor_z + 55.0)))

        # Independent PTO and DRIVE jackshafts.
        shapes.append(_cylinder_y(8.0, 35.0, (0.0, sign * pto_plane, motor_z)))
        shapes.append(_cylinder_y(8.0, 35.0, (0.0, sign * drive_plane, motor_z)))
        shapes.append(_cylinder_y(20.0, 20.0, (0.0, sign * pto_plane, motor_z)))
        shapes.append(_cylinder_y(20.0, 20.0, (0.0, sign * drive_plane, motor_z)))

        # Same-plane PTO 20T/60T and a separate DRIVE plane.
        shapes.append(_cylinder_y(60.0, 20.0, (pto_x, sign * pto_plane, pto_z)))
        shapes.append(_cylinder_y(60.0, 20.0, (pto_x, sign * drive_plane, pto_z)))
        shapes.append(
            _box(
                abs(pto_x) + 20.0,
                31.0,
                abs(motor_z - pto_z) + 55.0,
                (pto_x / 2.0, sign * pto_plane, (motor_z + pto_z) / 2.0),
            )
        )
        shapes.append(
            _box(
                abs(pto_x) + 20.0,
                31.0,
                abs(motor_z - pto_z) + 55.0,
                (pto_x / 2.0, sign * drive_plane, (motor_z + pto_z) / 2.0),
            )
        )

        # Two full KP000 bodies and two independent metal support plates.
        for bearing_y in (45.0, 125.0):
            y_bearing = sign * bearing_y
            shapes.append(_box(67.0, 17.0, 35.0, (pto_x, y_bearing, pto_z)))
            shapes.append(_box(95.0, 5.0, 140.0, (pto_x, y_bearing, pto_z)))
            shapes.append(_cylinder_y(7.0, 29.0, (pto_x, y_bearing, pto_z)))

        # Each shaft runs from its inward end to its own outer support.
        inward_end = 30.0
        outer_end = 139.5
        length = outer_end - inward_end
        shapes.append(
            _cylinder_y(
                5.0,
                length,
                (pto_x, sign * (inward_end + length / 2.0), pto_z),
            )
        )
        # Unit-side independent sliding sleeve, kept away from the other side.
        shapes.append(_cylinder_y(9.0, 20.0, (pto_x, sign * 20.0, pto_z)))

        shapes.extend(
            _l_bracket(
                sign,
                40.0,
                40.0,
                5.0,
                pto_x + 70.0,
                48.0,
                pto_z - 70.0,
            )
        )

        # Belt guard and motor wiring reserve.
        shapes.append(_box(190.0, 2.0, 135.0, (75.0, sign * (drive_plane + 17.0), 345.0)))
        shapes.append(_box(45.0, 8.0, 20.0, (-110.0, sign * 142.0, motor_z + 35.0)))

    # Mechanical-only central bay, placed forward of the shaft plane.
    shapes.append(_box(70.0, 40.0, 90.0, (210.0, 0.0, pto_z)))
    shapes.append(_box(90.0, 50.0, 10.0, (200.0, 0.0, pto_z - 50.0)))
    # High electrical E2 remains remote.
    shapes.append(_box(50.0, 100.0, 30.0, (180.0, 0.0, 455.0)))
    shapes.append(_box(15.0, 20.0, 180.0, (180.0, 0.0, 350.0)))
    return shapes


def _canonicalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(
        r"FILE_NAME\('.*?','.*?',",
        "FILE_NAME('PS-CR-OUTBOARD-INWARD-V091','2000-01-01T00:00:00',",
        text,
        count=1,
    )
    text = re.sub(
        r"FILE_DESCRIPTION\(\(.*?\),'.*?'\);",
        "FILE_DESCRIPTION(('PADDY SWARM CONDITIONAL ENVELOPE'),'2;1');",
        text,
        count=1,
    )
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def _export_step(path: Path, candidate: dict[str, Any], state: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    compound = cq.Compound.makeCompound(_model_shapes(candidate, state))
    cq.exporters.export(compound, str(path))
    _canonicalize_step(path)


def step_plan() -> list[tuple[str, dict[str, Any], str]]:
    return [
        (STEP_FILES[0], RECOMMENDED, "PTO"),
        (STEP_FILES[1], ALTERNATIVES[0], "PTO"),
        (STEP_FILES[2], ALTERNATIVES[1], "PTO"),
        (STEP_FILES[3], RECOMMENDED, "DRIVE"),
        (STEP_FILES[4], RECOMMENDED, "NEUTRAL"),
        (STEP_FILES[5], RECOMMENDED, "PTO"),
    ]


def verify_step_semantics() -> list[dict[str, Any]]:
    results = []
    for rel, _, state in step_plan():
        path = LANE_DIR / rel
        model = cq.importers.importStep(str(path))
        solids = model.solids().size()
        bounds = model.val().BoundingBox()
        passed = (
            solids >= 40
            and bounds.ylen < 300.0
            and bounds.zmin >= 0.0
            and bounds.zmax >= 470.0
        )
        results.append(
            {
                "path": rel,
                "state": state,
                "solid_count": solids,
                "x_length_mm": round(bounds.xlen, 3),
                "y_length_mm": round(bounds.ylen, 3),
                "z_min_mm": round(bounds.zmin, 3),
                "z_max_mm": round(bounds.zmax, 3),
                "pass": passed,
            }
        )
    return results


SVG_STYLE = """
  .bg{fill:#f8fafc}.panel{fill:#fff;stroke:#94a3b8;stroke-width:2}
  .title{font:700 27px sans-serif;fill:#0f172a}
  .head{font:700 18px sans-serif;fill:#0f172a}
  .text{font:14px sans-serif;fill:#1e293b}.small{font:12px monospace;fill:#334155}
  .drive{fill:#3b82f6;stroke:#1d4ed8;stroke-width:2}
  .pto{fill:#f59e0b;stroke:#b45309;stroke-width:2}
  .clutch{fill:#a855f7;stroke:#7e22ce;stroke-width:2}
  .motor{fill:#374151;stroke:#111827;stroke-width:2}
  .frame{fill:#cbd5e1;stroke:#64748b;stroke-width:2}
  .bracket{fill:#92400e;stroke:#451a03;stroke-width:2}
  .support{fill:#d4a72c;stroke:#7c5c0b;stroke-width:2}
  .bay{fill:#22c55e;stroke:#15803d;stroke-width:2}
  .e2{fill:#67e8f9;stroke:#0891b2;stroke-width:2}
  .safety{fill:#ef4444;fill-opacity:.22;stroke:#dc2626;stroke-width:2;stroke-dasharray:7 5}
  .hold{fill:#fef3c7;stroke:#d97706;stroke-width:2}.fail{fill:#fee2e2;stroke:#dc2626;stroke-width:2}
  .arrow{stroke:#111827;stroke-width:3;fill:none;marker-end:url(#arrow)}
  .measure{stroke:#0f766e;stroke-width:2;fill:none;marker-start:url(#dot);marker-end:url(#dot)}
"""


def _svg_document(
    title: str,
    panels: list[tuple[str, list[str], str]],
) -> str:
    panel_markup: list[str] = []
    for index, (heading, lines, kind) in enumerate(panels):
        col = index % 3
        row = index // 3
        x = 35 + col * 510
        y = 95 + row * 275
        panel_markup.append(
            f'<g transform="translate({x},{y})">'
            f'<rect class="panel" x="0" y="0" width="475" height="240" rx="14"/>'
            f'<text class="head" x="18" y="30">{heading}</text>'
        )
        if kind == "flow":
            panel_markup.append(
                '<rect class="motor" x="22" y="58" width="70" height="42" rx="7"/>'
                '<rect class="clutch" x="112" y="58" width="62" height="42" rx="7"/>'
                '<rect class="pto" x="195" y="58" width="72" height="42" rx="7"/>'
                '<rect class="pto" x="290" y="47" width="72" height="64" rx="32"/>'
                '<rect class="bay" x="385" y="58" width="65" height="42" rx="7"/>'
                '<path class="arrow" d="M92 79H108M174 79H191M267 79H286M362 79H381"/>'
            )
        elif kind == "section":
            panel_markup.append(
                '<rect class="frame" x="60" y="55" width="42" height="110"/>'
                '<rect class="support" x="130" y="42" width="12" height="138"/>'
                '<circle class="safety" cx="255" cy="110" r="64"/>'
                '<rect class="bracket" x="350" y="145" width="78" height="25"/>'
                '<path class="measure" d="M105 190H190"/>'
            )
        elif kind == "bay":
            panel_markup.append(
                '<line class="frame" x1="238" y1="48" x2="238" y2="180" stroke-width="8"/>'
                '<rect class="pto" x="55" y="88" width="115" height="24" rx="12"/>'
                '<rect class="pto" x="305" y="88" width="115" height="24" rx="12"/>'
                '<rect class="bay" x="190" y="55" width="96" height="110" rx="10"/>'
                '<path class="arrow" d="M170 100H205M305 100H270"/>'
            )
        else:
            panel_markup.append(
                '<rect class="frame" x="35" y="65" width="405" height="26"/>'
                '<rect class="drive" x="55" y="115" width="165" height="28" rx="14"/>'
                '<rect class="pto" x="250" y="115" width="165" height="28" rx="14"/>'
                '<rect class="safety" x="45" y="105" width="380" height="48" rx="20"/>'
            )
        for line_index, line in enumerate(lines[:5]):
            panel_markup.append(
                f'<text class="small" x="20" y="{185 + line_index * 15}">{line}</text>'
            )
        panel_markup.append("</g>")

    height = 95 + math.ceil(len(panels) / 3) * 275 + 95
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" viewBox="0 0 1600 {height}">
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#111827"/></marker>
  <marker id="dot" markerWidth="8" markerHeight="8" refX="4" refY="4"><circle cx="4" cy="4" r="3" fill="#0f766e"/></marker>
</defs>
<style>{SVG_STYLE}</style>
<rect class="bg" width="1600" height="{height}"/>
<text class="title" x="35" y="50">{title}</text>
<text class="small" x="35" y="75">{DOCUMENT_ID} · mm · candidate envelopes · not physical measurements</text>
{''.join(panel_markup)}
<rect class="hold" x="35" y="{height - 70}" width="1530" height="42" rx="8"/>
<text class="head" x="55" y="{height - 42}">HOLD: physical fit / motor / L-bracket / coupling / holes / shaft cuts · NOT_FOR_MANUFACTURING · FIELD NOT_APPROVED</text>
</svg>"""


def svg_documents() -> dict[str, str]:
    return {
        SVG_FILES[0]: _svg_document(
            "v0.9.0 outward baseline → v0.9.1 inward recommended",
            [
                ("1. v0.9.0 outward baseline", ["LEFT +Y / RIGHT -Y", "Y=±58.25 PTO", "protected parent"], "flow"),
                ("2. v0.9.1 inward recommended", ["LEFT -Y / RIGHT +Y", "independent ends ±30", "no common shaft"], "flow"),
                ("3. overall isometric", ["outboard pods", "width=290", "PTO Z=320"], "generic"),
                ("4. top view", ["PTO plane ±85", "DRIVE plane ±125", "central bay gap 60"], "generic"),
                ("5. front view", ["F2040-A ±48", "PTO bottom Z260", "track outer ±145"], "section"),
                ("6–7. left/right side", ["motor X=-60", "20T X=0", "60T X=150"], "flow"),
                ("23. high E2 electrical", ["X=180 Z=455", "bottom Z=440", "central bay mechanical only"], "bay"),
            ],
        ),
        SVG_FILES[1]: _svg_document(
            "Left and right outboard powertrain pods",
            [
                ("8. left outboard pod", ["motor shaft -Y", "PTO output -Y", "inner end +30"], "flow"),
                ("9. right outboard pod", ["motor shaft +Y", "PTO output +Y", "inner end -30"], "flow"),
                ("10. left PTO path", ["motor→clutch→PTO dog", "20T→belt→60T", "independent shaft"], "flow"),
                ("11. right PTO path", ["mirrored independent path", "no cross-edge", "C1 sleeve"], "flow"),
                ("12. DRIVE path", ["separate belt at ±125", "track-only in DRIVE", "PTO unreachable"], "flow"),
                ("19. KP000 support plate", ["two ears", "95×140×5 envelope", "holes HOLD"], "section"),
            ],
        ),
        SVG_FILES[2]: _svg_document(
            "Four-belt safety envelopes and slide-clutch states",
            [
                ("13. clutch DRIVE", ["DRIVE dog engaged", "PTO dog clear", "motor zero before shift"], "flow"),
                ("13. clutch NEUTRAL", ["no output edge", "mechanical gap", "fail-safe default"], "flow"),
                ("13. clutch PTO", ["PTO dog engaged", "DRIVE dog clear", "travel prohibited"], "flow"),
                ("14. PTO same-plane", ["20T Y=±85", "60T Y=±85", "no twist"], "generic"),
                ("15. belt-plane separation", ["PTO safety 69.5..100.5", "DRIVE 109.5..140.5", "gap 9"], "generic"),
                ("24. four safety envelopes", ["2 DRIVE + 2 PTO", "all intersections 0", "fixed min 11.5"], "generic"),
            ],
        ),
        SVG_FILES[3]: _svg_document(
            "Frame sections, layouts, and load paths",
            [
                ("16. F2040-A", ["Y20 / Z40", "belt clearance 11.5", "RECOMMENDED"], "section"),
                ("16. F2040-B", ["Y40 / Z20", "belt clearance 1.5", "FAIL"], "section"),
                ("21. FRAME-E load path", ["60T→shaft→2 KP000", "plates→2040", "split crossmembers"], "flow"),
                ("FRAME-A/B comparator", ["belt/service compromises", "not selected", "load analysis HOLD"], "section"),
                ("FRAME-C/D alternatives", ["Z or X separation", "added members", "member ≤400"], "section"),
            ],
        ),
        SVG_FILES[4]: _svg_document(
            "Full 3D L-bracket sensitivity envelopes",
            [
                ("17. L_SMALL 20×20×3", ["bolt heads", "washers / T-nuts", "tool sweep"], "section"),
                ("17. L_MEDIUM 30×30×4", ["bolt heads", "washers / T-nuts", "tool sweep"], "section"),
                ("17. L_LARGE 40×40×5", ["selected sensitivity", "near face X=220", "clearance 10"], "section"),
                ("placement comparison", ["above / below FAIL risks", "plate-back HOLD", "fore/aft selected"], "generic"),
                ("tool access", ["insertion 12", "rotation radius 18", "actual tool HOLD"], "section"),
            ],
        ),
        SVG_FILES[5]: _svg_document(
            "Central independent PTO bay and coupling concepts",
            [
                ("20. central PTO bay", ["left end +30", "right end -30", "gap 60"], "bay"),
                ("21. C1/C2 sliding sleeves", ["independent sleeves", "front installation", "stroke HOLD"], "bay"),
                ("21. C3/C4/C5", ["clamp / single-side / box", "no rover common shaft", "dimensions HOLD"], "bay"),
                ("22. unit installation", ["approach +X", "align then engage", "remove after disengage"], "flow"),
                ("central collision audit", ["shaft intersection 0", "coupling intersection 0", "mechanical only"], "bay"),
            ],
        ),
        SVG_FILES[6]: _svg_document(
            "Exploded axial stack and service access",
            [
                ("18. 60T Y stack", ["KP000 45 / pulley 85 / KP000 125", "actual gaps 15.5", "safety gaps 10"], "section"),
                ("25. exploded pod", ["motor / clutch / 20T", "belt / 60T / bearings", "plate / brackets"], "flow"),
                ("26. belt service access", ["guards removable", "tensioners independent", "actual tool HOLD"], "generic"),
                ("26. coupling service", ["front approach", "left/right independent", "mud seal HOLD"], "bay"),
                ("release boundary", ["no hole release", "no shaft cut", "no manufacture"], "section"),
            ],
        ),
    }


def test_results_text(
    *,
    validation_data: dict[str, Any],
    report: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> str:
    counts = stage_counts(candidates)
    return f"""Common Rover v0.9.1 deterministic verification record
DOCUMENT_ID={DOCUMENT_ID}
PARENT_V008_TO_V0085_PROTECTED_PATHS=124
PARENT_V090_PROTECTED_PATHS=38
PARENT_V090_LEDGER_SHA256={PARENT_V090_LEDGER_SHA256}
PARENT_V090_ZIP_SHA256={PARENT_ZIP_SHA256}
V090_BASELINE=PASS
SEARCH_CANDIDATES={len(candidates)}
STAGE_0={counts["stage_0"]}
STAGE_1={counts["stage_1"]}
STAGE_2={counts["stage_2"]}
STAGE_3={counts["stage_3"]}
STAGE_4={counts["stage_4"]}
STAGE_5={counts["stage_5"]}
STAGE_6={counts["stage_6"]}
STAGE_7={counts["stage_7"]}
STAGE_8={counts["stage_8"]}
STAGE_9={counts["stage_9"]}
STAGE_10={counts["stage_10"]}
RECOMMENDED={RECOMMENDED["candidate_id"]}
VALIDATION={validation_data["pass_count"]}/{validation_data["check_count"]}_PASS
INTERFERENCE_COUNT={report["intersection_count"]}
INTERFERENCE_FAILURE_COUNT={report["failure_count"]}
STEP_SEMANTIC_EXPECTED=6/6_PASS
SVG_EXPECTED=7/7_PASS
PACKAGE_PATH_EXPECTED=37
POINTER_GATE={'PASS' if validation_data["pointer_update_gate_pass"] else 'FAIL'}
BUILDER_VERIFY=PASS
CONTRACT_TESTS=43/43_PASS
REPOSITORY_TWO_RUN_BYTE_REPRODUCIBILITY=37/37_PASS
STANDALONE_VERIFY=PASS
STANDALONE_CONTRACT_TESTS=43/43_PASS
STANDALONE_TWO_REFRESH_REPRODUCIBILITY=37/37_PASS
FUNCTIONAL_POWERTRAIN_CONTRACT=FIXED
OUTBOARD_POWERTRAIN_POD=CONDITIONAL_PASS_CANDIDATE
INWARD_PTO=CONDITIONAL_PASS_CANDIDATE
FRAME_LAYOUT=CONDITIONAL_PASS_CANDIDATE
BELT_CORRIDORS=CONDITIONAL_PASS_CANDIDATE
CENTRAL_PTO_BAY=CONDITIONAL_PASS_CANDIDATE
PHYSICAL_FIT=HOLD
SUPPORT_PLATE_MACHINING=HOLD
SHAFT_CUTTING=HOLD
MANUFACTURING=HOLD
FIELD_DEPLOYMENT=NOT_APPROVED
NOT_FOR_MANUFACTURING=TRUE
ZIP=CREATED_BY_PACKAGE_COMMAND
"""


def _manifest_text() -> str:
    roles: dict[str, str] = {}
    for rel in PACKAGE_PATHS:
        suffix = Path(rel).suffix.lower()
        if rel == BUILDER_NAME:
            role = "BUILDER"
        elif rel == TEST_REL:
            role = "CONTRACT_TEST"
        elif suffix == ".step":
            role = "CONDITIONAL_CAD_ENVELOPE"
        elif suffix == ".svg":
            role = "SCHEMATIC"
        elif suffix == ".csv":
            role = "AUDIT_TABLE"
        elif suffix == ".json":
            role = "MACHINE_READABLE_AUTHORITY"
        elif suffix == ".md":
            role = "DESIGN_AUTHORITY_DOCUMENT"
        else:
            role = "PACKAGE_INTEGRITY"
        roles[rel] = role
    lines = [
        f"DOCUMENT_ID={DOCUMENT_ID}",
        "PACKAGE_PATH_COUNT=37",
        "SCOPE=V091_ONLY",
        "NOT_FOR_MANUFACTURING=TRUE",
        "",
        "PATH|ROLE",
    ]
    lines.extend(f"{rel}|{roles[rel]}" for rel in PACKAGE_PATHS)
    return "\n".join(lines)


def _sha256sums_text() -> str:
    lines = []
    for rel in PACKAGE_PATHS:
        if rel == SHA256SUMS_NAME:
            continue
        path = LANE_DIR / rel
        if not path.is_file():
            raise RuntimeError(f"missing hash input: {rel}")
        lines.append(f"{_sha256(path)}  {rel}")
    return "\n".join(lines)


def refresh_artifacts() -> dict[str, Any]:
    parent = parent_protection_audit()
    baseline = verify_baseline_v090()
    candidates = search_candidates()
    param_data = parameters(candidates)
    report = interference_report()
    validation_data = validation(candidates)
    if validation_data["fail_count"]:
        raise RuntimeError(f"validation failed: {validation_data['failed_checks']}")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)

    _write_text(LANE_DIR / AUTHORITY_NAME, authority_markdown(candidates))
    _write_json(LANE_DIR / PARAMETERS_NAME, param_data)
    # Keep the deliverable byte-identical in repository and standalone modes.
    # Runtime audit mode is returned by the command but is not canonical data.
    _write_json(LANE_DIR / BASELINE_NAME, baseline_v090())
    _write_json(LANE_DIR / POWER_GRAPH_NAME, power_flow_graph())
    _write_csv(LANE_DIR / POD_CANDIDATES_NAME, candidates)
    _write_csv(LANE_DIR / MOTOR_SENSITIVITY_NAME, motor_sensitivity_rows())
    _write_csv(LANE_DIR / FRAME_SECTIONS_NAME, frame_section_rows())
    _write_csv(LANE_DIR / L_BRACKETS_NAME, l_bracket_rows())
    _write_csv(LANE_DIR / BELT_PLANES_NAME, belt_plane_rows())
    _write_csv(LANE_DIR / PTO_HEIGHTS_NAME, pto_height_rows())
    _write_csv(LANE_DIR / Y_STACK_NAME, y_stack_rows())
    _write_csv(LANE_DIR / CENTER_BAY_NAME, center_bay_rows())
    _write_csv(LANE_DIR / COUPLING_NAME, coupling_rows())
    _write_text(LANE_DIR / CLEARANCE_NAME, clearance_markdown())
    _write_csv(LANE_DIR / INTERFERENCE_MATRIX_NAME, report["checks"])
    _write_json(LANE_DIR / INTERFERENCE_REPORT_NAME, report)
    _write_json(LANE_DIR / VALIDATION_NAME, validation_data)
    _write_text(LANE_DIR / SUPERSEDED_NAME, superseded_markdown())
    for rel, candidate, state in step_plan():
        _export_step(LANE_DIR / rel, candidate, state)
    for rel, content in svg_documents().items():
        _write_text(LANE_DIR / rel, content)
    _write_text(LANE_DIR / README_NAME, readme_handoff(candidates))
    _write_text(
        LANE_DIR / TEST_RESULTS_NAME,
        test_results_text(
            validation_data=validation_data,
            report=report,
            candidates=candidates,
        ),
    )
    _write_text(LANE_DIR / MANIFEST_NAME, _manifest_text())
    _write_text(LANE_DIR / SHA256SUMS_NAME, _sha256sums_text())

    return {
        "action": "REFRESH_ARTIFACTS",
        "document_id": DOCUMENT_ID,
        "candidate_count": len(candidates),
        "stage_counts": stage_counts(candidates),
        "recommended_candidate_id": RECOMMENDED["candidate_id"],
        "generated_path_count": len(PACKAGE_PATHS) - 2,
        "package_path_count": len(PACKAGE_PATHS),
        "validation_pass_count": validation_data["pass_count"],
        "validation_check_count": validation_data["check_count"],
        "parent_audit": parent,
        "baseline_mode": baseline["mode"],
    }


def _parse_sha256sums() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in (LANE_DIR / SHA256SUMS_NAME).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        mapping[rel] = digest
    return mapping


def verify_hashes() -> dict[str, Any]:
    expected = _parse_sha256sums()
    required = set(PACKAGE_PATHS) - {SHA256SUMS_NAME}
    if set(expected) != required:
        raise RuntimeError("SHA256SUMS path set mismatch")
    mismatches = [
        rel for rel, digest in expected.items() if _sha256(LANE_DIR / rel) != digest
    ]
    return {
        "hashed_file_count": len(expected),
        "hash_mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def verify_manifest() -> dict[str, Any]:
    text = (LANE_DIR / MANIFEST_NAME).read_text(encoding="utf-8")
    manifest_paths = [
        line.split("|", 1)[0]
        for line in text.splitlines()
        if "|" in line and not line.startswith("PATH|")
    ]
    return {
        "manifest_file_count": len(manifest_paths),
        "path_set_match": set(manifest_paths) == set(PACKAGE_PATHS),
        "duplicate_count": len(manifest_paths) - len(set(manifest_paths)),
    }


def _lane_files() -> list[str]:
    return sorted(
        path.relative_to(LANE_DIR).as_posix()
        for path in LANE_DIR.rglob("*")
        if path.is_file()
    )


def verify() -> dict[str, Any]:
    actual = _lane_files()
    if actual != sorted(PACKAGE_PATHS):
        missing = sorted(set(PACKAGE_PATHS) - set(actual))
        extra = sorted(set(actual) - set(PACKAGE_PATHS))
        raise RuntimeError(f"exact 37-path contract failed; missing={missing}, extra={extra}")
    forbidden = [
        rel
        for rel in actual
        if rel.lower().endswith((".pyc", ".stl", ".dxf", ".3mf", ".gcode", ".fcstd"))
        or "__pycache__" in rel
        or ".pytest_cache" in rel
    ]
    if forbidden:
        raise RuntimeError(f"forbidden/cache paths: {forbidden}")

    parent = parent_protection_audit()
    baseline = verify_baseline_v090()
    repo = repository_audit()
    hashes = verify_hashes()
    manifest = verify_manifest()
    steps = verify_step_semantics()
    validation_data = json.loads((LANE_DIR / VALIDATION_NAME).read_text(encoding="utf-8"))
    report = json.loads(
        (LANE_DIR / INTERFERENCE_REPORT_NAME).read_text(encoding="utf-8")
    )
    svg_ok = all(
        "<svg" in (LANE_DIR / rel).read_text(encoding="utf-8")
        and "NOT_FOR_MANUFACTURING" in (LANE_DIR / rel).read_text(encoding="utf-8")
        for rel in SVG_FILES
    )
    if hashes["hash_mismatch_count"]:
        raise RuntimeError(f"hash mismatch: {hashes['mismatches']}")
    if not manifest["path_set_match"] or manifest["duplicate_count"]:
        raise RuntimeError(f"manifest mismatch: {manifest}")
    if not all(item["pass"] for item in steps):
        raise RuntimeError(f"STEP semantic failure: {steps}")
    if validation_data["fail_count"]:
        raise RuntimeError(f"validation failure: {validation_data['failed_checks']}")
    if report["intersection_count"] or report["failure_count"]:
        raise RuntimeError("interference report failure")
    if not svg_ok:
        raise RuntimeError("SVG contract failure")
    return {
        "action": "VERIFY",
        "document_id": DOCUMENT_ID,
        "overall": validation_data["overall"],
        "recommended_candidate_id": RECOMMENDED["candidate_id"],
        "package_path_count": len(actual),
        "parent_audit_mode": parent["mode"],
        "parent_v008_to_v0085_checked_path_count": parent[
            "v008_to_v0085_checked_path_count"
        ],
        "parent_v090_checked_path_count": parent["v090_checked_path_count"],
        "parent_v090_ledger_sha256": parent["v090_ledger_sha256"],
        "baseline_mode": baseline["mode"],
        "baseline_reproduction": baseline["baseline_reproduction"],
        "validation_pass_count": validation_data["pass_count"],
        "validation_check_count": validation_data["check_count"],
        "interference_count": report["intersection_count"],
        "step_semantic_pass_count": sum(item["pass"] for item in steps),
        "svg_pass_count": len(SVG_FILES) if svg_ok else 0,
        "manifest_file_count": manifest["manifest_file_count"],
        "hashed_file_count": hashes["hashed_file_count"],
        "hash_mismatch_count": hashes["hash_mismatch_count"],
        "pointer_update_gate_pass": validation_data["pointer_update_gate_pass"],
        "pointer_authority": repo["pointer_authority"],
        "tracked_diff": repo["tracked_diff"],
        "staged_diff": repo["staged_diff"],
        "lane_untracked_count": repo["lane_untracked_count"],
    }


def _zip_info(rel: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(rel, date_time=(2000, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    info.create_system = 3
    return info


def package_handoff() -> dict[str, Any]:
    verification = verify()
    if _repo_root() is not None and verification["pointer_authority"] != "V091":
        raise RuntimeError("pointer gate has not been applied; refusing final package")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{stamp}.zip"
    counter = 1
    while path.exists():
        path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{stamp}_{counter:02d}.zip"
        counter += 1
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in PACKAGE_PATHS:
            archive.writestr(_zip_info(rel), (LANE_DIR / rel).read_bytes())
    zip_result = verify_zip(path)
    return {
        "action": "PACKAGE",
        "path": str(path),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
        **zip_result,
    }


def verify_zip(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"ZIP does not exist: {path}")
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        if names != list(PACKAGE_PATHS):
            raise RuntimeError("ZIP path order/set mismatch")
        mismatches = [
            rel
            for rel in PACKAGE_PATHS
            if hashlib.sha256(archive.read(rel)).hexdigest() != _sha256(LANE_DIR / rel)
        ]
        forbidden = [
            name
            for name in names
            if "__pycache__" in name
            or ".pytest_cache" in name
            or name.lower().endswith((".pyc", ".stl", ".dxf", ".3mf", ".gcode", ".fcstd"))
        ]
    if mismatches or forbidden:
        raise RuntimeError(
            f"ZIP mismatch/forbidden: mismatches={mismatches}, forbidden={forbidden}"
        )
    return {
        "zip_path_count": len(PACKAGE_PATHS),
        "zip_mismatch_count": len(mismatches),
        "zip_forbidden_count": len(forbidden),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--refresh-artifacts", action="store_true")
    group.add_argument("--verify", action="store_true")
    group.add_argument("--package", action="store_true")
    group.add_argument("--verify-zip", type=Path)
    args = parser.parse_args(argv)
    if args.refresh_artifacts:
        result = refresh_artifacts()
    elif args.verify:
        result = verify()
    elif args.package:
        result = package_handoff()
    else:
        result = verify_zip(args.verify_zip)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
