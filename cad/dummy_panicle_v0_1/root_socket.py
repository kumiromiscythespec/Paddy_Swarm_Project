"""DR-B01 one-piece MEDIUM root socket."""

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
from .interfaces import M4_CLEARANCE_DIAMETER, STEM


@dataclass(frozen=True)
class RootSocketParams:
    """DR-B01 dimensional parameters in mm."""

    stem_nominal_diameter: float = STEM.nominal_diameter
    stem_hole_diameter: float = STEM.receiver_diameter
    stem_insertion_depth: float = 25.0
    entry_chamfer: float = STEM.entry_chamfer
    base_width: float = 40.0
    base_length: float = 40.0
    base_height: float = 12.0
    socket_outer_diameter: float = 16.0
    socket_height: float = 35.0
    clamp_slit_width: float = 1.2
    clamp_screw_diameter: float = STEM.clamp_screw_clearance_diameter
    clamp_screw_from_socket_top: float = STEM.clamp_screw_offset
    clamp_lug_x_start: float = 3.5
    clamp_lug_x_end: float = 14.5
    clamp_lug_outer_y: float = 5.4
    clamp_lug_height: float = 12.0
    mount_hole_diameter: float = M4_CLEARANCE_DIAMETER
    mount_pitch_x: float = 30.0
    mount_pitch_y: float = 30.0
    petg_minimum_wall: float = PRINT.petg_min_wall
    tilt_angle_degrees: float = 0.0


def mount_hole_centers(params: RootSocketParams) -> tuple[tuple[float, float], ...]:
    """Return the four M4 mounting-hole centers."""

    half_x = 0.5 * params.mount_pitch_x
    half_y = 0.5 * params.mount_pitch_y
    return ((-half_x, -half_y), (-half_x, half_y), (half_x, -half_y), (half_x, half_y))


def clamp_screw_center(params: RootSocketParams) -> tuple[float, float]:
    """Return clamp screw X and Z center coordinates."""

    x = 0.5 * (params.clamp_lug_x_start + params.clamp_lug_x_end)
    z = params.base_height + params.socket_height - params.clamp_screw_from_socket_top
    return x, z


def validate_params(params: RootSocketParams) -> None:
    """Validate DR-B01 clearances, walls, depths, and the fixed 0° preset."""

    require_positive(
        stem_nominal_diameter=params.stem_nominal_diameter,
        stem_hole_diameter=params.stem_hole_diameter,
        stem_insertion_depth=params.stem_insertion_depth,
        entry_chamfer=params.entry_chamfer,
        base_width=params.base_width,
        base_length=params.base_length,
        base_height=params.base_height,
        socket_outer_diameter=params.socket_outer_diameter,
        socket_height=params.socket_height,
        clamp_slit_width=params.clamp_slit_width,
        clamp_screw_diameter=params.clamp_screw_diameter,
        clamp_lug_height=params.clamp_lug_height,
        mount_hole_diameter=params.mount_hole_diameter,
        mount_pitch_x=params.mount_pitch_x,
        mount_pitch_y=params.mount_pitch_y,
        petg_minimum_wall=params.petg_minimum_wall,
    )
    require_clearance(
        params.stem_hole_diameter,
        params.stem_nominal_diameter,
        "DR-B01 stem receiver",
    )
    require_minimum(
        params.stem_insertion_depth,
        STEM.insertion_depth,
        "DR-B01 stem insertion depth",
    )
    if params.stem_insertion_depth > params.socket_height:
        raise ValueError("DR-B01 stem insertion depth exceeds socket height")
    require_minimum(params.petg_minimum_wall, PRINT.petg_min_wall, "PETG minimum wall")
    radial_wall = 0.5 * (params.socket_outer_diameter - params.stem_hole_diameter)
    require_minimum(radial_wall, params.petg_minimum_wall, "DR-B01 socket radial wall")
    if params.tilt_angle_degrees != 0.0:
        raise ValueError("DR-B01 v0.1 supports only the fixed 0 degree preset")

    for center_x, center_y in mount_hole_centers(params):
        x_wall = 0.5 * params.base_width - abs(center_x) - 0.5 * params.mount_hole_diameter
        y_wall = 0.5 * params.base_length - abs(center_y) - 0.5 * params.mount_hole_diameter
        require_minimum(x_wall, params.petg_minimum_wall, "M4 hole X edge wall")
        require_minimum(y_wall, params.petg_minimum_wall, "M4 hole Y edge wall")

    screw_x, screw_z = clamp_screw_center(params)
    screw_radius = 0.5 * params.clamp_screw_diameter
    require_minimum(
        screw_x - screw_radius - params.clamp_lug_x_start,
        params.petg_minimum_wall,
        "M3 lug inner X wall",
    )
    require_minimum(
        params.clamp_lug_x_end - screw_x - screw_radius,
        params.petg_minimum_wall,
        "M3 lug outer X wall",
    )
    lug_bottom = screw_z - 0.5 * params.clamp_lug_height
    lug_top = screw_z + 0.5 * params.clamp_lug_height
    require_minimum(screw_z - screw_radius - lug_bottom, params.petg_minimum_wall, "M3 lug lower wall")
    require_minimum(lug_top - screw_z - screw_radius, params.petg_minimum_wall, "M3 lug upper wall")


def _solid_workplane(solid: cq.Shape) -> cq.Workplane:
    """Wrap one CadQuery solid in a Workplane."""

    return cq.Workplane("XY").newObject([solid])


def build(params: RootSocketParams = RootSocketParams()) -> cq.Workplane:
    """Build the one-piece, bottom-flat DR-B01 root socket."""

    validate_params(params)
    base = cq.Workplane("XY").box(
        params.base_width,
        params.base_length,
        params.base_height,
        centered=(True, True, False),
    )
    socket = (
        cq.Workplane("XY")
        .circle(0.5 * params.socket_outer_diameter)
        .extrude(params.socket_height)
        .translate((0.0, 0.0, params.base_height))
    )

    screw_x, screw_z = clamp_screw_center(params)
    lug_bottom = screw_z - 0.5 * params.clamp_lug_height
    lug_length = params.clamp_lug_x_end - params.clamp_lug_x_start
    lug_side_width = params.clamp_lug_outer_y - 0.5 * params.clamp_slit_width
    positive_lug = (
        cq.Workplane("XY")
        .box(lug_length, lug_side_width, params.clamp_lug_height, centered=(False, False, False))
        .translate(
            (
                params.clamp_lug_x_start,
                0.5 * params.clamp_slit_width,
                lug_bottom,
            )
        )
    )
    negative_lug = (
        cq.Workplane("XY")
        .box(lug_length, lug_side_width, params.clamp_lug_height, centered=(False, False, False))
        .translate(
            (
                params.clamp_lug_x_start,
                -params.clamp_lug_outer_y,
                lug_bottom,
            )
        )
    )
    part = base.union(socket).union(positive_lug).union(negative_lug)

    for center_x, center_y in mount_hole_centers(params):
        cutter = (
            cq.Workplane("XY")
            .center(center_x, center_y)
            .circle(0.5 * params.mount_hole_diameter)
            .extrude(params.base_height)
        )
        part = part.cut(cutter)

    socket_top = params.base_height + params.socket_height
    hole_bottom = socket_top - params.stem_insertion_depth
    stem_hole = (
        cq.Workplane("XY")
        .circle(0.5 * params.stem_hole_diameter)
        .extrude(params.stem_insertion_depth + 0.05)
        .translate((0.0, 0.0, hole_bottom))
    )
    part = part.cut(stem_hole)
    chamfer = cq.Solid.makeCone(
        0.5 * params.stem_hole_diameter,
        0.5 * params.stem_hole_diameter + params.entry_chamfer,
        params.entry_chamfer + 0.01,
        cq.Vector(0.0, 0.0, socket_top - params.entry_chamfer),
        cq.Vector(0.0, 0.0, 1.0),
    )
    part = part.cut(_solid_workplane(chamfer))

    slit = (
        cq.Workplane("XY")
        .box(
            params.clamp_lug_x_end + 0.1,
            params.clamp_slit_width,
            params.stem_insertion_depth + 0.1,
            centered=(False, True, False),
        )
        .translate((0.0, 0.0, hole_bottom))
    )
    part = part.cut(slit)
    screw_hole = cq.Solid.makeCylinder(
        0.5 * params.clamp_screw_diameter,
        2.0 * params.clamp_lug_outer_y + 0.2,
        cq.Vector(screw_x, -params.clamp_lug_outer_y - 0.1, screw_z),
        cq.Vector(0.0, 1.0, 0.0),
    )
    part = part.cut(_solid_workplane(screw_hole))
    validate_printable_shape(part, "DR-B01 root socket")
    return part


def export_step(params: RootSocketParams, output_path: str | Path) -> Path:
    """Build and export DR-B01 as STEP."""

    return export_shape_step(build(params), output_path)


def export_stl(
    params: RootSocketParams,
    output_path: str | Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1,
) -> Path:
    """Build and export DR-B01 as STL."""

    return export_shape_stl(build(params), output_path, tolerance, angular_tolerance)
