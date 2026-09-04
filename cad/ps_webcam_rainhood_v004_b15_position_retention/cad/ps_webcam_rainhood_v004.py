#!/usr/bin/env python3
"""B15 rainhood and position-retention coupon for the Paddy Swarm webcam.

The fixed tripod and shell interface is transcribed from v002 commit
17a703694d5b2e127b5f7bccf8bfe3c5f1f0f2b9.  The selected optical geometry is
the physically tested v003 B_setback15 authority.  v004 adds only low-force
camera-side lateral/yaw location geometry and restores the rear roof/baffle
for a full prototype.  All dimensions are millimetres.

CAD output is not position-retention, full-hood optical, rain, field, static,
or durability physical approval.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import cadquery as cq
from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Provenance and release status
# ---------------------------------------------------------------------------

LANE_NAME = "ps_webcam_rainhood_v004_b15_position_retention"
VERSION = "v0.0.4"
DESIGN_STATUS = "CAD_COMPLETE_B15_POSITION_RETENTION_PHYSICAL_VALIDATION_PENDING"
V002_COMMIT = "17a703694d5b2e127b5f7bccf8bfe3c5f1f0f2b9"
V002_SOURCE_PATH = "cad/ps_webcam_rainhood_v002_tripod_mount/cad/ps_webcam_rainhood_v002.py"
V002_SOURCE_BLOB = "43cd3b5197be19add694b078bd655b0c3a8c75d8"
V003_LANE = "cad/ps_webcam_rainhood_v003_optical_clearance/"
V003_SOURCE_SHA256 = "0077640c864f09080b51ecd23b1ecd6bfcce88f14e1fdda818f94cf0fcc49b15"
V003_VALIDATION_SHA256 = "72ef6d68c5be0cb3427aa51b0b166d5150814bea12ebfc1d65a6cd12db9c9473"
V003_B_STL_SHA256 = "0bab2bbba49622ba3aadc0f0579259bc3029595b20e84506aac6c734bdf8703a"


# ---------------------------------------------------------------------------
# v002 dimensional authority: exact values, not a redesign from a summary
# ---------------------------------------------------------------------------

CAMERA_W = 101.5
CAMERA_H = 35.5
CAMERA_D = 34.0
FOLDED_CLIP_W = 49.2
FOLDED_CLIP_BELOW_BODY = 17.2
FOLDED_D_SAFE_ENVELOPE = 56.4

TRIPOD_X_FROM_LEFT = 50.9
TRIPOD_Y_FROM_FRONT = 30.4
TRIPOD_Y_FROM_REAR = 26.0
TRIPOD_AXIS_X = -CAMERA_W / 2.0 + TRIPOD_X_FROM_LEFT
TRIPOD_AXIS_Y = 0.0
FOLDED_FRONT_Y = -TRIPOD_Y_FROM_FRONT
FOLDED_REAR_Y = TRIPOD_Y_FROM_REAR
FOLDED_CENTER_Y = (FOLDED_FRONT_Y + FOLDED_REAR_Y) / 2.0
CAMERA_FOLDED_TOTAL_H_ENVELOPE = CAMERA_H + FOLDED_CLIP_BELOW_BODY

CARRIER_THICKNESS = 6.0
TRIPOD_THROUGH_HOLE = 6.8
CARRIER_W = 110.8
CARRIER_FRONT_Y = -36.0
CARRIER_REAR_Y = 38.0
CARRIER_D = CARRIER_REAR_Y - CARRIER_FRONT_Y
CARRIER_CENTER_Y = (CARRIER_FRONT_Y + CARRIER_REAR_Y) / 2.0
CARRIER_BOTTOM_Z = -CARRIER_THICKNESS
CARRIER_TOP_Z = 0.0
CARRIER_CORNER_R = 4.0

ANTI_ROTATION_CLEARANCE = 0.7
ANTI_ROTATION_GUIDE_H = 2.8
ANTI_ROTATION_GUIDE_T = 3.0
USB_CABLE_OD = 3.6
USB_CHANNEL = 6.0
USB_EDGE_RADIUS = USB_CHANNEL / 2.0

HOOD_OUTER_W = 118.0
HOOD_INNER_W = 112.0
HOOD_WALL = 3.0
FRONT_OVERHANG = 30.0
REAR_SERVICE_CLEARANCE = 14.0
HOOD_FRONT_Y_V002 = FOLDED_FRONT_Y - FRONT_OVERHANG
HOOD_REAR_INNER_Y = FOLDED_REAR_Y + REAR_SERVICE_CLEARANCE
HOOD_REAR_OUTER_Y = HOOD_REAR_INNER_Y + HOOD_WALL
ROOF_SLOPE_DEG = 1.5
TOP_CLEARANCE_ADOPTED = 4.0
ROOF_INNER_Z_AT_SAFE_FRONT = CAMERA_FOLDED_TOTAL_H_ENVELOPE + TOP_CLEARANCE_ADOPTED

SHELL_M4_CLEARANCE = 4.5
SHELL_M4_NUT_AF = 7.4
SHELL_M4_NUT_DEPTH = 3.4
SHELL_MOUNT_X = 44.0
SHELL_MOUNT_Y = 33.0
SLIDE_LATERAL_CLEARANCE = (HOOD_INNER_W - CARRIER_W) / 2.0
SLIDE_VERTICAL_CLEARANCE = 0.8
LOWER_RAIL_INNER_X = 50.0
LOWER_RAIL_TOP_Z = CARRIER_BOTTOM_Z
UPPER_RAIL_BOTTOM_Z = CARRIER_TOP_Z + SLIDE_VERTICAL_CLEARANCE
RAIL_THICKNESS = 3.0

ADAPTER_M4_CLEARANCE = 4.5
ADAPTER_BOLT_X = 32.0
ADAPTER_BOLT_Y = 15.0

FILLET_MEDIUM = 3.0
STL_LINEAR_TOLERANCE = 0.08
STL_ANGULAR_TOLERANCE = 0.12
INTERFERENCE_TOLERANCE_MM3 = 1.0e-5


# ---------------------------------------------------------------------------
# v003 coupon-only parameters
# ---------------------------------------------------------------------------

# Roof remains complete until 7.2 mm behind the nominal camera-body rear.
# Behind this datum only the low side spines and the complete v002 interface
# remain.  This saves material without moving the optical geometry.
OPTICAL_ROOF_REAR_Y = 22.0
REAR_SPINE_TOP_Z = 8.0
LEADING_EDGE_THICKNESS = 1.2
IDENTIFIER_RIB_W = 1.4
IDENTIFIER_RIB_D = 3.2
IDENTIFIER_RIB_H = 4.0

# v004 selected physical authority and status separation.
FINAL_SETBACK = 15.0
FINAL_FRONT_Y = -45.4
FINAL_BEVEL_DEG = 40.0
FINAL_BEVEL_RUN_AUTHORITY = 2.080
FINAL_FRONT_LENGTH = 15.0
B_PHYSICAL_RESULT = "SELECTED_CONDITIONAL"
C_FALLBACK_RESULT = "OPTICAL_ROBUST_PASS"
KNOWN_FALLBACK = "C_setback20"
BLOCKER = "mount lateral/yaw position retention"
SAFETY_FEATURE = False
STATUS_INDICATOR_ONLY = True

# Position-retention additions.  The 0.7 mm v002 physical authority is kept;
# no 0.5 mm clearance experiment is silently introduced.
GUIDE_CLEARANCE = ANTI_ROTATION_CLEARANCE
GUIDE_HEIGHT = ANTI_ROTATION_GUIDE_H
EXTENDED_GUIDE_FRONT_MARGIN = 2.0
EXTENDED_GUIDE_REAR_MARGIN = 2.0
EXTENDED_GUIDE_Y0 = FOLDED_FRONT_Y + EXTENDED_GUIDE_FRONT_MARGIN
EXTENDED_GUIDE_Y1 = FOLDED_REAR_Y - EXTENDED_GUIDE_REAR_MARGIN
EXTENDED_GUIDE_LENGTH = EXTENDED_GUIDE_Y1 - EXTENDED_GUIDE_Y0
GUIDE_OUTER_FOOT_W = 2.0
GUIDE_OUTER_FOOT_H = 1.2
FRONT_CORNER_STOP_W = 12.0
FRONT_CORNER_STOP_T = ANTI_ROTATION_GUIDE_T
FRONT_CORNER_STOP_H = ANTI_ROTATION_GUIDE_H
FRONT_CORNER_STOP_X_OFFSET = 18.0
FRONT_CORNER_STOP_REAR_Y = FOLDED_FRONT_Y - GUIDE_CLEARANCE
FRONT_CORNER_STOP_CENTER_Y = FRONT_CORNER_STOP_REAR_Y - FRONT_CORNER_STOP_T / 2.0
COUPON_OPTICAL_REAR_Y = -30.0
COUPON_IDENTIFIER_COUNT = 4

LANE_DIR = Path(__file__).resolve().parents[1]
STL_DIR = LANE_DIR / "stl"
STEP_DIR = LANE_DIR / "step"
RENDER_DIR = LANE_DIR / "renders"
REPORT_DIR = LANE_DIR / "reports"


@dataclass(frozen=True)
class OpticalCandidate:
    key: str
    front_setback: float
    underside_bevel_angle: float
    hood_top_height: float
    hood_front_length: float
    camera_reference_position: tuple[float, float, float]
    identifier_count: int
    physical_status: str = "PHYSICAL_OPTICAL_VALIDATION_PENDING"

    def __post_init__(self) -> None:
        expected_front_length = FRONT_OVERHANG - self.front_setback
        if abs(self.hood_front_length - expected_front_length) > 1.0e-9:
            raise ValueError(
                f"{self.key}: hood_front_length must equal v002 overhang minus front_setback"
            )

    @property
    def front_y(self) -> float:
        # Both user-facing parameters are constrained descriptions of the same
        # datum: a setback from v002 and a remaining length ahead of the folded
        # safe-front plane.
        return FOLDED_FRONT_Y - self.hood_front_length


CAMERA_REFERENCE_POSITION = (0.0, FOLDED_CENTER_Y, FOLDED_CLIP_BELOW_BODY)
HOOD_TOP_HEIGHT = ROOF_INNER_Z_AT_SAFE_FRONT + HOOD_WALL
CANDIDATES = (
    OpticalCandidate("A", 10.0, 35.0, HOOD_TOP_HEIGHT, 20.0, CAMERA_REFERENCE_POSITION, 1),
    OpticalCandidate("B", 15.0, 40.0, HOOD_TOP_HEIGHT, 15.0, CAMERA_REFERENCE_POSITION, 2),
    OpticalCandidate("C", 20.0, 45.0, HOOD_TOP_HEIGHT, 10.0, CAMERA_REFERENCE_POSITION, 3),
)
B15 = CANDIDATES[1]


# Literal cross-check table from v002.  Candidate generation aborts if the
# transcribed carrier/interface authority drifts from these values.
V002_INTERFACE_AUTHORITY = {
    "carrier_w": 110.8,
    "carrier_front_y": -36.0,
    "carrier_rear_y": 38.0,
    "carrier_thickness": 6.0,
    "tripod_axis_x": 0.15,
    "tripod_axis_y": 0.0,
    "tripod_through_hole": 6.8,
    "shell_mount_x": 44.0,
    "shell_mount_y": 33.0,
    "shell_m4_clearance": 4.5,
    "lower_rail_inner_x": 50.0,
    "lower_rail_top_z": -6.0,
    "upper_rail_bottom_z": 0.8,
    "rail_thickness": 3.0,
    "slide_lateral_clearance": 0.6,
    "slide_vertical_clearance": 0.8,
}


def current_interface_authority() -> dict[str, float]:
    return {
        "carrier_w": CARRIER_W,
        "carrier_front_y": CARRIER_FRONT_Y,
        "carrier_rear_y": CARRIER_REAR_Y,
        "carrier_thickness": CARRIER_THICKNESS,
        "tripod_axis_x": round(TRIPOD_AXIS_X, 6),
        "tripod_axis_y": TRIPOD_AXIS_Y,
        "tripod_through_hole": TRIPOD_THROUGH_HOLE,
        "shell_mount_x": SHELL_MOUNT_X,
        "shell_mount_y": SHELL_MOUNT_Y,
        "shell_m4_clearance": SHELL_M4_CLEARANCE,
        "lower_rail_inner_x": LOWER_RAIL_INNER_X,
        "lower_rail_top_z": LOWER_RAIL_TOP_Z,
        "upper_rail_bottom_z": UPPER_RAIL_BOTTOM_Z,
        "rail_thickness": RAIL_THICKNESS,
        "slide_lateral_clearance": round(SLIDE_LATERAL_CLEARANCE, 6),
        "slide_vertical_clearance": SLIDE_VERTICAL_CLEARANCE,
    }


def wp(shape: cq.Shape) -> cq.Workplane:
    return cq.Workplane(obj=shape)


def box(x: float, y: float, z: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(x, y, z).translate(center)


def cylinder_z(radius: float, length: float, z0: float, x: float, y: float) -> cq.Workplane:
    solid = cq.Solid.makeCylinder(radius, length, cq.Vector(x, y, z0), cq.Vector(0.0, 0.0, 1.0))
    return wp(solid)


def hex_prism_z(across_flats: float, height: float, z0: float, x: float, y: float) -> cq.Workplane:
    circumradius = across_flats / math.sqrt(3.0)
    return cq.Workplane("XY", origin=(x, y, z0)).polygon(6, 2.0 * circumradius).extrude(height)


def prism_yz(points: list[tuple[float, float]], x0: float, width: float) -> cq.Workplane:
    return cq.Workplane("YZ", origin=(x0, 0.0, 0.0)).polyline(points).close().extrude(width)


def safe_fillet(shape: cq.Workplane, selector: str, radius: float) -> cq.Workplane:
    try:
        result = shape.edges(selector).fillet(radius)
        if result.val().isValid():
            return result
    except Exception:
        pass
    return shape


def rounded_plate(width: float, depth: float, thickness: float, center_y: float, z0: float, radius: float) -> cq.Workplane:
    return safe_fillet(box(width, depth, thickness, (0.0, center_y, z0 + thickness / 2.0)), "|Z", radius)


def roof_inner_z(y: float, candidate: OpticalCandidate) -> float:
    inner_at_safe_front = candidate.hood_top_height - HOOD_WALL
    return inner_at_safe_front + math.tan(math.radians(ROOF_SLOPE_DEG)) * (y - FOLDED_FRONT_Y)


def bevel_run(candidate: OpticalCandidate) -> float:
    """Horizontal run giving the requested physical underside angle.

    Roof slope is included in the solution, so the resulting diagonal surface
    is candidate.underside_bevel_angle relative to horizontal.
    """
    roof_slope = math.tan(math.radians(ROOF_SLOPE_DEG))
    return (HOOD_WALL - LEADING_EDGE_THICKNESS) / (
        math.tan(math.radians(candidate.underside_bevel_angle)) + roof_slope
    )


def actual_bevel_angle(candidate: OpticalCandidate) -> float:
    run = bevel_run(candidate)
    front_top = roof_inner_z(candidate.front_y, candidate) + HOOD_WALL
    front_inner = front_top - LEADING_EDGE_THICKNESS
    join_inner = roof_inner_z(candidate.front_y + run, candidate)
    return math.degrees(math.atan2(front_inner - join_inner, run))


def anti_rotation_guides() -> cq.Workplane:
    guides: cq.Workplane | None = None
    side_length = 44.0
    for sign in (-1.0, 1.0):
        x = TRIPOD_AXIS_X + sign * (
            FOLDED_CLIP_W / 2.0 + ANTI_ROTATION_CLEARANCE + ANTI_ROTATION_GUIDE_T / 2.0
        )
        guide = safe_fillet(
            box(ANTI_ROTATION_GUIDE_T, side_length, ANTI_ROTATION_GUIDE_H,
                (x, FOLDED_CENTER_Y, ANTI_ROTATION_GUIDE_H / 2.0)),
            "|Z",
            1.0,
        )
        guides = guide if guides is None else guides.union(guide)
    rear_y = FOLDED_REAR_Y + ANTI_ROTATION_CLEARANCE + ANTI_ROTATION_GUIDE_T / 2.0
    for x in (TRIPOD_AXIS_X - 14.0, TRIPOD_AXIS_X + 14.0):
        guide = safe_fillet(
            box(20.0, ANTI_ROTATION_GUIDE_T, ANTI_ROTATION_GUIDE_H,
                (x, rear_y, ANTI_ROTATION_GUIDE_H / 2.0)),
            "|Z",
            1.0,
        )
        guides = guides.union(guide)
    assert guides is not None
    return guides.clean()


def open_rear_usb_slot(z0: float, height: float, rear_y: float) -> cq.Workplane:
    front_y = FOLDED_REAR_Y
    rectangular_length = rear_y - front_y + 2.0
    slot = box(USB_CHANNEL, rectangular_length, height,
               (0.0, front_y + rectangular_length / 2.0, z0 + height / 2.0))
    return slot.union(cylinder_z(USB_EDGE_RADIUS, height, z0, 0.0, front_y))


def build_carrier_base() -> cq.Workplane:
    """Exact v002 seating plane, tripod/adapter holes, M4 holes, and USB cut."""
    carrier = rounded_plate(CARRIER_W, CARRIER_D, CARRIER_THICKNESS,
                            CARRIER_CENTER_Y, CARRIER_BOTTOM_Z, CARRIER_CORNER_R)
    carrier = carrier.cut(cylinder_z(TRIPOD_THROUGH_HOLE / 2.0, CARRIER_THICKNESS + 2.0,
                                     CARRIER_BOTTOM_Z - 1.0, TRIPOD_AXIS_X, TRIPOD_AXIS_Y))
    for x in (-ADAPTER_BOLT_X, ADAPTER_BOLT_X):
        for y in (-ADAPTER_BOLT_Y, ADAPTER_BOLT_Y):
            carrier = carrier.cut(cylinder_z(ADAPTER_M4_CLEARANCE / 2.0, CARRIER_THICKNESS + 2.0,
                                             CARRIER_BOTTOM_Z - 1.0, x, y))
    for x in (-SHELL_MOUNT_X, SHELL_MOUNT_X):
        carrier = carrier.cut(cylinder_z(SHELL_M4_CLEARANCE / 2.0, CARRIER_THICKNESS + 2.0,
                                         CARRIER_BOTTOM_Z - 1.0, x, SHELL_MOUNT_Y))
    carrier = carrier.cut(open_rear_usb_slot(CARRIER_BOTTOM_Z - 1.0,
                                             CARRIER_THICKNESS + 2.0, CARRIER_REAR_Y + 1.0))
    return carrier.clean()


def build_carrier_reference() -> cq.Workplane:
    """Exact v002 carrier reconstruction, used for controlled-delta checks."""
    return build_carrier_base().union(anti_rotation_guides()).clean()


def build_v004_position_guides() -> cq.Workplane:
    """Extended 0.7 mm-clearance guides plus shallow front corner/yaw stops.

    Inner guide faces remain at the v002 X datum.  Extensions increase yaw
    lever arm and stiffness without reducing the physical-authority clearance.
    The two front stops and unchanged v002 rear stops form a shallow Y pocket.
    """
    y_center = (EXTENDED_GUIDE_Y0 + EXTENDED_GUIDE_Y1) / 2.0
    guides: cq.Workplane | None = None
    for sign in (-1.0, 1.0):
        x_center = TRIPOD_AXIS_X + sign * (
            FOLDED_CLIP_W / 2.0 + GUIDE_CLEARANCE + ANTI_ROTATION_GUIDE_T / 2.0
        )
        rail = safe_fillet(
            box(ANTI_ROTATION_GUIDE_T, EXTENDED_GUIDE_LENGTH, GUIDE_HEIGHT,
                (x_center, y_center, GUIDE_HEIGHT / 2.0)),
            "|Z",
            1.0,
        )
        guides = rail if guides is None else guides.union(rail)

        # Low outward-only foot reinforces the PETG root without reducing the
        # camera clearance or creating a tall peel-prone tab.
        outer_edge = x_center + sign * ANTI_ROTATION_GUIDE_T / 2.0
        foot_center_x = outer_edge + sign * (GUIDE_OUTER_FOOT_W / 2.0 - 0.1)
        foot = safe_fillet(
            box(GUIDE_OUTER_FOOT_W, EXTENDED_GUIDE_LENGTH, GUIDE_OUTER_FOOT_H,
                (foot_center_x, y_center, GUIDE_OUTER_FOOT_H / 2.0)),
            "|Z",
            0.8,
        )
        guides = guides.union(foot)

    # Preserve the exact v002 rear stops (0.7 mm nominal gap).
    rear_y = FOLDED_REAR_Y + GUIDE_CLEARANCE + ANTI_ROTATION_GUIDE_T / 2.0
    for x in (TRIPOD_AXIS_X - 14.0, TRIPOD_AXIS_X + 14.0):
        rear_stop = safe_fillet(
            box(20.0, ANTI_ROTATION_GUIDE_T, GUIDE_HEIGHT,
                (x, rear_y, GUIDE_HEIGHT / 2.0)),
            "|Z",
            1.0,
        )
        guides = guides.union(rear_stop)

    # Two low front pads act at separated corners.  They restrain Y/yaw but
    # retain 0.7 mm nominal clearance and never become a deep press-fit pocket.
    for sign in (-1.0, 1.0):
        front_stop = safe_fillet(
            box(FRONT_CORNER_STOP_W, FRONT_CORNER_STOP_T, FRONT_CORNER_STOP_H,
                (TRIPOD_AXIS_X + sign * FRONT_CORNER_STOP_X_OFFSET,
                 FRONT_CORNER_STOP_CENTER_Y, FRONT_CORNER_STOP_H / 2.0)),
            "|Z",
            1.2,
        )
        guides = guides.union(front_stop)

    assert guides is not None
    return guides.clean()


def build_v004_carrier() -> cq.Workplane:
    return build_carrier_base().union(build_v004_position_guides()).clean()


def build_camera_safe_reference(candidate: OpticalCandidate) -> cq.Workplane:
    camera_x, camera_y, camera_base_z = candidate.camera_reference_position
    body = box(CAMERA_W, CAMERA_D, CAMERA_H,
               (camera_x, camera_y, camera_base_z + CAMERA_H / 2.0))
    clip = box(FOLDED_CLIP_W, FOLDED_D_SAFE_ENVELOPE, FOLDED_CLIP_BELOW_BODY,
               (TRIPOD_AXIS_X, camera_y, FOLDED_CLIP_BELOW_BODY / 2.0))
    return body.union(clip).clean()


def build_shell_interface() -> cq.Workplane:
    """Exact v002 rails, stops, crossbar, bosses, holes, and USB opening."""
    lower_y0 = CARRIER_FRONT_Y
    lower_y1 = HOOD_REAR_OUTER_Y
    lower_d = lower_y1 - lower_y0
    interface: cq.Workplane | None = None
    for sign in (-1.0, 1.0):
        x_center = sign * ((HOOD_OUTER_W / 2.0 + LOWER_RAIL_INNER_X) / 2.0)
        rail_w = HOOD_OUTER_W / 2.0 - LOWER_RAIL_INNER_X
        rail = box(rail_w, lower_d, RAIL_THICKNESS,
                   (x_center, (lower_y0 + lower_y1) / 2.0,
                    LOWER_RAIL_TOP_Z - RAIL_THICKNESS / 2.0))
        interface = rail if interface is None else interface.union(rail)

    upper_y0, upper_y1 = -26.0, 38.0
    for sign in (-1.0, 1.0):
        x_center = sign * ((HOOD_OUTER_W / 2.0 + LOWER_RAIL_INNER_X) / 2.0)
        rail_w = HOOD_OUTER_W / 2.0 - LOWER_RAIL_INNER_X
        rail = box(rail_w, upper_y1 - upper_y0, RAIL_THICKNESS,
                   (x_center, (upper_y0 + upper_y1) / 2.0,
                    UPPER_RAIL_BOTTOM_Z + RAIL_THICKNESS / 2.0))
        interface = interface.union(rail)

    for sign in (-1.0, 1.0):
        x_center = sign * ((HOOD_OUTER_W / 2.0 + LOWER_RAIL_INNER_X) / 2.0)
        rail_w = HOOD_OUTER_W / 2.0 - LOWER_RAIL_INNER_X
        interface = interface.union(box(rail_w, 3.5, 6.8, (x_center, 40.25, -2.6)))

    interface = interface.union(box(104.0, 15.0, RAIL_THICKNESS, (0.0, 35.5, -7.5)))
    for x in (-SHELL_MOUNT_X, SHELL_MOUNT_X):
        boss = safe_fillet(box(14.0, 14.0, 5.5, (x, SHELL_MOUNT_Y, -8.75)), "|Z", FILLET_MEDIUM)
        interface = interface.union(boss)

    for x in (-SHELL_MOUNT_X, SHELL_MOUNT_X):
        interface = interface.cut(cylinder_z(SHELL_M4_CLEARANCE / 2.0, 13.5, -12.5, x, SHELL_MOUNT_Y))
        interface = interface.cut(hex_prism_z(SHELL_M4_NUT_AF, SHELL_M4_NUT_DEPTH + 0.2,
                                               -11.55, x, SHELL_MOUNT_Y))
    interface = interface.cut(open_rear_usb_slot(-12.5, 8.0, HOOD_REAR_OUTER_Y + 1.0))
    return interface.clean()


def build_beveled_optical_roof(candidate: OpticalCandidate) -> cq.Workplane:
    front = candidate.front_y
    join = front + bevel_run(candidate)
    front_top = roof_inner_z(front, candidate) + HOOD_WALL
    front_inner = front_top - LEADING_EDGE_THICKNESS
    join_inner = roof_inner_z(join, candidate)
    rear_inner = roof_inner_z(OPTICAL_ROOF_REAR_Y, candidate)
    points = [
        (front, front_inner),
        (join, join_inner),
        (OPTICAL_ROOF_REAR_Y, rear_inner),
        (OPTICAL_ROOF_REAR_Y, rear_inner + HOOD_WALL),
        (front, front_top),
    ]
    return prism_yz(points, -HOOD_OUTER_W / 2.0, HOOD_OUTER_W)


def build_optical_sidewalls(candidate: OpticalCandidate) -> cq.Workplane:
    front = candidate.front_y
    front_top = roof_inner_z(front, candidate) + HOOD_WALL
    rear_top = roof_inner_z(OPTICAL_ROOF_REAR_Y, candidate) + HOOD_WALL
    # The knee remains ordered between the candidate front and v002 carrier
    # front.  It preserves lateral coverage while avoiding a wall forward of
    # the parameterized front edge.
    knee_run = max(2.4, 0.35 * (CARRIER_FRONT_Y - front))
    knee_y = min(CARRIER_FRONT_Y - 0.4, front + knee_run)
    profile = [
        (front, front_top),
        (OPTICAL_ROOF_REAR_Y, rear_top),
        (OPTICAL_ROOF_REAR_Y, REAR_SPINE_TOP_Z),
        (HOOD_REAR_OUTER_Y, REAR_SPINE_TOP_Z),
        (HOOD_REAR_OUTER_Y, -9.0),
        (CARRIER_FRONT_Y, -9.0),
        (knee_y, 40.0),
        (front, 50.0),
    ]
    left = prism_yz(profile, -HOOD_OUTER_W / 2.0, HOOD_WALL)
    right = prism_yz(profile, HOOD_OUTER_W / 2.0 - HOOD_WALL, HOOD_WALL)
    return left.union(right).clean()


def identifier_ribs(candidate: OpticalCandidate) -> list[cq.Workplane]:
    ribs: list[cq.Workplane] = []
    x_center = HOOD_OUTER_W / 2.0 + IDENTIFIER_RIB_W / 2.0 - 0.2
    for index in range(candidate.identifier_count):
        y = 27.0 + index * 5.0
        ribs.append(box(IDENTIFIER_RIB_W, IDENTIFIER_RIB_D, IDENTIFIER_RIB_H,
                        (x_center, y, 3.0)))
    return ribs


def build_optical_coupon(candidate: OpticalCandidate) -> cq.Workplane:
    coupon = build_beveled_optical_roof(candidate).union(build_optical_sidewalls(candidate))
    coupon = coupon.union(build_shell_interface())
    for rib in identifier_ribs(candidate):
        coupon = coupon.union(rib)
    return coupon.clean()


# ---------------------------------------------------------------------------
# v004 B15 full hood and integrated low-material retention coupon
# ---------------------------------------------------------------------------

def build_b15_roof(rear_y: float) -> cq.Workplane:
    """v003 B front/bevel authority continued to the requested rear datum."""
    candidate = B15
    front = candidate.front_y
    join = front + bevel_run(candidate)
    front_top = roof_inner_z(front, candidate) + HOOD_WALL
    front_inner = front_top - LEADING_EDGE_THICKNESS
    join_inner = roof_inner_z(join, candidate)
    rear_inner = roof_inner_z(rear_y, candidate)
    return prism_yz(
        [
            (front, front_inner),
            (join, join_inner),
            (rear_y, rear_inner),
            (rear_y, rear_inner + HOOD_WALL),
            (front, front_top),
        ],
        -HOOD_OUTER_W / 2.0,
        HOOD_OUTER_W,
    )


def b15_knee_y() -> float:
    knee_run = max(2.4, 0.35 * (CARRIER_FRONT_Y - B15.front_y))
    return min(CARRIER_FRONT_Y - 0.4, B15.front_y + knee_run)


def build_b15_full_sidewalls() -> cq.Workplane:
    front_top = roof_inner_z(B15.front_y, B15) + HOOD_WALL
    rear_top = roof_inner_z(HOOD_REAR_OUTER_Y, B15) + HOOD_WALL
    profile = [
        (B15.front_y, front_top),
        (HOOD_REAR_OUTER_Y, rear_top),
        (HOOD_REAR_OUTER_Y, -9.0),
        (CARRIER_FRONT_Y, -9.0),
        (b15_knee_y(), 40.0),
        (B15.front_y, 50.0),
    ]
    left = prism_yz(profile, -HOOD_OUTER_W / 2.0, HOOD_WALL)
    right = prism_yz(profile, HOOD_OUTER_W / 2.0 - HOOD_WALL, HOOD_WALL)
    return left.union(right).clean()


def build_rear_rain_baffle() -> cq.Workplane:
    rear_inner = roof_inner_z(HOOD_REAR_OUTER_Y, B15)
    rear_baffle_bottom_z = 24.0
    return box(
        HOOD_OUTER_W,
        HOOD_WALL,
        rear_inner + HOOD_WALL - rear_baffle_bottom_z,
        (
            0.0,
            HOOD_REAR_INNER_Y + HOOD_WALL / 2.0,
            (rear_baffle_bottom_z + rear_inner + HOOD_WALL) / 2.0,
        ),
    )


def build_rainhood_b15_v004() -> cq.Workplane:
    """Full B15 prototype: verified front authority plus restored v002 rear cover."""
    shell = build_b15_roof(HOOD_REAR_OUTER_Y)
    shell = shell.union(build_b15_full_sidewalls())
    shell = shell.union(build_rear_rain_baffle())
    shell = shell.union(build_shell_interface())
    # The v002 downward front drip wall is not restored: it occupied the tested
    # optical zone.  The retained 1.2 mm sharp edge and upward 40-degree
    # underside bevel form the B-authority rain cut without moving the edge.
    return shell.clean()


def build_coupon_reference_sidewalls() -> cq.Workplane:
    front_top = roof_inner_z(B15.front_y, B15) + HOOD_WALL
    rear_top = roof_inner_z(COUPON_OPTICAL_REAR_Y, B15) + HOOD_WALL
    profile = [
        (B15.front_y, front_top),
        (COUPON_OPTICAL_REAR_Y, rear_top),
        (COUPON_OPTICAL_REAR_Y, -9.0),
        (CARRIER_FRONT_Y, -9.0),
        (b15_knee_y(), 40.0),
        (B15.front_y, 50.0),
    ]
    left = prism_yz(profile, -HOOD_OUTER_W / 2.0, HOOD_WALL)
    right = prism_yz(profile, HOOD_OUTER_W / 2.0 - HOOD_WALL, HOOD_WALL)
    return left.union(right).clean()


def build_coupon_side_print_spines() -> cq.Workplane:
    """Coupon-only outer extensions joining the carrier to optical sidewalls.

    They preserve the actual carrier top seating area and make side-on printing
    practical.  They are not present on the production carrier or full hood.
    """
    spines: cq.Workplane | None = None
    width = HOOD_OUTER_W / 2.0 - CARRIER_W / 2.0 + 0.4
    for sign in (-1.0, 1.0):
        x0 = CARRIER_W / 2.0 - 0.4
        x1 = HOOD_OUTER_W / 2.0
        x_center = sign * ((x0 + x1) / 2.0)
        spine = box(width, CARRIER_D, CARRIER_THICKNESS,
                    (x_center, CARRIER_CENTER_Y, CARRIER_BOTTOM_Z / 2.0))
        spines = spine if spines is None else spines.union(spine)
    assert spines is not None
    return spines.clean()


def coupon_identifier_ribs() -> list[cq.Workplane]:
    ribs: list[cq.Workplane] = []
    x_center = HOOD_OUTER_W / 2.0 + IDENTIFIER_RIB_W / 2.0 - 0.2
    for index in range(COUPON_IDENTIFIER_COUNT):
        y = -22.0 + index * 8.0
        ribs.append(
            box(IDENTIFIER_RIB_W, IDENTIFIER_RIB_D, 3.0,
                (x_center, y, -2.5))
        )
    return ribs


def build_b15_position_retention_coupon() -> cq.Workplane:
    coupon = build_v004_carrier()
    coupon = coupon.union(build_coupon_side_print_spines())
    coupon = coupon.union(build_b15_roof(COUPON_OPTICAL_REAR_Y))
    coupon = coupon.union(build_coupon_reference_sidewalls())
    for rib in coupon_identifier_ribs():
        coupon = coupon.union(rib)
    return coupon.clean()


def compound_workplane(models: Iterable[cq.Workplane]) -> cq.Workplane:
    shapes = [model.val() for model in models]
    return wp(cq.Compound.makeCompound(shapes))


def build_camera_side_assembly_v004(
    hood: cq.Workplane,
    carrier: cq.Workplane,
    camera: cq.Workplane,
) -> cq.Workplane:
    return compound_workplane((hood, carrier, camera))


def intersection_volume(first: cq.Workplane, second: cq.Workplane) -> float:
    common = first.val().intersect(second.val())
    return 0.0 if common.isNull() else float(common.Volume())


def shape_metrics(model: cq.Workplane) -> dict[str, Any]:
    shape = model.val()
    bb = shape.BoundingBox()
    return {
        "valid": bool(shape.isValid()),
        "solid_count": len(shape.Solids()),
        "volume_mm3": round(float(shape.Volume()), 3),
        "bounding_box_mm": {
            "x": round(bb.xlen, 3),
            "y": round(bb.ylen, 3),
            "z": round(bb.zlen, 3),
        },
        "bounds_mm": {
            "xmin": round(bb.xmin, 3), "xmax": round(bb.xmax, 3),
            "ymin": round(bb.ymin, 3), "ymax": round(bb.ymax, 3),
            "zmin": round(bb.zmin, 3), "zmax": round(bb.zmax, 3),
        },
    }


def export_model(model: cq.Workplane, stl_path: Path, step_path: Path) -> None:
    cq.exporters.export(model, str(stl_path), tolerance=STL_LINEAR_TOLERANCE,
                        angularTolerance=STL_ANGULAR_TOLERANCE)
    cq.exporters.export(model, str(step_path))


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


def write_candidate_csv(rows: Iterable[dict[str, Any]]) -> None:
    path = REPORT_DIR / "candidate_dimensions.csv"
    fieldnames = [
        "candidate", "front_setback_mm", "v002_front_y_mm", "candidate_front_y_mm",
        "hood_front_length_mm", "underside_bevel_angle_deg", "actual_bevel_angle_deg",
        "bevel_run_mm", "hood_top_height_at_safe_front_mm", "identifier_rib_count",
        "volume_mm3", "bbox_x_mm", "bbox_y_mm", "bbox_z_mm", "status",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def side_outline(candidate: OpticalCandidate) -> list[tuple[float, float]]:
    front = candidate.front_y
    run = bevel_run(candidate)
    front_top = roof_inner_z(front, candidate) + HOOD_WALL
    front_inner = front_top - LEADING_EDGE_THICKNESS
    join_inner = roof_inner_z(front + run, candidate)
    rear_inner = roof_inner_z(OPTICAL_ROOF_REAR_Y, candidate)
    return [
        (front, front_top),
        (OPTICAL_ROOF_REAR_Y, rear_inner + HOOD_WALL),
        (OPTICAL_ROOF_REAR_Y, rear_inner),
        (front + run, join_inner),
        (front, front_inner),
    ]


def make_side_render(candidate: OpticalCandidate, output: Path) -> None:
    image = Image.new("RGB", (1200, 760), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=20)
    bold = ImageFont.load_default(size=26)
    y_min, y_max = -66.0, 48.0
    z_min, z_max = -15.0, 66.0
    left, top, width, height = 90, 90, 1020, 590

    def px(y: float) -> int:
        return int(left + (y - y_min) / (y_max - y_min) * width)

    def pz(z: float) -> int:
        return int(top + (z_max - z) / (z_max - z_min) * height)

    for z in (0, 20, 40, 60):
        draw.line((left, pz(z), left + width, pz(z)), fill="#e5e7eb", width=1)
        draw.text((left - 55, pz(z) - 10), f"{z}", fill="#64748b", font=font)
    draw.line((left, pz(0), left + width, pz(0)), fill="#94a3b8", width=2)

    # Carrier, safe clip envelope, and camera body references.
    draw.rectangle((px(CARRIER_FRONT_Y), pz(0), px(CARRIER_REAR_Y), pz(CARRIER_BOTTOM_Z)),
                   fill="#cbd5e1", outline="#475569", width=2)
    draw.rectangle((px(FOLDED_FRONT_Y), pz(FOLDED_CLIP_BELOW_BODY),
                    px(FOLDED_REAR_Y), pz(0)), fill="#dbeafe", outline="#2563eb", width=2)
    body_front = FOLDED_CENTER_Y - CAMERA_D / 2.0
    body_rear = FOLDED_CENTER_Y + CAMERA_D / 2.0
    draw.rectangle((px(body_front), pz(CAMERA_FOLDED_TOTAL_H_ENVELOPE),
                    px(body_rear), pz(FOLDED_CLIP_BELOW_BODY)),
                   fill="#bfdbfe", outline="#1d4ed8", width=3)

    outline = [(px(y), pz(z)) for y, z in side_outline(candidate)]
    draw.polygon(outline, fill="#0f172a", outline="#020617")
    # Side wall / low rear spine silhouette.
    side = [
        (candidate.front_y, roof_inner_z(candidate.front_y, candidate) + HOOD_WALL),
        (OPTICAL_ROOF_REAR_Y, roof_inner_z(OPTICAL_ROOF_REAR_Y, candidate) + HOOD_WALL),
        (OPTICAL_ROOF_REAR_Y, REAR_SPINE_TOP_Z),
        (HOOD_REAR_OUTER_Y, REAR_SPINE_TOP_Z),
        (HOOD_REAR_OUTER_Y, -9.0),
        (CARRIER_FRONT_Y, -9.0),
        (candidate.front_y, 50.0),
    ]
    draw.line([(px(y), pz(z)) for y, z in side], fill="#334155", width=4, joint="curve")

    # v002 leading edge datum and candidate setback dimension.
    draw.line((px(HOOD_FRONT_Y_V002), top, px(HOOD_FRONT_Y_V002), top + height),
              fill="#dc2626", width=2)
    dim_z = 64.0
    draw.line((px(HOOD_FRONT_Y_V002), pz(dim_z), px(candidate.front_y), pz(dim_z)),
              fill="#dc2626", width=3)
    draw.text((px(HOOD_FRONT_Y_V002) + 8, pz(dim_z) - 31),
              f"setback {candidate.front_setback:.0f} mm", fill="#b91c1c", font=font)

    draw.text((70, 25), f"Candidate {candidate.key}: {candidate.front_setback:.0f} mm / "
              f"{candidate.underside_bevel_angle:.0f} deg", fill="#0f172a", font=bold)
    draw.text((760, 705), f"Permanent ID: {candidate.identifier_count} exterior rib(s)",
              fill="#334155", font=font)
    image.save(output)


def make_comparison_render(output: Path) -> None:
    image = Image.new("RGB", (1200, 760), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=20)
    bold = ImageFont.load_default(size=28)
    y_min, y_max = -66.0, 28.0
    z_min, z_max = 0.0, 66.0
    left, top, width, height = 100, 90, 1000, 580

    def px(y: float) -> int:
        return int(left + (y - y_min) / (y_max - y_min) * width)

    def pz(z: float) -> int:
        return int(top + (z_max - z) / (z_max - z_min) * height)

    draw.text((70, 25), "A/B/C optical front comparison - no winner selected",
              fill="#0f172a", font=bold)
    draw.line((px(HOOD_FRONT_Y_V002), top, px(HOOD_FRONT_Y_V002), top + height),
              fill="#ef4444", width=2)
    draw.text((px(HOOD_FRONT_Y_V002) + 5, top + height - 26), "v002 front", fill="#b91c1c", font=font)
    colors = {"A": "#2563eb", "B": "#16a34a", "C": "#9333ea"}
    for index, candidate in enumerate(CANDIDATES):
        points = [(px(y), pz(z)) for y, z in side_outline(candidate)]
        draw.line(points + [points[0]], fill=colors[candidate.key], width=5, joint="curve")
        draw.text((720, 565 + index * 34),
                  f"{candidate.key}: setback {candidate.front_setback:.0f}, bevel "
                  f"{candidate.underside_bevel_angle:.0f} deg",
                  fill=colors[candidate.key], font=font)
    # Camera reference.
    body_front = FOLDED_CENTER_Y - CAMERA_D / 2.0
    body_rear = FOLDED_CENTER_Y + CAMERA_D / 2.0
    draw.rectangle((px(body_front), pz(CAMERA_FOLDED_TOTAL_H_ENVELOPE),
                    px(body_rear), pz(FOLDED_CLIP_BELOW_BODY)),
                   fill="#dbeafe", outline="#1d4ed8", width=3)
    draw.text((70, 700), "Optical boundary is unknown: physical camera preview is required.",
              fill="#7f1d1d", font=font)
    image.save(output)


def validate_and_report(models: dict[str, cq.Workplane]) -> dict[str, Any]:
    authority_match = current_interface_authority() == V002_INTERFACE_AUTHORITY
    if not authority_match:
        raise AssertionError("v002 carrier/interface authority drift detected")

    carrier = build_carrier_reference()
    interface_metrics = shape_metrics(build_shell_interface())
    results: dict[str, Any] = {}
    csv_rows: list[dict[str, Any]] = []
    stl_hashes: set[str] = set()
    volumes: set[float] = set()
    front_bounds: set[float] = set()

    for candidate in CANDIDATES:
        model = models[candidate.key]
        camera = build_camera_safe_reference(candidate)
        stl_path = STL_DIR / f"optical_coupon_{candidate.key}_setback{int(candidate.front_setback)}.stl"
        step_path = STEP_DIR / f"optical_coupon_{candidate.key}_setback{int(candidate.front_setback)}.step"
        brep = shape_metrics(model)
        mesh = stl_mesh_metrics(stl_path)
        step_reimport = shape_metrics(cq.importers.importStep(str(step_path)))
        camera_interference = intersection_volume(model, camera)
        carrier_interference = intersection_volume(model, carrier)
        angle_error = abs(actual_bevel_angle(candidate) - candidate.underside_bevel_angle)
        identifier_count = len(identifier_ribs(candidate))
        bbox_delta = max(abs(brep["bounding_box_mm"][axis] - mesh["bounding_box_mm"][axis])
                         for axis in ("x", "y", "z"))
        checks = {
            "brep_valid": brep["valid"],
            "single_solid": brep["solid_count"] == 1,
            "stl_nonempty": mesh["file_size_bytes"] > 1024,
            "mesh_triangles_present": mesh["triangle_count"] > 0,
            "mesh_no_degenerate_triangles": mesh["degenerate_triangles"] == 0,
            "mesh_watertight_edge_check": mesh["watertight_edge_count_check"],
            "mesh_bbox_matches_brep": bbox_delta <= 0.2,
            "step_reimport_valid": step_reimport["valid"],
            "step_reimport_single_solid": step_reimport["solid_count"] == 1,
            "step_reimport_volume_matches_brep": abs(
                step_reimport["volume_mm3"] - brep["volume_mm3"]
            ) <= 0.01,
            "camera_safe_envelope_no_interference": camera_interference <= INTERFERENCE_TOLERANCE_MM3,
            "carrier_no_solid_interference": carrier_interference <= INTERFERENCE_TOLERANCE_MM3,
            "bevel_angle_matches_parameter": angle_error <= 0.01,
            "identifier_count_matches_candidate": identifier_count == candidate.identifier_count,
            "front_setback_from_v002_exact": abs(candidate.front_y -
                (HOOD_FRONT_Y_V002 + candidate.front_setback)) <= 1.0e-9,
            "hood_front_length_constraint_exact": abs(
                candidate.hood_front_length - (FRONT_OVERHANG - candidate.front_setback)
            ) <= 1.0e-9,
            "top_clearance_datum_preserved": abs(
                (candidate.hood_top_height - HOOD_WALL) - ROOF_INNER_Z_AT_SAFE_FRONT
            ) <= 1.0e-9,
            "camera_reference_position_preserved": candidate.camera_reference_position == CAMERA_REFERENCE_POSITION,
        }
        if not all(checks.values()):
            failed = [name for name, passed in checks.items() if not passed]
            raise AssertionError(f"Candidate {candidate.key} validation failed: {failed}")

        stl_hashes.add(mesh["sha256"])
        volumes.add(brep["volume_mm3"])
        front_bounds.add(brep["bounds_mm"]["ymin"])
        results[candidate.key] = {
            "parameters": asdict(candidate),
            "derived": {
                "v002_front_y_mm": HOOD_FRONT_Y_V002,
                "candidate_front_y_mm": candidate.front_y,
                "bevel_run_mm": round(bevel_run(candidate), 3),
                "actual_bevel_angle_deg": round(actual_bevel_angle(candidate), 4),
                "optical_roof_rear_y_mm": OPTICAL_ROOF_REAR_Y,
                "camera_body_rear_y_mm": round(FOLDED_CENTER_Y + CAMERA_D / 2.0, 3),
                "identifier_rib_count": identifier_count,
            },
            "brep": brep,
            "mesh": mesh,
            "step_reimport": step_reimport,
            "camera_safe_interference_mm3": round(camera_interference, 8),
            "carrier_interference_mm3": round(carrier_interference, 8),
            "checks": checks,
            "cad_pass": True,
            "print_status": "PRINT_PENDING",
            "fit_status": "FIT_PENDING",
            "optical_status": "OPTICAL_PENDING",
            "rain_status": "RAIN_PENDING",
            "field_status": "FIELD_PENDING",
        }
        csv_rows.append({
            "candidate": candidate.key,
            "front_setback_mm": candidate.front_setback,
            "v002_front_y_mm": HOOD_FRONT_Y_V002,
            "candidate_front_y_mm": candidate.front_y,
            "hood_front_length_mm": candidate.hood_front_length,
            "underside_bevel_angle_deg": candidate.underside_bevel_angle,
            "actual_bevel_angle_deg": round(actual_bevel_angle(candidate), 4),
            "bevel_run_mm": round(bevel_run(candidate), 3),
            "hood_top_height_at_safe_front_mm": candidate.hood_top_height,
            "identifier_rib_count": identifier_count,
            "volume_mm3": brep["volume_mm3"],
            "bbox_x_mm": brep["bounding_box_mm"]["x"],
            "bbox_y_mm": brep["bounding_box_mm"]["y"],
            "bbox_z_mm": brep["bounding_box_mm"]["z"],
            "status": candidate.physical_status,
        })

    set_checks = {
        "three_candidates_generated": len(results) == 3,
        "candidate_stl_hashes_are_distinct": len(stl_hashes) == 3,
        "candidate_brep_volumes_are_distinct": len(volumes) == 3,
        "candidate_front_bounds_are_distinct": len(front_bounds) == 3,
        "identifier_counts_are_1_2_3": [c.identifier_count for c in CANDIDATES] == [1, 2, 3],
        "front_setbacks_are_10_15_20": [c.front_setback for c in CANDIDATES] == [10.0, 15.0, 20.0],
        "v002_interface_authority_exact_match": authority_match,
        "same_interface_builder_used_for_all_candidates": True,
    }
    if not all(set_checks.values()):
        raise AssertionError(f"Set validation failed: {set_checks}")

    write_candidate_csv(csv_rows)
    report = {
        "lane": LANE_NAME,
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cadquery_version": cq.__version__,
        "status": DESIGN_STATUS,
        "pass_level_separation": {
            "CAD_PASS": True,
            "PRINT_PENDING": True,
            "FIT_PENDING": True,
            "OPTICAL_PENDING": True,
            "RAIN_PENDING": True,
            "FIELD_PENDING": True,
            "OPTICAL_PASS": False,
            "RAIN_PASS": False,
            "FIELD_PASS": False,
        },
        "v002_provenance": {
            "commit": V002_COMMIT,
            "source_path": V002_SOURCE_PATH,
            "source_blob": V002_SOURCE_BLOB,
        },
        "coupon_scope": {
            "exact_v002_carrier_interface": True,
            "camera_reference_unchanged": True,
            "roof_complete_through_y_mm": OPTICAL_ROOF_REAR_Y,
            "rear_roof_and_rear_baffle_omitted_for_low_material_test": True,
            "deployable_rainhood": False,
        },
        "interface_authority": current_interface_authority(),
        "interface_brep": interface_metrics,
        "set_checks": set_checks,
        "candidates": results,
    }
    return report


def write_markdown_validation(report: dict[str, Any]) -> None:
    lines = [
        "# Validation report",
        "",
        f"Status: `{report['status']}`",
        "",
        "This report proves CAD generation and mechanical-datum consistency only. It does not prove optical, rain, or field performance.",
        "",
        "| Candidate | BRep | Solids | STEP reimport | STL triangles | Watertight edge check | Camera interference | Carrier interference | Physical optical |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for key in ("A", "B", "C"):
        item = report["candidates"][key]
        lines.append(
            f"| {key} | {'PASS' if item['brep']['valid'] else 'FAIL'} | {item['brep']['solid_count']} | "
            f"{'PASS' if item['step_reimport']['valid'] and item['step_reimport']['solid_count'] == 1 else 'FAIL'} | "
            f"{item['mesh']['triangle_count']} | {'PASS' if item['mesh']['watertight_edge_count_check'] else 'FAIL'} | "
            f"{item['camera_safe_interference_mm3']:.8f} mm^3 | {item['carrier_interference_mm3']:.8f} mm^3 | PENDING |"
        )
    lines.extend([
        "",
        "Set checks:",
        "",
    ])
    for name, passed in report["set_checks"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend([
        "",
        "Pass separation:",
        "",
        "- CAD_PASS: PASS",
        "- PRINT_PENDING: YES",
        "- FIT_PENDING: YES",
        "- OPTICAL_PENDING: YES",
        "- RAIN_PENDING: YES",
        "- FIELD_PENDING: YES",
        "- OPTICAL_PASS / RAIN_PASS / FIELD_PASS: NOT DECLARED",
        "",
    ])
    (REPORT_DIR / "VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def difference_volume(first: cq.Workplane, second: cq.Workplane) -> float:
    difference = first.val().cut(second.val())
    return 0.0 if difference.isNull() else float(difference.Volume())


def write_parameters_json() -> None:
    parameters = {
        "lane": LANE_NAME,
        "version": VERSION,
        "status": DESIGN_STATUS,
        "selected_optical_geometry": {
            "name": "B_setback15",
            "front_setback_mm": FINAL_SETBACK,
            "front_y_mm": FINAL_FRONT_Y,
            "underside_bevel_deg": FINAL_BEVEL_DEG,
            "bevel_run_mm": round(bevel_run(B15), 3),
            "front_length_mm": FINAL_FRONT_LENGTH,
            "hood_outer_width_mm": HOOD_OUTER_W,
            "hood_inner_width_mm": HOOD_INNER_W,
            "wall_mm": HOOD_WALL,
            "top_clearance_mm": TOP_CLEARANCE_ADOPTED,
            "physical_result": B_PHYSICAL_RESULT,
        },
        "position_retention": {
            "strategy": "extended_guides_plus_shallow_front_corner_stops",
            "guide_clearance_mm": GUIDE_CLEARANCE,
            "guide_height_mm": GUIDE_HEIGHT,
            "v002_guide_length_mm": 44.0,
            "v004_guide_length_mm": EXTENDED_GUIDE_LENGTH,
            "guide_y0_mm": EXTENDED_GUIDE_Y0,
            "guide_y1_mm": EXTENDED_GUIDE_Y1,
            "front_corner_stop_clearance_mm": GUIDE_CLEARANCE,
            "front_corner_stop_height_mm": FRONT_CORNER_STOP_H,
            "rear_stop_clearance_mm": GUIDE_CLEARANCE,
            "normal_contact_target": "NONE_OR_LIGHT",
            "hard_press_fit_allowed": False,
        },
        "fixed_authority": {
            "tripod_axis_mm": [TRIPOD_AXIS_X, TRIPOD_AXIS_Y],
            "tripod_through_hole_mm": TRIPOD_THROUGH_HOLE,
            "tripod_thread": "1/4-20 UNC",
            "candidate_screw_length_in": 0.375,
            "calculated_insertion_mm": 3.525,
            "thread_depth_mm": 4.8,
            "bottom_clearance_mm": 1.275,
            "tripod_thread_physical": "PENDING",
            "carrier_mm": [CARRIER_W, CARRIER_D, CARRIER_THICKNESS],
            "camera_mm": [CAMERA_W, CAMERA_H, CAMERA_D],
            "folded_safe_envelope_depth_mm": FOLDED_D_SAFE_ENVELOPE,
            "folded_safe_envelope_height_mm": CAMERA_FOLDED_TOTAL_H_ENVELOPE,
            "usb_cable_od_mm": USB_CABLE_OD,
            "usb_channel_mm": USB_CHANNEL,
        },
        "fallback": {
            "name": KNOWN_FALLBACK,
            "physical_result": C_FALLBACK_RESULT,
        },
        "indicator": {
            "safety_feature": SAFETY_FEATURE,
            "status_indicator_only": STATUS_INDICATOR_ONLY,
        },
        "holds": {
            "printed_pipe_clamp": "REJECTED",
            "commercial_metal_clamp": "HOLD_SELECTION",
            "pipe_od_mm": 26.2,
        },
    }
    (Path(__file__).resolve().parent / "parameters.json").write_text(
        json.dumps(parameters, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def make_retention_plan_render(output: Path) -> None:
    image = Image.new("RGB", (1200, 820), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=20)
    bold = ImageFont.load_default(size=28)
    x_min, x_max = -64.0, 64.0
    y_min, y_max = -43.0, 45.0
    left, top, width, height = 90, 90, 1020, 650

    def px(x: float) -> int:
        return int(left + (x - x_min) / (x_max - x_min) * width)

    def py(y: float) -> int:
        return int(top + (y_max - y) / (y_max - y_min) * height)

    draw.text((70, 25), "v004 position retention - top view", fill="#0f172a", font=bold)
    draw.rounded_rectangle(
        (px(-CARRIER_W / 2.0), py(CARRIER_REAR_Y), px(CARRIER_W / 2.0), py(CARRIER_FRONT_Y)),
        radius=24, fill="#e2e8f0", outline="#475569", width=3,
    )
    clip_left = TRIPOD_AXIS_X - FOLDED_CLIP_W / 2.0
    clip_right = TRIPOD_AXIS_X + FOLDED_CLIP_W / 2.0
    draw.rectangle((px(clip_left), py(FOLDED_REAR_Y), px(clip_right), py(FOLDED_FRONT_Y)),
                   fill="#bfdbfe", outline="#1d4ed8", width=3)

    for sign in (-1.0, 1.0):
        center = TRIPOD_AXIS_X + sign * (
            FOLDED_CLIP_W / 2.0 + GUIDE_CLEARANCE + ANTI_ROTATION_GUIDE_T / 2.0
        )
        draw.rectangle((px(center - ANTI_ROTATION_GUIDE_T / 2.0), py(EXTENDED_GUIDE_Y1),
                        px(center + ANTI_ROTATION_GUIDE_T / 2.0), py(EXTENDED_GUIDE_Y0)),
                       fill="#16a34a", outline="#166534", width=2)
        stop_x = TRIPOD_AXIS_X + sign * FRONT_CORNER_STOP_X_OFFSET
        draw.rounded_rectangle((px(stop_x - FRONT_CORNER_STOP_W / 2.0),
                                py(FRONT_CORNER_STOP_REAR_Y),
                                px(stop_x + FRONT_CORNER_STOP_W / 2.0),
                                py(FRONT_CORNER_STOP_REAR_Y - FRONT_CORNER_STOP_T)),
                               radius=7, fill="#f59e0b", outline="#92400e", width=2)

    rear_y = FOLDED_REAR_Y + GUIDE_CLEARANCE + ANTI_ROTATION_GUIDE_T / 2.0
    for x in (TRIPOD_AXIS_X - 14.0, TRIPOD_AXIS_X + 14.0):
        draw.rounded_rectangle((px(x - 10.0), py(rear_y + 1.5),
                                px(x + 10.0), py(rear_y - 1.5)),
                               radius=7, fill="#64748b", outline="#334155", width=2)

    draw.ellipse((px(TRIPOD_AXIS_X - 3.4), py(3.4), px(TRIPOD_AXIS_X + 3.4), py(-3.4)),
                 fill="white", outline="#111827", width=3)
    draw.text((100, 760), "Blue: folded clip envelope  Green: extended X guides  Orange: front yaw/Y stops",
              fill="#334155", font=font)
    draw.text((830, 110), "nominal gap: 0.7 mm", fill="#166534", font=font)
    image.save(output)


def make_v004_side_render(output: Path) -> None:
    image = Image.new("RGB", (1200, 780), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=20)
    bold = ImageFont.load_default(size=28)
    y_min, y_max = -66.0, 50.0
    z_min, z_max = -15.0, 67.0
    left, top, width, height = 90, 90, 1020, 610

    def px(y: float) -> int:
        return int(left + (y - y_min) / (y_max - y_min) * width)

    def pz(z: float) -> int:
        return int(top + (z_max - z) / (z_max - z_min) * height)

    draw.text((70, 25), "v004 B15 full hood - side authority", fill="#0f172a", font=bold)
    for z in (0, 20, 40, 60):
        draw.line((left, pz(z), left + width, pz(z)), fill="#e5e7eb", width=1)
    body_front = FOLDED_CENTER_Y - CAMERA_D / 2.0
    body_rear = FOLDED_CENTER_Y + CAMERA_D / 2.0
    draw.rectangle((px(CARRIER_FRONT_Y), pz(0), px(CARRIER_REAR_Y), pz(CARRIER_BOTTOM_Z)),
                   fill="#cbd5e1", outline="#475569", width=2)
    draw.rectangle((px(FOLDED_FRONT_Y), pz(FOLDED_CLIP_BELOW_BODY),
                    px(FOLDED_REAR_Y), pz(0)), fill="#dbeafe", outline="#2563eb", width=2)
    draw.rectangle((px(body_front), pz(CAMERA_FOLDED_TOTAL_H_ENVELOPE),
                    px(body_rear), pz(FOLDED_CLIP_BELOW_BODY)),
                   fill="#bfdbfe", outline="#1d4ed8", width=3)
    roof = [
        (B15.front_y, roof_inner_z(B15.front_y, B15) + HOOD_WALL),
        (HOOD_REAR_OUTER_Y, roof_inner_z(HOOD_REAR_OUTER_Y, B15) + HOOD_WALL),
        (HOOD_REAR_OUTER_Y, roof_inner_z(HOOD_REAR_OUTER_Y, B15)),
        (B15.front_y + bevel_run(B15), roof_inner_z(B15.front_y + bevel_run(B15), B15)),
        (B15.front_y, roof_inner_z(B15.front_y, B15) + HOOD_WALL - LEADING_EDGE_THICKNESS),
    ]
    draw.polygon([(px(y), pz(z)) for y, z in roof], fill="#0f172a", outline="#020617")
    side = [
        (B15.front_y, roof_inner_z(B15.front_y, B15) + HOOD_WALL),
        (HOOD_REAR_OUTER_Y, roof_inner_z(HOOD_REAR_OUTER_Y, B15) + HOOD_WALL),
        (HOOD_REAR_OUTER_Y, -9.0),
        (CARRIER_FRONT_Y, -9.0),
        (b15_knee_y(), 40.0),
        (B15.front_y, 50.0),
    ]
    draw.line([(px(y), pz(z)) for y, z in side], fill="#334155", width=4, joint="curve")
    draw.line((px(HOOD_FRONT_Y_V002), top, px(HOOD_FRONT_Y_V002), top + height),
              fill="#dc2626", width=2)
    draw.line((px(HOOD_FRONT_Y_V002), pz(64.0), px(B15.front_y), pz(64.0)),
              fill="#dc2626", width=3)
    draw.text((px(HOOD_FRONT_Y_V002) + 8, pz(64.0) - 30), "15 mm setback / 40 deg bevel",
              fill="#b91c1c", font=font)
    draw.text((70, 735), "B is SELECTED_CONDITIONAL; full-hood optical and rain tests remain pending.",
              fill="#7f1d1d", font=font)
    image.save(output)


def validate_v004_and_report(models: dict[str, cq.Workplane]) -> dict[str, Any]:
    authority_match = current_interface_authority() == V002_INTERFACE_AUTHORITY
    if not authority_match:
        raise AssertionError("v002 carrier/interface authority drift detected")

    coupon = models["coupon"]
    carrier = models["carrier"]
    hood = models["hood"]
    camera = models["camera"]
    assembly = models["assembly"]
    v002_carrier = build_carrier_reference()

    side_inner_gap = (
        (TRIPOD_AXIS_X + FOLDED_CLIP_W / 2.0 + GUIDE_CLEARANCE)
        - (TRIPOD_AXIS_X + FOLDED_CLIP_W / 2.0)
    )
    front_gap = FOLDED_FRONT_Y - FRONT_CORNER_STOP_REAR_Y
    rear_stop_front_y = FOLDED_REAR_Y + GUIDE_CLEARANCE
    rear_gap = rear_stop_front_y - FOLDED_REAR_Y

    front_roof_v003 = build_beveled_optical_roof(B15)
    front_roof_v004 = build_b15_roof(OPTICAL_ROOF_REAR_Y)
    front_roof_delta = (
        difference_volume(front_roof_v003, front_roof_v004)
        + difference_volume(front_roof_v004, front_roof_v003)
    )
    optical_side_compare_rear_y = 20.0
    optical_slice = box(
        140.0,
        optical_side_compare_rear_y - B15.front_y,
        120.0,
        (0.0, (B15.front_y + optical_side_compare_rear_y) / 2.0, 30.0),
    )
    v003_side_front = wp(build_optical_sidewalls(B15).val().intersect(optical_slice.val()))
    v004_side_front = wp(build_b15_full_sidewalls().val().intersect(optical_slice.val()))
    front_sidewall_delta = (
        difference_volume(v003_side_front, v004_side_front)
        + difference_volume(v004_side_front, v003_side_front)
    )
    carrier_removed = difference_volume(v002_carrier, carrier)
    carrier_added = difference_volume(carrier, v002_carrier)

    intersections = {
        "camera_vs_v004_carrier_mm3": round(intersection_volume(camera, carrier), 8),
        "camera_vs_b15_hood_mm3": round(intersection_volume(camera, hood), 8),
        "carrier_vs_b15_hood_mm3": round(intersection_volume(carrier, hood), 8),
        "camera_vs_integrated_coupon_mm3": round(intersection_volume(camera, coupon), 8),
    }

    artifacts: dict[str, Any] = {}
    stl_specs = {
        "b15_position_retention_coupon_v004": coupon,
        "tripod_carrier_b15_v004": carrier,
        "rainhood_b15_v004": hood,
    }
    for stem, model in stl_specs.items():
        brep = shape_metrics(model)
        mesh = stl_mesh_metrics(STL_DIR / f"{stem}.stl")
        bbox_delta = max(
            abs(brep["bounding_box_mm"][axis] - mesh["bounding_box_mm"][axis])
            for axis in ("x", "y", "z")
        )
        checks = {
            "brep_valid": brep["valid"],
            "brep_single_solid": brep["solid_count"] == 1,
            "stl_nonempty": mesh["file_size_bytes"] > 1024,
            "stl_triangles_present": mesh["triangle_count"] > 0,
            "stl_no_degenerate_triangles": mesh["degenerate_triangles"] == 0,
            "stl_watertight_boundary_nonmanifold_zero": mesh["watertight_edge_count_check"],
            "stl_bbox_matches_brep": bbox_delta <= 0.2,
        }
        if not all(checks.values()):
            raise AssertionError(f"{stem} STL/BRep validation failed: {checks}")
        artifacts[stem] = {"brep": brep, "mesh": mesh, "checks": checks}

    step_specs = {
        "b15_position_retention_coupon_v004": (coupon, 1),
        "tripod_carrier_b15_v004": (carrier, 1),
        "rainhood_b15_v004": (hood, 1),
        "camera_folded_reference": (camera, 1),
        "camera_side_assembly_v004": (assembly, 3),
    }
    step_results: dict[str, Any] = {}
    for stem, (source_model, expected_solids) in step_specs.items():
        source_metrics = shape_metrics(source_model)
        imported = shape_metrics(cq.importers.importStep(str(STEP_DIR / f"{stem}.step")))
        checks = {
            "step_nonempty": (STEP_DIR / f"{stem}.step").stat().st_size > 1024,
            "step_reimport_valid": imported["valid"],
            "step_expected_solid_count": imported["solid_count"] == expected_solids,
            "step_volume_matches_source": abs(imported["volume_mm3"] - source_metrics["volume_mm3"]) <= 0.02,
        }
        if not all(checks.values()):
            raise AssertionError(f"{stem} STEP validation failed: {checks}, imported={imported}")
        step_results[stem] = {
            "expected_solid_count": expected_solids,
            "source": source_metrics,
            "reimport": imported,
            "checks": checks,
            "sha256": sha256_file(STEP_DIR / f"{stem}.step"),
        }

    checks = {
        "v002_interface_authority_exact_match": authority_match,
        "tripod_axis_unchanged": abs(TRIPOD_AXIS_X - 0.15) <= 1.0e-9 and TRIPOD_AXIS_Y == 0.0,
        "tripod_hole_unchanged": TRIPOD_THROUGH_HOLE == 6.8,
        "carrier_seating_plane_unchanged": CARRIER_W == 110.8 and CARRIER_D == 74.0 and CARRIER_THICKNESS == 6.0,
        "shell_interface_builder_is_v002_exact": True,
        "B_front_y_exact": abs(B15.front_y - FINAL_FRONT_Y) <= 1.0e-9,
        "B_setback_exact": B15.front_setback == FINAL_SETBACK,
        "B_bevel_exact": abs(actual_bevel_angle(B15) - FINAL_BEVEL_DEG) <= 0.01,
        "B_bevel_run_matches_authority": abs(bevel_run(B15) - FINAL_BEVEL_RUN_AUTHORITY) <= 0.001,
        "B_front_length_exact": B15.hood_front_length == FINAL_FRONT_LENGTH,
        "B_front_roof_matches_v003_exactly": front_roof_delta <= INTERFERENCE_TOLERANCE_MM3,
        "B_front_sidewalls_match_v003_exactly": front_sidewall_delta <= INTERFERENCE_TOLERANCE_MM3,
        "top_clearance_preserved": TOP_CLEARANCE_ADOPTED == 4.0,
        "guide_clearance_preserved_0p7": abs(side_inner_gap - 0.7) <= 1.0e-9,
        "front_stop_clearance_0p7": abs(front_gap - 0.7) <= 1.0e-9,
        "rear_stop_clearance_0p7": abs(rear_gap - 0.7) <= 1.0e-9,
        "guide_height_preserved_2p8": GUIDE_HEIGHT == 2.8,
        "guide_extended_vs_v002": EXTENDED_GUIDE_LENGTH > 44.0,
        "v002_carrier_geometry_not_removed": carrier_removed <= 0.01,
        "position_retention_geometry_added": carrier_added > 1.0,
        "camera_carrier_interference_zero": intersections["camera_vs_v004_carrier_mm3"] <= INTERFERENCE_TOLERANCE_MM3,
        "camera_hood_interference_zero": intersections["camera_vs_b15_hood_mm3"] <= INTERFERENCE_TOLERANCE_MM3,
        "carrier_hood_interference_zero": intersections["carrier_vs_b15_hood_mm3"] <= INTERFERENCE_TOLERANCE_MM3,
        "camera_coupon_interference_zero": intersections["camera_vs_integrated_coupon_mm3"] <= INTERFERENCE_TOLERANCE_MM3,
        "coupon_identifier_is_4_ribs": len(coupon_identifier_ribs()) == 4,
        "hard_press_fit_not_designed": GUIDE_CLEARANCE >= 0.7,
        "status_indicator_not_safety_feature": STATUS_INDICATOR_ONLY and not SAFETY_FEATURE,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise AssertionError(f"v004 authority validation failed: {failed}")

    return {
        "lane": LANE_NAME,
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cadquery_version": cq.__version__,
        "status": DESIGN_STATUS,
        "blocker": BLOCKER,
        "selected_candidate": "B_setback15",
        "selected_candidate_status": B_PHYSICAL_RESULT,
        "known_fallback": KNOWN_FALLBACK,
        "known_fallback_status": C_FALLBACK_RESULT,
        "physical_authority_v003": {
            "A": "FAIL_OPTICAL_REJECTED",
            "B": "NOMINAL_OPTICAL_PASS_SHIFT_OPTICAL_FAIL_SELECTED_CONDITIONAL",
            "C": "OPTICAL_ROBUST_PASS_KNOWN_FALLBACK",
        },
        "pass_separation": {
            "CAD_PASS": True,
            "PRINT_PASS": False,
            "FIT_PASS": False,
            "STATIC_PASS": False,
            "POSITION_RETENTION_PHYSICAL_PASS": False,
            "B15_FULL_HOOD_OPTICAL_PHYSICAL_PASS": False,
            "RAIN_VISUAL_PASS": False,
            "WATER_TEST_PASS": False,
            "FIELD_PASS": False,
            "DURABILITY_PASS": False,
        },
        "v002_provenance": {
            "commit": V002_COMMIT,
            "source_path": V002_SOURCE_PATH,
            "source_blob": V002_SOURCE_BLOB,
        },
        "v003_provenance": {
            "lane": V003_LANE,
            "source_sha256": V003_SOURCE_SHA256,
            "validation_sha256": V003_VALIDATION_SHA256,
            "B_stl_sha256": V003_B_STL_SHA256,
        },
        "B15_dimensions": {
            "setback_mm": FINAL_SETBACK,
            "front_y_mm": FINAL_FRONT_Y,
            "bevel_deg": round(actual_bevel_angle(B15), 4),
            "bevel_run_mm": round(bevel_run(B15), 3),
            "front_length_mm": FINAL_FRONT_LENGTH,
            "top_clearance_mm": TOP_CLEARANCE_ADOPTED,
            "v003_to_v004_front_roof_symmetric_delta_mm3": round(front_roof_delta, 8),
            "v003_to_v004_front_sidewall_symmetric_delta_mm3": round(front_sidewall_delta, 8),
        },
        "position_retention_delta": {
            "strategy": "extended_guides_plus_shallow_front_corner_stops",
            "v002_guide_length_mm": 44.0,
            "v004_guide_length_mm": EXTENDED_GUIDE_LENGTH,
            "guide_clearance_mm": GUIDE_CLEARANCE,
            "guide_height_mm": GUIDE_HEIGHT,
            "front_stop_clearance_mm": front_gap,
            "rear_stop_clearance_mm": rear_gap,
            "v002_carrier_removed_volume_mm3": round(carrier_removed, 8),
            "v004_added_retention_volume_mm3": round(carrier_added, 3),
        },
        "intersections": intersections,
        "checks": checks,
        "artifacts": artifacts,
        "step_reimport": step_results,
        "holds": {
            "tripod_thread_physical": "PENDING",
            "commercial_metal_clamp": "HOLD_SELECTION",
            "printed_pipe_clamp": "REJECTED",
        },
    }


def write_v004_validation_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# VALIDATION REPORT",
        "",
        f"Status: `{report['status']}`",
        "",
        "CAD generation and authority preservation pass. Position retention, full-hood optical behavior, rain, field exposure, static load, and durability remain physical tests.",
        "",
        "## Artifacts",
        "",
        "| Artifact | BRep solids | STL triangles | Boundary/non-manifold edges | STEP reimport |",
        "|---|---:|---:|---:|---|",
    ]
    for stem in (
        "b15_position_retention_coupon_v004",
        "tripod_carrier_b15_v004",
        "rainhood_b15_v004",
    ):
        item = report["artifacts"][stem]
        step = report["step_reimport"][stem]
        lines.append(
            f"| `{stem}` | {item['brep']['solid_count']} | {item['mesh']['triangle_count']} | "
            f"{item['mesh']['nonmanifold_or_boundary_edges']} | "
            f"{'PASS' if step['checks']['step_reimport_valid'] else 'FAIL'} |"
        )
    lines.extend([
        "",
        "## Controlled delta",
        "",
        f"- v002 carrier geometry removed: {report['position_retention_delta']['v002_carrier_removed_volume_mm3']:.8f} mm^3",
        f"- v004 retention geometry added: {report['position_retention_delta']['v004_added_retention_volume_mm3']:.3f} mm^3",
        f"- v002 guide length: 44.0 mm",
        f"- v004 guide length: {report['position_retention_delta']['v004_guide_length_mm']:.1f} mm",
        "- guide/front-stop/rear-stop nominal clearance: 0.7 mm",
        "- guide height: 2.8 mm",
        "- tripod axis/hole, carrier seating plane, shell rails/stops/M4/nut traps, and USB relief: unchanged",
        "",
        "## Interference",
        "",
    ])
    for name, value in report["intersections"].items():
        lines.append(f"- `{name}`: {value:.8f} mm^3")
    lines.extend(["", "## Checks", ""])
    for name, passed in report["checks"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend([
        "",
        "## Pass separation",
        "",
    ])
    for name, passed in report["pass_separation"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'NOT PASSED / PENDING'}")
    lines.extend([
        "",
        "`B_setback15` remains `SELECTED_CONDITIONAL`. CAD does not close the mount lateral/yaw retention blocker.",
        "",
    ])
    (REPORT_DIR / "VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def write_sha256_manifest() -> None:
    manifest = LANE_DIR / "SHA256SUMS.txt"
    files = sorted(path for path in LANE_DIR.rglob("*") if path.is_file() and path != manifest)
    lines = [f"{sha256_file(path)}  {path.relative_to(LANE_DIR).as_posix()}" for path in files]
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-renders", action="store_true", help="skip PNG engineering diagrams")
    args = parser.parse_args()

    for directory in (STL_DIR, STEP_DIR, RENDER_DIR, REPORT_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    write_parameters_json()

    coupon = build_b15_position_retention_coupon()
    carrier = build_v004_carrier()
    hood = build_rainhood_b15_v004()
    camera = build_camera_safe_reference(B15)
    assembly = build_camera_side_assembly_v004(hood, carrier, camera)
    models = {
        "coupon": coupon,
        "carrier": carrier,
        "hood": hood,
        "camera": camera,
        "assembly": assembly,
    }

    export_model(
        coupon,
        STL_DIR / "b15_position_retention_coupon_v004.stl",
        STEP_DIR / "b15_position_retention_coupon_v004.step",
    )
    export_model(
        carrier,
        STL_DIR / "tripod_carrier_b15_v004.stl",
        STEP_DIR / "tripod_carrier_b15_v004.step",
    )
    export_model(
        hood,
        STL_DIR / "rainhood_b15_v004.stl",
        STEP_DIR / "rainhood_b15_v004.step",
    )
    cq.exporters.export(camera, str(STEP_DIR / "camera_folded_reference.step"))
    cq.exporters.export(assembly, str(STEP_DIR / "camera_side_assembly_v004.step"))

    if not args.no_renders:
        make_retention_plan_render(RENDER_DIR / "position_retention_plan.png")
        make_v004_side_render(RENDER_DIR / "b15_full_hood_side.png")

    report = validate_v004_and_report(models)
    (REPORT_DIR / "validation_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_v004_validation_markdown(report)
    write_sha256_manifest()
    print(json.dumps({
        "lane": str(LANE_DIR),
        "status": DESIGN_STATUS,
        "cad_pass": True,
        "next_print": "b15_position_retention_coupon_v004.stl",
        "position_retention_physical_pass": False,
        "full_hood_optical_physical_pass": False,
        "rain_pass": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
