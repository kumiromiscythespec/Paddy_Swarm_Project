"""Phase 2 external spigot/socket, indexing, sealing, and M4 interface."""

from __future__ import annotations

from functools import lru_cache
from math import cos, radians, sin

import cadquery as cq

THIN_SIX_KEY_STATUS = "DEPRECATED_AFTER_PRINT_FAILURE"

from ps_mht_v001.common.fasteners import (
    CARTRIDGE_BOTTOM_Z,
    CARTRIDGE_PLACEMENT_RADIUS,
    CARTRIDGE_RADIAL_LENGTH,
    CARTRIDGE_TANGENTIAL_WIDTH,
    RETAINER_BOTTOM_Z,
    RETAINER_HEIGHT,
    RETAINER_LOCK_ARM_RADIAL_LENGTH,
    RETAINER_LOCK_ARM_TANGENTIAL_WIDTH,
    RETAINER_LOCK_ARM_THICKNESS,
    RETAINER_PLACEMENT_RADIUS,
    RETAINER_RADIAL_THICKNESS,
    RETAINER_TANGENTIAL_WIDTH,
)
from ps_mht_v001.parameters import (
    available_fastener_angles,
    gasket_groove_depth,
    gasket_groove_width,
    index_station_count,
    index_station_step,
    interface_boss_diameter,
    interface_fastener_pitch_radius,
    interface_flange_height,
    interface_key_axial_height,
    interface_key_clearance,
    interface_key_radial_height,
    interface_key_tangential_width,
    interface_lip_height,
    interface_outer_diameter,
    interface_radial_clearance,
    interface_socket_outer_diameter,
    interface_socket_roof_thickness,
    interface_spigot_inner_diameter,
    interface_spigot_outer_diameter,
    m4_clearance_diameter,
    module_height,
    module_wall_thickness,
    tower_body_diameter,
)


def _annulus(
    inner_radius: float,
    outer_radius: float,
    height: float,
    z: float = 0.0,
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(height)
        .translate((0.0, 0.0, z))
    )


def station_point(radius: float, angle_deg: float) -> tuple[float, float]:
    angle = radians(angle_deg)
    return radius * cos(angle), radius * sin(angle)


def radial_box(
    radial_length: float,
    tangential_width: float,
    height: float,
    radial_center: float,
    angle_deg: float,
    z: float,
) -> cq.Workplane:
    """Build a box whose local X direction is radial."""

    return (
        cq.Workplane("XY")
        .box(
            radial_length,
            tangential_width,
            height,
            centered=(True, True, False),
        )
        .translate((radial_center, 0.0, z))
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
    )


def index_angles() -> tuple[float, ...]:
    return tuple(index * index_station_step for index in range(index_station_count))


def build_index_key_solid(angle_deg: float) -> cq.Workplane:
    """Return one male key at its real assembled-module location."""

    spigot_outer_radius = 0.5 * interface_spigot_outer_diameter
    key_overlap = 0.3
    key_radial_center = (
        spigot_outer_radius
        + 0.5 * interface_key_radial_height
        - 0.5 * key_overlap
    )
    key_z = (
        module_height
        + interface_lip_height
        - interface_key_axial_height
    )
    return radial_box(
        interface_key_radial_height + key_overlap,
        interface_key_tangential_width,
        interface_key_axial_height,
        key_radial_center,
        angle_deg,
        key_z,
    )


def build_socket_key_groove_void(
    angle_deg: float,
    clearance: float = interface_key_clearance,
) -> cq.Workplane:
    """Return one real female-key clearance volume in module coordinates."""

    spigot_outer_radius = 0.5 * interface_spigot_outer_diameter
    key_overlap = 0.3
    key_radial_center = (
        spigot_outer_radius
        + 0.5 * interface_key_radial_height
        - 0.5 * key_overlap
    )
    socket_key_height = interface_key_axial_height + 0.4
    socket_key_z = interface_lip_height - socket_key_height
    return radial_box(
        interface_key_radial_height + 2.0 * interface_radial_clearance,
        interface_key_tangential_width + 2.0 * clearance,
        socket_key_height + 0.1,
        key_radial_center + 0.5 * interface_radial_clearance,
        angle_deg,
        socket_key_z,
    )


def build_m4_axis_probe(
    angle_deg: float,
    radius: float = 2.0,
    z: float = -0.5,
    height: float = 11.0,
) -> cq.Workplane:
    """Return a physical axial probe smaller than the real M4 clearance bore."""

    x, y = station_point(interface_fastener_pitch_radius, angle_deg)
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(height)
        .translate((x, y, z))
    )


def build_m4_required_wall_probe(
    angle_deg: float,
    required_wall: float = 5.5,
) -> cq.Workplane:
    """Return an annular material probe in the uninterrupted top boss."""

    bore_radius = 0.5 * m4_clearance_diameter
    x, y = station_point(interface_fastener_pitch_radius, angle_deg)
    return (
        _annulus(
            bore_radius,
            bore_radius + required_wall,
            1.0,
            module_height - interface_flange_height + 1.0,
        )
        .translate((x, y, 0.0))
    )


def m4_boss_nominal_radial_wall() -> float:
    """Return the minimum nominal boss radius outside the M4 bore."""

    return 0.5 * (interface_boss_diameter - m4_clearance_diameter)


def build_cartridge_pocket(angle_deg: float) -> cq.Workplane:
    """Return the externally open clearance volume for one cartridge."""

    return radial_box(
        CARTRIDGE_RADIAL_LENGTH + 3.8,
        CARTRIDGE_TANGENTIAL_WIDTH + 1.2,
        5.8,
        112.4,
        angle_deg,
        1.1,
    )


def build_cartridge_retainer_slot(angle_deg: float) -> cq.Workplane:
    """Return the top-open external slide-gate slot."""

    gate_slot = radial_box(
        RETAINER_RADIAL_THICKNESS + 0.6,
        RETAINER_TANGENTIAL_WIDTH + 0.6,
        RETAINER_HEIGHT + 1.2,
        RETAINER_PLACEMENT_RADIUS,
        angle_deg,
        0.2,
    )
    arm_recess = radial_box(
        RETAINER_LOCK_ARM_RADIAL_LENGTH + 0.6,
        RETAINER_LOCK_ARM_TANGENTIAL_WIDTH + 0.6,
        RETAINER_LOCK_ARM_THICKNESS + 0.5,
        RETAINER_PLACEMENT_RADIUS
        - 0.5 * RETAINER_LOCK_ARM_RADIAL_LENGTH,
        angle_deg,
        RETAINER_BOTTOM_Z + RETAINER_HEIGHT - 0.2,
    )
    return gate_slot.union(arm_recess)


def build_cartridge_access_probe(angle_deg: float) -> cq.Workplane:
    """Return a small probe entirely inside the intended radial access path."""

    return radial_box(
        10.0,
        8.0,
        3.0,
        115.0,
        angle_deg,
        2.4,
    )


@lru_cache(maxsize=1)
def build_planting_module_with_interface() -> cq.Workplane:
    """Build one Phase 2 module body as a single printable PETG solid."""

    body_outer_radius = 0.5 * tower_body_diameter
    body_inner_radius = body_outer_radius - module_wall_thickness
    interface_outer_radius = 0.5 * interface_outer_diameter
    spigot_inner_radius = 0.5 * interface_spigot_inner_diameter
    spigot_outer_radius = 0.5 * interface_spigot_outer_diameter
    socket_outer_radius = 0.5 * interface_socket_outer_diameter
    boss_radius = 0.5 * interface_boss_diameter

    model = _annulus(
        body_inner_radius,
        body_outer_radius,
        module_height,
    )
    model = model.union(
        _annulus(
            body_inner_radius,
            interface_outer_radius,
            interface_lip_height + interface_socket_roof_thickness,
            0.0,
        )
    )
    model = model.union(
        _annulus(
            body_inner_radius,
            interface_outer_radius,
            interface_flange_height,
            module_height - interface_flange_height,
        )
    )

    for angle in available_fastener_angles:
        x, y = station_point(interface_fastener_pitch_radius, angle)
        bottom_boss = (
            cq.Workplane("XY")
            .circle(boss_radius)
            .extrude(interface_lip_height + interface_socket_roof_thickness)
            .translate((x, y, 0.0))
        )
        top_boss = (
            cq.Workplane("XY")
            .circle(boss_radius)
            .extrude(interface_flange_height)
            .translate(
                (
                    x,
                    y,
                    module_height - interface_flange_height,
                )
            )
        )
        model = model.union(bottom_boss).union(top_boss)

    socket = _annulus(
        spigot_inner_radius - interface_radial_clearance,
        socket_outer_radius,
        interface_lip_height + 0.05,
        -0.05,
    )
    model = model.cut(socket)

    spigot = _annulus(
        spigot_inner_radius,
        spigot_outer_radius,
        interface_lip_height,
        module_height,
    )
    model = model.union(spigot)

    for angle in index_angles():
        model = model.union(build_index_key_solid(angle))

    for angle in index_angles():
        model = model.cut(build_socket_key_groove_void(angle))

    groove_outer_radius = spigot_outer_radius + 0.05
    groove_inner_radius = spigot_outer_radius - gasket_groove_depth
    groove_z = module_height + 1.2
    model = model.cut(
        _annulus(
            groove_inner_radius,
            groove_outer_radius,
            gasket_groove_width,
            groove_z,
        )
    )

    for angle in available_fastener_angles:
        x, y = station_point(interface_fastener_pitch_radius, angle)
        through_hole = (
            cq.Workplane("XY")
            .circle(0.5 * m4_clearance_diameter)
            .extrude(module_height + 2.0 * interface_lip_height + 2.0)
            .translate((x, y, -1.0))
        )
        model = model.cut(through_hole)
        model = model.cut(build_cartridge_pocket(angle))
        model = model.cut(build_cartridge_retainer_slot(angle))

    return model


def build_fastener_boss_reference() -> cq.Workplane:
    """Return six bottom and six top boss envelopes for keep-out checks."""

    boss_radius = 0.5 * interface_boss_diameter
    shapes: list[cq.Shape] = []
    for angle in available_fastener_angles:
        x, y = station_point(interface_fastener_pitch_radius, angle)
        for z, height in (
            (0.0, interface_lip_height + interface_socket_roof_thickness),
            (
                module_height - interface_flange_height,
                interface_flange_height,
            ),
        ):
            boss = (
                cq.Workplane("XY")
                .circle(boss_radius)
                .extrude(height)
                .translate((x, y, z))
            )
            shapes.append(boss.val())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


def interface_fixed_outer_diameter() -> float:
    """Maximum fixed printed diameter including the six M4 bosses."""

    return 2.0 * (
        interface_fastener_pitch_radius + 0.5 * interface_boss_diameter
    )


def socket_spigot_diametral_clearance() -> float:
    """Return the designed diametral clearance."""

    return interface_socket_outer_diameter - interface_spigot_outer_diameter


def compression_stop_radial_width() -> float:
    """Return the uninterrupted nominal radial contact band."""

    return (
        0.5 * interface_outer_diameter
        - 0.5 * interface_socket_outer_diameter
    )


def gasket_to_bolt_radial_clearance() -> float:
    """Minimum radial clearance from groove outer edge to M4 bore."""

    groove_outer_radius = 0.5 * interface_spigot_outer_diameter
    bolt_inner_radius = (
        interface_fastener_pitch_radius - 0.5 * m4_clearance_diameter
    )
    return bolt_inner_radius - groove_outer_radius


def cartridge_placement(
    cartridge: cq.Workplane,
    angle_deg: float,
    z_offset: float = 0.0,
) -> cq.Workplane:
    """Place a local cartridge model into one module bottom pocket."""

    return (
        cartridge.translate(
            (
                CARTRIDGE_PLACEMENT_RADIUS,
                0.0,
                CARTRIDGE_BOTTOM_Z + z_offset,
            )
        )
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
    )


def retainer_placement(
    retainer: cq.Workplane,
    angle_deg: float,
    z_offset: float = 0.0,
) -> cq.Workplane:
    """Place a retainer in the external slide-gate slot."""

    return (
        retainer.translate(
            (
                RETAINER_PLACEMENT_RADIUS,
                0.0,
                RETAINER_BOTTOM_Z + z_offset,
            )
        )
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
    )
