"""Flexible root-sleeve volume, overlap, service, and extraction checks."""

from __future__ import annotations

from ps_mht_v001.assembly.root_zone_reference_phase3a import (
    SELECTED_PATTERN,
    compare_root_zone_candidates,
)
from ps_mht_v001.parameters import (
    port_receiver_bore_diameter,
    root_sleeve_collapsed_diameter,
    root_sleeve_material_reference,
)
from ps_mht_v001.tower_module.root_sleeve_reference import (
    build_expanded_root_sleeve,
    build_rear_drain_service_volume,
    expanded_root_overlap_volumes,
    expanded_root_volumes_liters,
)


def _volume(model) -> float:
    return sum(solid.Volume() for solid in model.solids().vals())


def test_each_expanded_root_envelope_is_0_7_to_1_0_liter() -> None:
    assert all(0.7 <= volume <= 1.0 for volume in expanded_root_volumes_liters())


def test_three_expanded_root_envelopes_do_not_overlap() -> None:
    assert max(expanded_root_overlap_volumes()) <= 1.0e-8


def test_expanded_roots_do_not_block_rear_drain_service_region() -> None:
    service = build_rear_drain_service_volume()
    for angle in (0.0, 120.0, 240.0):
        assert _volume(build_expanded_root_sleeve(angle).intersect(service)) <= 1.0e-8


def test_collapsed_root_sleeve_fits_through_common_receiver() -> None:
    assert root_sleeve_collapsed_diameter < port_receiver_bore_diameter


def test_root_sleeve_is_purchased_flexible_pp_or_pe_not_printed_mesh() -> None:
    assert root_sleeve_material_reference == "PURCHASED_PP_OR_PE_FLEXIBLE_MESH"


def test_candidate_a_is_retained_after_real_envelope_comparison() -> None:
    comparison = compare_root_zone_candidates()
    assert SELECTED_PATTERN == "A"
    assert max(comparison["A"]["pair_overlap_mm3"]) <= 1.0e-8
    assert max(comparison["B"]["pair_overlap_mm3"]) <= 1.0e-8
    assert comparison["A"]["structure"] != comparison["B"]["structure"]

