"""Phase 3I-D translation, rotation and falling-stream envelope tests (7)."""

from ps_mht_v001.tower_module.positive_interstage_cascade_phase3id import (
    COMBINED_TANGENTIAL_SHIFT_MM,
    NOMINAL_TANGENTIAL_MARGIN_PER_SIDE_MM,
    receiver_tolerance_audit_phase3id,
    water_stream_envelope_audit_phase3id,
)


def test_phase3id_exactly_eight_misalignment_cases_are_audited() -> None:
    assert len(receiver_tolerance_audit_phase3id()["cases"]) == 8


def test_phase3id_all_misalignment_cases_pass() -> None:
    assert receiver_tolerance_audit_phase3id()["all_cases_pass"]


def test_phase3id_plus_minus_2mm_translation_cases_pass() -> None:
    cases = receiver_tolerance_audit_phase3id()["cases"]
    assert all(cases[name]["pass"] for name in ("X_PLUS_2", "X_MINUS_2", "Y_PLUS_2", "Y_MINUS_2"))


def test_phase3id_plus_minus_2degree_rotation_cases_pass() -> None:
    cases = receiver_tolerance_audit_phase3id()["cases"]
    assert cases["ROT_PLUS_2"]["pass"] and cases["ROT_MINUS_2"]["pass"]


def test_phase3id_combined_translation_rotation_cases_pass() -> None:
    cases = receiver_tolerance_audit_phase3id()["cases"]
    assert cases["Y_PLUS_2_ROT_PLUS_2"]["pass"]
    assert cases["Y_MINUS_2_ROT_MINUS_2"]["pass"]
    assert COMBINED_TANGENTIAL_SHIFT_MM < NOMINAL_TANGENTIAL_MARGIN_PER_SIDE_MM


def test_phase3id_worst_stream_envelope_is_inside_receiver() -> None:
    audit = water_stream_envelope_audit_phase3id()
    assert audit["receiver_planar_envelope_contains_stream"]
    assert audit["uncaptured_volume_mm3"] <= 1.0e-5


def test_phase3id_envelope_is_not_cfd_and_misses_central_hole() -> None:
    audit = water_stream_envelope_audit_phase3id()
    assert not audit["cfd_performed"]
    assert audit["central_dry_opening_clear"]

