"""Assembly-to-print coordinate transform for one Phase 3S-A panel."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    RAIL_CHORD_PLANE_X,
    rail_contact_area_phase3sa,
)


STATUS = "PHASE3SA_CHORD_PLANE_DOWN_SUPPORT_FREE_FIRST_CANDIDATE"
COORDINATE_TRANSFORM = {
    "assembly_Y": "print_X",
    "assembly_Z": "print_Y",
    "assembly_radial_outward_X": "print_Z",
    "panel_chord_plane": "print_Z=0",
}


def orient_sector_for_print_phase3sa(
    panel: cq.Workplane,
) -> cq.Workplane:
    """Map (assembly X,Y,Z) to (print Z basis, X basis, Y basis).

    In coordinate-value form this is print (X,Y,Z) = assembly (Y,Z,X),
    followed by the permanent-rail datum offset.
    """

    return panel.rotate(
        (0.0, 0.0, 0.0),
        (1.0, 1.0, 1.0),
        -120.0,
    ).translate((0.0, 0.0, -RAIL_CHORD_PLANE_X))


def print_stability_metrics_phase3sa(
    assembly_panel: cq.Workplane,
) -> dict[str, float | bool]:
    printed = orient_sector_for_print_phase3sa(assembly_panel)
    box = printed.val().BoundingBox()
    center = printed.val().Center()
    support_half_width_x = 0.5 * box.xlen
    support_half_length_y = 0.5 * box.ylen
    center_height = center.z
    minimum_tip_distance = min(
        support_half_width_x - abs(center.x - box.center.x),
        support_half_length_y - abs(center.y - box.center.y),
    )
    return {
        "size_x_mm": box.xlen,
        "size_y_mm": box.ylen,
        "size_z_mm": box.zlen,
        "contact_area_mm2": rail_contact_area_phase3sa(box.ylen),
        "center_projection_x_mm": center.x,
        "center_projection_y_mm": center.y,
        "center_height_mm": center_height,
        "support_polygon_margin_mm": minimum_tip_distance,
        "center_projection_inside_support_polygon":
            minimum_tip_distance >= 0.0,
        "tip_stability_index":
            minimum_tip_distance / max(center_height, 1.0e-9),
    }
