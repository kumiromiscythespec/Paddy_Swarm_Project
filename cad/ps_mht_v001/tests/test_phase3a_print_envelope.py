"""Phase 3A printable-part, coupon, and immutable-output gates."""

from __future__ import annotations

from pathlib import Path

from ps_mht_v001.common.phase_baseline import audit_baseline_hashes
from ps_mht_v001.common.validation import (
    validate_printable_set,
    validate_single_printable,
)
from ps_mht_v001.coupons.angled_port_print_coupon import (
    build_angled_port_print_coupon,
)
from ps_mht_v001.coupons.gasket_compression_leak_coupon import (
    COUPON_SOLID_COUNT as GASKET_SOLIDS,
    build_gasket_compression_leak_coupon,
)
from ps_mht_v001.coupons.index_key_fit_coupon import (
    COUPON_SOLID_COUNT as KEY_SOLIDS,
    build_index_key_fit_coupon,
)
from ps_mht_v001.coupons.m4_cartridge_fit_coupon import (
    COUPON_SOLID_COUNT as M4_SOLIDS,
    build_m4_cartridge_fit_coupon,
)
from ps_mht_v001.coupons.netpot_adapter_coupon import (
    COUPON_SOLID_COUNT as NETPOT_SOLIDS,
    build_netpot_adapter_coupon,
)
from ps_mht_v001.coupons.port_receiver_adapter_coupon import (
    COUPON_SOLID_COUNT as RECEIVER_SOLIDS,
    build_port_receiver_adapter_coupon,
)
from ps_mht_v001.tower_module.blank_port_cap import build_blank_port_cap
from ps_mht_v001.tower_module.netpot_60_adapter import build_netpot_60_adapter
from ps_mht_v001.tower_module.planting_port import (
    build_planting_module_with_ports_phase3a,
    build_planting_port_receiver,
)
from ps_mht_v001.tower_module.planting_port_adapter import (
    build_planting_port_adapter,
)
from ps_mht_v001.tower_module.root_sleeve_retaining_ring import (
    build_root_sleeve_retaining_ring,
)


def test_phase3a_primary_printed_parts_fit_a1() -> None:
    parts = {
        "module": build_planting_module_with_ports_phase3a(),
        "receiver": build_planting_port_receiver(),
        "common_adapter": build_planting_port_adapter(),
        "netpot_adapter": build_netpot_60_adapter(),
        "blank_cap": build_blank_port_cap(),
        "root_ring": build_root_sleeve_retaining_ring(),
    }
    for name, part in parts.items():
        validate_single_printable(part, name)


def test_phase2_helper_coupons_fit_a1() -> None:
    validate_printable_set(build_index_key_fit_coupon(), "key", KEY_SOLIDS)
    validate_printable_set(build_m4_cartridge_fit_coupon(), "m4", M4_SOLIDS)
    validate_printable_set(
        build_gasket_compression_leak_coupon(),
        "gasket",
        GASKET_SOLIDS,
    )


def test_phase3a_port_coupons_fit_a1() -> None:
    validate_printable_set(
        build_netpot_adapter_coupon(),
        "netpot",
        NETPOT_SOLIDS,
    )
    validate_printable_set(
        build_port_receiver_adapter_coupon(),
        "receiver",
        RECEIVER_SOLIDS,
    )
    validate_single_printable(
        build_angled_port_print_coupon(),
        "angled_port",
    )


def test_phase1_and_phase2_output_hashes_are_unchanged() -> None:
    package_root = Path(__file__).resolve().parents[1]
    audit = audit_baseline_hashes(package_root / "exports")
    assert audit["phase1"]["unchanged"]
    assert audit["phase2"]["unchanged"]


def test_full_module_name_contract_forbids_uncalibrated_printing() -> None:
    from ps_mht_v001.tower_module.planting_port import DO_NOT_PRINT_STATUS

    assert DO_NOT_PRINT_STATUS == "DO_NOT_PRINT_UNTIL_CALIBRATION"
