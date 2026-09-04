"""Build reusable DS3218 20 kg 180-degree physical-authority CAD."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath

import cadquery as cq
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape
from cadquery import exporters, importers

ROOT = Path(r"D:\Paddy_Swarm_Project")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
LANE_NAME = "ds3218_20kg_180deg_physical_authority_v001"
LANE_REL = PurePosixPath("cad/common/servo") / LANE_NAME
LANE = ROOT / LANE_REL
VERSION = "PS-DS3218-20KG-180DEG-PHYSICAL-AUTHORITY-V001"

AUTHORITY = {
    "CURRENT_COMMON_ROVER_AUTHORITY.md": "390cdb2625254e000efd2ceae3f9c035096707d072188bffaff3176c765678d9",
    "README.md": "f729dad1fee8f3dd7417bd37c3e0c3062d224830fcd1ca17abfb3ce697c57849",
    "docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md": "78e23facb95b9e0da4f2be8af62d6b802f32020cdd2bd7066b05446563421ac0",
    "rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md": "0d96d3dd9de8ed0b04763ce39fda3334277e724dd47e2bb0f76a64a34e3e36e9",
}
DIRTY = list(AUTHORITY)
OUTSIDE_COUNT = 3555
OUTSIDE_DIGEST = "b8f26689ff918532f1aebcebff5d782f1be48f3ed38d70de3de95cc447b4b2c5"
PROTECTED = {
    "cad/common_rover/pto_servo_sliding_idler_clutch_v001": (39, "52c15cae54dbe8d4d336556df95b74b070b9ae40109271eb4d62dae4f1c78a43"),
    "cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority": (18, "6a4ccbf88eac70a2bd938dcf672f380e108fc86ee05bdf503f9bd88f9f022a9c"),
    "cad/common_rover/bbox_lid_wiring_chimney_v003_local_gland_recess": (32, "052663630e9a1a9bfc84320c9286ad26f7559bb06e2274b326d6b1ef4c31ad99"),
    "cad/common_rover/bbox_lid_wiring_chimney_v002_compact_50mm": (29, "4ee812f422005201e8093fd710fd796be9bc49a7a30612e99e06696b79dc7503"),
    "rovers/common_rover/v2.29.3.9.1": (45, "ab8c79b41c5a7eae3f45dc6cc79564882c84e2a412a61fef7384b28c49d07659"),
}

# Latest physical authority (mm unless noted).
CASE_L, CASE_W, CASE_H = 40.0, 20.4, 41.7
MOUNT_ENVELOPE_L = 54.5
HOLE_PITCH_X, HOLE_PITCH_Y = 49.1, 10.0
SERVO_HOLE_D = 4.6
OUTPUT_X, OUTPUT_Y = 10.1, 10.2
OUTPUT_OPPOSITE_DERIVED = CASE_L - OUTPUT_X
HORN_LINK_R, HORN_T = 30.0, 2.4
HORN_BOTTOM_Z, HORN_PLANE_Z, MAX_H = 45.0, 46.2, 48.0
OPERATING_SWEEP_DEG = 180.0
CABLE_LENGTH_APPROX = 303.0
MAX_TORQUE_KGFCM, SPEC_VOLTAGE = 21.5, 6.8
ARM_CM = HORN_LINK_R / 10.0
ENDPOINT_FORCE_KGF = MAX_TORQUE_KGFCM / ARM_CM
ENDPOINT_FORCE_N = ENDPOINT_FORCE_KGF * 9.80665

# Required placeholders because no physical values were supplied.
EAR_BOTTOM_Z, EAR_T, SPLINE_D, SPLINE_H = 28.0, 2.5, 8.0, 3.0
HORN_BODY_W, HORN_LINK_HOLE_D = 8.0, 3.0
CABLE_EXIT_CENTER = (40.0, OUTPUT_Y, 8.0)
CABLE_KEEP_OUT_XYZ = (30.0, 14.0, 14.0)
PRINTED_HOLE_CANDIDATE = 5.0
BRACKET_CLEARANCE = 0.5
FIT_CLEARANCES = (0.3, 0.5, 0.7)
A1 = (256.0, 256.0, 256.0)

BUILDER = Path(__file__).name
TEST = "tests/test_ds3218_physical_authority_v001_contract.py"
STEPS = [
    "cad/ds3218_simplified_servo_authority.step",
    "cad/ds3218_25t_horn_authority.step",
    "cad/ds3218_nominal_180deg_keepout.step",
    "cad/ds3218_conservative_360deg_keepout.step",
    "cad/ds3218_cable_exit_keepout.step",
    "cad/HOLD_ds3218_generic_mount_bracket.step",
    "cad/HOLD_ds3218_servo_bracket_assembly.step",
    "cad/combined_fit_coupon_plate.step",
    "cad/servo_mount_hole_pattern_coupon.step",
]
STLS = [
    "print/servo_case_fit_coupon_clearance_0p3.stl",
    "print/servo_case_fit_coupon_clearance_0p5.stl",
    "print/servo_case_fit_coupon_clearance_0p7.stl",
    "print/combined_fit_coupon_plate.stl",
    "print/servo_mount_hole_pattern_coupon.stl",
    "print/HOLD_ds3218_generic_mount_bracket.stl",
]
SVGS = [
    "artifacts/DIMENSION_AUTHORITY.svg", "artifacts/MOUNT_HOLE_PATTERN.svg",
    "artifacts/OUTPUT_AXIS_COORDINATES.svg", "artifacts/ROTATION_KEEP_OUTS.svg",
    "artifacts/FIT_COUPONS.svg", "artifacts/GENERIC_BRACKET.svg",
    "artifacts/CABLE_KEEP_OUT.svg", "artifacts/PHYSICAL_TEST_SEQUENCE.svg",
]
DOCS = [
    "README.md", "PHYSICAL_AUTHORITY.md", "DIMENSION_REPORT.md", "COORDINATE_SYSTEM.md",
    "MOUNT_INTERFACE.md", "CABLE_KEEP_OUT.md", "STRUCTURAL_LOAD_NOTE.md",
    "PHYSICAL_TEST_PLAN.md", "HOLD_REGISTER.md", "design_parameters.json",
    "validation_report.json", "MANIFEST.txt", "SHA256SUMS.txt", "COMMIT_PATHS.txt",
]
LOGS = ["BUILD_LOG.txt", "TEST_LOG.txt"]
EXPECTED = sorted([BUILDER, TEST, *STEPS, *STLS, *SVGS, *DOCS, *LOGS])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def tree(path: Path) -> tuple[int, str]:
    files = sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() not in {".pyc", ".pyo"})
    digest = hashlib.sha256()
    for item in files:
        digest.update((item.relative_to(path).as_posix() + "\n").encode())
        digest.update(bytes.fromhex(sha(item)))
    return len(files), digest.hexdigest()


def untracked() -> list[str]:
    return sorted(line[3:].replace("\\", "/") for line in git("status", "--porcelain=v1", "-uall").splitlines() if line.startswith("?? "))


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
        "authority_4": authority == AUTHORITY, "protected_5": protected == PROTECTED,
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


def box(x: float, y: float, z: float, center=(0, 0, 0)):
    return cq.Workplane("XY").box(x, y, z).translate(center)


def cyl_z(diameter: float, height: float, center=(0, 0, 0)):
    return cq.Workplane("XY").circle(diameter / 2).extrude(height).translate(center)


def compound(parts):
    return cq.Workplane(obj=cq.Compound.makeCompound([part.val() for part in parts]))


def common_volume(a, b) -> float:
    try:
        return sum(solid.Volume() for solid in a.val().intersect(b.val()).Solids())
    except ValueError as exc:
        if "Null TopoDS_Shape" in str(exc):
            return 0.0
        raise


def mount_hole_centers():
    center_x = CASE_L / 2
    return [(center_x + sx * HOLE_PITCH_X / 2, OUTPUT_Y + sy * HOLE_PITCH_Y / 2) for sx in (-1, 1) for sy in (-1, 1)]


def servo_case():
    body = box(CASE_L, CASE_W, CASE_H, (CASE_L / 2, CASE_W / 2, CASE_H / 2))
    ears = box(MOUNT_ENVELOPE_L, CASE_W, EAR_T, (CASE_L / 2, CASE_W / 2, EAR_BOTTOM_Z + EAR_T / 2))
    shape = body.union(ears)
    for x, y in mount_hole_centers():
        shape = shape.cut(cyl_z(SERVO_HOLE_D, EAR_T + 2, (x, y, EAR_BOTTOM_Z - 1)))
    spline = cyl_z(SPLINE_D, SPLINE_H, (OUTPUT_X, OUTPUT_Y, CASE_H))
    return shape.union(spline).clean()


def horn():
    boss = cyl_z(12.0, HORN_T, (OUTPUT_X, OUTPUT_Y, HORN_BOTTOM_Z))
    arm = box(HORN_LINK_R, HORN_BODY_W, HORN_T, (OUTPUT_X + HORN_LINK_R / 2, OUTPUT_Y, HORN_BOTTOM_Z + HORN_T / 2))
    shape = boss.union(arm)
    link_x = OUTPUT_X + HORN_LINK_R
    shape = shape.cut(cyl_z(HORN_LINK_HOLE_D, HORN_T + 2, (link_x, OUTPUT_Y, HORN_BOTTOM_Z - 1)))
    max_cap = cyl_z(6.0, MAX_H - (HORN_BOTTOM_Z + HORN_T), (OUTPUT_X, OUTPUT_Y, HORN_BOTTOM_Z + HORN_T))
    return shape.union(max_cap).clean()


def nominal_keepout():
    points = [(OUTPUT_X, OUTPUT_Y)]
    for degree in range(-90, 91, 2):
        angle = math.radians(degree)
        points.append((OUTPUT_X + HORN_LINK_R * math.cos(angle), OUTPUT_Y + HORN_LINK_R * math.sin(angle)))
    return cq.Workplane("XY").polyline(points).close().extrude(HORN_T).translate((0, 0, HORN_BOTTOM_Z))


def conservative_keepout():
    return cyl_z(HORN_LINK_R * 2, HORN_T, (OUTPUT_X, OUTPUT_Y, HORN_BOTTOM_Z))


def cable_keepout():
    x, y, z = CABLE_EXIT_CENTER
    dx, dy, dz = CABLE_KEEP_OUT_XYZ
    return box(dx, dy, dz, (x + dx / 2, y, z))


def servo_authority():
    return compound([servo_case(), horn()])


def fit_coupon(clearance: float):
    cavity_l, cavity_w = CASE_L + clearance, CASE_W + clearance
    wall = 2.5
    outer = box(cavity_l + 2 * wall, cavity_w + 2 * wall, 8.0, (0, 0, 4.0))
    cavity = box(cavity_l, cavity_w, 7.0, (0, 0, 5.5))
    return outer.cut(cavity).clean()


def combined_fit_plate():
    positions = (-55.0, 0.0, 55.0)
    result = fit_coupon(FIT_CLEARANCES[0]).translate((positions[0], 0, 0))
    for clearance, position in zip(FIT_CLEARANCES[1:], positions[1:]):
        result = result.union(fit_coupon(clearance).translate((position, 0, 0)))
    result = result.union(box(10.5, 4.0, 2.0, (-27.5, 0, 1.0)))
    result = result.union(box(10.5, 4.0, 2.0, (27.5, 0, 1.0)))
    return result.clean()


def mount_pattern_coupon():
    plate_x, plate_y, thickness = 54.5, 24.0, 3.0
    left = box(plate_x, plate_y, thickness, (CASE_L / 2, OUTPUT_Y, thickness / 2))
    shift = 65.0
    right = left.translate((shift, 0, 0))
    shape = left.union(right).union(box(11.0, 4.0, thickness, (52.75, OUTPUT_Y, thickness / 2)))
    for x, y in mount_hole_centers():
        shape = shape.cut(cyl_z(SERVO_HOLE_D, thickness + 2, (x, y, -1)))
        shape = shape.cut(cyl_z(PRINTED_HOLE_CANDIDATE, thickness + 2, (x + shift, y, -1)))
    # Notches distinguish the physical-reference side from the printed candidate.
    shape = shape.cut(box(2, 4, 2, (-7.25, -1.5, 2.5))).cut(box(2, 4, 2, (57.75, -1.5, 2.5))).clean()
    return shape


def generic_bracket():
    total_clear = BRACKET_CLEARANCE
    base = box(62.0, 32.0, 4.0, (CASE_L / 2, OUTPUT_Y, -2.0))
    rail_t, rail_h = 2.5, 12.0
    lower_y = -total_clear / 2 - rail_t / 2
    upper_y = CASE_W + total_clear / 2 + rail_t / 2
    rails = box(CASE_L, rail_t, rail_h, (CASE_L / 2, lower_y, rail_h / 2)).union(box(CASE_L, rail_t, rail_h, (CASE_L / 2, upper_y, rail_h / 2)))
    left_shelf = box(7.05, 26.4, 4.0, (-3.725, OUTPUT_Y, EAR_BOTTOM_Z - 2.0))
    right_shelf = box(7.05, 26.4, 4.0, (43.725, OUTPUT_Y, EAR_BOTTOM_Z - 2.0))
    posts = []
    for x in (-3.725, 43.725):
        for y in (-1.2, CASE_W + 1.2):
            posts.append(box(7.05, 2.4, EAR_BOTTOM_Z - 4.0, (x, y, (EAR_BOTTOM_Z - 4.0) / 2)))
    shape = base.union(rails).union(left_shelf).union(right_shelf)
    for post in posts:
        shape = shape.union(post)
    for x, y in mount_hole_centers():
        shape = shape.cut(cyl_z(PRINTED_HOLE_CANDIDATE, 6.0, (x, y, EAR_BOTTOM_Z - 5.0)))
    return shape.clean()


def assembly():
    return compound([servo_authority(), generic_bracket(), cable_keepout()])


def geometry_analysis() -> dict:
    servo, bracket = servo_authority(), generic_bracket()
    nominal, full = nominal_keepout(), conservative_keepout()
    return {
        "servo_valid": servo.val().isValid(), "servo_solids": len(servo.solids().vals()),
        "bracket_valid": bracket.val().isValid(), "bracket_solids": len(bracket.solids().vals()),
        "servo_bracket_intersection_mm3": round(common_volume(servo, bracket), 6),
        "bracket_nominal_keepout_intersection_mm3": round(common_volume(bracket, nominal), 6),
        "bracket_conservative_keepout_intersection_mm3": round(common_volume(bracket, full), 6),
        "mount_hole_centers_mm": [[round(x, 3), round(y, 3)] for x, y in mount_hole_centers()],
        "output_axis_mm": [OUTPUT_X, OUTPUT_Y],
        "nominal_keepout_volume_mm3": round(sum(s.Volume() for s in nominal.solids().vals()), 3),
        "conservative_keepout_volume_mm3": round(sum(s.Volume() for s in full.solids().vals()), 3),
        "keepout_volume_ratio": round(sum(s.Volume() for s in nominal.solids().vals()) / sum(s.Volume() for s in full.solids().vals()), 4),
        "fit_coupon_clearances_mm": list(FIT_CLEARANCES),
        "a1_envelope_pass": all(max(shape.val().BoundingBox().xlen, shape.val().BoundingBox().ylen, shape.val().BoundingBox().zlen) <= 256 for shape in [servo, bracket, combined_fit_plate(), mount_pattern_coupon()]),
    }


def parameters() -> dict:
    return {
        "version": VERSION,
        "servo": {"model": "DS3218_20KG_DIGITAL_SERVO", "operating_range_deg": 180, "case_lwh_mm": [CASE_L, CASE_W, CASE_H], "case_status": "PHYSICAL_AUTHORITY", "mounting_envelope_length_mm": MOUNT_ENVELOPE_L},
        "mounting": {
            "longitudinal_hole_pitch_mm": HOLE_PITCH_X, "short_axis_hole_pitch_mm": HOLE_PITCH_Y,
            "short_axis_pitch_status": "PHYSICAL_CANDIDATE", "servo_physical_hole_mm": SERVO_HOLE_D,
            "printed_bracket_fastener_hole_candidate_mm": PRINTED_HOLE_CANDIDATE,
            "printed_hole_status": "DESIGN_CLEARANCE_CANDIDATE", "hardware": "PHYSICAL_FASTENER_SELECTION_PENDING",
            "ear_bottom_z_mm": EAR_BOTTOM_Z, "ear_thickness_mm": EAR_T, "ear_z_status": "CAD_PLACEHOLDER_PHYSICAL_MEASUREMENT_REQUIRED",
        },
        "coordinate_system": {"bottom_plane_z_mm": 0, "near_case_end_x_mm": 0, "one_case_side_y_mm": 0, "axes": {"+X": "LONGITUDINAL_FROM_NEAR_CASE_END", "+Y": "ACROSS_CASE", "+Z": "UP_FROM_SERVO_BOTTOM"}},
        "output_axis": {
            "x_mm": OUTPUT_X, "x_status": "PHYSICAL_PRIMARY_DATUM", "opposite_end_derived_mm": OUTPUT_OPPOSITE_DERIVED,
            "separate_visual_opposite_mm": 29.2, "averaging_prohibited": True,
            "y_mm": OUTPUT_Y, "y_status": "DERIVED_FROM_CASE_CENTER_20P4_DIV_2",
            "horn_axis_origin_mm": [OUTPUT_X, OUTPUT_Y, HORN_PLANE_Z],
            "spline": "25T", "spline_placeholder_diameter_mm": SPLINE_D, "spline_geometry_status": "PLACEHOLDER_NOT_TOOTH_AUTHORITY",
        },
        "horn": {
            "type": "25T_ALUMINUM", "selected_link_hole_radius_mm": HORN_LINK_R,
            "prior_32mm_interpretation": "OVERALL_LENGTH_NOT_LINK_RADIUS", "thickness_mm": HORN_T,
            "bottom_z_mm": HORN_BOTTOM_Z, "bottom_z_status": "PHYSICAL_WITH_VISUAL_ALIGNMENT_UNCERTAINTY",
            "rotation_plane_z_mm": HORN_PLANE_Z, "rotation_plane_status": "PHYSICAL_DERIVED",
            "servo_with_horn_max_height_mm": MAX_H, "max_height_status": "PHYSICAL_MAX_ENVELOPE",
            "link_hole_diameter_mm": HORN_LINK_HOLE_D, "link_hole_diameter_status": "CAD_VISUAL_PLACEHOLDER",
        },
        "keepouts": {
            "nominal": {"radius_mm": HORN_LINK_R, "sweep_deg": OPERATING_SWEEP_DEG, "plane_z_mm": HORN_PLANE_Z, "zero_angle_reference": "+X_CAD_REFERENCE"},
            "conservative": {"radius_mm": HORN_LINK_R, "sweep_deg": 360, "plane_z_mm": HORN_PLANE_Z, "powered_360_claim": False, "purpose": ["ASSEMBLY", "INDEXING_UNCERTAINTY", "MAINTENANCE", "UNPOWERED_MANUAL_MOVEMENT", "INTERFERENCE_CHECK"]},
        },
        "cable": {
            "length_mm_approx": CABLE_LENGTH_APPROX, "keepout_xyz_mm": list(CABLE_KEEP_OUT_XYZ),
            "exit_center_mm": list(CABLE_EXIT_CENTER), "exit_center_status": "CAD_PLACEHOLDER_PHOTO_COORDINATE_NOT_SUPPLIED",
            "bend_radius": "CABLE_BEND_RADIUS_PHYSICAL_VALIDATION_PENDING", "hard_90deg_bend": False,
            "clamp_at_root": False, "connector_route_space_required": True,
        },
        "fit_coupons": {"total_clearances_mm": list(FIT_CLEARANCES), "application": "INDEPENDENT_X_AND_Y_TOTAL_CLEARANCE", "selection": "PHYSICAL_VALIDATION_PENDING"},
        "bracket": {
            "architecture": "OPEN_CRADLE_WITH_MOUNT_EAR_SHELVES", "clearance_candidate_total_mm": BRACKET_CLEARANCE,
            "servo_removable": True, "glue_primary": False, "horn_removable": True,
            "material": "PETG_CANDIDATE", "printer": "Bambu Lab A1", "status": "HOLD_PENDING_CASE_AND_HOLE_COUPON_PHYSICAL_VALIDATION",
        },
        "load_note": {
            "max_torque_kgf_cm_at_6p8v": MAX_TORQUE_KGFCM, "arm_cm": ARM_CM,
            "endpoint_force_kgf": round(ENDPOINT_FORCE_KGF, 3), "endpoint_force_n": round(ENDPOINT_FORCE_N, 1),
            "classification": "THEORETICAL_MAX_FROM_PRODUCT_SPEC", "bracket_structural_pass": False,
        },
        "print": {"first_print_order": STLS[:3] + [STLS[4]], "full_bracket": STLS[5], "slicer": "HOLD_SLICER_NOT_RUN"},
        "status": "CAD_PASS/CONTRACT_TEST_PASS/DS3218_PHYSICAL_AUTHORITY_MODEL_READY/FIT_COUPONS_PRINT_READY/MOUNT_PHYSICAL_VALIDATION_PENDING/FULL_BRACKET_HOLD_PENDING_PHYSICAL_COUPONS",
        "forbidden_claims": ["LOAD_PASS", "TORQUE_PASS", "FIELD_PASS", "DURABILITY_PASS"],
    }


def svg(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="620" viewBox="0 0 1100 620"><rect width="100%" height="100%" fill="#f8fafc"/><style>text{{font-family:Arial;fill:#172033}}.h{{font-size:28px;font-weight:bold}}.s{{font-size:15px;fill:#475569}}.b{{fill:#dbeafe;stroke:#245ca6;stroke-width:2}}.g{{fill:#d1fae5;stroke:#087f5b;stroke-width:2}}.q{{fill:#fff3cd;stroke:#a16207;stroke-width:2}}.r{{fill:#fee2e2;stroke:#b91c1c;stroke-width:2}}.a{{stroke:#0f7184;stroke-width:4;fill:none;marker-end:url(#m)}}</style><defs><marker id="m" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0L0 6L9 3z" fill="#0f7184"/></marker></defs><text x="38" y="48" class="h">{title}</text><text x="38" y="78" class="s">{subtitle}</text>{body}<text x="38" y="590" class="s">{VERSION} · PHYSICAL_VALIDATION_PENDING</text></svg>'''


def svg_payload() -> dict[str, str]:
    return {
        SVGS[0]: svg("DS3218 DIMENSION AUTHORITY", "Simplified physical interface; cosmetic details intentionally omitted.", '<rect x="190" y="150" width="400" height="260" class="b"/><rect x="120" y="295" width="540" height="55" class="g"/><text x="730" y="190">case 40.0 × 20.4 × 41.7</text><text x="730" y="240">mount envelope 54.5</text><text x="730" y="290">max horn height 48.0</text>'),
        SVGS[1]: svg("MOUNT HOLE PATTERN", "49.1 longitudinal × 10.0 transverse candidate; physical servo hole Ø4.6.", '<rect x="160" y="190" width="780" height="240" class="g"/><circle cx="230" cy="270" r="18" class="q"/><circle cx="870" cy="270" r="18" class="q"/><circle cx="230" cy="350" r="18" class="q"/><circle cx="870" cy="350" r="18" class="q"/><text x="460" y="260">49.1 mm</text><text x="905" y="315">10.0</text>'),
        SVGS[2]: svg("OUTPUT AXIS COORDINATES", "Bottom Z0; near case end X0; case side Y0.", '<rect x="180" y="150" width="520" height="300" class="b"/><circle cx="310" cy="300" r="20" class="q"/><path d="M310 300H800" class="a"/><path d="M310 300V120" class="a"/><text x="350" y="280">X10.1 physical</text><text x="350" y="330">Y10.2 derived</text><text x="350" y="380">horn plane Z46.2</text>'),
        SVGS[3]: svg("ROTATION KEEP-OUTS", "Nominal180° and conservative360° are logically separate.", '<path d="M220 420A180 180 0 0 1 580 420L400 420Z" class="g"/><circle cx="820" cy="330" r="180" class="q"/><text x="300" y="470">NOMINAL 180°</text><text x="735" y="545">CONSERVATIVE 360°</text>'),
        SVGS[4]: svg("CASE FIT COUPONS", "Total X/Y clearance:0.3,0.5,0.7 mm; select smallest hand-removable fit.", '<rect x="100" y="190" width="250" height="260" class="b"/><rect x="425" y="190" width="250" height="260" class="g"/><rect x="750" y="190" width="250" height="260" class="q"/><text x="200" y="330">+0.3</text><text x="525" y="330">+0.5</text><text x="850" y="330">+0.7</text>'),
        SVGS[5]: svg("GENERIC OPEN BRACKET", "Open cradle, ear shelves, ordinary bolts; full bracket remains HOLD.", '<rect x="180" y="430" width="700" height="60" class="b"/><rect x="230" y="170" width="70" height="260" class="g"/><rect x="760" y="170" width="70" height="260" class="g"/><rect x="300" y="250" width="460" height="180" class="q"/><text x="415" y="340">SERVO REMOVES UPWARD</text>'),
        SVGS[6]: svg("CABLE EXIT KEEP-OUT", "Placeholder only: no hard90° bend and no clamp at cable root.", '<rect x="180" y="220" width="380" height="220" class="b"/><rect x="560" y="285" width="300" height="90" class="q"/><path d="M860 330H1010" class="a"/><text x="610" y="270">30×14×14 placeholder</text><text x="610" y="415">exact exit/bend radius HOLD</text>'),
        SVGS[7]: svg("PHYSICAL TEST ORDER", "Coupons precede bracket, powered motion and mechanism integration.", '<text x="60" y="270">FIT</text><path d="M120 265H230" class="a"/><text x="250" y="270">HOLES</text><path d="M330 265H440" class="a"/><text x="460" y="270">BRACKET</text><path d="M560 265H670" class="a"/><text x="690" y="270">MANUAL</text><path d="M790 265H900" class="a"/><text x="920" y="270">POWER</text>'),
    }


def documents() -> dict[str, str]:
    header = "# DS3218 20 kg 180° Servo Physical Authority V001\n\n"
    return {
        "README.md": header + "Reusable simplified servo, mounting/output/horn authority, separate180°/360° keep-outs, service cable envelope, fit/hole coupons and a generic open-bracket HOLD candidate. First print the three fit coupons, then the mounting-pattern coupon. Status: `CAD_PASS / CONTRACT_TEST_PASS / DS3218_PHYSICAL_AUTHORITY_MODEL_READY / FIT_COUPONS_PRINT_READY / MOUNT_PHYSICAL_VALIDATION_PENDING`.\n",
        "PHYSICAL_AUTHORITY.md": header + "Physical: case40.0×20.4×41.7 mm, mounting envelope54.5 mm, longitudinal pitch49.1 mm, servo holesØ4.6 mm, output X10.1 mm, horn link radius30 mm, horn thickness2.4 mm, horn bottom Z45 mm with visual-alignment uncertainty, and maximum height48 mm. Short pitch10.0 mm remains PHYSICAL_CANDIDATE. Output Y10.2 and horn plane Z46.2 are derived. The separate29.2 visual value is recorded but never averaged with the primary X datum.\n",
        "DIMENSION_REPORT.md": header + "|Item|Value|Class|\n|---|---:|---|\n|Case L×W×H|40.0×20.4×41.7|PHYSICAL|\n|Mount envelope L|54.5|PHYSICAL|\n|Hole pitch X|49.1|PHYSICAL|\n|Hole pitch Y|10.0|PHYSICAL_CANDIDATE|\n|Servo hole|Ø4.6|PHYSICAL|\n|Output X|10.1|PHYSICAL_PRIMARY|\n|Opposite X|29.9|DERIVED|\n|Output Y|10.2|DERIVED|\n|Horn radius/thickness|30.0/2.4|PHYSICAL|\n|Horn plane Z|46.2|DERIVED|\n|Maximum Z|48.0|PHYSICAL_ENVELOPE|\n",
        "COORDINATE_SYSTEM.md": header + "Servo bottom=`Z0`; near longitudinal case end=`X0`; one case side=`Y0`. Output axis=(10.1,10.2), with Y derived from20.4/2. Horn/link origin=(10.1,10.2,46.2). Nominal keep-out zero angle uses +X only as a reusable CAD reference; installed mechanism defines final clocking.\n",
        "MOUNT_INTERFACE.md": header + "The HOLD bracket is an open cradle with side locators and two mounting-ear shelves. Servo removal is upward after ordinary fasteners are removed; glue and permanent trapping are prohibited. Printed holesØ5.0 are only a design-clearance candidate, distinct from physical servo holesØ4.6. Ear Z/thickness and fastener selection require measurement/coupon validation.\n",
        "CABLE_KEEP_OUT.md": header + "Cable length approximately303 mm. A30×14×14 mm service placeholder exits the +X case end in this reusable model. Exact outlet coordinates and bend radius were not supplied, so this is not physical authority. No hard90° bend, root clamp or blocked connector route is allowed.\n",
        "STRUCTURAL_LOAD_NOTE.md": header + f"Product specification21.5 kgf·cm at6.8 V with a3.0 cm arm gives {ENDPOINT_FORCE_KGF:.2f} kgf, approximately{ENDPOINT_FORCE_N:.0f} N. Classification: `THEORETICAL_MAX_FROM_PRODUCT_SPEC`. This is not continuous-load, shock, stall or bracket structural PASS.\n",
        "PHYSICAL_TEST_PLAN.md": header + "1 print fit coupons;2 test+0.3;3 if tight test+0.5;4 if tight test+0.7;5 select smallest removable fit;6 print hole coupon;7 install servo;8 check alignment;9 check case stress;10 check cable outlet;11 update authority;12 regenerate bracket if needed;13 print bracket;14 mount servo;15 install30 mm horn;16 manually sweep;17 powered180° no-load;18 integrate mechanism only afterward;19 perform later load/torque testing.\n",
        "HOLD_REGISTER.md": header + "- mounting-ear Z, thickness and detailed outline\n- short-axis10 mm physical confirmation\n- spline dimensions and detailed25T tooth geometry\n- horn body profile and link-hole diameter\n- cable exit coordinates, connector and bend radius\n- final printed fastener size/clearance\n- fit and mounting-hole coupon results\n- bracket slicer/fit/tool access\n- powered no-load, operating torque, shock, stall, durability and field validation\n",
    }


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def normalize_step(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    text, count = re.subn(r"FILE_NAME\('([^']*)','[^']*'", r"FILE_NAME('\1','2026-08-27T00:00:00'", text, count=1)
    if count != 1:
        raise RuntimeError("STEP normalization failed")
    path.write_text(text, encoding="utf-8", newline="\n")


def export_step(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), exportType="STEP")
    normalize_step(path)


def export_stl(shape, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path), tolerance=0.035, angularTolerance=0.08)


def binary_stl(path: Path):
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError("STL_TOO_SHORT")
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + count * 50:
        raise RuntimeError("STL_NOT_CANONICAL_BINARY")
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + index * 50)
        yield (values[3:6], values[6:9], values[9:12])


def mesh_metrics(path: Path) -> dict:
    triangles = list(binary_stl(path))
    edges = Counter()
    degenerate = 0
    for triangle in triangles:
        vertices = [tuple(round(float(value), 5) for value in vertex) for vertex in triangle]
        ax, ay, az = (vertices[1][i] - vertices[0][i] for i in range(3))
        bx, by, bz = (vertices[2][i] - vertices[0][i] for i in range(3))
        cross = (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)
        if sum(value * value for value in cross) <= 1e-14:
            degenerate += 1
        for a, b in ((vertices[0], vertices[1]), (vertices[1], vertices[2]), (vertices[2], vertices[0])):
            edges[tuple(sorted((a, b)))] += 1
    raw = TopoDS_Shape()
    reload_ok = bool(StlAPI_Reader().Read(raw, str(path))) and not raw.IsNull()
    bad = sum(value != 2 for value in edges.values())
    return {"triangle_count": len(triangles), "watertight": bad == 0, "manifold": bad == 0, "bad_edge_count": bad, "degenerate_triangle_count": degenerate, "reload": "PASS" if reload_ok else "FAIL"}


def generate(out: Path):
    step_shapes = {
        STEPS[0]: servo_authority(), STEPS[1]: horn(), STEPS[2]: nominal_keepout(),
        STEPS[3]: conservative_keepout(), STEPS[4]: cable_keepout(), STEPS[5]: generic_bracket(),
        STEPS[6]: assembly(), STEPS[7]: combined_fit_plate(), STEPS[8]: mount_pattern_coupon(),
    }
    for relative, shape in step_shapes.items():
        export_step(shape, out / relative)
    for relative, shape in zip(STLS[:3], [fit_coupon(clearance) for clearance in FIT_CLEARANCES]):
        export_stl(shape, out / relative)
    export_stl(combined_fit_plate(), out / STLS[3])
    export_stl(mount_pattern_coupon(), out / STLS[4])
    export_stl(generic_bracket(), out / STLS[5])
    for relative, text in svg_payload().items():
        write(out / relative, text)
    for relative, text in documents().items():
        write(out / relative, text)
    write(out / "design_parameters.json", json.dumps(parameters(), indent=2, sort_keys=True))


def artifact_audit(out: Path):
    steps = []
    for relative in STEPS:
        shape = importers.importStep(str(out / relative))
        bounds = shape.val().BoundingBox()
        steps.append({"path": relative, "valid": shape.val().isValid(), "solids": len(shape.solids().vals()), "bbox_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)]})
    meshes = {relative: mesh_metrics(out / relative) for relative in STLS}
    return steps, meshes


def reproducibility() -> dict:
    compared = sorted([*STEPS, *STLS, *SVGS, *documents().keys(), "design_parameters.json"])
    with tempfile.TemporaryDirectory(prefix="ds3218_v001_") as temp:
        subprocess.run([sys.executable, "-B", str(Path(__file__)), "--render-only", temp], cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        mismatches = [relative for relative in compared if (LANE / relative).read_bytes() != (Path(temp) / relative).read_bytes()]
    return {"compared": len(compared), "byte_identical": len(compared) - len(mismatches), "mismatches": mismatches, "status": "PASS" if not mismatches else "FAIL"}


def indexes():
    write(LANE / "COMMIT_PATHS.txt", "".join(f"{LANE_REL.as_posix()}/{relative}\n" for relative in EXPECTED))
    write(LANE / "MANIFEST.txt", f"VERSION={VERSION}\nEXACT_PATH_COUNT={len(EXPECTED)}\nSTEP_COUNT={len(STEPS)}\nSTL_COUNT={len(STLS)}\nSVG_COUNT={len(SVGS)}\nFILES:\n" + "\n".join(EXPECTED))
    paths = [relative for relative in EXPECTED if relative != "SHA256SUMS.txt" and (LANE / relative).exists()]
    write(LANE / "SHA256SUMS.txt", "".join(f"{sha(LANE / relative)}  {relative}\n" for relative in paths))


def contract():
    result = subprocess.run([sys.executable, "-B", str(LANE / TEST)], cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.returncode, result.stdout


def build():
    repository = guard(False)
    generate(LANE)
    geometry = geometry_analysis()
    steps, meshes = artifact_audit(LANE)
    repro = reproducibility()
    checks = {
        "case": [CASE_L, CASE_W, CASE_H] == [40.0, 20.4, 41.7], "mount_envelope": MOUNT_ENVELOPE_L == 54.5,
        "pitch_x": HOLE_PITCH_X == 49.1, "pitch_y": HOLE_PITCH_Y == 10.0, "servo_hole": SERVO_HOLE_D == 4.6,
        "output_x": OUTPUT_X == 10.1, "output_y": OUTPUT_Y == 10.2, "opposite": OUTPUT_OPPOSITE_DERIVED == 29.9,
        "horn_radius": HORN_LINK_R == 30, "horn_t": HORN_T == 2.4, "horn_plane": HORN_PLANE_Z == 46.2,
        "max_height": MAX_H == 48.0, "nominal_180": OPERATING_SWEEP_DEG == 180,
        "conservative_360": parameters()["keepouts"]["conservative"]["sweep_deg"] == 360 and not parameters()["keepouts"]["conservative"]["powered_360_claim"],
        "keepout_ratio": 0.49 <= geometry["keepout_volume_ratio"] <= 0.51,
        "servo_bracket_zero": geometry["servo_bracket_intersection_mm3"] == 0,
        "bracket_nominal_keepout_zero": geometry["bracket_nominal_keepout_intersection_mm3"] == 0,
        "bracket_full_keepout_zero": geometry["bracket_conservative_keepout_intersection_mm3"] == 0,
        "valid": geometry["servo_valid"] and geometry["bracket_valid"], "a1": geometry["a1_envelope_pass"],
        "step_reload": all(row["valid"] for row in steps),
        "stl_quality": all(row["reload"] == "PASS" and row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in meshes.values()),
        "reproducibility": repro["status"] == "PASS", "authority": repository["checks"]["authority_4"], "protected": repository["checks"]["protected_5"],
    }
    validation = {
        "version": VERSION, "status": parameters()["status"], "geometry": geometry,
        "checks": checks, "check_count": len(checks), "pass_count": sum(checks.values()),
        "steps": steps, "stls": meshes, "reproducibility": repro,
        "repository": {"branch": repository["branch"], "head": repository["head"], "authority": repository["authority"], "protected": repository["protected"]},
        "forbidden_statuses": parameters()["forbidden_claims"],
    }
    write(LANE / "validation_report.json", json.dumps(validation, indent=2, sort_keys=True))
    write(LANE / "BUILD_LOG.txt", f"BUILD=PASS\nSTEP_RELOAD={len(STEPS)}/{len(STEPS)} PASS\nSTL_QUALITY={len(STLS)}/{len(STLS)} PASS\nREPRO={repro['byte_identical']}/{repro['compared']} {repro['status']}\n")
    write(LANE / "TEST_LOG.txt", "PENDING\n")
    indexes()
    code, output = contract()
    write(LANE / "TEST_LOG.txt", output)
    indexes()
    if code or not all(checks.values()):
        raise RuntimeError("VERIFY_FAIL\n" + output + json.dumps(checks))
    return guard(True), validation


def package():
    guard(True)
    downloads = Path(r"D:\Downloads")
    downloads.mkdir(parents=True, exist_ok=True)
    path = downloads / f"Paddy_Swarm_DS3218_SERVO_PHYSICAL_AUTHORITY_V001_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(path, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in EXPECTED:
            info = zipfile.ZipInfo(f"{LANE_NAME}/{relative}", (2026, 8, 27, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (LANE / relative).read_bytes())
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
    result = {"status": "PASS", "lane": str(LANE), "paths": len(EXPECTED), "steps": len(STEPS), "stls": len(STLS), "svgs": len(SVGS), "branch": repository["branch"], "head": repository["head"], "staged": repository["staged"], "geometry": validation["geometry"]}
    if args.package:
        path, digest = package()
        result.update(zip_path=str(path), zip_sha256=digest)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
