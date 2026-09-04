"""Phase 3I-C corrected-full authority and Phase 3I-B delta tests (7)."""

from ps_mht_v001.tower_module.floating_region_diagnostics_phase3ic import (
    build_integrated_stage_full_corrected_phase3ic,
    build_phase3ic_diag_05,
    diagnostic_geometry_audit_phase3ic,
    phase3ic_phase3ib_geometry_delta_audit,
    retention_lug_boolean_audit_phase3ic,
)


def test_phase3ic_d05_equals_corrected_full() -> None:
    audit = diagnostic_geometry_audit_phase3ic()["d05_phase3ic_corrected_full_equivalence"]
    assert audit["within_tolerance"]
    assert audit["brep_volume_difference_mm3"] == 0.0
    assert max(audit["bbox_difference_mm"]) == 0.0


def test_phase3ic_d05_and_corrected_full_are_same_authority() -> None:
    assert build_phase3ic_diag_05().val().isSame(build_integrated_stage_full_corrected_phase3ic().val())


def test_phase3ic_corrected_full_differs_from_phase3ib() -> None:
    delta = phase3ic_phase3ib_geometry_delta_audit()
    assert delta["volume_difference_mm3"] > 1.0
    assert delta["changed_regions"] == ["RETENTION_LUG_BOOLEAN_ONLY"]


def test_phase3ic_delta_contains_six_lugs_and_six_holes() -> None:
    delta = phase3ic_phase3ib_geometry_delta_audit()
    assert delta["added_complete_lug_count"] == 6
    assert delta["penetrating_rope_hole_count"] == 6
    assert retention_lug_boolean_audit_phase3ic()["status"] == "PASS"


def test_phase3ic_sump_dam_overflow_and_stacking_interfaces_unchanged() -> None:
    delta = phase3ic_phase3ib_geometry_delta_audit()
    assert delta["sump_dimensions_unchanged"]
    assert delta["inner_dam_dimensions_unchanged"]
    assert delta["overflow_dimensions_unchanged"]
    assert delta["stacking_guides_unchanged"]


def test_phase3ic_actual_water_volume_is_numerically_unchanged() -> None:
    delta = phase3ic_phase3ib_geometry_delta_audit()
    assert abs(delta["water_volume_difference_l"]) <= 1.0e-8


def test_phase3ic_recess_and_envelope_remain_fixed() -> None:
    delta = phase3ic_phase3ib_geometry_delta_audit()
    assert delta["port_recess_mm"] == 2.0
    assert delta["maximum_xy_mm"] <= 238.0
    assert delta["within_238mm"]

