"""Independent CadQuery validation and export helpers for HHD-V001."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cadquery as cq
from cadquery import exporters, importers

from .cq_config import EXPORT, PRINT
from .interfaces import require_positive


@dataclass(frozen=True)
class ShapeMetrics:
    """Measured bounding box, solid count, and total volume."""

    size_x: float
    size_y: float
    size_z: float
    solid_count: int
    volume_mm3: float


def shape_solids(shape: cq.Workplane) -> list[cq.Shape]:
    """Return all solids represented by a workplane or compound."""

    return list(shape.solids().vals())


def measure_shape(shape: cq.Workplane) -> ShapeMetrics:
    """Measure any non-empty shape."""

    solids = shape_solids(shape)
    if not solids:
        raise ValueError("shape contains no solids")
    bounding_box = shape.val().BoundingBox()
    return ShapeMetrics(
        size_x=bounding_box.xlen,
        size_y=bounding_box.ylen,
        size_z=bounding_box.zlen,
        solid_count=len(solids),
        volume_mm3=sum(solid.Volume() for solid in solids),
    )


def validate_single_solid(shape: cq.Workplane, name: str) -> None:
    """Require exactly one valid solid."""

    solids = shape_solids(shape)
    if len(solids) != 1:
        raise ValueError(f"{name}: expected one solid, got {len(solids)}")
    if not solids[0].isValid():
        raise ValueError(f"{name}: CadQuery reported an invalid solid")


def validate_positive_volume(shape: cq.Workplane, name: str) -> None:
    """Require positive shape volume."""

    if measure_shape(shape).volume_mm3 <= 0.0:
        raise ValueError(f"{name}: volume must be positive")


def validate_print_bounds(shape: cq.Workplane, name: str) -> ShapeMetrics:
    """Require one valid solid inside the conservative A1 envelope."""

    validate_single_solid(shape, name)
    validate_positive_volume(shape, name)
    metrics = measure_shape(shape)
    limits = (PRINT.max_x_mm, PRINT.max_y_mm, PRINT.max_z_mm)
    values = (metrics.size_x, metrics.size_y, metrics.size_z)
    violations = [
        f"{axis}={value:.3f}>{limit:.3f}"
        for axis, value, limit in zip(("X", "Y", "Z"), values, limits)
        if value > limit + 1.0e-7
    ]
    if violations:
        raise ValueError(f"{name}: exceeds A1 envelope: {', '.join(violations)}")
    return metrics


def ensure_output_directory(path: str | Path) -> Path:
    """Create and return an output directory."""

    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def export_step(shape: cq.Workplane, output_path: str | Path) -> Path:
    """Validate and export one printable solid as STEP."""

    path = Path(output_path)
    ensure_output_directory(path.parent)
    validate_print_bounds(shape, path.stem)
    exporters.export(shape, str(path), exportType="STEP")
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"STEP export produced no data: {path}")
    return path


def export_stl(
    shape: cq.Workplane,
    output_path: str | Path,
    tolerance: float = EXPORT.linear_tolerance_mm,
    angular_tolerance: float = EXPORT.angular_tolerance_rad,
) -> Path:
    """Validate and export one printable solid as STL."""

    require_positive(
        tolerance=tolerance,
        angular_tolerance=angular_tolerance,
    )
    path = Path(output_path)
    ensure_output_directory(path.parent)
    validate_print_bounds(shape, path.stem)
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


def validate_step_round_trip(
    step_path: str | Path,
    expected_solid_count: int = 1,
    printable: bool = True,
) -> ShapeMetrics:
    """Re-import STEP and validate expected solids and volume."""

    path = Path(step_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    imported = importers.importStep(str(path))
    metrics = measure_shape(imported)
    if metrics.solid_count != expected_solid_count:
        raise ValueError(
            f"{path.name}: expected {expected_solid_count} imported solids, "
            f"got {metrics.solid_count}"
        )
    if metrics.volume_mm3 <= 0.0:
        raise ValueError(f"{path.name}: imported STEP volume must be positive")
    if printable:
        validate_print_bounds(imported, f"{path.stem} STEP round-trip")
    elif any(not solid.isValid() for solid in shape_solids(imported)):
        raise ValueError(f"{path.name}: imported preview contains invalid solids")
    return metrics


def export_preview_step(
    shape: cq.Workplane,
    output_path: str | Path,
    expected_solid_count: int,
) -> Path:
    """Export a non-printable multi-solid preview and validate re-import."""

    path = Path(output_path)
    ensure_output_directory(path.parent)
    metrics = measure_shape(shape)
    if metrics.solid_count != expected_solid_count:
        raise ValueError(
            f"{path.stem}: expected {expected_solid_count} preview solids, "
            f"got {metrics.solid_count}"
        )
    exporters.export(shape, str(path), exportType="STEP")
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"preview STEP export produced no data: {path}")
    validate_step_round_trip(path, expected_solid_count, printable=False)
    return path


def relative_output_path(path: str | Path, output_root: str | Path) -> str:
    """Return an output-root-relative POSIX path."""

    resolved_path = Path(path).resolve()
    resolved_root = Path(output_root).resolve()
    try:
        return resolved_path.relative_to(resolved_root).as_posix()
    except ValueError as exc:
        raise ValueError(f"path is outside output root: {resolved_path}") from exc


def remove_known_outputs(
    output_root: str | Path,
    known_relative_paths: Iterable[str],
) -> None:
    """Delete only explicitly listed files contained by the output root."""

    root = Path(output_root).resolve()
    for relative_path in known_relative_paths:
        candidate = (root / relative_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"refusing out-of-root removal: {candidate}") from exc
        if candidate.is_file():
            candidate.unlink()
