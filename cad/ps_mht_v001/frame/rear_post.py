"""Rear vertical 2020 post reference model."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.common.extrusion import place_member
from ps_mht_v001.parameters import frame_height, frame_post_offset


def build_rear_post() -> cq.Workplane:
    """Build the 1250 mm purchased rear post outside the root zone."""

    return place_member(
        frame_height,
        "z",
        y=frame_post_offset,
        z=0.0,
    )

