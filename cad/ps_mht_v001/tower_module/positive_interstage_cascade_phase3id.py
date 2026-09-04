"""Positive, open and brush-cleanable interstage cascade geometry for Phase 3I-D."""

from __future__ import annotations

from functools import lru_cache
from math import asin, degrees, radians, sin

import cadquery as cq

from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib


REAR_SERVICE_DIRECTION = "-X"

UPPER_DOWNCHUTE_CLEAR_WIDTH_MM = 30.0
UPPER_DOWNCHUTE_MINIMUM_CLEAR_WIDTH_MM = 28.0
UPPER_DOWNCHUTE_RADIAL_DEPTH_MM = 10.0
UPPER_DOWNCHUTE_SIDE_WALL_THICKNESS_MM = 3.2
UPPER_DOWNCHUTE_SIDE_WALL_HEIGHT_MM = 8.0
UPPER_DOWNCHUTE_INLET_CREST_Z_MM = 26.0
UPPER_DOWNCHUTE_OUTLET_TIP_Z_MM = 6.0
UPPER_DOWNCHUTE_INLET_RADIUS_MM = 96.0
DRIP_NOSE_TIP_RADIUS_MM = 106.0
DRIP_NOSE_MAXIMUM_TIP_RADIUS_MM = 106.5
DRIP_NOSE_TANGENTIAL_WIDTH_MM = 30.0
DRIP_NOSE_TERMINAL_EDGE_THICKNESS_MM = 1.6
DRIP_NOSE_UNDERSIDE_ANGLE_FROM_VERTICAL_DEG = degrees(
    asin((DRIP_NOSE_TIP_RADIUS_MM - UPPER_DOWNCHUTE_INLET_RADIUS_MM) / 20.0)
)

LOWER_RECEIVER_TANGENTIAL_MOUTH_WIDTH_MM = 46.0
LOWER_RECEIVER_MINIMUM_MOUTH_WIDTH_MM = 44.0
LOWER_RECEIVER_INNER_RADIUS_MM = 101.5
LOWER_RECEIVER_OUTER_RADIUS_MM = 118.0
LOWER_RECEIVER_MAXIMUM_OUTER_RADIUS_MM = 118.5
LOWER_RECEIVER_MOUTH_FLOOR_Z_MM = 165.6
LOWER_RECEIVER_TOP_Z_MM = 170.0
LOWER_RECEIVER_SIDE_WALL_TOTAL_HEIGHT_MM = 12.0
LOWER_RECEIVER_SIDE_WALL_THICKNESS_MM = 3.2
LOWER_RECEIVER_HALF_ANGLE_DEG = degrees(
    asin(0.5 * LOWER_RECEIVER_TANGENTIAL_MOUTH_WIDTH_MM / DRIP_NOSE_TIP_RADIUS_MM)
)

LOWER_CHANNEL_CLEAR_WIDTH_MM = 32.0
LOWER_CHANNEL_MINIMUM_CLEAR_WIDTH_MM = 30.0
LOWER_CHANNEL_RADIAL_DEPTH_MM = 13.0
LOWER_CHANNEL_WALL_THICKNESS_MM = 3.2
LOWER_CHANNEL_TOP_TRANSITION_Z_MM = 158.0
LOWER_CHANNEL_BOTTOM_DISCHARGE_Z_MM = 28.0
LOWER_CHANNEL_BRUSH_MINIMUM_WIDTH_MM = 12.0
BOTTOM_DISCHARGE_CLEAR_WIDTH_MM = 30.0
BOTTOM_DISCHARGE_RAMP_ANGLE_FROM_VERTICAL_DEG = 45.0

AIR_GAP_MM = 6.0
TANGENTIAL_TRANSLATION_TOLERANCE_MM = 2.0
RADIAL_TRANSLATION_TOLERANCE_MM = 2.0
ROTATIONAL_MISALIGNMENT_DEG = 2.0
ROTATIONAL_TANGENTIAL_SHIFT_MM = DRIP_NOSE_TIP_RADIUS_MM * radians(
    ROTATIONAL_MISALIGNMENT_DEG
)
COMBINED_TANGENTIAL_SHIFT_MM = (
    TANGENTIAL_TRANSLATION_TOLERANCE_MM + ROTATIONAL_TANGENTIAL_SHIFT_MM
)
NOMINAL_TANGENTIAL_MARGIN_PER_SIDE_MM = 0.5 * (
    LOWER_RECEIVER_TANGENTIAL_MOUTH_WIDTH_MM - DRIP_NOSE_TANGENTIAL_WIDTH_MM
)


def _xz_prism(
    points: list[tuple[float, float]],
    tangential_center_mm: float,
    tangential_thickness_mm: float,
) -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .polyline(points)
        .close()
        .extrude(0.5 * tangential_thickness_mm, both=True)
        .translate((0.0, tangential_center_mm, 0.0))
    )


def _receiver_radius_clip() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(LOWER_RECEIVER_OUTER_RADIUS_MM)
        .extrude(30.0)
        .translate((0.0, 0.0, 144.0))
    )


@lru_cache(maxsize=1)
def build_upper_downchute_floor_phase3id() -> cq.Workplane:
    # The water surface descends continuously from the Z26 crest.  The outer
    # terminal edge is only 1.6 mm high and ends at local Z6, breaking surface
    # tension without a downward-facing hook or unsupported shelf.
    return _xz_prism(
        [
            (-UPPER_DOWNCHUTE_INLET_RADIUS_MM, 22.8),
            (-UPPER_DOWNCHUTE_INLET_RADIUS_MM, UPPER_DOWNCHUTE_INLET_CREST_Z_MM),
            (-DRIP_NOSE_TIP_RADIUS_MM, UPPER_DOWNCHUTE_OUTLET_TIP_Z_MM + DRIP_NOSE_TERMINAL_EDGE_THICKNESS_MM),
            (-DRIP_NOSE_TIP_RADIUS_MM, UPPER_DOWNCHUTE_OUTLET_TIP_Z_MM),
        ],
        0.0,
        DRIP_NOSE_TANGENTIAL_WIDTH_MM,
    ).clean()


@lru_cache(maxsize=1)
def build_upper_downchute_phase3id() -> cq.Workplane:
    chute = build_upper_downchute_floor_phase3id()
    for sign in (-1.0, 1.0):
        wall = _xz_prism(
            [
                (-UPPER_DOWNCHUTE_INLET_RADIUS_MM, UPPER_DOWNCHUTE_INLET_CREST_Z_MM),
                (-UPPER_DOWNCHUTE_INLET_RADIUS_MM, UPPER_DOWNCHUTE_INLET_CREST_Z_MM + UPPER_DOWNCHUTE_SIDE_WALL_HEIGHT_MM),
                (-DRIP_NOSE_TIP_RADIUS_MM, UPPER_DOWNCHUTE_OUTLET_TIP_Z_MM + DRIP_NOSE_TERMINAL_EDGE_THICKNESS_MM + UPPER_DOWNCHUTE_SIDE_WALL_HEIGHT_MM),
                (-DRIP_NOSE_TIP_RADIUS_MM, UPPER_DOWNCHUTE_OUTLET_TIP_Z_MM + DRIP_NOSE_TERMINAL_EDGE_THICKNESS_MM),
            ],
            sign * 16.4,
            UPPER_DOWNCHUTE_SIDE_WALL_THICKNESS_MM,
        )
        chute = chute.union(wall, clean=True, glue=False)
    return chute.clean()


@lru_cache(maxsize=1)
def build_lower_vertical_channel_phase3id() -> cq.Workplane:
    # A shallow back plate replaces the removed rear wall only above the Z26
    # overflow crest.  Two outward rails leave the full route open to sight
    # and to a >=12 mm brush.
    back = (
        cq.Workplane("XY")
        .box(3.2, LOWER_CHANNEL_CLEAR_WIDTH_MM, 138.0, centered=(True, True, False))
        .translate((-99.8, 0.0, LOWER_CHANNEL_BOTTOM_DISCHARGE_Z_MM))
    )
    channel = back
    for sign in (-1.0, 1.0):
        rail = (
            cq.Workplane("XY")
            .box(15.4, LOWER_CHANNEL_WALL_THICKNESS_MM, 136.2, centered=(True, True, False))
            .translate((-106.3, sign * 17.6, LOWER_CHANNEL_BOTTOM_DISCHARGE_Z_MM))
        )
        channel = channel.union(rail, clean=True, glue=False)
    return channel.clean()


def _receiver_side_support(sign: float) -> cq.Workplane:
    bottom = cq.Workplane(
        "XY", origin=(-106.3, sign * 17.6, 145.6)
    ).rect(15.4, LOWER_RECEIVER_SIDE_WALL_THICKNESS_MM).val()
    top = cq.Workplane(
        "XY", origin=(-109.75, sign * 24.6, 164.2)
    ).rect(16.5, LOWER_RECEIVER_SIDE_WALL_THICKNESS_MM).val()
    return cq.Workplane("XY").newObject([cq.Solid.makeLoft([bottom, top], True)])


@lru_cache(maxsize=1)
def build_lower_receiver_phase3id() -> cq.Workplane:
    receiver = (
        cq.Workplane("XY")
        .box(3.2, 46.4, 12.0, centered=(True, True, False))
        .translate((-100.0, 0.0, LOWER_CHANNEL_TOP_TRANSITION_Z_MM))
    )
    # A <=8 mm inner landing catches nominal droplets without introducing a
    # 16.5 mm horizontal shelf.  The rest of the mouth remains vertically open.
    landing = (
        cq.Workplane("XY")
        .box(5.1, 46.4, 3.2, centered=(True, True, False))
        .translate((-103.75, 0.0, LOWER_RECEIVER_MOUTH_FLOOR_Z_MM - 3.2))
    )
    receiver = receiver.union(landing, clean=True, glue=False)
    for sign in (-1.0, 1.0):
        support = _receiver_side_support(sign)
        upper_wall = (
            cq.Workplane("XY")
            .box(16.5, LOWER_RECEIVER_SIDE_WALL_THICKNESS_MM, 6.2, centered=(True, True, False))
            .translate((-109.75, sign * 24.6, 163.8))
        )
        receiver = receiver.union(support, clean=True, glue=False)
        receiver = receiver.union(upper_wall, clean=True, glue=False)
    return receiver.intersect(_receiver_radius_clip()).clean()


@lru_cache(maxsize=1)
def build_bottom_discharge_phase3id() -> cq.Workplane:
    # The incoming stream is intercepted at the rear channel and carried 16 mm
    # inward on a 45-degree open ramp.  Its inner top edge is Z28, 2 mm above
    # the selected water surface, and points into the annular sump.
    ramp = _xz_prism(
        [(-106.0, 40.8), (-106.0, 44.0), (-90.0, 28.0), (-90.0, 24.8)],
        0.0,
        32.4,
    )
    discharge = ramp
    for sign in (-1.0, 1.0):
        wall = _xz_prism(
            [(-106.0, 44.0), (-106.0, 52.0), (-90.0, 36.0), (-90.0, 28.0)],
            # 0.1 mm volumetric overlap with the 32.4 mm ramp avoids a
            # face-only seam in the exported STL while retaining >32 mm clear.
            sign * 17.7,
            3.2,
        )
        discharge = discharge.union(wall, clean=True, glue=False)
    return discharge.clean()


@lru_cache(maxsize=1)
def build_lower_receiver_channel_discharge_phase3id() -> cq.Workplane:
    route = build_lower_vertical_channel_phase3id()
    route = route.union(build_lower_receiver_phase3id(), clean=True, glue=False)
    route = route.union(build_bottom_discharge_phase3id(), clean=True, glue=False)
    return route.clean()


@lru_cache(maxsize=1)
def build_positive_interstage_cascade_phase3id() -> cq.Workplane:
    route = build_upper_downchute_phase3id()
    route = route.union(build_lower_receiver_channel_discharge_phase3id(), clean=True, glue=False)
    return route.clean()


def build_receiver_capture_envelope_reference_phase3id(height_mm: float = AIR_GAP_MM) -> cq.Workplane:
    return phase3ib._sector(
        LOWER_RECEIVER_INNER_RADIUS_MM,
        LOWER_RECEIVER_OUTER_RADIUS_MM,
        180.0,
        2.0 * LOWER_RECEIVER_HALF_ANGLE_DEG,
        height_mm,
        LOWER_RECEIVER_TOP_Z_MM,
    )


def build_water_stream_envelope_reference_phase3id() -> cq.Workplane:
    radial_size = 2.0 * RADIAL_TRANSLATION_TOLERANCE_MM + DRIP_NOSE_TERMINAL_EDGE_THICKNESS_MM
    tangential_size = DRIP_NOSE_TANGENTIAL_WIDTH_MM + 2.0 * COMBINED_TANGENTIAL_SHIFT_MM
    return (
        cq.Workplane("XY")
        .box(radial_size, tangential_size, AIR_GAP_MM, centered=(True, True, False))
        .translate((-DRIP_NOSE_TIP_RADIUS_MM, 0.0, LOWER_RECEIVER_TOP_Z_MM))
    )


def interstage_path_dimension_audit_phase3id() -> dict[str, object]:
    upper = build_upper_downchute_phase3id()
    receiver = build_lower_receiver_phase3id()
    channel = build_lower_vertical_channel_phase3id()
    discharge = build_bottom_discharge_phase3id()
    return {
        "architecture": "RECESSED_OPEN_DOWNCHUTE_WITH_DRIP_NOSE_TO_POSITIVE_FLARED_RECEIVER_MOUTH",
        "central_hole_as_water_route": False,
        "upper_downchute": {
            "clear_width_mm": 29.6,
            "minimum_clear_width_mm": UPPER_DOWNCHUTE_MINIMUM_CLEAR_WIDTH_MM,
            "radial_depth_mm": UPPER_DOWNCHUTE_RADIAL_DEPTH_MM,
            "side_wall_thickness_mm": UPPER_DOWNCHUTE_SIDE_WALL_THICKNESS_MM,
            "side_wall_height_mm": UPPER_DOWNCHUTE_SIDE_WALL_HEIGHT_MM,
            "inlet_crest_z_mm": UPPER_DOWNCHUTE_INLET_CREST_Z_MM,
            "outlet_tip_z_mm": UPPER_DOWNCHUTE_OUTLET_TIP_Z_MM,
            "tip_centerline_radius_mm": DRIP_NOSE_TIP_RADIUS_MM,
            "terminal_edge_thickness_mm": DRIP_NOSE_TERMINAL_EDGE_THICKNESS_MM,
            "surface_tension_break": True,
            "open_for_brush_cleaning": True,
            "solid_count_before_body_fuse": len(upper.solids().vals()),
        },
        "lower_receiver": {
            "nominal_tangential_mouth_width_mm": LOWER_RECEIVER_TANGENTIAL_MOUTH_WIDTH_MM,
            "minimum_mouth_width_mm": LOWER_RECEIVER_MINIMUM_MOUTH_WIDTH_MM,
            "inner_radius_mm": LOWER_RECEIVER_INNER_RADIUS_MM,
            "outer_radius_mm": LOWER_RECEIVER_OUTER_RADIUS_MM,
            "top_z_mm": LOWER_RECEIVER_TOP_Z_MM,
            "mouth_floor_z_mm": LOWER_RECEIVER_MOUTH_FLOOR_Z_MM,
            "side_wall_total_height_mm": LOWER_RECEIVER_SIDE_WALL_TOTAL_HEIGHT_MM,
            "side_wall_thickness_mm": LOWER_RECEIVER_SIDE_WALL_THICKNESS_MM,
            "nominal_margin_per_side_mm": NOMINAL_TANGENTIAL_MARGIN_PER_SIDE_MM,
            "solid_count_before_channel_fuse": len(receiver.solids().vals()),
        },
        "lower_vertical_channel": {
            "clear_width_mm": LOWER_CHANNEL_CLEAR_WIDTH_MM,
            "minimum_clear_width_mm": LOWER_CHANNEL_MINIMUM_CLEAR_WIDTH_MM,
            "radial_depth_mm": LOWER_CHANNEL_RADIAL_DEPTH_MM,
            "wall_thickness_mm": LOWER_CHANNEL_WALL_THICKNESS_MM,
            "open_direction": "REAR_OUTWARD",
            "brush_minimum_width_mm": LOWER_CHANNEL_BRUSH_MINIMUM_WIDTH_MM,
            "top_transition_z_mm": LOWER_CHANNEL_TOP_TRANSITION_Z_MM,
            "solid_count_before_route_fuse": len(channel.solids().vals()),
        },
        "bottom_discharge": {
            "outlet_z_mm": LOWER_CHANNEL_BOTTOM_DISCHARGE_Z_MM,
            "clear_width_mm": BOTTOM_DISCHARGE_CLEAR_WIDTH_MM,
            "ramp_angle_from_vertical_deg": BOTTOM_DISCHARGE_RAMP_ANGLE_FROM_VERTICAL_DEG,
            "direction": "INTO_ANNULAR_SUMP",
            "central_hole_direction": False,
            "solid_count_before_route_fuse": len(discharge.solids().vals()),
        },
    }


def receiver_tolerance_audit_phase3id() -> dict[str, object]:
    cases = {
        "X_PLUS_2": {"radial_shift_mm": -2.0, "tangential_shift_mm": 0.0},
        "X_MINUS_2": {"radial_shift_mm": 2.0, "tangential_shift_mm": 0.0},
        "Y_PLUS_2": {"radial_shift_mm": 0.0, "tangential_shift_mm": 2.0},
        "Y_MINUS_2": {"radial_shift_mm": 0.0, "tangential_shift_mm": -2.0},
        "ROT_PLUS_2": {"radial_shift_mm": 0.0, "tangential_shift_mm": ROTATIONAL_TANGENTIAL_SHIFT_MM},
        "ROT_MINUS_2": {"radial_shift_mm": 0.0, "tangential_shift_mm": -ROTATIONAL_TANGENTIAL_SHIFT_MM},
        "Y_PLUS_2_ROT_PLUS_2": {"radial_shift_mm": 0.0, "tangential_shift_mm": COMBINED_TANGENTIAL_SHIFT_MM},
        "Y_MINUS_2_ROT_MINUS_2": {"radial_shift_mm": 0.0, "tangential_shift_mm": -COMBINED_TANGENTIAL_SHIFT_MM},
    }
    evaluated: dict[str, object] = {}
    stream_half_width = 0.5 * DRIP_NOSE_TANGENTIAL_WIDTH_MM
    stream_radial_half = 0.5 * DRIP_NOSE_TERMINAL_EDGE_THICKNESS_MM
    for name, offsets in cases.items():
        radial_center = DRIP_NOSE_TIP_RADIUS_MM + offsets["radial_shift_mm"]
        tangential_center = offsets["tangential_shift_mm"]
        radial_min = radial_center - stream_radial_half
        radial_max = radial_center + stream_radial_half
        tangent_abs_max = abs(tangential_center) + stream_half_width
        passed = (
            radial_min >= LOWER_RECEIVER_INNER_RADIUS_MM
            and radial_max <= LOWER_RECEIVER_OUTER_RADIUS_MM
            and tangent_abs_max <= 0.5 * LOWER_RECEIVER_TANGENTIAL_MOUTH_WIDTH_MM
        )
        evaluated[name] = {
            **offsets,
            "stream_radial_range_mm": [radial_min, radial_max],
            "stream_max_abs_tangential_mm": tangent_abs_max,
            "remaining_tangential_margin_mm": 0.5 * LOWER_RECEIVER_TANGENTIAL_MOUTH_WIDTH_MM - tangent_abs_max,
            "pass": passed,
        }
    return {
        "receiver_nominal_width_mm": LOWER_RECEIVER_TANGENTIAL_MOUTH_WIDTH_MM,
        "drip_nose_width_mm": DRIP_NOSE_TANGENTIAL_WIDTH_MM,
        "nominal_margin_per_side_mm": NOMINAL_TANGENTIAL_MARGIN_PER_SIDE_MM,
        "rotation_shift_at_106mm_mm": ROTATIONAL_TANGENTIAL_SHIFT_MM,
        "combined_worst_tangential_shift_mm": COMBINED_TANGENTIAL_SHIFT_MM,
        "cases": evaluated,
        "all_cases_pass": all(bool(item["pass"]) for item in evaluated.values()),
        "analysis_type": "SIMPLE_PLANAR_FALLING_STREAM_ENVELOPE_REFERENCE_NOT_CFD",
        "cfd_performed": False,
    }


def water_stream_envelope_audit_phase3id() -> dict[str, object]:
    stream = build_water_stream_envelope_reference_phase3id()
    capture = build_receiver_capture_envelope_reference_phase3id()
    stream_volume = stream.val().Volume()
    captured_volume = stream.intersect(capture).val().Volume()
    central_dry_void = cq.Workplane("XY").circle(50.0).extrude(AIR_GAP_MM).translate((0.0, 0.0, LOWER_RECEIVER_TOP_Z_MM))
    central_intersections = len(stream.intersect(central_dry_void).solids().vals())
    return {
        "stream_envelope_volume_mm3": stream_volume,
        "captured_intersection_volume_mm3": captured_volume,
        "uncaptured_volume_mm3": max(0.0, stream_volume - captured_volume),
        "receiver_planar_envelope_contains_stream": abs(stream_volume - captured_volume) <= 1.0e-5,
        "central_dry_opening_intersection_solid_count": central_intersections,
        "central_dry_opening_clear": central_intersections == 0,
        "nominal_air_gap_mm": AIR_GAP_MM,
        "reference_only": True,
        "cfd_performed": False,
    }
