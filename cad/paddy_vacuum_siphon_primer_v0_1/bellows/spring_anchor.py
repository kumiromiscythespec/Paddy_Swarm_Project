from __future__ import annotations

import cadquery as cq


def build() -> cq.Workplane:
    body = cq.Workplane("XY").box(28.0, 18.0, 18.0, centered=(True, True, False))
    mounting = cq.Workplane("XY").workplane(offset=-0.5).circle(2.75).extrude(19.0)
    cross = (
        cq.Workplane("XZ")
        .workplane(offset=-10.0)
        .circle(3.25)
        .extrude(20.0)
        .translate((0, 0, 11.0))
    )
    return body.cut(mounting).cut(cross).clean()
