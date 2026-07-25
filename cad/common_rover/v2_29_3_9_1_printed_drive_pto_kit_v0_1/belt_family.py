from __future__ import annotations

from dataclasses import dataclass
import math

from drive_pto_contract import (
    BELT_WIDTH_MM,
    DRIVE_BELT_PITCH_LENGTH_MM,
    PITCH_MM,
    TOOTH_COMPENSATION_MM,
    belt_tooth_count,
)
from geometry_common import (
    BuiltPart,
    add_label_pad,
    box_xyz,
    cylinder_z,
    engrave_part_number,
    require_cadquery,
)
from htd5m_profile import (
    BELT_TOOTH_DEPTH_MM,
    belt_pitch_radius_mm,
    belt_tooth_solids,
)
from part_number_registry import PART_BY_KEY


BACKING_THICKNESS_MM = 2.20
LABEL_PAD_WIDTH_MM = 38.0
LABEL_PAD_DEPTH_MM = 10.0
LABEL_PAD_THICKNESS_MM = 1.0


@dataclass(frozen=True)
class ContinuousBeltConfig:
    key: str
    path_id: str
    pitch_length_mm: float
    pitch_compensation_mm: float = 0.0
    shrinkage_compensation: float = 1.0
    tooth_depth_mm: float = BELT_TOOTH_DEPTH_MM
    tooth_width_compensation_mm: float = 0.0


CONTINUOUS_BELTS: tuple[ContinuousBeltConfig, ...] = (
    ContinuousBeltConfig("drive_l_450_belt", "DRIVE-L", 450.0),
    ContinuousBeltConfig("drive_r_450_belt", "DRIVE-R", 450.0),
    ContinuousBeltConfig("spare_450_belt", "SPARE", 450.0),
)


def build_continuous_belt(config: ContinuousBeltConfig) -> BuiltPart:
    spec = PART_BY_KEY[config.key]
    tooth_count = belt_tooth_count(config.pitch_length_mm)
    pitch_radius = belt_pitch_radius_mm(
        config.pitch_length_mm,
        pitch_compensation_mm=config.pitch_compensation_mm,
        shrinkage_compensation=config.shrinkage_compensation,
    )
    backing_inner_radius = pitch_radius + 0.25
    backing_outer_radius = pitch_radius + BACKING_THICKNESS_MM
    backing = cylinder_z(backing_outer_radius, BELT_WIDTH_MM).cut(
        cylinder_z(backing_inner_radius, BELT_WIDTH_MM + 2.0, z=-1.0)
    )
    teeth = belt_tooth_solids(
        tooth_count,
        pitch_radius,
        BELT_WIDTH_MM,
        tooth_depth_mm=config.tooth_depth_mm,
        tooth_width_compensation_mm=config.tooth_width_compensation_mm,
    )
    shape = backing.fuse(*teeth)
    label_center_y = backing_outer_radius + 3.0
    shape = add_label_pad(
        shape,
        width_mm=LABEL_PAD_WIDTH_MM,
        depth_mm=LABEL_PAD_DEPTH_MM,
        bottom_z=BELT_WIDTH_MM - 0.20,
        thickness_mm=LABEL_PAD_THICKNESS_MM,
        center_y=label_center_y,
    )
    metadata = {
        "profile": "HTD-5M",
        "path_id": config.path_id,
        "form": "CONTINUOUS_CLOSED_LOOP",
        "pitch_mm": PITCH_MM,
        "pitch_length_mm": config.pitch_length_mm,
        "tooth_count": tooth_count,
        "belt_width_mm": BELT_WIDTH_MM,
        "pitch_radius_mm": pitch_radius,
        "outside_backing_thickness_mm": BACKING_THICKNESS_MM,
        "tooth_depth_mm": config.tooth_depth_mm,
        "pitch_compensation_mm": config.pitch_compensation_mm,
        "shrinkage_compensation": config.shrinkage_compensation,
        "inner_tooth_orientation": True,
        "closed_loop": True,
        "self_intersection": False,
        "id_pad": "EXTERIOR THIN INTEGRATED MARKING PAD",
        "minimum_wall_mm": BACKING_THICKNESS_MM - 0.25,
        "print_orientation": "FLAT CIRCULAR LOOP ON BUILD PLATE",
        "support": "OFF",
        "trapped_support": False,
        "powered_status": "HOLD_STAGED_APPROVAL_REQUIRED",
    }
    return engrave_part_number(
        shape,
        spec,
        centers_xy=(
            (0.0, backing_outer_radius + 1.0),
            (0.0, backing_outer_radius + 5.5),
        ),
        surface_z=BELT_WIDTH_MM + 0.80,
        size_mm=2.0,
        depth_mm=0.50,
        metadata=metadata,
    )


def _straight_tooth(
    center_x: float,
    pitch_mm: float,
    tooth_depth_mm: float,
    root_width_mm: float,
    tip_width_mm: float,
    backing_thickness_mm: float,
):
    cq = require_cadquery()
    overlap = 0.20
    polygon = (
        (center_x - root_width_mm / 2.0, backing_thickness_mm - overlap),
        (center_x - tip_width_mm / 2.0, backing_thickness_mm + tooth_depth_mm),
        (center_x + tip_width_mm / 2.0, backing_thickness_mm + tooth_depth_mm),
        (center_x + root_width_mm / 2.0, backing_thickness_mm - overlap),
    )
    return (
        cq.Workplane("XZ")
        .polyline(polygon)
        .close()
        .extrude(BELT_WIDTH_MM)
        .translate((0.0, BELT_WIDTH_MM / 2.0, 0.0))
        .val()
    )


def build_short_belt(
    key: str,
    *,
    tooth_count: int,
    tooth_width_compensation_mm: float,
    backing_thickness_mm: float = BACKING_THICKNESS_MM,
    joiner_groove: bool = False,
) -> BuiltPart:
    spec = PART_BY_KEY[key]
    length = tooth_count * PITCH_MM
    backing = box_xyz(
        length + PITCH_MM,
        BELT_WIDTH_MM,
        backing_thickness_mm,
        z=0.0,
    )
    tooth_solids = []
    for index in range(tooth_count):
        center_x = (index - (tooth_count - 1) / 2.0) * PITCH_MM
        tooth_solids.append(
            _straight_tooth(
                center_x,
                PITCH_MM,
                BELT_TOOTH_DEPTH_MM,
                3.15 + tooth_width_compensation_mm,
                1.60 + tooth_width_compensation_mm,
                backing_thickness_mm,
            )
        )
    shape = backing.fuse(*tooth_solids)
    label_center_y = BELT_WIDTH_MM / 2.0 + 3.0
    shape = add_label_pad(
        shape,
        width_mm=34.0,
        depth_mm=8.0,
        bottom_z=backing_thickness_mm - 0.20,
        thickness_mm=1.0,
        center_y=label_center_y,
    )
    if joiner_groove:
        groove = box_xyz(
            1.0,
            BELT_WIDTH_MM - 4.0,
            0.8,
            z=backing_thickness_mm - 0.50,
        )
        shape = shape.cut(groove)
    compensation_index = (
        ("tooth_fit_a", "tooth_fit_b", "tooth_fit_c").index(key)
        if key in {"tooth_fit_a", "tooth_fit_b", "tooth_fit_c"}
        else None
    )
    metadata = {
        "profile": "HTD-5M",
        "form": (
            "JOINER_FIT_HAND_ONLY"
            if joiner_groove
            else "FLEXIBLE_SHORT_TOOTH_STRIP"
        ),
        "pitch_mm": PITCH_MM,
        "tooth_count": tooth_count,
        "belt_width_mm": BELT_WIDTH_MM,
        "backing_thickness_mm": backing_thickness_mm,
        "tooth_depth_mm": BELT_TOOTH_DEPTH_MM,
        "tooth_width_compensation_mm": tooth_width_compensation_mm,
        "compensation_variant": (
            None if compensation_index is None else "ABC"[compensation_index]
        ),
        "wrap_target": "20T HAND FIT" if key == "bend_fit_short" else "20T/60T HAND FIT",
        "joiner_location_rule": (
            "JOINT MUST NOT WRAP 20T" if joiner_groove else None
        ),
        "closed_loop": False,
        "powered_status": "NEVER_POWERED" if joiner_groove else "HAND_FIT_ONLY",
        "minimum_wall_mm": backing_thickness_mm,
        "print_orientation": "BACKING FLAT; TEETH UP",
        "support": "OFF",
        "trapped_support": False,
    }
    return engrave_part_number(
        shape,
        spec,
        centers_xy=((0.0, label_center_y - 1.5), (0.0, label_center_y + 2.0)),
        surface_z=backing_thickness_mm + 0.80,
        size_mm=2.0,
        depth_mm=0.50,
        metadata=metadata,
    )


def build_belt_family() -> list[BuiltPart]:
    parts = [build_continuous_belt(config) for config in CONTINUOUS_BELTS]
    for key, compensation in zip(
        ("tooth_fit_a", "tooth_fit_b", "tooth_fit_c"),
        TOOTH_COMPENSATION_MM,
    ):
        parts.append(
            build_short_belt(
                key,
                tooth_count=8,
                tooth_width_compensation_mm=compensation,
            )
        )
    parts.append(
        build_short_belt(
            "bend_fit_short",
            tooth_count=10,
            tooth_width_compensation_mm=0.0,
            backing_thickness_mm=1.8,
        )
    )
    parts.append(
        build_short_belt(
            "joiner_fit",
            tooth_count=8,
            tooth_width_compensation_mm=0.0,
            joiner_groove=True,
        )
    )
    return parts


def belt_manifest_rows() -> list[dict[str, object]]:
    rows = []
    for config in CONTINUOUS_BELTS:
        spec = PART_BY_KEY[config.key]
        rows.append(
            {
                "part_number": spec.part_number,
                "path_id": config.path_id,
                "belt_type": "CONTINUOUS_CLOSED_LOOP",
                "pitch_mm": PITCH_MM,
                "pitch_length_mm": config.pitch_length_mm,
                "tooth_count": belt_tooth_count(config.pitch_length_mm),
                "belt_width_mm": BELT_WIDTH_MM,
                "length_status": "CANDIDATE",
                "powered_status": "HOLD_STAGED_APPROVAL_REQUIRED",
                "filename": spec.filename,
            }
        )
    for key, belt_type in (
        ("tooth_fit_a", "TOOTH-FIT-SHORT-A"),
        ("tooth_fit_b", "TOOTH-FIT-SHORT-B"),
        ("tooth_fit_c", "TOOTH-FIT-SHORT-C"),
        ("bend_fit_short", "BEND-FIT-SHORT"),
        ("joiner_fit", "JOINER-FIT"),
    ):
        spec = PART_BY_KEY[key]
        rows.append(
            {
                "part_number": spec.part_number,
                "path_id": "CALIBRATION",
                "belt_type": belt_type,
                "pitch_mm": PITCH_MM,
                "pitch_length_mm": "SHORT_COUPON",
                "tooth_count": 10 if key == "bend_fit_short" else 8,
                "belt_width_mm": BELT_WIDTH_MM,
                "length_status": "CALIBRATION",
                "powered_status": (
                    "NEVER_POWERED"
                    if key == "joiner_fit"
                    else "HAND_FIT_ONLY"
                ),
                "filename": spec.filename,
            }
        )
    for key, path_id in (
        ("pto_a_final_belt_hold", "PTO-A"),
        ("pto_b_final_belt_hold", "PTO-B"),
    ):
        spec = PART_BY_KEY[key]
        rows.append(
            {
                "part_number": spec.part_number,
                "path_id": path_id,
                "belt_type": "CONTINUOUS_CLOSED_LOOP",
                "pitch_mm": PITCH_MM,
                "pitch_length_mm": "CALIBRATION_PENDING",
                "tooth_count": "CALIBRATION_PENDING",
                "belt_width_mm": BELT_WIDTH_MM,
                "length_status": "HOLD",
                "powered_status": "HOLD",
                "filename": "NOT_GENERATED",
            }
        )
    return rows
