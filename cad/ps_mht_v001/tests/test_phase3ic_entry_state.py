"""Phase 3I-C entry, frozen-baseline, and authorization tests (7)."""

from ps_mht_v001 import phase3ic_state as state


def test_phase3ic_process_name() -> None:
    assert state.PHASE3IC_PROCESS_NAME == "PHASE_3IC_ENVELOPE_NEUTRAL_POT_RETENTION_AND_FLOATING_REGION_ISOLATION"


def test_phase3ib_floating_warning_is_recorded() -> None:
    assert state.PHASE3IB_REVIEW["full_stage_bambu_review"] == "FAIL_FLOATING_REGION_WARNING"
    assert state.PHASE3IB_REVIEW["full_stage_print"] == "PROHIBITED"


def test_phase3ib_is_frozen_historical_failed_baseline() -> None:
    frozen = state.PHASE3IB_FROZEN_BASELINE
    assert frozen["status"] == "HISTORICAL_FAILED_BASELINE"
    assert frozen["official_artifacts_count"] == 46
    assert frozen["mutation"] == "PROHIBITED"


def test_phase3ib_retention_boolean_defect_is_recorded() -> None:
    defect = state.PHASE3IB_FROZEN_BASELINE["retention_lug_boolean"]
    assert defect["intended"] == "SIX_COMPLETE_LUGS"
    assert defect["actual_increment_mm3"] < 0.1
    assert defect["result"] == "FAILED_OR_NEAR_TANGENTIAL_FUSE"


def test_phase3ic_normal_completion_status_lines() -> None:
    assert "PHASE3IC_CORRECTED_FULL_AUTHORITY_CREATED" in state.PHASE3IC_STATUS_LINES
    assert "COMPLETE_RETENTION_LUGS_IMPLEMENTED" in state.PHASE3IC_STATUS_LINES
    assert "BAMBU_STUDIO_DIAGNOSTIC_PENDING" in state.PHASE3IC_STATUS_LINES


def test_phase3ic_fixed_dimensions_and_recess() -> None:
    assert state.MODULE_HEIGHT_MM == 170.0
    assert state.NOMINAL_BODY_OUTER_DIAMETER_MM == 200.0
    assert state.MAXIMUM_TOTAL_XY_ENVELOPE_MM == 238.0
    assert state.PORT_RECESS_MM == 2.0


def test_phase3ic_does_not_claim_unperformed_results() -> None:
    assert not state.FLOATING_REGION_SOURCE_IDENTIFIED
    assert not state.FLOATING_REGION_FIXED
    assert not state.FULL_STAGE_PRINT_APPROVED
    assert not state.NETPOT_RETENTION_PASS
    assert not state.SUMP_WATERTIGHT
    assert not state.OVERFLOW_PASS

