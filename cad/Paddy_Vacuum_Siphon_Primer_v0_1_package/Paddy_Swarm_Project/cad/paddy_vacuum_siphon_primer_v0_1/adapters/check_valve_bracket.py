from __future__ import annotations

import cadquery as cq
import parameters as p


def build() -> cq.Workplane:
    inner = p.CHECK_VALVE_OUTER_DIAMETER + p.CHECK_VALVE_BRACKET_CLEARANCE
    outer = inner + 8.0
    ring = cq.Workplane("XY").circle(outer / 2.0).circle(inner / 2.0).extrude(16.0)
    split = cq.Workplane("XY").box(5.0, outer, 18.0, centered=(True, True, False)).translate((outer / 2.0 - 2.0, 0, -1.0))
    ring = ring.cut(split)
    tab1 = cq.Workplane("XY").box(16.0, 8.0, 16.0, centered=(True, True, False)).translate((outer / 2.0 + 5.0, 7.0, 0))
    tab2 = tab1.mirror("XZ")
    bracket = ring.union(tab1).union(tab2)
    clamp_hole = (
        cq.Workplane("XZ")
        .workplane(offset=-(outer / 2.0 + 14.0))
        .circle(2.1)
        .extrude(outer + 28.0)
        .translate((outer / 2.0 + 5.0, 0, 8.0))
    )
    return bracket.cut(clamp_hole).clean()
