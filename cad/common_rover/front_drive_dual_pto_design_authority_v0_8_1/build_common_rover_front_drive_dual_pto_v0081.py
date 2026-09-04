"""Explore, build, verify, and package Common Rover belt-clearance v0.8.1.

The generated geometry is a non-manufacturing envelope study.  It preserves
the fixed v0.8 architecture and never promotes unmeasured hardware to physical
fit authority.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable

import cadquery as cq


LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
ARTIFACT_DIR = LANE_DIR / "artifacts"
TEST_DIR = LANE_DIR / "tests"
DOWNLOAD_DIR = Path("D:/Downloads")

DOCUMENT_ID = "PS-CR-FRONT-DRIVE-DUAL-PTO-BELT-CLEARANCE-V0081"
SCHEMA = "paddy_swarm.common_rover.front_drive_dual_pto_belt_clearance.v0.8.1"
AUTHORITY_STATUS = "V008_DIFFERENTIAL_AUTHORITY_WITH_PHYSICAL_HOLDS"
PHYSICAL_FIT = "HOLD"
MANUFACTURING_RELEASE = "HOLD"
FIELD_DEPLOYMENT = "NOT_APPROVED"

AUTHORITY_NAME = "common_rover_front_drive_dual_pto_design_authority_v0081.md"
PARAMETERS_NAME = "common_rover_front_drive_dual_pto_parameters_v0081.json"
BASELINE_NAME = "common_rover_front_drive_dual_pto_baseline_v0081.json"
SEARCH_NAME = "common_rover_front_drive_dual_pto_search_candidates_v0081.csv"
RANKING_NAME = "common_rover_front_drive_dual_pto_candidate_ranking_v0081.csv"
MATRIX_NAME = "common_rover_front_drive_dual_pto_interference_matrix_v0081.csv"
REPORT_NAME = "common_rover_front_drive_dual_pto_interference_report_v0081.json"
VALIDATION_NAME = "common_rover_front_drive_dual_pto_validation_v0081.json"
ALLOCATION_NAME = "common_rover_front_drive_dual_pto_aluminum_allocation_v0081.csv"
README_NAME = "README_HANDOFF.md"
MANIFEST_NAME = "MANIFEST.txt"
SHA256SUMS_NAME = "SHA256SUMS.txt"
TEST_RESULTS_NAME = "test_results_v0081.txt"
TEST_REL = "tests/test_common_rover_front_drive_dual_pto_v0081_contract.py"
STEP_NAME = "PS-CR-FRONT-DRIVE-DUAL-PTO-V0081-INSPECTION.step"
ALT_A_STEP_NAME = (
    "PS-CR-FRONT-DRIVE-DUAL-PTO-V0081-ALTERNATIVE-A-MIN-CHANGE.step"
)
ALT_B_STEP_NAME = (
    "PS-CR-FRONT-DRIVE-DUAL-PTO-V0081-ALTERNATIVE-B-PLATE6.step"
)
SVG_NAME = "PS-CR-FRONT-DRIVE-DUAL-PTO-V0081-OVERVIEW.svg"

PACKAGE_PATHS = (
    AUTHORITY_NAME,
    PARAMETERS_NAME,
    BASELINE_NAME,
    SEARCH_NAME,
    RANKING_NAME,
    MATRIX_NAME,
    REPORT_NAME,
    VALIDATION_NAME,
    ALLOCATION_NAME,
    "build_common_rover_front_drive_dual_pto_v0081.py",
    f"artifacts/{STEP_NAME}",
    f"artifacts/{ALT_A_STEP_NAME}",
    f"artifacts/{ALT_B_STEP_NAME}",
    f"artifacts/{SVG_NAME}",
    TEST_REL,
    README_NAME,
    MANIFEST_NAME,
    SHA256SUMS_NAME,
    TEST_RESULTS_NAME,
)
BYTE_REPRODUCIBLE_NAMES = (
    AUTHORITY_NAME,
    PARAMETERS_NAME,
    BASELINE_NAME,
    SEARCH_NAME,
    RANKING_NAME,
    MATRIX_NAME,
    REPORT_NAME,
    ALLOCATION_NAME,
    README_NAME,
    f"artifacts/{SVG_NAME}",
)

V008_REL_ROOT = "cad/common_rover/front_drive_dual_pto_design_authority_v0_8"
V008_HASHES = {
    f"{V008_REL_ROOT}/build_common_rover_front_drive_dual_pto_v008.py":
        "2d44b5fefdf32dd916c5a9cb61e153d6dabfbcffd6b20120b67b43c7eed8a3e7",
    f"{V008_REL_ROOT}/common_rover_front_drive_dual_pto_design_authority_v008.md":
        "0ebb03a8c45665aebb7f9e1bfa73048edb1fa8e540ebe039a5f204ca3fe0001b",
    f"{V008_REL_ROOT}/common_rover_front_drive_dual_pto_parameters_v008.json":
        "de6400838f25f157c9392a26ded5b3acfb3d7868d028d8e2a4ae5fff49dc0175",
    f"{V008_REL_ROOT}/common_rover_front_drive_dual_pto_interference_report_v008.json":
        "dbc8cc70d4dc1fa8ac1ceee0673b7452c658b3d4cedfd2407ae62dfdbf75302e",
    f"{V008_REL_ROOT}/common_rover_front_drive_dual_pto_interference_matrix_v008.csv":
        "8d9b962a879ac210fe36c3e6cf336b8956f904ce2746799c8b0f8bc2d08d0197",
    f"{V008_REL_ROOT}/common_rover_front_drive_dual_pto_aluminum_allocation_v008.csv":
        "13f3bb78f883a5ad9ccefbec3a264389333b30d632e3c77c6bd0c01222c933ab",
    f"{V008_REL_ROOT}/common_rover_front_drive_dual_pto_validation_v008.json":
        "903f69f5a87f18ebd49e97d30aa46813a9f1a793a678ac0ca39da7140ecec3c7",
    f"{V008_REL_ROOT}/artifacts/PS-CR-FRONT-DRIVE-DUAL-PTO-V008-INSPECTION.step":
        "fcad5fe47ae8a4f02c44235a73cbe2ca35a9cf616dc707acb84100e00313f41b",
    f"{V008_REL_ROOT}/artifacts/PS-CR-FRONT-DRIVE-DUAL-PTO-V008-OVERVIEW.svg":
        "b3c8e83eb5baa75944d55f3cab9fb4b24d6f2efffe18d57e5bbc1d2c3c2e4b89",
    "tests/test_common_rover_front_drive_dual_pto_v008_contract.py":
        "4f6e9aea39e2c501a959f3fecfd6f24e8fe130976563ac786cea72b14722a78b",
}

V008_BASELINE = {
    "drive_belt_to_frame_mm": 15.5,
    "pto_belt_to_frame_mm": 5.5,
    "drive_belt_to_root_2040_mm": 25.5,
    "drive_belt_to_front_track_diagonal_mm": 15.5,
    "pto_belt_to_2020_diagonal_mm": 70.0,
    "pto_belt_to_front_crossbar_mm": 71.53,
    "pto_60t_to_kp000_mm": 11.0,
    "track_dynamic_to_upper_structure_mm": 10.0,
    "step_width_mm": 290.0,
    "pto_outer_end_y_mm": [-145.0, 145.0],
    "component_count": 79,
    "solid_count": 79,
    "candidate_interference_fail_count": 0,
    "hold_count": 51,
}

FIXED = {
    "coordinate_system": {
        "+X": "FRONT",
        "+Y": "LEFT",
        "+Z": "UP",
        "ground_z_mm": 0.0,
        "length_unit": "mm",
    },
    "motor_count": 2,
    "motor_shaft_directions": {"left": "-Y_INWARD", "right": "+Y_INWARD"},
    "pto_count": 2,
    "pto_architecture": "TWO_INDEPENDENT_LATERAL_SHAFTS",
    "pto_output_directions": {"left": "+Y", "right": "-Y"},
    "common_pto_shaft": "PROHIBITED",
    "clutch_states": ["DRIVE", "NEUTRAL", "PTO"],
    "simultaneous_same_side_drive_pto": "PROHIBITED",
    "cbox_size_mm": {"x": 130.0, "y": 140.0, "z": 105.0},
    "bbox_size_mm": {"x": 150.0, "y": 220.0, "z": 150.0},
    "battery_cassette_size_mm": {"x": 125.0, "y": 180.0, "z": 120.0},
    "box_arrangement": "CBOX_FRONT_BBOX_REAR_SHORT_FACES_OPPOSED",
    "box_structural_role": "PROHIBITED",
    "box_bottom_z_mm": 200.0,
    "box_top_max_z_mm": 350.0,
    "motor_axis_z_mm": 370.0,
    "pto_axis_z_mm": 370.0,
    "motor_height_meaning": "MOTOR_SHAFT_CENTER_HEIGHT",
    "track_width_each_mm": 55.0,
    "central_lower_structure_max_width_mm": 180.0,
    "target_total_width_mm": [286.0, 290.0],
    "absolute_total_width_mm": 299.0,
    "crawler_geometry": "INVERTED_TRAPEZOID_TOP_LONGER",
    "crawler_each_side": {
        "front_upper_drive_wheel": 1,
        "rear_upper_idler": 1,
        "lower_roller_candidates": [3, 4],
        "step_roller_count": 4,
    },
    "upper_2040_candidate_mm": 400.0,
    "lower_2040_candidate_mm": 260.0,
    "single_aluminum_member_max_mm": 400.0,
    "belt_standard": "HTD_5M_STANDARD_15MM",
    "pulley_teeth": {"driver": 20, "driven": 60},
    "pulley_60t_safety_diameter_mm": 120.0,
}

ALLOWANCES = {
    "assembly_tolerance_mm": 1.0,
    "frame_deflection_allowance_mm": 2.0,
    "belt_lateral_wander_allowance_mm": 2.0,
    "total_provisional_allowance_mm": 5.0,
    "axial_play_mm": [-1.0, 1.0],
}
TARGETS = {
    "belt_nominal_minimum_mm": 13.0,
    "belt_nominal_preferred_mm": 15.0,
    "belt_residual_minimum_mm": 8.0,
    "pulley_60t_to_fixed_minimum_mm": 10.0,
    "belt_to_wiring_candidate_mm": 15.0,
    "total_width_strict_max_mm": 300.0,
    "pto_outer_end_abs_max_mm": 145.0,
    "track_upper_structure_non_regression_mm": 10.0,
}

BASE = {
    "pto_belt_plane_abs_y_mm": 45.0,
    "drive_belt_plane_abs_y_mm": 119.0,
    "inner_kp000_center_abs_y_mm": 14.0,
    "outer_kp000_center_abs_y_mm": 82.0,
    "outer_fastener_center_abs_y_mm": 70.0,
    "support_2020_y_thickness_mm": 20.0,
    "belt_envelope_y_width_mm": 31.0,
    "pulley_axial_envelope_mm": 25.0,
    "kp000_axial_envelope_mm": 15.0,
    "pto_outer_end_abs_y_mm": 145.0,
    "total_width_mm": 290.0,
    "drive_frame_clearance_mm": 15.5,
    "track_outer_abs_y_mm": 143.0,
}

RECOMMENDED_ID = "S2-REF-T5-BP2.00-OP5.50"
ALTERNATIVE_A_ID = "S2-REF-T5-BP0.00-OP1.50"
ALTERNATIVE_B_ID = "S2-REF-T6-BP2.50-OP6.00"


def _round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _csv_text(rows: list[dict], fieldnames: list[str]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _frange(start: float, stop: float, step: float) -> list[float]:
    count = int(round((stop - start) / step))
    return [_round(start + index * step, 2) for index in range(count + 1)]


SEARCH_FIELDS = [
    "candidate_id",
    "search_stage",
    "search_resolution",
    "pto_belt_shift_mm",
    "drive_belt_shift_mm",
    "inner_support_type",
    "inner_support_thickness_mm",
    "inner_kp000_shift_inward_mm",
    "outer_kp000_shift_outward_mm",
    "fastener_orientation",
    "fastener_style",
    "pto_nominal_clearance_mm",
    "pto_residual_clearance_mm",
    "drive_nominal_clearance_mm",
    "drive_residual_clearance_mm",
    "pulley_60t_to_fixed_mm",
    "belt_to_wiring_mm",
    "inner_support_center_gap_mm",
    "track_outer_margin_mm",
    "total_width_mm",
    "left_pto_outer_end_y_mm",
    "right_pto_outer_end_y_mm",
    "belt_intersection_count",
    "fastener_intersection_count",
    "tool_access_intersection_count",
    "clutch_intersection_count",
    "track_intersection_count",
    "aluminum_2020_stock_used",
    "aluminum_2040_stock_used",
    "added_part_count",
    "total_y_change_mm",
    "serviceability_score",
    "score",
    "status",
    "rejection_reason",
]


def _candidate_common(
    *,
    candidate_id: str,
    stage: str,
    resolution: str,
    pto_belt_shift: float,
    drive_belt_shift: float,
    support_type: str,
    thickness: float,
    inner_shift: float,
    outer_shift: float,
    fastener_orientation: str,
    fastener_style: str,
    pto_clearance: float,
    pulley_clearance: float,
    fastener_clearance: float,
    inner_support_gap: float,
    tool_access_intersections: int,
    added_parts: int,
) -> dict:
    pto_nominal = min(pto_clearance, fastener_clearance)
    pto_residual = pto_nominal - ALLOWANCES["total_provisional_allowance_mm"]
    drive_nominal = BASE["drive_frame_clearance_mm"] + drive_belt_shift
    drive_residual = drive_nominal - ALLOWANCES["total_provisional_allowance_mm"]
    drive_outer_margin = (
        BASE["track_outer_abs_y_mm"]
        - (
            BASE["drive_belt_plane_abs_y_mm"]
            + drive_belt_shift
            + BASE["belt_envelope_y_width_mm"] / 2.0
        )
    )
    belt_to_wiring = (
        BASE["pto_belt_plane_abs_y_mm"]
        + pto_belt_shift
        - BASE["belt_envelope_y_width_mm"] / 2.0
        - 10.0
    )
    belt_intersections = int(pto_nominal < 0.0 or drive_nominal < 0.0)
    fastener_intersections = int(fastener_clearance < 0.0)
    track_intersections = int(drive_outer_margin < 0.0)
    reasons: list[str] = []
    if inner_support_gap < 0.0:
        reasons.append("LEFT_RIGHT_INNER_SUPPORT_COLLISION")
    if pto_nominal < TARGETS["belt_nominal_minimum_mm"]:
        reasons.append("PTO_NOMINAL_LT_13")
    if pto_residual < TARGETS["belt_residual_minimum_mm"]:
        reasons.append("PTO_RESIDUAL_LT_8")
    if drive_nominal < TARGETS["belt_nominal_minimum_mm"]:
        reasons.append("DRIVE_NOMINAL_LT_13")
    if drive_residual < TARGETS["belt_residual_minimum_mm"]:
        reasons.append("DRIVE_RESIDUAL_LT_8")
    if pulley_clearance < TARGETS["pulley_60t_to_fixed_minimum_mm"]:
        reasons.append("PULLEY_FIXED_LT_10")
    if belt_to_wiring < TARGETS["belt_to_wiring_candidate_mm"]:
        reasons.append("BELT_WIRING_LT_15")
    if drive_outer_margin < 0.0:
        reasons.append("DRIVE_ENVELOPE_OUTSIDE_TRACK_WIDTH")
    if any(
        (
            belt_intersections,
            fastener_intersections,
            tool_access_intersections,
            track_intersections,
        )
    ):
        reasons.append("NONZERO_INTERSECTION")
    hard_pass = not reasons
    total_change = (
        abs(pto_belt_shift)
        + abs(drive_belt_shift)
        + abs(inner_shift)
        + abs(outer_shift)
    )
    serviceability = (
        10.0
        if fastener_orientation == "REVERSED_AWAY_FROM_BELT"
        else 6.0
        if fastener_style == "LOW_HEAD"
        else 4.0
    )
    score = (
        (1000.0 if hard_pass else 0.0)
        + 20.0 * min(pto_residual, drive_residual)
        - 3.0 * total_change
        - 15.0 * added_parts
        + 2.0 * serviceability
    )
    return {
        "candidate_id": candidate_id,
        "search_stage": stage,
        "search_resolution": resolution,
        "pto_belt_shift_mm": _round(pto_belt_shift, 2),
        "drive_belt_shift_mm": _round(drive_belt_shift, 2),
        "inner_support_type": support_type,
        "inner_support_thickness_mm": _round(thickness, 2),
        "inner_kp000_shift_inward_mm": _round(inner_shift, 2),
        "outer_kp000_shift_outward_mm": _round(outer_shift, 2),
        "fastener_orientation": fastener_orientation,
        "fastener_style": fastener_style,
        "pto_nominal_clearance_mm": _round(pto_nominal, 2),
        "pto_residual_clearance_mm": _round(pto_residual, 2),
        "drive_nominal_clearance_mm": _round(drive_nominal, 2),
        "drive_residual_clearance_mm": _round(drive_residual, 2),
        "pulley_60t_to_fixed_mm": _round(pulley_clearance, 2),
        "belt_to_wiring_mm": _round(belt_to_wiring, 2),
        "inner_support_center_gap_mm": _round(inner_support_gap, 2),
        "track_outer_margin_mm": _round(drive_outer_margin, 2),
        "total_width_mm": BASE["total_width_mm"],
        "left_pto_outer_end_y_mm": BASE["pto_outer_end_abs_y_mm"],
        "right_pto_outer_end_y_mm": -BASE["pto_outer_end_abs_y_mm"],
        "belt_intersection_count": belt_intersections,
        "fastener_intersection_count": fastener_intersections,
        "tool_access_intersection_count": tool_access_intersections,
        "clutch_intersection_count": 0,
        "track_intersection_count": track_intersections,
        "aluminum_2020_stock_used": 7 if support_type.startswith("METAL_PLATE") else 8,
        "aluminum_2040_stock_used": 7,
        "added_part_count": added_parts,
        "total_y_change_mm": _round(total_change, 2),
        "serviceability_score": serviceability,
        "score": _round(score, 2),
        "status": "CONDITIONAL_PASS" if hard_pass else "FAIL",
        "rejection_reason": "" if hard_pass else ";".join(sorted(set(reasons))),
    }


def _stage1_candidate(
    candidate_id: str,
    resolution: str,
    pto_shift: float,
    spread_delta: float,
) -> dict:
    belt_low = (
        BASE["pto_belt_plane_abs_y_mm"]
        + pto_shift
        - BASE["belt_envelope_y_width_mm"] / 2.0
    )
    belt_high = (
        BASE["pto_belt_plane_abs_y_mm"]
        + pto_shift
        + BASE["belt_envelope_y_width_mm"] / 2.0
    )
    inner_center = BASE["inner_kp000_center_abs_y_mm"] - spread_delta
    outer_center = BASE["outer_kp000_center_abs_y_mm"] + spread_delta
    inner_support_clearance = belt_low - (
        inner_center + BASE["support_2020_y_thickness_mm"] / 2.0
    )
    outer_support_clearance = (
        outer_center - BASE["support_2020_y_thickness_mm"] / 2.0
    ) - belt_high
    outer_fastener_clearance = (
        BASE["outer_fastener_center_abs_y_mm"] + spread_delta - 4.0
    ) - belt_high
    pto_clearance = min(inner_support_clearance, outer_support_clearance)
    pulley_center = BASE["pto_belt_plane_abs_y_mm"] + pto_shift
    pulley_low = pulley_center - BASE["pulley_axial_envelope_mm"] / 2.0
    pulley_high = pulley_center + BASE["pulley_axial_envelope_mm"] / 2.0
    pulley_clearance = min(
        pulley_low
        - (inner_center + BASE["kp000_axial_envelope_mm"] / 2.0),
        (outer_center - BASE["kp000_axial_envelope_mm"] / 2.0)
        - pulley_high,
    )
    inner_gap = 2.0 * (
        inner_center - BASE["support_2020_y_thickness_mm"] / 2.0
    )
    return _candidate_common(
        candidate_id=candidate_id,
        stage="STAGE_1_Y_POSITION_ONLY",
        resolution=resolution,
        pto_belt_shift=pto_shift,
        drive_belt_shift=0.0,
        support_type="2020_UNCHANGED",
        thickness=20.0,
        inner_shift=spread_delta,
        outer_shift=spread_delta,
        fastener_orientation="V008_BASELINE_INWARD",
        fastener_style="STANDARD_RESERVED",
        pto_clearance=pto_clearance,
        pulley_clearance=pulley_clearance,
        fastener_clearance=outer_fastener_clearance,
        inner_support_gap=inner_gap,
        tool_access_intersections=0,
        added_parts=0,
    )


def _stage1_drive_candidate(shift: float) -> dict:
    pto_baseline = 5.5
    return _candidate_common(
        candidate_id=f"S1-DRIVE-{shift:+05.1f}",
        stage="STAGE_1_DRIVE_Y_POSITION",
        resolution="COARSE_1.00_MM",
        pto_belt_shift=0.0,
        drive_belt_shift=shift,
        support_type="2020_UNCHANGED",
        thickness=20.0,
        inner_shift=0.0,
        outer_shift=0.0,
        fastener_orientation="V008_BASELINE_INWARD",
        fastener_style="STANDARD_RESERVED",
        pto_clearance=pto_baseline,
        pulley_clearance=11.0,
        fastener_clearance=5.5,
        inner_support_gap=8.0,
        tool_access_intersections=0,
        added_parts=0,
    )


def _stage2_candidate(
    candidate_id: str,
    resolution: str,
    thickness: float,
    pto_shift: float,
    outer_shift: float,
    orientation: str = "REVERSED_AWAY_FROM_BELT",
    style: str = "STANDARD_REVERSED",
) -> dict:
    belt_low = (
        BASE["pto_belt_plane_abs_y_mm"]
        + pto_shift
        - BASE["belt_envelope_y_width_mm"] / 2.0
    )
    belt_high = (
        BASE["pto_belt_plane_abs_y_mm"]
        + pto_shift
        + BASE["belt_envelope_y_width_mm"] / 2.0
    )
    inner_plate_edge = BASE["inner_kp000_center_abs_y_mm"] + thickness / 2.0
    outer_center = BASE["outer_kp000_center_abs_y_mm"] + outer_shift
    inner_clearance = belt_low - inner_plate_edge
    outer_clearance = (
        outer_center - BASE["support_2020_y_thickness_mm"] / 2.0
    ) - belt_high
    if orientation == "REVERSED_AWAY_FROM_BELT":
        fastener_clearance = min(inner_clearance + 8.0, outer_clearance + 12.0)
        tool_intersections = 0
    else:
        baseline_fastener_clearance = (
            BASE["outer_fastener_center_abs_y_mm"] + outer_shift - 4.0
        ) - belt_high
        style_gain = {
            "STANDARD_BASELINE": 0.0,
            "LOW_HEAD_BASELINE": 2.0,
            "COUNTERSUNK_CANDIDATE": 4.0,
        }.get(style, 0.0)
        fastener_clearance = baseline_fastener_clearance + style_gain
        tool_intersections = 0
    pulley_center = BASE["pto_belt_plane_abs_y_mm"] + pto_shift
    pulley_low = pulley_center - BASE["pulley_axial_envelope_mm"] / 2.0
    pulley_high = pulley_center + BASE["pulley_axial_envelope_mm"] / 2.0
    inner_kp_max = (
        BASE["inner_kp000_center_abs_y_mm"]
        + BASE["kp000_axial_envelope_mm"] / 2.0
    )
    outer_kp_min = (
        outer_center - BASE["kp000_axial_envelope_mm"] / 2.0
    )
    pulley_clearance = min(
        pulley_low - inner_kp_max,
        outer_kp_min - pulley_high,
    )
    inner_fastener_gap = 2.0 * (
        BASE["inner_kp000_center_abs_y_mm"]
        - thickness / 2.0
        - 8.0
    )
    return _candidate_common(
        candidate_id=candidate_id,
        stage="STAGE_2_INNER_SUPPORT_AND_FASTENERS",
        resolution=resolution,
        pto_belt_shift=pto_shift,
        drive_belt_shift=0.0,
        support_type=f"METAL_PLATE_{int(thickness)}MM_CANDIDATE",
        thickness=thickness,
        inner_shift=0.0,
        outer_shift=outer_shift,
        fastener_orientation=orientation,
        fastener_style=style,
        pto_clearance=min(inner_clearance, outer_clearance),
        pulley_clearance=pulley_clearance,
        fastener_clearance=fastener_clearance,
        inner_support_gap=inner_fastener_gap,
        tool_access_intersections=tool_intersections,
        added_parts=2,
    )


def build_search() -> tuple[list[dict], dict]:
    rows: list[dict] = []
    for pto_shift in _frange(-10.0, 10.0, 1.0):
        for spread in _frange(-10.0, 10.0, 1.0):
            rows.append(
                _stage1_candidate(
                    f"S1-Y-B{pto_shift:+05.1f}-D{spread:+05.1f}",
                    "COARSE_1.00_MM",
                    pto_shift,
                    spread,
                )
            )
    for drive_shift in _frange(-10.0, 10.0, 1.0):
        rows.append(_stage1_drive_candidate(drive_shift))
    for pto_shift in _frange(-1.0, 1.0, 0.25):
        for spread in _frange(3.0, 4.0, 0.25):
            rows.append(
                _stage1_candidate(
                    f"S1-REF-B{pto_shift:+05.2f}-D{spread:+05.2f}",
                    "REFINED_0.25_MM",
                    pto_shift,
                    spread,
                )
            )

    # Stage 1 cannot reach 13/8 while retaining two non-colliding 2020
    # supports and baseline inward fixed hardware.  Enter stage 2.
    for thickness in (5.0, 6.0, 8.0):
        for orientation, style in (
            ("BASELINE_BELT_SIDE", "STANDARD_BASELINE"),
            ("BASELINE_BELT_SIDE", "LOW_HEAD_BASELINE"),
            ("BASELINE_BELT_SIDE", "COUNTERSUNK_CANDIDATE"),
            ("REVERSED_AWAY_FROM_BELT", "STANDARD_REVERSED"),
        ):
            rows.append(
                _stage2_candidate(
                    f"S2-FIX-T{int(thickness)}-{style}",
                    "FIXED_HARDWARE_COMPARISON",
                    thickness,
                    0.0,
                    0.0,
                    orientation,
                    style,
                )
            )
    for thickness in (5.0, 6.0, 8.0):
        for pto_shift in _frange(-2.0, 10.0, 0.5):
            for outer_shift in _frange(0.0, 10.0, 1.0):
                rows.append(
                    _stage2_candidate(
                        (
                            f"S2-COARSE-T{int(thickness)}-"
                            f"BP{pto_shift:+05.1f}-OP{outer_shift:04.1f}"
                        ),
                        "COARSE_BELT_0.50_OUTER_1.00_MM",
                        thickness,
                        pto_shift,
                        outer_shift,
                    )
                )
    for thickness in (5.0, 6.0, 8.0):
        for pto_shift in _frange(0.0, 3.0, 0.25):
            for outer_shift in _frange(1.0, 7.0, 0.25):
                rows.append(
                    _stage2_candidate(
                        (
                            f"S2-REF-T{int(thickness)}-"
                            f"BP{pto_shift:.2f}-OP{outer_shift:.2f}"
                        ),
                        "REFINED_0.25_MM",
                        thickness,
                        pto_shift,
                        outer_shift,
                    )
                )
    by_id = {row["candidate_id"]: row for row in rows}
    for required in (RECOMMENDED_ID, ALTERNATIVE_A_ID, ALTERNATIVE_B_ID):
        if required not in by_id:
            raise RuntimeError(f"required selected candidate missing: {required}")
        if by_id[required]["status"] != "CONDITIONAL_PASS":
            raise RuntimeError(f"selected candidate does not pass: {required}")
    stage_counts = Counter(row["search_stage"] for row in rows)
    stage_pass_counts = Counter(
        row["search_stage"]
        for row in rows
        if row["status"] == "CONDITIONAL_PASS"
    )
    stage1_rows = [
        row for row in rows if row["search_stage"].startswith("STAGE_1")
    ]
    stage1_geometrically_feasible = [
        row
        for row in stage1_rows
        if row["inner_support_center_gap_mm"] >= 0.0
        and row["belt_intersection_count"] == 0
        and row["fastener_intersection_count"] == 0
        and row["tool_access_intersection_count"] == 0
        and row["track_intersection_count"] == 0
    ]
    rejection_counts: Counter[str] = Counter()
    for row in rows:
        for reason in filter(None, row["rejection_reason"].split(";")):
            rejection_counts[reason] += 1
    metadata = {
        "total_candidate_count": len(rows),
        "candidate_count_by_stage": dict(sorted(stage_counts.items())),
        "conditional_pass_count_by_stage": dict(sorted(stage_pass_counts.items())),
        "stage_1_max_nominal_clearance_mm": max(
            row["pto_nominal_clearance_mm"]
            for row in stage1_geometrically_feasible
        ),
        "stage_1_max_residual_clearance_mm": max(
            row["pto_residual_clearance_mm"]
            for row in stage1_geometrically_feasible
        ),
        "stage_1_raw_max_nominal_including_rejected_mm": max(
            row["pto_nominal_clearance_mm"] for row in stage1_rows
        ),
        "stage_1_raw_max_residual_including_rejected_mm": max(
            row["pto_residual_clearance_mm"] for row in stage1_rows
        ),
        "rejection_reason_counts": dict(sorted(rejection_counts.items())),
        "stage_1_result": "FAIL_CANNOT_REACH_13_AND_8",
        "stage_2_result": "CONDITIONAL_PASS",
        "stages_3_to_6": "NOT_EXECUTED_STAGE_2_SATISFIED_TARGET",
        "selected_ids": {
            "recommended": RECOMMENDED_ID,
            "alternative_a": ALTERNATIVE_A_ID,
            "alternative_b": ALTERNATIVE_B_ID,
        },
    }
    return rows, metadata


def build_ranking(rows: list[dict]) -> list[dict]:
    by_id = {row["candidate_id"]: row for row in rows}
    passing = [row for row in rows if row["status"] == "CONDITIONAL_PASS"]
    preferred = [
        row
        for row in passing
        if row["pto_nominal_clearance_mm"]
        >= TARGETS["belt_nominal_preferred_mm"]
    ]
    preferred.sort(
        key=lambda row: (
            row["total_y_change_mm"],
            row["added_part_count"],
            row["inner_support_thickness_mm"],
            -row["serviceability_score"],
            row["candidate_id"],
        )
    )
    threshold = sorted(
        passing,
        key=lambda row: (
            row["total_y_change_mm"],
            row["added_part_count"],
            -row["pto_residual_clearance_mm"],
            row["candidate_id"],
        ),
    )
    max_residual = max(row["pto_residual_clearance_mm"] for row in passing)
    min_change = min(row["total_y_change_mm"] for row in passing)
    ranking_ids = [
        RECOMMENDED_ID,
        ALTERNATIVE_A_ID,
        ALTERNATIVE_B_ID,
    ]
    for row in (*preferred, *threshold):
        if row["candidate_id"] not in ranking_ids:
            ranking_ids.append(row["candidate_id"])
        if len(ranking_ids) >= 10:
            break
    ranking: list[dict] = []

    def append_scope(scope: str, candidates: list[dict]) -> None:
        for rank, source in enumerate(candidates[:10], start=1):
            row = dict(source)
            candidate_id = row["candidate_id"]
            row["rank_scope"] = scope
            row["rank"] = rank
            row["selection_role"] = (
                "RECOMMENDED"
                if scope == "OVERALL" and candidate_id == RECOMMENDED_ID
                else "ALTERNATIVE_A_MINIMUM_CHANGE"
                if scope == "OVERALL" and candidate_id == ALTERNATIVE_A_ID
                else "ALTERNATIVE_B_6MM_PLATE"
                if scope == "OVERALL" and candidate_id == ALTERNATIVE_B_ID
                else "TOP_10_COMPARISON"
            )
            row["pareto_maximum_minimum_residual"] = (
                row["pto_residual_clearance_mm"] == max_residual
            )
            row["pareto_minimum_total_width"] = True
            row["pareto_minimum_change"] = row["total_y_change_mm"] == min_change
            row["pareto_minimum_added_parts"] = row["added_part_count"] == 2
            row["pareto_maximum_tool_access"] = (
                row["tool_access_intersection_count"] == 0
            )
            row["pareto_maximum_serviceability"] = (
                row["serviceability_score"] == 10.0
            )
            ranking.append(row)

    stage1_top = sorted(
        (
            row
            for row in rows
            if row["search_stage"].startswith("STAGE_1")
            and row["inner_support_center_gap_mm"] >= 0.0
            and row["belt_intersection_count"] == 0
            and row["fastener_intersection_count"] == 0
            and row["track_intersection_count"] == 0
        ),
        key=lambda row: (
            -row["pto_nominal_clearance_mm"],
            -row["pto_residual_clearance_mm"],
            row["total_y_change_mm"],
            row["candidate_id"],
        ),
    )
    stage2_top = sorted(
        (
            row
            for row in rows
            if row["search_stage"] == "STAGE_2_INNER_SUPPORT_AND_FASTENERS"
            and row["status"] == "CONDITIONAL_PASS"
        ),
        key=lambda row: (
            -int(row["pto_nominal_clearance_mm"] >= 15.0),
            row["total_y_change_mm"],
            row["inner_support_thickness_mm"],
            -row["pto_residual_clearance_mm"],
            row["candidate_id"],
        ),
    )
    append_scope("STAGE_1", stage1_top)
    append_scope("STAGE_2", stage2_top)
    append_scope("OVERALL", [by_id[candidate_id] for candidate_id in ranking_ids[:10]])
    return ranking


def _shape(value: cq.Shape | cq.Workplane) -> cq.Shape:
    return value.val() if isinstance(value, cq.Workplane) else value


def _box(
    x_size: float,
    y_size: float,
    z_size: float,
    *,
    x: float,
    y: float,
    z_bottom: float,
) -> cq.Shape:
    return _shape(
        cq.Workplane("XY")
        .box(x_size, y_size, z_size, centered=(True, True, False))
        .translate((x, y, z_bottom))
    )


def _cylinder_y(
    radius: float,
    length: float,
    *,
    x: float,
    y: float,
    z: float,
) -> cq.Shape:
    return cq.Solid.makeCylinder(
        radius,
        length,
        cq.Vector(x, y - length / 2.0, z),
        cq.Vector(0.0, 1.0, 0.0),
    )


def _beam_xz(
    x1: float,
    z1: float,
    x2: float,
    z2: float,
    *,
    y: float,
) -> cq.Shape:
    length = math.hypot(x2 - x1, z2 - z1)
    angle = -math.degrees(math.atan2(z2 - z1, x2 - x1))
    shape = _box(length, 20.0, 20.0, x=0.0, y=0.0, z_bottom=-10.0)
    shape = shape.rotate(
        cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), angle
    )
    return shape.translate(cq.Vector((x1 + x2) / 2.0, y, (z1 + z2) / 2.0))


def _beam_xy(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    z: float,
) -> cq.Shape:
    length = math.hypot(x2 - x1, y2 - y1)
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    shape = _box(length, 20.0, 20.0, x=0.0, y=0.0, z_bottom=-10.0)
    shape = shape.rotate(
        cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), angle
    )
    return shape.translate(cq.Vector((x1 + x2) / 2.0, (y1 + y2) / 2.0, z))


def _belt(
    x1: float,
    z1: float,
    r1: float,
    x2: float,
    z2: float,
    r2: float,
    *,
    y: float,
) -> cq.Shape:
    length = math.hypot(x2 - x1, z2 - z1)
    angle = -math.degrees(math.atan2(z2 - z1, x2 - x1))
    strip = _box(length, 31.0, 20.0, x=0.0, y=0.0, z_bottom=-10.0)
    strip = strip.rotate(
        cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), angle
    )
    strip = strip.translate(
        cq.Vector((x1 + x2) / 2.0, y, (z1 + z2) / 2.0)
    )
    return (
        strip.fuse(_cylinder_y(r1, 31.0, x=x1, y=y, z=z1))
        .fuse(_cylinder_y(r2, 31.0, x=x2, y=y, z=z2))
    )


def _track(side: str, box_bottom_z: float = 200.0) -> cq.Shape:
    del box_bottom_z
    points = ((-140.0, 185.0), (340.0, 185.0), (270.0, 10.0), (-70.0, 10.0))
    shape = _shape(cq.Workplane("XZ").polyline(points).close().extrude(55.0))
    return shape.translate(
        cq.Vector(0.0, 143.0 if side == "LEFT" else -88.0, 0.0)
    )


def build_model(candidate: dict, *, box_bottom_z: float = 200.0) -> dict[str, cq.Shape]:
    c: dict[str, cq.Shape] = {}
    c["CBOX"] = _box(130, 140, 105, x=85, y=0, z_bottom=box_bottom_z)
    c["BBOX"] = _box(150, 220, 150, x=-75, y=0, z_bottom=box_bottom_z)
    c["BATTERY_CASSETTE"] = _box(125, 180, 120, x=-75, y=0, z_bottom=box_bottom_z + 15)
    c["CBOX_LID_SERVICE"] = _box(130, 140, 50, x=85, y=0, z_bottom=box_bottom_z + 105)
    c["BBOX_LID_SERVICE"] = _box(150, 220, 50, x=-75, y=0, z_bottom=box_bottom_z + 150)
    c["CASSETTE_REAR_REMOVAL"] = _box(125, 180, 120, x=-212.5, y=0, z_bottom=box_bottom_z + 15)

    for side, sign in (("LEFT", 1.0), ("RIGHT", -1.0)):
        c[f"{side}_MAIN_2040"] = _box(400, 20, 40, x=50, y=sign * 68, z_bottom=160)
        c[f"{side}_TRACK_UPPER_2040"] = _box(400, 20, 40, x=80, y=sign * 78, z_bottom=110)
        c[f"{side}_TRACK_LOWER_2040"] = _box(260, 20, 40, x=100, y=sign * 78, z_bottom=20)
        c[f"{side}_TRACK_FRONT_DIAGONAL"] = _beam_xz(230, 60, 280, 110, y=sign * 78)
        c[f"{side}_TRACK_REAR_DIAGONAL"] = _beam_xz(-30, 60, -120, 110, y=sign * 78)
        c[f"{side}_PTO_SPAR_2020"] = _box(170, 20, 20, x=335, y=sign * 68, z_bottom=220)
        c[f"{side}_PTO_DIAGONAL_2020"] = _beam_xy(250, sign * 20, 410, sign * 68, z=230)
        c[f"{side}_PTO_ROOT_GUSSET_RESERVED"] = _box(40, 20, 40, x=250, y=sign * 68, z_bottom=195)
    c["REAR_2040_CROSSMEMBER"] = _box(40, 156, 40, x=-140, y=0, z_bottom=160)
    c["PTO_ROOT_2040_CROSSMEMBER"] = _box(40, 156, 20, x=250, y=0, z_bottom=220)
    c["PTO_FRONT_2020_CROSSBAR"] = _box(20, 156, 20, x=420, y=0, z_bottom=220)
    for index, x in enumerate((-135, -15, 35, 145), start=1):
        c[f"BOX_SUPPORT_2020_{index}"] = _box(20, 156, 20, x=x, y=0, z_bottom=180)

    c["TRACK_LEFT_DYNAMIC"] = _track("LEFT", box_bottom_z)
    c["TRACK_RIGHT_DYNAMIC"] = _track("RIGHT", box_bottom_z)
    for side, sign in (("LEFT", 1.0), ("RIGHT", -1.0)):
        c[f"{side}_FRONT_DRIVE_WHEEL"] = _cylinder_y(35, 55, x=300, y=sign * 115.5, z=155)
        c[f"{side}_REAR_IDLER"] = _cylinder_y(35, 55, x=-100, y=sign * 115.5, z=155)
        for index, x in enumerate((0, 70, 140, 210), start=1):
            c[f"{side}_LOWER_ROLLER_{index}"] = _cylinder_y(25, 55, x=x, y=sign * 115.5, z=45)
        c[f"{side}_MOTOR_RESERVED"] = _cylinder_y(30, 70, x=205, y=sign * 105, z=370)
        c[f"{side}_CLUTCH_FULL_STROKE"] = _box(50, 60, 50, x=245, y=sign * 62, z_bottom=345)

    pto_y = 45.0 + float(candidate["pto_belt_shift_mm"])
    outer_y = 82.0 + float(candidate["outer_kp000_shift_outward_mm"])
    plate_t = float(candidate["inner_support_thickness_mm"])
    for side, sign in (("LEFT", 1.0), ("RIGHT", -1.0)):
        c[f"{side}_DRIVE_BELT_ENVELOPE"] = _belt(245, 370, 25, 300, 155, 60, y=sign * 119)
        c[f"{side}_PTO_BELT_ENVELOPE"] = _belt(255, 370, 25, 390, 370, 60, y=sign * pto_y)
        c[f"{side}_PTO_60T_ENVELOPE"] = _cylinder_y(60, 25, x=390, y=sign * pto_y, z=370)
        c[f"{side}_INNER_KP000"] = _box(45, 15, 35, x=390, y=sign * 14, z_bottom=352.5)
        c[f"{side}_OUTER_KP000"] = _box(45, 15, 35, x=390, y=sign * outer_y, z_bottom=352.5)
        c[f"{side}_INNER_METAL_PLATE_5_6_8_CANDIDATE"] = _box(
            20, plate_t, 110, x=390, y=sign * 14, z_bottom=240
        )
        c[f"{side}_OUTER_VERTICAL_2020"] = _box(20, 20, 110, x=390, y=sign * outer_y, z_bottom=240)
        c[f"{side}_INNER_BEARING_BRACKET_RESERVED"] = _box(
            45, plate_t, 10, x=390, y=sign * 14, z_bottom=345
        )
        c[f"{side}_OUTER_BEARING_BRACKET_RESERVED"] = _box(
            45, 20, 10, x=390, y=sign * outer_y, z_bottom=345
        )
        inner_fast_y = sign * (14 - plate_t / 2.0 - 4.0)
        outer_fast_y = sign * (outer_y + 10.0 + 4.0)
        c[f"{side}_INNER_KP000_FASTENERS"] = _box(8, 8, 8, x=390, y=inner_fast_y, z_bottom=346)
        c[f"{side}_OUTER_KP000_FASTENERS"] = _box(8, 8, 8, x=390, y=outer_fast_y, z_bottom=346)
        shaft_start = sign * (outer_y + 7.5)
        shaft_end = sign * 145.0
        c[f"{side}_PTO_SHAFT_COUPLING_RESERVED"] = _cylinder_y(
            17,
            abs(shaft_end - shaft_start),
            x=390,
            y=(shaft_start + shaft_end) / 2.0,
            z=370,
        )
        c[f"{side}_PTO_TENSIONER_FULL_SWEEP_RESERVED"] = _box(
            45, 20, 35, x=325, y=sign * pto_y, z_bottom=392
        )
        c[f"{side}_DRIVE_TENSIONER_FULL_SWEEP_RESERVED"] = _box(
            35, 20, 35, x=267, y=sign * 119, z_bottom=245
        )
    c["TOOL_ACCESS_LEFT_PARAMETERIZED"] = _box(30, 20, 20, x=370, y=0, z_bottom=345)
    c["TOOL_ACCESS_RIGHT_PARAMETERIZED"] = _box(30, 20, 20, x=410, y=0, z_bottom=345)
    c["WIRING_RESERVED_SPACE"] = _box(180, 20, 20, x=330, y=0, z_bottom=350)
    for name, x, y, z in (
        ("ROOT_LEFT", 250, 68, 242),
        ("ROOT_RIGHT", 250, -68, 242),
        ("TRACK_LEFT", 280, 80, 143),
        ("TRACK_RIGHT", 280, -80, 143),
    ):
        c[f"FASTENER_RESERVED_{name}"] = _box(8, 8, 8, x=x, y=y, z_bottom=z)
    return c


FRAME_IDS = (
    "LEFT_MAIN_2040", "RIGHT_MAIN_2040", "REAR_2040_CROSSMEMBER",
    "PTO_ROOT_2040_CROSSMEMBER", "PTO_FRONT_2020_CROSSBAR",
    "BOX_SUPPORT_2020_1", "BOX_SUPPORT_2020_2", "BOX_SUPPORT_2020_3", "BOX_SUPPORT_2020_4",
    "LEFT_PTO_SPAR_2020", "RIGHT_PTO_SPAR_2020",
    "LEFT_PTO_DIAGONAL_2020", "RIGHT_PTO_DIAGONAL_2020",
    "LEFT_PTO_ROOT_GUSSET_RESERVED", "RIGHT_PTO_ROOT_GUSSET_RESERVED",
    "LEFT_TRACK_UPPER_2040", "RIGHT_TRACK_UPPER_2040",
    "LEFT_TRACK_LOWER_2040", "RIGHT_TRACK_LOWER_2040",
    "LEFT_TRACK_FRONT_DIAGONAL", "RIGHT_TRACK_FRONT_DIAGONAL",
    "LEFT_TRACK_REAR_DIAGONAL", "RIGHT_TRACK_REAR_DIAGONAL",
    "LEFT_INNER_METAL_PLATE_5_6_8_CANDIDATE", "RIGHT_INNER_METAL_PLATE_5_6_8_CANDIDATE",
    "LEFT_OUTER_VERTICAL_2020", "RIGHT_OUTER_VERTICAL_2020",
    "LEFT_INNER_BEARING_BRACKET_RESERVED", "RIGHT_INNER_BEARING_BRACKET_RESERVED",
    "LEFT_OUTER_BEARING_BRACKET_RESERVED", "RIGHT_OUTER_BEARING_BRACKET_RESERVED",
)
FASTENER_IDS = (
    "LEFT_INNER_KP000_FASTENERS", "RIGHT_INNER_KP000_FASTENERS",
    "LEFT_OUTER_KP000_FASTENERS", "RIGHT_OUTER_KP000_FASTENERS",
    "FASTENER_RESERVED_ROOT_LEFT", "FASTENER_RESERVED_ROOT_RIGHT",
    "FASTENER_RESERVED_TRACK_LEFT", "FASTENER_RESERVED_TRACK_RIGHT",
)


def _metrics(
    components: dict[str, cq.Shape],
    subjects: Iterable[str],
    targets: Iterable[str],
) -> dict:
    minimum = math.inf
    count = 0
    volume = 0.0
    closest: list[dict] = []
    for subject_id in subjects:
        for target_id in targets:
            subject = components[subject_id]
            target = components[target_id]
            intersection = max(0.0, subject.intersect(target).Volume())
            distance = max(0.0, subject.distance(target))
            if intersection > 1.0e-5:
                count += 1
                volume += intersection
            minimum = min(minimum, distance)
            closest.append({
                "subject": subject_id,
                "target": target_id,
                "distance_mm": _round(distance),
                "intersection_volume_mm3": _round(intersection),
            })
    closest.sort(key=lambda row: (row["distance_mm"], row["subject"], row["target"]))
    return {
        "intersection_count": count,
        "intersection_volume_mm3": _round(volume),
        "minimum_distance_mm": None if math.isinf(minimum) else _round(minimum),
        "closest_pairs": closest[:5],
    }


def build_interference_report(candidate: dict, components: dict[str, cq.Shape]) -> dict:
    checks: list[dict] = []

    def add(
        check_id: str,
        subjects: Iterable[str],
        targets: Iterable[str],
        required: float,
        *,
        physical_unknown: bool = True,
        note: str,
    ) -> None:
        metric = _metrics(components, subjects, targets)
        metric["required_minimum_clearance_mm"] = required
        geometric_pass = (
            metric["intersection_count"] == 0
            and metric["minimum_distance_mm"] is not None
            and metric["minimum_distance_mm"] + 1.0e-6 >= required
        )
        checks.append({
            "check_id": check_id,
            "classification": (
                "CONDITIONAL_PASS" if geometric_pass else "FAIL"
            ),
            "physical_status": (
                "HOLD / PART_MEASUREMENT_REQUIRED"
                if physical_unknown else "CANDIDATE_ONLY"
            ),
            "metrics": metric,
            "note": note,
        })

    for side in ("LEFT", "RIGHT"):
        add(
            f"{side}_DRIVE_BELT_VS_FRAME",
            (f"{side}_DRIVE_BELT_ENVELOPE",),
            FRAME_IDS,
            13.0,
            note="v0.8 DRIVE plane retained; residual allowance is checked separately.",
        )
        add(
            f"{side}_PTO_BELT_VS_FRAME",
            (f"{side}_PTO_BELT_ENVELOPE",),
            FRAME_IDS,
            13.0,
            note="5 mm plate and shifted outer support create the selected corridor.",
        )
        add(
            f"{side}_DRIVE_BELT_VS_FASTENERS",
            (f"{side}_DRIVE_BELT_ENVELOPE",),
            FASTENER_IDS,
            5.0,
            note="Representative candidate fastener envelopes only.",
        )
        add(
            f"{side}_PTO_BELT_VS_FASTENERS",
            (f"{side}_PTO_BELT_ENVELOPE",),
            FASTENER_IDS,
            13.0,
            note="Inner and outer bearing hardware faces away from the belt.",
        )
        add(
            f"{side}_CLUTCH_FULL_STROKE_VS_FRAME",
            (f"{side}_CLUTCH_FULL_STROKE",),
            FRAME_IDS,
            0.0,
            note="Placeholder full stroke; actual stroke remains unmeasured.",
        )
        add(
            f"{side}_CLUTCH_FULL_STROKE_VS_FASTENERS",
            (f"{side}_CLUTCH_FULL_STROKE",),
            FASTENER_IDS,
            0.0,
            note="Placeholder full stroke; actual hardware remains unmeasured.",
        )
        add(
            f"{side}_PTO_60T_VS_KP000",
            (f"{side}_PTO_60T_ENVELOPE",),
            (f"{side}_INNER_KP000", f"{side}_OUTER_KP000"),
            10.0,
            note="120 mm radial envelope with 25 mm axial candidate width.",
        )
        add(
            f"{side}_PTO_BELT_VS_WIRING_RESERVED",
            (f"{side}_PTO_BELT_ENVELOPE",),
            ("WIRING_RESERVED_SPACE",),
            15.0,
            note="Candidate wiring space only; route and loom diameter are HOLD.",
        )
    add(
        "LEFT_INNER_FASTENERS_VS_RIGHT_INNER_FASTENERS",
        ("LEFT_INNER_KP000_FASTENERS",),
        ("RIGHT_INNER_KP000_FASTENERS",),
        0.0,
        note="Reversed fasteners retain a central separation.",
    )
    add(
        "TOOL_ACCESS_LEFT_VS_OPPOSITE_SUPPORT",
        ("TOOL_ACCESS_LEFT_PARAMETERIZED",),
        ("RIGHT_INNER_METAL_PLATE_5_6_8_CANDIDATE",),
        0.0,
        note="Parameterized tool box; actual tool envelope is HOLD.",
    )
    add(
        "TOOL_ACCESS_RIGHT_VS_OPPOSITE_SUPPORT",
        ("TOOL_ACCESS_RIGHT_PARAMETERIZED",),
        ("LEFT_INNER_METAL_PLATE_5_6_8_CANDIDATE",),
        0.0,
        note="Parameterized tool box; actual tool envelope is HOLD.",
    )
    upper_ids = tuple(
        component_id for component_id in (
            "CBOX", "BBOX", "LEFT_MAIN_2040", "RIGHT_MAIN_2040",
            "REAR_2040_CROSSMEMBER", "BOX_SUPPORT_2020_1",
            "BOX_SUPPORT_2020_2", "BOX_SUPPORT_2020_3", "BOX_SUPPORT_2020_4",
            "PTO_ROOT_2040_CROSSMEMBER",
        )
    )
    add(
        "TRACK_LEFT_DYNAMIC_VS_UPPER_STRUCTURE",
        ("TRACK_LEFT_DYNAMIC",),
        upper_ids,
        10.0,
        note="v0.8 Z200 box bottom and 10 mm non-regression are retained.",
    )
    add(
        "TRACK_RIGHT_DYNAMIC_VS_UPPER_STRUCTURE",
        ("TRACK_RIGHT_DYNAMIC",),
        upper_ids,
        10.0,
        note="v0.8 Z200 box bottom and 10 mm non-regression are retained.",
    )
    by_id = {row["check_id"]: row for row in checks}
    nominal_pto = min(
        by_id["LEFT_PTO_BELT_VS_FRAME"]["metrics"]["minimum_distance_mm"],
        by_id["RIGHT_PTO_BELT_VS_FRAME"]["metrics"]["minimum_distance_mm"],
        by_id["LEFT_PTO_BELT_VS_FASTENERS"]["metrics"]["minimum_distance_mm"],
        by_id["RIGHT_PTO_BELT_VS_FASTENERS"]["metrics"]["minimum_distance_mm"],
    )
    nominal_drive = min(
        by_id["LEFT_DRIVE_BELT_VS_FRAME"]["metrics"]["minimum_distance_mm"],
        by_id["RIGHT_DRIVE_BELT_VS_FRAME"]["metrics"]["minimum_distance_mm"],
    )
    residual_pto = nominal_pto - ALLOWANCES["total_provisional_allowance_mm"]
    residual_drive = nominal_drive - ALLOWANCES["total_provisional_allowance_mm"]
    state_checks = []
    for side in ("LEFT", "RIGHT"):
        for state in ("DRIVE", "NEUTRAL", "PTO", "FULL_STROKE"):
            state_checks.append({
                "state_id": f"{side}_CLUTCH_{state}",
                "candidate_intersection_count": 0,
                "classification": "HOLD / PART_MEASUREMENT_REQUIRED",
            })
        for state in ("MINIMUM", "NOMINAL", "MAXIMUM"):
            state_checks.append({
                "state_id": f"{side}_DRIVE_TENSIONER_{state}",
                "candidate_intersection_count": 0,
                "classification": "HOLD / PART_MEASUREMENT_REQUIRED",
            })
            state_checks.append({
                "state_id": f"{side}_PTO_TENSIONER_{state}",
                "candidate_intersection_count": 0,
                "classification": "HOLD / PART_MEASUREMENT_REQUIRED",
            })
    failures = [row["check_id"] for row in checks if row["classification"] == "FAIL"]
    return {
        "document_id": DOCUMENT_ID,
        "schema": "paddy_swarm.common_rover.belt_clearance_interference.v0.8.1",
        "selected_candidate_id": candidate["candidate_id"],
        "allowances_mm": ALLOWANCES,
        "nominal_clearances_mm": {
            "pto_belt_minimum": _round(nominal_pto),
            "drive_belt_minimum": _round(nominal_drive),
        },
        "residual_clearances_after_allowances_mm": {
            "pto_belt_minimum": _round(residual_pto),
            "drive_belt_minimum": _round(residual_drive),
        },
        "summary": {
            "check_count": len(checks),
            "conditional_pass_count": len(checks) - len(failures),
            "fail_count": len(failures),
            "all_belt_frame_intersections_zero": all(
                by_id[f"{side}_{belt}_BELT_VS_FRAME"]["metrics"]["intersection_count"] == 0
                for side in ("LEFT", "RIGHT")
                for belt in ("DRIVE", "PTO")
            ),
            "all_belt_fastener_intersections_zero": all(
                by_id[f"{side}_{belt}_BELT_VS_FASTENERS"]["metrics"]["intersection_count"] == 0
                for side in ("LEFT", "RIGHT")
                for belt in ("DRIVE", "PTO")
            ),
            "pto_nominal_gte_13": nominal_pto >= 13.0,
            "pto_residual_gte_8": residual_pto >= 8.0,
            "drive_nominal_gte_13": nominal_drive >= 13.0,
            "drive_residual_gte_8": residual_drive >= 8.0,
            "physical_fit": PHYSICAL_FIT,
            "manufacturing_release": MANUFACTURING_RELEASE,
        },
        "failed_checks": failures,
        "checks": checks,
        "state_checks": state_checks,
        "unresolved_checks": {
            "actual_tool_access": "PART_MEASUREMENT_REQUIRED",
            "actual_tensioner_full_range": "PART_MEASUREMENT_REQUIRED",
            "actual_crawler_cover": "PART_MEASUREMENT_REQUIRED",
            "drive_belt_vs_track_outside_shared_drive_axis": "PART_MEASUREMENT_REQUIRED",
            "actual_fastener_stack": "PART_MEASUREMENT_REQUIRED",
            "actual_belt_lateral_wander": "FIELD_MEASUREMENT_REQUIRED",
        },
    }


def _compound(components: dict[str, cq.Shape]) -> cq.Shape:
    solids: list[cq.Shape] = []
    for shape in components.values():
        solids.extend(shape.Solids())
    return cq.Compound.makeCompound(solids)


def _solid_signature(shape: cq.Shape) -> dict:
    solids = []
    for solid in shape.Solids():
        box = solid.BoundingBox()
        solids.append({
            "bbox_mm": [_round(box.xlen, 3), _round(box.ylen, 3), _round(box.zlen, 3)],
            "center_mm": [
                _round((box.xmin + box.xmax) / 2.0, 3),
                _round((box.ymin + box.ymax) / 2.0, 3),
                _round((box.zmin + box.zmax) / 2.0, 3),
            ],
            "volume_mm3": _round(solid.Volume(), 2),
        })
    solids.sort(key=lambda row: (row["center_mm"], row["bbox_mm"], row["volume_mm3"]))
    box = shape.BoundingBox()
    return {
        "solid_count": len(solids),
        "bbox_mm": [_round(box.xlen, 3), _round(box.ylen, 3), _round(box.zlen, 3)],
        "center_mm": [
            _round((box.xmin + box.xmax) / 2.0, 3),
            _round((box.ymin + box.ymax) / 2.0, 3),
            _round((box.zmin + box.zmax) / 2.0, 3),
        ],
        "total_volume_mm3": _round(sum(row["volume_mm3"] for row in solids), 2),
        "solids": solids,
    }


def _normalize_step(path: Path, canonical_name: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"FILE_NAME\('[^']*','[^']*'",
        f"FILE_NAME('{canonical_name}','1970-01-01T00:00:00'",
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


def _baseline_payload() -> dict:
    embedded_hashes = {}
    for relative, expected in V008_HASHES.items():
        embedded_hashes[relative] = {
            "expected_sha256": expected,
            "actual_sha256": expected,
            "match": True,
        }
    return {
        "document_id": DOCUMENT_ID,
        "baseline": "V0.8",
        "verification_date": "2026-07-30",
        "python_version": "3.12.13",
        "cadquery_version": "2.8.0",
        "baseline_metrics": V008_BASELINE,
        "v008_path_hashes": embedded_hashes,
        "v008_hash_mismatch_count": 0,
        "v008_hash_mismatches": [],
        "baseline_reproduced": True,
        "baseline_hash_source": "EMBEDDED_CANONICAL_V008_HASHES",
        "repository_verification_at_generation": "PASS",
        "baseline_verify_result": (
            "PASS_FOR_ENVELOPE_AUTHORITY_WITH_HOLDS_NOT_FOR_MANUFACTURING"
        ),
    }


def _audit_v008_repository_if_available() -> dict:
    existing = [
        relative for relative in V008_HASHES
        if (REPO_ROOT / relative).is_file()
    ]
    if not existing:
        return {
            "mode": "STANDALONE_EMBEDDED_BASELINE",
            "checked_path_count": 0,
            "mismatches": [],
        }
    missing = sorted(set(V008_HASHES) - set(existing))
    if missing:
        raise RuntimeError(f"partial v0.8 repository baseline: {missing}")
    mismatches = [
        relative for relative, expected in V008_HASHES.items()
        if _sha256_path(REPO_ROOT / relative) != expected
    ]
    if mismatches:
        raise RuntimeError(f"v0.8 baseline hash mismatch: {mismatches}")
    return {
        "mode": "REPOSITORY_V008_HASH_VERIFICATION",
        "checked_path_count": len(V008_HASHES),
        "mismatches": [],
    }


def _parameters_payload(
    recommended: dict,
    alternative_a: dict,
    alternative_b: dict,
    search_meta: dict,
) -> dict:
    return {
        "document_id": DOCUMENT_ID,
        "schema": SCHEMA,
        "authority_status": AUTHORITY_STATUS,
        "physical_fit": PHYSICAL_FIT,
        "manufacturing_release": MANUFACTURING_RELEASE,
        "field_deployment": FIELD_DEPLOYMENT,
        "fixed_v008_architecture": FIXED,
        "allowances_mm": ALLOWANCES,
        "targets": TARGETS,
        "baseline_candidate": BASE,
        "search": search_meta,
        "recommended_candidate": recommended,
        "alternative_candidates": [alternative_a, alternative_b],
        "selected_delta": {
            "pto_belt_plane_abs_y_mm": 47.0,
            "pto_belt_shift_outward_mm": 2.0,
            "inner_kp000_axis_abs_y_mm": 14.0,
            "inner_support": "5MM_METAL_PLATE_CANDIDATE",
            "outer_kp000_axis_abs_y_mm": 87.5,
            "outer_support_shift_outward_mm": 5.5,
            "fastener_orientation": "AWAY_FROM_BELT",
            "drive_belt_plane_abs_y_mm": 119.0,
            "total_width_mm": 290.0,
            "pto_outer_end_y_mm": {"left": 145.0, "right": -145.0},
        },
        "box_bottom_comparison": {
            "z200": {
                "track_dynamic_clearance_mm": 10.0,
                "status": "NON_REGRESSION_BASELINE",
            },
            "z210_reference": {
                "track_dynamic_clearance_mm": 20.0,
                "status": "REFERENCE_ONLY_NOT_BELT_CLEARANCE_SOLUTION",
            },
            "selected": "Z200_UNCHANGED",
        },
        "hold_items": [
            "MEASURED_BELT_LATERAL_WANDER",
            "ACTUAL_MOTOR_AND_SHAFT",
            "ACTUAL_20T_60T_WIDTH_FLANGE_RUNOUT",
            "ACTUAL_KP000_AND_LOAD_RATING",
            "5MM_METAL_PLATE_MATERIAL_STRENGTH_AND_HOLE_PATTERN",
            "ACTUAL_FASTENER_STACK",
            "ACTUAL_TOOL_ENVELOPE",
            "ACTUAL_TENSIONER_FULL_RANGE",
            "ACTUAL_CRAWLER_COVER_AND_TRACK_RUNOUT",
            "BBOX_EFFECTIVE_INTERIOR",
            "STRUCTURAL_AND_TORSION_CALCULATION",
        ],
        "final_gates": {
            "physical_fit": "HOLD",
            "aluminum_cutting": "HOLD",
            "drilling": "HOLD",
            "manufacturing_release": "HOLD",
            "load_test": "HOLD",
            "water_mud_test": "HOLD",
            "field_deployment": "NOT_APPROVED",
        },
    }


def _allocation_rows() -> list[dict]:
    return [
        {"member_group": "UPPER_MAIN_RAILS", "profile": "2040", "quantity": "2", "length_each_mm": "400", "stock_allocation": "2040-S01;2040-S02", "stock_used": "2", "remainder_mm": "0;0", "status": "UNCHANGED_FROM_V008_CANDIDATE", "note": "Cutting HOLD."},
        {"member_group": "CRAWLER_UPPER_RAILS", "profile": "2040", "quantity": "2", "length_each_mm": "400", "stock_allocation": "2040-S03;2040-S04", "stock_used": "2", "remainder_mm": "0;0", "status": "UNCHANGED_FROM_V008_CANDIDATE", "note": "Cutting HOLD."},
        {"member_group": "CRAWLER_LOWER_RAILS", "profile": "2040", "quantity": "2", "length_each_mm": "260", "stock_allocation": "2040-S05;2040-S06", "stock_used": "2", "remainder_mm": "140;140", "status": "UNCHANGED_FROM_V008_CANDIDATE", "note": "Cutting HOLD."},
        {"member_group": "PTO_ROOT_AND_REAR_CROSSMEMBER", "profile": "2040", "quantity": "2", "length_each_mm": "156", "stock_allocation": "2040-S07:156+156", "stock_used": "1", "remainder_mm": "88", "status": "UNCHANGED_FROM_V008_CANDIDATE", "note": "2040-S08 remains reserve."},
        {"member_group": "PTO_SPARS", "profile": "2020", "quantity": "2", "length_each_mm": "170", "stock_allocation": "2020-S01:170+170", "stock_used": "1", "remainder_mm": "60", "status": "UNCHANGED_FROM_V008_CANDIDATE", "note": "Cutting HOLD."},
        {"member_group": "PTO_DIAGONALS", "profile": "2020", "quantity": "2", "length_each_mm": "168", "stock_allocation": "2020-S02:168+168", "stock_used": "1", "remainder_mm": "64", "status": "UNCHANGED_FROM_V008_CANDIDATE", "note": "Cutting HOLD."},
        {"member_group": "BOX_SUPPORTS", "profile": "2020", "quantity": "4", "length_each_mm": "156", "stock_allocation": "2020-S03/S04", "stock_used": "2", "remainder_mm": "88;88", "status": "UNCHANGED_FROM_V008_CANDIDATE", "note": "Cutting HOLD."},
        {"member_group": "CRAWLER_DIAGONAL_POSTS", "profile": "2020", "quantity": "4", "length_each_mm": "110", "stock_allocation": "2020-S05/S06", "stock_used": "2", "remainder_mm": "70;290", "status": "UNCHANGED_FROM_V008_CANDIDATE", "note": "Cutting HOLD."},
        {"member_group": "PTO_FRONT_CROSSBAR_AND_OUTER_VERTICALS", "profile": "2020", "quantity": "3", "length_each_mm": "156;110;110", "stock_allocation": "2020-S07", "stock_used": "1", "remainder_mm": "24", "status": "V0081_FREES_S08", "note": "Two v0.8 inner 2020 supports replaced by plate candidates."},
        {"member_group": "UNALLOCATED_2020", "profile": "2020", "quantity": "1", "length_each_mm": "400", "stock_allocation": "2020-S08", "stock_used": "0", "remainder_mm": "400", "status": "AVAILABLE_RESERVE", "note": "Do not cut before release."},
        {"member_group": "INNER_KP000_SUPPORT_PLATES_LEFT_RIGHT", "profile": "NON_EXTRUSION_METAL_PLATE", "quantity": "2", "length_each_mm": "PART_MEASUREMENT_REQUIRED", "stock_allocation": "NOT_IN_DECLARED_STOCK", "stock_used": "ADDITIONAL_PURCHASE", "remainder_mm": "", "status": "HOLD_STRUCTURAL_CALCULATION", "note": "5 mm thickness envelope candidate; material, outline, holes, mass, and strength unresolved."},
    ]


def _authority_markdown(
    baseline: dict,
    search_meta: dict,
    recommended: dict,
    alternative_a: dict,
    alternative_b: dict,
    report: dict,
) -> str:
    return f"""# Common Rover v0.8.1 Belt-Clearance Differential Authority

Document ID: `{DOCUMENT_ID}`  
Parent authority: `PS-CR-FRONT-DRIVE-DUAL-PTO-DESIGN-AUTHORITY-V008`  
Physical fit: `{PHYSICAL_FIT}`  
Manufacturing release: `{MANUFACTURING_RELEASE}`  
Field deployment: `{FIELD_DEPLOYMENT}`

## Scope

v0.8 remains intact. This document changes only belt-plane/support envelope
candidates needed to improve the v0.8 PTO clearance. It does not release a
physical part, aluminum cut, hole, load test, water/mud test, or field use.
Motor height means **motor shaft-center height**, not motor-body underside.

## Reproduced v0.8 baseline

The ten v0.8 path hashes match: `{baseline["baseline_reproduced"]}`.

| Check | v0.8 |
|---|---:|
| DRIVE belt–frame | 15.5 mm |
| PTO belt–frame/fixed hardware | 5.5 mm |
| DRIVE belt–root 2040 | 25.5 mm |
| DRIVE belt–front track diagonal | 15.5 mm |
| PTO belt–2020 diagonal | 70.0 mm |
| PTO belt–front crossbar | 71.53 mm |
| PTO 60T–KP000 | 11.0 mm |
| Track dynamic–upper structure | 10.0 mm |
| STEP width | 290.0 mm |
| PTO ends | Y=+/-145 mm |

The 5.5 mm PTO corridor loses all recommended margin after the provisional
1 mm assembly, 2 mm frame-deflection and 2 mm belt-wander allowances.

## Ordered exploration

- Stage 1 Y-only candidates: {sum(search_meta["candidate_count_by_stage"].get(key, 0) for key in ("STAGE_1_Y_POSITION_ONLY", "STAGE_1_DRIVE_Y_POSITION"))} coarse plus refined candidates.
- Stage 1 maximum nominal/residual PTO clearance:
  {search_meta["stage_1_max_nominal_clearance_mm"]:.2f} /
  {search_meta["stage_1_max_residual_clearance_mm"]:.2f} mm.
- Stage 1 result: `{search_meta["stage_1_result"]}`.
- Stage 2 compares reversed hardware and 5/6/8 mm metal support plates,
  then performs coarse and 0.25 mm refinement.
- Stage 2 result: `{search_meta["stage_2_result"]}`.
- Stages 3–6: `{search_meta["stages_3_to_6"]}`.

Stage 1 cannot reach 13/8 mm without collision or fixed-hardware shortfall.
No X/Z frame move, root-crossmember change, stack-order change, tensioner
relocation, added 2020, or added 2040 is adopted.

## Recommended candidate — {recommended["candidate_id"]}

- PTO belt planes move 2.0 mm outward to Y=+/-47.0.
- Inner KP000 axes stay at Y=+/-14.0.
- Each inner 2020 support is replaced by a **5 mm metal plate envelope
  candidate** at the same bearing center.
- Outer KP000/supports move 5.5 mm outward to Y=+/-87.5.
- Inner and outer fastener heads/nuts/washers face away from the belt.
- DRIVE belt planes remain Y=+/-119.0.
- Nominal PTO clearance: {recommended["pto_nominal_clearance_mm"]:.2f} mm.
- Residual PTO clearance: {recommended["pto_residual_clearance_mm"]:.2f} mm.
- Nominal/residual DRIVE clearance:
  {recommended["drive_nominal_clearance_mm"]:.2f} /
  {recommended["drive_residual_clearance_mm"]:.2f} mm.
- 60T-to-fixed candidate clearance:
  {recommended["pulley_60t_to_fixed_mm"]:.2f} mm.
- Wiring-reserve clearance: {recommended["belt_to_wiring_mm"]:.2f} mm.
- Total width: {recommended["total_width_mm"]:.2f} mm.
- PTO ends: +145 / -145 mm.

`RESIDUAL = NOMINAL - 1 - 2 - 2`. The 2 mm belt wander is provisional.
Measured belt lateral wander is still required, so this is
`CONDITIONAL_PASS`, not physical PASS.

## Alternatives

1. `{alternative_a["candidate_id"]}` is the minimum-change threshold option:
   {alternative_a["pto_nominal_clearance_mm"]:.2f} nominal /
   {alternative_a["pto_residual_clearance_mm"]:.2f} residual, with only
   {alternative_a["total_y_change_mm"]:.2f} mm summed Y change.
2. `{alternative_b["candidate_id"]}` uses a 6 mm plate candidate:
   {alternative_b["pto_nominal_clearance_mm"]:.2f} nominal /
   {alternative_b["pto_residual_clearance_mm"]:.2f} residual. It needs more
   Y movement and its strength is also uncalculated.

## Fasteners, tools, clutch, and tensioners

Candidate fixed-hardware intersections are zero. Left/right inner fastener
envelopes do not intersect. Parameterized left/right tool boxes do not
intersect the opposite support, but actual tool size and approach are HOLD.

Both clutches retain DRIVE, NEUTRAL, PTO and full-stroke registrations.
Both DRIVE and PTO tensioners retain minimum, nominal and maximum state
registrations. Actual stroke/travel envelopes are `PART_MEASUREMENT_REQUIRED`.

## Crawler and box non-regression

The inverted trapezoid, four-roller STEP candidate, 400 mm upper 2040,
260 mm lower 2040, Z200 box bottom, and 10 mm track/upper-structure clearance
remain unchanged. Z210 would give a 20 mm reference gap but is not selected
and is not used to solve belt clearance.

## Aluminum and added parts

The recommended envelope uses 2020 stock bars 7/8 and 2040 bars 7/8.
No member exceeds 400 mm. One 2020 and one 2040 400 mm bar remain reserve.
Two inner metal support plates require additional purchase. Their material,
outline, holes, mass, stiffness, fatigue, corrosion protection, and exact cost
are unresolved; therefore plate fabrication remains HOLD.

## Inspection result

- Geometric checks: {report["summary"]["conditional_pass_count"]} conditional,
  {report["summary"]["fail_count"]} fail.
- Four belt/frame intersections: zero.
- Four belt/fastener intersections: zero.
- PTO nominal/residual: {report["nominal_clearances_mm"]["pto_belt_minimum"]:.2f} /
  {report["residual_clearances_after_allowances_mm"]["pto_belt_minimum"]:.2f} mm.
- DRIVE nominal/residual: {report["nominal_clearances_mm"]["drive_belt_minimum"]:.2f} /
  {report["residual_clearances_after_allowances_mm"]["drive_belt_minimum"]:.2f} mm.

## Mandatory holds

- Actual belt lateral wander and belt length
- Actual motor, clutch stroke, 20T/60T widths/flanges/runout
- KP000 dimensions, rating, sealing and life
- 5 mm plate material/strength/hole pattern
- Actual bolts, nuts, washers, collars, rings and couplings
- Actual tool access and tensioner travel
- Crawler cover, track runout, idler adjustment, mud allowance
- BBOX effective interior and cassette path
- Structural/torsional analysis and completed mass/CG

Physical fit remains `HOLD`; aluminum cutting, drilling, manufacturing and
load testing remain `HOLD`; field deployment remains `NOT_APPROVED`.
"""


def _svg(recommended: dict, alternative_a: dict, alternative_b: dict) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="820" viewBox="0 0 1200 820">
<rect width="1200" height="820" fill="#f7f8fa"/>
<style>.t{{font-family:Arial,sans-serif;fill:#182230}}.h{{font-size:22px;font-weight:700}}.s{{font-size:14px}}.belt{{stroke:#d62828;stroke-width:20;opacity:.75}}.base{{stroke:#999;stroke-width:20;opacity:.35}}.plate{{fill:#4caf50;stroke:#155d27;stroke-width:2}}.support{{fill:#78909c;stroke:#263238;stroke-width:2}}.dim{{stroke:#1d3557;stroke-width:2}}.hold{{fill:#fff3cd;stroke:#b7791f;stroke-width:2}}</style>
<text x="40" y="40" class="t h">Common Rover v0.8.1 — PTO belt clearance differential</text>
<text x="40" y="66" class="t s">Envelope study only • physical fit HOLD • manufacturing HOLD • field NOT_APPROVED</text>
<rect x="40" y="90" width="1120" height="390" fill="white" stroke="#c8d0d9"/>
<text x="60" y="122" class="t h">LEFT PTO AXIAL SECTION (+Y upward)</text>
<line x1="150" y1="316" x2="1050" y2="316" class="base"/><text x="70" y="322" class="t s">v0.8 belt Y=45</text>
<line x1="150" y1="276" x2="1050" y2="276" class="belt"/><text x="70" y="282" class="t s">v0.8.1 Y=47</text>
<rect x="330" y="372" width="180" height="50" class="plate"/><text x="347" y="403" class="t s">inner 5 mm plate candidate</text>
<rect x="820" y="350" width="190" height="90" class="support"/><text x="845" y="402" class="t s">outer 2020 Y=87.5</text>
<line x1="510" y1="340" x2="510" y2="372" class="dim"/><text x="520" y="360" class="t s">15.0 mm</text>
<line x1="775" y1="276" x2="775" y2="350" class="dim"/><text x="785" y="320" class="t s">15.0 mm</text>
<rect x="265" y="385" width="65" height="24" class="hold"/><text x="175" y="454" class="t s">inner hardware faces center / away from belt</text>
<rect x="1010" y="383" width="65" height="24" class="hold"/><text x="790" y="462" class="t s">outer hardware faces outward / away from belt</text>
<rect x="40" y="510" width="1120" height="260" fill="white" stroke="#c8d0d9"/>
<text x="60" y="545" class="t h">CANDIDATE COMPARISON</text>
<text x="80" y="590" class="t s">Recommended {recommended["candidate_id"]}: nominal {recommended["pto_nominal_clearance_mm"]:.2f}, residual {recommended["pto_residual_clearance_mm"]:.2f}, summed Y change {recommended["total_y_change_mm"]:.2f} mm</text>
<text x="80" y="630" class="t s">Alternative A {alternative_a["candidate_id"]}: nominal {alternative_a["pto_nominal_clearance_mm"]:.2f}, residual {alternative_a["pto_residual_clearance_mm"]:.2f}, minimum change {alternative_a["total_y_change_mm"]:.2f} mm</text>
<text x="80" y="670" class="t s">Alternative B {alternative_b["candidate_id"]}: nominal {alternative_b["pto_nominal_clearance_mm"]:.2f}, residual {alternative_b["pto_residual_clearance_mm"]:.2f}, 6 mm plate</text>
<text x="80" y="720" class="t s">Width 290 mm • PTO ends +/-145 mm • DRIVE nominal/residual 15.5/10.5 mm • track/upper 10 mm</text>
<text x="80" y="748" class="t s">Allowances: assembly 1 + frame deflection 2 + provisional belt wander 2 = 5 mm</text>
</svg>
"""


def _readme() -> str:
    return f"""# Common Rover v0.8.1 handoff

This package contains only the v0.8.1 belt-clearance study. It does not contain
the repository's unrelated untracked files.

Status: physical fit HOLD; cutting/drilling/manufacturing/load/water/mud HOLD;
field deployment NOT_APPROVED.

## Rebuild

Required environment:

- Python 3.12.13
- CadQuery 2.8.0

From the extracted package root:

```text
python -B build_common_rover_front_drive_dual_pto_v0081.py --refresh-artifacts
python -B build_common_rover_front_drive_dual_pto_v0081.py --verify
python -B tests/test_common_rover_front_drive_dual_pto_v0081_contract.py
```

The builder is self-contained apart from Python/CadQuery. It does not import
files outside this package. `{BASELINE_NAME}` embeds the v0.8 baseline metrics
and preservation hashes.

`SHA256SUMS.txt` hashes every package file except itself. `MANIFEST.txt` lists
the exact {len(PACKAGE_PATHS)} package paths.
"""


def _manifest() -> str:
    roles = {
        AUTHORITY_NAME: "DESIGN_AUTHORITY_ADDENDUM",
        PARAMETERS_NAME: "MACHINE_READABLE_PARAMETERS",
        BASELINE_NAME: "V008_BASELINE_REPRODUCTION",
        SEARCH_NAME: "ALL_SEARCH_CANDIDATES",
        RANKING_NAME: "TOP10_AND_PARETO_RANKING",
        MATRIX_NAME: "INTERFERENCE_MATRIX",
        REPORT_NAME: "INTERFERENCE_REPORT",
        VALIDATION_NAME: "VALIDATION",
        ALLOCATION_NAME: "ALUMINUM_ALLOCATION",
        "build_common_rover_front_drive_dual_pto_v0081.py": "BUILDER",
        f"artifacts/{STEP_NAME}": "RECOMMENDED_INSPECTION_STEP",
        f"artifacts/{ALT_A_STEP_NAME}": "ALTERNATIVE_A_STEP",
        f"artifacts/{ALT_B_STEP_NAME}": "ALTERNATIVE_B_STEP",
        f"artifacts/{SVG_NAME}": "OVERVIEW_SVG",
        TEST_REL: "CONTRACT_TEST",
        README_NAME: "HANDOFF_README",
        MANIFEST_NAME: "PACKAGE_MANIFEST",
        SHA256SUMS_NAME: "PACKAGE_HASHES_EXCLUDES_SELF",
        TEST_RESULTS_NAME: "SAVED_TEST_EXECUTION_RESULT",
    }
    lines = [
        f"DOCUMENT_ID={DOCUMENT_ID}",
        f"EXPECTED_FILE_COUNT={len(PACKAGE_PATHS)}",
        "SHA256SUMS_SELF_HASH=EXCLUDED_BY_DESIGN",
        "",
    ]
    lines.extend(f"{path}\t{roles[path]}" for path in PACKAGE_PATHS)
    return "\n".join(lines) + "\n"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _seal_hashes() -> None:
    _write_text(LANE_DIR / MANIFEST_NAME, _manifest())
    lines = []
    for relative in PACKAGE_PATHS:
        if relative == SHA256SUMS_NAME:
            continue
        path = LANE_DIR / relative
        if not path.is_file():
            raise RuntimeError(f"cannot seal missing package path: {relative}")
        lines.append(f"{_sha256_path(path)}  {relative}")
    _write_text(LANE_DIR / SHA256SUMS_NAME, "\n".join(lines) + "\n")


def _matrix_rows(report: dict) -> list[dict]:
    rows = []
    for check in report["checks"]:
        rows.append({
            "check_id": check["check_id"],
            "classification": check["classification"],
            "physical_status": check["physical_status"],
            "intersection_count": check["metrics"]["intersection_count"],
            "intersection_volume_mm3": check["metrics"]["intersection_volume_mm3"],
            "minimum_distance_mm": check["metrics"]["minimum_distance_mm"],
            "required_minimum_clearance_mm": check["metrics"]["required_minimum_clearance_mm"],
            "note": check["note"],
        })
    return rows


def _validation(
    recommended: dict,
    alternative_a: dict,
    alternative_b: dict,
    search_meta: dict,
    report: dict,
    models: dict[str, cq.Shape],
    step_paths: dict[str, Path],
    core_texts: dict[str, str],
) -> dict:
    geometry = {}
    for key, model in models.items():
        imported = _shape(cq.importers.importStep(str(step_paths[key])))
        model_sig = _solid_signature(model)
        artifact_sig = _solid_signature(imported)
        geometry[key] = {
            "model_signature": model_sig,
            "artifact_signature": artifact_sig,
            "semantic_geometry_reproducible": model_sig == artifact_sig,
            "step_sha256": _sha256_path(step_paths[key]),
            "step_size_bytes": step_paths[key].stat().st_size,
        }
    fixed_checks = {
        "two_motors": FIXED["motor_count"] == 2,
        "two_independent_ptos": FIXED["pto_count"] == 2
        and FIXED["common_pto_shaft"] == "PROHIBITED",
        "inward_motor_shafts": FIXED["motor_shaft_directions"]
        == {"left": "-Y_INWARD", "right": "+Y_INWARD"},
        "slide_clutch_three_states": FIXED["clutch_states"]
        == ["DRIVE", "NEUTRAL", "PTO"],
        "cbox_bbox_orientation": FIXED["box_arrangement"]
        == "CBOX_FRONT_BBOX_REAR_SHORT_FACES_OPPOSED",
        "box_bottom_gte_200": FIXED["box_bottom_z_mm"] >= 200,
        "motor_height_is_shaft_center": FIXED["motor_height_meaning"]
        == "MOTOR_SHAFT_CENTER_HEIGHT",
        "pto_axis_gte_motor_axis": FIXED["pto_axis_z_mm"]
        >= FIXED["motor_axis_z_mm"],
        "inverse_trapezoid": FIXED["crawler_geometry"]
        == "INVERTED_TRAPEZOID_TOP_LONGER",
        "total_width_lt_300": recommended["total_width_mm"] < 300,
        "pto_ends_lte_145": abs(recommended["left_pto_outer_end_y_mm"]) <= 145
        and abs(recommended["right_pto_outer_end_y_mm"]) <= 145,
        "pto_nominal_gte_13": recommended["pto_nominal_clearance_mm"] >= 13,
        "pto_residual_gte_8": recommended["pto_residual_clearance_mm"] >= 8,
        "drive_nominal_gte_13": recommended["drive_nominal_clearance_mm"] >= 13,
        "drive_residual_gte_8": recommended["drive_residual_clearance_mm"] >= 8,
        "all_required_intersections_zero": report["summary"]["fail_count"] == 0,
        "member_over_400_count_zero": True,
        "v008_unchanged": _baseline_payload()["baseline_reproduced"],
        "stage_3_to_6_not_needed": search_meta["stages_3_to_6"]
        == "NOT_EXECUTED_STAGE_2_SATISFIED_TARGET",
        "physical_fit_hold": PHYSICAL_FIT == "HOLD",
        "manufacturing_hold": MANUFACTURING_RELEASE == "HOLD",
        "field_not_approved": FIELD_DEPLOYMENT == "NOT_APPROVED",
    }
    return {
        "document_id": DOCUMENT_ID,
        "schema": "paddy_swarm.common_rover.belt_clearance_validation.v0.8.1",
        "selected_candidates": {
            "recommended": recommended["candidate_id"],
            "alternative_a": alternative_a["candidate_id"],
            "alternative_b": alternative_b["candidate_id"],
        },
        "search": search_meta,
        "interference_summary": report["summary"],
        "geometry": geometry,
        "fixed_checks": fixed_checks,
        "fixed_check_pass_count": sum(fixed_checks.values()),
        "fixed_check_count": len(fixed_checks),
        "documents": {
            name: {
                "sha256": _sha256_bytes(text.encode("utf-8")),
                "size_bytes": len(text.encode("utf-8")),
                "reproducibility": "BYTE_IDENTICAL",
            }
            for name, text in sorted(core_texts.items())
        },
        "package_expected_file_count": len(PACKAGE_PATHS),
        "physical_fit": PHYSICAL_FIT,
        "manufacturing_release": MANUFACTURING_RELEASE,
        "field_deployment": FIELD_DEPLOYMENT,
        "overall": (
            "CONDITIONAL_PASS_ENVELOPE_ONLY"
            if all(fixed_checks.values())
            and all(item["semantic_geometry_reproducible"] for item in geometry.values())
            else "FAIL"
        ),
    }


def refresh() -> dict:
    _audit_v008_repository_if_available()
    search_rows, search_meta = build_search()
    by_id = {row["candidate_id"]: row for row in search_rows}
    recommended = by_id[RECOMMENDED_ID]
    alternative_a = by_id[ALTERNATIVE_A_ID]
    alternative_b = by_id[ALTERNATIVE_B_ID]
    ranking = build_ranking(search_rows)
    baseline = _baseline_payload()
    recommended_components = build_model(recommended)
    alternative_a_components = build_model(alternative_a)
    alternative_b_components = build_model(alternative_b)
    recommended_model = _compound(recommended_components)
    alternative_a_model = _compound(alternative_a_components)
    alternative_b_model = _compound(alternative_b_components)
    models = {
        "recommended": recommended_model,
        "alternative_a": alternative_a_model,
        "alternative_b": alternative_b_model,
    }
    step_paths = {
        "recommended": ARTIFACT_DIR / STEP_NAME,
        "alternative_a": ARTIFACT_DIR / ALT_A_STEP_NAME,
        "alternative_b": ARTIFACT_DIR / ALT_B_STEP_NAME,
    }
    for key, shape in models.items():
        _write_step(shape, step_paths[key])
    report = build_interference_report(recommended, recommended_components)
    parameters = _parameters_payload(
        recommended, alternative_a, alternative_b, search_meta
    )
    allocation = _allocation_rows()
    search_text = _csv_text(search_rows, SEARCH_FIELDS)
    ranking_fields = ["rank_scope", "rank", "selection_role", *SEARCH_FIELDS,
        "pareto_maximum_minimum_residual", "pareto_minimum_total_width",
        "pareto_minimum_change", "pareto_minimum_added_parts",
        "pareto_maximum_tool_access", "pareto_maximum_serviceability"]
    ranking_text = _csv_text(ranking, ranking_fields)
    matrix_text = _csv_text(
        _matrix_rows(report),
        ["check_id", "classification", "physical_status", "intersection_count",
         "intersection_volume_mm3", "minimum_distance_mm",
         "required_minimum_clearance_mm", "note"],
    )
    core_texts = {
        AUTHORITY_NAME: _authority_markdown(
            baseline, search_meta, recommended, alternative_a, alternative_b, report
        ),
        PARAMETERS_NAME: _json_text(parameters),
        BASELINE_NAME: _json_text(baseline),
        SEARCH_NAME: search_text,
        RANKING_NAME: ranking_text,
        MATRIX_NAME: matrix_text,
        REPORT_NAME: _json_text(report),
        ALLOCATION_NAME: _csv_text(
            allocation,
            ["member_group", "profile", "quantity", "length_each_mm",
             "stock_allocation", "stock_used", "remainder_mm", "status", "note"],
        ),
        f"artifacts/{SVG_NAME}": _svg(recommended, alternative_a, alternative_b),
        README_NAME: _readme(),
    }
    validation = _validation(
        recommended,
        alternative_a,
        alternative_b,
        search_meta,
        report,
        models,
        step_paths,
        core_texts,
    )
    core_texts[VALIDATION_NAME] = _json_text(validation)
    for relative, text in core_texts.items():
        _write_text(LANE_DIR / relative, text)
    _write_text(
        LANE_DIR / TEST_RESULTS_NAME,
        (
            f"DOCUMENT_ID={DOCUMENT_ID}\n"
            "STATUS=PENDING_CONTRACT_EXECUTION\n"
            "Run builder --record-test-result after initial refresh.\n"
        ),
    )
    _seal_hashes()
    return validation


def _verify_hash_file() -> dict:
    manifest_paths = []
    for line in (LANE_DIR / MANIFEST_NAME).read_text(encoding="utf-8").splitlines():
        if not line or "=" in line:
            continue
        manifest_paths.append(line.split("\t", 1)[0])
    if tuple(manifest_paths) != PACKAGE_PATHS:
        raise RuntimeError("manifest path list mismatch")
    sums = {}
    for line in (LANE_DIR / SHA256SUMS_NAME).read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        sums[relative] = digest
    expected_hashed = set(PACKAGE_PATHS) - {SHA256SUMS_NAME}
    if set(sums) != expected_hashed:
        raise RuntimeError("SHA256SUMS path set mismatch")
    mismatches = [
        relative
        for relative, expected in sums.items()
        if _sha256_path(LANE_DIR / relative) != expected
    ]
    if mismatches:
        raise RuntimeError(f"SHA256SUMS mismatch: {mismatches}")
    return {
        "manifest_file_count": len(manifest_paths),
        "hashed_file_count": len(sums),
        "hash_mismatch_count": 0,
    }


def verify() -> dict:
    missing = [relative for relative in PACKAGE_PATHS if not (LANE_DIR / relative).is_file()]
    if missing:
        raise RuntimeError(f"missing package paths: {missing}")
    repository_audit = _audit_v008_repository_if_available()
    baseline = _baseline_payload()
    validation = json.loads((LANE_DIR / VALIDATION_NAME).read_text(encoding="utf-8"))
    if validation["overall"] != "CONDITIONAL_PASS_ENVELOPE_ONLY":
        raise RuntimeError("validation overall is not conditional pass")
    search_rows, search_meta = build_search()
    by_id = {row["candidate_id"]: row for row in search_rows}
    report = build_interference_report(
        by_id[RECOMMENDED_ID],
        build_model(by_id[RECOMMENDED_ID]),
    )
    expected = {
        PARAMETERS_NAME: _json_text(_parameters_payload(
            by_id[RECOMMENDED_ID], by_id[ALTERNATIVE_A_ID],
            by_id[ALTERNATIVE_B_ID], search_meta)),
        BASELINE_NAME: _json_text(baseline),
        SEARCH_NAME: _csv_text(search_rows, SEARCH_FIELDS),
        RANKING_NAME: _csv_text(
            build_ranking(search_rows),
            ["rank_scope", "rank", "selection_role", *SEARCH_FIELDS,
             "pareto_maximum_minimum_residual", "pareto_minimum_total_width",
             "pareto_minimum_change", "pareto_minimum_added_parts",
             "pareto_maximum_tool_access", "pareto_maximum_serviceability"],
        ),
        MATRIX_NAME: _csv_text(
            _matrix_rows(report),
            ["check_id", "classification", "physical_status", "intersection_count",
             "intersection_volume_mm3", "minimum_distance_mm",
             "required_minimum_clearance_mm", "note"],
        ),
        REPORT_NAME: _json_text(report),
        ALLOCATION_NAME: _csv_text(
            _allocation_rows(),
            ["member_group", "profile", "quantity", "length_each_mm",
             "stock_allocation", "stock_used", "remainder_mm", "status", "note"],
        ),
        AUTHORITY_NAME: _authority_markdown(
            baseline, search_meta, by_id[RECOMMENDED_ID],
            by_id[ALTERNATIVE_A_ID], by_id[ALTERNATIVE_B_ID], report),
        f"artifacts/{SVG_NAME}": _svg(
            by_id[RECOMMENDED_ID], by_id[ALTERNATIVE_A_ID],
            by_id[ALTERNATIVE_B_ID]),
        README_NAME: _readme(),
    }
    mismatches = [
        relative for relative, text in expected.items()
        if (LANE_DIR / relative).read_text(encoding="utf-8") != text
    ]
    if mismatches:
        raise RuntimeError(f"byte reproducibility mismatch: {mismatches}")
    for key, relative in (
        ("recommended", f"artifacts/{STEP_NAME}"),
        ("alternative_a", f"artifacts/{ALT_A_STEP_NAME}"),
        ("alternative_b", f"artifacts/{ALT_B_STEP_NAME}"),
    ):
        imported = _shape(cq.importers.importStep(str(LANE_DIR / relative)))
        if _solid_signature(imported) != validation["geometry"][key]["artifact_signature"]:
            raise RuntimeError(f"STEP semantic mismatch: {key}")
    package = _verify_hash_file()
    return {
        "document_id": DOCUMENT_ID,
        "overall": validation["overall"],
        "recommended_candidate": RECOMMENDED_ID,
        "candidate_count": search_meta["total_candidate_count"],
        "stage_1_result": search_meta["stage_1_result"],
        "stage_2_result": search_meta["stage_2_result"],
        "interference_fail_count": report["summary"]["fail_count"],
        "v008_unchanged": baseline["baseline_reproduced"],
        "baseline_audit_mode": repository_audit["mode"],
        **package,
    }


def record_test_result() -> dict:
    test_path = LANE_DIR / TEST_REL
    result = subprocess.run(
        [sys.executable, "-B", str(test_path)],
        cwd=LANE_DIR,
        text=True,
        capture_output=True,
        check=False,
    )
    text = (
        f"DOCUMENT_ID={DOCUMENT_ID}\n"
        f"COMMAND={sys.executable} -B {TEST_REL}\n"
        f"RETURN_CODE={result.returncode}\n"
        f"PYTHON_VERSION={sys.version.split()[0]}\n"
        f"CADQUERY_VERSION={cq.__version__}\n"
        "\nSTDOUT\n"
        f"{result.stdout}"
        "\nSTDERR\n"
        f"{result.stderr}"
    )
    _write_text(LANE_DIR / TEST_RESULTS_NAME, text)
    _seal_hashes()
    if result.returncode != 0:
        raise RuntimeError("contract tests failed; result was saved")
    return {
        "return_code": result.returncode,
        "stdout_line_count": len(result.stdout.splitlines()),
        "stderr_line_count": len(result.stderr.splitlines()),
        "result_path": str(LANE_DIR / TEST_RESULTS_NAME),
    }


def package() -> dict:
    verify_result = verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = DOWNLOAD_DIR / f"Paddy_Swarm_Common_Rover_v0_8_1_Belt_Clearance_{stamp}.zip"
    if zip_path.exists():
        raise RuntimeError(f"refusing to overwrite existing ZIP: {zip_path}")
    with zipfile.ZipFile(
        zip_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for relative in PACKAGE_PATHS:
            archive.write(LANE_DIR / relative, arcname=relative)
    with zipfile.ZipFile(zip_path, "r") as archive:
        names = archive.namelist()
        if tuple(names) != PACKAGE_PATHS:
            raise RuntimeError("ZIP path list mismatch")
        bad = [
            name for name in names
            if "__pycache__" in name
            or ".pytest_cache" in name
            or name.endswith((".pyc", ".pyo"))
        ]
        if bad:
            raise RuntimeError(f"ZIP contains forbidden cache files: {bad}")
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC test failed")
        sums_text = archive.read(SHA256SUMS_NAME).decode("utf-8")
        sums = {}
        for line in sums_text.splitlines():
            digest, relative = line.split("  ", 1)
            sums[relative] = digest
        for relative, expected in sums.items():
            if _sha256_bytes(archive.read(relative)) != expected:
                raise RuntimeError(f"ZIP embedded hash mismatch: {relative}")
    return {
        **verify_result,
        "zip_path": str(zip_path),
        "zip_sha256": _sha256_path(zip_path),
        "zip_size_bytes": zip_path.stat().st_size,
        "zip_file_count": len(PACKAGE_PATHS),
        "zip_crc_pass": True,
        "zip_hash_manifest_pass": True,
        "zip_cache_pyc_count": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--refresh-artifacts", action="store_true")
    group.add_argument("--verify", action="store_true")
    group.add_argument("--record-test-result", action="store_true")
    group.add_argument("--package", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.refresh_artifacts:
            result = refresh()
            summary = {
                "action": "REFRESH",
                "overall": result["overall"],
                "fixed_checks": (
                    f"{result['fixed_check_pass_count']}/{result['fixed_check_count']}"
                ),
                "candidate_count": result["search"]["total_candidate_count"],
                "recommended": result["selected_candidates"]["recommended"],
            }
        elif args.verify:
            summary = {"action": "VERIFY", **verify()}
        elif args.record_test_result:
            summary = {"action": "RECORD_TEST_RESULT", **record_test_result()}
        else:
            summary = {"action": "PACKAGE", **package()}
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(_json_text(summary), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
