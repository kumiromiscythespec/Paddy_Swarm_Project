"""Broad Phase 3R upper clamping/load-distribution ring."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    m4_clearance_diameter,
    module_clamping_ring_inner_diameter,
    module_clamping_ring_outer_diameter,
    module_clamping_ring_thickness,
    phase3r_m4_pitch_radius,
    used_fastener_angles,
)


STATUS = "PHASE3R_BROAD_ANNULAR_LOAD_DISTRIBUTION"
PRINT_ORIENTATION = "FLAT_ON_LARGEST_FACE"


def build_module_clamping_ring_phase3r() -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(0.5 * module_clamping_ring_outer_diameter)
        .circle(0.5 * module_clamping_ring_inner_diameter)
        .extrude(module_clamping_ring_thickness)
    )
    for angle_deg in used_fastener_angles:
        angle = radians(angle_deg)
        x = phase3r_m4_pitch_radius * cos(angle)
        y = phase3r_m4_pitch_radius * sin(angle)
        hole = (
            cq.Workplane("XY")
            .center(x, y)
            .circle(0.5 * m4_clearance_diameter)
            .extrude(module_clamping_ring_thickness + 2.0)
            .translate((0.0, 0.0, -1.0))
        )
        ring = ring.cut(hole)
    return ring
