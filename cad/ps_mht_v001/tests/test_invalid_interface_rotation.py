"""Real-shape Phase 2 invalid-rotation safeguards required by Phase 3A."""

from __future__ import annotations

from ps_mht_v001.assembly.module_pair_phase2 import (
    is_normal_assembly_rotation,
    key_alignment_intersection_volume,
    m4_axis_alignment_intersection_volume,
    minimum_noninterfering_lift,
    module_pair_interference_volume,
)


def test_30_degree_connection_has_real_key_interference() -> None:
    assert module_pair_interference_volume(30.0) > 100.0


def test_0_and_60_degree_connections_fully_seat() -> None:
    assert module_pair_interference_volume(0.0) <= 1.0e-6
    assert module_pair_interference_volume(60.0) <= 1.0e-6


def test_30_degree_connection_cannot_descend_to_nominal_position() -> None:
    assert minimum_noninterfering_lift(30.0) >= 2.0


def test_30_degree_connection_m4_axes_do_not_align() -> None:
    assert m4_axis_alignment_intersection_volume(0.0) > 800.0
    assert m4_axis_alignment_intersection_volume(60.0) > 800.0
    assert m4_axis_alignment_intersection_volume(30.0) <= 1.0e-8


def test_90_degree_is_not_a_normal_assembly_rotation() -> None:
    assert not is_normal_assembly_rotation(90.0)
