#!/usr/bin/env python3
"""Independent-shaft, no-load dry-fit jig geometry for Common Rover v0.9.2.1."""

from __future__ import annotations

from typing import Any

import cadquery as cq


AXIS_X_MM = 150.0
AXIS_Z_MM = 320.0
LEFT_FACE_Y_MM = 30.5
RIGHT_FACE_Y_MM = -30.5
LEFT_SHAFT_END_Y_MM = 18.0
RIGHT_SHAFT_END_Y_MM = -18.0
STUB_LENGTH_MM = 12.5
CENTER_GAP_MM = 36.0
SHAFT_DIAMETER_MM = 10.0
SHAFT_STOCK_LENGTH_MM = 300.0
SLEEVE_OD_MM = 20.0
SLEEVE_BODY_LENGTH_MM = 25.0
SLEEVE_MOVING_LENGTH_MM = 10.0
SLEEVE_STROKE_MM = 10.0
ENGAGEMENT_REFERENCE_MM = 8.0
DUMMY_BORE_DIAMETER_MM = 11.2

DRY_FIT_STATES = (
    "DF0_PARTS",
    "DF1_SHAFTS_POSITIONED",
    "DF2_SLEEVES_RETRACTED",
    "DF3_UNIT_INSERTING",
    "DF4_UNIT_LOCKED",
    "DF5_PARTIAL",
    "DF6_ENGAGED",
    "DF7_DISENGAGING",
    "DF8_REMOVABLE",
)


def box(
    x_size: float,
    y_size: float,
    z_size: float,
    center: tuple[float, float, float],
) -> cq.Shape:
    return (
        cq.Workplane("XY").box(x_size, y_size, z_size)
        .translate(cq.Vector(*center)).val()
    )


def cylinder_y(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Shape:
    x, y, z = center
    return cq.Solid.makeCylinder(
        radius,
        length,
        cq.Vector(x, y - length / 2.0, z),
        cq.Vector(0.0, 1.0, 0.0),
    )


def annulus_y(
    outer_radius: float,
    inner_radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Shape:
    return cylinder_y(outer_radius, length, center).cut(
        cylinder_y(inner_radius, length + 2.0, center)
    )


def shaft_positioning_block(side: str) -> cq.Shape:
    sign = 1.0 if side == "LEFT" else -1.0
    center_y = sign * 36.5
    base = box(38.0, 12.0, 32.0, (AXIS_X_MM, center_y, AXIS_Z_MM))
    bore = cylinder_y(
        DUMMY_BORE_DIAMETER_MM / 2.0,
        16.0,
        (AXIS_X_MM, center_y, AXIS_Z_MM),
    )
    slot = box(14.0, 16.0, 18.0, (AXIS_X_MM, center_y, AXIS_Z_MM + 12.0))
    return base.cut(bore).cut(slot)


def inboard_face_reference(side: str) -> cq.Shape:
    y = LEFT_FACE_Y_MM if side == "LEFT" else RIGHT_FACE_Y_MM
    plate = box(45.0, 2.0, 45.0, (AXIS_X_MM, y, AXIS_Z_MM))
    bore = cylinder_y(5.6, 4.0, (AXIS_X_MM, y, AXIS_Z_MM))
    return plate.cut(bore)


def test_shaft(side: str, stock_length_mm: float = SHAFT_STOCK_LENGTH_MM) -> cq.Shape:
    if side == "LEFT":
        center_y = LEFT_SHAFT_END_Y_MM + stock_length_mm / 2.0
    else:
        center_y = RIGHT_SHAFT_END_Y_MM - stock_length_mm / 2.0
    return cylinder_y(
        SHAFT_DIAMETER_MM / 2.0,
        stock_length_mm,
        (AXIS_X_MM, center_y, AXIS_Z_MM),
    )


def unit_input_dummy(side: str) -> cq.Shape:
    sign = 1.0 if side == "LEFT" else -1.0
    return cylinder_y(5.0, 16.0, (AXIS_X_MM, sign * 10.0, AXIS_Z_MM))


def sliding_sleeve_dummy(side: str, travel_mm: float) -> cq.Shape:
    if not 0.0 <= travel_mm <= SLEEVE_STROKE_MM:
        raise ValueError(f"travel outside 0..10mm: {travel_mm}")
    sign = 1.0 if side == "LEFT" else -1.0
    center_y = sign * (13.0 + travel_mm)
    return annulus_y(
        SLEEVE_OD_MM / 2.0,
        DUMMY_BORE_DIAMETER_MM / 2.0,
        SLEEVE_MOVING_LENGTH_MM,
        (AXIS_X_MM, center_y, AXIS_Z_MM),
    )


def sleeve_body_dummy(side: str) -> cq.Shape:
    sign = 1.0 if side == "LEFT" else -1.0
    return annulus_y(
        SLEEVE_OD_MM / 2.0 + 2.0,
        SLEEVE_OD_MM / 2.0 + 0.4,
        SLEEVE_BODY_LENGTH_MM,
        (AXIS_X_MM, sign * 18.0, AXIS_Z_MM),
    )


def central_unit_bridge(x_center: float = 205.0) -> list[cq.Shape]:
    return [
        box(70.0, 44.0, 10.0, (x_center, 0.0, AXIS_Z_MM + 45.0)),
        box(10.0, 44.0, 75.0, (x_center + 30.0, 0.0, AXIS_Z_MM + 10.0)),
        box(42.0, 6.0, 12.0, (x_center - 12.0, 25.0, AXIS_Z_MM - 18.0)),
        box(42.0, 6.0, 12.0, (x_center - 12.0, -25.0, AXIS_Z_MM - 18.0)),
    ]


def alignment_guides() -> list[cq.Shape]:
    return [
        box(75.0, 4.0, 12.0, (205.0, 28.0, AXIS_Z_MM - 35.0)),
        box(75.0, 4.0, 12.0, (205.0, -28.0, AXIS_Z_MM - 35.0)),
    ]


def mechanical_lock_dummy() -> cq.Shape:
    return box(18.0, 32.0, 18.0, (236.0, 0.0, AXIS_Z_MM + 30.0))


def position_flag(side: str, travel_mm: float) -> cq.Shape:
    sign = 1.0 if side == "LEFT" else -1.0
    return box(5.0, 2.0, 25.0, (
        AXIS_X_MM + 11.0,
        sign * (13.0 + travel_mm),
        AXIS_Z_MM + 20.0,
    ))


def guard_clearance_gauge(side: str) -> cq.Shape:
    sign = 1.0 if side == "LEFT" else -1.0
    return box(38.0, 3.0, 38.0, (
        AXIS_X_MM,
        sign * 36.5,
        AXIS_Z_MM,
    )).cut(
        cylinder_y(13.0, 5.0, (
            AXIS_X_MM,
            sign * 36.5,
            AXIS_Z_MM,
        ))
    )


def center_gap_gauge(width_mm: float = CENTER_GAP_MM) -> cq.Shape:
    body = box(12.0, width_mm, 5.0, (0.0, 0.0, 2.5))
    handle = box(28.0, 8.0, 8.0, (10.0, 0.0, 7.0))
    return body.fuse(handle)


def stub_gauge(length_mm: float = STUB_LENGTH_MM) -> cq.Shape:
    body = box(20.0, length_mm, 6.0, (0.0, length_mm / 2.0, 3.0))
    # Keep the stop inside the nominal 0..length axial interval so the
    # exported gauge's Y bounding length is the stated reference length.
    stop = box(28.0, 2.0, 16.0, (0.0, 1.0, 8.0))
    return body.fuse(stop)


def warning_text_plate(text: str, center: tuple[float, float, float]) -> cq.Shape:
    x, y, z = center
    plate = box(72.0, 22.0, 3.0, (x, y, z))
    label = (
        cq.Workplane("XY").text(text, 5.0, 1.0, combine=True)
        .translate((x, y, z + 2.0)).val()
    )
    return cq.Compound.makeCompound([plate, label])


def engagement_overlap_from_intervals(travel_mm: float) -> float:
    """Derive overlap from sleeve/stub axial intervals, not a fixed result."""
    left_sleeve_min = 8.0 + travel_mm
    left_sleeve_max = 18.0 + travel_mm
    left_stub_min = LEFT_SHAFT_END_Y_MM
    left_stub_max = LEFT_FACE_Y_MM
    return max(
        0.0,
        min(left_sleeve_max, left_stub_max)
        - max(left_sleeve_min, left_stub_min),
    )


def assembly_named_shapes(state: str) -> dict[str, cq.Shape]:
    if state not in DRY_FIT_STATES:
        raise ValueError(f"unknown dry-fit state: {state}")
    shapes: dict[str, cq.Shape] = {}
    if state == "DF0_PARTS":
        # Exploded view; all three gauges are comparison references, not
        # tolerance gauges. Test shafts remain separate and disconnected.
        shapes = {
            "LEFT_TEST_SHAFT": test_shaft("LEFT").translate(cq.Vector(-80, 0, 0)),
            "RIGHT_TEST_SHAFT": test_shaft("RIGHT").translate(cq.Vector(80, 0, 0)),
            "LEFT_STUB_POSITIONING_BLOCK": shaft_positioning_block("LEFT").translate(cq.Vector(-50, 0, 0)),
            "RIGHT_STUB_POSITIONING_BLOCK": shaft_positioning_block("RIGHT").translate(cq.Vector(50, 0, 0)),
            "CENTER_GAP_GAUGE_35": center_gap_gauge(35.0).translate(cq.Vector(80, 0, 280)),
            "CENTER_GAP_GAUGE_36": center_gap_gauge(36.0).translate(cq.Vector(110, 0, 280)),
            "CENTER_GAP_GAUGE_37": center_gap_gauge(37.0).translate(cq.Vector(140, 0, 280)),
            "LEFT_STUB_GAUGE_12P5": stub_gauge().translate(cq.Vector(100, 40, 280)),
            "RIGHT_STUB_GAUGE_12P5": stub_gauge().mirror("XZ").translate(cq.Vector(100, -40, 280)),
        }
        return shapes

    shapes.update({
        "LEFT_TEST_SHAFT": test_shaft("LEFT"),
        "RIGHT_TEST_SHAFT": test_shaft("RIGHT"),
        "LEFT_STUB_POSITIONING_BLOCK": shaft_positioning_block("LEFT"),
        "RIGHT_STUB_POSITIONING_BLOCK": shaft_positioning_block("RIGHT"),
        "LEFT_INBOARD_FACE_REFERENCE": inboard_face_reference("LEFT"),
        "RIGHT_INBOARD_FACE_REFERENCE": inboard_face_reference("RIGHT"),
    })
    if state == "DF1_SHAFTS_POSITIONED":
        return shapes

    travel = {
        "DF2_SLEEVES_RETRACTED": 0.0,
        "DF3_UNIT_INSERTING": 0.0,
        "DF4_UNIT_LOCKED": 0.0,
        "DF5_PARTIAL": 5.0,
        "DF6_ENGAGED": 10.0,
        "DF7_DISENGAGING": 5.0,
        "DF8_REMOVABLE": 0.0,
    }[state]
    shapes.update({
        "LEFT_SLIDING_SLEEVE_DUMMY": sliding_sleeve_dummy("LEFT", travel),
        "RIGHT_SLIDING_SLEEVE_DUMMY": sliding_sleeve_dummy("RIGHT", travel),
        "LEFT_COUPLING_BODY_DUMMY": sleeve_body_dummy("LEFT"),
        "RIGHT_COUPLING_BODY_DUMMY": sleeve_body_dummy("RIGHT"),
        "LEFT_COUPLING_POSITION_FLAG": position_flag("LEFT", travel),
        "RIGHT_COUPLING_POSITION_FLAG": position_flag("RIGHT", travel),
        "LEFT_GUARD_CLEARANCE_GAUGE": guard_clearance_gauge("LEFT"),
        "RIGHT_GUARD_CLEARANCE_GAUGE": guard_clearance_gauge("RIGHT"),
    })
    if state == "DF2_SLEEVES_RETRACTED":
        return shapes

    insertion_x = 250.0 if state in {"DF3_UNIT_INSERTING", "DF8_REMOVABLE"} else 205.0
    for index, part in enumerate(central_unit_bridge(insertion_x), 1):
        shapes[f"CENTRAL_UNIT_BRIDGE_DUMMY_{index}"] = part
    shapes["LEFT_UNIT_INPUT_DUMMY"] = unit_input_dummy("LEFT").translate(
        cq.Vector(insertion_x - 205.0, 0, 0)
    )
    shapes["RIGHT_UNIT_INPUT_DUMMY"] = unit_input_dummy("RIGHT").translate(
        cq.Vector(insertion_x - 205.0, 0, 0)
    )
    for index, guide in enumerate(alignment_guides(), 1):
        shapes[f"ALIGNMENT_GUIDE_{index}"] = guide
    if state not in {"DF3_UNIT_INSERTING", "DF8_REMOVABLE"}:
        shapes["MECHANICAL_LOCK_DUMMY"] = mechanical_lock_dummy()
        shapes["SENSOR_TARGET_DUMMY"] = box(
            8.0, 8.0, 8.0, (210.0, 0.0, AXIS_Z_MM + 70.0)
        )
    return shapes


def print_plate_shapes() -> dict[str, cq.Shape]:
    """Arrange only printable no-load parts inside a Bambu A1-size plate."""
    shapes: dict[str, cq.Shape] = {
        "PLATE_LEFT_POSITION_BLOCK": shaft_positioning_block("LEFT").translate(cq.Vector(-240, -25, -304)),
        "PLATE_RIGHT_POSITION_BLOCK": shaft_positioning_block("RIGHT").translate(cq.Vector(-190, 25, -304)),
        "PLATE_LEFT_FACE_REF": inboard_face_reference("LEFT").translate(cq.Vector(-130, -45, -297.5)),
        "PLATE_RIGHT_FACE_REF": inboard_face_reference("RIGHT").translate(cq.Vector(-80, 45, -297.5)),
        "PLATE_GAP_35": center_gap_gauge(35.0).translate(cq.Vector(-90, 75, 0)),
        "PLATE_GAP_36": center_gap_gauge(36.0).translate(cq.Vector(-55, 75, 0)),
        "PLATE_GAP_37": center_gap_gauge(37.0).translate(cq.Vector(-20, 75, 0)),
        "PLATE_STUB_LEFT": stub_gauge().translate(cq.Vector(20, 70, 0)),
        "PLATE_STUB_RIGHT": stub_gauge().mirror("XZ").translate(cq.Vector(55, 70, 0)),
        "PLATE_SLEEVE_LEFT": sliding_sleeve_dummy("LEFT", 0.0).translate(cq.Vector(-150, 5, -305)),
        "PLATE_SLEEVE_RIGHT": sliding_sleeve_dummy("RIGHT", 0.0).translate(cq.Vector(-110, -5, -305)),
        "WARNING_NO_LOAD": warning_text_plate("NO LOAD", (55.0, -75.0, 1.5)),
        "WARNING_HAND_FIT": warning_text_plate("HAND FIT", (-35.0, -75.0, 1.5)),
        "WARNING_NO_COMMON": warning_text_plate("NO COMMON SHAFT", (10.0, -42.0, 1.5)),
    }
    return shapes


def dry_fit_part_rows() -> list[dict[str, Any]]:
    return [
        {"part_name": "LEFT_STUB_POSITIONING_BLOCK", "quantity": 1, "approximate_bounding_size_mm": "38x12x32", "recommended_orientation": "flat side down", "support_requirement": "none", "material_candidate": "PETG", "warning": "NO_LOAD_JIG_SLOT; NOT_A_MANUFACTURING_HOLE", "expected_purpose": "locate uncut left shaft independently"},
        {"part_name": "RIGHT_STUB_POSITIONING_BLOCK", "quantity": 1, "approximate_bounding_size_mm": "38x12x32", "recommended_orientation": "flat side down", "support_requirement": "none", "material_candidate": "PETG", "warning": "NO_LOAD_JIG_SLOT; NOT_A_MANUFACTURING_HOLE", "expected_purpose": "locate uncut right shaft independently"},
        {"part_name": "INBOARD_FACE_REFERENCE", "quantity": 2, "approximate_bounding_size_mm": "45x2x45", "recommended_orientation": "face flat", "support_requirement": "none", "material_candidate": "PETG", "warning": "NOMINAL_GEOMETRY_REFERENCE_ONLY", "expected_purpose": "bearing inboard face reference"},
        {"part_name": "CENTER_GAP_GAUGE_35", "quantity": 1, "approximate_bounding_size_mm": "28x35x11", "recommended_orientation": "flat", "support_requirement": "none", "material_candidate": "PETG", "warning": "NOT_A_TOLERANCE_GAUGE", "expected_purpose": "comparison only"},
        {"part_name": "CENTER_GAP_GAUGE_36", "quantity": 1, "approximate_bounding_size_mm": "28x36x11", "recommended_orientation": "flat", "support_requirement": "none", "material_candidate": "PETG", "warning": "CENTER_GAP_REFERENCE; NO_LOAD_ONLY", "expected_purpose": "nominal center gap check"},
        {"part_name": "CENTER_GAP_GAUGE_37", "quantity": 1, "approximate_bounding_size_mm": "28x37x11", "recommended_orientation": "flat", "support_requirement": "none", "material_candidate": "PETG", "warning": "NOT_A_TOLERANCE_GAUGE", "expected_purpose": "comparison only"},
        {"part_name": "STUB_GAUGE_12P5", "quantity": 2, "approximate_bounding_size_mm": "28x12.5x16", "recommended_orientation": "stop face down", "support_requirement": "none", "material_candidate": "PETG", "warning": "NOMINAL_GEOMETRY_REFERENCE_ONLY", "expected_purpose": "12.5mm stub reference"},
        {"part_name": "SLIDING_SLEEVE_DUMMY", "quantity": 2, "approximate_bounding_size_mm": "20x10x20", "recommended_orientation": "axis vertical", "support_requirement": "none", "material_candidate": "PETG", "warning": "DUMMY_CLEARANCE_NOT_PRODUCT_FIT", "expected_purpose": "manual 0/5/10mm travel check"},
        {"part_name": "COUPLING_BODY_DUMMY", "quantity": 2, "approximate_bounding_size_mm": "24x25x24", "recommended_orientation": "axis vertical", "support_requirement": "none", "material_candidate": "PETG", "warning": "NOT_FOR_TORQUE", "expected_purpose": "SMALL body envelope"},
        {"part_name": "CENTRAL_UNIT_BRIDGE_DUMMY", "quantity": 4, "approximate_bounding_size_mm": "70x44x10 max", "recommended_orientation": "split flat", "support_requirement": "none", "material_candidate": "PETG", "warning": "NO_LOAD_GEOMETRY_DUMMY", "expected_purpose": "front insertion and independent input supports"},
        {"part_name": "ALIGNMENT_GUIDE", "quantity": 2, "approximate_bounding_size_mm": "75x4x12", "recommended_orientation": "flat", "support_requirement": "none", "material_candidate": "PETG", "warning": "HAND_FIT_ONLY", "expected_purpose": "front insertion reference"},
        {"part_name": "MECHANICAL_LOCK_DUMMY", "quantity": 1, "approximate_bounding_size_mm": "18x32x18", "recommended_orientation": "flat", "support_requirement": "none", "material_candidate": "PETG", "warning": "NO_LOAD_ONLY", "expected_purpose": "sequence confirmation"},
        {"part_name": "COUPLING_POSITION_FLAG", "quantity": 2, "approximate_bounding_size_mm": "5x2x25", "recommended_orientation": "flat", "support_requirement": "none", "material_candidate": "PETG", "warning": "SENSOR_TARGET_DUMMY", "expected_purpose": "retracted/partial/engaged indication"},
        {"part_name": "GUARD_CLEARANCE_GAUGE", "quantity": 2, "approximate_bounding_size_mm": "38x3x38", "recommended_orientation": "flat", "support_requirement": "none", "material_candidate": "PETG", "warning": "NOT_A_GUARD", "expected_purpose": "guard clearance reference"},
        {"part_name": "WARNING_PLATE", "quantity": 3, "approximate_bounding_size_mm": "72x22x4", "recommended_orientation": "text up", "support_requirement": "none", "material_candidate": "PETG", "warning": "NOT_FOR_MANUFACTURING", "expected_purpose": "mandatory no-load labeling"},
        {"part_name": "LEFT_TEST_SHAFT / RIGHT_TEST_SHAFT", "quantity": 2, "approximate_bounding_size_mm": "OD10x300 stock", "recommended_orientation": "not printed", "support_requirement": "not applicable", "material_candidate": "existing stock only", "warning": "DO_NOT_CUT; NO_POWERED_ROTATION", "expected_purpose": "two physically independent uncut shaft references"},
    ]


def dry_fit_dimension_rows() -> list[dict[str, Any]]:
    values = [
        ("LEFT_INBOARD_FACE_Y", LEFT_FACE_Y_MM, "mm", "NOMINAL_GEOMETRY_REFERENCE_ONLY"),
        ("RIGHT_INBOARD_FACE_Y", RIGHT_FACE_Y_MM, "mm", "NOMINAL_GEOMETRY_REFERENCE_ONLY"),
        ("LEFT_SHAFT_END_Y", LEFT_SHAFT_END_Y_MM, "mm", "NOMINAL_GEOMETRY_REFERENCE_ONLY"),
        ("RIGHT_SHAFT_END_Y", RIGHT_SHAFT_END_Y_MM, "mm", "NOMINAL_GEOMETRY_REFERENCE_ONLY"),
        ("LEFT_STUB_LENGTH", STUB_LENGTH_MM, "mm", "NOMINAL_GEOMETRY_REFERENCE_ONLY"),
        ("RIGHT_STUB_LENGTH", STUB_LENGTH_MM, "mm", "NOMINAL_GEOMETRY_REFERENCE_ONLY"),
        ("CENTER_GAP", CENTER_GAP_MM, "mm", "NOT_A_TOLERANCE_GAUGE"),
        ("SLEEVE_OD", SLEEVE_OD_MM, "mm", "PARAMETRIC_ENVELOPE_CANDIDATE"),
        ("SLEEVE_BODY_LENGTH", SLEEVE_BODY_LENGTH_MM, "mm", "PARAMETRIC_ENVELOPE_CANDIDATE"),
        ("SLEEVE_MOVING_LENGTH", SLEEVE_MOVING_LENGTH_MM, "mm", "NO_LOAD_DUMMY"),
        ("SLEEVE_STROKE", SLEEVE_STROKE_MM, "mm", "NO_LOAD_DUMMY"),
        ("ENGAGEMENT_REFERENCE", ENGAGEMENT_REFERENCE_MM, "mm", "NO_LOAD_ONLY"),
        ("DUMMY_BORE_DIAMETER", DUMMY_BORE_DIAMETER_MM, "mm", "DUMMY_CLEARANCE_NOT_PRODUCT_FIT"),
        ("TEST_SHAFT_STOCK_LENGTH", SHAFT_STOCK_LENGTH_MM, "mm", "DO_NOT_CUT"),
        ("SINGLE_CONTINUOUS_SHAFT_USED", False, "boolean", "MUST_BE_FALSE"),
    ]
    return [
        {
            "parameter": name,
            "value": value,
            "unit": unit,
            "classification": classification,
        }
        for name, value, unit, classification in values
    ]
