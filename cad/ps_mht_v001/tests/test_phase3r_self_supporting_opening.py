"""Self-supporting shell opening and full-module envelope gates."""

from __future__ import annotations

from ps_mht_v001.assembly.full_module_reference_phase3r import (
    FULL_MODULE_REFERENCE_SOLID_COUNT,
    build_full_module_reference_phase3r,
)
from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    port_shell_max_overhang_angle,
    port_shell_opening_type,
    port_shell_reinforcement_thickness,
    tower_max_diameter,
)
from ps_mht_v001.tower_module.planting_port import maximum_radial_radius
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r import (
    ROUNDNESS_POLICY,
    build_self_supporting_port_shell_coupon_phase3r,
    build_three_port_module_shell_phase3r,
    self_supporting_upper_slope_angle,
)


def test_shell_opening_is_teardrop_not_a_circular_fit_datum() -> None:
    assert port_shell_opening_type == "TEARDROP_45_DEGREE_SELF_SUPPORTING"
    assert ROUNDNESS_POLICY == "NO_CIRCULAR_FIT_DATUM_ON_PRINTED_SHELL"


def test_shell_opening_upper_overhang_is_at_most_45_degrees() -> None:
    assert self_supporting_upper_slope_angle() <= 45.0
    assert port_shell_max_overhang_angle <= 45.0


def test_shell_opening_reinforcement_is_at_least_four_mm() -> None:
    assert port_shell_reinforcement_thickness >= 4.0


def test_vertical_shell_coupon_is_one_valid_a1_safe_solid() -> None:
    metrics = measure_shape(build_self_supporting_port_shell_coupon_phase3r())
    assert metrics.solid_count == 1 and metrics.all_solids_valid
    assert metrics.size_x <= 245.0
    assert metrics.size_y <= 245.0
    assert metrics.size_z <= 240.0


def test_three_self_supporting_ports_form_one_valid_shell() -> None:
    metrics = measure_shape(build_three_port_module_shell_phase3r())
    assert metrics.solid_count == 1 and metrics.all_solids_valid


def test_full_phase3r_reference_stays_inside_240mm_diameter() -> None:
    module = build_full_module_reference_phase3r()
    metrics = measure_shape(module)
    assert metrics.solid_count == FULL_MODULE_REFERENCE_SOLID_COUNT
    assert 2.0 * maximum_radial_radius(module) <= tower_max_diameter
