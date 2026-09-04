"""Two-stage hydraulic, dry-opening, stream and rear-post references for Phase 3I-D."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
    build_installed_netpot_reference_phase3ia,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3id import (
    build_actual_water_volume_phase3id,
    build_integrated_stage_full_corrected_phase3id,
    maximum_xy_diameter_phase3id,
)
from ps_mht_v001.tower_module.positive_interstage_cascade_phase3id import (
    AIR_GAP_MM,
    DRIP_NOSE_TIP_RADIUS_MM,
    LOWER_RECEIVER_OUTER_RADIUS_MM,
    LOWER_RECEIVER_TOP_Z_MM,
    UPPER_DOWNCHUTE_OUTLET_TIP_Z_MM,
    build_lower_receiver_phase3id,
    build_upper_downchute_phase3id,
    build_water_stream_envelope_reference_phase3id,
    water_stream_envelope_audit_phase3id,
)


REFERENCE_ONLY = True
REAR_2020_POST_CENTER_X_MM = -150.0
REAR_2020_POST_SIZE_MM = 20.0


def _append_solids(items: list[cq.Shape], model: cq.Workplane) -> None:
    items.extend(model.solids().vals())


def build_rear_2020_post_reference_phase3id() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(REAR_2020_POST_SIZE_MM, REAR_2020_POST_SIZE_MM, 340.0, centered=(True, True, False))
        .translate((REAR_2020_POST_CENTER_X_MM, 0.0, 0.0))
    )


def build_central_dry_opening_reference_phase3id() -> cq.Workplane:
    return cq.Workplane("XY").circle(50.0).extrude(340.0)


def build_two_stage_interstage_cascade_assembly_reference_phase3id() -> cq.Workplane:
    lower = build_integrated_stage_full_corrected_phase3id()
    upper = build_integrated_stage_full_corrected_phase3id().translate((0.0, 0.0, 170.0))
    lower_water = build_actual_water_volume_phase3id()
    upper_water = build_actual_water_volume_phase3id().translate((0.0, 0.0, 170.0))
    stream = build_water_stream_envelope_reference_phase3id()
    dry_opening = build_central_dry_opening_reference_phase3id()
    post = build_rear_2020_post_reference_phase3id()
    items: list[cq.Shape] = []
    for model in (lower, upper, lower_water, upper_water, stream, dry_opening, post):
        _append_solids(items, model)
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(items)])


def two_stage_collision_audit_phase3id() -> dict[str, object]:
    lower = build_integrated_stage_full_corrected_phase3id()
    upper = build_integrated_stage_full_corrected_phase3id().translate((0.0, 0.0, 170.0))
    lower_receiver = build_lower_receiver_phase3id()
    upper_downchute = build_upper_downchute_phase3id().translate((0.0, 0.0, 170.0))
    post = build_rear_2020_post_reference_phase3id()
    pots = [build_installed_netpot_reference_phase3ia(angle) for angle in (0.0, 120.0, 240.0)]

    full_intersection = sum(solid.Volume() for solid in lower.intersect(upper).solids().vals())
    receiver_upper_intersection = sum(
        solid.Volume() for solid in lower_receiver.intersect(upper).solids().vals()
    )
    outlet_receiver_intersection = sum(
        solid.Volume() for solid in upper_downchute.intersect(lower_receiver).solids().vals()
    )
    receiver_post_intersection = sum(
        solid.Volume() for solid in lower_receiver.intersect(post).solids().vals()
    )
    receiver_pot_intersections = [
        sum(solid.Volume() for solid in lower_receiver.intersect(pot).solids().vals())
        for pot in pots
    ]
    air_gap = upper_downchute.val().BoundingBox().zmin - lower_receiver.val().BoundingBox().zmax
    stream_audit = water_stream_envelope_audit_phase3id()
    return {
        "lower_module_z_mm": [0.0, 170.0],
        "upper_module_z_mm": [170.0, 340.0],
        "upper_water_surface_global_z_mm": 196.0,
        "upper_outlet_tip_local_z_mm": UPPER_DOWNCHUTE_OUTLET_TIP_Z_MM,
        "upper_outlet_tip_global_z_mm": 170.0 + UPPER_DOWNCHUTE_OUTLET_TIP_Z_MM,
        "lower_receiver_top_global_z_mm": LOWER_RECEIVER_TOP_Z_MM,
        "nominal_air_gap_mm": AIR_GAP_MM,
        "measured_air_gap_mm": air_gap,
        "lower_upper_full_intersection_volume_mm3": full_intersection,
        "receiver_upper_bottom_intersection_volume_mm3": receiver_upper_intersection,
        "outlet_receiver_intersection_volume_mm3": outlet_receiver_intersection,
        "receiver_2020_post_intersection_volume_mm3": receiver_post_intersection,
        "receiver_netpot_intersection_volumes_mm3": receiver_pot_intersections,
        "receiver_netpot_clear": all(value <= 1.0e-7 for value in receiver_pot_intersections),
        "full_modules_clear": full_intersection <= 1.0e-7,
        "receiver_upper_bottom_clear": receiver_upper_intersection <= 1.0e-7,
        "outlet_receiver_clear": outlet_receiver_intersection <= 1.0e-7,
        "receiver_2020_post_clear": receiver_post_intersection <= 1.0e-7,
        "stream_envelope_captured": stream_audit["receiver_planar_envelope_contains_stream"],
        "central_dry_opening_clear": stream_audit["central_dry_opening_clear"],
        "drip_nose_centerline_radius_mm": DRIP_NOSE_TIP_RADIUS_MM,
        "receiver_outer_radius_mm": LOWER_RECEIVER_OUTER_RADIUS_MM,
        "maximum_xy_mm": maximum_xy_diameter_phase3id(lower),
        "within_238mm": maximum_xy_diameter_phase3id(lower) <= 238.0,
        "reference_only": True,
    }


def two_stage_reference_metadata_phase3id() -> dict[str, object]:
    reference = build_two_stage_interstage_cascade_assembly_reference_phase3id()
    return {
        "reference_only": True,
        "solid_count": len(reference.solids().vals()),
        "contains": [
            "LOWER_PHASE3ID_CORRECTED_FULL",
            "UPPER_PHASE3ID_CORRECTED_FULL_AT_Z_PLUS_170",
            "UPPER_OUTLET_AND_LOWER_RECEIVER",
            "SIX_MM_AIR_GAP",
            "LOWER_VERTICAL_CHANNEL_AND_SUMP",
            "TWO_SELECTED_WATER_VOLUME_REFERENCES",
            "CENTRAL_DRY_OPENING_REFERENCE",
            "WORST_CASE_FALLING_STREAM_ENVELOPE_REFERENCE",
            "REAR_2020_POST_REFERENCE",
        ],
    }

