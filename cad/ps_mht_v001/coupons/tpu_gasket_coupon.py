"""PETG groove fixture for 3 mm TPU/EPDM cord compression trials."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import gasket_groove_width


GROOVE_DEPTHS = (2.0, 2.2, 2.4)


def _marker_dots(
    model: cq.Workplane,
    x: float,
    count: int,
) -> cq.Workplane:
    for index in range(count):
        dot = (
            cq.Workplane("XY")
            .circle(1.1)
            .extrude(0.7)
            .translate((x + (index - 0.5 * (count - 1)) * 3.2, 18.0, 8.0))
        )
        model = model.union(dot)
    return model


def build_tpu_gasket_coupon() -> cq.Workplane:
    """Build one plate with 2.0/2.2/2.4 mm-deep 3.6 mm grooves."""

    plate = cq.Workplane("XY").box(
        100.0,
        42.0,
        8.0,
        centered=(True, True, False),
    )
    for index, (x, depth) in enumerate(
        zip((-30.0, 0.0, 30.0), GROOVE_DEPTHS),
        start=1,
    ):
        groove = (
            cq.Workplane("XY")
            .box(
                gasket_groove_width,
                30.0,
                depth + 0.05,
                centered=(True, True, False),
            )
            .translate((x, 0.0, 8.0 - depth))
        )
        plate = plate.cut(groove)
        plate = _marker_dots(plate, x, index)
    return plate

