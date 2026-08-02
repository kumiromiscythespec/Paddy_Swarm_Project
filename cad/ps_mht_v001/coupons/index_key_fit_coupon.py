"""Phase 2 index-key fit coupon using the production key curvature."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    interface_key_axial_height,
    interface_key_clearance,
    interface_spigot_inner_diameter,
    interface_spigot_outer_diameter,
)
from ps_mht_v001.tower_module.module_interface import (
    build_index_key_solid,
    build_socket_key_groove_void,
)


KEY_CLEARANCES = (0.20, 0.30, 0.40)
COUPON_SOLID_COUNT = 6
STATUS = "DO_NOT_REPRINT_DEPRECATED_AFTER_PHYSICAL_FAILURE"


def _sector(
    inner_radius: float,
    outer_radius: float,
    height: float,
    start_deg: float = -8.0,
    end_deg: float = 8.0,
) -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(height)
    )
    reach = outer_radius + 2.0
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


def _dots(model: cq.Workplane, count: int, z: float) -> cq.Workplane:
    for index in range(count):
        angle = -3.0 + index * 3.0
        dot = (
            cq.Workplane("XY")
            .circle(1.0)
            .extrude(0.8)
            .translate(
                (
                    100.0 * cos(radians(angle)),
                    100.0 * sin(radians(angle)),
                    z,
                )
            )
        )
        model = model.union(dot)
    return model


def _male_piece() -> cq.Workplane:
    inner = 0.5 * interface_spigot_inner_diameter
    outer = 0.5 * interface_spigot_outer_diameter
    body = _sector(inner, outer, 5.0)
    key = build_index_key_solid(0.0).translate(
        (0.0, 0.0, 5.0 - (178.0 - interface_key_axial_height))
    )
    return body.union(key)


def _female_piece(clearance: float, marker_count: int) -> cq.Workplane:
    body = _sector(
        0.5 * interface_spigot_inner_diameter - 0.8,
        0.5 * interface_spigot_outer_diameter + 4.0,
        6.0,
    )
    groove = build_socket_key_groove_void(
        0.0,
        clearance=clearance,
    ).translate((0.0, 0.0, -2.0))
    return _dots(body.cut(groove), marker_count, 6.0)


def build_index_key_fit_coupon() -> cq.Workplane:
    """Return three male/female real-curvature key pairs on one A1 plate."""

    shapes: list[cq.Shape] = []
    for index, clearance in enumerate(KEY_CLEARANCES, start=1):
        x = -55.0 + (index - 1) * 55.0
        male = _male_piece().translate((x - 100.0, -23.0, 0.0))
        female = _female_piece(clearance, index).translate(
            (x - 100.0, 23.0, 0.0)
        )
        shapes.extend((male.val(), female.val()))
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


SELECTED_KEY_CLEARANCE = interface_key_clearance
