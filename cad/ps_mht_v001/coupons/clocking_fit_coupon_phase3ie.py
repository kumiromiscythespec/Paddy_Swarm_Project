"""Three separated short-arc fit candidates for the Phase 3I-E gauge."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.fixtures.stack_clocking_gauge_30deg_phase3ie import (
    GAUGE_INNER_DIAMETER_CANDIDATES_MM,
    GAUGE_RADIAL_WIDTH_MM,
    GAUGE_THICKNESS_MM,
)
from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib


FIT_COUPON_ARC_SPAN_DEG = 30.0
FIT_COUPON_CENTER_SPACING_MM = 71.0


def _candidate_arc(inner_diameter_mm: float, identification_holes: int) -> cq.Workplane:
    inner_r = 0.5 * inner_diameter_mm
    outer_r = inner_r + GAUGE_RADIAL_WIDTH_MM
    arc = phase3ib._sector(inner_r, outer_r, 0.0, FIT_COUPON_ARC_SPAN_DEG, GAUGE_THICKNESS_MM, 0.0)
    for index in range(identification_holes):
        y = (index - 0.5 * (identification_holes - 1)) * 4.0
        hole = (
            cq.Workplane("XY")
            .center(inner_r + 8.5, y)
            .circle(1.1)
            .extrude(GAUGE_THICKNESS_MM)
        )
        arc = arc.cut(hole)
    return arc.clean().translate((-(inner_r + 0.5 * GAUGE_RADIAL_WIDTH_MM), 0.0, 0.0))


def build_clocking_fit_coupon_phase3ie() -> cq.Workplane:
    solids: list[cq.Shape] = []
    for index, diameter in enumerate(GAUGE_INNER_DIAMETER_CANDIDATES_MM):
        candidate = _candidate_arc(diameter, index + 1).translate((0.0, (index - 1) * FIT_COUPON_CENTER_SPACING_MM, 0.0))
        solids.extend(candidate.solids().vals())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def clocking_fit_coupon_audit_phase3ie() -> dict[str, object]:
    model = build_clocking_fit_coupon_phase3ie()
    box = model.val().BoundingBox()
    return {
        "candidate_inner_diameters_mm": list(GAUGE_INNER_DIAMETER_CANDIDATES_MM),
        "arc_span_deg": FIT_COUPON_ARC_SPAN_DEG,
        "thickness_mm": GAUGE_THICKNESS_MM,
        "identification_hole_counts": [1, 2, 3],
        "solid_count": len(model.solids().vals()),
        "bbox_mm": [box.xlen, box.ylen, box.zlen],
        "a1_envelope_pass": box.xlen <= 245.0 and box.ylen <= 245.0 and box.zlen <= 240.0,
        "print_status": "READY_FIRST_LOW_COST_FIT_TEST",
    }
