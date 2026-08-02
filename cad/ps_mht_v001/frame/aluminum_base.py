"""450 x 450 mm simplified 2020 aluminium base and load plate."""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from ps_mht_v001.common.extrusion import place_member
from ps_mht_v001.parameters import (
    frame_base_depth,
    frame_base_width,
    frame_center_member_length,
    frame_profile_size,
    frame_side_member_length,
    support_plate_diameter,
    support_plate_thickness,
)


@dataclass(frozen=True)
class FramePart:
    """One purchased/reference frame component."""

    name: str
    model: cq.Workplane
    material: str


def build_base_parts() -> tuple[FramePart, ...]:
    """Build five 2020 members plus the broad aluminium support plate."""

    half_width = 0.5 * frame_base_width
    half_depth = 0.5 * frame_base_depth
    half_profile = 0.5 * frame_profile_size
    rail_z = -frame_profile_size

    parts = (
        FramePart(
            "frame_front_2020_450",
            place_member(
                frame_base_width,
                "x",
                y=-half_depth + half_profile,
                z=rail_z,
            ),
            "PURCHASED_2020_ALUMINIUM",
        ),
        FramePart(
            "frame_rear_2020_450",
            place_member(
                frame_base_width,
                "x",
                y=half_depth - half_profile,
                z=rail_z,
            ),
            "PURCHASED_2020_ALUMINIUM",
        ),
        FramePart(
            "frame_left_2020_410",
            place_member(
                frame_side_member_length,
                "y",
                x=-half_width + half_profile,
                z=rail_z,
            ),
            "PURCHASED_2020_ALUMINIUM",
        ),
        FramePart(
            "frame_right_2020_410",
            place_member(
                frame_side_member_length,
                "y",
                x=half_width - half_profile,
                z=rail_z,
            ),
            "PURCHASED_2020_ALUMINIUM",
        ),
        FramePart(
            "frame_center_2020_410",
            place_member(
                frame_center_member_length,
                "y",
                z=rail_z,
            ),
            "PURCHASED_2020_ALUMINIUM",
        ),
        FramePart(
            "tower_load_spreader_plate",
            cq.Workplane("XY")
            .circle(0.5 * support_plate_diameter)
            .extrude(support_plate_thickness)
            .translate((0.0, 0.0, -support_plate_thickness)),
            "PURCHASED_ALUMINIUM_PLATE",
        ),
    )
    return parts


def build_aluminum_base() -> cq.Workplane:
    """Return the disconnected purchased base components as a compound."""

    compound = cq.Compound.makeCompound(
        [part.model.val() for part in build_base_parts()]
    )
    return cq.Workplane("XY").newObject([compound])

