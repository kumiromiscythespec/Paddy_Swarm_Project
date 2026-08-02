"""Phase 3A.1 coupon, export, mesh, and immutable-baseline gates."""

from __future__ import annotations

from pathlib import Path

from ps_mht_v001.common.phase_baseline import audit_baseline_hashes
from ps_mht_v001.common.validation import (
    validate_printable_set,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.coupons.complete_port_passage_coupon import (
    COUPON_SOLID_COUNT as COMPLETE_SOLIDS,
    build_complete_port_passage_coupon,
)
from ps_mht_v001.coupons.m3_port_cartridge_fit_coupon import (
    COUPON_SOLID_COUNT as M3_SOLIDS,
    build_m3_port_cartridge_fit_coupon,
)
from ps_mht_v001.coupons.port_receiver_adapter_coupon_phase3a1 import (
    COUPON_SOLID_COUNT as RECEIVER_SOLIDS,
    build_port_receiver_adapter_coupon_phase3a1,
)
from ps_mht_v001.coupons.root_ring_passage_coupon import (
    COUPON_SOLID_COUNT as ROOT_RING_SOLIDS,
    ROOT_RING_CLEARANCES,
    build_root_ring_passage_coupon,
)
from ps_mht_v001.parameters import port_adapter_inner_diameter
from ps_mht_v001.tower_module.root_sleeve_retaining_ring import (
    root_ring_actual_maximum_diameter,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def test_root_ring_actual_clearances_match_all_candidates() -> None:
    for clearance in ROOT_RING_CLEARANCES:
        actual = 0.5 * (
            port_adapter_inner_diameter
            - root_ring_actual_maximum_diameter(clearance)
        )
        assert abs(actual - clearance) <= 0.01


def test_all_four_phase3a1_coupons_fit_a1() -> None:
    validate_printable_set(
        build_port_receiver_adapter_coupon_phase3a1(),
        "receiver_phase3a1",
        RECEIVER_SOLIDS,
    )
    validate_printable_set(
        build_m3_port_cartridge_fit_coupon(),
        "m3_phase3a1",
        M3_SOLIDS,
    )
    validate_printable_set(
        build_complete_port_passage_coupon(),
        "complete_phase3a1",
        COMPLETE_SOLIDS,
    )
    validate_printable_set(
        build_root_ring_passage_coupon(),
        "root_ring_phase3a1",
        ROOT_RING_SOLIDS,
    )


def test_phase3a1_exported_steps_reimport_valid() -> None:
    expected = {
        "ps_mht_v001_planting_port_adapter_phase3a1.step": 1,
        "ps_mht_v001_m3_port_nut_cartridge_phase3a1.step": 1,
        "ps_mht_v001_m3_port_nut_cartridge_retainer_phase3a1.step": 1,
        "ps_mht_v001_root_sleeve_retaining_ring_phase3a1.step": 1,
        "ps_mht_v001_complete_port_assembly_phase3a1.step": 14,
        "ps_mht_v001_complete_port_exploded_phase3a1.step": 14,
        "ps_mht_v001_complete_port_passage_probe_phase3a1.step": 1,
    }
    for name, count in expected.items():
        metrics = validate_step_round_trip(EXPORT_ROOT / "step" / name, count)
        assert metrics.all_solids_valid


def test_phase3a1_exported_stls_are_closed_manifolds() -> None:
    names = (
        "ps_mht_v001_planting_port_adapter_phase3a1.stl",
        "ps_mht_v001_m3_port_nut_cartridge_phase3a1.stl",
        "ps_mht_v001_m3_port_nut_cartridge_retainer_phase3a1.stl",
        "ps_mht_v001_root_sleeve_retaining_ring_phase3a1.stl",
        "ps_mht_v001_m3_port_cartridge_fit_coupon_phase3a1.stl",
        "ps_mht_v001_port_receiver_adapter_coupon_phase3a1.stl",
        "ps_mht_v001_complete_port_passage_coupon_phase3a1.stl",
        "ps_mht_v001_root_ring_passage_coupon_phase3a1.stl",
    )
    for name in names:
        assert validate_stl_mesh(EXPORT_ROOT / "stl" / name).closed_manifold


def test_phase1_through_phase3a_hashes_remain_unchanged() -> None:
    audit = audit_baseline_hashes(EXPORT_ROOT)
    assert all(item["unchanged"] for item in audit.values())
