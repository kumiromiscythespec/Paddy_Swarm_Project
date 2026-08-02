"""Measured Siawadeky dimensions and deprecated assumptions."""

from ps_mht_v001 import parameters
from ps_mht_v001.reference.siawadeky_netpot_measurements_phase3pa import (
    INSIDE_MEASUREMENT_METHOD,
    OUTSIDE_MEASUREMENT_METHOD,
    siawadeky_measurements_phase3pa,
)


def test_phase3pa_sample_count_and_equality() -> None:
    assert parameters.netpot_siawadeky_sample_count == 3
    assert parameters.netpot_siawadeky_measurements_equal is True


def test_phase3pa_flange_and_overall_measurements() -> None:
    assert parameters.netpot_siawadeky_flange_outer_diameter == 108.0
    assert parameters.netpot_siawadeky_flange_thickness == 4.0
    assert parameters.netpot_siawadeky_overall_height == 68.0
    assert parameters.netpot_siawadeky_body_height_below_flange == 64.0


def test_phase3pa_external_body_measurements() -> None:
    assert parameters.netpot_siawadeky_max_body_outer_diameter == 78.6
    assert parameters.netpot_siawadeky_max_rib_outer_diameter == 78.6
    assert parameters.netpot_siawadeky_external_rib_projection == 0.0
    assert parameters.netpot_siawadeky_flange_radial_overhang == 14.7


def test_phase3pa_internal_measurements_are_reference_only() -> None:
    record = siawadeky_measurements_phase3pa()
    assert record["measured_mm"]["upper_inner_diameter"] == 77.2
    assert record["measured_mm"]["lower_inner_diameter_reachable"] == 75.8
    assert record["measured_mm"]["deepest_reachable_inner_diameter"] == 69.6
    assert record["inner_diameter_usage"] == "REFERENCE_ONLY_NOT_EXTERNAL_ENVELOPE"


def test_phase3pa_caliper_methods_are_explicit() -> None:
    assert INSIDE_MEASUREMENT_METHOD == "CALIPER_INSIDE_JAWS"
    assert OUTSIDE_MEASUREMENT_METHOD == "CALIPER_OUTSIDE_JAWS"


def test_phase3pa_old_assumptions_are_deprecated() -> None:
    assert parameters.netpot_siawadeky_flange_diameter_assumed_78_5 == (
        "REJECTED_BY_PHYSICAL_MEASUREMENT"
    )
    assert parameters.netpot_siawadeky_body_diameter_assumed_72_0 == (
        "REJECTED_BY_PHYSICAL_MEASUREMENT"
    )
    assert parameters.phase3r1_port_inner_diameter_84_0 == (
        "NOT_FINAL_EXCESS_CLEARANCE"
    )
