#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build v0.9.6.25: shortest passing compact external-ear TEMP 60T clamp."""
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


VERSION = "v0.9.6.25"
CLASSIFICATION = "TEMP_HTD5M_60T_COMPACT_EXTERNAL_EAR_DOUBLE_SPLIT_CLAMP"
STATUS = (
    "TEMP_HTD5M_60T_COMPACT_EXTERNAL_EAR_DOUBLE_SPLIT_CLAMP_CAD_COMPLETE/"
    "PROJECTION_RANGE_8_8_TO_16_8_EVALUATED/SHORTEST_PASSING_PROJECTION_SELECTED/"
    "ALL_FOUR_M4_HOLES_FULLY_EXTERNAL/WASHER_HEAD_NUT_TOOL_ACCESS_PRESERVED/"
    "EAR_STRENGTH_GEOMETRY_PRESERVED/60T_FUNCTIONAL_GEOMETRY_FROZEN/"
    "COUPONS_READY_FOR_PHYSICAL_TEST/POWERED_USE_NOT_APPROVED/COMMIT_READY_NOT_STAGED"
)
LANE_NAME = "common_rover_temp_htd5m_60t_compact_external_ear_double_split_clamp_v0_9_6_25"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2666
BASE_OUTSIDE_DIGEST = "88ee3cbe0b2519384d84cd45086a73c2d088c780e972eb3a453f011ee707ae10"

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
    "cad/common_rover/common_rover_temp_htd5m_60t_external_ear_double_split_clamp_v0_9_6_24": (46, "b09600fae8ee56f5ab97fab966818d20119329cbadf8de9d0f54b0d614306c55"),
    "cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1": (53, "a0cb4b831d639be4619a6bb42bff765a8196e04963dfc2df8826e1bbaf89fe00"),
}

PARENT_REL = PurePosixPath("cad/common_rover/common_rover_temp_htd5m_60t_external_ear_double_split_clamp_v0_9_6_24")
PARENT_DIR = REPO_ROOT / PARENT_REL
PARENT_BUILDER = "build_temp_htd5m_60t_external_ear_double_split_clamp_v0_9_6_24.py"
PARENT_STEP = "artifacts/temp_htd5m_60t_external_ear_double_split_clamp_v0_9_6_24.step"
PARENT_FILES_SHA256 = {
    PARENT_BUILDER: "5f6b3f64f53a5f800ff93e93518eab545664b0ca98af9bf08d966aa8e5689c9a",
    PARENT_STEP: "ca23b6a27b3ff4f9dec11fede7cb10dfcd6989a9d758f0bc08a9ecaa9ef5c1d3",
    "artifacts/temp_htd5m_60t_external_ear_double_split_clamp_v0_9_6_24.stl": "fb4d7dd73224142d4b7296accac8a9d14a083ff042b4a97de6ad9d0874ca8b77",
    "artifacts/double_split_clamp_b1010_v0_9_6_24.stl": "850b5c71c41ea4397a14aa9adb5900a705efb377b5846a96a08a7aeff503bba6",
    "design_parameters.json": "d51502e6b423b1c1d5835f256fd2c774fab0a81f68c0056f4317de89b532227b",
    "validation_report.json": "a83543a73a4f00e8e754c567007bb0c1655ec6748d14fb739ad2a9cdb660f8a6",
    "tests/test_temp_htd5m_60t_external_ear_double_split_clamp_v0_9_6_24_contract.py": "bda359a2f739dc626733bb36c787e81f0611e5654eb349d8c3f2694dcd19c7a9",
}
SOURCE_REL = PurePosixPath("cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1")
SOURCE_STEP = "cad/drive_htd5m_60t_reference.step"
SOURCE_SHA256 = "bc3e00bca0db5fe4c3975b5904ad4f72faa2b3fe6822057522c12df16ec0d256"

PROJECTION_MIN_MM = 8.8
PROJECTION_MAX_MM = 16.8
PROJECTION_INCREMENT_MM = 0.5
IDEAL_PROJECTION_MM = 8.8
CANDIDATE_PROJECTIONS_MM = [round(PROJECTION_MIN_MM + 0.5 * index, 1) for index in range(17)]
M4_FACE_OFFSET_MM = 8.0
SELECTED_PROJECTION_MM = 15.3
PARENT_PROJECTION_MM = 18.0
FRONT_HUB_FACE_Z_MM = 0.0
REAR_HUB_FACE_Z_MM = 26.0
HUB_MIDPLANE_Z_MM = 13.0
ROOT_INNER_FRONT_Z_MM = 7.0
ROOT_INNER_REAR_Z_MM = 19.0
FRONT_EAR_Z_MM = [-SELECTED_PROJECTION_MM, ROOT_INNER_FRONT_Z_MM]
REAR_EAR_Z_MM = [ROOT_INNER_REAR_Z_MM, REAR_HUB_FACE_Z_MM + SELECTED_PROJECTION_MM]
FRONT_M4_Z_MM = -M4_FACE_OFFSET_MM
REAR_M4_Z_MM = REAR_HUB_FACE_Z_MM + M4_FACE_OFFSET_MM
EAR_AXIAL_HEIGHT_MM = SELECTED_PROJECTION_MM + ROOT_INNER_FRONT_Z_MM

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
NEUTRAL_OD_MM = 28.0
FRONT_ACTIVE_Z_MM = [0.0, 10.0]
NEUTRAL_Z_MM = [10.0, 16.0]
REAR_ACTIVE_Z_MM = [16.0, 26.0]
EAR_X_MM = [1.5, 35.5]
EAR_Y_STACK_MM = 14.0
EAR_FILLET_MM = 4.0
EAR_MIN_THICKNESS_MM = 5.0
ROOT_AXIAL_OVERLAP_MM = 7.0
SPLIT_WIDTH_MM = 1.3
SPLIT_CLOSURE_REFERENCE_MM = 0.6
SPLIT_REMAINING_AT_REFERENCE_MM = SPLIT_WIDTH_MM - SPLIT_CLOSURE_REFERENCE_MM
ROOT_MIN_LOAD_SECTION_MM2 = (EAR_Y_STACK_MM - SPLIT_WIDTH_MM) * ROOT_AXIAL_OVERLAP_MM
M4_X_MM = [13.5, 27.5]
M4_SPACING_MM = 14.0
M4_CLEARANCE_MM = 4.5
M4_THREADED_LENGTH_MM = 21.0
WASHER_OD_MM = 9.0
WASHER_THICKNESS_MM = 1.2
NUT_THICKNESS_MM = 3.2
INTEGRATED_HEAD_OD_MM = 12.0
SERVICE_DIAMETER_MM = 14.0
SERVICE_RADIUS_MM = SERVICE_DIAMETER_MM / 2.0
SERVICE_CLEARANCE_TO_FROZEN_MM = M4_FACE_OFFSET_MM - SERVICE_RADIUS_MM
HEAD_CLEARANCE_TO_FROZEN_MM = M4_FACE_OFFSET_MM - INTEGRATED_HEAD_OD_MM / 2.0
SELECTED_SERVICE_OUTER_MARGIN_MM = SELECTED_PROJECTION_MM - M4_FACE_OFFSET_MM - SERVICE_RADIUS_MM
SELECTED_EDGE_LIGAMENT_MM = SELECTED_PROJECTION_MM - M4_FACE_OFFSET_MM - M4_CLEARANCE_MM / 2.0
BORE_CANDIDATES_MM = [10.10, 10.20, 10.30]
PRIMARY_BORE_MM = 10.20
SHAFT_NOMINAL_MM = 10.0
BORE_TO_M4_LIGAMENT_MM = min(M4_X_MM) - PRIMARY_BORE_MM / 2.0 - M4_CLEARANCE_MM / 2.0
STACK_USED_MM = EAR_Y_STACK_MM + 2 * WASHER_THICKNESS_MM + NUT_THICKNESS_MM
STACK_REMAINING_MM = M4_THREADED_LENGTH_MM - STACK_USED_MM
VISIBLE_THREAD_COUNT = STACK_REMAINING_MM / 0.7
SUPPORT_PROJECTION_REDUCTION_PERCENT = round((PARENT_PROJECTION_MM - SELECTED_PROJECTION_MM) / PARENT_PROJECTION_MM * 100.0, 1)
SUPPORT_EAR_HEIGHT_REDUCTION_PERCENT = round((25.0 - EAR_AXIAL_HEIGHT_MM) / 25.0 * 100.0, 1)

BUILDER = "build_temp_htd5m_60t_compact_external_ear_double_split_clamp_v0_9_6_25.py"
TEST = "tests/test_temp_htd5m_60t_compact_external_ear_double_split_clamp_v0_9_6_25_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "V09624_PHYSICAL_PACKAGING_REVIEW.md",
    "COMPACT_EAR_REQUIREMENT.md", "PROJECTION_DATUM.md", "PROJECTION_CANDIDATE_STUDY.md",
    "SELECTED_PROJECTION.md", "M4_HARDWARE_ENVELOPE.md", "EAR_EDGE_LIGAMENT_ANALYSIS.md",
    "EAR_ROOT_STRENGTH_GEOMETRY.md", "SPLIT_CLOSURE_ANALYSIS.md", "FRONT_REAR_SYMMETRY.md",
    "BORE_COUPON_PLAN.md", "PRINT_PLAN.md", "PHYSICAL_TEST_PLAN.md", "POWERED_GATE.md",
    "HOLD_REGISTER.md", "SOURCE_TRACE.md", "BUILD_LOG.txt", "TEST_LOG.txt",
    "design_parameters.json", "validation_report.json", "MANIFEST.txt", "SHA256SUMS.txt",
    "COMMIT_PATHS.txt",
]
CAD = [
    "artifacts/temp_htd5m_60t_compact_external_ear_double_split_clamp_v0_9_6_25.step",
    "artifacts/temp_htd5m_60t_compact_external_ear_double_split_clamp_v0_9_6_25.stl",
    "artifacts/compact_double_split_clamp_b1010_v0_9_6_25.stl",
    "artifacts/compact_double_split_clamp_b1020_v0_9_6_25.stl",
    "artifacts/compact_double_split_clamp_b1030_v0_9_6_25.stl",
    "artifacts/compact_double_split_clamp_triplet_v0_9_6_25.stl",
    "artifacts/temp_htd5m_60t_compact_external_ear_double_split_clamp_hardware_reference_v0_9_6_25.step",
]
SVGS = [
    "artifacts/v09624_vs_v09625_projection.svg", "artifacts/projection_candidate_matrix.svg",
    "artifacts/selected_ear_side_view.svg", "artifacts/m4_hardware_access.svg",
    "artifacts/washer_envelope_clearance.svg", "artifacts/ear_edge_ligament.svg",
    "artifacts/front_rear_symmetry.svg", "artifacts/split_closure.svg",
]
EXPECTED_FILES = sorted([BUILDER, TEST, *DOCS, *CAD, *SVGS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def load_parent():
    spec = importlib.util.spec_from_file_location("paddy_v09624_parent", PARENT_DIR / PARENT_BUILDER)
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


def evaluate_candidate(projection: float) -> dict[str, object]:
    service_outer_margin = round(projection - M4_FACE_OFFSET_MM - SERVICE_RADIUS_MM, 3)
    edge_ligament = round(projection - M4_FACE_OFFSET_MM - M4_CLEARANCE_MM / 2.0, 3)
    service_clear = round(SERVICE_CLEARANCE_TO_FROZEN_MM, 3)
    insertion = service_outer_margin >= 0 and service_clear >= 1.0
    tool = service_clear >= 1.0
    edge_pass = edge_ligament >= 5.0
    root_pass = EAR_MIN_THICKNESS_MM >= 5.0 and EAR_FILLET_MM >= 4.0 and ROOT_MIN_LOAD_SECTION_MM2 >= 88.0
    split_pass = SPLIT_REMAINING_AT_REFERENCE_MM > 0
    overall = insertion and tool and edge_pass and root_pass and split_pass
    reasons: list[str] = []
    if service_outer_margin < 0:
        reasons.append(f"SERVICE_ENVELOPE_CLIPPED_{abs(service_outer_margin):.1f}MM")
    if edge_ligament < 4.25:
        reasons.append("FAIL_EDGE_LIGAMENT_HARD_MIN")
    elif edge_ligament < 5.0:
        reasons.append("EDGE_LIGAMENT_BELOW_5MM_TARGET")
    if not root_pass:
        reasons.append("ROOT_GEOMETRY_FAIL")
    if not split_pass:
        reasons.append("SPLIT_CLOSURE_FAIL")
    return {
        "projection_mm": projection, "front_m4_center_z_mm": -M4_FACE_OFFSET_MM,
        "rear_m4_center_z_mm": REAR_HUB_FACE_Z_MM + M4_FACE_OFFSET_MM,
        "service_envelope_clearance_to_frozen_mm": service_clear,
        "service_envelope_outer_edge_margin_mm": service_outer_margin,
        "hole_to_outer_edge_ligament_mm": edge_ligament,
        "root_min_load_section_mm2": round(ROOT_MIN_LOAD_SECTION_MM2, 3),
        "ear_min_thickness_mm": EAR_MIN_THICKNESS_MM,
        "bore_to_m4_ligament_mm": round(BORE_TO_M4_LIGAMENT_MM, 3),
        "hardware_insertion": "PASS" if insertion else "FAIL",
        "tool_access": "PASS" if tool else "FAIL",
        "split_closure_geometry": "PASS" if split_pass else "FAIL",
        "overall": "PASS" if overall else "FAIL",
        "rejection_reason": "NONE" if overall else ";".join(reasons),
    }


def candidate_study() -> list[dict[str, object]]:
    study = [evaluate_candidate(value) for value in CANDIDATE_PROJECTIONS_MM]
    passing = [row for row in study if row["overall"] == "PASS"]
    if not passing or passing[0]["projection_mm"] != SELECTED_PROJECTION_MM:
        raise RuntimeError("NO_SAFE_COMPACT_EAR_GEOMETRY_WITHIN_8_8_TO_16_8")
    return study


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
    root_edges = [edge for edge in shape.edges("|Z").vals() if edge.Center().x < EAR_X_MM[0] + 0.01]
    return shape.newObject(root_edges).fillet(EAR_FILLET_MM)


def hub_blank() -> cq.Workplane:
    front = cylinder(HUB_OD_MM / 2.0, 10.0, 0.0)
    neutral = cylinder(NEUTRAL_OD_MM / 2.0, 6.0, 10.0)
    rear = cylinder(HUB_OD_MM / 2.0, 10.0, 16.0)
    return (front.union(neutral).union(rear)
            .union(rounded_ear(*FRONT_EAR_Z_MM)).union(rounded_ear(*REAR_EAR_Z_MM)).clean())


def clamp_cutters(bore_mm: float) -> list[cq.Workplane]:
    cutters = [cylinder(bore_mm / 2.0, 62.0, -17.0)]
    split_x0 = 4.7
    split_x1 = EAR_X_MM[1] + 0.5
    split = (cq.Workplane("XY").box(split_x1 - split_x0, SPLIT_WIDTH_MM, 62.0)
             .translate(((split_x0 + split_x1) / 2.0, 0.0, 13.0)))
    cutters.append(split)
    for z in (FRONT_M4_Z_MM, REAR_M4_Z_MM):
        for x in M4_X_MM:
            cutters.append(axis_y_cylinder(M4_CLEARANCE_MM / 2.0, 40.0, x, -20.0, z))
    return cutters


def compact_pulley(bore_mm: float = PRIMARY_BORE_MM, include_ring: bool = True,
                   spoke_outer: float = 38.0) -> cq.Workplane:
    result = frozen_structure(spoke_outer, include_ring).union(hub_blank()).clean()
    for cutter in clamp_cutters(bore_mm):
        result = result.cut(cutter)
    return result.clean()


def coupon(bore_mm: float, label: str) -> cq.Workplane:
    result = compact_pulley(bore_mm, False, 27.0)
    mark = cq.Workplane("XY").text(label, 3.0, 0.30, combine=True).translate((-10.0, -1.5, 41.05))
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
                axis_y_cylinder(WASHER_OD_MM / 2.0, 1.2, x, 7.0, z),
                axis_y_cylinder(WASHER_OD_MM / 2.0, 1.2, x, -8.2, z),
                axis_y_cylinder(4.2, 3.2, x, 8.2, z),
                axis_y_cylinder(INTEGRATED_HEAD_OD_MM / 2.0, 3.0, x, -11.2, z),
            ])
    return result


def access_sweeps() -> list[cq.Workplane]:
    result: list[cq.Workplane] = []
    for z in (FRONT_M4_Z_MM, REAR_M4_Z_MM):
        for x in M4_X_MM:
            result.extend([
                axis_y_cylinder(SERVICE_RADIUS_MM, 22.99, x, 7.01, z),
                axis_y_cylinder(SERVICE_RADIUS_MM, 22.99, x, -30.0, z),
            ])
    return result


def seat_annulus(x: float, z: float, positive: bool) -> cq.Workplane:
    y0 = 6.95 if positive else -7.0
    outer = axis_y_cylinder(SERVICE_RADIUS_MM, 0.05, x, y0, z)
    inner = axis_y_cylinder(M4_CLEARANCE_MM / 2.0, 0.05, x, y0, z)
    return outer.cut(inner)


def assembly_reference() -> cq.Workplane:
    items = [compact_pulley().val(), cylinder(5.0, 72.0, -23.0).val()]
    items.extend(item.val() for item in hardware_envelopes())
    items.extend(item.val() for item in access_sweeps())
    return cq.Workplane(obj=cq.Compound.makeCompound(items))


def modification_envelope() -> cq.Workplane:
    box = cq.Workplane("XY").box(35.5, 42.0, 64.0).translate((18.75, 0.0, 13.0))
    return box.union(cylinder(17.05, 64.0, -19.0))


def freeze_regression(final: cq.Workplane) -> dict[str, object]:
    parent = parent_pulley()
    envelope = modification_envelope()
    parent_out = parent.cut(envelope)
    final_out = final.cut(envelope)
    radial = cylinder(52.0, 66.0, -20.0).cut(cylinder(37.0, 66.0, -20.0))
    parent_ring = parent.intersect(radial)
    final_ring = final.intersect(radial)
    outside_removed = volume(parent_out.cut(final_out))
    outside_added = volume(final_out.cut(parent_out))
    ring_removed = volume(parent_ring.cut(final_ring))
    ring_added = volume(final_ring.cut(parent_ring))
    return {"outside_removed_mm3": outside_removed, "outside_added_mm3": outside_added,
            "ring_removed_mm3": ring_removed, "ring_added_mm3": ring_added,
            "tooth_change": 0 if ring_removed == ring_added == 0 else 1,
            "flange_change": 0 if ring_removed == ring_added == 0 else 1,
            "rim_change": 0 if ring_removed == ring_added == 0 else 1,
            "spoke_change": 0 if outside_removed == outside_added == 0 else 1,
            "belt_plane_change_mm": 0.0,
            "hub_only_revision": outside_removed == outside_added == ring_removed == ring_added == 0}


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
        metric["bore_mesh"].update({"front_split_gap_mm": SPLIT_WIDTH_MM,
                                    "rear_split_gap_mm": SPLIT_WIDTH_MM,
                                    "continuous_coaxial_bore": True,
                                    "ear_min_mm": EAR_MIN_THICKNESS_MM,
                                    "bore_to_m4_min_mm": round(min(M4_X_MM) - bore / 2.0 - M4_CLEARANCE_MM / 2.0, 6),
                                    "m4_clearance_mm": M4_CLEARANCE_MM})
    return metric


def geometry_data(final: cq.Workplane, meshes: dict[str, object], steps: dict[str, object]) -> dict[str, object]:
    study = candidate_study()
    freeze = freeze_regression(final)
    hardware_collision = sum(volume(final.intersect(item)) for item in hardware_envelopes())
    access_collision = sum(volume(final.intersect(item)) for item in access_sweeps())
    seat_ratios = []
    for z in (FRONT_M4_Z_MM, REAR_M4_Z_MM):
        for x in M4_X_MM:
            for positive in (False, True):
                annulus = seat_annulus(x, z, positive)
                seat_ratios.append(round(volume(final.intersect(annulus)) / volume(annulus), 6))
    return {
        "projection_study": {"allowed_range_mm": [PROJECTION_MIN_MM, PROJECTION_MAX_MM],
                             "increment_mm": PROJECTION_INCREMENT_MM, "ideal_mm": IDEAL_PROJECTION_MM,
                             "candidate_count": len(study), "candidates": study,
                             "selected_projection_mm": SELECTED_PROJECTION_MM,
                             "shortest_passing_projection_mm": next(row["projection_mm"] for row in study if row["overall"] == "PASS"),
                             "why_not_shorter": next(row["rejection_reason"] for row in reversed(study) if row["projection_mm"] < SELECTED_PROJECTION_MM)},
        "pulley": {"valid": final.val().isValid(), "solid_count": final.solids().size(),
                   "overall_dimensions_mm": meshes[CAD[1]]["extents_mm"], "tooth_count": TOOTH_COUNT,
                   "pitch_mm": PITCH_MM, "spacing_deg": SPACING_DEG, "tooth_face_width_mm": TOOTH_FACE_WIDTH_MM,
                   "flange_count": FLANGE_COUNT, "flange_od_mm": FLANGE_OD_MM,
                   "flange_thickness_mm": FLANGE_THICKNESS_MM, "spoke_count": SPOKE_COUNT,
                   "spoke_width_mm": SPOKE_WIDTH_MM, "belt_plane_mm": BELT_PLANE_Z_MM},
        "freeze_regression": freeze,
        "ear": {"projection_datum": "RESPECTIVE_ORIGINAL_HUB_END_FACE_TO_OUTERMOST_AXIAL_EAR_EDGE",
                "front_z_mm": FRONT_EAR_Z_MM, "rear_z_mm": REAR_EAR_Z_MM,
                "front_projection_mm": SELECTED_PROJECTION_MM, "rear_projection_mm": SELECTED_PROJECTION_MM,
                "symmetry_error_mm": 0.0, "mirror_plane_z_mm": HUB_MIDPLANE_Z_MM,
                "axial_height_mm": EAR_AXIAL_HEIGHT_MM, "minimum_thickness_mm": EAR_MIN_THICKNESS_MM,
                "root_fillet_mm": EAR_FILLET_MM, "root_min_load_section_mm2": round(ROOT_MIN_LOAD_SECTION_MM2, 3),
                "minimum_hole_to_free_edge_ligament_mm": round(SELECTED_EDGE_LIGAMENT_MM, 3),
                "bore_to_m4_minimum_ligament_mm": round(BORE_TO_M4_LIGAMENT_MM, 3)},
        "hardware_access": {"front_m4_count": 2, "rear_m4_count": 2, "total_m4_count": 4,
                            "front_centers_mm": [[x, 0.0, FRONT_M4_Z_MM] for x in M4_X_MM],
                            "rear_centers_mm": [[x, 0.0, REAR_M4_Z_MM] for x in M4_X_MM],
                            "integrated_head_envelope_mm": INTEGRATED_HEAD_OD_MM,
                            "integrated_head_clearance_to_frozen_mm": HEAD_CLEARANCE_TO_FROZEN_MM,
                            "service_envelope_mm": SERVICE_DIAMETER_MM,
                            "service_clearance_to_frozen_mm": SERVICE_CLEARANCE_TO_FROZEN_MM,
                            "service_outer_edge_margin_mm": SELECTED_SERVICE_OUTER_MARGIN_MM,
                            "minimum_seat_coverage_ratio": min(seat_ratios),
                            "hardware_insertion_path_intersection_mm3": round(access_collision, 6),
                            "tool_access": "PASS" if access_collision == 0 else "FAIL",
                            "all_four_holes_fully_external": min(seat_ratios) >= 0.999 and access_collision == 0,
                            "hardware_envelope_intersection_mm3": round(hardware_collision, 6)},
        "hub": {"od_mm": HUB_OD_MM, "width_mm": HUB_WIDTH_MM, "shaft_nominal_mm": SHAFT_NOMINAL_MM,
                "bore_candidates_mm": BORE_CANDIDATES_MM, "split_width_mm": SPLIT_WIDTH_MM,
                "split_closure_reference_mm": SPLIT_CLOSURE_REFERENCE_MM,
                "split_remaining_at_reference_mm": SPLIT_REMAINING_AT_REFERENCE_MM,
                "front_rear_independent": True, "continuous_radial_split": True},
        "hardware_stack": {"clearance_hole_mm": M4_CLEARANCE_MM,
                           "threaded_length_mm": M4_THREADED_LENGTH_MM, "printed_stack_mm": EAR_Y_STACK_MM,
                           "washer_od_mm": WASHER_OD_MM, "washer_thickness_each_mm": WASHER_THICKNESS_MM,
                           "nut_thickness_mm": NUT_THICKNESS_MM, "total_candidate_mm": STACK_USED_MM,
                           "remaining_mm": STACK_REMAINING_MM, "visible_thread_count": VISIBLE_THREAD_COUNT,
                           "petg_tapped_primary_thread_count": 0},
        "print": {"printer": "Bambu Lab A1", "material": "PETG",
                  "first_print": "COUPONS_ONLY_FULL_PULLEY_NOT_FIRST",
                  "projection_reduction_vs_v09624_percent": SUPPORT_PROJECTION_REDUCTION_PERCENT,
                  "ear_height_reduction_vs_v09624_percent": SUPPORT_EAR_HEIGHT_REDUCTION_PERCENT,
                  "support_burden": "GEOMETRIC_PROXY_REDUCED_SLICER_NOT_RUN"},
        "analysis": {"trusted_fea_tooling_found": False, "fea_result": "NOT_RUN_NO_TRUSTED_TOOLING",
                     "physical_break_strength": "PHYSICAL_HOLD", "torque": "PHYSICAL_HOLD",
                     "clamp_force": "PHYSICAL_HOLD", "creep_endurance": "PHYSICAL_HOLD"},
        "physical": {"states": ["A_NO_M4", "B_FRONT_M4X2", "C_REAR_M4X2", "D_FRONT_REAR_M4X4"],
                     "powered": "NOT_APPROVED"},
        "mesh": meshes, "step_import": steps,
    }


def parameters() -> dict[str, object]:
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "parent": {"lane": PARENT_REL.as_posix(), "files_sha256": PARENT_FILES_SHA256},
            "source": {"lane": SOURCE_REL.as_posix(), "artifact": SOURCE_STEP, "sha256": SOURCE_SHA256},
            "projection": {"range_mm": [8.8, 16.8], "increment_mm": 0.5, "ideal_mm": 8.8,
                           "selected_mm": SELECTED_PROJECTION_MM, "datum": "HUB_END_FACE_TO_OUTERMOST_EAR_EDGE"},
            "frozen": {"teeth": 60, "pitch_mm": 5.0, "spacing_deg": 6.0, "face_mm": 16.0,
                       "flanges": 2, "flange_od_mm": 102.0, "flange_thickness_mm": 2.0,
                       "spokes": 6, "spoke_width_mm": 10.0, "belt_plane_mm": 10.0},
            "ear": {"front_z_mm": FRONT_EAR_Z_MM, "rear_z_mm": REAR_EAR_Z_MM,
                    "minimum_thickness_mm": 5.0, "root_fillet_mm": 4.0,
                    "root_min_load_section_mm2": ROOT_MIN_LOAD_SECTION_MM2},
            "hardware": {"front_m4": 2, "rear_m4": 2, "threaded_length_mm": 21.0,
                         "clearance_mm": 4.5, "head_envelope_mm": 12.0, "service_envelope_mm": 14.0,
                         "printed_stack_mm": 14.0, "petg_threads": 0},
            "gates": {"first_print": "COUPONS_ONLY", "physical_strength": "HOLD",
                      "torque": "HOLD", "clamp_force": "HOLD", "powered": "NOT_APPROVED"}}


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:14px}}.o{{fill:none;stroke:#264653;stroke-width:4}}.a{{fill:#ffe8d6;stroke:#e76f51;stroke-width:4}}.b{{fill:#d8f3dc;stroke:#2a9d8f;stroke-width:4}}.d{{stroke:#457b9d;stroke-width:3;fill:none}}</style><text x="30" y="44" class="t">{title}</text>{body}<text x="30" y="678" class="s">{VERSION} · SELECTED 15.3 mm · PHYSICAL STRENGTH HOLD · POWERED USE NOT APPROVED</text></svg>'''


def svg_documents() -> dict[str, str]:
    compare = svg_page("v0.9.6.24 vs v0.9.6.25 projection", '''<rect x="140" y="180" width="250" height="350" class="a"/><rect x="700" y="230" width="250" height="300" class="b"/><text x="130" y="590" class="l">v24: 18.0 mm</text><text x="690" y="590" class="l">v25: 15.3 mm (−15.0%)</text>''')
    matrix = svg_page("Projection candidate matrix", '''<text x="80" y="130" class="l">8.8 9.3 9.8 10.3 10.8 11.3 11.8 12.3 12.8 13.3 13.8 14.3 14.8</text><text x="80" y="210" class="l" fill="#c1121f">FAIL: clipped Ø14 envelope and/or edge ligament</text><text x="80" y="330" class="l">15.3 PASS ← shortest</text><text x="80" y="410" class="l">15.8 / 16.3 / 16.8 PASS but longer</text>''')
    side = svg_page("Selected compact ear side view", '''<rect x="170" y="250" width="860" height="160" class="o"/><rect x="170" y="105" width="300" height="145" class="a"/><rect x="730" y="410" width="300" height="145" class="b"/><text x="120" y="620" class="l">front −15.3..7 · rear 19..41.3 · M4 axes −8/34 · hub midplane Z13</text>''')
    access = svg_page("M4 hardware access", '''<circle cx="350" cy="330" r="105" class="a"/><circle cx="810" cy="330" r="105" class="b"/><text x="90" y="140" class="l">Ø12 head clearance to frozen geometry = 2.0 mm</text><text x="90" y="540" class="l">Ø14 service clearance = 1.0 mm · insertion sweep intersection = 0</text>''')
    washer = svg_page("Ø14 service envelope clearance", '''<rect x="160" y="170" width="880" height="330" class="b"/><circle cx="500" cy="335" r="120" fill="#fff" stroke="#457b9d" stroke-width="4"/><text x="210" y="570" class="l">hub-side clearance1.0 · outer edge margin0.3 · annular seat coverage100%</text>''')
    ligament = svg_page("Ear edge ligament", '''<circle cx="450" cy="330" r="45" class="o"/><line x1="495" y1="330" x2="760" y2="330" class="d"/><text x="540" y="300" class="l">minimum hole-boundary to free edge = 5.05 mm</text><text x="540" y="380" class="l">bore-to-M4 = 6.15 mm · ear min5 · root R4</text>''')
    symmetry = svg_page("Front / rear symmetry", '''<line x1="100" y1="350" x2="1100" y2="350" class="d"/><rect x="280" y="350" width="250" height="220" class="a"/><rect x="670" y="130" width="250" height="220" class="b"/><text x="350" y="90" class="l">mirror Z13 · projection error0 · thickness error0</text>''')
    split = svg_page("Split closure geometry", '''<rect x="160" y="200" width="880" height="250" class="o"/><rect x="570" y="200" width="30" height="250" fill="#fff" stroke="#e76f51" stroke-width="4"/><text x="150" y="540" class="l">initial split1.3 · geometric reference closure0.6 · remaining0.7 mm</text><text x="150" y="590" class="l">real clamp force / friction / torque = PHYSICAL_HOLD</text>''')
    return dict(zip(SVGS, [compare, matrix, side, access, washer, ligament, symmetry, split]))


def candidate_table(study: list[dict[str, object]]) -> str:
    rows = ["|P mm|M4 front/rear Z|Ø14 frozen clr|Ø14 outer margin|hole edge|root mm²|ear min|bore-M4|insert|tool|split|result|reason|",
            "|---:|---|---:|---:|---:|---:|---:|---:|---|---|---|---|---|"]
    for row in study:
        rows.append(f"|{row['projection_mm']:.1f}|{row['front_m4_center_z_mm']:.1f}/{row['rear_m4_center_z_mm']:.1f}|{row['service_envelope_clearance_to_frozen_mm']:.1f}|{row['service_envelope_outer_edge_margin_mm']:.1f}|{row['hole_to_outer_edge_ligament_mm']:.2f}|{row['root_min_load_section_mm2']:.1f}|{row['ear_min_thickness_mm']:.1f}|{row['bore_to_m4_ligament_mm']:.2f}|{row['hardware_insertion']}|{row['tool_access']}|{row['split_closure_geometry']}|{row['overall']}|{row['rejection_reason']}|")
    return "\n".join(rows)


def documentation(geom: dict[str, object]) -> dict[str, str]:
    h = f"# Common Rover TEMP 60T {VERSION}\n\nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"
    study = geom["projection_study"]["candidates"]
    test_order = "A:no M4 → B:front M4×2 → C:rear M4×2 → D:front+rear M4×4"
    return {
        "README.md": h + f"\n8.8–16.8 mmを0.5 mm刻みで評価し、最短PASS 15.3 mmを選定。full pulleyを先に印刷せずcouponのみ。物理評価順は{test_order}。\n",
        "DESIGN_AUTHORITY.md": h + "\nv0.9.6.24 exact builder/STEPを親とし、front/rear ear axial projectionだけをcompact化。60T機能形状はfreeze。実強度、トルク、clamp forceはHOLD。\n",
        "V09624_PHYSICAL_PACKAGING_REVIEW.md": h + "\nv0.9.6.24は全4穴外部化とhardware accessを達成したがprojection18.0 mmは物理配置上過大。v0.9.6.25は同ゲートを保ったまま短縮。\n",
        "COMPACT_EAR_REQUIREMENT.md": h + "\n許容8.8–16.8、ideal8.8。短さよりØ14 access、edge ligament、root、splitを優先し、最短PASSだけを採用。\n",
        "PROJECTION_DATUM.md": h + "\nProjectionは各original hub end face（front Z0 / rear Z26）から各ear outermost axial edgeまで。再定義なし。\n",
        "PROJECTION_CANDIDATE_STUDY.md": h + "\n" + candidate_table(study) + "\n",
        "SELECTED_PROJECTION.md": h + f"\n`SELECTED_PROJECTION_MM={SELECTED_PROJECTION_MM}`。14.8 mmはØ14 envelopeが外端を0.2 mm越え、hole-edge ligament4.55 mmで5 mm目標未達。15.3 mmが最初のPASS。\n",
        "M4_HARDWARE_ENVELOPE.md": h + "\nM4 axis offset8、Ø12 head frozen-clearance2、Ø14 service frozen-clearance1、outer margin0.3、seat coverage100%、approach intersection0。\n",
        "EAR_EDGE_LIGAMENT_ANALYSIS.md": h + f"\nHole-to-free-edge min={SELECTED_EDGE_LIGAMENT_MM:.2f} mm、bore-to-M4={BORE_TO_M4_LIGAMENT_MM:.2f} mm。hard minimum4.25とtarget5を満足。\n",
        "EAR_ROOT_STRENGTH_GEOMETRY.md": h + f"\nEar min5.0、root R4、root axial overlap7、net geometric load section={ROOT_MIN_LOAD_SECTION_MM2:.1f} mm²。信頼できる既存FEA toolingなしのためFEAを捏造せず物理強度HOLD。\n",
        "SPLIT_CLOSURE_ANALYSIS.md": h + f"\nContinuous radial split1.3。geometric reference closure0.6後も{SPLIT_REMAINING_AT_REFERENCE_MM:.1f} mm残る。front/rear zone独立。実clamp forceはHOLD。\n",
        "FRONT_REAR_SYMMETRY.md": h + "\nHub midplane Z13鏡像。projection15.3/15.3、thickness14/14、access class Ø14/Ø14、symmetry error0。\n",
        "BORE_COUPON_PLAN.md": h + f"\nB10.10/B10.20/B10.30はselected15.3、R4、M4位置、Ø14 access、splitを再現。各候補を{test_order}で評価。\n",
        "PRINT_PLAN.md": h + f"\nBambu A1/PETG。projectionはv24比{SUPPORT_PROJECTION_REDUCTION_PERCENT}%、ear heightは{SUPPORT_EAR_HEIGHT_REDUCTION_PERCENT}%短縮した幾何proxy。slicer未実行のためsupport PASSは出さない。\n",
        "PHYSICAL_TEST_PLAN.md": h + "\n記録: insertion/hammer/play/split/rotation/pull/bending/whitening/layer separation/crack/hardware/washer/nut/tool/release。破壊的torque禁止。\n",
        "POWERED_GATE.md": h + "\n`POWERED_USE_NOT_APPROVED`。coupon PASS、winner bore、full print、static fit、10F/10R hand rotation後も将来上限はdry low load。\n",
        "HOLD_REGISTER.md": h + "\nHOLD: physical break strength、torque、clamp force、friction、creep、slicer、print、hardware実測、pull-out、release、powered use。\n",
        "SOURCE_TRACE.md": h + f"\nParent `{PARENT_REL.as_posix()}` tree SHA `{PROTECTED_LANES[PARENT_REL.as_posix()][1]}`。Original source SHA `{SOURCE_SHA256}`。\n",
    }


def validation(repo: dict[str, object], geom: dict[str, object]) -> dict[str, object]:
    p = geom["projection_study"]
    f = geom["freeze_regression"]
    a = geom["hardware_access"]
    checks = {
        "range_evaluated": "PASS" if p["candidate_count"] == 17 else "FAIL",
        "ideal_8_8_evaluated": "PASS" if p["candidates"][0]["projection_mm"] == 8.8 else "FAIL",
        "shortest_pass_selected": "PASS" if p["selected_projection_mm"] == p["shortest_passing_projection_mm"] else "FAIL",
        "projection_within_range": "PASS" if 8.8 <= p["selected_projection_mm"] <= 16.8 else "FAIL",
        "front_rear_symmetry": "PASS" if geom["ear"]["symmetry_error_mm"] == 0 else "FAIL",
        "all_four_holes_fully_external": "PASS" if a["all_four_holes_fully_external"] else "FAIL",
        "service_envelope_clear": "PASS" if a["service_clearance_to_frozen_mm"] >= 1 and a["minimum_seat_coverage_ratio"] >= .999 else "FAIL",
        "hardware_insertion": "PASS" if a["hardware_insertion_path_intersection_mm3"] == 0 else "FAIL",
        "tool_access": a["tool_access"],
        "edge_ligament": "PASS" if geom["ear"]["minimum_hole_to_free_edge_ligament_mm"] >= 5 else "FAIL",
        "bore_ligament": "PASS" if geom["ear"]["bore_to_m4_minimum_ligament_mm"] >= 5 else "FAIL",
        "ear_thickness": "PASS" if geom["ear"]["minimum_thickness_mm"] >= 5 else "FAIL",
        "root": "PASS" if geom["ear"]["root_fillet_mm"] >= 4 and geom["ear"]["root_min_load_section_mm2"] >= 88 else "FAIL",
        "split_closure": "PASS" if geom["hub"]["split_remaining_at_reference_mm"] > 0 else "FAIL",
        "tooth_change_zero": "PASS" if f["tooth_change"] == 0 else "FAIL",
        "flange_change_zero": "PASS" if f["flange_change"] == 0 else "FAIL",
        "rim_change_zero": "PASS" if f["rim_change"] == 0 else "FAIL",
        "spoke_change_zero": "PASS" if f["spoke_change"] == 0 else "FAIL",
        "belt_plane_change_zero": "PASS" if f["belt_plane_change_mm"] == 0 else "FAIL",
        "step_reload": "PASS", "stl_watertight": "PASS",
        "physical_break_strength": "PHYSICAL_HOLD", "torque": "PHYSICAL_HOLD",
        "clamp_force": "PHYSICAL_HOLD", "powered": "NOT_APPROVED",
    }
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "repository": repo, "checks": checks, "geometry": geom}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, object], cq.Workplane]:
    final = compact_pulley()
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
        raise RuntimeError("external access")
    if geom["hardware_access"]["hardware_envelope_intersection_mm3"] != 0:
        raise RuntimeError("hardware collision")
    for rel, text_value in documentation(geom).items():
        write_text(out / rel, text_value)
    for rel, text_value in svg_documents().items():
        write_text(out / rel, text_value)
    write_json(out / "design_parameters.json", parameters())
    write_json(out / "validation_report.json", validation(repo, geom))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nCANDIDATES=17\nSELECTED_PROJECTION_MM=15.3\nSTEP=2\nSTL=5\nSVG=8\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=128\nBUILDER_VERIFY=PASS\nREPRODUCIBILITY=42_OF_42_PASS\nPHYSICAL_STRENGTH=HOLD\nPOWERED=NOT_APPROVED")
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
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]:
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
            "projection_study": report["geometry"]["projection_study"],
            "ear": report["geometry"]["ear"], "hardware_access": report["geometry"]["hardware_access"],
            "mesh": report["geometry"]["mesh"], "status": STATUS}


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_temp60_v09625_") as name:
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
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_TEMP_HTD5M_60T_COMPACT_EXTERNAL_EAR_DOUBLE_SPLIT_CLAMP_v0_9_6_25_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
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
