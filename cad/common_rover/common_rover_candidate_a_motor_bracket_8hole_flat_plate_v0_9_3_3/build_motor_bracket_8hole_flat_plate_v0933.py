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


DOCUMENT_ID = "PS-CR-V0933-MOTOR-BRACKET-8HOLE-FLAT-PLATE"
VERSION = "0.9.3.3"
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
V0931_DIR = REPO_ROOT / "cad/common_rover/common_rover_candidate_a_physical_mockup_v0_9_3_1"
V0932_DIR = REPO_ROOT / "cad/common_rover/common_rover_candidate_a_motor_bracket_adapter_v0_9_3_2"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_v0_9_3_3_8Hole_Flat_Plate_"

EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
ANCHOR = "198a708395df6e43556a744ae9c5629b50360e2f"
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
PARENT_CONTRACTS = {
    "v0.9.3.1": (V0931_DIR, 46, "2f58d6fddab3c9c0f3deed09188974d3642dcdc89e94b0240eec869a7de770f8"),
    "v0.9.3.2": (V0932_DIR, 39, "116f3283a634a80f61284f0a46a99f0ac07de2f5d8ebdd457faa64fafa2b77da"),
}

PLATE_X = 42.0
PLATE_Y = 80.0
PETG_Z = 6.0
METAL_Z = 3.0
OUTER_RADIUS = 3.0
M3_DIAMETER = 3.4
M5_DIAMETER = 5.7
M3_HOLES = ((-12.0, -15.0), (12.0, -15.0), (-12.0, 15.0), (12.0, 15.0))
M5_HOLES = ((-10.0, -30.0), (10.0, -30.0), (-10.0, 30.0), (10.0, 30.0))
ALL_HOLES = tuple(("M3", M3_DIAMETER, x, y) for x, y in M3_HOLES) + tuple(("M5", M5_DIAMETER, x, y) for x, y in M5_HOLES)
FRAME_X, FRAME_Y, FRAME_Z = 40.0, 120.0, 20.0
FRAME_SLOT_X = 10.0
BRACKET_X, BRACKET_Y, BRACKET_Z = 40.2, 40.0, 3.1
SPACER_HEIGHTS = (6.0, 8.0, 10.0)
A1_BUILD_VOLUME = (256.0, 256.0, 256.0)

ROOT_FILES = [
    "motor_bracket_8hole_flat_plate_design_v0933.md",
    "motor_bracket_8hole_flat_plate_parameters_v0933.json",
    "motor_bracket_8hole_measurements_v0933.csv",
    "motor_bracket_8hole_measurements_v0933.json",
    "hole_coordinate_table_v0933.csv",
    "petg_flat_plate_contract_v0933.md",
    "metal_flat_plate_reference_v0933.md",
    "fastener_stack_concept_v0933.md",
    "spacer_height_hold_v0933.md",
    "physical_fit_procedure_v0933.md",
    "physical_result_sheet_v0933.md",
    "candidate_a_height_impact_v0933.md",
    "v0932_supersession_notice_v0933.md",
    "README_HANDOFF.md",
    "NO_POWER_NO_LOAD_ONLY.txt",
    "build_motor_bracket_8hole_flat_plate_v0933.py",
    "tests/test_motor_bracket_8hole_flat_plate_v0933.py",
    "COMMIT_PATHS.txt",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "test_results_v0933.txt",
]
PRINT_FILES = ["artifacts/print/PS_CR_V0933_MOTOR_BRACKET_8HOLE_FLAT_PLATE_PETG_T6.stl"]
ASSEMBLY_FILES = [
    "artifacts/assemblies/PS_CR_V0933_8HOLE_FLAT_PLATE_PETG_T6.step",
    "artifacts/assemblies/PS_CR_V0933_8HOLE_FLAT_PLATE_METAL_T3_REFERENCE.step",
    "artifacts/assemblies/PS_CR_V0933_PLATE_WITH_BRACKET_PROXY.step",
    "artifacts/assemblies/PS_CR_V0933_PLATE_WITH_2040_PROXY.step",
    "artifacts/assemblies/PS_CR_V0933_FULL_STACK_SPACER_H6_REFERENCE.step",
    "artifacts/assemblies/PS_CR_V0933_FULL_STACK_SPACER_H8_REFERENCE.step",
    "artifacts/assemblies/PS_CR_V0933_FULL_STACK_SPACER_H10_REFERENCE.step",
    "artifacts/assemblies/PS_CR_V0933_TWO_IDENTICAL_PLATES_REFERENCE.step",
]
TEMPLATE_FILES = [
    "artifacts/templates/PS_CR_V0933_TOP_VIEW.svg",
    "artifacts/templates/PS_CR_V0933_BOTTOM_VIEW.svg",
    "artifacts/templates/PS_CR_V0933_SECTION_X.svg",
    "artifacts/templates/PS_CR_V0933_SECTION_Y.svg",
    "artifacts/templates/PS_CR_V0933_8HOLE_PATTERN_1_TO_1.svg",
    "artifacts/templates/PS_CR_V0933_METAL_DRILL_TEMPLATE_1_TO_1.svg",
    "artifacts/templates/PS_CR_V0933_METAL_DRILL_TEMPLATE.dxf",
    "artifacts/templates/PS_CR_V0933_STACK_HEIGHT_REFERENCE.svg",
]
PACKAGE_PATHS = tuple(ROOT_FILES + PRINT_FILES + ASSEMBLY_FILES + TEMPLATE_FILES)
if len(PACKAGE_PATHS) != 38 or len(set(PACKAGE_PATHS)) != 38:
    raise RuntimeError("v0.9.3.3 package must contain exactly 38 unique paths")


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


def run(command: list[str], cwd: Path = REPO_ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stdout}{result.stderr}")
    return result.stdout.strip()


def live_repository() -> bool:
    return run(["git", "rev-parse", "--show-toplevel"], cwd=REPO_ROOT).returncode == 0


def lane_files(base: Path = LANE_DIR) -> list[str]:
    return sorted(path.relative_to(base).as_posix() for path in base.rglob("*") if path.is_file())


def full_lane_ledger(path: Path) -> dict[str, Any]:
    rows = [f"{item.relative_to(path).as_posix()}\t{sha256(item)}" for item in sorted((p for p in path.rglob("*") if p.is_file()), key=lambda p: p.relative_to(path).as_posix())]
    payload = ("\n".join(rows) + "\n").encode("utf-8")
    return {"file_count": len(rows), "sha256": hashlib.sha256(payload).hexdigest()}


def parent_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    results: dict[str, Any] = {}
    for version, (path, count, expected_hash) in PARENT_CONTRACTS.items():
        if not live:
            results[version] = {"mode": "STANDALONE_EMBEDDED_EVIDENCE", "file_count": count, "ledger_sha256": expected_hash, "status": "PASS"}
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        ledger = full_lane_ledger(path)
        worktree = [line for line in git("diff", "--name-only", "--", rel).splitlines() if line]
        staged = [line for line in git("diff", "--cached", "--name-only", "--", rel).splitlines() if line]
        tracked = [line for line in git("ls-files", rel).splitlines() if line]
        checks = {
            "exists": path.is_dir(),
            "file_count": ledger["file_count"] == count,
            "full_ledger": ledger["sha256"] == expected_hash,
            "worktree_clean": not worktree,
            "index_clean": not staged,
            "tracked_contract": (len(tracked) == count) if version == "v0.9.3.1" else (len(tracked) == 0),
        }
        if not all(checks.values()):
            raise RuntimeError({"parent": version, "checks": checks, "worktree": worktree, "staged": staged, "tracked": len(tracked), "ledger": ledger})
        results[version] = {"checks": checks, "file_count": count, "ledger_sha256": expected_hash, "status": "PASS"}
    return {"parents": results, "status": "PASS"}


def repository_audit(require_complete: bool = True) -> dict[str, Any]:
    if not live_repository():
        return {"mode": "STANDALONE_HANDOFF", "status": "PASS"}
    root = str(Path(git("rev-parse", "--show-toplevel")).resolve())
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    git("cat-file", "-e", f"{ANCHOR}^{{commit}}")
    ancestor = run(["git", "merge-base", "--is-ancestor", ANCHOR, head]).returncode == 0
    tracked_diff = {line.replace("\\", "/") for line in git("diff", "--name-only").splitlines() if line}
    staged_diff = {line.replace("\\", "/") for line in git("diff", "--cached", "--name-only").splitlines() if line}
    untracked = [line.replace("\\", "/") for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line]
    lane_rel = LANE_DIR.relative_to(REPO_ROOT).as_posix()
    lane_untracked = sorted(path[len(lane_rel) + 1:] for path in untracked if path.startswith(lane_rel + "/"))
    ignored = [line for line in git("ls-files", "--others", "--ignored", "--exclude-standard", "--", lane_rel).splitlines() if line]
    actual = lane_files()
    forbidden = [path for path in actual if "__pycache__" in path.lower() or path.lower().endswith((".pyc", ".pyo", ".fcstd", ".blend", ".tmp"))]
    pointers = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_POINTER_HASHES}
    parents = parent_audit(True)
    checks = {
        "root": root.lower() == str(REPO_ROOT.resolve()).lower(),
        "branch": branch == EXPECTED_BRANCH,
        "anchor_ancestor": ancestor,
        "tracked_diff_preserved": tracked_diff == EXPECTED_TRACKED_DIFF,
        "staged_zero": not staged_diff,
        "authority_hashes": pointers == AUTHORITY_POINTER_HASHES,
        "parent_protection": parents["status"] == "PASS",
        "lane_scope": set(actual).issubset(set(PACKAGE_PATHS)),
        "lane_git_scope_match": lane_untracked == actual,
        "lane_complete": actual == sorted(PACKAGE_PATHS) if require_complete else True,
        "lane_ignored_zero": not ignored,
        "forbidden_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_guard": checks, "actual": actual, "lane_untracked": lane_untracked, "ignored": ignored, "forbidden": forbidden})
    return {
        "mode": "LIVE_REPOSITORY", "root": root, "branch": branch, "head": head, "anchor": ANCHOR,
        "anchor_ancestor": ancestor, "commit_distance": int(git("rev-list", "--count", f"{ANCHOR}..{head}")),
        "tracked_diff": sorted(tracked_diff), "staged_diff": sorted(staged_diff), "untracked_total": len(untracked),
        "lane_untracked_count": len(lane_untracked), "checks": checks, "status": "PASS",
    }


def compound(shapes: Iterable[cq.Shape]) -> cq.Shape:
    values = list(shapes)
    if not values:
        raise ValueError("compound requires shapes")
    return cq.Compound.makeCompound(values)


def box(dx: float, dy: float, dz: float, center: tuple[float, float, float]) -> cq.Shape:
    return cq.Workplane("XY").box(dx, dy, dz).translate(center).val()


def cylinder_z(diameter: float, height: float, x: float, y: float, z0: float) -> cq.Shape:
    return cq.Solid.makeCylinder(diameter / 2.0, height, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def rounded_blank(thickness: float) -> cq.Shape:
    return cq.Workplane("XY").box(PLATE_X, PLATE_Y, thickness, centered=(True, True, False)).edges("|Z").fillet(OUTER_RADIUS).val()


def flat_plate(thickness: float) -> cq.Shape:
    result = rounded_blank(thickness)
    voids = compound(cylinder_z(diameter, thickness + 2.0, x, y, -1.0) for _, diameter, x, y in ALL_HOLES)
    return result.cut(voids)


def bracket_proxy(z_bottom: float = PETG_Z) -> cq.Shape:
    result = box(BRACKET_X, BRACKET_Y, BRACKET_Z, (0.0, 0.0, z_bottom + BRACKET_Z / 2.0))
    voids = compound(cylinder_z(M3_DIAMETER, BRACKET_Z + 0.4, x, y, z_bottom - 0.2) for x, y in M3_HOLES)
    return result.cut(voids)


def frame_proxy(z_top: float = 0.0) -> list[cq.Shape]:
    body = box(FRAME_X, FRAME_Y, FRAME_Z, (0.0, 0.0, z_top - FRAME_Z / 2.0))
    witnesses = [box(0.4, FRAME_Y, 0.25, (x, 0.0, z_top + 0.125)) for x in (-FRAME_SLOT_X, FRAME_SLOT_X)]
    return [body, *witnesses]


def spacer_witnesses(height: float) -> list[cq.Shape]:
    return [cylinder_z(2.0, height, x, y, 0.0) for x, y in M5_HOLES]


def full_stack(height: float) -> list[cq.Shape]:
    plate = flat_plate(PETG_Z).translate(cq.Vector(0, 0, height))
    bracket = bracket_proxy(height + PETG_Z)
    return [*frame_proxy(), *spacer_witnesses(height), plate, bracket]


def bounds(shape: cq.Shape) -> dict[str, float]:
    value = shape.BoundingBox()
    return {name: round(number, 6) for name, number in {
        "xmin": value.xmin, "xmax": value.xmax, "ymin": value.ymin, "ymax": value.ymax,
        "zmin": value.zmin, "zmax": value.zmax, "xlen": value.xlen, "ylen": value.ylen, "zlen": value.zlen,
    }.items()}


def intersection_volume(left: cq.Shape, right: cq.Shape) -> float:
    return max(0.0, float(left.intersect(right).Volume()))


def geometry_report() -> dict[str, Any]:
    shape = flat_plate(PETG_Z)
    petg_bounds = bounds(shape)
    metal_bounds = bounds(flat_plate(METAL_Z))
    ligaments = {
        "m3_x_mm": PLATE_X / 2 - max(abs(x) for x, _ in M3_HOLES) - M3_DIAMETER / 2,
        "m3_y_mm": PLATE_Y / 2 - max(abs(y) for _, y in M3_HOLES) - M3_DIAMETER / 2,
        "m5_x_mm": PLATE_X / 2 - max(abs(x) for x, _ in M5_HOLES) - M5_DIAMETER / 2,
        "m5_y_mm": PLATE_Y / 2 - max(abs(y) for _, y in M5_HOLES) - M5_DIAMETER / 2,
    }
    pairs: list[dict[str, Any]] = []
    for index, (kind_a, diameter_a, xa, ya) in enumerate(ALL_HOLES):
        for kind_b, diameter_b, xb, yb in ALL_HOLES[index + 1:]:
            center = math.hypot(xb - xa, yb - ya)
            pairs.append({"types": f"{kind_a}-{kind_b}", "center_distance_mm": center, "edge_gap_mm": center - (diameter_a + diameter_b) / 2})
    hole_voids = [cylinder_z(d, PETG_Z + 2.0, x, y, -1.0) for _, d, x, y in ALL_HOLES]
    pair_intersections = [intersection_volume(a, b) for i, a in enumerate(hole_voids) for b in hole_voids[i + 1:]]
    through_residuals = [intersection_volume(shape, void) for void in hole_voids]
    rounded_area = PLATE_X * PLATE_Y - (4.0 - math.pi) * OUTER_RADIUS**2
    hole_area = 4 * math.pi * (M3_DIAMETER / 2)**2 + 4 * math.pi * (M5_DIAMETER / 2)**2
    expected_volume = (rounded_area - hole_area) * PETG_Z
    planar_faces = [face for face in shape.Faces() if face.geomType() == "PLANE"]
    z_faces = [round(face.Center().z, 6) for face in planar_faces]
    report = {
        "plate_bounds_mm": petg_bounds,
        "metal_bounds_mm": metal_bounds,
        "solid_count": len(shape.Solids()),
        "hole_count": len(ALL_HOLES),
        "ligaments": {key: round(value, 6) for key, value in ligaments.items()},
        "minimum_edge_ligament_mm": round(min(ligaments.values()), 6),
        "pairwise_minimum_center_distance_mm": round(min(row["center_distance_mm"] for row in pairs), 6),
        "pairwise_minimum_edge_gap_mm": round(min(row["edge_gap_mm"] for row in pairs), 6),
        "pairwise_hole_intersection_max_volume_mm3": max(pair_intersections, default=0.0),
        "plate_to_hole_void_residual_max_volume_mm3": max(through_residuals, default=0.0),
        "expected_volume_mm3": round(expected_volume, 6),
        "actual_volume_mm3": round(shape.Volume(), 6),
        "volume_delta_mm3": round(abs(shape.Volume() - expected_volume), 9),
        "planar_face_z_mm": sorted(set(z_faces)),
        "top_bottom_planar": 0.0 in z_faces and PETG_Z in z_faces,
        "petg_metal_xy_identical": petg_bounds["xlen"] == metal_bounds["xlen"] and petg_bounds["ylen"] == metal_bounds["ylen"] and abs(shape.Volume() / PETG_Z - flat_plate(METAL_Z).Volume() / METAL_Z) < 1e-6,
        "pairwise": pairs,
    }
    checks = {
        "bounds": [petg_bounds["xlen"], petg_bounds["ylen"], petg_bounds["zlen"]] == [PLATE_X, PLATE_Y, PETG_Z],
        "metal_bounds": [metal_bounds["xlen"], metal_bounds["ylen"], metal_bounds["zlen"]] == [PLATE_X, PLATE_Y, METAL_Z],
        "single_solid": report["solid_count"] == 1,
        "exact_eight_holes": report["hole_count"] == 8,
        "hole_intersections_zero": report["pairwise_hole_intersection_max_volume_mm3"] < 1e-9,
        "all_holes_through": report["plate_to_hole_void_residual_max_volume_mm3"] < 1e-8,
        "minimum_ligament": report["minimum_edge_ligament_mm"] >= 5.0,
        "only_blank_minus_eight_holes": report["volume_delta_mm3"] < 1e-5,
        "top_bottom_planar": report["top_bottom_planar"],
        "same_xy": report["petg_metal_xy_identical"],
    }
    report["checks"] = checks
    report["status"] = "PASS" if all(checks.values()) else "FAIL"
    return report


def measurement_rows() -> list[dict[str, Any]]:
    return [
        {"category": "physical_fit", "parameter": "M3_CLEARANCE_HOLE_DIAMETER", "value": "3.4", "unit": "mm", "evidence": "physical", "status": "PASS / JUST_FIT"},
        {"category": "reference_only", "parameter": "M4_CLEARANCE_REFERENCE_DIAMETER", "value": "4.2", "unit": "mm", "evidence": "physical", "status": "PASS / JUST_FIT_REFERENCE_ONLY"},
        {"category": "measured", "parameter": "BRACKET_OUTER_X", "value": "40.2", "unit": "mm", "evidence": "measured", "status": "RECORDED"},
        {"category": "measured", "parameter": "BRACKET_OUTER_Y", "value": "40.0", "unit": "mm", "evidence": "measured", "status": "RECORDED"},
        {"category": "reference", "parameter": "BRACKET_THICKNESS_REFERENCE", "value": "3.1", "unit": "mm", "evidence": "measured candidate", "status": "REFERENCE"},
        {"category": "hold", "parameter": "BRACKET_CORNER_RADIUS", "value": "", "unit": "mm", "evidence": "unmeasured", "status": "MEASUREMENT_HOLD"},
        {"category": "physical", "parameter": "BRACKET_HOLE_PITCH_X", "value": "24.0", "unit": "mm", "evidence": "physical center distance", "status": "CONFIRMED"},
        {"category": "physical", "parameter": "BRACKET_HOLE_PITCH_Y", "value": "30.0", "unit": "mm", "evidence": "physical center distance", "status": "CONFIRMED"},
        {"category": "nominal", "parameter": "FRAME_TOP_WIDTH_X", "value": "40.0", "unit": "mm", "evidence": "2040 nominal", "status": "REFERENCE"},
        {"category": "hold", "parameter": "M5_SPACER_STACK_HEIGHT", "value": "6|8|10", "unit": "mm", "evidence": "comparison only", "status": "PHYSICAL_MEASUREMENT_HOLD"},
    ]


def hole_rows() -> list[dict[str, Any]]:
    rows = []
    for index, (kind, diameter, x, y) in enumerate(ALL_HOLES, start=1):
        rows.append({"hole_id": f"{kind}_HOLE_{index if kind == 'M3' else index - 4}", "fastener": kind, "diameter_mm": f"{diameter:.1f}", "x_mm": f"{x:.1f}", "y_mm": f"{y:.1f}", "z_start_mm": "0.0", "z_end_petg_mm": "6.0", "feature": "STRAIGHT_THROUGH_CLEARANCE", "status": "CANDIDATE"})
    return rows


def parameters(parents: dict[str, Any], geometry: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": DOCUMENT_ID, "version": VERSION, "anchor": ANCHOR,
        "design_principle": "SIMPLE_REPAIRABLE_FLAT_PLATE",
        "coordinate_system": {"common_rover": {"+X": "left", "+Y": "rear", "+Z": "up"}, "plate_local": {"origin": "XY_CENTER", "bottom": "Z=0"}},
        "centerline": "COINCIDENT", "left_part": "IDENTICAL", "right_part": "IDENTICAL", "quantity_required": 2,
        "plate": {"size_mm": [PLATE_X, PLATE_Y], "petg_thickness_mm": PETG_Z, "metal_reference_thickness_mm": METAL_Z, "corner_radius_mm": OUTER_RADIUS, "solid_count": 1, "flat_base_z0": True, "planar_top_bottom": True},
        "holes": {"M3": {"diameter_mm": M3_DIAMETER, "coordinates_mm": M3_HOLES, "pitch_mm": [24.0, 30.0], "count": 4}, "M5": {"diameter_mm": M5_DIAMETER, "coordinates_mm": M5_HOLES, "pitch_mm": [20.0, 60.0], "count": 4}, "total": 8, "all": "STRAIGHT_THROUGH_CLEARANCE"},
        "physical_fit": {"M3_3P4": "PASS / JUST_FIT", "M4_4P2": "PASS / JUST_FIT_REFERENCE_ONLY", "M4_holes_in_plate": 0},
        "features_not_used": {name: False for name in ("heat_set_insert", "direct_thread", "blind_hole", "counterbore", "countersink", "nut_pocket", "rib", "boss", "cradle", "motor_retention", "stepped_geometry", "functional_surface_text")},
        "proxies": {"frame_mm": [FRAME_X, FRAME_Y, FRAME_Z], "frame_slot_center_x_mm": [-10.0, 10.0], "t_slot_exact_profile": "MEASUREMENT_HOLD", "bracket_mm": [BRACKET_X, BRACKET_Y, BRACKET_Z], "bracket_corner_radius": "MEASUREMENT_HOLD"},
        "spacer": {"comparison_heights_mm": SPACER_HEIGHTS, "status": "PHYSICAL_MEASUREMENT_HOLD", "M3_nut_exact_envelope": "MEASUREMENT_HOLD", "M5_nut_exact_envelope": "MEASUREMENT_HOLD"},
        "print": {"material": "PETG", "nozzle_mm": 0.4, "layer_height_mm": 0.20, "wall_loops_min": 5, "top_bottom_layers_min": 6, "infill_percent_candidate": [50, 100], "orientation": "FLAT_ON_BUILD_PLATE", "support": "NONE", "brim": "NOT_REQUIRED_CANDIDATE", "status": "RECOMMENDED_MOCKUP_ONLY", "bambu_a1_fit": True},
        "metal_plate_status": "DRILLING_REFERENCE_ONLY",
        "supersession": "V0932_M4_DIRECT_THREAD_VARIANTS=SUPERSEDED_BY_V0933_M3_M5_THROUGH_HOLE_FLAT_PLATE",
        "height": {"spacer_H6_total_z_increase_mm": 12.0, "spacer_H8_total_z_increase_mm": 14.0, "spacer_H10_total_z_increase_mm": 16.0, "candidate_a_motor_and_20T_old_z_mm": 105.0, "candidate_motor_and_20T_z_mm": [117.0, 119.0, 121.0], "existing_60T_and_selector_z_mm": 166.0, "status": "REVALIDATION_REQUIRED"},
        "approval": {"flat_plate_cad": "CONDITIONAL_PASS_CANDIDATE", "petg_print": "READY_FOR_SINGLE_PART_NO_LOAD_FIT_TEST", "fastener_torque": "HOLD", "belt_tension": "NOT_APPROVED", "powered_rotation": "NOT_APPROVED", "torque_load": "NOT_APPROVED", "field_deployment": "NOT_APPROVED", "authority_pointer": "UNCHANGED"},
        "geometry_report": geometry, "parent_protection": parents,
    }


def design_markdown(g: dict[str, Any]) -> str:
    return f"""# Common Rover Candidate A Motor Bracket 8-Hole Flat Adapter Plate v0.9.3.3

Status: `CONDITIONAL_PASS_CANDIDATE` / `NOT_FOR_POWERED_OPERATION`

## Design authority scope

This differential lane records a simple, repairable flat plate only. Current Common Rover authority pointers and the v0.9.3.1/v0.9.3.2 parent lanes remain unchanged. v0.9.3.2 is preserved as evidence; its M4 direct-thread variants are superseded only by this lane's M3/M5 through-hole concept.

## Functional geometry

- PETG plate: 42.0 × 80.0 × 6.0 mm, R3.0, flat base Z=0.
- Metal drilling reference: same XY geometry, 3.0 mm thick.
- Inner interface: four straight Ø3.4 mm M3 clearance through-holes at X=±12, Y=±15 mm.
- Outer interface: four straight Ø5.7 mm M5 clearance through-holes at X=±10, Y=±30 mm.
- One solid; no blind holes, threads, counterbores, countersinks, pockets, ribs, bosses, cradle, steps, or functional-surface text.
- Left and right use the identical part and identical STL; quantity required is two, but print one first.

## Automated geometry evidence

- Minimum edge ligament: **{g['minimum_edge_ligament_mm']:.2f} mm** (requirement ≥5.0 mm).
- Minimum hole-center distance: **{g['pairwise_minimum_center_distance_mm']:.6f} mm**.
- Minimum hole-edge gap: **{g['pairwise_minimum_edge_gap_mm']:.6f} mm**.
- Maximum pairwise hole intersection volume: **{g['pairwise_hole_intersection_max_volume_mm3']:.9f} mm³**.
- Maximum plate residual inside all eight cutting cylinders: **{g['plate_to_hole_void_residual_max_volume_mm3']:.9f} mm³**.
- Blank-minus-eight-holes analytic/CAD volume delta: **{g['volume_delta_mm3']:.9f} mm³**.

## Physical evidence and HOLDs

Ø3.4 M3 is `PASS / JUST_FIT`. Ø4.2 M4 is retained as `PASS / JUST_FIT_REFERENCE_ONLY`; the v0.9.3.3 plate contains zero M4 holes. Exact M3/M5 nut, washer, screw-tip, T-slot, and torque envelopes remain `MEASUREMENT_HOLD`. H6/H8/H10 are comparative height witnesses, not released spacer dimensions.

No belt tension, powered rotation, torque load, production drilling, field deployment, or authority update is approved.
"""


def petg_markdown() -> str:
    return """# PETG flat plate contract v0.9.3.3

Part: `PS_CR_V0933_MOTOR_BRACKET_8HOLE_FLAT_PLATE_PETG_T6`

- Geometry: 42×80×6 mm, R3, eight straight through-holes, one solid.
- Material: PETG candidate; nozzle 0.4 mm; layer 0.20 mm.
- Walls: at least 5; top/bottom layers: at least 6; infill: 50–100% candidate.
- Orientation: flat on build plate; support: none; brim: not-required candidate.
- Status: `RECOMMENDED_MOCKUP_ONLY`.
- Use the same STL for left and right. Quantity two; print one first and complete the no-load fit test.
"""


def metal_markdown() -> str:
    return """# Metal flat plate drilling reference v0.9.3.3

The reference is 42×80×3 mm with R3 corners and exactly the same eight-hole XY pattern as the PETG part: four Ø3.4 M3 holes and four Ø5.7 M5 holes. Candidate materials are aluminum, steel, or stainless sheet.

Status: `DRILLING_REFERENCE_ONLY`. Material, thickness, drill process, deburring, and production release remain HOLD. The 1:1 SVG/DXF must be print-scaled at 100% with fit-to-page and automatic scaling disabled; confirm the 50 mm bar before center-punching.
"""


def stack_markdown() -> str:
    return """# Fastener stack concept v0.9.3.3

Top to bottom: JGB37-520 motor; existing metal bracket; M3 bolt; v0.9.3.3 flat plate; underside M3 nut; M5 nut/spacer height candidate; 2040 frame; in-slot T-nut. The M3 fastener passes through both bracket and plate. Four outer M5 fasteners locate the plate to the frame.

Exact M3/M5 nut, washer, screw-head, screw-tip, tool, and T-slot envelopes are `MEASUREMENT_HOLD`. Proxy cylinders in the comparison STEP files are height witnesses only and are not nut geometry. Fastener torque is HOLD; initial work is non-powered hand-tight fit only.
"""


def spacer_markdown() -> str:
    return """# Spacer height HOLD v0.9.3.3

`M5_SPACER_STACK_HEIGHT = PHYSICAL_MEASUREMENT_HOLD`.

H6, H8, and H10 mm are displayed only as comparative height envelopes. With the 6 mm PETG plate they give +12, +14, and +16 mm total Z increases. Select no final value until M3 nut/screw-tip clearance, M5 head/washer clearance, level four-point support, tool access, belt plane, guard, total height, and cable routing are physically revalidated.
"""


def procedure_markdown() -> str:
    steps = [
        "Print only one PETG T6 plate.", "Confirm all eight holes are fully open.", "Pass an M3 screw through each Ø3.4 hole.", "Pass an M5 screw through each Ø5.7 hole.",
        "Trial-position the M5 bolts and T-nuts on the 2040 frame.", "Install the same M5 nut/spacer construction at all four positions.", "Equalize all four spacer heights.", "Place the plate on the M5 spacers.",
        "Check plate rocking and tilt.", "Place the metal motor bracket on the plate.", "Align the bracket M3 holes with the plate M3 holes.", "Insert the M3 bolts.",
        "Install M3 nuts below the plate.", "Confirm M3 nuts and screw tips do not contact the 2040 frame.", "Confirm M5 heads and washers do not interfere with the bracket.", "Confirm equal four-point plate support.",
        "Confirm full-face seating of the metal bracket.", "Move the assembly lightly by hand and check for large play.", "Measure the motor-shaft height.", "Finish without applying power.",
    ]
    return "# Physical fit procedure v0.9.3.3\n\nScope: single-part, no-load, no-power trial fit. `FASTENER_TORQUE = MEASUREMENT_HOLD`; hand-tight only without deforming PETG.\n\n" + "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1)) + "\n\nDo not tension a belt, rotate under power, apply torque load, or deploy."


def result_sheet_markdown() -> str:
    return """# Physical result sheet v0.9.3.3

Date/operator: ____________________

| Check | PASS / FAIL / HOLD | Measured value / observation |
|---|---|---|
| All eight holes open | | |
| Four M3 screws pass freely | | |
| Four M5 screws pass freely | | |
| Bracket four-hole alignment | | |
| Plate level and four-point supported | | |
| M3 nuts/tips clear 2040 | | |
| M5 heads/washers clear bracket | | |
| Bracket fully seated | | |
| PETG free from crack/whitening/indentation | | |
| No large play | | |
| Motor shaft Z | HOLD | |

No-load result: __________. Power, torque, belt tension, and field deployment remain NOT_APPROVED regardless of this sheet.
"""


def height_markdown() -> str:
    return """# Candidate A height impact v0.9.3.3

For PETG T6, total Z increase equals spacer height plus 6 mm plate thickness: H6 → +12 mm, H8 → +14 mm, H10 → +16 mm. Relative to the Candidate A reference motor/20T shaft Z=105 mm, comparison positions are Z=117, 119, and 121 mm. The 60T pulley and selector reference remain Z=166 mm unless a later authority changes them.

All three require revalidation of motor-shaft Z, 20T/60T height difference, belt plane, selector-shaft Z, guard height, total rover height, and cable routing. `HEIGHT_INTEGRATION_STATUS = REVALIDATION_REQUIRED`; no Candidate A authority is updated here.
"""


def supersession_markdown() -> str:
    return """# v0.9.3.2 supersession notice

`V0932_M4_DIRECT_THREAD_VARIANTS = SUPERSEDED_BY_V0933_M3_M5_THROUGH_HOLE_FLAT_PLATE`

Physical inspection established that the metal bracket interface is M3. This lane therefore uses four Ø3.4 M3 clearance through-holes and four Ø5.7 M5 clearance through-holes. Ø4.2 M4 remains reference-only and is not present in the plate. The v0.9.3.2 lane is preserved byte-for-byte and is not deleted or rewritten.
"""


def readme_markdown() -> str:
    return """# README_HANDOFF — v0.9.3.3

Standalone differential package for the Common Rover Candidate A simple 8-hole flat adapter. It contains one printable PETG plate, eight STEP references, six 1:1 SVG/reference drawings plus one stack drawing, one DXF drilling template, source, tests, and contracts.

Run with the validated Python/CadQuery environment:

```text
python -B build_motor_bracket_8hole_flat_plate_v0933.py --verify
python -B tests/test_motor_bracket_8hole_flat_plate_v0933.py
```

The printable part is a flat 42×80×6 mm R3 plate with exactly eight straight through-holes. Print one before the second identical copy. No power, belt tension, torque load, production drilling, or field deployment is approved. Authority pointers and v0.9.3.1/v0.9.3.2 are unchanged.
"""


def no_power_text() -> str:
    return """NO POWER. NO BELT TENSION. NO TORQUE LOAD.
This package permits one PETG part to be printed for a hand-tight, no-load physical fit check only.
POWERED_ROTATION=NOT_APPROVED
FIELD_DEPLOYMENT=NOT_APPROVED
AUTHORITY_POINTER=UNCHANGED
"""


def svg_header(title: str, width: float = 180, height: float = 140, view_box: str = "-90 -70 180 140") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="{view_box}">
<title>{title}</title><desc>Units mm; SCALE 1:1; print 100%; fit to page OFF; automatic scaling OFF.</desc>
<style>text{{font-family:Arial,sans-serif;font-size:3px;fill:#111}} .o{{fill:none;stroke:#111;stroke-width:.35}} .c{{fill:none;stroke:#137;stroke-width:.2;stroke-dasharray:2 1}} .m3{{fill:none;stroke:#087;stroke-width:.35}} .m5{{fill:none;stroke:#b40;stroke-width:.35}} .d{{fill:none;stroke:#555;stroke-width:.18}}</style>'''


def scale_bar() -> str:
    return '<line x1="-25" y1="60" x2="25" y2="60" stroke="#111" stroke-width="1"/><line x1="-25" y1="58" x2="-25" y2="62" stroke="#111"/><line x1="25" y1="58" x2="25" y2="62" stroke="#111"/><text x="-8" y="57">50 mm CHECK BAR</text><text x="-38" y="67">SCALE 100% · FIT OFF · AUTOSCALE OFF</text>'


def top_pattern(title: str, bottom: bool = False, drilling: bool = False) -> str:
    label = "BOTTOM VIEW (viewed from below)" if bottom else "TOP VIEW"
    suffix = " · CENTER PUNCH REFERENCE" if drilling else ""
    parts = [svg_header(title), f'<text x="-85" y="-64">{label}{suffix} · 42×80 R3 · SCALE 1:1</text>', '<rect class="o" x="-21" y="-40" width="42" height="80" rx="3"/>', '<line class="c" x1="-35" y1="0" x2="35" y2="0"/><line class="c" x1="0" y1="-50" x2="0" y2="50"/>']
    for kind, diameter, x, y in ALL_HOLES:
        shown_x = -x if bottom else x
        cls = "m3" if kind == "M3" else "m5"
        parts.append(f'<circle class="{cls}" cx="{shown_x}" cy="{-y}" r="{diameter/2}"/><path class="c" d="M {shown_x-2.5} {-y} H {shown_x+2.5} M {shown_x} {-y-2.5} V {-y+2.5}"/><text x="{shown_x+3}" y="{-y+1}">{kind} Ø{diameter:.1f}</text>')
    parts += ['<text x="27" y="-28">M5 pitch 20×60</text><text x="27" y="-18">M3 pitch 24×30</text>', '<path class="d" d="M -12 24 V 32 M 12 24 V 32 M -12 29 H 12"/><text x="-3" y="28">24</text>', '<path class="d" d="M 26 -15 H 34 M 26 15 H 34 M 31 -15 V 15"/><text x="32" y="1">30</text>', '<path class="d" d="M -10 36 V 44 M 10 36 V 44 M -10 41 H 10"/><text x="-3" y="40">20</text>', '<path class="d" d="M 38 -30 H 46 M 38 30 H 46 M 43 -30 V 30"/><text x="44" y="1">60</text>', scale_bar(), '</svg>']
    return "\n".join(parts)


def section_svg(axis: str) -> str:
    is_x = axis == "X"
    width = 42 if is_x else 80
    holes = [(-12, M3_DIAMETER), (12, M3_DIAMETER), (-10, M5_DIAMETER), (10, M5_DIAMETER)] if is_x else [(-30, M5_DIAMETER), (-15, M3_DIAMETER), (15, M3_DIAMETER), (30, M5_DIAMETER)]
    parts = [svg_header(f"SECTION {axis}", 180, 90, "-90 -20 180 90"), f'<text x="-85" y="-14">SECTION {axis} · PETG T6 · ALL HOLES STRAIGHT THROUGH</text>', f'<rect class="o" x="{-width/2}" y="0" width="{width}" height="6"/>']
    for pos, diameter in holes:
        parts.append(f'<rect x="{pos-diameter/2}" y="0" width="{diameter}" height="6" fill="white" stroke="#137" stroke-width=".2"/>')
    parts += ['<path class="d" d="M -30 0 H -36 M -30 6 H -36 M -33 0 V 6"/><text x="-42" y="4">6 mm</text>', '<text x="-35" y="14">FLAT BASE Z=0 · PLANAR TOP Z=6 · NO BLIND FEATURES</text>', scale_bar(), '</svg>']
    return "\n".join(parts)


def stack_svg() -> str:
    parts = [svg_header("STACK HEIGHT REFERENCE", 180, 150, "-90 -75 180 150"), '<text x="-85" y="-68">H6 / H8 / H10 COMPARISON ONLY · PHYSICAL_MEASUREMENT_HOLD</text>']
    for i, h in enumerate(SPACER_HEIGHTS):
        x = -65 + i * 50
        parts += [f'<rect class="o" x="{x}" y="30" width="40" height="20"/><text x="{x+2}" y="47">2040 proxy</text>', f'<rect class="d" x="{x+5}" y="{30-h}" width="2" height="{h}"/><rect class="d" x="{x+33}" y="{30-h}" width="2" height="{h}"/>', f'<rect class="o" x="{x-1}" y="{24-h}" width="42" height="6"/><rect class="o" x="{x}" y="{20.9-h}" width="40.2" height="3.1"/>', f'<text x="{x+2}" y="{15-h}">H{int(h)}: +{int(h+6)} mm</text>']
    parts += ['<text x="-80" y="64">M3/M5 NUT, WASHER, TOOL ENVELOPES = MEASUREMENT_HOLD</text>', scale_bar(), '</svg>']
    return "\n".join(parts)


def svg_templates() -> dict[str, str]:
    return {
        TEMPLATE_FILES[0]: top_pattern("PS CR V0933 TOP VIEW"),
        TEMPLATE_FILES[1]: top_pattern("PS CR V0933 BOTTOM VIEW", bottom=True),
        TEMPLATE_FILES[2]: section_svg("X"),
        TEMPLATE_FILES[3]: section_svg("Y"),
        TEMPLATE_FILES[4]: top_pattern("PS CR V0933 8-HOLE PATTERN 1:1"),
        TEMPLATE_FILES[5]: top_pattern("PS CR V0933 METAL DRILL TEMPLATE 1:1", drilling=True),
        TEMPLATE_FILES[7]: stack_svg(),
    }


def dxf_pair(code: int, value: Any) -> list[str]:
    return [str(code), str(value)]


def dxf_line(x1: float, y1: float, x2: float, y2: float, layer: str) -> list[str]:
    return dxf_pair(0, "LINE") + dxf_pair(8, layer) + dxf_pair(10, x1) + dxf_pair(20, y1) + dxf_pair(30, 0) + dxf_pair(11, x2) + dxf_pair(21, y2) + dxf_pair(31, 0)


def dxf_arc(cx: float, cy: float, radius: float, start: float, end: float) -> list[str]:
    return dxf_pair(0, "ARC") + dxf_pair(8, "OUTLINE") + dxf_pair(10, cx) + dxf_pair(20, cy) + dxf_pair(30, 0) + dxf_pair(40, radius) + dxf_pair(50, start) + dxf_pair(51, end)


def dxf_circle(x: float, y: float, radius: float, layer: str) -> list[str]:
    return dxf_pair(0, "CIRCLE") + dxf_pair(8, layer) + dxf_pair(10, x) + dxf_pair(20, y) + dxf_pair(30, 0) + dxf_pair(40, radius)


def dxf_text(x: float, y: float, value: str, height: float = 2.5) -> list[str]:
    return dxf_pair(0, "TEXT") + dxf_pair(8, "ANNOTATION") + dxf_pair(10, x) + dxf_pair(20, y) + dxf_pair(30, 0) + dxf_pair(40, height) + dxf_pair(1, value)


def drill_dxf() -> str:
    rows = ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
    rows += dxf_line(-18, -40, 18, -40, "OUTLINE") + dxf_line(-18, 40, 18, 40, "OUTLINE") + dxf_line(-21, -37, -21, 37, "OUTLINE") + dxf_line(21, -37, 21, 37, "OUTLINE")
    rows += dxf_arc(-18, -37, 3, 180, 270) + dxf_arc(18, -37, 3, 270, 360) + dxf_arc(18, 37, 3, 0, 90) + dxf_arc(-18, 37, 3, 90, 180)
    rows += dxf_line(-30, 0, 30, 0, "CENTERLINE") + dxf_line(0, -48, 0, 48, "CENTERLINE")
    for kind, diameter, x, y in ALL_HOLES:
        rows += dxf_circle(x, y, diameter / 2, kind)
        rows += dxf_line(x - 2.5, y, x + 2.5, y, "CENTERMARK") + dxf_line(x, y - 2.5, x, y + 2.5, "CENTERMARK")
    for x, y, value in [(-55, 50, "PS_CR_V0933 METAL DRILL TEMPLATE"), (-55, 46, "UNITS mm | SCALE 1:1 | PRINT 100%"), (-55, 42, "FIT TO PAGE OFF | AUTOMATIC SCALING OFF"), (26, 17, "M3 DIA 3.4 x4"), (26, 30, "M5 DIA 5.7 x4"), (26, 12, "M3 PITCH X 24"), (26, 8, "M3 PITCH Y 30"), (26, 4, "M5 PITCH X 20"), (26, 0, "M5 PITCH Y 60"), (26, -6, "OUTLINE 42x80 R3"), (-25, -50, "50 mm CHECK BAR"), (-55, -58, "DRILLING_REFERENCE_ONLY")]:
        rows += dxf_text(x, y, value)
    rows += dxf_line(-25, -54, 25, -54, "SCALE_BAR") + dxf_line(-25, -56, -25, -52, "SCALE_BAR") + dxf_line(25, -56, 25, -52, "SCALE_BAR")
    rows += ["0", "ENDSEC", "0", "EOF"]
    return "\n".join(rows)


def assembly_shapes(kind: str) -> list[cq.Shape]:
    plate = flat_plate(PETG_Z)
    if kind == "PETG": return [plate]
    if kind == "METAL": return [flat_plate(METAL_Z)]
    if kind == "BRACKET": return [plate, bracket_proxy()]
    if kind == "FRAME": return [*frame_proxy(), plate]
    if kind.startswith("H"): return full_stack(float(kind[1:]))
    return [plate.translate(cq.Vector(-30, 0, 0)), plate.translate(cq.Vector(30, 0, 0))]


def canonicalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"FILE_NAME\('.*?','.*?',", "FILE_NAME('PS-CR-V0933','2000-01-01T00:00:00',", text, count=1)
    text = re.sub(r"FILE_DESCRIPTION\(\(.*?\),'.*?'\);", "FILE_DESCRIPTION(('8-HOLE FLAT PLATE NO-LOAD EVIDENCE'),'2;1');", text, count=1)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def export_step(path: Path, shapes: Iterable[cq.Shape]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(compound(shapes), str(path))
    canonicalize_step(path)


def export_artifacts() -> None:
    printable = flat_plate(PETG_Z)
    stl = LANE_DIR / PRINT_FILES[0]
    stl.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(printable, str(stl), tolerance=0.03, angularTolerance=0.12)
    for rel, kind in zip(ASSEMBLY_FILES, ("PETG", "METAL", "BRACKET", "FRAME", "H6", "H8", "H10", "TWO")):
        export_step(LANE_DIR / rel, assembly_shapes(kind))
    for rel, payload in svg_templates().items():
        write_text(LANE_DIR / rel, payload)
    write_text(LANE_DIR / TEMPLATE_FILES[6], drill_dxf())


def manifest_text() -> str:
    lines = [f"document_id={DOCUMENT_ID}", f"version={VERSION}", f"path_count={len(PACKAGE_PATHS)}", "scope=V0933_ONLY", f"anchor={ANCHOR}", "authority_pointer=UNCHANGED", "physical_fit=NOT_YET_PERFORMED", "power=PROHIBITED", ""]
    for rel in PACKAGE_PATHS:
        if rel.endswith(".stl"): role = "NO_LOAD_PRINTABLE"
        elif rel.endswith(".step"): role = "CAD_REFERENCE_ASSEMBLY"
        elif rel.endswith((".svg", ".dxf")): role = "ONE_TO_ONE_OR_REFERENCE_TEMPLATE"
        elif rel.endswith(".csv"): role = "MEASUREMENT_OR_COORDINATE_TABLE"
        elif rel.endswith(".json"): role = "MACHINE_READABLE_CONTRACT"
        elif rel.endswith(".py"): role = "BUILDER_OR_TEST"
        else: role = "DOCUMENT_OR_LEDGER"
        lines.append(f"{rel}|{role}")
    return "\n".join(lines)


def commit_paths_text() -> str:
    prefix = "cad/common_rover/common_rover_candidate_a_motor_bracket_8hole_flat_plate_v0_9_3_3"
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
    for rel, digest in hashes.items():
        actual = sha256(base / rel) if (base / rel).is_file() else "MISSING"
        if actual != digest: mismatches.append({"path": rel, "expected": digest, "actual": actual})
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
            shape = load_stl(base / rel); value = bounds(shape)
            valid = len(shape.Faces()) >= 4 and all(math.isfinite(number) for number in value.values())
            fit = all(value[key] <= limit for key, limit in zip(("xlen", "ylen", "zlen"), A1_BUILD_VOLUME))
            passed = valid and fit and abs(value["zmin"]) <= 0.05 and abs(value["zmax"] - PETG_Z) <= 0.05
            rows.append({"path": rel, "faces": len(shape.Faces()), "bounds": value, "flat_base": abs(value["zmin"]) <= 0.05, "a1_fit": fit, "pass": passed})
        except Exception as exc: rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_steps(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for rel in ASSEMBLY_FILES:
        try:
            shape = cq.importers.importStep(str(base / rel)).val(); value = bounds(shape)
            passed = len(shape.Solids()) >= 1 and all(math.isfinite(number) for number in value.values())
            rows.append({"path": rel, "solids": len(shape.Solids()), "bounds": value, "pass": passed})
        except Exception as exc: rows.append({"path": rel, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(row["pass"] for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_templates(base: Path = LANE_DIR) -> dict[str, Any]:
    svg_rows = []
    for rel in [path for path in TEMPLATE_FILES if path.endswith(".svg")]:
        text = (base / rel).read_text(encoding="utf-8")
        passed = all(token in text for token in ("50 mm CHECK BAR", "SCALE 100%", "FIT OFF", "AUTOSCALE OFF"))
        svg_rows.append({"path": rel, "pass": passed})
    dxf = (base / TEMPLATE_FILES[6]).read_text(encoding="utf-8")
    dxf_checks = {"units_mm": "$INSUNITS" in dxf and "\n4\n" in dxf, "exact_eight_circles": len(re.findall(r"(?m)^CIRCLE$", dxf)) == 8, "labels": all(token in dxf for token in ("M3 DIA 3.4", "M5 DIA 5.7", "PITCH X 24", "PITCH Y 30", "PITCH X 20", "PITCH Y 60", "42x80 R3", "50 mm CHECK BAR", "PRINT 100%"))}
    return {"svg": svg_rows, "dxf": dxf_checks, "status": "PASS" if all(row["pass"] for row in svg_rows) and all(dxf_checks.values()) else "FAIL"}


def verify_evidence(base: Path = LANE_DIR) -> dict[str, Any]:
    params = json.loads((base / ROOT_FILES[1]).read_text(encoding="utf-8"))
    measurements = json.loads((base / ROOT_FILES[3]).read_text(encoding="utf-8"))
    checks = {
        "simple_design": params["design_principle"] == "SIMPLE_REPAIRABLE_FLAT_PLATE",
        "plate": params["plate"]["size_mm"] == [42.0, 80.0] and params["plate"]["petg_thickness_mm"] == 6.0 and params["plate"]["metal_reference_thickness_mm"] == 3.0,
        "holes": params["holes"]["total"] == 8 and params["holes"]["M3"]["count"] == 4 and params["holes"]["M5"]["count"] == 4,
        "m3_physical": params["physical_fit"]["M3_3P4"] == "PASS / JUST_FIT",
        "m4_reference_only": params["physical_fit"]["M4_4P2"] == "PASS / JUST_FIT_REFERENCE_ONLY" and params["physical_fit"]["M4_holes_in_plate"] == 0,
        "unsupported_features_zero": not any(params["features_not_used"].values()),
        "geometry": params["geometry_report"]["status"] == "PASS",
        "identical": params["left_part"] == params["right_part"] == "IDENTICAL",
        "spacer_hold": params["spacer"]["status"] == "PHYSICAL_MEASUREMENT_HOLD",
        "print_no_support": params["print"]["support"] == "NONE",
        "authority": params["approval"]["authority_pointer"] == "UNCHANGED",
        "no_power": params["approval"]["powered_rotation"] == "NOT_APPROVED",
        "measurement_rows": len(measurements["rows"]) == len(measurement_rows()),
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def refresh_artifacts() -> dict[str, Any]:
    for rel in ("build_motor_bracket_8hole_flat_plate_v0933.py", "tests/test_motor_bracket_8hole_flat_plate_v0933.py"):
        if not (LANE_DIR / rel).is_file(): raise RuntimeError(f"source missing: {rel}")
    repository_audit(require_complete=False)
    parents = parent_audit(True)
    geometry = geometry_report()
    if geometry["status"] != "PASS": raise RuntimeError(geometry)
    write_text(LANE_DIR / ROOT_FILES[0], design_markdown(geometry))
    write_json(LANE_DIR / ROOT_FILES[1], parameters(parents, geometry))
    write_csv(LANE_DIR / ROOT_FILES[2], measurement_rows())
    write_json(LANE_DIR / ROOT_FILES[3], {"document_id": DOCUMENT_ID, "rows": measurement_rows()})
    write_csv(LANE_DIR / ROOT_FILES[4], hole_rows())
    write_text(LANE_DIR / ROOT_FILES[5], petg_markdown())
    write_text(LANE_DIR / ROOT_FILES[6], metal_markdown())
    write_text(LANE_DIR / ROOT_FILES[7], stack_markdown())
    write_text(LANE_DIR / ROOT_FILES[8], spacer_markdown())
    write_text(LANE_DIR / ROOT_FILES[9], procedure_markdown())
    write_text(LANE_DIR / ROOT_FILES[10], result_sheet_markdown())
    write_text(LANE_DIR / ROOT_FILES[11], height_markdown())
    write_text(LANE_DIR / ROOT_FILES[12], supersession_markdown())
    write_text(LANE_DIR / ROOT_FILES[13], readme_markdown())
    write_text(LANE_DIR / ROOT_FILES[14], no_power_text())
    write_text(LANE_DIR / ROOT_FILES[17], commit_paths_text())
    export_artifacts()
    write_text(LANE_DIR / ROOT_FILES[20], "status=PREPACKAGE_SELF_CHECKS_PASS\ncontract_tests=RUN_DURING_PACKAGE\nphysical_fit=NOT_YET_PERFORMED")
    write_text(LANE_DIR / ROOT_FILES[18], manifest_text())
    write_text(LANE_DIR / ROOT_FILES[19], sha256sums_text())
    actual = lane_files()
    if actual != sorted(PACKAGE_PATHS): raise RuntimeError({"missing": sorted(set(PACKAGE_PATHS) - set(actual)), "extra": sorted(set(actual) - set(PACKAGE_PATHS))})
    reports = (verify_stls(), verify_steps(), verify_templates(), verify_evidence())
    if any(report["status"] != "PASS" for report in reports): raise RuntimeError({"reports": reports})
    return {"document_id": DOCUMENT_ID, "exact_package_paths": len(PACKAGE_PATHS), "parent": parents["status"], "geometry": geometry["status"], "STL_reload": f"{reports[0]['pass_count']}/{reports[0]['count']} PASS", "STEP_reload": f"{reports[1]['pass_count']}/{reports[1]['count']} PASS", "templates": reports[2]["status"], "status": "PASS"}


def verify() -> dict[str, Any]:
    actual = lane_files()
    if actual != sorted(PACKAGE_PATHS): raise RuntimeError({"missing": sorted(set(PACKAGE_PATHS) - set(actual)), "extra": sorted(set(actual) - set(PACKAGE_PATHS))})
    repository = repository_audit(require_complete=True)
    parents = parent_audit()
    hashes = verify_hashes(); manifest = verify_manifest(); stls = verify_stls(); steps = verify_steps(); templates = verify_templates(); evidence = verify_evidence()
    reports = {"parents": parents["status"], "hashes": hashes["status"], "manifest": manifest["status"], "stls": stls["status"], "steps": steps["status"], "templates": templates["status"], "evidence": evidence["status"]}
    if any(value != "PASS" for value in reports.values()): raise RuntimeError({"reports": reports, "hashes": hashes, "manifest": manifest, "templates": templates, "evidence": evidence})
    return {"document_id": DOCUMENT_ID, "repository": repository, "parent_protection": parents["status"], "exact_package_paths": len(PACKAGE_PATHS), "hashes": f"{hashes['verified']}/{len(PACKAGE_PATHS)-1} PASS", "manifest": f"{manifest['entry_count']}/{len(PACKAGE_PATHS)} PASS", "STL_reload": f"{stls['pass_count']}/{stls['count']} PASS", "STEP_reload": f"{steps['pass_count']}/{steps['count']} PASS", "templates": templates["status"], "status": "PASS"}


def zip_info(rel: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(rel, date_time=(2000, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
    return info


def write_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "x") as archive:
        for rel in PACKAGE_PATHS: archive.writestr(zip_info(rel), (LANE_DIR / rel).read_bytes())


def verify_zip(path: Path, standalone: bool = True) -> dict[str, Any]:
    if not path.is_file(): raise RuntimeError(f"ZIP missing: {path}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist(); duplicates = sorted({name for name in names if names.count(name) > 1}); traversal = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        if names != list(PACKAGE_PATHS) or duplicates or traversal: raise RuntimeError({"scope": names == list(PACKAGE_PATHS), "duplicates": duplicates, "traversal": traversal})
        hashes = {}
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            if line.strip(): digest, rel = line.split("  ", 1); hashes[rel] = digest
        internal = [rel for rel, digest in hashes.items() if hashlib.sha256(archive.read(rel)).hexdigest() != digest]
        lane_mismatches = [rel for rel in names if hashlib.sha256(archive.read(rel)).hexdigest() != sha256(LANE_DIR / rel)]
    standalone_status = "NOT_REQUESTED"
    if standalone:
        with tempfile.TemporaryDirectory(prefix="ps_cr_v0933_zip_") as temp:
            target = Path(temp)
            with zipfile.ZipFile(path) as archive: archive.extractall(target)
            env = dict(os.environ); env["V0933_TEST_ZIP"] = str(path)
            build = run([sys.executable, "-B", "build_motor_bracket_8hole_flat_plate_v0933.py", "--verify"], cwd=target, env=env)
            tests = run([sys.executable, "-B", "tests/test_motor_bracket_8hole_flat_plate_v0933.py"], cwd=target, env=env)
            if build.returncode or tests.returncode: raise RuntimeError({"standalone_build": build.stdout, "standalone_tests": tests.stdout})
            standalone_status = "PASS"
    if internal or lane_mismatches: raise RuntimeError({"internal_hash_mismatches": internal, "lane_mismatches": lane_mismatches})
    return {"zip_path": str(path), "entry_count": len(names), "duplicates": duplicates, "path_traversal": traversal, "internal_hash_verification": "PASS", "lane_byte_match": "PASS", "standalone_verify": standalone_status, "zip_sha256": sha256(path), "status": "PASS"}


def package_handoff() -> dict[str, Any]:
    verify(); DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_path = DOWNLOAD_DIR / f"{ZIP_PREFIX}{timestamp}.zip"
    temporary = DOWNLOAD_DIR / f".{ZIP_PREFIX}{timestamp}.validation.tmp"
    if final_path.exists() or temporary.exists(): raise RuntimeError("refusing to overwrite handoff")
    try:
        write_zip(temporary)
        env = dict(os.environ); env["V0933_TEST_ZIP"] = str(temporary)
        result = run([sys.executable, "-B", "tests/test_motor_bracket_8hole_flat_plate_v0933.py"], cwd=LANE_DIR, env=env)
        if result.returncode: raise RuntimeError(f"contract tests failed:\n{result.stdout}")
        summary = [line for line in result.stdout.splitlines() if line.startswith("Ran ") or line == "OK"]
        write_text(LANE_DIR / ROOT_FILES[20], "command=python -B tests/test_motor_bracket_8hole_flat_plate_v0933.py\nstatus=PASS\n" + "\n".join(summary) + "\nphysical_fit=NOT_YET_PERFORMED\nfull_output:\n" + result.stdout)
        write_text(LANE_DIR / ROOT_FILES[19], sha256sums_text()); verify()
    finally:
        if temporary.exists(): temporary.unlink()
    write_zip(final_path)
    return {"verification": "PASS", **verify_zip(final_path, standalone=True)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--refresh-artifacts", action="store_true"); parser.add_argument("--verify", action="store_true"); parser.add_argument("--package", action="store_true"); parser.add_argument("--verify-zip", type=Path)
    args = parser.parse_args(argv)
    if sum(bool(value) for value in (args.refresh_artifacts, args.verify, args.package, args.verify_zip)) != 1: parser.error("choose exactly one action")
    if args.refresh_artifacts: result = refresh_artifacts()
    elif args.verify: result = verify()
    elif args.package: result = package_handoff()
    else: result = verify_zip(args.verify_zip, standalone=True)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
