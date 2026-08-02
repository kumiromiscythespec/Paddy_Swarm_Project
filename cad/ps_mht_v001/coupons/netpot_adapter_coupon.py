"""Three real net-pot adapter interfaces for fit calibration."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.tower_module.netpot_60_adapter import (
    build_netpot_60_adapter,
)


NETPOT_CLEARANCES = (0.20, 0.35, 0.50)
COUPON_SOLID_COUNT = 3


def _marked_adapter(clearance: float, marker_count: int) -> cq.Workplane:
    model = build_netpot_60_adapter(clearance)
    for index in range(marker_count):
        dot = (
            cq.Workplane("XY")
            .circle(1.2)
            .extrude(0.8)
            .translate((-8.0 + index * 3.2, 35.0, 12.2))
        )
        model = model.union(dot)
    return model


def build_netpot_adapter_coupon() -> cq.Workplane:
    """Return three actual-size adapters; raised dots identify clearance."""

    placements = ((-55.0, -42.0), (55.0, -42.0), (0.0, 48.0))
    shapes = [
        _marked_adapter(clearance, index)
        .translate((x, y, 0.0))
        .val()
        for index, (clearance, (x, y)) in enumerate(
            zip(NETPOT_CLEARANCES, placements),
            start=1,
        )
    ]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])
