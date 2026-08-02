"""Phase 3S-A asymmetric vertical seam and permanent bed rails."""

from __future__ import annotations

from math import asin, cos, radians, sin, tan

import cadquery as cq

from ps_mht_v001.parameters import (
    phase3sa_panel_height,
    phase3sa_seam_clearance_candidates,
    phase3sa_seam_overlap,
    phase3sa_seam_rail_min_contact_area,
    phase3sa_seam_rail_width,
    phase3sa_seam_root_radius,
    phase3sa_seam_root_thickness,
    phase3sa_shell_outer_radius,
    phase3sa_water_return_height,
    phase3sa_water_return_thickness,
)


STATUS = "PHASE3SA_CALIBRATION_PENDING_TWO_STAGE_LABYRINTH"
SEAM_POLICY = "LEFT_OUTER_COVER_RIGHT_INNER_RECEIVER"
WATERTIGHTNESS = "NOT_GUARANTEED_RETURN_DRIPS_INWARD"
FORBIDDEN_FEATURES = (
    "UNDERCUT",
    "SNAP",
    "THIN_TONGUE",
    "CANTILEVER_GATE",
    "CARTRIDGE",
    "VERTICAL_GASKET",
)
LEAD_CHAMFER_MM = 1.0
RAIL_CHORD_PLANE_X = 40.0
RAIL_COUNT = 2


def validate_seam_clearance_phase3sa(clearance: float) -> float:
    value = float(clearance)
    if value not in phase3sa_seam_clearance_candidates:
        raise ValueError(
            "seam clearance must be an explicit Phase 3S-A candidate "
            f"{phase3sa_seam_clearance_candidates}, got {value}"
        )
    return value


def _seam_point(
    angle_deg: float,
    radial: float,
    tangent: float,
) -> tuple[float, float]:
    angle = radians(angle_deg)
    radial_x, radial_y = cos(angle), sin(angle)
    tangent_x, tangent_y = -sin(angle), cos(angle)
    return (
        radial * radial_x + tangent * tangent_x,
        radial * radial_y + tangent * tangent_y,
    )


def _seam_prism(
    angle_deg: float,
    radial_tangent_points: tuple[tuple[float, float], ...],
    height: float,
) -> cq.Workplane:
    points = [
        _seam_point(angle_deg, radial, tangent)
        for radial, tangent in radial_tangent_points
    ]
    return cq.Workplane("XY").polyline(points).close().extrude(height)


def _root_blend_cylinder(
    angle_deg: float,
    radial: float,
    tangent: float,
    height: float,
) -> cq.Workplane:
    x, y = _seam_point(angle_deg, radial, tangent)
    return (
        cq.Workplane("XY")
        .center(x, y)
        .circle(phase3sa_seam_root_radius)
        .extrude(height)
    )


def build_left_outer_cover_phase3sa(
    height: float,
    seam_clearance: float,
) -> cq.Workplane:
    """External cover at +60 degrees with a 1 mm lead chamfer."""

    clearance = validate_seam_clearance_phase3sa(seam_clearance)
    outer = phase3sa_shell_outer_radius + clearance + 4.0
    inner = phase3sa_shell_outer_radius + clearance
    root = _seam_prism(
        60.0,
        (
            (phase3sa_shell_outer_radius - 4.0, -5.0),
            (outer, -5.0),
            (outer, 0.0),
            (phase3sa_shell_outer_radius - 4.0, 0.0),
        ),
        height,
    )
    cover = _seam_prism(
        60.0,
        (
            (inner, -1.0),
            (outer, -1.0),
            (outer, phase3sa_seam_overlap - LEAD_CHAMFER_MM),
            (
                outer - LEAD_CHAMFER_MM,
                phase3sa_seam_overlap,
            ),
            (
                inner + LEAD_CHAMFER_MM,
                phase3sa_seam_overlap,
            ),
            (inner, phase3sa_seam_overlap - LEAD_CHAMFER_MM),
        ),
        height,
    )
    return root.union(cover).union(
        _root_blend_cylinder(
            60.0,
            phase3sa_shell_outer_radius - 3.0,
            -3.0,
            height,
        )
    )


def build_right_inner_water_return_phase3sa(
    height: float,
) -> cq.Workplane:
    """Open, brush-accessible inner return at the -60 degree receiver."""

    inner = (
        phase3sa_shell_outer_radius
        - 3.0
        - phase3sa_water_return_height
    )
    outer = phase3sa_shell_outer_radius - 3.0
    water_return = _seam_prism(
        -60.0,
        (
            (inner, 0.0),
            (outer, 0.0),
            (outer, phase3sa_seam_overlap),
            (
                outer - phase3sa_water_return_thickness,
                phase3sa_seam_overlap,
            ),
            (
                inner,
                phase3sa_seam_overlap
                - phase3sa_seam_root_thickness,
            ),
        ),
        height,
    )
    return water_return.union(
        _root_blend_cylinder(
            -60.0,
            phase3sa_shell_outer_radius - 6.0,
            3.0,
            height,
        )
    )


def _rail_polygon(y_sign: float) -> list[tuple[float, float]]:
    outer_radius = phase3sa_shell_outer_radius
    edge_angle = radians(60.0)
    edge_y = outer_radius * sin(edge_angle)
    chord_seam_y = RAIL_CHORD_PLANE_X * tan(edge_angle)
    inner_y = chord_seam_y - phase3sa_seam_rail_width
    inner_angle = asin(inner_y / outer_radius)
    points: list[tuple[float, float]] = [
        (RAIL_CHORD_PLANE_X, y_sign * inner_y),
        (RAIL_CHORD_PLANE_X, y_sign * chord_seam_y),
        (
            outer_radius * cos(edge_angle),
            y_sign * edge_y,
        ),
    ]
    sample_count = 12
    for index in range(1, sample_count + 1):
        angle = edge_angle - (
            edge_angle - inner_angle
        ) * index / sample_count
        points.append(
            (
                outer_radius * cos(angle),
                y_sign * outer_radius * sin(angle),
            )
        )
    return points


def build_contact_rails_phase3sa(
    height: float = phase3sa_panel_height,
) -> cq.Workplane:
    """Two continuous broad wedges sharing one flat chord-plane datum."""

    rails = [
        cq.Workplane("XY")
        .polyline(_rail_polygon(sign))
        .close()
        .extrude(height)
        for sign in (-1.0, 1.0)
    ]
    edge_angle = radians(60.0)
    chord_seam_y = RAIL_CHORD_PLANE_X * tan(edge_angle)
    inner_y = chord_seam_y - phase3sa_seam_rail_width
    inner_angle = asin(inner_y / phase3sa_shell_outer_radius)
    result = rails[0].union(rails[1])
    for sign in (-1.0, 1.0):
        result = result.union(
            cq.Workplane("XY")
            .center(
                97.0 * cos(inner_angle),
                sign * 97.0 * sin(inner_angle),
            )
            .circle(phase3sa_seam_root_radius)
            .extrude(height)
        )
    return result


def rail_contact_area_phase3sa(
    height: float = phase3sa_panel_height,
) -> float:
    area = RAIL_COUNT * phase3sa_seam_rail_width * height
    assert area >= phase3sa_seam_rail_min_contact_area
    return area


def seam_minimum_features_phase3sa() -> dict[str, float]:
    return {
        "overlap_mm": phase3sa_seam_overlap,
        "root_thickness_mm": phase3sa_seam_root_thickness,
        "root_radius_mm": phase3sa_seam_root_radius,
        "rail_width_mm": phase3sa_seam_rail_width,
        "water_return_height_mm": phase3sa_water_return_height,
        "water_return_thickness_mm": phase3sa_water_return_thickness,
        "lead_chamfer_mm": LEAD_CHAMFER_MM,
    }


def nominal_seam_angles_phase3sa() -> tuple[float, float, float]:
    return (60.0, 180.0, 300.0)


def seam_has_direct_radial_sightline_phase3sa() -> bool:
    """The outer cover and offset inner return form a two-stage labyrinth."""

    return False
