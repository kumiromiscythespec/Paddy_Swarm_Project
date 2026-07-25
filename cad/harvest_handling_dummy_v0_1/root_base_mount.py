"""Left/right HHD-V001 workbench mount plates."""

from __future__ import annotations

import math

import cadquery as cq

from .cq_utils import validate_print_bounds
from .interfaces import validate_root_base, validate_root_mount
from .parameters import ROOT_BASE, ROOT_MOUNT, RootMountParams
from .root_base import locating_key_centers, m4_hole_centers


MOUNT_PART_IDS: dict[str, str] = {
    "L": "HU-H0-HHD-MNT-L",
    "R": "HU-H0-HHD-MNT-R",
}


def modules_for_side(side: str) -> tuple[str, str]:
    """Return the two base modules carried by one mount half."""

    if side == "L":
        return ("A", "C")
    if side == "R":
        return ("B", "D")
    raise ValueError(f"unknown mount side: {side!r}")


def m6_hole_centers(
    side: str,
    params: RootMountParams = ROOT_MOUNT,
) -> tuple[tuple[float, float], ...]:
    """Return two workbench M6 locations per mount half."""

    if side not in MOUNT_PART_IDS:
        raise ValueError(f"unknown mount side: {side!r}")
    x = (
        -0.5 * params.assembled_width + params.m6_edge_offset
        if side == "L"
        else 0.5 * params.assembled_width - params.m6_edge_offset
    )
    y = 0.5 * params.assembled_length - params.m6_edge_offset
    return ((x, -y), (x, y))


def minimum_m6_m4_wall(
    side: str,
    params: RootMountParams = ROOT_MOUNT,
) -> float:
    """Return the minimum edge wall between M6 and M4 bores."""

    return min(
        math.hypot(m6_x - m4_x, m6_y - m4_y)
        - 0.5 * params.m6_clearance_diameter
        - 0.5 * params.m4_clearance_diameter
        for m6_x, m6_y in m6_hole_centers(side, params)
        for module in modules_for_side(side)
        for m4_x, m4_y in m4_hole_centers(module)
    )


def validate_side(side: str, params: RootMountParams = ROOT_MOUNT) -> None:
    """Validate mount-hole and seam clearances."""

    validate_root_mount(params)
    validate_root_base()
    if minimum_m6_m4_wall(side, params) < params.petg_min_wall:
        raise ValueError(f"mount {side}: M6-to-M4 wall is below 2 mm")
    if params.seam_tongue_depth > params.thickness:
        raise ValueError("mount seam tongue depth exceeds plate thickness")
    for m6_x, m6_y in m6_hole_centers(side, params):
        x_edge = (
            m6_x + 0.5 * params.assembled_width
            if side == "L"
            else 0.5 * params.assembled_width - m6_x
        )
        y_edge = 0.5 * params.assembled_length - abs(m6_y)
        if min(x_edge, y_edge) - 0.5 * params.m6_clearance_diameter < 2.0:
            raise ValueError(f"mount {side}: M6 outer edge wall is below 2 mm")


def build(
    side: str,
    params: RootMountParams = ROOT_MOUNT,
) -> cq.Workplane:
    """Build one flat mount half with M6/M4 holes, pins, and seam index."""

    validate_side(side, params)
    center_x = -0.5 * params.half_width if side == "L" else 0.5 * params.half_width
    part = (
        cq.Workplane("XY")
        .box(
            params.half_width,
            params.assembled_length,
            params.thickness,
            centered=(True, True, False),
        )
        .translate((center_x, 0.0, 0.0))
    )

    for hole_x, hole_y in m6_hole_centers(side, params):
        hole = (
            cq.Workplane("XY")
            .center(hole_x, hole_y)
            .circle(0.5 * params.m6_clearance_diameter)
            .extrude(params.thickness)
        )
        part = part.cut(hole)
    for module in modules_for_side(side):
        for hole_x, hole_y in m4_hole_centers(module):
            hole = (
                cq.Workplane("XY")
                .center(hole_x, hole_y)
                .circle(0.5 * params.m4_clearance_diameter)
                .extrude(params.thickness)
            )
            part = part.cut(hole)
        for pin_x, pin_y in locating_key_centers(module):
            pin = (
                cq.Workplane("XY")
                .center(pin_x, pin_y)
                .circle(0.5 * params.locating_pin_diameter)
                .extrude(params.locating_pin_height)
                .translate((0.0, 0.0, params.thickness))
            )
            part = part.union(pin)

    seam_y_positions = (-52.5, 52.5)
    if side == "L":
        for y in seam_y_positions:
            tongue = (
                cq.Workplane("XY")
                .box(
                    params.seam_tongue_depth,
                    params.seam_tongue_length,
                    0.5 * params.thickness,
                    centered=(False, True, False),
                )
                .translate((0.0, y, 0.25 * params.thickness))
            )
            part = part.union(tongue)
    else:
        for y in seam_y_positions:
            pocket = (
                cq.Workplane("XY")
                .box(
                    params.seam_tongue_depth + params.seam_clearance,
                    params.seam_tongue_length + params.seam_clearance,
                    0.5 * params.thickness + params.seam_clearance,
                    centered=(False, True, False),
                )
                .translate(
                    (
                        -0.1,
                        y,
                        0.25 * params.thickness
                        - 0.5 * params.seam_clearance,
                    )
                )
            )
            part = part.cut(pocket)

    validate_print_bounds(part, MOUNT_PART_IDS[side])
    return part
