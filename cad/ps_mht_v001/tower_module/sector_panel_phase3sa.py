"""One replaceable 120-degree Phase 3S-A shell panel."""

from __future__ import annotations

from math import cos, pi, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    phase3sa_panel_capture_depth,
    phase3sa_panel_height,
    phase3sa_sector_angle_deg,
    phase3sa_shell_outer_radius,
    phase3sa_shell_wall,
    phase3sa_short_panel_height,
)
from ps_mht_v001.tower_module.sector_port_opening_phase3sa import (
    add_sector_port_opening_phase3sa,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    build_contact_rails_phase3sa,
    build_left_outer_cover_phase3sa,
    build_right_inner_water_return_phase3sa,
    validate_seam_clearance_phase3sa,
)


STATUS = "PHASE3SA_IDENTICAL_REPLACEABLE_120_DEGREE_PANEL"
PART_COUNT_PER_MODULE = 3
PORT_COUNT_PER_PANEL = 1
END_DATUM_POLICY = "IDENTICAL_TOP_AND_BOTTOM_CONTINUOUS_LANDS"
BLANK_REFERENCE_STATUS = "COUPON_ONLY_NOT_A_PRODUCTION_PANEL"
REFERENCE_DRAIN_ZONE = "REFERENCE_ONLY_NO_GEOMETRY"
IMPLEMENTED_SMALL_PART_COUNT = 0
IMPLEMENTED_HARDWARE: tuple[str, ...] = ()
IMPLEMENTED_DRAIN_OR_IRRIGATION_FEATURES: tuple[str, ...] = ()


def _annular_sector_phase3sa(
    inner_radius: float,
    outer_radius: float,
    height: float,
    z_offset: float = 0.0,
) -> cq.Workplane:
    half_angle = 0.5 * phase3sa_sector_angle_deg
    sample_count = 72
    points: list[tuple[float, float]] = []
    for index in range(sample_count + 1):
        angle = (-half_angle + phase3sa_sector_angle_deg * index / sample_count)
        radians_value = pi * angle / 180.0
        points.append(
            (
                outer_radius * cos(radians_value),
                outer_radius * sin(radians_value),
            )
        )
    for index in range(sample_count + 1):
        angle = (half_angle - phase3sa_sector_angle_deg * index / sample_count)
        radians_value = pi * angle / 180.0
        points.append(
            (
                inner_radius * cos(radians_value),
                inner_radius * sin(radians_value),
            )
        )
    return (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(height)
        .translate((0.0, 0.0, z_offset))
    )


def build_sector_shell_phase3sa(
    height: float,
) -> cq.Workplane:
    return _annular_sector_phase3sa(
        phase3sa_shell_outer_radius - phase3sa_shell_wall,
        phase3sa_shell_outer_radius,
        height,
    )


def build_panel_end_datums_phase3sa(
    height: float,
) -> cq.Workplane:
    datum_height = min(phase3sa_panel_capture_depth, 0.5 * height)
    bottom = _annular_sector_phase3sa(
        phase3sa_shell_outer_radius - 5.0,
        phase3sa_shell_outer_radius,
        datum_height,
    )
    top = _annular_sector_phase3sa(
        phase3sa_shell_outer_radius - 5.0,
        phase3sa_shell_outer_radius,
        datum_height,
        height - datum_height,
    )
    return bottom.union(top)


def build_blank_sector_panel_calibration_reference_phase3sa(
    seam_clearance: float,
    height: float = phase3sa_short_panel_height,
) -> cq.Workplane:
    """Coupon-only blank made from the same panel body and seam definitions."""

    clearance = validate_seam_clearance_phase3sa(seam_clearance)
    panel = build_sector_shell_phase3sa(height)
    panel = panel.union(build_contact_rails_phase3sa(height))
    panel = panel.union(
        build_left_outer_cover_phase3sa(height, clearance)
    )
    panel = panel.union(build_right_inner_water_return_phase3sa(height))
    panel = panel.union(build_panel_end_datums_phase3sa(height))
    return panel


def build_sector_panel_phase3sa(
    seam_clearance: float,
    height: float = phase3sa_panel_height,
) -> cq.Workplane:
    panel = build_blank_sector_panel_calibration_reference_phase3sa(
        seam_clearance,
        height,
    )
    return add_sector_port_opening_phase3sa(panel, height)


def sector_panel_nominal_dimensions_phase3sa() -> dict[str, float]:
    return {
        "outer_radius_mm": phase3sa_shell_outer_radius,
        "wall_mm": phase3sa_shell_wall,
        "height_mm": phase3sa_panel_height,
        "angle_deg": phase3sa_sector_angle_deg,
    }
