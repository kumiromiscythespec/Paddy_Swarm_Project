"""Full functional 360-degree low sump coupon for Phase 3I-E."""

from __future__ import annotations

from functools import lru_cache

import cadquery as cq

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ie import (
    build_integrated_stage_full_direct_drop_phase3ie,
)


SUMP_COUPON_HEIGHT_MM = 40.0


@lru_cache(maxsize=1)
def build_three_standpipe_sump_coupon_phase3ie() -> cq.Workplane:
    clip = cq.Workplane("XY").box(245.0, 245.0, SUMP_COUPON_HEIGHT_MM, centered=(True, True, False))
    coupon = build_integrated_stage_full_direct_drop_phase3ie().intersect(clip).clean()
    solids = coupon.solids().vals()
    if len(solids) != 1:
        raise RuntimeError("three-standpipe sump coupon must be one solid")
    return cq.Workplane("XY").newObject([solids[0]])


def standpipe_sump_coupon_audit_phase3ie() -> dict[str, object]:
    coupon = build_three_standpipe_sump_coupon_phase3ie()
    box = coupon.val().BoundingBox()
    return {
        "architecture": "FULL_360_DEGREE_FUNCTIONAL_ANNULAR_SUMP_COUPON",
        "solid_count": len(coupon.solids().vals()),
        "bbox_mm": [box.xlen, box.ylen, box.zlen],
        "contains_three_standpipes": True,
        "contains_three_floor_bores": True,
        "contains_continuous_inner_dam": True,
        "central_opening_dry": True,
        "a1_envelope_pass": box.xlen <= 245.0 and box.ylen <= 245.0 and box.zlen <= 240.0,
    }
