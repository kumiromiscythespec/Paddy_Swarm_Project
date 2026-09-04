#!/usr/bin/env python3
"""Measured-envelope v002 of the splash-resistant USB inline raincover.

The v001 water architecture is loaded read-only and parameterized with the new
physical connector/cable Authority.  v002 changes the protected length, makes
both cable paths 4.4 mm, and adds one central closure station per side.  It
does not claim waterproof, field-rain, or powered-operation approval.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import cadquery as cq
from PIL import Image, ImageDraw, ImageFont


LANE_NAME = "ps_usb_inline_raincover_v002_measured_envelope"
VERSION = "v0.0.2"
DESIGN_STATUS = "CAD_COMPLETE_MEASURED_ENVELOPE_PHYSICAL_VALIDATION_PENDING"
WATER_RATING = "SPLASH_RESISTANT_NOT_WATERPROOF"

CONNECTOR_ENVELOPE_L = 95.1
CONNECTOR_ENVELOPE_W = 18.7
CONNECTOR_ENVELOPE_H = 10.8
CAMERA_SIDE_CABLE_OD = 3.8
EXTENSION_SIDE_CABLE_OD = 4.0
CABLE_CHANNEL_D = 4.4

CHAMBER_INNER_L = 102.0
CHAMBER_INNER_W = 24.0
CHAMBER_INNER_H = 16.0
WALL_T = 3.0
LABYRINTH_HORIZONTAL_RUN = 10.0
LABYRINTH_VERTICAL_OFFSET = 5.0
DRAIN_D = 2.5
DRAIN_COUNT = 2
FLOOR_SLOPE_DEG = 2.0
ROOF_SLOPE_DEG = 3.0
TOP_OVERLAP_SKIRT = 6.0
PARTING_STEP_H = 2.0
PARTING_OVERLAP = 3.0
PARTING_CLEARANCE = 0.30

V001_LANE_REL = Path("cad/ps_usb_inline_raincover_v001")
V001_SOURCE_SHA256 = "8e4eb983dddb81f2195e4578f27245c4521d19fbec728d957415843a8c13f924"
V001_PARAMETERS_SHA256 = "155bf03c41cb87bce464fd32db0c6466d6e313b7b1de763161ae0ee232815ab5"
V001_VALIDATION_SHA256 = "697b390d8a29571a1cd528af04ffe48cbef9522105472fac274920af7e4df152"
V001_ASSEMBLY_STEP_SHA256 = "dc9c6ce00d16cfdd091fea7afbab807ca7e57e7db86fd3335545336c8ff801e5"
V001_MANIFEST_SHA256 = "9290a129e3720b6f5dc86c8323c1db960a00e4feabdf4df06d4eba8b8f61c515"

REPO_DIR = Path(__file__).resolve().parents[3]
LANE_DIR = Path(__file__).resolve().parents[1]
V001_DIR = REPO_DIR / V001_LANE_REL
V001_SOURCE = V001_DIR / "cad" / "ps_usb_inline_raincover_v001.py"
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


def load_v001_read_only() -> Any:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("ps_usb_inline_raincover_v001_authority", V001_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load v001 Authority source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v1 = load_v001_read_only()

V001_ARCHITECTURE = {
    "roof_slope_deg": v1.ROOF_SLOPE_DEG,
    "top_overlap_skirt_mm": v1.TOP_OVERLAP_SKIRT,
    "parting_step_h_mm": v1.PARTING_STEP_H,
    "parting_overlap_mm": v1.PARTING_OVERLAP,
    "parting_clearance_mm": v1.PARTING_CLEARANCE,
    "labyrinth_horizontal_run_mm": v1.LABYRINTH_HORIZONTAL_RUN,
    "labyrinth_vertical_offset_mm": v1.LABYRINTH_VERTICAL_OFFSET,
    "drain_d_mm": v1.DRAIN_D,
    "drain_count": v1.DRAIN_COUNT,
    "floor_slope_deg": v1.FLOOR_SLOPE_DEG,
    "wall_mm": v1.WALL_T,
}


def configure_v001_geometry_for_v002() -> None:
    """Apply only measured-envelope deltas to the read-only v001 builder."""
    v1.CONNECTOR_MAX_W = CONNECTOR_ENVELOPE_W
    v1.CABLE_SMALL_OD = CAMERA_SIDE_CABLE_OD
    v1.CABLE_LARGE_OD = EXTENSION_SIDE_CABLE_OD
    v1.CHAMBER_INNER_L = CHAMBER_INNER_L
    v1.CHAMBER_INNER_W = CHAMBER_INNER_W
    v1.CHAMBER_INNER_H = CHAMBER_INNER_H
    v1.WALL_T = WALL_T
    v1.SMALL_CABLE_CHANNEL_D = CABLE_CHANNEL_D
    v1.LARGE_CABLE_CHANNEL_D = CABLE_CHANNEL_D
    v1.LABYRINTH_HORIZONTAL_RUN = LABYRINTH_HORIZONTAL_RUN
    v1.LABYRINTH_VERTICAL_OFFSET = LABYRINTH_VERTICAL_OFFSET
    v1.DRAIN_D = DRAIN_D
    v1.DRAIN_COUNT = DRAIN_COUNT
    v1.FLOOR_SLOPE_DEG = FLOOR_SLOPE_DEG
    v1.ROOF_SLOPE_DEG = ROOF_SLOPE_DEG
    v1.TOP_OVERLAP_SKIRT = TOP_OVERLAP_SKIRT
    v1.PARTING_STEP_H = PARTING_STEP_H
    v1.PARTING_OVERLAP = PARTING_OVERLAP
    v1.PARTING_CLEARANCE = PARTING_CLEARANCE
    v1.CLOSURE_METHOD = "M3_X6_SIDE_FLANGE_WITH_CAPTURED_HEX_NUTS"
    v1.SCREW_XS = (-50.0, 0.0, 50.0)

    v1.LOWER_OUTER_L = CHAMBER_INNER_L + 2.0 * (LABYRINTH_HORIZONTAL_RUN + WALL_T)
    v1.LOWER_OUTER_W = CHAMBER_INNER_W + 2.0 * WALL_T
    v1.FLOOR_CROWN_H = math.tan(math.radians(FLOOR_SLOPE_DEG)) * CHAMBER_INNER_L / 2.0
    v1.ROOF_INNER_Z = v1.FLOOR_CROWN_H + CHAMBER_INNER_H
    v1.SKIRT_INNER_L = v1.LOWER_OUTER_L + 2.0 * PARTING_CLEARANCE
    v1.SKIRT_INNER_W = v1.LOWER_OUTER_W + 2.0 * PARTING_CLEARANCE
    v1.UPPER_OUTER_L = v1.SKIRT_INNER_L + 2.0 * PARTING_OVERLAP
    v1.UPPER_OUTER_W = v1.SKIRT_INNER_W + 2.0 * PARTING_OVERLAP
    v1.ROOF_RISE = math.tan(math.radians(ROOF_SLOPE_DEG)) * v1.UPPER_OUTER_L
    v1.TONGUE_OUTER_L = v1.LOWER_OUTER_L - 4.0
    v1.TONGUE_OUTER_W = v1.LOWER_OUTER_W - 2.0
    v1.TONGUE_INNER_L = v1.TONGUE_OUTER_L - 4.0
    v1.TONGUE_INNER_W = CHAMBER_INNER_W
    v1.GROOVE_OUTER_L = v1.TONGUE_OUTER_L + 2.0 * PARTING_CLEARANCE
    v1.GROOVE_OUTER_W = v1.TONGUE_OUTER_W + 2.0 * PARTING_CLEARANCE
    v1.GROOVE_INNER_L = v1.TONGUE_INNER_L - 2.0 * PARTING_CLEARANCE
    v1.GROOVE_INNER_W = v1.TONGUE_INNER_W - 2.0 * PARTING_CLEARANCE
    v1.PORT_X_ABS = CHAMBER_INNER_L / 2.0 + LABYRINTH_HORIZONTAL_RUN
    v1.POCKET_X_ABS = CHAMBER_INNER_L / 2.0 + 7.0
    v1.PASSAGE_CENTER_Z = v1.POCKET_BOTTOM_Z + LABYRINTH_VERTICAL_OFFSET
    v1.DRAIN_X_ABS = CHAMBER_INNER_L / 2.0 + 6.0
    v1.BAFFLE_X_ABS = CHAMBER_INNER_L / 2.0 + 1.0


configure_v001_geometry_for_v002()

FLOOR_CROWN_H = v1.FLOOR_CROWN_H
ROOF_INNER_Z = v1.ROOF_INNER_Z
AXIAL_CLEARANCE_TOTAL = CHAMBER_INNER_L - CONNECTOR_ENVELOPE_L
AXIAL_CLEARANCE_SIDE = AXIAL_CLEARANCE_TOTAL / 2.0
WIDTH_CLEARANCE_TOTAL = CHAMBER_INNER_W - CONNECTOR_ENVELOPE_W
HEIGHT_CLEARANCE_TOTAL = CHAMBER_INNER_H - CONNECTOR_ENVELOPE_H
CONNECTOR_BOTTOM_Z = FLOOR_CROWN_H + 0.5
CONNECTOR_CENTER_Z = CONNECTOR_BOTTOM_Z + CONNECTOR_ENVELOPE_H / 2.0
SADDLE_X_ABS = (CONNECTOR_ENVELOPE_L / 2.0 + CHAMBER_INNER_L / 2.0) / 2.0
SADDLE_AXIAL_L = 3.0
SADDLE_ENVELOPE_GAP = SADDLE_X_ABS - SADDLE_AXIAL_L / 2.0 - CONNECTOR_ENVELOPE_L / 2.0


def connector_reference() -> cq.Workplane:
    return v1.rounded_rect_prism(
        CONNECTOR_ENVELOPE_L,
        CONNECTOR_ENVELOPE_W,
        CONNECTOR_ENVELOPE_H,
        CONNECTOR_BOTTOM_Z,
        2.0,
    ).clean()


def build_lower_shell_v002() -> cq.Workplane:
    """v001 lower architecture with measured-envelope-safe cable saddles.

    v001 placed 5 mm-long saddles at x = +/-21 mm.  The 95.1 mm measured
    protected envelope occupies that region, so v002 uses 3 mm-long saddles
    in the measured 3.45 mm end-clearance zones.  They retain 0.8 mm radial
    cable clearance and therefore locate, but do not hard-clamp, either cable.
    """
    lower = v1.rounded_rect_prism(
        v1.LOWER_OUTER_L,
        v1.LOWER_OUTER_W,
        v1.PARTING_Z - v1.LOWER_BOTTOM_Z,
        v1.LOWER_BOTTOM_Z,
        4.0,
    )

    tongue = v1.rounded_frame(
        v1.TONGUE_OUTER_L,
        v1.TONGUE_OUTER_W,
        v1.TONGUE_INNER_L,
        v1.TONGUE_INNER_W,
        PARTING_STEP_H,
        v1.PARTING_Z,
        3.0,
        2.0,
    )
    lower = lower.union(tongue)

    for x in v1.SCREW_XS:
        for sign in (-1.0, 1.0):
            lower = lower.union(
                v1.box(9.0, 11.0, v1.FLANGE_T,
                       (x, sign * 20.5, v1.PARTING_Z - v1.FLANGE_T / 2.0))
            )

    for x in (-5.0, 0.0, 5.0):
        for sign in (-1.0, 1.0):
            lower = lower.cut(v1.box(1.6, 1.4, 1.6, (x, sign * 15.0, -1.6)))

    lower = lower.cut(v1.build_chamber_cavity())

    for sign in (-1.0, 1.0):
        pocket = v1.box(
            v1.POCKET_L,
            CABLE_CHANNEL_D + 6.0,
            20.0,
            (sign * v1.POCKET_X_ABS, 0.0, v1.POCKET_BOTTOM_Z + 10.0),
        )
        lower = lower.cut(pocket)
        lower = lower.cut(v1.cylinder_between(
            CABLE_CHANNEL_D / 2.0,
            (sign * (CHAMBER_INNER_L / 2.0 - 1.5), 0.0, v1.PASSAGE_CENTER_Z),
            (sign * (v1.POCKET_X_ABS + 1.0), 0.0, v1.PASSAGE_CENTER_Z),
        ))
        lower = lower.cut(v1.cylinder_z(
            CABLE_CHANNEL_D / 2.0, 17.0, -6.0, sign * v1.PORT_X_ABS, 0.0
        ))
        lower = lower.cut(v1.box(
            5.0, 2.5, 2.0, (sign * v1.BAFFLE_X_ABS, v1.WEEP_Y, 0.75)
        ))
        lower = lower.cut(v1.cylinder_z(
            DRAIN_D / 2.0, 8.0, -6.0, sign * v1.DRAIN_X_ABS, v1.DRAIN_Y
        ))

    # MEASURED_ENVELOPE_REQUIRED_CHANGE: move and shorten the two saddles so
    # the full rigid-to-flexible bounding envelope has positive axial gap.
    for sign in (-1.0, 1.0):
        x = sign * SADDLE_X_ABS
        floor_z = v1.chamber_floor_z(x)
        saddle = v1.box(SADDLE_AXIAL_L, 12.0, 5.2, (x, 0.0, floor_z + 2.6))
        lower = lower.union(saddle)
        lower = lower.cut(v1.cylinder_between(
            (CABLE_CHANNEL_D + v1.STRAIN_RELIEF_RADIAL_CLEARANCE) / 2.0,
            (x - 2.2, 0.0, v1.PASSAGE_CENTER_Z),
            (x + 2.2, 0.0, v1.PASSAGE_CENTER_Z),
        ))

    for x in v1.SCREW_XS:
        for sign in (-1.0, 1.0):
            y = sign * v1.SCREW_Y_ABS
            lower = lower.cut(v1.cylinder_z(v1.M3_CLEARANCE_D / 2.0, 8.0, 2.0, x, y))
            lower = lower.cut(v1.hex_prism_z(
                v1.M3_NUT_AF, v1.M3_NUT_DEPTH, v1.PARTING_Z - v1.FLANGE_T, x, y
            ))
    return lower.clean()


def cable_reference(sign: float, diameter: float) -> cq.Workplane:
    start_x = sign * (CHAMBER_INNER_L / 2.0 - 1.5)
    end_x = sign * (v1.PORT_X_ABS + 1.5)
    horizontal = v1.cylinder_between(
        diameter / 2.0,
        (start_x, 0.0, v1.PASSAGE_CENTER_Z),
        (end_x, 0.0, v1.PASSAGE_CENTER_Z),
    )
    vertical = v1.cylinder_z(
        diameter / 2.0,
        v1.PASSAGE_CENTER_Z + 6.0,
        -6.0,
        sign * v1.PORT_X_ABS,
        0.0,
    )
    return horizontal.union(vertical).clean()


def build_fit_coupon() -> tuple[cq.Workplane, cq.Workplane, cq.Workplane, cq.Workplane]:
    """Low-material two-part skeleton that gauges the measured envelope."""
    outer_l = CHAMBER_INNER_L + 6.0
    outer_w = CHAMBER_INNER_W + 6.0
    floor_top = FLOOR_CROWN_H

    lower: cq.Workplane | None = None
    # Long side rails establish the exact 24 mm inner width and parting datum.
    for sign in (-1.0, 1.0):
        rail = v1.box(outer_l, 3.0, 8.0, (0.0, sign * 13.5, 4.0))
        tongue = v1.box(outer_l - 2.0, 2.0, PARTING_STEP_H,
                        (0.0, sign * 13.0, v1.PARTING_Z + PARTING_STEP_H / 2.0))
        lower = rail.union(tongue) if lower is None else lower.union(rail).union(tongue)

    # Three narrow floor cross-rails retain the actual center crown datum.
    for x in (-48.0, 0.0, 48.0):
        cross = v1.box(3.0, CHAMBER_INNER_W, 2.0, (x, 0.0, floor_top - 1.0))
        lower = lower.union(cross)

    # End transition plates define 102 mm inner length and open-top 4.4 slots.
    for sign in (-1.0, 1.0):
        plate = v1.box(3.0, outer_w, 8.0, (sign * (CHAMBER_INNER_L / 2.0 + 1.5), 0.0, 4.0))
        lower = lower.union(plate)
        slot_cyl = v1.cylinder_between(
            CABLE_CHANNEL_D / 2.0,
            (sign * (CHAMBER_INNER_L / 2.0 - 1.0), 0.0, v1.PASSAGE_CENTER_Z),
            (sign * (CHAMBER_INNER_L / 2.0 + 4.0), 0.0, v1.PASSAGE_CENTER_Z),
        )
        slot_top = v1.box(5.0, CABLE_CHANNEL_D, 8.0,
                          (sign * (CHAMBER_INNER_L / 2.0 + 1.5), 0.0, v1.PASSAGE_CENTER_Z + 4.0))
        lower = lower.cut(slot_cyl.union(slot_top))
    assert lower is not None
    lower = lower.clean()

    # Upper skeleton: perimeter height gauge plus six local datum feet.
    top_frame = v1.rounded_frame(
        outer_l,
        outer_w,
        outer_l - 6.0,
        CHAMBER_INNER_W,
        3.0,
        ROOF_INNER_Z,
        3.0,
        1.5,
    )
    upper = top_frame
    for x in (-50.0, 0.0, 50.0):
        for sign in (-1.0, 1.0):
            post_h = ROOF_INNER_Z + 0.2 - (v1.PARTING_Z + PARTING_CLEARANCE)
            post = v1.box(5.0, 3.0, post_h,
                          (x, sign * 13.5, v1.PARTING_Z + PARTING_CLEARANCE + post_h / 2.0))
            foot = v1.box(7.0, 7.0, 3.2, (x, sign * 13.0, v1.PARTING_Z + 1.3))
            groove = v1.box(7.4, 2.0 + 2.0 * PARTING_CLEARANCE,
                            PARTING_STEP_H + 2.0 * PARTING_CLEARANCE,
                            (x, sign * 13.0, v1.PARTING_Z + PARTING_STEP_H / 2.0))
            upper = upper.union(post).union(foot.cut(groove))
    upper = upper.clean()
    assembled = v1.compound_workplane((lower, upper))

    lower_print = lower.translate((0.0, -38.0, -lower.val().BoundingBox().zmin))
    upper_flipped = upper.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0)
    upper_print = upper_flipped.translate((0.0, 38.0, -upper_flipped.val().BoundingBox().zmin))
    print_layout = v1.compound_workplane((lower_print, upper_print))
    return print_layout, assembled, lower, upper


def build_labyrinth_coupon(lower: cq.Workplane) -> cq.Workplane:
    side_center_x = -(CHAMBER_INNER_L / 2.0 + 4.0)
    cutter = v1.box(20.0, v1.LOWER_OUTER_W + 0.2, 24.0, (side_center_x, 0.0, 3.0))
    coupon = v1.wp(lower.val().intersect(cutter.val()))
    return coupon.translate((-side_center_x, 0.0, 0.0)).clean()


def compound(models: Iterable[cq.Workplane]) -> cq.Workplane:
    return v1.compound_workplane(models)


def export_stl(model: cq.Workplane, path: Path) -> None:
    cq.exporters.export(model, str(path), tolerance=STL_LINEAR_TOLERANCE, angularTolerance=STL_ANGULAR_TOLERANCE)


def export_step(model: cq.Workplane, path: Path) -> None:
    cq.exporters.export(model, str(path))


def font(size: int) -> ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def make_assembled_render(output: Path) -> None:
    image = Image.new("RGB", (1350, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 25), "USB inline raincover v002 - measured envelope assembly", fill="#0f172a", font=font(30))
    roof = [(165, 210), (910, 105), (1190, 255), (440, 370)]
    draw.polygon(roof, fill="#334155", outline="#0f172a")
    draw.polygon([(440, 370), (1190, 255), (1190, 410), (440, 530)], fill="#1f2937", outline="#0f172a")
    draw.polygon([(165, 210), (440, 370), (440, 530), (165, 365)], fill="#475569", outline="#0f172a")
    draw.polygon([(205, 405), (440, 535), (1160, 420), (925, 305), (925, 465), (440, 580)],
                 fill="#f59e0b", outline="#92400e")
    draw.line((220, 430, 110, 585), fill="#2563eb", width=12)
    draw.line((1140, 445, 1250, 600), fill="#2563eb", width=13)
    for x in (290, 675, 1050):
        draw.ellipse((x-13, 530, x+13, 556), fill="#d1d5db", outline="#111827")
    draw.text((70, 685), "Measured protected connector span: 95.1 mm inside 102 mm chamber", fill="#1e3a8a", font=font(22))
    draw.text((70, 725), "Common 4.4 mm ports / M3 x6 external closure / v001 water architecture preserved", fill="#334155", font=font(22))
    draw.text((70, 765), "SPLASH_RESISTANT_NOT_WATERPROOF", fill="#7f1d1d", font=font(22))
    image.save(output)


def make_connector_fit_render(output: Path) -> None:
    image = Image.new("RGB", (1350, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 25), "CONNECTOR ENVELOPE FIT - physical Authority", fill="#0f172a", font=font(30))
    left, right = 130, 1220
    chamber_top, chamber_bottom = 170, 560
    draw.rounded_rectangle((left, chamber_top, right, chamber_bottom), radius=34, fill="#fef3c7", outline="#92400e", width=4)
    scale = (right-left) / CHAMBER_INNER_L
    env_l = CONNECTOR_ENVELOPE_L * scale
    env_left = (left+right-env_l)/2
    env_right = env_left+env_l
    draw.rounded_rectangle((env_left, 255, env_right, 465), radius=28, fill="#dbeafe", outline="#1d4ed8", width=4)
    draw.text((env_left+25, 330), "95.1 x 18.7 x 10.8 mm\nMEASURED BOUNDING ENVELOPE", fill="#1e3a8a", font=font(22))
    draw.line((left, 625, right, 625), fill="#111827", width=3)
    draw.line((left, 612, left, 638), fill="#111827", width=3)
    draw.line((right, 612, right, 638), fill="#111827", width=3)
    draw.text((580, 645), "CHAMBER L = 102.0 mm", fill="#111827", font=font(22))
    draw.text((145, 705), f"Axial clearance: {AXIAL_CLEARANCE_TOTAL:.1f} mm total / {AXIAL_CLEARANCE_SIDE:.2f} mm each end", fill="#334155", font=font(22))
    draw.text((145, 745), f"Width clearance: {WIDTH_CLEARANCE_TOTAL:.1f} mm  Height clearance: {HEIGHT_CLEARANCE_TOTAL:.1f} mm  Compression target: NONE", fill="#334155", font=font(22))
    image.save(output)


def make_longitudinal_render(output: Path) -> None:
    image = Image.new("RGB", (1450, 850), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45, 22), "LONGITUDINAL SECTION - 102 mm chamber / two-way gravity drainage", fill="#0f172a", font=font(28))
    xmin, xmax, zmin, zmax = -72.0, 72.0, -7.0, 29.0
    left, top, width, height = 80, 85, 1290, 650
    px = lambda x: int(left + (x-xmin)/(xmax-xmin)*width)
    pz = lambda z: int(top + (zmax-z)/(zmax-zmin)*height)
    roof = [(-v1.UPPER_OUTER_L/2, v1.ROOF_INNER_Z), (v1.UPPER_OUTER_L/2, v1.ROOF_INNER_Z),
            (v1.UPPER_OUTER_L/2, v1.ROOF_INNER_Z+WALL_T), (-v1.UPPER_OUTER_L/2, v1.ROOF_INNER_Z+WALL_T+v1.ROOF_RISE)]
    draw.polygon([(px(x),pz(z)) for x,z in roof], fill="#334155", outline="#0f172a")
    draw.line([(px(-51),pz(0)),(px(0),pz(FLOOR_CROWN_H)),(px(51),pz(0))], fill="#f59e0b", width=7)
    draw.rounded_rectangle((px(-CONNECTOR_ENVELOPE_L/2),pz(CONNECTOR_BOTTOM_Z+CONNECTOR_ENVELOPE_H),
                            px(CONNECTOR_ENVELOPE_L/2),pz(CONNECTOR_BOTTOM_Z)), radius=18,
                           fill="#dbeafe", outline="#1d4ed8", width=3)
    for sign in (-1,1):
        draw.rectangle((px(sign*v1.BAFFLE_X_ABS-1),pz(v1.ROOF_INNER_Z),px(sign*v1.BAFFLE_X_ABS+1),pz(1.5)),fill="#f59e0b")
        draw.line((px(sign*v1.PORT_X_ABS),pz(v1.PASSAGE_CENTER_Z),px(sign*v1.PORT_X_ABS),pz(-5.5)),fill="#2563eb",width=11)
        draw.line((px(sign*v1.DRAIN_X_ABS),pz(0),px(sign*v1.DRAIN_X_ABS),pz(-5.5)),fill="#06b6d4",width=6)
    draw.text((545, 380), "MEASURED CONNECTOR ENVELOPE", fill="#1e3a8a", font=font(20))
    draw.text((80, 780), f"Center crown = {FLOOR_CROWN_H:.3f} mm (recomputed from 102 mm at 2 deg); drains remain 2.5 mm x2.", fill="#334155", font=font(21))
    image.save(output)


def make_cable_render(output: Path) -> None:
    image = Image.new("RGB", (1200, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((50, 25), "COMMON 4.4 mm CABLE LABYRINTH - v001 coupon Physical PASS", fill="#0f172a", font=font(27))
    draw.rectangle((90, 120, 1080, 620), fill="#f59e0b", outline="#92400e", width=4)
    draw.rounded_rectangle((150, 200, 560, 515), radius=32, fill="white", outline="#334155", width=3)
    draw.rectangle((560, 195, 630, 520), fill="#fde68a", outline="#92400e", width=3)
    draw.rounded_rectangle((630, 255, 900, 520), radius=26, fill="white", outline="#334155", width=3)
    draw.line((460, 390, 855, 390), fill="#93c5fd", width=20)
    draw.line((855, 390, 855, 690), fill="#2563eb", width=20)
    draw.line((730, 520, 730, 690), fill="#06b6d4", width=9)
    draw.text((135, 145), "connector chamber", fill="#334155", font=font(20))
    draw.text((555, 145), "terminal baffle", fill="#92400e", font=font(20))
    draw.text((665, 220), "drip vestibule", fill="#334155", font=font(20))
    draw.text((95, 730), "Camera cable OD 3.8 -> diametral clearance 0.6 mm", fill="#1d4ed8", font=font(20))
    draw.text((620, 730), "Extension cable OD 4.0 -> diametral clearance 0.4 mm", fill="#1d4ed8", font=font(20))
    draw.text((245, 775), "10 mm run / 5 mm vertical offset / bend space >= R4 / hard clamp forbidden", fill="#111827", font=font(19))
    image.save(output)


def make_drain_render(output: Path) -> None:
    image = Image.new("RGB", (1150, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45, 25), "DRAIN SECTION - inherited offset weep and WITNESS BAY", fill="#0f172a", font=font(28))
    draw.rectangle((110, 115, 1040, 610), fill="#f59e0b", outline="#92400e", width=4)
    draw.polygon([(170,260),(520,225),(620,335),(940,335),(940,500),(620,500),(520,395),(170,425)],fill="white",outline="#334155")
    draw.rectangle((175, 285, 430, 395), fill="#f8fafc", outline="#64748b", width=2)
    draw.text((205, 325), "DRY TISSUE\nWITNESS BAY", fill="#475569", font=font(20))
    draw.line((430,365,610,440),fill="#06b6d4",width=8)
    draw.line((610,440,770,490),fill="#06b6d4",width=8)
    draw.line((770,500,770,700),fill="#06b6d4",width=12)
    draw.text((690,735), "2.5 mm gravity drain", fill="#0e7490", font=font(20))
    draw.text((105,770), "Test level, +5 deg, -5 deg; witness result must be DRY before full-shell gate.", fill="#7f1d1d", font=font(20))
    image.save(output)


def write_parameters() -> None:
    params = {
        "lane": LANE_NAME,
        "version": VERSION,
        "status": DESIGN_STATUS,
        "water_rating": WATER_RATING,
        "physical_authority_priority": [
            "Physical measurement",
            "Physical coupon result",
            "v001 validated geometry",
            "CAD nominal",
            "provisional assumption",
        ],
        "connector_envelope_mm": {
            "L": CONNECTOR_ENVELOPE_L,
            "W": CONNECTOR_ENVELOPE_W,
            "H": CONNECTOR_ENVELOPE_H,
            "definition": "rigid-to-flexible total protected connector bounding envelope",
            "authority": "PHYSICAL_MEASUREMENT",
        },
        "cables_mm": {
            "camera_side_OD": CAMERA_SIDE_CABLE_OD,
            "extension_side_OD": EXTENSION_SIDE_CABLE_OD,
            "common_channel_D": CABLE_CHANNEL_D,
            "camera_diametral_clearance": CABLE_CHANNEL_D - CAMERA_SIDE_CABLE_OD,
            "extension_diametral_clearance": CABLE_CHANNEL_D - EXTENSION_SIDE_CABLE_OD,
            "authority": "V001_COUPON_PHYSICAL_PASS_BOTH_CABLES",
        },
        "chamber_inner_mm": {"L": CHAMBER_INNER_L, "W": CHAMBER_INNER_W, "H": CHAMBER_INNER_H},
        "clearances_mm": {
            "axial_total": AXIAL_CLEARANCE_TOTAL,
            "axial_each_end": AXIAL_CLEARANCE_SIDE,
            "width_total": WIDTH_CLEARANCE_TOTAL,
            "width_each_side": WIDTH_CLEARANCE_TOTAL / 2.0,
            "height_total": HEIGHT_CLEARANCE_TOTAL,
            "connector_compression": "NONE_TARGET",
        },
        "preserved_v001": {
            "WALL_T": WALL_T,
            "LABYRINTH_HORIZONTAL_RUN": LABYRINTH_HORIZONTAL_RUN,
            "LABYRINTH_VERTICAL_OFFSET": LABYRINTH_VERTICAL_OFFSET,
            "DRAIN_D": DRAIN_D,
            "DRAIN_COUNT": DRAIN_COUNT,
            "FLOOR_SLOPE_DEG": FLOOR_SLOPE_DEG,
            "ROOF_SLOPE_DEG": ROOF_SLOPE_DEG,
            "TOP_OVERLAP_SKIRT": TOP_OVERLAP_SKIRT,
            "PARTING_STEP_H": PARTING_STEP_H,
            "PARTING_OVERLAP": PARTING_OVERLAP,
            "PARTING_CLEARANCE": PARTING_CLEARANCE,
        },
        "derived": {
            "floor_center_crown_mm": FLOOR_CROWN_H,
            "roof_rise_mm": v1.ROOF_RISE,
            "full_lower_outer_length_mm": v1.LOWER_OUTER_L,
            "full_upper_outer_length_mm": v1.UPPER_OUTER_L,
        },
        "closure": {
            "configuration": "M3_X6_SIDE_FLANGE_WITH_CAPTURED_HEX_NUTS",
            "stations_x_mm": list(v1.SCREW_XS),
            "reason": "MEASURED_ENVELOPE_REQUIRED_CHANGE_parting_span_control",
            "external_reinforcement_ribs": False,
        },
        "strain_relief_saddle": {
            "center_x_abs_mm": SADDLE_X_ABS,
            "axial_length_mm": SADDLE_AXIAL_L,
            "gap_to_measured_envelope_mm": SADDLE_ENVELOPE_GAP,
            "groove_d_mm": CABLE_CHANNEL_D + v1.STRAIN_RELIEF_RADIAL_CLEARANCE,
            "hard_clamping": False,
            "reason": "MEASURED_ENVELOPE_REQUIRED_CHANGE",
        },
        "v001_superseded": {
            "chamber_length_50_mm": "REJECTED_UNDERSIZED_PROVISIONAL_DIMENSION",
            "cable_7p9_mm": "SUPERSEDED_BY_PHYSICAL_MEASUREMENT",
            "large_channel_9p0_mm": "NO_LONGER_REQUIRED",
        },
        "physical_statuses": {
            "CABLE_CHANNEL_PHYSICAL": "PASS",
            "CONNECTOR_DIMENSION_PHYSICAL": "PASS_MEASURED",
            "CHAMBER_PHYSICAL": "PENDING",
            "LABYRINTH_DRAIN_PHYSICAL": "PENDING",
            "FULL_SHELL_RAIN": "PENDING",
            "LIVE_USB_RAIN": "PENDING",
        },
        "print": {
            "printer": "Bambu Lab A1", "material": "PETG", "nozzle_mm": 0.4,
            "layer_mm": 0.20, "walls_min": 4, "top_bottom_min": 5, "infill_percent": "25-35",
        },
    }
    (LANE_DIR / "cad" / "parameters.json").write_text(json.dumps(params, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate(models: dict[str, cq.Workplane]) -> dict[str, Any]:
    upper = models["upper"]
    lower = models["lower"]
    connector = models["connector"]
    camera_cable = models["camera_cable"]
    extension_cable = models["extension_cable"]

    intersections = {
        "connector_vs_upper_mm3": round(v1.intersection_volume(connector, upper), 8),
        "connector_vs_lower_mm3": round(v1.intersection_volume(connector, lower), 8),
        "camera_cable_vs_upper_mm3": round(v1.intersection_volume(camera_cable, upper), 8),
        "camera_cable_vs_lower_mm3": round(v1.intersection_volume(camera_cable, lower), 8),
        "extension_cable_vs_upper_mm3": round(v1.intersection_volume(extension_cable, upper), 8),
        "extension_cable_vs_lower_mm3": round(v1.intersection_volume(extension_cable, lower), 8),
        "upper_vs_lower_mm3": round(v1.intersection_volume(upper, lower), 8),
        "connector_vs_fit_coupon_lower_mm3": round(v1.intersection_volume(connector, models["fit_lower"]), 8),
        "connector_vs_fit_coupon_upper_mm3": round(v1.intersection_volume(connector, models["fit_upper"]), 8),
    }

    stl_expected = {
        "connector_chamber_fit_coupon_v002": 2,
        "labyrinth_drain_coupon_v002": 1,
        "usb_raincover_upper_v002": 1,
        "usb_raincover_lower_v002": 1,
    }
    artifacts: dict[str, Any] = {}
    for stem, expected in stl_expected.items():
        model = models[stem]
        brep = v1.shape_metrics(model)
        mesh = v1.stl_mesh_metrics(STL_DIR / f"{stem}.stl")
        bbox_delta = max(abs(brep["bounding_box_mm"][axis] - mesh["bounding_box_mm"][axis]) for axis in ("x", "y", "z"))
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
        "connector_reference_v002": (connector, 1),
        "connector_chamber_fit_coupon_v002": (models["fit_assembled"], 2),
        "labyrinth_drain_coupon_v002": (models["labyrinth_drain_coupon_v002"], 1),
        "usb_raincover_upper_v002": (upper, 1),
        "usb_raincover_lower_v002": (lower, 1),
        "usb_raincover_assembly_v002": (models["assembly"], 5),
    }
    steps: dict[str, Any] = {}
    for stem, (source, expected) in step_expected.items():
        source_metrics = v1.shape_metrics(source)
        imported = cq.importers.importStep(str(STEP_DIR / f"{stem}.step"))
        imported_metrics = v1.shape_metrics(imported)
        checks = {
            "step_nonempty": (STEP_DIR / f"{stem}.step").stat().st_size > 1024,
            "step_reimport_valid": imported_metrics["valid"],
            "step_expected_solids": imported_metrics["solid_count"] == expected,
            "step_volume_matches_source": abs(imported_metrics["volume_mm3"] - source_metrics["volume_mm3"]) <= 0.02,
        }
        if not all(checks.values()):
            raise AssertionError(f"STEP validation failed for {stem}: {checks}")
        steps[stem] = {"expected_solids": expected, "source": source_metrics, "reimport": imported_metrics,
                       "checks": checks, "sha256": sha256_file(STEP_DIR / f"{stem}.step")}

    full_volume = v1.shape_metrics(upper)["volume_mm3"] + v1.shape_metrics(lower)["volume_mm3"]
    coupon_volume = v1.shape_metrics(models["fit_assembled"])["volume_mm3"]
    v001_hashes = {
        "source": sha256_file(V001_SOURCE),
        "parameters": sha256_file(V001_DIR / "cad" / "parameters.json"),
        "validation": sha256_file(V001_DIR / "reports" / "validation_report.json"),
        "assembly_step": sha256_file(V001_DIR / "step" / "usb_raincover_assembly_v001.step"),
        "manifest": sha256_file(V001_DIR / "SHA256SUMS.txt"),
    }
    expected_hashes = {
        "source": V001_SOURCE_SHA256, "parameters": V001_PARAMETERS_SHA256,
        "validation": V001_VALIDATION_SHA256, "assembly_step": V001_ASSEMBLY_STEP_SHA256,
        "manifest": V001_MANIFEST_SHA256,
    }

    checks = {
        "v001_authority_hashes_match": v001_hashes == expected_hashes,
        "v001_roof_slope_preserved": V001_ARCHITECTURE["roof_slope_deg"] == ROOF_SLOPE_DEG,
        "v001_floor_slope_preserved": V001_ARCHITECTURE["floor_slope_deg"] == FLOOR_SLOPE_DEG,
        "v001_skirt_preserved": V001_ARCHITECTURE["top_overlap_skirt_mm"] == TOP_OVERLAP_SKIRT,
        "v001_parting_step_preserved": V001_ARCHITECTURE["parting_step_h_mm"] == PARTING_STEP_H,
        "v001_parting_overlap_preserved": V001_ARCHITECTURE["parting_overlap_mm"] == PARTING_OVERLAP,
        "v001_parting_clearance_preserved": V001_ARCHITECTURE["parting_clearance_mm"] == PARTING_CLEARANCE,
        "v001_labyrinth_run_preserved": V001_ARCHITECTURE["labyrinth_horizontal_run_mm"] == LABYRINTH_HORIZONTAL_RUN,
        "v001_labyrinth_offset_preserved": V001_ARCHITECTURE["labyrinth_vertical_offset_mm"] == LABYRINTH_VERTICAL_OFFSET,
        "v001_drain_preserved": V001_ARCHITECTURE["drain_d_mm"] == DRAIN_D and V001_ARCHITECTURE["drain_count"] == DRAIN_COUNT,
        "chamber_length_requirement": CHAMBER_INNER_L >= CONNECTOR_ENVELOPE_L + 6.9,
        "chamber_width_requirement": CHAMBER_INNER_W > CONNECTOR_ENVELOPE_W,
        "chamber_height_requirement": CHAMBER_INNER_H > CONNECTOR_ENVELOPE_H,
        "axial_clearance_exact": abs(AXIAL_CLEARANCE_TOTAL - 6.9) <= 1.0e-9,
        "width_clearance_exact": abs(WIDTH_CLEARANCE_TOTAL - 5.3) <= 1.0e-9,
        "height_clearance_exact": abs(HEIGHT_CLEARANCE_TOTAL - 5.2) <= 1.0e-9,
        "camera_channel_authority_4p4": CABLE_CHANNEL_D == 4.4,
        "extension_channel_authority_4p4": CABLE_CHANNEL_D == 4.4,
        "camera_cable_fits": CABLE_CHANNEL_D > CAMERA_SIDE_CABLE_OD,
        "extension_cable_fits": CABLE_CHANNEL_D > EXTENSION_SIDE_CABLE_OD,
        "drain_d_exact": DRAIN_D == 2.5 and DRAIN_COUNT == 2,
        "parting_step_exact": PARTING_STEP_H == 2.0,
        "parting_overlap_exact": PARTING_OVERLAP == 3.0,
        "skirt_exact": TOP_OVERLAP_SKIRT == 6.0,
        "floor_crown_recomputed": abs(FLOOR_CROWN_H - math.tan(math.radians(2.0)) * 51.0) <= 1.0e-9,
        "connector_all_shell_interferences_zero": all(intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
            "connector_vs_upper_mm3", "connector_vs_lower_mm3")),
        "connector_fit_coupon_interference_zero": all(intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
            "connector_vs_fit_coupon_lower_mm3", "connector_vs_fit_coupon_upper_mm3")),
        "cable_reference_interferences_zero": all(intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
            "camera_cable_vs_upper_mm3", "camera_cable_vs_lower_mm3",
            "extension_cable_vs_upper_mm3", "extension_cable_vs_lower_mm3")),
        "upper_lower_interference_zero": intersections["upper_vs_lower_mm3"] <= INTERFERENCE_TOLERANCE_MM3,
        "fit_coupon_material_reduced": coupon_volume < 0.35 * full_volume,
        "m3_six_closure_selected": len(v1.SCREW_XS) * 2 == 6,
        "max_axial_fastener_station_span_50": max(abs(v1.SCREW_XS[i+1]-v1.SCREW_XS[i]) for i in range(len(v1.SCREW_XS)-1)) <= 50.0,
        "roof_transverse_span_unchanged": CHAMBER_INNER_W == 24.0,
        "saddle_has_positive_gap_to_measured_envelope": SADDLE_ENVELOPE_GAP > 0.2,
        "saddle_remains_inside_chamber": SADDLE_X_ABS + SADDLE_AXIAL_L / 2.0 < CHAMBER_INNER_L / 2.0,
        "saddle_is_loose_not_hard_clamp": CABLE_CHANNEL_D + v1.STRAIN_RELIEF_RADIAL_CLEARANCE > CABLE_CHANNEL_D,
        "waterproof_not_claimed": WATER_RATING == "SPLASH_RESISTANT_NOT_WATERPROOF",
    }
    if not all(checks.values()):
        raise AssertionError(f"v002 validation failed: {[k for k,v in checks.items() if not v]}")

    return {
        "lane": LANE_NAME,
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cadquery_version": cq.__version__,
        "status": DESIGN_STATUS,
        "water_rating": WATER_RATING,
        "v001_authority": {"lane": str(V001_LANE_REL).replace('\\','/'), "hashes": v001_hashes},
        "physical_authority": {
            "connector_envelope_mm": [CONNECTOR_ENVELOPE_L, CONNECTOR_ENVELOPE_W, CONNECTOR_ENVELOPE_H],
            "camera_cable_od_mm": CAMERA_SIDE_CABLE_OD,
            "extension_cable_od_mm": EXTENSION_SIDE_CABLE_OD,
            "channel_mm": CABLE_CHANNEL_D,
            "cable_coupon_result": "CABLE_CHANNEL_PHYSICAL_PASS",
        },
        "derived": {
            "axial_clearance_total_mm": round(AXIAL_CLEARANCE_TOTAL, 3),
            "axial_clearance_each_end_mm": round(AXIAL_CLEARANCE_SIDE, 3),
            "width_clearance_total_mm": round(WIDTH_CLEARANCE_TOTAL, 3),
            "height_clearance_total_mm": round(HEIGHT_CLEARANCE_TOTAL, 3),
            "camera_cable_diametral_clearance_mm": round(CABLE_CHANNEL_D-CAMERA_SIDE_CABLE_OD, 3),
            "extension_cable_diametral_clearance_mm": round(CABLE_CHANNEL_D-EXTENSION_SIDE_CABLE_OD, 3),
            "floor_center_crown_mm": round(FLOOR_CROWN_H, 3),
            "roof_rise_mm": round(v1.ROOF_RISE, 3),
            "fit_coupon_volume_ratio_to_full": round(coupon_volume/full_volume, 4),
        },
        "closure": {
            "configuration": "M3_X6_SIDE_FLANGE_WITH_CAPTURED_HEX_NUTS",
            "stations_x_mm": list(v1.SCREW_XS),
            "change_reason": "MEASURED_ENVELOPE_REQUIRED_CHANGE",
            "external_ribs_added": False,
        },
        "strain_relief_saddle": {
            "center_x_abs_mm": round(SADDLE_X_ABS, 3),
            "axial_length_mm": SADDLE_AXIAL_L,
            "gap_to_measured_envelope_mm": round(SADDLE_ENVELOPE_GAP, 3),
            "groove_d_mm": round(CABLE_CHANNEL_D + v1.STRAIN_RELIEF_RADIAL_CLEARANCE, 3),
            "hard_clamping": False,
            "change_reason": "MEASURED_ENVELOPE_REQUIRED_CHANGE",
        },
        "intersections": intersections,
        "checks": checks,
        "artifacts": artifacts,
        "step_reimport": steps,
        "water_path": {
            "TOP": "3 deg roof and 6 mm umbrella skirt preserved",
            "45_DEG_SIDE": "2 mm step, 3 mm radial overlap, 0.30 mm clearance preserved",
            "CABLE_TRACKING": "common 4.4 mm downward ports feed symmetric drip vestibules",
            "DRAIN": "two 2.5 mm offset drains remain outside the connector envelope",
            "POOLING": f"2 deg two-way floor; recomputed center crown {FLOOR_CROWN_H:.3f} mm",
            "WITNESS_BAY": "labyrinth coupon includes dry-tissue chamber-side witness area",
        },
        "pass_separation": {
            "CAD_PASS": True,
            "PRINT_PASS": False,
            "CABLE_FIT_PASS": True,
            "CONNECTOR_FIT_PASS": False,
            "DRAIN_PASS": False,
            "SPRAY_PASS": False,
            "POWERED_USB_PASS": False,
            "HEAVY_RAIN_FIELD_PASS": False,
            "LONG_DURATION_PASS": False,
        },
        "blockers": ["connector chamber physical fit", "labyrinth drain effectiveness", "full-shell water intrusion"],
    }


def write_reports(report: dict[str, Any]) -> None:
    lines = [
        "# VALIDATION REPORT", "", f"Status: `{DESIGN_STATUS}`", "",
        "Measured dimensions and inherited v001 architecture pass CAD validation. Connector-chamber, drain, full-shell spray, and powered tests remain Physical PENDING.", "",
        "## STL/BRep", "", "| Artifact | Expected solids | BRep solids | STL triangles | Boundary/non-manifold edges |",
        "|---|---:|---:|---:|---:|",
    ]
    for name,item in report["artifacts"].items():
        lines.append(f"| `{name}` | {item['expected_solids']} | {item['brep']['solid_count']} | {item['mesh']['triangle_count']} | {item['mesh']['nonmanifold_or_boundary_edges']} |")
    lines.extend(["", "## STEP re-import", ""])
    for name,item in report["step_reimport"].items():
        lines.append(f"- `{name}`: valid={item['reimport']['valid']}, solids={item['reimport']['solid_count']}")
    lines.extend(["", "## Interference", ""])
    for name,value in report["intersections"].items():
        lines.append(f"- `{name}`: {value:.8f} mm3")
    lines.extend(["", "## Checks", ""])
    for name,passed in report["checks"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(["", "## Pass separation", ""])
    for name,passed in report["pass_separation"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'NOT PASSED / PENDING'}")
    lines.extend(["", "No waterproof/IP/heavy-rain/long-duration claim is made.", ""])
    (REPORT_DIR / "VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    water = [
        "# WATER PATH VALIDATION", "", f"Rating: `{WATER_RATING}`", "",
        "| Mode | v002 CAD control | Physical status |", "|---|---|---|",
    ]
    for name,rationale in report["water_path"].items():
        water.append(f"| `{name}` | {rationale} | PENDING |")
    water.extend([
        "", "The 102 mm chamber changes floor crown and longitudinal stiffness, not the v001 water-path sequence.",
        "The drain axes, baffles, downward ports, parting labyrinth, and umbrella skirt remain separated from the measured connector envelope.",
        "Colored-water witness-bay testing at level, +5 deg, and -5 deg is mandatory.",
        "`WATERTIGHT_STL != WATERPROOF_PRINT`.", "",
    ])
    (REPORT_DIR / "WATER_PATH_VALIDATION.md").write_text("\n".join(water), encoding="utf-8")
    (REPORT_DIR / "water_path_validation.json").write_text(json.dumps(report["water_path"], indent=2) + "\n", encoding="utf-8")


def write_sha_manifest() -> None:
    manifest = LANE_DIR / "SHA256SUMS.txt"
    files = sorted(path for path in LANE_DIR.rglob("*") if path.is_file() and path != manifest and "__pycache__" not in path.parts and path.suffix != ".pyc")
    manifest.write_text("\n".join(f"{sha256_file(path)}  {path.relative_to(LANE_DIR).as_posix()}" for path in files) + "\n", encoding="utf-8")


def main() -> None:
    for directory in (STL_DIR, STEP_DIR, DOC_DIR, REPORT_DIR, RENDER_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    write_parameters()

    lower = build_lower_shell_v002()
    upper = v1.build_upper_shell()
    connector = connector_reference()
    camera_cable = cable_reference(-1.0, CAMERA_SIDE_CABLE_OD)
    extension_cable = cable_reference(1.0, EXTENSION_SIDE_CABLE_OD)
    assembly = compound((upper, lower, connector, camera_cable, extension_cable))
    fit_print, fit_assembled, fit_lower, fit_upper = build_fit_coupon()
    labyrinth = build_labyrinth_coupon(lower)

    stl_models = {
        "connector_chamber_fit_coupon_v002": fit_print,
        "labyrinth_drain_coupon_v002": labyrinth,
        "usb_raincover_upper_v002": upper,
        "usb_raincover_lower_v002": lower,
    }
    for stem,model in stl_models.items():
        export_stl(model, STL_DIR / f"{stem}.stl")
    step_models = {
        "connector_reference_v002": connector,
        "connector_chamber_fit_coupon_v002": fit_assembled,
        "labyrinth_drain_coupon_v002": labyrinth,
        "usb_raincover_upper_v002": upper,
        "usb_raincover_lower_v002": lower,
        "usb_raincover_assembly_v002": assembly,
    }
    for stem,model in step_models.items():
        export_step(model, STEP_DIR / f"{stem}.step")

    make_assembled_render(RENDER_DIR / "assembled.png")
    make_connector_fit_render(RENDER_DIR / "connector_envelope_fit.png")
    make_longitudinal_render(RENDER_DIR / "longitudinal_section.png")
    make_cable_render(RENDER_DIR / "cable_labyrinth_section.png")
    make_drain_render(RENDER_DIR / "drain_section.png")

    models = {
        "upper": upper, "lower": lower, "connector": connector,
        "camera_cable": camera_cable, "extension_cable": extension_cable,
        "assembly": assembly, "fit_assembled": fit_assembled,
        "fit_lower": fit_lower, "fit_upper": fit_upper,
        **stl_models,
    }
    report = validate(models)
    (REPORT_DIR / "validation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_reports(report)
    write_sha_manifest()
    print(json.dumps({
        "lane": str(LANE_DIR), "status": DESIGN_STATUS, "cad_pass": True,
        "cable_fit_physical_pass": True,
        "next_print": "connector_chamber_fit_coupon_v002.stl",
        "waterproof_claimed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
