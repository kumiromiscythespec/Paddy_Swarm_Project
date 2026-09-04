from __future__ import annotations

import cadquery as cq
import parameters as p


def build() -> cq.Workplane:
    pad = (
        cq.Workplane("XY")
        .rect(p.FOOT_PAD_LENGTH, p.FOOT_PAD_WIDTH)
        .extrude(p.FOOT_PAD_THICKNESS)
        .edges("|Z")
        .fillet(6.0)
    )
    # Coarse, washable tread ribs.
    for x in range(-60, 61, 20):
        rib = cq.Workplane("XY").box(6.0, 86.0, 1.5, centered=(True, True, False)).translate((x, 0, p.FOOT_PAD_THICKNESS))
        pad = pad.union(rib)
    return pad.clean()
