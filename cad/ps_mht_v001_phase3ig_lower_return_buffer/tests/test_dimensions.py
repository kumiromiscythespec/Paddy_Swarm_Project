import pytest

from ps_mht_v001_phase3ig_lower_return_buffer.src.phase3ig_lower_return_buffer import *


def test_tank_envelope_within_limit():
    b = build_lower_buffer_tank_phase3ig().val().BoundingBox()
    assert b.xlen <= 240.0 + 1e-6 and b.ylen <= 160.0 + 1e-6 and b.zlen <= 105.0 + 1e-6


def test_tray_envelope_within_limit():
    b = build_terminal_collection_tray_phase3ig().val().BoundingBox()
    assert b.xlen <= 236.0 + 1e-6 and b.ylen <= 236.0 + 1e-6 and b.zlen <= 30.0 + 1e-6


@pytest.mark.parametrize("actual,minimum", [(TANK_WALL_MM, 3.0), (TANK_FLOOR_MM, 4.0), (DOWNCOMER_WALL_MM, 3.0)])
def test_minimum_material_dimensions(actual, minimum):
    assert actual >= minimum


def test_normal_weir_crest():
    assert NORMAL_WATER_Z_MM == pytest.approx(82.0)


def test_emergency_crest():
    assert EMERGENCY_WATER_Z_MM == pytest.approx(94.0)


def test_tank_top():
    assert TANK_HEIGHT_MM == pytest.approx(105.0)


def test_diffuser_slot():
    assert (DIFFUSER_SLOT_WIDTH_MM, DIFFUSER_SLOT_HEIGHT_MM) == pytest.approx((100.0, 9.0))


def test_diffuser_plenum_envelope():
    assert (DIFFUSER_WIDTH_MM, DIFFUSER_LENGTH_MM, DIFFUSER_HEIGHT_MM) == pytest.approx((112.0, 32.0, 30.0))


def test_downcomer_clear_bore():
    assert DOWNCOMER_CLEAR_BORE_MM == pytest.approx(25.0)


def test_downcomer_wall_preserving_offset_is_explicit():
    assert DOWNCOMER_OUTLET_TARGET_ABOVE_INNER_FLOOR_MM == pytest.approx(15.0)
    assert DOWNCOMER_OUTLET_ACTUAL_ABOVE_INNER_FLOOR_MM == pytest.approx(15.5)


def test_dry_opening_and_mast_clearance():
    assert TRAY_CENTRAL_OPENING_MM >= 30.0
    assert TRAY_CENTRAL_OPENING_MM - max(MAST_MEASURED_X_MM, MAST_MEASURED_Y_MM) > 10.0


def test_real_landing_angles_and_stage_rotation_preserved():
    assert LOWER_LANDING_ANGLES_DEG == (60.0, 180.0, 300.0)
    assert STAGE_RELATIVE_ROTATION_DEG == 30.0
    assert STAGE_ABSOLUTE_ROTATIONS_DEG == (0.0, 30.0, 60.0, 90.0, 120.0)


def test_normal_and_emergency_widths():
    assert NORMAL_WEIR_EFFECTIVE_WIDTH_MM == pytest.approx(112.0)
    assert EMERGENCY_OVERFLOW_CLEAR_WIDTH_MM >= 25.0

