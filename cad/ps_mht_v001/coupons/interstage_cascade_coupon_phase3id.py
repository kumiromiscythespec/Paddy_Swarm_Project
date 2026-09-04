"""Full-scale two-stage hydraulic-path coupons for Phase 3I-D."""

from __future__ import annotations

from functools import lru_cache

import cadquery as cq

from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib
from ps_mht_v001.tower_module.floating_region_diagnostics_phase3ic import build_phase3ic_diag_03
from ps_mht_v001.tower_module.positive_interstage_cascade_phase3id import (
    build_lower_receiver_channel_discharge_phase3id,
    build_upper_downchute_phase3id,
    build_water_stream_envelope_reference_phase3id,
)


UPPER_COUPON_HEIGHT_MM = 40.0
LOWER_COUPON_HEIGHT_MM = 170.0
FUNCTIONAL_CLIP_X_RANGE_MM = (-125.0, -45.0)
UPPER_COUPON_TANGENTIAL_WIDTH_MM = 70.0
LOWER_COUPON_TANGENTIAL_WIDTH_MM = 90.0
LOWER_COUPON_TEST_BASE_TANGENTIAL_WIDTH_MM = 110.0
LOWER_COUPON_TEST_BASE_THICKNESS_MM = 2.0
COUPON_ALIGNMENT_GUIDE_COUNT = 2
COUPON_ALIGNMENT_GUIDE_CLEARANCE_PER_SIDE_MM = 0.5


def _rear_clip(height_mm: float, tangential_width_mm: float) -> cq.Workplane:
    x_min, x_max = FUNCTIONAL_CLIP_X_RANGE_MM
    return (
        cq.Workplane("XY")
        .box(x_max - x_min, tangential_width_mm, height_mm, centered=(True, True, False))
        .translate((0.5 * (x_min + x_max), 0.0, 0.0))
    )


@lru_cache(maxsize=1)
def build_upper_overflow_drop_chute_coupon_phase3id() -> cq.Workplane:
    authority = build_phase3ic_diag_03().union(
        build_upper_downchute_phase3id(), clean=True, glue=False
    )
    coupon = authority.intersect(
        _rear_clip(UPPER_COUPON_HEIGHT_MM, UPPER_COUPON_TANGENTIAL_WIDTH_MM)
    ).clean()
    solids = list(coupon.solids().vals())
    if len(solids) != 1 or not solids[0].isValid():
        raise RuntimeError(f"upper Phase 3I-D coupon produced {len(solids)} solids")
    return coupon


@lru_cache(maxsize=1)
def build_lower_receiver_full_channel_coupon_phase3id() -> cq.Workplane:
    authority = build_phase3ic_diag_03().union(
        build_lower_receiver_channel_discharge_phase3id(), clean=True, glue=False
    )
    authority = authority.union(phase3ib.build_stacking_guides_phase3ib(), clean=True, glue=False)
    clipped = authority.intersect(
        _rear_clip(LOWER_COUPON_HEIGHT_MM, LOWER_COUPON_TANGENTIAL_WIDTH_MM)
    ).clean()
    # The rectangular rear clip also grazes two remote retention-lug tips whose
    # roots lie outside the hydraulic coupon.  They are intentionally excluded;
    # the largest connected solid contains the complete receiver/channel route.
    functional = phase3ib._largest_solid(clipped)
    # A dry-test-only annular base broadens the footprint while preserving the
    # central dry opening and every functional hydraulic face.
    x_min, x_max = FUNCTIONAL_CLIP_X_RANGE_MM
    base_clip = (
        cq.Workplane("XY")
        .box(
            x_max - x_min,
            LOWER_COUPON_TEST_BASE_TANGENTIAL_WIDTH_MM,
            LOWER_COUPON_TEST_BASE_THICKNESS_MM,
            centered=(True, True, False),
        )
        .translate((0.5 * (x_min + x_max), 0.0, 0.0))
    )
    annular_base = phase3ib._annulus(120.0, 50.0, LOWER_COUPON_TEST_BASE_THICKNESS_MM).intersect(base_clip)
    coupon = functional.union(annular_base, clean=True, glue=False).clean()
    # Two dry locating towers bracket the upper coupon's +/-35 mm clip edges.
    # They fuse into the retained top band, remain outside the open channel and
    # are intentionally absent from the production full-stage authority.
    for sign in (-1.0, 1.0):
        guide = (
            cq.Workplane("XY")
            .box(8.0, 5.0, 10.0, centered=(True, True, False))
            .translate((-92.0, sign * 38.0, 160.0))
        )
        coupon = coupon.union(guide, clean=True, glue=False)
    coupon = coupon.clean()
    solids = list(coupon.solids().vals())
    if len(solids) != 1 or not solids[0].isValid():
        raise RuntimeError(f"lower Phase 3I-D coupon produced {len(solids)} solids")
    return coupon


def build_two_stage_cascade_coupon_assembly_reference_phase3id() -> cq.Workplane:
    lower = build_lower_receiver_full_channel_coupon_phase3id()
    upper = build_upper_overflow_drop_chute_coupon_phase3id().translate((0.0, 0.0, 170.0))
    stream = build_water_stream_envelope_reference_phase3id()
    items: list[cq.Shape] = []
    for model in (lower, upper, stream):
        items.extend(model.solids().vals())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(items)])


def coupon_geometry_audit_phase3id() -> dict[str, object]:
    upper = build_upper_overflow_drop_chute_coupon_phase3id()
    lower = build_lower_receiver_full_channel_coupon_phase3id()
    assembly = build_two_stage_cascade_coupon_assembly_reference_phase3id()
    upper_box = upper.val().BoundingBox()
    lower_box = lower.val().BoundingBox()
    return {
        "upper": {
            "height_mm": UPPER_COUPON_HEIGHT_MM,
            "bbox_mm": [upper_box.xlen, upper_box.ylen, upper_box.zlen],
            "solid_count": len(upper.solids().vals()),
            "valid": upper.val().isValid(),
            "contains_full_scale_overflow_crest_downchute_drip_nose": True,
            "print_status": "BAMBU_REVIEW_FIRST",
        },
        "lower": {
            "height_mm": LOWER_COUPON_HEIGHT_MM,
            "bbox_mm": [lower_box.xlen, lower_box.ylen, lower_box.zlen],
            "solid_count": len(lower.solids().vals()),
            "valid": lower.val().isValid(),
            "contains_full_scale_receiver_vertical_channel_bottom_discharge": True,
            "dry_test_stability_base_present": True,
            "dry_test_stability_base_in_production_full": False,
            "dry_alignment_guide_count": COUPON_ALIGNMENT_GUIDE_COUNT,
            "upper_coupon_side_clearance_per_side_mm": COUPON_ALIGNMENT_GUIDE_CLEARANCE_PER_SIDE_MM,
            "dry_alignment_guides_in_production_full": False,
            "central_opening_preserved": True,
            "print_status": "BAMBU_REVIEW_AFTER_UPPER_COUPON",
        },
        "assembly_reference_solid_count": len(assembly.solids().vals()),
        "physical_print": "HOLD_UNTIL_BOTH_SLICER_REVIEWS_PASS",
    }
