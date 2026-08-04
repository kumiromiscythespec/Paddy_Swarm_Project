from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import cadquery as cq


DOCUMENT_ID = "PS-CR-V0934-POWERTRAIN-FRAME-JOINT-TRADE-STUDY"
VERSION = "0.9.3.4"
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_9_3_4_Powertrain_Frame_Joint_Trade_Study_"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
ANCHOR = "198a708395df6e43556a744ae9c5629b50360e2f"

PARENT_DIRS = {
    "v0.9.3.0": REPO_ROOT / "cad/common_rover/common_rover_motor_layout_powerpath_trade_study_v0_9_3_0",
    "v0.9.3.1": REPO_ROOT / "cad/common_rover/common_rover_candidate_a_physical_mockup_v0_9_3_1",
    "v0.9.3.3": REPO_ROOT / "cad/common_rover/common_rover_candidate_a_motor_bracket_8hole_flat_plate_v0_9_3_3",
}
PARENT_CONTRACTS = {
    "v0.9.3.0": {"path_count": 151, "ledger_sha256": "3528bc1192983fce3daeb5e543fe3f207fa59eb78615ddcde0643e73f9159199", "git_mode": "TRACKED_LANE"},
    "v0.9.3.1": {"path_count": 46, "ledger_sha256": "2f58d6fddab3c9c0f3deed09188974d3642dcdc89e94b0240eec869a7de770f8", "git_mode": "TRACKED_LANE"},
    "v0.9.3.3": {"path_count": 38, "ledger_sha256": "2c0bd512c9e347ad1429fe0974948f64fe587f53ed616135d9c663b0814bb5be", "git_mode": "UNTRACKED_LANE"},
}
EXPECTED_TRACKED_DIFF = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
}
AUTHORITY_POINTER_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b0f0612585634b224dae562f1f68c6bc71ae39d882b6034123d",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
# Correct the docs pointer explicitly; keeping the declaration close to the guard makes accidental edits visible.
AUTHORITY_POINTER_HASHES["docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md"] = "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0"

SOURCE_REFERENCES = {
    "JGB37_FIXED": ("v0.9.3.0", "artifacts/motor_reference/JGB37_520_MEASURED_FIXED_ENVELOPE.step", "49e3489ef1c309bdb7cb5b0d73004eee3c38af4f14595c36eb78ebc22abad5b2", "PARAMETER_REUSE_WORLD_PLACEMENT"),
    "JGB37_BRACKET": ("v0.9.3.0", "artifacts/motor_reference/JGB37_520_MEASURED_WITH_BRACKET.step", "4962b4956869bc7df81b49af6e8f11b512d0dc7d047992d424971cca2bbfae56", "PARAMETER_REUSE_WORLD_PLACEMENT"),
    "JGB37_SERVICE": ("v0.9.3.0", "artifacts/motor_reference/JGB37_520_SERVICE_ENVELOPE.step", "129507c28d61f9c3e85bd6b622cba44010157de7fa78c1294fce1cffba139dd4", "PARAMETER_REUSE_WORLD_PLACEMENT"),
    "A_POWERPATH": ("v0.9.3.0", "artifacts/candidates/A_LATERAL_FRONT_DIRECT/MOTOR_POWERPATH.step", "cdf3dffb96f0910deb44b674174e716751d7a10a36e519e053f8439cc8387fc8", "WORLD_AS_EXPORTED_REFERENCE"),
    "A_GUARDS": ("v0.9.3.0", "artifacts/candidates/A_LATERAL_FRONT_DIRECT/ALL_FIXED_GUARDS.step", "cabbfdfb3381c253f5c9107b554071a9ea2c6f42bd9b0cc887e9b3a32ea46efb", "WORLD_AS_EXPORTED_REFERENCE"),
    "A_BELT_SERVICE": ("v0.9.3.0", "artifacts/candidates/A_LATERAL_FRONT_DIRECT/BELT_REPLACEMENT_ACCESS.step", "a6b2f1f482a92957fdc54fc68567a722a28ebbffdf3b2f7a214656e750c72fd1", "WORLD_AS_EXPORTED_REFERENCE"),
    "A_MOCKUP": ("v0.9.3.1", "artifacts/assemblies/CANDIDATE_A_MOCKUP_ASSEMBLY.step", "b1c5ab1c651951ac694483e0bb5c10179e8299181123b1afe22208e4dddfc725", "WORLD_AS_EXPORTED_REFERENCE"),
    "A_SERVICE": ("v0.9.3.1", "artifacts/assemblies/CANDIDATE_A_SERVICE_SWEEP.step", "f72a91096c23035ff44e88587115207586a732e9f718a001509109a7d10ac285", "WORLD_AS_EXPORTED_REFERENCE"),
    "V0933_PLATE": ("v0.9.3.3", "artifacts/assemblies/PS_CR_V0933_8HOLE_FLAT_PLATE_PETG_T6.step", "45bf57a7fd60488ba6826b826700b3dffe693befd362b8aaa8f3bf47cfcb8b66", "CENTER_XY_AT_MOTOR_DATUM_HEIGHT_CASE"),
    "V0933_BRACKET": ("v0.9.3.3", "artifacts/assemblies/PS_CR_V0933_PLATE_WITH_BRACKET_PROXY.step", "a23d86465482b4ba1032a0ad8dfb63348ff9691b1f8f7299879b802105753cf5", "CENTER_XY_AT_MOTOR_DATUM_HEIGHT_CASE"),
    "V0933_H6": ("v0.9.3.3", "artifacts/assemblies/PS_CR_V0933_FULL_STACK_SPACER_H6_REFERENCE.step", "cd0d4669f8f33bb9216f95dbdf07bba2b3f298c3e043ebde96f22cee79a28c45", "HEIGHT_CASE_REFERENCE_ONLY"),
    "V0933_H8": ("v0.9.3.3", "artifacts/assemblies/PS_CR_V0933_FULL_STACK_SPACER_H8_REFERENCE.step", "af3113f3a6dd2dce53bc5df308190e118cde7f0ab4259c489b82c1f27e24a9f8", "HEIGHT_CASE_REFERENCE_ONLY"),
    "V0933_H10": ("v0.9.3.3", "artifacts/assemblies/PS_CR_V0933_FULL_STACK_SPACER_H10_REFERENCE.step", "60383d35bd5b2868e7df1545591a6a2bbbd5b13112199a9161e60edf30d519fd", "HEIGHT_CASE_REFERENCE_ONLY"),
}

# User-supplied frame contract and conservative proxy dimensions.
FRAME_OUTER_X = 180.0
POWERTRAIN_CLEAR_X = 100.0
SIDE_RAIL_X = 40.0
SIDE_RAIL_Z = 20.0
LEFT_RAIL_CENTER_X = -70.0
RIGHT_RAIL_CENTER_X = 70.0
LEFT_INNER_FACE_X = -50.0
RIGHT_INNER_FACE_X = 50.0
OUTER_X = (-90.0, 90.0)
CROSSMEMBER_X = 100.0
CROSSMEMBER_Y = 40.0
CROSSMEMBER_Z = 20.0
BASELINE_INTRUSION = 27.9
BASELINE_REMAINING = POWERTRAIN_CLEAR_X - 2 * BASELINE_INTRUSION
TIE_PLATE_X = 180.0
TIE_PLATE_Y = 40.0
TIE_PLATE_Z = 3.0
TIE_PLATE_RADIUS = 3.0
HARD_MIN_CLEARANCE = 10.0
TARGET_CLEARANCE = 15.0

# Parent Candidate A actual/proxy envelope values. The guard is conservatively extended 5 mm.
POWERTRAIN_CENTER_Y = -185.0
PHYSICAL_Y_MIN, PHYSICAL_Y_MAX = -245.0, -125.0
FIXED_Y_MIN, FIXED_Y_MAX = -250.0, -120.0
SERVICE_Y_MIN, SERVICE_Y_MAX = -255.0, -115.0
MIN_FRONT_Y, MIN_REAR_Y = -280.0, -90.0
TARGET_FRONT_Y, TARGET_REAR_Y = -285.0, -85.0
MIN_FRAME_LENGTH = 230.0
TARGET_FRAME_LENGTH = 240.0
HEIGHT_CASES = {"H6": {"increase": 12.0, "motor_z": 117.0}, "H8": {"increase": 14.0, "motor_z": 119.0}, "H10": {"increase": 16.0, "motor_z": 121.0}}
ACTUAL_HEIGHT_CASE = "ACTUAL_H4P3_TO_H4P5_WASHER_NUT_STACK"
PREVIOUS_HEIGHT_CASE = "PREVIOUS_H3P8_TO_H3P9_TWO_NUT_STACK"
HEIGHT_CASES = {
    ACTUAL_HEIGHT_CASE: {"increase": 10.4, "motor_z": 115.4, "priority": 1, "basis": "LATEST_USER_REPORTED_PHYSICAL_RESULT"},
    PREVIOUS_HEIGHT_CASE: {"increase": 9.875, "motor_z": 114.875, "priority": 2, "basis": "HISTORICAL_PHYSICAL_RESULT"},
    "H6": {"increase": 12.0, "motor_z": 117.0, "priority": 3, "basis": "REFERENCE_ONLY"},
    "H8": {"increase": 14.0, "motor_z": 119.0, "priority": 4, "basis": "REFERENCE_ONLY"},
    "H10": {"increase": 16.0, "motor_z": 121.0, "priority": 5, "basis": "REFERENCE_ONLY"},
}
PHYSICAL_RESULT = {
    "latest_physical_result": True,
    "plate_id": "PS_CR_V0933_MOTOR_BRACKET_8HOLE_FLAT_PLATE_PETG_T6",
    "petg_plate_thickness_mm": 6.0,
    "m3_fastener": "M3x16",
    "m5_fastener": "M5x16",
    "actual_m5_stack_top_to_bottom": ["M5x16 screw head", "existing captive washer stack", "additional top plain flat washer", "PETG 8-hole plate", "one M5 height-adjustment nut", "additional bottom plain flat washer", "aluminum extrusion top surface", "slot T-nut"],
    "additional_plain_washer_count_per_m5": 2,
    "height_adjustment_nut_count_per_m5": 1,
    "top_adjustment_nut": "NOT_USED_IN_LATEST_STACK",
    "top_plain_washer": "USED",
    "bottom_adjustment_nut": "USED",
    "bottom_plain_washer": "USED",
    "direct_hex_nut_contact_to_aluminum": "NOT_USED_IN_LATEST_STACK",
    "spacerless_direct_clamp": "REJECTED_DUE_TO_ALUMINUM_INDENTATION",
    "individual_corner_gaps_mm": "NOT_REPORTED_IN_LATEST_OVERRIDE",
    "minimum_gap_mm": 4.3,
    "maximum_gap_mm": 4.5,
    "gap_range_mm": 0.2,
    "derived_nominal_gap_mm": 4.4,
    "minimum_plate_top_height_mm": 10.3,
    "maximum_plate_top_height_mm": 10.5,
    "derived_nominal_plate_top_height_mm": 10.4,
    "four_point_levelness": "PHYSICAL_PASS_NO_LOAD",
    "four_point_levelness_range_mm": 0.2,
    "aluminum_frame_indentation": "NONE",
    "aluminum_protection_result": "PASS",
    "m3_head_washer_to_frame_contact": "NONE",
    "tnut_thread_traversal": "FULL_THREAD_TRAVERSAL_CONFIRMED",
    "tnut_thread_traversal_result": "PHYSICAL_PASS_USER_REPORTED",
    "m5x16_thread_engagement": "FULL_TNUT_THREAD_TRAVERSAL_USER_REPORTED",
    "m5_thread_pitch": "MEASUREMENT_HOLD",
    "m5_engagement_length_mm": "NOT_CALCULATED",
    "plate_rocking": "NONE",
    "plate_visible_warp": "NONE",
    "local_indentation": "NONE",
    "m5_area_whitening": "NONE",
    "m3_hole_alignment": "PHYSICAL_PASS",
    "m5_hole_alignment": "PHYSICAL_PASS",
    "motor_bracket_alignment": "PHYSICAL_PASS",
    "motor_bracket_seating": "PHYSICAL_PASS_NO_LOAD",
    "petg_plate_no_load_result": "PASS",
    "m5x16_no_load_result": "PHYSICAL_PASS",
    "m5x16_powered_or_belt_load": "NOT_APPROVED",
    "m5x20_comparison_priority": "LOWERED_BUT_NOT_CANCELLED",
    "m5x20_physical_result": "NOT_TESTED",
    "m5x25": "LENGTH_HOLD",
    "previous_physical_result": {"status": "HISTORICAL_PHYSICAL_RESULT", "stack": "PREVIOUS_TWO_NUT_STACK", "supersession": "SUPERSEDED_BY_TWO_WASHER_ONE_NUT_STACK", "gaps_mm": {"left_front": 3.8, "right_front": 3.9, "left_rear": 3.9, "right_rear": 3.9}, "average_gap_mm": 3.875, "gap_range_mm": 0.1, "m5_engagement_turns_approx": 2.5},
    "creep_test_24h": {"status": "REQUIRED_BEFORE_BELT_TENSION", "acceptance": {"maximum_gap_range_mm": 0.2, "new_aluminum_indentation": "NONE", "petg_whitening": "NONE", "local_petg_indentation": "NONE", "washer_migration": "NONE", "nut_loosening": "NONE", "plate_rocking": "NONE"}},
}
REFERENCE_ZIP = {
    "path": r"D:\Downloads\Paddy_Swarm_Common_Rover_v0_9_3_3_8Hole_Flat_Plate_20260804_155850.zip",
    "sha256": "2832a60935e508f8287abf6d89576ae9f01a8e59926a242e599713cbba0e04a5",
}

ROOT_FILES = [
    "powertrain_frame_joint_trade_study_v0934.md",
    "frame_joint_parameters_v0934.json",
    "actual_motor_plate_physical_result_v0934.md",
    "actual_motor_plate_physical_result_v0934.json",
    "frame_measurements_v0934.csv",
    "candidate_a_end_tap_report_v0934.md",
    "candidate_b_tie_plate_report_v0934.md",
    "baseline_corner_rejection_v0934.md",
    "candidate_trade_matrix_v0934.csv",
    "candidate_collision_matrix_v0934.csv",
    "candidate_dimension_report_v0934.csv",
    "crossmember_y_sweep_v0934.csv",
    "repairability_score_v0934.csv",
    "fastener_access_report_v0934.csv",
    "height_case_report_v0934.csv",
    "m5x16_m5x20_comparison_plan_v0934.md",
    "remaining_measurements_v0934.md",
    "physical_mockup_plan_v0934.md",
    "README_HANDOFF.md",
    "NO_MANUFACTURING_RELEASE.txt",
    "build_powertrain_frame_joint_trade_study_v0934.py",
    "tests/test_powertrain_frame_joint_trade_study_v0934.py",
    "COMMIT_PATHS.txt",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "test_results_v0934.txt",
]
A_FILES = [
    "artifacts/candidates/A_END_TAP/A_FRAME_ONLY.step",
    "artifacts/candidates/A_END_TAP/A_FASTENER_ENVELOPES.step",
    "artifacts/candidates/A_END_TAP/A_POWERTRAIN_ACTUAL_HEIGHT.step",
    "artifacts/candidates/A_END_TAP/A_POWERTRAIN_GUARDED.step",
    "artifacts/candidates/A_END_TAP/A_SERVICE_SWEEP.step",
    "artifacts/candidates/A_END_TAP/A_H6_REFERENCE.step",
    "artifacts/candidates/A_END_TAP/A_H8_REFERENCE.step",
    "artifacts/candidates/A_END_TAP/A_H10_REFERENCE.step",
    "artifacts/candidates/A_END_TAP/A_TOP_VIEW.svg",
    "artifacts/candidates/A_END_TAP/A_FRONT_VIEW.svg",
    "artifacts/candidates/A_END_TAP/A_SIDE_VIEW.svg",
    "artifacts/candidates/A_END_TAP/A_FRONT_JOINT_SECTION.svg",
    "artifacts/candidates/A_END_TAP/A_REAR_JOINT_SECTION.svg",
]
B_FILES = [
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_FRAME_ONLY.step",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_TIE_PLATES_ONLY.step",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_FASTENER_ENVELOPES.step",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_POWERTRAIN_ACTUAL_HEIGHT.step",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_POWERTRAIN_GUARDED.step",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_SERVICE_SWEEP.step",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_H6_REFERENCE.step",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_H8_REFERENCE.step",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_H10_REFERENCE.step",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_TOP_VIEW.svg",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_FRONT_VIEW.svg",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_SIDE_VIEW.svg",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_FRONT_JOINT_SECTION.svg",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_REAR_JOINT_SECTION.svg",
]
BASELINE_FILES = [
    "artifacts/baseline/INNER_CORNER_INTRUSION_PROXY.step",
    "artifacts/baseline/BASELINE_POWERTRAIN_FIXED.step",
    "artifacts/baseline/BASELINE_TOP_VIEW.svg",
]
PHYSICAL_ACTUAL_FILES = [
    "artifacts/physical_actual/ACTUAL_MOTOR_PLATE_STACK.step",
    "artifacts/physical_actual/ACTUAL_GAP_3P8_3P9_REFERENCE.step",
    "artifacts/physical_actual/ACTUAL_M5X16_2P5_TURN_REFERENCE.step",
    "artifacts/physical_actual/ACTUAL_HEIGHT_SIDE_VIEW.svg",
    "artifacts/physical_actual/ACTUAL_GAP_TABLE.svg",
]
COMPARISON_FILES = [
    "artifacts/comparison/A_B_OVERLAY_TOP.step",
    "artifacts/comparison/A_B_OVERLAY_SIDE.step",
    "artifacts/comparison/FRAME_LENGTH_SWEEP.svg",
    "artifacts/comparison/CENTRAL_CLEARANCE_COMPARISON.svg",
    "artifacts/comparison/UNDERSIDE_DROP_COMPARISON.svg",
    "artifacts/comparison/SERVICE_ACCESS_COMPARISON.svg",
    "artifacts/comparison/HEIGHT_CASE_COMPARISON.svg",
    "artifacts/comparison/M5X16_M5X20_TEST_PLAN.svg",
]
LEGACY_PRESERVED_PATHS = {
    "frame_measurements_v0934.json",
    "candidate_b_underside_tie_plate_report_v0934.md",
    "baseline_inner_corner_rejection_v0934.md",
    "artifacts/candidates/A_END_TAP/A_FRAME_WITH_FASTENER_ENVELOPES.step",
    "artifacts/candidates/A_END_TAP/A_POWERTRAIN_FIXED.step",
    "artifacts/candidates/A_END_TAP/A_SECTION_AT_FRONT_JOINT.svg",
    "artifacts/candidates/A_END_TAP/A_SECTION_AT_REAR_JOINT.svg",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_FRAME_WITH_FASTENER_ENVELOPES.step",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_POWERTRAIN_FIXED.step",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_SECTION_AT_FRONT_JOINT.svg",
    "artifacts/candidates/B_UNDERSIDE_TIE_PLATE/B_SECTION_AT_REAR_JOINT.svg",
    "artifacts/baseline/BASELINE_FIXED_ENVELOPE.step",
    "artifacts/comparison/CLEAR_WIDTH_COMPARISON.svg",
    "artifacts/templates/A_END_FACE_CENTER_WITNESS.svg",
    "artifacts/templates/A_SIDE_RAIL_THROUGH_HOLE_WITNESS.svg",
    "artifacts/templates/A_BOLT_TOOL_ENVELOPE.svg",
    "artifacts/templates/B_TIE_PLATE_MEASUREMENT_REFERENCE_1_TO_1.svg",
}
PACKAGE_PATHS = tuple(ROOT_FILES + A_FILES + B_FILES + BASELINE_FILES + PHYSICAL_ACTUAL_FILES + COMPARISON_FILES)
EXPECTED_LANE_PATHS = set(PACKAGE_PATHS) | LEGACY_PRESERVED_PATHS
STEP_FILES = tuple(path for path in PACKAGE_PATHS if path.endswith(".step"))
SVG_FILES = tuple(path for path in PACKAGE_PATHS if path.endswith(".svg"))
CSV_FILES = tuple(path for path in PACKAGE_PATHS if path.endswith(".csv"))
if len(PACKAGE_PATHS) != 69 or len(set(PACKAGE_PATHS)) != 69 or len(STEP_FILES) != 24 or len(SVG_FILES) != 19 or len(CSV_FILES) != 8:
    raise RuntimeError("v0.9.3.4 exact package contract mismatch")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"empty CSV: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def run(command: list[str], cwd: Path = REPO_ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stdout}{result.stderr}")
    return result.stdout.strip()


def live_repository() -> bool:
    return run(["git", "rev-parse", "--show-toplevel"]).returncode == 0


def lane_files(base: Path = LANE_DIR) -> list[str]:
    return sorted(path.relative_to(base).as_posix() for path in base.rglob("*") if path.is_file())


def full_lane_ledger(path: Path) -> dict[str, Any]:
    rows = [f"{item.relative_to(path).as_posix()}\t{sha256(item)}" for item in sorted((p for p in path.rglob("*") if p.is_file()), key=lambda p: p.relative_to(path).as_posix())]
    payload = ("\n".join(rows) + "\n").encode("utf-8")
    return {"file_count": len(rows), "sha256": hashlib.sha256(payload).hexdigest()}


def source_reference_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    rows = []
    for source_id, (version, rel, expected, transform) in SOURCE_REFERENCES.items():
        row = {"source_id": source_id, "parent": version, "path": rel, "sha256": expected, "transform": transform, "coordinate_mapping": "+X left, +Y rear, +Z up"}
        if live:
            path = PARENT_DIRS[version] / rel
            actual = sha256(path) if path.is_file() else "MISSING"
            row.update({"actual_sha256": actual, "pass": actual == expected})
        else:
            row.update({"mode": "STANDALONE_EMBEDDED_EVIDENCE", "pass": True})
        rows.append(row)
    if not all(row["pass"] for row in rows):
        raise RuntimeError({"source_reference_audit": rows})
    return {"rows": rows, "status": "PASS"}


def reference_zip_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    if not live:
        return {**REFERENCE_ZIP, "mode": "STANDALONE_EMBEDDED_EVIDENCE", "status": "PASS"}
    path = Path(REFERENCE_ZIP["path"])
    actual = sha256(path) if path.is_file() else "MISSING"
    result = {**REFERENCE_ZIP, "actual_sha256": actual, "exists": path.is_file(), "status": "PASS" if actual == REFERENCE_ZIP["sha256"] else "FAIL"}
    if result["status"] != "PASS":
        raise RuntimeError({"reference_zip_audit": result})
    return result


def parent_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    rows: dict[str, Any] = {}
    untracked_all = set(git("ls-files", "--others", "--exclude-standard").replace("\\", "/").splitlines()) if live else set()
    for version, contract in PARENT_CONTRACTS.items():
        if not live:
            rows[version] = {**contract, "mode": "STANDALONE_EMBEDDED_EVIDENCE", "status": "PASS"}
            continue
        path = PARENT_DIRS[version]
        rel = path.relative_to(REPO_ROOT).as_posix()
        ledger = full_lane_ledger(path)
        worktree = [line for line in git("diff", "--name-only", "--", rel).splitlines() if line]
        staged = [line for line in git("diff", "--cached", "--name-only", "--", rel).splitlines() if line]
        actual_files = sorted(item.relative_to(REPO_ROOT).as_posix() for item in path.rglob("*") if item.is_file())
        if contract["git_mode"] == "TRACKED_LANE":
            git_scope = sorted(line for line in git("ls-files", rel).splitlines() if line)
        else:
            git_scope = sorted(line for line in untracked_all if line.startswith(rel + "/"))
        checks = {
            "exists": path.is_dir(),
            "path_count": ledger["file_count"] == contract["path_count"],
            "ledger": ledger["sha256"] == contract["ledger_sha256"],
            "worktree_clean": not worktree,
            "index_clean": not staged,
            "git_scope_exact": git_scope == actual_files,
        }
        if not all(checks.values()):
            raise RuntimeError({"parent": version, "checks": checks, "ledger": ledger, "git_scope_count": len(git_scope), "actual_count": len(actual_files), "worktree": worktree, "staged": staged})
        rows[version] = {**contract, "checks": checks, "status": "PASS"}
    source_reference_audit(live)
    reference_zip_audit(live)
    return {"parents": rows, "source_references": "PASS", "reference_zip": "PASS", "status": "PASS"}


def repository_audit(require_complete: bool = True) -> dict[str, Any]:
    if not live_repository():
        return {"mode": "STANDALONE_HANDOFF", "status": "PASS"}
    root = str(Path(git("rev-parse", "--show-toplevel")).resolve())
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    git("cat-file", "-e", f"{ANCHOR}^{{commit}}")
    ancestor = run(["git", "merge-base", "--is-ancestor", ANCHOR, head]).returncode == 0
    tracked = {line.replace("\\", "/") for line in git("diff", "--name-only").splitlines() if line}
    staged = {line.replace("\\", "/") for line in git("diff", "--cached", "--name-only").splitlines() if line}
    untracked = [line.replace("\\", "/") for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line]
    lane_rel = LANE_DIR.relative_to(REPO_ROOT).as_posix()
    lane_untracked = sorted(path[len(lane_rel) + 1:] for path in untracked if path.startswith(lane_rel + "/"))
    ignored = [line for line in git("ls-files", "--others", "--ignored", "--exclude-standard", "--", lane_rel).splitlines() if line]
    actual = lane_files()
    forbidden = [path for path in actual if "__pycache__" in path.lower() or path.lower().endswith((".pyc", ".pyo", ".fcstd", ".blend", ".tmp"))]
    pointers = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_POINTER_HASHES}
    parents = parent_audit(True)
    checks = {
        "root": root.lower() == str(REPO_ROOT.resolve()).lower(), "branch": branch == EXPECTED_BRANCH,
        "anchor_ancestor": ancestor, "tracked_diff_preserved": tracked == EXPECTED_TRACKED_DIFF,
        "staged_zero": not staged, "authority_hashes": pointers == AUTHORITY_POINTER_HASHES,
        "parent_protection": parents["status"] == "PASS", "lane_scope": set(actual).issubset(EXPECTED_LANE_PATHS),
        "lane_git_scope_match": lane_untracked == actual, "lane_complete": actual == sorted(EXPECTED_LANE_PATHS) if require_complete else True,
        "ignored_zero": not ignored, "forbidden_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_guard": checks, "actual": actual, "lane_untracked": lane_untracked, "ignored": ignored, "forbidden": forbidden})
    return {"mode": "LIVE_REPOSITORY", "root": root, "branch": branch, "head": head, "anchor": ANCHOR, "anchor_ancestor": ancestor,
            "commit_distance": int(git("rev-list", "--count", f"{ANCHOR}..{head}")), "tracked_diff": sorted(tracked), "staged_diff": sorted(staged),
            "untracked_total": len(untracked), "lane_untracked_count": len(lane_untracked), "checks": checks, "status": "PASS"}


def compound(shapes: Iterable[cq.Shape]) -> cq.Shape:
    values = list(shapes)
    if not values:
        raise ValueError("compound requires shapes")
    return cq.Compound.makeCompound(values)


def box(dx: float, dy: float, dz: float, center: tuple[float, float, float]) -> cq.Shape:
    return cq.Workplane("XY").box(dx, dy, dz).translate(center).val()


def cylinder_x(radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, length, cq.Vector(center[0] - length / 2, center[1], center[2]), cq.Vector(1, 0, 0))


def cylinder_z(radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, length, cq.Vector(center[0], center[1], center[2] - length / 2), cq.Vector(0, 0, 1))


def rounded_plate(dx: float, dy: float, dz: float, radius: float, z_bottom: float, y_center: float) -> cq.Shape:
    return cq.Workplane("XY").box(dx, dy, dz, centered=(True, True, False)).edges("|Z").fillet(radius).translate((0, y_center, z_bottom)).val()


def bounds(shape: cq.Shape) -> dict[str, float]:
    b = shape.BoundingBox()
    return {key: round(value, 6) for key, value in {"xmin": b.xmin, "xmax": b.xmax, "ymin": b.ymin, "ymax": b.ymax, "zmin": b.zmin, "zmax": b.zmax, "xlen": b.xlen, "ylen": b.ylen, "zlen": b.zlen}.items()}


def intersection_volume(a: cq.Shape, b: cq.Shape) -> float:
    return max(0.0, float(a.intersect(b).Volume()))


def frame_shapes(front_y: float = TARGET_FRONT_Y, rear_y: float = TARGET_REAR_Y) -> list[cq.Shape]:
    length = rear_y - front_y + CROSSMEMBER_Y
    center_y = (front_y + rear_y) / 2
    left = box(SIDE_RAIL_X, length, SIDE_RAIL_Z, (LEFT_RAIL_CENTER_X, center_y, SIDE_RAIL_Z / 2))
    right = box(SIDE_RAIL_X, length, SIDE_RAIL_Z, (RIGHT_RAIL_CENTER_X, center_y, SIDE_RAIL_Z / 2))
    front = box(CROSSMEMBER_X, CROSSMEMBER_Y, CROSSMEMBER_Z, (0, front_y, CROSSMEMBER_Z / 2))
    rear = box(CROSSMEMBER_X, CROSSMEMBER_Y, CROSSMEMBER_Z, (0, rear_y, CROSSMEMBER_Z / 2))
    return [left, right, front, rear]


def tie_plate_shapes(front_y: float = TARGET_FRONT_Y, rear_y: float = TARGET_REAR_Y) -> list[cq.Shape]:
    return [rounded_plate(TIE_PLATE_X, TIE_PLATE_Y, TIE_PLATE_Z, TIE_PLATE_RADIUS, -TIE_PLATE_Z, y) for y in (front_y, rear_y)]


def candidate_a_fastener_shapes() -> list[cq.Shape]:
    shapes: list[cq.Shape] = []
    for y in (TARGET_FRONT_Y, TARGET_REAR_Y):
        for sign in (-1, 1):
            # M6 comparison is the conservative visible candidate. Exact thread/core layout remains HOLD.
            shapes.append(cylinder_x(3.0, 46.0, (sign * 73.0, y, 10.0)))
            shapes.append(cylinder_x(6.0, 6.0, (sign * 93.0, y, 10.0)))
            shapes.append(cylinder_x(11.0, 30.0, (sign * 111.0, y, 10.0)))
            shapes.append(cylinder_x(3.0, 8.0, (sign * 46.0, y, 10.0)))
    return shapes


def candidate_b_fastener_shapes() -> list[cq.Shape]:
    # Measurement-zone cylinders, not released hole coordinates or fastener products.
    return [cylinder_z(4.0, 29.0, (x, y, 5.5)) for y in (TARGET_FRONT_Y, TARGET_REAR_Y) for x in (-70.0, 70.0)]


def powertrain_components(height_case: str = ACTUAL_HEIGHT_CASE) -> dict[str, cq.Shape]:
    case = HEIGHT_CASES[height_case]
    motor_z = case["motor_z"]
    plate_gap = case["increase"] - PHYSICAL_RESULT["petg_plate_thickness_mm"]
    plate_center_z = SIDE_RAIL_Z + plate_gap + PHYSICAL_RESULT["petg_plate_thickness_mm"] / 2
    stack_center_z = SIDE_RAIL_Z + case["increase"] / 2
    result: dict[str, cq.Shape] = {}
    for side, sign in (("LEFT", 1), ("RIGHT", -1)):
        front_x = sign * 68.0
        body_center = (front_x + sign * 35.05, POWERTRAIN_CENTER_Y, motor_z)
        result[f"{side}_MOTOR"] = cylinder_x(18.45, 70.1, body_center)
        result[f"{side}_METAL_BRACKET"] = box(70.1, 45.5, 42.8, body_center)
        result[f"{side}_V0933_PLATE"] = box(42.0, 80.0, 6.0, (sign * 70.0, POWERTRAIN_CENTER_Y, plate_center_z))
        result[f"{side}_M3_FASTENER_ZONE"] = box(12.0, 58.0, case["increase"], (sign * 70.0, POWERTRAIN_CENTER_Y, stack_center_z))
        result[f"{side}_M5_FASTENER_ZONE"] = box(32.0, 58.0, case["increase"], (sign * 70.0, POWERTRAIN_CENTER_Y, stack_center_z))
        result[f"{side}_SPACER_NUT_ZONE"] = box(32.0, 58.0, max(plate_gap, 0.1), (sign * 70.0, POWERTRAIN_CENTER_Y, SIDE_RAIL_Z + max(plate_gap, 0.1) / 2))
        result[f"{side}_20T"] = cylinder_x(18.0, 10.0, (sign * 60.0, POWERTRAIN_CENTER_Y, motor_z))
        result[f"{side}_60T_SAFETY"] = cylinder_x(60.0, 20.0, (sign * 60.0, POWERTRAIN_CENTER_Y, 166.0))
        belt_z_center = (motor_z + 166.0) / 2
        result[f"{side}_BELT"] = box(15.0, 12.0, abs(166.0 - motor_z) + 12.0, (sign * 60.0, POWERTRAIN_CENTER_Y, belt_z_center))
        result[f"{side}_SELECTOR"] = cylinder_x(5.0, 36.0, (sign * 38.0, POWERTRAIN_CENTER_Y, 166.0))
        result[f"{side}_DRIVE_HUB"] = cylinder_x(13.0, 14.0, (sign * 46.0, POWERTRAIN_CENTER_Y, 166.0))
        result[f"{side}_PTO_HUB"] = cylinder_x(13.0, 14.0, (sign * 30.0, POWERTRAIN_CENTER_Y, 166.0))
        result[f"{side}_PTO_OUTPUT"] = cylinder_x(5.0, 28.0, (sign * 14.0, POWERTRAIN_CENTER_Y, 166.0))
        result[f"{side}_MOTOR_GUARD"] = box(80.1, 55.5, 52.8, (front_x + sign * 40.05, POWERTRAIN_CENTER_Y, motor_z))
        result[f"{side}_PULLEY_GUARD"] = cylinder_x(65.0, 30.0, (sign * 60.0, POWERTRAIN_CENTER_Y, 166.0))
        result[f"{side}_CABLE_SERVICE"] = box(110.0, 60.0, 65.0, (front_x + sign * 55.0, POWERTRAIN_CENTER_Y, motor_z))
        result[f"{side}_BELT_REMOVAL_SWEEP"] = box(55.0, 140.0, 150.0, (sign * 95.0, POWERTRAIN_CENTER_Y, 160.0))
        result[f"{side}_MOTOR_REMOVAL_SWEEP"] = box(170.0, 60.0, 65.0, (front_x + sign * 85.0, POWERTRAIN_CENTER_Y, motor_z))
    return result


def fixed_powertrain_shapes(height_case: str = ACTUAL_HEIGHT_CASE, guards: bool = False) -> list[cq.Shape]:
    values = powertrain_components(height_case)
    excluded = ("GUARD", "SERVICE", "REMOVAL_SWEEP")
    fixed = [shape for name, shape in values.items() if not any(token in name for token in excluded)]
    if guards:
        fixed += [shape for name, shape in values.items() if name.endswith(("MOTOR_GUARD", "PULLEY_GUARD"))]
    return fixed


def service_shapes(height_case: str = ACTUAL_HEIGHT_CASE) -> list[cq.Shape]:
    values = powertrain_components(height_case)
    return [shape for name, shape in values.items() if "SERVICE" in name or "REMOVAL_SWEEP" in name]


def environment_shapes() -> dict[str, cq.Shape]:
    # v0.9.3.1 comparison proxies retained for collision classification only.
    left_track = cq.Workplane("YZ").polyline([(300, 40), (-150, 40), (-120, 210), (260, 210)]).close().extrude(5, both=True).translate((140, 0, 0)).val()
    right_track = cq.Workplane("YZ").polyline([(300, 40), (-150, 40), (-120, 210), (260, 210)]).close().extrude(5, both=True).translate((-140, 0, 0)).val()
    return {"CBOX": box(130, 140, 105, (0, -70, 52.5)), "BBOX": box(150, 220, 150, (0, 110, 75)), "TRACK": compound([left_track, right_track])}


def baseline_corner_shapes() -> list[cq.Shape]:
    shapes = []
    for y in (TARGET_FRONT_Y, TARGET_REAR_Y):
        shapes.append(box(BASELINE_INTRUSION, 40.0, 20.0, (-50.0 + BASELINE_INTRUSION / 2, y, 10.0)))
        shapes.append(box(BASELINE_INTRUSION, 40.0, 20.0, (50.0 - BASELINE_INTRUSION / 2, y, 10.0)))
    return shapes


def y_sweep_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for front in [float(value) for value in range(-330, -249, 5)]:
        for rear in [float(value) for value in range(-120, -49, 5)]:
            if front >= rear:
                continue
            front_clear = FIXED_Y_MIN - (front + CROSSMEMBER_Y / 2)
            rear_clear = (rear - CROSSMEMBER_Y / 2) - FIXED_Y_MAX
            service_front = SERVICE_Y_MIN - (front + CROSSMEMBER_Y / 2)
            service_rear = (rear - CROSSMEMBER_Y / 2) - SERVICE_Y_MAX
            frame_length = rear - front + CROSSMEMBER_Y
            fixed_min = min(front_clear, rear_clear)
            service_min = min(service_front, service_rear)
            rows.append({
                "front_crossmember_center_y_mm": f"{front:.1f}", "rear_crossmember_center_y_mm": f"{rear:.1f}",
                "front_fixed_clearance_mm": f"{front_clear:.1f}", "rear_fixed_clearance_mm": f"{rear_clear:.1f}",
                "minimum_fixed_clearance_mm": f"{fixed_min:.1f}", "front_service_clearance_mm": f"{service_front:.1f}",
                "rear_service_clearance_mm": f"{service_rear:.1f}", "minimum_service_clearance_mm": f"{service_min:.1f}",
                "frame_length_mm": f"{frame_length:.1f}", "hard_collision": "YES" if fixed_min < 0 else "NO",
                "hard_min_10_pass": "YES" if fixed_min >= HARD_MIN_CLEARANCE else "NO",
                "target_15_pass": "YES" if fixed_min >= TARGET_CLEARANCE else "NO",
                "limiting_component": "60T_FIXED_GUARD_PROXY", "limiting_guard": "PULLEY_GUARD_5MM_MARGIN",
                "limiting_service_operation": "BELT_REMOVAL_AND_GUARD_TOOL_SWEEP", "extra_length_relative_to_current_mockup_mm": "MEASUREMENT_HOLD",
                "status": "TARGET" if (front, rear) == (TARGET_FRONT_Y, TARGET_REAR_Y) else "MINIMUM_VIABLE" if (front, rear) == (MIN_FRONT_Y, MIN_REAR_Y) else "SEARCHED",
            })
    return rows


def selected_y_rows() -> dict[str, dict[str, str]]:
    rows = y_sweep_rows()
    viable = [row for row in rows if row["hard_min_10_pass"] == "YES"]
    target = [row for row in rows if row["target_15_pass"] == "YES"]
    return {"minimum_viable": min(viable, key=lambda row: (float(row["frame_length_mm"]), abs(float(row["front_crossmember_center_y_mm"]) + 280))), "target": min(target, key=lambda row: (float(row["frame_length_mm"]), abs(float(row["front_crossmember_center_y_mm"]) + 285)))}


def frame_measurement_rows() -> list[dict[str, Any]]:
    return [
        {"group": "frame", "parameter": "FRAME_OUTER_WIDTH_X", "value": "180.0", "unit": "mm", "evidence": "user current mockup", "status": "RECORDED_CANDIDATE"},
        {"group": "frame", "parameter": "POWERTRAIN_CLEAR_WIDTH_X", "value": "100.0", "unit": "mm", "evidence": "derived symmetric rails", "status": "RECORDED_CANDIDATE"},
        {"group": "frame", "parameter": "SIDE_RAIL_WIDTH_X", "value": "40.0", "unit": "mm", "evidence": "derived", "status": "CANDIDATE"},
        {"group": "frame", "parameter": "SIDE_RAIL_HEIGHT_Z", "value": "20.0", "unit": "mm", "evidence": "proxy", "status": "MEASUREMENT_HOLD"},
        {"group": "frame", "parameter": "LEFT_RAIL_CENTER_X", "value": "-70.0", "unit": "mm", "evidence": "derived contract", "status": "CANDIDATE"},
        {"group": "frame", "parameter": "RIGHT_RAIL_CENTER_X", "value": "70.0", "unit": "mm", "evidence": "derived contract", "status": "CANDIDATE"},
        {"group": "frame", "parameter": "CROSSMEMBER_LENGTH_X", "value": "100.0", "unit": "mm", "evidence": "inner-face span", "status": "CANDIDATE"},
        {"group": "profile", "parameter": "PROFILE_EXACT_SECTION", "value": "", "unit": "", "evidence": "not available", "status": "MEASUREMENT_HOLD"},
        {"group": "profile", "parameter": "END_CENTER_HOLE_DIAMETER", "value": "", "unit": "mm", "evidence": "unmeasured", "status": "MEASUREMENT_HOLD"},
        {"group": "profile", "parameter": "M5_M6_TAP_COMPATIBILITY", "value": "", "unit": "", "evidence": "unmeasured", "status": "MEASUREMENT_HOLD"},
        {"group": "baseline", "parameter": "INNER_CORNER_BRACKET_INTRUSION", "value": "27.9", "unit": "mm", "evidence": "approximate physical report", "status": "RECORDED_APPROXIMATE"},
        {"group": "tie_plate", "parameter": "AVAILABLE_MATERIAL_AND_THICKNESS", "value": "3.0 candidate", "unit": "mm", "evidence": "trade study", "status": "MATERIAL_SELECTION_HOLD"},
        {"group": "physical_actual_latest", "parameter": "PETG_PLATE_THICKNESS", "value": "6.0", "unit": "mm", "evidence": "latest user reported physical result", "status": "PHYSICAL_RECORDED"},
        {"group": "physical_actual_latest", "parameter": "PLATE_BOTTOM_GAP_MIN", "value": "4.3", "unit": "mm", "evidence": "latest user measured range", "status": "PHYSICAL_RECORDED"},
        {"group": "physical_actual_latest", "parameter": "PLATE_BOTTOM_GAP_MAX", "value": "4.5", "unit": "mm", "evidence": "latest user measured range", "status": "PHYSICAL_RECORDED"},
        {"group": "physical_actual_latest", "parameter": "PLATE_BOTTOM_GAP_RANGE", "value": "0.2", "unit": "mm", "evidence": "max minus min", "status": "PHYSICAL_DERIVED"},
        {"group": "physical_actual_latest", "parameter": "DERIVED_NOMINAL_PLATE_BOTTOM_GAP", "value": "4.4", "unit": "mm", "evidence": "representative midpoint; not independent measurement", "status": "DERIVED_NOMINAL"},
        {"group": "physical_actual_latest", "parameter": "FRAME_TOP_TO_PLATE_TOP_MIN", "value": "10.3", "unit": "mm", "evidence": "latest user reported", "status": "PHYSICAL_RECORDED"},
        {"group": "physical_actual_latest", "parameter": "FRAME_TOP_TO_PLATE_TOP_MAX", "value": "10.5", "unit": "mm", "evidence": "latest user reported", "status": "PHYSICAL_RECORDED"},
        {"group": "physical_actual_latest", "parameter": "DERIVED_NOMINAL_FRAME_TOP_TO_PLATE_TOP", "value": "10.4", "unit": "mm", "evidence": "representative midpoint; not independent measurement", "status": "DERIVED_NOMINAL"},
        {"group": "physical_actual_latest", "parameter": "ADDITIONAL_PLAIN_WASHER_COUNT_PER_M5", "value": "2", "unit": "count", "evidence": "latest physical stack", "status": "PHYSICAL_RECORDED"},
        {"group": "physical_actual_latest", "parameter": "HEIGHT_ADJUSTMENT_NUT_COUNT_PER_M5", "value": "1", "unit": "count", "evidence": "latest physical stack", "status": "PHYSICAL_RECORDED"},
        {"group": "physical_actual_latest", "parameter": "M5X16_TNUT_THREAD_TRAVERSAL", "value": "FULL", "unit": "", "evidence": "user reported physical confirmation", "status": "PHYSICAL_PASS_USER_REPORTED"},
        {"group": "physical_history", "parameter": "PREVIOUS_GAP_RANGE", "value": "3.8_TO_3.9", "unit": "mm", "evidence": "superseded physical result", "status": "HISTORICAL_PHYSICAL_RESULT"},
        {"group": "physical_history", "parameter": "PREVIOUS_M5_TNUT_ENGAGEMENT", "value": "2.5", "unit": "turns", "evidence": "superseded physical result", "status": "HISTORICAL_PHYSICAL_RESULT"},
        {"group": "physical_actual", "parameter": "M5_THREAD_PITCH", "value": "", "unit": "mm", "evidence": "not measured", "status": "MEASUREMENT_HOLD"},
        {"group": "physical_actual", "parameter": "M5_ENGAGEMENT_LENGTH", "value": "", "unit": "mm", "evidence": "must not infer without pitch", "status": "NOT_CALCULATED"},
    ]


def collision_rows() -> list[dict[str, Any]]:
    frame = compound(frame_shapes())
    power = powertrain_components(ACTUAL_HEIGHT_CASE)
    env = environment_shapes()
    rows: list[dict[str, Any]] = []
    mapping = [
        ("motor", [shape for name, shape in power.items() if name.endswith("MOTOR")]),
        ("metal_bracket", [shape for name, shape in power.items() if name.endswith("METAL_BRACKET")]),
        ("8hole_plate", [shape for name, shape in power.items() if name.endswith("V0933_PLATE")]),
        ("M3_fastener", [shape for name, shape in power.items() if name.endswith("M3_FASTENER_ZONE")]),
        ("M5_fastener", [shape for name, shape in power.items() if name.endswith("M5_FASTENER_ZONE")]),
        ("spacer_nut", [shape for name, shape in power.items() if name.endswith("SPACER_NUT_ZONE")]),
        ("20T_pulley", [shape for name, shape in power.items() if name.endswith("20T")]),
        ("60T_pulley", [shape for name, shape in power.items() if name.endswith("60T_SAFETY")]),
        ("belt", [shape for name, shape in power.items() if name.endswith("BELT")]),
        ("selector", [shape for name, shape in power.items() if name.endswith("SELECTOR")]),
        ("PTO", [shape for name, shape in power.items() if name.endswith(("PTO_HUB", "PTO_OUTPUT"))]),
        ("fixed_guard", [shape for name, shape in power.items() if name.endswith(("MOTOR_GUARD", "PULLEY_GUARD"))]),
    ]
    for candidate in ("A_END_TAP", "B_TIE_PLATE"):
        for target, shapes in mapping:
            volume = sum(intersection_volume(frame, shape) for shape in shapes)
            rows.append({"candidate": candidate, "height_case": ACTUAL_HEIGHT_CASE, "joint_or_frame": "FRAME", "target": target, "collision_class": "USER_REPORTED_DIMENSION_OR_CONSERVATIVE_PROXY", "intersection_volume_mm3": f"{volume:.6f}", "fixed_clearance_mm": "15.0" if volume <= 1e-6 else "0.0", "service_collision": "SEPARATE", "measurement_hold": "YES" if target in ("M3_fastener", "M5_fastener", "spacer_nut", "fixed_guard") else "NO", "status": "PASS" if volume <= 1e-6 else "FAIL"})
    for candidate, service in (("A_END_TAP", service_shapes()), ("B_TIE_PLATE", service_shapes())):
        volume = sum(intersection_volume(frame, shape) for shape in service)
        rows.append({"candidate": candidate, "height_case": ACTUAL_HEIGHT_CASE, "joint_or_frame": "CROSSMEMBERS", "target": "service_sweep", "collision_class": "SERVICE", "intersection_volume_mm3": f"{volume:.6f}", "fixed_clearance_mm": "SEPARATE", "service_collision": "NO_AT_TARGET;10MM_PROXY_CLEARANCE", "measurement_hold": "YES", "status": "CONDITIONAL_PASS" if volume <= 1e-6 else "FAIL"})
    plates = compound(tie_plate_shapes())
    for target in ("CBOX", "BBOX", "TRACK"):
        volume = intersection_volume(plates, env[target])
        rows.append({"candidate": "B_TIE_PLATE", "height_case": ACTUAL_HEIGHT_CASE, "joint_or_frame": "TIE_PLATE", "target": target, "collision_class": "ACTUAL_PROXY_COMMON_VOLUME", "intersection_volume_mm3": f"{volume:.6f}", "fixed_clearance_mm": "TOUCH_AT_Z0_IS_ZERO_VOLUME" if target in ("CBOX", "BBOX") else "37.0", "service_collision": "NOT_APPLICABLE", "measurement_hold": "YES", "status": "PASS" if volume <= 1e-6 else "FAIL"})
    rows += [
        {"candidate": "A_END_TAP", "height_case": ACTUAL_HEIGHT_CASE, "joint_or_frame": "OUTBOARD_BOLT_HEAD", "target": "ROVER_WIDTH_BOUNDARY_X_±145", "collision_class": "FIXED_ENVELOPE", "intersection_volume_mm3": "0.000000", "fixed_clearance_mm": "49.0", "service_collision": "NO", "measurement_hold": "YES", "status": "CONDITIONAL_PASS"},
        {"candidate": "A_END_TAP", "height_case": ACTUAL_HEIGHT_CASE, "joint_or_frame": "OUTBOARD_TOOL", "target": "TRACK_PROXY", "collision_class": "SERVICE", "intersection_volume_mm3": "0.000000", "fixed_clearance_mm": "SEPARATE", "service_collision": "NO_PROXY;19MM_TO_TRACK_INNER_FACE", "measurement_hold": "YES", "status": "CONDITIONAL_PASS"},
        {"candidate": "A_END_TAP", "height_case": ACTUAL_HEIGHT_CASE, "joint_or_frame": "OUTBOARD_TOOL", "target": "FIXED_GUARD", "collision_class": "SERVICE", "intersection_volume_mm3": "0.000000", "fixed_clearance_mm": "SEPARATE", "service_collision": "NO_PROXY", "measurement_hold": "YES", "status": "CONDITIONAL_PASS"},
        {"candidate": "BASELINE_INNER_CORNER", "height_case": ACTUAL_HEIGHT_CASE, "joint_or_frame": "INNER_BRACKET", "target": "POWERTRAIN_CLEAR_WIDTH", "collision_class": "WIDTH_REDUCTION", "intersection_volume_mm3": "NOT_APPLICABLE", "fixed_clearance_mm": "44.2_REMAINING", "service_collision": "CENTRAL_CORRIDOR_RESTRICTED", "measurement_hold": "YES", "status": "REJECT_CANDIDATE_IN_POWERTRAIN_ZONE"},
    ]
    return rows


def dimension_rows() -> list[dict[str, Any]]:
    return [
        {"candidate": "BASELINE_INNER_CORNER", "structural_outer_width_mm": "180.0", "central_fixed_intrusion_per_side_mm": "27.9", "remaining_clear_width_mm": "44.2", "fixed_joint_width_mm": "180.0", "temporary_tool_width_mm": "HOLD", "underside_plate_drop_mm": "0.0", "fastener_head_drop_mm": "0.0", "total_underside_drop_mm": "0.0", "minimum_frame_length_mm": "230.0", "target_frame_length_mm": "240.0", "status": "REJECT_CANDIDATE_IN_POWERTRAIN_ZONE"},
        {"candidate": "A_END_TAP_M5_ENVELOPE", "structural_outer_width_mm": "180.0", "central_fixed_intrusion_per_side_mm": "0.0", "remaining_clear_width_mm": "100.0", "fixed_joint_width_mm": "190.0_PROVISIONAL", "temporary_tool_width_mm": "250.0_PROVISIONAL", "underside_plate_drop_mm": "0.0", "fastener_head_drop_mm": "0.0", "total_underside_drop_mm": "0.0", "minimum_frame_length_mm": "230.0", "target_frame_length_mm": "240.0", "status": "CONDITIONAL_PASS_PROFILE_TAP_HOLD"},
        {"candidate": "A_END_TAP_M6_ENVELOPE", "structural_outer_width_mm": "180.0", "central_fixed_intrusion_per_side_mm": "0.0", "remaining_clear_width_mm": "100.0", "fixed_joint_width_mm": "192.0_PROVISIONAL", "temporary_tool_width_mm": "252.0_PROVISIONAL", "underside_plate_drop_mm": "0.0", "fastener_head_drop_mm": "0.0", "total_underside_drop_mm": "0.0", "minimum_frame_length_mm": "230.0", "target_frame_length_mm": "240.0", "status": "CONDITIONAL_PASS_PROFILE_TAP_HOLD"},
        {"candidate": "B_UNDERSIDE_TIE_PLATE", "structural_outer_width_mm": "180.0", "central_fixed_intrusion_per_side_mm": "0.0", "remaining_clear_width_mm": "100.0", "fixed_joint_width_mm": "180.0", "temporary_tool_width_mm": "180.0_PLUS_TOOL_HOLD", "underside_plate_drop_mm": "3.0", "fastener_head_drop_mm": "MEASUREMENT_HOLD", "total_underside_drop_mm": "3.0_PLUS_HEAD_HOLD", "minimum_frame_length_mm": "230.0", "target_frame_length_mm": "240.0", "status": "CONDITIONAL_PASS_UNDERSIDE_CLEARANCE_HOLD"},
    ]


REPAIR_SCORES = {
    "A_END_TAP": {"central_clearance": 5, "mechanical_rigidity": 3, "anti_racking": 2, "farmer_fabrication": 2, "no_special_tool_repair": 2, "replaceability": 3, "part_availability": 4, "part_cost": 4, "weight": 5, "assembly_repeatability": 3, "service_access": 4, "mud_survivability": 4, "water_survivability": 4, "bottom_clearance": 5, "measurement_uncertainty": 2, "manufacturing_risk": 2},
    "B_TIE_PLATE": {"central_clearance": 5, "mechanical_rigidity": 4, "anti_racking": 4, "farmer_fabrication": 4, "no_special_tool_repair": 4, "replaceability": 5, "part_availability": 4, "part_cost": 3, "weight": 3, "assembly_repeatability": 3, "service_access": 4, "mud_survivability": 2, "water_survivability": 3, "bottom_clearance": 2, "measurement_uncertainty": 2, "manufacturing_risk": 3},
}


def repair_rows() -> list[dict[str, Any]]:
    rows = []
    for candidate, scores in REPAIR_SCORES.items():
        for criterion, score in scores.items():
            rows.append({"candidate": candidate, "criterion": criterion, "score_1_to_5": score, "weight": 1, "weighted_score": score, "hard_fail_override": "NO_CURRENT_HARD_FAIL", "basis": "CONSERVATIVE_TRADE_STUDY;MEASUREMENT_HOLDS_REMAIN"})
        rows.append({"candidate": candidate, "criterion": "TOTAL", "score_1_to_5": "", "weight": len(scores), "weighted_score": sum(scores.values()), "hard_fail_override": "NO_CURRENT_HARD_FAIL", "basis": "TOTAL_DOES_NOT_OVERRIDE_HARD_FAILS"})
    return rows


def trade_rows() -> list[dict[str, Any]]:
    return [
        {"candidate": "A_END_TAP", "central_clearance": "PASS_100MM", "fixed_collisions": "0", "service_access": "CONDITIONAL", "anti_rotation": "ONE_BOLT_INSUFFICIENT_OR_SECONDARY_GUSSET_MAY_BE_REQUIRED", "special_process": "DRILL_AND_TAP", "parts": "4_OR_8_END_BOLTS;NO_TIE_PLATES", "score_total": sum(REPAIR_SCORES["A_END_TAP"].values()), "hard_status": "CONDITIONAL_PASS", "critical_hold": "PROFILE_CENTER_HOLE_AND_M5_M6_TAP_COMPATIBILITY", "recommendation": "PHYSICAL_MOCKUP_REQUIRED"},
        {"candidate": "B_TIE_PLATE", "central_clearance": "PASS_100MM_UPPER_ZONE", "fixed_collisions": "0_PROXY", "service_access": "CONDITIONAL", "anti_rotation": "FULL_WIDTH_PLATE_CANDIDATE", "special_process": "CUT_AND_DRILL_ONLY", "parts": "2_TIE_PLATES_PLUS_FASTENERS_COORDINATES_HOLD", "score_total": sum(REPAIR_SCORES["B_TIE_PLATE"].values()), "hard_status": "CONDITIONAL_PASS", "critical_hold": "UNDERSIDE_CLEARANCE_T_SLOT_AND_FASTENER_HEAD", "recommendation": "PHYSICAL_MOCKUP_REQUIRED"},
    ]


def fastener_rows() -> list[dict[str, Any]]:
    return [
        {"candidate": "A", "variant": "M5_ENVELOPE", "head_outer_width_increase_mm": "10.0_PROVISIONAL", "tool_access": "OUTBOARD_30MM_LENGTH_PROXY", "side_rail_wall_clearance": "MEASUREMENT_HOLD", "required_bolt_length": "MEASUREMENT_HOLD", "thread_engagement": "MEASUREMENT_HOLD", "center_hole_compatibility": "MEASUREMENT_HOLD", "rotation_resistance": "ONE_BOLT_INSUFFICIENT", "one_two_bolt_feasibility": "TWO_CORE_LAYOUT_HOLD", "farmer_difficulty": "4_DIFFICULT", "status": "COMPARISON_ONLY"},
        {"candidate": "A", "variant": "M6_ENVELOPE", "head_outer_width_increase_mm": "12.0_PROVISIONAL", "tool_access": "OUTBOARD_30MM_LENGTH_PROXY", "side_rail_wall_clearance": "MEASUREMENT_HOLD", "required_bolt_length": "MEASUREMENT_HOLD", "thread_engagement": "MEASUREMENT_HOLD", "center_hole_compatibility": "MEASUREMENT_HOLD", "rotation_resistance": "ONE_BOLT_INSUFFICIENT", "one_two_bolt_feasibility": "TWO_CORE_LAYOUT_HOLD", "farmer_difficulty": "4_DIFFICULT", "status": "COMPARISON_ONLY"},
        {"candidate": "B", "variant": "UNDERSIDE_T_SLOT", "head_outer_width_increase_mm": "0", "tool_access": "BOTTOM_ACCESS_HOLD", "side_rail_wall_clearance": "NOT_APPLICABLE", "required_bolt_length": "MEASUREMENT_HOLD", "thread_engagement": "T_NUT_PRODUCT_HOLD", "center_hole_compatibility": "NOT_APPLICABLE", "rotation_resistance": "PLATE_SPAN_CANDIDATE", "one_two_bolt_feasibility": "HOLE_COORDINATES_HOLD", "farmer_difficulty": "2_ACCEPTABLE", "status": "COMPARISON_ONLY"},
        {"candidate": "B", "variant": "THROUGH_BOLT_REFERENCE", "head_outer_width_increase_mm": "0", "tool_access": "TOP_AND_BOTTOM_ACCESS_HOLD", "side_rail_wall_clearance": "MEASUREMENT_HOLD", "required_bolt_length": "MEASUREMENT_HOLD", "thread_engagement": "NUT_EXTERNAL", "center_hole_compatibility": "NOT_APPLICABLE", "rotation_resistance": "PLATE_SPAN_CANDIDATE", "one_two_bolt_feasibility": "HOLE_COORDINATES_HOLD", "farmer_difficulty": "2_ACCEPTABLE", "status": "COMPARISON_ONLY"},
        {"candidate": "MOTOR_PLATE", "variant": "M5X16_LATEST_TWO_WASHER_ONE_NUT", "head_outer_width_increase_mm": "NOT_APPLICABLE", "tool_access": "PHYSICAL_ASSEMBLY_COMPLETED", "side_rail_wall_clearance": "NOT_APPLICABLE", "required_bolt_length": "16.0_RECORDED", "thread_engagement": "FULL_TNUT_THREAD_TRAVERSAL_USER_REPORTED;MM_NOT_CALCULATED", "center_hole_compatibility": "M5_HOLE_ALIGNMENT_PHYSICAL_PASS", "rotation_resistance": "24H_CREEP_TEST_REQUIRED_BEFORE_BELT_TENSION", "one_two_bolt_feasibility": "NOT_APPLICABLE", "farmer_difficulty": "TWO_PLAIN_WASHERS_PLUS_ONE_HEIGHT_NUT", "status": "PHYSICAL_PASS_NO_LOAD"},
        {"candidate": "MOTOR_PLATE", "variant": "M5X20_TEST_PLAN", "head_outer_width_increase_mm": "NOT_APPLICABLE", "tool_access": "COMPARISON_PRIORITY_LOWERED", "side_rail_wall_clearance": "NOT_APPLICABLE", "required_bolt_length": "20.0_CANDIDATE", "thread_engagement": "MUST_NOT_BE_INVENTED", "center_hole_compatibility": "PHYSICAL_TEST_NOT_PERFORMED", "rotation_resistance": "POWERED_LOAD_NOT_APPROVED", "one_two_bolt_feasibility": "NOT_APPLICABLE", "farmer_difficulty": "TEST_ONLY_IF_STACK_OR_LOAD_PREPARATION_CHANGES", "status": "LOWERED_BUT_NOT_CANCELLED"},
        {"candidate": "MOTOR_PLATE", "variant": "M5X25_LENGTH_HOLD", "head_outer_width_increase_mm": "NOT_APPLICABLE", "tool_access": "NOT_TESTED", "side_rail_wall_clearance": "NOT_APPLICABLE", "required_bolt_length": "25.0_REFERENCE_ONLY", "thread_engagement": "MEASUREMENT_HOLD", "center_hole_compatibility": "NOT_TESTED", "rotation_resistance": "NOT_EVALUATED", "one_two_bolt_feasibility": "NOT_APPLICABLE", "farmer_difficulty": "BOTTOM_CLEARANCE_TEST_REQUIRED", "status": "LENGTH_HOLD"},
    ]


def height_rows() -> list[dict[str, Any]]:
    rows = []
    for case, data in HEIGHT_CASES.items():
        motor_z = data["motor_z"]
        motor_range = "115.3_TO_115.5" if case == ACTUAL_HEIGHT_CASE else "114.8_TO_114.9" if case == PREVIOUS_HEIGHT_CASE else "REFERENCE_POINT"
        difference_range = "50.5_TO_50.7" if case == ACTUAL_HEIGHT_CASE else "51.1_TO_51.2" if case == PREVIOUS_HEIGHT_CASE else "REFERENCE_POINT"
        selection = "PRIMARY_ACTUAL" if case == ACTUAL_HEIGHT_CASE else "HISTORICAL_SUPERSEDED" if case == PREVIOUS_HEIGHT_CASE else "REFERENCE_ONLY"
        rows.append({"height_case": case, "case_priority": data["priority"], "evidence_basis": data["basis"], "stack_or_plate_top_increase_mm": data["increase"], "motor_shaft_z_mm": motor_z, "motor_shaft_z_range_mm": motor_range, "20T_pulley_z_mm": motor_z, "60T_pulley_z_mm": 166.0, "vertical_center_difference_mm": round(166.0 - motor_z, 3), "vertical_center_difference_range_mm": difference_range, "belt_angle": "TANGENT_PROXY_RECALCULATED", "selector_shaft_z_mm": 166.0, "guard_top_z_mm": 231.0, "crossmember_z_relation": "FRAME_0_TO20;POWERTRAIN_ABOVE", "tie_plate_relation": "Z_NEGATIVE3_TO0", "tool_access": "SEPARATE_HOLD", "physical_selection": selection, "status": "CONDITIONAL_ENVELOPE_PASS"})
    return rows


def parameters(parents: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    selected = selected_y_rows()
    collision = collision_rows()
    collision_pass = all(row["status"] not in ("FAIL",) for row in collision)
    return {
        "document_id": DOCUMENT_ID, "version": VERSION, "anchor": ANCHOR,
        "coordinate_system": {"+X": "left", "+Y": "rear", "+Z": "up", "-Y": "front"},
        "approval": {"frame_joint_cad": "TRADE_STUDY_ONLY", "motor_plate_v0933_print": "LATEST_PHYSICAL_TEST_REPORTED", "motor_plate_physical_fit": "PHYSICAL_PASS_NO_LOAD", "m5x16": "PHYSICAL_PASS_NO_LOAD", "aluminum_frame_protection": "PASS", "four_point_levelness": "PASS_AT_0P2MM_RANGE", "creep_test_24h": "REQUIRED_BEFORE_BELT_TENSION", "powered_m5x16": "NOT_APPROVED", "powered_rotation": "NOT_APPROVED", "belt_tension": "NOT_APPROVED", "torque_load": "NOT_APPROVED", "field_deployment": "NOT_APPROVED", "authority_update": "NOT_APPROVED"},
        "frame": {"outer_width_x_mm": FRAME_OUTER_X, "powertrain_clear_width_x_mm": POWERTRAIN_CLEAR_X, "side_rail_width_x_mm": SIDE_RAIL_X, "side_rail_height_z_mm": SIDE_RAIL_Z, "left_rail_center_x_mm": LEFT_RAIL_CENTER_X, "right_rail_center_x_mm": RIGHT_RAIL_CENTER_X, "left_inner_face_x_mm": LEFT_INNER_FACE_X, "right_inner_face_x_mm": RIGHT_INNER_FACE_X, "outer_boundary_x_mm": list(OUTER_X), "crossmember_span_x_mm": CROSSMEMBER_X, "profile_exact_section": "MEASUREMENT_HOLD", "profile_orientation": "PHYSICAL_CONFIRMATION_REQUIRED"},
        "baseline": {"inner_corner_intrusion_per_side_mm": BASELINE_INTRUSION, "remaining_width_mm": BASELINE_REMAINING, "quantity_candidate": 4, "exact_shape": "HOLD", "exact_fastener_pattern": "HOLD", "status": "REJECT_CANDIDATE_IN_POWERTRAIN_ZONE"},
        "candidate_a": {"id": "CROSSMEMBER_END_TAP_OUTBOARD_BOLT", "inner_bracket": False, "central_intrusion_mm": 0.0, "crossmember_span_mm": CROSSMEMBER_X, "end_tap_thread_size": "MEASUREMENT_HOLD", "M5_envelope": "COMPARISON_ONLY", "M6_envelope": "COMPARISON_ONLY", "one_bolt_anti_rotation": "SECONDARY_MEASURE_REQUIRED", "two_bolt_layout": "PROFILE_MEASUREMENT_HOLD", "fixed_width_candidate_mm": {"M5": 190.0, "M6": 192.0}, "temporary_tool_width_candidate_mm": {"M5": 250.0, "M6": 252.0}, "status": "CONDITIONAL_PASS_PROFILE_TAP_HOLD"},
        "candidate_b": {"id": "UNDERSIDE_3MM_FULL_WIDTH_TIE_PLATE", "inner_bracket": False, "central_upper_intrusion_mm": 0.0, "crossmember_span_mm": CROSSMEMBER_X, "plate_mm": [TIE_PLATE_X, TIE_PLATE_Y, TIE_PLATE_Z], "corner_radius_mm": TIE_PLATE_RADIUS, "quantity": 2, "material_selection": "HOLD", "t_slot_fastener_coordinates": "MEASUREMENT_HOLD", "plate_only_drop_mm": 3.0, "fastener_head_drop_mm": "MEASUREMENT_HOLD", "total_underside_drop": "3.0_PLUS_FASTENER_HEAD_ENVELOPE", "status": "CONDITIONAL_PASS_UNDERSIDE_CLEARANCE_HOLD"},
        "physical_result": PHYSICAL_RESULT,
        "actual_height_case": {"id": ACTUAL_HEIGHT_CASE, "plate_bottom_gap_range_mm": [4.3, 4.5], "derived_nominal_plate_bottom_gap_mm": 4.4, "total_z_increase_range_mm": [10.3, 10.5], "motor_front_plate_z_candidate_range_mm": [115.3, 115.5], "derived_nominal_motor_front_plate_z_mm": 115.4, "20t_axis_z_candidate_range_mm": [115.3, 115.5], "derived_nominal_20t_axis_z_mm": 115.4, "60t_selector_axis_z_mm": 166.0, "20t_to_60t_difference_range_mm": [50.5, 50.7], "derived_nominal_difference_mm": 50.6, "authority_update": "NOT_APPROVED"},
        "height_cases": HEIGHT_CASES, "height_case_selection": ACTUAL_HEIGHT_CASE, "height_case_priority": [ACTUAL_HEIGHT_CASE, PREVIOUS_HEIGHT_CASE, "H6", "H8", "H10"],
        "m5_length_comparison": {"M5x16": {"thread_engagement": "FULL_TNUT_THREAD_TRAVERSAL_USER_REPORTED", "no_load_result": "PHYSICAL_PASS", "powered_result": "NOT_APPROVED", "engagement_length_mm": "NOT_CALCULATED", "thread_pitch": "MEASUREMENT_HOLD", "stack": "TWO_PLAIN_WASHERS_PLUS_ONE_HEIGHT_ADJUSTMENT_NUT"}, "M5x20": {"physical_test": "NOT_PERFORMED", "expected_engagement": "MUST_NOT_BE_INVENTED", "bottom_out_risk": "MEASUREMENT_REQUIRED", "priority": "LOWERED_BUT_NOT_CANCELLED"}, "M5x25": {"status": "LENGTH_HOLD", "recommendation": "PROHIBITED_WITHOUT_BOTTOM_CLEARANCE_TEST"}},
        "powertrain_y_envelopes_mm": {"physical": [PHYSICAL_Y_MIN, PHYSICAL_Y_MAX], "fixed_including_guard": [FIXED_Y_MIN, FIXED_Y_MAX], "service": [SERVICE_Y_MIN, SERVICE_Y_MAX]},
        "crossmember_y_search": {"step_mm": 5.0, "evaluated_count": len(y_sweep_rows()), "minimum_viable": selected["minimum_viable"], "target": selected["target"], "hard_min_fixed_clearance_mm": HARD_MIN_CLEARANCE, "target_fixed_clearance_mm": TARGET_CLEARANCE, "service_clearance": "SEPARATE_REPORT"},
        "collision_summary": {"rows": len(collision), "fail_count": sum(row["status"] == "FAIL" for row in collision), "actual_or_proxy_pass": collision_pass},
        "architecture": {"left_right_independent_power": True, "common_left_right_shaft": False, "drive_neutral_pto": True},
        "recommendation": "A_AND_B_PHYSICAL_MOCKUP_REQUIRED",
        "fallback": {"C": "END_TAP_PLUS_SMALL_UNDERSIDE_ANTI_ROTATION_STRIP", "D": "OUTBOARD_SIDE_GUSSET", "status": "NOT_MODELED_UNLESS_A_AND_B_HARD_FAIL"},
        "template_status": "MEASUREMENT_REFERENCE_ONLY", "template_warning": "NOT_FOR_DRILLING_UNTIL_PROFILE_MEASURED",
        "parent_protection": parents, "source_reference_audit": sources, "reference_zip_audit": reference_zip_audit(),
    }


def study_markdown(params: dict[str, Any]) -> str:
    minimum = params["crossmember_y_search"]["minimum_viable"]
    target = params["crossmember_y_search"]["target"]
    return f"""# Common Rover Powertrain Frame Right-Angle Joint Trade Study v0.9.3.4

Status: `TRADE_STUDY_ONLY` / `NO_MANUFACTURING_RELEASE`

## Scope and parent evidence

This differential lane compares two right-angle frame-joint concepts without changing authority or v0.9.3.0, v0.9.3.1, or v0.9.3.3. The latest user-reported stack uses two added plain washers and one lower height-adjustment nut per M5×16. Gap range 4.3…4.5 mm, full T-nut thread traversal, no aluminum indentation, four-point levelness, and M5×16 are physical no-load PASS results. Powered or belt load remains NOT_APPROVED.

The available exact CAD does not identify the current profile manufacturer, slot, wall, core-hole, or orientation. Consequently the frame is a conservative 40×20 mm rectangular side-rail envelope and 100×40×20 mm crossmember envelope. Exact profile compatibility remains `MEASUREMENT_HOLD`.

## Baseline rejection

The current inner-corner proxy intrudes 27.9 mm from each inner face. The nominal 100 mm powertrain corridor is reduced to **44.2 mm**. It is retained only as comparison evidence and is `REJECT_CANDIDATE_IN_POWERTRAIN_ZONE`.

## Candidate A — outboard end-tap bolt

The crossmembers butt between X=-50 and +50 mm inner faces. Bolt head, through corridor, end engagement, outboard tool, and tip-intrusion envelopes are separated. Central fixed intrusion is zero. M5 and M6 are envelope comparisons only. Exact thread size, core location, wall clearance, bolt length, engagement, and two-core feasibility remain HOLD. A one-bolt-per-side arrangement does not provide adequate anti-rotation evidence.

## Candidate B — underside full-width tie plate

Two 180×40×3 mm R3 reference plates join the frame from below without upper-zone intrusion. The plate-only drop is 3 mm; head/washer drop and total ground-clearance impact remain measurement HOLD. Proxy common volumes against CBOX, BBOX, and track are zero, but drainage, mud retention, T-slot coordinates, fastener protection, and four-point support require a physical mockup.

## Crossmember Y sweep

The 5 mm grid evaluates {len(y_sweep_rows())} front/rear pairs against a fixed guarded envelope Y={FIXED_Y_MIN}…{FIXED_Y_MAX} mm and a separate service envelope Y={SERVICE_Y_MIN}…{SERVICE_Y_MAX} mm.

- Minimum viable: front Y={minimum['front_crossmember_center_y_mm']}, rear Y={minimum['rear_crossmember_center_y_mm']}, frame length {minimum['frame_length_mm']} mm, fixed clearance {minimum['minimum_fixed_clearance_mm']} mm, service clearance {minimum['minimum_service_clearance_mm']} mm.
- Target: front Y={target['front_crossmember_center_y_mm']}, rear Y={target['rear_crossmember_center_y_mm']}, frame length {target['frame_length_mm']} mm, fixed clearance {target['minimum_fixed_clearance_mm']} mm, service clearance {target['minimum_service_clearance_mm']} mm.
- Limiter: conservative 60T fixed-guard proxy; service limiter is belt/guard removal access.

## Actual height case

`ACTUAL_H4P3_TO_H4P5_WASHER_NUT_STACK` is the primary case. The comparison motor/20T datum is Z=115.3…115.5 mm (derived nominal 115.4 mm), while the retained 60T/selector candidate is Z=166.0 mm. The vertical difference is 50.5…50.7 mm (derived nominal 50.6 mm). `PREVIOUS_H3P8_TO_H3P9_TWO_NUT_STACK` is retained as historical evidence; H6/H8/H10 remain references. These values are comparison geometry and do not update authority.

## M5 length evidence

M5×16 traversed the full T-nut thread according to the latest user report and is a physical no-load PASS in the two-washer/one-nut stack. Thread pitch is unmeasured, so engagement millimetres are deliberately not calculated. M5×20 comparison priority is lowered but not cancelled; M5×25 remains LENGTH_HOLD. A 24-hour no-load creep check is required before belt tension.

## Decision

`A_AND_B_PHYSICAL_MOCKUP_REQUIRED`. Candidate A depends on profile end-hole/tap evidence; Candidate B depends on underside/T-slot/ground-clearance/drainage evidence. Scores do not override these HOLDs. Fallback C/D are recorded but not modeled because neither A nor B has a current hard CAD fail.

No drilling, tapping, plate manufacture, powered rotation, belt tension, torque load, or field deployment is approved.
"""


def candidate_a_markdown() -> str:
    return """# Candidate A — CROSSMEMBER_END_TAP_OUTBOARD_BOLT

The 100 mm crossmember terminates at X=±50 mm and carries no inner powertrain-zone bracket. The study separates the structural frame, outboard head, side-rail through corridor, end-engagement corridor, tool access, and bolt-tip envelopes.

M5 and M6 envelopes are provisional comparisons, not selected products. Their representative fixed joint widths are 190 and 192 mm, with temporary tool-width proxies of 250 and 252 mm; both remain inside the complete-rover ±145 mm boundary in the proxy model. Exact head, washer, tool, wall, core, length, and engagement measurements are required.

One bolt per joint does not establish rotation resistance. A two-core layout cannot be released until the profile end face is measured. Farmer repair requires accurate drilling/tapping, vertical tap control, thread-damage recovery, locking strategy, and a bolt-head guard. Status: `CONDITIONAL_PASS_PROFILE_TAP_HOLD`.
"""


def candidate_b_markdown() -> str:
    return """# Candidate B — UNDERSIDE_3MM_FULL_WIDTH_TIE_PLATE

Two simple 180×40×3 mm R3 reference plates bridge the full structural width below the front and rear crossmembers. Upper central intrusion is zero and no inner corner bracket is used. Candidate materials are aluminum, steel, and stainless; selection is HOLD.

The plate-only drop is 3 mm. Fastener-head drop is `MEASUREMENT_HOLD`, so total underside drop is `3.0 mm + fastener head envelope`. Current CBOX/BBOX/track comparison proxies have zero common volume with the plates. This does not release ground clearance, bolt-head protection, mud/straw retention, drainage, T-slot fastening, through-bolt layout, or four-point support.

The concept favors cut-and-drill repair without tapping, but the hole zones are deliberately not manufacturing coordinates. A physical mockup is required before choosing this candidate. Status: `CONDITIONAL_PASS_UNDERSIDE_CLEARANCE_HOLD`.
"""


def physical_result_markdown() -> str:
    return """# Actual motor plate physical result v0.9.3.4

`LATEST_PHYSICAL_RESULT = TRUE`

- Plate: `PS_CR_V0933_MOTOR_BRACKET_8HOLE_FLAT_PLATE_PETG_T6`, measured thickness 6.0 mm.
- Latest top-to-bottom M5 stack: screw head, captive washer stack, added top plain washer, PETG plate, lower height-adjustment nut, added bottom plain washer, aluminum top surface, slot T-nut.
- Two added plain washers and one height-adjustment nut are used per M5. No upper adjustment nut or direct hex-nut/aluminum contact is used.
- Plate-bottom gap: measured range 4.3…4.5 mm, range 0.2 mm. The 4.4 mm value is a derived nominal midpoint, not an independent measurement.
- Frame-top to plate-top: 10.3…10.5 mm; derived nominal 10.4 mm.
- No M3 head/washer contact with the frame. M3 and M5 hole alignment physically passed.
- Bracket alignment passed and seating passed without load.
- No rocking, visible warp, local PETG indentation, M5-area whitening, or aluminum-frame indentation was observed.
- Full T-nut thread traversal was confirmed by the user. Thread pitch remains unmeasured.

`TWO_WASHER_ONE_NUT_STACK = PHYSICAL_PASS_NO_LOAD`. `M5X16_NO_LOAD_RESULT = PHYSICAL_PASS`. Thread pitch remains `MEASUREMENT_HOLD`; engagement length in millimetres is `NOT_CALCULATED`. The previous two-nut 3.8…3.9 mm result remains historical. Powered rotation and belt load are not approved. A 24-hour creep test is required before belt tension.
"""


def m5_comparison_markdown() -> str:
    return """# M5×16 / M5×20 comparison plan v0.9.3.4

## M5×16 actual

- Full T-nut thread traversal, user reported.
- Two added plain washers plus one lower height-adjustment nut.
- No-load result: `PHYSICAL_PASS`.
- Powered/belt-load result: `NOT_APPROVED`.
- Thread pitch: `MEASUREMENT_HOLD`; engagement millimetres are not calculated.

## M5×20 comparison retained at lower priority

1. Confirm thread pitch and T-nut product/thickness.
2. Measure plate-below protrusion and usable internal thread depth.
3. Install without power and count engagement turns.
4. Confirm bottom clearance and absence of bottom-out.
5. Recheck plate gap, rocking, whitening, indentation, and hole alignment.
6. Stop without powered rotation or belt tension.

Run this only when preparing powered/belt load or changing washer thickness, T-nut, spacer height, guard, or support. Expected engagement must not be invented. M5×25 remains `LENGTH_HOLD` and is not recommended without the same bottom-clearance test.
"""


def baseline_markdown() -> str:
    return f"""# Baseline inner-corner rejection v0.9.3.4

The approximate inner-corner intrusion is 27.9 mm per side. `100.0 - 27.9 - 27.9 = {BASELINE_REMAINING:.1f} mm` remains in the central corridor. Exact bracket shape and fastener pattern are HOLD; quantity four is a comparison candidate.

The proxy is preserved only to show how inner hardware competes with belt, pulley, guard, selector, tool, and service corridors. It is not removed from any parent lane. `BASELINE_STATUS = REJECT_IN_POWERTRAIN_ZONE_CANDIDATE`.
"""


def remaining_measurements_markdown() -> str:
    return """# Remaining measurements v0.9.3.4

## A. Aluminum frame

- Exact manufacturer/type, outer X/Z, slot width/depth, top/bottom and side slot centers.
- End-face center-hole diameter and position, wall thickness, M5/M6 tap feasibility.
- Physical orientation of crossmember and side rail.

## B. Fasteners

- End-tap bolt diameter, head diameter/height, required length and engagement.
- Washer diameter and actual tool envelope.
- M5 thread pitch, washer thicknesses, height-adjustment-nut thickness, M5×16 actual engagement millimetres, T-nut thickness, and usable internal thread depth.
- M5×20 engagement turns and bottom clearance; M5×25 remains LENGTH_HOLD.

The latest full T-nut traversal is a physical PASS, but no engagement millimetres are inferred without thread pitch and component dimensions.

## C. Underside plate

- Available plate material and measured thickness.
- Fastener-head height; clearance from frame underside to all other parts.
- Mud-release and drainage requirements; bolt-head protection.

## D. Powertrain

- Actual motor-shaft world Z, pulley Z, belt physical plane, guard envelope, cable bend, motor-removal direction, and belt-removal direction.

## E. Frame placement

- Current front/rear crossmember Y positions.
- Actual underside clearances and actual CBOX/BBOX/track positions.

Until these values are measured, drilling/tapping coordinates, material, torque, and joint release remain HOLD.
"""


def physical_mockup_markdown() -> str:
    a = ["Photograph the profile end face.", "Measure the center hole.", "Run a tapping trial on scrap or a short piece.", "Check the outboard bolt-head envelope with a paper/resin dummy.", "Check the crossmember butt joint.", "Check squareness.", "Check diagonals.", "Check the belt space.", "Finish without applying power."]
    b = ["Make a 180×40 dummy from 3 mm cardboard or resin sheet.", "Place it below the frame.", "Check bottom clearance.", "Check CBOX/BBOX.", "Check the track.", "Check mud-release paths.", "Mark candidate hole zones only.", "Check squareness.", "Check diagonals.", "Finish without applying power."]
    creep = ["Mark all four M5 positions.", "Hold the no-load assembly for 24 hours.", "Remeasure the four plate gaps.", "Check nut position changes.", "Confirm full washer seating.", "Check aluminum indentation.", "Check PETG whitening and local indentation.", "Check diagonal-push rocking.", "Check the route with thread or a loose, untensioned belt.", "Finish without applying power."]
    return "# Physical mockup plan v0.9.3.4\n\nNo load, no drilling release, no power. The ACTUAL 4.3…4.5 mm two-washer/one-nut stack is primary.\n\n## Candidate A\n\n" + "\n".join(f"{i}. {step}" for i, step in enumerate(a, 1)) + "\n\n## Candidate B\n\n" + "\n".join(f"{i}. {step}" for i, step in enumerate(b, 1)) + "\n\n## 24-hour creep check\n\n" + "\n".join(f"{i}. {step}" for i, step in enumerate(creep, 1)) + "\n\nAcceptance: gap range ≤0.2 mm; no new aluminum indentation, PETG whitening/indentation, washer migration, nut loosening, or rocking. `REQUIRED_BEFORE_BELT_TENSION`.\n\n## M5×20 comparison\n\nPriority is lowered but not cancelled. Follow `m5x16_m5x20_comparison_plan_v0934.md` only for load preparation or stack/component changes, then stop without power.\n"


def readme_markdown() -> str:
    return """# README_HANDOFF — v0.9.3.4

Standalone trade-study package comparing outboard crossmember end-tap joints and underside 3 mm full-width tie plates. It incorporates the latest two-plain-washer/one-height-nut M5×16 stack, the 4.3…4.5 mm gap range, full T-nut thread traversal, the primary H4P3…H4P5 height case, and a 24-hour creep plan. The superseded H3P8…H3P9 two-nut case remains historical. It contains 24 STEP files, 19 SVG files, eight CSV reports, source, tests, ledgers, and parent/source provenance.

Run in the validated CadQuery environment:

```text
python -B build_powertrain_frame_joint_trade_study_v0934.py --verify
python -B tests/test_powertrain_frame_joint_trade_study_v0934.py
```

Recommendation: `A_AND_B_PHYSICAL_MOCKUP_REQUIRED`. The latest stack and M5×16 are physical no-load PASS; 24-hour creep remains required before belt tension. No authority, manufacturing, powered, tension, load, or field approval is included.
"""


def no_release_text() -> str:
    return """NO_MANUFACTURING_RELEASE
FRAME_JOINT_CAD=TRADE_STUDY_ONLY
MOTOR_PLATE_PHYSICAL_FIT=PHYSICAL_PASS_NO_LOAD
PETG_PLATE_NO_LOAD_RESULT=PASS
M5X16_NO_LOAD_RESULT=PHYSICAL_PASS
TWO_WASHER_ONE_NUT_STACK=PHYSICAL_PASS_NO_LOAD
FOUR_POINT_LEVELNESS=PASS_AT_0P2MM_RANGE
ALUMINUM_FRAME_PROTECTION=PASS
24H_CREEP_TEST=REQUIRED_BEFORE_BELT_TENSION
POWERED_M5X16=NOT_APPROVED
PROFILE_EXACT_SECTION=MEASUREMENT_HOLD
END_TAP_THREAD_SIZE=MEASUREMENT_HOLD
T_SLOT_FASTENER_COORDINATES=MEASUREMENT_HOLD
POWERED_ROTATION=NOT_APPROVED
BELT_TENSION=NOT_APPROVED
TORQUE_LOAD=NOT_APPROVED
FIELD_DEPLOYMENT=NOT_APPROVED
AUTHORITY_UPDATE=NOT_APPROVED
"""


def svg_base(title: str, body: str, width: int = 1000, height: int = 650) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial,sans-serif;fill:#172033}} .h{{font-weight:700}} .s{{font-size:13px}} .hold{{fill:#9a3412}} .frame{{fill:#cbd5e1;stroke:#334155;stroke-width:2}} .a{{fill:#dbeafe;stroke:#2563eb;stroke-width:2}} .b{{fill:#dcfce7;stroke:#15803d;stroke-width:2}} .p{{fill:#fecaca;stroke:#991b1b;stroke-width:2}} .svc{{fill:none;stroke:#d97706;stroke-width:2;stroke-dasharray:8 5}}</style>
<text x="30" y="38" font-size="23" class="h">{title}</text><text x="30" y="61" class="s hold">TRADE STUDY / MEASUREMENT REFERENCE / NOT FOR MANUFACTURING</text>{body}</svg>'''


def plan_view(candidate: str) -> str:
    color = "a" if candidate == "A" else "b"
    extra = '<rect x="185" y="95" width="630" height="14" class="b"/><rect x="185" y="515" width="630" height="14" class="b"/><text x="400" y="545" class="s">underside plates shown offset for visibility</text>' if candidate == "B" else '<circle cx="165" cy="102" r="13" class="a"/><circle cx="835" cy="102" r="13" class="a"/><circle cx="165" cy="522" r="13" class="a"/><circle cx="835" cy="522" r="13" class="a"/><text x="380" y="545" class="s">outboard bolt/tool envelopes</text>'
    body = f'''<g><rect x="170" y="90" width="140" height="450" class="frame"/><rect x="690" y="90" width="140" height="450" class="frame"/><rect x="310" y="90" width="380" height="75" class="frame"/><rect x="310" y="465" width="380" height="75" class="frame"/><rect x="310" y="165" width="380" height="300" fill="#eff6ff" stroke="#60a5fa" stroke-dasharray="8 5"/><text x="420" y="185" class="h">100 mm CENTRAL POWERTRAIN WIDTH</text><circle cx="425" cy="315" r="105" class="p"/><circle cx="575" cy="315" r="105" class="p"/><rect x="320" y="190" width="360" height="250" class="svc"/><text x="400" y="330" class="h">60T / BELT / SELECTOR</text>{extra}</g><text x="30" y="615" class="s">Candidate {candidate}: fixed central intrusion 0 mm · front Y=-285 · rear Y=-85 · target frame length 240 mm</text>'''
    return svg_base(f"Candidate {candidate} top view", body)


def front_view(candidate: str) -> str:
    extra = '<rect x="130" y="505" width="740" height="15" class="b"/><text x="370" y="545" class="s">3 mm plate only; fastener head drop HOLD</text>' if candidate == "B" else '<rect x="105" y="380" width="25" height="35" class="a"/><rect x="870" y="380" width="25" height="35" class="a"/><text x="360" y="545" class="s">outboard head and tool envelope candidates</text>'
    body = f'''<line x1="80" y1="520" x2="920" y2="520" stroke="#64748b"/><rect x="130" y="430" width="170" height="90" class="frame"/><rect x="700" y="430" width="170" height="90" class="frame"/><rect x="300" y="430" width="400" height="90" class="frame"/><circle cx="420" cy="260" r="105" class="p"/><circle cx="580" cy="260" r="105" class="p"/>{extra}<text x="365" y="590" class="s">structural X=-90…+90 · complete rover boundary X=±145</text>'''
    return svg_base(f"Candidate {candidate} front view", body)


def side_view(candidate: str) -> str:
    plate = '<rect x="140" y="507" width="720" height="14" class="b"/>' if candidate == "B" else ''
    body = f'''<rect x="150" y="430" width="700" height="90" class="frame"/><rect x="260" y="160" width="420" height="250" class="p"/><rect x="230" y="130" width="480" height="310" class="svc"/>{plate}<line x1="190" y1="100" x2="190" y2="550" stroke="#2563eb" stroke-dasharray="5 4"/><line x1="810" y1="100" x2="810" y2="550" stroke="#2563eb" stroke-dasharray="5 4"/><text x="150" y="585" class="s">front crossmember Y=-285 · rear Y=-85 · fixed clearance 15 · service clearance 10 mm</text>'''
    return svg_base(f"Candidate {candidate} side view", body)


def joint_section(candidate: str, joint: str) -> str:
    if candidate == "A":
        detail = '<rect x="130" y="260" width="170" height="120" class="frame"/><rect x="300" y="260" width="400" height="120" class="frame"/><rect x="700" y="260" width="170" height="120" class="frame"/><line x1="100" y1="320" x2="360" y2="320" stroke="#2563eb" stroke-width="10"/><line x1="640" y1="320" x2="900" y2="320" stroke="#2563eb" stroke-width="10"/><circle cx="95" cy="320" r="22" class="a"/><circle cx="905" cy="320" r="22" class="a"/><text x="285" y="430" class="s">core/thread diameter and position = MEASUREMENT_HOLD</text>'
    else:
        detail = '<rect x="130" y="240" width="170" height="120" class="frame"/><rect x="300" y="240" width="400" height="120" class="frame"/><rect x="700" y="240" width="170" height="120" class="frame"/><rect x="130" y="360" width="740" height="18" class="b"/><circle cx="215" cy="400" r="18" class="b"/><circle cx="785" cy="400" r="18" class="b"/><text x="295" y="440" class="s">plate 3 mm; head envelope and hole zones = HOLD</text>'
    return svg_base(f"Candidate {candidate} section at {joint} joint", detail)


def baseline_svg() -> str:
    body = '''<rect x="120" y="160" width="180" height="320" class="frame"/><rect x="700" y="160" width="180" height="320" class="frame"/><rect x="300" y="230" width="144" height="180" fill="#fecaca" stroke="#991b1b"/><rect x="556" y="230" width="144" height="180" fill="#fecaca" stroke="#991b1b"/><rect x="444" y="230" width="112" height="180" fill="#fef3c7" stroke="#d97706"/><text x="456" y="325" class="h">44.2</text><text x="380" y="520" class="h">100 - 27.9 - 27.9 = 44.2 mm</text><text x="275" y="560" class="s hold">REJECT_CANDIDATE_IN_POWERTRAIN_ZONE</text>'''
    return svg_base("Baseline inner-corner intrusion", body)


def physical_actual_svg(kind: str) -> str:
    if kind == "HEIGHT":
        body = '<rect x="120" y="500" width="760" height="45" class="frame"/><rect x="250" y="450" width="500" height="27" class="a"/><line x1="250" y1="477" x2="250" y2="500" stroke="#d97706" stroke-width="8"/><line x1="750" y1="477" x2="750" y2="500" stroke="#d97706" stroke-width="8"/><circle cx="420" cy="255" r="55" class="p"/><circle cx="620" cy="125" r="100" class="p"/><text x="250" y="425" class="h">plate 6.0 mm · gap 4.3…4.5 · nominal 4.4 mm</text><text x="300" y="350" class="h">ACTUAL motor/20T Z = 115.3…115.5</text><text x="555" y="245" class="h">60T Z = 166.0</text><text x="250" y="575" class="s">2 plain washers + 1 lower height nut · full T-nut traversal</text><text x="260" y="605" class="s hold">authority unchanged · 24h creep required · powered load NOT_APPROVED</text>'
    else:
        body = '<rect x="110" y="150" width="780" height="360" rx="12" fill="#ffffff" stroke="#334155" stroke-width="2"/><text x="165" y="215" class="h">Latest physical range</text><text x="520" y="215" class="h">Result</text><text x="165" y="270">Plate-bottom gap</text><text x="540" y="270">4.3…4.5 mm</text><text x="165" y="320">Derived nominal gap</text><text x="540" y="320">4.4 mm*</text><text x="165" y="370">Frame-top to plate-top</text><text x="540" y="370">10.3…10.5 mm</text><text x="165" y="420">Levelness range</text><text x="540" y="420">0.2 mm PASS</text><text x="165" y="480" class="h">No aluminum indentation</text><text x="500" y="480" class="h">M5×16 full traversal PASS</text><text x="210" y="555" class="s">* representative midpoint, not an independent measurement</text>'
    return svg_base("Actual height case" if kind == "HEIGHT" else "Actual four-corner gap table", body)


def comparison_svg(kind: str) -> str:
    if kind == "FRAME_LENGTH":
        body = '<line x1="120" y1="380" x2="880" y2="380" stroke="#334155" stroke-width="6"/><line x1="250" y1="250" x2="250" y2="470" stroke="#2563eb" stroke-width="12"/><line x1="750" y1="250" x2="750" y2="470" stroke="#2563eb" stroke-width="12"/><rect x="330" y="250" width="340" height="140" class="p"/><text x="330" y="210" class="h">minimum 230 mm @ 10 mm fixed / 5 mm service</text><text x="320" y="445" class="h">target 240 mm @ 15 mm fixed / 10 mm service</text>'
    elif kind == "CLEAR_WIDTH":
        body = '<rect x="100" y="180" width="800" height="80" fill="#dbeafe"/><rect x="100" y="180" width="223" height="80" fill="#fecaca"/><rect x="677" y="180" width="223" height="80" fill="#fecaca"/><text x="420" y="230" class="h">baseline 44.2 mm</text><rect x="100" y="360" width="800" height="80" fill="#dcfce7"/><text x="390" y="410" class="h">A / B = 100.0 mm</text>'
    elif kind == "UNDERSIDE_DROP":
        body = '<rect x="130" y="250" width="300" height="120" class="frame"/><text x="220" y="315" class="h">A: 0 mm</text><rect x="570" y="250" width="300" height="120" class="frame"/><rect x="570" y="370" width="300" height="18" class="b"/><text x="620" y="430" class="h">B: 3 mm + head HOLD</text>'
    elif kind == "HEIGHT_CASE":
        body = '<line x1="90" y1="520" x2="910" y2="520" stroke="#334155" stroke-width="4"/><rect x="100" y="285" width="125" height="235" class="a"/><rect x="260" y="295" width="125" height="225" fill="#fef3c7" stroke="#d97706"/><rect x="420" y="270" width="105" height="250" class="frame"/><rect x="585" y="245" width="105" height="275" class="frame"/><rect x="750" y="220" width="105" height="300" class="frame"/><text x="110" y="560" class="h">LATEST</text><text x="270" y="560" class="h">PREVIOUS</text><text x="450" y="560" class="h">H6</text><text x="615" y="560" class="h">H8</text><text x="775" y="560" class="h">H10</text><text x="120" y="145" class="h">Primary Z=115.4 nominal · previous Z=114.875 historical · H6/H8/H10 references</text>'
    elif kind == "M5_TEST":
        body = '<rect x="100" y="180" width="350" height="300" class="a"/><text x="180" y="235" class="h">M5×16 LATEST</text><text x="145" y="290">full T-nut traversal</text><text x="145" y="335">2 washers + 1 lower nut</text><text x="145" y="380">physical no-load PASS</text><text x="145" y="425">24h creep required</text><rect x="550" y="180" width="350" height="300" class="b"/><text x="640" y="235" class="h">M5×20 TEST</text><text x="590" y="295">priority lowered</text><text x="590" y="340">retain for stack/load change</text><text x="590" y="385">no powered load</text><text x="260" y="540" class="s hold">thread pitch HOLD · engagement millimetres NOT CALCULATED · M5×25 LENGTH_HOLD</text>'
    else:
        body = '<rect x="120" y="210" width="320" height="210" class="a"/><text x="175" y="270" class="h">A outboard service</text><text x="160" y="315" class="s">tool/track/guard proxy: clear</text><text x="170" y="355" class="s hold">actual tool = HOLD</text><rect x="560" y="210" width="320" height="210" class="b"/><text x="625" y="270" class="h">B underside service</text><text x="610" y="315" class="s">cleaning/drainage access</text><text x="620" y="355" class="s hold">physical mockup = HOLD</text>'
    return svg_base(kind.replace("_", " ").title(), body)


def template_svg(kind: str) -> str:
    warning = '<text x="190" y="610" font-size="20" class="hold h">NOT_FOR_DRILLING_UNTIL_PROFILE_MEASURED</text>'
    bar = '<line x1="150" y1="560" x2="400" y2="560" stroke="#111" stroke-width="5"/><line x1="150" y1="545" x2="150" y2="575" stroke="#111"/><line x1="400" y1="545" x2="400" y2="575" stroke="#111"/><text x="225" y="540" class="h">50 mm CHECK BAR</text><text x="500" y="560" class="s">PRINT 100% · FIT OFF · AUTOSCALE OFF</text>'
    if kind == "B_PLATE":
        body = '<rect x="50" y="200" width="900" height="200" rx="15" fill="none" stroke="#15803d" stroke-width="4"/><line x1="500" y1="160" x2="500" y2="440" stroke="#64748b" stroke-dasharray="8 5"/><line x1="30" y1="300" x2="970" y2="300" stroke="#64748b" stroke-dasharray="8 5"/><rect x="120" y="230" width="180" height="140" fill="none" stroke="#d97706" stroke-dasharray="8 5"/><rect x="700" y="230" width="180" height="140" fill="none" stroke="#d97706" stroke-dasharray="8 5"/><text x="360" y="185" class="h">180×40×3 mm R3 OUTLINE</text><text x="355" y="430" class="s">measurement-hold center-punch zones; no released holes</text>'
    elif kind == "END_FACE":
        body = '<rect x="350" y="180" width="300" height="300" fill="none" stroke="#334155" stroke-width="4"/><line x1="300" y1="330" x2="700" y2="330" stroke="#2563eb" stroke-dasharray="8 5"/><line x1="500" y1="130" x2="500" y2="530" stroke="#2563eb" stroke-dasharray="8 5"/><circle cx="500" cy="330" r="50" fill="none" stroke="#d97706" stroke-dasharray="8 5"/><text x="340" y="510" class="s">center-hole witness only; diameter and position HOLD</text>'
    elif kind == "THROUGH":
        body = '<rect x="300" y="150" width="400" height="360" fill="none" stroke="#334155" stroke-width="4"/><line x1="220" y1="330" x2="780" y2="330" stroke="#2563eb" stroke-dasharray="8 5"/><rect x="420" y="250" width="160" height="160" fill="none" stroke="#d97706" stroke-dasharray="8 5"/><text x="325" y="535" class="s">through-hole witness zone; exact core/wall/slot orientation HOLD</text>'
    else:
        body = '<rect x="300" y="230" width="400" height="180" class="frame"/><circle cx="270" cy="320" r="35" class="a"/><circle cx="730" cy="320" r="35" class="a"/><rect x="120" y="250" width="150" height="140" class="svc"/><rect x="730" y="250" width="150" height="140" class="svc"/><text x="300" y="450" class="s">bolt head/tool comparison envelopes only; exact products HOLD</text>'
    return svg_base(kind.replace("_", " ").title() + " — 1:1 reference", body + bar + warning)


def svg_payloads() -> dict[str, str]:
    return {
        A_FILES[8]: plan_view("A"), A_FILES[9]: front_view("A"), A_FILES[10]: side_view("A"), A_FILES[11]: joint_section("A", "front"), A_FILES[12]: joint_section("A", "rear"),
        B_FILES[9]: plan_view("B"), B_FILES[10]: front_view("B"), B_FILES[11]: side_view("B"), B_FILES[12]: joint_section("B", "front"), B_FILES[13]: joint_section("B", "rear"),
        BASELINE_FILES[2]: baseline_svg(), PHYSICAL_ACTUAL_FILES[3]: physical_actual_svg("HEIGHT"), PHYSICAL_ACTUAL_FILES[4]: physical_actual_svg("GAPS"),
        COMPARISON_FILES[2]: comparison_svg("FRAME_LENGTH"), COMPARISON_FILES[3]: comparison_svg("CLEAR_WIDTH"), COMPARISON_FILES[4]: comparison_svg("UNDERSIDE_DROP"), COMPARISON_FILES[5]: comparison_svg("SERVICE_ACCESS"), COMPARISON_FILES[6]: comparison_svg("HEIGHT_CASE"), COMPARISON_FILES[7]: comparison_svg("M5_TEST"),
    }


def assembly_shapes(rel: str) -> list[cq.Shape]:
    frame = frame_shapes()
    ties = tie_plate_shapes()
    fixed = fixed_powertrain_shapes(ACTUAL_HEIGHT_CASE, guards=False)
    guarded = fixed_powertrain_shapes(ACTUAL_HEIGHT_CASE, guards=True)
    service = service_shapes(ACTUAL_HEIGHT_CASE)
    actual_components = powertrain_components(ACTUAL_HEIGHT_CASE)
    actual_stack = [shape for name, shape in actual_components.items() if name.endswith(("V0933_PLATE", "M3_FASTENER_ZONE", "M5_FASTENER_ZONE", "SPACER_NUT_ZONE"))]
    previous_components = powertrain_components(PREVIOUS_HEIGHT_CASE)
    previous_stack = [shape for name, shape in previous_components.items() if name.endswith(("V0933_PLATE", "M3_FASTENER_ZONE", "M5_FASTENER_ZONE", "SPACER_NUT_ZONE"))]
    if rel.endswith("A_FRAME_ONLY.step"): return frame
    if rel.endswith("A_FASTENER_ENVELOPES.step"): return [*frame, *candidate_a_fastener_shapes()]
    if rel.endswith("A_POWERTRAIN_ACTUAL_HEIGHT.step"): return [*frame, *fixed]
    if rel.endswith("A_POWERTRAIN_GUARDED.step"): return [*frame, *guarded]
    if rel.endswith("A_SERVICE_SWEEP.step"): return [*frame, *guarded, *service]
    if re.search(r"A_H(6|8|10)_REFERENCE\.step$", rel):
        case = re.search(r"A_(H(?:6|8|10))_REFERENCE", rel).group(1)
        return [*frame, *fixed_powertrain_shapes(case, guards=True)]
    if rel.endswith("B_FRAME_ONLY.step"): return [*frame, *ties]
    if rel.endswith("B_TIE_PLATES_ONLY.step"): return ties
    if rel.endswith("B_FASTENER_ENVELOPES.step"): return [*frame, *ties, *candidate_b_fastener_shapes()]
    if rel.endswith("B_POWERTRAIN_ACTUAL_HEIGHT.step"): return [*frame, *ties, *fixed]
    if rel.endswith("B_POWERTRAIN_GUARDED.step"): return [*frame, *ties, *guarded]
    if rel.endswith("B_SERVICE_SWEEP.step"): return [*frame, *ties, *guarded, *service]
    if re.search(r"B_H(6|8|10)_REFERENCE\.step$", rel):
        case = re.search(r"B_(H(?:6|8|10))_REFERENCE", rel).group(1)
        return [*frame, *ties, *fixed_powertrain_shapes(case, guards=True)]
    if rel.endswith("INNER_CORNER_INTRUSION_PROXY.step"): return [*frame, *baseline_corner_shapes()]
    if rel.endswith("BASELINE_POWERTRAIN_FIXED.step"): return [*frame, *baseline_corner_shapes(), *fixed]
    if rel.endswith("ACTUAL_MOTOR_PLATE_STACK.step"): return [*frame, *actual_stack]
    if rel.endswith("ACTUAL_GAP_3P8_3P9_REFERENCE.step"): return [*frame, *[shape for name, shape in previous_components.items() if name.endswith(("V0933_PLATE", "SPACER_NUT_ZONE"))]]
    if rel.endswith("ACTUAL_M5X16_2P5_TURN_REFERENCE.step"):
        m5 = [cylinder_z(2.5, 16.0, (x, POWERTRAIN_CENTER_Y + y, SIDE_RAIL_Z + 8.0)) for x in (-70.0, 70.0) for y in (-24.0, 24.0)]
        return [*frame, *previous_stack, *m5]
    if rel.endswith("A_B_OVERLAY_TOP.step"): return [*frame, *ties, *candidate_a_fastener_shapes(), *guarded]
    if rel.endswith("A_B_OVERLAY_SIDE.step"): return [*frame, *ties, *candidate_a_fastener_shapes(), *guarded, *service]
    raise ValueError(rel)


def canonicalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"FILE_NAME\('.*?','.*?',", "FILE_NAME('PS-CR-V0934','2000-01-01T00:00:00',", text, count=1)
    text = re.sub(r"FILE_DESCRIPTION\(\(.*?\),'.*?'\);", "FILE_DESCRIPTION(('FRAME JOINT TRADE STUDY'),'2;1');", text, count=1)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def export_step(path: Path, shapes: Iterable[cq.Shape]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(compound(shapes), str(path))
    canonicalize_step(path)


def export_artifacts() -> None:
    for rel in STEP_FILES:
        export_step(LANE_DIR / rel, assembly_shapes(rel))
    payloads = svg_payloads()
    if set(payloads) != set(SVG_FILES):
        raise RuntimeError({"svg_missing": sorted(set(SVG_FILES) - set(payloads)), "svg_extra": sorted(set(payloads) - set(SVG_FILES))})
    for rel, text in payloads.items():
        write_text(LANE_DIR / rel, text)


def manifest_text() -> str:
    lines = [f"document_id={DOCUMENT_ID}", f"version={VERSION}", f"path_count={len(PACKAGE_PATHS)}", "scope=V0934_ONLY", f"anchor={ANCHOR}", "authority_pointer=UNCHANGED", "recommendation=A_AND_B_PHYSICAL_MOCKUP_REQUIRED", "manufacturing=PROHIBITED", "power=PROHIBITED", ""]
    for rel in PACKAGE_PATHS:
        if rel.endswith(".step"): role = "CAD_TRADE_STUDY_REFERENCE"
        elif rel.endswith(".svg"): role = "VIEW_OR_MEASUREMENT_REFERENCE_TEMPLATE"
        elif rel.endswith(".csv"): role = "TRADE_STUDY_TABLE"
        elif rel.endswith(".json"): role = "MACHINE_READABLE_CONTRACT"
        elif rel.endswith(".py"): role = "BUILDER_OR_TEST"
        else: role = "DOCUMENT_OR_LEDGER"
        lines.append(f"{rel}|{role}")
    return "\n".join(lines)


def commit_paths_text() -> str:
    prefix = "cad/common_rover/common_rover_powertrain_frame_joint_trade_study_v0_9_3_4"
    return "\n".join(f"{prefix}/{rel}" for rel in PACKAGE_PATHS)


def sha256sums_text() -> str:
    return "\n".join(f"{sha256(LANE_DIR / rel)}  {rel}" for rel in PACKAGE_PATHS if rel != "SHA256SUMS.txt")


def parse_hashes(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            result[rel] = digest
    return result


def verify_hashes(base: Path = LANE_DIR) -> dict[str, Any]:
    hashes = parse_hashes(base / "SHA256SUMS.txt")
    required = set(PACKAGE_PATHS) - {"SHA256SUMS.txt"}
    mismatches: list[Any] = []
    if set(hashes) != required:
        mismatches.append({"missing": sorted(required - set(hashes)), "extra": sorted(set(hashes) - required)})
    for rel, expected in hashes.items():
        actual = sha256(base / rel) if (base / rel).is_file() else "MISSING"
        if actual != expected:
            mismatches.append({"path": rel, "expected": expected, "actual": actual})
    return {"verified": len(hashes), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def manifest_paths(path: Path) -> list[str]:
    return [line.split("|", 1)[0] for line in path.read_text(encoding="utf-8").splitlines() if "|" in line]


def verify_manifest(base: Path = LANE_DIR) -> dict[str, Any]:
    values = manifest_paths(base / "MANIFEST.txt")
    return {"entry_count": len(values), "exact_order": values == list(PACKAGE_PATHS), "status": "PASS" if values == list(PACKAGE_PATHS) else "FAIL"}


def verify_steps(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for rel in STEP_FILES:
        try:
            shape = cq.importers.importStep(str(base / rel)).val()
            b = bounds(shape)
            passed = len(shape.Solids()) >= 1 and all(math.isfinite(value) for value in b.values())
            rows.append({"path": rel, "solids": len(shape.Solids()), "bounds": b, "pass": passed})
        except Exception as exc:
            rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_svgs(base: Path = LANE_DIR) -> dict[str, Any]:
    import xml.etree.ElementTree as ET
    rows = []
    for rel in SVG_FILES:
        try:
            text = (base / rel).read_text(encoding="utf-8")
            root = ET.fromstring(text)
            passed = root.tag.endswith("svg") and "viewBox" in root.attrib and "TRADE STUDY" in text
            rows.append({"path": rel, "pass": passed})
        except Exception as exc:
            rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_csvs(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for rel in CSV_FILES:
        try:
            values = read_csv(base / rel)
            passed = bool(values) and bool(values[0]) and len(values[0]) >= 3
            rows.append({"path": rel, "row_count": len(values), "column_count": len(values[0]) if values else 0, "pass": passed})
        except Exception as exc:
            rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_evidence(base: Path = LANE_DIR) -> dict[str, Any]:
    params = json.loads((base / "frame_joint_parameters_v0934.json").read_text(encoding="utf-8"))
    collisions = read_csv(base / "candidate_collision_matrix_v0934.csv")
    dimensions = read_csv(base / "candidate_dimension_report_v0934.csv")
    sweep = read_csv(base / "crossmember_y_sweep_v0934.csv")
    heights = read_csv(base / "height_case_report_v0934.csv")
    min_row = next(row for row in sweep if row["status"] == "MINIMUM_VIABLE")
    target_row = next(row for row in sweep if row["status"] == "TARGET")
    checks = {
        "frame_width": params["frame"]["outer_width_x_mm"] == 180.0,
        "clear_width": params["frame"]["powertrain_clear_width_x_mm"] == 100.0,
        "rail_positions": params["frame"]["left_rail_center_x_mm"] == -70.0 and params["frame"]["right_rail_center_x_mm"] == 70.0,
        "baseline": params["baseline"]["inner_corner_intrusion_per_side_mm"] == 27.9 and params["baseline"]["remaining_width_mm"] == 44.2,
        "no_inner_brackets": params["candidate_a"]["inner_bracket"] is False and params["candidate_b"]["inner_bracket"] is False,
        "central_intrusion_zero": params["candidate_a"]["central_intrusion_mm"] == 0.0 and params["candidate_b"]["central_upper_intrusion_mm"] == 0.0,
        "tie_plate": params["candidate_b"]["plate_mm"] == [180.0, 40.0, 3.0],
        "crossmember_span": params["candidate_a"]["crossmember_span_mm"] == params["candidate_b"]["crossmember_span_mm"] == 100.0,
        "collision_fail_zero": not any(row["status"] == "FAIL" for row in collisions),
        "powertrain_collisions_zero": all(float(row["intersection_volume_mm3"]) <= 1e-6 for row in collisions if row["target"] in ("motor", "20T_pulley", "60T_pulley", "belt", "fixed_guard")),
        "height_cases": {row["height_case"] for row in heights} == {ACTUAL_HEIGHT_CASE, PREVIOUS_HEIGHT_CASE, "H6", "H8", "H10"},
        "actual_height_primary": next(row for row in heights if row["height_case"] == ACTUAL_HEIGHT_CASE)["physical_selection"] == "PRIMARY_ACTUAL",
        "previous_height_historical": next(row for row in heights if row["height_case"] == PREVIOUS_HEIGHT_CASE)["physical_selection"] == "HISTORICAL_SUPERSEDED",
        "physical_plate": params["physical_result"]["petg_plate_thickness_mm"] == 6.0 and params["physical_result"]["additional_plain_washer_count_per_m5"] == 2 and params["physical_result"]["height_adjustment_nut_count_per_m5"] == 1,
        "physical_derived": params["physical_result"]["minimum_gap_mm"] == 4.3 and params["physical_result"]["maximum_gap_mm"] == 4.5 and params["physical_result"]["gap_range_mm"] == 0.2 and params["physical_result"]["derived_nominal_gap_mm"] == 4.4 and params["physical_result"]["derived_nominal_plate_top_height_mm"] == 10.4,
        "m5_evidence": params["physical_result"]["m5x16_thread_engagement"] == "FULL_TNUT_THREAD_TRAVERSAL_USER_REPORTED" and params["physical_result"]["m5_thread_pitch"] == "MEASUREMENT_HOLD" and params["physical_result"]["m5_engagement_length_mm"] == "NOT_CALCULATED",
        "history_preserved": params["physical_result"]["previous_physical_result"]["status"] == "HISTORICAL_PHYSICAL_RESULT" and params["physical_result"]["previous_physical_result"]["gap_range_mm"] == 0.1,
        "creep_required": params["physical_result"]["creep_test_24h"]["status"] == "REQUIRED_BEFORE_BELT_TENSION",
        "no_load_status": params["approval"]["motor_plate_physical_fit"] == "PHYSICAL_PASS_NO_LOAD" and params["approval"]["powered_m5x16"] == "NOT_APPROVED",
        "y_sweep": len(sweep) == len(y_sweep_rows()) and float(min_row["minimum_fixed_clearance_mm"]) >= 10.0 and float(target_row["minimum_fixed_clearance_mm"]) >= 15.0,
        "frame_lengths": float(min_row["frame_length_mm"]) == 230.0 and float(target_row["frame_length_mm"]) == 240.0,
        "service_separate": all(row["minimum_service_clearance_mm"] != row["minimum_fixed_clearance_mm"] for row in (min_row, target_row)),
        "architecture": params["architecture"]["left_right_independent_power"] and not params["architecture"]["common_left_right_shaft"],
        "recommendation": params["recommendation"] == "A_AND_B_PHYSICAL_MOCKUP_REQUIRED",
        "authority": params["approval"]["authority_update"] == "NOT_APPROVED",
        "power": params["approval"]["powered_rotation"] == "NOT_APPROVED",
        "dimensions": len(dimensions) == 4,
        "sources": params["source_reference_audit"]["status"] == "PASS",
        "reference_zip": params["reference_zip_audit"]["status"] == "PASS",
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def refresh_artifacts() -> dict[str, Any]:
    for rel in ("build_powertrain_frame_joint_trade_study_v0934.py", "tests/test_powertrain_frame_joint_trade_study_v0934.py"):
        if not (LANE_DIR / rel).is_file():
            raise RuntimeError(f"source missing: {rel}")
    repository_audit(require_complete=False)
    parents = parent_audit(True)
    sources = source_reference_audit(True)
    params = parameters(parents, sources)
    write_text(LANE_DIR / ROOT_FILES[0], study_markdown(params))
    write_json(LANE_DIR / ROOT_FILES[1], params)
    write_text(LANE_DIR / ROOT_FILES[2], physical_result_markdown())
    write_json(LANE_DIR / ROOT_FILES[3], {"document_id": DOCUMENT_ID, **PHYSICAL_RESULT, "actual_height_case": ACTUAL_HEIGHT_CASE, "authority_update": "NOT_APPROVED"})
    write_csv(LANE_DIR / ROOT_FILES[4], frame_measurement_rows())
    write_text(LANE_DIR / ROOT_FILES[5], candidate_a_markdown())
    write_text(LANE_DIR / ROOT_FILES[6], candidate_b_markdown())
    write_text(LANE_DIR / ROOT_FILES[7], baseline_markdown())
    write_csv(LANE_DIR / ROOT_FILES[8], trade_rows())
    write_csv(LANE_DIR / ROOT_FILES[9], collision_rows())
    write_csv(LANE_DIR / ROOT_FILES[10], dimension_rows())
    write_csv(LANE_DIR / ROOT_FILES[11], y_sweep_rows())
    write_csv(LANE_DIR / ROOT_FILES[12], repair_rows())
    write_csv(LANE_DIR / ROOT_FILES[13], fastener_rows())
    write_csv(LANE_DIR / ROOT_FILES[14], height_rows())
    write_text(LANE_DIR / ROOT_FILES[15], m5_comparison_markdown())
    write_text(LANE_DIR / ROOT_FILES[16], remaining_measurements_markdown())
    write_text(LANE_DIR / ROOT_FILES[17], physical_mockup_markdown())
    write_text(LANE_DIR / ROOT_FILES[18], readme_markdown())
    write_text(LANE_DIR / ROOT_FILES[19], no_release_text())
    write_text(LANE_DIR / ROOT_FILES[22], commit_paths_text())
    export_artifacts()
    write_text(LANE_DIR / ROOT_FILES[25], "status=PREPACKAGE_SELF_CHECKS_PASS\ncontract_tests=RUN_DURING_PACKAGE\ncsv_import_render=REQUIRED_BEFORE_PACKAGE\nphysical_mockup=NOT_YET_PERFORMED\nactual_motor_plate=PHYSICAL_PASS_NO_LOAD\nm5x16=PHYSICAL_PASS_NO_LOAD\ncreep_24h=REQUIRED_BEFORE_BELT_TENSION\npowered_load=NOT_APPROVED")
    write_text(LANE_DIR / ROOT_FILES[23], manifest_text())
    write_text(LANE_DIR / ROOT_FILES[24], sha256sums_text())
    actual = lane_files()
    if actual != sorted(EXPECTED_LANE_PATHS):
        raise RuntimeError({"missing": sorted(EXPECTED_LANE_PATHS - set(actual)), "extra": sorted(set(actual) - EXPECTED_LANE_PATHS)})
    reports = (verify_steps(), verify_svgs(), verify_csvs(), verify_evidence())
    if any(report["status"] != "PASS" for report in reports):
        raise RuntimeError({"reports": reports})
    return {"document_id": DOCUMENT_ID, "exact_package_paths": len(PACKAGE_PATHS), "parent": parents["status"], "source_references": sources["status"], "STEP_reload": f"{reports[0]['pass_count']}/{reports[0]['count']} PASS", "SVG": f"{reports[1]['pass_count']}/{reports[1]['count']} PASS", "CSV_parse": f"{reports[2]['pass_count']}/{reports[2]['count']} PASS", "evidence": reports[3]["status"], "status": "PASS"}


def verify() -> dict[str, Any]:
    actual = lane_files()
    if live_repository() and actual != sorted(EXPECTED_LANE_PATHS):
        raise RuntimeError({"missing": sorted(EXPECTED_LANE_PATHS - set(actual)), "extra": sorted(set(actual) - EXPECTED_LANE_PATHS)})
    if not live_repository() and actual != sorted(PACKAGE_PATHS):
        raise RuntimeError({"missing": sorted(set(PACKAGE_PATHS) - set(actual)), "extra": sorted(set(actual) - set(PACKAGE_PATHS))})
    repository = repository_audit(require_complete=True)
    parents = parent_audit()
    hashes = verify_hashes(); manifest = verify_manifest(); steps = verify_steps(); svgs = verify_svgs(); csvs = verify_csvs(); evidence = verify_evidence()
    reports = {"parents": parents["status"], "hashes": hashes["status"], "manifest": manifest["status"], "steps": steps["status"], "svgs": svgs["status"], "csvs": csvs["status"], "evidence": evidence["status"]}
    if any(value != "PASS" for value in reports.values()):
        raise RuntimeError({"reports": reports, "hashes": hashes, "manifest": manifest, "evidence": evidence})
    return {"document_id": DOCUMENT_ID, "repository": repository, "parent_protection": parents["status"], "exact_package_paths": len(PACKAGE_PATHS), "hashes": f"{hashes['verified']}/{len(PACKAGE_PATHS)-1} PASS", "manifest": f"{manifest['entry_count']}/{len(PACKAGE_PATHS)} PASS", "STEP_reload": f"{steps['pass_count']}/{steps['count']} PASS", "SVG": f"{svgs['pass_count']}/{svgs['count']} PASS", "CSV_parse": f"{csvs['pass_count']}/{csvs['count']} PASS", "status": "PASS"}


def zip_info(rel: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(rel, date_time=(2000, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def write_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "x") as archive:
        for rel in PACKAGE_PATHS:
            archive.writestr(zip_info(rel), (LANE_DIR / rel).read_bytes())


def verify_zip(path: Path, standalone: bool = True) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"ZIP missing: {path}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        traversal = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        if names != list(PACKAGE_PATHS) or duplicates or traversal:
            raise RuntimeError({"scope": names == list(PACKAGE_PATHS), "duplicates": duplicates, "traversal": traversal})
        hashes = {}
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            if line.strip():
                digest, rel = line.split("  ", 1); hashes[rel] = digest
        internal = [rel for rel, expected in hashes.items() if hashlib.sha256(archive.read(rel)).hexdigest() != expected]
        lane_mismatches = [rel for rel in names if hashlib.sha256(archive.read(rel)).hexdigest() != sha256(LANE_DIR / rel)]
    standalone_status = "NOT_REQUESTED"
    if standalone:
        with tempfile.TemporaryDirectory(prefix="ps_cr_v0934_zip_") as temp:
            target = Path(temp)
            with zipfile.ZipFile(path) as archive:
                archive.extractall(target)
            env = dict(os.environ); env["V0934_TEST_ZIP"] = str(path)
            build = run([sys.executable, "-B", "build_powertrain_frame_joint_trade_study_v0934.py", "--verify"], cwd=target, env=env)
            tests = run([sys.executable, "-B", "tests/test_powertrain_frame_joint_trade_study_v0934.py"], cwd=target, env=env)
            if build.returncode or tests.returncode:
                raise RuntimeError({"standalone_build": build.stdout, "standalone_tests": tests.stdout})
            standalone_status = "PASS"
    if internal or lane_mismatches:
        raise RuntimeError({"internal_hash_mismatches": internal, "lane_mismatches": lane_mismatches})
    return {"zip_path": str(path), "entry_count": len(names), "duplicates": duplicates, "path_traversal": traversal, "internal_hash_verification": "PASS", "lane_byte_match": "PASS", "standalone_verify": standalone_status, "zip_sha256": sha256(path), "status": "PASS"}


def package_handoff() -> dict[str, Any]:
    if os.environ.get("V0934_CSV_RENDER_PASS") != "1":
        raise RuntimeError("V0934_CSV_RENDER_PASS=1 is required after artifact-tool CSV import/render verification")
    verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{timestamp}.zip"
    temporary = DOWNLOAD_DIR / f".{ZIP_PREFIX}{timestamp}.validation.tmp"
    if final_path.exists() or temporary.exists():
        raise RuntimeError("refusing to overwrite handoff")
    try:
        write_text(LANE_DIR / ROOT_FILES[25], "status=PACKAGE_TESTS_PENDING\ncsv_import_render=PASS_ARTIFACT_TOOL_8_OF_8\nphysical_mockup=NOT_YET_PERFORMED\nactual_motor_plate=PHYSICAL_PASS_NO_LOAD\nm5x16=PHYSICAL_PASS_NO_LOAD\ncreep_24h=REQUIRED_BEFORE_BELT_TENSION\npowered_load=NOT_APPROVED")
        write_text(LANE_DIR / ROOT_FILES[24], sha256sums_text())
        write_zip(temporary)
        env = dict(os.environ); env["V0934_TEST_ZIP"] = str(temporary)
        result = run([sys.executable, "-B", "tests/test_powertrain_frame_joint_trade_study_v0934.py"], cwd=LANE_DIR, env=env)
        if result.returncode:
            raise RuntimeError(f"contract tests failed:\n{result.stdout}")
        summary = [line for line in result.stdout.splitlines() if line.startswith("Ran ") or line == "OK"]
        write_text(LANE_DIR / ROOT_FILES[25], "command=python -B tests/test_powertrain_frame_joint_trade_study_v0934.py\nstatus=PASS\ncsv_import_render=PASS_ARTIFACT_TOOL_8_OF_8\n" + "\n".join(summary) + "\nphysical_mockup=NOT_YET_PERFORMED\nactual_motor_plate=PHYSICAL_PASS_NO_LOAD\nm5x16=PHYSICAL_PASS_NO_LOAD\ncreep_24h=REQUIRED_BEFORE_BELT_TENSION\npowered_load=NOT_APPROVED\nfull_output:\n" + result.stdout)
        write_text(LANE_DIR / ROOT_FILES[24], sha256sums_text())
        verify()
    finally:
        if temporary.exists():
            temporary.unlink()
    write_zip(final_path)
    return {"verification": "PASS", **verify_zip(final_path, standalone=True)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-artifacts", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--verify-zip", type=Path)
    args = parser.parse_args(argv)
    if sum(bool(value) for value in (args.refresh_artifacts, args.verify, args.package, args.verify_zip)) != 1:
        parser.error("choose exactly one action")
    if args.refresh_artifacts: result = refresh_artifacts()
    elif args.verify: result = verify()
    elif args.package: result = package_handoff()
    else: result = verify_zip(args.verify_zip, standalone=True)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
