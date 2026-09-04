"""Separate upper outlet and lower ramp coupons for a 170 mm external-frame test."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.tower_module.direct_drop_standpipe_cascade_phase3ie import (
    build_landing_ramp_phase3ie,
    build_single_floor_bore_void_phase3ie,
    build_single_standpipe_wall_phase3ie,
)


COUPON_PLATE_CENTER_SPACING_MM = 100.0
EXTERNAL_TEST_SEPARATION_MM = 170.0


def build_upper_outlet_coupon_phase3ie() -> cq.Workplane:
    plate = cq.Workplane("XY").box(60.0, 60.0, 4.0, centered=(True, True, False))
    standpipe = build_single_standpipe_wall_phase3ie(0.0, 0.0)
    bore = build_single_floor_bore_void_phase3ie(0.0, 0.0)
    return plate.union(standpipe).cut(bore).clean()


def build_lower_landing_ramp_coupon_phase3ie() -> cq.Workplane:
    plate = cq.Workplane("XY").box(70.0, 70.0, 4.0, centered=(True, True, False))
    ramp = build_landing_ramp_phase3ie(0.0, 0.0)
    return plate.union(ramp).clean()


def build_direct_drop_landing_coupon_phase3ie() -> cq.Workplane:
    upper = build_upper_outlet_coupon_phase3ie().translate((-50.0, 0.0, 0.0))
    lower = build_lower_landing_ramp_coupon_phase3ie().translate((50.0, 0.0, 0.0))
    solids = list(upper.solids().vals()) + list(lower.solids().vals())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def build_two_stage_direct_drop_coupon_assembly_reference_phase3ie() -> cq.Workplane:
    lower = build_lower_landing_ramp_coupon_phase3ie()
    upper = build_upper_outlet_coupon_phase3ie().translate((0.0, 0.0, EXTERNAL_TEST_SEPARATION_MM))
    post = (
        cq.Workplane("XY")
        .box(20.0, 20.0, EXTERNAL_TEST_SEPARATION_MM + 34.0, centered=(True, True, False))
        .translate((-55.0, 0.0, 0.0))
    )
    solids = list(lower.solids().vals()) + list(upper.solids().vals()) + list(post.solids().vals())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def direct_drop_landing_coupon_audit_phase3ie() -> dict[str, object]:
    upper = build_upper_outlet_coupon_phase3ie()
    lower = build_lower_landing_ramp_coupon_phase3ie()
    plate = build_direct_drop_landing_coupon_phase3ie()
    box = plate.val().BoundingBox()
    return {
        "architecture": "TWO_SEPARATE_PRINTABLE_PARTS_WITH_EXTERNAL_2020_TEST_FRAME",
        "one_piece_170mm_monolith": False,
        "upper_outlet_solid_count": len(upper.solids().vals()),
        "lower_ramp_solid_count": len(lower.solids().vals()),
        "plate_component_count": len(plate.solids().vals()),
        "external_test_separation_mm": EXTERNAL_TEST_SEPARATION_MM,
        "small_snaps": False,
        "bbox_mm": [box.xlen, box.ylen, box.zlen],
        "a1_envelope_pass": box.xlen <= 245.0 and box.ylen <= 245.0 and box.zlen <= 240.0,
    }
