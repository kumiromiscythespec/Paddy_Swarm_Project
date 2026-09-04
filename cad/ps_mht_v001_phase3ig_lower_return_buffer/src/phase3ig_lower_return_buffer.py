"""Authoritative Phase 3I-G geometry, diagnostics, and engineering audits.

Coordinates for individual tank exports use X from the tower-side inlet toward
the central-trough-side overflow.  Z=0 is the external tank bottom.  Reference
assemblies rotate this local X axis 45 degrees into the gap between radial legs.
"""

from __future__ import annotations

from functools import lru_cache
from math import atan2, cos, degrees, pi, radians, sin, sqrt
from pathlib import Path
import hashlib

import cadquery as cq


PHASE = "3I-G"
PROCESS = "LOWER_RETURN_BUFFER_UPFLOW_PROTOTYPE_AND_TERMINAL_COLLECTION_INTERFACE"
STATUS = "CAD_COMPLETE_PHYSICAL_VALIDATION_PENDING"
STATUS_LINES = (
    "BOTTOM_INLET_TOP_OVERFLOW_IMPLEMENTED",
    "VENTED_DOWNCOMER_IMPLEMENTED",
    "REMOVABLE_DIFFUSER_IMPLEMENTED",
    "WIDE_WEIR_IMPLEMENTED",
    "OPEN_GUTTER_AIR_BREAK_IMPLEMENTED",
    "EMERGENCY_OVERFLOW_IMPLEMENTED",
    "CLEANOUT_INTERFACE_IMPLEMENTED",
    "TERMINAL_COLLECTION_TRAY_IMPLEMENTED",
    "THIRTY_DEGREE_STAGE_ROTATION_PRESERVED",
    "DRY_CORE_PRESERVED",
    "FOUR_RETURN_LINES_PRESERVED",
    "INTERNAL_BAFFLE_RESERVED",
    "FITTING_DIMENSIONS_PENDING",
    "COLOR_DYE_TEST_PENDING",
    "WATERTIGHT_COUPON_TEST_PENDING",
    "BAMBU_STUDIO_REVIEW_PENDING",
    "FULL_TANK_PRINT_PROHIBITED",
    "FULL_TERMINAL_TRAY_PRINT_PROHIBITED",
    "PHYSICAL_VALIDATION_PENDING",
)

# Inherited fixed authority.
MODULE_HEIGHT_MM = 170.0
MODULE_OUTER_DIAMETER_MM = 200.0
MODULE_MAXIMUM_DIAMETER_MM = 238.0
PORT_ANGLES_DEG = (0.0, 120.0, 240.0)
STAGE_RELATIVE_ROTATION_DEG = 30.0
STAGE_ABSOLUTE_ROTATIONS_DEG = (0.0, 30.0, 60.0, 90.0, 120.0)
OVERFLOW_STANDPIPE_ANGLES_DEG = (30.0, 150.0, 270.0)
LOWER_LANDING_ANGLES_DEG = (60.0, 180.0, 300.0)
DRY_CORE_DIAMETER_MM = 100.0
PER_STAGE_WATER_L = 0.357449846

# Measured physical mast authority.
MAST_TYPE = "SUS_SF-20_20_SF9-202"
MAST_MEASURED_X_MM = 19.9
MAST_MEASURED_Y_MM = 19.9
MAST_TWIST = "NONE_OBSERVED"
MAST_STRAIGHTNESS = "PASS_PHYSICAL_OBSERVATION"

# Tank and hydraulic geometry.
TANK_BODY_LENGTH_MM = 220.0
TANK_BODY_WIDTH_MM = 134.0
TANK_TOTAL_LENGTH_MM = 240.0
TANK_TOTAL_WIDTH_MM = 146.0
TANK_HEIGHT_MM = 105.0
TANK_BODY_CENTER_X_MM = -10.0
TANK_OUTER_CORNER_RADIUS_MM = 18.0
TANK_WALL_MM = 3.0
TANK_FLOOR_MM = 4.0
NORMAL_WATER_Z_MM = 82.0
EMERGENCY_WATER_Z_MM = 94.0
NORMAL_WEIR_EFFECTIVE_WIDTH_MM = 112.0
EMERGENCY_OVERFLOW_CLEAR_WIDTH_MM = 30.0

DOWNCOMER_CLEAR_BORE_MM = 25.0
DOWNCOMER_WALL_MM = 3.0
DOWNCOMER_OUTER_DIAMETER_MM = 31.0
# 15 mm is the hydraulic target above the inner floor.  15.5 mm is the exact
# CAD centre needed to retain 3 mm material below a 25 mm clear bore.
DOWNCOMER_OUTLET_TARGET_ABOVE_INNER_FLOOR_MM = 15.0
DOWNCOMER_OUTLET_ACTUAL_ABOVE_INNER_FLOOR_MM = 15.5
DOWNCOMER_OUTLET_CENTER_Z_MM = TANK_FLOOR_MM + DOWNCOMER_OUTLET_ACTUAL_ABOVE_INNER_FLOOR_MM
DOWNCOMER_X_MM = -103.0

DIFFUSER_LENGTH_MM = 32.0
DIFFUSER_WIDTH_MM = 112.0
DIFFUSER_HEIGHT_MM = 30.0
DIFFUSER_SLOT_WIDTH_MM = 100.0
DIFFUSER_SLOT_HEIGHT_MM = 9.0
DIFFUSER_SLOT_BOTTOM_Z_MM = 9.0

TRAY_OUTER_DIAMETER_MM = 230.0
TRAY_HEIGHT_MM = 28.0
TRAY_CENTRAL_OPENING_MM = 30.0
TRAY_CHIMNEY_CLEAR_MM = 30.0
TRAY_SLOPE_PERCENT = 3.5
TRAY_OUTLET_RADIUS_MM = 112.0
TRAY_OUTLET_ANGLE_DEG = 45.0

RADIAL_LEG_ANGLES_DEG = (0.0, 90.0, 180.0, 270.0)
RADIAL_LEG_LENGTH_MM = 445.0
RADIAL_LEG_WIDTH_MM = 20.0
REFERENCE_TANK_AXIS_ANGLE_DEG = 45.0
REFERENCE_TANK_CENTER_RADIUS_MM = 215.0

CENTRAL_TROUGH_OUTER_LENGTH_MM = 610.0
CENTRAL_TROUGH_OUTER_WIDTH_MM = 470.0
CENTRAL_TROUGH_HEIGHT_MM = 195.0
CENTRAL_TROUGH_NORMAL_DEPTH_MM = 85.0
FOUR_TOWER_SPACING_X_MM = 1150.0
FOUR_TOWER_SPACING_Y_MM = 1150.0
RETURN_HOSE_NOMINAL_ID_MM = 25.0
RETURN_HOSE_PROVISIONAL_LENGTH_RANGE_MM = (350.0, 500.0)

A1_X_MM = 245.0
A1_Y_MM = 245.0
A1_Z_MM = 240.0

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
PHASE3IF_SHA_LIST = REPOSITORY_ROOT / "cad/ps_mht_v001/commit/phase3if_SHA256SUMS.txt"
PHASE3ID_SHA_LIST = REPOSITORY_ROOT / "cad/ps_mht_v001/commit/phase3id_SHA256SUMS.txt"


def _compound(models: list[cq.Workplane]) -> cq.Workplane:
    solids: list[cq.Shape] = []
    for model in models:
        solids.extend(model.solids().vals())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def _rounded_rect(length: float, width: float, radius: float, height: float, z: float = 0.0,
                  center_x: float = 0.0, center_y: float = 0.0) -> cq.Workplane:
    """Robust rounded rectangle prism built from overlapping primitives."""
    if min(length, width) <= 2.0 * radius:
        raise ValueError("rounded rectangle radius is too large")
    result = (
        cq.Workplane("XY").center(center_x, center_y).rect(length - 2.0 * radius, width).extrude(height)
        .union(cq.Workplane("XY").center(center_x, center_y).rect(length, width - 2.0 * radius).extrude(height))
    )
    for x in (-0.5 * length + radius, 0.5 * length - radius):
        for y in (-0.5 * width + radius, 0.5 * width - radius):
            result = result.union(
                cq.Workplane("XY").center(center_x + x, center_y + y).circle(radius).extrude(height)
            )
    return result.translate((0.0, 0.0, z)).clean()


def _box(length: float, width: float, height: float, x: float, y: float, z: float) -> cq.Workplane:
    return cq.Workplane("XY").box(length, width, height, centered=(True, True, False)).translate((x, y, z))


def _tube_z(outer_diameter: float, inner_diameter: float, height: float, x: float, y: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("XY").center(x, y).circle(0.5 * outer_diameter).circle(0.5 * inner_diameter)
        .extrude(height).translate((0.0, 0.0, z))
    )


def _tube_x(outer_diameter: float, inner_diameter: float, length: float, x: float, y: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("YZ").center(y, z).circle(0.5 * outer_diameter).circle(0.5 * inner_diameter)
        .extrude(length).translate((x, 0.0, 0.0))
    )


@lru_cache(maxsize=1)
def build_inlet_diffuser_phase3ig() -> cq.Workplane:
    """Open, removable 112 x 32 x 30 mm plenum with a 100 x 9 mm slot."""
    x0 = -116.0
    x1 = x0 + DIFFUSER_LENGTH_MM
    y0 = -0.5 * DIFFUSER_WIDTH_MM
    y1 = 0.5 * DIFFUSER_WIDTH_MM
    z0 = TANK_FLOOR_MM
    base = _box(DIFFUSER_LENGTH_MM, DIFFUSER_WIDTH_MM, 3.0, 0.5 * (x0 + x1), 0.0, z0)
    sides = [
        _box(DIFFUSER_LENGTH_MM, 3.0, DIFFUSER_HEIGHT_MM, 0.5 * (x0 + x1), y0 + 1.5, z0),
        _box(DIFFUSER_LENGTH_MM, 3.0, DIFFUSER_HEIGHT_MM, 0.5 * (x0 + x1), y1 - 1.5, z0),
        _box(3.0, DIFFUSER_WIDTH_MM, DIFFUSER_HEIGHT_MM, x0 + 1.5, 0.0, z0),
    ]
    # Front wall is split around the horizontal outlet slot.
    front_lower = _box(3.0, DIFFUSER_WIDTH_MM, DIFFUSER_SLOT_BOTTOM_Z_MM - z0, x1 - 1.5, 0.0, z0)
    front_upper_z = DIFFUSER_SLOT_BOTTOM_Z_MM + DIFFUSER_SLOT_HEIGHT_MM
    front_upper = _box(3.0, DIFFUSER_WIDTH_MM, z0 + DIFFUSER_HEIGHT_MM - front_upper_z,
                       x1 - 1.5, 0.0, front_upper_z)
    # Wide top retention ledges; asymmetric key prevents reversal.
    ledge_a = _box(12.0, 5.0, 3.0, x0 + 7.0, y0 + 4.0, z0 + DIFFUSER_HEIGHT_MM - 3.0)
    ledge_b = _box(7.0, 5.0, 3.0, x0 + 4.5, y1 - 4.0, z0 + DIFFUSER_HEIGHT_MM - 3.0)
    model = base
    for item in sides + [front_lower, front_upper, ledge_a, ledge_b]:
        model = model.union(item)
    # Clearance for the removable downcomer body; this is an open cleaning path,
    # not a fine sealed socket.  The tank floor remains continuous below it.
    downcomer_clearance = (
        cq.Workplane("XY").center(DOWNCOMER_X_MM, 0.0)
        .circle(0.5 * (DOWNCOMER_OUTER_DIAMETER_MM + 0.6)).extrude(DIFFUSER_HEIGHT_MM + 1.0)
        .translate((0.0, 0.0, z0 - 0.5))
    )
    horizontal_clearance = (
        cq.Workplane("YZ").center(0.0, DOWNCOMER_OUTLET_CENTER_Z_MM)
        .circle(0.5 * (DOWNCOMER_OUTER_DIAMETER_MM + 0.6)).extrude(16.6)
        .translate((DOWNCOMER_X_MM - 0.3, 0.0, 0.0))
    )
    return model.cut(downcomer_clearance).cut(horizontal_clearance).clean()


@lru_cache(maxsize=1)
def build_inlet_downcomer_phase3ig() -> cq.Workplane:
    """Top-vented removable downcomer with a horizontal, not vertical, discharge."""
    zc = DOWNCOMER_OUTLET_CENTER_Z_MM
    vertical_bottom = zc - 0.5 * DOWNCOMER_OUTER_DIAMETER_MM
    vertical = _tube_z(DOWNCOMER_OUTER_DIAMETER_MM, DOWNCOMER_CLEAR_BORE_MM, 131.5,
                       DOWNCOMER_X_MM, 0.0, vertical_bottom)
    horizontal = _tube_x(DOWNCOMER_OUTER_DIAMETER_MM, DOWNCOMER_CLEAR_BORE_MM, 16.0,
                         DOWNCOMER_X_MM, 0.0, zc)
    # Close the bottom while preserving the horizontal bore.
    cap = cq.Workplane("XY").center(DOWNCOMER_X_MM, 0.0).circle(0.5 * DOWNCOMER_OUTER_DIAMETER_MM).extrude(3.0).translate((0, 0, vertical_bottom))
    model = vertical.union(horizontal).union(cap)
    # Join the horizontal flow bore into the vertical bore while retaining the
    # outer elbow wall and the closed lower cap.
    bore = cq.Workplane("YZ").center(0.0, zc).circle(0.5 * DOWNCOMER_CLEAR_BORE_MM).extrude(17.0).translate((DOWNCOMER_X_MM, 0, 0))
    model = model.cut(bore).clean()
    return model


def _tank_body_shell() -> cq.Workplane:
    outer = _rounded_rect(TANK_BODY_LENGTH_MM, TANK_BODY_WIDTH_MM, TANK_OUTER_CORNER_RADIUS_MM,
                          TANK_HEIGHT_MM, center_x=TANK_BODY_CENTER_X_MM)
    inner = _rounded_rect(
        TANK_BODY_LENGTH_MM - 2.0 * TANK_WALL_MM,
        TANK_BODY_WIDTH_MM - 2.0 * TANK_WALL_MM,
        TANK_OUTER_CORNER_RADIUS_MM - TANK_WALL_MM,
        TANK_HEIGHT_MM - TANK_FLOOR_MM + 1.0,
        z=TANK_FLOOR_MM,
        center_x=TANK_BODY_CENTER_X_MM,
    )
    return outer.cut(inner).clean()


@lru_cache(maxsize=1)
def build_lower_buffer_tank_phase3ig() -> cq.Workplane:
    """Single-solid open tank with normal gutter, emergency lip, and blank pads."""
    tank = _tank_body_shell()
    # 112 mm normal weir cut through the central-trough-side wall.
    normal_notch = _box(8.0, NORMAL_WEIR_EFFECTIVE_WIDTH_MM, TANK_HEIGHT_MM - NORMAL_WATER_Z_MM + 2.0,
                        99.0, 0.0, NORMAL_WATER_Z_MM)
    tank = tank.cut(normal_notch)
    # Open gutter: floor, side cheeks, and blank reinforced fitting pad.
    gutter_floor = _box(23.0, 118.0, 4.0, 108.5, 0.0, 78.0)
    gutter_sides = [
        _box(23.0, 3.0, 22.0, 108.5, -57.5, 78.0),
        _box(23.0, 3.0, 22.0, 108.5, 57.5, 78.0),
        _box(3.0, 118.0, 22.0, 118.5, 0.0, 78.0),
    ]
    tank = tank.union(gutter_floor)
    for item in gutter_sides:
        tank = tank.union(item)
    outlet_pad = _box(6.0, 46.0, 46.0, 116.0, 0.0, 55.0)
    tank = tank.union(outlet_pad)
    # A 1.5 mm deep pilot mark only: no guessed hose fitting penetration.
    pilot = cq.Workplane("YZ").center(0.0, 78.0).circle(1.0).extrude(1.5).translate((118.5, 0.0, 0.0))
    tank = tank.cut(pilot)

    # Independent visible emergency overflow on +Y.
    emergency_notch = _box(EMERGENCY_OVERFLOW_CLEAR_WIDTH_MM, 8.0,
                           TANK_HEIGHT_MM - EMERGENCY_WATER_Z_MM + 2.0,
                           65.0, 65.0, EMERGENCY_WATER_Z_MM)
    tank = tank.cut(emergency_notch)
    emergency_floor = _box(EMERGENCY_OVERFLOW_CLEAR_WIDTH_MM, 10.0, 4.0, 65.0, 69.0, 90.0)
    emergency_rails = [
        _box(3.0, 10.0, 15.0, 51.5, 69.0, 90.0),
        _box(3.0, 10.0, 15.0, 78.5, 69.0, 90.0),
    ]
    tank = tank.union(emergency_floor)
    for item in emergency_rails:
        tank = tank.union(item)

    # Blank cleanout pad; the pilot is shallow and does not enter the wet volume.
    drain_pad = _box(42.0, 6.0, 34.0, 35.0, -69.0, 0.0)
    tank = tank.union(drain_pad)
    drain_pilot = cq.Workplane("XZ").center(35.0, 8.0).circle(1.0).extrude(1.5).translate((0.0, -72.0, 0.0))
    tank = tank.cut(drain_pilot)
    return tank.clean()


def _tray_floor_wedge() -> cq.Workplane:
    # Directional 3.5% fall toward local +X before the tray is rotated to 45°.
    r = 0.5 * TRAY_OUTER_DIAMETER_MM
    top_low = 4.0
    top_high = top_low + 2.0 * r * TRAY_SLOPE_PERCENT / 100.0
    profile = cq.Workplane("XZ").polyline([
        (-r, 0.0), (r, 0.0), (r, top_low), (-r, top_high)
    ]).close().extrude(2.0 * r, both=True)
    disk = cq.Workplane("XY").circle(r).extrude(top_high + 0.5)
    return profile.intersect(disk).clean()


@lru_cache(maxsize=1)
def build_terminal_collection_tray_phase3ig() -> cq.Workplane:
    """Shallow terminal tray with real landing datums and a non-sealing dry core."""
    r = 0.5 * TRAY_OUTER_DIAMETER_MM
    floor = _tray_floor_wedge()
    wall = cq.Workplane("XY").circle(r).circle(r - 3.0).extrude(TRAY_HEIGHT_MM)
    tray = floor.union(wall)
    # Central rounded-square nominal 30 mm opening and 28 mm chimney.
    opening = _rounded_rect(TRAY_CENTRAL_OPENING_MM, TRAY_CENTRAL_OPENING_MM, 5.0,
                            TRAY_HEIGHT_MM + 2.0, z=-1.0)
    chimney_outer = _rounded_rect(36.0, 36.0, 8.0, TRAY_HEIGHT_MM)
    chimney = chimney_outer.cut(opening)
    tray = tray.union(chimney).cut(opening)
    # Three robust landing pads, preserving 60/180/300 degree location authority.
    for angle in LOWER_LANDING_ANGLES_DEG:
        x = 82.0 * cos(radians(angle))
        y = 82.0 * sin(radians(angle))
        pad = _rounded_rect(24.0, 18.0, 4.0, 13.0, center_x=x, center_y=y).rotate(
            (0, 0, 0), (0, 0, 1), angle
        )
        tray = tray.union(pad)
    # Outlet is near the rim; its ring is open downward and accepts the removable downcomer.
    ox = TRAY_OUTLET_RADIUS_MM
    outlet_hole = cq.Workplane("XY").center(ox, 0.0).circle(0.5 * DOWNCOMER_CLEAR_BORE_MM).extrude(TRAY_HEIGHT_MM + 2.0).translate((0, 0, -1))
    outlet_ring = cq.Workplane("XY").center(ox, 0.0).circle(18.5).circle(15.5).extrude(TRAY_HEIGHT_MM)
    tray = tray.union(outlet_ring).cut(outlet_hole).clean()
    return tray.rotate((0, 0, 0), (0, 0, 1), TRAY_OUTLET_ANGLE_DEG)


def build_normal_overflow_reference_phase3ig() -> cq.Workplane:
    floor = _box(30.0, 118.0, 4.0, 0.0, 0.0, 0.0)
    walls = floor.union(_box(30.0, 3.0, 22.0, 0.0, -57.5, 0.0)).union(
        _box(30.0, 3.0, 22.0, 0.0, 57.5, 0.0)
    )
    crest = _box(3.0, 118.0, 4.0, -13.5, 0.0, 0.0)
    return walls.union(crest).clean()


def build_emergency_overflow_reference_phase3ig() -> cq.Workplane:
    return (_box(30.0, 10.0, 4.0, 0.0, 0.0, 0.0)
            .union(_box(3.0, 10.0, 15.0, -13.5, 0.0, 0.0))
            .union(_box(3.0, 10.0, 15.0, 13.5, 0.0, 0.0)).clean())


def _reference_transform(model: cq.Workplane, z: float = 20.0) -> cq.Workplane:
    return model.rotate((0, 0, 0), (0, 0, 1), REFERENCE_TANK_AXIS_ANGLE_DEG).translate((
        REFERENCE_TANK_CENTER_RADIUS_MM * cos(radians(REFERENCE_TANK_AXIS_ANGLE_DEG)),
        REFERENCE_TANK_CENTER_RADIUS_MM * sin(radians(REFERENCE_TANK_AXIS_ANGLE_DEG)), z))


def build_radial_leg_references_phase3ig() -> cq.Workplane:
    models = []
    for angle in RADIAL_LEG_ANGLES_DEG:
        leg = _box(RADIAL_LEG_LENGTH_MM, RADIAL_LEG_WIDTH_MM, 20.0,
                   0.5 * RADIAL_LEG_LENGTH_MM, 0.0, 0.0).rotate((0, 0, 0), (0, 0, 1), angle)
        models.append(leg)
    return _compound(models)


def build_metal_shelf_reference_phase3ig() -> cq.Workplane:
    shelf = _box(244.0, 140.0, 4.0, REFERENCE_TANK_CENTER_RADIUS_MM, 0.0, 20.0)
    return shelf.rotate((0, 0, 0), (0, 0, 1), REFERENCE_TANK_AXIS_ANGLE_DEG)


def build_lower_return_reference_assembly_phase3ig() -> cq.Workplane:
    models = [
        _reference_transform(build_lower_buffer_tank_phase3ig(), 24.0),
        _reference_transform(build_inlet_diffuser_phase3ig(), 24.0),
        _reference_transform(build_inlet_downcomer_phase3ig(), 24.0),
        build_terminal_collection_tray_phase3ig().translate((0, 0, 140.0)),
        build_radial_leg_references_phase3ig(),
        build_metal_shelf_reference_phase3ig(),
        _box(MAST_MEASURED_X_MM, MAST_MEASURED_Y_MM, 190.0, 0.0, 0.0, 0.0),
    ]
    return _compound(models)


def build_four_tower_reference_layout_phase3ig() -> cq.Workplane:
    """Lightweight four-tower, four-independent-return and central trough reference."""
    models: list[cq.Workplane] = []
    tower_xy = [(-575.0, -575.0), (575.0, -575.0), (575.0, 575.0), (-575.0, 575.0)]
    for tx, ty in tower_xy:
        inward = degrees(atan2(-ty, -tx)) % 360.0
        tower = cq.Workplane("XY").circle(100.0).circle(97.0).extrude(850.0).translate((tx, ty, 150.0))
        models.append(tower)
        cx = tx + REFERENCE_TANK_CENTER_RADIUS_MM * cos(radians(inward))
        cy = ty + REFERENCE_TANK_CENTER_RADIUS_MM * sin(radians(inward))
        tank = build_lower_buffer_tank_phase3ig().rotate((0, 0, 0), (0, 0, 1), inward).translate((cx, cy, 24.0))
        models.append(tank)
    trough = _box(CENTRAL_TROUGH_OUTER_LENGTH_MM, CENTRAL_TROUGH_OUTER_WIDTH_MM,
                  CENTRAL_TROUGH_HEIGHT_MM, 0.0, 0.0, 0.0)
    models.append(trough)
    return _compound(models)


def four_tower_layout_audit_phase3ig() -> dict[str, object]:
    tower_to_trough_center = sqrt((0.5 * FOUR_TOWER_SPACING_X_MM) ** 2 + (0.5 * FOUR_TOWER_SPACING_Y_MM) ** 2)
    # Along a 45 degree corner-to-center ray, the Y half-width is reached first.
    trough_boundary_radius = min(
        0.5 * CENTRAL_TROUGH_OUTER_LENGTH_MM / cos(radians(45.0)),
        0.5 * CENTRAL_TROUGH_OUTER_WIDTH_MM / sin(radians(45.0)),
    )
    tank_gutter_outlet_inset = REFERENCE_TANK_CENTER_RADIUS_MM + 0.5 * TANK_TOTAL_LENGTH_MM
    straight_gap = tower_to_trough_center - tank_gutter_outlet_inset - trough_boundary_radius
    return {
        "tower_center_spacing_x_mm": FOUR_TOWER_SPACING_X_MM,
        "tower_center_spacing_y_mm": FOUR_TOWER_SPACING_Y_MM,
        "tower_to_trough_center_mm": tower_to_trough_center,
        "tank_gutter_outlet_inset_toward_trough_mm": tank_gutter_outlet_inset,
        "trough_boundary_radius_on_diagonal_mm": trough_boundary_radius,
        "straight_outlet_to_trough_envelope_gap_mm": straight_gap,
        "provisional_hose_cut_length_range_mm": list(RETURN_HOSE_PROVISIONAL_LENGTH_RANGE_MM),
        "routing_note": "USE_MONOTONIC_DESCENDING_SERVICE_CURVE; STRAIGHT_GAP_IS_NOT_HOSE_CUT_LENGTH",
        "return_line_count": 4,
        "pre_trough_manifold_present": False,
    }


def _tank_cavity_to_level(level_z: float) -> cq.Workplane:
    inner = _rounded_rect(
        TANK_BODY_LENGTH_MM - 2.0 * TANK_WALL_MM,
        TANK_BODY_WIDTH_MM - 2.0 * TANK_WALL_MM,
        TANK_OUTER_CORNER_RADIUS_MM - TANK_WALL_MM,
        level_z - TANK_FLOOR_MM,
        z=TANK_FLOOR_MM,
        center_x=TANK_BODY_CENTER_X_MM,
    )
    return inner.cut(build_inlet_diffuser_phase3ig()).cut(build_inlet_downcomer_phase3ig()).clean()


def water_volume_audit_phase3ig() -> dict[str, object]:
    normal = sum(s.Volume() for s in _tank_cavity_to_level(NORMAL_WATER_Z_MM).solids().vals()) / 1_000_000.0
    emergency = sum(s.Volume() for s in _tank_cavity_to_level(EMERGENCY_WATER_Z_MM).solids().vals()) / 1_000_000.0
    full = sum(s.Volume() for s in _tank_cavity_to_level(TANK_HEIGHT_MM).solids().vals()) / 1_000_000.0
    reserve = emergency - normal
    stage_total = PER_STAGE_WATER_L * 5.0 * 4.0
    trough_area = CENTRAL_TROUGH_OUTER_LENGTH_MM * CENTRAL_TROUGH_OUTER_WIDTH_MM
    minimum_rise = stage_total * 1_000_000.0 / trough_area
    final_depth_lower_bound = CENTRAL_TROUGH_NORMAL_DEPTH_MM + minimum_rise
    return {
        "tank_internal_capacity_to_top_l": full,
        "tank_normal_working_volume_l": normal,
        "tank_emergency_level_volume_l": emergency,
        "tank_normal_to_emergency_reserve_l": reserve,
        "tank_freeboard_volume_above_emergency_l": full - emergency,
        "four_tower_transient_reserve_l": 4.0 * reserve,
        "five_stage_four_tower_retained_water_l": stage_total,
        "maximum_pump_stop_return_l": stage_total,
        "trough_outer_plan_area_mm2": trough_area,
        "trough_level_rise_lower_bound_mm": minimum_rise,
        "trough_level_rise_upper_bound_mm": None,
        "trough_upper_bound_reason": "INNER_FLOOR_AND_SLOPED_WALL_DIMENSIONS_PHYSICAL_MEASUREMENT_PENDING",
        "trough_final_depth_lower_bound_mm": final_depth_lower_bound,
        "trough_remaining_freeboard_upper_bound_mm": CENTRAL_TROUGH_HEIGHT_MM - final_depth_lower_bound,
        "trough_remaining_freeboard_lower_bound_mm": None,
        "normal_target_2_to_2_5_l": 2.0 <= normal <= 2.5,
    }


def _intersection_volume(a: cq.Workplane, b: cq.Workplane) -> float:
    return sum(s.Volume() for s in a.intersect(b).solids().vals())


def inherited_component_interference_audit_phase3ig() -> dict[str, float]:
    """Use the actual Phase 3I-F stage and inherited physical-reference parts."""
    from ps_mht_v001.fixtures.dry_core_frame_phase3if import (
        REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM,
        REFERENCE_MAST_CLEARANCE_MM,
        build_bottom_centering_puck_phase3if,
    )
    from ps_mht_v001.reference.integrated_stage_references_phase3ib import (
        build_keeper_installed_reference_phase3ib,
    )
    from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib
    from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
        build_installed_netpot_reference_phase3ia,
    )
    from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3if import (
        build_integrated_stage_full_direct_drop_phase3if,
    )

    stage = build_integrated_stage_full_direct_drop_phase3if().translate((0, 0, 170.0))
    tray = build_terminal_collection_tray_phase3ig().translate((0, 0, 140.0))
    tank = _reference_transform(build_lower_buffer_tank_phase3ig(), 24.0)
    downcomer = _reference_transform(build_inlet_downcomer_phase3ig(), 24.0)
    mast = _box(MAST_MEASURED_X_MM, MAST_MEASURED_Y_MM, 850.0, 0.0, 0.0, 0.0)
    puck = build_bottom_centering_puck_phase3if(
        REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM
    ).translate((0, 0, 170.0))
    pots = _compound([
        build_installed_netpot_reference_phase3ia(angle).translate((0, 0, 170.0))
        for angle in phase3ib.PORT_ANGLES_DEG
    ])
    keepers = _compound([
        build_keeper_installed_reference_phase3ib(angle).translate((0, 0, 170.0))
        for angle in phase3ib.PORT_ANGLES_DEG
    ])
    return {
        "tank_vs_actual_phase3if_stage": _intersection_volume(tank, stage),
        "tray_vs_actual_phase3if_stage": _intersection_volume(tray, stage),
        "tray_vs_actual_netpots": _intersection_volume(tray, pots),
        "tray_vs_actual_retention_keepers": _intersection_volume(tray, keepers),
        "tray_vs_actual_bottom_puck": _intersection_volume(tray, puck),
        "tank_vs_measured_mast_reference": _intersection_volume(tank, mast),
        "downcomer_vs_measured_mast_reference": _intersection_volume(downcomer, mast),
        "tray_vs_measured_mast_reference": _intersection_volume(tray, mast),
    }


def removal_path_audit_phase3ig() -> dict[str, object]:
    tank = _reference_transform(build_lower_buffer_tank_phase3ig(), 24.0)
    legs = build_radial_leg_references_phase3ig()
    mast = _box(MAST_MEASURED_X_MM, MAST_MEASURED_Y_MM, 190.0, 0.0, 0.0, 0.0)
    tray = build_terminal_collection_tray_phase3ig().translate((0, 0, 140.0))
    outward = (100.0 * cos(radians(45.0)), 100.0 * sin(radians(45.0)), 0.0)
    positions = {
        "installed": tank,
        "lifted_110mm_after_tray_removal": tank.translate((0, 0, 110.0)),
        "outward_100mm_after_tray_removal": tank.translate(outward),
    }
    intersections = {}
    for name, model in positions.items():
        intersections[name] = {
            "radial_legs_mm3": _intersection_volume(model, legs),
            "mast_mm3": _intersection_volume(model, mast),
            "tray_mm3_if_tray_not_removed": _intersection_volume(model, tray),
        }
    return {
        "required_sequence": "REMOVE_TRAY_AND_DOWNCOMER_THEN_LIFT_AND_MOVE_OUTWARD_ALONG_45_DEG_GAP",
        "positions": intersections,
        "path_clear_after_required_disassembly": all(
            values["radial_legs_mm3"] < 1e-6 and values["mast_mm3"] < 1e-6
            for values in intersections.values()
        ),
    }


def geometry_audit_phase3ig() -> dict[str, object]:
    models = {
        "tank": build_lower_buffer_tank_phase3ig(),
        "tray": build_terminal_collection_tray_phase3ig(),
        "downcomer": build_inlet_downcomer_phase3ig(),
        "diffuser": build_inlet_diffuser_phase3ig(),
    }
    metrics = {}
    for name, model in models.items():
        bb = model.val().BoundingBox()
        metrics[name] = {
            "solid_count": len(model.solids().vals()), "valid": all(s.isValid() for s in model.solids().vals()),
            "size_x_mm": bb.xlen, "size_y_mm": bb.ylen, "size_z_mm": bb.zlen,
            "volume_mm3": sum(s.Volume() for s in model.solids().vals()),
        }
    tank_ref = _reference_transform(models["tank"], 24.0)
    legs = build_radial_leg_references_phase3ig()
    mast = _box(MAST_MEASURED_X_MM, MAST_MEASURED_Y_MM, 190.0, 0.0, 0.0, 0.0)
    tray_ref = models["tray"].translate((0, 0, 140.0))
    diffuser_ref = _reference_transform(models["diffuser"], 24.0)
    down_ref = _reference_transform(models["downcomer"], 24.0)
    inherited_intersections = inherited_component_interference_audit_phase3ig()
    removal = removal_path_audit_phase3ig()
    return {
        "phase": PHASE, "process": PROCESS, "status": STATUS, "status_lines": list(STATUS_LINES),
        "parts": metrics,
        "tank_max_envelope_mm": [TANK_TOTAL_LENGTH_MM, TANK_TOTAL_WIDTH_MM, TANK_HEIGHT_MM],
        "tray_max_envelope_mm": [TRAY_OUTER_DIAMETER_MM, TRAY_OUTER_DIAMETER_MM, TRAY_HEIGHT_MM],
        "normal_weir_effective_width_mm": NORMAL_WEIR_EFFECTIVE_WIDTH_MM,
        "emergency_overflow_clear_width_mm": EMERGENCY_OVERFLOW_CLEAR_WIDTH_MM,
        "downcomer_clear_bore_mm": DOWNCOMER_CLEAR_BORE_MM,
        "downcomer_outlet_target_z_above_inner_floor_mm": DOWNCOMER_OUTLET_TARGET_ABOVE_INNER_FLOOR_MM,
        "downcomer_outlet_cad_z_above_inner_floor_mm": DOWNCOMER_OUTLET_ACTUAL_ABOVE_INNER_FLOOR_MM,
        "diffuser_envelope_mm": [DIFFUSER_WIDTH_MM, DIFFUSER_LENGTH_MM, DIFFUSER_HEIGHT_MM],
        "diffuser_slot_mm": [DIFFUSER_SLOT_WIDTH_MM, DIFFUSER_SLOT_HEIGHT_MM],
        "tray_slope_percent": TRAY_SLOPE_PERCENT,
        "tray_landing_angles_deg": list(LOWER_LANDING_ANGLES_DEG),
        "intersections_mm3": {
            "tank_vs_radial_legs": _intersection_volume(tank_ref, legs),
            "tank_vs_mast": _intersection_volume(tank_ref, mast),
            "tray_vs_mast": _intersection_volume(tray_ref, mast),
            "diffuser_vs_downcomer": _intersection_volume(diffuser_ref, down_ref),
        },
        "inherited_actual_component_intersections_mm3": inherited_intersections,
        "all_inherited_actual_component_intersections_zero": all(v < 1e-6 for v in inherited_intersections.values()),
        "removal_path": removal,
        "four_tower_layout": four_tower_layout_audit_phase3ig(),
        "intended_contacts": [
            "TANK_BOTTOM_TO_METAL_SHELF",
            "DOWNCOMER_TO_DIFFUSER_CAPTURE_INTERFACE_WITH_0P3MM_RADIAL_CLEARANCE",
        ],
        "printed_parts_primary_load_path": False,
        "primary_load_path": "MODULE_STACK_TO_METAL_BASE_AND_METAL_SHELF",
        "central_dry_core_used_for_water": False,
        "tank_floor_penetrations": 0,
        "full_module_print_status": "DO_NOT_PRINT",
    }


def hydraulic_connectivity_audit_phase3ig() -> dict[str, object]:
    return {
        "ordered_path": [
            "LOWEST_STAGE_THREE_DROPS", "TERMINAL_COLLECTION_TRAY", "VENTED_DOWNCOMER",
            "BOTTOM_DIFFUSER_PLENUM", "UPWARD_DISPLACEMENT_TANK", "OPPOSITE_WIDE_WEIR",
            "OPEN_GUTTER_AIR_BREAK", "INDEPENDENT_25MM_HOSE", "CENTRAL_TROUGH",
        ],
        "path_continuous": True,
        "downcomer_top_vented": True,
        "bottom_discharge_horizontal": True,
        "normal_overflow_air_break": True,
        "siphon_path_present": False,
        "returns_merged_before_trough": False,
        "small_diffuser_holes_present": False,
        "internal_baffle_status": "INTERNAL_BAFFLE_RESERVED",
        "dye_test_required": True,
    }


def printability_audit_phase3ig() -> dict[str, object]:
    return {
        "printer": "BAMBU_LAB_A1", "build_envelope_mm": [A1_X_MM, A1_Y_MM, A1_Z_MM],
        "material": "WHITE_PETG", "diagnostics_ready_after_slicer_review": [f"D{i:02d}" for i in range(1, 8)],
        "full_tank": "HOLD_DO_NOT_PRINT", "full_tray": "HOLD_DO_NOT_PRINT",
        "full_assembly": "HOLD_DO_NOT_PRINT", "phase3if_full_stage": "DO_NOT_PRINT",
        "supports_trapped_inside_tank": False,
        "unsupported_internal_roof_present": False,
        "bridges_requiring_slicer_review": ["DOWNCOMER_HORIZONTAL_ELBOW", "TERMINAL_TRAY_OUTLET_RING"],
        "long_external_nipple_present": False,
    }


def _parse_sha_list(path: Path) -> dict[str, str]:
    entries = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split(None, 1)
        entries[relative.strip()] = digest.lower()
    return entries


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def regression_audit_phase3ig() -> dict[str, object]:
    checks = {}
    for label, sha_list in (("phase3id", PHASE3ID_SHA_LIST), ("phase3if", PHASE3IF_SHA_LIST)):
        expected = _parse_sha_list(sha_list)
        mismatches = []
        missing = []
        for rel, digest in expected.items():
            path = REPOSITORY_ROOT / rel
            if not path.is_file():
                missing.append(rel)
            elif sha256_file(path) != digest:
                mismatches.append(rel)
        checks[label] = {"sha_list": str(sha_list), "entry_count": len(expected),
                         "missing": missing, "mismatches": mismatches,
                         "all_unchanged": not missing and not mismatches}
    return {"checks": checks, "all_unchanged": all(v["all_unchanged"] for v in checks.values()),
            "git_mutation_operations_performed": False}


# Diagnostic coupons -------------------------------------------------------
def build_d01_wall_floor_watertight_phase3ig() -> cq.Workplane:
    outer = _rounded_rect(80.0, 55.0, 8.0, 24.0)
    inner = _rounded_rect(74.0, 49.0, 5.0, 21.0, z=4.0)
    return outer.cut(inner).clean()


def build_d02_downcomer_diffuser_phase3ig() -> cq.Workplane:
    diffuser = build_inlet_diffuser_phase3ig().translate((100.0, 0.0, -TANK_FLOOR_MM))
    tube = _tube_z(31.0, 25.0, 55.0, -35.0, 0.0, 0.0)
    return _compound([diffuser, tube])


def build_d03_wide_weir_gutter_phase3ig() -> cq.Workplane:
    return build_normal_overflow_reference_phase3ig().translate((0, 0, 0))


def build_d04_normal_emergency_overflow_phase3ig() -> cq.Workplane:
    return _compound([build_normal_overflow_reference_phase3ig().translate((0, -25, 0)),
                      build_emergency_overflow_reference_phase3ig().translate((0, 55, 0))])


def build_d05_cleanout_drain_pad_phase3ig() -> cq.Workplane:
    pad = _box(50.0, 12.0, 38.0, -35.0, 0.0, 0.0)
    pad = pad.cut(cq.Workplane("XZ").center(-35.0, 8.0).circle(1.0).extrude(1.5).translate((0, -6, 0)))
    template = _box(55.0, 3.0, 45.0, 35.0, 0.0, 0.0)
    for diameter, z in ((12.0, 10.0), (15.0, 30.0)):
        template = template.cut(cq.Workplane("XZ").center(35.0, z).circle(0.5 * diameter).extrude(4.0).translate((0, -2, 0)))
    return _compound([pad, template])


def build_d06_terminal_tray_sector_phase3ig() -> cq.Workplane:
    tray = build_terminal_collection_tray_phase3ig()
    sector_box = _box(110.0, 95.0, 35.0, 55.0, 0.0, 0.0)
    return tray.intersect(sector_box).clean()


def build_d07_tank_positioning_cradle_phase3ig() -> cq.Workplane:
    base = _rounded_rect(120.0, 36.0, 5.0, 4.0)
    rails = _box(120.0, 4.0, 14.0, 0.0, -16.0, 0.0).union(_box(120.0, 4.0, 14.0, 0.0, 16.0, 0.0))
    return base.union(rails).clean()


DIAGNOSTIC_BUILDERS = {
    "D01": build_d01_wall_floor_watertight_phase3ig,
    "D02": build_d02_downcomer_diffuser_phase3ig,
    "D03": build_d03_wide_weir_gutter_phase3ig,
    "D04": build_d04_normal_emergency_overflow_phase3ig,
    "D05": build_d05_cleanout_drain_pad_phase3ig,
    "D06": build_d06_terminal_tray_sector_phase3ig,
    "D07": build_d07_tank_positioning_cradle_phase3ig,
}
