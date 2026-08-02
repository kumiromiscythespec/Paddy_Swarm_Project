"""Temporary Phase 3S-A ring for circularity and short water tests."""

from __future__ import annotations

from math import cos, pi, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    phase3sa_external_band_reference_width,
    phase3sa_panel_capture_depth,
    phase3sa_temporary_ring_clearance,
)


STATUS = "PHASE3SA_TEMPORARY_CALIBRATION_RING_NOT_PRODUCTION_INTERFACE"
PRINT_ORIENTATION = "FLAT_ON_FULL_ANNULAR_BASE"
RING_OUTER_RADIUS_MM = 112.0
RING_INNER_RADIUS_MM = 76.0
RING_HEIGHT_MM = phase3sa_panel_capture_depth + 3.0
GROOVE_FLOOR_MM = 3.0
GROOVE_INNER_RADIUS_MM = 80.0
GROOVE_OUTER_RADIUS_MM = 106.0
SEAM_RELIEF_INNER_RADIUS_MM = RING_INNER_RADIUS_MM
SEAM_RELIEF_HALF_ANGLE_DEG = 25.0
REFERENCE_EXTERNAL_BAND = "PURCHASED_REUSABLE_BAND_NOT_PRINTED"


def _annular_sector_cut(
    inner_radius: float,
    outer_radius: float,
    center_angle_deg: float,
    half_angle_deg: float,
    height: float,
    z_offset: float,
) -> cq.Workplane:
    points: list[tuple[float, float]] = []
    samples = 24
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


def build_temporary_panel_capture_ring_phase3sa() -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(RING_OUTER_RADIUS_MM)
        .circle(RING_INNER_RADIUS_MM)
        .extrude(RING_HEIGHT_MM)
    )
    groove = (
        cq.Workplane("XY")
        .circle(GROOVE_OUTER_RADIUS_MM)
        .circle(GROOVE_INNER_RADIUS_MM)
        .extrude(phase3sa_panel_capture_depth + 1.0)
        .translate((0.0, 0.0, GROOVE_FLOOR_MM))
    )
    ring = ring.cut(groove)
    for angle in (60.0, 180.0, 300.0):
        ring = ring.cut(
            _annular_sector_cut(
                SEAM_RELIEF_INNER_RADIUS_MM,
                GROOVE_OUTER_RADIUS_MM,
                angle,
                SEAM_RELIEF_HALF_ANGLE_DEG,
                phase3sa_panel_capture_depth + 1.0,
                GROOVE_FLOOR_MM,
            )
        )
    return ring


def build_external_band_reference_phase3sa(
    z_center: float,
) -> cq.Workplane:
    """Purchased strap envelope; STEP reference only, never printable STL."""

    return (
        cq.Workplane("XY")
        .circle(RING_OUTER_RADIUS_MM + 0.6)
        .circle(RING_OUTER_RADIUS_MM + 0.1)
        .extrude(phase3sa_external_band_reference_width)
        .translate(
            (
                0.0,
                0.0,
                z_center - 0.5 * phase3sa_external_band_reference_width,
            )
        )
    )


def capture_ring_dimensions_phase3sa() -> dict[str, float]:
    return {
        "outer_diameter_mm": 2.0 * RING_OUTER_RADIUS_MM,
        "inner_diameter_mm": 2.0 * RING_INNER_RADIUS_MM,
        "height_mm": RING_HEIGHT_MM,
        "capture_depth_mm": phase3sa_panel_capture_depth,
        "groove_inner_radius_mm": GROOVE_INNER_RADIUS_MM,
        "groove_outer_radius_mm": GROOVE_OUTER_RADIUS_MM,
        "radial_clearance_mm": phase3sa_temporary_ring_clearance,
    }
