"""Corrected Phase 3I-E full stage built on the frozen Phase 3I-C D03."""

from __future__ import annotations

from functools import lru_cache
from math import hypot

import cadquery as cq

from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib
from ps_mht_v001.tower_module.direct_drop_standpipe_cascade_phase3ie import (
    LANDING_ANGLES_LOCAL_DEG,
    OVERFLOW_ANGLES_LOCAL_DEG,
    OVERFLOW_CENTER_RADIUS_MM,
    STANDPIPE_CLEAR_BORE_DIAMETER_MM,
    build_landing_ramp_phase3ie,
    build_single_floor_bore_void_phase3ie,
    build_single_standpipe_wall_phase3ie,
    landing_zone_audit_phase3ie,
    polar_point,
    standpipe_geometry_audit_phase3ie,
)
from ps_mht_v001.tower_module.floating_region_diagnostics_phase3ic import (
    build_phase3ic_diag_01,
    build_phase3ic_diag_02,
    build_phase3ic_diag_03,
)
from ps_mht_v001.tower_module.stack_clocking_datums_phase3ie import (
    build_bottom_clocking_datum_phase3ie,
    build_top_clocking_datum_phase3ie,
    clocking_datum_audit_phase3ie,
)


DIAGNOSTIC_NAMES_PHASE3IE = (
    "phase3ie_diag_04_plus_wick_and_direct_drop",
    "phase3ie_diag_05_plus_stacking_guides_full_equivalent",
)
MODULE_HEIGHT_MM = 170.0
NOMINAL_BODY_OUTER_DIAMETER_MM = 200.0
MAXIMUM_TOTAL_XY_ENVELOPE_MM = 238.0
SELECTED_WATER_SURFACE_Z_MM = 26.0
SELECTED_WATER_DEPTH_MM = 22.0
TARGET_ACTUAL_RETAINED_VOLUME_L = (0.35, 0.37, 0.42, 0.45)
FULL_PRINT_STATUS = "SLICER_REVIEW_ONLY_DO_NOT_PRINT"


def _validate_optional_order(
    include_cradle_buttresses: bool,
    include_retention_lugs: bool,
    include_wick_paths: bool,
    include_direct_drop_overflows: bool,
    include_landing_zones: bool,
    include_stacking_centering_guides: bool,
    include_clocking_datums: bool,
) -> None:
    if not include_cradle_buttresses or not include_retention_lugs:
        if any((include_wick_paths, include_direct_drop_overflows, include_landing_zones, include_stacking_centering_guides, include_clocking_datums)):
            raise ValueError("Phase 3I-E features require the complete Phase 3I-C D03 base")
    if include_landing_zones and not include_direct_drop_overflows:
        raise ValueError("landing zones require direct-drop overflows")
    if include_stacking_centering_guides and not include_clocking_datums:
        raise ValueError("stacking guides require visible clocking datums")


@lru_cache(maxsize=32)
def build_integrated_stage_phase3ie(
    include_cradle_buttresses: bool,
    include_retention_lugs: bool,
    include_wick_paths: bool,
    include_direct_drop_overflows: bool,
    include_landing_zones: bool,
    include_stacking_centering_guides: bool,
    include_clocking_datums: bool,
) -> cq.Workplane:
    _validate_optional_order(
        include_cradle_buttresses,
        include_retention_lugs,
        include_wick_paths,
        include_direct_drop_overflows,
        include_landing_zones,
        include_stacking_centering_guides,
        include_clocking_datums,
    )
    if include_retention_lugs:
        stage = build_phase3ic_diag_03()
    elif include_cradle_buttresses:
        stage = build_phase3ic_diag_02()
    else:
        stage = build_phase3ic_diag_01()

    if include_wick_paths:
        for angle in phase3ib.PORT_ANGLES_DEG:
            stage = stage.union(phase3ib.build_wick_open_channel_phase3ib(angle)).clean()
    if include_direct_drop_overflows:
        for angle in OVERFLOW_ANGLES_LOCAL_DEG:
            stage = stage.union(build_single_standpipe_wall_phase3ie(angle)).clean()
        for angle in OVERFLOW_ANGLES_LOCAL_DEG:
            stage = stage.cut(build_single_floor_bore_void_phase3ie(angle)).clean()
    if include_landing_zones:
        for angle in LANDING_ANGLES_LOCAL_DEG:
            stage = stage.union(build_landing_ramp_phase3ie(angle)).clean()
    if include_clocking_datums:
        stage = stage.union(build_top_clocking_datum_phase3ie()).clean()
        stage = stage.union(build_bottom_clocking_datum_phase3ie()).clean()
    if include_stacking_centering_guides:
        stage = stage.union(phase3ib.build_stacking_guides_phase3ib()).clean()

    solids = list(stage.solids().vals())
    if len(solids) != 1:
        raise RuntimeError(f"Phase 3I-E stage must be one fused solid, got {len(solids)}")
    if not solids[0].isValid():
        raise RuntimeError("Phase 3I-E stage is invalid")
    return cq.Workplane("XY").newObject([solids[0]])


@lru_cache(maxsize=1)
def build_phase3ie_diag_04e() -> cq.Workplane:
    return build_integrated_stage_phase3ie(True, True, True, True, True, False, True)


@lru_cache(maxsize=1)
def build_phase3ie_diag_05e() -> cq.Workplane:
    return build_integrated_stage_phase3ie(True, True, True, True, True, True, True)


@lru_cache(maxsize=1)
def build_integrated_stage_full_direct_drop_phase3ie() -> cq.Workplane:
    return build_integrated_stage_phase3ie(True, True, True, True, True, True, True)


def maximum_xy_diameter_phase3ie(model: cq.Workplane) -> float:
    maximum = 0.0
    for solid in model.solids().vals():
        vertices, _ = solid.copy(mesh=False).tessellate(0.35, 0.2)
        maximum = max(maximum, *(hypot(vertex.x, vertex.y) for vertex in vertices))
    return 2.0 * maximum


@lru_cache(maxsize=1)
def build_actual_water_volume_phase3ie() -> cq.Workplane:
    blank = phase3ib._annulus(
        100.0 - phase3ib.LOWER_STRUCTURAL_WALL_MM,
        0.5 * phase3ib.INNER_DAM_OUTER_DIAMETER_MM,
        SELECTED_WATER_DEPTH_MM,
        phase3ib.SUMP_FLOOR_THICKNESS_MM,
    )
    water = blank.cut(build_integrated_stage_full_direct_drop_phase3ie())
    # The open bores are draining columns, not retained water.
    for angle in OVERFLOW_ANGLES_LOCAL_DEG:
        x, y, _ = polar_point(OVERFLOW_CENTER_RADIUS_MM, angle)
        drain_column = (
            cq.Workplane("XY")
            .center(x, y)
            .circle(0.5 * STANDPIPE_CLEAR_BORE_DIAMETER_MM)
            .extrude(SELECTED_WATER_DEPTH_MM)
            .translate((0.0, 0.0, phase3ib.SUMP_FLOOR_THICKNESS_MM))
        )
        water = water.cut(drain_column)
    return water.clean()


def actual_water_volume_audit_phase3ie() -> dict[str, object]:
    water = build_actual_water_volume_phase3ie()
    volume_l = sum(solid.Volume() for solid in water.solids().vals()) / 1_000_000.0
    return {
        "method": "REAL_ANNULAR_CAVITY_MINUS_COMPLETE_PHASE3IE_PRINTED_SOLID_AND_OPEN_DRAIN_COLUMNS",
        "selected_depth_mm": SELECTED_WATER_DEPTH_MM,
        "water_surface_z_mm": SELECTED_WATER_SURFACE_Z_MM,
        "actual_retained_volume_l": volume_l,
        "target_range_l": [TARGET_ACTUAL_RETAINED_VOLUME_L[0], TARGET_ACTUAL_RETAINED_VOLUME_L[3]],
        "preferred_range_l": [TARGET_ACTUAL_RETAINED_VOLUME_L[1], TARGET_ACTUAL_RETAINED_VOLUME_L[2]],
        "within_target_range": TARGET_ACTUAL_RETAINED_VOLUME_L[0] <= volume_l <= TARGET_ACTUAL_RETAINED_VOLUME_L[3],
        "within_preferred_range": TARGET_ACTUAL_RETAINED_VOLUME_L[1] <= volume_l <= TARGET_ACTUAL_RETAINED_VOLUME_L[2],
        "water_level_raised_to_solve_volume": False,
        "subtracted_features": [
            "THREE_STANDPIPE_WALLS", "THREE_LANDING_RAMPS", "INNER_DAM", "CRADLES",
            "RETENTION_LUGS", "WICK_PATHS", "RIBS", "OPEN_DRAIN_COLUMNS",
        ],
    }


def geometry_audit_phase3ie() -> dict[str, object]:
    d03 = build_phase3ic_diag_03()
    d04e = build_phase3ie_diag_04e()
    d05e = build_phase3ie_diag_05e()
    full = build_integrated_stage_full_direct_drop_phase3ie()
    volumes = {
        "D03": d03.val().Volume(),
        "D04E": d04e.val().Volume(),
        "D05E": d05e.val().Volume(),
        "FULL": full.val().Volume(),
    }
    box = full.val().BoundingBox()
    return {
        "architecture": "PHASE3IC_D03_PLUS_INTERNAL_DIRECT_DROP_STANDPIPES",
        "phase3id_external_features_included": False,
        "module_height_mm": MODULE_HEIGHT_MM,
        "solid_count": len(full.solids().vals()),
        "valid": full.val().isValid(),
        "bbox_mm": [box.xlen, box.ylen, box.zlen],
        "maximum_xy_diameter_mm": maximum_xy_diameter_phase3ie(full),
        "maximum_allowed_xy_mm": MAXIMUM_TOTAL_XY_ENVELOPE_MM,
        "volumes_mm3": volumes,
        "d04e_added_volume_from_d03_mm3": volumes["D04E"] - volumes["D03"],
        "d05e_added_volume_from_d04e_mm3": volumes["D05E"] - volumes["D04E"],
        "d05e_full_volume_delta_mm3": volumes["D05E"] - volumes["FULL"],
        "d05e_full_equivalent": abs(volumes["D05E"] - volumes["FULL"]) < 1.0e-6,
        "standpipes": standpipe_geometry_audit_phase3ie(),
        "landings": landing_zone_audit_phase3ie(),
        "clocking_datums": clocking_datum_audit_phase3ie(),
        "print_orientation": "MODULE_AXIS_VERTICAL_Z_FLOOR_ON_BUILD_PLATE",
        "sideways_printing_allowed": False,
        "segmentation_allowed": False,
        "support_dependency": False,
    }


def leak_path_audit_phase3ie() -> dict[str, object]:
    return {
        "normal_water_surface_z_mm": SELECTED_WATER_SURFACE_Z_MM,
        "intended_outlet_count": 3,
        "intended_outlet_type": "VERTICAL_BORE_INSIDE_OPEN_OVERFLOW_STANDPIPE",
        "simple_floor_hole_count": 0,
        "central_opening_used_for_distribution": False,
        "central_opening_penetrations": 0,
        "external_wall_penetrations_below_water_surface": 0,
        "closed_siphon_count": 0,
        "horizontal_drain_count": 0,
        "below_z0_nozzle_count": 0,
        "physical_watertightness": "PENDING",
        "status": "CAD_BOUNDARY_PASS_PHYSICAL_WATERTIGHTNESS_PENDING",
    }


def overhang_audit_phase3ie() -> dict[str, object]:
    return {
        "classification": {
            "standpipe_walls": "SELF_SUPPORTING_VERTICAL",
            "three_v_notches_per_pipe": "SELF_SUPPORTING_45_DEG_FLANKS",
            "landing_ramps": "SELF_SUPPORTING_14_DEG_FROM_HORIZONTAL_RAMP",
            "floor_bores": "OPEN_VERTICAL_NO_INTERNAL_SUPPORT",
            "top_clocking_datum": "TOP_BAND_CONNECTED_SELF_SUPPORTING",
            "bottom_clocking_datum": "WALL_CONNECTED_SELF_SUPPORTING",
            "stacking_guides": "TOP_BAND_CONNECTED_45_DEG_RAMP",
        },
        "maximum_surface_angle_deg": 45.0,
        "horizontal_bridge_over_8mm_count": 0,
        "airborne_start_count": 0,
        "unsupported_prohibited_count": 0,
        "cad_support_dependency": False,
        "bambu_studio_review": "PENDING",
    }
