"""Machine-readable Phase 3I-C entry, review, and authorization state."""

from __future__ import annotations


PHASE3IC_PROCESS_NAME = "PHASE_3IC_ENVELOPE_NEUTRAL_POT_RETENTION_AND_FLOATING_REGION_ISOLATION"
PHASE3IC_NORMAL_COMPLETION_STATUS_LINES = (
    "PHASE3IB_RETENTION_BOOLEAN_DEFECT_RECORDED",
    "PHASE3IB_ARTIFACTS_FROZEN",
    "PHASE3IC_CORRECTED_FULL_AUTHORITY_CREATED",
    "COMPLETE_RETENTION_LUGS_IMPLEMENTED",
    "ENVELOPE_NEUTRAL_KEEPER_V2_READY",
    "PROGRESSIVE_DIAGNOSTIC_STLS_READY",
    "BAMBU_STUDIO_DIAGNOSTIC_PENDING",
    "PHYSICAL_PRINT_PENDING",
)

PHASE3IC_STATUS = "CORRECTED_FULL_AUTHORITY_IMPLEMENTED_PHYSICAL_REVIEW_PENDING"
PHASE3IC_STATUS_LINES = (
    "PHASE3IB_RETENTION_BOOLEAN_DEFECT_RECORDED",
    "PHASE3IB_ARTIFACTS_FROZEN",
    "PHASE3IC_CORRECTED_FULL_AUTHORITY_CREATED",
    "COMPLETE_RETENTION_LUGS_IMPLEMENTED",
    "ENVELOPE_NEUTRAL_KEEPER_V2_READY",
    "PROGRESSIVE_DIAGNOSTIC_STLS_READY",
    "BAMBU_STUDIO_DIAGNOSTIC_PENDING",
    "PHYSICAL_PRINT_PENDING",
)

PHASE3IC_CONFLICT = {
    "id": "PHASE3IB_RETENTION_LUG_BOOLEAN_NOT_IN_FULL_AUTHORITY",
    "d02_to_d03_actual_volume_increment_mm3": 0.021438298164866865,
    "intended_complete_lug_addition_mm3": 85367.31804521475,
    "lug_fraction_present_per_port": 0.2888932,
    "rope_hole_cut_volume_present_in_full_mm3": 0.0,
    "corrected_d03_delta_to_phase3ib_full_mm3": 52050.25134037493,
    "requirements_in_conflict": [
        "D03_MUST_INCLUDE_COMPLETE_RETENTION_LUGS_AND_TEARDROP_HOLES",
        "D05_MUST_EQUAL_UNCHANGED_PHASE3IB_FULL",
        "PROGRESSION_MUST_ONLY_ADD_FEATURES",
        "PHASE3IB_SHA_MUST_REMAIN_UNCHANGED",
    ],
    "required_authorization": "CORRECT_PHASE3IB_RETENTION_BOOLEAN_OR_REBASE_D05_AUTHORITY",
    "resolution": "RESOLVED_BY_USER_WITHDRAWAL_OF_D05_EQUALS_PHASE3IB_REQUIREMENT",
}

PHASE3IB_FROZEN_BASELINE = {
    "status": "HISTORICAL_FAILED_BASELINE",
    "official_artifacts_count": 46,
    "mutation": "PROHIBITED",
    "sha_change": "PROHIBITED",
    "retention_lug_boolean": {
        "intended": "SIX_COMPLETE_LUGS",
        "actual_increment_mm3": 0.021438298164866865,
        "result": "FAILED_OR_NEAR_TANGENTIAL_FUSE",
    },
}

PHASE3IB_REVIEW = {
    "cad_geometry": "PASS",
    "real_annular_sump": "CAD_PASS",
    "continuous_inner_dam": "PASS",
    "rear_overflow": "CAD_PASS",
    "pot_retention_interface": "CAD_PASS_PENDING_PHYSICAL",
    "full_stage_bambu_review": "FAIL_FLOATING_REGION_WARNING",
    "full_stage_print": "PROHIBITED",
    "physical_sump_test": "PENDING",
    "physical_pot_retention_test": "PENDING",
}

BAMBU_STUDIO_DIAGNOSTIC_STATUS = "PENDING"
FLOATING_REGION_SOURCE_IDENTIFIED = False
FLOATING_REGION_FIXED = False
FULL_STAGE_PRINT_APPROVED = False
NETPOT_RETENTION_PASS = False
SUMP_WATERTIGHT = False
OVERFLOW_PASS = False
PRODUCTION_READY = False
FULL_STAGE_GEOMETRY_CORRECTION_AUTHORIZED = True

MODULE_HEIGHT_MM = 170.0
NOMINAL_BODY_OUTER_DIAMETER_MM = 200.0
MAXIMUM_TOTAL_XY_ENVELOPE_MM = 238.0
PORT_RECESS_MM = 2.0

PHASE3IB_SUMP_FROZEN = {
    "central_clear_opening_diameter_mm": 100.0,
    "inner_dam_inner_diameter_mm": 100.0,
    "inner_dam_outer_diameter_mm": 109.6,
    "inner_dam_top_z_mm": 31.0,
    "sump_floor_top_z_mm": 4.0,
    "selected_water_depth_mm": 22.0,
    "selected_water_surface_z_mm": 26.0,
    "calculated_retained_volume_l": 0.3848264183344072,
    "rear_weir_width_mm": 30.0,
    "rear_weir_crest_z_mm": 26.0,
}
