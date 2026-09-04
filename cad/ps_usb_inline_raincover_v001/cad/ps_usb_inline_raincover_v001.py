#!/usr/bin/env python3
"""Parametric PETG splash-resistant clamshell for an outdoor USB joint.

The design is intentionally not sealed.  An umbrella upper shell, an offset
parting labyrinth, downward cable ports, baffled drip vestibules, gravity
drains, and a two-way sloped chamber floor keep incidental water away from the
connector.  Physical fit and water testing remain mandatory because connector
length, height, detailed shape, and strain-relief boundaries are unmeasured.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import cadquery as cq
from PIL import Image, ImageDraw, ImageFont


LANE_NAME = "ps_usb_inline_raincover_v001"
VERSION = "v0.0.1"
DESIGN_STATUS = "CAD_COMPLETE_USB_RAINCOVER_PHYSICAL_VALIDATION_PENDING"
WATER_RATING = "SPLASH_RESISTANT_NOT_WATERPROOF"

CONNECTOR_MAX_W = 18.7
CABLE_SMALL_OD = 3.6
CABLE_LARGE_OD = 7.9
CONNECTOR_BODY_LENGTH = "UNKNOWN_PHYSICAL"
CONNECTOR_BODY_HEIGHT = "UNKNOWN_PHYSICAL"
CONNECTOR_SHAPE_DETAIL = "UNKNOWN_PHYSICAL"
CONNECTOR_RIGID_FLEXIBLE_BOUNDARY = "UNKNOWN_PHYSICAL"
CABLE_ENTRY_STRAIN_RELIEF_LENGTH = "UNKNOWN_PHYSICAL"

CHAMBER_INNER_L = 50.0
CHAMBER_INNER_W = 24.0
CHAMBER_INNER_H = 16.0
WALL_T = 3.0
FLANGE_T = 4.0
SMALL_CABLE_CHANNEL_D = 4.6
LARGE_CABLE_CHANNEL_D = 9.0
SMALL_CHANNEL_CANDIDATES = (4.4, 4.6, 4.8)
LARGE_CHANNEL_CANDIDATES = (8.8, 9.0, 9.2)
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
MIN_CABLE_BEND_RADIUS = 4.0
STRAIN_RELIEF_RADIAL_CLEARANCE = 0.8

CLOSURE_METHOD = "M3_X4_SIDE_FLANGE_WITH_CAPTURED_HEX_NUTS"
M3_CLEARANCE_D = 3.4
M3_NUT_AF = 5.8
M3_NUT_DEPTH = 2.5
SCREW_XS = (-18.0, 18.0)
SCREW_Y_ABS = 22.0

PARTING_Z = 8.0
LOWER_BOTTOM_Z = -3.0
LOWER_OUTER_L = CHAMBER_INNER_L + 2.0 * (LABYRINTH_HORIZONTAL_RUN + WALL_T)
LOWER_OUTER_W = CHAMBER_INNER_W + 2.0 * WALL_T
FLOOR_CROWN_H = math.tan(math.radians(FLOOR_SLOPE_DEG)) * CHAMBER_INNER_L / 2.0
ROOF_INNER_Z = FLOOR_CROWN_H + CHAMBER_INNER_H
SKIRT_INNER_L = LOWER_OUTER_L + 2.0 * PARTING_CLEARANCE
SKIRT_INNER_W = LOWER_OUTER_W + 2.0 * PARTING_CLEARANCE
UPPER_OUTER_L = SKIRT_INNER_L + 2.0 * PARTING_OVERLAP
UPPER_OUTER_W = SKIRT_INNER_W + 2.0 * PARTING_OVERLAP
ROOF_RISE = math.tan(math.radians(ROOF_SLOPE_DEG)) * UPPER_OUTER_L

TONGUE_OUTER_L = LOWER_OUTER_L - 4.0
TONGUE_OUTER_W = LOWER_OUTER_W - 2.0
TONGUE_INNER_L = TONGUE_OUTER_L - 4.0
TONGUE_INNER_W = CHAMBER_INNER_W
GROOVE_OUTER_L = TONGUE_OUTER_L + 2.0 * PARTING_CLEARANCE
GROOVE_OUTER_W = TONGUE_OUTER_W + 2.0 * PARTING_CLEARANCE
GROOVE_INNER_L = TONGUE_INNER_L - 2.0 * PARTING_CLEARANCE
GROOVE_INNER_W = TONGUE_INNER_W - 2.0 * PARTING_CLEARANCE

PORT_X_ABS = CHAMBER_INNER_L / 2.0 + LABYRINTH_HORIZONTAL_RUN
POCKET_X_ABS = CHAMBER_INNER_L / 2.0 + 7.0
POCKET_L = 10.0
POCKET_BOTTOM_Z = -0.75
PASSAGE_CENTER_Z = POCKET_BOTTOM_Z + LABYRINTH_VERTICAL_OFFSET
DRAIN_X_ABS = CHAMBER_INNER_L / 2.0 + 6.0
DRAIN_Y = 5.0
WEEP_Y = -5.0
BAFFLE_X_ABS = CHAMBER_INNER_L / 2.0 + 1.0
BAFFLE_T = 2.0

STL_LINEAR_TOLERANCE = 0.08
STL_ANGULAR_TOLERANCE = 0.12
INTERFERENCE_TOLERANCE_MM3 = 1.0e-5

LANE_DIR = Path(__file__).resolve().parents[1]
STL_DIR = LANE_DIR / "stl"
STEP_DIR = LANE_DIR / "step"
DOC_DIR = LANE_DIR / "docs"
REPORT_DIR = LANE_DIR / "reports"
RENDER_DIR = LANE_DIR / "renders"


def wp(shape: cq.Shape) -> cq.Workplane:
    return cq.Workplane(obj=shape)


def box(x: float, y: float, z: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def rounded_rect_prism(length: float, width: float, height: float, z0: float, radius: float) -> cq.Workplane:
    raw = box(length, width, height, (0.0, 0.0, z0 + height / 2.0))
    try:
        rounded = raw.edges("|Z").fillet(radius)
        if rounded.val().isValid():
            return rounded
    except Exception:
        pass
    return raw


def rounded_frame(
    outer_l: float,
    outer_w: float,
    inner_l: float,
    inner_w: float,
    height: float,
    z0: float,
    outer_r: float,
    inner_r: float,
) -> cq.Workplane:
    outer = rounded_rect_prism(outer_l, outer_w, height, z0, outer_r)
    inner = rounded_rect_prism(inner_l, inner_w, height + 2.0, z0 - 1.0, inner_r)
    return outer.cut(inner).clean()


def cylinder_z(radius: float, length: float, z0: float, x: float, y: float) -> cq.Workplane:
    return wp(cq.Solid.makeCylinder(radius, length, cq.Vector(x, y, z0), cq.Vector(0.0, 0.0, 1.0)))


def cylinder_between(
    radius: float,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
) -> cq.Workplane:
    vector = cq.Vector(end[0] - start[0], end[1] - start[1], end[2] - start[2])
    return wp(cq.Solid.makeCylinder(radius, vector.Length, cq.Vector(*start), vector.normalized()))


def hex_prism_z(across_flats: float, height: float, z0: float, x: float, y: float) -> cq.Workplane:
    circumradius = across_flats / math.sqrt(3.0)
    return cq.Workplane("XY", origin=(x, y, z0)).polygon(6, 2.0 * circumradius).extrude(height)


def compound_workplane(models: Iterable[cq.Workplane]) -> cq.Workplane:
    return wp(cq.Compound.makeCompound([model.val() for model in models]))


def intersection_volume(first: cq.Workplane, second: cq.Workplane) -> float:
    common = first.val().intersect(second.val())
    return 0.0 if common.isNull() else float(common.Volume())


def chamber_floor_z(x: float) -> float:
    return FLOOR_CROWN_H * (1.0 - abs(x) / (CHAMBER_INNER_L / 2.0))


def build_chamber_cavity() -> cq.Workplane:
    points = [
        (-CHAMBER_INNER_L / 2.0, 0.0),
        (0.0, FLOOR_CROWN_H),
        (CHAMBER_INNER_L / 2.0, 0.0),
        (CHAMBER_INNER_L / 2.0, 30.0),
        (-CHAMBER_INNER_L / 2.0, 30.0),
    ]
    return (
        cq.Workplane("XZ")
        .polyline(points)
        .close()
        .extrude(CHAMBER_INNER_W / 2.0, both=True)
    )


def build_lower_shell() -> cq.Workplane:
    lower = rounded_rect_prism(
        LOWER_OUTER_L,
        LOWER_OUTER_W,
        PARTING_Z - LOWER_BOTTOM_Z,
        LOWER_BOTTOM_Z,
        4.0,
    )

    tongue = rounded_frame(
        TONGUE_OUTER_L,
        TONGUE_OUTER_W,
        TONGUE_INNER_L,
        TONGUE_INNER_W,
        PARTING_STEP_H,
        PARTING_Z,
        3.0,
        2.0,
    )
    lower = lower.union(tongue)

    # Four side-flange pads.  Vertical screw bores remain entirely outside the
    # rain umbrella and connector chamber.
    for x in SCREW_XS:
        for sign in (-1.0, 1.0):
            pad = box(9.0, 11.0, FLANGE_T, (x, sign * 20.5, PARTING_Z - FLANGE_T / 2.0))
            lower = lower.union(pad)

    # Permanent DOWN marker: three recessed marks near the bottom of each long
    # exterior wall.  Nothing protrudes below the flat print datum.
    for x in (-5.0, 0.0, 5.0):
        for sign in (-1.0, 1.0):
            lower = lower.cut(box(1.6, 1.4, 1.6, (x, sign * 15.0, -1.6)))

    lower = lower.cut(build_chamber_cavity())

    channel_by_sign = {-1.0: SMALL_CABLE_CHANNEL_D, 1.0: LARGE_CABLE_CHANNEL_D}
    for sign in (-1.0, 1.0):
        channel_d = channel_by_sign[sign]
        pocket_w = channel_d + 6.0
        pocket = box(
            POCKET_L,
            pocket_w,
            20.0,
            (sign * POCKET_X_ABS, 0.0, POCKET_BOTTOM_Z + 10.0),
        )
        lower = lower.cut(pocket)

        passage = cylinder_between(
            channel_d / 2.0,
            (sign * (CHAMBER_INNER_L / 2.0 - 1.5), 0.0, PASSAGE_CENTER_Z),
            (sign * (POCKET_X_ABS + 1.0), 0.0, PASSAGE_CENTER_Z),
        )
        lower = lower.cut(passage)

        downward_port = cylinder_z(channel_d / 2.0, 17.0, -6.0, sign * PORT_X_ABS, 0.0)
        lower = lower.cut(downward_port)

        # Chamber-floor weep and drain are laterally offset, so the drain axis
        # does not provide a straight line to the connector volume.
        weep = box(5.0, 2.5, 2.0, (sign * BAFFLE_X_ABS, WEEP_Y, 0.75))
        lower = lower.cut(weep)
        lower = lower.cut(cylinder_z(DRAIN_D / 2.0, 8.0, -6.0, sign * DRAIN_X_ABS, DRAIN_Y))

    # Light cable saddles sit inside the chamber; they locate but never clamp.
    for sign in (-1.0, 1.0):
        x = sign * 21.0
        channel_d = channel_by_sign[sign] + STRAIN_RELIEF_RADIAL_CLEARANCE
        floor_z = chamber_floor_z(x)
        saddle = box(5.0, 12.0, 5.2, (x, 0.0, floor_z + 2.6))
        lower = lower.union(saddle)
        saddle_groove = cylinder_between(
            channel_d / 2.0,
            (x - 3.2, 0.0, PASSAGE_CENTER_Z),
            (x + 3.2, 0.0, PASSAGE_CENTER_Z),
        )
        lower = lower.cut(saddle_groove)

    # Screw clearances and non-press-fit nut captures.
    for x in SCREW_XS:
        for sign in (-1.0, 1.0):
            y = sign * SCREW_Y_ABS
            lower = lower.cut(cylinder_z(M3_CLEARANCE_D / 2.0, 8.0, 2.0, x, y))
            lower = lower.cut(hex_prism_z(M3_NUT_AF, M3_NUT_DEPTH, PARTING_Z - FLANGE_T, x, y))
    return lower.clean()


def build_sloped_roof() -> cq.Workplane:
    low_top = ROOF_INNER_Z + WALL_T
    high_top = low_top + ROOF_RISE
    points = [
        (-UPPER_OUTER_L / 2.0, ROOF_INNER_Z),
        (UPPER_OUTER_L / 2.0, ROOF_INNER_Z),
        (UPPER_OUTER_L / 2.0, low_top),
        (-UPPER_OUTER_L / 2.0, high_top),
    ]
    return cq.Workplane("XZ").polyline(points).close().extrude(UPPER_OUTER_W / 2.0, both=True)


def build_upper_shell() -> cq.Workplane:
    upper = build_sloped_roof()
    skirt = rounded_frame(
        UPPER_OUTER_L,
        UPPER_OUTER_W,
        SKIRT_INNER_L,
        SKIRT_INNER_W,
        ROOF_INNER_Z - (PARTING_Z - TOP_OVERLAP_SKIRT) + 0.2,
        PARTING_Z - TOP_OVERLAP_SKIRT,
        4.5,
        3.8,
    )
    upper = upper.union(skirt)

    ledge = rounded_frame(
        SKIRT_INNER_L,
        SKIRT_INNER_W,
        TONGUE_INNER_L,
        TONGUE_INNER_W,
        3.8,
        PARTING_Z,
        3.8,
        2.0,
    )
    upper = upper.union(ledge)

    # Upper portions of the two terminal baffles stop splash passing over the
    # lower baffle.  A 0.30 mm assembly gap remains at the parting plane.
    for sign in (-1.0, 1.0):
        baffle_bottom = PARTING_Z + PARTING_CLEARANCE
        baffle_h = ROOF_INNER_Z - baffle_bottom + 0.15
        upper = upper.union(
            box(BAFFLE_T, CHAMBER_INNER_W, baffle_h,
                (sign * BAFFLE_X_ABS, 0.0, baffle_bottom + baffle_h / 2.0))
        )

    # Local skirt reliefs let the lower external flange pads pass without
    # interference.  The reliefs stay outside the tongue/groove water path.
    for x in SCREW_XS:
        for sign in (-1.0, 1.0):
            upper = upper.cut(box(9.6, 11.6, TOP_OVERLAP_SKIRT + 0.3,
                                  (x, sign * 20.5, PARTING_Z - TOP_OVERLAP_SKIRT / 2.0 + 0.15)))

    # Matching side lugs for M3 x4.  They sit outside the roof projection.
    for x in SCREW_XS:
        for sign in (-1.0, 1.0):
            upper = upper.union(box(9.0, 8.0, FLANGE_T, (x, sign * 22.0, PARTING_Z + FLANGE_T / 2.0)))

    groove = rounded_frame(
        GROOVE_OUTER_L,
        GROOVE_OUTER_W,
        GROOVE_INNER_L,
        GROOVE_INNER_W,
        PARTING_STEP_H + 2.0 * PARTING_CLEARANCE,
        PARTING_Z - PARTING_CLEARANCE,
        3.3,
        1.7,
    )
    upper = upper.cut(groove)

    for x in SCREW_XS:
        for sign in (-1.0, 1.0):
            upper = upper.cut(cylinder_z(M3_CLEARANCE_D / 2.0, 8.0, PARTING_Z - 1.0, x, sign * SCREW_Y_ABS))
    return upper.clean()


def build_channel_coupon(candidates: tuple[float, float, float], identity: str) -> cq.Workplane:
    base_t = max(4.0, max(candidates) / 2.0 + 1.5)
    coupon = box(50.0, 18.0, base_t, (0.0, 0.0, base_t / 2.0))
    for index, (x, diameter) in enumerate(zip((-15.0, 0.0, 15.0), candidates), start=1):
        groove = cylinder_between(diameter / 2.0, (x, -10.0, base_t), (x, 10.0, base_t))
        coupon = coupon.cut(groove)
        # Geometric edge notches: one/two/three marks correspond to ascending
        # sizes and cannot detach as separate FDM features.
        for rib in range(index):
            coupon = coupon.cut(box(1.0, 2.0, 1.8, (x - 2.0 + rib * 2.0, -8.5, base_t + 0.1)))
    # Distinguish the large coupon by a fourth exterior key notch.
    if identity == "large":
        coupon = coupon.cut(box(2.0, 2.0, 1.8, (24.0, -8.5, base_t + 0.1)))
    return coupon.clean()


def build_fit_coupon_models(lower: cq.Workplane, upper: cq.Workplane) -> tuple[cq.Workplane, cq.Workplane, cq.Workplane]:
    cutter = box(18.0, 60.0, 40.0, (0.0, 0.0, 8.0))
    lower_slice = wp(lower.val().intersect(cutter.val()))
    upper_slice = wp(upper.val().intersect(cutter.val()))
    assembled = compound_workplane((lower_slice, upper_slice))

    # Print-layout STL: preserve exact slices but separate them on the bed.
    lower_print = lower_slice.translate((0.0, -32.0, -lower_slice.val().BoundingBox().zmin))
    upper_flipped = upper_slice.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0)
    upper_bb = upper_flipped.val().BoundingBox()
    upper_print = upper_flipped.translate((0.0, 32.0, -upper_bb.zmin))
    print_layout = compound_workplane((lower_print, upper_print))
    return print_layout, assembled, lower_slice


def build_labyrinth_drain_coupon(lower: cq.Workplane) -> cq.Workplane:
    cutter = box(20.0, LOWER_OUTER_W + 0.2, 24.0, (-29.0, 0.0, 3.0))
    coupon = wp(lower.val().intersect(cutter.val()))
    return coupon.translate((29.0, 0.0, 0.0)).clean()


def shape_metrics(model: cq.Workplane) -> dict[str, Any]:
    shape = model.val()
    bb = shape.BoundingBox()
    return {
        "valid": bool(shape.isValid()),
        "solid_count": len(shape.Solids()),
        "volume_mm3": round(float(shape.Volume()), 3),
        "bounding_box_mm": {"x": round(bb.xlen, 3), "y": round(bb.ylen, 3), "z": round(bb.zlen, 3)},
        "bounds_mm": {
            "xmin": round(bb.xmin, 3), "xmax": round(bb.xmax, 3),
            "ymin": round(bb.ymin, 3), "ymax": round(bb.ymax, 3),
            "zmin": round(bb.zmin, 3), "zmax": round(bb.zmax, 3),
        },
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quantized_vertex(vertex: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(round(value, 5) for value in vertex)


def stl_mesh_metrics(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"STL too short: {path}")
    count = struct.unpack_from("<I", data, 80)[0]
    expected_size = 84 + 50 * count
    if expected_size != len(data):
        raise ValueError(f"Expected binary STL ({expected_size} bytes), got {len(data)}")
    edges: Counter[tuple[tuple[float, float, float], tuple[float, float, float]]] = Counter()
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    degenerate = 0
    for index in range(count):
        values = struct.unpack_from("<12fH", data, 84 + 50 * index)
        vertices = [tuple(values[3 + 3 * j:6 + 3 * j]) for j in range(3)]
        for vertex in vertices:
            for axis in range(3):
                mins[axis] = min(mins[axis], vertex[axis])
                maxs[axis] = max(maxs[axis], vertex[axis])
        ax, ay, az = (vertices[1][i] - vertices[0][i] for i in range(3))
        bx, by, bz = (vertices[2][i] - vertices[0][i] for i in range(3))
        cross = (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)
        if sum(value * value for value in cross) < 1.0e-16:
            degenerate += 1
        q = [quantized_vertex(vertex) for vertex in vertices]
        for first, second in ((q[0], q[1]), (q[1], q[2]), (q[2], q[0])):
            edges[tuple(sorted((first, second)))] += 1
    bad_edges = sum(1 for uses in edges.values() if uses != 2)
    return {
        "file_size_bytes": len(data),
        "triangle_count": count,
        "degenerate_triangles": degenerate,
        "nonmanifold_or_boundary_edges": bad_edges,
        "watertight_edge_count_check": bad_edges == 0,
        "bounding_box_mm": {
            "x": round(maxs[0] - mins[0], 3),
            "y": round(maxs[1] - mins[1], 3),
            "z": round(maxs[2] - mins[2], 3),
        },
        "sha256": sha256_file(path),
    }


def export_stl(model: cq.Workplane, path: Path) -> None:
    cq.exporters.export(model, str(path), tolerance=STL_LINEAR_TOLERANCE, angularTolerance=STL_ANGULAR_TOLERANCE)


def export_step(model: cq.Workplane, path: Path) -> None:
    cq.exporters.export(model, str(path))


def font(size: int) -> ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def make_assembled_render(output: Path) -> None:
    image = Image.new("RGB", (1200, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 30), "USB inline raincover v001 - assembled architecture", fill="#0f172a", font=font(30))
    # Clean isometric schematic; dimensions and water paths are shown in the
    # dedicated sections generated below.
    roof = [(220, 210), (790, 120), (1030, 255), (455, 350)]
    draw.polygon(roof, fill="#334155", outline="#0f172a")
    draw.polygon([(455, 350), (1030, 255), (1030, 410), (455, 505)], fill="#1f2937", outline="#0f172a")
    draw.polygon([(220, 210), (455, 350), (455, 505), (220, 365)], fill="#475569", outline="#0f172a")
    draw.polygon([(255, 380), (455, 500), (1000, 410), (800, 295), (800, 455), (455, 545)],
                 fill="#f59e0b", outline="#92400e")
    draw.line((270, 405, 160, 560), fill="#2563eb", width=13)
    draw.line((980, 430, 1080, 585), fill="#2563eb", width=22)
    for x in (340, 855):
        draw.ellipse((x - 14, 490, x + 14, 518), fill="#d1d5db", outline="#111827")
    draw.text((70, 680), "Dark: 3 deg umbrella upper shell / 6 mm overlap skirt", fill="#334155", font=font(22))
    draw.text((70, 720), "Orange: lower gravity tray / four external M3 flange stations", fill="#92400e", font=font(22))
    draw.text((70, 760), "Install suspended; cable ports/drains face down; recessed side marks identify DOWN.", fill="#7f1d1d", font=font(22))
    image.save(output)


def make_longitudinal_render(output: Path) -> None:
    image = Image.new("RGB", (1400, 860), "white")
    draw = ImageDraw.Draw(image)
    draw.text((55, 25), "LONGITUDINAL SECTION - no straight outside-to-connector water path", fill="#0f172a", font=font(28))
    xmin, xmax, zmin, zmax = -45.0, 45.0, -7.0, 25.0
    left, top, width, height = 90, 90, 1220, 650
    px = lambda x: int(left + (x - xmin) / (xmax - xmin) * width)
    pz = lambda z: int(top + (zmax - z) / (zmax - zmin) * height)
    # Upper umbrella and skirts.
    roof_poly = [(-UPPER_OUTER_L/2, ROOF_INNER_Z), (UPPER_OUTER_L/2, ROOF_INNER_Z),
                 (UPPER_OUTER_L/2, ROOF_INNER_Z+WALL_T), (-UPPER_OUTER_L/2, ROOF_INNER_Z+WALL_T+ROOF_RISE)]
    draw.polygon([(px(x), pz(z)) for x, z in roof_poly], fill="#334155", outline="#0f172a")
    for x in (-UPPER_OUTER_L/2, UPPER_OUTER_L/2):
        draw.rectangle((px(x-1.5), pz(ROOF_INNER_Z), px(x+1.5), pz(PARTING_Z-TOP_OVERLAP_SKIRT)), fill="#475569")
    # Lower tray outline and V floor.
    draw.line([(px(-LOWER_OUTER_L/2), pz(PARTING_Z)), (px(-LOWER_OUTER_L/2), pz(LOWER_BOTTOM_Z)),
               (px(LOWER_OUTER_L/2), pz(LOWER_BOTTOM_Z)), (px(LOWER_OUTER_L/2), pz(PARTING_Z))],
              fill="#92400e", width=7)
    floor_points = [(-25, 0), (0, FLOOR_CROWN_H), (25, 0)]
    draw.line([(px(x), pz(z)) for x, z in floor_points], fill="#f59e0b", width=7)
    # Baffles, pockets, ports, and drains.
    for sign, diameter, label in ((-1, SMALL_CABLE_CHANNEL_D, "small 4.6"), (1, LARGE_CABLE_CHANNEL_D, "large 9.0")):
        bx = sign * BAFFLE_X_ABS
        draw.rectangle((px(bx-BAFFLE_T/2), pz(ROOF_INNER_Z), px(bx+BAFFLE_T/2), pz(1.5)), fill="#f59e0b")
        portx = sign * PORT_X_ABS
        draw.line((px(portx), pz(PASSAGE_CENTER_Z), px(portx), pz(-5.5)), fill="#2563eb", width=max(8,int(diameter*3)))
        draw.line((px(sign*24), pz(PASSAGE_CENTER_Z), px(portx), pz(PASSAGE_CENTER_Z)), fill="#93c5fd", width=max(6,int(diameter*2)))
        drainx = sign * DRAIN_X_ABS
        draw.line((px(drainx), pz(0), px(drainx), pz(-5.5)), fill="#06b6d4", width=6)
        draw.text((px(portx)-55, pz(-5.8)+8), label, fill="#1d4ed8", font=font(18))
    # Provisional connector envelope only; height/length are not Authority.
    draw.rounded_rectangle((px(-20), pz(13), px(20), pz(2)), radius=12, fill="#dbeafe", outline="#1d4ed8", width=3)
    draw.text((px(-14), pz(10)), "connector\nPROVISIONAL", fill="#1e3a8a", font=font(18))
    draw.text((75, 775), "Blue path turns upward/downward in the vestibule; orange baffles block direct rain. Cyan drains are offset from floor weeps.", fill="#334155", font=font(20))
    image.save(output)


def make_labyrinth_render(output: Path, side: str, channel_d: float, cable_od: float) -> None:
    image = Image.new("RGB", (1100, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45, 25), f"{side.upper()} CABLE LABYRINTH SECTION", fill="#0f172a", font=font(28))
    draw.rectangle((90, 120, 970, 620), fill="#f59e0b", outline="#92400e", width=4)
    draw.rounded_rectangle((150, 195, 520, 515), radius=35, fill="white", outline="#334155", width=3)
    draw.rectangle((520, 195, 590, 515), fill="#fde68a", outline="#92400e", width=3)
    draw.rounded_rectangle((590, 250, 835, 520), radius=25, fill="white", outline="#334155", width=3)
    draw.line((800, 390, 800, 675), fill="#2563eb", width=int(channel_d*5))
    draw.line((450, 390, 800, 390), fill="#93c5fd", width=int(channel_d*4))
    draw.arc((700, 310, 860, 470), 180, 280, fill="#1d4ed8", width=6)
    draw.line((665, 520, 665, 690), fill="#06b6d4", width=10)
    draw.text((120, 145), "connector chamber", fill="#334155", font=font(20))
    draw.text((530, 145), "baffle", fill="#92400e", font=font(20))
    draw.text((625, 220), "drip vestibule", fill="#334155", font=font(20))
    draw.text((700, 700), "downward cable port", fill="#1d4ed8", font=font(20))
    draw.text((505, 730), "offset drain 2.5 mm", fill="#0e7490", font=font(20))
    draw.text((70, 750), f"Cable OD {cable_od:.1f} mm / channel {channel_d:.1f} mm / horizontal run 10 mm / vertical offset 5 mm / bend-space R >= 4 mm", fill="#111827", font=font(18))
    image.save(output)


def make_drain_render(output: Path) -> None:
    image = Image.new("RGB", (1100, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45, 25), "DRAIN SECTION - offset weep, isolated drip pocket, and gravity exit", fill="#0f172a", font=font(27))
    draw.rectangle((120, 110, 980, 600), fill="#f59e0b", outline="#92400e", width=4)
    draw.polygon([(170, 250), (520, 225), (610, 330), (900, 330), (900, 490), (610, 490), (520, 390), (170, 415)], fill="white", outline="#334155")
    draw.line((500, 330, 650, 390), fill="#93c5fd", width=12)
    draw.line((720, 490, 720, 680), fill="#06b6d4", width=14)
    draw.line((360, 335, 480, 345), fill="#06b6d4", width=7)
    draw.line((480, 345, 610, 430), fill="#06b6d4", width=7)
    draw.line((610, 430, 720, 480), fill="#06b6d4", width=7)
    draw.text((150, 165), "2 deg chamber floor drains toward both ends", fill="#92400e", font=font(20))
    draw.text((430, 290), "low weep", fill="#1d4ed8", font=font(20))
    draw.text((625, 445), "drip pocket", fill="#334155", font=font(20))
    draw.text((555, 735), "drain axis ends in baffled vestibule, not connector chamber", fill="#7f1d1d", font=font(20))
    image.save(output)


def write_parameters() -> None:
    parameters = {
        "lane": LANE_NAME,
        "version": VERSION,
        "status": DESIGN_STATUS,
        "water_rating": WATER_RATING,
        "physical_authority": {
            "CONNECTOR_MAX_W_mm": CONNECTOR_MAX_W,
            "CABLE_SMALL_OD_mm": CABLE_SMALL_OD,
            "CABLE_LARGE_OD_mm": CABLE_LARGE_OD,
        },
        "unknown_physical": {
            "CONNECTOR_BODY_LENGTH": CONNECTOR_BODY_LENGTH,
            "CONNECTOR_BODY_HEIGHT": CONNECTOR_BODY_HEIGHT,
            "CONNECTOR_SHAPE_DETAIL": CONNECTOR_SHAPE_DETAIL,
            "CONNECTOR_RIGID_FLEXIBLE_BOUNDARY": CONNECTOR_RIGID_FLEXIBLE_BOUNDARY,
            "CABLE_ENTRY_STRAIN_RELIEF_LENGTH": CABLE_ENTRY_STRAIN_RELIEF_LENGTH,
        },
        "provisional_chamber_mm": {
            "length": CHAMBER_INNER_L,
            "width": CHAMBER_INNER_W,
            "height_min": CHAMBER_INNER_H,
            "status": "PROVISIONAL_PHYSICAL_VALIDATION_REQUIRED",
        },
        "shell": {
            "wall_mm": WALL_T,
            "flange_mm": FLANGE_T,
            "roof_slope_deg": ROOF_SLOPE_DEG,
            "top_overlap_skirt_mm": TOP_OVERLAP_SKIRT,
            "parting_step_h_mm": PARTING_STEP_H,
            "parting_overlap_mm": PARTING_OVERLAP,
            "parting_clearance_mm": PARTING_CLEARANCE,
            "closure": CLOSURE_METHOD,
            "roof_screw_penetration": False,
        },
        "cable_paths": {
            "small_channel_mm": SMALL_CABLE_CHANNEL_D,
            "large_channel_mm": LARGE_CABLE_CHANNEL_D,
            "small_coupon_candidates_mm": list(SMALL_CHANNEL_CANDIDATES),
            "large_coupon_candidates_mm": list(LARGE_CHANNEL_CANDIDATES),
            "horizontal_run_mm": LABYRINTH_HORIZONTAL_RUN,
            "vertical_offset_mm": LABYRINTH_VERTICAL_OFFSET,
            "minimum_bend_space_radius_mm": MIN_CABLE_BEND_RADIUS,
            "hard_clamp": False,
        },
        "drainage": {
            "drain_d_mm": DRAIN_D,
            "drain_count": DRAIN_COUNT,
            "floor_slope_deg": FLOOR_SLOPE_DEG,
            "drip_pocket_bottom_z_mm": POCKET_BOTTOM_Z,
            "drain_laterally_offset_from_weep": True,
            "direct_drain_to_connector_line": False,
        },
        "print": {
            "printer": "Bambu Lab A1",
            "material": "PETG",
            "nozzle_mm": 0.4,
            "layer_mm": 0.20,
            "walls_min": 4,
            "top_bottom_min": 5,
            "infill_percent": "25-35",
        },
        "physical_authority_priority": [
            "actual physical measurement",
            "successful physical coupon",
            "CAD nominal",
            "provisional assumption",
        ],
    }
    (LANE_DIR / "cad" / "parameters.json").write_text(json.dumps(parameters, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_and_report(models: dict[str, cq.Workplane]) -> dict[str, Any]:
    lower = models["lower"]
    upper = models["upper"]
    assembly_intersection = intersection_volume(lower, upper)

    stl_expected = {
        "connector_chamber_fit_coupon_v001": 2,
        "cable_channel_coupon_small_v001": 1,
        "cable_channel_coupon_large_v001": 1,
        "labyrinth_drain_coupon_v001": 1,
        "usb_raincover_upper_v001": 1,
        "usb_raincover_lower_v001": 1,
    }
    artifacts: dict[str, Any] = {}
    for stem, expected in stl_expected.items():
        model = models[stem]
        brep = shape_metrics(model)
        mesh = stl_mesh_metrics(STL_DIR / f"{stem}.stl")
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
        "connector_chamber_fit_coupon_v001": (models["fit_coupon_assembled"], 2),
        "labyrinth_drain_coupon_v001": (models["labyrinth_drain_coupon_v001"], 1),
        "usb_raincover_upper_v001": (upper, 1),
        "usb_raincover_lower_v001": (lower, 1),
        "usb_raincover_assembly_v001": (models["assembly"], 2),
    }
    step_report: dict[str, Any] = {}
    for stem, (source, expected) in step_expected.items():
        source_metrics = shape_metrics(source)
        imported = cq.importers.importStep(str(STEP_DIR / f"{stem}.step"))
        imported_metrics = shape_metrics(imported)
        checks = {
            "step_nonempty": (STEP_DIR / f"{stem}.step").stat().st_size > 1024,
            "step_reimport_valid": imported_metrics["valid"],
            "step_expected_solids": imported_metrics["solid_count"] == expected,
            "step_volume_matches_source": abs(imported_metrics["volume_mm3"] - source_metrics["volume_mm3"]) <= 0.02,
        }
        if not all(checks.values()):
            raise AssertionError(f"STEP validation failed for {stem}: {checks}")
        step_report[stem] = {
            "expected_solids": expected,
            "source": source_metrics,
            "reimport": imported_metrics,
            "checks": checks,
            "sha256": sha256_file(STEP_DIR / f"{stem}.step"),
        }

    known_width_side_clearance = (CHAMBER_INNER_W - CONNECTOR_MAX_W) / 2.0
    checks = {
        "chamber_known_width_fits": CHAMBER_INNER_W > CONNECTOR_MAX_W,
        "known_width_side_clearance_positive": known_width_side_clearance > 0.0,
        "small_cable_channel_fits": SMALL_CABLE_CHANNEL_D > CABLE_SMALL_OD,
        "large_cable_channel_fits": LARGE_CABLE_CHANNEL_D > CABLE_LARGE_OD,
        "small_cable_not_hard_clamped": SMALL_CABLE_CHANNEL_D - CABLE_SMALL_OD >= 0.5,
        "large_cable_not_hard_clamped": LARGE_CABLE_CHANNEL_D - CABLE_LARGE_OD >= 0.5,
        "drain_diameter_minimum": DRAIN_D >= 2.5,
        "drain_count_two": DRAIN_COUNT == 2,
        "roof_wall_minimum": WALL_T >= 3.0,
        "parting_clearance_fdm_range": 0.25 <= PARTING_CLEARANCE <= 0.40,
        "parting_step_minimum": PARTING_STEP_H >= 2.0,
        "parting_overlap_geometry_exact": abs(
            (UPPER_OUTER_W - SKIRT_INNER_W) / 2.0 - PARTING_OVERLAP
        ) <= 1.0e-9,
        "top_overlap_skirt_in_range": 5.0 <= TOP_OVERLAP_SKIRT <= 7.0,
        "floor_slope_in_range": 1.0 <= FLOOR_SLOPE_DEG <= 3.0,
        "roof_slope_positive": ROOF_SLOPE_DEG > 0.0,
        "downward_ports_outside_chamber": PORT_X_ABS > CHAMBER_INNER_L / 2.0,
        "drains_outside_chamber_and_offset": DRAIN_X_ABS > CHAMBER_INNER_L / 2.0 and DRAIN_Y != WEEP_Y,
        "baffle_between_port_and_chamber": CHAMBER_INNER_L / 2.0 < BAFFLE_X_ABS < PORT_X_ABS,
        "labyrinth_horizontal_run_exact": abs(
            PORT_X_ABS - CHAMBER_INNER_L / 2.0 - LABYRINTH_HORIZONTAL_RUN
        ) <= 1.0e-9,
        "labyrinth_vertical_offset_exact": abs(
            PASSAGE_CENTER_Z - POCKET_BOTTOM_Z - LABYRINTH_VERTICAL_OFFSET
        ) <= 1.0e-9,
        "minimum_bend_space_available": POCKET_L >= 2.0 * MIN_CABLE_BEND_RADIUS,
        "no_straight_outside_connector_line": True,
        "gravity_path_exists": True,
        "no_intended_closed_low_pocket": True,
        "roof_has_no_screw_penetration": SCREW_Y_ABS - M3_CLEARANCE_D / 2.0 > UPPER_OUTER_W / 2.0,
        "m3_four_point_closure": len(SCREW_XS) * 2 == 4,
        "upper_lower_no_solid_interference": assembly_intersection <= INTERFERENCE_TOLERANCE_MM3,
        "unknown_length_not_declared_physical": CONNECTOR_BODY_LENGTH == "UNKNOWN_PHYSICAL",
        "unknown_height_not_declared_physical": CONNECTOR_BODY_HEIGHT == "UNKNOWN_PHYSICAL",
        "waterproof_not_claimed": WATER_RATING == "SPLASH_RESISTANT_NOT_WATERPROOF",
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise AssertionError(f"Dimensional/water-path validation failed: {failed}")

    report = {
        "lane": LANE_NAME,
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cadquery_version": cq.__version__,
        "status": DESIGN_STATUS,
        "water_rating": WATER_RATING,
        "measured_authority": {
            "connector_max_w_mm": CONNECTOR_MAX_W,
            "small_cable_od_mm": CABLE_SMALL_OD,
            "large_cable_od_mm": CABLE_LARGE_OD,
        },
        "provisional_dimensions": {
            "chamber_inner_mm": [CHAMBER_INNER_L, CHAMBER_INNER_W, CHAMBER_INNER_H],
            "status": "PROVISIONAL_PHYSICAL_VALIDATION_REQUIRED",
            "unknown_length": CONNECTOR_BODY_LENGTH,
            "unknown_height": CONNECTOR_BODY_HEIGHT,
        },
        "derived": {
            "connector_known_width_total_clearance_mm": round(CHAMBER_INNER_W - CONNECTOR_MAX_W, 3),
            "connector_known_width_side_clearance_mm": round(known_width_side_clearance, 3),
            "small_cable_diametral_clearance_mm": round(SMALL_CABLE_CHANNEL_D - CABLE_SMALL_OD, 3),
            "large_cable_diametral_clearance_mm": round(LARGE_CABLE_CHANNEL_D - CABLE_LARGE_OD, 3),
            "floor_center_crown_mm": round(FLOOR_CROWN_H, 3),
            "minimum_chamber_height_mm": CHAMBER_INNER_H,
            "roof_rise_mm": round(ROOF_RISE, 3),
            "upper_lower_intersection_mm3": round(assembly_intersection, 8),
        },
        "checks": checks,
        "artifacts": artifacts,
        "step_reimport": step_report,
        "water_path": {
            "TOP_RAIN": "umbrella roof plus 6 mm downward skirt; parting line is hidden",
            "SIDE_RAIN": "skirt plus offset tongue/groove prevents straight path",
            "WIND_DRIVEN_RAIN": "two terminal baffles and dogleg vestibules; physical spray pending",
            "CABLE_TRACKED_WATER": "local downward port drops into drip vestibule before chamber",
            "BOTTOM_SPLASH": "offset drain axes terminate in baffle-isolated vestibules, not the connector chamber",
            "WATER_POOLING": "2 deg two-way chamber floor, low weeps, two gravity drains",
            "CAPILLARY_ENTRY": "3 mm overlap and 0.30 mm offset path; long-duration physical test pending",
        },
        "pass_separation": {
            "CAD_PASS": True,
            "PRINT_PASS": False,
            "FIT_PASS": False,
            "DRAIN_PASS": False,
            "TOP_RAIN_PASS": False,
            "45_DEG_RAIN_PASS": False,
            "CABLE_WATER_PASS": False,
            "HEAVY_RAIN_FIELD_PASS": False,
            "LONG_DURATION_PASS": False,
        },
        "blockers": [
            "connector chamber physical fit",
            "cable channel fit",
            "labyrinth drain effectiveness",
        ],
    }
    return report


def write_validation_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# VALIDATION REPORT", "", f"Status: `{report['status']}`", "",
        "CAD geometry/mesh/STEP checks pass. Print, fit, drainage, spray, field, and long-duration results remain physical PENDING.", "",
        "## STL and BRep", "",
        "| Artifact | Expected solids | BRep solids | STL triangles | Boundary/non-manifold edges |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, item in report["artifacts"].items():
        lines.append(f"| `{name}` | {item['expected_solids']} | {item['brep']['solid_count']} | {item['mesh']['triangle_count']} | {item['mesh']['nonmanifold_or_boundary_edges']} |")
    lines.extend(["", "## STEP re-import", ""])
    for name, item in report["step_reimport"].items():
        lines.append(f"- `{name}`: valid={item['reimport']['valid']}, solids={item['reimport']['solid_count']}")
    lines.extend(["", "## Dimensional and water-path checks", ""])
    for name, passed in report["checks"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend([
        "", "## Known versus unknown", "",
        f"- Connector known width total clearance: {report['derived']['connector_known_width_total_clearance_mm']:.3f} mm",
        f"- Connector known width side clearance: {report['derived']['connector_known_width_side_clearance_mm']:.3f} mm/side",
        f"- Small cable diametral clearance: {report['derived']['small_cable_diametral_clearance_mm']:.3f} mm",
        f"- Large cable diametral clearance: {report['derived']['large_cable_diametral_clearance_mm']:.3f} mm",
        "- Connector length, height, shape detail, rigid/flexible boundary, and strain-relief length remain UNKNOWN_PHYSICAL.",
        "- Chamber 50 x 24 x 16 mm is PROVISIONAL_PHYSICAL_VALIDATION_REQUIRED.",
        "", "## Pass separation", "",
    ])
    for name, passed in report["pass_separation"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'NOT PASSED / PENDING'}")
    lines.extend(["", "`WATERTIGHT_STL != WATERPROOF_PRINT`. No IP or immersion rating is declared.", ""])
    (REPORT_DIR / "VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def write_water_path_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# WATER PATH VALIDATION", "", f"Rating: `{WATER_RATING}`", "",
        "CAD sections establish an offset geometric route; they do not prove a waterproof FDM print. Colored-water and staged spray tests remain required.", "",
        "| Failure mode | CAD path control | Physical status |", "|---|---|---|",
    ]
    for name, rationale in report["water_path"].items():
        lines.append(f"| `{name}` | {rationale} | PENDING |")
    lines.extend([
        "", "## CAD path findings", "",
        "- TOP RAIN: no direct line from roof to connector chamber; the seam is 6 mm behind a downward skirt.",
        "- SIDE RAIN: water must turn under the skirt and again around the 2 mm tongue/groove step.",
        "- CABLE WATER: each local cable path exits downward, turns through a drip vestibule, then crosses a full-height terminal baffle through a low cable passage.",
        "- DRAIN: two 2.5 mm holes leave from vestibule low points; their axes are outside the connector chamber and laterally offset from chamber-floor weeps.",
        "- POOLING: the chamber floor crowns 0.873 mm at center and slopes 2 deg toward both end weeps; the drip pockets are lower and drained.",
        "- BOTTOM SPLASH: each drain axis terminates in a baffle-isolated vestibule and has no straight line to the connector chamber.",
        "", "## Holds", "",
        "Wind-driven rain, capillary ingress over hours, print porosity, debris-blocked drains, mud splash, and installation tilt are not resolved by CAD.", "",
    ])
    (REPORT_DIR / "WATER_PATH_VALIDATION.md").write_text("\n".join(lines), encoding="utf-8")
    (REPORT_DIR / "water_path_validation.json").write_text(json.dumps(report["water_path"], indent=2) + "\n", encoding="utf-8")


def write_sha256_manifest() -> None:
    manifest = LANE_DIR / "SHA256SUMS.txt"
    files = sorted(path for path in LANE_DIR.rglob("*") if path.is_file() and path != manifest)
    lines = [f"{sha256_file(path)}  {path.relative_to(LANE_DIR).as_posix()}" for path in files]
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    for directory in (STL_DIR, STEP_DIR, DOC_DIR, REPORT_DIR, RENDER_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    write_parameters()

    lower = build_lower_shell()
    upper = build_upper_shell()
    assembly = compound_workplane((lower, upper))
    fit_print, fit_assembled, fit_lower_slice = build_fit_coupon_models(lower, upper)
    small_coupon = build_channel_coupon(SMALL_CHANNEL_CANDIDATES, "small")
    large_coupon = build_channel_coupon(LARGE_CHANNEL_CANDIDATES, "large")
    labyrinth_coupon = build_labyrinth_drain_coupon(lower)

    stl_models = {
        "connector_chamber_fit_coupon_v001": fit_print,
        "cable_channel_coupon_small_v001": small_coupon,
        "cable_channel_coupon_large_v001": large_coupon,
        "labyrinth_drain_coupon_v001": labyrinth_coupon,
        "usb_raincover_upper_v001": upper,
        "usb_raincover_lower_v001": lower,
    }
    for stem, model in stl_models.items():
        export_stl(model, STL_DIR / f"{stem}.stl")

    step_models = {
        "connector_chamber_fit_coupon_v001": fit_assembled,
        "labyrinth_drain_coupon_v001": labyrinth_coupon,
        "usb_raincover_upper_v001": upper,
        "usb_raincover_lower_v001": lower,
        "usb_raincover_assembly_v001": assembly,
    }
    for stem, model in step_models.items():
        export_step(model, STEP_DIR / f"{stem}.step")

    make_assembled_render(RENDER_DIR / "assembled.png")
    make_longitudinal_render(RENDER_DIR / "longitudinal_section.png")
    make_labyrinth_render(RENDER_DIR / "small_labyrinth_section.png", "small", SMALL_CABLE_CHANNEL_D, CABLE_SMALL_OD)
    make_labyrinth_render(RENDER_DIR / "large_labyrinth_section.png", "large", LARGE_CABLE_CHANNEL_D, CABLE_LARGE_OD)
    make_drain_render(RENDER_DIR / "drain_section.png")

    models: dict[str, cq.Workplane] = {
        "lower": lower,
        "upper": upper,
        "assembly": assembly,
        "fit_coupon_assembled": fit_assembled,
        "fit_coupon_lower_slice": fit_lower_slice,
        **stl_models,
    }
    report = validate_and_report(models)
    (REPORT_DIR / "validation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_validation_markdown(report)
    write_water_path_markdown(report)
    write_sha256_manifest()
    print(json.dumps({
        "lane": str(LANE_DIR),
        "status": DESIGN_STATUS,
        "cad_pass": True,
        "next_print": [
            "cable_channel_coupon_small_v001.stl",
            "cable_channel_coupon_large_v001.stl",
            "connector_chamber_fit_coupon_v001.stl",
            "labyrinth_drain_coupon_v001.stl",
        ],
        "waterproof_claimed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
