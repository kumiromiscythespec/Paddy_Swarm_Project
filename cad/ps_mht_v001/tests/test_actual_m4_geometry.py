"""Physical M4 bore and surrounding-wall probes."""

from __future__ import annotations

from ps_mht_v001.parameters import available_fastener_angles
from ps_mht_v001.tower_module.module_interface import (
    build_m4_axis_probe,
    build_m4_required_wall_probe,
    build_planting_module_with_interface,
    m4_boss_nominal_radial_wall,
)


MODULE = build_planting_module_with_interface()


def _volume(model) -> float:
    return sum(solid.Volume() for solid in model.solids().vals())


def test_all_six_real_m4_axes_accept_physical_probes() -> None:
    for angle in available_fastener_angles:
        assert _volume(MODULE.intersect(build_m4_axis_probe(angle))) <= 1.0e-8


def test_angle_without_m4_hole_blocks_axis_probe() -> None:
    assert _volume(MODULE.intersect(build_m4_axis_probe(0.0))) > 50.0


def test_all_six_top_bosses_contain_required_wall_probe() -> None:
    for angle in available_fastener_angles:
        probe = build_m4_required_wall_probe(angle, required_wall=5.5)
        present = _volume(MODULE.intersect(probe))
        assert present >= 0.999 * _volume(probe)


def test_phase2_actual_m4_boss_wall_is_reported_not_overclaimed() -> None:
    assert m4_boss_nominal_radial_wall() == 5.75
    assert m4_boss_nominal_radial_wall() >= 5.5
    assert m4_boss_nominal_radial_wall() < 6.0

