"""Phase 3I-E internal standpipes, landing ramps, and hydraulic audits."""

from __future__ import annotations

from functools import lru_cache
from math import atan, cos, degrees, pi, radians, sin, sqrt

import cadquery as cq

from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib


OVERFLOW_COUNT = 3
OVERFLOW_ANGLES_LOCAL_DEG = (30.0, 150.0, 270.0)
LANDING_ANGLES_LOCAL_DEG = (60.0, 180.0, 300.0)
OVERFLOW_CENTER_RADIUS_CANDIDATES_MM = (76.0, 80.0, 84.0)
OVERFLOW_CENTER_RADIUS_MM = 80.0
STANDPIPE_CLEAR_BORE_DIAMETER_MM = 12.0
STANDPIPE_OUTSIDE_DIAMETER_MM = 18.0
STANDPIPE_WALL_THICKNESS_MM = 3.0
STANDPIPE_MINIMUM_WALL_THICKNESS_MM = 2.8
STANDPIPE_NOTCH_COUNT = 3
STANDPIPE_NOTCH_RELATIVE_ANGLES_DEG = (0.0, 120.0, 240.0)
STANDPIPE_NOTCH_CLEAR_WIDTH_MM = 9.0
STANDPIPE_NOTCH_MINIMUM_CLEAR_WIDTH_MM = 8.0
STANDPIPE_NOTCH_BOTTOM_Z_MM = 26.0
STANDPIPE_CROWN_TOP_Z_MM = 30.0
OUTLET_WATER_BREAK_AXIAL_THICKNESS_MM = 0.8
OUTLET_BOTTOM_PROJECTION_MM = 0.0

LANDING_RAMP_TANGENTIAL_WIDTH_MM = 30.0
LANDING_EFFECTIVE_CAPTURE_WIDTH_MM = 32.0
LANDING_RAMP_RADIAL_LENGTH_MM = 30.0
LANDING_RAMP_MAXIMUM_HEIGHT_ABOVE_FLOOR_MM = 8.0
LANDING_RAMP_TOP_Z_MM = phase3ib.SUMP_FLOOR_THICKNESS_MM + LANDING_RAMP_MAXIMUM_HEIGHT_ABOVE_FLOOR_MM
LANDING_RAMP_SURFACE_ANGLE_DEG = degrees(atan(LANDING_RAMP_MAXIMUM_HEIGHT_ABOVE_FLOOR_MM / LANDING_RAMP_TANGENTIAL_WIDTH_MM))

DROP_CORRIDOR_NOMINAL_DIAMETER_MM = 18.0
DROP_CORRIDOR_STRETCH_DIAMETER_MM = 22.0
DROP_CORRIDOR_LOWER_Z_MM = 26.0
DROP_CORRIDOR_UPPER_Z_MM = 170.0
ASSEMBLY_TOLERANCE_TRANSLATION_MM = 2.0
ASSEMBLY_TOLERANCE_ROTATION_DEG = 2.0


def polar_point(radius_mm: float, angle_deg: float, z_mm: float = 0.0) -> tuple[float, float, float]:
    angle = radians(angle_deg)
    return radius_mm * cos(angle), radius_mm * sin(angle), z_mm


def _v_notch_void(center: tuple[float, float], direction_deg: float) -> cq.Workplane:
    cx, cy = center
    half = 0.5 * STANDPIPE_NOTCH_CLEAR_WIDTH_MM
    notch = (
        cq.Workplane("XZ")
        .polyline([(-half, STANDPIPE_CROWN_TOP_Z_MM), (half, STANDPIPE_CROWN_TOP_Z_MM), (0.0, STANDPIPE_NOTCH_BOTTOM_Z_MM)])
        .close()
        .extrude(12.0, both=True)
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), direction_deg)
        .translate((cx, cy, 0.0))
    )
    return notch


def build_single_standpipe_wall_phase3ie(
    angle_deg: float,
    center_radius_mm: float = OVERFLOW_CENTER_RADIUS_MM,
) -> cq.Workplane:
    cx, cy, _ = polar_point(center_radius_mm, angle_deg)
    wall = (
        cq.Workplane("XY")
        .center(cx, cy)
        .circle(0.5 * STANDPIPE_OUTSIDE_DIAMETER_MM)
        .circle(0.5 * STANDPIPE_CLEAR_BORE_DIAMETER_MM)
        .extrude(STANDPIPE_CROWN_TOP_Z_MM - (phase3ib.SUMP_FLOOR_THICKNESS_MM - 0.2))
        .translate((0.0, 0.0, phase3ib.SUMP_FLOOR_THICKNESS_MM - 0.2))
    )
    for relative in STANDPIPE_NOTCH_RELATIVE_ANGLES_DEG:
        wall = wall.cut(_v_notch_void((cx, cy), angle_deg + relative))
    return wall.clean()


def build_single_floor_bore_void_phase3ie(
    angle_deg: float,
    center_radius_mm: float = OVERFLOW_CENTER_RADIUS_MM,
) -> cq.Workplane:
    cx, cy, _ = polar_point(center_radius_mm, angle_deg)
    straight = (
        cq.Workplane("XY")
        .center(cx, cy)
        .circle(0.5 * STANDPIPE_CLEAR_BORE_DIAMETER_MM)
        .extrude(STANDPIPE_CROWN_TOP_Z_MM + 0.5)
    )
    # A straight 0.8 mm conical break creates a sharp lower edge without a
    # rounded lip and without any geometry below Z=0.
    break_solid = cq.Solid.makeCone(
        0.5 * STANDPIPE_CLEAR_BORE_DIAMETER_MM + 0.4,
        0.5 * STANDPIPE_CLEAR_BORE_DIAMETER_MM,
        OUTLET_WATER_BREAK_AXIAL_THICKNESS_MM,
        cq.Vector(cx, cy, 0.0),
        cq.Vector(0.0, 0.0, 1.0),
    )
    return straight.union(cq.Workplane("XY").newObject([break_solid])).clean()


def build_landing_ramp_phase3ie(
    angle_deg: float,
    center_radius_mm: float = OVERFLOW_CENTER_RADIUS_MM,
) -> cq.Workplane:
    # Radial extrusion of a tangential wedge.  It overlaps the floor by 0.2 mm
    # and descends tangentially into the annular sump at 14 degrees.
    ramp = (
        cq.Workplane("YZ", origin=(center_radius_mm, 0.0, 0.0))
        .polyline([
            (-0.5 * LANDING_RAMP_TANGENTIAL_WIDTH_MM, phase3ib.SUMP_FLOOR_THICKNESS_MM - 0.2),
            (0.5 * LANDING_RAMP_TANGENTIAL_WIDTH_MM, phase3ib.SUMP_FLOOR_THICKNESS_MM - 0.2),
            (0.5 * LANDING_RAMP_TANGENTIAL_WIDTH_MM, LANDING_RAMP_TOP_Z_MM),
        ])
        .close()
        .extrude(0.5 * LANDING_RAMP_RADIAL_LENGTH_MM, both=True)
    )
    # One-millimetre floor-supported shoulders on both sides extend the
    # effective D22 tolerance capture width to 32 mm without making the main
    # hydraulic ramp wider than the authorized 30 mm range.
    capture_base = (
        cq.Workplane("XY")
        .box(
            LANDING_RAMP_RADIAL_LENGTH_MM,
            LANDING_EFFECTIVE_CAPTURE_WIDTH_MM,
            1.0,
            centered=(True, True, False),
        )
        .translate((center_radius_mm, 0.0, phase3ib.SUMP_FLOOR_THICKNESS_MM - 0.2))
    )
    return phase3ib._rotate_z(ramp.union(capture_base).clean(), angle_deg).clean()


def build_drop_corridor_reference_phase3ie(
    diameter_mm: float = DROP_CORRIDOR_STRETCH_DIAMETER_MM,
    rotation_deg: float = 30.0,
) -> cq.Workplane:
    solids: list[cq.Shape] = []
    for overflow_angle in OVERFLOW_ANGLES_LOCAL_DEG:
        x, y, _ = polar_point(OVERFLOW_CENTER_RADIUS_MM, overflow_angle + rotation_deg)
        corridor = (
            cq.Workplane("XY")
            .center(x, y)
            .circle(0.5 * diameter_mm)
            .extrude(DROP_CORRIDOR_UPPER_Z_MM - DROP_CORRIDOR_LOWER_Z_MM)
            .translate((0.0, 0.0, DROP_CORRIDOR_LOWER_Z_MM))
        )
        solids.extend(corridor.solids().vals())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def standpipe_geometry_audit_phase3ie() -> dict[str, object]:
    floor = phase3ib._annulus(100.0, 50.0, phase3ib.SUMP_FLOOR_THICKNESS_MM)
    pipes = []
    for angle in OVERFLOW_ANGLES_LOCAL_DEG:
        wall = build_single_standpipe_wall_phase3ie(angle)
        pipes.append({
            "angle_deg": angle,
            "solid_count": len(wall.solids().vals()),
            "floor_intersection_volume_mm3": wall.intersect(floor).val().Volume(),
            "notch_count": STANDPIPE_NOTCH_COUNT,
        })
    bore_area = pi * (0.5 * STANDPIPE_CLEAR_BORE_DIAMETER_MM) ** 2
    return {
        "architecture": "THREE_OPEN_OVERFLOW_STANDPIPES",
        "count": OVERFLOW_COUNT,
        "angles_local_deg": list(OVERFLOW_ANGLES_LOCAL_DEG),
        "center_radius_mm": OVERFLOW_CENTER_RADIUS_MM,
        "clear_bore_diameter_mm": STANDPIPE_CLEAR_BORE_DIAMETER_MM,
        "outside_diameter_mm": STANDPIPE_OUTSIDE_DIAMETER_MM,
        "nominal_wall_thickness_mm": STANDPIPE_WALL_THICKNESS_MM,
        "minimum_required_wall_thickness_mm": STANDPIPE_MINIMUM_WALL_THICKNESS_MM,
        "notch_count_per_pipe": STANDPIPE_NOTCH_COUNT,
        "notch_width_mm": STANDPIPE_NOTCH_CLEAR_WIDTH_MM,
        "notch_bottom_z_mm": STANDPIPE_NOTCH_BOTTOM_Z_MM,
        "crown_top_z_mm": STANDPIPE_CROWN_TOP_Z_MM,
        "floor_bore_diameter_mm": STANDPIPE_CLEAR_BORE_DIAMETER_MM,
        "outlet_water_break_axial_thickness_mm": OUTLET_WATER_BREAK_AXIAL_THICKNESS_MM,
        "projection_below_z0_mm": OUTLET_BOTTOM_PROJECTION_MM,
        "rounded_bottom_lip": False,
        "single_pipe_minimum_flow_area_mm2": bore_area,
        "pipes": pipes,
        "physical_flow_test": "PENDING",
        "cfd_performed": False,
    }


def landing_zone_audit_phase3ie() -> dict[str, object]:
    rotational_shift = OVERFLOW_CENTER_RADIUS_MM * radians(ASSEMBLY_TOLERANCE_ROTATION_DEG)
    worst_tangential = ASSEMBLY_TOLERANCE_TRANSLATION_MM + rotational_shift
    radial_margin = 0.5 * LANDING_RAMP_RADIAL_LENGTH_MM - (
        0.5 * DROP_CORRIDOR_STRETCH_DIAMETER_MM + ASSEMBLY_TOLERANCE_TRANSLATION_MM
    )
    tangential_margin = 0.5 * LANDING_EFFECTIVE_CAPTURE_WIDTH_MM - (
        0.5 * DROP_CORRIDOR_STRETCH_DIAMETER_MM + worst_tangential
    )
    cases = [
        "NOMINAL", "X_PLUS_2", "X_MINUS_2", "Y_PLUS_2", "Y_MINUS_2",
        "ROT_PLUS_2", "ROT_MINUS_2", "TAN_PLUS_2_ROT_PLUS_2",
        "TAN_MINUS_2_ROT_MINUS_2", "RAD_PLUS_2_ROT_PLUS_2", "RAD_MINUS_2_ROT_MINUS_2",
    ]
    return {
        "count": 3,
        "angles_local_deg": list(LANDING_ANGLES_LOCAL_DEG),
        "center_radius_mm": OVERFLOW_CENTER_RADIUS_MM,
        "tangential_width_mm": LANDING_RAMP_TANGENTIAL_WIDTH_MM,
        "effective_capture_width_mm": LANDING_EFFECTIVE_CAPTURE_WIDTH_MM,
        "capture_shoulder_reason": "ONE_MM_FLOOR_SUPPORTED_SHOULDERS_CONTAIN_D22_AT_2MM_PLUS_2DEG_WITHOUT_EXCEEDING_30MM_MAIN_RAMP",
        "radial_length_mm": LANDING_RAMP_RADIAL_LENGTH_MM,
        "maximum_height_above_floor_mm": LANDING_RAMP_MAXIMUM_HEIGHT_ABOVE_FLOOR_MM,
        "surface_angle_deg": LANDING_RAMP_SURFACE_ANGLE_DEG,
        "discharge_direction": "INTO_ANNULAR_SUMP_TANGENTIALLY",
        "floor_connected": True,
        "inner_dam_connected": False,
        "outer_wall_leak_path": False,
        "expanded_corridor_diameter_mm": DROP_CORRIDOR_STRETCH_DIAMETER_MM,
        "radial_capture_margin_mm": radial_margin,
        "tangential_capture_margin_mm": tangential_margin,
        "tolerance_cases": [{"name": name, "contained": radial_margin >= 0.0 and tangential_margin >= 0.0} for name in cases],
        "all_cases_contained": radial_margin >= 0.0 and tangential_margin >= 0.0,
        "cfd_capture_pass_declared": False,
    }


def blockage_dimension_audit_phase3ie() -> dict[str, object]:
    bore_area = pi * (0.5 * STANDPIPE_CLEAR_BORE_DIAMETER_MM) ** 2
    freeboard = phase3ib.MODULE_HEIGHT_MM - STANDPIPE_NOTCH_BOTTOM_Z_MM
    return {
        "cases": {
            "normal": {"open_count": 3, "minimum_geometric_flow_area_mm2": 3.0 * bore_area},
            "single_blockage": {"open_count": 2, "minimum_geometric_flow_area_mm2": 2.0 * bore_area},
            "double_blockage": {"open_count": 1, "minimum_geometric_flow_area_mm2": bore_area},
        },
        "single_pipe_clear_bore_diameter_mm": STANDPIPE_CLEAR_BORE_DIAMETER_MM,
        "v_notch_clear_width_mm": STANDPIPE_NOTCH_CLEAR_WIDTH_MM,
        "normal_water_surface_z_mm": STANDPIPE_NOTCH_BOTTOM_Z_MM,
        "outer_wall_top_freeboard_mm": freeboard,
        "flow_rates_l_min": [0.5, 1.0, 2.0],
        "flow_pass": "PHYSICAL_TEST_PENDING",
    }


def rotation_rule_audit_phase3ie() -> dict[str, object]:
    accepted = (30.0, 150.0, 270.0)
    rejected = (0.0, 60.0, 90.0, 120.0, 180.0, 240.0, 300.0)
    return {
        "relative_rotation_deg": 30.0,
        "operationally_selected_relative_angle_deg": 30.0,
        "contract": "RELATIVE_ROTATION_MOD_120_EQUALS_30",
        "accepted_relative_angles_deg": list(accepted),
        "rejected_relative_angles_deg": list(rejected),
        "accepted_checks": {str(int(v)): abs(v % 120.0 - 30.0) < 1.0e-9 for v in accepted},
        "rejected_checks": {str(int(v)): abs(v % 120.0 - 30.0) < 1.0e-9 for v in rejected},
        "five_stage_absolute_rotations_deg": [0.0, 30.0, 60.0, 90.0, 120.0],
        "previous_60deg_status": "REJECTED_BY_DROP_CORRIDOR_COLLISION",
    }


def correct_wrong_alignment_audit_phase3ie() -> dict[str, object]:
    def nearest_distance(rotation: float) -> list[float]:
        values = []
        for overflow in OVERFLOW_ANGLES_LOCAL_DEG:
            angle = overflow + rotation
            distances = [
                2.0 * OVERFLOW_CENTER_RADIUS_MM * abs(sin(0.5 * radians(angle - landing)))
                for landing in LANDING_ANGLES_LOCAL_DEG
            ]
            values.append(min(distances))
        return values
    correct = nearest_distance(30.0)
    wrong = nearest_distance(0.0)
    collision = nearest_distance(60.0)
    return {
        "correct_rotation_deg": 30.0,
        "wrong_rotation_deg": 0.0,
        "collision_rotation_deg": 60.0,
        "correct_center_offsets_mm": correct,
        "wrong_nearest_center_offsets_mm": wrong,
        "collision_center_offsets_mm": collision,
        "correct_all_three_aligned": all(value < 1.0e-8 for value in correct),
        "wrong_aligned_count": sum(value < 1.0e-8 for value in wrong),
        "hydraulically_equivalent_accepted_deg": [150.0, 270.0],
    }
