"""Ninety-degree Phase 3H-A joint coupons for preliminary calibration."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import horizontal_joint_arc_coupon_angle
from ps_mht_v001.tower_module.horizontal_ring_joint_phase3ha import (
    build_lower_full_ring_phase3ha,
    build_upper_arc_assembly_phase3ha,
    clearance_token_phase3ha,
    horizontal_joint_requirements_phase3ha,
    validate_horizontal_joint_clearance_phase3ha,
)


STATUS = "PRELIMINARY_ONLY_FULL_RING_REQUIRED_FOR_SELECTION"
PART_COUNT = 2
PART_SPACING_MM = 15.0
DIMPLE_DIAMETER_MM = 5.0
TEXT_MARKING_COUNT = 0
SMALL_FEATURE_COUNT = 0


def candidate_index_phase3ha(clearance: float) -> int:
    value = validate_horizontal_joint_clearance_phase3ha(clearance)
    return {0.3: 1, 0.5: 2, 0.7: 3}[value]


def _quadrant_prism() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(110.0, 110.0, 100.0, centered=(False, False, False))
        .translate((0.0, 0.0, -20.0))
    )


def _add_candidate_dimples(
    lower: cq.Workplane,
    clearance: float,
) -> cq.Workplane:
    result = lower
    count = candidate_index_phase3ha(clearance)
    for index in range(count):
        angle = radians(22.5 + 15.0 * index)
        radius = 101.0
        cutter = (
            cq.Workplane("XY")
            .transformed(
                offset=(radius * cos(angle), radius * sin(angle), 15.0)
            )
            .sphere(0.5 * DIMPLE_DIAMETER_MM)
        )
        result = result.cut(cutter)
    return result


def _normalize(model: cq.Workplane) -> cq.Workplane:
    box = model.val().BoundingBox()
    return model.translate((-box.xmin, -box.ymin, -box.zmin))


def horizontal_joint_arc_parts_phase3ha(
    clearance: float,
) -> tuple[cq.Workplane, cq.Workplane]:
    """Return independently printable lower and skirt-up upper arc parts."""

    value = validate_horizontal_joint_clearance_phase3ha(clearance)
    cutter = _quadrant_prism()
    lower = _add_candidate_dimples(
        build_lower_full_ring_phase3ha().intersect(cutter), value
    )
    upper = build_upper_arc_assembly_phase3ha(
        value, horizontal_joint_arc_coupon_angle
    )
    upper = upper.rotate(
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0
    ).translate((0.0, 0.0, 40.0))
    return _normalize(lower), _normalize(upper)


def build_horizontal_joint_arc_coupon_phase3ha(
    clearance: float,
) -> cq.Workplane:
    """Place both real-section arc parts on one A1 printable set."""

    lower, upper = horizontal_joint_arc_parts_phase3ha(clearance)
    lower_box = lower.val().BoundingBox()
    upper_box = upper.val().BoundingBox()
    upper = upper.translate(
        (
            lower_box.xlen + PART_SPACING_MM - upper_box.xmin,
            -upper_box.ymin,
            -upper_box.zmin,
        )
    )
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound([lower.val(), upper.val()])]
    )


def arc_coupon_requirements_phase3ha(clearance: float) -> dict[str, object]:
    value = validate_horizontal_joint_clearance_phase3ha(clearance)
    return {
        **horizontal_joint_requirements_phase3ha(value),
        "coupon_status": STATUS,
        "file_token": clearance_token_phase3ha(value),
        "arc_angle_deg": horizontal_joint_arc_coupon_angle,
        "actual_diameter_curvature": True,
        "part_count": PART_COUNT,
        "dimple_count": candidate_index_phase3ha(value),
        "dimple_diameter_mm": DIMPLE_DIAMETER_MM,
        "text_marking_count": TEXT_MARKING_COUNT,
        "small_feature_count": SMALL_FEATURE_COUNT,
        "selection_authority": False,
    }
