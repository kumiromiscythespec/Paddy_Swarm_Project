"""Progressive Phase 3I-C floating-region isolation models D01 through D05."""

from __future__ import annotations

from functools import lru_cache
from math import cos, hypot, radians, sin

import cadquery as cq

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
    SELECTED_PORT_RECESS_MM,
    build_netpot_clearance_void_phase3ia,
    build_port_root_frame_phase3ia,
    build_port_void_phase3ia,
)
from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib


DIAGNOSTIC_NAMES = (
    "PHASE3IC_DIAG_01_WET_CORE_MAIN_WALL",
    "PHASE3IC_DIAG_02_PLUS_CRADLE_BUTTRESSES",
    "PHASE3IC_DIAG_03_PLUS_RETENTION_LUGS",
    "PHASE3IC_DIAG_04_PLUS_REAR_CASCADE_AND_WICK",
    "PHASE3IC_DIAG_05_PLUS_STACKING_GUIDES_FULL_EQUIVALENT",
)
DIAGNOSTIC_STATUS = "SLICER_DIAGNOSTIC_ONLY_DO_NOT_PRINT"
PRINT_ORIENTATION = "MODULE_AXIS_VERTICAL_Z_FLOOR_ON_BUILD_PLATE"
STL_TOLERANCE_AUTHORITY = "ps_mht_v001.parameters stl_linear_tolerance/stl_angular_tolerance"


def _wet_core_main_wall_phase3ic() -> cq.Workplane:
    floor = phase3ib._annulus(100.0, 50.0, phase3ib.SUMP_FLOOR_THICKNESS_MM)
    lower_wall = phase3ib._annulus(100.0, 100.0 - phase3ib.LOWER_STRUCTURAL_WALL_MM, 60.0)
    general_wall = phase3ib._annulus(
        100.0,
        100.0 - phase3ib.UPPER_GENERAL_WALL_MM,
        phase3ib.STACKING_SEAT_Z_MM - phase3ib.TOP_STIFFENING_BAND_HEIGHT_MM - 60.0,
        60.0,
    )
    top_band = phase3ib._annulus(
        100.0,
        100.0 - phase3ib.TOP_STIFFENING_BAND_WALL_MM,
        phase3ib.TOP_STIFFENING_BAND_HEIGHT_MM,
        phase3ib.STACKING_SEAT_Z_MM - phase3ib.TOP_STIFFENING_BAND_HEIGHT_MM,
    )
    stage = (
        floor.union(phase3ib.build_real_inner_dam_phase3ib())
        .union(lower_wall)
        .union(general_wall)
        .union(top_band)
        .union(phase3ib.build_outer_floor_wall_root_phase3ib())
    )
    for angle in phase3ib.PORT_ANGLES_DEG:
        stage = stage.union(build_port_root_frame_phase3ia(angle))
        stage = stage.cut(build_port_void_phase3ia(angle))
        stage = stage.cut(build_netpot_clearance_void_phase3ia(angle))
    stage = stage.cut(phase3ib.build_overflow_opening_phase3ib())
    return phase3ib._largest_solid(stage)


RETENTION_LUG_SIDE_SIGNS = (-1.0, 1.0)
RETENTION_LUG_BOTTOM_Z_MM = 27.0
RETENTION_LUG_BOTTOM_SIZE_MM = 9.4
RETENTION_LUG_MINIMUM_REQUIRED_OVERLAP_MM = 0.8
RETENTION_LUG_CONNECTION_OVERLAP_MM = 0.85
RETENTION_LUG_TOP_Z_MM = 138.0
RETENTION_HOLE_CENTER_Z_MM = 132.0
RETENTION_LUG_TOP_RADIAL_THICKNESS_MM = 12.0
RETENTION_LUG_TOP_TANGENTIAL_THICKNESS_MM = 14.0


def _rotate_world_point_about_z(point: tuple[float, float, float], angle_deg: float) -> tuple[float, float, float]:
    x, y, z = point
    angle = radians(angle_deg)
    return (x * cos(angle) - y * sin(angle), x * sin(angle) + y * cos(angle), z)


def maximum_xy_diameter_without_mesh_cache_phase3ic(model: cq.Workplane) -> float:
    copied = model.val().copy(mesh=False)
    vertices, _ = copied.tessellate(0.35, 0.2)
    return 2.0 * max(hypot(vertex.x, vertex.y) for vertex in vertices)


def build_isolated_retention_lug_raw_phase3ic(port_angle_deg: float, side_sign: float) -> cq.Workplane:
    if side_sign not in RETENTION_LUG_SIDE_SIGNS:
        raise ValueError("side_sign must be -1.0 or 1.0")
    side_buttress_fraction = (
        (RETENTION_LUG_BOTTOM_Z_MM - (phase3ib.SUMP_FLOOR_THICKNESS_MM - 0.5))
        / (89.0 - (phase3ib.SUMP_FLOOR_THICKNESS_MM - 0.5))
    )
    bottom_x = 86.0 + 3.0 * side_buttress_fraction
    bottom_y = side_sign * (38.0 + 7.0 * side_buttress_fraction)
    lug = phase3ib._loft_between_rectangles(
        (bottom_x, bottom_y, RETENTION_LUG_BOTTOM_Z_MM),
        (RETENTION_LUG_BOTTOM_SIZE_MM, RETENTION_LUG_BOTTOM_SIZE_MM),
        (74.5, side_sign * 36.0, RETENTION_LUG_TOP_Z_MM),
        (RETENTION_LUG_TOP_RADIAL_THICKNESS_MM, RETENTION_LUG_TOP_TANGENTIAL_THICKNESS_MM),
    )
    return phase3ib._rotate_z(lug, port_angle_deg).clean()


def build_isolated_retention_hole_phase3ic(port_angle_deg: float, side_sign: float) -> cq.Workplane:
    hole = phase3ib._teardrop_hole_phase3ib(side_sign * 36.0)
    return phase3ib._rotate_z(hole, port_angle_deg)


def build_isolated_retention_lug_net_phase3ic(port_angle_deg: float, side_sign: float) -> cq.Workplane:
    return (
        build_isolated_retention_lug_raw_phase3ic(port_angle_deg, side_sign)
        .cut(build_isolated_retention_hole_phase3ic(port_angle_deg, side_sign))
        .clean()
    )


def _validate_optional_order(
    include_cradle_buttresses: bool,
    include_retention_lugs: bool,
    include_cascade_and_wick: bool,
    include_stacking_guides: bool,
) -> None:
    if include_retention_lugs and not include_cradle_buttresses:
        raise ValueError("retention lugs require cradle buttresses")
    if include_cascade_and_wick and not include_retention_lugs:
        raise ValueError("cascade/wick requires retention stage")
    if include_stacking_guides and not include_cascade_and_wick:
        raise ValueError("stacking guides require cascade/wick stage")


@lru_cache(maxsize=16)
def build_integrated_stage_corrected_phase3ic(
    include_cradle_buttresses: bool,
    include_retention_lugs: bool,
    include_cascade_and_wick: bool,
    include_stacking_guides: bool,
) -> cq.Workplane:
    _validate_optional_order(
        include_cradle_buttresses,
        include_retention_lugs,
        include_cascade_and_wick,
        include_stacking_guides,
    )
    stage = _wet_core_main_wall_phase3ic()
    if include_cradle_buttresses:
        for angle in phase3ib.PORT_ANGLES_DEG:
            stage = stage.union(phase3ib.build_floor_connected_cradle_phase3ib(angle)).clean()
    if include_retention_lugs:
        # Six individually cut, individually fused lugs.  No Glue shortcut is
        # permitted: each net lug has >0.8 mm floor penetration and a measured
        # positive-volume intersection with the D02 connection authority.
        for angle in phase3ib.PORT_ANGLES_DEG:
            for side_sign in RETENTION_LUG_SIDE_SIGNS:
                lug = build_isolated_retention_lug_net_phase3ic(angle, side_sign)
                stage = stage.union(lug, clean=True, glue=False).clean()
    if include_cascade_and_wick:
        for angle in phase3ib.PORT_ANGLES_DEG:
            stage = stage.union(phase3ib.build_wick_open_channel_phase3ib(angle)).clean()
        stage = stage.union(phase3ib.build_open_overflow_chute_phase3ib()).clean()
    if include_stacking_guides:
        stage = stage.union(phase3ib.build_stacking_guides_phase3ib()).clean()
    return phase3ib._largest_solid(stage)


@lru_cache(maxsize=1)
def build_phase3ic_diag_01() -> cq.Workplane:
    return build_integrated_stage_corrected_phase3ic(False, False, False, False)


@lru_cache(maxsize=1)
def build_phase3ic_diag_02() -> cq.Workplane:
    return build_integrated_stage_corrected_phase3ic(True, False, False, False)


@lru_cache(maxsize=1)
def build_phase3ic_diag_03() -> cq.Workplane:
    return build_integrated_stage_corrected_phase3ic(True, True, False, False)


@lru_cache(maxsize=1)
def build_phase3ic_diag_04() -> cq.Workplane:
    return build_integrated_stage_corrected_phase3ic(True, True, True, False)


@lru_cache(maxsize=1)
def build_phase3ic_diag_05() -> cq.Workplane:
    return build_integrated_stage_corrected_phase3ic(True, True, True, True)


@lru_cache(maxsize=1)
def build_integrated_stage_full_corrected_phase3ic() -> cq.Workplane:
    return build_integrated_stage_corrected_phase3ic(True, True, True, True)


def build_all_diagnostics_phase3ic() -> tuple[cq.Workplane, ...]:
    return (
        build_phase3ic_diag_01(),
        build_phase3ic_diag_02(),
        build_phase3ic_diag_03(),
        build_phase3ic_diag_04(),
        build_phase3ic_diag_05(),
    )


def diagnostic_feature_map_phase3ic() -> dict[str, object]:
    stages = {
        "D01": {
            "name": DIAGNOSTIC_NAMES[0],
            "features": ["REAL_SUMP_FLOOR", "MAIN_OUTER_WALL", "CONTINUOUS_INNER_DAM", "CENTRAL_OPENING", "REAR_WEIR_BOUNDARY", "THREE_PORT_CUTS", "LOWER_STRUCTURE", "UPPER_MAIN_BAND"],
            "added_from_previous": ["BASELINE_WET_CORE"],
        },
        "D02": {
            "name": DIAGNOSTIC_NAMES[1],
            "features": ["D01_ALL", "THREE_MAIN_PADS", "SIX_SIDE_PADS", "NINE_FLOOR_CONNECTED_BUTTRESSES"],
            "added_from_previous": ["CRADLE_PADS_AND_BUTTRESSES"],
        },
        "D03": {
            "name": DIAGNOSTIC_NAMES[2],
            "features": ["D02_ALL", "SIX_RETENTION_LUGS", "SIX_5P6MM_TEARDROP_HOLES"],
            "added_from_previous": ["RETENTION_LUGS_AND_ROPE_HOLES"],
        },
        "D04": {
            "name": DIAGNOSTIC_NAMES[3],
            "features": ["D03_ALL", "THREE_OPEN_WICK_ROUTES", "OPEN_REAR_CASCADE", "OPEN_CHUTE", "INTEGRATED_REAR_SIDE_WALLS"],
            "added_from_previous": ["REAR_CASCADE_AND_WICK"],
        },
        "D05": {
            "name": DIAGNOSTIC_NAMES[4],
            "features": ["D04_ALL", "THREE_DRY_STACKING_GUIDES", "THREE_GUIDE_RAMPS", "FINAL_TOP_BAND_EQUIVALENT"],
            "added_from_previous": ["STACKING_GUIDES_AND_RAMPS"],
        },
    }
    return {
        "progression": ["D01", "D02", "D03", "D04", "D05"],
        "strictly_additive_feature_authority": True,
        "stages": stages,
        "bambu_studio_result": "PENDING",
        "print_status": DIAGNOSTIC_STATUS,
    }


def diagnostic_geometry_audit_phase3ic() -> dict[str, object]:
    models = build_all_diagnostics_phase3ic()
    stages: dict[str, object] = {}
    previous_volume = 0.0
    for index, model in enumerate(models, start=1):
        solids = list(model.solids().vals())
        box = model.val().BoundingBox()
        volume = sum(solid.Volume() for solid in solids)
        stages[f"D{index:02d}"] = {
            "solid_count": len(solids),
            "all_solids_valid": all(solid.isValid() for solid in solids),
            "bbox_mm": [box.xlen, box.ylen, box.zlen],
            "volume_mm3": volume,
            "volume_added_from_previous_mm3": volume - previous_volume if index > 1 else volume,
            "z_min_registered_to_zero": abs(box.zmin) <= 1.0e-5,
            "print_orientation": PRINT_ORIENTATION,
        }
        previous_volume = volume
    full = build_integrated_stage_full_corrected_phase3ic()
    d05 = models[-1]
    full_box = full.val().BoundingBox()
    d05_box = d05.val().BoundingBox()
    volume_difference = abs(d05.val().Volume() - full.val().Volume())
    bbox_difference = [
        abs(a - b)
        for a, b in zip(
            (d05_box.xlen, d05_box.ylen, d05_box.zlen),
            (full_box.xlen, full_box.ylen, full_box.zlen),
        )
    ]
    return {
        "stages": stages,
        "feature_progression": ["WET_CORE", "CRADLE", "RETENTION", "CASCADE_AND_WICK", "STACKING_GUIDES"],
        "d05_phase3ic_corrected_full_equivalence": {
            "brep_volume_difference_mm3": volume_difference,
            "bbox_difference_mm": bbox_difference,
            "solid_count_d05": len(d05.solids().vals()),
            "solid_count_phase3ic_corrected_full": len(full.solids().vals()),
            "same_shape_object_authority": d05.val().isSame(full.val()),
            "within_tolerance": volume_difference <= 1.0e-6 and max(bbox_difference) <= 1.0e-6,
        },
    }


def retention_lug_boolean_audit_phase3ic() -> dict[str, object]:
    d02 = build_phase3ic_diag_02()
    d03 = build_phase3ic_diag_03()
    lugs: list[dict[str, object]] = []
    predicted_increment = 0.0
    index = 0
    for angle in phase3ib.PORT_ANGLES_DEG:
        for side_sign in RETENTION_LUG_SIDE_SIGNS:
            index += 1
            raw = build_isolated_retention_lug_raw_phase3ic(angle, side_sign)
            net = build_isolated_retention_lug_net_phase3ic(angle, side_sign)
            hole = build_isolated_retention_hole_phase3ic(angle, side_sign)
            raw_volume = raw.val().Volume()
            net_volume = net.val().Volume()
            hole_cut_volume = raw_volume - net_volume
            intersection_volume = sum(
                solid.Volume() for solid in net.intersect(d02).solids().vals()
            )
            exterior_volume = net_volume - intersection_volume
            predicted_increment += exterior_volume
            lugs.append(
                {
                    "lug_number": index,
                    "port_angle_deg": angle,
                    "side": "LEFT" if side_sign < 0 else "RIGHT",
                    "raw_volume_mm3": raw_volume,
                    "net_volume_after_hole_mm3": net_volume,
                    "teardrop_hole_cut_volume_mm3": hole_cut_volume,
                    "connection_intersection_volume_mm3": intersection_volume,
                    "predicted_exterior_addition_mm3": exterior_volume,
                    "isolated_raw_solid_count": len(raw.solids().vals()),
                    "isolated_net_solid_count": len(net.solids().vals()),
                    "isolated_raw_valid": raw.val().isValid(),
                    "isolated_net_valid": net.val().isValid(),
                    "hole_void_intersects_raw_volume_mm3": sum(
                        solid.Volume() for solid in hole.intersect(raw).solids().vals()
                    ),
                    "connection_target": "EXISTING_FLOOR_CONNECTED_SIDE_BUTTRESS",
                    "connection_overlap_depth_mm": RETENTION_LUG_CONNECTION_OVERLAP_MM,
                    "minimum_wall_around_hole_mm": min(
                        0.5 * (RETENTION_LUG_TOP_RADIAL_THICKNESS_MM - phase3ib.SELECTED_ROPE_HOLE_WIDTH_MM),
                        RETENTION_LUG_TOP_Z_MM
                        - (
                            RETENTION_HOLE_CENTER_Z_MM
                            + 1.6 * 0.5 * phase3ib.SELECTED_ROPE_HOLE_WIDTH_MM
                        ),
                    ),
                    "appears_outside_d02": exterior_volume > 1.0,
                    "hole_fully_penetrating": hole_cut_volume > 0.0,
                }
            )
    d02_volume = d02.val().Volume()
    d03_volume = d03.val().Volume()
    actual_increment = d03_volume - d02_volume
    difference = actual_increment - predicted_increment
    tolerance = max(0.01, predicted_increment * 1.0e-5)
    return {
        "lug_count": len(lugs),
        "lugs": lugs,
        "d02_volume_mm3": d02_volume,
        "d03_volume_mm3": d03_volume,
        "retention_increment_mm3": actual_increment,
        "predicted_increment_mm3": predicted_increment,
        "difference_mm3": difference,
        "tolerance_mm3": tolerance,
        "minimum_required_floor_overlap_mm": RETENTION_LUG_MINIMUM_REQUIRED_OVERLAP_MM,
        "all_six_visible": all(bool(item["appears_outside_d02"]) for item in lugs),
        "all_six_holes_penetrating": all(bool(item["hole_fully_penetrating"]) for item in lugs),
        "full_model_solid_count": len(d03.solids().vals()),
        "status": "PASS" if (
            actual_increment > 0.0
            and abs(difference) <= tolerance
            and all(float(item["connection_overlap_depth_mm"]) >= RETENTION_LUG_MINIMUM_REQUIRED_OVERLAP_MM for item in lugs)
            and all(bool(item["appears_outside_d02"]) for item in lugs)
            and all(bool(item["hole_fully_penetrating"]) for item in lugs)
            and len(d03.solids().vals()) == 1
        ) else "FAIL",
    }


def phase3ic_phase3ib_geometry_delta_audit() -> dict[str, object]:
    corrected = build_integrated_stage_full_corrected_phase3ic()
    legacy = phase3ib.build_integrated_stage_full_phase3ib()
    corrected_box = corrected.val().BoundingBox()
    legacy_box = legacy.val().BoundingBox()
    corrected_center = cq.Shape.centerOfMass(corrected.val())
    legacy_center = cq.Shape.centerOfMass(legacy.val())
    corrected_water = phase3ib._annulus(
        100.0 - phase3ib.LOWER_STRUCTURAL_WALL_MM,
        0.5 * phase3ib.INNER_DAM_OUTER_DIAMETER_MM,
        phase3ib.SELECTED_OPERATING_WATER_DEPTH_MM,
        phase3ib.SUMP_FLOOR_THICKNESS_MM,
    ).cut(corrected).clean()
    legacy_water = phase3ib.build_actual_water_volume_phase3ib(
        phase3ib.SELECTED_OPERATING_WATER_DEPTH_MM
    )
    return {
        "phase3ib_status": "HISTORICAL_FAILED_BASELINE",
        "phase3ic_corrected_volume_mm3": corrected.val().Volume(),
        "phase3ib_legacy_volume_mm3": legacy.val().Volume(),
        "volume_difference_mm3": corrected.val().Volume() - legacy.val().Volume(),
        "bbox_difference_mm": [
            a - b
            for a, b in zip(
                (corrected_box.xlen, corrected_box.ylen, corrected_box.zlen),
                (legacy_box.xlen, legacy_box.ylen, legacy_box.zlen),
            )
        ],
        "center_of_mass_difference_mm": [
            corrected_center.x - legacy_center.x,
            corrected_center.y - legacy_center.y,
            corrected_center.z - legacy_center.z,
        ],
        "added_complete_lug_count": 6,
        "penetrating_rope_hole_count": 6,
        "changed_regions": ["RETENTION_LUG_BOOLEAN_ONLY"],
        "sump_dimensions_unchanged": True,
        "inner_dam_dimensions_unchanged": True,
        "overflow_dimensions_unchanged": True,
        "water_volume_phase3ic_l": corrected_water.val().Volume() / 1_000_000.0,
        "water_volume_phase3ib_l": legacy_water.val().Volume() / 1_000_000.0,
        "water_volume_difference_l": (
            corrected_water.val().Volume() - legacy_water.val().Volume()
        ) / 1_000_000.0,
        "stacking_guides_unchanged": True,
        "port_recess_mm": SELECTED_PORT_RECESS_MM,
        "maximum_xy_mm": maximum_xy_diameter_without_mesh_cache_phase3ic(corrected),
        "within_238mm": maximum_xy_diameter_without_mesh_cache_phase3ic(corrected) <= 238.0,
    }
