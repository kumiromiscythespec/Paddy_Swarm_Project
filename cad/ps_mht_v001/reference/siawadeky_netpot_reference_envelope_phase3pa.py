"""Conservative measured Siawadeky interference envelope, not a pot model."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    netpot_siawadeky_body_height_below_flange,
    netpot_siawadeky_flange_outer_diameter,
    netpot_siawadeky_flange_thickness,
    netpot_siawadeky_max_body_outer_diameter,
)
from ps_mht_v001.reference.siawadeky_netpot_measurements_phase3pa import (
    siawadeky_measurements_phase3pa,
)


STATUS = "REFERENCE_ENVELOPE_NOT_A_PRINTABLE_NETPOT_MODEL"
PRINT_STATUS = "REFERENCE_STEP_ONLY_NO_STL"
SOLID_COUNT = 1


def build_siawadeky_netpot_reference_envelope_phase3pa() -> cq.Workplane:
    body = (
        cq.Workplane("XY")
        .circle(0.5 * netpot_siawadeky_max_body_outer_diameter)
        .extrude(netpot_siawadeky_body_height_below_flange)
    )
    flange = (
        cq.Workplane("XY")
        .circle(0.5 * netpot_siawadeky_flange_outer_diameter)
        .extrude(netpot_siawadeky_flange_thickness)
        .translate((0.0, 0.0, netpot_siawadeky_body_height_below_flange))
    )
    return body.union(flange)


def reference_envelope_metadata_phase3pa() -> dict[str, object]:
    return {
        "status": STATUS,
        "print_status": PRINT_STATUS,
        "geometry_policy": "CONSERVATIVE_FULL_HEIGHT_BODY_CYLINDER",
        "solid_count": SOLID_COUNT,
        "measurements": siawadeky_measurements_phase3pa(),
        "internal_diameters_geometry": "NOT_MODELED_REFERENCE_ONLY",
    }
