from __future__ import annotations

from authority_adapter import controlled_dimensions, load_context
from part_number_registry import PART_BY_KEY
from stl_exporter import (
    add_recessed_top_id_panel,
    engrave_top_markings,
    hollow_cage,
)


def _build_body_dummy(body_key: str, part_key: str):
    context = load_context(validate_seed_geometry=False)
    dims = controlled_dimensions(context)["body_mm"][body_key]
    dimensions = (float(dims["X"]), float(dims["Y"]), float(dims["Z"]))
    shape = hollow_cage(dimensions, beam=4.0, open_bottom=True)
    xlen, _, zlen = dimensions
    panel_x = 7.0
    panel_y = 3.0
    panel_width = xlen - 14.0
    panel_depth = 34.0
    panel_z = zlen - 6.0
    shape = add_recessed_top_id_panel(
        shape,
        x=panel_x,
        y=panel_y,
        z=panel_z,
        width=panel_width,
        depth=panel_depth,
        thickness=2.0,
    )
    return engrave_top_markings(
        shape,
        PART_BY_KEY[part_key],
        center_x=xlen / 2.0,
        first_y=8.0,
        surface_z=panel_z + 2.0,
        line_spacing=7.0,
        sizes=(3.3, 3.0, 3.0, 2.5),
        metadata={
            "body_authority_key": body_key,
            "authority_envelope_mm": {
                "X": dimensions[0],
                "Y": dimensions[1],
                "Z": dimensions[2],
            },
            "construction": "OPEN_BOTTOM_CONNECTED_EDGE_CAGE",
            "waterproof_claim": False,
            "sealed_vessel_claim": False,
            "electrical_use": False,
            "structural_enclosure_claim": False,
        },
    )


def build_current_cbox_dummy():
    return _build_body_dummy("CBOX", "current_cbox_dummy")


def build_current_bbox_dummy():
    return _build_body_dummy("BBOX", "current_bbox_dummy")
