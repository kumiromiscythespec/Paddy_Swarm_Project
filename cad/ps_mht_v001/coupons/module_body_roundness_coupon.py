"""Full-diameter short ring for body roundness and wall calibration."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    module_wall_thickness,
    tower_body_diameter,
)


ROUNDNESS_COUPON_HEIGHT = 28.0


def build_module_body_roundness_coupon() -> cq.Workplane:
    """Build the support-free 200 mm OD, 3 mm wall calibration ring."""

    outer_radius = 0.5 * tower_body_diameter
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(outer_radius - module_wall_thickness)
        .extrude(ROUNDNESS_COUPON_HEIGHT)
    )

