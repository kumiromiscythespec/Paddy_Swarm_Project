from __future__ import annotations

from authority_adapter import controlled_dimensions, load_context
from part_number_registry import PART_BY_KEY
from stl_exporter import (
    add_recessed_top_id_panel,
    engrave_top_markings,
    hollow_cage,
)


def build_battery_cassette_dummy():
    context = load_context(validate_seed_geometry=False)
    dims = controlled_dimensions(context)["body_mm"]["BATTERY_CASSETTE"]
    dimensions = (float(dims["X"]), float(dims["Y"]), float(dims["Z"]))
    shape = hollow_cage(dimensions, beam=4.0, open_bottom=True)
    xlen, _, zlen = dimensions
    panel_z = zlen - 6.0
    shape = add_recessed_top_id_panel(
        shape,
        x=7.0,
        y=3.0,
        z=panel_z,
        width=xlen - 14.0,
        depth=34.0,
        thickness=2.0,
    )
    return engrave_top_markings(
        shape,
        PART_BY_KEY["battery_cassette_dummy"],
        center_x=xlen / 2.0,
        first_y=8.0,
        surface_z=panel_z + 2.0,
        line_spacing=7.0,
        sizes=(3.1, 2.8, 2.6, 2.4),
        metadata={
            "body_authority_key": "BATTERY_CASSETTE",
            "authority_envelope_mm": {
                "X": dimensions[0],
                "Y": dimensions[1],
                "Z": dimensions[2],
            },
            "construction": "OPEN_BOTTOM_CONNECTED_EDGE_CAGE",
            "real_battery_use": False,
            "electrical_use": False,
            "structural_restraint_claim": False,
        },
    )
