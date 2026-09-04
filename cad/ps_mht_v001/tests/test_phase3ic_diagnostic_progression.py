"""Phase 3I-C strictly additive D01-D05 geometry tests (7)."""

import pytest

from ps_mht_v001.tower_module.floating_region_diagnostics_phase3ic import (
    build_all_diagnostics_phase3ic,
    build_integrated_stage_corrected_phase3ic,
    diagnostic_feature_map_phase3ic,
    diagnostic_geometry_audit_phase3ic,
    retention_lug_boolean_audit_phase3ic,
)


def test_phase3ic_all_diagnostics_are_one_valid_solid() -> None:
    for model in build_all_diagnostics_phase3ic():
        assert len(model.solids().vals()) == 1 and model.val().isValid()


def test_phase3ic_invalid_flag_order_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_integrated_stage_corrected_phase3ic(False, True, False, False)
    with pytest.raises(ValueError):
        build_integrated_stage_corrected_phase3ic(True, False, True, False)


def test_phase3ic_stage_volumes_increase_in_order() -> None:
    stages = diagnostic_geometry_audit_phase3ic()["stages"]
    volumes = [stages[f"D{index:02d}"]["volume_mm3"] for index in range(1, 6)]
    assert volumes == sorted(volumes) and len(set(volumes)) == 5


def test_phase3ic_d02_adds_only_cradle_group() -> None:
    feature = diagnostic_feature_map_phase3ic()["stages"]["D02"]
    assert feature["added_from_previous"] == ["CRADLE_PADS_AND_BUTTRESSES"]


def test_phase3ic_d03_adds_six_complete_retention_lugs() -> None:
    audit = retention_lug_boolean_audit_phase3ic()
    assert audit["lug_count"] == 6
    assert audit["retention_increment_mm3"] > 1.0
    assert audit["all_six_visible"] and audit["all_six_holes_penetrating"]
    assert audit["status"] == "PASS"


def test_phase3ic_d04_adds_cascade_and_wick_only() -> None:
    feature = diagnostic_feature_map_phase3ic()["stages"]["D04"]
    assert feature["added_from_previous"] == ["REAR_CASCADE_AND_WICK"]


def test_phase3ic_d05_adds_stacking_guides_only() -> None:
    feature = diagnostic_feature_map_phase3ic()["stages"]["D05"]
    assert feature["added_from_previous"] == ["STACKING_GUIDES_AND_RAMPS"]
    assert diagnostic_feature_map_phase3ic()["strictly_additive_feature_authority"] is True

