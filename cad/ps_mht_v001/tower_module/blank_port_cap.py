"""Blank cap using the same keyed two-M3 common receiver."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    m3_clearance_diameter,
    m3_fastener_boss_radius,
    m3_fastener_pitch_radius,
    port_adapter_body_length,
    port_adapter_fit_clearance,
    port_adapter_flange_diameter,
    port_adapter_flange_thickness,
    port_rain_return_lip_height,
)
from ps_mht_v001.tower_module.planting_port_adapter import (
    adapter_body_outer_diameter,
    build_adapter_anti_rotation_key,
)


MATERIAL = "PRINTED_PETG"
RETENTION = "SAME_TWO_M3_COMMON_RECEIVER"


def build_blank_port_cap(
    clearance: float = port_adapter_fit_clearance,
) -> cq.Workplane:
    """Close an unused port with a keyed body and external rain-return lip."""

    outer_diameter = adapter_body_outer_diameter(clearance)
    body = (
        cq.Workplane("XY")
        .circle(0.5 * outer_diameter)
        .extrude(port_adapter_body_length)
    )
    flange = (
        cq.Workplane("XY")
        .circle(0.5 * port_adapter_flange_diameter)
        .extrude(port_adapter_flange_thickness)
        .translate((0.0, 0.0, port_adapter_body_length - 0.5))
    )
    model = body.union(flange).union(
        build_adapter_anti_rotation_key(outer_diameter)
    )
    for y in (-m3_fastener_pitch_radius, m3_fastener_pitch_radius):
        lug = (
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(m3_fastener_boss_radius)
            .extrude(port_adapter_flange_thickness)
            .translate((0.0, 0.0, port_adapter_body_length - 0.5))
        )
        hole = (
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(0.5 * m3_clearance_diameter)
            .extrude(port_adapter_flange_thickness + 2.0)
            .translate((0.0, 0.0, port_adapter_body_length - 1.0))
        )
        model = model.union(lug).cut(hole)
    rain_return = (
        cq.Workplane("XY")
        .circle(0.5 * port_adapter_flange_diameter)
        .circle(0.5 * port_adapter_flange_diameter - 2.0)
        .extrude(port_rain_return_lip_height)
        .translate(
            (
                0.0,
                0.0,
                port_adapter_body_length + port_adapter_flange_thickness - 0.5,
            )
        )
    )
    return model.union(rain_return)

