"""Standard 24-fixed-root non-printable HHD-V001 preview."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, replace

import cadquery as cq

from ..cq_utils import ShapeMetrics, measure_shape, shape_solids
from ..parameters import BASE_SOCKET, HEIGHTS_MM, ROOT_BASE, ROOT_MOUNT
from ..presets.layout_standard_v001 import (
    LAYOUT_STANDARD_V001,
    LayoutEntry,
    entries_for_module,
)
from ..root_base import build as build_base
from ..root_base_mount import build as build_mount
from ..stem_socket import (
    axis_vector,
    build as build_socket,
    params_for_angle,
    receiver_entry_point,
)


@dataclass(frozen=True)
class StandardAssemblyPreview:
    """Validated metadata and compound for the fixed-root preview."""

    shape: cq.Workplane
    metrics: ShapeMetrics
    socket_ids: tuple[str, ...]
    socket_count: int
    virtual_stem_count: int
    component_solid_count: int
    height_counts: dict[str, int]
    tilt_counts: dict[float, int]
    direction_counts: dict[float, int]
    top_z_values: tuple[float, ...]
    minimum_socket_clearance_mm: float
    projected_stem_crossing_count: int
    printable: bool = False


def _compound(shapes: list[cq.Workplane]) -> cq.Workplane:
    """Create a non-fused compound retaining independent components."""

    solids: list[cq.Shape] = []
    for shape in shapes:
        solids.extend(shape_solids(shape))
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def _socket_params(entry: LayoutEntry):
    """Return fixed-angle parameters rotated to the entry's index direction."""

    return replace(
        params_for_angle(entry.tilt_angle_deg),
        tilt_direction_deg=entry.tilt_direction_deg,
    )


def _socket_bottom_z(base_bottom_z: float) -> float:
    """Return socket-shank bottom for a base placed at base_bottom_z."""

    return (
        base_bottom_z
        + ROOT_BASE.module_thickness
        - BASE_SOCKET.insertion_depth
    )


def placed_socket(
    entry: LayoutEntry,
    base_bottom_z: float,
) -> cq.Workplane:
    """Build and place one independently indexed socket."""

    params = _socket_params(entry)
    return build_socket(params).translate(
        (
            entry.x_mm,
            entry.y_mm,
            _socket_bottom_z(base_bottom_z),
        )
    )


def virtual_stem_start(
    entry: LayoutEntry,
    base_bottom_z: float,
) -> tuple[float, float, float]:
    """Return the open socket entry in assembly coordinates."""

    local = receiver_entry_point(_socket_params(entry))
    socket_bottom = _socket_bottom_z(base_bottom_z)
    return (
        entry.x_mm + local[0],
        entry.y_mm + local[1],
        socket_bottom + local[2],
    )


def virtual_stem_end(
    entry: LayoutEntry,
    base_bottom_z: float,
) -> tuple[float, float, float]:
    """Return virtual commercial-stem endpoint."""

    start = virtual_stem_start(entry, base_bottom_z)
    direction = axis_vector(_socket_params(entry))
    length = HEIGHTS_MM[entry.height_class]
    return tuple(
        start[index] + length * direction[index]
        for index in range(3)
    )


def build_virtual_stem(
    entry: LayoutEntry,
    base_bottom_z: float,
) -> cq.Workplane:
    """Build one simple non-printable 4 mm virtual commercial stem."""

    start = virtual_stem_start(entry, base_bottom_z)
    direction = axis_vector(_socket_params(entry))
    solid = cq.Solid.makeCylinder(
        2.0,
        HEIGHTS_MM[entry.height_class],
        cq.Vector(*start),
        cq.Vector(*direction),
    )
    return cq.Workplane("XY").newObject([solid])


def _segment_distance(
    first_start: tuple[float, float, float],
    first_end: tuple[float, float, float],
    second_start: tuple[float, float, float],
    second_end: tuple[float, float, float],
) -> float:
    """Return shortest distance between two finite 3D line segments."""

    small = 1.0e-12
    u = tuple(first_end[index] - first_start[index] for index in range(3))
    v = tuple(second_end[index] - second_start[index] for index in range(3))
    w = tuple(first_start[index] - second_start[index] for index in range(3))
    a = sum(value * value for value in u)
    b = sum(u[index] * v[index] for index in range(3))
    c = sum(value * value for value in v)
    d = sum(u[index] * w[index] for index in range(3))
    e = sum(v[index] * w[index] for index in range(3))
    denominator = a * c - b * b
    numerator_s = denominator
    denominator_s = denominator
    numerator_t = denominator
    denominator_t = denominator
    if denominator < small:
        numerator_s = 0.0
        denominator_s = 1.0
        numerator_t = e
        denominator_t = c
    else:
        numerator_s = b * e - c * d
        numerator_t = a * e - b * d
        if numerator_s < 0.0:
            numerator_s = 0.0
            numerator_t = e
            denominator_t = c
        elif numerator_s > denominator_s:
            numerator_s = denominator_s
            numerator_t = e + b
            denominator_t = c
    if numerator_t < 0.0:
        numerator_t = 0.0
        if -d < 0.0:
            numerator_s = 0.0
        elif -d > a:
            numerator_s = denominator_s
        else:
            numerator_s = -d
            denominator_s = a
    elif numerator_t > denominator_t:
        numerator_t = denominator_t
        if -d + b < 0.0:
            numerator_s = 0.0
        elif -d + b > a:
            numerator_s = denominator_s
        else:
            numerator_s = -d + b
            denominator_s = a
    sc = 0.0 if abs(numerator_s) < small else numerator_s / denominator_s
    tc = 0.0 if abs(numerator_t) < small else numerator_t / denominator_t
    delta = tuple(w[index] + sc * u[index] - tc * v[index] for index in range(3))
    return math.sqrt(sum(value * value for value in delta))


def minimum_socket_clearance(
    entries: tuple[LayoutEntry, ...] = LAYOUT_STANDARD_V001,
    base_bottom_z: float = ROOT_MOUNT.thickness,
) -> float:
    """Return conservative minimum outer-surface clearance between sockets."""

    tube_radius = 0.5 * params_for_angle(0.0).outer_tube_diameter
    index_corner_radius = (
        0.5 * BASE_SOCKET.index_af / math.cos(math.pi / 8.0)
    )
    clearances: list[float] = []
    base_top_z = base_bottom_z + ROOT_BASE.module_thickness
    for index, left in enumerate(entries):
        for right in entries[index + 1 :]:
            center_distance = math.hypot(
                left.x_mm - right.x_mm,
                left.y_mm - right.y_mm,
            )
            clearances.append(center_distance - 2.0 * index_corner_radius)
            left_direction = axis_vector(_socket_params(left))
            right_direction = axis_vector(_socket_params(right))
            left_start = (left.x_mm, left.y_mm, base_top_z)
            right_start = (right.x_mm, right.y_mm, base_top_z)
            axis_length = params_for_angle(0.0).outer_axis_length
            left_end = tuple(
                left_start[axis] + axis_length * left_direction[axis]
                for axis in range(3)
            )
            right_end = tuple(
                right_start[axis] + axis_length * right_direction[axis]
                for axis in range(3)
            )
            clearances.append(
                _segment_distance(
                    left_start,
                    left_end,
                    right_start,
                    right_end,
                )
                - 2.0 * tube_radius
            )
    return min(clearances)


def _orientation(
    first: tuple[float, float],
    second: tuple[float, float],
    third: tuple[float, float],
) -> float:
    """Return signed 2D turn."""

    return (
        (second[0] - first[0]) * (third[1] - first[1])
        - (second[1] - first[1]) * (third[0] - first[0])
    )


def _strict_projected_crossing(
    a_start: tuple[float, float, float],
    a_end: tuple[float, float, float],
    b_start: tuple[float, float, float],
    b_end: tuple[float, float, float],
) -> bool:
    """Return whether XY projections cross away from endpoints."""

    p1, p2 = a_start[:2], a_end[:2]
    q1, q2 = b_start[:2], b_end[:2]
    if math.dist(p1, p2) < 1.0e-6 or math.dist(q1, q2) < 1.0e-6:
        return False
    o1 = _orientation(p1, p2, q1)
    o2 = _orientation(p1, p2, q2)
    o3 = _orientation(q1, q2, p1)
    o4 = _orientation(q1, q2, p2)
    return o1 * o2 < 0.0 and o3 * o4 < 0.0


def projected_stem_crossings(
    entries: tuple[LayoutEntry, ...] = LAYOUT_STANDARD_V001,
    base_bottom_z: float = ROOT_MOUNT.thickness,
) -> tuple[tuple[str, str], ...]:
    """Return pairs whose long-stem XY projections cross."""

    pairs: list[tuple[str, str]] = []
    for index, left in enumerate(entries):
        for right in entries[index + 1 :]:
            if _strict_projected_crossing(
                virtual_stem_start(left, base_bottom_z),
                virtual_stem_end(left, base_bottom_z),
                virtual_stem_start(right, base_bottom_z),
                virtual_stem_end(right, base_bottom_z),
            ):
                pairs.append((left.socket_id, right.socket_id))
    return tuple(pairs)


def build_six_stem_preview(module: str = "A") -> StandardAssemblyPreview:
    """Build the Phase-3 one-module/six-stem connectivity preview."""

    entries = entries_for_module(module)
    base_bottom_z = 0.0
    shapes: list[cq.Workplane] = [build_base(module)]
    shapes.extend(placed_socket(entry, base_bottom_z) for entry in entries)
    shapes.extend(build_virtual_stem(entry, base_bottom_z) for entry in entries)
    compound = _compound(shapes)
    metrics = measure_shape(compound)
    return StandardAssemblyPreview(
        shape=compound,
        metrics=metrics,
        socket_ids=tuple(entry.socket_id for entry in entries),
        socket_count=6,
        virtual_stem_count=6,
        component_solid_count=len(shape_solids(compound)),
        height_counts=dict(Counter(entry.height_class for entry in entries)),
        tilt_counts=dict(Counter(entry.tilt_angle_deg for entry in entries)),
        direction_counts=dict(Counter(entry.tilt_direction_deg for entry in entries)),
        top_z_values=tuple(
            virtual_stem_end(entry, base_bottom_z)[2]
            for entry in entries
        ),
        minimum_socket_clearance_mm=minimum_socket_clearance(
            entries,
            base_bottom_z,
        ),
        projected_stem_crossing_count=len(
            projected_stem_crossings(entries, base_bottom_z)
        ),
    )


def validate_standard_preview(preview: StandardAssemblyPreview) -> None:
    """Validate counts, independence, fixed-root distribution, and clearance."""

    if preview.printable:
        raise ValueError("standard HHD preview must remain non-printable")
    if preview.socket_count != 24 or preview.virtual_stem_count != 24:
        raise ValueError("standard HHD preview requires 24 sockets and 24 stems")
    if len(set(preview.socket_ids)) != 24:
        raise ValueError("standard HHD preview requires 24 unique socket IDs")
    if preview.component_solid_count != 54:
        raise ValueError(
            f"standard preview expected 54 independent solids, "
            f"got {preview.component_solid_count}"
        )
    if preview.height_counts != {"HIGH": 6, "LOW": 8, "STANDARD": 10}:
        raise ValueError(f"incorrect height counts: {preview.height_counts}")
    if preview.tilt_counts != {20.0: 6, 0.0: 8, 10.0: 8, 30.0: 2}:
        raise ValueError(f"incorrect tilt counts: {preview.tilt_counts}")
    if preview.direction_counts != {
        0.0: 3,
        45.0: 3,
        90.0: 3,
        135.0: 3,
        180.0: 3,
        225.0: 3,
        270.0: 3,
        315.0: 3,
    }:
        raise ValueError(f"incorrect direction counts: {preview.direction_counts}")
    if len({round(value, 6) for value in preview.top_z_values}) < 3:
        raise ValueError("virtual stem tops must not share one plane")
    if preview.minimum_socket_clearance_mm < -1.0e-7:
        raise ValueError(
            f"socket interference detected: "
            f"{preview.minimum_socket_clearance_mm:.3f} mm"
        )
    if preview.projected_stem_crossing_count <= 0:
        raise ValueError("standard layout requires projected upper-stem crossings")
    if any(not solid.isValid() for solid in shape_solids(preview.shape)):
        raise ValueError("standard preview contains invalid component solids")


def build_standard_preview() -> StandardAssemblyPreview:
    """Build mount x2, base x4, socket x24, and virtual stem x24."""

    base_bottom_z = ROOT_MOUNT.thickness
    shapes: list[cq.Workplane] = [
        build_mount("L"),
        build_mount("R"),
    ]
    shapes.extend(
        build_base(module).translate((0.0, 0.0, base_bottom_z))
        for module in ("A", "B", "C", "D")
    )
    shapes.extend(
        placed_socket(entry, base_bottom_z)
        for entry in LAYOUT_STANDARD_V001
    )
    shapes.extend(
        build_virtual_stem(entry, base_bottom_z)
        for entry in LAYOUT_STANDARD_V001
    )
    compound = _compound(shapes)
    preview = StandardAssemblyPreview(
        shape=compound,
        metrics=measure_shape(compound),
        socket_ids=tuple(
            entry.socket_id
            for entry in LAYOUT_STANDARD_V001
        ),
        socket_count=24,
        virtual_stem_count=24,
        component_solid_count=len(shape_solids(compound)),
        height_counts=dict(
            Counter(entry.height_class for entry in LAYOUT_STANDARD_V001)
        ),
        tilt_counts=dict(
            Counter(entry.tilt_angle_deg for entry in LAYOUT_STANDARD_V001)
        ),
        direction_counts=dict(
            Counter(entry.tilt_direction_deg for entry in LAYOUT_STANDARD_V001)
        ),
        top_z_values=tuple(
            virtual_stem_end(entry, base_bottom_z)[2]
            for entry in LAYOUT_STANDARD_V001
        ),
        minimum_socket_clearance_mm=minimum_socket_clearance(
            LAYOUT_STANDARD_V001,
            base_bottom_z,
        ),
        projected_stem_crossing_count=len(
            projected_stem_crossings(
                LAYOUT_STANDARD_V001,
                base_bottom_z,
            )
        ),
    )
    validate_standard_preview(preview)
    return preview
