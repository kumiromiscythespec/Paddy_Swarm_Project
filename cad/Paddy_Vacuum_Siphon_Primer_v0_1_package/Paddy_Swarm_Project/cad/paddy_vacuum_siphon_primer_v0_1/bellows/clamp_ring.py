from __future__ import annotations

import cadquery as cq
import parameters as p
from common.cq_helpers import add_cylindrical_cut, bolt_circle_points


def build() -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(p.CLAMP_RING_OUTER_DIAMETER / 2.0)
        .circle(p.CLAMP_RING_INNER_DIAMETER / 2.0)
        .extrude(p.CLAMP_RING_THICKNESS)
    )
    ring = add_cylindrical_cut(
        ring,
        bolt_circle_points(p.BELLOWS_BOLT_COUNT, p.BELLOWS_BOLT_CIRCLE),
        p.BELLOWS_BOLT_HOLE_DIAMETER,
        -0.5,
        p.CLAMP_RING_THICKNESS + 1.0,
    )
    return ring.clean()
