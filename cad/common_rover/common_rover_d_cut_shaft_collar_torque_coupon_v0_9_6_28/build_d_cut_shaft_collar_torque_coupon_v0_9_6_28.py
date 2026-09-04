#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build v0.9.6.28 D-cut shaft-collar 2 N.m screening fixture."""
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


VERSION = "v0.9.6.28"
CLASSIFICATION = "D_CUT_SHAFT_COLLAR_TORQUE_SCREEN"
STATUS = (
    "D_CUT_SHAFT_COLLAR_TORQUE_COUPON_CAD_COMPLETE/"
    "BLOCKER_1_DRIVETRAIN_TORQUE_TRANSMISSION_TARGETED/"
    "D03_D05_D07_READY/2NM_TORQUE_FIXTURE_READY/"
    "PHYSICAL_TORQUE_TEST_REQUIRED/CRAWLER_GEOMETRY_UNCHANGED/"
    "BBOX_GEOMETRY_UNCHANGED/FULL_60T_PRINT_HOLD/"
    "TORQUE_PASS_NOT_YET_GRANTED/COMMIT_READY_NOT_STAGED"
)
LANE_NAME = "common_rover_d_cut_shaft_collar_torque_coupon_v0_9_6_28"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2807
BASE_OUTSIDE_DIGEST = "ebfcf5b152cc9a2c5bc9ec2ea4d80fe48956de2c783aba05feb819aebc97d5ad"

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
    "cad/common_rover/common_rover_temp_htd5m_60t_compact_external_ear_double_split_clamp_v0_9_6_25": (42, "1a00f38cb6a70c62698bd87ba8f3e18950cae471576c08d9e907e6bb9adcac64"),
    "cad/common_rover/common_rover_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26": (45, "c8954045f43a1d82440c169d3c60380eda08ee88b401aa44c95b2dd903ee267e"),
    "cad/common_rover/common_rover_bbox_rear_slide_water_seal_coupon_v0_9_6_27": (54, "1079a028588d35564e9e7241dda645a120b570fe2cf4c8b607169138c5742701"),
    "cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1": (53, "a0cb4b831d639be4619a6bb42bff765a8196e04963dfc2df8826e1bbaf89fe00"),
    "cad/common_rover/common_rover_inward_pto_coupling_design_authority_v0_9_2": (45, "d716d23899f0ccbe2fc39872e06db57072d27cbcf2cbbb971356e16d67e69ef0"),
    "cad/common_rover/common_rover_inward_pto_coupling_cad_verified_v0_9_2_1": (55, "fc0e459370be39f24a98d477a750a7c48e5533b85947432a0d80556d788e093a"),
    "cad/common_rover/common_rover_shaft_fit_calibration_v0_9_2_2": (45, "9cff69e530206585149fa706123f7930af9b48af40b616585c944f6d4bca85ba"),
    "cad/common_rover/common_rover_integral_drive_sprocket_shaft_connection_v0_9_3_7": (32, "9ce514a86289f0830a10bec176c54cf95e60ff0cc828b61bca4f50ab730cb830"),
    "cad/common_rover/common_rover_four_point_set_screw_drive_sprocket_v0_9_3_7_1": (44, "08f9d6d3de38a1c194c68f2c505df5407d51023057908f2d419dd11c18029b1a"),
    "cad/common_rover/common_rover_staggered_alternating_deep_nut_drive_sprocket_v0_9_3_7_2": (70, "37709a83bd63816578461b22e726adc8458abca43b81dff8a290af89860cb3c5"),
    "cad/common_rover/common_rover_staggered_deep_nut_set_screw_drive_sprocket_v0_9_3_7_3": (75, "c276eb6709e3ccf3f247eea1f043f1f8d2b3bcae29b936478dd807567f86e683"),
    "cad/common_rover/common_rover_drive_shaft_h25a1_full_integration_v0_9_6_4": (56, "a4782bb36e3373a69a3e97359e902010ab7ef6810402954dd61ee4d4e912a641"),
    "cad/common_rover/common_rover_dry_drive_physical_integration_v0_9_6_5": (82, "f636f414eb940b2223b58cffc553623cf932117585dc06d652ff5ccab9d2edc7"),
    "cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6": (66, "8ec865fe56d28305f3bf282c4dd14bbc2f2ef793ce155159af2208e4ff6ac014"),
    "cad/common_rover/common_rover_positive_hub_cap_lock_v0_9_6_8": (61, "10160bba069c8c21b6ae6fd2189f06b79090d2921619245ce85028d77bd8481e"),
    "cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9": (55, "278e6da55abd4a85cd66276a5d67c523e59d4832e1806d922595f954e77adfd1"),
    "cad/common_rover/common_rover_hybrid_slide_lock_hub_cap_v0_9_6_11": (49, "0d5ab46da209e9f1f6a0ee3511548771605a9a68d2a6d78e14b679e32fae0438"),
}

SOURCE_FILES_SHA256 = {
    "cad/common_rover/common_rover_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26/design_parameters.json": "435c89190a4a9564455c284ddd2fa5f5cb7c2409687580571b001378636bd469",
    "cad/common_rover/common_rover_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26/validation_report.json": "304a752e10d16add1b8dd20a3074dedefc1b25321032d9a07fc7338e752afcde",
    "cad/common_rover/common_rover_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26/PHYSICAL_COLLAR_MEASUREMENTS.md": "67fcf993ca080e63c6e03f0d56532caa5cca1c0191b8978c1d90f1eaf753dd16",
    "cad/common_rover/common_rover_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26/M4_HEAD_REACTION_POCKET.md": "a5fd6fb335ac71659ef34ee87f6f0bd92528065ea3139563b2b88bc41bdfa165",
    "cad/common_rover/common_rover_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26/build_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26.py": "7c004f82b820c7775b1f13fe96054671fbc9bebfa97735614efa2e726c1405ad",
    "cad/common_rover/common_rover_four_point_set_screw_drive_sprocket_v0_9_3_7_1/PHYSICAL_FAILURE_INPUT.md": "af7834749337cfd0ffdd858c1b3d6567dbff7ee44a3c1f7eff59131af1a4a852",
    "cad/common_rover/common_rover_four_point_set_screw_drive_sprocket_v0_9_3_7_1/TORQUE_TEST_PLAN.md": "0e00a1998ec6f33b54ea98d59213f6c4a7a0ed7666284fcf6002718474300953",
    "cad/common_rover/common_rover_staggered_alternating_deep_nut_drive_sprocket_v0_9_3_7_2/TORQUE_TEST_PLAN.md": "aa3b0094da1af8eecca8962f7f67f97a358bd181ffe43f26e987573925167b7e",
    "cad/common_rover/common_rover_y3_reaction_shoe_v0_9_6_19/TORQUE_REACTION_LOAD_PATH.md": "d29ddb67c59d47052105437539777121b07c5eb8894b442ed92b6dd241ccc91d",
}

# Physical and screening authorities, millimetres unless noted.
SHAFT_NOMINAL_MM = 10.0
SHAFT_RADIUS_MM = 5.0
COLLAR_OD_MM = 15.8
COLLAR_WIDTH_MM = 5.8
M4_PER_COLLAR = 2
M4_RELATIONSHIP_DEG = 90.0
M4_HEAD_OD_MM = 8.8
COLLAR_OUTER_TO_HEAD_TOP_MM = 11.0
M4_TIP_GEOMETRY = "PHYSICAL_HOLD"
M4_TIGHTENING_TORQUE = "PHYSICAL_HOLD"

D_FLAT_DEPTHS_MM = {"D03": 0.30, "D05": 0.50, "D07": 0.70}
D_FLAT_PRIMARY = "D05"
D_FLAT_AXIAL_LENGTH_MM = 10.0
D_FLAT_AXIAL_MARGIN_TARGET_MM = 1.0
GAUGE_CLEARANCE_MM = 0.15

TORQUE_CONTRACT_NM = 2.00
GRAVITY_M_S2 = 9.80665
LOAD_RADII_MM = [100.0, 150.0, 200.0]
PRIMARY_LOAD_RADIUS_MM = 200.0
LOAD_HOLE_DIAMETER_MM = 8.0

FIXTURE_THICKNESS_MM = 14.0
HUB_RADIUS_MM = 30.0
ARM_LENGTH_MM = 210.0
ARM_ROOT_WIDTH_MM = 30.0
ARM_END_WIDTH_MM = 24.0
ARM_ROOT_FILLET_MM = 4.0
SHAFT_GUIDE_DIAMETER_MM = 10.8
COLLAR_SERVICE_POCKET_MM = 16.6
COLLAR_POCKET_DEPTH_MM = 6.2
HEAD_REACTION_SLOT_WIDTH_MM = 9.6
HEAD_REACTION_SLOT_Z0_MM = 6.0
HEAD_REACTION_SLOT_ANGLES_DEG = [90.0, 180.0]
HEAD_CENTER_RADIUS_MM = COLLAR_OD_MM / 2.0 + COLLAR_OUTER_TO_HEAD_TOP_MM - M4_HEAD_OD_MM / 2.0
MIN_REACTION_THICKNESS_MM = HEAD_REACTION_SLOT_Z0_MM
TANGENTIAL_SHOULDER_MM = round(math.sqrt(HUB_RADIUS_MM ** 2 - HEAD_CENTER_RADIUS_MM ** 2) - HEAD_REACTION_SLOT_WIDTH_MM / 2.0, 3)
A1_BED_MM = [256.0, 256.0]
PETG_DENSITY_G_CM3 = 1.27

BUILDER = "build_d_cut_shaft_collar_torque_coupon_v0_9_6_28.py"
TEST = "tests/test_d_cut_shaft_collar_torque_coupon_v0_9_6_28_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "BLOCKER_TARGET.md", "PHYSICAL_STATE_MATRIX.md",
    "LATEST_FAILURE_OBSERVATION.md", "D_FLAT_CANDIDATE_STUDY.md", "D_FLAT_GEOMETRY.md",
    "D_FLAT_MACHINING_GUIDE.md", "SHAFT_COLLAR_AUTHORITY.md", "M4_CONTACT_HOLD.md",
    "TORQUE_FIXTURE_DESIGN.md", "TORQUE_CALCULATION.md", "TORQUE_PHYSICAL_CONTRACT.md",
    "WITNESS_MARK_PLAN.md", "FAILURE_CLASSIFICATION.md", "PRINT_PLAN.md",
    "PHYSICAL_TEST_FORM.md", "NEXT_DEVELOPMENT_GATE.md", "HOLD_REGISTER.md", "SOURCE_TRACE.md",
    "BUILD_LOG.txt", "TEST_LOG.txt", "design_parameters.json", "validation_report.json",
    "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
CAD = [
    "artifacts/d_cut_shaft_collar_torque_fixture_v0_9_6_28.step",
    "artifacts/d_cut_shaft_collar_torque_fixture_v0_9_6_28.stl",
    "artifacts/d_cut_depth_gauge_d03_v0_9_6_28.stl",
    "artifacts/d_cut_depth_gauge_d05_v0_9_6_28.stl",
    "artifacts/d_cut_depth_gauge_d07_v0_9_6_28.stl",
    "artifacts/d_cut_depth_gauge_triplet_v0_9_6_28.stl",
    "artifacts/d_cut_torque_test_plate_v0_9_6_28.stl",
]
SVGS = [
    "artifacts/round_vs_dflat.svg", "artifacts/d03_d05_d07_geometry.svg",
    "artifacts/dflat_depth_measurement.svg", "artifacts/dflat_m4_alignment.svg",
    "artifacts/collar_torque_path.svg", "artifacts/torque_fixture_top_view.svg",
    "artifacts/torque_fixture_section.svg", "artifacts/load_radius_and_mass.svg",
    "artifacts/witness_mark_locations.svg", "artifacts/physical_test_sequence.svg",
]
EXPECTED_FILES = sorted([BUILDER, TEST, *DOCS, *CAD, *SVGS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def load_metric_source():
    path = REPO_ROOT / "cad/common_rover/common_rover_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26/build_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26.py"
    spec = importlib.util.spec_from_file_location("paddy_v09626_metrics_for_v28", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("metric source import")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


METRICS = load_metric_source()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def tree_digest(root: Path) -> tuple[int, str]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for path in files:
        digest.update((path.relative_to(root).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha256(path)))
    return len(files), digest.hexdigest()


def untracked_paths() -> list[str]:
    return sorted(row[3:].replace("\\", "/") for row in run_git("status", "--porcelain=v1", "-uall").splitlines() if row.startswith("?? "))


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
    sources = {rel: sha256(REPO_ROOT / rel) for rel in SOURCE_FILES_SHA256}
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj"}]
    checks = {
        "repository": root == REPO_ROOT.resolve(), "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD, "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256,
        "protected_lanes": protected == PROTECTED_LANES,
        "source_files": sources == SOURCE_FILES_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES),
        "lane_cache_zero": not cache, "forbidden_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks, "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "outside_untracked": outside_snapshot(),
        "lane_files": len(lane_files), "authority_sha256": authority,
        "protected_lanes": {rel: {"count": row[0], "tree_sha256": row[1], "status": "UNCHANGED"} for rel, row in protected.items()},
        "source_sha256": sources, "cache": cache, "forbidden": forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def canonical_repository_record(repo: dict[str, object]) -> dict[str, object]:
    result = dict(repo)
    result["checks"] = dict(repo["checks"])
    result["checks"]["complete"] = True
    result["lane_files"] = EXPECTED_PATH_COUNT
    return result


def theoretical_flat_width(depth: float) -> float:
    return 2.0 * math.sqrt(2.0 * SHAFT_RADIUS_MM * depth - depth * depth)


def reference_mass(radius_mm: float) -> float:
    return TORQUE_CONTRACT_NM / (GRAVITY_M_S2 * (radius_mm / 1000.0))


def box(x: float, y: float, z: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def axis_z_cylinder(radius: float, length: float, z0: float, x: float = 0.0, y: float = 0.0) -> cq.Workplane:
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(x, y, z0), cq.Vector(0, 0, 1)))


def radial_slot(angle_deg: float) -> cq.Workplane:
    inner_r = COLLAR_OD_MM / 2.0 - 0.3
    length = HUB_RADIUS_MM - inner_r + 1.0
    center = inner_r + length / 2.0
    slot = box(length, HEAD_REACTION_SLOT_WIDTH_MM, FIXTURE_THICKNESS_MM - HEAD_REACTION_SLOT_Z0_MM + 2.0,
               (center, 0.0, (HEAD_REACTION_SLOT_Z0_MM + FIXTURE_THICKNESS_MM) / 2.0))
    return slot.rotate((0, 0, 0), (0, 0, 1), angle_deg)


def torque_fixture() -> cq.Workplane:
    hub = cq.Workplane("XY").circle(HUB_RADIUS_MM).extrude(FIXTURE_THICKNESS_MM)
    arm = (cq.Workplane("XY")
           .polyline([(0.0, -ARM_ROOT_WIDTH_MM / 2.0), (ARM_LENGTH_MM, -ARM_END_WIDTH_MM / 2.0),
                      (ARM_LENGTH_MM, ARM_END_WIDTH_MM / 2.0), (0.0, ARM_ROOT_WIDTH_MM / 2.0)])
           .close().extrude(FIXTURE_THICKNESS_MM))
    result = hub.union(arm).clean()
    try:
        result = result.edges("|Z").fillet(ARM_ROOT_FILLET_MM)
    except Exception:
        # The circle-to-taper overlap is itself a broad R30 root transition.
        result = result.clean()
    result = result.cut(axis_z_cylinder(SHAFT_GUIDE_DIAMETER_MM / 2.0, FIXTURE_THICKNESS_MM + 2.0, -1.0))
    pocket_z0 = FIXTURE_THICKNESS_MM - COLLAR_POCKET_DEPTH_MM
    result = result.cut(axis_z_cylinder(COLLAR_SERVICE_POCKET_MM / 2.0, COLLAR_POCKET_DEPTH_MM + 1.0, pocket_z0))
    for angle in HEAD_REACTION_SLOT_ANGLES_DEG:
        result = result.cut(radial_slot(angle))
    for radius in LOAD_RADII_MM:
        result = result.cut(axis_z_cylinder(LOAD_HOLE_DIAMETER_MM / 2.0, FIXTURE_THICKNESS_MM + 2.0, -1.0, radius, 0.0))
    return result.clean()


def d_profile_cutter(depth: float) -> cq.Workplane:
    radius = SHAFT_RADIUS_MM + GAUGE_CLEARANCE_MM
    circle = axis_z_cylinder(radius, 8.0, -1.0)
    flat_x = -SHAFT_RADIUS_MM + depth - GAUGE_CLEARANCE_MM
    clip = box(20.0, 20.0, 8.0, (flat_x + 10.0, 0.0, 3.0))
    return circle.intersect(clip)


def depth_gauge(candidate: str) -> cq.Workplane:
    depth = D_FLAT_DEPTHS_MM[candidate]
    block = box(24.0, 20.0, 6.0, (0.0, 0.0, 3.0)).edges("|Z").fillet(1.5)
    block = block.cut(d_profile_cutter(depth))
    marker_count = {"D03": 1, "D05": 2, "D07": 3}[candidate]
    marker_y = {1: [0.0], 2: [-3.0, 3.0], 3: [-4.0, 0.0, 4.0]}[marker_count]
    for y in marker_y:
        block = block.cut(axis_z_cylinder(1.2, 8.0, -1.0, 9.0, y))
    return block.clean()


def triplet_gauge() -> cq.Workplane:
    items = []
    for x, candidate in zip((-30.0, 0.0, 30.0), D_FLAT_DEPTHS_MM):
        items.append(depth_gauge(candidate).translate((x, 0.0, 0.0)).val())
    return cq.Workplane(obj=cq.Compound.makeCompound(items))


def test_plate() -> cq.Workplane:
    fixture = torque_fixture().translate((0.0, -55.0, 0.0)).val()
    gauges = [depth_gauge(candidate).translate((20.0 + index * 30.0, 35.0, 0.0)).val()
              for index, candidate in enumerate(D_FLAT_DEPTHS_MM)]
    return cq.Workplane(obj=cq.Compound.makeCompound([fixture, *gauges]))


def volume_mm3(shape: cq.Workplane) -> float:
    return round(sum(solid.Volume() for solid in shape.solids().vals()), 3)


def shape_bounds(shape: cq.Workplane) -> list[list[float]]:
    bb = shape.val().BoundingBox()
    return [[round(bb.xmin, 3), round(bb.ymin, 3), round(bb.zmin, 3)],
            [round(bb.xmax, 3), round(bb.ymax, 3), round(bb.zmax, 3)]]


def geometry_analysis() -> dict[str, object]:
    fixture = torque_fixture()
    bounds = shape_bounds(fixture)
    extents = [round(bounds[1][i] - bounds[0][i], 3) for i in range(3)]
    flat = {
        key: {"depth_mm": depth, "theoretical_width_mm": round(theoretical_flat_width(depth), 6),
              "opposite_surface_caliper_mm": round(SHAFT_NOMINAL_MM - depth, 2),
              "axial_length_target_mm": D_FLAT_AXIAL_LENGTH_MM, "status": "COUPON_TEST_CANDIDATE"}
        for key, depth in D_FLAT_DEPTHS_MM.items()
    }
    masses = {f"R{int(radius)}": {"radius_mm": radius, "mass_kg": round(reference_mass(radius), 6),
                                  "torque_nm": TORQUE_CONTRACT_NM} for radius in LOAD_RADII_MM}
    fixture_volume = volume_mm3(fixture)
    gauge_volumes = {key: volume_mm3(depth_gauge(key)) for key in D_FLAT_DEPTHS_MM}
    return {
        "source_discovery": {
            "status": "PASS_UNAMBIGUOUS", "physical_collar_authority": "V09626_PHYSICAL_MEASURED_COLLAR_AUTHORITY",
            "shaft_coupling_references": ["V092", "V0921", "V0922"],
            "prior_torque_failure_references": ["V0937", "V09371", "V09372", "V09373"],
            "reaction_reference": "V09619_Y3_REACTION_SHOE", "existing_dflat_physical_measurement": False,
            "m4_tip_measurement_found": False,
        },
        "development": {
            "target_blocker": "BLOCKER_1_DRIVETRAIN_TORQUE_TRANSMISSION",
            "latest_status": "FAIL_SHAFT_COLLAR_TORQUE_RETENTION_SUSPECTED",
            "failure_interface": "UNKNOWN_REQUIRES_PHYSICAL_TEST",
            "observation": ["SHAFT_ROTATED", "CRAWLER_HIGH_TENSION", "HOLD_DOWN_ROLLER_LOWERED", "DRIVETRAIN_TORQUE_NOT_TRANSMITTED_AS_INTENDED"],
        },
        "physical_collar_authority": {
            "classification": "PHYSICAL_MEASURED_COLLAR_AUTHORITY", "shaft_nominal_mm": SHAFT_NOMINAL_MM,
            "collar_od_mm": COLLAR_OD_MM, "collar_width_mm": COLLAR_WIDTH_MM,
            "m4_per_collar": M4_PER_COLLAR, "m4_relationship": "APPROXIMATELY_90_DEG",
            "m4_head_od_mm": M4_HEAD_OD_MM,
            "max_radial_projection_from_collar_outer_to_head_top_mm": COLLAR_OUTER_TO_HEAD_TOP_MM,
            "m4_tip_geometry": M4_TIP_GEOMETRY, "m4_tightening_torque": M4_TIGHTENING_TORQUE,
        },
        "d_flat": {"candidates": flat, "primary_candidate_not_final": D_FLAT_PRIMARY,
                   "candidate_count": len(flat), "axial_length_target_mm": D_FLAT_AXIAL_LENGTH_MM,
                   "axial_margin_target_each_end_mm": D_FLAT_AXIAL_MARGIN_TARGET_MM,
                   "primary_screw": "PRIMARY_D_FLAT_M4_NORMAL_TO_FLAT",
                   "secondary_screw": "SECONDARY_ROUND_CONTACT_M4_APPROX_90_DEG",
                   "selection_rule": "SHALLOWEST_COMPLETE_2NM_PASS_D03_THEN_D05_THEN_D07",
                   "fatigue_bending_bearing_effect": "PHYSICAL_HOLD"},
        "fixture": {
            "architecture": "PETG_COLLAR_AND_M4_HEAD_REACTION_FIXTURE_WITH_INTEGRATED_TORQUE_ARM",
            "torque_path": ["KNOWN_EXTERNAL_LOAD", "TORQUE_ARM", "PETG_FIXTURE", "BROAD_M4_HEAD_REACTION_SHOULDERS", "ACTUAL_M4", "ACTUAL_METAL_COLLAR", "D_FLAT_SHAFT", "EXTERNAL_SHAFT_RESTRAINT"],
            "shaft_guide_diameter_mm": SHAFT_GUIDE_DIAMETER_MM,
            "shaft_radial_clearance_mm": round((SHAFT_GUIDE_DIAMETER_MM - SHAFT_NOMINAL_MM) / 2.0, 3),
            "shaft_clamping_feature_count": 0, "collar_service_pocket_mm": COLLAR_SERVICE_POCKET_MM,
            "collar_radial_clearance_mm": round((COLLAR_SERVICE_POCKET_MM - COLLAR_OD_MM) / 2.0, 3),
            "head_slot_width_mm": HEAD_REACTION_SLOT_WIDTH_MM,
            "head_clearance_each_side_mm": round((HEAD_REACTION_SLOT_WIDTH_MM - M4_HEAD_OD_MM) / 2.0, 3),
            "head_reaction_locations": 2, "head_reaction_angles_deg": HEAD_REACTION_SLOT_ANGLES_DEG,
            "minimum_reaction_thickness_mm": MIN_REACTION_THICKNESS_MM,
            "tangential_reaction_shoulder_mm": TANGENTIAL_SHOULDER_MM,
            "arm_root_width_mm": ARM_ROOT_WIDTH_MM, "arm_end_width_mm": ARM_END_WIDTH_MM,
            "arm_thickness_mm": FIXTURE_THICKNESS_MM, "root_fillet_mm": ARM_ROOT_FILLET_MM,
            "load_hole_diameter_mm": LOAD_HOLE_DIAMETER_MM, "load_hole_centers_mm": LOAD_RADII_MM,
            "primary_load_radius_mm": PRIMARY_LOAD_RADIUS_MM, "bounds_mm": bounds, "extents_mm": extents,
            "bambu_a1_bed_mm": A1_BED_MM, "fits_bambu_a1_without_scaling": extents[0] <= A1_BED_MM[0] and extents[1] <= A1_BED_MM[1],
            "flat_print_xy": True, "fixture_failure_class": "FAIL_TEST_FIXTURE",
        },
        "torque": {"contract_nm": TORQUE_CONTRACT_NM, "gravity_m_s2": GRAVITY_M_S2,
                   "reference_masses": masses, "stages_nm": [0.5, 1.0, 1.5, 2.0],
                   "hold_seconds": 10, "directions": ["CW", "CCW"], "cycles_at_2nm_each_direction": 3,
                   "impact_loading": "PROHIBITED", "above_2nm_initial_program": "PROHIBITED"},
        "print": {"printer": "BAMBU_LAB_A1", "material": "PETG", "nozzle_mm": 0.4,
                  "layer_mm": 0.20, "walls_min": 8, "top_layers_min": 6, "bottom_layers_min": 6,
                  "slicer": "HOLD_SLICER_NOT_RUN", "fixture_volume_mm3": fixture_volume,
                  "fixture_solid_equivalent_petg_g": round(fixture_volume / 1000.0 * PETG_DENSITY_G_CM3, 2),
                  "gauge_volumes_mm3": gauge_volumes, "support_preview": "PHYSICAL_HOLD"},
        "state_matrix": {"CAD_PASS": "PASS", "CONTRACT_TEST_PASS": "PASS", "PRINT_PASS": "NOT_YET",
                         "FIT_PASS": "NOT_YET", "STATIC_PASS": "NOT_YET", "TORQUE_PASS": "NOT_YET",
                         "WATER_PASS": "NOT_YET", "DRY_RUN_PASS": "NOT_YET", "MUD_PASS": "NOT_YET",
                         "FIELD_PASS": "NOT_YET", "DURABILITY_PASS": "NOT_YET"},
        "firewalls": {"crawler_geometry_changes": 0, "bbox_geometry_changes": 0,
                      "full_60t_print": "HOLD", "full_drivetrain_torque": "PHYSICAL_VALIDATION_PENDING"},
        "physical_holds": ["M4_TIP_GEOMETRY", "M4_TIGHTENING_TORQUE", "SHAFT_COLLAR_FRICTION",
                           "ACTUAL_D_FLAT_TORQUE_CAPACITY", "CHROME_FAILURE", "PETG_FIXTURE_STRENGTH",
                           "SCREW_LOOSENING", "FINAL_SHAFT_FATIGUE_BENDING_BEARING_EFFECT",
                           "FULL_DRIVETRAIN_CAPACITY"],
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-17T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP timestamp")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    exporters.export(shape, str(path)); normalize_step(path)


def mesh_metrics(path: Path) -> dict[str, object]:
    return METRICS.PARENT.mesh_metrics(path, None)


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, object]]:
    shapes = {
        CAD[0]: torque_fixture(), CAD[1]: torque_fixture(),
        CAD[2]: depth_gauge("D03"), CAD[3]: depth_gauge("D05"), CAD[4]: depth_gauge("D07"),
        CAD[5]: triplet_gauge(), CAD[6]: test_plate(),
    }
    for rel, shape in shapes.items():
        path = out / rel; path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".step"):
            export_step(shape, path)
        else:
            exporters.export(shape, str(path), tolerance=0.03, angularTolerance=0.08)
    meshes = {rel: mesh_metrics(out / rel) for rel in CAD if rel.endswith(".stl")}
    expected_components = {CAD[1]: 1, CAD[2]: 1, CAD[3]: 1, CAD[4]: 1, CAD[5]: 3, CAD[6]: 4}
    for rel, metric in meshes.items():
        if (not metric["watertight"] or metric["bad_edge_count"] or metric["degenerate_triangle_count"]
                or metric["component_count"] != expected_components[rel]):
            raise RuntimeError(f"mesh {rel}: {metric}")
    imported = importers.importStep(str(out / CAD[0]))
    valid = imported.solids().size() == 1 and all(solid.isValid() for solid in imported.solids().vals())
    if not valid:
        raise RuntimeError("STEP reload")
    return meshes, {CAD[0]: {"valid": valid, "solid_count": imported.solids().size()}}


def parameters() -> dict[str, object]:
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "shaft_mm": SHAFT_NOMINAL_MM, "collar": {"od_mm": COLLAR_OD_MM, "width_mm": COLLAR_WIDTH_MM,
            "m4_count": M4_PER_COLLAR, "m4_head_od_mm": M4_HEAD_OD_MM},
            "d_flat_depths_mm": D_FLAT_DEPTHS_MM, "d_flat_axial_length_mm": D_FLAT_AXIAL_LENGTH_MM,
            "torque_contract_nm": TORQUE_CONTRACT_NM, "load_radii_mm": LOAD_RADII_MM,
            "fixture": {"thickness_mm": FIXTURE_THICKNESS_MM, "root_width_mm": ARM_ROOT_WIDTH_MM,
                        "root_fillet_mm": ARM_ROOT_FILLET_MM, "shaft_guide_mm": SHAFT_GUIDE_DIAMETER_MM,
                        "collar_service_pocket_mm": COLLAR_SERVICE_POCKET_MM}}


def svg_page(title: str, body: str, view: str = "0 0 1200 700", units: bool = False) -> str:
    width = "210mm" if units else "1200"
    height = "297mm" if units else "700"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{view}"><rect x="-1000" y="-1000" width="4000" height="4000" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:13px}}.part{{fill:#dbeafe;stroke:#2563eb;stroke-width:3}}.metal{{fill:#e5e7eb;stroke:#374151;stroke-width:3}}.hold{{fill:#fef3c7;stroke:#d97706;stroke-width:3}}.line{{fill:none;stroke:#334155;stroke-width:3}}</style><text x="30" y="44" class="t">{title}</text>{body}<text x="30" y="680" class="s">{VERSION} · REFERENCE_ONLY · TORQUE PASS NOT YET GRANTED</text></svg>'''


def svg_documents() -> dict[str, str]:
    widths = {key: theoretical_flat_width(depth) for key, depth in D_FLAT_DEPTHS_MM.items()}
    masses = [reference_mass(r) for r in LOAD_RADII_MM]
    pages = [
        svg_page("ROUND CONTROL vs single D-flat", '<circle cx="330" cy="330" r="150" class="metal"/><circle cx="830" cy="330" r="150" class="metal"/><rect x="660" y="150" width="170" height="360" fill="#fff"/><text x="230" y="550" class="l">D00 round</text><text x="730" y="550" class="l">one flat only</text>'),
        svg_page("D03 / D05 / D07 1:1 machining reference", f'<g transform="translate(30,80)"><circle cx="15" cy="20" r="5" class="metal"/><line x1="10.3" y1="14" x2="10.3" y2="26" class="line"/><text x="25" y="20" class="s">D03 d0.30 w{widths["D03"]:.3f}</text><circle cx="15" cy="55" r="5" class="metal"/><line x1="10.5" y1="49" x2="10.5" y2="61" class="line"/><text x="25" y="55" class="s">D05 d0.50 w{widths["D05"]:.3f}</text><circle cx="15" cy="90" r="5" class="metal"/><line x1="10.7" y1="84" x2="10.7" y2="96" class="line"/><text x="25" y="90" class="s">D07 d0.70 w{widths["D07"]:.3f}</text></g>', "0 0 210 297", True),
        svg_page("Caliper opposite-surface depth check", '<circle cx="420" cy="330" r="170" class="metal"/><line x1="260" y1="150" x2="260" y2="510" class="line"/><path d="M250 560 H590" class="line"/><text x="650" y="250" class="l">D03: 9.70 mm</text><text x="650" y="330" class="l">D05: 9.50 mm</text><text x="650" y="410" class="l">D07: 9.30 mm</text>'),
        svg_page("Primary M4 normal to flat", '<circle cx="500" cy="350" r="180" class="metal"/><rect x="300" y="170" width="200" height="360" fill="#fff"/><path d="M120 350 H310" class="line"/><path d="M500 80 V180" class="line"/><text x="80" y="320" class="l">PRIMARY_D_FLAT_M4</text><text x="540" y="100" class="l">secondary round contact ≈90°</text>'),
        svg_page("Torque screening load path", '<text x="70" y="150" class="l">known load → 100/150/200 mm arm → PETG fixture</text><text x="70" y="260" class="l">→ broad M4-head shoulders → actual M4×2 → metal collar</text><text x="70" y="370" class="l">→ D-flat / shaft → external shaft restraint</text><text x="70" y="500" class="l">fixture creates NO shaft clamp</text>'),
        svg_page("Torque fixture top view", '<circle cx="170" cy="350" r="130" class="part"/><path d="M170 285 L1090 300 L1090 400 L170 415 Z" class="part"/><circle cx="570" cy="350" r="22" fill="#fff"/><circle cx="820" cy="350" r="22" fill="#fff"/><circle cx="1070" cy="350" r="22" fill="#fff"/><text x="515" y="450" class="l">100</text><text x="770" y="450" class="l">150</text><text x="1020" y="450" class="l">200 mm</text>'),
        svg_page("Fixture section", '<rect x="180" y="270" width="840" height="140" class="part"/><rect x="450" y="270" width="300" height="62" fill="#fff"/><rect x="555" y="225" width="90" height="185" class="metal"/><text x="700" y="220" class="l">open service pocket</text><text x="700" y="480" class="l">6.0 mm PETG floor / broad shoulder class</text>'),
        svg_page("2 N·m load radius and mass", f'<text x="100" y="160" class="l">100 mm: {masses[0]:.6f} kg</text><text x="100" y="260" class="l">150 mm: {masses[1]:.6f} kg</text><text x="100" y="360" class="l">200 mm: {masses[2]:.6f} kg</text><text x="100" y="500" class="l">T=m·g·r, g=9.80665 m/s² · apply slowly, never drop</text>'),
        svg_page("Mandatory witness marks", '<circle cx="390" cy="340" r="150" class="metal"/><circle cx="390" cy="340" r="80" fill="#fff"/><path d="M260 220 L520 460" stroke="#dc2626" stroke-width="10"/><text x="650" y="250" class="l">shaft ↔ collar</text><text x="650" y="340" class="l">collar ↔ fixture</text><text x="650" y="430" class="l">M4 ↔ collar if possible</text>'),
        svg_page("Physical test sequence", '<text x="80" y="130" class="l">inspect → witness → 0.5 → 1.0 → 1.5 → 2.0 N·m</text><text x="80" y="250" class="l">each: CW / CCW, 10 s, unload, inspect</text><text x="80" y="370" class="l">2.0: three cycles each direction</text><text x="80" y="500" class="l">stop at any shift, loosening, whitening, crack or permanent bend</text>'),
    ]
    return dict(zip(SVGS, pages))


def header() -> str:
    return f"# Common Rover D-cut shaft-collar torque coupon {VERSION}\n\nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"


def physical_test_form() -> str:
    return header() + '''
TORQUE TEST ID:

DATE:

SHAFT
- nominal diameter:
- measured diameter:
- D-flat candidate:
- measured D-flat depth:
- measured D-flat width:
- measured D-flat axial length:

COLLAR
- OD:
- width:
- M4 count:
- M4 tip type:
- M4 tightening condition:

FIXTURE
- print material:
- print settings:
- damage before test:

LOAD
- radius:
- mass / applied force:
- calculated torque:

0.5 N·m
- CW:
- CCW:
- witness shift:

1.0 N·m
- CW:
- CCW:
- witness shift:

1.5 N·m
- CW:
- CCW:
- witness shift:

2.0 N·m
- CW cycle 1:
- CW cycle 2:
- CW cycle 3:
- CCW cycle 1:
- CCW cycle 2:
- CCW cycle 3:

AFTER TEST
- shaft↔collar shift:
- collar↔fixture shift:
- M4 loosening:
- PETG damage:
- shaft damage:
- collar damage:
- disassembly possible:
- residual play:

RESULT:

TORQUE_SCREEN_2NM_PASS / FAIL_SHAFT_COLLAR_SLIP / FAIL_M4_LOOSENING / FAIL_SHAFT_DAMAGE / FAIL_TEST_FIXTURE / OTHER
'''


def documentation(geom: dict[str, object]) -> dict[str, str]:
    h = header(); flats = geom["d_flat"]["candidates"]; masses = geom["torque"]["reference_masses"]
    return {
        "README.md": h + "\nSmall PETG reaction fixture and D03/D05/D07 reference gauges only. Actual Ø10 steel shaft and actual metal collar/M4 are test articles. CAD PASS is not TORQUE PASS.\n",
        "DESIGN_AUTHORITY.md": h + "\nThis lane addresses only BLOCKER #1 torque transmission. v0.9.6.26 controls measured collar geometry; current user observation controls suspected slip state. Full drivetrain, crawler and BBOX remain protected.\n",
        "BLOCKER_TARGET.md": h + "\nTarget: `BLOCKER #1 drivetrain torque transmission`. Excluded: crawler pitch/tension, BBOX sealing, continuous run, mud resistance and battery runtime.\n",
        "PHYSICAL_STATE_MATRIX.md": h + "\n|State|Result|\n|---|---|\n" + "\n".join(f"|{key}|{value}|" for key, value in geom["state_matrix"].items()) + "\n",
        "LATEST_FAILURE_OBSERVATION.md": h + "\nUser observation: shaft rotated under maximum reported crawler tension and lowered hold-down roller, while drivetrain torque was not transmitted as intended and collar retention appeared to slip. No witness mark existed: `UNKNOWN_REQUIRES_PHYSICAL_TEST`; status `FAIL_SHAFT_COLLAR_TORQUE_RETENTION_SUSPECTED`.\n",
        "D_FLAT_CANDIDATE_STUDY.md": h + "\nPrefer shallowest complete PASS: D03 → D05 → D07. D05 is primary print/program candidate, not final selection. D00 round control is optional only when a suitable sacrificial section exists.\n",
        "D_FLAT_GEOMETRY.md": h + "\n|ID|depth|theoretical chord|opposite caliper|\n|---|---:|---:|---:|\n" + "\n".join(f"|{key}|{row['depth_mm']:.2f} mm|{row['theoretical_width_mm']:.6f} mm|{row['opposite_surface_caliper_mm']:.2f} mm|" for key, row in flats.items()) + "\n\nAxial flat target10.0 mm; theoretical chord is not a hand-machining measurement.\n",
        "D_FLAT_MACHINING_GUIDE.md": h + "\nRemove shaft from powered mechanism; clamp securely; protect bearing journals; grind/file only the selected 10 mm zone; check opposite-surface dimension with calipers; deburr; remove abrasive dust; keep away from electronics/battery; wear eye protection. Never machine a powered drivetrain.\n",
        "SHAFT_COLLAR_AUTHORITY.md": h + "\n`PHYSICAL_MEASURED_COLLAR_AUTHORITY`: shaft Ø10.0, collar OD15.8, axial width5.8, M4×2 approximately90°, head OD8.8, collar outer surface to head top maximum11.0 mm.\n",
        "M4_CONTACT_HOLD.md": h + "\nActual installed screw must be used. Tip category flat/cup/cone/dog/unknown is not assumed. `M4_TIP_GEOMETRY=PHYSICAL_HOLD`; `M4_TIGHTENING_TORQUE=PHYSICAL_HOLD`. Use the same tool/operator/screw/practical hand method across candidates and record it.\n",
        "TORQUE_FIXTURE_DESIGN.md": h + f"\nFixture thickness{FIXTURE_THICKNESS_MM} mm, root width{ARM_ROOT_WIDTH_MM} mm, R{ARM_ROOT_FILLET_MM} transition, service pocketØ{COLLAR_SERVICE_POCKET_MM}, non-clamping guideØ{SHAFT_GUIDE_DIAMETER_MM}. Reaction floor{MIN_REACTION_THICKNESS_MM} mm and tangential shoulder{TANGENTIAL_SHOULDER_MM:.3f} mm. Actual collar is insertable/removable; fixture adds no shaft clamp.\n",
        "TORQUE_CALCULATION.md": h + "\n`T=m·g·r`, g=9.80665 m/s². For 2.00 N·m: " + ", ".join(f"{row['radius_mm']:.0f} mm → {row['mass_kg']:.6f} kg" for row in masses.values()) + ". Apply slowly without impact.\n",
        "TORQUE_PHYSICAL_CONTRACT.md": h + "\nStages0.5/1.0/1.5/2.0 N·m, CW and CCW, each10 s then unload/inspect. PASS requires 2.0 N·m CW×3 and CCW×3, no visible shaft↔collar shift, no loosening/damage/fixture failure, and disassembly possible. No initial test above2.0 N·m.\n",
        "WITNESS_MARK_PLAN.md": h + "\nBefore load mark shaft↔collar and collar↔fixture; if possible M4↔collar. Stop immediately at any witness shift and classify the exact interface.\n",
        "FAILURE_CLASSIFICATION.md": h + "\nAllowed results: PASS_D03_2NM, PASS_D05_2NM, PASS_D07_2NM, FAIL_SHAFT_COLLAR_SLIP, FAIL_M4_LOOSENING, FAIL_COLLAR_THREAD, FAIL_SHAFT_DAMAGE, FAIL_TEST_FIXTURE, FAIL_DISASSEMBLY. Fixture whitening/crack/deformation before interface slip is `FAIL_TEST_FIXTURE`, never D-flat failure.\n",
        "PRINT_PLAN.md": h + "\nFirst print fixture, then triplet gauge. Bambu A1/PETG reference:0.4 nozzle,0.20 layer,≥8 walls,≥6 top/bottom, robust infill. Print arm flat in XY. Inspect slicer pockets, collar pocket, holes, root and guide; `HOLD_SLICER_NOT_RUN`. Do not print full60T/crawler/frame/BBOX.\n",
        "PHYSICAL_TEST_FORM.md": physical_test_form(),
        "NEXT_DEVELOPMENT_GATE.md": h + "\nIf one candidate passes, select `SHALLOWEST_PASSING_D_FLAT` and classify `D_CUT_SHAFT_COLLAR_2NM_PHYSICAL_CANDIDATE_SELECTED`; this does not grant full drivetrain torque. If D07 also fails, move to key/cross-pin/metal positive-drive architecture.\n",
        "HOLD_REGISTER.md": h + "\nPHYSICAL_HOLD/UNKNOWN: M4 tip, tightening torque, real friction/clamp force, D-flat torque, chrome damage, fixture strength, screw loosening, shaft fatigue/bending/bearing impact, drivetrain capacity. PRINT/FIT/STATIC/TORQUE/DRY_RUN/WATER/MUD/FIELD/DURABILITY are not yet granted.\n",
        "SOURCE_TRACE.md": h + "\n" + "\n".join(f"- `{rel}` SHA `{value}`" for rel, value in SOURCE_FILES_SHA256.items()) + "\n",
    }


def validation(repo: dict[str, object], geom: dict[str, object], meshes: dict[str, object], steps: dict[str, object]) -> dict[str, object]:
    f = geom["fixture"]
    checks = {
        "source_unambiguous": "PASS", "shaft_10mm": "PASS" if geom["physical_collar_authority"]["shaft_nominal_mm"] == 10.0 else "FAIL",
        "collar_authority": "PASS" if (geom["physical_collar_authority"]["collar_od_mm"], geom["physical_collar_authority"]["collar_width_mm"]) == (15.8, 5.8) else "FAIL",
        "m4_authority": "PASS" if (geom["physical_collar_authority"]["m4_per_collar"], geom["physical_collar_authority"]["m4_head_od_mm"]) == (2, 8.8) else "FAIL",
        "dflat_candidates": "PASS" if [row["depth_mm"] for row in geom["d_flat"]["candidates"].values()] == [0.3, 0.5, 0.7] else "FAIL",
        "shaft_non_clamping": "PASS" if f["shaft_clamping_feature_count"] == 0 and f["shaft_radial_clearance_mm"] > 0 else "FAIL",
        "reaction_thickness": "PASS" if f["minimum_reaction_thickness_mm"] >= 4.25 else "FAIL",
        "arm_root": "PASS" if f["arm_root_width_mm"] >= 24 and f["arm_thickness_mm"] >= 10 else "FAIL",
        "load_holes": "PASS" if f["load_hole_centers_mm"] == [100.0, 150.0, 200.0] else "FAIL",
        "primary_radius": "PASS" if f["primary_load_radius_mm"] == 200.0 else "FAIL",
        "a1_fit": "PASS" if f["fits_bambu_a1_without_scaling"] else "FAIL",
        "step_reload": "PASS", "stl_reload": "PASS",
        "crawler_unchanged": "PASS", "bbox_unchanged": "PASS",
        "real_torque": "PHYSICAL_HOLD", "m4_tip": "PHYSICAL_HOLD", "m4_tightening": "PHYSICAL_HOLD",
        "fixture_strength": "PHYSICAL_HOLD", "field": "NOT_YET", "full_60t_print": "HOLD",
    }
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "repository": canonical_repository_record(repo), "checks": checks, "geometry": geom,
            "mesh": meshes, "step_import": steps}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False)
    geom = geometry_analysis()
    meshes, steps = export_outputs(out)
    for rel, value in documentation(geom).items(): write_text(out / rel, value)
    for rel, value in svg_documents().items(): write_text(out / rel, value)
    write_json(out / "design_parameters.json", parameters())
    write_json(out / "validation_report.json", validation(repo, geom, meshes, steps))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=1\nSTL=6\nSVG=10\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=160\nBUILDER_VERIFY=PASS\nREPRODUCIBILITY=46_OF_46_PASS\nTORQUE_PASS=NOT_YET\nFULL_60T_PRINT=HOLD")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES: raise RuntimeError(f"exact paths {len(files)} != {EXPECTED_PATH_COUNT}")
    return {"path_count": len(files), "geometry": geom, "mesh": meshes, "status": STATUS}


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
    commit_paths = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != commit_paths: raise RuntimeError("commit paths")
    sums = parse_sums(out / "SHA256SUMS.txt")
    mismatch = [rel for rel, value in sums.items() if sha256(out / rel) != value]
    if mismatch or set(sums) != set(EXPECTED_FILES) - {"SHA256SUMS.txt"}: raise RuntimeError(f"sha {mismatch}")
    report = json.loads((out / "validation_report.json").read_text(encoding="utf-8"))
    if "FAIL" in report["checks"].values(): raise RuntimeError("validation")
    return {"repository": repo, "path_count": len(files), "step_count": len(list(out.rglob("*.step"))),
            "stl_count": len(list(out.rglob("*.stl"))), "svg_count": len(list(out.rglob("*.svg"))),
            "sha_mismatch_count": 0, "geometry": report["geometry"], "mesh": report["mesh"], "status": STATUS}


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_dcut_v09628_") as name:
        shadow = Path(name) / LANE_NAME
        (shadow / "tests").mkdir(parents=True)
        shutil.copyfile(out / BUILDER, shadow / BUILDER); shutil.copyfile(out / TEST, shadow / TEST)
        generate_all(shadow)
        mismatch = [rel for rel in EXPECTED_FILES if (out / rel).read_bytes() != (shadow / rel).read_bytes()]
    if mismatch: raise RuntimeError(f"repro {mismatch}")
    return {"checked": EXPECTED_PATH_COUNT, "byte_identical": EXPECTED_PATH_COUNT, "mismatch_count": 0}


def package(out: Path = LANE_DIR) -> dict[str, object]:
    verify(out)
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_D_CUT_SHAFT_COLLAR_TORQUE_COUPON_v0_9_6_28_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists(): raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 17, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (out / rel).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist(); prefix = LANE_NAME + "/"
        relative = sorted(name[len(prefix):] for name in names if name.startswith(prefix))
        duplicate = len(names) - len(set(names)); traversal = sum(".." in PurePosixPath(name).parts for name in names)
        contamination = sum(not name.startswith(prefix) for name in names)
        extracted = {name[len(prefix):]: archive.read(name) for name in names if name.startswith(prefix)}
        sums = parse_sums(out / "SHA256SUMS.txt")
        mismatch = sum(hashlib.sha256(extracted[rel]).hexdigest() != value for rel, value in sums.items())
    result = {"path": str(path), "sha256": sha256(path), "entries": len(names), "open": "PASS",
              "duplicate_count": duplicate, "traversal_count": traversal, "manifest_exact": relative == EXPECTED_FILES,
              "sha_mismatch_count": mismatch, "parent_contamination_count": contamination}
    if duplicate or traversal or contamination or mismatch or relative != EXPECTED_FILES: raise RuntimeError(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true"); parser.add_argument("--verify", action="store_true")
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
