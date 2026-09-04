"""Permanent, support-free 0-degree clocking datums for Phase 3I-E."""

from __future__ import annotations

import cadquery as cq


TOP_DATUM_ANGLE_DEG = 0.0
TOP_DATUM_TANGENTIAL_WIDTH_MM = 16.0
TOP_DATUM_RADIAL_PROJECTION_MM = 1.5
TOP_DATUM_HEIGHT_MM = 1.2
BOTTOM_DATUM_ANGLE_DEG = 0.0
BOTTOM_DATUM_TANGENTIAL_WIDTH_MM = 12.0
BOTTOM_DATUM_RADIAL_PROJECTION_MM = 1.0
BOTTOM_DATUM_Z_RANGE_MM = (8.0, 18.0)


def build_top_clocking_datum_phase3ie() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .polyline([(99.0, -8.0), (101.5, 0.0), (99.0, 8.0)])
        .close()
        .extrude(TOP_DATUM_HEIGHT_MM)
        .translate((0.0, 0.0, 162.8))
    )


def build_bottom_clocking_datum_phase3ie() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .polyline([(99.0, -6.0), (101.0, 0.0), (99.0, 6.0)])
        .close()
        .extrude(BOTTOM_DATUM_Z_RANGE_MM[1] - BOTTOM_DATUM_Z_RANGE_MM[0])
        .translate((0.0, 0.0, BOTTOM_DATUM_Z_RANGE_MM[0]))
    )


def clocking_datum_audit_phase3ie() -> dict[str, object]:
    return {
        "top": {
            "angle_deg": TOP_DATUM_ANGLE_DEG,
            "shape": "LARGE_TRIANGULAR_RELIEF",
            "location": "DRY_TOP_STIFFENING_BAND",
            "tangential_width_mm": TOP_DATUM_TANGENTIAL_WIDTH_MM,
            "radial_projection_mm": TOP_DATUM_RADIAL_PROJECTION_MM,
            "height_mm": TOP_DATUM_HEIGHT_MM,
            "support_required": False,
        },
        "bottom": {
            "angle_deg": BOTTOM_DATUM_ANGLE_DEG,
            "shape": "LARGE_VERTICAL_TRIANGULAR_RELIEF",
            "location": "EXTERNAL_DRY_VISUAL_ZONE",
            "z_range_mm": list(BOTTOM_DATUM_Z_RANGE_MM),
            "tangential_width_mm": BOTTOM_DATUM_TANGENTIAL_WIDTH_MM,
            "radial_projection_mm": BOTTOM_DATUM_RADIAL_PROJECTION_MM,
            "wet_wall_penetration": False,
            "support_required": False,
        },
    }
