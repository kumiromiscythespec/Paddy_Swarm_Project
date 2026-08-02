"""Non-pressurized curved gasket compression/leak coupon."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    gasket_groove_width,
    interface_boss_diameter,
    interface_radial_clearance,
    interface_socket_outer_diameter,
    interface_spigot_inner_diameter,
    interface_spigot_outer_diameter,
    m4_clearance_diameter,
)


GROOVE_DEPTHS = (2.0, 2.2, 2.4)
COUPON_SOLID_COUNT = 6
TEST_MODE = "NON_PRESSURIZED_SMALL_WATER_CHARGE"
PRIMARY_GASKET = "PURCHASED_3MM_EPDM_CORD"
COMPARISON_GASKET = "PRINTED_TPU_CORD_CALIBRATION_ONLY"


def _sector(
    inner_radius: float,
    outer_radius: float,
    height: float,
    start_deg: float = -10.0,
    end_deg: float = 10.0,
) -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(height)
    )
    reach = outer_radius + 10.0
    points = [(0.0, 0.0)]
    points.extend(
        (
            reach * cos(radians(angle)),
            reach * sin(radians(angle)),
        )
        for angle in range(int(start_deg), int(end_deg) + 1, 2)
    )
    wedge = cq.Workplane("XY").polyline(points).close().extrude(height + 1.0)
    return ring.intersect(wedge)


def _m4_boss_and_hole(model: cq.Workplane, z_height: float) -> cq.Workplane:
    radius = 0.5 * interface_socket_outer_diameter + 6.6
    boss = (
        cq.Workplane("XY")
        .circle(0.5 * interface_boss_diameter)
        .extrude(z_height)
        .translate((radius, 0.0, 0.0))
    )
    hole = (
        cq.Workplane("XY")
        .circle(0.5 * m4_clearance_diameter)
        .extrude(z_height + 2.0)
        .translate((radius, 0.0, -1.0))
    )
    return model.union(boss).cut(hole)


def _male(depth: float, marker_count: int) -> cq.Workplane:
    spigot_outer = 0.5 * interface_spigot_outer_diameter
    model = _sector(0.5 * interface_spigot_inner_diameter, 110.0, 8.0)
    groove = _sector(
        spigot_outer - depth,
        spigot_outer + 0.05,
        gasket_groove_width,
    ).translate((0.0, 0.0, 2.0))
    catch = _sector(106.0, 108.0, 1.2).translate((0.0, 0.0, 6.8))
    model = _m4_boss_and_hole(model.cut(groove).cut(catch), 8.0)
    for index in range(marker_count):
        dot = (
            cq.Workplane("XY")
            .circle(1.0)
            .extrude(0.7)
            .translate((107.0, -7.0 + 3.2 * index, 8.0))
        )
        model = model.union(dot)
    return model


def _female() -> cq.Workplane:
    model = _sector(
        0.5 * interface_spigot_inner_diameter - interface_radial_clearance,
        110.0,
        8.0,
    )
    socket = _sector(
        0.5 * interface_spigot_inner_diameter - interface_radial_clearance,
        0.5 * interface_socket_outer_diameter,
        6.1,
    )
    fill_port = (
        cq.Workplane("XY")
        .circle(2.5)
        .extrude(10.0)
        .translate((106.0, 7.0, -1.0))
    )
    return _m4_boss_and_hole(model.cut(socket).cut(fill_port), 8.0)


def build_gasket_compression_leak_coupon() -> cq.Workplane:
    """Return three bolt-together curved male/female gasket trials."""

    shapes: list[cq.Shape] = []
    for index, depth in enumerate(GROOVE_DEPTHS, start=1):
        x = -58.0 + (index - 1) * 58.0
        male = _male(depth, index).translate((x - 104.0, -27.0, 0.0))
        female = _female().translate((x - 104.0, 27.0, 0.0))
        shapes.extend((male.val(), female.val()))
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])
