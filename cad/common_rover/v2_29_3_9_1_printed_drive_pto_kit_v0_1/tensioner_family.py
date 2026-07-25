from __future__ import annotations

import math

from geometry_common import (
    BuiltPart,
    box_xyz,
    cylinder_z,
    engrave_part_number,
)
from part_number_registry import PART_BY_KEY


PATH_KEYS = (
    ("drive-l", "DL"),
    ("drive-r", "DR"),
    ("pto-a", "PA"),
    ("pto-b", "PB"),
)


def _slot_tool(
    *,
    center_x: float,
    center_y: float,
    length_mm: float,
    width_mm: float,
    height_mm: float,
):
    straight = box_xyz(
        length_mm - width_mm,
        width_mm,
        height_mm,
        x=center_x,
        y=center_y,
        z=-1.0,
    )
    offset = (length_mm - width_mm) / 2.0
    return straight.fuse(
        cylinder_z(
            width_mm / 2.0,
            height_mm,
            x=center_x - offset,
            y=center_y,
            z=-1.0,
        ),
        cylinder_z(
            width_mm / 2.0,
            height_mm,
            x=center_x + offset,
            y=center_y,
            z=-1.0,
        ),
    )


def build_tensioner_slider(path_key: str, code: str) -> BuiltPart:
    spec = PART_BY_KEY[f"{path_key}_tensioner_slider"]
    shape = box_xyz(78.0, 34.0, 8.0)
    slots = (
        _slot_tool(
            center_x=13.0,
            center_y=8.0,
            length_mm=22.0,
            width_mm=4.5,
            height_mm=10.0,
        ),
        _slot_tool(
            center_x=13.0,
            center_y=-8.0,
            length_mm=22.0,
            width_mm=4.5,
            height_mm=10.0,
        ),
    )
    idler_bolt = cylinder_z(3.2, 10.0, x=28.0, z=-1.0)
    shape = shape.cut(*slots, idler_bolt)
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((-22.0, 6.0), (-22.0, -6.0)),
        surface_z=8.0,
        size_mm=2.3,
        metadata={
            "part_type": "PARAMETERIZED_TENSIONER_GUIDE",
            "path_code": code,
            "adjustment_slot_length_mm": 22.0,
            "minimum_usable_adjustment_stroke_mm": 12.0,
            "drive_center_distance_candidate_mm": [112.0, 130.0],
            "final_mounting_holes": "HOLD_FRAME_DIMENSIONS_UNCONFIRMED",
            "belt_reaction_carrier": "PURCHASED_METAL_MOTOR_SLIDE_OR_BRACKET",
            "printed_part_role": (
                "GUIDE LOCATE SCALE RETAIN LOW-LOAD IDLER WEAR PAD"
            ),
            "printed_part_is_only_bearing_race": False,
            "minimum_wall_mm": 3.0,
            "print_orientation": "LARGE FLAT FACE DOWN",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_adjustment_knob() -> BuiltPart:
    spec = PART_BY_KEY["tension_adjustment_knob"]
    center = cylinder_z(13.0, 8.0)
    lobes = []
    for index in range(8):
        angle = index * math.pi / 4.0
        lobes.append(
            cylinder_z(
                4.2,
                8.0,
                x=13.5 * math.cos(angle),
                y=13.5 * math.sin(angle),
            )
        )
    shape = center.fuse(*lobes).cut(cylinder_z(2.2, 10.0, z=-1.0))
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 7.0), (0.0, -7.0)),
        surface_z=8.0,
        size_mm=2.0,
        metadata={
            "part_type": "HAND_ADJUSTMENT_KNOB",
            "metal_nut_or_insert_required": True,
            "printed_thread_primary": False,
            "minimum_wall_mm": 4.0,
            "print_orientation": "FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_tensioner_family() -> list[BuiltPart]:
    parts = [
        build_tensioner_slider(path_key, code)
        for path_key, code in PATH_KEYS
    ]
    parts.append(build_adjustment_knob())
    return parts
