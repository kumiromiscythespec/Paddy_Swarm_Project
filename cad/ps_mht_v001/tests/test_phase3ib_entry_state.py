"""Phase 3I-B entry and Phase 3I-A failure-state tests (7)."""

from ps_mht_v001 import phase3ib_state as state


def test_phase3ib_process_name_is_fixed() -> None:
    assert state.PHASE3IB_PROCESS_NAME == "PHASE_3IB_INTEGRATED_WET_BASE_FUNCTIONAL_CORRECTION"


def test_phase3ia_failure_status_is_recorded() -> None:
    assert state.PHASE3IA_SLICER_REVIEW["status"] == "FAILED_SLICER_AND_FUNCTIONAL_REVIEW"


def test_phase3ia_slicer_and_functional_failures_are_complete() -> None:
    review = state.PHASE3IA_SLICER_REVIEW
    assert review["floating_region_warning"] == "PRESENT"
    assert review["tree_support_dependency"] == "PRESENT"
    assert review["pot_positive_retention"] == "ABSENT"
    assert review["continuous_inner_sump_dam"] == "ABSENT"
    assert review["actual_water_retention"] == "FAIL"


def test_phase3ia_full_stage_is_prohibited() -> None:
    assert state.PHASE3IA_PRINT_DISPOSITION["full_stage"] == "PROHIBITED"


def test_phase3ia_lower_coupon_is_prohibited() -> None:
    assert state.PHASE3IA_PRINT_DISPOSITION["lower_60mm_coupon"] == "PROHIBITED"


def test_phase3ib_normal_status_lines_are_present() -> None:
    assert "REAL_ANNULAR_SUMP_IMPLEMENTED" in state.PHASE3IB_STATUS_LINES
    assert "SELF_SUPPORTING_CRADLE_IMPLEMENTED" in state.PHASE3IB_STATUS_LINES
    assert "NETPOT_RETENTION_INTERFACE_IMPLEMENTED" in state.PHASE3IB_STATUS_LINES
    assert "PHYSICAL_PRINT_PENDING" in state.PHASE3IB_STATUS_LINES


def test_phase3ib_does_not_claim_physical_approval() -> None:
    assert state.BAMBU_STUDIO_REVIEW_STATUS == "PENDING"
    assert not state.FULL_STAGE_PRINT_APPROVED
    assert not state.SUMP_WATERTIGHT
    assert not state.OVERFLOW_PASS
    assert not state.NETPOT_RETENTION_PASS

