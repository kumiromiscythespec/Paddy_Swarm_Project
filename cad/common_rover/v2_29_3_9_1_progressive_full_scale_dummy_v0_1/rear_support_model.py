from __future__ import annotations

from authority_adapter import controlled_dimensions, load_context
from part_number_registry import PART_BY_KEY
from stl_exporter import box, engrave_top_markings, fuse_all


def _bbox_support(position: str):
    context = load_context(validate_seed_geometry=False)
    authority = controlled_dimensions(context)
    width = float(authority["bare_frame_width_mm"])
    key = f"bbox_support_{position.lower()}"
    # A visibly separate bridge, not a manufacturing shape.  Feet make the
    # support path independent of the CBOX in the visual assembly.
    base = box(width, 36.0, 6.0)
    left_foot = box(12.0, 24.0, 22.0, 0.0, 0.0, 6.0)
    right_foot = box(12.0, 24.0, 22.0, width - 12.0, 0.0, 6.0)
    seat_left = box(20.0, 6.0, 10.0, 12.0, 0.0, 6.0)
    seat_right = box(20.0, 6.0, 10.0, width - 32.0, 0.0, 6.0)
    if position == "FRONT":
        key_block = box(10.0, 8.0, 8.0, width / 2.0 - 18.0, 0.0, 6.0)
    else:
        key_block = box(10.0, 8.0, 8.0, width / 2.0 + 8.0, 0.0, 6.0)
    shape = fuse_all(
        (base, left_foot, right_foot, seat_left, seat_right, key_block)
    )
    return engrave_top_markings(
        shape,
        PART_BY_KEY[key],
        center_x=width / 2.0,
        first_y=9.0,
        surface_z=6.0,
        line_spacing=7.0,
        sizes=(3.2, 3.0, 3.0, 2.6),
        metadata={
            "position": position,
            "independent_support_path_visible": True,
            "bbox_supported_only_by_cbox": False,
            "rear_bridge_hardpoints": "HOLD",
            "cradle_section": "HOLD",
            "frame_tie": "HOLD",
            "clamp_geometry": "HOLD",
            "stiffness": "HOLD",
            "implement_clearance": "HOLD",
            "structural_claim": False,
        },
    )


def build_bbox_support_front():
    return _bbox_support("FRONT")


def build_bbox_support_rear():
    return _bbox_support("REAR")


def _rear_cradle_half(side: str):
    context = load_context(validate_seed_geometry=False)
    authority = controlled_dimensions(context)
    half_width = float(authority["bare_frame_width_mm"]) / 2.0
    key = (
        "rear_cradle_dummy_part_1"
        if side == "LEFT"
        else "rear_cradle_dummy_part_2"
    )
    base = box(half_width, 72.0, 6.0)
    outer = box(8.0, 72.0, 20.0, 0.0 if side == "LEFT" else half_width - 8.0, 0.0, 6.0)
    rear = box(half_width, 8.0, 16.0, 0.0, 64.0, 6.0)
    joiner = box(
        12.0,
        16.0,
        8.0,
        half_width - 12.0 if side == "LEFT" else 0.0,
        0.0,
        6.0,
    )
    shape = fuse_all((base, outer, rear, joiner))
    return engrave_top_markings(
        shape,
        PART_BY_KEY[key],
        center_x=half_width / 2.0,
        first_y=16.0,
        surface_z=6.0,
        line_spacing=9.0,
        sizes=(2.9, 2.7, 2.7, 2.2),
        metadata={
            "side": side,
            "classification": "VISUAL_REAR_CRADLE_SECTION_ONLY",
            "structural_claim": False,
            "hardpoints": "HOLD",
            "frame_tie": "HOLD",
        },
    )


def build_rear_cradle_dummy_part_1():
    return _rear_cradle_half("LEFT")


def build_rear_cradle_dummy_part_2():
    return _rear_cradle_half("RIGHT")
