"""Print sequencing and holds for Phase 3I-F."""


def build_print_manifest_phase3if() -> dict[str, object]:
    return {
        "project": "PS-MHT-V001",
        "phase": "3I-F",
        "plates": [
            {
                "plate": 1,
                "file_name": "plate_01_dry_core_puck_fit_coupons_phase3if.stl",
                "status": "READY_FIRST_LOW_COST_FIT_TEST",
                "print": True,
                "prerequisite": "MEASURE_CENTRAL_OPENING_AND_REFERENCE_MAST",
                "support": "OFF",
            },
            {
                "plate": 2,
                "file_name": "plate_02_bottom_centering_puck_HOLD_phase3if.stl",
                "status": "HOLD_UNTIL_PHYSICAL_FIT_SELECTED",
                "print": False,
                "reference_candidate_only": True,
                "selected_outer_diameter_mm": None,
            },
            {
                "plate": 3,
                "file_name": "plate_03_top_centering_cap_HOLD_phase3if.stl",
                "status": "HOLD_UNTIL_MAST_AND_FIT_SELECTED",
                "print": False,
                "reference_candidate_only": True,
                "selected_mast_clearance_mm": None,
            },
            {
                "plate": 4,
                "file_name": "plate_04_integrated_stage_full_SLICER_REVIEW_ONLY_phase3if.stl",
                "status": "SLICER_REVIEW_ONLY_DO_NOT_PRINT",
                "print": False,
            },
        ],
        "reference_only_not_printable": [
            "DRY_CORE_FRAME_ARCHITECTURE_REFERENCE",
            "FIVE_STAGE_DRY_CORE_FRAME_REFERENCE",
            "CENTRAL_2020_MAST_REFERENCE",
            "REAR_2020_POST_REFERENCE",
            "METAL_UPPER_AND_LOWER_BRACKET_REFERENCES",
        ],
        "historical": {
            "phase3id": "FROZEN_DO_NOT_PRINT",
            "phase3ie_60deg": "ABORTED_PARTIAL_SOURCE_NOT_FOR_ZIP",
            "legacy_local_minus_x_fixing": "SUPERSEDED_BY_NON_ROTATING_DRY_CORE_FRAME",
        },
        "bambu_studio_result": "PENDING",
        "physical_frame_validation": "PENDING",
    }

