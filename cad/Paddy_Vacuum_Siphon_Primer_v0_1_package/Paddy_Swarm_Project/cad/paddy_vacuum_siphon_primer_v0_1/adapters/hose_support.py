from __future__ import annotations

import cadquery as cq
import parameters as p


def build() -> cq.Workplane:
    base = cq.Workplane("XY").box(42.0, 30.0, 6.0, centered=(True, True, False))
    saddle = (
        cq.Workplane("XZ")
        .circle((p.HOSE_OUTER_DIAMETER + 6.0) / 2.0)
        .circle((p.HOSE_OUTER_DIAMETER + 1.0) / 2.0)
        .extrude(18.0)
        .translate((0, -9.0, 10.0))
    )
    # Remove upper half to create a snap-in U saddle.
    cutter = cq.Workplane("XY").box(50.0, 30.0, 30.0, centered=(True, True, False)).translate((0, 0, 18.0))
    saddle = saddle.cut(cutter)
    mount_holes = (
        cq.Workplane("XY")
        .pushPoints([(-15.0, 0.0), (15.0, 0.0)])
        .circle(2.25)
        .extrude(7.0)
        .translate((0, 0, -0.5))
    )
    return base.union(saddle).cut(mount_holes).clean()
