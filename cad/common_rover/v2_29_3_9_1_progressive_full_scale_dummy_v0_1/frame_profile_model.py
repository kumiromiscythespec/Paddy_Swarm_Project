from __future__ import annotations

from authority_adapter import controlled_dimensions, load_context
from part_number_registry import PART_BY_KEY
from stl_exporter import (
    box,
    engrave_rail_markings,
    engrave_top_markings,
)


def _rail(side: str):
    context = load_context(validate_seed_geometry=False)
    authority = controlled_dimensions(context)
    section = authority["profile_section_mm"]
    width = float(section["X_or_Y"])
    height = float(section["Z"])
    length = float(authority["rail_length_mm"])
    key = f"fpb_rail_{side.lower()}_dummy"
    outer = box(width, length, height)
    # Non-structural square-tube dummy.  It does not imitate a supplier slot.
    inner = box(width - 4.0, length - 4.0, height - 4.0, 2.0, 2.0, 2.0)
    shape = outer.cut(inner)
    # Recess a bounded ID band; surrounding edges retain the exact envelope.
    recess = box(width - 4.0, 154.0, 0.80, 2.0, 39.0, height - 0.80)
    shape = shape.cut(recess)
    return engrave_rail_markings(
        shape,
        PART_BY_KEY[key],
        x_positions=(4.0, 8.0, 12.0, 16.0),
        center_y=116.0,
        surface_z=height - 0.80,
        sizes=(2.3, 2.1, 2.1, 1.8),
        metadata={
            "side": side,
            "authority_envelope_mm": {
                "X": width,
                "Y": length,
                "Z": height,
            },
            "profile_option": "PROFILE-3",
            "profile_class": "AUTHORITY_IMPORTED_20X20MM_CLASS",
            "supplier_slot_geometry": None,
            "direct_rail_holes": False,
            "front_corner_reserved_zone_preserved": True,
            "structural_claim": False,
        },
    )


def build_fpb_rail_left_dummy():
    return _rail("LEFT")


def build_fpb_rail_right_dummy():
    return _rail("RIGHT")


def build_fpb_front_crossmember_dummy():
    context = load_context(validate_seed_geometry=False)
    authority = controlled_dimensions(context)
    envelope = authority["front_crossmember_envelope_mm"]
    xlen = float(envelope["X"])
    ylen = float(envelope["Y"])
    zlen = float(envelope["Z"])
    outer = box(xlen, ylen, zlen)
    inner = box(xlen - 4.0, ylen - 4.0, zlen - 4.0, 2.0, 2.0, 2.0)
    shape = outer.cut(inner)
    recess = box(xlen - 6.0, ylen - 4.0, 0.80, 3.0, 2.0, zlen - 0.80)
    shape = shape.cut(recess)
    return engrave_top_markings(
        shape,
        PART_BY_KEY["fpb_front_crossmember_dummy"],
        center_x=xlen / 2.0,
        first_y=4.5,
        surface_z=zlen - 0.80,
        line_spacing=3.5,
        sizes=(2.5, 2.2, 2.3, 1.8),
        metadata={
            "authority_envelope_mm": {
                "X": xlen,
                "Y": ylen,
                "Z": zlen,
            },
            "profile_option": "PROFILE-3",
            "supplier_slot_geometry": None,
            "direct_rail_holes": False,
            "upper_torque_mount": "XMEMBER-TOP_PRESERVED",
            "front_corner_reserved_zone_preserved": True,
            "structural_claim": False,
        },
    )
