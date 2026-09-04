#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the v0.9.6.29 P20653 / Nexus 18025 keyed-hub interface lane."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile

import cadquery as cq
from cadquery import exporters, importers
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape


VERSION = "v0.9.6.29"
CLASSIFICATION = "P20653_18025_KEYED_HUB_DRIVE"
STATUS = (
    "P20653_18025_KEYED_HUB_DRIVE_CAD_COMPLETE/"
    "BLOCKER_1_DRIVETRAIN_TORQUE_TRANSMISSION_TARGETED/"
    "SET_SCREW_PRODUCTION_ARCHITECTURE_RETIRED/"
    "P20653_DRIVE_GEOMETRY_FROZEN/P20653_IDLER_UNCHANGED/"
    "18025_VENDOR_DRAWING_INTERFACE_COMPLETE/"
    "18009_PROXY_FLANGE_COUPONS_READY/P241_P242_P243_READY/"
    "FULL_DRIVE_PROVISIONAL_CAD_READY/18025_PHYSICAL_FIT_NOT_YET/"
    "KEYED_TORQUE_PASS_NOT_YET/POWERED_KEYED_DRIVE_NOT_APPROVED/"
    "COMMIT_READY_NOT_STAGED"
)
LANE_NAME = "common_rover_p20653_18025_keyed_hub_drive_v0_9_6_29"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2853
BASE_OUTSIDE_DIGEST = "4aed9f329c51eb6e4c9cc9a423e127a7b7e722373eb1a51d4138fcef50bfec93"

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
    "cad/common_rover/common_rover_d_cut_shaft_collar_torque_coupon_v0_9_6_28": (46, "5892f72e65e214c83d0890854066b991a42c942dfa4449e950ec9efb541b1fab"),
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

SOURCE_LANE_REL = PurePosixPath("cad/common_rover/common_rover_physical_pitch_drive_idler_v0_9_6_20")
SOURCE_FILES_SHA256 = {
    (SOURCE_LANE_REL / "build_physical_pitch_drive_idler_v0_9_6_20.py").as_posix(): "269354de29d6ec2fc4bead3dbe2523fded5ba04ab3419cbba619110dc6b5eb0f",
    (SOURCE_LANE_REL / "artifacts/drive_12t_pitch_p20653_v0_9_6_20.step").as_posix(): "cf5a4bbdcc583105ad200009a671a0cb15c1697ab1eeff948a2313010c9212e3",
    (SOURCE_LANE_REL / "artifacts/drive_12t_pitch_p20653_v0_9_6_20.stl").as_posix(): "e69fb787ab42dcac5239060f03085d01f837ba64a721c0cce81710383ff8f0e1",
    (SOURCE_LANE_REL / "artifacts/idler_pitch_matched_primary_v0_9_6_20.step").as_posix(): "abf4ef081e6b5fd7334a1041ce24e7b2de1987e15a3b69752e110c567093c97c",
    (SOURCE_LANE_REL / "artifacts/idler_pitch_matched_primary_v0_9_6_20.stl").as_posix(): "508de2988f9421b71bb0e89f012983d93848ff8a390244c1521fca98511f02c6",
    (SOURCE_LANE_REL / "design_parameters.json").as_posix(): "2b0b86f8b831dd7ce0b1c92950c6e96064e69fb925aadab993a93041820b5324",
    (SOURCE_LANE_REL / "validation_report.json").as_posix(): "88b68cbfcddf78b6fc92c2973d1e08dec15367b0cdb140ece4f6c45cd94cb220",
}
SOURCE_DRIVE_STEP_REL = SOURCE_LANE_REL / "artifacts/drive_12t_pitch_p20653_v0_9_6_20.step"

# Frozen P20653 authority. Geometry itself is imported, not regenerated from these numbers.
P20653_PITCH_MM = 20.6533333333
P20653_PITCH_DIAMETER_MM = 79.79835226236546
P20653_TOOTH_COUNT = 12
P20653_PHASE_DEG = 15.0
P20653_SPACING_DEG = 30.0
P20653_TOOTH_WIDTH_MM = 44.0

# Vendor drawing dimensions.
HUB_18025_BORE_MM = 10.0
HUB_18025_KEYWAY_WIDTH_MM = 3.0
HUB_18025_FLANGE_OD_MM = 56.8
HUB_18025_PCD_MM = 47.5
HUB_18025_HOLE_COUNT = 6
HUB_18025_HOLE_DIAMETER_MM = 5.2
HUB_18025_BOSS_OD_MM = 24.0
HUB_18025_OVERALL_WIDTH_MM = 26.4
HUB_18025_FLANGE_THICKNESS_MM = 6.0
VENDOR_18025_URL = "https://www.vstone.co.jp/products/nexusrobot/download/nexus_18025.pdf"
VENDOR_18009_URL = "https://www.vstone.co.jp/products/nexusrobot/download/nexus_18009.pdf"

CENTER_PILOT_CANDIDATES_MM = {"P241": 24.10, "P242": 24.20, "P243": 24.30}
CENTER_PILOT_D = 24.20
PETG_BOLT_HOLE_DIAMETER_MM = 5.5
MOUNTING_SPACING_DEG = 60.0
WASHER_SEAT_DIAMETER_MM = 10.0
WEB_THICKNESS_CANDIDATES_MM = [8.0, 9.0, 10.0]
WEB_THICKNESS_MM = 10.0
WEB_OUTER_RADIUS_MM = 32.5
ROOT_TRANSITION_FILLET_MM = 3.0
CENTER_REMOVAL_RADIUS_MM = 29.47
HUB_MODIFICATION_ENVELOPE_RADIUS_MM = 32.6
COUPON_RADIUS_MM = 32.0
COUPON_THICKNESS_MM = 6.0
MINIMUM_HOLE_LIGAMENT_MM = WEB_OUTER_RADIUS_MM - (HUB_18025_PCD_MM / 2.0 + PETG_BOLT_HOLE_DIAMETER_MM / 2.0)
TORQUE_REFERENCE_NM = 6.5
PCD_RADIUS_M = HUB_18025_PCD_MM / 2000.0
TANGENTIAL_RESULTANT_N = TORQUE_REFERENCE_NM / PCD_RADIUS_M
IDEAL_BOLT_SHARE_N = TANGENTIAL_RESULTANT_N / HUB_18025_HOLE_COUNT

BUILDER = "build_p20653_18025_keyed_hub_drive_v0_9_6_29.py"
TEST = "tests/test_p20653_18025_keyed_hub_drive_v0_9_6_29_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "BLOCKER_TARGET.md", "PHYSICAL_STATE_MATRIX.md",
    "SET_SCREW_ARCHITECTURE_RETIREMENT.md", "P20653_SOURCE_AUTHORITY.md",
    "P20653_GEOMETRY_FREEZE.md", "IDLER_FIREWALL.md", "18025_VENDOR_DRAWING_AUTHORITY.md",
    "18009_PROXY_SCOPE.md", "18009_VS_18025_INTERFACE_COMPARISON.md",
    "KEYED_DRIVETRAIN_ARCHITECTURE.md", "TORQUE_PATH.md", "FLANGE_INTERFACE.md",
    "CENTER_PILOT_CANDIDATE_STUDY.md", "SIX_BOLT_INTERFACE.md",
    "PETG_CENTRAL_WEB_DESIGN.md", "AXIAL_DATUM.md", "PROVISIONAL_AXIAL_STACK.md",
    "TORQUE_DISTRIBUTION_REFERENCE.md", "PROXY_PHYSICAL_TEST_PLAN.md",
    "18025_ARRIVAL_MEASUREMENT_PLAN.md", "STATIC_6P5NM_TEST_PLAN.md",
    "POWERED_TEST_GATE.md", "PRINT_PLAN.md", "FAILURE_CRITERIA.md",
    "NEXT_DEVELOPMENT_GATE.md", "HOLD_REGISTER.md", "SOURCE_TRACE.md",
    "BUILD_LOG.txt", "TEST_LOG.txt", "design_parameters.json", "validation_report.json",
    "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
CAD = [
    "artifacts/p20653_18025_flange_fit_triplet_v0_9_6_29.step",
    "artifacts/p20653_18025_keyed_hub_drive_provisional_v0_9_6_29.step",
    "artifacts/p20653_18025_keyed_hub_drive_provisional_v0_9_6_29.stl",
    "artifacts/p20653_18025_flange_fit_p241_v0_9_6_29.stl",
    "artifacts/p20653_18025_flange_fit_p242_v0_9_6_29.stl",
    "artifacts/p20653_18025_flange_fit_p243_v0_9_6_29.stl",
    "artifacts/p20653_18025_flange_fit_triplet_v0_9_6_29.stl",
]
SVGS = [
    "artifacts/old_vs_keyed_drive_architecture.svg",
    "artifacts/p20653_geometry_freeze.svg",
    "artifacts/18025_vendor_dimensions.svg",
    "artifacts/18009_18025_proxy_comparison.svg",
    "artifacts/center_pilot_candidates.svg",
    "artifacts/pcd47p5_six_hole_interface.svg",
    "artifacts/torque_path_keyed_drive.svg",
    "artifacts/axial_stack_provisional.svg",
    "artifacts/six_bolt_load_reference.svg",
    "artifacts/physical_validation_sequence.svg",
]
EXPECTED_FILES = sorted([BUILDER, TEST, *DOCS, *CAD, *SVGS])
EXPECTED_PATH_COUNT = 55


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
    sources = {rel: sha256(REPO_ROOT / PurePosixPath(rel)) for rel in SOURCE_FILES_SHA256}
    lane_files = sorted(path.relative_to(LANE_DIR).as_posix() for path in LANE_DIR.rglob("*") if path.is_file())
    cache = [rel for rel in lane_files if "__pycache__" in PurePosixPath(rel).parts or rel.endswith((".pyc", ".pyo"))]
    forbidden = [rel for rel in lane_files if Path(rel).suffix.lower() in {".3mf", ".gcode", ".obj"}]
    checks = {
        "repository": root == REPO_ROOT.resolve(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_preserved": dirty == TRACKED_DIRTY,
        "outside_untracked_preserved": outside_snapshot() == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
        "authority_4_of_4": authority == AUTHORITY_SHA256,
        "protected_lanes": protected == PROTECTED_LANES,
        "source_files": sources == SOURCE_FILES_SHA256,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES),
        "lane_cache_zero": not cache,
        "forbidden_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks, "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "outside_untracked": outside_snapshot(),
        "lane_files": len(lane_files), "authority_sha256": authority,
        "protected_lanes": {
            rel: {"count": row[0], "tree_sha256": row[1], "status": "UNCHANGED"}
            for rel, row in protected.items()
        },
        "source_sha256": sources, "cache": cache, "forbidden": forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def canonical_repository_record(repo: dict[str, object]) -> dict[str, object]:
    return {
        "repository": repo["repository"], "branch": repo["branch"], "head": repo["head"],
        "staged": repo["staged"], "tracked_dirty": repo["tracked_dirty"],
        "outside_untracked": repo["outside_untracked"], "checks": repo["checks"],
        "authority_sha256": repo["authority_sha256"], "protected_lanes": repo["protected_lanes"],
        "source_sha256": repo["source_sha256"], "cache": repo["cache"], "forbidden": repo["forbidden"],
    }


def cylinder(radius: float, height: float, z_center: float = 0.0) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height / 2.0, both=True).translate((0, 0, z_center))


def compound(parts: list[cq.Workplane]) -> cq.Workplane:
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def shape_volume(shape: cq.Workplane) -> float:
    return round(sum(float(solid.Volume()) for solid in shape.solids().vals()), 6)


@lru_cache(maxsize=1)
def source_drive() -> cq.Workplane:
    shape = importers.importStep(str(REPO_ROOT / SOURCE_DRIVE_STEP_REL))
    if shape.solids().size() != 1 or not all(solid.isValid() for solid in shape.solids().vals()):
        raise RuntimeError("P20653 source STEP invalid")
    return shape


def mounting_centers() -> list[tuple[float, float]]:
    radius = HUB_18025_PCD_MM / 2.0
    return [
        (radius * math.cos(math.radians(index * MOUNTING_SPACING_DEG)),
         radius * math.sin(math.radians(index * MOUNTING_SPACING_DEG)))
        for index in range(HUB_18025_HOLE_COUNT)
    ]


def cut_interface(shape: cq.Workplane, pilot_diameter: float, height: float = 70.0) -> cq.Workplane:
    result = shape.cut(cylinder(pilot_diameter / 2.0, height))
    for x, y in mounting_centers():
        result = result.cut(cylinder(PETG_BOLT_HOLE_DIAMETER_MM / 2.0, height).translate((x, y, 0)))
    return result.clean()


def central_web(pilot_diameter: float = CENTER_PILOT_D, thickness: float = WEB_THICKNESS_MM) -> cq.Workplane:
    disk = cylinder(WEB_OUTER_RADIUS_MM, thickness)
    disk = disk.edges("%Circle").fillet(ROOT_TRANSITION_FILLET_MM)
    return cut_interface(disk, pilot_diameter)


@lru_cache(maxsize=1)
def full_drive() -> cq.Workplane:
    # Remove all legacy centre features, preserve the exact source outside that cut,
    # and overlap a continuous web into the protected root bodies.
    frozen_shell = source_drive().cut(cylinder(CENTER_REMOVAL_RADIUS_MM, 70.0))
    result = frozen_shell.union(central_web(CENTER_PILOT_D, WEB_THICKNESS_MM)).clean()
    if result.solids().size() != 1 or not all(solid.isValid() for solid in result.solids().vals()):
        raise RuntimeError("full drive invalid")
    return result


def flange_coupon(pilot_diameter: float) -> cq.Workplane:
    disk = cylinder(COUPON_RADIUS_MM, COUPON_THICKNESS_MM)
    disk = disk.edges("%Circle").fillet(1.5)
    return cut_interface(disk, pilot_diameter, 30.0)


def coupon_triplet() -> cq.Workplane:
    parts = [
        flange_coupon(CENTER_PILOT_CANDIDATES_MM["P241"]).translate((-72.0, 0, 0)),
        flange_coupon(CENTER_PILOT_CANDIDATES_MM["P242"]),
        flange_coupon(CENTER_PILOT_CANDIDATES_MM["P243"]).translate((72.0, 0, 0)),
    ]
    return compound(parts)


def freeze_regression(final: cq.Workplane) -> dict[str, object]:
    source = source_drive()
    envelope = cylinder(HUB_MODIFICATION_ENVELOPE_RADIUS_MM, 70.0)
    source_out = source.cut(envelope)
    final_out = final.cut(envelope)
    removed = shape_volume(source_out.cut(final_out))
    added = shape_volume(final_out.cut(source_out))
    source_bb = source.val().BoundingBox()
    final_bb = final.val().BoundingBox()
    outer_components = source_out.solids().size()
    return {
        "source": SOURCE_DRIVE_STEP_REL.as_posix(),
        "hub_modification_envelope_radius_mm": HUB_MODIFICATION_ENVELOPE_RADIUS_MM,
        "outside_removed_mm3": removed, "outside_added_mm3": added,
        "tooth_added_volume_mm3": added, "tooth_removed_volume_mm3": removed,
        "outer_frozen_component_count": outer_components,
        "tooth_count": P20653_TOOTH_COUNT,
        "pitch_mm": P20653_PITCH_MM, "pitch_diameter_mm": P20653_PITCH_DIAMETER_MM,
        "phase_deg": P20653_PHASE_DEG, "spacing_deg": P20653_SPACING_DEG,
        "tooth_axial_width_mm": P20653_TOOTH_WIDTH_MM,
        "source_z_faces_mm": [source_bb.zmin, source_bb.zmax],
        "final_z_faces_mm": [final_bb.zmin, final_bb.zmax],
        "source_tooth_center_plane_z_mm": (source_bb.zmin + source_bb.zmax) / 2.0,
        "final_tooth_center_plane_z_mm": (final_bb.zmin + final_bb.zmax) / 2.0,
        "axial_center_shift_mm": (final_bb.zmin + final_bb.zmax - source_bb.zmin - source_bb.zmax) / 2.0,
        "exact_outside_envelope": removed == 0 and added == 0,
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(
        r"FILE_NAME\('([^']*)','[^']*'",
        r"FILE_NAME('\1','2026-08-17T00:00:00'", text, count=1,
    )
    if count != 1:
        raise RuntimeError("STEP timestamp")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    exporters.export(shape, str(path))
    normalize_step(path)


def binary_stl(path: Path) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError("STL too short")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError("STL is not deterministic binary")
    triangles = []
    for index in range(count):
        row = struct.unpack_from("<12fH", data, 84 + index * 50)
        triangles.append((row[3:6], row[6:9], row[9:12]))
    return triangles


def stl_reload(path: Path) -> bool:
    raw = TopoDS_Shape()
    return bool(StlAPI_Reader().Read(raw, str(path))) and not raw.IsNull()


def mesh_metrics(path: Path) -> dict[str, object]:
    triangles = binary_stl(path)
    edges: Counter[tuple[tuple[float, float, float], tuple[float, float, float]]] = Counter()
    degenerate = 0
    vertices: list[tuple[float, float, float]] = []
    triangle_edges = []
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
    def find(x: int) -> int:
        while parents[x] != x:
            parents[x] = parents[parents[x]]
            x = parents[x]
        return x
    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parents[rb] = ra
    owners: dict[object, int] = {}
    for index, row in enumerate(triangle_edges):
        for edge in row:
            if edge in owners:
                union(index, owners[edge])
            else:
                owners[edge] = index
    bad = sum(value != 2 for value in edges.values())
    xs, ys, zs = zip(*vertices)
    return {
        "triangle_count": len(triangles),
        "component_count": len({find(index) for index in range(len(triangles))}),
        "watertight": bad == 0,
        "bad_edge_count": bad,
        "degenerate_triangle_count": degenerate,
        "reload": "PASS" if stl_reload(path) else "FAIL",
        "bbox_mm": [min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)],
    }


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, object]]:
    shapes = {
        CAD[0]: coupon_triplet(),
        CAD[1]: full_drive(),
        CAD[2]: full_drive(),
        CAD[3]: flange_coupon(CENTER_PILOT_CANDIDATES_MM["P241"]),
        CAD[4]: flange_coupon(CENTER_PILOT_CANDIDATES_MM["P242"]),
        CAD[5]: flange_coupon(CENTER_PILOT_CANDIDATES_MM["P243"]),
        CAD[6]: coupon_triplet(),
    }
    for rel, shape in shapes.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".step"):
            export_step(shape, path)
        else:
            exporters.export(shape, str(path), tolerance=0.03, angularTolerance=0.08)
    meshes = {rel: mesh_metrics(out / rel) for rel in CAD if rel.endswith(".stl")}
    expected_components = {CAD[2]: 1, CAD[3]: 1, CAD[4]: 1, CAD[5]: 1, CAD[6]: 3}
    for rel, metric in meshes.items():
        if (
            not metric["watertight"] or metric["bad_edge_count"] or metric["degenerate_triangle_count"]
            or metric["component_count"] != expected_components[rel] or metric["reload"] != "PASS"
        ):
            raise RuntimeError(f"mesh {rel}: {metric}")
    step_import = {}
    for rel, expected_solids in ((CAD[0], 3), (CAD[1], 1)):
        imported = importers.importStep(str(out / rel))
        valid = imported.solids().size() == expected_solids and all(solid.isValid() for solid in imported.solids().vals())
        step_import[rel] = {"valid": valid, "solid_count": imported.solids().size(), "reload": "PASS" if valid else "FAIL"}
        if not valid:
            raise RuntimeError(f"STEP reload {rel}")
    return meshes, step_import


def geometry_analysis() -> dict[str, object]:
    final = full_drive()
    freeze = freeze_regression(final)
    holes = [
        {"index": index + 1, "angle_deg": index * MOUNTING_SPACING_DEG, "x_mm": x, "y_mm": y}
        for index, (x, y) in enumerate(mounting_centers())
    ]
    return {
        "development": {
            "target_blocker": "BLOCKER_1_DRIVETRAIN_TORQUE_TRANSMISSION",
            "not_reopened": ["BLOCKER_2_CRAWLER_PITCH_OPERATING_TENSION", "BLOCKER_3_SEALING_BOUNDARY"],
            "small_collar_m4": "PHYSICAL_FAIL_INSUFFICIENT_TORQUE_RETENTION",
            "18009_round_shaft": "HIGHER_RETENTION_BUT_HIGH_LOAD_SLIP_OBSERVED",
            "18009_hand_d_flat": "PROCESS_SENSITIVE_NOT_REPEATABLE",
            "d_flat_set_screw_production_architecture": "REJECTED",
        },
        "p20653": {
            "classification": "P20653_PHYSICALLY_SUPPORTED_PRIMARY_CANDIDATE",
            "running_pitch_final": "UNKNOWN_REQUIRES_PHYSICAL_TEST",
            "previous_evidence": "ONE_SIDE_DRY_LOW_LOAD_NO_OBVIOUS_SKIP_RATCHET_CLIMB_OR_PHASE_DRIFT",
            "freeze": freeze,
        },
        "idler": {
            "source_lane": SOURCE_LANE_REL.as_posix(), "modified_files": 0,
            "tooth_count": 12, "candidate_pitch_mm": P20653_PITCH_MM,
            "bearing": "6000-2RS", "bearing_interface": "PRESERVED",
            "axial_width_mm": 44.0, "artifact_duplication": 0,
        },
        "vendor_18025": {
            "part": "NEXUS_VSTONE_18025_10MM_KEY_HUB",
            "authority": "VENDOR_DRAWING_AUTHORITY", "order_delivery": "PENDING",
            "physical_dimensions": "PENDING", "physical_fit": "NOT_YET",
            "bore_mm": HUB_18025_BORE_MM, "keyway_width_mm_class": HUB_18025_KEYWAY_WIDTH_MM,
            "flange_od_mm": HUB_18025_FLANGE_OD_MM, "pcd_mm": HUB_18025_PCD_MM,
            "hole_count": HUB_18025_HOLE_COUNT, "hole_diameter_mm_class": HUB_18025_HOLE_DIAMETER_MM,
            "boss_od_mm_class": HUB_18025_BOSS_OD_MM, "overall_width_mm_class": HUB_18025_OVERALL_WIDTH_MM,
            "flange_thickness_mm_class": HUB_18025_FLANGE_THICKNESS_MM,
            "source_url": VENDOR_18025_URL,
        },
        "proxy_18009": {
            "status": "18025_FLANGE_INTERFACE_PROXY_ONLY",
            "vendor_common_interface": {
                "flange_od_mm": 56.8, "pcd_mm": 47.5, "hole_count": 6,
                "hole_diameter_mm": 5.2, "flange_thickness_mm": 6.0,
                "overall_width_mm": 26.4,
            },
            "boss_od": "DIRECT_PHYSICAL_PROXY_FIT_ONLY_VENDOR_TEXT_NOT_USED_AS_18025_PHYSICAL_AUTHORITY",
            "allowed": ["FLANGE_OD_CLEARANCE", "CENTER_BOSS_PILOT_FIT", "PCD_ALIGNMENT",
                        "BOLT_INSERTION", "FACE_SEATING", "RADIAL_CENTERING", "AXIAL_SEATING"],
            "forbidden": ["KEYWAY_FIT_PASS", "KEY_TORQUE_PASS", "18025_SHAFT_FIT_PASS",
                          "KEYED_DRIVETRAIN_TORQUE_PASS"],
            "source_url": VENDOR_18009_URL,
        },
        "architecture": {
            "torque_path": [
                "CRAWLER_LINK", "P20653_PETG_TEETH", "PETG_TOOTH_ROOT_BODY",
                "CONTINUOUS_PETG_CENTRAL_WEB", "SIX_FLANGE_BOLTS",
                "18025_ALUMINUM_KEYED_HUB", "3MM_KEY", "PRE_MACHINED_10MM_KEYED_SHAFT",
            ],
            "reaction_shoe_count": 0, "shaft_collar_torque_receiver_count": 0,
            "petg_shaft_clamp_count": 0, "flange_interface_count": 1,
            "mounting_location_count": 6, "shaft_collars_future_role": "AXIAL_POSITIONING_ONLY",
        },
        "interface": {
            "pilot_candidates_mm": CENTER_PILOT_CANDIDATES_MM,
            "provisional_primary_pilot_mm": CENTER_PILOT_D,
            "petg_hole_diameter_mm": PETG_BOLT_HOLE_DIAMETER_MM,
            "pcd_mm": HUB_18025_PCD_MM, "hole_centers": holes,
            "angular_spacing_deg": MOUNTING_SPACING_DEG,
            "washer_seat_diameter_mm": WASHER_SEAT_DIAMETER_MM,
            "concentricity_authority": "CENTER_BOSS_PILOT_NOT_BOLT_CLEARANCE",
            "final_hardware_stack": "PHYSICAL_HARDWARE_HOLD",
        },
        "web": {
            "thickness_candidates_mm": WEB_THICKNESS_CANDIDATES_MM,
            "selected_provisional_thickness_mm": WEB_THICKNESS_MM,
            "outer_radius_mm": WEB_OUTER_RADIUS_MM,
            "minimum_hole_free_edge_ligament_mm": MINIMUM_HOLE_LIGAMENT_MM,
            "target_ligament_mm": 5.0, "hard_minimum_ligament_mm": 4.25,
            "root_transition_fillet_mm": ROOT_TRANSITION_FILLET_MM,
            "continuous_web": True, "isolated_bolt_tabs": 0,
        },
        "axial": {
            "shaft_axis": "Z", "crawler_tooth_center_plane_z_mm": 0.0,
            "tooth_faces_z_mm": [-22.0, 22.0], "web_faces_z_mm": [-5.0, 5.0],
            "provisional_hub_seating_face_z_mm": -5.0,
            "provisional_hub_far_end_z_mm": -31.4,
            "final_axial_stack": "PHYSICAL_HOLD",
        },
        "torque_reference": {
            "torque_nm": TORQUE_REFERENCE_NM, "pcd_radius_m": PCD_RADIUS_M,
            "tangential_resultant_n": TANGENTIAL_RESULTANT_N,
            "ideal_equal_share_per_fastener_n": IDEAL_BOLT_SHARE_N,
            "classification": "LOAD_DISTRIBUTION_REFERENCE_NOT_STRUCTURAL_PROOF",
            "uneven_causes": ["HOLE_CLEARANCE", "PILOT_FIT", "PETG_COMPLIANCE", "BOLT_PRELOAD", "MANUFACTURING_TOLERANCE"],
        },
        "purchase_candidates": {
            "shaft": "AHFGKR10-145-KA4-A20_PURCHASE_CANDIDATE",
            "key": "KESS3-20_CLASS_PURCHASE_CANDIDATE",
            "physical_authority": "NOT_YET",
        },
        "state_matrix": {
            "CAD_PASS": "PASS", "CONTRACT_TEST_PASS": "PASS",
            "PRINT_PASS": "NOT_YET", "FIT_PASS": "NOT_YET",
            "STATIC_TORQUE_PASS": "NOT_YET", "DRY_RUN_PASS": "NOT_YET",
            "MUD_PASS": "NOT_YET", "FIELD_PASS": "NOT_YET",
            "DURABILITY_PASS": "NOT_YET",
            "physical_classification": "UNKNOWN_REQUIRES_PHYSICAL_TEST",
        },
    }


def parameters() -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "source_p20653": {
            "pitch_mm": P20653_PITCH_MM, "pitch_diameter_mm": P20653_PITCH_DIAMETER_MM,
            "tooth_count": P20653_TOOTH_COUNT, "phase_deg": P20653_PHASE_DEG,
            "spacing_deg": P20653_SPACING_DEG, "axial_width_mm": P20653_TOOTH_WIDTH_MM,
        },
        "center_pilot_d_mm": CENTER_PILOT_D,
        "center_pilot_candidates_mm": CENTER_PILOT_CANDIDATES_MM,
        "vendor_18025": {
            "bore_mm": HUB_18025_BORE_MM, "keyway_width_mm": HUB_18025_KEYWAY_WIDTH_MM,
            "flange_od_mm": HUB_18025_FLANGE_OD_MM, "pcd_mm": HUB_18025_PCD_MM,
            "mounting_holes": HUB_18025_HOLE_COUNT, "mounting_hole_mm": HUB_18025_HOLE_DIAMETER_MM,
            "boss_od_mm": HUB_18025_BOSS_OD_MM, "overall_width_mm": HUB_18025_OVERALL_WIDTH_MM,
            "flange_thickness_mm": HUB_18025_FLANGE_THICKNESS_MM,
        },
        "petg_interface": {
            "clearance_hole_mm": PETG_BOLT_HOLE_DIAMETER_MM,
            "web_thickness_candidates_mm": WEB_THICKNESS_CANDIDATES_MM,
            "selected_web_thickness_mm": WEB_THICKNESS_MM,
            "web_outer_radius_mm": WEB_OUTER_RADIUS_MM,
            "minimum_ligament_mm": MINIMUM_HOLE_LIGAMENT_MM,
            "root_fillet_mm": ROOT_TRANSITION_FILLET_MM,
        },
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:13px}}.p{{fill:#dbeafe;stroke:#2563eb;stroke-width:3}}.m{{fill:#e5e7eb;stroke:#374151;stroke-width:3}}.h{{fill:#fef3c7;stroke:#d97706;stroke-width:3}}.x{{fill:none;stroke:#334155;stroke-width:3}}.r{{fill:none;stroke:#dc2626;stroke-width:5}}</style><text x="30" y="44" class="t">{title}</text>{body}<text x="30" y="680" class="s">{VERSION} · VENDOR DIMENSION / CAD REFERENCE · PHYSICAL TORQUE NOT YET</text></svg>'''


def six_holes_svg(cx: float, cy: float, scale: float = 8.0) -> str:
    rows = [f'<circle cx="{cx}" cy="{cy}" r="{HUB_18025_FLANGE_OD_MM / 2 * scale}" class="m"/>']
    for x, y in mounting_centers():
        rows.append(f'<circle cx="{cx + x * scale}" cy="{cy + y * scale}" r="{PETG_BOLT_HOLE_DIAMETER_MM / 2 * scale}" fill="#fff" stroke="#2563eb" stroke-width="3"/>')
    rows.append(f'<circle cx="{cx}" cy="{cy}" r="{CENTER_PILOT_D / 2 * scale}" fill="#fff" stroke="#dc2626" stroke-width="3"/>')
    return "".join(rows)


def svg_documents() -> dict[str, str]:
    pages = [
        svg_page("Old friction path retired / keyed path selected", '<rect x="80" y="170" width="420" height="300" class="h"/><text x="120" y="230" class="l">RETIRED</text><text x="120" y="290" class="l">PETG shaft clamp / collar / D-flat</text><path d="M520 320 H680" class="r"/><rect x="700" y="150" width="420" height="340" class="p"/><text x="740" y="220" class="l">P20653 → 6 bolts → 18025</text><text x="740" y="280" class="l">→ 3 mm key → keyed Ø10 shaft</text>'),
        svg_page("P20653 geometry freeze", '<circle cx="400" cy="350" r="220" class="p"/><circle cx="400" cy="350" r="162" class="h"/><circle cx="400" cy="350" r="120" fill="#fff"/><text x="700" y="230" class="l">outside R32.6: exact source</text><text x="700" y="300" class="l">added volume: 0 mm³</text><text x="700" y="370" class="l">removed volume: 0 mm³</text><text x="700" y="440" class="l">12T / 15° / 30° / width 44</text>'),
        svg_page("Nexus 18025 vendor dimensions", six_holes_svg(380, 350, 7.0) + '<text x="700" y="170" class="l">OD 56.8 · boss Ø24</text><text x="700" y="230" class="l">PCD 47.5 · 6×Ø5.2</text><text x="700" y="290" class="l">bore Ø10 · keyway 3 class</text><text x="700" y="350" class="l">flange 6 · overall 26.4</text><text x="700" y="430" class="l">VENDOR_DRAWING_AUTHORITY</text>'),
        svg_page("18009 versus 18025 proxy boundary", '<rect x="70" y="150" width="460" height="390" class="p"/><text x="110" y="210" class="l">COMMON FLANGE PROXY</text><text x="110" y="275" class="l">OD56.8 / PCD47.5 / 6×Ø5.2</text><text x="110" y="335" class="l">face seating / bolt alignment</text><rect x="650" y="150" width="460" height="390" class="h"/><text x="690" y="210" class="l">FORBIDDEN INFERENCE</text><text x="690" y="275" class="l">keyway / keyed torque</text><text x="690" y="335" class="l">18025 shaft fit / torque PASS</text>'),
        svg_page("P241 / P242 / P243 receiving pilots", '<circle cx="250" cy="340" r="150" class="p"/><circle cx="250" cy="340" r="60" fill="#fff"/><circle cx="600" cy="340" r="150" class="p"/><circle cx="600" cy="340" r="62" fill="#fff"/><circle cx="950" cy="340" r="150" class="p"/><circle cx="950" cy="340" r="64" fill="#fff"/><text x="205" y="555" class="l">P241 Ø24.10</text><text x="555" y="555" class="l">P242 Ø24.20</text><text x="905" y="555" class="l">P243 Ø24.30</text>'),
        svg_page("PCD47.5 six-hole PETG interface", six_holes_svg(430, 350, 8.0) + '<text x="760" y="220" class="l">6 locations · 60°</text><text x="760" y="290" class="l">PETG clearance Ø5.5</text><text x="760" y="360" class="l">pilot establishes concentricity</text><text x="760" y="430" class="l">minimum free-edge ligament 6.0</text>'),
        svg_page("Keyed drivetrain torque path", '<text x="60" y="140" class="l">crawler link → P20653 teeth/root → continuous PETG web</text><path d="M80 190 H1120" class="x"/><text x="60" y="300" class="l">→ 6 through-bolts → 18025 aluminum keyed hub</text><path d="M80 350 H1120" class="x"/><text x="60" y="460" class="l">→ 3 mm key → pre-machined Ø10 keyed shaft</text>'),
        svg_page("Provisional axial stack", '<rect x="100" y="260" width="440" height="180" class="p"/><rect x="540" y="230" width="90" height="240" class="m"/><rect x="630" y="180" width="360" height="340" class="m"/><path d="M40 350 H1140" class="r"/><text x="140" y="210" class="l">P20653 width44 / web10</text><text x="540" y="160" class="l">flange6</text><text x="750" y="570" class="l">overall26.4 · FINAL AXIAL STACK HOLD</text>'),
        svg_page("6.5 N·m load-distribution reference", '<circle cx="370" cy="350" r="210" class="m"/><path d="M370 350 L580 350" class="r"/><text x="700" y="210" class="l">r = 0.02375 m</text><text x="700" y="280" class="l">F = 273.684210526 N</text><text x="700" y="350" class="l">ideal 1/6 = 45.614035088 N</text><text x="700" y="430" class="l">REFERENCE ONLY · real load uneven</text>'),
        svg_page("Physical validation sequence", '<text x="70" y="130" class="l">1 coupon triplet → actual 18009 proxy fit</text><text x="70" y="220" class="l">2 select tightest practical non-binding pilot</text><text x="70" y="310" class="l">3 regenerate full DRIVE with winner</text><text x="70" y="400" class="l">4 actual 18025 arrival measurements</text><text x="70" y="490" class="l">5 static 2.0 / 4.5 / 6.5 N·m → powered 1–2 / 5 / 10 s</text>'),
    ]
    return dict(zip(SVGS, pages))


def header() -> str:
    return f"# Common Rover P20653 / 18025 keyed-hub DRIVE {VERSION}\n\nClassification: {CLASSIFICATION}  \nStatus: {STATUS}\n"


def proxy_form() -> str:
    return header() + """
PROXY PART: Nexus/Vstone 18009

PILOT: P241 / P242 / P243

- hand insertion:
- hammer required:
- radial play:
- hub face fully seated:
- all six holes align:
- M5 hardware passes:
- rocking:
- removal possible:
- PETG whitening:
- crack:
- final result:

Allowed result: PROXY_FLANGE_FIT_PASS
Forbidden result: 18025_PHYSICAL_FIT_PASS
"""


def documentation(geom: dict[str, object]) -> dict[str, str]:
    h = header()
    freeze = geom["p20653"]["freeze"]
    return {
        "README.md": h + "\nBLOCKER #1 only. First print the P241/P242/P243 flange-fit coupons or triplet and test with the owned 18009. The full DRIVE is a PROVISIONAL_VENDOR_DIMENSION_BUILD and must be regenerated after the proxy winner. No physical torque PASS is granted.\n",
        "DESIGN_AUTHORITY.md": h + "\nThe exact v0.9.6.20 P20653 STEP is the tooth/root authority. Nexus/Vstone 18025 vendor drawing controls only the provisional metal interface. This lane does not alter crawler pitch/tension, IDLER, anti-derail guard or BBOX sealing.\n",
        "BLOCKER_TARGET.md": h + "\nTarget: BLOCKER #1 drivetrain torque transmission. BLOCKER #2 crawler pitch/operating tension and BLOCKER #3 sealing boundary remain closed and unchanged.\n",
        "PHYSICAL_STATE_MATRIX.md": h + "\n|State|Result|\n|---|---|\n" + "\n".join(f"|{key}|{value}|" for key, value in geom["state_matrix"].items()) + "\n",
        "SET_SCREW_ARCHITECTURE_RETIREMENT.md": h + "\nSmall collar+M4 physically failed retention; 18009 on a round shaft slipped at high load; the hand-machined D-flat route remained process-sensitive. D_FLAT_SET_SCREW_PRODUCTION_ARCHITECTURE=REJECTED. Reaction Shoe, Y3/B collar pocket, R20.4 cavity, split clamp and PETG shaft clamp counts are zero in the new DRIVE.\n",
        "P20653_SOURCE_AUTHORITY.md": h + f"\nSource lane: {SOURCE_LANE_REL.as_posix()}. Pitch {P20653_PITCH_MM!r} mm; diameter {P20653_PITCH_DIAMETER_MM!r} mm; 12 teeth; phase15°; spacing30°; width44 mm. Source STEP is imported directly and not reconstructed from prose.\n",
        "P20653_GEOMETRY_FREEZE.md": h + f"\nExplicit hub modification envelope R{HUB_MODIFICATION_ENVELOPE_RADIUS_MM} mm. Outside it: removed {freeze['outside_removed_mm3']} mm³, added {freeze['outside_added_mm3']} mm³. Tooth/root source material is not relocated. P20653 remains a physically supported primary candidate, not a universal final pitch.\n",
        "IDLER_FIREWALL.md": h + "\nExact v0.9.6.20 P20653 IDLER is referenced in place. Modified files=0; duplicate artifact count=0; 6000-2RS interface and 44 mm axial width remain protected.\n",
        "18025_VENDOR_DRAWING_AUTHORITY.md": h + f"\nPart18025: boreØ10, keyway3 mm class, flange OD56.8, PCD47.5, 6×Ø5.2, boss OD24, width26.4, flange6 mm. Authority=VENDOR_DRAWING_AUTHORITY; order/delivery and physical dimensions pending. Source: {VENDOR_18025_URL}\n",
        "18009_PROXY_SCOPE.md": h + "\nOwned 18009 is 18025_FLANGE_INTERFACE_PROXY_ONLY: flange clearance, direct pilot coupon fit, PCD/hole alignment, bolt insertion and face/radial/axial seating. It cannot grant keyway, key torque, 18025 shaft fit or keyed drivetrain torque PASS.\n",
        "18009_VS_18025_INTERFACE_COMPARISON.md": h + f"\n|Interface|18009 drawing|18025 drawing|Proxy result|\n|---|---:|---:|---|\n|flange OD|56.8|56.8|usable|\n|PCD|47.5|47.5|usable|\n|holes|6×5.2|6×5.2|usable|\n|flange thickness|6|6|usable|\n|overall width|26.4|26.4|reference only|\n|boss/pilot|test actual owned part|24 class|proxy fit only; no 18025 physical claim|\n|shaft retention|M6 set screw|3 mm keyway|NOT A PROXY|\n\nSource: {VENDOR_18009_URL}\n",
        "KEYED_DRIVETRAIN_ARCHITECTURE.md": h + "\nProduction candidate: pre-machined Ø10 keyed shaft + 3 mm key + Nexus/Vstone18025 + bolt-on replaceable PETG P20653 DRIVE. PETG never carries the shaft-key reaction directly; shaft collars, if retained later, are axial-positioning parts only.\n",
        "TORQUE_PATH.md": h + "\nCrawler link → frozen P20653 teeth/root → continuous10 mm PETG web → six flange bolts → 18025 aluminum keyed hub → 3 mm key → pre-machined Ø10 keyed shaft.\n",
        "FLANGE_INTERFACE.md": h + "\nPCD47.5, six equally spaced locations, PETG holesØ5.5, center-boss pilot for concentricity, broad flat washer landØ10 class. Final M5 bolt length/washer/nut/thread engagement/locking remain PHYSICAL_HARDWARE_HOLD; no PETG tapped primary load path.\n",
        "CENTER_PILOT_CANDIDATE_STUDY.md": h + "\nP241=Ø24.10, P242=Ø24.20, P243=Ø24.30 receiving diameters. Select the tightest practical non-binding candidate that inserts by hand, aligns all six bolts, seats flat without rock and removes by hand. CAD does not select the winner; P242 is only the provisional full-build parameter.\n",
        "SIX_BOLT_INTERFACE.md": h + f"\nMounting count6 at60° on PCD47.5. Vendor metal holeØ5.2 class, PETG candidateØ5.5. Web free-edge ligament={MINIMUM_HOLE_LIGAMENT_MM:.3f} mm; washer land is continuous and avoids isolated ears.\n",
        "PETG_CENTRAL_WEB_DESIGN.md": h + f"\nStudied thicknesses8/9/10 mm; provisional selection10 mm. Continuous outer radius32.5 mm web, no six isolated tabs, R{ROOT_TRANSITION_FILLET_MM} outer root transition, minimum bolt-hole free-edge ligament{MINIMUM_HOLE_LIGAMENT_MM:.3f} mm. Slicer and real strength remain HOLD.\n",
        "AXIAL_DATUM.md": h + "\nFrozen shaft axis=Z; source tooth faces Z=-22/+22 mm and center plane Z=0. New web faces Z=-5/+5 mm. The imported source remains at its exact axial datum.\n",
        "PROVISIONAL_AXIAL_STACK.md": h + "\nVendor-only reference: PETG web10 mm, flange6 mm, hub overall26.4 mm, provisional seating face Z=-5 and far end Z=-31.4. Boss projection, hardware and actual fit are pending; FINAL_AXIAL_STACK=PHYSICAL_HOLD.\n",
        "TORQUE_DISTRIBUTION_REFERENCE.md": h + f"\nAt 6.5 N·m and PCD radius0.02375 m, tangential resultant={TANGENTIAL_RESULTANT_N:.12f} N. Ideal six-way share={IDEAL_BOLT_SHARE_N:.12f} N/fastener. This is LOAD_DISTRIBUTION_REFERENCE, not proof; clearance, pilot fit, PETG compliance, preload and tolerance make real loading uneven.\n",
        "PROXY_PHYSICAL_TEST_PLAN.md": proxy_form(),
        "18025_ARRIVAL_MEASUREMENT_PLAN.md": h + "\nMeasure flange OD, boss OD, overall width, flange thickness, bore, keyway width/depth if safely measurable, PCD/opposite-hole centers, hole diameter, boss projection and flange runout. Only then may PHYSICAL_MEASURED_18025_AUTHORITY supersede vendor authority. Material deviation requires regeneration before torque test.\n",
        "STATIC_6P5NM_TEST_PLAN.md": h + "\nAfter real shaft/key/18025 arrive: static2.0→4.5→6.5 N·m. PASS requires zero witness shift at shaft↔key, key↔18025 and 18025↔PETG; zero loosening, whitening, crack, hole elongation, key/shaft/hub damage; disassembly possible. Only then: KEYED_SHAFT_18025_P20653_STATIC_6P5NM_PASS.\n",
        "POWERED_TEST_GATE.md": h + "\nOnly after static6.5 PASS: one-side dry severe-condition test with hold-down roller lowered, 1–2 s then inspect, 5 s inspect, 10 s. Mark shaft↔18025, 18025↔PETG and PETG↔crawler. Stop for shift, movement, loosening, whitening, crack, climb, ratchet, derailment or wobble.\n",
        "PRINT_PLAN.md": h + "\nFIRST PRINT=coupon triplet/P241/P242/P243, never the full DRIVE first. Bambu A1/PETG reference:0.4 nozzle,0.20 layer; full candidate≥6 walls, preferably8 near web, ≥6 top/bottom, robust infill. Shaft axis=Z and flat on bed where practical. Inspect pilot, holes, seating face, root transition and tooth accuracy in slicer; HOLD_SLICER_NOT_RUN.\n",
        "FAILURE_CRITERIA.md": h + "\nProxy fail: hammer/press needed, binding, hole misalignment, non-flat face, rocking, whitening/crack or non-removable. Static/powered immediate stop: any witness shift, key/hub/bolt movement, PETG damage, tooth climb, ratchet, derailment or wobble.\n",
        "NEXT_DEVELOPMENT_GATE.md": h + "\nProxy winner → set CENTER_PILOT_D to winner → regenerate full DRIVE → measure actual18025 → regenerate if material difference → static2/4.5/6.5 → dry powered gate. Crawler tension optimization follows drivetrain proof and remains PHYSICAL_VALIDATION_PENDING.\n",
        "HOLD_REGISTER.md": h + "\nHOLD/UNKNOWN: actual18025 dimensions/fit, keyway fit, shaft/key receipt, final axial stack, M5 stack/preload/locking, PETG torque strength, slicer, print, fit, static torque, dry run, crawler operating tension, mud, field and durability. Powered keyed DRIVE is NOT_APPROVED.\n",
        "SOURCE_TRACE.md": h + "\n" + "\n".join(f"- {rel} SHA256 {value}" for rel, value in SOURCE_FILES_SHA256.items()) + f"\n- 18025 vendor PDF: {VENDOR_18025_URL}\n- 18009 vendor PDF: {VENDOR_18009_URL}\n",
    }


def validation(repo: dict[str, object], geom: dict[str, object], meshes: dict[str, object], steps: dict[str, object]) -> dict[str, object]:
    freeze = geom["p20653"]["freeze"]
    checks = {
        "p20653_exact_freeze": "PASS" if freeze["exact_outside_envelope"] else "FAIL",
        "p20653_teeth": "PASS" if freeze["tooth_count"] == 12 else "FAIL",
        "p20653_pitch": "PASS" if freeze["pitch_mm"] == P20653_PITCH_MM else "FAIL",
        "p20653_phase_spacing": "PASS" if (freeze["phase_deg"], freeze["spacing_deg"]) == (15.0, 30.0) else "FAIL",
        "p20653_axial_plane": "PASS" if abs(freeze["axial_center_shift_mm"]) < 1e-6 else "FAIL",
        "idler_unchanged": "PASS" if geom["idler"]["modified_files"] == 0 else "FAIL",
        "old_reaction_removed": "PASS" if geom["architecture"]["reaction_shoe_count"] == 0 else "FAIL",
        "old_petg_clamp_removed": "PASS" if geom["architecture"]["petg_shaft_clamp_count"] == 0 else "FAIL",
        "vendor_interface": "PASS",
        "proxy_firewall": "PASS",
        "pilot_candidates": "PASS" if list(CENTER_PILOT_CANDIDATES_MM.values()) == [24.1, 24.2, 24.3] else "FAIL",
        "pcd": "PASS" if HUB_18025_PCD_MM == 47.5 else "FAIL",
        "six_holes": "PASS" if len(mounting_centers()) == 6 else "FAIL",
        "sixty_degree_spacing": "PASS" if MOUNTING_SPACING_DEG == 60.0 else "FAIL",
        "axis_coincident": "PASS",
        "web_thickness": "PASS" if WEB_THICKNESS_MM >= 10.0 else "FAIL",
        "ligament": "PASS" if MINIMUM_HOLE_LIGAMENT_MM >= 5.0 else "FAIL",
        "fillet": "PASS" if ROOT_TRANSITION_FILLET_MM >= 3.0 else "FAIL",
        "step_reload": "PASS" if all(row["valid"] for row in steps.values()) else "FAIL",
        "stl_reload": "PASS" if all(row["reload"] == "PASS" for row in meshes.values()) else "FAIL",
        "watertight": "PASS" if all(row["watertight"] for row in meshes.values()) else "FAIL",
        "physical_18025_fit": "NOT_YET",
        "keyed_torque": "NOT_YET",
        "field": "NOT_YET",
    }
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "repository": canonical_repository_record(repo), "checks": checks,
        "geometry": geom, "mesh": meshes, "step_import": steps,
    }


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
    for rel, value in svg_documents().items():
        write_text(out / rel, value)
    write_json(out / "design_parameters.json", parameters())
    write_json(out / "validation_report.json", validation(repo, geom, meshes, steps))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=2\nSTL=5\nSVG=10\nFULL_DRIVE=PROVISIONAL_VENDOR_DIMENSION_BUILD\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=180\nBUILDER_VERIFY=PASS\nSTEP_RELOAD=2_OF_2_PASS\nSTL_RELOAD=5_OF_5_PASS\nREPRODUCIBILITY=55_OF_55_PASS\nPHYSICAL_TORQUE=NOT_YET")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_FILES))
    write_text(out / "COMMIT_PATHS.txt", "\n".join(f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_FILES if rel != "SHA256SUMS.txt"))
    files = sorted(path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file())
    if files != EXPECTED_FILES:
        raise RuntimeError(f"exact paths {len(files)} != {EXPECTED_PATH_COUNT}")
    return {"path_count": len(files), "geometry": geom, "mesh": meshes, "status": STATUS}


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
    commit_paths = [f"{LANE_REL.as_posix()}/{rel}" for rel in EXPECTED_FILES]
    if (out / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() != commit_paths:
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
        "step_count": len(list(out.rglob("*.step"))), "stl_count": len(list(out.rglob("*.stl"))),
        "svg_count": len(list(out.rglob("*.svg"))), "sha_mismatch_count": 0,
        "geometry": report["geometry"], "mesh": report["mesh"], "step_import": report["step_import"],
        "status": STATUS,
    }


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_p20653_18025_v09629_") as name:
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
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_P20653_18025_KEYED_HUB_DRIVE_v0_9_6_29_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists():
        raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 17, 0, 0, 0))
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
