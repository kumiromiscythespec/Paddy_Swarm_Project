"""Printed retaining ring for a purchased flexible root sleeve."""

from __future__ import annotations

from math import hypot

import cadquery as cq

from ps_mht_v001.parameters import (
    root_sleeve_retaining_ring_inner_diameter,
    root_sleeve_retaining_ring_thickness,
    port_adapter_inner_diameter,
    root_ring_passage_clearance,
)


MATERIAL = "PRINTED_PETG"


def build_root_sleeve_retaining_ring(
    clearance: float = root_ring_passage_clearance,
) -> cq.Workplane:
    maximum_diameter = port_adapter_inner_diameter - 2.0 * clearance
    # Keep the continuous ring wall substantial while the rounded local tabs
    # remain the tab-inclusive maximum used by the passage calibration.
    base_outer_diameter = maximum_diameter - 0.4
    ring = (
        cq.Workplane("XY")
        .circle(0.5 * base_outer_diameter)
        .circle(0.5 * root_sleeve_retaining_ring_inner_diameter)
        .extrude(root_sleeve_retaining_ring_thickness)
    )
    tab_radius = 1.0
    tab_center_radius = (
        0.5 * maximum_diameter - tab_radius
    )
    for angle in (0.0, 120.0, 240.0):
        tab = (
            cq.Workplane("XY")
            .center(tab_center_radius, 0.0)
            .circle(tab_radius)
            .extrude(root_sleeve_retaining_ring_thickness)
            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle)
        )
        ring = ring.union(tab)
    return ring


def root_ring_actual_maximum_diameter(
    clearance: float = root_ring_passage_clearance,
) -> float:
    """Measure the tab-inclusive radial diameter from real tessellation."""

    maximum = 0.0
    for solid in build_root_sleeve_retaining_ring(clearance).solids().vals():
        vertices, _ = solid.tessellate(0.05, 0.1)
        maximum = max(maximum, *(hypot(v.x, v.y) for v in vertices))
    return 2.0 * maximum
