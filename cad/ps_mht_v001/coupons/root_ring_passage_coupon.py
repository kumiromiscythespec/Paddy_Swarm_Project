"""Root-ring tab-inclusive passage coupon at three per-side clearances."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    port_adapter_inner_diameter,
    root_ring_passage_clearance_candidates,
)
from ps_mht_v001.tower_module.root_sleeve_retaining_ring import (
    build_root_sleeve_retaining_ring,
)


ROOT_RING_CLEARANCES = root_ring_passage_clearance_candidates
COUPON_SOLID_COUNT = 6


def _passage_gauge(marker_count: int) -> cq.Workplane:
    gauge = (
        cq.Workplane("XY")
        .circle(0.5 * port_adapter_inner_diameter + 5.0)
        .circle(0.5 * port_adapter_inner_diameter)
        .extrude(6.0)
    )
    for index in range(marker_count):
        dot = (
            cq.Workplane("XY")
            .circle(1.0)
            .extrude(0.7)
            .translate((-5.0 + 3.0 * index, 36.0, 5.8))
        )
        gauge = gauge.union(dot)
    return gauge


def build_root_ring_passage_coupon() -> cq.Workplane:
    shapes: list[cq.Shape] = []
    for index, clearance in enumerate(ROOT_RING_CLEARANCES, start=1):
        x = -70.0 + (index - 1) * 70.0
        gauge = _passage_gauge(index).translate((x, -32.0, 0.0))
        ring = build_root_sleeve_retaining_ring(clearance).translate(
            (x, 32.0, 0.0)
        )
        shapes.extend((gauge.val(), ring.val()))
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])
