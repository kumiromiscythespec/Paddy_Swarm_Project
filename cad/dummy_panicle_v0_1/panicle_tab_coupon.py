"""Flat TPU tab coupon for PANICLE-TAB-V001."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from .cq_config import PRINT
from .cq_utils import (
    export_step as export_shape_step,
    export_stl as export_shape_stl,
    require_minimum,
    require_positive,
    validate_printable_shape,
)
from .interfaces import PANICLE_TAB


@dataclass(frozen=True)
class PanicleTabCouponParams:
    """Parameters for a flat TPU tab and handling paddle in mm."""

    tab_width: float = PANICLE_TAB.tab_width
    tab_thickness: float = PANICLE_TAB.tab_thickness
    tab_length: float = PANICLE_TAB.tab_length
    handle_width: float = 22.0
    handle_length: float = 24.0
    handle_thickness: float = 3.2
    tpu_minimum_wall: float = PRINT.tpu_min_wall


def validate_params(params: PanicleTabCouponParams) -> None:
    """Validate the TPU coupon parameters."""

    require_positive(
        tab_width=params.tab_width,
        tab_thickness=params.tab_thickness,
        tab_length=params.tab_length,
        handle_width=params.handle_width,
        handle_length=params.handle_length,
        handle_thickness=params.handle_thickness,
        tpu_minimum_wall=params.tpu_minimum_wall,
    )
    require_minimum(params.tab_thickness, params.tpu_minimum_wall, "TPU tab thickness")
    require_minimum(params.handle_thickness, params.tpu_minimum_wall, "TPU handle thickness")
    if params.handle_width < params.tab_width + 2.0 * params.tpu_minimum_wall:
        raise ValueError("TPU handle is too narrow around the tab root")


def build(params: PanicleTabCouponParams = PanicleTabCouponParams()) -> cq.Workplane:
    """Build a support-free, flat TPU tab coupon."""

    validate_params(params)
    handle = (
        cq.Workplane("XY")
        .box(
            params.handle_width,
            params.handle_length,
            params.handle_thickness,
            centered=(True, True, False),
        )
        .translate((0.0, -0.5 * params.handle_length, 0.0))
    )
    tab = (
        cq.Workplane("XY")
        .box(
            params.tab_width,
            params.tab_length + 0.5,
            params.tab_thickness,
            centered=(True, True, False),
        )
        .translate((0.0, 0.5 * params.tab_length - 0.25, 0.0))
    )
    part = handle.union(tab)
    validate_printable_shape(part, "TPU panicle tab coupon")
    return part


def export_step(params: PanicleTabCouponParams, output_path: str | Path) -> Path:
    """Build and export the TPU tab coupon as STEP."""

    return export_shape_step(build(params), output_path)


def export_stl(
    params: PanicleTabCouponParams,
    output_path: str | Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1,
) -> Path:
    """Build and export the TPU tab coupon as STL."""

    return export_shape_stl(build(params), output_path, tolerance, angular_tolerance)
