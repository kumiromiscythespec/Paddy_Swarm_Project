"""Flat PETG carrier ring for the retained 3 mm EPDM cord seal."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    gasket_cord_diameter,
    gasket_groove_depth,
    gasket_groove_width,
    m4_clearance_diameter,
    module_gasket_ring_inner_diameter,
    module_gasket_ring_outer_diameter,
    module_gasket_ring_thickness,
    phase3r_m4_pitch_radius,
    used_fastener_angles,
)


STATUS = "PHASE3R_FLAT_ANNULAR_EPDM_CARRIER"
PRINT_ORIENTATION = "FLAT_GROOVE_FACE_UP"
GASKET_MATERIAL = "PURCHASED_SOLID_EPDM_ROUND_CORD"
GROOVE_CENTER_RADIUS = 97.0


def build_module_gasket_groove_void_phase3r(
    groove_depth: float = gasket_groove_depth,
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(GROOVE_CENTER_RADIUS + 0.5 * gasket_groove_width)
        .circle(GROOVE_CENTER_RADIUS - 0.5 * gasket_groove_width)
        .extrude(groove_depth + 0.1)
        .translate(
            (0.0, 0.0, module_gasket_ring_thickness - groove_depth)
        )
    )


def build_module_gasket_m4_hole_voids_phase3r() -> cq.Workplane:
    holes: list[cq.Shape] = []
    for angle_deg in used_fastener_angles:
        angle = radians(angle_deg)
        x = phase3r_m4_pitch_radius * cos(angle)
        y = phase3r_m4_pitch_radius * sin(angle)
        hole = (
            cq.Workplane("XY")
            .center(x, y)
            .circle(0.5 * m4_clearance_diameter)
            .extrude(module_gasket_ring_thickness + 2.0)
            .translate((0.0, 0.0, -1.0))
        )
        holes.append(hole.val())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(holes)])


def build_module_gasket_ring_phase3r(
    groove_depth: float = gasket_groove_depth,
) -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(0.5 * module_gasket_ring_outer_diameter)
        .circle(0.5 * module_gasket_ring_inner_diameter)
        .extrude(module_gasket_ring_thickness)
    )
    ring = ring.cut(build_module_gasket_groove_void_phase3r(groove_depth))
    return ring.cut(build_module_gasket_m4_hole_voids_phase3r())


def build_epdm_cord_reference_phase3r() -> cq.Workplane:
    """A torus-like purchasing envelope for a solid φ3 mm cord."""

    center_radius = 97.0
    return cq.Workplane("XY").newObject(
        [
            cq.Solid.makeTorus(
                center_radius,
                0.5 * gasket_cord_diameter,
                pnt=cq.Vector(0.0, 0.0, module_gasket_ring_thickness),
            )
        ]
    )
