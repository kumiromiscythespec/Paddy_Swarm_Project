"""Four independent six-socket HHD-V001 root-base modules."""

from __future__ import annotations

import math

import cadquery as cq

from .cq_utils import validate_print_bounds
from .interfaces import require_positive, validate_base_socket_interface, validate_root_base
from .parameters import BASE_SOCKET, ROOT_BASE, RootBaseParams
from .presets.layout_standard_v001 import LayoutEntry, entries_for_module


MODULE_IDS: dict[str, str] = {
    "A": "HU-H0-HHD-BAS-A",
    "B": "HU-H0-HHD-BAS-B",
    "C": "HU-H0-HHD-BAS-C",
    "D": "HU-H0-HHD-BAS-D",
}


def module_bounds(
    module: str,
    params: RootBaseParams = ROOT_BASE,
) -> tuple[float, float, float, float]:
    """Return global x-min, x-max, y-min, y-max for one quadrant module."""

    if module == "A":
        return (-params.module_width, 0.0, 0.0, params.module_length)
    if module == "B":
        return (0.0, params.module_width, 0.0, params.module_length)
    if module == "C":
        return (-params.module_width, 0.0, -params.module_length, 0.0)
    if module == "D":
        return (0.0, params.module_width, -params.module_length, 0.0)
    raise ValueError(f"unknown base module: {module!r}")


def m4_hole_centers(
    module: str,
    params: RootBaseParams = ROOT_BASE,
) -> tuple[tuple[float, float], ...]:
    """Return the four module-to-mount M4 hole centres."""

    x_min, x_max, y_min, y_max = module_bounds(module, params)
    offset = params.m4_edge_offset
    return (
        (x_min + offset, y_min + offset),
        (x_max - offset, y_min + offset),
        (x_min + offset, y_max - offset),
        (x_max - offset, y_max - offset),
    )


def locating_key_centers(
    module: str,
    params: RootBaseParams = ROOT_BASE,
) -> tuple[tuple[float, float], ...]:
    """Return two mount-mediated module registration locations."""

    x_min, x_max, y_min, y_max = module_bounds(module, params)
    center_x = 0.5 * (x_min + x_max)
    return (
        (center_x, y_min + 10.0),
        (center_x, y_max - 10.0),
    )


def _octagon_corner_diameter(across_flats: float) -> float:
    """Convert regular-octagon across-flats to corner diameter."""

    return across_flats / math.cos(math.pi / 8.0)


def socket_edge_margin(
    entry: LayoutEntry,
    params: RootBaseParams = ROOT_BASE,
) -> float:
    """Return circular receiver-edge to nearest module boundary."""

    x_min, x_max, y_min, y_max = module_bounds(entry.base_module, params)
    center_to_edge = min(
        entry.x_mm - x_min,
        x_max - entry.x_mm,
        entry.y_mm - y_min,
        y_max - entry.y_mm,
    )
    return center_to_edge - 0.5 * BASE_SOCKET.receiver_diameter


def minimum_m4_socket_wall(
    module: str,
    params: RootBaseParams = ROOT_BASE,
) -> float:
    """Return minimum edge-to-edge wall between M4 and socket bores."""

    return min(
        math.hypot(entry.x_mm - hole_x, entry.y_mm - hole_y)
        - 0.5 * BASE_SOCKET.receiver_diameter
        - 0.5 * params.m4_clearance_diameter
        for entry in entries_for_module(module)
        for hole_x, hole_y in m4_hole_centers(module, params)
    )


def validate_module(module: str, params: RootBaseParams = ROOT_BASE) -> None:
    """Validate one module's six receivers, boundaries, and M4 separation."""

    validate_root_base(params)
    validate_base_socket_interface()
    entries = entries_for_module(module)
    if len(entries) != params.socket_count_per_module:
        raise ValueError(f"BASE-{module} must have exactly six sockets")
    for entry in entries:
        if socket_edge_margin(entry, params) + 1.0e-9 < params.min_socket_edge_margin:
            raise ValueError(
                f"{entry.socket_id} receiver edge margin "
                f"{socket_edge_margin(entry, params):.3f} mm is below "
                f"{params.min_socket_edge_margin:.3f} mm"
            )
    if minimum_m4_socket_wall(module, params) < params.petg_min_wall:
        raise ValueError(
            f"BASE-{module} M4-to-socket wall is below PETG minimum"
        )
    require_positive(
        receiver_bottom_wall=(
            params.module_thickness - BASE_SOCKET.insertion_depth
        )
    )


def build(
    module: str,
    params: RootBaseParams = ROOT_BASE,
) -> cq.Workplane:
    """Build one 105 x 105 x 18 mm module with six indexed receivers."""

    validate_module(module, params)
    x_min, x_max, y_min, y_max = module_bounds(module, params)
    center = (0.5 * (x_min + x_max), 0.5 * (y_min + y_max), 0.0)
    part = (
        cq.Workplane("XY")
        .box(
            params.module_width,
            params.module_length,
            params.module_thickness,
            centered=(True, True, False),
        )
        .translate(center)
    )
    receiver_bottom_z = params.module_thickness - BASE_SOCKET.insertion_depth
    index_bottom_z = params.module_thickness - BASE_SOCKET.index_depth
    for entry in entries_for_module(module):
        receiver = (
            cq.Workplane("XY")
            .center(entry.x_mm, entry.y_mm)
            .circle(0.5 * BASE_SOCKET.receiver_diameter)
            .extrude(BASE_SOCKET.insertion_depth + 0.05)
            .translate((0.0, 0.0, receiver_bottom_z))
        )
        index = (
            cq.Workplane("XY")
            .center(entry.x_mm, entry.y_mm)
            .polygon(
                8,
                _octagon_corner_diameter(BASE_SOCKET.receiver_index_af),
            )
            .extrude(BASE_SOCKET.index_depth + 0.05)
            .translate((0.0, 0.0, index_bottom_z))
        )
        push_out = (
            cq.Workplane("XY")
            .center(entry.x_mm, entry.y_mm)
            .circle(0.5 * params.push_out_hole_diameter)
            .extrude(receiver_bottom_z + 0.05)
        )
        part = part.cut(receiver).cut(index).cut(push_out)

    for hole_x, hole_y in m4_hole_centers(module, params):
        m4_hole = (
            cq.Workplane("XY")
            .center(hole_x, hole_y)
            .circle(0.5 * params.m4_clearance_diameter)
            .extrude(params.module_thickness)
        )
        part = part.cut(m4_hole)

    for key_x, key_y in locating_key_centers(module, params):
        key_hole = (
            cq.Workplane("XY")
            .center(key_x, key_y)
            .circle(0.5 * params.locating_key_hole_diameter)
            .extrude(params.locating_key_depth)
        )
        part = part.cut(key_hole)

    validate_print_bounds(part, MODULE_IDS[module])
    return part
