from __future__ import annotations

import cadquery as cq
import parameters as p


def build() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .rect(p.STAND_SIZE, p.STAND_SIZE)
        .extrude(p.STAND_BASE_THICKNESS)
        .faces(">Z")
        .workplane()
        .hole(p.STAND_DRAIN_CLEARANCE_DIAMETER)
    )

    cradle = (
        cq.Workplane("XY")
        .workplane(offset=p.STAND_BASE_THICKNESS)
        .circle(p.STAND_CRADLE_OUTER_DIAMETER / 2.0)
        .circle(p.STAND_CRADLE_INNER_DIAMETER / 2.0)
        .extrude(p.STAND_CRADLE_HEIGHT)
    )
    stand = plate.union(cradle)

    mounts = [
        (sx * p.STAND_MOUNT_OFFSET, sy * p.STAND_MOUNT_OFFSET)
        for sx in (-1, 1)
        for sy in (-1, 1)
    ]
    cutter = (
        cq.Workplane("XY")
        .pushPoints(mounts)
        .circle(p.STAND_MOUNT_HOLE_DIAMETER / 2.0)
        .extrude(p.STAND_BASE_THICKNESS + 1.0)
        .translate((0, 0, -0.5))
    )
    return stand.cut(cutter).clean()
