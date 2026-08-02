"""Simplified purchased nominal-60 net-pot reference geometry."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    netpot_body_bottom_outer_diameter,
    netpot_body_height,
    netpot_body_top_outer_diameter,
    netpot_flange_outer_diameter,
    netpot_flange_thickness,
    netpot_insertion_clearance,
    netpot_lip_height,
    netpot_slot_count,
    netpot_slot_width,
    port_service_sweep_length,
)


REFERENCE_STATUS = "REFERENCE_PURCHASED_PART"
MEASUREMENT_STATUS = "CALIBRATION_PENDING"
NETPOT_REFERENCE_SOLID_COUNT_WITH_AXIS = 2


def _tapered_shell() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .workplane(offset=netpot_flange_thickness)
        .circle(0.5 * netpot_body_top_outer_diameter)
        .workplane(offset=netpot_body_height)
        .circle(0.5 * netpot_body_bottom_outer_diameter)
        .loft(combine=True)
    )
    wall = 1.5
    inner = (
        cq.Workplane("XY")
        .workplane(offset=netpot_flange_thickness - 0.2)
        .circle(0.5 * netpot_body_top_outer_diameter - wall)
        .workplane(offset=netpot_body_height + 0.4)
        .circle(0.5 * netpot_body_bottom_outer_diameter - wall)
        .loft(combine=True)
    )
    return outer.cut(inner)


def build_netpot_reference() -> cq.Workplane:
    """Build one simplified slotted purchased-part interference solid."""

    flange = (
        cq.Workplane("XY")
        .circle(0.5 * netpot_flange_outer_diameter)
        .circle(0.5 * netpot_body_top_outer_diameter - 1.5)
        .extrude(netpot_flange_thickness)
    )
    lip = (
        cq.Workplane("XY")
        .circle(0.5 * netpot_flange_outer_diameter)
        .circle(0.5 * netpot_flange_outer_diameter - 1.5)
        .extrude(netpot_lip_height)
    )
    model = flange.union(lip).union(_tapered_shell())
    slot_height = 0.58 * netpot_body_height
    slot_z = netpot_flange_thickness + 0.20 * netpot_body_height
    slot_radius = 0.43 * netpot_body_top_outer_diameter
    for index in range(netpot_slot_count):
        angle = index * 360.0 / netpot_slot_count
        slot = (
            cq.Workplane("XY")
            .box(
                14.0,
                netpot_slot_width,
                slot_height,
                centered=(True, True, False),
            )
            .translate((slot_radius, 0.0, slot_z))
            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle)
        )
        model = model.cut(slot)
    bottom_opening = (
        cq.Workplane("XY")
        .circle(0.5 * netpot_body_bottom_outer_diameter - 2.0)
        .extrude(4.0)
        .translate(
            (
                0.0,
                0.0,
                netpot_flange_thickness + netpot_body_height - 2.0,
            )
        )
    )
    return model.cut(bottom_opening)


def build_netpot_insertion_axis_reference() -> cq.Workplane:
    """Non-printing insertion-axis datum placed clear of the purchased part."""

    return (
        cq.Workplane("XY")
        .center(40.0, 0.0)
        .circle(0.7)
        .extrude(
            netpot_flange_thickness
            + netpot_body_height
            + netpot_insertion_clearance
        )
    )


def build_netpot_reference_with_axis() -> cq.Workplane:
    shapes = [
        build_netpot_reference().val(),
        build_netpot_insertion_axis_reference().val(),
    ]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


def build_netpot_insertion_sweep_local(
    length: float = port_service_sweep_length,
) -> cq.Workplane:
    """Conservative extraction cylinder based on the maximum flange."""

    return (
        cq.Workplane("XY")
        .circle(0.5 * netpot_flange_outer_diameter)
        .extrude(length)
    )

