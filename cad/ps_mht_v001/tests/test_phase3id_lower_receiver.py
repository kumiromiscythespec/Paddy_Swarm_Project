"""Phase 3I-D receiver, open channel and bottom-discharge tests (7)."""

from ps_mht_v001.tower_module.positive_interstage_cascade_phase3id import (
    BOTTOM_DISCHARGE_RAMP_ANGLE_FROM_VERTICAL_DEG,
    LOWER_CHANNEL_BOTTOM_DISCHARGE_Z_MM,
    LOWER_CHANNEL_BRUSH_MINIMUM_WIDTH_MM,
    LOWER_CHANNEL_CLEAR_WIDTH_MM,
    LOWER_CHANNEL_MINIMUM_CLEAR_WIDTH_MM,
    LOWER_RECEIVER_MAXIMUM_OUTER_RADIUS_MM,
    LOWER_RECEIVER_MINIMUM_MOUTH_WIDTH_MM,
    LOWER_RECEIVER_OUTER_RADIUS_MM,
    LOWER_RECEIVER_TANGENTIAL_MOUTH_WIDTH_MM,
    LOWER_RECEIVER_TOP_Z_MM,
    build_lower_receiver_channel_discharge_phase3id,
    build_lower_receiver_phase3id,
    interstage_path_dimension_audit_phase3id,
)


def test_phase3id_receiver_is_one_valid_solid() -> None:
    model = build_lower_receiver_phase3id()
    assert len(model.solids().vals()) == 1 and model.val().isValid()


def test_phase3id_receiver_width_is_46mm_and_above_minimum() -> None:
    assert LOWER_RECEIVER_TANGENTIAL_MOUTH_WIDTH_MM == 46.0
    assert LOWER_RECEIVER_TANGENTIAL_MOUTH_WIDTH_MM >= LOWER_RECEIVER_MINIMUM_MOUTH_WIDTH_MM


def test_phase3id_receiver_outer_radius_is_below_limit() -> None:
    assert LOWER_RECEIVER_OUTER_RADIUS_MM == 118.0
    assert LOWER_RECEIVER_OUTER_RADIUS_MM <= LOWER_RECEIVER_MAXIMUM_OUTER_RADIUS_MM == 118.5


def test_phase3id_receiver_top_is_exactly_z170() -> None:
    assert LOWER_RECEIVER_TOP_Z_MM == 170.0
    assert abs(build_lower_receiver_phase3id().val().BoundingBox().zmax - 170.0) <= 1.0e-6


def test_phase3id_lower_channel_is_open_and_wide_enough() -> None:
    audit = interstage_path_dimension_audit_phase3id()["lower_vertical_channel"]
    assert LOWER_CHANNEL_CLEAR_WIDTH_MM >= LOWER_CHANNEL_MINIMUM_CLEAR_WIDTH_MM
    assert audit["open_direction"] == "REAR_OUTWARD"


def test_phase3id_lower_channel_accepts_a_12mm_brush() -> None:
    audit = interstage_path_dimension_audit_phase3id()["lower_vertical_channel"]
    assert audit["brush_minimum_width_mm"] >= LOWER_CHANNEL_BRUSH_MINIMUM_WIDTH_MM == 12.0


def test_phase3id_bottom_discharge_is_open_inward_and_one_route_solid() -> None:
    audit = interstage_path_dimension_audit_phase3id()["bottom_discharge"]
    assert audit["outlet_z_mm"] == LOWER_CHANNEL_BOTTOM_DISCHARGE_Z_MM == 28.0
    assert audit["direction"] == "INTO_ANNULAR_SUMP"
    assert not audit["central_hole_direction"]
    assert BOTTOM_DISCHARGE_RAMP_ANGLE_FROM_VERTICAL_DEG <= 45.0
    assert len(build_lower_receiver_channel_discharge_phase3id().solids().vals()) == 1

