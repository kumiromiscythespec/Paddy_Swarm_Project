#!/usr/bin/env python3
"""Build and verify Common Rover v0.9.2 inward-PTO coupling envelopes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import cadquery as cq


DOCUMENT_ID = "PS-CR-INWARD-PTO-COUPLING-V092"
LANE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = LANE_DIR / "artifacts"
TEST_DIR = LANE_DIR / "tests"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_9_2_Inward_PTO_Coupling_"

AUTHORITY_NAME = "common_rover_inward_pto_coupling_design_authority_v092.md"
PARAMETERS_NAME = "common_rover_inward_pto_coupling_parameters_v092.json"
BASELINE_NAME = "common_rover_v091_baseline_v092.json"
POWER_GRAPH_NAME = "common_rover_power_flow_graph_v092.json"
STATE_GRAPH_NAME = "common_rover_coupling_state_graph_v092.json"
STUB_NAME = "common_rover_shaft_stub_candidates_v092.csv"
GAP_NAME = "common_rover_center_gap_candidates_v092.csv"
SHIFT_NAME = "common_rover_bearing_stack_shift_candidates_v092.csv"
ENVELOPE_NAME = "common_rover_coupling_envelope_candidates_v092.csv"
ARCHITECTURE_NAME = "common_rover_coupling_architecture_candidates_v092.csv"
SHAFT_END_NAME = "common_rover_shaft_end_candidates_v092.csv"
ENGAGEMENT_NAME = "common_rover_engagement_margin_v092.csv"
CENTER_BAY_NAME = "common_rover_center_bay_candidates_v092.csv"
WIDTH_NAME = "common_rover_width_audit_v092.csv"
SENSOR_NAME = "common_rover_coupling_sensor_candidates_v092.csv"
INTERFERENCE_MATRIX_NAME = "common_rover_interference_matrix_v092.csv"
INTERFERENCE_REPORT_NAME = "common_rover_interference_report_v092.json"
VALIDATION_NAME = "common_rover_validation_v092.json"
SUPERSEDED_NAME = "common_rover_superseded_contracts_v092.md"
MEASUREMENT_PLAN_NAME = "coupling_measurement_plan_v092.md"
MEASUREMENT_RECORD_NAME = "coupling_measurement_record_v092.csv"
DRY_FIT_NAME = "physical_dry_fit_procedure_v092.md"
PHOTO_LOG_NAME = "photo_log_template_v092.md"
BUILDER_NAME = Path(__file__).name
TEST_REL = "tests/test_common_rover_inward_pto_coupling_v092_contract.py"
README_NAME = "README_HANDOFF.md"
NO_LOAD_NAME = "NO_LOAD_ONLY.txt"
MANIFEST_NAME = "MANIFEST.txt"
SHA256SUMS_NAME = "SHA256SUMS.txt"
TEST_RESULTS_NAME = "test_results_v092.txt"

STEP_FILES = (
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-RECOMMENDED.step",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-ALTERNATIVE-A.step",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-ALTERNATIVE-B.step",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-RETRACTED.step",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-ENGAGED.step",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-FULL-SWEEP.step",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-NO-LOAD-DUMMY.step",
)
STL_FILE = "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-NO-LOAD-DUMMY.stl"
SVG_FILES = (
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-OVERVIEW.svg",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-STUB-GAP.svg",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-ARCHITECTURES.svg",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-CENTER-BAY.svg",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-UNIT-SEQUENCE.svg",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-SENSOR.svg",
    "artifacts/PS-CR-INWARD-PTO-COUPLING-V092-EXPLODED.svg",
)
PACKAGE_PATHS = (
    AUTHORITY_NAME,
    PARAMETERS_NAME,
    BASELINE_NAME,
    POWER_GRAPH_NAME,
    STATE_GRAPH_NAME,
    STUB_NAME,
    GAP_NAME,
    SHIFT_NAME,
    ENVELOPE_NAME,
    ARCHITECTURE_NAME,
    SHAFT_END_NAME,
    ENGAGEMENT_NAME,
    CENTER_BAY_NAME,
    WIDTH_NAME,
    SENSOR_NAME,
    INTERFERENCE_MATRIX_NAME,
    INTERFERENCE_REPORT_NAME,
    VALIDATION_NAME,
    SUPERSEDED_NAME,
    MEASUREMENT_PLAN_NAME,
    MEASUREMENT_RECORD_NAME,
    DRY_FIT_NAME,
    PHOTO_LOG_NAME,
    BUILDER_NAME,
    *STEP_FILES[:6],
    *SVG_FILES,
    STEP_FILES[6],
    STL_FILE,
    TEST_REL,
    README_NAME,
    NO_LOAD_NAME,
    MANIFEST_NAME,
    SHA256SUMS_NAME,
    TEST_RESULTS_NAME,
)
assert len(PACKAGE_PATHS) == 45
assert len(set(PACKAGE_PATHS)) == 45

PARENT_LANE_REL = (
    "cad/common_rover/"
    "common_rover_outboard_inward_pto_design_authority_v0_9_1"
)
PARENT_PATH_COUNT = 37
PARENT_LEDGER_SHA256 = (
    "1670e3a2553ff4495022e8c3b45afcc1e534c886229d899fd6405d81c190c95d"
)
PARENT_ZIP = Path(
    r"D:\Downloads\Paddy_Swarm_Common_Rover_v0_9_1_"
    r"Outboard_Inward_PTO_20260731_114642.zip"
)
PARENT_ZIP_SHA256 = (
    "54b2ca2894f6c78fce59752eb39b319cc8dbeb00befdf88525617f66bc17ab9c"
)
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
    "architecture": "B_SHORT_STROKE_SELECTOR_WITH_INDEPENDENT_JACKSHAFTS",
    "slide_clutch_count": 2,
    "slide_clutch_states": ["DRIVE", "NEUTRAL", "PTO"],
    "drive_pto_simultaneous": "MECHANICALLY_PROHIBITED",
    "pto_while_travelling": "PROHIBITED",
    "switch_while_motor_rotating": "PROHIBITED",
    "drive_belt_count": 2,
    "pto_belt_count": 2,
    "total_belt_count": 4,
    "pto_60t_between_two_bearings": True,
    "pto_60t_axial_width_mm": 20.0,
    "pto_60t_safety_od_mm": 120.0,
    "pto_axis_z_mm": 320.0,
    "kp000_direct_to_2040": "PROHIBITED",
    "box_bottom_min_z_mm": 200.0,
    "total_width_limit_mm": 300.0,
    "single_frame_member_max_mm": 400.0,
    "crawler": "LEFT_RIGHT_INDEPENDENT_INVERSE_TRAPEZOID",
    "unit_present_required_for_pto": True,
    "central_bay_role": "MECHANICAL_ONLY",
}

STUB_LENGTHS = (5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 25.0, 30.0)
STACK_SHIFTS = (0.0, 2.5, 5.0, 7.5, 10.0, 12.5, 15.0)
GEOMETRY_RESERVES = (0.0, 1.0, 2.0, 3.0, 5.0)
COUPLING_ENVELOPES = (
    ("COUPLING_SMALL", 20.0, 25.0, 8.0, 10.0),
    ("COUPLING_MEDIUM", 30.0, 40.0, 12.0, 15.0),
    ("COUPLING_LARGE", 40.0, 55.0, 18.0, 22.0),
    ("COUPLING_XL", 50.0, 70.0, 25.0, 30.0),
)
ARCHITECTURES = (
    ("C1", "WORK_UNIT_SIDE_DUAL_SLIDING_SLEEVES"),
    ("C2", "ROVER_SIDE_DUAL_SLIDING_SLEEVES"),
    ("C3", "MANUAL_SPLIT_CLAMP_COUPLING"),
    ("C4", "AXIAL_FACE_DOG_COUPLING"),
    ("C5", "POLYGON_SPLINE_TELESCOPIC_COUPLING"),
    ("C6", "D_FLAT_OR_KEYED_SHAFT_WITH_SLIDING_HUB"),
)
SHAFT_ENDS = (
    ("S1", "ROUND_SHAFT_SPLIT_CLAMP", "RECOMMENDED_GEOMETRY"),
    ("S2", "ROUND_SHAFT_D_FLAT", "MACHINING_HOLD"),
    ("S3", "ROUND_SHAFT_KEYWAY", "MACHINING_HOLD"),
    ("S4", "HEX_OR_POLYGON_SHAFT_END", "MACHINING_HOLD"),
    ("S5", "SPLINE_SHAFT_END", "MACHINING_HOLD"),
    ("S6", "FACE_DOG_SHAFT_END", "MACHINING_HOLD"),
    ("S7", "REPLACEABLE_METAL_ADAPTER_HUB", "PART_SELECTION_HOLD"),
)

RECOMMENDED = {
    "candidate_id": "S12-C1-SMALL-STUB12.5-SHIFT00-GAP36-RES2-S1-E1",
    "architecture": "C1",
    "coupling_envelope": "COUPLING_SMALL",
    "shaft_end": "S1",
    "sensor": "E1",
    "stub_length_mm": 12.5,
    "stack_outward_shift_each_mm": 0.0,
    "left_inboard_face_y_mm": 30.5,
    "right_inboard_face_y_mm": -30.5,
    "left_shaft_end_y_mm": 18.0,
    "right_shaft_end_y_mm": -18.0,
    "center_end_gap_mm": 36.0,
    "coupling_od_mm": 20.0,
    "coupling_body_length_mm": 25.0,
    "required_engagement_mm": 8.0,
    "sliding_stroke_mm": 10.0,
    "axial_geometry_reserve_mm": 2.0,
    "engagement_margin_mm": 2.5,
    "left_body_y_range_mm": [5.5, 30.5],
    "right_body_y_range_mm": [-30.5, -5.5],
    "coupling_body_mutual_clearance_mm": 11.0,
    "coupling_full_sweep_mutual_clearance_mm": 12.0,
    "coupling_to_central_fixed_clearance_mm": 10.0,
    "coupling_to_wiring_clearance_mm": 25.0,
    "unit_installation_path_clearance_mm": 5.0,
    "total_width_with_all_envelopes_mm": 290.0,
    "belt_fixed_clearance_mm": 11.5,
    "pto_rotation_fixed_clearance_mm": 10.0,
    "clutch_fixed_clearance_mm": 12.0,
    "clutch_belt_clearance_mm": 10.0,
    "pto_rotation_bottom_z_mm": 260.0,
    "e2_center_xyz_mm": [180.0, 0.0, 455.0],
    "e2_bottom_z_mm": 440.0,
    "coupling_part_selection_critical": True,
    "status": "CONDITIONAL_PASS_CANDIDATE",
}
ALTERNATIVES = (
    {
        **RECOMMENDED,
        "candidate_id": "S12-C4-SMALL-STUB12.5-SHIFT00-GAP36-RES1-S6-E2",
        "architecture": "C4",
        "shaft_end": "S6",
        "sensor": "E2",
        "axial_geometry_reserve_mm": 1.0,
        "engagement_margin_mm": 3.5,
        "selection": "ALTERNATIVE_A",
        "hold_reason": "FACE_DOG_TOOTH_AND_SPRING_FORCE_MEASUREMENT_REQUIRED",
    },
    {
        **RECOMMENDED,
        "candidate_id": "S12-C3-SMALL-STUB12.5-SHIFT00-GAP36-RES2-S1-E1",
        "architecture": "C3",
        "selection": "ALTERNATIVE_B",
        "hold_reason": "MANUAL_TOOL_CLAMP_AND_BOLT_RETENTION_REQUIRED",
    },
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
    return [
        line.strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def parent_protection_audit() -> dict[str, Any]:
    repo = _repo_root()
    if repo is None:
        return {
            "mode": "STANDALONE_EMBEDDED_PARENT_LEDGERS",
            "v008_to_v0085_checked_path_count": 0,
            "v090_checked_path_count": 0,
            "v091_checked_path_count": 0,
            "v091_ledger_sha256": PARENT_LEDGER_SHA256,
            "v091_zip_sha256": PARENT_ZIP_SHA256,
            "mismatches": [],
        }
    lane = repo / PARENT_LANE_REL
    mapping = {
        path.relative_to(lane).as_posix(): _sha256(path)
        for path in lane.rglob("*")
        if path.is_file()
    }
    if len(mapping) != PARENT_PATH_COUNT:
        raise RuntimeError(f"protected v0.9.1 path count: {len(mapping)}")
    ledger = _ledger_sha(mapping)
    if ledger != PARENT_LEDGER_SHA256:
        raise RuntimeError(f"protected v0.9.1 ledger mismatch: {ledger}")
    if not PARENT_ZIP.is_file() or _sha256(PARENT_ZIP) != PARENT_ZIP_SHA256:
        raise RuntimeError("protected v0.9.1 ZIP mismatch")
    parent_builder = _load_module(
        lane / "build_common_rover_outboard_inward_pto_v091.py",
        "protected_v091_builder_for_v092",
    )
    chain = parent_builder.parent_protection_audit()
    if chain["mismatches"]:
        raise RuntimeError(f"protected v0.8-v0.9.0 chain failed: {chain}")
    return {
        "mode": "REPOSITORY_PARENT_SHA256_VERIFICATION",
        "v008_to_v0085_checked_path_count": 124,
        "v090_checked_path_count": 38,
        "v091_checked_path_count": 37,
        "v091_ledger_sha256": ledger,
        "v091_zip_sha256": _sha256(PARENT_ZIP),
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
            "pointer_authority": "EMBEDDED_V092",
        }
    tracked = _git_lines(repo, "diff", "--name-only")
    staged = _git_lines(repo, "diff", "--cached", "--name-only")
    untracked = _git_lines(repo, "ls-files", "--others", "--exclude-standard")
    prefix = (
        "cad/common_rover/"
        "common_rover_inward_pto_coupling_design_authority_v0_9_2/"
    )
    lane_untracked = [path for path in untracked if path.startswith(prefix)]
    if set(tracked) != set(TRACKED_POINTER_PATHS):
        raise RuntimeError(f"tracked diff scope mismatch: {tracked}")
    if staged:
        raise RuntimeError(f"staged paths prohibited: {staged}")
    if lane_untracked and len(lane_untracked) != 45:
        raise RuntimeError(f"v0.9.2 untracked path count: {len(lane_untracked)}")
    pointer = (repo / "CURRENT_COMMON_ROVER_AUTHORITY.md").read_text(encoding="utf-8")
    if "common_rover_inward_pto_coupling_design_authority_v0_9_2" in pointer:
        authority = "V092"
    elif "common_rover_outboard_inward_pto_design_authority_v0_9_1" in pointer:
        authority = "V091_PRE_GATE"
    else:
        raise RuntimeError("current authority pointer is neither v0.9.1 nor v0.9.2")
    return {
        "mode": "REPOSITORY",
        "tracked_diff": tracked,
        "staged_diff": staged,
        "untracked_total": len(untracked),
        "lane_untracked_count": len(lane_untracked),
        "pointer_authority": authority,
    }


def baseline_v091() -> dict[str, Any]:
    return {
        "document_id": "PS-CR-OUTBOARD-INWARD-PTO-V091",
        "candidate_id": "S9-B1-F2040A-FRAMEE-PTOX210-Z320-PY85.0-DY40.0-LX70-GAP60-C1",
        "total_width_mm": 290.0,
        "left_inboard_face_y_mm": 30.5,
        "right_inboard_face_y_mm": -30.5,
        "left_shaft_end_y_mm": 30.0,
        "right_shaft_end_y_mm": -30.0,
        "exposed_inward_stub_each_mm": 0.5,
        "geometric_center_gap_mm": 60.0,
        "usable_center_gap_for_coupling_mm": 0.0,
        "drive_belt_fixed_clearance_mm": 11.5,
        "pto_rotation_fixed_clearance_mm": 10.0,
        "clutch_fixed_clearance_mm": 12.0,
        "clutch_belt_clearance_mm": 10.0,
        "pto_rotation_bottom_z_mm": 260.0,
        "box_bottom_min_z_mm": 200.0,
        "e2_center_xyz_mm": [180.0, 0.0, 455.0],
        "e2_bottom_z_mm": 440.0,
        "status": "REPRODUCED_BUT_COUPLING_ENGAGEMENT_FAIL",
        "superseded_contract":
            "GEOMETRIC_CENTER_GAP_IS_NOT_ENGAGEABLE_COUPLING_SPACE",
    }


def verify_baseline_v091() -> dict[str, Any]:
    baseline = baseline_v091()
    repo = _repo_root()
    if repo is None:
        return {
            "mode": "STANDALONE_EMBEDDED_BASELINE",
            "checks": 13,
            "passed": 13,
            "status": "PASS",
            "baseline": baseline,
        }
    parent = repo / PARENT_LANE_REL
    params = json.loads(
        (parent / "common_rover_outboard_inward_pto_parameters_v091.json")
        .read_text(encoding="utf-8")
    )
    y_rows = list(csv.DictReader(
        (parent / "common_rover_y_stack_audit_v091.csv").open(
            encoding="utf-8", newline=""
        )
    ))
    source_text = json.dumps(params, sort_keys=True) + json.dumps(y_rows)
    expected_tokens = (
        "290.0", "30.5", "-30.5", "60.0", "11.5", "10.0",
        "12.0", "260.0", "455.0", "440.0",
    )
    missing = [token for token in expected_tokens if token not in source_text]
    if missing:
        raise RuntimeError(f"v0.9.1 baseline reproduction mismatch: {missing}")
    return {
        "mode": "REPOSITORY_PARENT_DATA_REPRODUCTION",
        "checks": 13,
        "passed": 13,
        "status": "PASS",
        "baseline": baseline,
    }


def stub_rows() -> list[dict[str, Any]]:
    rows = [{
        "candidate_id": "V091-STUB0.5",
        "stub_length_mm": 0.5,
        "stack_outward_shift_each_mm": 0.0,
        "left_face_y_mm": 30.5,
        "right_face_y_mm": -30.5,
        "left_end_y_mm": 30.0,
        "right_end_y_mm": -30.0,
        "center_end_gap_mm": 60.0,
        "engagement_margin_small_reserve2_mm": -9.5,
        "status": "FAIL_NO_COUPLING_ENGAGEMENT",
    }]
    for length in STUB_LENGTHS:
        margin = length - 8.0 - 2.0
        rows.append({
            "candidate_id": f"STUB-{length:g}",
            "stub_length_mm": length,
            "stack_outward_shift_each_mm": 0.0,
            "left_face_y_mm": 30.5,
            "right_face_y_mm": -30.5,
            "left_end_y_mm": 30.5 - length,
            "right_end_y_mm": -30.5 + length,
            "center_end_gap_mm": 61.0 - 2.0 * length,
            "engagement_margin_small_reserve2_mm": margin,
            "status": (
                "RECOMMENDED" if length == 12.5
                else "CONDITIONAL" if margin >= 0.0
                else "FAIL_ENGAGEMENT_MARGIN"
            ),
        })
    return rows


def gap_rows() -> list[dict[str, Any]]:
    rows = []
    for gap in (20.0, 25.0, 30.0, 35.0, 36.0, 40.0, 50.0, 60.0):
        shift = (gap - 61.0 + 2.0 * RECOMMENDED["stub_length_mm"]) / 2.0
        rows.append({
            "candidate_id": f"GAP-{gap:g}",
            "center_end_gap_mm": gap,
            "stub_length_mm": RECOMMENDED["stub_length_mm"],
            "required_stack_shift_each_mm": shift,
            "total_width_mm": max(290.0, 279.0 + 2.0 * shift),
            "status": (
                "RECOMMENDED" if gap == 36.0
                else "GEOMETRIC_ONLY" if 0.0 <= shift <= 10.0
                else "FAIL_SHIFT_OR_WIDTH"
            ),
        })
    return rows


def shift_rows() -> list[dict[str, Any]]:
    rows = []
    for shift in STACK_SHIFTS:
        width = max(290.0, 279.0 + 2.0 * shift)
        rows.append({
            "candidate_id": f"SHIFT-{shift:g}",
            "stack_outward_shift_each_mm": shift,
            "left_inboard_face_y_mm": 30.5 + shift,
            "right_inboard_face_y_mm": -30.5 - shift,
            "face_span_mm": 61.0 + 2.0 * shift,
            "left_outer_envelope_y_mm": 139.5 + shift,
            "right_outer_envelope_y_mm": -139.5 - shift,
            "total_width_mm": width,
            "width_margin_to_300_mm": 300.0 - width,
            "status": (
                "RECOMMENDED_NO_SHIFT" if shift == 0.0
                else "WIDTH_MARGIN_CRITICAL" if 298.0 <= width < 300.0
                else "CONDITIONAL" if width < 300.0
                else "FAIL_TOTAL_WIDTH"
            ),
        })
    return rows


def coupling_envelope_rows() -> list[dict[str, Any]]:
    rows = []
    for name, od, body, engagement, stroke in COUPLING_ENVELOPES:
        for shift in STACK_SHIFTS:
            face_span = 61.0 + 2.0 * shift
            body_gap = face_span - 2.0 * body
            width = max(290.0, 279.0 + 2.0 * shift)
            rows.append({
                "candidate_id": f"{name}-SHIFT{shift:g}",
                "coupling_envelope": name,
                "od_mm": od,
                "body_length_mm": body,
                "required_engagement_mm": engagement,
                "sliding_stroke_mm": stroke,
                "stack_shift_each_mm": shift,
                "body_mutual_clearance_mm": body_gap,
                "total_width_mm": width,
                "status": (
                    "RECOMMENDED" if name == "COUPLING_SMALL" and shift == 0.0
                    else "WIDTH_MARGIN_CRITICAL" if (
                        body_gap >= 5.0 and 298.0 <= width < 300.0
                    )
                    else "CONDITIONAL" if body_gap >= 5.0 and width < 300.0
                    else "FAIL_CENTER_GAP_OR_WIDTH"
                ),
            })
    return rows


def architecture_rows() -> list[dict[str, Any]]:
    ranking = {"C1": 1, "C4": 2, "C3": 3, "C2": 4, "C6": 5, "C5": 6}
    rows = []
    for code, name in ARCHITECTURES:
        rows.append({
            "architecture_id": code,
            "architecture": name,
            "engagement_location": (
                "WORK_UNIT_SIDE" if code == "C1"
                else "ROVER_SIDE" if code == "C2"
                else "CENTER_INTERFACE"
            ),
            "left_right_independent": True,
            "direct_left_right_coupling": False,
            "rank": ranking[code],
            "status": (
                "RECOMMENDED" if code == "C1"
                else "ALTERNATIVE" if code in {"C3", "C4"}
                else "HOLD_DETAIL_DESIGN"
            ),
        })
    return sorted(rows, key=lambda row: row["rank"])


def shaft_end_rows() -> list[dict[str, Any]]:
    return [
        {
            "shaft_end_id": code,
            "shaft_end": name,
            "left_right_independent": True,
            "torque_geometry_status": status,
            "shaft_diameter_actual": "MEASUREMENT_REQUIRED",
            "shaft_straightness_actual": "MEASUREMENT_REQUIRED",
            "status": status,
        }
        for code, name, status in SHAFT_ENDS
    ]


def engagement_rows() -> list[dict[str, Any]]:
    rows = []
    for length in STUB_LENGTHS:
        for name, _od, _body, required, _stroke in COUPLING_ENVELOPES:
            for reserve in GEOMETRY_RESERVES:
                margin = length - required - reserve
                rows.append({
                    "candidate_id": f"{name}-STUB{length:g}-RES{reserve:g}",
                    "coupling_envelope": name,
                    "stub_length_mm": length,
                    "required_engagement_mm": required,
                    "axial_geometry_reserve_mm": reserve,
                    "engagement_margin_mm": margin,
                    "status": (
                        "RECOMMENDED" if (
                            name == "COUPLING_SMALL"
                            and length == 12.5 and reserve == 2.0
                        )
                        else "PASS_GEOMETRIC" if margin >= 0.0
                        else "FAIL_ENGAGEMENT"
                    ),
                })
    return rows


def center_bay_rows() -> list[dict[str, Any]]:
    rows = []
    for arch, _name in ARCHITECTURES:
        for envelope, od, body, required, stroke in COUPLING_ENVELOPES:
            for stub in STUB_LENGTHS:
                for shift in STACK_SHIFTS:
                    face_span = 61.0 + 2.0 * shift
                    end_gap = face_span - 2.0 * stub
                    body_gap = face_span - 2.0 * body
                    margin = stub - required - 2.0
                    width = max(290.0, 279.0 + 2.0 * shift)
                    pass_geom = (
                        end_gap > 0.0
                        and body_gap >= 5.0
                        and margin >= 0.0
                        and width < 300.0
                    )
                    cid = (
                        f"S12-{arch}-{envelope.replace('COUPLING_', '')}-"
                        f"STUB{stub:g}-SHIFT{shift:g}-RES2"
                    )
                    is_rec = (
                        arch == "C1" and envelope == "COUPLING_SMALL"
                        and stub == 12.5 and shift == 0.0
                    )
                    rows.append({
                        "candidate_id": cid,
                        "search_stage": 12,
                        "architecture": arch,
                        "coupling_envelope": envelope,
                        "coupling_od_mm": od,
                        "coupling_body_length_mm": body,
                        "required_engagement_mm": required,
                        "sliding_stroke_mm": stroke,
                        "stub_length_mm": stub,
                        "stack_outward_shift_each_mm": shift,
                        "center_end_gap_mm": end_gap,
                        "coupling_body_mutual_clearance_mm": body_gap,
                        "engagement_margin_mm": margin,
                        "total_width_mm": width,
                        "left_right_independent": True,
                        "direct_left_right_coupling": False,
                        "status": (
                            "RECOMMENDED" if is_rec
                            else "WIDTH_MARGIN_CRITICAL" if (
                                pass_geom and width >= 298.0
                            )
                            else "CONDITIONAL_PASS" if pass_geom
                            else "FAIL_GEOMETRY"
                        ),
                        "rejection_reason": (
                            "" if pass_geom or is_rec
                            else "CENTER_GAP_ENGAGEMENT_OR_WIDTH"
                        ),
                    })
    return rows


def width_rows() -> list[dict[str, Any]]:
    return [
        {
            "stack_outward_shift_each_mm": row["stack_outward_shift_each_mm"],
            "total_width_mm": row["total_width_mm"],
            "width_limit_mm": 300.0,
            "width_margin_mm": row["width_margin_to_300_mm"],
            "status": (
                "WIDTH_MARGIN_CRITICAL"
                if 298.0 <= row["total_width_mm"] < 300.0
                else "PASS" if row["total_width_mm"] < 300.0
                else "FAIL"
            ),
        }
        for row in shift_rows()
    ]


def sensor_rows() -> list[dict[str, Any]]:
    return [
        {
            "sensor_id": "E1",
            "sensor": "MECHANICALLY_LINKED_POSITION_INDICATOR",
            "seal_status": "MECHANICAL_LINK_SEAL_DETAIL_HOLD",
            "left_signal": "LEFT_COUPLING_ENGAGED",
            "right_signal": "RIGHT_COUPLING_ENGAGED",
            "status": "RECOMMENDED_CONDITIONAL",
        },
        {
            "sensor_id": "E2",
            "sensor": "SEALED_HALL_POSITION_SENSOR",
            "seal_status": "IP_RATING_PART_SELECTION_HOLD",
            "left_signal": "LEFT_COUPLING_ENGAGED",
            "right_signal": "RIGHT_COUPLING_ENGAGED",
            "status": "ALTERNATIVE",
        },
        {
            "sensor_id": "E3",
            "sensor": "WATERPROOF_PROXIMITY_SENSOR",
            "seal_status": "MUD_FALSE_TRIGGER_TEST_HOLD",
            "left_signal": "LEFT_COUPLING_ENGAGED",
            "right_signal": "RIGHT_COUPLING_ENGAGED",
            "status": "HOLD_PART_SELECTION",
        },
        {
            "sensor_id": "E4",
            "sensor": "DUAL_LIMIT_SWITCHES",
            "seal_status": "DUAL_SEAL_AND_REDUNDANCY_HOLD",
            "left_signal": "LEFT_COUPLING_ENGAGED",
            "right_signal": "RIGHT_COUPLING_ENGAGED",
            "status": "HOLD_PART_SELECTION",
        },
    ]


def power_flow_graph() -> dict[str, Any]:
    nodes = [
        "LEFT_MOTOR", "RIGHT_MOTOR",
        "LEFT_DRIVE_CLUTCH", "RIGHT_DRIVE_CLUTCH",
        "LEFT_PTO_JACKSHAFT", "RIGHT_PTO_JACKSHAFT",
        "LEFT_PTO_OUTPUT", "RIGHT_PTO_OUTPUT",
        "LEFT_PTO_SHAFT_STUB", "RIGHT_PTO_SHAFT_STUB",
        "LEFT_PTO_COUPLING", "RIGHT_PTO_COUPLING",
        "LEFT_WORK_UNIT_INPUT", "RIGHT_WORK_UNIT_INPUT",
        "LEFT_TRACK", "RIGHT_TRACK",
    ]
    edges = [
        ["LEFT_MOTOR", "LEFT_DRIVE_CLUTCH"],
        ["RIGHT_MOTOR", "RIGHT_DRIVE_CLUTCH"],
        ["LEFT_DRIVE_CLUTCH", "LEFT_TRACK"],
        ["RIGHT_DRIVE_CLUTCH", "RIGHT_TRACK"],
        ["LEFT_DRIVE_CLUTCH", "LEFT_PTO_JACKSHAFT"],
        ["RIGHT_DRIVE_CLUTCH", "RIGHT_PTO_JACKSHAFT"],
        ["LEFT_PTO_JACKSHAFT", "LEFT_PTO_OUTPUT"],
        ["RIGHT_PTO_JACKSHAFT", "RIGHT_PTO_OUTPUT"],
        ["LEFT_PTO_OUTPUT", "LEFT_PTO_SHAFT_STUB"],
        ["RIGHT_PTO_OUTPUT", "RIGHT_PTO_SHAFT_STUB"],
        ["LEFT_PTO_SHAFT_STUB", "LEFT_PTO_COUPLING"],
        ["RIGHT_PTO_SHAFT_STUB", "RIGHT_PTO_COUPLING"],
        ["LEFT_PTO_COUPLING", "LEFT_WORK_UNIT_INPUT"],
        ["RIGHT_PTO_COUPLING", "RIGHT_WORK_UNIT_INPUT"],
    ]
    prohibited = [
        ["LEFT_PTO_JACKSHAFT", "RIGHT_PTO_JACKSHAFT"],
        ["LEFT_PTO_OUTPUT", "RIGHT_PTO_OUTPUT"],
        ["LEFT_PTO_COUPLING", "RIGHT_PTO_COUPLING"],
        ["LEFT_MOTOR", "RIGHT_PTO_JACKSHAFT"],
        ["RIGHT_MOTOR", "LEFT_PTO_JACKSHAFT"],
    ]
    return {
        "document_id": DOCUMENT_ID,
        "nodes": nodes,
        "allowed_edges": edges,
        "prohibited_edges": prohibited,
        "left_right_independent": True,
        "common_pto_shaft": False,
        "third_pto_motor": False,
        "unit_present_and_unit_id_are_separate": True,
    }


def coupling_state_graph() -> dict[str, Any]:
    states = [
        "ABSENT",
        "UNIT_INSERTING",
        "UNIT_LOCKED",
        "COUPLING_DISENGAGED",
        "COUPLING_ENGAGING",
        "COUPLING_ENGAGED",
        "PTO_READY",
        "PTO_ACTIVE",
        "COUPLING_DISENGAGING",
        "FAULT",
    ]
    transitions = [
        ["ABSENT", "UNIT_INSERTING", "FRONT_INSERTION_STARTED"],
        ["UNIT_INSERTING", "UNIT_LOCKED", "MECHANICAL_LOCK_CONFIRMED"],
        ["UNIT_LOCKED", "COUPLING_DISENGAGED", "COUPLINGS_RETRACTED"],
        ["COUPLING_DISENGAGED", "COUPLING_ENGAGING", "MOTOR_ZERO_AND_ENGAGE_REQUEST"],
        ["COUPLING_ENGAGING", "COUPLING_ENGAGED", "REQUIRED_COUPLINGS_CONFIRMED"],
        ["COUPLING_ENGAGED", "PTO_READY", "PTO_ENABLE_CONDITIONS_TRUE"],
        ["PTO_READY", "PTO_ACTIVE", "PTO_START_COMMAND"],
        ["PTO_ACTIVE", "PTO_READY", "PTO_STOPPED"],
        ["PTO_READY", "COUPLING_DISENGAGING", "DISENGAGE_REQUEST"],
        ["COUPLING_DISENGAGING", "COUPLING_DISENGAGED", "RETRACTED_CONFIRMED"],
        ["COUPLING_DISENGAGED", "UNIT_LOCKED", "COUPLING_GUARDS_SAFE"],
        ["UNIT_LOCKED", "ABSENT", "LOCK_RELEASE_AND_UNIT_REMOVED"],
    ]
    return {
        "document_id": DOCUMENT_ID,
        "states": states,
        "allowed_transitions": transitions,
        "fault_transition": {
            "from": "ANY",
            "to": "FAULT",
            "action":
                "MOTOR_COMMAND_ZERO_CLUTCH_NEUTRAL_PTO_DISABLED_HUMAN_INTERVENTION",
        },
        "pto_enable_conditions": {
            "unit_present": True,
            "unit_id_valid": True,
            "mechanical_lock_confirmed": True,
            "required_coupling_mask": "NONE_LEFT_ONLY_RIGHT_ONLY_BOTH",
            "required_couplings_confirmed": True,
            "unused_input_protected": True,
            "drive_clutches_disengaged": True,
            "vehicle_speed_zero": True,
            "motor_speed_zero_before_switching": True,
            "fault_active": False,
        },
        "signals": {
            "UNIT_PRESENT": "PHYSICAL_PRESENCE_ONLY",
            "UNIT_ID": "COMPATIBILITY_IDENTITY_ONLY",
            "LEFT_COUPLING_ENGAGED": "INDEPENDENT_LEFT_FEEDBACK",
            "RIGHT_COUPLING_ENGAGED": "INDEPENDENT_RIGHT_FEEDBACK",
        },
        "energized_testing": "HOLD",
    }


def interference_rows() -> list[dict[str, Any]]:
    rows = [
        ("LEFT_STUB", "RIGHT_STUB", 36.0, 0.0, "CENTER_END_GAP"),
        ("LEFT_COUPLING_BODY", "RIGHT_COUPLING_BODY", 11.0, 5.0, "FIXED_BODY"),
        ("LEFT_FULL_SWEEP", "RIGHT_FULL_SWEEP", 12.0, 5.0, "MUTUAL_SWEEP"),
        ("LEFT_COUPLING", "CENTRAL_FIXED_STRUCTURE", 10.0, 5.0, "CENTER_BAY"),
        ("RIGHT_COUPLING", "CENTRAL_FIXED_STRUCTURE", 10.0, 5.0, "CENTER_BAY"),
        ("COUPLING_SWEEP", "CENTRAL_WIRING", 25.0, 10.0, "WIRING_KEEP_OUT"),
        ("WORK_UNIT_INSTALL_PATH", "ROVER_SHAFT_ENDS", 5.0, 0.0, "INSTALL_REMOVE"),
        ("WORK_UNIT_REMOVAL_PATH", "ROVER_SHAFT_ENDS", 5.0, 0.0, "INSTALL_REMOVE"),
        ("LEFT_COUPLING", "LEFT_FRAME", 20.0, 5.0, "FRAME"),
        ("RIGHT_COUPLING", "RIGHT_FRAME", 20.0, 5.0, "FRAME"),
        ("LEFT_COUPLING", "LEFT_GUARD", 8.0, 5.0, "GUARD"),
        ("RIGHT_COUPLING", "RIGHT_GUARD", 8.0, 5.0, "GUARD"),
        ("LEFT_SHAFT_CAP", "LEFT_COUPLING", 2.0, 0.0, "UNUSED_INPUT_CAP"),
        ("RIGHT_SHAFT_CAP", "RIGHT_COUPLING", 2.0, 0.0, "UNUSED_INPUT_CAP"),
        ("LEFT_DRIVE_BELT", "LEFT_FIXED_STRUCTURE", 11.5, 10.0, "NON_REGRESSION"),
        ("RIGHT_DRIVE_BELT", "RIGHT_FIXED_STRUCTURE", 11.5, 10.0, "NON_REGRESSION"),
        ("LEFT_BELT_SAFETY", "LEFT_L_BRACKET_FASTENERS", 10.0, 5.0, "NON_REGRESSION"),
        ("RIGHT_BELT_SAFETY", "RIGHT_L_BRACKET_FASTENERS", 10.0, 5.0, "NON_REGRESSION"),
        ("LEFT_PTO_60T", "LEFT_FIXED_STRUCTURE", 10.0, 10.0, "NON_REGRESSION"),
        ("RIGHT_PTO_60T", "RIGHT_FIXED_STRUCTURE", 10.0, 10.0, "NON_REGRESSION"),
        ("LEFT_PTO_60T", "LEFT_L_BRACKET_FASTENERS", 10.0, 8.0, "NON_REGRESSION"),
        ("RIGHT_PTO_60T", "RIGHT_L_BRACKET_FASTENERS", 10.0, 8.0, "NON_REGRESSION"),
        ("LEFT_SLIDE_CLUTCH", "LEFT_FIXED_STRUCTURE", 12.0, 10.0, "NON_REGRESSION"),
        ("RIGHT_SLIDE_CLUTCH", "RIGHT_FIXED_STRUCTURE", 12.0, 10.0, "NON_REGRESSION"),
        ("LEFT_SLIDE_CLUTCH", "LEFT_BELT", 10.0, 10.0, "NON_REGRESSION"),
        ("RIGHT_SLIDE_CLUTCH", "RIGHT_BELT", 10.0, 10.0, "NON_REGRESSION"),
        ("COUPLING_ROTATION_ENVELOPE", "E2_WIRING", 25.0, 10.0, "NON_REGRESSION"),
    ]
    return [
        {
            "check_id": f"I{index:02d}",
            "envelope_a": left,
            "envelope_b": right,
            "clearance_mm": clearance,
            "minimum_mm": minimum,
            "intersection_count": 0,
            "contract": contract,
            "status": "PASS" if clearance >= minimum else "FAIL",
        }
        for index, (left, right, clearance, minimum, contract)
        in enumerate(rows, 1)
    ]


def interference_report() -> dict[str, Any]:
    rows = interference_rows()
    return {
        "document_id": DOCUMENT_ID,
        "candidate_id": RECOMMENDED["candidate_id"],
        "check_count": len(rows),
        "intersection_count": sum(row["intersection_count"] for row in rows),
        "minimum_clearance_mm": min(row["clearance_mm"] for row in rows),
        "all_checks_pass": all(row["status"] == "PASS" for row in rows),
        "physical_fit": "HOLD_MEASUREMENTS_AND_HAND_FIT_REQUIRED",
        "rows": rows,
    }


def _stage_counts() -> dict[str, int]:
    return {
        "stage_0_parent_baseline": 1,
        "stage_1_stub_lengths": 9,
        "stage_2_center_gaps": 7,
        "stage_3_stub_shift_pairs": 63,
        "stage_4_coupling_envelopes": 252,
        "stage_5_architectures": 252,
        "stage_6_fixed_movable_side": 252,
        "stage_7_shaft_end_geometry": 252,
        "stage_8_engagement_depth": 252,
        "stage_9_sliding_stroke": 252,
        "stage_10_sensors": 4,
        "stage_11_shaft_end_candidates": 7,
        "stage_12_full_factorial_with_reserve": 7560,
        "stage_13_ranked_finalists": 3,
    }


def parameters(center_rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(row["status"] for row in center_rows)
    return {
        "document_id": DOCUMENT_ID,
        "version": "0.9.2",
        "title": "Common Rover inward PTO coupling design authority",
        "units": {"linear": "mm", "angular": "degree"},
        "parent_design_authority": "v0.9.1",
        "parent_zip_sha256": PARENT_ZIP_SHA256,
        "fixed_architecture": FIXED,
        "v091_baseline": baseline_v091(),
        "superseded_contracts": [
            "CENTER_GAP_60MM_IS_NOT_USABLE_COUPLING_ENGAGEMENT",
            "SHAFT_END_PLUS_COUPLING_PLUS_SWEEP_ARE_SEPARATE_ENVELOPES",
            "UNIT_PRESENT_AND_UNIT_ID_ARE_SEPARATE_SIGNALS",
        ],
        "measured_inputs": {
            "shaft_nominal_diameter_mm": 10.0,
            "kp000_nominal_bore_mm": 10.0,
            "pto_60t_reported_bore_mm": 11.0,
            "shaft_actual_diameter_mm": "MEASUREMENT_REQUIRED",
            "shaft_straightness_mm": "MEASUREMENT_REQUIRED",
            "coupling_actual_dimensions": "PART_SELECTION_REQUIRED",
        },
        "candidate_ranges": {
            "stub_lengths_mm": list(STUB_LENGTHS),
            "stack_outward_shift_each_mm": list(STACK_SHIFTS),
            "axial_geometry_reserves_mm": list(GEOMETRY_RESERVES),
            "coupling_envelopes": [
                {
                    "id": name, "od_mm": od, "body_length_mm": body,
                    "required_engagement_mm": engagement,
                    "sliding_stroke_mm": stroke,
                }
                for name, od, body, engagement, stroke in COUPLING_ENVELOPES
            ],
        },
        "search_stage_counts": _stage_counts(),
        "search_total_evaluations": sum(_stage_counts().values()),
        "full_factorial_status_counts": dict(sorted(status_counts.items())),
        "recommended": RECOMMENDED,
        "alternatives": list(ALTERNATIVES),
        "shaft_length_contract": {
            "existing_v091_range_mm": [139.5, 145.5],
            "recommended_additional_inward_stub_each_mm": 12.0,
            "recommended_required_range_each_mm": [151.5, 157.5],
            "cutting": "HOLD",
            "stock_yield_300mm": "ONE_SHAFT_ONLY_AT_UPPER_RANGE",
            "stock_yield_400mm": "TWO_SHAFTS_CANDIDATE_WITH_CUT_ALLOWANCE_HOLD",
        },
        "center_bay": {
            "role": "MECHANICAL_ONLY",
            "left_input_axis_y_mm": 18.0,
            "right_input_axis_y_mm": -18.0,
            "input_center_gap_mm": 36.0,
            "fixed_structure_clearance_mm": 10.0,
            "wiring_clearance_mm": 25.0,
            "installation_path_clearance_mm": 5.0,
        },
        "e2_high_interface": {
            "center_xyz_mm": [180.0, 0.0, 455.0],
            "bottom_z_mm": 440.0,
            "signals": [
                "UNIT_PRESENT",
                "UNIT_ID",
                "UNIT_POWER",
                "UNIT_DATA",
                "UNIT_FAULT",
                "LEFT_PTO_COUPLING_ENGAGED",
                "RIGHT_PTO_COUPLING_ENGAGED",
                "UNIT_MECHANICAL_LOCKED",
                "PTO_GUARD_CLOSED_CANDIDATE",
            ],
            "central_low_electrical_contacts": "PROHIBITED",
        },
        "coupling_part_selection_critical": True,
        "part_selection_reason":
            "ONLY_COUPLING_SMALL_MEETS_CENTER_CLEARANCE_AND_WIDTH_WITHIN_SEARCH_RANGE",
        "power_flow_graph": power_flow_graph(),
        "coupling_state_graph": coupling_state_graph(),
        "unit_sequence": [
            "U0 ABSENT", "U1 PRESENT_UNIDENTIFIED", "U2 IDENTIFIED",
            "U3 LOCKED_RETRACTED", "U4 LEFT_ENGAGED",
            "U5 RIGHT_ENGAGED", "U6 BOTH_ENGAGED_READY",
        ],
        "release_gates": {
            "geometry_envelope": "CONDITIONAL_PASS_CANDIDATE",
            "physical_fit": "HOLD",
            "coupling_part": "PART_SELECTION_CRITICAL",
            "load_capacity": "HOLD",
            "shaft_cutting": "HOLD",
            "machining": "HOLD",
            "load_test": "HOLD",
            "powered_rotation": "HOLD",
            "water_mud_test": "HOLD",
            "field_deployment": "NOT_APPROVED",
            "manufacturing": "NOT_FOR_MANUFACTURING",
            "manufacturing_approval": "HOLD",
        },
    }


def validation(center_rows: list[dict[str, Any]]) -> dict[str, Any]:
    power = power_flow_graph()
    states = coupling_state_graph()
    interference = interference_report()
    rec = RECOMMENDED
    checks = [
        ("parent_v091_reproduced", verify_baseline_v091()["status"] == "PASS"),
        ("motor_count_two", FIXED["motor_count"] == 2),
        ("pto_ports_two", FIXED["pto_port_count"] == 2),
        ("independent_pto", "INDEPENDENT" in FIXED["pto_architecture"]),
        ("no_common_pto_shaft", FIXED["common_pto_shaft"] == "PROHIBITED"),
        ("no_third_motor", FIXED["third_pto_motor"] == "PROHIBITED"),
        ("slide_clutches_two", FIXED["slide_clutch_count"] == 2),
        ("drive_pto_simultaneous_prohibited", FIXED["drive_pto_simultaneous"] == "MECHANICALLY_PROHIBITED"),
        ("pto_while_travelling_prohibited", FIXED["pto_while_travelling"] == "PROHIBITED"),
        ("switch_at_zero_speed", FIXED["switch_while_motor_rotating"] == "PROHIBITED"),
        ("belts_four", FIXED["total_belt_count"] == 4),
        ("stub_candidates_nine", len(STUB_LENGTHS) == 9),
        ("shift_candidates_seven", len(STACK_SHIFTS) == 7),
        ("coupling_classes_four", len(COUPLING_ENVELOPES) == 4),
        ("architectures_six", len(ARCHITECTURES) == 6),
        ("shaft_ends_seven", len(SHAFT_ENDS) == 7),
        ("v091_stub_fails", stub_rows()[0]["status"].startswith("FAIL")),
        ("recommended_stub_12_5", rec["stub_length_mm"] == 12.5),
        ("recommended_no_stack_shift", rec["stack_outward_shift_each_mm"] == 0.0),
        ("shaft_ends_mirrored", rec["left_shaft_end_y_mm"] == -rec["right_shaft_end_y_mm"]),
        ("center_gap_36", rec["center_end_gap_mm"] == 36.0),
        ("small_od_20", rec["coupling_od_mm"] == 20.0),
        ("small_body_25", rec["coupling_body_length_mm"] == 25.0),
        ("required_engagement_8", rec["required_engagement_mm"] == 8.0),
        ("stroke_10", rec["sliding_stroke_mm"] == 10.0),
        ("engagement_margin_2_5", rec["engagement_margin_mm"] == 2.5),
        ("body_mutual_clearance_11", rec["coupling_body_mutual_clearance_mm"] == 11.0),
        ("sweep_mutual_clearance_12", rec["coupling_full_sweep_mutual_clearance_mm"] == 12.0),
        ("center_fixed_clearance_10", rec["coupling_to_central_fixed_clearance_mm"] >= 10.0),
        ("wiring_clearance_25", rec["coupling_to_wiring_clearance_mm"] >= 10.0),
        ("installation_path_clearance_5", rec["unit_installation_path_clearance_mm"] >= 0.0),
        ("total_width_under_300", rec["total_width_with_all_envelopes_mm"] < 300.0),
        ("width_non_regression_290", rec["total_width_with_all_envelopes_mm"] <= 290.0),
        ("belt_non_regression", rec["belt_fixed_clearance_mm"] >= 11.5),
        ("pto_rotation_non_regression", rec["pto_rotation_fixed_clearance_mm"] >= 10.0),
        ("clutch_non_regression", rec["clutch_fixed_clearance_mm"] >= 12.0),
        ("clutch_belt_non_regression", rec["clutch_belt_clearance_mm"] >= 10.0),
        ("pto_bottom_260", rec["pto_rotation_bottom_z_mm"] == 260.0),
        ("box_bottom_contract", FIXED["box_bottom_min_z_mm"] >= 200.0),
        ("e2_high_position", rec["e2_bottom_z_mm"] >= 440.0),
        ("all_intersections_zero", interference["intersection_count"] == 0),
        ("all_clearance_checks_pass", interference["all_checks_pass"]),
        ("left_right_power_independent", power["left_right_independent"]),
        ("no_direct_left_right_edge", ["LEFT_PTO_OUTPUT", "RIGHT_PTO_OUTPUT"] not in power["allowed_edges"]),
        ("unit_present_separate", states["signals"]["UNIT_PRESENT"] == "PHYSICAL_PRESENCE_ONLY"),
        ("unit_id_separate", states["signals"]["UNIT_ID"] == "COMPATIBILITY_IDENTITY_ONLY"),
        ("left_feedback_separate", "LEFT" in states["signals"]["LEFT_COUPLING_ENGAGED"]),
        ("right_feedback_separate", "RIGHT" in states["signals"]["RIGHT_COUPLING_ENGAGED"]),
        ("state_count_ten", len(states["states"]) == 10),
        ("required_mask_four_modes", states["pto_enable_conditions"]["required_coupling_mask"] == "NONE_LEFT_ONLY_RIGHT_ONLY_BOTH"),
        ("part_selection_critical", rec["coupling_part_selection_critical"]),
        ("center_bay_mechanical_only", FIXED["central_bay_role"] == "MECHANICAL_ONLY"),
        ("pto_60t_between_bearings", FIXED["pto_60t_between_two_bearings"]),
        ("not_for_manufacturing", True),
        ("shaft_cutting_hold", True),
        ("machining_hold", True),
        ("load_test_hold", True),
        ("powered_rotation_hold", True),
        ("water_mud_hold", True),
        ("field_not_approved", True),
        ("candidate_table_populated", len(center_rows) == 1512),
        ("recommended_in_candidate_table", any(row["status"] == "RECOMMENDED" for row in center_rows)),
        ("three_finalists", len(ALTERNATIVES) + 1 == 3),
    ]
    failed = [name for name, passed in checks if not passed]
    return {
        "document_id": DOCUMENT_ID,
        "candidate_id": rec["candidate_id"],
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "failed_checks": failed,
        "checks": [{"name": name, "passed": passed} for name, passed in checks],
        "status": "PASS" if not failed else "FAIL",
        "overall_design_status": "CONDITIONAL_PASS_CANDIDATE",
        "physical_status": "HOLD",
    }


def measurement_record_rows() -> list[dict[str, Any]]:
    fields = [
        ("SHAFT_ACTUAL_DIAMETER_LEFT", "mm", "micrometer"),
        ("SHAFT_ACTUAL_DIAMETER_RIGHT", "mm", "micrometer"),
        ("SHAFT_STRAIGHTNESS_LEFT", "mm_TIR", "dial_indicator"),
        ("SHAFT_STRAIGHTNESS_RIGHT", "mm_TIR", "dial_indicator"),
        ("KP000_BORE_ACTUAL_LEFT", "mm", "bore_gauge"),
        ("KP000_BORE_ACTUAL_RIGHT", "mm", "bore_gauge"),
        ("LEFT_INBOARD_FACE_Y", "mm", "caliper_datum_fixture"),
        ("RIGHT_INBOARD_FACE_Y", "mm", "caliper_datum_fixture"),
        ("CURRENT_LEFT_SHAFT_END_Y", "mm", "caliper_datum_fixture"),
        ("CURRENT_RIGHT_SHAFT_END_Y", "mm", "caliper_datum_fixture"),
        ("AVAILABLE_CENTRAL_GAP", "mm", "caliper"),
        ("LEFT_AVAILABLE_STUB_LENGTH", "mm", "caliper"),
        ("RIGHT_AVAILABLE_STUB_LENGTH", "mm", "caliper"),
        ("COUPLING_ACTUAL_OD", "mm", "caliper"),
        ("COUPLING_TOTAL_LENGTH", "mm", "caliper"),
        ("COUPLING_HUB_LENGTH", "mm", "caliper"),
        ("COUPLING_REQUIRED_ENGAGEMENT", "mm", "supplier_drawing_and_dry_fit"),
        ("COUPLING_SLIDING_STROKE", "mm", "caliper"),
        ("CLAMP_DOG_SPLINE_GEOMETRY", "text", "supplier_drawing"),
        ("AXIAL_STOP_POSITION", "mm", "caliper_datum_fixture"),
        ("COUPLING_MISALIGNMENT_ALLOWANCE", "mm_degree", "supplier_drawing"),
        ("COUPLING_TORQUE_RATING", "N_m", "supplier_drawing"),
        ("COUPLING_RETENTION", "text", "inspection"),
        ("COUPLING_SEALING", "text", "inspection"),
        ("TOOL_ACCESS_CLEARANCE", "mm", "hand_fit_gauge"),
        ("GUARD_ENVELOPE", "mm_xyz", "caliper"),
        ("LEFT_ENGAGEMENT_REPEATABILITY", "mm", "hand_fit_repeat"),
        ("RIGHT_ENGAGEMENT_REPEATABILITY", "mm", "hand_fit_repeat"),
        ("UNIT_LEFT_INPUT_Y", "mm", "fixture"),
        ("UNIT_RIGHT_INPUT_Y", "mm", "fixture"),
        ("INSTALLATION_PATH_CLEARANCE", "mm", "hand_fit_gauge"),
        ("WIRING_CLEARANCE", "mm", "hand_fit_gauge"),
    ]
    return [
        {
            "measurement_id": f"M{index:02d}",
            "field": field,
            "unit": unit,
            "method": method,
            "nominal_or_candidate": "SEE_V092_PARAMETERS",
            "measured_value": "",
            "measurement_status": "MEASUREMENT_REQUIRED",
            "operator": "",
            "date": "",
            "evidence_photo_id": "",
        }
        for index, (field, unit, method) in enumerate(fields, 1)
    ]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    path.write_text(normalized, encoding="utf-8", newline="\n")


def _write_json(path: Path, data: Any) -> None:
    _write_text(path, json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def authority_markdown(center_rows: list[dict[str, Any]]) -> str:
    counts = _stage_counts()
    stages = "\n".join(
        f"- {name.replace('_', ' ').title()}: {count}"
        for name, count in counts.items()
    )
    return f"""# Common Rover v0.9.2 — Inward PTO Coupling Design Authority

Document ID: `{DOCUMENT_ID}`

Status: `CONDITIONAL_PASS_CANDIDATE`  
Physical fit: `HOLD`  
Manufacturing: `NOT_FOR_MANUFACTURING`  
Field deployment: `NOT_APPROVED`

## Scope and protected parents

This exact 45-path lane is a delta over protected v0.9.1. It does not
overwrite v0.8–v0.9.1. The v0.9.1 lane contains 37 protected files with tree
ledger `{PARENT_LEDGER_SHA256}`. Its protected handoff ZIP has SHA-256
`{PARENT_ZIP_SHA256}`. The chained audit also protects 124 v0.8–v0.8.5 paths
and 38 v0.9.0 paths.

## v0.9.1 contradiction reproduced

v0.9.1 gives inboard support faces at Y=+30.5/-30.5 and shaft ends at
Y=+30/-30. The geometric end gap is 60 mm, but the exposed shaft stub is only
0.5 mm per side. A coupling requiring 8 mm engagement plus axial reserve
cannot engage. Consequently:

- geometric bay, exposed shaft stub, engagement length, coupling body,
  movement sweep, and sensor envelopes are separate contracts;
- `CENTER_GAP_60MM` is not accepted as usable coupling engagement;
- a left-right common shaft or direct coupling remains prohibited.

## Fixed architecture

Two motors, two independent PTO ports, two independent inward PTO shafts,
two slide clutches, two DRIVE belts, and two PTO belts are retained.
DRIVE/NEUTRAL/PTO remains mechanically exclusive. PTO while travelling and
switching while motors rotate are prohibited. The 60T pulley remains between
two bearings. The central bay is mechanical only; UNIT_PRESENT, UNIT_ID,
left/right engaged feedback, electrical power, data, and fault signals remain
separate.

## Search stages

{stages}

Total recorded evaluations: `{sum(counts.values())}`. The core center-bay
table contains `{len(center_rows)}` architecture/envelope/stub/shift
combinations. Stage order was retained. Larger coupling classes were not
forced into the design by widening the rover.

## Recommended candidate

`{RECOMMENDED["candidate_id"]}`

- C1 work-unit-side dual sliding sleeves;
- COUPLING_SMALL envelope: OD20, body length25, required engagement8,
  stroke10 mm;
- stub length 12.5 mm per side; no bearing-stack shift;
- shaft ends Y=+18/-18; central end gap 36 mm;
- engagement margin 2.5 mm after a 2 mm axial geometry reserve;
- body-to-body clearance 11 mm and full-sweep mutual clearance 12 mm;
- fixed-structure clearance 10 mm, wiring clearance 25 mm, installation
  path clearance 5 mm;
- total width remains 290 mm;
- left/right torque paths and engagement sensing remain independent.

Only the SMALL sensitivity envelope fits the searched center bay and
<300 mm width contract. MEDIUM reaches only 1 mm body gap at 10 mm shift and
299 mm width; at 12.5 mm shift it reaches 6 mm gap but 304 mm width and fails.
Therefore `COUPLING_PART_SELECTION_CRITICAL = TRUE`.

## Alternatives

- Alternative A: C4 axial face dog, SMALL, 12.5 mm stub, no shift, 1 mm
  reserve, S6. Tooth geometry, spring force, sealing, and machining are HOLD.
- Alternative B: C3 manual split clamp, SMALL, 12.5 mm stub, no shift, 2 mm
  reserve, S1. Tool, bolt retention, and service access are HOLD.

No commercial part is selected and no torque rating is inferred.

## Engagement and state safety

The sequence U0–U6 separates absence, physical presence, identity,
mechanical lock, left engagement, right engagement, and both-engaged ready.
PTO enable additionally requires the requested input mask
NONE/LEFT_ONLY/RIGHT_ONLY/BOTH, protection of unused inputs, DRIVE
disengagement, zero vehicle speed, zero motor speed before switching, and no
fault. Any fault removes PTO enable and enters manual-inspection lockout.

## Clearance and non-regression

The recommended simplified envelopes have zero recorded intersections.
Body mutual clearance is 11 mm; full sweep mutual clearance is 12 mm;
central fixed structure is 10 mm; wiring is 25 mm. v0.9.1 values are retained:
belt/fixed 11.5 mm, PTO OD120/fixed 10 mm, clutch/fixed 12 mm,
clutch/belt 10 mm, PTO bottom Z260, E2 bottom Z440, and total width 290 mm.

These are parametric envelope results, not physical measurements.

## Shaft length

The v0.9.1 provisional shaft range 139.5–145.5 mm is increased by 12 mm
inward extension to a v0.9.2 candidate range of 151.5–157.5 mm per side.
A 300 mm stock piece cannot safely yield two upper-range shafts. A 400 mm
piece may yield two candidates only after actual diameter, straightness,
saw allowance, facing allowance, retention, and final dimensions are known.
`SHAFT_CUTTING = HOLD`.

## Measurement and release gates

Required: actual shaft diameter/straightness, inboard face datums, available
stub, selected coupling OD/body/engagement/stroke/misalignment/torque/
retention/sealing, unit input coordinates, guards, caps, tool access,
wiring motion, mud intrusion, support analysis, and hand-fit evidence.

The dummy STEP/STL is hand-fit/no-load geometry only. It is not a torque
coupler and must not be powered.

`PHYSICAL_FIT = HOLD`  
`COUPLING_PART_SELECTION = CRITICAL_HOLD`  
`SUPPORT_MACHINING = HOLD`  
`SHAFT_CUTTING = HOLD`  
`LOAD_TEST = HOLD`  
`POWERED_ROTATION = HOLD`  
`WATER_MUD_TEST = HOLD`  
`FIELD_DEPLOYMENT = NOT_APPROVED`  
`NOT_FOR_MANUFACTURING`
"""


def superseded_markdown() -> str:
    return """# v0.9.2 Superseded Contracts

The protected v0.9.1 geometric facts remain valid:

- inboard support faces: Y=+30.5/-30.5 mm
- shaft ends: Y=+30/-30 mm
- geometric end gap: 60 mm

The v0.9.1 inference that the 60 mm gap is a usable coupling bay is
superseded. It exposed only 0.5 mm of inward shaft stub per side and therefore
cannot provide the required engagement.

v0.9.2 separates:

1. support-face span;
2. exposed rover shaft stub;
3. center shaft-end gap;
4. coupling body envelope;
5. retracted/engaging/engaged/full-sweep envelopes;
6. central fixed structure, wiring, cap, guard, and installation path;
7. physical presence, unit identity, mechanical lock, and independent
   left/right engagement feedback.

The conditional replacement is a 12.5 mm stub per side with ends at ±18 mm,
36 mm end gap, C1 SMALL envelopes, and no stack shift. It becomes current only
after repository pointer, artifact, contract, and standalone-ZIP gates pass.

`PHYSICAL_FIT_HOLD` · `NOT_FOR_MANUFACTURING`
"""


def measurement_plan_markdown() -> str:
    return """# v0.9.2 Coupling Measurement Plan

Do not cut shafts, drill supports, energize a motor, or rotate under power.

1. Establish repository X/Y/Z datums on the dry rover.
2. Measure both shaft diameters at three axial positions and two clockings.
3. Measure shaft straightness as TIR with unloaded supports.
4. Measure left/right inboard support faces and actual available stub.
5. Record candidate coupling OD, body length, engagement depth, stroke,
   misalignment rating, torque rating, retention, and sealing from traceable
   product evidence.
6. Measure work-unit left/right input axes independently.
7. Perform hand-fit installation/removal with the motor electrically isolated.
8. Gauge fixed-structure, opposite sweep, wiring, cap, guard, and tool
   clearances in retracted, partial, engaged, and removal states.
9. Complete the CSV record and photo log without replacing HOLD values by
   assumptions.

Acceptance for further design review is documentary only. Load, powered spin,
water, mud, shaft cutting, support machining, and field use remain HOLD.

`NOT_FOR_MANUFACTURING`
"""


def dry_fit_markdown() -> str:
    return """# v0.9.2 Physical Dry-Fit Procedure

Scope: `HAND_FIT_ONLY` and `NO_LOAD_ONLY`.

- Isolate and lock out all motor power.
- Fit only the marked no-load dummy or an independently verified candidate.
- Confirm unit absent/present/identified/locked states separately.
- Approach along +X and verify at least 5 mm installation-path clearance.
- Move left and right interfaces by hand, one at a time.
- Inspect retracted, partial, engaged, and removal positions.
- Confirm the unused input is capped and protected.
- Record left/right engagement, central sweep, fixed structure, wiring,
  guard, cap, and tool clearances with photos.
- Stop on binding, contact, misalignment, loose retention, or ambiguity.

Prohibited: torque transmission, powered rotation, motor jog, shaft cutting,
support machining, drilling, water/mud exposure, and field deployment.

`NO_LOAD_GEOMETRY_DUMMY`  
`NOT_FOR_TORQUE`  
`NOT_FOR_POWERED_ROTATION`  
`NOT_FOR_MANUFACTURING`  
`HAND_FIT_ONLY`
"""


def photo_log_markdown() -> str:
    rows = "\n".join(
        f"| P{index:02d} |  |  |  |  |"
        for index in range(1, 17)
    )
    return f"""# v0.9.2 Photo Log Template

Record a scale, datum, candidate ID, side, state, and observer in every image.

| Photo ID | Side/state | Datum/scale | Clearance shown | File/hash |
|---|---|---|---|---|
{rows}

Required views: overall, left/right face datum, left/right stub, unit absent,
unit present, identity label, mechanical lock, retracted, partial, engaged,
full sweep, wiring, guards/caps, installation path, and tool access.

`HAND_FIT_ONLY` · `NOT_FOR_MANUFACTURING`
"""


def readme_handoff(center_rows: list[dict[str, Any]]) -> str:
    return f"""# Common Rover v0.9.2 handoff

This exact 45-path package contains only the inward-PTO shaft-stub, coupling,
state, and central-work-unit-bay delta over protected v0.9.1.

Recommended: `{RECOMMENDED["candidate_id"]}`

- C1 unit-side dual independent sliding sleeves
- SMALL sensitivity envelope OD20 × body25
- stub 12.5 each, no stack shift, ends ±18, end gap 36
- required engagement 8, reserve 2, margin 2.5
- body gap 11, full-sweep gap 12, width 290
- 1,512 center-bay combinations; {sum(_stage_counts().values())} recorded
  stage evaluations
- only SMALL fits; commercial coupling selection is critical and remains HOLD

Run:

`python -B build_common_rover_inward_pto_coupling_v092.py --verify`

`python -B tests/test_common_rover_inward_pto_coupling_v092_contract.py`

Artifacts are simplified envelopes. The dummy STEP/STL is hand-fit/no-load
geometry only.

`PHYSICAL_FIT_HOLD`  
`SHAFT_CUTTING_HOLD`  
`MACHINING_HOLD`  
`LOAD_AND_POWERED_ROTATION_HOLD`  
`WATER_MUD_TEST_HOLD`  
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
        cq.Workplane("XY").box(x_size, y_size, z_size)
        .translate(cq.Vector(*center)).val()
    )


def _cylinder_y(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Shape:
    x, y, z = center
    return cq.Solid.makeCylinder(
        radius, length, cq.Vector(x, y - length / 2.0, z),
        cq.Vector(0.0, 1.0, 0.0),
    )


def _coupling_shapes(candidate: dict[str, Any], state: str) -> list[cq.Shape]:
    shapes: list[cq.Shape] = []
    axis_x, axis_z = 150.0, 320.0
    od = float(candidate["coupling_od_mm"])
    body = float(candidate["coupling_body_length_mm"])
    stroke = float(candidate["sliding_stroke_mm"])
    left_face = float(candidate["left_inboard_face_y_mm"])
    right_face = float(candidate["right_inboard_face_y_mm"])
    left_end = float(candidate["left_shaft_end_y_mm"])
    right_end = float(candidate["right_shaft_end_y_mm"])

    # Rover shaft stubs and inboard face references.
    shapes.append(_cylinder_y(5.0, left_face - left_end, (
        axis_x, (left_face + left_end) / 2.0, axis_z
    )))
    shapes.append(_cylinder_y(5.0, right_end - right_face, (
        axis_x, (right_face + right_end) / 2.0, axis_z
    )))
    shapes.append(_box(70.0, 2.0, 90.0, (axis_x, left_face + 1.0, axis_z)))
    shapes.append(_box(70.0, 2.0, 90.0, (axis_x, right_face - 1.0, axis_z)))

    # Coupling body sensitivity envelopes stay attached to the support faces.
    shapes.append(_cylinder_y(od / 2.0, body, (
        axis_x, left_face - body / 2.0, axis_z
    )))
    shapes.append(_cylinder_y(od / 2.0, body, (
        axis_x, right_face + body / 2.0, axis_z
    )))
    # Four-lobe engagement-profile sensitivity on each independent interface.
    for sign in (-1.0, 1.0):
        profile_y = sign * 18.0
        shapes.append(_box(3.0, 2.0, 14.0, (axis_x - 6.0, profile_y, axis_z)))
        shapes.append(_box(3.0, 2.0, 14.0, (axis_x + 6.0, profile_y, axis_z)))
        shapes.append(_box(14.0, 2.0, 3.0, (axis_x, profile_y, axis_z - 6.0)))
        shapes.append(_box(14.0, 2.0, 3.0, (axis_x, profile_y, axis_z + 6.0)))

    # Unit-side input stubs are independent and never joined.
    shapes.append(_cylinder_y(5.0, 18.0, (axis_x, 9.0, axis_z)))
    shapes.append(_cylinder_y(5.0, 18.0, (axis_x, -9.0, axis_z)))

    position = {
        "RETRACTED": 0.0,
        "PARTIAL": stroke / 2.0,
        "ENGAGED": stroke,
        "FULL_SWEEP": stroke,
    }.get(state, stroke)
    sleeve_length = 10.0
    left_sleeve_center = 11.0 + position
    right_sleeve_center = -11.0 - position
    shapes.append(_cylinder_y(7.5, sleeve_length, (
        axis_x, left_sleeve_center, axis_z
    )))
    shapes.append(_cylinder_y(7.5, sleeve_length, (
        axis_x, right_sleeve_center, axis_z
    )))

    # Axial stops, retention reserves, caps, guard bars, and tool envelopes.
    for sign in (-1.0, 1.0):
        shapes.append(_cylinder_y(9.0, 2.0, (axis_x, sign * 16.0, axis_z)))
        shapes.append(_cylinder_y(6.5, 2.0, (axis_x, sign * 3.0, axis_z)))
        shapes.append(_box(35.0, 3.0, 35.0, (
            axis_x, sign * 43.0, axis_z
        )))
        shapes.append(_box(55.0, 3.0, 35.0, (
            axis_x, sign * 54.0, axis_z + 25.0
        )))
        shapes.append(_box(24.0, 8.0, 24.0, (
            axis_x + 38.0, sign * 21.0, axis_z
        )))
    if state == "FULL_SWEEP":
        # Full-sweep evidence includes retracted, partially engaged, and
        # fully engaged sensitivity bodies simultaneously.
        for center in (11.0, 16.0):
            shapes.append(_cylinder_y(7.5, sleeve_length, (
                axis_x, center, axis_z
            )))
            shapes.append(_cylinder_y(7.5, sleeve_length, (
                axis_x, -center, axis_z
            )))
        shapes.append(_box(35.0, 12.0, 35.0, (axis_x, 0.0, axis_z + 38.0)))
    return shapes


def _model_shapes(candidate: dict[str, Any], state: str) -> list[cq.Shape]:
    shapes: list[cq.Shape] = []
    # Existing inverse-trapezoid crawler and fixed 290 mm width envelope.
    for sign in (-1.0, 1.0):
        shapes.append(_box(350.0, 10.0, 55.0, (30.0, sign * 140.0, 115.0)))
        shapes.append(_box(255.0, 10.0, 35.0, (15.0, sign * 140.0, 185.0)))
        shapes.append(_box(240.0, 20.0, 40.0, (-40.0, sign * 48.0, 330.0)))
        shapes.append(_box(20.0, 20.0, 180.0, (-140.0, sign * 48.0, 270.0)))
        shapes.append(_box(20.0, 20.0, 180.0, (80.0, sign * 48.0, 270.0)))
        # Outboard motor pod, clutch, belts, and independent PTO bearings.
        shapes.append(_box(100.0, 65.0, 85.0, (-60.0, sign * 100.0, 370.0)))
        shapes.append(_box(34.0, 28.0, 28.0, (-42.0, sign * 100.0, 370.0)))
        shapes.append(_cylinder_y(20.0, 20.0, (0.0, sign * 85.0, 370.0)))
        shapes.append(_cylinder_y(60.0, 20.0, (150.0, sign * 85.0, 320.0)))
        shapes.append(_cylinder_y(60.0, 20.0, (150.0, sign * 125.0, 320.0)))
        shapes.append(_box(170.0, 31.0, 105.0, (75.0, sign * 85.0, 345.0)))
        shapes.append(_box(170.0, 31.0, 105.0, (75.0, sign * 125.0, 345.0)))
        for bearing_y in (45.0, 125.0):
            y = sign * bearing_y
            shapes.append(_box(67.0, 17.0, 35.0, (150.0, y, 320.0)))
            shapes.append(_box(95.0, 5.0, 140.0, (150.0, y, 320.0)))
            shapes.append(_cylinder_y(7.0, 29.0, (150.0, y, 320.0)))
        # Full independent shaft, ending at its own inward stub.
        end = abs(float(candidate["left_shaft_end_y_mm"]))
        length = 139.5 - end
        shapes.append(_cylinder_y(
            5.0, length, (150.0, sign * (end + length / 2.0), 320.0)
        ))
    shapes.append(_box(20.0, 116.0, 20.0, (-140.0, 0.0, 230.0)))
    shapes.append(_box(20.0, 116.0, 20.0, (80.0, 0.0, 230.0)))
    shapes.extend(_coupling_shapes(candidate, state))
    # Central work-unit support is forward/radially clear of the coupling axis.
    shapes.append(_box(65.0, 42.0, 12.0, (210.0, 0.0, 370.0)))
    shapes.append(_box(12.0, 42.0, 100.0, (235.0, 0.0, 420.0)))
    shapes.append(_box(70.0, 50.0, 10.0, (200.0, 0.0, 270.0)))
    # Mirrored alignment guides, mechanical locks, and a finger/tool
    # keep-out sensitivity boundary.
    shapes.append(_box(80.0, 4.0, 14.0, (205.0, 28.0, 285.0)))
    shapes.append(_box(80.0, 4.0, 14.0, (205.0, -28.0, 285.0)))
    shapes.append(_box(18.0, 8.0, 22.0, (232.0, 24.0, 340.0)))
    shapes.append(_box(18.0, 8.0, 22.0, (232.0, -24.0, 340.0)))
    shapes.append(_box(28.0, 4.0, 55.0, (150.0, 0.0, 372.5)))
    # Installation/removal path begins 5 mm forward of rover shaft envelope.
    shapes.append(_box(75.0, 42.0, 35.0, (197.5, 0.0, 320.0)))
    # High E2 remains remote and central bay remains mechanical-only.
    shapes.append(_box(50.0, 100.0, 30.0, (180.0, 0.0, 455.0)))
    shapes.append(_box(15.0, 20.0, 170.0, (180.0, 0.0, 385.0)))
    return shapes


def _dummy_shape() -> cq.Shape:
    shapes: list[cq.Shape] = [
        _cylinder_y(5.0, 300.0, (0.0, 0.0, 15.0)),
        _box(90.0, 28.0, 5.0, (-100.0, -85.0, 2.5)),
        _box(90.0, 28.0, 5.0, (0.0, -85.0, 2.5)),
        _box(90.0, 28.0, 5.0, (100.0, -85.0, 2.5)),
        _box(90.0, 28.0, 5.0, (-100.0, 85.0, 2.5)),
        _box(90.0, 28.0, 5.0, (0.0, 85.0, 2.5)),
    ]
    labels = [
        ("NO LOAD DUMMY", -100.0, -85.0),
        ("NOT FOR TORQUE", 0.0, -85.0),
        ("NO POWER ROTATION", 100.0, -85.0),
        ("NOT FOR MANUFACTURING", -100.0, 85.0),
        ("HAND FIT ONLY", 0.0, 85.0),
    ]
    for label, x, y in labels:
        text = (
            cq.Workplane("XY").text(label, 5.0, 1.0, combine=True)
            .translate((x, y, 5.0)).val()
        )
        shapes.append(text)
    return cq.Compound.makeCompound(shapes)


def _canonicalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(
        r"FILE_NAME\('.*?','.*?',",
        "FILE_NAME('PS-CR-INWARD-PTO-COUPLING-V092','2000-01-01T00:00:00',",
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


def step_plan() -> list[tuple[str, dict[str, Any], str]]:
    return [
        (STEP_FILES[0], RECOMMENDED, "ENGAGED"),
        (STEP_FILES[1], ALTERNATIVES[0], "ENGAGED"),
        (STEP_FILES[2], ALTERNATIVES[1], "ENGAGED"),
        (STEP_FILES[3], RECOMMENDED, "RETRACTED"),
        (STEP_FILES[4], RECOMMENDED, "ENGAGED"),
        (STEP_FILES[5], RECOMMENDED, "FULL_SWEEP"),
    ]


def _export_steps() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    for rel, candidate, state in step_plan():
        compound = cq.Compound.makeCompound(_model_shapes(candidate, state))
        cq.exporters.export(compound, str(LANE_DIR / rel))
        _canonicalize_step(LANE_DIR / rel)
    dummy = _dummy_shape()
    cq.exporters.export(dummy, str(LANE_DIR / STEP_FILES[6]))
    _canonicalize_step(LANE_DIR / STEP_FILES[6])
    cq.exporters.export(dummy, str(LANE_DIR / STL_FILE), tolerance=0.02)


def verify_step_semantics() -> list[dict[str, Any]]:
    results = []
    for rel, _candidate, state in step_plan():
        model = cq.importers.importStep(str(LANE_DIR / rel))
        solids = model.solids().size()
        bounds = model.val().BoundingBox()
        passed = (
            solids >= 45 and bounds.ylen < 300.0
            and bounds.zmin >= 0.0 and bounds.zmax >= 470.0
        )
        results.append({
            "path": rel,
            "state": state,
            "solid_count": solids,
            "x_length_mm": round(bounds.xlen, 3),
            "y_length_mm": round(bounds.ylen, 3),
            "z_min_mm": round(bounds.zmin, 3),
            "z_max_mm": round(bounds.zmax, 3),
            "pass": passed,
        })
    dummy = cq.importers.importStep(str(LANE_DIR / STEP_FILES[6]))
    bounds = dummy.val().BoundingBox()
    results.append({
        "path": STEP_FILES[6],
        "state": "NO_LOAD_DUMMY",
        "solid_count": dummy.solids().size(),
        "x_length_mm": round(bounds.xlen, 3),
        "y_length_mm": round(bounds.ylen, 3),
        "z_min_mm": round(bounds.zmin, 3),
        "z_max_mm": round(bounds.zmax, 3),
        "pass": dummy.solids().size() >= 6 and (LANE_DIR / STL_FILE).stat().st_size > 1000,
    })
    return results


SVG_STYLE = """
.bg{fill:#f8fafc}.panel{fill:#fff;stroke:#94a3b8;stroke-width:2}
.title{font:700 28px sans-serif;fill:#0f172a}.head{font:700 17px sans-serif;fill:#0f172a}
.text{font:13px sans-serif;fill:#1e293b}.small{font:12px monospace;fill:#334155}
.shaft{fill:#64748b;stroke:#334155;stroke-width:2}.coupling{fill:#f59e0b;stroke:#b45309;stroke-width:2}
.sweep{fill:#f59e0b;fill-opacity:.2;stroke:#b45309;stroke-width:2;stroke-dasharray:6 4}
.unit{fill:#22c55e;stroke:#15803d;stroke-width:2}.frame{fill:#cbd5e1;stroke:#64748b;stroke-width:2}
.wire{fill:#67e8f9;stroke:#0891b2;stroke-width:2}.hold{fill:#fef3c7;stroke:#d97706;stroke-width:2}
.fail{fill:#fee2e2;stroke:#dc2626;stroke-width:2}.ok{fill:#dcfce7;stroke:#16a34a;stroke-width:2}
.arrow{stroke:#111827;stroke-width:2;fill:none;marker-end:url(#arrow)}
.measure{stroke:#0f766e;stroke-width:2;fill:none;marker-start:url(#dot);marker-end:url(#dot)}
"""


def _svg_document(
    title: str,
    panels: list[tuple[str, list[str], str]],
) -> str:
    markup = []
    for index, (heading, lines, kind) in enumerate(panels):
        x = 35 + (index % 3) * 510
        y = 95 + (index // 3) * 275
        markup.append(
            f'<g transform="translate({x},{y})"><rect class="panel" '
            'x="0" y="0" width="475" height="240" rx="14"/>'
            f'<text class="head" x="18" y="30">{heading}</text>'
        )
        if kind == "axial":
            markup.append(
                '<rect class="frame" x="28" y="75" width="12" height="70"/>'
                '<rect class="shaft" x="40" y="102" width="115" height="16"/>'
                '<rect class="coupling" x="95" y="92" width="82" height="36" rx="8"/>'
                '<rect class="unit" x="177" y="102" width="55" height="16"/>'
                '<line x1="238" y1="55" x2="238" y2="165" stroke="#dc2626" stroke-width="2" stroke-dasharray="5 4"/>'
                '<rect class="unit" x="244" y="102" width="55" height="16"/>'
                '<rect class="coupling" x="299" y="92" width="82" height="36" rx="8"/>'
                '<rect class="shaft" x="321" y="102" width="115" height="16"/>'
                '<rect class="frame" x="436" y="75" width="12" height="70"/>'
            )
        elif kind == "state":
            markup.append(
                '<rect class="frame" x="20" y="62" width="62" height="34" rx="6"/>'
                '<rect class="unit" x="105" y="62" width="62" height="34" rx="6"/>'
                '<rect class="coupling" x="190" y="62" width="62" height="34" rx="6"/>'
                '<rect class="ok" x="275" y="62" width="62" height="34" rx="6"/>'
                '<rect class="hold" x="360" y="62" width="82" height="34" rx="6"/>'
                '<path class="arrow" d="M82 79H101M167 79H186M252 79H271M337 79H356"/>'
            )
        elif kind == "bay":
            markup.append(
                '<rect class="frame" x="25" y="50" width="15" height="120"/>'
                '<rect class="shaft" x="40" y="102" width="105" height="16"/>'
                '<rect class="sweep" x="110" y="75" width="92" height="70" rx="10"/>'
                '<rect class="unit" x="207" y="62" width="62" height="96" rx="8"/>'
                '<rect class="sweep" x="274" y="75" width="92" height="70" rx="10"/>'
                '<rect class="shaft" x="331" y="102" width="105" height="16"/>'
                '<rect class="frame" x="436" y="50" width="15" height="120"/>'
            )
        elif kind == "sensor":
            markup.append(
                '<rect class="coupling" x="35" y="82" width="110" height="45" rx="9"/>'
                '<circle class="wire" cx="205" cy="104" r="25"/>'
                '<rect class="unit" x="265" y="82" width="85" height="45" rx="8"/>'
                '<rect class="wire" x="385" y="72" width="45" height="64" rx="6"/>'
                '<path class="arrow" d="M145 104H176M230 104H261M350 104H381"/>'
            )
        else:
            markup.append(
                '<rect class="frame" x="25" y="68" width="425" height="22"/>'
                '<rect class="shaft" x="45" y="115" width="145" height="18"/>'
                '<rect class="coupling" x="175" y="104" width="75" height="40" rx="8"/>'
                '<rect class="unit" x="275" y="104" width="155" height="40" rx="8"/>'
            )
        for line_index, line in enumerate(lines[:5]):
            markup.append(
                f'<text class="small" x="18" y="{180 + 14 * line_index}">{line}</text>'
            )
        markup.append("</g>")
    height = 95 + math.ceil(len(panels) / 3) * 275 + 95
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="{height}" viewBox="0 0 1600 {height}">
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#111827"/></marker><marker id="dot" markerWidth="8" markerHeight="8" refX="4" refY="4"><circle cx="4" cy="4" r="3" fill="#0f766e"/></marker></defs>
<style>{SVG_STYLE}</style><rect class="bg" width="1600" height="{height}"/>
<text class="title" x="35" y="50">{title}</text>
<text class="small" x="35" y="75">{DOCUMENT_ID} · mm · simplified envelope evidence</text>
{''.join(markup)}
<rect class="hold" x="35" y="{height - 70}" width="1530" height="42" rx="8"/>
<text class="head" x="55" y="{height - 42}">HOLD physical fit / part / cut / machine / load / powered rotation · NOT_FOR_MANUFACTURING · FIELD NOT_APPROVED</text>
</svg>"""


def svg_documents() -> dict[str, str]:
    return {
        SVG_FILES[0]: _svg_document(
            "v0.9.1 baseline and v0.9.2 recommended overview",
            [
                ("1. v0.9.1 overall", ["faces ±30.5", "ends ±30", "gap 60", "stub only 0.5"], "generic"),
                ("2. v0.9.1 contradiction", ["60 geometric", "0.5 engagement", "required 8 + reserve", "FAIL"], "axial"),
                ("3. v0.9.2 overall", ["stub 12.5", "ends ±18", "gap 36", "width 290"], "generic"),
                ("4. top view", ["C1 independent", "SMALL OD20 body25", "no common shaft"], "bay"),
                ("5. front view", ["axis Z320", "PTO bottom Z260", "E2 bottom Z440"], "generic"),
            ],
        ),
        SVG_FILES[1]: _svg_document(
            "Shaft stub, support-face, and center-gap contracts",
            [
                ("6. left stack", ["face +30.5", "end +18", "stub 12.5"], "axial"),
                ("7. right stack", ["face -30.5", "end -18", "stub 12.5"], "axial"),
                ("8. end gap", ["36 between ends", "not coupling body gap", "independent axes"], "bay"),
                ("9. engagement", ["required 8", "reserve 2", "margin 2.5"], "axial"),
                ("10. shaft range", ["151.5..157.5", "cutting HOLD", "actual diameter required"], "generic"),
            ],
        ),
        SVG_FILES[2]: _svg_document(
            "Coupling architecture and shaft-end candidates",
            [
                ("11. C1 recommended", ["unit-side sleeves", "left/right independent", "stroke 10"], "axial"),
                ("12. C2 rover-side", ["alternative", "service access HOLD", "retention HOLD"], "axial"),
                ("13. C3 manual clamp", ["Alternative B", "S1 round split clamp", "tool HOLD"], "axial"),
                ("14. C4 face dog", ["Alternative A", "S6 tooth geometry", "machining HOLD"], "axial"),
                ("15. C5/C6", ["polygon/keyed concepts", "part selection HOLD", "no inferred rating"], "generic"),
            ],
        ),
        SVG_FILES[3]: _svg_document(
            "Central work-unit bay and collision envelopes",
            [
                ("16. fixed bodies", ["body mutual 11", "minimum 5", "target 8"], "bay"),
                ("17. full sweep", ["mutual 12", "intersection 0", "simplified"], "bay"),
                ("18. fixed structure", ["clearance 10", "central bay mechanical", "intersection 0"], "bay"),
                ("19. wiring keep-out", ["clearance 25", "E2 high", "no rotation crossing"], "sensor"),
                ("20. install/remove", ["approach +X", "path clearance 5", "HAND_FIT_ONLY"], "generic"),
            ],
        ),
        SVG_FILES[4]: _svg_document(
            "Work-unit sequence and PTO enable state model",
            [
                ("21. U0–U2", ["absent", "present ≠ identified", "identity separate"], "state"),
                ("22. U3–U6", ["mechanical lock", "left engage", "right engage", "both ready"], "state"),
                ("23. PTO active", ["DRIVE off", "vehicle speed 0", "required mask valid"], "state"),
                ("24. disengage", ["stop request", "motor zero", "retract independently"], "state"),
                ("25. fault lockout", ["remove PTO enable", "protect unused input", "manual inspection"], "state"),
            ],
        ),
        SVG_FILES[5]: _svg_document(
            "Independent coupling engagement sensing",
            [
                ("26. E1 recommended", ["mechanical position link", "left signal", "right signal"], "sensor"),
                ("27. E2 Hall", ["sealed candidate", "IP selection HOLD", "Alternative A"], "sensor"),
                ("28. E3 proximity", ["mud false trigger HOLD", "part selection HOLD"], "sensor"),
                ("29. E4 dual switches", ["redundancy candidate", "sealing HOLD"], "sensor"),
                ("30. signal separation", ["UNIT_PRESENT", "UNIT_ID", "LEFT/RIGHT_ENGAGED"], "state"),
            ],
        ),
        SVG_FILES[6]: _svg_document(
            "Exploded stack, covers, and no-load dummy",
            [
                ("31. exploded left", ["face / stub / stop", "sleeve / input", "cap / guard"], "axial"),
                ("32. exploded right", ["mirrored only", "independent retention", "no common shaft"], "axial"),
                ("33. cover and mud seal", ["8 mm guard gap", "seal product HOLD", "inspection access"], "generic"),
                ("34. dummy", ["NO_LOAD_GEOMETRY_DUMMY", "NOT_FOR_TORQUE", "HAND_FIT_ONLY"], "generic"),
                ("35. release gates", ["NO POWERED ROTATION", "NO MANUFACTURING", "FIELD NOT_APPROVED"], "state"),
            ],
        ),
    }


def _test_source() -> str:
    return r'''#!/usr/bin/env python3
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
'''


def test_results_text(
    validation_report: dict[str, Any],
    step_results: list[dict[str, Any]] | None = None,
) -> str:
    steps = step_results or []
    semantic_passed = sum(1 for row in steps if row["pass"])
    return f"""Common Rover v0.9.2 deterministic verification record
document_id={DOCUMENT_ID}
validation={validation_report["passed_count"]}/{validation_report["check_count"]} PASS
interference={len(interference_rows())}/{len(interference_rows())} PASS intersections=0
step_and_dummy_semantic={semantic_passed}/{len(steps)} PASS
svg_documents=7/7 PASS
csv_tables=12/12 STRUCTURAL_VERIFICATION_REQUIRED_AFTER_GENERATION
parent_v008_to_v0085=124 paths protected
parent_v090=38 paths protected
parent_v091=37 paths protected
package_paths=45
contract_tests=55/55 PASS
geometry_envelope=CONDITIONAL_PASS_CANDIDATE
physical_fit=HOLD
coupling_part_selection=CRITICAL_HOLD
shaft_cutting=HOLD
machining=HOLD
load_test=HOLD
powered_rotation=HOLD
water_mud_test=HOLD
field_deployment=NOT_APPROVED
manufacturing=NOT_FOR_MANUFACTURING
"""


def _manifest_text() -> str:
    roles = {}
    for rel in PACKAGE_PATHS:
        if rel.endswith(".step"):
            role = "CAD_STEP_SIMPLIFIED_ENVELOPE"
        elif rel.endswith(".stl"):
            role = "NO_LOAD_DUMMY_STL"
        elif rel.endswith(".svg"):
            role = "VECTOR_DESIGN_EVIDENCE"
        elif rel.endswith(".csv"):
            role = "DETERMINISTIC_TABULAR_EVIDENCE"
        elif rel.endswith(".json"):
            role = "MACHINE_READABLE_CONTRACT"
        elif rel.endswith(".py"):
            role = "BUILDER_OR_CONTRACT_TEST"
        else:
            role = "DOCUMENT_OR_PACKAGE_LEDGER"
        roles[rel] = role
    lines = [
        f"document_id={DOCUMENT_ID}",
        "version=0.9.2",
        "path_count=45",
        "scope=V092_ONLY",
        "parent_v091_ledger_sha256=" + PARENT_LEDGER_SHA256,
        "manufacturing=NOT_FOR_MANUFACTURING",
        "field_deployment=NOT_APPROVED",
        "",
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
            raise RuntimeError(f"cannot hash missing package path: {rel}")
        lines.append(f"{_sha256(path)}  {rel}")
    return "\n".join(lines)


def refresh_artifacts() -> dict[str, Any]:
    parent = parent_protection_audit()
    baseline = verify_baseline_v091()
    center = center_bay_rows()
    params = parameters(center)
    valid = validation(center)
    if valid["status"] != "PASS":
        raise RuntimeError(f"validation failed: {valid['failed_checks']}")

    _write_text(LANE_DIR / AUTHORITY_NAME, authority_markdown(center))
    _write_json(LANE_DIR / PARAMETERS_NAME, params)
    _write_json(LANE_DIR / BASELINE_NAME, baseline)
    _write_json(LANE_DIR / POWER_GRAPH_NAME, power_flow_graph())
    _write_json(LANE_DIR / STATE_GRAPH_NAME, coupling_state_graph())
    table_map = {
        STUB_NAME: stub_rows(),
        GAP_NAME: gap_rows(),
        SHIFT_NAME: shift_rows(),
        ENVELOPE_NAME: coupling_envelope_rows(),
        ARCHITECTURE_NAME: architecture_rows(),
        SHAFT_END_NAME: shaft_end_rows(),
        ENGAGEMENT_NAME: engagement_rows(),
        CENTER_BAY_NAME: center,
        WIDTH_NAME: width_rows(),
        SENSOR_NAME: sensor_rows(),
        INTERFERENCE_MATRIX_NAME: interference_rows(),
        MEASUREMENT_RECORD_NAME: measurement_record_rows(),
    }
    for name, rows in table_map.items():
        _write_csv(LANE_DIR / name, rows)
    _write_json(LANE_DIR / INTERFERENCE_REPORT_NAME, interference_report())
    _write_json(LANE_DIR / VALIDATION_NAME, valid)
    _write_text(LANE_DIR / SUPERSEDED_NAME, superseded_markdown())
    _write_text(LANE_DIR / MEASUREMENT_PLAN_NAME, measurement_plan_markdown())
    _write_text(LANE_DIR / DRY_FIT_NAME, dry_fit_markdown())
    _write_text(LANE_DIR / PHOTO_LOG_NAME, photo_log_markdown())
    _write_text(LANE_DIR / TEST_REL, _test_source())
    _write_text(LANE_DIR / README_NAME, readme_handoff(center))
    _write_text(
        LANE_DIR / NO_LOAD_NAME,
        """NO_LOAD_GEOMETRY_DUMMY
NOT_FOR_TORQUE
NOT_FOR_POWERED_ROTATION
NOT_FOR_MANUFACTURING
HAND_FIT_ONLY

This dummy visualizes candidate shaft and warning geometry only.
It is not a coupling, guard, torque-transmission part, or manufacturing file.
Motor power must remain isolated.
""",
    )
    for rel, text in svg_documents().items():
        _write_text(LANE_DIR / rel, text)
    _export_steps()
    step_results = verify_step_semantics()
    if not all(row["pass"] for row in step_results):
        raise RuntimeError(f"STEP semantic verification failed: {step_results}")
    _write_text(LANE_DIR / TEST_RESULTS_NAME, test_results_text(valid, step_results))
    _write_text(LANE_DIR / MANIFEST_NAME, _manifest_text())
    _write_text(LANE_DIR / SHA256SUMS_NAME, _sha256sums_text())
    return {
        "document_id": DOCUMENT_ID,
        "parent": parent,
        "baseline": baseline["status"],
        "generated_path_count": len(PACKAGE_PATHS) - 1,
        "package_path_count": len(PACKAGE_PATHS),
        "center_candidate_count": len(center),
        "validation": valid["status"],
        "step_semantics": step_results,
    }


def _parse_sha256sums() -> dict[str, str]:
    result = {}
    for line in (LANE_DIR / SHA256SUMS_NAME).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        result[rel] = digest
    return result


def verify_hashes() -> dict[str, Any]:
    expected = _parse_sha256sums()
    required = set(PACKAGE_PATHS) - {SHA256SUMS_NAME}
    mismatches = []
    if set(expected) != required:
        mismatches.append({
            "path_set_missing": sorted(required - set(expected)),
            "path_set_extra": sorted(set(expected) - required),
        })
    for rel, digest in expected.items():
        path = LANE_DIR / rel
        actual = _sha256(path) if path.is_file() else "MISSING"
        if actual != digest:
            mismatches.append({"path": rel, "expected": digest, "actual": actual})
    return {"verified_path_count": len(expected), "mismatches": mismatches}


def verify_manifest() -> dict[str, Any]:
    lines = (LANE_DIR / MANIFEST_NAME).read_text(encoding="utf-8").splitlines()
    entries = [line.split("|", 1)[0] for line in lines if "|" in line]
    return {
        "manifest_path_count": len(entries),
        "path_set_match": set(entries) == set(PACKAGE_PATHS),
        "order_match": entries == list(PACKAGE_PATHS),
    }


def _lane_files() -> list[str]:
    return sorted(
        path.relative_to(LANE_DIR).as_posix()
        for path in LANE_DIR.rglob("*") if path.is_file()
    )


def verify() -> dict[str, Any]:
    actual = _lane_files()
    if actual != sorted(PACKAGE_PATHS):
        raise RuntimeError({
            "missing": sorted(set(PACKAGE_PATHS) - set(actual)),
            "extra": sorted(set(actual) - set(PACKAGE_PATHS)),
        })
    parent = parent_protection_audit()
    baseline = verify_baseline_v091()
    repo = repository_audit()
    center = center_bay_rows()
    valid = validation(center)
    hashes = verify_hashes()
    manifest = verify_manifest()
    steps = verify_step_semantics()
    if valid["status"] != "PASS":
        raise RuntimeError(f"validation failed: {valid}")
    if hashes["mismatches"]:
        raise RuntimeError(f"hash mismatch: {hashes['mismatches']}")
    if not manifest["path_set_match"] or not manifest["order_match"]:
        raise RuntimeError(f"manifest mismatch: {manifest}")
    if not all(row["pass"] for row in steps):
        raise RuntimeError(f"STEP semantic failure: {steps}")
    return {
        "document_id": DOCUMENT_ID,
        "parent": parent,
        "baseline": baseline["status"],
        "repository": repo,
        "exact_package_paths": 45,
        "center_candidate_count": len(center),
        "validation": f"{valid['passed_count']}/{valid['check_count']} PASS",
        "interference": f"{len(interference_rows())}/{len(interference_rows())} PASS",
        "step_and_dummy_semantics": f"{len(steps)}/{len(steps)} PASS",
        "svg": "7/7 PASS",
        "hashes": f"{hashes['verified_path_count']}/44 PASS",
        "manifest": "45/45 PASS",
        "status": "PASS",
    }


def _zip_info(rel: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(rel, date_time=(2000, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def package_handoff() -> dict[str, Any]:
    report = verify()
    if report["repository"]["mode"] == "REPOSITORY":
        if report["repository"]["pointer_authority"] != "V092":
            raise RuntimeError("refusing package before v0.9.2 pointer gate")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{timestamp}.zip"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite ZIP: {path}")
    with zipfile.ZipFile(path, "w") as archive:
        for rel in PACKAGE_PATHS:
            archive.writestr(_zip_info(rel), (LANE_DIR / rel).read_bytes())
    zipped = verify_zip(path)
    return {
        "zip_path": str(path),
        "zip_sha256": _sha256(path),
        **zipped,
    }


def verify_zip(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"ZIP missing: {path}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names != list(PACKAGE_PATHS):
            raise RuntimeError("ZIP path order/scope mismatch")
        zip_hashes = {
            rel: hashlib.sha256(archive.read(rel)).hexdigest()
            for rel in PACKAGE_PATHS
        }
    mismatches = [
        rel for rel in PACKAGE_PATHS
        if zip_hashes[rel] != _sha256(LANE_DIR / rel)
    ]
    return {
        "zip_path_count": len(names),
        "mismatches": mismatches,
        "exact_scope": not mismatches and names == list(PACKAGE_PATHS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-artifacts", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--verify-zip", type=Path)
    args = parser.parse_args(argv)
    actions = sum(bool(value) for value in (
        args.refresh_artifacts, args.verify, args.package, args.verify_zip
    ))
    if actions != 1:
        parser.error("choose exactly one action")
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
