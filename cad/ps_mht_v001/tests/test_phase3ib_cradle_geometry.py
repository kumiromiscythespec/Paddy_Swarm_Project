"""Phase 3I-B three-pad floor-connected cradle tests (7)."""

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ib import (
    CRADLE_ARCHITECTURE,
    MAIN_PAD_CONTACT_DEPTH_MM,
    MAIN_PAD_TANGENTIAL_WIDTH_MM,
    PORT_BODY_PASSAGE_DIAMETER_MM,
    SIDE_PAD_CONTACT_DEPTH_MM,
    SIDE_PAD_TANGENTIAL_WIDTH_MM,
    build_floor_connected_cradle_phase3ib,
    cradle_support_audit_phase3ib,
)


def test_phase3ib_cradle_architecture_is_three_pad_buttress() -> None:
    audit = cradle_support_audit_phase3ib()
    assert CRADLE_ARCHITECTURE == "FLOOR_CONNECTED_THREE_PAD_BUTTRESS_CRADLE"
    assert audit["pad_count_per_port"] == 3


def test_phase3ib_main_pad_meets_width_and_depth() -> None:
    assert MAIN_PAD_TANGENTIAL_WIDTH_MM >= 36.0
    assert MAIN_PAD_CONTACT_DEPTH_MM >= 8.0


def test_phase3ib_side_pads_meet_width_and_depth() -> None:
    assert SIDE_PAD_TANGENTIAL_WIDTH_MM >= 18.0
    assert SIDE_PAD_CONTACT_DEPTH_MM >= 8.0


def test_phase3ib_all_three_buttresses_are_floor_connected() -> None:
    audit = cradle_support_audit_phase3ib()
    assert audit["floor_connected_buttress_count_per_port"] == 3
    assert audit["all_buttresses_floor_connected"] is True


def test_phase3ib_cradle_has_no_airborne_complete_ring() -> None:
    audit = cradle_support_audit_phase3ib()
    assert audit["complete_independent_ring_count"] == 0
    assert audit["airborne_start_count"] == 0


def test_phase3ib_cradle_stays_within_angle_and_bridge_limits() -> None:
    audit = cradle_support_audit_phase3ib()
    assert audit["maximum_unsupported_surface_angle_from_vertical_deg"] <= 45.0
    assert audit["maximum_horizontal_bridge_mm"] <= 8.0


def test_phase3ib_each_port_cradle_geometry_is_valid() -> None:
    for angle in (0.0, 120.0, 240.0):
        cradle = build_floor_connected_cradle_phase3ib(angle)
        assert cradle.solids().size() >= 1
        assert all(solid.isValid() for solid in cradle.solids().vals())
    assert PORT_BODY_PASSAGE_DIAMETER_MM == 80.5

