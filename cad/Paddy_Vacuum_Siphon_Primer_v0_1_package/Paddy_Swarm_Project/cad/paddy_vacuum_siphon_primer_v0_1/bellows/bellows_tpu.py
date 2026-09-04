from __future__ import annotations

import math
import cadquery as cq

import parameters as p
from common.cq_helpers import add_cylindrical_cut, bolt_circle_points


def _corrugated_radius(z: float) -> float:
    usable = p.BELLOWS_FREE_HEIGHT - 2.0 * p.BELLOWS_FLANGE_THICKNESS
    phase = (z - p.BELLOWS_FLANGE_THICKNESS) / usable
    mean_r = (p.BELLOWS_MAX_DIAMETER + p.BELLOWS_MIN_DIAMETER) / 4.0
    amplitude = (p.BELLOWS_MAX_DIAMETER - p.BELLOWS_MIN_DIAMETER) / 4.0
    return mean_r + amplitude * math.sin(2.0 * math.pi * p.BELLOWS_CONVOLUTION_COUNT * phase)


def _wall_at_radius(r: float) -> float:
    min_r = p.BELLOWS_MIN_DIAMETER / 2.0
    max_r = p.BELLOWS_MAX_DIAMETER / 2.0
    root_factor = 1.0 - (r - min_r) / max(max_r - min_r, 1e-6)
    return p.BELLOWS_WALL + (p.BELLOWS_ROOT_WALL - p.BELLOWS_WALL) * max(0.0, min(1.0, root_factor))


def build() -> cq.Workplane:
    flange_r = p.BELLOWS_FLANGE_DIAMETER / 2.0
    inner_flange_r = p.BELLOWS_MIN_DIAMETER / 2.0 - 2.0
    z0 = p.BELLOWS_FLANGE_THICKNESS
    z1 = p.BELLOWS_FREE_HEIGHT - p.BELLOWS_FLANGE_THICKNESS
    samples = p.BELLOWS_CONVOLUTION_COUNT * p.BELLOW_PROFILE_SAMPLES_PER_CONVOLUTION + 1

    outer_points = []
    inner_points = []
    for i in range(samples):
        z = z0 + (z1 - z0) * i / (samples - 1)
        r = _corrugated_radius(z)
        outer_points.append((r, z))
        inner_points.append((r - _wall_at_radius(r), z))

    profile = [
        (inner_flange_r, 0.0),
        (flange_r, 0.0),
        (flange_r, p.BELLOWS_FLANGE_THICKNESS),
        outer_points[0],
        *outer_points[1:],
        (flange_r, z1),
        (flange_r, p.BELLOWS_FREE_HEIGHT),
        (inner_flange_r, p.BELLOWS_FREE_HEIGHT),
        (inner_flange_r, z1),
        *reversed(inner_points),
        (inner_flange_r, z0),
    ]

    bellows = cq.Workplane("XZ").polyline(profile).close().revolve(360.0, (0, 0), (0, 1))

    holes = bolt_circle_points(p.BELLOWS_BOLT_COUNT, p.BELLOWS_BOLT_CIRCLE)
    bellows = add_cylindrical_cut(
        bellows,
        holes,
        p.BELLOWS_BOLT_HOLE_DIAMETER,
        -0.5,
        p.BELLOWS_FLANGE_THICKNESS + 1.0,
    )
    bellows = add_cylindrical_cut(
        bellows,
        holes,
        p.BELLOWS_BOLT_HOLE_DIAMETER,
        p.BELLOWS_FREE_HEIGHT - p.BELLOWS_FLANGE_THICKNESS - 0.5,
        p.BELLOWS_FLANGE_THICKNESS + 1.0,
    )
    return bellows.clean()


if __name__ == "__main__":
    from cadquery import exporters
    exporters.export(build(), "bellows_tpu.step")
