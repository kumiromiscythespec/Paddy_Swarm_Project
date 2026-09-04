"""Authoritative removable 30-degree clocking gauge for Phase 3I-E/3I-F."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib


GAUGE_INNER_DIAMETER_CANDIDATES_MM = (201.5, 202.0, 202.5)
SELECTED_GAUGE_INNER_DIAMETER_MM = None
REFERENCE_EXPORT_GAUGE_INNER_DIAMETER_MM = 202.0
GAUGE_RADIAL_WIDTH_MM = 12.0
GAUGE_THICKNESS_MM = 3.8
GAUGE_ARC_SPAN_DEG = 220.0
GAUGE_OPEN_GAP_DEG = 140.0
GAUGE_MAXIMUM_OUTER_DIAMETER_MM = 228.0
LOWER_DATUM_NOTCH_ANGLE_DEG = 0.0
UPPER_PLUS_30_POINTER_ANGLE_DEG = 30.0
WRONG_ZERO_WARNING_ANGLE_DEG = 0.0
WRONG_60_WARNING_ANGLE_DEG = 60.0


def _validate_candidate(inner_diameter_mm: float) -> None:
    if inner_diameter_mm not in GAUGE_INNER_DIAMETER_CANDIDATES_MM:
        raise ValueError("reference_inner_diameter_mm must explicitly be 201.5, 202.0, or 202.5")


def _rotate(model: cq.Workplane, angle_deg: float) -> cq.Workplane:
    return model.rotate((0, 0, 0), (0, 0, 1), angle_deg)


def _radial_warning_hole(radius_mm: float, angle_deg: float, diameter_mm: float) -> cq.Workplane:
    x = radius_mm * cos(radians(angle_deg))
    y = radius_mm * sin(radians(angle_deg))
    return cq.Workplane("XY").center(x, y).circle(0.5 * diameter_mm).extrude(GAUGE_THICKNESS_MM)


def build_stack_clocking_gauge_30deg_phase3ie(reference_inner_diameter_mm: float) -> cq.Workplane:
    _validate_candidate(reference_inner_diameter_mm)
    inner_r = 0.5 * reference_inner_diameter_mm
    outer_r = inner_r + GAUGE_RADIAL_WIDTH_MM
    gauge = phase3ib._sector(inner_r, outer_r, 0.0, GAUGE_ARC_SPAN_DEG, GAUGE_THICKNESS_MM, 0.0)

    lower_notch = (
        cq.Workplane("XY")
        .polyline([(inner_r - 1.0, -6.0), (inner_r + 7.0, 0.0), (inner_r - 1.0, 6.0)])
        .close()
        .extrude(GAUGE_THICKNESS_MM)
    )
    gauge = gauge.cut(lower_notch)

    pointer = (
        cq.Workplane("XY")
        .polyline([(outer_r + 1.0, -5.5), (outer_r - 7.0, 0.0), (outer_r + 1.0, 5.5)])
        .close()
        .extrude(GAUGE_THICKNESS_MM)
    )
    gauge = gauge.cut(_rotate(pointer, UPPER_PLUS_30_POINTER_ANGLE_DEG))

    # Unequal double windows mark the prohibited zero position; three equal
    # windows mark the collision-proven 60-degree position.
    warning_r = inner_r + 9.5
    for angle, diameter in ((-8.0, 3.2), (8.0, 4.4)):
        gauge = gauge.cut(_radial_warning_hole(warning_r, angle, diameter))
    for angle in (56.0, 60.0, 64.0):
        gauge = gauge.cut(_radial_warning_hole(warning_r, angle, 2.6))

    solids = gauge.clean().solids().vals()
    if len(solids) != 1:
        raise RuntimeError("30-degree clocking gauge must remain one removable solid")
    return cq.Workplane("XY").newObject([solids[0]])


def clocking_gauge_30deg_audit_phase3ie() -> dict[str, object]:
    candidates = []
    for diameter in GAUGE_INNER_DIAMETER_CANDIDATES_MM:
        model = build_stack_clocking_gauge_30deg_phase3ie(diameter)
        box = model.val().BoundingBox()
        candidates.append({
            "inner_diameter_mm": diameter,
            "outer_diameter_mm": diameter + 2.0 * GAUGE_RADIAL_WIDTH_MM,
            "solid_count": len(model.solids().vals()),
            "bbox_mm": [box.xlen, box.ylen, box.zlen],
        })
    return {
        "type": "REMOVABLE_30_DEGREE_STACK_CLOCKING_GAUGE",
        "candidate_inner_diameters_mm": list(GAUGE_INNER_DIAMETER_CANDIDATES_MM),
        "selected_inner_diameter_mm": SELECTED_GAUGE_INNER_DIAMETER_MM,
        "selection_status": "PHYSICAL_CALIBRATION_PENDING",
        "reference_export_candidate_inner_diameter_mm": REFERENCE_EXPORT_GAUGE_INNER_DIAMETER_MM,
        "reference_export_is_production_selection": False,
        "radial_width_mm": GAUGE_RADIAL_WIDTH_MM,
        "thickness_mm": GAUGE_THICKNESS_MM,
        "arc_span_deg": GAUGE_ARC_SPAN_DEG,
        "open_gap_deg": GAUGE_OPEN_GAP_DEG,
        "maximum_allowed_outer_diameter_mm": GAUGE_MAXIMUM_OUTER_DIAMETER_MM,
        "lower_datum_notch_angle_deg": LOWER_DATUM_NOTCH_ANGLE_DEG,
        "upper_plus_30_pointer_angle_deg": UPPER_PLUS_30_POINTER_ANGLE_DEG,
        "pointer_difference_deg": 30.0,
        "wrong_zero_warning_angle_deg": WRONG_ZERO_WARNING_ANGLE_DEG,
        "wrong_60_warning_angle_deg": WRONG_60_WARNING_ANGLE_DEG,
        "flat_print": True,
        "support_required": False,
        "load_bearing": False,
        "watertight_part": False,
        "remove_after_alignment": True,
        "candidates": candidates,
    }
