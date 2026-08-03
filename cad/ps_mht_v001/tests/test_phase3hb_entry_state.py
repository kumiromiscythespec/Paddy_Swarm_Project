"""Phase 3H-B entry and physical-state tests (7)."""

from ps_mht_v001 import phase3hb_state as state


def test_phase3hb_arc_candidate_is_c050() -> None:
    assert state.phase3ha_arc_candidate_selected == "C050"


def test_phase3hb_arc_radial_clearance_is_point_five() -> None:
    assert state.phase3ha_arc_radial_clearance_mm == 0.50


def test_phase3hb_preferred_arc_pairing_is_hole_1_record_only() -> None:
    assert state.phase3ha_preferred_pairing_orientation == "HOLE_1"
    assert state.PREFERRED_PAIRING_IS_PHYSICAL_RECORD_ONLY
    assert not state.HOLE_OR_KEY_ADDED_TO_FULL_RING


def test_phase3hb_arc_physical_status_is_pass() -> None:
    result = state.phase3ha_arc_physical_result_phase3hb()
    assert result["status"] == "PASS"
    assert result["user_check_items_1_to_5"] == "ALL_PASS"


def test_phase3hb_radius_correction_is_not_required() -> None:
    result = state.phase3ha_arc_physical_result_phase3hb()
    assert result["cad_radius_correction"] == "NOT_REQUIRED"
    assert result["free_arc_springback"]["disposition"] == "ACCEPTABLE"


def test_phase3hb_production_selection_is_none() -> None:
    selection = state.production_selection_state_phase3hb()
    assert selection["horizontal_joint_clearance_mm"] is None


def test_phase3hb_full_ring_compression_and_water_are_pending() -> None:
    selection = state.production_selection_state_phase3hb()
    assert selection["full_ring_physical_status"] == "PENDING"
    assert selection["compression_ring_physical_status"] == "PENDING"
    assert selection["water_leak_status"] == "PENDING"
