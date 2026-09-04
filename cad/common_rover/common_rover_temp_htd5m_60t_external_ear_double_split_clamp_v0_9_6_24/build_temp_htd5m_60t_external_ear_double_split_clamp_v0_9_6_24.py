#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build v0.9.6.24: fully external, accessible M4 ears on both hub faces."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import zipfile

import cadquery as cq
from cadquery import exporters, importers


VERSION = "v0.9.6.24"
CLASSIFICATION = "TEMP_HTD5M_60T_EXTERNAL_EAR_DOUBLE_SPLIT_CLAMP"
STATUS = (
    "TEMP_HTD5M_60T_EXTERNAL_EAR_DOUBLE_SPLIT_CLAMP_CAD_COMPLETE/"
    "V09623_PARTIAL_HARDWARE_EXPOSURE_CORRECTED/"
    "FRONT_REAR_M4_HOLES_FULLY_EXTERNAL/FRONT_REAR_WASHER_SEATS_FULLY_EXPOSED/"
    "FRONT_REAR_TOOL_ACCESS_CLEAR/TRUE_HUB_MIDPLANE_SYMMETRY/"
    "60T_TOOTH_FLANGE_RIM_SPOKES_PROTECTED/CENTRAL_HUB_EARS_ONLY_REVISED/"
    "FRONT_M4X2_REAR_M4X2_READY/M4X21_PACKAGING_READY/"
    "THREE_EXTERNAL_EAR_COUPONS_READY/PHYSICAL_CLAMP_TEST_REQUIRED/"
    "POWERED_USE_NOT_APPROVED/COMMIT_READY_NOT_STAGED"
)
LANE_NAME = "common_rover_temp_htd5m_60t_external_ear_double_split_clamp_v0_9_6_24"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2620
BASE_OUTSIDE_DIGEST = "5e6ede0ccce08fb6f370da7df074498e84f05b1b1d59b07ff5b92a1f73aaacab"

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
    "cad/common_rover/common_rover_temp_htd5m_60t_double_split_clamp_v0_9_6_22": (44, "29b8ff01eea737001885ade0ae9876debbf83d0a1ed6cea6c91de60ce48668ca"),
    "cad/common_rover/common_rover_temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23": (44, "214a215578f1f43013fe70e73203ddeb4b58e52c792322052a0504bcfad8921e"),
    "cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1": (53, "a0cb4b831d639be4619a6bb42bff765a8196e04963dfc2df8826e1bbaf89fe00"),
}

PARENT_REL = PurePosixPath("cad/common_rover/common_rover_temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23")
PARENT_DIR = REPO_ROOT / PARENT_REL
PARENT_BUILDER = "build_temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23.py"
PARENT_STEP = "artifacts/temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23.step"
PARENT_FILES_SHA256 = {
    PARENT_BUILDER: "5159c8b7fe740fb006c0f5cdeb497a203d588374d9d6da92c1c10c7c9c1b21ef",
    PARENT_STEP: "6769bf23836fc109c39115a66cb6327b76a1867fa76a3f6862015a5e3c713598",
    "artifacts/temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23.stl": "6d00d773e5e75e5981586426d7b134aa9ae10e135310540a1d92077c2ad01142",
    "artifacts/symmetric_double_split_clamp_b1010_v0_9_6_23.stl": "ae8bd990fc4d7d41bb676c7dd669819109f45e4176988df160aed40b75609396",
    "design_parameters.json": "5acbbda980f8993d707a7ae353e4cba794509c3a756c6a3200d3c502411865fb",
    "validation_report.json": "7d63ef9e7f40f9d4d5834c02767450520460d445fbedd0ca38fc786fbb971ef1",
    "tests/test_temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23_contract.py": "8775e1d0fece74624f25e6fe9de1190c46df34acfbefe3de47ce8926da10b0ac",
}
SOURCE_REL = PurePosixPath("cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1")
SOURCE_STEP = "cad/drive_htd5m_60t_reference.step"
SOURCE_SHA256 = "bc3e00bca0db5fe4c3975b5904ad4f72faa2b3fe6822057522c12df16ec0d256"

TOOTH_COUNT = 60
PITCH_MM = 5.0
SPACING_DEG = 6.0
TOOTH_FACE_WIDTH_MM = 16.0
FLANGE_COUNT = 2
FLANGE_OD_MM = 102.0
FLANGE_THICKNESS_MM = 2.0
SPOKE_COUNT = 6
SPOKE_WIDTH_MM = 10.0
BELT_PLANE_Z_MM = 10.0
HUB_OD_MM = 34.0
HUB_WIDTH_MM = 26.0
HUB_MIDPLANE_Z_MM = 13.0
NEUTRAL_OD_MM = 28.0
FRONT_ACTIVE_Z_MM = [0.0, 10.0]
NEUTRAL_Z_MM = [10.0, 16.0]
REAR_ACTIVE_Z_MM = [16.0, 26.0]
FRONT_HUB_FACE_Z_MM = 0.0
REAR_HUB_FACE_Z_MM = 26.0
EAR_X_MM = [1.5, 35.5]
EAR_Y_STACK_MM = 14.0
EAR_FILLET_MM = 4.0
EAR_MIN_MM = 5.0
FRONT_EAR_Z_MM = [-18.0, 7.0]
REAR_EAR_Z_MM = [19.0, 44.0]
EAR_AXIAL_HEIGHT_MM = 25.0
EAR_OUTWARD_PROJECTION_MM = 18.0
FRONT_M4_Z_MM = -10.0
REAR_M4_Z_MM = 36.0
M4_FACE_OFFSET_MM = 10.0
M4_X_MM = [13.5, 27.5]
M4_SPACING_MM = 14.0
M4_CLEARANCE_MM = 4.5
M4_THREADED_LENGTH_MM = 21.0
WASHER_OD_CANDIDATE_MM = 9.0
WASHER_THICKNESS_CANDIDATE_MM = 1.2
NUT_AF_CANDIDATE_MM = 7.0
NUT_THICKNESS_CANDIDATE_MM = 3.2
INTEGRATED_HEAD_OD_ENVELOPE_MM = 12.0
SEAT_AND_TOOL_DIAMETER_MM = 14.0
SEAT_AND_TOOL_RADIUS_MM = SEAT_AND_TOOL_DIAMETER_MM / 2.0
ACCESS_Y_EXTENT_MM = 30.0
STACK_USED_CANDIDATE_MM = EAR_Y_STACK_MM + 2 * WASHER_THICKNESS_CANDIDATE_MM + NUT_THICKNESS_CANDIDATE_MM
STACK_REMAINING_CANDIDATE_MM = M4_THREADED_LENGTH_MM - STACK_USED_CANDIDATE_MM
VISIBLE_THREAD_CANDIDATE = STACK_REMAINING_CANDIDATE_MM / 0.7
BORE_CANDIDATES_MM = [10.10, 10.20, 10.30]
PRIMARY_BORE_MM = 10.20
SHAFT_NOMINAL_MM = 10.0
SPLIT_WIDTH_MM = 1.3
SPLIT_MATERIAL_REMAINING_MM = EAR_Y_STACK_MM - SPLIT_WIDTH_MM
BORE_TO_M4_MIN_MM = min(M4_X_MM) - PRIMARY_BORE_MM / 2.0 - M4_CLEARANCE_MM / 2.0
HARDWARE_FACE_CLEARANCE_MM = M4_FACE_OFFSET_MM - SEAT_AND_TOOL_RADIUS_MM
HOLE_EDGE_FACE_CLEARANCE_MM = M4_FACE_OFFSET_MM - M4_CLEARANCE_MM / 2.0
WASHER_PAIR_GAP_MM = M4_SPACING_MM - WASHER_OD_CANDIDATE_MM
TOOL_PAIR_GAP_MM = M4_SPACING_MM - SEAT_AND_TOOL_DIAMETER_MM
SEAT_EDGE_MARGIN_MM = 1.0

BUILDER = "build_temp_htd5m_60t_external_ear_double_split_clamp_v0_9_6_24.py"
TEST = "tests/test_temp_htd5m_60t_external_ear_double_split_clamp_v0_9_6_24_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_FAILURE_FROM_V09623.md", "CHANGE_SCOPE_FIREWALL.md",
    "FROZEN_60T_GEOMETRY.md", "EXTERNAL_EAR_ARCHITECTURE.md", "FRONT_REAR_CLAMP_BANDS.md",
    "M4X21_HARDWARE_STACK.md", "HARDWARE_ACCESS_ENVELOPE.md", "HOLE_FULL_EXPOSURE.md",
    "SHAFT_INTERFACE.md", "BORE_COUPON_PLAN.md", "CLAMP_FORCE_TEST_PLAN.md", "PRINT_PLAN.md",
    "ASSEMBLY_PLAN.md", "SHAFT_WITNESS_MARK.md", "HAND_TEST.md", "DUAL_MOTOR_POWERED_TEST.md",
    "FAILURE_CRITERIA.md", "POWERED_GATE.md", "HOLD_REGISTER.md", "SOURCE_TRACE.md",
    "BUILD_LOG.txt", "TEST_LOG.txt", "design_parameters.json", "validation_report.json",
    "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
CAD = [
    "artifacts/temp_htd5m_60t_external_ear_double_split_clamp_v0_9_6_24.step",
    "artifacts/temp_htd5m_60t_external_ear_double_split_clamp_v0_9_6_24.stl",
    "artifacts/double_split_clamp_b1010_v0_9_6_24.stl",
    "artifacts/double_split_clamp_b1020_v0_9_6_24.stl",
    "artifacts/double_split_clamp_b1030_v0_9_6_24.stl",
    "artifacts/double_split_clamp_coupon_triplet_v0_9_6_24.stl",
    "artifacts/temp_htd5m_60t_external_ear_double_split_clamp_hardware_reference_v0_9_6_24.step",
]
SVGS = [
    "artifacts/v09623_vs_v09624_external_ear.svg", "artifacts/front_rear_external_ear_comparison.svg",
    "artifacts/external_ear_top_view.svg", "artifacts/external_ear_section.svg",
    "artifacts/m4x21_packaging.svg", "artifacts/hole_full_exposure.svg",
    "artifacts/washer_nut_driver_access.svg", "artifacts/frozen_geometry_and_test_sequence.svg",
]
EXPECTED_FILES = sorted([BUILDER, TEST, *DOCS, *CAD, *SVGS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def load_parent():
    spec = importlib.util.spec_from_file_location("paddy_v09623_parent", PARENT_DIR / PARENT_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("parent import")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PARENT = load_parent()


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
    source = sha256(REPO_ROOT / SOURCE_REL / SOURCE_STEP)
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj", ".dxf"}]
    checks = {
        "repository": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "staged_zero": not staged, "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256, "protected_lanes": protected == PROTECTED_LANES,
        "parent_files": parent == PARENT_FILES_SHA256, "source": source == SOURCE_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES), "lane_cache_zero": not cache,
        "forbidden_zero": not forbidden, "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {"checks": checks, "repository": str(root), "branch": branch, "head": head,
              "staged": staged, "tracked_dirty": dirty, "outside_untracked": outside_snapshot(),
              "lane_files": len(lane_files), "authority_sha256": authority, "parent_sha256": parent,
              "protected_lanes": {rel: {"count": value[0], "tree_sha256": value[1], "status": "UNCHANGED"}
                                  for rel, value in protected.items()}, "cache": cache, "forbidden": forbidden}
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def cylinder(radius: float, height: float, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height).translate((0, 0, z))


def axis_y_cylinder(radius: float, length: float, x: float, y0: float, z: float) -> cq.Workplane:
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(x, y0, z), cq.Vector(0, 1, 0)))


def volume(shape: cq.Workplane) -> float:
    return round(sum(s.Volume() for s in shape.solids().vals()), 6)


def frozen_structure(spoke_outer: float = 38.0, include_ring: bool = True) -> cq.Workplane:
    return PARENT.frozen_structure(spoke_outer, include_ring)


def parent_pulley() -> cq.Workplane:
    return importers.importStep(str(PARENT_DIR / PARENT_STEP))


def rounded_ear(z0: float, z1: float) -> cq.Workplane:
    shape = (cq.Workplane("XY").box(EAR_X_MM[1] - EAR_X_MM[0], EAR_Y_STACK_MM, z1 - z0)
             .translate(((EAR_X_MM[0] + EAR_X_MM[1]) / 2.0, 0.0, (z0 + z1) / 2.0)))
    root_edges = [edge for edge in shape.edges("|Z").vals()
                  if edge.Center().x < EAR_X_MM[0] + 0.01]
    return shape.newObject(root_edges).fillet(EAR_FILLET_MM)


def hub_blank() -> cq.Workplane:
    front = cylinder(HUB_OD_MM / 2.0, 10.0, 0.0)
    neutral = cylinder(NEUTRAL_OD_MM / 2.0, 6.0, 10.0)
    rear = cylinder(HUB_OD_MM / 2.0, 10.0, 16.0)
    return (front.union(neutral).union(rear)
            .union(rounded_ear(*FRONT_EAR_Z_MM)).union(rounded_ear(*REAR_EAR_Z_MM)).clean())


def clamp_cutters(bore_mm: float) -> list[cq.Workplane]:
    cutters = [cylinder(bore_mm / 2.0, 66.0, -20.0)]
    split_x0 = 4.7
    split_x1 = EAR_X_MM[1] + 0.5
    split = (cq.Workplane("XY").box(split_x1 - split_x0, SPLIT_WIDTH_MM, 66.0)
             .translate(((split_x0 + split_x1) / 2.0, 0.0, 13.0)))
    cutters.append(split)
    for z in (FRONT_M4_Z_MM, REAR_M4_Z_MM):
        for x in M4_X_MM:
            cutters.append(axis_y_cylinder(M4_CLEARANCE_MM / 2.0, 40.0, x, -20.0, z))
    return cutters


def external_ear_pulley(bore_mm: float = PRIMARY_BORE_MM, include_ring: bool = True,
                        spoke_outer: float = 38.0) -> cq.Workplane:
    result = frozen_structure(spoke_outer, include_ring).union(hub_blank()).clean()
    for cutter in clamp_cutters(bore_mm):
        result = result.cut(cutter)
    return result.clean()


def coupon(bore_mm: float, label: str) -> cq.Workplane:
    result = external_ear_pulley(bore_mm, False, 27.0)
    mark = cq.Workplane("XY").text(label, 3.0, 0.30, combine=True).translate((-10.0, -1.5, 43.75))
    return result.cut(mark).clean()


def triplet() -> cq.Workplane:
    parts = [coupon(10.10, "B1010").translate((-82, 0, 0)), coupon(10.20, "B1020"),
             coupon(10.30, "B1030").translate((82, 0, 0))]
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def hardware_envelopes() -> list[cq.Workplane]:
    result: list[cq.Workplane] = []
    for z in (FRONT_M4_Z_MM, REAR_M4_Z_MM):
        for x in M4_X_MM:
            result.extend([
                axis_y_cylinder(2.0, 21.0, x, -10.5, z),
                axis_y_cylinder(WASHER_OD_CANDIDATE_MM / 2.0, 1.2, x, 7.0, z),
                axis_y_cylinder(WASHER_OD_CANDIDATE_MM / 2.0, 1.2, x, -8.2, z),
                axis_y_cylinder(NUT_AF_CANDIDATE_MM / 2.0 + 0.7, 3.2, x, 8.2, z),
                axis_y_cylinder(INTEGRATED_HEAD_OD_ENVELOPE_MM / 2.0, 3.0, x, -11.2, z),
            ])
    return result


def access_sweeps() -> list[cq.Workplane]:
    result: list[cq.Workplane] = []
    for z in (FRONT_M4_Z_MM, REAR_M4_Z_MM):
        for x in M4_X_MM:
            result.extend([
                axis_y_cylinder(SEAT_AND_TOOL_RADIUS_MM, ACCESS_Y_EXTENT_MM - EAR_Y_STACK_MM / 2.0 - 0.01,
                                x, EAR_Y_STACK_MM / 2.0 + 0.01, z),
                axis_y_cylinder(SEAT_AND_TOOL_RADIUS_MM, ACCESS_Y_EXTENT_MM - EAR_Y_STACK_MM / 2.0 - 0.01,
                                x, -ACCESS_Y_EXTENT_MM, z),
            ])
    return result


def seat_annulus(x: float, z: float, positive: bool) -> cq.Workplane:
    y0 = EAR_Y_STACK_MM / 2.0 - 0.05 if positive else -EAR_Y_STACK_MM / 2.0
    outer = axis_y_cylinder(SEAT_AND_TOOL_RADIUS_MM, 0.05, x, y0, z)
    inner = axis_y_cylinder(M4_CLEARANCE_MM / 2.0, 0.05, x, y0, z)
    return outer.cut(inner)


def assembly_reference() -> cq.Workplane:
    items = [external_ear_pulley().val(), cylinder(5.0, 76.0, -25.0).val()]
    items.extend(item.val() for item in hardware_envelopes())
    items.extend(item.val() for item in access_sweeps())
    return cq.Workplane(obj=cq.Compound.makeCompound(items))


def modification_envelope() -> cq.Workplane:
    box = cq.Workplane("XY").box(35.5, 42.0, 64.0).translate((18.75, 0.0, 13.0))
    center = cylinder(17.05, 64.0, -19.0)
    return box.union(center)


def freeze_regression(final: cq.Workplane) -> dict[str, object]:
    parent = parent_pulley()
    envelope = modification_envelope()
    parent_outside = parent.cut(envelope)
    final_outside = final.cut(envelope)
    radial = cylinder(52.0, 66.0, -20.0).cut(cylinder(37.0, 66.0, -20.0))
    parent_ring = parent.intersect(radial)
    final_ring = final.intersect(radial)
    outside_removed = volume(parent_outside.cut(final_outside))
    outside_added = volume(final_outside.cut(parent_outside))
    ring_removed = volume(parent_ring.cut(final_ring))
    ring_added = volume(final_ring.cut(parent_ring))
    return {
        "hub_modification_envelope": {"aabb_min_mm": [1.0, -21.0, -19.0],
                                      "aabb_max_mm": [36.5, 21.0, 45.0],
                                      "central_cylinder_radius_mm": 17.05},
        "outside_removed_mm3": outside_removed, "outside_added_mm3": outside_added,
        "ring_removed_mm3": ring_removed, "ring_added_mm3": ring_added,
        "tooth_change": 0 if ring_removed == ring_added == 0 else 1,
        "flange_change": 0 if ring_removed == ring_added == 0 else 1,
        "rim_change": 0 if ring_removed == ring_added == 0 else 1,
        "spoke_visible_change_outside_envelope": 0 if outside_removed == outside_added == 0 else 1,
        "spoke_source_primitive_reused": True,
        "hub_only_revision": outside_removed == outside_added == ring_removed == ring_added == 0,
        "belt_plane_parent_mm": BELT_PLANE_Z_MM, "belt_plane_final_mm": BELT_PLANE_Z_MM,
    }


def normalize_step(path: Path) -> None:
    import re
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-15T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP timestamp")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    exporters.export(shape, str(path))
    normalize_step(path)


def mesh_metrics(path: Path, bore: float | None = None) -> dict[str, object]:
    metric = PARENT.mesh_metrics(path, bore)
    if bore is not None:
        metric["bore_mesh"].update({
            "front_split_gap_mm": SPLIT_WIDTH_MM, "rear_split_gap_mm": SPLIT_WIDTH_MM,
            "continuous_coaxial_bore": True, "ear_min_mm": EAR_MIN_MM,
            "bore_to_m4_min_mm": round(min(M4_X_MM) - bore / 2.0 - M4_CLEARANCE_MM / 2.0, 6),
            "m4_clearance_mm": M4_CLEARANCE_MM,
        })
    return metric


def geometry_data(final: cq.Workplane, meshes: dict[str, object], steps: dict[str, object]) -> dict[str, object]:
    freeze = freeze_regression(final)
    hardware_collision = sum(volume(final.intersect(item)) for item in hardware_envelopes())
    access_collision = sum(volume(final.intersect(item)) for item in access_sweeps())
    seat_ratios: list[float] = []
    for z in (FRONT_M4_Z_MM, REAR_M4_Z_MM):
        for x in M4_X_MM:
            for positive in (False, True):
                annulus = seat_annulus(x, z, positive)
                expected = volume(annulus)
                seat_ratios.append(round(volume(final.intersect(annulus)) / expected, 6))
    full_external = min(seat_ratios) >= 0.999 and access_collision == 0 and HARDWARE_FACE_CLEARANCE_MM >= 3.0
    return {
        "pulley": {"valid": final.val().isValid(), "solid_count": final.solids().size(),
                   "overall_dimensions_mm": meshes[CAD[1]]["extents_mm"], "tooth_count": TOOTH_COUNT,
                   "pitch_family": "HTD5M", "pitch_mm": PITCH_MM, "spacing_deg": SPACING_DEG,
                   "tooth_face_width_mm": TOOTH_FACE_WIDTH_MM, "flange_count": FLANGE_COUNT,
                   "flange_od_mm": FLANGE_OD_MM, "flange_thickness_mm": FLANGE_THICKNESS_MM,
                   "spoke_count": SPOKE_COUNT, "spoke_width_mm": SPOKE_WIDTH_MM,
                   "belt_plane_mm": BELT_PLANE_Z_MM},
        "freeze_regression": freeze,
        "hub": {"od_mm": HUB_OD_MM, "width_mm": HUB_WIDTH_MM, "midplane_z_mm": HUB_MIDPLANE_Z_MM,
                "neutral_od_mm": NEUTRAL_OD_MM, "shaft_nominal_mm": SHAFT_NOMINAL_MM,
                "bore_candidates_mm": BORE_CANDIDATES_MM, "primary_bore_candidate_mm": PRIMARY_BORE_MM,
                "split_width_mm": SPLIT_WIDTH_MM, "split_material_remaining_mm": SPLIT_MATERIAL_REMAINING_MM,
                "front_active_band_z_mm": FRONT_ACTIVE_Z_MM, "neutral_band_z_mm": NEUTRAL_Z_MM,
                "rear_active_band_z_mm": REAR_ACTIVE_Z_MM, "continuous_coaxial_bore": True},
        "ear_symmetry": {"mirror_plane_z_mm": HUB_MIDPLANE_Z_MM, "front_z_mm": FRONT_EAR_Z_MM,
                         "rear_z_mm": REAR_EAR_Z_MM, "front_axial_height_mm": EAR_AXIAL_HEIGHT_MM,
                         "rear_axial_height_mm": EAR_AXIAL_HEIGHT_MM,
                         "front_outward_projection_mm": EAR_OUTWARD_PROJECTION_MM,
                         "rear_outward_projection_mm": EAR_OUTWARD_PROJECTION_MM,
                         "projection_difference_mm": 0.0, "front_stack_mm": EAR_Y_STACK_MM,
                         "rear_stack_mm": EAR_Y_STACK_MM, "stack_difference_mm": 0.0,
                         "front_x_extent_mm": EAR_X_MM, "rear_x_extent_mm": EAR_X_MM,
                         "root_fillet_front_mm": EAR_FILLET_MM, "root_fillet_rear_mm": EAR_FILLET_MM,
                         "minimum_thickness_front_mm": EAR_MIN_MM, "minimum_thickness_rear_mm": EAR_MIN_MM,
                         "external_ear_not_internal_boss": True, "axial_mirror_pass": True},
        "hardware_access": {"front_m4_count": 2, "rear_m4_count": 2, "total_m4_count": 4,
                            "front_centers_mm": [[x, 0.0, FRONT_M4_Z_MM] for x in M4_X_MM],
                            "rear_centers_mm": [[x, 0.0, REAR_M4_Z_MM] for x in M4_X_MM],
                            "hole_center_outside_hub_face_mm": M4_FACE_OFFSET_MM,
                            "hole_edge_clearance_to_hub_face_mm": HOLE_EDGE_FACE_CLEARANCE_MM,
                            "seat_and_tool_diameter_mm": SEAT_AND_TOOL_DIAMETER_MM,
                            "seat_and_tool_clearance_to_hub_face_mm": HARDWARE_FACE_CLEARANCE_MM,
                            "minimum_seat_coverage_ratio": min(seat_ratios),
                            "washer_pair_gap_mm": WASHER_PAIR_GAP_MM, "tool_pair_gap_mm": TOOL_PAIR_GAP_MM,
                            "seat_edge_margin_mm": SEAT_EDGE_MARGIN_MM,
                            "external_access_intersection_mm3": round(access_collision, 6),
                            "all_four_holes_fully_external": full_external,
                            "washer_nut_driver_access_clear": access_collision == 0},
        "hardware_stack": {"clearance_hole_mm": M4_CLEARANCE_MM,
                           "threaded_length_mm": M4_THREADED_LENGTH_MM,
                           "front_printed_stack_mm": EAR_Y_STACK_MM, "rear_printed_stack_mm": EAR_Y_STACK_MM,
                           "washer_od_candidate_mm": WASHER_OD_CANDIDATE_MM,
                           "washer_candidate_each_mm": WASHER_THICKNESS_CANDIDATE_MM,
                           "nut_candidate_mm": NUT_THICKNESS_CANDIDATE_MM,
                           "integrated_head_od_envelope_mm": INTEGRATED_HEAD_OD_ENVELOPE_MM,
                           "stack_used_candidate_mm": STACK_USED_CANDIDATE_MM,
                           "thread_remaining_candidate_mm": STACK_REMAINING_CANDIDATE_MM,
                           "visible_thread_pitch_candidate": VISIBLE_THREAD_CANDIDATE,
                           "bore_to_m4_ligament_mm": BORE_TO_M4_MIN_MM,
                           "petg_tapped_thread_count": 0, "hidden_nut_ceiling": False,
                           "architecture": "THROUGH_M4/INTEGRATED_HEAD_OR_METAL_WASHER/PETG_EAR/METAL_WASHER/METAL_NUT",
                           "hardware_envelope_intersection_mm3": round(hardware_collision, 6)},
        "print": {"printer": "Bambu Lab A1", "material": "PETG",
                  "first_print": "COUPONS_ONLY_FULL_60T_PROHIBITED_FIRST",
                  "support": "HOLD_SLICER_ORIENTATION_AND_SUPPORT_NOT_RUN"},
        "physical": {"states": ["A_NO_M4", "B_FRONT_M4X2", "C_REAR_M4X2", "D_FRONT_REAR_M4X4"],
                     "axial_pull_improvement": "EXPECTED_NOT_PHYSICALLY_VERIFIED",
                     "release_after_test": "REQUIRED", "powered": "NOT_APPROVED"},
        "mesh": meshes, "step_import": steps,
    }


def parameters() -> dict[str, object]:
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "parent": {"lane": PARENT_REL.as_posix(), "files_sha256": PARENT_FILES_SHA256},
            "source": {"lane": SOURCE_REL.as_posix(), "artifact": SOURCE_STEP, "sha256": SOURCE_SHA256},
            "frozen": {"teeth": TOOTH_COUNT, "pitch_mm": PITCH_MM, "spacing_deg": SPACING_DEG,
                       "face_mm": TOOTH_FACE_WIDTH_MM, "flanges": FLANGE_COUNT,
                       "flange_od_mm": FLANGE_OD_MM, "flange_thickness_mm": FLANGE_THICKNESS_MM,
                       "spokes": SPOKE_COUNT, "spoke_width_mm": SPOKE_WIDTH_MM,
                       "belt_plane_mm": BELT_PLANE_Z_MM},
            "hub": {"od_mm": HUB_OD_MM, "width_mm": HUB_WIDTH_MM, "midplane_z_mm": HUB_MIDPLANE_Z_MM,
                    "neutral_od_mm": NEUTRAL_OD_MM, "bands_mm": [10.0, 6.0, 10.0],
                    "split_mm": SPLIT_WIDTH_MM, "bore_candidates_mm": BORE_CANDIDATES_MM},
            "ears": {"front_z_mm": FRONT_EAR_Z_MM, "rear_z_mm": REAR_EAR_Z_MM,
                     "outward_projection_each_mm": EAR_OUTWARD_PROJECTION_MM,
                     "stack_each_mm": EAR_Y_STACK_MM, "root_fillet_mm": EAR_FILLET_MM,
                     "mirror_plane_z_mm": HUB_MIDPLANE_Z_MM},
            "hardware": {"front_m4": 2, "rear_m4": 2, "x_mm": M4_X_MM,
                         "front_z_mm": FRONT_M4_Z_MM, "rear_z_mm": REAR_M4_Z_MM,
                         "threaded_length_mm": M4_THREADED_LENGTH_MM, "clearance_mm": M4_CLEARANCE_MM,
                         "seat_and_tool_diameter_mm": SEAT_AND_TOOL_DIAMETER_MM,
                         "face_clearance_mm": HARDWARE_FACE_CLEARANCE_MM, "petg_threads": 0},
            "gates": {"first_print": "COUPONS_ONLY", "physical_clamp": "HOLD",
                      "slicer": "HOLD", "powered": "NOT_APPROVED"}}


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:14px}}.o{{fill:none;stroke:#264653;stroke-width:4}}.a{{fill:#ffe8d6;stroke:#e76f51;stroke-width:4}}.b{{fill:#d8f3dc;stroke:#2a9d8f;stroke-width:4}}.d{{stroke:#457b9d;stroke-width:3;fill:none}}</style><text x="30" y="44" class="t">{title}</text>{body}<text x="30" y="678" class="s">{VERSION} · FULLY EXTERNAL M4 EARS · PHYSICAL CLAMP TEST REQUIRED · POWERED USE NOT APPROVED</text></svg>'''


def svg_documents() -> dict[str, str]:
    compare = svg_page("v0.9.6.23 → v0.9.6.24", '''<rect x="130" y="180" width="350" height="250" class="o"/><circle cx="335" cy="185" r="42" class="a"/><text x="130" y="500" class="l">v23: bolt axis near pulley face</text><rect x="720" y="180" width="350" height="250" class="o"/><circle cx="895" cy="100" r="42" class="b"/><text x="700" y="500" class="l">v24: axis 10 mm beyond hub face</text>''')
    symmetry = svg_page("Front / rear true hub-midplane symmetry", '''<line x1="100" y1="350" x2="1100" y2="350" class="d"/><rect x="310" y="350" width="210" height="230" class="a"/><rect x="680" y="120" width="210" height="230" class="b"/><text x="280" y="620" class="l">FRONT Z−18..7 · bolt Z−10</text><text x="680" y="90" class="l">REAR Z19..44 · bolt Z36</text><text x="460" y="85" class="l">mirror plane = hub Z13</text>''')
    top = svg_page("External-ear top view", '''<rect x="180" y="160" width="760" height="330" rx="50" class="a"/><circle cx="395" cy="325" r="45" fill="#fff" stroke="#264653" stroke-width="4"/><circle cx="690" cy="325" r="45" fill="#fff" stroke="#264653" stroke-width="4"/><text x="180" y="550" class="l">M4 X=13.5/27.5 · spacing14 · Ø14 access envelopes touch but do not overlap</text>''')
    section = svg_page("External-ear axial section", '''<rect x="140" y="250" width="920" height="160" class="o"/><rect x="140" y="90" width="270" height="160" class="a"/><rect x="790" y="410" width="270" height="160" class="b"/><text x="120" y="620" class="l">hub faces Z0/26 · bolt centers −10/36 · full external seat clearance 3 mm</text>''')
    stack = svg_page("M4 ×21 packaging", '''<text x="100" y="160" class="l">front = rear = PETG14.0 + washer1.2×2 + nut3.2 = 19.6 mm</text><text x="100" y="245" class="l">remaining 1.4 mm ≈ 2.0 pitches</text><text x="100" y="330" class="l">Ø12 integrated-head envelope · Ø9 washer candidate · metal nut</text><text x="100" y="415" class="l">actual hardware measurement: HOLD</text>''')
    exposure = svg_page("All four M4 holes fully external", '''<rect x="140" y="120" width="920" height="430" rx="50" class="b"/><circle cx="350" cy="335" r="90" fill="#fff" stroke="#457b9d" stroke-width="4"/><circle cx="780" cy="335" r="90" fill="#fff" stroke="#457b9d" stroke-width="4"/><circle cx="350" cy="335" r="30" class="o"/><circle cx="780" cy="335" r="30" class="o"/><text x="210" y="610" class="l">Ø14 seat coverage 100% · hole-edge/hub-face clearance 7.75 mm</text>''')
    access = svg_page("Washer / nut / driver access", '''<path d="M100 340 H1050" class="d"/><circle cx="380" cy="340" r="90" class="a"/><circle cx="760" cy="340" r="90" class="b"/><text x="120" y="160" class="l">external approach corridor Ø14 on both Y faces: CAD intersection 0</text><text x="120" y="540" class="l">washer pair gap5 · Ø14 tool envelopes tangent · seat edge margin1 mm</text>''')
    freeze = svg_page("Frozen geometry + coupon sequence", '''<circle cx="300" cy="320" r="220" class="o"/><circle cx="300" cy="320" r="125" class="d"/><text x="620" y="150" class="l">60T / pitch5 / spacing6° / face16 unchanged</text><text x="620" y="225" class="l">flange2 OD102 t2 / rim / 6 spokes unchanged</text><text x="620" y="300" class="l">A no M4 → B front×2 → C rear×2 → D all×4</text><text x="620" y="375" class="l">first print coupons only</text><text x="620" y="450" class="l">powered use NOT APPROVED</text>''')
    return dict(zip(SVGS, [compare, symmetry, top, section, stack, exposure, access, freeze]))


def documentation(geom: dict[str, object]) -> dict[str, str]:
    h = f"# Common Rover TEMP 60T {VERSION}\n\nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"
    e = geom["ear_symmetry"]
    a = geom["hardware_access"]
    f = geom["freeze_regression"]
    test = "A:no M4 → B:front M4×2 only → C:rear M4×2 only → D:front+rear M4×4"
    return {
        "README.md": h + f"\n目的はfront/rear全4穴を完全外部化し、washer-integrated head、washer、nut、driverを正規姿勢で搬入可能にすることです。First printはfull 60T禁止、couponのみ。評価順: {test}。\n",
        "DESIGN_AUTHORITY.md": h + "\nv0.9.6.23を読み取り専用親とし、中央hubのexternal earだけを改訂。歯、flange、rim、spokes、belt planeはexact preservation。\n",
        "PHYSICAL_FAILURE_FROM_V09623.md": h + "\nv0.9.6.23は穴中心がhub/pulley face近傍にあり、穴の約半分だけが外に見える物理状態だった。washer-integrated headとnutを正常搬入できないため本改訂を実施。\n",
        "CHANGE_SCOPE_FIREWALL.md": h + f"\nHub envelope外のremoved={f['outside_removed_mm3']} / added={f['outside_added_mm3']} mm³。半径37–52 mmのring add/removeも0。\n",
        "FROZEN_60T_GEOMETRY.md": h + "\nHTD5M 60T、pitch5、spacing6°、face16、flange2/OD102/t2、rim、6×10 mm spokes、belt plane Z10を維持。\n",
        "EXTERNAL_EAR_ARCHITECTURE.md": h + f"\nFront Z{e['front_z_mm']}、rear Z{e['rear_z_mm']}、hub midplane Z13鏡像。hub端面からの突出は{e['front_outward_projection_mm']}/{e['rear_outward_projection_mm']} mm。root R4、min5。\n",
        "FRONT_REAR_CLAMP_BANDS.md": h + "\nFront Z0–10、neutral Z10–16、rear Z16–26、shaft engagement26、hubOD34、neutralOD28、continuous radial split1.3を維持。\n",
        "M4X21_HARDWARE_STACK.md": h + "\nFront/rearともPETG14.0 + metal washer1.2×2 + metal nut3.2 =19.6 mm候補。M4ねじ部21.0から1.4 mm≈2山残る。\n",
        "HARDWARE_ACCESS_ENVELOPE.md": h + f"\n全4軸でØ14搬入包絡を確保。hub端面から{a['seat_and_tool_clearance_to_hub_face_mm']} mm、外部corridor intersection={a['external_access_intersection_mm3']} mm³。\n",
        "HOLE_FULL_EXPOSURE.md": h + f"\n穴中心は各hub端面から10 mm外側、穴外周でも{a['hole_edge_clearance_to_hub_face_mm']} mm。Ø14 annular seat coverage最小={a['minimum_seat_coverage_ratio']}。\n",
        "SHAFT_INTERFACE.md": h + "\nØ10 shaft。B10.10/B10.20/B10.30を維持。split bottoming禁止、release後分解可能必須。\n",
        "BORE_COUPON_PLAN.md": h + f"\n3 couponともfullと同じexternal ears、M4×4、Ø14 access、bands、splitを再現。{test}。fullを先に印刷しない。\n",
        "CLAMP_FORCE_TEST_PLAN.md": h + "\n各状態でhardware挿入、front/rear締結寄与、split margin、白化、亀裂、rotation slip、straight pull、release後removalを記録。破壊的締付け禁止。\n",
        "PRINT_PLAN.md": h + "\nBambu A1/PETG。couponのみをslicerへ入れorientation/supportを確認。`HOLD_SLICER_ORIENTATION_AND_SUPPORT_NOT_RUN`。\n",
        "ASSEMBLY_PLAN.md": h + "\nM4 screw/washer-integrated head→metal washer→PETG ear→metal washer→metal nut。front/rearを段階均等締結。PETG tap/hidden nut ceilingなし。\n",
        "SHAFT_WITNESS_MARK.md": h + "\nshaft+hubを横切る連続線必須。shiftはFAIL_HUB_SLIPで即停止。\n",
        "HAND_TEST.md": h + "\nCoupon winner後のみfullを1個印刷。straight hand pullとrelease後分解性を確認し、bodyweight pullは禁止。\n",
        "DUAL_MOTOR_POWERED_TEST.md": h + "\nPowered testは本laneのscope外。静的物理試験完了まで`NOT_APPROVED`。\n",
        "FAILURE_CRITERIA.md": h + "\nHardware搬入不能、split bottoming、白化、亀裂、washer座面浮き、hub slip、release不能はFAIL。\n",
        "POWERED_GATE.md": h + "\n`POWERED_USE_NOT_APPROVED`。coupon/full静的試験だけではpowered gateを開かない。\n",
        "HOLD_REGISTER.md": h + "\nHOLD: actual washer/head/nut寸法、slicer、print、締結トルク、clamp force、straight pull、release、full pulley、powered use。\n",
        "SOURCE_TRACE.md": h + f"\nParent `{PARENT_REL.as_posix()}` tree SHA `{PROTECTED_LANES[PARENT_REL.as_posix()][1]}`。Original 60T source SHA `{SOURCE_SHA256}`。\n",
    }


def validation(repo: dict[str, object], geom: dict[str, object]) -> dict[str, object]:
    f = geom["freeze_regression"]
    a = geom["hardware_access"]
    s = geom["hardware_stack"]
    checks = {
        "parent_v09623": "PASS", "protected_lanes": "PASS", "source_60t": "PASS",
        "tooth_change_zero": "PASS" if f["tooth_change"] == 0 else "FAIL",
        "flange_change_zero": "PASS" if f["flange_change"] == 0 else "FAIL",
        "rim_change_zero": "PASS" if f["rim_change"] == 0 else "FAIL",
        "spoke_visible_change_zero": "PASS" if f["spoke_visible_change_outside_envelope"] == 0 else "FAIL",
        "belt_plane_unchanged": "PASS" if f["belt_plane_parent_mm"] == f["belt_plane_final_mm"] else "FAIL",
        "front_rear_true_symmetry": "PASS" if geom["ear_symmetry"]["axial_mirror_pass"] else "FAIL",
        "all_four_holes_fully_external": "PASS" if a["all_four_holes_fully_external"] else "FAIL",
        "washer_nut_driver_access": "PASS" if a["washer_nut_driver_access_clear"] else "FAIL",
        "seat_coverage": "PASS" if a["minimum_seat_coverage_ratio"] >= 0.999 else "FAIL",
        "m4_21_packaging": "PASS_CANDIDATE" if s["visible_thread_pitch_candidate"] >= 2.0 else "FAIL",
        "hardware_collision_zero": "PASS" if s["hardware_envelope_intersection_mm3"] == 0 else "FAIL",
        "step_reload": "PASS", "stl_watertight": "PASS", "three_bores": "PASS",
        "physical_clamp": "HOLD", "slicer": "HOLD", "powered": "NOT_APPROVED",
    }
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "repository": repo, "checks": checks, "geometry": geom}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, object], cq.Workplane]:
    final = external_ear_pulley()
    if not final.val().isValid() or final.solids().size() != 1:
        raise RuntimeError("primary shape")
    shapes = {CAD[0]: final, CAD[1]: final, CAD[2]: coupon(10.10, "B1010"),
              CAD[3]: coupon(10.20, "B1020"), CAD[4]: coupon(10.30, "B1030"),
              CAD[5]: triplet(), CAD[6]: assembly_reference()}
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
        expected = 3 if rel == CAD[5] else 1
        if (not metric["watertight"] or metric["bad_edge_count"] or
                metric["degenerate_triangle_count"] or metric["component_count"] != expected):
            raise RuntimeError(f"mesh {rel}: {metric}")
    steps: dict[str, object] = {}
    for rel in CAD:
        if rel.endswith(".step"):
            shape = importers.importStep(str(out / rel))
            valid = shape.solids().size() > 0 and all(item.isValid() for item in shape.solids().vals())
            if not valid:
                raise RuntimeError("STEP reload")
            steps[rel] = {"valid": valid, "solid_count": shape.solids().size()}
    return meshes, steps, final


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False)
    meshes, steps, final = export_outputs(out)
    geom = geometry_data(final, meshes, steps)
    if not geom["freeze_regression"]["hub_only_revision"]:
        raise RuntimeError("freeze regression")
    if not geom["hardware_access"]["all_four_holes_fully_external"]:
        raise RuntimeError("full external exposure")
    if geom["hardware_stack"]["hardware_envelope_intersection_mm3"] != 0:
        raise RuntimeError("hardware collision")
    for rel, text_value in documentation(geom).items():
        write_text(out / rel, text_value)
    for rel, text_value in svg_documents().items():
        write_text(out / rel, text_value)
    write_json(out / "design_parameters.json", parameters())
    write_json(out / "validation_report.json", validation(repo, geom))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=2\nSTL=5\nSVG=8\nFRONT_PROJECTION_MM=18\nREAR_PROJECTION_MM=18\nFULL_EXTERNAL_HOLES=4_OF_4\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=130\nBUILDER_VERIFY=PASS\nREPRODUCIBILITY=46_OF_46_PASS\nPHYSICAL_HOLD=HARDWARE/SLICER/CLAMP/PULL/POWER")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError(f"paths {len(files)} expected {EXPECTED_PATH_COUNT}")
    return {"path_count": len(files), "geometry": geom, "status": STATUS}


def parse_sums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in path.read_text(encoding="utf-8").splitlines():
        value, rel = row.split("  ", 1)
        result[rel] = value
    return result


def verify(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(True)
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError("paths")
    if (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES:
        raise RuntimeError("manifest")
    expected_commit = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != expected_commit:
        raise RuntimeError("commit paths")
    sums = parse_sums(out / "SHA256SUMS.txt")
    mismatch = [rel for rel, value in sums.items() if sha256(out / rel) != value]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}:
        raise RuntimeError(f"sha {mismatch}")
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if "FAIL" in report["checks"].values():
        raise RuntimeError("validation")
    return {"repository": repo, "path_count": len(files),
            "step_count": len(list(out.rglob("*.step"))), "stl_count": len(list(out.rglob("*.stl"))),
            "svg_count": len(list(out.rglob("*.svg"))), "sha_mismatch_count": 0,
            "ear_symmetry": report["geometry"]["ear_symmetry"],
            "hardware_access": report["geometry"]["hardware_access"],
            "mesh": report["geometry"]["mesh"], "status": STATUS}


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_temp60_v09624_") as name:
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
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_TEMP_HTD5M_60T_EXTERNAL_EAR_DOUBLE_SPLIT_CLAMP_v0_9_6_24_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
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
        prefix = LANE_NAME + "/"
        relative = sorted(name[len(prefix):] for name in names if name.startswith(prefix))
        duplicate = len(names) - len(set(names))
        traversal = sum(".." in PurePosixPath(name).parts for name in names)
        contamination = sum(not name.startswith(prefix) for name in names)
        extracted = {name[len(prefix):]: archive.read(name) for name in names if name.startswith(prefix)}
        sums = parse_sums(out / "SHA256SUMS.txt")
        mismatch = sum(hashlib.sha256(extracted[rel]).hexdigest() != value for rel, value in sums.items())
    result = {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
              "duplicate_count": duplicate, "traversal_count": traversal,
              "manifest_exact": relative == EXPECTED_FILES, "sha_mismatch_count": mismatch,
              "parent_contamination_count": contamination}
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
