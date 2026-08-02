"""Phase 3H-A full-ring functional geometry tests (10)."""

import inspect

import pytest

from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    horizontal_joint_band_axial_contribution_height,
    horizontal_joint_clearance_selected,
    horizontal_joint_lower_physical_print_height,
    horizontal_joint_upper_physical_print_height,
)
from ps_mht_v001.tower_module.horizontal_ring_joint_phase3ha import (
    build_full_ring_joint_pair_phase3ha,
    build_lower_full_ring_phase3ha,
    build_upper_full_ring_print_phase3ha,
    horizontal_joint_requirements_phase3ha,
)


def test_phase3ha_clearance_is_explicit_and_restricted() -> None:
    parameter = inspect.signature(
        build_full_ring_joint_pair_phase3ha
    ).parameters["clearance"]
    assert parameter.default is inspect.Parameter.empty
    with pytest.raises(ValueError):
        build_full_ring_joint_pair_phase3ha(0.4)


def test_phase3ha_nominal_outer_diameter_is_200_mm() -> None:
    assert horizontal_joint_requirements_phase3ha(0.5)[
        "nominal_outer_diameter_mm"
    ] == 200.0


def test_phase3ha_structural_wall_is_at_least_3_mm() -> None:
    assert horizontal_joint_requirements_phase3ha(0.5)[
        "structural_wall_mm"
    ] >= 3.0


def test_phase3ha_skirt_overlap_is_10_mm() -> None:
    assert horizontal_joint_requirements_phase3ha(0.5)["skirt_overlap_mm"] == 10.0


def test_phase3ha_skirt_tip_never_falls_below_2_4_mm() -> None:
    assert horizontal_joint_requirements_phase3ha(0.5)[
        "skirt_minimum_tip_thickness_mm"
    ] >= 2.4


def test_phase3ha_continuous_skirt_root_is_r3_or_larger() -> None:
    requirements = horizontal_joint_requirements_phase3ha(0.5)
    assert requirements["skirt_root_radius_mm"] >= 3.0
    assert requirements["full_circumference"] is True


def test_phase3ha_hard_stop_width_is_at_least_4_mm() -> None:
    assert horizontal_joint_requirements_phase3ha(0.5)[
        "hard_stop_width_mm"
    ] >= 4.0


def test_phase3ha_joint_has_no_direct_outside_inside_sightline() -> None:
    requirements = horizontal_joint_requirements_phase3ha(0.5)
    assert requirements["direct_outside_to_inside_sightline"] is False
    assert requirements["closed_cavity"] is False


def test_phase3ha_selected_clearance_remains_none() -> None:
    assert horizontal_joint_clearance_selected is None


def test_phase3ha_axial_contribution_and_print_heights_are_consistent_and_a1() -> None:
    assert horizontal_joint_band_axial_contribution_height == 40.0
    assert horizontal_joint_lower_physical_print_height == 40.0
    assert horizontal_joint_upper_physical_print_height == 50.0
    lower = measure_shape(build_lower_full_ring_phase3ha())
    assert lower.solid_count == 1 and lower.size_x <= 245.0 and lower.size_z <= 40.0
    for clearance in (0.3, 0.5, 0.7):
        upper = measure_shape(build_upper_full_ring_print_phase3ha(clearance))
        assert upper.solid_count == 1
        assert upper.size_x <= 245.0 and upper.size_y <= 245.0
        assert upper.size_z <= 50.000001
