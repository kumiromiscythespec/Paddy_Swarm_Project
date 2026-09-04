#!/usr/bin/env python3
"""Deterministic CAD builder for the Common Rover front interface V001.

This lane is a non-manufacturing authority candidate.  It records the user
physical drive-axis datum supplied on 2026-08-30 and intentionally keeps the
future 500 mm frame, PTO pulley centre interface, fasteners, and physical
alignment behind explicit HOLD gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Callable

import cadquery as cq


REPO = Path(__file__).resolve().parents[4]
LANE = Path(__file__).resolve().parent
LANE_REL = Path("cad/common_rover/frame/front_interface_dual_pto_20t_v001")
ART = LANE / "artifacts"
TESTS = LANE / "tests"
DOWNLOADS = Path(r"D:\Downloads")
BRANCH = "agent/organize-untracked-cad-assets-20260725"
HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
VERSION = "FRONT_INTERFACE_DUAL_PTO_20T_V001"
STATUS = "CAD_PASS/CONTRACT_TEST_PASS/FRONT_INTERFACE_AUTHORITY_CANDIDATE_READY/PHYSICAL_VALIDATION_PENDING"

DRIVE_Z = 122.5
DRIVE_Z_LEFT = 122.0
DRIVE_Z_RIGHT = 123.0
DRIVE_Z_AS_BUILT_RANGE = [122.0, 123.0]
DRIVE_Z_LATERAL_DEVIATION = 1.0
DRIVE_Z_NOMINAL_DEVIATION = 0.5
DRIVE_FORE_AFT_TILT = 1.0

BEAM_LENGTH = 400.0
BEAM_X = 40.0
BEAM_Z = 20.0
BEAM_TOP_Z = 99.0
BEAM_CENTER_Z = BEAM_TOP_Z - BEAM_Z / 2.0
PLATE_THICKNESS = 5.0
PLATE_X = 95.0
PLATE_Y = 70.0
PLATE_INNER_Y = 40.0
PLATE_OUTER_Y = 110.0
KP_WIDTH_X = 67.0
KP_DEPTH_Y = 17.0
KP_HEIGHT_Z = 35.0
KP_AXIS_HEIGHT = 18.5
KP_AXIS_TOL = 0.5
KP_BORE = 10.0
KP_COLLAR_PROTRUSION = 6.0
KP_HOLE_CENTER = 53.0
KP_HOLE_DIAMETER_REFERENCE = 8.0
KP_INNER_Y = 50.0
KP_OUTER_Y = 100.0
KP_PAIR_SPACING = KP_OUTER_Y - KP_INNER_Y

PTO_SHAFT_DIAMETER = 10.0
PTO_SHAFT_CENTER_GAP = 60.0
PTO_SHAFT_END_ABS_Y = 160.0
PULLEY_TEETH = 20
PULLEY_PITCH = 5.0
PULLEY_OD_REFERENCE = 35.0
PULLEY_WIDTH_REFERENCE = 20.0
PULLEY_CENTER_Y = 130.0
PULLEY_OVERHANG = PULLEY_CENTER_Y - KP_OUTER_Y
PULLEY_HOUSING_GAP = (PULLEY_CENTER_Y - PULLEY_WIDTH_REFERENCE / 2.0) - (KP_OUTER_Y + KP_DEPTH_Y / 2.0)
PULLEY_KEEPOUT_RADIUS = PULLEY_OD_REFERENCE / 2.0 + 5.0
PULLEY_KEEPOUT_WIDTH = PULLEY_WIDTH_REFERENCE + 10.0

BELT_WIDTH = 15.0
BELT_CORRIDOR_WIDTH = 25.0
BELT_CORRIDOR_Z = 45.0
BELT_CORRIDOR_X0 = 22.5
BELT_CORRIDOR_X1 = 102.5
UNIT_INPUT_X = 120.0
UNIT_INPUT_RADIUS = 30.0
UNIT_INPUT_WIDTH = 30.0
UNIT_ADJUSTMENT_RANGE = [10.0, 20.0]

UNIT_MOUNT_Y = 75.0
UNIT_MOUNT_LOWER_Z = 55.0
UNIT_MOUNT_UPPER_Z = 185.0
UNIT_MOUNT_X = 60.0
UNIT_MOUNT_HOLE_REFERENCE = 9.0
MAIN_RAIL_LENGTH = 500.0
MAIN_RAIL_CENTER_X = -150.0
MAIN_RAIL_CENTER_Y = 80.5
MAIN_RAIL_LOWER_Z = 40.0
MAIN_RAIL_UPPER_Z = 185.0

CRAWLER_CENTER_Y = 145.0
CRAWLER_INNER_Y = 118.0
CRAWLER_OUTER_Y = 172.0
CRAWLER_X0 = -300.0
CRAWLER_X1 = -40.0
CRAWLER_Z0 = 0.0
CRAWLER_Z1 = 160.0

SOURCE_HASHES = {
    "cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2/dimensions.json": "77ae432278d07302883f78ad71f3152d28895c672bb0282a486c78ffc8db1f16",
    "cad/common_rover/common_rover_physical_fit_closure_v0_9_4_2/measurement_ledger.json": "655a94e023a608c6b68564f0b355230a11e015c7cdadb5cdb95b84ac99a66b0b",
    "cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1/cad/drive_htd5m_20t_reference.step": "95684926935f9f49ae02cd02b88fd71bc4cac318cfe0f16c48099d735b2c46c1",
    "cad/common_rover/pto_servo_sliding_idler_clutch_v001/design_parameters.json": "88b5eb4d1c2cfbd543792ff738d728b3011d9349d0d7f2e4da99da70cab87265",
    "cad/common_rover/drivetrain/crawler_candidate_c_12t_misumi_groove1_keeperless_v003/cad/candidate_C_12T_misumi_groove1_keeperless.step": "86532a8b70387f67e26de929dd061d85bd5efc4a21699251971b16a5f62952fd",
    "cad/common_rover/drivetrain/crawler_idler_candidate_c_v001/cad/candidate_C_crawler_idler.step": "111522ec40ba7fd8b2c6c88b8a86833445314d305c6fcccf0331bea7c1bd0418",
    "cad/common_rover/common_rover_crawler_link_anti_derail_guard_v0_9_6_17/artifacts/crawler_link_reinforced_anti_derail_guard_v0_9_6_17.stl": "3bf2f55347d045faf62d5f269d80ad59917c29c4029399a381397b4fe1d1d16c",
    "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/common_rover_front_drive_dual_pto_design_authority_v008.md": "0ebb03a8c45665aebb7f9e1bfa73048edb1fa8e540ebe039a5f204ca3fe0001b",
}

GENERATED = [
    "README.md",
    "DESIGN_AUTHORITY.md",
    "STRUCTURAL_SIMPLIFICATION_REPORT.md",
    "PHYSICAL_TEST_PLAN.md",
    "HOLD_REGISTER.md",
    "design_parameters.json",
    "validation_report.json",
    "source_authority_audit.json",
    "collision_report.json",
    "named_datums.json",
    "artifacts/front_interface_dual_pto_20t.step",
    "artifacts/front_interface_dual_pto_20t_reference.stl",
    "artifacts/front_interface_assembly_reference.step",
    "artifacts/left_pto_reference.step",
    "artifacts/right_pto_reference.step",
    "artifacts/unit_mount_interface_reference.step",
    "artifacts/pulley_keepout_reference.step",
    "artifacts/belt_keepout_reference.step",
    "artifacts/unit_input_pulley_envelope.step",
    "artifacts/500mm_frame_reference.step",
    "artifacts/front_interface_section_reference.step",
    "artifacts/crawler_clearance_reference.step",
    "artifacts/service_access_reference.step",
    "artifacts/front_interface_overview.svg",
    "artifacts/front_interface_section.svg",
    "COMMIT_PATHS.txt",
    "MANIFEST.txt",
    "SHA256SUMS.txt",
]
SOURCE_FILES = [
    "build_front_interface_dual_pto_20t_v001.py",
    "tests/test_front_interface_dual_pto_20t_v001_contract.py",
]
ALL_PATHS = sorted(SOURCE_FILES + GENERATED)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    cp = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=True)
    return cp.stdout.strip()


def repository_guard() -> dict:
    root = Path(git("rev-parse", "--show-toplevel")).resolve()
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    if root != REPO.resolve():
        raise RuntimeError(f"repository root mismatch: {root}")
    if branch != BRANCH:
        raise RuntimeError(f"branch mismatch: {branch}")
    if head != HEAD:
        raise RuntimeError(f"HEAD mismatch: {head}")
    staged = [p for p in git("diff", "--cached", "--name-only").splitlines() if p]
    if staged:
        raise RuntimeError(f"staged paths prohibited: {staged}")
    for rel, expected in SOURCE_HASHES.items():
        path = REPO / rel
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"protected source mismatch: {rel}")
    return {"repository": str(root), "branch": branch, "head": head, "staged_count": len(staged)}


def box_at(x: float, y: float, z: float, center: tuple[float, float, float]) -> cq.Shape:
    cx, cy, cz = center
    return cq.Solid.makeBox(x, y, z, cq.Vector(cx - x / 2, cy - y / 2, cz - z / 2))


def cyl_y(radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    cx, cy, cz = center
    return cq.Solid.makeCylinder(radius, length, cq.Vector(cx, cy - length / 2, cz), cq.Vector(0, 1, 0))


def cyl_z(radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    cx, cy, cz = center
    return cq.Solid.makeCylinder(radius, length, cq.Vector(cx, cy, cz - length / 2), cq.Vector(0, 0, 1))


def cyl_x(radius: float, length: float, center: tuple[float, float, float]) -> cq.Shape:
    cx, cy, cz = center
    return cq.Solid.makeCylinder(radius, length, cq.Vector(cx - length / 2, cy, cz), cq.Vector(1, 0, 0))


def compound(shapes: list[cq.Shape]) -> cq.Shape:
    return cq.Compound.makeCompound([s for s in shapes if s is not None])


def beam() -> cq.Shape:
    return box_at(BEAM_X, BEAM_LENGTH, BEAM_Z, (0, 0, BEAM_CENTER_Z))


def support_plate(side: int) -> cq.Shape:
    cy = side * (PLATE_INNER_Y + PLATE_OUTER_Y) / 2.0
    plate = box_at(PLATE_X, PLATE_Y, PLATE_THICKNESS, (0, cy, BEAM_TOP_Z + PLATE_THICKNESS / 2))
    for bearing_y in (side * KP_INNER_Y, side * KP_OUTER_Y):
        for x in (-KP_HOLE_CENTER / 2.0, KP_HOLE_CENTER / 2.0):
            plate = plate.cut(cyl_z(KP_HOLE_DIAMETER_REFERENCE / 2.0, PLATE_THICKNESS + 2.0, (x, bearing_y, BEAM_TOP_Z + PLATE_THICKNESS / 2)))
    return plate.clean()


def kp000(center_y: float) -> cq.Shape:
    base_z = BEAM_TOP_Z + PLATE_THICKNESS
    body = box_at(KP_WIDTH_X, KP_DEPTH_Y, KP_HEIGHT_Z, (0, center_y, base_z + KP_HEIGHT_Z / 2.0))
    return body.cut(cyl_y(KP_BORE / 2.0, KP_DEPTH_Y + 2.0, (0, center_y, DRIVE_Z))).clean()


def pto_shaft(side: int) -> cq.Shape:
    center_y = side * ((PTO_SHAFT_CENTER_GAP / 2.0 + PTO_SHAFT_END_ABS_Y) / 2.0)
    length = PTO_SHAFT_END_ABS_Y - PTO_SHAFT_CENTER_GAP / 2.0
    return cyl_y(PTO_SHAFT_DIAMETER / 2.0, length, (0, center_y, DRIVE_Z))


def pulley_reference(side: int) -> cq.Shape:
    # Conservative current PTO envelope.  The exact legacy STEP has a 6.1 mm
    # bore, so it is not silently promoted to the current 10 mm PTO interface.
    center = (0, side * PULLEY_CENTER_Y, DRIVE_Z)
    return cyl_y(PULLEY_OD_REFERENCE / 2.0, PULLEY_WIDTH_REFERENCE, center).cut(
        cyl_y((PTO_SHAFT_DIAMETER + 0.4) / 2.0, PULLEY_WIDTH_REFERENCE + 2.0, center)
    ).clean()


def pulley_keepout(side: int) -> cq.Shape:
    return cyl_y(PULLEY_KEEPOUT_RADIUS, PULLEY_KEEPOUT_WIDTH, (0, side * PULLEY_CENTER_Y, DRIVE_Z))


def belt_keepout(side: int) -> cq.Shape:
    return box_at(
        BELT_CORRIDOR_X1 - BELT_CORRIDOR_X0,
        BELT_CORRIDOR_WIDTH,
        BELT_CORRIDOR_Z,
        ((BELT_CORRIDOR_X0 + BELT_CORRIDOR_X1) / 2.0, side * PULLEY_CENTER_Y, DRIVE_Z),
    )


def input_pulley_envelope(side: int) -> cq.Shape:
    return cyl_y(UNIT_INPUT_RADIUS, UNIT_INPUT_WIDTH, (UNIT_INPUT_X, side * PULLEY_CENTER_Y, DRIVE_Z))


def pto_assembly(side: int) -> cq.Shape:
    return compound([
        support_plate(side),
        kp000(side * KP_INNER_Y),
        kp000(side * KP_OUTER_Y),
        pto_shaft(side),
        pulley_reference(side),
    ])


def unit_mount() -> cq.Shape:
    parts = [
        box_at(20, 220, 40, (50, 0, UNIT_MOUNT_LOWER_Z)),
        box_at(20, 220, 40, (50, 0, UNIT_MOUNT_UPPER_Z)),
        box_at(20, 20, UNIT_MOUNT_UPPER_Z - UNIT_MOUNT_LOWER_Z, (50, 100, (UNIT_MOUNT_UPPER_Z + UNIT_MOUNT_LOWER_Z) / 2)),
        box_at(20, 20, UNIT_MOUNT_UPPER_Z - UNIT_MOUNT_LOWER_Z, (50, -100, (UNIT_MOUNT_UPPER_Z + UNIT_MOUNT_LOWER_Z) / 2)),
        box_at(60, 20, 20, (20, 100, 85)),
        box_at(60, 20, 20, (20, -100, 85)),
    ]
    for z in (UNIT_MOUNT_LOWER_Z, UNIT_MOUNT_UPPER_Z):
        for y in (-UNIT_MOUNT_Y, UNIT_MOUNT_Y):
            parts.append(cyl_x(UNIT_MOUNT_HOLE_REFERENCE / 2.0, 24.0, (60, y, z)))
    return compound(parts)


def service_access() -> cq.Shape:
    parts: list[cq.Shape] = []
    for side in (-1, 1):
        for y in (side * KP_INNER_Y, side * KP_OUTER_Y):
            for x in (-KP_HOLE_CENTER / 2.0, KP_HOLE_CENTER / 2.0):
                parts.append(cyl_z(7.0, 45.0, (x, y, 161.5)))
        parts.append(cyl_z(6.0, 35.0, (0, side * PULLEY_CENTER_Y, 162.5)))
    return compound(parts)


def frame_500_reference() -> cq.Shape:
    parts: list[cq.Shape] = []
    for y in (-MAIN_RAIL_CENTER_Y, MAIN_RAIL_CENTER_Y):
        parts.append(box_at(MAIN_RAIL_LENGTH, 20, 40, (MAIN_RAIL_CENTER_X, y, MAIN_RAIL_LOWER_Z)))
        parts.append(box_at(MAIN_RAIL_LENGTH, 20, 40, (MAIN_RAIL_CENTER_X, y, MAIN_RAIL_UPPER_Z)))
    return compound(parts)


def crawler_envelope(side: int) -> cq.Shape:
    return box_at(
        CRAWLER_X1 - CRAWLER_X0,
        CRAWLER_OUTER_Y - CRAWLER_INNER_Y,
        CRAWLER_Z1 - CRAWLER_Z0,
        ((CRAWLER_X0 + CRAWLER_X1) / 2.0, side * CRAWLER_CENTER_Y, (CRAWLER_Z0 + CRAWLER_Z1) / 2.0),
    )


def interface_structure() -> cq.Shape:
    return compound([beam(), support_plate(-1), support_plate(1), unit_mount()])


def assembly() -> cq.Shape:
    return compound([
        interface_structure(),
        pto_assembly(-1),
        pto_assembly(1),
        pulley_keepout(-1), pulley_keepout(1),
        belt_keepout(-1), belt_keepout(1),
        input_pulley_envelope(-1), input_pulley_envelope(1),
        frame_500_reference(), crawler_envelope(-1), crawler_envelope(1),
    ])


def section_reference() -> cq.Shape:
    return compound([
        beam(), support_plate(1), kp000(KP_INNER_Y), kp000(KP_OUTER_Y),
        pulley_reference(1), pulley_keepout(1), belt_keepout(1), input_pulley_envelope(1),
    ])


def bbox_values(shape: cq.Shape) -> list[float]:
    b = shape.BoundingBox()
    return [round(v, 6) for v in (b.xlen, b.ylen, b.zlen, b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)]


def intersection_volume(a: cq.Shape, b: cq.Shape) -> float:
    try:
        return round(a.intersect(b).Volume(), 9)
    except Exception:
        return float("inf")


def bbox_clearance(a: cq.Shape, b: cq.Shape) -> float:
    aa, bb = a.BoundingBox(), b.BoundingBox()
    dx = max(0.0, aa.xmin - bb.xmax, bb.xmin - aa.xmax)
    dy = max(0.0, aa.ymin - bb.ymax, bb.ymin - aa.ymax)
    dz = max(0.0, aa.zmin - bb.zmax, bb.zmin - aa.zmax)
    return round(math.sqrt(dx * dx + dy * dy + dz * dz), 6)


def shape_clearance(a: cq.Shape, b: cq.Shape) -> float:
    return round(float(a.distance(b)), 6)


def collision_data() -> dict:
    groups: dict[str, cq.Shape] = {
        "PTO_BEAM": beam(),
        "KP000_ALL": compound([kp000(-KP_INNER_Y), kp000(-KP_OUTER_Y), kp000(KP_INNER_Y), kp000(KP_OUTER_Y)]),
        "UNIT_MOUNT": unit_mount(),
        "PTO_PULLEY_ALL": compound([pulley_reference(-1), pulley_reference(1)]),
        "PULLEY_KEEPOUT_ALL": compound([pulley_keepout(-1), pulley_keepout(1)]),
        "BELT_KEEPOUT_ALL": compound([belt_keepout(-1), belt_keepout(1)]),
        "CRAWLER_ALL": compound([crawler_envelope(-1), crawler_envelope(1)]),
    }
    checks = {}
    for name in ("PTO_BEAM", "KP000_ALL", "UNIT_MOUNT", "PTO_PULLEY_ALL"):
        checks[f"{name}_TO_CRAWLER"] = {
            "intersection_mm3": intersection_volume(groups[name], groups["CRAWLER_ALL"]),
            "bbox_clearance_mm": bbox_clearance(groups[name], groups["CRAWLER_ALL"]),
            "minimum_clearance_mm": shape_clearance(groups[name], groups["CRAWLER_ALL"]),
        }
    for name in ("PULLEY_KEEPOUT_ALL", "BELT_KEEPOUT_ALL"):
        checks[f"UNIT_MOUNT_TO_{name}"] = {
            "intersection_mm3": intersection_volume(groups["UNIT_MOUNT"], groups[name]),
            "bbox_clearance_mm": bbox_clearance(groups["UNIT_MOUNT"], groups[name]),
            "minimum_clearance_mm": shape_clearance(groups["UNIT_MOUNT"], groups[name]),
        }
    return {"method": "conservative_axis_aligned_crawler_and_service_envelopes", "checks": checks}


def source_audit() -> dict:
    rows = []
    for rel, expected in SOURCE_HASHES.items():
        actual = sha256(REPO / rel)
        rows.append({"path": rel, "expected_sha256": expected, "actual_sha256": actual, "pass": actual == expected})
    return {"all_pass": all(r["pass"] for r in rows), "rows": rows}


def parameters() -> dict:
    return {
        "version": VERSION,
        "classification": "FRONT_INTERFACE_AUTHORITY_CANDIDATE",
        "status": STATUS,
        "coordinates": {"x": "vehicle_forward", "y": "vehicle_left", "z": "up", "floor_datum_z_mm": 0.0,
                        "front_interface_origin_mm": [0.0, 0.0, DRIVE_Z]},
        "drive_axis": {
            "source": "USER_PHYSICAL_DATUM_UPDATE_2026-08-30",
            "left_measured_z_mm": DRIVE_Z_LEFT, "right_measured_z_mm": DRIVE_Z_RIGHT,
            "physical_nominal_z_mm": DRIVE_Z, "as_built_range_mm": DRIVE_Z_AS_BUILT_RANGE,
            "lateral_deviation_total_mm": DRIVE_Z_LATERAL_DEVIATION,
            "deviation_about_nominal_mm": KP_AXIS_TOL,
            "fore_aft_tilt_approx_mm": DRIVE_FORE_AFT_TILT,
            "historical_178_mm": "PROVISIONAL_OBSOLETE", "historical_175_mm": "CAD_ONLY_NOT_PHYSICAL_AUTHORITY",
        },
        "pto": {
            "quantity": 2, "left_right_independent": True, "continuous_cross_shaft": False,
            "axis_direction": "Y", "axis_z_mm": DRIVE_Z, "axis_z_difference_from_drive_mm": 0.0,
            "left_segment_y_mm": [PTO_SHAFT_CENTER_GAP / 2.0, PTO_SHAFT_END_ABS_Y],
            "right_segment_y_mm": [-PTO_SHAFT_END_ABS_Y, -PTO_SHAFT_CENTER_GAP / 2.0],
            "center_gap_mm": PTO_SHAFT_CENTER_GAP, "diameter_mm": PTO_SHAFT_DIAMETER,
            "load_role": "ROTATIONAL_TORQUE_ONLY",
        },
        "kp000": {
            "source": "common_rover_physical_fit_closure_v0_9_4_2 plus v0_9_4_0 measured envelope",
            "quantity_total": 4, "quantity_per_pto": 2, "housing_envelope_mm": [KP_WIDTH_X, KP_DEPTH_Y, KP_HEIGHT_Z],
            "axis_height_mm": KP_AXIS_HEIGHT, "axis_tolerance_mm": KP_AXIS_TOL, "bore_mm": KP_BORE,
            "one_side_collar_protrusion_mm": KP_COLLAR_PROTRUSION, "mount_hole_center_mm": KP_HOLE_CENTER,
            "mount_hole_diameter_mm": "8.0_REFERENCE_NOT_MANUFACTURING_AUTHORITY",
            "left_centers_y_mm": [KP_INNER_Y, KP_OUTER_Y], "right_centers_y_mm": [-KP_INNER_Y, -KP_OUTER_Y],
            "pair_spacing_mm": KP_PAIR_SPACING,
        },
        "pulley": {
            "status": "PTO_20T_GEOMETRY_AUTHORITY_PENDING", "belt_family": "HTD5M", "pitch_mm": PULLEY_PITCH,
            "teeth": PULLEY_TEETH, "conservative_reference_od_mm": PULLEY_OD_REFERENCE,
            "conservative_reference_width_mm": PULLEY_WIDTH_REFERENCE, "shaft_interface_mm": 10.0,
            "exact_legacy_external_step_sha256": SOURCE_HASHES["cad/common_rover/common_rover_drive_htd5m_tpu_trial_belt_v0_9_5_1/cad/drive_htd5m_20t_reference.step"],
            "legacy_step_bore_conflict": "6.1_MM_LEGACY_VS_10_MM_CURRENT_PTO",
            "left_center_y_mm": PULLEY_CENTER_Y, "right_center_y_mm": -PULLEY_CENTER_Y,
            "outer_bearing_plane_abs_y_mm": KP_OUTER_Y, "pulley_center_plane_abs_y_mm": PULLEY_CENTER_Y,
            "axial_overhang_from_outer_bearing_plane_mm": PULLEY_OVERHANG,
            "housing_to_pulley_actual_gap_mm": PULLEY_HOUSING_GAP,
            "spacer_thickness": "SPACER_THICKNESS_PHYSICAL_PENDING",
            "old_60t_architecture": "ABSENT",
        },
        "keepouts": {
            "pulley_rotation_radius_mm": PULLEY_KEEPOUT_RADIUS, "pulley_axial_width_mm": PULLEY_KEEPOUT_WIDTH,
            "belt_corridor_x_mm": [BELT_CORRIDOR_X0, BELT_CORRIDOR_X1], "belt_corridor_width_y_mm": BELT_CORRIDOR_WIDTH,
            "belt_corridor_height_z_mm": BELT_CORRIDOR_Z, "nominal_belt_width_mm": BELT_WIDTH,
            "unit_input_center_x_mm": UNIT_INPUT_X, "unit_input_radius_mm": UNIT_INPUT_RADIUS,
            "unit_input_width_mm": UNIT_INPUT_WIDTH, "local_adjustment_range_mm": UNIT_ADJUSTMENT_RANGE,
        },
        "beam": {
            "profile": "2040", "length_mm": BEAM_LENGTH, "section_xz_mm": [BEAM_X, BEAM_Z],
            "source_status": "DECLARED_PHYSICAL_STOCK_2040_X_400_V0_8", "top_z_mm": BEAM_TOP_Z,
            "support_plate": "A5052_95X70X5_REFERENCE_NOT_FOR_MANUFACTURING",
        },
        "unit_mount": {
            "point_count": 4, "point_centers_yz_mm": [[-UNIT_MOUNT_Y, UNIT_MOUNT_LOWER_Z], [UNIT_MOUNT_Y, UNIT_MOUNT_LOWER_Z], [-UNIT_MOUNT_Y, UNIT_MOUNT_UPPER_Z], [UNIT_MOUNT_Y, UNIT_MOUNT_UPPER_Z]],
            "lower_role": "PRIMARY_LOAD_SUPPORT", "upper_role": "ATTITUDE_ROTATION_RESTRAINT",
            "load_role": "WEIGHT_WORK_REACTION_IMPACT_ATTITUDE_CONTROL", "unit_position": "FIXED",
            "fastener": "UNIT_MOUNT_FASTENER_PHYSICAL_SELECTION_PENDING", "hole_reference_mm": UNIT_MOUNT_HOLE_REFERENCE,
            "shear_panel_attachment_provision": True, "bbox_as_structural_brace": False,
        },
        "frame_500_reference": {
            "status": "REFERENCE_FRAME_ENVELOPE_DESIGN_CANDIDATE_NOT_PHYSICAL_AUTHORITY",
            "upper_2040_count": 2, "lower_2040_count": 2, "length_each_mm": MAIN_RAIL_LENGTH,
            "center_y_abs_mm": MAIN_RAIL_CENTER_Y, "diagonal_braces": 0,
        },
        "crawler": {
            "driven": "Candidate C 12T MISUMI Groove-1 keeperless V003", "idler": "Candidate C V001",
            "link": "reinforced anti-derail guard v0.9.6.17", "reference_envelope_xyz_mm": [CRAWLER_X1 - CRAWLER_X0, CRAWLER_OUTER_Y - CRAWLER_INNER_Y, CRAWLER_Z1 - CRAWLER_Z0],
            "placement_status": "CONSERVATIVE_FRONT_INTERFACE_REFERENCE_PHYSICAL_REGISTRATION_PENDING",
        },
        "gates": {
            "physical_validation": "PENDING", "frame_500mm": "PHYSICAL_VALIDATION_PENDING",
            "pto_alignment": "PHYSICAL_VALIDATION_PENDING", "unit_mount_load": "VALIDATION_PENDING",
            "frame_structural": "NOT_CLAIMED", "pto_field": "NOT_APPROVED", "unit_field": "NOT_APPROVED",
        },
    }


def named_datums() -> dict:
    return {
        "FRONT_INTERFACE_ORIGIN": [0.0, 0.0, DRIVE_Z],
        "PTO_LEFT_AXIS": {"point": [0.0, KP_INNER_Y, DRIVE_Z], "direction": [0, 1, 0], "segment_y": [30.0, 160.0]},
        "PTO_RIGHT_AXIS": {"point": [0.0, -KP_INNER_Y, DRIVE_Z], "direction": [0, -1, 0], "segment_y": [-160.0, -30.0]},
        "UNIT_MOUNT_LOWER_LEFT": [UNIT_MOUNT_X, UNIT_MOUNT_Y, UNIT_MOUNT_LOWER_Z],
        "UNIT_MOUNT_LOWER_RIGHT": [UNIT_MOUNT_X, -UNIT_MOUNT_Y, UNIT_MOUNT_LOWER_Z],
        "UNIT_MOUNT_UPPER_LEFT": [UNIT_MOUNT_X, UNIT_MOUNT_Y, UNIT_MOUNT_UPPER_Z],
        "UNIT_MOUNT_UPPER_RIGHT": [UNIT_MOUNT_X, -UNIT_MOUNT_Y, UNIT_MOUNT_UPPER_Z],
    }


def contract_checks() -> dict[str, object]:
    p = parameters()
    c = collision_data()["checks"]
    checks: dict[str, object] = {
        "drive_axis_physical_source": p["drive_axis"]["source"] == "USER_PHYSICAL_DATUM_UPDATE_2026-08-30",
        "left_drive_measurement": DRIVE_Z_LEFT == 122.0,
        "right_drive_measurement": DRIVE_Z_RIGHT == 123.0,
        "drive_nominal": DRIVE_Z == 122.5,
        "pto_axis_equals_drive_axis": p["pto"]["axis_z_difference_from_drive_mm"] == 0.0,
        "historical_178_obsolete": p["drive_axis"]["historical_178_mm"] == "PROVISIONAL_OBSOLETE",
        "historical_175_cad_only": p["drive_axis"]["historical_175_mm"] == "CAD_ONLY_NOT_PHYSICAL_AUTHORITY",
        "two_pto": p["pto"]["quantity"] == 2,
        "independent_pto": p["pto"]["left_right_independent"] and not p["pto"]["continuous_cross_shaft"],
        "center_gap_positive": p["pto"]["center_gap_mm"] > 0,
        "kp000_four": p["kp000"]["quantity_total"] == 4,
        "kp000_two_each": p["kp000"]["quantity_per_pto"] == 2,
        "kp000_envelope": p["kp000"]["housing_envelope_mm"] == [67.0, 17.0, 35.0],
        "kp000_hole_center": p["kp000"]["mount_hole_center_mm"] == 53.0,
        "kp000_pair_spacing": p["kp000"]["pair_spacing_mm"] == 50.0,
        "pto_20t": p["pulley"]["teeth"] == 20,
        "htd5m": p["pulley"]["pitch_mm"] == 5.0 and p["pulley"]["belt_family"] == "HTD5M",
        "20t_authority_pending_honest": p["pulley"]["status"] == "PTO_20T_GEOMETRY_AUTHORITY_PENDING",
        "legacy_bore_conflict_recorded": "6.1" in p["pulley"]["legacy_step_bore_conflict"],
        "old_60t_absent": p["pulley"]["old_60t_architecture"] == "ABSENT",
        "pulley_overhang": p["pulley"]["axial_overhang_from_outer_bearing_plane_mm"] == 30.0,
        "pulley_housing_gap": p["pulley"]["housing_to_pulley_actual_gap_mm"] >= 5.0,
        "torque_only": p["pto"]["load_role"] == "ROTATIONAL_TORQUE_ONLY",
        "unit_mount_four": p["unit_mount"]["point_count"] == 4,
        "unit_mount_separate_load": "WEIGHT" in p["unit_mount"]["load_role"],
        "fixed_unit": p["unit_mount"]["unit_position"] == "FIXED",
        "local_adjustment": p["keepouts"]["local_adjustment_range_mm"] == [10.0, 20.0],
        "pulley_keepout": p["keepouts"]["pulley_rotation_radius_mm"] == 22.5,
        "belt_keepout": p["keepouts"]["belt_corridor_width_y_mm"] == 25.0,
        "unit_input_envelope": p["keepouts"]["unit_input_radius_mm"] == 30.0,
        "beam_400_stock": p["beam"]["length_mm"] == 400.0,
        "frame_500_candidate_only": "DESIGN_CANDIDATE" in p["frame_500_reference"]["status"],
        "no_diagonal": p["frame_500_reference"]["diagonal_braces"] == 0,
        "shear_provision": p["unit_mount"]["shear_panel_attachment_provision"],
        "bbox_not_brace": not p["unit_mount"]["bbox_as_structural_brace"],
        "beam_crawler_zero": c["PTO_BEAM_TO_CRAWLER"]["intersection_mm3"] == 0.0,
        "kp000_crawler_zero": c["KP000_ALL_TO_CRAWLER"]["intersection_mm3"] == 0.0,
        "unit_mount_crawler_zero": c["UNIT_MOUNT_TO_CRAWLER"]["intersection_mm3"] == 0.0,
        "pulley_crawler_zero": c["PTO_PULLEY_ALL_TO_CRAWLER"]["intersection_mm3"] == 0.0,
        "mount_pulley_keepout_zero": c["UNIT_MOUNT_TO_PULLEY_KEEPOUT_ALL"]["intersection_mm3"] == 0.0,
        "mount_belt_keepout_zero": c["UNIT_MOUNT_TO_BELT_KEEPOUT_ALL"]["intersection_mm3"] == 0.0,
        "service_access_exists": len(service_access().Solids()) == 10,
        "source_hashes": source_audit()["all_pass"],
    }
    return checks


def validation() -> dict:
    checks = contract_checks()
    return {
        "version": VERSION,
        "status": STATUS if all(bool(v) for v in checks.values()) else "FAIL_CLOSED",
        "check_count": len(checks), "pass_count": sum(bool(v) for v in checks.values()),
        "fail_count": sum(not bool(v) for v in checks.values()), "checks": checks,
        "geometry_bounds": {
            "interface": bbox_values(interface_structure()), "assembly": bbox_values(assembly()),
            "left_pto": bbox_values(pto_assembly(1)), "right_pto": bbox_values(pto_assembly(-1)),
        },
        "holds": [
            "PTO_20T_GEOMETRY_AUTHORITY_PENDING", "SPACER_THICKNESS_PHYSICAL_PENDING",
            "KP000_OPPOSITE_PROTRUSION_PHYSICAL_PENDING", "UNIT_MOUNT_FASTENER_PHYSICAL_SELECTION_PENDING",
            "CRAWLER_FRONT_INTERFACE_REGISTRATION_PHYSICAL_PENDING", "FRAME_500MM_PHYSICAL_VALIDATION_PENDING",
            "PTO_ALIGNMENT_PHYSICAL_VALIDATION_PENDING", "UNIT_MOUNT_LOAD_VALIDATION_PENDING",
        ],
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def export_step(shape: cq.Shape, name: str) -> None:
    path = ART / name
    cq.exporters.export(shape, str(path), exportType="STEP")
    # OCCT writes the wall-clock time into FILE_NAME.  The geometric DATA
    # section is deterministic, so normalize only that non-semantic header.
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'", "'2026-08-30T00:00:00'", text, count=1)
    path.write_text(text, encoding="utf-8", newline="\n")


def export_stl(shape: cq.Shape, name: str) -> None:
    cq.exporters.export(shape, str(ART / name), exportType="STL", tolerance=0.05, angularTolerance=0.1)


def svg_page(title: str, content: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720">
<rect width="1200" height="720" fill="#f8fafc"/><text x="55" y="62" font-family="sans-serif" font-size="30" font-weight="700" fill="#0f172a">{title}</text>
<style>.b{{fill:#64748b;stroke:#334155;stroke-width:2}}.k{{fill:#10b981;stroke:#047857;stroke-width:2}}.p{{fill:#f59e0b;stroke:#b45309;stroke-width:2}}.r{{fill:none;stroke:#ef4444;stroke-width:3;stroke-dasharray:10 8}}.m{{fill:#2563eb;stroke:#1e40af;stroke-width:2}}.t{{font:20px sans-serif;fill:#0f172a}}.s{{font:16px monospace;fill:#334155}}</style>
{content}</svg>
'''


def docs() -> dict[str, str]:
    header = "# Common Rover Front Interface Authority V001\n\nStatus: `" + STATUS + "`  \nClassification: `NOT_FOR_MANUFACTURING / PHYSICAL_VALIDATION_PENDING`\n\n"
    readme = header + f"""## Result

This isolated lane defines a reusable front interface with two mechanically independent PTO half-shafts, four KP000 references, a 400 mm 2040 transverse beam, explicit pulley/belt keep-outs, and a separate four-point unit-load portal. The user-supplied physical datum is `Z={DRIVE_Z:.1f} mm` from crawler-bottom/floor `Z0`; PTO and drive axes differ by exactly `0.0 mm` in CAD.

Torque path and structural load path remain separate:

- `PTO_LOAD_ROLE = ROTATIONAL_TORQUE_ONLY`
- `UNIT_MOUNT_LOAD_ROLE = WEIGHT + WORK_REACTION + IMPACT + ATTITUDE_CONTROL`

The available exact 20T STEP is retained only as a hashed external source because its 6.1 mm legacy bore conflicts with the current 10 mm PTO shaft. This lane therefore uses a conservative Ø35×20 mm reference envelope and retains `PTO_20T_GEOMETRY_AUTHORITY_PENDING`. No 60T PTO geometry is present.

The combined STL is a coloured-agnostic assembly/reference mesh only. It is **not** a printable monolithic bracket. Standard extrusion, A5052 candidate plates, KP000, shafts and pulleys remain separate physical parts.

## Candidate layout

| item | value |
|---|---:|
| PTO / DRIVE axis Z | {DRIVE_Z:.1f} mm |
| KP000 centers per side | 50 / 100 mm from center |
| KP000 pair spacing | {KP_PAIR_SPACING:.1f} mm |
| pulley center plane | ±{PULLEY_CENTER_Y:.1f} mm |
| bearing-plane to pulley-plane overhang | {PULLEY_OVERHANG:.1f} mm |
| housing-to-pulley actual gap | {PULLEY_HOUSING_GAP:.1f} mm |
| independent shaft center gap | {PTO_SHAFT_CENTER_GAP:.1f} mm |
| unit mount rectangle | {2*UNIT_MOUNT_Y:.0f}×{UNIT_MOUNT_UPPER_Z-UNIT_MOUNT_LOWER_Z:.0f} mm |

Local input-pulley adjustment is 10–20 mm candidate; the work unit itself stays fixed. No diagonal member is used. Straight orthogonal members and future shear-panel attachment provisions carry the architecture.
"""
    authority = header + f"""## Datum authority

`CRAWLER_BOTTOM/FLOOR = Z0`. User physical measurements: left drive center {DRIVE_Z_LEFT:.1f} mm, right {DRIVE_Z_RIGHT:.1f} mm; nominal authority {DRIVE_Z:.1f} mm; observed range 122–123 mm; ±0.5 mm about nominal; approximate fore/aft tilt 1.0 mm. Historical 178 mm is provisional/obsolete and 175 mm is CAD-only.

## Reused authorities

- KP000: 67×17×35 mm, axis height 18.5±0.5 mm, bore 10 mm, collar protrusion 6 mm; measured mounting-hole centers 53 mm.
- PTO architecture: two independent 10 mm outputs, double supported, HTD5M 20T/20T, 5 mm pitch.
- 20T outside reference: exact protected source hash, bounding reference Ø35×20 mm. Current 10 mm centre interface remains pending.
- 400 mm 2040: declared physical inventory from v0.8; no cutting is released.
- Crawler: Candidate C driven V003, Candidate C idler V001 and reinforced 54 mm link authority are protected source references.

## Formal separation

The PTO shafts are independent segments with a 60 mm centre gap. They are collinear by candidate symmetry but not physically connected. PTO shafts carry torque only. Four unit mount points on the independent rectangular portal carry unit weight, working reaction, impact and attitude restraint. BBOX/CBOX is not a structural brace.

Support plates and all holes are reference-only. No manufacturing hole, shaft cut, spacer, fastener or frame migration is released.
"""
    simplification = header + """## Removed or avoided

- diagonal braces: 0
- special angled joints: 0
- dedicated raised PTO support: removed
- 60T PTO support: removed
- PTO-as-unit-support: prohibited

## Common candidate components

- 2040×400 front beam: 1
- straight unit-mount crossrails: 2
- straight unit-mount uprights: 2
- straight orthogonal links: 2
- KP000: 4
- independent PTO shafts: 2
- 20T PTO reference envelopes: 2
- four-point unit interface: 1 standard

Relative to the older diagonal/raised-PTO concept, two diagonal members, their special joints, and the dedicated raised pulley support are eliminated. This is a component-count opportunity, not a structural-strength claim. A planar shear plate/deck may be added later at reserved orthogonal points after load definition.
"""
    physical = header + """## Physical sequence

1. Mock the 400 mm beam without cutting authority material.
2. Install four KP000 units on non-manufacturing reference plates.
3. Install independent left/right 10 mm PTO shafts and keep the 60 mm centre gap.
4. Measure both shaft axes from floor/crawler-bottom and compare to 122.5 mm.
5. Install verified 20T pulleys only after bore/interface selection.
6. Check actual pulley rotation and axial keep-outs.
7. Place a dummy unit-input pulley and test the belt corridor.
8. Install a mock four-point unit mount; support dummy mass only through the mount.
9. Verify KP000, pulley, unit bolt and tension-adjust tool access.
10. Register the physical crawler loop and repeat all clearance checks.
11. Hand rotate PTO; powered no-load later.
12. Add representative dummy unit mass and inspect frame racking.
13. Evaluate 500 mm frame migration only after the interface passes.

Stop on contact, shaft loading by the unit, bearing bind, insufficient tool access, or frame racking. Powered, load, water, mud and field gates remain closed.
"""
    hold = header + """- `PTO_20T_GEOMETRY_AUTHORITY_PENDING`: current Ø10 centre/bore and retention are not exact authority.
- `SPACER_THICKNESS_PHYSICAL_PENDING`: measure the outer KP000 rotating face and pulley datum.
- `KP000_OPPOSITE_PROTRUSION_PHYSICAL_PENDING`.
- `UNIT_MOUNT_FASTENER_PHYSICAL_SELECTION_PENDING`.
- `CRAWLER_FRONT_INTERFACE_REGISTRATION_PHYSICAL_PENDING`.
- `FRAME_500MM_PHYSICAL_VALIDATION_PENDING`.
- `PTO_ALIGNMENT_PHYSICAL_VALIDATION_PENDING`.
- `UNIT_MOUNT_LOAD_VALIDATION_PENDING`.
- `FRAME_STRUCTURAL_PASS`, `PTO_FIELD_PASS`, and `UNIT_FIELD_PASS` are not claimed.
"""
    return {
        "README.md": readme,
        "DESIGN_AUTHORITY.md": authority,
        "STRUCTURAL_SIMPLIFICATION_REPORT.md": simplification,
        "PHYSICAL_TEST_PLAN.md": physical,
        "HOLD_REGISTER.md": hold,
    }


def write_svgs() -> None:
    overview = svg_page("Front Interface V001 — top view", f'''<g transform="translate(100 105)">
<rect x="400" y="0" width="40" height="400" class="b"/><text x="450" y="25" class="s">2040 × 400 beam</text>
<rect x="365" y="40" width="110" height="70" class="m"/><rect x="365" y="290" width="110" height="70" class="m"/>
<circle cx="420" cy="60" r="16" class="k"/><circle cx="420" cy="110" r="16" class="k"/><circle cx="420" cy="290" r="16" class="k"/><circle cx="420" cy="340" r="16" class="k"/>
<circle cx="420" cy="30" r="23" class="p"/><circle cx="420" cy="370" r="23" class="p"/>
<rect x="443" y="17" width="180" height="26" class="r"/><rect x="443" y="357" width="180" height="26" class="r"/>
<rect x="480" y="120" width="145" height="160" fill="none" stroke="#2563eb" stroke-width="8"/>
<text x="660" y="32" class="t">forward belt corridor</text><text x="660" y="372" class="t">forward belt corridor</text>
<text x="650" y="160" class="t">4-point unit-load portal</text><text x="650" y="195" class="s">PTO shafts do not carry unit weight</text>
<text x="15" y="215" class="t">RIGHT PTO</text><text x="785" y="215" class="t">LEFT PTO</text>
</g>''')
    section = svg_page("Front Interface V001 — section / datum", f'''<g transform="translate(90 90)">
<line x1="0" y1="520" x2="1020" y2="520" stroke="#111827" stroke-width="4"/><text x="20" y="555" class="t">CRAWLER BOTTOM / FLOOR = Z0</text>
<rect x="170" y="328" width="400" height="40" class="b"/><text x="190" y="400" class="s">beam top Z99</text>
<rect x="210" y="318" width="320" height="10" class="m"/><rect x="260" y="248" width="95" height="70" class="k"/><rect x="420" y="248" width="95" height="70" class="k"/>
<line x1="110" y1="275" x2="940" y2="275" stroke="#ef4444" stroke-width="4"/><text x="630" y="260" class="t">PTO = DRIVE axis Z {DRIVE_Z:.1f} mm</text>
<circle cx="575" cy="275" r="50" class="p"/><circle cx="575" cy="275" r="64" class="r"/>
<rect x="639" y="225" width="220" height="100" class="r"/><circle cx="920" cy="275" r="80" class="r"/>
<text x="635" y="345" class="s">belt keep-out</text><text x="855" y="375" class="s">unit-input envelope</text>
<text x="110" y="65" class="t">Observed drive Z: left 122.0 / right 123.0</text><text x="110" y="100" class="s">178 obsolete · 175 CAD-only</text>
</g>''')
    write_text(ART / "front_interface_overview.svg", overview)
    write_text(ART / "front_interface_section.svg", section)


def build() -> None:
    repository_guard()
    ART.mkdir(parents=True, exist_ok=True)
    TESTS.mkdir(parents=True, exist_ok=True)
    export_step(interface_structure(), "front_interface_dual_pto_20t.step")
    export_stl(interface_structure(), "front_interface_dual_pto_20t_reference.stl")
    export_step(assembly(), "front_interface_assembly_reference.step")
    export_step(pto_assembly(1), "left_pto_reference.step")
    export_step(pto_assembly(-1), "right_pto_reference.step")
    export_step(unit_mount(), "unit_mount_interface_reference.step")
    export_step(compound([pulley_keepout(-1), pulley_keepout(1)]), "pulley_keepout_reference.step")
    export_step(compound([belt_keepout(-1), belt_keepout(1)]), "belt_keepout_reference.step")
    export_step(compound([input_pulley_envelope(-1), input_pulley_envelope(1)]), "unit_input_pulley_envelope.step")
    export_step(frame_500_reference(), "500mm_frame_reference.step")
    export_step(section_reference(), "front_interface_section_reference.step")
    export_step(compound([crawler_envelope(-1), crawler_envelope(1)]), "crawler_clearance_reference.step")
    export_step(service_access(), "service_access_reference.step")
    write_svgs()
    for rel, text in docs().items():
        write_text(LANE / rel, text)
    write_json(LANE / "design_parameters.json", parameters())
    write_json(LANE / "named_datums.json", named_datums())
    write_json(LANE / "source_authority_audit.json", source_audit())
    write_json(LANE / "collision_report.json", collision_data())
    write_json(LANE / "validation_report.json", validation())
    write_text(LANE / "COMMIT_PATHS.txt", "".join(f"{(LANE_REL / p).as_posix()}\n" for p in ALL_PATHS))
    write_manifest()


def write_manifest() -> None:
    manifest_excluded = {"MANIFEST.txt", "SHA256SUMS.txt"}
    rows = []
    for rel in ALL_PATHS:
        path = LANE / rel
        if rel in manifest_excluded or not path.is_file():
            continue
        rows.append(f"{rel}\t{path.stat().st_size}\t{sha256(path)}")
    write_text(LANE / "MANIFEST.txt", "path\tbytes\tsha256\n" + "\n".join(rows) + "\n")
    hash_rows = []
    for rel in ALL_PATHS:
        path = LANE / rel
        if rel == "SHA256SUMS.txt" or not path.is_file():
            continue
        hash_rows.append(f"{sha256(path)}  {rel}")
    write_text(LANE / "SHA256SUMS.txt", "\n".join(hash_rows) + "\n")


def verify_artifacts() -> dict:
    repository_guard()
    missing = [p for p in ALL_PATHS if not (LANE / p).is_file()]
    if missing:
        raise RuntimeError(f"missing lane paths: {missing}")
    actual = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    extra = sorted(set(actual) - set(ALL_PATHS))
    if extra:
        raise RuntimeError(f"unexpected lane paths: {extra}")
    step_rows = []
    for path in sorted(ART.glob("*.step")):
        shape = cq.importers.importStep(str(path)).val()
        step_rows.append({"file": path.name, "valid": shape.isValid(), "solids": len(shape.Solids()), "bounds": bbox_values(shape)})
    if not step_rows or not all(r["valid"] and r["solids"] > 0 for r in step_rows):
        raise RuntimeError("STEP reload failure")
    stl = inspect_binary_stl(ART / "front_interface_dual_pto_20t_reference.stl")
    checks = contract_checks()
    if not all(bool(v) for v in checks.values()):
        raise RuntimeError(f"contract failure: {[k for k,v in checks.items() if not v]}")
    return {"step": step_rows, "stl": stl, "contract": {"count": len(checks), "pass": sum(bool(v) for v in checks.values())}}


def inspect_binary_stl(path: Path) -> dict:
    """Pure-Python topology audit for deterministic OpenCascade binary STL."""
    data = path.read_bytes()
    if len(data) < 84:
        raise RuntimeError("STL too short")
    faces = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + faces * 50:
        raise RuntimeError("STL binary length/count mismatch")
    edge_counts: dict[tuple[tuple[float, float, float], tuple[float, float, float]], int] = {}
    directions: dict[tuple[tuple[float, float, float], tuple[float, float, float]], list[tuple[tuple[float, float, float], tuple[float, float, float]]]] = {}
    vertices: set[tuple[float, float, float]] = set()
    degenerate = 0
    for i in range(faces):
        vals = struct.unpack_from("<12fH", data, 84 + i * 50)
        tri = [tuple(round(float(v), 7) for v in vals[j:j + 3]) for j in (3, 6, 9)]
        vertices.update(tri)
        ax, ay, az = (tri[1][k] - tri[0][k] for k in range(3))
        bx, by, bz = (tri[2][k] - tri[0][k] for k in range(3))
        cx, cy, cz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
        if cx * cx + cy * cy + cz * cz <= 1e-20:
            degenerate += 1
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            key = tuple(sorted((a, b)))
            edge_counts[key] = edge_counts.get(key, 0) + 1
            directions.setdefault(key, []).append((a, b))
    bad_edges = sum(count != 2 for count in edge_counts.values())
    inconsistent = 0
    for key, oriented in directions.items():
        if len(oriented) == 2 and oriented[0] != (oriented[1][1], oriented[1][0]):
            inconsistent += 1
    return {
        "watertight": bad_edges == 0,
        "manifold": bad_edges == 0,
        "winding_consistent": inconsistent == 0,
        "bad_edges": bad_edges,
        "inconsistent_edges": inconsistent,
        "vertices": len(vertices),
        "faces": faces,
        "degenerate_triangles": degenerate,
    }


def make_zip() -> tuple[Path, str]:
    verify_artifacts()
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = DOWNLOADS / f"Paddy_Swarm_FRONT_INTERFACE_DUAL_PTO_20T_V001_{stamp}.zip"
    counter = 1
    while target.exists():
        target = DOWNLOADS / f"Paddy_Swarm_FRONT_INTERFACE_DUAL_PTO_20T_V001_{stamp}_{counter:02d}.zip"
        counter += 1
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in ALL_PATHS:
            path = LANE / rel
            info = zipfile.ZipInfo((Path(LANE.name) / rel).as_posix(), (2026, 8, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes())
    return target, sha256(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    if not (args.build or args.verify or args.zip):
        args.build = True
    if args.build:
        build()
    result = verify_artifacts() if (args.verify or args.zip) else None
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.zip:
        path, digest = make_zip()
        print(f"ZIP_PATH={path}")
        print(f"ZIP_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
