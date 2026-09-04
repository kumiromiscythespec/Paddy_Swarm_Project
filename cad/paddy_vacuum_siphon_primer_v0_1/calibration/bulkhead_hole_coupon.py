from __future__ import annotations

import cadquery as cq

HOLES = [21.6, 21.8, 22.0, 22.2]


def build() -> cq.Workplane:
    plate = cq.Workplane("XY").rect(120.0, 42.0).extrude(5.0)
    x_positions = [-45.0, -15.0, 15.0, 45.0]
    for x, diameter in zip(x_positions, HOLES):
        cutter = cq.Workplane("XY").center(x, 0).circle(diameter / 2.0).extrude(6.0).translate((0, 0, -0.5))
        plate = plate.cut(cutter)
    return plate.clean()
