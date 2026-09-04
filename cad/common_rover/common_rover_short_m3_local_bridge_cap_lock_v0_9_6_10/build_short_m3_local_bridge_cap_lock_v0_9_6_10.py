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


VERSION = "v0.9.6.10"
CLASSIFICATION = "SHORT_M3_LOCAL_BRIDGE_CAP_LOCK_CORRECTION"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_short_m3_local_bridge_cap_lock_v0_9_6_10")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 2041
BASE_OUTSIDE_DIGEST = "edf780fa62ce99c8e24acee1c9dd1fa179a4c397306de6a8ab0661a93b8c8649"
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

PARENT_BUILDER = REPO_ROOT / "cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9/build_reinforced_guard_reaction_yoke_v0_9_6_9.py"
_spec = importlib.util.spec_from_file_location("v0969_parent", PARENT_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load protected parent: {PARENT_BUILDER}")
parent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = parent
_spec.loader.exec_module(parent)

PROTECTED_LANES = dict(parent.PROTECTED_LANES)
PROTECTED_LANES["v0.9.6.9"] = (
    "cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9",
    54,
    "5df591b85bb4f93148b162c1e92ac6bf30a45a5d523a785a9b7f8f5ba19cf479",
)

DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_INPUTS.md",
    "M3_SHORT_HARDWARE_AUTHORITY.md", "V0969_FULL_THROUGHBOLT_FAILURE.md",
    "LOCAL_BRIDGE_CAP_LOCK_SPEC.md", "LOCAL_BRIDGE_LOAD_PATH.md",
    "REAR_SERVICE_WINDOW_SPEC.md", "SHORT_M3_STACK_BUDGET.md",
    "REACTION_YOKE_PARENT_STATUS.md", "REINFORCED_GUARD_PARENT_STATUS.md",
    "TORQUE_LOAD_PATH.md", "ASSEMBLY_PROCEDURE.md", "PRINT_PLAN.md",
    "PHYSICAL_TEST_PLAN.md", "POWERED_TEST_GATE.md", "SAFETY_NOTES.md",
    "HOLD_REGISTER.md", "SOURCE_TRACE.md",
]
CAD = [
    "drive/artifacts/drive_12t_h25a1_short_m3_bridge_v0_9_6_10.step",
    "drive/artifacts/drive_12t_h25a1_short_m3_bridge_v0_9_6_10.stl",
    "hub_cap/artifacts/h25a1_short_m3_bridge_cap_v0_9_6_10.step",
    "hub_cap/artifacts/h25a1_short_m3_bridge_cap_v0_9_6_10.stl",
    "local_bridge/artifacts/short_m3_local_bridge_coupon_v0_9_6_10.step",
    "local_bridge/artifacts/short_m3_local_bridge_coupon_v0_9_6_10.stl",
    "integration/artifacts/short_m3_local_bridge_full_assembly_v0_9_6_10.step",
]
SVGS = [f"integration/artifacts/{name}" for name in (
    "m3_20p5_stack_budget_v0_9_6_10.svg",
    "full44mm_through_vs_local_bridge_v0_9_6_10.svg",
    "local_bridge_section_v0_9_6_10.svg",
    "local_bridge_b7_b8_b9_v0_9_6_10.svg",
    "rear_nut_service_window_v0_9_6_10.svg",
    "local_bridge_load_path_v0_9_6_10.svg",
    "reaction_yoke_plus_bridge_clearance_v0_9_6_10.svg",
    "full_hub_section_v0_9_6_10.svg",
)]
JSONS = ["design_parameters.json", "validation_report.json"]
SOURCES = ["build_short_m3_local_bridge_cap_lock_v0_9_6_10.py", "tests/test_short_m3_local_bridge_cap_lock_v0_9_6_10_contract.py"]
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
PARAMS = {
    "version": VERSION,
    "classification": CLASSIFICATION,
    "units": "mm",
    "m3_physical": {
        "under_head_usable_length_mm": 20.5,
        "overall_reference_mm": 27.9,
        "status": "MEASURED_USER_PHYSICAL_AUTHORITY",
        "available_for_immediate_prototype": True,
        "longer_hypothetical_screw_assumed": False,
    },
    "v0969_full_body_throughbolt": {
        "status": "GEOMETRICALLY_IMPOSSIBLE_WITH_AVAILABLE_M3",
        "classification": "SUPERSEDED_BEFORE_PHYSICAL_ACCEPTANCE",
        "full_body_through": False,
        "body_mm": 44.0,
        "cap_mm": 5.5,
        "minimum_petg_only_mm": 49.5,
        "shortfall_before_rear_hardware_mm": 29.0,
    },
    "local_bridge": {
        "architecture": "SHORT_M3_LOCAL_THROUGH_BOLT_WITH_OPEN_REAR_SERVICE_WINDOW",
        "count": 2,
        "variants_mm": {"B7": 7.0, "B8": 8.0, "B9": 9.0},
        "design_primary": "B8",
        "design_primary_mm": 8.0,
        "cap_mm": 5.5,
        "petg_stack_mm": {"B7": 12.5, "B8": 13.5, "B9": 14.5},
        "remaining_hardware_budget_mm": {"B7": 8.0, "B8": 7.0, "B9": 6.0},
        "preferred_petg_stack_max_mm": 14.5,
        "absolute_petg_stack_max_mm": 15.5,
        "root_fillet_mm": 2.5,
        "root_fillet_class": "R2P5_CLASS_LARGEST_COLLISION_FREE",
        "broad_pad_mm": [15.0, 15.0],
        "thin_cantilever": False,
        "integrated_with_one_piece_hub": True,
        "primary_torque_path": False,
        "physical_selection": "THICKEST_SAFE_FUNCTIONAL_BRIDGE_PENDING",
    },
    "service_window": {
        "count": 2,
        "open_to_rear": True,
        "diameter_mm": 12.4,
        "depth_to_bridge_mm": 30.5,
        "rear_nut_visible": True,
        "rear_nut_accessible": True,
        "rear_nut_removable": True,
        "hidden_cavity": False,
        "tool_reference_diameter_mm": 11.2,
        "clearance_status": "CAD_REFERENCE_PASS_PHYSICAL_HOLD",
    },
    "fastener": {
        "count": 2,
        "angles_deg": [45.0, 225.0],
        "pcd_mm": 46.0,
        "hole_diameter_mm": 3.4,
        "front_heads": True,
        "front_washer_candidate": True,
        "rear_washers": True,
        "rear_nuts": True,
        "rear_nuts_accessible": True,
        "hidden_captive_nut": False,
        "petg_thread": False,
        "full_44mm_throughbolt": False,
        "snap": False,
        "adhesive": False,
        "exact_nut_and_washer": "HOLD_PHYSICAL_MEASUREMENT",
        "thread_engagement": "PHYSICAL_PENDING_FULL_NUT_ENGAGEMENT_REQUIRED",
        "primary_torque_path": False,
    },
    "cap": {
        "outer_diameter_mm": 54.0,
        "thickness_mm": 5.5,
        "broad_seating": True,
        "snap_fingers": 0,
        "role": "YOKE_CONTAINMENT_LOAD_SPREAD_DEBRIS_EXCLUSION_CANDIDATE_CAP_RETENTION",
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
    "envelopes": {
        "protected_sprocket_body_axial_mm": 44.0,
        "petg_rotating_axial_mm": 48.0,
        "m3_hardware_axial_mm": 27.9,
        "full_assembly_axial_mm": 55.4,
        "rear_nut_inside_44mm_claim": False,
    },
    "gates": {
        "local_bridge_coupon": "READY_FOR_PHYSICAL_COUPON",
        "reaction_yoke": "PHYSICAL_PASS_REQUIRED",
        "full_12t": "PRINT_PENDING_YOKE_AND_LOCAL_BRIDGE_COUPON",
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


def local_bridge_rear_z(thickness_mm: float = 8.0) -> float:
    return 16.5 - thickness_mm


def short_m3_holes(thickness_mm: float = 8.0) -> list[cq.Workplane]:
    z0 = local_bridge_rear_z(thickness_mm) - 0.2
    return [cylinder(1.7, 8.4, z0).translate((*center_xy(23.0, angle), 0)) for angle in (45.0, 225.0)]


def service_windows(thickness_mm: float = 8.0) -> list[cq.Workplane]:
    z_top = local_bridge_rear_z(thickness_mm)
    result = []
    for angle in (45.0, 225.0):
        x, y = center_xy(23.0, angle)
        core = cylinder(6.2, z_top + 22.2, -22.2).translate((x, y, 0))
        # The tapered crown is the conservative CAD representation of the
        # selected R2.5-class broad bridge root; actual print is coupon-gated.
        crown = cq.Workplane(obj=cq.Solid.makeCone(6.2, 5.7, 2.5, cq.Vector(x, y, z_top - 2.5), cq.Vector(0, 0, 1)))
        result.append(core.union(crown).clean())
    return result


def main_sprocket() -> cq.Workplane:
    part = parent.parent.protected_blank()
    voids = [
        cylinder(5.15, 46.0, -23.0),
        cylinder(8.1, 24.0, -2.0),
        box(40.8, 9.2, 26.6, (0, 0, 8.7)),
        box(9.2, 40.8, 26.6, (0, 0, 8.7)),
        cylinder(27.2, 5.7, 16.5),
        parent.yoke_pocket(),
        parent.yoke_pocket().rotate((0, 0, 0), (0, 0, 1), 90),
        *short_m3_holes(8.0),
        *service_windows(8.0),
    ]
    for void in compound(voids).solids().vals():
        part = part.cut(cq.Workplane(obj=void))
    return part.union(parent.reinforced_guard()).clean()


def cap() -> cq.Workplane:
    return parent.cap()


def short_m3_hardware(thickness_mm: float = 8.0) -> cq.Workplane:
    rear_z = local_bridge_rear_z(thickness_mm)
    parts = []
    for angle in (45.0, 225.0):
        x, y = center_xy(23.0, angle)
        shaft = cylinder(1.5, 20.5, 1.5).translate((x, y, 0))
        head_and_front_washer_reference = cylinder(3.6, 7.4, 22.0).translate((x, y, 0))
        rear_washer = parent.parent.m3_washer_reference().translate((x, y, rear_z - 0.5))
        rear_nut = parent.parent.m3_nut_reference().translate((x, y, rear_z - 2.9))
        parts.extend([shaft, head_and_front_washer_reference, rear_washer, rear_nut])
    return compound(parts)


def rear_tool_envelope(thickness_mm: float = 8.0) -> cq.Workplane:
    z_top = local_bridge_rear_z(thickness_mm)
    return compound([cylinder(5.6, z_top + 24.0, -24.0).translate((*center_xy(23.0, angle), 0)) for angle in (45.0, 225.0)])


def bridge_reference(thickness_mm: float = 8.0) -> cq.Workplane:
    rear_z = local_bridge_rear_z(thickness_mm)
    pads = []
    for angle in (45.0, 225.0):
        x, y = center_xy(23.0, angle)
        pad = box(15.0, 15.0, thickness_mm, (x, y, rear_z + thickness_mm / 2.0))
        pad = pad.cut(cylinder(1.7, thickness_mm + 0.4, rear_z - 0.2).translate((x, y, 0)))
        pads.append(pad.clean())
    return compound(pads)


def label_geometry(digit: int, z0: float) -> cq.Workplane:
    # Deterministic embossed B7/B8/B9 marks without relying on host fonts.
    t, d, h = 0.55, 0.6, 4.8
    parts = [
        box(t, h, d, (-5.5, 0, z0 + d / 2)),
        box(3.0, t, d, (-4.0, 2.1, z0 + d / 2)),
        box(3.0, t, d, (-4.0, 0, z0 + d / 2)),
        box(3.0, t, d, (-4.0, -2.1, z0 + d / 2)),
        box(t, 2.1, d, (-2.5, 1.05, z0 + d / 2)),
        box(t, 2.1, d, (-2.5, -1.05, z0 + d / 2)),
    ]
    segments = {
        7: ("top", "ur", "lr"),
        8: ("top", "mid", "bot", "ul", "ur", "ll", "lr"),
        9: ("top", "mid", "ul", "ur", "lr"),
    }[digit]
    x0 = 3.0
    shapes = {
        "top": box(3.0, t, d, (x0, 2.1, z0 + d / 2)),
        "mid": box(3.0, t, d, (x0, 0, z0 + d / 2)),
        "bot": box(3.0, t, d, (x0, -2.1, z0 + d / 2)),
        "ul": box(t, 2.1, d, (x0 - 1.5, 1.05, z0 + d / 2)),
        "ur": box(t, 2.1, d, (x0 + 1.5, 1.05, z0 + d / 2)),
        "ll": box(t, 2.1, d, (x0 - 1.5, -1.05, z0 + d / 2)),
        "lr": box(t, 2.1, d, (x0 + 1.5, -1.05, z0 + d / 2)),
    }
    return fused(parts + [shapes[name] for name in segments]).clean()


def coupon_body(thickness_mm: float, digit: int) -> tuple[cq.Workplane, cq.Workplane]:
    # Body spans rear-open z=-10 to bridge front z=t. The axial window opens
    # directly to the print's rear face and ends at the bridge seating face.
    body = box(30.0, 24.0, thickness_mm + 10.0, (0, 0, (thickness_mm - 10.0) / 2.0))
    window = cylinder(6.2, 10.2, -10.2)
    body = body.cut(window).cut(cylinder(1.7, thickness_mm + 0.4, -0.2))
    cap_part = box(30.0, 24.0, 5.5, (0, 0, thickness_mm + 2.75))
    cap_part = cap_part.cut(cylinder(1.7, 5.9, thickness_mm - 0.2)).cut(cylinder(3.6, 3.7, thickness_mm + 1.8))
    cap_part = cap_part.union(label_geometry(digit, thickness_mm + 5.5)).clean()
    return body.clean(), cap_part


def bridge_coupon() -> cq.Workplane:
    parts = []
    for offset, thickness, digit in zip((-42.0, 0.0, 42.0), (7.0, 8.0, 9.0), (7, 8, 9)):
        body, cap_part = coupon_body(thickness, digit)
        parts.append(body.translate((offset, -18.0, 0)))
        parts.append(cap_part.translate((offset, 20.0, -thickness)))
    return compound(parts)


def full_assembly() -> cq.Workplane:
    yokes = parent.installed_yokes(3.5)
    shaft = cylinder(5.0, 70.0, -35.0)
    spacer = parent.parent.spacer_8().translate((0, 0, -34.0))
    kp000 = box(67.0, 35.0, 17.0, (0, 0, -44.5)).cut(cylinder(8.0, 17.4, -53.2))
    frame = box(92.0, 92.0, 0.4, (0, 0, -30.6))
    return compound([main_sprocket(), cap(), *yokes, parent.parent.m4_hardware(), short_m3_hardware(), rear_tool_envelope(), shaft, spacer, kp000, frame])


GEOMETRIES: dict[str, tuple[object, bool]] = {
    "drive/artifacts/drive_12t_h25a1_short_m3_bridge_v0_9_6_10": (main_sprocket, True),
    "hub_cap/artifacts/h25a1_short_m3_bridge_cap_v0_9_6_10": (cap, True),
    "local_bridge/artifacts/short_m3_local_bridge_coupon_v0_9_6_10": (bridge_coupon, True),
    "integration/artifacts/short_m3_local_bridge_full_assembly_v0_9_6_10": (full_assembly, False),
}


def protected_external_missing_mm3() -> float:
    source = parent.parent.protected_blank()
    external = source.cut(cylinder(29.469, 44.4, -22.2))
    retained = main_sprocket().intersect(external)
    return round(max(0.0, float(external.val().Volume()) - float(retained.val().Volume())), 6)


def geometry_metrics() -> dict[str, object]:
    main = main_sprocket()
    cap_part = cap()
    yoke_a, yoke_b = parent.installed_yokes(3.5)
    m4 = parent.parent.m4_hardware()
    m3 = short_m3_hardware()
    tool = rear_tool_envelope()
    guard = parent.reinforced_guard()
    coupon = bridge_coupon()
    spacer = parent.parent.spacer_8().translate((0, 0, -34.0))
    kp000 = box(67.0, 35.0, 17.0, (0, 0, -44.5)).cut(cylinder(8.0, 17.4, -53.2))
    frame = box(92.0, 92.0, 0.4, (0, 0, -30.6))
    return {
        "main_bounds_mm": dims(main),
        "main_solids": main.solids().size(),
        "protected_external_missing_mm3": round(protected_external_missing_mm3(), 6),
        "petg_rotating_axial_mm": dims(main)[2],
        "m3_hardware_axial_mm": dims(m3)[2],
        "total_assembly_axial_mm": round(max(main.val().BoundingBox().zmax, m3.val().BoundingBox().zmax) - min(main.val().BoundingBox().zmin, m3.val().BoundingBox().zmin), 3),
        "cap_bounds_mm": dims(cap_part),
        "coupon_solids": coupon.solids().size(),
        "coupon_all_valid": all(s.isValid() for s in coupon.solids().vals()),
        "bridge_reference_solids": bridge_reference().solids().size(),
        "m3_main_intersection_mm3": volume(m3, main),
        "m3_cap_intersection_mm3": volume(m3, cap_part),
        "m3_m4_intersection_mm3": volume(m3, m4),
        "m3_yoke_a_intersection_mm3": volume(m3, yoke_a),
        "m3_yoke_b_intersection_mm3": volume(m3, yoke_b),
        "m3_guard_intersection_mm3": volume(m3, guard),
        "tool_main_intersection_mm3": volume(tool, main),
        "tool_cap_intersection_mm3": volume(tool, cap_part),
        "tool_m4_intersection_mm3": volume(tool, m4),
        "tool_yoke_a_intersection_mm3": volume(tool, yoke_a),
        "tool_yoke_b_intersection_mm3": volume(tool, yoke_b),
        "tool_guard_intersection_mm3": volume(tool, guard),
        "tool_spacer_intersection_mm3": volume(tool, spacer),
        "tool_kp000_intersection_mm3": volume(tool, kp000),
        "tool_frame_intersection_mm3": volume(tool, frame),
        "guard_parent_volume_difference_mm3": round(float(guard.val().Volume()) - float(parent.reinforced_guard().val().Volume()), 6),
        "yoke_parent_volume_difference_mm3": 0.0,
        "cap_parent_volume_difference_mm3": round(float(cap_part.val().Volume()) - float(parent.cap().val().Volume()), 6),
        "all_primary_valid": all(all(s.isValid() for s in obj.solids().vals()) for obj in [main, cap_part, coupon, full_assembly()]),
    }


def collision_report() -> dict[str, object]:
    m = geometry_metrics()
    keys = [key for key in m if key.endswith("intersection_mm3")]
    return {
        "method": "CADQUERY_COMMON_VOLUME_SHORT_M3_LOCAL_BRIDGE_AND_REAR_SERVICE_WINDOW",
        "known_unintended": {key: m[key] for key in keys},
        "known_all_zero": all(m[key] == 0.0 for key in keys),
        "intended_contacts_excluded": ["CAP_TO_HUB_SEAT", "REAR_WASHER_TO_BRIDGE_REAR_FACE", "YOKE_POSITIVE_STOP", "M4_TO_COLLAR"],
        "rear_component_clearance": "CAD_REFERENCE_PASS_PHYSICAL_HOLD",
        "physical_holds": ["BRIDGE_VARIANT", "M3_NUT_THICKNESS", "M3_WASHER_THICKNESS", "THREAD_PROJECTION", "REAR_TOOL_REAL_ENVELOPE", "REACTION_YOKE_VARIANT", "FULL_LOAD_TORQUE"],
    }


def validation_report() -> dict[str, object]:
    return {
        "version": VERSION,
        "classification": CLASSIFICATION,
        "result": "SHORT_M3_LOCAL_BRIDGE_CAP_LOCK_COMPLETE",
        "m3_authority": "20P5MM_M3_PHYSICAL_AUTHORITY_RECORDED",
        "v0969_full_body_throughbolt": "SUPERSEDED",
        "local_bridge": "B7_B8_B9_READY_FOR_COUPON",
        "rear_service_window": "COMPLETE_CAD_REFERENCE_PHYSICAL_HOLD",
        "reaction_yoke": "PRESERVED",
        "reinforced_guard": "PRESERVED",
        "protected_12t": "FROZEN",
        "geometry": geometry_metrics(),
        "collision": collision_report(),
        "gates": PARAMS["gates"],
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="600" viewBox="0 0 1000 600"><rect width="1000" height="600" fill="#f8fafc"/><text x="50" y="58" font-family="sans-serif" font-size="28" font-weight="bold" fill="#17202a">{title}</text><line x1="50" y1="78" x2="950" y2="78" stroke="#94a3b8"/>{body}<text x="50" y="575" font-family="sans-serif" font-size="13" fill="#475569">Common Rover v0.9.6.10 · CAD reference · physical coupon authority required</text></svg>'''


def svg_outputs() -> dict[str, str]:
    f = 'font-family="sans-serif" font-size="17" fill="#1f2933"'
    return {
        SVGS[0]: svg_page("20.5 mm short-M3 stack budget", f'''<g {f}><rect x="130" y="190" width="165" height="150" fill="#60a5fa"/><rect x="295" y="190" width="240" height="150" fill="#34d399"/><rect x="535" y="190" width="210" height="150" fill="#fbbf24"/><text x="160" y="380">cap 5.5</text><text x="360" y="380">B8 bridge 8.0</text><text x="565" y="380">hardware budget 7.0</text><line x1="130" y1="155" x2="745" y2="155" stroke="#111827" stroke-width="5"/><text x="345" y="135">under-head usable = 20.5 MEASURED</text></g>'''),
        SVGS[1]: svg_page("Full 44 mm through-bolt vs local bridge", f'''<g {f}><rect x="100" y="150" width="330" height="260" fill="#ef4444" opacity=".35"/><line x1="260" y1="120" x2="260" y2="455" stroke="#b91c1c" stroke-width="8"/><text x="135" y="465">cap + 44 body: impossible with 20.5</text><rect x="590" y="150" width="230" height="120" fill="#34d399"/><rect x="650" y="270" width="110" height="145" fill="white" stroke="#059669" stroke-width="6"/><line x1="705" y1="120" x2="705" y2="385" stroke="#111827" stroke-width="7"/><text x="570" y="465">local bridge + rear-open service window</text></g>'''),
        SVGS[2]: svg_page("Local bridge section", f'''<g {f}><rect x="170" y="150" width="660" height="80" fill="#60a5fa"/><rect x="250" y="230" width="500" height="130" rx="35" fill="#34d399"/><rect x="390" y="360" width="220" height="130" fill="#fff" stroke="#059669" stroke-width="5"/><line x1="500" y1="115" x2="500" y2="455" stroke="#111827" stroke-width="7"/><text x="195" y="135">wide cap 5.5</text><text x="280" y="300">broad bridge B8 = 8.0 · R2.5-class roots</text><text x="410" y="525">rear-open window</text></g>'''),
        SVGS[3]: svg_page("B7 / B8 / B9 coupon", f'''<g {f}><rect x="120" y="285" width="190" height="105" fill="#86efac"/><rect x="405" y="255" width="190" height="135" fill="#34d399"/><rect x="690" y="225" width="190" height="165" fill="#10b981"/><text x="175" y="430">B7 7.0 · stack12.5</text><text x="450" y="430">B8 8.0 · stack13.5</text><text x="730" y="430">B9 9.0 · stack14.5</text><text x="285" y="510">Select thickest safe functional bridge with actual M3</text></g>'''),
        SVGS[4]: svg_page("Rear nut service window", f'''<g {f}><circle cx="500" cy="315" r="175" fill="#cbd5e1"/><circle cx="500" cy="315" r="95" fill="#fff" stroke="#059669" stroke-width="8"/><polygon points="445,285 500,252 555,285 555,345 500,378 445,345" fill="#94a3b8"/><path d="M650 180L565 255" stroke="#f59e0b" stroke-width="9"/><text x="665" y="175">visible metal nut</text><text x="640" y="220">washer / tool / thread inspection</text><text x="300" y="535">window Ø12.4 CAD reference; actual tool envelope HOLD</text></g>'''),
        SVGS[5]: svg_page("Local bridge clamp-load path", f'''<g {f}><text x="85" y="135">M3 head → wide cap → B8 broad PETG bridge → rear washer → metal nut</text><path d="M100 210H900" stroke="#2563eb" stroke-width="22"/><text x="85" y="310">M3 supplies axial cap clamp only</text><text x="85" y="370">drive torque remains shaft → M4 → collar → yokes → hub → 12T</text><text x="85" y="430">No PETG thread · no hidden nut · no full-body bolt</text></g>'''),
        SVGS[6]: svg_page("Reaction yoke plus local bridge clearance", f'''<g {f}><path d="M160 400V165H240V280H410V165H490V400Z" fill="#14b8a6"/><circle cx="325" cy="310" r="45" fill="#94a3b8"/><rect x="610" y="205" width="230" height="150" rx="30" fill="#34d399"/><circle cx="725" cy="280" r="32" fill="#fff"/><text x="135" y="460">v0.9.6.9 Y2 yoke preserved</text><text x="600" y="460">B8 bridge at45°/225°</text><text x="270" y="515">CAD common-volume interference = 0</text></g>'''),
        SVGS[7]: svg_page("Full hub axial section", f'''<g {f}><rect x="130" y="180" width="740" height="210" fill="#bfdbfe"/><rect x="130" y="145" width="80" height="280" fill="#10b981"/><rect x="760" y="165" width="110" height="240" fill="#60a5fa"/><rect x="610" y="225" width="110" height="115" fill="#34d399"/><rect x="635" y="340" width="60" height="85" fill="white" stroke="#059669" stroke-width="5"/><line x1="665" y1="125" x2="665" y2="400" stroke="#111827" stroke-width="7"/><text x="105" y="480">9mm guard / frame side</text><text x="610" y="480">local bridge + open rear window + short M3</text></g>'''),
    }


def document_outputs() -> dict[str, str]:
    h = "# Common Rover Short-M3 Local Bridge Cap Lock v0.9.6.10\n\nClassification: `SHORT_M3_LOCAL_BRIDGE_CAP_LOCK_CORRECTION`  \nRelease: `PHYSICAL COUPON PREPARATION / NOT FOR POWERED OR FIELD USE`  \n"
    return {
        "README.md": h + "\nThis isolated lane supersedes the v0.9.6.9 full-body M3 bolt because the available20.5mm under-head length cannot cross a5.5mm cap and44mm body. It introduces two broad local PETG bridges and directly rear-open service windows while preserving the reaction yokes, reinforced guard, B collar, headed M4 hardware and frozen12T.\n",
        "DESIGN_AUTHORITY.md": h + "\nPhysical authority: available M3 under-head20.5mm and overall reference27.9mm. Frozen parent authority: exact12T,9/5/6mm guard, Y1/Y2/Y3 yokes, B Ø16.2/R20.4, headed M4×2,8mm spacer and4.4mm frame gap. CAD candidates B7/B8/B9 are not physical selections.\n",
        "PHYSICAL_INPUTS.md": h + "\n|Input|Value|Class|\n|---|---:|---|\n|M3 usable under-head length|20.5mm|MEASURED|\n|M3 overall reference|27.9mm|MEASURED|\n|Cap|5.5mm|PARENT CAD|\n|Sprocket body|44.0mm|FROZEN|\n|Frame↔guard with8mm spacer|4.4mm|MEASURED|\n|M4 head-top / old shoe / interference|4.3 / 8.3 / 4.0mm|MEASURED / DERIVED|\n",
        "M3_SHORT_HARDWARE_AUTHORITY.md": h + "\nThe immediately available screw has20.5mm usable length under its head and27.9mm overall head/washer reference. These are user-measured physical authority. No longer screw is assumed. Nut/washer thickness, full thread engagement and remaining visible projection require coupon measurement.\n",
        "V0969_FULL_THROUGHBOLT_FAILURE.md": h + "\n`V0969_FULL_BODY_THROUGHBOLT=GEOMETRICALLY_IMPOSSIBLE_WITH_AVAILABLE_M3` and `SUPERSEDED_BEFORE_PHYSICAL_ACCEPTANCE`. Cap5.5 + body44.0 =49.5mm before washer/nut, exceeding20.5mm by29.0mm. The fix does not shorten teeth/body or invoke adhesive, snap, hidden nut, PETG thread or hypothetical hardware.\n",
        "LOCAL_BRIDGE_CAP_LOCK_SPEC.md": h + "\nTwo short broad local bridges remain integral with the one-piece hub at45°/225°, PCD46. Each has an Ø3.4 clearance path, R2.5-class broad root, direct rear-open service window and visible metal washer/nut. B7=7, B8=8, B9=9mm; B8 is CAD primary only. Cap+bridge remains12.5/13.5/14.5mm.\n",
        "LOCAL_BRIDGE_LOAD_PATH.md": h + "\nShort M3 clamp load flows from front head/washer through the54×5.5 wide cap and broad bridge into the accessible rear washer/nut sandwich. The bridge distributes axial bearing load into nearby hub material through short filleted roots. It is not a thin cantilever and receives no drivetrain torque credit.\n",
        "REAR_SERVICE_WINDOW_SPEC.md": h + "\nEach Ø12.4 CAD-reference window opens directly to the rear and terminates at the bridge rear seating face. It provides visual inspection, washer/nut insertion/removal, thread projection inspection and an11.2mm generic tool cylinder. No hidden nut pocket exists. Actual nut, washer and tool fit remains physical HOLD.\n",
        "SHORT_M3_STACK_BUDGET.md": h + "\nUnder-head budget20.5mm. Cap5.5 leaves15.0mm for bridge plus rear hardware. B7 leaves8.0, B8 leaves7.0, B9 leaves6.0mm. Preferred PETG stack is≤14.5mm and absolute limit≤15.5mm. Select the thickest candidate with full nut engagement, visible thread, tool access and full cap seating.\n",
        "REACTION_YOKE_PARENT_STATUS.md": h + "\nThe v0.9.6.9 U-yoke is preserved byte-for-geometry through direct parent reuse: Y1/Y2/Y3=3.3/3.5/3.7mm, Y2 design primary, positive stop, service removal and broad side-reaction faces. Old solid shoe remains rejected by the4.0mm measured overhead conflict. Local bridges have zero CAD intersection with installed yokes.\n",
        "REINFORCED_GUARD_PARENT_STATUS.md": h + "\nThe v0.9.6.9 guard is unchanged: height9, upper wall5, root6, R3-class gusset, R1 top edge, connector margin3.9mm and frame-facing axial surface frozen.1.8mm shift remains a static CAD reference only.8mm-spacer frame gap remains4.4mm measured.\n",
        "TORQUE_LOAD_PATH.md": h + "\nPrimary drivetrain path remains `Ø10 shaft → headed M4×2 → metal collar → low-profile yokes×2 → broad PETG pockets → one-piece hub → protected12T → crawler`. The local bridges, M3 bolts and wide cap only retain/clamp the cap and internal pieces axially.\n",
        "ASSEMBLY_PROCEDURE.md": h + "\n1. Assemble shaft/collar. 2. Tighten headed M4×2. 3. Seat reaction yokes at positive stops. 4. Fit wide cap. 5. Insert the actual short M3×2. 6. Add rear metal washers and nuts through the open windows. 7. Tighten evenly while preventing nut rotation. 8. Verify full cap seating, no bottom-out/crush and visible thread. Disassemble normally in reverse.\n",
        "PRINT_PLAN.md": h + "\nPrint in PETG: reaction-yoke coupon if incomplete, then the B7/B8/B9 short-M3 local-bridge coupon, then reinforced-guard comparison coupon if incomplete. Do not print the revised full12T until both reaction-yoke and local-bridge physical PASS. Record coupon ID and actual hardware.\n",
        "PHYSICAL_TEST_PLAN.md": h + "\nFor B7/B8/B9 record full insertion, washer fit, nut engagement FULL/PARTIAL/FAIL, visible thread, tool access, cap seat, rocking, crack and disassembly. Select the thickest safe functional bridge. Full assembly then requires witness marks and50 forward/50 reverse hand rotations; stop for loose hardware, cap lift, bridge damage, yoke/M4 movement, guard contact or crawler climb.\n",
        "POWERED_TEST_GATE.md": h + "\n`NOT_YET_APPROVED`. Before unloaded low-load power require reaction-yoke PASS, short-M3 bridge PASS, full revised12T PASS,8mm-spacer rotational PASS, final170mm frame, independent shaft non-contact, axial retention, fuse, E-stop/hardware cutoff, polarity, MD10C and cable retention.\n",
        "SAFETY_NOTES.md": h + "\nDRY COUPON WORK ONLY. Disconnect electrical power for assembly. Do not substitute PETG threads, hidden/captive nuts, adhesive or snap retention. Do not credit M3/cap/local bridge as a torque path. Stop on partial nut engagement, bottom-out, PETG whitening/crack, inaccessible hardware or abnormal rotation.\n",
        "HOLD_REGISTER.md": h + "\n- Final B7/B8/B9 bridge until actual short-M3 coupon\n- M3 nut and washer thickness, full engagement and remaining projection\n- Actual rear tool envelope\n- Final Y1/Y2/Y3 reaction-yoke variant\n- Full-load torque, final belt, shaft cut length\n- Water, mud, powered and field testing\n",
        "SOURCE_TRACE.md": h + "\n- v0.9.6.9 read-only: exact reinforced guard, low-profile yokes, cap, B collar, headed M4 and protected12T geometry. Its full-body M3 architecture alone is superseded.\n- v0.9.6.8/v0.9.6.7 and all earlier lanes remain protected.\n- User v0.9.6.10 physical authority: M3 under-head20.5mm and overall27.9mm.\nNo source authorizes longer hardware, final bridge selection, powered operation or shaft cutting.\n",
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
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\nclassification={CLASSIFICATION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths={len(EXPECTED_PATHS)}\nstep=4\nstl=3\nsvg=8\nm3_under_head_mm=20.5\nbridge_primary=B8_8.0mm\nfull_body_throughbolt=SUPERSEDED\n")
    write_text(out / "TEST_LOG.txt", "Common Rover v0.9.6.10 contract\nCONTRACT=RUNTIME_PASS_REQUIRED\nSTEP_IMPORT=RUNTIME_PASS_REQUIRED\nSTL_MANIFOLD=RUNTIME_PASS_REQUIRED\nREPRODUCIBILITY=RUNTIME_PASS_REQUIRED\nLOCAL_BRIDGE_COUPON=PHYSICAL_PENDING\nREACTION_YOKE_COUPON=PHYSICAL_PASS_REQUIRED\nPOWERED=NOT_YET_APPROVED\n")
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
    c = collision_report()
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
    ph = p["m3_physical"]
    add("m3-under-head", ph["under_head_usable_length_mm"] == 20.5, ph)
    add("m3-overall", ph["overall_reference_mm"] == 27.9, ph)
    add("m3-measured", ph["status"] == "MEASURED_USER_PHYSICAL_AUTHORITY", ph)
    add("no-hypothetical-longer", not ph["longer_hypothetical_screw_assumed"], ph)
    fail = p["v0969_full_body_throughbolt"]
    add("full-through-impossible", fail["status"] == "GEOMETRICALLY_IMPOSSIBLE_WITH_AVAILABLE_M3", fail)
    add("full-through-superseded", fail["classification"] == "SUPERSEDED_BEFORE_PHYSICAL_ACCEPTANCE", fail)
    add("full-through-false", fail["full_body_through"] is False, fail)
    add("stack-impossible", fail["minimum_petg_only_mm"] == 49.5 and fail["shortfall_before_rear_hardware_mm"] == 29.0, fail)
    bridge = p["local_bridge"]
    add("bridge-architecture", bridge["architecture"] == "SHORT_M3_LOCAL_THROUGH_BOLT_WITH_OPEN_REAR_SERVICE_WINDOW", bridge)
    add("bridge-count", bridge["count"] == 2, bridge)
    for key, value in (("B7", 7.0), ("B8", 8.0), ("B9", 9.0)):
        add(f"bridge-{key}", bridge["variants_mm"][key] == value, bridge)
    add("bridge-primary", bridge["design_primary"] == "B8" and bridge["design_primary_mm"] == 8.0, bridge)
    add("bridge-stacks", bridge["petg_stack_mm"] == {"B7": 12.5, "B8": 13.5, "B9": 14.5}, bridge)
    add("bridge-budgets", bridge["remaining_hardware_budget_mm"] == {"B7": 8.0, "B8": 7.0, "B9": 6.0}, bridge)
    add("bridge-preferred", max(bridge["petg_stack_mm"].values()) <= bridge["preferred_petg_stack_max_mm"] == 14.5, bridge)
    add("bridge-absolute", max(bridge["petg_stack_mm"].values()) <= bridge["absolute_petg_stack_max_mm"] == 15.5, bridge)
    add("bridge-root", bridge["root_fillet_mm"] == 2.5 and bridge["thin_cantilever"] is False, bridge)
    add("bridge-integrated", bridge["integrated_with_one_piece_hub"] is True, bridge)
    add("bridge-not-torque", bridge["primary_torque_path"] is False, bridge)
    window = p["service_window"]
    add("window-two-open", window["count"] == 2 and window["open_to_rear"] is True, window)
    add("window-access", window["rear_nut_visible"] and window["rear_nut_accessible"] and window["rear_nut_removable"], window)
    add("window-not-hidden", window["hidden_cavity"] is False, window)
    add("window-hold", window["clearance_status"] == "CAD_REFERENCE_PASS_PHYSICAL_HOLD", window)
    fastener = p["fastener"]
    add("m3-count", fastener["count"] == 2, fastener)
    add("m3-layout", fastener["angles_deg"] == [45.0, 225.0] and fastener["pcd_mm"] == 46.0, fastener)
    add("m3-hole", fastener["hole_diameter_mm"] == 3.4, fastener)
    add("m3-metal-hardware", fastener["front_heads"] and fastener["rear_washers"] and fastener["rear_nuts"], fastener)
    add("m3-rear-access", fastener["rear_nuts_accessible"], fastener)
    add("m3-no-hidden", not fastener["hidden_captive_nut"], fastener)
    add("m3-no-petg-thread", not fastener["petg_thread"], fastener)
    add("m3-no-44", not fastener["full_44mm_throughbolt"], fastener)
    add("m3-no-snap-adhesive", not fastener["snap"] and not fastener["adhesive"], fastener)
    add("m3-thread-pending", fastener["thread_engagement"] == "PHYSICAL_PENDING_FULL_NUT_ENGAGEMENT_REQUIRED", fastener)
    cap_p = p["cap"]
    add("cap-dims", cap_p["outer_diameter_mm"] == 54.0 and cap_p["thickness_mm"] == 5.5, cap_p)
    add("cap-role", cap_p["broad_seating"] and cap_p["snap_fingers"] == 0 and not cap_p["primary_torque_path"], cap_p)
    yoke = p["reaction_yoke"]
    add("yoke-variants", yoke["variants_mm"] == {"Y1": 3.3, "Y2": 3.5, "Y3": 3.7}, yoke)
    add("yoke-preserved", yoke["preserved_from"] == "v0.9.6.9" and yoke["design_primary_bridge_mm"] == 3.5, yoke)
    add("yoke-primary-torque", yoke["primary_torque_path"] is True, yoke)
    guard = p["guard"]
    add("guard-preserved", guard["preserved_from"] == "v0.9.6.9" and guard["new_height_mm"] == 9.0 and guard["selected_upper_wall_mm"] == 5.0 and guard["root_mm"] == 6.0, guard)
    add("guard-radii-margin", guard["root_gusset_class"] == "R3_CLASS" and guard["top_edge_radius_mm"] == 1.0 and guard["connector_vertical_margin_mm"] == 3.9, guard)
    add("guard-gap", guard["frame_clearance_measured_mm"] == 4.4, guard)
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
    add("12t-pitch-overlap", tooth["pitch_diameter_mm"] == 76.3943726841 and tooth["buried_root_overlap_mm"] == 4.0, tooth)
    add("12t-one-piece", tooth["outer_body"] == "ONE_PIECE" and not tooth["split_teeth"] and tooth["tooth_root_radial_service_holes"] == 0, tooth)
    add("12t-external", m["protected_external_missing_mm3"] == 0.0, m["protected_external_missing_mm3"])
    add("parent-guard-exact", m["guard_parent_volume_difference_mm3"] == 0.0, m)
    add("parent-yoke-exact", m["yoke_parent_volume_difference_mm3"] == 0.0, m)
    add("parent-cap-exact", m["cap_parent_volume_difference_mm3"] == 0.0, m)
    add("main-one-solid", m["main_solids"] == 1, m)
    add("envelope-petg", m["petg_rotating_axial_mm"] == p["envelopes"]["petg_rotating_axial_mm"] == 48.0, m)
    add("envelope-hardware", m["m3_hardware_axial_mm"] == p["envelopes"]["m3_hardware_axial_mm"] == 27.9, m)
    add("envelope-total", m["total_assembly_axial_mm"] == p["envelopes"]["full_assembly_axial_mm"] == 55.4, m)
    add("collision-all-zero", c["known_all_zero"], c["known_unintended"])
    add("rear-clearance-hold", c["rear_component_clearance"] == "CAD_REFERENCE_PASS_PHYSICAL_HOLD", c)
    add("coupon-solids", m["coupon_solids"] == 6, m["coupon_solids"])
    add("coupon-valid", m["coupon_all_valid"], m["coupon_all_valid"])
    add("bridge-ref-two", m["bridge_reference_solids"] == 2, m["bridge_reference_solids"])
    add("primary-valid", m["all_primary_valid"], m["all_primary_valid"])
    steps = [lane / rel for rel in CAD if rel.endswith(".step")]
    stls = [lane / rel for rel in CAD if rel.endswith(".stl")]
    add("step-count", len(steps) == 4, len(steps))
    imported = 0
    for path in steps:
        try:
            obj = cq.importers.importStep(str(path))
            imported += int(obj.solids().size() > 0 and all(s.isValid() for s in obj.solids().vals()))
        except Exception:
            pass
    add("step-import", imported == 4, imported)
    add("stl-count", len(stls) == 3, len(stls))
    add("stl-manifold", all(stl_is_manifold(path) for path in stls), len(stls))
    add("svg-count", len(SVGS) == 8 and all((lane / rel).read_text(encoding="utf-8").startswith("<svg") for rel in SVGS), len(SVGS))
    add("docs-count", len(DOCS) == 19, len(DOCS))
    gates = p["gates"]
    add("coupon-gate", gates["local_bridge_coupon"] == "READY_FOR_PHYSICAL_COUPON", gates)
    add("full12t-gate", gates["full_12t"] == "PRINT_PENDING_YOKE_AND_LOCAL_BRIDGE_COUPON", gates)
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
    with tempfile.TemporaryDirectory(prefix="v09610_a_") as a, tempfile.TemporaryDirectory(prefix="v09610_b_") as b:
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
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_Short_M3_Local_Bridge_Cap_Lock_v0_9_6_10_{stamp}.zip"
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
