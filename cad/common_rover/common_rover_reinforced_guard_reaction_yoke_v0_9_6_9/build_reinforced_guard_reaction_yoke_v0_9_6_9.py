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


VERSION = "v0.9.6.9"
CLASSIFICATION = "DRIVE_REACTION_AND_CRAWLER_PHYSICAL_CORRECTION"
REPO_ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE_REL = Path("cad/common_rover/common_rover_reinforced_guard_reaction_yoke_v0_9_6_9")
DEFAULT_LANE = REPO_ROOT / LANE_REL
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
BASE_OUTSIDE_COUNT = 1987
BASE_OUTSIDE_DIGEST = "1583d3e9d8a1a646ef3ff0f491140a86dd5520e3d54c3b21b1943f8ff914e8ac"
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

PARENT_BUILDER = REPO_ROOT / "cad/common_rover/common_rover_positive_hub_cap_lock_v0_9_6_8/build_positive_hub_cap_lock_v0_9_6_8.py"
_spec = importlib.util.spec_from_file_location("v0968_parent", PARENT_BUILDER)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load protected parent: {PARENT_BUILDER}")
parent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = parent
_spec.loader.exec_module(parent)

PROTECTED_LANES = dict(parent.PROTECTED_LANES)
PROTECTED_LANES["v0.9.6.8"] = (
    "cad/common_rover/common_rover_positive_hub_cap_lock_v0_9_6_8",
    60,
    "71dff91a280c404408ed3453af95515b138cd7df65573cff54f477796e1cea55",
)

DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "PHYSICAL_INPUTS.md",
    "REACTION_SHOE_GEOMETRIC_FAILURE.md", "LOW_PROFILE_REACTION_YOKE_SPEC.md",
    "REACTION_YOKE_LOAD_PATH.md", "CRAWLER_CLIMB_FAILURE_RECORD.md",
    "ANTI_CLIMB_GUARD_SPEC.md", "V0968_CAPTIVE_NUT_SUPERSESSION.md",
    "M3_REAR_NUT_THROUGHBOLT_SPEC.md", "TORQUE_LOAD_PATH.md",
    "SPACER_8MM_PHYSICAL_UPDATE.md", "ASSEMBLY_PROCEDURE.md", "PRINT_PLAN.md",
    "PHYSICAL_TEST_PLAN.md", "POWERED_TEST_GATE.md", "SAFETY_NOTES.md",
    "HOLD_REGISTER.md", "SOURCE_TRACE.md",
]
CAD = [
    "drive/artifacts/drive_12t_h25a1_reaction_yoke_high_guard_v0_9_6_9.step",
    "drive/artifacts/drive_12t_h25a1_reaction_yoke_high_guard_v0_9_6_9.stl",
    "reaction_yoke/artifacts/h25a1_low_profile_reaction_yoke_v0_9_6_9.step",
    "reaction_yoke/artifacts/h25a1_low_profile_reaction_yoke_v0_9_6_9.stl",
    "hub_cap/artifacts/h25a1_rear_nut_throughbolt_cap_v0_9_6_9.step",
    "hub_cap/artifacts/h25a1_rear_nut_throughbolt_cap_v0_9_6_9.stl",
    "reaction_yoke/artifacts/low_profile_reaction_yoke_coupon_v0_9_6_9.step",
    "reaction_yoke/artifacts/low_profile_reaction_yoke_coupon_v0_9_6_9.stl",
    "hub_cap/artifacts/m3_rear_nut_throughbolt_coupon_v0_9_6_9.step",
    "hub_cap/artifacts/m3_rear_nut_throughbolt_coupon_v0_9_6_9.stl",
    "crawler_guard/artifacts/crawler_guard_comparison_coupon_v0_9_6_9.step",
    "crawler_guard/artifacts/crawler_guard_comparison_coupon_v0_9_6_9.stl",
    "integration/artifacts/crawler_drive_reaction_yoke_full_assembly_v0_9_6_9.step",
]
SVGS = [f"integration/artifacts/{name}" for name in (
    "reaction_shoe_8p3_vs_clearance_4p3_v0_9_6_9.svg",
    "solid_shoe_vs_low_profile_yoke_v0_9_6_9.svg",
    "reaction_yoke_cross_section_v0_9_6_9.svg",
    "reaction_yoke_load_path_v0_9_6_9.svg",
    "crawler_guard_old_vs_new_v0_9_6_9.svg",
    "crawler_lateral_shift_1p8_v0_9_6_9.svg",
    "m3_captive_vs_rear_nut_throughbolt_v0_9_6_9.svg",
    "rear_nut_service_v0_9_6_9.svg",
    "full_hub_section_v0_9_6_9.svg",
    "frame_guard_clearance_v0_9_6_9.svg",
)]
JSONS = ["design_parameters.json", "source_evidence.json", "collision_report.json", "validation_report.json", "reproducibility_report.json"]
SOURCES = ["build_reinforced_guard_reaction_yoke_v0_9_6_9.py", "tests/test_reinforced_guard_reaction_yoke_v0_9_6_9_contract.py"]
RELEASE = ["BUILD_LOG.txt", "TEST_LOG.txt", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt"]
EXPECTED_PATHS = sorted(DOCS + CAD + SVGS + JSONS + SOURCES + RELEASE)

PROTECTED_12T = dict(parent.PROTECTED_12T)
PARAMS = {
    "version": VERSION, "classification": CLASSIFICATION, "units": "mm",
    "pitch": {"physical_result": "PHYSICAL_MATCH", "status": "FROZEN", "difference_mm": 0.0, "spacing_difference_deg": 0.0},
    "crawler_failure": {
        "failure_mode": "LATERAL_DRIFT_TO_CONNECTOR_CLIMB",
        "current_guard": "ANTI_CLIMB_FAIL", "strength": "FAIL_ONE_FRACTURE_USER_REPORTED",
        "sequence": ["LATERAL_DRIFT", "CONNECTOR_APPROACH", "CONNECTOR_CLIMB", "CRAWLER_RISE", "ABNORMAL_GUARD_BENDING", "GUARD_FRACTURE"],
    },
    "guard": {
        "current_height_mm": 6.0, "link_body_height_mm": 24.1,
        "connector_max_protrusion_mm": 5.1, "current_wall_mm": 4.0,
        "failed_root_mm": 4.0, "max_lateral_shift_mm": 1.8,
        "current_vertical_margin_mm": 0.9, "current_margin_class": "INSUFFICIENT",
        "new_height_mm": 9.0, "selected_upper_wall_mm": 5.0,
        "allowed_upper_wall_mm": [4.5, 5.0], "root_mm": 6.0,
        "root_gusset_radial_run_mm": 3.0, "root_gusset_class": "R3_CLASS",
        "top_edge_radius_mm": 1.0, "link_facing_wall": "NEAR_VERTICAL_NO_INWARD_RAMP",
        "connector_vertical_margin_mm": 3.9,
        "frame_facing_surface_z_mm": -26.0, "frame_facing_surface": "AXIAL_POSITION_FROZEN",
        "frame_clearance_measured_mm": 4.4, "frame_clearance_target_mm": 4.0,
        "lateral_shift_static_path": "NO_DIRECT_PATH_OVER_9MM_TOP_CAD_REFERENCE",
        "dynamic_pass": False,
    },
    "protected_12t": PROTECTED_12T,
    "collar": {"od_mm": 15.9, "id_mm": 10.1, "width_mm": 3.0},
    "full_capture": {
        "selected": "B", "collar_pocket_diameter_mm": 16.2, "hardware_cavity_radius_mm": 20.4,
        "A": "REJECT_TOO_TIGHT", "B": "PHYSICAL_PRIMARY_PASS", "C": "REJECT_TOO_LOOSE",
    },
    "m4": {
        "type": "HEADED_M4", "count": 2, "separation_deg": 90.0,
        "head_od_mm": 6.8, "head_height_mm": 2.8, "washer_od_mm": 8.8,
        "washer_stack_mm": 1.8, "full_radial_envelope_mm": 20.0,
        "grub_screw_primary_count": 0, "unchanged": True,
        "qualification": "1.0KG_AT_70MM_24H_NO_SHAFT_SHIFT",
    },
    "old_reaction_shoe": {
        "head_top_space_mm": 4.3, "installed_overhead_requirement_mm": 8.3,
        "interference_mm": 4.0,
        "status": "GEOMETRICALLY_INCOMPATIBLE_WITH_ACTUAL_M4_HEAD_SPACE",
        "primary": False, "deeper_pocket_fix_valid": False,
        "physical_measurement_precedes_stl_axis_bounds": True,
    },
    "reaction_yoke": {
        "architecture": "LOW_PROFILE_U_SHAPED_REACTION_BRIDGE",
        "low_profile_bridge": True, "solid_overhead_block": False,
        "variants_mm": {"Y1": 3.3, "Y2": 3.5, "Y3": 3.7},
        "variant_remaining_clearance_mm": {"Y1": 1.0, "Y2": 0.8, "Y3": 0.6},
        "design_primary_bridge_mm": 3.5, "physical_selection": "THICKEST_RELIABLE_FIT_PENDING",
        "direct_overlap_max_mm": 3.7, "side_shoulders": "THICK_BROAD_REACTION_SURFACES",
        "roof_role": "RETENTION_AND_GEOMETRY_BRIDGE_NOT_SOLE_TORQUE_MEMBER",
        "positive_stop": True, "removable": True, "hammer_required": False,
        "insertion": "FRONT_AXIAL_PRESENTATION_THEN_SHORT_RADIAL_SEATING_SLIDE",
        "service_notch": True, "quantity_per_sprocket": 2,
    },
    "cap_lock": {
        "v0968_captive_nut": "SUPERSEDED", "captive_internal_nut": False,
        "fastener": "M3_TRUE_THROUGH_BOLT", "count": 2,
        "angles_deg": [45.0, 225.0], "separation_deg": 180.0,
        "center_radius_mm": 23.0, "pcd_mm": 46.0, "through_hole_diameter_mm": 3.4,
        "front_head": True, "front_washer_optional": True,
        "rear_washer": True, "rear_nut": True, "rear_nut_visible": True,
        "rear_nut_accessible": True, "petg_threads": False, "snap_retention": False,
        "primary_torque_path": False, "bolt_length": "HOLD_PHYSICAL_MEASUREMENT",
        "rear_tool_envelope": "GENERIC_REFERENCE_ACTUAL_TOOL_HOLD",
    },
    "cap": {
        "outer_diameter_mm": 54.0, "thickness_mm": 5.5,
        "broad_seating": True, "snap_fingers": 0,
        "role": "AXIAL_RETENTION_AND_LOAD_SPREAD", "primary_torque_path": False,
    },
    "envelopes": {
        "protected_tooth_axial_mm": 44.0, "petg_rotating_axial_mm": 48.0,
        "throughbolt_hardware_axial_mm": 46.9, "total_assembly_axial_mm": 48.0,
        "rear_nut_projection_from_tooth_face_mm": 2.9,
    },
    "spacer": {
        "id_mm": 10.2, "od_mm": 13.8, "thickness_mm": 8.0, "chamfer_mm": 0.35,
        "frame_guard_clearance_mm": 4.4, "clearance_class": "PHYSICAL_MEASURED_4P4MM",
        "other_checks": "PHYSICAL_PENDING", "width_nominal_mm": 294.0,
        "width_conservative_mm": 295.0,
    },
    "shaft": {
        "architecture": "LEFT_RIGHT_INDEPENDENT_HALF_SHAFTS", "diameter_mm": 10.0,
        "cut_length": "HOLD_PHYSICAL_MEASUREMENT", "final_center_gap": "HOLD_NON_CONTACT_REQUIRED",
    },
    "print": {
        "printer": "BAMBU_A1", "material": "PETG",
        "order": ["LOW_PROFILE_REACTION_YOKE_COUPON", "M3_REAR_NUT_THROUGHBOLT_COUPON", "CRAWLER_GUARD_COMPARISON_COUPON"],
        "full_12t_gate": "PENDING_REACTION_YOKE_AND_THROUGHBOLT_PHYSICAL_PASS",
    },
    "gates": {
        "reaction_yoke": "READY_FOR_PHYSICAL_COUPON", "reinforced_guard": "READY_FOR_PHYSICAL_COUPON",
        "m3_throughbolt": "READY_FOR_PHYSICAL_COUPON", "full_12t": "PRINT_PENDING_REACTION_YOKE_AND_CAP_COUPON",
        "powered": "NOT_YET_APPROVED", "shaft_cut": "HOLD_PHYSICAL_MEASUREMENT",
        "water": "NOT_APPROVED", "mud": "NOT_APPROVED", "field": "NOT_APPROVED",
    },
}


sha256 = parent.sha256
write_text = parent.write_text
write_json = parent.write_json
run_git = parent.run_git
tree_digest = parent.tree_digest
box = parent.box
cylinder = parent.cylinder
axis_cylinder = parent.axis_cylinder
compound = parent.compound
fused = parent.fused
volume = parent.volume
dims = parent.dims
center_xy = parent.center_xy
hex_prism = parent.hex_prism


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


def ring(outer_radius: float, inner_radius: float, length: float, z0: float) -> cq.Workplane:
    return cylinder(outer_radius, length, z0).cut(cylinder(inner_radius, length + 0.4, z0 - 0.2)).clean()


def reinforced_guard() -> cq.Workplane:
    upper = ring(38.47, 29.47, 5.0, -26.0)
    try:
        upper = upper.edges(">Z").fillet(1.0)
    except Exception:
        pass
    narrow_root = ring(29.97, 29.47, 6.0, -26.0)
    wedge = cq.Workplane(obj=cq.Solid.makeCone(32.47, 29.47, 1.0, cq.Vector(0, 0, -21.0), cq.Vector(0, 0, 1))).cut(cylinder(29.47, 1.4, -21.2))
    return fused([upper, narrow_root, wedge]).clean()


def old_guard_reference() -> cq.Workplane:
    return ring(35.47, 29.47, 4.0, -26.0)


def yoke_levels(bridge_mm: float) -> tuple[float, float, float]:
    split_clearance = (4.3 - bridge_mm) / 2.0
    bottom = 3.4 + split_clearance
    return bottom, bottom + bridge_mm, split_clearance * 2.0


def reaction_yoke(bridge_mm: float = 3.5) -> cq.Workplane:
    roof_bottom, roof_top, _ = yoke_levels(bridge_mm)
    shoulder_bottom = -4.6
    shoulder_height = roof_top - shoulder_bottom
    legs = [box(6.0, 3.2, shoulder_height, (12.0, sign * 6.0, shoulder_bottom + shoulder_height / 2.0)) for sign in (-1, 1)]
    roof = box(4.2, 15.2, bridge_mm, (12.9, 0, roof_bottom + bridge_mm / 2.0))
    reaction_mass = box(9.0, 15.2, shoulder_height, (19.5, 0, shoulder_bottom + shoulder_height / 2.0))
    yoke = fused([*legs, roof, reaction_mass])
    yoke = yoke.cut(box(2.4, 4.0, 3.0, (23.0, 0, -1.0)))
    return yoke.clean()


def yoke_pocket() -> cq.Workplane:
    _, roof_top, _ = yoke_levels(3.7)
    zmin, zmax = -4.8, 16.7
    height = zmax - zmin
    legs = [box(6.4, 3.6, height, (12.0, sign * 6.0, zmin + height / 2.0)) for sign in (-1, 1)]
    roof_corridor = box(4.6, 15.6, zmax - 3.3, (12.9, 0, 3.3 + (zmax - 3.3) / 2.0))
    outer = box(9.0, 15.6, height, (19.5, 0, zmin + height / 2.0))
    return compound([*legs, roof_corridor, outer])


def installed_yokes(bridge_mm: float = 3.5) -> tuple[cq.Workplane, cq.Workplane]:
    first = reaction_yoke(bridge_mm)
    second = first.rotate((0, 0, 0), (0, 0, 1), 90)
    return first, second


def m3_through_holes() -> list[cq.Workplane]:
    return [cylinder(1.7, 48.0, -24.0).translate((*center_xy(23.0, angle), 0)) for angle in (45.0, 225.0)]


def main_sprocket() -> cq.Workplane:
    part = parent.protected_blank()
    voids = [
        cylinder(5.15, 46.0, -23.0), cylinder(8.1, 24.0, -2.0),
        box(40.8, 9.2, 26.6, (0, 0, 8.7)), box(9.2, 40.8, 26.6, (0, 0, 8.7)),
        cylinder(27.2, 5.7, 16.5), yoke_pocket(),
        yoke_pocket().rotate((0, 0, 0), (0, 0, 1), 90), *m3_through_holes(),
    ]
    for void in compound(voids).solids().vals():
        part = part.cut(cq.Workplane(obj=void))
    return part.union(reinforced_guard()).clean()


def cap() -> cq.Workplane:
    return parent.wide_cap()


def rear_nut_hardware() -> cq.Workplane:
    parts = []
    for angle in (45.0, 225.0):
        x, y = center_xy(23.0, angle)
        # Generic through-bolt reference only: the rear nut, rather than
        # excess shank, defines the rear-most axial envelope. Exact catalogue
        # length remains HOLD until the printed coupon stack is measured.
        shaft = cylinder(1.5, 43.9, -24.9).translate((x, y, 0))
        front_washer = parent.m3_washer_reference().translate((x, y, 18.5))
        head = cylinder(2.75, 3.0, 19.0).translate((x, y, 0))
        rear_washer = parent.m3_washer_reference().translate((x, y, -22.5))
        rear_nut = parent.m3_nut_reference().translate((x, y, -24.9))
        parts += [shaft, front_washer, head, rear_washer, rear_nut]
    return compound(parts)


def rear_tool_envelope() -> cq.Workplane:
    parts = []
    for angle in (45.0, 225.0):
        x, y = center_xy(23.0, angle)
        parts.append(cylinder(4.5, 4.0, -26.0).translate((x, y, 0)))
    return compound(parts)


def full_hub_assembly() -> cq.Workplane:
    yokes = installed_yokes()
    shaft = cylinder(5.0, 70.0, -35.0)
    spacer = parent.spacer_8().translate((0, 0, -34.0))
    kp000 = box(67.0, 35.0, 17.0, (0, 0, -44.5)).cut(cylinder(8.0, 17.4, -53.2))
    frame_plane = box(92.0, 92.0, 0.4, (0, 0, -30.6))
    link_nominal = box(20.0, 24.1, 4.0, (0, 44.0, -10.0))
    connector_nominal = box(8.0, 5.1, 5.0, (0, 38.5, -13.0))
    link_shifted = box(20.0, 24.1, 4.0, (1.8, 44.0, 8.0))
    connector_shifted = box(8.0, 5.1, 5.0, (1.8, 38.5, 5.0))
    return compound([main_sprocket(), cap(), *yokes, parent.m4_hardware(), rear_nut_hardware(), shaft, spacer, kp000, frame_plane, link_nominal, connector_nominal, link_shifted, connector_shifted])


def coupon_pocket_block(bridge_mm: float) -> cq.Workplane:
    base = box(34.0, 24.0, 12.7, (17.0, 0, 1.35))
    pocket = yoke_pocket()
    hardware_void = parent.m4_hardware()
    for void in compound([pocket, hardware_void]).solids().vals():
        base = base.cut(cq.Workplane(obj=void))
    return base.clean()


def yoke_coupon() -> cq.Workplane:
    parts = []
    for offset, bridge in zip((-50.0, 0.0, 50.0), (3.3, 3.5, 3.7)):
        parts.append(coupon_pocket_block(bridge).translate((offset - 17.0, -18.0, 0)))
        parts.append(reaction_yoke(bridge).translate((offset - 17.0, 22.0, 0)))
    return compound(parts)


def throughbolt_coupon() -> cq.Workplane:
    body = box(60.0, 18.0, 44.0)
    cap_bar = box(60.0, 18.0, 5.5, (0, 30.0, 0))
    for x in (-23.0, 23.0):
        body = body.cut(cylinder(1.7, 44.4, -22.2).translate((x, 0, 0)))
        cap_bar = cap_bar.cut(cylinder(1.7, 5.9, -2.95).translate((x, 30.0, 0)))
        cap_bar = cap_bar.cut(cylinder(3.6, 3.7, -0.75).translate((x, 30.0, 0)))
    return compound([body.clean(), cap_bar.clean()])


def guard_section(height: float, wall: float, root: float, new: bool) -> cq.Workplane:
    wall_part = box(30.0, wall, height, (0, 0, height / 2.0))
    root_part = box(30.0, root, 2.0, (0, (root - wall) / 2.0, 1.0))
    parts = [wall_part, root_part]
    if new:
        gusset = cq.Workplane("YZ").polyline([(wall / 2.0, 0.0), (root / 2.0 + 3.0, 0.0), (wall / 2.0, 3.0)]).close().extrude(15.0, both=True)
        parts.append(gusset)
    return fused(parts).clean()


def guard_coupon() -> cq.Workplane:
    old = guard_section(6.0, 4.0, 4.0, False).translate((-25.0, 0, 0))
    new = guard_section(9.0, 5.0, 6.0, True).translate((25.0, 0, 0))
    return compound([old, new])


GEOMETRIES: dict[str, tuple[object, bool]] = {
    "drive/artifacts/drive_12t_h25a1_reaction_yoke_high_guard_v0_9_6_9": (main_sprocket, True),
    "reaction_yoke/artifacts/h25a1_low_profile_reaction_yoke_v0_9_6_9": (reaction_yoke, True),
    "hub_cap/artifacts/h25a1_rear_nut_throughbolt_cap_v0_9_6_9": (cap, True),
    "reaction_yoke/artifacts/low_profile_reaction_yoke_coupon_v0_9_6_9": (yoke_coupon, True),
    "hub_cap/artifacts/m3_rear_nut_throughbolt_coupon_v0_9_6_9": (throughbolt_coupon, True),
    "crawler_guard/artifacts/crawler_guard_comparison_coupon_v0_9_6_9": (guard_coupon, True),
    "integration/artifacts/crawler_drive_reaction_yoke_full_assembly_v0_9_6_9": (full_hub_assembly, False),
}


def protected_external_missing_mm3() -> float:
    source = parent.protected_blank()
    external = source.cut(cylinder(29.469, 44.4, -22.2))
    retained = main_sprocket().intersect(external)
    return round(max(0.0, float(external.val().Volume()) - float(retained.val().Volume())), 6)


def geometry_metrics() -> dict[str, object]:
    main, wide_cap, m3, m4 = main_sprocket(), cap(), rear_nut_hardware(), parent.m4_hardware()
    yokes = installed_yokes()
    guard = reinforced_guard()
    y1, y2, y3 = (reaction_yoke(v) for v in (3.3, 3.5, 3.7))
    source_old_shoe = parent.reaction_shoe()
    frame_plane = box(92.0, 92.0, 0.4, (0, 0, -30.6))
    return {
        "main_bounds_mm": dims(main), "main_solids": main.solids().size(),
        "protected_external_missing_mm3": protected_external_missing_mm3(),
        "guard_bounds_mm": dims(guard), "guard_frame_face_z_mm": round(guard.val().BoundingBox().zmin, 3),
        "guard_height_mm": round((guard.val().BoundingBox().xlen - 2 * 29.47) / 2.0, 3),
        "guard_frame_plane_intersection_mm3": volume(guard, frame_plane),
        "guard_frame_clearance_mm": round((-26.0) - (-30.4), 3),
        "cap_bounds_mm": dims(wide_cap), "cap_main_intersection_mm3": volume(wide_cap, main),
        "cap_contact_area_sampled_mm2": round(volume(wide_cap.translate((0, 0, -0.01)), main) / 0.01, 2),
        "yoke_bounds_mm": dims(y2), "yoke_volumes_mm3": [round(float(y.val().Volume()), 3) for y in (y1, y2, y3)],
        "old_shoe_volume_mm3": round(float(source_old_shoe.val().Volume()), 3),
        "yoke_a_main_intersection_mm3": volume(yokes[0], main), "yoke_b_main_intersection_mm3": volume(yokes[1], main),
        "yoke_mutual_intersection_mm3": volume(yokes[0], yokes[1]),
        "yoke_a_m4_intersection_mm3": volume(yokes[0], m4), "yoke_b_m4_intersection_mm3": volume(yokes[1], m4),
        "m3_main_intersection_mm3": volume(m3, main), "m3_cap_intersection_mm3": volume(m3, wide_cap),
        "m3_m4_intersection_mm3": volume(m3, m4), "m3_yoke_a_intersection_mm3": volume(m3, yokes[0]),
        "m3_yoke_b_intersection_mm3": volume(m3, yokes[1]), "m3_guard_intersection_mm3": volume(m3, guard),
        "rear_tool_guard_intersection_mm3": volume(rear_tool_envelope(), guard),
        "rear_tool_main_intersection_mm3": volume(rear_tool_envelope(), main),
        "petg_rotating_axial_mm": round(max(main.val().BoundingBox().zmax, wide_cap.val().BoundingBox().zmax) - min(main.val().BoundingBox().zmin, wide_cap.val().BoundingBox().zmin), 3),
        "hardware_axial_mm": round(m3.val().BoundingBox().zmax - m3.val().BoundingBox().zmin, 3),
        "yoke_coupon_solids": yoke_coupon().solids().size(), "throughbolt_coupon_solids": throughbolt_coupon().solids().size(),
        "guard_coupon_solids": guard_coupon().solids().size(),
        "all_primary_valid": all(all(s.isValid() for s in obj.solids().vals()) for obj in [main, guard, y1, y2, y3, wide_cap, yoke_coupon(), throughbolt_coupon(), guard_coupon(), full_hub_assembly()]),
    }


def collision_report() -> dict[str, object]:
    m = geometry_metrics()
    keys = [
        "guard_frame_plane_intersection_mm3", "cap_main_intersection_mm3",
        "yoke_a_main_intersection_mm3", "yoke_b_main_intersection_mm3", "yoke_mutual_intersection_mm3",
        "yoke_a_m4_intersection_mm3", "yoke_b_m4_intersection_mm3",
        "m3_main_intersection_mm3", "m3_cap_intersection_mm3", "m3_m4_intersection_mm3",
        "m3_yoke_a_intersection_mm3", "m3_yoke_b_intersection_mm3", "m3_guard_intersection_mm3",
        "rear_tool_guard_intersection_mm3", "rear_tool_main_intersection_mm3",
    ]
    local = {key: m[key] for key in keys}
    return {
        "method": "CADQUERY_COMMON_VOLUME_FULL_AXIAL_M3_PATH_PLUS_PHYSICAL_DIMENSION_CONTRACT",
        "known_unintended": local, "known_all_zero": all(value == 0 for value in local.values()),
        "intended_contacts_excluded": ["M4_TO_COLLAR", "YOKE_POSITIVE_STOP", "CAP_TO_SEATING_LAND", "REAR_WASHER_TO_REAR_FACE"],
        "physical_holds": ["ACTUAL_YOKE_VARIANT", "M3_BOLT_LENGTH", "M3_NUT_DIMENSIONS", "REAR_TOOL_ENVELOPE", "DYNAMIC_GUARD_LIFE", "FULL_MOTOR_TORQUE"],
    }


def source_evidence() -> dict[str, object]:
    return {
        "classification": "READ_ONLY_PARENT_AND_USER_PHYSICAL_TRACE",
        "sources": [
            {"lane": "v0.9.6.6", "role": "170MM_INDEPENDENT_DRIVE_PARENT", "tree_sha256": PROTECTED_LANES["v0.9.6.6"][2]},
            {"lane": "v0.9.6.8", "role": "POSITIVE_CAP_PARENT_SUPERSEDED_REFERENCE", "tree_sha256": PROTECTED_LANES["v0.9.6.8"][2]},
            {"lane": "v0.9.6.7", "role": "RAPID_DRY_BBOX_CBOX_READ_ONLY", "tree_sha256": PROTECTED_LANES["v0.9.6.7"][2]},
            {"source": "USER_V0.9.6.9_PHYSICAL_CORRECTION", "role": "4P3_HEAD_SPACE_8P3_SHOE_GUARD_AND_SPACER_AUTHORITY"},
        ],
        "parent_modified": False, "physical_measurement_precedence": True,
    }


def validation_report() -> dict[str, object]:
    return {
        "version": VERSION, "classification": CLASSIFICATION,
        "result": "REACTION_YOKE_GUARD_CORRECTION_COMPLETE",
        "geometry": geometry_metrics(), "collision": collision_report(), "gates": PARAMS["gates"],
        "pitch": "PHYSICAL_MATCH_FROZEN", "old_shoe": "GEOMETRIC_FAIL_RECORDED",
        "yoke": "READY_FOR_COUPON", "guard": "READY_FOR_COUPON",
        "throughbolt": "READY_FOR_COUPON", "powered": "NOT_YET_APPROVED",
    }


def svg_page(title: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560"><rect width="1000" height="560" fill="#f8f9fa"/><text x="30" y="40" font-family="sans-serif" font-size="24" font-weight="bold">{title}</text><text x="970" y="38" text-anchor="end" font-family="sans-serif" font-size="12">v0.9.6.9 · PHYSICAL COUPON ONLY</text>{body}</svg>'''


def svg_outputs() -> dict[str, str]:
    f = 'font-family="sans-serif" font-size="17" fill="#1f2933"'
    return {
        SVGS[0]: svg_page("Reaction shoe 8.3 vs available 4.3", f'''<g {f}><rect x="150" y="120" width="250" height="300" fill="#e74c3c" opacity=".45"/><rect x="600" y="265" width="250" height="155" fill="#27ae60" opacity=".45"/><text x="200" y="470">OLD SHOE 8.3 mm</text><text x="625" y="470">SPACE 4.3 mm</text><text x="385" y="520">INTERFERENCE = 4.0 mm · NOT A POCKET-DEPTH PROBLEM</text></g>'''),
        SVGS[1]: svg_page("Solid shoe vs low-profile yoke", f'''<g {f}><rect x="100" y="150" width="300" height="240" fill="#d9534f"/><path d="M610 390V180H680V275H780V180H850V390Z" fill="#27ae60"/><text x="130" y="445">solid overhead block: REJECT</text><text x="610" y="445">U-shaped bridge + shoulders</text></g>'''),
        SVGS[2]: svg_page("Reaction yoke cross-section", f'''<g {f}><path d="M270 390V170H350V290H650V170H730V390H610V340H390V390Z" fill="#3caea3"/><circle cx="500" cy="315" r="55" fill="#aaa"/><line x1="390" y1="135" x2="610" y2="135" stroke="#e67e22" stroke-width="6"/><text x="370" y="105">Y2 bridge 3.5 mm · total remaining clearance0.8</text><text x="305" y="455">thick side shoulders</text><text x="635" y="455">positive radial stop</text></g>'''),
        SVGS[3]: svg_page("Reaction yoke load path", f'''<g {f}><text x="80" y="135" font-size="21">headed M4 / collar → yoke side shoulders → broad PETG pocket → one-piece hub</text><path d="M100 220H900" stroke="#27ae60" stroke-width="22"/><text x="80" y="310">3.3–3.7 roof = retention/geometry bridge only</text><text x="80" y="370">roof bending alone is NOT credited as torque strength</text></g>'''),
        SVGS[4]: svg_page("Crawler guard old vs new", f'''<g {f}><rect x="180" y="250" width="90" height="150" fill="#d9534f"/><rect x="600" y="175" width="110" height="225" fill="#27ae60"/><path d="M560 400H750L710 330H600Z" fill="#1b7f5a"/><text x="130" y="455">OLD H6 / wall4 / root4 / margin0.9</text><text x="555" y="455">NEW H9 / wall5 / root6 / R3-class gusset / margin3.9</text></g>'''),
        SVGS[5]: svg_page("Crawler lateral shift 1.8", f'''<g {f}><rect x="180" y="240" width="400" height="120" fill="#aaa"/><rect x="620" y="145" width="55" height="215" fill="#27ae60"/><path d="M420 210L610 210" stroke="#e67e22" stroke-width="8" marker-end="url(#a)"/><text x="390" y="185">shift toward guard = 1.8 mm</text><text x="210" y="430">connector protrusion5.1 remains below9mm guard top; CAD static reference only</text></g>'''),
        SVGS[6]: svg_page("Captive nut superseded by rear nut", f'''<g {f}><rect x="120" y="170" width="280" height="180" fill="#e74c3c" opacity=".4"/><line x1="500" y1="100" x2="500" y2="430" stroke="#222"/><rect x="600" y="170" width="280" height="180" fill="#27ae60" opacity=".4"/><text x="160" y="395">v0.9.6.8 hidden/captive nut</text><text x="635" y="395">front head → full through-hole → rear washer/nut</text></g>'''),
        SVGS[7]: svg_page("Rear nut service", f'''<g {f}><rect x="250" y="140" width="380" height="250" fill="#8fc1e3"/><line x1="440" y1="90" x2="440" y2="445" stroke="#222" stroke-width="9"/><polygon points="440,420 500,455 560,420 560,350 500,315 440,350" fill="#aaa"/><text x="590" y="385">visible rear M3 nut</text><text x="270" y="500">hold rear nut with normal tool; actual tool envelope remains HOLD</text></g>'''),
        SVGS[8]: svg_page("Full hub section", f'''<g {f}><rect x="120" y="160" width="760" height="220" fill="#8fc1e3"/><rect x="120" y="125" width="95" height="290" fill="#27ae60"/><rect x="780" y="150" width="100" height="240" fill="#f3b562"/><line x1="265" y1="90" x2="265" y2="430" stroke="#222" stroke-width="7"/><line x1="735" y1="90" x2="735" y2="430" stroke="#222" stroke-width="7"/><text x="105" y="470">rear guard/frame side</text><text x="760" y="470">wide cap/front heads</text></g>'''),
        SVGS[9]: svg_page("Frame to guard clearance", f'''<g {f}><rect x="180" y="170" width="90" height="230" fill="#777"/><rect x="540" y="130" width="130" height="270" fill="#27ae60"/><line x1="270" y1="280" x2="540" y2="280" stroke="#e67e22" stroke-width="4"/><text x="340" y="255">4.4 mm MEASURED</text><text x="250" y="460">8mm spacer installed · guard frame-facing surface frozen · target predicted >=4.0</text></g>'''),
    }


def document_outputs() -> dict[str, str]:
    h = "# Common Rover Reinforced Guard + Reaction Yoke v0.9.6.9\n\nClassification: `DRIVE_REACTION_AND_CRAWLER_PHYSICAL_CORRECTION`  \nRelease: `PHYSICAL COUPON PREPARATION / NOT FOR POWERED OR FIELD USE`  \n"
    return {
        "README.md": h + "\nThis lane freezes the physically matching12T pitch/tooth geometry, records the4.0mm old-shoe overhead conflict, replaces the solid shoe with a low-profile U-yoke, reinforces the anti-climb guard and supersedes the v0.9.6.8 captive nut with a visible rear-nut M3 through-bolt. Print coupons before the full12T.\n",
        "DESIGN_AUTHORITY.md": h + "\nPhysical authority: head-top space4.3, old shoe overhead8.3, guard6/wall4/root4, connector5.1, lateral shift1.8 and8mm-spacer frame gap4.4. Frozen authority: exact one-piece12T, B Ø16.2/R20.4 and headed M4×2. CAD candidates: Y1/Y2/Y3, Y2 design primary,9mm guard and rear-nut through-bolt.\n",
        "PHYSICAL_INPUTS.md": h + "\n|Input|Value|Class|\n|---|---:|---|\n|M4 head-top available|4.3|MEASURED|\n|Old shoe overhead need|8.3|MEASURED|\n|Derived interference|4.0|DERIVED FROM PHYSICAL|\n|Guard H/wall/root|6/4/4|MEASURED|\n|Link body/connector|24.1/5.1|MEASURED|\n|Maximum lateral shift|1.8|MEASURED|\n|8mm spacer frame↔guard|4.4|MEASURED|\n",
        "REACTION_SHOE_GEOMETRIC_FAILURE.md": h + "\n`CURRENT_REACTION_SHOE=GEOMETRICALLY_INCOMPATIBLE_WITH_ACTUAL_M4_HEAD_SPACE`. The blocking dimension is overhead:8.3-4.3=4.0mm. It is not a shallow-pocket or partial-seating problem; increasing a6.8 pocket to7.0 cannot solve it. Physical installed orientation overrides any STL bounding-box axis.\n",
        "LOW_PROFILE_REACTION_YOKE_SPEC.md": h + "\nThe replacement is a U-shaped low-profile bridge with two thick side shoulders, central head/washer relief, broad outer reaction mass, a positive radial stop and service notch. Y1=3.3, Y2=3.5, Y3=3.7mm; Y2 is design primary only. Select the thickest reliable physical fit. The roof is not the sole torque member.\n",
        "REACTION_YOKE_LOAD_PATH.md": h + "\nM4/collar reaction enters tangential yoke side faces and broad main-body pocket surfaces. The thicker side/root sections distribute load into the hub; the3.3–3.7 bridge retains geometry over the head. Cap may retain the yoke axially but does not provide primary reaction.\n",
        "CRAWLER_CLIMB_FAILURE_RECORD.md": h + "\nObserved sequence: lateral drift→connector approaches guard→connector climbs→crawler rises→abnormal guard bending→one guard fractures. `FAILURE_MODE=LATERAL_DRIFT_TO_CONNECTOR_CLIMB`, `CURRENT_GUARD=ANTI_CLIMB_FAIL`, `GUARD_STRENGTH=FAIL_ONE_FRACTURE_USER_REPORTED`. Pitch mismatch is excluded by physical match.\n",
        "ANTI_CLIMB_GUARD_SPEC.md": h + "\nNew guard is9mm high with selected5mm upper wall,6mm root,3mm radial gusset/R3-class root and R1 top-edge design. Connector margin rises from0.9 to3.9mm. Frame-facing Z stays frozen; material grows toward the wheel body. Link-facing wall is near vertical with no inward climbing ramp.1.8mm CAD shift is static only.\n",
        "V0968_CAPTIVE_NUT_SUPERSESSION.md": h + "\nThe v0.9.6.8 internal captive-nut concept is superseded and remains read-only history. v0.9.6.9 has no hidden nut pocket and no PETG thread. It uses complete axial through-holes with visible, accessible rear metal washers and nuts.\n",
        "M3_REAR_NUT_THROUGHBOLT_SPEC.md": h + "\nM3×2 remain at45°/225°, radius23/PCD46. Front: recessed head and optional washer. Rear: exposed washer and removable M3 nut. Exact bolt length and actual nut/tool dimensions are HOLD. The CAD cylinder traverses the complete body and is checked against M4, collar, yokes, root, guard, shaft and service spaces.\n",
        "TORQUE_LOAD_PATH.md": h + "\n`Ø10 shaft → headed M4×2 → metal collar → low-profile reaction yokes×2 → broad PETG pockets → one-piece hub → frozen12T → crawler`. M3 cap bolts and wide cap receive no primary torque credit.\n",
        "SPACER_8MM_PHYSICAL_UPDATE.md": h + "\n8mm spacer remains ID10.2/OD13.8/T8/chamfer0.35. With it installed, frame↔guard clearance4.4mm is physical authority. Other8mm drivetrain checks remain pending. Width remains294mm from170 core or295mm from171 conservative reference.\n",
        "ASSEMBLY_PROCEDURE.md": h + "\n1. Tighten headed M4×2 on the physical collar. 2. Present each yoke from the open cap side and make the short radial seating slide to its stop. 3. Confirm roof/head clearance and broad side contact. 4. Fit wide cap. 5. Pass M3 bolts front-to-rear. 6. Fit accessible rear washers/nuts while holding with a normal tool. 7. Remove in reverse; no hammer.\n",
        "PRINT_PLAN.md": h + "\nBambu A1/PETG. Print first the Y1/Y2/Y3 reaction-yoke coupon, second the rear-nut through-bolt coupon, third the old/new guard coupon. Inspect bridge ceilings, shoulder layer direction, stop/notch, rear tool access, guard root/gusset, top edge and warp. Do not print the full12T until yoke and through-bolt physical PASS.\n",
        "PHYSICAL_TEST_PLAN.md": h + "\nFor each yoke record insertion, top contact, stop, rocking and removal; select the thickest reliable fit. Through-bolt PASS requires complete passage, rear washer/nut fit/tool access, full cap seating, no crack and normal disassembly. After full assembly measure guard gap, push link1.8mm, then rotate50 forward/50 reverse. Stop on climb, crack/whitening, yoke walk, cap lift, M3/nut loosen, M4 shift, frame contact or jam.\n",
        "POWERED_TEST_GATE.md": h + "\n`NOT_YET_APPROVED`. Low-load unloaded power additionally requires yoke PASS, through-bolt cap PASS, reinforced full12T PASS,8mm spacer rotational PASS, final170mm frame, independent shaft non-contact/axial retention, fuse, E-stop/hardware cutoff, polarity, MD10C and cable retention.\n",
        "SAFETY_NOTES.md": h + "\nDRY COUPON WORK ONLY. Disconnect battery during service. Do not credit a thin bridge, cap or M3 bolt as the primary torque member. Do not use permanent adhesive, hidden nut, PETG thread or snap retention. Shaft cutting, powered floor operation, water, mud and field use are not approved.\n",
        "HOLD_REGISTER.md": h + "\n- Final Y1/Y2/Y3 bridge selection until actual M4 coupon\n- Exact M3 length, nut dimensions and rear tool envelope\n- Dynamic guard life, full motor torque, final belt and full12T physical result\n- All other8mm drivetrain checks, shaft cuts and center gap\n- Powered test, water, mud and field deployment\n",
        "SOURCE_TRACE.md": h + "\n- v0.9.6.6 read-only:170mm independent-drive parent and8mm spacer geometry.\n- v0.9.6.8 read-only: exact protected12T/B/M4/cap source; captive-nut and solid-shoe ideas superseded only in this new lane.\n- v0.9.6.7 read-only: rapid BBOX/CBOX authority.\n- User v0.9.6.9: pitch match, guard failure/dimensions,4.3/8.3 overhead authority and4.4 frame gap.\nNo source releases yoke variant, bolt length, shaft cut, dynamic life or powered operation.\n",
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
    write_text(out / "BUILD_LOG.txt", f"version={VERSION}\nclassification={CLASSIFICATION}\npython={sys.version.split()[0]}\ncadquery={cq.__version__}\npaths={len(EXPECTED_PATHS)}\nstep=7\nstl=6\nsvg=10\nbridge_design_mm=3.5\nguard_height_mm=9.0\nshaft_cut=HOLD_PHYSICAL_MEASUREMENT\n")
    write_text(out / "TEST_LOG.txt", "Common Rover v0.9.6.9 contract\nCONTRACT=RUNTIME_PASS_REQUIRED\nSTEP_IMPORT=RUNTIME_PASS_REQUIRED\nSTL_MANIFOLD=RUNTIME_PASS_REQUIRED\nREPRODUCIBILITY=RUNTIME_PASS_REQUIRED\nYOKE_COUPON=PHYSICAL_PENDING\nTHROUGHBOLT_COUPON=PHYSICAL_PENDING\nPOWERED=NOT_YET_APPROVED\n")
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
    write_json(out / "source_evidence.json", source_evidence())
    write_json(out / "collision_report.json", collision_report())
    write_json(out / "validation_report.json", validation_report())
    write_json(out / "reproducibility_report.json", {"version": VERSION, "method": "TWO_ISOLATED_BUILDS_WITH_STEP_NORMALIZATION", "checked": len(EXPECTED_PATHS), "status": "RUNTIME_VERIFICATION_REQUIRED"})
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


def contract_checks(lane: Path = DEFAULT_LANE, repo_checks: bool = True) -> list[tuple[str, bool, str]]:
    p, m, c = PARAMS, geometry_metrics(), collision_report()
    checks: list[tuple[str, bool, str]] = []
    def add(name: str, ok: bool, detail: object) -> None:
        checks.append((name, bool(ok), str(detail)))
    actual = sorted(path.relative_to(lane).as_posix() for path in lane.rglob("*") if path.is_file())
    add("version", p["version"] == VERSION, p["version"])
    add("classification", p["classification"] == CLASSIFICATION, p["classification"])
    add("paths", actual == EXPECTED_PATHS, len(actual))
    add("manifest", (lane / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == EXPECTED_PATHS, len(EXPECTED_PATHS))
    add("sha", sums_ok(lane), len(EXPECTED_PATHS) - 1)
    add("commit-paths", (lane / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() == [(LANE_REL / rel).as_posix() for rel in EXPECTED_PATHS], len(EXPECTED_PATHS))
    add("no-cache", not any(path.name in ("__pycache__", ".pytest_cache") or path.suffix == ".pyc" for path in lane.rglob("*")), "clean")
    pitch = p["pitch"]
    add("pitch-match", pitch["physical_result"] == "PHYSICAL_MATCH" and pitch["status"] == "FROZEN", pitch)
    add("pitch-zero-diff", pitch["difference_mm"] == 0 and pitch["spacing_difference_deg"] == 0, pitch)
    q = p["protected_12t"]
    add("12t-count", q["teeth"] == 12, q)
    add("12t-phase-spacing", q["phase_deg"] == 15 and q["spacing_deg"] == 30, q)
    add("12t-radii", q["tip_radius_mm"] == 33.07 and q["root_radius_mm"] == 29.47, q)
    add("12t-widths", q["tip_width_mm"] == 7.5 and q["root_width_mm"] == 9.5, q)
    add("12t-axial-pitch", q["axial_width_mm"] == 44 and q["pitch_diameter_mm"] == 76.3943726841, q)
    add("12t-overlap", q["buried_root_overlap_mm"] == 4, q)
    add("12t-one-piece", q["outer_body"] == "ONE_PIECE" and m["main_solids"] == 1, m["main_solids"])
    add("12t-no-split-holes", not q["split_teeth"] and q["tooth_root_radial_service_holes"] == 0, q)
    add("12t-external-missing-zero", m["protected_external_missing_mm3"] == 0, m["protected_external_missing_mm3"])
    failure = p["crawler_failure"]
    add("crawler-failure", failure["failure_mode"] == "LATERAL_DRIFT_TO_CONNECTOR_CLIMB", failure)
    add("guard-fail", failure["current_guard"] == "ANTI_CLIMB_FAIL" and failure["strength"].startswith("FAIL_ONE_FRACTURE"), failure)
    guard = p["guard"]
    add("guard-input-height", guard["current_height_mm"] == 6 and guard["link_body_height_mm"] == 24.1, guard)
    add("guard-input-connector", guard["connector_max_protrusion_mm"] == 5.1, guard)
    add("guard-input-wall-root", guard["current_wall_mm"] == guard["failed_root_mm"] == 4, guard)
    add("guard-shift", guard["max_lateral_shift_mm"] == 1.8, guard)
    add("guard-old-margin", guard["current_vertical_margin_mm"] == 0.9 and guard["current_margin_class"] == "INSUFFICIENT", guard)
    add("guard-new-height", guard["new_height_mm"] == 9 and m["guard_height_mm"] == 9, m["guard_height_mm"])
    add("guard-new-margin", guard["connector_vertical_margin_mm"] == 3.9, guard)
    add("guard-wall", 4.5 <= guard["selected_upper_wall_mm"] <= 5.0, guard)
    add("guard-root", guard["root_mm"] == 6 and guard["root_gusset_radial_run_mm"] == 3, guard)
    add("guard-top", guard["top_edge_radius_mm"] == 1 and guard["link_facing_wall"].startswith("NEAR_VERTICAL"), guard)
    add("guard-face-freeze", m["guard_frame_face_z_mm"] == guard["frame_facing_surface_z_mm"] == -26, m)
    add("guard-frame-gap", guard["frame_clearance_measured_mm"] == m["guard_frame_clearance_mm"] == 4.4, m)
    add("guard-frame-zero", m["guard_frame_plane_intersection_mm3"] == 0, m)
    add("guard-dynamic-not-claimed", not guard["dynamic_pass"], guard)
    old = p["old_reaction_shoe"]
    add("head-space", old["head_top_space_mm"] == 4.3, old)
    add("old-shoe-height", old["installed_overhead_requirement_mm"] == 8.3, old)
    add("old-shoe-interference", old["interference_mm"] == 4.0, old)
    add("old-shoe-class", old["status"] == "GEOMETRICALLY_INCOMPATIBLE_WITH_ACTUAL_M4_HEAD_SPACE", old)
    add("old-shoe-not-primary", not old["primary"] and not old["deeper_pocket_fix_valid"], old)
    add("physical-over-stl", old["physical_measurement_precedes_stl_axis_bounds"], old)
    yoke = p["reaction_yoke"]
    add("yoke-architecture", yoke["architecture"] == "LOW_PROFILE_U_SHAPED_REACTION_BRIDGE" and yoke["low_profile_bridge"], yoke)
    add("yoke-no-solid-block", not yoke["solid_overhead_block"], yoke)
    add("yoke-variants", yoke["variants_mm"] == {"Y1": 3.3, "Y2": 3.5, "Y3": 3.7}, yoke)
    add("yoke-clearances", yoke["variant_remaining_clearance_mm"] == {"Y1": 1.0, "Y2": 0.8, "Y3": 0.6}, yoke)
    add("yoke-design", yoke["design_primary_bridge_mm"] == 3.5 and yoke["direct_overlap_max_mm"] == 3.7, yoke)
    add("yoke-selection-pending", yoke["physical_selection"].endswith("PENDING"), yoke)
    add("yoke-shoulders", yoke["side_shoulders"] == "THICK_BROAD_REACTION_SURFACES", yoke)
    add("yoke-roof-rule", "NOT_SOLE_TORQUE" in yoke["roof_role"], yoke)
    add("yoke-stop-removal", yoke["positive_stop"] and yoke["removable"] and not yoke["hammer_required"], yoke)
    add("yoke-service", yoke["service_notch"] and yoke["quantity_per_sprocket"] == 2, yoke)
    add("yoke-mass", min(m["yoke_volumes_mm3"]) >= m["old_shoe_volume_mm3"], m)
    add("yoke-main-zero", m["yoke_a_main_intersection_mm3"] == m["yoke_b_main_intersection_mm3"] == 0, m)
    add("yoke-m4-zero", m["yoke_a_m4_intersection_mm3"] == m["yoke_b_m4_intersection_mm3"] == 0, m)
    add("yoke-mutual-zero", m["yoke_mutual_intersection_mm3"] == 0, m)
    fc = p["full_capture"]
    add("b-selected", fc["selected"] == "B" and fc["B"] == "PHYSICAL_PRIMARY_PASS", fc)
    add("b-geometry", fc["collar_pocket_diameter_mm"] == 16.2 and fc["hardware_cavity_radius_mm"] == 20.4, fc)
    collar = p["collar"]
    add("collar", collar == {"od_mm": 15.9, "id_mm": 10.1, "width_mm": 3.0}, collar)
    m4 = p["m4"]
    add("m4-two-headed", m4["type"] == "HEADED_M4" and m4["count"] == 2 and m4["separation_deg"] == 90, m4)
    add("m4-envelope", m4["head_od_mm"] == 6.8 and m4["washer_od_mm"] == 8.8 and m4["head_height_mm"] == 2.8 and m4["washer_stack_mm"] == 1.8, m4)
    add("m4-unchanged", m4["unchanged"] and m4["grub_screw_primary_count"] == 0, m4)
    lock = p["cap_lock"]
    add("captive-superseded", lock["v0968_captive_nut"] == "SUPERSEDED" and not lock["captive_internal_nut"], lock)
    add("throughbolt", lock["fastener"] == "M3_TRUE_THROUGH_BOLT" and lock["count"] == 2, lock)
    add("throughbolt-layout", lock["angles_deg"] == [45.0, 225.0] and lock["pcd_mm"] == 46, lock)
    add("through-hole", lock["through_hole_diameter_mm"] == 3.4, lock)
    add("rear-hardware", lock["rear_washer"] and lock["rear_nut"] and lock["rear_nut_visible"] and lock["rear_nut_accessible"], lock)
    add("no-petg-snap", not lock["petg_threads"] and not lock["snap_retention"], lock)
    add("m3-not-torque", not lock["primary_torque_path"], lock)
    add("bolt-length-hold", lock["bolt_length"] == "HOLD_PHYSICAL_MEASUREMENT", lock)
    add("m3-main-zero", m["m3_main_intersection_mm3"] == 0, m)
    add("m3-cap-zero", m["m3_cap_intersection_mm3"] == 0, m)
    add("m3-m4-zero", m["m3_m4_intersection_mm3"] == 0, m)
    add("m3-yokes-zero", m["m3_yoke_a_intersection_mm3"] == m["m3_yoke_b_intersection_mm3"] == 0, m)
    add("m3-guard-zero", m["m3_guard_intersection_mm3"] == 0, m)
    add("rear-tool-zero", m["rear_tool_guard_intersection_mm3"] == m["rear_tool_main_intersection_mm3"] == 0, m)
    cap_p = p["cap"]
    add("cap-size", cap_p["outer_diameter_mm"] == 54 and cap_p["thickness_mm"] == 5.5 and m["cap_bounds_mm"] == [54.0, 54.0, 5.5], m)
    add("cap-zero", m["cap_main_intersection_mm3"] == 0, m)
    add("cap-broad", cap_p["broad_seating"] and m["cap_contact_area_sampled_mm2"] >= 850, m)
    add("cap-role", cap_p["snap_fingers"] == 0 and not cap_p["primary_torque_path"], cap_p)
    env = p["envelopes"]
    add("tooth-envelope", env["protected_tooth_axial_mm"] == 44, env)
    add("petg-envelope", m["petg_rotating_axial_mm"] == env["petg_rotating_axial_mm"] == 48, m)
    add("hardware-envelope", m["hardware_axial_mm"] == env["throughbolt_hardware_axial_mm"] == 46.9, m)
    spacer = p["spacer"]
    add("spacer-geometry", [spacer["id_mm"], spacer["od_mm"], spacer["thickness_mm"], spacer["chamfer_mm"]] == [10.2, 13.8, 8.0, 0.35], spacer)
    add("spacer-gap", spacer["frame_guard_clearance_mm"] == 4.4 and spacer["clearance_class"] == "PHYSICAL_MEASURED_4P4MM", spacer)
    add("spacer-other-pending", spacer["other_checks"] == "PHYSICAL_PENDING", spacer)
    add("width", spacer["width_nominal_mm"] == 294 and spacer["width_conservative_mm"] == 295, spacer)
    add("coupon-yoke", m["yoke_coupon_solids"] == 6, m["yoke_coupon_solids"])
    add("coupon-through", m["throughbolt_coupon_solids"] == 2, m["throughbolt_coupon_solids"])
    add("coupon-guard", m["guard_coupon_solids"] == 2, m["guard_coupon_solids"])
    add("collisions", c["known_all_zero"], c)
    add("primary-valid", m["all_primary_valid"], m["all_primary_valid"])
    steps = [lane / rel for rel in CAD if rel.endswith(".step")]
    stls = [lane / rel for rel in CAD if rel.endswith(".stl")]
    add("step-count", len(steps) == 7, len(steps))
    add("step-import", all(cq.importers.importStep(str(path)).solids().size() > 0 for path in steps), len(steps))
    add("stl-count", len(stls) == 6, len(stls))
    add("stl-manifold", all(stl_is_manifold(path) for path in stls), len(stls))
    add("svg-count", len(SVGS) == 10 and all((lane / rel).read_text(encoding="utf-8").startswith("<svg") for rel in SVGS), len(SVGS))
    add("docs-count", len(DOCS) == 19, len(DOCS))
    add("json-count", len(JSONS) == 5 and all(json.loads((lane / rel).read_text(encoding="utf-8")) for rel in JSONS), len(JSONS))
    gates = p["gates"]
    add("coupon-gates", gates["reaction_yoke"] == gates["reinforced_guard"] == gates["m3_throughbolt"] == "READY_FOR_PHYSICAL_COUPON", gates)
    add("full12t-gate", gates["full_12t"] == "PRINT_PENDING_REACTION_YOKE_AND_CAP_COUPON", gates)
    add("power-field", gates["powered"] == "NOT_YET_APPROVED" and gates["field"] == "NOT_APPROVED", gates)
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
    with tempfile.TemporaryDirectory(prefix="v0969_a_") as a, tempfile.TemporaryDirectory(prefix="v0969_b_") as b:
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
    target = Path(r"D:\Downloads") / f"Paddy_Swarm_Common_Rover_Reaction_Yoke_Guard_v0_9_6_9_{stamp}.zip"
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
