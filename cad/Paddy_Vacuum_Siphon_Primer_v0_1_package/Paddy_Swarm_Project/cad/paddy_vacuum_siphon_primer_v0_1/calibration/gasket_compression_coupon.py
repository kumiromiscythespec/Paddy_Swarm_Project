from __future__ import annotations

import cadquery as cq


def build() -> cq.Workplane:
    lower = cq.Workplane("XY").circle(42.0).circle(30.0).extrude(6.0)
    # Three groove depths on three removable sectors are represented by rings.
    ring_a = cq.Workplane("XY").workplane(offset=6.0).circle(40.0).circle(36.5).extrude(0.8)
    ring_b = cq.Workplane("XY").workplane(offset=6.0).circle(34.5).circle(31.0).extrude(1.1)
    bolt_points = [(34.0, 0), (-34.0, 0), (0, 34.0), (0, -34.0)]
    holes = cq.Workplane("XY").pushPoints(bolt_points).circle(2.25).extrude(8.0).translate((0, 0, -0.5))
    return lower.union(ring_a).union(ring_b).cut(holes).clean()
