from __future__ import annotations

import math
import cadquery as cq

import parameters as p
from common.cq_helpers import add_cylindrical_cut, bolt_circle_points, radial_box


def build() -> cq.Workplane:
    lid = cq.Workplane("XY").circle(p.TANK_LID_DIAMETER / 2.0).extrude(p.TANK_LID_THICKNESS)

    lid = add_cylindrical_cut(
        lid,
        bolt_circle_points(p.TANK_BOLT_COUNT, p.TANK_BOLT_CIRCLE),
        p.TANK_BOLT_HOLE_DIAMETER,
        -0.5,
        p.TANK_LID_THICKNESS + 1.0,
    )

    port_specs = [
        ((p.BULKHEAD_OUTLET_X, 0.0), p.BULKHEAD_NOMINAL_HOLE),
        ((p.BULKHEAD_INLET_X, 0.0), p.BULKHEAD_NOMINAL_HOLE),
        ((p.GAUGE_PORT_X, 0.0), p.GAUGE_HOLE_DIAMETER),
    ]
    for point, diameter in port_specs:
        lid = add_cylindrical_cut(lid, [point], diameter, -0.5, p.TANK_LID_THICKNESS + 1.0)
        boss = (
            cq.Workplane("XY")
            .workplane(offset=p.TANK_LID_THICKNESS)
            .center(*point)
            .circle(diameter / 2.0 + 4.0)
            .circle(diameter / 2.0)
            .extrude(5.0)
        )
        lid = lid.union(boss)

    # Eight low-profile top ribs. They do not cross the gasket face.
    for i in range(8):
        rib = radial_box(3.0, 38.0, 5.0, 22.0, i * 45.0, z0=p.TANK_LID_THICKNESS)
        lid = lid.union(rib)

    return lid.clean()


if __name__ == "__main__":
    from cadquery import exporters
    exporters.export(build(), "tank_lid.step")
