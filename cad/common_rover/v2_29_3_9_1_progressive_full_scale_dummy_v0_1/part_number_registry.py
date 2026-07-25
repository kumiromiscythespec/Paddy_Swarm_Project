from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


PART_NUMBER_PATTERN = re.compile(
    r"^PS-PR-A1-(BDY|FRM|MNT|GDE|CVR|FLT|BOX|BAT)-3\d{2}-R00$"
)
PART_NUMBER_FORMAT_SOURCE = "docs/3d_print_pack_README.md"
SERIAL_ALLOCATION = "LANE_LOCAL_300_SERIES"
GLOBAL_PART_NUMBER_RATIFICATION = "HOLD"
REVISION = "R00"


@dataclass(frozen=True)
class PrintedPart:
    key: str
    part_number: str
    filename: str
    title: str
    category: str
    interface_id: str
    orientation_marking: str
    classification_marking: str
    marking_surface: str
    material: str
    print_orientation: str
    support: str
    brim: str
    mirror_of: str | None = None
    optional_dummy: bool = False

    @property
    def required_marking_lines(self) -> tuple[str, ...]:
        return (
            self.part_number,
            self.orientation_marking,
            self.interface_id,
            self.classification_marking,
        )


def _p(
    key: str,
    number: str,
    filename: str,
    title: str,
    category: str,
    interface_id: str,
    orientation: str,
    classification: str = "DUMMY ONLY NO LOAD",
    marking_surface: str = "RECESSED NON-FUNCTIONAL TOP ID PANEL",
    material: str = "PLA FIRST ARTICLE / PETG OPTIONAL",
    print_orientation: str = "MARKED PANEL UP; FLAT DATUM DOWN",
    support: str = "NONE",
    brim: str = "5 MM IF WARP RISK",
    mirror_of: str | None = None,
    optional_dummy: bool = False,
) -> PrintedPart:
    return PrintedPart(
        key,
        number,
        filename,
        title,
        category,
        interface_id,
        orientation,
        classification,
        marking_surface,
        material,
        print_orientation,
        support,
        brim,
        mirror_of,
        optional_dummy,
    )


PARTS: tuple[PrintedPart, ...] = (
    _p(
        "current_cbox_dummy",
        "PS-PR-A1-BOX-301-R00",
        "current_cbox_dummy.stl",
        "CBOX full-scale placement cage",
        "BOX",
        "AI-02",
        "FRONT TOP",
    ),
    _p(
        "current_bbox_dummy",
        "PS-PR-A1-BOX-302-R00",
        "current_bbox_dummy.stl",
        "BBOX full-scale placement cage",
        "BOX",
        "AI-03",
        "REAR TOP",
    ),
    _p(
        "battery_cassette_dummy",
        "PS-PR-A1-BAT-301-R00",
        "battery_cassette_dummy.stl",
        "Battery cassette full-scale placement cage",
        "BAT",
        "BATTERY-CASSETTE",
        "FRONT TOP",
    ),
    _p(
        "cbox_saddle_left",
        "PS-PR-A1-BOX-303-R00",
        "cbox_saddle_left.stl",
        "CBOX positioning saddle left",
        "BOX",
        "AI-02",
        "LEFT FRONT TOP",
    ),
    _p(
        "cbox_saddle_right",
        "PS-PR-A1-BOX-304-R00",
        "cbox_saddle_right.stl",
        "CBOX positioning saddle right",
        "BOX",
        "AI-02",
        "RIGHT FRONT TOP",
        mirror_of="cbox_saddle_left",
    ),
    _p(
        "bbox_support_front",
        "PS-PR-A1-BOX-305-R00",
        "bbox_support_front.stl",
        "Independent BBOX support front",
        "BOX",
        "AI-03",
        "FRONT TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL",
    ),
    _p(
        "bbox_support_rear",
        "PS-PR-A1-BOX-306-R00",
        "bbox_support_rear.stl",
        "Independent BBOX support rear",
        "BOX",
        "AI-03",
        "REAR TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL",
    ),
    _p(
        "core_alignment_key",
        "PS-PR-A1-GDE-301-R00",
        "core_alignment_key.stl",
        "CBOX/BBOX asymmetric alignment key",
        "GDE",
        "AI-04",
        "FRONT TOP INSERT REARWARD",
        "FIT TEST ONLY NO LOAD",
    ),
    _p(
        "anti_separation_lock_carrier",
        "PS-PR-A1-MNT-301-R00",
        "anti_separation_lock_carrier.stl",
        "Visible metal-pin anti-separation carrier",
        "MNT",
        "AI-04",
        "REAR TOP LOCK WINDOW",
        "DUMMY ONLY NO LOAD METAL PIN PRIMARY",
    ),
    _p(
        "lower_float_adapter_left",
        "PS-PR-A1-FLT-301-R00",
        "lower_float_adapter_left.stl",
        "BOTTOM_SLOT lower float adapter left",
        "FLT",
        "AI-05",
        "LEFT FRONT BOTTOM",
        "DUMMY ONLY NO LOAD BOTTOM SLOT",
    ),
    _p(
        "lower_float_adapter_right",
        "PS-PR-A1-FLT-302-R00",
        "lower_float_adapter_right.stl",
        "BOTTOM_SLOT lower float adapter right",
        "FLT",
        "AI-05",
        "RIGHT FRONT BOTTOM",
        "DUMMY ONLY NO LOAD BOTTOM SLOT",
        mirror_of="lower_float_adapter_left",
    ),
    _p(
        "float_slide_receiver_left",
        "PS-PR-A1-FLT-303-R00",
        "float_slide_receiver_left.stl",
        "Legacy float slide receiver left",
        "FLT",
        "AI-06",
        "LEFT FRONT TOP SLIDE REARWARD",
        "FIT TEST ONLY NO LOAD",
    ),
    _p(
        "float_slide_receiver_right",
        "PS-PR-A1-FLT-304-R00",
        "float_slide_receiver_right.stl",
        "Legacy float slide receiver right",
        "FLT",
        "AI-06",
        "RIGHT FRONT TOP SLIDE REARWARD",
        "FIT TEST ONLY NO LOAD",
        mirror_of="float_slide_receiver_left",
    ),
    _p(
        "pin_retainer_cover",
        "PS-PR-A1-CVR-301-R00",
        "pin_retainer_cover.stl",
        "Removable pin retainer cover",
        "CVR",
        "AI-08",
        "TOP FRONT",
        "SECONDARY ONLY DUMMY ONLY NO LOAD",
    ),
    _p(
        "fpb_rail_left_dummy",
        "PS-PR-A1-FRM-301-R00",
        "fpb_rail_left_dummy.stl",
        "FPB left 20x20 envelope rail dummy",
        "FRM",
        "AI-01",
        "LEFT FRONT TOP",
        "PROFILE ENVELOPE ONLY NOT ALUMINUM NO LOAD",
        marking_surface="RECESSED NON-DATUM OUTER ID PANEL",
        brim="8 MM; VERIFY 232 MM BED CLEARANCE",
        optional_dummy=True,
    ),
    _p(
        "fpb_rail_right_dummy",
        "PS-PR-A1-FRM-302-R00",
        "fpb_rail_right_dummy.stl",
        "FPB right 20x20 envelope rail dummy",
        "FRM",
        "AI-01",
        "RIGHT FRONT TOP",
        "PROFILE ENVELOPE ONLY NOT ALUMINUM NO LOAD",
        marking_surface="RECESSED NON-DATUM OUTER ID PANEL",
        brim="8 MM; VERIFY 232 MM BED CLEARANCE",
        mirror_of="fpb_rail_left_dummy",
        optional_dummy=True,
    ),
    _p(
        "fpb_front_crossmember_dummy",
        "PS-PR-A1-FRM-303-R00",
        "fpb_front_crossmember_dummy.stl",
        "FPB front crossmember envelope dummy",
        "FRM",
        "AI-01",
        "FRONT TOP",
        "PROFILE ENVELOPE ONLY NOT ALUMINUM NO LOAD",
        marking_surface="RECESSED NON-DATUM OUTER ID PANEL",
        optional_dummy=True,
    ),
    _p(
        "rear_cradle_dummy_part_1",
        "PS-PR-A1-FRM-304-R00",
        "rear_cradle_dummy_part_1.stl",
        "Rear lower-frame/cradle dummy left section",
        "FRM",
        "AI-03",
        "LEFT REAR TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL",
        optional_dummy=True,
    ),
    _p(
        "rear_cradle_dummy_part_2",
        "PS-PR-A1-FRM-305-R00",
        "rear_cradle_dummy_part_2.stl",
        "Rear lower-frame/cradle dummy right section",
        "FRM",
        "AI-03",
        "RIGHT REAR TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL",
        mirror_of="rear_cradle_dummy_part_1",
        optional_dummy=True,
    ),
)

PART_BY_KEY = {part.key: part for part in PARTS}
PART_BY_NUMBER = {part.part_number: part for part in PARTS}
PART_BY_FILENAME = {part.filename: part for part in PARTS}

# Additive physical-connectivity correction.  PARTS above is intentionally
# frozen so every existing v0.1 part number and STL builder remains unchanged.
CONNECTIVITY_PARTS: tuple[PrintedPart, ...] = (
    _p(
        "front_frame_corner_connector_left",
        "PS-PR-A1-FRM-306-R00",
        "front_frame_corner_connector_left.stl",
        "PROFILE-3 removable front corner connector left",
        "FRM",
        "AI-01",
        "LEFT FRONT TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY",
        brim="5 MM; EXTERNAL SLEEVE OPEN SIDE UP",
    ),
    _p(
        "front_frame_corner_connector_right",
        "PS-PR-A1-FRM-307-R00",
        "front_frame_corner_connector_right.stl",
        "PROFILE-3 removable front corner connector right",
        "FRM",
        "AI-01",
        "RIGHT FRONT TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY",
        brim="5 MM; EXTERNAL SLEEVE OPEN SIDE UP",
        mirror_of="front_frame_corner_connector_left",
    ),
    _p(
        "rear_cradle_center_joiner",
        "PS-PR-A1-FRM-308-R00",
        "rear_cradle_center_joiner.stl",
        "Rear cradle keyed center joiner",
        "FRM",
        "AI-03",
        "CENTER REAR TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY",
    ),
    _p(
        "rear_cradle_left_attachment",
        "PS-PR-A1-FRM-309-R00",
        "rear_cradle_left_attachment.stl",
        "Rear cradle to PROFILE-3 attachment left",
        "FRM",
        "AI-03",
        "LEFT REAR TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY",
    ),
    _p(
        "rear_cradle_right_attachment",
        "PS-PR-A1-FRM-310-R00",
        "rear_cradle_right_attachment.stl",
        "Rear cradle to PROFILE-3 attachment right",
        "FRM",
        "AI-03",
        "RIGHT REAR TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY",
        mirror_of="rear_cradle_left_attachment",
    ),
    _p(
        "front_fpb_to_rear_cradle_visual_locator",
        "PS-PR-A1-FRM-311-R00",
        "front_fpb_to_rear_cradle_visual_locator.stl",
        "FPB-to-rear-cradle removable visual locator",
        "FRM",
        "AI-03",
        "CENTER REAR TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY",
        brim="8 MM; 178 MM CROSS TIE",
    ),
    _p(
        "cbox_saddle_base_clip_left",
        "PS-PR-A1-BOX-307-R00",
        "cbox_saddle_base_clip_left.stl",
        "CBOX saddle-to-PROFILE-3 base clip left",
        "BOX",
        "AI-02",
        "LEFT FRONT TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY",
    ),
    _p(
        "cbox_saddle_base_clip_right",
        "PS-PR-A1-BOX-308-R00",
        "cbox_saddle_base_clip_right.stl",
        "CBOX saddle-to-PROFILE-3 base clip right",
        "BOX",
        "AI-02",
        "RIGHT FRONT TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY",
        mirror_of="cbox_saddle_base_clip_left",
    ),
    _p(
        "bbox_support_anchor_front",
        "PS-PR-A1-BOX-309-R00",
        "bbox_support_anchor_front.stl",
        "BBOX front support removable cradle anchor",
        "BOX",
        "AI-03",
        "FRONT TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY",
    ),
    _p(
        "bbox_support_anchor_rear",
        "PS-PR-A1-BOX-310-R00",
        "bbox_support_anchor_rear.stl",
        "BBOX rear support removable cradle anchor",
        "BOX",
        "AI-03",
        "REAR TOP",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY",
    ),
    _p(
        "profile3_rail_outer_clamp_left",
        "PS-PR-A1-FLT-305-R00",
        "profile3_rail_outer_clamp_left.stl",
        "PROFILE-3 rail outer float clamp left",
        "FLT",
        "AI-05",
        "LEFT FRONT BOTTOM",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY REMOVE FOR REAL ALUMINUM",
    ),
    _p(
        "profile3_rail_outer_clamp_right",
        "PS-PR-A1-FLT-306-R00",
        "profile3_rail_outer_clamp_right.stl",
        "PROFILE-3 rail outer float clamp right",
        "FLT",
        "AI-05",
        "RIGHT FRONT BOTTOM",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY REMOVE FOR REAL ALUMINUM",
        mirror_of="profile3_rail_outer_clamp_left",
    ),
    _p(
        "lower_adapter_visual_locator_left",
        "PS-PR-A1-FLT-307-R00",
        "lower_adapter_visual_locator_left.stl",
        "Lower float adapter visual locator left",
        "FLT",
        "AI-05",
        "LEFT FRONT BOTTOM",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY REMOVE FOR REAL ALUMINUM",
    ),
    _p(
        "lower_adapter_visual_locator_right",
        "PS-PR-A1-FLT-308-R00",
        "lower_adapter_visual_locator_right.stl",
        "Lower float adapter visual locator right",
        "FLT",
        "AI-05",
        "RIGHT FRONT BOTTOM",
        "DUMMY ONLY NO LOAD NOT STRUCTURAL PROFILE-3 ONLY REMOVE FOR REAL ALUMINUM",
        mirror_of="lower_adapter_visual_locator_left",
    ),
)

ALL_PARTS: tuple[PrintedPart, ...] = PARTS + CONNECTIVITY_PARTS
CONNECTIVITY_PART_BY_KEY = {part.key: part for part in CONNECTIVITY_PARTS}
ALL_PART_BY_KEY = {part.key: part for part in ALL_PARTS}
ALL_PART_BY_NUMBER = {part.part_number: part for part in ALL_PARTS}
ALL_PART_BY_FILENAME = {part.filename: part for part in ALL_PARTS}


def validate_registry(parts: Iterable[PrintedPart] = PARTS) -> dict:
    records = tuple(parts)
    numbers = [part.part_number for part in records]
    filenames = [part.filename for part in records]
    missing = [part.key for part in records if not part.part_number]
    malformed = [
        part.part_number
        for part in records
        if not PART_NUMBER_PATTERN.fullmatch(part.part_number)
    ]
    duplicates = sorted(
        {value for value in numbers if numbers.count(value) > 1}
    )
    duplicate_files = sorted(
        {value for value in filenames if filenames.count(value) > 1}
    )
    invalid_surfaces = [
        part.key
        for part in records
        if any(
            token in part.marking_surface.upper()
            for token in (
                "SLIDING SURFACE",
                "FIT SURFACE",
                "SEAL SURFACE",
                "MEASUREMENT SURFACE",
                "CLAMP SURFACE",
                "BUILD-PLATE",
                "HIDDEN ASSEMBLED",
            )
        )
    ]
    missing_no_load = [
        part.key
        for part in records
        if "DUMMY ONLY" in part.classification_marking
        and "NO LOAD" not in part.classification_marking
    ]
    missing_dummy_only = [
        part.key
        for part in records
        if part.part_number
        in {item.part_number for item in CONNECTIVITY_PARTS}
        and "DUMMY ONLY" not in part.classification_marking
    ]
    valid = not (
        missing
        or malformed
        or duplicates
        or duplicate_files
        or invalid_surfaces
        or missing_no_load
        or missing_dummy_only
    )
    if not valid:
        raise ValueError(
            "INVALID_PART_NUMBER_REGISTRY:"
            f"missing={missing};malformed={malformed};"
            f"duplicate_numbers={duplicates};"
            f"duplicate_files={duplicate_files};"
            f"invalid_surfaces={invalid_surfaces};"
            f"missing_no_load={missing_no_load};"
            f"missing_dummy_only={missing_dummy_only}"
        )
    return {
        "status": "PASS",
        "physically_marked_part_count": len(records),
        "unique_part_number_count": len(set(numbers)),
        "global_part_number_ratification": (
            GLOBAL_PART_NUMBER_RATIFICATION
        ),
        "format_source": PART_NUMBER_FORMAT_SOURCE,
        "serial_allocation": SERIAL_ALLOCATION,
    }


def reject_filename_or_metadata_only(
    *,
    physical_marking: bool,
    filename_marking: bool,
    metadata_marking: bool,
) -> None:
    if not physical_marking:
        if filename_marking:
            raise ValueError("PART_NUMBER_ONLY_IN_FILENAME")
        if metadata_marking:
            raise ValueError("PART_NUMBER_ONLY_IN_METADATA")
        raise ValueError("MISSING_PHYSICAL_PART_NUMBER")


validate_registry()
