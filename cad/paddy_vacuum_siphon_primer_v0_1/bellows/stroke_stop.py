from __future__ import annotations

import cadquery as cq
import parameters as p


def build() -> cq.Workplane:
    collar = (
        cq.Workplane("XY")
        .circle(10.0)
        .circle((p.GUIDE_ROD_DIAMETER + 0.7) / 2.0)
        .extrude(12.0)
    )
    slit = cq.Workplane("XY").box(4.0, 12.0, 14.0, centered=(True, False, False)).translate((8.0, 0, -1.0))
    collar = collar.cut(slit)
    clamp_hole = (
        cq.Workplane("XZ")
        .workplane(offset=-11.0)
        .circle(2.1)
        .extrude(22.0)
        .translate((6.5, 0, 6.0))
    )
    return collar.cut(clamp_hole).clean()
