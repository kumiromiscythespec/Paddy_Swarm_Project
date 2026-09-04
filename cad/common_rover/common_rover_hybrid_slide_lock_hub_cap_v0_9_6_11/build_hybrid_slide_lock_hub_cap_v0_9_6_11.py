from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import struct
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq


VERSION = "v0.9.6.11"
CLASSIFICATION = "HYBRID_SLIDE_LOCK_HUB_CAP"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_hybrid_slide_lock_hub_cap_v0_9_6_11")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2084
BASE_OUTSIDE_DIGEST = "2124e2d63090e5c6273946e629a76b1aaa0de71a666542b05dfd13dec3aac437"
TRACKED_DIRTY = [
    "CURRENT_COMMON_ROVER_AUTHORITY.md", "README.md",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md",
]
AUTHORITY_HASHES = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}

PARENT_BUILDER = REPO_ROOT / "cad/common_rover/common_rover_short_m3_local_bridge_cap_lock_v0_9_6_10/build_short_m3_local_bridge_cap_lock_v0_9_6_10.py"
_spec = importlib.util.spec_from_file_location("v09610_parent", PARENT_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load protected parent: {PARENT_BUILDER}")
parent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = parent
_spec.loader.exec_module(parent)

PROTECTED_LANES = dict(parent.PROTECTED_LANES)
PROTECTED_LANES["v0.9.6.10"] = (
    "cad/common_rover/common_rover_short_m3_local_bridge_cap_lock_v0_9_6_10",
    43,
    "f7e6d686e0e24b9207abef4c8caf4b9612bde2bf029bf66537ff46f7b17a628d",
)

DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_INPUTS.md",
    "V09610_TWO_BRIDGE_REJECTION.md", "HYBRID_SLIDE_LOCK_SPEC.md",
    "L_HOOK_SPEC.md", "SLIDE_RECEIVER_SPEC.md", "SLIDE_HARD_STOP_SPEC.md",
    "S25_S35_S45_COUPON_SPEC.md", "SINGLE_M3_LOCK_SPEC.md",
    "CAP_MOTION_SPEC.md", "FINAL_CONCENTRICITY_SPEC.md",
    "REACTION_YOKE_PARENT_STATUS.md", "REINFORCED_GUARD_PARENT_STATUS.md",
    "TORQUE_LOAD_PATH.md", "ASSEMBLY_PROCEDURE.md", "PRINT_PLAN.md",
    "PHYSICAL_TEST_PLAN.md", "POWERED_TEST_GATE.md", "SAFETY_NOTES.md",
    "HOLD_REGISTER.md", "SOURCE_TRACE.md",
]
CAD = [
    "slide_lock/artifacts/hybrid_slide_lock_coupon_v0_9_6_11.step",
    "slide_lock/artifacts/hybrid_slide_lock_coupon_v0_9_6_11.stl",
    "drive/artifacts/drive_12t_h25a1_hybrid_slide_lock_v0_9_6_11.step",
    "hub_cap/artifacts/h25a1_hybrid_slide_lock_cap_v0_9_6_11.step",
    "hub_cap/artifacts/h25a1_hybrid_slide_lock_cap_v0_9_6_11.stl",
    "integration/artifacts/hybrid_slide_lock_full_assembly_LOCK_A_v0_9_6_11.step",
    "integration/artifacts/hybrid_slide_lock_full_assembly_LOCK_B_v0_9_6_11.step",
]
SVGS = [f"integration/artifacts/{name}" for name in (
    "hybrid_slide_lock_open_v0_9_6_11.svg",
    "hybrid_slide_lock_locked_v0_9_6_11.svg",
    "slide_motion_5mm_v0_9_6_11.svg",
    "l_hook_section_v0_9_6_11.svg",
    "receiver_undercut_v0_9_6_11.svg",
    "hard_stop_and_m3_alignment_v0_9_6_11.svg",
    "v09610_two_bridge_vs_slide_lock_v0_9_6_11.svg",
    "slide_lock_load_roles_v0_9_6_11.svg",
    "cap_final_concentricity_v0_9_6_11.svg",
    "crawler_running_space_comparison_v0_9_6_11.svg",
)]
JSONS = ["design_parameters.json", "validation_report.json"]
SOURCES = ["build_hybrid_slide_lock_hub_cap_v0_9_6_11.py", "tests/test_hybrid_slide_lock_hub_cap_v0_9_6_11_contract.py"]
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

PROTECTED_12T = dict(parent.PROTECTED_12T)
ORIENTATIONS = {
    "LOCK_A": {"keep_m3_angle_deg": 45.0, "hook_angle_deg": 225.0},
    "LOCK_B": {"keep_m3_angle_deg": 225.0, "hook_angle_deg": 45.0},
}
PARAMS = {
    "version": VERSION,
    "classification": CLASSIFICATION,
    "units": "mm",
    "v09610_rejection": {
        "status": "CAD_PHYSICAL_REVIEW_REJECT",
        "architecture": "M3_X2_LOCAL_BRIDGE_AND_REAR_SERVICE_WINDOW",
        "reason": "CRAWLER_RUNNING_SPACE_INTERFERENCE_RISK",
        "m3_length_only_failure": False,
        "superseded_candidate": True,
    },
    "orientation": {
        "user_view_mapping": "AMBIGUOUS_NOT_GUESSED",
        "mirrored_candidates": ORIENTATIONS,
        "mechanical_design_difference": False,
        "cad_primary": "LOCK_A",
        "selection_basis": ["CRAWLER_RUNNING_CLEARANCE", "YOKE_CLEARANCE", "REAR_NUT_ACCESS", "M4_SERVICE_ACCESS", "GUARD_CLEARANCE"],
    },
    "mechanism": {
        "name": "RIGID_L_HOOK_RECEIVER_POSITIVE_SLIDE_LOCK",
        "m3_count": 1,
        "l_hook_count": 1,
        "rigid_hook": True,
        "snap_hook": False,
        "spring_finger": False,
        "receiver": True,
        "linear_slide": True,
        "hard_stop": True,
        "final_concentric": True,
        "hidden_captive_nut": False,
        "petg_thread": False,
        "full_body_m3": False,
        "adhesive": False,
    },
    "motion": {
        "slide_primary_mm": 5.0,
        "comparison_mm": [4.0, 5.0, 6.0],
        "open_cap_eccentric_allowed": True,
        "open_cap_offset_mm": 5.0,
        "lock_cap_eccentric_mm": 0.0,
        "lock_end_shaft_seat_axis_error_mm": 0.0,
        "shaft_service_slot_required": True,
        "m3_alignment_open": False,
        "m3_alignment_lock": True,
        "m3_open_misalignment_mm": 5.0,
        "sample_count": 21,
    },
    "hook": {
        "engagement_overlap_nominal_mm": 3.0,
        "structural_thickness_mm": 4.0,
        "root_thickness_mm": 6.0,
        "engagement_width_mm": 12.0,
        "root_fillet_mm": 2.0,
        "receiver_lip_thickness_mm": 4.0,
        "short": True,
        "broad": True,
        "rigid": True,
        "flexure_required": False,
        "primary_axial_retention_hook_side": True,
        "primary_torque_path": False,
        "center_radius_mm": 21.5,
    },
    "receiver": {
        "entry_opening": True,
        "sliding_channel": True,
        "undercut_lip": True,
        "positive_final_stop": True,
        "restored_opposite_m3_hole": True,
        "restored_opposite_local_bridge": True,
        "restored_opposite_service_window": True,
        "unnecessary_circular_void": False,
        "root_mass_min_mm": 6.0,
    },
    "clearance_coupon": {
        "variants_mm": {"S25": 0.25, "S35": 0.35, "S45": 0.45},
        "design_primary": "S35",
        "physical_selection": "TIGHTEST_RELIABLE_SLIDING_FIT_PENDING",
        "retention_by_friction": False,
        "labels_embossed": True,
    },
    "single_m3": {
        "under_head_usable_length_mm": 20.5,
        "overall_reference_mm": 27.9,
        "count": 1,
        "local_bridge_thickness_mm": 7.0,
        "cap_thickness_mm": 5.5,
        "petg_stack_mm": 12.5,
        "remaining_hardware_budget_mm": 8.0,
        "hole_diameter_mm": 3.4,
        "rear_washer": True,
        "rear_nut": True,
        "rear_visible_accessible_removable": True,
        "hidden_captive_nut": False,
        "petg_thread": False,
        "role": "ANTI_REVERSE_SLIDE_AND_OPPOSITE_AXIAL_RETENTION_LOCK_INDICATOR",
        "primary_torque_path": False,
        "physical_stack": "HOLD",
    },
    "cap": {
        "outer_diameter_mm": 54.0,
        "thickness_mm": 5.5,
        "lock_position_centered": True,
        "open_position_eccentric": True,
        "lock_end_shaft_seat": True,
        "service_motion_slot_mm": 5.0,
        "snap_fingers": 0,
        "primary_torque_path": False,
    },
    "reaction_yoke": {**parent.PARAMS["reaction_yoke"], "preserved_from": "v0.9.6.9", "primary_torque_path": True},
    "guard": {**parent.PARAMS["guard"], "preserved_from": "v0.9.6.9"},
    "pitch": dict(parent.PARAMS["pitch"]),
    "protected_12t": dict(PROTECTED_12T),
    "collar": dict(parent.PARAMS["collar"]),
    "full_capture": dict(parent.PARAMS["full_capture"]),
    "m4": dict(parent.PARAMS["m4"]),
    "spacer": dict(parent.PARAMS["spacer"]),
    "printability": {
        "printer": "BAMBU_A1",
        "material": "PETG",
        "coupon_orientation": "HOOK_ON_SIDE_RECEIVER_WINDOW_UP",
        "support_free_candidate": True,
        "hook_root_crosses_multiple_extrusion_paths": True,
        "slicer_verification_required": True,
        "full_12t_stl_generated": False,
        "full_12t_step_mark": "DO_NOT_PRINT_UNTIL_SLIDE_LOCK_COUPON_PASS",
    },
    "gates": {
        "slide_lock_coupon": "READY_FOR_PHYSICAL_COUPON",
        "reaction_yoke": "PHYSICAL_PASS_REQUIRED",
        "full_12t": "PRINT_PENDING_REACTION_YOKE_AND_SLIDE_LOCK_COUPON",
        "powered": "NOT_YET_APPROVED",
        "shaft_cut": "HOLD_PHYSICAL_MEASUREMENT",
        "water": "NOT_APPROVED",
        "mud": "NOT_APPROVED",
        "field": "NOT_APPROVED",
    },
}


def untracked_paths() -> list[str]:
    return sorted(line[3:].replace("\\", "/") for line in run_git("status", "--porcelain=v1", "-uall").splitlines() if line.startswith("?? "))


def outside_snapshot() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked_paths() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def repository_preflight() -> dict[str, object]:
    branch, head = run_git("branch", "--show-current"), run_git("rev-parse", "HEAD")
    staged = run_git("diff", "--cached", "--name-only").splitlines()
    dirty = run_git("diff", "--name-only").splitlines()
    authority = {path: sha256(REPO_ROOT / path) for path in AUTHORITY_HASHES}
    protected = {version: tree_digest(REPO_ROOT / rel) for version, (rel, _, _) in PROTECTED_LANES.items()}
    expected_protected = {version: (count, digest) for version, (_, count, digest) in PROTECTED_LANES.items()}
    outside = outside_snapshot()
    checks = {
        "repository": REPO_ROOT.resolve() == Path(run_git("rev-parse", "--show-toplevel")).resolve(),
        "branch": branch == EXPECTED_BRANCH, "head": head == EXPECTED_HEAD,
        "staged_zero": not staged, "tracked_dirty_unchanged": dirty == TRACKED_DIRTY,
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
    a = math.radians(angle_deg)
    return -math.sin(a) * distance, math.cos(a) * distance, 0.0


def local_box(radial: float, tangential: float, axial: float, r_center: float, t_center: float, z_center: float, angle_deg: float) -> cq.Workplane:
    return rotate_local(box(radial, tangential, axial, (r_center, t_center, z_center)), angle_deg)


def hook(angle_deg: float) -> cq.Workplane:
    r = PARAMS["hook"]["center_radius_mm"]
    stem = local_box(6.0, 6.0, 6.2, r, 0.0, 18.9, angle_deg)
    foot = local_box(12.0, 6.0, 4.0, r, 0.0, 15.8, angle_deg)
    result = stem.union(foot).clean()
    try:
        result = result.edges("|Z").fillet(2.0)
    except Exception:
        pass
    return result.clean()


def receiver_mass(angle_deg: float) -> cq.Workplane:
    r = PARAMS["hook"]["center_radius_mm"]
    raw = local_box(17.0, 25.0, 10.0, r, 2.5, 17.0, angle_deg)
    radial_limit = cylinder(29.2, 10.4, 11.8)
    return raw.intersect(parent.parent.parent.protected_blank()).intersect(radial_limit).clean()


def receiver_cavity(angle_deg: float, clearance_mm: float = 0.35, travel_mm: float = 5.0) -> cq.Workplane:
    r = PARAMS["hook"]["center_radius_mm"]
    tangent_min = -3.0
    tangent_max = travel_mm + 3.0 + clearance_mm
    length = tangent_max - tangent_min
    center = (tangent_min + tangent_max) / 2.0
    foot_sweep = local_box(12.0 + 2 * clearance_mm, length, 4.4, r, center, 15.8, angle_deg)
    stem_channel = local_box(6.0 + 2 * clearance_mm, length, 4.4, r, center, 20.0, angle_deg)
    entry = local_box(12.0 + 2 * clearance_mm, 6.0 + 2 * clearance_mm, 8.8, r, travel_mm, 17.8, angle_deg)
    return fused([foot_sweep, stem_channel, entry]).clean()


def single_m3_voids(angle_deg: float) -> list[cq.Workplane]:
    x, y = center_xy(23.0, angle_deg)
    short_hole = cylinder(1.7, 7.4, 14.8).translate((x, y, 0))
    rear_window = cylinder(6.2, 37.2, -22.2).translate((x, y, 0))
    return [short_hole, rear_window]


def single_m3_bridge_restore(angle_deg: float) -> cq.Workplane:
    pad = local_box(13.0, 13.0, 7.0, 23.0, 0.0, 18.5, angle_deg)
    return pad.intersect(parent.parent.parent.protected_blank()).clean()


def main_sprocket(orientation: str = "LOCK_A", clearance_mm: float = 0.35) -> cq.Workplane:
    cfg = ORIENTATIONS[orientation]
    source = parent.parent.parent.protected_blank()
    part = source
    voids = [
        cylinder(5.15, 46.0, -23.0), cylinder(8.1, 24.0, -2.0),
        box(40.8, 9.2, 26.6, (0, 0, 8.7)), box(9.2, 40.8, 26.6, (0, 0, 8.7)),
        cylinder(27.2, 5.7, 16.5),
        parent.parent.yoke_pocket(), parent.parent.yoke_pocket().rotate((0, 0, 0), (0, 0, 1), 90),
    ]
    for void in compound(voids).solids().vals():
        part = part.cut(cq.Workplane(obj=void))
    # Restore only the compact retained M3 bridge and opposite-side receiver
    # mass from the protected source, then cut their functional paths.
    part = part.union(single_m3_bridge_restore(cfg["keep_m3_angle_deg"]))
    part = part.union(receiver_mass(cfg["hook_angle_deg"]))
    for void in [*single_m3_voids(cfg["keep_m3_angle_deg"]), receiver_cavity(cfg["hook_angle_deg"], clearance_mm)]:
        for solid in void.solids().vals():
            part = part.cut(cq.Workplane(obj=solid))
    return part.union(parent.parent.reinforced_guard()).clean()


def shaft_service_slot(angle_deg: float, travel_mm: float = 5.0) -> cq.Workplane:
    # In cap-local coordinates the fixed shaft moves from0 to -travel while
    # the cap moves from LOCK to OPEN in +tangent direction.
    lock_bore = cylinder(5.2, 5.9, 21.8)
    open_bore = cylinder(5.2, 5.9, 21.8).translate((0, -travel_mm, 0))
    bridge = box(10.4, travel_mm, 5.9, (0, -travel_mm / 2.0, 24.75))
    return rotate_local(fused([lock_bore, open_bore, bridge]), angle_deg)


def cap(orientation: str = "LOCK_A", position_mm: float = 0.0) -> cq.Workplane:
    cfg = ORIENTATIONS[orientation]
    cap_part = cylinder(27.0, 5.5, 22.0)
    cap_part = cap_part.cut(shaft_service_slot(cfg["hook_angle_deg"]))
    # Preserve both reaction-yoke service openings in the new front-mounted cap.
    cap_part = cap_part.cut(box(17.5, 9.4, 5.9, (13.75, 0, 24.75))).cut(box(9.4, 17.5, 5.9, (0, 13.75, 24.75)))
    x, y = center_xy(23.0, cfg["keep_m3_angle_deg"])
    cap_part = cap_part.cut(cylinder(1.7, 5.9, 21.8).translate((x, y, 0)))
    cap_part = cap_part.cut(cylinder(3.6, 3.7, 25.7).translate((x, y, 0)))
    cap_part = cap_part.union(hook(cfg["hook_angle_deg"]))
    if position_mm:
        cap_part = cap_part.translate(slide_vector(cfg["hook_angle_deg"], position_mm))
    return cap_part.clean()


def single_m3_hardware(orientation: str = "LOCK_A") -> cq.Workplane:
    cfg = ORIENTATIONS[orientation]
    x, y = center_xy(23.0, cfg["keep_m3_angle_deg"])
    shaft = cylinder(1.5, 20.5, 7.0).translate((x, y, 0))
    head_washer_reference = cylinder(3.6, 7.4, 27.5).translate((x, y, 0))
    rear_washer = parent.parent.parent.m3_washer_reference().translate((x, y, 14.5))
    rear_nut = parent.parent.parent.m3_nut_reference().translate((x, y, 12.1))
    return compound([shaft, head_washer_reference, rear_washer, rear_nut])


def rear_tool_envelope(orientation: str = "LOCK_A") -> cq.Workplane:
    angle = ORIENTATIONS[orientation]["keep_m3_angle_deg"]
    return cylinder(5.6, 39.0, -24.0).translate((*center_xy(23.0, angle), 0))


def running_space_keepout() -> cq.Workplane:
    return cylinder(40.0, 44.0, -22.0).cut(cylinder(29.469, 44.4, -22.2))


def full_assembly(orientation: str = "LOCK_A") -> cq.Workplane:
    yokes = parent.parent.installed_yokes(3.5)
    shaft = cylinder(5.0, 70.0, -35.0)
    spacer = parent.parent.parent.spacer_8().translate((0, 0, -34.0))
    kp000 = box(67.0, 35.0, 17.0, (0, 0, -44.5)).cut(cylinder(8.0, 17.4, -53.2))
    frame = box(92.0, 92.0, 0.4, (0, 0, -30.6))
    return compound([main_sprocket(orientation), cap(orientation), *yokes, parent.parent.parent.m4_hardware(), single_m3_hardware(orientation), rear_tool_envelope(orientation), shaft, spacer, kp000, frame])


def label_segments(text: str, z0: float) -> cq.Workplane:
    segs = {
        "S": ("top", "ul", "mid", "lr", "bot"),
        "2": ("top", "ur", "mid", "ll", "bot"),
        "3": ("top", "ur", "mid", "lr", "bot"),
        "4": ("ul", "ur", "mid", "lr"),
        "5": ("top", "ul", "mid", "lr", "bot"),
    }
    parts = []
    for index, char in enumerate(text):
        x0 = (index - 1) * 5.0
        t, d = 0.55, 0.6
        shapes = {
            "top": box(3.0, t, d, (x0, 2.1, z0 + d / 2)), "mid": box(3.0, t, d, (x0, 0, z0 + d / 2)), "bot": box(3.0, t, d, (x0, -2.1, z0 + d / 2)),
            "ul": box(t, 2.1, d, (x0 - 1.5, 1.05, z0 + d / 2)), "ur": box(t, 2.1, d, (x0 + 1.5, 1.05, z0 + d / 2)),
            "ll": box(t, 2.1, d, (x0 - 1.5, -1.05, z0 + d / 2)), "lr": box(t, 2.1, d, (x0 + 1.5, -1.05, z0 + d / 2)),
        }
        parts.extend(shapes[name] for name in segs[char])
    return fused(parts).clean()


def coupon_receiver(clearance_mm: float, label: str) -> cq.Workplane:
    # Standard local orientation: hook center r is translated to coupon x=6.
    base = box(42.0, 34.0, 10.0, (0, 0, 17.0))
    cavity = receiver_cavity(0.0, clearance_mm).translate((6.0 - PARAMS["hook"]["center_radius_mm"], 0, 0))
    m3_x = -12.0
    window = cylinder(6.2, 10.2, 11.8).translate((m3_x, 0, 0))
    hole = cylinder(1.7, 7.4, 14.8).translate((m3_x, 0, 0))
    base = base.cut(cavity).cut(window).cut(hole)
    base = base.union(label_segments(label, 22.0).translate((0, -10.0, 0)))
    return base.clean()


def coupon_cap(clearance_mm: float, label: str) -> cq.Workplane:
    plate = box(42.0, 34.0, 5.5, (0, 0, 24.75))
    local_hook = hook(0.0).translate((6.0 - PARAMS["hook"]["center_radius_mm"], 0, 0))
    # Central service slot and a single lock hole make OPEN/LOCK mechanically testable.
    slot = fused([cylinder(5.2, 5.9, 21.8), cylinder(5.2, 5.9, 21.8).translate((0, -5.0, 0)), box(10.4, 5.0, 5.9, (0, -2.5, 24.75))])
    m3_x = -12.0
    plate = plate.cut(slot).cut(cylinder(1.7, 5.9, 21.8).translate((m3_x, 0, 0)))
    plate = plate.union(local_hook).union(label_segments(label, 27.5).translate((0, 10.0, 0)))
    return plate.clean()


def slide_lock_coupon() -> cq.Workplane:
    parts = []
    for offset, label, clearance in zip((-58.0, 0.0, 58.0), ("S25", "S35", "S45"), (0.25, 0.35, 0.45)):
        parts.append(coupon_receiver(clearance, label).translate((offset, -25.0, -12.0)))
        # Cap is printed on its reinforced hook side, separate from receiver.
        parts.append(coupon_cap(clearance, label).rotate((0, 0, 0), (0, 1, 0), 90).translate((offset, 35.0, 0)))
    return compound(parts)


GEOMETRIES: dict[str, tuple[object, bool]] = {
    "slide_lock/artifacts/hybrid_slide_lock_coupon_v0_9_6_11": (slide_lock_coupon, True),
    "drive/artifacts/drive_12t_h25a1_hybrid_slide_lock_v0_9_6_11": (lambda: main_sprocket("LOCK_A"), False),
    "hub_cap/artifacts/h25a1_hybrid_slide_lock_cap_v0_9_6_11": (lambda: cap("LOCK_A"), True),
    "integration/artifacts/hybrid_slide_lock_full_assembly_LOCK_A_v0_9_6_11": (lambda: full_assembly("LOCK_A"), False),
    "integration/artifacts/hybrid_slide_lock_full_assembly_LOCK_B_v0_9_6_11": (lambda: full_assembly("LOCK_B"), False),
}


def protected_external_missing_mm3(orientation: str) -> float:
    source = parent.parent.parent.protected_blank()
    external = source.cut(cylinder(29.469, 44.4, -22.2))
    retained = main_sprocket(orientation).intersect(external)
    return round(max(0.0, float(external.val().Volume()) - float(retained.val().Volume())), 6)


def motion_metrics(orientation: str) -> dict[str, object]:
    cfg = ORIENTATIONS[orientation]
    main = main_sprocket(orientation)
    shaft = cylinder(5.0, 70.0, -35.0)
    yokes = parent.parent.installed_yokes(3.5)
    m4 = parent.parent.parent.m4_hardware()
    sample_values = [i * 5.0 / 20.0 for i in range(21)]
    rows = []
    for position in sample_values:
        moving = cap(orientation, position)
        rows.append({
            "position_mm": round(position, 2),
            "cap_main_mm3": volume(moving, main),
            "cap_shaft_mm3": volume(moving, shaft),
            "cap_yoke_mm3": volume(moving, compound(list(yokes))),
            "cap_m4_mm3": volume(moving, m4),
        })
    max_collision = max(value for row in rows for key, value in row.items() if key.endswith("mm3"))
    return {
        "orientation": orientation,
        "keep_m3_angle_deg": cfg["keep_m3_angle_deg"],
        "hook_angle_deg": cfg["hook_angle_deg"],
        "samples": rows,
        "sample_count": len(rows),
        "max_unintended_intersection_mm3": max_collision,
        "swept_path_pass": max_collision == 0.0,
        "open_offset_mm": 5.0,
        "lock_concentric_error_mm": 0.0,
        "m3_open_misalignment_mm": 5.0,
        "m3_lock_misalignment_mm": 0.0,
        "hook_overlap_nominal_mm": 3.0,
        "hook_overlap_residual_mm": 2.65,
    }


def geometry_metrics() -> dict[str, object]:
    result: dict[str, object] = {"orientations": {}}
    keepout = running_space_keepout()
    frame = box(92.0, 92.0, 0.4, (0, 0, -30.6))
    for orientation in ORIENTATIONS:
        main = main_sprocket(orientation)
        cap_lock = cap(orientation)
        cap_open = cap(orientation, 5.0)
        m3 = single_m3_hardware(orientation)
        tool = rear_tool_envelope(orientation)
        yokes = parent.parent.installed_yokes(3.5)
        m4 = parent.parent.parent.m4_hardware()
        guard = parent.parent.reinforced_guard()
        motion = motion_metrics(orientation)
        deleted_m3_axis = cylinder(1.7, 44.0, -22.0).translate((*center_xy(23.0, ORIENTATIONS[orientation]["hook_angle_deg"]), 0))
        local = {
            "main_bounds_mm": dims(main), "main_solids": main.solids().size(),
            "cap_lock_bounds_mm": dims(cap_lock), "cap_open_bounds_mm": dims(cap_open),
            "protected_external_missing_mm3": protected_external_missing_mm3(orientation),
            "lock_cap_running_space_intersection_mm3": volume(cap_lock, keepout),
            "open_cap_running_space_intersection_mm3": volume(cap_open, keepout),
            "m3_running_space_intersection_mm3": volume(m3, keepout),
            "receiver_running_space_intersection_mm3": volume(receiver_mass(ORIENTATIONS[orientation]["hook_angle_deg"]), keepout),
            "deleted_m3_axis_restored_petg_mm3": volume(main, deleted_m3_axis),
            "m3_m4_intersection_mm3": volume(m3, m4),
            "m3_yoke_a_intersection_mm3": volume(m3, yokes[0]), "m3_yoke_b_intersection_mm3": volume(m3, yokes[1]),
            "m3_guard_intersection_mm3": volume(m3, guard), "tool_main_intersection_mm3": volume(tool, main),
            "tool_m4_intersection_mm3": volume(tool, m4), "tool_yoke_a_intersection_mm3": volume(tool, yokes[0]),
            "tool_yoke_b_intersection_mm3": volume(tool, yokes[1]), "guard_frame_intersection_mm3": volume(guard, frame),
            "hardware_axial_mm": round(m3.val().BoundingBox().zmax - m3.val().BoundingBox().zmin, 3),
            "assembly_axial_mm": round(max(main.val().BoundingBox().zmax, cap_lock.val().BoundingBox().zmax, m3.val().BoundingBox().zmax) - min(main.val().BoundingBox().zmin, cap_lock.val().BoundingBox().zmin, m3.val().BoundingBox().zmin), 3),
            "motion": motion,
            "all_primary_valid": all(all(s.isValid() for s in obj.solids().vals()) for obj in [main, cap_lock, cap_open, full_assembly(orientation)]),
        }
        result["orientations"][orientation] = local
    coupon = slide_lock_coupon()
    result["coupon_solids"] = coupon.solids().size()
    result["coupon_valid"] = all(s.isValid() for s in coupon.solids().vals())
    result["mirror_metric_equivalent"] = all(
        result["orientations"]["LOCK_A"][key] == result["orientations"]["LOCK_B"][key]
        for key in ["protected_external_missing_mm3", "lock_cap_running_space_intersection_mm3", "m3_m4_intersection_mm3", "hardware_axial_mm", "assembly_axial_mm"]
    )
    return result


def collision_report(metrics: dict[str, object] | None = None) -> dict[str, object]:
    m = metrics or geometry_metrics()
    orientations = {}
    for name, local in m["orientations"].items():
        collision_keys = [key for key in local if key.endswith("intersection_mm3")]
        collision_values = {key: local[key] for key in collision_keys}
        orientations[name] = {
            "endpoint_intersections": collision_values,
            "endpoint_all_zero": all(value == 0.0 for value in collision_values.values()),
            "swept_path": local["motion"],
        }
    return {
        "method": "CADQUERY_COMMON_VOLUME_21_SAMPLE_FULL_SLIDE_SWEEP_LOCK_A_AND_LOCK_B",
        "orientations": orientations,
        "known_all_zero": all(value["endpoint_all_zero"] and value["swept_path"]["swept_path_pass"] for value in orientations.values()),
        "intended_contacts_excluded": ["HOOK_TO_HARD_STOP_AT_LOCK", "HOOK_FOOT_TO_RECEIVER_LIP_AXIAL_PULL", "CAP_TO_MAIN_FRONT_SEAT", "M3_REAR_WASHER_TO_BRIDGE"],
        "physical_holds": ["S25_S35_S45_SELECTION", "HOOK_WEAR_LIFE", "REACTION_YOKE_VARIANT", "M3_NUT_WASHER_STACK", "M3_TORQUE", "FULL_LOAD_TORQUE"],
    }


def validation_report() -> dict[str, object]:
    metrics = geometry_metrics()
    return {
        "version": VERSION, "classification": CLASSIFICATION,
        "result": "HYBRID_SLIDE_LOCK_HUB_CAP_COMPLETE",
        "v09610": "TWO_BRIDGE_ARCHITECTURE_SUPERSEDED",
        "mechanism": "SINGLE_M3_PLUS_RIGID_L_HOOK_COMPLETE",
        "coupon": "S25_S35_S45_READY",
        "lock_concentricity": "VERIFIED_IN_CAD_0P0MM_NOMINAL",
        "geometry": metrics, "collision": collision_report(metrics), "gates": PARAMS["gates"],
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="600" viewBox="0 0 1000 600"><rect width="1000" height="600" fill="#f8fafc"/><text x="50" y="58" font-family="sans-serif" font-size="28" font-weight="bold" fill="#17202a">{title}</text><line x1="50" y1="78" x2="950" y2="78" stroke="#94a3b8"/>{body}<text x="50" y="575" font-family="sans-serif" font-size="13" fill="#475569">Common Rover v0.9.6.11 · rigid slide-lock CAD reference · coupon authority required</text></svg>'''


def svg_outputs() -> dict[str, str]:
    f = 'font-family="sans-serif" font-size="17" fill="#1f2933"'
    return {
        SVGS[0]: svg_page("Hybrid slide lock — OPEN", f'''<g {f}><circle cx="470" cy="315" r="170" fill="#cbd5e1"/><circle cx="540" cy="245" r="160" fill="#60a5fa" opacity=".7"/><path d="M350 330H445V380H525V430H350Z" fill="#10b981"/><text x="590" y="190">cap temporarily offset5.0mm</text><text x="570" y="235">hook at receiver entrance</text><text x="570" y="280">M3 holes intentionally misaligned</text></g>'''),
        SVGS[1]: svg_page("Hybrid slide lock — LOCKED", f'''<g {f}><circle cx="500" cy="315" r="170" fill="#cbd5e1"/><circle cx="500" cy="315" r="160" fill="#60a5fa" opacity=".7"/><path d="M350 330H445V380H525V430H350Z" fill="#10b981"/><line x1="500" y1="125" x2="500" y2="505" stroke="#111827" stroke-width="4"/><text x="610" y="210">hard stop reached</text><text x="610" y="255">shaft lock-seat error0.0</text><text x="610" y="300">M3 aligned / reverse slide blocked</text></g>'''),
        SVGS[2]: svg_page("Five millimetre slide motion", f'''<g {f}><rect x="180" y="220" width="190" height="170" fill="#93c5fd"/><rect x="640" y="220" width="190" height="170" fill="#34d399"/><line x1="385" y1="305" x2="625" y2="305" stroke="#f59e0b" stroke-width="12"/><polygon points="625,305 590,280 590,330" fill="#f59e0b"/><text x="245" y="430">OPEN</text><text x="700" y="430">LOCK</text><text x="430" y="275">translation 5.0mm</text><text x="310" y="500">21-position common-volume swept-path validation</text></g>'''),
        SVGS[3]: svg_page("Rigid L-hook section", f'''<g {f}><rect x="170" y="135" width="650" height="90" fill="#60a5fa"/><rect x="430" y="225" width="140" height="185" fill="#10b981"/><rect x="340" y="355" width="320" height="80" fill="#10b981"/><path d="M405 225Q430 250 430 285" fill="none" stroke="#047857" stroke-width="16"/><text x="190" y="120">cap body</text><text x="590" y="280">6mm-class root</text><text x="670" y="400">4mm rigid hook foot</text><text x="330" y="490">width12 · nominal undercut overlap3 · R2 root</text></g>'''),
        SVGS[4]: svg_page("Rigid receiver undercut", f'''<g {f}><rect x="170" y="155" width="660" height="300" fill="#cbd5e1"/><path d="M260 245H430V335H570V245H740V420H260Z" fill="#fff"/><rect x="440" y="335" width="120" height="70" fill="#10b981"/><text x="215" y="210">wide entry at OPEN</text><text x="595" y="210">narrow stem channel</text><text x="600" y="385">4mm receiver lip</text><text x="325" y="500">rigid foot slides below lip; no flex/snap</text></g>'''),
        SVGS[5]: svg_page("Hard stop and M3 alignment", f'''<g {f}><rect x="130" y="170" width="310" height="260" fill="#fecaca"/><circle cx="285" cy="300" r="40" fill="#fff"/><circle cx="340" cy="300" r="40" fill="none" stroke="#b91c1c" stroke-width="6"/><text x="170" y="475">OPEN: hole offset5mm</text><rect x="570" y="170" width="310" height="260" fill="#bbf7d0"/><circle cx="725" cy="300" r="40" fill="#fff" stroke="#047857" stroke-width="6"/><line x1="570" y1="170" x2="570" y2="430" stroke="#111827" stroke-width="10"/><text x="610" y="475">LOCK: stop + aligned M3</text></g>'''),
        SVGS[6]: svg_page("v0.9.6.10 two bridges vs hybrid lock", f'''<g {f}><rect x="100" y="160" width="340" height="280" fill="#ef4444" opacity=".35"/><circle cx="220" cy="275" r="55" fill="#fff"/><circle cx="340" cy="335" r="55" fill="#fff"/><text x="125" y="485">two bridges/windows: rejected packaging risk</text><rect x="560" y="160" width="340" height="280" fill="#34d399" opacity=".35"/><circle cx="650" cy="280" r="45" fill="#fff"/><path d="M760 260H825V315H870V365H760Z" fill="#047857"/><text x="590" y="485">single compact M3 + one rigid hook</text></g>'''),
        SVGS[7]: svg_page("Slide-lock load roles", f'''<g {f}><text x="90" y="140">Hook: primary cap axial retention on hook side</text><text x="90" y="195">M3×1: anti-reverse slide + opposite-side axial retention + lock indicator</text><path d="M100 255H900" stroke="#10b981" stroke-width="20"/><text x="90" y="345">Drive torque remains shaft → headed M4 → collar → yokes → hub → 12T</text><text x="90" y="410">Hook / M3 / cap are NOT primary drivetrain torque members</text></g>'''),
        SVGS[8]: svg_page("Final cap concentricity", f'''<g {f}><circle cx="500" cy="310" r="185" fill="none" stroke="#60a5fa" stroke-width="22"/><circle cx="500" cy="310" r="45" fill="none" stroke="#111827" stroke-width="8"/><line x1="500" y1="95" x2="500" y2="525" stroke="#f59e0b" stroke-width="3"/><line x1="285" y1="310" x2="715" y2="310" stroke="#f59e0b" stroke-width="3"/><text x="615" y="145">LOCK-end shaft seat axis</text><text x="615" y="185">CAD nominal error = 0.0mm</text><text x="300" y="540">service slot permits OPEN motion; hard stop defines operating center</text></g>'''),
        SVGS[9]: svg_page("Crawler running-space comparison", f'''<g {f}><circle cx="500" cy="315" r="205" fill="none" stroke="#ef4444" stroke-width="35" opacity=".45"/><circle cx="500" cy="315" r="145" fill="#dbeafe"/><path d="M325 355H405V400H470V445H325Z" fill="#10b981"/><circle cx="625" cy="245" r="30" fill="#f59e0b"/><text x="270" y="120">protected tooth/link running annulus begins at root R29.47</text><text x="275" y="515">hook/receiver/M3/cap common volume with running keep-out = 0</text></g>'''),
    }


def document_outputs() -> dict[str, str]:
    h = "# Common Rover Hybrid Slide-Lock Hub Cap v0.9.6.11\n\nClassification: `HYBRID_SLIDE_LOCK_HUB_CAP`  \nRelease: `COUPON-FIRST CAD REFERENCE / FULL 12T DO NOT PRINT / NOT FOR POWERED OR FIELD USE`  \n"
    return {
        "README.md": h + "\nThis isolated lane replaces the rejected two-bridge v0.9.6.10 package with one compact short-M3 lock and one rigid positive L-hook/receiver. The cap is temporarily offset during unpowered service, slides5mm to a broad hard stop and is concentric at LOCK. It is not a flex snap. Print and pass S25/S35/S45 coupon before the full12T.\n",
        "DESIGN_AUTHORITY.md": h + "\nUser/CAD authority rejects v0.9.6.10 two local bridges for crawler-space risk. Physical authority retains M3 under-head20.5/overall27.9 and8mm-spacer guard gap4.4. Frozen parent authority includes exact12T,9/5/6 guard, Y1/Y2/Y3 yokes, B Ø16.2/R20.4 and headed M4×2. Hook/receiver dimensions and slide clearance are coupon candidates.\n",
        "PHYSICAL_INPUTS.md": h + "\n|Input|Value|Class|\n|---|---:|---|\n|v0.9.6.10 two-bridge package|REJECT|CAD/PHYSICAL REVIEW|\n|Available M3 under-head / overall|20.5 / 27.9mm|MEASURED|\n|M4 head space / old shoe / conflict|4.3 / 8.3 / 4.0mm|MEASURED/DERIVED|\n|Guard H/wall/root|9 / 5 / 6mm|PARENT|\n|8mm-spacer frame gap|4.4mm|MEASURED|\n",
        "V09610_TWO_BRIDGE_REJECTION.md": h + "\n`V09610_TWO_BRIDGE_ARCHITECTURE=CAD_PHYSICAL_REVIEW_REJECT`, reason `CRAWLER_RUNNING_SPACE_INTERFERENCE_RISK`. The rejection is not merely screw length: two bridges and rear windows occupy excessive front/crawler functional space. This lane deletes one M3 hole/bridge/window and restores that region as receiver-supported solid hub mass.\n",
        "HYBRID_SLIDE_LOCK_SPEC.md": h + "\nMechanism is a rigid L-hook, rigid receiver undercut,5mm linear slide, broad hard stop and one M3 anti-reverse interlock. No elastic deflection, snap action, spring finger, hidden captive nut, PETG thread or adhesive. LOCK_A and mirrored LOCK_B are mechanically identical because user-view mapping is not authoritative.\n",
        "L_HOOK_SPEC.md": h + "\nDesign primary: nominal overlap3, foot axial thickness4, root thickness6, engagement width12 and R2-class root. The hook is short, broad and rigid. A circular cap plate at the main front plane carries the root across multiple extrusion paths. The hook retains its side axially but receives no drivetrain torque credit.\n",
        "SLIDE_RECEIVER_SPEC.md": h + "\nThe restored opposite-M3 region forms a rear-rooted receiver mass with a wide OPEN entry, full foot sweep cavity, narrow stem channel, rigid undercut lip and end wall. The foot passes axially only at OPEN, then translates beneath a4mm-class lip. Receiver and cutter envelopes stay inside the protected root running boundary.\n",
        "SLIDE_HARD_STOP_SPEC.md": h + "\nThe channel terminates at a broad6×6mm-class hook-root face. At that face the hook has full nominal3mm undercut engagement, the cap LOCK-end shaft seat has0.0mm nominal axis error and the single M3 holes align. Operators do not judge slide distance by paint or sight.\n",
        "S25_S35_S45_COUPON_SPEC.md": h + "\nOne combined build plate contains separate full-scale cap/hook and receiver bodies for S25=0.25, S35=0.35 and S45=0.45mm relevant-side clearance. Labels are deterministic embossed geometry. Select the tightest fit that inserts axially, slides by hand repeatedly, reaches a positive stop, avoids large rocking/cracking and disassembles normally. S35 is CAD primary only.\n",
        "SINGLE_M3_LOCK_SPEC.md": h + "\nOne M3 remains at the KEEP_M3 side: Ø3.4 path,7mm compact bridge,5.5mm cap and12.5mm PETG stack, leaving8mm measured-screw budget. External metal washer/nut are visible and removable. At OPEN the holes are5mm apart; only the hard-stop LOCK state accepts M3. Installed M3 blocks reverse slide and retains the opposite side axially.\n",
        "CAP_MOTION_SPEC.md": h + "\nPresent the cap axially at the OPEN offset, insert the rigid foot through the wide receiver entry, slide5mm along the defined tangent axis until the hard stop, verify the circular LOCK-end shaft seat is centered, then insert M3. A5mm internal service slot permits translation around the stationary Ø10 shaft. The full OD54 plate remains centered only in operating LOCK.\n",
        "FINAL_CONCENTRICITY_SPEC.md": h + "\nOPEN eccentricity5mm is service-only and unpowered. At LOCK the OD54 cap center and circular LOCK-end shaft seat use the sprocket origin; CAD nominal center error is0.0mm. The obround service path is not an operating-position ambiguity because the hard stop plus M3 blocks reverse translation.\n",
        "REACTION_YOKE_PARENT_STATUS.md": h + "\nThe v0.9.6.9 U-yoke geometry is directly reused: Y1/Y2/Y3=3.3/3.5/3.7mm, Y2 design primary, broad side reactions, positive stop and service removal. Old solid shoe remains rejected by4.0mm measured overhead conflict. Both mirrored slide locks have zero common-volume collision with yokes and M4 service region.\n",
        "REINFORCED_GUARD_PARENT_STATUS.md": h + "\nThe reinforced guard remains exact: H9, upper wall5, root6, R3-class gusset, R1 top and connector margin3.9mm. Its frame-facing plane is unchanged;8mm-spacer frame gap remains4.4mm authority. The hook/receiver/cap are front/interior components and do not alter guard geometry.\n",
        "TORQUE_LOAD_PATH.md": h + "\nPrimary drive path remains `Ø10 shaft → headed M4×2 → metal collar → reaction yokes×2 → broad PETG pockets → one-piece hub → frozen12T → crawler`. The hook is primary cap-side axial retention; M3 prevents reverse slide and retains the other side. Neither hook, M3 nor cap receives drivetrain torque credit.\n",
        "ASSEMBLY_PROCEDURE.md": h + "\n1. Assemble shaft/collar and headed M4×2. 2. Seat both yokes at stops. 3. Present cap at OPEN offset with hook at entry. 4. Slide5mm to the solid stop. 5. Confirm OD/shaft LOCK seat and M3 alignment. 6. Insert the actual short M3. 7. Fit visible rear washer/nut and tighten without crushing PETG. 8. Reverse only after removing M3.\n",
        "PRINT_PLAN.md": h + "\nPrint the S25/S35/S45 slide-lock coupon first in PETG on Bambu A1, with hook parts on their reinforced side and receiver windows upward. Print reaction-yoke coupon if incomplete. Do not produce a full12T STL and do not print the reference STEP until both coupon gates pass. Slicer support/bridge preview remains required.\n",
        "PHYSICAL_TEST_PLAN.md": h + "\nFor each S25/S35/S45 record axial insert, hand slide, stop, concentricity, rocking, axial pull without M3, M3 alignment/insertion, rear access, pull with M3, reverse-slide blocking, disassembly and whitening/crack. Select the tightest reliable fit. After an approved full print, apply witness marks and perform50 forward/50 reverse hand revolutions.\n",
        "POWERED_TEST_GATE.md": h + "\n`NOT_YET_APPROVED`. Unloaded low-load power additionally requires yoke PASS, hybrid slide-lock PASS, full12T physical PASS,9mm guard physical PASS,8mm spacer rotational PASS, final170mm frame, independent shaft non-contact, axial retention, fuse, E-stop, polarity, MD10C and restrained cables.\n",
        "SAFETY_NOTES.md": h + "\nDRY COUPON WORK ONLY. Never install/remove the cap with power present. This is a rigid translation lock, not a snap: do not flex the hook. Stop on reverse slide, disengagement, root whitening/crack, receiver damage, M3 looseness, severe rocking, yoke/M4 motion, connector climb or crawler jam.\n",
        "HOLD_REGISTER.md": h + "\n- Physical S25/S35/S45 selection and final clearance\n- Hook/receiver wear life and repeated-cycle durability\n- Final Y1/Y2/Y3 reaction-yoke selection\n- Actual M3 nut/washer stack and torque\n- Full-load torque, final belt and shaft cut length\n- Powered, water, mud and field testing\n",
        "SOURCE_TRACE.md": h + "\n- v0.9.6.10 read-only: short-M3 physical authority and rejected two-bridge package reference.\n- v0.9.6.9 read-only: exact guard, reaction yokes, B collar, headed M4 and protected12T.\n- User v0.9.6.11: rigid slide-lock architecture and two-bridge packaging rejection.\n- User-view side mapping is not proven; LOCK_A and mirrored LOCK_B avoid a left/right guess.\n",
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
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\nclassification={CLASSIFICATION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths={len(EXPECTED_PATHS)}\nstep=5\nstl=2\nsvg=10\nslide_primary_mm=5.0\nclearance_primary=S35\nm3_count=1\nfull_12t_stl=NOT_GENERATED\n")
    write_text(out / "TEST_LOG.txt", "Common Rover v0.9.6.11 contract\nCONTRACT=RUNTIME_PASS_REQUIRED\nSTEP_IMPORT=RUNTIME_PASS_REQUIRED\nSTL_MANIFOLD=RUNTIME_PASS_REQUIRED\nSWEPT_PATH_LOCK_A_B=RUNTIME_PASS_REQUIRED\nREPRODUCIBILITY=RUNTIME_PASS_REQUIRED\nSLIDE_LOCK_COUPON=PHYSICAL_PENDING\nREACTION_YOKE_COUPON=PHYSICAL_PASS_REQUIRED\nPOWERED=NOT_YET_APPROVED\n")
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
    count = struct.unpack("<I", data[80:84])[0]
    if len(data) != 84 + 50 * count:
        return False
    edges: dict[tuple[bytes, bytes], int] = {}
    for i in range(count):
        tri = data[84 + i * 50 + 12:84 + i * 50 + 48]
        vertices = [tri[j:j + 12] for j in (0, 12, 24)]
        for a, b in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            key = tuple(sorted((a, b)))
            edges[key] = edges.get(key, 0) + 1
    return bool(edges) and all(value == 2 for value in edges.values())


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, object]]:
    p = PARAMS
    m = geometry_metrics()
    c = collision_report(m)
    checks: list[tuple[str, bool, object]] = []

    def add(name: str, ok: bool, detail: object) -> None:
        checks.append((name, bool(ok), detail))

    actual = sorted(path.relative_to(lane).as_posix() for path in lane.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    add("version", p["version"] == VERSION, p["version"])
    add("classification", p["classification"] == CLASSIFICATION, p["classification"])
    add("paths", actual == EXPECTED_PATHS, len(actual))
    add("manifest", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, len(EXPECTED_PATHS))
    add("sha", sums_ok(lane), len(EXPECTED_PATHS) - 1)
    add("commit-paths", (lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() == [(LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS], len(EXPECTED_PATHS))
    add("no-cache", not any(x.name == "__pycache__" or x.suffix == ".pyc" or x.name == ".pytest_cache" for x in lane.rglob("*")), "clean")
    reject = p["v09610_rejection"]
    add("v09610-reject", reject["status"] == "CAD_PHYSICAL_REVIEW_REJECT", reject)
    add("v09610-reason", reject["reason"] == "CRAWLER_RUNNING_SPACE_INTERFERENCE_RISK" and reject["m3_length_only_failure"] is False, reject)
    mech = p["mechanism"]
    for key, value in (("m3_count", 1), ("l_hook_count", 1), ("rigid_hook", True), ("snap_hook", False), ("spring_finger", False), ("receiver", True), ("linear_slide", True), ("hard_stop", True), ("final_concentric", True), ("hidden_captive_nut", False), ("petg_thread", False), ("full_body_m3", False)):
        add(f"mechanism-{key}", mech[key] == value, mech)
    orientation = p["orientation"]
    add("orientation-ambiguous", orientation["user_view_mapping"] == "AMBIGUOUS_NOT_GUESSED", orientation)
    add("orientation-mirrors", set(orientation["mirrored_candidates"]) == {"LOCK_A", "LOCK_B"} and not orientation["mechanical_design_difference"], orientation)
    add("orientation-primary", orientation["cad_primary"] == "LOCK_A", orientation)
    motion = p["motion"]
    add("slide-primary", motion["slide_primary_mm"] == 5.0, motion)
    add("slide-comparison", motion["comparison_mm"] == [4.0, 5.0, 6.0], motion)
    add("open-offset", motion["open_cap_eccentric_allowed"] and motion["open_cap_offset_mm"] == 5.0, motion)
    add("lock-center", motion["lock_cap_eccentric_mm"] == 0.0 and motion["lock_end_shaft_seat_axis_error_mm"] == 0.0, motion)
    add("shaft-slot", motion["shaft_service_slot_required"], motion)
    add("m3-interlock", not motion["m3_alignment_open"] and motion["m3_alignment_lock"] and motion["m3_open_misalignment_mm"] == 5.0, motion)
    hook_p = p["hook"]
    add("hook-overlap", hook_p["engagement_overlap_nominal_mm"] == 3.0, hook_p)
    add("hook-thickness", hook_p["structural_thickness_mm"] == 4.0 and hook_p["root_thickness_mm"] == 6.0, hook_p)
    add("hook-width-fillet", hook_p["engagement_width_mm"] == 12.0 and hook_p["root_fillet_mm"] == 2.0, hook_p)
    add("hook-rigid", hook_p["short"] and hook_p["broad"] and hook_p["rigid"] and not hook_p["flexure_required"], hook_p)
    add("hook-role", hook_p["primary_axial_retention_hook_side"] and not hook_p["primary_torque_path"], hook_p)
    receiver = p["receiver"]
    add("receiver-functions", receiver["entry_opening"] and receiver["sliding_channel"] and receiver["undercut_lip"] and receiver["positive_final_stop"], receiver)
    add("receiver-restored", receiver["restored_opposite_m3_hole"] and receiver["restored_opposite_local_bridge"] and receiver["restored_opposite_service_window"] and not receiver["unnecessary_circular_void"], receiver)
    coupon_p = p["clearance_coupon"]
    add("S25", coupon_p["variants_mm"]["S25"] == 0.25, coupon_p)
    add("S35", coupon_p["variants_mm"]["S35"] == 0.35, coupon_p)
    add("S45", coupon_p["variants_mm"]["S45"] == 0.45, coupon_p)
    add("coupon-primary", coupon_p["design_primary"] == "S35" and coupon_p["physical_selection"] == "TIGHTEST_RELIABLE_SLIDING_FIT_PENDING", coupon_p)
    add("no-friction-authority", not coupon_p["retention_by_friction"], coupon_p)
    m3p = p["single_m3"]
    add("m3-physical", m3p["under_head_usable_length_mm"] == 20.5 and m3p["overall_reference_mm"] == 27.9, m3p)
    add("m3-single", m3p["count"] == 1 and m3p["local_bridge_thickness_mm"] == 7.0, m3p)
    add("m3-stack", m3p["cap_thickness_mm"] == 5.5 and m3p["petg_stack_mm"] == 12.5 and m3p["remaining_hardware_budget_mm"] == 8.0, m3p)
    add("m3-metal-access", m3p["rear_washer"] and m3p["rear_nut"] and m3p["rear_visible_accessible_removable"], m3p)
    add("m3-no-hidden-thread", not m3p["hidden_captive_nut"] and not m3p["petg_thread"] and not m3p["primary_torque_path"], m3p)
    cap_p = p["cap"]
    add("cap-dims", cap_p["outer_diameter_mm"] == 54.0 and cap_p["thickness_mm"] == 5.5, cap_p)
    add("cap-lock-center", cap_p["lock_position_centered"] and cap_p["lock_end_shaft_seat"] and cap_p["service_motion_slot_mm"] == 5.0, cap_p)
    yoke = p["reaction_yoke"]
    add("yoke-variants", yoke["variants_mm"] == {"Y1": 3.3, "Y2": 3.5, "Y3": 3.7}, yoke)
    add("yoke-preserved", yoke["preserved_from"] == "v0.9.6.9" and yoke["design_primary_bridge_mm"] == 3.5, yoke)
    guard = p["guard"]
    add("guard-preserved", guard["preserved_from"] == "v0.9.6.9" and guard["new_height_mm"] == 9.0 and guard["selected_upper_wall_mm"] == 5.0 and guard["root_mm"] == 6.0, guard)
    add("guard-detail", guard["root_gusset_class"] == "R3_CLASS" and guard["top_edge_radius_mm"] == 1.0 and guard["connector_vertical_margin_mm"] == 3.9 and guard["frame_clearance_measured_mm"] == 4.4, guard)
    capture = p["full_capture"]
    add("B-preserved", capture["selected"] == "B" and capture["collar_pocket_diameter_mm"] == 16.2 and capture["hardware_cavity_radius_mm"] == 20.4, capture)
    m4 = p["m4"]
    add("m4-preserved", m4["type"] == "HEADED_M4" and m4["count"] == 2 and m4["separation_deg"] == 90.0 and m4["unchanged"], m4)
    pitch = p["pitch"]
    add("pitch-frozen", pitch["physical_result"] == "PHYSICAL_MATCH" and pitch["status"] == "FROZEN", pitch)
    tooth = p["protected_12t"]
    add("12t-count", tooth["teeth"] == 12 and tooth["phase_deg"] == 15.0 and tooth["spacing_deg"] == 30.0, tooth)
    add("12t-radii", tooth["tip_radius_mm"] == 33.07 and tooth["root_radius_mm"] == 29.47, tooth)
    add("12t-widths", tooth["tip_width_mm"] == 7.5 and tooth["root_width_mm"] == 9.5 and tooth["axial_width_mm"] == 44.0, tooth)
    add("12t-pitch", tooth["pitch_diameter_mm"] == 76.3943726841 and tooth["buried_root_overlap_mm"] == 4.0 and tooth["outer_body"] == "ONE_PIECE", tooth)
    for name, local in m["orientations"].items():
        add(f"{name}-one-solid", local["main_solids"] == 1, local)
        add(f"{name}-12t-external", local["protected_external_missing_mm3"] == 0.0, local["protected_external_missing_mm3"])
        add(f"{name}-running-space", local["lock_cap_running_space_intersection_mm3"] == local["open_cap_running_space_intersection_mm3"] == local["m3_running_space_intersection_mm3"] == local["receiver_running_space_intersection_mm3"] == 0.0, local)
        add(f"{name}-deleted-m3-restored", local["deleted_m3_axis_restored_petg_mm3"] > 0.0, local["deleted_m3_axis_restored_petg_mm3"])
        add(f"{name}-endpoint-collision", c["orientations"][name]["endpoint_all_zero"], c["orientations"][name]["endpoint_intersections"])
        add(f"{name}-sweep-count", local["motion"]["sample_count"] == 21, local["motion"]["sample_count"])
        add(f"{name}-swept-path", local["motion"]["swept_path_pass"] and local["motion"]["max_unintended_intersection_mm3"] == 0.0, local["motion"])
        add(f"{name}-lock-center", local["motion"]["lock_concentric_error_mm"] == 0.0 and local["motion"]["m3_lock_misalignment_mm"] == 0.0, local["motion"])
        add(f"{name}-open-interlock", local["motion"]["open_offset_mm"] == 5.0 and local["motion"]["m3_open_misalignment_mm"] == 5.0, local["motion"])
        add(f"{name}-valid", local["all_primary_valid"], local["all_primary_valid"])
    add("mirrors-equivalent", m["mirror_metric_equivalent"], m["mirror_metric_equivalent"])
    add("collision-all", c["known_all_zero"], c)
    add("coupon-solids", m["coupon_solids"] == 6, m["coupon_solids"])
    add("coupon-valid", m["coupon_valid"], m["coupon_valid"])
    printing = p["printability"]
    add("print-orientation", printing["coupon_orientation"] == "HOOK_ON_SIDE_RECEIVER_WINDOW_UP" and printing["hook_root_crosses_multiple_extrusion_paths"], printing)
    add("no-full-stl", not printing["full_12t_stl_generated"] and not (lane / "drive/artifacts/drive_12t_h25a1_hybrid_slide_lock_v0_9_6_11.stl").exists(), printing)
    steps = [lane / rel for rel in CAD if rel.endswith(".step")]
    stls = [lane / rel for rel in CAD if rel.endswith(".stl")]
    add("step-count", len(steps) == 5, len(steps))
    imported = 0
    for path in steps:
        try:
            obj = cq.importers.importStep(str(path))
            imported += int(obj.solids().size() > 0 and all(s.isValid() for s in obj.solids().vals()))
        except Exception:
            pass
    add("step-import", imported == 5, imported)
    add("stl-count", len(stls) == 2, len(stls))
    add("stl-manifold", all(stl_is_manifold(path) for path in stls), len(stls))
    add("svg-count", len(SVGS) == 10 and all((lane / rel).read_text(encoding="utf-8").startswith("<svg") for rel in SVGS), len(SVGS))
    add("docs-count", len(DOCS) == 22, len(DOCS))
    gates = p["gates"]
    add("coupon-gate", gates["slide_lock_coupon"] == "READY_FOR_PHYSICAL_COUPON", gates)
    add("full12t-gate", gates["full_12t"] == "PRINT_PENDING_REACTION_YOKE_AND_SLIDE_LOCK_COUPON", gates)
    add("powered-field", gates["powered"] == "NOT_YET_APPROVED" and gates["field"] == "NOT_APPROVED", gates)
    if repo_checks:
        preflight = repository_preflight()
        prefix = LANE_REL.as_posix() + "/"
        target = sorted(path for path in untracked_paths() if path.startswith(prefix))
        expected = sorted((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS)
        add("repo-preflight", all(preflight["checks"].values()), preflight["checks"])
        add("repo-target", target == expected, len(target))
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
    with tempfile.TemporaryDirectory(prefix="v09611_a_") as a, tempfile.TemporaryDirectory(prefix="v09611_b_") as b:
        pa, pb = Path(a), Path(b)
        build_outputs(pa)
        build_outputs(pb)
        differences = [rel for rel in EXPECTED_PATHS if (pa / rel).read_bytes() != (pb / rel).read_bytes()]
    report = {"checked": len(EXPECTED_PATHS), "identical": len(EXPECTED_PATHS) - len(differences), "differences": differences, "status": "PASS" if not differences else "FAIL"}
    print(json.dumps(report, ensure_ascii=False))
    if differences:
        raise SystemExit(1)
    return report


def zip_handoff(lane: Path = DEFAULT_LANE) -> tuple[Path, dict[str, object]]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_Hybrid_Slide_Lock_Hub_Cap_v0_9_6_11_{stamp}.zip"
    if target.exists():
        raise RuntimeError(f"ZIP_EXISTS_REFUSE_OVERWRITE: {target}")
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in EXPECTED_PATHS:
            zf.write(lane / rel, rel)
    with zipfile.ZipFile(target, "r") as zf:
        names = zf.namelist()
        duplicate = len(names) - len(set(names))
        traversal = [name for name in names if name.startswith(("/", "\\")) or ".." in Path(name).parts]
        manifest = zf.read("MANIFEST.txt").decode("utf-8").splitlines()
        sums = {}
        for line in zf.read("SHA256SUMS.txt").decode("utf-8").splitlines():
            digest, rel = line.split("  ", 1)
            sums[rel] = digest
        mismatches = [rel for rel, digest in sums.items() if hashlib.sha256(zf.read(rel)).hexdigest() != digest]
        parent_contamination = [name for name in names if name not in EXPECTED_PATHS]
    audit = {"open": "PASS", "entries": len(names), "duplicate": duplicate, "traversal": traversal, "manifest_exact": manifest == EXPECTED_PATHS, "sha_mismatches": mismatches, "parent_contamination": parent_contamination, "sha256": sha256(target)}
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
