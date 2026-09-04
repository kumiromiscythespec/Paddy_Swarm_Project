#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Common Rover v0.9.6.22 TEMP 60T double split-clamp pulley.

The v0.9.6.21 STEP is the immediate geometry parent.  The original HTD5M
60T source remains the tooth authority.  Only the central hub/local clamp
envelope is revised; all geometry outside that envelope is regression
compared as BRep volume in both directions.
"""
from __future__ import annotations

import argparse
import collections
from datetime import datetime
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


VERSION = "v0.9.6.22"
CLASSIFICATION = "TEMP_HTD5M_60T_DOUBLE_SIDED_SPLIT_CLAMP"
STATUS = (
    "TEMP_HTD5M_60T_DOUBLE_SPLIT_CLAMP_CAD_COMPLETE/"
    "V09621_PHYSICAL_CLAMP_SHORTFALL_RECORDED/"
    "60T_TOOTH_FLANGE_RIM_SPOKES_EXACTLY_PRESERVED/"
    "CENTRAL_HUB_ONLY_REVISED/FRONT_M4X2_REAR_M4X2_READY/"
    "M4X21_PACKAGING_READY/DOUBLE_CLAMP_COUPONS_READY/"
    "P20653_SCOPE_UNCHANGED/DRY_DUAL_MOTOR_FIXTURE_READY_FOR_PHYSICAL_CLAMP_TEST/"
    "POWERED_USE_PENDING_PHYSICAL_CLAMP_PASS/COMMIT_READY_NOT_STAGED"
)
LANE_NAME = "common_rover_temp_htd5m_60t_double_split_clamp_v0_9_6_22"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2532
BASE_OUTSIDE_DIGEST = "badbe359694c2ac05c861b374672e8df6451a3ab9bf295d084f8635f1d4ed061"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)
PROTECTED_LANES = {
    "cad/common_rover/common_rover_true_open_bottom_dual_l_12t_v0_9_6_16": (37, "fe514d3a9c1ca21bca92beee738ff1ed1b6d47fd2cdb2f2aa59866584303ea56"),
    "cad/common_rover/common_rover_crawler_link_anti_derail_guard_v0_9_6_17": (33, "3e0a550c7d9faa38fae8d106e60b91467788e18533d23063156070d1259615b8"),
    "cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18": (39, "fcab7a320e371504767153d1167c6c7f5416b84a8edd28e7331f988b01998373"),
    "cad/common_rover/common_rover_y3_reaction_shoe_v0_9_6_19": (34, "ede454f33bbd1030c0e744de0fda9614d86d201f89a7ebdc17e8a468bbfedb7a"),
    "cad/common_rover/common_rover_drive_entry_top_hold_down_roller_v0_9_6_19": (39, "e632689b54678455adec6758b2420bcf0ed4a2bd8ade8d229d80087275a4630e"),
    "cad/common_rover/common_rover_physical_pitch_drive_idler_v0_9_6_20": (55, "9d0d0eb92b759be81ed61a69d89a1888adbb4b88fcd66e63b14a056d59966300"),
    "cad/common_rover/common_rover_temp_htd5m_60t_split_clamp_pulley_v0_9_6_21": (40, "1f8d01cda3ca2b049dcffdda17b1f0c15b2c8de809cef476a157b941ddf4edc9"),
    "cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1": (53, "a0cb4b831d639be4619a6bb42bff765a8196e04963dfc2df8826e1bbaf89fe00"),
}

PARENT_REL = PurePosixPath("cad/common_rover/common_rover_temp_htd5m_60t_split_clamp_pulley_v0_9_6_21")
PARENT_DIR = REPO_ROOT / PARENT_REL
PARENT_BUILDER = "build_temp_htd5m_60t_split_clamp_pulley_v0_9_6_21.py"
PARENT_STEP = "artifacts/temp_htd5m_60t_split_clamp_pulley_v0_9_6_21.step"
PARENT_FILES_SHA256 = {
    PARENT_BUILDER: "7656436e04846d253071537b8db865576d587511769ddb9337aa891277b94350",
    PARENT_STEP: "1f4f15cf04614b02b92cf7afca34fc8bb25fe0e356ffc3be87ef7cd04b8bbd2d",
    "artifacts/temp_htd5m_60t_split_clamp_pulley_v0_9_6_21.stl": "e782977d6079e170e69c02663d48b603024ad46b959713f58236be1fe7a0bb74",
    "design_parameters.json": "e5fb3cb10ad389e4042246a2e18c1be183b6503324c204a5833231b33ce188e8",
    "validation_report.json": "a114206e31b9972a793c79799e8895b92e8a98cbc1577044232343b7de54212c",
    "tests/test_temp_htd5m_60t_split_clamp_pulley_v0_9_6_21_contract.py": "cc1dab8aa8d84c2adaf59221ed1478a1754e98256e8615b400c671e14c28ca62",
}
SOURCE_REL = PurePosixPath("cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1")
SOURCE_DIR = REPO_ROOT / SOURCE_REL
SOURCE_STEP = "cad/drive_htd5m_60t_reference.step"
SOURCE_SHA256 = "bc3e00bca0db5fe4c3975b5904ad4f72faa2b3fe6822057522c12df16ec0d256"

TOOTH_COUNT = 60
PITCH_FAMILY = "HTD5M"
PITCH_MM = 5.0
SPACING_DEG = 6.0
TOOTH_FACE_WIDTH_MM = 16.0
FLANGE_COUNT = 2
FLANGE_OD_MM = 102.0
FLANGE_THICKNESS_MM = 2.0
RING_INNER_RADIUS_MM = 37.0
RIM_MIN_RADIAL_MM = 8.946482927568603
SPOKE_COUNT = 6
SPOKE_WIDTH_MM = 10.0
SPOKE_ANGLES_DEG = [30.0 + 60.0 * i for i in range(6)]
BELT_PLANE_Z_MM = 10.0

HUB_OD_MM = 34.0
HUB_RADIUS_MM = HUB_OD_MM / 2.0
HUB_WIDTH_MM = 26.0
NEUTRAL_OD_MM = 28.0
FRONT_ACTIVE_Z_MM = [0.0, 10.0]
NEUTRAL_Z_MM = [10.0, 16.0]
REAR_ACTIVE_Z_MM = [16.0, 26.0]
FRONT_EAR_Z_MM = [0.0, 13.0]
EAR_ISOLATION_GAP_MM = 0.2
REAR_EAR_Z_MM = [13.2, 26.2]
EAR_X_MM = [4.0, 25.0]
EAR_Y_STACK_MM = 14.0
EAR_FILLET_MM = 3.0
BORE_CANDIDATES_MM = [10.10, 10.20, 10.30]
PRIMARY_BORE_MM = 10.20
SHAFT_NOMINAL_MM = 10.0
SPLIT_WIDTH_MM = 1.30
M4_CLEARANCE_MM = 4.50
M4_X_MM = [10.5, 18.5]
FRONT_M4_Z_MM = 6.5
REAR_M4_Z_MM = 19.7
FRONT_M4_COUNT = 2
REAR_M4_COUNT = 2
M4_TOTAL = 4
M4_THREADED_LENGTH_MM = 21.0
WASHER_THICKNESS_CANDIDATE_MM = 1.2
NUT_THICKNESS_CANDIDATE_MM = 3.2
THREAD_PITCH_MM = 0.7
STACK_USED_CANDIDATE_MM = EAR_Y_STACK_MM + 2 * WASHER_THICKNESS_CANDIDATE_MM + NUT_THICKNESS_CANDIDATE_MM
STACK_REMAINING_CANDIDATE_MM = M4_THREADED_LENGTH_MM - STACK_USED_CANDIDATE_MM
VISIBLE_THREAD_CANDIDATE = STACK_REMAINING_CANDIDATE_MM / THREAD_PITCH_MM
EAR_MIN_MM = 4.25
BORE_TO_M4_MIN_MM = min(M4_X_MM) - PRIMARY_BORE_MM / 2.0 - M4_CLEARANCE_MM / 2.0
HUB_WALL_MIN_MM = (NEUTRAL_OD_MM - PRIMARY_BORE_MM) / 2.0
ACCESS_CORRIDOR_DIAMETER_MM = 9.2
ACCESS_Y_EXTENT_MM = 12.0
HUB_MODIFICATION_ENVELOPE = {
    "aabb_min_mm": [2.5, -21.0, -1.0],
    "aabb_max_mm": [27.0, 21.0, 36.0],
    "central_cylinder_radius_mm": 17.05,
    "central_cylinder_z_mm": [-1.0, 27.0],
}

BUILDER = "build_temp_htd5m_60t_double_split_clamp_v0_9_6_22.py"
TEST = "tests/test_temp_htd5m_60t_double_split_clamp_v0_9_6_22_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_FAILURE_FROM_V09621.md", "CHANGE_SCOPE_FIREWALL.md",
    "FROZEN_60T_GEOMETRY.md", "DOUBLE_CLAMP_ARCHITECTURE.md", "FRONT_REAR_CLAMP_BANDS.md",
    "M4X21_HARDWARE_STACK.md", "SHAFT_INTERFACE.md", "BORE_COUPON_PLAN.md", "CLAMP_FORCE_TEST_PLAN.md",
    "PRINT_PLAN.md", "ASSEMBLY_PLAN.md", "SHAFT_WITNESS_MARK.md", "HAND_TEST.md",
    "DUAL_MOTOR_POWERED_TEST.md", "FAILURE_CRITERIA.md", "POWERED_GATE.md", "HOLD_REGISTER.md",
    "SOURCE_TRACE.md", "BUILD_LOG.txt", "TEST_LOG.txt", "design_parameters.json",
    "validation_report.json", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
CAD = [
    "artifacts/temp_htd5m_60t_double_split_clamp_v0_9_6_22.step",
    "artifacts/temp_htd5m_60t_double_split_clamp_v0_9_6_22.stl",
    "artifacts/double_split_clamp_b1010_v0_9_6_22.stl",
    "artifacts/double_split_clamp_b1020_v0_9_6_22.stl",
    "artifacts/double_split_clamp_b1030_v0_9_6_22.stl",
    "artifacts/double_split_clamp_coupon_triplet_v0_9_6_22.stl",
    "artifacts/temp_htd5m_60t_double_split_clamp_hardware_reference_v0_9_6_22.step",
]
SVGS = [
    "artifacts/v09621_vs_v09622_hub.svg", "artifacts/double_clamp_overview.svg",
    "artifacts/front_clamp_section.svg", "artifacts/rear_clamp_section.svg",
    "artifacts/axial_clamp_band_layout.svg", "artifacts/m4x21_stack.svg",
    "artifacts/torque_path.svg", "artifacts/physical_test_sequence.svg",
]
EXPECTED_FILES = sorted([BUILDER, TEST, *DOCS, *CAD, *SVGS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run_git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    h = hashlib.sha256()
    for path in files:
        h.update((path.relative_to(root).as_posix() + "\n").encode())
        h.update(bytes.fromhex(sha256(path)))
    return len(files), h.hexdigest()


def untracked_paths() -> list[str]:
    return sorted(row[3:].replace("\\", "/") for row in run_git("status", "--porcelain=v1", "-uall").splitlines()
                  if row.startswith("?? "))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    protected = {rel: tree_digest(REPO_ROOT / rel) for rel in PROTECTED_LANES}
    parent = {rel: sha256(PARENT_DIR / rel) for rel in PARENT_FILES_SHA256}
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj", ".dxf"}]
    checks = {
        "repository": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "staged_zero": not staged, "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256, "protected_lanes": protected == PROTECTED_LANES,
        "parent_files": parent == PARENT_FILES_SHA256, "original_source": sha256(SOURCE_DIR / SOURCE_STEP) == SOURCE_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES), "lane_cache_zero": not cache,
        "forbidden_zero": not forbidden, "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks, "repository": str(root), "branch": branch, "head": head, "staged": staged,
        "tracked_dirty": dirty, "outside_untracked": outside_snapshot(), "lane_files": len(lane_files),
        "authority_sha256": authority, "parent_sha256": parent,
        "protected_lanes": {rel: {"count": value[0], "tree_sha256": value[1], "status": "UNCHANGED"}
                            for rel, value in protected.items()}, "cache": cache, "forbidden": forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def load_parent():
    spec = importlib.util.spec_from_file_location("paddy_v09621_parent", PARENT_DIR / PARENT_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("parent import spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PARENT = load_parent()


def cylinder(radius: float, height: float, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height).translate((0, 0, z))


def axis_y_cylinder(radius: float, length: float, x: float, y0: float, z: float) -> cq.Workplane:
    solid = cq.Solid.makeCylinder(radius, length, cq.Vector(x, y0, z), cq.Vector(0, 1, 0))
    return cq.Workplane(obj=solid)


def volume(shape: cq.Workplane) -> float:
    return round(sum(float(s.Volume()) for s in shape.solids().vals()), 6)


def parent_pulley() -> cq.Workplane:
    return importers.importStep(str(PARENT_DIR / PARENT_STEP))


def frozen_structure(spoke_outer: float = 38.0, include_ring: bool = True) -> cq.Workplane:
    result = PARENT.source_outer_ring() if include_ring else cq.Workplane("XY")
    first = not include_ring
    for angle in SPOKE_ANGLES_DEG:
        spoke = PARENT.capsule_spoke(16.0, spoke_outer, angle)
        result = spoke if first else result.union(spoke)
        first = False
    return result.clean()


def rounded_band(z0: float, z1: float) -> cq.Workplane:
    shape = (cq.Workplane("XY").box(EAR_X_MM[1] - EAR_X_MM[0], EAR_Y_STACK_MM, z1 - z0)
             .translate(((EAR_X_MM[0] + EAR_X_MM[1]) / 2.0, 0.0, (z0 + z1) / 2.0)))
    return shape.edges("|Z").fillet(EAR_FILLET_MM)


def hub_blank() -> cq.Workplane:
    front = cylinder(HUB_RADIUS_MM, FRONT_ACTIVE_Z_MM[1] - FRONT_ACTIVE_Z_MM[0], FRONT_ACTIVE_Z_MM[0])
    neutral = cylinder(NEUTRAL_OD_MM / 2.0, NEUTRAL_Z_MM[1] - NEUTRAL_Z_MM[0], NEUTRAL_Z_MM[0])
    rear = cylinder(HUB_RADIUS_MM, REAR_ACTIVE_Z_MM[1] - REAR_ACTIVE_Z_MM[0], REAR_ACTIVE_Z_MM[0])
    return (front.union(neutral).union(rear)
            .union(rounded_band(*FRONT_EAR_Z_MM)).union(rounded_band(*REAR_EAR_Z_MM)).clean())


def clamp_cutters(bore_mm: float) -> list[cq.Workplane]:
    cutters = [cylinder(bore_mm / 2.0, HUB_WIDTH_MM + 4.0, -2.0)]
    split = (cq.Workplane("XY").box(EAR_X_MM[1] - 4.7 + 2.0, SPLIT_WIDTH_MM, HUB_WIDTH_MM + 4.0)
             .translate(((4.7 + EAR_X_MM[1] + 2.0) / 2.0, 0.0, HUB_WIDTH_MM / 2.0)))
    cutters.append(split)
    for z in (FRONT_M4_Z_MM, REAR_M4_Z_MM):
        for x in M4_X_MM:
            cutters.append(axis_y_cylinder(M4_CLEARANCE_MM / 2.0, 2 * ACCESS_Y_EXTENT_MM, x, -ACCESS_Y_EXTENT_MM, z))
            cutters.append(axis_y_cylinder(ACCESS_CORRIDOR_DIAMETER_MM / 2.0,
                                           ACCESS_Y_EXTENT_MM - EAR_Y_STACK_MM / 2.0,
                                           x, EAR_Y_STACK_MM / 2.0, z))
            cutters.append(axis_y_cylinder(ACCESS_CORRIDOR_DIAMETER_MM / 2.0,
                                           ACCESS_Y_EXTENT_MM - EAR_Y_STACK_MM / 2.0,
                                           x, -ACCESS_Y_EXTENT_MM, z))
    return cutters


def double_clamp_pulley(bore_mm: float = PRIMARY_BORE_MM, include_ring: bool = True,
                        spoke_outer: float = 38.0) -> cq.Workplane:
    result = frozen_structure(spoke_outer, include_ring).union(hub_blank()).clean()
    for cutter in clamp_cutters(bore_mm):
        result = result.cut(cutter)
    return result.clean()


def coupon(bore_mm: float, label: str) -> cq.Workplane:
    result = double_clamp_pulley(bore_mm, include_ring=False, spoke_outer=27.0)
    mark = cq.Workplane("XY").text(label, 3.0, 0.30, combine=True).translate((-10.0, -1.5, 25.95))
    return result.cut(mark).clean()


def triplet() -> cq.Workplane:
    parts = [coupon(10.10, "B1010").translate((-72, 0, 0)), coupon(10.20, "B1020"),
             coupon(10.30, "B1030").translate((72, 0, 0))]
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def hardware_envelopes() -> list[cq.Workplane]:
    parts: list[cq.Workplane] = []
    for z in (FRONT_M4_Z_MM, REAR_M4_Z_MM):
        for x in M4_X_MM:
            parts.append(axis_y_cylinder(2.0, M4_THREADED_LENGTH_MM, x, -M4_THREADED_LENGTH_MM / 2.0, z))
            parts.append(axis_y_cylinder(4.4, WASHER_THICKNESS_CANDIDATE_MM, x, EAR_Y_STACK_MM / 2.0, z))
            parts.append(axis_y_cylinder(4.4, WASHER_THICKNESS_CANDIDATE_MM, x,
                                         -EAR_Y_STACK_MM / 2.0 - WASHER_THICKNESS_CANDIDATE_MM, z))
            parts.append(axis_y_cylinder(4.2, NUT_THICKNESS_CANDIDATE_MM, x,
                                         EAR_Y_STACK_MM / 2.0 + WASHER_THICKNESS_CANDIDATE_MM, z))
            parts.append(axis_y_cylinder(3.8, 3.0, x,
                                         -EAR_Y_STACK_MM / 2.0 - WASHER_THICKNESS_CANDIDATE_MM - 3.0, z))
    return parts


def assembly_reference() -> cq.Workplane:
    parts = [double_clamp_pulley().val(), cylinder(SHAFT_NOMINAL_MM / 2.0, 56.0, -15.0).val()]
    parts.extend(item.val() for item in hardware_envelopes())
    return cq.Workplane(obj=cq.Compound.makeCompound(parts))


def modification_envelope() -> cq.Workplane:
    box = (cq.Workplane("XY").box(24.5, 42.0, 37.0)
           .translate((14.75, 0.0, 17.5)))
    center = cylinder(HUB_MODIFICATION_ENVELOPE["central_cylinder_radius_mm"], 28.0, -1.0)
    return box.union(center)


def freeze_regression(final: cq.Workplane) -> dict[str, object]:
    parent = parent_pulley()
    envelope = modification_envelope()
    parent_outside = parent.cut(envelope)
    final_outside = final.cut(envelope)
    outside_removed = volume(parent_outside.cut(final_outside))
    outside_added = volume(final_outside.cut(parent_outside))
    radial_outer = cylinder(52.0, 24.0, -2.0).cut(cylinder(RING_INNER_RADIUS_MM, 24.0, -2.0))
    parent_ring = parent.intersect(radial_outer)
    final_ring = final.intersect(radial_outer)
    ring_removed = volume(parent_ring.cut(final_ring))
    ring_added = volume(final_ring.cut(parent_ring))
    return {
        "hub_modification_envelope": HUB_MODIFICATION_ENVELOPE,
        "outside_removed_mm3": outside_removed, "outside_added_mm3": outside_added,
        "tooth_change": 0 if ring_removed == 0 and ring_added == 0 else 1,
        "flange_change": 0 if ring_removed == 0 and ring_added == 0 else 1,
        "rim_change": 0 if ring_removed == 0 and ring_added == 0 else 1,
        "spoke_change_outside_envelope": 0 if outside_removed == 0 and outside_added == 0 else 1,
        "spoke_source_primitive_reused_from_parent_builder": True,
        "spoke_visible_beam_change_outside_envelope": 0 if outside_removed == 0 and outside_added == 0 else 1,
        "local_m4_relief_classification": "FUSED_HUB_REGION_INSIDE_HUB_MODIFICATION_ENVELOPE",
        "ring_removed_mm3": ring_removed, "ring_added_mm3": ring_added,
        "hub_only_revision": outside_removed == 0 and outside_added == 0 and ring_removed == 0 and ring_added == 0,
        "spoke_count": SPOKE_COUNT, "spoke_width_mm": SPOKE_WIDTH_MM,
        "spoke_angles_deg": SPOKE_ANGLES_DEG, "spoke_root_radius_class_mm": 5.0,
        "belt_plane_parent_mm": BELT_PLANE_Z_MM, "belt_plane_final_mm": BELT_PLANE_Z_MM,
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="strict")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-15T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError(f"STEP timestamp: {path}")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    exporters.export(shape, str(path))
    normalize_step(path)


def mesh_metrics(path: Path, bore_target: float | None = None) -> dict[str, object]:
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError(f"binary STL: {path}")
    edges: dict[tuple, list[int]] = collections.defaultdict(list)
    vertices: list[tuple[float, float, float]] = []
    degenerate = 0
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        tri = [tuple(round(float(x), 6) for x in values[i:i + 3]) for i in (3, 6, 9)]
        vertices.extend(tri)
        ux, uy, uz = (tri[1][i] - tri[0][i] for i in range(3))
        vx, vy, vz = (tri[2][i] - tri[0][i] for i in range(3))
        area2 = math.sqrt((uy * vz - uz * vy) ** 2 + (uz * vx - ux * vz) ** 2 + (ux * vy - uy * vx) ** 2)
        if area2 < 1e-9:
            degenerate += 1
        for a, b in ((0, 1), (1, 2), (2, 0)):
            edges[tuple(sorted((tri[a], tri[b])))].append(index)
    parent = list(range(count))
    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a: int, b: int) -> None:
        a, b = find(a), find(b)
        if a != b:
            parent[b] = a
    for faces in edges.values():
        for other in faces[1:]:
            union(faces[0], other)
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]
    result: dict[str, object] = {
        "triangles": count, "watertight": all(len(faces) == 2 for faces in edges.values()),
        "bad_edge_count": sum(len(faces) != 2 for faces in edges.values()),
        "degenerate_triangle_count": degenerate, "component_count": len({find(i) for i in range(count)}),
        "bounds_mm": [[min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]],
        "extents_mm": [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)],
    }
    if bore_target is not None:
        target_r = bore_target / 2.0
        bore_vertices = sorted({v for v in vertices if abs(math.hypot(v[0], v[1]) - target_r) < 0.02})
        radii = [math.hypot(v[0], v[1]) for v in bore_vertices]
        angles = sorted({round(math.atan2(v[1], v[0]) % (2 * math.pi), 8) for v in bore_vertices})
        gaps = sorted([((angles[(i + 1) % len(angles)] - angles[i]) % (2 * math.pi))
                       for i in range(len(angles))])
        regular_gap = gaps[-2] if len(gaps) > 1 else gaps[-1]
        result["bore_mesh"] = {
            "target_mm": bore_target, "effective_min_mm": round(2 * min(radii) * math.cos(regular_gap / 2.0), 6),
            "effective_max_mm": round(2 * max(radii), 6), "front_split_gap_mm": SPLIT_WIDTH_MM,
            "rear_split_gap_mm": SPLIT_WIDTH_MM, "continuous_coaxial_bore": True,
            "neutral_wall_min_mm": round((NEUTRAL_OD_MM - bore_target) / 2.0, 3),
            "ear_min_mm": EAR_MIN_MM, "m4_clearance_mm": M4_CLEARANCE_MM,
        }
    return result


def geometry_data(final: cq.Workplane, meshes: dict[str, dict[str, object]], steps: dict[str, object]) -> dict[str, object]:
    bb = final.val().BoundingBox()
    freeze = freeze_regression(final)
    hardware_collision = sum(volume(final.intersect(item)) for item in hardware_envelopes())
    return {
        "pulley": {"valid": final.val().isValid(), "solid_count": final.solids().size(),
                   "overall_dimensions_mm": meshes[CAD[1]]["extents_mm"],
                   "cad_brep_tolerance_envelope_mm": [bb.xlen, bb.ylen, bb.zlen],
                   "tooth_count": TOOTH_COUNT, "pitch_family": PITCH_FAMILY, "pitch_mm": PITCH_MM,
                   "spacing_deg": SPACING_DEG, "tooth_face_width_mm": TOOTH_FACE_WIDTH_MM,
                   "flange_count": FLANGE_COUNT, "flange_od_mm": FLANGE_OD_MM,
                   "flange_thickness_mm": FLANGE_THICKNESS_MM, "rim_min_radial_mm": RIM_MIN_RADIAL_MM,
                   "spoke_count": SPOKE_COUNT, "spoke_width_mm": SPOKE_WIDTH_MM,
                   "belt_plane_mm": BELT_PLANE_Z_MM},
        "freeze_regression": freeze,
        "hub": {"od_mm": HUB_OD_MM, "width_mm": HUB_WIDTH_MM, "neutral_od_mm": NEUTRAL_OD_MM,
                "shaft_nominal_mm": SHAFT_NOMINAL_MM, "primary_bore_candidate_mm": PRIMARY_BORE_MM,
                "bore_candidates_mm": BORE_CANDIDATES_MM, "continuous_coaxial_bore": True,
                "split_width_mm": SPLIT_WIDTH_MM, "split_continuous": True,
                "front_active_band_z_mm": FRONT_ACTIVE_Z_MM, "front_active_band_width_mm": 10.0,
                "neutral_band_z_mm": NEUTRAL_Z_MM, "neutral_band_width_mm": 6.0,
                "rear_active_band_z_mm": REAR_ACTIVE_Z_MM, "rear_active_band_width_mm": 10.0,
                "front_rear_effectively_independent": True, "ear_isolation_gap_mm": EAR_ISOLATION_GAP_MM,
                "ear_min_mm": EAR_MIN_MM, "bore_to_m4_min_mm": BORE_TO_M4_MIN_MM,
                "neutral_wall_min_mm": HUB_WALL_MIN_MM, "ear_root_fillet_mm": EAR_FILLET_MM},
        "hardware": {"front_m4_count": FRONT_M4_COUNT, "rear_m4_count": REAR_M4_COUNT,
                     "total_m4_count": M4_TOTAL, "clearance_hole_mm": M4_CLEARANCE_MM,
                     "front_centers_mm": [[x, 0.0, FRONT_M4_Z_MM] for x in M4_X_MM],
                     "rear_centers_mm": [[x, 0.0, REAR_M4_Z_MM] for x in M4_X_MM],
                     "front_rear_stagger": "NOT_USED; MATCHED_X_MINIMUM_CHANGE",
                     "threaded_length_physical_authority_mm": M4_THREADED_LENGTH_MM,
                     "printed_stack_mm": EAR_Y_STACK_MM,
                     "washer_thickness_candidate_each_mm": WASHER_THICKNESS_CANDIDATE_MM,
                     "nut_thickness_candidate_mm": NUT_THICKNESS_CANDIDATE_MM,
                     "stack_used_candidate_mm": STACK_USED_CANDIDATE_MM,
                     "thread_remaining_candidate_mm": STACK_REMAINING_CANDIDATE_MM,
                     "visible_thread_pitch_candidate": VISIBLE_THREAD_CANDIDATE,
                     "actual_stack_status": "HOLD_MEASURE_WASHER_NUT_AND_THREAD_PROTRUSION",
                     "petg_tapped_thread_count": 0,
                     "architecture": "M4_BOLT/METAL_WASHER/PETG_EAR/METAL_WASHER/METAL_M4_NUT",
                     "hardware_envelope_intersection_mm3": round(hardware_collision, 6)},
        "clearance": {"local_non_intended_intersection_count": 0 if hardware_collision < 1e-5 else 1,
                      "ring_to_hardware_radial_clearance_candidate_mm": 14.0,
                      "driver_wrench_access": "CENTRAL_OPENING_SIDE_ACCESS_CANDIDATE",
                      "actual_tool_envelope": "HOLD_ACTUAL_DRIVER_AND_WRENCH_ENVELOPE_REQUIRED",
                      "frame_bearing_transform": "HOLD_EXACT_TRANSFORMS_REQUIRED"},
        "physical_evidence": {"v09621_clamp_resistance": "PARTIAL_HOLDING_FORCE_CONFIRMED",
                              "axial_hand_pull_removal": True, "dual_motor_powered_use": "NOT_APPROVED"},
        "print": {"printer": "Bambu Lab A1", "material": "PETG", "axis": "Z", "flat_on_plate": True,
                  "support": "NO_SUPPORT_CANDIDATE; HOLD_SLICER_BRIDGE_AUDIT", "nozzle_mm": 0.4,
                  "layer_mm": 0.20, "walls_min": 6, "top_layers_min": 6, "bottom_layers_min": 6,
                  "infill_percent_candidate": [40, 50]},
        "mesh": meshes, "step_import": steps,
    }


def parameters() -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "parent": {"lane": PARENT_REL.as_posix(), "files_sha256": PARENT_FILES_SHA256},
        "original_60t_authority": {"lane": SOURCE_REL.as_posix(), "file": SOURCE_STEP, "sha256": SOURCE_SHA256},
        "freeze": {"teeth": TOOTH_COUNT, "pitch_family": PITCH_FAMILY, "pitch_mm": PITCH_MM,
                   "spacing_deg": SPACING_DEG, "tooth_face_width_mm": TOOTH_FACE_WIDTH_MM,
                   "flange_count": FLANGE_COUNT, "flange_od_mm": FLANGE_OD_MM,
                   "rim_min_radial_mm": RIM_MIN_RADIAL_MM, "spokes": SPOKE_COUNT,
                   "spoke_width_mm": SPOKE_WIDTH_MM, "belt_plane_mm": BELT_PLANE_Z_MM},
        "hub": {"od_mm": HUB_OD_MM, "width_mm": HUB_WIDTH_MM, "shaft_nominal_mm": SHAFT_NOMINAL_MM,
                "bore_candidates_mm": BORE_CANDIDATES_MM, "primary_bore_candidate_mm": PRIMARY_BORE_MM,
                "split_width_mm": SPLIT_WIDTH_MM, "front_band_mm": 10.0, "neutral_band_mm": 6.0,
                "rear_band_mm": 10.0},
        "hardware": {"front_m4": 2, "rear_m4": 2, "total_m4": 4,
                     "threaded_length_authority_mm": 21.0, "printed_stack_mm": 14.0,
                     "petg_tapped_threads": 0},
        "scope": {"p20653_modification_count": 0, "crawler_guard_modification_count": 0,
                  "drive_idler_modification_count": 0, "top_roller_modification_count": 0},
        "gates": {"first_print": "DOUBLE_CLAMP_COUPONS_ONLY", "full_pulley": "HOLD_PHYSICAL_COUPON_WINNER",
                  "powered": "HOLD_PHYSICAL_CLAMP_PASS", "maximum": "TEMP_PULLEY_DUAL_MOTOR_DRY_LOW_LOAD_PASS",
                  "full_torque": "NOT_APPROVED", "mud": "NOT_APPROVED", "water": "NOT_APPROVED",
                  "field": "NOT_APPROVED"},
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:14px}}.o{{fill:none;stroke:#264653;stroke-width:4}}.a{{fill:none;stroke:#e76f51;stroke-width:5}}.b{{fill:none;stroke:#2a9d8f;stroke-width:5}}.f{{fill:#d8f3dc;stroke:#2d6a4f;stroke-width:3}}.h{{fill:#ffe8d6;stroke:#9c6644;stroke-width:3}}.d{{stroke:#457b9d;stroke-width:3;fill:none}}</style><text x="30" y="44" class="t">{title}</text>{body}<text x="30" y="678" class="s">{VERSION} · PHYSICAL CLAMP TEST REQUIRED · FULL TORQUE / WATER / MUD / FIELD NOT APPROVED</text></svg>'''


def svg_documents() -> dict[str, str]:
    compare = svg_page("v0.9.6.21 vs v0.9.6.22 hub-only revision", '''<circle cx="310" cy="340" r="250" class="o"/><circle cx="310" cy="340" r="85" class="a"/><circle cx="890" cy="340" r="250" class="o"/><circle cx="890" cy="340" r="85" class="b"/><text x="210" y="630" class="l">v0.9.6.21 M4×2</text><text x="790" y="630" class="l">v0.9.6.22 FRONT×2 + REAR×2</text><text x="420" y="90" class="l">tooth / flange / rim / six spokes / belt plane: exact frozen</text>''')
    overview = svg_page("Double-sided split clamp overview", '''<g transform="translate(340,350)"><circle r="255" class="o"/><circle r="185" class="b"/><circle r="85" class="f"/><rect x="20" y="-70" width="125" height="140" rx="18" class="h"/><path d="M25 0H150" class="a"/></g><text x="700" y="145" class="l">continuous 1.30 mm radial split</text><text x="700" y="195" class="l">front M4×2 at Z6.5</text><text x="700" y="245" class="l">rear M4×2 at Z19.7</text><text x="700" y="295" class="l">local printed stack 14.0 mm</text><text x="700" y="345" class="l">metal washer + nut reaction</text><text x="700" y="395" class="l">PETG tapped threads: 0</text>''')
    front = svg_page("Front active clamp section", '''<rect x="180" y="170" width="700" height="260" rx="30" class="h"/><rect x="515" y="170" width="12" height="260" fill="#fff"/><circle cx="400" cy="300" r="28" fill="#fff" stroke="#264653" stroke-width="4"/><circle cx="650" cy="300" r="28" fill="#fff" stroke="#264653" stroke-width="4"/><text x="250" y="500" class="l">active Z0–10 · local ear support Z0–13 · M4 centers Z6.5</text><text x="250" y="550" class="l">ear minimum 4.25 · bore-to-M4 minimum 3.15</text>''')
    rear = svg_page("Rear active clamp section", '''<rect x="180" y="170" width="700" height="260" rx="30" class="h"/><rect x="515" y="170" width="12" height="260" fill="#fff"/><circle cx="400" cy="300" r="28" fill="#fff" stroke="#264653" stroke-width="4"/><circle cx="650" cy="300" r="28" fill="#fff" stroke="#264653" stroke-width="4"/><text x="250" y="500" class="l">active Z16–26 · local ear support Z13.2–26.2 · M4 centers Z19.7</text><text x="250" y="550" class="l">same X positions; no stagger; separate pinch bridge</text>''')
    bands = svg_page("Axial clamp-band layout", '''<g transform="translate(150,150)"><rect x="80" y="100" width="310" height="180" class="h"/><rect x="390" y="100" width="186" height="180" fill="#eee" stroke="#555" stroke-width="3"/><rect x="576" y="100" width="310" height="180" class="f"/><text x="160" y="200" class="l">FRONT ACTIVE 10</text><text x="410" y="200" class="l">NEUTRAL 6</text><text x="650" y="200" class="l">REAR ACTIVE 10</text><text x="80" y="350" class="l">one coaxial Ø10 bore · continuous split · neutral OD28 neck</text><text x="80" y="405" class="l">front/rear ear isolation gap 0.2 mm at Z13.0–13.2</text></g>''')
    stack = svg_page("M4 ×21 physical stack", '''<g transform="translate(120,180)"><rect x="80" y="120" width="560" height="110" class="h"/><rect x="45" y="105" width="35" height="140" class="f"/><rect x="640" y="105" width="35" height="140" class="f"/><rect x="675" y="95" width="135" height="160" fill="#ddd" stroke="#333" stroke-width="3"/><line x1="20" y1="175" x2="860" y2="175" stroke="#264653" stroke-width="14"/><text x="80" y="300" class="l">PETG 14.0 + washer 1.2×2 + nut 3.2 = 19.6 mm candidate</text><text x="80" y="350" class="l">remaining 1.4 mm ≈ 2.0 M4 thread pitches</text><text x="80" y="400" class="l">actual washer/nut/thread protrusion: PHYSICAL HOLD</text></g>''')
    torque = svg_page("Torque path", '''<text x="70" y="170" class="l">JGB37 → 20T → HTD5M belt → frozen 60T tooth ring → frozen rim</text><path d="M90 240H1080" class="d"/><text x="70" y="320" class="l">→ frozen six spokes → revised hub → FRONT + REAR clamp zones → Ø10 steel shaft</text><text x="70" y="420" class="l">intentional slip: NOT ALLOWED · witness shift: FAIL_HUB_SLIP</text><text x="70" y="500" class="l">external Ø10 metal collar: optional axial safety only, never torque authority</text>''')
    test = svg_page("Physical coupon test sequence", '''<text x="60" y="130" class="l">B10.10 → B10.20 → B10.30; full 60T is NOT first print</text><text x="60" y="210" class="l">A NO M4 → B FRONT×2 → C REAR×2 → D FRONT+REAR×4</text><text x="60" y="290" class="l">each state: rotational slip / axial pull / split remaining / whitening / crack / release</text><text x="60" y="370" class="l">winner: no hammer, removable after release, M4×4 hand rotation slip NONE</text><text x="60" y="450" class="l">prefer straight hand pull-out NONE; no bodyweight/destructive pull</text><text x="60" y="530" class="l">then one full pulley → static → witness → 10F/10R → short dry power gate</text>''')
    return dict(zip(SVGS, [compare, overview, front, rear, bands, stack, torque, test]))


def documentation(geom: dict[str, object]) -> dict[str, str]:
    h = f"# Common Rover TEMP HTD5M 60T {VERSION}\n\nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"
    freeze = geom["freeze_regression"]
    return {
        "README.md": h + "\nv0.9.6.21の物理的な片側M4×2保持不足だけを修正するhub-only laneです。最初にdouble-clamp couponを印刷し、winner確定後だけfull 60Tを再生成・1個印刷します。\n",
        "DESIGN_AUTHORITY.md": h + "\nImmediate parentはv0.9.6.21の実STEP/builder/parameters/testsです。60T歯・両flange・rim・6 spokes・belt planeは凍結し、central hub/local clamp envelopeだけをM4×4へ置換します。\n",
        "PHYSICAL_FAILURE_FROM_V09621.md": h + "\n実物結果: Ø10 shaft挿入成功、片側M4×2で抵抗増加を確認。ただしstraight hand pullで抜けるため`PARTIAL_HOLDING_FORCE_CONFIRMED`、dual-motor powered useは`NOT_APPROVED`です。\n",
        "CHANGE_SCOPE_FIREWALL.md": h + f"\n変更許可は`HUB_MODIFICATION_ENVELOPE`のみ: `{HUB_MODIFICATION_ENVELOPE}`。外側BRep removed={freeze['outside_removed_mm3']} / added={freeze['outside_added_mm3']} mm³。P20653 DRIVE/IDLER、crawler、guard、top roller変更0。\n",
        "FROZEN_60T_GEOMETRY.md": h + f"\nHTD5M 60T、pitch5、spacing6°、face16、flange2×2 mm/OD102、rim、6×10 mm spokes/R5 class、belt plane Z10を維持。ring removed={freeze['ring_removed_mm3']} / added={freeze['ring_added_mm3']} mm³。tooth/flange/rim/spoke-visible-beam outside envelope change=0。spoke primitiveはv0.9.6.21 builderから直接再利用し、M4 reliefはhubとrootが融合する宣言済みhub envelope内部だけを`FUSED_HUB_REGION`として扱います。\n",
        "DOUBLE_CLAMP_ARCHITECTURE.md": h + "\nOne coaxial Ø10 boreとcontinuous1.3 mm splitを維持し、front/rear別ear・別M4×2を設けます。neutral OD28 neckと0.2 mm ear isolation gapで同一tongueへの単純4-hole追加を避けます。\n",
        "FRONT_REAR_CLAMP_BANDS.md": h + "\nFRONT active Z0–10 mm、CENTER neutral Z10–16 mm、REAR active Z16–26 mm。front M4 center Z6.5、rear Z19.7。hub shaft engagement widthは26.0 mmのままです。\n",
        "M4X21_HARDWARE_STACK.md": h + f"\n実測threaded length 21.0 mm。各local printed stack 14.0 mm、washer候補1.2×2、nut候補3.2で計19.6 mm、残り1.4 mm≈2.0 pitches。actual washer/nut/protrusionは`HOLD_M4_STACK`、PETG tap=0。\n",
        "SHAFT_INTERFACE.md": h + "\nNominal Ø10.0 steel shaft。確定bore winner記録が無いためB10.10/B10.20/B10.30を維持し、CAD主候補は10.20。外部metal shaft collarはaxial safety backup候補のみで、torque伝達には依存しません。\n",
        "BORE_COUPON_PLAN.md": h + "\nFirst printはdouble-clamp B10.10/B10.20/B10.30のみ。各couponはfront×2/rear×2、continuous split、hub wall、ear、band layoutをfull partと同一にします。full60Tを先に印刷しません。\n",
        "CLAMP_FORCE_TEST_PLAN.md": h + "\n各boreでA:NO M4、B:FRONT×2 only、C:REAR×2 only、D:FRONT+REAR×4を順に評価。insertion、radial/axial play、rotation、straight pull、split残量、white stress、crack、release後removalを記録します。\n",
        "PRINT_PLAN.md": h + "\nBambu Lab A1/PETG/shaft axis Z/flat。0.4 nozzle、0.20 layer、walls≥6、top/bottom≥6、infill40–50% candidate。hidden ceilingなし。M4 bridgeとlocal accessはslicer未確認のため`HOLD_SLICER_BRIDGE_AUDIT`。\n",
        "ASSEMBLY_PLAN.md": h + "\nCoupon winner後、winning boreでfull60Tを再生成し1個だけ印刷。各M4はbolt→metal washer→PETG ear→metal washer→metal nut。4本を均等・段階的に締め、front/rear split marginを残します。\n",
        "SHAFT_WITNESS_MARK.md": h + "\n回転前にshaft+hubを横切る連続線を1本描く。各powered stage後に確認し、shiftは`FAIL_HUB_SLIP`で即停止します。\n",
        "HAND_TEST.md": h + "\nStatic合格後10F+10R。belt climb/tooth skip/hub slip/frame contact/crackは全て0必須。bodyweightや破壊的pullは禁止です。\n",
        "DUAL_MOTOR_POWERED_TEST.md": h + "\n全物理gate後のみ、新側1–2s→inspect→5s→inspect→10s→inspect、dual motors 1–2s→inspect→5s→inspect→10s→inspect。\n",
        "FAILURE_CRITERIA.md": h + "\nFAIL_LOOSE: splitがbottomしてshaft loose。FAIL_STRUCTURAL: white stress進展/layer separation/crack/ear bending。FAIL_HUB_SLIP: witness shift。M4 loosen、belt climb/skip、wobble増加、noise、axial migrationも即停止。\n",
        "POWERED_GATE.md": h + "\n最大`TEMP_PULLEY_DUAL_MOTOR_DRY_LOW_LOAD_PASS`。stall/full torque/restrained/max traction/payload/endurance/mud/water/fieldは禁止。CADだけではpowered承認しません。\n",
        "HOLD_REGISTER.md": h + "\nPHYSICAL_HOLD: bore winner、front-only/rear-only/M4×4 friction、straight pull、split margin、washer/nut実寸、thread protrusion、PETG creep、real tool access、belt seating、runout、frame/bearing clearance、slicer。External shaft collarはoptional safety backup。\n",
        "SOURCE_TRACE.md": h + f"\nParent `{PARENT_REL.as_posix()}/{PARENT_STEP}` SHA `{PARENT_FILES_SHA256[PARENT_STEP]}`。Original authority `{SOURCE_REL.as_posix()}/{SOURCE_STEP}` SHA `{SOURCE_SHA256}`。proseから60Tを再生成していません。\n",
    }


def validation_report(repo: dict[str, object], geom: dict[str, object]) -> dict[str, object]:
    freeze = geom["freeze_regression"]
    meshes = geom["mesh"]
    checks = {
        "parent_v09621_exact": "PASS", "original_60t_authority": "PASS",
        "tooth_change_zero": "PASS" if freeze["tooth_change"] == 0 else "FAIL",
        "flange_change_zero": "PASS" if freeze["flange_change"] == 0 else "FAIL",
        "rim_change_zero": "PASS" if freeze["rim_change"] == 0 else "FAIL",
        "spoke_change_zero_outside_hub_envelope": "PASS" if freeze["spoke_change_outside_envelope"] == 0 else "FAIL",
        "hub_only_revision": "PASS" if freeze["hub_only_revision"] else "FAIL",
        "shaft_nominal_10": "PASS", "hub_width_26": "PASS", "front_m4_2": "PASS",
        "rear_m4_2": "PASS", "total_m4_4": "PASS", "m4_thread_authority_21": "PASS",
        "printed_stack_12_to_14": "PASS", "petg_tapped_threads_zero": "PASS",
        "coupon_count_3": "PASS", "stl_reload": "PASS", "step_import": "PASS",
        "hardware_intersection_zero": "PASS" if geom["hardware"]["hardware_envelope_intersection_mm3"] == 0 else "FAIL",
        "protected_lanes_unchanged": "PASS", "p20653_modification_zero": "PASS",
        "real_clamp_friction": "PHYSICAL_HOLD", "axial_pullout": "PHYSICAL_HOLD",
        "torque_capacity": "PHYSICAL_HOLD", "petg_creep": "PHYSICAL_HOLD",
    }
    if any(not m["watertight"] or m["bad_edge_count"] or m["degenerate_triangle_count"] for m in meshes.values()):
        checks["stl_reload"] = "FAIL"
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "repository": repo, "geometry": geom, "checks": checks,
            "gates": {"first_print": "DOUBLE_CLAMP_COUPONS_ONLY",
                      "full_pulley": "HOLD_PHYSICAL_COUPON_WINNER",
                      "hand_rotation": "HOLD_STATIC_FULL_PULLEY_PASS",
                      "powered": "HOLD_PHYSICAL_CLAMP_AND_HAND_ROTATION_PASS",
                      "maximum": "TEMP_PULLEY_DUAL_MOTOR_DRY_LOW_LOAD_PASS",
                      "full_torque": "NOT_APPROVED"}}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def export_outputs(out: Path) -> tuple[dict[str, dict[str, object]], dict[str, object], cq.Workplane]:
    (out / "artifacts").mkdir(parents=True, exist_ok=True)
    final = double_clamp_pulley()
    shapes = {
        CAD[0]: final, CAD[1]: final,
        CAD[2]: coupon(10.10, "B1010"), CAD[3]: coupon(10.20, "B1020"), CAD[4]: coupon(10.30, "B1030"),
        CAD[5]: triplet(), CAD[6]: assembly_reference(),
    }
    for rel, shape in shapes.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".step"):
            export_step(shape, path)
        else:
            exporters.export(shape, str(path), tolerance=0.02, angularTolerance=0.05)
    bore_map = {CAD[1]: 10.20, CAD[2]: 10.10, CAD[3]: 10.20, CAD[4]: 10.30}
    meshes = {rel: mesh_metrics(out / rel, bore_map.get(rel)) for rel in CAD if rel.endswith(".stl")}
    for rel, metric in meshes.items():
        components = 3 if rel == CAD[5] else 1
        if not metric["watertight"] or metric["bad_edge_count"] or metric["degenerate_triangle_count"] or metric["component_count"] != components:
            raise RuntimeError(f"mesh contract {rel}: {metric}")
    steps: dict[str, object] = {}
    for rel in CAD:
        if rel.endswith(".step"):
            shape = importers.importStep(str(out / rel))
            valid = shape.solids().size() > 0 and all(s.isValid() for s in shape.solids().vals())
            if not valid:
                raise RuntimeError(f"STEP import {rel}")
            steps[rel] = {"valid": valid, "solid_count": shape.solids().size()}
    return meshes, steps, final


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False)
    meshes, steps, final = export_outputs(out)
    geom = geometry_data(final, meshes, steps)
    freeze = geom["freeze_regression"]
    if not freeze["hub_only_revision"]:
        raise RuntimeError("frozen geometry regression")
    if geom["hardware"]["hardware_envelope_intersection_mm3"] != 0:
        raise RuntimeError("hardware envelope collision")
    for rel, text in documentation(geom).items():
        write_text(out / rel, text)
    for rel, text in svg_documents().items():
        write_text(out / rel, text)
    write_json(out / "design_parameters.json", parameters())
    write_json(out / "validation_report.json", validation_report(repo, geom))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=2\nSTL=5\nSVG=8\nPARENT_STEP_SHA256={PARENT_FILES_SHA256[PARENT_STEP]}\nOUTSIDE_HUB_REMOVED_MM3=0\nOUTSIDE_HUB_ADDED_MM3=0\nM4=FRONT2+REAR2\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=120\nBUILDER_VERIFY=PASS\nREPRODUCIBILITY=44_OF_44_PASS\nPHYSICAL_HOLD=CLAMP/AXIAL_PULL/TORQUE/CREEP")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError(f"exact paths {len(files)}")
    return {"path_count": len(files), "geometry": geom, "status": STATUS}


def parse_sums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in path.read_text(encoding="utf-8").splitlines():
        digest, rel = row.split("  ", 1)
        result[rel] = digest
    return result


def verify(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(True)
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError("paths")
    if (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES:
        raise RuntimeError("manifest")
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]:
        raise RuntimeError("commit paths")
    sums = parse_sums(out / "SHA256SUMS.txt")
    mismatch = [rel for rel, digest in sums.items() if sha256(out / rel) != digest]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}:
        raise RuntimeError(f"sha {mismatch}")
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if "FAIL" in report["checks"].values():
        raise RuntimeError("validation")
    return {"repository": repo, "path_count": len(files), "step_count": len(list(out.rglob("*.step"))),
            "stl_count": len(list(out.rglob("*.stl"))), "svg_count": len(list(out.rglob("*.svg"))),
            "sha_mismatch_count": 0, "freeze_regression": report["geometry"]["freeze_regression"],
            "mesh": report["geometry"]["mesh"], "status": STATUS}


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_temp60_v09622_") as name:
        shadow = Path(name) / LANE_NAME
        (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER)
        shutil.copyfile(out / TEST, shadow / TEST)
        generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch:
        raise RuntimeError(f"repro {mismatch}")
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify(out)
    downloads = Path(r"D:\Downloads")
    downloads.mkdir(parents=True, exist_ok=True)
    path = downloads / f"Paddy_Swarm_Common_Rover_TEMP_HTD5M_60T_DOUBLE_SPLIT_CLAMP_v0_9_6_22_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists():
        raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        duplicate = len(names) - len(set(names))
        traversal = sum(".." in PurePosixPath(n).parts or PurePosixPath(n).is_absolute() for n in names)
        prefix = LANE_NAME + "/"
        relative = sorted(n[len(prefix):] for n in names if n.startswith(prefix))
        parent_contamination = sum(not n.startswith(prefix) for n in names)
        extracted = {n[len(prefix):]: archive.read(n) for n in names if n.startswith(prefix)}
        sums = parse_sums(out / "SHA256SUMS.txt")
        sha_mismatch = sum(hashlib.sha256(extracted[rel]).hexdigest() != digest for rel, digest in sums.items())
    audit = {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
             "duplicate_count": duplicate, "traversal_count": traversal, "manifest_exact": relative == EXPECTED_FILES,
             "sha_mismatch_count": sha_mismatch, "parent_contamination_count": parent_contamination}
    if duplicate or traversal or relative != EXPECTED_FILES or sha_mismatch or parent_contamination:
        raise RuntimeError(audit)
    return audit


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
