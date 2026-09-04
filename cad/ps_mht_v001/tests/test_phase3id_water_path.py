"""Phase 3I-D open water path and actual retained-volume tests (7)."""

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3id import (
    actual_water_volume_audit_phase3id,
    water_path_audit_phase3id,
)


def test_phase3id_actual_water_volume_is_within_required_range() -> None:
    audit = actual_water_volume_audit_phase3id()
    assert audit["within_target_range"]
    assert 0.35 <= audit["actual_retained_volume_l"] <= 0.45


def test_phase3id_actual_water_volume_is_in_preferred_range() -> None:
    assert actual_water_volume_audit_phase3id()["within_preferred_range"]


def test_phase3id_selected_water_surface_remains_z26() -> None:
    audit = actual_water_volume_audit_phase3id()
    assert audit["selected_water_surface_z_mm"] == 26.0
    assert not audit["water_level_changed"]


def test_phase3id_all_printed_intrusions_are_subtracted() -> None:
    assert actual_water_volume_audit_phase3id()["all_printed_intrusions_subtracted"]


def test_phase3id_has_no_low_external_or_central_leak_path() -> None:
    audit = water_path_audit_phase3id()
    assert audit["external_penetrations_below_water_surface"] == 0
    assert audit["central_hole_penetrations_below_water_surface"] == 0


def test_phase3id_channel_is_open_and_non_siphoning() -> None:
    audit = water_path_audit_phase3id()
    assert audit["closed_channel_count"] == 0
    assert audit["closed_pipe_count"] == 0
    assert not audit["siphon_path_present"]


def test_phase3id_bottom_discharge_avoids_central_hole_and_exterior() -> None:
    audit = water_path_audit_phase3id()
    assert audit["bottom_discharge_direction"] == "INTO_ANNULAR_SUMP"
    assert not audit["bottom_discharge_toward_central_hole"]
    assert not audit["bottom_discharge_toward_external_wall"]

