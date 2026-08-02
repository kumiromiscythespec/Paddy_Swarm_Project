"""Phase 3R coupon, orientation layout, export, and SHA gates."""

from __future__ import annotations

from pathlib import Path

from ps_mht_v001.common.phase_baseline import audit_baseline_hashes
from ps_mht_v001.common.validation import (
    validate_printable_set,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.coupons.annular_nut_ring_coupon_phase3r import (
    build_annular_nut_ring_coupon_phase3r,
)
from ps_mht_v001.coupons.large_index_ring_coupon_phase3r import (
    COUPON_SOLID_COUNT as INDEX_SOLIDS,
    LARGE_INDEX_CLEARANCES,
    build_large_index_ring_coupon_phase3r,
)
from ps_mht_v001.coupons.port_function_ring_coupon_phase3r import (
    BODY_CLEARANCE_CANDIDATES,
    COUPON_SOLID_COUNT as PORT_SOLIDS,
    build_port_function_ring_coupon_phase3r,
)
from ps_mht_v001.coupons.self_supporting_port_shell_coupon_phase3r import (
    COUPON_SOLID_COUNT as SHELL_SOLIDS,
    build_self_supporting_port_shell_coupon_set_phase3r,
)
from ps_mht_v001.print_plate_layout_phase3r import (
    PRINT_PLATE_SOLID_COUNT,
    TARGET_ZONE_GAP,
    build_print_plate_layout_phase3r,
    phase3r_plate_positions,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def test_all_four_large_coupon_families_fit_a1() -> None:
    for clearance in LARGE_INDEX_CLEARANCES:
        validate_printable_set(
            build_large_index_ring_coupon_phase3r(clearance),
            f"large_index_{clearance}",
            INDEX_SOLIDS,
        )
    validate_printable_set(
        build_annular_nut_ring_coupon_phase3r(),
        "annular_nut_ring",
        1,
    )
    for clearance in BODY_CLEARANCE_CANDIDATES:
        validate_printable_set(
            build_port_function_ring_coupon_phase3r(clearance),
            f"port_function_{clearance}",
            PORT_SOLIDS,
        )
    validate_printable_set(
        build_self_supporting_port_shell_coupon_set_phase3r(),
        "self_supporting_shell",
        SHELL_SOLIDS,
    )


def test_print_layout_has_eight_oriented_parts_and_15mm_zones() -> None:
    positions = phase3r_plate_positions()
    assert len(positions) == PRINT_PLATE_SOLID_COUNT
    for first, second in zip(positions, positions[1:]):
        first_right = first[1] + 0.5 * first[2]
        second_left = second[1] - 0.5 * second[2]
        assert second_left - first_right >= TARGET_ZONE_GAP - 1.0e-7
    assert len(build_print_plate_layout_phase3r().solids().vals()) == 8


def test_phase3r_exported_steps_reimport_valid() -> None:
    step_dir = EXPORT_ROOT / "step"
    expected = {
        "ps_mht_v001_module_alignment_ring_phase3r.step": 1,
        "ps_mht_v001_module_nut_ring_phase3r.step": 1,
        "ps_mht_v001_module_clamping_ring_phase3r.step": 1,
        "ps_mht_v001_module_gasket_ring_phase3r.step": 1,
        "ps_mht_v001_self_supporting_port_shell_coupon_phase3r.step": 2,
        "ps_mht_v001_port_function_ring_phase3r.step": 1,
        "ps_mht_v001_port_backing_ring_phase3r.step": 1,
        "ps_mht_v001_root_sleeve_ring_phase3r.step": 1,
        "ps_mht_v001_module_pair_0deg_phase3r.step": 11,
        "ps_mht_v001_module_pair_60deg_phase3r.step": 11,
        "ps_mht_v001_module_pair_30deg_misassembly_phase3r.step": 11,
        "ps_mht_v001_port_exploded_phase3r.step": 12,
        "ps_mht_v001_print_plate_layout_phase3r.step": 8,
    }
    for name, solid_count in expected.items():
        metrics = validate_step_round_trip(
            step_dir / name,
            solid_count,
        )
        assert metrics.all_solids_valid


def test_phase3r_exported_stls_are_closed_manifolds() -> None:
    for path in sorted((EXPORT_ROOT / "stl").glob("*phase3r.stl")):
        assert validate_stl_mesh(path).closed_manifold


def test_phase1_through_phase3a1_hashes_are_unchanged() -> None:
    audit = audit_baseline_hashes(EXPORT_ROOT)
    assert all(item["unchanged"] for item in audit.values())
