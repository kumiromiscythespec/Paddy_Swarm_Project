"""Phase 3R.1 shell/frame fusion and root-load-path gates."""

from __future__ import annotations

from math import isclose
from pathlib import Path

from ps_mht_v001.common.validation import (
    measure_shape,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.parameters import port_shell_coupon_height
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r1 import (
    FRAME_INWARD_SHIFT_MM,
    ROOT_INCLUSION_PROBE_DIAMETER_MM,
    SHELL_FRAME_RADIAL_FUSION_INCREASE_MM,
    build_root_inclusion_probe_phase3r1,
    build_self_supporting_port_frame_phase3r1,
    build_self_supporting_port_shell_coupon_phase3r1,
    build_self_supporting_port_void_phase3r1,
    build_shell_blank_phase3r1,
    fusion_volume_relation_phase3r1,
    self_supporting_upper_slope_angle_phase3r1,
)


EXPORT_ROOT = Path(__file__).resolve().parents[1] / "exports"
SHELL_STEM = "ps_mht_v001_self_supporting_port_shell_coupon_phase3r1"


def _parts():
    shell = build_shell_blank_phase3r1()
    frame = build_self_supporting_port_frame_phase3r1(
        0.5 * port_shell_coupon_height
    )
    void = build_self_supporting_port_void_phase3r1(
        0.5 * port_shell_coupon_height
    )
    return shell, frame, void


def test_phase3r1_shell_and_frame_physically_intersect() -> None:
    shell, frame, _ = _parts()
    intersection = shell.intersect(frame)
    assert sum(s.Volume() for s in intersection.solids().vals()) > 0.0
    assert SHELL_FRAME_RADIAL_FUSION_INCREASE_MM >= 1.0


def test_phase3r1_shell_frame_union_is_one_solid() -> None:
    shell, frame, _ = _parts()
    metrics = measure_shape(shell.union(frame))
    assert metrics.solid_count == 1 and metrics.all_solids_valid


def test_phase3r1_union_volume_obeys_boolean_identity() -> None:
    volumes = fusion_volume_relation_phase3r1()
    expected = (
        volumes["shell_mm3"]
        + volumes["frame_mm3"]
        - volumes["intersection_mm3"]
    )
    assert isclose(volumes["union_mm3"], expected, abs_tol=1.0e-5)


def test_phase3r1_void_cut_preserves_one_solid() -> None:
    shell, frame, void = _parts()
    result = shell.union(frame).cut(void)
    metrics = measure_shape(result)
    assert metrics.solid_count == 1 and metrics.all_solids_valid


def test_phase3r1_root_contains_real_four_mm_probe() -> None:
    coupon = build_self_supporting_port_shell_coupon_phase3r1()
    probe = build_root_inclusion_probe_phase3r1()
    probe_volume = probe.val().Volume()
    contained = sum(
        solid.Volume() for solid in coupon.intersect(probe).solids().vals()
    )
    assert ROOT_INCLUSION_PROBE_DIAMETER_MM >= 4.0
    assert isclose(contained, probe_volume, abs_tol=1.0e-5)


def test_phase3r1_teardrop_overhang_and_inward_shift_are_retained() -> None:
    assert self_supporting_upper_slope_angle_phase3r1() <= 45.0
    assert 1.0 <= FRAME_INWARD_SHIFT_MM <= 2.0


def test_phase3r1_shell_step_reloads_as_one_valid_solid() -> None:
    metrics = validate_step_round_trip(
        EXPORT_ROOT / "step" / f"{SHELL_STEM}.step",
        1,
        printable=True,
    )
    assert metrics.solid_count == 1 and metrics.all_solids_valid


def test_phase3r1_shell_stl_is_one_closed_connected_component() -> None:
    metrics = validate_stl_mesh(
        EXPORT_ROOT / "stl" / f"{SHELL_STEM}.stl"
    )
    assert metrics.closed_manifold
    assert metrics.connected_component_count == 1
