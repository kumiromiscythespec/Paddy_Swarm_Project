"""Machine-readable physical and workflow state for Phase 3H-B."""

from __future__ import annotations


PHASE3HB_STATUS = (
    "C050_ARC_PHYSICAL_PASS_RECORDED_"
    "FULL_RING_PRINT_ARTIFACTS_READY_"
    "FULL_RING_PHYSICAL_VALIDATION_PENDING"
)

phase3ha_arc_candidate_selected = "C050"
phase3ha_arc_radial_clearance_mm = 0.50
phase3ha_preferred_pairing_orientation = "HOLE_1"
phase3ha_arc_physical_status = "PASS"
phase3ha_arc_cad_radius_correction = "NOT_REQUIRED"
phase3ha_arc_exact_cycle_count = "NOT_RECORDED"

production_horizontal_joint_clearance_selected = None
production_selection_status = "FULL_RING_PHYSICAL_VALIDATION_PENDING"
full_ring_physical_status = "PENDING"
compression_ring_physical_status = "PENDING"
water_leak_status = "PENDING"
temporary_test_membrane_status = "REFERENCE_ONLY"

FULL_RING_CLEARANCE_MM = 0.50
PREFERRED_PAIRING_IS_PHYSICAL_RECORD_ONLY = True
HOLE_OR_KEY_ADDED_TO_FULL_RING = False

LOWER_PRINT_ORIENTATION = "ASSEMBLY_Z_RECEIVER_AND_HARD_STOP_UP"
UPPER_PRINT_ORIENTATION = "ASSEMBLY_ORIENTATION_ROTATED_X_180_SKIRT_UP"
SIDEWAYS_PRINT_ALLOWED = False
ANGLED_PRINT_ALLOWED = False
AUTOMATIC_SUPPORT_ALLOWED = False
RING_SPLIT_ALLOWED = False
SECTORIZATION_ALLOWED = False
AUXILIARY_FEET_COUNT = 0
CAD_BRIM_COUNT = 0
SLICER_BRIM_OPTION_MM = (5.0, 8.0)


def phase3ha_arc_physical_result_phase3hb() -> dict[str, object]:
    return {
        "candidate": phase3ha_arc_candidate_selected,
        "radial_clearance_mm": phase3ha_arc_radial_clearance_mm,
        "preferred_pairing_orientation": phase3ha_preferred_pairing_orientation,
        "assembly_direction": "PASS",
        "light_finger_alignment": "PASS",
        "repeated_attachment": "PASS",
        "whitening": "NONE_REPORTED",
        "cracking": "NONE_REPORTED",
        "abnormal_abrasion": "NONE_REPORTED",
        "strong_reaction": "NONE_REPORTED",
        "self_separation": "NONE_REPORTED",
        "user_check_items_1_to_5": "ALL_PASS",
        "free_arc_springback": {
            "present": True,
            "severity": "LIGHT",
            "disposition": "ACCEPTABLE",
        },
        "cad_radius_correction": phase3ha_arc_cad_radius_correction,
        "status": phase3ha_arc_physical_status,
        "exact_cycle_count": phase3ha_arc_exact_cycle_count,
    }


def production_selection_state_phase3hb() -> dict[str, object]:
    return {
        "horizontal_joint_clearance_mm":
            production_horizontal_joint_clearance_selected,
        "status": production_selection_status,
        "full_ring_physical_status": full_ring_physical_status,
        "compression_ring_physical_status": compression_ring_physical_status,
        "water_leak_status": water_leak_status,
    }
