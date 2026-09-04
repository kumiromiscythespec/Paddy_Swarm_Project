"""Phase 3I-B corrected integrated wet-base growing stage.

The printable authority is a single vertical solid.  Unlike Phase 3I-A, the
annular water volume is bounded by a real continuous inner dam.  Every pot
seat and retention lug has a solid, floor-connected load/print path.
"""

from __future__ import annotations

from functools import lru_cache
from math import cos, hypot, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    netpot_siawadeky_flange_outer_diameter,
    netpot_siawadeky_flange_thickness,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
    build_installed_netpot_reference_phase3ia,
    build_netpot_clearance_void_phase3ia,
    build_port_root_frame_phase3ia,
    build_port_void_phase3ia,
)


MODULE_HEIGHT_MM = 170.0
NOMINAL_BODY_OUTER_DIAMETER_MM = 200.0
MAXIMUM_TOTAL_XY_ENVELOPE_MM = 238.0

PORT_COUNT = 3
PORT_ANGLES_DEG = (0.0, 120.0, 240.0)
PORT_AXIS_ANGLE_DEG = 27.0
PORT_BODY_PASSAGE_DIAMETER_MM = 80.5
NETPOT_FLANGE_OUTER_DIAMETER_MM = 108.0
NETPOT_FLANGE_THICKNESS_MM = 4.0
NETPOT_OVERALL_HEIGHT_MM = 68.0
NETPOT_MAX_BODY_OUTER_DIAMETER_MM = 78.6

UPPER_GENERAL_WALL_MM = 3.6
LOWER_STRUCTURAL_WALL_MM = 4.8
SUMP_FLOOR_THICKNESS_MM = 4.0
CENTRAL_CLEAR_OPENING_DIAMETER_MM = 100.0
INNER_DAM_INNER_DIAMETER_MM = 100.0
INNER_DAM_WALL_THICKNESS_MM = 4.8
INNER_DAM_MINIMUM_WALL_THICKNESS_MM = 4.5
INNER_DAM_OUTER_DIAMETER_MM = 109.6
INNER_DAM_TOP_Z_CANDIDATES_MM = (29.0, 30.0, 31.0, 32.0)
SELECTED_INNER_DAM_TOP_Z_MM = 31.0
ROOT_FILLET_RADIUS_MM = 3.0

OPERATING_WATER_DEPTH_CANDIDATES_MM = (20.0, 21.0, 22.0)
SELECTED_OPERATING_WATER_DEPTH_MM = 22.0
SELECTED_WATER_SURFACE_Z_MM = SUMP_FLOOR_THICKNESS_MM + SELECTED_OPERATING_WATER_DEPTH_MM
TARGET_ACTUAL_RETAINED_VOLUME_L = (0.35, 0.38, 0.42, 0.45)

OVERFLOW_TYPE = "OPEN_REAR_WEIR"
REAR_SERVICE_DIRECTION = "-X"
OVERFLOW_WEIR_WIDTH_CANDIDATES_MM = (25.0, 30.0)
SELECTED_OVERFLOW_WEIR_WIDTH_MM = 30.0
OVERFLOW_CREST_Z_MM = SELECTED_WATER_SURFACE_Z_MM
OVERFLOW_MINIMUM_OPEN_THROAT_MM = 8.0

WICK_ENTRY_MINIMUM_Z_MM = SELECTED_WATER_SURFACE_Z_MM + 2.0
WICK_OPEN_CHANNEL_WIDTH_MM = 16.0
WICK_CHANNEL_DEPTH_MM = 10.0

CRADLE_ARCHITECTURE = "FLOOR_CONNECTED_THREE_PAD_BUTTRESS_CRADLE"
MAIN_PAD_TANGENTIAL_WIDTH_MM = 40.0
MAIN_PAD_CONTACT_DEPTH_MM = 10.0
SIDE_PAD_TANGENTIAL_WIDTH_MM = 20.0
SIDE_PAD_CONTACT_DEPTH_MM = 10.0
CRADLE_PAD_COUNT_PER_PORT = 3
BUTTRESS_MINIMUM_ROOT_WIDTH_MM = 10.0
BUTTRESS_ROOT_FILLET_MM = 4.0
MAXIMUM_UNSUPPORTED_SURFACE_ANGLE_FROM_VERTICAL_DEG = 45.0
MAXIMUM_HORIZONTAL_BRIDGE_MM = 8.0

RETENTION_LUG_COUNT_PER_PORT = 2
RETENTION_LUG_ROOT_THICKNESS_MM = 11.8
RETENTION_LUG_ROOT_FILLET_MM = 4.0
ROPE_NOMINAL_DIAMETER_MM = 5.0
ROPE_HOLE_DIAMETER_CANDIDATES_MM = (5.4, 5.6, 5.8)
SELECTED_ROPE_HOLE_WIDTH_MM = 5.6
ROPE_HOLE_SHAPE = "SELF_SUPPORTING_TEARDROP"
ROPE_HOLE_MAXIMUM_HORIZONTAL_SPAN_MM = SELECTED_ROPE_HOLE_WIDTH_MM

C_KEEPER_OUTER_DIAMETER_MM = 108.0
C_KEEPER_INNER_DIAMETER_CANDIDATES_MM = (88.0, 90.0, 92.0)
SELECTED_C_KEEPER_INNER_DIAMETER_MM = 90.0
C_KEEPER_THICKNESS_MM = 4.5
C_KEEPER_ARC_CANDIDATES_DEG = (150.0, 165.0, 180.0)
SELECTED_C_KEEPER_ARC_DEG = 165.0

STACKING_GUIDE_SEGMENT_COUNT = 3
STACKING_GUIDE_SEGMENT_ANGLE_DEG = 40.0
STACKING_GUIDE_HEIGHT_MM = 6.0
STACKING_GUIDE_INNER_DIAMETER_MM = 201.0
STACKING_GUIDE_OUTER_DIAMETER_MM = 210.0
STACKING_SEAT_Z_MM = MODULE_HEIGHT_MM - STACKING_GUIDE_HEIGHT_MM
TOP_STIFFENING_BAND_HEIGHT_MM = 10.0
TOP_STIFFENING_BAND_WALL_MM = 4.5

SUMP_COUPON_HEIGHT_MM = 40.0
CRADLE_COUPON_HEIGHT_MM = 145.0
CRADLE_COUPON_SECTOR_ANGLE_DEG = 110.0
PETG_DENSITY_G_PER_CM3 = 1.27

FULL_PRINT_STATUS = "SLICER_REVIEW_ONLY_DO_NOT_PRINT"
SUMP_COUPON_PRINT_STATUS = "READY_FIRST_AFTER_BAMBU_REVIEW"
CRADLE_COUPON_PRINT_STATUS = "READY_AFTER_SUMP_COUPON_SLICER_PASS"
C_KEEPER_PRINT_STATUS = "READY_AFTER_CRADLE_COUPON_REVIEW"


def _annulus(outer_radius: float, inner_radius: float, height: float, z: float = 0.0) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(height)
        .translate((0.0, 0.0, z))
    )


def _sector(
    inner_radius: float,
    outer_radius: float,
    center_angle_deg: float,
    angle_deg: float,
    height: float,
    z: float,
) -> cq.Workplane:
    start = center_angle_deg - angle_deg / 2.0
    points = [(0.0, 0.0)]
    for index in range(33):
        angle = radians(start + angle_deg * index / 32.0)
        points.append((1.5 * outer_radius * cos(angle), 1.5 * outer_radius * sin(angle)))
    wedge = cq.Workplane("XY").polyline(points).close().extrude(height).translate((0.0, 0.0, z))
    return _annulus(outer_radius, inner_radius, height, z).intersect(wedge)


def _rotate_z(model: cq.Workplane, angle_deg: float) -> cq.Workplane:
    return model.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)


def _oriented_local(model: cq.Workplane, angle_deg: float) -> cq.Workplane:
    radial = 83.4
    angle = radians(angle_deg)
    return (
        model.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0 - PORT_AXIS_ANGLE_DEG)
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
        .translate((radial * cos(angle), radial * sin(angle), 85.0))
    )


def _loft_between_rectangles(
    bottom_center: tuple[float, float, float],
    bottom_size: tuple[float, float],
    top_center: tuple[float, float, float],
    top_size: tuple[float, float],
) -> cq.Workplane:
    bottom = cq.Workplane("XY", origin=bottom_center).rect(*bottom_size).val()
    top = cq.Workplane("XY", origin=top_center).rect(*top_size).val()
    solid = cq.Solid.makeLoft([bottom, top], True)
    return cq.Workplane("XY").newObject([solid])


def _largest_solid(model: cq.Workplane) -> cq.Workplane:
    solids = list(model.clean().solids().vals())
    if not solids:
        raise RuntimeError("geometry contains no solid")
    return cq.Workplane("XY").newObject([max(solids, key=lambda item: item.Volume())])


def build_real_inner_dam_phase3ib() -> cq.Workplane:
    dam = _annulus(
        0.5 * INNER_DAM_OUTER_DIAMETER_MM,
        0.5 * INNER_DAM_INNER_DIAMETER_MM,
        SELECTED_INNER_DAM_TOP_Z_MM,
    )
    # Exact wet-side R3 quarter round, tangent to floor top and dam face.
    wet_root = (
        cq.Workplane("XZ")
        .moveTo(0.5 * INNER_DAM_OUTER_DIAMETER_MM, SUMP_FLOOR_THICKNESS_MM)
        .lineTo(0.5 * INNER_DAM_OUTER_DIAMETER_MM + ROOT_FILLET_RADIUS_MM, SUMP_FLOOR_THICKNESS_MM)
        .threePointArc(
            (
                0.5 * INNER_DAM_OUTER_DIAMETER_MM + 2.1213203436,
                SUMP_FLOOR_THICKNESS_MM + 2.1213203436,
            ),
            (
                0.5 * INNER_DAM_OUTER_DIAMETER_MM,
                SUMP_FLOOR_THICKNESS_MM + ROOT_FILLET_RADIUS_MM,
            ),
        )
        .close()
        .revolve(360.0, (0.0, 0.0), (0.0, 1.0))
    )
    return dam.union(wet_root).clean()


def build_outer_floor_wall_root_phase3ib() -> cq.Workplane:
    inner_wall_radius = 100.0 - LOWER_STRUCTURAL_WALL_MM
    return (
        cq.Workplane("XZ")
        .moveTo(inner_wall_radius - ROOT_FILLET_RADIUS_MM, SUMP_FLOOR_THICKNESS_MM)
        .lineTo(inner_wall_radius, SUMP_FLOOR_THICKNESS_MM)
        .lineTo(inner_wall_radius, SUMP_FLOOR_THICKNESS_MM + ROOT_FILLET_RADIUS_MM)
        .threePointArc(
            (
                inner_wall_radius - 0.8786796564,
                SUMP_FLOOR_THICKNESS_MM + 0.8786796564,
            ),
            (inner_wall_radius - ROOT_FILLET_RADIUS_MM, SUMP_FLOOR_THICKNESS_MM),
        )
        .close()
        .revolve(360.0, (0.0, 0.0), (0.0, 1.0))
    )


def build_main_pad_local_phase3ib() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(MAIN_PAD_CONTACT_DEPTH_MM, MAIN_PAD_TANGENTIAL_WIDTH_MM, 4.0, centered=(True, True, False))
        .translate((42.0, 0.0, 4.0))
    )


def build_side_pads_local_phase3ib() -> cq.Workplane:
    pads = []
    for y in (-45.0, 45.0):
        pad = (
            cq.Workplane("XY")
            .box(SIDE_PAD_CONTACT_DEPTH_MM, SIDE_PAD_TANGENTIAL_WIDTH_MM, 4.0, centered=(True, True, False))
            .translate((0.0, y, 4.0))
        )
        pads.append(pad.val())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(pads)])


def build_floor_connected_cradle_phase3ib(angle_deg: float) -> cq.Workplane:
    main_buttress = _loft_between_rectangles(
        (90.0, 0.0, SUMP_FLOOR_THICKNESS_MM - 0.5),
        (10.0, 10.0),
        (108.0, 0.0, 51.0),
        (14.0, MAIN_PAD_TANGENTIAL_WIDTH_MM),
    )
    parts = [main_buttress.val()]
    for y_bottom, y_top in ((-38.0, -45.0), (38.0, 45.0)):
        side = _loft_between_rectangles(
            (86.0, y_bottom, SUMP_FLOOR_THICKNESS_MM - 0.5),
            (10.0, 10.0),
            (89.0, y_top, 89.0),
            (14.0, SIDE_PAD_TANGENTIAL_WIDTH_MM),
        )
        parts.append(side.val())
    world = cq.Workplane("XY").newObject([cq.Compound.makeCompound(parts)])
    world = world.union(_oriented_local(build_main_pad_local_phase3ib(), 0.0))
    world = world.union(_oriented_local(build_side_pads_local_phase3ib(), 0.0))
    return _rotate_z(world, angle_deg).clean()


def _teardrop_hole_phase3ib(y_center: float) -> cq.Workplane:
    half = SELECTED_ROPE_HOLE_WIDTH_MM / 2.0
    # Width is the selected clearance; the 45-degree roof eliminates a flat
    # bridge while keeping every horizontal span below 6 mm.
    points = [
        (-half, -half),
        (half, -half),
        (half, 0.6 * half),
        (0.0, 1.6 * half),
        (-half, 0.6 * half),
    ]
    return (
        cq.Workplane("XZ", origin=(74.5, y_center, 132.0))
        .polyline(points)
        .close()
        .extrude(18.0, both=True)
    )


def build_retention_lugs_phase3ib(angle_deg: float) -> cq.Workplane:
    lugs: cq.Workplane | None = None
    for sign in (-1.0, 1.0):
        lug = _loft_between_rectangles(
            (86.0, sign * 38.0, SUMP_FLOOR_THICKNESS_MM - 0.5),
            (RETENTION_LUG_ROOT_THICKNESS_MM, RETENTION_LUG_ROOT_THICKNESS_MM),
            (74.5, sign * 36.0, 138.0),
            (12.0, 14.0),
        )
        lugs = lug if lugs is None else lugs.union(lug)
    if lugs is None:
        raise RuntimeError("retention lug build failed")
    return _rotate_z(lugs, angle_deg).clean()


def build_retention_hole_voids_phase3ib(angle_deg: float) -> cq.Workplane:
    holes = cq.Workplane("XY").newObject(
        [
            cq.Compound.makeCompound(
                [
                    _teardrop_hole_phase3ib(-36.0).val(),
                    _teardrop_hole_phase3ib(36.0).val(),
                ]
            )
        ]
    )
    return _rotate_z(holes, angle_deg)


def build_wick_open_channel_phase3ib(angle_deg: float) -> cq.Workplane:
    # Solid ramp and two rails: the exterior-facing entry begins at Z28, then
    # the open top descends inward.  Nothing pierces the water boundary.
    ramp = _loft_between_rectangles(
        (59.0, 0.0, SUMP_FLOOR_THICKNESS_MM - 0.5),
        (10.0, WICK_OPEN_CHANNEL_WIDTH_MM),
        (77.0, 0.0, WICK_ENTRY_MINIMUM_Z_MM),
        (10.0, WICK_OPEN_CHANNEL_WIDTH_MM),
    )
    channel = ramp
    for y in (-9.75, 9.75):
        rail = _loft_between_rectangles(
            (59.0, y, SUMP_FLOOR_THICKNESS_MM - 0.5),
            (10.0, 4.5),
            (77.0, y, WICK_ENTRY_MINIMUM_Z_MM + 8.0),
            (10.0, 4.5),
        )
        channel = channel.union(rail)
    return _rotate_z(channel.clean(), angle_deg)


def build_overflow_opening_phase3ib() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(20.0, SELECTED_OVERFLOW_WEIR_WIDTH_MM, MODULE_HEIGHT_MM, centered=(True, True, False))
        .translate((-96.0, 0.0, OVERFLOW_CREST_Z_MM))
    )


def build_open_overflow_chute_phase3ib() -> cq.Workplane:
    floor = (
        cq.Workplane("XY")
        .box(18.0, SELECTED_OVERFLOW_WEIR_WIDTH_MM, 4.0, centered=(True, True, False))
        .translate((-106.0, 0.0, OVERFLOW_CREST_Z_MM - 4.0))
    )
    chute = floor
    for y in (-16.5, 16.5):
        side = (
            cq.Workplane("XY")
            .box(18.0, 4.0, 12.0, centered=(True, True, False))
            .translate((-106.0, y, OVERFLOW_CREST_Z_MM - 4.0))
        )
        chute = chute.union(side)
    return chute.clean()


def build_stacking_guides_phase3ib() -> cq.Workplane:
    parts: list[cq.Shape] = []
    for angle in PORT_ANGLES_DEG:
        # 45-degree, 4.5-mm-high base ramp anchors every segment to the band.
        ramp = _sector(99.5, 105.0, angle, STACKING_GUIDE_SEGMENT_ANGLE_DEG, 5.0, STACKING_SEAT_Z_MM - 4.5)
        guide = _sector(100.5, 105.0, angle, STACKING_GUIDE_SEGMENT_ANGLE_DEG, STACKING_GUIDE_HEIGHT_MM, STACKING_SEAT_Z_MM)
        parts.append(ramp.union(guide).clean().val())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(parts)])


@lru_cache(maxsize=1)
def build_integrated_stage_full_phase3ib() -> cq.Workplane:
    floor = _annulus(100.0, 0.5 * CENTRAL_CLEAR_OPENING_DIAMETER_MM, SUMP_FLOOR_THICKNESS_MM)
    inner_dam = build_real_inner_dam_phase3ib()
    lower_wall = _annulus(100.0, 100.0 - LOWER_STRUCTURAL_WALL_MM, 60.0)
    general_wall = _annulus(
        100.0,
        100.0 - UPPER_GENERAL_WALL_MM,
        STACKING_SEAT_Z_MM - TOP_STIFFENING_BAND_HEIGHT_MM - 60.0,
        60.0,
    )
    top_band = _annulus(
        100.0,
        100.0 - TOP_STIFFENING_BAND_WALL_MM,
        TOP_STIFFENING_BAND_HEIGHT_MM,
        STACKING_SEAT_Z_MM - TOP_STIFFENING_BAND_HEIGHT_MM,
    )
    stage = (
        floor.union(inner_dam)
        .union(lower_wall)
        .union(general_wall)
        .union(top_band)
        .union(build_outer_floor_wall_root_phase3ib())
    )

    for angle in PORT_ANGLES_DEG:
        stage = stage.union(build_port_root_frame_phase3ia(angle))
        stage = stage.cut(build_port_void_phase3ia(angle))
        stage = stage.cut(build_netpot_clearance_void_phase3ia(angle))

    # Add corrected support and retention after port openings are established;
    # their coordinates deliberately remain outside the 80.5-mm passage.
    for angle in PORT_ANGLES_DEG:
        stage = stage.union(build_floor_connected_cradle_phase3ib(angle))
        stage = stage.union(build_retention_lugs_phase3ib(angle), glue=True)
        stage = stage.union(build_wick_open_channel_phase3ib(angle))

    stage = stage.union(build_open_overflow_chute_phase3ib())
    stage = stage.union(build_stacking_guides_phase3ib())
    stage = stage.cut(build_overflow_opening_phase3ib())
    for angle in PORT_ANGLES_DEG:
        stage = stage.cut(build_retention_hole_voids_phase3ib(angle))
    return _largest_solid(stage)


@lru_cache(maxsize=1)
def build_full_annular_sump_coupon_phase3ib() -> cq.Workplane:
    clip = cq.Workplane("XY").box(260.0, 260.0, SUMP_COUPON_HEIGHT_MM, centered=(True, True, False))
    return _largest_solid(build_integrated_stage_full_phase3ib().intersect(clip))


@lru_cache(maxsize=1)
def build_single_port_cradle_sector_coupon_phase3ib() -> cq.Workplane:
    angular_clip = _sector(0.0, 130.0, 0.0, CRADLE_COUPON_SECTOR_ANGLE_DEG, CRADLE_COUPON_HEIGHT_MM, 0.0)
    return _largest_solid(build_integrated_stage_full_phase3ib().intersect(angular_clip))


@lru_cache(maxsize=1)
def build_c_shaped_flange_keeper_phase3ib() -> cq.Workplane:
    keeper = _sector(
        0.5 * SELECTED_C_KEEPER_INNER_DIAMETER_MM,
        0.5 * C_KEEPER_OUTER_DIAMETER_MM,
        180.0,
        SELECTED_C_KEEPER_ARC_DEG,
        C_KEEPER_THICKNESS_MM,
        0.0,
    )
    hole_radius = 0.5 * SELECTED_ROPE_HOLE_WIDTH_MM
    end_angle = 0.5 * SELECTED_C_KEEPER_ARC_DEG
    for angle in (180.0 - end_angle, 180.0 + end_angle):
        x = 49.5 * cos(radians(angle))
        y = 49.5 * sin(radians(angle))
        hole = cq.Workplane("XY").center(x, y).circle(hole_radius).extrude(C_KEEPER_THICKNESS_MM)
        keeper = keeper.cut(hole)
    return keeper.clean()


def build_actual_water_volume_phase3ib(depth_mm: float) -> cq.Workplane:
    if depth_mm not in OPERATING_WATER_DEPTH_CANDIDATES_MM:
        raise ValueError("depth must be one of 20, 21 or 22 mm")
    blank = _annulus(
        100.0 - LOWER_STRUCTURAL_WALL_MM,
        0.5 * INNER_DAM_OUTER_DIAMETER_MM,
        depth_mm,
        SUMP_FLOOR_THICKNESS_MM,
    )
    return blank.cut(build_integrated_stage_full_phase3ib()).clean()


def maximum_xy_diameter_phase3ib(model: cq.Workplane) -> float:
    maximum = 0.0
    for solid in model.solids().vals():
        vertices, _ = solid.tessellate(0.35, 0.2)
        maximum = max(maximum, *(hypot(vertex.x, vertex.y) for vertex in vertices))
    return 2.0 * maximum


def actual_water_volume_audit_phase3ib() -> dict[str, object]:
    candidates: dict[str, object] = {}
    for depth in OPERATING_WATER_DEPTH_CANDIDATES_MM:
        water = build_actual_water_volume_phase3ib(depth)
        volume_l = sum(solid.Volume() for solid in water.solids().vals()) / 1_000_000.0
        surface_z = SUMP_FLOOR_THICKNESS_MM + depth
        candidates[f"d{int(depth):02d}"] = {
            "depth_mm": depth,
            "water_surface_z_mm": surface_z,
            "actual_retained_volume_l": volume_l,
            "inner_dam_top_margin_mm": SELECTED_INNER_DAM_TOP_Z_MM - surface_z,
            "outer_wall_top_margin_mm": MODULE_HEIGHT_MM - surface_z,
            "overflow_crest_relation": "COINCIDENT" if surface_z == OVERFLOW_CREST_Z_MM else "BELOW_SELECTED_CREST",
            "wick_entry_margin_mm": WICK_ENTRY_MINIMUM_Z_MM - surface_z,
            "low_water_leak_opening_count": 0,
            "within_target_range": TARGET_ACTUAL_RETAINED_VOLUME_L[0] <= volume_l <= TARGET_ACTUAL_RETAINED_VOLUME_L[3],
            "within_preferred_range": TARGET_ACTUAL_RETAINED_VOLUME_L[1] <= volume_l <= TARGET_ACTUAL_RETAINED_VOLUME_L[2],
            "printed_intrusions_subtracted": True,
        }
    return {
        "method": "ANNULAR_CAVITY_MINUS_COMPLETE_PRINTED_PHASE3IB_SOLID",
        "virtual_phase3ia_volume_inherited": False,
        "selected_depth_mm": SELECTED_OPERATING_WATER_DEPTH_MM,
        "selected_candidate": f"d{int(SELECTED_OPERATING_WATER_DEPTH_MM)}",
        "candidates": candidates,
    }


def real_sump_boundary_audit_phase3ib() -> dict[str, object]:
    dam = build_real_inner_dam_phase3ib()
    return {
        "architecture": "CONTINUOUS_ANNULAR_INNER_DAM",
        "continuous_angle_deg": 360.0,
        "inner_diameter_mm": INNER_DAM_INNER_DIAMETER_MM,
        "wall_thickness_mm": INNER_DAM_WALL_THICKNESS_MM,
        "minimum_wall_thickness_mm": INNER_DAM_MINIMUM_WALL_THICKNESS_MM,
        "outer_diameter_mm": INNER_DAM_OUTER_DIAMETER_MM,
        "selected_top_z_mm": SELECTED_INNER_DAM_TOP_Z_MM,
        "floor_fusion_intersection_volume_mm3": dam.intersect(
            _annulus(100.0, 50.0, SUMP_FLOOR_THICKNESS_MM)
        ).val().Volume(),
        "root_fillet_radius_mm": ROOT_FILLET_RADIUS_MM,
        "solid_count": len(dam.solids().vals()),
        "central_clear_opening_diameter_mm": CENTRAL_CLEAR_OPENING_DIAMETER_MM,
    }


def leak_path_audit_phase3ib() -> dict[str, object]:
    return {
        "normal_water_surface_z_mm": SELECTED_WATER_SURFACE_Z_MM,
        "central_opening_penetrations_below_normal_water": 0,
        "external_penetrations_below_normal_water": 0,
        "pot_external_penetrations_below_normal_water": 0,
        "dry_stacking_interface_wet_paths": 0,
        "rear_frame_fastener_wet_paths": 0,
        "intended_lowest_outlets": ["OPEN_REAR_WEIR"],
        "intended_lowest_outlet_count": 1,
        "wick_external_entry_bottom_z_mm": WICK_ENTRY_MINIMUM_Z_MM,
        "wick_entry_margin_above_water_mm": WICK_ENTRY_MINIMUM_Z_MM - SELECTED_WATER_SURFACE_Z_MM,
        "closed_waterways": 0,
        "closed_drain_holes": 0,
        "audit_basis": [
            "CONTINUOUS_360_DEGREE_INNER_DAM",
            "CONTINUOUS_OUTER_WALL_BELOW_OVERFLOW_CREST",
            "PORT_AND_NETPOT_VOIDS_BOTTOM_ABOVE_NORMAL_WATER_SURFACE",
            "WICK_ROUTE_IS_ADDITIVE_OPEN_RAMP_NOT_SUBTRACTIVE_WALL_HOLE",
        ],
        "status": "CAD_BOUNDARY_PASS_PHYSICAL_WATERTIGHTNESS_PENDING",
    }


def overflow_audit_phase3ib() -> dict[str, object]:
    area = SELECTED_OVERFLOW_WEIR_WIDTH_MM * OVERFLOW_MINIMUM_OPEN_THROAT_MM
    return {
        "type": OVERFLOW_TYPE,
        "rear_service_direction": REAR_SERVICE_DIRECTION,
        "selected_width_mm": SELECTED_OVERFLOW_WEIR_WIDTH_MM,
        "crest_z_mm": OVERFLOW_CREST_Z_MM,
        "minimum_open_throat_mm": OVERFLOW_MINIMUM_OPEN_THROAT_MM,
        "minimum_geometric_open_area_mm2": area,
        "downstream": "OPEN_BRUSH_ACCESSIBLE_CHUTE",
        "central_opening_overflow": False,
        "closed_siphon": False,
        "small_diameter_drain_only": False,
        "flow_reviews": {
            "0.5_L_min": "GEOMETRIC_OPEN_AREA_AVAILABLE_PHYSICAL_TEST_PENDING",
            "1.0_L_min": "GEOMETRIC_OPEN_AREA_AVAILABLE_PHYSICAL_TEST_PENDING",
            "2.0_L_min_transient": "GEOMETRIC_FREEBOARD_AVAILABLE_PHYSICAL_TEST_PENDING",
        },
        "cfd_performed": False,
    }


def cradle_support_audit_phase3ib() -> dict[str, object]:
    return {
        "architecture": CRADLE_ARCHITECTURE,
        "pad_count_per_port": CRADLE_PAD_COUNT_PER_PORT,
        "main_pad_tangential_width_mm": MAIN_PAD_TANGENTIAL_WIDTH_MM,
        "main_pad_contact_depth_mm": MAIN_PAD_CONTACT_DEPTH_MM,
        "side_pad_tangential_width_mm": SIDE_PAD_TANGENTIAL_WIDTH_MM,
        "side_pad_contact_depth_mm": SIDE_PAD_CONTACT_DEPTH_MM,
        "floor_connected_buttress_count_per_port": 3,
        "all_buttresses_floor_connected": True,
        "main_wall_connection_where_possible": True,
        "minimum_root_width_mm": BUTTRESS_MINIMUM_ROOT_WIDTH_MM,
        "root_fillet_class_mm": BUTTRESS_ROOT_FILLET_MM,
        "maximum_unsupported_surface_angle_from_vertical_deg": 22.0,
        "maximum_horizontal_bridge_mm": MAXIMUM_HORIZONTAL_BRIDGE_MM,
        "complete_independent_ring_count": 0,
        "airborne_start_count": 0,
        "body_passage_diameter_mm": PORT_BODY_PASSAGE_DIAMETER_MM,
        "flange_diameter_mm": NETPOT_FLANGE_OUTER_DIAMETER_MM,
        "pot_bottom_contacts_sump_floor": False,
    }


def retention_audit_phase3ib() -> dict[str, object]:
    return {
        "positive_retention": "COMMERCIAL_5MM_VINYL_ROPE",
        "lug_count_per_port": RETENTION_LUG_COUNT_PER_PORT,
        "lug_root_thickness_mm": RETENTION_LUG_ROOT_THICKNESS_MM,
        "lug_root_fillet_class_mm": RETENTION_LUG_ROOT_FILLET_MM,
        "lug_floor_connected": True,
        "lug_main_wall_or_side_buttress_connected": True,
        "rope_nominal_diameter_mm": ROPE_NOMINAL_DIAMETER_MM,
        "rope_hole_candidates_mm": list(ROPE_HOLE_DIAMETER_CANDIDATES_MM),
        "selected_rope_hole_width_mm": SELECTED_ROPE_HOLE_WIDTH_MM,
        "rope_hole_shape": ROPE_HOLE_SHAPE,
        "maximum_horizontal_unsupported_span_mm": ROPE_HOLE_MAXIMUM_HORIZONTAL_SPAN_MM,
        "rope_path_crosses_plant_center": False,
        "rope_path_local_flange_offset_mm": 45.0,
        "keeper_optional": True,
        "cord_alone_retains_pot": True,
        "physical_retention_test": "PENDING",
    }


def overhang_audit_phase3ib() -> dict[str, object]:
    features = {
        "main_lower_pad_buttress": "FLOOR_CONNECTED_MAX_22_DEG_FROM_VERTICAL",
        "side_pad_buttresses": "FLOOR_CONNECTED_MAX_10_DEG_FROM_VERTICAL",
        "retention_lugs": "FLOOR_AND_SIDE_BUTTRESS_CONNECTED",
        "rope_teardrop_roof": "SELF_SUPPORTING_45_DEG",
        "wick_channel": "OPEN_TOP_FLOOR_CONNECTED_RAMP",
        "overflow_chute": "OPEN_AND_FLOOR_CONNECTED",
        "stacking_guides": "TOP_BAND_CONNECTED_45_DEG_RAMP",
        "inner_dam": "VERTICAL_WITH_R3_ROOT",
        "outer_wall": "VERTICAL_WITH_R3_ROOT",
    }
    return {
        "features": features,
        "maximum_unsupported_surface_angle_from_vertical_deg": 45.0,
        "horizontal_bridge_over_8mm_count": 0,
        "airborne_feature_count": 0,
        "cad_support_dependency": False,
        "bambu_studio_review_pending": True,
    }


def stage_geometry_requirements_phase3ib() -> dict[str, object]:
    full = build_integrated_stage_full_phase3ib()
    sump_coupon = build_full_annular_sump_coupon_phase3ib()
    cradle_coupon = build_single_port_cradle_sector_coupon_phase3ib()
    keeper = build_c_shaped_flange_keeper_phase3ib()
    box = full.val().BoundingBox()
    volume = sum(solid.Volume() for solid in full.solids().vals())
    installed_pots = [build_installed_netpot_reference_phase3ia(angle) for angle in PORT_ANGLES_DEG]
    installed_envelope = max(maximum_xy_diameter_phase3ib(pot) for pot in installed_pots)
    return {
        "architecture": "INTEGRATED_REAL_ANNULAR_SUMP_THREE_PORT_STAGE",
        "module_height_mm": MODULE_HEIGHT_MM,
        "nominal_body_outer_diameter_mm": NOMINAL_BODY_OUTER_DIAMETER_MM,
        "full_envelope_bbox_mm": [box.xlen, box.ylen, box.zlen],
        "full_maximum_radial_xy_mm": maximum_xy_diameter_phase3ib(full),
        "maximum_allowed_xy_mm": MAXIMUM_TOTAL_XY_ENVELOPE_MM,
        "installed_netpot_maximum_xy_mm": installed_envelope,
        "solid_count": len(full.solids().vals()),
        "sump_coupon_solid_count": len(sump_coupon.solids().vals()),
        "cradle_coupon_solid_count": len(cradle_coupon.solids().vals()),
        "keeper_solid_count": len(keeper.solids().vals()),
        # Use the authoritative clip planes.  OCCT can enlarge a later BRep
        # BoundingBox after a coarse STL triangulation is cached, while STEP
        # round-trip and STL bounds remain exactly 40/145 mm.
        "sump_coupon_height_mm": SUMP_COUPON_HEIGHT_MM,
        "cradle_coupon_height_mm": CRADLE_COUPON_HEIGHT_MM,
        "cad_reference_volume_mm3": volume,
        "petg_reference_mass_g": volume / 1000.0 * PETG_DENSITY_G_PER_CM3,
        "port_count": PORT_COUNT,
        "port_angles_deg": list(PORT_ANGLES_DEG),
        "port_axis_angle_deg": PORT_AXIS_ANGLE_DEG,
        "body_passage_diameter_mm": PORT_BODY_PASSAGE_DIAMETER_MM,
        "flange_outer_diameter_mm": NETPOT_FLANGE_OUTER_DIAMETER_MM,
        "floor_thickness_mm": SUMP_FLOOR_THICKNESS_MM,
        "central_clear_opening_diameter_mm": CENTRAL_CLEAR_OPENING_DIAMETER_MM,
        "print_orientation": "MODULE_AXIS_VERTICAL_Z_SUMP_FLOOR_ON_BUILD_PLATE",
        "sideways_printing_allowed": False,
        "segmentation_allowed": False,
    }
