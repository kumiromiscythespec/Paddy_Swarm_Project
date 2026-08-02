"""Large M4 ring, metal retainer, and load-path gates."""

from __future__ import annotations

from math import pi

from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    module_nut_pocket_clearance_candidates,
    module_nut_ring_inner_diameter,
    module_nut_ring_outer_diameter,
    phase3r_min_isolated_footprint,
)
from ps_mht_v001.tower_module.module_nut_ring_phase3r import (
    NUT_POCKET_COUNT,
    RETAINER,
    build_module_nut_retaining_plate_reference_phase3r,
    build_module_nut_ring_phase3r,
)
from ps_mht_v001.tower_module.module_gasket_ring_phase3r import (
    build_module_gasket_groove_void_phase3r,
    build_module_gasket_m4_hole_voids_phase3r,
)


def test_module_nut_ring_is_one_large_a1_safe_flat_part() -> None:
    metrics = measure_shape(build_module_nut_ring_phase3r())
    assert metrics.solid_count == 1 and metrics.all_solids_valid
    assert metrics.size_x == module_nut_ring_outer_diameter
    assert metrics.size_x <= 245.0 and metrics.size_z <= 10.0


def test_module_nut_ring_contains_three_real_clearance_candidates() -> None:
    assert NUT_POCKET_COUNT == 3
    assert module_nut_pocket_clearance_candidates == (0.15, 0.25, 0.35)


def test_module_nut_ring_uses_no_printed_small_gate() -> None:
    assert RETAINER == "COMMERCIAL_METAL_WASHER_OR_REFERENCE_METAL_PLATE"


def test_reference_metal_plate_is_valid_but_not_a_printed_gate() -> None:
    metrics = measure_shape(
        build_module_nut_retaining_plate_reference_phase3r()
    )
    assert metrics.solid_count == 1 and metrics.all_solids_valid
    assert metrics.size_z < 1.0


def test_annular_contact_area_carries_vertical_load() -> None:
    gross_annular_area = 0.25 * pi * (
        module_nut_ring_outer_diameter**2
        - module_nut_ring_inner_diameter**2
    )
    assert gross_annular_area > 5000.0
    assert gross_annular_area > phase3r_min_isolated_footprint


def test_nut_ring_pockets_retain_root_side_floor() -> None:
    ring = build_module_nut_ring_phase3r()
    assert sum(face.Area() for face in ring.faces("<Z").vals()) > 5000.0


def test_module_gasket_groove_does_not_intersect_m4_holes() -> None:
    groove = build_module_gasket_groove_void_phase3r()
    holes = build_module_gasket_m4_hole_voids_phase3r()
    intersection = groove.intersect(holes)
    assert sum(s.Volume() for s in intersection.solids().vals()) <= 1.0e-8
