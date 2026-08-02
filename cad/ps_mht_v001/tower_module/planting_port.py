"""Phase 3A three-port tower receiver and real-geometry inspections."""

from __future__ import annotations

from functools import lru_cache
from math import cos, hypot, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    available_fastener_angles,
    interface_boss_diameter,
    interface_fastener_pitch_radius,
    m3_clearance_diameter,
    m3_fastener_boss_radius,
    m3_fastener_pitch_radius,
    m3_port_cartridge_bottom_z,
    m3_port_cartridge_clearance,
    m3_port_cartridge_height,
    m3_port_cartridge_length,
    m3_port_cartridge_width,
    m3_port_lug_housing_length,
    m3_port_lug_housing_width,
    m4_clearance_diameter,
    module_height,
    plant_port_angle,
    plant_port_center_z,
    plant_port_local_angles,
    plant_port_wall_thickness,
    port_receiver_bore_diameter,
    port_receiver_key_depth,
    port_receiver_key_width,
    port_receiver_length,
    port_receiver_outer_diameter,
    port_receiver_start_radius,
    port_saddle_length,
    port_saddle_outer_diameter,
    port_z_offset_pattern_candidate_a,
    port_z_offset_pattern_candidate_b,
    selected_port_z_offset_pattern,
    tower_max_diameter,
)
from ps_mht_v001.tower_module.module_interface import (
    build_planting_module_with_interface,
    station_point,
)
from ps_mht_v001.tower_module.m3_port_nut_cartridge import (
    build_m3_port_cartridge_slot_void,
    place_m3_port_cartridge_slot,
)


DO_NOT_PRINT_STATUS = "DO_NOT_PRINT_UNTIL_CALIBRATION"
SELECTED_SADDLE_CONCEPT = "A_INTEGRATED_SHALLOW_SADDLE"
PORT_RECEIVER_SOLID_COUNT = 3


def port_axis_vector(angle_deg: float) -> cq.Vector:
    """Unit vector pointing outward and 27 degrees above horizontal."""

    azimuth = radians(angle_deg)
    tilt = radians(plant_port_angle)
    return cq.Vector(
        cos(tilt) * cos(azimuth),
        cos(tilt) * sin(azimuth),
        sin(tilt),
    )


def port_origin(angle_deg: float, center_z: float) -> cq.Vector:
    """Axis datum placed inside the shell so the receiver stays shallow."""

    azimuth = radians(angle_deg)
    return cq.Vector(
        port_receiver_start_radius * cos(azimuth),
        port_receiver_start_radius * sin(azimuth),
        center_z,
    )


def orient_local_to_port(
    model: cq.Workplane,
    angle_deg: float,
    center_z: float,
) -> cq.Workplane:
    """Map a local +Z insertion axis onto one world-space plant-port axis."""

    origin = port_origin(angle_deg, center_z)
    return (
        model.rotate(
            (0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            90.0 - plant_port_angle,
        )
        .rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            angle_deg,
        )
        .translate((origin.x, origin.y, origin.z))
    )


def build_receiver_outer_local() -> cq.Workplane:
    """Uncut receiver, R-target saddle, and two M3 metal-fastener lugs."""

    receiver = (
        cq.Workplane("XY")
        .circle(0.5 * port_receiver_outer_diameter)
        .extrude(port_receiver_length)
    )
    saddle = (
        cq.Workplane("XY")
        .circle(0.5 * port_saddle_outer_diameter)
        .extrude(port_saddle_length)
    )
    model = receiver.union(saddle)
    for y in (-m3_fastener_pitch_radius, m3_fastener_pitch_radius):
        lug = (
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(m3_fastener_boss_radius)
            .extrude(port_receiver_length)
        )
        model = model.union(lug)
        side = 1 if y > 0.0 else -1
        housing = (
            cq.Workplane("XY")
            .box(
                m3_port_lug_housing_width,
                m3_port_lug_housing_length,
                port_receiver_length,
                centered=(True, True, False),
            )
            .translate((0.0, side * m3_fastener_pitch_radius, 0.0))
        )
        model = model.union(housing)
    return model


def build_receiver_void_local(
    adapter_clearance: float | None = None,
    m3_cartridge_clearance: float = m3_port_cartridge_clearance,
) -> cq.Workplane:
    """Common bore, asymmetric anti-rotation slot, and two M3 axes."""

    bore_diameter = port_receiver_bore_diameter
    if adapter_clearance is not None:
        from ps_mht_v001.parameters import port_adapter_outer_diameter

        bore_diameter = port_adapter_outer_diameter + 2.0 * adapter_clearance
    bore_radius = 0.5 * bore_diameter
    bore = (
        cq.Workplane("XY")
        .circle(bore_radius)
        .extrude(port_receiver_length + 12.0)
        .translate((0.0, 0.0, -6.0))
    )
    slot_outer_x = (
        0.5 * port_receiver_bore_diameter + port_receiver_key_depth
    )
    key_slot = (
        cq.Workplane("XY")
        .box(
            port_receiver_key_depth + 2.0,
            port_receiver_key_width + 1.0,
            port_receiver_length + 2.0,
            centered=(True, True, False),
        )
        .translate(
            (
                slot_outer_x - 0.5 * (port_receiver_key_depth + 2.0),
                0.0,
                -1.0,
            )
        )
    )
    void = bore.union(key_slot)
    for y in (-m3_fastener_pitch_radius, m3_fastener_pitch_radius):
        hole = (
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(0.5 * m3_clearance_diameter)
            .extrude(port_receiver_length + 2.0)
            .translate((0.0, 0.0, -1.0))
        )
        void = void.union(hole)
        side = 1 if y > 0.0 else -1
        void = void.union(
            place_m3_port_cartridge_slot(
                build_m3_port_cartridge_slot_void(
                    clearance=m3_cartridge_clearance
                ),
                side,
            )
        )
    return void


def build_planting_port_receiver() -> cq.Workplane:
    """Standalone common receiver/saddle geometry in print coordinates."""

    return build_receiver_outer_local().cut(build_receiver_void_local())


def build_receiver_outer(
    angle_deg: float,
    center_z: float,
) -> cq.Workplane:
    return orient_local_to_port(
        build_receiver_outer_local(),
        angle_deg,
        center_z,
    )


def build_receiver_void(
    angle_deg: float,
    center_z: float,
) -> cq.Workplane:
    return orient_local_to_port(
        build_receiver_void_local(),
        angle_deg,
        center_z,
    )


def selected_port_offsets() -> tuple[float, float, float]:
    if selected_port_z_offset_pattern == "A":
        return port_z_offset_pattern_candidate_a
    return port_z_offset_pattern_candidate_b


def port_center_heights(
    pattern: str = selected_port_z_offset_pattern,
) -> tuple[float, float, float]:
    offsets = (
        port_z_offset_pattern_candidate_a
        if pattern == "A"
        else port_z_offset_pattern_candidate_b
    )
    return tuple(plant_port_center_z + offset for offset in offsets)


def rotated_port_angles(module_rotation_deg: float) -> tuple[float, ...]:
    return tuple(
        (angle + module_rotation_deg) % 360.0
        for angle in plant_port_local_angles
    )


def _phase3a_m4_reinforcement(model: cq.Workplane) -> cq.Workplane:
    """Bring Phase 3A M4 roof samples to a real 6.0 mm radial wall."""

    outer_radius = 0.5 * m4_clearance_diameter + 6.0
    for angle in available_fastener_angles:
        x, y = station_point(interface_fastener_pitch_radius, angle)
        z = module_height - 1.75
        height = 1.75
        reinforcement = (
            cq.Workplane("XY")
            .circle(outer_radius)
            .extrude(height)
            .translate((x, y, z))
        )
        bore = (
            cq.Workplane("XY")
            .circle(0.5 * m4_clearance_diameter)
            .extrude(height + 0.2)
            .translate((x, y, z - 0.1))
        )
        model = model.union(reinforcement).cut(bore)
    return model


@lru_cache(maxsize=2)
def build_planting_module_with_ports_phase3a(
    pattern: str = selected_port_z_offset_pattern,
) -> cq.Workplane:
    """Build the one reusable Phase 3A module with exactly three ports."""

    if pattern not in ("A", "B"):
        raise ValueError("pattern must be A or B")
    model = _phase3a_m4_reinforcement(
        build_planting_module_with_interface()
    )
    heights = port_center_heights(pattern)
    for angle, center_z in zip(plant_port_local_angles, heights):
        model = model.union(build_receiver_outer(angle, center_z))
    for angle, center_z in zip(plant_port_local_angles, heights):
        model = model.cut(build_receiver_void(angle, center_z))
    return model


def receiver_outward_radius_formula() -> float:
    """Analytic worst projection along a port direction for the receiver."""

    tilt = radians(plant_port_angle)
    return (
        port_receiver_start_radius
        + port_receiver_length * cos(tilt)
        + 0.5 * port_saddle_outer_diameter * sin(tilt)
    )


def directional_max_radius(
    model: cq.Workplane,
    angle_deg: float,
) -> float:
    """Measure the exact B-rep support extent in one horizontal direction."""

    rotated = model.rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        -angle_deg,
    )
    return rotated.val().BoundingBox().xmax


def maximum_radial_radius(model: cq.Workplane) -> float:
    """Measure maximum XY radius from tessellated real geometry."""

    maximum = 0.0
    for solid in model.solids().vals():
        vertices, _ = solid.tessellate(0.35, 0.2)
        maximum = max(maximum, *(hypot(v.x, v.y) for v in vertices))
    return maximum


def receiver_pair_intersection_volumes(
    pattern: str = selected_port_z_offset_pattern,
) -> tuple[float, float, float]:
    """Return actual overlap volumes between the three saddle solids."""

    heights = port_center_heights(pattern)
    receivers = [
        build_receiver_outer(angle, center_z)
        for angle, center_z in zip(plant_port_local_angles, heights)
    ]
    pairs = ((0, 1), (0, 2), (1, 2))
    return tuple(
        sum(
            solid.Volume()
            for solid in receivers[first]
            .intersect(receivers[second])
            .solids()
            .vals()
        )
        for first, second in pairs
    )


def build_port_root_wall_probe_local() -> cq.Workplane:
    """Material sample through the thinnest anti-rotation-key wall."""

    bore_radius = 0.5 * port_receiver_bore_diameter
    slot_outer = bore_radius + port_receiver_key_depth
    return (
        cq.Workplane("XY")
        .box(
            plant_port_wall_thickness,
            port_receiver_key_width,
            6.0,
            centered=(True, True, False),
        )
        .translate(
            (
                slot_outer + 0.5 * plant_port_wall_thickness,
                0.0,
                3.0,
            )
        )
    )


def build_m3_wall_probe_local(y: float) -> cq.Workplane:
    """Five-millimetre annular material probe around one real M3 bore."""

    bore_radius = 0.5 * m3_clearance_diameter
    return (
        cq.Workplane("XY")
        .center(0.0, y)
        .circle(bore_radius + 5.0)
        .circle(bore_radius)
        .extrude(1.0)
        .translate((0.0, 0.0, 0.4))
    )


def build_m3_slot_side_wall_probe_local(side: int) -> cq.Workplane:
    """Two real 3 mm lateral wall samples alongside the cartridge pocket."""

    if side not in (-1, 1):
        raise ValueError("side must be -1 or +1")
    pocket_half_width = (
        0.5 * m3_port_cartridge_width + m3_port_cartridge_clearance
    )
    local_walls = []
    for lateral_sign in (-1, 1):
        wall = (
            cq.Workplane("XY")
            .box(
                9.0,
                3.0,
                m3_port_cartridge_height,
                centered=(True, True, False),
            )
            .translate(
                (
                    0.5,
                    lateral_sign * (pocket_half_width + 1.5),
                    m3_port_cartridge_bottom_z,
                )
            )
        )
        local_walls.append(wall.val())
    compound = cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound(local_walls)]
    )
    return place_m3_port_cartridge_slot(compound, side)


def build_phase3a_m4_wall_probe(angle_deg: float) -> cq.Workplane:
    """Actual six-millimetre wall probe in the reinforced top M4 boss."""

    bore_radius = 0.5 * m4_clearance_diameter
    x, y = station_point(interface_fastener_pitch_radius, angle_deg)
    return (
        cq.Workplane("XY")
        .center(x, y)
        .circle(bore_radius + 6.0)
        .circle(bore_radius)
        .extrude(1.0)
        .translate((0.0, 0.0, module_height - 1.5))
    )


def build_continuous_shell_band_probe(z: float) -> cq.Workplane:
    """Two-millimetre-high actual nominal shell band sample."""

    return (
        cq.Workplane("XY")
        .circle(100.0)
        .circle(97.0)
        .extrude(2.0)
        .translate((0.0, 0.0, z))
    )


def containment_ratio(
    material: cq.Workplane,
    probe: cq.Workplane,
) -> float:
    """Return the actual Boolean fraction of a required wall probe present."""

    probe_volume = sum(s.Volume() for s in probe.solids().vals())
    present = sum(
        s.Volume() for s in material.intersect(probe).solids().vals()
    )
    return present / probe_volume


def validate_receiver_design_limits() -> None:
    """Raise on receiver constraints independent of the full module."""

    if receiver_outward_radius_formula() > 0.5 * tower_max_diameter:
        raise ValueError("receiver analytic radial extent exceeds 120 mm")
    receiver = build_planting_port_receiver()
    if containment_ratio(receiver, build_port_root_wall_probe_local()) < 0.999:
        raise ValueError("actual anti-key port wall is below 4 mm")
    for y in (-m3_fastener_pitch_radius, m3_fastener_pitch_radius):
        if containment_ratio(receiver, build_m3_wall_probe_local(y)) < 0.999:
            raise ValueError("actual M3 surrounding wall is below 5 mm")


validate_receiver_design_limits()
