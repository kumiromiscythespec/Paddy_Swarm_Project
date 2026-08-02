"""Self-supporting non-circular tower-shell opening for Phase 3R."""

from __future__ import annotations

from math import cos, pi, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    module_height,
    module_wall_thickness,
    phase3r_min_root_thickness,
    plant_port_angle,
    plant_port_local_angles,
    port_shell_coupon_height,
    port_shell_max_overhang_angle,
    port_shell_opening_height,
    port_shell_opening_type,
    port_shell_opening_width,
    port_shell_reinforcement_thickness,
    tower_body_diameter,
)


STATUS = "PHASE3R_SELF_SUPPORTING_NONCIRCULAR_SHELL_OPENING"
PRINT_ORIENTATION = "TOWER_AXIS_VERTICAL_NO_SUPPORT_TARGET"
ROUNDNESS_POLICY = "NO_CIRCULAR_FIT_DATUM_ON_PRINTED_SHELL"
MOUNT_FACE = "QUASI_FLAT_TEARDROP_FRAME"
ROOT_FILLET_TARGET = "R4_CLASS_CALIBRATION_PENDING"


def _teardrop_points(offset: float = 0.0) -> list[tuple[float, float]]:
    half_width = 0.5 * port_shell_opening_width + offset
    half_height = 0.5 * port_shell_opening_height + offset
    lower_center_z = -8.0
    points: list[tuple[float, float]] = []
    for index in range(25):
        angle = pi + pi * index / 24.0
        points.append(
            (
                half_width * cos(angle),
                lower_center_z + half_width * sin(angle),
            )
        )
    shoulder_z = half_height - half_width
    points.extend(
        (
            (half_width, shoulder_z),
            (0.0, half_height),
            (-half_width, shoulder_z),
        )
    )
    return points


def _profile_prism(
    x_origin: float,
    z_center: float,
    extrusion: float,
    offset: float,
) -> cq.Workplane:
    return (
        cq.Workplane("YZ", origin=(x_origin, 0.0, z_center))
        .polyline(_teardrop_points(offset))
        .close()
        .extrude(extrusion)
        .rotate(
            (100.0, 0.0, z_center),
            (100.0, 1.0, z_center),
            -plant_port_angle,
        )
    )


def build_self_supporting_port_void_phase3r(
    z_center: float,
    angle_deg: float = 0.0,
) -> cq.Workplane:
    void = _profile_prism(70.0, z_center, 58.0, 0.0)
    return void.rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        angle_deg,
    )


def build_self_supporting_port_frame_phase3r(
    z_center: float,
    angle_deg: float = 0.0,
) -> cq.Workplane:
    outer = _profile_prism(
        80.5,
        z_center,
        13.0,
        port_shell_reinforcement_thickness,
    )
    inner = _profile_prism(78.5, z_center, 18.0, 0.0)
    frame = outer.cut(inner)
    return frame.rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        angle_deg,
    )


def _shell(height: float) -> cq.Workplane:
    outer = 0.5 * tower_body_diameter
    return (
        cq.Workplane("XY")
        .circle(outer)
        .circle(outer - module_wall_thickness)
        .extrude(height)
    )


def add_self_supporting_port_phase3r(
    shell: cq.Workplane,
    z_center: float,
    angle_deg: float,
) -> cq.Workplane:
    frame = build_self_supporting_port_frame_phase3r(z_center, angle_deg)
    void = build_self_supporting_port_void_phase3r(z_center, angle_deg)
    return shell.union(frame).cut(void)


def build_self_supporting_port_shell_coupon_phase3r() -> cq.Workplane:
    shell = _shell(port_shell_coupon_height)
    return add_self_supporting_port_phase3r(
        shell,
        0.5 * port_shell_coupon_height,
        0.0,
    )


def build_three_port_module_shell_phase3r() -> cq.Workplane:
    shell = _shell(module_height)
    for angle in plant_port_local_angles:
        shell = add_self_supporting_port_phase3r(
            shell,
            0.5 * module_height,
            angle,
        )
    return shell


def self_supporting_upper_slope_angle() -> float:
    """The two apex faces are constructed at the requested 45 degrees."""

    assert port_shell_opening_type == "TEARDROP_45_DEGREE_SELF_SUPPORTING"
    assert phase3r_min_root_thickness >= 4.0
    return port_shell_max_overhang_angle
