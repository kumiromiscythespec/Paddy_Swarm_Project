"""Single parametric implementation of the four fixed-angle HHD sockets."""

from __future__ import annotations

import math

import cadquery as cq

from .cq_utils import validate_print_bounds
from .interfaces import validate_base_socket_interface, validate_stem_plug_interface, validate_stem_socket
from .parameters import BASE_SOCKET, STEM_PLUG_IF, StemSocketParams


SOCKET_PART_IDS: dict[float, str] = {
    0.0: "HU-H0-HHD-SKT-00",
    10.0: "HU-H0-HHD-SKT-10",
    20.0: "HU-H0-HHD-SKT-20",
    30.0: "HU-H0-HHD-SKT-30",
}


def params_for_angle(angle_deg: float) -> StemSocketParams:
    """Return one standard fixed-angle preset in the 0-degree index direction."""

    if angle_deg not in SOCKET_PART_IDS:
        raise ValueError(f"unknown HHD socket angle: {angle_deg}")
    return StemSocketParams(tilt_angle_deg=angle_deg)


def _octagon_corner_diameter(across_flats: float) -> float:
    """Convert octagon across-flats to CadQuery polygon diameter."""

    return across_flats / math.cos(math.pi / 8.0)


def axis_vector(params: StemSocketParams) -> tuple[float, float, float]:
    """Return the unit stem axis for tilt and index direction."""

    tilt = math.radians(params.tilt_angle_deg)
    direction = math.radians(params.tilt_direction_deg)
    return (
        math.sin(tilt) * math.cos(direction),
        math.sin(tilt) * math.sin(direction),
        math.cos(tilt),
    )


def measured_axis_angle_deg(params: StemSocketParams) -> float:
    """Measure the analytic axis angle from global +Z."""

    vector = axis_vector(params)
    return math.degrees(math.acos(max(-1.0, min(1.0, vector[2]))))


def receiver_entry_point(
    params: StemSocketParams,
) -> tuple[float, float, float]:
    """Return the open stem-receiver entry point in socket-local coordinates."""

    direction = axis_vector(params)
    return tuple(
        start + params.outer_axis_length * component
        for start, component in zip((0.0, 0.0, BASE_SOCKET.insertion_depth), direction)
    )


def _workplane_from_solid(solid: cq.Shape) -> cq.Workplane:
    """Wrap one CadQuery solid."""

    return cq.Workplane("XY").newObject([solid])


def _transform_from_vertical(
    shape: cq.Workplane,
    params: StemSocketParams,
) -> cq.Workplane:
    """Rotate a local-Z cutter into tilt and index direction."""

    return shape.rotate(
        (0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        params.tilt_angle_deg,
    ).rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        params.tilt_direction_deg,
    )


def build(params: StemSocketParams = StemSocketParams()) -> cq.Workplane:
    """Build one split-shank, octagon-indexed, fixed-angle PETG socket."""

    validate_base_socket_interface()
    validate_stem_plug_interface()
    validate_stem_socket(params)

    shank = (
        cq.Workplane("XY")
        .circle(0.5 * BASE_SOCKET.shank_diameter)
        .extrude(BASE_SOCKET.insertion_depth)
    )
    index = (
        cq.Workplane("XY")
        .workplane(offset=BASE_SOCKET.insertion_depth - BASE_SOCKET.index_depth)
        .polygon(8, _octagon_corner_diameter(BASE_SOCKET.index_af))
        .extrude(BASE_SOCKET.index_depth)
    )
    bead_bottom = 1.2
    bead = (
        cq.Workplane("XY")
        .workplane(offset=bead_bottom)
        .circle(0.5 * BASE_SOCKET.shank_diameter)
        .workplane(offset=0.6)
        .circle(
            0.5
            * (
                BASE_SOCKET.receiver_diameter
                + BASE_SOCKET.snap_interference
            )
        )
        .workplane(offset=0.6)
        .circle(0.5 * BASE_SOCKET.shank_diameter)
        .loft(combine=True)
    )
    part = shank.union(index).union(bead)

    direction = axis_vector(params)
    tube_start = cq.Vector(0.0, 0.0, BASE_SOCKET.insertion_depth)
    outer_tube = cq.Solid.makeCylinder(
        0.5 * params.outer_tube_diameter,
        params.outer_axis_length,
        tube_start,
        cq.Vector(*direction),
    )
    part = part.union(_workplane_from_solid(outer_tube))

    receiver_start_distance = (
        params.outer_axis_length - STEM_PLUG_IF.shank_length
    )
    receiver_start = cq.Vector(
        *(component * receiver_start_distance for component in direction)
    ) + tube_start
    receiver = cq.Solid.makeCylinder(
        0.5 * STEM_PLUG_IF.receiver_diameter,
        STEM_PLUG_IF.shank_length + 0.1,
        receiver_start,
        cq.Vector(*direction),
    )
    part = part.cut(_workplane_from_solid(receiver))

    chamfer_start_distance = (
        params.outer_axis_length - STEM_PLUG_IF.receiver_entry_chamfer
    )
    chamfer_start = cq.Vector(
        *(component * chamfer_start_distance for component in direction)
    ) + tube_start
    entry_chamfer = cq.Solid.makeCone(
        0.5 * STEM_PLUG_IF.receiver_diameter,
        0.5 * STEM_PLUG_IF.receiver_diameter
        + STEM_PLUG_IF.receiver_entry_chamfer,
        STEM_PLUG_IF.receiver_entry_chamfer + 0.05,
        chamfer_start,
        cq.Vector(*direction),
    )
    part = part.cut(_workplane_from_solid(entry_chamfer))

    slit_local = (
        cq.Workplane("XY")
        .box(
            0.5 * params.outer_tube_diameter + 1.0,
            STEM_PLUG_IF.receiver_slot_width,
            STEM_PLUG_IF.shank_length + 0.2,
            centered=(False, True, False),
        )
        .translate((0.0, 0.0, receiver_start_distance))
    )
    slit = _transform_from_vertical(slit_local, params).translate(
        (0.0, 0.0, BASE_SOCKET.insertion_depth)
    )
    part = part.cut(slit)

    shank_slit = (
        cq.Workplane("XY")
        .box(
            BASE_SOCKET.shank_diameter + 1.0,
            BASE_SOCKET.shank_split_width,
            5.0,
            centered=(True, True, False),
        )
    )
    part = part.cut(shank_slit)

    part_name = SOCKET_PART_IDS[params.tilt_angle_deg]
    validate_print_bounds(part, part_name)
    if abs(measured_axis_angle_deg(params) - params.tilt_angle_deg) > 0.3:
        raise ValueError(f"{part_name}: measured axis angle is outside ±0.3 degrees")
    return part
