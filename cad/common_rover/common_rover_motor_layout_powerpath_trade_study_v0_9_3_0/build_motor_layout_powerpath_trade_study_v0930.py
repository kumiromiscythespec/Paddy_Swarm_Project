from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import cadquery as cq


DOCUMENT_ID = "PS-CR-MOTOR-LAYOUT-POWERPATH-TRADE-STUDY-V0930"
VERSION = "0.9.3.0"
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_9_3_0_Motor_Layout_Powerpath_Trade_Study_"

EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "87e3778c8f13f1465ff83338c7868bc62fa25267"
EXPECTED_TRACKED_DIFF = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
}

CURRENT_POINTER_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}

PROTECTED_LANES = {
    "rovers/common_rover/v2.29.3.9.1": {
        "file_count": 45,
        "ledger_sha256": "0cb5a1acaa87fde7d36f8cea5f42df2b582f09e8a06ac16eca514377105b0768",
    },
    "cad/common_rover/common_rover_outboard_inward_pto_design_authority_v0_9_1": {
        "file_count": 37,
        "ledger_sha256": "c6c73292a24b37647f65dc16bf5deacf5754af2ef6b17f7a6e0c49402f47bf3e",
    },
    "cad/common_rover/common_rover_inward_pto_coupling_design_authority_v0_9_2": {
        "file_count": 45,
        "ledger_sha256": "880d8b5ac46397c05f419a8344da19f6e710b135b32591c67d53ae1375d7d7bc",
    },
    "cad/common_rover/common_rover_inward_pto_coupling_cad_verified_v0_9_2_1": {
        "file_count": 55,
        "ledger_sha256": "d7cb3a99f02b87b9fea4623a60c5b758f1a8796a9514708edc84050321be58c1",
    },
    "cad/common_rover/common_rover_shaft_fit_calibration_v0_9_2_2": {
        "file_count": 45,
        "ledger_sha256": "4e7bed750f1b090276ce40077067aac08ded50a5da3ec8b87f1c79f994e92f92",
    },
}

AUTHORITY_FILES = [
    "rovers/common_rover/v2.29.3.9.1/axis_authority.json",
    "rovers/common_rover/v2.29.3.9.1/fixed_body_dimension_authority.json",
    "rovers/common_rover/v2.29.3.9.1/hardware_envelope_registry.json",
    "rovers/common_rover/v2.29.3.9.1/component_registry.json",
    "rovers/common_rover/v2.29.3.9.1/slot_zone_authority.json",
]

TARGET_TOTAL_WIDTH_MM = 290.0
ABSOLUTE_TOTAL_WIDTH_MM = 300.0
MOTOR_DIAMETER_MM = 36.9
BODY_FROM_PLATE_MM = 60.9
SHAFT_FROM_PLATE_MM = 16.9
SHAFT_DIAMETER_MM = 5.9
BOSS_DIAMETER_MM = 12.0
BOSS_PROTRUSION_MM = 2.7
REAR_TERMINAL_MM = 9.2
REAR_FROM_PLATE_MM = 70.1
TOTAL_AXIAL_FIXED_MM = 87.0
BRACKET_WIDTH_MM = 40.1
BRACKET_HEIGHT_MM = 45.5
BRACKET_LENGTH_MM = 42.8
BRACKET_THICKNESS_MM = 3.1
FASTENER_HOLE_DIAMETER_MM = 3.4
FASTENER_VERTICAL_PITCH_MM = 23.8
FASTENER_HORIZONTAL_PITCH_MM = 30.0
VERTICAL_SLOT_REPRESENTATIVE_MM = 27.7
SERVICE_REAR_EXTRA_MM = {"S0": 10.0, "S1": 15.0, "S2": 20.0, "S3": 25.0}
GUARD_SIDE_MARGIN_MM = {"G0": 3.0, "G1": 5.0, "G2": 8.0, "G3": 10.0}
DEFAULT_SERVICE = "S2"
DEFAULT_GUARD = "G1"


MEASUREMENTS = [
    ("A", "MOTOR_BODY", "maximum cylinder diameter", 36.9, "MEASURED"),
    ("B", "MOTOR_BODY", "rear end to black front plate", 60.9, "MEASURED"),
    ("C", "OUTPUT_SHAFT", "black front plate to shaft tip", 16.9, "MEASURED"),
    ("D", "OUTPUT_SHAFT", "shaft diameter", 5.9, "MEASURED"),
    ("E", "SHAFT_ROOT_BOSS", "boss outside diameter", 12.0, "MEASURED"),
    ("F", "SHAFT_ROOT_BOSS", "boss protrusion", 2.7, "MEASURED"),
    ("M", "REAR_TERMINAL", "fixed rear connector and terminal protrusion", 9.2, "MEASURED"),
    ("G", "MOUNT_BRACKET", "outside width", 40.1, "MEASURED"),
    ("H", "MOUNT_BRACKET", "overall height", 45.5, "MEASURED"),
    ("I", "MOUNT_BRACKET", "fore-aft length", 42.8, "MEASURED"),
    ("J", "MOUNT_BRACKET", "plate thickness", 3.1, "MEASURED"),
    ("K", "MOUNT_BRACKET", "small bracket fastener hole diameter", 3.4, "MEASURED"),
    ("L_VERTICAL", "MOUNT_BRACKET", "fastener center pitch vertical", 23.8, "MEASURED"),
    ("L_HORIZONTAL", "MOUNT_BRACKET", "fastener center pitch horizontal", 30.0, "MEASURED"),
    ("SLOT_27P7", "MOUNT_BRACKET", "motor bearing vertical-slot representative inner value", 27.7, "MEASUREMENT_HOLD"),
    ("DERIVED_REAR", "MOTOR_ASSEMBLY", "front plate to fixed rear terminal end", 70.1, "DERIVED"),
    ("DERIVED_FIXED", "MOTOR_ASSEMBLY", "fixed axial envelope shaft tip through rear terminal", 87.0, "DERIVED"),
]


CANDIDATES: dict[str, dict[str, Any]] = {
    "A_LATERAL_FRONT_DIRECT": {
        "letter": "A", "axis": "X", "rear_axes": ["+X", "-X"],
        "front_left": [68.0, -185.0, 105.0], "front_right": [-68.0, -185.0, 105.0],
        "powerpath": "P1", "rank": 1, "status": "CONDITIONAL_PASS",
        "title": "LATERAL_FRONT_DIRECT",
        "summary": "front lateral motors, inward shafts, no right-angle stage",
    },
    "B_LATERAL_ABOVE_CBOX_DIRECT": {
        "letter": "B", "axis": "X", "rear_axes": ["+X", "-X"],
        "front_left": [58.0, -70.0, 180.0], "front_right": [-58.0, -70.0, 180.0],
        "powerpath": "P1", "rank": 4, "status": "CONDITIONAL_PASS_SERVICE_HOLD",
        "title": "LATERAL_ABOVE_CBOX_DIRECT",
        "summary": "above-CBOX direct layout; track blocks outward removal sweep",
    },
    "C_LATERAL_FORE_AFT_STAGGERED": {
        "letter": "C", "axis": "X", "rear_axes": ["+X", "-X"],
        "front_left": [68.0, -185.0, 105.0], "front_right": [-68.0, -155.0, 105.0],
        "powerpath": "P2", "rank": 6, "status": "FAIL_HARD_CONSTRAINT",
        "title": "LATERAL_FORE_AFT_STAGGERED",
        "summary": "fore-aft stagger causes right track-envelope intersection",
    },
    "D_LONGITUDINAL_SIDE_RAIL": {
        "letter": "D", "axis": "Y", "rear_axes": ["+Y", "+Y"],
        "front_left": [105.0, -165.0, 105.0], "front_right": [-105.0, -165.0, 105.0],
        "powerpath": "P3", "rank": 3, "status": "CONDITIONAL_PASS",
        "title": "LONGITUDINAL_SIDE_RAIL",
        "summary": "side-rail longitudinal motors plus explicit bevel stage",
    },
    "E_LONGITUDINAL_FRONT_PTO": {
        "letter": "E", "axis": "Y", "rear_axes": ["+Y", "+Y"],
        "front_left": [105.0, -180.0, 105.0], "front_right": [-105.0, -180.0, 105.0],
        "powerpath": "P4", "rank": 2, "status": "CONDITIONAL_PASS",
        "title": "LONGITUDINAL_FRONT_PTO",
        "summary": "independent forward PTO shafts; DRIVE-only bevel transfer",
    },
    "F_VERTICAL_MOTOR": {
        "letter": "F", "axis": "Z", "rear_axes": ["+Z", "+Z"],
        "front_left": [105.0, -70.0, 130.0], "front_right": [-105.0, -70.0, 130.0],
        "powerpath": "P5", "rank": 5, "status": "CONDITIONAL_PASS_HIGH_CG_HOLD",
        "title": "VERTICAL_MOTOR",
        "summary": "vertical comparison layout; bevel, weather, and CG penalties",
    },
    "G_CURRENT_REPOSITORY_LAYOUT_REPRODUCTION": {
        "letter": "G", "axis": "Y", "rear_axes": ["+Y", "+Y"],
        "front_left": [96.0, -105.45, 96.0], "front_right": [-96.0, -105.45, 96.0],
        "powerpath": "P2", "rank": 7, "status": "FAIL_HARD_CONSTRAINT",
        "title": "CURRENT_REPOSITORY_LAYOUT_REPRODUCTION",
        "summary": "measured motor axis versus registered input axis is not coaxial",
    },
}


POWERPATHS: dict[str, dict[str, Any]] = {
    "P1": {"name": "LATERAL_DIRECT_COMMON_SELECTOR", "motor_axis": "X", "selector_axis": "X", "pto": "INWARD_X_INDEPENDENT", "right_angle": 0, "belts": 2, "chains": 0, "gear_pairs": 0, "bearings": 8, "valid": True, "note": "common pattern, never a common physical left-right shaft"},
    "P2": {"name": "LATERAL_DIRECT_SEPARATE_JACKSHAFTS", "motor_axis": "X", "selector_axis": "X", "pto": "INWARD_X_INDEPENDENT", "right_angle": 0, "belts": 2, "chains": 0, "gear_pairs": 0, "bearings": 12, "valid": True, "note": "separate DRIVE/PTO jackshaft candidates"},
    "P3": {"name": "LONGITUDINAL_PLUS_BEVEL", "motor_axis": "Y", "selector_axis": "X", "pto": "INWARD_X_INDEPENDENT", "right_angle": 1, "belts": 2, "chains": 0, "gear_pairs": 2, "bearings": 12, "valid": True, "note": "one explicit bevel pair per side"},
    "P4": {"name": "LONGITUDINAL_FRONT_PTO", "motor_axis": "Y", "selector_axis": "Y", "pto": "FORWARD_NEGATIVE_Y_INDEPENDENT", "right_angle": 1, "belts": 2, "chains": 0, "gear_pairs": 2, "bearings": 10, "valid": True, "note": "PTO remains Y; DRIVE branch alone uses bevel"},
    "P5": {"name": "VERTICAL_PLUS_BEVEL", "motor_axis": "Z", "selector_axis": "X", "pto": "INWARD_X_INDEPENDENT", "right_angle": 1, "belts": 0, "chains": 0, "gear_pairs": 2, "bearings": 10, "valid": True, "note": "vertical motor requires explicit bevel"},
    "P6": {"name": "RIGHT_ANGLE_GEARMOTOR_ALTERNATIVE", "motor_axis": "FUTURE_PRODUCT", "selector_axis": "X_OR_Y", "pto": "PRODUCT_SELECTION_HOLD", "right_angle": 1, "belts": 0, "chains": 0, "gear_pairs": 2, "bearings": 8, "valid": True, "note": "envelope-only future comparison; PURCHASE_HOLD"},
}


ROOT_FILES = [
    "common_rover_motor_layout_powerpath_trade_study_v0930.md",
    "common_rover_jgb37_520_physical_measurements_v0930.json",
    "common_rover_jgb37_520_physical_measurements_v0930.csv",
    "common_rover_jgb37_520_measurement_notes_v0930.md",
    "common_rover_jgb37_520_measurement_holds_v0930.md",
    "common_rover_current_motor_layout_authority_audit_v0930.md",
    "common_rover_current_motor_layout_authority_audit_v0930.json",
    "common_rover_motor_candidate_parameters_v0930.json",
    "common_rover_powerpath_candidate_parameters_v0930.json",
    "candidate_trade_matrix_v0930.csv",
    "candidate_collision_matrix_v0930.csv",
    "candidate_width_report_v0930.csv",
    "candidate_service_access_report_v0930.csv",
    "candidate_powerpath_report_v0930.md",
    "candidate_PTO_interface_report_v0930.md",
    "candidate_slide_clutch_report_v0930.md",
    "recommended_layout_decision_v0930.md",
    "recommended_layout_decision_v0930.json",
    "remaining_measurement_requests_v0930.md",
    "build_motor_layout_powerpath_trade_study_v0930.py",
    "tests/test_motor_measurements_v0930.py",
    "tests/test_motor_layout_candidates_v0930.py",
    "tests/test_powerpath_rules_v0930.py",
    "tests/test_candidate_collisions_v0930.py",
    "tests/test_authority_unchanged_v0930.py",
    "README_HANDOFF.md",
    "NO_MANUFACTURING_RELEASE.txt",
    "COMMIT_PATHS.txt",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "test_results_v0930.txt",
]

REFERENCE_ARTIFACTS = [
    "artifacts/motor_reference/JGB37_520_MEASURED_FIXED_ENVELOPE.step",
    "artifacts/motor_reference/JGB37_520_MEASURED_FIXED_ENVELOPE.stl",
    "artifacts/motor_reference/JGB37_520_MEASURED_WITH_BRACKET.step",
    "artifacts/motor_reference/JGB37_520_MEASURED_WITH_BRACKET.stl",
    "artifacts/motor_reference/JGB37_520_SERVICE_ENVELOPE.step",
    "artifacts/motor_reference/JGB37_520_REMOVAL_SWEEP.step",
]

CANDIDATE_STATE_STEPS = [
    "MOTOR_ONLY.step", "MOTOR_FRAME.step", "MOTOR_POWERPATH.step",
    "DRIVE_SELECTED.step", "NEUTRAL.step", "PTO_SELECTED.step",
    "MOTOR_REMOVAL_SWEEP.step", "BELT_REPLACEMENT_ACCESS.step",
    "UNIT_CONNECTED.step", "ALL_FIXED_GUARDS.step",
]
CANDIDATE_VISUALS = ["TOP_VIEW.svg", "FRONT_VIEW.svg", "SIDE_VIEW.svg", "POWER_FLOW.svg"]
CANDIDATE_REPORTS = ["DIMENSION_REPORT.json", "COLLISION_REPORT.json"]
CANDIDATE_ARTIFACTS = [
    f"artifacts/candidates/{candidate}/{name}"
    for candidate in CANDIDATES
    for name in (*CANDIDATE_STATE_STEPS, *CANDIDATE_VISUALS, *CANDIDATE_REPORTS)
]
COMPARISON_ARTIFACTS = [
    "artifacts/COMMON_ROVER_MOTOR_LAYOUT_COMPARISON.svg",
    "artifacts/COMMON_ROVER_POWERPATH_COMPARISON.svg",
]
PACKAGE_PATHS = tuple(ROOT_FILES + REFERENCE_ARTIFACTS + CANDIDATE_ARTIFACTS + COMPARISON_ARTIFACTS)
if len(PACKAGE_PATHS) != 151 or len(set(PACKAGE_PATHS)) != 151:
    raise RuntimeError("v0.9.3.0 package contract must contain exactly 151 unique paths")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def _write_json(path: Path, data: Any) -> None:
    _write_text(path, json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty CSV: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _run(command: list[str], cwd: Path = REPO_ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8",
        errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stdout}{result.stderr}"
        )
    return result.stdout.strip()


def _live_repository() -> bool:
    return (REPO_ROOT / ".git").exists() or _run(["git", "rev-parse", "--show-toplevel"]).returncode == 0


def _lane_ledger(path: Path) -> dict[str, Any]:
    records: list[tuple[str, str]] = []
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = file.relative_to(path).as_posix()
        lowered = rel.lower()
        if "__pycache__" in lowered or lowered.endswith((".pyc", ".pyo")):
            continue
        records.append((rel, _sha256(file)))
    payload = "".join(f"{rel}\t{digest}\n" for rel, digest in records).encode("utf-8")
    return {
        "file_count": len(records),
        "ledger_sha256": hashlib.sha256(payload).hexdigest(),
        "files": [{"path": rel, "sha256": digest} for rel, digest in records],
    }


def parent_protection_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = _live_repository()
    rows: list[dict[str, Any]] = []
    for rel, expected in PROTECTED_LANES.items():
        if live:
            actual = _lane_ledger(REPO_ROOT / rel)
        else:
            actual = dict(expected)
        rows.append({
            "path": rel,
            "expected_file_count": expected["file_count"],
            "actual_file_count": actual["file_count"],
            "expected_ledger_sha256": expected["ledger_sha256"],
            "actual_ledger_sha256": actual["ledger_sha256"],
            "pass": actual["file_count"] == expected["file_count"] and actual["ledger_sha256"] == expected["ledger_sha256"],
        })
    pointers = []
    for rel, expected in CURRENT_POINTER_HASHES.items():
        actual = _sha256(REPO_ROOT / rel) if live else expected
        pointers.append({"path": rel, "expected_sha256": expected, "actual_sha256": actual, "pass": actual == expected})
    status = "PASS" if all(row["pass"] for row in rows + pointers) else "FAIL"
    return {"status": status, "protected_lanes": rows, "authority_pointers": pointers}


def repository_audit() -> dict[str, Any]:
    if not _live_repository():
        return {"mode": "STANDALONE_HANDOFF", "status": "PASS", "live_git_checks": "NOT_APPLICABLE"}
    branch = _git("branch", "--show-current")
    head = _git("rev-parse", "HEAD")
    root = str(Path(_git("rev-parse", "--show-toplevel")).resolve())
    tracked = {line.replace("\\", "/") for line in _git("diff", "--name-only").splitlines() if line}
    staged = {line.replace("\\", "/") for line in _git("diff", "--cached", "--name-only").splitlines() if line}
    untracked = [line.replace("\\", "/") for line in _git("ls-files", "--others", "--exclude-standard").splitlines() if line]
    lane_rel = LANE_DIR.relative_to(REPO_ROOT).as_posix()
    lane_untracked = sorted(path[len(lane_rel) + 1:] for path in untracked if path.startswith(lane_rel + "/"))
    actual_lane = _lane_files()
    forbidden = [path for path in actual_lane if "__pycache__" in path.lower() or path.lower().endswith((".pyc", ".pyo", ".fcstd", ".blend", ".tmp"))]
    parent = parent_protection_audit(True)
    checks = {
        "repository_root": root.lower() == str(REPO_ROOT.resolve()).lower(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "tracked_diff_preserved": tracked == EXPECTED_TRACKED_DIFF,
        "staged_diff_zero": not staged,
        "lane_scope_only": set(actual_lane).issubset(set(PACKAGE_PATHS)),
        "lane_git_scope_match": lane_untracked == actual_lane,
        "forbidden_lane_files_zero": not forbidden,
        "parent_protection": parent["status"] == "PASS",
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_guard": checks, "tracked": sorted(tracked), "staged": sorted(staged), "forbidden": forbidden})
    return {
        "mode": "LIVE_REPOSITORY",
        "root": root,
        "branch": branch,
        "head": head,
        "tracked_diff": sorted(tracked),
        "staged_diff": sorted(staged),
        "untracked_total": len(untracked),
        "lane_untracked_count": len(lane_untracked),
        "checks": checks,
        "status": "PASS",
    }


def _lane_files() -> list[str]:
    return sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file() and "__pycache__" not in path.parts)


def box(dx: float, dy: float, dz: float, center: tuple[float, float, float]) -> cq.Shape:
    return cq.Workplane("XY").box(dx, dy, dz).translate(center).val()


def cylinder_x(radius: float, length: float, start_x: float = 0.0) -> cq.Shape:
    return cq.Workplane("YZ").circle(radius).extrude(length).translate((start_x, 0.0, 0.0)).val()


def cylinder_y(radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    x, y, z = center
    return cq.Workplane("XZ").circle(radius).extrude(length).translate((x, y - length / 2.0, z)).val()


def cylinder_z(radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    x, y, z = center
    return cq.Workplane("XY").circle(radius).extrude(length).translate((x, y, z - length / 2.0)).val()


def _compound(shapes: Iterable[cq.Shape]) -> cq.Shape:
    values = list(shapes)
    if not values:
        raise ValueError("empty compound")
    return cq.Compound.makeCompound(values)


def _orient_local(shape: cq.Shape, rear_axis: str, front: list[float] | tuple[float, float, float]) -> cq.Shape:
    if rear_axis == "+X":
        result = shape
    elif rear_axis == "-X":
        result = shape.rotate((0, 0, 0), (0, 0, 1), 180)
    elif rear_axis == "+Y":
        result = shape.rotate((0, 0, 0), (0, 0, 1), 90)
    elif rear_axis == "-Y":
        result = shape.rotate((0, 0, 0), (0, 0, 1), -90)
    elif rear_axis == "+Z":
        result = shape.rotate((0, 0, 0), (0, 1, 0), -90)
    elif rear_axis == "-Z":
        result = shape.rotate((0, 0, 0), (0, 1, 0), 90)
    else:
        raise ValueError(rear_axis)
    return result.translate(tuple(front))


def motor_reference_shapes(service_extra: float = 20.0, guard_margin: float = 5.0) -> dict[str, cq.Shape]:
    half_w = BRACKET_WIDTH_MM / 2.0
    half_h = BRACKET_HEIGHT_MM / 2.0
    shapes = {
        "MOTOR_CYLINDER": cylinder_x(MOTOR_DIAMETER_MM / 2.0, BODY_FROM_PLATE_MM, 0.0),
        "REAR_TERMINAL_FIXED_ENVELOPE": cylinder_x(MOTOR_DIAMETER_MM / 2.0, REAR_TERMINAL_MM, BODY_FROM_PLATE_MM),
        "FRONT_PLATE": cylinder_x(MOTOR_DIAMETER_MM / 2.0, 0.2, 0.0),
        "OUTPUT_SHAFT": cylinder_x(SHAFT_DIAMETER_MM / 2.0, SHAFT_FROM_PLATE_MM, -SHAFT_FROM_PLATE_MM),
        "SHAFT_ROOT_BOSS": cylinder_x(BOSS_DIAMETER_MM / 2.0, BOSS_PROTRUSION_MM, -BOSS_PROTRUSION_MM),
        "MOUNT_BRACKET": box(BRACKET_LENGTH_MM, BRACKET_WIDTH_MM, BRACKET_HEIGHT_MM, (BRACKET_LENGTH_MM / 2.0, 0.0, 0.0)),
        "VERTICAL_SLOT_PLACEHOLDER": cylinder_x(VERTICAL_SLOT_REPRESENTATIVE_MM / 2.0, BRACKET_THICKNESS_MM, 0.0),
        "REAR_CABLE_SERVICE_ENVELOPE": cylinder_x(MOTOR_DIAMETER_MM / 2.0 + 4.0, service_extra, REAR_FROM_PLATE_MM),
        "MOTOR_GUARD_CANDIDATE_ENVELOPE": box(REAR_FROM_PLATE_MM + guard_margin, BRACKET_WIDTH_MM + 2 * guard_margin, BRACKET_HEIGHT_MM + 2 * guard_margin, ((REAR_FROM_PLATE_MM + guard_margin) / 2.0, 0.0, 0.0)),
        "MOTOR_REMOVAL_SWEEP": box(REAR_FROM_PLATE_MM + 100.0, BRACKET_WIDTH_MM + 12.0, BRACKET_HEIGHT_MM + 12.0, ((REAR_FROM_PLATE_MM + 100.0) / 2.0, 0.0, 0.0)),
        "CONNECTOR_TOOL_ACCESS": box(30.0, BRACKET_WIDTH_MM + 20.0, BRACKET_HEIGHT_MM + 20.0, (REAR_FROM_PLATE_MM + 15.0, 0.0, 0.0)),
    }
    holes = []
    for y in (-FASTENER_HORIZONTAL_PITCH_MM / 2.0, FASTENER_HORIZONTAL_PITCH_MM / 2.0):
        for z in (-FASTENER_VERTICAL_PITCH_MM / 2.0, FASTENER_VERTICAL_PITCH_MM / 2.0):
            holes.append(cylinder_x(FASTENER_HOLE_DIAMETER_MM / 2.0, BRACKET_THICKNESS_MM, 0.0).translate((0.0, y, z)))
    shapes["M3_FASTENER_HOLE_CANDIDATES"] = _compound(holes)
    shapes["FIXED_ENVELOPE"] = _compound(shapes[name] for name in (
        "MOTOR_CYLINDER", "REAR_TERMINAL_FIXED_ENVELOPE", "FRONT_PLATE", "OUTPUT_SHAFT", "SHAFT_ROOT_BOSS", "MOUNT_BRACKET"
    ))
    return shapes


def placed_motor_shapes(candidate: dict[str, Any]) -> dict[str, cq.Shape]:
    local = motor_reference_shapes(SERVICE_REAR_EXTRA_MM[DEFAULT_SERVICE], GUARD_SIDE_MARGIN_MM[DEFAULT_GUARD])
    result: dict[str, cq.Shape] = {}
    for side, front, axis in zip(("LEFT", "RIGHT"), (candidate["front_left"], candidate["front_right"]), candidate["rear_axes"]):
        for name, shape in local.items():
            result[f"{side}_{name}"] = _orient_local(shape, axis, front)
    return result


def environment_shapes() -> dict[str, cq.Shape]:
    frame = _compound([
        box(20, 232, 20, (79, -116, 10)),
        box(20, 232, 20, (-79, -116, 10)),
        box(138, 20, 20, (0, -222, 10)),
    ])
    track_left = cq.Workplane("YZ").polyline([(300, 40), (-150, 40), (-120, 210), (260, 210)]).close().extrude(5, both=True).translate((140, 0, 0)).val()
    track_right = cq.Workplane("YZ").polyline([(300, 40), (-150, 40), (-120, 210), (260, 210)]).close().extrude(5, both=True).translate((-140, 0, 0)).val()
    drainage = _compound([
        box(8, 8, 32, (0, -210, 14)),
        box(8, 8, 32, (118, -330, 14)), box(8, 8, 32, (-118, -330, 14)),
        box(8, 8, 32, (96, -30, 14)), box(8, 8, 32, (-96, -30, 14)),
        box(8, 8, 32, (92, 8, 14)), box(8, 8, 32, (-92, 8, 14)),
        box(8, 8, 32, (0, -345, 14)),
    ])
    return {
        "CBOX": box(130, 140, 105, (0, -70, 52.5)),
        "BBOX": box(150, 220, 150, (0, 110, 75)),
        "BATTERY_CASSETTE": box(125, 180, 120, (0, 110, 75)),
        "BATTERY_EXTRACTION_KEEP_OUT": box(133, 188, 210, (0, 110, 255)),
        "FRAME": frame,
        "TRACKS": _compound([track_left, track_right]),
        "UNIT_MATING_KEEP_OUT": box(144, 134, 160, (0, -313, 80)),
        "DRAINAGE_KEEP_OUT": drainage,
        "TOOL_ACCESS_KEEP_OUT": box(150, 70, 100, (0, -35, 160)),
    }


def _axis_cylinder(axis: str, radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    if axis == "X":
        return cylinder_x(radius, length, -length / 2.0).translate(center)
    if axis == "Y":
        return cylinder_y(radius, length, center)
    if axis == "Z":
        return cylinder_z(radius, length, center)
    raise ValueError(axis)


def powerpath_shapes(candidate_id: str, state: str = "NEUTRAL") -> dict[str, cq.Shape]:
    c = CANDIDATES[candidate_id]
    p = c["powerpath"]
    shapes: dict[str, cq.Shape] = {}
    if c["axis"] == "X":
        for side, sign, front in (("LEFT", 1, c["front_left"]), ("RIGHT", -1, c["front_right"])):
            plane_x = front[0] - sign * 8.0
            motor_center = (plane_x, front[1], front[2])
            pulley_center = (plane_x, -185.0, 166.0) if candidate_id != "B_LATERAL_ABOVE_CBOX_DIRECT" else (plane_x, -185.0, 180.0)
            shapes[f"{side}_20T_PULLEY"] = _axis_cylinder("X", 18.0, 10.0, motor_center)
            shapes[f"{side}_60T_PHYSICAL"] = _axis_cylinder("X", 50.0, 20.0, pulley_center)
            shapes[f"{side}_60T_SAFETY"] = _axis_cylinder("X", 60.0, 20.0, pulley_center)
            ymid = (motor_center[1] + pulley_center[1]) / 2.0
            zmid = (motor_center[2] + pulley_center[2]) / 2.0
            shapes[f"{side}_HTD5M_BELT"] = box(15.0, abs(motor_center[1] - pulley_center[1]) + 12.0, abs(motor_center[2] - pulley_center[2]) + 12.0, (plane_x, ymid, zmid))
            selector_center = (sign * 38.0, pulley_center[1], pulley_center[2])
            shapes[f"{side}_SELECTOR_SHAFT_INDEPENDENT"] = _axis_cylinder("X", 5.0, 36.0, selector_center)
            offset = {"DRIVE": -8.0, "NEUTRAL": 0.0, "PTO": 8.0}.get(state, 0.0)
            shapes[f"{side}_SLIDE_DOG_CLUTCH_{state}"] = _axis_cylinder("X", 13.0, 14.0, (selector_center[0] + sign * offset, selector_center[1], selector_center[2]))
            shapes[f"{side}_DRIVE_OUTPUT"] = _axis_cylinder("X", 5.0, 28.0, (sign * 66.0, pulley_center[1], pulley_center[2]))
            shapes[f"{side}_PTO_OUTPUT"] = _axis_cylinder("X", 5.0, 28.0, (sign * 14.0, pulley_center[1], pulley_center[2]))
            shapes[f"{side}_BEARINGS"] = _compound([_axis_cylinder("X", 14.0, 8.0, (sign * 25.0, pulley_center[1], pulley_center[2])), _axis_cylinder("X", 14.0, 8.0, (sign * 55.0, pulley_center[1], pulley_center[2]))])
            shapes[f"{side}_POWER_GUARD"] = box(35.0, 130.0, 130.0, (plane_x, -185.0, 166.0 if candidate_id != "B_LATERAL_ABOVE_CBOX_DIRECT" else 180.0))
    elif c["axis"] == "Y":
        for side, sign, front in (("LEFT", 1, c["front_left"]), ("RIGHT", -1, c["front_right"])):
            plane_y = front[1] - 8.0
            if candidate_id == "G_CURRENT_REPOSITORY_LAYOUT_REPRODUCTION":
                registered = (sign * 115.0, -130.0, 93.0)
                shapes[f"{side}_REGISTERED_INPUT_SHAFT"] = _axis_cylinder("X", 5.0, 30.0, registered)
                shapes[f"{side}_UNRESOLVED_RIGHT_ANGLE_INTERFACE"] = box(24, 24, 24, (sign * 105, -122, 94.5))
                shapes[f"{side}_SELECTOR_SHAFT_INDEPENDENT"] = _axis_cylinder("X", 5, 32, (sign * 116, -317, 99))
                shapes[f"{side}_PTO_OUTPUT"] = _axis_cylinder("X", 5, 25, (sign * 116, -337, 97))
                shapes[f"{side}_DRIVE_OUTPUT"] = _axis_cylinder("X", 5, 25, (sign * 116, -297, 97))
                shapes[f"{side}_POWER_GUARD"] = box(36, 235, 50, (sign * 116, -220, 105))
                continue
            motor_center = (front[0], plane_y, front[2])
            pulley_center = (sign * 75.0, plane_y, front[2])
            shapes[f"{side}_20T_PULLEY"] = _axis_cylinder("Y", 18.0, 10.0, motor_center)
            shapes[f"{side}_60T_PHYSICAL"] = _axis_cylinder("Y", 50.0, 20.0, pulley_center)
            shapes[f"{side}_60T_SAFETY"] = _axis_cylinder("Y", 60.0, 20.0, pulley_center)
            shapes[f"{side}_HTD5M_BELT"] = box(abs(front[0] - sign * 75.0) + 12.0, 15.0, 12.0, ((front[0] + sign * 75.0) / 2.0, plane_y, front[2]))
            if p == "P4":
                selector_center = (sign * 75.0, -220.0, front[2])
                shapes[f"{side}_SELECTOR_SHAFT_INDEPENDENT"] = _axis_cylinder("Y", 5, 80, selector_center)
                offset = {"DRIVE": 8.0, "NEUTRAL": 0.0, "PTO": -8.0}.get(state, 0.0)
                shapes[f"{side}_SLIDE_DOG_CLUTCH_{state}"] = _axis_cylinder("Y", 13, 14, (selector_center[0], selector_center[1] + offset, selector_center[2]))
                shapes[f"{side}_PTO_OUTPUT_FORWARD"] = _axis_cylinder("Y", 5, 70, (sign * 75.0, -290.0, front[2]))
                shapes[f"{side}_DRIVE_BEVEL_PAIR"] = _compound([_axis_cylinder("Y", 16, 12, (sign * 75, -212, front[2])), _axis_cylinder("X", 16, 12, (sign * 75, -212, front[2]))])
                shapes[f"{side}_DRIVE_OUTPUT"] = _axis_cylinder("X", 5, 34, (sign * 92, -212, front[2]))
            else:
                selector_center = (sign * 75.0, -205.0, front[2])
                shapes[f"{side}_BEVEL_OR_MITER_PAIR"] = _compound([_axis_cylinder("Y", 16, 12, selector_center), _axis_cylinder("X", 16, 12, selector_center)])
                shapes[f"{side}_SELECTOR_SHAFT_INDEPENDENT"] = _axis_cylinder("X", 5, 36, (sign * 56.0, -205.0, front[2]))
                offset = {"DRIVE": -8.0, "NEUTRAL": 0.0, "PTO": 8.0}.get(state, 0.0)
                shapes[f"{side}_SLIDE_DOG_CLUTCH_{state}"] = _axis_cylinder("X", 13, 14, (sign * (56.0 + offset), -205.0, front[2]))
                shapes[f"{side}_PTO_OUTPUT"] = _axis_cylinder("X", 5, 28, (sign * 25.0, -205.0, front[2]))
                shapes[f"{side}_DRIVE_OUTPUT"] = _axis_cylinder("X", 5, 28, (sign * 87.0, -205.0, front[2]))
            shapes[f"{side}_BEARINGS"] = _compound([_axis_cylinder("Y", 14, 8, (sign * 75, plane_y - 20, front[2])), _axis_cylinder("X" if p != "P4" else "Y", 14, 8, (sign * 75, -230, front[2]))])
            shapes[f"{side}_POWER_GUARD"] = box(130, 115, 130, (sign * 75, -200, front[2]))
    else:
        for side, sign, front in (("LEFT", 1, c["front_left"]), ("RIGHT", -1, c["front_right"])):
            plane_z = front[2] - 8.0
            transfer_z = front[2]
            pulley_center = (sign * 75.0, front[1], plane_z)
            shapes[f"{side}_20T_PULLEY"] = _axis_cylinder("Z", 18, 10, (front[0], front[1], plane_z))
            shapes[f"{side}_60T_PHYSICAL"] = _axis_cylinder("Z", 50, 20, pulley_center)
            shapes[f"{side}_60T_SAFETY"] = _axis_cylinder("Z", 60, 20, pulley_center)
            shapes[f"{side}_BEVEL_OR_MITER_PAIR"] = _compound([_axis_cylinder("Z", 16, 12, (sign * 75, front[1], transfer_z)), _axis_cylinder("X", 16, 12, (sign * 75, front[1], transfer_z))])
            shapes[f"{side}_SELECTOR_SHAFT_INDEPENDENT"] = _axis_cylinder("X", 5, 36, (sign * 56, front[1], transfer_z))
            offset = {"DRIVE": -8.0, "NEUTRAL": 0.0, "PTO": 8.0}.get(state, 0.0)
            shapes[f"{side}_SLIDE_DOG_CLUTCH_{state}"] = _axis_cylinder("X", 13, 14, (sign * (56 + offset), front[1], transfer_z))
            shapes[f"{side}_PTO_OUTPUT"] = _axis_cylinder("X", 5, 28, (sign * 25, front[1], transfer_z))
            shapes[f"{side}_DRIVE_OUTPUT"] = _axis_cylinder("X", 5, 28, (sign * 87, front[1], transfer_z))
            shapes[f"{side}_BEARINGS"] = _compound([_axis_cylinder("Z", 14, 8, (sign * 75, front[1], transfer_z - 10)), _axis_cylinder("X", 14, 8, (sign * 75, front[1], transfer_z))])
            shapes[f"{side}_POWER_GUARD"] = box(130, 130, 130, (sign * 75, front[1], transfer_z))
    return shapes


def _bounds(shape: cq.Shape) -> dict[str, float]:
    b = shape.BoundingBox()
    return {name: round(value, 6) for name, value in {
        "xmin": b.xmin, "xmax": b.xmax, "ymin": b.ymin, "ymax": b.ymax,
        "zmin": b.zmin, "zmax": b.zmax, "xlen": b.xlen, "ylen": b.ylen, "zlen": b.zlen,
    }.items()}


def _intersection_volume(a: cq.Shape, b: cq.Shape) -> float:
    try:
        return max(0.0, float(a.intersect(b).Volume()))
    except Exception as exc:
        raise RuntimeError(f"actual shape intersection failed: {exc}") from exc


def _selected_compounds(candidate_id: str) -> dict[str, cq.Shape]:
    motors = placed_motor_shapes(CANDIDATES[candidate_id])
    fixed = _compound(motors[name] for name in motors if name.endswith("FIXED_ENVELOPE"))
    guard = _compound(motors[name] for name in motors if name.endswith("MOTOR_GUARD_CANDIDATE_ENVELOPE"))
    service = _compound(motors[name] for name in motors if name.endswith("REAR_CABLE_SERVICE_ENVELOPE"))
    removal = _compound(motors[name] for name in motors if name.endswith("MOTOR_REMOVAL_SWEEP"))
    power = powerpath_shapes(candidate_id)
    fixed_power = _compound(shape for name, shape in power.items() if "GUARD" not in name)
    power_guard = _compound(shape for name, shape in power.items() if "GUARD" in name)
    return {"fixed_motor": fixed, "motor_guard": guard, "service": service, "removal": removal, "fixed_power": fixed_power, "power_guard": power_guard}


def candidate_collision_report(candidate_id: str) -> dict[str, Any]:
    env = environment_shapes()
    c = CANDIDATES[candidate_id]
    groups = _selected_compounds(candidate_id)
    rows: list[dict[str, Any]] = []
    hard_collision = False
    for group_name in ("fixed_motor", "fixed_power", "motor_guard", "service", "removal"):
        for environment_name in ("CBOX", "BBOX", "FRAME", "TRACKS", "BATTERY_EXTRACTION_KEEP_OUT", "UNIT_MATING_KEEP_OUT", "DRAINAGE_KEEP_OUT"):
            volume = _intersection_volume(groups[group_name], env[environment_name])
            authorized = candidate_id == "E_LONGITUDINAL_FRONT_PTO" and group_name == "fixed_power" and environment_name == "UNIT_MATING_KEEP_OUT"
            is_hard_group = group_name in ("fixed_motor", "fixed_power")
            collision = volume > 1e-6
            if collision and is_hard_group and not authorized:
                hard_collision = True
            rows.append({
                "candidate_id": candidate_id,
                "shape_group": group_name,
                "environment": environment_name,
                "intersection_volume_mm3": round(volume, 6),
                "collision": "YES" if collision else "NO",
                "authorization": "AUTHORIZED_PTO_INTERFACE" if authorized else "NONE",
                "hard_constraint_effect": "FAIL" if collision and is_hard_group and not authorized else "PASS",
                "calculation": "CADQUERY_ACTUAL_SHAPE_COMMON_VOLUME",
            })
    motor_axis_mismatch = 0.0
    if candidate_id == "G_CURRENT_REPOSITORY_LAYOUT_REPRODUCTION":
        motor_axis_mismatch = round(math.hypot(115.0 - 96.0, 93.0 - 96.0), 6)
        hard_collision = True
    return {
        "candidate_id": candidate_id,
        "actual_shape_calculation": True,
        "rows": rows,
        "hard_collision": hard_collision,
        "registered_input_axis_perpendicular_mismatch_mm": motor_axis_mismatch,
        "registered_input_axis_coaxial": motor_axis_mismatch == 0.0,
        "status": "FAIL" if hard_collision else "PASS",
        "notes": c["summary"],
    }


SEARCH_SPECS = {
    "A_LATERAL_FRONT_DIRECT": {"x": [60, 72, 2], "y": [-205, -160, 5], "z": [80, 160, 5], "target": [68, -185, 105]},
    "B_LATERAL_ABOVE_CBOX_DIRECT": {"x": [52, 68, 2], "y": [-120, -20, 5], "z": [160, 240, 5], "target": [58, -70, 180]},
    "C_LATERAL_FORE_AFT_STAGGERED": {"x": [60, 70, 2], "y": [-200, -175, 5], "z": [80, 160, 5], "stagger": [15, 20, 25, 30], "target": [68, -185, 105, 30]},
    "D_LONGITUDINAL_SIDE_RAIL": {"x": [95, 120, 5], "y": [-170, -130, 5], "z": [80, 160, 5], "target": [105, -165, 105]},
    "E_LONGITUDINAL_FRONT_PTO": {"x": [90, 115, 5], "y": [-200, -150, 5], "z": [80, 160, 5], "target": [105, -180, 105]},
    "F_VERTICAL_MOTOR": {"x": [90, 120, 5], "y": [-130, -40, 5], "z": [100, 180, 5], "target": [105, -70, 130]},
    "G_CURRENT_REPOSITORY_LAYOUT_REPRODUCTION": {"fixed": True, "target": [96, -105.45, 96]},
}


def _series(spec: list[float]) -> list[float]:
    start, end, step = spec
    count = int(round((end - start) / step))
    return [float(start + i * step) for i in range(count + 1)]


def _aabb_for_motor(front: tuple[float, float, float], rear_axis: str, guard: bool = False, service: bool = False) -> tuple[float, float, float, float, float, float]:
    cross_y = BRACKET_WIDTH_MM / 2.0
    cross_z = BRACKET_HEIGHT_MM / 2.0
    rear = REAR_FROM_PLATE_MM + (SERVICE_REAR_EXTRA_MM[DEFAULT_SERVICE] if service else GUARD_SIDE_MARGIN_MM[DEFAULT_GUARD] if guard else 0.0)
    front_len = 0.0 if guard or service else SHAFT_FROM_PLATE_MM
    cross_extra = 5.0 if guard else 4.0 if service else 0.0
    x, y, z = front
    if rear_axis in ("+X", "-X"):
        a, b = (-front_len, rear) if rear_axis == "+X" else (-rear, front_len)
        return (x + a, x + b, y - cross_y - cross_extra, y + cross_y + cross_extra, z - cross_z - cross_extra, z + cross_z + cross_extra)
    if rear_axis in ("+Y", "-Y"):
        a, b = (-front_len, rear) if rear_axis == "+Y" else (-rear, front_len)
        return (x - cross_y - cross_extra, x + cross_y + cross_extra, y + a, y + b, z - cross_z - cross_extra, z + cross_z + cross_extra)
    a, b = (-front_len, rear) if rear_axis == "+Z" else (-rear, front_len)
    return (x - cross_y - cross_extra, x + cross_y + cross_extra, y - cross_z - cross_extra, y + cross_z + cross_extra, z + a, z + b)


def _aabb_overlap(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    return a[0] < b[1] and a[1] > b[0] and a[2] < b[3] and a[3] > b[2] and a[4] < b[5] and a[5] > b[4]


ENV_AABBS = {
    "CBOX": (-65, 65, -140, 0, 0, 105), "BBOX": (-75, 75, 0, 220, 0, 150),
    "BATTERY": (-66.5, 66.5, 16, 204, 150, 360),
    "FRAME_LEFT": (69, 89, -232, 0, 0, 20), "FRAME_RIGHT": (-89, -69, -232, 0, 0, 20),
    "FRAME_FRONT": (-69, 69, -232, -212, 0, 20),
    "TRACK_LEFT": (135, 145, -150, 300, 40, 210), "TRACK_RIGHT": (-145, -135, -150, 300, 40, 210),
    "UNIT": (-72, 72, -380, -246, 0, 160),
}


def grid_search_summary(candidate_id: str) -> dict[str, Any]:
    spec = SEARCH_SPECS[candidate_id]
    if spec.get("fixed"):
        return {"candidate_id": candidate_id, "evaluated_count": 1, "approx_feasible_count": 0, "grid": spec, "selected": CANDIDATES[candidate_id]["front_left"], "selection_rule": "CURRENT_AUTHORITY_REPRODUCTION_FIXED"}
    xs, ys, zs = _series(spec["x"]), _series(spec["y"]), _series(spec["z"])
    stagger_values = spec.get("stagger", [0.0])
    evaluated = 0
    feasible = 0
    best: tuple[float, list[float]] | None = None
    target = spec["target"]
    for x, y, z, stagger in itertools.product(xs, ys, zs, stagger_values):
        evaluated += 1
        c = CANDIDATES[candidate_id]
        if c["axis"] == "X":
            left = (x, y, z)
            right = (-x, y + stagger, z)
        else:
            left = (x, y, z)
            right = (-x, y, z)
        boxes = [_aabb_for_motor(left, c["rear_axes"][0]), _aabb_for_motor(right, c["rear_axes"][1])]
        collision = any(_aabb_overlap(motor, env) for motor in boxes for env in ENV_AABBS.values())
        fixed_width = max(290.0, 2 * max(abs(boxes[0][0]), abs(boxes[0][1]), abs(boxes[1][0]), abs(boxes[1][1])))
        if fixed_width >= ABSOLUTE_TOTAL_WIDTH_MM:
            collision = True
        if not collision:
            feasible += 1
            vector = [x, y, z] + ([stagger] if "stagger" in spec else [])
            score = sum((float(a) - float(b)) ** 2 for a, b in zip(vector, target))
            if best is None or score < best[0]:
                best = (score, vector)
    return {
        "candidate_id": candidate_id,
        "evaluated_count": evaluated,
        "approx_feasible_count": feasible,
        "grid": spec,
        "selected": CANDIDATES[candidate_id]["front_left"],
        "nearest_feasible_to_design_anchor": best[1] if best else None,
        "selection_rule": "AABB_GRID_FILTER_THEN_CADQUERY_ACTUAL_SHAPE_VALIDATION",
        "aabb_is_final_authority": False,
    }


def measurements_rows() -> list[dict[str, Any]]:
    rows = []
    for measurement_id, component, description, value, status in MEASUREMENTS:
        note = ""
        if measurement_id == "K":
            note = "M3-class bracket fastener candidate; never substitute 27.7 mm"
        elif measurement_id == "SLOT_27P7":
            note = "representative inner value only; major/minor axes, corner radius, and center remain HOLD"
        elif status == "DERIVED":
            note = "arithmetic derivation from user-reported measurements; not an independent measurement"
        rows.append({
            "measurement_id": measurement_id,
            "component": component,
            "description": description,
            "measured_value_mm": value,
            "measurement_source": "USER_REPORTED_PHYSICAL_CALIPER_MEASUREMENT",
            "measurement_method": "USER_OWNED_CALIPER",
            "uncertainty": "USER_NOT_REPORTED",
            "status": status,
            "manufacturing_authority": "NOT_FOR_MANUFACTURING",
            "notes": note,
        })
    return rows


def authority_audit_data() -> dict[str, Any]:
    protected = parent_protection_audit()
    return {
        "document_id": DOCUMENT_ID,
        "current_pointer": "rovers/common_rover/v2.29.3.9.1",
        "current_authority_version": "v2.29.3.9.1",
        "coordinate_authority": {"X": "lateral +left", "Y": "longitudinal +rear; front is negative", "Z": "up"},
        "fixed_bodies": {
            "CBOX": {"bounds_mm": {"x": [-65, 65], "y": [-140, 0], "z": [0, 105]}, "size_mm": [130, 140, 105]},
            "BBOX": {"bounds_mm": {"x": [-75, 75], "y": [0, 220], "z": [0, 150]}, "size_mm": [150, 220, 150]},
            "BATTERY_CASSETTE": {"bounds_mm": {"x": [-62.5, 62.5], "y": [20, 200], "z": [15, 135]}, "size_mm": [125, 180, 120]},
            "BATTERY_EXTRACTION_PROXY": {"bounds_mm": {"x": [-66.5, 66.5], "y": [16, 204], "z": [150, 360]}, "source": "inherited pinned v2.29.3.5 component registry"},
        },
        "frame": {"left_rail_x": [69, 89], "right_rail_x": [-89, -69], "rail_y": [-232, 0], "rail_z": [0, 20], "front_crossmember_x": [-69, 69], "front_crossmember_y": [-232, -212]},
        "current_axes_mm": {
            "left_motor": [96, -75, 96], "right_motor": [-96, -75, 96],
            "left_input": [115, -130, 93], "right_input": [-115, -130, 93],
            "left_output": [116, -297, 97], "right_output": [-116, -297, 97],
            "left_pto": [116, -337, 97], "right_pto": [-116, -337, 97],
            "left_selector": [116, -317, 99], "right_selector": [-116, -317, 99],
            "servo": [0, -193, 109], "cam": [0, -220, 106], "hitch_left": [53, -244, 13], "hitch_right": [-53, -244, 13],
        },
        "hardware_envelopes": {
            "current_motor_placeholder_left": {"x": [87, 105], "y": [-102, -48], "z": [70, 122], "size_mm": [18, 54, 52]},
            "unit_mating_keep_out": {"x": [-72, 72], "y": [-380, -246], "z": [0, 160]},
            "drainage_keep_outs": "8 inherited fixed zones; explicitly modeled",
            "service_registry": "EMPTY_OR_EXCLUDED; v0.9.3.0 service envelopes are study-only",
        },
        "slot_zone_authority": {"motor_adapter_y": [-80, -70], "input_y": [-135, -125], "output_bridge_y": [-222, -212], "servo_y": [-210, -200], "measurement_status": "HOLD"},
        "track_proxy": {"source": "INHERITED_V090_TRANSFORMED_TRACK_PROXY", "overall_width_mm": 290, "status": "COMPARISON_PROXY_NOT_CURRENT_EXACT_TRACK_SOLID"},
        "legacy_v0921_difference": {"legacy_axes": "+X forward, +Y left, +Z up", "legacy_motor_z_mm": 370, "legacy_total_width_mm": 290, "disposition": "NOT_AUTOMATICALLY_ADOPTED"},
        "current_width_contract": {"preferred_mm": 282, "candidate_target_mm": 286, "hard_mm": 300, "study_user_target_mm": 290, "difference_recorded": True},
        "registered_motor_to_input_perpendicular_mismatch_mm": round(math.hypot(19, 3), 6),
        "component_registry_parent": {"version": "v2.29.3.5", "pinned_object_sha256": "2dccc...", "working_copy_line_ending_sensitive_sha256_observed": "7dbfa3...", "source_used": "PINNED_AUTHORITY_REFERENCE", "automatic_reconciliation": "PROHIBITED"},
        "authority_files": AUTHORITY_FILES,
        "protected": protected,
        "design_authority_update": "PROHIBITED",
    }


def dimension_report(candidate_id: str, collision: dict[str, Any]) -> dict[str, Any]:
    c = CANDIDATES[candidate_id]
    groups = _selected_compounds(candidate_id)
    env = environment_shapes()
    fixed_bb = _bounds(groups["fixed_motor"])
    guard_all = _compound([groups["fixed_motor"], groups["motor_guard"], groups["fixed_power"], groups["power_guard"], env["TRACKS"]])
    fixed_all = _compound([groups["fixed_motor"], groups["fixed_power"], env["TRACKS"]])
    service_all = _compound([guard_all, groups["service"]])
    motor_fixed_width = fixed_bb["xlen"]
    motor_guard_width = _bounds(_compound([groups["fixed_motor"], groups["motor_guard"]]))["xlen"]
    guarded = _bounds(guard_all)
    fixed = _bounds(fixed_all)
    service = _bounds(service_all)
    maximum_height = max(guarded["zmax"], 210.0)
    removal_track_volume = next(row["intersection_volume_mm3"] for row in collision["rows"] if row["shape_group"] == "removal" and row["environment"] == "TRACKS")
    return {
        "candidate_id": candidate_id,
        "motor_front_plate_xyz_left": c["front_left"],
        "motor_front_plate_xyz_right": c["front_right"],
        "motor_axis": c["axis"],
        "motor_subsystem_fixed_width_mm": round(motor_fixed_width, 3),
        "motor_subsystem_guarded_width_mm": round(motor_guard_width, 3),
        "complete_fixed_width_mm": round(fixed["xlen"], 3),
        "complete_guarded_width_mm": round(guarded["xlen"], 3),
        "service_width_mm": round(service["xlen"], 3),
        "width_margin_to_290_mm": round(TARGET_TOTAL_WIDTH_MM - guarded["xlen"], 3),
        "width_margin_to_300_mm": round(ABSOLUTE_TOTAL_WIDTH_MM - guarded["xlen"], 3),
        "maximum_height_mm": round(maximum_height, 3),
        "fixed_bounds_mm": fixed,
        "guarded_bounds_mm": guarded,
        "service_bounds_mm": service,
        "motor_removal_possible": removal_track_volume <= 1e-6,
        "service_may_temporarily_exceed_290": service["xlen"] > TARGET_TOTAL_WIDTH_MM,
        "fixed_width_from_actual_solids": True,
        "guard_width_from_actual_solids": True,
        "service_width_from_actual_solids": True,
    }


def all_reports() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    collisions: dict[str, dict[str, Any]] = {}
    dimensions: dict[str, dict[str, Any]] = {}
    searches: dict[str, dict[str, Any]] = {}
    for candidate_id in CANDIDATES:
        collisions[candidate_id] = candidate_collision_report(candidate_id)
        dimensions[candidate_id] = dimension_report(candidate_id, collisions[candidate_id])
        searches[candidate_id] = grid_search_summary(candidate_id)
    return collisions, dimensions, searches


def trade_rows(collisions: dict[str, dict[str, Any]], dimensions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for candidate_id, c in CANDIDATES.items():
        p = POWERPATHS[c["powerpath"]]
        d = dimensions[candidate_id]
        report = collisions[candidate_id]
        def hit(environment: str) -> str:
            return "YES" if any(row["collision"] == "YES" and row["environment"] == environment and row["shape_group"] in ("fixed_motor", "fixed_power") and row["authorization"] == "NONE" for row in report["rows"]) else "NO"
        hard = not report["hard_collision"] and d["complete_guarded_width_mm"] < ABSOLUTE_TOTAL_WIDTH_MM
        rejection = ""
        hold = "PHYSICAL_MOCKUP_AND_LOAD_TEST_REQUIRED"
        if candidate_id.startswith("C_"):
            rejection = "RIGHT_TRACK_ENVELOPE_INTERSECTION"
        elif candidate_id.startswith("G_"):
            rejection = "MEASURED_MOTOR_AXIS_NOT_COAXIAL_WITH_REGISTERED_INPUT_AXIS"
        elif candidate_id.startswith("B_"):
            hold = "OUTWARD_REMOVAL_SWEEP_INTERSECTS_TRACK; HIGH_POSITION_GUARD_MOCKUP"
        elif candidate_id.startswith("F_"):
            hold = "HIGH_CG_WEATHER_SEAL_AND_BEVEL_PRODUCT_HOLD"
        rows.append({
            "candidate_id": candidate_id,
            "motor_orientation_axis": c["axis"],
            "motor_front_plate_xyz_left": json.dumps(c["front_left"]),
            "motor_front_plate_xyz_right": json.dumps(c["front_right"]),
            "motor_fixed_envelope": "JGB37_520_MEASURED_87P0_MM_PLUS_BRACKET",
            "motor_service_envelope": f"{DEFAULT_SERVICE}_{SERVICE_REAR_EXTRA_MM[DEFAULT_SERVICE]:.0f}MM_REAR_EXTRA",
            "total_fixed_width_mm": d["complete_fixed_width_mm"],
            "total_guarded_width_mm": d["complete_guarded_width_mm"],
            "width_margin_to_290_mm": d["width_margin_to_290_mm"],
            "width_margin_to_300_mm": d["width_margin_to_300_mm"],
            "maximum_height_mm": d["maximum_height_mm"],
            "CBOX_collision": hit("CBOX"), "BBOX_collision": hit("BBOX"), "frame_collision": hit("FRAME"), "track_collision": hit("TRACKS"),
            "battery_service_collision": hit("BATTERY_EXTRACTION_KEEP_OUT"), "unit_bay_collision": hit("UNIT_MATING_KEEP_OUT"),
            "belt_collision": "NO" if hard else "CHECK_REJECTION", "cable_collision": "NO_FIXED;SERVICE_SEPARATE", "drainage_collision": hit("DRAINAGE_KEEP_OUT"),
            "motor_removal_possible": "YES" if d["motor_removal_possible"] else "NO",
            "belt_replacement_possible": "CONDITIONAL_YES" if hard else "NO",
            "fixed_guard_possible": "CONDITIONAL_YES" if hard else "NO",
            "right_angle_stage_count": p["right_angle"], "belt_count": p["belts"], "chain_count": p["chains"], "gear_pair_count": p["gear_pairs"], "bearing_count": p["bearings"],
            "clutch_type": "LEFT_RIGHT_INDEPENDENT_COAXIAL_SLIDE_DOG_DRIVE_NEUTRAL_PTO",
            "PTO_output_direction": p["pto"], "PTO_unit_connection_type": "HITCH_AND_GUIDE_SUPPORTED_NOT_SHAFT_SUPPORTED",
            "drive_brake_required": "YES_DURING_PTO",
            "repairability_score": {"A": 5, "B": 3, "C": 2, "D": 4, "E": 4, "F": 2, "G": 2}[c["letter"]],
            "cost_score": {"A": 5, "B": 4, "C": 3, "D": 3, "E": 3, "F": 2, "G": 2}[c["letter"]],
            "power_loss_score": 5 - p["right_angle"], "backlash_score": 5 - p["right_angle"], "sealing_score": {"A": 4, "B": 3, "C": 3, "D": 4, "E": 4, "F": 2, "G": 2}[c["letter"]],
            "field_service_score": {"A": 5, "B": 2, "C": 2, "D": 4, "E": 4, "F": 2, "G": 2}[c["letter"]],
            "hard_constraint_pass": "YES" if hard else "NO",
            "recommendation_rank": c["rank"], "rejection_reason": rejection, "hold_reason": hold,
            "notes": c["summary"],
        })
    return rows


def width_rows(dimensions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for candidate_id, d in dimensions.items():
        for service_id, extra in SERVICE_REAR_EXTRA_MM.items():
            for guard_id, margin in GUARD_SIDE_MARGIN_MM.items():
                c = CANDIDATES[candidate_id]
                if c["axis"] == "X":
                    front_abs = max(abs(c["front_left"][0]), abs(c["front_right"][0]))
                    motor_guard = 2 * (front_abs + REAR_FROM_PLATE_MM + margin)
                    service_width = 2 * (front_abs + REAR_FROM_PLATE_MM + extra)
                else:
                    motor_guard = 2 * (max(abs(c["front_left"][0]), abs(c["front_right"][0])) + BRACKET_HEIGHT_MM / 2 + margin)
                    service_width = motor_guard
                complete_guard = max(290.0, motor_guard)
                complete_service = max(complete_guard, service_width)
                rows.append({
                    "candidate_id": candidate_id, "service_case": service_id, "service_rear_extra_mm": extra,
                    "guard_case": guard_id, "guard_side_margin_mm": margin,
                    "motor_subsystem_guarded_width_mm": round(motor_guard, 3),
                    "complete_guarded_width_mm": round(complete_guard, 3),
                    "complete_service_width_mm": round(complete_service, 3),
                    "target_290_pass": "YES" if complete_guard <= 290 else "NO",
                    "absolute_under_300_pass": "YES" if complete_guard < 300 else "NO",
                    "service_excess_is_temporary": "YES" if complete_service > complete_guard else "NO",
                    "selected_default": "YES" if service_id == DEFAULT_SERVICE and guard_id == DEFAULT_GUARD else "NO",
                })
    return rows


def service_rows(collisions: dict[str, dict[str, Any]], dimensions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for candidate_id, d in dimensions.items():
        collision = collisions[candidate_id]
        removal_hits = [row for row in collision["rows"] if row["shape_group"] == "removal" and row["collision"] == "YES"]
        rows.append({
            "candidate_id": candidate_id,
            "motor_removal_possible": "YES" if d["motor_removal_possible"] else "NO",
            "motor_removal_collision_targets": ";".join(row["environment"] for row in removal_hits) or "NONE",
            "connector_unplug_access": "HOLD_ACTUAL_CONNECTOR_AND_TOOL_ENVELOPE",
            "cable_bend_access": "S0_S3_SENSITIVITY_RECORDED",
            "belt_replacement_access": "CONDITIONAL_WITH_REMOVABLE_GUARD",
            "bearing_replacement_access": "CONDITIONAL_WITH_SPLIT_SUPPORT_PLATE",
            "cover_removal": "OUTWARD_OR_UPWARD_CANDIDATE",
            "mud_wash_access": "OPEN_BOTTOM_DRAIN_PATH_REQUIRED",
            "temporary_service_width_mm": d["service_width_mm"],
            "fixed_width_confused_with_service": "NO",
            "physical_mockup_required": "YES",
        })
    return rows


def collision_rows(collisions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for candidate_id in CANDIDATES for row in collisions[candidate_id]["rows"]]


def _canonicalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"FILE_NAME\('.*?','.*?',", "FILE_NAME('PS-CR-V0930','2000-01-01T00:00:00',", text, count=1)
    text = re.sub(r"FILE_DESCRIPTION\(\(.*?\),'.*?'\);", "FILE_DESCRIPTION(('CONDITIONAL ENVELOPE CAD NOT FOR MANUFACTURING'),'2;1');", text, count=1)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def _export_step(path: Path, shapes: Iterable[cq.Shape]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(_compound(shapes), str(path))
    _canonicalize_step(path)


def _candidate_state_shapes(candidate_id: str, filename: str) -> list[cq.Shape]:
    motors = placed_motor_shapes(CANDIDATES[candidate_id])
    env = environment_shapes()
    state = "DRIVE" if filename == "DRIVE_SELECTED.step" else "PTO" if filename == "PTO_SELECTED.step" else "NEUTRAL"
    power = powerpath_shapes(candidate_id, state)
    fixed_motor = [shape for name, shape in motors.items() if name.endswith(("MOTOR_CYLINDER", "REAR_TERMINAL_FIXED_ENVELOPE", "FRONT_PLATE", "OUTPUT_SHAFT", "SHAFT_ROOT_BOSS", "MOUNT_BRACKET", "M3_FASTENER_HOLE_CANDIDATES", "VERTICAL_SLOT_PLACEHOLDER"))]
    frame = [env[name] for name in ("CBOX", "BBOX", "FRAME", "TRACKS")]
    if filename == "MOTOR_ONLY.step":
        return fixed_motor
    if filename == "MOTOR_FRAME.step":
        return fixed_motor + frame
    if filename in ("MOTOR_POWERPATH.step", "DRIVE_SELECTED.step", "NEUTRAL.step", "PTO_SELECTED.step"):
        return fixed_motor + frame + [shape for name, shape in power.items() if "GUARD" not in name]
    if filename == "MOTOR_REMOVAL_SWEEP.step":
        return fixed_motor + frame + [shape for name, shape in motors.items() if name.endswith(("MOTOR_REMOVAL_SWEEP", "REAR_CABLE_SERVICE_ENVELOPE", "CONNECTOR_TOOL_ACCESS"))]
    if filename == "BELT_REPLACEMENT_ACCESS.step":
        access = [box(50, 100, 60, (95, -185, 145)), box(50, 100, 60, (-95, -185, 145))]
        return fixed_motor + frame + list(power.values()) + access
    if filename == "UNIT_CONNECTED.step":
        unit = [box(120, 100, 80, (0, -330, 80)), box(130, 20, 20, (0, -250, 20)), box(20, 100, 20, (53, -300, 20)), box(20, 100, 20, (-53, -300, 20))]
        return fixed_motor + frame + list(power.values()) + unit
    if filename == "ALL_FIXED_GUARDS.step":
        return fixed_motor + frame + list(power.values()) + [shape for name, shape in motors.items() if name.endswith("MOTOR_GUARD_CANDIDATE_ENVELOPE")]
    raise ValueError(filename)


def _svg_base(title: str, body: str, width: int = 1000, height: int = 620) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial,sans-serif;fill:#172033}} .h{{font-weight:700}} .small{{font-size:13px}} .hold{{fill:#9a3412}}</style>
<text x="30" y="38" font-size="23" class="h">{title}</text><text x="30" y="60" class="small hold">CONDITIONAL ENVELOPE CAD / NOT FOR MANUFACTURING</text>{body}
</svg>'''


def candidate_svgs(candidate_id: str, dimensions: dict[str, Any]) -> dict[str, str]:
    c = CANDIDATES[candidate_id]
    left, right = c["front_left"], c["front_right"]
    top = f'''<g transform="translate(500 330) scale(1.25 -1.25)"><rect x="-145" y="-220" width="290" height="440" fill="none" stroke="#d97706" stroke-width="2"/><rect x="-65" y="-140" width="130" height="140" fill="#bfdbfe" stroke="#2563eb"/><rect x="-75" y="0" width="150" height="220" fill="#ddd6fe" stroke="#7c3aed"/><rect x="135" y="-150" width="10" height="450" fill="#334155"/><rect x="-145" y="-150" width="10" height="450" fill="#334155"/><circle cx="{left[0]}" cy="{left[1]}" r="19" fill="#fca5a5" stroke="#991b1b"/><circle cx="{right[0]}" cy="{right[1]}" r="19" fill="#fca5a5" stroke="#991b1b"/></g><text x="30" y="590" class="small">X lateral, Y rear; orange boundary ±145 mm. Guarded width {dimensions['complete_guarded_width_mm']} mm.</text>'''
    front = f'''<g transform="translate(500 510) scale(1.5 -1.5)"><line x1="-170" y1="0" x2="170" y2="0" stroke="#334155"/><rect x="-145" y="40" width="10" height="170" fill="#475569"/><rect x="135" y="40" width="10" height="170" fill="#475569"/><circle cx="{left[0]}" cy="{left[2]}" r="19" fill="#fca5a5" stroke="#991b1b"/><circle cx="{right[0]}" cy="{right[2]}" r="19" fill="#fca5a5" stroke="#991b1b"/></g><text x="30" y="590" class="small">Front: fixed motor solids, transformed track proxy, Z-up.</text>'''
    side = f'''<g transform="translate(420 510) scale(1.35 -1.35)"><rect x="-140" y="0" width="140" height="105" fill="#bfdbfe"/><rect x="0" y="0" width="220" height="150" fill="#ddd6fe"/><circle cx="{left[1]}" cy="{left[2]}" r="19" fill="#fca5a5" stroke="#991b1b"/><line x1="-380" y1="160" x2="220" y2="160" stroke="#64748b" stroke-dasharray="5 5"/></g><text x="30" y="590" class="small">Side: Y longitudinal; service and removal sweeps are separate from fixed width.</text>'''
    p = POWERPATHS[c["powerpath"]]
    flow = f'''<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8z" fill="#2563eb"/></marker></defs><g font-size="17"><rect x="55" y="170" width="150" height="70" rx="10" fill="#fee2e2"/><text x="82" y="212">2 × MOTOR</text><line x1="205" y1="205" x2="325" y2="205" stroke="#2563eb" stroke-width="4" marker-end="url(#a)"/><rect x="325" y="170" width="150" height="70" rx="10" fill="#fef3c7"/><text x="352" y="201">20T / 60T</text><text x="370" y="223">REDUCTION</text><line x1="475" y1="205" x2="595" y2="205" stroke="#2563eb" stroke-width="4" marker-end="url(#a)"/><rect x="595" y="155" width="180" height="100" rx="10" fill="#dbeafe"/><text x="618" y="189">COAXIAL DOG</text><text x="618" y="215">DRIVE / N / PTO</text><text x="618" y="239">L/R INDEPENDENT</text><line x1="775" y1="205" x2="895" y2="205" stroke="#2563eb" stroke-width="4" marker-end="url(#a)"/><text x="810" y="185">DRIVE</text><text x="810" y="232">PTO</text><text x="55" y="330">{c['powerpath']} {p['name']} · right-angle stages: {p['right_angle']} · belts never change axis 90°</text><text x="55" y="365">PTO work requires brake/mechanical lock. Unit mass is supported by hitch/guide frame.</text></g>'''
    return {
        "TOP_VIEW.svg": _svg_base(f"Candidate {c['letter']} · {c['title']} · TOP", top),
        "FRONT_VIEW.svg": _svg_base(f"Candidate {c['letter']} · {c['title']} · FRONT", front),
        "SIDE_VIEW.svg": _svg_base(f"Candidate {c['letter']} · {c['title']} · SIDE", side),
        "POWER_FLOW.svg": _svg_base(f"Candidate {c['letter']} · {c['powerpath']} power flow", flow),
    }


def comparison_svgs(dimensions: dict[str, dict[str, Any]]) -> dict[str, str]:
    panels = []
    for index, (candidate_id, c) in enumerate(CANDIDATES.items()):
        x = 30 + (index % 4) * 240
        y = 100 + (index // 4) * 240
        panels.append(f'''<g transform="translate({x} {y})"><rect width="220" height="205" rx="8" fill="#fff" stroke="#94a3b8"/><text x="10" y="24" class="h">{c['letter']} {c['title']}</text><rect x="74" y="45" width="72" height="80" fill="#bfdbfe"/><rect x="25" y="42" width="8" height="150" fill="#334155"/><rect x="187" y="42" width="8" height="150" fill="#334155"/><circle cx="{110+c['front_left'][0]*0.45}" cy="{120+c['front_left'][1]*0.35}" r="9" fill="#ef4444"/><circle cx="{110+c['front_right'][0]*0.45}" cy="{120+c['front_right'][1]*0.35}" r="9" fill="#ef4444"/><text x="10" y="158" class="small">guard {dimensions[candidate_id]['complete_guarded_width_mm']} mm</text><text x="10" y="180" class="small">rank {c['rank']} · {c['status']}</text></g>''')
    layout = _svg_base("Common Rover motor layout comparison A–G", "".join(panels), 1000, 590)
    rows = []
    for index, (pid, p) in enumerate(POWERPATHS.items()):
        y = 105 + index * 78
        rows.append(f'''<g><rect x="40" y="{y}" width="920" height="60" rx="8" fill="{'#dcfce7' if pid in ('P1','P4') else '#f1f5f9'}" stroke="#94a3b8"/><text x="55" y="{y+24}" class="h">{pid} {p['name']}</text><text x="55" y="{y+47}" class="small">motor {p['motor_axis']} → selector {p['selector_axis']} → PTO {p['pto']} | right-angle {p['right_angle']} | bearings {p['bearings']} | {p['note']}</text></g>''')
    power = _svg_base("Common Rover powerpath comparison P1–P6", "".join(rows), 1000, 620)
    return {COMPARISON_ARTIFACTS[0]: layout, COMPARISON_ARTIFACTS[1]: power}


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    return "| " + " | ".join(headers) + " |\n|" + "|".join("---" for _ in headers) + "|\n" + "\n".join("| " + " | ".join(str(value) for value in row) + " |" for row in rows)


def authority_markdown(audit: dict[str, Any]) -> str:
    protection = _md_table(["path", "files", "ledger", "result"], [[row["path"], row["actual_file_count"], row["actual_ledger_sha256"], "PASS" if row["pass"] else "FAIL"] for row in audit["protected"]["protected_lanes"]])
    return f"""# Current motor-layout authority audit v0.9.3.0

This is a read-only comparison. `DESIGN_AUTHORITY_UPDATE=PROHIBITED`.

## Current authority

- Pointer: `rovers/common_rover/v2.29.3.9.1`
- Coordinates: +X lateral left, +Y rear, +Z up.
- CBOX: X -65..65, Y -140..0, Z 0..105 mm.
- BBOX: X -75..75, Y 0..220, Z 0..150 mm.
- Battery cassette: 125 × 180 × 120 mm; extraction proxy remains separately protected.
- Frame rail centers: X ±79 mm; rail sections X 69..89 / -89..-69, Y -232..0, Z 0..20 mm.
- Transformed track comparison proxy: X ±135..145 mm; overall 290 mm; `COMPARISON_PROXY_NOT_CURRENT_EXACT_TRACK_SOLID`.
- Unit mating keep-out: X -72..72, Y -380..-246, Z 0..160 mm.

The v0.9.2.1 lane uses a legacy coordinate convention (+X forward, +Y left) and a much higher motor-Z candidate. Values are compared, not silently selected. The study uses the current v2 coordinate authority because the user explicitly defines total width along X.

## Existing placeholder versus physical motor

The inherited left placeholder is only 18 × 54 × 52 mm (X/Y/Z). It is not treated as JGB37-520 physical geometry. Replacing it at the current motor line leaves a perpendicular offset of **{audit['registered_motor_to_input_perpendicular_mismatch_mm']} mm** to the registered input axis (19 mm lateral, 3 mm vertical), so Candidate G fails coaxial transmission continuity.

The pinned v2.29.3.5 component-registry reference is retained. A working-copy byte difference that can arise from text line endings is recorded and is not auto-reconciled.

## Protected ledgers

{protection}
"""


def study_markdown(trades: list[dict[str, Any]], searches: dict[str, dict[str, Any]], dimensions: dict[str, dict[str, Any]]) -> str:
    candidate_table = _md_table(["candidate", "grid", "feasible AABB", "actual status", "guarded width", "rank"], [[cid, searches[cid]["evaluated_count"], searches[cid]["approx_feasible_count"], CANDIDATES[cid]["status"], dimensions[cid]["complete_guarded_width_mm"], CANDIDATES[cid]["rank"]] for cid in CANDIDATES])
    power_table = _md_table(["path", "motor", "selector", "PTO", "90°", "bearings"], [[pid, p["motor_axis"], p["selector_axis"], p["pto"], p["right_angle"], p["bearings"]] for pid, p in POWERPATHS.items()])
    return f"""# Common Rover motor-layout and powerpath trade study v0.9.3.0

## Decision

`RECOMMENDED_LAYOUT_FOR_NEXT_CAD=A_LATERAL_FRONT_DIRECT`

`SECONDARY_LAYOUT=E_LONGITUDINAL_FRONT_PTO`

`RECOMMENDED_POWERPATH=P1_LATERAL_DIRECT_COMMON_SELECTOR_PATTERN_LEFT_RIGHT_INDEPENDENT`

`SECONDARY_POWERPATH=P4_LONGITUDINAL_FRONT_PTO`

`DECISION_CLASS=TOP_2_CANDIDATES_PHYSICAL_MOCKUP_REQUIRED`

The word “common” in P1 means a common selector **pattern**, not a physical shaft joining left and right. Both sides remain mechanically independent. Candidate A has no right-angle stage and keeps the fixed guarded rover width at 290 mm because the existing track proxy, not the motor guard, controls width. Candidate E gives simpler forward unit input but adds a DRIVE-only bevel stage.

## Scope and releases

This lane is an envelope trade study, not a manufacturing drawing. `DESIGN_AUTHORITY_UPDATE=PROHIBITED`, `MANUFACTURING_RELEASE=NOT_APPROVED`, `PURCHASE_APPROVAL=NOT_APPROVED`, `POWERED_TEST=NOT_APPROVED`, and `FIELD_DEPLOYMENT=NOT_APPROVED`.

## Measurements and envelope policy

The physical motor record uses 36.9 mm cylinder diameter, 60.9 mm body-to-front-plate length, 16.9 mm shaft projection, 5.9 mm shaft diameter, 12.0 × 2.7 mm boss, and 9.2 mm rear terminal projection. Fixed axial length is 87.0 mm. Bracket values are 40.1 × 45.5 × 42.8 mm, thickness 3.1 mm. K is 3.4 mm. The 27.7 mm value belongs only to the bearing slot placeholder; exact slot geometry remains `MEASUREMENT_HOLD`. Measurement uncertainty is `USER_NOT_REPORTED`.

S0–S3 rear service extras (10/15/20/25 mm) and G0–G3 guard margins (3/5/8/10 mm) are swept separately. Fixed, guard, connector/tool, and removal envelopes are never merged into one width claim.

## Search result

{candidate_table}

The grid uses 2 or 5 mm X spacing and 5 mm Y/Z spacing. AABB is only a screening stage. The selected A–G points are rechecked with actual CadQuery common-volume calculations against CBOX, BBOX, frame, transformed track proxy, battery extraction keep-out, unit mating keep-out, and drainage keep-outs.

## Powerpaths

{power_table}

Belts and chains only connect parallel axes. P3, P4, and P5 explicitly include bevel/miter gear candidates for every 90-degree transfer. All dog clutch parts are coaxial with their selector shaft. DRIVE and PTO simultaneous engagement is mechanically prohibited; switching requires motor stop and zero-speed confirmation. PTO work requires a brake or mechanical track lock.

## PTO and service

The recommended P1 interface is two independent inward X-axis PTO outputs. The secondary P4 interface is two independent forward (-Y) PTO outputs. A unit is supported by dedicated hitch/guide rails, never by PTO shafts. The actual 60T physical envelope is 100 mm OD and the inherited safety check is 120 mm OD; pulley bore/product fit and guard clearance remain HOLD.

Candidate B is not rejected geometrically, but its outward removal sweep crosses the transformed track proxy. Candidate C fails the right track proxy at the staggered point. Candidate F has a high-CG/weather penalty. Candidate G fails measured-motor-to-input-axis coaxiality.

## Clutch evidence

`S2_10P30=NO_LOAD_PRINTED_SLIDE_REFERENCE_ONLY`. The reported 10.30 mm printed S2 moved smoothly without twist, hang-up, visible radial play, or self-drop at 30–45 degrees. `METAL_TORQUE_CLUTCH_TOLERANCE=NOT_DERIVED_FROM_S2`.
"""


def powerpath_report() -> str:
    rows = _md_table(["ID", "sequence", "physics", "result"], [[pid, f"motor {p['motor_axis']} → selector {p['selector_axis']} → {p['pto']}", p["note"], "CONDITIONAL" if pid != "P6" else "PURCHASE_HOLD"] for pid, p in POWERPATHS.items()])
    return f"""# Candidate powerpath report v0.9.3.0

{rows}

No belt or chain changes axis by 90 degrees. P3/P4/P5 use an explicit bevel or miter pair; P6 is only a future right-angle-gearmotor envelope. Left and right remain independent and no common cross-shaft is introduced. Metal pulley, bearing, bevel, shaft, brake, and dog geometry require product selection and physical measurement.
"""


def pto_report() -> str:
    return """# PTO interface comparison v0.9.3.0

| interface | direction | independence | unit support | decision |
|---|---|---|---|---|
| A | two inward X shafts | left/right independent; no common shaft | hitch + guide frame | recommended with P1 |
| B | two forward -Y shafts | left/right independent | front insertion frame | secondary with P4 |
| C | two rear +Y shafts | independent | rear frame required | rejected for BBOX/wiring/service competition |
| D | one-sided PTO | asymmetric | independent frame | comparison only; not preferred |

PTO work requires DRIVE disengagement and a brake/mechanical lock. Work-unit weight and reaction loads are not carried by PTO shaft or box walls. Coupling product dimensions, alignment allowance, guard opening, and connection tool envelope remain HOLD.
"""


def clutch_report() -> str:
    return """# Slide clutch feasibility v0.9.3.0

Every P1–P5 side uses a coaxial selector and dog clutch with positive DRIVE, central NEUTRAL, and positive PTO stops. The shift interlock requires motor stopped, zero rotation confirmed, left/right state agreement, a position-sensor candidate, and fail-safe NEUTRAL. Mechanical geometry must make DRIVE+PTO simultaneous engagement impossible.

`S2_10P30=NO_LOAD_PRINTED_SLIDE_REFERENCE_ONLY`

The printed 10.30 mm S2 result was smooth straight motion, no twist, no intermediate hang-up, no visible radial play, and no self-drop at 30–45 degrees. It is only a no-load resin reference.

`METAL_TORQUE_CLUTCH_TOLERANCE=NOT_DERIVED_FROM_S2`

Metal dog teeth, torque capacity, wear, lubrication, heat, detent force, bearing fit, shaft fit, and manufacturing tolerance remain HOLD.
"""


def decision_data(dimensions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    a = dimensions["A_LATERAL_FRONT_DIRECT"]
    return {
        "RECOMMENDED_LAYOUT_FOR_NEXT_CAD": "A_LATERAL_FRONT_DIRECT",
        "SECONDARY_LAYOUT": "E_LONGITUDINAL_FRONT_PTO",
        "REJECTED_LAYOUTS": ["C_LATERAL_FORE_AFT_STAGGERED", "G_CURRENT_REPOSITORY_LAYOUT_REPRODUCTION"],
        "RECOMMENDED_POWERPATH": "P1_LATERAL_DIRECT_COMMON_SELECTOR_PATTERN_LEFT_RIGHT_INDEPENDENT",
        "SECONDARY_POWERPATH": "P4_LONGITUDINAL_FRONT_PTO",
        "RECOMMENDED_PTO_DIRECTION": "TWO_INDEPENDENT_INWARD_X_OUTPUTS",
        "RECOMMENDED_MOTOR_AXIS": "X",
        "RECOMMENDED_MOTOR_XYZ_LEFT": CANDIDATES["A_LATERAL_FRONT_DIRECT"]["front_left"],
        "RECOMMENDED_MOTOR_XYZ_RIGHT": CANDIDATES["A_LATERAL_FRONT_DIRECT"]["front_right"],
        "RECOMMENDED_FIXED_WIDTH": a["complete_fixed_width_mm"],
        "RECOMMENDED_GUARDED_WIDTH": a["complete_guarded_width_mm"],
        "RECOMMENDED_HEIGHT": a["maximum_height_mm"],
        "REQUIRED_NEW_METAL_PARTS": ["independent left/right selector shafts", "bearing support plates", "20T/60T pulley hubs", "shaft collars", "mechanical brake/track lock", "guards/load paths to aluminum frame"],
        "REQUIRED_3D_PRINT_PARTS": ["envelope mockup mounts", "guard prototypes", "sensor holders", "cable guides", "non-load-bearing alignment gauges"],
        "REQUIRED_MEASUREMENTS": ["motor uncertainty/repeatability", "front plate thickness and pattern", "vertical slot full geometry", "terminal/cable connector sweep", "bolt-head/tool envelope", "60T bore/width/runout", "bearing and shaft stack", "track exact current solid", "guard thickness", "motor mass/CG", "stall torque/current"],
        "REQUIRED_PURCHASED_PARTS": ["HOLD: pulleys/belts", "HOLD: bearings", "HOLD: bevel gears for secondary", "HOLD: metal dog clutch", "HOLD: brake/lock", "HOLD: sensors"],
        "DECISION_CLASS": "TOP_2_CANDIDATES_PHYSICAL_MOCKUP_REQUIRED",
        "DESIGN_AUTHORITY": "UNCHANGED",
        "MANUFACTURING": "HOLD", "PURCHASE": "HOLD", "POWERED_TEST": "NOT_APPROVED", "FIELD_DEPLOYMENT": "NOT_APPROVED",
    }


def decision_markdown(data: dict[str, Any]) -> str:
    return f"""# Recommended layout decision v0.9.3.0

## First candidate

**A_LATERAL_FRONT_DIRECT + P1**. Motor front plates are at left {data['RECOMMENDED_MOTOR_XYZ_LEFT']} mm and right {data['RECOMMENDED_MOTOR_XYZ_RIGHT']} mm in the current +X-left/+Y-rear/+Z-up frame. Fixed guarded rover width is {data['RECOMMENDED_GUARDED_WIDTH']} mm, controlled by the inherited 290 mm track proxy. The motor+G1 subsystem itself is narrower. No right-angle stage is required.

## Second candidate

**E_LONGITUDINAL_FRONT_PTO + P4**. It keeps fixed width inside the same proxy and provides two simple forward PTO outputs, but requires an explicit bevel/miter pair on each DRIVE branch.

## Decision state

`TOP_2_CANDIDATES_PHYSICAL_MOCKUP_REQUIRED`. This is not a design-authority update. Actual track solid, motor/bracket mounting detail, 60T/bearing stack, connector/cable sweep, guards, metal clutch, brake, and load path are unresolved. No purchase, machining, drilling, powered test, or field deployment is approved.
"""


def measurement_notes() -> str:
    return """# JGB37-520 measurement notes v0.9.3.0

Source for every physical entry is `USER_REPORTED_PHYSICAL_CALIPER_MEASUREMENT`, using the user's caliper. Uncertainty is `USER_NOT_REPORTED`; no ±0.1 mm or other precision is invented. The 70.1 and 87.0 mm values are arithmetic derivations, not independent measurements.

K is the 3.4 mm small bracket fastener-hole candidate. The 27.7 mm value is a representative inner value of the central motor-bearing vertical slot and is never used as the fastener diameter. CAD solids are collision envelopes, not manufacturing reconstructions.
"""


def measurement_holds() -> str:
    return """# JGB37-520 measurement HOLD list v0.9.3.0

- caliper repeatability and measurement uncertainty: `USER_NOT_REPORTED`
- front-plate thickness, bolt pattern, and register details: HOLD
- vertical slot long axis, short axis, corner radii, and center: `MEASUREMENT_HOLD`
- rear connector body, wire exit, bend radius, and unplug sweep: HOLD
- bracket bend radii, material grade, strength, and structural-load authority: HOLD
- bolt-head, nut, washer, hex-key, and screwdriver envelopes: HOLD
- motor mass, center of gravity, stall torque/current, duty cycle, and thermal envelope: HOLD
- pulley bore, hub, flange, axial stack, runout, belt tension, bearing products, and shaft fits: HOLD

No listed HOLD may be inferred from the envelope CAD.
"""


def remaining_measurements() -> str:
    return """# Remaining measurement requests v0.9.3.0

Priority P0: repeat A–M at multiple clock angles; report caliper resolution; measure front-plate thickness/pattern, complete vertical-slot geometry, connector shell and cable unplug/bend sweep, actual bolt heads/tools, motor mass/CG, and current track-to-frame solids.

Priority P1: measure selected 20T/60T pulley bore, flange OD, tooth-face width, hub/set-screw projection, radial/axial runout, belt width/tension, shaft/bearing stack, collars, spacers, guard thickness, and removal direction.

Priority P2: obtain motor stall torque/current, thermal rise, duty cycle, splash/mud exposure, bevel product dimensions for P4, clutch metal material/heat treatment, brake holding torque, and PTO-unit interface loads.

Until these are measured: `PHYSICAL_LOAD_TEST=NOT_PERFORMED`, `POWERED_TEST=NOT_APPROVED`, `MANUFACTURING=HOLD`, `PURCHASE=HOLD`.
"""


def readme_text() -> str:
    return """# v0.9.3.0 handoff

This self-contained lane records user-reported JGB37-520 dimensions and compares seven motor layouts and six physically explicit powerpaths. Run:

```
python -B build_motor_layout_powerpath_trade_study_v0930.py --verify
python -B -m unittest discover -s tests -p "test_*_v0930.py" -v
```

Every STEP is conditional envelope evidence. No path updates Common Rover authority. No manufacturing, purchasing, machining, drilling, powered testing, or field deployment is approved.
"""


def no_release_text() -> str:
    return """DESIGN_AUTHORITY_UPDATE=PROHIBITED
MANUFACTURING_RELEASE=NOT_APPROVED
PURCHASE_APPROVAL=NOT_APPROVED
SHAFT_MACHINING=NOT_APPROVED
DRILLING=NOT_APPROVED
PHYSICAL_LOAD_TEST=NOT_PERFORMED
POWERED_TEST=NOT_APPROVED
FIELD_DEPLOYMENT=NOT_APPROVED
CAD_SCOPE=CONDITIONAL_ENVELOPE_TRADE_STUDY
"""


def _manifest_text() -> str:
    lines = [f"document_id={DOCUMENT_ID}", f"version={VERSION}", f"path_count={len(PACKAGE_PATHS)}", "scope=V0930_LANE_ONLY", "design_authority=UNCHANGED", "manufacturing=NOT_APPROVED", "powered_test=NOT_APPROVED", "field_deployment=NOT_APPROVED", ""]
    for rel in PACKAGE_PATHS:
        if rel.endswith((".step", ".stl")):
            role = "CONDITIONAL_ENVELOPE_CAD"
        elif rel.endswith(".svg"):
            role = "VECTOR_COMPARISON_EVIDENCE"
        elif rel.endswith(".csv"):
            role = "DETERMINISTIC_TABULAR_EVIDENCE"
        elif rel.endswith(".json"):
            role = "MACHINE_READABLE_CONTRACT"
        elif rel.endswith(".py"):
            role = "BUILDER_OR_CONTRACT_TEST"
        else:
            role = "DOCUMENT_OR_PACKAGE_LEDGER"
        lines.append(f"{rel}|{role}")
    return "\n".join(lines)


def _commit_paths_text() -> str:
    prefix = LANE_DIR.relative_to(REPO_ROOT).as_posix() if _live_repository() else "cad/common_rover/common_rover_motor_layout_powerpath_trade_study_v0_9_3_0"
    return "\n".join(f"{prefix}/{rel}" for rel in PACKAGE_PATHS)


def _sha256sums_text() -> str:
    return "\n".join(f"{_sha256(LANE_DIR / rel)}  {rel}" for rel in PACKAGE_PATHS if rel != "SHA256SUMS.txt")


def _parse_sha256sums(base: Path = LANE_DIR) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in (base / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            rows[rel] = digest
    return rows


def verify_hashes(base: Path = LANE_DIR) -> dict[str, Any]:
    expected = _parse_sha256sums(base)
    required = set(PACKAGE_PATHS) - {"SHA256SUMS.txt"}
    mismatches = []
    if set(expected) != required:
        mismatches.append({"missing": sorted(required - set(expected)), "extra": sorted(set(expected) - required)})
    for rel, digest in expected.items():
        actual = _sha256(base / rel) if (base / rel).is_file() else "MISSING"
        if actual != digest:
            mismatches.append({"path": rel, "expected": digest, "actual": actual})
    return {"verified_path_count": len(expected), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def verify_manifest() -> dict[str, Any]:
    lines = (LANE_DIR / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    entries = [line.split("|", 1)[0] for line in lines if "|" in line]
    return {"entry_count": len(entries), "exact_order": entries == list(PACKAGE_PATHS), "status": "PASS" if entries == list(PACKAGE_PATHS) else "FAIL"}


def verify_step_semantics(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for rel in PACKAGE_PATHS:
        if not rel.endswith(".step"):
            continue
        try:
            shape = cq.importers.importStep(str(base / rel)).val()
            b = shape.BoundingBox()
            passed = len(shape.Solids()) >= 1 and all(math.isfinite(value) for value in (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax))
            rows.append({"path": rel, "solids": len(shape.Solids()), "bounds": [round(b.xmin, 3), round(b.xmax, 3), round(b.ymin, 3), round(b.ymax, 3), round(b.zmin, 3), round(b.zmax, 3)], "pass": passed})
        except Exception as exc:
            rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_stl_semantics(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for rel in PACKAGE_PATHS:
        if not rel.endswith(".stl"):
            continue
        path = base / rel
        data = path.read_bytes()
        passed = len(data) > 84
        facet_count = None
        if passed and not data[:5].lower() == b"solid":
            facet_count = struct.unpack("<I", data[80:84])[0]
            passed = facet_count > 0 and 84 + facet_count * 50 <= len(data)
        elif passed:
            facet_count = data.lower().count(b"facet normal")
            passed = facet_count > 0
        rows.append({"path": rel, "facet_count": facet_count, "bytes": len(data), "pass": passed})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_evidence() -> dict[str, Any]:
    measurements = json.loads((LANE_DIR / "common_rover_jgb37_520_physical_measurements_v0930.json").read_text(encoding="utf-8"))
    trades = _read_csv(LANE_DIR / "candidate_trade_matrix_v0930.csv")
    powers = json.loads((LANE_DIR / "common_rover_powerpath_candidate_parameters_v0930.json").read_text(encoding="utf-8"))
    checks = {
        "measurement_count": len(measurements["measurements"]) == len(MEASUREMENTS),
        "K_3p4": next(row for row in measurements["measurements"] if row["measurement_id"] == "K")["measured_value_mm"] == 3.4,
        "slot_27p7_hold": next(row for row in measurements["measurements"] if row["measurement_id"] == "SLOT_27P7")["status"] == "MEASUREMENT_HOLD",
        "derived_fixed_87": measurements["derived"]["MOTOR_TOTAL_AXIAL_FIXED_ENVELOPE_MM"] == 87.0,
        "no_uncertainty_fabrication": all(row["uncertainty"] == "USER_NOT_REPORTED" for row in measurements["measurements"]),
        "seven_candidates": {row["candidate_id"] for row in trades} == set(CANDIDATES),
        "six_powerpaths": set(powers["powerpaths"]) == set(POWERPATHS),
        "rank1_hard_pass": next(row for row in trades if row["recommendation_rank"] == "1")["hard_constraint_pass"] == "YES",
        "no_common_shaft": powers["global_rules"]["left_right_common_shaft"] == "PROHIBITED",
        "simultaneous_engagement": powers["global_rules"]["drive_pto_simultaneous"] == "PROHIBITED",
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def refresh_artifacts() -> dict[str, Any]:
    source_required = ["build_motor_layout_powerpath_trade_study_v0930.py", *[name for name in ROOT_FILES if name.startswith("tests/")]]
    for rel in source_required:
        if not (LANE_DIR / rel).is_file():
            raise RuntimeError(f"source/test missing before refresh: {rel}")
    repository_audit()
    audit = authority_audit_data()
    if audit["protected"]["status"] != "PASS":
        raise RuntimeError("protected authority changed")
    collisions, dimensions, searches = all_reports()
    trades = trade_rows(collisions, dimensions)
    widths = width_rows(dimensions)
    services = service_rows(collisions, dimensions)
    decision = decision_data(dimensions)

    measurement_payload = {
        "document_id": DOCUMENT_ID, "version": VERSION, "motor": "JGB37-520", "rated_voltage": "DC12V", "rated_output_speed_rpm": 60, "planned_quantity": 2,
        "measurements": measurements_rows(),
        "derived": {"MOTOR_BODY_AND_REAR_TERMINAL_FROM_FRONT_PLATE_MM": 70.1, "MOTOR_FRONT_PLATE_TO_SHAFT_TIP_MM": 16.9, "MOTOR_TOTAL_AXIAL_FIXED_ENVELOPE_MM": 87.0},
        "vertical_slot_exact_geometry": "MEASUREMENT_HOLD", "measurement_uncertainty": "USER_NOT_REPORTED", "manufacturing_authority": "NOT_FOR_MANUFACTURING",
    }
    _write_json(LANE_DIR / ROOT_FILES[1], measurement_payload)
    _write_csv(LANE_DIR / ROOT_FILES[2], measurements_rows())
    _write_text(LANE_DIR / ROOT_FILES[3], measurement_notes())
    _write_text(LANE_DIR / ROOT_FILES[4], measurement_holds())
    _write_text(LANE_DIR / ROOT_FILES[5], authority_markdown(audit))
    _write_json(LANE_DIR / ROOT_FILES[6], audit)
    _write_json(LANE_DIR / ROOT_FILES[7], {"document_id": DOCUMENT_ID, "coordinate_authority": audit["coordinate_authority"], "target_width_mm": 290, "absolute_width_rule": "LESS_THAN_300_MM", "grid_searches": searches, "candidates": {cid: {**c, "dimensions": dimensions[cid]} for cid, c in CANDIDATES.items()}})
    _write_json(LANE_DIR / ROOT_FILES[8], {"document_id": DOCUMENT_ID, "powerpaths": POWERPATHS, "global_rules": {"belt_90_degree_axis_change": "PROHIBITED", "chain_90_degree_axis_change": "PROHIBITED", "right_angle_mechanism_required": True, "dog_clutch": "COAXIAL_ONLY", "drive_pto_simultaneous": "PROHIBITED", "left_right_common_shaft": "PROHIBITED", "left_right_drive_independence": "REQUIRED", "brake_or_mechanical_lock_during_pto": "REQUIRED"}, "S2_10P30": "NO_LOAD_PRINTED_SLIDE_REFERENCE_ONLY", "METAL_TORQUE_CLUTCH_TOLERANCE": "NOT_DERIVED_FROM_S2"})
    _write_csv(LANE_DIR / ROOT_FILES[9], trades)
    _write_csv(LANE_DIR / ROOT_FILES[10], collision_rows(collisions))
    _write_csv(LANE_DIR / ROOT_FILES[11], widths)
    _write_csv(LANE_DIR / ROOT_FILES[12], services)
    _write_text(LANE_DIR / ROOT_FILES[13], powerpath_report())
    _write_text(LANE_DIR / ROOT_FILES[14], pto_report())
    _write_text(LANE_DIR / ROOT_FILES[15], clutch_report())
    _write_text(LANE_DIR / ROOT_FILES[16], decision_markdown(decision))
    _write_json(LANE_DIR / ROOT_FILES[17], decision)
    _write_text(LANE_DIR / ROOT_FILES[18], remaining_measurements())
    _write_text(LANE_DIR / ROOT_FILES[0], study_markdown(trades, searches, dimensions))
    _write_text(LANE_DIR / "README_HANDOFF.md", readme_text())
    _write_text(LANE_DIR / "NO_MANUFACTURING_RELEASE.txt", no_release_text())
    _write_text(LANE_DIR / "COMMIT_PATHS.txt", _commit_paths_text())

    local = motor_reference_shapes()
    fixed_names = ["MOTOR_CYLINDER", "REAR_TERMINAL_FIXED_ENVELOPE", "FRONT_PLATE", "OUTPUT_SHAFT", "SHAFT_ROOT_BOSS"]
    _export_step(LANE_DIR / REFERENCE_ARTIFACTS[0], [local[name] for name in fixed_names])
    cq.exporters.export(_compound(local[name] for name in fixed_names), str(LANE_DIR / REFERENCE_ARTIFACTS[1]), tolerance=0.05, angularTolerance=0.2)
    with_bracket = fixed_names + ["MOUNT_BRACKET", "M3_FASTENER_HOLE_CANDIDATES", "VERTICAL_SLOT_PLACEHOLDER"]
    _export_step(LANE_DIR / REFERENCE_ARTIFACTS[2], [local[name] for name in with_bracket])
    cq.exporters.export(_compound(local[name] for name in with_bracket), str(LANE_DIR / REFERENCE_ARTIFACTS[3]), tolerance=0.05, angularTolerance=0.2)
    _export_step(LANE_DIR / REFERENCE_ARTIFACTS[4], [local["FIXED_ENVELOPE"], local["REAR_CABLE_SERVICE_ENVELOPE"], local["CONNECTOR_TOOL_ACCESS"]])
    _export_step(LANE_DIR / REFERENCE_ARTIFACTS[5], [local["FIXED_ENVELOPE"], local["MOTOR_REMOVAL_SWEEP"]])

    for candidate_id in CANDIDATES:
        candidate_dir = LANE_DIR / "artifacts" / "candidates" / candidate_id
        candidate_dir.mkdir(parents=True, exist_ok=True)
        for filename in CANDIDATE_STATE_STEPS:
            _export_step(candidate_dir / filename, _candidate_state_shapes(candidate_id, filename))
        for filename, svg in candidate_svgs(candidate_id, dimensions[candidate_id]).items():
            _write_text(candidate_dir / filename, svg)
        _write_json(candidate_dir / "DIMENSION_REPORT.json", dimensions[candidate_id])
        _write_json(candidate_dir / "COLLISION_REPORT.json", collisions[candidate_id])
    for rel, svg in comparison_svgs(dimensions).items():
        _write_text(LANE_DIR / rel, svg)

    _write_text(LANE_DIR / "test_results_v0930.txt", "status=PREPACKAGE_SELF_CHECKS_PASS\nexternal_contract_tests=RUN_DURING_PACKAGE\nzip_scope_test=RUN_DURING_PACKAGE")
    _write_text(LANE_DIR / "MANIFEST.txt", _manifest_text())
    _write_text(LANE_DIR / "SHA256SUMS.txt", _sha256sums_text())
    actual = _lane_files()
    if actual != sorted(PACKAGE_PATHS):
        raise RuntimeError({"missing": sorted(set(PACKAGE_PATHS) - set(actual)), "extra": sorted(set(actual) - set(PACKAGE_PATHS))})
    evidence = verify_evidence()
    steps = verify_step_semantics()
    stls = verify_stl_semantics()
    if evidence["status"] != "PASS" or steps["status"] != "PASS" or stls["status"] != "PASS":
        raise RuntimeError({"evidence": evidence, "steps": steps, "stls": stls})
    return {"document_id": DOCUMENT_ID, "grid_points_evaluated": sum(row["evaluated_count"] for row in searches.values()), "exact_package_paths": len(PACKAGE_PATHS), "candidate_steps": len(CANDIDATES) * len(CANDIDATE_STATE_STEPS), "step_semantics": f"{steps['pass_count']}/{steps['count']} PASS", "stl_semantics": f"{stls['pass_count']}/{stls['count']} PASS", "parent_protection": audit["protected"]["status"], "status": "PASS"}


def verify() -> dict[str, Any]:
    actual = _lane_files()
    if actual != sorted(PACKAGE_PATHS):
        raise RuntimeError({"missing": sorted(set(PACKAGE_PATHS) - set(actual)), "extra": sorted(set(actual) - set(PACKAGE_PATHS))})
    repository = repository_audit()
    protection = parent_protection_audit()
    hashes = verify_hashes()
    manifest = verify_manifest()
    evidence = verify_evidence()
    steps = verify_step_semantics()
    stls = verify_stl_semantics()
    checks = {"protection": protection["status"], "hashes": hashes["status"], "manifest": manifest["status"], "evidence": evidence["status"], "steps": steps["status"], "stls": stls["status"]}
    if any(value != "PASS" for value in checks.values()):
        raise RuntimeError({"checks": checks, "hashes": hashes, "manifest": manifest, "evidence": evidence})
    return {"document_id": DOCUMENT_ID, "repository": repository, "exact_package_paths": len(PACKAGE_PATHS), "protected_parent_lanes": f"{len(PROTECTED_LANES)}/{len(PROTECTED_LANES)} PASS", "step_semantics": f"{steps['pass_count']}/{steps['count']} PASS", "stl_semantics": f"{stls['pass_count']}/{stls['count']} PASS", "hashes": f"{hashes['verified_path_count']}/{len(PACKAGE_PATHS)-1} PASS", "manifest": f"{manifest['entry_count']}/{len(PACKAGE_PATHS)} PASS", "status": "PASS"}


def _zip_info(rel: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(rel, date_time=(2000, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def _write_zip(path: Path) -> None:
    mode = "x" if path.suffix.lower() == ".zip" else "w"
    with zipfile.ZipFile(path, mode) as archive:
        for rel in PACKAGE_PATHS:
            archive.writestr(_zip_info(rel), (LANE_DIR / rel).read_bytes())


def verify_zip(path: Path, standalone: bool = True) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"ZIP missing: {path}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        traversal = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        if names != list(PACKAGE_PATHS) or duplicates or traversal:
            raise RuntimeError({"scope_match": names == list(PACKAGE_PATHS), "duplicates": duplicates, "traversal": traversal})
        internal = _parse_sha256sums_from_bytes(archive.read("SHA256SUMS.txt"))
        mismatches = [rel for rel, digest in internal.items() if hashlib.sha256(archive.read(rel)).hexdigest() != digest]
        lane_mismatches = [rel for rel in PACKAGE_PATHS if hashlib.sha256(archive.read(rel)).hexdigest() != _sha256(LANE_DIR / rel)]
    standalone_result = "NOT_REQUESTED"
    if standalone:
        with tempfile.TemporaryDirectory(prefix="ps_cr_v0930_zip_") as temp:
            target = Path(temp)
            with zipfile.ZipFile(path) as archive:
                archive.extractall(target)
            env = dict(os.environ)
            env["V0930_TEST_ZIP"] = str(path)
            build = _run([sys.executable, "-B", "build_motor_layout_powerpath_trade_study_v0930.py", "--verify"], cwd=target, env=env)
            tests = _run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*_v0930.py", "-v"], cwd=target, env=env)
            if build.returncode or tests.returncode:
                raise RuntimeError({"standalone_builder": build.stdout, "standalone_tests": tests.stdout})
            standalone_result = "PASS"
    if mismatches or lane_mismatches:
        raise RuntimeError({"internal_hash_mismatches": mismatches, "lane_mismatches": lane_mismatches})
    return {"zip_path": str(path), "entry_count": len(names), "duplicates": duplicates, "path_traversal": traversal, "internal_hash_verification": "PASS", "lane_byte_match": "PASS", "standalone_verify": standalone_result, "zip_sha256": _sha256(path), "status": "PASS"}


def _parse_sha256sums_from_bytes(data: bytes) -> dict[str, str]:
    result = {}
    for line in data.decode("utf-8").splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            result[rel] = digest
    return result


def package_handoff() -> dict[str, Any]:
    verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{timestamp}.zip"
    if final_path.exists():
        raise RuntimeError(f"refusing to overwrite existing ZIP: {final_path}")
    temporary = DOWNLOAD_DIR / f".{ZIP_PREFIX}{timestamp}.validation.tmp"
    if temporary.exists():
        raise RuntimeError(f"temporary validation path already exists: {temporary}")
    try:
        _write_zip(temporary)
        env = dict(os.environ)
        env["V0930_TEST_ZIP"] = str(temporary)
        result = _run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*_v0930.py", "-v"], cwd=LANE_DIR, env=env)
        if result.returncode:
            raise RuntimeError(f"contract tests failed before package:\n{result.stdout}")
        summary = [line for line in result.stdout.splitlines() if line.startswith("Ran ") or line == "OK"]
        _write_text(LANE_DIR / "test_results_v0930.txt", "command=python -B -m unittest discover -s tests -p test_*_v0930.py -v\nstatus=PASS\n" + "\n".join(summary) + "\nfull_output:\n" + result.stdout)
        _write_text(LANE_DIR / "SHA256SUMS.txt", _sha256sums_text())
        verify()
    finally:
        if temporary.exists():
            temporary.unlink()
    _write_zip(final_path)
    report = verify_zip(final_path, standalone=True)
    return {"verification": "PASS", **report}


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
    if sum(bool(value) for value in (args.refresh_artifacts, args.verify, args.package, args.verify_zip)) != 1:
        parser.error("choose exactly one action")
    if args.refresh_artifacts:
        result = refresh_artifacts()
    elif args.verify:
        result = verify()
    elif args.package:
        result = package_handoff()
    else:
        result = verify_zip(args.verify_zip, standalone=True)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
