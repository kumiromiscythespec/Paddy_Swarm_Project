"""Large nested wave-ring fit coupon, one file per clearance."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import large_ring_clearance_candidates
from ps_mht_v001.tower_module.module_alignment_ring_phase3r import (
    build_module_alignment_ring_phase3r,
    build_module_alignment_socket_ring_phase3r,
)


LARGE_INDEX_CLEARANCES = large_ring_clearance_candidates
COUPON_SOLID_COUNT = 2
PRINT_ORIENTATION = "BOTH_CONTINUOUS_RINGS_FLAT_AND_CONCENTRIC"
TEST_PROTOCOL = "30_DEGREE_MISASSEMBLY_AND_TEN_INSERTION_CYCLES"


def build_large_index_ring_coupon_phase3r(
    clearance: float,
) -> cq.Workplane:
    male = build_module_alignment_ring_phase3r()
    socket = build_module_alignment_socket_ring_phase3r(clearance)
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound([male.val(), socket.val()])]
    )
