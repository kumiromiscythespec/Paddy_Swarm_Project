"""DR-C01 reusable cartridge holder and removable tube-marking gauge."""

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
    validate_printable_shape,
)
from .interfaces import CARTRIDGE, STEM


@dataclass(frozen=True)
class CuttingCartridgeHolderParams:
    """DR-C01 holder dimensions in mm.

    The 4.10 mm cartridge bore and 4.30 mm stem bore are calibration
    candidates.  They do not guarantee retention before physical measurement.
    """

    holder_length: float = CARTRIDGE.holder_length
    holder_outer_diameter: float = 12.0
    cartridge_outer_diameter: float = CARTRIDGE.tube_outer_diameter
    cartridge_bore_diameter: float = 4.10
    cartridge_insertion_depth: float = CARTRIDGE.holder_insertion_depth
    stem_nominal_diameter: float = STEM.nominal_diameter
    stem_bore_diameter: float = STEM.receiver_diameter
    fiber_channel_diameter: float = CARTRIDGE.fiber_channel_diameter
    separator_thickness: float = 0.8
    guard_ring_outer_diameter: float = 14.0
    guard_ring_width: float = 1.2
    petg_minimum_wall: float = PRINT.petg_min_wall


@dataclass(frozen=True)
class TubeMarkingGaugeParams:
    """Temporary split gauge for marking paper tube, removed before cutting."""

    cartridge_outer_diameter: float = CARTRIDGE.tube_outer_diameter
    gauge_inner_diameter: float = 4.4
    gauge_outer_diameter: float = 8.8
    gauge_width: float = 2.4
    split_width: float = 1.0
    petg_minimum_wall: float = PRINT.petg_min_wall


def stem_socket_depth(params: CuttingCartridgeHolderParams) -> float:
    """Return the compact non-standard outer-stem engagement depth."""

    return params.holder_length - params.cartridge_insertion_depth - params.separator_thickness


def validate_params(params: CuttingCartridgeHolderParams) -> None:
    """Validate DR-C01 fit, separator, walls, and cut-zone derivation."""

    require_positive(
        holder_length=params.holder_length,
        holder_outer_diameter=params.holder_outer_diameter,
        cartridge_outer_diameter=params.cartridge_outer_diameter,
        cartridge_bore_diameter=params.cartridge_bore_diameter,
        cartridge_insertion_depth=params.cartridge_insertion_depth,
        stem_nominal_diameter=params.stem_nominal_diameter,
        stem_bore_diameter=params.stem_bore_diameter,
        fiber_channel_diameter=params.fiber_channel_diameter,
        separator_thickness=params.separator_thickness,
        guard_ring_outer_diameter=params.guard_ring_outer_diameter,
        guard_ring_width=params.guard_ring_width,
        petg_minimum_wall=params.petg_minimum_wall,
    )
    require_clearance(
        params.cartridge_bore_diameter,
        params.cartridge_outer_diameter,
        "DR-C01 cartridge friction bore",
    )
    require_clearance(
        params.stem_bore_diameter,
        params.stem_nominal_diameter,
        "DR-C01 outer stem bore",
    )
    require_minimum(
        params.cartridge_insertion_depth,
        CARTRIDGE.holder_insertion_depth,
        "DR-C01 cartridge insertion depth",
    )
    if params.cartridge_insertion_depth + params.separator_thickness >= params.holder_length:
        raise ValueError("DR-C01 cartridge pocket leaves no outer stem socket")
    if params.fiber_channel_diameter >= CARTRIDGE.tube_inner_diameter:
        raise ValueError("DR-C01 fiber channel does not fit inside the paper tube")
    require_minimum(params.separator_thickness, 2.0 * PRINT.layer_height, "DR-C01 separator")
    require_minimum(params.petg_minimum_wall, PRINT.petg_min_wall, "PETG minimum wall")
    radial_wall = 0.5 * (
        params.holder_outer_diameter - max(
            params.cartridge_bore_diameter,
            params.stem_bore_diameter,
        )
    )
    require_minimum(radial_wall, params.petg_minimum_wall, "DR-C01 radial wall")
    if params.guard_ring_outer_diameter < params.holder_outer_diameter:
        raise ValueError("DR-C01 guard ring cannot be smaller than the holder")
    if abs(CARTRIDGE.derived_cuttable_length - CARTRIDGE.cuttable_length) > 1.0e-9:
        raise ValueError("DR-C01 shared cut-zone dimensions are inconsistent")


def validate_gauge_params(params: TubeMarkingGaugeParams) -> None:
    """Validate the removable paper-tube marking gauge."""

    require_positive(
        cartridge_outer_diameter=params.cartridge_outer_diameter,
        gauge_inner_diameter=params.gauge_inner_diameter,
        gauge_outer_diameter=params.gauge_outer_diameter,
        gauge_width=params.gauge_width,
        split_width=params.split_width,
        petg_minimum_wall=params.petg_minimum_wall,
    )
    require_clearance(
        params.gauge_inner_diameter,
        params.cartridge_outer_diameter,
        "DR-C01 marking gauge clearance",
    )
    radial_wall = 0.5 * (params.gauge_outer_diameter - params.gauge_inner_diameter)
    require_minimum(radial_wall, params.petg_minimum_wall, "DR-C01 gauge radial wall")
    if params.split_width >= params.gauge_outer_diameter:
        raise ValueError("DR-C01 gauge split is wider than the ring")


def build(
    params: CuttingCartridgeHolderParams = CuttingCartridgeHolderParams(),
) -> cq.Workplane:
    """Build one common holder; print two copies for upper and lower positions."""

    validate_params(params)
    body = (
        cq.Workplane("XY")
        .circle(0.5 * params.holder_outer_diameter)
        .extrude(params.holder_length)
    )
    ring = (
        cq.Workplane("XY")
        .circle(0.5 * params.guard_ring_outer_diameter)
        .extrude(params.guard_ring_width)
        .translate((0.0, 0.0, params.holder_length - params.guard_ring_width))
    )
    part = body.union(ring)

    outer_depth = stem_socket_depth(params)
    stem_pocket = (
        cq.Workplane("XY")
        .circle(0.5 * params.stem_bore_diameter)
        .extrude(outer_depth)
    )
    cartridge_pocket = (
        cq.Workplane("XY")
        .circle(0.5 * params.cartridge_bore_diameter)
        .extrude(params.cartridge_insertion_depth + 0.05)
        .translate((0.0, 0.0, params.holder_length - params.cartridge_insertion_depth))
    )
    fiber_channel = (
        cq.Workplane("XY")
        .circle(0.5 * params.fiber_channel_diameter)
        .extrude(params.holder_length)
    )
    part = part.cut(stem_pocket).cut(cartridge_pocket).cut(fiber_channel)
    validate_printable_shape(part, "DR-C01 cutting cartridge holder")
    return part


def build_tube_marking_gauge(
    params: TubeMarkingGaugeParams = TubeMarkingGaugeParams(),
) -> cq.Workplane:
    """Build a marking aid that must be removed before any cutting operation."""

    validate_gauge_params(params)
    gauge = (
        cq.Workplane("XY")
        .circle(0.5 * params.gauge_outer_diameter)
        .circle(0.5 * params.gauge_inner_diameter)
        .extrude(params.gauge_width)
    )
    split = (
        cq.Workplane("XY")
        .box(
            0.5 * params.gauge_outer_diameter + 0.1,
            params.split_width,
            params.gauge_width,
            centered=(False, True, False),
        )
    )
    gauge = gauge.cut(split)
    validate_printable_shape(gauge, "DR-C01 tube marking gauge")
    return gauge


def export_step(
    params: CuttingCartridgeHolderParams,
    output_path: str | Path,
) -> Path:
    """Build and export one DR-C01 holder as STEP."""

    return export_shape_step(build(params), output_path)


def export_stl(
    params: CuttingCartridgeHolderParams,
    output_path: str | Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1,
) -> Path:
    """Build and export one DR-C01 holder as STL."""

    return export_shape_stl(build(params), output_path, tolerance, angular_tolerance)


def export_gauge_step(params: TubeMarkingGaugeParams, output_path: str | Path) -> Path:
    """Build and export one DR-C01 tube-marking gauge as STEP."""

    return export_shape_step(build_tube_marking_gauge(params), output_path)


def export_gauge_stl(
    params: TubeMarkingGaugeParams,
    output_path: str | Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1,
) -> Path:
    """Build and export one DR-C01 tube-marking gauge as STL."""

    return export_shape_stl(
        build_tube_marking_gauge(params),
        output_path,
        tolerance,
        angular_tolerance,
    )
