from ps_mht_v001_phase3ig_lower_return_buffer.src.phase3ig_lower_return_buffer import (
    four_tower_layout_audit_phase3ig, hydraulic_connectivity_audit_phase3ig,
)


def test_ordered_bottom_inlet_upflow_path_is_continuous():
    a = hydraulic_connectivity_audit_phase3ig()
    assert a["path_continuous"]
    assert a["ordered_path"][0] == "LOWEST_STAGE_THREE_DROPS"
    assert a["ordered_path"][-1] == "CENTRAL_TROUGH"


def test_downcomer_is_vented_and_horizontal_at_bottom():
    a = hydraulic_connectivity_audit_phase3ig()
    assert a["downcomer_top_vented"] and a["bottom_discharge_horizontal"]


def test_open_gutter_breaks_siphon():
    a = hydraulic_connectivity_audit_phase3ig()
    assert a["normal_overflow_air_break"]
    assert not a["siphon_path_present"]


def test_four_returns_do_not_merge_before_trough():
    a = four_tower_layout_audit_phase3ig()
    assert a["return_line_count"] == 4
    assert not a["pre_trough_manifold_present"]


def test_layout_distance_is_calculated_not_assumed():
    a = four_tower_layout_audit_phase3ig()
    assert a["tower_to_trough_center_mm"] > 800
    assert a["straight_outlet_to_trough_envelope_gap_mm"] > 100
    assert a["provisional_hose_cut_length_range_mm"] == [350.0, 500.0]


def test_no_small_diffuser_holes():
    assert not hydraulic_connectivity_audit_phase3ig()["small_diffuser_holes_present"]


def test_baffle_is_reserved_not_silently_added():
    a = hydraulic_connectivity_audit_phase3ig()
    assert a["internal_baffle_status"] == "INTERNAL_BAFFLE_RESERVED"
    assert a["dye_test_required"]


def test_cleanout_is_not_open_in_normal_configuration():
    from ps_mht_v001_phase3ig_lower_return_buffer.src.phase3ig_lower_return_buffer import geometry_audit_phase3ig
    assert geometry_audit_phase3ig()["tank_floor_penetrations"] == 0

