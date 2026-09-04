from __future__ import annotations

import cadquery as cq

import parameters as p
from common.cq_helpers import add_cylindrical_cut, bolt_circle_points, radial_box


def build() -> cq.Workplane:
    outer_r = p.TANK_OUTER_DIAMETER / 2.0
    inner_r = p.TANK_INNER_DIAMETER / 2.0
    flange_r = p.TANK_FLANGE_DIAMETER / 2.0

    outer = cq.Workplane("XY").circle(outer_r).extrude(p.TANK_BODY_HEIGHT)
    cavity = (
        cq.Workplane("XY")
        .workplane(offset=p.TANK_BASE_THICKNESS)
        .circle(inner_r)
        .extrude(p.TANK_INNER_HEIGHT + 0.2)
    )
    body = outer.cut(cavity)

    flange = (
        cq.Workplane("XY")
        .workplane(offset=p.TANK_BODY_HEIGHT)
        .circle(flange_r)
        .circle(inner_r)
        .extrude(p.TANK_FLANGE_THICKNESS)
    )
    body = body.union(flange)

    points = bolt_circle_points(p.TANK_BOLT_COUNT, p.TANK_BOLT_CIRCLE)
    body = add_cylindrical_cut(
        body,
        points,
        p.TANK_BOLT_HOLE_DIAMETER,
        p.TANK_BODY_HEIGHT - 0.5,
        p.TANK_FLANGE_THICKNESS + 1.0,
    )

    rib_height = p.TANK_BODY_HEIGHT - 16.0
    rib_radius = outer_r + p.TANK_VERTICAL_RIB_DEPTH / 2.0
    for i in range(p.TANK_VERTICAL_RIB_COUNT):
        rib = radial_box(
            p.TANK_VERTICAL_RIB_WIDTH,
            p.TANK_VERTICAL_RIB_DEPTH,
            rib_height,
            rib_radius,
            i * 360.0 / p.TANK_VERTICAL_RIB_COUNT,
            z0=8.0,
        )
        body = body.union(rib)

    # Bottom drain is intentionally a pilot recess, not a through-hole, until
    # the purchased bulkhead fitting is measured.
    drain_pilot = (
        cq.Workplane("XY")
        .circle(4.0)
        .extrude(1.0)
        .translate((0, 0, -0.01))
    )
    body = body.cut(drain_pilot)
    return body.clean()


if __name__ == "__main__":
    from cadquery import exporters
    exporters.export(build(), "tank_body.step")
