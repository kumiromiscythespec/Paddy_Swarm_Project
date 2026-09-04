"""Machine-readable Phase 3I-A failure and Phase 3I-B entry state."""

from __future__ import annotations


PHASE3IB_PROCESS_NAME = "PHASE_3IB_INTEGRATED_WET_BASE_FUNCTIONAL_CORRECTION"
PHASE3IB_STATUS_LINES = (
    "PHASE3IA_FAILURE_RECORDED",
    "REAL_ANNULAR_SUMP_IMPLEMENTED",
    "SELF_SUPPORTING_CRADLE_IMPLEMENTED",
    "NETPOT_RETENTION_INTERFACE_IMPLEMENTED",
    "FULL_STL_READY_FOR_BAMBU_STUDIO_REVIEW",
    "FUNCTIONAL_COUPONS_READY_AFTER_SLICER_REVIEW",
    "PHYSICAL_PRINT_PENDING",
)

PHASE3IA_SLICER_REVIEW = {
    "floating_region_warning": "PRESENT",
    "tree_support_dependency": "PRESENT",
    "pot_positive_retention": "ABSENT",
    "continuous_inner_sump_dam": "ABSENT",
    "actual_water_retention": "FAIL",
    "status": "FAILED_SLICER_AND_FUNCTIONAL_REVIEW",
}

PHASE3IA_PRINT_DISPOSITION = {
    "full_stage": "PROHIBITED",
    "lower_60mm_coupon": "PROHIBITED",
}

BAMBU_STUDIO_REVIEW_STATUS = "PENDING"
PHYSICAL_PRINT_STATUS = "PENDING"
FULL_STAGE_PRINT_APPROVED = False
SUMP_WATERTIGHT = False
OVERFLOW_PASS = False
NETPOT_RETENTION_PASS = False
PLANT_READY = False
PRODUCTION_READY = False
READY_FOR_80_TOWERS = False

PRINT_ORIENTATION = "MODULE_AXIS_VERTICAL_Z_SUMP_FLOOR_ON_BUILD_PLATE"
SIDEWAYS_PRINTING_ALLOWED = False
SEGMENTATION_ALLOWED = False
AUTOMATIC_SUPPORT_DEPENDENCY_ALLOWED = False


def phase3ia_failure_record_phase3ib() -> dict[str, object]:
    return {
        "phase3ia_slicer_review": dict(PHASE3IA_SLICER_REVIEW),
        "phase3ia_print_disposition": dict(PHASE3IA_PRINT_DISPOSITION),
        "reported_0_385071_l_disposition": "VIRTUAL_VOLUME_NOT_ACTUAL_RETENTION_AUTHORITY",
        "phase3ia_artifacts": "PRESERVED_READ_ONLY_BY_SHA256",
    }

