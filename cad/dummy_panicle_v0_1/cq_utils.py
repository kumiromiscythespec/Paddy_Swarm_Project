"""CadQuery validation, bounding-box, and export helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cadquery as cq
from cadquery import exporters, importers

from .cq_config import EXPORT, PRINT


@dataclass(frozen=True)
class ShapeMetrics:
    """Measured shape properties used by tests and reports."""

    size_x: float
    size_y: float
    size_z: float
    solid_count: int
    volume: float


def require_positive(**dimensions: float) -> None:
    """Validate that every named dimension is finite and strictly positive."""

    for name, value in dimensions.items():
        if (
            not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0.0
        ):
            raise ValueError(f"{name} must be finite and positive, got {value!r}")


def require_minimum(value: float, minimum: float, name: str) -> None:
    """Validate a minimum dimension."""

    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum:.3f} mm, got {value:.3f} mm")


def require_clearance(opening: float, insert: float, name: str) -> None:
    """Validate a positive diametral or linear clearance."""

    if opening <= insert:
        raise ValueError(
            f"{name} requires opening > insert, got {opening:.3f} <= {insert:.3f} mm"
        )


def _solids(shape: cq.Workplane) -> list[cq.Shape]:
    """Return all solids represented by a Workplane."""

    return list(shape.solids().vals())


def measure_shape(shape: cq.Workplane) -> ShapeMetrics:
    """Measure a non-empty CadQuery shape."""

    solids = _solids(shape)
    if not solids:
        raise ValueError("shape contains no solids")
    bounding_box = shape.val().BoundingBox()
    return ShapeMetrics(
        size_x=bounding_box.xlen,
        size_y=bounding_box.ylen,
        size_z=bounding_box.zlen,
        solid_count=len(solids),
        volume=sum(solid.Volume() for solid in solids),
    )


def validate_printable_shape(shape: cq.Workplane, part_name: str) -> ShapeMetrics:
    """Validate solid validity, volume, and the conservative A1 build envelope."""

    metrics = measure_shape(shape)
    invalid = [solid for solid in _solids(shape) if not solid.isValid()]
    if invalid:
        raise ValueError(f"{part_name}: CadQuery reported an invalid solid")
    if metrics.solid_count != 1:
        raise ValueError(f"{part_name}: expected one solid, got {metrics.solid_count}")
    if metrics.volume <= 0.0:
        raise ValueError(f"{part_name}: volume must be positive")
    limits = (PRINT.max_x, PRINT.max_y, PRINT.max_z)
    measured = (metrics.size_x, metrics.size_y, metrics.size_z)
    axes = ("X", "Y", "Z")
    violations = [
        f"{axis}={actual:.3f}>{limit:.3f}"
        for axis, actual, limit in zip(axes, measured, limits)
        if actual > limit + 1.0e-7
    ]
    if violations:
        raise ValueError(f"{part_name}: exceeds A1 safe envelope: {', '.join(violations)}")
    return metrics


def export_step(shape: cq.Workplane, output_path: str | Path) -> Path:
    """Export a validated shape as STEP, creating parent directories."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    validate_printable_shape(shape, path.stem)
    exporters.export(shape, str(path), exportType="STEP")
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"STEP export produced no data: {path}")
    return path


def export_stl(
    shape: cq.Workplane,
    output_path: str | Path,
    tolerance: float = EXPORT.tolerance,
    angular_tolerance: float = EXPORT.angular_tolerance,
) -> Path:
    """Export a validated shape as STL, creating parent directories."""

    require_positive(tolerance=tolerance, angular_tolerance=angular_tolerance)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    validate_printable_shape(shape, path.stem)
    exporters.export(
        shape,
        str(path),
        exportType="STL",
        tolerance=tolerance,
        angularTolerance=angular_tolerance,
    )
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"STL export produced no data: {path}")
    return path


def validate_step_round_trip(step_path: str | Path) -> ShapeMetrics:
    """Re-import a STEP file and validate its geometry."""

    path = Path(step_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    imported = importers.importStep(str(path))
    return validate_printable_shape(imported, f"{path.stem} STEP round-trip")


def validate_pairwise_wall(
    centers: Iterable[float],
    widths: Iterable[float],
    minimum_wall: float,
    name: str,
) -> None:
    """Validate edge-to-edge wall between ordered openings."""

    pairs = sorted(zip(centers, widths), key=lambda item: item[0])
    for (left_center, left_width), (right_center, right_width) in zip(pairs, pairs[1:]):
        wall = right_center - left_center - 0.5 * (left_width + right_width)
        require_minimum(wall, minimum_wall, name)
