from __future__ import annotations

from authority_adapter import controlled_dimensions, load_context
from part_number_registry import CONNECTIVITY_PART_BY_KEY
from stl_exporter import (
    box,
    cylinder_x,
    cylinder_z,
    engrave_top_markings,
    fuse_all,
)

PROFILE_ENVELOPE_CLEARANCE_CANDIDATE_MM = 0.60
EXISTING_SADDLE_BASE_CLEARANCE_CANDIDATE_MM = 0.50
EXISTING_SUPPORT_BASE_CLEARANCE_CANDIDATE_MM = 0.50
REMOVABLE_DUMMY_BOLT_BORE_MM = 5.50
REMOVABLE_DUMMY_PIN_BORE_MM = 6.30


def _marked(
    shape,
    key: str,
    *,
    center_x: float,
    first_y: float,
    surface_z: float,
    line_spacing: float,
    metadata: dict,
    sizes: tuple[float, float, float, float] = (2.6, 2.2, 2.3, 1.65),
):
    common = {
        "classification": (
            "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY"
        ),
        "structural_claim": False,
        "profile3_only": True,
        "supplier_slot_geometry_used": False,
        "t_nut_used": False,
        "direct_rail_holes": False,
        "glue_only": False,
        "tape_only": False,
        "hidden_connection": False,
        "permanent_trap": False,
        "removal_method": (
            "REMOVE VISIBLE DUMMY BOLT OR PIN; SLIDE EXTERNALLY"
        ),
        "glove_release": True,
        "marking_visible_after_assembly": True,
    }
    common.update(metadata)
    return engrave_top_markings(
        shape,
        CONNECTIVITY_PART_BY_KEY[key],
        center_x=center_x,
        first_y=first_y,
        surface_z=surface_z,
        line_spacing=line_spacing,
        sizes=sizes,
        metadata=common,
    )


def _front_corner(side: str):
    key = f"front_frame_corner_connector_{side.lower()}"
    # External L-sleeve: the two 20 mm envelopes rest on open orthogonal
    # channels.  Connector-only ears accept a visible dummy bolt; neither
    # profile receives a hole.
    floor = fuse_all((box(62, 30, 5), box(30, 62, 5)))
    outer_x = box(5, 62, 28, 0, 0, 5)
    outer_y = box(62, 5, 28, 0, 0, 5)
    ear_a = box(10, 10, 14, 48, 20, 5)
    ear_b = box(10, 10, 14, 20, 48, 5)
    key_block = (
        box(8, 12, 8, 32, 5, 5)
        if side == "LEFT"
        else box(12, 8, 8, 5, 32, 5)
    )
    id_wing = box(70, 34, 5, 62, 0, 0)
    shape = fuse_all(
        (floor, outer_x, outer_y, ear_a, ear_b, key_block, id_wing)
    )
    shape = shape.cut(
        cylinder_z(
            REMOVABLE_DUMMY_BOLT_BORE_MM,
            16,
            53,
            25,
            4,
        ),
        cylinder_z(
            REMOVABLE_DUMMY_BOLT_BORE_MM,
            16,
            25,
            53,
            4,
        ),
    )
    return _marked(
        shape,
        key,
        center_x=97,
        first_y=7,
        surface_z=5,
        line_spacing=7,
        sizes=(2.4, 2.1, 2.2, 1.55),
        metadata={
            "side": side,
            "physical_mates": (
                f"fpb_rail_{side.lower()}_dummy",
                "fpb_front_crossmember_dummy",
            ),
            "interface_type": "EXTERNAL_ORTHOGONAL_CORNER_SLEEVE",
            "insertion_direction": "SLIDE PROFILE ENDS INTO OPEN L CHANNELS",
            "retention_method": (
                "VISIBLE REMOVABLE DUMMY BOLTS THROUGH CONNECTOR-ONLY EARS"
            ),
            "positive_stop": "ORTHOGONAL BUTT-FACE FLOOR AND OUTER WALLS",
            "front_datum_preserved": True,
            "left_right_mismatch_rejection": f"{side}_OFFSET_KEY",
            "support_required": False,
        },
    )


def build_front_frame_corner_connector_left():
    return _front_corner("LEFT")


def build_front_frame_corner_connector_right():
    return _front_corner("RIGHT")


def build_rear_cradle_center_joiner():
    base = box(82, 52, 6)
    left_outer = box(6, 30, 20, 8, 0, 6)
    left_inner = box(6, 30, 20, 27, 0, 6)
    right_inner = box(6, 30, 20, 49, 0, 6)
    right_outer = box(6, 30, 20, 68, 0, 6)
    center_stop = box(10, 8, 18, 36, 22, 6)
    id_band = box(82, 22, 6, 0, 30, 0)
    shape = fuse_all(
        (
            base,
            left_outer,
            left_inner,
            right_inner,
            right_outer,
            center_stop,
            id_band,
        )
    )
    shape = shape.cut(
        cylinder_x(REMOVABLE_DUMMY_PIN_BORE_MM, 84, -1, 14, 15)
    )
    return _marked(
        shape,
        "rear_cradle_center_joiner",
        center_x=41,
        first_y=34,
        surface_z=6,
        line_spacing=5,
        metadata={
            "physical_mates": (
                "rear_cradle_dummy_part_1",
                "rear_cradle_dummy_part_2",
            ),
            "interface_type": "DUAL_KEYED_EXTERNAL_TAB_RECEIVER",
            "insertion_direction": "SLIDE CRADLE HALVES TOWARD CENTER",
            "retention_method": "VISIBLE 6MM-CLASS DUMMY PIN",
            "positive_stop": "CENTER STOP SEPARATES LEFT AND RIGHT TABS",
            "support_spacing_unique": True,
            "support_required": False,
        },
    )


def _rear_attachment(side: str):
    key = f"rear_cradle_{side.lower()}_attachment"
    # One open 20.6 mm envelope channel and one external cradle-edge channel.
    base = box(104, 58, 6)
    rail_x = 4 if side == "LEFT" else 79
    cradle_x = 47 if side == "LEFT" else 31
    rail_wall_a = box(6, 36, 28, rail_x, 0, 6)
    rail_wall_b = box(6, 36, 28, rail_x + 26.6, 0, 6)
    cradle_wall_a = box(5, 28, 18, cradle_x, 0, 6)
    cradle_wall_b = box(5, 28, 18, cradle_x + 13.0, 0, 6)
    stop = box(34, 6, 18, min(rail_x, cradle_x), 30, 6)
    shape = fuse_all(
        (
            base,
            rail_wall_a,
            rail_wall_b,
            cradle_wall_a,
            cradle_wall_b,
            stop,
        )
    )
    shape = shape.cut(
        cylinder_x(
            REMOVABLE_DUMMY_PIN_BORE_MM,
            106,
            -1,
            20,
            16,
        )
    )
    return _marked(
        shape,
        key,
        center_x=52,
        first_y=37,
        surface_z=6,
        line_spacing=5,
        metadata={
            "side": side,
            "physical_mates": (
                f"fpb_rail_{side.lower()}_dummy",
                (
                    "rear_cradle_dummy_part_1"
                    if side == "LEFT"
                    else "rear_cradle_dummy_part_2"
                ),
            ),
            "interface_type": (
                "PROFILE_ENVELOPE_TO_CRADLE_EXTERNAL_DUAL_CHANNEL"
            ),
            "insertion_direction": "SLIDE FROM OPEN REAR ENDS",
            "retention_method": "VISIBLE CONNECTOR-ONLY DUMMY PIN",
            "positive_stop": "REAR TRANSVERSE STOP WALL",
            "left_right_mismatch_rejection": f"{side}_OFFSET_CHANNELS",
            "support_required": False,
        },
    )


def build_rear_cradle_left_attachment():
    return _rear_attachment("LEFT")


def build_rear_cradle_right_attachment():
    return _rear_attachment("RIGHT")


def build_front_fpb_to_rear_cradle_visual_locator():
    context = load_context(validate_seed_geometry=False)
    authority = controlled_dimensions(context)
    width = float(authority["bare_frame_width_mm"])
    base = box(width, 38, 6)
    left_stop = box(8, 28, 20, 0, 0, 6)
    right_stop = box(8, 28, 20, width - 8, 0, 6)
    center_key = box(18, 18, 14, width / 2 - 9, 0, 6)
    pin_lugs = fuse_all(
        (
            box(10, 10, 14, 18, 18, 6),
            box(10, 10, 14, width - 28, 18, 6),
        )
    )
    shape = fuse_all((base, left_stop, right_stop, center_key, pin_lugs))
    shape = shape.cut(
        cylinder_z(REMOVABLE_DUMMY_PIN_BORE_MM, 16, 23, 23, 5),
        cylinder_z(
            REMOVABLE_DUMMY_PIN_BORE_MM,
            16,
            width - 23,
            23,
            5,
        ),
    )
    return _marked(
        shape,
        "front_fpb_to_rear_cradle_visual_locator",
        center_x=width / 2,
        first_y=7,
        surface_z=6,
        line_spacing=7,
        sizes=(3.0, 2.7, 2.7, 2.2),
        metadata={
            "physical_mates": (
                "fpb_rail_left_dummy",
                "fpb_rail_right_dummy",
                "rear_cradle_center_joiner",
            ),
            "interface_type": "REMOVABLE_DUMMY_CROSS_TIE_LOCATOR",
            "insertion_direction": "LOWER FROM +Z AT REAR FPB DATUM",
            "retention_method": "TWO VISIBLE 6MM-CLASS DUMMY PINS",
            "positive_stop": "LEFT RIGHT END STOPS AND CENTER KEY",
            "rear_position_fixed": True,
            "support_spacing_unique": True,
            "support_required": False,
        },
    )


def _cbox_clip(side: str):
    key = f"cbox_saddle_base_clip_{side.lower()}"
    base = box(112, 54, 6)
    # Upper channel captures the existing 76 x 5 saddle base edge.  Lower
    # open channel captures only the 20 mm PROFILE-3 outer envelope.
    saddle_x = 8
    upper_a = box(6, 26, 15, saddle_x, 0, 6)
    upper_b = box(
        6,
        26,
        15,
        saddle_x + 76 + 2 * EXISTING_SADDLE_BASE_CLEARANCE_CANDIDATE_MM,
        0,
        6,
    )
    rail_center = 26 if side == "LEFT" else 86
    lower_a = box(6, 30, 28, rail_center - 16.3, 0, 6)
    lower_b = box(6, 30, 28, rail_center + 10.3, 0, 6)
    side_key = box(
        10,
        8,
        10,
        18 if side == "LEFT" else 84,
        24,
        6,
    )
    stop = box(96, 6, 12, 8, 24, 6)
    shape = fuse_all(
        (base, upper_a, upper_b, lower_a, lower_b, side_key, stop)
    )
    shape = shape.cut(
        cylinder_x(REMOVABLE_DUMMY_PIN_BORE_MM, 114, -1, 17, 16)
    )
    return _marked(
        shape,
        key,
        center_x=56,
        first_y=34,
        surface_z=6,
        line_spacing=5,
        metadata={
            "side": side,
            "physical_mates": (
                f"cbox_saddle_{side.lower()}",
                f"fpb_rail_{side.lower()}_dummy",
            ),
            "interface_type": "SADDLE_BASE_EDGE_TO_PROFILE_OUTER_CLIP",
            "insertion_direction": "SLIDE CLIP FROM VISIBLE REAR EDGE",
            "retention_method": "VISIBLE CONNECTOR-ONLY DUMMY PIN",
            "positive_stop": "FULL-WIDTH SADDLE BASE REAR STOP",
            "visible_seated_state": True,
            "left_right_mismatch_rejection": f"{side}_OFFSET_RAIL_CHANNEL",
            "existing_saddle_modified": False,
            "support_required": False,
        },
    )


def build_cbox_saddle_base_clip_left():
    return _cbox_clip("LEFT")


def build_cbox_saddle_base_clip_right():
    return _cbox_clip("RIGHT")


def _bbox_anchor(position: str):
    key = f"bbox_support_anchor_{position.lower()}"
    base = box(96, 58, 6)
    support_a = box(6, 32, 16, 10, 0, 6)
    support_b = box(
        6,
        32,
        16,
        10 + 36 + 2 * EXISTING_SUPPORT_BASE_CLEARANCE_CANDIDATE_MM,
        0,
        6,
    )
    cradle_a = box(6, 30, 20, 67, 0, 6)
    cradle_b = box(6, 30, 20, 83, 0, 6)
    unique_key = (
        box(12, 8, 10, 18, 26, 6)
        if position == "FRONT"
        else box(12, 8, 10, 42, 26, 6)
    )
    stop = box(80, 6, 14, 8, 26, 6)
    shape = fuse_all(
        (base, support_a, support_b, cradle_a, cradle_b, unique_key, stop)
    )
    shape = shape.cut(
        cylinder_x(REMOVABLE_DUMMY_PIN_BORE_MM, 98, -1, 18, 14)
    )
    return _marked(
        shape,
        key,
        center_x=48,
        first_y=36,
        surface_z=6,
        line_spacing=5,
        metadata={
            "position": position,
            "physical_mates": (
                f"bbox_support_{position.lower()}",
                (
                    "rear_cradle_dummy_part_1"
                    if position == "FRONT"
                    else "rear_cradle_dummy_part_2"
                ),
            ),
            "interface_type": "SUPPORT_BASE_TO_CRADLE_EXTERNAL_ANCHOR",
            "insertion_direction": "SLIDE FROM OUTBOARD VISIBLE EDGE",
            "retention_method": "VISIBLE CONNECTOR-ONLY DUMMY PIN",
            "positive_stop": f"UNIQUE_{position}_OFFSET_STOP",
            "front_rear_position_unique": True,
            "lateral_slide_rejected": True,
            "support_remains_when_bbox_removed": True,
            "carry_retention_dummy_only": True,
            "support_required": False,
        },
    )


def build_bbox_support_anchor_front():
    return _bbox_anchor("FRONT")


def build_bbox_support_anchor_rear():
    return _bbox_anchor("REAR")


def _profile3_float_clamp(side: str):
    key = f"profile3_rail_outer_clamp_{side.lower()}"
    base = box(86, 58, 6)
    channel_x = 8 if side == "LEFT" else 51.4
    wall_a = box(6, 36, 30, channel_x, 0, 6)
    wall_b = box(6, 36, 30, channel_x + 26.6, 0, 6)
    ear_a = box(12, 12, 16, channel_x - 2, 28, 6)
    ear_b = box(12, 12, 16, channel_x + 22.6, 28, 6)
    locator_tongue = box(
        18,
        34,
        8,
        52 if side == "LEFT" else 16,
        0,
        6,
    )
    side_key = box(
        7,
        12,
        8,
        70 if side == "LEFT" else 9,
        0,
        14,
    )
    shape = fuse_all(
        (base, wall_a, wall_b, ear_a, ear_b, locator_tongue, side_key)
    )
    shape = shape.cut(
        cylinder_x(REMOVABLE_DUMMY_BOLT_BORE_MM, 88, -1, 33, 16)
    )
    return _marked(
        shape,
        key,
        center_x=43,
        first_y=39,
        surface_z=6,
        line_spacing=4,
        sizes=(2.4, 2.0, 2.2, 1.45),
        metadata={
            "side": side,
            "physical_mates": (
                f"fpb_rail_{side.lower()}_dummy",
                f"lower_adapter_visual_locator_{side.lower()}",
            ),
            "interface_type": "SLIDE_ON_PROFILE_OUTER_ENVELOPE_CLAMP",
            "insertion_direction": "SLIDE FROM OPEN RAIL END BEFORE FRAME CLOSE",
            "retention_method": "VISIBLE DUMMY BOLT THROUGH CLAMP EARS",
            "positive_stop": "Y ZONE WITNESS STOP AT -110 MM ASSEMBLY DATUM",
            "authority_zone_y_mm": [-125, -95],
            "assembly_anchor_y_mm": -110,
            "left_right_mismatch_rejection": f"{side}_OFFSET_TONGUE",
            "remove_for_real_aluminum": True,
            "support_required": False,
        },
    )


def build_profile3_rail_outer_clamp_left():
    return _profile3_float_clamp("LEFT")


def build_profile3_rail_outer_clamp_right():
    return _profile3_float_clamp("RIGHT")


def _lower_adapter_locator(side: str):
    key = f"lower_adapter_visual_locator_{side.lower()}"
    base = box(112, 50, 6)
    # Channel wraps one visible 82 mm edge of the existing lower adapter.
    edge_a = box(6, 30, 18, 8, 0, 6)
    edge_b = box(6, 30, 18, 90.8, 0, 6)
    clamp_receiver_a = box(6, 26, 16, 40, 0, 6)
    clamp_receiver_b = box(6, 26, 16, 64, 0, 6)
    side_key = box(
        8,
        10,
        10,
        18 if side == "LEFT" else 84,
        22,
        6,
    )
    stop = box(96, 6, 14, 8, 24, 6)
    shape = fuse_all(
        (
            base,
            edge_a,
            edge_b,
            clamp_receiver_a,
            clamp_receiver_b,
            side_key,
            stop,
        )
    )
    shape = shape.cut(
        cylinder_x(REMOVABLE_DUMMY_PIN_BORE_MM, 114, -1, 16, 14)
    )
    return _marked(
        shape,
        key,
        center_x=56,
        first_y=32,
        surface_z=6,
        line_spacing=4,
        sizes=(2.4, 2.0, 2.2, 1.45),
        metadata={
            "side": side,
            "physical_mates": (
                f"profile3_rail_outer_clamp_{side.lower()}",
                f"lower_float_adapter_{side.lower()}",
            ),
            "interface_type": (
                "PROFILE3_CLAMP_TONGUE_TO_EXISTING_ADAPTER_EDGE_LOCATOR"
            ),
            "insertion_direction": "SLIDE FROM OUTBOARD VISIBLE EDGE",
            "retention_method": "VISIBLE CONNECTOR-ONLY DUMMY PIN",
            "positive_stop": "FULL-WIDTH EXISTING ADAPTER EDGE STOP",
            "authority_zone_y_mm": [-125, -95],
            "assembly_anchor_y_mm": -110,
            "left_right_mismatch_rejection": f"{side}_OFFSET_EDGE_KEY",
            "existing_lower_adapter_modified": False,
            "remove_for_real_aluminum": True,
            "support_required": False,
        },
    )


def build_lower_adapter_visual_locator_left():
    return _lower_adapter_locator("LEFT")


def build_lower_adapter_visual_locator_right():
    return _lower_adapter_locator("RIGHT")


CONNECTIVITY_BUILDERS = (
    build_front_frame_corner_connector_left,
    build_front_frame_corner_connector_right,
    build_rear_cradle_center_joiner,
    build_rear_cradle_left_attachment,
    build_rear_cradle_right_attachment,
    build_front_fpb_to_rear_cradle_visual_locator,
    build_cbox_saddle_base_clip_left,
    build_cbox_saddle_base_clip_right,
    build_bbox_support_anchor_front,
    build_bbox_support_anchor_rear,
    build_profile3_rail_outer_clamp_left,
    build_profile3_rail_outer_clamp_right,
    build_lower_adapter_visual_locator_left,
    build_lower_adapter_visual_locator_right,
)
