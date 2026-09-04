from __future__ import annotations

import cadquery as cq
import parameters as p


def build() -> cq.Workplane:
    tube = (
        cq.Workplane("XY")
        .circle(p.DIP_TUBE_OUTER_DIAMETER / 2.0)
        .circle(p.DIP_TUBE_INNER_DIAMETER / 2.0)
        .extrude(p.DIP_TUBE_LENGTH)
    )
    # Four anti-blockage slots at the lower end.
    for angle in (0, 90, 180, 270):
        slot = (
            cq.Workplane("XZ")
            .rect(5.0, 12.0)
            .extrude(p.DIP_TUBE_OUTER_DIAMETER)
            .translate((0, -p.DIP_TUBE_OUTER_DIAMETER / 2.0, 5.0))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        tube = tube.cut(slot)
    return tube.clean()
