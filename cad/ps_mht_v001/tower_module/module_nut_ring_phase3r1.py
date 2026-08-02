"""Phase 3R.1 production M4 nut ring with one explicit uniform clearance."""

from __future__ import annotations

from math import cos, isfinite, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    CALIBRATION_PENDING,
    m4_clearance_diameter,
    m4_nut_across_flats,
    m4_nut_thickness,
    module_nut_pocket_clearance_candidates,
    module_nut_ring_inner_diameter,
    module_nut_ring_outer_diameter,
    module_nut_ring_thickness,
    phase3r_m4_pitch_radius,
    used_fastener_angles,
)


STATUS = "PHASE3R1_PRODUCTION_CANDIDATE_CALIBRATION_PENDING"
CALIBRATION_STATUS = CALIBRATION_PENDING
SELECTED_NUT_POCKET_CLEARANCE: None = None
NUT_POCKET_COUNT = 3
PRINT_ORIENTATION = "FLAT_POCKETS_UP"
RETAINER = "COMMERCIAL_METAL_WASHER_OR_REFERENCE_METAL_PLATE"


def _station(angle_deg: float) -> tuple[float, float]:
    angle = radians(angle_deg)
    return (
        phase3r_m4_pitch_radius * cos(angle),
        phase3r_m4_pitch_radius * sin(angle),
    )


def _validate_clearance(clearance: float) -> float:
    value = float(clearance)
    if not isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(
            "nut_pocket_clearance must be an explicit finite value in 0..1 mm"
        )
    return value


def production_pocket_clearances_phase3r1(
    nut_pocket_clearance: float,
) -> tuple[float, float, float]:
    value = _validate_clearance(nut_pocket_clearance)
    return (value, value, value)


def _build_ring_with_clearances_phase3r1(
    clearances: tuple[float, float, float],
) -> cq.Workplane:
    if len(clearances) != len(used_fastener_angles):
        raise ValueError("exactly three M4 pocket clearances are required")
    ring = (
        cq.Workplane("XY")
        .circle(0.5 * module_nut_ring_outer_diameter)
        .circle(0.5 * module_nut_ring_inner_diameter)
        .extrude(module_nut_ring_thickness)
    )
    for angle_deg, clearance in zip(used_fastener_angles, clearances):
        value = _validate_clearance(clearance)
        x, y = _station(angle_deg)
        through = (
            cq.Workplane("XY")
            .center(x, y)
            .circle(0.5 * m4_clearance_diameter)
            .extrude(module_nut_ring_thickness + 2.0)
            .translate((0.0, 0.0, -1.0))
        )
        nut_circumscribed = (
            m4_nut_across_flats / 0.8660254037844386 + 2.0 * value
        )
        pocket = (
            cq.Workplane("XY")
            .center(x, y)
            .polygon(6, nut_circumscribed)
            .extrude(m4_nut_thickness + 0.8)
            .translate(
                (
                    0.0,
                    0.0,
                    module_nut_ring_thickness - m4_nut_thickness - 0.8,
                )
            )
        )
        ring = ring.cut(through).cut(pocket)
    return ring


def build_module_nut_ring_phase3r1(
    nut_pocket_clearance: float,
) -> cq.Workplane:
    """Build a production candidate; no clearance is selected by default."""

    return _build_ring_with_clearances_phase3r1(
        production_pocket_clearances_phase3r1(nut_pocket_clearance)
    )


def calibration_clearance_candidates_phase3r1(
) -> tuple[float, float, float]:
    return tuple(module_nut_pocket_clearance_candidates)
