"""Externally replaceable independent M3 nut cartridge and captured gate."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    m3_clearance_diameter,
    m3_fastener_pitch_radius,
    m3_metal_nut_across_flats,
    m3_metal_nut_thickness,
    m3_port_cartridge_bottom_z,
    m3_port_cartridge_center_offset,
    m3_port_cartridge_clearance,
    m3_port_cartridge_fastener_x,
    m3_port_cartridge_height,
    m3_port_cartridge_length,
    m3_port_cartridge_width,
    m3_port_lug_housing_width,
    m3_port_retainer_arm_length,
    m3_port_retainer_arm_thickness,
    m3_port_retainer_arm_width,
    m3_port_retainer_bottom_z,
    m3_port_retainer_center_offset,
    m3_port_retainer_gate_height,
    m3_port_retainer_gate_thickness,
    m3_port_retainer_gate_width,
)


CARTRIDGE_STATUS = "DEPRECATED_AFTER_PRINT_FAILURE"
RETAINER_STATUS = "DEPRECATED_AFTER_PRINT_FAILURE"
PRINT_ORIENTATION = "BROAD_SIDE_ON_BED_NO_SUPPORT_TARGET"


def build_m3_port_nut_cartridge() -> cq.Workplane:
    """Side-load cartridge with floor/roof preventing root-side nut loss."""

    cartridge = cq.Workplane("XY").box(
        m3_port_cartridge_length,
        m3_port_cartridge_width,
        m3_port_cartridge_height,
        centered=(True, True, False),
    )
    through = (
        cq.Workplane("XY")
        .center(m3_port_cartridge_fastener_x, 0.0)
        .circle(0.5 * m3_clearance_diameter)
        .extrude(m3_port_cartridge_height + 2.0)
        .translate((0.0, 0.0, -1.0))
    )
    nut_diameter = m3_metal_nut_across_flats / 0.8660254037844386
    nut_height = m3_metal_nut_thickness + 0.30
    nut_chamber = (
        cq.Workplane("XY")
        .center(m3_port_cartridge_fastener_x, 0.0)
        .polygon(6, nut_diameter + 0.30)
        .extrude(nut_height)
        .translate((0.0, 0.0, 0.9))
    )
    feed_length = (
        0.5 * m3_port_cartridge_length
        - m3_port_cartridge_fastener_x
        + 0.2
    )
    nut_feed = (
        cq.Workplane("XY")
        .box(
            feed_length,
            m3_metal_nut_across_flats + 0.30,
            nut_height,
            centered=(True, True, False),
        )
        .translate(
            (
                m3_port_cartridge_fastener_x + 0.5 * feed_length,
                0.0,
                0.9,
            )
        )
    )
    return cartridge.cut(through).cut(nut_chamber.union(nut_feed))


def build_m3_port_nut_cartridge_retainer() -> cq.Workplane:
    """Rigid slide gate with a 2.4 mm arm captured by the normal M3 bolt."""

    gate = cq.Workplane("XY").box(
        m3_port_retainer_gate_thickness,
        m3_port_retainer_gate_width,
        m3_port_retainer_gate_height,
        centered=(True, True, False),
    )
    arm = (
        cq.Workplane("XY")
        .box(
            m3_port_retainer_arm_length,
            m3_port_retainer_arm_width,
            m3_port_retainer_arm_thickness,
            centered=(True, True, False),
        )
        .translate(
            (
                -0.5 * m3_port_retainer_arm_length,
                0.0,
                m3_port_retainer_gate_height,
            )
        )
    )
    lock_hole = (
        cq.Workplane("XY")
        .center(-m3_port_retainer_center_offset, 0.0)
        .circle(0.5 * m3_clearance_diameter)
        .extrude(m3_port_retainer_arm_thickness + 0.4)
        .translate((0.0, 0.0, m3_port_retainer_gate_height - 0.2))
    )
    return gate.union(arm).cut(lock_hole)


def build_m3_port_cartridge_slot_void(
    clearance: float = m3_port_cartridge_clearance,
) -> cq.Workplane:
    """Pocket, side feed, gate slot, and washable open arm recess."""

    pocket = (
        cq.Workplane("XY")
        .box(
            m3_port_cartridge_length + 2.0 * clearance,
            m3_port_cartridge_width + 2.0 * clearance,
            m3_port_cartridge_height + 2.0 * clearance,
            centered=(True, True, False),
        )
        .translate(
            (
                m3_port_cartridge_center_offset,
                0.0,
                m3_port_cartridge_bottom_z - clearance,
            )
        )
    )
    feed = (
        cq.Workplane("XY")
        .box(
            9.0,
            m3_port_cartridge_width + 2.0 * clearance,
            m3_port_cartridge_height + 2.0 * clearance,
            centered=(True, True, False),
        )
        .translate(
            (
                5.5,
                0.0,
                m3_port_cartridge_bottom_z - clearance,
            )
        )
    )
    gate_slot = (
        cq.Workplane("XY")
        .box(
            m3_port_retainer_gate_thickness + 2.0 * clearance,
            m3_port_retainer_gate_width + 2.0 * clearance,
            m3_port_retainer_gate_height + 2.0 * clearance,
            centered=(True, True, False),
        )
        .translate(
            (
                m3_port_retainer_center_offset,
                0.0,
                m3_port_retainer_bottom_z - clearance,
            )
        )
    )
    arm_recess = (
        cq.Workplane("XY")
        .box(
            m3_port_retainer_arm_length + 2.0 * clearance,
            m3_port_retainer_arm_width + 2.0 * clearance,
            m3_port_retainer_arm_thickness + 2.0 * clearance,
            centered=(True, True, False),
        )
        .translate(
            (
                m3_port_retainer_center_offset
                - 0.5 * m3_port_retainer_arm_length,
                0.0,
                m3_port_retainer_bottom_z
                + m3_port_retainer_gate_height
                - clearance,
            )
        )
    )
    return pocket.union(feed).union(gate_slot).union(arm_recess)


def _orient_lug(model: cq.Workplane, side: int) -> cq.Workplane:
    if side not in (-1, 1):
        raise ValueError("side must be -1 or +1")
    return (
        model.rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            90.0 * side,
        )
        .translate((0.0, side * m3_fastener_pitch_radius, 0.0))
    )


def place_m3_port_nut_cartridge(
    cartridge: cq.Workplane,
    side: int,
) -> cq.Workplane:
    local = cartridge.translate(
        (
            m3_port_cartridge_center_offset,
            0.0,
            m3_port_cartridge_bottom_z,
        )
    )
    return _orient_lug(local, side)


def place_m3_port_cartridge_retainer(
    retainer: cq.Workplane,
    side: int,
) -> cq.Workplane:
    local = retainer.translate(
        (
            m3_port_retainer_center_offset,
            0.0,
            m3_port_retainer_bottom_z,
        )
    )
    return _orient_lug(local, side)


def place_m3_port_cartridge_slot(
    slot: cq.Workplane,
    side: int,
) -> cq.Workplane:
    return _orient_lug(slot, side)


def build_m3_port_bolt_axis_reference(side: int) -> cq.Workplane:
    axis = (
        cq.Workplane("XY")
        .circle(0.5 * m3_clearance_diameter)
        .extrude(24.0)
        .translate((0.0, 0.0, -2.0))
    )
    return _orient_lug(axis, side)


def build_m3_port_cartridge_removal_sweep(side: int) -> cq.Workplane:
    """Straight side-removal envelope extending 45 mm outside the lug."""

    sweep = (
        cq.Workplane("XY")
        .box(
            54.0,
            m3_port_cartridge_width + 0.4,
            m3_port_cartridge_height + 0.4,
            centered=(True, True, False),
        )
        .translate((23.3, 0.0, m3_port_cartridge_bottom_z - 0.2))
    )
    return _orient_lug(sweep, side)


def m3_cartridge_slot_side_wall(clearance: float) -> float:
    """Nominal lateral wall around the real pocket in the lug housing."""

    return 0.5 * (
        m3_port_lug_housing_width
        - m3_port_cartridge_width
        - 2.0 * clearance
    )
