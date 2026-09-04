"""Phase 3I-A process and supersession state tests (8)."""

from ps_mht_v001 import phase3ia_state as state


def test_phase3ia_process_name() -> None:
    assert state.PHASE3IA_PROCESS_NAME == "PHASE_3IA_INTEGRATED_WET_BASE_MODULE"


def test_phase3ia_interstage_joint_is_not_watertight() -> None:
    assert state.INTERSTAGE_INTERFACE == "DRY_POSITIONING_ONLY"
    assert state.INTERSTAGE_WATERTIGHT_REQUIRED is False


def test_phase3ia_compression_ring_is_superseded() -> None:
    assert state.COMPRESSION_RING_V1_STATUS == "SUPERSEDED_BY_PHASE_3IA"
    assert state.COMPRESSION_RING_V2_IMPLEMENTATION is False


def test_phase3ia_second_compression_ring_is_not_required() -> None:
    assert state.SECOND_COMPRESSION_RING_PRINT_REQUIRED is False


def test_phase3ia_c050_is_dry_reference_at_point_five_per_side() -> None:
    assert state.C050_DRY_STACKING_CLEARANCE_REFERENCE_MM_PER_SIDE == 0.50
    assert state.C050_IS_WATERTIGHT_SELECTION is False


def test_phase3ia_phase3h_physical_results_are_recorded() -> None:
    result = state.phase3h_physical_results_phase3ia()
    assert result["c050_arc"]["assembly"] == "PASS"
    assert result["c050_full_ring"]["repeated_cycles"] == 20
    assert result["c050_full_ring"]["mechanical_status"] == "PASS"
    assert result["compression_ring_v1"]["lateral_centering"] == "FAIL"


def test_phase3ia_physical_and_production_approvals_remain_false() -> None:
    assert not state.FULL_STAGE_PRINT_APPROVED
    assert not state.WATER_TIGHT
    assert not state.OVERFLOW_PASS
    assert not state.PLANT_READY
    assert not state.PRODUCTION_READY


def test_phase3ia_bambu_studio_review_is_pending() -> None:
    assert state.BAMBU_STUDIO_REVIEW_STATUS == "BAMBU_STUDIO_REVIEW_PENDING"
