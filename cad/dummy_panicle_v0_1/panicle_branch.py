"""DR-H01 flat TPU panicle branch panel."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path

import cadquery as cq

from .cq_config import PRINT
from .cq_utils import (
    export_step as export_shape_step,
    export_stl as export_shape_stl,
    require_minimum,
    require_positive,
    validate_printable_shape,
)
from .interfaces import PANICLE_HEAD, PANICLE_TAB


@dataclass(frozen=True)
class PanicleBranchParams:
    """DR-H01 deterministic 2.5D panel dimensions in mm."""

    total_length: float = 195.0
    max_half_width: float = 42.0
    thickness: float = 1.0
    tab_width: float = PANICLE_TAB.tab_width
    tab_thickness: float = PANICLE_TAB.tab_thickness
    tab_length: float = PANICLE_TAB.tab_length
    neck_length: float = 12.0
    neck_width: float = 1.8
    neck_thickness: float = 0.8
    rachis_width_base: float = 2.2
    rachis_width_tip: float = 1.2
    lateral_branch_count: int = 10
    branch_root_width: float = 1.2
    branch_tip_width: float = 0.8
    branch_root_fillet: float = 1.0
    grain_count: int = 14
    grain_length: float = 7.0
    grain_width: float = 3.0
    grain_thickness: float = 2.0
    grain_connection_width: float = 1.0
    grain_min_spacing: float = 0.8
    root_fillet: float = 1.5
    branch_positions_y: tuple[float, ...] = (
        42.0,
        55.0,
        68.0,
        82.0,
        96.0,
        111.0,
        126.0,
        142.0,
        158.0,
        174.0,
    )
    branch_lengths: tuple[float, ...] = (
        36.0,
        34.0,
        31.0,
        29.0,
        26.0,
        24.0,
        21.0,
        18.0,
        15.0,
        11.0,
    )
    branch_rises: tuple[float, ...] = (
        11.0,
        10.0,
        10.0,
        9.0,
        9.0,
        8.0,
        7.0,
        6.0,
        5.0,
        4.0,
    )
    grain_angles_degrees: tuple[float, ...] = (15.0, 22.5, 30.0)
    calibration_status: str = PANICLE_HEAD.calibration_status


@dataclass(frozen=True)
class BranchPlacement:
    """One lateral branch centerline in the panel XY plane."""

    start: tuple[float, float]
    end: tuple[float, float]
    side: int


@dataclass(frozen=True)
class GrainPlacement:
    """One deterministic grain center and in-plane orientation."""

    center: tuple[float, float]
    angle_degrees: float
    branch_index: int


def branch_placements(params: PanicleBranchParams) -> tuple[BranchPlacement, ...]:
    """Return deterministic alternating branch centerlines."""

    placements: list[BranchPlacement] = []
    for index in range(params.lateral_branch_count):
        side = 1 if index % 2 == 0 else -1
        y = params.branch_positions_y[index]
        placements.append(
            BranchPlacement(
                start=(0.0, y),
                end=(
                    side * params.branch_lengths[index],
                    y + params.branch_rises[index],
                ),
                side=side,
            )
        )
    return tuple(placements)


def grain_placements(params: PanicleBranchParams) -> tuple[GrainPlacement, ...]:
    """Return exactly ``grain_count`` deterministic grain placements."""

    branches = branch_placements(params)
    fractions = [1.0] * min(params.grain_count, len(branches))
    branch_indices = list(range(len(fractions)))
    remaining = params.grain_count - len(fractions)
    for index in range(remaining):
        branch_indices.append(index % len(branches))
        fractions.append(0.65)

    placements: list[GrainPlacement] = []
    for grain_index, (branch_index, fraction) in enumerate(zip(branch_indices, fractions)):
        branch = branches[branch_index]
        dx = branch.end[0] - branch.start[0]
        dy = branch.end[1] - branch.start[1]
        length = math.hypot(dx, dy)
        unit_x = dx / length
        unit_y = dy / length
        attach_x = branch.start[0] + fraction * dx
        attach_y = branch.start[1] + fraction * dy
        center = (
            attach_x + 1.5 * unit_x,
            attach_y + 1.5 * unit_y,
        )
        base_angle = math.degrees(math.atan2(dy, dx))
        angle_offset = params.grain_angles_degrees[grain_index % 3]
        placements.append(
            GrainPlacement(
                center=center,
                angle_degrees=base_angle + branch.side * angle_offset,
                branch_index=branch_index,
            )
        )
    return tuple(placements)


def validate_params(params: PanicleBranchParams) -> None:
    """Validate DR-H01 dimensions, interface values, counts, and spacing."""

    require_positive(
        total_length=params.total_length,
        max_half_width=params.max_half_width,
        thickness=params.thickness,
        tab_width=params.tab_width,
        tab_thickness=params.tab_thickness,
        tab_length=params.tab_length,
        neck_length=params.neck_length,
        neck_width=params.neck_width,
        neck_thickness=params.neck_thickness,
        rachis_width_base=params.rachis_width_base,
        rachis_width_tip=params.rachis_width_tip,
        branch_root_width=params.branch_root_width,
        branch_tip_width=params.branch_tip_width,
        branch_root_fillet=params.branch_root_fillet,
        grain_length=params.grain_length,
        grain_width=params.grain_width,
        grain_thickness=params.grain_thickness,
        grain_connection_width=params.grain_connection_width,
        grain_min_spacing=params.grain_min_spacing,
        root_fillet=params.root_fillet,
    )
    if params.total_length > PRINT.max_z:
        raise ValueError("DR-H01 total length exceeds the 220 mm A1 Z limit")
    if not 175.0 <= params.total_length <= 215.0:
        raise ValueError("DR-H01 total length must remain in the 175-215 mm range")
    if not 35.0 <= params.max_half_width <= 50.0:
        raise ValueError("DR-H01 max half width must remain in the 35-50 mm range")
    require_minimum(params.thickness, PRINT.tpu_min_wall, "DR-H01 panel thickness")
    require_minimum(params.neck_width, 1.4, "DR-H01 neck width")
    require_minimum(params.neck_thickness, PRINT.tpu_min_wall, "DR-H01 neck thickness")
    require_minimum(params.rachis_width_tip, PRINT.tpu_min_wall, "DR-H01 rachis tip")
    require_minimum(params.branch_root_width, PRINT.tpu_min_wall, "DR-H01 branch root")
    require_minimum(params.branch_tip_width, PRINT.tpu_min_wall, "DR-H01 branch tip")
    require_minimum(params.grain_width, 2.5, "DR-H01 grain width")
    require_minimum(
        params.grain_connection_width,
        1.0,
        "DR-H01 grain connection width",
    )
    if params.tab_width != PANICLE_TAB.tab_width:
        raise ValueError("DR-H01 tab width must equal PANICLE-TAB-V001")
    if params.tab_thickness != PANICLE_TAB.tab_thickness:
        raise ValueError("DR-H01 tab thickness must equal PANICLE-TAB-V001")
    if params.tab_length < PANICLE_TAB.insertion_depth:
        raise ValueError("DR-H01 tab is shorter than the slot insertion depth")
    if params.lateral_branch_count <= 0:
        raise ValueError("DR-H01 branch count must be positive")
    if params.grain_count <= 0:
        raise ValueError("DR-H01 grain count must be positive")
    if params.lateral_branch_count > min(
        len(params.branch_positions_y),
        len(params.branch_lengths),
        len(params.branch_rises),
    ):
        raise ValueError("DR-H01 branch layout has insufficient deterministic entries")

    grains = grain_placements(params)
    for left_index, left in enumerate(grains):
        for right in grains[left_index + 1 :]:
            center_distance = math.dist(left.center, right.center)
            conservative_gap = center_distance - params.grain_length
            if conservative_gap < params.grain_min_spacing:
                raise ValueError(
                    "DR-H01 grain spacing is below the conservative 0.8 mm limit"
                )


def _tapered_bar(
    start: tuple[float, float],
    end: tuple[float, float],
    start_width: float,
    end_width: float,
    height: float,
) -> cq.Workplane:
    """Create one tapered XY bar extruded in +Z."""

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    normal_x = -dy / length
    normal_y = dx / length
    points = (
        (
            start[0] + 0.5 * start_width * normal_x,
            start[1] + 0.5 * start_width * normal_y,
        ),
        (
            end[0] + 0.5 * end_width * normal_x,
            end[1] + 0.5 * end_width * normal_y,
        ),
        (
            end[0] - 0.5 * end_width * normal_x,
            end[1] - 0.5 * end_width * normal_y,
        ),
        (
            start[0] - 0.5 * start_width * normal_x,
            start[1] - 0.5 * start_width * normal_y,
        ),
    )
    return cq.Workplane("XY").polyline(points).close().extrude(height)


def _capsule(params: PanicleBranchParams) -> cq.Workplane:
    """Create one simple printable capsule-shaped grain."""

    straight_length = params.grain_length - params.grain_width
    body = cq.Workplane("XY").box(
        straight_length,
        params.grain_width,
        params.grain_thickness,
        centered=(True, True, False),
    )
    for x in (-0.5 * straight_length, 0.5 * straight_length):
        end = (
            cq.Workplane("XY")
            .center(x, 0.0)
            .circle(0.5 * params.grain_width)
            .extrude(params.grain_thickness)
        )
        body = body.union(end)
    return body


def build(params: PanicleBranchParams = PanicleBranchParams()) -> cq.Workplane:
    """Build the complete 10-branch, 14-grain DR-H01 TPU panel."""

    validate_params(params)
    tab = (
        cq.Workplane("XY")
        .box(
            params.tab_width,
            params.tab_length,
            params.tab_thickness,
            centered=(True, False, False),
        )
    )
    transition = (
        cq.Workplane("XY")
        .polyline(
            (
                (-0.5 * params.tab_width, params.tab_length - 2.0),
                (-0.5 * params.neck_width, params.tab_length + 2.0),
                (0.5 * params.neck_width, params.tab_length + 2.0),
                (0.5 * params.tab_width, params.tab_length - 2.0),
            )
        )
        .close()
        .extrude(params.neck_thickness)
    )
    neck = (
        cq.Workplane("XY")
        .box(
            params.neck_width,
            params.neck_length + 0.4,
            params.neck_thickness,
            centered=(True, False, False),
        )
        .translate((0.0, params.tab_length - 0.2, 0.0))
    )
    neck_root = (
        cq.Workplane("XY")
        .center(0.0, params.tab_length)
        .circle(params.root_fillet)
        .extrude(params.neck_thickness)
    )
    rachis_start = params.tab_length + params.neck_length - 0.2
    rachis = (
        cq.Workplane("XY")
        .polyline(
            (
                (-0.5 * params.rachis_width_base, rachis_start),
                (-0.5 * params.rachis_width_tip, params.total_length),
                (0.5 * params.rachis_width_tip, params.total_length),
                (0.5 * params.rachis_width_base, rachis_start),
            )
        )
        .close()
        .extrude(params.thickness)
    )
    part = tab.union(transition).union(neck).union(neck_root).union(rachis)

    branches = branch_placements(params)
    for branch in branches:
        bar = _tapered_bar(
            branch.start,
            branch.end,
            params.branch_root_width,
            params.branch_tip_width,
            params.thickness,
        )
        root_pad = (
            cq.Workplane("XY")
            .center(*branch.start)
            .circle(params.branch_root_fillet)
            .extrude(params.thickness)
        )
        part = part.union(bar).union(root_pad)

    grain_template = _capsule(params)
    grain_positions = grain_placements(params)
    for grain in grain_positions:
        branch = branches[grain.branch_index]
        dx = branch.end[0] - branch.start[0]
        dy = branch.end[1] - branch.start[1]
        length = math.hypot(dx, dy)
        unit_x = dx / length
        unit_y = dy / length
        attach = (
            grain.center[0] - 1.5 * unit_x,
            grain.center[1] - 1.5 * unit_y,
        )
        connector = (
            cq.Workplane("XY")
            .center(*attach)
            .circle(0.5 * params.grain_connection_width)
            .extrude(params.thickness)
        )
        shaped_grain = grain_template.rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            grain.angle_degrees,
        ).translate((grain.center[0], grain.center[1], 0.0))
        part = part.union(connector).union(shaped_grain)

    metrics = validate_printable_shape(part, "DR-H01 panicle branch TPU")
    bounding_box = part.val().BoundingBox()
    measured_half_width = max(abs(bounding_box.xmin), abs(bounding_box.xmax))
    if measured_half_width > params.max_half_width + 1.0e-6:
        raise ValueError(
            f"DR-H01 measured half width {measured_half_width:.3f} exceeds "
            f"{params.max_half_width:.3f} mm"
        )
    if not 175.0 <= metrics.size_y <= 215.0:
        raise ValueError("DR-H01 built length is outside the 175-215 mm range")
    return part


def build_minimal() -> cq.Workplane:
    """Build the Phase-2 two-branch/two-grain connectivity proof."""

    return build(
        replace(
            PanicleBranchParams(),
            lateral_branch_count=2,
            grain_count=2,
        )
    )


def export_step(params: PanicleBranchParams, output_path: str | Path) -> Path:
    """Build and export DR-H01 as STEP."""

    return export_shape_step(build(params), output_path)


def export_stl(
    params: PanicleBranchParams,
    output_path: str | Path,
    tolerance: float = 0.05,
    angular_tolerance: float = 0.1,
) -> Path:
    """Build and export DR-H01 as STL."""

    return export_shape_stl(build(params), output_path, tolerance, angular_tolerance)
