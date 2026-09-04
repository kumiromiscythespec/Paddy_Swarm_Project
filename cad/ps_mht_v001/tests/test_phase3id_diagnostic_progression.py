"""Phase 3I-D frozen D01-D03 and additive D04D-D05D tests (7)."""

import pytest

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3id import (
    build_integrated_stage_full_corrected_phase3id,
    build_integrated_stage_phase3id,
    build_phase3id_diag_05d,
    geometry_audit_phase3id,
    phase3id_phase3ic_geometry_delta_audit,
)


def test_phase3id_d01_through_d03_are_exact_phase3ic_authority() -> None:
    delta = phase3id_phase3ic_geometry_delta_audit()
    assert delta["phase3ic_d01_unchanged"]
    assert delta["phase3ic_d02_unchanged"]
    assert delta["phase3ic_d03_unchanged"]


def test_phase3id_d04d_adds_positive_cascade_to_d03() -> None:
    stages = geometry_audit_phase3id()["stages"]
    assert stages["D04D"]["volume_mm3"] > stages["D03"]["volume_mm3"]


def test_phase3id_d05d_adds_stacking_guides_to_d04d() -> None:
    stages = geometry_audit_phase3id()["stages"]
    assert stages["D05D"]["volume_mm3"] > stages["D04D"]["volume_mm3"]


def test_phase3id_all_progression_stages_are_one_valid_solid() -> None:
    assert all(item["solid_count"] == 1 and item["all_solids_valid"] for item in geometry_audit_phase3id()["stages"].values())


def test_phase3id_d05d_equals_corrected_full() -> None:
    equivalence = geometry_audit_phase3id()["d05d_corrected_full_equivalence"]
    assert equivalence["within_tolerance"]
    assert build_phase3id_diag_05d().val().isSame(build_integrated_stage_full_corrected_phase3id().val())


def test_phase3id_old_phase3ic_d04_d05_are_excluded() -> None:
    assert geometry_audit_phase3id()["old_phase3ic_d04_d05_excluded"]


def test_phase3id_invalid_optional_flag_orders_are_rejected() -> None:
    with pytest.raises(ValueError):
        build_integrated_stage_phase3id(False, True, False, False)
    with pytest.raises(ValueError):
        build_integrated_stage_phase3id(True, True, False, True)

