"""Four A1 plates plus a non-sliceable multi-plate orientation reference."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.coupons.annular_nut_ring_coupon_phase3r1 import (
    build_annular_nut_ring_coupon_phase3r1,
)
from ps_mht_v001.coupons.large_index_ring_coupon_phase3r import (
    build_large_index_ring_coupon_phase3r,
)
from ps_mht_v001.coupons.port_function_ring_coupon_phase3r import (
    build_port_function_ring_coupon_phase3r,
)
from ps_mht_v001.parameters import large_ring_selected_clearance
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r1 import (
    build_self_supporting_port_shell_coupon_phase3r1,
)


STATUS = "DO_NOT_SLICE_AS_SINGLE_PLATE"
TARGET_ZONE_GAP_MM = 15.0
ORIENTATION_REFERENCE_SOLID_COUNT = 6


def phase3r1_individual_plates(
) -> tuple[tuple[str, cq.Workplane, int], ...]:
    return (
        (
            "plate_01_large_index_ring_phase3r1",
            build_large_index_ring_coupon_phase3r(
                large_ring_selected_clearance
            ),
            2,
        ),
        (
            "plate_02_annular_nut_ring_phase3r1",
            build_annular_nut_ring_coupon_phase3r1(),
            1,
        ),
        (
            "plate_03_self_supporting_shell_phase3r1",
            build_self_supporting_port_shell_coupon_phase3r1(),
            1,
        ),
        (
            "plate_04_port_function_ring_phase3r1",
            build_port_function_ring_coupon_phase3r(0.50),
            2,
        ),
    )


def phase3r1_plate_positions(
) -> tuple[tuple[str, float, float], ...]:
    positions: list[tuple[str, float, float]] = []
    cursor = 0.0
    for name, model, _ in phase3r1_individual_plates():
        box = model.val().BoundingBox()
        positions.append((name, cursor + 0.5 * box.xlen, box.xlen))
        cursor += box.xlen + TARGET_ZONE_GAP_MM
    return tuple(positions)


def build_multi_plate_orientation_reference_phase3r1() -> cq.Workplane:
    shapes: list[cq.Shape] = []
    cursor = 0.0
    for _, model, _ in phase3r1_individual_plates():
        box = model.val().BoundingBox()
        placed = model.translate((cursor - box.xmin, 0.0, 0.0))
        shapes.extend(placed.solids().vals())
        cursor += box.xlen + TARGET_ZONE_GAP_MM
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound(shapes)]
    )
