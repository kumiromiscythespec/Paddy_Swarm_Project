"""Phase 3I-B low-water leak-path and overflow tests (7)."""

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ib import (
    OVERFLOW_CREST_Z_MM,
    OVERFLOW_MINIMUM_OPEN_THROAT_MM,
    OVERFLOW_TYPE,
    SELECTED_OVERFLOW_WEIR_WIDTH_MM,
    SELECTED_WATER_SURFACE_Z_MM,
    leak_path_audit_phase3ib,
    overflow_audit_phase3ib,
)


def test_phase3ib_central_opening_has_no_low_water_penetration() -> None:
    assert leak_path_audit_phase3ib()["central_opening_penetrations_below_normal_water"] == 0


def test_phase3ib_exterior_has_no_low_water_penetration() -> None:
    audit = leak_path_audit_phase3ib()
    assert audit["external_penetrations_below_normal_water"] == 0
    assert audit["pot_external_penetrations_below_normal_water"] == 0


def test_phase3ib_dry_interfaces_have_no_continuous_wet_path() -> None:
    audit = leak_path_audit_phase3ib()
    assert audit["dry_stacking_interface_wet_paths"] == 0
    assert audit["rear_frame_fastener_wet_paths"] == 0


def test_phase3ib_only_intended_lowest_outlet_is_rear_weir() -> None:
    audit = leak_path_audit_phase3ib()
    assert audit["intended_lowest_outlet_count"] == 1
    assert audit["intended_lowest_outlets"] == ["OPEN_REAR_WEIR"]


def test_phase3ib_overflow_is_open_rear_weir_at_water_surface() -> None:
    audit = overflow_audit_phase3ib()
    assert OVERFLOW_TYPE == "OPEN_REAR_WEIR"
    assert audit["rear_service_direction"] == "-X"
    assert OVERFLOW_CREST_Z_MM == SELECTED_WATER_SURFACE_Z_MM


def test_phase3ib_overflow_has_30_by_8mm_minimum_opening() -> None:
    audit = overflow_audit_phase3ib()
    assert SELECTED_OVERFLOW_WEIR_WIDTH_MM == 30.0
    assert OVERFLOW_MINIMUM_OPEN_THROAT_MM >= 8.0
    assert audit["minimum_geometric_open_area_mm2"] >= 240.0


def test_phase3ib_has_no_closed_siphon_drain_or_waterway() -> None:
    overflow = overflow_audit_phase3ib()
    leaks = leak_path_audit_phase3ib()
    assert not overflow["closed_siphon"]
    assert not overflow["small_diameter_drain_only"]
    assert leaks["closed_waterways"] == 0
    assert leaks["closed_drain_holes"] == 0

