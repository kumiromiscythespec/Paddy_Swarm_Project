from __future__ import annotations

from geometry_common import (
    BuiltPart,
    box_xyz,
    cylinder_z,
    engrave_part_number,
)
from part_number_registry import PART_BY_KEY
from tensioner_family import _slot_tool


PATH_KEYS = (
    ("drive-l", "DL"),
    ("drive-r", "DR"),
    ("pto-a", "PA"),
    ("pto-b", "PB"),
)


def build_belt_guard(path_key: str, code: str) -> BuiltPart:
    spec = PART_BY_KEY[f"{path_key}_belt_guard"]
    shape = box_xyz(126.0, 56.0, 3.0)
    vents = []
    for x in (8.0, 30.0, 52.0):
        for y in (-13.0, 13.0):
            vents.append(box_xyz(14.0, 6.0, 5.0, x=x, y=y, z=-1.0))
    mount_slots = (
        _slot_tool(
            center_x=-50.0,
            center_y=19.0,
            length_mm=16.0,
            width_mm=4.5,
            height_mm=5.0,
        ),
        _slot_tool(
            center_x=-50.0,
            center_y=-19.0,
            length_mm=16.0,
            width_mm=4.5,
            height_mm=5.0,
        ),
    )
    shape = shape.cut(*vents, *mount_slots)
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((-33.0, 7.0), (-33.0, -7.0)),
        surface_z=3.0,
        size_mm=2.5,
        metadata={
            "part_type": "TEMPORARY_BELT_GUARD",
            "path_code": code,
            "minimum_guard_clearance_mm": 8.0,
            "final_mounting_holes": "HOLD_FRAME_DIMENSIONS_UNCONFIRMED",
            "mount_interface": "PARAMETERIZED_SLOTS",
            "minimum_wall_mm": 3.0,
            "print_orientation": "COVER FLAT",
            "support": "OFF",
            "trapped_support": False,
            "safety": "FIRST POWERED TEST GUARD REQUIRED",
        },
    )


def build_shaft_end_guard() -> BuiltPart:
    spec = PART_BY_KEY["shaft_end_guard"]
    shape = cylinder_z(26.0, 3.5)
    for angle_x, angle_y in ((17.0, 0.0), (-8.5, 14.72), (-8.5, -14.72)):
        shape = shape.cut(
            cylinder_z(2.3, 5.5, x=angle_x, y=angle_y, z=-1.0)
        )
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 9.0), (0.0, -9.0)),
        surface_z=3.5,
        size_mm=2.4,
        metadata={
            "part_type": "TEMPORARY_SHAFT_END_COVER",
            "final_mounting_holes": "HOLD_FRAME_DIMENSIONS_UNCONFIRMED",
            "minimum_wall_mm": 3.5,
            "print_orientation": "COVER FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_guard_family() -> list[BuiltPart]:
    parts = [
        build_belt_guard(path_key, code) for path_key, code in PATH_KEYS
    ]
    parts.append(build_shaft_end_guard())
    return parts
