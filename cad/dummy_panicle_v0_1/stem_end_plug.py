"""DR-S03 common stem end plug."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import cadquery as cq

from .cq_utils import (
    export_step as export_shape_step,
    export_stl as export_shape_stl,
    require_minimum,
    require_positive,
    validate_printable_shape,
)
from .interfaces import STEM


@dataclass(frozen=True)
class StemEndPlugParams:
    """DR-S03 dimensional parameters in mm.

    The 15 mm and 17 mm side lengths meet at a datum plane and therefore sum
    to the required 32 mm overall length.  The 2 mm stop flange straddles that
    datum by 1 mm on each side instead of adding extra axial length.
    """

    preset: str = "tube_id_3p6_calibration"
    total_length: float = 32.0
    material_side_length: float = 15.0
    interface_side_length: float = 17.0
    interface_diameter: float = STEM.nominal_diameter
    material_core_diameter: float = 3.6
    barb_count: int = 2
    barb_height: float = 0.4
    barb_axial_length: float = 1.6
    flange_diameter: float = 7.0
    flange_thickness: float = 2.0
    tip_chamfer_length: float = 0.8
    shaft_tip_chamfer: float = 0.5


PRESET_MATERIAL_DIAMETERS = {
    "tube_id_3p6_calibration": 3.6,
    "soft_tube": 3.8,
    "solid_stem": 3.4,
}


def params_for_preset(name: str) -> StemEndPlugParams:
    """Return a DR-S03 fit candidate without implying a verified tube ID."""

    if name not in PRESET_MATERIAL_DIAMETERS:
        raise ValueError(f"unknown DR-S03 preset: {name!r}")
    return replace(
        StemEndPlugParams(),
        preset=name,
        material_core_diameter=PRESET_MATERIAL_DIAMETERS[name],
    )


def validate_params(params: StemEndPlugParams) -> None:
    """Validate DR-S03 lengths, diameters, flange, and rounded barb ramps."""

    require_positive(
        total_length=params.total_length,
        material_side_length=params.material_side_length,
        interface_side_length=params.interface_side_length,
        interface_diameter=params.interface_diameter,
        material_core_diameter=params.material_core_diameter,
        barb_height=params.barb_height,
        barb_axial_length=params.barb_axial_length,
        flange_diameter=params.flange_diameter,
        flange_thickness=params.flange_thickness,
        tip_chamfer_length=params.tip_chamfer_length,
        shaft_tip_chamfer=params.shaft_tip_chamfer,
    )
    if params.preset not in PRESET_MATERIAL_DIAMETERS:
        raise ValueError(f"unknown DR-S03 preset: {params.preset!r}")
    if params.barb_count < 1:
        raise ValueError("DR-S03 must have at least one barb")
    if abs(params.material_side_length + params.interface_side_length - params.total_length) > 1.0e-9:
        raise ValueError("DR-S03 side lengths must sum to total length")
    if params.flange_diameter <= max(
        params.interface_diameter,
        params.material_core_diameter + 2.0 * params.barb_height,
    ):
        raise ValueError("DR-S03 flange must be the largest radial feature")
    if params.flange_thickness >= 2.0 * min(
        params.material_side_length,
        params.interface_side_length,
    ):
        raise ValueError("DR-S03 flange is too thick for the side-length datum")
    require_minimum(params.interface_diameter, 3.0, "DR-S03 interface diameter")
    available_barb_length = params.material_side_length - params.tip_chamfer_length - 2.0
    if params.barb_count * params.barb_axial_length > available_barb_length:
        raise ValueError("DR-S03 barbs do not fit on the material-side shaft")


def _solid_workplane(solid: cq.Shape) -> cq.Workplane:
    """Wrap one CadQuery solid in a Workplane."""

    return cq.Workplane("XY").newObject([solid])


def build(params: StemEndPlugParams = StemEndPlugParams()) -> cq.Workplane:
    """Build a vertically printable DR-S03 with two gradual annular barbs."""

    validate_params(params)
    material_radius = 0.5 * params.material_core_diameter
    interface_radius = 0.5 * params.interface_diameter
    datum_z = params.material_side_length

    lower_tip = cq.Solid.makeCone(
        material_radius - 0.3,
        material_radius,
        params.tip_chamfer_length,
        cq.Vector(0.0, 0.0, 0.0),
        cq.Vector(0.0, 0.0, 1.0),
    )
    material_shaft = (
        cq.Workplane("XY")
        .circle(material_radius)
        .extrude(params.material_side_length - params.tip_chamfer_length)
        .translate((0.0, 0.0, params.tip_chamfer_length))
    )
    interface_shaft = (
        cq.Workplane("XY")
        .circle(interface_radius)
        .extrude(params.interface_side_length - params.shaft_tip_chamfer)
        .translate((0.0, 0.0, datum_z))
    )
    upper_tip = cq.Solid.makeCone(
        interface_radius,
        interface_radius - 0.3,
        params.shaft_tip_chamfer,
        cq.Vector(0.0, 0.0, params.total_length - params.shaft_tip_chamfer),
        cq.Vector(0.0, 0.0, 1.0),
    )
    flange = (
        cq.Workplane("XY")
        .circle(0.5 * params.flange_diameter)
        .extrude(params.flange_thickness)
        .translate((0.0, 0.0, datum_z - 0.5 * params.flange_thickness))
    )
    part = (
        _solid_workplane(lower_tip)
        .union(material_shaft)
        .union(interface_shaft)
        .union(_solid_workplane(upper_tip))
        .union(flange)
    )

    usable_start = params.tip_chamfer_length + 1.5
    spacing = (
        params.material_side_length - usable_start - 2.0
    ) / params.barb_count
    ramp = 0.5 * params.barb_axial_length
    for index in range(params.barb_count):
        start_z = usable_start + index * spacing
        up_ramp = cq.Solid.makeCone(
            material_radius,
            material_radius + params.barb_height,
            ramp,
            cq.Vector(0.0, 0.0, start_z),
            cq.Vector(0.0, 0.0, 1.0),
        )
        down_ramp = cq.Solid.makeCone(
            material_radius + params.barb_height,
            material_radius,
            ramp,
            cq.Vector(0.0, 0.0, start_z + ramp),
            cq.Vector(0.0, 0.0, 1.0),
        )
        part = part.union(_solid_workplane(up_ramp)).union(_solid_workplane(down_ramp))
    validate_printable_shape(part, f"DR-S03 {params.preset} stem end plug")
    return part


def export_step(params: StemEndPlugParams, output_path: str | Path) -> Path:
    """Build and export DR-S03 as STEP."""

    return export_shape_step(build(params), output_path)


def export_stl(
    params: StemEndPlugParams,
    output_path: str | Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1,
) -> Path:
    """Build and export DR-S03 as STL."""

    return export_shape_stl(build(params), output_path, tolerance, angular_tolerance)
