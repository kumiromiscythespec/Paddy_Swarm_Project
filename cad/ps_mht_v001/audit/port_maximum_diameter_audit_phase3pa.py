"""Reference-only 116/120/124 mm ring and 240 mm module audit."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.assembly.full_module_reference_phase3r1 import (
    _orient_at_port,
)
from ps_mht_v001.parameters import (
    m4_clearance_diameter,
    netpot_siawadeky_flange_outer_diameter,
    port_backing_ring_outer_diameter,
    port_function_ring_inner_diameter,
    port_function_ring_thickness,
    tower_max_diameter,
)
from ps_mht_v001.reference.siawadeky_netpot_reference_envelope_phase3pa import (
    build_siawadeky_netpot_reference_envelope_phase3pa,
)
from ps_mht_v001.tower_module.planting_port import maximum_radial_radius


BASELINE_PHASE3SA_MAXIMUM_DIAMETER_MM = 237.48183810800376
CANDIDATE_OUTER_DIAMETERS_MM = (116.0, 120.0, 124.0)
REFERENCE_RING_RADIAL_POSITION_MM = 85.4
STRUCTURAL_WALL_MINIMUM_MM = 3.0
NETPOT_FLANGE_BOTTOM_AT_RING_OUTER_FACE_LOCAL_Z_MM = (
    port_function_ring_thickness
)


def _candidate_ring(outer_diameter: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(0.5 * outer_diameter)
        .circle(0.5 * port_function_ring_inner_diameter)
        .extrude(port_function_ring_thickness)
    )


def build_reference_seated_netpot_phase3pa() -> cq.Workplane:
    """Seat the measured envelope on the existing ring's outward face."""

    local_shift = (
        NETPOT_FLANGE_BOTTOM_AT_RING_OUTER_FACE_LOCAL_Z_MM
        - 64.0
    )
    local = build_siawadeky_netpot_reference_envelope_phase3pa().translate(
        (0.0, 0.0, local_shift)
    )
    return _orient_at_port(local, 0.0, REFERENCE_RING_RADIAL_POSITION_MM)


def installed_netpot_maximum_diameter_phase3pa() -> float:
    return 2.0 * maximum_radial_radius(
        build_reference_seated_netpot_phase3pa()
    )


def candidate_maximum_diameter_phase3pa(outer_diameter: float) -> float:
    ring = _orient_at_port(
        _candidate_ring(outer_diameter),
        0.0,
        REFERENCE_RING_RADIAL_POSITION_MM,
    )
    ring_diameter = 2.0 * maximum_radial_radius(ring)
    return max(BASELINE_PHASE3SA_MAXIMUM_DIAMETER_MM, ring_diameter)


def ring_candidate_comparison_phase3pa() -> dict[str, object]:
    result: dict[str, object] = {}
    installed_pot_maximum = installed_netpot_maximum_diameter_phase3pa()
    flange_radius = 0.5 * netpot_siawadeky_flange_outer_diameter
    required_outboard_band = 2.0 * (
        0.5 * m4_clearance_diameter + STRUCTURAL_WALL_MINIMUM_MM
    )
    for outer_diameter in CANDIDATE_OUTER_DIAMETERS_MM:
        outer_radius = 0.5 * outer_diameter
        ring_only_maximum = candidate_maximum_diameter_phase3pa(
            outer_diameter
        )
        maximum = max(ring_only_maximum, installed_pot_maximum)
        margin = tower_max_diameter - maximum
        support = outer_radius - flange_radius
        outside_fastener_possible = support >= required_outboard_band
        if ring_only_maximum > tower_max_diameter:
            status = "REJECTED_MAXIMUM_DIAMETER"
        elif maximum > tower_max_diameter:
            status = "REDESIGN_REQUIRED_INSTALLED_POT_MAXIMUM_DIAMETER"
        elif not outside_fastener_possible:
            status = "REDESIGN_REQUIRED_FASTENER"
        else:
            status = "PASS_AS_REFERENCE"
        if (
            outer_diameter == 120.0
            and ring_only_maximum <= tower_max_diameter
            and tower_max_diameter - ring_only_maximum < 0.5
            and maximum <= tower_max_diameter
        ):
            status = "REDESIGN_REQUIRED_LOW_DIAMETER_MARGIN"
        result[f"od_{int(outer_diameter)}"] = {
            "outer_diameter_mm": outer_diameter,
            "flange_outer_margin_mm": support,
            "outside_flange_m4_band_required_mm": required_outboard_band,
            "outside_flange_m4_possible_with_3mm_walls":
                outside_fastener_possible,
            "reference_ring_only_maximum_module_diameter_mm":
                ring_only_maximum,
            "reference_installed_netpot_maximum_diameter_mm":
                installed_pot_maximum,
            "reference_maximum_module_diameter_mm": maximum,
            "limit_margin_mm": margin,
            "ring_only_within_240mm":
                ring_only_maximum <= tower_max_diameter,
            "within_240mm": margin >= 0.0,
            "candidate_adoption": False,
            "panel_reinforcement": (
                "EXISTING_116_DATUM"
                if outer_diameter == 116.0
                else "REQUIRES_REAUDIT_NO_GEOMETRY_GENERATED"
            ),
            "backing_ring_alignment": (
                "FUNCTION_RING_2MM_PER_SIDE_INSIDE_BACKING"
                if outer_diameter == 116.0
                else "OUTER_DIAMETERS_MATCH"
                if outer_diameter == port_backing_ring_outer_diameter
                else "FUNCTION_RING_2MM_PER_SIDE_OUTSIDE_BACKING"
            ),
            "status": status,
        }
    return {
        "baseline_phase3sa_maximum_diameter_mm":
            BASELINE_PHASE3SA_MAXIMUM_DIAMETER_MM,
        "tower_limit_mm": tower_max_diameter,
        "installed_netpot_reference": {
            "seat_datum": "PHASE3R1_RING_OUTER_FACE_AT_27_DEGREES",
            "maximum_diameter_mm": installed_pot_maximum,
            "within_240mm": installed_pot_maximum <= tower_max_diameter,
            "status": "REDESIGN_REQUIRED_MAXIMUM_DIAMETER",
        },
        "candidates": result,
        "local_ear_reference": {
            "status": "REFERENCE_ONLY_NOT_GENERATED",
            "minimum_local_outer_radius_for_18mm_head_and_3mm_wall_mm":
                75.0,
            "warning": "LIKELY_EXCEEDS_240MM_REQUIRES_DEDICATED_REDESIGN",
        },
        "inboard_fastener_reference": {
            "status": "POT_REMOVED_ONLY_REFERENCE",
            "existing_axis_radius_mm": 50.0,
            "finalized": False,
        },
    }


def maximum_diameter_audit_phase3pa() -> dict[str, object]:
    comparison = ring_candidate_comparison_phase3pa()
    rejected = [
        name
        for name, item in comparison["candidates"].items()
        if not item["within_240mm"]
    ]
    ring_only_rejected = [
        name
        for name, item in comparison["candidates"].items()
        if not item["ring_only_within_240mm"]
    ]
    return {
        "status": "REDESIGN_REQUIRED",
        "limit_mm": tower_max_diameter,
        "baseline_mm": BASELINE_PHASE3SA_MAXIMUM_DIAMETER_MM,
        "rejected_candidates": rejected,
        "ring_only_rejected_candidates": ring_only_rejected,
        "installed_netpot_maximum_diameter_mm": comparison[
            "installed_netpot_reference"
        ]["maximum_diameter_mm"],
        "installed_netpot_exceeds_limit": not comparison[
            "installed_netpot_reference"
        ]["within_240mm"],
        "od_124_rejected": "od_124" in rejected,
        "measured_values_or_27deg_axis_changed": False,
        "final_ring_selected": None,
    }
