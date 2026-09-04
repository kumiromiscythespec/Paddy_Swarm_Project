from ps_mht_v001.phase3if_state import (
    LEGACY_REAR_FIXING_STATUS,
    PHASE3IE_60DEG_PARTIAL_STATUS,
    PHASE3IF_PROCESS_NAME,
    PHASE3IF_STATUS_LINES,
    STAGE_ABSOLUTE_ROTATIONS_DEG,
    STAGE_RELATIVE_ROTATION_DEG,
)
from ps_mht_v001.fixtures import stack_clocking_gauge_60deg_phase3ie as old_gauge


def test_phase3if_process_name():
    assert "NON_ROTATING_DRY_CORE_FRAME" in PHASE3IF_PROCESS_NAME


def test_phase3if_relative_rotation_is_30():
    assert STAGE_RELATIVE_ROTATION_DEG == 30.0


def test_phase3if_five_stage_rotations():
    assert STAGE_ABSOLUTE_ROTATIONS_DEG == (0.0, 30.0, 60.0, 90.0, 120.0)


def test_phase3if_legacy_fixing_superseded():
    assert LEGACY_REAR_FIXING_STATUS == "SUPERSEDED_BY_NON_ROTATING_DRY_CORE_FRAME"


def test_phase3if_old_sixty_source_aborted():
    assert PHASE3IE_60DEG_PARTIAL_STATUS == "ABORTED_PARTIAL_SOURCE"
    assert old_gauge.PARTIAL_SOURCE_STATUS == "ABORTED_PARTIAL_SOURCE"


def test_phase3if_old_sixty_source_not_authoritative():
    assert old_gauge.AUTHORITATIVE is False


def test_phase3if_old_sixty_source_excluded_from_delivery():
    assert old_gauge.NOT_FOR_COMMIT and old_gauge.NOT_FOR_ZIP


def test_phase3if_completion_statuses_are_explicit():
    assert "NON_ROTATING_DRY_CORE_FRAME_IMPLEMENTED" in PHASE3IF_STATUS_LINES
    assert "FULL_STAGE_PRINT_PROHIBITED" in PHASE3IF_STATUS_LINES

