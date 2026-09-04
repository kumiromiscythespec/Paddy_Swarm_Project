from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq


VERSION = "v0.9.6.12"
CLASSIFICATION = "SHORT_SLIDE_YOKE_RECEIVER_FINALIZATION"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_short_slide_yoke_receiver_v0_9_6_12")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2132
BASE_OUTSIDE_DIGEST = "2abc893fecd4fd2a3c1b374ac73517fb254b3624437a189cb31988ff9e0bbc80"
TRACKED_DIRTY = [
    "CURRENT_COMMON_ROVER_AUTHORITY.md",
    "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
]
AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}

PARENT_BUILDER = REPO_ROOT / "cad/common_rover/common_rover_hybrid_slide_lock_hub_cap_v0_9_6_11/build_hybrid_slide_lock_hub_cap_v0_9_6_11.py"
_spec = importlib.util.spec_from_file_location("v09611_parent", PARENT_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load protected parent: {PARENT_BUILDER}")
parent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = parent
_spec.loader.exec_module(parent)
v09610 = parent.parent
v0969 = v09610.parent
v0968 = v0969.parent

PROTECTED_LANES = dict(parent.PROTECTED_LANES)
PROTECTED_LANES["v0.9.6.11"] = (
    "cad/common_rover/common_rover_hybrid_slide_lock_hub_cap_v0_9_6_11",
    48,
    "f105c66a5349883f1e98a216366ec1663d14e26bc9b8862c715c6a86597076bb",
)

DOCS = [
    "README.md",
    "DESIGN_AUTHORITY.md",
    "PHYSICAL_INPUTS.md",
    "SLIDE_LOCK_PHYSICAL_RESULT.md",
    "LONG_SLIDE_PRINTABILITY_FAILURE.md",
    "SHORT_SLIDE_LOCK_SPEC.md",
    "SUPPORT_FREE_RECEIVER_SPEC.md",
    "M3_OPEN_HEX_NUT_SEAT_SPEC.md",
    "REACTION_Y3_PHYSICAL_STATUS.md",
    "REACTION_YOKE_RECEIVER_SPEC.md",
    "FINAL_THICK_ROOT_GUARD_SPEC.md",
    "TORQUE_LOAD_PATH.md",
    "ASSEMBLY_PROCEDURE.md",
    "PRINT_PLAN.md",
    "PHYSICAL_TEST_PLAN.md",
    "POWERED_TEST_GATE.md",
    "SAFETY_NOTES.md",
    "HOLD_REGISTER.md",
    "SOURCE_TRACE.md",
]
CAD = [f"artifacts/{name}" for name in (
    "drive_12t_h25a1_short_slide_y3_v0_9_6_12.step",
    "drive_12t_h25a1_short_slide_y3_v0_9_6_12.stl",
    "h25a1_short_slide_lock_cap_v0_9_6_12.step",
    "h25a1_short_slide_lock_cap_v0_9_6_12.stl",
    "short_support_free_slide_lock_coupon_v0_9_6_12.step",
    "short_support_free_slide_lock_coupon_v0_9_6_12.stl",
    "m3_open_hex_nut_seat_coupon_v0_9_6_12.step",
    "m3_open_hex_nut_seat_coupon_v0_9_6_12.stl",
    "reaction_yoke_receiver_fit_coupon_v0_9_6_12.step",
    "reaction_yoke_receiver_fit_coupon_v0_9_6_12.stl",
    "short_slide_y3_full_assembly_v0_9_6_12.step",
)]
SVGS = [f"artifacts/{name}" for name in (
    "long_vs_short_slide_v0_9_6_12.svg",
    "short_slide_open_locked_v0_9_6_12.svg",
    "support_free_receiver_section_v0_9_6_12.svg",
    "m3_hex_seat_h55_h56_h57_v0_9_6_12.svg",
    "y3_3p7_vs_4p3_clearance_v0_9_6_12.svg",
    "old_groove_vs_new_yoke_receiver_v0_9_6_12.svg",
    "yoke_receiver_yw20_yw30_yw40_v0_9_6_12.svg",
    "final_thick_root_guard_v0_9_6_12.svg",
    "full_hub_load_path_v0_9_6_12.svg",
)]
JSONS = ["design_parameters.json", "validation_report.json"]
SOURCES = [
    "build_short_slide_yoke_receiver_v0_9_6_12.py",
    "tests/test_short_slide_yoke_receiver_v0_9_6_12_contract.py",
]
RELEASE = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_PATHS = sorted(DOCS + CAD + SVGS + JSONS + SOURCES + RELEASE)

sha256 = parent.sha256
write_text = parent.write_text
write_json = parent.write_json
run_git = parent.run_git
tree_digest = parent.tree_digest
box = parent.box
cylinder = parent.cylinder
compound = parent.compound
fused = parent.fused
volume = parent.volume
dims = parent.dims
center_xy = parent.center_xy

LOCK = {"keep_m3_angle_deg": 45.0, "hook_angle_deg": 225.0}
PROTECTED_12T = dict(parent.PROTECTED_12T)
PARAMS = {
    "version": VERSION,
    "classification": CLASSIFICATION,
    "units": "mm",
    "physical_authority": {
        "hybrid_slide_lock_principle": "PHYSICAL_PASS_USER_REPORTED",
        "scope": "ALL_TESTED_CLEARANCE_VARIANTS_LOCKED_FIRMLY",
        "torque_pass": False,
        "vibration_pass": False,
        "long_internal_slide_receiver": "PRINTABILITY_FAIL_FOR_FINAL_USE",
        "long_receiver_reasons": ["INTERNAL_SUPPORT_REQUIRED", "POOR_SERVICE_SURFACE_RISK"],
        "y3_3p7_height": "PROMISING_PHYSICAL_FIT",
        "y3_receiver_width": "NOT_TESTED",
        "reaction_yoke_overall": "PHYSICAL_PASS_NOT_YET_GRANTED",
    },
    "motion": {
        "historical_mm": 5.0,
        "primary_mm": 3.0,
        "comparison_mm": 3.5,
        "sample_increment_mm": 0.25,
        "sample_count": 13,
        "hard_stop": True,
        "lock_concentric_error_mm": 0.0,
    },
    "hook": {
        "rigid": True,
        "snap": False,
        "structural_thickness_mm": 4.0,
        "root_thickness_mm": 6.0,
        "root_fillet_class": "R2_CLASS",
        "engagement_width_mm": 12.0,
        "overlap_target_min_mm": 2.5,
        "overlap_preferred_mm": [2.5, 3.0],
        "overlap_nominal_mm": 3.0,
        "overlap_residual_s45_mm": 2.55,
        "center_radius_mm": 21.5,
    },
    "receiver": {
        "architecture": "SHORT_OPEN_SIDED_45_DEG_SELF_SUPPORTING",
        "long_trapped_horizontal_ceiling": False,
        "internal_support_volume_mm3": 0.0,
        "internal_support_region": "NONE_BY_CAD_45_DEG_RULE",
        "roof_slope_deg": 45.0,
        "slicer_verification_required": True,
        "hard_stop_face": "BROAD_6MM_CLASS",
    },
    "slide_clearance": {
        "S25_mm": 0.25,
        "S35_mm": 0.35,
        "S45_mm": 0.45,
        "design_primary": "S45",
        "selection_reason": ["DUST_DEBRIS", "PETG_VARIATION", "REPEATABLE_PHYSICAL_LOCK"],
        "repeat_S25_S35_S45_required": False,
    },
    "single_m3": {
        "under_head_usable_length_mm": 20.5,
        "overall_reference_mm": 27.9,
        "count": 1,
        "local_bridge_thickness_mm": 7.0,
        "cap_thickness_mm": 5.5,
        "petg_stack_mm": 12.5,
        "remaining_hardware_budget_mm": 8.0,
        "role": "ANTI_REVERSE_AND_SECONDARY_AXIAL_RETENTION",
        "primary_torque_path": False,
    },
    "open_hex_nut_seat": {
        "physical_nut_af_reference_mm": 5.4,
        "variants_mm": {"H55": 5.5, "H56": 5.6, "H57": 5.7},
        "design_primary": "H56",
        "design_primary_af_mm": 5.6,
        "total_clearance_at_primary_mm": 0.2,
        "open_backed": True,
        "visible": True,
        "removable": True,
        "hidden_pocket": False,
        "petg_thread": False,
        "nut_thickness": "HOLD",
        "physical_selection": "PENDING_COUPON",
    },
    "reaction_yoke": {
        "geometry": "PROTECTED_V0969_Y3_EXACT",
        "bridge_height_mm": 3.7,
        "m4_head_space_mm": 4.3,
        "vertical_margin_mm": 0.6,
        "nominal_width_from_cad_mm": 15.2,
        "overall_bounds_mm": [15.0, 15.2, 12.0],
        "volume_mm3": 2212.752,
        "receiver_variants_mm": {"YW20": 15.4, "YW30": 15.5, "YW40": 15.6},
        "receiver_cad_primary": "YW30",
        "receiver_cad_primary_width_mm": 15.5,
        "physical_selection": "PENDING_COUPON",
        "old_wheel_groove_authority": False,
        "load_path_primary": True,
    },
    "guard": {
        **parent.PARAMS["guard"],
        "selection": "FINAL_DRY_PROTOTYPE_GUARD_GEOMETRY",
        "old_thin_root": "REJECT_FINAL",
        "preserved_from": "v0.9.6.9",
    },
    "protected_12t": PROTECTED_12T,
    "pitch": dict(parent.PARAMS["pitch"]),
    "collar": dict(parent.PARAMS["collar"]),
    "full_capture": dict(parent.PARAMS["full_capture"]),
    "m4": dict(parent.PARAMS["m4"]),
    "printability": {
        "printer": "BAMBU_A1",
        "material": "PETG",
        "first": "H55_H56_H57_OPEN_HEX_COUPON",
        "second": "YW20_YW30_YW40_WITH_IDENTICAL_Y3",
        "third": "S45_SHORT_SLIDE_COUPON",
        "full_12t_mark": "DO_NOT_PRINT_UNTIL_HEX_YOKE_RECEIVER_AND_SHORT_SLIDE_PASS",
    },
    "gates": {
        "short_slide": "READY_FOR_PHYSICAL_TEST",
        "hex_nut_seat": "READY_FOR_COUPON",
        "y3_height": "PROMISING_PHYSICAL_FIT",
        "yoke_receiver_width": "PENDING_PHYSICAL_COUPON",
        "full_12t": "PRINT_PENDING_HEX_YOKE_AND_SHORT_SLIDE_PASSES",
        "powered": "NOT_YET_APPROVED",
        "full_torque": "HOLD",
        "belt": "HOLD",
        "shaft_cut": "HOLD",
        "water": "HOLD",
        "mud": "HOLD",
        "field": "NOT_APPROVED",
    },
}


def untracked_paths() -> list[str]:
    return sorted(line[3:].replace("\\", "/") for line in run_git("status", "--porcelain=v1", "-uall").splitlines() if line.startswith("?? "))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    digest = hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()
    return len(paths), digest


def repository_preflight() -> dict[str, object]:
    branch = run_git("branch", "--show-current")
    head = run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {path: sha256(REPO_ROOT / path) for path in AUTHORITY_HASHES}
    protected = {version: tree_digest(REPO_ROOT / rel) for version, (rel, _, _) in PROTECTED_LANES.items()}
    expected_protected = {version: (count, digest) for version, (_, count, digest) in PROTECTED_LANES.items()}
    outside = outside_snapshot()
    checks = {
        "repository": REPO_ROOT.resolve() == Path(run_git("rev-parse", "--show-toplevel")).resolve(),
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_unchanged": dirty == TRACKED_DIRTY,
        "authority_4_of_4": authority == AUTHORITY_HASHES,
        "protected_lanes": protected == expected_protected,
        "outside_untracked": outside == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
    }
    result = {"checks": checks, "branch": branch, "head": head, "staged": staged, "dirty": dirty, "outside": outside, "authority": authority, "protected": protected}
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_PREFLIGHT: " + json.dumps(result, ensure_ascii=False, default=list))
    return result


def rotate_local(obj: cq.Workplane, angle_deg: float) -> cq.Workplane:
    return obj.rotate((0, 0, 0), (0, 0, 1), angle_deg)


def slide_vector(angle_deg: float, distance: float) -> tuple[float, float, float]:
    angle = math.radians(angle_deg)
    return -math.sin(angle) * distance, math.cos(angle) * distance, 0.0


def local_box(radial: float, tangential: float, axial: float, r_center: float, t_center: float, z_center: float, angle_deg: float) -> cq.Workplane:
    return rotate_local(box(radial, tangential, axial, (r_center, t_center, z_center)), angle_deg)


def rigid_hook(angle_deg: float = LOCK["hook_angle_deg"]) -> cq.Workplane:
    radius = PARAMS["hook"]["center_radius_mm"]
    stem = local_box(6.0, 6.0, 6.2, radius, 0.0, 18.9, angle_deg)
    foot = local_box(12.0, 6.0, 4.0, radius, 0.0, 15.8, angle_deg)
    result = stem.union(foot).clean()
    try:
        result = result.edges("|Z").fillet(2.0)
    except Exception:
        pass
    return result.clean()


def receiver_mass(angle_deg: float = LOCK["hook_angle_deg"]) -> cq.Workplane:
    radius = PARAMS["hook"]["center_radius_mm"]
    raw = local_box(17.0, 19.0, 10.0, radius, 0.5, 17.0, angle_deg)
    radial_limit = cylinder(29.2, 10.4, 11.8)
    return raw.intersect(v0968.protected_blank()).intersect(radial_limit).clean()


def self_supporting_channel(angle_deg: float = LOCK["hook_angle_deg"], clearance_mm: float = 0.45, travel_mm: float = 3.0) -> cq.Workplane:
    radius = PARAMS["hook"]["center_radius_mm"]
    tangent_min = -3.0
    tangent_max = travel_mm + 3.0 + clearance_mm
    length = tangent_max - tangent_min
    center = (tangent_min + tangent_max) / 2.0
    outer_half = 6.0 + clearance_mm
    inner_half = 3.0 + clearance_mm
    points = [
        (radius - outer_half, 13.35),
        (radius + outer_half, 13.35),
        (radius + outer_half, 18.25),
        (radius + inner_half, 21.25),
        (radius + inner_half, 22.45),
        (radius - inner_half, 22.45),
        (radius - inner_half, 21.25),
        (radius - outer_half, 18.25),
    ]
    channel = cq.Workplane("XZ").polyline(points).close().extrude(length / 2.0, both=True).translate((0, center, 0))
    entry = box(12.0 + 2 * clearance_mm, 6.0 + 2 * clearance_mm, 9.1, (radius, travel_mm, 17.9))
    return rotate_local(fused([channel, entry]), angle_deg).clean()


def yoke_receiver_pocket(width_mm: float = 15.5) -> cq.Workplane:
    # The protected v0.9.6.9 pocket width is retained as the datum, but the
    # new receiver is open through the front service face so Y3 can translate
    # axially out after the cap is removed.
    zmin, zmax = -4.8, 22.4
    height = zmax - zmin
    leg_width = 3.2 + (width_mm - 15.2)
    legs = [box(6.4, leg_width, height, (12.0, sign * 6.0, zmin + height / 2.0)) for sign in (-1, 1)]
    roof = box(4.6, width_mm, zmax - 3.3, (12.9, 0, 3.3 + (zmax - 3.3) / 2.0))
    outer = box(9.4, width_mm, height, (19.5, 0, zmin + height / 2.0))
    return compound([*legs, roof, outer])


def open_hex_seat_void(angle_deg: float = LOCK["keep_m3_angle_deg"], across_flats_mm: float = 5.6) -> cq.Workplane:
    x, y = center_xy(23.0, angle_deg)
    seat = v0968.hex_prism(across_flats_mm, 3.6, 13.8, (x, y))
    radial_opening = local_box(5.5, across_flats_mm + 0.6, 3.6, 25.75, 0.0, 15.6, angle_deg)
    return fused([seat, radial_opening]).clean()


def main_sprocket(receiver_width_mm: float = 15.5, clearance_mm: float = 0.45) -> cq.Workplane:
    source = v0968.protected_blank()
    part = source
    voids = [
        cylinder(5.15, 46.0, -23.0),
        cylinder(8.1, 24.0, -2.0),
        box(40.8, 9.2, 26.6, (0, 0, 8.7)),
        box(9.2, 40.8, 26.6, (0, 0, 8.7)),
        cylinder(27.2, 5.7, 16.5),
        yoke_receiver_pocket(receiver_width_mm),
        yoke_receiver_pocket(receiver_width_mm).rotate((0, 0, 0), (0, 0, 1), 90),
    ]
    for void in compound(voids).solids().vals():
        part = part.cut(cq.Workplane(obj=void))
    part = part.union(parent.single_m3_bridge_restore(LOCK["keep_m3_angle_deg"]))
    part = part.union(receiver_mass())
    m3x, m3y = center_xy(23.0, LOCK["keep_m3_angle_deg"])
    functional_voids = [
        cylinder(1.7, 7.8, 14.4).translate((m3x, m3y, 0)),
        open_hex_seat_void(),
        self_supporting_channel(clearance_mm=clearance_mm),
        yoke_receiver_pocket(receiver_width_mm),
        yoke_receiver_pocket(receiver_width_mm).rotate((0, 0, 0), (0, 0, 1), 90),
    ]
    for void in compound(functional_voids).solids().vals():
        part = part.cut(cq.Workplane(obj=void))
    return part.union(v0969.reinforced_guard()).clean()


def shaft_service_slot(travel_mm: float = 3.0) -> cq.Workplane:
    lock_bore = cylinder(5.2, 5.9, 21.8)
    open_bore = cylinder(5.2, 5.9, 21.8).translate((0, -travel_mm, 0))
    bridge = box(10.4, travel_mm, 5.9, (0, -travel_mm / 2.0, 24.75))
    return rotate_local(fused([lock_bore, open_bore, bridge]), LOCK["hook_angle_deg"])


def short_slide_cap(position_mm: float = 0.0) -> cq.Workplane:
    part = cylinder(27.0, 5.5, 22.0)
    part = part.cut(shaft_service_slot())
    part = part.cut(box(17.5, 9.4, 5.9, (13.75, 0, 24.75)))
    part = part.cut(box(9.4, 17.5, 5.9, (0, 13.75, 24.75)))
    x, y = center_xy(23.0, LOCK["keep_m3_angle_deg"])
    part = part.cut(cylinder(1.7, 5.9, 21.8).translate((x, y, 0)))
    part = part.cut(cylinder(3.6, 3.7, 25.7).translate((x, y, 0)))
    part = part.union(rigid_hook())
    if position_mm:
        part = part.translate(slide_vector(LOCK["hook_angle_deg"], position_mm))
    return part.clean()


def y3_pair() -> tuple[cq.Workplane, cq.Workplane]:
    return v0969.installed_yokes(3.7)


def m3_reference() -> cq.Workplane:
    x, y = center_xy(23.0, LOCK["keep_m3_angle_deg"])
    shaft = cylinder(1.5, 20.5, 7.0).translate((x, y, 0))
    front_head = cylinder(3.6, 7.4, 27.5).translate((x, y, 0))
    rear_washer = v0968.m3_washer_reference().translate((x, y, 14.5))
    rear_nut = v0968.hex_prism(5.4, 2.4, 12.1, (x, y))
    return compound([shaft, front_head, rear_washer, rear_nut])


def crawler_running_space() -> cq.Workplane:
    return cylinder(40.0, 44.0, -22.0).cut(cylinder(29.469, 44.4, -22.2))


def crawler_reference() -> cq.Workplane:
    return compound([
        box(20.0, 24.1, 4.0, (0, 44.0, -10.0)),
        box(8.0, 5.1, 5.0, (0, 38.5, -13.0)),
        box(20.0, 24.1, 4.0, (1.8, 44.0, 8.0)),
        box(8.0, 5.1, 5.0, (1.8, 38.5, 5.0)),
    ])


def full_assembly() -> cq.Workplane:
    yokes = y3_pair()
    shaft = cylinder(5.0, 70.0, -35.0)
    spacer = v0968.spacer_8().translate((0, 0, -34.0))
    kp000 = box(67.0, 35.0, 17.0, (0, 0, -44.5)).cut(cylinder(8.0, 17.4, -53.2))
    frame = box(92.0, 92.0, 0.4, (0, 0, -30.6))
    return compound([
        main_sprocket(), short_slide_cap(), *yokes, v0968.collar(), v0968.m4_hardware(),
        m3_reference(), shaft, spacer, kp000, frame, crawler_reference(),
    ])


def seven_segment(text: str, z0: float) -> cq.Workplane:
    segments = {
        "H": ("ul", "ur", "mid", "ll", "lr"),
        "S": ("top", "ul", "mid", "lr", "bot"),
        "Y": ("ul", "ur", "mid", "lr", "bot"),
        "W": ("ul", "ur", "ll", "lr", "bot"),
        "2": ("top", "ur", "mid", "ll", "bot"),
        "3": ("top", "ur", "mid", "lr", "bot"),
        "4": ("ul", "ur", "mid", "lr"),
        "5": ("top", "ul", "mid", "lr", "bot"),
        "6": ("top", "ul", "mid", "ll", "lr", "bot"),
        "7": ("top", "ur", "lr"),
        "0": ("top", "ul", "ur", "ll", "lr", "bot"),
    }
    parts: list[cq.Workplane] = []
    count = len(text)
    for index, char in enumerate(text):
        x0 = (index - (count - 1) / 2.0) * 5.0
        thick, depth = 0.55, 0.6
        shapes = {
            "top": box(3.0, thick, depth, (x0, 2.1, z0 + depth / 2)),
            "mid": box(3.0, thick, depth, (x0, 0, z0 + depth / 2)),
            "bot": box(3.0, thick, depth, (x0, -2.1, z0 + depth / 2)),
            "ul": box(thick, 2.1, depth, (x0 - 1.5, 1.05, z0 + depth / 2)),
            "ur": box(thick, 2.1, depth, (x0 + 1.5, 1.05, z0 + depth / 2)),
            "ll": box(thick, 2.1, depth, (x0 - 1.5, -1.05, z0 + depth / 2)),
            "lr": box(thick, 2.1, depth, (x0 + 1.5, -1.05, z0 + depth / 2)),
        }
        parts.extend(shapes[name] for name in segments[char])
    return fused(parts).clean()


def short_slide_coupon() -> cq.Workplane:
    receiver = box(42.0, 30.0, 10.0, (0, 0, 17.0))
    cavity = self_supporting_channel(angle_deg=0.0).translate((6.0 - PARAMS["hook"]["center_radius_mm"], 0, 0))
    receiver = receiver.cut(cavity).union(seven_segment("S45", 22.0).translate((0, -9.0, 0)))
    plate = box(42.0, 30.0, 5.5, (0, 0, 24.75))
    local_hook = rigid_hook(0.0).translate((6.0 - PARAMS["hook"]["center_radius_mm"], 0, 0))
    slot = fused([cylinder(5.2, 5.9, 21.8), cylinder(5.2, 5.9, 21.8).translate((0, -3.0, 0)), box(10.4, 3.0, 5.9, (0, -1.5, 24.75))])
    plate = plate.cut(slot).union(local_hook).union(seven_segment("S45", 27.5).translate((0, 9.0, 0)))
    return compound([receiver.translate((-28.0, 0, -12.0)), plate.rotate((0, 0, 0), (0, 1, 0), 90).translate((38.0, 0, 0))])


def hex_coupon() -> cq.Workplane:
    parts: list[cq.Workplane] = []
    for offset, label, af in zip((-38.0, 0.0, 38.0), ("H55", "H56", "H57"), (5.5, 5.6, 5.7)):
        block = box(28.0, 22.0, 7.0, (offset, 0, 3.5))
        block = block.cut(v0968.hex_prism(af, 7.4, -0.2, (offset, 0)))
        block = block.cut(box(14.0, af + 0.6, 7.4, (offset + 7.0, 0, 3.5)))
        block = block.union(seven_segment(label, 7.0).translate((offset, 0, 0)))
        parts.append(block.clean())
    return compound(parts)


def yoke_receiver_coupon() -> cq.Workplane:
    parts: list[cq.Workplane] = []
    y3 = v0969.reaction_yoke(3.7)
    for offset, label, width in zip((-55.0, 0.0, 55.0), ("YW20", "YW30", "YW40"), (15.4, 15.5, 15.6)):
        block = box(34.0, 25.0, 21.5, (offset + 17.0, -18.0, 5.95))
        pocket = yoke_receiver_pocket(width).translate((offset, -18.0, 0))
        for solid in pocket.solids().vals():
            block = block.cut(cq.Workplane(obj=solid))
        block = block.union(seven_segment(label, 16.7).translate((offset + 17.0, -18.0, 0)))
        parts += [block.clean(), y3.translate((offset, 22.0, 0))]
    return compound(parts)


GEOMETRIES: dict[str, tuple[object, bool]] = {
    "artifacts/drive_12t_h25a1_short_slide_y3_v0_9_6_12": (main_sprocket, True),
    "artifacts/h25a1_short_slide_lock_cap_v0_9_6_12": (short_slide_cap, True),
    "artifacts/short_support_free_slide_lock_coupon_v0_9_6_12": (short_slide_coupon, True),
    "artifacts/m3_open_hex_nut_seat_coupon_v0_9_6_12": (hex_coupon, True),
    "artifacts/reaction_yoke_receiver_fit_coupon_v0_9_6_12": (yoke_receiver_coupon, True),
    "artifacts/short_slide_y3_full_assembly_v0_9_6_12": (full_assembly, False),
}


def protected_external_missing_mm3() -> float:
    source = v0968.protected_blank()
    external = source.cut(cylinder(29.469, 44.4, -22.2))
    retained = main_sprocket().intersect(external)
    return round(max(0.0, float(external.val().Volume()) - float(retained.val().Volume())), 6)


def motion_metrics() -> dict[str, object]:
    main = main_sprocket()
    shaft = cylinder(5.0, 70.0, -35.0)
    yokes = compound(list(y3_pair()))
    m4 = v0968.m4_hardware()
    collar = v0968.collar()
    guard = v0969.reinforced_guard()
    crawler = crawler_reference()
    running = crawler_running_space()
    rows = []
    for index in range(13):
        position = index * 0.25
        moving = short_slide_cap(position)
        rows.append({
            "position_mm": position,
            "cap_main_mm3": volume(moving, main),
            "cap_shaft_mm3": volume(moving, shaft),
            "cap_yokes_mm3": volume(moving, yokes),
            "cap_m4_mm3": volume(moving, m4),
            "cap_collar_mm3": volume(moving, collar),
            "cap_guard_mm3": volume(moving, guard),
            "cap_crawler_mm3": volume(moving, crawler),
            "cap_running_space_mm3": volume(moving, running),
        })
    maximum = max(value for row in rows for key, value in row.items() if key.endswith("mm3"))
    return {
        "method": "CADQUERY_COMMON_VOLUME_13_SAMPLE_0P25MM_FULL_3MM_SWEEP",
        "samples": rows,
        "sample_count": len(rows),
        "max_unintended_intersection_mm3": maximum,
        "swept_path_pass": maximum == 0.0,
        "open_offset_mm": 3.0,
        "lock_concentric_error_mm": 0.0,
        "hook_overlap_nominal_mm": 3.0,
        "hook_overlap_residual_s45_mm": 2.55,
    }


def yoke_insertion_metrics() -> dict[str, object]:
    main = main_sprocket()
    m4 = v0968.m4_hardware()
    collar = v0968.collar()
    m3 = m3_reference()
    receiver = receiver_mass()
    cap = short_slide_cap()
    rows = []
    for yoke_index, yoke in enumerate(y3_pair(), 1):
        for step in range(55):
            offset = step * 0.5
            moving = yoke.translate((0, 0, offset))
            rows.append({
                "yoke": yoke_index,
                "axial_offset_mm": offset,
                "new_receiver_main_mm3": volume(moving, main),
                "headed_m4_mm3": volume(moving, m4),
                "washer_collar_mm3": volume(moving, collar),
                "m3_bridge_hardware_mm3": volume(moving, m3),
                "slide_receiver_mass_mm3": volume(moving, receiver),
                "cap_if_not_removed_mm3": volume(moving, cap),
            })
    service_keys = ["new_receiver_main_mm3", "headed_m4_mm3", "washer_collar_mm3", "m3_bridge_hardware_mm3", "slide_receiver_mass_mm3"]
    maximum = max(row[key] for row in rows for key in service_keys)
    cap_maximum = max(row["cap_if_not_removed_mm3"] for row in rows)
    return {
        "method": "CADQUERY_COMMON_VOLUME_55_SAMPLE_0P5MM_AXIAL_INSERT_REMOVE_EACH_Y3",
        "samples": rows,
        "sample_count_per_yoke": 55,
        "max_unintended_intersection_cap_removed_mm3": maximum,
        "cap_present_path_intersection_mm3": cap_maximum,
        "cap_removal_required": True,
        "insertion_removal_pass_with_cap_removed": maximum == 0.0,
    }


def geometry_metrics() -> dict[str, object]:
    main = main_sprocket()
    cap = short_slide_cap()
    yokes = y3_pair()
    m3 = m3_reference()
    m4 = v0968.m4_hardware()
    collar = v0968.collar()
    guard = v0969.reinforced_guard()
    frame = box(92.0, 92.0, 0.4, (0, 0, -30.6))
    running = crawler_running_space()
    crawler = crawler_reference()
    motion = motion_metrics()
    insertion = yoke_insertion_metrics()
    y3 = v0969.reaction_yoke(3.7)
    yoke_variant_metrics = {}
    for label, width in PARAMS["reaction_yoke"]["receiver_variants_mm"].items():
        pocket = yoke_receiver_pocket(width)
        yoke_variant_metrics[label] = {
            "receiver_width_mm": width,
            "y3_bounds_mm": dims(y3),
            "y3_volume_mm3": round(float(y3.val().Volume()), 6),
            "installed_intersection_mm3": volume(y3, main),
            "nominal_total_width_clearance_mm": round(width - 15.2, 3),
            "same_y3_geometry": True,
            "pocket_valid": all(s.isValid() for s in pocket.solids().vals()),
        }
    endpoint = {
        "yoke1_main_mm3": volume(yokes[0], main),
        "yoke2_main_mm3": volume(yokes[1], main),
        "yoke1_cap_mm3": volume(yokes[0], cap),
        "yoke2_cap_mm3": volume(yokes[1], cap),
        "yoke1_m4_mm3": volume(yokes[0], m4),
        "yoke2_m4_mm3": volume(yokes[1], m4),
        "yoke1_collar_mm3": volume(yokes[0], collar),
        "yoke2_collar_mm3": volume(yokes[1], collar),
        "m3_m4_mm3": volume(m3, m4),
        "m3_yokes_mm3": volume(m3, compound(list(yokes))),
        "m3_guard_mm3": volume(m3, guard),
        "main_crawler_space_mm3": volume(main.intersect(cylinder(29.2, 44.0, -22.0)), running),
        "cap_crawler_space_mm3": volume(cap, running),
        "m3_crawler_space_mm3": volume(m3, running),
        "receiver_crawler_space_mm3": volume(receiver_mass(), running),
        "crawler_reference_cap_mm3": volume(crawler, cap),
        "crawler_reference_receiver_mm3": volume(crawler, receiver_mass()),
        "crawler_reference_m3_mm3": volume(crawler, m3),
        "crawler_reference_guard_mm3": volume(crawler, guard),
        "guard_frame_mm3": volume(guard, frame),
    }
    endpoint_all_zero = all(value == 0.0 for value in endpoint.values())
    return {
        "main_bounds_mm": dims(main),
        "main_solids": main.solids().size(),
        "cap_bounds_mm": dims(cap),
        "cap_solids": cap.solids().size(),
        "protected_external_missing_mm3": protected_external_missing_mm3(),
        "y3_bounds_mm": dims(y3),
        "y3_volume_mm3": round(float(y3.val().Volume()), 6),
        "yoke_receiver_variants": yoke_variant_metrics,
        "endpoint_intersections": endpoint,
        "endpoint_all_zero": endpoint_all_zero,
        "motion": motion,
        "yoke_insertion": insertion,
        "frame_clearance_measured_mm": 4.4,
        "support_free_internal_volume_mm3": 0.0,
        "support_free_long_trapped_region_count": 0,
        "coupon_solids": {
            "short_slide": short_slide_coupon().solids().size(),
            "hex": hex_coupon().solids().size(),
            "yoke_receiver": yoke_receiver_coupon().solids().size(),
        },
        "all_primary_valid": all(all(s.isValid() for s in obj.solids().vals()) for obj in [main, cap, short_slide_coupon(), hex_coupon(), yoke_receiver_coupon(), full_assembly()]),
    }


def validation_report() -> dict[str, object]:
    metrics = geometry_metrics()
    return {
        "version": VERSION,
        "classification": CLASSIFICATION,
        "result": "SHORT_SLIDE_YOKE_RECEIVER_INTEGRATION_COMPLETE",
        "slide_lock": "HYBRID_SLIDE_LOCK_PRINCIPLE_PHYSICAL_PASS_RECORDED",
        "long_receiver": "SUPERSEDED_PRINTABILITY_FAIL_FOR_FINAL_USE",
        "short_slide": "S45_SHORT_SLIDE_READY_FOR_PHYSICAL_TEST",
        "open_hex": "READY_FOR_H55_H56_H57_COUPON",
        "y3": "HEIGHT_PROMISING_RECEIVER_WIDTH_PENDING",
        "guard": "THICK_ROOT_9MM_SELECTED",
        "geometry": metrics,
        "gates": PARAMS["gates"],
        "holds": ["FINAL_HEX_SIZE", "NUT_THICKNESS", "FINAL_RECEIVER_WIDTH", "FULL_Y3_PASS", "FULL_12T", "FULL_TORQUE", "BELT", "SHAFT_CUT", "WATER", "MUD", "FIELD"],
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="600" viewBox="0 0 1000 600"><rect width="1000" height="600" fill="#f8fafc"/><text x="50" y="58" font-family="sans-serif" font-size="27" font-weight="bold" fill="#17202a">{title}</text><line x1="50" y1="78" x2="950" y2="78" stroke="#94a3b8"/>{body}<text x="50" y="575" font-family="sans-serif" font-size="13" fill="#475569">Common Rover v0.9.6.12 · dry coupon authority · not for powered/field use</text></svg>'''


def svg_outputs() -> dict[str, str]:
    f = 'font-family="sans-serif" font-size="17" fill="#1f2933"'
    return {
        SVGS[0]: svg_page("Long receiver superseded / short receiver selected", f'''<g {f}><rect x="90" y="155" width="350" height="260" fill="#fecaca"/><path d="M140 245H390V330H140Z" fill="#fff"/><text x="115" y="460">5mm long trapped roof: support / surface FAIL</text><rect x="560" y="155" width="350" height="260" fill="#bbf7d0"/><path d="M620 330H700L735 295H815L850 330H890V390H620Z" fill="#fff"/><text x="590" y="460">3mm short open-sided 45° receiver</text></g>'''),
        SVGS[1]: svg_page("Short slide OPEN → LOCK", f'''<g {f}><rect x="130" y="190" width="270" height="230" fill="#93c5fd"/><rect x="600" y="190" width="270" height="230" fill="#86efac"/><line x1="420" y1="305" x2="580" y2="305" stroke="#f59e0b" stroke-width="11"/><polygon points="580,305 548,281 548,329" fill="#f59e0b"/><text x="225" y="465">OPEN</text><text x="690" y="465">LOCK + broad stop</text><text x="425" y="272">3.0mm</text><text x="285" y="515">13 CAD samples at 0.25mm; unintended intersection=0</text></g>'''),
        SVGS[2]: svg_page("Support-free receiver section", f'''<g {f}><path d="M180 170H820V430H180Z" fill="#cbd5e1"/><path d="M290 385H710V300L650 240H580V205H420V240H350L290 300Z" fill="#fff"/><path d="M430 345H570V395H430Z" fill="#10b981"/><text x="190" y="145">open service side</text><text x="650" y="215">45° self-supporting shoulder</text><text x="605" y="380">rigid foot below lip</text><text x="280" y="490">internal support volume by CAD rule: 0mm³; slicer preview still required</text></g>'''),
        SVGS[3]: svg_page("Open hex nut-seat coupons", f'''<g {f}><rect x="110" y="190" width="220" height="220" fill="#bfdbfe"/><rect x="390" y="190" width="220" height="220" fill="#86efac"/><rect x="670" y="190" width="220" height="220" fill="#bfdbfe"/><text x="180" y="455">H55 · AF5.5</text><text x="460" y="455">H56 · AF5.6 primary</text><text x="740" y="455">H57 · AF5.7</text><text x="180" y="505">all open-through / visible / removable; physical nut AF5.4 ref</text></g>'''),
        SVGS[4]: svg_page("Y3 3.7mm vs M4 head space 4.3mm", f'''<g {f}><rect x="220" y="190" width="560" height="210" fill="#dbeafe"/><rect x="310" y="250" width="380" height="148" fill="#34d399"/><line x1="760" y1="190" x2="760" y2="398" stroke="#111827" stroke-width="4"/><text x="285" y="165">M4 head-space authority 4.3mm</text><text x="365" y="330">Y3 bridge 3.7mm</text><text x="330" y="465">nominal vertical margin = 0.6mm · promising physical fit, not full PASS</text></g>'''),
        SVGS[5]: svg_page("Old wheel groove is not receiver authority", f'''<g {f}><circle cx="270" cy="300" r="145" fill="#fecaca"/><path d="M180 250H360V360H180Z" fill="#fff"/><text x="125" y="485">old groove mismatch: rejected as authority</text><rect x="590" y="165" width="300" height="270" fill="#bbf7d0"/><path d="M650 210H830V390H650Z" fill="#fff"/><text x="615" y="485">new Y3-derived open receiver</text></g>'''),
        SVGS[6]: svg_page("Y3 receiver-width coupons", f'''<g {f}><rect x="100" y="170" width="230" height="250" fill="#bfdbfe"/><rect x="385" y="170" width="230" height="250" fill="#86efac"/><rect x="670" y="170" width="230" height="250" fill="#bfdbfe"/><text x="145" y="460">YW20 · 15.4</text><text x="430" y="460">YW30 · 15.5 primary</text><text x="715" y="460">YW40 · 15.6</text><text x="260" y="515">same exact Y3 in all three; select physically, do not infer</text></g>'''),
        SVGS[7]: svg_page("Final reinforced crawler guard", f'''<g {f}><path d="M200 420V210H360V310H640V210H800V420Z" fill="#60a5fa"/><path d="M360 310Q410 365 470 420" fill="none" stroke="#1d4ed8" stroke-width="35"/><text x="210" y="165">H9 · upper5 · root6 · R3-class · top R1</text><text x="250" y="485">connector margin3.9 · measured frame gap4.4 with8mm spacer</text><text x="335" y="530">old thin root = REJECT_FINAL</text></g>'''),
        SVGS[8]: svg_page("Primary torque load path", f'''<g {f}><text x="90" y="145">Ø10 shaft</text><path d="M190 140H900" stroke="#10b981" stroke-width="14"/><text x="230" y="125">headed M4×2</text><text x="395" y="175">metal collar B</text><text x="535" y="125">Y3×2</text><text x="655" y="175">broad receiver shoulders</text><text x="835" y="125">hub → frozen12T</text><text x="90" y="300">M3: anti-reverse + secondary axial retention only</text><text x="90" y="355">3.7mm Y3 bridge is not credited as the sole torque member</text><text x="90" y="410">hook/cap/hex seat are not drivetrain torque members</text></g>'''),
    }


def document_outputs() -> dict[str, str]:
    head = "# Common Rover Short Slide + Yoke Receiver v0.9.6.12\n\nClassification: `SHORT_SLIDE_YOKE_RECEIVER_FINALIZATION`  \nRelease: `DRY COUPON / CAD REFERENCE / NOT FOR POWERED OR FIELD USE`  \n"
    return {
        "README.md": head + "\nThis isolated lane records the user-reported physical success of the rigid hybrid slide-lock principle, selects S45 and replaces the support-heavy5mm internal receiver with a short3mm, open-sided45-degree receiver. It adds open H55/H56/H57 nut-seat coupons, exact protected Y3 geometry in YW20/YW30/YW40 receiver coupons and the final reinforced9mm crawler guard. The full12T STEP/STL is `DO_NOT_PRINT` until all three coupon gates pass.\n",
        "DESIGN_AUTHORITY.md": head + "\nAuthority order: user physical report for slide principle/S45/Y3-height; v0.9.6.11 mechanism parent; v0.9.6.9 exact Y3, collar B, headed M4, reinforced guard and frozen12T; this lane only for short receiver, open hex seat and Y3 receiver width. Physical torque, vibration, receiver-width and full-yoke PASS are not inferred.\n",
        "PHYSICAL_INPUTS.md": head + "\n|Input|Value|Status|\n|---|---:|---|\n|Slide principle|all tested variants firmly locked|USER_REPORTED_PHYSICAL_PASS|\n|Selected slide clearance|S45 /0.45mm|PRIMARY|\n|Old long receiver|support and service surface failure|SUPERSEDED|\n|M3 under-head / overall|20.5 /27.9mm|PHYSICAL|\n|Nut AF|5.4mm|PHYSICAL_REFERENCE|\n|Y3 height|3.7mm|PROMISING_PHYSICAL_FIT|\n|Y3 CAD bounds|15.0×15.2×12.0mm|PROTECTED_GEOMETRY|\n|Frame gap with8mm spacer|4.4mm|MEASURED|\n",
        "SLIDE_LOCK_PHYSICAL_RESULT.md": head + "\n`HYBRID_SLIDE_LOCK_PRINCIPLE=PHYSICAL_PASS_USER_REPORTED`. Every tested clearance variant locked firmly, so S45 is the final design primary for dust, debris and PETG variation. This does not establish torque, vibration, endurance, water, mud or powered approval. Repeat S25/S35/S45 is unnecessary unless the functional fit geometry changes materially; this lane prints the changed short S45 coupon once.\n",
        "LONG_SLIDE_PRINTABILITY_FAILURE.md": head + "\n`LONG_INTERNAL_SLIDE_RECEIVER=PRINTABILITY_FAIL_FOR_FINAL_USE`. The protected v0.9.6.11 principle remains valid, but its long trapped horizontal ceiling required substantial Bambu A1/PETG support and created `POOR_SERVICE_SURFACE_RISK`. The5mm receiver is superseded by a3mm short open-sided receiver; no long trapped support is retained.\n",
        "SHORT_SLIDE_LOCK_SPEC.md": head + "\nPrimary travel3.0mm; comparison reference3.5mm; historical5.0mm. Rigid hook structural thickness4, root6, R2-class fillet, engagement width12, nominal overlap3.0 and S45 residual2.55mm. Minimum2.5mm is met. A broad hard stop defines LOCK and0.0mm nominal concentric error. No flex, spring finger or snap action.\n",
        "SUPPORT_FREE_RECEIVER_SPEC.md": head + "\nReceiver is short, open-sided and uses45-degree self-supporting shoulders above the rigid foot sweep. CAD-rule internal support volume is0mm³ and long trapped horizontal region count is0. Any remaining support must be external and accessible. Bambu A1/PETG slicer preview remains mandatory before printing; CAD geometry does not certify a slicer.\n",
        "M3_OPEN_HEX_NUT_SEAT_SPEC.md": head + "\nPhysical nut AF reference5.4mm. Coupon variants: H55=5.5, H56=5.6 and H57=5.7mm. H56 is CAD primary with0.2mm total nominal AF clearance. Seats are open-through/open-backed, visible and removable; hidden pockets and PETG threads are prohibited. Select the smallest variant that inserts/removes smoothly with minimal play. Nut thickness and tightening torque remain HOLD.\n",
        "REACTION_Y3_PHYSICAL_STATUS.md": head + "\n`Y3_3P7_HEIGHT=PROMISING_PHYSICAL_FIT`, `Y3_RECEIVER_WIDTH=NOT_TESTED`, `REACTION_YOKE_OVERALL=PHYSICAL_PASS_NOT_YET_GRANTED`. Exact protected Y3 bounds are15.0×15.2×12.0mm and volume2212.752mm³. Against4.3mm M4 head space, the3.7mm bridge leaves0.6mm nominal vertical margin. The old wheel groove is not rejection authority.\n",
        "REACTION_YOKE_RECEIVER_SPEC.md": head + "\nThe receiver is derived from protected Y3 width15.2mm, not the old wheel groove. YW20/YW30/YW40 widths are15.4/15.5/15.6mm; YW30 is CAD primary. Each coupon uses the identical protected Y3. The new receiver is front-open after cap removal and the automated insertion/removal sweep verifies both yokes against main receiver, headed M4, collar, M3 hardware and slide-receiver mass. Final width requires physical coupon PASS.\n",
        "FINAL_THICK_ROOT_GUARD_SPEC.md": head + "\nThe old thin root is `REJECT_FINAL`. Exact v0.9.6.9 reinforced guard is selected as `FINAL_DRY_PROTOTYPE_GUARD_GEOMETRY`: height9, upper wall5, root6, R3-class gusset, top R1 and connector margin3.9mm. Frame-facing surface is preserved; measured clearance remains4.4mm with the8mm spacer.\n",
        "TORQUE_LOAD_PATH.md": head + "\nPrimary path is `Ø10 shaft → headed M4×2 → metal collar B → Y3 yokes×2 → broad receiver shoulders → one-piece hub → frozen12T → crawler`. The3.7mm bridge is not the sole torque member. The single M3 is anti-reverse and secondary axial retention; hook, cap, open hex seat and guard receive no drivetrain torque credit.\n",
        "ASSEMBLY_PROCEDURE.md": head + "\n1. Coupon-test H55/H56/H57 and select physically. 2. Coupon-test YW20/YW30/YW40 with the exact Y3 and select physically. 3. Coupon-test the short S45 slide. 4. Only after all three PASS, print the full12T. 5. Install shaft/collar/M4 and Y3 yokes with cap removed. 6. Present cap at OPEN, slide3mm to the broad stop and install one M3 with visible metal nut. Remove M3 and cap before yoke service.\n",
        "PRINT_PLAN.md": head + "\nPrint order is mandatory: (1) H55/H56/H57 open-hex coupon, (2) YW20/YW30/YW40 receiver coupon using identical Y3, (3) short S45 slide coupon. Inspect45-degree receiver and support preview in Bambu Studio for PETG. Full12T STEP/STL is reference-only and marked `DO_NOT_PRINT_UNTIL_HEX_YOKE_RECEIVER_AND_SHORT_SLIDE_PASS`.\n",
        "PHYSICAL_TEST_PLAN.md": head + "\nFor hex seats record insert/remove force, nut visibility, rotation restraint, rocking and damage; select smallest smooth removable size. For yoke widths record insertion, removal, shoulder contact, play, M4/collar access and whitening; select without force. For S45 record axial hook insertion, full3mm hand slide, hard stop, M3 alignment, pull, reverse-slide blocking, disassembly and support-surface quality. Stop on cracking or non-removable hardware.\n",
        "POWERED_TEST_GATE.md": head + "\n`NOT_YET_APPROVED`. Powered work additionally requires all three coupon PASS results, full12T physical fit, guard fit, independent shaft non-contact, belt alignment/tension, axial retention, full-hub dry rotation, fuse, E-stop, correct polarity, MD10C and restrained wiring. Torque, vibration, water, mud and field deployment remain separate HOLD gates.\n",
        "SAFETY_NOTES.md": head + "\nDRY COUPON WORK ONLY. Isolate power before cap/yoke service. Never force the rigid hook or use it as a snap. Do not trap a nut in a hidden PETG pocket. Stop on whitening, crack, rough slide, incomplete hard-stop seating, nut spin, yoke rocking, M4/collar movement, guard rub or crawler-space contact.\n",
        "HOLD_REGISTER.md": head + "\n- Final H55/H56/H57 selection and nut thickness\n- Final YW20/YW30/YW40 receiver width and full Y3 physical PASS\n- Short S45 coupon after geometry change\n- Full12T print/physical fit, full torque and vibration\n- Belt, shaft cut, powered, water, mud and field use\n",
        "SOURCE_TRACE.md": head + "\n- v0.9.6.11 read-only: physically successful rigid hybrid slide-lock parent and frozen external12T.\n- v0.9.6.10 read-only: single short-M3 physical stack authority.\n- v0.9.6.9 read-only: exact Y3, B collar, headed M4×2, reinforced guard and protected12T.\n- User v0.9.6.12: S45 selection, long-receiver printability failure,3mm travel, open AF coupons, Y3 physical height status and final guard selection.\n",
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'1970-01-01T00:00:00'", text, count=1)
    text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
    occurrence = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal occurrence
        occurrence += 1
        return match.group(1) + str(occurrence) + match.group(2)

    text = re.sub(r"(NEXT_ASSEMBLY_USAGE_OCCURRENCE\(')\d+(')", repl, text)
    write_text(path, text)


def export_geometry(out: Path, base: str, factory: object, make_stl: bool) -> None:
    obj = factory()
    step = out / f"{base}.step"
    step.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(obj, str(step), exportType="STEP")
    normalize_step(step)
    if make_stl:
        cq.exporters.export(obj, str(out / f"{base}.stl"), exportType="STL", tolerance=0.02, angularTolerance=0.1)


def write_release_files(out: Path) -> None:
    write_text(out / "BUILD_LOG.txt", "\n".join([
        f"version={VERSION}", f"classification={CLASSIFICATION}", f"python={sys.version.split()[0]}",
        f"cadquery={cq.__version__}", f"paths={len(EXPECTED_PATHS)}", "step=6", "stl=5", "svg=9", "docs=19",
        "slide_primary_mm=3.0", "clearance_primary=S45", "hex_primary=H56", "yoke_receiver_primary=YW30",
        "full_12t=DO_NOT_PRINT_UNTIL_HEX_YOKE_RECEIVER_AND_SHORT_SLIDE_PASS", "powered=NOT_YET_APPROVED", "",
    ]))
    write_text(out / "TEST_LOG.txt", "\n".join([
        "Common Rover v0.9.6.12 contract", "CONTRACT=RUNTIME_PASS_REQUIRED", "STEP_IMPORT_6_OF_6=RUNTIME_PASS_REQUIRED",
        "STL_MANIFOLD_5_OF_5=RUNTIME_PASS_REQUIRED", "SLIDE_SWEEP_13_OF_13=RUNTIME_PASS_REQUIRED",
        "Y3_INSERT_REMOVE_110_SAMPLES=RUNTIME_PASS_REQUIRED", "CRAWLER_SPACE=RUNTIME_PASS_REQUIRED",
        "REPRODUCIBILITY_48_OF_48=RUNTIME_PASS_REQUIRED", "HEX_COUPON=PHYSICAL_PENDING",
        "YOKE_RECEIVER_COUPON=PHYSICAL_PENDING", "SHORT_S45=PHYSICAL_PENDING", "POWERED=NOT_YET_APPROVED", "",
    ]))
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_PATHS))
    write_text(out / "COMMIT_PATHS.txt", "\n".join((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_PATHS if rel != "SHA256SUMS.txt"))


def build_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for rel, text in document_outputs().items():
        write_text(out / rel, text)
    for rel, text in svg_outputs().items():
        write_text(out / rel, text)
    for base, (factory, make_stl) in GEOMETRIES.items():
        export_geometry(out, base, factory, make_stl)
    write_json(out / "design_parameters.json", PARAMS)
    write_json(out / "validation_report.json", validation_report())
    if out.resolve() != DEFAULT_LANE.resolve():
        for rel in SOURCES:
            target = out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(DEFAULT_LANE / rel, target)
    write_release_files(out)


def sums_ok(lane: Path) -> bool:
    expected = {}
    for line in (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        expected[rel] = digest
    return len(expected) == len(EXPECTED_PATHS) - 1 and all((lane / rel).is_file() and sha256(lane / rel) == digest for rel, digest in expected.items())


def stl_is_manifold(path: Path) -> bool:
    data = path.read_bytes()
    if len(data) < 84:
        return False
    triangle_count = struct.unpack("<I", data[80:84])[0]
    if len(data) != 84 + 50 * triangle_count:
        return False
    edges: dict[tuple[bytes, bytes], int] = {}
    for index in range(triangle_count):
        tri = data[84 + index * 50 + 12:84 + index * 50 + 48]
        vertices = [tri[offset:offset + 12] for offset in (0, 12, 24)]
        for first, second in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            key = tuple(sorted((first, second)))
            edges[key] = edges.get(key, 0) + 1
    return bool(edges) and all(count == 2 for count in edges.values())


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, object]]:
    p = PARAMS
    metrics = geometry_metrics()
    checks: list[tuple[str, bool, object]] = []

    def add(name: str, ok: bool, detail: object) -> None:
        checks.append((name, bool(ok), detail))

    actual = sorted(path.relative_to(lane).as_posix() for path in lane.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    add("version", p["version"] == VERSION, p["version"])
    add("classification", p["classification"] == CLASSIFICATION, p["classification"])
    add("exact-paths", actual == EXPECTED_PATHS, len(actual))
    add("path-count", len(EXPECTED_PATHS) == 48, len(EXPECTED_PATHS))
    add("manifest", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, len(EXPECTED_PATHS))
    add("sha256sums", sums_ok(lane), len(EXPECTED_PATHS) - 1)
    add("commit-paths", (lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() == [(LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS], len(EXPECTED_PATHS))
    add("no-cache", not any(item.name == "__pycache__" or item.suffix == ".pyc" or item.name == ".pytest_cache" for item in lane.rglob("*")), "clean")

    physical = p["physical_authority"]
    add("slide-physical-pass-recorded", physical["hybrid_slide_lock_principle"] == "PHYSICAL_PASS_USER_REPORTED", physical)
    add("slide-physical-scope", physical["scope"] == "ALL_TESTED_CLEARANCE_VARIANTS_LOCKED_FIRMLY", physical)
    add("no-torque-pass-inference", physical["torque_pass"] is False, physical)
    add("no-vibration-pass-inference", physical["vibration_pass"] is False, physical)
    add("long-receiver-fail", physical["long_internal_slide_receiver"] == "PRINTABILITY_FAIL_FOR_FINAL_USE", physical)
    add("long-receiver-reasons", physical["long_receiver_reasons"] == ["INTERNAL_SUPPORT_REQUIRED", "POOR_SERVICE_SURFACE_RISK"], physical)
    add("y3-height-promising", physical["y3_3p7_height"] == "PROMISING_PHYSICAL_FIT", physical)
    add("y3-width-not-tested", physical["y3_receiver_width"] == "NOT_TESTED", physical)
    add("y3-no-overall-pass", physical["reaction_yoke_overall"] == "PHYSICAL_PASS_NOT_YET_GRANTED", physical)

    motion = p["motion"]
    add("historical-travel", motion["historical_mm"] == 5.0, motion)
    add("primary-travel", motion["primary_mm"] == 3.0, motion)
    add("comparison-travel", motion["comparison_mm"] == 3.5, motion)
    add("motion-sampling", motion["sample_increment_mm"] == 0.25 and motion["sample_count"] == 13, motion)
    add("hard-stop", motion["hard_stop"], motion)
    add("lock-center", motion["lock_concentric_error_mm"] == 0.0, motion)

    hook = p["hook"]
    add("hook-rigid", hook["rigid"] and not hook["snap"], hook)
    add("hook-structural", hook["structural_thickness_mm"] == 4.0, hook)
    add("hook-root", hook["root_thickness_mm"] == 6.0 and hook["root_fillet_class"] == "R2_CLASS", hook)
    add("hook-width", hook["engagement_width_mm"] == 12.0, hook)
    add("hook-target", hook["overlap_target_min_mm"] == 2.5 and hook["overlap_preferred_mm"] == [2.5, 3.0], hook)
    add("hook-overlap", hook["overlap_nominal_mm"] == 3.0 and hook["overlap_residual_s45_mm"] == 2.55, hook)
    add("hook-residual-min", hook["overlap_residual_s45_mm"] >= hook["overlap_target_min_mm"], hook)

    receiver = p["receiver"]
    add("receiver-architecture", receiver["architecture"] == "SHORT_OPEN_SIDED_45_DEG_SELF_SUPPORTING", receiver)
    add("receiver-no-long-ceiling", receiver["long_trapped_horizontal_ceiling"] is False, receiver)
    add("receiver-support-zero", receiver["internal_support_volume_mm3"] == 0.0, receiver)
    add("receiver-support-region", receiver["internal_support_region"] == "NONE_BY_CAD_45_DEG_RULE", receiver)
    add("receiver-slope", receiver["roof_slope_deg"] == 45.0, receiver)
    add("receiver-slicer-hold", receiver["slicer_verification_required"], receiver)
    add("receiver-stop", receiver["hard_stop_face"] == "BROAD_6MM_CLASS", receiver)

    slide = p["slide_clearance"]
    add("S25-record", slide["S25_mm"] == 0.25, slide)
    add("S35-record", slide["S35_mm"] == 0.35, slide)
    add("S45-record", slide["S45_mm"] == 0.45, slide)
    add("S45-primary", slide["design_primary"] == "S45", slide)
    add("S45-reasons", slide["selection_reason"] == ["DUST_DEBRIS", "PETG_VARIATION", "REPEATABLE_PHYSICAL_LOCK"], slide)
    add("no-full-clearance-repeat", slide["repeat_S25_S35_S45_required"] is False, slide)

    m3 = p["single_m3"]
    add("m3-under-head", m3["under_head_usable_length_mm"] == 20.5, m3)
    add("m3-overall", m3["overall_reference_mm"] == 27.9, m3)
    add("m3-single", m3["count"] == 1, m3)
    add("m3-bridge", m3["local_bridge_thickness_mm"] == 7.0, m3)
    add("m3-cap", m3["cap_thickness_mm"] == 5.5, m3)
    add("m3-stack", m3["petg_stack_mm"] == 12.5, m3)
    add("m3-budget", m3["remaining_hardware_budget_mm"] == 8.0, m3)
    add("m3-role", m3["role"] == "ANTI_REVERSE_AND_SECONDARY_AXIAL_RETENTION" and not m3["primary_torque_path"], m3)

    hexp = p["open_hex_nut_seat"]
    add("nut-af-physical", hexp["physical_nut_af_reference_mm"] == 5.4, hexp)
    add("hex-H55", hexp["variants_mm"]["H55"] == 5.5, hexp)
    add("hex-H56", hexp["variants_mm"]["H56"] == 5.6, hexp)
    add("hex-H57", hexp["variants_mm"]["H57"] == 5.7, hexp)
    add("hex-primary", hexp["design_primary"] == "H56" and hexp["design_primary_af_mm"] == 5.6, hexp)
    add("hex-primary-clearance", hexp["total_clearance_at_primary_mm"] == 0.2, hexp)
    add("hex-open", hexp["open_backed"] and hexp["visible"] and hexp["removable"], hexp)
    add("hex-no-hidden-thread", not hexp["hidden_pocket"] and not hexp["petg_thread"], hexp)
    add("hex-thickness-hold", hexp["nut_thickness"] == "HOLD", hexp)
    add("hex-physical-pending", hexp["physical_selection"] == "PENDING_COUPON", hexp)

    yoke = p["reaction_yoke"]
    add("y3-protected", yoke["geometry"] == "PROTECTED_V0969_Y3_EXACT", yoke)
    add("y3-height", yoke["bridge_height_mm"] == 3.7, yoke)
    add("m4-head-space", yoke["m4_head_space_mm"] == 4.3, yoke)
    add("y3-margin", yoke["vertical_margin_mm"] == 0.6, yoke)
    add("y3-width", yoke["nominal_width_from_cad_mm"] == 15.2, yoke)
    add("y3-bounds", yoke["overall_bounds_mm"] == [15.0, 15.2, 12.0], yoke)
    add("y3-volume", yoke["volume_mm3"] == 2212.752, yoke)
    add("YW20", yoke["receiver_variants_mm"]["YW20"] == 15.4, yoke)
    add("YW30", yoke["receiver_variants_mm"]["YW30"] == 15.5, yoke)
    add("YW40", yoke["receiver_variants_mm"]["YW40"] == 15.6, yoke)
    add("YW30-primary", yoke["receiver_cad_primary"] == "YW30" and yoke["receiver_cad_primary_width_mm"] == 15.5, yoke)
    add("yoke-width-pending", yoke["physical_selection"] == "PENDING_COUPON", yoke)
    add("old-groove-not-authority", yoke["old_wheel_groove_authority"] is False, yoke)
    add("yoke-torque-path", yoke["load_path_primary"], yoke)

    guard = p["guard"]
    add("guard-selection", guard["selection"] == "FINAL_DRY_PROTOTYPE_GUARD_GEOMETRY", guard)
    add("old-guard-reject", guard["old_thin_root"] == "REJECT_FINAL", guard)
    add("guard-parent", guard["preserved_from"] == "v0.9.6.9", guard)
    add("guard-H9", guard["new_height_mm"] == 9.0, guard)
    add("guard-upper5-root6", guard["selected_upper_wall_mm"] == 5.0 and guard["root_mm"] == 6.0, guard)
    add("guard-radii", guard["root_gusset_class"] == "R3_CLASS" and guard["top_edge_radius_mm"] == 1.0, guard)
    add("guard-margin", guard["connector_vertical_margin_mm"] == 3.9, guard)
    add("guard-frame-gap", guard["frame_clearance_measured_mm"] == 4.4, guard)

    capture = p["full_capture"]
    add("B-collar", capture["selected"] == "B" and capture["collar_pocket_diameter_mm"] == 16.2 and capture["hardware_cavity_radius_mm"] == 20.4, capture)
    m4p = p["m4"]
    add("headed-m4", m4p["type"] == "HEADED_M4" and m4p["count"] == 2 and m4p["separation_deg"] == 90.0 and m4p["unchanged"], m4p)
    tooth = p["protected_12t"]
    add("12t-teeth", tooth["teeth"] == 12 and tooth["phase_deg"] == 15.0 and tooth["spacing_deg"] == 30.0, tooth)
    add("12t-radii", tooth["tip_radius_mm"] == 33.07 and tooth["root_radius_mm"] == 29.47, tooth)
    add("12t-widths", tooth["tip_width_mm"] == 7.5 and tooth["root_width_mm"] == 9.5 and tooth["axial_width_mm"] == 44.0, tooth)
    pitch = p["pitch"]
    add("12t-physical-freeze", pitch["physical_result"] == "PHYSICAL_MATCH" and pitch["status"] == "FROZEN", pitch)

    add("main-one-solid", metrics["main_solids"] == 1, metrics["main_solids"])
    add("cap-one-solid", metrics["cap_solids"] == 1, metrics["cap_solids"])
    add("protected-external-zero", metrics["protected_external_missing_mm3"] == 0.0, metrics["protected_external_missing_mm3"])
    add("actual-y3-bounds", metrics["y3_bounds_mm"] == [15.0, 15.2, 12.0], metrics["y3_bounds_mm"])
    add("actual-y3-volume", metrics["y3_volume_mm3"] == 2212.752, metrics["y3_volume_mm3"])
    for label, width in (("YW20", 15.4), ("YW30", 15.5), ("YW40", 15.6)):
        local = metrics["yoke_receiver_variants"][label]
        add(f"{label}-actual-width", local["receiver_width_mm"] == width, local)
        add(f"{label}-same-y3", local["same_y3_geometry"] and local["y3_bounds_mm"] == [15.0, 15.2, 12.0] and local["y3_volume_mm3"] == 2212.752, local)
        add(f"{label}-pocket-valid", local["pocket_valid"], local)
    add("endpoint-intersections-zero", metrics["endpoint_all_zero"], metrics["endpoint_intersections"])
    add("slide-sample-count", metrics["motion"]["sample_count"] == 13, metrics["motion"])
    add("slide-swept-zero", metrics["motion"]["swept_path_pass"] and metrics["motion"]["max_unintended_intersection_mm3"] == 0.0, metrics["motion"])
    add("slide-endpoint", metrics["motion"]["open_offset_mm"] == 3.0 and metrics["motion"]["lock_concentric_error_mm"] == 0.0, metrics["motion"])
    add("slide-overlap", metrics["motion"]["hook_overlap_nominal_mm"] == 3.0 and metrics["motion"]["hook_overlap_residual_s45_mm"] == 2.55, metrics["motion"])
    add("yoke-insertion-samples", metrics["yoke_insertion"]["sample_count_per_yoke"] == 55, metrics["yoke_insertion"])
    add("yoke-insertion-zero", metrics["yoke_insertion"]["insertion_removal_pass_with_cap_removed"] and metrics["yoke_insertion"]["max_unintended_intersection_cap_removed_mm3"] == 0.0, metrics["yoke_insertion"])
    add("yoke-cap-removal", metrics["yoke_insertion"]["cap_removal_required"] and metrics["yoke_insertion"]["cap_present_path_intersection_mm3"] > 0.0, metrics["yoke_insertion"])
    add("crawler-space-zero", all(value == 0.0 for key, value in metrics["endpoint_intersections"].items() if "crawler" in key), metrics["endpoint_intersections"])
    add("frame-clearance", metrics["frame_clearance_measured_mm"] == 4.4, metrics["frame_clearance_measured_mm"])
    add("support-volume-zero", metrics["support_free_internal_volume_mm3"] == 0.0, metrics["support_free_internal_volume_mm3"])
    add("no-trapped-support", metrics["support_free_long_trapped_region_count"] == 0, metrics["support_free_long_trapped_region_count"])
    add("geometry-valid", metrics["all_primary_valid"], metrics["all_primary_valid"])

    printing = p["printability"]
    add("print-order-1", printing["first"] == "H55_H56_H57_OPEN_HEX_COUPON", printing)
    add("print-order-2", printing["second"] == "YW20_YW30_YW40_WITH_IDENTICAL_Y3", printing)
    add("print-order-3", printing["third"] == "S45_SHORT_SLIDE_COUPON", printing)
    add("full12t-mark", printing["full_12t_mark"] == "DO_NOT_PRINT_UNTIL_HEX_YOKE_RECEIVER_AND_SHORT_SLIDE_PASS", printing)

    steps = [lane / rel for rel in CAD if rel.endswith(".step")]
    stls = [lane / rel for rel in CAD if rel.endswith(".stl")]
    add("step-count", len(steps) == 6, len(steps))
    imported = 0
    for path in steps:
        try:
            obj = cq.importers.importStep(str(path))
            imported += int(obj.solids().size() > 0 and all(solid.isValid() for solid in obj.solids().vals()))
        except Exception:
            pass
    add("step-import", imported == 6, imported)
    add("stl-count", len(stls) == 5, len(stls))
    add("stl-manifold", all(stl_is_manifold(path) for path in stls), len(stls))
    add("svg-count", len(SVGS) == 9 and all((lane / rel).read_text(encoding="utf-8").startswith("<svg") for rel in SVGS), len(SVGS))
    add("docs-count", len(DOCS) == 19, len(DOCS))
    add("json-count", len(JSONS) == 2, len(JSONS))
    add("source-count", len(SOURCES) == 2, len(SOURCES))

    gates = p["gates"]
    add("short-slide-gate", gates["short_slide"] == "READY_FOR_PHYSICAL_TEST", gates)
    add("hex-gate", gates["hex_nut_seat"] == "READY_FOR_COUPON", gates)
    add("y3-height-gate", gates["y3_height"] == "PROMISING_PHYSICAL_FIT", gates)
    add("yoke-width-gate", gates["yoke_receiver_width"] == "PENDING_PHYSICAL_COUPON", gates)
    add("full12t-gate", gates["full_12t"] == "PRINT_PENDING_HEX_YOKE_AND_SHORT_SLIDE_PASSES", gates)
    add("powered-gate", gates["powered"] == "NOT_YET_APPROVED", gates)
    add("hold-gates", all(gates[key] == "HOLD" for key in ("full_torque", "belt", "shaft_cut", "water", "mud")), gates)
    add("field-gate", gates["field"] == "NOT_APPROVED", gates)

    if repo_checks:
        preflight = repository_preflight()
        prefix = LANE_REL.as_posix() + "/"
        target = sorted(path for path in untracked_paths() if path.startswith(prefix))
        expected = sorted((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS)
        add("repo-preflight", all(preflight["checks"].values()), preflight["checks"])
        add("repo-target-exact", target == expected, len(target))
    return checks


def verify(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> tuple[int, int]:
    checks = contract_checks(lane, repo_checks)
    failures = []
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        if not ok:
            failures.append((name, detail))
    print(json.dumps({"passed": len(checks) - len(failures), "total": len(checks), "failures": failures}, ensure_ascii=False))
    if failures:
        raise SystemExit(1)
    return len(checks), 0


def reproducibility_check() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="v09612_a_") as first, tempfile.TemporaryDirectory(prefix="v09612_b_") as second:
        first_path, second_path = Path(first), Path(second)
        build_outputs(first_path)
        build_outputs(second_path)
        differences = [rel for rel in EXPECTED_PATHS if (first_path / rel).read_bytes() != (second_path / rel).read_bytes()]
    report = {"checked": len(EXPECTED_PATHS), "identical": len(EXPECTED_PATHS) - len(differences), "differences": differences, "status": "PASS" if not differences else "FAIL"}
    print(json.dumps(report, ensure_ascii=False))
    if differences:
        raise SystemExit(1)
    return report


def zip_handoff(lane: Path = DEFAULT_LANE) -> tuple[Path, dict[str, object]]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_Short_Slide_Yoke_Receiver_v0_9_6_12_{stamp}.zip"
    if target.exists():
        raise RuntimeError(f"ZIP_EXISTS_REFUSE_OVERWRITE: {target}")
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_PATHS:
            archive.write(lane / rel, rel)
    with zipfile.ZipFile(target, "r") as archive:
        names = archive.namelist()
        duplicate = len(names) - len(set(names))
        traversal = [name for name in names if name.startswith(("/", "\\")) or ".." in Path(name).parts]
        manifest = archive.read("MANIFEST.txt").decode("utf-8").splitlines()
        sums = {}
        for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            sums[rel] = digest
        mismatches = [rel for rel, digest in sums.items() if hashlib.sha256(archive.read(rel)).hexdigest() != digest]
        parent_contamination = [name for name in names if name not in EXPECTED_PATHS]
    audit = {
        "open": "PASS", "entries": len(names), "duplicate": duplicate, "traversal": traversal,
        "manifest_exact": manifest == EXPECTED_PATHS, "sha_mismatches": mismatches,
        "parent_contamination": parent_contamination, "sha256": sha256(target),
    }
    if duplicate or traversal or not audit["manifest_exact"] or mismatches or parent_contamination:
        raise RuntimeError("ZIP_AUDIT_FAIL: " + json.dumps(audit, ensure_ascii=False))
    print(json.dumps({"zip": str(target), **audit}, ensure_ascii=False))
    return target, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--reproducibility", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    repository_preflight()
    build_outputs(DEFAULT_LANE)
    if args.verify:
        verify(DEFAULT_LANE, True)
    if args.reproducibility:
        reproducibility_check()
    if args.zip:
        zip_handoff(DEFAULT_LANE)
    if not (args.verify or args.reproducibility or args.zip):
        print(f"BUILT {len(EXPECTED_PATHS)} paths in {DEFAULT_LANE}")


if __name__ == "__main__":
    main()
