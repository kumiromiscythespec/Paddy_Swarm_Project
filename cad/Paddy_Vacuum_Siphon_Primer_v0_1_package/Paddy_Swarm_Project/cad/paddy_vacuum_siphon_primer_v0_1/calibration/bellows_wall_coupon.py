from __future__ import annotations

import math
import cadquery as cq


def mini_bellows(wall: float, x: float) -> cq.Workplane:
    height = 45.0
    max_r = 16.0
    min_r = 12.0
    samples = 31
    outer = []
    inner = []
    for i in range(samples):
        z = 3.0 + 39.0 * i / (samples - 1)
        r = (max_r + min_r) / 2.0 + (max_r - min_r) / 2.0 * math.sin(2 * math.pi * 3 * i / (samples - 1))
        outer.append((r, z))
        inner.append((r - wall, z))
    profile = [(10.0, 0), (19.0, 0), (19.0, 3.0), *outer, (19.0, 42.0), (19.0, 45.0), (10.0, 45.0), (10.0, 42.0), *reversed(inner), (10.0, 3.0)]
    return cq.Workplane("XZ").polyline(profile).close().revolve(360, (0, 0), (0, 1)).translate((x, 0, 0))


def build() -> cq.Workplane:
    result = mini_bellows(1.4, -45.0)
    result = result.union(mini_bellows(1.6, 0.0))
    result = result.union(mini_bellows(1.8, 45.0))
    return result.clean()
