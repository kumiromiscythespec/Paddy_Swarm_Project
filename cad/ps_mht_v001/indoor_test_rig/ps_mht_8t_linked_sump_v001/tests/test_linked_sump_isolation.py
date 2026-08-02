"""Isolation ordering and shared-zone behavior tests (7)."""

from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001 import parameters as p
from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.reference_cad import (
    isolation_reference_metadata,
)
from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.water_balance import (
    build_water_balance_report,
)


def test_isolation_sequence_is_fixed_in_safe_order() -> None:
    assert p.ISOLATION_SEQUENCE == (
        "CLOSE_UPPER_SUPPLY",
        "WAIT_FOR_TOWER_DRAIN_TO_LOCAL_SUMP",
        "CONFIRM_LOCAL_LEVEL_STABLE",
        "CLOSE_EQUALIZATION_VALVE",
        "DISCONNECT_OR_SERVICE_TOWER_AND_SUMP",
    )


def test_equalization_first_isolation_is_prohibited() -> None:
    assert p.equalization_first_isolation_allowed is False


def test_reconnection_sequence_checks_cleanliness_chemistry_and_leaks() -> None:
    assert p.RECONNECTION_SEQUENCE[0:3] == (
        "VERIFY_SUMP_CLEAN",
        "VERIFY_EC_AND_PH_COMPATIBLE",
        "MATCH_LOCAL_WATER_LEVEL_TO_ZONE",
    )
    assert "CHECK_FOR_LEAKS" in p.RECONNECTION_SEQUENCE
    assert p.RECONNECTION_SEQUENCE[-1] == "CONFIRM_RETURN_FLOW"


def test_each_of_eight_branches_has_both_individual_valves() -> None:
    assert p.equalization_valve_count == 8
    assert p.upper_supply_valve_count == 8
    assert p.branch_identifiers == tuple("ABCDEFGH")


def test_one_branch_isolation_does_not_disconnect_other_branches() -> None:
    metadata = isolation_reference_metadata()
    assert metadata["equalization_closure_does_not_disconnect_other_branches"] is True


def test_shared_nutrient_zone_constraints_are_explicit() -> None:
    assert "DO_NOT_MIX_DIFFERENT_FERTILIZER_CONCENTRATIONS" in p.shared_zone_constraints
    assert "ISOLATE_SUSPECTED_DISEASE_IMMEDIATELY" in p.shared_zone_constraints
    assert "CLEANING_DOES_NOT_REDUCE_DISEASE_TRANSMISSION_RISK_TO_ZERO" in p.shared_zone_constraints


def test_supply_misopen_routes_to_noncirculating_overflow() -> None:
    case = build_water_balance_report()["upper_supply_mistakenly_open_during_isolation"]
    assert case["equalization_valve_state"] == "CLOSED"
    assert case["route"] == "LOCAL_HIGH_OVERFLOW_TO_NON_CIRCULATING_RECEIVER"
