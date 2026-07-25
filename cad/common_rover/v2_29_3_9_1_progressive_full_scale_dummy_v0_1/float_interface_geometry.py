from __future__ import annotations

from authority_adapter import controlled_dimensions, load_context
from part_number_registry import PART_BY_KEY
from stl_exporter import (
    box,
    cylinder_x,
    engrave_top_markings,
    fuse_all,
)


SLIDE_CLEARANCE_CANDIDATE_MM = 0.40
PIN_BORE_CANDIDATE_MM = 6.30


def _lower_adapter(side: str):
    context = load_context(validate_seed_geometry=False)
    authority = controlled_dimensions(context)
    zone = authority[
        "lower_adapter_left" if side == "LEFT" else "lower_adapter_right"
    ]
    key = f"lower_float_adapter_{side.lower()}"
    base = box(82.0, 58.0, 7.0)
    # Supplier-neutral envelope witness shoulders; no inferred slot tooth.
    shoulder_a = box(8.0, 34.0, 9.0, 5.0, 0.0, 7.0)
    shoulder_b = box(8.0, 34.0, 9.0, 69.0, 0.0, 7.0)
    tongue_x = 0.0 if side == "LEFT" else 66.0
    tongue = box(16.0, 40.0, 5.0, tongue_x, 0.0, 16.0)
    # Side-specific key rejects the opposite receiver.
    key_x = 16.0 if side == "LEFT" else 60.0
    key_bar = box(6.0, 12.0, 5.0, key_x, 0.0, 16.0)
    shape = fuse_all((base, shoulder_a, shoulder_b, tongue, key_bar))
    return engrave_top_markings(
        shape,
        PART_BY_KEY[key],
        center_x=41.0,
        first_y=35.0,
        surface_z=7.0,
        line_spacing=6.0,
        sizes=(2.7, 2.3, 2.4, 2.0),
        metadata={
            "side": side,
            "host_slot": zone["normalized_slot_face"],
            "authority_zone_id": zone["zone_id"],
            "authority_zone_interval_y_mm": zone["zone_interval"],
            "zone_anchor_y_mm": sum(zone["zone_interval"]) / 2.0,
            "direct_rail_holes": False,
            "inferred_supplier_slot_geometry": False,
            "metal_m5_t_nut_candidate": True,
            "reversed_insertion_rejection": (
                f"{side}_OFFSET_TONGUE_KEY"
            ),
        },
    )


def build_lower_float_adapter_left():
    return _lower_adapter("LEFT")


def build_lower_float_adapter_right():
    return _lower_adapter("RIGHT")


def _float_receiver(side: str):
    key = f"float_slide_receiver_{side.lower()}"
    base = box(92.0, 62.0, 7.0)
    left_wall = box(8.0, 42.0, 19.0, 0.0, 0.0, 7.0)
    right_wall = box(8.0, 42.0, 19.0, 84.0, 0.0, 7.0)
    positive_stop = box(92.0, 7.0, 19.0, 0.0, 35.0, 7.0)
    key_x = 8.0 if side == "LEFT" else 76.0
    rejection_key = box(8.0, 14.0, 6.0, key_x, 0.0, 7.0)
    shape = fuse_all(
        (base, left_wall, right_wall, positive_stop, rejection_key)
    )
    bore = cylinder_x(
        PIN_BORE_CANDIDATE_MM,
        94.0,
        -1.0,
        29.0,
        15.0,
    )
    shape = shape.cut(bore)
    # A window from the marked-side rear band exposes pin alignment.
    window = box(30.0, 9.0, 30.0, 31.0, 31.0, 6.5)
    shape = shape.cut(window)
    return engrave_top_markings(
        shape,
        PART_BY_KEY[key],
        center_x=46.0,
        first_y=45.0,
        surface_z=7.0,
        line_spacing=4.0,
        sizes=(2.7, 2.1, 2.4, 2.0),
        metadata={
            "side": side,
            "slide_clearance_candidate_mm": SLIDE_CLEARANCE_CANDIDATE_MM,
            "pin_bore_candidate_mm": PIN_BORE_CANDIDATE_MM,
            "positive_stop": "INTEGRAL_REAR_STOP",
            "pin_alignment_window": True,
            "reversed_insertion_rejection": f"{side}_OFFSET_CHANNEL_KEY",
            "glove_access": "OPEN_TOP_AND_VISIBLE_PIN_ENDS",
            "legacy_float_hardpoint": (
                "LEGACY_GRADE0_SLIDE_PIN_CANDIDATE_EXPLICIT"
            ),
            "structural_claim": False,
        },
    )


def build_float_slide_receiver_left():
    return _float_receiver("LEFT")


def build_float_slide_receiver_right():
    return _float_receiver("RIGHT")


def build_pin_retainer_cover():
    base = box(72.0, 38.0, 4.0)
    left_lip = box(5.0, 24.0, 8.0, 0.0, 0.0, 4.0)
    right_lip = box(5.0, 24.0, 8.0, 67.0, 0.0, 4.0)
    shape = fuse_all((base, left_lip, right_lip))
    # Visible slot prevents the cover from hiding the primary pin state.
    shape = shape.cut(box(26.0, 8.0, 10.0, 23.0, 4.0, 3.5))
    return engrave_top_markings(
        shape,
        PART_BY_KEY["pin_retainer_cover"],
        center_x=36.0,
        first_y=17.0,
        surface_z=4.0,
        line_spacing=5.0,
        sizes=(2.4, 2.1, 2.3, 1.7),
        metadata={
            "classification": "SECONDARY_ONLY",
            "primary_lock": False,
            "primary_metal_pin_remains_visible": True,
            "thumb_latch_primary": False,
        },
    )
