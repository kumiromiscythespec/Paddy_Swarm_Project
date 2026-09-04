"""Phase 3I-A integrated wet-base growing stage.

The full and lower-coupon models are single vertically printed solids.  The
water volumes and purchased net pots are reference geometry only.
"""

from __future__ import annotations

from functools import lru_cache
from math import cos, hypot, radians, sin

import cadquery as cq

from ps_mht_v001.parameters import (
    netpot_body_passage_selected,
    netpot_siawadeky_flange_outer_diameter,
    netpot_siawadeky_flange_thickness,
    netpot_siawadeky_max_body_outer_diameter,
    netpot_siawadeky_overall_height,
    plant_port_angle,
    plant_port_local_angles,
)
from ps_mht_v001.reference.siawadeky_netpot_reference_envelope_phase3pa import (
    build_siawadeky_netpot_reference_envelope_phase3pa,
)


MODULE_HEIGHT_MM = 170.0
NOMINAL_BODY_OUTER_DIAMETER_MM = 200.0
MAXIMUM_TOTAL_XY_ENVELOPE_MM = 238.0
LOWER_COUPON_HEIGHT_MM = 60.0

UPPER_GENERAL_WALL_MM = 3.6
UPPER_GENERAL_WALL_MINIMUM_MM = 3.2
LOWER_STRUCTURAL_WALL_MM = 4.8
SUMP_FLOOR_THICKNESS_MM = 4.0
PORT_ROOT_MINIMUM_THICKNESS_MM = 6.0
TOP_STIFFENING_BAND_HEIGHT_MM = 10.0
TOP_STIFFENING_BAND_WALL_MM = 4.5
GENERAL_ROOT_FILLET_MM = 3.0
PORT_ROOT_FILLET_CLASS_MM = 4.0

SUMP_OUTER_RADIUS_MM = 96.0
SUMP_INNER_RADIUS_MM = 50.0
CENTRAL_OPENING_DIAMETER_MM = 100.0
OPERATING_DEPTH_CANDIDATES_MM = (18.0, 19.0, 20.0)
SELECTED_OPERATING_DEPTH_MM = 20.0
TARGET_OPERATING_VOLUME_L = (0.35, 0.40, 0.45)

PORT_COUNT = 3
PORT_ANGLES_DEG = (0.0, 120.0, 240.0)
PORT_AXIS_ANGLE_DEG = 27.0
PORT_CENTER_Z_MM = 85.0
PORT_REFERENCE_RADIAL_DATUM_MM = 85.4
PORT_RECESS_CANDIDATES_MM = (2.0, 3.0, 4.0, 5.0)
SELECTED_PORT_RECESS_MM = 2.0
CRADLE_OUTER_DIAMETER_MM = 112.0
CRADLE_BODY_PASSAGE_DIAMETER_MM = 80.5
CRADLE_AXIAL_THICKNESS_MM = 8.0
CRADLE_SIDE_GUSSET_WIDTH_MM = 8.0

WICK_PASSAGE_WIDTH_MM = 16.0
WICK_PASSAGE_DEPTH_MM = 30.0
REAR_CHANNEL_WIDTH_MM = 25.0
REAR_CHANNEL_DEPTH_MM = 10.0
REAR_CHANNEL_WALL_MM = 3.0
OVERFLOW_WEIR_WIDTH_MM = 25.0
OVERFLOW_CREST_ABOVE_FLOOR_MM = SELECTED_OPERATING_DEPTH_MM
OVERFLOW_MINIMUM_OPEN_THROAT_MM = 8.0

INTERNAL_RIB_COUNT = 3
INTERNAL_RIB_THICKNESS_MM = 3.6
INTERNAL_RIB_RADIAL_DEPTH_MM = 8.0
REAR_SERVICE_SPINE_TANGENTIAL_WIDTH_MM = 25.0
REAR_SERVICE_SPINE_RADIAL_DEPTH_MM = 10.0

STACKING_GUIDE_SEGMENT_COUNT = 3
STACKING_GUIDE_SEGMENT_ANGLE_DEG = 40.0
STACKING_GUIDE_HEIGHT_MM = 6.0
STACKING_GUIDE_INNER_DIAMETER_MM = 201.0
STACKING_GUIDE_OUTER_DIAMETER_MM = 210.0
STACKING_GUIDE_CLEARANCE_MM_PER_SIDE = 0.50
STACKING_SEAT_Z_MM = MODULE_HEIGHT_MM - STACKING_GUIDE_HEIGHT_MM

PETG_DENSITY_G_PER_CM3 = 1.27
FULL_PRINT_STATUS = "SLICER_REVIEW_ONLY_DO_NOT_PRINT"
COUPON_PRINT_STATUS = "READY_FIRST_AFTER_SLICER_REVIEW"
ARCHITECTURE = "ANNULAR_OPEN_CLEANABLE_SUMP_OPEN_TOP_GRAVITY_CRADLE"


def _annulus(
    outer_radius: float,
    inner_radius: float,
    height: float,
    z: float = 0.0,
) -> cq.Workplane:
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
    start = center_angle_deg - 0.5 * angle_deg
    points = [(0.0, 0.0)]
    for index in range(17):
        angle = radians(start + angle_deg * index / 16.0)
        points.append((1.5 * outer_radius * cos(angle), 1.5 * outer_radius * sin(angle)))
    wedge = cq.Workplane("XY").polyline(points).close().extrude(height).translate((0, 0, z))
    return _annulus(outer_radius, inner_radius, height, z).intersect(wedge)


def _rotate_about_z(model: cq.Workplane, angle_deg: float) -> cq.Workplane:
    return model.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)


def _orient_local_axis(
    model: cq.Workplane,
    angle_deg: float,
    radial_position_mm: float,
    center_z_mm: float = PORT_CENTER_Z_MM,
) -> cq.Workplane:
    angle = radians(angle_deg)
    return (
        model.rotate((0, 0, 0), (0, 1, 0), 90.0 - PORT_AXIS_ANGLE_DEG)
        .rotate((0, 0, 0), (0, 0, 1), angle_deg)
        .translate(
            (
                radial_position_mm * cos(angle),
                radial_position_mm * sin(angle),
                center_z_mm,
            )
        )
    )


def _teardrop_points(
    width_mm: float,
    height_mm: float,
    offset_mm: float = 0.0,
) -> list[tuple[float, float]]:
    half_width = 0.5 * width_mm + offset_mm
    half_height = 0.5 * height_mm + offset_mm
    lower_center_z = -8.0
    points: list[tuple[float, float]] = []
    from math import pi

    for index in range(25):
        angle = pi + pi * index / 24.0
        points.append(
            (
                half_width * cos(angle),
                lower_center_z + half_width * sin(angle),
            )
        )
    shoulder_z = half_height - half_width
    points.extend(((half_width, shoulder_z), (0.0, half_height), (-half_width, shoulder_z)))
    return points


def _teardrop_prism(
    x_origin_mm: float,
    z_center_mm: float,
    extrusion_mm: float,
    offset_mm: float,
) -> cq.Workplane:
    model = (
        cq.Workplane("YZ", origin=(x_origin_mm, 0.0, z_center_mm))
        .polyline(_teardrop_points(88.0, 96.0, offset_mm))
        .close()
        .extrude(extrusion_mm)
    )
    return model.rotate(
        (100.0, 0.0, z_center_mm),
        (100.0, 1.0, z_center_mm),
        -PORT_AXIS_ANGLE_DEG,
    )


def build_port_void_phase3ia(angle_deg: float) -> cq.Workplane:
    return _rotate_about_z(
        _teardrop_prism(68.0, PORT_CENTER_Z_MM, 62.0, 0.0),
        angle_deg,
    )


def build_port_root_frame_phase3ia(angle_deg: float) -> cq.Workplane:
    outer = _teardrop_prism(73.0, PORT_CENTER_Z_MM, 18.0, PORT_ROOT_MINIMUM_THICKNESS_MM)
    inner = _teardrop_prism(71.0, PORT_CENTER_Z_MM, 22.0, 0.0)
    return _rotate_about_z(outer.cut(inner), angle_deg)


def build_netpot_clearance_void_phase3ia(angle_deg: float) -> cq.Workplane:
    """Return measured body passage plus a shallow removable-flange envelope."""

    body = (
        cq.Workplane("XY")
        .circle(0.5 * CRADLE_BODY_PASSAGE_DIAMETER_MM)
        .extrude(78.0)
        .translate((0.0, 0.0, -70.0))
    )
    flange = (
        cq.Workplane("XY")
        .circle(0.5 * (netpot_siawadeky_flange_outer_diameter + 0.5))
        .extrude(netpot_siawadeky_flange_thickness + 2.0)
        .translate((0.0, 0.0, CRADLE_AXIAL_THICKNESS_MM))
    )
    radial = PORT_REFERENCE_RADIAL_DATUM_MM - SELECTED_PORT_RECESS_MM
    return _orient_local_axis(body.union(flange), angle_deg, radial)


def build_open_cradle_local_phase3ia() -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(0.5 * CRADLE_OUTER_DIAMETER_MM)
        .circle(0.5 * CRADLE_BODY_PASSAGE_DIAMETER_MM)
        .extrude(CRADLE_AXIAL_THICKNESS_MM)
    )
    lower_and_side_support = (
        cq.Workplane("XY")
        .box(128.0, 128.0, 12.0, centered=(True, True, False))
        .translate((56.0, 0.0, -2.0))
    )
    return ring.intersect(lower_and_side_support)


def build_open_cradle_phase3ia(angle_deg: float) -> cq.Workplane:
    radial = PORT_REFERENCE_RADIAL_DATUM_MM - SELECTED_PORT_RECESS_MM
    return _orient_local_axis(build_open_cradle_local_phase3ia(), angle_deg, radial)


def build_cradle_gussets_phase3ia(angle_deg: float) -> cq.Workplane:
    gussets: list[cq.Shape] = []
    for y in (-38.0, 38.0):
        gusset = (
            cq.Workplane("XY")
            .box(30.0, CRADLE_SIDE_GUSSET_WIDTH_MM, 52.0, centered=(True, True, False))
            .translate((93.0, y, SUMP_FLOOR_THICKNESS_MM - 0.5))
        )
        gussets.append(gusset.val())
    compound = cq.Workplane("XY").newObject([cq.Compound.makeCompound(gussets)])
    return _rotate_about_z(compound, angle_deg)


def build_wick_guide_rails_phase3ia(angle_deg: float) -> cq.Workplane:
    rails: list[cq.Shape] = []
    for y in (-10.0, 10.0):
        rail = (
            cq.Workplane("XY")
            .box(WICK_PASSAGE_DEPTH_MM, 4.0, 32.0, centered=(True, True, False))
            .translate((70.0, y, SUMP_FLOOR_THICKNESS_MM - 0.5))
        )
        rails.append(rail.val())
    compound = cq.Workplane("XY").newObject([cq.Compound.makeCompound(rails)])
    return _rotate_about_z(compound, angle_deg)


def build_internal_rib_phase3ia(angle_deg: float) -> cq.Workplane:
    rib = (
        cq.Workplane("XY")
        .box(
            INTERNAL_RIB_RADIAL_DEPTH_MM + 1.0,
            INTERNAL_RIB_THICKNESS_MM,
            STACKING_SEAT_Z_MM - SUMP_FLOOR_THICKNESS_MM,
            centered=(True, True, False),
        )
        .translate((91.0, 0.0, SUMP_FLOOR_THICKNESS_MM - 0.5))
    )
    return _rotate_about_z(rib, angle_deg)


def build_rear_channel_walls_phase3ia() -> cq.Workplane:
    walls: list[cq.Shape] = []
    for y in (-0.5 * REAR_CHANNEL_WIDTH_MM, 0.5 * REAR_CHANNEL_WIDTH_MM):
        wall = (
            cq.Workplane("XY")
            .box(
                REAR_CHANNEL_DEPTH_MM + 1.0,
                REAR_CHANNEL_WALL_MM,
                STACKING_SEAT_Z_MM - SUMP_FLOOR_THICKNESS_MM,
                centered=(True, True, False),
            )
            .translate((90.5, y, SUMP_FLOOR_THICKNESS_MM - 0.5))
        )
        walls.append(wall.val())
    return _rotate_about_z(
        cq.Workplane("XY").newObject([cq.Compound.makeCompound(walls)]),
        180.0,
    )


def build_overflow_opening_phase3ia() -> cq.Workplane:
    crest_z = SUMP_FLOOR_THICKNESS_MM + OVERFLOW_CREST_ABOVE_FLOOR_MM
    return (
        cq.Workplane("XY")
        .box(14.0, OVERFLOW_WEIR_WIDTH_MM, MODULE_HEIGHT_MM, centered=(True, True, False))
        .translate((-98.0, 0.0, crest_z))
    )


def build_stacking_guides_phase3ia() -> cq.Workplane:
    shapes: list[cq.Shape] = []
    for angle in PORT_ANGLES_DEG:
        base = _sector(99.5, 105.0, angle, STACKING_GUIDE_SEGMENT_ANGLE_DEG, 2.0, STACKING_SEAT_Z_MM - 2.0)
        guide = _sector(100.5, 105.0, angle, STACKING_GUIDE_SEGMENT_ANGLE_DEG, STACKING_GUIDE_HEIGHT_MM, STACKING_SEAT_Z_MM)
        shapes.extend((base.val(), guide.val()))
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


@lru_cache(maxsize=1)
def build_integrated_stage_full_phase3ia() -> cq.Workplane:
    floor = _annulus(100.0, SUMP_INNER_RADIUS_MM, SUMP_FLOOR_THICKNESS_MM)
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
    # Exact R3 quarter-round at the wet floor/wall corner.  The arc is tangent
    # to the floor at r=92.2 and to the 95.2 mm inner wall at z=7.0.
    root_transition = (
        cq.Workplane("XZ")
        .moveTo(92.2, SUMP_FLOOR_THICKNESS_MM)
        .lineTo(95.2, SUMP_FLOOR_THICKNESS_MM)
        .lineTo(95.2, SUMP_FLOOR_THICKNESS_MM + GENERAL_ROOT_FILLET_MM)
        .threePointArc(
            (94.3213203436, 4.8786796564),
            (92.2, SUMP_FLOOR_THICKNESS_MM),
        )
        .close()
        .revolve(360.0, (0.0, 0.0), (0.0, 1.0))
    )
    stage = floor.union(lower_wall).union(general_wall).union(top_band).union(root_transition)

    for angle in PORT_ANGLES_DEG:
        stage = stage.union(build_port_root_frame_phase3ia(angle))
        stage = stage.union(build_open_cradle_phase3ia(angle))
        stage = stage.union(build_cradle_gussets_phase3ia(angle))
        stage = stage.union(build_wick_guide_rails_phase3ia(angle))
        stage = stage.cut(build_port_void_phase3ia(angle))
        stage = stage.cut(build_netpot_clearance_void_phase3ia(angle))

    for angle in (60.0, 180.0, 300.0):
        stage = stage.union(build_internal_rib_phase3ia(angle))
    stage = stage.union(build_rear_channel_walls_phase3ia())
    for angle in PORT_ANGLES_DEG:
        stage = stage.union(
            _sector(
                99.5,
                105.0,
                angle,
                STACKING_GUIDE_SEGMENT_ANGLE_DEG,
                2.0,
                STACKING_SEAT_Z_MM - 2.0,
            )
        )
        stage = stage.union(
            _sector(
                100.5,
                105.0,
                angle,
                STACKING_GUIDE_SEGMENT_ANGLE_DEG,
                STACKING_GUIDE_HEIGHT_MM,
                STACKING_SEAT_Z_MM,
            )
        )
    stage = stage.cut(build_overflow_opening_phase3ia())
    cleaned = stage.clean()
    # The flange-clearance cut can detach three non-load-bearing fragments of
    # the sacrificial outer frame roof.  They are deliberately omitted: the
    # printable authority is the single floor-connected load path.
    solids = list(cleaned.solids().vals())
    main = max(solids, key=lambda solid: solid.Volume())
    return cq.Workplane("XY").newObject([main])


@lru_cache(maxsize=1)
def build_integrated_stage_lower_60mm_coupon_phase3ia() -> cq.Workplane:
    full = build_integrated_stage_full_phase3ia()
    clip = (
        cq.Workplane("XY")
        .box(260.0, 260.0, LOWER_COUPON_HEIGHT_MM, centered=(True, True, False))
    )
    return full.intersect(clip).clean()


def build_installed_netpot_reference_phase3ia(
    angle_deg: float,
    recess_mm: float = SELECTED_PORT_RECESS_MM,
) -> cq.Workplane:
    # The Phase 3P-A reference has its flange bottom at local Z=64 mm.
    # Shift it to the unchanged 8 mm seat face before orienting it.
    local = build_siawadeky_netpot_reference_envelope_phase3pa().translate((0.0, 0.0, 8.0 - 64.0))
    return _orient_local_axis(
        local,
        angle_deg,
        PORT_REFERENCE_RADIAL_DATUM_MM - recess_mm,
    )


def maximum_xy_radius_phase3ia(model: cq.Workplane) -> float:
    maximum = 0.0
    for solid in model.solids().vals():
        vertices, _ = solid.tessellate(0.35, 0.2)
        maximum = max(maximum, *(hypot(vertex.x, vertex.y) for vertex in vertices))
    return maximum


def netpot_recess_audit_phase3ia() -> dict[str, object]:
    stage = build_integrated_stage_full_phase3ia()
    candidates: dict[str, object] = {}
    for recess in PORT_RECESS_CANDIDATES_MM:
        pots = [build_installed_netpot_reference_phase3ia(angle, recess) for angle in PORT_ANGLES_DEG]
        maximum = max(2.0 * maximum_xy_radius_phase3ia(pot) for pot in pots)
        pot_stage_intersection = sum(
            solid.Volume() for pot in pots for solid in pot.intersect(stage).solids().vals()
        )
        pair_intersections = []
        for first, second in ((0, 1), (0, 2), (1, 2)):
            pair_intersections.append(
                sum(solid.Volume() for solid in pots[first].intersect(pots[second]).solids().vals())
            )
        candidates[f"r{int(recess):02d}"] = {
            "recess_mm": recess,
            "installed_netpot_maximum_xy_mm": maximum,
            "printed_stage_maximum_xy_mm": 2.0 * maximum_xy_radius_phase3ia(stage),
            "pot_stage_intersection_volume_mm3": pot_stage_intersection,
            "pot_pair_intersection_volume_mm3": pair_intersections,
            "within_238mm": maximum <= MAXIMUM_TOTAL_XY_ENVELOPE_MM,
            "tool_free_removal_geometry": "OPEN_TOP_NO_PRINTED_RETENTION",
            "root_wick_access_width_mm": WICK_PASSAGE_WIDTH_MM,
        }
    return {
        "selected_recess_mm": SELECTED_PORT_RECESS_MM,
        "selection_rule": "SMALLEST_CANDIDATE_MEETING_ALL_GEOMETRIC_LIMITS",
        "candidates": candidates,
        "inner_diameter_measurements_used_for_external_envelope": False,
    }


def build_water_volume_phase3ia(depth_mm: float) -> cq.Workplane:
    if depth_mm not in OPERATING_DEPTH_CANDIDATES_MM:
        raise ValueError("depth must be one of 18, 19 or 20 mm")
    blank = _annulus(
        100.0 - LOWER_STRUCTURAL_WALL_MM,
        SUMP_INNER_RADIUS_MM,
        depth_mm,
        SUMP_FLOOR_THICKNESS_MM,
    )
    return blank.cut(build_integrated_stage_full_phase3ia()).clean()


def water_volume_audit_phase3ia() -> dict[str, object]:
    candidates: dict[str, object] = {}
    for depth in OPERATING_DEPTH_CANDIDATES_MM:
        water = build_water_volume_phase3ia(depth)
        solids = list(water.solids().vals())
        volume = sum(solid.Volume() for solid in solids)
        center = cq.Shape.centerOfMass(cq.Compound.makeCompound(solids))
        volume_l = volume / 1_000_000.0
        candidates[f"d{int(depth):02d}"] = {
            "depth_mm": depth,
            "actual_water_volume_l": volume_l,
            "remaining_to_0_45_l": 0.45 - volume_l,
            "distance_below_overflow_crest_mm": OVERFLOW_CREST_ABOVE_FLOOR_MM - depth,
            "water_mass_kg_reference": volume_l,
            "center_of_mass_mm": [center.x, center.y, center.z],
            "solid_count": len(solids),
            "within_target_range": TARGET_OPERATING_VOLUME_L[0] <= volume_l <= TARGET_OPERATING_VOLUME_L[2],
        }
    return {
        "sump_type": "ANNULAR_OPEN_CLEANABLE_SUMP",
        "selected_depth_mm": SELECTED_OPERATING_DEPTH_MM,
        "target_volume_l": {
            "minimum": TARGET_OPERATING_VOLUME_L[0],
            "preferred": TARGET_OPERATING_VOLUME_L[1],
            "maximum": TARGET_OPERATING_VOLUME_L[2],
        },
        "candidates": candidates,
    }


def overflow_audit_phase3ia() -> dict[str, object]:
    geometric_area = OVERFLOW_WEIR_WIDTH_MM * OVERFLOW_MINIMUM_OPEN_THROAT_MM
    return {
        "type": "OPEN_WEIR",
        "width_mm": OVERFLOW_WEIR_WIDTH_MM,
        "crest_height_above_sump_floor_mm": OVERFLOW_CREST_ABOVE_FLOOR_MM,
        "minimum_open_throat_mm": OVERFLOW_MINIMUM_OPEN_THROAT_MM,
        "minimum_geometric_open_area_mm2": geometric_area,
        "closed_siphon": False,
        "small_diameter_drain": False,
        "flow_review": {
            "0.5_L_min": "GEOMETRIC_AREA_AVAILABLE_PHYSICAL_TEST_PENDING",
            "1.0_L_min": "GEOMETRIC_AREA_AVAILABLE_PHYSICAL_TEST_PENDING",
            "2.0_L_min_transient": "PHYSICAL_OVERFLOW_TEST_REQUIRED",
        },
        "cfd_performed": False,
    }


def overhang_audit_phase3ia() -> dict[str, object]:
    features = {
        "plant_port_upper_opening": "SELF_SUPPORTING_45_OR_LESS",
        "flange_seat_underside": "SLICER_REVIEW_REQUIRED",
        "port_cradle_inside": "SLICER_REVIEW_REQUIRED",
        "root_wick_passage": "SELF_SUPPORTING_45_OR_LESS",
        "sump_inner_wall": "SELF_SUPPORTING_45_OR_LESS",
        "sump_outer_wall": "SELF_SUPPORTING_45_OR_LESS",
        "rear_channel": "SELF_SUPPORTING_45_OR_LESS",
        "overflow_weir": "SELF_SUPPORTING_45_OR_LESS",
        "stacking_guide": "SELF_SUPPORTING_45_OR_LESS",
        "port_gusset_root": "SELF_SUPPORTING_45_OR_LESS",
        "sump_floor_wall_transition": "SELF_SUPPORTING_45_OR_LESS",
        "top_stiffening_band": "SELF_SUPPORTING_45_OR_LESS",
    }
    return {
        "features": features,
        "unsupported_prohibited_count": sum(value == "UNSUPPORTED_PROHIBITED" for value in features.values()),
        "automatic_support_dependency": False,
        "bambu_studio_review_pending": True,
    }


def stage_geometry_requirements_phase3ia() -> dict[str, object]:
    stage = build_integrated_stage_full_phase3ia()
    coupon = build_integrated_stage_lower_60mm_coupon_phase3ia()
    stage_box = stage.val().BoundingBox()
    coupon_box = coupon.val().BoundingBox()
    volume_mm3 = sum(solid.Volume() for solid in stage.solids().vals())
    center = cq.Shape.centerOfMass(cq.Compound.makeCompound(list(stage.solids().vals())))
    return {
        "architecture": ARCHITECTURE,
        "module_height_mm": MODULE_HEIGHT_MM,
        "nominal_body_outer_diameter_mm": NOMINAL_BODY_OUTER_DIAMETER_MM,
        "maximum_allowed_xy_mm": MAXIMUM_TOTAL_XY_ENVELOPE_MM,
        "full_envelope_mm": [stage_box.xlen, stage_box.ylen, stage_box.zlen],
        "full_maximum_radial_xy_mm": 2.0 * maximum_xy_radius_phase3ia(stage),
        "coupon_envelope_mm": [coupon_box.xlen, coupon_box.ylen, coupon_box.zlen],
        "solid_count": len(stage.solids().vals()),
        "coupon_solid_count": len(coupon.solids().vals()),
        "volume_mm3": volume_mm3,
        "petg_reference_mass_g": volume_mm3 / 1000.0 * PETG_DENSITY_G_PER_CM3,
        "center_of_mass_mm": [center.x, center.y, center.z],
        "floor_contact_annular_area_mm2": 3.141592653589793 * (100.0**2 - SUMP_INNER_RADIUS_MM**2),
        "walls_mm": {
            "upper_nominal": UPPER_GENERAL_WALL_MM,
            "upper_minimum": UPPER_GENERAL_WALL_MINIMUM_MM,
            "lower_structural": LOWER_STRUCTURAL_WALL_MM,
            "sump_floor": SUMP_FLOOR_THICKNESS_MM,
            "port_root": PORT_ROOT_MINIMUM_THICKNESS_MM,
            "top_band": TOP_STIFFENING_BAND_WALL_MM,
        },
        "closed_waterways": 0,
        "uncleanable_cavities": 0,
        "print_orientation": "VERTICAL_Z",
        "sideways_printing": False,
        "segmentation": False,
    }
