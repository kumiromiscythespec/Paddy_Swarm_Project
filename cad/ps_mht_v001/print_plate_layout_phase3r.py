"""Multi-plate orientation reference for all Phase 3R printable parts.

The large rings cannot share one 245 mm A1 bed.  This compound places each
already-oriented part in a separate virtual plate zone with at least 15 mm
between zones; it is an orientation/reference STL, not one physical print job.
"""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.tower_module.module_alignment_ring_phase3r import (
    build_module_alignment_ring_phase3r,
)
from ps_mht_v001.tower_module.module_clamping_ring_phase3r import (
    build_module_clamping_ring_phase3r,
)
from ps_mht_v001.tower_module.module_gasket_ring_phase3r import (
    build_module_gasket_ring_phase3r,
)
from ps_mht_v001.tower_module.module_nut_ring_phase3r import (
    build_module_nut_ring_phase3r,
)
from ps_mht_v001.tower_module.port_backing_ring_phase3r import (
    build_port_backing_ring_phase3r,
)
from ps_mht_v001.tower_module.port_function_ring_phase3r import (
    build_port_function_ring_phase3r,
)
from ps_mht_v001.tower_module.root_sleeve_ring_phase3r import (
    build_root_sleeve_ring_phase3r,
)
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r import (
    build_self_supporting_port_shell_coupon_phase3r,
)


STATUS = "REFERENCE_MULTI_PLATE_LAYOUT_NOT_ONE_A1_PRINT_JOB"
TARGET_ZONE_GAP = 15.0
PRINT_PLATE_SOLID_COUNT = 8


def phase3r_plate_parts() -> tuple[tuple[str, cq.Workplane], ...]:
    return (
        ("module_alignment_ring", build_module_alignment_ring_phase3r()),
        ("module_nut_ring", build_module_nut_ring_phase3r()),
        ("module_clamping_ring", build_module_clamping_ring_phase3r()),
        ("module_gasket_ring", build_module_gasket_ring_phase3r()),
        (
            "self_supporting_port_shell_coupon",
            build_self_supporting_port_shell_coupon_phase3r(),
        ),
        ("port_function_ring", build_port_function_ring_phase3r()),
        ("port_backing_ring", build_port_backing_ring_phase3r()),
        ("root_sleeve_ring", build_root_sleeve_ring_phase3r()),
    )


def phase3r_plate_positions() -> tuple[tuple[str, float, float], ...]:
    positions: list[tuple[str, float, float]] = []
    cursor = 0.0
    for name, model in phase3r_plate_parts():
        box = model.val().BoundingBox()
        placed_center_x = cursor + 0.5 * box.xlen
        positions.append((name, placed_center_x, box.xlen))
        cursor += box.xlen + TARGET_ZONE_GAP
    return tuple(positions)


def build_print_plate_layout_phase3r() -> cq.Workplane:
    shapes: list[cq.Shape] = []
    cursor = 0.0
    for name, model in phase3r_plate_parts():
        box = model.val().BoundingBox()
        translation_x = cursor - box.xmin
        placed = model.translate((translation_x, 0.0, 0.0))
        shapes.extend(placed.solids().vals())
        cursor += box.xlen + TARGET_ZONE_GAP
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])
