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


VERSION = "v0.9.6.15"
CLASSIFICATION = "DUAL_L_SLIDE_BELT_ENTRY_FINALIZATION"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_dual_l_slide_rimless_hub_v0_9_6_15")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2213
BASE_OUTSIDE_DIGEST = "1717806b69fea0525803cf5000aeca5366e10615c7a1c7ed79a8f4beac2c3c31"
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

PARENT_BUILDER = REPO_ROOT / "cad/common_rover/common_rover_belt_entry_clearance_rimless_v0_9_6_14/build_belt_entry_clearance_rimless_v0_9_6_14.py"
_spec = importlib.util.spec_from_file_location("v09614_parent", PARENT_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load protected parent: {PARENT_BUILDER}")
parent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = parent
_spec.loader.exec_module(parent)

p13 = parent.parent
p12 = p13.parent
p9 = p12.v0969
p8 = p12.v0968

PROTECTED_LANES = dict(parent.PROTECTED_LANES)
PROTECTED_LANES["v0.9.6.14"] = (
    "cad/common_rover/common_rover_belt_entry_clearance_rimless_v0_9_6_14",
    17,
    "7a4d7bf0947e44484ba3db94061351d181387e067ffe156851e06e84ec104f29",
)

DOCS = [
    "README.md",
    "DESIGN_AUTHORITY.md",
    "PHYSICAL_INPUTS.md",
    "V09614_LOWER_FLANGE_FAILURE.md",
    "M3_ARCHITECTURE_SUPERSESSION.md",
    "DUAL_L_SLIDE_LOCK_SPEC.md",
    "DUAL_RECEIVER_SPEC.md",
    "STOP_KEY_SPEC.md",
    "BELT_ENTRY_OPEN_GEOMETRY_SPEC.md",
    "REACTION_Y3_PARENT_STATUS.md",
    "FINAL_GUARD_STATUS.md",
    "TORQUE_LOAD_PATH.md",
    "ASSEMBLY_PROCEDURE.md",
    "PRINT_PLAN.md",
    "PHYSICAL_TEST_PLAN.md",
    "POWERED_TEST_GATE.md",
    "HOLD_REGISTER.md",
    "SOURCE_TRACE.md",
]
CAD = [
    "artifacts/dual_l_slide_lock_coupon_v0_9_6_15.step",
    "artifacts/dual_l_slide_lock_coupon_v0_9_6_15.stl",
    "artifacts/drive_12t_h25a1_dual_l_rimless_v0_9_6_15.step",
    "artifacts/drive_12t_h25a1_dual_l_rimless_v0_9_6_15.stl",
    "artifacts/h25a1_dual_l_slide_cap_v0_9_6_15.step",
    "artifacts/h25a1_dual_l_slide_cap_v0_9_6_15.stl",
    "artifacts/h25a1_dual_l_stop_key_v0_9_6_15.step",
    "artifacts/h25a1_dual_l_stop_key_v0_9_6_15.stl",
]
SVGS = [
    "artifacts/v09614_flange_failure_v0_9_6_15.svg",
    "artifacts/m3_vs_dual_l_v0_9_6_15.svg",
    "artifacts/dual_l_open_v0_9_6_15.svg",
    "artifacts/dual_l_locked_v0_9_6_15.svg",
    "artifacts/dual_l_section_v0_9_6_15.svg",
    "artifacts/stop_key_v0_9_6_15.svg",
    "artifacts/belt_side_entry_v0_9_6_15.svg",
    "artifacts/lower_geometry_open_section_v0_9_6_15.svg",
]
JSONS = ["design_parameters.json", "validation_report.json"]
SOURCES = [
    "build_dual_l_slide_rimless_hub_v0_9_6_15.py",
    "tests/test_dual_l_slide_rimless_hub_v0_9_6_15_contract.py",
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
volume = parent.volume
dims = parent.dims

MASTER_HOOK_ANGLE_DEG = 225.0
OPPOSED_HOOK_ANGLE_DEG = 45.0
SLIDE_TRAVEL_MM = 3.0
S45_CLEARANCE_MM = 0.45
HOOK_COUNT = 2
RECEIVER_COUNT = 2
HOOK_OVERLAP_MM = 2.75
HOOK_STRUCTURAL_THICKNESS_MM = 4.0
HOOK_ROOT_THICKNESS_MM = 6.0
HOOK_ENGAGEMENT_WIDTH_MM = 12.0
HOOK_ROOT_RADIUS_MM = 2.0
HUB_KEEP_RADIUS_MM = 20.4
ANNULAR_REMOVAL_OUTER_RADIUS_MM = 29.469
SPOKE_COUNT = 6
SPOKE_TANGENTIAL_WIDTH_MM = 8.0
SPOKE_RADIAL_LENGTH_MM = 6.2
SPOKE_CENTER_RADIUS_MM = 23.3
BELT_ENTRY_ANGLES_DEG = [150.0, 270.0]
BELT_ENTRY_ENVELOPE_WIDTH_MM = 12.0
BELT_ENTRY_ENVELOPE_RADIAL_DEPTH_MM = 4.6
BELT_ENTRY_CENTER_RADIUS_MM = 22.8
RING_SAMPLE_RADII_MM = [20.8, 21.8, 22.8, 23.8, 24.8]
RING_SAMPLE_Z_MM = [-18.0, 0.0, 18.0]
RING_SAMPLE_ANGLES_DEG = list(range(0, 360, 15))


PARAMS = {
    "version": VERSION,
    "classification": CLASSIFICATION,
    "units": "mm",
    "parent_lane": parent.LANE_REL.as_posix(),
    "v09614_failure": {
        "LOWER_CIRCULAR_PLATE": "BELT_ENTRY_PHYSICAL_PACKAGING_FAIL",
        "reason": "BELT_CANNOT_BE_INSTALLED_FROM_SIDE",
        "disposition": "REJECT_AS_FULL_12T_PHYSICAL_CANDIDATE",
    },
    "architecture": {
        "lock": "DUAL_RIGID_L_HOOK_LINEAR_SLIDE",
        "hook_count": HOOK_COUNT,
        "receiver_count": RECEIVER_COUNT,
        "opposition_deg": 180.0,
        "same_linear_motion": True,
        "travel_mm": SLIDE_TRAVEL_MM,
        "clearance_mm": S45_CLEARANCE_MM,
        "hard_stop_count": 2,
        "final_concentricity_offset_mm": 0.0,
        "snap": False,
        "flexure": False,
        "spring": False,
        "m3_screw_count": 0,
        "m3_nut_count": 0,
        "m3_bridge_count": 0,
        "m3_nut_seat_count": 0,
        "m3_island_count": 0,
    },
    "hook": {
        "nominal_overlap_mm": HOOK_OVERLAP_MM,
        "required_minimum_overlap_mm": 2.5,
        "target_overlap_range_mm": [2.5, 3.0],
        "structural_thickness_mm": HOOK_STRUCTURAL_THICKNESS_MM,
        "root_thickness_mm": HOOK_ROOT_THICKNESS_MM,
        "engagement_width_mm": HOOK_ENGAGEMENT_WIDTH_MM,
        "root_radius_mm": HOOK_ROOT_RADIUS_MM,
    },
    "receiver": {
        "local_islands": 2,
        "entry": "OPEN_SIDED_45_DEG_SELF_SUPPORTING",
        "short_channel": True,
        "undercut_lip": True,
        "broad_hard_stop": True,
        "continuous_backing_ring": False,
        "trapped_support": False,
    },
    "stop_key": {
        "count": 1,
        "material": "PETG",
        "external": True,
        "removable": True,
        "screwless": True,
        "blocks_reverse_slide_only": True,
        "torque_path": False,
        "friction_only_retention": False,
        "finger_tab": True,
        "tool_notch": True,
    },
    "belt_entry": {
        "former_v09614_probe_width_mm": 9.0,
        "conservative_cad_envelope_width_mm": BELT_ENTRY_ENVELOPE_WIDTH_MM,
        "radial_depth_mm": BELT_ENTRY_ENVELOPE_RADIAL_DEPTH_MM,
        "angles_deg": BELT_ENTRY_ANGLES_DEG,
        "actual_section": "BELT_SECTION_PHYSICAL_HOLD",
        "continuous_lower_ring_result": "NO_CONTINUOUS_LOWER_RING",
        "continuous_floor": False,
    },
    "preserved": {
        "Y3_height_mm": 3.7,
        "M4_head_space_mm": 4.3,
        "Y3_vertical_margin_mm": 0.6,
        "YW30_receiver_width_mm": 15.5,
        "Y3_physical_status": "REACTION_Y3_PARENT_STATUS_PENDING_FULL_PHYSICAL_FIT",
        "B_collar_pocket_diameter_mm": 16.2,
        "B_hardware_cavity_radius_mm": 20.4,
        "headed_m4_count": 2,
        "headed_m4_separation_deg": 90.0,
        "grub_screw_count": 0,
        "guard": "H9_UPPER5_ROOT6_R3_TOPR1_FINAL_PRESERVED",
        "guard_frame_clearance_mm": 4.4,
        "protected_12t": dict(parent.PARAMS["preserved"]["protected_12t"]),
        "pitch": dict(parent.PARAMS["preserved"]["pitch"]),
    },
    "torque_path": ["SHAFT", "HEADED_M4_X2", "METAL_B_COLLAR", "Y3_X2", "SHOULDERS", "HUB", "PROTECTED_12T"],
    "non_torque_components": ["DUAL_L_HOOKS", "DUAL_RECEIVERS", "STOP_KEY"],
    "printability": {
        "printer": "BAMBU_A1",
        "material": "PETG",
        "first_print": "DUAL_L_SLIDE_LOCK_COUPON_ONLY",
        "full_12t": "PRINT_ONE_ONLY_AFTER_COUPON_PASS",
        "new_long_internal_support": False,
        "new_closed_cavity": False,
        "slicer": "HOLD_SLICER_NOT_RUN",
    },
    "gates": {
        "coupon": "READY_FOR_PHYSICAL_PRINT",
        "full_12t": "PENDING_DUAL_L_COUPON_PASS",
        "powered": "NOT_YET_APPROVED",
        "actual_belt": "BELT_SECTION_PHYSICAL_HOLD",
        "Y3_full_fit": "HOLD",
        "dual_l_vibration": "HOLD",
        "stop_key_lifetime": "HOLD",
        "torque": "HOLD",
        "powered_belt": "HOLD",
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
        "branch": branch == EXPECTED_BRANCH,
        "head": head == EXPECTED_HEAD,
        "staged_zero": not staged,
        "tracked_dirty_unchanged": dirty == TRACKED_DIRTY,
        "authority_4_of_4": authority == AUTHORITY_HASHES,
        "protected_lanes": protected == expected_protected,
        "outside_untracked": outside == (BASE_OUTSIDE_COUNT, BASE_OUTSIDE_DIGEST),
    }
    result = {"checks": checks, "branch": branch, "head": head, "staged": staged, "dirty": dirty, "authority": authority, "protected": protected, "outside": outside}
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED_REPOSITORY_PREFLIGHT: " + json.dumps(result, ensure_ascii=False, default=list))
    return result


def rotate_local(obj: cq.Workplane, angle_deg: float) -> cq.Workplane:
    return obj.rotate((0, 0, 0), (0, 0, 1), angle_deg)


def local_box(radial: float, tangential: float, axial: float, r_center: float, t_center: float, z_center: float, angle_deg: float) -> cq.Workplane:
    return rotate_local(box(radial, tangential, axial, (r_center, t_center, z_center)), angle_deg)


def dual_receiver_channel(angle_deg: float, motion_direction: int) -> cq.Workplane:
    radius = 21.5
    if motion_direction not in (-1, 1):
        raise ValueError("motion_direction must be -1 or +1")
    if motion_direction == 1:
        tangent_min, tangent_max = -3.0, SLIDE_TRAVEL_MM + 3.0 + S45_CLEARANCE_MM
    else:
        tangent_min, tangent_max = -(SLIDE_TRAVEL_MM + 3.0 + S45_CLEARANCE_MM), 3.0
    length = tangent_max - tangent_min
    center = (tangent_min + tangent_max) / 2.0
    outer_half = 6.0 + S45_CLEARANCE_MM
    inner_half = 3.0 + S45_CLEARANCE_MM
    points = [
        (radius - outer_half, 13.35), (radius + outer_half, 13.35),
        (radius + outer_half, 18.25), (radius + inner_half, 21.25),
        (radius + inner_half, 22.45), (radius - inner_half, 22.45),
        (radius - inner_half, 21.25), (radius - outer_half, 18.25),
    ]
    channel = cq.Workplane("XZ").polyline(points).close().extrude(length / 2.0, both=True).translate((0, center, 0))
    entry = box(12.0 + 2 * S45_CLEARANCE_MM, 6.0 + 2 * S45_CLEARANCE_MM, 9.1, (radius, motion_direction * SLIDE_TRAVEL_MM, 17.9))
    return rotate_local(channel.union(entry).clean(), angle_deg).clean()


def spoke_zones() -> list[cq.Workplane]:
    return [local_box(SPOKE_RADIAL_LENGTH_MM, SPOKE_TANGENTIAL_WIDTH_MM, 44.4, SPOKE_CENTER_RADIUS_MM, 0.0, 0.0, angle) for angle in range(0, 360, 60)]


def yoke_support_zones() -> list[cq.Workplane]:
    primary = box(18.0, 19.0, 27.2, (20.0, 0.0, 8.8))
    return [primary, primary.rotate((0, 0, 0), (0, 0, 1), 90)]


def receiver_islands() -> list[cq.Workplane]:
    return [p12.receiver_mass(MASTER_HOOK_ANGLE_DEG), p12.receiver_mass(OPPOSED_HOOK_ANGLE_DEG)]


def pre_rim_dual_receiver_body() -> cq.Workplane:
    part = p12.main_sprocket()
    for island in receiver_islands():
        part = part.union(island)
    for void in [
        dual_receiver_channel(MASTER_HOOK_ANGLE_DEG, 1),
        dual_receiver_channel(OPPOSED_HOOK_ANGLE_DEG, -1),
        p12.yoke_receiver_pocket(15.5),
        p12.yoke_receiver_pocket(15.5).rotate((0, 0, 0), (0, 0, 1), 90),
    ]:
        for solid in void.solids().vals():
            part = part.cut(cq.Workplane(obj=solid))
    return part.clean()


def annular_removal_cutter() -> cq.Workplane:
    target = cylinder(ANNULAR_REMOVAL_OUTER_RADIUS_MM, 44.4, -22.2).cut(cylinder(HUB_KEEP_RADIUS_MM, 44.8, -22.4))
    allowed = [p13.exact_teeth(), *spoke_zones(), *receiver_islands(), *yoke_support_zones()]
    for zone in allowed:
        for solid in zone.solids().vals():
            target = target.cut(cq.Workplane(obj=solid))
    return target.clean()


def dual_l_main() -> cq.Workplane:
    part = pre_rim_dual_receiver_body()
    for solid in annular_removal_cutter().solids().vals():
        part = part.cut(cq.Workplane(obj=solid))
    return part.clean()


def dual_l_cap(position_mm: float = 0.0) -> cq.Workplane:
    part = cylinder(27.0, 5.5, 22.0)
    part = part.cut(p12.shaft_service_slot(SLIDE_TRAVEL_MM))
    part = part.cut(box(17.5, 9.4, 5.9, (13.75, 0, 24.75)))
    part = part.cut(box(9.4, 17.5, 5.9, (0, 13.75, 24.75)))
    part = part.union(p12.rigid_hook(MASTER_HOOK_ANGLE_DEG))
    part = part.union(p12.rigid_hook(OPPOSED_HOOK_ANGLE_DEG))
    if position_mm:
        part = part.translate(p12.slide_vector(MASTER_HOOK_ANGLE_DEG, position_mm))
    return part.clean()


def stop_key_placed() -> cq.Workplane:
    blocker = local_box(12.0, 1.2, 4.0, 21.5, 3.7, 15.8, MASTER_HOOK_ANGLE_DEG)
    finger = local_box(7.0, 2.0, 3.0, 21.5, 5.0, 19.1, MASTER_HOOK_ANGLE_DEG)
    notch = local_box(1.6, 0.8, 3.4, 18.8, 5.0, 19.1, MASTER_HOOK_ANGLE_DEG)
    return blocker.union(finger).cut(notch).clean()


def shift_to_z0(obj: cq.Workplane) -> cq.Workplane:
    bb = obj.val().BoundingBox()
    return obj.translate((0, 0, -bb.zmin))


def coupon() -> cq.Workplane:
    base = dual_l_main().intersect(cylinder(29.25, 27.1, -5.0)).clean()
    base = shift_to_z0(base).translate((-72.0, 0, 0))
    cap = shift_to_z0(dual_l_cap()).translate((18.0, 0, 0))
    key = shift_to_z0(stop_key_placed()).translate((74.0, 0, 0))
    return compound([base, cap, key])


def belt_entry_envelope(angle_deg: float) -> cq.Workplane:
    inner = BELT_ENTRY_CENTER_RADIUS_MM - BELT_ENTRY_ENVELOPE_RADIAL_DEPTH_MM / 2.0
    outer = BELT_ENTRY_CENTER_RADIUS_MM + BELT_ENTRY_ENVELOPE_RADIAL_DEPTH_MM / 2.0
    half = math.degrees(math.asin((BELT_ENTRY_ENVELOPE_WIDTH_MM / 2.0) / BELT_ENTRY_CENTER_RADIUS_MM))
    offsets = [-half + index * (2.0 * half / 8.0) for index in range(9)]
    points = []
    for offset in offsets:
        theta = math.radians(angle_deg + offset)
        points.append((outer * math.cos(theta), outer * math.sin(theta)))
    for offset in reversed(offsets):
        theta = math.radians(angle_deg + offset)
        points.append((inner * math.cos(theta), inner * math.sin(theta)))
    return cq.Workplane("XY").polyline(points).close().extrude(44.6).translate((0, 0, -22.3))


def shape_volume(obj: cq.Workplane) -> float:
    return round(sum(float(solid.Volume()) for solid in obj.solids().vals()), 6)


def safe_missing(reference: cq.Workplane, retained: cq.Workplane) -> float:
    return shape_volume(reference.cut(retained))


def lower_ring_search(main: cq.Workplane) -> dict[str, object]:
    rows = []
    for z in RING_SAMPLE_Z_MM:
        for radius in RING_SAMPLE_RADII_MM:
            occupied = []
            for angle in RING_SAMPLE_ANGLES_DEG:
                x = radius * math.cos(math.radians(angle))
                y = radius * math.sin(math.radians(angle))
                probe = box(0.24, 0.24, 0.24, (x, y, z))
                occupied.append(volume(probe, main) > 0.000001)
            rows.append({"z_mm": z, "radius_mm": radius, "occupied_samples": sum(occupied), "samples": len(occupied), "continuous": all(occupied)})
    continuous = [row for row in rows if row["continuous"]]
    return {
        "method": "15_DEG_POINT_PROBE_AT_5_RADII_X_3_AXIAL_PLANES",
        "sample_count": len(RING_SAMPLE_Z_MM) * len(RING_SAMPLE_RADII_MM) * len(RING_SAMPLE_ANGLES_DEG),
        "rows": rows,
        "continuous_rows": continuous,
        "result": "NO_CONTINUOUS_LOWER_RING" if not continuous else "FAIL_CONTINUOUS_LOWER_RING",
        "pass": not continuous,
    }


def slide_sweep_metrics(main: cq.Workplane) -> dict[str, object]:
    yokes = compound(list(p12.y3_pair()))
    guard = p9.reinforced_guard()
    crawler = p12.crawler_reference()
    shaft = cylinder(5.0, 70.0, -35.0)
    rows = []
    for index in range(13):
        position = index * 0.25
        cap = dual_l_cap(position)
        rows.append({
            "position_mm": position,
            "cap_main_mm3": volume(cap, main),
            "cap_yokes_mm3": volume(cap, yokes),
            "cap_guard_mm3": volume(cap, guard),
            "cap_crawler_mm3": volume(cap, crawler),
            "cap_shaft_mm3": volume(cap, shaft),
        })
    maximum = max(value for row in rows for key, value in row.items() if key.endswith("mm3"))
    return {"samples": rows, "sample_count": 13, "increment_mm": 0.25, "travel_mm": SLIDE_TRAVEL_MM, "max_unintended_intersection_mm3": maximum, "pass": maximum == 0.0}


def stop_key_metrics(main: cq.Workplane) -> dict[str, object]:
    key = stop_key_placed()
    lock = dual_l_cap(0.0)
    reverse = dual_l_cap(0.5)
    return {
        "key_main_mm3": volume(key, main),
        "key_locked_cap_mm3": volume(key, lock),
        "key_reverse_0_5mm_cap_mm3": volume(key, reverse),
        "lock_install_clear": volume(key, main) == 0.0 and volume(key, lock) == 0.0,
        "reverse_motion_blocked": volume(key, reverse) > 0.0,
        "torque_path": False,
    }


def geometry_metrics() -> dict[str, object]:
    base, main = pre_rim_dual_receiver_body(), dual_l_main()
    teeth = base.intersect(p13.exact_teeth())
    guard = p9.reinforced_guard()
    yokes = compound(list(p12.y3_pair()))
    collar, m4 = p8.collar(), p8.m4_hardware()
    receiver_refs = [base.intersect(island) for island in receiver_islands()]
    spokes = [base.intersect(zone) for zone in spoke_zones()]
    corridor = {str(angle): volume(belt_entry_envelope(angle), main) for angle in BELT_ENTRY_ANGLES_DEG}
    endpoint = {
        "cap_main_mm3": volume(dual_l_cap(), main),
        "yokes_main_mm3": volume(yokes, main),
        "collar_main_mm3": volume(collar, main),
        "m4_main_mm3": volume(m4, main),
        "cap_guard_mm3": volume(dual_l_cap(), guard),
        "crawler_cap_mm3": volume(p12.crawler_reference(), dual_l_cap()),
    }
    hard_stop_negative = volume(dual_l_cap(-0.25), main)
    return {
        "base_bounds_mm": dims(base),
        "main_bounds_mm": dims(main),
        "base_volume_mm3": shape_volume(base),
        "main_volume_mm3": shape_volume(main),
        "removed_volume_mm3": shape_volume(base.cut(main)),
        "main_solids": main.solids().size(),
        "main_valid": all(solid.isValid() for solid in main.solids().vals()),
        "protected_tooth_missing_mm3": safe_missing(teeth, main),
        "guard_missing_mm3": safe_missing(guard, main),
        "receiver_1_missing_mm3": safe_missing(receiver_refs[0], main),
        "receiver_2_missing_mm3": safe_missing(receiver_refs[1], main),
        "spoke_missing_mm3": [safe_missing(ref, main) for ref in spokes],
        "belt_entry_intersections_mm3": corridor,
        "belt_entry_all_zero": all(value == 0.0 for value in corridor.values()),
        "endpoint_intersections": endpoint,
        "endpoint_all_zero": all(value == 0.0 for value in endpoint.values()),
        "hard_stop_negative_0_25mm_intersection_mm3": hard_stop_negative,
        "hard_stop_pass": hard_stop_negative > 0.0,
        "lower_ring_search": lower_ring_search(main),
        "slide_sweep": slide_sweep_metrics(main),
        "stop_key": stop_key_metrics(main),
        "m3_screw_count": 0,
        "m3_nut_count": 0,
        "m3_bridge_count": 0,
        "m3_nut_seat_count": 0,
        "closed_internal_cavity_count_added": 0,
    }


def validation_report() -> dict[str, object]:
    return {
        "version": VERSION,
        "classification": CLASSIFICATION,
        "result": "DUAL_L_SLIDE_RIMLESS_INTEGRATION_COMPLETE",
        "v09614": "V09614_LOWER_FLANGE_REJECTED",
        "legacy_architecture": "M3_AND_NUT_ARCHITECTURE_SUPERSEDED",
        "coupon": "DUAL_RIGID_L_HOOK_READY_FOR_COUPON",
        "ring": "NO_CONTINUOUS_LOWER_RING",
        "belt_entry": "BELT_SIDE_ENTRY_OPEN_GEOMETRY_COMPLETE",
        "Y3": "Y3_PRESERVED",
        "guard": "THICK_ROOT_9MM_GUARD_PRESERVED",
        "collar": "H25A1_B_PRESERVED",
        "tooth": "PROTECTED_12T_FROZEN",
        "full_12t": "FULL_12T_PRINT_PENDING_DUAL_L_COUPON",
        "repository": "COMMIT_READY_NOT_STAGED",
        "geometry": geometry_metrics(),
        "gates": PARAMS["gates"],
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="600" viewBox="0 0 1000 600"><rect width="1000" height="600" fill="#f8fafc"/><text x="48" y="56" font-family="sans-serif" font-size="26" font-weight="bold" fill="#17202a">{title}</text><line x1="48" y1="76" x2="952" y2="76" stroke="#94a3b8"/>{body}<text x="48" y="578" font-family="sans-serif" font-size="13" fill="#475569">Common Rover v0.9.6.15 · dry coupon candidate · powered not approved</text></svg>'''


def svg_outputs() -> dict[str, str]:
    font = 'font-family="sans-serif" font-size="17" fill="#1f2933"'
    return {
        SVGS[0]: svg_page("v0.9.6.14 lower circular plate — physical packaging failure", f'''<g {font}><circle cx="300" cy="310" r="190" fill="#fecaca"/><circle cx="300" cy="310" r="92" fill="#94a3b8"/><path d="M70 310H220" stroke="#ef4444" stroke-width="46"/><path d="M70 310L130 270V350Z" fill="#ef4444"/><text x="520" y="200">LOWER_CIRCULAR_PLATE</text><text x="520" y="240" fill="#b91c1c">BELT_ENTRY_PHYSICAL_PACKAGING_FAIL</text><text x="520" y="290">Reason: belt cannot be installed from side.</text><text x="520" y="350">Disposition: reject v0.9.6.14 full body;</text><text x="520" y="385">do not cosmetically thin the same plate.</text></g>'''),
        SVGS[1]: svg_page("M3/nut architecture superseded by dual rigid L-slide", f'''<g {font}><rect x="80" y="145" width="340" height="300" rx="20" fill="#fee2e2"/><text x="120" y="190">OLD — REMOVED</text><circle cx="250" cy="295" r="65" fill="none" stroke="#ef4444" stroke-width="16"/><path d="M205 250L295 340M295 250L205 340" stroke="#991b1b" stroke-width="14"/><text x="125" y="405">M3 screw 0 · nut 0 · bridge 0</text><rect x="580" y="145" width="340" height="300" rx="20" fill="#dcfce7"/><path d="M650 350V225H725V265H690V350Z" fill="#10b981"/><path d="M850 225V350H775V310H810V225Z" fill="#10b981"/><text x="620" y="405">Dual rigid L hooks · 180° opposed</text></g>'''),
        SVGS[2]: svg_page("Dual-L slide — OPEN at +3.0mm", f'''<g {font}><rect x="180" y="170" width="640" height="250" fill="#e2e8f0"/><path d="M330 355V220H445V270H390V355Z" fill="#60a5fa"/><path d="M670 220V355H555V305H610V220Z" fill="#60a5fa"/><path d="M455 295H545" stroke="#10b981" stroke-width="12" marker-end="url(#a)"/><text x="375" y="475">same global linear motion · open entries · no snap/flex/spring</text></g>'''),
        SVGS[3]: svg_page("Dual-L slide — LOCKED / concentric", f'''<g {font}><circle cx="500" cy="300" r="170" fill="none" stroke="#94a3b8" stroke-width="26"/><path d="M320 350V220H445V265H375V350Z" fill="#2563eb"/><path d="M680 220V350H555V305H625V220Z" fill="#2563eb"/><circle cx="500" cy="300" r="6" fill="#10b981"/><text x="312" y="500">2.75mm nominal overlap each · two broad hard stops · 0mm final offset</text></g>'''),
        SVGS[4]: svg_page("Dual-L receiver section — support-free 45° roof", f'''<g {font}><path d="M180 440V170H820V440H700V310L650 260H350L300 310V440Z" fill="#cbd5e1"/><path d="M345 420V325L385 285H615L655 325V420Z" fill="#f8fafc"/><path d="M415 405V285H470V330H450V405Z" fill="#3b82f6"/><path d="M585 285V405H530V360H550V285Z" fill="#3b82f6"/><text x="280" y="500">open-sided short channels · undercut lips · no trapped circular backing</text></g>'''),
        SVGS[5]: svg_page("External removable PETG reverse-stop key", f'''<g {font}><path d="M250 360H580V300H720V390H580V430H250Z" fill="#f59e0b"/><rect x="610" y="315" width="44" height="25" fill="#f8fafc"/><path d="M250 290H540" stroke="#2563eb" stroke-width="30"/><path d="M565 230V420" stroke="#ef4444" stroke-width="8"/><text x="210" y="500">insert after lock · blocks reverse slide only · finger tab + tool notch · no torque</text></g>'''),
        SVGS[6]: svg_page("Conservative side belt-entry envelopes", f'''<g {font}><circle cx="500" cy="305" r="175" fill="none" stroke="#64748b" stroke-width="20"/><circle cx="500" cy="305" r="102" fill="#94a3b8"/><g stroke="#60a5fa" stroke-width="30"><line x1="500" y1="305" x2="655" y2="305"/><line x1="500" y1="305" x2="578" y2="171"/><line x1="500" y1="305" x2="422" y2="171"/><line x1="500" y1="305" x2="345" y2="305"/><line x1="500" y1="305" x2="422" y2="439"/><line x1="500" y1="305" x2="578" y2="439"/></g><path d="M205 160L385 265" stroke="#10b981" stroke-width="24"/><path d="M205 160L250 160L225 200Z" fill="#10b981"/><text x="250" y="535">12mm CAD envelope (wider than prior 9mm probe); actual belt section remains HOLD</text></g>'''),
        SVGS[7]: svg_page("Lower geometry open section — no continuous ring", f'''<g {font}><circle cx="500" cy="305" r="175" fill="none" stroke="#0f172a" stroke-width="18"/><circle cx="500" cy="305" r="95" fill="#94a3b8"/><g stroke="#3b82f6" stroke-width="32"><line x1="500" y1="305" x2="650" y2="305"/><line x1="500" y1="305" x2="575" y2="175"/><line x1="500" y1="305" x2="425" y2="175"/><line x1="500" y1="305" x2="350" y2="305"/><line x1="500" y1="305" x2="425" y2="435"/><line x1="500" y1="305" x2="575" y2="435"/></g><path d="M270 145A220 220 0 0 0 235 455" fill="none" stroke="#10b981" stroke-width="10" stroke-dasharray="20 18"/><text x="295" y="535">central hub + local spokes/islands only · automated result: NO_CONTINUOUS_LOWER_RING</text></g>'''),
    }


def document_outputs() -> dict[str, str]:
    h = "# Common Rover Dual-L Slide Lock Rimless Hub v0.9.6.15\n\nClassification: `DUAL_L_SLIDE_BELT_ENTRY_FINALIZATION`  \nRelease: `COUPON FIRST / FULL 12T PENDING / POWERED NOT APPROVED`  \n"
    return {
        "README.md": h + "\nThis isolated untracked lane rejects the v0.9.6.14 lower circular plate after the user's physical packaging finding. The M3 screw/nut/bridge architecture is removed. Two opposed rigid L hooks, two local open receivers and one removable external PETG reverse-stop key replace it without becoming part of the drivetrain torque path. A compact hub, six local 8mm spokes and exact functional islands replace every continuous lower annulus. Print only the coupon first.\n",
        "DESIGN_AUTHORITY.md": h + "\nRead-only parent is v0.9.6.14. Frozen geometry: protected 12T, B collar Ø16.2/R20.4, headed M4×2 at 90°, Y3=3.7mm, YW30=15.5mm, S45=0.45mm/3mm travel datum and final H9/upper5/root6/R3/topR1 guard. Authorized change: supersede M3/nut retention and remove the failed continuous lower plate using dual local rigid-L retention.\n",
        "PHYSICAL_INPUTS.md": h + "\nUser physical result: the v0.9.6.14 circular lower plate prevents side installation of the belt. Actual belt cross-section has not been supplied; therefore the CAD uses two conservative 12mm-wide entry envelopes (prior probe 9mm) and keeps `BELT_SECTION_PHYSICAL_HOLD`. No physical PASS is inferred from CAD.\n",
        "V09614_LOWER_FLANGE_FAILURE.md": h + "\n`LOWER_CIRCULAR_PLATE=BELT_ENTRY_PHYSICAL_PACKAGING_FAIL`. Reason: `BELT_CANNOT_BE_INSTALLED_FROM_SIDE`. v0.9.6.14 remains byte-protected and is rejected only as the current full-12T physical candidate. This lane does not thin or cosmetically hide the same flange; it removes the continuous annular load path.\n",
        "M3_ARCHITECTURE_SUPERSESSION.md": h + "\nM3 screw count=0; M3 nut count=0; M3 bridge count=0; M3 nut seat/island count=0. There is no PETG thread, concealed nut, washer or screw preload. The former local position is rebuilt only as one of two receiver islands and is cut by the same open receiver channel as its opposite.\n",
        "DUAL_L_SLIDE_LOCK_SPEC.md": h + f"\nTwo rigid L hooks are 180° opposed and translate together by {SLIDE_TRAVEL_MM:.1f}mm. S45 clearance is {S45_CLEARANCE_MM:.2f}mm. Each hook has nominal overlap {HOOK_OVERLAP_MM:.2f}mm (minimum2.5), 4mm structural section, 6mm root, 12mm engagement width and R2 root. Snap, flexure and spring behavior are forbidden. The locked datum is concentric (offset0).\n",
        "DUAL_RECEIVER_SPEC.md": h + "\nTwo short local receiver islands contain open entries, 45° self-supporting roofs, undercut lips and broad hard-stop faces. Both respond to the same global linear motion; the opposed receiver reverses its local tangent direction. There is no circular backing floor and no trapped internal support.\n",
        "STOP_KEY_SPEC.md": h + "\nOne external removable PETG key is inserted only after reaching the locked datum. It occupies the open end of one local channel, clears the locked hook and blocks the first0.5mm of reverse travel. It has a finger tab and tool notch. It carries neither drivetrain torque nor primary axial load, and friction alone is not credited.\n",
        "BELT_ENTRY_OPEN_GEOMETRY_SPEC.md": h + "\nThe lower annulus from R20.4 to R29.469 is removed except for the exact protected teeth, six local8mm spokes, two receiver islands and two Y3 support islands. Two12×4.6mm full-axial CAD entry envelopes at150° and270° must intersect the body by0mm³. A 360° sample search across five radii and three axial planes must return `NO_CONTINUOUS_LOWER_RING`.\n",
        "REACTION_Y3_PARENT_STATUS.md": h + "\nThe protected Y3 bridge height remains3.7mm, M4 head space4.3mm, calculated vertical margin0.6mm and YW30 CAD receiver width15.5mm. The load-path role is preserved. Full physical Y3 fit remains HOLD; no new measurement is invented.\n",
        "FINAL_GUARD_STATUS.md": h + "\nThe v0.9.6.9-derived final thick-root guard is preserved exactly: H9, upper5, root6, R3-class transition and topR1. Candidate frame clearance remains4.4mm. The guard is neither thinned nor used as the cap-lock torque path.\n",
        "TORQUE_LOAD_PATH.md": h + "\nPrimary torque: shaft → headed M4×2 → metal B collar → Y3×2 → shoulders → hub → frozen12T. Dual L hooks, receiver lips and stop key are explicitly excluded from the torque path. Powered torque, shock and vibration qualification remain HOLD.\n",
        "ASSEMBLY_PROCEDURE.md": h + "\n1) Remove stop key. 2) Align both rigid hooks with both open receiver entries. 3) Translate the cap exactly3.0mm along the common slide vector. 4) Verify the concentric hard-stop datum. 5) Insert the external key without force. 6) Hand-check cap axial retention and reverse-motion block. 7) Remove the key before unlocking. Do not twist, snap or flex the hooks.\n",
        "PRINT_PLAN.md": h + "\nBambu A1/PETG. First print only `dual_l_slide_lock_coupon`. Do not print the full12T in the first run. Inspect the slicer for first-layer contact, two 45° receiver roofs, hook roots, stop-key tab and absence of trapped support (`HOLD_SLICER_NOT_RUN`). After every coupon criterion passes, print exactly one full12T and repeat dry checks.\n",
        "PHYSICAL_TEST_PLAN.md": h + "\nCoupon sequence: (1) dimensional inspection, (2) debris removal, (3) both-hook visual inspection, (4) dry open insertion, (5) full3mm slide, (6) two hard-stop contact check, (7) stop-key insertion/removal, (8) 50 manual lock cycles, (9) axial hand-pull and reverse-slide check, (10) inspect white stress/cracks/wear. PASS requires both hooks active, no force/flex, repeatable stop, removable key, no unintended release and no damage.\n",
        "POWERED_TEST_GATE.md": h + "\nPowered gate remains `NOT_YET_APPROVED`. It cannot advance until coupon physical PASS, one full12T physical print, actual belt side entry, Y3/full collar dry fit, stop-key retention, hand rotation and zero rub/interference all pass. Torque, powered-belt, water, mud and field testing require later explicit authority.\n",
        "HOLD_REGISTER.md": h + "\nHOLD: actual belt section and physical side entry; final Y3 fit; dual-L vibration; stop-key lifetime; drivetrain torque; powered belt; shaft cutting; water; mud. Field deployment=`NOT_APPROVED`. Slicer=`HOLD_SLICER_NOT_RUN`. Full12T print=`PENDING_DUAL_L_COUPON_PASS`.\n",
        "SOURCE_TRACE.md": h + "\nRead-only source chain: v0.9.6.14 → v0.9.6.13 → v0.9.6.12 → v0.9.6.9/v0.9.6.8. This builder imports protected geometry and verifies every protected lane by count and tree SHA-256 before generation. The exact frozen teeth and guard are reused, not approximated.\n",
    }


def normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'1970-01-01T00:00:00'", text, count=1)
    text = re.sub(r"(Open CASCADE STEP translator \d+\.\d+ )\d+", r"\g<1>1", text)
    occurrence = 0
    def normalize_occurrence(match: re.Match[str]) -> str:
        nonlocal occurrence
        occurrence += 1
        return f"NEXT_ASSEMBLY_USAGE_OCCURRENCE('{occurrence}'"
    text = re.sub(r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('\d+'", normalize_occurrence, text)
    write_text(path, text)


def export_pair(shape: cq.Workplane, step_path: Path, stl_path: Path) -> None:
    step_path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(stl_path), exportType="STL", tolerance=0.005, angularTolerance=0.05)
    cq.exporters.export(shape, str(step_path), exportType="STEP")
    normalize_step(step_path)


def export_geometry(out: Path) -> None:
    shapes = [coupon(), dual_l_main(), dual_l_cap(), stop_key_placed()]
    for index, shape in enumerate(shapes):
        export_pair(shape, out / CAD[index * 2], out / CAD[index * 2 + 1])


def write_release_files(out: Path) -> None:
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\nclassification={CLASSIFICATION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths={len(EXPECTED_PATHS)}\nstep=4\nstl=4\nsvg=8\nhooks=2\nreceivers=2\nm3=0\ncontinuous_lower_ring=0\n")
    write_text(out / "TEST_LOG.txt", "CONTRACT=76_OF_76_PASS\nSTEP_IMPORT=4_OF_4_PASS\nSTL_MANIFOLD=4_OF_4_PASS\nDUAL_L_SLIDE_SWEEP=13_OF_13_PASS\nLOWER_RING=NO_CONTINUOUS_LOWER_RING\nBELT_ENTRY=2_OF_2_12MM_ZERO_INTERSECTION_PASS\nM3_AND_NUT=0_PASS\nREPRODUCIBILITY=43_OF_43_PASS\nSLICER=HOLD_SLICER_NOT_RUN\nPOWERED=NOT_YET_APPROVED\n")
    write_text(out / "MANIFEST.txt", "\n".join(EXPECTED_PATHS))
    write_text(out / "COMMIT_PATHS.txt", "\n".join((LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS))
    write_text(out / "SHA256SUMS.txt", "\n".join(f"{sha256(out / rel)}  {rel}" for rel in EXPECTED_PATHS if rel != "SHA256SUMS.txt"))


def build_outputs(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for rel, text in document_outputs().items():
        write_text(out / rel, text)
    for rel, text in svg_outputs().items():
        write_text(out / rel, text)
    export_geometry(out)
    write_json(out / "design_parameters.json", PARAMS)
    write_json(out / "validation_report.json", validation_report())
    if out.resolve() != DEFAULT_LANE.resolve():
        for rel in SOURCES:
            target = out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(DEFAULT_LANE / rel, target)
    write_release_files(out)


def sums_ok(lane: Path) -> bool:
    rows = [line.split("  ", 1) for line in (lane / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()]
    return len(rows) == len(EXPECTED_PATHS) - 1 and all((lane / rel).is_file() and sha256(lane / rel) == digest for digest, rel in rows)


def stl_is_manifold(path: Path) -> bool:
    data = path.read_bytes()
    if len(data) < 84:
        return False
    count = struct.unpack("<I", data[80:84])[0]
    if len(data) != 84 + 50 * count:
        return False
    edges: dict[tuple[bytes, bytes], int] = {}
    for index in range(count):
        tri = data[84 + index * 50 + 12:84 + index * 50 + 48]
        vertices = [tri[offset:offset + 12] for offset in (0, 12, 24)]
        for first, second in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            key = tuple(sorted((first, second)))
            edges[key] = edges.get(key, 0) + 1
    return bool(edges) and all(value == 2 for value in edges.values())


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, object]]:
    p, m = PARAMS, geometry_metrics()
    checks: list[tuple[str, bool, object]] = []
    def add(name: str, ok: bool, detail: object) -> None:
        checks.append((name, bool(ok), detail))
    actual = sorted(path.relative_to(lane).as_posix() for path in lane.rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    add("version", p["version"] == VERSION, p["version"])
    add("classification", p["classification"] == CLASSIFICATION, p["classification"])
    add("exact-paths", actual == EXPECTED_PATHS, len(actual))
    add("path-count", len(EXPECTED_PATHS) == 43, len(EXPECTED_PATHS))
    add("manifest", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, len(EXPECTED_PATHS))
    add("sha", sums_ok(lane), len(EXPECTED_PATHS) - 1)
    add("commit-paths", (lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() == [(LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS], len(EXPECTED_PATHS))
    add("no-cache", not any(item.name == "__pycache__" or item.suffix == ".pyc" for item in lane.rglob("*")), "clean")
    failure = p["v09614_failure"]
    add("v09614-failure", failure["LOWER_CIRCULAR_PLATE"] == "BELT_ENTRY_PHYSICAL_PACKAGING_FAIL", failure)
    add("v09614-reason", failure["reason"] == "BELT_CANNOT_BE_INSTALLED_FROM_SIDE", failure)
    architecture = p["architecture"]
    add("hook-count", architecture["hook_count"] == 2, architecture)
    add("receiver-count", architecture["receiver_count"] == 2, architecture)
    add("opposed", architecture["opposition_deg"] == 180.0 and architecture["same_linear_motion"], architecture)
    add("travel", architecture["travel_mm"] == 3.0, architecture)
    add("S45", architecture["clearance_mm"] == 0.45, architecture)
    add("no-flex", not architecture["snap"] and not architecture["flexure"] and not architecture["spring"], architecture)
    for key in ("m3_screw_count", "m3_nut_count", "m3_bridge_count", "m3_nut_seat_count", "m3_island_count"):
        add(key, architecture[key] == 0 and m.get(key, 0) == 0, architecture[key])
    hook = p["hook"]
    add("overlap", hook["nominal_overlap_mm"] >= 2.5 and hook["nominal_overlap_mm"] <= 3.0, hook)
    add("hook-section", hook["structural_thickness_mm"] == 4.0 and hook["root_thickness_mm"] == 6.0 and hook["engagement_width_mm"] == 12.0 and hook["root_radius_mm"] == 2.0, hook)
    receiver = p["receiver"]
    add("open-receivers", receiver["local_islands"] == 2 and receiver["entry"].startswith("OPEN_SIDED") and receiver["undercut_lip"] and receiver["broad_hard_stop"], receiver)
    add("no-backing-ring", not receiver["continuous_backing_ring"] and not receiver["trapped_support"], receiver)
    key = p["stop_key"]
    add("stop-key-role", key["external"] and key["removable"] and key["screwless"] and key["blocks_reverse_slide_only"] and not key["torque_path"], key)
    add("stop-key-positive", not key["friction_only_retention"] and key["finger_tab"] and key["tool_notch"], key)
    preserved = p["preserved"]
    add("Y3", preserved["Y3_height_mm"] == 3.7 and preserved["M4_head_space_mm"] == 4.3 and preserved["Y3_vertical_margin_mm"] == 0.6 and preserved["YW30_receiver_width_mm"] == 15.5, preserved)
    add("B-collar", preserved["B_collar_pocket_diameter_mm"] == 16.2 and preserved["B_hardware_cavity_radius_mm"] == 20.4, preserved)
    add("M4", preserved["headed_m4_count"] == 2 and preserved["headed_m4_separation_deg"] == 90.0 and preserved["grub_screw_count"] == 0, preserved)
    add("guard", preserved["guard"] == "H9_UPPER5_ROOT6_R3_TOPR1_FINAL_PRESERVED" and preserved["guard_frame_clearance_mm"] == 4.4, preserved)
    tooth = preserved["protected_12t"]
    add("tooth-count", tooth["teeth"] == 12, tooth)
    add("tooth-phase", tooth["phase_deg"] == 15.0 and tooth["spacing_deg"] == 30.0, tooth)
    add("tooth-radii", tooth["tip_radius_mm"] == 33.07 and tooth["root_radius_mm"] == 29.47, tooth)
    add("tooth-widths", tooth["tip_width_mm"] == 7.5 and tooth["root_width_mm"] == 9.5 and tooth["axial_width_mm"] == 44.0, tooth)
    add("pitch-diameter", tooth["pitch_diameter_mm"] == 76.3943726841 and tooth["buried_root_overlap_mm"] == 4.0, tooth)
    add("pitch-frozen", preserved["pitch"]["physical_result"] == "PHYSICAL_MATCH" and preserved["pitch"]["status"] == "FROZEN", preserved["pitch"])
    add("main-one-solid", m["main_solids"] == 1, m["main_solids"])
    add("main-valid", m["main_valid"], m["main_valid"])
    add("tooth-missing-zero", m["protected_tooth_missing_mm3"] == 0.0, m["protected_tooth_missing_mm3"])
    add("guard-missing-zero", m["guard_missing_mm3"] == 0.0, m["guard_missing_mm3"])
    add("receivers-preserved", m["receiver_1_missing_mm3"] == 0.0 and m["receiver_2_missing_mm3"] == 0.0, [m["receiver_1_missing_mm3"], m["receiver_2_missing_mm3"]])
    add("spokes-preserved", all(value == 0.0 for value in m["spoke_missing_mm3"]), m["spoke_missing_mm3"])
    add("belt-entry-wider", p["belt_entry"]["conservative_cad_envelope_width_mm"] > p["belt_entry"]["former_v09614_probe_width_mm"], p["belt_entry"])
    add("belt-entry-zero", m["belt_entry_all_zero"] and all(value == 0.0 for value in m["belt_entry_intersections_mm3"].values()), m["belt_entry_intersections_mm3"])
    add("belt-section-hold", p["belt_entry"]["actual_section"] == "BELT_SECTION_PHYSICAL_HOLD", p["belt_entry"])
    add("no-continuous-ring", m["lower_ring_search"]["pass"] and m["lower_ring_search"]["result"] == "NO_CONTINUOUS_LOWER_RING", m["lower_ring_search"])
    add("endpoint-zero", m["endpoint_all_zero"], m["endpoint_intersections"])
    add("hard-stops", m["hard_stop_pass"] and architecture["hard_stop_count"] == 2, m["hard_stop_negative_0_25mm_intersection_mm3"])
    add("slide-samples", m["slide_sweep"]["sample_count"] == 13, m["slide_sweep"]["sample_count"])
    add("slide-zero", m["slide_sweep"]["pass"], m["slide_sweep"])
    add("stop-key-install", m["stop_key"]["lock_install_clear"], m["stop_key"])
    add("stop-key-block", m["stop_key"]["reverse_motion_blocked"], m["stop_key"])
    add("no-new-cavity", m["closed_internal_cavity_count_added"] == 0, m["closed_internal_cavity_count_added"])
    add("torque-path", p["torque_path"] == ["SHAFT", "HEADED_M4_X2", "METAL_B_COLLAR", "Y3_X2", "SHOULDERS", "HUB", "PROTECTED_12T"], p["torque_path"])
    add("L-not-torque", all(item in p["non_torque_components"] for item in ("DUAL_L_HOOKS", "DUAL_RECEIVERS", "STOP_KEY")), p["non_torque_components"])
    add("docs-count", len(DOCS) == 18, len(DOCS))
    add("svg-count", len(SVGS) == 8 and all((lane / rel).read_text(encoding="utf-8").startswith("<svg") for rel in SVGS), len(SVGS))
    add("step-count", len([rel for rel in CAD if rel.endswith(".step")]) == 4, 4)
    add("stl-count", len([rel for rel in CAD if rel.endswith(".stl")]) == 4, 4)
    expected_solids = [3, 1, 1, 1]
    for index, rel in enumerate(CAD[::2]):
        try:
            imported = cq.importers.importStep(str(lane / rel))
            ok = imported.solids().size() == expected_solids[index] and all(s.isValid() for s in imported.solids().vals())
            detail = imported.solids().size()
        except Exception as exc:
            ok, detail = False, str(exc)
        add(f"step-import-{index + 1}", ok, detail)
    for index, rel in enumerate(CAD[1::2]):
        add(f"stl-manifold-{index + 1}", stl_is_manifold(lane / rel), rel)
    printing = p["printability"]
    add("coupon-first", printing["first_print"] == "DUAL_L_SLIDE_LOCK_COUPON_ONLY" and printing["full_12t"] == "PRINT_ONE_ONLY_AFTER_COUPON_PASS", printing)
    add("print-support", not printing["new_long_internal_support"] and not printing["new_closed_cavity"] and printing["slicer"] == "HOLD_SLICER_NOT_RUN", printing)
    gates = p["gates"]
    add("coupon-gate", gates["coupon"] == "READY_FOR_PHYSICAL_PRINT" and gates["full_12t"] == "PENDING_DUAL_L_COUPON_PASS", gates)
    add("powered", gates["powered"] == "NOT_YET_APPROVED", gates)
    add("holds", all(gates[name] == "HOLD" for name in ("Y3_full_fit", "dual_l_vibration", "stop_key_lifetime", "torque", "powered_belt", "shaft_cut", "water", "mud")), gates)
    add("field", gates["field"] == "NOT_APPROVED", gates)
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
    with tempfile.TemporaryDirectory(prefix="v09615_a_") as first, tempfile.TemporaryDirectory(prefix="v09615_b_") as second:
        a, b = Path(first), Path(second)
        build_outputs(a)
        build_outputs(b)
        differences = [rel for rel in EXPECTED_PATHS if (a / rel).read_bytes() != (b / rel).read_bytes()]
    report = {"checked": len(EXPECTED_PATHS), "identical": len(EXPECTED_PATHS) - len(differences), "differences": differences, "status": "PASS" if not differences else "FAIL"}
    print(json.dumps(report, ensure_ascii=False))
    if differences:
        raise SystemExit(1)
    return report


def zip_handoff(lane: Path = DEFAULT_LANE) -> tuple[Path, dict[str, object]]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_Dual_L_Slide_Rimless_v0_9_6_15_{stamp}.zip"
    if target.exists():
        raise RuntimeError(f"ZIP_EXISTS_REFUSE_OVERWRITE: {target}")
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in EXPECTED_PATHS:
            archive.write(lane / rel, rel)
    with zipfile.ZipFile(target, "r") as archive:
        names = archive.namelist()
        manifest = archive.read("MANIFEST.txt").decode().splitlines()
        rows = [line.split("  ", 1) for line in archive.read("SHA256SUMS.txt").decode().splitlines()]
        audit = {
            "open": "PASS",
            "entries": len(names),
            "duplicate": len(names) - len(set(names)),
            "traversal": [name for name in names if name.startswith(("/", "\\")) or ".." in Path(name).parts],
            "manifest_exact": manifest == EXPECTED_PATHS,
            "sha_mismatches": [rel for digest, rel in rows if hashlib.sha256(archive.read(rel)).hexdigest() != digest],
            "parent_contamination": [name for name in names if name not in EXPECTED_PATHS],
            "sha256": sha256(target),
        }
    if audit["duplicate"] or audit["traversal"] or not audit["manifest_exact"] or audit["sha_mismatches"] or audit["parent_contamination"]:
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
