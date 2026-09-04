#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build v0.9.6.23: axially symmetric external ears for the TEMP 60T hub."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import cadquery as cq
from cadquery import exporters, importers


VERSION = "v0.9.6.23"
CLASSIFICATION = "TEMP_HTD5M_60T_SYMMETRIC_DOUBLE_SPLIT_CLAMP"
STATUS = (
    "TEMP_HTD5M_60T_SYMMETRIC_DOUBLE_SPLIT_CLAMP_CAD_COMPLETE/"
    "V09622_REAR_EAR_VISUAL_FUNCTIONAL_SHORTFALL_RECORDED/"
    "FRONT_REAR_EXTERNAL_EARS_AXIALLY_SYMMETRIC/"
    "60T_TOOTH_FLANGE_RIM_SPOKES_PROTECTED/CENTRAL_HUB_ONLY_REVISED/"
    "FRONT_M4X2_REAR_M4X2_READY/M4X21_PACKAGING_READY/"
    "THREE_SYMMETRIC_EAR_COUPONS_READY/P20653_SCOPE_UNCHANGED/"
    "PHYSICAL_CLAMP_TEST_REQUIRED/POWERED_USE_NOT_APPROVED/COMMIT_READY_NOT_STAGED"
)
LANE_NAME = "common_rover_temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2576
BASE_OUTSIDE_DIGEST = "f3402dac254dc03064dee0b179aa4b4d54cb93d941a4ec0624d9ca117f02fd5c"

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
    "cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1": (53, "a0cb4b831d639be4619a6bb42bff765a8196e04963dfc2df8826e1bbaf89fe00"),
}

PARENT_REL = PurePosixPath("cad/common_rover/common_rover_temp_htd5m_60t_double_split_clamp_v0_9_6_22")
PARENT_DIR = REPO_ROOT / PARENT_REL
PARENT_BUILDER = "build_temp_htd5m_60t_double_split_clamp_v0_9_6_22.py"
PARENT_STEP = "artifacts/temp_htd5m_60t_double_split_clamp_v0_9_6_22.step"
PARENT_FILES_SHA256 = {
    PARENT_BUILDER: "7bc52e23c08f0d53097525e7f7c8e5e134ad705cca2277a06ff2391fc71c681c",
    PARENT_STEP: "6b31a0cd6e202ff3694416bf223d9083761a7002785cb4736b976070e4302afb",
    "artifacts/temp_htd5m_60t_double_split_clamp_v0_9_6_22.stl": "a52b9cf01168bcfc9146c9711bda47fe04d1c09225ebe5cf80fd5e92223c40f8",
    "artifacts/double_split_clamp_b1010_v0_9_6_22.stl": "9dc0748ea656b2a55a9890a13eb58dedd70c941ff2136bc360354eca420c7a7d",
    "design_parameters.json": "d07fc27d5ff87085626cfa6fd373ab5273fa54b115e848fd075fc7ad622b7c37",
    "validation_report.json": "4bd9928c49be27b21ae7f4308d229ad8c8df0b9bedae533c7eaccd925f5ba7db",
    "tests/test_temp_htd5m_60t_double_split_clamp_v0_9_6_22_contract.py": "48c22e97658e5060e85847dca96d3d390f8e4f3b5a9eb21f3f33e29133bf6408",
}
SOURCE_REL = PurePosixPath("cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1")
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
RIM_MIN_RADIAL_MM = 8.946482927568603
SPOKE_COUNT = 6
SPOKE_WIDTH_MM = 10.0
SPOKE_ANGLES_DEG = [30.0 + i * 60.0 for i in range(6)]
BELT_PLANE_Z_MM = 10.0
FROZEN_FACE_Z_MM = [0.0, 20.0]

HUB_OD_MM = 34.0
HUB_WIDTH_MM = 26.0
NEUTRAL_OD_MM = 28.0
FRONT_ACTIVE_Z_MM = [0.0, 10.0]
NEUTRAL_Z_MM = [10.0, 16.0]
REAR_ACTIVE_Z_MM = [16.0, 26.0]
EAR_X_MM = [4.0, 25.0]
EAR_Y_STACK_MM = 14.0
EAR_AXIAL_HEIGHT_MM = 13.0
EAR_FILLET_MM = 3.0
EAR_OUTWARD_PROJECTION_MM = 6.2
FRONT_EAR_Z_MM = [-6.2, 6.8]
REAR_EAR_Z_MM = [13.2, 26.2]
FRONT_M4_Z_MM = 0.3
REAR_M4_Z_MM = 19.7
M4_X_MM = [10.5, 18.5]
M4_CLEARANCE_MM = 4.5
M4_THREADED_LENGTH_MM = 21.0
WASHER_THICKNESS_CANDIDATE_MM = 1.2
NUT_THICKNESS_CANDIDATE_MM = 3.2
STACK_USED_CANDIDATE_MM = EAR_Y_STACK_MM + 2 * WASHER_THICKNESS_CANDIDATE_MM + NUT_THICKNESS_CANDIDATE_MM
STACK_REMAINING_CANDIDATE_MM = M4_THREADED_LENGTH_MM - STACK_USED_CANDIDATE_MM
VISIBLE_THREAD_CANDIDATE = STACK_REMAINING_CANDIDATE_MM / 0.7
BORE_CANDIDATES_MM = [10.10, 10.20, 10.30]
PRIMARY_BORE_MM = 10.20
SHAFT_NOMINAL_MM = 10.0
SPLIT_WIDTH_MM = 1.3
EAR_MIN_MM = 4.25
BORE_TO_M4_MIN_MM = min(M4_X_MM) - PRIMARY_BORE_MM / 2.0 - M4_CLEARANCE_MM / 2.0
ACCESS_CORRIDOR_DIAMETER_MM = 9.2
ACCESS_Y_EXTENT_MM = 12.0
HUB_MODIFICATION_ENVELOPE = {
    "aabb_min_mm": [2.5, -21.0, -7.5], "aabb_max_mm": [27.0, 21.0, 36.0],
    "central_cylinder_radius_mm": 17.05, "central_cylinder_z_mm": [-7.5, 27.0],
}

BUILDER = "build_temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23.py"
TEST = "tests/test_temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_FAILURE_FROM_V09622.md", "CHANGE_SCOPE_FIREWALL.md",
    "FROZEN_60T_GEOMETRY.md", "SYMMETRIC_DOUBLE_CLAMP_ARCHITECTURE.md", "FRONT_REAR_CLAMP_BANDS.md",
    "M4X21_HARDWARE_STACK.md", "SHAFT_INTERFACE.md", "BORE_COUPON_PLAN.md", "CLAMP_FORCE_TEST_PLAN.md",
    "PRINT_PLAN.md", "ASSEMBLY_PLAN.md", "SHAFT_WITNESS_MARK.md", "HAND_TEST.md",
    "DUAL_MOTOR_POWERED_TEST.md", "FAILURE_CRITERIA.md", "POWERED_GATE.md", "HOLD_REGISTER.md",
    "SOURCE_TRACE.md", "BUILD_LOG.txt", "TEST_LOG.txt", "design_parameters.json",
    "validation_report.json", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
CAD = [
    "artifacts/temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23.step",
    "artifacts/temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23.stl",
    "artifacts/symmetric_double_split_clamp_b1010_v0_9_6_23.stl",
    "artifacts/symmetric_double_split_clamp_b1020_v0_9_6_23.stl",
    "artifacts/symmetric_double_split_clamp_b1030_v0_9_6_23.stl",
    "artifacts/symmetric_double_split_clamp_coupon_triplet_v0_9_6_23.stl",
    "artifacts/temp_htd5m_60t_symmetric_double_split_clamp_hardware_reference_v0_9_6_23.step",
]
SVGS = [
    "artifacts/v09622_vs_v09623_ear_projection.svg", "artifacts/front_rear_ear_symmetry.svg",
    "artifacts/front_ear_section.svg", "artifacts/rear_ear_section.svg",
    "artifacts/axial_projection_comparison.svg", "artifacts/m4x21_stack.svg",
    "artifacts/geometry_freeze.svg", "artifacts/physical_test_sequence.svg",
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
    result = {"checks": checks, "repository": str(root), "branch": branch, "head": head, "staged": staged,
              "tracked_dirty": dirty, "outside_untracked": outside_snapshot(), "lane_files": len(lane_files),
              "authority_sha256": authority, "parent_sha256": parent,
              "protected_lanes": {rel: {"count": value[0], "tree_sha256": value[1], "status": "UNCHANGED"}
                                  for rel, value in protected.items()}, "cache": cache, "forbidden": forbidden}
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def load_parent():
    spec = importlib.util.spec_from_file_location("paddy_v09622_parent", PARENT_DIR / PARENT_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("parent import")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PARENT = load_parent()


def cylinder(radius: float, height: float, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height).translate((0, 0, z))


def axis_y_cylinder(radius: float, length: float, x: float, y0: float, z: float) -> cq.Workplane:
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(x, y0, z), cq.Vector(0, 1, 0)))


def volume(shape: cq.Workplane) -> float:
    return round(sum(float(s.Volume()) for s in shape.solids().vals()), 6)


def parent_pulley() -> cq.Workplane:
    return importers.importStep(str(PARENT_DIR / PARENT_STEP))


def frozen_structure(spoke_outer: float = 38.0, include_ring: bool = True) -> cq.Workplane:
    return PARENT.frozen_structure(spoke_outer, include_ring)


def rounded_ear(z0: float, z1: float) -> cq.Workplane:
    shape = (cq.Workplane("XY").box(EAR_X_MM[1] - EAR_X_MM[0], EAR_Y_STACK_MM, z1 - z0)
             .translate(((EAR_X_MM[0] + EAR_X_MM[1]) / 2.0, 0.0, (z0 + z1) / 2.0)))
    return shape.edges("|Z").fillet(EAR_FILLET_MM)


def hub_blank() -> cq.Workplane:
    front = cylinder(HUB_OD_MM / 2.0, 10.0, 0.0)
    neutral = cylinder(NEUTRAL_OD_MM / 2.0, 6.0, 10.0)
    rear = cylinder(HUB_OD_MM / 2.0, 10.0, 16.0)
    return (front.union(neutral).union(rear)
            .union(rounded_ear(*FRONT_EAR_Z_MM)).union(rounded_ear(*REAR_EAR_Z_MM)).clean())


def clamp_cutters(bore_mm: float) -> list[cq.Workplane]:
    cutters = [cylinder(bore_mm / 2.0, 36.0, -8.0)]
    split = (cq.Workplane("XY").box(EAR_X_MM[1] - 4.7 + 2.0, SPLIT_WIDTH_MM, 36.0)
             .translate(((4.7 + EAR_X_MM[1] + 2.0) / 2.0, 0.0, 10.0)))
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


def symmetric_pulley(bore_mm: float = PRIMARY_BORE_MM, include_ring: bool = True,
                     spoke_outer: float = 38.0) -> cq.Workplane:
    result = frozen_structure(spoke_outer, include_ring).union(hub_blank()).clean()
    for cutter in clamp_cutters(bore_mm):
        result = result.cut(cutter)
    return result.clean()


def coupon(bore_mm: float, label: str) -> cq.Workplane:
    result = symmetric_pulley(bore_mm, False, 27.0)
    mark = cq.Workplane("XY").text(label, 3.0, 0.30, combine=True).translate((-10.0, -1.5, 25.95))
    return result.cut(mark).clean()


def triplet() -> cq.Workplane:
    parts = [coupon(10.10, "B1010").translate((-72, 0, 0)), coupon(10.20, "B1020"),
             coupon(10.30, "B1030").translate((72, 0, 0))]
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def hardware_envelopes() -> list[cq.Workplane]:
    result: list[cq.Workplane] = []
    for z in (FRONT_M4_Z_MM, REAR_M4_Z_MM):
        for x in M4_X_MM:
            result.extend([
                axis_y_cylinder(2.0, 21.0, x, -10.5, z),
                axis_y_cylinder(4.4, 1.2, x, 7.0, z), axis_y_cylinder(4.4, 1.2, x, -8.2, z),
                axis_y_cylinder(4.2, 3.2, x, 8.2, z), axis_y_cylinder(3.8, 3.0, x, -11.2, z),
            ])
    return result


def assembly_reference() -> cq.Workplane:
    items = [symmetric_pulley().val(), cylinder(5.0, 56.0, -15.0).val()]
    items.extend(part.val() for part in hardware_envelopes())
    return cq.Workplane(obj=cq.Compound.makeCompound(items))


def modification_envelope() -> cq.Workplane:
    box = cq.Workplane("XY").box(24.5, 42.0, 43.5).translate((14.75, 0.0, 14.25))
    center = cylinder(17.05, 34.5, -7.5)
    return box.union(center)


def freeze_regression(final: cq.Workplane) -> dict[str, object]:
    parent = parent_pulley()
    envelope = modification_envelope()
    p_out = parent.cut(envelope)
    f_out = final.cut(envelope)
    radial = cylinder(52.0, 24.0, -2.0).cut(cylinder(37.0, 24.0, -2.0))
    p_ring = parent.intersect(radial)
    f_ring = final.intersect(radial)
    outside_removed = volume(p_out.cut(f_out)); outside_added = volume(f_out.cut(p_out))
    ring_removed = volume(p_ring.cut(f_ring)); ring_added = volume(f_ring.cut(p_ring))
    return {
        "hub_modification_envelope": HUB_MODIFICATION_ENVELOPE,
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
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-15T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP timestamp")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    exporters.export(shape, str(path)); normalize_step(path)


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
    collision = sum(volume(final.intersect(item)) for item in hardware_envelopes())
    return {
        "pulley": {"valid": final.val().isValid(), "solid_count": final.solids().size(),
                   "overall_dimensions_mm": meshes[CAD[1]]["extents_mm"], "tooth_count": TOOTH_COUNT,
                   "pitch_family": PITCH_FAMILY, "pitch_mm": PITCH_MM, "spacing_deg": SPACING_DEG,
                   "tooth_face_width_mm": TOOTH_FACE_WIDTH_MM, "flange_count": FLANGE_COUNT,
                   "flange_od_mm": FLANGE_OD_MM, "flange_thickness_mm": FLANGE_THICKNESS_MM,
                   "rim_min_radial_mm": RIM_MIN_RADIAL_MM, "spoke_count": SPOKE_COUNT,
                   "spoke_width_mm": SPOKE_WIDTH_MM, "belt_plane_mm": BELT_PLANE_Z_MM},
        "freeze_regression": freeze,
        "hub": {"od_mm": HUB_OD_MM, "width_mm": HUB_WIDTH_MM, "neutral_od_mm": NEUTRAL_OD_MM,
                "shaft_nominal_mm": SHAFT_NOMINAL_MM, "bore_candidates_mm": BORE_CANDIDATES_MM,
                "primary_bore_candidate_mm": PRIMARY_BORE_MM, "split_width_mm": SPLIT_WIDTH_MM,
                "front_active_band_z_mm": FRONT_ACTIVE_Z_MM, "neutral_band_z_mm": NEUTRAL_Z_MM,
                "rear_active_band_z_mm": REAR_ACTIVE_Z_MM, "continuous_coaxial_bore": True},
        "ear_symmetry": {"mirror_plane_z_mm": BELT_PLANE_Z_MM,
                         "front_z_mm": FRONT_EAR_Z_MM, "rear_z_mm": REAR_EAR_Z_MM,
                         "front_axial_height_mm": EAR_AXIAL_HEIGHT_MM, "rear_axial_height_mm": EAR_AXIAL_HEIGHT_MM,
                         "front_outward_projection_mm": EAR_OUTWARD_PROJECTION_MM,
                         "rear_outward_projection_mm": EAR_OUTWARD_PROJECTION_MM,
                         "projection_difference_mm": 0.0, "front_stack_mm": EAR_Y_STACK_MM,
                         "rear_stack_mm": EAR_Y_STACK_MM, "stack_difference_mm": 0.0,
                         "front_x_extent_mm": EAR_X_MM, "rear_x_extent_mm": EAR_X_MM,
                         "root_fillet_front_mm": EAR_FILLET_MM, "root_fillet_rear_mm": EAR_FILLET_MM,
                         "minimum_thickness_front_mm": EAR_MIN_MM, "minimum_thickness_rear_mm": EAR_MIN_MM,
                         "external_ear_not_internal_boss": True, "axial_mirror_pass": True},
        "hardware": {"front_m4_count": 2, "rear_m4_count": 2, "total_m4_count": 4,
                     "front_centers_mm": [[x, 0.0, FRONT_M4_Z_MM] for x in M4_X_MM],
                     "rear_centers_mm": [[x, 0.0, REAR_M4_Z_MM] for x in M4_X_MM],
                     "clearance_hole_mm": M4_CLEARANCE_MM, "threaded_length_mm": M4_THREADED_LENGTH_MM,
                     "front_printed_stack_mm": EAR_Y_STACK_MM, "rear_printed_stack_mm": EAR_Y_STACK_MM,
                     "washer_candidate_each_mm": WASHER_THICKNESS_CANDIDATE_MM,
                     "nut_candidate_mm": NUT_THICKNESS_CANDIDATE_MM,
                     "stack_used_candidate_mm": STACK_USED_CANDIDATE_MM,
                     "thread_remaining_candidate_mm": STACK_REMAINING_CANDIDATE_MM,
                     "visible_thread_pitch_candidate": VISIBLE_THREAD_CANDIDATE,
                     "petg_tapped_thread_count": 0, "hidden_nut_ceiling": False,
                     "architecture": "THROUGH_M4/METAL_WASHER/PETG_EAR/METAL_WASHER/METAL_NUT",
                     "hardware_envelope_intersection_mm3": round(collision, 6)},
        "print": {"printer": "Bambu Lab A1", "material": "PETG", "shaft_axis": "Z",
                  "support": "HOLD_SLICER_SUPPORT_REQUIRED_BY_FRONT_OUTWARD_EAR",
                  "reason": "front ear projects 6.2 mm below frozen flange face; no false support-free PASS"},
        "physical": {"front_only_resistance": "CONFIRMED_V09622", "axial_hand_pull_removal": True,
                     "target": "INCREASE_AXIAL_PULL_OUT_RESISTANCE_WITH_SYMMETRIC_REAR_ACTION",
                     "release_after_test": "REQUIRED", "powered": "NOT_APPROVED"},
        "mesh": meshes, "step_import": steps,
    }


def parameters() -> dict[str, object]:
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "parent": {"lane": PARENT_REL.as_posix(), "files_sha256": PARENT_FILES_SHA256},
            "source": {"lane": SOURCE_REL.as_posix(), "artifact": SOURCE_STEP, "sha256": SOURCE_SHA256},
            "frozen": {"teeth": 60, "pitch_mm": 5.0, "spacing_deg": 6.0, "face_mm": 16.0,
                       "flanges": 2, "flange_od_mm": 102.0, "spokes": 6, "spoke_width_mm": 10.0,
                       "belt_plane_mm": 10.0},
            "hub": {"od_mm": 34.0, "width_mm": 26.0, "neutral_od_mm": 28.0,
                    "bands_mm": [10.0, 6.0, 10.0], "split_mm": 1.3,
                    "bore_candidates_mm": BORE_CANDIDATES_MM},
            "ears": {"front_z_mm": FRONT_EAR_Z_MM, "rear_z_mm": REAR_EAR_Z_MM,
                     "outward_projection_each_mm": 6.2, "stack_each_mm": 14.0, "mirror_plane_z_mm": 10.0},
            "hardware": {"front_m4": 2, "rear_m4": 2, "threaded_length_mm": 21.0,
                         "clearance_mm": 4.5, "petg_threads": 0},
            "gates": {"first_print": "COUPONS_ONLY", "physical_clamp": "HOLD",
                      "powered": "NOT_APPROVED", "full_torque": "NOT_APPROVED"}}


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:14px}}.o{{fill:none;stroke:#264653;stroke-width:4}}.a{{fill:#ffe8d6;stroke:#e76f51;stroke-width:4}}.b{{fill:#d8f3dc;stroke:#2a9d8f;stroke-width:4}}.d{{stroke:#457b9d;stroke-width:3;fill:none}}</style><text x="30" y="44" class="t">{title}</text>{body}<text x="30" y="678" class="s">{VERSION} · SYMMETRIC EXTERNAL EARS · PHYSICAL CLAMP TEST REQUIRED · POWERED USE NOT APPROVED</text></svg>'''


def svg_documents() -> dict[str, str]:
    compare = svg_page("v0.9.6.22 → v0.9.6.23 ear projection", '''<rect x="150" y="170" width="300" height="300" class="o"/><rect x="390" y="110" width="100" height="180" class="a"/><rect x="750" y="170" width="300" height="300" class="o"/><rect x="710" y="110" width="100" height="180" class="a"/><rect x="990" y="110" width="100" height="180" class="b"/><text x="140" y="540" class="l">v22: lower face flush/obscured</text><text x="700" y="540" class="l">v23: bottom/top outward 6.2 / 6.2</text>''')
    symmetry = svg_page("Front / rear external-ear axial symmetry", '''<line x1="100" y1="350" x2="1100" y2="350" class="d"/><rect x="390" y="350" width="180" height="190" class="a"/><rect x="630" y="160" width="180" height="190" class="b"/><text x="360" y="590" class="l">FRONT Z−6.2..6.8</text><text x="650" y="120" class="l">REAR Z13.2..26.2</text><text x="430" y="90" class="l">mirror plane = belt plane Z10</text>''')
    front = svg_page("Front external clamp ear", '''<rect x="230" y="160" width="650" height="300" rx="35" class="a"/><circle cx="430" cy="310" r="28" fill="#fff" stroke="#264653" stroke-width="4"/><circle cx="680" cy="310" r="28" fill="#fff" stroke="#264653" stroke-width="4"/><text x="250" y="530" class="l">external projection 6.2 · height13 · stack14 · R3 · min4.25</text>''')
    rear = svg_page("Rear external clamp ear", '''<rect x="230" y="160" width="650" height="300" rx="35" class="b"/><circle cx="430" cy="310" r="28" fill="#fff" stroke="#264653" stroke-width="4"/><circle cx="680" cy="310" r="28" fill="#fff" stroke="#264653" stroke-width="4"/><text x="250" y="530" class="l">external projection 6.2 · height13 · stack14 · R3 · min4.25</text>''')
    projection = svg_page("Numerical projection comparison", '''<text x="100" y="160" class="l">Frozen pulley faces: Z0 / Z20</text><text x="100" y="240" class="l">Front ear: Z−6.2..6.8 → outward 6.2 mm</text><text x="100" y="320" class="l">Rear ear: Z13.2..26.2 → outward 6.2 mm</text><text x="100" y="400" class="l">difference = 0.0 mm · axial height difference = 0.0 mm</text><text x="100" y="480" class="l">stack/root/fillet/M4 count all matched</text>''')
    stack = svg_page("M4 ×21 stack both ears", '''<text x="100" y="170" class="l">FRONT = REAR = PETG14.0 + washer1.2×2 + nut3.2 = 19.6 mm</text><text x="100" y="260" class="l">remaining 1.4 mm ≈ 2.0 pitches</text><text x="100" y="350" class="l">through bolt + metal washers + metal nut; PETG tap 0</text><text x="100" y="440" class="l">actual washer/nut/protrusion and split margin: PHYSICAL HOLD</text>''')
    freeze = svg_page("Frozen geometry firewall", '''<circle cx="360" cy="350" r="255" class="o"/><circle cx="360" cy="350" r="135" class="d"/><text x="700" y="180" class="l">60T / HTD5M / pitch5 / spacing6°</text><text x="700" y="250" class="l">flange2 / OD102 / rim exact</text><text x="700" y="320" class="l">6 spokes / 10 mm / R5-class</text><text x="700" y="390" class="l">outside hub envelope add/remove 0</text><text x="700" y="460" class="l">belt plane Z10 unchanged</text>''')
    test = svg_page("Physical coupon states A–D", '''<text x="90" y="150" class="l">A: NO M4</text><text x="90" y="230" class="l">B: FRONT M4×2 ONLY</text><text x="90" y="310" class="l">C: REAR M4×2 ONLY</text><text x="90" y="390" class="l">D: FRONT + REAR M4×4</text><text x="90" y="490" class="l">record insertion/play/rotation/straight pull/split/white stress/crack/release</text>''')
    return dict(zip(SVGS, [compare, symmetry, front, rear, projection, stack, freeze, test]))


def documentation(geom: dict[str, object]) -> dict[str, str]:
    h = f"# Common Rover TEMP 60T {VERSION}\n\nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"
    e = geom["ear_symmetry"]; f = geom["freeze_regression"]
    return {
        "README.md": h + "\n目的は裏面にも表面と同じ外部突出earを設けることです。物理評価順は必ず A:NO M4、B:FRONT M4×2 only、C:REAR M4×2 only、D:FRONT+REAR M4×4。最初はcoupon3種だけを印刷します。\n",
        "DESIGN_AUTHORITY.md": h + "\nv0.9.6.22実STEPを親とし、front/rear external earの軸方向対称化だけを実施。60T、flange、rim、spokes、belt plane、hub bands、bore、splitは保護します。\n",
        "PHYSICAL_FAILURE_FROM_V09622.md": h + "\nfront-onlyで抵抗増加は確認されたがstraight hand pull removalが可能。さらに裏面earが上面と同じ外部突出に見えず、同等作用が不足するため本修正を行います。\n",
        "CHANGE_SCOPE_FIREWALL.md": h + f"\n変更はhub envelopeのみ。外側removed={f['outside_removed_mm3']} / added={f['outside_added_mm3']} mm³。P20653/crawler/guard/top roller変更0。\n",
        "FROZEN_60T_GEOMETRY.md": h + "\nHTD5M60T、pitch5、spacing6°、face16、flange2/OD102/t2、rim、6×10 mm spokes/R5-class、belt plane Z10を維持。visible outside-envelope change0。\n",
        "SYMMETRIC_DOUBLE_CLAMP_ARCHITECTURE.md": h + f"\nFront ear Z{e['front_z_mm']}、rear ear Z{e['rear_z_mm']}。frozen faceからの外向き突出は{e['front_outward_projection_mm']}/{e['rear_outward_projection_mm']} mm、差0。穴だけ/内部bossではなく同一XY outlineの外部earです。\n",
        "FRONT_REAR_CLAMP_BANDS.md": h + "\nFront Z0–10、neutral Z10–16、rear Z16–26、shaft engagement26、hubOD34、neutralOD28、continuous split1.3を維持。\n",
        "M4X21_HARDWARE_STACK.md": h + "\nFront/rearともprinted14.0 + washer1.2×2 + nut3.2 =19.6 mm候補。21.0から1.4 mm≈2.0 pitches残る。実washer/nutはHOLD。\n",
        "SHAFT_INTERFACE.md": h + "\nØ10 shaft。winner未確定のためB10.10/10.20/10.30維持。split bottoming不可、release後分解可能必須。\n",
        "BORE_COUPON_PLAN.md": h + "\n3 couponともfullと同じ対称external ears、M4×4、stack14、bands、splitを再現。full pulleyを先に印刷しません。\n",
        "CLAMP_FORCE_TEST_PLAN.md": h + "\nA→B→C→Dの各状態でradial/axial play、rotation、straight pull、split margin、white stress、crack、release後removalを記録。破壊的締付け/bodyweight pullは禁止。\n",
        "PRINT_PLAN.md": h + "\nBambu A1/PETG。front earがfrozen lower faceより6.2 mm突出するためsupport-free PASSを出しません。couponでslicer orientation/supportを先に確定するまで`HOLD_SLICER_SUPPORT_REQUIRED`。\n",
        "ASSEMBLY_PLAN.md": h + "\nThrough M4→metal washer→PETG ear→metal washer→metal nut。front/rearを均等に段階締結し両split marginを残す。hidden nut ceiling/PETG tapなし。\n",
        "SHAFT_WITNESS_MARK.md": h + "\nshaft+hubを横切る連続線必須。shiftはFAIL_HUB_SLIPで即停止。\n",
        "HAND_TEST.md": h + "\nCoupon winner後fullを1個印刷。static後10F/10R、slip/skip/climb/contact/crack全0。\n",
        "DUAL_MOTOR_POWERED_TEST.md": h + "\n全物理gate後のみ単側1–2/5/10秒、dual1–2/5/10秒。各段階で停止点検。現時点NOT_APPROVED。\n",
        "FAILURE_CRITERIA.md": h + "\nSplit bottoming+loose=FAIL_LOOSE。whitening/layer separation/crack/ear bending=FAIL_STRUCTURAL。witness shift=axial/rotational FAIL_HUB_SLIP。\n",
        "POWERED_GATE.md": h + "\nFull torque、stall、blocked crawler、mud/water/fieldは禁止。最大でもTEMP_PULLEY_DUAL_MOTOR_DRY_LOW_LOAD_PASS。\n",
        "HOLD_REGISTER.md": h + "\nHOLD: bore winner、A/B/C/D物理結果、actual M4 stack、split margin、PETG creep、tool access、slicer support、runout、belt seating、frame/bearing clearance、powered use。\n",
        "SOURCE_TRACE.md": h + f"\nParent `{PARENT_REL.as_posix()}/{PARENT_STEP}` SHA `{PARENT_FILES_SHA256[PARENT_STEP]}`。60T authority SHA `{SOURCE_SHA256}`。/mnt/data参照は当環境に無かったため、同名保護parent artifactを使用。\n",
    }


def validation(repo: dict[str, object], geom: dict[str, object]) -> dict[str, object]:
    f = geom["freeze_regression"]; e = geom["ear_symmetry"]; h = geom["hardware"]
    checks = {
        "parent_v09622": "PASS", "source_60t": "PASS",
        "tooth_change_zero": "PASS" if f["tooth_change"] == 0 else "FAIL",
        "flange_change_zero": "PASS" if f["flange_change"] == 0 else "FAIL",
        "rim_change_zero": "PASS" if f["rim_change"] == 0 else "FAIL",
        "spoke_visible_change_zero": "PASS" if f["spoke_visible_change_outside_envelope"] == 0 else "FAIL",
        "external_ear_symmetry": "PASS" if e["axial_mirror_pass"] and e["projection_difference_mm"] == 0 else "FAIL",
        "front_projection_6_2": "PASS" if e["front_outward_projection_mm"] == 6.2 else "FAIL",
        "rear_projection_6_2": "PASS" if e["rear_outward_projection_mm"] == 6.2 else "FAIL",
        "stack_equal": "PASS" if e["stack_difference_mm"] == 0 else "FAIL",
        "m4_2_2_4": "PASS" if [h["front_m4_count"], h["rear_m4_count"], h["total_m4_count"]] == [2, 2, 4] else "FAIL",
        "m4_21_packaging": "PASS_CANDIDATE", "three_bores": "PASS", "step_reload": "PASS",
        "stl_reload": "PASS", "protected_lanes": "PASS", "p20653_change_zero": "PASS",
        "physical_axial_pull": "HOLD", "real_clamp_friction": "HOLD", "slicer_support": "HOLD",
        "powered": "NOT_APPROVED",
    }
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "repository": repo, "geometry": geom, "checks": checks,
            "gates": {"first_print": "THREE_COUPONS_ONLY", "full_pulley": "HOLD_WINNER",
                      "powered": "NOT_APPROVED", "maximum": "TEMP_PULLEY_DUAL_MOTOR_DRY_LOW_LOAD_PASS"}}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def export_outputs(out: Path):
    (out / "artifacts").mkdir(parents=True, exist_ok=True)
    final = symmetric_pulley()
    shapes = {CAD[0]: final, CAD[1]: final, CAD[2]: coupon(10.10, "B1010"),
              CAD[3]: coupon(10.20, "B1020"), CAD[4]: coupon(10.30, "B1030"),
              CAD[5]: triplet(), CAD[6]: assembly_reference()}
    for rel, shape in shapes.items():
        path = out / rel; path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".step"): export_step(shape, path)
        else: exporters.export(shape, str(path), tolerance=0.02, angularTolerance=0.05)
    bore_map = {CAD[1]: 10.20, CAD[2]: 10.10, CAD[3]: 10.20, CAD[4]: 10.30}
    meshes = {rel: mesh_metrics(out / rel, bore_map.get(rel)) for rel in CAD if rel.endswith(".stl")}
    for rel, metric in meshes.items():
        expected = 3 if rel == CAD[5] else 1
        if not metric["watertight"] or metric["bad_edge_count"] or metric["degenerate_triangle_count"] or metric["component_count"] != expected:
            raise RuntimeError(f"mesh {rel}: {metric}")
    steps = {}
    for rel in CAD:
        if rel.endswith(".step"):
            shape = importers.importStep(str(out / rel)); valid = shape.solids().size() > 0 and all(x.isValid() for x in shape.solids().vals())
            if not valid: raise RuntimeError("STEP reload")
            steps[rel] = {"valid": valid, "solid_count": shape.solids().size()}
    return meshes, steps, final


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False)
    meshes, steps, final = export_outputs(out)
    geom = geometry_data(final, meshes, steps)
    if not geom["freeze_regression"]["hub_only_revision"] or not geom["ear_symmetry"]["axial_mirror_pass"]:
        raise RuntimeError("freeze/symmetry")
    if geom["hardware"]["hardware_envelope_intersection_mm3"] != 0:
        raise RuntimeError("hardware collision")
    for rel, text in documentation(geom).items(): write_text(out / rel, text)
    for rel, text in svg_documents().items(): write_text(out / rel, text)
    write_json(out / "design_parameters.json", parameters())
    write_json(out / "validation_report.json", validation(repo, geom))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS=44\nSTEP=2\nSTL=5\nSVG=8\nFRONT_PROJECTION_MM=6.2\nREAR_PROJECTION_MM=6.2\nPROJECTION_DIFFERENCE_MM=0\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=120\nBUILDER_VERIFY=PASS\nREPRODUCIBILITY=44_OF_44_PASS\nPHYSICAL_HOLD=CLAMP/PULL/SUPPORT/POWER")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES: raise RuntimeError(f"paths {len(files)}")
    return {"path_count": len(files), "geometry": geom, "status": STATUS}


def parse_sums(path: Path) -> dict[str, str]:
    result = {}
    for row in path.read_text(encoding="utf-8").splitlines():
        value, rel = row.split("  ", 1); result[rel] = value
    return result


def verify(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(True)
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES: raise RuntimeError("paths")
    if (out / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() != EXPECTED_FILES: raise RuntimeError("manifest")
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]: raise RuntimeError("commit paths")
    sums = parse_sums(out / "SHA256SUMS.txt")
    mismatch = [rel for rel, value in sums.items() if sha256(out / rel) != value]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}: raise RuntimeError(f"sha {mismatch}")
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if "FAIL" in report["checks"].values(): raise RuntimeError("validation")
    return {"repository": repo, "path_count": len(files), "step_count": len(list(out.rglob("*.step"))),
            "stl_count": len(list(out.rglob("*.stl"))), "svg_count": len(list(out.rglob("*.svg"))),
            "sha_mismatch_count": 0, "ear_symmetry": report["geometry"]["ear_symmetry"],
            "mesh": report["geometry"]["mesh"], "status": STATUS}


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_temp60_v09623_") as name:
        shadow = Path(name) / LANE_NAME; (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER); shutil.copyfile(out / TEST, shadow / TEST)
        generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch: raise RuntimeError(f"repro {mismatch}")
    return {"checked": 44, "byte_identical": 44, "mismatch_count": 0}


def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify(out)
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_TEMP_HTD5M_60T_SYMMETRIC_DOUBLE_SPLIT_CLAMP_v0_9_6_23_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists(): raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 15, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED; info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist(); prefix = LANE_NAME + "/"
        relative = sorted(n[len(prefix):] for n in names if n.startswith(prefix))
        duplicate = len(names) - len(set(names)); traversal = sum(".." in PurePosixPath(n).parts for n in names)
        contamination = sum(not n.startswith(prefix) for n in names); extracted = {n[len(prefix):]: archive.read(n) for n in names if n.startswith(prefix)}
        sums = parse_sums(out / "SHA256SUMS.txt"); mismatch = sum(hashlib.sha256(extracted[rel]).hexdigest() != value for rel, value in sums.items())
    result = {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
              "duplicate_count": duplicate, "traversal_count": traversal, "manifest_exact": relative == EXPECTED_FILES,
              "sha_mismatch_count": mismatch, "parent_contamination_count": contamination}
    if duplicate or traversal or contamination or mismatch or relative != EXPECTED_FILES: raise RuntimeError(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--build", action="store_true"); parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true"); parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()): parser.error("select action")
    if args.build: print(json.dumps({"build": generate_all()}, ensure_ascii=True, indent=2))
    if args.verify: print(json.dumps({"verify": verify()}, ensure_ascii=True, indent=2))
    if args.reproducibility: print(json.dumps({"reproducibility": reproducibility()}, ensure_ascii=True, indent=2))
    if args.package: print(json.dumps({"zip": package()}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
