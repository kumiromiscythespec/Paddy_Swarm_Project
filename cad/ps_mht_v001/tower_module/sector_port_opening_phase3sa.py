"""Phase 3S-A planting opening retained from the fused Phase 3R.1 geometry."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    phase3sa_max_print_overhang,
    phase3sa_port_axis_angle,
    phase3sa_shell_wall,
    port_shell_reinforcement_thickness,
)
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r1 import (
    ROOT_FILLET_TARGET,
    build_self_supporting_port_frame_phase3r1,
    build_self_supporting_port_void_phase3r1,
)


STATUS = "PHASE3SA_PANEL_OWNS_NONCIRCULAR_STRUCTURAL_OPENING_ONLY"
ROUNDNESS_OWNER = "SEPARATE_FLAT_PORT_FUNCTION_RING"
NETPOT_FINAL_FIT = "NOT_IMPLEMENTED_CALIBRATION_PENDING"
SUPPORT_POLICY = "NO_SUPPORT_FIRST_CANDIDATE"


def add_sector_port_opening_phase3sa(
    panel: cq.Workplane,
    panel_height: float,
) -> cq.Workplane:
    center = 0.5 * panel_height
    frame = build_self_supporting_port_frame_phase3r1(center)
    void = build_self_supporting_port_void_phase3r1(center)
    return panel.union(frame).cut(void)


def port_printability_phase3sa() -> dict[str, float | str]:
    """Report print-frame overhang after assembly radial becomes print Z."""

    return {
        "assembly_axis_angle_deg": phase3sa_port_axis_angle,
        "maximum_print_overhang_deg": phase3sa_max_print_overhang,
        "minimum_surrounding_structure_mm":
            port_shell_reinforcement_thickness,
        "shell_wall_mm": phase3sa_shell_wall,
        "root_target": ROOT_FILLET_TARGET,
    }
