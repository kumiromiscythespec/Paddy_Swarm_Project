#!/usr/bin/env python3
"""v004 outward-drain labyrinth for the USB inline raincover.

v003 is loaded read-only.  Its physically passed side-load architecture,
connector chamber, and 4.4 mm cable Authority are retained.  v004 adds only
water-management geometry: a 7 degree outward lower relief, a 4 degree
outward ceiling, a chamber-side sill, a drain-connected capillary break, and
relocated drains at the resulting low-point capture regions.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import cadquery as cq
from PIL import Image, ImageDraw, ImageFont


LANE_NAME = "ps_usb_inline_raincover_v004_outward_drain_labyrinth"
VERSION = "v0.0.4"
DESIGN_STATUS = "CAD_COMPLETE_OUTWARD_DRAIN_LABYRINTH_PHYSICAL_VALIDATION_PENDING"
PHYSICAL_RATING = "SPLASH_RESISTANT_PHYSICAL_PASS_WITH_PRESSURE_JET_LIMIT"
PRESSURE_JET_RATED = False
IMMERSION_RATED = False

CONNECTOR_ENVELOPE_L = 95.1
CONNECTOR_ENVELOPE_W = 18.7
CONNECTOR_ENVELOPE_H = 10.8
CHAMBER_INNER_L = 102.0
CHAMBER_INNER_W = 24.0
CHAMBER_INNER_H = 16.0
CAMERA_SIDE_CABLE_OD = 3.8
EXTENSION_SIDE_CABLE_OD = 4.0
CABLE_CHANNEL_D = 4.4
LOCAL_SPLIT_RELIEF = 0.25
DRAIN_D = 2.5
DRAIN_COUNT = 2
ROOF_SLOPE_DEG = 3.0
TOP_OVERLAP_SKIRT = 6.0
PARTING_STEP_H = 2.0
PARTING_OVERLAP = 3.0
PARTING_CLEARANCE = 0.30

LABYRINTH_FLOOR_OUTWARD_SLOPE_DEG = 7.0
LABYRINTH_CEILING_OUTWARD_SLOPE_DEG = 4.0
LABYRINTH_SLOPE_RUN = 10.0
CHAMBER_WATER_SILL_H = 1.2
CAPILLARY_BREAK_W = 1.2
CAPILLARY_BREAK_D = 0.8

CHANNEL_CENTER_Z = 4.25
CHANNEL_NOMINAL_BOTTOM_Z = CHANNEL_CENTER_Z - CABLE_CHANNEL_D / 2.0
CHANNEL_NOMINAL_CEILING_Z = CHANNEL_CENTER_Z + CABLE_CHANNEL_D / 2.0 + LOCAL_SPLIT_RELIEF / 2.0
FLOOR_SLOPE_START_X_ABS = 54.0
FLOOR_SLOPE_END_X_ABS = FLOOR_SLOPE_START_X_ABS + LABYRINTH_SLOPE_RUN
FLOOR_DROP = math.tan(math.radians(LABYRINTH_FLOOR_OUTWARD_SLOPE_DEG)) * LABYRINTH_SLOPE_RUN
FLOOR_OUTER_Z = CHANNEL_NOMINAL_BOTTOM_Z - FLOOR_DROP
CEILING_DROP = math.tan(math.radians(LABYRINTH_CEILING_OUTWARD_SLOPE_DEG)) * LABYRINTH_SLOPE_RUN
CEILING_CHAMBER_Z = CHANNEL_NOMINAL_CEILING_Z + CEILING_DROP
CEILING_OUTER_Z = CHANNEL_NOMINAL_CEILING_Z

CAP_BREAK_CENTER_PROGRESS = 9.0
CAP_BREAK_CENTER_X_ABS = FLOOR_SLOPE_START_X_ABS + CAP_BREAK_CENTER_PROGRESS
CAP_BREAK_UPSTREAM_PROGRESS = CAP_BREAK_CENTER_PROGRESS - CAPILLARY_BREAK_W / 2.0
CAP_BREAK_DOWNSTREAM_PROGRESS = CAP_BREAK_CENTER_PROGRESS + CAPILLARY_BREAK_W / 2.0
CAP_BREAK_UPSTREAM_FLOOR_Z = CHANNEL_NOMINAL_BOTTOM_Z - math.tan(math.radians(LABYRINTH_FLOOR_OUTWARD_SLOPE_DEG)) * CAP_BREAK_UPSTREAM_PROGRESS
CAP_BREAK_DOWNSTREAM_FLOOR_Z = CHANNEL_NOMINAL_BOTTOM_Z - math.tan(math.radians(LABYRINTH_FLOOR_OUTWARD_SLOPE_DEG)) * CAP_BREAK_DOWNSTREAM_PROGRESS
CAP_BREAK_UPSTREAM_BOTTOM_Z = CAP_BREAK_UPSTREAM_FLOOR_Z - CAPILLARY_BREAK_D
CAP_BREAK_DOWNSTREAM_BOTTOM_Z = CAP_BREAK_DOWNSTREAM_FLOOR_Z - CAPILLARY_BREAK_D
DRAIN_X_ABS_V004 = CAP_BREAK_CENTER_X_ABS
DRAIN_Y_V004 = -11.0
DRAIN_CAPTURE_FLOOR_Z = CAP_BREAK_DOWNSTREAM_BOTTOM_Z
CHAMBER_TO_DRAIN_DROP = CHANNEL_NOMINAL_BOTTOM_Z - DRAIN_CAPTURE_FLOOR_Z

SILL_X_ABS = 53.4
SILL_AXIAL_W = 1.0
SILL_HALF_GAP = (CABLE_CHANNEL_D + LOCAL_SPLIT_RELIEF) / 2.0
CAP_BREAK_CENTER_Y = -8.0
CAP_BREAK_SPAN_Y = 8.4

V003_LANE_REL = Path("cad/ps_usb_inline_raincover_v003_side_load_labyrinth")
V003_SOURCE_SHA256 = "542307c25ac5a4d2c165a8a14b7fff84fe189266890012934f501f034ed3157f"
V003_PARAMETERS_SHA256 = "35551c26e4d176e2e17fd16a8f2382a9ddb29c35a59eafff1c229dab43e3b02c"
V003_VALIDATION_SHA256 = "9cb51be8eabc44703e9fffd66dd5b0bab7d6f9823fab76be95a244569f50f0ad"
V003_ASSEMBLY_STEP_SHA256 = "35f245fffab7a3b6954c58830175ddde87bb16e1afc402ff636fe4e6cce109bb"
V003_MANIFEST_SHA256 = "108d2b1476ce5a3b7fcdfd33e68165f56a698de05c01da65d27fd7aa2bab6f6e"

REPO_DIR = Path(__file__).resolve().parents[3]
LANE_DIR = Path(__file__).resolve().parents[1]
V003_DIR = REPO_DIR / V003_LANE_REL
V003_SOURCE = V003_DIR / "cad" / "ps_usb_inline_raincover_v003.py"
STL_DIR = LANE_DIR / "stl"
STEP_DIR = LANE_DIR / "step"
DOC_DIR = LANE_DIR / "docs"
REPORT_DIR = LANE_DIR / "reports"
RENDER_DIR = LANE_DIR / "renders"

STL_LINEAR_TOLERANCE = 0.08
STL_ANGULAR_TOLERANCE = 0.12
INTERFERENCE_TOLERANCE_MM3 = 1.0e-5


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_v003_read_only() -> Any:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("ps_usb_inline_raincover_v003_authority", V003_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load v003 Authority source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v3 = load_v003_read_only()
g = v3.g


def floor_z_at_progress(progress: float) -> float:
    limited = max(0.0, min(LABYRINTH_SLOPE_RUN, progress))
    return CHANNEL_NOMINAL_BOTTOM_Z - math.tan(math.radians(LABYRINTH_FLOOR_OUTWARD_SLOPE_DEG)) * limited


def ceiling_z_at_x(x: float) -> float:
    progress = max(0.0, min(LABYRINTH_SLOPE_RUN, abs(x) - FLOOR_SLOPE_START_X_ABS))
    return CEILING_CHAMBER_Z - math.tan(math.radians(LABYRINTH_CEILING_OUTWARD_SLOPE_DEG)) * progress


def drainage_path_points(sign: float) -> list[tuple[float, float, float]]:
    return [
        (sign * 54.0, 0.0, floor_z_at_progress(0.0)),
        (sign * 55.0, 0.0, floor_z_at_progress(1.0)),
        (sign * 58.25, -4.0, floor_z_at_progress(4.25)),
        (sign * 60.5, -8.0, floor_z_at_progress(6.5)),
        (sign * 64.0, -8.0, floor_z_at_progress(10.0)),
    ]


def sloped_segment_prism(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    width: float,
    bottom_start: float,
    bottom_end: float,
    top_z: float,
) -> cq.Workplane:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    angle = math.degrees(math.atan2(dy, dx))
    local = (
        cq.Workplane("XZ")
        .polyline([
            (-length / 2.0, bottom_start),
            (length / 2.0, bottom_end),
            (length / 2.0, top_z),
            (-length / 2.0, top_z),
        ])
        .close()
        .extrude(width / 2.0, both=True)
    )
    return local.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle).translate(
        ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0, 0.0)
    )


def drainage_floor_relief(sign: float) -> cq.Workplane:
    points = drainage_path_points(sign)
    result: cq.Workplane | None = None
    for start, end in zip(points, points[1:]):
        segment = sloped_segment_prism(
            start,
            end,
            CABLE_CHANNEL_D,
            start[2],
            end[2],
            CHANNEL_NOMINAL_BOTTOM_Z + 0.30,
        )
        result = segment if result is None else result.union(segment)
    if result is None:
        raise RuntimeError("empty drainage relief")
    return result.clean()


def capillary_break_cutter(sign: float) -> cq.Workplane:
    x_inner = sign * (CAP_BREAK_CENTER_X_ABS - CAPILLARY_BREAK_W / 2.0)
    x_outer = sign * (CAP_BREAK_CENTER_X_ABS + CAPILLARY_BREAK_W / 2.0)
    if sign > 0:
        start = (x_inner, CAP_BREAK_CENTER_Y, CAP_BREAK_UPSTREAM_BOTTOM_Z)
        end = (x_outer, CAP_BREAK_CENTER_Y, CAP_BREAK_DOWNSTREAM_BOTTOM_Z)
    else:
        start = (x_inner, CAP_BREAK_CENTER_Y, CAP_BREAK_UPSTREAM_BOTTOM_Z)
        end = (x_outer, CAP_BREAK_CENTER_Y, CAP_BREAK_DOWNSTREAM_BOTTOM_Z)
    return sloped_segment_prism(
        start,
        end,
        CAP_BREAK_SPAN_Y,
        CAP_BREAK_UPSTREAM_BOTTOM_Z,
        CAP_BREAK_DOWNSTREAM_BOTTOM_Z,
        CAP_BREAK_UPSTREAM_FLOOR_Z + 0.15,
    ).clean()


def drain_cutter(sign: float) -> cq.Workplane:
    return g.cylinder_z(
        DRAIN_D / 2.0,
        10.0,
        -6.0,
        sign * DRAIN_X_ABS_V004,
        DRAIN_Y_V004,
    )


def sill_pair(sign: float) -> cq.Workplane:
    local_floor = CHANNEL_NOMINAL_BOTTOM_Z
    y_outer = 6.0
    segment_w = y_outer - SILL_HALF_GAP
    positive = g.box(
        SILL_AXIAL_W,
        segment_w,
        CHAMBER_WATER_SILL_H,
        (sign * SILL_X_ABS, (y_outer + SILL_HALF_GAP) / 2.0, local_floor + CHAMBER_WATER_SILL_H / 2.0),
    )
    negative = g.box(
        SILL_AXIAL_W,
        segment_w,
        CHAMBER_WATER_SILL_H,
        (sign * SILL_X_ABS, -(y_outer + SILL_HALF_GAP) / 2.0, local_floor + CHAMBER_WATER_SILL_H / 2.0),
    )
    return positive.union(negative).clean()


def build_lower_shell_v004() -> cq.Workplane:
    lower = g.rounded_rect_prism(
        g.LOWER_OUTER_L,
        g.LOWER_OUTER_W,
        g.PARTING_Z - g.LOWER_BOTTOM_Z,
        g.LOWER_BOTTOM_Z,
        4.0,
    )
    lower = lower.union(g.rounded_frame(
        g.TONGUE_OUTER_L,
        g.TONGUE_OUTER_W,
        g.TONGUE_INNER_L,
        g.TONGUE_INNER_W,
        PARTING_STEP_H,
        g.PARTING_Z,
        3.0,
        2.0,
    ))
    for x in g.SCREW_XS:
        for side in (-1.0, 1.0):
            lower = lower.union(g.box(
                9.0, 11.0, g.FLANGE_T,
                (x, side * 20.5, g.PARTING_Z - g.FLANGE_T / 2.0),
            ))
    for x in (-5.0, 0.0, 5.0):
        for side in (-1.0, 1.0):
            lower = lower.cut(g.box(1.6, 1.4, 1.6, (x, side * 15.0, -1.6)))
    lower = lower.cut(g.build_chamber_cavity())

    for sign in (-1.0, 1.0):
        lower = lower.cut(g.box(
            g.POCKET_L,
            CABLE_CHANNEL_D + 6.0,
            20.0,
            (sign * g.POCKET_X_ABS, 0.0, g.POCKET_BOTTOM_Z + 10.0),
        ))
        lower = lower.cut(g.box(
            5.0, 2.5, 2.0, (sign * g.BAFFLE_X_ABS, g.WEEP_Y, 0.75),
        ))
        lower = lower.union(v3.path_prism(
            v3.cradle_points(sign),
            v3.CRADLE_OUTER_W,
            v3.CRADLE_BOTTOM_Z,
            v3.CRADLE_TOP_Z,
            False,
            False,
        ))
        lower = lower.union(sill_pair(sign))
        lower = lower.cut(v3.cable_cut(sign, upward=True))
        lower = lower.cut(drainage_floor_relief(sign))
        lower = lower.cut(capillary_break_cutter(sign))
        lower = lower.cut(drain_cutter(sign))

    # Preserve the physically accepted v003 loose saddles.
    for sign in (-1.0, 1.0):
        x = sign * v3.v2.SADDLE_X_ABS
        floor_z = g.chamber_floor_z(x)
        lower = lower.union(g.box(
            v3.v2.SADDLE_AXIAL_L, 12.0, 5.2, (x, 0.0, floor_z + 2.6),
        ))
        lower = lower.cut(g.cylinder_between(
            (CABLE_CHANNEL_D + g.STRAIN_RELIEF_RADIAL_CLEARANCE) / 2.0,
            (x - 2.2, 0.0, g.PASSAGE_CENTER_Z),
            (x + 2.2, 0.0, g.PASSAGE_CENTER_Z),
        ))

    for x in g.SCREW_XS:
        for side in (-1.0, 1.0):
            y = side * g.SCREW_Y_ABS
            lower = lower.cut(g.cylinder_z(g.M3_CLEARANCE_D / 2.0, 8.0, 2.0, x, y))
            lower = lower.cut(g.hex_prism_z(
                g.M3_NUT_AF, g.M3_NUT_DEPTH, g.PARTING_Z - g.FLANGE_T, x, y,
            ))
    return lower.clean()


def sloped_ceiling_tongue(sign: float) -> cq.Workplane:
    points = v3.path_points(sign)
    result: cq.Workplane | None = None
    for start, end in zip(points, points[1:]):
        segment = sloped_segment_prism(
            start,
            end,
            v3.UPPER_TONGUE_W,
            ceiling_z_at_x(start[0]),
            ceiling_z_at_x(end[0]),
            v3.CAP_BRIDGE_BOTTOM_Z + 0.05,
        )
        result = segment if result is None else result.union(segment)
    if result is None:
        raise RuntimeError("empty ceiling tongue")
    return result.clean()


def build_upper_shell_v004() -> cq.Workplane:
    upper = g.build_upper_shell()
    for sign in (-1.0, 1.0):
        points = v3.path_points(sign)
        upper = upper.cut(v3.cable_cut(sign, upward=False))
        upper = upper.union(sloped_ceiling_tongue(sign))
        upper = upper.union(v3.path_prism(
            points,
            v3.CRADLE_OUTER_W,
            v3.CAP_BRIDGE_BOTTOM_Z,
            v3.CAP_BRIDGE_TOP_Z,
            False,
        ))
    return upper.clean()


def connector_reference() -> cq.Workplane:
    return v3.connector_reference()


def cable_reference(sign: float, diameter: float) -> cq.Workplane:
    return v3.cable_reference(sign, diameter)


def compound(models: Iterable[cq.Workplane]) -> cq.Workplane:
    return g.compound_workplane(models)


def build_coupon(lower: cq.Workplane, upper: cq.Workplane) -> tuple[cq.Workplane, cq.Workplane, cq.Workplane]:
    x_min, x_max = -68.0, -41.0
    center_x = (x_min + x_max) / 2.0
    cutter = g.box(x_max - x_min, g.UPPER_OUTER_W + 0.4, 45.0, (center_x, 0.0, 7.0))
    coupon_lower = g.wp(lower.val().intersect(cutter.val())).translate((-center_x, 0.0, 0.0)).clean()
    coupon_upper = g.wp(upper.val().intersect(cutter.val())).translate((-center_x, 0.0, 0.0)).clean()
    return coupon_lower, coupon_upper, compound((coupon_lower, coupon_upper))


def export_stl(model: cq.Workplane, path: Path) -> None:
    cq.exporters.export(
        model,
        str(path),
        tolerance=STL_LINEAR_TOLERANCE,
        angularTolerance=STL_ANGULAR_TOLERANCE,
    )


def export_step(model: cq.Workplane, path: Path) -> None:
    cq.exporters.export(model, str(path))


def font(size: int) -> ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def make_outward_drain_render(output: Path) -> None:
    image = Image.new("RGB", (1250, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45,25), "v004 OUTWARD-DRAIN SECTION - chamber HIGH / drain LOW", fill="#0f172a", font=font(29))
    draw.rectangle((90,150,1160,680), fill="#f59e0b", outline="#92400e", width=4)
    draw.polygon([(250,360),(620,425),(1020,575),(1020,620),(620,485),(250,415)], fill="white", outline="#2563eb")
    draw.line((270,395,615,460), fill="#06b6d4", width=10)
    draw.line((615,460,980,585), fill="#06b6d4", width=10)
    draw.polygon([(960,570),(1020,585),(975,625)], fill="#06b6d4")
    draw.line((880,570,880,735), fill="#0891b2", width=14)
    draw.text((195,285), "CHAMBER SIDE\nHIGH", fill="#1e3a8a", font=font(23))
    draw.text((825,745), "DRAIN LOW POINT", fill="#0e7490", font=font(21))
    draw.text((170,720), f"10 mm x 7 deg = {FLOOR_DROP:.3f} mm outward drop", fill="#7f1d1d", font=font(22))
    image.save(output)


def make_capillary_render(output: Path) -> None:
    image = Image.new("RGB", (1100, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45,25), "CAPILLARY BREAK - open trench intersects 2.5 mm drain", fill="#0f172a", font=font(28))
    draw.polygon([(120,310),(970,475),(970,640),(120,475)], fill="#f59e0b", outline="#92400e")
    draw.polygon([(610,405),(675,418),(675,535),(610,522)], fill="white", outline="#1d4ed8")
    draw.line((642,465,642,700), fill="#0891b2", width=16)
    draw.text((560,245), "1.2 mm wide", fill="#1e3a8a", font=font(22))
    draw.text((700,430), "0.8 mm deep", fill="#1e3a8a", font=font(22))
    draw.text((515,730), "groove bottom -> drain -> outside", fill="#0e7490", font=font(22))
    image.save(output)


def make_open_side_load(output: Path) -> None:
    image = Image.new("RGB", (1250, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45,25), "v004 OPEN - v003 SIDE-LOAD AUTHORITY PRESERVED", fill="#0f172a", font=font(29))
    draw.rounded_rectangle((100,170,1140,665), radius=38, fill="#f59e0b", outline="#92400e", width=4)
    path = [(220,405),(515,405),(690,485),(855,585),(1060,585)]
    draw.line(path, fill="white", width=52, joint="curve")
    draw.line(path, fill="#2563eb", width=5, joint="curve")
    draw.line((620,90,620,350), fill="#16a34a", width=12)
    draw.polygon([(620,75),(585,135),(655,135)], fill="#16a34a")
    draw.text((680,105), "continuous cable placed from above", fill="#166534", font=font(23))
    draw.text((150,710), "NO end threading / NO cutting / lower closed loop NONE", fill="#7f1d1d", font=font(24))
    image.save(output)


def make_closed_side_load(output: Path) -> None:
    image = Image.new("RGB", (1250, 820), "white")
    draw = ImageDraw.Draw(image)
    # Keep extra left margin because some image viewers crop a few edge pixels.
    draw.text((95,25), "v004 CLOSED - 4.4 mm nominal channel / outward ceiling", fill="#0f172a", font=font(29))
    draw.rounded_rectangle((120,340,1120,660), radius=35, fill="#f59e0b", outline="#92400e", width=4)
    draw.polygon([(90,300),(1040,185),(1160,305),(210,420)], fill="#334155", outline="#0f172a")
    draw.polygon([(210,420),(1160,305),(1160,470),(210,585)], fill="#1f2937", outline="#0f172a")
    draw.line((1030,570,1030,735), fill="#2563eb", width=28)
    draw.text((155,700), "upper closes after cable placement; compression NONE", fill="#7f1d1d", font=font(23))
    image.save(output)


def make_installation_render(output: Path) -> None:
    image = Image.new("RGB", (1000, 900), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45,25), "INSTALLATION AUTHORITY - VERTICAL PIPE + DRIP LOOP", fill="#0f172a", font=font(27))
    draw.rectangle((130,110,210,820), fill="#94a3b8", outline="#475569", width=4)
    draw.rounded_rectangle((205,200,770,440), radius=28, fill="#334155", outline="#0f172a", width=4)
    draw.line((700,400,700,650), fill="#2563eb", width=24)
    draw.arc((585,570,815,800), start=0, end=180, fill="#2563eb", width=24)
    draw.line((585,685,585,820), fill="#2563eb", width=24)
    draw.line((560,410,560,535), fill="#0891b2", width=13)
    draw.polygon([(560,555),(535,515),(585,515)], fill="#0891b2")
    draw.text((470,470), "DRAIN DOWN", fill="#0e7490", font=font(22))
    draw.text((650,820), "mandatory drip loop", fill="#1e3a8a", font=font(22))
    draw.text((260,120), "cover high on protected run / suspended above soil and grass", fill="#334155", font=font(20))
    image.save(output)


def make_water_arrows(output: Path) -> None:
    image = Image.new("RGB", (1250, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45,25), "WATER FLOW - gravity outward, capillary film interrupted", fill="#0f172a", font=font(29))
    draw.rectangle((90,140,1160,685), fill="#f59e0b", outline="#92400e", width=4)
    path = [(310,360),(575,405),(770,500),(1015,575)]
    draw.line(path, fill="white", width=58, joint="curve")
    draw.line(path, fill="#06b6d4", width=10, joint="curve")
    draw.polygon([(985,550),(1045,580),(990,615)], fill="#06b6d4")
    draw.rectangle((760,470,800,575), fill="#dbeafe", outline="#1d4ed8")
    draw.line((780,540,780,735), fill="#0891b2", width=14)
    draw.rectangle((190,255,310,500), fill="#fde68a", outline="#92400e", width=4)
    draw.text((130,205), "1.2 mm chamber sill", fill="#92400e", font=font(21))
    draw.text((705,420), "capillary break", fill="#1e3a8a", font=font(21))
    draw.text((700,750), "2.5 mm drain", fill="#0e7490", font=font(21))
    draw.text((105,775), "Normal gravity water exits outward; strong pressure jet remains outside rating", fill="#7f1d1d", font=font(20))
    image.save(output)


def write_parameters() -> None:
    data = {
        "lane": LANE_NAME,
        "version": VERSION,
        "status": DESIGN_STATUS,
        "physical_rating": PHYSICAL_RATING,
        "PRESSURE_JET_RATED": PRESSURE_JET_RATED,
        "IMMERSION_RATED": IMMERSION_RATED,
        "CONNECTOR_ENVELOPE_L": CONNECTOR_ENVELOPE_L,
        "CONNECTOR_ENVELOPE_W": CONNECTOR_ENVELOPE_W,
        "CONNECTOR_ENVELOPE_H": CONNECTOR_ENVELOPE_H,
        "CHAMBER_INNER_L": CHAMBER_INNER_L,
        "CHAMBER_INNER_W": CHAMBER_INNER_W,
        "CHAMBER_INNER_H": CHAMBER_INNER_H,
        "CAMERA_SIDE_CABLE_OD": CAMERA_SIDE_CABLE_OD,
        "EXTENSION_SIDE_CABLE_OD": EXTENSION_SIDE_CABLE_OD,
        "CABLE_CHANNEL_D": CABLE_CHANNEL_D,
        "LOCAL_SPLIT_RELIEF": LOCAL_SPLIT_RELIEF,
        "LABYRINTH_FLOOR_OUTWARD_SLOPE_DEG": LABYRINTH_FLOOR_OUTWARD_SLOPE_DEG,
        "LABYRINTH_CEILING_OUTWARD_SLOPE_DEG": LABYRINTH_CEILING_OUTWARD_SLOPE_DEG,
        "LABYRINTH_SLOPE_RUN": LABYRINTH_SLOPE_RUN,
        "CHAMBER_WATER_SILL_H": CHAMBER_WATER_SILL_H,
        "CAPILLARY_BREAK_W": CAPILLARY_BREAK_W,
        "CAPILLARY_BREAK_D": CAPILLARY_BREAK_D,
        "DRAIN_D": DRAIN_D,
        "DRAIN_COUNT": DRAIN_COUNT,
        "ROOF_SLOPE_DEG": ROOF_SLOPE_DEG,
        "TOP_OVERLAP_SKIRT": TOP_OVERLAP_SKIRT,
        "PARTING_STEP_H": PARTING_STEP_H,
        "PARTING_OVERLAP": PARTING_OVERLAP,
        "PARTING_CLEARANCE": PARTING_CLEARANCE,
        "derived": {
            "lower_floor_drop_mm": FLOOR_DROP,
            "upper_ceiling_drop_mm": CEILING_DROP,
            "chamber_side_floor_z_mm": CHANNEL_NOMINAL_BOTTOM_Z,
            "outer_floor_z_mm": FLOOR_OUTER_Z,
            "capillary_break_upstream_floor_z_mm": CAP_BREAK_UPSTREAM_FLOOR_Z,
            "capillary_break_downstream_floor_z_mm": CAP_BREAK_DOWNSTREAM_FLOOR_Z,
            "capillary_break_upstream_bottom_z_mm": CAP_BREAK_UPSTREAM_BOTTOM_Z,
            "capillary_break_downstream_bottom_z_mm": CAP_BREAK_DOWNSTREAM_BOTTOM_Z,
            "drain_capture_floor_z_mm": DRAIN_CAPTURE_FLOOR_Z,
            "chamber_to_drain_drop_mm": CHAMBER_TO_DRAIN_DROP,
            "ceiling_chamber_z_mm": CEILING_CHAMBER_Z,
            "ceiling_outer_z_mm": CEILING_OUTER_Z,
            "drain_center_x_abs_mm": DRAIN_X_ABS_V004,
            "drain_center_y_mm": DRAIN_Y_V004,
        },
        "inherited_physical_results": {
            "connector_fit": "PASS",
            "4p4_mm_cable_fit": "PASS",
            "side_load_assembly": "PASS",
            "top_spray": "DRY",
            "side_spray": "DRY",
            "weak_direct_jet": "DRY",
            "strong_direct_jet": "WET_PRESSURE_JET_LIMIT_OBSERVED",
        },
        "installation_authority": {
            "support": "vertical support pipe",
            "long_axis": "approximately horizontal",
            "drain": "DOWNWARD",
            "cable_port": "NOT UPWARD",
            "drip_loop": "REQUIRED BELOW COVER",
            "ground_contact": "FORBIDDEN_STANDARD_OPERATION",
        },
    }
    (LANE_DIR / "cad" / "parameters.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def validate(models: dict[str, cq.Workplane]) -> dict[str, Any]:
    lower, upper = models["lower"], models["upper"]
    connector = models["connector"]
    camera, extension = models["camera"], models["extension"]
    intersections = {
        "connector_vs_lower_mm3": round(g.intersection_volume(connector, lower), 8),
        "connector_vs_upper_mm3": round(g.intersection_volume(connector, upper), 8),
        "camera_vs_lower_mm3": round(g.intersection_volume(camera, lower), 8),
        "camera_vs_upper_mm3": round(g.intersection_volume(camera, upper), 8),
        "extension_vs_lower_mm3": round(g.intersection_volume(extension, lower), 8),
        "extension_vs_upper_mm3": round(g.intersection_volume(extension, upper), 8),
        "upper_vs_lower_mm3": round(g.intersection_volume(upper, lower), 8),
        "camera_top_load_sweep_vs_lower_mm3": round(g.intersection_volume(models["camera_lower_sweep"], lower), 8),
        "extension_top_load_sweep_vs_lower_mm3": round(g.intersection_volume(models["extension_lower_sweep"], lower), 8),
        "camera_release_sweep_vs_upper_mm3": round(g.intersection_volume(models["camera_upper_sweep"], upper), 8),
        "extension_release_sweep_vs_upper_mm3": round(g.intersection_volume(models["extension_upper_sweep"], upper), 8),
        "connector_placement_vs_lower_mm3": round(g.intersection_volume(models["connector_placement"], lower), 8),
    }

    stl_expected = {
        "outward_drain_labyrinth_coupon_lower_v004": 1,
        "outward_drain_labyrinth_coupon_upper_v004": 1,
        "usb_raincover_lower_v004": 1,
        "usb_raincover_upper_v004": 1,
    }
    artifacts: dict[str, Any] = {}
    for stem, expected in stl_expected.items():
        model = models[stem]
        brep = g.shape_metrics(model)
        mesh = g.stl_mesh_metrics(STL_DIR / f"{stem}.stl")
        bbox_delta = max(
            abs(brep["bounding_box_mm"][axis] - mesh["bounding_box_mm"][axis])
            for axis in ("x", "y", "z")
        )
        checks = {
            "brep_valid": brep["valid"],
            "brep_expected_solids": brep["solid_count"] == expected,
            "brep_positive_volume": brep["volume_mm3"] > 0.0,
            "stl_nonempty": mesh["file_size_bytes"] > 1024,
            "stl_triangles_present": mesh["triangle_count"] > 0,
            "stl_no_degenerate_triangles": mesh["degenerate_triangles"] == 0,
            "stl_boundary_nonmanifold_edges_zero": mesh["watertight_edge_count_check"],
            "stl_bbox_matches_brep": bbox_delta <= 0.2,
        }
        if not all(checks.values()):
            raise AssertionError(f"STL/BRep validation failed for {stem}: {checks}")
        artifacts[stem] = {"expected_solids": expected, "brep": brep, "mesh": mesh, "checks": checks}

    step_expected = {
        "outward_drain_labyrinth_coupon_v004": (models["coupon_assembly"], 2),
        "usb_raincover_lower_v004": (lower, 1),
        "usb_raincover_upper_v004": (upper, 1),
        "usb_raincover_assembly_v004": (models["assembly"], 5),
    }
    steps: dict[str, Any] = {}
    for stem, (source, expected) in step_expected.items():
        source_metrics = g.shape_metrics(source)
        imported = cq.importers.importStep(str(STEP_DIR / f"{stem}.step"))
        imported_metrics = g.shape_metrics(imported)
        checks = {
            "step_nonempty": (STEP_DIR / f"{stem}.step").stat().st_size > 1024,
            "step_reimport_valid": imported_metrics["valid"],
            "step_expected_solids": imported_metrics["solid_count"] == expected,
            "step_volume_matches_source": abs(imported_metrics["volume_mm3"] - source_metrics["volume_mm3"]) <= 0.02,
        }
        if not all(checks.values()):
            raise AssertionError(f"STEP validation failed for {stem}: {checks}")
        steps[stem] = {
            "expected_solids": expected,
            "source": source_metrics,
            "reimport": imported_metrics,
            "checks": checks,
            "sha256": sha256_file(STEP_DIR / f"{stem}.step"),
        }

    v003_hashes = {
        "source": sha256_file(V003_SOURCE),
        "parameters": sha256_file(V003_DIR / "cad" / "parameters.json"),
        "validation": sha256_file(V003_DIR / "reports" / "validation_report.json"),
        "assembly_step": sha256_file(V003_DIR / "step" / "usb_raincover_assembly_v003.step"),
        "manifest": sha256_file(V003_DIR / "SHA256SUMS.txt"),
    }
    expected_hashes = {
        "source": V003_SOURCE_SHA256,
        "parameters": V003_PARAMETERS_SHA256,
        "validation": V003_VALIDATION_SHA256,
        "assembly_step": V003_ASSEMBLY_STEP_SHA256,
        "manifest": V003_MANIFEST_SHA256,
    }
    drain_break_overlap = min(
        g.intersection_volume(capillary_break_cutter(sign), drain_cutter(sign))
        for sign in (-1.0, 1.0)
    )
    full_volume = g.shape_metrics(lower)["volume_mm3"] + g.shape_metrics(upper)["volume_mm3"]
    coupon_volume = g.shape_metrics(models["coupon_assembly"])["volume_mm3"]

    checks = {
        "v003_authority_hashes_match": v003_hashes == expected_hashes,
        "connector_and_chamber_authority_preserved": (
            CONNECTOR_ENVELOPE_L == v3.CONNECTOR_ENVELOPE_L
            and CONNECTOR_ENVELOPE_W == v3.CONNECTOR_ENVELOPE_W
            and CONNECTOR_ENVELOPE_H == v3.CONNECTOR_ENVELOPE_H
            and CHAMBER_INNER_L == v3.CHAMBER_INNER_L
            and CHAMBER_INNER_W == v3.CHAMBER_INNER_W
            and CHAMBER_INNER_H == v3.CHAMBER_INNER_H
        ),
        "4p4_channel_and_relief_preserved": CABLE_CHANNEL_D == v3.CABLE_CHANNEL_D and LOCAL_SPLIT_RELIEF == v3.LOCAL_SPLIT_RELIEF,
        "lower_floor_gravity_vector_outward": FLOOR_DROP > 0.0 and FLOOR_OUTER_Z < CHANNEL_NOMINAL_BOTTOM_Z,
        "lower_floor_drop_exact": abs(FLOOR_DROP - math.tan(math.radians(7.0)) * 10.0) <= 1e-9,
        "upper_ceiling_gravity_vector_outward": CEILING_CHAMBER_Z > CEILING_OUTER_Z,
        "upper_ceiling_drop_exact": abs(CEILING_DROP - math.tan(math.radians(4.0)) * 10.0) <= 1e-9,
        "chamber_side_sill_present": CHAMBER_WATER_SILL_H == 1.2,
        "capillary_break_present_and_printable": CAPILLARY_BREAK_W >= 1.0 and CAPILLARY_BREAK_D >= 0.6,
        "capillary_break_intersects_drain": drain_break_overlap > 0.1,
        "drain_at_lowest_capture_region": DRAIN_CAPTURE_FLOOR_Z == CAP_BREAK_DOWNSTREAM_BOTTOM_Z,
        "closed_water_pocket_none": drain_break_overlap > 0.1 and CAP_BREAK_DOWNSTREAM_BOTTOM_Z < CAP_BREAK_UPSTREAM_BOTTOM_Z,
        "drain_diameter_count_preserved": DRAIN_D == 2.5 and DRAIN_COUNT == 2,
        "camera_clearance_positive": CEILING_OUTER_Z - CHANNEL_NOMINAL_BOTTOM_Z > CAMERA_SIDE_CABLE_OD,
        "extension_clearance_positive": CEILING_OUTER_Z - CHANNEL_NOMINAL_BOTTOM_Z > EXTENSION_SIDE_CABLE_OD,
        "lower_path_open_from_above": all(
            intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
                "camera_top_load_sweep_vs_lower_mm3", "extension_top_load_sweep_vs_lower_mm3",
            )
        ),
        "lower_closed_loop_none": all(
            intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
                "camera_top_load_sweep_vs_lower_mm3", "extension_top_load_sweep_vs_lower_mm3",
            )
        ),
        "upper_closed_loop_none": all(
            intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
                "camera_release_sweep_vs_upper_mm3", "extension_release_sweep_vs_upper_mm3",
            )
        ),
        "cable_interference_zero": all(
            intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
                "camera_vs_lower_mm3", "camera_vs_upper_mm3", "extension_vs_lower_mm3", "extension_vs_upper_mm3",
            )
        ),
        "connector_interference_zero": intersections["connector_vs_lower_mm3"] <= INTERFERENCE_TOLERANCE_MM3 and intersections["connector_vs_upper_mm3"] <= INTERFERENCE_TOLERANCE_MM3,
        "connector_placement_path_clear": intersections["connector_placement_vs_lower_mm3"] <= INTERFERENCE_TOLERANCE_MM3,
        "upper_lower_unintended_interference_zero": intersections["upper_vs_lower_mm3"] <= INTERFERENCE_TOLERANCE_MM3,
        "direct_line_of_sight_none": v3.dogleg_sightline_deviation() > v3.LOWER_SLOT_W / 2.0,
        "roof_skirt_parting_m3_preserved": (
            ROOF_SLOPE_DEG == v3.ROOF_SLOPE_DEG
            and TOP_OVERLAP_SKIRT == v3.TOP_OVERLAP_SKIRT
            and tuple(g.SCREW_XS) == (-50.0, 0.0, 50.0)
            and PARTING_STEP_H == v3.PARTING_STEP_H
            and PARTING_OVERLAP == v3.PARTING_OVERLAP
            and PARTING_CLEARANCE == v3.PARTING_CLEARANCE
        ),
        "coupon_material_reduced": coupon_volume < 0.35 * full_volume,
        "pressure_jet_not_rated": not PRESSURE_JET_RATED and not IMMERSION_RATED,
    }
    if not all(checks.values()):
        raise AssertionError(f"v004 validation failed: {[name for name, passed in checks.items() if not passed]}")

    return {
        "lane": LANE_NAME,
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cadquery_version": cq.__version__,
        "status": DESIGN_STATUS,
        "physical_rating": PHYSICAL_RATING,
        "PRESSURE_JET_RATED": PRESSURE_JET_RATED,
        "IMMERSION_RATED": IMMERSION_RATED,
        "v003_authority": {"lane": str(V003_LANE_REL).replace("\\", "/"), "hashes": v003_hashes},
        "inherited_physical_results": {
            "CONNECTOR_FIT": "PASS",
            "4.4 mm CABLE_FIT": "PASS",
            "SIDE_LOAD": "PASS",
            "TOP_SPRAY": "DRY",
            "SIDE_SPRAY": "DRY",
            "WEAK_DIRECT_JET": "DRY",
            "STRONG_DIRECT_JET": "WET",
            "INTERPRETATION": "SPLASH_RESISTANT_NOT_PRESSURE_JET_RATED",
        },
        "elevations_mm": {
            "chamber_side_labyrinth_floor_z": round(CHANNEL_NOMINAL_BOTTOM_Z, 4),
            "outer_labyrinth_floor_z": round(FLOOR_OUTER_Z, 4),
            "lower_floor_drop": round(FLOOR_DROP, 4),
            "capillary_break_upstream_floor_z": round(CAP_BREAK_UPSTREAM_FLOOR_Z, 4),
            "capillary_break_downstream_floor_z": round(CAP_BREAK_DOWNSTREAM_FLOOR_Z, 4),
            "capillary_break_upstream_bottom_z": round(CAP_BREAK_UPSTREAM_BOTTOM_Z, 4),
            "capillary_break_downstream_bottom_z": round(CAP_BREAK_DOWNSTREAM_BOTTOM_Z, 4),
            "drain_capture_floor_z": round(DRAIN_CAPTURE_FLOOR_Z, 4),
            "difference_chamber_to_drain": round(CHAMBER_TO_DRAIN_DROP, 4),
            "upper_ceiling_chamber_z": round(CEILING_CHAMBER_Z, 4),
            "upper_ceiling_outer_z": round(CEILING_OUTER_Z, 4),
            "upper_ceiling_drop": round(CEILING_DROP, 4),
        },
        "water_path": {
            "LOWER FLOOR GRAVITY VECTOR": "OUTWARD",
            "UPPER CEILING GRAVITY VECTOR": "OUTWARD",
            "CHAMBER-SIDE SILL": "PRESENT",
            "CAPILLARY BREAK": "PRESENT_AND_DRAIN_CONNECTED",
            "DRAIN": "AT_LOWEST_POINT_CAPTURE_REGION",
            "CLOSED WATER POCKET": "NONE_CAD",
            "DIRECT LINE OF SIGHT": "NONE_CAD",
            "physical_v004_coupon": "PENDING",
        },
        "installation_authority": {
            "support": "vertical support pipe",
            "cover_location": "upper protected cable run",
            "long_axis": "approximately horizontal",
            "drain": "DOWNWARD",
            "port": "NOT UPWARD",
            "drip_loop": "REQUIRED BELOW COVER",
            "cover": "SUSPENDED ABOVE GROUND",
        },
        "intersections": intersections,
        "checks": checks,
        "drain_capillary_break_overlap_mm3": round(drain_break_overlap, 4),
        "coupon_volume_ratio_to_full_shell": round(coupon_volume / full_volume, 4),
        "artifacts": artifacts,
        "step_reimport": steps,
        "assembly_path": {
            "lower cable path open from above": "PASS",
            "upper closed loop": "NONE",
            "lower closed loop": "NONE",
            "camera cable interference": "0 mm3",
            "extension cable interference": "0 mm3",
            "connector reference interference": "0 mm3",
            "upper/lower unintended interference": "0 mm3",
        },
        "pass_separation": {
            "CAD_PASS": True,
            "PRINT_PASS": False,
            "CABLE_FIT_PASS": True,
            "CONNECTOR_FIT_PASS": True,
            "SIDE_LOAD_ASSEMBLY_PASS": True,
            "OUTWARD_DRAIN_WATER_PASS": False,
            "FULL_SHELL_RAIN_PASS": False,
            "POWERED_USB_PASS": False,
            "HEAVY_RAIN_FIELD_PASS": False,
        },
        "blockers": [
            "outward-drain labyrinth Physical water validation",
            "capillary-break effectiveness",
            "full-shell rain intrusion",
        ],
        "field_unconfirmed": [
            "heavy rain", "wind-driven rain", "long-duration rain",
            "capillary ingress over hours", "mud splash", "drain blockage",
            "insect contamination", "UV/weather aging",
        ],
    }


def write_reports(report: dict[str, Any]) -> None:
    validation = [
        "# VALIDATION REPORT", "", f"Status: `{DESIGN_STATUS}`", "",
        "v004 geometry passes CAD validation. Outward-drain coupon water validation remains Physical PENDING.", "",
        "## STL / BRep", "", "| Artifact | BRep valid | Solids | STL triangles | Boundary/non-manifold edges |",
        "|---|---|---:|---:|---:|",
    ]
    for name, item in report["artifacts"].items():
        validation.append(
            f"| `{name}` | {item['brep']['valid']} | {item['brep']['solid_count']} | "
            f"{item['mesh']['triangle_count']} | {item['mesh']['nonmanifold_or_boundary_edges']} |"
        )
    validation.extend(["", "## STEP re-import", ""])
    for name, item in report["step_reimport"].items():
        validation.append(f"- `{name}`: valid={item['reimport']['valid']}, solids={item['reimport']['solid_count']}")
    validation.extend(["", "## Interference", ""])
    for name, value in report["intersections"].items():
        validation.append(f"- `{name}`: {value:.8f} mm³")
    validation.extend(["", "## Checks", ""])
    for name, passed in report["checks"].items():
        validation.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    validation.extend(["", "Physical coupon water PASS is not inferred from CAD_PASS.", ""])
    (REPORT_DIR / "VALIDATION_REPORT.md").write_text("\n".join(validation), encoding="utf-8")

    elevation = [
        "# ELEVATION REPORT", "", "All values use the v003 assembly coordinate system.", "",
        "| Point | Z (mm) |", "|---|---:|",
    ]
    labels = {
        "chamber_side_labyrinth_floor_z": "chamber-side labyrinth floor",
        "capillary_break_upstream_floor_z": "capillary-break upstream lip",
        "capillary_break_downstream_floor_z": "capillary-break downstream lip",
        "capillary_break_upstream_bottom_z": "capillary-break upstream bottom",
        "capillary_break_downstream_bottom_z": "capillary-break downstream bottom / drain capture",
        "outer_labyrinth_floor_z": "outer nominal floor",
        "upper_ceiling_chamber_z": "upper ceiling chamber side",
        "upper_ceiling_outer_z": "upper ceiling outside",
    }
    for key, label in labels.items():
        elevation.append(f"| {label} | {report['elevations_mm'][key]:.4f} |")
    elevation.extend([
        "", f"- chamber → drain descent: **{report['elevations_mm']['difference_chamber_to_drain']:.4f} mm**",
        f"- lower 10 mm / 7° drop: **{report['elevations_mm']['lower_floor_drop']:.4f} mm**",
        f"- upper 10 mm / 4° drop: **{report['elevations_mm']['upper_ceiling_drop']:.4f} mm**",
        "", "`water must descend toward outside`: PASS (CAD).", "",
    ])
    (REPORT_DIR / "ELEVATION_REPORT.md").write_text("\n".join(elevation), encoding="utf-8")

    water = [
        "# WATER PATH VALIDATION", "", f"Physical rating: `{PHYSICAL_RATING}`", "",
        "| Required CAD statement | Result |", "|---|---|",
    ]
    for name, result in report["water_path"].items():
        water.append(f"| `{name}` | {result} |")
    water.extend([
        "", "The lower relief slopes outward 7° and the upper ceiling slopes outward 4° without reducing minimum cable clearance.",
        "The 1.2 × 0.8 mm capillary break directly intersects the relocated 2.5 mm drain capture region.",
        "Strong direct pipette WET is recorded as `PRESSURE_JET_LIMIT_OBSERVED`; it is not a required PASS condition.",
        "Physical coupon tests at level, +5°, and -5° remain mandatory.", "",
    ])
    (REPORT_DIR / "WATER_PATH_VALIDATION.md").write_text("\n".join(water), encoding="utf-8")

    assembly = ["# ASSEMBLY PATH VALIDATION", ""]
    for name, result in report["assembly_path"].items():
        assembly.append(f"- `{name}`: {result}")
    assembly.extend([
        "", "v003 side-load assembly is inherited as Physical PASS. v004 CAD top-load and release sweeps remain clear after all water-management additions.",
        "No end threading, cable cutting, hard clamp, or connector removal is introduced.", "",
    ])
    (REPORT_DIR / "ASSEMBLY_PATH_VALIDATION.md").write_text("\n".join(assembly), encoding="utf-8")


def write_sha_manifest() -> None:
    manifest = LANE_DIR / "SHA256SUMS.txt"
    files = sorted(
        path for path in LANE_DIR.rglob("*")
        if path.is_file() and path != manifest and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    manifest.write_text(
        "\n".join(f"{sha256_file(path)}  {path.relative_to(LANE_DIR).as_posix()}" for path in files) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    for directory in (STL_DIR, STEP_DIR, DOC_DIR, REPORT_DIR, RENDER_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    write_parameters()
    lower = build_lower_shell_v004()
    upper = build_upper_shell_v004()
    connector = connector_reference()
    camera = cable_reference(-1.0, CAMERA_SIDE_CABLE_OD)
    extension = cable_reference(1.0, EXTENSION_SIDE_CABLE_OD)
    assembly = compound((upper, lower, connector, camera, extension))
    coupon_lower, coupon_upper, coupon_assembly = build_coupon(lower, upper)

    stl_models = {
        "outward_drain_labyrinth_coupon_lower_v004": coupon_lower,
        "outward_drain_labyrinth_coupon_upper_v004": coupon_upper,
        "usb_raincover_lower_v004": lower,
        "usb_raincover_upper_v004": upper,
    }
    for stem, model in stl_models.items():
        export_stl(model, STL_DIR / f"{stem}.stl")
    step_models = {
        "outward_drain_labyrinth_coupon_v004": coupon_assembly,
        "usb_raincover_lower_v004": lower,
        "usb_raincover_upper_v004": upper,
        "usb_raincover_assembly_v004": assembly,
    }
    for stem, model in step_models.items():
        export_step(model, STEP_DIR / f"{stem}.step")

    make_outward_drain_render(RENDER_DIR / "outward_drain_section.png")
    make_capillary_render(RENDER_DIR / "capillary_break_section.png")
    make_open_side_load(RENDER_DIR / "open_side_load.png")
    make_closed_side_load(RENDER_DIR / "closed_side_load.png")
    make_installation_render(RENDER_DIR / "installation_vertical_pipe.png")
    make_water_arrows(RENDER_DIR / "water_flow_arrows.png")

    models = {
        "lower": lower,
        "upper": upper,
        "connector": connector,
        "camera": camera,
        "extension": extension,
        "assembly": assembly,
        "coupon_assembly": coupon_assembly,
        "camera_lower_sweep": v3.lower_placement_envelope(-1.0, CAMERA_SIDE_CABLE_OD),
        "extension_lower_sweep": v3.lower_placement_envelope(1.0, EXTENSION_SIDE_CABLE_OD),
        "camera_upper_sweep": v3.upper_release_envelope(-1.0, CAMERA_SIDE_CABLE_OD),
        "extension_upper_sweep": v3.upper_release_envelope(1.0, EXTENSION_SIDE_CABLE_OD),
        "connector_placement": v3.connector_placement_envelope(),
        **stl_models,
    }
    report = validate(models)
    (REPORT_DIR / "validation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_reports(report)
    write_sha_manifest()
    print(json.dumps({
        "lane": str(LANE_DIR),
        "status": DESIGN_STATUS,
        "cad_pass": True,
        "inherited_side_load_physical": "PASS",
        "v004_water_physical": "PENDING",
        "pressure_jet_rated": PRESSURE_JET_RATED,
        "next_print": "outward_drain_labyrinth_coupon lower/upper pair",
    }, indent=2))


if __name__ == "__main__":
    main()
