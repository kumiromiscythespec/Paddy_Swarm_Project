from __future__ import annotations

import cadquery as cq
import parameters as p


def build() -> cq.Workplane:
    sleeve = (
        cq.Workplane("XY")
        .circle(p.GUIDE_BUSHING_OUTER_DIAMETER / 2.0)
        .circle(p.GUIDE_HOLE_DIAMETER / 2.0)
        .extrude(p.GUIDE_BUSHING_LENGTH)
    )
    flange = (
        cq.Workplane("XY")
        .workplane(offset=p.GUIDE_BUSHING_LENGTH)
        .circle(p.GUIDE_BUSHING_FLANGE_DIAMETER / 2.0)
        .circle(p.GUIDE_HOLE_DIAMETER / 2.0)
        .extrude(p.GUIDE_BUSHING_FLANGE_THICKNESS)
    )
    return sleeve.union(flange).clean()
