"""Phase 3S-A structural port fidelity and printability gates."""

from __future__ import annotations

from ps_mht_v001.parameters import (
    netpot_siawadeky_body_diameter_pending,
    netpot_siawadeky_flange_diameter_assumed,
    netpot_siawadeky_height_assumed,
    phase3sa_max_print_overhang,
    phase3sa_port_axis_angle,
    port_shell_reinforcement_thickness,
)
from ps_mht_v001.tower_module.sector_port_opening_phase3sa import (
    NETPOT_FINAL_FIT,
    ROUNDNESS_OWNER,
    port_printability_phase3sa,
)


def test_port_axis_remains_outward_and_upward_27_degrees() -> None:
    assert phase3sa_port_axis_angle == 27.0
    assert port_printability_phase3sa()[
        "assembly_axis_angle_deg"
    ] == 27.0


def test_print_posture_port_overhang_is_self_supporting_candidate() -> None:
    assert phase3sa_max_print_overhang <= 45.0
    assert port_printability_phase3sa()[
        "maximum_print_overhang_deg"
    ] <= 45.0


def test_port_surround_and_root_target_are_at_least_four_mm_class() -> None:
    report = port_printability_phase3sa()
    assert port_shell_reinforcement_thickness >= 4.0
    assert report["minimum_surrounding_structure_mm"] >= 4.0
    assert report["root_target"] == "R4_CLASS_CALIBRATION_PENDING"


def test_panel_does_not_own_final_round_netpot_fit() -> None:
    assert ROUNDNESS_OWNER == "SEPARATE_FLAT_PORT_FUNCTION_RING"
    assert NETPOT_FINAL_FIT == "NOT_IMPLEMENTED_CALIBRATION_PENDING"


def test_siawadeky_unknown_body_dimensions_remain_unselected() -> None:
    assert netpot_siawadeky_flange_diameter_assumed == 78.5
    assert netpot_siawadeky_height_assumed == 70.0
    assert netpot_siawadeky_body_diameter_pending is None
