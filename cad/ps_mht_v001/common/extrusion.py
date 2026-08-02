"""Simplified purchased 2020 aluminium extrusion geometry."""

from __future__ import annotations

from typing import Literal

import cadquery as cq

from ps_mht_v001.parameters import frame_profile_size


Axis = Literal["x", "y", "z"]


def make_2020_member(length: float, axis: Axis) -> cq.Workplane:
    """Build a solid 20 x 20 mm purchasing-envelope member.

    Slot details are deliberately omitted until the purchased profile is
    measured. Horizontal members start at Z=0 and vertical members grow in +Z.
    """

    if length <= 0.0:
        raise ValueError(f"extrusion length must be positive, got {length}")
    profile = frame_profile_size
    if axis == "x":
        dimensions = (length, profile, profile)
    elif axis == "y":
        dimensions = (profile, length, profile)
    elif axis == "z":
        dimensions = (profile, profile, length)
    else:
        raise ValueError(f"unsupported extrusion axis: {axis!r}")
    return cq.Workplane("XY").box(
        *dimensions,
        centered=(True, True, False),
    )


def place_member(
    length: float,
    axis: Axis,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
) -> cq.Workplane:
    """Build and translate one simplified extrusion member."""

    return make_2020_member(length, axis).translate((x, y, z))

