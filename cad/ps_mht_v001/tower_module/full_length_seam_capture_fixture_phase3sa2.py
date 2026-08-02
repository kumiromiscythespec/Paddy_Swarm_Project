"""Reusable local capture fixture for full-length seam specimens."""

from __future__ import annotations

from math import cos, pi, sin

import cadquery as cq

from ps_mht_v001.coupons.full_length_seam_pair_phase3sa2 import (
    SHARED_SEAM_ANGLE_DEG,
)
from ps_mht_v001.parameters import (
    phase3sa2_fixture_arc_half_angle_deg,
    phase3sa2_fixture_capture_depth,
    phase3sa2_fixture_height,
    phase3sa2_fixture_inner_radius,
    phase3sa2_fixture_outer_radius,
    phase3sa2_fixture_seam_relief_half_angle_deg,
)


STATUS = "PHASE3SA2_REUSABLE_LOCAL_CAPTURE_FIXTURE"
PRINT_ORIENTATION = "FLAT"
REFERENCE_EXTERNAL_BAND = "PURCHASED_REUSABLE_BAND_NOT_PRINTED"
GROOVE_FLOOR_MM = phase3sa2_fixture_height - phase3sa2_fixture_capture_depth
TOOLLESS_CLEARANCE_MM = 0.6
FIXTURES_PER_CANDIDATE = 2
FIXTURES_FOR_SIMULTANEOUS_C040_C060 = 4
INNER_STOP_OUTER_RADIUS_MM = 66.8
OUTER_STOP_INNER_RADIUS_MM = 105.8
LEFT_STOP_CENTER_ANGLE_DEG = 28.8
RIGHT_STOP_CENTER_ANGLE_DEG = 91.2
RADIAL_STOP_HALF_ANGLE_DEG = 0.5


def _annular_sector(
    inner_radius: float,
    outer_radius: float,
    center_angle_deg: float,
    half_angle_deg: float,
    height: float,
    z_offset: float = 0.0,
) -> cq.Workplane:
    points: list[tuple[float, float]] = []
    samples = 48
    for index in range(samples + 1):
        angle = (
            center_angle_deg
            - half_angle_deg
            + 2.0 * half_angle_deg * index / samples
        )
        value = pi * angle / 180.0
        points.append((outer_radius * cos(value), outer_radius * sin(value)))
    for index in range(samples + 1):
        angle = (
            center_angle_deg
            + half_angle_deg
            - 2.0 * half_angle_deg * index / samples
        )
        value = pi * angle / 180.0
        points.append((inner_radius * cos(value), inner_radius * sin(value)))
    return (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(height)
        .translate((0.0, 0.0, z_offset))
    )


def build_full_length_seam_capture_fixture_phase3sa2() -> cq.Workplane:
    """Build an open local cradle with no wall against the seam faces."""

    floor = _annular_sector(
        phase3sa2_fixture_inner_radius,
        phase3sa2_fixture_outer_radius,
        SHARED_SEAM_ANGLE_DEG,
        phase3sa2_fixture_arc_half_angle_deg,
        GROOVE_FLOOR_MM,
    )
    side_half_angle = 0.5 * (
        phase3sa2_fixture_arc_half_angle_deg
        - phase3sa2_fixture_seam_relief_half_angle_deg
    )
    side_offset = 0.5 * (
        phase3sa2_fixture_arc_half_angle_deg
        + phase3sa2_fixture_seam_relief_half_angle_deg
    )
    fixture = floor
    for sign in (-1.0, 1.0):
        center = SHARED_SEAM_ANGLE_DEG + sign * side_offset
        inner_stop = _annular_sector(
            phase3sa2_fixture_inner_radius,
            INNER_STOP_OUTER_RADIUS_MM,
            center,
            side_half_angle,
            phase3sa2_fixture_capture_depth,
            GROOVE_FLOOR_MM,
        )
        outer_stop = _annular_sector(
            OUTER_STOP_INNER_RADIUS_MM,
            phase3sa2_fixture_outer_radius,
            center,
            side_half_angle,
            phase3sa2_fixture_capture_depth,
            GROOVE_FLOOR_MM,
        )
        fixture = fixture.union(inner_stop).union(outer_stop)
    for center in (
        LEFT_STOP_CENTER_ANGLE_DEG,
        RIGHT_STOP_CENTER_ANGLE_DEG,
    ):
        fixture = fixture.union(
            _annular_sector(
                INNER_STOP_OUTER_RADIUS_MM,
                OUTER_STOP_INNER_RADIUS_MM,
                center,
                RADIAL_STOP_HALF_ANGLE_DEG,
                phase3sa2_fixture_capture_depth,
                GROOVE_FLOOR_MM,
            )
        )
    return fixture


def fixture_requirements_phase3sa2() -> dict[str, object]:
    return {
        "capture_depth_mm": phase3sa2_fixture_capture_depth,
        "height_mm": phase3sa2_fixture_height,
        "inner_radius_mm": phase3sa2_fixture_inner_radius,
        "outer_radius_mm": phase3sa2_fixture_outer_radius,
        "arc_half_angle_deg": phase3sa2_fixture_arc_half_angle_deg,
        "seam_relief_half_angle_deg":
            phase3sa2_fixture_seam_relief_half_angle_deg,
        "tool_less_clearance_mm": TOOLLESS_CLEARANCE_MM,
        "inner_stop_outer_radius_mm": INNER_STOP_OUTER_RADIUS_MM,
        "outer_stop_inner_radius_mm": OUTER_STOP_INNER_RADIUS_MM,
        "same_upper_and_lower_part": True,
        "fixture_contacts_seam_face": False,
        "small_snap": False,
        "reusable": True,
        "external_band": REFERENCE_EXTERNAL_BAND,
        "quantity_per_candidate": FIXTURES_PER_CANDIDATE,
        "quantity_simultaneous_c040_c060":
            FIXTURES_FOR_SIMULTANEOUS_C040_C060,
    }
