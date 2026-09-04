"""Print and review sequencing for Phase 3I-D."""

from __future__ import annotations


def build_print_manifest_phase3id() -> dict[str, object]:
    return {
        "project": "PS-MHT-V001",
        "phase": "3I-D",
        "full_stage": {
            "file_name": "plate_01_integrated_stage_full_SLICER_REVIEW_ONLY_phase3id.stl",
            "status": "SLICER_REVIEW_ONLY_DO_NOT_PRINT",
            "print": False,
        },
        "diagnostics": [
            {
                "stage": "D04D",
                "file_name": "phase3id_diag_04_plus_positive_cascade.stl",
                "status": "SLICER_DIAGNOSTIC_ONLY_DO_NOT_PRINT",
                "object_count_per_project": 1,
                "print": False,
            },
            {
                "stage": "D05D",
                "file_name": "phase3id_diag_05_plus_stacking_guides_full_equivalent.stl",
                "status": "SLICER_DIAGNOSTIC_ONLY_DO_NOT_PRINT",
                "object_count_per_project": 1,
                "print": False,
            },
        ],
        "coupons": [
            {
                "plate": 2,
                "file_name": "plate_02_upper_overflow_drop_chute_coupon_phase3id.stl",
                "status": "BAMBU_REVIEW_FIRST",
                "physical_print": "HOLD_UNTIL_SLICER_REVIEW_PASS",
                "support": "OFF",
                "orientation": "REGISTERED_VERTICAL",
            },
            {
                "plate": 3,
                "file_name": "plate_03_lower_receiver_full_channel_coupon_phase3id.stl",
                "status": "BAMBU_REVIEW_AFTER_UPPER_COUPON",
                "prerequisite": "PLATE_02_UPPER_COUPON_BAMBU_REVIEW_PASS",
                "physical_print": "HOLD_UNTIL_BOTH_SLICER_REVIEWS_PASS",
                "support": "OFF",
                "orientation": "REGISTERED_VERTICAL",
            },
        ],
        "bambu_review_order": [
            "PHASE3IC_D01",
            "PHASE3IC_D02",
            "PHASE3IC_D03",
            "PHASE3ID_D04D",
            "PHASE3ID_D05D",
            "UPPER_COUPON",
            "LOWER_COUPON",
        ],
        "old_phase3ic_d04_d05": "HISTORICAL_HYDRAULICALLY_INCOMPLETE_DO_NOT_USE",
        "phase3ic_corrected_full": "HISTORICAL_HYDRAULICALLY_INCOMPLETE_DO_NOT_PRINT",
        "bambu_studio_result": "PENDING",
        "hydraulic_flow_test": "PENDING",
    }
