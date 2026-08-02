"""Full-curvature vertical shell coupon with a nested flat function ring."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.tower_module.port_function_ring_phase3r import (
    build_port_function_ring_phase3r,
)
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r import (
    build_self_supporting_port_shell_coupon_phase3r,
)


COUPON_SOLID_COUNT = 2
PRINT_ORIENTATION = "SHELL_VERTICAL_FUNCTION_RING_FLAT_NESTED_INSIDE"
SUPPORT_POLICY = "NO_SUPPORT_TARGET"


def build_self_supporting_port_shell_coupon_set_phase3r() -> cq.Workplane:
    shell = build_self_supporting_port_shell_coupon_phase3r()
    ring = build_port_function_ring_phase3r()
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound([shell.val(), ring.val()])]
    )
