"""Five-size PETG stem-hole clearance coupon."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from .cq_config import PRINT
from .cq_utils import (
    export_step as export_shape_step,
    export_stl as export_shape_stl,
    require_clearance,
    require_minimum,
    require_positive,
    validate_pairwise_wall,
    validate_printable_shape,
)
from .interfaces import STEM


@dataclass(frozen=True)
class StemClearanceCouponParams:
    """Parameters for the stem clearance coupon in mm."""

    stem_nominal_diameter: float = STEM.nominal_diameter
    hole_diameters: tuple[float, ...] = (4.10, 4.20, 4.30, 4.40, 4.50)
    length: float = 76.0
    width: float = 24.0
    height: float = 8.0
    hole_pitch: float = 14.0
    hole_y: float = 4.5
    label_y: float = -6.0
    label_size: float = 5.0
    label_relief: float = 0.6
    minimum_wall: float = PRINT.petg_min_wall


def hole_centers(params: StemClearanceCouponParams) -> tuple[float, ...]:
    """Return symmetric X coordinates for the coupon holes."""

    count = len(params.hole_diameters)
    return tuple((index - 0.5 * (count - 1)) * params.hole_pitch for index in range(count))


def validate_params(params: StemClearanceCouponParams) -> None:
    """Validate coupon dimensions and printable walls."""

    require_positive(
        stem_nominal_diameter=params.stem_nominal_diameter,
        length=params.length,
        width=params.width,
        height=params.height,
        hole_pitch=params.hole_pitch,
        label_size=params.label_size,
        label_relief=params.label_relief,
        minimum_wall=params.minimum_wall,
    )
    if len(params.hole_diameters) != 5:
        raise ValueError("stem clearance coupon must contain exactly five hole diameters")
    for index, diameter in enumerate(params.hole_diameters, start=1):
        require_positive(**{f"hole_diameter_{index}": diameter})
        require_clearance(diameter, params.stem_nominal_diameter, f"hole {index}")
    require_minimum(params.minimum_wall, PRINT.petg_min_wall, "coupon minimum wall")

    centers = hole_centers(params)
    validate_pairwise_wall(
        centers,
        params.hole_diameters,
        params.minimum_wall,
        "wall between stem coupon holes",
    )
    edge_wall_x = 0.5 * params.length - (
        max(abs(center) + 0.5 * diameter for center, diameter in zip(centers, params.hole_diameters))
    )
    require_minimum(edge_wall_x, params.minimum_wall, "coupon X edge wall")
    edge_wall_y = 0.5 * params.width - abs(params.hole_y) - 0.5 * max(params.hole_diameters)
    require_minimum(edge_wall_y, params.minimum_wall, "coupon Y edge wall")


def _raised_label(text: str, x: float, y: float, params: StemClearanceCouponParams) -> cq.Workplane:
    """Create a nozzle-readable raised numeric label."""

    return (
        cq.Workplane("XY")
        .workplane(offset=params.height - 0.05)
        .center(x, y)
        .text(text, params.label_size, params.label_relief + 0.05, combine=False)
    )


def build(params: StemClearanceCouponParams = StemClearanceCouponParams()) -> cq.Workplane:
    """Build one PETG coupon with five vertical through holes and labels 1–5."""

    validate_params(params)
    part = cq.Workplane("XY").box(
        params.length,
        params.width,
        params.height,
        centered=(True, True, False),
    )
    for center, diameter in zip(hole_centers(params), params.hole_diameters):
        cutter = (
            cq.Workplane("XY")
            .center(center, params.hole_y)
            .circle(0.5 * diameter)
            .extrude(params.height)
        )
        part = part.cut(cutter)
    for index, center in enumerate(hole_centers(params), start=1):
        part = part.union(_raised_label(str(index), center, params.label_y, params))
    validate_printable_shape(part, "stem clearance coupon")
    return part


def export_step(
    params: StemClearanceCouponParams,
    output_path: str | Path,
) -> Path:
    """Build and export the coupon as STEP."""

    return export_shape_step(build(params), output_path)


def export_stl(
    params: StemClearanceCouponParams,
    output_path: str | Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1,
) -> Path:
    """Build and export the coupon as STL."""

    return export_shape_stl(build(params), output_path, tolerance, angular_tolerance)
