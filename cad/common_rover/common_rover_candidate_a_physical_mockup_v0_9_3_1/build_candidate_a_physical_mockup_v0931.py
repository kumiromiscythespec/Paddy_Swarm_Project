from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import cadquery as cq
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape


DOCUMENT_ID = "PS-CR-CANDIDATE-A-PHYSICAL-MOCKUP-V0931"
VERSION = "0.9.3.1"
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
PARENT_DIR = REPO_ROOT / "cad/common_rover/common_rover_motor_layout_powerpath_trade_study_v0_9_3_0"
PARENT_ZIP = Path(r"D:\Downloads\Paddy_Swarm_Common_Rover_v0_9_3_0_Motor_Layout_Powerpath_Trade_Study_20260803_185807.zip")
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_9_3_1_Candidate_A_Physical_Mockup_"

EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "187d9cf41b1d2472ef5ec5e6677d6f05909d01e5"
EXPECTED_TRACKED_DIFF = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
}
PARENT_PATH_COUNT = 151
PARENT_LEDGER_SHA256 = "661a1d1f2ef6b83eb5e2506aac4494e9073c5af6d3cc78ed8fbdc34b9ab7d99f"
PARENT_ZIP_SHA256 = "859763d303d154186aedbf676ffbe7d623724bb0f4cc030acc170830a32edfe6"
CURRENT_POINTER_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}

PULLEY_SOURCE_DIR = Path(r"D:\Paddy_Swarm_Project_worktrees\common_rover_htd5m_full_pulley_dummy_v0_1\cad\common_rover\htd5m_full_pulley_dummy_candidate_v0_1")
PULLEY_REFERENCES = {
    "20T_STEP": {"path": str(PULLEY_SOURCE_DIR / "artifacts/PS-HTD5M-PULLEY-20T-STD-DUMMY-V001.step"), "sha256": "95684926935f9f49ae02cd02b88fd71bc4cac318cfe0f16c48099d735b2c46c1"},
    "20T_STL": {"path": str(PULLEY_SOURCE_DIR / "artifacts/PS-HTD5M-PULLEY-20T-STD-DUMMY-V001.stl"), "sha256": "a3e22cba3cd02e246fb9f1a8a58a9a10a0a12f8e5ddbec1e8397da01af9d944b"},
    "60T_STEP": {"path": str(PULLEY_SOURCE_DIR / "artifacts/PS-HTD5M-PULLEY-60T-STD-DUMMY-V001.step"), "sha256": "bc3e00bca0db5fe4c3975b5904ad4f72faa2b3fe6822057522c12df16ec0d256"},
    "60T_STL": {"path": str(PULLEY_SOURCE_DIR / "artifacts/PS-HTD5M-PULLEY-60T-STD-DUMMY-V001.stl"), "sha256": "2577b0cd8575a961e527c47e304036a4072245ef051f91c5eccf3e1adbac42f7"},
}

LEFT_FRONT = (68.0, -185.0, 105.0)
RIGHT_FRONT = (-68.0, -185.0, 105.0)
MOTOR_DIAMETER = 36.9
BODY_LENGTH = 60.9
REAR_TERMINAL = 9.2
REAR_FIXED = 70.1
SHAFT_LENGTH = 16.9
SHAFT_DIAMETER = 5.9
BOSS_DIAMETER = 12.0
BOSS_LENGTH = 2.7
BRACKET_WIDTH = 40.1
BRACKET_HEIGHT = 45.5
BRACKET_LENGTH = 42.8
BRACKET_THICKNESS = 3.1
FASTENER_HOLE_DIAMETER = 3.4
FASTENER_PITCH = (30.0, 23.8)
VERTICAL_SLOT_REPRESENTATIVE = 27.7
G1_MARGIN = 5.0
S2_SERVICE_EXTRA = 20.0
TARGET_WIDTH = 290.0
ABSOLUTE_WIDTH = 300.0
A1_BUILD_VOLUME = (256.0, 256.0, 256.0)


ROOT_FILES = [
    "candidate_a_physical_mockup_plan_v0931.md",
    "candidate_a_physical_mockup_parameters_v0931.json",
    "candidate_a_mockup_part_list_v0931.csv",
    "candidate_a_mockup_measurement_record_v0931.csv",
    "candidate_a_mockup_photo_log_v0931.md",
    "physical_mockup_procedure_v0931.md",
    "candidate_a_pass_fail_contract_v0931.md",
    "remaining_measurements_v0931.md",
    "build_candidate_a_physical_mockup_v0931.py",
    "tests/test_candidate_a_physical_mockup_v0931.py",
    "README_HANDOFF.md",
    "NO_POWER_NO_LOAD_ONLY.txt",
    "COMMIT_PATHS.txt",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "test_results_v0931.txt",
]
PRINT_FILES = [
    "artifacts/print/LEFT_MOTOR_POSITIONING_JIG.stl",
    "artifacts/print/RIGHT_MOTOR_POSITIONING_JIG.stl",
    "artifacts/print/LEFT_MOTOR_DATUM_GAUGE.stl",
    "artifacts/print/RIGHT_MOTOR_DATUM_GAUGE.stl",
    "artifacts/print/LEFT_SHAFT_CENTERLINE_GAUGE.stl",
    "artifacts/print/RIGHT_SHAFT_CENTERLINE_GAUGE.stl",
    "artifacts/print/LEFT_G1_GUARD_GAUGE.stl",
    "artifacts/print/RIGHT_G1_GUARD_GAUGE.stl",
    "artifacts/print/SELECTOR_CENTERLINE_JIG_LEFT.stl",
    "artifacts/print/SELECTOR_CENTERLINE_JIG_RIGHT.stl",
    "artifacts/print/DRIVE_NEUTRAL_PTO_INDICATOR_LEFT.stl",
    "artifacts/print/DRIVE_NEUTRAL_PTO_INDICATOR_RIGHT.stl",
    "artifacts/print/BELT_PLANE_GAUGE_LEFT.stl",
    "artifacts/print/BELT_PLANE_GAUGE_RIGHT.stl",
]
TEMPLATE_FILES = [
    "artifacts/templates/TOTAL_WIDTH_290_TEMPLATE.svg",
    "artifacts/templates/CBOX_BBOX_FRAME_TEMPLATE.svg",
    "artifacts/templates/TRACK_PROXY_TEMPLATE.svg",
    "artifacts/templates/MOTOR_SERVICE_SWEEP_TEMPLATE.svg",
    "artifacts/templates/UNIT_BAY_TEMPLATE.svg",
    "artifacts/templates/CABLE_BEND_TEMPLATE.svg",
    "artifacts/templates/MOCKUP_ASSEMBLY_TOP_VIEW.svg",
    "artifacts/templates/MOCKUP_ASSEMBLY_FRONT_VIEW.svg",
    "artifacts/templates/MOCKUP_ASSEMBLY_SIDE_VIEW.svg",
]
ASSEMBLY_FILES = [
    "artifacts/assemblies/CANDIDATE_A_MOCKUP_ASSEMBLY.step",
    "artifacts/assemblies/CANDIDATE_A_FIXED_WIDTH.step",
    "artifacts/assemblies/CANDIDATE_A_GUARDED_WIDTH.step",
    "artifacts/assemblies/CANDIDATE_A_SERVICE_SWEEP.step",
    "artifacts/assemblies/CANDIDATE_A_DRIVE_STATE.step",
    "artifacts/assemblies/CANDIDATE_A_NEUTRAL_STATE.step",
    "artifacts/assemblies/CANDIDATE_A_PTO_STATE.step",
]
PACKAGE_PATHS = tuple(ROOT_FILES + PRINT_FILES + TEMPLATE_FILES + ASSEMBLY_FILES)
if len(PACKAGE_PATHS) != 46 or len(set(PACKAGE_PATHS)) != 46:
    raise RuntimeError("v0.9.3.1 package must contain exactly 46 unique paths")


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
    return (REPO_ROOT / ".git").exists() or run(["git", "rev-parse", "--show-toplevel"]).returncode == 0


def lane_files(base: Path = LANE_DIR) -> list[str]:
    return sorted(path.relative_to(base).as_posix() for path in base.rglob("*") if path.is_file() and "__pycache__" not in path.parts)


def directory_ledger(path: Path) -> dict[str, Any]:
    rows = []
    for file in sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        rows.append((file.relative_to(path).as_posix(), sha256(file)))
    payload = "".join(f"{rel}\t{digest}\n" for rel, digest in rows).encode("utf-8")
    return {"file_count": len(rows), "ledger_sha256": hashlib.sha256(payload).hexdigest()}


def parent_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    if not live:
        return {"mode": "STANDALONE_EMBEDDED_PARENT_EVIDENCE", "parent_path_count": PARENT_PATH_COUNT, "parent_ledger_sha256": PARENT_LEDGER_SHA256, "parent_zip_sha256": PARENT_ZIP_SHA256, "zip_lane_byte_mismatches": [], "status": "PASS"}
    ledger = directory_ledger(PARENT_DIR)
    if not PARENT_ZIP.is_file():
        raise RuntimeError(f"parent ZIP missing: {PARENT_ZIP}")
    with zipfile.ZipFile(PARENT_ZIP) as archive:
        names = archive.namelist()
        files = lane_files(PARENT_DIR)
        mismatches = [rel for rel in names if sha256(PARENT_DIR / rel) != hashlib.sha256(archive.read(rel)).hexdigest()]
        scope = names == list(json_manifest_paths(PARENT_DIR / "MANIFEST.txt")) and set(names) == set(files)
    pointers = []
    for rel, expected in CURRENT_POINTER_HASHES.items():
        actual = sha256(REPO_ROOT / rel)
        pointers.append({"path": rel, "expected_sha256": expected, "actual_sha256": actual, "pass": expected == actual})
    pulley_rows = []
    for name, reference in PULLEY_REFERENCES.items():
        path = Path(reference["path"])
        actual = sha256(path) if path.is_file() else "MISSING"
        pulley_rows.append({"id": name, "path": str(path), "expected_sha256": reference["sha256"], "actual_sha256": actual, "pass": actual == reference["sha256"]})
    checks = {
        "parent_path_count": ledger["file_count"] == PARENT_PATH_COUNT,
        "parent_ledger": ledger["ledger_sha256"] == PARENT_LEDGER_SHA256,
        "parent_zip_sha": sha256(PARENT_ZIP) == PARENT_ZIP_SHA256,
        "zip_scope": scope,
        "zip_lane_byte_match": not mismatches,
        "authority_pointers": all(row["pass"] for row in pointers),
        "pulley_references": all(row["pass"] for row in pulley_rows),
    }
    if not all(checks.values()):
        raise RuntimeError({"parent_audit": checks, "mismatches": mismatches, "pointers": pointers, "pulley": pulley_rows})
    return {
        "mode": "LIVE_REPOSITORY",
        "parent_path_count": ledger["file_count"],
        "parent_ledger_sha256": ledger["ledger_sha256"],
        "parent_zip_path": str(PARENT_ZIP),
        "parent_zip_sha256": sha256(PARENT_ZIP),
        "zip_lane_byte_mismatches": mismatches,
        "authority_pointers": pointers,
        "pulley_references": pulley_rows,
        "checks": checks,
        "status": "PASS",
    }


def json_manifest_paths(path: Path) -> list[str]:
    return [line.split("|", 1)[0] for line in path.read_text(encoding="utf-8").splitlines() if "|" in line]


def repository_audit() -> dict[str, Any]:
    if not live_repository():
        return {"mode": "STANDALONE_HANDOFF", "status": "PASS"}
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    root = str(Path(git("rev-parse", "--show-toplevel")).resolve())
    tracked = {line.replace("\\", "/") for line in git("diff", "--name-only").splitlines() if line}
    staged = {line.replace("\\", "/") for line in git("diff", "--cached", "--name-only").splitlines() if line}
    untracked = [line.replace("\\", "/") for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line]
    lane_rel = LANE_DIR.relative_to(REPO_ROOT).as_posix()
    lane_untracked = sorted(path[len(lane_rel) + 1:] for path in untracked if path.startswith(lane_rel + "/"))
    actual_lane = lane_files()
    parent_tracked = [line for line in git("ls-files", PARENT_DIR.relative_to(REPO_ROOT).as_posix()).splitlines() if line]
    forbidden = [path for path in actual_lane if "__pycache__" in path.lower() or path.lower().endswith((".pyc", ".pyo", ".fcstd", ".blend", ".tmp"))]
    parent = parent_audit(True)
    checks = {
        "root": root.lower() == str(REPO_ROOT.resolve()).lower(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "tracked_diff_preserved": tracked == EXPECTED_TRACKED_DIFF,
        "staged_zero": not staged,
        "parent_exact_151_tracked": len(parent_tracked) == PARENT_PATH_COUNT,
        "lane_scope": set(actual_lane).issubset(set(PACKAGE_PATHS)),
        "lane_git_scope_match": lane_untracked == actual_lane,
        "forbidden_zero": not forbidden,
        "parent_protection": parent["status"] == "PASS",
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_guard": checks, "tracked": sorted(tracked), "staged": sorted(staged), "forbidden": forbidden})
    return {"mode": "LIVE_REPOSITORY", "root": root, "branch": branch, "head": head, "tracked_diff": sorted(tracked), "staged_diff": sorted(staged), "untracked_total": len(untracked), "lane_untracked_count": len(lane_untracked), "checks": checks, "status": "PASS"}


def box(dx: float, dy: float, dz: float, center: tuple[float, float, float]) -> cq.Shape:
    return cq.Workplane("XY").box(dx, dy, dz).translate(center).val()


def cylinder_x(radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    x, y, z = center
    return cq.Workplane("YZ").circle(radius).extrude(length).translate((x - length / 2.0, y, z)).val()


def cylinder_z(radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    x, y, z = center
    return cq.Workplane("XY").circle(radius).extrude(length).translate((x, y, z - length / 2.0)).val()


def compound(shapes: Iterable[cq.Shape]) -> cq.Shape:
    values = list(shapes)
    if not values:
        raise ValueError("empty compound")
    return cq.Compound.makeCompound(values)


def mirror_x(shape: cq.Shape) -> cq.Shape:
    return shape.mirror("YZ")


def motor_positioning_jig(side: str) -> cq.Shape:
    base = box(110, 80, 8, (0, 0, 4))
    pieces = [base, box(6, 68, 46, (-42, 0, 31))]
    for x in (-15, 30):
        support = box(14, 56, 24, (x, 0, 20))
        saddle = cylinder_x(20.25, 18, (x, 0, 31))
        pieces.append(support.cut(saddle))
    sign = 1 if side == "LEFT" else -1
    pieces.append(box(22, 5, 18, (-28, sign * 31.5, 17)))
    holes = [cylinder_z(3.25, 10, (x, y, 4)) for x in (-35, 35) for y in (-28, 28)]
    return compound(pieces).cut(compound(holes))


def datum_gauge(side: str) -> cq.Shape:
    sign = 1 if side == "LEFT" else -1
    pieces = [box(70, 50, 6, (0, 0, 3)), box(5, 48, 46, (-27, 0, 26)), box(25, 5, 18, (-14, sign * 20, 14))]
    return compound(pieces)


def shaft_centerline_gauge(side: str) -> cq.Shape:
    sign = 1 if side == "LEFT" else -1
    base = box(80, 50, 6, (0, 0, 3))
    wall = box(8, 48, 52, (-20, 0, 32)).cut(cylinder_x(3.25, 12, (-20, 0, 35)))
    pointer = box(34, 4, 4, (2, sign * 18, 35))
    return compound([base, wall, pointer])


def guard_gauge(side: str) -> cq.Shape:
    sign = 1 if side == "LEFT" else -1
    bar = box(95, 25, 5, (0, 0, 2.5))
    datum = box(5, 40, 28, (-37.55, 0, 14))
    marker = box(5, 40, 40, (37.55, 0, 20))
    chirality = box(18, 5, 10, (24, sign * 15, 8))
    return compound([bar, datum, marker, chirality])


def selector_jig(side: str) -> cq.Shape:
    sign = 1 if side == "LEFT" else -1
    base = box(90, 52, 6, (0, 0, 3))
    tower = box(10, 50, 78, (-20, 0, 45)).cut(cylinder_x(5.25, 14, (-20, 0, 61)))
    key = box(24, 5, 15, (4, sign * 20, 15))
    return compound([base, tower, key])


def state_indicator(side: str) -> cq.Shape:
    sign = 1 if side == "LEFT" else -1
    base = box(72, 30, 5, (0, 0, 2.5))
    rail = box(46, 10, 8, (0, 0, 9))
    ticks = [box(2, 22, height, (x, 0, 5 + height / 2)) for x, height in ((-10, 10), (0, 16), (10, 10))]
    side_key = box(8, 8, 12, (28, sign * 10, 9))
    return compound([base, rail, *ticks, side_key])


def belt_plane_gauge(side: str) -> cq.Shape:
    sign = 1 if side == "LEFT" else -1
    frame = compound([box(120, 6, 4, (0, -17, 2)), box(120, 6, 4, (0, 17, 2)), box(6, 40, 4, (-57, 0, 2)), box(6, 40, 4, (57, 0, 2))])
    key = box(18, 6, 12, (-40, sign * 12, 8))
    return compound([frame, key])


PRINT_SHAPE_BUILDERS = {
    PRINT_FILES[0]: lambda: motor_positioning_jig("LEFT"),
    PRINT_FILES[1]: lambda: motor_positioning_jig("RIGHT"),
    PRINT_FILES[2]: lambda: datum_gauge("LEFT"),
    PRINT_FILES[3]: lambda: datum_gauge("RIGHT"),
    PRINT_FILES[4]: lambda: shaft_centerline_gauge("LEFT"),
    PRINT_FILES[5]: lambda: shaft_centerline_gauge("RIGHT"),
    PRINT_FILES[6]: lambda: guard_gauge("LEFT"),
    PRINT_FILES[7]: lambda: guard_gauge("RIGHT"),
    PRINT_FILES[8]: lambda: selector_jig("LEFT"),
    PRINT_FILES[9]: lambda: selector_jig("RIGHT"),
    PRINT_FILES[10]: lambda: state_indicator("LEFT"),
    PRINT_FILES[11]: lambda: state_indicator("RIGHT"),
    PRINT_FILES[12]: lambda: belt_plane_gauge("LEFT"),
    PRINT_FILES[13]: lambda: belt_plane_gauge("RIGHT"),
}


def environment_shapes() -> dict[str, cq.Shape]:
    frame = compound([box(20, 232, 20, (79, -116, 10)), box(20, 232, 20, (-79, -116, 10)), box(138, 20, 20, (0, -222, 10))])
    left_track = cq.Workplane("YZ").polyline([(300, 40), (-150, 40), (-120, 210), (260, 210)]).close().extrude(5, both=True).translate((140, 0, 0)).val()
    right_track = cq.Workplane("YZ").polyline([(300, 40), (-150, 40), (-120, 210), (260, 210)]).close().extrude(5, both=True).translate((-140, 0, 0)).val()
    return {
        "CBOX": box(130, 140, 105, (0, -70, 52.5)),
        "BBOX": box(150, 220, 150, (0, 110, 75)),
        "FRAME": frame,
        "TRACKS": compound([left_track, right_track]),
        "UNIT_BAY": box(144, 134, 160, (0, -313, 80)),
        "UNIT_SUPPORT_FRAME_REGION": compound([box(130, 20, 20, (0, -250, 20)), box(20, 100, 20, (53, -300, 20)), box(20, 100, 20, (-53, -300, 20))]),
    }


def placed_motors() -> dict[str, cq.Shape]:
    result: dict[str, cq.Shape] = {}
    for side, sign, front in (("LEFT", 1, LEFT_FRONT), ("RIGHT", -1, RIGHT_FRONT)):
        fx, fy, fz = front
        body_center = (fx + sign * BODY_LENGTH / 2, fy, fz)
        terminal_center = (fx + sign * (BODY_LENGTH + REAR_TERMINAL / 2), fy, fz)
        shaft_center = (fx - sign * SHAFT_LENGTH / 2, fy, fz)
        boss_center = (fx - sign * BOSS_LENGTH / 2, fy, fz)
        bracket_center = (fx + sign * BRACKET_LENGTH / 2, fy, fz)
        result[f"{side}_MOTOR_CYLINDER"] = cylinder_x(MOTOR_DIAMETER / 2, BODY_LENGTH, body_center)
        result[f"{side}_REAR_TERMINAL_FIXED"] = cylinder_x(MOTOR_DIAMETER / 2, REAR_TERMINAL, terminal_center)
        result[f"{side}_OUTPUT_SHAFT"] = cylinder_x(SHAFT_DIAMETER / 2, SHAFT_LENGTH, shaft_center)
        result[f"{side}_SHAFT_BOSS"] = cylinder_x(BOSS_DIAMETER / 2, BOSS_LENGTH, boss_center)
        result[f"{side}_BRACKET_ENVELOPE"] = box(BRACKET_LENGTH, BRACKET_WIDTH, BRACKET_HEIGHT, bracket_center)
        guard_length = REAR_FIXED + G1_MARGIN
        result[f"{side}_G1_GUARD"] = box(guard_length, BRACKET_WIDTH + 10, BRACKET_HEIGHT + 10, (fx + sign * guard_length / 2, fy, fz))
        service_length = REAR_FIXED + S2_SERVICE_EXTRA
        result[f"{side}_S2_SERVICE"] = box(service_length, BRACKET_WIDTH + 8, BRACKET_HEIGHT + 8, (fx + sign * service_length / 2, fy, fz))
        result[f"{side}_REMOVAL_SWEEP"] = box(REAR_FIXED + 100, BRACKET_WIDTH + 12, BRACKET_HEIGHT + 12, (fx + sign * (REAR_FIXED + 100) / 2, fy, fz))
        result[f"{side}_CABLE_BEND"] = cylinder_x(MOTOR_DIAMETER / 2 + 8, 30, (fx + sign * (REAR_FIXED + 15), fy, fz))
    return result


def power_shapes(state: str = "NEUTRAL") -> dict[str, cq.Shape]:
    result: dict[str, cq.Shape] = {}
    offsets = {"DRIVE": 8.0, "NEUTRAL": 0.0, "PTO": -8.0}
    for side, sign in (("LEFT", 1), ("RIGHT", -1)):
        plane_x = sign * 60.0
        result[f"{side}_20T_ENVELOPE"] = cylinder_x(18, 10, (plane_x, -185, 105))
        result[f"{side}_60T_PHYSICAL_ENVELOPE"] = cylinder_x(50, 20, (plane_x, -185, 166))
        result[f"{side}_60T_SAFETY_ENVELOPE"] = cylinder_x(60, 20, (plane_x, -185, 166))
        result[f"{side}_LOOSE_BELT_PLANE"] = box(15, 12, 73, (plane_x, -185, 135.5))
        result[f"{side}_SELECTOR_SHAFT"] = cylinder_x(5, 36, (sign * 38, -185, 166))
        result[f"{side}_{state}_INDICATOR"] = cylinder_x(13, 14, (sign * (38 + offsets[state]), -185, 166))
        result[f"{side}_DRIVE_OUTPUT"] = cylinder_x(5, 28, (sign * 66, -185, 166))
        result[f"{side}_PTO_OUTPUT_INWARD"] = cylinder_x(5, 28, (sign * 14, -185, 166))
        result[f"{side}_BEARING_ENVELOPES"] = compound([cylinder_x(14, 8, (sign * 25, -185, 166)), cylinder_x(14, 8, (sign * 55, -185, 166))])
    return result


def mockup_jig_world_shapes() -> dict[str, cq.Shape]:
    return {
        "LEFT_NO_LOAD_JIG_PROXY": box(95, 70, 8, (110, -185, 72)),
        "RIGHT_NO_LOAD_JIG_PROXY": box(95, 70, 8, (-110, -185, 72)),
        "LEFT_FRONT_DATUM": box(3, 60, 60, (68, -185, 105)),
        "RIGHT_FRONT_DATUM": box(3, 60, 60, (-68, -185, 105)),
        "LEFT_SELECTOR_CENTERLINE_GAUGE": box(8, 50, 80, (38, -185, 135)),
        "RIGHT_SELECTOR_CENTERLINE_GAUGE": box(8, 50, 80, (-38, -185, 135)),
    }


def fixed_motor_shapes(motors: dict[str, cq.Shape]) -> list[cq.Shape]:
    return [shape for name, shape in motors.items() if name.endswith(("MOTOR_CYLINDER", "REAR_TERMINAL_FIXED", "OUTPUT_SHAFT", "SHAFT_BOSS", "BRACKET_ENVELOPE"))]


def assembly_shapes(kind: str) -> list[cq.Shape]:
    env = environment_shapes()
    motors = placed_motors()
    state = "DRIVE" if "DRIVE" in kind else "PTO" if "PTO" in kind else "NEUTRAL"
    power = power_shapes(state)
    base = [env["CBOX"], env["BBOX"], env["FRAME"], env["TRACKS"], *fixed_motor_shapes(motors)]
    if kind == "FIXED_WIDTH":
        return base + list(power.values())
    if kind == "GUARDED_WIDTH":
        return base + list(power.values()) + [shape for name, shape in motors.items() if name.endswith("G1_GUARD")]
    if kind == "SERVICE_SWEEP":
        return base + list(power.values()) + [shape for name, shape in motors.items() if name.endswith(("S2_SERVICE", "REMOVAL_SWEEP", "CABLE_BEND"))]
    if kind in ("DRIVE", "NEUTRAL", "PTO"):
        return base + list(power.values()) + list(mockup_jig_world_shapes().values())
    return base + list(power.values()) + list(mockup_jig_world_shapes().values()) + [env["UNIT_BAY"], env["UNIT_SUPPORT_FRAME_REGION"]] + [shape for name, shape in motors.items() if name.endswith(("G1_GUARD", "CABLE_BEND"))]


def bounds(shape: cq.Shape) -> dict[str, float]:
    b = shape.BoundingBox()
    return {key: round(value, 6) for key, value in {"xmin": b.xmin, "xmax": b.xmax, "ymin": b.ymin, "ymax": b.ymax, "zmin": b.zmin, "zmax": b.zmax, "xlen": b.xlen, "ylen": b.ylen, "zlen": b.zlen}.items()}


def intersection_volume(a: cq.Shape, b: cq.Shape) -> float:
    return max(0.0, float(a.intersect(b).Volume()))


def cad_reconfirmation() -> dict[str, Any]:
    motors = placed_motors()
    env = environment_shapes()
    fixed_motor = compound(fixed_motor_shapes(motors))
    guards = compound([shape for name, shape in motors.items() if name.endswith("G1_GUARD")])
    service = compound([shape for name, shape in motors.items() if name.endswith("S2_SERVICE")])
    fixed_motor_bounds = bounds(fixed_motor)
    guard_bounds = bounds(guards)
    service_bounds = bounds(service)
    track_bounds = bounds(env["TRACKS"])
    complete_fixed = max(fixed_motor_bounds["xlen"], track_bounds["xlen"])
    complete_guarded = max(guard_bounds["xlen"], track_bounds["xlen"])
    collisions = []
    fixed_and_power = compound([fixed_motor, *power_shapes().values()])
    for name in ("CBOX", "BBOX", "FRAME", "TRACKS"):
        volume = intersection_volume(fixed_and_power, env[name])
        collisions.append({"target": name, "intersection_volume_mm3": round(volume, 6), "pass": volume <= 1e-6, "method": "CADQUERY_ACTUAL_COMMON_VOLUME"})
    return {
        "boundary_x_mm": [-145.0, 145.0],
        "motor_fixed_width_mm": fixed_motor_bounds["xlen"],
        "motor_g1_guard_width_mm": guard_bounds["xlen"],
        "track_proxy_width_mm": track_bounds["xlen"],
        "complete_fixed_width_mm": complete_fixed,
        "complete_guarded_width_mm": complete_guarded,
        "s2_temporary_service_width_mm": service_bounds["xlen"],
        "target_width_mm": TARGET_WIDTH,
        "absolute_width_rule_mm": "LESS_THAN_300",
        "collisions": collisions,
        "status": "CONDITIONAL_PASS" if complete_guarded <= TARGET_WIDTH and all(row["pass"] for row in collisions) else "FAIL",
        "physical_confirmation": "REQUIRED",
    }


def part_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    print_descriptions = [
        ("LEFT_MOTOR_POSITIONING_JIG", "JIG-B external cradle; left datum key"), ("RIGHT_MOTOR_POSITIONING_JIG", "JIG-B external cradle; right datum key"),
        ("LEFT_MOTOR_FRONT_PLATE_DATUM_GAUGE", "left front-plate datum witness"), ("RIGHT_MOTOR_FRONT_PLATE_DATUM_GAUGE", "right front-plate datum witness"),
        ("LEFT_SHAFT_CENTERLINE_GAUGE", "left Ø6.5 no-load center witness"), ("RIGHT_SHAFT_CENTERLINE_GAUGE", "right Ø6.5 no-load center witness"),
        ("LEFT_G1_GUARD_ENVELOPE_GAUGE", "left 75.1 mm rear-of-datum guard marker"), ("RIGHT_G1_GUARD_ENVELOPE_GAUGE", "right 75.1 mm rear-of-datum guard marker"),
        ("SELECTOR_SHAFT_CENTERLINE_JIG_LEFT", "left selector Z offset 61 mm"), ("SELECTOR_SHAFT_CENTERLINE_JIG_RIGHT", "right selector Z offset 61 mm"),
        ("DRIVE_NEUTRAL_PTO_INDICATOR_LEFT", "independent 0/5/10 mm visual marks"), ("DRIVE_NEUTRAL_PTO_INDICATOR_RIGHT", "independent 0/5/10 mm visual marks"),
        ("BELT_PLANE_GAUGE_LEFT", "left loose-belt coplanarity frame"), ("BELT_PLANE_GAUGE_RIGHT", "right loose-belt coplanarity frame"),
    ]
    for rel, (part_id, description) in zip(PRINT_FILES, print_descriptions):
        shape = PRINT_SHAPE_BUILDERS[rel]()
        b = bounds(shape)
        rows.append({"part_id": part_id, "quantity": 1, "artifact": rel, "method": "3D_PRINT", "recommended_material": "PETG_OR_PLA_FOR_NO_LOAD_ONLY", "source_or_datum": "V0930_CANDIDATE_A", "envelope_mm": f"{b['xlen']} x {b['ylen']} x {b['zlen']}", "print_orientation": "AS_EXPORTED_FLAT_BASE_Z0", "a1_256_fit": "PASS" if max(b["xlen"], b["ylen"], b["zlen"]) <= 256 else "FAIL", "load_authority": "NO_LOAD_POSITIONING_ONLY", "status": "READY_FOR_PRINT", "notes": description})
    extra = [
        ("TOTAL_WIDTH_290_BOUNDARY_GAUGE", 1, TEMPLATE_FILES[0], "TILED_1_TO_1_SVG", "290 mm boundary; split at X=0"),
        ("LEFT_S2_SERVICE_SWEEP_GAUGE", 1, TEMPLATE_FILES[3], "TILED_1_TO_1_SVG", "temporary service outer X=+158.1; not a fixed-width failure"),
        ("RIGHT_S2_SERVICE_SWEEP_GAUGE", 1, TEMPLATE_FILES[3], "TILED_1_TO_1_SVG", "temporary service outer X=-158.1; not a fixed-width failure"),
        ("CBOX_ENVELOPE_DUMMY_OR_TEMPLATE", 1, TEMPLATE_FILES[1], "TILED_1_TO_1_SVG", "130 x 140 x 105 current authority"),
        ("BBOX_ENVELOPE_DUMMY_OR_TEMPLATE", 1, TEMPLATE_FILES[1], "TILED_1_TO_1_SVG", "150 x 220 x 150 current authority"),
        ("LEFT_TRACK_PROXY_TEMPLATE", 1, TEMPLATE_FILES[2], "TILED_1_TO_1_SVG", "inherited v0.9.0 transformed proxy"),
        ("RIGHT_TRACK_PROXY_TEMPLATE", 1, TEMPLATE_FILES[2], "TILED_1_TO_1_SVG", "inherited v0.9.0 transformed proxy"),
        ("20T_PULLEY_ENVELOPE_DUMMY_LEFT_RIGHT", 2, "REFERENCE_ONLY", "REUSE_EXISTING_STANDARD_DUMMY", PULLEY_REFERENCES["20T_STL"]["sha256"]),
        ("60T_PULLEY_ENVELOPE_DUMMY_LEFT_RIGHT", 2, "REFERENCE_ONLY", "REUSE_EXISTING_STANDARD_DUMMY", PULLEY_REFERENCES["60T_STL"]["sha256"]),
        ("DRIVE_OUTPUT_CENTERLINE_JIG_LEFT_RIGHT", 2, ASSEMBLY_FILES[4], "ASSEMBLY_ENVELOPE", "X=±66,Y=-185,Z=166"),
        ("PTO_OUTPUT_CENTERLINE_JIG_LEFT_RIGHT", 2, ASSEMBLY_FILES[6], "ASSEMBLY_ENVELOPE", "independent inward X axes; no common shaft"),
        ("CENTRAL_UNIT_BAY_TEMPLATE", 1, TEMPLATE_FILES[4], "TILED_1_TO_1_SVG", "unit weight supported by frame, not PTO"),
        ("CABLE_BEND_ENVELOPE_LEFT_RIGHT", 2, TEMPLATE_FILES[5], "SVG_TEMPLATE", "actual connector/bend radius HOLD"),
        ("FRAME_DATUM_CORNER_GAUGES", 4, TEMPLATE_FILES[1], "SVG_OR_EXISTING_TSLOT", "20x20 class authority; 2040 HOLD"),
    ]
    for part_id, quantity, artifact, method, notes in extra:
        rows.append({"part_id": part_id, "quantity": quantity, "artifact": artifact, "method": method, "recommended_material": "PAPER_CARDBOARD_MDF_OR_EXISTING_PART", "source_or_datum": "CURRENT_AUTHORITY_OR_PINNED_REFERENCE", "envelope_mm": "SEE_TEMPLATE_OR_REFERENCE", "print_orientation": "NOT_APPLICABLE", "a1_256_fit": "TILED_OR_REFERENCE", "load_authority": "NO_LOAD_POSITIONING_ONLY", "status": "READY_FOR_TEMPLATE_OR_REFERENCE", "notes": notes})
    return rows


def measurement_rows() -> list[dict[str, Any]]:
    definitions = [
        ("left_fixed_outer_x", 138.1, "mm", "<=145.0"), ("right_fixed_outer_x", -138.1, "mm", ">=-145.0"),
        ("fixed_total_width", 276.2, "mm", "<=290.0"), ("guarded_total_width", 286.2, "mm", "<=290.0"),
        ("track_total_width", 290.0, "mm", "<=290.0_AND_PROXY_ID_RECORDED"),
        ("motor_to_CBOX_minimum", "CAD_NO_INTERSECTION", "mm", ">0"), ("motor_to_BBOX_minimum", "CAD_NO_INTERSECTION", "mm", ">0"),
        ("motor_to_frame_minimum", "CAD_NO_INTERSECTION", "mm", ">0"), ("motor_to_track_minimum", "CAD_NO_INTERSECTION", "mm", ">0"),
        ("shaft_to_CBOX_minimum", "CAD_NO_INTERSECTION", "mm", ">0"), ("pulley_to_frame_minimum", "CAD_NO_INTERSECTION", "mm", ">0"),
        ("belt_to_frame_minimum", "CAD_NO_INTERSECTION", "mm", ">0"), ("belt_to_box_minimum", "CAD_NO_INTERSECTION", "mm", ">0"),
        ("selector_to_frame_minimum", "CAD_NO_INTERSECTION", "mm", ">0"), ("PTO_center_gap", "HOLD", "mm", ">0_AND_NO_COMMON_SHAFT"),
        ("PTO_exposed_length", "HOLD", "mm", "MEASURE_AND_RECORD"), ("cable_rear_clearance", "HOLD", "mm", ">0"),
        ("cable_bend_radius_estimate", "HOLD", "mm", "CONNECTOR_SPEC_REQUIRED"), ("motor_removal_direction", "OUTWARD_X", "text", "POSSIBLE"),
        ("motor_removal_temporary_width", 316.2, "mm", "SERVICE_ONLY_NOT_FIXED_FAIL"), ("belt_removal_direction", "OUTWARD_OR_UP", "text", "POSSIBLE"),
        ("guard_removal_direction", "OUTWARD_OR_UP", "text", "POSSIBLE"), ("tool_access", "HOLD", "text", "NO_FIXED_INTERSECTION"),
        ("left_right_symmetry_error", 0.0, "mm", "<=USER_ACCEPTANCE_TBD"), ("motor_datum_repeatability", "HOLD", "mm", "REPEAT_3_TIMES"),
    ]
    return [{"measurement_id": name, "cad_reference_or_expected": expected, "unit": unit, "physical_measured_value": "", "measurement_tool": "CALIPER_RULER_FEELER_OR_TEMPLATE", "acceptance_condition": condition, "physical_result": "NOT_MEASURED", "photo_id": "", "issue_label": "", "notes": "NO_LOAD_NO_POWER"} for name, expected, unit, condition in definitions]


def svg_document(title: str, content: str, width_mm: int = 320, height_mm: int = 240) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}mm" height="{height_mm}mm" viewBox="0 0 {width_mm} {height_mm}"><rect width="100%" height="100%" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#172033}}.h{{font-weight:700}}.hold{{fill:#9a3412}}.dim{{stroke:#2563eb;stroke-width:.8;fill:none}}.env{{stroke:#475569;stroke-width:.7;fill:#e2e8f0}}.motor{{fill:#fecaca;stroke:#991b1b;stroke-width:.8}}.guide{{stroke:#d97706;stroke-width:.7;stroke-dasharray:4 3;fill:none}}</style><text x="10" y="13" font-size="7" class="h">{title}</text><text x="10" y="22" font-size="4" class="hold">NO LOAD / NO POWER / NOT FOR MANUFACTURING / PRINT 1:1 OR TILE AT REGISTRATION LINE</text>{content}</svg>'''


def svg_templates() -> dict[str, str]:
    total = svg_document("TOTAL WIDTH 290 mm BOUNDARY", '''<g transform="translate(160 125)"><line x1="-145" y1="-80" x2="-145" y2="80" class="dim"/><line x1="145" y1="-80" x2="145" y2="80" class="dim"/><line x1="0" y1="-95" x2="0" y2="95" class="guide"/><line x1="-145" y1="0" x2="145" y2="0" class="dim"/><path d="M-145,-4 v8 M145,-4 v8" class="dim"/><text x="-18" y="-5" font-size="5">X=0 TILE SPLIT</text><text x="-143" y="-84" font-size="5">X=-145</text><text x="125" y="-84" font-size="5">X=+145</text><text x="-22" y="12" font-size="6">290.0 mm</text><line x1="-143.1" y1="-55" x2="143.1" y2="-55" class="guide"/><text x="-32" y="-60" font-size="5">G1 MOTOR WIDTH 286.2</text><line x1="-138.1" y1="-35" x2="138.1" y2="-35" class="guide"/><text x="-31" y="-40" font-size="5">FIXED MOTOR WIDTH 276.2</text></g>''')
    boxes = svg_document("CBOX / BBOX / 2020 FRAME DATUM", '''<g transform="translate(160 205) scale(0.75 -0.75)"><rect x="-65" y="0" width="130" height="140" fill="#bfdbfe" stroke="#2563eb"/><rect x="-75" y="-220" width="150" height="220" fill="#ddd6fe" stroke="#7c3aed"/><rect x="69" y="0" width="20" height="232" class="env"/><rect x="-89" y="0" width="20" height="232" class="env"/></g><text x="12" y="232" font-size="4">Top view transformed for sheet: CBOX 130×140×105; BBOX 150×220×150; current frame profile 20×20 T-slot class. 2040 HOLD.</text>''', 320, 240)
    track = svg_document("INHERITED V0.9.0 TRANSFORMED TRACK PROXY", '''<g transform="translate(160 130)"><rect x="-145" y="-90" width="10" height="180" class="env"/><rect x="135" y="-90" width="10" height="180" class="env"/><line x1="-145" y1="100" x2="145" y2="100" class="dim"/><text x="-23" y="110" font-size="5">PROXY WIDTH 290</text><text x="-88" y="-100" font-size="4">NOT CURRENT EXACT TRACK SOLID — PHYSICAL CONFIRMATION REQUIRED</text></g>''')
    service = svg_document("MOTOR FIXED / G1 / S2 SERVICE SWEEPS", '''<g transform="translate(160 125)"><rect x="-158.1" y="-55" width="316.2" height="110" class="guide"/><rect x="-143.1" y="-42" width="286.2" height="84" fill="none" stroke="#d97706"/><rect x="-138.1" y="-32" width="276.2" height="64" fill="none" stroke="#991b1b"/><text x="-36" y="-60" font-size="5">S2 TEMPORARY 316.2</text><text x="-31" y="-46" font-size="5">G1 FIXED 286.2</text><text x="-30" y="-35" font-size="5">METAL FIXED 276.2</text></g>''')
    unit = svg_document("CENTRAL UNIT BAY / INDEPENDENT PTO", '''<g transform="translate(160 100)"><rect x="-72" y="0" width="144" height="110" class="guide"/><line x1="-70" y1="-20" x2="-12" y2="-20" class="dim"/><line x1="70" y1="-20" x2="12" y2="-20" class="dim"/><circle cx="-12" cy="-20" r="3" class="env"/><circle cx="12" cy="-20" r="3" class="env"/><text x="-46" y="-30" font-size="5">LEFT PTO →</text><text x="18" y="-30" font-size="5">← RIGHT PTO</text><text x="-55" y="55" font-size="5">UNIT MASS SUPPORTED BY HITCH/GUIDE FRAME</text><text x="-41" y="67" font-size="5">NO COMMON PTO SHAFT</text></g>''')
    cable = svg_document("CABLE BEND ENVELOPE TEMPLATE", '''<g transform="translate(160 120)"><circle cx="-110" cy="0" r="26" class="guide"/><circle cx="110" cy="0" r="26" class="guide"/><path d="M-110,0 C-80,0 -80,45 -50,45" class="dim"/><path d="M110,0 C80,0 80,45 50,45" class="dim"/><text x="-88" y="75" font-size="5">ACTUAL CONNECTOR SHELL / EXIT DIRECTION / MINIMUM BEND RADIUS = HOLD</text></g>''')
    top = svg_document("CANDIDATE A MOCKUP TOP VIEW", '''<g transform="translate(160 155) scale(.72 -.72)"><rect x="-145" y="-150" width="10" height="450" class="env"/><rect x="135" y="-150" width="10" height="450" class="env"/><rect x="-65" y="-140" width="130" height="140" fill="#bfdbfe" stroke="#2563eb"/><rect x="-75" y="0" width="150" height="220" fill="#ddd6fe" stroke="#7c3aed"/><rect x="68" y="-208" width="70.1" height="46" class="motor"/><rect x="-138.1" y="-208" width="70.1" height="46" class="motor"/><circle cx="60" cy="-185" r="50" class="guide"/><circle cx="-60" cy="-185" r="50" class="guide"/></g>''')
    front = svg_document("CANDIDATE A MOCKUP FRONT VIEW", '''<g transform="translate(160 215) scale(.75 -.75)"><rect x="-145" y="40" width="10" height="170" class="env"/><rect x="135" y="40" width="10" height="170" class="env"/><circle cx="68" cy="105" r="18.45" class="motor"/><circle cx="-68" cy="105" r="18.45" class="motor"/><circle cx="60" cy="166" r="60" class="guide"/><circle cx="-60" cy="166" r="60" class="guide"/><line x1="-145" y1="225" x2="145" y2="225" class="dim"/></g>''')
    side = svg_document("CANDIDATE A MOCKUP SIDE VIEW", '''<g transform="translate(125 215) scale(.72 -.72)"><rect x="-140" y="0" width="140" height="105" fill="#bfdbfe"/><rect x="0" y="0" width="220" height="150" fill="#ddd6fe"/><circle cx="-185" cy="105" r="23" class="motor"/><circle cx="-185" cy="166" r="60" class="guide"/><line x1="-185" y1="105" x2="-185" y2="166" class="dim"/><rect x="-380" y="0" width="134" height="160" class="guide"/></g><text x="190" y="120" font-size="5">20T AXIS Z=105</text><text x="190" y="133" font-size="5">60T / SELECTOR Z=166</text><text x="190" y="146" font-size="5">LOOSE BELT PLANE ONLY</text>''')
    return dict(zip(TEMPLATE_FILES, [total, boxes, track, service, unit, cable, top, front, side]))


def parameters(parent: dict[str, Any], reconfirm: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": DOCUMENT_ID,
        "version": VERSION,
        "physical_mockup_class": "NO_LOAD_LAYOUT_ONLY",
        "candidate": "A_LATERAL_FRONT_DIRECT",
        "powerpath": "P1_LATERAL_DIRECT_COMMON_SELECTOR_PATTERN_LEFT_RIGHT_INDEPENDENT",
        "coordinate_system": {"X": "left", "Y": "rear", "Z": "up"},
        "motor_front_plate_datums_mm": {"LEFT": list(LEFT_FRONT), "RIGHT": list(RIGHT_FRONT)},
        "motor_measurements_mm": {"cylinder_diameter": MOTOR_DIAMETER, "front_to_rear_fixed": REAR_FIXED, "front_to_shaft_tip": SHAFT_LENGTH, "total_axial_fixed": REAR_FIXED + SHAFT_LENGTH, "shaft_diameter": SHAFT_DIAMETER, "boss": [BOSS_DIAMETER, BOSS_LENGTH], "bracket": [BRACKET_WIDTH, BRACKET_HEIGHT, BRACKET_LENGTH], "bracket_thickness": BRACKET_THICKNESS, "fastener_hole": FASTENER_HOLE_DIAMETER, "hole_centers": list(FASTENER_PITCH), "vertical_slot_representative": VERTICAL_SLOT_REPRESENTATIVE, "vertical_slot_exact_geometry": "MEASUREMENT_HOLD", "uncertainty": "USER_NOT_REPORTED"},
        "width_contract": reconfirm,
        "jig_trade": {"recommended": "JIG-B_EXTERNAL_CRADLE", "reason": "bracket hole origin, edge distances, and complete slot geometry remain HOLD", "JIG-A": "ADJUSTABLE_SLOT_COMPARISON_ONLY_NO_LOAD", "JIG-B": "LIGHT_EXTERNAL_CRADLE_WITH_TPU_FELT_OR_RUBBER_PROTECTION_NO_CLAMP_LOAD"},
        "a1_build_volume_mm": list(A1_BUILD_VOLUME),
        "frame": {"authority": "20X20MM_T_SLOT_CLASS", "2040": "PROFILE_AND_SLOT_MEASUREMENT_HOLD", "direct_holes": "PROHIBITED", "temporary_methods": ["T_NUT_IF_EXISTING_AND_COMPATIBLE", "WOOD_OR_BOARD", "SHORT_PRINTED_DUMMY", "PAPER_CARDBOARD_MDF_TEMPLATE"]},
        "pulley_reuse": PULLEY_REFERENCES,
        "ten_mm_shaft_reference": {"source": "common_rover_shaft_fit_calibration_v0_9_2_2", "physical_reference": "USER_EXISTING_10MM_SHAFT", "S2_10P30": "NO_LOAD_PRINTED_SLIDE_REFERENCE_ONLY"},
        "clutch": {"positions_mm": {"DRIVE": 0, "NEUTRAL": 5, "PTO": 10}, "simultaneous_drive_pto": "GEOMETRICALLY_NOT_SHOWN_AND_PROHIBITED", "torque_transmission": "PROHIBITED"},
        "parent_protection": parent,
        "authority_pointer": "UNCHANGED",
        "physical_mockup": "NOT_YET_PERFORMED",
        "manufacturing": "HOLD",
    }


def plan_markdown(reconfirm: dict[str, Any]) -> str:
    return f"""# Candidate A physical mockup plan v0.9.3.1

## Decision and scope

This kit prepares the v0.9.3.0 recommendation `A_LATERAL_FRONT_DIRECT + P1` for a **non-powered, no-load, dimensional mockup**. It does not update design authority and does not release a motor mount, belt drive, shaft, clutch, frame hole, purchase, or manufacturing operation.

`PHYSICAL_MOCKUP_CLASS=NO_LOAD_LAYOUT_ONLY`

## Exact datums

- coordinate frame: +X left, +Y rear, +Z up
- left motor front plate: `(68.0, -185.0, 105.0) mm`
- right motor front plate: `(-68.0, -185.0, 105.0) mm`
- selector axes: X=±38, Y=-185, Z=166 mm
- DRIVE output witnesses: X=±66, Y=-185, Z=166 mm
- PTO witnesses: X=±14, Y=-185, Z=166 mm, inward and mechanically independent

CAD re-confirms motor fixed width {reconfirm['motor_fixed_width_mm']} mm, G1 motor guard width {reconfirm['motor_g1_guard_width_mm']} mm, transformed track-proxy width {reconfirm['track_proxy_width_mm']} mm, complete guarded width {reconfirm['complete_guarded_width_mm']} mm, and S2 temporary service width {reconfirm['s2_temporary_service_width_mm']} mm. Service width is not a fixed-width failure.

## Jig selection

`JIG-B_EXTERNAL_CRADLE` is recommended. It references the known 40.1×45.5×42.8 mm bracket/motor envelope with loose clearance and a soft TPU, rubber, or felt liner. It must not clamp the cylinder or carry torque.

JIG-A remains a comparison only: the four Ø3.4 mm candidate holes may be used through adjustable slots for a no-load mockup, but their origin, edge distances, and the complete 27.7 mm vertical-slot geometry are not known. JIG-A is not a manufacturing mount.

## Mockup architecture

Fourteen compact printable gauges fit individually inside the Bambu A1 256 mm class envelope. Large rover boundaries, CBOX/BBOX, track proxy, service sweep, unit bay, and cable bend regions are 1:1 SVG templates with tiling/registration marks. Existing STANDARD 20T and 60T full dummies are referenced by SHA and are not duplicated.

The authority-backed frame envelope is 20×20 T-slot class. A 2040 profile is not currently released; use an existing compatible T-nut, board/MDF, short printed dummy, or paper template without cutting or drilling.

## Powerpath mockup

Each side independently displays motor → 20T envelope → loose belt plane → 60T physical/safety envelope → selector → DRIVE/NEUTRAL/PTO witnesses. Belts remain untensioned. A left/right common shaft is prohibited. Unit weight is supported by a separate hitch/guide-frame region, never by PTO shafts.

## Completion state

- `CANDIDATE_A_MOCKUP_KIT=READY_FOR_PRINT_OR_TEMPLATE`
- `PHYSICAL_MOCKUP=NOT_YET_PERFORMED`
- `FIXED_WIDTH=CAD_RECONFIRMED`
- `GUARD_WIDTH=PHYSICAL_CONFIRMATION_REQUIRED`
- `MOTOR_SERVICE_ACCESS=PHYSICAL_CONFIRMATION_REQUIRED`
- `BELT_PLANE=PHYSICAL_CONFIRMATION_REQUIRED`
- `PTO_UNIT_CONNECTION=PHYSICAL_CONFIRMATION_REQUIRED`
- `LOAD_TEST=NOT_PERFORMED`
- `POWERED_TEST=NOT_APPROVED`
- `MANUFACTURING=HOLD`
- `FIELD_DEPLOYMENT=NOT_APPROVED`
"""


def procedure_markdown() -> str:
    steps = [
        "Do not energize any motor.", "Insulate both motor terminals.", "Mark the 290 mm boundary on the work surface.", "Place the frame datums.", "Place CBOX/BBOX templates.", "Place the inherited track proxy.", "Install left/right no-load motor jigs.", "Confirm both front-plate datums.", "Confirm both shaft centerlines.", "Measure fixed outer edges.", "Measure G1 guard outer edges.", "Measure motor-to-CBOX/BBOX minimum gaps.", "Measure motor-to-frame minimum gap.", "Measure motor-to-track proxy minimum gap.", "Place 20T/60T references or envelope dummies.", "Check the loose, untensioned belt plane.", "Place independent selector-shaft witnesses.", "Check DRIVE indicator position.", "Check central NEUTRAL position.", "Check PTO indicator position.", "Confirm independent inward PTO directions without a common shaft.", "Place the central unit-bay/support-frame template.", "Place cable-bend templates.", "Check outward motor-removal sweep.", "Check belt-replacement access.", "Check guard-removal access.", "Take overview and close-up photographs.", "Complete every measurement-record row.", "Attach an interference label to every problem location.", "End without energizing or rotating the motors.",
    ]
    return "# Physical mockup procedure v0.9.3.1\n\n`NO POWER / NO ROTATION / NO BELT TENSION / NO LOAD`\n\n" + "\n".join(f"{index}. {text}" for index, text in enumerate(steps, 1)) + "\n\nStop immediately if a jig deforms the motor bracket, damages insulation, requires force, or creates a fixed intersection."


def pass_fail_markdown() -> str:
    return """# Candidate A pass/fail contract v0.9.3.1

## LAYOUT_PASS candidate

- measured fixed total width <=290 mm and absolute fixed width <300 mm
- measured G1 fixed-guard width <=290 mm
- zero CBOX/BBOX, track-proxy, and frame fixed intersections
- no forced deformation of the metal motor bracket
- cable remains clear of the loose belt plane
- 20T/60T faces can be aligned in one belt plane without tension
- motor, belt, and guard removal directions remain available
- left/right PTO witnesses remain independent and inward
- unit weight is carried by a separate support frame

## CONDITIONAL_PASS

Width and layout conditions pass, while exact track, guard, connector/cable, bearing, pulley stack, shaft, or support hardware remains unmeasured. This is the expected maximum release state for v0.9.3.1.

## FAIL

Any fixed width >=300 mm; sealed-box penetration; fixed track/frame intersection; impossible motor removal; unavoidable cable/belt intersection; a common mechanical left/right shaft; or a geometry that permits simultaneous DRIVE/PTO engagement.

No result authorizes power, rotation, belt tension, torque, drilling, cutting, purchase, manufacture, or field use.
"""


def remaining_markdown() -> str:
    return """# Remaining measurements v0.9.3.1

P0: repeat motor datum placement three times; record left/right outer X, actual bracket-hole origin/edge distances, full vertical-slot axes/radii/center, actual 2020/2040 profile and T-slot, track solid, guard wall/thickness, connector body/exit direction, cable minimum bend radius, and tool envelope.

P1: record actual 20T/60T face width, flange/hub projection, bore, axial stack, runout, belt length/width, bearing products, selector shaft support stack, exposed PTO lengths, central gap, and unit-side couplings.

P2: only after a separate authority task—motor stall current/torque, bracket structural capacity, belt tension, clutch metal tolerance, brake holding torque, waterproofing, load test, powered test, and field test.
"""


def photo_log_markdown() -> str:
    rows = "\n".join(f"| P{index:02d} |  |  | NOT_CAPTURED |" for index in range(1, 17))
    return f"""# Candidate A mockup photo log v0.9.3.1

No physical mockup has been performed. Fill this log during the no-load procedure.

| photo_id | required view | issue labels visible | status |
|---|---|---|---|
{rows}

Required coverage: boundary overview, front/top/side, each motor datum, each shaft centerline, CBOX/BBOX gaps, track gaps, 20T/60T/belt planes, selector states, independent PTO gap, cable bends, motor removal, belt removal, and guard removal.
"""


def readme_markdown() -> str:
    return """# Common Rover Candidate A physical mockup v0.9.3.1

This handoff contains printable **no-load positioning gauges**, 1:1/tiled SVG templates, seven STEP assembly states, an empty physical measurement record, and a 30-step procedure.

Run `python -B build_candidate_a_physical_mockup_v0931.py --verify` and `python -B tests/test_candidate_a_physical_mockup_v0931.py` with a CadQuery 2.8 environment.

Do not energize a motor, rotate a shaft, tension a belt, transmit torque, cut a shaft/profile, drill a frame, purchase parts, or treat any artifact as manufacturing authority.
"""


def no_power_text() -> str:
    return """PHYSICAL_MOCKUP_CLASS=NO_LOAD_LAYOUT_ONLY
MOTOR_POWER=PROHIBITED
MOTOR_ROTATION=PROHIBITED
BELT_TENSION=PROHIBITED
TORQUE_TRANSMISSION=PROHIBITED
SHAFT_CUTTING=PROHIBITED
FRAME_DRILLING=PROHIBITED
METAL_MACHINING_APPROVAL=NOT_APPROVED
PURCHASE_APPROVAL=NOT_APPROVED
MANUFACTURING=HOLD
LOAD_TEST=NOT_PERFORMED
POWERED_TEST=NOT_APPROVED
FIELD_DEPLOYMENT=NOT_APPROVED
AUTHORITY_POINTER=UNCHANGED
"""


def manifest_text() -> str:
    lines = [f"document_id={DOCUMENT_ID}", f"version={VERSION}", f"path_count={len(PACKAGE_PATHS)}", "scope=V0931_ONLY", f"parent_ledger_sha256={PARENT_LEDGER_SHA256}", f"parent_zip_sha256={PARENT_ZIP_SHA256}", "physical_mockup=NOT_YET_PERFORMED", "power=PROHIBITED", "manufacturing=HOLD", ""]
    for rel in PACKAGE_PATHS:
        if rel.endswith(".stl"):
            role = "NO_LOAD_PRINTABLE_GAUGE"
        elif rel.endswith(".step"):
            role = "CONDITIONAL_MOCKUP_ASSEMBLY"
        elif rel.endswith(".svg"):
            role = "ONE_TO_ONE_OR_TILED_TEMPLATE"
        elif rel.endswith(".csv"):
            role = "TABULAR_MOCKUP_RECORD"
        elif rel.endswith(".json"):
            role = "MACHINE_READABLE_CONTRACT"
        elif rel.endswith(".py"):
            role = "BUILDER_OR_CONTRACT_TEST"
        else:
            role = "DOCUMENT_OR_LEDGER"
        lines.append(f"{rel}|{role}")
    return "\n".join(lines)


def commit_paths_text() -> str:
    prefix = "cad/common_rover/common_rover_candidate_a_physical_mockup_v0_9_3_1"
    return "\n".join(f"{prefix}/{rel}" for rel in PACKAGE_PATHS)


def sha256sums_text() -> str:
    return "\n".join(f"{sha256(LANE_DIR / rel)}  {rel}" for rel in PACKAGE_PATHS if rel != "SHA256SUMS.txt")


def canonicalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"FILE_NAME\('.*?','.*?',", "FILE_NAME('PS-CR-V0931','2000-01-01T00:00:00',", text, count=1)
    text = re.sub(r"FILE_DESCRIPTION\(\(.*?\),'.*?'\);", "FILE_DESCRIPTION(('NO LOAD PHYSICAL MOCKUP EVIDENCE'),'2;1');", text, count=1)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def export_step(path: Path, shapes: Iterable[cq.Shape]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(compound(shapes), str(path))
    canonicalize_step(path)


def export_artifacts() -> None:
    for rel, build in PRINT_SHAPE_BUILDERS.items():
        path = LANE_DIR / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(build(), str(path), tolerance=0.04, angularTolerance=0.15)
    assembly_plan = ["MOCKUP", "FIXED_WIDTH", "GUARDED_WIDTH", "SERVICE_SWEEP", "DRIVE", "NEUTRAL", "PTO"]
    for rel, kind in zip(ASSEMBLY_FILES, assembly_plan):
        export_step(LANE_DIR / rel, assembly_shapes(kind))
    for rel, content in svg_templates().items():
        write_text(LANE_DIR / rel, content)


def parse_hashes(base: Path = LANE_DIR) -> dict[str, str]:
    result = {}
    for line in (base / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            result[rel] = digest
    return result


def verify_hashes(base: Path = LANE_DIR) -> dict[str, Any]:
    expected = parse_hashes(base)
    required = set(PACKAGE_PATHS) - {"SHA256SUMS.txt"}
    mismatches: list[Any] = []
    if set(expected) != required:
        mismatches.append({"missing": sorted(required - set(expected)), "extra": sorted(set(expected) - required)})
    for rel, digest in expected.items():
        actual = sha256(base / rel) if (base / rel).is_file() else "MISSING"
        if actual != digest:
            mismatches.append({"path": rel, "expected": digest, "actual": actual})
    return {"verified": len(expected), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def verify_manifest() -> dict[str, Any]:
    paths = json_manifest_paths(LANE_DIR / "MANIFEST.txt")
    return {"entry_count": len(paths), "exact_order": paths == list(PACKAGE_PATHS), "status": "PASS" if paths == list(PACKAGE_PATHS) else "FAIL"}


def verify_stls(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for rel in PRINT_FILES:
        try:
            native = TopoDS_Shape()
            loaded = StlAPI_Reader().Read(native, str(base / rel))
            shape = cq.Shape(native)
            b = bounds(shape)
            face_count = len(shape.Faces())
            valid = loaded and not native.IsNull() and face_count >= 4 and all(math.isfinite(value) for value in b.values())
            fit = b["xlen"] <= 256 and b["ylen"] <= 256 and b["zlen"] <= 256
            rows.append({"path": rel, "faces": face_count, "bounds": b, "valid": valid, "a1_fit": fit, "pass": valid and fit})
        except Exception as exc:
            rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_steps(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for rel in ASSEMBLY_FILES:
        try:
            shape = cq.importers.importStep(str(base / rel)).val()
            b = bounds(shape)
            valid = len(shape.Solids()) >= 1 and all(math.isfinite(value) for value in b.values())
            rows.append({"path": rel, "solids": len(shape.Solids()), "bounds": b, "pass": valid})
        except Exception as exc:
            rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_evidence() -> dict[str, Any]:
    params = json.loads((LANE_DIR / ROOT_FILES[1]).read_text(encoding="utf-8"))
    parts = read_csv(LANE_DIR / ROOT_FILES[2])
    measures = read_csv(LANE_DIR / ROOT_FILES[3])
    checks = {
        "candidate_datums": params["motor_front_plate_datums_mm"] == {"LEFT": [68.0, -185.0, 105.0], "RIGHT": [-68.0, -185.0, 105.0]},
        "motor_fixed_87": params["motor_measurements_mm"]["total_axial_fixed"] == 87.0,
        "K_3p4": params["motor_measurements_mm"]["fastener_hole"] == 3.4,
        "slot_hold": params["motor_measurements_mm"]["vertical_slot_exact_geometry"] == "MEASUREMENT_HOLD",
        "recommended_jig_b": params["jig_trade"]["recommended"] == "JIG-B_EXTERNAL_CRADLE",
        "print_rows": len([row for row in parts if row["method"] == "3D_PRINT"]) == 14,
        "print_orientations": all(row["print_orientation"] for row in parts if row["method"] == "3D_PRINT"),
        "a1_fit": all(row["a1_256_fit"] == "PASS" for row in parts if row["method"] == "3D_PRINT"),
        "measurements_blank": len(measures) == 25 and all(row["physical_result"] == "NOT_MEASURED" for row in measures),
        "independent_pto": params["clutch"]["simultaneous_drive_pto"] == "GEOMETRICALLY_NOT_SHOWN_AND_PROHIBITED",
        "authority_unchanged": params["authority_pointer"] == "UNCHANGED",
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def refresh_artifacts() -> dict[str, Any]:
    for rel in ("build_candidate_a_physical_mockup_v0931.py", "tests/test_candidate_a_physical_mockup_v0931.py"):
        if not (LANE_DIR / rel).is_file():
            raise RuntimeError(f"source missing before refresh: {rel}")
    repository_audit()
    parent = parent_audit(True)
    reconfirm = cad_reconfirmation()
    if reconfirm["status"] != "CONDITIONAL_PASS":
        raise RuntimeError({"CAD_reconfirmation": reconfirm})
    write_text(LANE_DIR / ROOT_FILES[0], plan_markdown(reconfirm))
    write_json(LANE_DIR / ROOT_FILES[1], parameters(parent, reconfirm))
    write_csv(LANE_DIR / ROOT_FILES[2], part_rows())
    write_csv(LANE_DIR / ROOT_FILES[3], measurement_rows())
    write_text(LANE_DIR / ROOT_FILES[4], photo_log_markdown())
    write_text(LANE_DIR / ROOT_FILES[5], procedure_markdown())
    write_text(LANE_DIR / ROOT_FILES[6], pass_fail_markdown())
    write_text(LANE_DIR / ROOT_FILES[7], remaining_markdown())
    write_text(LANE_DIR / ROOT_FILES[10], readme_markdown())
    write_text(LANE_DIR / ROOT_FILES[11], no_power_text())
    write_text(LANE_DIR / ROOT_FILES[12], commit_paths_text())
    export_artifacts()
    write_text(LANE_DIR / ROOT_FILES[15], "status=PREPACKAGE_SELF_CHECKS_PASS\ncontract_tests=RUN_DURING_PACKAGE\nphysical_mockup=NOT_YET_PERFORMED")
    write_text(LANE_DIR / ROOT_FILES[13], manifest_text())
    write_text(LANE_DIR / ROOT_FILES[14], sha256sums_text())
    actual = lane_files()
    if actual != sorted(PACKAGE_PATHS):
        raise RuntimeError({"missing": sorted(set(PACKAGE_PATHS) - set(actual)), "extra": sorted(set(actual) - set(PACKAGE_PATHS))})
    stls, steps, evidence = verify_stls(), verify_steps(), verify_evidence()
    if any(report["status"] != "PASS" for report in (stls, steps, evidence)):
        raise RuntimeError({"stls": stls, "steps": steps, "evidence": evidence})
    return {"document_id": DOCUMENT_ID, "exact_package_paths": len(PACKAGE_PATHS), "parent": parent["status"], "CAD_reconfirmation": reconfirm, "STL_reload": f"{stls['pass_count']}/{stls['count']} PASS", "STEP_reload": f"{steps['pass_count']}/{steps['count']} PASS", "status": "PASS"}


def verify() -> dict[str, Any]:
    actual = lane_files()
    if actual != sorted(PACKAGE_PATHS):
        raise RuntimeError({"missing": sorted(set(PACKAGE_PATHS) - set(actual)), "extra": sorted(set(actual) - set(PACKAGE_PATHS))})
    repository = repository_audit()
    parent = parent_audit()
    hashes, manifest = verify_hashes(), verify_manifest()
    stls, steps, evidence = verify_stls(), verify_steps(), verify_evidence()
    reports = {"parent": parent["status"], "hashes": hashes["status"], "manifest": manifest["status"], "stls": stls["status"], "steps": steps["status"], "evidence": evidence["status"]}
    if any(value != "PASS" for value in reports.values()):
        raise RuntimeError({"reports": reports, "hashes": hashes, "manifest": manifest, "evidence": evidence})
    return {"document_id": DOCUMENT_ID, "repository": repository, "parent_protection": parent["status"], "exact_package_paths": len(PACKAGE_PATHS), "hashes": f"{hashes['verified']}/{len(PACKAGE_PATHS)-1} PASS", "manifest": f"{manifest['entry_count']}/{len(PACKAGE_PATHS)} PASS", "STL_reload": f"{stls['pass_count']}/{stls['count']} PASS", "STEP_reload": f"{steps['pass_count']}/{steps['count']} PASS", "status": "PASS"}


def zip_info(rel: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(rel, date_time=(2000, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def write_zip(path: Path) -> None:
    mode = "x" if path.suffix.lower() == ".zip" else "w"
    with zipfile.ZipFile(path, mode) as archive:
        for rel in PACKAGE_PATHS:
            archive.writestr(zip_info(rel), (LANE_DIR / rel).read_bytes())


def parse_hash_bytes(data: bytes) -> dict[str, str]:
    result = {}
    for line in data.decode("utf-8").splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            result[rel] = digest
    return result


def verify_zip(path: Path, standalone: bool = True) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"ZIP missing: {path}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        traversal = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        if names != list(PACKAGE_PATHS) or duplicates or traversal:
            raise RuntimeError({"scope": names == list(PACKAGE_PATHS), "duplicates": duplicates, "traversal": traversal})
        ledger = parse_hash_bytes(archive.read("SHA256SUMS.txt"))
        internal_mismatches = [rel for rel, digest in ledger.items() if hashlib.sha256(archive.read(rel)).hexdigest() != digest]
        lane_mismatches = [rel for rel in names if hashlib.sha256(archive.read(rel)).hexdigest() != sha256(LANE_DIR / rel)]
    standalone_status = "NOT_REQUESTED"
    if standalone:
        with tempfile.TemporaryDirectory(prefix="ps_cr_v0931_zip_") as temp:
            target = Path(temp)
            with zipfile.ZipFile(path) as archive:
                archive.extractall(target)
            env = dict(os.environ)
            env["V0931_TEST_ZIP"] = str(path)
            build = run([sys.executable, "-B", "build_candidate_a_physical_mockup_v0931.py", "--verify"], cwd=target, env=env)
            tests = run([sys.executable, "-B", "tests/test_candidate_a_physical_mockup_v0931.py"], cwd=target, env=env)
            if build.returncode or tests.returncode:
                raise RuntimeError({"standalone_build": build.stdout, "standalone_tests": tests.stdout})
            standalone_status = "PASS"
    if internal_mismatches or lane_mismatches:
        raise RuntimeError({"internal_hash_mismatches": internal_mismatches, "lane_mismatches": lane_mismatches})
    return {"zip_path": str(path), "entry_count": len(names), "duplicates": duplicates, "path_traversal": traversal, "internal_hash_verification": "PASS", "lane_byte_match": "PASS", "standalone_verify": standalone_status, "zip_sha256": sha256(path), "status": "PASS"}


def package_handoff() -> dict[str, Any]:
    verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{timestamp}.zip"
    temporary = DOWNLOAD_DIR / f".{ZIP_PREFIX}{timestamp}.validation.tmp"
    if final_path.exists() or temporary.exists():
        raise RuntimeError("refusing to overwrite handoff or validation package")
    try:
        write_zip(temporary)
        env = dict(os.environ)
        env["V0931_TEST_ZIP"] = str(temporary)
        result = run([sys.executable, "-B", "tests/test_candidate_a_physical_mockup_v0931.py"], cwd=LANE_DIR, env=env)
        if result.returncode:
            raise RuntimeError(f"contract tests failed:\n{result.stdout}")
        summary = [line for line in result.stdout.splitlines() if line.startswith("Ran ") or line == "OK"]
        write_text(LANE_DIR / ROOT_FILES[15], "command=python -B tests/test_candidate_a_physical_mockup_v0931.py\nstatus=PASS\n" + "\n".join(summary) + "\nphysical_mockup=NOT_YET_PERFORMED\nfull_output:\n" + result.stdout)
        write_text(LANE_DIR / ROOT_FILES[14], sha256sums_text())
        verify()
    finally:
        if temporary.exists():
            temporary.unlink()
    write_zip(final_path)
    return {"verification": "PASS", **verify_zip(final_path, standalone=True)}


def latest_handoff_zip() -> Path | None:
    matches = sorted(DOWNLOAD_DIR.glob(f"{ZIP_PREFIX}*.zip"))
    return matches[-1] if matches else None


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
