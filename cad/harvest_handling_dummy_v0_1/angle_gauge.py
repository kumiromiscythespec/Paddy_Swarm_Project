"""Flat 0/10/20/30-degree and eight-direction HHD setup gauge."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq

from .cq_utils import validate_print_bounds
from .interfaces import require_positive
from .parameters import ALLOWED_DIRECTIONS, ALLOWED_TILT_ANGLES, GAUGE


@dataclass(frozen=True)
class AngleGaugeParams:
    """Printable flat gauge dimensions in mm."""

    width: float = 120.0
    length: float = 82.0
    thickness: float = GAUGE.plate_thickness
    rib_length: float = 42.0
    rib_width: float = GAUGE.line_width
    rib_height: float = GAUGE.label_height
    compass_radius: float = 16.0


def validate_params(params: AngleGaugeParams) -> None:
    """Validate minimum printable gauge features."""

    require_positive(
        width=params.width,
        length=params.length,
        thickness=params.thickness,
        rib_length=params.rib_length,
        rib_width=params.rib_width,
        rib_height=params.rib_height,
        compass_radius=params.compass_radius,
    )
    if params.rib_width + 1.0e-9 < 3.0 * 0.4:
        raise ValueError("angle-gauge ribs must be at least three nozzle widths")


def _raised_bar(
    start: tuple[float, float],
    angle_deg: float,
    length: float,
    width: float,
    height: float,
    z: float,
) -> cq.Workplane:
    """Create a raised line joined to the plate."""

    return (
        cq.Workplane("XY")
        .box(length, width, height, centered=(False, True, False))
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
        .translate((start[0], start[1], z))
    )


def build(params: AngleGaugeParams = AngleGaugeParams()) -> cq.Workplane:
    """Build one support-free planar angle and direction gauge."""

    validate_params(params)
    part = cq.Workplane("XY").box(
        params.width,
        params.length,
        params.thickness,
        centered=(True, True, False),
    )
    angle_origin = (-50.0, -27.0)
    vertical_reference = 90.0
    for tilt in ALLOWED_TILT_ANGLES:
        part = part.union(
            _raised_bar(
                angle_origin,
                vertical_reference - tilt,
                params.rib_length,
                params.rib_width,
                params.rib_height,
                params.thickness,
            )
        )
        label_angle = math.radians(vertical_reference - tilt)
        label_center = (
            angle_origin[0] + (params.rib_length + 5.0) * math.cos(label_angle),
            angle_origin[1] + (params.rib_length + 5.0) * math.sin(label_angle),
        )
        label = (
            cq.Workplane("XY")
            .workplane(offset=params.thickness)
            .center(*label_center)
            .text(
                str(int(tilt)),
                4.5,
                GAUGE.label_height,
                combine=True,
                halign="center",
                valign="center",
            )
        )
        part = part.union(label)

    compass_center = (34.0, 0.0)
    ring = (
        cq.Workplane("XY")
        .workplane(offset=params.thickness)
        .center(*compass_center)
        .circle(params.compass_radius)
        .circle(params.compass_radius - params.rib_width)
        .extrude(params.rib_height)
    )
    part = part.union(ring)
    for direction in ALLOWED_DIRECTIONS:
        part = part.union(
            _raised_bar(
                compass_center,
                direction,
                params.compass_radius,
                params.rib_width,
                params.rib_height,
                params.thickness,
            )
        )
    zero_label = (
        cq.Workplane("XY")
        .workplane(offset=params.thickness)
        .center(55.0, 0.0)
        .text(
            "0>",
            5.0,
            GAUGE.label_height,
            combine=True,
            halign="center",
            valign="center",
        )
    )
    datum_label = (
        cq.Workplane("XY")
        .workplane(offset=params.thickness)
        .center(32.0, -31.0)
        .text(
            "BASE",
            5.0,
            GAUGE.label_height,
            combine=True,
            halign="center",
            valign="center",
        )
    )
    part = part.union(zero_label).union(datum_label)
    validate_print_bounds(part, "HU-H0-HHD-GAG-ANGLE")
    return part
