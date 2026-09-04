"""Phase 3I-D two-stage coordinate and dry-air-gap tests (7)."""

from ps_mht_v001.reference.interstage_cascade_references_phase3id import two_stage_collision_audit_phase3id


def _audit() -> dict[str, object]:
    return two_stage_collision_audit_phase3id()


def test_phase3id_module_coordinate_ranges_are_fixed() -> None:
    assert _audit()["lower_module_z_mm"] == [0.0, 170.0]
    assert _audit()["upper_module_z_mm"] == [170.0, 340.0]


def test_phase3id_upper_water_surface_is_global_z196() -> None:
    assert _audit()["upper_water_surface_global_z_mm"] == 196.0


def test_phase3id_upper_outlet_is_global_z176() -> None:
    assert _audit()["upper_outlet_tip_global_z_mm"] == 176.0


def test_phase3id_lower_receiver_top_is_global_z170() -> None:
    assert _audit()["lower_receiver_top_global_z_mm"] == 170.0


def test_phase3id_nominal_air_gap_is_6mm() -> None:
    assert _audit()["nominal_air_gap_mm"] == 6.0
    assert abs(_audit()["measured_air_gap_mm"] - 6.0) <= 1.0e-6


def test_phase3id_outlet_and_receiver_do_not_touch() -> None:
    assert _audit()["outlet_receiver_clear"]
    assert _audit()["outlet_receiver_intersection_volume_mm3"] == 0


def test_phase3id_receiver_does_not_touch_upper_bottom() -> None:
    assert _audit()["receiver_upper_bottom_clear"]
    assert _audit()["receiver_upper_bottom_intersection_volume_mm3"] == 0

