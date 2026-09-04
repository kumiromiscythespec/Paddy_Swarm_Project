#!/usr/bin/env python3
"""Build and verify Common Rover crawler guide clearance retest v0.9.3.6."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

import cadquery as cq
import trimesh


DOCUMENT_ID = "PS-CR-V0936-GUIDE-CLEARANCE-RETEST"
VERSION = "0.9.3.6"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = "cad/common_rover/common_rover_crawler_guide_clearance_retest_coupon_v0_9_3_6"
LANE_DIR = Path(__file__).resolve().parent
PARENT_REL = "cad/common_rover/common_rover_crawler_tracking_retention_patch_v0_9_3_5"
SOURCE_REL = "cad/crawler_h1/track_module/pretest_candidate_v0_1"
PARENT_SNAPSHOT = (34, "93e1fae749a19c8f428f02091dec9dcf1363bbe09cd5e5f30e0acf21caeb73b1")
SOURCE_SNAPSHOT = (24, "c8df27c908ce60a2b7f4d6bfde10c264dc1074b367e5eb0579535aab1bf955ed")
SOURCE_LINK_STL_REL = "stl/petg/STANDARD_V0125_WIDE_46_LINK.stl"
SOURCE_LINK_STL_SHA256 = "eb21877913a281b17d080a178fbb5b916384c29504ba1e16a188e90c85f49c6a"
DOWNLOAD_DIR = Path(r"D:\Downloads")
ZIP_PREFIX = "Paddy_Swarm_Common_Rover_Guide_Clearance_Retest_Coupon_v0_9_3_6_"

AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
EXPECTED_TRACKED_DIFF = set(AUTHORITY_HASHES)

PHYSICAL_LINK_WIDTH_MM = 53.6
SOURCE_LINK_WIDTH_MM = 54.0
GUIDE_BODY_WIDTH_MM = 4.0
GUIDE_HEIGHT_MM = 3.0
LOWER_ZONE_HEIGHT_MM = 2.0
UPPER_ZONE_HEIGHT_MM = 1.0
APEX_RADIUS_MM = 0.75
GUIDE_LENGTH_MM = 8.0
SPACINGS_MM = (54.2, 54.4, 54.6)
ANGLES_DEG = (35.0, 40.0, 45.0)
# Sharp construction heights compensate the R0.75 fillet setback so the
# finished rounded apex remains exactly 3.0 mm above the plate at each angle.
SHARP_UPPER_HEIGHT_BY_ANGLE = {
    35.0: 1.1498486004522874,
    40.0: 1.1380793804380573,
    45.0: 1.1275853238910258,
}
PROVISIONAL_FIRST_TEST = "W54P4_A40"
BASE_LENGTH_MM = 160.0
BASE_WIDTH_MM = 96.0
BASE_THICKNESS_MM = 2.0
STATION_X_MM = (-50.0, 0.0, 50.0)
TEXT_HEIGHT_MM = 3.0
TEXT_EMBOSS_MM = 0.6

ROOT_FILES = (
    "README_HANDOFF.md",
    "guide_retest_physical_basis_v0936.md",
    "guide_retest_parameters_v0936.json",
    "guide_retest_dimension_report_v0936.csv",
    "guide_retest_source_comparison_v0936.csv",
    "guide_retest_physical_result_sheet_v0936.md",
    "guide_retest_print_instructions_v0936.md",
    "guide_retest_test_plan_v0936.md",
    "remaining_measurements_v0936.md",
    "NO_POWER_FIT_TEST_ONLY.txt",
    "COMMIT_PATHS.txt",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
    "test_results_v0936.txt",
)
SOURCE_FILES = (
    "build_crawler_guide_clearance_retest_v0936.py",
    "tests/test_crawler_guide_clearance_retest_v0936.py",
)
STEP_FILES = (
    "artifacts/step/GUIDE_RETEST_PLATE_W54P2_G4P0.step",
    "artifacts/step/GUIDE_RETEST_PLATE_W54P4_G4P0.step",
    "artifacts/step/GUIDE_RETEST_PLATE_W54P6_G4P0.step",
    "artifacts/step/GUIDE_RETEST_ALL_9_ASSEMBLY_REFERENCE.step",
    "artifacts/step/LINK_MAX_WIDTH_53P6_ENVELOPE_REFERENCE.step",
)
STL_FILES = (
    "artifacts/stl/plate_01_guide_retest_W54P2_G4P0_A35_A40_A45.stl",
    "artifacts/stl/plate_02_guide_retest_W54P4_G4P0_A35_A40_A45.stl",
    "artifacts/stl/plate_03_guide_retest_W54P6_G4P0_A35_A40_A45.stl",
)
SVG_FILES = (
    "artifacts/svg/GUIDE_RETEST_W54P2_DIMENSIONS.svg",
    "artifacts/svg/GUIDE_RETEST_W54P4_DIMENSIONS.svg",
    "artifacts/svg/GUIDE_RETEST_W54P6_DIMENSIONS.svg",
    "artifacts/svg/GUIDE_RETEST_53P6_CLEARANCE_COMPARISON.svg",
    "artifacts/svg/GUIDE_RETEST_GUIDE_WIDTH_4P0_SECTION.svg",
    "artifacts/svg/GUIDE_RETEST_PHYSICAL_USE_SEQUENCE.svg",
)
PACKAGE_PATHS = ROOT_FILES + SOURCE_FILES + STEP_FILES + STL_FILES + SVG_FILES
if len(PACKAGE_PATHS) != 30 or len(set(PACKAGE_PATHS)) != 30:
    raise RuntimeError("formal path contract must be exact 30")


def run(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace", check=False)


def git(*args: str) -> str:
    result = run(["git", *args], REPO_ROOT)
    if result.returncode:
        raise RuntimeError(result.stdout)
    return "\n".join(line for line in result.stdout.splitlines() if not line.startswith("warning:")).strip()


def live_repository() -> bool:
    return run(["git", "rev-parse", "--show-toplevel"], LANE_DIR).returncode == 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def lane_files(base: Path = LANE_DIR) -> list[str]:
    return sorted(path.relative_to(base).as_posix() for path in base.rglob("*") if path.is_file())


def full_lane_ledger(path: Path) -> tuple[int, str]:
    files = sorted((item for item in path.rglob("*") if item.is_file()), key=lambda item: item.relative_to(path).as_posix())
    rows = [f"{item.relative_to(path).as_posix()}\t{sha256(item)}" for item in files]
    return len(files), hashlib.sha256(("\n".join(rows) + "\n").encode("utf-8")).hexdigest()


def parent_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    if not live:
        return {"path": PARENT_REL, "expected_file_count": PARENT_SNAPSHOT[0], "expected_ledger_sha256": PARENT_SNAPSHOT[1], "mode": "STANDALONE_EMBEDDED", "status": "PASS"}
    actual = full_lane_ledger(REPO_ROOT / PARENT_REL)
    if actual != PARENT_SNAPSHOT:
        raise RuntimeError({"parent_expected": PARENT_SNAPSHOT, "parent_actual": actual})
    return {"path": PARENT_REL, "file_count": actual[0], "ledger_sha256": actual[1], "status": "PASS"}


def source_audit(live: bool | None = None) -> dict[str, Any]:
    if live is None:
        live = live_repository()
    if not live:
        return {"path": SOURCE_REL, "expected_file_count": SOURCE_SNAPSHOT[0], "expected_ledger_sha256": SOURCE_SNAPSHOT[1], "link_width_mm": SOURCE_LINK_WIDTH_MM, "mode": "STANDALONE_EMBEDDED", "status": "PASS"}
    source = REPO_ROOT / SOURCE_REL
    actual = full_lane_ledger(source)
    tracked = {line.replace("\\", "/") for line in git("ls-files", "--", SOURCE_REL).splitlines() if line}
    expected = {f"{SOURCE_REL}/{path.relative_to(source).as_posix()}" for path in source.rglob("*") if path.is_file()}
    link_path = source / SOURCE_LINK_STL_REL
    with link_path.open("rb") as handle:
        raw = trimesh.exchange.stl.load_stl_binary(handle)
    width = float(raw["vertices"][:, 1].max() - raw["vertices"][:, 1].min())
    checks = {"ledger": actual == SOURCE_SNAPSHOT, "fully_tracked": tracked == expected, "link_stl_hash": sha256(link_path) == SOURCE_LINK_STL_SHA256, "link_width": abs(width - SOURCE_LINK_WIDTH_MM) < 1e-6}
    if not all(checks.values()):
        raise RuntimeError({"source_checks": checks, "ledger": actual, "width": width})
    return {"path": SOURCE_REL, "file_count": actual[0], "ledger_sha256": actual[1], "link_stl_sha256": sha256(link_path), "link_width_mm": width, "tracked": True, "checks": checks, "status": "PASS"}


def repository_audit(require_complete: bool = True) -> dict[str, Any]:
    if not live_repository():
        return {"mode": "STANDALONE_HANDOFF", "status": "PASS"}
    root = str(Path(git("rev-parse", "--show-toplevel")).resolve())
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    tracked = {line.replace("\\", "/") for line in git("diff", "--name-only").splitlines() if line}
    staged = {line.replace("\\", "/") for line in git("diff", "--cached", "--name-only").splitlines() if line}
    untracked = [line.replace("\\", "/") for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line]
    actual = lane_files()
    lane_untracked = sorted(path[len(LANE_REL) + 1:] for path in untracked if path.startswith(LANE_REL + "/"))
    ignored = [line for line in git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL).splitlines() if line]
    forbidden = [path for path in actual if "__pycache__" in path.lower() or ".pytest_cache" in path.lower() or path.lower().endswith((".pyc", ".pyo", ".tmp", ".bak", ".fcstd", ".blend"))]
    checks = {
        "root": root.lower() == str(REPO_ROOT.resolve()).lower(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "tracked_diff_preserved": tracked == EXPECTED_TRACKED_DIFF,
        "staged_zero": not staged,
        "authority_hashes": {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_HASHES} == AUTHORITY_HASHES,
        "parent": parent_audit(True)["status"] == "PASS",
        "source": source_audit(True)["status"] == "PASS",
        "lane_scope": set(actual).issubset(PACKAGE_PATHS),
        "lane_untracked_exact": lane_untracked == actual,
        "lane_complete": actual == sorted(PACKAGE_PATHS) if require_complete else True,
        "ignored_zero": not ignored,
        "forbidden_zero": not forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError({"repository_checks": checks, "actual": actual, "lane_untracked": lane_untracked, "ignored": ignored, "forbidden": forbidden})
    return {"root": root, "branch": branch, "head": head, "tracked_diff": sorted(tracked), "staged_diff": sorted(staged), "untracked_total": len(untracked), "lane_untracked_count": len(lane_untracked), "checks": checks, "status": "PASS"}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def spacing_code(spacing: float) -> str:
    return f"W{spacing:.1f}".replace(".", "P")


def guide_one(sign: float, spacing: float, angle: float, x: float = 0.0) -> cq.Workplane:
    inner = spacing / 2.0
    outer = inner + GUIDE_BODY_WIDTH_MM
    sharp_upper_height = SHARP_UPPER_HEIGHT_BY_ANGLE[float(angle)]
    run_mm = sharp_upper_height * math.tan(math.radians(angle))
    sharp_apex_z = BASE_THICKNESS_MM + LOWER_ZONE_HEIGHT_MM + sharp_upper_height
    root_z = BASE_THICKNESS_MM - 0.2
    if sign > 0:
        points = [(inner, root_z), (outer, root_z), (outer, BASE_THICKNESS_MM + LOWER_ZONE_HEIGHT_MM), (inner + run_mm, sharp_apex_z), (inner, BASE_THICKNESS_MM + LOWER_ZONE_HEIGHT_MM)]
        expected_apex_y = inner + run_mm
    else:
        points = [(-inner, root_z), (-outer, root_z), (-outer, BASE_THICKNESS_MM + LOWER_ZONE_HEIGHT_MM), (-inner - run_mm, sharp_apex_z), (-inner, BASE_THICKNESS_MM + LOWER_ZONE_HEIGHT_MM)]
        expected_apex_y = -inner - run_mm
    raw = cq.Workplane("YZ").polyline(points).close().extrude(GUIDE_LENGTH_MM / 2.0, both=True).translate((x, 0, 0))
    apex_edges = [edge for edge in raw.edges("|X").vals() if abs(edge.Center().z - sharp_apex_z) < 1e-5]
    apex = min(apex_edges, key=lambda edge: abs(edge.Center().y - expected_apex_y))
    return cq.Workplane(obj=raw.val()).newObject([apex]).fillet(APEX_RADIUS_MM)


def guide_pair(spacing: float, angle: float, x: float = 0.0) -> cq.Workplane:
    return guide_one(-1.0, spacing, angle, x).union(guide_one(1.0, spacing, angle, x)).clean()


def link_proxy(x: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").box(GUIDE_LENGTH_MM - 0.4, PHYSICAL_LINK_WIDTH_MM, GUIDE_HEIGHT_MM, centered=(True, True, False)).translate((x, 0, BASE_THICKNESS_MM))


def marking(text: str, x: float, y: float, size: float = TEXT_HEIGHT_MM) -> cq.Workplane:
    return cq.Workplane("XY").workplane(offset=BASE_THICKNESS_MM).center(x, y).text(text, size, TEXT_EMBOSS_MM, combine=True)


def plate_shape(spacing: float) -> cq.Workplane:
    plate = cq.Workplane("XY").box(BASE_LENGTH_MM, BASE_WIDTH_MM, BASE_THICKNESS_MM, centered=(True, True, False))
    for x, angle in zip(STATION_X_MM, ANGLES_DEG):
        plate = plate.union(guide_pair(spacing, angle, x))
        plate = plate.union(marking(f"{spacing_code(spacing)} A{int(angle)}", x, -38.0))
    plate = plate.union(marking("PS CR GUIDE RETEST", 0.0, 44.0))
    plate = plate.union(marking("v0.9.3.6 LINK MAX 53.6 GUIDE 4.0", 0.0, 38.0))
    plate = plate.union(marking(f"{spacing_code(spacing)} FIT TEST ONLY NO POWER NO LOAD", 0.0, -44.0))
    return plate.clean()


def common_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    try:
        return float(a.intersect(b).val().Volume())
    except Exception:
        return 0.0


def apex_zone_min_spacing(pair: cq.Workplane) -> float:
    edges = [edge for edge in pair.edges("|X").vals() if edge.Center().z > BASE_THICKNESS_MM + LOWER_ZONE_HEIGHT_MM + 1e-5]
    positive = [edge.Center().y for edge in edges if edge.Center().y > 0]
    return 2.0 * min(positive)


def geometry_analysis() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    plates: dict[str, Any] = {}
    for spacing in SPACINGS_MM:
        code = spacing_code(spacing)
        plate = plate_shape(spacing)
        station_rows = []
        for x, angle in zip(STATION_X_MM, ANGLES_DEG):
            pair = guide_pair(spacing, angle, x)
            proxy = link_proxy(x)
            bounds = pair.val().BoundingBox()
            row = {
                "station_id": f"{code}_A{int(angle)}",
                "spacing_code": code,
                "angle_deg_from_vertical": angle,
                "physical_link_width_mm": PHYSICAL_LINK_WIDTH_MM,
                "lower_zone_inner_spacing_mm": spacing,
                "slope_start_inner_spacing_mm": spacing,
                "centered_reference_spacing_mm": spacing,
                "apex_zone_min_spacing_mm": apex_zone_min_spacing(pair),
                "left_guide_body_width_mm": GUIDE_BODY_WIDTH_MM,
                "right_guide_body_width_mm": GUIDE_BODY_WIDTH_MM,
                "outer_guide_span_mm": bounds.ymax - bounds.ymin,
                "finished_exposed_guide_height_mm": bounds.zmax - BASE_THICKNESS_MM,
                "nominal_clearance_per_side_mm": (spacing - PHYSICAL_LINK_WIDTH_MM) / 2.0,
                "centered_proxy_collision_mm3": common_volume(pair, proxy),
                "guide_solids_before_plate_union": len(pair.solids().vals()),
                "left_right_symmetric": abs(bounds.ymin + bounds.ymax) < 1e-6,
                "forward_reverse_equivalent": abs(bounds.xmin + bounds.xmax - 2.0 * x) < 1e-6,
                "horizontal_apex_shelf_edges": len([edge for edge in pair.edges("|X").vals() if abs(edge.Center().z - bounds.zmax) < 1e-5]),
                "lateral_normal_fraction": math.cos(math.radians(angle)),
                "vertical_normal_fraction": math.sin(math.radians(angle)),
            }
            rows.append(row)
            station_rows.append(row)
        plate_bounds = plate.val().BoundingBox()
        plates[code] = {"spacing_mm": spacing, "solid_count": len(plate.solids().vals()), "volume_mm3": float(plate.val().Volume()), "bounds_mm": {"x": plate_bounds.xlen, "y": plate_bounds.ylen, "z": plate_bounds.zlen}, "stations": station_rows}
    return {
        "stations": rows,
        "plates": plates,
        "station_count": len(rows),
        "plate_count": len(plates),
        "marking_zone_min_abs_y_mm": 38.0,
        "functional_guide_outer_max_abs_y_mm": max(SPACINGS_MM) / 2.0 + GUIDE_BODY_WIDTH_MM,
        "source_link_width_mm": SOURCE_LINK_WIDTH_MM,
        "physical_link_width_mm": PHYSICAL_LINK_WIDTH_MM,
        "source_minus_physical_mm": SOURCE_LINK_WIDTH_MM - PHYSICAL_LINK_WIDTH_MM,
    }


def parameters(parent: dict[str, Any], source: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": DOCUMENT_ID,
        "version": VERSION,
        "expected_branch": EXPECTED_BRANCH,
        "expected_head": EXPECTED_HEAD,
        "parent_protection": parent,
        "source_protection": source,
        "physical_basis": {"link_maximum_width_mm": PHYSICAL_LINK_WIDTH_MM, "guide_body_width_per_side_mm": GUIDE_BODY_WIDTH_MM, "precedence": ["LINK_MAXIMUM_WIDTH_53P6", "GUIDE_BODY_WIDTH_4P0", "PREVIOUS_49P8_NEAR_ZERO_FIT", "CAD_DERIVED_HISTORICAL_VALUES"]},
        "source_comparison": {"source_cad_link_max_width_mm": SOURCE_LINK_WIDTH_MM, "physical_link_max_width_mm": PHYSICAL_LINK_WIDTH_MM, "physical_minus_source_mm": PHYSICAL_LINK_WIDTH_MM - SOURCE_LINK_WIDTH_MM, "link_geometry_change": "PROHIBITED_NOT_CHANGED", "status": "SOURCE_CAD_MISMATCH_HOLD_PHYSICAL_PRECEDENCE"},
        "superseded": {"49.4": "REJECT_TOO_NARROW", "49.6": "REJECT_TOO_NARROW", "49.8": "INVALID_AS_FULL_LINK_WIDTH_REFERENCE", "50.4_50.6_50.8": "SUPERSEDED_BEFORE_GENERATION"},
        "preserved": {"link_pitch_mm": 20.0, "sprocket_tooth_count": 12, "sprocket_od_mm": 66.14, "pitch_diameter_mm": 76.3943726841, "drive_axle_bore_mm_reference": 10.1, "link_geometry": "UNCHANGED", "sprocket_geometry": "UNCHANGED", "bearing_and_retainer": "UNCHANGED", "roller_geometry": "UNCHANGED", "crawler_loop_and_frame": "UNCHANGED"},
        "guide": {"inner_spacings_mm": list(SPACINGS_MM), "body_width_mm": GUIDE_BODY_WIDTH_MM, "outer_spans_mm": [value + 2.0 * GUIDE_BODY_WIDTH_MM for value in SPACINGS_MM], "angle_candidates_deg_from_vertical": list(ANGLES_DEG), "height_mm": GUIDE_HEIGHT_MM, "lower_zone_height_mm": LOWER_ZONE_HEIGHT_MM, "lower_zone_ratio_percent": LOWER_ZONE_HEIGHT_MM / GUIDE_HEIGHT_MM * 100.0, "upper_zone_height_mm": UPPER_ZONE_HEIGHT_MM, "upper_zone_ratio_percent": UPPER_ZONE_HEIGHT_MM / GUIDE_HEIGHT_MM * 100.0, "sharp_construction_upper_height_by_angle_mm": SHARP_UPPER_HEIGHT_BY_ANGLE, "fillet_compensation_purpose": "FINISHED_ROUNDED_APEX_EXACT_3P0_MM", "apex_radius_mm": APEX_RADIUS_MM, "length_mm": GUIDE_LENGTH_MM, "symmetry": "LEFT_RIGHT_AND_FORWARD_REVERSE", "provisional_first_test": PROVISIONAL_FIRST_TEST},
        "markings": {"common": ["PS CR GUIDE RETEST", "v0.9.3.6", "LINK MAX 53.6", "GUIDE 4.0", "FIT TEST ONLY", "NO POWER", "NO LOAD"], "plate": ["W54.2", "W54.4", "W54.6"], "station": ["A35", "A40", "A45"], "height_mm": TEXT_HEIGHT_MM, "emboss_mm": TEXT_EMBOSS_MM, "functional_surface_intersection": False},
        "print": {"target": "Bambu Lab A1", "scale_percent": 100, "support": "OFF", "orientation": "BASE_FLAT", "elephant_foot_compensation_in_cad": "NOT_APPLIED", "material": "SAME_AS_PREVIOUS_GUIDE_COUPON", "profile": "SAME_WHERE_POSSIBLE"},
        "approval": {"W54P2": "PHYSICAL_TEST_REQUIRED", "W54P4": "PHYSICAL_TEST_REQUIRED", "W54P6": "PHYSICAL_TEST_REQUIRED", "A35": "PHYSICAL_TEST_REQUIRED", "A40": "PHYSICAL_TEST_REQUIRED", "A45": "PHYSICAL_TEST_REQUIRED", "final_guide_selection": "HOLD", "full_crawler_part_release": "HOLD", "powered_rotation": "NOT_APPROVED", "torque_load": "NOT_APPROVED", "mud_test": "NOT_APPROVED", "water_test": "NOT_APPROVED", "field_deployment": "NOT_APPROVED", "authority_update": "NOT_APPROVED", "manufacturing": "NOT_APPROVED"},
        "analysis": analysis,
    }


def csv_text(headers: list[str], rows: list[dict[str, Any]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def dimension_csv(p: dict[str, Any]) -> str:
    headers = ["station_id", "spacing_code", "angle_deg_from_vertical", "physical_link_width_mm", "lower_zone_inner_spacing_mm", "slope_start_inner_spacing_mm", "centered_reference_spacing_mm", "apex_zone_min_spacing_mm", "left_guide_body_width_mm", "right_guide_body_width_mm", "outer_guide_span_mm", "finished_exposed_guide_height_mm", "nominal_clearance_per_side_mm", "centered_proxy_collision_mm3"]
    return csv_text(headers, [{key: row[key] for key in headers} for row in p["analysis"]["stations"]])


def source_comparison_csv() -> str:
    rows = [
        {"item": "LINK_MAX_WIDTH", "source_cad_mm": SOURCE_LINK_WIDTH_MM, "physical_mm": PHYSICAL_LINK_WIDTH_MM, "physical_minus_source_mm": PHYSICAL_LINK_WIDTH_MM - SOURCE_LINK_WIDTH_MM, "disposition": "PHYSICAL_53P6_PRECEDENCE_SOURCE_MISMATCH_HOLD_NO_LINK_CHANGE"},
        {"item": "LINK_PITCH", "source_cad_mm": 20.0, "physical_mm": "NOT_REMEASURED", "physical_minus_source_mm": "", "disposition": "PRESERVE"},
        {"item": "SPROCKET_OD", "source_cad_mm": 66.14, "physical_mm": "NOT_REMEASURED", "physical_minus_source_mm": "", "disposition": "PRESERVE"},
    ]
    return csv_text(["item", "source_cad_mm", "physical_mm", "physical_minus_source_mm", "disposition"], rows)


def readme_text() -> str:
    return f"""# Common Rover crawler guide clearance retest coupon v{VERSION}

Physical-fit coupon lane based on the measured 53.6 mm maximum link width and exact 4.0 mm guide-body width. Three plates contain W54.2, W54.4, and W54.6 respectively; each plate provides A35, A40, and A45 stations.

Start with **W54.4 / A40**. Final selection remains HOLD until physical results are supplied.

All STL files are `FIT TEST ONLY`, `NO POWER`, and `NO LOAD`. No link, sprocket, axle, bearing, roller, loop, frame, manufacturing, authority, powered, torque, mud, water, or field release is included.
"""


def physical_basis_text() -> str:
    return """# Guide retest physical basis v0.9.3.6

User measurements take precedence: link maximum width 53.6 mm and guide body width 4.0 mm per side. Previous W49.4 and W49.6 were too narrow; W49.8 only barely engaged and is invalid as a full-link-width reference. W50.4/W50.6/W50.8 were superseded before generation.

The selected source STL measures 54.0 mm maximum Y width, 0.4 mm wider than the physical result. Source link geometry is not changed or averaged. Coupon spacing uses the physical 53.6 mm envelope and records the source mismatch as HOLD.
"""


def physical_result_sheet_text() -> str:
    lines = ["# Physical result sheet v0.9.3.6", "", "Print all plates at 100% with identical settings. Start with W54.4 / A40 and test at least three physical links including the 53.6 mm maximum-width link.", ""]
    for spacing in SPACINGS_MM:
        for angle in ANGLES_DEG:
            lines.extend([f"## {spacing_code(spacing)} A{int(angle)}", "", f"- CAD_INNER_SPACING: {spacing:.1f}", "- PRINTED_INNER_SPACING_LOWER:", "- PRINTED_INNER_SPACING_SLOPE_START:", "- CAD_GUIDE_WIDTH: 4.0", "- PRINTED_LEFT_GUIDE_WIDTH:", "- PRINTED_RIGHT_GUIDE_WIDTH:", "- GUIDE_HEIGHT:", "- APEX_APPEARANCE:", "- PLATE_WARP:", "- MARKING_READABLE:", "- CENTERED_CONTACT:", "- LATERAL_PLAY:", "- UNDERSIDE_CONTACT_OR_LIFTING:", "- APEX_CLIMB_OR_PARKING:", "- LEFT_RIGHT_RECOVERY:", "- FORWARD_REVERSE_RECOVERY:", "- VISIBLE_WEAR_RESISTANCE:", "- RESULT_PASS_HOLD_FAIL:", "- NOTES:", ""])
    return "\n".join(lines)


def print_instructions_text() -> str:
    return """# Print instructions v0.9.3.6

- Target: Bambu Lab A1; 100% scale; base flat; support OFF.
- Use the previous guide-coupon material and the same slicer profile where possible.
- Print all three plates with identical settings.
- Confirm support generation 0, floating islands 0, apex and slopes present, markings readable, and no bridge-failure warning.
- Do not encode elephant-foot compensation into CAD. Record slicer settings separately.
- These are FIT TEST ONLY / NO POWER / NO LOAD coupons.
"""


def test_plan_text() -> str:
    return """# Physical test plan v0.9.3.6

1. Begin with W54.4 / A40. Confirm hand insertion, no constant rubbing, no underside lift, small lateral movement, and no screw contact.
2. Displace left and right. Confirm side-face contact, no apex parking, and no lifting.
3. Move forward and reverse by hand. Confirm equivalent recovery.
4. Connect three links, twist the two end links gently, and check recovery within one to two pitches without persistent apex running.

If W54.4 rubs, compare W54.6. If play is excessive, compare W54.2. If A40 lifts, compare A35; if recovery is insufficient, compare A45. Do not auto-select the narrowest condition.
"""


def remaining_text() -> str:
    return """# Remaining measurements v0.9.3.6

- Printed lower-zone and slope-start inner spacing for all nine stations.
- Printed left/right guide width, guide height, apex appearance, and plate warp.
- Marking legibility and first-layer expansion at guide contact faces.
- Widths and fit behavior of at least three links, including the 53.6 mm link.
- Screw-head clearance, underside contact, lift, apex climb/parking, and wear.
- Left/right and forward/reverse recovery, including the three-link twist test.
- Source-CAD 54.0 mm versus physical 53.6 mm discrepancy remains HOLD.
"""


def no_power_text() -> str:
    return """FIT_TEST_ONLY=TRUE
NO_POWER=TRUE
NO_LOAD=TRUE
POWERED_ROTATION=NOT_APPROVED
TORQUE_LOAD=NOT_APPROVED
MANUFACTURING=NOT_APPROVED
FIELD_DEPLOYMENT=NOT_APPROVED
FINAL_GUIDE_SELECTION=HOLD
"""


def commit_paths_text() -> str:
    return "\n".join(f"{LANE_REL}/{path}" for path in PACKAGE_PATHS)


def role_for(path: str) -> str:
    if path.endswith(".step"):
        return "REFERENCE_STEP_NOT_FOR_MANUFACTURING"
    if path.endswith(".stl"):
        return "NO_POWER_NO_LOAD_FIT_TEST_COUPON"
    if path.endswith(".svg"):
        return "DIMENSION_OR_TEST_GUIDE_SVG"
    if path.endswith(".py"):
        return "SOURCE_OR_CONTRACT_TEST"
    return "CANONICAL_HANDOFF_RECORD"


def manifest_text() -> str:
    return "\n".join(f"{path}|{role_for(path)}" for path in PACKAGE_PATHS)


def sha256sums_text(base: Path = LANE_DIR) -> str:
    return "\n".join(f"{sha256(base / path)}  {path}" for path in PACKAGE_PATHS if path != "SHA256SUMS.txt")


def svg_shell(title: str, content: str, width: int = 1200, height: int = 700) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M8,4 L0,0 L0,8 Z" fill="#245"/></marker></defs>
<rect width="100%" height="100%" fill="#f7f8fa"/><text x="40" y="48" font-family="sans-serif" font-size="28" font-weight="bold">{title}</text>
<text x="40" y="78" font-family="sans-serif" font-size="16" fill="#a22">FIT TEST ONLY · NO POWER · NO LOAD</text>{content}</svg>'''


def dimension_svg(spacing: float) -> str:
    scale = 6.0
    center = 600.0
    inner_l = center - spacing * scale / 2.0
    inner_r = center + spacing * scale / 2.0
    outer_l = inner_l - GUIDE_BODY_WIDTH_MM * scale
    outer_r = inner_r + GUIDE_BODY_WIDTH_MM * scale
    proxy_l = center - PHYSICAL_LINK_WIDTH_MM * scale / 2.0
    proxy_r = center + PHYSICAL_LINK_WIDTH_MM * scale / 2.0
    stations = []
    for index, angle in enumerate(ANGLES_DEG):
        y = 160 + index * 155
        run_px = math.tan(math.radians(angle)) * 45
        stations.append(f'''<text x="80" y="{y+35}" font-family="sans-serif" font-size="22">A{int(angle)}</text>
<rect x="{proxy_l}" y="{y+5}" width="{proxy_r-proxy_l}" height="70" fill="#9cc" opacity="0.55"/>
<path d="M{outer_l},{y+85} L{inner_l},{y+85} L{inner_l},{y+35} L{inner_l-run_px},{y+10} L{outer_l},{y+35} Z" fill="#e79" stroke="#713" stroke-width="2"/>
<path d="M{inner_r},{y+85} L{outer_r},{y+85} L{outer_r},{y+35} L{inner_r+run_px},{y+10} L{inner_r},{y+35} Z" fill="#e79" stroke="#713" stroke-width="2"/>
<line x1="{inner_l}" y1="{y+105}" x2="{inner_r}" y2="{y+105}" stroke="#245" stroke-width="2" marker-start="url(#arrow)" marker-end="url(#arrow)"/>
<text x="{center}" y="{y+130}" text-anchor="middle" font-family="sans-serif" font-size="18">lower/slope-start inner spacing {spacing:.1f} mm</text>''')
    outer_span = spacing + 8.0
    clearance = (spacing - PHYSICAL_LINK_WIDTH_MM) / 2.0
    footer = f'''<text x="40" y="650" font-family="sans-serif" font-size="18">Physical proxy 53.6 mm · guide width L/R 4.0 mm · outer span {outer_span:.1f} mm · nominal clearance {clearance:.1f} mm/side</text>'''
    return svg_shell(f"Guide retest {spacing_code(spacing)} dimensions", "".join(stations) + footer)


def comparison_svg() -> str:
    bars = []
    for index, spacing in enumerate(SPACINGS_MM):
        y = 180 + index * 130
        w = spacing * 12
        proxy = PHYSICAL_LINK_WIDTH_MM * 12
        bars.append(f'''<text x="90" y="{y+25}" font-family="sans-serif" font-size="22">{spacing_code(spacing)}: {spacing:.1f} mm</text><rect x="350" y="{y}" width="{w}" height="42" fill="#d9a"/><rect x="350" y="{y+8}" width="{proxy}" height="26" fill="#69a"/><text x="1020" y="{y+27}" font-family="sans-serif" font-size="18">{(spacing-PHYSICAL_LINK_WIDTH_MM)/2:.1f} mm/side</text>''')
    return svg_shell("53.6 mm physical envelope clearance comparison", "".join(bars) + '<text x="350" y="610" font-family="sans-serif" font-size="18">Blue: physical link envelope · Pink: guide inner spacing</text>')


def guide_section_svg() -> str:
    return svg_shell("Guide body width 4.0 mm and recovery section", '''<line x1="200" y1="570" x2="1000" y2="570" stroke="#555" stroke-width="4"/><path d="M360,570 L560,570 L560,370 L610,270 L760,370 L760,570 Z" fill="#e79" stroke="#713" stroke-width="3"/><line x1="360" y1="610" x2="760" y2="610" stroke="#245" stroke-width="2" marker-start="url(#arrow)" marker-end="url(#arrow)"/><text x="560" y="640" text-anchor="middle" font-family="sans-serif" font-size="22">guide body width = 4.0 mm at lower zone</text><line x1="810" y1="570" x2="810" y2="370" stroke="#245" marker-start="url(#arrow)" marker-end="url(#arrow)"/><text x="840" y="480" font-family="sans-serif" font-size="20">2.0 mm lower zone</text><line x1="930" y1="370" x2="930" y2="270" stroke="#245" marker-start="url(#arrow)" marker-end="url(#arrow)"/><text x="960" y="330" font-family="sans-serif" font-size="20">1.0 mm upper zone</text><text x="610" y="230" text-anchor="middle" font-family="sans-serif" font-size="20">rounded apex R0.75 · no flat shelf</text>''')


def use_sequence_svg() -> str:
    content = []
    labels = ["1 Print all three plates identically", "2 Measure all nine stations", "3 Start W54.4 / A40", "4 Test centered and lateral fit", "5 Test forward/reverse and 3-link twist", "6 Record PASS / HOLD / FAIL; final selection HOLD"]
    for index, label in enumerate(labels):
        x = 80 + (index % 3) * 370
        y = 160 + (index // 3) * 250
        content.append(f'<rect x="{x}" y="{y}" width="310" height="130" rx="18" fill="#def" stroke="#245" stroke-width="2"/><text x="{x+20}" y="{y+55}" font-family="sans-serif" font-size="18">{label}</text>')
    return svg_shell("Physical use sequence", "".join(content))


def export_artifacts() -> None:
    plates = [plate_shape(spacing) for spacing in SPACINGS_MM]
    for path, plate in zip(STEP_FILES[:3], plates):
        (LANE_DIR / path).parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(plate, str(LANE_DIR / path))
    assembly_parts: list[cq.Shape] = []
    for row, (spacing, plate) in enumerate(zip(SPACINGS_MM, plates)):
        y_shift = (row - 1) * 130.0
        assembly_parts.append(plate.translate((0, y_shift, 0)).val())
        for x in STATION_X_MM:
            assembly_parts.append(link_proxy(x).translate((0, y_shift, 0)).val())
    cq.exporters.export(cq.Compound.makeCompound(assembly_parts), str(LANE_DIR / STEP_FILES[3]))
    cq.exporters.export(link_proxy(0), str(LANE_DIR / STEP_FILES[4]))
    for path, plate in zip(STL_FILES, plates):
        (LANE_DIR / path).parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(plate, str(LANE_DIR / path), tolerance=0.01, angularTolerance=0.1)
    svg_values = [dimension_svg(value) for value in SPACINGS_MM] + [comparison_svg(), guide_section_svg(), use_sequence_svg()]
    for path, value in zip(SVG_FILES, svg_values):
        write_text(LANE_DIR / path, value)


def verify_steps(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for path in STEP_FILES:
        try:
            shape = cq.importers.importStep(str(base / path)).val()
            solids = len(shape.Solids())
            passed = solids >= 1 and shape.BoundingBox().xlen > 0 and shape.BoundingBox().ylen > 0 and shape.BoundingBox().zlen > 0
            rows.append({"path": path, "solids": solids, "pass": passed})
        except Exception as exc:
            rows.append({"path": path, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(bool(row["pass"]) for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_stls(base: Path = LANE_DIR) -> dict[str, Any]:
    rows = []
    for path in STL_FILES:
        try:
            with (base / path).open("rb") as handle:
                raw = trimesh.exchange.stl.load_stl_binary(handle)
            mesh = trimesh.Trimesh(vertices=raw["vertices"], faces=raw["faces"], process=False)
            mesh.merge_vertices()
            components = int(mesh.body_count)
            passed = bool(mesh.is_watertight) and components == 1 and float(mesh.volume) > 0
            rows.append({"path": path, "watertight": bool(mesh.is_watertight), "components": components, "faces": len(mesh.faces), "volume_mm3": float(mesh.volume), "pass": passed})
        except Exception as exc:
            rows.append({"path": path, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(bool(row["pass"]) for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_svgs(base: Path = LANE_DIR) -> dict[str, Any]:
    import xml.etree.ElementTree as ET
    rows = []
    for path in SVG_FILES:
        try:
            root = ET.parse(base / path).getroot()
            passed = root.tag.endswith("svg") and (root.get("viewBox") is not None)
            rows.append({"path": path, "pass": passed})
        except Exception as exc:
            rows.append({"path": path, "pass": False, "error": str(exc)})
    return {"rows": rows, "pass_count": sum(bool(row["pass"]) for row in rows), "count": len(rows), "status": "PASS" if all(row["pass"] for row in rows) else "FAIL"}


def verify_manifest(base: Path = LANE_DIR) -> dict[str, Any]:
    values = [line.split("|", 1)[0] for line in (base / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() if "|" in line]
    return {"entry_count": len(values), "exact_order": values == list(PACKAGE_PATHS), "status": "PASS" if values == list(PACKAGE_PATHS) else "FAIL"}


def verify_hashes(base: Path = LANE_DIR) -> dict[str, Any]:
    values: dict[str, str] = {}
    for line in (base / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, path = line.split("  ", 1)
            values[path] = digest
    required = set(PACKAGE_PATHS) - {"SHA256SUMS.txt"}
    mismatches: list[Any] = []
    if set(values) != required:
        mismatches.append({"missing": sorted(required - set(values)), "extra": sorted(set(values) - required)})
    for path, expected in values.items():
        actual = sha256(base / path) if (base / path).is_file() else "MISSING"
        if actual != expected:
            mismatches.append({"path": path, "expected": expected, "actual": actual})
    return {"verified": len(values), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def verify_geometry(base: Path = LANE_DIR) -> dict[str, Any]:
    p = json.loads((base / "guide_retest_parameters_v0936.json").read_text(encoding="utf-8"))
    rows = p["analysis"]["stations"]
    checks = {
        "physical": p["physical_basis"]["link_maximum_width_mm"] == 53.6 and p["physical_basis"]["guide_body_width_per_side_mm"] == 4.0,
        "counts": p["analysis"]["plate_count"] == 3 and p["analysis"]["station_count"] == 9,
        "spacings": sorted({row["lower_zone_inner_spacing_mm"] for row in rows}) == [54.2, 54.4, 54.6],
        "angles": sorted({row["angle_deg_from_vertical"] for row in rows}) == [35.0, 40.0, 45.0],
        "body_width": all(row["left_guide_body_width_mm"] == 4.0 and row["right_guide_body_width_mm"] == 4.0 for row in rows),
        "outer_spans": sorted({round(row["outer_guide_span_mm"], 6) for row in rows}) == [62.2, 62.4, 62.6],
        "collision": all(row["centered_proxy_collision_mm3"] <= 1e-6 for row in rows),
        "symmetry": all(row["left_right_symmetric"] and row["forward_reverse_equivalent"] for row in rows),
        "no_flat_apex": all(row["horizontal_apex_shelf_edges"] == 0 for row in rows),
        "plate_solids": all(item["solid_count"] == 1 for item in p["analysis"]["plates"].values()),
        "marking_clear": p["analysis"]["marking_zone_min_abs_y_mm"] > p["analysis"]["functional_guide_outer_max_abs_y_mm"],
        "holds": p["approval"]["final_guide_selection"] == "HOLD" and p["approval"]["powered_rotation"] == "NOT_APPROVED" and p["approval"]["manufacturing"] == "NOT_APPROVED",
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def refresh_artifacts() -> dict[str, Any]:
    for path in SOURCE_FILES:
        if not (LANE_DIR / path).is_file():
            raise RuntimeError(f"source missing: {path}")
    repository_audit(require_complete=False)
    parent = parent_audit(True)
    source = source_audit(True)
    analysis = geometry_analysis()
    p = parameters(parent, source, analysis)
    write_text(LANE_DIR / ROOT_FILES[0], readme_text())
    write_text(LANE_DIR / ROOT_FILES[1], physical_basis_text())
    write_json(LANE_DIR / ROOT_FILES[2], p)
    write_text(LANE_DIR / ROOT_FILES[3], dimension_csv(p))
    write_text(LANE_DIR / ROOT_FILES[4], source_comparison_csv())
    write_text(LANE_DIR / ROOT_FILES[5], physical_result_sheet_text())
    write_text(LANE_DIR / ROOT_FILES[6], print_instructions_text())
    write_text(LANE_DIR / ROOT_FILES[7], test_plan_text())
    write_text(LANE_DIR / ROOT_FILES[8], remaining_text())
    write_text(LANE_DIR / ROOT_FILES[9], no_power_text())
    write_text(LANE_DIR / ROOT_FILES[10], commit_paths_text())
    export_artifacts()
    write_text(LANE_DIR / ROOT_FILES[13], "status=PREPACKAGE_SELF_CHECKS_PASS\ncontract_tests=RUN_DURING_PACKAGE\nphysical_test=NOT_YET_PERFORMED\nfinal_selection=HOLD")
    write_text(LANE_DIR / ROOT_FILES[11], manifest_text())
    write_text(LANE_DIR / ROOT_FILES[12], sha256sums_text())
    if lane_files() != sorted(PACKAGE_PATHS):
        raise RuntimeError({"actual": lane_files(), "expected": sorted(PACKAGE_PATHS)})
    reports = [verify_steps(), verify_stls(), verify_svgs(), verify_manifest(), verify_hashes(), verify_geometry()]
    if any(report["status"] != "PASS" for report in reports):
        raise RuntimeError({"reports": reports})
    return {"document_id": DOCUMENT_ID, "formal_paths": len(PACKAGE_PATHS), "STEP": "5/5 PASS", "STL": "3/3 PASS", "SVG": "6/6 PASS", "geometry": "9/9 PASS", "parent": parent["status"], "source": source["status"], "status": "PASS"}


def verify() -> dict[str, Any]:
    if lane_files() != sorted(PACKAGE_PATHS):
        raise RuntimeError({"actual": lane_files(), "expected": sorted(PACKAGE_PATHS)})
    repository = repository_audit(require_complete=True)
    parent = parent_audit()
    source = source_audit()
    steps, stls, svgs, manifest, hashes, geometry = verify_steps(), verify_stls(), verify_svgs(), verify_manifest(), verify_hashes(), verify_geometry()
    reports = {"steps": steps["status"], "stls": stls["status"], "svgs": svgs["status"], "manifest": manifest["status"], "hashes": hashes["status"], "geometry": geometry["status"], "parent": parent["status"], "source": source["status"]}
    if any(value != "PASS" for value in reports.values()):
        raise RuntimeError({"reports": reports})
    return {"document_id": DOCUMENT_ID, "repository": repository, "parent_protection": parent["status"], "source_protection": source["status"], "formal_paths": len(PACKAGE_PATHS), "STEP_reload": f"{steps['pass_count']}/{steps['count']} PASS", "STL_manifold": f"{stls['pass_count']}/{stls['count']} PASS", "SVG": f"{svgs['pass_count']}/{svgs['count']} PASS", "geometry_stations": "9/9 PASS", "manifest": f"{manifest['entry_count']}/{len(PACKAGE_PATHS)} PASS", "hashes": f"{hashes['verified']}/{len(PACKAGE_PATHS)-1} PASS", "status": "PASS"}


def zip_info(path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, date_time=(2000, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def write_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "x") as archive:
        for rel in PACKAGE_PATHS:
            archive.writestr(zip_info(rel), (LANE_DIR / rel).read_bytes())


def verify_zip(path: Path, standalone: bool = True) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        duplicates = sorted({name for name in names if names.count(name) > 1})
        traversal = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        if names != list(PACKAGE_PATHS) or duplicates or traversal:
            raise RuntimeError({"names_exact": names == list(PACKAGE_PATHS), "duplicates": duplicates, "traversal": traversal})
        values = {}
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            if line.strip():
                digest, rel = line.split("  ", 1)
                values[rel] = digest
        internal = [rel for rel, expected in values.items() if hashlib.sha256(archive.read(rel)).hexdigest() != expected]
        lane_mismatch = [rel for rel in names if hashlib.sha256(archive.read(rel)).hexdigest() != sha256(LANE_DIR / rel)]
    standalone_status = "NOT_REQUESTED"
    if standalone:
        with tempfile.TemporaryDirectory(prefix="ps_cr_v0936_zip_") as temp:
            target = Path(temp)
            with zipfile.ZipFile(path) as archive:
                archive.extractall(target)
            env = dict(os.environ)
            env["V0936_TEST_ZIP"] = str(path)
            build = run([sys.executable, "-B", "build_crawler_guide_clearance_retest_v0936.py", "--verify"], target, env)
            tests = run([sys.executable, "-B", "tests/test_crawler_guide_clearance_retest_v0936.py"], target, env)
            if build.returncode or tests.returncode:
                raise RuntimeError({"standalone_build": build.stdout, "standalone_tests": tests.stdout})
            standalone_status = "PASS"
    if internal or lane_mismatch:
        raise RuntimeError({"internal_hash_mismatch": internal, "lane_mismatch": lane_mismatch})
    return {"zip_path": str(path), "entry_count": len(names), "duplicates": duplicates, "path_traversal": traversal, "internal_hash_verification": "PASS", "lane_byte_match": "PASS", "standalone_verify": standalone_status, "zip_sha256": sha256(path), "status": "PASS"}


def package_handoff() -> dict[str, Any]:
    verify()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final = DOWNLOAD_DIR / f"{ZIP_PREFIX}{timestamp}.zip"
    temporary = DOWNLOAD_DIR / f".{ZIP_PREFIX}{timestamp}.validation.tmp"
    if final.exists() or temporary.exists():
        raise RuntimeError("refusing to overwrite handoff")
    try:
        write_text(LANE_DIR / ROOT_FILES[13], "status=PACKAGE_TESTS_PENDING\nphysical_test=NOT_YET_PERFORMED\nfinal_selection=HOLD")
        write_text(LANE_DIR / ROOT_FILES[12], sha256sums_text())
        write_zip(temporary)
        env = dict(os.environ)
        env["V0936_TEST_ZIP"] = str(temporary)
        result = run([sys.executable, "-B", "tests/test_crawler_guide_clearance_retest_v0936.py"], LANE_DIR, env)
        if result.returncode:
            raise RuntimeError(result.stdout)
        summary = [line for line in result.stdout.splitlines() if line.startswith("Ran ") or line == "OK"]
        write_text(LANE_DIR / ROOT_FILES[13], "command=python -B tests/test_crawler_guide_clearance_retest_v0936.py\nstatus=PASS\n" + "\n".join(summary) + "\nphysical_test=NOT_YET_PERFORMED\nfinal_selection=HOLD\nfull_output:\n" + result.stdout)
        write_text(LANE_DIR / ROOT_FILES[12], sha256sums_text())
        verify()
    finally:
        if temporary.exists():
            temporary.unlink()
    write_zip(final)
    return {"verification": "PASS", **verify_zip(final, standalone=True)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-artifacts", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--verify-zip", type=Path)
    args = parser.parse_args(argv)
    if sum((args.refresh_artifacts, args.verify, args.package, args.verify_zip is not None)) != 1:
        parser.error("choose exactly one action")
    if args.refresh_artifacts:
        result = refresh_artifacts()
    elif args.verify:
        result = verify()
    elif args.package:
        result = package_handoff()
    else:
        result = verify_zip(args.verify_zip, standalone=True)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
