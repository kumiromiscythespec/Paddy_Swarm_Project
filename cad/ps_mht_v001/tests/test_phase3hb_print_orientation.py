"""Phase 3H-B print-posture prohibition tests (6)."""

from ps_mht_v001 import phase3hb_state as state


def test_phase3hb_lower_receiver_and_hard_stop_face_up() -> None:
    assert state.LOWER_PRINT_ORIENTATION == "ASSEMBLY_Z_RECEIVER_AND_HARD_STOP_UP"


def test_phase3hb_upper_skirt_and_hard_stop_face_up() -> None:
    assert state.UPPER_PRINT_ORIENTATION == "ASSEMBLY_ORIENTATION_ROTATED_X_180_SKIRT_UP"


def test_phase3hb_sideways_and_angled_prints_are_prohibited() -> None:
    assert not state.SIDEWAYS_PRINT_ALLOWED
    assert not state.ANGLED_PRINT_ALLOWED


def test_phase3hb_automatic_support_is_prohibited() -> None:
    assert not state.AUTOMATIC_SUPPORT_ALLOWED


def test_phase3hb_split_and_sectorization_are_prohibited() -> None:
    assert not state.RING_SPLIT_ALLOWED
    assert not state.SECTORIZATION_ALLOWED


def test_phase3hb_has_no_auxiliary_feet_or_cad_brim() -> None:
    assert state.AUXILIARY_FEET_COUNT == 0
    assert state.CAD_BRIM_COUNT == 0
    assert state.SLICER_BRIM_OPTION_MM == (5.0, 8.0)
