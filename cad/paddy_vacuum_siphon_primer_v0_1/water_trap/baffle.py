from __future__ import annotations

import cadquery as cq
import parameters as p


def build() -> cq.Workplane:
    plate = cq.Workplane("XY").box(
        p.BAFFLE_WIDTH,
        p.BAFFLE_THICKNESS,
        p.BAFFLE_HEIGHT,
        centered=(True, True, False),
    )
    left_foot = cq.Workplane("XY").box(
        p.BAFFLE_FOOT_LENGTH,
        p.BAFFLE_FOOT_WIDTH,
        p.BAFFLE_THICKNESS,
        centered=(True, True, False),
    ).translate((-p.BAFFLE_WIDTH / 2.0 + p.BAFFLE_FOOT_LENGTH / 2.0, 0, 0))
    right_foot = left_foot.mirror("YZ")
    return plate.union(left_foot).union(right_foot).clean()
