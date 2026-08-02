"""Measured-pot audit of the unchanged Phase 3R.1 port ring stack."""

from __future__ import annotations

from ps_mht_v001.audit.port_fastener_envelope_audit_phase3pa import (
    port_fastener_envelope_audit_phase3pa,
)
from ps_mht_v001.audit.port_maximum_diameter_audit_phase3pa import (
    build_reference_seated_netpot_phase3pa,
    installed_netpot_maximum_diameter_phase3pa,
)
from ps_mht_v001.parameters import (
    netpot_siawadeky_flange_outer_diameter,
    netpot_siawadeky_max_body_outer_diameter,
    port_backing_ring_inner_diameter,
    port_backing_ring_outer_diameter,
    port_function_ring_inner_diameter,
    port_function_ring_outer_diameter,
    port_function_ring_thickness,
    port_shell_opening_height,
    port_shell_opening_width,
    root_sleeve_ring_inner_diameter_phase3r,
    root_sleeve_ring_outer_diameter_phase3r,
)
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r1 import (
    build_three_port_module_shell_phase3r1,
)


STATUS = "REDESIGN_REQUIRED"


def _intersection_volume(first, second) -> float:
    return sum(
        solid.Volume()
        for solid in first.intersect(second).solids().vals()
    )


def port_function_ring_audit_phase3pa() -> dict[str, object]:
    flange_support = 0.5 * (
        netpot_siawadeky_flange_outer_diameter
        - port_function_ring_inner_diameter
    )
    outer_residual = 0.5 * (
        port_function_ring_outer_diameter
        - netpot_siawadeky_flange_outer_diameter
    )
    fastener = port_fastener_envelope_audit_phase3pa()
    seated_pot = build_reference_seated_netpot_phase3pa()
    shell_intersection = _intersection_volume(
        seated_pot,
        build_three_port_module_shell_phase3r1(),
    )
    return {
        "status": STATUS,
        "existing_ring_mm": {
            "outer_diameter": port_function_ring_outer_diameter,
            "inner_diameter": port_function_ring_inner_diameter,
            "thickness": port_function_ring_thickness,
        },
        "flange_seating": {
            "measured_flange_diameter_mm":
                netpot_siawadeky_flange_outer_diameter,
            "full_circular_seating_geometrically_possible": True,
            "flange_support_radial_width_mm": flange_support,
            "ring_outside_flange_radial_width_mm": outer_residual,
            "continuous_support_interrupted_by_existing_m4_holes": True,
            "status": "PASS_AS_REFERENCE",
        },
        "body_passage": {
            "body_diameter_mm": netpot_siawadeky_max_body_outer_diameter,
            "existing_bore_diameter_mm": port_function_ring_inner_diameter,
            "diametral_clearance_mm": (
                port_function_ring_inner_diameter
                - netpot_siawadeky_max_body_outer_diameter
            ),
            "status": "NOT_FINAL_EXCESS_CLEARANCE",
        },
        "m4_fastener": {
            "status": "FAIL_FASTENER_INTERFERENCE",
            "summary": fastener,
        },
        "tool_envelope": {
            "status": "FAIL_TOOL_ENVELOPE",
            "pot_installed_access": False,
            "pot_removed_access": True,
        },
        "panel_opening": {
            "opening_width_mm": port_shell_opening_width,
            "opening_height_mm": port_shell_opening_height,
            "body_width_clearance_mm": (
                port_shell_opening_width
                - netpot_siawadeky_max_body_outer_diameter
            ),
            "body_height_clearance_mm": (
                port_shell_opening_height
                - netpot_siawadeky_max_body_outer_diameter
            ),
            "axis_angle_deg": 27.0,
            "seated_pot_shell_intersection_volume_mm3":
                shell_intersection,
            "cad_boolean_intersection_free": shell_intersection <= 1.0e-7,
            "status": "REDESIGN_REQUIRED_SHELL_INTERFERENCE",
        },
        "backing_ring": {
            "outer_diameter_mm": port_backing_ring_outer_diameter,
            "inner_diameter_mm": port_backing_ring_inner_diameter,
            "body_diametral_clearance_mm": (
                port_backing_ring_inner_diameter
                - netpot_siawadeky_max_body_outer_diameter
            ),
            "status": "PASS_AS_REFERENCE",
        },
        "root_sleeve_ring": {
            "outer_diameter_mm": root_sleeve_ring_outer_diameter_phase3r,
            "inner_diameter_mm": root_sleeve_ring_inner_diameter_phase3r,
            "body_passage_deficit_mm": (
                netpot_siawadeky_max_body_outer_diameter
                - root_sleeve_ring_inner_diameter_phase3r
            ),
            "status": "REDESIGN_REQUIRED",
        },
        "root_zone_projection": {
            "body_depth_below_flange_mm": 64.0,
            "status": "REDESIGN_REQUIRED_ROOT_ZONE_REAUDIT",
        },
        "maximum_diameter": {
            "installed_measured_pot_reference_mm":
                installed_netpot_maximum_diameter_phase3pa(),
            "limit_mm": 240.0,
            "status": "FAIL_MAXIMUM_DIAMETER",
        },
        "final_conclusion": (
            "The 116 mm ring supports the flange and passes the body, but "
            "the seated measured envelope intersects the shell/frame, "
            "exceeds the 240 mm installed envelope, and is incompatible "
            "with the existing M4/tool and 50 mm root-sleeve geometry."
        ),
    }
