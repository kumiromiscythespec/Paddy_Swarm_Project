"""Physical sequence gauges for the corrected complete axial passage."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    netpot_body_top_outer_diameter,
    root_sleeve_collapsed_diameter,
)
from ps_mht_v001.tower_module.netpot_60_adapter import (
    build_netpot_60_adapter,
)
from ps_mht_v001.tower_module.planting_port import (
    build_planting_port_receiver,
)
from ps_mht_v001.tower_module.planting_port_adapter import (
    build_planting_port_adapter,
)
from ps_mht_v001.tower_module.root_sleeve_retaining_ring import (
    build_root_sleeve_retaining_ring,
)


COUPON_SOLID_COUNT = 6
STATUS = "PHASE3A1_COMPLETE_PASSAGE_SEQUENCE"


def build_complete_port_passage_coupon() -> cq.Workplane:
    receiver = build_planting_port_receiver().translate((-60.0, -55.0, 0.0))
    common_adapter = build_planting_port_adapter().translate(
        (45.0, -55.0, 0.0)
    )
    netpot_adapter = build_netpot_60_adapter().translate(
        (-75.0, 55.0, 0.0)
    )
    root_ring = build_root_sleeve_retaining_ring().translate(
        (-5.0, 55.0, 0.0)
    )
    netpot_axis_gauge = (
        cq.Workplane("XY")
        .circle(0.5 * netpot_body_top_outer_diameter)
        .extrude(18.0)
        .translate((65.0, 55.0, 0.0))
    )
    folded_root_gauge = (
        cq.Workplane("XY")
        .circle(0.5 * root_sleeve_collapsed_diameter)
        .extrude(18.0)
        .translate((95.0, 0.0, 0.0))
    )
    shapes = [
        receiver.val(),
        common_adapter.val(),
        netpot_adapter.val(),
        root_ring.val(),
        netpot_axis_gauge.val(),
        folded_root_gauge.val(),
    ]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])

