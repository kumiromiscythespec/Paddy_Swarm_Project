"""Physical-inspection-gated print manifest for Phase 3H-B."""

from __future__ import annotations


def build_print_manifest_phase3hb() -> dict[str, object]:
    return {
        "project": "PS-MHT-V001",
        "phase": "3H-B",
        "production_horizontal_joint_clearance_selected": None,
        "items": [
            {
                "plate": "plate_01",
                "file_name": "plate_01_full_ring_lower_c050_phase3hb.stl",
                "part": "FULL_RING_LOWER_C050",
                "print_status": "READY_FIRST",
                "print_alone": True,
                "orientation": "RECEIVER_AND_HARD_STOP_UP",
                "automatic_support": False,
                "cad_brim": False,
                "optional_slicer_outer_brim_mm": [5, 8],
            },
            {
                "plate": "plate_02",
                "file_name": "plate_02_full_ring_upper_c050_phase3hb.stl",
                "part": "FULL_RING_UPPER_C050",
                "print_status": "READY_AFTER_PLATE_01_INSPECTION",
                "print_alone": True,
                "orientation": "SKIRT_AND_HARD_STOP_UP",
                "automatic_support": False,
                "cad_brim": False,
                "optional_slicer_outer_brim_mm": [5, 8],
            },
            {
                "plate": "plate_03",
                "file_name": "plate_03_compression_ring_HOLD_phase3hb.stl",
                "part": "COMPRESSION_RING",
                "print_status": "HOLD_UNTIL_FULL_RING_PAIR_PASS",
                "print_alone": True,
                "orientation": "FLAT_FULL_RING",
                "automatic_support": False,
                "cad_brim": False,
            },
        ],
        "candidate_disposition": {
            "c030": "NOT_REQUIRED",
            "c050": "FULL_RING_MECHANICAL_VALIDATION_CANDIDATE",
            "c070": "NOT_REQUIRED",
        },
        "reference_only": [
            "ps_mht_v001_full_ring_pair_c050_reference_phase3hb.step",
            "temporary_test_membrane_reference_phase3ha.step",
        ],
        "temporary_test_membrane_status": "REFERENCE_ONLY",
        "water_test_status": "PENDING",
        "compression_ring_release_is_automatic": False,
    }
