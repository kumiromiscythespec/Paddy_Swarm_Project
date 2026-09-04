from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import cadquery as cq
from cadquery import exporters


def bolt_circle_points(count: int, diameter: float, phase_deg: float = 22.5):
    radius = diameter / 2.0
    return [
        (
            radius * math.cos(math.radians(phase_deg + i * 360.0 / count)),
            radius * math.sin(math.radians(phase_deg + i * 360.0 / count)),
        )
        for i in range(count)
    ]


def export_part(part: cq.Workplane, output_dir: Path, stem: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    exporters.export(part, str(output_dir / f"{stem}.step"))
    exporters.export(part, str(output_dir / f"{stem}.stl"), tolerance=0.08, angularTolerance=0.12)


def add_cylindrical_cut(
    part: cq.Workplane,
    points: Iterable[tuple[float, float]],
    diameter: float,
    z0: float,
    height: float,
) -> cq.Workplane:
    cutter = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .pushPoints(list(points))
        .circle(diameter / 2.0)
        .extrude(height)
    )
    return part.cut(cutter)


def radial_box(width: float, depth: float, height: float, radius: float, angle_deg: float, z0: float = 0.0):
    box = cq.Workplane("XY").box(depth, width, height, centered=(True, True, False))
    box = box.translate((radius, 0.0, z0)).rotate((0, 0, 0), (0, 0, 1), angle_deg)
    return box
