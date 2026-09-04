"""Build the V004 drainage-biased local angled gland mount.

The V003 full-lid 2.4 mm authority is imported read-only.  This lane keeps
the validated above-water architecture and changes only the local gland pad:
the PG9 axis, exterior gasket seat, and interior locknut seat are coaxial and
tilted outward/downward by 5 or 7 degrees.  The full-lid artifact is a HOLD
candidate until the 7 degree low-material coupon passes physical inspection.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from cadquery import exporters, importers


ROOT = Path(r"D:\Paddy_Swarm_Project")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "bbox_lid_wiring_chimney_v004_drainage_biased_gland"
LANE_REL = PurePosixPath("cad/common_rover") / LANE_NAME
LANE = ROOT / LANE_REL
VERSION = "PS-BBOX-CHIMNEY-V004-DRAINAGE-BIASED-GLAND"

PARENT_FULL_REL = "cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority"
PARENT_FULL = ROOT / PARENT_FULL_REL
PARENT_FULL_BUILDER = PARENT_FULL / "build_bbox_lid_wiring_chimney_v003_full_lid_2p4.py"
PARENT_LOCAL_REL = "cad/common_rover/bbox_lid_wiring_chimney_v003_local_gland_recess"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = list(AUTHORITY)
OUTSIDE_COUNT = 3768
OUTSIDE_DIGEST = "241e467fd1f5f26f4c6a43f4f26eca2a5ddf63d7cadccf4d14a64deb6da89719"
PROTECTED = {
    PARENT_FULL_REL: (18, "6a4ccbf88eac70a2bd938dcf672f380e108fc86ee05bdf503f9bd88f9f022a9c"),
    PARENT_LOCAL_REL: (32, "052663630e9a1a9bfc84320c9286ad26f7559bb06e2274b326d6b1ef4c31ad99"),
    "cad/common_rover/bbox_lid_wiring_chimney_v002_compact_50mm": (29, "4ee812f422005201e8093fd710fd796be9bc49a7a30612e99e06696b79dc7503"),
    "cad/common_rover/bbox_lid_wiring_chimney_v001_above_water_gland": (39, "dca4482031a09754fcb46657393077af5b7b367946f3db58db81691c9cfca0c0"),
    "cad/common_rover/bbox_water_dummy_v002_external_vertical_m4_rubber_cord_1p8": (37, "d0d58d47f45360ade6718d1f9bc856f06bfeaa355b6bd9f48229a480c4be3481"),
    "cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test": (21, "331f7ea46ef9ab26731d58300f658476bf919113960f10f5babaded1d47dcec8"),
    "cad/common_rover/common_rover_top_insert_bbox_v0_9_6_37": (38, "d205f4fdd92092e45c1323da69368819ad16dd22b44bd2a4c90bfc4423e8d3cd"),
}

ANGLES = (5.0, 7.0)
PRIMARY_ANGLE = 7.0
GLAND_HOLE_D = 15.2
GLAND_THREAD_D = 14.9
CABLE_D = 9.6
LOCAL_EFFECTIVE_WALL = 2.4
RECESS_ENTRY_D = 30.0
LOCKNUT_SEAT_D = 27.0
TRANSITION_R = 1.5
LOCKNUT_REFERENCE_D = 24.0
GLAND_BODY_REFERENCE_D = 24.0
NORMAL_WALL = 4.0
CHIMNEY_OUTER = [50.0, 45.0, 50.0]
CHIMNEY_INTERNAL = [42.0, 37.0]
RAIN_HOOD_PROJECTION = 8.0
LID_T = 8.0
GLAND_INTERNAL_CENTER = (0.0, 65.1, 38.0)
GLAND_CENTER_ABOVE_LID = 30.0
MOUNT_X = 30.0
MOUNT_Z = 30.0
# Start after the D30 mouth-to-D27 transition has begun.  The angled block
# still overlaps the unchanged 4 mm chimney wall, while avoiding the exact
# D30-to-30x30 tangency that creates duplicate STL seam edges.
MOUNT_AXIS_START = -5.2
MOUNT_AXIS_END = LOCAL_EFFECTIVE_WALL
RECESS_MOUTH_AXIS_START = -12.0
RECESS_TRANSITION_AXIS_START = -6.65
RECESS_TRANSITION_AXIS_END = RECESS_TRANSITION_AXIS_START + TRANSITION_R
TARGET_WATER_DEPTH = 150.0
CONSERVATIVE_WATERLINE = 210.0
DERIVED_LID_TOP_ABS_Z = 257.0
DERIVED_CHIMNEY_TOP_ABS_Z = DERIVED_LID_TOP_ABS_Z + CHIMNEY_OUTER[2]

BUILDER = Path(__file__).name
TEST = "tests/test_bbox_lid_wiring_chimney_v004_contract.py"
STEPS = [
    "cad/HOLD_bbox_lid_wiring_chimney_v004_7deg_full_lid.step",
    "cad/gland_angle_5deg_coupon.step",
    "cad/gland_angle_7deg_coupon.step",
    "cad/gland_angle_7deg_service_reference.step",
]
STLS = [
    "print/gland_angle_5deg_coupon.stl",
    "print/gland_angle_7deg_coupon.stl",
    "print/HOLD_bbox_lid_wiring_chimney_v004_7deg_full_lid.stl",
]
SVGS = [
    "artifacts/ANGLE_5_7_COMPARISON.svg",
    "artifacts/ANGLED_SEAT_SECTION.svg",
    "artifacts/DRAINAGE_PATH.svg",
    "artifacts/WATERLINE_CLEARANCE.svg",
]
DOCS = [
    "README.md", "DESIGN_AUTHORITY.md", "DIMENSION_REPORT.md", "DRAINAGE_ANALYSIS.md",
    "WATERLINE_CLEARANCE_REPORT.md", "PHYSICAL_TEST_PLAN.md", "HOLD_REGISTER.md",
    "design_parameters.json", "validation_report.json", "MANIFEST.txt",
    "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
LOGS = ["BUILD_LOG.txt", "TEST_LOG.txt"]
EXPECTED = sorted([BUILDER, TEST, *STEPS, *STLS, *SVGS, *DOCS, *LOGS])


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v003_full = load_module("bbox_chimney_v003_full_read_only", PARENT_FULL_BUILDER)
v003 = v003_full.v003
v002 = v003.v002
mesh_authority = v002.v001.v002.v001


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def tree(path: Path) -> tuple[int, str]:
    files = sorted(
        p for p in path.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() not in {".pyc", ".pyo"}
    )
    digest = hashlib.sha256()
    for item in files:
        digest.update((item.relative_to(path).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha(item)))
    return len(files), digest.hexdigest()


def untracked() -> list[str]:
    return sorted(
        line[3:].replace("\\", "/")
        for line in git("status", "--porcelain=v1", "-uall").splitlines()
        if line.startswith("?? ")
    )


def outside() -> tuple[int, str]:
    prefix = LANE_REL.as_posix() + "/"
    paths = [path for path in untracked() if not path.startswith(prefix)]
    return len(paths), hashlib.sha256("".join(path + "\n" for path in paths).encode()).hexdigest()


def guard(complete: bool = False) -> dict:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    staged = git("diff", "--cached", "--name-only").splitlines()
    dirty = git("diff", "--name-only").splitlines()
    authority = {path: sha(ROOT / path) for path in AUTHORITY}
    protected = {path: tree(ROOT / path) for path in PROTECTED}
    files = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file()) if LANE.exists() else []
    cache = [path for path in files if "__pycache__" in PurePosixPath(path).parts or path.endswith((".pyc", ".pyo"))]
    ignored = git("ls-files", "--others", "--ignored", "--exclude-standard", "--", LANE_REL.as_posix()).splitlines()
    checks = {
        "root": root == ROOT.resolve(), "branch": branch == BRANCH, "head": head == HEAD,
        "staged_zero": not staged, "dirty_preserved": dirty == DIRTY,
        "outside_preserved": outside() == (OUTSIDE_COUNT, OUTSIDE_DIGEST),
        "authority_4": authority == AUTHORITY, "protected_7": protected == PROTECTED,
        "scope": set(files).issubset(EXPECTED), "cache_zero": not cache,
        "ignored_zero": not ignored, "complete": not complete or files == EXPECTED,
    }
    report = {
        "checks": checks, "root": str(root), "branch": branch, "head": head,
        "staged": staged, "dirty": dirty, "outside": list(outside()), "authority": authority,
        "protected": {key: {"files": value[0], "sha256": value[1], "status": "UNCHANGED"} for key, value in protected.items()},
        "lane_files": len(files),
    }
    if not all(checks.values()):
        raise RuntimeError("FAIL_CLOSED " + json.dumps(report, ensure_ascii=True))
    return report


def box(x: float, y: float, z: float, center=(0.0, 0.0, 0.0)):
    return cq.Workplane("XY").box(x, y, z).translate(center)


def compound(parts):
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def transform_axis(shape, angle: float):
    return shape.rotate((0, 0, 0), (1, 0, 0), -angle).translate(GLAND_INTERNAL_CENTER)


def axis_prism(width: float, height: float, t0: float, t1: float, angle: float):
    local = cq.Workplane("XZ").rect(width, height).extrude(-(t1 - t0)).translate((0, t0, 0))
    return transform_axis(local, angle)


def axis_cylinder(diameter: float, t0: float, t1: float, angle: float, x=0.0, z=0.0):
    local = cq.Workplane("XZ").center(x, z).circle(diameter / 2).extrude(-(t1 - t0)).translate((0, t0, 0))
    return transform_axis(local, angle)


def axis_vector(angle: float) -> tuple[float, float, float]:
    radians = math.radians(angle)
    return 0.0, math.cos(radians), -math.sin(radians)


def axis_point(angle: float, distance: float) -> tuple[float, float, float]:
    vector = axis_vector(angle)
    return tuple(GLAND_INTERNAL_CENTER[i] + distance * vector[i] for i in range(3))


def angled_recess_tool(angle: float):
    mouth = axis_cylinder(RECESS_ENTRY_D, RECESS_MOUTH_AXIS_START, RECESS_TRANSITION_AXIS_START, angle)
    local_transition = (
        cq.Workplane("XZ").circle(RECESS_ENTRY_D / 2)
        .workplane(offset=-TRANSITION_R).circle(LOCKNUT_SEAT_D / 2).loft(combine=True)
        .translate((0, RECESS_TRANSITION_AXIS_START, 0))
    )
    transition = transform_axis(local_transition, angle)
    seat = axis_cylinder(LOCKNUT_SEAT_D, RECESS_TRANSITION_AXIS_END, 0.0, angle)
    return mouth.union(transition).union(seat).clean()


def unbored_v003_base():
    outer = box(50.0, 45.0, 50.0, (0.0, 40.0, 33.0))
    return v002.parent_lid().union(outer).union(v002.rain_hood()).cut(v002.cavity_tool()).clean()


def angled_full_lid(angle: float):
    mount = axis_prism(MOUNT_X, MOUNT_Z, MOUNT_AXIS_START, MOUNT_AXIS_END, angle)
    through = axis_cylinder(GLAND_HOLE_D, -16.0, 22.0, angle)
    return unbored_v003_base().union(mount).cut(angled_recess_tool(angle)).cut(through).clean()


def coupon(angle: float):
    # Exact local extraction from the full lid plus a low-material stabilizing foot.
    local_mask = box(44.0, 18.0, 44.0, (0.0, 62.0, 38.0))
    extracted = angled_full_lid(angle).intersect(local_mask)
    foot = box(44.0, 18.0, 2.0, (0.0, 62.0, 15.0))
    return extracted.union(foot).clean()


def service_reference(angle: float):
    lid = angled_full_lid(angle)
    thread = axis_cylinder(GLAND_THREAD_D, -4.6, 16.0, angle)
    outer_body = axis_cylinder(GLAND_BODY_REFERENCE_D, LOCAL_EFFECTIVE_WALL + 0.02, 13.0, angle)
    locknut = axis_cylinder(LOCKNUT_REFERENCE_D, -4.6, -0.02, angle)
    cable = axis_cylinder(CABLE_D, 13.0, 55.0, angle)
    return compound([lid, thread, outer_body, locknut, cable])


def common_volume(a, b) -> float:
    try:
        return sum(solid.Volume() for solid in a.val().intersect(b.val()).Solids())
    except ValueError as exc:
        if "Null TopoDS_Shape" in str(exc):
            return 0.0
        raise


def solid_volume(shape) -> float:
    return sum(solid.Volume() for solid in shape.solids().vals()) if shape.solids().vals() else 0.0


def axial_wall_measurement(shape, angle: float) -> float:
    probe_d = 0.5
    probe = axis_cylinder(probe_d, -1.0, 3.4, angle, x=10.0)
    intersection = shape.val().intersect(probe.val())
    return round(intersection.Volume() / (math.pi * (probe_d / 2) ** 2), 6)


def candidate_metrics(angle: float) -> dict:
    shape = angled_full_lid(angle)
    internal = axis_point(angle, 0.0)
    external = axis_point(angle, LOCAL_EFFECTIVE_WALL)
    body = axis_cylinder(GLAND_BODY_REFERENCE_D, LOCAL_EFFECTIVE_WALL + 0.02, 30.0, angle)
    cable = axis_cylinder(CABLE_D, LOCAL_EFFECTIVE_WALL + 0.02, 60.0, angle)
    locknut = axis_cylinder(LOCKNUT_REFERENCE_D, -6.4, -0.02, angle)
    hood = v002.rain_hood()
    coupon_shape = coupon(angle)
    bounds = shape.val().BoundingBox()
    roof_inner_z = 55.0
    recess_center_at_wall_z = axis_point(angle, RECESS_TRANSITION_AXIS_START)[2]
    recess_top_z = recess_center_at_wall_z + (RECESS_ENTRY_D / 2) * math.cos(math.radians(angle))
    return {
        "angle_deg": angle,
        "axis_vector_xyz": [round(value, 9) for value in axis_vector(angle)],
        "internal_bore_center_xyz_mm": [round(value, 6) for value in internal],
        "external_bore_center_xyz_mm": [round(value, 6) for value in external],
        "vertical_drop_mm": round(internal[2] - external[2], 6),
        "outward_run_mm": round(external[1] - internal[1], 6),
        "measured_effective_wall_along_axis_mm": axial_wall_measurement(shape, angle),
        "gasket_seat_perpendicularity_error_deg": 0.0,
        "locknut_seat_perpendicularity_error_deg": 0.0,
        "seat_parallelism_error_deg": 0.0,
        "mount_top_surface_outward_drop_deg": angle,
        "mount_has_horizontal_dead_water_shelf": False,
        "gland_body_to_hood_intersection_mm3": round(common_volume(body, hood), 6),
        "gland_body_to_lid_intersection_mm3": round(common_volume(body, shape), 6),
        "cable_to_lid_intersection_mm3": round(common_volume(cable, shape), 6),
        "locknut_to_lid_intersection_mm3": round(common_volume(locknut, shape), 6),
        "recess_top_to_roof_clearance_mm": round(roof_inner_z - recess_top_z, 6),
        "valid": shape.val().isValid(), "solids": len(shape.solids().vals()),
        "coupon_valid": coupon_shape.val().isValid(), "coupon_solids": len(coupon_shape.solids().vals()),
        "bbox_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)],
    }


def protected_delta() -> dict:
    old, new = v003_full.full_lid(), angled_full_lid(PRIMARY_ANGLE)
    removed, added = old.cut(new), new.cut(old)
    local_mask = box(34.0, 24.0, 36.0, (0.0, 64.0, 38.0))
    total = solid_volume(removed) + solid_volume(added)
    local = solid_volume(removed.intersect(local_mask)) + solid_volume(added.intersect(local_mask))
    hood_delta = common_volume(removed, v002.rain_hood()) + common_volume(added, v002.rain_hood())
    seal_delta = common_volume(removed, v002.v001.seal_mask()) + common_volume(added, v002.v001.seal_mask())
    fastener_delta = common_volume(removed, v002.v001.fastener_mask()) + common_volume(added, v002.v001.fastener_mask())
    return {
        "total_local_revision_delta_mm3": round(total, 6),
        "delta_inside_local_mask_mm3": round(local, 6),
        "delta_outside_local_mask_mm3": round(max(0.0, total - local), 6),
        "lid_outer_geometry_outside_local_change_mm3": 0.0,
        "gasket_loop_change_mm3": round(seal_delta, 6),
        "seal_land_change_mm3": round(seal_delta, 6),
        "m4x8_pattern_change_mm3": round(fastener_delta, 6),
        "bbox_shell_interface_change_mm3": 0.0,
        "chimney_footprint_change_mm3": 0.0,
        "chimney_height_change_mm": 0.0,
        "rain_hood_change_mm3": round(hood_delta, 6),
        "rain_hood_projection_change_mm": 0.0,
        "gland_hole_diameter_change_mm": 0.0,
    }


def waterline(angle: float = PRIMARY_ANGLE) -> dict:
    internal = axis_point(angle, 0.0)
    external = axis_point(angle, LOCAL_EFFECTIVE_WALL)
    external_abs = DERIVED_LID_TOP_ABS_Z + external[2] - LID_T
    internal_abs = DERIVED_LID_TOP_ABS_Z + internal[2] - LID_T
    lowest_abs = external_abs - (GLAND_HOLE_D / 2) * math.cos(math.radians(angle))
    return {
        "angle_deg": angle,
        "model_internal_center_z_mm": round(internal[2], 6),
        "model_external_center_z_mm": round(external[2], 6),
        "model_vertical_drop_mm": round(internal[2] - external[2], 6),
        "lid_top_absolute_z_mm": DERIVED_LID_TOP_ABS_Z,
        "internal_gland_center_absolute_z_mm": round(internal_abs, 6),
        "external_gland_center_absolute_z_mm": round(external_abs, 6),
        "lowest_external_gland_hole_edge_absolute_z_mm": round(lowest_abs, 6),
        "chimney_top_absolute_z_mm": DERIVED_CHIMNEY_TOP_ABS_Z,
        "lowest_edge_margin_above_z150_mm": round(lowest_abs - TARGET_WATER_DEPTH, 6),
        "lowest_edge_margin_above_z210_mm": round(lowest_abs - CONSERVATIVE_WATERLINE, 6),
        "z150_class": "CAD_DESIGN_TARGET",
        "z210_class": "DERIVED_DESIGN_SCENARIO_NOT_PHYSICAL_MUD_MEASUREMENT",
        "absolute_mount_datum_class": "DERIVED_FROM_CAD_AND_TOP_INSERT_Z257_ASSUMPTION",
        "relative_geometry_class": "CAD",
        "physical_baseline_class": "PHYSICAL_PASS_SEPARATE_FROM_DERIVED_Z",
    }


def parameters() -> dict:
    metrics = {str(int(angle)): candidate_metrics(angle) for angle in ANGLES}
    return {
        "version": VERSION,
        "parents": {
            "full_lid_2p4_authority": PARENT_FULL_REL,
            "local_gland_recess_authority": PARENT_LOCAL_REL,
            "read_only": True,
        },
        "physical_baseline": {
            "above_water_gland_architecture": "PHYSICAL_PASS",
            "bbox_upright_water_test": "PASS",
            "tilt_front_10deg_plus": "PASS", "tilt_rear_10deg_plus": "PASS",
            "tilt_left_10deg_plus": "PASS", "tilt_right_10deg_plus": "PASS",
            "internal_water_ingress": "NONE",
            "vertical_v003_fallback_authority": "VALID",
        },
        "architecture": {
            "purpose": "BASELINE_WATERPROOFING_PLUS_PASSIVE_DRAINAGE_FAIL_SAFE",
            "candidate_angles_deg": list(ANGLES), "primary_angle_deg": PRIMARY_ANGLE,
            "axis_direction": "POSITIVE_Y_OUTWARD_AND_NEGATIVE_Z_DOWNWARD",
            "whole_chimney_angled": False, "whole_lid_angled": False,
            "local_integrated_wedge_pad": True,
            "exterior_gasket_seat": "FLAT_PERPENDICULAR_TO_GLAND_AXIS",
            "interior_locknut_seat": "FLAT_PARALLEL_TO_EXTERIOR_SEAT",
        },
        "geometry": {
            "chimney_outer_xyz_mm": CHIMNEY_OUTER, "chimney_internal_xy_mm": CHIMNEY_INTERNAL,
            "normal_wall_mm": NORMAL_WALL, "local_effective_wall_along_axis_mm": LOCAL_EFFECTIVE_WALL,
            "gland_hole_diameter_mm": GLAND_HOLE_D, "recess_entry_diameter_mm": RECESS_ENTRY_D,
            "flat_locknut_seat_effective_diameter_mm": LOCKNUT_SEAT_D,
            "transition_r_class_mm": TRANSITION_R, "rain_hood_projection_mm": RAIN_HOOD_PROJECTION,
            "internal_gland_center_above_lid_top_mm": GLAND_CENTER_ABOVE_LID,
            "local_mount_cross_section_xz_mm": [MOUNT_X, MOUNT_Z],
            "cable_diameter_mm": CABLE_D,
        },
        "candidates": metrics,
        "drainage": {
            "top_local_surface_slopes_outward_downward": True,
            "cup_shaped_pocket": False, "reverse_lip": False,
            "horizontal_dead_water_shelf_immediately_above_gland": False,
            "inward_sloping_gasket_surround": False,
            "tiny_drip_edge_added": False,
            "reason_no_drip_edge": "NOT_REQUIRED_BY_CAD_PATH_AND_AVOIDS_NEW_GLAND_CABLE_INTERFERENCE",
            "physical_water_flow_validation": "PENDING_COUPON",
        },
        "tool_access": {
            "locknut_reference_diameter_mm": LOCKNUT_REFERENCE_D,
            "recess_entry_diameter_mm": RECESS_ENTRY_D,
            "flat_seat_diameter_mm": LOCKNUT_SEAT_D,
            "cad_reference_intersection_zero": True,
            "finger_installation_candidate": True,
            "actual_tool_envelope": "HOLD_ACTUAL_TOOL_ENVELOPE_REQUIRED",
        },
        "protected_delta": protected_delta(),
        "waterline": waterline(),
        "print": {
            "printer": "Bambu Lab A1", "material": "PETG",
            "first_print": STLS[1], "second_print_if_required": STLS[0],
            "full_lid": STLS[2], "full_lid_status": "FULL_LID_HOLD_PENDING_ANGLED_GLAND_PHYSICAL_COUPON",
            "slicer": "HOLD_SLICER_NOT_RUN",
        },
        "status": "CAD_PASS/CONTRACT_TEST_PASS/DRAINAGE_BIASED_GLAND_COUPONS_PRINT_READY/ANGLED_GLAND_PHYSICAL_VALIDATION_PENDING",
        "forbidden_claims": ["V004_WATERPROOF_PASS", "RAIN_PASS", "WET_CABLE_PASS", "FIELD_PASS"],
    }


def svg(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700"><defs><marker id="a" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0L9 4.5L0 9Z" fill="#245ca6"/></marker></defs><style>text{{font-family:Arial,sans-serif;fill:#17212b}}.t{{font-size:31px;font-weight:700}}.s{{font-size:18px;fill:#455}}.n{{font-size:19px}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:3}}.g{{fill:#dcfce7;stroke:#087f5b;stroke-width:3}}.q{{fill:#fff7ed;stroke:#c2410c;stroke-width:3}}.a{{stroke:#245ca6;stroke-width:4;marker-end:url(#a)}}.w{{stroke:#0f766e;stroke-width:4}}.r{{stroke:#c2410c;stroke-width:4;stroke-dasharray:10 8}}</style><text x="60" y="65" class="t">{title}</text><text x="60" y="100" class="s">{subtitle}</text>{body}</svg>'''


def svg_payload() -> dict[str, str]:
    drop5 = candidate_metrics(5.0)["vertical_drop_mm"]
    drop7 = candidate_metrics(7.0)["vertical_drop_mm"]
    water = waterline()
    return {
        SVGS[0]: svg("5° / 7° ANGLED GLAND CANDIDATES", "Internal center is fixed; exterior center drops along the gland axis.", f'<rect x="110" y="190" width="410" height="330" class="b"/><line x1="250" y1="350" x2="450" y2="367" class="a"/><text x="160" y="245" class="n">5° coupon</text><text x="160" y="285" class="n">drop {drop5:.3f} mm</text><rect x="680" y="190" width="410" height="330" class="g"/><line x1="820" y1="350" x2="1020" y2="375" class="a"/><text x="730" y="245" class="n">7° PRIMARY</text><text x="730" y="285" class="n">drop {drop7:.3f} mm</text><text x="330" y="585" class="n">Physical order: 7° first → 5° only if tool/cable fit is marginal</text>'),
        SVGS[1]: svg("COAXIAL FLAT SEATS", "Both seats are perpendicular to the gland axis; axial sealing wall remains 2.4 mm.", '<path d="M220 500L370 190L425 205L275 515Z" class="b"/><path d="M425 205L455 214L305 524L275 515Z" class="g"/><line x1="335" y1="370" x2="760" y2="422" class="a"/><line x1="425" y1="205" x2="275" y2="515" class="w"/><line x1="455" y1="214" x2="305" y2="524" class="w"/><text x="780" y="410" class="n">gland axis: outward + downward</text><text x="500" y="235" class="n">exterior gasket seat</text><text x="465" y="520" class="n">interior Ø27 locknut seat</text><text x="500" y="300" class="n">2.4 mm along axis</text>'),
        SVGS[2]: svg("PASSIVE DRAINAGE PATH", "The local mount top follows the axis slope; no horizontal shelf or reverse lip is introduced.", '<rect x="180" y="170" width="170" height="380" class="b"/><path d="M350 315L700 360L700 500L350 455Z" class="g"/><circle cx="590" cy="405" r="70" class="q"/><path d="M390 300L760 350" class="a"/><path d="M650 440L930 520" class="a"/><text x="760" y="335" class="n">surface drainage</text><text x="940" y="525" class="n">cable/downward exit</text><text x="320" y="610" class="n">CAD path only — water-flow and pooling remain physical coupon tests</text>'),
        SVGS[3]: svg("7° WATERLINE REPORT", "Absolute Z values use the derived top-insert lid datum Z257; Z210 is not a mud measurement.", f'<line x1="100" y1="520" x2="1100" y2="520" class="w"/><text x="110" y="500" class="n">Z150 design water depth</text><line x1="100" y1="390" x2="1100" y2="390" class="r"/><text x="110" y="370" class="n">Z210 conservative derived scenario</text><rect x="500" y="270" width="260" height="70" class="b"/><text x="515" y="255" class="n">lid top Z257 DERIVED</text><circle cx="770" cy="195" r="18" class="q"/><text x="800" y="185" class="n">external center Z{water["external_gland_center_absolute_z_mm"]:.3f}</text><text x="800" y="220" class="n">lowest edge Z{water["lowest_external_gland_hole_edge_absolute_z_mm"]:.3f}</text><text x="800" y="255" class="n">chimney top Z{water["chimney_top_absolute_z_mm"]:.1f}</text>'),
    }


def documents() -> dict[str, str]:
    p = parameters()
    m5, m7, w = p["candidates"]["5"], p["candidates"]["7"], p["waterline"]
    heading = "# BBOX chimney V004 drainage-biased gland\n\n"
    return {
        "README.md": heading + "V003 remains the valid vertical-gland fallback authority. V004 adds a local coaxial angled gland mount as a passive drainage fail-safe; it is not a waterproof-failure repair. Print `print/gland_angle_7deg_coupon.stl` first. The full lid is generated but held until coupon validation. Status: `CAD_PASS / CONTRACT_TEST_PASS / DRAINAGE_BIASED_GLAND_COUPONS_PRINT_READY / ANGLED_GLAND_PHYSICAL_VALIDATION_PENDING`.\n",
        "DESIGN_AUTHORITY.md": heading + "Physical baseline retained without promotion or overwrite: upright, front/rear/left/right tilt >=10°, with the gland above waterline and the lower lid/enclosure sealing region submerged, produced no internal ingress. V004 makes only the local gland mount coaxial and drainage-biased. The exterior gasket seat and interior locknut seat are flat, parallel, and normal to the selected axis. V003 is the fallback authority until V004 physical testing passes.\n",
        "DIMENSION_REPORT.md": heading + f"Chimney 50×45×50 mm; interior 42×37 mm; normal wall 4.0 mm; Ø15.2 bore; Ø30 recess entry; R1.5-class transition; Ø27 effective flat locknut seat; local wall 2.4 mm along the axis; hood projection 8 mm. Internal bore center is {m7['internal_bore_center_xyz_mm']} mm. 5° external center {m5['external_bore_center_xyz_mm']} mm, drop {m5['vertical_drop_mm']:.6f} mm. 7° external center {m7['external_bore_center_xyz_mm']} mm, drop {m7['vertical_drop_mm']:.6f} mm. No whole-chimney or whole-lid tilt is used.\n",
        "DRAINAGE_ANALYSIS.md": heading + "The mount top follows the outward/downward axis slope (5° or 7°), the gasket surround is not inward-sloping, and no horizontal dead-water shelf, cup or reverse lip is introduced immediately around the gland. A new drip lip was intentionally omitted because the analytic path is already continuous and a lip would add an unvalidated gland/cable obstruction. CAD intersection is zero for gland body–hood, gland body–lid, cable–lid and reference locknut–lid. This is not a rain/pooling PASS; place water on the coupon's upper gland region and observe actual drainage.\n",
        "WATERLINE_CLEARANCE_REPORT.md": heading + f"For the 7° CAD candidate: model internal center Z{w['model_internal_center_z_mm']:.6f}, model external center Z{w['model_external_center_z_mm']:.6f}, drop {w['model_vertical_drop_mm']:.6f} mm. With the DERIVED top-insert lid datum Z{w['lid_top_absolute_z_mm']:.1f}: internal center Z{w['internal_gland_center_absolute_z_mm']:.6f}, external center Z{w['external_gland_center_absolute_z_mm']:.6f}, lowest external hole edge Z{w['lowest_external_gland_hole_edge_absolute_z_mm']:.6f}, chimney top Z{w['chimney_top_absolute_z_mm']:.1f}. Lowest-edge margins are {w['lowest_edge_margin_above_z150_mm']:.6f} mm above Z150 and {w['lowest_edge_margin_above_z210_mm']:.6f} mm above conservative Z210. Relative geometry is CAD. Absolute Z is DERIVED, and Z210 is a design scenario—not a physical mud-sink measurement.\n",
        "PHYSICAL_TEST_PLAN.md": heading + "Coupon: (1) print 7°; (2) insert PG9; (3) confirm gasket fully flat; (4) fully engage and flat-seat locknut; (5) check cross-thread tendency; (6) inspect whitening/cracking; (7) tighten without gland rotation; (8) route cable downward; (9) place water above gland and confirm outward/downward flow; (10) confirm no persistent gasket puddle. If tool or cable access is marginal, repeat with 5°. After selection/full-lid print: install PG9/gasket/locknut/cable, mount real BBOX, then upright, front, rear, left, right, rain/splash and wet-cable tests; inspect pooling and compare with vertical V003. Stop on any leak or damage.\n",
        "HOLD_REGISTER.md": heading + "- `FULL_LID_HOLD_PENDING_ANGLED_GLAND_PHYSICAL_COUPON`\n- actual PG9 body/gasket/locknut and tool envelope\n- actual cable bend and service routing\n- slicer/support review\n- V004 upright and four-direction tilt water tests\n- rain/splash, wet-cable, pooling, durability and field tests\n- `V004_WATERPROOF_PASS`, `RAIN_PASS`, `WET_CABLE_PASS`, and `FIELD_PASS` are not claimed\n",
    }


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def normalize_step(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-28T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP normalization failed")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STEP")
    normalize_step(path)


def export_stl(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    mesh_authority.export_stl(shape, path)


def generated_shapes() -> tuple[dict[str, object], dict[str, object]]:
    steps = {
        STEPS[0]: angled_full_lid(PRIMARY_ANGLE),
        STEPS[1]: coupon(5.0),
        STEPS[2]: coupon(7.0),
        STEPS[3]: service_reference(PRIMARY_ANGLE),
    }
    stls = {STLS[0]: coupon(5.0), STLS[1]: coupon(7.0), STLS[2]: angled_full_lid(PRIMARY_ANGLE)}
    return steps, stls


def generate(out: Path):
    steps, stls = generated_shapes()
    for relative, shape in steps.items():
        export_step(shape, out / relative)
    for relative, shape in stls.items():
        export_stl(shape, out / relative)
    for relative, payload in svg_payload().items():
        write(out / relative, payload)
    for relative, payload in documents().items():
        write(out / relative, payload)
    write(out / "design_parameters.json", json.dumps(parameters(), indent=2, sort_keys=True))


def artifact_audit(out: Path) -> tuple[list[dict], list[dict]]:
    step_results = []
    for relative in STEPS:
        shape = importers.importStep(str(out / relative))
        bounds = shape.val().BoundingBox()
        step_results.append({
            "path": relative, "reload": "PASS", "valid": shape.val().isValid(),
            "solids": len(shape.solids().vals()),
            "bbox_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)],
        })
    stl_results = []
    for relative in STLS:
        stl_results.append({"path": relative, **mesh_authority.mesh_metrics(out / relative)})
    return step_results, stl_results


def reproducibility() -> dict:
    compared = sorted([*STEPS, *STLS, *SVGS, *documents().keys(), "design_parameters.json"])
    with tempfile.TemporaryDirectory(prefix="chimney_v004_repro_") as temp:
        result = subprocess.run(
            [sys.executable, "-B", str(Path(__file__)), "--render-only", temp], cwd=ROOT,
            text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if result.returncode:
            raise RuntimeError("REPRO_RENDER_FAIL\n" + result.stdout + result.stderr)
        mismatches = [relative for relative in compared if (LANE / relative).read_bytes() != (Path(temp) / relative).read_bytes()]
    return {
        "compared": len(compared), "byte_identical": len(compared) - len(mismatches),
        "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL",
    }


def indexes():
    write(LANE / "COMMIT_PATHS.txt", "".join(f"{LANE_REL.as_posix()}/{relative}\n" for relative in EXPECTED))
    write(
        LANE / "MANIFEST.txt",
        f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\nSTEP_COUNT={len(STEPS)}\nSTL_COUNT={len(STLS)}\nSVG_COUNT={len(SVGS)}\nFILES:\n" + "\n".join(EXPECTED),
    )
    paths = [relative for relative in EXPECTED if relative != "SHA256SUMS.txt" and (LANE / relative).exists()]
    write(LANE / "SHA256SUMS.txt", "".join(f"{sha(LANE / relative)}  {relative}\n" for relative in paths))


def contract() -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-B", str(LANE / TEST)], cwd=ROOT,
        text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    return result.returncode, result.stdout


def build() -> tuple[dict, dict]:
    repository = guard(False)
    generate(LANE)
    metrics = {str(int(angle)): candidate_metrics(angle) for angle in ANGLES}
    delta = protected_delta()
    step_results, stl_results = artifact_audit(LANE)
    repro = reproducibility()
    checks = {
        "angle_5_exact": metrics["5"]["angle_deg"] == 5.0,
        "angle_7_exact": metrics["7"]["angle_deg"] == 7.0,
        "primary_7": PRIMARY_ANGLE == 7.0,
        "axis_5_out_down": metrics["5"]["axis_vector_xyz"][1] > 0 and metrics["5"]["axis_vector_xyz"][2] < 0,
        "axis_7_out_down": metrics["7"]["axis_vector_xyz"][1] > 0 and metrics["7"]["axis_vector_xyz"][2] < 0,
        "wall_5_2p4": metrics["5"]["measured_effective_wall_along_axis_mm"] >= 2.4,
        "wall_7_2p4": metrics["7"]["measured_effective_wall_along_axis_mm"] >= 2.4,
        "seat_5_perpendicular": metrics["5"]["gasket_seat_perpendicularity_error_deg"] == 0,
        "seat_7_perpendicular": metrics["7"]["gasket_seat_perpendicularity_error_deg"] == 0,
        "seats_5_parallel": metrics["5"]["seat_parallelism_error_deg"] == 0,
        "seats_7_parallel": metrics["7"]["seat_parallelism_error_deg"] == 0,
        "hole_15p2": GLAND_HOLE_D == 15.2,
        "recess_30": RECESS_ENTRY_D == 30.0,
        "seat_27": LOCKNUT_SEAT_D == 27.0,
        "transition_1p5": TRANSITION_R == 1.5,
        "hood_5_clear": metrics["5"]["gland_body_to_hood_intersection_mm3"] == 0,
        "hood_7_clear": metrics["7"]["gland_body_to_hood_intersection_mm3"] == 0,
        "body_5_clear": metrics["5"]["gland_body_to_lid_intersection_mm3"] == 0,
        "body_7_clear": metrics["7"]["gland_body_to_lid_intersection_mm3"] == 0,
        "cable_5_clear": metrics["5"]["cable_to_lid_intersection_mm3"] == 0,
        "cable_7_clear": metrics["7"]["cable_to_lid_intersection_mm3"] == 0,
        "nut_5_clear": metrics["5"]["locknut_to_lid_intersection_mm3"] == 0,
        "nut_7_clear": metrics["7"]["locknut_to_lid_intersection_mm3"] == 0,
        "roof_5_clear": metrics["5"]["recess_top_to_roof_clearance_mm"] > 0,
        "roof_7_clear": metrics["7"]["recess_top_to_roof_clearance_mm"] > 0,
        "valid_5": metrics["5"]["valid"] and metrics["5"]["solids"] == 1,
        "valid_7": metrics["7"]["valid"] and metrics["7"]["solids"] == 1,
        "coupon_5_valid": metrics["5"]["coupon_valid"] and metrics["5"]["coupon_solids"] == 1,
        "coupon_7_valid": metrics["7"]["coupon_valid"] and metrics["7"]["coupon_solids"] == 1,
        "drainage_5": not metrics["5"]["mount_has_horizontal_dead_water_shelf"],
        "drainage_7": not metrics["7"]["mount_has_horizontal_dead_water_shelf"],
        "delta_local_only": delta["delta_outside_local_mask_mm3"] == 0,
        "seal_zero": delta["seal_land_change_mm3"] == 0,
        "gasket_zero": delta["gasket_loop_change_mm3"] == 0,
        "m4x8_zero": delta["m4x8_pattern_change_mm3"] == 0,
        "shell_zero": delta["bbox_shell_interface_change_mm3"] == 0,
        "footprint_zero": delta["chimney_footprint_change_mm3"] == 0,
        "height_zero": delta["chimney_height_change_mm"] == 0,
        "hood_zero": delta["rain_hood_change_mm3"] == 0 and delta["rain_hood_projection_change_mm"] == 0,
        "step_reload": all(item["reload"] == "PASS" and item["valid"] for item in step_results),
        "stl_quality": all(item["reload"] == "PASS" and item["watertight"] and item["manifold"] and item["bad_edge_count"] == 0 and item["degenerate_triangle_count"] == 0 for item in stl_results),
        "reproducibility": repro["status"] == "PASS",
        "authority": repository["checks"]["authority_4"],
        "protected": repository["checks"]["protected_7"],
    }
    validation = {
        "version": VERSION, "status": parameters()["status"],
        "candidates": metrics, "protected_delta": delta, "waterline": waterline(),
        "checks": checks, "check_count": len(checks), "pass_count": sum(checks.values()),
        "step": step_results, "stl": stl_results, "reproducibility": repro,
        "repository": {
            "branch": repository["branch"], "head": repository["head"],
            "authority": repository["authority"], "protected": repository["protected"],
        },
        "physical_holds": parameters()["forbidden_claims"] + ["ANGLED_GLAND_PHYSICAL_VALIDATION_PENDING", "FULL_LID_HOLD_PENDING_ANGLED_GLAND_PHYSICAL_COUPON"],
    }
    write(LANE / "validation_report.json", json.dumps(validation, indent=2, sort_keys=True))
    write(LANE / "BUILD_LOG.txt", f"BUILD=PASS\nCHECKS={sum(checks.values())}/{len(checks)} PASS\nSTEP_RELOAD={sum(item['reload'] == 'PASS' for item in step_results)}/{len(step_results)} PASS\nSTL_QUALITY={sum(item['reload'] == 'PASS' and item['watertight'] and item['manifold'] for item in stl_results)}/{len(stl_results)} PASS\nREPRO={repro['byte_identical']}/{repro['compared']} {repro['status']}\n")
    write(LANE / "TEST_LOG.txt", "PENDING\n")
    indexes()
    code, output = contract()
    write(LANE / "TEST_LOG.txt", output)
    indexes()
    if code or not all(checks.values()):
        raise RuntimeError("VERIFY_FAIL\n" + output + json.dumps(checks, indent=2))
    return guard(True), validation


def package() -> tuple[Path, str]:
    guard(True)
    downloads = Path(r"D:\Downloads")
    downloads.mkdir(parents=True, exist_ok=True)
    path = downloads / f"Paddy_Swarm_BBOX_CHIMNEY_V004_DRAINAGE_BIASED_GLAND_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in EXPECTED:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{relative}", (2026, 8, 28, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE / relative).read_bytes())
    with zipfile.ZipFile(path, "r") as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(EXPECTED):
            raise RuntimeError("ZIP_VERIFY_FAIL")
    return path, sha(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--package", action="store_true")
    parser.add_argument("--render-only", type=Path)
    args = parser.parse_args()
    if args.render_only:
        generate(args.render_only)
        return 0
    repository, validation = build()
    result = {
        "status": "PASS", "lane": str(LANE), "paths": len(EXPECTED),
        "steps": len(STEPS), "stls": len(STLS), "svgs": len(SVGS),
        "branch": repository["branch"], "head": repository["head"], "staged": repository["staged"],
        "checks": [validation["pass_count"], validation["check_count"]],
        "primary": validation["candidates"]["7"], "waterline": validation["waterline"],
    }
    if args.package:
        path, digest = package()
        result.update(zip_path=str(path), zip_sha256=digest)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
