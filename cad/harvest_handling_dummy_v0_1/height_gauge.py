"""Generic zip-tie height-reference markers; no metre-scale printed ruler."""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from .cq_utils import validate_print_bounds
from .interfaces import require_positive
from .parameters import GAUGE


@dataclass(frozen=True)
class HeightMarkerParams:
    """Flat generic marker dimensions in mm."""

    width: float = 44.0
    length: float = 24.0
    thickness: float = 3.0
    label_relief: float = GAUGE.label_height
    zip_tie_slot_width: float = GAUGE.zip_tie_slot_width
    zip_tie_slot_length: float = GAUGE.zip_tie_slot_length


PART_IDS: dict[str, str] = {
    "BASE": "HU-H0-HHD-GAG-HEIGHT-BASE",
    "650": "HU-H0-HHD-GAG-HEIGHT-650",
    "750": "HU-H0-HHD-GAG-HEIGHT-750",
    "850": "HU-H0-HHD-GAG-HEIGHT-850",
}


def validate_params(params: HeightMarkerParams) -> None:
    """Validate printable marker and generic tie slots."""

    require_positive(
        width=params.width,
        length=params.length,
        thickness=params.thickness,
        label_relief=params.label_relief,
        zip_tie_slot_width=params.zip_tie_slot_width,
        zip_tie_slot_length=params.zip_tie_slot_length,
    )
    if params.zip_tie_slot_width < 4.0:
        raise ValueError("height marker zip-tie slot must be at least 4 mm")


def build(
    label: str,
    params: HeightMarkerParams = HeightMarkerParams(),
) -> cq.Workplane:
    """Build BASE, 650, 750, or 850 generic marker."""

    validate_params(params)
    if label not in PART_IDS:
        raise ValueError(f"unknown height marker: {label!r}")
    part = cq.Workplane("XY").box(
        params.width,
        params.length,
        params.thickness,
        centered=(True, True, False),
    )
    for x in (-15.0, 15.0):
        slot = (
            cq.Workplane("XY")
            .center(x, 0.0)
            .box(
                params.zip_tie_slot_width,
                params.zip_tie_slot_length,
                params.thickness,
                centered=(True, True, False),
            )
        )
        part = part.cut(slot)
    text_value = "HHD" if label == "BASE" else label
    text = (
        cq.Workplane("XY")
        .workplane(offset=params.thickness)
        .text(
            text_value,
            6.0,
            params.label_relief,
            combine=True,
            halign="center",
            valign="center",
        )
    )
    part = part.union(text)
    validate_print_bounds(part, PART_IDS[label])
    return part
