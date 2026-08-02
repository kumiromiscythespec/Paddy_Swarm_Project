"""Phase 3H-A physical-result and scoped-entry state tests (7)."""

from ps_mht_v001.parameters import (
    final_port_assembly,
    module_buffer_0_4L_status,
    module_buffer_0_6L_status,
    module_buffer_0_8L_status,
    netpot_20_cycle_test,
    netpot_27deg_retention_test,
    netpot_500g_load_test,
    netpot_body_passage_selected,
    netpot_body_passage_selection_status,
    netpot_c800_status,
    netpot_c810_status,
    netpot_wet_media_test,
    phase3cb0_audit_status,
    phase3cb0_cad_generation,
    scoped_next_phase_cad,
)


def test_phase3ha_c805_physical_body_passage_selection_is_recorded() -> None:
    assert netpot_body_passage_selected == 80.5
    assert netpot_body_passage_selection_status == "PASS_BODY_PASSAGE_PHYSICAL"


def test_phase3ha_c800_and_c810_are_not_required_after_c805_pass() -> None:
    assert netpot_c800_status == "NOT_REQUIRED_AFTER_C805_PASS"
    assert netpot_c810_status == "NOT_REQUIRED_AFTER_C805_PASS"


def test_phase3ha_remaining_netpot_tests_and_final_port_stay_pending() -> None:
    assert {
        netpot_20_cycle_test,
        netpot_27deg_retention_test,
        netpot_wet_media_test,
        netpot_500g_load_test,
    } == {"CALIBRATION_PENDING"}
    assert final_port_assembly == "REDESIGN_REQUIRED"


def test_phase3ha_shallow_0_8_l_buffer_is_rejected() -> None:
    assert (
        module_buffer_0_8L_status
        == "REJECTED_FOR_15_TO_25MM_SHALLOW_BUFFER"
    )


def test_phase3ha_buffer_primary_and_stretch_targets_are_recorded() -> None:
    assert module_buffer_0_4L_status == "PRIMARY_TARGET"
    assert module_buffer_0_6L_status == "STRETCH_TARGET"


def test_phase3ha_phase3cb0_conflict_history_and_cad_prohibition_remain() -> None:
    assert phase3cb0_audit_status == "CONFLICT_FOUND"
    assert phase3cb0_cad_generation == "PROHIBITED"


def test_phase3ha_scoped_next_phase_cad_is_allowed() -> None:
    assert scoped_next_phase_cad == "ALLOWED_WHEN_ENTRY_CONDITIONS_PASS"
