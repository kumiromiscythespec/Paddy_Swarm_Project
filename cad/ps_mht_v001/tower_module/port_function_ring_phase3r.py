"""Flat-print circular planting-port structure ring for Phase 3R."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    m4_clearance_diameter,
    phase3r_min_small_hole_surround,
    port_function_ring_fastener_pitch,
    port_function_ring_inner_diameter,
    port_function_ring_outer_diameter,
    port_function_ring_thickness,
)


STATUS = "PHASE3R_FLAT_PRINT_CIRCULAR_FUNCTION_DATUM"
PRINT_ORIENTATION = "FLAT_ON_LARGEST_ANNULAR_FACE"
ROUNDNESS_DATUM = "GENERATED_IN_FLAT_XY_PLANE"


def build_port_function_ring_phase3r() -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(0.5 * port_function_ring_outer_diameter)
        .circle(0.5 * port_function_ring_inner_diameter)
        .extrude(port_function_ring_thickness)
    )
    for y in (-port_function_ring_fastener_pitch, port_function_ring_fastener_pitch):
        hole = (
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(0.5 * m4_clearance_diameter)
            .extrude(port_function_ring_thickness + 2.0)
            .translate((0.0, 0.0, -1.0))
        )
        ring = ring.cut(hole)
    return ring


def port_function_ring_minimum_hole_surround() -> float:
    bore_radius = 0.5 * m4_clearance_diameter
    inner_margin = (
        port_function_ring_fastener_pitch
        - bore_radius
        - 0.5 * port_function_ring_inner_diameter
    )
    outer_margin = (
        0.5 * port_function_ring_outer_diameter
        - port_function_ring_fastener_pitch
        - bore_radius
    )
    result = min(inner_margin, outer_margin)
    assert result >= phase3r_min_small_hole_surround
    return result
