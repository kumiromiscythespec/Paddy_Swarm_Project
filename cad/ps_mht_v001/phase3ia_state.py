"""Machine-readable architecture and physical-entry state for Phase 3I-A."""

from __future__ import annotations


PHASE3IA_PROCESS_NAME = "PHASE_3IA_INTEGRATED_WET_BASE_MODULE"
PHASE3IA_STATUS_LINES = (
    "INTEGRATED_STAGE_ARCHITECTURE_COMPLETE",
    "FULL_STL_READY_FOR_BAMBU_STUDIO_REVIEW",
    "LOWER_60MM_COUPON_READY_AFTER_SLICER_REVIEW",
    "PHYSICAL_PRINT_PENDING",
)

INTERSTAGE_WATERTIGHT_REQUIRED = False
INTERSTAGE_INTERFACE = "DRY_POSITIONING_ONLY"
COMPRESSION_RING_V1_STATUS = "SUPERSEDED_BY_PHASE_3IA"
COMPRESSION_RING_V2_IMPLEMENTATION = False
SECOND_COMPRESSION_RING_PRINT_REQUIRED = False
FULL_STAGE_PRINT_APPROVED = False
WATER_TIGHT = False
OVERFLOW_PASS = False
PLANT_READY = False
PRODUCTION_READY = False

C050_DRY_STACKING_CLEARANCE_REFERENCE_MM_PER_SIDE = 0.50
C050_IS_WATERTIGHT_SELECTION = False

PRINT_ORIENTATION = "MODULE_AXIS_VERTICAL_Z_SUMP_FLOOR_ON_BUILD_PLATE"
SIDEWAYS_PRINTING_ALLOWED = False
TILTED_PRINTING_ALLOWED = False
SEGMENTATION_ALLOWED = False
AUTOMATIC_SUPPORT_DEPENDENCY_ALLOWED = False
BAMBU_STUDIO_REVIEW_STATUS = "BAMBU_STUDIO_REVIEW_PENDING"


def phase3h_physical_results_phase3ia() -> dict[str, object]:
    return {
        "c050_arc": {
            "radial_clearance_mm_per_side": 0.50,
            "assembly": "PASS",
            "repeated_cycles": "PASS_EXACT_COUNT_NOT_RECORDED",
            "springback": "LIGHT_ACCEPTABLE",
            "preferred_pairing_orientation": "HOLE_1",
            "whitening": "NONE",
            "cracking": "NONE",
        },
        "c050_full_ring": {
            "lower_receiver_inner_diameter_mm": {
                "deg_0": 194.0,
                "deg_45": 194.0,
                "deg_90": 194.0,
                "deg_135": 194.0,
            },
            "lower_outer_diameter_mm": {
                "deg_0": 200.0,
                "deg_45": 200.0,
                "deg_90": 201.0,
                "deg_135": 200.0,
            },
            "lower_outer_ovality_mm": 1.0,
            "upper_skirt_outer_diameter_mm": {
                "deg_0": 192.5,
                "deg_45": 193.0,
                "deg_90": 192.5,
                "deg_135": 192.5,
            },
            "upper_skirt_ovality_mm": 0.5,
            "repeated_cycles": 20,
            "whitening_after_cycles": "NONE",
            "cracking_after_cycles": "NONE",
            "abnormal_wear_after_cycles": "NONE",
            "mechanical_status": "PASS",
            "use_in_phase3ia": "DRY_STACKING_REFERENCE_ONLY",
        },
        "compression_ring_v1": {
            "printed_quantity": 1,
            "lateral_centering": "FAIL",
            "second_ring_print_required": False,
            "status": COMPRESSION_RING_V1_STATUS,
        },
    }
