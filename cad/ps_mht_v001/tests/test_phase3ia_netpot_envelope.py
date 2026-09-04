"""Phase 3I-A measured net-pot, recess, and cradle tests (8)."""

from ps_mht_v001.parameters import (
    netpot_siawadeky_flange_outer_diameter,
    netpot_siawadeky_max_body_outer_diameter,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
    CRADLE_SIDE_GUSSET_WIDTH_MM,
    PORT_RECESS_CANDIDATES_MM,
    SELECTED_PORT_RECESS_MM,
    WICK_PASSAGE_WIDTH_MM,
    netpot_recess_audit_phase3ia,
)


def test_phase3ia_measured_flange_is_108mm() -> None:
    assert netpot_siawadeky_flange_outer_diameter == 108.0


def test_phase3ia_measured_body_envelope_is_78_6mm() -> None:
    assert netpot_siawadeky_max_body_outer_diameter == 78.6


def test_phase3ia_recess_candidates_are_2_3_4_5mm() -> None:
    assert PORT_RECESS_CANDIDATES_MM == (2.0, 3.0, 4.0, 5.0)


def test_phase3ia_selects_smallest_geometrically_valid_recess() -> None:
    audit = netpot_recess_audit_phase3ia()
    assert SELECTED_PORT_RECESS_MM == 2.0
    assert audit["selected_recess_mm"] == 2.0


def test_phase3ia_selected_installed_pot_envelope_is_at_most_238mm() -> None:
    selected = netpot_recess_audit_phase3ia()["candidates"]["r02"]
    assert selected["installed_netpot_maximum_xy_mm"] <= 238.0


def test_phase3ia_selected_pots_do_not_intersect_stage_or_each_other() -> None:
    selected = netpot_recess_audit_phase3ia()["candidates"]["r02"]
    assert selected["pot_stage_intersection_volume_mm3"] == 0
    assert selected["pot_pair_intersection_volume_mm3"] == [0, 0, 0]


def test_phase3ia_internal_diameters_are_not_external_envelope_inputs() -> None:
    assert netpot_recess_audit_phase3ia()["inner_diameter_measurements_used_for_external_envelope"] is False


def test_phase3ia_cradle_is_tool_free_with_gussets_and_open_wick_access() -> None:
    selected = netpot_recess_audit_phase3ia()["candidates"]["r02"]
    assert selected["tool_free_removal_geometry"] == "OPEN_TOP_NO_PRINTED_RETENTION"
    assert CRADLE_SIDE_GUSSET_WIDTH_MM >= 6.0
    assert WICK_PASSAGE_WIDTH_MM >= 12.0
