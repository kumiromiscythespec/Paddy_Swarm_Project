"""Real common-receiver/adapter section coupon at three clearances."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.tower_module.planting_port import (
    build_planting_port_receiver,
    build_receiver_outer_local,
    build_receiver_void_local,
)
from ps_mht_v001.tower_module.planting_port_adapter import (
    build_planting_port_adapter,
)


ADAPTER_CLEARANCES = (0.20, 0.35, 0.50)
COUPON_SOLID_COUNT = 6


def _section(model: cq.Workplane) -> cq.Workplane:
    cutter = (
        cq.Workplane("XY")
        .box(34.0, 54.0, 24.0, centered=(True, True, False))
        .translate((29.0, 0.0, -2.0))
    )
    return model.intersect(cutter)


def _receiver(clearance: float, marker_count: int) -> cq.Workplane:
    model = build_receiver_outer_local().cut(
        build_receiver_void_local(adapter_clearance=clearance)
    )
    model = _section(model)
    for index in range(marker_count):
        dot = (
            cq.Workplane("XY")
            .circle(1.0)
            .extrude(0.8)
            .translate((39.0, -8.0 + 3.2 * index, 12.0))
        )
        model = model.union(dot)
    return model


def build_port_receiver_adapter_coupon() -> cq.Workplane:
    """Return three separated production-interface section pairs."""

    shapes: list[cq.Shape] = []
    for index, clearance in enumerate(ADAPTER_CLEARANCES, start=1):
        x = -55.0 + (index - 1) * 55.0
        receiver = _receiver(clearance, index).translate((x, -32.0, 0.0))
        adapter = _section(
            build_planting_port_adapter(clearance)
        ).translate((x, 32.0, 0.0))
        shapes.extend((receiver.val(), adapter.val()))
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


PRODUCTION_RECEIVER_REFERENCE = build_planting_port_receiver

