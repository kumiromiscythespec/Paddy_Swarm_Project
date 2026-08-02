"""M4 hex-nut capture versus heat-set insert calibration plate."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    m4_clearance_diameter,
    m4_heat_set_insert_depth,
    m4_heat_set_insert_hole_diameter,
    m4_nut_across_flats,
    m4_nut_thickness,
)


def _marker_dots(
    model: cq.Workplane,
    x: float,
    count: int,
) -> cq.Workplane:
    for index in range(count):
        dot = (
            cq.Workplane("XY")
            .circle(1.3)
            .extrude(0.8)
            .translate((x + (index - 0.5 * (count - 1)) * 3.5, 13.5, 8.0))
        )
        model = model.union(dot)
    return model


def build_m4_insert_coupon() -> cq.Workplane:
    """Build one PETG plate carrying both provisional M4 retention tests."""

    plate = cq.Workplane("XY").box(
        90.0,
        40.0,
        8.0,
        centered=(True, True, False),
    )
    nut_x = -22.5
    insert_x = 22.5
    through = (
        cq.Workplane("XY")
        .pushPoints(((nut_x, 0.0), (insert_x, 0.0)))
        .circle(0.5 * m4_clearance_diameter)
        .extrude(10.0)
        .translate((0.0, 0.0, -1.0))
    )
    plate = plate.cut(through)

    nut_circumscribed_diameter = m4_nut_across_flats / 0.8660254037844386
    nut_pocket = (
        cq.Workplane("XY")
        .center(nut_x, 0.0)
        .polygon(6, nut_circumscribed_diameter)
        .extrude(m4_nut_thickness + 0.4)
        .translate((0.0, 0.0, 8.0 - m4_nut_thickness - 0.4))
    )
    plate = plate.cut(nut_pocket)

    insert_pocket = (
        cq.Workplane("XY")
        .center(insert_x, 0.0)
        .circle(0.5 * m4_heat_set_insert_hole_diameter)
        .extrude(m4_heat_set_insert_depth + 0.1)
        .translate((0.0, 0.0, 8.0 - m4_heat_set_insert_depth))
    )
    plate = plate.cut(insert_pocket)
    plate = _marker_dots(plate, nut_x, 1)
    plate = _marker_dots(plate, insert_x, 2)
    return plate

