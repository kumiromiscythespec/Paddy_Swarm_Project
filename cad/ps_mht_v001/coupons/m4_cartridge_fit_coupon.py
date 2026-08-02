"""Replaceable M4 cartridge/retainer fit coupon with three clearances."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.common.fasteners import (
    CARTRIDGE_HEIGHT,
    CARTRIDGE_RADIAL_LENGTH,
    CARTRIDGE_TANGENTIAL_WIDTH,
    RETAINER_HEIGHT,
    RETAINER_RADIAL_THICKNESS,
    RETAINER_TANGENTIAL_WIDTH,
    build_m4_nut_cartridge,
    build_m4_nut_cartridge_retainer,
)
from ps_mht_v001.parameters import m4_clearance_diameter


CARTRIDGE_CLEARANCES = (0.20, 0.30, 0.40)
COUPON_SOLID_COUNT = 9
STATUS = "DO_NOT_REPRINT_DEPRECATED_AFTER_PHYSICAL_FAILURE"


def _receiver_block(clearance: float, marker_count: int) -> cq.Workplane:
    block = cq.Workplane("XY").box(
        44.0,
        28.0,
        12.0,
        centered=(True, True, False),
    )
    cartridge_pocket = (
        cq.Workplane("XY")
        .box(
            CARTRIDGE_RADIAL_LENGTH + 2.0 * clearance,
            CARTRIDGE_TANGENTIAL_WIDTH + 2.0 * clearance,
            CARTRIDGE_HEIGHT + clearance,
            centered=(True, True, False),
        )
        .translate((8.0, 0.0, 1.5))
    )
    external_feed = (
        cq.Workplane("XY")
        .box(
            18.0,
            CARTRIDGE_TANGENTIAL_WIDTH + 2.0 * clearance,
            CARTRIDGE_HEIGHT + clearance,
            centered=(True, True, False),
        )
        .translate((19.0, 0.0, 1.5))
    )
    retainer_slot = (
        cq.Workplane("XY")
        .box(
            RETAINER_RADIAL_THICKNESS + 2.0 * clearance,
            RETAINER_TANGENTIAL_WIDTH + 2.0 * clearance,
            RETAINER_HEIGHT + clearance,
            centered=(True, True, False),
        )
        .translate((18.0, 0.0, 0.5))
    )
    m4_axis = (
        cq.Workplane("XY")
        .circle(0.5 * m4_clearance_diameter)
        .extrude(14.0)
        .translate((6.8, 0.0, -1.0))
    )
    block = block.cut(cartridge_pocket.union(external_feed))
    block = block.cut(retainer_slot).cut(m4_axis)
    for index in range(marker_count):
        dot = (
            cq.Workplane("XY")
            .circle(1.1)
            .extrude(0.8)
            .translate((-6.0 + 3.4 * index, 10.5, 12.0))
        )
        block = block.union(dot)
    return block


def build_m4_cartridge_fit_coupon() -> cq.Workplane:
    """Return three receiver walls plus actual cartridges and retainers."""

    shapes: list[cq.Shape] = []
    for index, clearance in enumerate(CARTRIDGE_CLEARANCES, start=1):
        x = -65.0 + (index - 1) * 65.0
        receiver = _receiver_block(clearance, index).translate((x, 0.0, 0.0))
        cartridge = build_m4_nut_cartridge().translate((x, -25.0, 0.0))
        retainer = build_m4_nut_cartridge_retainer().translate(
            (x, 25.0, 0.0)
        )
        shapes.extend((receiver.val(), cartridge.val(), retainer.val()))
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])
