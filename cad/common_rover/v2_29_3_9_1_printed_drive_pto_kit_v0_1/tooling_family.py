from __future__ import annotations

import math

from geometry_common import (
    BuiltPart,
    add_label_pad,
    box_xyz,
    cylinder_z,
    engrave_part_number,
)
from part_number_registry import PART_BY_KEY
from tensioner_family import _slot_tool


def build_center_distance_gauge() -> BuiltPart:
    spec = PART_BY_KEY["center_distance_gauge"]
    shape = box_xyz(148.0, 24.0, 4.0)
    fixed = cylinder_z(3.1, 6.0, x=-60.5, z=-1.0)
    adjustment = _slot_tool(
        center_x=60.5,
        center_y=0.0,
        length_mm=18.0,
        width_mm=6.2,
        height_mm=6.0,
    )
    shape = shape.cut(fixed, adjustment)
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((-34.0, 5.0), (-34.0, -5.0)),
        surface_z=4.0,
        size_mm=2.3,
        metadata={
            "part_type": "CENTER_DISTANCE_GAUGE",
            "nominal_center_distance_mm": 121.0,
            "adjustment_range_mm": [112.0, 130.0],
            "measurement_status": "CALIBRATION_PENDING",
            "minimum_wall_mm": 4.0,
            "print_orientation": "FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_alignment_gauge() -> BuiltPart:
    spec = PART_BY_KEY["pulley_alignment_gauge"]
    base = box_xyz(150.0, 22.0, 4.0)
    lip = box_xyz(150.0, 3.0, 12.0, y=-9.5)
    shape = base.fuse(lip)
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 5.0), (0.0, -1.0)),
        surface_z=4.0,
        size_mm=2.5,
        metadata={
            "part_type": "PULLEY_FACE_ALIGNMENT_GAUGE",
            "reference_length_mm": 150.0,
            "measurement_status": "CALIBRATION_PENDING",
            "minimum_wall_mm": 3.0,
            "print_orientation": "BASE FLAT; LIP VERTICAL",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_parallelism_gauge() -> BuiltPart:
    spec = PART_BY_KEY["parallelism_gauge"]
    outer = box_xyz(142.0, 58.0, 4.0)
    opening = box_xyz(116.0, 36.0, 6.0, z=-1.0)
    shape = outer.cut(opening)
    shape = add_label_pad(
        shape,
        width_mm=46.0,
        depth_mm=11.0,
        bottom_z=3.8,
        thickness_mm=1.0,
        center_y=23.0,
    )
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 21.0), (0.0, 25.0)),
        surface_z=4.8,
        size_mm=2.2,
        metadata={
            "part_type": "SHAFT_PARALLELISM_FRAME_GAUGE",
            "reference_span_mm": 116.0,
            "measurement_status": "CALIBRATION_PENDING",
            "minimum_wall_mm": 4.0,
            "print_orientation": "FRAME FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def _build_transfer_template(
    key: str,
    *,
    title: str,
    slot_spacing_candidate_mm: float,
) -> BuiltPart:
    spec = PART_BY_KEY[key]
    shape = box_xyz(126.0, 52.0, 4.0)
    for y in (-slot_spacing_candidate_mm / 2.0, slot_spacing_candidate_mm / 2.0):
        shape = shape.cut(
            _slot_tool(
                center_x=25.0,
                center_y=y,
                length_mm=30.0,
                width_mm=4.5,
                height_mm=6.0,
            )
        )
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((-35.0, 7.0), (-35.0, -7.0)),
        surface_z=4.0,
        size_mm=2.4,
        metadata={
            "part_type": title,
            "slot_spacing_candidate_mm": slot_spacing_candidate_mm,
            "final_hole_authority": "HOLD_DO_NOT_DRILL_WITHOUT_MEASUREMENT",
            "measurement_status": "CALIBRATION_PENDING",
            "minimum_wall_mm": 4.0,
            "print_orientation": "PLATE FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_joining_jig() -> BuiltPart:
    spec = PART_BY_KEY["tpu_joining_jig"]
    shape = box_xyz(94.0, 42.0, 10.0)
    channel = box_xyz(76.0, 15.4, 5.0, z=6.0)
    shape = shape.cut(channel)
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 15.0), (0.0, -15.0)),
        surface_z=10.0,
        size_mm=2.5,
        metadata={
            "part_type": "TPU_JOINING_ALIGNMENT_JIG",
            "channel_width_mm": 15.4,
            "powered_approval": "NEVER",
            "joint_location_rule": "DO_NOT_WRAP JOINT AROUND 20T",
            "minimum_wall_mm": 5.0,
            "print_orientation": "BASE FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_torque_fuse() -> BuiltPart:
    spec = PART_BY_KEY["sacrificial_torque_fuse"]
    shape = cylinder_z(30.0, 6.0).cut(cylinder_z(5.1, 8.0, z=-1.0))
    holes = []
    for index in range(6):
        angle = index * math.pi / 3.0
        holes.append(
            cylinder_z(
                3.0,
                8.0,
                x=18.0 * math.cos(angle),
                y=18.0 * math.sin(angle),
                z=-1.0,
            )
        )
    shape = shape.cut(*holes)
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, 11.0), (0.0, -11.0)),
        surface_z=6.0,
        size_mm=2.4,
        metadata={
            "part_type": "SACRIFICIAL_TORQUE_FUSE_CANDIDATE",
            "release_torque": "CALIBRATION_PENDING",
            "powered_loaded_status": "HOLD",
            "minimum_wall_mm": 4.0,
            "print_orientation": "DISK FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_storage_fixture() -> BuiltPart:
    spec = PART_BY_KEY["belt_storage_fixture"]
    shape = box_xyz(148.0, 44.0, 5.0)
    shape = shape.cut(
        _slot_tool(
            center_x=34.0,
            center_y=0.0,
            length_mm=54.0,
            width_mm=18.0,
            height_mm=7.0,
        )
    )
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((-42.0, 7.0), (-42.0, -7.0)),
        surface_z=5.0,
        size_mm=2.5,
        metadata={
            "part_type": "LABELED_BELT_STORAGE_FIXTURE",
            "storage_only": True,
            "minimum_wall_mm": 5.0,
            "print_orientation": "PLATE FLAT",
            "support": "OFF",
            "trapped_support": False,
        },
    )


def build_tooling_family() -> list[BuiltPart]:
    return [
        build_center_distance_gauge(),
        build_alignment_gauge(),
        build_parallelism_gauge(),
        _build_transfer_template(
            "motor_slide_template",
            title="PARAMETERIZED_MOTOR_SLIDE_TRANSFER_TEMPLATE",
            slot_spacing_candidate_mm=30.0,
        ),
        _build_transfer_template(
            "bearing_block_template",
            title="PARAMETERIZED_BEARING_BLOCK_TRANSFER_TEMPLATE",
            slot_spacing_candidate_mm=36.0,
        ),
        build_joining_jig(),
        build_torque_fuse(),
        build_storage_fixture(),
    ]
