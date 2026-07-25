"""Panicle-head-only STEP previews; these compounds are not printable parts."""

from __future__ import annotations

import math
from itertools import combinations
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq
from cadquery import exporters, importers

from ..cq_utils import ShapeMetrics, measure_shape
from ..interfaces import PANICLE_HEAD
from ..panicle_branch import PanicleBranchParams, build as build_branch
from ..panicle_hub import (
    PanicleHubParams,
    params_for_preset,
    stem_axis,
    build as build_hub,
)
from ..panicle_weight_cap import (
    PanicleWeightCapParams,
    build as build_weight_cap,
)


@dataclass(frozen=True)
class PanicleAssemblyPreview:
    """One validated, non-printable panicle-only preview compound."""

    preset: str
    shape: cq.Workplane
    metrics: ShapeMetrics
    branch_count: int
    branch_angles_degrees: tuple[float, ...]
    tab_insertion_depth: float
    component_solid_count: int
    max_panel_overlap_volume_mm3: float
    printable: bool = False


def _all_solids(shape: cq.Workplane) -> list[cq.Shape]:
    """Return all solids held by a workplane or compound."""

    return list(shape.solids().vals())


def _compound(shapes: list[cq.Workplane]) -> cq.Workplane:
    """Create a non-fused compound while retaining all assembly components."""

    solids: list[cq.Shape] = []
    for shape in shapes:
        solids.extend(_all_solids(shape))
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def _panel_at_slot(
    panel: cq.Workplane,
    hub_params: PanicleHubParams,
    angle_degrees: float,
    panel_thickness: float,
) -> cq.Workplane:
    """Place a flat panel tab into one vertical top-entry hub slot."""

    radial_center = hub_params.slot_center_radius - 0.5 * panel_thickness
    slot_bottom_z = hub_params.height - hub_params.slot_depth
    return (
        panel.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
        .rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            angle_degrees + 90.0,
        )
        .translate(
            (
                radial_center * math.cos(math.radians(angle_degrees)),
                radial_center * math.sin(math.radians(angle_degrees)),
                slot_bottom_z,
            )
        )
    )


def _rotation_only_point(
    point: tuple[float, float, float],
    axis: tuple[float, float, float],
    angle_degrees: float,
) -> tuple[float, float, float]:
    """Rotate a point by Rodrigues' formula."""

    angle = math.radians(angle_degrees)
    x, y, z = point
    ax, ay, az = axis
    dot = ax * x + ay * y + az * z
    cross = (
        ay * z - az * y,
        az * x - ax * z,
        ax * y - ay * x,
    )
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return (
        x * cosine + cross[0] * sine + ax * dot * (1.0 - cosine),
        y * cosine + cross[1] * sine + ay * dot * (1.0 - cosine),
        z * cosine + cross[2] * sine + az * dot * (1.0 - cosine),
    )


def _align_head(
    shape: cq.Workplane,
    hub_params: PanicleHubParams,
) -> cq.Workplane:
    """Apply the fixed droop and put the stem-hole entry at the origin."""

    if hub_params.droop_angle == 0.0:
        return shape
    azimuth = math.radians(hub_params.droop_azimuth_degrees)
    tangent_axis = (-math.sin(azimuth), math.cos(azimuth), 0.0)
    start, _direction = stem_axis(hub_params)
    rotated_start = _rotation_only_point(
        start,
        tangent_axis,
        -hub_params.droop_angle,
    )
    return shape.rotate(
        (0.0, 0.0, 0.0),
        tangent_axis,
        -hub_params.droop_angle,
    ).translate(tuple(-value for value in rotated_start))


def validate_preview(preview: PanicleAssemblyPreview) -> None:
    """Validate the required assembly count, spacing, and overall envelope."""

    if preview.printable:
        raise ValueError("panicle preview must remain non-printable")
    if preview.branch_count != 4:
        raise ValueError("panicle preview requires exactly four branch panels")
    if preview.branch_angles_degrees != (0.0, 90.0, 180.0, 270.0):
        raise ValueError("panicle preview panels must be spaced at 90 degrees")
    if preview.tab_insertion_depth != 12.0:
        raise ValueError("panicle preview requires 12 mm tab insertion")
    if preview.component_solid_count != 7:
        raise ValueError("panicle preview requires 7 separate component solids")
    if preview.max_panel_overlap_volume_mm3 > 1.0e-7:
        raise ValueError(
            "panicle preview contains unintended panel-to-panel overlap: "
            f"{preview.max_panel_overlap_volume_mm3:.6f} mm3"
        )
    if not 180.0 <= preview.metrics.size_z <= 220.0:
        raise ValueError(
            f"panicle preview length {preview.metrics.size_z:.3f} is outside 180-220 mm"
        )
    maximum_width = max(preview.metrics.size_x, preview.metrics.size_y)
    if not 80.0 <= maximum_width <= 110.0:
        raise ValueError(
            f"panicle preview width {maximum_width:.3f} is outside 80-110 mm"
        )
    invalid = [solid for solid in _all_solids(preview.shape) if not solid.isValid()]
    if invalid:
        raise ValueError("panicle preview contains invalid solids")


def build_preview(preset: str) -> PanicleAssemblyPreview:
    """Build upright or droop20 DR-H01 x4 + DR-H02 + DR-H03 + simple stem."""

    hub_params = params_for_preset(preset)
    branch_params = PanicleBranchParams()
    cap_params = PanicleWeightCapParams(
        pocket_diameter=hub_params.weight_pocket_diameter
    )
    panel = build_branch(branch_params)
    branch_angles = (0.0, 90.0, 180.0, 270.0)
    panels = [
        _panel_at_slot(
            panel,
            hub_params,
            angle,
            branch_params.tab_thickness,
        )
        for angle in branch_angles
    ]
    panel_overlap_volumes: list[float] = []
    for left, right in combinations(panels, 2):
        intersection = left.intersect(right)
        panel_overlap_volumes.append(
            sum(solid.Volume() for solid in _all_solids(intersection))
        )
    hub = build_hub(hub_params)
    cap = (
        build_weight_cap(cap_params)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0)
        .translate(
            (
                0.0,
                0.0,
                hub_params.height + cap_params.flange_thickness,
            )
        )
    )
    head = _compound([hub, cap, *panels])
    head = _align_head(head, hub_params)
    stem = (
        cq.Workplane("XY")
        .circle(0.5 * hub_params.stem_od)
        .extrude(hub_params.stem_insert_depth + 8.0)
        .translate((0.0, 0.0, -8.0))
    )
    assembly = _compound([head, stem])
    metrics = measure_shape(assembly)
    preview = PanicleAssemblyPreview(
        preset=preset,
        shape=assembly,
        metrics=metrics,
        branch_count=PANICLE_HEAD.branch_panel_count,
        branch_angles_degrees=branch_angles,
        tab_insertion_depth=hub_params.slot_depth,
        component_solid_count=len(_all_solids(assembly)),
        max_panel_overlap_volume_mm3=max(panel_overlap_volumes, default=0.0),
    )
    validate_preview(preview)
    return preview


def export_preview_step(
    preview: PanicleAssemblyPreview,
    output_path: str | Path,
) -> Path:
    """Export and re-import a non-printable preview STEP compound."""

    validate_preview(preview)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(preview.shape, str(path), exportType="STEP")
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"preview STEP export produced no data: {path}")
    imported = importers.importStep(str(path))
    imported_metrics = measure_shape(imported)
    if imported_metrics.solid_count != preview.component_solid_count:
        raise ValueError(
            f"preview STEP round-trip changed solid count: "
            f"{preview.component_solid_count} -> {imported_metrics.solid_count}"
        )
    return path
