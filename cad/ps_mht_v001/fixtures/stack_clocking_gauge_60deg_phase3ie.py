"""Aborted partial 60-degree gauge retained only for collision history.

This file predates the authorized 30-degree revision.  It is deliberately not
an authoritative Phase 3I-E source and must not enter a commit manifest or
delivery archive.
"""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib


PARTIAL_SOURCE_STATUS = "ABORTED_PARTIAL_SOURCE"
AUTHORITATIVE = False
NOT_FOR_COMMIT = True
NOT_FOR_ZIP = True


GAUGE_INNER_DIAMETER_CANDIDATES_MM = (201.5, 202.0, 202.5)
SELECTED_GAUGE_INNER_DIAMETER_MM = None
REFERENCE_EXPORT_GAUGE_INNER_DIAMETER_MM = 202.0
GAUGE_RADIAL_WIDTH_MM = 12.0
GAUGE_THICKNESS_MM = 3.8
GAUGE_ARC_SPAN_DEG = 220.0
GAUGE_OPEN_GAP_DEG = 360.0 - GAUGE_ARC_SPAN_DEG
GAUGE_MAXIMUM_OUTER_DIAMETER_MM = 228.0
LOWER_DATUM_NOTCH_ANGLE_DEG = 0.0
UPPER_PLUS_60_POINTER_ANGLE_DEG = 60.0
WRONG_ZERO_WARNING_ANGLE_DEG = 0.0


def _validate_candidate(inner_diameter_mm: float) -> None:
    if inner_diameter_mm not in GAUGE_INNER_DIAMETER_CANDIDATES_MM:
        raise ValueError("reference_inner_diameter_mm must explicitly be 201.5, 202.0, or 202.5")


def _rotate(model: cq.Workplane, angle_deg: float) -> cq.Workplane:
    return model.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)


def build_stack_clocking_gauge_60deg_phase3ie(reference_inner_diameter_mm: float) -> cq.Workplane:
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
    gauge = gauge.cut(_rotate(pointer, UPPER_PLUS_60_POINTER_ANGLE_DEG))

    # Two unequal warning windows near zero make the 0-degree location visibly
    # different from the single V pointer at +60 degrees.
    for angle, diameter in ((-8.0, 3.2), (8.0, 4.4)):
        radius = inner_r + 9.5
        x, y = radius * cos(radians(angle)), radius * sin(radians(angle))
        warning = cq.Workplane("XY").center(x, y).circle(0.5 * diameter).extrude(GAUGE_THICKNESS_MM)
        gauge = gauge.cut(warning)
    solids = gauge.clean().solids().vals()
    if len(solids) != 1:
        raise RuntimeError("clocking gauge must remain one removable solid")
    return cq.Workplane("XY").newObject([solids[0]])


def clocking_gauge_audit_phase3ie() -> dict[str, object]:
    candidates = []
    for diameter in GAUGE_INNER_DIAMETER_CANDIDATES_MM:
        model = build_stack_clocking_gauge_60deg_phase3ie(diameter)
        box = model.val().BoundingBox()
        candidates.append({
            "inner_diameter_mm": diameter,
            "outer_diameter_mm": diameter + 2.0 * GAUGE_RADIAL_WIDTH_MM,
            "solid_count": len(model.solids().vals()),
            "bbox_mm": [box.xlen, box.ylen, box.zlen],
        })
    return {
        "type": "REMOVABLE_60_DEGREE_STACK_CLOCKING_GAUGE",
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
        "upper_plus_60_pointer_angle_deg": UPPER_PLUS_60_POINTER_ANGLE_DEG,
        "pointer_difference_deg": UPPER_PLUS_60_POINTER_ANGLE_DEG - LOWER_DATUM_NOTCH_ANGLE_DEG,
        "wrong_zero_warning_angle_deg": WRONG_ZERO_WARNING_ANGLE_DEG,
        "flat_print": True,
        "support_required": False,
        "small_snaps": False,
        "load_bearing": False,
        "watertight_part": False,
        "remove_after_alignment": True,
        "candidates": candidates,
    }
