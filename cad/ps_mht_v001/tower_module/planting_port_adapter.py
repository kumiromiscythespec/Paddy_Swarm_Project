"""Replaceable common tower-port adapter with keyed M3 retention."""

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
    port_adapter_inner_diameter,
    port_adapter_outer_diameter,
    port_rain_return_lip_height,
    port_receiver_key_depth,
    port_receiver_key_width,
)


MATERIAL = "PRINTED_PETG"
RETENTION = "TWO_M3_REPLACEABLE_METAL_NUTS"


def adapter_body_outer_diameter(
    clearance: float = port_adapter_fit_clearance,
) -> float:
    from ps_mht_v001.parameters import port_receiver_bore_diameter

    return port_receiver_bore_diameter - 2.0 * clearance


def _flange_with_lugs(z: float, height: float) -> cq.Workplane:
    flange = (
        cq.Workplane("XY")
        .circle(0.5 * port_adapter_flange_diameter)
        .circle(0.5 * port_adapter_inner_diameter)
        .extrude(height)
        .translate((0.0, 0.0, z))
    )
    for y in (-m3_fastener_pitch_radius, m3_fastener_pitch_radius):
        lug = (
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(m3_fastener_boss_radius)
            .extrude(height)
            .translate((0.0, 0.0, z))
        )
        flange = flange.union(lug)
    return flange


def _m3_holes(height: float) -> cq.Workplane:
    holes: cq.Workplane | None = None
    for y in (-m3_fastener_pitch_radius, m3_fastener_pitch_radius):
        hole = (
            cq.Workplane("XY")
            .center(0.0, y)
            .circle(0.5 * m3_clearance_diameter)
            .extrude(height)
            .translate((0.0, 0.0, -1.0))
        )
        holes = hole if holes is None else holes.union(hole)
    assert holes is not None
    return holes


def build_adapter_anti_rotation_key(
    body_outer_diameter: float = port_adapter_outer_diameter,
) -> cq.Workplane:
    """Single asymmetric key that fits only the receiver's +X slot."""

    body_radius = 0.5 * body_outer_diameter
    return (
        cq.Workplane("XY")
        .box(
            port_receiver_key_depth + 0.6,
            port_receiver_key_width - 1.0,
            0.7 * port_adapter_body_length,
            centered=(True, True, False),
        )
        .translate(
            (
                body_radius + 0.3,
                0.0,
                0.15 * port_adapter_body_length,
            )
        )
    )


def build_planting_port_adapter(
    clearance: float = port_adapter_fit_clearance,
) -> cq.Workplane:
    """Generic adapter carrier, deliberately independent of net-pot size."""

    outer_diameter = adapter_body_outer_diameter(clearance)
    body = (
        cq.Workplane("XY")
        .circle(0.5 * outer_diameter)
        .circle(0.5 * port_adapter_inner_diameter)
        .extrude(port_adapter_body_length)
    )
    flange = _flange_with_lugs(
        port_adapter_body_length - 0.5,
        port_adapter_flange_thickness + 0.5,
    )
    rain_lip = (
        cq.Workplane("XY")
        .circle(0.5 * port_adapter_inner_diameter + 2.5)
        .circle(0.5 * port_adapter_inner_diameter)
        .extrude(port_rain_return_lip_height)
        .translate(
            (
                0.0,
                0.0,
                port_adapter_body_length + port_adapter_flange_thickness,
            )
        )
    )
    model = body.union(flange).union(rain_lip)
    model = model.union(build_adapter_anti_rotation_key(outer_diameter))
    return model.cut(
        _m3_holes(
            port_adapter_body_length
            + port_adapter_flange_thickness
            + port_rain_return_lip_height
            + 2.0
        )
    )


def build_common_adapter_full_length_passage_probe() -> cq.Workplane:
    """Exact φ66 probe through the body, flange, and rain lip."""

    return (
        cq.Workplane("XY")
        .circle(0.5 * port_adapter_inner_diameter)
        .extrude(
            port_adapter_body_length
            + port_adapter_flange_thickness
            + port_rain_return_lip_height
            + 4.0
        )
        .translate((0.0, 0.0, -2.0))
    )


def m3_nominal_surrounding_wall() -> float:
    """Minimum real radial/tangential wall around each adapter M3 hole."""

    return min(
        m3_fastener_boss_radius - 0.5 * m3_clearance_diameter,
        (
            m3_fastener_pitch_radius
            - 0.5 * m3_clearance_diameter
            - 0.5 * port_adapter_inner_diameter
        ),
    )
