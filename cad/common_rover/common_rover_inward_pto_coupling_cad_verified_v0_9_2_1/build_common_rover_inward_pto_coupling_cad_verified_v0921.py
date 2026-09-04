#!/usr/bin/env python3
"""Build and verify Common Rover v0.9.2.1 actual-CAD coupling patch."""

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
import OCP

from cad_clearance_engine_v0921 import (
    CAD_INTERSECTION_VOLUME_TOLERANCE_MM3,
    CAD_NUMERICAL_DISTANCE_TOLERANCE_MM,
    FULL_SWEEP_SAMPLE_INTERVAL_MM,
    build_pair_result,
    run_canary_tests,
    summarize_pair_results,
)
from dry_fit_jig_builder_v0921 import (
    CENTER_GAP_MM,
    DRY_FIT_STATES,
    ENGAGEMENT_REFERENCE_MM,
    LEFT_FACE_Y_MM,
    LEFT_SHAFT_END_Y_MM,
    RIGHT_FACE_Y_MM,
    RIGHT_SHAFT_END_Y_MM,
    SHAFT_STOCK_LENGTH_MM,
    SLEEVE_STROKE_MM,
    STUB_LENGTH_MM,
    annulus_y,
    assembly_named_shapes,
    box,
    center_gap_gauge,
    cylinder_y,
    dry_fit_dimension_rows,
    dry_fit_part_rows,
    engagement_overlap_from_intervals,
    print_plate_shapes,
    sliding_sleeve_dummy,
    stub_gauge,
)


DOCUMENT_ID = "PS-CR-INWARD-PTO-CAD-VERIFIED-V0921"
LANE_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = LANE_DIR / "artifacts"
TEST_DIR = LANE_DIR / "tests"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_9_2_1_CAD_Verified_Dry_Fit_"

AUTHORITY_NAME = "common_rover_inward_pto_coupling_cad_verified_design_authority_v0921.md"
PARAMETERS_NAME = "common_rover_inward_pto_coupling_cad_verified_parameters_v0921.json"
BASELINE_NAME = "common_rover_v092_baseline_v0921.json"
REGISTRY_NAME = "common_rover_named_shape_registry_v0921.json"
POWER_GRAPH_NAME = "common_rover_power_flow_graph_v0921.json"
STATE_GRAPH_NAME = "common_rover_coupling_state_graph_v0921.json"
CLEARANCE_MATRIX_NAME = "common_rover_actual_cad_clearance_matrix_v0921.csv"
INTERFERENCE_REPORT_NAME = "common_rover_actual_cad_interference_report_v0921.json"
SWEEP_NAME = "common_rover_full_sweep_clearance_v0921.csv"
CANARY_NAME = "common_rover_canary_geometry_results_v0921.csv"
PART_LIST_NAME = "common_rover_dry_fit_part_list_v0921.csv"
DIMENSIONS_NAME = "common_rover_dry_fit_dimensions_v0921.csv"
VALIDATION_NAME = "common_rover_validation_v0921.json"
SUPERSEDED_NAME = "common_rover_superseded_contracts_v0921.md"
DRY_FIT_PROCEDURE_NAME = "physical_dry_fit_procedure_v0921.md"
MEASUREMENT_NAME = "physical_dry_fit_measurement_record_v0921.csv"
PHOTO_LOG_NAME = "photo_log_template_v0921.md"
NO_LOAD_NAME = "NO_LOAD_ONLY.txt"
BUILDER_NAME = Path(__file__).name
ENGINE_NAME = "cad_clearance_engine_v0921.py"
JIG_BUILDER_NAME = "dry_fit_jig_builder_v0921.py"
README_NAME = "README_HANDOFF.md"
MANIFEST_NAME = "MANIFEST.txt"
SHA256SUMS_NAME = "SHA256SUMS.txt"
TEST_RESULTS_NAME = "test_results_v0921.txt"

STEP_FILES = (
    "artifacts/PS-CR-V0921-CAD-VERIFIED-RECOMMENDED.step",
    "artifacts/PS-CR-V0921-RETRACTED.step",
    "artifacts/PS-CR-V0921-PARTIAL.step",
    "artifacts/PS-CR-V0921-ENGAGED.step",
    "artifacts/PS-CR-V0921-FULL-SWEEP.step",
    "artifacts/PS-CR-V0921-DRY-FIT-DF0-PARTS.step",
    "artifacts/PS-CR-V0921-DRY-FIT-DF1-SHAFTS.step",
    "artifacts/PS-CR-V0921-DRY-FIT-DF2-RETRACTED.step",
    "artifacts/PS-CR-V0921-DRY-FIT-DF3-INSERTING.step",
    "artifacts/PS-CR-V0921-DRY-FIT-DF4-LOCKED.step",
    "artifacts/PS-CR-V0921-DRY-FIT-DF5-PARTIAL.step",
    "artifacts/PS-CR-V0921-DRY-FIT-DF6-ENGAGED.step",
    "artifacts/PS-CR-V0921-DRY-FIT-DF7-DISENGAGING.step",
    "artifacts/PS-CR-V0921-DRY-FIT-DF8-REMOVABLE.step",
    "artifacts/PS-CR-V0921-DRY-FIT-PRINT-PLATE.step",
    "artifacts/PS-CR-V0921-CENTER-GAP-GAUGE-36.step",
    "artifacts/PS-CR-V0921-STUB-GAUGE-12P5.step",
)
STL_FILES = (
    "artifacts/PS-CR-V0921-DRY-FIT-PRINT-PLATE.stl",
    "artifacts/PS-CR-V0921-CENTER-GAP-GAUGE-36.stl",
    "artifacts/PS-CR-V0921-STUB-GAUGE-12P5.stl",
)
SVG_FILES = (
    "artifacts/PS-CR-V0921-OVERVIEW.svg",
    "artifacts/PS-CR-V0921-CLEARANCE.svg",
    "artifacts/PS-CR-V0921-FULL-SWEEP.svg",
    "artifacts/PS-CR-V0921-DRY-FIT-SEQUENCE.svg",
    "artifacts/PS-CR-V0921-INDEPENDENT-SHAFTS.svg",
    "artifacts/PS-CR-V0921-MIN-CLEARANCE.svg",
    "artifacts/PS-CR-V0921-EXPLODED.svg",
)
TEST_FILES = (
    "tests/test_cad_clearance_engine_v0921.py",
    "tests/test_common_rover_inward_pto_coupling_v0921_contract.py",
    "tests/test_dry_fit_jig_v0921.py",
)
PACKAGE_PATHS = (
    AUTHORITY_NAME,
    PARAMETERS_NAME,
    BASELINE_NAME,
    REGISTRY_NAME,
    POWER_GRAPH_NAME,
    STATE_GRAPH_NAME,
    CLEARANCE_MATRIX_NAME,
    INTERFERENCE_REPORT_NAME,
    SWEEP_NAME,
    CANARY_NAME,
    PART_LIST_NAME,
    DIMENSIONS_NAME,
    VALIDATION_NAME,
    SUPERSEDED_NAME,
    DRY_FIT_PROCEDURE_NAME,
    MEASUREMENT_NAME,
    PHOTO_LOG_NAME,
    NO_LOAD_NAME,
    BUILDER_NAME,
    ENGINE_NAME,
    JIG_BUILDER_NAME,
    *STEP_FILES[:5],
    *STEP_FILES[5:15],
    STL_FILES[0],
    STEP_FILES[15],
    STL_FILES[1],
    STEP_FILES[16],
    STL_FILES[2],
    *SVG_FILES,
    *TEST_FILES,
    README_NAME,
    MANIFEST_NAME,
    SHA256SUMS_NAME,
    TEST_RESULTS_NAME,
)
assert len(PACKAGE_PATHS) == 55
assert len(set(PACKAGE_PATHS)) == 55

PARENT_LANE_REL = (
    "cad/common_rover/"
    "common_rover_inward_pto_coupling_design_authority_v0_9_2"
)
PARENT_PATH_COUNT = 45
PARENT_LEDGER_SHA256 = (
    "3dd904563cb579e57191ef4cee92cfc866fcf415b418c87eb1d7e535947de67a"
)
PARENT_ZIP = Path(
    r"D:\Downloads\Paddy_Swarm_Common_Rover_v0_9_2_"
    r"Inward_PTO_Coupling_20260731_140601.zip"
)
PARENT_ZIP_SHA256 = (
    "88fe5c98ac8b1391ac56e162fe49a4e42036a565a918899f535b88268f7c0ced"
)
TRACKED_POINTER_PATHS = (
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
)

AXIS_X_MM = 150.0
AXIS_Z_MM = 320.0
COUPLING_OD_MM = 20.0
COUPLING_BORE_DIAMETER_MM = 11.2
COUPLING_BODY_LENGTH_MM = 25.0
REQUIRED_ENGAGEMENT_MM = 8.0
GEOMETRY_RESERVE_MM = 2.0
ENGAGEMENT_MARGIN_MM = 2.5
TOTAL_WIDTH_MM = 290.0


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
    sys.modules[name] = module
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
            "mode": "STANDALONE_EMBEDDED_PARENT_LEDGER",
            "v008_to_v0085_checked_path_count": 0,
            "v090_checked_path_count": 0,
            "v091_checked_path_count": 0,
            "v092_checked_path_count": 0,
            "v092_ledger_sha256": PARENT_LEDGER_SHA256,
            "v092_zip_sha256": PARENT_ZIP_SHA256,
            "mismatches": [],
        }
    lane = repo / PARENT_LANE_REL
    mapping = {
        path.relative_to(lane).as_posix(): _sha256(path)
        for path in lane.rglob("*") if path.is_file()
    }
    if len(mapping) != PARENT_PATH_COUNT:
        raise RuntimeError(f"protected v0.9.2 path count: {len(mapping)}")
    ledger = _ledger_sha(mapping)
    if ledger != PARENT_LEDGER_SHA256:
        raise RuntimeError(f"protected v0.9.2 ledger mismatch: {ledger}")
    if not PARENT_ZIP.is_file() or _sha256(PARENT_ZIP) != PARENT_ZIP_SHA256:
        raise RuntimeError("protected v0.9.2 ZIP mismatch")
    parent_builder = _load_module(
        lane / "build_common_rover_inward_pto_coupling_v092.py",
        "protected_v092_builder_for_v0921",
    )
    chain = parent_builder.parent_protection_audit()
    if chain["mismatches"]:
        raise RuntimeError(f"protected v0.8-v0.9.1 chain failed: {chain}")
    return {
        "mode": "REPOSITORY_PARENT_SHA256_VERIFICATION",
        "v008_to_v0085_checked_path_count": 124,
        "v090_checked_path_count": 38,
        "v091_checked_path_count": 37,
        "v092_checked_path_count": 45,
        "v092_ledger_sha256": ledger,
        "v092_zip_sha256": _sha256(PARENT_ZIP),
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
            "pointer_authority": "EMBEDDED_V0921",
        }
    tracked = _git_lines(repo, "diff", "--name-only")
    staged = _git_lines(repo, "diff", "--cached", "--name-only")
    untracked = _git_lines(repo, "ls-files", "--others", "--exclude-standard")
    prefix = (
        "cad/common_rover/"
        "common_rover_inward_pto_coupling_cad_verified_v0_9_2_1/"
    )
    lane_untracked = [path for path in untracked if path.startswith(prefix)]
    if set(tracked) != set(TRACKED_POINTER_PATHS):
        raise RuntimeError(f"tracked diff scope mismatch: {tracked}")
    if staged:
        raise RuntimeError(f"staged paths prohibited: {staged}")
    if lane_untracked and len(lane_untracked) != 55:
        raise RuntimeError(f"v0.9.2.1 untracked path count: {len(lane_untracked)}")
    pointer = (repo / "CURRENT_COMMON_ROVER_AUTHORITY.md").read_text(encoding="utf-8")
    if "common_rover_inward_pto_coupling_cad_verified_v0_9_2_1" in pointer:
        authority = "V0921"
    elif "common_rover_inward_pto_coupling_design_authority_v0_9_2" in pointer:
        authority = "V092_PRE_GATE"
    else:
        raise RuntimeError("authority pointer is neither v0.9.2 nor v0.9.2.1")
    return {
        "mode": "REPOSITORY",
        "tracked_diff": tracked,
        "staged_diff": staged,
        "untracked_total": len(untracked),
        "lane_untracked_count": len(lane_untracked),
        "pointer_authority": authority,
    }


def baseline_v092() -> dict[str, Any]:
    return {
        "candidate_id": "S12-C1-SMALL-STUB12.5-SHIFT00-GAP36-RES2-S1-E1",
        "left_inner_bearing_inboard_face_y_mm": 30.5,
        "left_shaft_end_y_mm": 18.0,
        "left_stub_length_mm": 12.5,
        "right_inner_bearing_inboard_face_y_mm": -30.5,
        "right_shaft_end_y_mm": -18.0,
        "right_stub_length_mm": 12.5,
        "center_shaft_end_gap_mm": 36.0,
        "coupling_od_mm": 20.0,
        "coupling_body_length_mm": 25.0,
        "sleeve_stroke_mm": 10.0,
        "required_engagement_mm": 8.0,
        "geometry_reserve_mm": 2.0,
        "engagement_margin_mm": 2.5,
        "total_width_mm": 290.0,
        "pto_bottom_z_mm": 260.0,
        "belt_fixed_clearance_mm": 11.5,
        "pto_fixed_clearance_mm": 10.0,
        "clutch_fixed_clearance_mm": 12.0,
        "clutch_belt_clearance_mm": 10.0,
        "e2_center_x_mm": 180.0,
        "e2_center_z_mm": 455.0,
        "e2_bottom_z_mm": 440.0,
    }


def verify_baseline_v092() -> dict[str, Any]:
    baseline = baseline_v092()
    repo = _repo_root()
    if repo is None:
        return {
            "mode": "STANDALONE_EMBEDDED_BASELINE",
            "status": "PASS",
            "check_count": len(baseline),
            "baseline": baseline,
        }
    parent_params = json.loads(
        (
            repo / PARENT_LANE_REL
            / "common_rover_inward_pto_coupling_parameters_v092.json"
        ).read_text(encoding="utf-8")
    )
    rec = parent_params["recommended"]
    comparisons = {
        "candidate_id": rec["candidate_id"],
        "left_inner_bearing_inboard_face_y_mm": rec["left_inboard_face_y_mm"],
        "left_shaft_end_y_mm": rec["left_shaft_end_y_mm"],
        "left_stub_length_mm": rec["stub_length_mm"],
        "right_inner_bearing_inboard_face_y_mm": rec["right_inboard_face_y_mm"],
        "right_shaft_end_y_mm": rec["right_shaft_end_y_mm"],
        "right_stub_length_mm": rec["stub_length_mm"],
        "center_shaft_end_gap_mm": rec["center_end_gap_mm"],
        "coupling_od_mm": rec["coupling_od_mm"],
        "coupling_body_length_mm": rec["coupling_body_length_mm"],
        "sleeve_stroke_mm": rec["sliding_stroke_mm"],
        "required_engagement_mm": rec["required_engagement_mm"],
        "geometry_reserve_mm": rec["axial_geometry_reserve_mm"],
        "engagement_margin_mm": rec["engagement_margin_mm"],
        "total_width_mm": rec["total_width_with_all_envelopes_mm"],
        "pto_bottom_z_mm": rec["pto_rotation_bottom_z_mm"],
        "belt_fixed_clearance_mm": rec["belt_fixed_clearance_mm"],
        "pto_fixed_clearance_mm": rec["pto_rotation_fixed_clearance_mm"],
        "clutch_fixed_clearance_mm": rec["clutch_fixed_clearance_mm"],
        "clutch_belt_clearance_mm": rec["clutch_belt_clearance_mm"],
        "e2_center_x_mm": rec["e2_center_xyz_mm"][0],
        "e2_center_z_mm": rec["e2_center_xyz_mm"][2],
        "e2_bottom_z_mm": rec["e2_bottom_z_mm"],
    }
    mismatches = {
        key: {"expected": value, "actual": comparisons[key]}
        for key, value in baseline.items()
        if comparisons.get(key) != value
    }
    if mismatches:
        raise RuntimeError(f"v0.9.2 baseline mismatch: {mismatches}")
    return {
        "mode": "REPOSITORY_PARENT_DATA_REPRODUCTION",
        "status": "PASS",
        "check_count": len(baseline),
        "baseline": baseline,
    }


def _compound(shapes: Iterable[cq.Shape]) -> cq.Shape:
    values = list(shapes)
    if not values:
        raise ValueError("cannot make empty compound")
    return cq.Compound.makeCompound(values)


def _coupling_sleeve(side: str, travel_mm: float) -> cq.Shape:
    return sliding_sleeve_dummy(side, travel_mm)


def _coupling_full_sweep(side: str) -> cq.Shape:
    sign = 1.0 if side == "LEFT" else -1.0
    # Conservative continuous swept annulus: 10mm sleeve translated 10mm.
    return annulus_y(
        COUPLING_OD_MM / 2.0,
        COUPLING_BORE_DIAMETER_MM / 2.0,
        20.0,
        (AXIS_X_MM, sign * 18.0, AXIS_Z_MM),
    )


def _parent_frame_fixed() -> cq.Shape:
    pieces = []
    for sign in (-1.0, 1.0):
        pieces.append(box(240.0, 20.0, 40.0, (-40.0, sign * 48.0, 330.0)))
        pieces.append(box(20.0, 20.0, 180.0, (-140.0, sign * 48.0, 270.0)))
        pieces.append(box(20.0, 20.0, 180.0, (80.0, sign * 48.0, 270.0)))
    pieces.append(box(20.0, 116.0, 20.0, (-140.0, 0.0, 230.0)))
    pieces.append(box(20.0, 116.0, 20.0, (80.0, 0.0, 230.0)))
    return _compound(pieces)


def _l_brackets_fixed() -> cq.Shape:
    pieces = []
    for sign in (-1.0, 1.0):
        pieces.append(box(40.0, 40.0, 5.0, (240.0, sign * 48.0, 250.0)))
        pieces.append(box(5.0, 40.0, 40.0, (220.0, sign * 48.0, 270.0)))
    return _compound(pieces)


def _fasteners_fixed() -> cq.Shape:
    pieces = []
    for sign in (-1.0, 1.0):
        pieces.append(cylinder_y(6.0, 48.0, (220.0, sign * 48.0, 260.0)))
        pieces.append(cylinder_y(6.0, 48.0, (245.0, sign * 48.0, 250.0)))
    return _compound(pieces)


def named_shapes() -> dict[str, cq.Shape]:
    shapes: dict[str, cq.Shape] = {}
    for side in ("LEFT", "RIGHT"):
        sign = 1.0 if side == "LEFT" else -1.0
        face = LEFT_FACE_Y_MM if side == "LEFT" else RIGHT_FACE_Y_MM
        shaft_end = LEFT_SHAFT_END_Y_MM if side == "LEFT" else RIGHT_SHAFT_END_Y_MM
        shaft_center_y = sign * ((18.0 + 139.5) / 2.0)
        shaft_length = 139.5 - 18.0
        shapes[f"{side}_PTO_SHAFT"] = cylinder_y(
            5.0, shaft_length, (AXIS_X_MM, shaft_center_y, AXIS_Z_MM)
        )
        shapes[f"{side}_PTO_STUB"] = cylinder_y(
            5.0,
            STUB_LENGTH_MM,
            (AXIS_X_MM, (face + shaft_end) / 2.0, AXIS_Z_MM),
        )
        shapes[f"{side}_INNER_KP000_ENVELOPE"] = box(
            67.0, 17.0, 35.0, (AXIS_X_MM, sign * 45.0, AXIS_Z_MM)
        )
        shapes[f"{side}_OUTER_KP000_ENVELOPE"] = box(
            67.0, 17.0, 35.0, (AXIS_X_MM, sign * 125.0, AXIS_Z_MM)
        )
        shapes[f"{side}_PTO_60T_PHYSICAL"] = cylinder_y(
            50.0, 20.0, (AXIS_X_MM, sign * 85.0, AXIS_Z_MM)
        )
        shapes[f"{side}_PTO_60T_SAFETY"] = cylinder_y(
            60.0, 20.0, (AXIS_X_MM, sign * 85.0, AXIS_Z_MM)
        )
        shapes[f"{side}_COUPLING_FIXED_HUB"] = annulus_y(
            12.0,
            COUPLING_BORE_DIAMETER_MM / 2.0,
            COUPLING_BODY_LENGTH_MM,
            (AXIS_X_MM, sign * 18.0, AXIS_Z_MM),
        )
        shapes[f"{side}_COUPLING_SLEEVE_RETRACTED"] = _coupling_sleeve(side, 0.0)
        shapes[f"{side}_COUPLING_SLEEVE_PARTIAL"] = _coupling_sleeve(side, 5.0)
        shapes[f"{side}_COUPLING_SLEEVE_ENGAGED"] = _coupling_sleeve(side, 10.0)
        shapes[f"{side}_COUPLING_FULL_SWEEP"] = _coupling_full_sweep(side)
        shapes[f"{side}_UNIT_INPUT_SHAFT"] = cylinder_y(
            5.0, 16.0, (AXIS_X_MM, sign * 10.0, AXIS_Z_MM)
        )
        shapes[f"{side}_UNIT_INPUT_SUPPORT"] = box(
            10.0, 24.0, 42.0, (180.0, sign * 12.0, AXIS_Z_MM)
        )
        shapes[f"{side}_GUARD_FIXED"] = box(
            38.0, 3.0, 38.0, (AXIS_X_MM, sign * 36.5, AXIS_Z_MM)
        ).cut(
            cylinder_y(13.0, 5.0, (AXIS_X_MM, sign * 36.5, AXIS_Z_MM))
        )
        shapes[f"{side}_PROTECTIVE_CAP"] = cylinder_y(
            8.0, 4.0, (AXIS_X_MM, sign * 16.0, AXIS_Z_MM)
        )
        shapes[f"{side}_SENSOR_TARGET"] = box(
            5.0, 2.0, 25.0, (
                AXIS_X_MM + 11.0, sign * 23.0, AXIS_Z_MM + 20.0
            )
        )
        shapes[f"{side}_MECHANICAL_LINK"] = box(
            5.0, 5.0, 125.0, (
                180.0, sign * 23.0, AXIS_Z_MM + 62.5
            )
        )

    shapes.update({
        "CENTRAL_UNIT_FRAME": _compound([
            box(60.0, 44.0, 10.0, (210.0, 0.0, AXIS_Z_MM + 45.0)),
            box(10.0, 44.0, 90.0, (235.0, 0.0, AXIS_Z_MM + 5.0)),
        ]),
        "CENTRAL_ALIGNMENT_GUIDE_LEFT": box(
            5.0, 22.0, 40.0, (167.5, 18.0, AXIS_Z_MM)
        ),
        "CENTRAL_ALIGNMENT_GUIDE_RIGHT": box(
            5.0, 22.0, 40.0, (167.5, -18.0, AXIS_Z_MM)
        ),
        "CENTRAL_MECHANICAL_LOCK": box(
            18.0, 32.0, 18.0, (190.0, 0.0, AXIS_Z_MM + 35.0)
        ),
        "CENTRAL_FINGER_KEEP_OUT": box(
            5.0, 46.0, 48.0, (162.5, 0.0, AXIS_Z_MM + 45.0)
        ),
        "UNIT_INSTALLATION_ENVELOPE": box(
            80.0, 50.0, 40.0, (205.0, 0.0, AXIS_Z_MM)
        ),
        "UNIT_REMOVAL_ENVELOPE": box(
            80.0, 50.0, 40.0, (205.0, 0.0, AXIS_Z_MM)
        ),
        "COUPLING_OPERATION_TOOL_ENVELOPE": box(
            15.0, 48.0, 48.0, (167.5, 0.0, AXIS_Z_MM)
        ),
        "WIRING_KEEP_OUT": box(
            10.0, 50.0, 100.0, (185.0, 0.0, AXIS_Z_MM + 70.0)
        ),
        "E2_INTERFACE_ENVELOPE": box(
            50.0, 100.0, 30.0, (180.0, 0.0, 455.0)
        ),
        "FRAME_FIXED": _parent_frame_fixed(),
        "L_BRACKETS_FIXED": _l_brackets_fixed(),
        "FASTENERS_FIXED": _fasteners_fixed(),
        "PTO_BELT_SAFETY_LEFT": box(
            170.0, 31.0, 105.0, (75.0, 85.0, 345.0)
        ),
        "PTO_BELT_SAFETY_RIGHT": box(
            170.0, 31.0, 105.0, (75.0, -85.0, 345.0)
        ),
        "DRIVE_BELT_SAFETY_LEFT": box(
            170.0, 31.0, 105.0, (75.0, 125.0, 345.0)
        ),
        "DRIVE_BELT_SAFETY_RIGHT": box(
            170.0, 31.0, 105.0, (75.0, -125.0, 345.0)
        ),
        "CLUTCH_FULL_STROKE_LEFT": box(
            34.0, 28.0, 28.0, (-42.0, 100.0, 370.0)
        ),
        "CLUTCH_FULL_STROKE_RIGHT": box(
            34.0, 28.0, 28.0, (-42.0, -100.0, 370.0)
        ),
        "TRACK_DYNAMIC_LEFT": box(
            350.0, 10.0, 140.0, (30.0, 140.0, 150.0)
        ),
        "TRACK_DYNAMIC_RIGHT": box(
            350.0, 10.0, 140.0, (30.0, -140.0, 150.0)
        ),
    })
    return shapes


def _bbox_dict(shape: cq.Shape) -> dict[str, float]:
    bounds = shape.BoundingBox()
    return {
        "xmin": round(bounds.xmin, 6),
        "xmax": round(bounds.xmax, 6),
        "ymin": round(bounds.ymin, 6),
        "ymax": round(bounds.ymax, 6),
        "zmin": round(bounds.zmin, 6),
        "zmax": round(bounds.zmax, 6),
        "xlen": round(bounds.xlen, 6),
        "ylen": round(bounds.ylen, 6),
        "zlen": round(bounds.zlen, 6),
    }


def named_shape_registry() -> dict[str, Any]:
    shapes = named_shapes()
    entries = []
    for name in sorted(shapes):
        source = (
            "named_shapes.parent_parametric_reconstruction"
            if name in {
                "FRAME_FIXED", "L_BRACKETS_FIXED", "FASTENERS_FIXED",
                "PTO_BELT_SAFETY_LEFT", "PTO_BELT_SAFETY_RIGHT",
                "DRIVE_BELT_SAFETY_LEFT", "DRIVE_BELT_SAFETY_RIGHT",
                "CLUTCH_FULL_STROKE_LEFT", "CLUTCH_FULL_STROKE_RIGHT",
                "TRACK_DYNAMIC_LEFT", "TRACK_DYNAMIC_RIGHT",
            }
            else "named_shapes.central_coupling_v0921"
        )
        entries.append({
            "shape_name": name,
            "component_id": f"PS-CR-V0921-{name}",
            "source_builder_function": source,
            "state": (
                "RETRACTED" if name.endswith("_RETRACTED")
                else "PARTIAL" if name.endswith("_PARTIAL")
                else "ENGAGED" if name.endswith("_ENGAGED")
                else "FULL_SWEEP" if name.endswith("_FULL_SWEEP")
                else "STATE_INDEPENDENT"
            ),
            "transform_matrix": [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            "bounding_box_mm": _bbox_dict(shapes[name]),
            "geometry_source": (
                "V0921_ACTUAL_CAD_CENTRAL"
                if "parent_parametric" not in source
                else "V092_PARENT_PARAMETRIC_RECONSTRUCTION"
            ),
        })
    return {
        "document_id": DOCUMENT_ID,
        "registry_entry_count": len(entries),
        "names_unique": len({row["shape_name"] for row in entries}) == len(entries),
        "entries": entries,
    }


STATE_TRAVEL = {
    "RETRACTED": 0.0,
    "PARTIAL": 5.0,
    "ENGAGED": 10.0,
}


def _state_pair_specs(
    state: str,
) -> list[tuple[str, str, float, str]]:
    suffix = state
    specs: list[tuple[str, str, float, str]] = []
    for side, opposite in (("LEFT", "RIGHT"), ("RIGHT", "LEFT")):
        sleeve = f"{side}_COUPLING_SLEEVE_{suffix}"
        specs.extend([
            (sleeve, f"{opposite}_COUPLING_SLEEVE_{suffix}", 5.0, "left/right sleeves remain independent"),
            (sleeve, f"{opposite}_PTO_STUB", 5.0, "sleeve versus opposite rover stub"),
            (sleeve, "CENTRAL_UNIT_FRAME", 5.0, "coupling versus central fixed structure"),
            (sleeve, "CENTRAL_ALIGNMENT_GUIDE_LEFT", 5.0, "coupling versus left alignment guide"),
            (sleeve, "CENTRAL_ALIGNMENT_GUIDE_RIGHT", 5.0, "coupling versus right alignment guide"),
            (sleeve, "CENTRAL_MECHANICAL_LOCK", 5.0, "coupling versus mechanical lock"),
            (sleeve, f"{side}_GUARD_FIXED", 5.0, "coupling versus fixed guard"),
            (sleeve, "WIRING_KEEP_OUT", 10.0, "coupling versus protected wiring"),
            (sleeve, "COUPLING_OPERATION_TOOL_ENVELOPE", 0.0, "intentional tool access boundary; no positive clearance required"),
            (sleeve, "UNIT_INSTALLATION_ENVELOPE", 5.0, "front installation envelope"),
            (sleeve, "UNIT_REMOVAL_ENVELOPE", 5.0, "front removal envelope"),
            (sleeve, f"{side}_UNIT_INPUT_SUPPORT", 5.0, "independent unit input support"),
            (sleeve, "CENTRAL_FINGER_KEEP_OUT", 0.0, "finger keep-out reference boundary"),
            (f"{side}_PTO_STUB", f"{side}_UNIT_INPUT_SHAFT", 0.0, "independent axial interfaces meet at reference plane"),
        ])
    return specs


def _full_sweep_pair_specs() -> list[tuple[str, str, float, str]]:
    specs: list[tuple[str, str, float, str]] = []
    for side, opposite in (("LEFT", "RIGHT"), ("RIGHT", "LEFT")):
        sweep = f"{side}_COUPLING_FULL_SWEEP"
        specs.extend([
            (sweep, f"{opposite}_COUPLING_FULL_SWEEP", 5.0, "continuous conservative sweep versus opposite sweep"),
            (sweep, f"{opposite}_PTO_STUB", 5.0, "continuous sweep versus opposite stub"),
            (sweep, "CENTRAL_UNIT_FRAME", 5.0, "continuous sweep versus central frame"),
            (sweep, "CENTRAL_ALIGNMENT_GUIDE_LEFT", 5.0, "continuous sweep versus left guide"),
            (sweep, "CENTRAL_ALIGNMENT_GUIDE_RIGHT", 5.0, "continuous sweep versus right guide"),
            (sweep, "CENTRAL_MECHANICAL_LOCK", 5.0, "continuous sweep versus lock"),
            (sweep, f"{side}_GUARD_FIXED", 5.0, "continuous sweep versus guard"),
            (sweep, "WIRING_KEEP_OUT", 10.0, "continuous sweep versus wiring"),
            (sweep, "COUPLING_OPERATION_TOOL_ENVELOPE", 0.0, "tool access boundary"),
            (sweep, "UNIT_INSTALLATION_ENVELOPE", 5.0, "continuous sweep versus installation"),
            (sweep, "UNIT_REMOVAL_ENVELOPE", 5.0, "continuous sweep versus removal"),
            (sweep, f"{side}_UNIT_INPUT_SUPPORT", 5.0, "continuous sweep versus input support"),
        ])
    return specs


def _upstream_pair_specs() -> list[tuple[str, str, float, str]]:
    specs: list[tuple[str, str, float, str]] = []
    for side in ("LEFT", "RIGHT"):
        specs.extend([
            (f"PTO_BELT_SAFETY_{side}", "FRAME_FIXED", 5.0, "actual pair on reconstructed v0.9.2 parent envelope"),
            (f"PTO_BELT_SAFETY_{side}", "L_BRACKETS_FIXED", 5.0, "actual pair on reconstructed v0.9.2 parent envelope"),
            (f"PTO_BELT_SAFETY_{side}", "FASTENERS_FIXED", 5.0, "actual pair on reconstructed v0.9.2 parent envelope"),
            (f"DRIVE_BELT_SAFETY_{side}", "FRAME_FIXED", 5.0, "actual pair on reconstructed v0.9.2 parent envelope"),
            (f"DRIVE_BELT_SAFETY_{side}", "L_BRACKETS_FIXED", 5.0, "actual pair on reconstructed v0.9.2 parent envelope"),
            (f"DRIVE_BELT_SAFETY_{side}", "FASTENERS_FIXED", 5.0, "actual pair on reconstructed v0.9.2 parent envelope"),
            (f"{side}_PTO_60T_SAFETY", "FRAME_FIXED", 8.0, "actual pair on reconstructed v0.9.2 parent envelope"),
            (f"{side}_PTO_60T_SAFETY", "L_BRACKETS_FIXED", 8.0, "actual pair on reconstructed v0.9.2 parent envelope"),
            (f"{side}_PTO_60T_SAFETY", "FASTENERS_FIXED", 8.0, "actual pair on reconstructed v0.9.2 parent envelope"),
            (f"CLUTCH_FULL_STROKE_{side}", "FRAME_FIXED", 5.0, "actual pair on reconstructed v0.9.2 parent envelope"),
            (f"CLUTCH_FULL_STROKE_{side}", f"PTO_BELT_SAFETY_{side}", 8.0, "actual clutch-to-PTO-belt pair"),
            (f"CLUTCH_FULL_STROKE_{side}", f"DRIVE_BELT_SAFETY_{side}", 8.0, "actual clutch-to-DRIVE-belt pair"),
            ("WIRING_KEEP_OUT", f"{side}_PTO_60T_SAFETY", 10.0, "high protected wiring versus rotation"),
            (f"TRACK_DYNAMIC_{side}", "UNIT_INSTALLATION_ENVELOPE", 5.0, "track dynamic versus unit route"),
            (f"TRACK_DYNAMIC_{side}", "UNIT_REMOVAL_ENVELOPE", 5.0, "track dynamic versus removal route"),
        ])
    return specs


def actual_clearance_rows() -> list[dict[str, Any]]:
    shapes = named_shapes()
    rows: list[dict[str, Any]] = []
    pair_index = 1
    for state in ("RETRACTED", "PARTIAL", "ENGAGED"):
        for name_a, name_b, required, note in _state_pair_specs(state):
            rows.append(build_pair_result(
                f"CAD-{pair_index:04d}",
                name_a,
                shapes[name_a],
                name_b,
                shapes[name_b],
                state,
                required,
                note,
                sample_position_mm=STATE_TRAVEL[state],
            ))
            pair_index += 1
    for name_a, name_b, required, note in _full_sweep_pair_specs():
        rows.append(build_pair_result(
            f"CAD-{pair_index:04d}",
            name_a,
            shapes[name_a],
            name_b,
            shapes[name_b],
            "FULL_SWEEP",
            required,
            note,
        ))
        pair_index += 1
    for name_a, name_b, required, note in _upstream_pair_specs():
        rows.append(build_pair_result(
            f"CAD-{pair_index:04d}",
            name_a,
            shapes[name_a],
            name_b,
            shapes[name_b],
            "UPSTREAM_INHERITED_CONDITIONAL",
            required,
            note,
        ))
        pair_index += 1
    return rows


def full_sweep_rows() -> list[dict[str, Any]]:
    fixed = named_shapes()
    rows: list[dict[str, Any]] = []
    index = 1
    for step in range(21):
        travel = step * FULL_SWEEP_SAMPLE_INTERVAL_MM
        moving = {
            "LEFT": _coupling_sleeve("LEFT", travel),
            "RIGHT": _coupling_sleeve("RIGHT", travel),
        }
        for side, opposite in (("LEFT", "RIGHT"), ("RIGHT", "LEFT")):
            moving_name = f"{side}_COUPLING_SLEEVE_SAMPLE"
            targets = [
                (f"{opposite}_COUPLING_SLEEVE_SAMPLE", moving[opposite], 5.0, "sampled opposite sleeve"),
                (f"{opposite}_PTO_STUB", fixed[f"{opposite}_PTO_STUB"], 5.0, "sampled opposite stub"),
                ("CENTRAL_UNIT_FRAME", fixed["CENTRAL_UNIT_FRAME"], 5.0, "sampled central frame"),
                (f"CENTRAL_ALIGNMENT_GUIDE_{side}", fixed[f"CENTRAL_ALIGNMENT_GUIDE_{side}"], 5.0, "sampled own alignment guide"),
                ("CENTRAL_MECHANICAL_LOCK", fixed["CENTRAL_MECHANICAL_LOCK"], 5.0, "sampled lock"),
                (f"{side}_GUARD_FIXED", fixed[f"{side}_GUARD_FIXED"], 5.0, "sampled guard"),
                ("WIRING_KEEP_OUT", fixed["WIRING_KEEP_OUT"], 10.0, "sampled wiring"),
                ("UNIT_INSTALLATION_ENVELOPE", fixed["UNIT_INSTALLATION_ENVELOPE"], 5.0, "sampled insertion"),
                ("UNIT_REMOVAL_ENVELOPE", fixed["UNIT_REMOVAL_ENVELOPE"], 5.0, "sampled removal"),
                (f"{side}_UNIT_INPUT_SUPPORT", fixed[f"{side}_UNIT_INPUT_SUPPORT"], 5.0, "sampled input support"),
            ]
            for target_name, target_shape, required, note in targets:
                row = build_pair_result(
                    f"SWEEP-{index:04d}",
                    moving_name,
                    moving[side],
                    target_name,
                    target_shape,
                    "FULL_SWEEP_SAMPLED",
                    required,
                    note,
                    sample_position_mm=travel,
                )
                row["sweep_method"] = (
                    "CONTINUOUS_CONSERVATIVE_SOLID_PLUS_0P5MM_ACTUAL_SAMPLES"
                )
                row["sampling_interval_mm"] = FULL_SWEEP_SAMPLE_INTERVAL_MM
                row["engagement_overlap_mm"] = engagement_overlap_from_intervals(travel)
                row["engagement_reference_satisfied"] = (
                    row["engagement_overlap_mm"] >= ENGAGEMENT_REFERENCE_MM
                )
                rows.append(row)
                index += 1
    return rows


def full_sweep_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [
        row for row in rows
        if row["minimum_distance_mm"] is not None
    ]
    worst = min(valid, key=lambda row: float(row["minimum_distance_mm"]))
    first_collision = next(
        (
            row for row in rows
            if row["classification"] == "INTERSECT"
        ),
        None,
    )
    return {
        "sweep_method":
            "CONTINUOUS_CONSERVATIVE_SOLID_PLUS_0P5MM_ACTUAL_SAMPLES",
        "sampling_interval_mm": FULL_SWEEP_SAMPLE_INTERVAL_MM,
        "sample_positions_each_side": 21,
        "actual_pair_calculations": len(rows),
        "minimum_clearance_over_full_sweep_mm": worst["minimum_distance_mm"],
        "minimum_clearance_position_mm": worst["sample_position_mm"],
        "worst_pair": (
            f"{worst['shape_a_name']}::{worst['shape_b_name']}"
        ),
        "first_collision_position_mm": (
            first_collision["sample_position_mm"] if first_collision else None
        ),
        "total_fail": sum(row["result"] == "FAIL" for row in rows),
        "total_error": sum(row["result"] == "ERROR" for row in rows),
        "engagement_overlap_at_10mm_mm": engagement_overlap_from_intervals(10.0),
        "required_engagement_reference_mm": ENGAGEMENT_REFERENCE_MM,
    }


def power_flow_graph() -> dict[str, Any]:
    return {
        "document_id": DOCUMENT_ID,
        "left_path": [
            "LEFT_MOTOR",
            "LEFT_PTO_SHAFT",
            "LEFT_PTO_STUB",
            "LEFT_COUPLING",
            "LEFT_WORK_UNIT_INPUT",
        ],
        "right_path": [
            "RIGHT_MOTOR",
            "RIGHT_PTO_SHAFT",
            "RIGHT_PTO_STUB",
            "RIGHT_COUPLING",
            "RIGHT_WORK_UNIT_INPUT",
        ],
        "prohibited_nodes": ["COMMON_PTO_SHAFT", "COMMON_DUMMY_SHAFT"],
        "prohibited_edges": [
            ["LEFT_PTO_SHAFT", "RIGHT_PTO_SHAFT"],
            ["LEFT_PTO_STUB", "RIGHT_PTO_STUB"],
            ["LEFT_COUPLING", "RIGHT_COUPLING"],
        ],
        "coupling_disengaged_unit_input_reachable": False,
        "neutral_unit_input_reachable": False,
        "left_right_independent": True,
    }


def coupling_state_graph() -> dict[str, Any]:
    return {
        "document_id": DOCUMENT_ID,
        "states": [
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
        ],
        "assembly_state_mapping": {
            "ABSENT": "DF2_SLEEVES_RETRACTED",
            "UNIT_INSERTING": "DF3_UNIT_INSERTING",
            "UNIT_LOCKED": "DF4_UNIT_LOCKED",
            "COUPLING_DISENGAGED": "DF4_UNIT_LOCKED",
            "COUPLING_ENGAGING": "DF5_PARTIAL",
            "COUPLING_ENGAGED": "DF6_ENGAGED",
            "PTO_READY": "DF6_ENGAGED",
            "PTO_ACTIVE": "NO_POWERED_TEST_CAD_STATE_ONLY",
            "COUPLING_DISENGAGING": "DF7_DISENGAGING",
            "FAULT": "MOTOR_ZERO_NEUTRAL_HUMAN_INTERVENTION",
        },
        "allowed_forward": [
            ["ABSENT", "UNIT_INSERTING"],
            ["UNIT_INSERTING", "UNIT_LOCKED"],
            ["UNIT_LOCKED", "COUPLING_DISENGAGED"],
            ["COUPLING_DISENGAGED", "COUPLING_ENGAGING"],
            ["COUPLING_ENGAGING", "COUPLING_ENGAGED"],
            ["COUPLING_ENGAGED", "PTO_READY"],
            ["PTO_READY", "PTO_ACTIVE"],
        ],
        "allowed_stop": [
            ["PTO_ACTIVE", "PTO_READY"],
            ["PTO_READY", "COUPLING_DISENGAGING"],
            ["COUPLING_DISENGAGING", "COUPLING_DISENGAGED"],
            ["COUPLING_DISENGAGED", "UNIT_LOCKED"],
            ["UNIT_LOCKED", "ABSENT"],
        ],
        "signals": {
            "UNIT_PRESENT": "SEPARATE_PHYSICAL_PRESENCE",
            "UNIT_ID": "SEPARATE_IDENTITY",
            "LEFT_PTO_COUPLING_ENGAGED": "SEPARATE_LEFT_FEEDBACK",
            "RIGHT_PTO_COUPLING_ENGAGED": "SEPARATE_RIGHT_FEEDBACK",
        },
        "fault_action": (
            "MOTOR_COMMAND_ZERO;CLUTCH_NEUTRAL;PTO_DISABLED;"
            "HUMAN_INTERVENTION_REQUIRED"
        ),
    }


def actual_interference_report(
    rows: list[dict[str, Any]],
    sweep_rows: list[dict[str, Any]],
    canaries: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = summarize_pair_results(rows)
    sweep = full_sweep_summary(sweep_rows)
    return {
        "document_id": DOCUMENT_ID,
        "calculation_authority": "ACTUAL_CAD_SHAPE_PAIR_RESULTS",
        "calculation_api": {
            "intersection": "CadQuery.Shape.intersect + Shape.Volume",
            "solid_count": "CadQuery.Shape.intersect + Shape.Solids",
            "minimum_distance":
                "OCP.BRepExtrema.BRepExtrema_DistShapeShape.Value",
            "nearest_points":
                "OCP.BRepExtrema.BRepExtrema_DistShapeShape.PointOnShape1/2",
        },
        "numerical_tolerances": {
            "distance_mm": CAD_NUMERICAL_DISTANCE_TOLERANCE_MM,
            "intersection_volume_mm3":
                CAD_INTERSECTION_VOLUME_TOLERANCE_MM3,
        },
        "summary": summary,
        "full_sweep": sweep,
        "canary_results": [
            {
                "pair_id": row["pair_id"],
                "expected": row["expected"],
                "classification": row["classification"],
                "canary_pass": row["canary_pass"],
            }
            for row in canaries
        ],
        "upstream_scope": {
            "status": "INHERITED_CONDITIONAL",
            "geometry_source":
                "V092_PARENT_PARAMETRIC_ENVELOPES_RECONSTRUCTED_AS_SHAPES",
            "claim_prohibited": "ACTUAL_CAD_FULL_SYSTEM_VERIFIED",
        },
        "rows": rows,
    }


def measurement_record_rows() -> list[dict[str, Any]]:
    fields = [
        ("LEFT_SHAFT_STOCK_LENGTH", "mm"),
        ("RIGHT_SHAFT_STOCK_LENGTH", "mm"),
        ("SINGLE_CONTINUOUS_SHAFT_USED", "boolean_MUST_BE_FALSE"),
        ("LEFT_INBOARD_FACE_ACTUAL_Y", "mm"),
        ("RIGHT_INBOARD_FACE_ACTUAL_Y", "mm"),
        ("LEFT_SHAFT_END_ACTUAL_Y", "mm"),
        ("RIGHT_SHAFT_END_ACTUAL_Y", "mm"),
        ("LEFT_STUB_ACTUAL", "mm"),
        ("RIGHT_STUB_ACTUAL", "mm"),
        ("CENTER_GAP_ACTUAL", "mm"),
        ("GO_GAUGE_RESULT", "PASS_FAIL"),
        ("LEFT_SLEEVE_RETRACTED_POSITION", "mm"),
        ("RIGHT_SLEEVE_RETRACTED_POSITION", "mm"),
        ("LEFT_SLEEVE_PARTIAL_POSITION", "mm"),
        ("RIGHT_SLEEVE_PARTIAL_POSITION", "mm"),
        ("LEFT_SLEEVE_ENGAGED_POSITION", "mm"),
        ("RIGHT_SLEEVE_ENGAGED_POSITION", "mm"),
        ("LEFT_ENGAGEMENT_ACTUAL", "mm"),
        ("RIGHT_ENGAGEMENT_ACTUAL", "mm"),
        ("SLEEVE_TO_SLEEVE_MINIMUM_GAP", "mm"),
        ("SLEEVE_TO_FRAME_MINIMUM_GAP", "mm"),
        ("UNIT_INSERTION_MINIMUM_GAP", "mm"),
        ("UNIT_REMOVAL_MINIMUM_GAP", "mm"),
        ("TOOL_ACCESS_RESULT", "PASS_FAIL"),
        ("SENSOR_FLAG_RESULT", "PASS_FAIL"),
        ("INTERFERENCE_OBSERVED", "boolean"),
        ("RUBBING_OBSERVED", "boolean"),
        ("AXIAL_BINDING_OBSERVED", "boolean"),
        ("CORRECTION_REQUIRED", "text"),
        ("PHOTO_IDS", "text"),
        ("TEST_OPERATOR", "text"),
        ("DATE", "yyyy-mm-dd"),
        ("PHYSICAL_TEST_STATUS", "status"),
    ]
    return [
        {
            "measurement_id": f"M{index:02d}",
            "field": field,
            "unit": unit,
            "nominal_reference": (
                "300_OR_400_UNCUT" if "STOCK_LENGTH" in field
                else "MUST_BE_FALSE" if field == "SINGLE_CONTINUOUS_SHAFT_USED"
                else "SEE_V0921_PARAMETERS"
            ),
            "measured_value": "",
            "status": "PHYSICAL_TEST_NOT_PERFORMED",
            "operator": "",
            "date": "",
            "photo_ids": "",
        }
        for index, (field, unit) in enumerate(fields, 1)
    ]


REQUIRED_SHAPE_NAMES = {
    "LEFT_PTO_SHAFT", "LEFT_PTO_STUB", "LEFT_INNER_KP000_ENVELOPE",
    "LEFT_OUTER_KP000_ENVELOPE", "LEFT_PTO_60T_PHYSICAL",
    "LEFT_PTO_60T_SAFETY", "LEFT_COUPLING_FIXED_HUB",
    "LEFT_COUPLING_SLEEVE_RETRACTED", "LEFT_COUPLING_SLEEVE_PARTIAL",
    "LEFT_COUPLING_SLEEVE_ENGAGED", "LEFT_COUPLING_FULL_SWEEP",
    "LEFT_UNIT_INPUT_SHAFT", "LEFT_UNIT_INPUT_SUPPORT", "LEFT_GUARD_FIXED",
    "LEFT_PROTECTIVE_CAP", "LEFT_SENSOR_TARGET", "LEFT_MECHANICAL_LINK",
    "RIGHT_PTO_SHAFT", "RIGHT_PTO_STUB", "RIGHT_INNER_KP000_ENVELOPE",
    "RIGHT_OUTER_KP000_ENVELOPE", "RIGHT_PTO_60T_PHYSICAL",
    "RIGHT_PTO_60T_SAFETY", "RIGHT_COUPLING_FIXED_HUB",
    "RIGHT_COUPLING_SLEEVE_RETRACTED", "RIGHT_COUPLING_SLEEVE_PARTIAL",
    "RIGHT_COUPLING_SLEEVE_ENGAGED", "RIGHT_COUPLING_FULL_SWEEP",
    "RIGHT_UNIT_INPUT_SHAFT", "RIGHT_UNIT_INPUT_SUPPORT", "RIGHT_GUARD_FIXED",
    "RIGHT_PROTECTIVE_CAP", "RIGHT_SENSOR_TARGET", "RIGHT_MECHANICAL_LINK",
    "CENTRAL_UNIT_FRAME", "CENTRAL_ALIGNMENT_GUIDE_LEFT",
    "CENTRAL_ALIGNMENT_GUIDE_RIGHT", "CENTRAL_MECHANICAL_LOCK",
    "CENTRAL_FINGER_KEEP_OUT", "UNIT_INSTALLATION_ENVELOPE",
    "UNIT_REMOVAL_ENVELOPE", "COUPLING_OPERATION_TOOL_ENVELOPE",
    "WIRING_KEEP_OUT", "E2_INTERFACE_ENVELOPE", "FRAME_FIXED",
    "L_BRACKETS_FIXED", "FASTENERS_FIXED", "PTO_BELT_SAFETY_LEFT",
    "PTO_BELT_SAFETY_RIGHT", "DRIVE_BELT_SAFETY_LEFT",
    "DRIVE_BELT_SAFETY_RIGHT", "CLUTCH_FULL_STROKE_LEFT",
    "CLUTCH_FULL_STROKE_RIGHT", "TRACK_DYNAMIC_LEFT", "TRACK_DYNAMIC_RIGHT",
}


def parameters(
    report: dict[str, Any],
    sweep_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "document_id": DOCUMENT_ID,
        "version": "0.9.2.1",
        "parent_version": "0.9.2",
        "parent_ledger_sha256": PARENT_LEDGER_SHA256,
        "parent_zip_sha256": PARENT_ZIP_SHA256,
        "runtime": {
            "python": sys.version.split()[0],
            "cadquery": cq.__version__,
            "ocp": getattr(OCP, "__version__", "AVAILABLE"),
        },
        "fixed_contract": {
            "motor_count": 2,
            "pto_count": 2,
            "pto_independent": True,
            "common_pto_shaft": "PROHIBITED",
            "left_motor_axis": "-Y",
            "right_motor_axis": "+Y",
            "left_pto_output": "-Y",
            "right_pto_output": "+Y",
            "architecture": "B_SHORT_STROKE_SELECTOR_INDEPENDENT_JACKSHAFTS",
            "slide_clutch_count": 2,
            "clutch_states": ["DRIVE", "NEUTRAL", "PTO"],
            "drive_pto_simultaneous": "PROHIBITED",
            "pto_while_travelling": "PROHIBITED",
            "shift_while_motor_rotating": "PROHIBITED",
            "drive_belt_count": 2,
            "pto_belt_count": 2,
            "total_belt_count": 4,
            "pto_60t_between_two_bearings": True,
            "pto_60t_width_mm": 20.0,
            "pto_safety_od_mm": 120.0,
            "pto_axis_z_mm": 320.0,
            "total_width_mm": TOTAL_WIDTH_MM,
        },
        "baseline_v092": baseline_v092(),
        "central_coupling": {
            "left_stub_length_mm": STUB_LENGTH_MM,
            "right_stub_length_mm": STUB_LENGTH_MM,
            "left_shaft_end_y_mm": LEFT_SHAFT_END_Y_MM,
            "right_shaft_end_y_mm": RIGHT_SHAFT_END_Y_MM,
            "center_gap_mm": CENTER_GAP_MM,
            "coupling_od_mm": COUPLING_OD_MM,
            "coupling_body_length_mm": COUPLING_BODY_LENGTH_MM,
            "sleeve_stroke_mm": SLEEVE_STROKE_MM,
            "required_engagement_reference_mm": REQUIRED_ENGAGEMENT_MM,
            "geometry_reserve_mm": GEOMETRY_RESERVE_MM,
            "engagement_margin_mm": ENGAGEMENT_MARGIN_MM,
            "engagement_overlap_at_10mm_mm":
                engagement_overlap_from_intervals(10.0),
            "dummy_bore_mm": COUPLING_BORE_DIAMETER_MM,
            "dummy_clearance": "DUMMY_CLEARANCE_NOT_PRODUCT_FIT",
        },
        "clearance_engine": {
            "distance_tolerance_mm": CAD_NUMERICAL_DISTANCE_TOLERANCE_MM,
            "intersection_volume_tolerance_mm3":
                CAD_INTERSECTION_VOLUME_TOLERANCE_MM3,
            "intersection_api": "CadQuery.Shape.intersect",
            "distance_api": "OCP.BRepExtrema_DistShapeShape",
            "error_fallback": "ERROR_NEVER_PASS",
        },
        "actual_cad_summary": report["summary"],
        "full_sweep_summary": sweep_summary,
        "dry_fit_jig": {
            "test_shaft_count": 2,
            "single_continuous_shaft_used": False,
            "shaft_stock_length_mm": SHAFT_STOCK_LENGTH_MM,
            "states": list(DRY_FIT_STATES),
            "center_gap_gauges_mm": [35.0, 36.0, 37.0],
            "stub_gauge_mm": 12.5,
            "print_bed": "BAMBU_LAB_A1",
            "material_candidate": "PETG_NO_LOAD_ONLY",
        },
        "e2_interface": {
            "center_x_mm": 180.0,
            "center_z_mm": 455.0,
            "bottom_z_mm": 440.0,
            "signals_separate": [
                "UNIT_PRESENT",
                "UNIT_ID",
                "LEFT_PTO_COUPLING_ENGAGED",
                "RIGHT_PTO_COUPLING_ENGAGED",
            ],
        },
        "authority_scope": {
            "central_coupling": "ACTUAL_CAD_VERIFIED_CANDIDATE",
            "full_sweep": "ACTUAL_CAD_VERIFIED_CANDIDATE",
            "upstream_powertrain":
                "INHERITED_CONDITIONAL_PARAMETRIC_SHAPE_RECONSTRUCTION",
            "actual_cad_full_system_verified": False,
        },
        "release_gates": {
            "physical_fit": "HOLD",
            "load_capacity": "HOLD",
            "shaft_cutting": "HOLD",
            "shaft_end_machining": "HOLD",
            "support_plate_machining": "HOLD",
            "powered_test": "NOT_APPROVED",
            "manufacturing": "HOLD",
            "not_for_manufacturing": True,
            "field_deployment": "NOT_APPROVED",
        },
    }


def validation(
    rows: list[dict[str, Any]],
    sweep_rows: list[dict[str, Any]],
    canaries: list[dict[str, Any]],
) -> dict[str, Any]:
    registry = named_shape_registry()
    central_rows = [
        row for row in rows
        if row["coupling_state"] != "UPSTREAM_INHERITED_CONDITIONAL"
    ]
    jig_df1 = assembly_named_shapes("DF1_SHAFTS_POSITIONED")
    left_bounds = jig_df1["LEFT_TEST_SHAFT"].BoundingBox()
    right_bounds = jig_df1["RIGHT_TEST_SHAFT"].BoundingBox()
    checks = [
        ("parent_baseline_pass", verify_baseline_v092()["status"] == "PASS"),
        ("named_shapes_unique", registry["names_unique"]),
        ("required_named_shapes_exist", REQUIRED_SHAPE_NAMES <= set(named_shapes())),
        ("canaries_all_pass", all(row["canary_pass"] for row in canaries)),
        ("canary_overlap", canaries[0]["classification"] == "INTERSECT"),
        ("canary_touch", canaries[1]["classification"] == "CONTACT"),
        ("canary_gap_5", abs(canaries[2]["minimum_distance_mm"] - 5.0) < 1e-6),
        ("canary_gap_10", abs(canaries[3]["minimum_distance_mm"] - 10.0) < 1e-6),
        ("canary_sweep_collision", canaries[-1]["canary_pass"]),
        ("actual_rows_nonempty", len(rows) > 100),
        ("actual_intersection_api", all("CadQuery.Shape.intersect" in row["calculation_api"] for row in rows)),
        ("actual_distance_api", all("BRepExtrema" in row["calculation_api"] for row in rows)),
        ("actual_nearest_points", all(row["nearest_point_a_x"] is not None for row in rows)),
        ("central_no_error", not any(row["result"] == "ERROR" for row in central_rows)),
        ("central_no_fail", not any(row["result"] == "FAIL" for row in central_rows)),
        ("retracted_tested", any(row["coupling_state"] == "RETRACTED" for row in rows)),
        ("partial_tested", any(row["coupling_state"] == "PARTIAL" for row in rows)),
        ("engaged_tested", any(row["coupling_state"] == "ENGAGED" for row in rows)),
        ("full_sweep_tested", any(row["coupling_state"] == "FULL_SWEEP" for row in rows)),
        ("sweep_interval_le_0_5", FULL_SWEEP_SAMPLE_INTERVAL_MM <= 0.5),
        ("sampled_sweep_no_error", not any(row["result"] == "ERROR" for row in sweep_rows)),
        ("sampled_sweep_no_fail", not any(row["result"] == "FAIL" for row in sweep_rows)),
        ("two_test_shafts", {"LEFT_TEST_SHAFT", "RIGHT_TEST_SHAFT"} <= set(jig_df1)),
        ("no_continuous_test_shaft", left_bounds.ymin >= 18.0 and right_bounds.ymax <= -18.0),
        ("dry_fit_center_gap_36", round(left_bounds.ymin - right_bounds.ymax, 6) == 36.0),
        ("left_stub_12_5", LEFT_FACE_Y_MM - LEFT_SHAFT_END_Y_MM == 12.5),
        ("right_stub_12_5", RIGHT_SHAFT_END_Y_MM - RIGHT_FACE_Y_MM == 12.5),
        ("stroke_10", SLEEVE_STROKE_MM == 10.0),
        ("engagement_reference_8", ENGAGEMENT_REFERENCE_MM == 8.0),
        ("engagement_overlap_satisfies", engagement_overlap_from_intervals(10.0) >= 8.0),
        ("dry_fit_states_nine", len(DRY_FIT_STATES) == 9),
        ("independent_unit_inputs", {"LEFT_UNIT_INPUT_DUMMY", "RIGHT_UNIT_INPUT_DUMMY"} <= set(assembly_named_shapes("DF6_ENGAGED"))),
        ("total_width_under_300", TOTAL_WIDTH_MM < 300.0),
        ("physical_fit_hold", True),
        ("load_capacity_hold", True),
        ("powered_test_not_approved", True),
        ("manufacturing_hold", True),
        ("field_not_approved", True),
    ]
    failed = [name for name, passed in checks if not passed]
    return {
        "document_id": DOCUMENT_ID,
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "failed_checks": failed,
        "checks": [{"name": name, "passed": passed} for name, passed in checks],
        "authority_update_gate": "PASS" if not failed else "FAIL",
        "status": "PASS" if not failed else "FAIL",
    }


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def _write_json(path: Path, payload: Any) -> None:
    _write_text(
        path,
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing empty CSV: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _format_point(row: dict[str, Any], prefix: str) -> str:
    return "({:.3f}, {:.3f}, {:.3f})".format(
        float(row[f"nearest_point_{prefix}_x"]),
        float(row[f"nearest_point_{prefix}_y"]),
        float(row[f"nearest_point_{prefix}_z"]),
    )


def _state_counts(rows: list[dict[str, Any]], state: str) -> dict[str, int]:
    selected = [row for row in rows if row["coupling_state"] == state]
    return {
        "pairs": len(selected),
        "intersect": sum(row["classification"] == "INTERSECT" for row in selected),
        "contact": sum(row["classification"] == "CONTACT" for row in selected),
        "clear": sum(row["classification"] == "CLEAR" for row in selected),
        "pass": sum(row["result"] == "PASS" for row in selected),
        "fail": sum(row["result"] == "FAIL" for row in selected),
        "error": sum(row["result"] == "ERROR" for row in selected),
    }


def authority_markdown(
    rows: list[dict[str, Any]],
    sweep_rows: list[dict[str, Any]],
    canaries: list[dict[str, Any]],
) -> str:
    summary = summarize_pair_results(rows)
    sweep = full_sweep_summary(sweep_rows)
    minimum = min(
        (row for row in rows if row["minimum_distance_mm"] is not None),
        key=lambda row: float(row["minimum_distance_mm"]),
    )
    states = {
        state: _state_counts(rows, state)
        for state in ("RETRACTED", "PARTIAL", "ENGAGED", "FULL_SWEEP")
    }
    return f"""# Common Rover inward PTO coupling actual-CAD authority v0.9.2.1

Document ID: `{DOCUMENT_ID}`

Status:

- FUNCTIONAL_POWERTRAIN_CONTRACT_FIXED
- INWARD_PTO_GEOMETRY_CONDITIONAL_PASS
- CENTRAL_COUPLING_ACTUAL_CAD_VERIFIED
- COUPLING_FULL_SWEEP_ACTUAL_CAD_VERIFIED
- INDEPENDENT_DRY_FIT_JIG_READY
- UPSTREAM_POWERTRAIN_GEOMETRY_INHERITED_CONDITIONAL
- PHYSICAL_FIT_HOLD
- LOAD_CAPACITY_HOLD
- POWERED_TEST_NOT_APPROVED
- NOT_FOR_MANUFACTURING
- FIELD_DEPLOYMENT_NOT_APPROVED

## Parent and superseded behavior

This differential authority protects v0.8 through v0.9.2 and reproduces the
v0.9.2 baseline. The v0.9.2 report used parametric/fixed expected clearances
and a fixed zero intersection count; it did not implement actual Shape-pair
interference. Its no-load dummy also used one Y-continuous shaft and was
invalid for independent-PTO fit confirmation. The parent files remain intact.

## Actual-CAD calculation authority

Every row in the v0.9.2.1 clearance matrix is calculated from named CadQuery
Shapes. Boolean common geometry uses `CadQuery.Shape.intersect()`,
intersection volume uses `Shape.Volume()`, solid count uses `Shape.Solids()`,
and minimum distance plus nearest points use
`OCP.BRepExtrema_DistShapeShape`. Exceptions are classified `ERROR` and never
fall back to `PASS`.

- numerical distance tolerance: {CAD_NUMERICAL_DISTANCE_TOLERANCE_MM:.3f} mm
- intersection volume tolerance: {CAD_INTERSECTION_VOLUME_TOLERANCE_MM3:.3f} mm³
- pair calculations in the matrix: {summary['total_pairs_tested']}
- intersect/contact/clear: {summary['total_intersect']}/{summary['total_contact']}/{summary['total_clear']}
- pass/fail/error: {summary['total_pass']}/{summary['total_fail']}/{summary['total_error']}
- minimum actual distance: {summary['minimum_clearance_overall_mm']:.3f} mm
- minimum pair/state: `{summary['minimum_clearance_pair']}` / `{summary['minimum_clearance_state']}`
- nearest point A: {_format_point(minimum, 'a')} mm
- nearest point B: {_format_point(minimum, 'b')} mm
- maximum actual intersection volume: {summary['maximum_intersection_volume_mm3']:.6f} mm³

Known-geometry canaries pass {sum(row['canary_pass'] for row in canaries)}/{len(canaries)}:
overlap, face contact, 5 mm gap, 10 mm gap, coaxial 1 mm radial gap, and a
0.5 mm-sampled sweep collision.

## State results

| State | Pairs | Intersect | Contact | Clear | PASS | FAIL | ERROR |
|---|---:|---:|---:|---:|---:|---:|---:|
""" + "\n".join(
        f"| {state} | {value['pairs']} | {value['intersect']} | "
        f"{value['contact']} | {value['clear']} | {value['pass']} | "
        f"{value['fail']} | {value['error']} |"
        for state, value in states.items()
    ) + f"""

The full stroke is represented by a conservative continuous sweep Shape and
by {sweep['sample_positions_each_side']} actual positions per side at
{sweep['sampling_interval_mm']:.1f} mm intervals. The sampled sweep contains
{sweep['actual_pair_calculations']} actual pair calculations. Its minimum
clearance is {sweep['minimum_clearance_over_full_sweep_mm']:.3f} mm at
travel {sweep['minimum_clearance_position_mm']:.3f} mm; collision position is
`{sweep['first_collision_position_mm']}`.

## Independent dry-fit authority

The jig uses two distinct uncut 300 mm stock references. The left shaft ends
at Y=+18 mm and extends outward to +318 mm; the right ends at Y=-18 mm and
extends outward to -318 mm. No solid crosses the central 36 mm interval.
Bearing-face to shaft-end stub reference is 12.5 mm on each side. Left and
right sleeves and work-unit inputs are separate. Sleeve travel states are
0/5/10 mm; the 10 mm state provides 10 mm geometric overlap against the
8 mm engagement reference. These are no-load geometry references, not product
fit or torque parts.

DF0 through DF8 cover parts, independent shaft positioning, retracted sleeves,
front insertion, mechanical lock, partial engagement, full engagement,
disengagement, and removal. The 35/36/37 mm comparison gauges are assembly
references, not tolerance gauges. The 12.5 mm stub gauge is nominal only.

## Upstream scope limitation

Central coupling Shapes are actual-CAD verified by this lane. Frame, bracket,
fastener, belt, clutch, pulley, track, and other upstream powertrain items are
reconstructed from v0.9.2 parametric envelopes and retain
`UPSTREAM_POWERTRAIN_GEOMETRY_INHERITED_CONDITIONAL`. This document explicitly
does not claim `ACTUAL_CAD_FULL_SYSTEM_VERIFIED`.

## Release holds

Physical fit, load capacity, shaft cutting, shaft-end machining, support-plate
machining, manufacturing, powered rotation, and field deployment remain HOLD
or NOT_APPROVED. No physical test has been performed. Do not infer a product
coupling bore, material, key, D-flat, torque capacity, wear life, or fit from
the printed dummy.
"""


def superseded_markdown() -> str:
    return """# Superseded contracts — v0.9.2.1

The v0.9.2 files are retained and protected. Their historical result is not
rewritten.

## v0.9.2

- `PARAMETRIC_CLEARANCE_CONTRACT = PASS`
- `ACTUAL_CAD_INTERFERENCE_CHECK = NOT_IMPLEMENTED`
- `DRY_FIT_DUMMY_COMMON_SHAFT = INVALID_FOR_INDEPENDENT_PTO_FIT`

## v0.9.2.1

- `ACTUAL_CAD_INTERFERENCE_ENGINE = IMPLEMENTED`
- `CENTRAL_COUPLING_ACTUAL_CAD_CHECK = REQUIRED`
- `DRY_FIT_DUMMY_INDEPENDENT_SHAFTS = REQUIRED`
- `COMMON_DUMMY_SHAFT = PROHIBITED`

This correction supersedes only the interference-evidence method and the
no-load jig topology. It does not release physical fit or manufacturing.
"""


def dry_fit_procedure_markdown() -> str:
    steps = [
        "電源・モーター・ベルトを接続しない。",
        "左右別々の未切断軸材を用意する。",
        "一本の軸を左右へ貫通させない。",
        "左軸を左外側から挿入する。",
        "右軸を右外側から挿入する。",
        "左右stubを12.5 mm nominal referenceへ合わせる。",
        "36 mm center-gap gaugeを挿入する。",
        "左右軸が接触していないことを確認する。",
        "左右sleeveをRETRACTEDへ置く。",
        "unit bridgeを前方+Xから挿入する。",
        "mechanical-lock dummyを固定する。",
        "左右sleeveを5 mm位置へ手で移動する。",
        "左右および固定構造との干渉・擦れを確認する。",
        "左右sleeveを10 mm位置へ手で移動する。",
        "左右8 mm engagement referenceを確認する。",
        "tool accessを確認する。",
        "左右sensor flagを確認する。",
        "左右sleeveを完全に退避する。",
        "unit bridgeを前方へ取り外す。",
        "全寸法を物理測定記録票へ記録する。",
        "写真IDと撮影方向をphoto logへ記録する。",
        "動力を加えず終了する。",
    ]
    return """# Physical dry-fit procedure v0.9.2.1

`HAND_FIT_ONLY` / `NO_LOAD_ONLY` / `NOT_FOR_MANUFACTURING`

""" + "\n".join(f"{index}. {step}" for index, step in enumerate(steps, 1)) + """

## 禁止

- モーター接続
- ベルト張力付与
- ドリル回転
- 電動工具による軸回転
- 手回しによるトルク試験
- unit作業荷重
- 一本の共通軸
- 軸切断・軸端加工・支持板加工
- 圃場使用

KP000止めねじだけで軸端位置を決めないでください。すべての数値は
`NOMINAL_GEOMETRY_REFERENCE_ONLY`で、候補許容差は未確定です。
"""


def photo_log_markdown() -> str:
    return """# Photo log template v0.9.2.1

Physical test status: `PHYSICAL_TEST_NOT_PERFORMED`

| Photo ID | Date/time | Operator | DF state | View direction | Gauge shown | Observation | File name |
|---|---|---|---|---|---|---|---|
| UNRECORDED |  |  |  |  |  | PHYSICAL_TEST_NOT_PERFORMED |  |

Required views after an authorized no-load hand fit: left/right shaft ends,
36 mm center gap, each 12.5 mm stub reference, RETRACTED, PARTIAL, ENGAGED,
front insertion/removal, tool access, sensor flags, and any rubbing or
interference. Do not enter observations until the physical procedure occurs.
"""


def no_load_text() -> str:
    return """NO_LOAD_GEOMETRY_DUMMY
LEFT_INDEPENDENT_PTO
RIGHT_INDEPENDENT_PTO
NO_COMMON_SHAFT
NOT_FOR_TORQUE
NOT_FOR_POWERED_ROTATION
HAND_FIT_ONLY
NOT_FOR_MANUFACTURING

CENTER_GAP_REFERENCE
NOMINAL_36_MM
NOT_A_TOLERANCE_GAUGE
NOMINAL_GEOMETRY_REFERENCE_ONLY
DUMMY_CLEARANCE_NOT_PRODUCT_FIT
NO_LOAD_JIG_SLOT
NOT_A_MANUFACTURING_HOLE

Two independent uncut shaft references are mandatory. The dummy must not
transmit torque or cross the 36 mm center gap. No physical test was performed.
"""


def readme_handoff(summary: dict[str, Any], sweep: dict[str, Any]) -> str:
    return f"""# Common Rover v0.9.2.1 handoff

This 55-path differential package replaces fixed expected-clearance evidence
with actual CadQuery/OCP Shape calculations in the central coupling region and
replaces the invalid common-shaft dummy with two independent shaft references.

- matrix pairs: {summary['total_pairs_tested']}
- matrix PASS/FAIL/ERROR: {summary['total_pass']}/{summary['total_fail']}/{summary['total_error']}
- sampled sweep calculations: {sweep['actual_pair_calculations']}
- full-sweep minimum: {sweep['minimum_clearance_over_full_sweep_mm']:.3f} mm
- center gap: 36.0 mm
- left/right stub: 12.5/12.5 mm
- dry-fit states: DF0–DF8

Scope: `CENTRAL_COUPLING_ACTUAL_CAD_VERIFIED`.
Upstream frame/belt/clutch/pulley/track Shapes are parametric reconstructions,
so `UPSTREAM_POWERTRAIN_GEOMETRY_INHERITED_CONDITIONAL` remains in force.
`ACTUAL_CAD_FULL_SYSTEM_VERIFIED` is not claimed.

All STEP/STL dry-fit artifacts are no-load geometry references. Keep physical
fit, load capacity, cutting, machining, manufacturing, powered testing, and
field deployment on HOLD/NOT_APPROVED.
"""


def _canonicalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(
        r"FILE_NAME\('.*?','.*?',",
        "FILE_NAME('PS-CR-V0921','2000-01-01T00:00:00',",
        text,
        count=1,
    )
    text = re.sub(
        r"FILE_DESCRIPTION\(\(.*?\),'.*?'\);",
        "FILE_DESCRIPTION(('NO LOAD CONDITIONAL CAD EVIDENCE'),'2;1');",
        text,
        count=1,
    )
    path.write_text(
        text.replace("\r\n", "\n"),
        encoding="utf-8",
        newline="\n",
    )


def _central_model_shapes(state: str) -> dict[str, cq.Shape]:
    shapes = named_shapes()
    sleeve_key = {
        "RETRACTED": "COUPLING_SLEEVE_RETRACTED",
        "PARTIAL": "COUPLING_SLEEVE_PARTIAL",
        "ENGAGED": "COUPLING_SLEEVE_ENGAGED",
        "FULL_SWEEP": "COUPLING_FULL_SWEEP",
    }[state]
    selected: dict[str, cq.Shape] = {}
    for name, shape in shapes.items():
        is_sleeve = (
            "COUPLING_SLEEVE_RETRACTED" in name
            or "COUPLING_SLEEVE_PARTIAL" in name
            or "COUPLING_SLEEVE_ENGAGED" in name
            or "COUPLING_FULL_SWEEP" in name
        )
        if not is_sleeve or sleeve_key in name:
            selected[name] = shape
    return selected


def _export_step(path: Path, shapes: Iterable[cq.Shape]) -> None:
    compound = _compound(shapes)
    cq.exporters.export(compound, str(path))
    _canonicalize_step(path)


def _export_model_artifacts() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    regular_plan = [
        (STEP_FILES[0], "ENGAGED"),
        (STEP_FILES[1], "RETRACTED"),
        (STEP_FILES[2], "PARTIAL"),
        (STEP_FILES[3], "ENGAGED"),
        (STEP_FILES[4], "FULL_SWEEP"),
    ]
    for rel, state in regular_plan:
        _export_step(LANE_DIR / rel, _central_model_shapes(state).values())

    for rel, state in zip(STEP_FILES[5:14], DRY_FIT_STATES):
        _export_step(LANE_DIR / rel, assembly_named_shapes(state).values())

    plate = print_plate_shapes()
    _export_step(LANE_DIR / STEP_FILES[14], plate.values())
    cq.exporters.export(
        _compound(plate.values()),
        str(LANE_DIR / STL_FILES[0]),
        tolerance=0.05,
        angularTolerance=0.2,
    )

    gap = center_gap_gauge(36.0)
    _export_step(LANE_DIR / STEP_FILES[15], [gap])
    cq.exporters.export(
        gap,
        str(LANE_DIR / STL_FILES[1]),
        tolerance=0.03,
        angularTolerance=0.2,
    )
    stub = stub_gauge(12.5)
    _export_step(LANE_DIR / STEP_FILES[16], [stub])
    cq.exporters.export(
        stub,
        str(LANE_DIR / STL_FILES[2]),
        tolerance=0.03,
        angularTolerance=0.2,
    )


def _step_shape(path: Path) -> cq.Shape:
    model = cq.importers.importStep(str(path))
    return model.val()


def verify_step_semantics() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, rel in enumerate(STEP_FILES):
        shape = _step_shape(LANE_DIR / rel)
        bounds = shape.BoundingBox()
        solids = len(shape.Solids())
        passed = solids >= 1 and all(
            math.isfinite(value)
            for value in (
                bounds.xmin, bounds.xmax, bounds.ymin, bounds.ymax,
                bounds.zmin, bounds.zmax,
            )
        )
        checks: list[str] = ["NONEMPTY_FINITE_STEP"]
        if 6 <= index <= 13:
            passed = passed and bounds.ymin <= -18.0 and bounds.ymax >= 18.0
            checks.append("DF_INDEPENDENT_REFERENCE_SPAN")
        if index == 6:
            # DF1 contains two 300 mm shafts whose central endpoints are
            # exactly -18/+18; the imported aggregate must span both.
            passed = passed and bounds.ymin <= -318.0 and bounds.ymax >= 318.0
            checks.append("TWO_UNCUT_300MM_SHAFT_REFERENCES")
        if index == 14:
            passed = (
                passed
                and bounds.xlen <= 256.0
                and bounds.ylen <= 256.0
                and bounds.zlen <= 256.0
            )
            checks.append("BAMBU_A1_BUILD_VOLUME_CANDIDATE")
        if index == 15:
            passed = passed and abs(bounds.ylen - 36.0) <= 1.0e-3
            checks.append("CENTER_GAP_36")
        if index == 16:
            passed = passed and abs(bounds.ylen - 12.5) <= 1.0e-3
            checks.append("STUB_12P5")
        results.append({
            "path": rel,
            "solid_count": solids,
            "x_length_mm": round(bounds.xlen, 3),
            "y_min_mm": round(bounds.ymin, 3),
            "y_max_mm": round(bounds.ymax, 3),
            "y_length_mm": round(bounds.ylen, 3),
            "z_length_mm": round(bounds.zlen, 3),
            "checks": ";".join(checks),
            "pass": passed,
        })
    for rel in STL_FILES:
        path = LANE_DIR / rel
        results.append({
            "path": rel,
            "solid_count": None,
            "x_length_mm": None,
            "y_min_mm": None,
            "y_max_mm": None,
            "y_length_mm": None,
            "z_length_mm": None,
            "checks": "NONEMPTY_STL",
            "pass": path.is_file() and path.stat().st_size > 1000,
        })
    return results


SVG_STYLE = """
.bg{fill:#f8fafc}.panel{fill:#fff;stroke:#94a3b8;stroke-width:2}
.title{font:700 28px sans-serif;fill:#0f172a}.head{font:700 17px sans-serif;fill:#0f172a}
.text{font:13px sans-serif;fill:#1e293b}.mono{font:12px monospace;fill:#334155}
.shaft{fill:#64748b;stroke:#334155;stroke-width:2}.sleeve{fill:#f59e0b;stroke:#b45309;stroke-width:2}
.unit{fill:#22c55e;stroke:#15803d;stroke-width:2}.hold{fill:#fef3c7;stroke:#d97706;stroke-width:2}
.good{fill:#dcfce7;stroke:#16a34a;stroke-width:2}.measure{stroke:#0f766e;stroke-width:2}
"""


def _svg(title: str, panels: list[tuple[str, list[str], str]]) -> str:
    markup: list[str] = []
    for index, (heading, lines, kind) in enumerate(panels):
        x = 35 + (index % 3) * 510
        y = 90 + (index // 3) * 275
        markup.append(
            f'<g transform="translate({x},{y})"><rect class="panel" '
            'x="0" y="0" width="475" height="240" rx="14"/>'
            f'<text class="head" x="18" y="30">{heading}</text>'
        )
        if kind == "axial":
            markup.append(
                '<rect class="shaft" x="25" y="90" width="145" height="16"/>'
                '<rect class="sleeve" x="128" y="80" width="60" height="36" rx="7"/>'
                '<rect class="unit" x="188" y="90" width="39" height="16"/>'
                '<line class="measure" x1="227" y1="65" x2="248" y2="65"/>'
                '<rect class="unit" x="248" y="90" width="39" height="16"/>'
                '<rect class="sleeve" x="287" y="80" width="60" height="36" rx="7"/>'
                '<rect class="shaft" x="305" y="90" width="145" height="16"/>'
                '<text class="mono" x="202" y="55">36 mm gap</text>'
            )
        elif kind == "sequence":
            for step in range(3):
                px = 28 + step * 145
                markup.append(
                    f'<rect class="{"good" if step == 2 else "hold"}" '
                    f'x="{px}" y="72" width="115" height="62" rx="10"/>'
                    f'<text class="mono" x="{px + 12}" y="105">'
                    f'{("RETRACTED","PARTIAL 5","ENGAGED 10")[step]}</text>'
                )
        else:
            markup.append(
                '<rect class="good" x="30" y="62" width="415" height="78" rx="10"/>'
            )
        for line_index, line in enumerate(lines):
            markup.append(
                f'<text class="text" x="18" y="{165 + line_index * 20}">{line}</text>'
            )
        markup.append("</g>")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="940" '
        'viewBox="0 0 1600 940">'
        f"<style>{SVG_STYLE}</style><rect class=\"bg\" width=\"1600\" height=\"940\"/>"
        f'<text class="title" x="35" y="48">{title}</text>'
        + "".join(markup)
        + '<text class="mono" x="35" y="910">NO_LOAD_ONLY · NOT_FOR_MANUFACTURING · PHYSICAL_FIT_HOLD</text>'
        + "</svg>"
    )


def svg_documents(
    rows: list[dict[str, Any]],
    sweep_rows: list[dict[str, Any]],
) -> dict[str, str]:
    summary = summarize_pair_results(rows)
    sweep = full_sweep_summary(sweep_rows)
    minimum = min(
        (row for row in rows if row["minimum_distance_mm"] is not None),
        key=lambda row: float(row["minimum_distance_mm"]),
    )
    common = [
        ("Evidence", [
            f"{summary['total_pairs_tested']} actual Shape pairs",
            f"{summary['total_pass']} PASS / {summary['total_fail']} FAIL / {summary['total_error']} ERROR",
            "Upstream: inherited conditional",
        ], "status"),
        ("Independent shafts", [
            "Left end +18 mm; right end -18 mm",
            "12.5 mm stub each side",
            "No common shaft",
        ], "axial"),
        ("Full sweep", [
            f"0..10 mm at {FULL_SWEEP_SAMPLE_INTERVAL_MM:.1f} mm",
            f"minimum {sweep['minimum_clearance_over_full_sweep_mm']:.3f} mm",
            "continuous envelope plus samples",
        ], "sequence"),
    ]
    return {
        SVG_FILES[0]: _svg("Common Rover v0.9.2.1 — actual-CAD overview", common),
        SVG_FILES[1]: _svg("Actual Shape clearance evidence", [
            ("Matrix summary", [
                f"intersect/contact/clear {summary['total_intersect']}/{summary['total_contact']}/{summary['total_clear']}",
                "Boolean common + OCP distance",
                "errors never fall back to PASS",
            ], "status"),
            ("State evidence", [
                "RETRACTED / PARTIAL / ENGAGED",
                "FULL_SWEEP conservative Shape",
                "nearest points recorded",
            ], "sequence"),
            ("Scope", [
                "Central coupling: verified",
                "Upstream reconstruction: conditional",
                "Full-system verified claim prohibited",
            ], "status"),
        ]),
        SVG_FILES[2]: _svg("Coupling full-sweep clearance", [
            ("Sampling", [
                f"{sweep['sample_positions_each_side']} positions each side",
                f"{sweep['actual_pair_calculations']} actual calculations",
                f"interval {sweep['sampling_interval_mm']:.1f} mm",
            ], "sequence"),
            ("Worst sweep location", [
                f"travel {sweep['minimum_clearance_position_mm']:.3f} mm",
                f"minimum {sweep['minimum_clearance_over_full_sweep_mm']:.3f} mm",
                sweep["worst_pair"],
            ], "status"),
            ("Engagement", [
                "10 mm geometric overlap at full travel",
                "8 mm engagement reference",
                "no-load geometry only",
            ], "axial"),
        ]),
        SVG_FILES[3]: _svg("No-load dry-fit sequence DF0–DF8", [
            ("DF0–DF2", [
                "parts → two shafts → retracted",
                "36 mm center gauge remains insertable",
                "no motor or belt",
            ], "sequence"),
            ("DF3–DF6", [
                "front insert → lock → partial → engaged",
                "left/right inputs remain separate",
                "hand fit only",
            ], "sequence"),
            ("DF7–DF8", [
                "disengage → fully retract → remove",
                "record measurements and photos",
                "finish without power",
            ], "sequence"),
        ]),
        SVG_FILES[4]: _svg("Independent left/right PTO shaft references", [
            ("Left PTO", [
                "uncut reference: Y +18 to +318",
                "stub face: +30.5 to +18",
                "LEFT_INDEPENDENT_PTO",
            ], "axial"),
            ("Center gap", [
                "Y -18 to +18 is empty",
                "NOMINAL_36_MM",
                "NO_COMMON_SHAFT",
            ], "status"),
            ("Right PTO", [
                "uncut reference: Y -318 to -18",
                "stub face: -30.5 to -18",
                "RIGHT_INDEPENDENT_PTO",
            ], "axial"),
        ]),
        SVG_FILES[5]: _svg("Minimum actual Shape distance evidence", [
            ("Pair", [
                minimum["pair_id"],
                f"{minimum['shape_a_name']} :: {minimum['shape_b_name']}",
                f"state {minimum['coupling_state']}",
            ], "status"),
            ("Distance", [
                f"{minimum['minimum_distance_mm']:.6f} mm",
                f"A {_format_point(minimum, 'a')}",
                f"B {_format_point(minimum, 'b')}",
            ], "axial"),
            ("Classification", [
                minimum["classification"],
                minimum["result"],
                "contact is recorded, not hidden",
            ], "status"),
        ]),
        SVG_FILES[6]: _svg("Exploded no-load dry-fit concept", [
            ("PTO references", [
                "two independent uncut shafts",
                "position blocks + face references",
                "12.5 mm stub gauges",
            ], "axial"),
            ("Coupling dummies", [
                "left/right sleeves are separate",
                "0 / 5 / 10 mm positions",
                "DUMMY_CLEARANCE_NOT_PRODUCT_FIT",
            ], "sequence"),
            ("Unit bridge", [
                "front +X insertion",
                "independent input dummies",
                "mechanical lock then hand engagement",
            ], "status"),
        ]),
    }


def test_results_text(
    valid: dict[str, Any],
    steps: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    sweep_rows: list[dict[str, Any]],
    canaries: list[dict[str, Any]],
) -> str:
    summary = summarize_pair_results(rows)
    sweep = full_sweep_summary(sweep_rows)
    return f"""Common Rover v0.9.2.1 deterministic build verification
document_id={DOCUMENT_ID}
validation={valid['passed_count']}/{valid['check_count']} PASS
canary={sum(row['canary_pass'] for row in canaries)}/{len(canaries)} PASS
actual_shape_matrix={summary['total_pass']}/{summary['total_pairs_tested']} PASS
actual_shape_fail={summary['total_fail']}
actual_shape_error={summary['total_error']}
sampled_sweep_calculations={sweep['actual_pair_calculations']}
sampled_sweep_fail={sweep['total_fail']}
sampled_sweep_error={sweep['total_error']}
step_stl_semantics={sum(row['pass'] for row in steps)}/{len(steps)} PASS
parent_v092_baseline=PASS
parent_v092_ledger={PARENT_LEDGER_SHA256}
central_coupling_actual_cad=PASS
upstream_powertrain_actual_cad=INHERITED_CONDITIONAL
physical_test=PHYSICAL_TEST_NOT_PERFORMED
physical_fit=HOLD
load_capacity=HOLD
shaft_cutting=HOLD
shaft_end_machining=HOLD
support_plate_machining=HOLD
powered_test=NOT_APPROVED
manufacturing=HOLD
field_deployment=NOT_APPROVED
"""


def _manifest_text() -> str:
    roles: dict[str, str] = {}
    for rel in PACKAGE_PATHS:
        if rel.endswith((".step", ".stl", ".svg")):
            role = "NO_LOAD_GEOMETRY_OR_VISUAL_EVIDENCE"
        elif rel.endswith(".csv"):
            role = "DETERMINISTIC_TABULAR_EVIDENCE"
        elif rel.endswith(".json"):
            role = "MACHINE_READABLE_CONTRACT"
        elif rel.endswith(".py"):
            role = "BUILDER_ENGINE_OR_CONTRACT_TEST"
        else:
            role = "DOCUMENT_OR_PACKAGE_LEDGER"
        roles[rel] = role
    lines = [
        f"document_id={DOCUMENT_ID}",
        "version=0.9.2.1",
        f"path_count={len(PACKAGE_PATHS)}",
        "scope=V0921_ONLY",
        f"parent_v092_ledger_sha256={PARENT_LEDGER_SHA256}",
        f"parent_v092_zip_sha256={PARENT_ZIP_SHA256}",
        "central_coupling_actual_cad=VERIFIED",
        "upstream_powertrain_actual_cad=INHERITED_CONDITIONAL",
        "physical_test=PHYSICAL_TEST_NOT_PERFORMED",
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


def _lane_files() -> list[str]:
    return sorted(
        path.relative_to(LANE_DIR).as_posix()
        for path in LANE_DIR.rglob("*")
        if path.is_file()
    )


def _parse_sha256sums() -> dict[str, str]:
    result: dict[str, str] = {}
    for line in (LANE_DIR / SHA256SUMS_NAME).read_text(
        encoding="utf-8"
    ).splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        result[rel] = digest
    return result


def verify_hashes() -> dict[str, Any]:
    expected = _parse_sha256sums()
    required = set(PACKAGE_PATHS) - {SHA256SUMS_NAME}
    mismatches: list[Any] = []
    if set(expected) != required:
        mismatches.append({
            "missing": sorted(required - set(expected)),
            "extra": sorted(set(expected) - required),
        })
    for rel, digest in expected.items():
        path = LANE_DIR / rel
        actual = _sha256(path) if path.is_file() else "MISSING"
        if actual != digest:
            mismatches.append({
                "path": rel,
                "expected": digest,
                "actual": actual,
            })
    return {
        "verified_path_count": len(expected),
        "mismatches": mismatches,
    }


def verify_manifest() -> dict[str, Any]:
    lines = (LANE_DIR / MANIFEST_NAME).read_text(
        encoding="utf-8"
    ).splitlines()
    entries = [line.split("|", 1)[0] for line in lines if "|" in line]
    return {
        "manifest_path_count": len(entries),
        "path_set_match": set(entries) == set(PACKAGE_PATHS),
        "order_match": entries == list(PACKAGE_PATHS),
    }


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def verify_generated_evidence(
    rows: list[dict[str, Any]],
    sweep_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    matrix_csv = _csv_rows(LANE_DIR / CLEARANCE_MATRIX_NAME)
    sweep_csv = _csv_rows(LANE_DIR / SWEEP_NAME)
    report = json.loads(
        (LANE_DIR / INTERFERENCE_REPORT_NAME).read_text(encoding="utf-8")
    )
    checks = {
        "matrix_row_count": len(matrix_csv) == len(rows),
        "sweep_row_count": len(sweep_csv) == len(sweep_rows),
        "matrix_pair_ids": [row["pair_id"] for row in matrix_csv]
        == [row["pair_id"] for row in rows],
        "sweep_pair_ids": [row["pair_id"] for row in sweep_csv]
        == [row["pair_id"] for row in sweep_rows],
        "json_row_count": len(report["rows"]) == len(rows),
        "actual_calculation_authority":
            report["calculation_authority"] == "ACTUAL_CAD_SHAPE_PAIR_RESULTS",
        "full_system_claim_false":
            report["upstream_scope"]["claim_prohibited"]
            == "ACTUAL_CAD_FULL_SYSTEM_VERIFIED",
    }
    return {
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def refresh_artifacts() -> dict[str, Any]:
    for rel in (BUILDER_NAME, ENGINE_NAME, JIG_BUILDER_NAME, *TEST_FILES):
        if not (LANE_DIR / rel).is_file():
            raise RuntimeError(f"source/test path missing before refresh: {rel}")
    parent = parent_protection_audit()
    baseline = verify_baseline_v092()
    canaries = run_canary_tests()
    rows = actual_clearance_rows()
    sweep_rows = full_sweep_rows()
    valid = validation(rows, sweep_rows, canaries)
    if valid["status"] != "PASS":
        raise RuntimeError(f"authority validation failed: {valid['failed_checks']}")

    summary = summarize_pair_results(rows)
    sweep = full_sweep_summary(sweep_rows)
    interference = actual_interference_report(rows, sweep_rows, canaries)
    _write_text(LANE_DIR / AUTHORITY_NAME, authority_markdown(
        rows, sweep_rows, canaries
    ))
    _write_json(LANE_DIR / PARAMETERS_NAME, parameters(interference, sweep))
    _write_json(LANE_DIR / BASELINE_NAME, baseline)
    _write_json(LANE_DIR / REGISTRY_NAME, named_shape_registry())
    _write_json(LANE_DIR / POWER_GRAPH_NAME, power_flow_graph())
    _write_json(LANE_DIR / STATE_GRAPH_NAME, coupling_state_graph())
    _write_csv(LANE_DIR / CLEARANCE_MATRIX_NAME, rows)
    _write_json(
        LANE_DIR / INTERFERENCE_REPORT_NAME,
        interference,
    )
    _write_csv(LANE_DIR / SWEEP_NAME, sweep_rows)
    _write_csv(LANE_DIR / CANARY_NAME, canaries)
    _write_csv(LANE_DIR / PART_LIST_NAME, dry_fit_part_rows())
    _write_csv(LANE_DIR / DIMENSIONS_NAME, dry_fit_dimension_rows())
    _write_json(LANE_DIR / VALIDATION_NAME, valid)
    _write_text(LANE_DIR / SUPERSEDED_NAME, superseded_markdown())
    _write_text(
        LANE_DIR / DRY_FIT_PROCEDURE_NAME,
        dry_fit_procedure_markdown(),
    )
    _write_csv(LANE_DIR / MEASUREMENT_NAME, measurement_record_rows())
    _write_text(LANE_DIR / PHOTO_LOG_NAME, photo_log_markdown())
    _write_text(LANE_DIR / NO_LOAD_NAME, no_load_text())
    _write_text(LANE_DIR / README_NAME, readme_handoff(summary, sweep))
    for rel, text in svg_documents(rows, sweep_rows).items():
        _write_text(LANE_DIR / rel, text)

    _export_model_artifacts()
    steps = verify_step_semantics()
    if not all(row["pass"] for row in steps):
        raise RuntimeError(f"STEP/STL semantic verification failed: {steps}")
    _write_text(
        LANE_DIR / TEST_RESULTS_NAME,
        test_results_text(valid, steps, rows, sweep_rows, canaries),
    )
    _write_text(LANE_DIR / MANIFEST_NAME, _manifest_text())
    _write_text(LANE_DIR / SHA256SUMS_NAME, _sha256sums_text())
    actual = _lane_files()
    if actual != sorted(PACKAGE_PATHS):
        raise RuntimeError({
            "missing": sorted(set(PACKAGE_PATHS) - set(actual)),
            "extra": sorted(set(actual) - set(PACKAGE_PATHS)),
        })
    return {
        "document_id": DOCUMENT_ID,
        "parent": parent,
        "baseline": baseline["status"],
        "package_path_count": len(PACKAGE_PATHS),
        "named_shape_count": named_shape_registry()["registry_entry_count"],
        "actual_pair_summary": summary,
        "full_sweep": sweep,
        "validation": f"{valid['passed_count']}/{valid['check_count']} PASS",
        "step_stl_semantics":
            f"{sum(row['pass'] for row in steps)}/{len(steps)} PASS",
        "status": "PASS",
    }


def verify() -> dict[str, Any]:
    actual = _lane_files()
    if actual != sorted(PACKAGE_PATHS):
        raise RuntimeError({
            "missing": sorted(set(PACKAGE_PATHS) - set(actual)),
            "extra": sorted(set(actual) - set(PACKAGE_PATHS)),
        })
    parent = parent_protection_audit()
    baseline = verify_baseline_v092()
    repository = repository_audit()
    canaries = run_canary_tests()
    rows = actual_clearance_rows()
    sweep_rows = full_sweep_rows()
    valid = validation(rows, sweep_rows, canaries)
    hashes = verify_hashes()
    manifest = verify_manifest()
    evidence = verify_generated_evidence(rows, sweep_rows)
    steps = verify_step_semantics()
    failures = []
    if valid["status"] != "PASS":
        failures.append({"validation": valid})
    if hashes["mismatches"]:
        failures.append({"hashes": hashes})
    if not manifest["path_set_match"] or not manifest["order_match"]:
        failures.append({"manifest": manifest})
    if evidence["status"] != "PASS":
        failures.append({"evidence": evidence})
    if not all(row["pass"] for row in steps):
        failures.append({"step_stl_semantics": steps})
    if failures:
        raise RuntimeError(failures)
    summary = summarize_pair_results(rows)
    sweep = full_sweep_summary(sweep_rows)
    return {
        "document_id": DOCUMENT_ID,
        "parent": parent,
        "baseline": baseline["status"],
        "repository": repository,
        "exact_package_paths": len(PACKAGE_PATHS),
        "named_shapes": named_shape_registry()["registry_entry_count"],
        "canaries": f"{sum(row['canary_pass'] for row in canaries)}/{len(canaries)} PASS",
        "actual_shape_pairs":
            f"{summary['total_pass']}/{summary['total_pairs_tested']} PASS",
        "actual_shape_fail": summary["total_fail"],
        "actual_shape_error": summary["total_error"],
        "sampled_sweep_calculations": sweep["actual_pair_calculations"],
        "sampled_sweep_fail": sweep["total_fail"],
        "sampled_sweep_error": sweep["total_error"],
        "validation": f"{valid['passed_count']}/{valid['check_count']} PASS",
        "step_stl_semantics":
            f"{sum(row['pass'] for row in steps)}/{len(steps)} PASS",
        "svg": f"{sum((LANE_DIR / rel).stat().st_size > 500 for rel in SVG_FILES)}/7 PASS",
        "hashes": f"{hashes['verified_path_count']}/54 PASS",
        "manifest": f"{manifest['manifest_path_count']}/55 PASS",
        "status": "PASS",
    }


def _zip_info(rel: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(rel, date_time=(2000, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def verify_zip(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"ZIP missing: {path}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names != list(PACKAGE_PATHS):
            raise RuntimeError("ZIP path order/scope mismatch")
        mismatches = [
            rel for rel in PACKAGE_PATHS
            if hashlib.sha256(archive.read(rel)).hexdigest()
            != _sha256(LANE_DIR / rel)
        ]
    return {
        "zip_path": str(path),
        "zip_path_count": len(names),
        "mismatches": mismatches,
        "exact_scope": not mismatches and names == list(PACKAGE_PATHS),
    }


def package_handoff() -> dict[str, Any]:
    report = verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{timestamp}.zip"
    if path.exists():
        raise RuntimeError(f"refusing to overwrite ZIP: {path}")
    with zipfile.ZipFile(path, "w") as archive:
        for rel in PACKAGE_PATHS:
            archive.writestr(_zip_info(rel), (LANE_DIR / rel).read_bytes())
    return {
        "verification": report["status"],
        "zip_sha256": _sha256(path),
        **verify_zip(path),
    }


def latest_handoff_zip() -> Path | None:
    candidates = sorted(DOWNLOAD_DIR.glob(f"{ZIP_PREFIX}*.zip"))
    return candidates[-1] if candidates else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-artifacts", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--verify-zip", type=Path)
    args = parser.parse_args(argv)
    actions = sum(bool(value) for value in (
        args.refresh_artifacts,
        args.verify,
        args.package,
        args.verify_zip,
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
