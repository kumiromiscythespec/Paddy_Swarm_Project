"""CadQuery shape measurement, build-envelope, and export validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import cadquery as cq
from cadquery import exporters, importers

from ps_mht_v001.parameters import (
    print_bed_x,
    print_bed_y,
    print_bed_z,
    stl_angular_tolerance,
    stl_linear_tolerance,
)


@dataclass(frozen=True)
class ShapeMetrics:
    """Measured properties of one Workplane or compound."""

    size_x: float
    size_y: float
    size_z: float
    solid_count: int
    volume_mm3: float
    all_solids_valid: bool

    def as_dict(self) -> dict[str, float | int | bool]:
        return asdict(self)


@dataclass(frozen=True)
class StlMetrics:
    """VTK audit result for one exported STL mesh."""

    point_count: int
    triangle_count: int
    size_x: float
    size_y: float
    size_z: float
    connected_component_count: int
    boundary_or_nonmanifold_edge_count: int
    closed_manifold: bool

    def as_dict(self) -> dict[str, float | int | bool]:
        return asdict(self)


def shape_solids(model: cq.Workplane) -> list[cq.Shape]:
    """Return every solid represented by a Workplane or compound."""

    return list(model.solids().vals())


def measure_shape(model: cq.Workplane) -> ShapeMetrics:
    """Measure bounding box, solid count, volume, and CadQuery validity."""

    solids = shape_solids(model)
    if not solids:
        raise ValueError("shape contains no solids")
    box = model.val().BoundingBox()
    return ShapeMetrics(
        size_x=box.xlen,
        size_y=box.ylen,
        size_z=box.zlen,
        solid_count=len(solids),
        volume_mm3=sum(solid.Volume() for solid in solids),
        all_solids_valid=all(solid.isValid() for solid in solids),
    )


def validate_single_printable(
    model: cq.Workplane,
    name: str,
) -> ShapeMetrics:
    """Require one valid positive-volume solid inside the A1 limit."""

    metrics = measure_shape(model)
    if metrics.solid_count != 1:
        raise ValueError(f"{name}: expected one solid, got {metrics.solid_count}")
    if not metrics.all_solids_valid:
        raise ValueError(f"{name}: CadQuery reported an invalid solid")
    if metrics.volume_mm3 <= 0.0:
        raise ValueError(f"{name}: volume must be positive")
    violations = [
        f"{axis}={actual:.3f}>{limit:.3f}"
        for axis, actual, limit in zip(
            ("X", "Y", "Z"),
            (metrics.size_x, metrics.size_y, metrics.size_z),
            (print_bed_x, print_bed_y, print_bed_z),
        )
        if actual > limit + 1.0e-7
    ]
    if violations:
        raise ValueError(
            f"{name}: exceeds Bambu Lab A1 envelope: {', '.join(violations)}"
        )
    return metrics


def validate_multi_solid(
    model: cq.Workplane,
    name: str,
    expected_solid_count: int,
) -> ShapeMetrics:
    """Require an exact number of individually valid, positive-volume solids."""

    metrics = measure_shape(model)
    if metrics.solid_count != expected_solid_count:
        raise ValueError(
            f"{name}: expected {expected_solid_count} solids, "
            f"got {metrics.solid_count}"
        )
    if not metrics.all_solids_valid:
        raise ValueError(f"{name}: one or more CadQuery solids are invalid")
    if metrics.volume_mm3 <= 0.0:
        raise ValueError(f"{name}: volume must be positive")
    return metrics


def validate_printable_set(
    model: cq.Workplane,
    name: str,
    expected_solid_count: int,
) -> ShapeMetrics:
    """Validate a one-plate set containing one or more closed solids."""

    metrics = validate_multi_solid(model, name, expected_solid_count)
    violations = [
        f"{axis}={actual:.3f}>{limit:.3f}"
        for axis, actual, limit in zip(
            ("X", "Y", "Z"),
            (metrics.size_x, metrics.size_y, metrics.size_z),
            (print_bed_x, print_bed_y, print_bed_z),
        )
        if actual > limit + 1.0e-7
    ]
    if violations:
        raise ValueError(
            f"{name}: exceeds Bambu Lab A1 envelope: {', '.join(violations)}"
        )
    return metrics


def export_printable_step(model: cq.Workplane, path: Path) -> Path:
    """Validate and export one printable STEP file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    validate_single_printable(model, path.stem)
    exporters.export(model, str(path), exportType="STEP")
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"empty STEP output: {path}")
    return path


def export_printable_stl(model: cq.Workplane, path: Path) -> Path:
    """Validate and export one printable STL file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    validate_single_printable(model, path.stem)
    exporters.export(
        model,
        str(path),
        exportType="STL",
        tolerance=stl_linear_tolerance,
        angularTolerance=stl_angular_tolerance,
    )
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"empty STL output: {path}")
    return path


def export_printable_set_step(
    model: cq.Workplane,
    path: Path,
    expected_solid_count: int,
) -> Path:
    """Export a validated multi-solid same-plate coupon set as STEP."""

    path.parent.mkdir(parents=True, exist_ok=True)
    validate_printable_set(model, path.stem, expected_solid_count)
    exporters.export(model, str(path), exportType="STEP")
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"empty STEP output: {path}")
    return path


def export_printable_set_stl(
    model: cq.Workplane,
    path: Path,
    expected_solid_count: int,
) -> Path:
    """Export a validated multi-solid same-plate coupon set as STL."""

    path.parent.mkdir(parents=True, exist_ok=True)
    validate_printable_set(model, path.stem, expected_solid_count)
    exporters.export(
        model,
        str(path),
        exportType="STL",
        tolerance=stl_linear_tolerance,
        angularTolerance=stl_angular_tolerance,
    )
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"empty STL output: {path}")
    return path


def export_reference_step(
    model: cq.Workplane,
    path: Path,
    expected_solid_count: int,
) -> Path:
    """Export a non-printable frame or assembly reference STEP."""

    path.parent.mkdir(parents=True, exist_ok=True)
    validate_multi_solid(model, path.stem, expected_solid_count)
    exporters.export(model, str(path), exportType="STEP")
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"empty STEP output: {path}")
    return path


def export_svg_preview(
    model: cq.Workplane,
    path: Path,
    projection: tuple[float, float, float],
) -> Path:
    """Export a vector preview without adding a rendering dependency."""

    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(
        model,
        str(path),
        exportType="SVG",
        opt={
            "width": 1024,
            "height": 1024,
            "marginLeft": 20,
            "marginTop": 20,
            "showAxes": True,
            "projectionDir": projection,
            "strokeWidth": 0.5,
        },
    )
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"empty SVG output: {path}")
    return path


def validate_step_round_trip(
    path: Path,
    expected_solid_count: int,
    printable: bool = False,
) -> ShapeMetrics:
    """Re-import STEP and repeat validity and optional print checks."""

    if not path.is_file():
        raise FileNotFoundError(path)
    imported = importers.importStep(str(path))
    if printable:
        if expected_solid_count != 1:
            raise ValueError("printable STEP round-trip must expect one solid")
        return validate_single_printable(imported, f"{path.stem} STEP round-trip")
    return validate_multi_solid(
        imported,
        f"{path.stem} STEP round-trip",
        expected_solid_count,
    )


def validate_stl_mesh(path: Path) -> StlMetrics:
    """Read an STL with VTK and require a non-empty closed manifold mesh."""

    if not path.is_file():
        raise FileNotFoundError(path)

    import vtk

    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.Update()
    mesh = reader.GetOutput()
    points = mesh.GetNumberOfPoints()
    triangles = mesh.GetNumberOfCells()
    bounds = mesh.GetBounds()
    if points <= 0 or triangles <= 0 or bounds is None:
        raise ValueError(f"{path.name}: STL mesh is empty")

    feature_edges = vtk.vtkFeatureEdges()
    feature_edges.SetInputData(mesh)
    feature_edges.BoundaryEdgesOn()
    feature_edges.NonManifoldEdgesOn()
    feature_edges.FeatureEdgesOff()
    feature_edges.ManifoldEdgesOff()
    feature_edges.Update()
    open_edge_count = feature_edges.GetOutput().GetNumberOfCells()
    if open_edge_count:
        raise ValueError(
            f"{path.name}: STL has {open_edge_count} boundary/non-manifold edges"
        )

    connectivity = vtk.vtkPolyDataConnectivityFilter()
    connectivity.SetInputData(mesh)
    connectivity.SetExtractionModeToAllRegions()
    connectivity.ColorRegionsOff()
    connectivity.Update()
    component_count = connectivity.GetNumberOfExtractedRegions()

    return StlMetrics(
        point_count=points,
        triangle_count=triangles,
        size_x=bounds[1] - bounds[0],
        size_y=bounds[3] - bounds[2],
        size_z=bounds[5] - bounds[4],
        connected_component_count=component_count,
        boundary_or_nonmanifold_edge_count=open_edge_count,
        closed_manifold=True,
    )
