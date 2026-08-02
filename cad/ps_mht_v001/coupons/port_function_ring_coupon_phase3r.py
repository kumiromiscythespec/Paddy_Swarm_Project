"""Preliminary flat structural-ring and replaceable-liner coupon."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    netpot_siawadeky_body_clearance_candidates,
)
from ps_mht_v001.tower_module.netpot_seat_ring_phase3r import (
    build_netpot_seat_ring_phase3r,
)
from ps_mht_v001.tower_module.port_function_ring_phase3r import (
    build_port_function_ring_phase3r,
)


STATUS = "REFERENCE_PRELIMINARY"
BODY_CLEARANCE_CANDIDATES = netpot_siawadeky_body_clearance_candidates
COUPON_SOLID_COUNT = 2
PRINT_ORIENTATION = "BOTH_RINGS_FLAT_ON_SEPARATE_LARGE_FACES"


def build_port_function_ring_coupon_phase3r(
    body_clearance: float,
) -> cq.Workplane:
    function_ring = build_port_function_ring_phase3r().translate(
        (-62.5, 0.0, 0.0)
    )
    seat_ring = build_netpot_seat_ring_phase3r(body_clearance).translate(
        (62.5, 0.0, 0.0)
    )
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound([function_ring.val(), seat_ring.val()])]
    )
