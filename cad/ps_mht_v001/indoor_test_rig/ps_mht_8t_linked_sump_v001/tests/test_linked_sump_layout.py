"""Support, room-height and protected-route tests (6)."""

from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001 import parameters as p
from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.reference_cad import (
    parallel_zone_metadata,
    support_deck_reference_metadata,
)


def test_support_deck_range_is_160_to_180_with_170_nominal() -> None:
    assert p.tower_support_deck_elevation_mm == (160.0, 170.0, 180.0)


def test_tower_bottom_drain_range_is_190_to_220_with_205_nominal() -> None:
    assert p.tower_bottom_drain_elevation_mm == (190.0, 205.0, 220.0)


def test_tower_and_pipe_loads_do_not_enter_sump_wall() -> None:
    metadata = support_deck_reference_metadata()
    assert metadata["tank_load_bearing"] is False
    assert metadata["pipe_load_bearing"] is False
    assert p.tower_load_path == "DRY_FOUR_CORNER_SUPPORT_DIRECT_TO_FLOOR"


def test_ceiling_and_upper_tank_clearance_are_consistent() -> None:
    assert p.room_ceiling_height_mm == 2300.0
    assert p.upper_tank_maximum_top_elevation_mm <= 2050.0
    assert p.room_ceiling_height_mm - p.upper_tank_maximum_top_elevation_mm >= 250.0


def test_aisle_minimum_and_room_measurement_pending() -> None:
    assert p.minimum_human_aisle_width_mm >= 600.0
    assert p.room_length_mm == "MEASUREMENT_PENDING"
    assert p.room_width_mm == "MEASUREMENT_PENDING"


def test_rear_trunk_does_not_cross_aisle_and_fresh_water_is_separate() -> None:
    assert parallel_zone_metadata(4)["crosses_human_aisle"] is False
    assert parallel_zone_metadata(8)["rear_service_route"] is True
    assert p.fresh_water_system_separate_from_circulation is True
    assert p.fresh_water_to_tower_at_night == "CLOSED"
