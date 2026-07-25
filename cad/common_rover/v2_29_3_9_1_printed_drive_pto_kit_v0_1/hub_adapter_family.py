from __future__ import annotations

import math

from geometry_common import (
    BuiltPart,
    add_label_pad,
    box_xyz,
    cylinder_z,
    engrave_part_number,
)
from part_number_registry import HUB_AND_SPACER_PARTS, PART_BY_KEY


PATH_CODES = (
    ("drive-l", "dl"),
    ("drive-r", "dr"),
    ("pto-a", "pa"),
    ("pto-b", "pb"),
)


def build_hub_adapter(path_key: str, code: str) -> BuiltPart:
    spec = PART_BY_KEY[f"{path_key}_hub_adapter"]
    shape = cylinder_z(18.0, 8.0).cut(cylinder_z(5.1, 10.0, z=-1.0))
    pcd_tools = []
    for index in range(4):
        angle = index * math.pi / 2.0
        pcd_tools.append(
            cylinder_z(
                2.15,
                10.0,
                x=12.0 * math.cos(angle),
                y=12.0 * math.sin(angle),
                z=-1.0,
            )
        )
    shape = shape.cut(*pcd_tools)
    if path_key.startswith("pto"):
        shape = shape.cut(box_xyz(14.0, 1.2, 10.0, x=12.0, z=-1.0))
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 8.0), (0.0, -8.0)),
        surface_z=8.0,
        size_mm=2.3,
        metadata={
            "part_type": "SACRIFICIAL_HUB_ADAPTER",
            "path_code": code.upper(),
            "bore_candidate_mm": 10.2,
            "hub_pcd_mm": 24.0,
            "hub_hole_diameter_mm": 4.3,
            "metal_fasteners_required": True,
            "shaft_measurement_status": "CALIBRATION_PENDING",
            "minimum_wall_mm": 3.0,
            "print_orientation": "FLAT FACE DOWN",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_spacer(path_key: str, code: str) -> BuiltPart:
    spec = PART_BY_KEY[f"{path_key}_shaft_spacer"]
    shape = cylinder_z(12.0, 4.0).cut(cylinder_z(5.1, 6.0, z=-1.0))
    shape = add_label_pad(
        shape,
        width_mm=30.0,
        depth_mm=10.0,
        bottom_z=3.8,
        thickness_mm=1.0,
        center_y=15.0,
    )
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 13.0), (0.0, 17.0)),
        surface_z=4.8,
        size_mm=2.0,
        metadata={
            "part_type": "SHAFT_SPACER_WITH_ID_TAB",
            "path_code": code.upper(),
            "bore_candidate_mm": 10.2,
            "axial_width_mm": 4.0,
            "measurement_status": "CALIBRATION_PENDING",
            "minimum_wall_mm": 4.0,
            "print_orientation": "RING FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_removable_flange(path_key: str, code: str) -> BuiltPart:
    spec = PART_BY_KEY[f"{path_key}_removable_flange"]
    shape = cylinder_z(50.3, 1.8).cut(cylinder_z(7.0, 3.8, z=-1.0))
    tools = []
    for index in range(4):
        angle = index * math.pi / 2.0
        tools.append(
            cylinder_z(
                2.15,
                3.8,
                x=12.0 * math.cos(angle),
                y=12.0 * math.sin(angle),
                z=-1.0,
            )
        )
    shape = shape.cut(*tools)
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 22.0), (0.0, -22.0)),
        surface_z=1.8,
        size_mm=2.7,
        metadata={
            "part_type": "REMOVABLE_60T_FLANGE",
            "path_code": code.upper(),
            "hub_pcd_mm": 24.0,
            "hub_hole_diameter_mm": 4.3,
            "outside_diameter_mm": 100.6,
            "metal_fasteners_required": True,
            "minimum_wall_mm": 1.8,
            "print_orientation": "FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_hubs_spacers_and_flanges() -> list[BuiltPart]:
    parts = []
    for path_key, code in PATH_CODES:
        parts.extend(
            (
                build_hub_adapter(path_key, code),
                build_spacer(path_key, code),
                build_removable_flange(path_key, code),
            )
        )
    return parts
