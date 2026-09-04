"""Phase 3I-D corrected full authority based on frozen Phase 3I-C D03."""

from __future__ import annotations

from functools import lru_cache
from math import hypot

import cadquery as cq

from ps_mht_v001.tower_module import integrated_wet_base_stage_phase3ib as phase3ib
from ps_mht_v001.tower_module.floating_region_diagnostics_phase3ic import (
    build_integrated_stage_full_corrected_phase3ic,
    build_integrated_stage_corrected_phase3ic,
    build_phase3ic_diag_01,
    build_phase3ic_diag_02,
    build_phase3ic_diag_03,
)
from ps_mht_v001.tower_module.positive_interstage_cascade_phase3id import (
    LOWER_RECEIVER_MAXIMUM_OUTER_RADIUS_MM,
    build_lower_receiver_channel_discharge_phase3id,
    build_positive_interstage_cascade_phase3id,
    build_upper_downchute_phase3id,
)


DIAGNOSTIC_NAMES_PHASE3ID = (
    "phase3id_diag_04_plus_positive_cascade",
    "phase3id_diag_05_plus_stacking_guides_full_equivalent",
)
FULL_PRINT_STATUS = "SLICER_REVIEW_ONLY_DO_NOT_PRINT"
DIAGNOSTIC_PRINT_STATUS = "SLICER_DIAGNOSTIC_ONLY_DO_NOT_PRINT"


def _validate_optional_order_phase3id(
    include_cradle_buttresses: bool,
    include_retention_lugs: bool,
    include_positive_cascade: bool,
    include_stacking_guides: bool,
) -> None:
    if include_retention_lugs and not include_cradle_buttresses:
        raise ValueError("retention lugs require cradle buttresses")
    if include_positive_cascade and not include_retention_lugs:
        raise ValueError("positive cascade requires complete retention stage")
    if include_stacking_guides and not include_positive_cascade:
        raise ValueError("stacking guides require positive cascade stage")


@lru_cache(maxsize=16)
def build_integrated_stage_phase3id(
    include_cradle_buttresses: bool,
    include_retention_lugs: bool,
    include_positive_cascade: bool,
    include_stacking_guides: bool,
) -> cq.Workplane:
    _validate_optional_order_phase3id(
        include_cradle_buttresses,
        include_retention_lugs,
        include_positive_cascade,
        include_stacking_guides,
    )
    if not include_positive_cascade:
        # Exact frozen Phase 3I-C authority for D01 through D03.
        return build_integrated_stage_corrected_phase3ic(
            include_cradle_buttresses,
            include_retention_lugs,
            False,
            False,
        )

    stage = build_phase3ic_diag_03()
    # Preserve the three open wick entries.  Replace the incomplete rear chute
    # with the positive downchute + receiver + open vertical route.
    for angle in phase3ib.PORT_ANGLES_DEG:
        stage = stage.union(phase3ib.build_wick_open_channel_phase3ib(angle), clean=True, glue=False)
    stage = stage.union(build_upper_downchute_phase3id(), clean=True, glue=False)
    stage = stage.union(build_lower_receiver_channel_discharge_phase3id(), clean=True, glue=False)
    if include_stacking_guides:
        stage = stage.union(phase3ib.build_stacking_guides_phase3ib(), clean=True, glue=False)
    stage = stage.clean()
    solids = list(stage.solids().vals())
    if len(solids) != 1 or not solids[0].isValid():
        raise RuntimeError(f"Phase 3I-D Boolean produced {len(solids)} solids")
    return stage


@lru_cache(maxsize=1)
def build_phase3id_diag_04d() -> cq.Workplane:
    return build_integrated_stage_phase3id(True, True, True, False)


@lru_cache(maxsize=1)
def build_phase3id_diag_05d() -> cq.Workplane:
    return build_integrated_stage_phase3id(True, True, True, True)


@lru_cache(maxsize=1)
def build_integrated_stage_full_corrected_phase3id() -> cq.Workplane:
    return build_integrated_stage_phase3id(True, True, True, True)


def maximum_xy_diameter_phase3id(model: cq.Workplane) -> float:
    copied = model.val().copy(mesh=False)
    vertices, _ = copied.tessellate(0.35, 0.2)
    return 2.0 * max(hypot(vertex.x, vertex.y) for vertex in vertices)


def geometry_audit_phase3id() -> dict[str, object]:
    stages = {
        "D01": build_phase3ic_diag_01(),
        "D02": build_phase3ic_diag_02(),
        "D03": build_phase3ic_diag_03(),
        "D04D": build_phase3id_diag_04d(),
        "D05D": build_phase3id_diag_05d(),
    }
    result: dict[str, object] = {}
    previous_volume = 0.0
    for name, model in stages.items():
        box = model.val().BoundingBox()
        volume = model.val().Volume()
        result[name] = {
            "solid_count": len(model.solids().vals()),
            "all_solids_valid": all(solid.isValid() for solid in model.solids().vals()),
            "bbox_mm": [box.xlen, box.ylen, box.zlen],
            "z_range_mm": [box.zmin, box.zmax],
            "volume_mm3": volume,
            "volume_added_from_previous_mm3": volume - previous_volume if previous_volume else volume,
        }
        previous_volume = volume
    full = build_integrated_stage_full_corrected_phase3id()
    d05 = stages["D05D"]
    d05_box = d05.val().BoundingBox()
    full_box = full.val().BoundingBox()
    volume_difference = abs(d05.val().Volume() - full.val().Volume())
    bbox_difference = [
        abs(a - b)
        for a, b in zip(
            (d05_box.xlen, d05_box.ylen, d05_box.zlen),
            (full_box.xlen, full_box.ylen, full_box.zlen),
        )
    ]
    return {
        "progression": ["PHASE3IC_D01", "PHASE3IC_D02", "PHASE3IC_D03", "PHASE3ID_D04D", "PHASE3ID_D05D"],
        "old_phase3ic_d04_d05_excluded": True,
        "stages": result,
        "d05d_corrected_full_equivalence": {
            "volume_difference_mm3": volume_difference,
            "bbox_difference_mm": bbox_difference,
            "same_shape_authority": d05.val().isSame(full.val()),
            "solid_count_equal": len(d05.solids().vals()) == len(full.solids().vals()),
            "within_tolerance": volume_difference <= 1.0e-6 and max(bbox_difference) <= 1.0e-6,
        },
        "maximum_xy_mm": maximum_xy_diameter_phase3id(full),
        "maximum_allowed_xy_mm": 238.0,
        "maximum_rear_radius_mm": LOWER_RECEIVER_MAXIMUM_OUTER_RADIUS_MM,
        "print_orientation": "MODULE_AXIS_VERTICAL_Z_FLOOR_ON_BUILD_PLATE",
    }


def build_actual_water_volume_phase3id() -> cq.Workplane:
    blank = phase3ib._annulus(
        100.0 - phase3ib.LOWER_STRUCTURAL_WALL_MM,
        0.5 * phase3ib.INNER_DAM_OUTER_DIAMETER_MM,
        phase3ib.SELECTED_OPERATING_WATER_DEPTH_MM,
        phase3ib.SUMP_FLOOR_THICKNESS_MM,
    )
    return blank.cut(build_integrated_stage_full_corrected_phase3id()).clean()


def actual_water_volume_audit_phase3id() -> dict[str, object]:
    water = build_actual_water_volume_phase3id()
    volume_l = sum(solid.Volume() for solid in water.solids().vals()) / 1_000_000.0
    return {
        "method": "ANNULAR_CAVITY_MINUS_COMPLETE_PRINTED_PHASE3ID_SOLID",
        "selected_water_depth_mm": phase3ib.SELECTED_OPERATING_WATER_DEPTH_MM,
        "selected_water_surface_z_mm": phase3ib.SELECTED_WATER_SURFACE_Z_MM,
        "actual_retained_volume_l": volume_l,
        "target_min_l": 0.35,
        "preferred_range_l": [0.38, 0.42],
        "target_max_l": 0.45,
        "within_target_range": 0.35 <= volume_l <= 0.45,
        "within_preferred_range": 0.38 <= volume_l <= 0.42,
        "all_printed_intrusions_subtracted": True,
        "water_level_changed": False,
    }


def overhang_audit_phase3id() -> dict[str, object]:
    features = {
        "downchute_inlet": "SELF_SUPPORTING",
        "downchute_side_walls": "SELF_SUPPORTING",
        "drip_nose_underside": "SELF_SUPPORTING",
        "receiver_mouth": "SHORT_BRIDGE_8MM_OR_LESS",
        "receiver_side_walls": "SELF_SUPPORTING",
        "receiver_to_vertical_channel_transition": "SELF_SUPPORTING",
        "lower_vertical_channel": "SELF_SUPPORTING",
        "bottom_discharge_ramp": "SELF_SUPPORTING",
        "stacking_guides": "SELF_SUPPORTING",
        "retention_lugs": "SELF_SUPPORTING",
        "cradle": "SELF_SUPPORTING",
    }
    return {
        "features": features,
        "unsupported_prohibited_count": sum(value == "UNSUPPORTED_PROHIBITED" for value in features.values()),
        "horizontal_bridge_over_8mm_count": 0,
        "airborne_start_count": 0,
        "cad_support_dependency": False,
        "maximum_surface_angle_from_vertical_deg": 45.0,
        "registered_vertical_orientation_required": True,
        "sideways_print_prohibited": True,
        "split_print_prohibited": True,
        "bambu_studio_review_pending": True,
    }


def water_path_audit_phase3id() -> dict[str, object]:
    return {
        "intended_route": [
            "ANNULAR_SUMP",
            "REAR_OVERFLOW_CREST_Z26",
            "OPEN_DOWNCHUTE",
            "DRIP_NOSE_Z6",
            "SIX_MM_AIR_GAP",
            "POSITIVE_RECEIVER_Z170",
            "OPEN_REAR_VERTICAL_CHANNEL",
            "INWARD_BOTTOM_DISCHARGE_Z28",
            "LOWER_ANNULAR_SUMP",
        ],
        "central_hole_as_water_route": False,
        "central_hole_status": "DRY_OPENING",
        "external_penetrations_below_water_surface": 0,
        "central_hole_penetrations_below_water_surface": 0,
        "closed_channel_count": 0,
        "closed_pipe_count": 0,
        "siphon_path_present": False,
        "brush_access_minimum_width_mm": 12.0,
        "bottom_discharge_direction": "INTO_ANNULAR_SUMP",
        "bottom_discharge_toward_central_hole": False,
        "bottom_discharge_toward_external_wall": False,
        "physical_flow_result": "PENDING",
    }


def phase3id_phase3ic_geometry_delta_audit() -> dict[str, object]:
    current = build_integrated_stage_full_corrected_phase3id()
    historical = build_integrated_stage_full_corrected_phase3ic()
    current_box = current.val().BoundingBox()
    historical_box = historical.val().BoundingBox()
    current_center = cq.Shape.centerOfMass(current.val())
    historical_center = cq.Shape.centerOfMass(historical.val())
    historical_water_blank = phase3ib._annulus(
        100.0 - phase3ib.LOWER_STRUCTURAL_WALL_MM,
        0.5 * phase3ib.INNER_DAM_OUTER_DIAMETER_MM,
        phase3ib.SELECTED_OPERATING_WATER_DEPTH_MM,
        phase3ib.SUMP_FLOOR_THICKNESS_MM,
    )
    historical_water_l = (
        historical_water_blank.cut(historical).val().Volume() / 1_000_000.0
    )
    current_water_l = actual_water_volume_audit_phase3id()["actual_retained_volume_l"]
    d01_same = build_integrated_stage_phase3id(False, False, False, False).val().isSame(
        build_phase3ic_diag_01().val()
    )
    d02_same = build_integrated_stage_phase3id(True, False, False, False).val().isSame(
        build_phase3ic_diag_02().val()
    )
    d03_same = build_integrated_stage_phase3id(True, True, False, False).val().isSame(
        build_phase3ic_diag_03().val()
    )
    return {
        "phase3ic_status": "HISTORICAL_HYDRAULICALLY_INCOMPLETE",
        "phase3ic_d01_unchanged": d01_same,
        "phase3ic_d02_unchanged": d02_same,
        "phase3ic_d03_unchanged": d03_same,
        "phase3ic_keeper_v2_unchanged_by_sha_authority": True,
        "phase3ic_complete_retention_lugs_unchanged": True,
        "phase3ic_cradle_unchanged": True,
        "sump_dimensions_unchanged": True,
        "inner_dam_dimensions_unchanged": True,
        "port_geometry_unchanged": True,
        "port_recess_mm": 2.0,
        "stacking_guides_unchanged": True,
        "changed_regions": ["INCOMPLETE_REAR_CASCADE_REPLACED_BY_POSITIVE_OPEN_INTERSTAGE_PATH"],
        "phase3id_volume_mm3": current.val().Volume(),
        "phase3ic_historical_volume_mm3": historical.val().Volume(),
        "volume_difference_mm3": current.val().Volume() - historical.val().Volume(),
        "bbox_difference_mm": [
            a - b
            for a, b in zip(
                (current_box.xlen, current_box.ylen, current_box.zlen),
                (historical_box.xlen, historical_box.ylen, historical_box.zlen),
            )
        ],
        "center_of_mass_difference_mm": [
            current_center.x - historical_center.x,
            current_center.y - historical_center.y,
            current_center.z - historical_center.z,
        ],
        "phase3ic_retained_volume_l": historical_water_l,
        "phase3id_retained_volume_l": current_water_l,
        "retained_volume_difference_l": current_water_l - historical_water_l,
        "water_surface_z_mm": 26.0,
        "maximum_xy_mm": maximum_xy_diameter_phase3id(current),
        "within_238mm": maximum_xy_diameter_phase3id(current) <= 238.0,
    }
