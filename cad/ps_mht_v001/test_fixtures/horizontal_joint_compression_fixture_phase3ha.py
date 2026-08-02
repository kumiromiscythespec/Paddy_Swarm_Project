"""External axial-compression fixture for Phase 3H-A joint testing."""

from __future__ import annotations

from math import cos, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    horizontal_joint_nominal_inner_diameter,
    phase3ha_compression_ring_inner_diameter,
    phase3ha_compression_ring_outer_diameter,
    phase3ha_compression_ring_thickness,
    phase3ha_m4_angle_positions,
    phase3ha_m4_clearance_hole,
    phase3ha_m4_pitch_radius,
    phase3ha_test_fixture_status,
)
from ps_mht_v001.tower_module.horizontal_ring_joint_phase3ha import (
    full_ring_joint_assembly_parts_phase3ha,
    validate_horizontal_joint_clearance_phase3ha,
)


PRINT_ORIENTATION = "FLAT_FULL_RING"
RING_PARTS_COMMON = True
THREADED_ROD_DIAMETER_MM = 4.0
THREADED_ROD_REFERENCE_LENGTH_MM = 112.0
WASHER_OUTER_DIAMETER_MM = 10.0
WASHER_THICKNESS_MM = 1.0
NUT_ACROSS_FLATS_MM = 7.0
NUT_THICKNESS_MM = 3.2
SMALL_NUT_CARTRIDGE_COUNT = 0
SMALL_GATE_COUNT = 0


def m4_axis_points_phase3ha() -> tuple[tuple[float, float], ...]:
    return tuple(
        (
            phase3ha_m4_pitch_radius * cos(radians(angle)),
            phase3ha_m4_pitch_radius * sin(radians(angle)),
        )
        for angle in phase3ha_m4_angle_positions
    )


def build_horizontal_joint_compression_ring_phase3ha() -> cq.Workplane:
    """Build one common upper/lower compression ring for flat printing."""

    ring = (
        cq.Workplane("XY")
        .circle(0.5 * phase3ha_compression_ring_outer_diameter)
        .circle(0.5 * phase3ha_compression_ring_inner_diameter)
        .extrude(phase3ha_compression_ring_thickness)
    )
    for x_value, y_value in m4_axis_points_phase3ha():
        hole = (
            cq.Workplane("XY")
            .transformed(offset=(x_value, y_value, -1.0))
            .circle(0.5 * phase3ha_m4_clearance_hole)
            .extrude(phase3ha_compression_ring_thickness + 2.0)
        )
        ring = ring.cut(hole)
    return ring


def _reference_rod(x_value: float, y_value: float) -> cq.Shape:
    return (
        cq.Workplane("XY")
        .transformed(offset=(x_value, y_value, -12.0))
        .circle(0.5 * THREADED_ROD_DIAMETER_MM)
        .extrude(THREADED_ROD_REFERENCE_LENGTH_MM)
        .val()
    )


def _reference_washer(x_value: float, y_value: float, z_value: float) -> cq.Shape:
    return (
        cq.Workplane("XY")
        .transformed(offset=(x_value, y_value, z_value))
        .circle(0.5 * WASHER_OUTER_DIAMETER_MM)
        .circle(0.5 * phase3ha_m4_clearance_hole)
        .extrude(WASHER_THICKNESS_MM)
        .val()
    )


def _reference_nut(x_value: float, y_value: float, z_value: float) -> cq.Shape:
    circumradius = NUT_ACROSS_FLATS_MM / (3.0 ** 0.5)
    return (
        cq.Workplane("XY")
        .transformed(offset=(x_value, y_value, z_value))
        .polygon(6, 2.0 * circumradius)
        .circle(0.5 * THREADED_ROD_DIAMETER_MM)
        .extrude(NUT_THICKNESS_MM)
        .val()
    )


def build_horizontal_joint_compression_assembly_reference_phase3ha(
    clearance: float,
) -> cq.Workplane:
    """Return a fixture-only assembly with purchased hardware references."""

    value = validate_horizontal_joint_clearance_phase3ha(clearance)
    lower_joint, upper_joint = full_ring_joint_assembly_parts_phase3ha(value)
    lower_fixture = build_horizontal_joint_compression_ring_phase3ha().translate(
        (0.0, 0.0, -8.0)
    )
    upper_fixture = build_horizontal_joint_compression_ring_phase3ha().translate(
        (0.0, 0.0, 80.0)
    )
    shapes: list[cq.Shape] = [
        lower_joint.val(),
        upper_joint.val(),
        lower_fixture.val(),
        upper_fixture.val(),
    ]
    for x_value, y_value in m4_axis_points_phase3ha():
        shapes.extend(
            [
                _reference_rod(x_value, y_value),
                _reference_washer(x_value, y_value, -9.5),
                _reference_nut(x_value, y_value, -12.0),
                _reference_washer(x_value, y_value, 88.5),
                _reference_nut(x_value, y_value, 89.5),
            ]
        )
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


def compression_fixture_requirements_phase3ha() -> dict[str, object]:
    minimum_m4_radius = (
        phase3ha_m4_pitch_radius - 0.5 * phase3ha_m4_clearance_hole
    )
    return {
        "status": phase3ha_test_fixture_status,
        "print_orientation": PRINT_ORIENTATION,
        "common_upper_lower_ring": RING_PARTS_COMMON,
        "outer_diameter_mm": phase3ha_compression_ring_outer_diameter,
        "inner_diameter_mm": phase3ha_compression_ring_inner_diameter,
        "thickness_mm": phase3ha_compression_ring_thickness,
        "m4_angle_positions_deg": list(phase3ha_m4_angle_positions),
        "m4_pitch_radius_mm": phase3ha_m4_pitch_radius,
        "m4_clearance_hole_mm": phase3ha_m4_clearance_hole,
        "minimum_m4_radial_envelope_mm": minimum_m4_radius,
        "root_envelope_radius_mm": 0.5 * horizontal_joint_nominal_inner_diameter,
        "m4_outside_root_envelope": minimum_m4_radius
        > 0.5 * horizontal_joint_nominal_inner_diameter,
        "m4_outside_200mm_body": minimum_m4_radius > 100.0,
        "threaded_rod_reference_count": 3,
        "washer_reference_count": 6,
        "nut_reference_count": 6,
        "small_nut_cartridge_count": SMALL_NUT_CARTRIDGE_COUNT,
        "small_gate_count": SMALL_GATE_COUNT,
        "production_fastener_authority": False,
    }
