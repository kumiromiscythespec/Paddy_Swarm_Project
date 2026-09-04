from ps_mht_v001_phase3ig_lower_return_buffer.src.phase3ig_lower_return_buffer import water_volume_audit_phase3ig


def test_normal_working_volume_is_targeted():
    a = water_volume_audit_phase3ig()
    assert a["normal_target_2_to_2_5_l"]


def test_volume_ordering():
    a = water_volume_audit_phase3ig()
    assert 0 < a["tank_normal_working_volume_l"] < a["tank_emergency_level_volume_l"] < a["tank_internal_capacity_to_top_l"]


def test_positive_normal_to_emergency_reserve():
    a = water_volume_audit_phase3ig()
    assert a["tank_normal_to_emergency_reserve_l"] > 0.3


def test_positive_freeboard_volume():
    assert water_volume_audit_phase3ig()["tank_freeboard_volume_above_emergency_l"] > 0


def test_four_tower_transient_reserve():
    a = water_volume_audit_phase3ig()
    assert a["four_tower_transient_reserve_l"] == 4 * a["tank_normal_to_emergency_reserve_l"]


def test_maximum_pump_stop_return_uses_actual_stage_water():
    a = water_volume_audit_phase3ig()
    assert 7.14 < a["maximum_pump_stop_return_l"] < 7.16


def test_trough_conservative_lower_bound_is_computed():
    a = water_volume_audit_phase3ig()
    assert a["trough_level_rise_lower_bound_mm"] > 24.0
    assert a["trough_remaining_freeboard_upper_bound_mm"] > 80.0


def test_unknown_trough_inner_shape_is_not_guessed():
    a = water_volume_audit_phase3ig()
    assert a["trough_level_rise_upper_bound_mm"] is None
    assert a["trough_remaining_freeboard_lower_bound_mm"] is None
    assert "PHYSICAL_MEASUREMENT_PENDING" in a["trough_upper_bound_reason"]

