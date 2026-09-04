"""Slicer-review-gated print manifest for Phase 3I-A."""

from __future__ import annotations


def build_print_manifest_phase3ia() -> dict[str, object]:
    return {
        "project": "PS-MHT-V001",
        "phase": "3I-A",
        "bambu_studio_review": "PENDING",
        "items": [
            {
                "file_name": "plate_01_integrated_stage_full_SLICER_REVIEW_ONLY_phase3ia.stl",
                "part": "INTEGRATED_STAGE_FULL",
                "status": "SLICER_REVIEW_ONLY_DO_NOT_PRINT",
                "orientation": "VERTICAL_Z_SUMP_FLOOR_ON_BUILD_PLATE",
                "single_object": True,
                "automatic_support_dependency": False,
                "do_not_print_before": "BAMBU_STUDIO_REVIEW_PASS",
            },
            {
                "file_name": "plate_02_integrated_stage_lower_60mm_coupon_phase3ia.stl",
                "part": "INTEGRATED_STAGE_LOWER_60MM_COUPON",
                "status": "READY_FIRST_AFTER_SLICER_REVIEW",
                "orientation": "VERTICAL_Z_SUMP_FLOOR_ON_BUILD_PLATE",
                "single_object": True,
                "automatic_support_dependency": False,
                "do_not_print_before": "BAMBU_STUDIO_REVIEW_PASS",
            },
        ],
        "not_printed": [
            "SECOND_COMPRESSION_RING",
            "COMPRESSION_RING_V2",
            "TEMPORARY_MEMBRANE",
            "ASSEMBLY_REFERENCE",
            "WATER_VOLUME_REFERENCE",
        ],
        "physical_state": {
            "full_stage_print_approved": False,
            "water_tight": False,
            "overflow_pass": False,
            "plant_ready": False,
            "production_ready": False,
        },
    }
