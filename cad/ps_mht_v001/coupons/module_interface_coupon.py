"""60-degree interface-sector coupon with three radial-clearance stations."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    interface_outer_diameter,
    interface_spigot_inner_diameter,
    interface_spigot_outer_diameter,
)


CLEARANCES_PER_SIDE = (0.30, 0.40, 0.50)
COUPON_SOLID_COUNT = 2


def _annular_sector(
    inner_radius: float,
    outer_radius: float,
    height: float,
    start_deg: float,
    end_deg: float,
    z: float = 0.0,
) -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(height)
        .translate((0.0, 0.0, z))
    )
    reach = outer_radius + 3.0
    steps = max(2, int((end_deg - start_deg) / 5.0))
    points = [(0.0, 0.0)]
    points.extend(
        (
            reach * cos(radians(start_deg + (end_deg - start_deg) * i / steps)),
            reach * sin(radians(start_deg + (end_deg - start_deg) * i / steps)),
        )
        for i in range(steps + 1)
    )
    wedge = (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(height + 2.0)
        .translate((0.0, 0.0, z - 1.0))
    )
    return ring.intersect(wedge)


def _add_symbol_dots(
    model: cq.Workplane,
    angle_deg: float,
    count: int,
    z: float,
) -> cq.Workplane:
    radius = 0.5 * interface_outer_diameter - 2.2
    for index in range(count):
        local_angle = angle_deg + (index - 0.5 * (count - 1)) * 1.7
        x = radius * cos(radians(local_angle))
        y = radius * sin(radians(local_angle))
        marker = (
            cq.Workplane("XY")
            .circle(1.15)
            .extrude(0.8)
            .translate((x, y, z))
        )
        model = model.union(marker)
    return model


def _male_sector() -> cq.Workplane:
    inner = 0.5 * interface_spigot_inner_diameter
    spigot_outer = 0.5 * interface_spigot_outer_diameter
    outer = 0.5 * interface_outer_diameter
    model = _annular_sector(inner, outer, 3.0, -30.0, 30.0)
    station_angles = (-20.0, 0.0, 20.0)
    for index, angle in enumerate(station_angles, start=1):
        pad = _annular_sector(
            inner,
            spigot_outer,
            8.0,
            angle - 5.0,
            angle + 5.0,
            z=3.0,
        )
        model = model.union(pad)
        model = _add_symbol_dots(model, angle, index, 3.0)
    return model


def _female_sector() -> cq.Workplane:
    inner = 0.5 * interface_spigot_inner_diameter
    outer = 0.5 * interface_outer_diameter
    spigot_outer = 0.5 * interface_spigot_outer_diameter
    model = _annular_sector(inner, outer, 8.0, -30.0, 30.0)
    station_angles = (-20.0, 0.0, 20.0)
    for index, (angle, clearance) in enumerate(
        zip(station_angles, CLEARANCES_PER_SIDE),
        start=1,
    ):
        socket = _annular_sector(
            inner - clearance,
            spigot_outer + clearance,
            8.2,
            angle - 5.3,
            angle + 5.3,
            z=-0.1,
        )
        model = model.cut(socket)
        model = _add_symbol_dots(model, angle, index, 8.0)
    return model


def build_module_interface_coupon() -> cq.Workplane:
    """Return male and female 60-degree sectors on one A1 print plate."""

    male = _male_sector()
    female = _female_sector().rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        180.0,
    )
    compound = cq.Compound.makeCompound([male.val(), female.val()])
    return cq.Workplane("XY").newObject([compound])

