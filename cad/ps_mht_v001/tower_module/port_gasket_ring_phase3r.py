"""Large flat Phase 3R planting-port gasket carrier."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    m4_clearance_diameter,
    port_function_ring_fastener_pitch,
    port_function_ring_inner_diameter,
    port_function_ring_outer_diameter,
)


STATUS = "PHASE3R_LARGE_FLAT_PORT_GASKET"
PRINT_ORIENTATION = "FLAT_ON_LARGEST_FACE"
MATERIAL = "TPU_OR_CUT_EPDM_CALIBRATION_PENDING"
THICKNESS = 2.0


def build_port_gasket_ring_phase3r() -> cq.Workplane:
    gasket = (
        cq.Workplane("XY")
        .circle(0.5 * port_function_ring_outer_diameter - 2.0)
        .circle(0.5 * port_function_ring_inner_diameter)
        .extrude(THICKNESS)
    )
    for y in (-port_function_ring_fastener_pitch, port_function_ring_fastener_pitch):
        gasket = gasket.cut(
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(0.5 * m4_clearance_diameter)
            .extrude(THICKNESS + 2.0)
            .translate((0.0, 0.0, -1.0))
        )
    return gasket
