"""Six real male keys and socket grooves, including rotation matching."""

from __future__ import annotations

from ps_mht_v001.assembly.module_pair_phase2 import (
    key_alignment_intersection_volume,
)
from ps_mht_v001.tower_module.module_interface import (
    build_index_key_solid,
    build_planting_module_with_interface,
    build_socket_key_groove_void,
    index_angles,
)


MODULE = build_planting_module_with_interface()


def _volume(model) -> float:
    return sum(solid.Volume() for solid in model.solids().vals())


def _intersection(first, second) -> float:
    return _volume(first.intersect(second))


def test_six_actual_male_keys_exist_in_module() -> None:
    for angle in index_angles():
        key = build_index_key_solid(angle)
        assert _volume(key) > 35.0
        assert _intersection(MODULE, key) >= 0.999 * _volume(key)


def test_six_actual_socket_grooves_exist_in_module() -> None:
    for angle in index_angles():
        groove = build_socket_key_groove_void(angle)
        assert _volume(groove) > 50.0
        assert _intersection(MODULE, groove) <= 1.0e-8


def test_real_keys_match_real_grooves_at_0_and_60() -> None:
    at_zero = key_alignment_intersection_volume(0.0)
    at_sixty = key_alignment_intersection_volume(60.0)
    assert at_zero > 200.0
    assert abs(at_zero - at_sixty) <= 1.0e-6


def test_real_keys_do_not_match_real_grooves_at_30() -> None:
    assert key_alignment_intersection_volume(30.0) <= 1.0e-8

