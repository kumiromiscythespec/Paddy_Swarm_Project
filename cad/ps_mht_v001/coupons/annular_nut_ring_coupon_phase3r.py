"""Full-size annular M4 nut-ring coupon with three pocket clearances."""

from __future__ import annotations

from ps_mht_v001.parameters import module_nut_pocket_clearance_candidates
from ps_mht_v001.tower_module.module_nut_ring_phase3r import (
    build_module_nut_ring_phase3r,
)


NUT_POCKET_CLEARANCES = module_nut_pocket_clearance_candidates
COUPON_SOLID_COUNT = 1
PRINT_ORIENTATION = "FLAT_POCKETS_UP"
RETAINER = "COMMERCIAL_WASHERS_OR_REFERENCE_METAL_PLATE"


def build_annular_nut_ring_coupon_phase3r():
    return build_module_nut_ring_phase3r()
