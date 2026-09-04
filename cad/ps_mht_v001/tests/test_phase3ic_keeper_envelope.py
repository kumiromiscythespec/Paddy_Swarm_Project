"""Phase 3I-C keeper and installed-pot envelope tests (7)."""

from ps_mht_v001.print_manifest_phase3ic import build_print_manifest_phase3ic
from ps_mht_v001.tower_module.horseshoe_flange_keeper_phase3ic import (
    KEEPER_V2_MAXIMUM_ALLOWED_OUTER_DIAMETER_MM,
    KEEPER_V2_OUTER_DIAMETER_MM,
    NETPOT_FLANGE_OUTER_DIAMETER_MM,
    keeper_v2_envelope_audit_phase3ic,
)


def test_phase3ic_keeper_is_below_107_5mm_limit() -> None:
    assert KEEPER_V2_OUTER_DIAMETER_MM <= KEEPER_V2_MAXIMUM_ALLOWED_OUTER_DIAMETER_MM


def test_phase3ic_keeper_does_not_exceed_108mm_flange() -> None:
    assert KEEPER_V2_OUTER_DIAMETER_MM < NETPOT_FLANGE_OUTER_DIAMETER_MM


def test_phase3ic_keeper_adds_zero_installed_envelope() -> None:
    audit = keeper_v2_envelope_audit_phase3ic()
    assert audit["envelope_increase_mm"] == 0.0
    assert audit["installed_netpot_envelope_with_keeper_mm"] == audit["installed_netpot_envelope_before_mm"]


def test_phase3ic_installed_pot_remains_below_238mm() -> None:
    audit = keeper_v2_envelope_audit_phase3ic()
    assert audit["installed_netpot_envelope_with_keeper_mm"] <= audit["maximum_allowed_total_xy_mm"]


def test_phase3ic_keeper_leaves_plant_center_open() -> None:
    assert keeper_v2_envelope_audit_phase3ic()["plant_center_open"] is True


def test_phase3ic_keeper_is_flat_and_support_free() -> None:
    audit = keeper_v2_envelope_audit_phase3ic()
    assert audit["print_orientation"] == "FLAT_Z_THICKNESS"
    assert audit["support"] == "NONE"


def test_phase3ic_keeper_manifest_prints_one_part_alone() -> None:
    keeper = build_print_manifest_phase3ic()["keeper"]
    assert keeper["quantity_initial"] == 1
    assert keeper["print_alone"] is True
    assert keeper["status"] == "READY_FIRST_LOW_COST_PHYSICAL_FIT"

