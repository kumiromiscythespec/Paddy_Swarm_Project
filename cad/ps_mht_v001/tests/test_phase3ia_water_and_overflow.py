"""Phase 3I-A actual water-volume and open-flow tests (8)."""

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
    OPERATING_DEPTH_CANDIDATES_MM,
    OVERFLOW_MINIMUM_OPEN_THROAT_MM,
    REAR_CHANNEL_WIDTH_MM,
    SELECTED_OPERATING_DEPTH_MM,
    WICK_PASSAGE_WIDTH_MM,
    build_water_volume_phase3ia,
    overflow_audit_phase3ia,
    stage_geometry_requirements_phase3ia,
    water_volume_audit_phase3ia,
)


def test_phase3ia_water_depth_candidates_are_18_19_20mm() -> None:
    assert OPERATING_DEPTH_CANDIDATES_MM == (18.0, 19.0, 20.0)


def test_phase3ia_water_volumes_are_boolean_actuals() -> None:
    audit = water_volume_audit_phase3ia()
    values = [audit["candidates"][key]["actual_water_volume_l"] for key in ("d18", "d19", "d20")]
    assert values[0] < values[1] < values[2]
    assert all(len(build_water_volume_phase3ia(depth).solids().vals()) == 1 for depth in OPERATING_DEPTH_CANDIDATES_MM)


def test_phase3ia_selected_water_volume_is_within_0_35_to_0_45_l() -> None:
    selected = water_volume_audit_phase3ia()["candidates"]["d20"]["actual_water_volume_l"]
    assert 0.35 <= selected <= 0.45


def test_phase3ia_20mm_depth_is_selected_and_18mm_is_rejected_low() -> None:
    audit = water_volume_audit_phase3ia()
    assert SELECTED_OPERATING_DEPTH_MM == 20.0
    assert not audit["candidates"]["d18"]["within_target_range"]
    assert audit["candidates"]["d20"]["within_target_range"]


def test_phase3ia_root_wick_passage_is_open_and_access_width_is_16mm() -> None:
    assert WICK_PASSAGE_WIDTH_MM == 16.0
    assert stage_geometry_requirements_phase3ia()["closed_waterways"] == 0


def test_phase3ia_rear_channel_is_open_and_at_least_20mm_wide() -> None:
    assert REAR_CHANNEL_WIDTH_MM >= 20.0
    assert stage_geometry_requirements_phase3ia()["uncleanable_cavities"] == 0


def test_phase3ia_overflow_is_open_weir_not_small_closed_drain() -> None:
    audit = overflow_audit_phase3ia()
    assert audit["type"] == "OPEN_WEIR"
    assert audit["small_diameter_drain"] is False
    assert audit["closed_siphon"] is False
    assert audit["minimum_open_throat_mm"] >= OVERFLOW_MINIMUM_OPEN_THROAT_MM


def test_phase3ia_overflow_reports_all_required_rates_without_fake_cfd() -> None:
    audit = overflow_audit_phase3ia()
    assert set(audit["flow_review"]) == {"0.5_L_min", "1.0_L_min", "2.0_L_min_transient"}
    assert audit["cfd_performed"] is False
