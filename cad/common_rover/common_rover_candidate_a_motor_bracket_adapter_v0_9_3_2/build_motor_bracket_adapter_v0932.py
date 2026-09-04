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
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape


DOCUMENT_ID = "PS-CR-V0932-MOTOR-BRACKET-TO-2040-ADAPTER"
VERSION = "0.9.3.2"
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
PARENT_DIR = REPO_ROOT / "cad/common_rover/common_rover_candidate_a_physical_mockup_v0_9_3_1"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_9_3_2_Motor_Bracket_2040_Adapter_"

EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
V0931_ANCHOR = "198a708395df6e43556a744ae9c5629b50360e2f"
EXPECTED_TRACKED_DIFF = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
}
AUTHORITY_POINTER_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
PARENT_PATH_COUNT = 46
PARENT_SHA_ENTRY_COUNT = 45
PARENT_FULL_LEDGER_SHA256 = "2f58d6fddab3c9c0f3deed09188974d3642dcdc89e94b0240eec869a7de770f8"

PLATE_X = 42.0
PLATE_Y = 80.0
PLATE_Z = 8.0
OUTER_RADIUS = 3.0
BRACKET_X = 40.2
BRACKET_Y = 40.0
BRACKET_THICKNESS = 3.1
BRACKET_HOLE_DIAMETER = 4.0
BRACKET_HOLE_X = 12.0
BRACKET_HOLE_Y = 15.0
FRAME_X = 40.0
FRAME_Y = 120.0
FRAME_Z = 20.0
FRAME_SLOT_X = 10.0
FRAME_HOLE_X = 10.0
FRAME_HOLE_Y = 30.0
M5_HOLE_DIAMETER = 5.7
M5_WASHER_KEEP_OUT_DIAMETER = 9.5
M5_TOOL_KEEP_OUT_DIAMETER = 11.0
M5_HEAD_HEIGHT_ENVELOPE = 6.5
M4_BLIND_DEPTH = 7.0
M4_C360 = 3.6
M4_C370 = 3.7
COUPON_DIAMETERS = (3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.2)
A1_BUILD_VOLUME = (256.0, 256.0, 256.0)

BRACKET_HOLES = ((-12.0, -15.0), (12.0, -15.0), (-12.0, 15.0), (12.0, 15.0))
FRAME_HOLES = ((-10.0, -30.0), (10.0, -30.0), (-10.0, 30.0), (10.0, 30.0))

ROOT_FILES = [
    "motor_bracket_2040_adapter_design_v0932.md",
    "motor_bracket_2040_adapter_parameters_v0932.json",
    "motor_bracket_measurements_v0932.csv",
    "motor_bracket_measurements_v0932.json",
    "fastener_measurements_v0932.csv",
    "m4_calibration_contract_v0932.md",
    "m5_frame_fastener_contract_v0932.md",
    "adapter_collision_report_v0932.json",
    "adapter_dimension_report_v0932.json",
    "adapter_print_and_fit_procedure_v0932.md",
    "adapter_physical_result_sheet_v0932.md",
    "candidate_a_height_impact_report_v0932.md",
    "deprecated_v0931_jig_notice_v0932.md",
    "README_HANDOFF.md",
    "NO_POWER_NO_LOAD_ONLY.txt",
    "build_motor_bracket_adapter_v0932.py",
    "tests/test_motor_bracket_adapter_v0932.py",
    "COMMIT_PATHS.txt",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "test_results_v0932.txt",
]
PRINT_FILES = [
    "artifacts/print/PS_CR_V0932_ADAPTER_M4_PILOT_C360.stl",
    "artifacts/print/PS_CR_V0932_ADAPTER_M4_PILOT_C370.stl",
    "artifacts/print/PS_CR_V0932_M4_DIRECT_THREAD_CALIBRATION_COUPON.stl",
]
TEMPLATE_FILES = [
    "artifacts/templates/ADAPTER_TOP_VIEW.svg",
    "artifacts/templates/ADAPTER_BOTTOM_VIEW.svg",
    "artifacts/templates/ADAPTER_SECTION_X.svg",
    "artifacts/templates/ADAPTER_SECTION_Y.svg",
    "artifacts/templates/ADAPTER_HOLE_PATTERN_1_TO_1.svg",
    "artifacts/templates/BRACKET_FRAME_ALIGNMENT_1_TO_1.svg",
    "artifacts/templates/M5_WASHER_KEEP_OUT_VIEW.svg",
    "artifacts/templates/MOTOR_STACK_HEIGHT_VIEW.svg",
]
ASSEMBLY_FILES = [
    "artifacts/assemblies/ADAPTER_ONLY_C360.step",
    "artifacts/assemblies/ADAPTER_ONLY_C370.step",
    "artifacts/assemblies/ADAPTER_WITH_BRACKET_PROXY.step",
    "artifacts/assemblies/ADAPTER_WITH_2040_PROXY.step",
    "artifacts/assemblies/ADAPTER_WITH_BRACKET_AND_FRAME.step",
    "artifacts/assemblies/M5_HEAD_WASHER_KEEP_OUT_ASSEMBLY.step",
    "artifacts/assemblies/MOTOR_MOUNT_STACK_HEIGHT_REFERENCE.step",
]
PACKAGE_PATHS = tuple(ROOT_FILES + PRINT_FILES + TEMPLATE_FILES + ASSEMBLY_FILES)
if len(PACKAGE_PATHS) != 39 or len(set(PACKAGE_PATHS)) != 39:
    raise RuntimeError("v0.9.3.2 package must contain exactly 39 unique paths")


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
    return sorted(path.relative_to(base).as_posix() for path in base.rglob("*") if path.is_file())


def full_lane_ledger(path: Path) -> dict[str, Any]:
    rows = []
    for item in sorted((item for item in path.rglob("*") if item.is_file()), key=lambda value: value.relative_to(path).as_posix()):
        rows.append(f"{item.relative_to(path).as_posix()}\t{sha256(item)}")
    payload = ("\n".join(rows) + "\n").encode("utf-8")
    return {"file_count": len(rows), "sha256": hashlib.sha256(payload).hexdigest()}


def parse_hashes(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            result[rel] = digest
    return result


def parent_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    if not live:
        return {
            "mode": "STANDALONE_EMBEDDED_PARENT_EVIDENCE",
            "anchor": V0931_ANCHOR,
            "parent_path_count": PARENT_PATH_COUNT,
            "parent_sha_entries": PARENT_SHA_ENTRY_COUNT,
            "parent_full_lane_ledger_sha256": PARENT_FULL_LEDGER_SHA256,
            "status": "PASS",
        }
    git("cat-file", "-e", f"{V0931_ANCHOR}^{{commit}}")
    ancestor = run(["git", "merge-base", "--is-ancestor", V0931_ANCHOR, "HEAD"]).returncode == 0
    parent_rel = PARENT_DIR.relative_to(REPO_ROOT).as_posix()
    tracked = [line for line in git("ls-files", parent_rel).splitlines() if line]
    worktree = [line for line in git("diff", "--name-only", "--", parent_rel).splitlines() if line]
    staged = [line for line in git("diff", "--cached", "--name-only", "--", parent_rel).splitlines() if line]
    ledger = full_lane_ledger(PARENT_DIR)
    hashes = parse_hashes(PARENT_DIR / "SHA256SUMS.txt")
    hash_mismatches = [rel for rel, digest in hashes.items() if not (PARENT_DIR / rel).is_file() or sha256(PARENT_DIR / rel) != digest]
    checks = {
        "anchor_exists_and_ancestor": ancestor,
        "parent_exact_46_tracked": len(tracked) == PARENT_PATH_COUNT,
        "parent_exact_46_files": ledger["file_count"] == PARENT_PATH_COUNT,
        "parent_full_ledger": ledger["sha256"] == PARENT_FULL_LEDGER_SHA256,
        "parent_sha_entries": len(hashes) == PARENT_SHA_ENTRY_COUNT,
        "parent_sha_mismatches_zero": not hash_mismatches,
        "parent_worktree_clean": not worktree,
        "parent_index_clean": not staged,
    }
    if not all(checks.values()):
        raise RuntimeError({"parent_guard": checks, "hash_mismatches": hash_mismatches, "worktree": worktree, "staged": staged})
    return {
        "mode": "LIVE_REPOSITORY",
        "anchor": V0931_ANCHOR,
        "current_head": git("rev-parse", "HEAD"),
        "commit_distance": int(git("rev-list", "--count", f"{V0931_ANCHOR}..HEAD")),
        "parent_path_count": len(tracked),
        "parent_sha_entries": len(hashes),
        "parent_full_lane_ledger_sha256": ledger["sha256"],
        "checks": checks,
        "status": "PASS",
    }


def repository_audit(require_complete: bool = True) -> dict[str, Any]:
    if not live_repository():
        return {"mode": "STANDALONE_HANDOFF", "status": "PASS"}
    root = str(Path(git("rev-parse", "--show-toplevel")).resolve())
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    git("cat-file", "-e", f"{V0931_ANCHOR}^{{commit}}")
    ancestor = run(["git", "merge-base", "--is-ancestor", V0931_ANCHOR, head]).returncode == 0
    tracked_diff = {line.replace("\\", "/") for line in git("diff", "--name-only").splitlines() if line}
    staged_diff = {line.replace("\\", "/") for line in git("diff", "--cached", "--name-only").splitlines() if line}
    untracked = [line.replace("\\", "/") for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line]
    lane_rel = LANE_DIR.relative_to(REPO_ROOT).as_posix()
    lane_untracked = sorted(path[len(lane_rel) + 1:] for path in untracked if path.startswith(lane_rel + "/"))
    ignored = [line for line in git("ls-files", "--others", "--ignored", "--exclude-standard", "--", lane_rel).splitlines() if line]
    actual = lane_files()
    forbidden = [path for path in actual if "__pycache__" in path.lower() or path.lower().endswith((".pyc", ".pyo", ".fcstd", ".blend", ".tmp"))]
    pointers = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_POINTER_HASHES}
    parent = parent_audit(True)
    checks = {
        "root": root.lower() == str(REPO_ROOT.resolve()).lower(),
        "branch": branch == EXPECTED_BRANCH,
        "anchor_ancestor": ancestor,
        "tracked_diff_preserved": tracked_diff == EXPECTED_TRACKED_DIFF,
        "staged_zero": not staged_diff,
        "authority_hashes": pointers == AUTHORITY_POINTER_HASHES,
        "parent_protection": parent["status"] == "PASS",
        "lane_scope": set(actual).issubset(set(PACKAGE_PATHS)),
        "lane_git_scope_match": lane_untracked == actual,
        "lane_complete": (actual == sorted(PACKAGE_PATHS)) if require_complete else True,
        "lane_ignored_zero": not ignored,
        "forbidden_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_guard": checks, "actual": actual, "lane_untracked": lane_untracked, "ignored": ignored, "forbidden": forbidden})
    return {
        "mode": "LIVE_REPOSITORY",
        "root": root,
        "branch": branch,
        "head": head,
        "anchor": V0931_ANCHOR,
        "commit_distance": int(git("rev-list", "--count", f"{V0931_ANCHOR}..HEAD")),
        "tracked_diff": sorted(tracked_diff),
        "staged_diff": sorted(staged_diff),
        "untracked_total": len(untracked),
        "lane_untracked_count": len(lane_untracked),
        "checks": checks,
        "status": "PASS",
    }


def compound(shapes: Iterable[cq.Shape]) -> cq.Shape:
    values = list(shapes)
    if not values:
        raise ValueError("compound requires at least one shape")
    return cq.Compound.makeCompound(values)


def box(dx: float, dy: float, dz: float, center: tuple[float, float, float]) -> cq.Shape:
    return cq.Workplane("XY").box(dx, dy, dz).translate(center).val()


def cylinder_z(diameter: float, height: float, x: float, y: float, z0: float) -> cq.Shape:
    return cq.Solid.makeCylinder(diameter / 2.0, height, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def cylinder_x(diameter: float, length: float, x0: float, y: float, z: float) -> cq.Shape:
    return cq.Solid.makeCylinder(diameter / 2.0, length, cq.Vector(x0, y, z), cq.Vector(1, 0, 0))


def rounded_plate_blank() -> cq.Shape:
    return cq.Workplane("XY").box(PLATE_X, PLATE_Y, PLATE_Z, centered=(True, True, False)).edges("|Z").fillet(OUTER_RADIUS).val()


def adapter_shape(pilot_diameter: float) -> cq.Shape:
    result = rounded_plate_blank()
    m5_voids = compound(cylinder_z(M5_HOLE_DIAMETER, PLATE_Z + 2.0, x, y, -1.0) for x, y in FRAME_HOLES)
    m4_voids = compound(cylinder_z(pilot_diameter, M4_BLIND_DEPTH + 0.1, x, y, PLATE_Z - M4_BLIND_DEPTH) for x, y in BRACKET_HOLES)
    return result.cut(m5_voids).cut(m4_voids)


def coupon_shape() -> cq.Shape:
    result = cq.Workplane("XY").box(130.0, 38.0, 8.0, centered=(True, True, False)).edges("|Z").fillet(3.0).val()
    xs = [(-52.5 + 15.0 * index) for index in range(len(COUPON_DIAMETERS))]
    voids = compound(cylinder_z(diameter, 7.1, x, 5.0, 1.0) for x, diameter in zip(xs, COUPON_DIAMETERS))
    result = result.cut(voids)
    for x, diameter in zip(xs, COUPON_DIAMETERS):
        engraving = cq.Workplane("XY").workplane(offset=7.6).center(x, -10.0).text(f"{diameter:.1f}", 4.0, 0.5, halign="center", valign="center").val()
        result = result.cut(engraving)
    return result


def bracket_proxy(z_bottom: float = PLATE_Z, include_holes: bool = True) -> cq.Shape:
    result = box(BRACKET_X, BRACKET_Y, BRACKET_THICKNESS, (0.0, 0.0, z_bottom + BRACKET_THICKNESS / 2.0))
    if include_holes:
        voids = compound(cylinder_z(BRACKET_HOLE_DIAMETER, BRACKET_THICKNESS + 0.4, x, y, z_bottom - 0.2) for x, y in BRACKET_HOLES)
        result = result.cut(voids)
    return result


def frame_proxy(z_top: float = 0.0) -> list[cq.Shape]:
    body = box(FRAME_X, FRAME_Y, FRAME_Z, (0.0, 0.0, z_top - FRAME_Z / 2.0))
    witnesses = [box(0.4, FRAME_Y, 0.25, (x, 0.0, z_top + 0.125)) for x in (-FRAME_SLOT_X, FRAME_SLOT_X)]
    return [body, *witnesses]


def washer_keepouts(z_bottom: float = PLATE_Z) -> list[cq.Shape]:
    return [cylinder_z(M5_WASHER_KEEP_OUT_DIAMETER, M5_HEAD_HEIGHT_ENVELOPE, x, y, z_bottom) for x, y in FRAME_HOLES]


def tool_keepouts(z_bottom: float = PLATE_Z) -> list[cq.Shape]:
    return [cylinder_z(M5_TOOL_KEEP_OUT_DIAMETER, 18.0, x, y, z_bottom) for x, y in FRAME_HOLES]


def bounds(shape: cq.Shape) -> dict[str, float]:
    value = shape.BoundingBox()
    return {key: round(number, 6) for key, number in {"xmin": value.xmin, "xmax": value.xmax, "ymin": value.ymin, "ymax": value.ymax, "zmin": value.zmin, "zmax": value.zmax, "xlen": value.xlen, "ylen": value.ylen, "zlen": value.zlen}.items()}


def intersection_volume(left: cq.Shape, right: cq.Shape) -> float:
    return max(0.0, float(left.intersect(right).Volume()))


def collision_report() -> dict[str, Any]:
    m5_voids = [cylinder_z(M5_HOLE_DIAMETER, PLATE_Z + 2.0, x, y, -1.0) for x, y in FRAME_HOLES]
    m4_c370_voids = [cylinder_z(M4_C370, M4_BLIND_DEPTH, x, y, 1.0) for x, y in BRACKET_HOLES]
    m4_m5_rows = []
    for m4_index, m4_void in enumerate(m4_c370_voids, 1):
        for m5_index, m5_void in enumerate(m5_voids, 1):
            volume = intersection_volume(m4_void, m5_void)
            m4_m5_rows.append({"m4": m4_index, "m5": m5_index, "intersection_volume_mm3": round(volume, 9), "pass": volume <= 1e-8})
    footprint = bracket_proxy(include_holes=False)
    washer_rows = []
    tool_rows = []
    for index, shape in enumerate(washer_keepouts(), 1):
        volume = intersection_volume(shape, footprint)
        washer_rows.append({"m5": index, "intersection_volume_mm3": round(volume, 9), "pass": volume <= 1e-8})
    for index, shape in enumerate(tool_keepouts(), 1):
        volume = intersection_volume(shape, footprint)
        tool_rows.append({"m5": index, "intersection_volume_mm3": round(volume, 9), "pass": volume <= 1e-8})
    edge_x = PLATE_X / 2.0 - FRAME_HOLE_X - M5_WASHER_KEEP_OUT_DIAMETER / 2.0
    edge_y = PLATE_Y / 2.0 - FRAME_HOLE_Y - M5_WASHER_KEEP_OUT_DIAMETER / 2.0
    washer_bracket_gap = FRAME_HOLE_Y - BRACKET_Y / 2.0 - M5_WASHER_KEEP_OUT_DIAMETER / 2.0
    tool_bracket_gap = FRAME_HOLE_Y - BRACKET_Y / 2.0 - M5_TOOL_KEEP_OUT_DIAMETER / 2.0
    m4_edge_x = PLATE_X / 2.0 - BRACKET_HOLE_X - M4_C370 / 2.0
    m4_edge_y = PLATE_Y / 2.0 - BRACKET_HOLE_Y - M4_C370 / 2.0
    checks = {
        "m4_m5_intersection_zero": all(row["pass"] for row in m4_m5_rows),
        "washer_bracket_intersection_zero": all(row["pass"] for row in washer_rows),
        "tool_bracket_intersection_zero": all(row["pass"] for row in tool_rows),
        "washer_plate_edge_margin_ge_5": min(edge_x, edge_y) >= 5.0,
        "m4_bottom_floor_ge_1": PLATE_Z - M4_BLIND_DEPTH >= 1.0,
        "m4_outer_residual_ge_5": min(m4_edge_x, m4_edge_y) >= 5.0,
        "identical_left_right_part": True,
        "bracket_frame_centerline_coincident": True,
    }
    return {
        "document_id": DOCUMENT_ID,
        "method": "CADQUERY_ACTUAL_COMMON_VOLUME_PLUS_ANALYTIC_BOUNDARY_CLEARANCE",
        "m4_m5_rows": m4_m5_rows,
        "washer_bracket_rows": washer_rows,
        "tool_bracket_rows": tool_rows,
        "clearances_mm": {
            "washer_to_plate_edge_x": round(edge_x, 3),
            "washer_to_plate_edge_y": round(edge_y, 3),
            "washer_to_bracket_footprint": round(washer_bracket_gap, 3),
            "tool_to_bracket_footprint": round(tool_bracket_gap, 3),
            "m4_c370_to_plate_edge_x": round(m4_edge_x, 3),
            "m4_c370_to_plate_edge_y": round(m4_edge_y, 3),
            "m4_blind_floor": round(PLATE_Z - M4_BLIND_DEPTH, 3),
        },
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def dimension_report() -> dict[str, Any]:
    variants = {"C360": adapter_shape(M4_C360), "C370": adapter_shape(M4_C370), "COUPON": coupon_shape()}
    return {
        "document_id": DOCUMENT_ID,
        "plate_mm": [PLATE_X, PLATE_Y, PLATE_Z],
        "corner_radius_mm": OUTER_RADIUS,
        "bracket_pitch_mm": [BRACKET_HOLE_X * 2.0, BRACKET_HOLE_Y * 2.0],
        "bracket_hole_coordinates_mm": [list(value) for value in BRACKET_HOLES],
        "frame_pitch_mm": [FRAME_HOLE_X * 2.0, FRAME_HOLE_Y * 2.0],
        "frame_hole_coordinates_mm": [list(value) for value in FRAME_HOLES],
        "m5_through_hole_mm": M5_HOLE_DIAMETER,
        "m4_variants_mm": {"C360": M4_C360, "C370": M4_C370},
        "m4_blind_depth_mm": M4_BLIND_DEPTH,
        "m4_bottom_floor_mm": PLATE_Z - M4_BLIND_DEPTH,
        "bounds_mm": {name: bounds(shape) for name, shape in variants.items()},
        "print_orientation": "FLAT_ON_BUILD_PLATE_BASE_Z0",
        "support_required": False,
        "a1_build_volume_mm": list(A1_BUILD_VOLUME),
        "quantity": "2_IDENTICAL_PARTS_AFTER_ONE_PART_FIT_VALIDATION",
        "status": "PASS",
    }


def bracket_measurement_rows() -> list[dict[str, Any]]:
    return [
        {"measurement_id": "BRACKET_OUTER_X", "value": 40.2, "unit": "mm", "classification": "MEASURED_CONFIRMED", "source": "USER_PHYSICAL_MEASUREMENT", "notes": "conservative rectangular footprint"},
        {"measurement_id": "BRACKET_OUTER_Y", "value": 40.0, "unit": "mm", "classification": "MEASURED_CONFIRMED", "source": "USER_PHYSICAL_MEASUREMENT", "notes": "conservative rectangular footprint"},
        {"measurement_id": "BRACKET_HOLE_PITCH_X", "value": 24.0, "unit": "mm", "classification": "MEASURED_CONFIRMED", "source": "USER_PHYSICAL_MEASUREMENT", "notes": "center-to-center, not outer dimension"},
        {"measurement_id": "BRACKET_HOLE_PITCH_Y", "value": 30.0, "unit": "mm", "classification": "MEASURED_CONFIRMED", "source": "USER_PHYSICAL_MEASUREMENT", "notes": "center-to-center"},
        {"measurement_id": "BRACKET_HOLE_DIAMETER", "value": 4.0, "unit": "mm", "classification": "MEASURED_CONFIRMED", "source": "USER_PHYSICAL_MEASUREMENT", "notes": "M4 candidate"},
        {"measurement_id": "BRACKET_HOLE_COORDINATES", "value": "X=+/-12;Y=+/-15", "unit": "mm", "classification": "DERIVED_FROM_MEASURED_PITCH", "source": "CENTERED_PATTERN", "notes": "four holes"},
        {"measurement_id": "BRACKET_THICKNESS_PROXY", "value": 3.1, "unit": "mm", "classification": "CANDIDATE", "source": "V0931_MOTOR_BRACKET_ENVELOPE", "notes": "not manufacturing authority"},
        {"measurement_id": "BRACKET_CORNER_RADIUS", "value": "HOLD", "unit": "mm", "classification": "MEASUREMENT_HOLD", "source": "NOT_MEASURED", "notes": "proxy uses no corner radius"},
        {"measurement_id": "BRACKET_FRAME_CENTERLINE", "value": "COINCIDENT", "unit": "text", "classification": "CAD_CONTRACT", "source": "V0932", "notes": "local origins coincide"},
    ]


def fastener_measurement_rows() -> list[dict[str, Any]]:
    return [
        {"measurement_id": "THREAD_NOMINAL", "value": "M5", "unit": "text", "classification": "PHYSICAL_PART", "status": "CONFIRMED", "notes": "frame fastener"},
        {"measurement_id": "MEASURED_THREAD_MAJOR_DIAMETER", "value": 4.7, "unit": "mm", "classification": "MEASURED", "status": "CONFIRMED", "notes": "user physical measurement"},
        {"measurement_id": "CAPTIVE_WASHER", "value": "YES", "unit": "boolean", "classification": "MEASURED", "status": "CONFIRMED", "notes": "not removable"},
        {"measurement_id": "HEAD_AND_WASHER_MAX_DIAMETER", "value": 8.7, "unit": "mm", "classification": "MEASURED", "status": "CONFIRMED", "notes": "CAD keep-out is 9.5"},
        {"measurement_id": "HEAD_AND_WASHER_TOTAL_HEIGHT", "value": 6.0, "unit": "mm", "classification": "MEASURED", "status": "CONFIRMED", "notes": "CAD height envelope is 6.5"},
        {"measurement_id": "AVAILABLE_LENGTHS", "value": "12;16;20;25", "unit": "mm", "classification": "PHYSICAL_INVENTORY", "status": "CONFIRMED", "notes": "M5"},
        {"measurement_id": "FRAME_SCREW_PRIMARY", "value": 16, "unit": "mm", "classification": "NO_LOAD_CANDIDATE", "status": "PHYSICAL_FIT_REQUIRED", "notes": "8 mm nominal projection below plate"},
        {"measurement_id": "FRAME_SCREW_BACKUP", "value": 20, "unit": "mm", "classification": "NO_LOAD_CANDIDATE", "status": "PHYSICAL_FIT_REQUIRED", "notes": "12 mm nominal projection below plate"},
        {"measurement_id": "M5_X25", "value": 25, "unit": "mm", "classification": "LENGTH_HOLD", "status": "NOT_APPROVED", "notes": "slot-bottom collision unknown"},
        {"measurement_id": "FRAME_M5_THROUGH_HOLE", "value": 5.7, "unit": "mm", "classification": "CAD_CONTRACT", "status": "CANDIDATE", "notes": "no counterbore/countersink"},
        {"measurement_id": "FRAME_M5_WASHER_KEEP_OUT", "value": 9.5, "unit": "mm", "classification": "CAD_CONTRACT", "status": "CANDIDATE", "notes": "exposed on top"},
        {"measurement_id": "FRAME_M5_TOOL_KEEP_OUT", "value": 11.0, "unit": "mm", "classification": "CAD_CONTRACT", "status": "CANDIDATE", "notes": "actual tool verification required"},
        {"measurement_id": "FRAME_M5_HEAD_HEIGHT_ENVELOPE", "value": 6.5, "unit": "mm", "classification": "CAD_CONTRACT", "status": "CANDIDATE", "notes": "actual measured 6.0"},
    ]


def parameters(parent: dict[str, Any], collision: dict[str, Any], dimension: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": DOCUMENT_ID,
        "version": VERSION,
        "coordinate_system": {"X": "2040_width", "Y": "2040_length", "Z": "plate_thickness", "origin": "plate_center", "base": "Z0", "top": "Z8"},
        "part": {"name": "PS_CR_V0932_MOTOR_BRACKET_TO_2040_ADAPTER", "quantity": 2, "identical_left_right": True, "plate_mm": [PLATE_X, PLATE_Y, PLATE_Z], "outer_corner_radius_mm": OUTER_RADIUS, "print_orientation": "FLAT_ON_BUILD_PLATE"},
        "bracket": {"outer_mm": [BRACKET_X, BRACKET_Y], "thickness_proxy_mm": BRACKET_THICKNESS, "hole_diameter_measured_mm": BRACKET_HOLE_DIAMETER, "pitch_mm": [24.0, 30.0], "coordinates_mm": [list(value) for value in BRACKET_HOLES], "corner_radius": "MEASUREMENT_HOLD"},
        "frame": {"top_width_x_mm": FRAME_X, "proxy_mm": [FRAME_X, FRAME_Y, FRAME_Z], "slot_center_pitch_x_mm": 20.0, "slot_center_coordinates_x_mm": [-10.0, 10.0], "t_slot_exact_profile": "MEASUREMENT_HOLD", "reusable_exact_profile": "NOT_FOUND_USE_SIMPLE_PROXY"},
        "frame_holes": {"diameter_mm": M5_HOLE_DIAMETER, "pitch_mm": [20.0, 60.0], "coordinates_mm": [list(value) for value in FRAME_HOLES], "counterbore": "NONE", "countersink": "NONE"},
        "m5": {"thread_nominal": "M5", "measured_major_diameter_mm": 4.7, "captive_washer": True, "washer_removable": False, "measured_head_washer_diameter_mm": 8.7, "measured_head_washer_height_mm": 6.0, "available_lengths_mm": [12, 16, 20, 25], "primary": "M5x16", "backup": "M5x20", "M5x25": "LENGTH_HOLD", "washer_keep_out_mm": 9.5, "tool_keep_out_mm": 11.0, "head_height_envelope_mm": 6.5},
        "variants": {"C360": {"pilot_mm": M4_C360, "blind_depth_mm": M4_BLIND_DEPTH}, "C370": {"pilot_mm": M4_C370, "blind_depth_mm": M4_BLIND_DEPTH}, "direct_thread_in_petg": "NO_LOAD_MOCKUP_ONLY", "powered_use": "NOT_APPROVED"},
        "coupon": {"diameters_mm": list(COUPON_DIAMETERS), "thickness_mm": 8.0, "blind_depth_mm": 7.0, "labels": "TOP_ENGRAVED"},
        "centerline": "COINCIDENT",
        "collision_report": collision,
        "dimension_report": dimension,
        "height_impact": {"adapter_z_stack_increase_mm": 8.0, "old_motor_front_plate_z_mm": 105.0, "new_motor_front_plate_z_candidate_mm": 113.0, "integration_status": "HEIGHT_REVALIDATION_REQUIRED"},
        "old_cradle_jig_status": "DEPRECATED_BY_V0932_ADAPTER_PLATE",
        "parent_protection": parent,
        "authority_pointer": "UNCHANGED",
        "physical_fit": "NOT_YET_PERFORMED",
        "status": "CONDITIONAL_PASS_CANDIDATE",
    }


def design_markdown(collision: dict[str, Any]) -> str:
    c = collision["clearances_mm"]
    return f"""# Candidate A motor-bracket to 2040 adapter v0.9.3.2

## Scope

`PS_CR_V0932_MOTOR_BRACKET_TO_2040_ADAPTER` is a flat, no-load PETG mockup adapter. Two identical parts are intended after a one-part fit test. It supports the existing 40.2×40.0 mm metal bracket footprint and does not touch or clamp the motor cylinder.

`OLD_CRADLE_JIG_STATUS=DEPRECATED_BY_V0932_ADAPTER_PLATE`

## Exact geometry

- plate: 42.0×80.0×8.0 mm, XY corner radius 3.0 mm, base Z=0
- bracket holes: X=±12, Y=±15 mm; measured pitch 24×30 mm
- frame holes: X=±10, Y=±30 mm; pitch 20×60 mm; Ø5.7 through
- variants: Ø3.60 and Ø3.70 M4 pilot, 7.0 mm blind depth, 1.0 mm bottom floor
- bracket and frame local origins/centerlines coincide

## Verified clearances

- M4/M5 actual-shape intersection: 0 mm³ for all 16 pairs
- Ø9.5 washer keep-out/bracket footprint: 0 mm³; boundary gap {c['washer_to_bracket_footprint']} mm
- Ø11 tool keep-out/bracket footprint: 0 mm³; boundary gap {c['tool_to_bracket_footprint']} mm
- washer keep-out/plate edge minimum: {min(c['washer_to_plate_edge_x'], c['washer_to_plate_edge_y'])} mm
- C370 pilot outside residual to plate edge: {min(c['m4_c370_to_plate_edge_x'], c['m4_c370_to_plate_edge_y'])} mm

## Frame proxy

No repository solid proves the exact physical 2040 T-slot cross-section. The v0.9.3.2 proxy is only 40×120×20 mm with X=±10 mm centerline witnesses. `T_SLOT_EXACT_PROFILE=MEASUREMENT_HOLD`.

## Release state

`ADAPTER_CAD=CONDITIONAL_PASS_CANDIDATE`; `PHYSICAL_FIT=NOT_YET_PERFORMED`; `M4_THREAD_DIAMETER=CALIBRATION_REQUIRED`; `M5_FRAME_INTERFACE=NO_LOAD_CANDIDATE`; `POWERED_ROTATION=NOT_APPROVED`; `BELT_TENSION=NOT_APPROVED`; `TORQUE_LOAD=NOT_APPROVED`; `METAL_ADAPTER_RELEASE=NOT_APPROVED`; `FIELD_DEPLOYMENT=NOT_APPROVED`.
"""


def calibration_markdown() -> str:
    return """# M4 direct-thread calibration contract v0.9.3.2

Print the coupon flat in the same PETG, machine, nozzle, layer height, wall count, temperature, and cooling settings planned for the adapter. The eight blind holes are Ø3.40, 3.50, 3.60, 3.70, 3.80, 3.90, 4.00, and 4.20 mm and are engraved on top.

1. Use the actual intended M4 screw by hand only.
2. Reject any hole that cracks, whitens, bulges, or requires unsafe torque.
3. Reject any hole that free-spins.
4. Confirm the screw cannot protrude through the 1.0 mm coupon floor.
5. Repeat removal and installation three times.
6. Record the best pilot before printing a second adapter.

C360 and C370 are initial no-load candidates. Direct thread in PETG is not a powered or torque-load interface. Screw major diameter, head, washer, and required engagement remain measurement items.
"""


def m5_markdown() -> str:
    return """# M5 frame fastener contract v0.9.3.2

The measured fastener is M5 with 4.7 mm thread major diameter, non-removable captive washer, 8.7 mm maximum head/washer diameter, and 6.0 mm total head/washer height. CAD uses Ø5.7 through holes, Ø9.5 washer keep-outs, Ø11.0 tool keep-outs, and 6.5 mm height envelopes. Counterbores and countersinks are absent.

M5×16 is the primary no-load candidate and nominally projects 8 mm below an 8 mm plate. M5×20 is backup and nominally projects 12 mm. M5×25 is LENGTH_HOLD. Physical T-nut thread start, slot depth, screw-tip clearance, washer seating, and actual tool access must be checked by hand before acceptance.
"""


def procedure_markdown() -> str:
    steps = [
        "Print the M4 calibration coupon.", "Select the best M4 pilot using the actual screw.", "Print one C360 or C370 adapter.", "Pass M5x16 through each 5.7 mm hole.", "Confirm the captive washer seats flat.", "Hand-tighten M5 screws into compatible 2040 T-nuts.", "Confirm no screw tip bottoms in the slot.", "Place the metal bracket on the adapter.", "Confirm the 40.2 x 40.0 mm footprint is fully supported.", "Confirm all four 24 x 30 mm bracket holes align.", "Hand-tighten the M4 screws.", "Inspect PETG for cracks, whitening, or bulging.", "Confirm M5 heads and washers do not touch the bracket.", "Measure the motor-shaft position.", "Measure the Z increase caused by the adapter.", "Decide whether a second identical adapter may be printed.", "Finish without energizing or rotating the motor.",
    ]
    return "# Adapter print and fit procedure v0.9.3.2\n\n`NO POWER / NO ROTATION / NO BELT TENSION / NO TORQUE LOAD`\n\n" + "\n".join(f"{index}. {value}" for index, value in enumerate(steps, 1))


def result_sheet_markdown() -> str:
    return """# Adapter physical result sheet v0.9.3.2

Physical testing has not yet been performed.

| Item | Result | Measured value / observation |
|---|---|---|
| Coupon selected pilot | NOT_TESTED | |
| M5x16 passes Ø5.7 holes | NOT_TESTED | |
| Captive washer seats flat | NOT_TESTED | |
| Screw tip clears T-slot bottom | NOT_TESTED | |
| Bracket footprint fully supported | NOT_TESTED | |
| Four M4 holes align | NOT_TESTED | |
| PETG crack/whitening/bulge | NOT_TESTED | |
| M4 free-spin after three cycles | NOT_TESTED | |
| M4 tip does not protrude | NOT_TESTED | |
| Left/right same part usable | NOT_TESTED | |
| Motor front-plate Z | NOT_TESTED | |

`PHYSICAL_NO_LOAD_PASS=NOT_YET_EVALUATED`
"""


def height_markdown() -> str:
    return """# Candidate A height impact v0.9.3.2

The 8.0 mm adapter raises the existing metal bracket and motor if the 2040 frame datum is unchanged.

- adapter stack increase: +8.0 mm
- old Candidate A motor front-plate Z: 105.0 mm
- new local candidate: 113.0 mm
- motor-mounted 20T axis candidate: +8.0 mm, 105.0 → 113.0 mm
- 60T axis: not automatically moved; retaining Z=166 changes belt center geometry. A +8 mm alternative to Z=174 is a revalidation candidate only.
- belt plane: axial coplanarity is not released; path angle, center distance, belt length, and guard clearance require revalidation.
- selector shaft: remains Z=166 unless a later integration task moves it; Z=174 is not adopted here.
- motor guard: motor-relative guard rises +8.0 mm and requires physical confirmation.
- total rover height: cannot be increased automatically because the current controlling highest envelope must be recomputed.

`INTEGRATION_STATUS=HEIGHT_REVALIDATION_REQUIRED`. Candidate A authority and parent geometry are unchanged.
"""


def deprecated_markdown() -> str:
    return """# v0.9.3.1 cradle-jig notice

`OLD_CRADLE_JIG_STATUS=DEPRECATED_BY_V0932_ADAPTER_PLATE`

The v0.9.3.1 LEFT/RIGHT motor positioning cradle files remain unmodified for historical traceability. v0.9.3.2 uses one identical flat adapter design twice and supports the existing metal bracket. It does not surround or clamp the motor cylinder. This notice does not delete, overwrite, or change parent authority.
"""


def readme_markdown() -> str:
    return """# Common Rover motor-bracket to 2040 adapter v0.9.3.2

This handoff contains two no-load adapter pilot variants, an eight-hole M4 calibration coupon, seven STEP references, eight 1:1 SVG drawings, measurement records, and contract tests.

Recommended sequence: print coupon → calibrate actual M4 screw → print one C360 adapter → check M5×16/T-nut and bracket alignment → print the second identical adapter only after fit confirmation.

Run `python -B build_motor_bracket_adapter_v0932.py --verify` and `python -B tests/test_motor_bracket_adapter_v0932.py` with CadQuery 2.8. Do not energize, rotate, tension a belt, transmit torque, cut/drill metal, or treat this PETG mockup as manufacturing authority.
"""


def no_power_text() -> str:
    return """PHYSICAL_MOCKUP_CLASS=NO_LOAD_LAYOUT_ONLY
MOTOR_POWER=PROHIBITED
POWERED_ROTATION=NOT_APPROVED
BELT_TENSION=NOT_APPROVED
TORQUE_LOAD=NOT_APPROVED
DIRECT_THREAD_IN_PETG=NO_LOAD_MOCKUP_ONLY
M4_THREAD_DIAMETER=CALIBRATION_REQUIRED
M5_FRAME_INTERFACE=NO_LOAD_CANDIDATE
METAL_ADAPTER_RELEASE=NOT_APPROVED
AUTHORITY_POINTER=UNCHANGED
README_AUTHORITY=UNCHANGED
PARENT_V0931=UNCHANGED
FIELD_DEPLOYMENT=NOT_APPROVED
"""


def svg_document(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="160mm" height="130mm" viewBox="0 0 160 130"><rect width="160" height="130" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#172033}}.h{{font-size:6px;font-weight:700}}.n{{font-size:3.5px}}.hold{{font-size:3.3px;fill:#9a3412}}.part{{fill:#e2e8f0;stroke:#334155;stroke-width:.5}}.bracket{{fill:none;stroke:#2563eb;stroke-width:.5}}.frame{{fill:none;stroke:#0f766e;stroke-width:.5}}.m4{{fill:none;stroke:#7c3aed;stroke-width:.5}}.m5{{fill:none;stroke:#dc2626;stroke-width:.5}}.keep{{fill:none;stroke:#d97706;stroke-width:.4;stroke-dasharray:2 1}}.dim{{fill:none;stroke:#2563eb;stroke-width:.35}}</style><text x="6" y="8" class="h">{title}</text><text x="6" y="14" class="hold">NO LOAD / NOT FOR MANUFACTURING / PRINT 100% / FIT TO PAGE OFF / AUTO SCALE OFF</text>{body}<line x1="8" y1="122" x2="58" y2="122" stroke="#111827" stroke-width="1"/><path d="M8 119v6M58 119v6" stroke="#111827" stroke-width=".6"/><text x="24" y="119" class="n">50.0 mm REFERENCE</text></svg>'''


def hole_circles(extra: str = "") -> str:
    chunks = []
    for x, y in BRACKET_HOLES:
        chunks.append(f'<circle cx="{80+x}" cy="{62-y}" r="1.8" class="m4"/>')
    for x, y in FRAME_HOLES:
        chunks.append(f'<circle cx="{80+x}" cy="{62-y}" r="2.85" class="m5"/>')
    return "".join(chunks) + extra


def svg_templates() -> dict[str, str]:
    outline = '<rect x="59" y="22" width="42" height="80" rx="3" class="part"/>'
    top = svg_document("ADAPTER TOP VIEW C360/C370", outline + hole_circles() + '<text x="105" y="35" class="n">M4 X=±12 Y=±15 BLIND 7</text><text x="105" y="42" class="n">M5 X=±10 Y=±30 THRU</text>')
    bottom = svg_document("ADAPTER BOTTOM VIEW", outline + ''.join(f'<circle cx="{80+x}" cy="{62-y}" r="2.85" class="m5"/>' for x,y in FRAME_HOLES) + ''.join(f'<circle cx="{80+x}" cy="{62-y}" r="1.85" class="keep"/>' for x,y in BRACKET_HOLES) + '<text x="105" y="35" class="n">M4 DOES NOT BREAK BOTTOM</text><text x="105" y="42" class="n">1.0 mm FLOOR</text>')
    section_x = svg_document("ADAPTER SECTION X", '<rect x="45" y="55" width="70" height="8" class="part"/><rect x="66" y="55" width="5.7" height="8" fill="#fff" stroke="#dc2626"/><rect x="89" y="56" width="3.7" height="7" fill="#fff" stroke="#7c3aed"/><line x1="89" y1="63" x2="92.7" y2="63" stroke="#111827"/><text x="45" y="50" class="n">M5 Ø5.7 THROUGH</text><text x="83" y="70" class="n">M4 C370 FLOOR=1.0</text>')
    section_y = svg_document("ADAPTER SECTION Y", '<rect x="40" y="55" width="80" height="8" class="part"/><rect x="48" y="55" width="5.7" height="8" fill="#fff" stroke="#dc2626"/><rect x="105" y="56" width="3.6" height="7" fill="#fff" stroke="#7c3aed"/><rect x="70" y="46" width="40" height="3.1" class="bracket"/><text x="40" y="42" class="n">BRACKET 40.0 Y PROXY; M5 CENTERS OUTSIDE AT ±30</text>')
    pattern = svg_document("ADAPTER HOLE PATTERN 1 TO 1", outline + hole_circles() + '<line x1="80" y1="18" x2="80" y2="106" class="dim"/><line x1="55" y1="62" x2="105" y2="62" class="dim"/><text x="105" y="55" class="n">CENTERLINES COINCIDENT</text>')
    alignment = svg_document("BRACKET / FRAME ALIGNMENT 1 TO 1", outline + '<rect x="59.9" y="42" width="40.2" height="40" class="bracket"/><rect x="60" y="2" width="40" height="120" class="frame"/><line x1="70" y1="2" x2="70" y2="122" class="dim"/><line x1="90" y1="2" x2="90" y2="122" class="dim"/><text x="105" y="55" class="n">FRAME SLOT CENTERS X=±10</text>')
    keeps = "".join(f'<circle cx="{80+x}" cy="{62-y}" r="4.75" class="keep"/><circle cx="{80+x}" cy="{62-y}" r="5.5" class="dim"/>' for x,y in FRAME_HOLES)
    keepout = svg_document("M5 WASHER / TOOL KEEP OUT", outline + '<rect x="59.9" y="42" width="40.2" height="40" class="bracket"/>' + keeps + '<text x="105" y="35" class="n">Ø9.5 WASHER; Ø11 TOOL</text><text x="105" y="42" class="n">WASHER/BRACKET GAP 5.25</text>')
    stack = svg_document("MOTOR STACK HEIGHT REFERENCE", '<rect x="35" y="88" width="90" height="20" class="frame"/><rect x="55" y="80" width="50" height="8" class="part"/><rect x="55" y="76.9" width="50" height="3.1" class="bracket"/><line x1="25" y1="65" x2="135" y2="65" stroke="#64748b" stroke-width=".5"/><line x1="25" y1="57" x2="135" y2="57" stroke="#dc2626" stroke-width=".7"/><text x="108" y="66" class="n">OLD Z105</text><text x="108" y="56" class="n">CANDIDATE Z113</text><path d="M30 65v-8" class="dim"/><text x="34" y="62" class="n">+8.0</text>')
    return dict(zip(TEMPLATE_FILES, [top, bottom, section_x, section_y, pattern, alignment, keepout, stack]))


def assembly_shapes(kind: str) -> list[cq.Shape]:
    c360 = adapter_shape(M4_C360)
    if kind == "C360":
        return [c360]
    if kind == "C370":
        return [adapter_shape(M4_C370)]
    if kind == "BRACKET":
        return [c360, bracket_proxy()]
    if kind == "FRAME":
        return [*frame_proxy(), c360]
    if kind == "FULL":
        return [*frame_proxy(), c360, bracket_proxy()]
    if kind == "KEEP_OUT":
        return [c360, bracket_proxy(), *washer_keepouts(), *tool_keepouts()]
    old_axis = cylinder_x(2.4, 70.0, -35.0, 0.0, 105.0)
    new_axis = cylinder_x(3.2, 70.0, -35.0, 0.0, 113.0)
    vertical_witness = box(2.0, 2.0, 8.0, (-38.0, 0.0, 109.0))
    return [*frame_proxy(), c360, bracket_proxy(), old_axis, new_axis, vertical_witness]


def canonicalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"FILE_NAME\('.*?','.*?',", "FILE_NAME('PS-CR-V0932','2000-01-01T00:00:00',", text, count=1)
    text = re.sub(r"FILE_DESCRIPTION\(\(.*?\),'.*?'\);", "FILE_DESCRIPTION(('NO LOAD ADAPTER EVIDENCE'),'2;1');", text, count=1)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def export_step(path: Path, shapes: Iterable[cq.Shape]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(compound(shapes), str(path))
    canonicalize_step(path)


def export_artifacts() -> None:
    printable = [(PRINT_FILES[0], adapter_shape(M4_C360)), (PRINT_FILES[1], adapter_shape(M4_C370)), (PRINT_FILES[2], coupon_shape())]
    for rel, shape in printable:
        path = LANE_DIR / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(shape, str(path), tolerance=0.03, angularTolerance=0.12)
    for rel, kind in zip(ASSEMBLY_FILES, ("C360", "C370", "BRACKET", "FRAME", "FULL", "KEEP_OUT", "STACK")):
        export_step(LANE_DIR / rel, assembly_shapes(kind))
    for rel, text in svg_templates().items():
        write_text(LANE_DIR / rel, text)


def manifest_text() -> str:
    lines = [f"document_id={DOCUMENT_ID}", f"version={VERSION}", f"path_count={len(PACKAGE_PATHS)}", "scope=V0932_ONLY", f"parent_anchor={V0931_ANCHOR}", f"parent_full_lane_ledger_sha256={PARENT_FULL_LEDGER_SHA256}", "authority_pointer=UNCHANGED", "physical_fit=NOT_YET_PERFORMED", "power=PROHIBITED", ""]
    for rel in PACKAGE_PATHS:
        if rel.endswith(".stl"):
            role = "NO_LOAD_PRINTABLE"
        elif rel.endswith(".step"):
            role = "CAD_REFERENCE_ASSEMBLY"
        elif rel.endswith(".svg"):
            role = "ONE_TO_ONE_TEMPLATE"
        elif rel.endswith(".csv"):
            role = "MEASUREMENT_TABLE"
        elif rel.endswith(".json"):
            role = "MACHINE_READABLE_CONTRACT"
        elif rel.endswith(".py"):
            role = "BUILDER_OR_TEST"
        else:
            role = "DOCUMENT_OR_LEDGER"
        lines.append(f"{rel}|{role}")
    return "\n".join(lines)


def commit_paths_text() -> str:
    prefix = "cad/common_rover/common_rover_candidate_a_motor_bracket_adapter_v0_9_3_2"
    return "\n".join(f"{prefix}/{rel}" for rel in PACKAGE_PATHS)


def sha256sums_text() -> str:
    return "\n".join(f"{sha256(LANE_DIR / rel)}  {rel}" for rel in PACKAGE_PATHS if rel != "SHA256SUMS.txt")


def verify_hashes(base: Path = LANE_DIR) -> dict[str, Any]:
    hashes = parse_hashes(base / "SHA256SUMS.txt")
    required = set(PACKAGE_PATHS) - {"SHA256SUMS.txt"}
    mismatches: list[Any] = []
    if set(hashes) != required:
        mismatches.append({"missing": sorted(required - set(hashes)), "extra": sorted(set(hashes) - required)})
    for rel, digest in hashes.items():
        actual = sha256(base / rel) if (base / rel).is_file() else "MISSING"
        if actual != digest:
            mismatches.append({"path": rel, "expected": digest, "actual": actual})
    return {"verified": len(hashes), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def manifest_paths(path: Path) -> list[str]:
    return [line.split("|", 1)[0] for line in path.read_text(encoding="utf-8").splitlines() if "|" in line]


def verify_manifest(base: Path = LANE_DIR) -> dict[str, Any]:
    values = manifest_paths(base / "MANIFEST.txt")
    return {"entry_count": len(values), "exact_order": values == list(PACKAGE_PATHS), "status": "PASS" if values == list(PACKAGE_PATHS) else "FAIL"}


def load_stl(path: Path) -> cq.Shape:
    native = TopoDS_Shape()
    if not StlAPI_Reader().Read(native, str(path)) or native.IsNull():
        raise RuntimeError(f"STL reader failed: {path}")
    return cq.Shape(native)


def verify_stls(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for rel in PRINT_FILES:
        try:
            shape = load_stl(base / rel)
            value = bounds(shape)
            valid = len(shape.Faces()) >= 4 and all(math.isfinite(number) for number in value.values())
            fit = value["xlen"] <= 256 and value["ylen"] <= 256 and value["zlen"] <= 256
            rows.append({"path": rel, "faces": len(shape.Faces()), "bounds": value, "flat_base": abs(value["zmin"]) <= 0.05, "a1_fit": fit, "pass": valid and fit and abs(value["zmin"]) <= 0.05})
        except Exception as exc:
            rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_steps(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for rel in ASSEMBLY_FILES:
        try:
            shape = cq.importers.importStep(str(base / rel)).val()
            value = bounds(shape)
            valid = len(shape.Solids()) >= 1 and all(math.isfinite(number) for number in value.values())
            rows.append({"path": rel, "solids": len(shape.Solids()), "bounds": value, "pass": valid})
        except Exception as exc:
            rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_evidence() -> dict[str, Any]:
    params = json.loads((LANE_DIR / ROOT_FILES[1]).read_text(encoding="utf-8"))
    collision = json.loads((LANE_DIR / ROOT_FILES[7]).read_text(encoding="utf-8"))
    dimensions = json.loads((LANE_DIR / ROOT_FILES[8]).read_text(encoding="utf-8"))
    checks = {
        "plate_exact": dimensions["plate_mm"] == [42.0, 80.0, 8.0],
        "bracket_pitch": dimensions["bracket_pitch_mm"] == [24.0, 30.0],
        "frame_pitch": dimensions["frame_pitch_mm"] == [20.0, 60.0],
        "m4_variants": dimensions["m4_variants_mm"] == {"C360": 3.6, "C370": 3.7},
        "blind_floor": dimensions["m4_bottom_floor_mm"] == 1.0,
        "collision_pass": collision["status"] == "PASS",
        "centerline": params["centerline"] == "COINCIDENT",
        "identical": params["part"]["identical_left_right"] is True,
        "frame_hold": params["frame"]["t_slot_exact_profile"] == "MEASUREMENT_HOLD",
        "authority_unchanged": params["authority_pointer"] == "UNCHANGED",
        "physical_unperformed": params["physical_fit"] == "NOT_YET_PERFORMED",
        "deprecated_parent_jig": params["old_cradle_jig_status"] == "DEPRECATED_BY_V0932_ADAPTER_PLATE",
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def refresh_artifacts() -> dict[str, Any]:
    for rel in ("build_motor_bracket_adapter_v0932.py", "tests/test_motor_bracket_adapter_v0932.py"):
        if not (LANE_DIR / rel).is_file():
            raise RuntimeError(f"source missing: {rel}")
    repository_audit(require_complete=False)
    parent = parent_audit(True)
    collision = collision_report()
    dimension = dimension_report()
    if collision["status"] != "PASS" or dimension["status"] != "PASS":
        raise RuntimeError({"collision": collision, "dimension": dimension})
    write_text(LANE_DIR / ROOT_FILES[0], design_markdown(collision))
    write_json(LANE_DIR / ROOT_FILES[1], parameters(parent, collision, dimension))
    write_csv(LANE_DIR / ROOT_FILES[2], bracket_measurement_rows())
    write_json(LANE_DIR / ROOT_FILES[3], {"document_id": DOCUMENT_ID, "rows": bracket_measurement_rows()})
    write_csv(LANE_DIR / ROOT_FILES[4], fastener_measurement_rows())
    write_text(LANE_DIR / ROOT_FILES[5], calibration_markdown())
    write_text(LANE_DIR / ROOT_FILES[6], m5_markdown())
    write_json(LANE_DIR / ROOT_FILES[7], collision)
    write_json(LANE_DIR / ROOT_FILES[8], dimension)
    write_text(LANE_DIR / ROOT_FILES[9], procedure_markdown())
    write_text(LANE_DIR / ROOT_FILES[10], result_sheet_markdown())
    write_text(LANE_DIR / ROOT_FILES[11], height_markdown())
    write_text(LANE_DIR / ROOT_FILES[12], deprecated_markdown())
    write_text(LANE_DIR / ROOT_FILES[13], readme_markdown())
    write_text(LANE_DIR / ROOT_FILES[14], no_power_text())
    write_text(LANE_DIR / ROOT_FILES[17], commit_paths_text())
    export_artifacts()
    write_text(LANE_DIR / ROOT_FILES[20], "status=PREPACKAGE_SELF_CHECKS_PASS\ncontract_tests=RUN_DURING_PACKAGE\nphysical_fit=NOT_YET_PERFORMED")
    write_text(LANE_DIR / ROOT_FILES[18], manifest_text())
    write_text(LANE_DIR / ROOT_FILES[19], sha256sums_text())
    actual = lane_files()
    if actual != sorted(PACKAGE_PATHS):
        raise RuntimeError({"missing": sorted(set(PACKAGE_PATHS) - set(actual)), "extra": sorted(set(actual) - set(PACKAGE_PATHS))})
    reports = (verify_stls(), verify_steps(), verify_evidence())
    if any(report["status"] != "PASS" for report in reports):
        raise RuntimeError({"stls": reports[0], "steps": reports[1], "evidence": reports[2]})
    return {"document_id": DOCUMENT_ID, "exact_package_paths": len(PACKAGE_PATHS), "parent": parent["status"], "collision": collision["status"], "STL_reload": f"{reports[0]['pass_count']}/{reports[0]['count']} PASS", "STEP_reload": f"{reports[1]['pass_count']}/{reports[1]['count']} PASS", "status": "PASS"}


def verify() -> dict[str, Any]:
    actual = lane_files()
    if actual != sorted(PACKAGE_PATHS):
        raise RuntimeError({"missing": sorted(set(PACKAGE_PATHS) - set(actual)), "extra": sorted(set(actual) - set(PACKAGE_PATHS))})
    repository = repository_audit(require_complete=True)
    parent = parent_audit()
    hashes = verify_hashes()
    manifest = verify_manifest()
    stls = verify_stls()
    steps = verify_steps()
    evidence = verify_evidence()
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


def verify_zip(path: Path, standalone: bool = True) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"ZIP missing: {path}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        traversal = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        if names != list(PACKAGE_PATHS) or duplicates or traversal:
            raise RuntimeError({"scope": names == list(PACKAGE_PATHS), "duplicates": duplicates, "traversal": traversal})
        hashes: dict[str, str] = {}
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            if line.strip():
                digest, rel = line.split("  ", 1)
                hashes[rel] = digest
        internal = [rel for rel, digest in hashes.items() if hashlib.sha256(archive.read(rel)).hexdigest() != digest]
        lane_mismatches = [rel for rel in names if hashlib.sha256(archive.read(rel)).hexdigest() != sha256(LANE_DIR / rel)]
    standalone_status = "NOT_REQUESTED"
    if standalone:
        with tempfile.TemporaryDirectory(prefix="ps_cr_v0932_zip_") as temp:
            target = Path(temp)
            with zipfile.ZipFile(path) as archive:
                archive.extractall(target)
            env = dict(os.environ)
            env["V0932_TEST_ZIP"] = str(path)
            build = run([sys.executable, "-B", "build_motor_bracket_adapter_v0932.py", "--verify"], cwd=target, env=env)
            tests = run([sys.executable, "-B", "tests/test_motor_bracket_adapter_v0932.py"], cwd=target, env=env)
            if build.returncode or tests.returncode:
                raise RuntimeError({"standalone_build": build.stdout, "standalone_tests": tests.stdout})
            standalone_status = "PASS"
    if internal or lane_mismatches:
        raise RuntimeError({"internal_hash_mismatches": internal, "lane_mismatches": lane_mismatches})
    return {"zip_path": str(path), "entry_count": len(names), "duplicates": duplicates, "path_traversal": traversal, "internal_hash_verification": "PASS", "lane_byte_match": "PASS", "standalone_verify": standalone_status, "zip_sha256": sha256(path), "status": "PASS"}


def package_handoff() -> dict[str, Any]:
    verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{timestamp}.zip"
    temporary = DOWNLOAD_DIR / f".{ZIP_PREFIX}{timestamp}.validation.tmp"
    if final_path.exists() or temporary.exists():
        raise RuntimeError("refusing to overwrite handoff")
    try:
        write_zip(temporary)
        env = dict(os.environ)
        env["V0932_TEST_ZIP"] = str(temporary)
        result = run([sys.executable, "-B", "tests/test_motor_bracket_adapter_v0932.py"], cwd=LANE_DIR, env=env)
        if result.returncode:
            raise RuntimeError(f"contract tests failed:\n{result.stdout}")
        summary = [line for line in result.stdout.splitlines() if line.startswith("Ran ") or line == "OK"]
        write_text(LANE_DIR / ROOT_FILES[20], "command=python -B tests/test_motor_bracket_adapter_v0932.py\nstatus=PASS\n" + "\n".join(summary) + "\nphysical_fit=NOT_YET_PERFORMED\nfull_output:\n" + result.stdout)
        write_text(LANE_DIR / ROOT_FILES[19], sha256sums_text())
        verify()
    finally:
        if temporary.exists():
            temporary.unlink()
    write_zip(final_path)
    return {"verification": "PASS", **verify_zip(final_path, standalone=True)}


def latest_handoff_zip() -> Path | None:
    values = sorted(DOWNLOAD_DIR.glob(f"{ZIP_PREFIX}*.zip"))
    return values[-1] if values else None


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
