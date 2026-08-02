"""Flat circular Siawadeky body-passage fit coupons."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    netpot_body_passage_candidates,
    netpot_siawadeky_flange_outer_diameter,
    netpot_siawadeky_max_body_outer_diameter,
    phase3pa_coupon_outer_diameter,
    phase3pa_coupon_thickness,
)


STATUS = "PHASE3PA_PHYSICAL_FIT_CALIBRATION_PENDING"
PRINT_ORIENTATION = "FLAT_ON_FULL_BOTTOM_FACE"
DIMPLE_RADIUS_MM = 1.25
DIMPLE_DEPTH_MM = 1.5
DIMPLE_CENTER_RADIUS_MM = 56.0
SMALL_CLAW_COUNT = 0
SNAP_COUNT = 0
SMALL_GATE_COUNT = 0
M4_HOLE_COUNT = 0


def validate_passage_phase3pa(passage_diameter: float) -> float:
    value = float(passage_diameter)
    if value not in netpot_body_passage_candidates:
        raise ValueError(
            "passage must be an explicit Phase 3P-A candidate "
            f"{netpot_body_passage_candidates}, got {value}"
        )
    return value


def passage_token_phase3pa(passage_diameter: float) -> str:
    value = validate_passage_phase3pa(passage_diameter)
    return f"c{int(round(value * 10)):03d}"


def candidate_index_phase3pa(passage_diameter: float) -> int:
    value = validate_passage_phase3pa(passage_diameter)
    return netpot_body_passage_candidates.index(value) + 1


def build_netpot_seat_fit_coupon_phase3pa(
    passage_diameter: float,
) -> cq.Workplane:
    passage = validate_passage_phase3pa(passage_diameter)
    coupon = (
        cq.Workplane("XY")
        .circle(0.5 * phase3pa_coupon_outer_diameter)
        .circle(0.5 * passage)
        .extrude(phase3pa_coupon_thickness)
    )
    count = candidate_index_phase3pa(passage)
    for index in range(count):
        angle = radians(82.0 + 8.0 * index)
        dimple = (
            cq.Workplane("XY")
            .center(
                DIMPLE_CENTER_RADIUS_MM * cos(angle),
                DIMPLE_CENTER_RADIUS_MM * sin(angle),
            )
            .circle(DIMPLE_RADIUS_MM)
            .extrude(DIMPLE_DEPTH_MM + 0.2)
            .translate(
                (
                    0.0,
                    0.0,
                    phase3pa_coupon_thickness - DIMPLE_DEPTH_MM,
                )
            )
        )
        coupon = coupon.cut(dimple)
    return coupon


def fit_theory_phase3pa(passage_diameter: float) -> dict[str, float]:
    passage = validate_passage_phase3pa(passage_diameter)
    diametral = passage - netpot_siawadeky_max_body_outer_diameter
    return {
        "passage_diameter_mm": passage,
        "diametral_clearance_mm": diametral,
        "radial_clearance_mm": 0.5 * diametral,
        "flange_support_width_mm": 0.5 * (
            netpot_siawadeky_flange_outer_diameter - passage
        ),
        "ring_outside_flange_width_mm": 0.5 * (
            phase3pa_coupon_outer_diameter
            - netpot_siawadeky_flange_outer_diameter
        ),
    }


def coupon_feature_policy_phase3pa() -> dict[str, object]:
    return {
        "outer_diameter_mm": phase3pa_coupon_outer_diameter,
        "thickness_mm": phase3pa_coupon_thickness,
        "top_face": "FLAT",
        "outer_centering_lip": False,
        "small_claw_count": SMALL_CLAW_COUNT,
        "snap_count": SNAP_COUNT,
        "small_gate_count": SMALL_GATE_COUNT,
        "m4_hole_count": M4_HOLE_COUNT,
        "identification": "ONE_TWO_THREE_LARGE_BLIND_DIMPLES",
    }
