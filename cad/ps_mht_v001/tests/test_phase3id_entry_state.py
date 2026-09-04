"""Phase 3I-D entry, frozen baseline and authorization tests (7)."""

from ps_mht_v001 import phase3id_state as state


def test_phase3id_process_name() -> None:
    assert state.PHASE3ID_PROCESS_NAME.startswith("PHASE_3ID_POSITIVE_INTERSTAGE")


def test_phase3ic_interstage_defect_is_recorded() -> None:
    defect = state.PHASE3IC_INTERSTAGE_TRANSFER
    assert defect["lower_positive_receiver"] == "ABSENT"
    assert defect["guaranteed_transfer"] == "FAIL"


def test_phase3ic_is_frozen_hydraulically_incomplete() -> None:
    frozen = state.PHASE3IC_FROZEN_BASELINE
    assert frozen["status"] == "HISTORICAL_HYDRAULICALLY_INCOMPLETE"
    assert frozen["official_artifact_count"] == 46
    assert frozen["mutation"] == "PROHIBITED"


def test_phase3ic_old_d04_d05_and_full_are_prohibited() -> None:
    assert state.PHASE3IC_FROZEN_BASELINE["print"] == "PROHIBITED"
    assert state.PHASE3IC_FROZEN_BASELINE["historical_hydraulically_incomplete"] == ["D04", "D05", "CORRECTED_FULL"]


def test_phase3id_fixed_module_dimensions() -> None:
    assert state.MODULE_HEIGHT_MM == 170.0
    assert state.MAXIMUM_TOTAL_XY_ENVELOPE_MM == 238.0
    assert state.PORT_RECESS_MM == 2.0


def test_phase3id_central_hole_is_not_a_water_route() -> None:
    assert state.CENTRAL_HOLE_WATER_ROUTE is False
    assert state.PHASE3IC_INTERSTAGE_TRANSFER["central_hole_as_water_route"] == "PROHIBITED"


def test_phase3id_does_not_claim_pending_physical_results() -> None:
    assert state.BAMBU_STUDIO_REVIEW == "PENDING"
    assert state.HYDRAULIC_FLOW_TEST == "PENDING"
    assert not state.INTERSTAGE_TRANSFER_PASS
    assert not state.FULL_STAGE_PRINT_APPROVED

