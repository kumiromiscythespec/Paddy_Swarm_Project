"""Phase 2 M4 hardware envelopes and replaceable nut-cartridge parts."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    m4_bolt_length,
    m4_clearance_diameter,
    interface_fastener_pitch_radius,
    m4_nut_across_flats,
    m4_nut_thickness,
    m4_star_knob_envelope_diameter,
    m4_star_knob_envelope_height,
    m4_washer_diameter,
)

M4_CARTRIDGE_STATUS = "DEPRECATED_AFTER_PRINT_FAILURE"
M4_RETAINER_STATUS = "DEPRECATED_AFTER_PRINT_FAILURE"


# Local cartridge coordinate system:
# X is radial (outward is +X), Y is tangential, and Z is the M4 axis.
CARTRIDGE_RADIAL_LENGTH = 11.4
CARTRIDGE_TANGENTIAL_WIDTH = 11.5
CARTRIDGE_HEIGHT = 5.2
CARTRIDGE_FASTENER_X = -1.2
CARTRIDGE_PLACEMENT_RADIUS = 111.2
CARTRIDGE_BOTTOM_Z = 1.4

RETAINER_RADIAL_THICKNESS = 2.2
RETAINER_TANGENTIAL_WIDTH = 18.0
RETAINER_HEIGHT = 8.5
RETAINER_PLACEMENT_RADIUS = 118.6
RETAINER_BOTTOM_Z = 0.4
RETAINER_LOCK_ARM_RADIAL_LENGTH = 10.8
RETAINER_LOCK_ARM_TANGENTIAL_WIDTH = 10.0
RETAINER_LOCK_ARM_THICKNESS = 2.0
RETAINER_LOCK_HOLE_X = (
    interface_fastener_pitch_radius - RETAINER_PLACEMENT_RADIUS
)


def build_m4_nut_cartridge() -> cq.Workplane:
    """Build a side-load M4 hex-nut cartridge.

    The roof and floor prevent the purchased nut from dropping toward the root
    zone. The outer radial feed opening is closed by the separate retainer.
    """

    cartridge = cq.Workplane("XY").box(
        CARTRIDGE_RADIAL_LENGTH,
        CARTRIDGE_TANGENTIAL_WIDTH,
        CARTRIDGE_HEIGHT,
        centered=(True, True, False),
    )
    through_hole = (
        cq.Workplane("XY")
        .center(CARTRIDGE_FASTENER_X, 0.0)
        .circle(0.5 * m4_clearance_diameter)
        .extrude(CARTRIDGE_HEIGHT + 2.0)
        .translate((0.0, 0.0, -1.0))
    )
    nut_circumscribed_diameter = m4_nut_across_flats / 0.8660254037844386
    nut_chamber = (
        cq.Workplane("XY")
        .center(CARTRIDGE_FASTENER_X, 0.0)
        .polygon(6, nut_circumscribed_diameter)
        .extrude(m4_nut_thickness + 0.35)
        .translate((0.0, 0.0, 0.9))
    )
    feed_length = (
        0.5 * CARTRIDGE_RADIAL_LENGTH - CARTRIDGE_FASTENER_X + 0.2
    )
    nut_feed = (
        cq.Workplane("XY")
        .box(
            feed_length,
            m4_nut_across_flats + 0.35,
            m4_nut_thickness + 0.35,
            centered=(True, True, False),
        )
        .translate(
            (
                CARTRIDGE_FASTENER_X + 0.5 * feed_length,
                0.0,
                0.9,
            )
        )
    )
    return cartridge.cut(through_hole).cut(nut_chamber.union(nut_feed))


def build_m4_nut_cartridge_retainer() -> cq.Workplane:
    """Build the external slide-gate with an M4-captured locking arm."""

    gate = cq.Workplane("XY").box(
        RETAINER_RADIAL_THICKNESS,
        RETAINER_TANGENTIAL_WIDTH,
        RETAINER_HEIGHT,
        centered=(True, True, False),
    )
    arm = (
        cq.Workplane("XY")
        .box(
            RETAINER_LOCK_ARM_RADIAL_LENGTH,
            RETAINER_LOCK_ARM_TANGENTIAL_WIDTH,
            RETAINER_LOCK_ARM_THICKNESS,
            centered=(True, True, False),
        )
        .translate(
            (
                -0.5 * RETAINER_LOCK_ARM_RADIAL_LENGTH,
                0.0,
                RETAINER_HEIGHT,
            )
        )
    )
    lock_hole = (
        cq.Workplane("XY")
        .center(RETAINER_LOCK_HOLE_X, 0.0)
        .circle(0.5 * m4_clearance_diameter)
        .extrude(RETAINER_LOCK_ARM_THICKNESS + 0.4)
        .translate((0.0, 0.0, RETAINER_HEIGHT - 0.2))
    )
    return gate.union(arm).cut(lock_hole)


def build_m4_star_knob_reference() -> cq.Workplane:
    """Build a conservative low-profile M4 star-knob purchasing envelope."""

    knob = (
        cq.Workplane("XY")
        .circle(0.5 * m4_star_knob_envelope_diameter)
        .extrude(m4_star_knob_envelope_height)
    )
    washer = (
        cq.Workplane("XY")
        .circle(0.5 * m4_washer_diameter)
        .extrude(1.0)
        .translate((0.0, 0.0, m4_star_knob_envelope_height))
    )
    shaft = (
        cq.Workplane("XY")
        .circle(2.0)
        .extrude(m4_bolt_length)
        .translate((0.0, 0.0, m4_star_knob_envelope_height + 1.0))
    )
    return knob.union(washer).union(shaft)
