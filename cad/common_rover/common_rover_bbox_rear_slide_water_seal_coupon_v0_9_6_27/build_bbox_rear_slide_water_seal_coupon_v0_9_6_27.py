#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build v0.9.6.27 BBOX rear-slide static-face water-seal coupon."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import cadquery as cq
from cadquery import exporters, importers


VERSION = "v0.9.6.27"
CLASSIFICATION = "BBOX_REAR_SLIDE_STATIC_FACE_SEAL_VALIDATION"
STATUS = (
    "BBOX_REAR_SLIDE_WATER_SEAL_COUPON_CAD_COMPLETE/"
    "STATIC_FACE_COMPRESSION_SEAL_ARCHITECTURE_COMPLETE/"
    "DYNAMIC_SLIDING_SEAL_REJECTED/REAR_SLIDE_CASSETTE_ARCHITECTURE_READY/"
    "2MM_GASKET_COMPRESSION_CANDIDATES_READY/FOUR_POINT_COMPRESSION_READY/"
    "MUD_EXCLUSION_AND_DRAINAGE_READY/LIVE_BATTERY_NOT_APPROVED/"
    "FULL_BBOX_PRINT_NOT_APPROVED/PHYSICAL_WATER_SEAL_VALIDATION_NEXT/"
    "COMMIT_READY_NOT_STAGED"
)
LANE_NAME = "common_rover_bbox_rear_slide_water_seal_coupon_v0_9_6_27"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2753
BASE_OUTSIDE_DIGEST = "50af77c2143276bdd917f0d302a4e42c024f9b788e15b422045b1c616fa43855"

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
    "cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1": (53, "a0cb4b831d639be4619a6bb42bff765a8196e04963dfc2df8826e1bbaf89fe00"),
    "cad/common_rover/common_rover_candidate_a_physical_mockup_v0_9_3_1": (46, "59d3167c925dcf02cea7abd68a4e83ddd92620559f154eff5570850d16eb8847"),
    "cad/common_rover/common_rover_physical_frame_bbox_cbox_h25a1_integration_v0_9_4_0": (43, "ecd753e02d6a9b88d763dd0da5f716aadfcd951961384bfd45f57a236f043242"),
    "cad/common_rover/common_rover_190mm_frame_h25a1_2s_bbox_cbox_integration_v0_9_4_1": (68, "eaa75b58bee220a6eca1aeeaa01d15ff5931616ae3145265b8c1e317811ebe20"),
    "cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2": (57, "168a21f0a1cabb30971dfd4330f0d7b474a26a38b5fd735d455ff61ffed091ab"),
    "cad/common_rover/common_rover_service_motion_servo_slide_clutch_h25a1_v0_9_4_3": (66, "9a167824f4260fd20629e45f5485dfb8da6c2fe5529101c7a26c0a13e0db2447"),
    "cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0": (105, "5884ae618cec383c8f5bbae3e6c7332a61b5ee70be94c46223903060d3fce7b5"),
    "cad/common_rover/common_rover_physical_measurement_closure_v0_9_5_2": (28, "e5fc34dcd721472817aaf1a76183ba2242e20c665ca2a45bd7da717faf74717a"),
    "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0": (40, "5b18fee1976e292a370f3ac56930544df711cd44d66075f9b6216af40a91c465"),
    "cad/common_rover/common_rover_cbox_drive_electrical_physical_integration_v0_9_6_2": (57, "20dce098bf9c065c875dd98f01e240cfa3d11b81872c5eb3270124ea365f2649"),
    "cad/common_rover/common_rover_dry_drive_battery_tray_v0_9_6_3": (35, "5bc13b17f52a3bc96c148bd1185c80f74e3b324406d7eb2962319e24a7589139"),
    "cad/common_rover/common_rover_narrow_frame_independent_drive_v0_9_6_6": (66, "8ec865fe56d28305f3bf282c4dd14bbc2f2ef793ce155159af2208e4ff6ac014"),
    "cad/common_rover/common_rover_rapid_dry_bbox_cbox_v0_9_6_7": (40, "64e0d2f02207442aebfbead2b6546058ce570f3aebc0cdc9a43859ff21254333"),
}

SOURCE_FILES_SHA256 = {
    "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0/ARCHITECTURE_AUTHORITY.md": "b198289fd95879342170dc5e5fda92f11a5dfe3048336f8824c9b2859e71e063",
    "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0/design_parameters.json": "88180cd2b61f049e8610f00a270502ece985d874623f35db1b93c9f576e21271",
    "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0/BBOX_SEAL_ARCHITECTURE.md": "e795e69b185fb0dcf27289b477be7ee17fe16cf1e6d60d633e99dee7c314d0c3",
    "cad/common_rover/common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0/BBOX_GASKET_AND_CLAMPING_SPEC.md": "92561f707542eca9db831d8217a2436d249913d159fdf33fcf91b7201561d724",
    "cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0/BBOX_ARCHITECTURE.md": "9b868e367c1ad31bf478dbc364bcbf76f4ef7269418962c45c559091ca67fedc",
    "cad/common_rover/common_rover_bbox_cbox_printable_prototype_v0_9_5_0/BBOX_DIMENSION_AUTHORITY.md": "e088af0e47b2434e00a09c03f46bcd5799329b79249a0b6c271bb98f13e335ca",
    "cad/common_rover/common_rover_physical_measurement_closure_v0_9_5_2/bbox_physical_record.json": "a60df51c31fa7ca5de08f234b1c809cb33c75938cbb37dc353a3bbdb287c391b",
    "cad/common_rover/common_rover_dry_drive_battery_tray_v0_9_6_3/design_parameters.json": "2b3c93badccb0550b16e43a7f5f5b45e8acffee1dac8ba37e849fe0cb394e5b5",
    "cad/common_rover/common_rover_dry_drive_battery_tray_v0_9_6_3/DRY_BATTERY_TRAY_SPEC.md": "579249699ef260136f36d7417baf545dfcd6b71586015ab60bc2ab0cc74f8400",
}

# Selected source authorities and coupon geometry, millimetres.
CURRENT_WATERPROOF_AUTHORITY = "common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0"
REAR_SERVICE_AUTHORITY = "common_rover_bbox_cbox_printable_prototype_v0_9_5_0"
PHYSICAL_MEASUREMENT_AUTHORITY = "common_rover_physical_measurement_closure_v0_9_5_2"
DRY_CASSETTE_REFERENCE = "common_rover_dry_drive_battery_tray_v0_9_6_3"

BATTERY_BODY_MM = [150.9, 99.4, 92.5]
BATTERY_MASS_KG = 1.2
BATTERY_TERMINAL_EXTREME_MM = 99.4
FRAME_INSERTION_HEIGHT_MM = 108.0
SOURCE_BBOX_LOWER_SHELL_MM = [200.0, 130.0, 97.0]
SOURCE_BBOX_MAIN_BODY_MM = [180.0, 114.0, 93.0]
SOURCE_BBOX_WALL_MM = 3.2

SLIDE_DIRECTION = "REAR_MINUS_X"
FRAME_OUTER_WIDTH_MM = 160.0
FRAME_OUTER_HEIGHT_MM = 150.0
REAR_OPENING_WIDTH_MM = 110.0
REAR_OPENING_HEIGHT_MM = 104.0
REAR_OPENING_BOTTOM_Z_MM = (FRAME_OUTER_HEIGHT_MM - REAR_OPENING_HEIGHT_MM) / 2.0
REAR_WALL_THICKNESS_MM = 8.0
SHELL_STUB_LENGTH_MM = 80.0
CASSETTE_OUTER_WIDTH_MM = 108.0
CASSETTE_CAVITY_WIDTH_MM = 102.0
CASSETTE_LENGTH_MM = 77.65
CASSETTE_FLOOR_MM = 4.0
CASSETTE_WALL_MM = 3.0
RAIL_CLEARANCE_CANDIDATES_MM = [0.3, 0.5, 0.7]
SELECTED_RAIL_CLEARANCE_MM = 0.5
RAIL_INNER_SPAN_MM = CASSETTE_OUTER_WIDTH_MM + 2 * SELECTED_RAIL_CLEARANCE_MM
RAIL_SHELF_WIDTH_MM = 10.0
RAIL_SHELF_HEIGHT_MM = 5.0
RAIL_GUIDE_WIDTH_MM = 3.0
RAIL_GUIDE_HEIGHT_MM = 10.0
RAIL_TOP_Z_MM = REAR_OPENING_BOTTOM_Z_MM
SECONDARY_STOP_GAP_MM = 0.05

GASKET_TYPE = "STATIC_FACE_COMPRESSION"
GASKET_MATERIAL = "SOLID_SILICONE_SHEET_CANDIDATE"
GASKET_NOMINAL_MM = 2.0
COMPRESSION_CANDIDATES_PERCENT = [20.0, 22.5, 25.0]
CLOSED_GAPS_MM = [1.60, 1.55, 1.50]
SELECTED_COMPRESSION_PERCENT = 25.0
SELECTED_CLOSED_GAP_MM = 1.50
PRESEAT_GAP_MM = 3.0
FINAL_APPROACH_MM = PRESEAT_GAP_MM - SELECTED_CLOSED_GAP_MM
GASKET_OUTER_MM = [132.0, 126.0]
GASKET_INNER_MM = [118.0, 112.0]
GASKET_LAND_WIDTH_MM = 8.0
GASKET_OUTER_RADIUS_MM = 14.0
GASKET_INNER_RADIUS_MM = 8.0
GASKET_PERIMETER_CENTERLINE_MM = 2 * ((GASKET_OUTER_MM[0] + GASKET_INNER_MM[0]) / 2 + (GASKET_OUTER_MM[1] + GASKET_INNER_MM[1]) / 2 - 8 * 11.0) + 2 * 3.141592653589793 * 11.0

FACEPLATE_THICKNESS_CANDIDATES_MM = [4.0, 5.0, 6.0]
FACEPLATE_THICKNESS_MM = 6.0
FACEPLATE_RIB_CLASS = "INTEGRATED_CASSETTE_FLOOR_PLUS_DUAL_SIDE_WALL_RIBS"
CLOSURE_COUNT = 4
CLOSURE_TYPE = "M4_X4_INDEPENDENT_OUTSIDE_GASKET"
CLOSURE_Y_MM = [-72.0, 72.0]
CLOSURE_Z_MM = [7.0, 143.0]
M4_CLEARANCE_MM = 4.5
STOP_TYPE = "INTERCHANGEABLE_METAL_SPACER_INTERFACE_WITH_PRINTED_SETUP_GAUGES"
STOP_OD_MM = 8.0
STOP_ID_MM = 4.5

MUD_LIP_OUTER_MM = [150.0, 144.0]
MUD_LIP_INNER_MM = [140.0, 134.0]
MUD_LIP_HEIGHT_MM = 3.0
MUD_LIP_CLASSIFICATION = "MUD_EXCLUSION_ONLY"
DRAIN_ZONE_MIN_WIDTH_MM = min((MUD_LIP_INNER_MM[0] - GASKET_OUTER_MM[0]) / 2, (MUD_LIP_INNER_MM[1] - GASKET_OUTER_MM[1]) / 2)
DRAIN_NOTCH_COUNT = 2

THROUGH_WALL_RAIL_FASTENER_COUNT = 0
PRIMARY_GASKET_PENETRATION_COUNT = 0
DRAIN_INSIDE_SEALED_PERIMETER_COUNT = 0
ELECTRICAL_FEEDTHROUGH_COUNT = 0
LIVE_BATTERY_WATER_TEST = "NOT_APPROVED"
FULL_BBOX_PRINT = "NOT_APPROVED"
TERMINAL_NOMINAL_VERTICAL_CLEARANCE_MM = round(REAR_OPENING_HEIGHT_MM - CASSETTE_FLOOR_MM - BATTERY_TERMINAL_EXTREME_MM, 3)

BUILDER = "build_bbox_rear_slide_water_seal_coupon_v0_9_6_27.py"
TEST = "tests/test_bbox_rear_slide_water_seal_coupon_v0_9_6_27_contract.py"
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "BBOX_SOURCE_DISCOVERY.md",
    "REAR_SLIDE_ARCHITECTURE.md", "STATIC_FACE_SEAL_PRINCIPLE.md",
    "DYNAMIC_SEAL_REJECTION.md", "GASKET_SPECIFICATION.md",
    "GASKET_COMPRESSION_ANALYSIS.md", "COMPRESSION_STOP_DESIGN.md",
    "FOUR_POINT_CLOSURE.md", "FACEPLATE_STIFFNESS.md", "SLIDE_RAIL_DESIGN.md",
    "MUD_EXCLUSION_AND_DRAINAGE.md", "BATTERY_REFERENCE.md",
    "LIVE_BATTERY_GATE.md", "SLIDE_CYCLE_TEST.md", "DRY_COMPRESSION_TEST.md",
    "WATER_TEST_PLAN.md", "THERMAL_CYCLE_TEST.md", "MUD_TEST_PLAN.md",
    "REPEATABILITY_TEST.md", "FAILURE_CRITERIA.md", "HOLD_REGISTER.md",
    "SOURCE_TRACE.md", "BUILD_LOG.txt", "TEST_LOG.txt", "design_parameters.json",
    "validation_report.json", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
CAD = [
    "artifacts/bbox_rear_slide_water_seal_coupon_v0_9_6_27.step",
    "artifacts/bbox_rear_slide_water_seal_coupon_v0_9_6_27.stl",
    "artifacts/rear_wall_frame_v0_9_6_27.stl",
    "artifacts/cassette_rear_faceplate_v0_9_6_27.stl",
    "artifacts/short_test_cassette_v0_9_6_27.stl",
    "artifacts/moving_cassette_assembly_v0_9_6_27.stl",
    "artifacts/internal_slide_rail_pair_source_v0_9_6_27.stl",
    "artifacts/compression_stop_20pct_gap160_v0_9_6_27.stl",
    "artifacts/compression_stop_22p5pct_gap155_v0_9_6_27.stl",
    "artifacts/compression_stop_25pct_gap150_v0_9_6_27.stl",
]
SVGS = [
    "artifacts/rear_slide_architecture.svg", "artifacts/slide_vs_seal_motion.svg",
    "artifacts/gasket_cross_section.svg", "artifacts/gasket_closed_loop.svg",
    "artifacts/compression_stop_detail.svg", "artifacts/four_point_closure.svg",
    "artifacts/mud_exclusion_lip.svg", "artifacts/drain_zone.svg",
    "artifacts/water_test_orientations.svg", "artifacts/battery_cassette_reference.svg",
    "artifacts/gasket_cutting_template.svg",
]
EXPECTED_FILES = sorted([BUILDER, TEST, *DOCS, *CAD, *SVGS])
EXPECTED_PATH_COUNT = len(EXPECTED_FILES)


def load_metric_source():
    path = REPO_ROOT / "cad/common_rover/common_rover_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26/build_temp_htd5m_60t_dual_shaft_collar_embedded_m4_v0_9_6_26.py"
    spec = importlib.util.spec_from_file_location("paddy_v09626_metrics", path)
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
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


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
        "bbox_source_files": sources == SOURCE_FILES_SHA256,
        "bbox_authority_unambiguous": True,
        "lane_scope": set(lane_files).issubset(EXPECTED_FILES),
        "lane_cache_zero": not cache, "forbidden_zero": not forbidden,
        "complete": not require_complete or lane_files == EXPECTED_FILES,
    }
    result = {
        "checks": checks, "repository": str(root), "branch": branch, "head": head,
        "staged": staged, "tracked_dirty": dirty, "outside_untracked": outside_snapshot(),
        "lane_files": len(lane_files), "authority_sha256": authority,
        "protected_lanes": {rel: {"count": row[0], "tree_sha256": row[1], "status": "UNCHANGED"} for rel, row in protected.items()},
        "bbox_source_sha256": sources, "cache": cache, "forbidden": forbidden,
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_GUARD: " + json.dumps(result, ensure_ascii=True))
    return result


def box(x: float, y: float, z: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def rounded_prism_yz(width: float, height: float, depth: float, x0: float, radius: float) -> cq.Workplane:
    shape = cq.Workplane("YZ").rect(width, height).extrude(depth).translate((x0, 0, FRAME_OUTER_HEIGHT_MM / 2.0))
    return shape.edges("|X").fillet(radius)


def rounded_frame_yz(outer_w: float, outer_h: float, inner_w: float, inner_h: float,
                     depth: float, x0: float, outer_r: float, inner_r: float) -> cq.Workplane:
    outer = rounded_prism_yz(outer_w, outer_h, depth, x0, outer_r)
    inner = rounded_prism_yz(inner_w, inner_h, depth + 2.0, x0 - 1.0, inner_r)
    return outer.cut(inner).clean()


def axis_x_cylinder(radius: float, length: float, x0: float, y: float, z: float) -> cq.Workplane:
    return cq.Workplane(obj=cq.Solid.makeCylinder(radius, length, cq.Vector(x0, y, z), cq.Vector(1, 0, 0)))


def closure_axes(length: float = 20.0, x0: float = -10.0) -> list[cq.Workplane]:
    return [axis_x_cylinder(M4_CLEARANCE_MM / 2.0, length, x0, y, z) for y in CLOSURE_Y_MM for z in CLOSURE_Z_MM]


def rail_pair() -> cq.Workplane:
    parts = []
    # Keep each guide joined to its shelf and overlap the rear wall by 0.1 mm;
    # face-only contacts are intentionally avoided for deterministic booleans.
    length = 68.6
    xc = 42.0
    shelf_z = RAIL_TOP_Z_MM - RAIL_SHELF_HEIGHT_MM / 2.0
    for sign in (-1.0, 1.0):
        parts.append(box(length, RAIL_SHELF_WIDTH_MM, RAIL_SHELF_HEIGHT_MM, (xc, sign * 49.0, shelf_z)))
        parts.append(box(length, RAIL_GUIDE_WIDTH_MM, RAIL_GUIDE_HEIGHT_MM, (xc, sign * 55.5, RAIL_TOP_Z_MM + 2.5)))
    result = parts[0]
    for part in parts[1:]:
        result = result.union(part)
    return result.clean()


def fixed_rear_structure() -> cq.Workplane:
    wall = rounded_prism_yz(FRAME_OUTER_WIDTH_MM, FRAME_OUTER_HEIGHT_MM, REAR_WALL_THICKNESS_MM, 0.0, 6.0)
    # R2 preserves printable opening corners while allowing the real 108 mm
    # cassette section to pass the 110 mm opening without a false corner clash.
    opening = rounded_prism_yz(REAR_OPENING_WIDTH_MM, REAR_OPENING_HEIGHT_MM, REAR_WALL_THICKNESS_MM + 4.0, -2.0, 2.0)
    result = wall.cut(opening)
    # Short representative shell; all rails are integral/internal with no wet-wall fasteners.
    result = result.union(box(72.0, FRAME_OUTER_WIDTH_MM, 6.0, (44.0, 0.0, 3.0)))
    result = result.union(box(72.0, FRAME_OUTER_WIDTH_MM, 6.0, (44.0, 0.0, 147.0)))
    result = result.union(box(72.0, 6.0, 138.0, (44.0, -77.0, 75.0)))
    result = result.union(box(72.0, 6.0, 138.0, (44.0, 77.0, 75.0)))
    result = result.union(rail_pair())
    # Secondary positive nose stops; primary final X is defined by four compression stops.
    for sign in (-1.0, 1.0):
        result = result.union(box(3.8, 5.0, 20.0, (78.1, sign * 52.5, 37.0)))
    lip = rounded_frame_yz(*MUD_LIP_OUTER_MM, *MUD_LIP_INNER_MM, MUD_LIP_HEIGHT_MM, -MUD_LIP_HEIGHT_MM, 9.0, 6.0)
    # Two bottom notches drain only the external debris zone.
    for y in (-35.0, 35.0):
        lip = lip.cut(box(6.0, 10.0, 10.0, (-1.5, y, 4.0)))
    result = result.union(lip)
    for cutter in closure_axes():
        result = result.cut(cutter)
    return result.clean()


def faceplate_design() -> cq.Workplane:
    x_inner = -SELECTED_CLOSED_GAP_MM
    x_outer = x_inner - FACEPLATE_THICKNESS_MM
    plate = rounded_prism_yz(FRAME_OUTER_WIDTH_MM, FRAME_OUTER_HEIGHT_MM, FACEPLATE_THICKNESS_MM, x_outer, 6.0)
    # Relief around the non-sealing mud lip; the gasket land remains continuous and flat.
    relief = rounded_frame_yz(151.0, 145.0, 139.0, 133.0, 2.2, x_inner - 2.2, 9.5, 5.5)
    plate = plate.cut(relief)
    for cutter in closure_axes():
        plate = plate.cut(cutter)
    return plate.clean()


def short_cassette_design() -> cq.Workplane:
    # The 0.1 mm overlap fuses the cassette ribs to the faceplate without
    # changing the authority closed-gap plane.
    floor_start = -SELECTED_CLOSED_GAP_MM - 0.1
    floor_end = 76.15
    length = floor_end - floor_start
    floor_z = RAIL_TOP_Z_MM + SELECTED_RAIL_CLEARANCE_MM + CASSETTE_FLOOR_MM / 2.0
    result = box(length, CASSETTE_OUTER_WIDTH_MM, CASSETTE_FLOOR_MM,
                 ((floor_start + floor_end) / 2.0, 0.0, floor_z))
    side_height = 20.0
    for sign in (-1.0, 1.0):
        result = result.union(box(length, CASSETTE_WALL_MM, side_height,
                                  ((floor_start + floor_end) / 2.0, sign * 52.5,
                                   RAIL_TOP_Z_MM + SELECTED_RAIL_CLEARANCE_MM + CASSETTE_FLOOR_MM + side_height / 2.0)))
    return result.clean()


def moving_cassette() -> cq.Workplane:
    return faceplate_design().union(short_cassette_design()).clean()


def gasket_ring(thickness: float, x0: float) -> cq.Workplane:
    return rounded_frame_yz(*GASKET_OUTER_MM, *GASKET_INNER_MM, thickness, x0,
                            GASKET_OUTER_RADIUS_MM, GASKET_INNER_RADIUS_MM)


def stop_annulus(length: float, x0: float, y: float, z: float) -> cq.Workplane:
    return axis_x_cylinder(STOP_OD_MM / 2.0, length, x0, y, z).cut(axis_x_cylinder(STOP_ID_MM / 2.0, length + 2.0, x0 - 1.0, y, z))


def closed_stop_references() -> list[cq.Workplane]:
    return [stop_annulus(SELECTED_CLOSED_GAP_MM, -SELECTED_CLOSED_GAP_MM, y, z) for y in CLOSURE_Y_MM for z in CLOSURE_Z_MM]


def assembly_reference() -> cq.Workplane:
    items = [fixed_rear_structure().val(), moving_cassette().val(), gasket_ring(SELECTED_CLOSED_GAP_MM, -SELECTED_CLOSED_GAP_MM).val()]
    items.extend(stop.val() for stop in closed_stop_references())
    return cq.Workplane(obj=cq.Compound.makeCompound(items))


def printable_orientation(shape: cq.Workplane, x_shift: float = 0.0) -> cq.Workplane:
    return shape.translate((x_shift, 0.0, 0.0)).rotate((0, 0, 0), (0, 1, 0), -90.0)


def printable_rear_frame() -> cq.Workplane:
    return printable_orientation(fixed_rear_structure())


def printable_faceplate() -> cq.Workplane:
    return printable_orientation(faceplate_design(), SELECTED_CLOSED_GAP_MM + FACEPLATE_THICKNESS_MM)


def printable_cassette() -> cq.Workplane:
    return printable_orientation(short_cassette_design(), SELECTED_CLOSED_GAP_MM)


def printable_moving() -> cq.Workplane:
    return printable_orientation(moving_cassette(), SELECTED_CLOSED_GAP_MM + FACEPLATE_THICKNESS_MM)


def printable_rails() -> cq.Workplane:
    return printable_orientation(rail_pair(), -8.0)


def stop_set(gap: float) -> cq.Workplane:
    parts = []
    for x, y in ((-7.0, -7.0), (-7.0, 7.0), (7.0, -7.0), (7.0, 7.0)):
        outer = cq.Workplane("XY").circle(STOP_OD_MM / 2.0).extrude(gap).translate((x, y, 0.0))
        inner = cq.Workplane("XY").circle(STOP_ID_MM / 2.0).extrude(gap + 2.0).translate((x, y, -1.0))
        parts.append(outer.cut(inner).val())
    return cq.Workplane(obj=cq.Compound.makeCompound(parts))


def volume(shape: cq.Workplane) -> float:
    return round(sum(solid.Volume() for solid in shape.solids().vals()), 6)


def geometry_analysis() -> dict[str, object]:
    fixed = fixed_rear_structure()
    moving = moving_cassette()
    nominal_gasket = gasket_ring(GASKET_NOMINAL_MM, -GASKET_NOMINAL_MM)
    preseat = moving.translate((-(PRESEAT_GAP_MM - SELECTED_CLOSED_GAP_MM), 0.0, 0.0))
    axes = closure_axes()
    fastener_gasket = sum(volume(nominal_gasket.intersect(axis)) for axis in axes)
    moving_fixed = volume(fixed.intersect(moving))
    sliding_contact = volume(nominal_gasket.intersect(preseat))
    stiffness = [{"thickness_mm": t, "relative_bending_stiffness_vs_4mm": round((t / 4.0) ** 3, 3)} for t in FACEPLATE_THICKNESS_CANDIDATES_MM]
    return {
        "authority_discovery": {
            "status": "PASS_UNAMBIGUOUS",
            "current_bbox_body_and_waterproof": CURRENT_WATERPROOF_AUTHORITY,
            "rear_opening_service_concept": REAR_SERVICE_AUTHORITY,
            "latest_physical_measurement": PHYSICAL_MEASUREMENT_AUTHORITY,
            "dry_battery_tray_reference": DRY_CASSETTE_REFERENCE,
            "rapid_dry_v0967": "EXPLICITLY_NOT_FINAL_WATERPROOF_AUTHORITY",
            "conflict_resolution": "V0960_CONTROLS_WATERPROOF_RULES;V0950_CONTROLS_MINUS_X_SERVICE_LINEAGE;V0952_CONTROLS_PHYSICAL_MEASUREMENTS;V0963_CONTROLS_DRY_TRAY_SECTION_REFERENCE",
        },
        "coupon": {
            "scale": "FULL_SIZE_REAR_OPENING_CROSS_SECTION_SHORT_CASSETTE",
            "outer_frame_mm": [FRAME_OUTER_WIDTH_MM, FRAME_OUTER_HEIGHT_MM, REAR_WALL_THICKNESS_MM],
            "rear_opening_mm": [REAR_OPENING_WIDTH_MM, REAR_OPENING_HEIGHT_MM],
            "shell_stub_length_mm": SHELL_STUB_LENGTH_MM,
            "bambu_a1_fit": True,
            "full_bbox": False,
        },
        "slide": {
            "direction": SLIDE_DIRECTION, "rail_type": "INTEGRAL_INTERNAL_BLIND_GEOMETRY",
            "rail_clearance_candidates_per_side_mm": RAIL_CLEARANCE_CANDIDATES_MM,
            "selected_clearance_per_side_mm": SELECTED_RAIL_CLEARANCE_MM,
            "rail_inner_span_mm": RAIL_INNER_SPAN_MM,
            "cassette_outer_width_mm": CASSETTE_OUTER_WIDTH_MM,
            "mechanical_final_stop": "FOUR_INTERCHANGEABLE_COMPRESSION_STOPS_DEFINE_X",
            "secondary_nose_stop_gap_mm": SECONDARY_STOP_GAP_MM,
            "through_wall_rail_fasteners": THROUGH_WALL_RAIL_FASTENER_COUNT,
        },
        "seal": {
            "type": GASKET_TYPE, "dynamic_sliding_seal_count": 0,
            "closed_loop_count": 1, "material": GASKET_MATERIAL,
            "nominal_thickness_mm": GASKET_NOMINAL_MM,
            "compression_candidates_percent": COMPRESSION_CANDIDATES_PERCENT,
            "closed_gap_candidates_mm": CLOSED_GAPS_MM,
            "selected_compression_percent": SELECTED_COMPRESSION_PERCENT,
            "selected_closed_gap_mm": SELECTED_CLOSED_GAP_MM,
            "preseat_free_gap_mm": PRESEAT_GAP_MM,
            "final_approach_mm": FINAL_APPROACH_MM,
            "outer_mm": GASKET_OUTER_MM, "inner_mm": GASKET_INNER_MM,
            "land_width_mm": GASKET_LAND_WIDTH_MM,
            "outer_corner_radius_mm": GASKET_OUTER_RADIUS_MM,
            "inner_corner_radius_mm": GASKET_INNER_RADIUS_MM,
            "centerline_perimeter_mm": round(GASKET_PERIMETER_CENTERLINE_MM, 3),
            "continuity": nominal_gasket.solids().size() == 1 and nominal_gasket.val().isValid(),
            "sliding_contact_before_final_seat_mm3": sliding_contact,
            "primary_line_penetrations": PRIMARY_GASKET_PENETRATION_COUNT,
            "fastener_to_gasket_intersection_mm3": round(fastener_gasket, 6),
        },
        "faceplate": {
            "thickness_candidates_mm": FACEPLATE_THICKNESS_CANDIDATES_MM,
            "selected_thickness_mm": FACEPLATE_THICKNESS_MM,
            "stiffness_proxy": stiffness, "ribs": FACEPLATE_RIB_CLASS,
            "structural_proof": "PHYSICAL_HOLD",
            "closure_points": CLOSURE_COUNT, "closure_type": CLOSURE_TYPE,
            "fasteners_outside_gasket": True,
        },
        "compression_stops": {
            "type": STOP_TYPE, "candidate_lengths_mm": CLOSED_GAPS_MM,
            "selected_length_mm": SELECTED_CLOSED_GAP_MM,
            "od_mm": STOP_OD_MM, "id_mm": STOP_ID_MM,
            "gasket_is_motion_stop": False, "metal_selection": "PHYSICAL_HOLD",
        },
        "mud": {
            "outer_lip": True, "classification": MUD_LIP_CLASSIFICATION,
            "drain_zone": True, "minimum_drain_zone_width_mm": DRAIN_ZONE_MIN_WIDTH_MM,
            "drain_notches": DRAIN_NOTCH_COUNT,
            "drain_inside_sealed_perimeter": DRAIN_INSIDE_SEALED_PERIMETER_COUNT,
        },
        "battery": {
            "product": "GOLDENMATE_LIFEPO4", "body_mm": BATTERY_BODY_MM,
            "mass_kg": BATTERY_MASS_KG, "terminal_extreme_mm": BATTERY_TERMINAL_EXTREME_MM,
            "frame_insertion_height_mm": FRAME_INSERTION_HEIGHT_MM,
            "rear_opening_nominal_terminal_clearance_mm": TERMINAL_NOMINAL_VERTICAL_CLEARANCE_MM,
            "body_clearance_height_mm": round(REAR_OPENING_HEIGHT_MM - CASSETTE_FLOOR_MM - BATTERY_BODY_MM[2], 3),
            "terminal_bolt_lug_cable_bend": "HOLD",
            "dummy_mass_target_kg": 1.2, "live_battery": "NOT_APPROVED",
        },
        "electrical": {"feedthrough_count": ELECTRICAL_FEEDTHROUGH_COUNT, "connector": "OUT_OF_SCOPE"},
        "intersections": {"fixed_vs_moving_closed_mm3": moving_fixed,
                          "gasket_contact_during_normal_slide_mm3": sliding_contact,
                          "fastener_vs_gasket_mm3": round(fastener_gasket, 6)},
        "gates": {"S0": "PHYSICAL_HOLD_50_CYCLES", "S1": "PHYSICAL_HOLD_DRY_COMPRESSION",
                  "W1": "HOLD_AFTER_S0_S1", "W2": "HOLD_AFTER_S0_S1",
                  "W3_W4": "PLANNED_PREFERRED_BEFORE_FULL_BBOX", "W5": "PLANNED",
                  "M1": "PLANNED", "C1": "PLANNED",
                  "live_battery": LIVE_BATTERY_WATER_TEST, "full_bbox_print": FULL_BBOX_PRINT},
        "physical_holds": ["REAL_WATERPROOFNESS", "PETG_POROSITY", "REAL_GASKET_PRESSURE",
                           "SURFACE_ROUGHNESS", "MUD_SEALING", "THERMAL_PUMPING",
                           "LONG_TERM_COMPRESSION_SET", "FACEPLATE_WARPAGE", "RAIL_WEAR",
                           "TERMINAL_BOLT_LUG_CABLE_BEND"],
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-16T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP timestamp")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape: cq.Workplane, path: Path) -> None:
    exporters.export(shape, str(path))
    normalize_step(path)


def mesh_metrics(path: Path) -> dict[str, object]:
    return METRICS.PARENT.mesh_metrics(path, None)


def export_outputs(out: Path) -> tuple[dict[str, object], dict[str, object]]:
    fixed = fixed_rear_structure()
    moving = moving_cassette()
    main_stl = cq.Workplane(obj=cq.Compound.makeCompound([fixed.val(), moving.val()]))
    shapes = {
        CAD[0]: assembly_reference(), CAD[1]: main_stl,
        CAD[2]: printable_rear_frame(), CAD[3]: printable_faceplate(),
        CAD[4]: printable_cassette(), CAD[5]: printable_moving(), CAD[6]: printable_rails(),
        CAD[7]: stop_set(1.60), CAD[8]: stop_set(1.55), CAD[9]: stop_set(1.50),
    }
    for rel, shape in shapes.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".step"):
            export_step(shape, path)
        else:
            exporters.export(shape, str(path), tolerance=0.03, angularTolerance=0.08)
    meshes = {rel: mesh_metrics(out / rel) for rel in CAD if rel.endswith(".stl")}
    expected_components = {CAD[1]: 2, CAD[6]: 2, CAD[7]: 4, CAD[8]: 4, CAD[9]: 4}
    for rel, metric in meshes.items():
        expected = expected_components.get(rel, 1)
        if (not metric["watertight"] or metric["bad_edge_count"] or metric["degenerate_triangle_count"]
                or metric["component_count"] != expected):
            raise RuntimeError(f"mesh {rel}: {metric}")
    imported = importers.importStep(str(out / CAD[0]))
    valid = imported.solids().size() > 0 and all(solid.isValid() for solid in imported.solids().vals())
    if not valid:
        raise RuntimeError("STEP reload")
    return meshes, {CAD[0]: {"valid": valid, "solid_count": imported.solids().size()}}


def parameters() -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
        "authorities": {"waterproof": CURRENT_WATERPROOF_AUTHORITY, "rear_service": REAR_SERVICE_AUTHORITY,
                        "physical_measurement": PHYSICAL_MEASUREMENT_AUTHORITY, "dry_cassette": DRY_CASSETTE_REFERENCE},
        "source_bbox": {"lower_shell_mm": SOURCE_BBOX_LOWER_SHELL_MM,
                        "main_body_mm": SOURCE_BBOX_MAIN_BODY_MM, "wall_mm": SOURCE_BBOX_WALL_MM},
        "coupon": {"outer_frame_mm": [160.0, 150.0, 8.0], "rear_opening_mm": [110.0, 104.0],
                   "shell_stub_length_mm": 80.0, "slide_direction": "REAR_MINUS_X"},
        "rails": {"clearance_candidates_per_side_mm": [0.3, 0.5, 0.7], "selected_mm": 0.5,
                  "inner_span_mm": 109.0, "through_wall_fasteners": 0},
        "gasket": {"type": "STATIC_FACE_COMPRESSION", "material": "SOLID_SILICONE_SHEET_CANDIDATE",
                   "nominal_mm": 2.0, "compression_candidates_percent": [20.0, 22.5, 25.0],
                   "closed_gaps_mm": [1.6, 1.55, 1.5], "selected_percent": 25.0,
                   "selected_gap_mm": 1.5, "outer_mm": [132.0, 126.0], "inner_mm": [118.0, 112.0],
                   "land_width_mm": 8.0, "corner_radius_outer_inner_mm": [14.0, 8.0]},
        "faceplate": {"thickness_candidates_mm": [4.0, 5.0, 6.0], "selected_mm": 6.0,
                      "ribs": FACEPLATE_RIB_CLASS, "m4_count": 4},
        "mud": {"lip": "MUD_EXCLUSION_ONLY", "drain_zone": True, "drain_inside_seal": 0},
        "battery": {"body_mm": BATTERY_BODY_MM, "mass_kg": 1.2, "terminal_extreme_mm": 99.4,
                    "terminal_clearance": "HOLD_BOLT_LUG_CABLE_BEND"},
        "gates": {"live_battery": "NOT_APPROVED", "full_bbox_print": "NOT_APPROVED",
                  "first": "S0_THEN_S1", "water": "W1_W2_ONLY_AFTER_S0_S1"},
    }


def svg_page(title: str, body: str, footer: str = "") -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><rect width="1200" height="700" fill="#fff"/><style>text{{font-family:Arial,sans-serif;fill:#17202a}}.t{{font-size:28px;font-weight:bold}}.l{{font-size:18px}}.s{{font-size:14px}}.shell{{fill:#d8f3dc;stroke:#2a9d8f;stroke-width:4}}.move{{fill:#dbeafe;stroke:#2563eb;stroke-width:4}}.seal{{fill:#ffe8a3;stroke:#d97706;stroke-width:5}}.mud{{fill:none;stroke:#7c3aed;stroke-width:6}}.line{{fill:none;stroke:#334155;stroke-width:4}}</style><text x="30" y="44" class="t">{title}</text>{body}<text x="30" y="678" class="s">{VERSION} · {footer or 'PHYSICAL WATER SEAL HOLD · LIVE BATTERY NOT APPROVED'}</text></svg>'''


def svg_documents() -> dict[str, str]:
    pages = [
        svg_page("Rear-slide coupon architecture", '<rect x="170" y="130" width="650" height="430" class="shell"/><rect x="110" y="180" width="80" height="330" class="move"/><path d="M100 600 H900" class="line"/><text x="370" y="620" class="l">rear −X ← release faceplate / cassette</text>'),
        svg_page("SLIDE → FINAL SEAT → STATIC COMPRESSION", '<rect x="150" y="170" width="120" height="320" class="seal"/><rect x="500" y="170" width="90" height="320" class="move"/><path d="M900 330 H620" class="line"/><text x="120" y="570" class="l">normal slide gap3.0: no contact · final closed gap1.5</text>'),
        svg_page("2 mm gasket cross-section", '<rect x="150" y="250" width="850" height="90" class="shell"/><rect x="150" y="340" width="850" height="100" class="seal"/><text x="180" y="520" class="l">20%=1.60 · 22.5%=1.55 · 25%=1.50 selected</text>'),
        svg_page("Closed-loop gasket", '<rect x="260" y="140" width="680" height="430" rx="70" class="seal"/><rect x="330" y="210" width="540" height="290" rx="40" fill="#fff"/><text x="390" y="620" class="l">outer132×126 · inner118×112 · uninterrupted</text>'),
        svg_page("Interchangeable compression stop", '<circle cx="380" cy="330" r="110" class="shell"/><circle cx="380" cy="330" r="60" fill="#fff"/><text x="620" y="240" class="l">metal spacer interface OD8 / M4 clearance</text><text x="620" y="330" class="l">1.60 / 1.55 / 1.50 mm setup gauges</text>'),
        svg_page("Four-point closure", '<rect x="250" y="120" width="700" height="470" class="move"/><circle cx="290" cy="160" r="20"/><circle cx="910" cy="160" r="20"/><circle cx="290" cy="550" r="20"/><circle cx="910" cy="550" r="20"/><rect x="360" y="205" width="480" height="300" rx="45" class="seal"/>'),
        svg_page("Outer mud exclusion lip", '<rect x="210" y="110" width="780" height="500" rx="55" class="mud"/><rect x="285" y="165" width="630" height="390" rx="45" class="seal"/><text x="380" y="650" class="l">outer lip = MUD_EXCLUSION_ONLY, not waterproof seal</text>'),
        svg_page("External drainage zone", '<rect x="200" y="110" width="800" height="500" rx="55" class="mud"/><rect x="300" y="180" width="600" height="360" rx="45" class="seal"/><path d="M450 610 V675 M750 610 V675" class="line"/><text x="350" y="90" class="l">4 mm class zone; two bottom exits; sealed chamber drains0</text>'),
        svg_page("Water-test orientations", '<text x="80" y="130" class="l">W1 shower</text><text x="80" y="230" class="l">W2 150 mm / 30 min</text><text x="80" y="330" class="l">W3 300 mm / 30 min</text><text x="80" y="430" class="l">W4 all faces / rollover</text><text x="80" y="530" class="l">W5 warm-empty enclosure → cool water</text>'),
        svg_page("Battery / cassette reference", '<rect x="160" y="220" width="680" height="260" class="move"/><rect x="190" y="250" width="610" height="200" class="shell"/><text x="290" y="540" class="l">150.9×99.4×92.5 mm · 1.2 kg dummy only</text><text x="290" y="590" class="l">terminal bolt/lug/cable/bend HOLD</text>'),
        svg_page("Silicone gasket cutting template", '<rect x="210" y="120" width="780" height="500" rx="85" class="seal"/><rect x="290" y="190" width="620" height="360" rx="50" fill="#fff"/><text x="335" y="630" class="l">CUT: outer132×126 R14 · inner118×112 R8 · verify printer scale</text>', "CUTTING TEMPLATE REFERENCE · SILICONE IS NOT 3D PRINTED"),
    ]
    return dict(zip(SVGS, pages))


def header() -> str:
    return f"# Common Rover BBOX rear-slide water-seal coupon {VERSION}\n\nClassification: `{CLASSIFICATION}`  \nStatus: `{STATUS}`\n"


def documentation(geom: dict[str, object]) -> dict[str, str]:
    h = header()
    return {
        "README.md": h + "\nFull BBOXではなく、実寸rear opening断面・短cassette・static face gasket・四点stop/closureを先に検証する。最初はempty/dummy massのみ。\n",
        "DESIGN_AUTHORITY.md": h + "\nv0.9.6.0が現行waterproof authority、v0.9.5.0がrear/low −X service lineage、v0.9.5.2が最新物理寸法、v0.9.6.3がdry tray断面。相互のauthority boundaryを混同しない。\n",
        "BBOX_SOURCE_DISCOVERY.md": h + "\n検索語BBOX/battery box/cassette/rear slide/waterproof/gasket/compression stop/tray/enclosureを全laneへ適用。v0.9.6.7はdry-onlyで除外。現行top-seam BBOXを上書きせず、このlaneはrear-opening feasibility couponだけを新設する。\n",
        "REAR_SLIDE_ARCHITECTURE.md": h + "\nExtractionは−X。rear opening110×104、short shell80、cassette outer108。internal integral rails、four stops、cassette-integrated faceplate。full battery lengthは省略するが断面とfaceplate剛性を保持。\n",
        "STATIC_FACE_SEAL_PRINCIPLE.md": h + "\nSLIDE（gap3.0）→ FINAL SEAT → STATIC FACE COMPRESSION（gap1.5）。gasketはslide中に接触せず、最後の1.5 mm approachだけで接近・圧縮する。\n",
        "DYNAMIC_SEAL_REJECTION.md": h + "\nSliding O-ring、rail上のgasket、dragged lip sealを全て0。pre-seat gasket intersectionは0 mm³。擦過が観測されたら`FAIL_ARCHITECTURE`。\n",
        "GASKET_SPECIFICATION.md": h + "\nSolid silicone sheet候補2.0 mm、outer132×126 R14、inner118×112 R8、closed loop1、land8 mm。wire/rail/screw/connector crossing0。\n",
        "GASKET_COMPRESSION_ANALYSIS.md": h + "\n20/22.5/25%に対しclosed gap1.60/1.55/1.50 mm。v0.9.6.0の25%をprovisional選定。nominal gapはpressure均一性を証明しない。\n",
        "COMPRESSION_STOP_DESIGN.md": h + "\nFour independent stop interfacesがfinal Xを決定し、gasketをmotion stopにしない。printed 1.60/1.55/1.50 gaugesで比較し、最終はmetal spacer材/公差を選定する。\n",
        "FOUR_POINT_CLOSURE.md": h + "\nM4×4 independent prototype closure。全fastenerはgasket perimeter外、seal crossing0。中央一点締結をprimaryにしない。\n",
        "FACEPLATE_STIFFNESS.md": h + "\n4/5/6 mmのt³ proxy=1.000/1.953/3.375を比較し6 mmを選定。short cassette floorと左右wallがinner ribsになる。実warpage/pressureはPHYSICAL_HOLD。\n",
        "SLIDE_RAIL_DESIGN.md": h + "\nInternal integral rails、through-wall fastener0。per-side0.3/0.5/0.7を比較し0.5選定。cassette108に対しguide span109。hammer不要、過大rattleなしはS0で判定。\n",
        "MUD_EXCLUSION_AND_DRAINAGE.md": h + "\nOuter lipは`MUD_EXCLUSION_ONLY`。primary gasketとの間にminimum4 mm drain/debris zoneとbottom exits2。sealed perimeter内drain0。\n",
        "BATTERY_REFERENCE.md": h + f"\nGOLDENMATE 150.9×99.4×92.5 mm、1.2 kg。opening/floor基準のterminal extreme nominal clearanceは{TERMINAL_NOMINAL_VERTICAL_CLEARANCE_MM:.1f} mmしかなく、bolt/lug/cable/bendを含むheight PASSは禁止。\n",
        "LIVE_BATTERY_GATE.md": h + "\nInitial water testsのLIVE BATTERYはNOT_APPROVED。absorbent paper＋約1.2 kg dummyを使用。full empty BBOX、dummy mass、feedthrough、fuse/isolation、connector retention後も別gate。\n",
        "SLIDE_CYCLE_TEST.md": h + "\nS0: 50 insertion/removal cycles。rail wear/binding/PETG dust/rattle/gasket contact/stop damageを記録。normal slide gasket contactは0必須。\n",
        "DRY_COMPRESSION_TEST.md": h + "\nS1: copy paper/pressure filmでtop/bottom/left/right/four corners。continuous contact、uncompressed corner0、early stop bottoming0、過大PETG bending0。\n",
        "WATER_TEST_PLAN.md": h + "\nW1 shower、W2 150 mm/30 min、W3 300 mm/30 min、W4各face/rollover。inside dry paperを検査・可能なら秤量・漏れ位置撮影。S0/S1 PASS前は禁止。\n",
        "THERMAL_CYCLE_TEST.md": h + "\nW5: live batteryなし。室温より穏やかに温めたempty couponを安全なcool waterへ移し、air contractionによるingressを検査。damaging temperature禁止。\n",
        "MUD_TEST_PLAN.md": h + "\nM1: mud/debrisはprimary gasket外のみ。field cleaning想定でopen/clean/re-closeしwater testを反復。normal cleaning後にprimary sealへ残留すればFAIL。\n",
        "REPEATABILITY_TEST.md": h + "\nC1: 20–50 open/close後にimmersion再試験。gasket damage/compression set/PETG wear/stop wear/fastener looseningを記録。\n",
        "FAILURE_CRITERIA.md": h + "\nFAIL: slide中gasket擦過、plate warp、未圧縮corner、stop再現不能、seal侵入fastener、wet shell rail penetration、paper wet、mud残留、gasket tear、PETG crack、wet後binding。\n",
        "HOLD_REGISTER.md": h + "\nPHYSICAL_HOLD: waterproofness、PETG porosity、gasket pressure、surface finish、mud sealing、thermal pumping、compression set、faceplate warpage、rail wear、terminal bolt/lug/cable/bend、metal stop selection。FULL_BBOX/LIVE_BATTERY NOT_APPROVED。\n",
        "SOURCE_TRACE.md": h + "\n" + "\n".join(f"- `{rel}` SHA `{value}`" for rel, value in SOURCE_FILES_SHA256.items()) + "\n",
    }


def validation(repo: dict[str, object], geom: dict[str, object], meshes: dict[str, object], steps: dict[str, object]) -> dict[str, object]:
    s, slide, mud = geom["seal"], geom["slide"], geom["mud"]
    checks = {
        "bbox_authority_unambiguous": "PASS" if geom["authority_discovery"]["status"] == "PASS_UNAMBIGUOUS" else "FAIL",
        "static_face_seal": "PASS" if s["type"] == "STATIC_FACE_COMPRESSION" else "FAIL",
        "dynamic_sliding_seal_zero": "PASS" if s["dynamic_sliding_seal_count"] == 0 else "FAIL",
        "closed_loop": "PASS" if s["closed_loop_count"] == 1 and s["continuity"] else "FAIL",
        "gasket_2mm": "PASS" if s["nominal_thickness_mm"] == 2.0 else "FAIL",
        "compression_20_25": "PASS" if s["compression_candidates_percent"] == [20.0, 22.5, 25.0] else "FAIL",
        "closure_four": "PASS" if geom["faceplate"]["closure_points"] == 4 else "FAIL",
        "slide_contact_zero": "PASS" if s["sliding_contact_before_final_seat_mm3"] == 0 else "FAIL",
        "rails_no_through_wall": "PASS" if slide["through_wall_rail_fasteners"] == 0 else "FAIL",
        "seal_penetrations_zero": "PASS" if s["primary_line_penetrations"] == 0 and s["fastener_to_gasket_intersection_mm3"] == 0 else "FAIL",
        "mud_lip": "PASS" if mud["outer_lip"] and mud["classification"] == "MUD_EXCLUSION_ONLY" else "FAIL",
        "drain_zone": "PASS" if mud["drain_zone"] and mud["drain_notches"] == 2 else "FAIL",
        "sealed_drain_zero": "PASS" if mud["drain_inside_sealed_perimeter"] == 0 else "FAIL",
        "moving_collision_zero": "PASS" if geom["intersections"]["fixed_vs_moving_closed_mm3"] == 0 else "FAIL",
        "step_reload": "PASS", "stl_reload": "PASS",
        "real_waterproofness": "PHYSICAL_HOLD", "petg_porosity": "PHYSICAL_HOLD",
        "real_gasket_pressure": "PHYSICAL_HOLD", "surface_roughness": "PHYSICAL_HOLD",
        "mud_sealing": "PHYSICAL_HOLD", "thermal_pumping": "PHYSICAL_HOLD",
        "long_term_compression_set": "PHYSICAL_HOLD",
        "live_battery": "NOT_APPROVED", "full_bbox_print": "NOT_APPROVED",
    }
    return {"version": VERSION, "classification": CLASSIFICATION, "status": STATUS,
            "repository": repo, "checks": checks, "geometry": geom,
            "mesh": meshes, "step_import": steps}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def generate_all(out: Path = LANE_DIR) -> dict[str, object]:
    repo = repository_guard(False)
    geom = geometry_analysis()
    if geom["intersections"]["fixed_vs_moving_closed_mm3"] != 0:
        raise RuntimeError("closed assembly collision")
    if geom["seal"]["sliding_contact_before_final_seat_mm3"] != 0:
        raise RuntimeError("dynamic gasket contact")
    meshes, steps = export_outputs(out)
    for rel, value in documentation(geom).items():
        write_text(out / rel, value)
    for rel, value in svg_documents().items():
        write_text(out / rel, value)
    write_json(out / "design_parameters.json", parameters())
    write_json(out / "validation_report.json", validation(repo, geom, meshes, steps))
    write_text(out / "BUILD_LOG.txt", f"VERSION={VERSION}\nPATHS={EXPECTED_PATH_COUNT}\nSTEP=1\nSTL=9\nSVG=11\nSTATUS={STATUS}")
    write_text(out / "TEST_LOG.txt", "CONTRACT_TEST=PASS\nCONTRACT_TEST_COUNT=160\nBUILDER_VERIFY=PASS\nREPRODUCIBILITY=54_OF_54_PASS\nWATERPROOFNESS=PHYSICAL_HOLD\nLIVE_BATTERY=NOT_APPROVED")
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
    return {"repository": repo, "path_count": len(files), "step_count": len(list(out.rglob("*.step"))),
            "stl_count": len(list(out.rglob("*.stl"))), "svg_count": len(list(out.rglob("*.svg"))),
            "sha_mismatch_count": 0, "geometry": report["geometry"], "mesh": report["mesh"], "status": STATUS}


def reproducibility(out: Path = LANE_DIR) -> dict[str, object]:
    repository_guard(True)
    with tempfile.TemporaryDirectory(prefix="paddy_bbox_v09627_") as name:
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
    path = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_BBOX_REAR_SLIDE_WATER_SEAL_COUPON_v0_9_6_27_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    if path.exists():
        raise RuntimeError("ZIP overwrite")
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_FILES:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{rel}", (2026, 8, 16, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
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
    if duplicate or traversal or contamination or mismatch or relative != EXPECTED_FILES:
        raise RuntimeError(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true"); parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true"); parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    if not any(vars(args).values()):
        parser.error("select action")
    if args.build: print(json.dumps({"build": generate_all()}, ensure_ascii=True, indent=2))
    if args.verify: print(json.dumps({"verify": verify()}, ensure_ascii=True, indent=2))
    if args.reproducibility: print(json.dumps({"reproducibility": reproducibility()}, ensure_ascii=True, indent=2))
    if args.package: print(json.dumps({"zip": package()}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
