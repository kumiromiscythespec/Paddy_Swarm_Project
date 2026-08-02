"""Large circular root-mesh foldover ring for Phase 3R."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    root_mesh_foldover_length,
    root_mesh_initial_length,
    root_sleeve_ring_inner_diameter_phase3r,
    root_sleeve_ring_outer_diameter_phase3r,
    root_sleeve_ring_thickness_phase3r,
)


STATUS = "PHASE3R_LARGE_CONTINUOUS_FOLDOVER_RING"
PRINT_ORIENTATION = "FLAT_ON_LARGEST_ANNULAR_FACE"
RETENTION = "MESH_BAG_FOLDED_AROUND_RING_NO_POSITIVE_SNAP"
LOAD_TESTS_PENDING_G = (500, 1000)


def build_root_sleeve_ring_phase3r() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(0.5 * root_sleeve_ring_outer_diameter_phase3r)
        .circle(0.5 * root_sleeve_ring_inner_diameter_phase3r)
        .extrude(root_sleeve_ring_thickness_phase3r)
    )


def build_root_mesh_bag_reference_phase3r() -> cq.Workplane:
    effective_length = root_mesh_initial_length - root_mesh_foldover_length
    return (
        cq.Workplane("XY")
        .circle(0.5 * root_sleeve_ring_inner_diameter_phase3r - 2.0)
        .extrude(effective_length)
        .translate((0.0, 0.0, -effective_length))
    )
