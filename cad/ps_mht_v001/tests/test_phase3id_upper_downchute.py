"""Phase 3I-D upper downchute and drip-nose tests (7)."""

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3id import (
    build_phase3id_diag_04d,
    overhang_audit_phase3id,
)
from ps_mht_v001.tower_module.positive_interstage_cascade_phase3id import (
    DRIP_NOSE_MAXIMUM_TIP_RADIUS_MM,
    DRIP_NOSE_TERMINAL_EDGE_THICKNESS_MM,
    DRIP_NOSE_TIP_RADIUS_MM,
    UPPER_DOWNCHUTE_INLET_CREST_Z_MM,
    UPPER_DOWNCHUTE_MINIMUM_CLEAR_WIDTH_MM,
    UPPER_DOWNCHUTE_OUTLET_TIP_Z_MM,
    UPPER_DOWNCHUTE_SIDE_WALL_HEIGHT_MM,
    UPPER_DOWNCHUTE_SIDE_WALL_THICKNESS_MM,
    build_upper_downchute_phase3id,
    interstage_path_dimension_audit_phase3id,
)


def test_phase3id_upper_downchute_is_one_valid_solid() -> None:
    model = build_upper_downchute_phase3id()
    assert len(model.solids().vals()) == 1 and model.val().isValid()


def test_phase3id_downchute_clear_width_meets_minimum() -> None:
    audit = interstage_path_dimension_audit_phase3id()["upper_downchute"]
    assert audit["clear_width_mm"] >= UPPER_DOWNCHUTE_MINIMUM_CLEAR_WIDTH_MM


def test_phase3id_downchute_inlet_and_outlet_z() -> None:
    audit = interstage_path_dimension_audit_phase3id()["upper_downchute"]
    assert audit["inlet_crest_z_mm"] == UPPER_DOWNCHUTE_INLET_CREST_Z_MM == 26.0
    assert audit["outlet_tip_z_mm"] == UPPER_DOWNCHUTE_OUTLET_TIP_Z_MM == 6.0


def test_phase3id_drip_nose_centerline_radius_is_bounded() -> None:
    assert DRIP_NOSE_TIP_RADIUS_MM == 106.0
    assert DRIP_NOSE_TIP_RADIUS_MM <= DRIP_NOSE_MAXIMUM_TIP_RADIUS_MM


def test_phase3id_drip_nose_terminal_edge_breaks_surface_tension() -> None:
    audit = interstage_path_dimension_audit_phase3id()["upper_downchute"]
    assert 1.2 <= DRIP_NOSE_TERMINAL_EDGE_THICKNESS_MM <= 2.0
    assert audit["surface_tension_break"]


def test_phase3id_downchute_walls_meet_dimensions_and_are_open() -> None:
    audit = interstage_path_dimension_audit_phase3id()["upper_downchute"]
    assert UPPER_DOWNCHUTE_SIDE_WALL_THICKNESS_MM >= 3.2
    assert 8.0 <= UPPER_DOWNCHUTE_SIDE_WALL_HEIGHT_MM <= 10.0
    assert audit["open_for_brush_cleaning"]


def test_phase3id_downchute_fuses_into_one_d04d_solid_without_support_dependency() -> None:
    assert len(build_phase3id_diag_04d().solids().vals()) == 1
    audit = overhang_audit_phase3id()
    assert audit["features"]["drip_nose_underside"] == "SELF_SUPPORTING"
    assert not audit["cad_support_dependency"]

