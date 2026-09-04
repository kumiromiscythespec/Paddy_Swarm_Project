from __future__ import annotations

import cadquery as cq

GUARD_LENGTH = 170.0
GUARD_WIDTH = 26.0
GUARD_DEPTH = 18.0
WALL = 3.0


def build() -> cq.Workplane:
    back = cq.Workplane("XY").box(GUARD_WIDTH, WALL, GUARD_LENGTH, centered=(True, True, False))
    left = cq.Workplane("XY").box(WALL, GUARD_DEPTH, GUARD_LENGTH, centered=(True, True, False)).translate((-(GUARD_WIDTH-WALL)/2, GUARD_DEPTH/2-WALL/2, 0))
    right = left.mirror("YZ")
    guard = back.union(left).union(right)
    for z in (20.0, GUARD_LENGTH - 20.0):
        tab = cq.Workplane("XY").box(16.0, 5.0, 12.0, centered=(True, True, False)).translate((0, -4.0, z))
        guard = guard.union(tab)
    return guard.clean()
