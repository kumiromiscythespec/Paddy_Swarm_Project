from __future__ import annotations

from part_number_registry import PART_BY_KEY
from stl_exporter import (
    box,
    cylinder_x,
    engrave_top_markings,
    fuse_all,
)


# These are explicitly lane-local print/fit candidates, not authority values.
SADDLE_WALL_CLEARANCE_CANDIDATE_MM = 0.40
METAL_PIN_BORE_CANDIDATE_MM = 6.30


def _cbox_saddle(side: str):
    key = f"cbox_saddle_{side.lower()}"
    base = box(76.0, 76.0, 5.0)
    # The locator walls contact only the open-cage dummy corner.  The long
    # rear band is a non-fit identification panel.
    if side == "LEFT":
        locator = fuse_all(
            (
                box(5.0, 38.0, 18.0, 0.0, 0.0, 5.0),
                box(34.0, 5.0, 18.0, 0.0, 0.0, 5.0),
                box(8.0, 6.0, 10.0, 28.0, 5.0, 5.0),
            )
        )
        seated_indicator = box(3.0, 14.0, 13.0, 34.0, 12.0, 5.0)
        asymmetry = "LEFT_KEY_AT_INBOARD_REAR"
    else:
        locator = fuse_all(
            (
                box(5.0, 38.0, 18.0, 71.0, 0.0, 5.0),
                box(34.0, 5.0, 18.0, 42.0, 0.0, 5.0),
                box(8.0, 6.0, 10.0, 40.0, 5.0, 5.0),
            )
        )
        seated_indicator = box(3.0, 14.0, 13.0, 39.0, 12.0, 5.0)
        asymmetry = "RIGHT_KEY_AT_INBOARD_REAR"
    shape = fuse_all((base, locator, seated_indicator))
    return engrave_top_markings(
        shape,
        PART_BY_KEY[key],
        center_x=38.0,
        first_y=48.0,
        surface_z=5.0,
        line_spacing=7.0,
        sizes=(2.8, 2.6, 2.6, 2.2),
        metadata={
            "side": side,
            "fit_clearance_candidate_mm": (
                SADDLE_WALL_CLEARANCE_CANDIDATE_MM
            ),
            "positive_stop": "INTEGRAL_FRONT_WALL",
            "asymmetric_key": asymmetry,
            "visible_seated_indicator": True,
            "primary_fastener": "METAL_CLAMP_CANDIDATE_HOLD",
            "printed_latch_primary": False,
            "host_cradle_geometry": "HOLD",
        },
    )


def build_cbox_saddle_left():
    return _cbox_saddle("LEFT")


def build_cbox_saddle_right():
    return _cbox_saddle("RIGHT")


def build_core_alignment_key():
    base = box(82.0, 34.0, 6.0)
    tongue = box(58.0, 16.0, 8.0, 12.0, 0.0, 6.0)
    front_stop = box(70.0, 5.0, 13.0, 6.0, 0.0, 6.0)
    asymmetric_key = box(11.0, 8.0, 5.0, 59.0, 16.0, 6.0)
    shape = fuse_all((base, tongue, front_stop, asymmetric_key))
    return engrave_top_markings(
        shape,
        PART_BY_KEY["core_alignment_key"],
        center_x=41.0,
        first_y=9.0,
        surface_z=6.0,
        line_spacing=6.0,
        sizes=(2.7, 2.3, 2.5, 2.1),
        metadata={
            "assembly_boundary": "CBOX_BBOX_Y_EQUALS_ZERO",
            "insertion_direction": "FRONT_TO_REAR_POSITIVE_Y",
            "reversed_insertion_rejection": "OFFSET_RIGHT_KEY",
            "vertical_bbox_support": False,
            "primary_lock": "SEPARATE_VISIBLE_METAL_PIN_CANDIDATE",
        },
    )


def build_anti_separation_lock_carrier():
    base = box(84.0, 42.0, 6.0)
    left = box(8.0, 28.0, 20.0, 0.0, 0.0, 6.0)
    right = box(8.0, 28.0, 20.0, 76.0, 0.0, 6.0)
    rear = box(84.0, 8.0, 20.0, 0.0, 20.0, 6.0)
    shape = fuse_all((base, left, right, rear))
    pin = cylinder_x(
        METAL_PIN_BORE_CANDIDATE_MM,
        86.0,
        -1.0,
        13.0,
        15.0,
    )
    shape = shape.cut(pin)
    # Through-window makes the primary metal pin state visible from above.
    window = box(34.0, 13.0, 30.0, 25.0, 7.0, 5.5)
    shape = shape.cut(window)
    return engrave_top_markings(
        shape,
        PART_BY_KEY["anti_separation_lock_carrier"],
        center_x=42.0,
        first_y=31.0,
        surface_z=6.0,
        line_spacing=3.0,
        sizes=(2.6, 2.2, 2.4, 1.8),
        metadata={
            "pin_bore_candidate_mm": METAL_PIN_BORE_CANDIDATE_MM,
            "visible_lock_window": True,
            "primary_lock": "REMOVABLE_METAL_PIN_CANDIDATE",
            "printed_latch_primary": False,
            "connector_structural_load": False,
            "vertical_bbox_support": False,
        },
    )
