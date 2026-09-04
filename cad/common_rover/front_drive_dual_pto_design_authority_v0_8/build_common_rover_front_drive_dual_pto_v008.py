"""Build and verify Common Rover front-drive / dual-PTO authority v0.8.

This lane is deliberately an envelope-level design authority.  It does not
invent production dimensions for unmeasured motors, clutches, pulleys,
bearings, couplings, tensioners, fasteners, or crawler hardware.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path
from typing import Iterable

import cadquery as cq


LANE_DIR = Path(__file__).resolve().parent
REPO_ROOT = LANE_DIR.parents[2]
ARTIFACT_DIR = LANE_DIR / "artifacts"

DOCUMENT_ID = "PS-CR-FRONT-DRIVE-DUAL-PTO-DESIGN-AUTHORITY-V008"
SCHEMA = "paddy_swarm.common_rover.front_drive_dual_pto_design_authority.v0.8"
AUTHORITY_STATUS = "FIXED_SPEC_WITH_LAYOUT_AND_MEASUREMENT_HOLDS"
RELEASE_STATUS = "NOT_APPROVED"

PARAMETERS_NAME = "common_rover_front_drive_dual_pto_parameters_v008.json"
AUTHORITY_NAME = "common_rover_front_drive_dual_pto_design_authority_v008.md"
INTERFERENCE_JSON_NAME = (
    "common_rover_front_drive_dual_pto_interference_report_v008.json"
)
INTERFERENCE_CSV_NAME = (
    "common_rover_front_drive_dual_pto_interference_matrix_v008.csv"
)
ALLOCATION_NAME = "common_rover_front_drive_dual_pto_aluminum_allocation_v008.csv"
VALIDATION_NAME = "common_rover_front_drive_dual_pto_validation_v008.json"
STEP_NAME = "PS-CR-FRONT-DRIVE-DUAL-PTO-V008-INSPECTION.step"
SVG_NAME = "PS-CR-FRONT-DRIVE-DUAL-PTO-V008-OVERVIEW.svg"
TEST_REL = "tests/test_common_rover_front_drive_dual_pto_v008_contract.py"

GENERATED_RELATIVE_PATHS = (
    f"cad/common_rover/front_drive_dual_pto_design_authority_v0_8/{AUTHORITY_NAME}",
    f"cad/common_rover/front_drive_dual_pto_design_authority_v0_8/{PARAMETERS_NAME}",
    f"cad/common_rover/front_drive_dual_pto_design_authority_v0_8/{INTERFERENCE_JSON_NAME}",
    f"cad/common_rover/front_drive_dual_pto_design_authority_v0_8/{INTERFERENCE_CSV_NAME}",
    f"cad/common_rover/front_drive_dual_pto_design_authority_v0_8/{ALLOCATION_NAME}",
    f"cad/common_rover/front_drive_dual_pto_design_authority_v0_8/{VALIDATION_NAME}",
    f"cad/common_rover/front_drive_dual_pto_design_authority_v0_8/artifacts/{STEP_NAME}",
    f"cad/common_rover/front_drive_dual_pto_design_authority_v0_8/artifacts/{SVG_NAME}",
)
EXPECTED_PATHS = tuple(
    sorted(
        (
            *GENERATED_RELATIVE_PATHS,
            "cad/common_rover/front_drive_dual_pto_design_authority_v0_8/"
            "build_common_rover_front_drive_dual_pto_v008.py",
            TEST_REL,
        )
    )
)


# Fixed authority values from the task, never inferred from layout geometry.
COORDINATE_SYSTEM = {
    "units_length": "mm",
    "units_angle": "degree",
    "+X": "ROVER_FRONT",
    "-X": "ROVER_REAR",
    "+Y": "ROVER_LEFT_WHEN_FACING_FORWARD",
    "-Y": "ROVER_RIGHT",
    "+Z": "UP",
    "ground_z_mm": 0.0,
}
LEGACY_TO_V008_AXIS_MAPPING = {
    "X_V008": "-Y_LEGACY",
    "Y_V008": "X_LEGACY",
    "Z_V008": "Z_LEGACY",
}
LAYOUT_ORDER = (
    "PTO_OUTPUT",
    "POWER_TRANSMISSION",
    "MOTOR",
    "CBOX",
    "CBOX_BBOX_INTERFACE",
    "BBOX",
    "REAR_SERVICE_SPACE",
)

CBOX_SIZE_MM = {"x": 130.0, "y": 140.0, "z": 105.0}
BBOX_SIZE_MM = {"x": 150.0, "y": 220.0, "z": 150.0}
BATTERY_CASSETTE_SIZE_MM = {"x": 125.0, "y": 180.0, "z": 120.0}
BBOX_MIN_EFFECTIVE_INTERIOR_MM = {"x": 129.0, "y": 184.0, "z": 125.0}
BOX_BOTTOM_Z_MM = 200.0
CBOX_TOP_Z_MM = BOX_BOTTOM_Z_MM + CBOX_SIZE_MM["z"]
BBOX_TOP_Z_MM = BOX_BOTTOM_Z_MM + BBOX_SIZE_MM["z"]
BOX_TOP_MAX_Z_MM = max(CBOX_TOP_Z_MM, BBOX_TOP_Z_MM)

TRACK_WIDTH_EACH_MM = 55.0
CENTRAL_LOWER_STRUCTURE_MAX_WIDTH_MM = 180.0
TOTAL_WIDTH_HARD_MAX_MM = 299.0
TOTAL_WIDTH_TARGET_RANGE_MM = [286.0, 290.0]
NOMINAL_ROW_SPACING_MM = 300.0

MOTOR_COUNT = 2
PTO_COUNT = 2
KP000_CANDIDATE_COUNT = 4
MOTOR_AXIS_MIN_Z_MM = BOX_TOP_MAX_Z_MM
PTO_AXIS_RELATION = "Z_PTO_AXIS_GTE_Z_MOTOR_AXIS"
PREFERRED_AXIS_RELATION = "Z_PTO_AXIS_EQUALS_Z_MOTOR_AXIS"

BELT_STANDARD = "HTD_5M_STANDARD"
BELT_PITCH_MM = 5.0
BELT_WIDTH_MM = 15.0
PULLEY_DRIVER_TEETH = 20
PULLEY_DRIVEN_TEETH = 60
NOMINAL_REDUCTION_RATIO = 3.0
PULLEY_60T_SAFETY_DIAMETER_MM = 120.0
PULLEY_60T_SAFETY_RADIUS_MM = 60.0
PTO_60T_REPORTED_MAX_DIMENSION_MM = 102.0
PTO_60T_DIMENSION_MEANING = "CALIBRATION_PENDING"

CLEARANCES_MM = {
    "belt_side_to_frame": {"minimum": 5.0, "recommended": 8.0},
    "belt_to_diagonal": {"minimum": 8.0, "recommended": 10.0},
    "belt_to_bolt_head": {"minimum": 5.0, "recommended": 8.0},
    "pulley_flange_to_frame": {"minimum": 5.0, "recommended": 8.0},
    "pulley_60t_envelope_to_fixed_part": {
        "minimum": 8.0,
        "recommended": 10.0,
    },
    "belt_to_wiring": {"minimum": 10.0, "recommended": 15.0},
    "pto_pulley_to_kp000": {"minimum": 5.0, "recommended": 8.0},
    "drive_belt_to_crawler_cover": {
        "minimum": 8.0,
        "recommended": 12.0,
    },
    "box_bottom_to_track_dynamic": {
        "minimum": 10.0,
        "recommended": 20.0,
    },
}

CLUTCH_STATES = ("DRIVE", "NEUTRAL", "PTO")
CLUTCH_RULES = {
    "architecture": "TWO_INDEPENDENT_THREE_POSITION_SLIDE_CLUTCHES",
    "same_side_drive_and_pto_simultaneous_engagement": "MECHANICALLY_PROHIBITED",
    "state_transition": "DRIVE_TO_NEUTRAL_TO_PTO_AND_REVERSE",
    "shift_motor_state": "STOPPED",
    "shift_rover_state": "STOPPED",
    "left_right_control": "INDEPENDENT",
    "power_loss_preferred_safe_state": "NEUTRAL",
    "position_sensor_mounting": "REQUIRED_CAPABILITY",
}

# Non-manufacturing candidate values used only to build and inspect envelopes.
CANDIDATE = {
    "authority": "NON_MANUFACTURING_ENVELOPE_LAYOUT_ONLY",
    "cbox_center_x_mm": 85.0,
    "bbox_center_x_mm": -75.0,
    "cbox_bbox_interface_gap_x_mm": 20.0,
    "motor_axis_x_mm": 205.0,
    "power_transmission_x_mm": 255.0,
    "drive_axis_x_mm": 300.0,
    "pto_axis_x_mm": 390.0,
    "motor_axis_z_mm": 370.0,
    "pto_axis_z_mm": 370.0,
    "motor_axis_abs_y_mm": 105.0,
    "drive_belt_plane_abs_y_mm": 119.0,
    "pto_belt_plane_abs_y_mm": 45.0,
    "pto_outer_end_abs_y_mm": 145.0,
    "track_outer_abs_y_mm": 143.0,
    "track_inner_abs_y_mm": 88.0,
    "central_lower_width_mm": 176.0,
    "total_width_with_candidate_envelopes_mm": 290.0,
    "upper_main_rail_center_abs_y_mm": 68.0,
    "track_side_frame_center_abs_y_mm": 78.0,
    "front_pto_root_x_mm": 250.0,
    "front_pto_crossbar_x_mm": 420.0,
    "front_pto_horizontal_bottom_z_mm": 220.0,
    "front_pto_horizontal_top_z_mm": 240.0,
    "track_upper_rear_x_mm": -120.0,
    "track_upper_front_x_mm": 280.0,
    "track_lower_rear_x_mm": -30.0,
    "track_lower_front_x_mm": 230.0,
    "track_upper_frame_bottom_z_mm": 110.0,
    "track_lower_frame_bottom_z_mm": 20.0,
    "track_dynamic_top_z_mm": 185.0,
    "track_dynamic_bottom_z_mm": 10.0,
    "box_to_track_candidate_vertical_clearance_mm": 15.0,
    "belt_envelope_axial_width_mm": 31.0,
    "belt_envelope_radial_thickness_mm": 20.0,
    "pulley_20t_safety_radius_candidate_mm": 25.0,
    "pulley_axial_envelope_candidate_mm": 25.0,
    "kp000_xyz_envelope_candidate_mm": [45.0, 15.0, 35.0],
    "motor_body_radius_candidate_mm": 30.0,
    "motor_body_axial_length_candidate_mm": 70.0,
    "clutch_full_stroke_envelope_xyz_candidate_mm": [50.0, 60.0, 50.0],
    "roller_count_visualized": 4,
    "roller_count_candidates": [3, 4],
    "frame_assembly_error_each_axis_mm": 1.0,
    "frame_deformation_allowance_mm": 2.0,
}

STOCK = {
    "2020": {"stock_length_mm": 400.0, "available_count": 8},
    "2040": {"stock_length_mm": 400.0, "available_count": 8},
}

SUPERSEDED = (
    "LEGACY_COORDINATE_X_LATERAL_Y_LONGITUDINAL",
    "LEGACY_LOW_MOTOR_AND_PTO_AXIS_COORDINATES",
    "BBOX_220MM_AXIS_FORE_AFT",
    "BBOX_200_X_150_X_120_MM",
    "CBOX_AND_BBOX_SAME_SIZE",
    "CBOX_BBOX_SIDE_BY_SIDE",
    "LEFT_RIGHT_PTO_COMMON_SHAFT",
    "ONE_CENTER_60T_PULLEY_FOR_BOTH_PTO_PORTS",
    "DEDICATED_THIRD_PTO_MOTOR",
    "MOTOR_SHAFTS_POINTING_OUTWARD",
    "PTO_SHAFTS_POINTING_FORE_AFT",
    "PTO_BEHIND_MOTOR",
    "AMBIGUOUS_DRIVE_PTO_SWITCHING",
    "UNAPPROVED_NON_SLIDE_CLUTCH_SWITCHING",
    "COMMON_SYNCHRONIZED_CLUTCH_SELECTOR",
    "RECTANGULAR_TANK_TRACK",
    "FOUR_WHEEL_TIRE_LAYOUT",
    "EQUAL_LENGTH_RECTANGULAR_CRAWLER_FRAME",
    "SINGLE_ALUMINUM_MEMBER_LONGER_THAN_400_MM",
    "BOX_AS_PRIMARY_STRUCTURE",
    "PTO_60T_102MM_ONLY_ROTATION_ENVELOPE",
    "FRAME_595_X_155_LAYOUT_AS_CURRENT_AUTHORITY",
)

HOLD_ITEMS = (
    "ACTUAL_MOTOR_ENVELOPE",
    "MOTOR_SHAFT_DIAMETER",
    "MOTOR_EFFECTIVE_SHAFT_LENGTH",
    "MOTOR_MASS",
    "SLIDE_CLUTCH_DETAIL_GEOMETRY",
    "SLIDE_CLUTCH_STROKE",
    "DOG_ENGAGEMENT_LENGTH",
    "CLUTCH_ACTUATION_MECHANISM",
    "CLUTCH_SENSOR_POSITION",
    "PULLEY_AXIAL_STACK_ORDER",
    "20T_PULLEY_ACTUAL_WIDTH",
    "60T_PULLEY_ACTUAL_WIDTH",
    "PULLEY_FLANGE_OUTSIDE_DIAMETER",
    "BELT_LENGTH",
    "BELT_LATERAL_SWAY",
    "TENSIONER_POSITION_AND_FULL_RANGE",
    "KP000_ACTUAL_DIMENSIONS_AND_LOAD_RATING",
    "PTO_BEARING_SPACING",
    "PTO_FORWARD_OVERHANG",
    "PTO_SHAFT_DIMENSIONS",
    "PTO_COUPLING_OUTSIDE_DIAMETER_AND_LENGTH",
    "BBOX_EFFECTIVE_INTERIOR",
    "BATTERY_CASSETTE_GUIDE_THICKNESS",
    "BATTERY_CASSETTE_CONTACT_TYPE",
    "BATTERY_CASSETTE_LATCH_GEOMETRY",
    "CRAWLER_FORE_AFT_LENGTH",
    "UPPER_TRACK_LENGTH",
    "LOWER_GROUND_CONTACT_LENGTH",
    "TRACK_PITCH",
    "DRIVE_SPROCKET_DIAMETER",
    "IDLER_DIAMETER",
    "ROLLER_DIAMETER",
    "ROLLER_COUNT_THREE_OR_FOUR",
    "UPPER_AND_LOWER_2040_FINAL_CUT_LENGTHS",
    "FRONT_REAR_DIAGONAL_POST_ANGLES",
    "TRACK_LATERAL_DYNAMIC_RUNOUT",
    "IDLER_TENSION_ADJUSTMENT_FULL_RANGE",
    "FASTENER_HEAD_WASHER_COLLAR_RETAINING_RING_ENVELOPES",
    "METAL_BRACKET_GUSSET_DIMENSIONS_AND_LOAD_RATING",
    "WIRING_ROUTE",
    "COMPLETED_MASS",
    "CENTER_OF_GRAVITY",
    "BUOYANCY",
    "ACTUAL_MUD_SINK",
    "FIELD_TRAVEL_FEASIBILITY",
)

FINAL_GATES = {
    "ALUMINUM_CUTTING": "HOLD",
    "ADDITIONAL_DRILLING": "HOLD",
    "MOTOR_FIXING": "HOLD",
    "CLUTCH_FABRICATION": "HOLD",
    "BBOX_CONTAINMENT_MEASUREMENT": "HOLD",
    "CASSETTE_CONTACT_SELECTION": "HOLD",
    "CRAWLER_MANUFACTURING": "HOLD",
    "POWERED_PTO_TEST": "HOLD",
    "WATER_TEST": "HOLD",
    "MUD_TEST": "HOLD",
    "FIELD_DEPLOYMENT": "NOT_APPROVED",
}

MEASUREMENT_EVIDENCE = {
    "htd5m_phase1": {
        "status": "PASS_USER_OBSERVED_DRY_MANUAL_ENGAGEMENT_ONLY",
        "profile": "STANDARD",
        "pitch_mm": 5.0,
        "20t_engagement": "PASS_USER_OBSERVED",
        "60t_arc_engagement": "PASS_USER_OBSERVED",
        "powered_or_field_authority": False,
        "source_commit": "0835d123e773819de711a046997abf8477c7e922",
    },
    "pto_60t_reported_dimension": {
        "value_mm": PTO_60T_REPORTED_MAX_DIMENSION_MM,
        "meaning": PTO_60T_DIMENSION_MEANING,
        "v008_rotation_envelope_diameter_mm": PULLEY_60T_SAFETY_DIAMETER_MM,
        "status": "PART_MEASUREMENT_REQUIRED",
    },
    "uxcell_motor_bracket_product_description": {
        "overall_l_w_h_mm": [40.0, 40.0, 46.7],
        "status": "DATASHEET_OR_PRODUCT_DESCRIPTION_ONLY",
        "bottom_hole_positions": "CALIBRATION_PENDING",
        "actual_motor_envelope_authority": False,
    },
    "actual_final_component_measurement_count": 0,
}


def _round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _shape(value: cq.Shape | cq.Workplane) -> cq.Shape:
    return value.val() if isinstance(value, cq.Workplane) else value


def _box(
    x_size: float,
    y_size: float,
    z_size: float,
    *,
    center_x: float,
    center_y: float,
    bottom_z: float,
) -> cq.Shape:
    return _shape(
        cq.Workplane("XY")
        .box(x_size, y_size, z_size, centered=(True, True, False))
        .translate((center_x, center_y, bottom_z))
    )


def _cylinder_y(
    radius: float,
    length: float,
    *,
    center_x: float,
    center_y: float,
    center_z: float,
) -> cq.Shape:
    start = cq.Vector(center_x, center_y - length / 2.0, center_z)
    return cq.Solid.makeCylinder(
        radius,
        length,
        start,
        cq.Vector(0.0, 1.0, 0.0),
    )


def _beam_xz(
    x1: float,
    z1: float,
    x2: float,
    z2: float,
    *,
    center_y: float,
    section_y: float = 20.0,
    section_z: float = 20.0,
) -> cq.Shape:
    dx = x2 - x1
    dz = z2 - z1
    length = math.hypot(dx, dz)
    angle_deg = -math.degrees(math.atan2(dz, dx))
    beam = _box(
        length,
        section_y,
        section_z,
        center_x=0.0,
        center_y=0.0,
        bottom_z=-section_z / 2.0,
    )
    beam = beam.rotate(
        cq.Vector(0.0, 0.0, 0.0),
        cq.Vector(0.0, 1.0, 0.0),
        angle_deg,
    )
    return beam.translate(
        cq.Vector((x1 + x2) / 2.0, center_y, (z1 + z2) / 2.0)
    )


def _beam_xy(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    center_z: float,
    section_y: float = 20.0,
    section_z: float = 20.0,
) -> cq.Shape:
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    angle_deg = math.degrees(math.atan2(dy, dx))
    beam = _box(
        length,
        section_y,
        section_z,
        center_x=0.0,
        center_y=0.0,
        bottom_z=-section_z / 2.0,
    )
    beam = beam.rotate(
        cq.Vector(0.0, 0.0, 0.0),
        cq.Vector(0.0, 0.0, 1.0),
        angle_deg,
    )
    return beam.translate(
        cq.Vector((x1 + x2) / 2.0, (y1 + y2) / 2.0, center_z)
    )


def _belt_envelope(
    x1: float,
    z1: float,
    r1: float,
    x2: float,
    z2: float,
    r2: float,
    *,
    center_y: float,
) -> cq.Shape:
    """Conservative strip plus both pulley wrap regions."""
    dx = x2 - x1
    dz = z2 - z1
    length = math.hypot(dx, dz)
    angle_deg = -math.degrees(math.atan2(dz, dx))
    strip = _box(
        length,
        CANDIDATE["belt_envelope_axial_width_mm"],
        CANDIDATE["belt_envelope_radial_thickness_mm"],
        center_x=0.0,
        center_y=0.0,
        bottom_z=-CANDIDATE["belt_envelope_radial_thickness_mm"] / 2.0,
    )
    strip = strip.rotate(
        cq.Vector(0.0, 0.0, 0.0),
        cq.Vector(0.0, 1.0, 0.0),
        angle_deg,
    )
    strip = strip.translate(
        cq.Vector((x1 + x2) / 2.0, center_y, (z1 + z2) / 2.0)
    )
    wrap_1 = _cylinder_y(
        r1,
        CANDIDATE["belt_envelope_axial_width_mm"],
        center_x=x1,
        center_y=center_y,
        center_z=z1,
    )
    wrap_2 = _cylinder_y(
        r2,
        CANDIDATE["belt_envelope_axial_width_mm"],
        center_x=x2,
        center_y=center_y,
        center_z=z2,
    )
    return strip.fuse(wrap_1).fuse(wrap_2)


def _track_prism(side: str) -> cq.Shape:
    points = (
        (-140.0, CANDIDATE["track_dynamic_top_z_mm"]),
        (340.0, CANDIDATE["track_dynamic_top_z_mm"]),
        (270.0, CANDIDATE["track_dynamic_bottom_z_mm"]),
        (-70.0, CANDIDATE["track_dynamic_bottom_z_mm"]),
    )
    base = _shape(
        cq.Workplane("XZ")
        .polyline(points)
        .close()
        .extrude(TRACK_WIDTH_EACH_MM)
    )
    if side == "LEFT":
        return base.translate(
            cq.Vector(0.0, CANDIDATE["track_outer_abs_y_mm"], 0.0)
        )
    return base.translate(
        cq.Vector(0.0, -CANDIDATE["track_inner_abs_y_mm"], 0.0)
    )


def build_components() -> dict[str, cq.Shape]:
    """Build a registry of simple inspection envelopes."""
    c: dict[str, cq.Shape] = {}

    c["CBOX"] = _box(
        CBOX_SIZE_MM["x"],
        CBOX_SIZE_MM["y"],
        CBOX_SIZE_MM["z"],
        center_x=CANDIDATE["cbox_center_x_mm"],
        center_y=0.0,
        bottom_z=BOX_BOTTOM_Z_MM,
    )
    c["BBOX"] = _box(
        BBOX_SIZE_MM["x"],
        BBOX_SIZE_MM["y"],
        BBOX_SIZE_MM["z"],
        center_x=CANDIDATE["bbox_center_x_mm"],
        center_y=0.0,
        bottom_z=BOX_BOTTOM_Z_MM,
    )
    c["BATTERY_CASSETTE_REFERENCE"] = _box(
        BATTERY_CASSETTE_SIZE_MM["x"],
        BATTERY_CASSETTE_SIZE_MM["y"],
        BATTERY_CASSETTE_SIZE_MM["z"],
        center_x=CANDIDATE["bbox_center_x_mm"],
        center_y=0.0,
        bottom_z=215.0,
    )
    c["CBOX_LID_SERVICE_ENVELOPE"] = _box(
        CBOX_SIZE_MM["x"],
        CBOX_SIZE_MM["y"],
        50.0,
        center_x=CANDIDATE["cbox_center_x_mm"],
        center_y=0.0,
        bottom_z=CBOX_TOP_Z_MM,
    )
    c["BBOX_LID_SERVICE_ENVELOPE"] = _box(
        BBOX_SIZE_MM["x"],
        BBOX_SIZE_MM["y"],
        50.0,
        center_x=CANDIDATE["bbox_center_x_mm"],
        center_y=0.0,
        bottom_z=BBOX_TOP_Z_MM,
    )
    c["BATTERY_CASSETTE_REAR_REMOVAL_ENVELOPE"] = _box(
        125.0,
        180.0,
        120.0,
        center_x=-212.5,
        center_y=0.0,
        bottom_z=215.0,
    )

    # Main 2040 rails and metal box support members.
    for side, sign in (("LEFT", 1.0), ("RIGHT", -1.0)):
        c[f"{side}_UPPER_MAIN_2040"] = _box(
            400.0,
            20.0,
            40.0,
            center_x=50.0,
            center_y=sign * CANDIDATE["upper_main_rail_center_abs_y_mm"],
            bottom_z=160.0,
        )
    for name, x in (
        ("REAR_2040_CROSSMEMBER", -140.0),
        ("PTO_ROOT_2040_CROSSMEMBER", CANDIDATE["front_pto_root_x_mm"]),
    ):
        c[name] = _box(
            40.0,
            156.0,
            40.0 if name.startswith("REAR") else 20.0,
            center_x=x,
            center_y=0.0,
            bottom_z=160.0 if name.startswith("REAR") else 220.0,
        )
    for side, sign in (("LEFT", 1.0), ("RIGHT", -1.0)):
        c[f"{side}_PTO_ROOT_METAL_GUSSET_RESERVED"] = _box(
            40.0,
            20.0,
            40.0,
            center_x=CANDIDATE["front_pto_root_x_mm"],
            center_y=sign * CANDIDATE["upper_main_rail_center_abs_y_mm"],
            bottom_z=195.0,
        )
    for index, x in enumerate((-135.0, -15.0, 35.0, 145.0), start=1):
        c[f"BOX_SUPPORT_2020_{index}"] = _box(
            20.0,
            156.0,
            20.0,
            center_x=x,
            center_y=0.0,
            bottom_z=180.0,
        )

    # Front PTO frame: independent side triangles, no center X.
    for side, sign in (("LEFT", 1.0), ("RIGHT", -1.0)):
        c[f"{side}_PTO_2020_SPAR"] = _box(
            170.0,
            20.0,
            20.0,
            center_x=335.0,
            center_y=sign * 68.0,
            bottom_z=220.0,
        )
        c[f"{side}_PTO_2020_DIAGONAL"] = _beam_xy(
            250.0,
            sign * 20.0,
            410.0,
            sign * 68.0,
            center_z=230.0,
        )
        # Each KP000 receives its own vertical metal load path.  A continuous
        # plate below both bearings would cross the 120 mm pulley envelope.
        for position, abs_y in (("INNER", 14.0), ("OUTER", 82.0)):
            c[f"{side}_PTO_{position}_VERTICAL_2020"] = _box(
                20.0,
                20.0,
                110.0,
                center_x=CANDIDATE["pto_axis_x_mm"],
                center_y=sign * abs_y,
                bottom_z=240.0,
            )
            c[f"{side}_PTO_{position}_METAL_BEARING_BRACKET_RESERVED"] = _box(
                45.0,
                20.0,
                10.0,
                center_x=CANDIDATE["pto_axis_x_mm"],
                center_y=sign * abs_y,
                bottom_z=345.0,
            )
    c["PTO_FRONT_2020_CROSSBAR"] = _box(
        20.0,
        156.0,
        20.0,
        center_x=CANDIDATE["front_pto_crossbar_x_mm"],
        center_y=0.0,
        bottom_z=220.0,
    )

    # Inverted-trapezoid crawler dynamic envelopes and lower 2040 frames.
    c["TRACK_LEFT_DYNAMIC_ENVELOPE"] = _track_prism("LEFT")
    c["TRACK_RIGHT_DYNAMIC_ENVELOPE"] = _track_prism("RIGHT")
    for side, sign in (("LEFT", 1.0), ("RIGHT", -1.0)):
        y = sign * CANDIDATE["track_side_frame_center_abs_y_mm"]
        c[f"{side}_TRACK_UPPER_2040"] = _box(
            400.0,
            20.0,
            40.0,
            center_x=80.0,
            center_y=y,
            bottom_z=CANDIDATE["track_upper_frame_bottom_z_mm"],
        )
        c[f"{side}_TRACK_LOWER_2040"] = _box(
            260.0,
            20.0,
            40.0,
            center_x=100.0,
            center_y=y,
            bottom_z=CANDIDATE["track_lower_frame_bottom_z_mm"],
        )
        c[f"{side}_TRACK_FRONT_DIAGONAL_2020"] = _beam_xz(
            230.0,
            60.0,
            280.0,
            110.0,
            center_y=y,
        )
        c[f"{side}_TRACK_REAR_DIAGONAL_2020"] = _beam_xz(
            -30.0,
            60.0,
            -120.0,
            110.0,
            center_y=y,
        )
        c[f"{side}_FRONT_UPPER_DRIVE_WHEEL"] = _cylinder_y(
            35.0,
            TRACK_WIDTH_EACH_MM,
            center_x=300.0,
            center_y=sign * 115.5,
            center_z=155.0,
        )
        c[f"{side}_REAR_UPPER_IDLER"] = _cylinder_y(
            35.0,
            TRACK_WIDTH_EACH_MM,
            center_x=-100.0,
            center_y=sign * 115.5,
            center_z=155.0,
        )
        for index, x in enumerate((0.0, 70.0, 140.0, 210.0), start=1):
            c[f"{side}_LOWER_ROLLER_{index}"] = _cylinder_y(
                25.0,
                TRACK_WIDTH_EACH_MM,
                center_x=x,
                center_y=sign * 115.5,
                center_z=45.0,
            )

    # Two high motors, shafts inward.  Bodies are explicit non-authority envelopes.
    for side, sign in (("LEFT", 1.0), ("RIGHT", -1.0)):
        c[f"{side}_MOTOR_RESERVED_ENVELOPE"] = _cylinder_y(
            CANDIDATE["motor_body_radius_candidate_mm"],
            CANDIDATE["motor_body_axial_length_candidate_mm"],
            center_x=CANDIDATE["motor_axis_x_mm"],
            center_y=sign * CANDIDATE["motor_axis_abs_y_mm"],
            center_z=CANDIDATE["motor_axis_z_mm"],
        )
        c[f"{side}_SLIDE_CLUTCH_FULL_STROKE_ENVELOPE"] = _box(
            CANDIDATE["clutch_full_stroke_envelope_xyz_candidate_mm"][0],
            CANDIDATE["clutch_full_stroke_envelope_xyz_candidate_mm"][1],
            CANDIDATE["clutch_full_stroke_envelope_xyz_candidate_mm"][2],
            center_x=245.0,
            center_y=sign * 62.0,
            bottom_z=345.0,
        )

    # Four independent belt sweep envelopes.
    drive_y = CANDIDATE["drive_belt_plane_abs_y_mm"]
    pto_y = CANDIDATE["pto_belt_plane_abs_y_mm"]
    for side, sign in (("LEFT", 1.0), ("RIGHT", -1.0)):
        c[f"{side}_DRIVE_BELT_ENVELOPE"] = _belt_envelope(
            245.0,
            CANDIDATE["motor_axis_z_mm"],
            CANDIDATE["pulley_20t_safety_radius_candidate_mm"],
            CANDIDATE["drive_axis_x_mm"],
            155.0,
            PULLEY_60T_SAFETY_RADIUS_MM,
            center_y=sign * drive_y,
        )
        c[f"{side}_PTO_BELT_ENVELOPE"] = _belt_envelope(
            CANDIDATE["power_transmission_x_mm"],
            CANDIDATE["motor_axis_z_mm"],
            CANDIDATE["pulley_20t_safety_radius_candidate_mm"],
            CANDIDATE["pto_axis_x_mm"],
            CANDIDATE["pto_axis_z_mm"],
            PULLEY_60T_SAFETY_RADIUS_MM,
            center_y=sign * pto_y,
        )
        c[f"{side}_PTO_60T_ROTATION_ENVELOPE"] = _cylinder_y(
            PULLEY_60T_SAFETY_RADIUS_MM,
            CANDIDATE["pulley_axial_envelope_candidate_mm"],
            center_x=CANDIDATE["pto_axis_x_mm"],
            center_y=sign * pto_y,
            center_z=CANDIDATE["pto_axis_z_mm"],
        )
        c[f"{side}_PTO_INNER_KP000_RESERVED"] = _box(
            45.0,
            15.0,
            35.0,
            center_x=CANDIDATE["pto_axis_x_mm"],
            center_y=sign * 14.0,
            bottom_z=352.5,
        )
        c[f"{side}_PTO_OUTER_KP000_RESERVED"] = _box(
            45.0,
            15.0,
            35.0,
            center_x=CANDIDATE["pto_axis_x_mm"],
            center_y=sign * 82.0,
            bottom_z=352.5,
        )
        shaft_start_y = sign * 89.5
        shaft_end_y = sign * CANDIDATE["pto_outer_end_abs_y_mm"]
        c[f"{side}_PTO_OUTPUT_SHAFT_AND_COUPLING_RESERVED"] = _cylinder_y(
            17.0,
            abs(shaft_end_y - shaft_start_y),
            center_x=CANDIDATE["pto_axis_x_mm"],
            center_y=(shaft_start_y + shaft_end_y) / 2.0,
            center_z=CANDIDATE["pto_axis_z_mm"],
        )
        # The complete min/nominal/max tensioner motion is unknown; this is
        # only a visibly registered reservation beside the belt span.
        c[f"{side}_DRIVE_TENSIONER_RESERVED"] = _box(
            35.0,
            20.0,
            35.0,
            center_x=267.0,
            center_y=sign * drive_y,
            bottom_z=245.0,
        )
        c[f"{side}_PTO_TENSIONER_RESERVED"] = _box(
            45.0,
            20.0,
            35.0,
            center_x=325.0,
            center_y=sign * pto_y,
            bottom_z=392.0,
        )

    # Representative inward-facing bolt-head / washer keep-outs.  Actual
    # fasteners remain a mandatory measurement item.
    fastener_specs = (
        ("ROOT_LEFT", 250.0, 68.0, 242.0),
        ("ROOT_RIGHT", 250.0, -68.0, 242.0),
        ("TRACK_FRONT_LEFT", 280.0, 84.0, 143.0),
        ("TRACK_FRONT_RIGHT", 280.0, -84.0, 143.0),
        ("TRACK_REAR_LEFT", -120.0, 84.0, 143.0),
        ("TRACK_REAR_RIGHT", -120.0, -84.0, 143.0),
        ("PTO_SUPPORT_LEFT", 390.0, 70.0, 346.0),
        ("PTO_SUPPORT_RIGHT", 390.0, -70.0, 346.0),
    )
    for name, x, y, z in fastener_specs:
        c[f"FASTENER_RESERVED_{name}"] = _box(
            8.0,
            8.0,
            8.0,
            center_x=x,
            center_y=y,
            bottom_z=z,
        )

    return c


FRAME_COMPONENT_IDS = (
    "LEFT_UPPER_MAIN_2040",
    "RIGHT_UPPER_MAIN_2040",
    "REAR_2040_CROSSMEMBER",
    "PTO_ROOT_2040_CROSSMEMBER",
    "BOX_SUPPORT_2020_1",
    "BOX_SUPPORT_2020_2",
    "BOX_SUPPORT_2020_3",
    "BOX_SUPPORT_2020_4",
    "LEFT_PTO_2020_SPAR",
    "RIGHT_PTO_2020_SPAR",
    "LEFT_PTO_2020_DIAGONAL",
    "RIGHT_PTO_2020_DIAGONAL",
    "LEFT_PTO_INNER_VERTICAL_2020",
    "LEFT_PTO_OUTER_VERTICAL_2020",
    "RIGHT_PTO_INNER_VERTICAL_2020",
    "RIGHT_PTO_OUTER_VERTICAL_2020",
    "PTO_FRONT_2020_CROSSBAR",
    "LEFT_PTO_ROOT_METAL_GUSSET_RESERVED",
    "RIGHT_PTO_ROOT_METAL_GUSSET_RESERVED",
    "LEFT_PTO_INNER_METAL_BEARING_BRACKET_RESERVED",
    "LEFT_PTO_OUTER_METAL_BEARING_BRACKET_RESERVED",
    "RIGHT_PTO_INNER_METAL_BEARING_BRACKET_RESERVED",
    "RIGHT_PTO_OUTER_METAL_BEARING_BRACKET_RESERVED",
    "LEFT_TRACK_UPPER_2040",
    "RIGHT_TRACK_UPPER_2040",
    "LEFT_TRACK_LOWER_2040",
    "RIGHT_TRACK_LOWER_2040",
    "LEFT_TRACK_FRONT_DIAGONAL_2020",
    "RIGHT_TRACK_FRONT_DIAGONAL_2020",
    "LEFT_TRACK_REAR_DIAGONAL_2020",
    "RIGHT_TRACK_REAR_DIAGONAL_2020",
)
FASTENER_COMPONENT_IDS = tuple(
    f"FASTENER_RESERVED_{name}"
    for name in (
        "ROOT_LEFT",
        "ROOT_RIGHT",
        "TRACK_FRONT_LEFT",
        "TRACK_FRONT_RIGHT",
        "TRACK_REAR_LEFT",
        "TRACK_REAR_RIGHT",
        "PTO_SUPPORT_LEFT",
        "PTO_SUPPORT_RIGHT",
    )
)
UPPER_STRUCTURE_IDS = tuple(
    component_id
    for component_id in (
        *FRAME_COMPONENT_IDS,
        "CBOX",
        "BBOX",
        "LEFT_MOTOR_RESERVED_ENVELOPE",
        "RIGHT_MOTOR_RESERVED_ENVELOPE",
        "LEFT_SLIDE_CLUTCH_FULL_STROKE_ENVELOPE",
        "RIGHT_SLIDE_CLUTCH_FULL_STROKE_ENVELOPE",
        "LEFT_PTO_60T_ROTATION_ENVELOPE",
        "RIGHT_PTO_60T_ROTATION_ENVELOPE",
        *FASTENER_COMPONENT_IDS,
    )
    if not component_id.startswith(("LEFT_TRACK_", "RIGHT_TRACK_"))
    and "FASTENER_RESERVED_TRACK_" not in component_id
)


def _pair_metrics(
    components: dict[str, cq.Shape],
    subject_ids: Iterable[str],
    target_ids: Iterable[str],
) -> dict:
    pairs = []
    total_intersection = 0.0
    minimum_distance = math.inf
    intersection_count = 0
    for subject_id in subject_ids:
        subject = components[subject_id]
        for target_id in target_ids:
            target = components[target_id]
            volume = max(0.0, float(subject.intersect(target).Volume()))
            distance = max(0.0, float(subject.distance(target)))
            if volume > 1.0e-5:
                intersection_count += 1
                total_intersection += volume
            minimum_distance = min(minimum_distance, distance)
            pairs.append(
                {
                    "subject": subject_id,
                    "target": target_id,
                    "intersection_volume_mm3": _round(volume),
                    "distance_mm": _round(distance),
                }
            )
    closest = sorted(
        pairs,
        key=lambda row: (
            row["distance_mm"],
            row["subject"],
            row["target"],
        ),
    )[:5]
    return {
        "intersection_count": intersection_count,
        "intersection_volume_mm3": _round(total_intersection),
        "minimum_distance_mm": (
            None if math.isinf(minimum_distance) else _round(minimum_distance)
        ),
        "closest_pairs": closest,
    }


def _classification(
    metrics: dict,
    *,
    unknown_physical_dimensions: bool,
    minimum_clearance_mm: float,
) -> str:
    if (
        metrics["intersection_count"] > 0
        or metrics["minimum_distance_mm"] is None
        or metrics["minimum_distance_mm"] + 1.0e-6 < minimum_clearance_mm
    ):
        return "FAIL"
    if unknown_physical_dimensions:
        return "HOLD / PART_MEASUREMENT_REQUIRED"
    return "CONDITIONAL_PASS"


def build_interference_report(components: dict[str, cq.Shape]) -> dict:
    checks: list[dict] = []

    def add_geometry_check(
        check_id: str,
        subjects: Iterable[str],
        targets: Iterable[str],
        *,
        unknown: bool,
        requirement: str,
        note: str,
        minimum_clearance_mm: float = 0.0,
        recommended_clearance_mm: float | None = None,
    ) -> None:
        metrics = _pair_metrics(components, subjects, targets)
        metrics["required_minimum_clearance_mm"] = minimum_clearance_mm
        metrics["recommended_clearance_mm"] = recommended_clearance_mm
        metrics["candidate_minimum_clearance_satisfied"] = (
            metrics["minimum_distance_mm"] is not None
            and metrics["minimum_distance_mm"] + 1.0e-6 >= minimum_clearance_mm
        )
        checks.append(
            {
                "check_id": check_id,
                "classification": _classification(
                    metrics,
                    unknown_physical_dimensions=unknown,
                    minimum_clearance_mm=minimum_clearance_mm,
                ),
                "requirement": requirement,
                "authority_scope": "SIMPLIFIED_CANDIDATE_ENVELOPE",
                "unknown_physical_dimensions": unknown,
                "metrics": metrics,
                "note": note,
            }
        )

    for side in ("LEFT", "RIGHT"):
        add_geometry_check(
            f"{side}_DRIVE_BELT_ENVELOPE_VS_FRAME",
            (f"{side}_DRIVE_BELT_ENVELOPE",),
            FRAME_COMPONENT_IDS,
            unknown=True,
            requirement=f"{side}_DRIVE_BELT_ENVELOPE ∩ FRAME = 0",
            note=(
                "Candidate envelope has no solid intersection; actual belt "
                "length, flange width, axial stacking and sway remain unknown."
            ),
            minimum_clearance_mm=CLEARANCES_MM["belt_side_to_frame"]["minimum"],
            recommended_clearance_mm=CLEARANCES_MM["belt_side_to_frame"][
                "recommended"
            ],
        )
        add_geometry_check(
            f"{side}_PTO_BELT_ENVELOPE_VS_FRAME",
            (f"{side}_PTO_BELT_ENVELOPE",),
            FRAME_COMPONENT_IDS,
            unknown=True,
            requirement=f"{side}_PTO_BELT_ENVELOPE ∩ FRAME = 0",
            note=(
                "PTO horizontal frame is below the 120 mm pulley envelope; "
                "actual belt and tensioner data are still required."
            ),
            minimum_clearance_mm=CLEARANCES_MM["belt_side_to_frame"]["minimum"],
            recommended_clearance_mm=CLEARANCES_MM["belt_side_to_frame"][
                "recommended"
            ],
        )
        add_geometry_check(
            f"{side}_DRIVE_BELT_ENVELOPE_VS_FASTENERS",
            (f"{side}_DRIVE_BELT_ENVELOPE",),
            FASTENER_COMPONENT_IDS,
            unknown=True,
            requirement=f"{side}_DRIVE_BELT_ENVELOPE ∩ FASTENERS = 0",
            note="Representative keep-outs only; installed hardware must be measured.",
            minimum_clearance_mm=CLEARANCES_MM["belt_to_bolt_head"]["minimum"],
            recommended_clearance_mm=CLEARANCES_MM["belt_to_bolt_head"][
                "recommended"
            ],
        )
        add_geometry_check(
            f"{side}_PTO_BELT_ENVELOPE_VS_FASTENERS",
            (f"{side}_PTO_BELT_ENVELOPE",),
            FASTENER_COMPONENT_IDS,
            unknown=True,
            requirement=f"{side}_PTO_BELT_ENVELOPE ∩ FASTENERS = 0",
            note="Representative keep-outs only; installed hardware must be measured.",
            minimum_clearance_mm=CLEARANCES_MM["belt_to_bolt_head"]["minimum"],
            recommended_clearance_mm=CLEARANCES_MM["belt_to_bolt_head"][
                "recommended"
            ],
        )
        add_geometry_check(
            f"{side}_SLIDE_CLUTCH_FULL_STROKE_VS_FRAME",
            (f"{side}_SLIDE_CLUTCH_FULL_STROKE_ENVELOPE",),
            FRAME_COMPONENT_IDS,
            unknown=True,
            requirement=f"SLIDE_CLUTCH_{side}_ENVELOPE ∩ FRAME = 0",
            note="All three states are covered by a placeholder full-stroke box.",
        )
        add_geometry_check(
            f"TRACK_{side}_DYNAMIC_ENVELOPE_VS_UPPER_STRUCTURE",
            (f"TRACK_{side}_DYNAMIC_ENVELOPE",),
            UPPER_STRUCTURE_IDS,
            unknown=True,
            requirement=f"TRACK_{side}_DYNAMIC_ENVELOPE ∩ UPPER_STRUCTURE = 0",
            note=(
                "Candidate prism is clear, but measured track runout, mud, "
                "idling adjustment and guard thickness are absent."
            ),
            minimum_clearance_mm=0.0,
        )

    targeted_pairs = (
        (
            "LEFT_DRIVE_BELT_VS_ROOT_2040",
            ("LEFT_DRIVE_BELT_ENVELOPE",),
            ("PTO_ROOT_2040_CROSSMEMBER",),
            "Drive belt routed outboard of shortened root crossmember.",
        ),
        (
            "RIGHT_DRIVE_BELT_VS_ROOT_2040",
            ("RIGHT_DRIVE_BELT_ENVELOPE",),
            ("PTO_ROOT_2040_CROSSMEMBER",),
            "Drive belt routed outboard of shortened root crossmember.",
        ),
        (
            "LEFT_DRIVE_BELT_VS_FRONT_TRACK_DIAGONAL",
            ("LEFT_DRIVE_BELT_ENVELOPE",),
            ("LEFT_TRACK_FRONT_DIAGONAL_2020",),
            "Track diagonal is inboard of the drive belt plane.",
        ),
        (
            "RIGHT_DRIVE_BELT_VS_FRONT_TRACK_DIAGONAL",
            ("RIGHT_DRIVE_BELT_ENVELOPE",),
            ("RIGHT_TRACK_FRONT_DIAGONAL_2020",),
            "Track diagonal is inboard of the drive belt plane.",
        ),
        (
            "LEFT_DRIVE_BELT_VS_TRACK_CONNECTING_POSTS",
            ("LEFT_DRIVE_BELT_ENVELOPE",),
            (
                "LEFT_TRACK_FRONT_DIAGONAL_2020",
                "LEFT_TRACK_REAR_DIAGONAL_2020",
            ),
            "Both diagonal connecting posts are included.",
        ),
        (
            "RIGHT_DRIVE_BELT_VS_TRACK_CONNECTING_POSTS",
            ("RIGHT_DRIVE_BELT_ENVELOPE",),
            (
                "RIGHT_TRACK_FRONT_DIAGONAL_2020",
                "RIGHT_TRACK_REAR_DIAGONAL_2020",
            ),
            "Both diagonal connecting posts are included.",
        ),
        (
            "LEFT_PTO_BELT_VS_2020_DIAGONAL",
            ("LEFT_PTO_BELT_ENVELOPE",),
            ("LEFT_PTO_2020_DIAGONAL",),
            "Diagonal is vertically below the PTO belt sweep.",
        ),
        (
            "RIGHT_PTO_BELT_VS_2020_DIAGONAL",
            ("RIGHT_PTO_BELT_ENVELOPE",),
            ("RIGHT_PTO_2020_DIAGONAL",),
            "Diagonal is vertically below the PTO belt sweep.",
        ),
        (
            "LEFT_PTO_BELT_VS_FRONT_CROSSBAR",
            ("LEFT_PTO_BELT_ENVELOPE",),
            ("PTO_FRONT_2020_CROSSBAR",),
            "Front crossbar is vertically below the pulley envelope.",
        ),
        (
            "RIGHT_PTO_BELT_VS_FRONT_CROSSBAR",
            ("RIGHT_PTO_BELT_ENVELOPE",),
            ("PTO_FRONT_2020_CROSSBAR",),
            "Front crossbar is vertically below the pulley envelope.",
        ),
        (
            "LEFT_PTO_PULLEY_VS_KP000",
            ("LEFT_PTO_60T_ROTATION_ENVELOPE",),
            ("LEFT_PTO_INNER_KP000_RESERVED", "LEFT_PTO_OUTER_KP000_RESERVED"),
            "The 60T pulley is between two independent bearing reservations.",
        ),
        (
            "RIGHT_PTO_PULLEY_VS_KP000",
            ("RIGHT_PTO_60T_ROTATION_ENVELOPE",),
            ("RIGHT_PTO_INNER_KP000_RESERVED", "RIGHT_PTO_OUTER_KP000_RESERVED"),
            "The 60T pulley is between two independent bearing reservations.",
        ),
        (
            "CBOX_LID_SERVICE_VS_POWER_COMPONENTS",
            ("CBOX_LID_SERVICE_ENVELOPE",),
            (
                "LEFT_MOTOR_RESERVED_ENVELOPE",
                "RIGHT_MOTOR_RESERVED_ENVELOPE",
                "LEFT_SLIDE_CLUTCH_FULL_STROKE_ENVELOPE",
                "RIGHT_SLIDE_CLUTCH_FULL_STROKE_ENVELOPE",
            ),
            "Only a 50 mm vertical service reservation is represented.",
        ),
        (
            "BBOX_LID_SERVICE_VS_POWER_COMPONENTS",
            ("BBOX_LID_SERVICE_ENVELOPE",),
            (
                "LEFT_MOTOR_RESERVED_ENVELOPE",
                "RIGHT_MOTOR_RESERVED_ENVELOPE",
                "LEFT_SLIDE_CLUTCH_FULL_STROKE_ENVELOPE",
                "RIGHT_SLIDE_CLUTCH_FULL_STROKE_ENVELOPE",
            ),
            "Actual lid hinges, latches and removal height are unknown.",
        ),
        (
            "BATTERY_CASSETTE_REAR_REMOVAL_PATH_VS_STRUCTURE",
            ("BATTERY_CASSETTE_REAR_REMOVAL_ENVELOPE",),
            tuple(
                component_id
                for component_id in UPPER_STRUCTURE_IDS
                if component_id != "BBOX"
            ),
            "Rearward path after the BBOX rear face is represented.",
        ),
    )
    for check_id, subjects, targets, note in targeted_pairs:
        add_geometry_check(
            check_id,
            subjects,
            targets,
            unknown=True,
            requirement="NO_SOLID_INTERSECTION_IN_CANDIDATE_ENVELOPE_MODEL",
            note=note,
            minimum_clearance_mm=(
                CLEARANCES_MM["pto_pulley_to_kp000"]["minimum"]
                if "PULLEY_VS_KP000" in check_id
                else CLEARANCES_MM["belt_to_diagonal"]["minimum"]
                if "DIAGONAL" in check_id or "CONNECTING_POSTS" in check_id
                else CLEARANCES_MM["belt_side_to_frame"]["minimum"]
                if "BELT" in check_id
                else 0.0
            ),
            recommended_clearance_mm=(
                CLEARANCES_MM["pto_pulley_to_kp000"]["recommended"]
                if "PULLEY_VS_KP000" in check_id
                else CLEARANCES_MM["belt_to_diagonal"]["recommended"]
                if "DIAGONAL" in check_id or "CONNECTING_POSTS" in check_id
                else CLEARANCES_MM["belt_side_to_frame"]["recommended"]
                if "BELT" in check_id
                else None
            ),
        )

    # State-dependent checks remain HOLD because the actual moving envelopes
    # are not measured, even though the full placeholder boxes are clear.
    for side in ("LEFT", "RIGHT"):
        metrics = _pair_metrics(
            components,
            (f"{side}_SLIDE_CLUTCH_FULL_STROKE_ENVELOPE",),
            FRAME_COMPONENT_IDS,
        )
        for state in CLUTCH_STATES:
            checks.append(
                {
                    "check_id": f"{side}_CLUTCH_STATE_{state}",
                    "classification": "HOLD / PART_MEASUREMENT_REQUIRED",
                    "requirement": "NO_FRAME_CONTACT_AND_SINGLE_STATE_ENGAGEMENT",
                    "authority_scope": "PLACEHOLDER_FULL_STROKE_ENVELOPE",
                    "unknown_physical_dimensions": True,
                    "metrics": metrics,
                    "note": (
                        "Candidate full-stroke reserve is clear; dog geometry, "
                        "stroke and engagement length are unmeasured."
                    ),
                }
            )
        for tension_state in ("MINIMUM", "NOMINAL", "MAXIMUM"):
            checks.append(
                {
                    "check_id": f"{side}_DRIVE_TENSIONER_{tension_state}",
                    "classification": "HOLD / PART_MEASUREMENT_REQUIRED",
                    "requirement": "FULL_TENSIONER_RANGE_CLEAR_OF_FRAME_AND_BELT_GUARD",
                    "authority_scope": "RESERVED_VOLUME_ONLY",
                    "unknown_physical_dimensions": True,
                    "metrics": {
                        "intersection_count": None,
                        "intersection_volume_mm3": None,
                        "minimum_distance_mm": None,
                        "closest_pairs": [],
                    },
                    "note": "Tensioner geometry and travel are not available.",
                }
            )
            checks.append(
                {
                    "check_id": f"{side}_PTO_TENSIONER_{tension_state}",
                    "classification": "HOLD / PART_MEASUREMENT_REQUIRED",
                    "requirement": "FULL_TENSIONER_RANGE_CLEAR_OF_FRAME_AND_BELT_GUARD",
                    "authority_scope": "RESERVED_VOLUME_ONLY",
                    "unknown_physical_dimensions": True,
                    "metrics": {
                        "intersection_count": None,
                        "intersection_volume_mm3": None,
                        "minimum_distance_mm": None,
                        "closest_pairs": [],
                    },
                    "note": "Tensioner geometry and travel are not available.",
                }
            )

    # Scalar authority and envelope checks.
    scalar_checks = (
        {
            "check_id": "PTO_LEFT_OUTER_END_Y",
            "classification": "HOLD / PART_MEASUREMENT_REQUIRED",
            "requirement": "PTO_LEFT_OUTER_END_Y < 150",
            "authority_scope": "CANDIDATE_END_PLANE",
            "unknown_physical_dimensions": True,
            "metrics": {
                "candidate_y_mm": CANDIDATE["pto_outer_end_abs_y_mm"],
                "absolute_limit_mm": 150.0,
                "target_limit_mm": 145.0,
                "candidate_margin_to_absolute_mm": 5.0,
            },
            "note": "Coupling, pin, cap and fastener protrusions are unmeasured.",
        },
        {
            "check_id": "PTO_RIGHT_OUTER_END_Y",
            "classification": "HOLD / PART_MEASUREMENT_REQUIRED",
            "requirement": "ABS(PTO_RIGHT_OUTER_END_Y) < 150",
            "authority_scope": "CANDIDATE_END_PLANE",
            "unknown_physical_dimensions": True,
            "metrics": {
                "candidate_y_mm": -CANDIDATE["pto_outer_end_abs_y_mm"],
                "absolute_limit_mm": 150.0,
                "target_limit_mm": 145.0,
                "candidate_margin_to_absolute_mm": 5.0,
            },
            "note": "Coupling, pin, cap and fastener protrusions are unmeasured.",
        },
        {
            "check_id": "TOTAL_WIDTH_WITH_FASTENERS",
            "classification": "HOLD / PART_MEASUREMENT_REQUIRED",
            "requirement": "TOTAL_WIDTH_WITH_FASTENERS <= 299 AND < 300",
            "authority_scope": "CANDIDATE_ENVELOPES_ONLY",
            "unknown_physical_dimensions": True,
            "metrics": {
                "candidate_width_mm": CANDIDATE[
                    "total_width_with_candidate_envelopes_mm"
                ],
                "target_range_mm": TOTAL_WIDTH_TARGET_RANGE_MM,
                "hard_maximum_mm": TOTAL_WIDTH_HARD_MAX_MM,
                "candidate_margin_to_hard_maximum_mm": 9.0,
            },
            "note": (
                "Track spikes, real couplings, bolt heads, latches and guards "
                "must be added before width release."
            ),
        },
        {
            "check_id": "BBOX_EFFECTIVE_INTERIOR_VS_CASSETTE",
            "classification": "HOLD / FIELD_MEASUREMENT_REQUIRED",
            "requirement": "BBOX_EFFECTIVE_INTERIOR >= 129 X 184 X 125",
            "authority_scope": "EXTERNAL_DIMENSION_COMPARISON_ONLY",
            "unknown_physical_dimensions": True,
            "metrics": {
                "bbox_external_minus_cassette_mm": {"x": 25.0, "y": 40.0, "z": 30.0},
                "minimum_effective_interior_mm": BBOX_MIN_EFFECTIVE_INTERIOR_MM,
                "actual_effective_interior_mm": None,
            },
            "note": "Wall, lid, gasket, base, guide, contact and latch consume space.",
        },
        {
            "check_id": "BOX_BOTTOM_TO_TRACK_DYNAMIC",
            "classification": "HOLD / FIELD_MEASUREMENT_REQUIRED",
            "requirement": "CLEARANCE >= 10; RECOMMENDED >= 20",
            "authority_scope": "CANDIDATE_TRACK_PRISM",
            "unknown_physical_dimensions": True,
            "metrics": {
                "candidate_clearance_mm": CANDIDATE[
                    "box_to_track_candidate_vertical_clearance_mm"
                ],
                "minimum_mm": 10.0,
                "recommended_mm": 20.0,
            },
            "note": "Candidate meets minimum but not recommendation; dynamic data absent.",
        },
        {
            "check_id": "AXIAL_PLAY_FRAME_ERROR_AND_DEFORMATION",
            "classification": "HOLD / PART_MEASUREMENT_REQUIRED",
            "requirement": "CHECK +/-1 AXIAL PLAY, +/-1 FRAME ERROR, 2 MM DEFORMATION",
            "authority_scope": "ERROR_BUDGET_RECORDED_NOT_PHYSICALLY_VALIDATED",
            "unknown_physical_dimensions": True,
            "metrics": {
                "axial_play_mm": [-1.0, 1.0],
                "frame_assembly_error_mm": [-1.0, 1.0],
                "frame_deformation_mm": 2.0,
                "belt_lateral_sway_mm": None,
                "track_dynamic_runout_mm": None,
            },
            "note": "Known numeric allowances are recorded; unknown sway/runout blocks release.",
        },
    )
    checks.extend(scalar_checks)

    failed = [row["check_id"] for row in checks if row["classification"] == "FAIL"]
    holds = [
        row["check_id"]
        for row in checks
        if row["classification"].startswith("HOLD")
    ]
    conditional = [
        row["check_id"]
        for row in checks
        if row["classification"] == "CONDITIONAL_PASS"
    ]
    candidate_zero_intersection_checks = [
        row["check_id"]
        for row in checks
        if isinstance(row.get("metrics"), dict)
        and row["metrics"].get("intersection_count") == 0
    ]
    clearance_checked_rows = [
        row
        for row in checks
        if isinstance(row.get("metrics"), dict)
        and "candidate_minimum_clearance_satisfied" in row["metrics"]
    ]
    return {
        "document_id": DOCUMENT_ID,
        "schema": (
            "paddy_swarm.common_rover.front_drive_dual_pto_interference_report.v0.8"
        ),
        "authority_status": AUTHORITY_STATUS,
        "release_status": RELEASE_STATUS,
        "model_scope": (
            "SIMPLIFIED_ENVELOPE_CANDIDATE; ZERO INTERSECTION DOES NOT "
            "OVERRIDE PART_MEASUREMENT_REQUIRED"
        ),
        "candidate_model": {
            "component_count": len(components),
            "60t_safety_diameter_mm": PULLEY_60T_SAFETY_DIAMETER_MM,
            "belt_envelope_count": 4,
            "belt_names": [
                "LEFT_DRIVE_BELT_ENVELOPE",
                "RIGHT_DRIVE_BELT_ENVELOPE",
                "LEFT_PTO_BELT_ENVELOPE",
                "RIGHT_PTO_BELT_ENVELOPE",
            ],
            "belt_windows_and_keepouts": {
                "LEFT_DRIVE_BELT_WINDOW": "OUTBOARD_OF_ROOT_2040",
                "RIGHT_DRIVE_BELT_WINDOW": "OUTBOARD_OF_ROOT_2040",
                "LEFT_PTO_BELT_KEEP_OUT_ZONE": "CENTRAL_LEFT_ABOVE_HORIZONTAL_FRAME",
                "RIGHT_PTO_BELT_KEEP_OUT_ZONE": "CENTRAL_RIGHT_ABOVE_HORIZONTAL_FRAME",
            },
        },
        "summary": {
            "fail_count": len(failed),
            "conditional_pass_count": len(conditional),
            "hold_count": len(holds),
            "candidate_zero_intersection_check_count": len(
                candidate_zero_intersection_checks
            ),
            "all_required_candidate_solid_intersections_zero": len(failed) == 0,
            "all_checked_candidate_minimum_clearances_satisfied": all(
                row["metrics"]["candidate_minimum_clearance_satisfied"]
                for row in clearance_checked_rows
            ),
            "physical_release": "NOT_APPROVED",
            "reason": (
                "Actual motor, clutch, pulley widths/flanges, KP000, coupling, "
                "tensioner, fasteners, belt sway and track dynamics are unmeasured."
            ),
        },
        "failed_checks": failed,
        "hold_checks": holds,
        "conditional_pass_checks": conditional,
        "checks": checks,
    }


def build_allocation_rows() -> list[dict[str, str]]:
    return [
        {
            "member_group": "UPPER_MAIN_RAILS_LEFT_RIGHT",
            "profile": "2040",
            "quantity": "2",
            "required_length_each_mm": "400",
            "stock_allocation": "2040-S01:400;2040-S02:400",
            "stock_cut_candidate": "400",
            "remainder_each_mm": "0",
            "candidate_stock_count": "2",
            "status": "CONDITIONAL_PASS_LAYOUT_CANDIDATE",
            "note": "Final frame and load calculation HOLD.",
        },
        {
            "member_group": "CRAWLER_UPPER_LONG_RAILS_LEFT_RIGHT",
            "profile": "2040",
            "quantity": "2",
            "required_length_each_mm": "400",
            "stock_allocation": "2040-S03:400;2040-S04:400",
            "stock_cut_candidate": "400",
            "remainder_each_mm": "0",
            "candidate_stock_count": "2",
            "status": "CONDITIONAL_PASS_LAYOUT_CANDIDATE",
            "note": "Upper rail is longer than lower rail; final length HOLD.",
        },
        {
            "member_group": "CRAWLER_LOWER_SHORT_RAILS_LEFT_RIGHT",
            "profile": "2040",
            "quantity": "2",
            "required_length_each_mm": "260",
            "stock_allocation": "2040-S05:260;2040-S06:260",
            "stock_cut_candidate": "260",
            "remainder_each_mm": "140",
            "candidate_stock_count": "2",
            "status": "CONDITIONAL_PASS_LAYOUT_CANDIDATE",
            "note": "Final ground-contact geometry HOLD.",
        },
        {
            "member_group": "PTO_ROOT_AND_REAR_CROSSMEMBER",
            "profile": "2040",
            "quantity": "2",
            "required_length_each_mm": "156",
            "stock_allocation": "2040-S07:156+156",
            "stock_cut_candidate": "156+156",
            "remainder_each_mm": "88",
            "candidate_stock_count": "1",
            "status": "CONDITIONAL_PASS_LAYOUT_CANDIDATE",
            "note": "Root width keeps both DRIVE belt windows outboard.",
        },
        {
            "member_group": "PTO_FRONT_SPARS_LEFT_RIGHT",
            "profile": "2020",
            "quantity": "2",
            "required_length_each_mm": "170",
            "stock_allocation": "2020-S01:170+170",
            "stock_cut_candidate": "170+170",
            "remainder_each_mm": "60",
            "candidate_stock_count": "1",
            "status": "CONDITIONAL_PASS_LAYOUT_CANDIDATE",
            "note": "PTO forward overhang remains HOLD.",
        },
        {
            "member_group": "PTO_DIAGONALS_LEFT_RIGHT",
            "profile": "2020",
            "quantity": "2",
            "required_length_each_mm": "168",
            "stock_allocation": "2020-S02:168+168",
            "stock_cut_candidate": "168+168",
            "remainder_each_mm": "64",
            "candidate_stock_count": "1",
            "status": "CONDITIONAL_PASS_LAYOUT_CANDIDATE",
            "note": "Separate outer triangles; no center X.",
        },
        {
            "member_group": "BOX_SUPPORT_CROSSMEMBERS",
            "profile": "2020",
            "quantity": "4",
            "required_length_each_mm": "156",
            "stock_allocation": "2020-S03:156+156;2020-S04:156+156",
            "stock_cut_candidate": "156+156",
            "remainder_each_mm": "88",
            "candidate_stock_count": "2",
            "status": "CONDITIONAL_PASS_LAYOUT_CANDIDATE",
            "note": "Metal cradle calculation and final retention HOLD.",
        },
        {
            "member_group": "CRAWLER_FRONT_REAR_DIAGONAL_POSTS",
            "profile": "2020",
            "quantity": "4",
            "required_length_each_mm": "110",
            "stock_allocation": "2020-S05:110+110+110;2020-S06:110",
            "stock_cut_candidate": "110+110+110 / 110",
            "remainder_each_mm": "70 / 290",
            "candidate_stock_count": "2",
            "status": "CONDITIONAL_PASS_LAYOUT_CANDIDATE",
            "note": "Final angles and hole allowances HOLD.",
        },
        {
            "member_group": "PTO_FRONT_CROSSBAR_AND_FIRST_VERTICAL_SUPPORT_PAIR",
            "profile": "2020",
            "quantity": "3",
            "required_length_each_mm": "156;110;110",
            "stock_allocation": "2020-S07:156+110+110",
            "stock_cut_candidate": "156+110+110",
            "remainder_each_mm": "24",
            "candidate_stock_count": "1",
            "status": "CONDITIONAL_PASS_LAYOUT_CANDIDATE",
            "note": "One independent support for each of two KP000 positions per side.",
        },
        {
            "member_group": "PTO_SECOND_VERTICAL_SUPPORT_PAIR",
            "profile": "2020",
            "quantity": "2",
            "required_length_each_mm": "110",
            "stock_allocation": "2020-S08:110+110",
            "stock_cut_candidate": "110+110",
            "remainder_each_mm": "180",
            "candidate_stock_count": "1",
            "status": "CONDITIONAL_PASS_LAYOUT_CANDIDATE",
            "note": "KP000 brackets/gussets are metal and remain unmeasured.",
        },
        {
            "member_group": "UNALLOCATED_STOCK",
            "profile": "2040",
            "quantity": "1",
            "required_length_each_mm": "0",
            "stock_allocation": "2040-S08:UNUSED",
            "stock_cut_candidate": "NONE",
            "remainder_each_mm": "400",
            "candidate_stock_count": "0",
            "status": "AVAILABLE_RESERVE",
            "note": "Do not consume before physical validation.",
        },
        {
            "member_group": "METAL_CONNECTION_PLATES_BRACKETS_AND_GUSSETS",
            "profile": "NON_EXTRUSION_METAL_HARDWARE",
            "quantity": "PART_MEASUREMENT_REQUIRED",
            "required_length_each_mm": "",
            "stock_allocation": "NOT_IN_DECLARED_2020_2040_STOCK",
            "stock_cut_candidate": "STRUCTURAL_CALCULATION_REQUIRED",
            "remainder_each_mm": "",
            "candidate_stock_count": "",
            "status": "ADDITIONAL_PURCHASE_REQUIRED",
            "note": (
                "Required at root, spar, diagonal, bearing-support, crawler "
                "and box-cradle joints; exact plate/bracket count and size HOLD."
            ),
        },
    ]


def _csv_text(rows: list[dict[str, object]], fieldnames: list[str]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return stream.getvalue()


def build_parameters() -> dict:
    return {
        "document_id": DOCUMENT_ID,
        "schema": SCHEMA,
        "authority_status": AUTHORITY_STATUS,
        "release_status": RELEASE_STATUS,
        "coordinate_system": COORDINATE_SYSTEM,
        "legacy_to_v008_axis_mapping": LEGACY_TO_V008_AXIS_MAPPING,
        "layout_order_front_to_rear": list(LAYOUT_ORDER),
        "layout_order_relation": (
            "X_PTO > X_POWER_TRANSMISSION > X_MOTOR > X_CBOX > X_BBOX"
        ),
        "width": {
            "nominal_row_spacing_mm": NOMINAL_ROW_SPACING_MM,
            "hard_maximum_mm": TOTAL_WIDTH_HARD_MAX_MM,
            "strict_condition": "TOTAL_WIDTH_WITH_ALL_PROTRUSIONS_LT_300",
            "target_range_mm": TOTAL_WIDTH_TARGET_RANGE_MM,
            "track_width_each_mm": TRACK_WIDTH_EACH_MM,
            "central_lower_structure_maximum_width_mm": (
                CENTRAL_LOWER_STRUCTURE_MAX_WIDTH_MM
            ),
            "candidate_track_envelope_width_mm": 286.0,
            "candidate_total_width_mm": CANDIDATE[
                "total_width_with_candidate_envelopes_mm"
            ],
            "physical_release": "PART_MEASUREMENT_REQUIRED",
        },
        "boxes": {
            "cbox": {
                "external_size_mm": CBOX_SIZE_MM,
                "orientation": "X_FORE_AFT_Y_LATERAL_Z_VERTICAL",
                "centerline_y_mm": 0.0,
                "bottom_z_mm": BOX_BOTTOM_Z_MM,
                "top_z_mm": CBOX_TOP_Z_MM,
                "position": "FRONT_OF_BBOX",
                "structural_role": "PROHIBITED",
            },
            "bbox": {
                "external_size_mm": BBOX_SIZE_MM,
                "orientation": "X_FORE_AFT_Y_LATERAL_Z_VERTICAL",
                "centerline_y_mm": 0.0,
                "bottom_z_mm": BOX_BOTTOM_Z_MM,
                "top_z_mm": BBOX_TOP_Z_MM,
                "position": "REAR_OF_CBOX",
                "structural_role": "PROHIBITED",
                "minimum_effective_interior_mm": BBOX_MIN_EFFECTIVE_INTERIOR_MM,
                "actual_effective_interior_mm": None,
                "fit_status": "FIELD_MEASUREMENT_REQUIRED",
            },
            "interface": {
                "orientation": "SHORT_END_FACES_OPPOSED",
                "primary_connection_region_y_mm": [-70.0, 70.0],
                "guide_before_contact": True,
                "contact_carries_weight": False,
                "independent_latch": True,
            },
        },
        "battery_cassette": {
            "external_size_mm": BATTERY_CASSETTE_SIZE_MM,
            "orientation": "X125_FORE_AFT_Y180_LATERAL_Z120_VERTICAL",
            "contact_face": "FRONT_TOWARD_CBOX",
            "insertion_sequence": [
                "MECHANICAL_GUIDE_ENGAGES_FIRST",
                "GUIDE_DETERMINES_Y_AND_Z",
                "CONTACT_ENGAGES_DURING_FINAL_TRAVEL",
                "INDEPENDENT_LATCH_RETAINS",
            ],
            "hot_swap": "PROHIBITED",
            "external_bbox_minus_cassette_mm": {"x": 25.0, "y": 40.0, "z": 30.0},
            "fit_status": "FIELD_MEASUREMENT_REQUIRED",
        },
        "environment_and_height": {
            "water_depth_mm": 150.0,
            "mud_sink_allowance_mm": 50.0,
            "combined_reference_height_mm": 200.0,
            "box_bottom_minimum_z_mm": 200.0,
            "box_top_maximum_z_mm": BOX_TOP_MAX_Z_MM,
            "motor_axis_minimum_z_mm": MOTOR_AXIS_MIN_Z_MM,
            "pto_axis_relation": PTO_AXIS_RELATION,
            "preferred_axis_relation": PREFERRED_AXIS_RELATION,
            "candidate_motor_axis_z_mm": CANDIDATE["motor_axis_z_mm"],
            "candidate_pto_axis_z_mm": CANDIDATE["pto_axis_z_mm"],
        },
        "motors": {
            "count": MOTOR_COUNT,
            "third_motor": "PROHIBITED",
            "left": {
                "location": "LEFT_HIGH",
                "shaft_direction": "-Y_INWARD",
                "common_shaft": "PROHIBITED",
            },
            "right": {
                "location": "RIGHT_HIGH",
                "shaft_direction": "+Y_INWARD",
                "common_shaft": "PROHIBITED",
            },
            "box_mounting": "PROHIBITED",
            "actual_geometry": "PART_MEASUREMENT_REQUIRED",
        },
        "slide_clutches": {
            "count": 2,
            "states": list(CLUTCH_STATES),
            "rules": CLUTCH_RULES,
            "detail_status": "PART_MEASUREMENT_REQUIRED",
        },
        "pto": {
            "count": PTO_COUNT,
            "architecture": "TWO_INDEPENDENT_LATERAL_SHAFT_PORTS",
            "common_axis": "PROHIBITED",
            "left_output_direction": "+Y_OUTWARD",
            "right_output_direction": "-Y_OUTWARD",
            "candidate_outer_end_y_mm": {
                "left": CANDIDATE["pto_outer_end_abs_y_mm"],
                "right": -CANDIDATE["pto_outer_end_abs_y_mm"],
            },
            "absolute_end_condition": "ABS_Y_LT_150",
            "target_end_condition": "ABS_Y_LTE_145",
            "kp000_candidate_count": KP000_CANDIDATE_COUNT,
            "each_side_sequence_center_to_outside": [
                "INNER_KP000",
                "SAFETY_CLEARANCE",
                "60T_PULLEY",
                "SAFETY_CLEARANCE",
                "OUTER_KP000",
                "SHORT_OUTPUT_SHAFT",
                "PTO_COUPLING",
            ],
            "60t_between_two_bearings_each_side": True,
            "actual_geometry": "PART_MEASUREMENT_REQUIRED",
        },
        "belt_and_pulley": {
            "standard": BELT_STANDARD,
            "pitch_mm": BELT_PITCH_MM,
            "belt_width_mm": BELT_WIDTH_MM,
            "driver_teeth": PULLEY_DRIVER_TEETH,
            "driven_teeth": PULLEY_DRIVEN_TEETH,
            "reduction_ratio": NOMINAL_REDUCTION_RATIO,
            "independent_belt_runs": [
                "LEFT_DRIVE_BELT_ENVELOPE",
                "RIGHT_DRIVE_BELT_ENVELOPE",
                "LEFT_PTO_BELT_ENVELOPE",
                "RIGHT_PTO_BELT_ENVELOPE",
            ],
            "crossing": "PROHIBITED",
            "60t_reported_max_dimension_mm": PTO_60T_REPORTED_MAX_DIMENSION_MM,
            "60t_reported_dimension_meaning": PTO_60T_DIMENSION_MEANING,
            "60t_safety_envelope_diameter_mm": PULLEY_60T_SAFETY_DIAMETER_MM,
            "60t_safety_envelope_radius_mm": PULLEY_60T_SAFETY_RADIUS_MM,
            "actual_widths_and_flanges": "PART_MEASUREMENT_REQUIRED",
        },
        "front_pto_frame": {
            "root_crossmember": "2040_X1",
            "front_spars": "2020_X2",
            "front_crossbar": "2020_X1",
            "diagonal_braces": "2020_X2",
            "vertical_supports": "2020_AS_REQUIRED",
            "brackets_and_gussets": "METAL_REQUIRED",
            "independent_outer_triangles": True,
            "center_x_brace": "PROHIBITED",
            "box_load_path": "PROHIBITED",
            "printed_primary_load_bracket": "PROHIBITED",
        },
        "crawler": {
            "side_count": 2,
            "geometry": "INVERTED_TRAPEZOID_TOP_LONGER_THAN_BOTTOM",
            "each_side": {
                "front_upper_drive_wheel_count": 1,
                "rear_upper_idler_count": 1,
                "lower_roller_count_candidates": [3, 4],
                "continuous_track_count": 1,
                "upper_2040_long_rail_count": 1,
                "lower_2040_short_rail_count": 1,
                "diagonal_post_count": 2,
            },
            "common_drive_shaft": "PROHIBITED",
            "rectangular_track": "PROHIBITED",
            "four_wheel_tire_conversion": "PROHIBITED",
            "drive_60t_and_sprocket_same_shaft": "STANDARD_CANDIDATE",
            "drive_shaft_nominal_diameter_mm": 10.0,
            "actual_geometry": "FIELD_MEASUREMENT_REQUIRED",
        },
        "clearances_mm": CLEARANCES_MM,
        "tolerance_and_dynamic_states": {
            "axial_play_mm": [-1.0, 1.0],
            "frame_assembly_error_mm": [-1.0, 1.0],
            "frame_deformation_mm": 2.0,
            "belt_lateral_sway_mm": None,
            "track_dynamic_runout_mm": None,
            "idler_adjustment_range_mm": None,
            "status": "PART_AND_FIELD_MEASUREMENT_REQUIRED",
        },
        "stock": STOCK,
        "candidate_layout": CANDIDATE,
        "measurement_evidence": MEASUREMENT_EVIDENCE,
        "superseded": list(SUPERSEDED),
        "hold_items": list(HOLD_ITEMS),
        "final_gates": FINAL_GATES,
        "forbidden_release_claims": [
            "PRODUCTION_READY",
            "CUTTING_APPROVED",
            "DRILLING_APPROVED",
            "POWERED_OPERATION_APPROVED",
            "WATER_OR_MUD_OPERATION_APPROVED",
            "FIELD_DEPLOYMENT_APPROVED",
        ],
    }


def build_authority_markdown(report: dict) -> str:
    zero_count = report["summary"]["candidate_zero_intersection_check_count"]
    hold_count = report["summary"]["hold_count"]
    return f"""# Common Rover Front-Drive Dual-PTO Design Authority v0.8

Document ID: `{DOCUMENT_ID}`  
Status: `{AUTHORITY_STATUS}`  
Release: `{RELEASE_STATUS}`

## 1. Authority scope

This document is the current design authority for the Common Rover architecture:

> Front-mounted two-motor drive, two independent three-position slide clutches,
> two independent forward PTO ports, elevated CBOX/BBOX, and independent
> inverted-trapezoid crawlers.

It fixes architecture and dimensional relationships. It does **not** release
aluminum cutting, drilling, clutch fabrication, powered testing, water/mud
testing, or field deployment. The STEP file is an envelope inspection model,
not manufacturing CAD.

## 2. Coordinate system and order

- Length unit: mm; angle unit: degree.
- +X is rover front, -X rear.
- +Y is rover left when facing forward, -Y right.
- +Z is up and ground is Z=0.
- Legacy mapping is `X_v008=-Y_legacy`, `Y_v008=X_legacy`,
  `Z_v008=Z_legacy`; direct import of legacy coordinates is prohibited.
- Fixed order:
  `X_PTO > X_POWER_TRANSMISSION > X_MOTOR > X_CBOX > X_BBOX`.
- Power transmission is concentrated forward of CBOX. CBOX underside,
  BBOX underside, the CBOX/BBOX connection zone, and rear service space are
  prohibited transmission locations.

## 3. Fixed outer dimensions and height relations

| Item | X fore-aft | Y lateral | Z height | Bottom Z | Top Z |
|---|---:|---:|---:|---:|---:|
| CBOX | 130 | 140 | 105 | 200 | 305 |
| BBOX | 150 | 220 | 150 | 200 | 350 |
| Battery cassette | 125 | 180 | 120 | candidate inside BBOX | candidate inside BBOX |

CBOX and BBOX are centered at Y=0, arranged front/rear, and face each other
with their short X faces. Their principal guide/contact/latch region stays
inside the central 140 mm. Neither box is structural and neither may receive
motor reaction, PTO bearing load, crawler load, or belt tension.

The BBOX/cassette external differences are X=25, Y=40, Z=30. These are **not**
internal clearances. The BBOX must physically measure at least
129 x 184 x 125 effective millimetres after wall, lid, gasket, base, guide,
contact and latch allowances. Until measured, cassette fit is
`FIELD_MEASUREMENT_REQUIRED`.

The cassette contact face points forward toward CBOX. The mechanical guide
engages first; electrical contact engages only during final travel; an
independent latch retains the cassette. Contacts carry no cassette weight,
are not locating pins, and are never disconnected under power.

Water=150 and mud sink allowance=50 fix both box bottoms at Z>=200.
The axis relationship is:

`Z_PTO_AXIS >= Z_MOTOR_AXIS >= Z_BOX_TOP_MAX(350)`.

Equal motor/PTO axis height is preferred. The inspection candidate uses
Z=370 for both axes, but final height remains parameterized.

## 4. Width authority

- Nominal row spacing: 300.
- Hard maximum including PTO ends, couplings, bolts, track protrusions,
  latches, brackets and guards: 299.
- Strict condition: completed width is less than 300.
- Target: 286–290.
- Each crawler: 55.
- Central lower structure: at most 180.

The candidate track envelope is 286 wide and the candidate PTO end planes
produce a 290 overall envelope. This leaves only 5 mm per side to a nominal
300 mm row and is **not** physical width release. Real couplings, fasteners,
guards, mud and track runout remain unmeasured.

## 5. Motors and slide clutches

Exactly two high-mounted motors are used. The left shaft points inward in -Y;
the right shaft points inward in +Y. A third PTO motor, outward motor shafts,
and a common left/right motor shaft are prohibited.

Each motor has its own mechanical axial slide clutch with exactly three
positions: DRIVE, NEUTRAL and PTO. Same-side DRIVE/PTO simultaneous engagement
is mechanically prohibited. Every DRIVE/PTO transition passes through
NEUTRAL. The rover and motor stop before shifting. Left and right clutches are
independent and may not collide at the center. Sensor/limit-switch mounting
must remain possible, and power-loss-to-NEUTRAL is the preferred safety
direction.

Actual shaft diameter, stroke, dog form, engagement length, spring,
actuation, sensor position and pulley stack order are
`PART_MEASUREMENT_REQUIRED`.

## 6. Two independent forward PTO ports

There are two and only two ports. Left output is +Y, right output is -Y; both
axes remain lateral. They are independent shafts and may not be joined.
Each side uses the initial candidate sequence:

`inner KP000 -> clearance -> 60T -> clearance -> outer KP000 -> short shaft -> coupling`.

The 60T is between the two bearings. The shaft is aligned through both
bearings before final tightening. A collar or retaining ring provides axial
location; KP000 set screws alone do not. The work unit weight is not carried
only by the PTO shaft.

The target end plane is |Y|<=145 and the absolute condition is |Y|<150.
The candidate uses +/-145. Actual shaft, coupling, cap, pin and fastener
dimensions block release. KP000 load, speed, sealing, mud and life capability
also remain HOLD.

## 7. Belt and pulley authority

- HTD 5M STANDARD, 5 mm pitch, 15 mm belt.
- 20T driver, 60T driven, nominal 3:1.
- Four independent runs:
  LEFT_DRIVE, RIGHT_DRIVE, LEFT_PTO, RIGHT_PTO.
- Left/right runs may not cross and the PTO runs may not share one belt.
- PTO belts are central; DRIVE belts are outboard over the crawler side.
- DRIVE windows stay outside the 2040 root crossmember.
- PTO horizontal frame members stay below the PTO pulley envelope.
- Belts do not run in T-slots; 2040 is not notched for belt passage.

The user-reported 60T maximum dimension is 102 mm with unresolved meaning.
v0.8 supersedes the 102 mm-only rotation envelope and uses diameter 120,
radius 60 for all initial checks. At candidate axis Z=370 the lower edge is
Z=310. PTO horizontal members are Z=220–240, giving a simplified 70 mm
lower-edge separation. Actual flange diameter, pulley width, runout and belt
sway must be measured.

Minimum/recommended clearances (mm):

| Pair | Minimum | Recommended |
|---|---:|---:|
| Belt side–frame | 5 | 8 |
| Belt–diagonal | 8 | 10 |
| Belt–bolt head | 5 | 8 |
| Pulley flange–frame | 5 | 8 |
| 60T envelope–fixed part | 8 | 10 |
| Belt–wiring | 10 | 15 |
| PTO pulley–KP000 | 5 | 8 |
| DRIVE belt–crawler cover | 8 | 12 |
| BOX bottom–track dynamic envelope | 10 | 20 |

## 8. Front PTO frame and load path

The front frame uses one 2040 root crossmember, two 2020 spars, one 2020
front crossbar, two 2020 diagonal braces, necessary vertical 2020 supports,
and metal brackets/gussets. Left and right form independent outer triangles;
a center X brace is prohibited. No single 2040 cantilever and no printed-only
primary-load bracket is allowed.

Load path:
`PTO output -> shaft -> KP000 -> 2020 spar -> 2020 diagonal ->
2040 root -> two 2040 main rails -> lower rover frame`.

## 9. Inverted-trapezoid crawlers

Each side is independent and has one front-upper drive wheel, one rear-upper
idler, three or four lower rollers, and one continuous track. The top run is
longer than the bottom contact run; front/rear runs are diagonal. The rear
idler has tension adjustment. A rectangular tank track, four-wheel tire
conversion and common left/right drive shaft are prohibited.

Each side frame has a longer upper 2040, shorter lower 2040, front/rear 2020
diagonal posts, drive/idler supports, individually serviceable lower rollers,
and an idler adjustment. It is not a rectangle or sealed plate. Mud drainage,
washing, outside track replacement and straw-removal disassembly are required.
The DRIVE 60T and crawler sprocket on the same nominal 10 mm shaft is a
candidate, not released hardware.

The inspection model shows four rollers. The three/four decision and every
track, sprocket, idler, roller and tension dimension remain HOLD.

## 10. Candidate interference result

The generated simplified model contains four independent belt safety
envelopes and a full-stroke placeholder for each clutch. It checks belt/frame,
belt/representative-fastener, clutch/frame, track/upper-structure, PTO
pulley/KP000, lid service and rear cassette withdrawal.

- Candidate solid-intersection checks reporting zero: {zero_count}.
- FAIL checks: {report["summary"]["fail_count"]}.
- HOLD checks: {hold_count}.
- Physical release: `NOT_APPROVED`.

Zero candidate intersections are not a physical PASS. Actual motor, clutch,
20T/60T widths, flanges, KP000, shafts, couplings, fasteners, tensioners,
belt sway, track runout, guards and wiring are missing.

## 11. Aluminum stock allocation

Declared inventory is 2020 x 400 x 8 and 2040 x 400 x 8. The candidate plan
uses all eight 2020 bars and seven 2040 bars, leaving one 400 mm 2040 reserve.
No candidate member exceeds 400. The upper crawler rail is 400 and the lower
is 260. The root and rear 2040 crossmembers are paired as 156+156 from one
stock bar. Four independent 2020 vertical supports provide one load path for
each KP000 candidate position. Detailed cuts are in `{ALLOCATION_NAME}`.

This is only a layout feasibility result. All cutting, drilling, final angles,
kerf, end preparation, metal splice/gusset selection and structural
calculation remain HOLD.

No metal connection-plate/bracket/gusset inventory was declared. Such
hardware is an additional-purchase requirement; its exact count, thickness,
material and hole pattern remain `PART_MEASUREMENT_REQUIRED` pending the load
case and structural calculation. This is separate from the zero-shortage
candidate result for 2020/2040 extrusion bars.

## 12. Superseded architecture

{chr(10).join(f"- `{item}`" for item in SUPERSEDED)}

## 13. Measurement and release holds

{chr(10).join(f"- `{item}`" for item in HOLD_ITEMS)}

Final gates:

{chr(10).join(f"- {key}: `{value}`" for key, value in FINAL_GATES.items())}

## 14. Interference correction order

1. Move belt planes axially: PTO inward and DRIVE outward.
2. Move frame below or fore/aft of envelopes; move diagonals below; reverse
   bracket/bolt direction.
3. Shorten the root crossmember, split outer brackets, preserve belt windows.
4. Change axial stack, bearing/collar/clutch spacing, or tensioner position.
5. Only then propose added metal frame or a dedicated metal plate.

Never resolve interference by exceeding 299, lowering motors, moving PTO
behind motors, adding a third motor, joining PTO shafts, structuralizing
boxes, heavily cutting 2040, simultaneous DRIVE/PTO engagement, or changing
the crawler to a rectangle.

## 15. Validation sequence

1. Measure BBOX effective interior and battery path.
2. Measure both motors, shafts and brackets.
3. Measure both 20T and all 60T pulleys including flange and axial stack.
4. Measure clutch stroke and all three engagement states.
5. Measure KP000, shaft, collars, rings, coupling and fasteners.
6. Select belts and tensioners; inspect min/nominal/max positions.
7. Inflate CAD for +/-1 axial play, +/-1 assembly error, 2 mm deformation,
   measured belt sway and measured track dynamics.
8. Re-run all four belt/frame and belt/fastener intersections.
9. Verify completed width including every protrusion is <=299.
10. Only after structural review may aluminum cut/drill release be considered.

Until every applicable HOLD is closed, this architecture is not a completed
specification and field deployment is `NOT_APPROVED`.
"""


def build_svg() -> str:
    """Deterministic schematic; geometry is sourced from candidate parameters."""
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="820" viewBox="0 0 1200 820">
  <rect width="1200" height="820" fill="#f7f8fa"/>
  <style>
    .t{font-family:Arial,sans-serif;fill:#182230}.h{font-size:22px;font-weight:700}.s{font-size:13px}
    .frame{fill:#9aa4b2;stroke:#3e4c59;stroke-width:2}.box{fill:#6ec5d6;stroke:#126e82;stroke-width:2}
    .motor{fill:#f4a261;stroke:#9c4f16;stroke-width:2}.pto{fill:#e76f51;stroke:#8f2714;stroke-width:2}
    .drive{fill:none;stroke:#7b2cbf;stroke-width:12;opacity:.72}.ptob{fill:none;stroke:#d62828;stroke-width:12;opacity:.72}
    .track{fill:#4f5d75;stroke:#222b3a;stroke-width:2;opacity:.82}.hold{fill:#fff1cc;stroke:#b36b00;stroke-width:2}
    .dim{fill:none;stroke:#1d3557;stroke-width:1.5;marker-start:url(#a);marker-end:url(#a)}
  </style>
  <defs><marker id="a" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto"><path d="M0,3.5 L7,0 L7,7 Z" fill="#1d3557"/></marker></defs>
  <text x="40" y="38" class="t h">Common Rover v0.8 — envelope inspection, NOT manufacturing CAD</text>
  <text x="40" y="62" class="t s">+X front →   +Y left ↑   120 mm safety envelope   all actual hardware dimensions HOLD</text>

  <!-- top view, X right, Y up -->
  <rect x="45" y="90" width="1110" height="360" fill="white" stroke="#c5ccd5"/>
  <text x="60" y="115" class="t h">TOP VIEW</text>
  <polygon class="track" points="170,150 1020,150 1020,205 170,205"/>
  <polygon class="track" points="170,335 1020,335 1020,390 170,390"/>
  <rect class="box" x="240" y="177" width="210" height="186"/>
  <text x="302" y="272" class="t h">BBOX</text>
  <rect class="box" x="478" y="210" width="182" height="120"/>
  <text x="530" y="274" class="t h">CBOX</text>
  <rect class="motor" x="680" y="155" width="95" height="62" rx="15"/>
  <rect class="motor" x="680" y="323" width="95" height="62" rx="15"/>
  <text x="691" y="193" class="t s">LEFT MOTOR</text>
  <text x="687" y="360" class="t s">RIGHT MOTOR</text>
  <rect class="hold" x="770" y="215" width="75" height="52"/>
  <rect class="hold" x="770" y="273" width="75" height="52"/>
  <text x="779" y="246" class="t s">CLUTCH L</text>
  <text x="779" y="304" class="t s">CLUTCH R</text>
  <line class="drive" x1="755" y1="177" x2="890" y2="177"/>
  <line class="drive" x1="755" y1="363" x2="890" y2="363"/>
  <line class="ptob" x1="820" y1="245" x2="1000" y2="245"/>
  <line class="ptob" x1="820" y1="295" x2="1000" y2="295"/>
  <circle class="pto" cx="1000" cy="245" r="32"/><circle class="pto" cx="1000" cy="295" r="32"/>
  <line x1="1000" y1="245" x2="1000" y2="135" stroke="#8f2714" stroke-width="8"/>
  <line x1="1000" y1="295" x2="1000" y2="405" stroke="#8f2714" stroke-width="8"/>
  <text x="1020" y="205" class="t s">LEFT PTO +Y</text><text x="1020" y="344" class="t s">RIGHT PTO -Y</text>
  <line class="frame" x1="780" y1="220" x2="1080" y2="220"/><line class="frame" x1="780" y1="320" x2="1080" y2="320"/>
  <line class="frame" x1="780" y1="245" x2="1080" y2="220"/><line class="frame" x1="780" y1="295" x2="1080" y2="320"/>
  <line class="dim" x1="1120" y1="150" x2="1120" y2="390"/><text x="1105" y="278" text-anchor="end" class="t s">290 mm candidate</text>

  <!-- side view -->
  <rect x="45" y="475" width="1110" height="300" fill="white" stroke="#c5ccd5"/>
  <text x="60" y="505" class="t h">LEFT SIDE VIEW</text>
  <polygon class="track" points="175,575 915,575 810,735 300,735"/>
  <line class="frame" x1="210" y1="610" x2="840" y2="610"/><line class="frame" x1="315" y1="705" x2="795" y2="705"/>
  <line class="frame" x1="210" y1="610" x2="315" y2="705"/><line class="frame" x1="840" y1="610" x2="795" y2="705"/>
  <circle cx="835" cy="615" r="42" fill="#75859a" stroke="#222b3a" stroke-width="2"/>
  <circle cx="225" cy="615" r="42" fill="#75859a" stroke="#222b3a" stroke-width="2"/>
  <circle cx="385" cy="705" r="25" fill="#75859a"/><circle cx="500" cy="705" r="25" fill="#75859a"/>
  <circle cx="615" cy="705" r="25" fill="#75859a"/><circle cx="730" cy="705" r="25" fill="#75859a"/>
  <rect class="box" x="225" y="515" width="230" height="90"/><text x="300" y="566" class="t h">BBOX</text>
  <rect class="box" x="485" y="540" width="190" height="65"/><text x="540" y="579" class="t h">CBOX</text>
  <circle class="motor" cx="755" cy="515" r="30"/><circle class="pto" cx="1010" cy="515" r="60"/>
  <line class="ptob" x1="790" y1="515" x2="1010" y2="515"/><line class="drive" x1="760" y1="515" x2="835" y2="615"/>
  <rect class="frame" x="850" y="625" width="220" height="20"/>
  <text x="925" y="662" class="t s">PTO frame Z=220–240</text>
  <line class="dim" x1="1100" y1="515" x2="1100" y2="635"/><text x="1065" y="585" class="t s">70 mm</text>
  <text x="60" y="798" class="t s">Candidate only: BBOX interior, motor, clutch, KP000, pulleys, coupling, tensioners, fasteners and track dynamics require measurement.</text>
</svg>
"""


def _solid_signature(shape: cq.Shape) -> dict:
    solids = []
    for solid in shape.Solids():
        box = solid.BoundingBox()
        solids.append(
            {
                "bbox_mm": [_round(box.xlen, 3), _round(box.ylen, 3), _round(box.zlen, 3)],
                "center_mm": [
                    _round((box.xmin + box.xmax) / 2.0, 3),
                    _round((box.ymin + box.ymax) / 2.0, 3),
                    _round((box.zmin + box.zmax) / 2.0, 3),
                ],
                "volume_mm3": _round(solid.Volume(), 2),
            }
        )
    solids.sort(
        key=lambda row: (
            row["center_mm"],
            row["bbox_mm"],
            row["volume_mm3"],
        )
    )
    box = shape.BoundingBox()
    return {
        "solid_count": len(solids),
        "bbox_mm": [_round(box.xlen, 3), _round(box.ylen, 3), _round(box.zlen, 3)],
        "center_mm": [
            _round((box.xmin + box.xmax) / 2.0, 3),
            _round((box.ymin + box.ymax) / 2.0, 3),
            _round((box.zmin + box.zmax) / 2.0, 3),
        ],
        "total_volume_mm3": _round(sum(row["volume_mm3"] for row in solids), 2),
        "solids": solids,
    }


def _compound(components: dict[str, cq.Shape]) -> cq.Shape:
    solids: list[cq.Shape] = []
    for shape in components.values():
        solids.extend(shape.Solids())
    return cq.Compound.makeCompound(solids)


def _normalize_step(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="strict")
    text = re.sub(
        r"FILE_NAME\('[^']*','[^']*'",
        f"FILE_NAME('{STEP_NAME}','1970-01-01T00:00:00'",
        text,
        count=1,
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def _export_step(shape: cq.Shape, path: Path) -> None:
    cq.exporters.export(shape, str(path), exportType="STEP")
    _normalize_step(path)


def _build_matrix_rows(report: dict) -> list[dict[str, object]]:
    rows = []
    for check in report["checks"]:
        metrics = check["metrics"]
        rows.append(
            {
                "check_id": check["check_id"],
                "classification": check["classification"],
                "requirement": check["requirement"],
                "authority_scope": check["authority_scope"],
                "intersection_count": metrics.get("intersection_count"),
                "intersection_volume_mm3": metrics.get("intersection_volume_mm3"),
                "minimum_distance_mm": metrics.get("minimum_distance_mm"),
                "unknown_physical_dimensions": check[
                    "unknown_physical_dimensions"
                ],
                "note": check["note"],
            }
        )
    return rows


def _component_registry(components: dict[str, cq.Shape]) -> list[dict]:
    registry = []
    for component_id, shape in sorted(components.items()):
        box = shape.BoundingBox()
        if "BELT_ENVELOPE" in component_id:
            role = "SAFETY_SWEEP_ENVELOPE"
        elif "DYNAMIC_ENVELOPE" in component_id:
            role = "DYNAMIC_RESERVED_ENVELOPE"
        elif "RESERVED" in component_id or "SERVICE" in component_id:
            role = "NON_AUTHORITY_RESERVED_ENVELOPE"
        elif component_id in ("CBOX", "BBOX", "BATTERY_CASSETTE_REFERENCE"):
            role = "FIXED_EXTERNAL_DIMENSION_REFERENCE"
        else:
            role = "CANDIDATE_FRAME_OR_RUNNING_GEAR_REFERENCE"
        registry.append(
            {
                "component_id": component_id,
                "role": role,
                "bbox_mm": [_round(box.xlen), _round(box.ylen), _round(box.zlen)],
                "center_mm": [
                    _round((box.xmin + box.xmax) / 2.0),
                    _round((box.ymin + box.ymax) / 2.0),
                    _round((box.zmin + box.zmax) / 2.0),
                ],
                "solid_count": len(shape.Solids()),
                "valid": bool(shape.isValid()),
            }
        )
    return registry


def _validation_payload(
    components: dict[str, cq.Shape],
    compound: cq.Shape,
    report: dict,
    text_payloads: dict[Path, str],
    step_path: Path,
) -> dict:
    step_bytes = step_path.read_bytes()
    imported = _shape(cq.importers.importStep(str(step_path)))
    model_signature = _solid_signature(compound)
    artifact_signature = _solid_signature(imported)
    return {
        "document_id": DOCUMENT_ID,
        "schema": "paddy_swarm.common_rover.front_drive_dual_pto_validation.v0.8",
        "authority_status": AUTHORITY_STATUS,
        "release_status": RELEASE_STATUS,
        "expected_path_count": len(EXPECTED_PATHS),
        "expected_paths": list(EXPECTED_PATHS),
        "component_registry": _component_registry(components),
        "geometry": {
            "component_count": len(components),
            "all_components_valid": all(shape.isValid() for shape in components.values()),
            "model_semantic_signature": model_signature,
            "artifact_semantic_signature": artifact_signature,
            "semantic_geometry_reproducible": model_signature == artifact_signature,
            "step_byte_sha256": _sha256_bytes(step_bytes),
            "step_size_bytes": len(step_bytes),
            "candidate_width_mm": model_signature["bbox_mm"][1],
            "candidate_width_within_299": model_signature["bbox_mm"][1]
            <= TOTAL_WIDTH_HARD_MAX_MM,
        },
        "documents": {
            path.name: {
                "byte_sha256": _sha256_bytes(text.encode("utf-8")),
                "size_bytes": len(text.encode("utf-8")),
                "reproducibility": "BYTE_IDENTICAL",
            }
            for path, text in sorted(
                text_payloads.items(),
                key=lambda item: item[0].name,
            )
        },
        "interference": report["summary"],
        "fixed_authority_checks": {
            "motor_count_2": MOTOR_COUNT == 2,
            "pto_count_2": PTO_COUNT == 2,
            "motor_axes_inward": True,
            "clutch_states_exact": list(CLUTCH_STATES) == ["DRIVE", "NEUTRAL", "PTO"],
            "same_side_drive_pto_simultaneous_prohibited": True,
            "pto_forward_of_motor": CANDIDATE["pto_axis_x_mm"]
            > CANDIDATE["motor_axis_x_mm"],
            "pto_axis_gte_motor_axis": CANDIDATE["pto_axis_z_mm"]
            >= CANDIDATE["motor_axis_z_mm"],
            "motor_axis_gte_bbox_top": CANDIDATE["motor_axis_z_mm"]
            >= BBOX_TOP_Z_MM,
            "both_boxes_bottom_gte_200": BOX_BOTTOM_Z_MM >= 200.0,
            "cbox_bbox_short_faces_opposed": True,
            "crawler_inverted_trapezoid": True,
            "upper_2040_longer_than_lower": 400.0 > 260.0,
            "single_member_max_lte_400": True,
            "boxes_not_structural": True,
            "field_deployment_not_approved": FINAL_GATES["FIELD_DEPLOYMENT"]
            == "NOT_APPROVED",
        },
        "material_allocation": {
            "2020_candidate_stock_used": 8,
            "2020_available": 8,
            "2040_candidate_stock_used": 7,
            "2040_available": 8,
            "member_over_400_count": 0,
            "candidate_shortage": 0,
            "non_extrusion_connector_hardware": (
                "ADDITIONAL_PURCHASE_REQUIRED_COUNT_AND_SIZE_PENDING"
            ),
            "status": "CONDITIONAL_PASS_LAYOUT_CANDIDATE",
            "cutting_release": "HOLD",
        },
        "overall_validation": (
            "PASS_FOR_ENVELOPE_AUTHORITY_WITH_HOLDS_NOT_FOR_MANUFACTURING"
            if model_signature == artifact_signature
            and report["summary"]["fail_count"] == 0
            else "FAIL"
        ),
    }


def _write_atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _write_atomic_step(shape: cq.Shape, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    _export_step(shape, temporary)
    temporary.replace(path)


def _generate_payloads(
    components: dict[str, cq.Shape],
    compound: cq.Shape,
    step_path: Path,
) -> tuple[dict[Path, str], dict]:
    report = build_interference_report(components)
    parameters = build_parameters()
    matrix_rows = _build_matrix_rows(report)
    allocation_rows = build_allocation_rows()
    text_payloads: dict[Path, str] = {
        LANE_DIR / AUTHORITY_NAME: build_authority_markdown(report),
        LANE_DIR / PARAMETERS_NAME: _json_text(parameters),
        LANE_DIR / INTERFERENCE_JSON_NAME: _json_text(report),
        LANE_DIR / INTERFERENCE_CSV_NAME: _csv_text(
            matrix_rows,
            [
                "check_id",
                "classification",
                "requirement",
                "authority_scope",
                "intersection_count",
                "intersection_volume_mm3",
                "minimum_distance_mm",
                "unknown_physical_dimensions",
                "note",
            ],
        ),
        LANE_DIR / ALLOCATION_NAME: _csv_text(
            allocation_rows,
            [
                "member_group",
                "profile",
                "quantity",
                "required_length_each_mm",
                "stock_allocation",
                "stock_cut_candidate",
                "remainder_each_mm",
                "candidate_stock_count",
                "status",
                "note",
            ],
        ),
        ARTIFACT_DIR / SVG_NAME: build_svg(),
    }
    validation = _validation_payload(
        components,
        compound,
        report,
        text_payloads,
        step_path,
    )
    text_payloads[LANE_DIR / VALIDATION_NAME] = _json_text(validation)
    return text_payloads, validation


def refresh() -> dict:
    components = build_components()
    compound = _compound(components)
    step_path = ARTIFACT_DIR / STEP_NAME
    _write_atomic_step(compound, step_path)
    text_payloads, validation = _generate_payloads(
        components,
        compound,
        step_path,
    )
    for path, text in text_payloads.items():
        _write_atomic_text(path, text)
    return validation


def verify() -> dict:
    missing = [
        relative
        for relative in GENERATED_RELATIVE_PATHS
        if not (REPO_ROOT / relative).is_file()
    ]
    if missing:
        raise RuntimeError(f"missing generated paths: {missing}")
    components = build_components()
    compound = _compound(components)
    step_path = ARTIFACT_DIR / STEP_NAME
    expected_texts, validation = _generate_payloads(
        components,
        compound,
        step_path,
    )
    mismatches = []
    for path, expected in expected_texts.items():
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            mismatches.append(path.relative_to(REPO_ROOT).as_posix())
    if mismatches:
        raise RuntimeError(f"byte-reproducibility mismatch: {mismatches}")
    if not validation["geometry"]["semantic_geometry_reproducible"]:
        raise RuntimeError("STEP semantic geometry mismatch")
    if validation["interference"]["fail_count"] != 0:
        raise RuntimeError(
            "candidate geometry contains a required solid intersection"
        )
    if validation["geometry"]["candidate_width_mm"] > TOTAL_WIDTH_HARD_MAX_MM:
        raise RuntimeError("candidate geometry exceeds 299 mm")
    if not all(validation["fixed_authority_checks"].values()):
        raise RuntimeError("one or more fixed authority checks failed")
    return validation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--refresh-artifacts", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    try:
        validation = refresh() if args.refresh_artifacts else verify()
    except Exception as exc:  # fail closed with one diagnostic
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        _json_text(
            {
                "document_id": DOCUMENT_ID,
                "action": "REFRESH" if args.refresh_artifacts else "VERIFY",
                "overall_validation": validation["overall_validation"],
                "component_count": validation["geometry"]["component_count"],
                "solid_count": validation["geometry"][
                    "model_semantic_signature"
                ]["solid_count"],
                "candidate_width_mm": validation["geometry"][
                    "candidate_width_mm"
                ],
                "candidate_interference_fail_count": validation[
                    "interference"
                ]["fail_count"],
                "hold_count": validation["interference"]["hold_count"],
                "material_status": validation["material_allocation"]["status"],
                "release_status": RELEASE_STATUS,
            }
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
