"""Removable module-specific layout transfer plates; CSV/JSON remain canonical."""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from .cq_utils import validate_print_bounds
from .interfaces import require_positive
from .parameters import GAUGE, ROOT_BASE
from .presets.layout_standard_v001 import entries_for_module
from .root_base import module_bounds


@dataclass(frozen=True)
class LayoutRecordPlateParams:
    """Thin overlay plate dimensions in mm."""

    width: float = ROOT_BASE.module_width
    length: float = ROOT_BASE.module_length
    thickness: float = 2.0
    socket_mark_diameter: float = 14.0
    label_relief: float = GAUGE.label_height
    label_font_size: float = 5.0
    direction_arrow_length: float = 18.0


PART_IDS: dict[str, str] = {
    module: f"HU-H0-HHD-MAP-{module}"
    for module in ("A", "B", "C", "D")
}


def validate_params(
    module: str,
    params: LayoutRecordPlateParams = LayoutRecordPlateParams(),
) -> None:
    """Validate overlay size, marks, and six-row mapping."""

    if module not in PART_IDS:
        raise ValueError(f"unknown layout plate module: {module!r}")
    require_positive(
        width=params.width,
        length=params.length,
        thickness=params.thickness,
        socket_mark_diameter=params.socket_mark_diameter,
        label_relief=params.label_relief,
        label_font_size=params.label_font_size,
        direction_arrow_length=params.direction_arrow_length,
    )
    if len(entries_for_module(module)) != 6:
        raise ValueError("layout record plate requires six socket marks")


def build(
    module: str,
    params: LayoutRecordPlateParams = LayoutRecordPlateParams(),
) -> cq.Workplane:
    """Build one removable six-hole numbered transfer plate."""

    validate_params(module, params)
    x_min, x_max, y_min, y_max = module_bounds(module)
    center_x = 0.5 * (x_min + x_max)
    center_y = 0.5 * (y_min + y_max)
    part = (
        cq.Workplane("XY")
        .box(
            params.width,
            params.length,
            params.thickness,
            centered=(True, True, False),
        )
        .translate((center_x, center_y, 0.0))
    )
    for entry in entries_for_module(module):
        mark = (
            cq.Workplane("XY")
            .center(entry.x_mm, entry.y_mm)
            .circle(0.5 * params.socket_mark_diameter)
            .extrude(params.thickness)
        )
        part = part.cut(mark)
        label = (
            cq.Workplane("XY")
            .workplane(offset=params.thickness)
            .center(entry.x_mm, entry.y_mm + 9.5)
            .text(
                entry.socket_id,
                params.label_font_size,
                params.label_relief,
                combine=True,
                halign="center",
                valign="center",
            )
        )
        part = part.union(label)

    module_label = (
        cq.Workplane("XY")
        .workplane(offset=params.thickness)
        .center(center_x, center_y)
        .text(
            module,
            10.0,
            params.label_relief,
            combine=True,
            halign="center",
            valign="center",
        )
    )
    arrow = (
        cq.Workplane("XY")
        .box(
            params.direction_arrow_length,
            1.4,
            params.label_relief,
            centered=(False, True, False),
        )
        .translate(
            (
                x_min + 8.0,
                y_max - 8.0,
                params.thickness,
            )
        )
    )
    arrow_head = (
        cq.Workplane("XY")
        .polyline(((0.0, -3.0), (6.0, 0.0), (0.0, 3.0)))
        .close()
        .extrude(params.label_relief)
        .translate(
            (
                x_min + 8.0 + params.direction_arrow_length,
                y_max - 8.0,
                params.thickness,
            )
        )
    )
    part = part.union(module_label).union(arrow).union(arrow_head)
    validate_print_bounds(part, PART_IDS[module])
    return part
