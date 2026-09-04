from __future__ import annotations

import cadquery as cq
import parameters as p
from common.cq_helpers import add_cylindrical_cut, bolt_circle_points


def build() -> cq.Workplane:
    base = cq.Workplane("XY").rect(p.BASE_SIZE, p.BASE_SIZE).extrude(p.BASE_THICKNESS)

    base = add_cylindrical_cut(
        base,
        bolt_circle_points(p.BELLOWS_BOLT_COUNT, p.BELLOWS_BOLT_CIRCLE),
        p.BELLOWS_BOLT_HOLE_DIAMETER,
        -0.5,
        p.BASE_THICKNESS + 1.0,
    )
    base = add_cylindrical_cut(
        base,
        bolt_circle_points(p.GUIDE_ROD_COUNT, p.GUIDE_ROD_CIRCLE, phase_deg=90.0),
        p.GUIDE_HOLE_DIAMETER,
        -0.5,
        p.BASE_THICKNESS + 1.0,
    )

    air_ports = [(-p.AIR_PORT_X, 0.0), (p.AIR_PORT_X, 0.0)]
    base = add_cylindrical_cut(
        base,
        air_ports,
        p.AIR_PORT_HOLE_DIAMETER,
        -0.5,
        p.BASE_THICKNESS + 1.0,
    )

    floor_mounts = [
        (sx * (p.BASE_SIZE / 2.0 - 12.0), sy * (p.BASE_SIZE / 2.0 - 12.0))
        for sx in (-1, 1)
        for sy in (-1, 1)
    ]
    base = add_cylindrical_cut(base, floor_mounts, 6.5, -0.5, p.BASE_THICKNESS + 1.0)
    return base.clean()
