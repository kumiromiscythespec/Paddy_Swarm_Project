"""Continuous wave-ring geometry and misassembly gates."""

from __future__ import annotations

from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    index_design_type,
    large_ring_clearance_candidates,
    phase3r_min_root_thickness,
    wave_amplitude,
    wave_lobe_count,
    wave_ring_base_radius,
    wave_ring_height,
    wave_ring_inner_diameter,
)
from ps_mht_v001.tower_module.module_alignment_ring_phase3r import (
    alignment_interference_volume,
    build_module_alignment_ring_phase3r,
    build_module_alignment_socket_ring_phase3r,
    build_wide_three_key_candidate_phase3r,
    minimum_wave_curvature_radius,
)


def test_wave_ring_is_selected_over_three_key_candidate() -> None:
    assert index_design_type == "SIX_LOBE_CONTINUOUS_WAVE_RING"
    assert measure_shape(build_wide_three_key_candidate_phase3r()).solid_count == 1


def test_wave_ring_is_one_continuous_valid_solid() -> None:
    metrics = measure_shape(build_module_alignment_ring_phase3r())
    assert metrics.solid_count == 1
    assert metrics.all_solids_valid
    assert wave_lobe_count == 6


def test_wave_ring_root_width_and_thickness_exceed_minimums() -> None:
    radial_root = (
        wave_ring_base_radius
        - wave_amplitude
        - 0.5 * wave_ring_inner_diameter
    )
    assert radial_root >= 15.0
    assert wave_ring_height >= phase3r_min_root_thickness
    assert minimum_wave_curvature_radius() >= 2.0


def test_zero_and_sixty_degree_wave_rings_fully_seat() -> None:
    assert alignment_interference_volume(0.0) <= 1.0e-8
    assert alignment_interference_volume(60.0) <= 1.0e-8


def test_thirty_degree_wave_ring_cannot_fully_seat() -> None:
    assert alignment_interference_volume(30.0) > 1000.0


def test_all_wave_ring_clearance_candidates_are_valid_and_a1_safe() -> None:
    for clearance in large_ring_clearance_candidates:
        metrics = measure_shape(
            build_module_alignment_socket_ring_phase3r(clearance)
        )
        assert metrics.solid_count == 1
        assert metrics.all_solids_valid
        assert metrics.size_x <= 245.0
        assert metrics.size_y <= 245.0
