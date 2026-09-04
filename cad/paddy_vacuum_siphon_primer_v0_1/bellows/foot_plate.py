from __future__ import annotations

import cadquery as cq
import parameters as p
from common.cq_helpers import add_cylindrical_cut, bolt_circle_points


def build() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .rect(p.FOOT_PLATE_SIZE, p.FOOT_PLATE_SIZE)
        .extrude(p.FOOT_PLATE_THICKNESS)
        .edges("|Z")
        .fillet(8.0)
    )
    plate = add_cylindrical_cut(
        plate,
        bolt_circle_points(p.BELLOWS_BOLT_COUNT, p.BELLOWS_BOLT_CIRCLE),
        p.BELLOWS_BOLT_HOLE_DIAMETER,
        -0.5,
        p.FOOT_PLATE_THICKNESS + 1.0,
    )
    plate = add_cylindrical_cut(
        plate,
        bolt_circle_points(p.GUIDE_ROD_COUNT, p.GUIDE_ROD_CIRCLE, phase_deg=90.0),
        p.GUIDE_HOLE_DIAMETER + 2.0,
        -0.5,
        p.FOOT_PLATE_THICKNESS + 1.0,
    )

    # Underside ribs kept inside the bellows bolt circle.
    for angle in (0, 45, 90, 135):
        rib = (
            cq.Workplane("XY")
            .box(150.0, 5.0, 6.0, centered=(True, True, False))
            .rotate((0, 0, 0), (0, 0, 1), angle)
            .translate((0, 0, -6.0))
        )
        plate = plate.union(rib)
    return plate.clean()
