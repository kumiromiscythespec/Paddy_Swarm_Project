"""Replaceable metal-nut carrier behind the two-M3 receiver lugs."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    m3_clearance_diameter,
    m3_fastener_boss_radius,
    m3_fastener_pitch_radius,
    m3_metal_nut_across_flats,
    m3_metal_nut_thickness,
    port_adapter_flange_diameter,
    port_receiver_bore_diameter,
)


MATERIAL = "PRINTED_PETG_WITH_REPLACEABLE_METAL_NUTS"
STATUS = "DEPRECATED_NOT_EXTERNALLY_SERVICEABLE"


def build_port_adapter_retainer() -> cq.Workplane:
    """Annular bridge with two externally serviceable hex-nut pockets."""

    thickness = 4.0
    model = (
        cq.Workplane("XY")
        .circle(0.5 * port_adapter_flange_diameter)
        .circle(0.5 * port_receiver_bore_diameter)
        .extrude(thickness)
    )
    nut_diameter = m3_metal_nut_across_flats / 0.8660254037844386
    for y in (-m3_fastener_pitch_radius, m3_fastener_pitch_radius):
        lug = (
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(m3_fastener_boss_radius)
            .extrude(thickness)
        )
        hole = (
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(0.5 * m3_clearance_diameter)
            .extrude(thickness + 2.0)
            .translate((0.0, 0.0, -1.0))
        )
        nut_pocket = (
            cq.Workplane("XY")
            .center(0.0, y)
            .polygon(6, nut_diameter)
            .extrude(m3_metal_nut_thickness + 0.25)
            .translate(
                (
                    0.0,
                    0.0,
                    thickness - m3_metal_nut_thickness - 0.25,
                )
            )
        )
        model = model.union(lug).cut(hole).cut(nut_pocket)
    return model
