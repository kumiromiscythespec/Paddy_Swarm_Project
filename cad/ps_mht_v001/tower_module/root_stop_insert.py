"""Optional perforated root-stop insert; not the primary root mesh."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    root_drain_hole_diameter,
    root_stop_insert_outer_diameter,
    root_stop_insert_thickness,
)


MATERIAL = "PRINTED_PETG_OPTIONAL"


def build_root_stop_insert() -> cq.Workplane:
    model = (
        cq.Workplane("XY")
        .circle(0.5 * root_stop_insert_outer_diameter)
        .extrude(root_stop_insert_thickness)
    )
    holes = [(0.0, 0.0)]
    for x in (-15.0, 0.0, 15.0):
        for y in (-15.0, 0.0, 15.0):
            if (x, y) != (0.0, 0.0):
                holes.append((x, y))
    cutters = (
        cq.Workplane("XY")
        .pushPoints(holes)
        .circle(0.5 * root_drain_hole_diameter)
        .extrude(root_stop_insert_thickness + 2.0)
        .translate((0.0, 0.0, -1.0))
    )
    return model.cut(cutters)

