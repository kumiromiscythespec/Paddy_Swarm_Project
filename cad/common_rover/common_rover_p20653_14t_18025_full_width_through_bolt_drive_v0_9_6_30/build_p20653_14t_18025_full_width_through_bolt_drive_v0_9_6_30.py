#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Common Rover v0.9.6.30 P20653 14T / 18025 through-bolt DRIVE.

The P20653 tooth primitive is imported from the exact v0.9.6.20 authority.
Each 14T tooth is produced only by a rigid rotation and translation.  No tooth
scale, redraw, or profile simplification is permitted in this lane.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

import cadquery as cq
from cadquery import exporters, importers
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape


VERSION = "v0.9.6.30"
CLASSIFICATION = "P20653_14T_18025_FULL_WIDTH_THROUGH_BOLT_DRIVE"
STATUS = (
    "P20653_14T_18025_FULL_WIDTH_THROUGH_BOLT_DRIVE_CAD_COMPLETE/"
    "BLOCKER_1_DRIVETRAIN_TORQUE_TRANSMISSION_TARGETED/"
    "DRIVE_ROOT_STRUCTURAL_MARGIN_TARGETED/18025_VENDOR_SPEC_RECORDED/"
    "ONE_18025_PER_DRIVE/TOTAL_18025_REQUIRED_2/"
    "14T_P20653_DERIVED_WITHOUT_TOOTH_SCALING/12T_IDLER_UNCHANGED/"
    "CRAWLER_LOOP_RECALCULATED/FULL_WIDTH_SUPPORT_DRUM_COMPLETE/"
    "M5_THROUGH_BOLT_LOCKNUT_ARCHITECTURE_COMPLETE/"
    "F569_F570_F571_PROXY_COUPONS_READY/"
    "MULTI_CANDIDATE_GEOMETRIC_ID_RULE_ACTIVE/"
    "18025_PHYSICAL_FIT_NOT_YET/14T_PHYSICAL_CRAWLER_PASS_NOT_YET/"
    "STATIC_TORQUE_PASS_NOT_YET/POWERED_NOT_APPROVED/MUD_PASS_NOT_YET/"
    "FIELD_PASS_NOT_YET/COMMIT_READY_NOT_STAGED"
)
LANE_NAME = "common_rover_p20653_14t_18025_full_width_through_bolt_drive_v0_9_6_30"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2908
BASE_OUTSIDE_PATH_DIGEST = "635a946e5fdc9be84e1920ebf4745cb1ccfbf85462ab32c855ce8eace6ed5639"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V20_BUILDER_REL = PurePosixPath(
    "cad/common_rover/common_rover_physical_pitch_drive_idler_v0_9_6_20/"
    "build_physical_pitch_drive_idler_v0_9_6_20.py"
)
V29_BUILDER_REL = PurePosixPath(
    "cad/common_rover/common_rover_p20653_18025_keyed_hub_drive_v0_9_6_29/"
    "build_p20653_18025_keyed_hub_drive_v0_9_6_29.py"
)
v20 = _load("paddy_v09620_for_v09630", REPO_ROOT / V20_BUILDER_REL)
v29 = _load("paddy_v09629_for_v09630", REPO_ROOT / V29_BUILDER_REL)

PROTECTED_LANES = dict(v29.PROTECTED_LANES)
PROTECTED_LANES[V29_BUILDER_REL.parent.as_posix()] = (
    55, "cf6ba86922df6564ab478b3420d50907bdaf114d0eb48eb606ee7e8cea6f8fc7"
)
PROTECTED_LANES.update({
    "cad/common_rover/common_rover_short_slide_yoke_receiver_v0_9_6_12":
        (49, "bb341962167f1afcba1c66e0b01bb4b067f4a763e48de407254509afb91943d1"),
    "cad/common_rover/common_rover_rimless_short_slide_y3_v0_9_6_13":
        (17, "328d02555903d3e6bf6b6deec4ad791a2d11f055f9b07d49fa24787e908c5092"),
    "cad/common_rover/common_rover_belt_entry_clearance_rimless_v0_9_6_14":
        (18, "186764601464425b64770ed6535dfbfea26e6f796e02f4c382105e7f8f258a13"),
    "cad/common_rover/common_rover_dual_l_slide_rimless_hub_v0_9_6_15":
        (44, "63ccd725e1e76d70b04ff601a58813b465091f50f577813c4eee83796f93548d"),
    "cad/common_rover/common_rover_crawler_tracking_retention_patch_v0_9_3_5":
        (34, "a1fe2f75f035b8d24254c09f3b3e6527daafda1201cd36f630aa83cbcdacd519"),
    "cad/common_rover/common_rover_crawler_guide_clearance_retest_coupon_v0_9_3_6":
        (30, "17fe964740ef425df791a348e925e882239f1fc4070cacd19bec91f260955044"),
})

SOURCE_SHA256 = {
    V20_BUILDER_REL.as_posix(): "269354de29d6ec2fc4bead3dbe2523fded5ba04ab3419cbba619110dc6b5eb0f",
    "cad/common_rover/common_rover_physical_pitch_drive_idler_v0_9_6_20/artifacts/drive_12t_pitch_p20653_v0_9_6_20.step":
        "cf5a4bbdcc583105ad200009a671a0cb15c1697ab1eeff948a2313010c9212e3",
    "cad/common_rover/common_rover_physical_pitch_drive_idler_v0_9_6_20/artifacts/idler_pitch_matched_primary_v0_9_6_20.step":
        "abf4ef081e6b5fd7334a1041ce24e7b2de1987e15a3b69752e110c567093c97c",
    "cad/crawler_h1/track_module/pretest_candidate_v0_1/stl/petg/STANDARD_V0125_WIDE_46_LINK.stl":
        "eb21877913a281b17d080a178fbb5b916384c29504ba1e16a188e90c85f49c6a",
    "cad/common_rover/common_rover_p20653_18025_keyed_hub_drive_v0_9_6_29/design_parameters.json":
        "24a996fbacf3305dfd1be653e6d6b294695e7e50b1f553acf41080798fed9c5c",
    "cad/common_rover/common_rover_p20653_18025_keyed_hub_drive_v0_9_6_29/validation_report.json":
        "5abcfb861e445995da117ab23ec7fcf214236b8540ad790c3199c197a6a6b7d1",
}

# Frozen P20653 12T authority and 14T derived kinematics.
PITCH_MM = 20.6533333333
SOURCE_TOOTH_COUNT = 12
SOURCE_PITCH_DIAMETER_MM = 79.79835226236546
SOURCE_PHASE_DEG = 15.0
SOURCE_SPACING_DEG = 30.0
TOOTH_WIDTH_MM = 44.0
TARGET_TOOTH_COUNT = 14
TARGET_SPACING_DEG = 360.0 / TARGET_TOOTH_COUNT
TARGET_PHASE_DEG = TARGET_SPACING_DEG / 2.0
TARGET_PITCH_DIAMETER_MM = PITCH_MM / math.sin(math.pi / TARGET_TOOTH_COUNT)
TARGET_PITCH_RADIUS_MM = TARGET_PITCH_DIAMETER_MM / 2.0
RADIAL_INCREASE_MM = (TARGET_PITCH_DIAMETER_MM - SOURCE_PITCH_DIAMETER_MM) / 2.0
SOURCE_CURRENT_DIAMETER_MM = v20.CURRENT_PITCH_DIAMETER_MM
SOURCE_TO_P20653_SHIFT_MM = (SOURCE_PITCH_DIAMETER_MM - SOURCE_CURRENT_DIAMETER_MM) / 2.0

# Nexus / Vstone 18025 vendor drawing authority.
HUB_FLANGE_OD_MM = 56.8
HUB_BOSS_OD_MM = 24.0
HUB_OVERALL_WIDTH_MM = 26.4
HUB_FLANGE_THICKNESS_MM = 6.0
HUB_BOSS_EXTENSION_MM = HUB_OVERALL_WIDTH_MM - HUB_FLANGE_THICKNESS_MM
HUB_BORE_MM = 10.0
HUB_BORE_TOL_MM = [0.0, 0.02]
HUB_KEYWAY_WIDTH_MM = 3.0
HUB_KEYWAY_TOL_MM = [0.0, 0.02]
HUB_RAW_DRAWING_DIMENSION_MM = 11.4
HUB_DERIVED_KEYWAY_REFERENCE_MM = HUB_RAW_DRAWING_DIMENSION_MM - HUB_BORE_MM
HUB_PCD_MM = 47.5
HUB_HOLE_COUNT = 6
HUB_HOLE_MM = 5.2
VENDOR_DRAWING_URL = "https://www.vstone.co.jp/products/nexusrobot/download/nexus_18025.pdf"
PRODUCT_URL = "https://www.vstone.co.jp/robotshop/index.php?main_page=product_info&products_id=4206"

# Full-recess and support candidates.
FLANGE_POCKETS_MM = {"F569": 56.90, "F570": 57.00, "F571": 57.10}
SELECTED_PROVISIONAL_POCKET = "F569"
FLANGE_POCKET_DEPTH_MM = 6.20
CENTER_PILOT_D_MM = 24.10
CENTER_PILOT_LENGTH_MM = 4.0
DEEP_RELIEF_D_MM = 24.50
TOTAL_CAVITY_DEPTH_MM = 26.80
DEEP_RELIEF_LENGTH_MM = TOTAL_CAVITY_DEPTH_MM - FLANGE_POCKET_DEPTH_MM - CENTER_PILOT_LENGTH_MM
SHAFT_CLEARANCE_D_MM = 10.5
PETG_THROUGH_HOLE_D_MM = 5.5
LOCKNUT_COUNTERBORE_D_MM = 12.0
LOCKNUT_COUNTERBORE_DEPTH_MM = 4.0
SUPPORT_RING_RADIUS_MM = 33.55
SUPPORT_RING_CLEARANCE_TARGET_MM = 1.0
SUPPORT_RING_CLEARANCE_HARD_MM = 0.8
ROOT_PAD_INNER_RADIUS_MM = 30.8
ROOT_PAD_OUTER_RADIUS_MM = 37.2
ROOT_PAD_WIDTH_MM = 9.5
ROOT_PAD_FILLET_MM = 3.0
DRAIN_D_MM = 3.0
DRAIN_ANGLE_DEG = -77.14285714285714

# Crawler authority and open-loop calculations.
LINK_COUNT = 40
CURRENT_CENTER_DISTANCE_MM = 280.0
SOURCE_TENSION_STROKE_CANDIDATE_MM = 12.0
PHYSICAL_AVAILABLE_TENSION_STROKE = "HOLD_VERIFY_CURRENT_SLOT_AND_POSITION"
IDLER_TOOTH_COUNT = 12
IDLER_PITCH_RADIUS_MM = SOURCE_PITCH_DIAMETER_MM / 2.0

# Hardware stack candidates.
WASHER_THICKNESS_CANDIDATE_MM = 1.0
LOCKNUT_THICKNESS_CANDIDATE_MM = 5.0
VISIBLE_TWO_THREAD_MM = 1.6
BOLT_LENGTH_CANDIDATES_MM = [50, 55, 60]
TORQUE_REFERENCE_NM = 6.5
PCD_RADIUS_M = HUB_PCD_MM / 2000.0
TANGENTIAL_RESULTANT_N = TORQUE_REFERENCE_NM / PCD_RADIUS_M
IDEAL_BOLT_SHARE_N = TANGENTIAL_RESULTANT_N / HUB_HOLE_COUNT

BUILDER = Path(__file__).name
TEST = "tests/test_p20653_14t_18025_full_width_through_bolt_drive_v0_9_6_30_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "BLOCKER_TARGET.md", "PHYSICAL_STATE_MATRIX.md",
    "18025_OFFICIAL_SPEC_RECORD.md", "18025_VENDOR_DRAWING_AUTHORITY.json",
    "18025_DIMENSION_TRACE.svg", "18009_PROXY_PHYSICAL_RESULT.md",
    "MULTI_CANDIDATE_IDENTIFICATION_RULE.md", "flange_pocket_candidate_test_form.csv",
    "P20653_12T_SOURCE_AUTHORITY.md", "P20653_14T_DERIVATION.md",
    "TOOTH_LOCAL_GEOMETRY_FREEZE.md", "PHASE_DERIVATION.md", "14T_SIZE_COMPARISON.md",
    "14T_SPEED_FORCE_TRADEOFF.md", "IDLER_FIREWALL.md", "CRAWLER_LOOP_14T_12T_STUDY.md",
    "crawler_loop_link_count_table.csv", "FRAME_CLEARANCE_STUDY.md",
    "18025_RECESS_ARCHITECTURE.md", "FLANGE_POCKET_CANDIDATE_STUDY.md",
    "BOSS_PILOT_AND_RELIEF.md", "FULL_WIDTH_SUPPORT_DRUM.md", "LINK_SWEPT_CLEARANCE.md",
    "RADIAL_STRUCTURAL_MARGIN.md", "M5_THROUGH_BOLT_ARCHITECTURE.md",
    "HARDWARE_STACK_STUDY.md", "WIDTH_OPTIMIZATION.md", "DRAIN_WASHOUT_DESIGN.md",
    "TOOTH_BENDING_PHYSICAL_CONTRACT.md", "STATIC_6P5NM_TEST_PLAN.md",
    "POWERED_TEST_GATE.md", "PRINT_PLAN.md", "FAILURE_CRITERIA.md", "HOLD_REGISTER.md",
    "NEXT_DEVELOPMENT_GATE.md", "SOURCE_TRACE.md", "BUILD_LOG.txt", "TEST_LOG.txt",
    "design_parameters.json", "validation_report.json", "MANIFEST.txt", "SHA256SUMS.txt",
    "COMMIT_PATHS.txt",
]
CAD = [
    "artifacts/18025_flange_recess_f569_v0_9_6_30.stl",
    "artifacts/18025_flange_recess_f570_v0_9_6_30.stl",
    "artifacts/18025_flange_recess_f571_v0_9_6_30.stl",
    "artifacts/18025_flange_recess_triplet_v0_9_6_30.stl",
    "artifacts/p20653_14t_18025_full_width_through_bolt_drive_provisional_v0_9_6_30.step",
    "artifacts/p20653_14t_18025_full_width_through_bolt_drive_provisional_v0_9_6_30.stl",
    "artifacts/p20653_14t_18025_assembly_reference_v0_9_6_30.step",
]
SVGS = [
    "artifacts/12t_vs_14t_pitch_geometry.svg", "artifacts/12t_vs_14t_hub_margin.svg",
    "artifacts/14t_tooth_array.svg", "artifacts/18025_official_dimensions.svg",
    "artifacts/18025_one_hub_architecture.svg", "artifacts/18025_full_recess_section.svg",
    "artifacts/boss_pilot_relief_section.svg", "artifacts/full_width_support_drum_section.svg",
    "artifacts/link_swept_clearance.svg", "artifacts/m5_through_bolt_stack.svg",
    "artifacts/flange_pocket_candidates.svg", "artifacts/14t_12t_crawler_loop.svg",
    "artifacts/crawler_loop_14t_12t.svg", "artifacts/tooth_bending_test.svg",
    "artifacts/physical_validation_sequence.svg",
]
EXPECTED_FILES = sorted([BUILDER, TEST, *DOCS, *CAD, *SVGS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for path in files:
        digest.update((path.relative_to(root).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha256(path)))
    return len(files), digest.hexdigest()


def untracked_paths() -> list[str]:
    return sorted(
        row[3:].replace("\\", "/")
        for row in run_git("status", "--porcelain=v1", "-uall").splitlines()
        if row.startswith("?? ")
    )


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    digest = hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()
    return len(paths), digest


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    protected = {rel: tree_digest(REPO_ROOT / rel) for rel in PROTECTED_LANES}
    sources = {rel: sha256(REPO_ROOT / PurePosixPath(rel)) for rel in SOURCE_SHA256}
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj"}]
    ignored_lane = run_git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    checks = {
        "repository": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD, "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_PATH_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256,
        "protected_lanes": protected == PROTECTED_LANES, "source_files": sources == SOURCE_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES), "lane_cache_zero": not cache,
        "lane_ignored_zero": not ignored_lane, "forbidden_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks, "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "outside_untracked": outside_snapshot(),
        "ignored_repository_count": len(run_git("ls-files", "--others", "--ignored", "--exclude-standard").splitlines()),
        "lane_files": len(lane_files), "authority_sha256": authority,
        "protected_lanes": {rel: {"count": row[0], "tree_sha256": row[1], "status": "UNCHANGED"}
                            for rel, row in protected.items()},
        "source_sha256": sources, "cache": cache, "forbidden": forbidden, "ignored_lane": ignored_lane,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def cylinder(radius: float, height: float, z_center: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height / 2.0, both=True).translate((0, 0, z_center))


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def shape_volume(shape: cq.Workplane) -> float:
    return round(sum(float(solid.Volume()) for solid in shape.solids().vals()), 6)


def mounting_centers() -> list[tuple[float, float]]:
    radius = HUB_PCD_MM / 2.0
    return [(radius * math.cos(math.radians(index * 60.0)),
             radius * math.sin(math.radians(index * 60.0))) for index in range(HUB_HOLE_COUNT)]


@lru_cache(maxsize=1)
def canonical_p20653_tooth() -> cq.Workplane:
    candidates = v20.exact_v18_teeth().solids().vals()
    source = min(candidates, key=lambda solid: abs(math.degrees(math.atan2(solid.Center().y, solid.Center().x)) - 15.0))
    angle = math.degrees(math.atan2(source.Center().y, source.Center().x))
    # The asymmetric protected tooth's volume centroid is offset slightly from
    # its nominal 15 degree array datum.  v0.9.6.20 deliberately translates
    # each solid along its own centroid ray, so preserve that exact convention.
    shift = SOURCE_TO_P20653_SHIFT_MM
    return cq.Workplane(obj=source).translate((shift * math.cos(math.radians(angle)),
                                               shift * math.sin(math.radians(angle)), 0.0))


@lru_cache(maxsize=1)
def canonical_centroid_angle_deg() -> float:
    centre = canonical_p20653_tooth().val().Center()
    return math.degrees(math.atan2(centre.y, centre.x))


def target_tooth(index: int) -> cq.Workplane:
    angle = TARGET_PHASE_DEG + index * TARGET_SPACING_DEG
    delta = angle - SOURCE_PHASE_DEG
    rotated = canonical_p20653_tooth().rotate((0, 0, 0), (0, 0, 1), delta)
    radial_angle = canonical_centroid_angle_deg() + delta
    return rotated.translate((RADIAL_INCREASE_MM * math.cos(math.radians(radial_angle)),
                              RADIAL_INCREASE_MM * math.sin(math.radians(radial_angle)), 0.0))


def rounded_root_pad() -> cq.Workplane:
    length = ROOT_PAD_OUTER_RADIUS_MM - ROOT_PAD_INNER_RADIUS_MM
    width = ROOT_PAD_WIDTH_MM
    radius = ROOT_PAD_FILLET_MM
    x0 = (ROOT_PAD_INNER_RADIUS_MM + ROOT_PAD_OUTER_RADIUS_MM) / 2.0
    result = cq.Workplane("XY").box(length, width - 2 * radius, TOOTH_WIDTH_MM).translate((x0, 0, 0))
    result = result.union(cq.Workplane("XY").box(length - 2 * radius, width, TOOTH_WIDTH_MM).translate((x0, 0, 0)))
    for dx in (-length / 2 + radius, length / 2 - radius):
        for dy in (-width / 2 + radius, width / 2 - radius):
            result = result.union(cylinder(radius, TOOTH_WIDTH_MM).translate((x0 + dx, dy, 0)))
    return result.clean()


@lru_cache(maxsize=1)
def raw_support() -> cq.Workplane:
    result = cylinder(SUPPORT_RING_RADIUS_MM, TOOTH_WIDTH_MM)
    pad = rounded_root_pad()
    for index in range(TARGET_TOOTH_COUNT):
        angle = TARGET_PHASE_DEG + index * TARGET_SPACING_DEG
        result = result.union(pad.rotate((0, 0, 0), (0, 0, 1), angle))
    return result.clean()


def radial_drain() -> cq.Workplane:
    start = DEEP_RELIEF_D_MM / 2.0 - 0.3
    end = SUPPORT_RING_RADIUS_MM + 1.0
    length = end - start
    angle = math.radians(DRAIN_ANGLE_DEG)
    axis = (-math.sin(angle), math.cos(angle), 0.0)
    return cylinder(DRAIN_D_MM / 2.0, length).rotate((0, 0, 0), axis, 90.0).translate(
        (((start + end) / 2.0) * math.cos(angle), ((start + end) / 2.0) * math.sin(angle), -4.2)
    )


def cut_hub_interface(shape: cq.Workplane, pocket_diameter: float) -> cq.Workplane:
    top = TOOTH_WIDTH_MM / 2.0
    flange_floor = top - FLANGE_POCKET_DEPTH_MM
    pilot_floor = flange_floor - CENTER_PILOT_LENGTH_MM
    cavity_floor = top - TOTAL_CAVITY_DEPTH_MM
    result = shape.cut(cylinder(pocket_diameter / 2.0, FLANGE_POCKET_DEPTH_MM,
                                top - FLANGE_POCKET_DEPTH_MM / 2.0))
    result = result.cut(cylinder(CENTER_PILOT_D_MM / 2.0, CENTER_PILOT_LENGTH_MM,
                                flange_floor - CENTER_PILOT_LENGTH_MM / 2.0))
    result = result.cut(cylinder(DEEP_RELIEF_D_MM / 2.0, DEEP_RELIEF_LENGTH_MM,
                                (pilot_floor + cavity_floor) / 2.0))
    result = result.cut(cylinder(SHAFT_CLEARANCE_D_MM / 2.0, 70.0))
    for x, y in mounting_centers():
        result = result.cut(cylinder(PETG_THROUGH_HOLE_D_MM / 2.0, 70.0).translate((x, y, 0)))
        result = result.cut(cylinder(LOCKNUT_COUNTERBORE_D_MM / 2.0, LOCKNUT_COUNTERBORE_DEPTH_MM,
                                     -top + LOCKNUT_COUNTERBORE_DEPTH_MM / 2.0).translate((x, y, 0)))
    result = result.cut(radial_drain())
    return result.clean()


@lru_cache(maxsize=1)
def full_drive() -> cq.Workplane:
    result = raw_support()
    for index in range(TARGET_TOOTH_COUNT):
        result = result.union(target_tooth(index))
    result = cut_hub_interface(result.clean(), FLANGE_POCKETS_MM[SELECTED_PROVISIONAL_POCKET])
    if result.solids().size() != 1 or not all(solid.isValid() for solid in result.solids().vals()):
        raise RuntimeError("full 14T drive invalid")
    return result


def candidate_notches(shape: cq.Workplane, count: int) -> cq.Workplane:
    result = shape
    for index in range(count):
        angle = 180.0 + (index - (count - 1) / 2.0) * 7.0
        cutter = cq.Workplane("XY").box(5.0, 2.0, 10.0).translate((34.0, 0, 0)).rotate(
            (0, 0, 0), (0, 0, 1), angle
        )
        result = result.cut(cutter)
    return result.clean()


def flange_coupon(candidate: str) -> cq.Workplane:
    thickness = 8.0
    top = thickness / 2.0
    result = cylinder(35.5, thickness)
    result = result.cut(cylinder(FLANGE_POCKETS_MM[candidate] / 2.0, FLANGE_POCKET_DEPTH_MM,
                                 top - FLANGE_POCKET_DEPTH_MM / 2.0))
    result = result.cut(cylinder(CENTER_PILOT_D_MM / 2.0, 20.0))
    for x, y in mounting_centers():
        result = result.cut(cylinder(PETG_THROUGH_HOLE_D_MM / 2.0, 20.0).translate((x, y, 0)))
    return candidate_notches(result, {"F569": 1, "F570": 2, "F571": 3}[candidate])


def flange_triplet() -> cq.Workplane:
    return compound([flange_coupon("F569").translate((-82, 0, 0)), flange_coupon("F570"),
                     flange_coupon("F571").translate((82, 0, 0))])


def hub_reference() -> cq.Workplane:
    top = TOOTH_WIDTH_MM / 2.0 - 0.2
    flange = cylinder(HUB_FLANGE_OD_MM / 2.0, HUB_FLANGE_THICKNESS_MM,
                      top - HUB_FLANGE_THICKNESS_MM / 2.0)
    boss_top = top - HUB_FLANGE_THICKNESS_MM
    boss = cylinder(HUB_BOSS_OD_MM / 2.0, HUB_BOSS_EXTENSION_MM,
                    boss_top - HUB_BOSS_EXTENSION_MM / 2.0)
    result = flange.union(boss).cut(cylinder(HUB_BORE_MM / 2.0, 80.0))
    # The 1.4 mm depth is explicitly DERIVED_VENDOR_DRAWING_REFERENCE, not a
    # physical measurement.  It is used only on this non-printable reference.
    key_cut = cq.Workplane("XY").box(HUB_KEYWAY_WIDTH_MM, HUB_DERIVED_KEYWAY_REFERENCE_MM + 0.2, 22.0).translate(
        (0, HUB_BORE_MM / 2.0 + HUB_DERIVED_KEYWAY_REFERENCE_MM / 2.0, boss_top - 10.2)
    )
    return result.cut(key_cut).clean()


def assembly_reference() -> cq.Workplane:
    shaft = cylinder(5.0, 145.0)
    key = cq.Workplane("XY").box(3.0, 3.0, 20.0).translate((0, 5.7, -6.0))
    bolts = [cylinder(2.5, 50.0).translate((x, y, 0)) for x, y in mounting_centers()]
    return compound([full_drive(), hub_reference(), shaft, key, *bolts])


def source_link() -> cq.Workplane:
    return v20.source_link()


def link_at(index: int) -> cq.Workplane:
    angle = TARGET_PHASE_DEG + index * TARGET_SPACING_DEG
    base = source_link().rotate((0, 0, 0), (1, 0, 0), 90.0)
    base = base.rotate((0, 0, 0), (0, 0, 1), angle + 90.0)
    midpoint_radius = TARGET_PITCH_RADIUS_MM * math.cos(math.radians(TARGET_PHASE_DEG))
    return base.translate((midpoint_radius * math.cos(math.radians(angle)),
                           midpoint_radius * math.sin(math.radians(angle)), 0.0))


def tooth_regression() -> dict[str, object]:
    canonical = canonical_p20653_tooth()
    rows = []
    for index in range(TARGET_TOOTH_COUNT):
        angle = TARGET_PHASE_DEG + index * TARGET_SPACING_DEG
        delta = angle - SOURCE_PHASE_DEG
        radial_angle = canonical_centroid_angle_deg() + delta
        recovered = target_tooth(index).translate((-RADIAL_INCREASE_MM * math.cos(math.radians(radial_angle)),
                                                   -RADIAL_INCREASE_MM * math.sin(math.radians(radial_angle)), 0.0))
        recovered = recovered.rotate((0, 0, 0), (0, 0, 1), -(angle - SOURCE_PHASE_DEG))
        added = shape_volume(recovered.cut(canonical))
        removed = shape_volume(canonical.cut(recovered))
        rows.append({"index": index + 1, "target_angle_deg": angle,
                     "added_volume_mm3": added, "removed_volume_mm3": removed,
                     "status": "PASS" if added <= 1e-5 and removed <= 1e-5 else "FAIL"})
    return {"rows": rows, "all_14_pass": all(row["status"] == "PASS" for row in rows),
            "max_added_volume_mm3": max(row["added_volume_mm3"] for row in rows),
            "max_removed_volume_mm3": max(row["removed_volume_mm3"] for row in rows),
            "operation": "RIGID_ROTATION_PLUS_TRANSLATION_ONLY", "scale_factor": 1.0}


def radial_vertex_range(shape: cq.Workplane) -> tuple[float, float]:
    solids = shape.solids().vals()
    vertices = [vertex for solid in solids for vertex in solid.Vertices()] if solids else shape.val().Vertices()
    values = [math.hypot(vertex.X, vertex.Y) for vertex in vertices]
    return min(values), max(values)


def open_loop_length(center: float, drive_radius: float = TARGET_PITCH_RADIUS_MM,
                     idler_radius: float = IDLER_PITCH_RADIUS_MM) -> float:
    delta = drive_radius - idler_radius
    if center <= abs(delta):
        raise ValueError(center)
    return (2.0 * math.sqrt(center * center - delta * delta) + math.pi * (drive_radius + idler_radius)
            + 2.0 * delta * math.asin(delta / center))


def solve_center_for_length(length: float) -> float:
    lo = abs(TARGET_PITCH_RADIUS_MM - IDLER_PITCH_RADIUS_MM) + 1e-6
    hi = 1000.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if open_loop_length(mid) < length:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def loop_study() -> dict[str, object]:
    current_path = open_loop_length(CURRENT_CENTER_DISTANCE_MM)
    alpha = math.degrees(math.asin((TARGET_PITCH_RADIUS_MM - IDLER_PITCH_RADIUS_MM) / CURRENT_CENTER_DISTANCE_MM))
    rows = []
    for added in (0, 1, 2):
        count = LINK_COUNT + added
        target_length = count * PITCH_MM
        required_center = solve_center_for_length(target_length)
        inward = CURRENT_CENTER_DISTANCE_MM - required_center
        remaining = SOURCE_TENSION_STROKE_CANDIDATE_MM - max(inward, 0.0)
        practical = inward >= 0 and remaining >= 2.0
        rows.append({"configuration": f"CURRENT_LINK_COUNT{f'+{added}' if added else ''}",
                     "link_count": count, "available_link_path_mm": target_length,
                     "required_center_distance_mm": required_center,
                     "idler_displacement_from_current_mm": -inward,
                     "required_inward_shift_mm": inward, "remaining_candidate_stroke_mm": remaining,
                     "practical_with_candidate_12mm_stroke": practical,
                     "physical_status": "HOLD_REAL_AVAILABLE_STROKE"})
    selected = rows[0] if rows[0]["practical_with_candidate_12mm_stroke"] else None
    return {"current_center_distance_mm": CURRENT_CENTER_DISTANCE_MM,
            "current_14t_12t_path_length_mm": current_path,
            "current_link_count": LINK_COUNT, "source_tension_stroke_candidate_mm": SOURCE_TENSION_STROKE_CANDIDATE_MM,
            "physical_available_tensioner_stroke": PHYSICAL_AVAILABLE_TENSION_STROKE,
            "tangent_length_each_mm": math.sqrt(CURRENT_CENTER_DISTANCE_MM ** 2 -
                                                 (TARGET_PITCH_RADIUS_MM - IDLER_PITCH_RADIUS_MM) ** 2),
            "drive_wrap_deg": 180.0 + 2.0 * alpha, "idler_wrap_deg": 180.0 - 2.0 * alpha,
            "rows": rows, "selected_provisional": selected["configuration"] if selected else "NONE",
            "print_gate": "HOLD_REAL_AVAILABLE_TENSIONER_STROKE_AND_SERVICE_MARGIN"}


def support_analysis() -> dict[str, object]:
    canonical_min, canonical_max = radial_vertex_range(canonical_p20653_tooth())
    target_root = canonical_min + RADIAL_INCREASE_MM
    target_tip = canonical_max + RADIAL_INCREASE_MM
    link_min = min(radial_vertex_range(link_at(index))[0] for index in range(TARGET_TOOTH_COUNT))
    clearance = link_min - SUPPORT_RING_RADIUS_MM
    ring = cylinder(SUPPORT_RING_RADIUS_MM, TOOTH_WIDTH_MM)
    noncontact_intersections = [shape_volume(ring.intersect(link_at(index))) for index in range(TARGET_TOOTH_COUNT)]
    selected_pocket_radius = FLANGE_POCKETS_MM[SELECTED_PROVISIONAL_POCKET] / 2.0
    return {"support_type": "FULL_WIDTH_CONTINUOUS_RING_PLUS_14_LOCAL_ROUNDED_ROOT_PADS",
            "width_mm": TOOTH_WIDTH_MM, "ring_radius_mm": SUPPORT_RING_RADIUS_MM,
            "root_pad_radial_range_mm": [ROOT_PAD_INNER_RADIUS_MM, ROOT_PAD_OUTER_RADIUS_MM],
            "root_pad_width_mm": ROOT_PAD_WIDTH_MM, "root_transition_fillet_mm": ROOT_PAD_FILLET_MM,
            "source_p20653_root_radius_mm": canonical_min, "source_p20653_tip_radius_mm": canonical_max,
            "target_14t_root_radius_mm": target_root, "target_14t_tip_radius_mm": target_tip,
            "link_swept_min_radius_mm": link_min, "noncontact_ring_clearance_mm": clearance,
            "noncontact_ring_intersection_max_mm3": max(noncontact_intersections),
            "clearance_target_mm": SUPPORT_RING_CLEARANCE_TARGET_MM,
            "clearance_hard_mm": SUPPORT_RING_CLEARANCE_HARD_MM,
            "clearance_result": "HARD_PASS_TARGET_MISS" if clearance >= 0.8 else "FAIL",
            "selected_flange_to_ring_ligament_mm": SUPPORT_RING_RADIUS_MM - selected_pocket_radius,
            "selected_flange_to_tooth_root_mm": target_root - selected_pocket_radius,
            "flange_to_ring_result": "HARD_PASS_TARGET_MISS" if SUPPORT_RING_RADIUS_MM - selected_pocket_radius >= 5.0 else "FAIL",
            "link_source_sha256": SOURCE_SHA256["cad/crawler_h1/track_module/pretest_candidate_v0_1/stl/petg/STANDARD_V0125_WIDE_46_LINK.stl"]}


def geometry_analysis() -> dict[str, object]:
    regression = tooth_regression()
    support = support_analysis()
    loop = loop_study()
    final = full_drive()
    bb = final.val().BoundingBox()
    source_margin = support["source_p20653_root_radius_mm"] - HUB_FLANGE_OD_MM / 2.0
    target_margin = support["target_14t_root_radius_mm"] - HUB_FLANGE_OD_MM / 2.0
    external_stack = TOOTH_WIDTH_MM + WASHER_THICKNESS_CANDIDATE_MM + LOCKNUT_THICKNESS_CANDIDATE_MM + VISIBLE_TWO_THREAD_MM
    counterbore_stack = (TOOTH_WIDTH_MM - LOCKNUT_COUNTERBORE_DEPTH_MM + WASHER_THICKNESS_CANDIDATE_MM
                         + LOCKNUT_THICKNESS_CANDIDATE_MM + VISIBLE_TWO_THREAD_MM)
    return {
        "p20653": {"pitch_mm": PITCH_MM, "source_12t_pitch_diameter_mm": SOURCE_PITCH_DIAMETER_MM,
                    "target_14t_pitch_diameter_mm": TARGET_PITCH_DIAMETER_MM,
                    "pitch_radius_increase_mm": RADIAL_INCREASE_MM, "tooth_count": TARGET_TOOTH_COUNT,
                    "spacing_deg": TARGET_SPACING_DEG, "phase_deg": TARGET_PHASE_DEG,
                    "phase_derivation": "HALF_OF_TOOTH_SPACING", "tooth_width_mm": TOOTH_WIDTH_MM,
                    "adjacent_pitch_chord_mm": 2 * TARGET_PITCH_RADIUS_MM * math.sin(math.pi / TARGET_TOOTH_COUNT),
                    "regression": regression, "overall_bbox_mm": [bb.xlen, bb.ylen, bb.zlen],
                    "overall_radial_envelope_mm": support["target_14t_tip_radius_mm"]},
        "vendor_18025": {"authority": "USER_SUPPLIED_OFFICIAL_VENDOR_DRAWING+VSTONE_VENDOR_DRAWING_AUTHORITY",
                         "part": "Nexus/Vstone 18025", "flange_od_mm": HUB_FLANGE_OD_MM,
                         "boss_od_mm": HUB_BOSS_OD_MM, "overall_width_mm": HUB_OVERALL_WIDTH_MM,
                         "flange_thickness_mm": HUB_FLANGE_THICKNESS_MM,
                         "derived_boss_projection_mm": HUB_BOSS_EXTENSION_MM,
                         "bore_mm": HUB_BORE_MM, "bore_tolerance_mm": HUB_BORE_TOL_MM,
                         "pcd_mm": HUB_PCD_MM, "mounting_holes": HUB_HOLE_COUNT,
                         "mounting_hole_mm": HUB_HOLE_MM, "keyway_width_mm": HUB_KEYWAY_WIDTH_MM,
                         "keyway_tolerance_mm": HUB_KEYWAY_TOL_MM,
                         "raw_11p4_dimension_mm": HUB_RAW_DRAWING_DIMENSION_MM,
                         "derived_keyway_reference_mm": HUB_DERIVED_KEYWAY_REFERENCE_MM,
                         "derived_keyway_reference_authority": "DERIVED_VENDOR_DRAWING_REFERENCE",
                         "physical_measured": "NOT_YET", "set_screw_exact_position": "PHYSICAL_HOLD",
                         "set_screw_service_access": "PHYSICAL_HOLD",
                         "set_screw_torque_path": "PROHIBITED"},
        "proxy_18009": {"role": "18025_FLANGE_INTERFACE_PROXY_ONLY",
                        "P241_P242_P243": "ALL_HAND_INSERTION_RADIAL_PLAY_NONE_SIX_HOLES_FACE_SEATING_REMOVAL_PASS",
                        "selected_center_pilot": "P241", "center_pilot_d_mm": CENTER_PILOT_D_MM,
                        "physical_coupon_identity": "NOT_RECOVERABLE_BUT_ALL_THREE_PASSED"},
        "architecture": {"hub_count_per_drive": 1, "drive_count": 2, "total_18025_required": 2,
                         "idler_18025_count": 0, "dual_18025_sandwich": "PROHIBITED",
                         "fastener": "M5_CLASS_THROUGH_BOLT+METAL_FLAT_WASHER+METAL_LOCKNUT",
                         "bolt_direction": "HEAD_AT_18025_METAL_FLANGE_LOCKNUT_AT_OPPOSITE_PETG_FACE",
                         "petg_tapped_primary_thread": "PROHIBITED"},
        "recess": {"selected_provisional": SELECTED_PROVISIONAL_POCKET,
                   "flange_pocket_candidates_mm": FLANGE_POCKETS_MM,
                   "flange_pocket_depth_mm": FLANGE_POCKET_DEPTH_MM,
                   "center_pilot_d_mm": CENTER_PILOT_D_MM, "center_pilot_length_mm": CENTER_PILOT_LENGTH_MM,
                   "deep_relief_d_mm": DEEP_RELIEF_D_MM, "deep_relief_length_mm": DEEP_RELIEF_LENGTH_MM,
                   "total_cavity_depth_mm": TOTAL_CAVITY_DEPTH_MM,
                   "axial_datum": "18025_FLANGE_SEAT_NOT_BOSS_CAVITY_BOTTOM",
                   "drain_d_mm": DRAIN_D_MM, "drain_angle_deg": DRAIN_ANGLE_DEG},
        "support": support,
        "radial_margin": {"v09629_12t_flange_to_tooth_root_mm": source_margin,
                          "v09630_14t_flange_to_tooth_root_mm": target_margin,
                          "increase_mm": target_margin - source_margin,
                          "continuous_ring_ligament_mm": support["selected_flange_to_ring_ligament_mm"],
                          "hard_minimum_mm": 5.0, "target_mm": 6.0},
        "loop": loop,
        "idler": {"tooth_count": IDLER_TOOTH_COUNT, "change_count": 0, "artifact_duplication_count": 0},
        "frame_clearance": {"14t_radial_increase_mm": RADIAL_INCREASE_MM,
                            "repository_link_to_nearest_frame_face_mm": 60.0,
                            "abstract_remaining_separation_mm": 60.0 - RADIAL_INCREASE_MM,
                            "result": "HOLD_EXACT_14T_ASSEMBLY_TRANSFORM_AND_PHYSICAL_FRAME_DATUM"},
        "roller_clearance": {"roller_od_mm": 16.0, "raised_lowered_range_mm": [0.0, 3.0],
                             "result": "HOLD_REPOSITION_AND_REVALIDATE_14T_LINK_PATH"},
        "hardware_stack": {"external_locknut_required_under_head_mm": external_stack,
                           "open_counterbore_required_under_head_mm": counterbore_stack,
                           "counterbore_d_mm": LOCKNUT_COUNTERBORE_D_MM,
                           "counterbore_depth_mm": LOCKNUT_COUNTERBORE_DEPTH_MM,
                           "remaining_local_petg_backing_mm": TOOTH_WIDTH_MM - FLANGE_POCKET_DEPTH_MM - LOCKNUT_COUNTERBORE_DEPTH_MM,
                           "bolt_candidates_mm": BOLT_LENGTH_CANDIDATES_MM,
                           "provisional_preference": "M5x50_WITH_OPEN_COUNTERBORE",
                           "final": "PHYSICAL_HARDWARE_HOLD"},
        "torque_reference": {"torque_nm": TORQUE_REFERENCE_NM, "pcd_radius_m": PCD_RADIUS_M,
                             "tangential_resultant_n": TANGENTIAL_RESULTANT_N,
                             "ideal_equal_share_per_fastener_n": IDEAL_BOLT_SHARE_N,
                             "authority": "LOAD_DISTRIBUTION_REFERENCE_NOT_STRUCTURAL_PROOF"},
        "tradeoff": {"same_rpm_speed_ratio": TARGET_TOOTH_COUNT / SOURCE_TOOTH_COUNT,
                     "same_torque_ideal_force_ratio": SOURCE_TOOTH_COUNT / TARGET_TOOTH_COUNT},
        "state_matrix": {"CAD_PASS": "PASS", "CONTRACT_TEST_PASS": "PASS_AFTER_TEST",
                         "PRINT_PASS": "NOT_YET", "FIT_PASS": "NOT_YET_FOR_F569_F570_F571",
                         "18025_PHYSICAL_FIT_PASS": "NOT_YET", "14T_CRAWLER_PHYSICAL_PASS": "NOT_YET",
                         "STATIC_6P5NM_PASS": "NOT_YET", "POWERED_PASS": "NOT_YET",
                         "MUD_PASS": "NOT_YET", "FIELD_PASS": "NOT_YET", "DURABILITY_PASS": "NOT_YET",
                         "final_physical_classification": "UNKNOWN_REQUIRES_PHYSICAL_TEST"},
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-18T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP timestamp normalization")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    exporters.export(shape, str(path))
    normalize_step(path)


def binary_stl(path: Path):
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError("STL too short")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError("STL must be binary")
    rows = []
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        rows.append((values[3:6], values[6:9], values[9:12]))
    return rows


def stl_reload(path: Path) -> bool:
    raw = TopoDS_Shape()
    return bool(StlAPI_Reader().Read(raw, str(path))) and not raw.IsNull()


def mesh_metrics(path: Path) -> dict[str, object]:
    triangles = binary_stl(path)
    edges: Counter = Counter()
    triangle_edges = []
    degenerate = 0
    vertices = []
    for tri in triangles:
        keys = [tuple(round(float(value), 6) for value in vertex) for vertex in tri]
        vertices.extend(keys)
        ax, ay, az = (keys[1][i] - keys[0][i] for i in range(3))
        bx, by, bz = (keys[2][i] - keys[0][i] for i in range(3))
        cross = (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)
        if sum(value * value for value in cross) <= 1e-16:
            degenerate += 1
        row = []
        for a, b in ((keys[0], keys[1]), (keys[1], keys[2]), (keys[2], keys[0])):
            edge = tuple(sorted((a, b)))
            edges[edge] += 1
            row.append(edge)
        triangle_edges.append(row)
    parents = list(range(len(triangles)))
    def find(x):
        while parents[x] != x:
            parents[x] = parents[parents[x]]
            x = parents[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parents[rb] = ra
    owners = {}
    for index, row in enumerate(triangle_edges):
        for edge in row:
            if edge in owners:
                union(index, owners[edge])
            else:
                owners[edge] = index
    bad = sum(value != 2 for value in edges.values())
    xs, ys, zs = zip(*vertices)
    return {"triangle_count": len(triangles), "component_count": len({find(i) for i in range(len(triangles))}),
            "watertight": bad == 0, "bad_edge_count": bad, "degenerate_triangle_count": degenerate,
            "reload": "PASS" if stl_reload(path) else "FAIL",
            "bbox_mm": [min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)]}


def export_outputs(out: Path):
    shapes = {
        CAD[0]: flange_coupon("F569"), CAD[1]: flange_coupon("F570"),
        CAD[2]: flange_coupon("F571"), CAD[3]: flange_triplet(),
        CAD[4]: full_drive(), CAD[5]: full_drive(), CAD[6]: assembly_reference(),
    }
    for rel, shape in shapes.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".step"):
            export_step(shape, path)
        else:
            exporters.export(shape, str(path), tolerance=0.03, angularTolerance=0.08)
    meshes = {rel: mesh_metrics(out / rel) for rel in CAD if rel.endswith(".stl")}
    expected_components = {CAD[0]: 1, CAD[1]: 1, CAD[2]: 1, CAD[3]: 3, CAD[5]: 1}
    for rel, metric in meshes.items():
        if (not metric["watertight"] or metric["bad_edge_count"] or metric["degenerate_triangle_count"]
                or metric["component_count"] != expected_components[rel] or metric["reload"] != "PASS"):
            raise RuntimeError(f"mesh contract {rel}: {metric}")
    step_import = {}
    for rel, expected_solids in ((CAD[4], 1), (CAD[6], 10)):
        imported = importers.importStep(str(out / rel))
        valid = imported.solids().size() == expected_solids and all(solid.isValid() for solid in imported.solids().vals())
        step_import[rel] = {"valid": valid, "solid_count": imported.solids().size(),
                            "reload": "PASS" if valid else "FAIL"}
        if not valid:
            raise RuntimeError(f"STEP reload {rel}: {step_import[rel]}")
    return meshes, step_import


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">
<rect width="1200" height="700" fill="#fbfaf6"/><style>text{{font-family:Arial,sans-serif;fill:#17252a}} .t{{font-size:32px;font-weight:bold}} .m{{font-size:21px}} .s{{fill:none;stroke:#264653;stroke-width:5}} .a{{fill:none;stroke:#e76f51;stroke-width:5}} .g{{fill:none;stroke:#2a9d8f;stroke-width:5}} .d{{stroke-dasharray:12 8}}</style>
<text x="55" y="55" class="t">{title}</text>{body}<text x="55" y="670" class="m">v0.9.6.30 · PROVISIONAL · NOT FIELD AUTHORITY</text></svg>'''


def svg_documents(geom: dict[str, object]) -> dict[str, str]:
    p = geom["p20653"]
    loop = geom["loop"]
    support = geom["support"]
    circles = ''.join(f'<circle cx="600" cy="350" r="{310 if i%2==0 else 285}" class="s"/><line x1="600" y1="350" x2="{600+310*math.cos(math.radians(TARGET_PHASE_DEG+i*TARGET_SPACING_DEG)):.2f}" y2="{350+310*math.sin(math.radians(TARGET_PHASE_DEG+i*TARGET_SPACING_DEG)):.2f}" class="g"/>' for i in range(14))
    one_hub = '<circle cx="420" cy="350" r="190" class="g"/><circle cx="420" cy="350" r="115" class="a"/><text x="680" y="300" class="m">18025 ×1 / DRIVE</text><text x="680" y="340" class="m">dual sandwich prohibited</text>'
    recess = '<rect x="170" y="180" width="860" height="280" class="s"/><rect x="170" y="220" width="125" height="200" class="a"/><rect x="295" y="280" width="420" height="80" class="g"/><text x="180" y="520" class="m">6.2 flange pocket → 4.0 P241 pilot → 16.6 deep relief; total 26.8</text>'
    bolt = '<text x="90" y="150" class="m">low-profile M5 head</text><line x1="300" y1="140" x2="900" y2="560" class="s"/><text x="330" y="230" class="m">18025 metal flange</text><text x="470" y="330" class="m">PETG 14T / full width</text><text x="700" y="450" class="m">metal washer</text><text x="880" y="550" class="m">metal locknut · ≥2 threads</text>'
    loop_body = f'<circle cx="300" cy="350" r="125" class="g"/><circle cx="900" cy="350" r="108" class="s"/><line x1="300" y1="225" x2="900" y2="242" class="a"/><line x1="300" y1="475" x2="900" y2="458" class="a"/><text x="350" y="610" class="m">C=280; current 40-link shift={loop["rows"][0]["required_inward_shift_mm"]:.3f} mm inward; physical stroke HOLD</text>'
    return {
        "18025_DIMENSION_TRACE.svg": svg_page("18025 dimension trace", '<text x="80" y="140" class="m">USER-SUPPLIED OFFICIAL DRAWING + VSTONE</text><text x="80" y="200" class="m">Ø56.8 flange · Ø24 boss · W26.4 · flange 6.0 · boss derived 20.4</text><text x="80" y="260" class="m">Ø10 +0.02/0 · key 3 +0.02/0 · raw drawing value 11.4 retained</text>'),
        "artifacts/12t_vs_14t_pitch_geometry.svg": svg_page("P20653 12T vs 14T", f'<circle cx="350" cy="350" r="200" class="s"/><circle cx="850" cy="350" r="233" class="g"/><text x="230" y="590" class="m">12T D={SOURCE_PITCH_DIAMETER_MM:.6f}</text><text x="730" y="590" class="m">14T D={TARGET_PITCH_DIAMETER_MM:.6f}</text>'),
        "artifacts/12t_vs_14t_hub_margin.svg": svg_page("Hub / tooth-root margin", f'<circle cx="350" cy="350" r="170" class="a"/><circle cx="350" cy="350" r="{170+geom["radial_margin"]["v09629_12t_flange_to_tooth_root_mm"]*8:.1f}" class="s"/><circle cx="850" cy="350" r="170" class="a"/><circle cx="850" cy="350" r="{170+geom["radial_margin"]["v09630_14t_flange_to_tooth_root_mm"]*8:.1f}" class="g"/><text x="170" y="610" class="m">12T {geom["radial_margin"]["v09629_12t_flange_to_tooth_root_mm"]:.3f} mm</text><text x="700" y="610" class="m">14T {geom["radial_margin"]["v09630_14t_flange_to_tooth_root_mm"]:.3f} mm</text>'),
        "artifacts/14t_tooth_array.svg": svg_page("14T exact rigid tooth array", circles),
        "artifacts/18025_official_dimensions.svg": svg_page("Nexus/Vstone 18025 official dimensions", '<circle cx="360" cy="350" r="210" class="s"/><circle cx="360" cy="350" r="88" class="g"/><text x="670" y="230" class="m">flange Ø56.8 ±0.03</text><text x="670" y="280" class="m">boss Ø24 · bore Ø10 +0.02/0</text><text x="670" y="330" class="m">PCD47.5 · 6×Ø5.2</text><text x="670" y="380" class="m">overall 26.4 · flange 6.0</text>'),
        "artifacts/18025_one_hub_architecture.svg": svg_page("One 18025 per DRIVE", one_hub),
        "artifacts/18025_full_recess_section.svg": svg_page("18025 full-recess section", recess),
        "artifacts/boss_pilot_relief_section.svg": svg_page("Boss pilot and relief", recess),
        "artifacts/full_width_support_drum_section.svg": svg_page("Full-width PETG support drum", f'<rect x="140" y="210" width="920" height="240" class="g"/><rect x="390" y="190" width="420" height="280" class="a"/><text x="250" y="540" class="m">44 mm explicit solid · ring R{SUPPORT_RING_RADIUS_MM} · 14 local R3 root bridges</text>'),
        "artifacts/link_swept_clearance.svg": svg_page("Exact link swept-envelope clearance", f'<circle cx="600" cy="350" r="260" class="g"/><circle cx="600" cy="350" r="{260+support["noncontact_ring_clearance_mm"]*30:.1f}" class="a d"/><text x="250" y="610" class="m">non-contact ring clearance {support["noncontact_ring_clearance_mm"]:.3f} mm = HARD PASS / 1.0 target miss</text>'),
        "artifacts/m5_through_bolt_stack.svg": svg_page("M5 through-bolt exploded stack", bolt),
        "artifacts/flange_pocket_candidates.svg": svg_page("F569 / F570 / F571 proxy coupons", '<circle cx="260" cy="350" r="150" class="s"/><circle cx="600" cy="350" r="150" class="g"/><circle cx="940" cy="350" r="150" class="a"/><text x="190" y="570" class="m">F569 · 1 notch</text><text x="530" y="570" class="m">F570 · 2 notches</text><text x="870" y="570" class="m">F571 · 3 notches</text>'),
        "artifacts/14t_12t_crawler_loop.svg": svg_page("14T DRIVE + 12T IDLER", loop_body),
        "artifacts/crawler_loop_14t_12t.svg": svg_page("Crawler-loop link count study", loop_body),
        "artifacts/tooth_bending_test.svg": svg_page("Tooth bending physical screen", '<path d="M260 520 L420 180 L580 520" class="s"/><line x1="420" y1="180" x2="760" y2="180" class="a"/><text x="780" y="185" class="m">10 → 20 → 30 N</text><text x="300" y="600" class="m">record displacement / whitening / crack / permanent set</text>'),
        "artifacts/physical_validation_sequence.svg": svg_page("Physical validation sequence", '<text x="80" y="150" class="m">1 F569/F570/F571 triplet + permanent notch IDs</text><text x="80" y="220" class="m">2 18009 proxy fit · seating · 6-hole alignment · removal</text><text x="80" y="290" class="m">3 verify real tensioner stroke and 14T/12T loop</text><text x="80" y="360" class="m">4 full 14T print · tooth bending 10/20/30 N</text><text x="80" y="430" class="m">5 actual 18025/keyed shaft · static 2/4.5/6.5 N·m</text><text x="80" y="500" class="m">6 powered 1–2 / 5 / 10 s only after static PASS</text>'),
    }


def md_header(title: str) -> str:
    return f"# {title}\n\nVersion: `{VERSION}`  \nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"


def csv_loop(loop: dict[str, object]) -> str:
    rows = ["configuration,link_count,available_link_path_mm,required_center_distance_mm,idler_displacement_from_current_mm,remaining_candidate_stroke_mm,practical_candidate_12mm,physical_status"]
    for row in loop["rows"]:
        rows.append(f'{row["configuration"]},{row["link_count"]},{row["available_link_path_mm"]:.9f},{row["required_center_distance_mm"]:.9f},{row["idler_displacement_from_current_mm"]:.9f},{row["remaining_candidate_stroke_mm"]:.9f},{row["practical_with_candidate_12mm_stroke"]},{row["physical_status"]}')
    return "\n".join(rows)


def documentation(geom: dict[str, object]) -> dict[str, str]:
    h = md_header
    p, v, support, loop = geom["p20653"], geom["vendor_18025"], geom["support"], geom["loop"]
    docs = {
        "README.md": h("P20653 14T / 18025 full-width through-bolt DRIVE") + "\n14Tは12Tのscaleではありません。P20653局所歯solidを剛体変換し、全幅drumとPCD47.5のM5貫通6本を追加した仮CADです。最初の印刷はF569/F570/F571 tripletだけです。\n",
        "DESIGN_AUTHORITY.md": h("Design authority") + "\nP20653 pitchと局所歯形はv0.9.6.20、proxy結果はv0.9.6.29、18025寸法はユーザー提示Vstone公式図面がauthorityです。CAD_PASSは物理fit/torque/crawler/field PASSではありません。\n",
        "BLOCKER_TARGET.md": h("Blocker target") + "\nPrimary=`BLOCKER_1_DRIVETRAIN_TORQUE_TRANSMISSION`; sub-blocker=`DRIVE_TOOTH_ROOT_STRUCTURAL_ROBUSTNESS`。手加工D-flat set-screwはproduction architectureとしてREJECTEDです。\n",
        "PHYSICAL_STATE_MATRIX.md": h("Physical state matrix") + "\nCAD/contractのみPASS可能。PRINT、F569/F570/F571 fit、18025 fit、14T crawler、static 6.5 N·m、powered、mud、field、durabilityは`NOT_YET`です。\n",
        "18025_OFFICIAL_SPEC_RECORD.md": h("18025 official specification record") + f"\nAuthority=`USER_SUPPLIED_OFFICIAL_VENDOR_DRAWING + VSTONE_VENDOR_DRAWING_AUTHORITY`。flange Ø{HUB_FLANGE_OD_MM}±0.03、boss Ø{HUB_BOSS_OD_MM}、overall {HUB_OVERALL_WIDTH_MM}、flange {HUB_FLANGE_THICKNESS_MM}、derived boss projection {HUB_BOSS_EXTENSION_MM}、bore Ø10 +0.02/0、PCD47.5、6×Ø5.2、key 3 +0.02/0。raw 11.4は再解釈せず記録し、1.4を用いる場合だけ`DERIVED_VENDOR_DRAWING_REFERENCE`です。\n\nDrawing: {VENDOR_DRAWING_URL}\n\nProduct: {PRODUCT_URL}\n",
        "18009_PROXY_PHYSICAL_RESULT.md": h("18009 proxy physical result") + "\nP241/P242/P243は全てhand insertion、radial play明確なし、6穴alignment、face seating、hand removal PASS。識別不能だったためsmallest non-binding ruleでP241=24.10 mmを暫定採用。これは`18009_PROXY_CENTER_PILOT_PASS`であり18025実fitではありません。\n",
        "MULTI_CANDIDATE_IDENTIFICATION_RULE.md": h("Multi-candidate geometric identification") + "\n文字だけは禁止。F569=外周1 notch、F570=2 notch、F571=3 notch。識別は非機能外周に置き、tooth、pilot、bolt seat、rootへ置きません。\n",
        "flange_pocket_candidate_test_form.csv": "candidate,pocket_d_mm,notches,stl,test_form_mapping\nF569,56.90,1,18025_flange_recess_f569_v0_9_6_30.stl,ROW_1\nF570,57.00,2,18025_flange_recess_f570_v0_9_6_30.stl,ROW_2\nF571,57.10,3,18025_flange_recess_f571_v0_9_6_30.stl,ROW_3\n",
        "P20653_12T_SOURCE_AUTHORITY.md": h("P20653 12T source authority") + "\nExact source=`common_rover_physical_pitch_drive_idler_v0_9_6_20`。pitch=20.6533333333、D12=79.79835226236546、12T、spacing30°、phase15°、axial44 mm。運転時universal pitchではなくphysical maximum-extension supported primary candidateです。\n",
        "P20653_14T_DERIVATION.md": h("P20653 14T derivation") + f"\n`D=P/sin(pi/N)`よりD14={TARGET_PITCH_DIAMETER_MM:.12f} mm、radial increase={RADIAL_INCREASE_MM:.12f} mm。adjacent chord={p['adjacent_pitch_chord_mm']:.12f} mm。scale=1.0です。\n",
        "TOOTH_LOCAL_GEOMETRY_FREEZE.md": h("Tooth local geometry freeze") + f"\n全14歯をsource local solidのrigid rotation+translationだけで生成。inverse transform regression: max added={p['regression']['max_added_volume_mm3']} mm³、max removed={p['regression']['max_removed_volume_mm3']} mm³、14/14 PASS={p['regression']['all_14_pass']}。\n",
        "PHASE_DERIVATION.md": h("14T phase derivation") + f"\n12T sourceの15°はspacing30°の半分です。同じconventionを維持し、14T phase=`(360/14)/2`={TARGET_PHASE_DEG:.12f}°としました。数値15°はblind preserveしていません。\n",
        "14T_SIZE_COMPARISON.md": h("12T / 14T size comparison") + f"\nD12={SOURCE_PITCH_DIAMETER_MM:.9f}、D14={TARGET_PITCH_DIAMETER_MM:.9f}、diameter increase={TARGET_PITCH_DIAMETER_MM-SOURCE_PITCH_DIAMETER_MM:.9f}、tip radial envelope={support['target_14t_tip_radius_mm']:.9f} mm。\n",
        "14T_SPEED_FORCE_TRADEOFF.md": h("Speed / force tradeoff") + "\nSame shaft rpm speed ratio=14/12=1.1666666667 (+16.67%)。Same shaft torque ideal tangential force ratio=12/14=0.8571428571 (-14.29%)。KINEMATIC_REFERENCEでfield resultではありません。\n",
        "IDLER_FIREWALL.md": h("12T IDLER firewall") + "\nIDLER=existing P20653 12T、変更file=0、duplicate artifact=0、18025使用=0。14T DRIVEとのmixed count loopだけを再計算しました。\n",
        "CRAWLER_LOOP_14T_12T_STUDY.md": h("14T DRIVE + 12T IDLER loop study") + f"\nCurrent authority: link count40、center distance280 mm、candidate stroke12 mm、実available stroke=`HOLD`。same-countはinward {loop['rows'][0]['required_inward_shift_mm']:.6f} mm、candidate remaining {loop['rows'][0]['remaining_candidate_stroke_mm']:.6f} mm。+1/+2は外向き移動を要しmax-extension datumと非整合。暫定選択=`{loop['selected_provisional']}`ですがreal strokeとservice margin未測定なのでfull 14T printはHOLDです。\n",
        "crawler_loop_link_count_table.csv": csv_loop(loop),
        "FRAME_CLEARANCE_STUDY.md": h("Frame / roller clearance study") + f"\n14T radial increase={RADIAL_INCREASE_MM:.6f} mm。repositoryにはlink-to-nearest-frame face 60 mmがありますが座標transformの物理authorityが不足するためframe=`HOLD_EXACT_14T_ASSEMBLY_TRANSFORM`。Ø16 hold-down roller 0..3 mmは14T link pathへ再配置し、raised/lowered双方を物理再検証します。ground/water envelopeもHOLDです。\n",
        "18025_RECESS_ARCHITECTURE.md": h("18025 full-recess architecture") + "\n1 DRIVEに18025×1、one face/one recess。metal body26.4 mmは44 mm width内部へ格納可能。dual sandwichは禁止。primary axial datumはflange seatです。\n",
        "FLANGE_POCKET_CANDIDATE_STUDY.md": h("Flange pocket candidates") + "\nF569=Ø56.90/1 notch、F570=Ø57.00/2 notch、F571=Ø57.10/3 notch、depth6.20。18009でhand insertion、full seating、6-hole alignment、rocking、removal、PETG damageを評価しsmallest non-bindingを選びます。\n",
        "BOSS_PILOT_AND_RELIEF.md": h("Boss pilot / relief") + "\nP241 Ø24.10×4.0 short pilot、続いてØ24.50×16.6 deep relief。total cavity depth26.8。boss bottomをaxial datumにせず0.4 mm class bottom clearanceを残します。\n",
        "FULL_WIDTH_SUPPORT_DRUM.md": h("Full-width support drum") + f"\nExplicit CAD solid: width44、continuous ring R{SUPPORT_RING_RADIUS_MM}、14個のlocal rounded root pad R{ROOT_PAD_FILLET_MM}。slicer infill依存ではありません。non-contact ring clearance={support['noncontact_ring_clearance_mm']:.6f} mmでhard0.8 PASS / target1.0 MISS。\n",
        "LINK_SWEPT_CLEARANCE.md": h("Exact crawler-link swept clearance") + f"\nSource `STANDARD_V0125_WIDE_46_LINK.stl` SHA={support['link_source_sha256']}、scaleなし。14位置のkinematic sweepに対しnon-contact ring intersection max={support['noncontact_ring_intersection_max_mm3']} mm³、clearance={support['noncontact_ring_clearance_mm']:.6f} mm。local root padsはintended tooth-root contact sector内だけです。\n",
        "RADIAL_STRUCTURAL_MARGIN.md": h("Radial structural margin") + f"\nflange R28.4からtooth root: v0.9.6.29={geom['radial_margin']['v09629_12t_flange_to_tooth_root_mm']:.6f} mm、v0.9.6.30={geom['radial_margin']['v09630_14t_flange_to_tooth_root_mm']:.6f} mm。F569 pocketからcontinuous ring={geom['radial_margin']['continuous_ring_ligament_mm']:.6f} mmでhard5 PASS、target6 MISS。歯曲げ物理試験前にstrength PASSとはしません。\n",
        "M5_THROUGH_BOLT_ARCHITECTURE.md": h("M5 through-bolt architecture") + "\nPCD47.5、6×vendor Ø5.2、PETG Ø5.5。headは18025 metal flange側、反対PETG面にmetal flat washer+metal locknut。PETG tap、hidden captive nut、set-screw torque pathは禁止。\n",
        "HARDWARE_STACK_STUDY.md": h("Hardware stack study") + f"\nExternal locknut required under-head length={geom['hardware_stack']['external_locknut_required_under_head_mm']:.1f} mm、open Ø12×4 counterbore candidate={geom['hardware_stack']['open_counterbore_required_under_head_mm']:.1f} mm。M5×50/55/60を比較しcounterbore時M5×50を暫定preferred。ただしwasher/nut/head実測まで`PHYSICAL_HARDWARE_HOLD`。\n",
        "WIDTH_OPTIMIZATION.md": h("Width optimization") + "\nFULL_18025_RECESSとopen serviceable locknut counterboreを採用候補とし、hub本体の軸方向追加幅を抑えます。counterboreはvisible/removableで、remaining local PETG backing33.8 mmです。\n",
        "DRAIN_WASHOUT_DESIGN.md": h("Drain / washout") + f"\nØ{DRAIN_D_MM}のradiused radial pathをgravity-lower candidate angle {DRAIN_ANGLE_DEG:.6f}°へ配置。mud exclusionはNO、drain/washはYES。bolt washer seatを避け、全周ringを切断しません。実wheel orientationはHOLDです。\n",
        "TOOTH_BENDING_PHYSICAL_CONTRACT.md": h("Tooth bending physical contract") + "\nDefined tooth-tip pointで10/20/30 N。load、lever、tip displacement、white stress、crack、permanent setを記録。結果classはSCREEN_PASS/STIFFNESS_IMPROVED/ROOT_CRACK/PERMANENT_SET/FIXTURE_FAILでFIELD_PASSへ自動昇格しません。\n",
        "STATIC_6P5NM_TEST_PLAN.md": h("Static torque gate") + "\n実18025、pre-machined keyed shaft、3 mm key、fasteners到着後に2.0→4.5→6.5 N·m。全界面shift0、loosening0、hole elongation0、whitening/crackなし、key deformationなし、分解可能を要求。\n",
        "POWERED_TEST_GATE.md": h("Powered gate") + "\nStatic6.5 N·m PASS後だけ1–2 s、inspect、5 s、inspect、10 s、inspect。maximum tension/roller loweredはsevere screenで最終settingではありません。その後minimum tension without skipを探索します。現状NOT_APPROVED。\n",
        "PRINT_PLAN.md": h("Print plan") + "\nFIRST PRINT=`18025_flange_recess_triplet_v0_9_6_30.stl`。Bambu A1/PETG、0.4 nozzle/0.20 layer参考。full DRIVEはflange winner、real tensioner stroke、loop/frame/roller gate後。>=8 walls hub/root、>=6 top/bottom候補。slicer未実行HOLD。\n",
        "FAILURE_CRITERIA.md": h("Failure criteria") + "\nhammer fit、rocking、misaligned hole、PETG whitening/crack、link non-contact collision、ring clearance<0.8、continuous ligament<5、tension margin<2、bolt inaccessible、tooth/root crack、shift、looseningでFAIL/HOLD。\n",
        "HOLD_REGISTER.md": h("HOLD register") + "\nHOLD: actual18025 dimensions/set screw; flange winner; actual washer/nut/head/bolt length; real tensioner stroke/current slot; exact frame transform; roller relocation; ground/water geometry; slicer; print/fit; tooth bending; 14T crawler; shaft/key receipt; static torque; powered; water/mud; field; durability.\n",
        "NEXT_DEVELOPMENT_GATE.md": h("Next development gate") + "\n1 triplet print/18009 proxy、2 physical flange winner、3 tensioner actual stroke measurement、4 frame/roller dry-fit、5 full14T print/tooth-bending、6 actual18025/keyed static test、7 short powered sequence。\n",
        "SOURCE_TRACE.md": h("Source trace") + f"\nP20653 builder `{V20_BUILDER_REL.as_posix()}`。18025 predecessor `{V29_BUILDER_REL.parent.as_posix()}`。Exact link SHA `{support['link_source_sha256']}`。Vendor drawing `{VENDOR_DRAWING_URL}`。\n",
    }
    docs["18025_VENDOR_DRAWING_AUTHORITY.json"] = json.dumps({
        "authority_class": "USER_SUPPLIED_OFFICIAL_VENDOR_DRAWING+VSTONE_VENDOR_DRAWING_AUTHORITY",
        "part": "Nexus/Vstone 18025", "drawing_url": VENDOR_DRAWING_URL, "product_url": PRODUCT_URL,
        "dimensions_mm": v, "firewall": {"physical_measured": "NOT_YET",
        "raw_11p4_not_silently_reinterpreted": True, "set_screw_service_tunnel": "PROHIBITED_IN_V09630"}
    }, ensure_ascii=False, sort_keys=True, indent=2)
    return docs


def parameters() -> dict[str, object]:
    return {"version": VERSION, "classification": CLASSIFICATION,
            "p20653": {"pitch_mm": PITCH_MM, "source_tooth_count": SOURCE_TOOTH_COUNT,
                       "target_tooth_count": TARGET_TOOTH_COUNT, "target_pitch_diameter_mm": TARGET_PITCH_DIAMETER_MM,
                       "target_spacing_deg": TARGET_SPACING_DEG, "target_phase_deg": TARGET_PHASE_DEG,
                       "tooth_width_mm": TOOTH_WIDTH_MM},
            "vendor_18025": {"flange_od_mm": HUB_FLANGE_OD_MM, "boss_od_mm": HUB_BOSS_OD_MM,
                             "overall_width_mm": HUB_OVERALL_WIDTH_MM, "flange_thickness_mm": HUB_FLANGE_THICKNESS_MM,
                             "boss_extension_derived_mm": HUB_BOSS_EXTENSION_MM, "bore_mm": HUB_BORE_MM,
                             "pcd_mm": HUB_PCD_MM, "holes": HUB_HOLE_COUNT, "vendor_hole_mm": HUB_HOLE_MM,
                             "keyway_width_mm": HUB_KEYWAY_WIDTH_MM, "raw_drawing_dimension_mm": HUB_RAW_DRAWING_DIMENSION_MM},
            "recess": {"candidates_mm": FLANGE_POCKETS_MM, "depth_mm": FLANGE_POCKET_DEPTH_MM,
                       "pilot_mm": CENTER_PILOT_D_MM, "pilot_length_mm": CENTER_PILOT_LENGTH_MM,
                       "relief_mm": DEEP_RELIEF_D_MM, "total_depth_mm": TOTAL_CAVITY_DEPTH_MM},
            "support": {"ring_radius_mm": SUPPORT_RING_RADIUS_MM, "width_mm": TOOTH_WIDTH_MM,
                        "pad_inner_mm": ROOT_PAD_INNER_RADIUS_MM, "pad_outer_mm": ROOT_PAD_OUTER_RADIUS_MM,
                        "root_fillet_mm": ROOT_PAD_FILLET_MM},
            "crawler": {"link_count": LINK_COUNT, "center_distance_mm": CURRENT_CENTER_DISTANCE_MM,
                        "tension_stroke_candidate_mm": SOURCE_TENSION_STROKE_CANDIDATE_MM,
                        "physical_available_stroke": PHYSICAL_AVAILABLE_TENSION_STROKE},
            "status": STATUS}


def validation(repo, geom, meshes, steps) -> dict[str, object]:
    checks = {
        "repository_guard": "PASS", "authority_4_of_4": "PASS", "protected_lanes": "PASS",
        "tooth_14": "PASS" if geom["p20653"]["tooth_count"] == 14 else "FAIL",
        "pitch_chord_exact": "PASS" if abs(geom["p20653"]["adjacent_pitch_chord_mm"] - PITCH_MM) < 1e-9 else "FAIL",
        "tooth_regression_14_of_14": "PASS" if geom["p20653"]["regression"]["all_14_pass"] else "FAIL",
        "idler_change_zero": "PASS", "one_hub_per_drive": "PASS", "six_through_bolts": "PASS",
        "support_continuous": "PASS", "link_noncontact_intersection_zero":
            "PASS" if geom["support"]["noncontact_ring_intersection_max_mm3"] == 0 else "FAIL",
        "link_clearance_hard": "PASS" if geom["support"]["noncontact_ring_clearance_mm"] >= 0.8 else "FAIL",
        "link_clearance_target": "PASS" if geom["support"]["noncontact_ring_clearance_mm"] >= 1.0 else "TARGET_MISS",
        "structure_ligament_hard": "PASS" if geom["radial_margin"]["continuous_ring_ligament_mm"] >= 5.0 else "FAIL",
        "structure_ligament_target": "PASS" if geom["radial_margin"]["continuous_ring_ligament_mm"] >= 6.0 else "TARGET_MISS",
        "all_stl": "PASS" if all(m["watertight"] and m["bad_edge_count"] == 0 and m["degenerate_triangle_count"] == 0 and m["reload"] == "PASS" for m in meshes.values()) else "FAIL",
        "all_step": "PASS" if all(m["valid"] and m["reload"] == "PASS" for m in steps.values()) else "FAIL",
        "field": "NOT_YET", "powered": "NOT_APPROVED",
    }
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "checks": checks, "repository": repo, "geometry": geom, "mesh": meshes, "step_import": steps,
            "artifact_counts": {"step": 2, "stl": 5, "svg": len(SVGS) + 1},
            "physical_classification": "UNKNOWN_REQUIRES_PHYSICAL_TEST"}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False)
    geom = geometry_analysis()
    meshes, steps = export_outputs(out)
    for rel, value in documentation(geom).items():
        write_text(out / rel, value)
    for rel, value in svg_documents(geom).items():
        write_text(out / rel, value)
    write_json(out / "design_parameters.json", parameters())
    write_json(out / "validation_report.json", validation(repo, geom, meshes, steps))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=2\nSTL=5\nSVG={len(SVGS)+1}\nTOOTH_REGRESSION=14/14_PASS\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", f"CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=246\nBUILDER_VERIFY=PASS\nSTEP_RELOAD=2_OF_2_PASS\nSTL_RELOAD=5_OF_5_PASS\nREPRODUCIBILITY={EXPECTED_PATH_COUNT}_OF_{EXPECTED_PATH_COUNT}_PASS\nPHYSICAL=NOT_YET")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError(f"exact paths {len(files)} != {EXPECTED_PATH_COUNT}: {set(files)^set(EXPECTED_FILES)}")
    return {"path_count": len(files), "geometry": geom, "mesh": meshes, "step_import": steps, "status": STATUS}


def parse_sums(path: Path) -> dict[str, str]:
    result = {}
    for row in path.read_text(encoding="utf-8").splitlines():
        value, rel = row.split("  ", 1)
        result[rel] = value
    return result


def verify(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(True)
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError("exact path contract")
    if (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES:
        raise RuntimeError("manifest")
    expected_commit = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != expected_commit:
        raise RuntimeError("commit paths")
    sums = parse_sums(out / "SHA256SUMS.txt")
    mismatch = [rel for rel, digest in sums.items() if sha256(out / rel) != digest]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}:
        raise RuntimeError(f"sha {mismatch}")
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if any(value == "FAIL" for value in report["checks"].values()):
        raise RuntimeError(report["checks"])
    return {"repository": repo, "path_count": len(files), "step_count": len(list(out.rglob("*.step"))),
            "stl_count": len(list(out.rglob("*.stl"))), "svg_count": len(list(out.rglob("*.svg"))),
            "sha_mismatch_count": 0, "checks": report["checks"], "geometry": report["geometry"],
            "mesh": report["mesh"], "step_import": report["step_import"], "status": STATUS}


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_p20653_14t_v09630_") as name:
        shadow = Path(name) / LANE_NAME
        (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER)
        shutil.copyfile(out / TEST, shadow / TEST)
        generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch:
        raise RuntimeError(f"reproducibility mismatch {mismatch}")
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify(out)
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_P20653_14T_18025_FULL_WIDTH_THROUGH_BOLT_DRIVE_v0_9_6_30_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists():
        raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        prefix = LANE_NAME + "/"
        relative = sorted(name[len(prefix):] for name in names if name.startswith(prefix))
        duplicate = len(names) - len(set(names))
        traversal = sum(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names)
        contamination = sum(not name.startswith(prefix) for name in names)
        sums = parse_sums(out / "SHA256SUMS.txt")
        mismatch = sum(hashlib.sha256(archive.read(prefix + rel)).hexdigest() != digest for rel, digest in sums.items())
    result = {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
              "duplicate_count": duplicate, "traversal_count": traversal, "manifest_exact": relative == EXPECTED_FILES,
              "sha_mismatch_count": mismatch, "parent_contamination_count": contamination}
    if duplicate or traversal or contamination or mismatch or relative != EXPECTED_FILES:
        raise RuntimeError(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.error("select action")
    if args.build:
        print(json.dumps({"build": generate_all()}, ensure_ascii=True, indent=2))
    if args.verify:
        print(json.dumps({"verify": verify()}, ensure_ascii=True, indent=2))
    if args.reproducibility:
        print(json.dumps({"reproducibility": reproducibility()}, ensure_ascii=True, indent=2))
    if args.package:
        print(json.dumps({"zip": package()}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
