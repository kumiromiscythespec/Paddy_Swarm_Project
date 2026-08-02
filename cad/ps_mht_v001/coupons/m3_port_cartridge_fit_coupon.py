"""Actual receiver-lug M3 cartridge/gate coupon at three clearances."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    m3_port_cartridge_clearance_candidates,
)
from ps_mht_v001.tower_module.m3_port_nut_cartridge import (
    build_m3_port_bolt_axis_reference,
    build_m3_port_nut_cartridge,
    build_m3_port_nut_cartridge_retainer,
)
from ps_mht_v001.tower_module.planting_port import (
    build_receiver_outer_local,
    build_receiver_void_local,
)


M3_CARTRIDGE_CLEARANCES = m3_port_cartridge_clearance_candidates
COUPON_SOLID_COUNT = 12
STATUS = "DO_NOT_REPRINT_DEPRECATED_AFTER_PHYSICAL_FAILURE"
PRINT_ORIENTATION = "RECEIVER_SECTION_AND_LOOSE_PARTS_FLAT"


def _receiver_lug_section(
    clearance: float,
    marker_count: int,
) -> cq.Workplane:
    receiver = build_receiver_outer_local().cut(
        build_receiver_void_local(m3_cartridge_clearance=clearance)
    )
    cutter = (
        cq.Workplane("XY")
        .box(28.0, 24.0, 14.0, centered=(True, True, False))
        .translate((0.0, 43.0, -1.0))
    )
    section = receiver.intersect(cutter)
    for index in range(marker_count):
        dot = (
            cq.Workplane("XY")
            .circle(1.0)
            .extrude(0.8)
            .translate((-6.0 + index * 3.0, 48.0, 11.7))
        )
        section = section.union(dot)
    return section


def build_m3_port_cartridge_fit_coupon() -> cq.Workplane:
    shapes: list[cq.Shape] = []
    for index, clearance in enumerate(M3_CARTRIDGE_CLEARANCES, start=1):
        x = -60.0 + (index - 1) * 60.0
        receiver = _receiver_lug_section(clearance, index).translate(
            (x, -43.0, 0.0)
        )
        cartridge = build_m3_port_nut_cartridge().translate(
            (x, -25.0, 0.0)
        )
        gate = build_m3_port_nut_cartridge_retainer().translate(
            (x, 25.0, 0.0)
        )
        bolt_axis = build_m3_port_bolt_axis_reference(1).translate(
            (x + 18.0, -43.0, 0.0)
        )
        shapes.extend(
            (receiver.val(), cartridge.val(), gate.val(), bolt_axis.val())
        )
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])
