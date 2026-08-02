"""Phase 3R.1 fused self-supporting shell opening.

The printable coupon contains only the shell and its structural frame.  The
replaceable circular function ring is intentionally exported on its own plate.
"""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.parameters import (
    module_height,
    module_wall_thickness,
    phase3r_min_root_thickness,
    plant_port_local_angles,
    port_shell_coupon_height,
    port_shell_max_overhang_angle,
    port_shell_reinforcement_thickness,
    tower_body_diameter,
)
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r import (
    _profile_prism,
    build_self_supporting_port_void_phase3r,
)


STATUS = "PHASE3R1_FUSED_SELF_SUPPORTING_SHELL_FRAME"
PRINT_ORIENTATION = "TOWER_AXIS_VERTICAL_NO_SUPPORT_TARGET"
ROUNDNESS_POLICY = "NO_CIRCULAR_FIT_DATUM_ON_PRINTED_SHELL"
ROOT_FILLET_TARGET = "R4_CLASS_CALIBRATION_PENDING"
FRAME_INWARD_SHIFT_MM = 1.0
SHELL_FRAME_RADIAL_FUSION_INCREASE_MM = 1.0
ROOT_INCLUSION_PROBE_DIAMETER_MM = 4.0
TARGET_MAXIMUM_DIAMETER_MM = 238.0


def build_shell_blank_phase3r1(
    height: float = port_shell_coupon_height,
) -> cq.Workplane:
    """Return the unchanged 3 mm cylindrical structural shell."""

    outer_radius = 0.5 * tower_body_diameter
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(outer_radius - module_wall_thickness)
        .extrude(height)
    )


def build_self_supporting_port_frame_phase3r1(
    z_center: float,
    angle_deg: float = 0.0,
) -> cq.Workplane:
    """Return the R4-class frame shifted 1 mm into the shell load path."""

    outer = _profile_prism(
        80.5 - FRAME_INWARD_SHIFT_MM,
        z_center,
        13.0,
        port_shell_reinforcement_thickness,
    )
    inner = _profile_prism(
        78.5 - FRAME_INWARD_SHIFT_MM,
        z_center,
        18.0,
        0.0,
    )
    return outer.cut(inner).rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        angle_deg,
    )


def build_self_supporting_port_void_phase3r1(
    z_center: float,
    angle_deg: float = 0.0,
) -> cq.Workplane:
    """Retain the Phase 3R 45-degree teardrop opening exactly."""

    return build_self_supporting_port_void_phase3r(z_center, angle_deg)


def build_shell_frame_union_before_void_phase3r1(
    height: float = port_shell_coupon_height,
    z_center: float | None = None,
    angle_deg: float = 0.0,
) -> cq.Workplane:
    center = 0.5 * height if z_center is None else z_center
    shell = build_shell_blank_phase3r1(height)
    frame = build_self_supporting_port_frame_phase3r1(center, angle_deg)
    return shell.union(frame)


def add_self_supporting_port_phase3r1(
    shell: cq.Workplane,
    z_center: float,
    angle_deg: float,
) -> cq.Workplane:
    """Fuse first, then cut the opening so the root connection survives."""

    frame = build_self_supporting_port_frame_phase3r1(z_center, angle_deg)
    void = build_self_supporting_port_void_phase3r1(z_center, angle_deg)
    return shell.union(frame).cut(void)


def build_self_supporting_port_shell_coupon_phase3r1() -> cq.Workplane:
    shell = build_shell_blank_phase3r1(port_shell_coupon_height)
    return add_self_supporting_port_phase3r1(
        shell,
        0.5 * port_shell_coupon_height,
        0.0,
    )


def build_three_port_module_shell_phase3r1() -> cq.Workplane:
    shell = build_shell_blank_phase3r1(module_height)
    for angle_deg in plant_port_local_angles:
        shell = add_self_supporting_port_phase3r1(
            shell,
            0.5 * module_height,
            angle_deg,
        )
    return shell


def build_root_inclusion_probe_phase3r1(
    z_center: float = 0.5 * port_shell_coupon_height,
) -> cq.Workplane:
    """A real 4 mm sphere located in the surviving shell/frame root."""

    return (
        cq.Workplane("XY")
        .sphere(0.5 * ROOT_INCLUSION_PROBE_DIAMETER_MM)
        .translate((86.5, 46.0, z_center - 12.0))
    )


def shell_frame_intersection_volume_phase3r1(
    height: float = port_shell_coupon_height,
) -> float:
    shell = build_shell_blank_phase3r1(height)
    frame = build_self_supporting_port_frame_phase3r1(0.5 * height)
    return sum(
        solid.Volume()
        for solid in shell.intersect(frame).solids().vals()
    )


def fusion_volume_relation_phase3r1() -> dict[str, float]:
    """Return the measured volume identity used to audit the boolean union."""

    shell = build_shell_blank_phase3r1()
    frame = build_self_supporting_port_frame_phase3r1(
        0.5 * port_shell_coupon_height
    )
    intersection = shell.intersect(frame)
    union = shell.union(frame)
    return {
        "shell_mm3": sum(s.Volume() for s in shell.solids().vals()),
        "frame_mm3": sum(s.Volume() for s in frame.solids().vals()),
        "intersection_mm3": sum(
            s.Volume() for s in intersection.solids().vals()
        ),
        "union_mm3": sum(s.Volume() for s in union.solids().vals()),
    }


def self_supporting_upper_slope_angle_phase3r1() -> float:
    assert phase3r_min_root_thickness >= ROOT_INCLUSION_PROBE_DIAMETER_MM
    return port_shell_max_overhang_angle
