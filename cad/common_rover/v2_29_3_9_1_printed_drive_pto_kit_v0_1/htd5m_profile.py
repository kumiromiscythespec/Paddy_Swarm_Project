from __future__ import annotations

import math
from typing import Iterable

from drive_pto_contract import PITCH_MM, pitch_diameter_mm
from geometry_common import cylinder_z, require_cadquery


PROFILE_NAME = "HTD-5M PRINTED TEST CANDIDATE"
ROOT_DEPTH_MM = 1.80
PULLEY_TOOTH_TIP_ABOVE_PITCH_MM = 0.72
PULLEY_TOOTH_ROOT_WIDTH_MM = 3.05
PULLEY_TOOTH_TIP_WIDTH_MM = 1.55
BELT_TOOTH_DEPTH_MM = 2.05
BELT_TOOTH_ROOT_WIDTH_MM = 3.15
BELT_TOOTH_TIP_WIDTH_MM = 1.60
RADIAL_OVERLAP_MM = 0.20


def pitch_radius_mm(teeth: int, pitch_mm: float = PITCH_MM) -> float:
    return pitch_diameter_mm(teeth, pitch_mm) / 2.0


def pulley_radii_mm(
    teeth: int,
    *,
    radial_compensation_mm: float = 0.0,
    tooth_depth_compensation_mm: float = 0.0,
) -> dict[str, float]:
    pitch_radius = pitch_radius_mm(teeth) + radial_compensation_mm
    root_radius = pitch_radius - ROOT_DEPTH_MM - tooth_depth_compensation_mm
    tip_radius = (
        pitch_radius
        + PULLEY_TOOTH_TIP_ABOVE_PITCH_MM
        + tooth_depth_compensation_mm
    )
    if root_radius <= 0.0 or tip_radius <= root_radius:
        raise ValueError("INVALID_PULLEY_RADII")
    return {
        "pitch_radius_mm": pitch_radius,
        "root_radius_mm": root_radius,
        "tip_radius_mm": tip_radius,
    }


def _polar(radius: float, angle: float) -> tuple[float, float]:
    return radius * math.cos(angle), radius * math.sin(angle)


def _tooth_polygon(
    *,
    root_radius: float,
    tip_radius: float,
    angle: float,
    root_width_mm: float,
    tip_width_mm: float,
) -> tuple[tuple[float, float], ...]:
    root_half_angle = root_width_mm / (2.0 * root_radius)
    tip_half_angle = tip_width_mm / (2.0 * tip_radius)
    return (
        _polar(root_radius - RADIAL_OVERLAP_MM, angle - root_half_angle),
        _polar(tip_radius, angle - tip_half_angle),
        _polar(tip_radius, angle + tip_half_angle),
        _polar(root_radius - RADIAL_OVERLAP_MM, angle + root_half_angle),
    )


def external_tooth_solids(
    teeth: int,
    height_mm: float,
    *,
    z_mm: float = 0.0,
    tooth_width_compensation_mm: float = 0.0,
    tooth_depth_compensation_mm: float = 0.0,
    radial_compensation_mm: float = 0.0,
) -> tuple[object, ...]:
    cq = require_cadquery()
    radii = pulley_radii_mm(
        teeth,
        radial_compensation_mm=radial_compensation_mm,
        tooth_depth_compensation_mm=tooth_depth_compensation_mm,
    )
    root_width = PULLEY_TOOTH_ROOT_WIDTH_MM + tooth_width_compensation_mm
    tip_width = PULLEY_TOOTH_TIP_WIDTH_MM + tooth_width_compensation_mm
    if tip_width <= 0.8 or root_width <= tip_width:
        raise ValueError("INVALID_PULLEY_TOOTH_WIDTH")
    solids = []
    for index in range(teeth):
        angle = 2.0 * math.pi * index / teeth
        polygon = _tooth_polygon(
            root_radius=radii["root_radius_mm"],
            tip_radius=radii["tip_radius_mm"],
            angle=angle,
            root_width_mm=root_width,
            tip_width_mm=tip_width,
        )
        solid = (
            cq.Workplane("XY")
            .polyline(polygon)
            .close()
            .extrude(height_mm)
            .translate((0.0, 0.0, z_mm))
            .val()
        )
        solids.append(solid)
    return tuple(solids)


def external_toothed_blank(
    teeth: int,
    height_mm: float,
    *,
    z_mm: float = 0.0,
    tooth_width_compensation_mm: float = 0.0,
    tooth_depth_compensation_mm: float = 0.0,
    radial_compensation_mm: float = 0.0,
):
    radii = pulley_radii_mm(
        teeth,
        radial_compensation_mm=radial_compensation_mm,
        tooth_depth_compensation_mm=tooth_depth_compensation_mm,
    )
    root = cylinder_z(
        radii["root_radius_mm"],
        height_mm,
        z=z_mm,
    )
    teeth_solids = external_tooth_solids(
        teeth,
        height_mm,
        z_mm=z_mm,
        tooth_width_compensation_mm=tooth_width_compensation_mm,
        tooth_depth_compensation_mm=tooth_depth_compensation_mm,
        radial_compensation_mm=radial_compensation_mm,
    )
    return root.fuse(*teeth_solids)


def belt_pitch_radius_mm(
    pitch_length_mm: float,
    *,
    pitch_compensation_mm: float = 0.0,
    shrinkage_compensation: float = 1.0,
) -> float:
    if shrinkage_compensation <= 0.0:
        raise ValueError("POSITIVE_SHRINKAGE_COMPENSATION_REQUIRED")
    compensated_length = (
        pitch_length_mm
        + (pitch_length_mm / PITCH_MM) * pitch_compensation_mm
    ) * shrinkage_compensation
    return compensated_length / (2.0 * math.pi)


def belt_tooth_solids(
    tooth_count: int,
    pitch_radius: float,
    belt_width_mm: float,
    *,
    tooth_depth_mm: float = BELT_TOOTH_DEPTH_MM,
    tooth_width_compensation_mm: float = 0.0,
) -> tuple[object, ...]:
    cq = require_cadquery()
    root_radius = pitch_radius + 0.45
    tip_radius = pitch_radius - tooth_depth_mm
    root_width = BELT_TOOTH_ROOT_WIDTH_MM + tooth_width_compensation_mm
    tip_width = BELT_TOOTH_TIP_WIDTH_MM + tooth_width_compensation_mm
    if tip_radius <= 0.0 or tip_width <= 0.8 or root_width <= tip_width:
        raise ValueError("INVALID_BELT_TOOTH_GEOMETRY")
    solids = []
    for index in range(tooth_count):
        angle = 2.0 * math.pi * index / tooth_count
        polygon = (
            _polar(root_radius + RADIAL_OVERLAP_MM, angle - root_width / (2.0 * root_radius)),
            _polar(tip_radius, angle - tip_width / (2.0 * tip_radius)),
            _polar(tip_radius, angle + tip_width / (2.0 * tip_radius)),
            _polar(root_radius + RADIAL_OVERLAP_MM, angle + root_width / (2.0 * root_radius)),
        )
        solids.append(
            (
                cq.Workplane("XY")
                .polyline(polygon)
                .close()
                .extrude(belt_width_mm)
                .val()
            )
        )
    return tuple(solids)


def minimum_feature_report() -> dict[str, float]:
    return {
        "pulley_tooth_tip_width_mm": PULLEY_TOOTH_TIP_WIDTH_MM,
        "pulley_tooth_root_width_mm": PULLEY_TOOTH_ROOT_WIDTH_MM,
        "belt_tooth_tip_width_mm": BELT_TOOTH_TIP_WIDTH_MM,
        "belt_tooth_root_width_mm": BELT_TOOTH_ROOT_WIDTH_MM,
        "radial_overlap_mm": RADIAL_OVERLAP_MM,
    }
