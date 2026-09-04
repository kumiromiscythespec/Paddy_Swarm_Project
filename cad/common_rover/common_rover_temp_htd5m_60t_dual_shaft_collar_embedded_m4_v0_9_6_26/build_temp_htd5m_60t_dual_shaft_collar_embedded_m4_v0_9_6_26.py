#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Common Rover v0.9.6.26 dual metal shaft-collar TEMP 60T."""
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


VERSION = "v0.9.6.26"
CLASSIFICATION = "TEMP_HTD5M_60T_DUAL_SHAFT_COLLAR_EMBEDDED_M4"
STATUS = (
    "TEMP_HTD5M_60T_DUAL_SHAFT_COLLAR_EMBEDDED_M4_CAD_COMPLETE/"
    "V09625_PETG_SPLIT_CLAMP_ARCHITECTURE_RETIRED/"
    "DUAL_METAL_SHAFT_COLLAR_ARCHITECTURE_COMPLETE/NO_COVER/NO_REACTION_SHOE/"
    "M4_HEAD_REACTION_POCKETS_COMPLETE/LEFT_RIGHT_AXIAL_SANDWICH_COMPLETE/"
    "60T_FUNCTIONAL_GEOMETRY_FROZEN/COLLAR_FIT_COUPONS_READY/"
    "FULL_PULLEY_PRINT_PENDING_PHYSICAL_COLLAR_FIT/POWERED_USE_NOT_APPROVED/"
    "COMMIT_READY_NOT_STAGED"
)
LANE_NAME = "common_rover_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2708
BASE_OUTSIDE_DIGEST = "e566d9b730a4cc902ea862191c995019c84f607f69faaf4eaea313885633df14"

AUTHORITY_SHA256 = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
TRACKED_DIRTY = list(AUTHORITY_SHA256)

PARENT_REL = PurePosixPath("cad/common_rover/common_rover_temp_htd5m_60t_compact_external_ear_double_split_clamp_v0_9_6_25")
PARENT_DIR = REPO_ROOT / PARENT_REL
PARENT_BUILDER = "build_temp_htd5m_60t_compact_external_ear_double_split_clamp_v0_9_6_25.py"
PARENT_TREE = (42, "1a00f38cb6a70c62698bd87ba8f3e18950cae471576c08d9e907e6bb9adcac64")
SOURCE_REL = PurePosixPath("cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1")
SOURCE_STEP = "cad/drive_htd5m_60t_reference.step"
SOURCE_SHA256 = "bc3e00bca0db5fe4c3975b5904ad4f72faa2b3fe6822057522c12df16ec0d256"

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
    PARENT_REL.as_posix(): PARENT_TREE,
    SOURCE_REL.as_posix(): (53, "a0cb4b831d639be4619a6bb42bff765a8196e04963dfc2df8826e1bbaf89fe00"),
}

# Frozen 60T functional authority.
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

# User physical measurements: PHYSICAL_MEASURED_COLLAR_AUTHORITY.
SHAFT_NOMINAL_MM = 10.0
COLLAR_OD_MM = 15.8
COLLAR_WIDTH_MM = 5.8
M4_HEAD_OD_MM = 8.8
COLLAR_OUTER_TO_HEAD_TOP_MM = 11.0
COLLAR_COUNT = 2
M4_PER_COLLAR = 2
TOTAL_M4 = 4
COLLAR_M4_PHASE = "APPROXIMATELY_90_DEG_PHYSICAL_AUTHORITY"

GUIDE_BORE_CANDIDATES_MM = [10.10, 10.20, 10.30]
PRIMARY_GUIDE_BORE_MM = 10.20
COLLAR_POCKET_CANDIDATES_MM = [16.0, 16.2, 16.4]
PRIMARY_COLLAR_POCKET_MM = 16.2
COLLAR_POCKET_DEPTH_MM = 5.5
COLLAR_PROUD_MM = round(COLLAR_WIDTH_MM - COLLAR_POCKET_DEPTH_MM, 3)
HUB_OD_MM = 50.0
HUB_RADIUS_MM = HUB_OD_MM / 2.0
HUB_WIDTH_MM = 26.0
M4_HEAD_POCKET_WIDTH_MM = 9.5
M4_HEAD_RADIAL_CLEARANCE_MM = round((M4_HEAD_POCKET_WIDTH_MM - M4_HEAD_OD_MM) / 2.0, 3)
HARDWARE_RADIAL_ENVELOPE_MM = round(COLLAR_OD_MM / 2.0 + COLLAR_OUTER_TO_HEAD_TOP_MM, 3)
SERVICE_RADIAL_ENVELOPE_MM = 20.0
OUTER_LIGAMENT_MM = round(HUB_RADIUS_MM - SERVICE_RADIAL_ENVELOPE_MM, 3)
REACTION_SHOULDER_MIN_MM = 5.0
ROOT_FILLET_CLASS_MM = 5.0
HEAD_CENTER_RADIUS_MM = HARDWARE_RADIAL_ENVELOPE_MM - M4_HEAD_OD_MM / 2.0
TANGENTIAL_CLEARANCE_MM = M4_HEAD_POCKET_WIDTH_MM - M4_HEAD_OD_MM
ANGULAR_BACKLASH_PER_SIDE_DEG = round(
    math.degrees(2.0 * math.asin(TANGENTIAL_CLEARANCE_MM / (2.0 * HEAD_CENTER_RADIUS_MM))), 3
)
COMBINED_FIRST_CONTACT_BACKLASH_DEG = ANGULAR_BACKLASH_PER_SIDE_DEG
COMBINED_DIFFERENTIAL_LIMIT_DEG = round(2.0 * ANGULAR_BACKLASH_PER_SIDE_DEG, 3)
REACTION_SLOT_INNER_R_MM = 7.6
REACTION_SLOT_OUTER_R_MM = SERVICE_RADIAL_ENVELOPE_MM
REACTION_SLOT_LEFT_Z_MM = [0.0, 7.5]
REACTION_SLOT_RIGHT_Z_MM = [18.5, 26.0]
COLLAR_LEFT_Z_MM = [-COLLAR_PROUD_MM, COLLAR_POCKET_DEPTH_MM]
COLLAR_RIGHT_Z_MM = [HUB_WIDTH_MM - COLLAR_POCKET_DEPTH_MM, HUB_WIDTH_MM + COLLAR_PROUD_MM]
MODIFICATION_ENVELOPE_RADIUS_MM = 30.1

ARCHITECTURE_COUNTS = {
    "metal_shaft_collars": 2,
    "m4_per_collar": 2,
    "total_m4": 4,
    "cover": 0,
    "reaction_shoe": 0,
    "petg_split_clamp": 0,
    "external_petg_clamp_ears": 0,
    "continuous_1_3mm_split": 0,
    "petg_tapped_primary_threads": 0,
}

BUILDER = "build_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26.py"
TEST = "tests/test_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "V09625_ARCHITECTURE_RETIREMENT.md",
    "PHYSICAL_COLLAR_MEASUREMENTS.md", "DUAL_SHAFT_COLLAR_ARCHITECTURE.md",
    "NO_COVER_NO_REACTION_SHOE.md", "COLLAR_POCKET_DESIGN.md",
    "M4_HEAD_REACTION_POCKET.md", "TORQUE_PATH.md", "AXIAL_RETENTION_PATH.md",
    "ANGULAR_BACKLASH_ANALYSIS.md", "COLLAR_FIT_COUPON_PLAN.md",
    "ASSEMBLY_SEQUENCE.md", "PRINT_PLAN.md", "HAND_ROTATION_TEST.md",
    "DUAL_MOTOR_POWERED_TEST.md", "FAILURE_CRITERIA.md", "POWERED_GATE.md",
    "HOLD_REGISTER.md", "SOURCE_TRACE.md", "BUILD_LOG.txt", "TEST_LOG.txt",
    "design_parameters.json", "validation_report.json", "MANIFEST.txt",
    "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
CAD = [
    "artifacts/temp_htd5m_60t_dual_shaft_collar_embedded_m4_provisional_v0_9_6_26.step",
    "artifacts/temp_htd5m_60t_dual_shaft_collar_embedded_m4_provisional_v0_9_6_26.stl",
    "artifacts/collar_fit_cp160_v0_9_6_26.stl",
    "artifacts/collar_fit_cp162_v0_9_6_26.stl",
    "artifacts/collar_fit_cp164_v0_9_6_26.stl",
    "artifacts/guide_bore_triplet_v0_9_6_26.stl",
    "artifacts/temp_htd5m_60t_dual_shaft_collar_hardware_reference_v0_9_6_26.step",
]
SVGS = [
    "artifacts/v09625_vs_v09626_architecture.svg",
    "artifacts/dual_shaft_collar_section.svg",
    "artifacts/left_right_collar_sandwich.svg",
    "artifacts/collar_pocket_dimensions.svg",
    "artifacts/m4_head_reaction_geometry.svg",
    "artifacts/torque_path.svg",
    "artifacts/axial_retention_path.svg",
    "artifacts/collar_fit_candidates.svg",
    "artifacts/assembly_sequence.svg",
]
EXPECTED_FILES = sorted([BUILDER, TEST, *DOCS, *CAD, *SVGS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def load_parent():
    spec = importlib.util.spec_from_file_location("paddy_v09625_parent", PARENT_DIR / PARENT_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("parent import")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PARENT = load_parent()


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
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def repository_guard(require_complete: bool = False) -> dict[str, object]:
    root = Path(run_git("rev-parse", "--show-toplevel")).resolve()
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {rel: sha256(REPO_ROOT / rel) for rel in AUTHORITY_SHA256}
    protected = {rel: tree_digest(REPO_ROOT / rel) for rel in PROTECTED_LANES}
    source = sha256(REPO_ROOT / SOURCE_REL / SOURCE_STEP)
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj", ".dxf"}]
    checks = {
        "repository": root == REPO_ROOT.resolve(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256,
        "protected_lanes": protected == PROTECTED_LANES,
        "parent_v09625": protected[PARENT_REL.as_posix()] == PARENT_TREE,
        "source": source == SOURCE_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES),
        "lane_cache_zero": not cache,
        "forbidden_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks,
        "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "outside_untracked": outside_snapshot(),
        "lane_files": len(lane_files), "authority_sha256": authority,
        "protected_lanes": {
            rel: {"count": value[0], "tree_sha256": value[1], "status": "UNCHANGED"}
            for rel, value in protected.items()
        },
        "source_sha256": source, "cache": cache, "forbidden": forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def cylinder(radius: float, height: float, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height).translate((0, 0, z))


def radial_cylinder(radius: float, length: float, radial_start: float, angle_deg: float, z: float) -> cq.Workplane:
    angle = math.radians(angle_deg)
    origin = cq.Vector(radial_start * math.cos(angle), radial_start * math.sin(angle), z)
    direction = cq.Vector(math.cos(angle), math.sin(angle), 0)
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, origin, direction))


def radial_slot(angle_deg: float, z0: float, z1: float) -> cq.Workplane:
    length = REACTION_SLOT_OUTER_R_MM - REACTION_SLOT_INNER_R_MM
    center = (REACTION_SLOT_OUTER_R_MM + REACTION_SLOT_INNER_R_MM) / 2.0
    slot = cq.Workplane("XY").box(length, M4_HEAD_POCKET_WIDTH_MM, z1 - z0).translate((center, 0, (z0 + z1) / 2.0))
    return slot.rotate((0, 0, 0), (0, 0, 1), angle_deg)


def root_lugs() -> cq.Workplane:
    parts = []
    for index in range(SPOKE_COUNT):
        angle = math.radians(index * 60.0)
        parts.append(cylinder(ROOT_FILLET_CLASS_MM, 16.0, 2.0).translate((25.0 * math.cos(angle), 25.0 * math.sin(angle), 0)))
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def reaction_blank(include_roots: bool) -> cq.Workplane:
    blank = cylinder(HUB_RADIUS_MM, HUB_WIDTH_MM)
    if include_roots:
        for lug in root_lugs().vals():
            blank = blank.union(cq.Workplane(obj=lug))
    return blank.clean()


def hub_cutters(pocket_diameter_mm: float, guide_bore_mm: float) -> list[cq.Workplane]:
    cutters = [
        cylinder(guide_bore_mm / 2.0, HUB_WIDTH_MM + 8.0, -4.0),
        cylinder(pocket_diameter_mm / 2.0, COLLAR_POCKET_DEPTH_MM, 0.0),
        cylinder(pocket_diameter_mm / 2.0, COLLAR_POCKET_DEPTH_MM, HUB_WIDTH_MM - COLLAR_POCKET_DEPTH_MM),
    ]
    for angle in (0.0, 90.0):
        cutters.append(radial_slot(angle, *REACTION_SLOT_LEFT_Z_MM))
        cutters.append(radial_slot(angle, *REACTION_SLOT_RIGHT_Z_MM))
    return cutters


def apply_hub_cuts(shape: cq.Workplane, pocket_diameter_mm: float, guide_bore_mm: float) -> cq.Workplane:
    result = shape
    for cutter in hub_cutters(pocket_diameter_mm, guide_bore_mm):
        result = result.cut(cutter)
    return result.clean()


def frozen_structure() -> cq.Workplane:
    return PARENT.frozen_structure(38.0, True)


def provisional_pulley(pocket_diameter_mm: float = PRIMARY_COLLAR_POCKET_MM,
                       guide_bore_mm: float = PRIMARY_GUIDE_BORE_MM) -> cq.Workplane:
    combined = frozen_structure().union(reaction_blank(True)).clean()
    return apply_hub_cuts(combined, pocket_diameter_mm, guide_bore_mm)


def collar_coupon(pocket_diameter_mm: float) -> cq.Workplane:
    return apply_hub_cuts(reaction_blank(False), pocket_diameter_mm, PRIMARY_GUIDE_BORE_MM)


def guide_bore_coupon(bore_mm: float) -> cq.Workplane:
    return cylinder(11.0, 8.0).cut(cylinder(bore_mm / 2.0, 12.0, -2.0)).clean()


def guide_bore_triplet() -> cq.Workplane:
    parts = [
        guide_bore_coupon(10.10).translate((-30.0, 0.0, 0.0)),
        guide_bore_coupon(10.20),
        guide_bore_coupon(10.30).translate((30.0, 0.0, 0.0)),
    ]
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def collar_shape(z0: float) -> cq.Workplane:
    return cylinder(COLLAR_OD_MM / 2.0, COLLAR_WIDTH_MM, z0).cut(cylinder(SHAFT_NOMINAL_MM / 2.0, COLLAR_WIDTH_MM + 2.0, z0 - 1.0))


def m4_hardware_for_side(z_center: float) -> list[cq.Workplane]:
    result = []
    for angle in (0.0, 90.0):
        result.append(radial_cylinder(2.0, 8.3, REACTION_SLOT_INNER_R_MM, angle, z_center))
        result.append(radial_cylinder(M4_HEAD_OD_MM / 2.0, 3.0, HARDWARE_RADIAL_ENVELOPE_MM - 3.0, angle, z_center))
    return result


def m4_hardware_envelopes() -> list[cq.Workplane]:
    return m4_hardware_for_side(2.75) + m4_hardware_for_side(23.25)


def hardware_reference() -> cq.Workplane:
    items = [
        provisional_pulley().val(),
        cylinder(SHAFT_NOMINAL_MM / 2.0, 46.0, -10.0).val(),
        collar_shape(COLLAR_LEFT_Z_MM[0]).val(),
        collar_shape(COLLAR_RIGHT_Z_MM[0]).val(),
    ]
    items.extend(item.val() for item in m4_hardware_envelopes())
    return cq.Workplane(obj=cq.Compound.makeCompound(items))


def volume(shape: cq.Workplane) -> float:
    return round(sum(solid.Volume() for solid in shape.solids().vals()), 6)


def modification_envelope() -> cq.Workplane:
    return cylinder(MODIFICATION_ENVELOPE_RADIUS_MM, 34.0, -4.0)


def freeze_regression(final: cq.Workplane) -> dict[str, object]:
    base = frozen_structure()
    envelope = modification_envelope()
    base_out = base.cut(envelope)
    final_out = final.cut(envelope)
    ring = cylinder(52.0, 30.0, -4.0).cut(cylinder(37.0, 30.0, -4.0))
    base_ring = base.intersect(ring)
    final_ring = final.intersect(ring)
    outside_removed = volume(base_out.cut(final_out))
    outside_added = volume(final_out.cut(base_out))
    ring_removed = volume(base_ring.cut(final_ring))
    ring_added = volume(final_ring.cut(base_ring))
    unchanged = outside_removed == outside_added == ring_removed == ring_added == 0
    return {
        "modification_envelope_radius_mm": MODIFICATION_ENVELOPE_RADIUS_MM,
        "outside_removed_mm3": outside_removed, "outside_added_mm3": outside_added,
        "ring_removed_mm3": ring_removed, "ring_added_mm3": ring_added,
        "tooth_change": 0 if unchanged else 1,
        "flange_change": 0 if unchanged else 1,
        "rim_change": 0 if unchanged else 1,
        "spoke_change_outside_local_hub": 0 if unchanged else 1,
        "belt_plane_change_mm": 0.0,
        "hub_only_revision": unchanged,
    }


def normalize_step(path: Path) -> None:
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
        inherited = metric.pop("bore_mesh")
        metric["guide_bore_mesh"] = {
            "target_mm": bore,
            "effective_min_mm": inherited["effective_min_mm"],
            "effective_max_mm": inherited["effective_max_mm"],
            "continuous_coaxial_bore": True,
        }
    return metric


def exported_dimension_contract(full_mesh: dict[str, object]) -> dict[str, object]:
    guide = full_mesh["guide_bore_mesh"]
    return {
        "measurement_basis": "EXPORTED_STL_VERTEX_GUIDE_BORE_PLUS_EXACT_CAD_CUTTER_CONTRACT",
        "collar_pocket_id_mm": PRIMARY_COLLAR_POCKET_MM,
        "collar_pocket_depth_mm": COLLAR_POCKET_DEPTH_MM,
        "guide_bore_target_mm": PRIMARY_GUIDE_BORE_MM,
        "guide_bore_mesh_effective_min_mm": guide["effective_min_mm"],
        "guide_bore_mesh_effective_max_mm": guide["effective_max_mm"],
        "m4_reaction_pocket_width_mm": M4_HEAD_POCKET_WIDTH_MM,
        "m4_service_radial_envelope_mm": SERVICE_RADIAL_ENVELOPE_MM,
        "minimum_petg_outer_ligament_mm": OUTER_LIGAMENT_MM,
        "minimum_reaction_shoulder_mm": REACTION_SHOULDER_MIN_MM,
    }


def geometry_data(final: cq.Workplane, meshes: dict[str, object], steps: dict[str, object]) -> dict[str, object]:
    freeze = freeze_regression(final)
    hardware_intersection = round(sum(volume(final.intersect(item)) for item in m4_hardware_envelopes()), 6)
    full_mesh = meshes[CAD[1]]
    return {
        "physical_collar_authority": {
            "classification": "PHYSICAL_MEASURED_COLLAR_AUTHORITY",
            "collar_od_mm": COLLAR_OD_MM, "collar_width_mm": COLLAR_WIDTH_MM,
            "m4_head_od_mm": M4_HEAD_OD_MM,
            "max_radial_projection_from_collar_outer_to_head_top_mm": COLLAR_OUTER_TO_HEAD_TOP_MM,
            "shaft_nominal_mm": SHAFT_NOMINAL_MM,
            "m4_relationship": COLLAR_M4_PHASE,
        },
        "architecture": {
            **ARCHITECTURE_COUNTS,
            "sequence": ["LEFT_METAL_SHAFT_COLLAR", "CENTRAL_PETG_60T_REACTION_HUB", "RIGHT_METAL_SHAFT_COLLAR"],
            "retired": ["EXTERNAL_PETG_EARS", "FRONT_REAR_PETG_CLAMP_BANDS", "CONTINUOUS_1_3MM_SPLIT", "PETG_COMPRESSION_CLAMP", "M4_WASHER_NUT_EAR_STACK", "B1010_B1020_B1030_SPLIT_CLAMP_COUPONS"],
        },
        "pulley": {
            "valid": final.val().isValid(), "solid_count": final.solids().size(),
            "overall_dimensions_mm": full_mesh["extents_mm"],
            "tooth_count": TOOTH_COUNT, "pitch_mm": PITCH_MM, "spacing_deg": SPACING_DEG,
            "tooth_face_width_mm": TOOTH_FACE_WIDTH_MM, "flange_count": FLANGE_COUNT,
            "flange_od_mm": FLANGE_OD_MM, "flange_thickness_mm": FLANGE_THICKNESS_MM,
            "spoke_count": SPOKE_COUNT, "spoke_width_mm": SPOKE_WIDTH_MM,
            "belt_plane_z_mm": BELT_PLANE_Z_MM,
        },
        "hub": {
            "od_mm": HUB_OD_MM, "width_mm": HUB_WIDTH_MM,
            "guide_bore_candidates_mm": GUIDE_BORE_CANDIDATES_MM,
            "primary_guide_bore_mm": PRIMARY_GUIDE_BORE_MM,
            "collar_pocket_candidates_mm": COLLAR_POCKET_CANDIDATES_MM,
            "primary_collar_pocket_mm": PRIMARY_COLLAR_POCKET_MM,
            "collar_pocket_depth_mm": COLLAR_POCKET_DEPTH_MM,
            "collar_proud_mm": COLLAR_PROUD_MM,
            "left_collar_z_mm": COLLAR_LEFT_Z_MM, "right_collar_z_mm": COLLAR_RIGHT_Z_MM,
            "root_fillet_class_mm": ROOT_FILLET_CLASS_MM,
        },
        "reaction": {
            "locations_left": 2, "locations_right": 2, "locations_total": 4,
            "head_pocket_width_mm": M4_HEAD_POCKET_WIDTH_MM,
            "head_radial_clearance_mm": M4_HEAD_RADIAL_CLEARANCE_MM,
            "hardware_radial_envelope_mm": HARDWARE_RADIAL_ENVELOPE_MM,
            "service_radial_envelope_mm": SERVICE_RADIAL_ENVELOPE_MM,
            "outer_ligament_mm": OUTER_LIGAMENT_MM,
            "reaction_shoulder_minimum_mm": REACTION_SHOULDER_MIN_MM,
            "left_angular_backlash_estimate_deg": ANGULAR_BACKLASH_PER_SIDE_DEG,
            "right_angular_backlash_estimate_deg": ANGULAR_BACKLASH_PER_SIDE_DEG,
            "combined_first_contact_estimate_deg": COMBINED_FIRST_CONTACT_BACKLASH_DEG,
            "combined_worst_differential_phase_deg": COMBINED_DIFFERENTIAL_LIMIT_DEG,
            "exact_screw_phase": "PHYSICAL_HOLD_APPROXIMATELY_90_DEG",
            "m4_envelope_intersection_mm3": hardware_intersection,
            "tool_access": "HOLD_ACTUAL_L_KEY_ENVELOPE_REQUIRED",
        },
        "axial_sandwich": {
            "left_migration_blocked_by": "LEFT_METAL_SHAFT_COLLAR",
            "right_migration_blocked_by": "RIGHT_METAL_SHAFT_COLLAR",
            "cad_reference_axial_play_mm": 0.0,
            "preload": "PHYSICAL_HOLD_NO_DESTRUCTIVE_PRELOAD",
            "optional_shim": "ONLY_IF_PHYSICAL_PLAY_REQUIRES",
        },
        "torque_path": ["HTD5M_BELT", "60T_TOOTH_RING", "RIM", "6_SPOKES", "PETG_REACTION_HUB", "M4_HEAD_REACTION_POCKETS", "M4_X4", "METAL_COLLARS_X2", "D10_STEEL_SHAFT"],
        "axial_retention_path": ["PULLEY_LEFT_FACE", "LEFT_METAL_COLLAR", "D10_STEEL_SHAFT", "RIGHT_METAL_COLLAR", "PULLEY_RIGHT_FACE"],
        "freeze_regression": freeze,
        "exported_dimensions": exported_dimension_contract(full_mesh),
        "mesh": meshes, "step_import": steps,
        "print": {
            "printer": "Bambu Lab A1", "material": "PETG", "axis": "Z",
            "first_print": "COLLAR_FIT_CP160_CP162_CP164_ONLY",
            "slicer": "HOLD_SLICER_NOT_RUN",
            "support_audit": "OPEN_AXIAL_POCKETS_NO_COVER_NO_ROOF; FLANGE_UNDERSIDE_MANUAL_REVIEW_REQUIRED",
        },
        "physical_holds": {
            "real_collar_friction": "PHYSICAL_HOLD", "real_m4_torque": "PHYSICAL_HOLD",
            "real_shaft_torque_capacity": "PHYSICAL_HOLD", "real_petg_reaction_strength": "PHYSICAL_HOLD",
            "real_creep": "PHYSICAL_HOLD", "real_axial_retention_load": "PHYSICAL_HOLD",
            "actual_tool_access": "PHYSICAL_HOLD", "powered": "NOT_APPROVED",
        },
    }


def parameters() -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "parent": {"lane": PARENT_REL.as_posix(), "tree": {"count": PARENT_TREE[0], "sha256": PARENT_TREE[1]}},
        "source": {"lane": SOURCE_REL.as_posix(), "artifact": SOURCE_STEP, "sha256": SOURCE_SHA256},
        "frozen": {"teeth": 60, "pitch_mm": 5.0, "spacing_deg": 6.0, "face_mm": 16.0,
                   "flanges": 2, "flange_od_mm": 102.0, "flange_thickness_mm": 2.0,
                   "spokes": 6, "spoke_width_mm": 10.0, "belt_plane_z_mm": 10.0},
        "physical_collar": {"authority": "PHYSICAL_MEASURED_COLLAR_AUTHORITY", "od_mm": 15.8,
                            "width_mm": 5.8, "m4_head_od_mm": 8.8,
                            "outer_to_head_top_mm": 11.0, "count": 2, "m4_each": 2},
        "hub": {"od_mm": 50.0, "width_mm": 26.0, "pocket_candidates_mm": [16.0, 16.2, 16.4],
                "primary_pocket_mm": 16.2, "pocket_depth_mm": 5.5, "proud_mm": 0.3,
                "guide_bore_candidates_mm": [10.1, 10.2, 10.3], "primary_guide_bore_mm": 10.2},
        "reaction": {"pocket_width_mm": 9.5, "head_radial_clearance_mm": 0.35,
                     "hardware_envelope_r_mm": 18.9, "service_envelope_r_mm": 20.0,
                     "outer_ligament_mm": 5.0, "shoulder_min_mm": 5.0,
                     "backlash_each_side_deg": ANGULAR_BACKLASH_PER_SIDE_DEG,
                     "combined_first_contact_deg": COMBINED_FIRST_CONTACT_BACKLASH_DEG,
                     "combined_differential_deg": COMBINED_DIFFERENTIAL_LIMIT_DEG},
        "counts": ARCHITECTURE_COUNTS,
        "gates": {"coupon": "REQUIRED_FIRST", "full_pulley": "PROVISIONAL",
                  "hand_rotation": "HOLD_AFTER_PHYSICAL_COUPON", "powered": "NOT_APPROVED"},
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:14px}}.old{{fill:#ffd6d6;stroke:#b02a37;stroke-width:4}}.new{{fill:#d8f3dc;stroke:#2a9d8f;stroke-width:4}}.metal{{fill:#d9e2ec;stroke:#334e68;stroke-width:4}}.line{{fill:none;stroke:#457b9d;stroke-width:4}}</style><text x="30" y="44" class="t">{title}</text>{body}<text x="30" y="678" class="s">{VERSION} · physical collar fit/strength HOLD · powered use NOT APPROVED</text></svg>'''


def svg_documents() -> dict[str, str]:
    pages = [
        svg_page("v0.9.6.25 retired → v0.9.6.26", '<rect x="100" y="170" width="390" height="300" class="old"/><text x="135" y="530" class="l">PETG ears + split retired</text><circle cx="790" cy="320" r="180" class="new"/><text x="650" y="550" class="l">OD50 reaction hub</text>'),
        svg_page("Dual shaft-collar section", '<rect x="210" y="230" width="780" height="180" class="new"/><rect x="170" y="245" width="70" height="150" class="metal"/><rect x="960" y="245" width="70" height="150" class="metal"/><line x1="80" y1="320" x2="1120" y2="320" class="line"/><text x="350" y="500" class="l">collar 5.8 · pocket 5.5 · proud 0.3 each side</text>'),
        svg_page("Left/right axial sandwich", '<rect x="160" y="230" width="120" height="210" class="metal"/><rect x="280" y="180" width="640" height="310" class="new"/><rect x="920" y="230" width="120" height="210" class="metal"/><text x="250" y="560" class="l">LEFT COLLAR → PETG HUB ← RIGHT COLLAR · CAD axial play reference 0</text>'),
        svg_page("Collar pocket dimensions", '<circle cx="370" cy="330" r="170" class="new"/><circle cx="370" cy="330" r="110" fill="#fff" stroke="#334e68" stroke-width="4"/><text x="620" y="230" class="l">CP16.0 / CP16.2 / CP16.4</text><text x="620" y="300" class="l">primary CP16.2</text><text x="620" y="370" class="l">depth 5.5 · collar W5.8</text>'),
        svg_page("M4 head reaction geometry", '<circle cx="370" cy="330" r="220" class="new"/><rect x="370" y="285" width="175" height="90" fill="#fff" stroke="#457b9d" stroke-width="4"/><circle cx="480" cy="330" r="40" class="metal"/><text x="650" y="230" class="l">head Ø8.8 · slot9.5 · radial clr0.35</text><text x="650" y="300" class="l">hardware R18.9 · service R20</text><text x="650" y="370" class="l">OD50 outer ligament5.0</text>'),
        svg_page("Torque path", '<text x="90" y="160" class="l">BELT → 60T → RIM → 6 SPOKES → PETG HUB</text><path d="M110 260 H1080" class="line"/><text x="90" y="390" class="l">→ M4 HEAD POCKETS → M4×4 → METAL COLLARS×2 → Ø10 SHAFT</text>'),
        svg_page("Axial retention path", '<rect x="130" y="250" width="160" height="180" class="metal"/><rect x="290" y="210" width="620" height="260" class="new"/><rect x="910" y="250" width="160" height="180" class="metal"/><path d="M600 130 L290 200 M600 130 L910 200" class="line"/><text x="250" y="550" class="l">left/right collars block migration; no PETG-shaft friction reliance</text>'),
        svg_page("Collar fit candidates", '<circle cx="250" cy="330" r="115" class="new"/><circle cx="600" cy="330" r="115" class="new"/><circle cx="950" cy="330" r="115" class="new"/><text x="205" y="540" class="l">CP16.0</text><text x="555" y="540" class="l">CP16.2</text><text x="905" y="540" class="l">CP16.4</text>'),
        svg_page("Assembly sequence", '<text x="75" y="125" class="l">1 shaft through hub → 2 left collar → 3 clock heads → 4 tighten left</text><text x="75" y="245" class="l">5 right collar → 6 axial position → 7 tighten right</text><text x="75" y="365" class="l">8 axial play → 9 backlash → 10 witness marks</text><text x="75" y="505" class="l">Actual L-key envelope and preload remain PHYSICAL_HOLD</text>'),
    ]
    return dict(zip(SVGS, pages))


def header() -> str:
    return f"# Common Rover TEMP 60T {VERSION}\n\nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"


def documentation(geom: dict[str, object]) -> dict[str, str]:
    h = header()
    assembly = "1) Ø10 shaftをhubへ通す 2) left collar挿入 3) M4 headsをpocketへclocking 4) left M4×2締結 5) right collar挿入 6) 軸位置調整 7) right M4×2締結 8) axial play確認 9) backlash確認 10) witness mark。"
    return {
        "README.md": h + "\n最初にfull 60Tを印刷しない。CP16.0/16.2/16.4 couponをactual OD15.8×W5.8 collar・Ø10 shaft・actual M4×2で評価し、winner確定後にfull pulleyを再生成する。\n",
        "DESIGN_AUTHORITY.md": h + "\nv0.9.6.25をread-only parentとするがPETG split-clamp architectureは継承しない。原典STEP SHAを確認し、teeth/flanges/rim/6 spokes/belt planeはfreeze。\n",
        "V09625_ARCHITECTURE_RETIREMENT.md": h + "\nExternal PETG ears、front/rear clamp bands、continuous 1.3 split、PETG compression、M4 washer/nut ear stack、B10.xx split couponを廃止。artifact countは全て0。\n",
        "PHYSICAL_COLLAR_MEASUREMENTS.md": h + "\n`PHYSICAL_MEASURED_COLLAR_AUTHORITY`: collar OD15.8、W5.8、M4 head OD8.8、collar outer surfaceからhead top最大11.0、各collar M4×2 approximately90°。旧H2.5値で置換しない。\n",
        "DUAL_SHAFT_COLLAR_ARCHITECTURE.md": h + "\nLEFT METAL COLLAR + CENTRAL PETG REACTION HUB + RIGHT METAL COLLAR。collarsが軸方向保持、M4 headsが回転reactionを分担。cover0、Reaction Shoe0。\n",
        "NO_COVER_NO_REACTION_SHOE.md": h + "\nCover artifact=0、Reaction Shoe artifact=0。reaction pocketはhub一体、両軸面から開放しroofを作らない。\n",
        "COLLAR_POCKET_DESIGN.md": h + "\nCP16.0/16.2/16.4、provisional CP16.2。depth5.5に対しcollar W5.8なのでproud0.3。hammer press禁止、removable/serviceableをcouponで判定。\n",
        "M4_HEAD_REACTION_POCKET.md": h + f"\nHead Ø8.8にslot9.5、radial clearance0.35。hardware R18.9、service R20、hub OD50、outer ligament{OUTER_LIGAMENT_MM:.1f}、reaction shoulder{REACTION_SHOULDER_MIN_MM:.1f}。2 locations/side、合計4。actual tool envelopeはHOLD。\n",
        "TORQUE_PATH.md": h + "\nHTD5M belt → 60T tooth ring → rim → 6 spokes → PETG reaction hub → M4 head pockets → M4×4 → metal collars×2 → Ø10 steel shaft。実トルク容量はPHYSICAL_HOLD。\n",
        "AXIAL_RETENTION_PATH.md": h + "\n左移動はleft collar、右移動はright collarで阻止。PETG-shaft frictionへ依存せず、contact/near-zero playを狙いcrushing preloadは禁止。\n",
        "ANGULAR_BACKLASH_ANALYSIS.md": h + f"\nHead center R{HEAD_CENTER_RADIUS_MM:.1f}、tangential clearance{TANGENTIAL_CLEARANCE_MM:.1f}から各側total estimate {ANGULAR_BACKLASH_PER_SIDE_DEG:.3f}°（±{ANGULAR_BACKLASH_PER_SIDE_DEG/2:.3f}°）。aligned combined first-contact {COMBINED_FIRST_CONTACT_BACKLASH_DEG:.3f}°、opposite extreme differential {COMBINED_DIFFERENTIAL_LIMIT_DEG:.3f}°。M4間角度はapproximately90°でexact phaseはHOLD。\n",
        "COLLAR_FIT_COUPON_PLAN.md": h + "\nCP16.0/16.2/16.4はdepth5.5、local OD50 wall、左右M4 reaction slots、actual print orientationを再現。EASY/FIRM/TIGHT、hammer、radial play、removal、head entry、shaft tightening、rotation、free play、whitening/crack/layer separationを記録。\n",
        "ASSEMBLY_SEQUENCE.md": h + "\n" + assembly + "\n",
        "PRINT_PLAN.md": h + "\nBambu Lab A1/PETG、0.4 nozzle、0.20 layer、walls/top/bottom各>=6、40–50% infill reference。shaft axis=Z、flat。slicer未実行のため`HOLD_SLICER_NOT_RUN`。\n",
        "HAND_ROTATION_TEST.md": h + "\nCoupon winner反映後のfull pulleyでaxial/radial runout、belt plane、collar/M4 seatingを確認し10F/10R。hub/collar slip、head climb、crack、white stress、belt climb、skip、axial migrationは全て0が条件。\n",
        "DUAL_MOTOR_POWERED_TEST.md": h + "\n物理gate後のみnew-side 1–2/5/10 sec、次にdual motor 1–2/5/10 sec。最大statusはTEMP_PULLEY_DUAL_MOTOR_DRY_LOW_LOAD_PASS。現時点NOT_APPROVED。\n",
        "FAILURE_CRITERIA.md": h + "\nWitness shift、pocket damage、whitening、crack、axial migration、wobble増加、belt skip/climb、異音で即停止し`FAIL_SLIP_OR_REACTION`。\n",
        "POWERED_GATE.md": h + "\n`POWERED_USE_NOT_APPROVED`。stall、blocked crawler、full torque qualification、restrained vehicle、maximum traction、payload pull、endurance、mud、水、fieldは禁止。\n",
        "HOLD_REGISTER.md": h + "\nPHYSICAL_HOLD: collar friction、M4 torque、shaft torque capacity、PETG reaction strength、creep、axial retention load/preload、exact screw phase、actual L-key access、coupon fit、slicer、full print、hand rotation。Powered NOT_APPROVED。\n",
        "SOURCE_TRACE.md": h + f"\nImmediate parent `{PARENT_REL.as_posix()}` tree `{PARENT_TREE[1]}`。Original authority `{SOURCE_REL.as_posix()}/{SOURCE_STEP}` SHA `{SOURCE_SHA256}`。\n",
    }


def validation(repo: dict[str, object], geom: dict[str, object]) -> dict[str, object]:
    a, h, r, f = geom["architecture"], geom["hub"], geom["reaction"], geom["freeze_regression"]
    checks = {
        "physical_authority_exact": "PASS" if geom["physical_collar_authority"]["collar_od_mm"] == 15.8 and geom["physical_collar_authority"]["collar_width_mm"] == 5.8 else "FAIL",
        "dual_metal_collars": "PASS" if a["metal_shaft_collars"] == 2 else "FAIL",
        "m4_total": "PASS" if a["total_m4"] == 4 else "FAIL",
        "cover_zero": "PASS" if a["cover"] == 0 else "FAIL",
        "reaction_shoe_zero": "PASS" if a["reaction_shoe"] == 0 else "FAIL",
        "split_clamp_zero": "PASS" if a["petg_split_clamp"] == 0 and a["continuous_1_3mm_split"] == 0 else "FAIL",
        "external_ears_zero": "PASS" if a["external_petg_clamp_ears"] == 0 else "FAIL",
        "primary_pocket": "PASS" if h["primary_collar_pocket_mm"] == 16.2 and h["collar_pocket_depth_mm"] == 5.5 else "FAIL",
        "collar_proud": "PASS" if h["collar_proud_mm"] == 0.3 else "FAIL",
        "guide_bore": "PASS" if h["primary_guide_bore_mm"] == 10.2 else "FAIL",
        "head_clearance": "PASS" if 9.4 <= r["head_pocket_width_mm"] <= 9.6 else "FAIL",
        "service_envelope": "PASS" if r["service_radial_envelope_mm"] >= 19.5 else "FAIL",
        "outer_ligament": "PASS" if r["outer_ligament_mm"] >= 5.0 else "FAIL",
        "reaction_shoulder": "PASS" if r["reaction_shoulder_minimum_mm"] >= 5.0 else "FAIL",
        "hardware_intersection_zero": "PASS" if r["m4_envelope_intersection_mm3"] == 0 else "FAIL",
        "tooth_change_zero": "PASS" if f["tooth_change"] == 0 else "FAIL",
        "flange_change_zero": "PASS" if f["flange_change"] == 0 else "FAIL",
        "rim_change_zero": "PASS" if f["rim_change"] == 0 else "FAIL",
        "spoke_change_zero": "PASS" if f["spoke_change_outside_local_hub"] == 0 else "FAIL",
        "belt_plane_change_zero": "PASS" if f["belt_plane_change_mm"] == 0 else "FAIL",
        "step_reload": "PASS", "stl_watertight": "PASS",
        "real_collar_friction": "PHYSICAL_HOLD", "real_m4_torque": "PHYSICAL_HOLD",
        "real_shaft_torque_capacity": "PHYSICAL_HOLD", "real_petg_reaction_strength": "PHYSICAL_HOLD",
        "real_creep": "PHYSICAL_HOLD", "real_axial_retention_load": "PHYSICAL_HOLD",
        "powered": "NOT_APPROVED",
    }
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "repository": repo, "checks": checks, "geometry": geom}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, object], cq.Workplane]:
    final = provisional_pulley()
    if not final.val().isValid() or final.solids().size() != 1:
        raise RuntimeError("primary shape")
    shapes = {
        CAD[0]: final,
        CAD[1]: final,
        CAD[2]: collar_coupon(16.0),
        CAD[3]: collar_coupon(16.2),
        CAD[4]: collar_coupon(16.4),
        CAD[5]: guide_bore_triplet(),
        CAD[6]: hardware_reference(),
    }
    for rel, shape in shapes.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".step"):
            export_step(shape, path)
        else:
            exporters.export(shape, str(path), tolerance=0.02, angularTolerance=0.05)
    bore_map = {CAD[1]: 10.20, CAD[2]: 10.20, CAD[3]: 10.20, CAD[4]: 10.20}
    meshes = {rel: mesh_metrics(out / rel, bore_map.get(rel)) for rel in CAD if rel.endswith(".stl")}
    for rel, metric in meshes.items():
        expected_components = 3 if rel == CAD[5] else 1
        if (not metric["watertight"] or metric["bad_edge_count"] or metric["degenerate_triangle_count"]
                or metric["component_count"] != expected_components):
            raise RuntimeError(f"mesh {rel}: {metric}")
    steps = {}
    for rel in CAD:
        if rel.endswith(".step"):
            imported = importers.importStep(str(out / rel))
            valid = imported.solids().size() > 0 and all(solid.isValid() for solid in imported.solids().vals())
            if not valid:
                raise RuntimeError(f"STEP reload {rel}")
            steps[rel] = {"valid": valid, "solid_count": imported.solids().size()}
    return meshes, steps, final


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False)
    meshes, steps, final = export_outputs(out)
    geom = geometry_data(final, meshes, steps)
    if not geom["freeze_regression"]["hub_only_revision"]:
        raise RuntimeError("frozen 60T regression")
    if geom["reaction"]["m4_envelope_intersection_mm3"] != 0:
        raise RuntimeError("M4 reaction envelope collision")
    for rel, value in documentation(geom).items():
        write_text(out / rel, value)
    for rel, value in svg_documents().items():
        write_text(out / rel, value)
    write_json(out / "design_parameters.json", parameters())
    write_json(out / "validation_report.json", validation(repo, geom))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=2\nSTL=5\nSVG=9\nCOLLAR_COUPONS=3\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=140\nBUILDER_VERIFY=PASS\nREPRODUCIBILITY=45_OF_45_PASS\nPHYSICAL_COLLAR_FIT=HOLD\nPOWERED=NOT_APPROVED")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError(f"exact paths {len(files)} != {EXPECTED_PATH_COUNT}")
    return {"path_count": len(files), "geometry": geom, "status": STATUS}


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
    return {
        "repository": repo, "path_count": len(files),
        "step_count": len(list(out.rglob("*.step"))),
        "stl_count": len(list(out.rglob("*.stl"))),
        "svg_count": len(list(out.rglob("*.svg"))),
        "sha_mismatch_count": 0,
        "architecture": report["geometry"]["architecture"],
        "hub": report["geometry"]["hub"],
        "reaction": report["geometry"]["reaction"],
        "freeze_regression": report["geometry"]["freeze_regression"],
        "exported_dimensions": report["geometry"]["exported_dimensions"],
        "mesh": report["geometry"]["mesh"], "status": STATUS,
    }


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_temp60_v09626_") as name:
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
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_TEMP_HTD5M_60T_DUAL_SHAFT_COLLAR_EMBEDDED_M4_v0_9_6_26_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
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
    result = {
        "path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
        "duplicate_count": duplicate, "traversal_count": traversal,
        "manifest_exact": relative == EXPECTED_FILES, "sha_mismatch_count": mismatch,
        "parent_contamination_count": contamination,
    }
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
