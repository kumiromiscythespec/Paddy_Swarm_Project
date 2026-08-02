"""Flat TPU/EPDM gasket reference for the removable port adapter."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    port_gasket_inner_diameter,
    port_gasket_outer_diameter,
    port_gasket_thickness,
)


MATERIAL = "TPU_OR_PURCHASED_EPDM"
STATUS = "CALIBRATION_PENDING_NON_PRESSURIZED"


def build_port_adapter_gasket() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(0.5 * port_gasket_outer_diameter)
        .circle(0.5 * port_gasket_inner_diameter)
        .extrude(port_gasket_thickness)
    )

