"""PETG multi-slot coupon for PANICLE-TAB-V001."""

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
from .interfaces import PANICLE_TAB


SlotSize = tuple[float, float]


@dataclass(frozen=True)
class PanicleSlotCouponParams:
    """Parameters for a vertical-entry PETG slot comparison block in mm."""

    tab_width: float = PANICLE_TAB.tab_width
    tab_thickness: float = PANICLE_TAB.tab_thickness
    slot_sizes: tuple[SlotSize, ...] = (
        (8.2, 2.4),
        (8.4, 2.4),
        (8.6, 2.4),
        (8.4, 2.2),
        (8.4, 2.6),
    )
    insertion_depth: float = PANICLE_TAB.insertion_depth
    length: float = 78.0
    width: float = 20.0
    height: float = 16.0
    slot_pitch: float = 15.0
    slot_y: float = 4.0
    label_y: float = -5.0
    label_size: float = 4.5
    label_relief: float = 0.6
    minimum_wall: float = PRINT.petg_min_wall


def slot_centers(params: PanicleSlotCouponParams) -> tuple[float, ...]:
    """Return symmetric X coordinates for all slots."""

    count = len(params.slot_sizes)
    return tuple((index - 0.5 * (count - 1)) * params.slot_pitch for index in range(count))


def validate_params(params: PanicleSlotCouponParams) -> None:
    """Validate slot clearances, floor thickness, and walls."""

    require_positive(
        tab_width=params.tab_width,
        tab_thickness=params.tab_thickness,
        insertion_depth=params.insertion_depth,
        length=params.length,
        width=params.width,
        height=params.height,
        slot_pitch=params.slot_pitch,
        label_size=params.label_size,
        label_relief=params.label_relief,
        minimum_wall=params.minimum_wall,
    )
    if len(params.slot_sizes) < 3:
        raise ValueError("slot coupon must compare at least three slot sizes")
    for index, (slot_width, slot_thickness) in enumerate(params.slot_sizes, start=1):
        require_positive(
            **{
                f"slot_width_{index}": slot_width,
                f"slot_thickness_{index}": slot_thickness,
            }
        )
        require_clearance(slot_width, params.tab_width, f"slot {index} width")
        require_clearance(slot_thickness, params.tab_thickness, f"slot {index} thickness")
    require_minimum(params.minimum_wall, PRINT.petg_min_wall, "slot coupon minimum wall")
    require_minimum(
        params.height - params.insertion_depth,
        params.minimum_wall,
        "slot coupon floor",
    )
    centers = slot_centers(params)
    widths = tuple(size[0] for size in params.slot_sizes)
    validate_pairwise_wall(centers, widths, params.minimum_wall, "wall between slots")
    edge_wall_x = 0.5 * params.length - max(
        abs(center) + 0.5 * size[0]
        for center, size in zip(centers, params.slot_sizes)
    )
    require_minimum(edge_wall_x, params.minimum_wall, "slot coupon X edge wall")
    edge_wall_y = 0.5 * params.width - abs(params.slot_y) - 0.5 * max(
        size[1] for size in params.slot_sizes
    )
    require_minimum(edge_wall_y, params.minimum_wall, "slot coupon Y edge wall")


def _raised_label(text: str, x: float, y: float, params: PanicleSlotCouponParams) -> cq.Workplane:
    """Create a raised numeric label with 0.6 mm relief."""

    return (
        cq.Workplane("XY")
        .workplane(offset=params.height - 0.05)
        .center(x, y)
        .text(text, params.label_size, params.label_relief + 0.05, combine=False)
    )


def build(params: PanicleSlotCouponParams = PanicleSlotCouponParams()) -> cq.Workplane:
    """Build a support-free PETG coupon with five downward slots."""

    validate_params(params)
    part = cq.Workplane("XY").box(
        params.length,
        params.width,
        params.height,
        centered=(True, True, False),
    )
    for center, (slot_width, slot_thickness) in zip(slot_centers(params), params.slot_sizes):
        cutter = (
            cq.Workplane("XY")
            .box(
                slot_width,
                slot_thickness,
                params.insertion_depth + 0.05,
                centered=(True, True, False),
            )
            .translate(
                (
                    center,
                    params.slot_y,
                    params.height - params.insertion_depth,
                )
            )
        )
        part = part.cut(cutter)
    for index, center in enumerate(slot_centers(params), start=1):
        part = part.union(_raised_label(str(index), center, params.label_y, params))
    validate_printable_shape(part, "PETG panicle slot coupon")
    return part


def export_step(params: PanicleSlotCouponParams, output_path: str | Path) -> Path:
    """Build and export the PETG slot coupon as STEP."""

    return export_shape_step(build(params), output_path)


def export_stl(
    params: PanicleSlotCouponParams,
    output_path: str | Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1,
) -> Path:
    """Build and export the PETG slot coupon as STL."""

    return export_shape_stl(build(params), output_path, tolerance, angular_tolerance)
