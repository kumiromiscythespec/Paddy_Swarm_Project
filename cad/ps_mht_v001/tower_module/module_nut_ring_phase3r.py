"""Large flat-print M4 nut ring replacing Phase 2 cartridges."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
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


STATUS = "PHASE3R_LARGE_ANNULAR_NUT_PLATE"
PRINT_ORIENTATION = "FLAT_ON_CONTINUOUS_ANNULAR_FACE"
NUT_POCKET_COUNT = 3
RETAINER = "COMMERCIAL_METAL_WASHER_OR_REFERENCE_METAL_PLATE"


def _station(angle_deg: float) -> tuple[float, float]:
    angle = radians(angle_deg)
    return (
        phase3r_m4_pitch_radius * cos(angle),
        phase3r_m4_pitch_radius * sin(angle),
    )


def build_module_nut_ring_phase3r() -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(0.5 * module_nut_ring_outer_diameter)
        .circle(0.5 * module_nut_ring_inner_diameter)
        .extrude(module_nut_ring_thickness)
    )
    for angle_deg, clearance in zip(
        used_fastener_angles,
        module_nut_pocket_clearance_candidates,
    ):
        x, y = _station(angle_deg)
        through = (
            cq.Workplane("XY")
            .center(x, y)
            .circle(0.5 * m4_clearance_diameter)
            .extrude(module_nut_ring_thickness + 2.0)
            .translate((0.0, 0.0, -1.0))
        )
        nut_circumscribed = (
            m4_nut_across_flats / 0.8660254037844386
            + 2.0 * clearance
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
                    module_nut_ring_thickness
                    - m4_nut_thickness
                    - 0.8,
                )
            )
        )
        ring = ring.cut(through).cut(pocket)
    return ring


def build_module_nut_retaining_plate_reference_phase3r() -> cq.Workplane:
    """Purchased metal plate envelope; never exported as printable STL."""

    plate = (
        cq.Workplane("XY")
        .circle(0.5 * module_nut_ring_outer_diameter - 2.0)
        .circle(0.5 * module_nut_ring_inner_diameter + 1.0)
        .extrude(0.8)
    )
    for angle_deg in used_fastener_angles:
        x, y = _station(angle_deg)
        plate = plate.cut(
            cq.Workplane("XY")
            .center(x, y)
            .circle(0.5 * m4_clearance_diameter)
            .extrude(2.0)
            .translate((0.0, 0.0, -0.5))
        )
    return plate
