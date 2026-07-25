"""DR-H02 PETG four-slot panicle hub with fixed droop presets."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
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
from .interfaces import PANICLE_HEAD, PANICLE_TAB, STEM


@dataclass(frozen=True)
class PanicleHubParams:
    """DR-H02 dimensions in mm.

    The original 24 mm nominal body cannot retain 2 mm walls around four
    chamfered slots.  The approved <=30 mm adjustment is set to 30 mm so the
    20-degree stem interface also clears the slots and weight pocket.
    """

    preset: str = "upright"
    nominal_diameter: float = 24.0
    diameter: float = 30.0
    height: float = 28.0
    stem_od: float = STEM.nominal_diameter
    stem_hole_diameter: float = STEM.receiver_diameter
    stem_insert_depth: float = STEM.insertion_depth
    slot_count: int = 4
    slot_width: float = PANICLE_TAB.slot_width
    slot_thickness: float = PANICLE_TAB.slot_thickness
    slot_depth: float = PANICLE_TAB.insertion_depth
    slot_center_radius: float = 10.65
    slot_entry_chamfer: float = 0.6
    clamp_slot_width: float = 1.2
    clamp_hole_diameter: float = 3.2
    clamp_center_radius: float = 7.4
    clamp_center_z: float = 8.0
    nut_trap_corner_diameter: float = 6.4
    nut_trap_depth: float = 3.2
    droop_angle: float = 0.0
    droop_azimuth_degrees: float = 45.0
    droop_stem_start_offset: float = 0.76
    weight_pocket_diameter: float = 8.0
    weight_pocket_depth: float = 6.0
    standard_fillet: float = 1.0
    min_wall: float = PRINT.petg_min_wall
    calibration_status: str = PANICLE_HEAD.calibration_status


def params_for_preset(name: str) -> PanicleHubParams:
    """Return the fixed-angle upright or droop20 preset."""

    if name == "upright":
        return replace(PanicleHubParams(), preset=name, droop_angle=0.0)
    if name == "droop20":
        return replace(
            PanicleHubParams(),
            preset=name,
            droop_angle=PANICLE_HEAD.standard_droop_angle_degrees,
        )
    raise ValueError(f"unknown DR-H02 preset: {name!r}")


def weight_pocket_volume_mm3(params: PanicleHubParams) -> float:
    """Return nominal cylindrical mass-pocket capacity."""

    return (
        math.pi
        * (0.5 * params.weight_pocket_diameter) ** 2
        * params.weight_pocket_depth
    )


def slot_angles_degrees(params: PanicleHubParams) -> tuple[float, ...]:
    """Return the four deterministic 90-degree slot angles."""

    return tuple(index * 360.0 / params.slot_count for index in range(params.slot_count))


def stem_axis(
    params: PanicleHubParams,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Return the stem-hole start point and unit direction."""

    angle = math.radians(params.droop_angle)
    azimuth = math.radians(params.droop_azimuth_degrees)
    radial_x = math.cos(azimuth)
    radial_y = math.sin(azimuth)
    offset = params.droop_stem_start_offset if params.droop_angle else 0.0
    start = (offset * radial_x, offset * radial_y, 0.0)
    direction = (
        math.sin(angle) * radial_x,
        math.sin(angle) * radial_y,
        math.cos(angle),
    )
    return start, direction


def interference_clearances(params: PanicleHubParams) -> dict[str, float]:
    """Return conservative cavity-to-cavity and cavity-to-wall clearances."""

    radius = 0.5 * params.diameter
    pocket_radius = 0.5 * params.weight_pocket_diameter
    hole_radius = 0.5 * params.stem_hole_diameter
    nominal_inner = params.slot_center_radius - 0.5 * params.slot_thickness
    nominal_outer = params.slot_center_radius + 0.5 * params.slot_thickness
    chamfer_inner = nominal_inner - params.slot_entry_chamfer
    chamfer_tangent = 0.5 * params.slot_width + params.slot_entry_chamfer
    outer_corner_radius = math.hypot(nominal_outer, chamfer_tangent)
    adjacent_entry_gap = math.sqrt(2.0) * (chamfer_inner - chamfer_tangent)

    start, direction = stem_axis(params)
    end = tuple(
        start[index] + params.stem_insert_depth * direction[index]
        for index in range(3)
    )
    stem_to_pocket = params.height - params.weight_pocket_depth - end[2]
    if params.droop_angle:
        stem_to_pocket = (
            math.dist(end, (0.0, 0.0, params.height - params.weight_pocket_depth))
            - hole_radius
            - pocket_radius
        )

    stem_to_slot = nominal_inner - hole_radius
    if params.droop_angle:
        point_x = end[0]
        point_y = end[1]
        nearest_x = nominal_inner
        nearest_y = min(max(point_y, -0.5 * params.slot_width), 0.5 * params.slot_width)
        stem_to_slot = math.hypot(nearest_x - point_x, nearest_y - point_y) - hole_radius

    return {
        "slot_outer_wall": radius - outer_corner_radius,
        "adjacent_slot_gap": adjacent_entry_gap,
        "slot_to_pocket": chamfer_inner - pocket_radius,
        "stem_to_slot": stem_to_slot,
        "stem_to_pocket": stem_to_pocket,
        "nut_trap_to_stem": (
            params.clamp_center_radius
            - 0.5 * params.nut_trap_corner_diameter
            - hole_radius
        ),
        "nut_trap_outer_wall": (
            radius
            - params.clamp_center_radius
            - 0.5 * params.nut_trap_corner_diameter
        ),
    }


def validate_params(params: PanicleHubParams) -> None:
    """Validate DR-H02 interfaces, walls, presets, and cavity separation."""

    require_positive(
        nominal_diameter=params.nominal_diameter,
        diameter=params.diameter,
        height=params.height,
        stem_od=params.stem_od,
        stem_hole_diameter=params.stem_hole_diameter,
        stem_insert_depth=params.stem_insert_depth,
        slot_width=params.slot_width,
        slot_thickness=params.slot_thickness,
        slot_depth=params.slot_depth,
        slot_center_radius=params.slot_center_radius,
        slot_entry_chamfer=params.slot_entry_chamfer,
        clamp_slot_width=params.clamp_slot_width,
        clamp_hole_diameter=params.clamp_hole_diameter,
        clamp_center_radius=params.clamp_center_radius,
        clamp_center_z=params.clamp_center_z,
        nut_trap_corner_diameter=params.nut_trap_corner_diameter,
        nut_trap_depth=params.nut_trap_depth,
        weight_pocket_diameter=params.weight_pocket_diameter,
        weight_pocket_depth=params.weight_pocket_depth,
        standard_fillet=params.standard_fillet,
        min_wall=params.min_wall,
    )
    if params.preset not in {"upright", "droop20"}:
        raise ValueError(f"unknown DR-H02 preset: {params.preset!r}")
    if not 0.0 <= params.droop_angle <= 30.0:
        raise ValueError("DR-H02 droop angle must be in the 0-30 degree range")
    if params.preset == "upright" and params.droop_angle != 0.0:
        raise ValueError("DR-H02 upright preset requires 0 degrees")
    if params.preset == "droop20" and params.droop_angle != 20.0:
        raise ValueError("DR-H02 droop20 preset requires 20 degrees")
    if params.diameter > 30.0:
        raise ValueError("DR-H02 adjusted diameter cannot exceed 30 mm")
    if params.diameter < 30.0:
        raise ValueError(
            "DR-H02 requires 30.0 mm OD: 24 mm leaves insufficient wall; "
            "the calculated droop20 minimum is approximately 29.6 mm"
        )
    require_clearance(params.stem_hole_diameter, params.stem_od, "DR-H02 stem hole")
    require_clearance(params.slot_width, PANICLE_TAB.tab_width, "DR-H02 slot width")
    require_clearance(
        params.slot_thickness,
        PANICLE_TAB.tab_thickness,
        "DR-H02 slot thickness",
    )
    if params.slot_depth > PANICLE_TAB.tab_length:
        raise ValueError("DR-H02 slot depth exceeds TPU tab length")
    if params.slot_count != 4:
        raise ValueError("DR-H02 must have exactly four slots")
    require_minimum(params.min_wall, PRINT.petg_min_wall, "DR-H02 PETG wall")
    if params.stem_insert_depth > params.height:
        raise ValueError("DR-H02 stem insertion exceeds hub height")
    if params.weight_pocket_depth >= params.height:
        raise ValueError("DR-H02 mass pocket depth exceeds hub height")
    if params.standard_fillet > params.min_wall:
        raise ValueError("DR-H02 standard fillet cannot exceed minimum wall")

    for name, clearance in interference_clearances(params).items():
        require_minimum(clearance, params.min_wall, f"DR-H02 {name}")


def _workplane_from_solid(solid: cq.Shape) -> cq.Workplane:
    """Wrap one CadQuery solid in a Workplane."""

    return cq.Workplane("XY").newObject([solid])


def _transform_from_stem_local(
    shape: cq.Workplane,
    params: PanicleHubParams,
) -> cq.Workplane:
    """Transform a local-Z stem feature into the fixed-angle stem frame."""

    azimuth = params.droop_azimuth_degrees
    azimuth_radians = math.radians(azimuth)
    tangent_axis = (
        -math.sin(azimuth_radians),
        math.cos(azimuth_radians),
        0.0,
    )
    start, _direction = stem_axis(params)
    transformed = shape.rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        azimuth,
    )
    if params.droop_angle:
        transformed = transformed.rotate(
            (0.0, 0.0, 0.0),
            tangent_axis,
            params.droop_angle,
        )
    return transformed.translate(start)


def _slot_cutter(params: PanicleHubParams, angle_degrees: float) -> cq.Workplane:
    """Create one top-entry slot with a 0.6 mm tapered lead-in."""

    slot = (
        cq.Workplane("XY")
        .box(
            params.slot_thickness,
            params.slot_width,
            params.slot_depth,
            centered=(True, True, False),
        )
        .translate(
            (
                params.slot_center_radius,
                0.0,
                params.height - params.slot_depth,
            )
        )
    )
    lead_in = (
        cq.Workplane("XY")
        .workplane(offset=params.height - params.slot_entry_chamfer)
        .center(params.slot_center_radius, 0.0)
        .rect(params.slot_thickness, params.slot_width)
        .workplane(offset=params.slot_entry_chamfer)
        .center(-0.5 * params.slot_entry_chamfer, 0.0)
        .rect(
            params.slot_thickness + params.slot_entry_chamfer,
            params.slot_width + 2.0 * params.slot_entry_chamfer,
        )
        .loft(combine=True)
    )
    return slot.union(lead_in).rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        angle_degrees,
    )


def build(params: PanicleHubParams = PanicleHubParams()) -> cq.Workplane:
    """Build one fixed-angle DR-H02 hub with four replaceable-panel slots."""

    validate_params(params)
    radius = 0.5 * params.diameter
    body = (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(params.height)
        .edges("<Z")
        .fillet(params.standard_fillet)
    )

    for angle in slot_angles_degrees(params):
        body = body.cut(_slot_cutter(params, angle))

    pocket = (
        cq.Workplane("XY")
        .circle(0.5 * params.weight_pocket_diameter)
        .extrude(params.weight_pocket_depth + 0.05)
        .translate((0.0, 0.0, params.height - params.weight_pocket_depth))
    )
    body = body.cut(pocket)

    stem_hole_local = (
        cq.Workplane("XY")
        .circle(0.5 * params.stem_hole_diameter)
        .extrude(params.stem_insert_depth + 0.05)
    )
    body = body.cut(_transform_from_stem_local(stem_hole_local, params))
    entry_cone = cq.Solid.makeCone(
        0.5 * params.stem_hole_diameter + params.slot_entry_chamfer,
        0.5 * params.stem_hole_diameter,
        params.slot_entry_chamfer,
        cq.Vector(0.0, 0.0, 0.0),
        cq.Vector(0.0, 0.0, 1.0),
    )
    body = body.cut(
        _transform_from_stem_local(_workplane_from_solid(entry_cone), params)
    )

    slit_local = cq.Workplane("XY").box(
        radius + 0.2,
        params.clamp_slot_width,
        params.stem_insert_depth,
        centered=(False, True, False),
    )
    body = body.cut(_transform_from_stem_local(slit_local, params))

    clamp_hole_solid = cq.Solid.makeCylinder(
        0.5 * params.clamp_hole_diameter,
        2.0 * radius + 0.4,
        cq.Vector(
            params.clamp_center_radius,
            -radius - 0.2,
            params.clamp_center_z,
        ),
        cq.Vector(0.0, 1.0, 0.0),
    )
    body = body.cut(
        _transform_from_stem_local(
            _workplane_from_solid(clamp_hole_solid),
            params,
        )
    )

    nut_entry_y = (
        math.sqrt(radius**2 - params.clamp_center_radius**2) + 0.1
    )
    nut_trap_local = (
        cq.Workplane("XY")
        .polygon(6, params.nut_trap_corner_diameter)
        .extrude(params.nut_trap_depth)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
        .translate(
            (
                params.clamp_center_radius,
                nut_entry_y,
                params.clamp_center_z,
            )
        )
    )
    body = body.cut(_transform_from_stem_local(nut_trap_local, params))
    validate_printable_shape(body, f"DR-H02 {params.preset} panicle hub")
    return body


def export_step(params: PanicleHubParams, output_path: str | Path) -> Path:
    """Build and export DR-H02 as STEP."""

    return export_shape_step(build(params), output_path)


def export_stl(
    params: PanicleHubParams,
    output_path: str | Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1,
) -> Path:
    """Build and export DR-H02 as STL."""

    return export_shape_stl(build(params), output_path, tolerance, angular_tolerance)
