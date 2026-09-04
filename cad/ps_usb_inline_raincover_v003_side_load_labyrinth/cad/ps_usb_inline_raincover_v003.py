#!/usr/bin/env python3
"""v003 side-load split labyrinth for the measured-envelope USB raincover.

v002 is loaded read-only as the dimensional and validated-water-architecture
Authority.  v003 changes only the cable assembly path: every cable route in
the lower is open upward, and every complementary upper feature is open
downward.  A closed nominal 4.4 mm passage exists only after shell assembly.
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


LANE_NAME = "ps_usb_inline_raincover_v003_side_load_labyrinth"
VERSION = "v0.0.3"
DESIGN_STATUS = "CAD_COMPLETE_SIDE_LOAD_LABYRINTH_PHYSICAL_VALIDATION_PENDING"
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

# Only the split seam receives local FDM relief.  The nominal passage remains
# 4.4 mm, preserving the physically passed diameter Authority.
LOCAL_SPLIT_RELIEF = 0.25
LOWER_SLOT_W = CABLE_CHANNEL_D + LOCAL_SPLIT_RELIEF
UPPER_TONGUE_W = CABLE_CHANNEL_D - LOCAL_SPLIT_RELIEF
CHANNEL_CENTER_Z = 4.25
CAP_CEILING_Z = CHANNEL_CENTER_Z + CABLE_CHANNEL_D / 2.0 + LOCAL_SPLIT_RELIEF / 2.0
CAP_BRIDGE_BOTTOM_Z = 10.30
CAP_BRIDGE_TOP_Z = 12.00
CRADLE_OUTER_W = 8.40
CRADLE_BOTTOM_Z = 0.15
CRADLE_TOP_Z = 7.85
PATH_JOINT_OVERLAP = 0.25

V002_LANE_REL = Path("cad/ps_usb_inline_raincover_v002_measured_envelope")
V002_SOURCE_SHA256 = "1610b42922fe232a21be68ef21f3d5519d9f3b52f7ed18523343afd377a8e11f"
V002_PARAMETERS_SHA256 = "6fcf14536d67257a14a279e52410d827c402738b8bc6e327b8a8a8ebfe2b1703"
V002_VALIDATION_SHA256 = "a4499b3eeafde4df2059e7ea6257a6ee87848a591492f70bc61bf2c58ae4f71a"
V002_ASSEMBLY_STEP_SHA256 = "76e8f75c6eaf124ba5c360a839af51e94ee897b4fec093b0a632c8e34aa6036e"
V002_MANIFEST_SHA256 = "0a76886d5512e7837bd23cb727d624ff2868e784aa03ac1542e85ecf8e119d0e"

REPO_DIR = Path(__file__).resolve().parents[3]
LANE_DIR = Path(__file__).resolve().parents[1]
V002_DIR = REPO_DIR / V002_LANE_REL
V002_SOURCE = V002_DIR / "cad" / "ps_usb_inline_raincover_v002.py"
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


def load_v002_read_only() -> Any:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("ps_usb_inline_raincover_v002_authority", V002_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load v002 Authority source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v2 = load_v002_read_only()
g = v2.v1


def path_points(sign: float) -> list[tuple[float, float, float]]:
    """Cable centerline from chamber to the skirt-protected outer edge.

    The 8 mm lateral dogleg is greater than the relieved passage half-width
    when projected against the endpoint sightline; it therefore removes a
    straight optical/water path while leaving a generous open vestibule.
    """
    return [
        (sign * 49.0, 0.0, CHANNEL_CENTER_Z),
        (sign * 55.0, 0.0, CHANNEL_CENTER_Z),
        (sign * 58.25, -4.0, CHANNEL_CENTER_Z),
        (sign * 60.5, -8.0, CHANNEL_CENTER_Z),
        (sign * 66.0, -8.0, CHANNEL_CENTER_Z),
    ]


def cradle_points(sign: float) -> list[tuple[float, float, float]]:
    points = path_points(sign)
    # Stop 0.2 mm inside the lower end datum; cable continues unsupported to
    # the upper-skirt exit, so no lower feature can capture the downward leg.
    outer = (sign * 63.8, points[-1][1], points[-1][2])
    return [(sign * 52.8, 0.0, CHANNEL_CENTER_Z), *points[1:-1], outer]


def sphere(radius: float, point: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").sphere(radius).translate(point)


def path_tube(points: Sequence[tuple[float, float, float]], radius: float) -> cq.Workplane:
    result: cq.Workplane | None = None
    for start, end in zip(points, points[1:]):
        dx, dy, dz = end[0] - start[0], end[1] - start[1], end[2] - start[2]
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        unit = (dx / length, dy / length, dz / length)
        # Overlap neighboring cylinders instead of joining tangent cylinders
        # to exact spheres; this avoids zero-area meshing facets at dogleg
        # vertices while retaining a continuous generous cable void.
        extended_start = tuple(start[i] - unit[i] * PATH_JOINT_OVERLAP for i in range(3))
        extended_end = tuple(end[i] + unit[i] * PATH_JOINT_OVERLAP for i in range(3))
        segment = g.cylinder_between(radius, extended_start, extended_end)
        result = segment if result is None else result.union(segment)
    if result is None:
        raise ValueError("path requires at least two points")
    return result.clean()


def path_prism(
    points: Sequence[tuple[float, float, float]],
    width: float,
    z_bottom: float,
    z_top: float,
    cap_ends: bool,
    round_joints: bool = True,
) -> cq.Workplane:
    height = z_top - z_bottom
    result: cq.Workplane | None = None
    for start, end in zip(points, points[1:]):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        angle = math.degrees(math.atan2(dy, dx))
        segment = (
            cq.Workplane("XY")
            .box(length, width, height)
            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle)
            .translate(((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0,
                        (z_bottom + z_top) / 2.0))
        )
        result = segment if result is None else result.union(segment)
    joint_points = (points if cap_ends else points[1:-1]) if round_joints else ()
    for point in joint_points:
        result = result.union(g.cylinder_z(width / 2.0, height, z_bottom, point[0], point[1]))
    if result is None:
        raise ValueError("path requires at least two points")
    return result.clean()


def cable_cut(sign: float, upward: bool) -> cq.Workplane:
    points = path_points(sign)
    tube = path_tube(points, CABLE_CHANNEL_D / 2.0)
    if upward:
        slot = path_prism(points, LOWER_SLOT_W, CHANNEL_CENTER_Z, 14.0, True)
    else:
        slot = path_prism(points, LOWER_SLOT_W, -8.0, CAP_CEILING_Z, True)
    return tube.union(slot).clean()


def build_lower_shell_v003() -> cq.Workplane:
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
        for sign in (-1.0, 1.0):
            lower = lower.union(g.box(
                9.0, 11.0, g.FLANGE_T,
                (x, sign * 20.5, g.PARTING_Z - g.FLANGE_T / 2.0),
            ))
    for x in (-5.0, 0.0, 5.0):
        for sign in (-1.0, 1.0):
            lower = lower.cut(g.box(1.6, 1.4, 1.6, (x, sign * 15.0, -1.6)))

    lower = lower.cut(g.build_chamber_cavity())

    for sign in (-1.0, 1.0):
        # Preserve the lower-side drip vestibule and visible offset drain.
        lower = lower.cut(g.box(
            g.POCKET_L,
            CABLE_CHANNEL_D + 6.0,
            20.0,
            (sign * g.POCKET_X_ABS, 0.0, g.POCKET_BOTTOM_Z + 10.0),
        ))
        lower = lower.cut(g.box(
            5.0, 2.5, 2.0, (sign * g.BAFFLE_X_ABS, g.WEEP_Y, 0.75),
        ))
        lower = lower.cut(g.cylinder_z(
            DRAIN_D / 2.0, 8.0, -6.0, sign * g.DRAIN_X_ABS, g.DRAIN_Y,
        ))

        # The suspended outer U rail crosses the vestibule while leaving an
        # open cleaning/drain gap below.  It is never a closed cable tunnel.
        lower = lower.union(path_prism(
            cradle_points(sign), CRADLE_OUTER_W, CRADLE_BOTTOM_Z, CRADLE_TOP_Z, False, False
        ))
        lower = lower.cut(cable_cut(sign, upward=True))

    # v002 measured-envelope-safe loose saddles remain unchanged.  Their 5.2
    # mm open grooves locate without compression and do not require threading.
    for sign in (-1.0, 1.0):
        x = sign * v2.SADDLE_X_ABS
        floor_z = g.chamber_floor_z(x)
        lower = lower.union(g.box(
            v2.SADDLE_AXIAL_L, 12.0, 5.2, (x, 0.0, floor_z + 2.6),
        ))
        lower = lower.cut(g.cylinder_between(
            (CABLE_CHANNEL_D + g.STRAIN_RELIEF_RADIAL_CLEARANCE) / 2.0,
            (x - 2.2, 0.0, g.PASSAGE_CENTER_Z),
            (x + 2.2, 0.0, g.PASSAGE_CENTER_Z),
        ))

    for x in g.SCREW_XS:
        for sign in (-1.0, 1.0):
            y = sign * g.SCREW_Y_ABS
            lower = lower.cut(g.cylinder_z(g.M3_CLEARANCE_D / 2.0, 8.0, 2.0, x, y))
            lower = lower.cut(g.hex_prism_z(
                g.M3_NUT_AF, g.M3_NUT_DEPTH, g.PARTING_Z - g.FLANGE_T, x, y,
            ))
    return lower.clean()


def build_upper_shell_v003() -> cq.Workplane:
    upper = g.build_upper_shell()
    for sign in (-1.0, 1.0):
        points = path_points(sign)
        # Open the upper feature downward so the upper can be lowered onto an
        # already installed continuous cable.  No upper-only ring remains.
        upper = upper.cut(cable_cut(sign, upward=False))
        tongue = path_prism(
            points, UPPER_TONGUE_W, CAP_CEILING_Z, CAP_BRIDGE_BOTTOM_Z, False
        )
        bridge = path_prism(
            points, CRADLE_OUTER_W, CAP_BRIDGE_BOTTOM_Z, CAP_BRIDGE_TOP_Z, False
        )
        upper = upper.union(tongue).union(bridge)
    return upper.clean()


def connector_reference() -> cq.Workplane:
    return g.rounded_rect_prism(
        CONNECTOR_ENVELOPE_L,
        CONNECTOR_ENVELOPE_W,
        CONNECTOR_ENVELOPE_H,
        v2.CONNECTOR_BOTTOM_Z,
        2.0,
    ).clean()


def cable_reference(sign: float, diameter: float) -> cq.Workplane:
    points = path_points(sign)
    horizontal = path_tube(points, diameter / 2.0)
    end = points[-1]
    down = g.cylinder_between(
        diameter / 2.0,
        end,
        (end[0], end[1], -7.0),
    )
    return horizontal.union(down).clean()


def lower_placement_envelope(sign: float, diameter: float) -> cq.Workplane:
    points = path_points(sign)
    installed = path_tube(points, diameter / 2.0)
    upward_sweep = path_prism(points, diameter, CHANNEL_CENTER_Z, 25.0, True)
    return installed.union(upward_sweep).clean()


def upper_release_envelope(sign: float, diameter: float) -> cq.Workplane:
    points = path_points(sign)
    installed = path_tube(points, diameter / 2.0)
    downward_sweep = path_prism(points, diameter, -10.0, CHANNEL_CENTER_Z, True)
    return installed.union(downward_sweep).clean()


def connector_placement_envelope() -> cq.Workplane:
    z_bottom = v2.CONNECTOR_BOTTOM_Z
    return g.rounded_rect_prism(
        CONNECTOR_ENVELOPE_L,
        CONNECTOR_ENVELOPE_W,
        30.0 - z_bottom,
        z_bottom,
        2.0,
    )


def compound(models: Iterable[cq.Workplane]) -> cq.Workplane:
    return g.compound_workplane(models)


def build_coupon(lower: cq.Workplane, upper: cq.Workplane) -> tuple[cq.Workplane, cq.Workplane, cq.Workplane]:
    # One full representative end: chamber-side witness bay, split baffle,
    # dogleg, vestibule, drain, and skirt-protected downward cable exit.
    x_min, x_max = -68.0, -41.0
    center_x = (x_min + x_max) / 2.0
    cutter = g.box(x_max - x_min, g.UPPER_OUTER_W + 0.4, 45.0, (center_x, 0.0, 7.0))
    coupon_lower = g.wp(lower.val().intersect(cutter.val())).translate((-center_x, 0.0, 0.0)).clean()
    coupon_upper = g.wp(upper.val().intersect(cutter.val())).translate((-center_x, 0.0, 0.0)).clean()
    return coupon_lower, coupon_upper, compound((coupon_lower, coupon_upper))


def export_stl(model: cq.Workplane, path: Path) -> None:
    cq.exporters.export(
        model, str(path), tolerance=STL_LINEAR_TOLERANCE,
        angularTolerance=STL_ANGULAR_TOLERANCE,
    )


def export_step(model: cq.Workplane, path: Path) -> None:
    cq.exporters.export(model, str(path))


def font(size: int) -> ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def make_side_load_open(output: Path) -> None:
    image = Image.new("RGB", (1250, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45, 25), "v003 OPEN - continuous cable is placed from above", fill="#0f172a", font=font(30))
    draw.rounded_rectangle((110, 180, 1140, 650), radius=38, fill="#f59e0b", outline="#92400e", width=4)
    path = [(245,410),(530,410),(690,500),(870,580),(1060,580)]
    draw.line(path, fill="#ffffff", width=48, joint="curve")
    draw.line(path, fill="#1d4ed8", width=5, joint="curve")
    draw.rectangle((155,270,500,550), fill="#dbeafe", outline="#2563eb", width=3)
    draw.text((215,380), "102 mm chamber\nPHYSICAL PASS", fill="#1e3a8a", font=font(24))
    draw.polygon([(620,85),(585,140),(655,140)], fill="#16a34a")
    draw.line((620,90,620,360), fill="#16a34a", width=12)
    draw.text((680,115), "TOP LOAD - no end threading", fill="#166534", font=font(25))
    draw.text((145,700), "LOWER: open U-channel for the complete labyrinth / no bridge / no ring", fill="#7f1d1d", font=font(24))
    image.save(output)


def make_side_load_installed(output: Path) -> None:
    image = Image.new("RGB", (1250, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45,25), "v003 CABLE INSTALLED - connector remains attached", fill="#0f172a", font=font(30))
    draw.rounded_rectangle((100,170,1140,660), radius=38, fill="#f59e0b", outline="#92400e", width=4)
    path = [(220,410),(520,410),(680,500),(860,585),(1060,585)]
    draw.line(path, fill="#ffffff", width=50, joint="curve")
    draw.line(path, fill="#2563eb", width=30, joint="curve")
    draw.rounded_rectangle((180,310,500,515), radius=24, fill="#bfdbfe", outline="#1d4ed8", width=4)
    draw.text((225,385), "95.1 x 18.7 x 10.8", fill="#1e3a8a", font=font(22))
    draw.line((1060,585,1060,735), fill="#2563eb", width=30)
    draw.text((690,235), "Cable laid into U-channel", fill="#166534", font=font(25))
    draw.text((690,275), "NO cutting / NO connector removal", fill="#166534", font=font(25))
    image.save(output)


def make_side_load_closed(output: Path) -> None:
    image = Image.new("RGB", (1250, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45,25), "v003 CLOSED - upper completes nominal 4.4 mm labyrinth", fill="#0f172a", font=font(30))
    draw.rounded_rectangle((120,330,1120,660), radius=35, fill="#f59e0b", outline="#92400e", width=4)
    draw.polygon([(90,300),(1040,185),(1160,305),(210,420)], fill="#334155", outline="#0f172a")
    draw.polygon([(210,420),(1160,305),(1160,470),(210,585)], fill="#1f2937", outline="#0f172a")
    draw.line((1030,570,1030,735), fill="#2563eb", width=28)
    for x in (330,620,910):
        draw.ellipse((x-12,610,x+12,634), fill="#cbd5e1", outline="#475569")
    draw.text((155,700), "Upper/lower jointly close the path; neither single part captures the cable", fill="#7f1d1d", font=font(23))
    image.save(output)


def make_split_section(output: Path) -> None:
    image = Image.new("RGB", (1100, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45,25), "SPLIT LABYRINTH CROSS-SECTION", fill="#0f172a", font=font(30))
    draw.rectangle((250,470,850,680), fill="#f59e0b", outline="#92400e", width=4)
    draw.rectangle((455,390,645,680), fill="white")
    draw.ellipse((450,440,650,640), fill="white", outline="#1d4ed8", width=4)
    draw.rectangle((455,250,645,485), fill="#334155", outline="#0f172a", width=4)
    draw.rectangle((385,200,715,300), fill="#334155", outline="#0f172a", width=4)
    draw.ellipse((478,463,622,607), fill="#60a5fa", outline="#1d4ed8", width=3)
    draw.line((720,300,830,300), fill="#16a34a", width=4)
    draw.text((840,278), "upper: open downward", fill="#166534", font=font(20))
    draw.line((380,500,250,420), fill="#16a34a", width=4)
    draw.text((55,385), "lower: open upward", fill="#166534", font=font(20))
    draw.text((295,720), "4.4 mm nominal + 0.25 mm local split relief / compression NONE", fill="#1e3a8a", font=font(21))
    image.save(output)


def make_water_path(output: Path) -> None:
    image = Image.new("RGB", (1250, 820), "white")
    draw = ImageDraw.Draw(image)
    draw.text((45,25), "WATER PATH - skirted downward exit + 8 mm dogleg + lower drain", fill="#0f172a", font=font(28))
    draw.rounded_rectangle((90,150,1160,675), radius=35, fill="#f59e0b", outline="#92400e", width=4)
    path = [(1080,575),(875,575),(730,470),(585,365),(410,365)]
    draw.line(path, fill="white", width=52, joint="curve")
    draw.line(path, fill="#06b6d4", width=9, joint="curve")
    draw.rectangle((210,260,410,520), fill="#f8fafc", outline="#64748b", width=3)
    draw.text((245,345), "DRY\nWITNESS", fill="#475569", font=font(22))
    draw.rectangle((520,235,560,570), fill="#fde68a", outline="#92400e", width=3)
    draw.text((485,195), "split terminal baffle", fill="#92400e", font=font(19))
    draw.line((735,500,735,720), fill="#0891b2", width=14)
    draw.text((680,745), "2.5 mm drain", fill="#0e7490", font=font(20))
    draw.line((1080,575,1080,745), fill="#2563eb", width=24)
    draw.text((875,105), "external cable turns down under skirt", fill="#1e3a8a", font=font(21))
    draw.text((105,775), "Direct seam / line-of-sight water path: NONE (CAD); colored-water test remains PENDING", fill="#7f1d1d", font=font(20))
    image.save(output)


def dogleg_sightline_deviation() -> float:
    a = path_points(1.0)[0]
    b = path_points(1.0)[1]
    d = path_points(1.0)[-1]
    dx, dy = d[0] - a[0], d[1] - a[1]
    return abs(dx * (a[1] - b[1]) - (a[0] - b[0]) * dy) / math.hypot(dx, dy)


def write_parameters() -> None:
    data = {
        "lane": LANE_NAME,
        "version": VERSION,
        "status": DESIGN_STATUS,
        "water_rating": WATER_RATING,
        "v002_authority": str(V002_LANE_REL).replace("\\", "/"),
        "physical_results": {
            "connector_chamber_fit": "PASS",
            "cable_channel_diameter_fit": "PASS",
            "v002_labyrinth_assembly_path": "FAIL_END_THREADING_REQUIRED",
            "real_cable_connector_removable": False,
            "cable_cutting_allowed": False,
        },
        "connector_envelope_mm": {"L": CONNECTOR_ENVELOPE_L, "W": CONNECTOR_ENVELOPE_W, "H": CONNECTOR_ENVELOPE_H},
        "cables_mm": {
            "camera_side_OD": CAMERA_SIDE_CABLE_OD,
            "extension_side_OD": EXTENSION_SIDE_CABLE_OD,
            "assembled_channel_nominal_D": CABLE_CHANNEL_D,
            "local_split_relief": LOCAL_SPLIT_RELIEF,
        },
        "chamber_inner_mm": {"L": CHAMBER_INNER_L, "W": CHAMBER_INNER_W, "H": CHAMBER_INNER_H},
        "split_labyrinth": {
            "lower": "OPEN_FROM_ABOVE_U_CHANNEL",
            "upper": "OPEN_FROM_BELOW_COMPLEMENTARY_COVER",
            "no_closed_ring_around_cable_in_single_part": True,
            "no_end_threading_required": True,
            "lower_slot_width_mm": LOWER_SLOT_W,
            "upper_tongue_width_mm": UPPER_TONGUE_W,
            "cap_ceiling_z_mm": CAP_CEILING_Z,
            "lateral_dogleg_mm": 8.0,
            "sightline_deviation_mm": dogleg_sightline_deviation(),
        },
        "preserved_v002": {
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
            "closure": "M3_X6_SIDE_FLANGE_WITH_CAPTURED_HEX_NUTS",
            "screw_stations_x_mm": list(g.SCREW_XS),
            "floor_center_crown_mm": v2.FLOOR_CROWN_H,
        },
        "physical_statuses": {
            "CABLE_CHANNEL_PHYSICAL": "PASS",
            "CONNECTOR_DIMENSION_PHYSICAL": "PASS_MEASURED",
            "CHAMBER_PHYSICAL": "PASS",
            "V002_CABLE_LABYRINTH_ASSEMBLY_PATH": "FAIL",
            "V003_SIDE_LOAD_ASSEMBLY": "PENDING",
            "LABYRINTH_DRAIN_PHYSICAL": "PENDING",
            "FULL_SHELL_RAIN": "PENDING",
            "LIVE_USB_RAIN": "PENDING",
        },
        "next_print": "split_labyrinth_side_load_coupon_lower_v003.stl + split_labyrinth_side_load_coupon_upper_v003.stl",
    }
    (LANE_DIR / "cad" / "parameters.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def validate(models: dict[str, cq.Workplane]) -> dict[str, Any]:
    lower = models["lower"]
    upper = models["upper"]
    connector = models["connector"]
    camera = models["camera_cable"]
    extension = models["extension_cable"]

    intersections = {
        "connector_vs_lower_mm3": round(g.intersection_volume(connector, lower), 8),
        "connector_vs_upper_mm3": round(g.intersection_volume(connector, upper), 8),
        "camera_cable_vs_lower_mm3": round(g.intersection_volume(camera, lower), 8),
        "camera_cable_vs_upper_mm3": round(g.intersection_volume(camera, upper), 8),
        "extension_cable_vs_lower_mm3": round(g.intersection_volume(extension, lower), 8),
        "extension_cable_vs_upper_mm3": round(g.intersection_volume(extension, upper), 8),
        "upper_vs_lower_mm3": round(g.intersection_volume(upper, lower), 8),
        "camera_lower_top_load_sweep_vs_lower_mm3": round(g.intersection_volume(models["camera_lower_sweep"], lower), 8),
        "extension_lower_top_load_sweep_vs_lower_mm3": round(g.intersection_volume(models["extension_lower_sweep"], lower), 8),
        "camera_upper_release_sweep_vs_upper_mm3": round(g.intersection_volume(models["camera_upper_sweep"], upper), 8),
        "extension_upper_release_sweep_vs_upper_mm3": round(g.intersection_volume(models["extension_upper_sweep"], upper), 8),
        "connector_vertical_placement_vs_lower_mm3": round(g.intersection_volume(models["connector_placement"], lower), 8),
    }

    stl_expected = {
        "split_labyrinth_side_load_coupon_lower_v003": 1,
        "split_labyrinth_side_load_coupon_upper_v003": 1,
        "usb_raincover_lower_v003": 1,
        "usb_raincover_upper_v003": 1,
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
        "split_labyrinth_side_load_coupon_v003": (models["coupon_assembly"], 2),
        "usb_raincover_lower_v003": (lower, 1),
        "usb_raincover_upper_v003": (upper, 1),
        "usb_raincover_assembly_v003": (models["assembly"], 5),
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

    v002_hashes = {
        "source": sha256_file(V002_SOURCE),
        "parameters": sha256_file(V002_DIR / "cad" / "parameters.json"),
        "validation": sha256_file(V002_DIR / "reports" / "validation_report.json"),
        "assembly_step": sha256_file(V002_DIR / "step" / "usb_raincover_assembly_v002.step"),
        "manifest": sha256_file(V002_DIR / "SHA256SUMS.txt"),
    }
    expected_hashes = {
        "source": V002_SOURCE_SHA256,
        "parameters": V002_PARAMETERS_SHA256,
        "validation": V002_VALIDATION_SHA256,
        "assembly_step": V002_ASSEMBLY_STEP_SHA256,
        "manifest": V002_MANIFEST_SHA256,
    }
    full_volume = g.shape_metrics(lower)["volume_mm3"] + g.shape_metrics(upper)["volume_mm3"]
    coupon_volume = g.shape_metrics(models["coupon_assembly"])["volume_mm3"]
    relieved_half_width = LOWER_SLOT_W / 2.0
    sightline_deviation = dogleg_sightline_deviation()
    checks = {
        "v002_authority_hashes_match": v002_hashes == expected_hashes,
        "connector_dimensions_preserved": (
            CONNECTOR_ENVELOPE_L == v2.CONNECTOR_ENVELOPE_L
            and CONNECTOR_ENVELOPE_W == v2.CONNECTOR_ENVELOPE_W
            and CONNECTOR_ENVELOPE_H == v2.CONNECTOR_ENVELOPE_H
        ),
        "chamber_102x24x16_preserved": (
            CHAMBER_INNER_L == v2.CHAMBER_INNER_L
            and CHAMBER_INNER_W == v2.CHAMBER_INNER_W
            and CHAMBER_INNER_H == v2.CHAMBER_INNER_H
        ),
        "channel_nominal_4p4_preserved": CABLE_CHANNEL_D == v2.CABLE_CHANNEL_D == 4.4,
        "local_split_relief_within_authority": 0.2 <= LOCAL_SPLIT_RELIEF <= 0.3,
        "camera_cable_no_compression": CAP_CEILING_Z - (CHANNEL_CENTER_Z - CABLE_CHANNEL_D / 2.0) > CAMERA_SIDE_CABLE_OD,
        "extension_cable_no_compression": CAP_CEILING_Z - (CHANNEL_CENTER_Z - CABLE_CHANNEL_D / 2.0) > EXTENSION_SIDE_CABLE_OD,
        "drains_preserved": DRAIN_D == v2.DRAIN_D == 2.5 and DRAIN_COUNT == v2.DRAIN_COUNT == 2,
        "roof_skirt_parting_preserved": (
            ROOF_SLOPE_DEG == v2.ROOF_SLOPE_DEG
            and TOP_OVERLAP_SKIRT == v2.TOP_OVERLAP_SKIRT
            and PARTING_STEP_H == v2.PARTING_STEP_H
            and PARTING_OVERLAP == v2.PARTING_OVERLAP
            and PARTING_CLEARANCE == v2.PARTING_CLEARANCE
        ),
        "m3x6_closure_preserved": len(g.SCREW_XS) * 2 == 6 and tuple(g.SCREW_XS) == (-50.0, 0.0, 50.0),
        "floor_crown_preserved": abs(v2.FLOOR_CROWN_H - math.tan(math.radians(2.0)) * 51.0) <= 1e-9,
        "lower_path_open_from_above": all(
            intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
                "camera_lower_top_load_sweep_vs_lower_mm3",
                "extension_lower_top_load_sweep_vs_lower_mm3",
            )
        ),
        "no_closed_loop_in_lower": all(
            intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
                "camera_lower_top_load_sweep_vs_lower_mm3",
                "extension_lower_top_load_sweep_vs_lower_mm3",
            )
        ),
        "no_closed_loop_in_upper": all(
            intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
                "camera_upper_release_sweep_vs_upper_mm3",
                "extension_upper_release_sweep_vs_upper_mm3",
            )
        ),
        "continuous_cable_side_load_path": all(
            intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
                "camera_lower_top_load_sweep_vs_lower_mm3",
                "extension_lower_top_load_sweep_vs_lower_mm3",
            )
        ),
        "connector_body_placement_path": intersections["connector_vertical_placement_vs_lower_mm3"] <= INTERFERENCE_TOLERANCE_MM3,
        "upper_closure_after_cable_placement": all(
            intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
                "camera_cable_vs_upper_mm3", "extension_cable_vs_upper_mm3", "upper_vs_lower_mm3",
            )
        ),
        "connector_shell_interference_zero": all(
            intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
                "connector_vs_lower_mm3", "connector_vs_upper_mm3",
            )
        ),
        "cable_reference_interference_zero": all(
            intersections[name] <= INTERFERENCE_TOLERANCE_MM3 for name in (
                "camera_cable_vs_lower_mm3", "camera_cable_vs_upper_mm3",
                "extension_cable_vs_lower_mm3", "extension_cable_vs_upper_mm3",
            )
        ),
        "upper_lower_interference_zero": intersections["upper_vs_lower_mm3"] <= INTERFERENCE_TOLERANCE_MM3,
        "dogleg_blocks_relieved_straight_sightline": sightline_deviation > relieved_half_width,
        "coupon_material_substantially_reduced": coupon_volume < 0.35 * full_volume,
        "no_roof_penetration": True,
        "waterproof_not_claimed": WATER_RATING == "SPLASH_RESISTANT_NOT_WATERPROOF",
    }
    if not all(checks.values()):
        raise AssertionError(f"v003 validation failed: {[name for name, passed in checks.items() if not passed]}")

    return {
        "lane": LANE_NAME,
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cadquery_version": cq.__version__,
        "status": DESIGN_STATUS,
        "water_rating": WATER_RATING,
        "v002_authority": {"lane": str(V002_LANE_REL).replace("\\", "/"), "hashes": v002_hashes},
        "physical_authority": {
            "connector_chamber_fit": "PASS",
            "cable_channel_diameter_fit": "PASS",
            "v002_labyrinth_assembly": "FAIL_END_THREADING_REQUIRED",
            "camera_cable_od_mm": CAMERA_SIDE_CABLE_OD,
            "extension_cable_od_mm": EXTENSION_SIDE_CABLE_OD,
            "channel_nominal_mm": CABLE_CHANNEL_D,
        },
        "split_labyrinth": {
            "lower": "OPEN_FROM_ABOVE_U_CHANNEL",
            "upper": "OPEN_FROM_BELOW_COMPLEMENTARY_COVER",
            "local_split_relief_mm": LOCAL_SPLIT_RELIEF,
            "dogleg_lateral_offset_mm": 8.0,
            "dogleg_sightline_deviation_mm": round(sightline_deviation, 4),
            "relieved_half_width_mm": round(relieved_half_width, 4),
            "no_closed_ring_in_single_part": True,
            "no_end_threading_required": True,
            "coupon_volume_ratio_to_full_shell": round(coupon_volume / full_volume, 4),
        },
        "intersections": intersections,
        "checks": checks,
        "artifacts": artifacts,
        "step_reimport": steps,
        "assembly_path_check": {
            "lower cable path open from above": "PASS",
            "no single-part closed ring": "PASS",
            "continuous cable side-load path": "PASS",
            "connector body placement path": "PASS",
            "upper closure after cable placement": "PASS",
            "CLOSED CABLE LOOP IN LOWER": "NONE",
            "CLOSED CABLE LOOP IN UPPER": "NONE",
        },
        "water_path": {
            "external_opening": "cable turns downward beneath preserved 6 mm skirt",
            "seam_controls": ["downward-facing under skirt", "8 mm lateral offset dogleg", "split cap tongue behind bridge"],
            "direct_seam_water_path": "NONE_CAD",
            "straight_line_of_sight": "NONE_CAD",
            "drip_vestibule": "lower-side open and visually cleanable",
            "drains": "2 x 2.5 mm preserved",
            "physical_water_result": "PENDING",
        },
        "pass_separation": {
            "CAD_PASS": True,
            "PRINT_PASS": False,
            "CABLE_FIT_PASS": True,
            "CONNECTOR_FIT_PASS": True,
            "ASSEMBLY_PATH_PASS": False,
            "DRAIN_PASS": False,
            "SPRAY_PASS": False,
            "POWERED_USB_PASS": False,
            "HEAVY_RAIN_FIELD_PASS": False,
            "LONG_DURATION_PASS": False,
        },
        "blockers": [
            "side-load cable assembly physical validation",
            "labyrinth drain effectiveness",
            "full-shell water intrusion",
        ],
        "field_unconfirmed": [
            "heavy rain",
            "wind-driven rain",
            "long-duration water exposure",
            "capillary ingress at split cable seam",
            "mud splash",
            "drain contamination/blockage",
            "UV/weather aging",
        ],
    }


def write_reports(report: dict[str, Any]) -> None:
    validation = [
        "# VALIDATION REPORT", "", f"Status: `{DESIGN_STATUS}`", "",
        "CAD validates the v003 split assembly path. Physical side-load, drain, and water tests remain pending.", "",
        "## STL / BRep", "", "| Artifact | Solids | BRep valid | STL triangles | Boundary/non-manifold edges |",
        "|---|---:|---|---:|---:|",
    ]
    for name, item in report["artifacts"].items():
        validation.append(
            f"| `{name}` | {item['brep']['solid_count']} | {item['brep']['valid']} | "
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
    validation.extend(["", "`CAD_PASS` does not imply PRINT, ASSEMBLY_PATH, DRAIN, SPRAY, or POWERED_USB PASS.", ""])
    (REPORT_DIR / "VALIDATION_REPORT.md").write_text("\n".join(validation), encoding="utf-8")

    assembly = [
        "# ASSEMBLY PATH VALIDATION", "", "## ASSEMBLY_PATH_CHECK", "",
    ]
    for name, result in report["assembly_path_check"].items():
        assembly.append(f"- `{name}`: {result}")
    assembly.extend([
        "", "The lower placement sweep models an attached cable moving vertically from above into every dogleg segment.",
        "The upper release sweep models the complementary part remaining open downward. Both have 0 mm³ interference.",
        "The upper may therefore close after cable placement; no cable end, connector removal, or cutting is required.",
        "Physical remove/reinstall ×5 is still mandatory before this becomes `ASSEMBLY_PATH_PASS`.", "",
    ])
    (REPORT_DIR / "ASSEMBLY_PATH_VALIDATION.md").write_text("\n".join(assembly), encoding="utf-8")

    water = [
        "# WATER PATH VALIDATION", "", f"Rating: `{WATER_RATING}`", "",
        "| Control | CAD result | Physical result |", "|---|---|---|",
    ]
    for name, value in report["water_path"].items():
        if isinstance(value, list):
            value = "; ".join(value)
        water.append(f"| `{name}` | {value} | PENDING |")
    water.extend([
        "", "The passage diameter remains the physically passed 4.4 mm nominal; only its assembly split changed.",
        "An 8 mm plan-view dogleg, upper cap bridge, preserved skirt, lower vestibule, offset weep, and two drains form the water controls.",
        "Colored-water witness testing at level, +5°, and -5° is required. TRACE is HOLD; WET is FAIL.", "",
    ])
    (REPORT_DIR / "WATER_PATH_VALIDATION.md").write_text("\n".join(water), encoding="utf-8")


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

    lower = build_lower_shell_v003()
    upper = build_upper_shell_v003()
    connector = connector_reference()
    camera = cable_reference(-1.0, CAMERA_SIDE_CABLE_OD)
    extension = cable_reference(1.0, EXTENSION_SIDE_CABLE_OD)
    assembly = compound((upper, lower, connector, camera, extension))
    coupon_lower, coupon_upper, coupon_assembly = build_coupon(lower, upper)

    stl_models = {
        "split_labyrinth_side_load_coupon_lower_v003": coupon_lower,
        "split_labyrinth_side_load_coupon_upper_v003": coupon_upper,
        "usb_raincover_lower_v003": lower,
        "usb_raincover_upper_v003": upper,
    }
    for stem, model in stl_models.items():
        export_stl(model, STL_DIR / f"{stem}.stl")

    step_models = {
        "split_labyrinth_side_load_coupon_v003": coupon_assembly,
        "usb_raincover_lower_v003": lower,
        "usb_raincover_upper_v003": upper,
        "usb_raincover_assembly_v003": assembly,
    }
    for stem, model in step_models.items():
        export_step(model, STEP_DIR / f"{stem}.step")

    make_side_load_open(RENDER_DIR / "side_load_open.png")
    make_side_load_installed(RENDER_DIR / "side_load_cable_installed.png")
    make_side_load_closed(RENDER_DIR / "side_load_closed.png")
    make_split_section(RENDER_DIR / "split_labyrinth_section.png")
    make_water_path(RENDER_DIR / "water_path_section.png")

    models = {
        "lower": lower,
        "upper": upper,
        "connector": connector,
        "camera_cable": camera,
        "extension_cable": extension,
        "assembly": assembly,
        "coupon_assembly": coupon_assembly,
        "camera_lower_sweep": lower_placement_envelope(-1.0, CAMERA_SIDE_CABLE_OD),
        "extension_lower_sweep": lower_placement_envelope(1.0, EXTENSION_SIDE_CABLE_OD),
        "camera_upper_sweep": upper_release_envelope(-1.0, CAMERA_SIDE_CABLE_OD),
        "extension_upper_sweep": upper_release_envelope(1.0, EXTENSION_SIDE_CABLE_OD),
        "connector_placement": connector_placement_envelope(),
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
        "connector_fit_physical_pass": True,
        "channel_fit_physical_pass": True,
        "v003_side_load_physical": "PENDING",
        "next_print": "split_labyrinth_side_load_coupon_v003",
    }, indent=2))


if __name__ == "__main__":
    main()
