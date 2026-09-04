import pytest

from ps_mht_v001.fixtures.dry_core_frame_phase3if import (
    BOTTOM_PUCK_OUTER_DIAMETER_CANDIDATES_MM,
    MAXIMUM_DRY_CORE_FRAME_RADIUS_MM,
    REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM,
    REFERENCE_MAST_CLEARANCE_MM,
    SELECTED_BOTTOM_PUCK_OUTER_DIAMETER_MM,
    SELECTED_MAST_CLEARANCE_MM,
    SELECTED_MAST_TYPE,
    build_bottom_centering_puck_fit_coupons_phase3if,
    build_bottom_centering_puck_phase3if,
    build_removable_top_centering_cap_phase3if,
    dry_core_component_audit_phase3if,
)


AUDIT = dry_core_component_audit_phase3if()


def test_phase3if_mast_selection_pending():
    assert SELECTED_MAST_TYPE is None


def test_phase3if_puck_selection_pending():
    assert SELECTED_BOTTOM_PUCK_OUTER_DIAMETER_MM is None


def test_phase3if_mast_clearance_pending():
    assert SELECTED_MAST_CLEARANCE_MM is None


def test_phase3if_puck_candidates():
    assert BOTTOM_PUCK_OUTER_DIAMETER_CANDIDATES_MM == (98.0, 98.5, 99.0)


def test_phase3if_installed_reference_radius_limit():
    assert 0.5 * REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM <= MAXIMUM_DRY_CORE_FRAME_RADIUS_MM


def test_phase3if_bottom_puck_one_solid():
    puck = build_bottom_centering_puck_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM)
    assert len(puck.solids().vals()) == 1 and puck.val().isValid()


def test_phase3if_top_cap_one_solid():
    cap = build_removable_top_centering_cap_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM)
    assert len(cap.solids().vals()) == 1 and cap.val().isValid()


def test_phase3if_fit_coupon_three_solids():
    assert len(build_bottom_centering_puck_fit_coupons_phase3if().solids().vals()) == 3


def test_phase3if_fit_coupon_inside_a1():
    assert AUDIT["fit_coupon_a1_pass"]


def test_phase3if_petg_not_primary_bending_member():
    assert AUDIT["petg_primary_bending_member"] is False


def test_phase3if_vertical_load_does_not_hang_from_mast():
    assert AUDIT["vertical_load_path"] == "MODULE_STACK_TO_BASE_NOT_SUSPENDED_FROM_MAST"


def test_phase3if_explicit_dimensions_required():
    with pytest.raises(TypeError):
        build_bottom_centering_puck_phase3if()


def test_phase3if_nominal_mast_requires_clearance():
    with pytest.raises(ValueError):
        build_bottom_centering_puck_phase3if(98.0, 20.0)

