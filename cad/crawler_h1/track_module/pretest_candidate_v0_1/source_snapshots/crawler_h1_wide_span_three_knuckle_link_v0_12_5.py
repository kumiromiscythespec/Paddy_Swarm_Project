#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""crawler_h1 v0.12.5 wide-span three-knuckle link generator.

Relative to v0.12.4:
- keeps the complete link body, GAP-B, guide, LUG and tool design;
- widens the three-knuckle bearing stack from 19.8 mm to 46.0 mm;
- moves Starlock service access outside the new ±23.0 mm ear faces;
- changes the provisional φ3 mm shaft length to 50.5 mm.

FIT TEST ONLY. Motor, load, mud, water and 40+8 production remain HOLD.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Sequence
import argparse
import hashlib
import importlib.util
import json
import shutil
import sys

try:
    import cadquery as cq
    from cadquery import exporters
except Exception:
    cq = None
    exporters = None


VERSION = "crawler-h1-v0.12.5-wide-span-three-knuckle"
PACKAGE_NAME = "crawler_h1_wide_span_three_knuckle_link_v0_12_5"
STATUS = "WIDE_46_TWO_LINK_FIT_TEST_MOTOR_LOAD_MUD_WATER_QUANTITY_HOLD"


@dataclass(frozen=True)
class WideKnuckleSpec:
    outer_ear_width_mm: float = 10.0
    center_ear_width_mm: float = 24.8
    interleave_gap_each_mm: float = 0.6
    target_total_width_mm: float = 46.0
    body_width_mm: float = 50.0
    guide_max_width_mm: float = 54.0

    @property
    def center_ear_half_width_mm(self) -> float:
        return self.center_ear_width_mm / 2.0

    @property
    def outer_ear_center_y_mm(self) -> float:
        return (
            self.center_ear_width_mm / 2.0
            + self.interleave_gap_each_mm
            + self.outer_ear_width_mm / 2.0
        )

    @property
    def calculated_total_width_mm(self) -> float:
        return (
            2.0 * self.outer_ear_width_mm
            + self.center_ear_width_mm
            + 2.0 * self.interleave_gap_each_mm
        )

    @property
    def outer_face_y_abs_mm(self) -> float:
        return self.calculated_total_width_mm / 2.0

    @property
    def body_edge_margin_each_mm(self) -> float:
        return self.body_width_mm / 2.0 - self.outer_face_y_abs_mm

    @property
    def guide_edge_margin_each_mm(self) -> float:
        return self.guide_max_width_mm / 2.0 - self.outer_face_y_abs_mm

    @property
    def total_bearing_material_mm(self) -> float:
        return 2.0 * self.outer_ear_width_mm + self.center_ear_width_mm

    @property
    def outer_ear_center_span_mm(self) -> float:
        return 2.0 * self.outer_ear_center_y_mm


WIDE = WideKnuckleSpec()


@dataclass(frozen=True)
class Params:
    access_diameter_mm: float = 9.4
    service_outer_y_abs_mm: float = 28.0
    service_ear_face_clearance_mm: float = 0.1

    receiver_relief_diameter_mm: float = 13.2
    receiver_y_clearance_each_mm: float = 0.6
    receiver_flare_extra_radius_mm: float = 0.8
    receiver_flare_depth_mm: float = 1.2

    shaft_reference_diameter_mm: float = 3.0
    shaft_reference_length_mm: float = 50.5
    shaft_fit_a_mm: float = 50.0
    shaft_fit_b_mm: float = 50.5
    shaft_fit_c_mm: float = 51.0

    starlock_od_reference_mm: float = 8.0
    starlock_thickness_reference_mm: float = 0.5
    starlock_dummy_offset_mm: float = 0.25

    intersection_limit_mm3: float = 0.01


DEFAULT = Params()
_V124 = None


def require_cadquery() -> None:
    if cq is None or exporters is None:
        raise RuntimeError(
            "CadQuery is not installed. Use --metadata-only or run in paddy-cad."
        )


def load_dependency(filename: str, module_name: str):
    path = Path(__file__).resolve().parent / "dependencies" / filename
    if not path.exists():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def v124():
    global _V124
    if _V124 is None:
        _V124 = load_dependency(
            "crawler_h1_three_knuckle_torsion_stable_link_v0_12_4.py",
            "crawler_h1_v0124_dep_for_v0125",
        )
    return _V124


def v123():
    return v124().v123()


def v122():
    return v124().v122()


def v120():
    return v124().v120()


def p_base():
    return v124().p_base()


def pivot_fit():
    return v124().pivot_fit()


def make_compound(parts: Iterable[object]):
    require_cadquery()
    values = [part.val() if hasattr(part, "val") else part for part in parts]
    return cq.Compound.makeCompound(values)


def place_on_bed(shape):
    require_cadquery()
    obj = shape.val() if hasattr(shape, "val") else shape
    bb = obj.BoundingBox()
    return shape.translate((0.0, 0.0, -bb.zmin))


def build_ear_and_root(
    axis_x_mm: float,
    center_y_mm: float,
    ear_width_y_mm: float,
):
    require_cadquery()
    p = p_base()
    dep = v120()
    lug = dep.lug_dep()

    ear = dep.cyl_y(
        p.ear_outer_diameter_mm,
        ear_width_y_mm,
    ).translate((axis_x_mm, center_y_mm, p.axis_z_mm))

    sign = 1.0 if axis_x_mm > 0.0 else -1.0
    root_center_x = (
        axis_x_mm - sign * p.ear_root_bridge_length_x_mm / 2.0
    )
    root_height = p.ear_root_top_z_mm - p.ear_root_bottom_z_mm

    root = lug.rounded_box_xy(
        p.ear_root_bridge_length_x_mm,
        ear_width_y_mm,
        root_height,
        min(3.0, ear_width_y_mm / 2.0),
    ).translate((
        root_center_x,
        center_y_mm,
        p.ear_root_bottom_z_mm,
    ))

    return ear.union(root).clean()


def build_receiver_relief(
    axis_x_mm: float,
    center_y_mm: float,
    received_width_mm: float,
):
    require_cadquery()
    p = p_base()
    dep = v120()
    lug = dep.lug_dep()

    total_y = (
        received_width_mm
        + 2.0 * DEFAULT.receiver_y_clearance_each_mm
    )
    radius = DEFAULT.receiver_relief_diameter_mm / 2.0

    main = dep.cyl_y(
        DEFAULT.receiver_relief_diameter_mm,
        total_y,
    ).translate((axis_x_mm, center_y_mm, p.axis_z_mm))

    low_y = center_y_mm - total_y / 2.0
    high_y = center_y_mm + total_y / 2.0

    low_flare = lug.cone_y(
        radius,
        radius + DEFAULT.receiver_flare_extra_radius_mm,
        DEFAULT.receiver_flare_depth_mm,
        (axis_x_mm, low_y, p.axis_z_mm),
        -1.0,
    )
    high_flare = lug.cone_y(
        radius,
        radius + DEFAULT.receiver_flare_extra_radius_mm,
        DEFAULT.receiver_flare_depth_mm,
        (axis_x_mm, high_y, p.axis_z_mm),
        +1.0,
    )

    return main.union(low_flare).union(high_flare)


def build_full_bore_cutter(axis_x_mm: float):
    require_cadquery()
    p = p_base()
    return v120().cyl_y(
        p.ear_hole_diameter_mm,
        WIDE.calculated_total_width_mm + 4.0,
    ).translate((axis_x_mm, 0.0, p.axis_z_mm))


def service_start_y_abs_mm() -> float:
    return (
        WIDE.outer_face_y_abs_mm
        + DEFAULT.service_ear_face_clearance_mm
    )


def service_length_mm() -> float:
    return DEFAULT.service_outer_y_abs_mm - service_start_y_abs_mm()


def service_center_y_mm(side_sign: float) -> float:
    return side_sign * (
        DEFAULT.service_outer_y_abs_mm + service_start_y_abs_mm()
    ) / 2.0


def build_service_access_cutter(
    axis_x_mm: float,
    side_sign: float,
):
    require_cadquery()
    p = p_base()
    return v120().cyl_y(
        DEFAULT.access_diameter_mm,
        service_length_mm(),
    ).translate((
        axis_x_mm,
        service_center_y_mm(side_sign),
        p.axis_z_mm,
    ))


def build_link(include_lug: bool = False):
    require_cadquery()
    dep = v120()
    p = p_base()
    fit = pivot_fit()

    # Preserve the complete v0.12.4 body contract.
    link = dep.build_core(p, fit)

    for sign in (-1.0, 1.0):
        link = link.cut(dep.build_half_pocket_cutter(p, fit, sign))

    for axis_x in (p.front_axis_x_mm, p.rear_axis_x_mm):
        link = link.cut(dep.build_round_floor_cutter(p, fit, axis_x))

    link = link.union(dep.build_guide(p))
    link = dep.add_lug_interface(link, p)

    # Receiving envelopes are cut before this link's own ears are restored.
    # Front outer pair receives the next link's wide centre ear.
    link = link.cut(build_receiver_relief(
        p.front_axis_x_mm,
        0.0,
        WIDE.center_ear_width_mm,
    ))

    # Rear centre ear receives the previous link's two wide outer ears.
    for y in (
        -WIDE.outer_ear_center_y_mm,
        WIDE.outer_ear_center_y_mm,
    ):
        link = link.cut(build_receiver_relief(
            p.rear_axis_x_mm,
            y,
            WIDE.outer_ear_width_mm,
        ))

    # Front: two wide outer ears.
    for y in (
        -WIDE.outer_ear_center_y_mm,
        WIDE.outer_ear_center_y_mm,
    ):
        link = link.union(build_ear_and_root(
            p.front_axis_x_mm,
            y,
            WIDE.outer_ear_width_mm,
        ))

    # Rear: one wide centre ear.
    link = link.union(build_ear_and_root(
        p.rear_axis_x_mm,
        0.0,
        WIDE.center_ear_width_mm,
    ))

    for axis_x in (p.front_axis_x_mm, p.rear_axis_x_mm):
        link = link.cut(build_full_bore_cutter(axis_x))

    link = link.cut(dep.build_identification_notch(p, fit))

    # Cut only outside the new ±23.0 mm ear faces.
    for axis_x in (p.front_axis_x_mm, p.rear_axis_x_mm):
        for side_sign in (-1.0, 1.0):
            link = link.cut(build_service_access_cutter(
                axis_x,
                side_sign,
            ))

    link = link.clean()

    if not include_lug:
        return link

    lug_dep = dep.lug_dep()
    lug_shape = lug_dep.build_lug(
        lug_dep.DEFAULT,
        lug_dep.STANDARD_CAPTURE,
        lug_dep.STANDARD_HEAD,
    ).translate((
        0.0,
        0.0,
        -lug_dep.STANDARD_CAPTURE.lug_thickness_mm,
    ))

    return make_compound([link, lug_shape])


def build_link_print():
    require_cadquery()
    return place_on_bed(
        build_link(False).rotate(
            (0, 0, 0),
            (1, 0, 0),
            180.0,
        )
    )


def linear_link(index: int, include_lug: bool = False):
    require_cadquery()
    p = p_base()
    return build_link(include_lug).translate(
        (index * p.pitch_mm, 0.0, 0.0)
    )


def build_two_link_shapes(
    angle_deg: float,
    include_lug: bool = False,
):
    require_cadquery()
    p = p_base()
    first = linear_link(0, include_lug)
    second = linear_link(1, include_lug)
    second = second.rotate(
        (p.front_axis_x_mm, 0.0, p.axis_z_mm),
        (p.front_axis_x_mm, 1.0, p.axis_z_mm),
        angle_deg,
    )
    return first, second


def build_shared_rod(
    joint_x_mm: float,
    length_mm: float = DEFAULT.shaft_reference_length_mm,
):
    require_cadquery()
    p = p_base()
    return v120().cyl_y(
        DEFAULT.shaft_reference_diameter_mm,
        length_mm,
    ).translate((joint_x_mm, 0.0, p.axis_z_mm))


def starlock_center_y_mm(side_sign: float) -> float:
    return side_sign * (
        WIDE.outer_face_y_abs_mm
        + DEFAULT.starlock_dummy_offset_mm
        + DEFAULT.starlock_thickness_reference_mm / 2.0
    )


def build_starlock_dummy(
    axis_x_mm: float,
    side_sign: float,
):
    require_cadquery()
    p = p_base()
    return v120().cyl_y(
        DEFAULT.starlock_od_reference_mm,
        DEFAULT.starlock_thickness_reference_mm,
    ).translate((
        axis_x_mm,
        starlock_center_y_mm(side_sign),
        p.axis_z_mm,
    ))


def build_tool_path_dummy(
    axis_x_mm: float,
    side_sign: float,
):
    require_cadquery()
    p = p_base()
    return v120().cyl_y(
        v123().DEFAULT.tool_nose_diameter_mm,
        service_length_mm(),
    ).translate((
        axis_x_mm,
        service_center_y_mm(side_sign),
        p.axis_z_mm,
    ))


def build_two_link_coupon():
    require_cadquery()
    p = p_base()
    first, second = build_two_link_shapes(0.0, False)

    crop = (
        cq.Workplane("XY")
        .box(32.0, 50.0, 22.0, centered=(True, True, False))
        .translate((p.front_axis_x_mm, 0.0, -2.0))
    )

    return make_compound([
        first.intersect(crop),
        second.intersect(crop),
    ])


def build_two_link_reference(angle_deg: float):
    require_cadquery()
    p = p_base()
    first, second = build_two_link_shapes(angle_deg, True)
    rod = build_shared_rod(p.front_axis_x_mm)
    return make_compound([first, second, rod])


def build_three_link_linear_reference():
    require_cadquery()
    return make_compound([
        linear_link(0, True),
        linear_link(1, True),
        linear_link(2, True),
    ])


def volume_of(shape):
    obj = shape.val() if hasattr(shape, "val") else shape
    try:
        return float(obj.Volume())
    except Exception:
        return None


def solid_count(shape):
    try:
        return len(shape.solids().vals())
    except Exception:
        return None


def geometry_validation():
    require_cadquery()
    p = p_base()
    link = build_link(False)

    articulation_rows = []
    required_angles = {5, 0, -15, -30, -35}
    for angle in (8, 5, 0, -15, -30, -35, -40):
        first, second = build_two_link_shapes(float(angle), False)
        intersection = volume_of(first.intersect(second))
        articulation_rows.append({
            "angle_deg": angle,
            "required": angle in required_angles,
            "intersection_volume_mm3": intersection,
            "clear": (
                intersection is not None
                and intersection <= DEFAULT.intersection_limit_mm3
            ),
        })

    assembly = make_compound(build_two_link_shapes(0.0, False))
    rod = build_shared_rod(p.front_axis_x_mm)
    rod_shape = rod.val() if hasattr(rod, "val") else rod
    rod_intersection = volume_of(assembly.intersect(rod_shape))

    tool_rows = []
    star_rows = []

    for axis_x in (p.front_axis_x_mm, p.rear_axis_x_mm):
        for side_sign in (-1.0, 1.0):
            tool = build_tool_path_dummy(axis_x, side_sign)
            tool_shape = tool.val() if hasattr(tool, "val") else tool
            tool_volume = volume_of(link.intersect(tool_shape))
            tool_rows.append({
                "axis_x_mm": axis_x,
                "side_sign": side_sign,
                "intersection_volume_mm3": tool_volume,
                "clear": (
                    tool_volume is not None
                    and tool_volume <= DEFAULT.intersection_limit_mm3
                ),
            })

            star = build_starlock_dummy(axis_x, side_sign)
            star_shape = star.val() if hasattr(star, "val") else star
            star_volume = volume_of(link.intersect(star_shape))
            star_rows.append({
                "axis_x_mm": axis_x,
                "side_sign": side_sign,
                "intersection_volume_mm3": star_volume,
                "clear": (
                    star_volume is not None
                    and star_volume <= DEFAULT.intersection_limit_mm3
                ),
            })

    articulation_pass = all(
        row["clear"]
        for row in articulation_rows
        if row["required"]
    )
    rod_pass = (
        rod_intersection is not None
        and rod_intersection <= DEFAULT.intersection_limit_mm3
    )
    tool_pass = all(row["clear"] for row in tool_rows)
    star_pass = all(row["clear"] for row in star_rows)

    return {
        "link_solid_count": solid_count(link),
        "link_single_solid_pass": solid_count(link) == 1,
        "outer_ear_width_mm": WIDE.outer_ear_width_mm,
        "center_ear_width_mm": WIDE.center_ear_width_mm,
        "gap_each_mm": WIDE.interleave_gap_each_mm,
        "total_width_mm": WIDE.calculated_total_width_mm,
        "outer_face_y_abs_mm": WIDE.outer_face_y_abs_mm,
        "body_edge_margin_each_mm": WIDE.body_edge_margin_each_mm,
        "guide_edge_margin_each_mm": WIDE.guide_edge_margin_each_mm,
        "articulation_rows": articulation_rows,
        "articulation_pass_plus5_to_minus35": articulation_pass,
        "rod_intersection_volume_mm3": rod_intersection,
        "rod_clearance_pass": rod_pass,
        "tool_path_rows": tool_rows,
        "tool_path_clearance_pass": tool_pass,
        "starlock_rows": star_rows,
        "starlock_clearance_pass": star_pass,
        "press_sleeve_solid_count": solid_count(
            v123().build_press_sleeve()
        ),
        "backing_cup_solid_count": solid_count(
            v123().build_backing_cup()
        ),
        "runtime_pass": (
            solid_count(link) == 1
            and articulation_pass
            and rod_pass
            and tool_pass
            and star_pass
            and solid_count(v123().build_press_sleeve()) == 1
            and solid_count(v123().build_backing_cup()) == 1
        ),
    }


def static_validation():
    p = p_base()
    old_center_span = 13.8
    old_bearing_material = 19.0
    old_total_width = 19.8

    issues = []

    def add(level: str, code: str, detail: str):
        issues.append({
            "level": level,
            "code": code,
            "detail": detail,
        })

    add(
        "PASS"
        if abs(WIDE.calculated_total_width_mm - 46.0) < 1e-9
        else "FAIL",
        "TOTAL_WIDTH_46MM",
        f"{WIDE.calculated_total_width_mm:.3f} mm",
    )
    add(
        "PASS"
        if WIDE.body_edge_margin_each_mm >= 2.0
        else "FAIL",
        "BODY_EDGE_MARGIN",
        f"{WIDE.body_edge_margin_each_mm:.3f} mm/side",
    )
    add(
        "PASS"
        if WIDE.guide_edge_margin_each_mm >= 4.0
        else "FAIL",
        "GUIDE_EDGE_MARGIN",
        f"{WIDE.guide_edge_margin_each_mm:.3f} mm/side",
    )
    add(
        "PASS" if WIDE.outer_ear_width_mm >= 10.0 else "FAIL",
        "OUTER_EAR_WIDTH",
        f"{WIDE.outer_ear_width_mm:.3f} mm × 2",
    )
    add(
        "PASS" if WIDE.center_ear_width_mm >= 24.0 else "FAIL",
        "CENTER_EAR_WIDTH",
        f"{WIDE.center_ear_width_mm:.3f} mm",
    )
    add(
        "PASS"
        if WIDE.interleave_gap_each_mm >= 0.6
        else "FAIL",
        "PRINT_CLEARANCE",
        f"{WIDE.interleave_gap_each_mm:.3f} mm/side",
    )
    add(
        "PASS" if p.pitch_mm == 20.0 else "FAIL",
        "PITCH_RETAINED",
        f"{p.pitch_mm:.3f} mm",
    )
    add(
        "PASS" if v123().gap_fit().code == "GAP-B" else "FAIL",
        "GAP_B_RETAINED",
        v123().gap_fit().code,
    )
    add(
        "PASS"
        if abs(DEFAULT.access_diameter_mm - 9.4) < 1e-9
        else "FAIL",
        "ACCESS_B_DIAMETER_RETAINED",
        f"φ{DEFAULT.access_diameter_mm:.3f} mm",
    )
    add(
        "PASS" if service_length_mm() > 0.0 else "FAIL",
        "SERVICE_ACCESS_LENGTH",
        f"{service_length_mm():.3f} mm",
    )
    add(
        "PASS"
        if DEFAULT.shaft_reference_length_mm > WIDE.calculated_total_width_mm
        else "FAIL",
        "SHAFT_LONGER_THAN_STACK",
        f"{DEFAULT.shaft_reference_length_mm:.3f} mm",
    )
    add(
        "PASS",
        "TOOLS_UNCHANGED",
        "v0.12.3 press sleeve and backing cup are reused.",
    )

    for code, detail in [
        (
            "CADQUERY_RUNTIME_NOT_RUN",
            "Actual STL/STEP and Boolean interference checks require paddy-cad.",
        ),
        (
            "WIDE_EAR_WARP_TEST_REQUIRED",
            "The 24.8 mm centre ear and 10 mm outer ears require a physical coupon.",
        ),
        (
            "RIGIDITY_NOT_CERTIFIED",
            "Wider support spacing improves geometry but is not a certified strength value.",
        ),
        (
            "SHAFT_LENGTH_PHYSICAL_FIT_REQUIRED",
            "Test 50.0, 50.5 and 51.0 mm before batch cutting.",
        ),
        (
            "STARLOCK_OD_STILL_MEASURE",
            "Confirm the actual Starlock OD and installed position.",
        ),
        (
            "MOTOR_LOAD_MUD_WATER_QUANTITY_HOLD",
            "Motor, load, mud, water and 40+8 production remain HOLD.",
        ),
    ]:
        add("WARN", code, detail)

    failures = [x for x in issues if x["level"] == "FAIL"]
    warnings = [x for x in issues if x["level"] == "WARN"]

    return {
        "package": PACKAGE_NAME,
        "version": VERSION,
        "status": STATUS,
        "result": (
            "STATIC_PASS_WITH_WARNINGS"
            if not failures
            else "STATIC_FAIL"
        ),
        "cadquery_available": cq is not None,
        "wide_knuckle": asdict(WIDE),
        "derived": {
            "outer_ear_center_y_mm": WIDE.outer_ear_center_y_mm,
            "outer_ear_center_span_mm": WIDE.outer_ear_center_span_mm,
            "outer_face_y_abs_mm": WIDE.outer_face_y_abs_mm,
            "body_edge_margin_each_mm": WIDE.body_edge_margin_each_mm,
            "guide_edge_margin_each_mm": WIDE.guide_edge_margin_each_mm,
            "bearing_material_total_mm": WIDE.total_bearing_material_mm,
            "center_span_ratio_vs_v0124": (
                WIDE.outer_ear_center_span_mm / old_center_span
            ),
            "bearing_length_ratio_vs_v0124": (
                WIDE.total_bearing_material_mm / old_bearing_material
            ),
            "total_width_ratio_vs_v0124": (
                WIDE.calculated_total_width_mm / old_total_width
            ),
            "service_start_y_abs_mm": service_start_y_abs_mm(),
            "service_length_mm": service_length_mm(),
            "shaft_reference_length_mm": (
                DEFAULT.shaft_reference_length_mm
            ),
            "shaft_fit_candidates_mm": [
                DEFAULT.shaft_fit_a_mm,
                DEFAULT.shaft_fit_b_mm,
                DEFAULT.shaft_fit_c_mm,
            ],
        },
        "issues": issues,
        "failures": len(failures),
        "warnings": len(warnings),
    }


def design_contract(validation: dict):
    return {
        "package": PACKAGE_NAME,
        "version": VERSION,
        "status": STATUS,
        "standard": "WIDE-46",
        "change_scope": [
            "three-knuckle Y span",
            "ear/root widths",
            "service-access Y start",
            "shaft reference length",
        ],
        "wide_knuckle": {
            "outer_ear_width_mm": 10.0,
            "center_ear_width_mm": 24.8,
            "gap_each_mm": 0.6,
            "total_width_mm": 46.0,
            "outer_ear_centers_y_mm": [-18.0, 18.0],
            "outer_faces_y_mm": [-23.0, 23.0],
            "body_margin_each_mm": 2.0,
            "guide_margin_each_mm": 4.0,
        },
        "unchanged": {
            "pitch_mm": 20.0,
            "axes_x_mm": [-10.0, 10.0],
            "axis_z_mm": 8.5,
            "ring_od_mm": 12.0,
            "bore_mm": 3.7,
            "GAP_B_mm": [8.2, 8.8],
            "RELIEF_B_diameter_mm": 13.2,
            "ACCESS_B_diameter_mm": 9.4,
            "side_guides": "unchanged",
            "lug": "unchanged",
            "press_sleeve": "unchanged",
            "backing_cup": "unchanged",
        },
        "shaft_fit_candidates_mm": [50.0, 50.5, 51.0],
        "first_print": (
            "WIDE_46_THREE_KNUCKLE_TWO_LINK_COUPON_PETG.stl"
        ),
        "validation_result": validation["result"],
        "hold": ["motor", "load", "mud", "water", "40+8 links"],
    }


def export_shape(shape, path: Path):
    require_cadquery()
    path.parent.mkdir(parents=True, exist_ok=True)
    exporters.export(shape, str(path))


def export_geometry(out: Path, target: str):
    require_cadquery()

    for folder in (
        "stl/petg",
        "step",
        "plates",
        "reference",
        "reports",
    ):
        (out / folder).mkdir(parents=True, exist_ok=True)

    runtime = geometry_validation()
    (out / "reports/geometry_runtime_validation.json").write_text(
        json.dumps(runtime, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Always export the cheap hinge coupon for physical diagnosis.
    if target in ("FIT_TEST", "ALL"):
        export_shape(
            place_on_bed(build_two_link_coupon()),
            out
            / "plates"
            / "WIDE_46_THREE_KNUCKLE_TWO_LINK_COUPON_PETG.stl",
        )

    if not runtime["runtime_pass"]:
        (out / "reports/GEOMETRY_HOLD_V0125.txt").write_text(
            "Runtime geometry validation failed. Full link export is HOLD.\n",
            encoding="utf-8",
        )
        return

    if target in ("PARTS", "ALL"):
        export_shape(
            build_link_print(),
            out
            / "stl"
            / "petg"
            / "STANDARD_V0125_WIDE_46_LINK.stl",
        )
        export_shape(
            build_link(False),
            out
            / "step"
            / "STANDARD_V0125_WIDE_46_LINK.step",
        )

    if target in ("FIT_TEST", "ALL"):
        export_shape(
            build_link_print(),
            out
            / "plates"
            / "V0125_SINGLE_LINK_FIT_TEST_PETG.stl",
        )

    if target in ("REFERENCES", "ALL"):
        export_shape(
            build_two_link_reference(0.0),
            out / "reference/TWO_LINK_0_DEG_REFERENCE.step",
        )
        export_shape(
            build_two_link_reference(-30.0),
            out / "reference/TWO_LINK_MINUS_30_DEG_REFERENCE.step",
        )
        export_shape(
            build_three_link_linear_reference(),
            out / "reference/THREE_LINK_LINEAR_REFERENCE.step",
        )
        export_shape(
            build_shared_rod(
                p_base().front_axis_x_mm,
                DEFAULT.shaft_reference_length_mm,
            ),
            out / "reference/SHAFT_50_5MM_REFERENCE.step",
        )


def write_metadata(out: Path, validation: dict):
    (out / "contracts").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    (
        out
        / "contracts"
        / "crawler_h1_v0_12_5_design_contract.json"
    ).write_text(
        json.dumps(
            design_contract(validation),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (out / "reports/validation_report.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_checksums(out: Path):
    lines = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(
                f"{sha256_file(path)}  "
                f"{path.relative_to(out).as_posix()}"
            )

    (out / "SHA256SUMS.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def parse_args(argv: Sequence[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--target",
        choices=("PARTS", "FIT_TEST", "REFERENCES", "ALL"),
        default="ALL",
    )
    parser.add_argument("--metadata-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None):
    args = parse_args(argv)
    validation = static_validation()
    write_metadata(args.out, validation)

    (args.out / "source").mkdir(parents=True, exist_ok=True)
    src = Path(__file__).resolve()
    dst = (args.out / "source" / src.name).resolve()
    if src != dst:
        shutil.copy2(src, dst)

    if not args.metadata_only:
        export_geometry(args.out, args.target)

    write_checksums(args.out)

    print(json.dumps({
        "version": VERSION,
        "validation": validation["result"],
        "failures": validation["failures"],
        "warnings": validation["warnings"],
        "cadquery_available": cq is not None,
        "knuckle_total_width_mm": (
            WIDE.calculated_total_width_mm
        ),
        "outer_ear_center_span_mm": (
            WIDE.outer_ear_center_span_mm
        ),
        "shaft_reference_length_mm": (
            DEFAULT.shaft_reference_length_mm
        ),
        "first_print": (
            "WIDE_46_THREE_KNUCKLE_TWO_LINK_COUPON_PETG.stl"
        ),
        "motor_load_mud_water_quantity": "HOLD",
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
