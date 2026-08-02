"""Selection-gated print manifest for Phase 3H-A."""

from __future__ import annotations

from ps_mht_v001.parameters import horizontal_joint_clearance_selected


def build_print_manifest_phase3ha() -> dict[str, object]:
    return {
        "project": "PS-MHT-V001",
        "phase": "3H-A",
        "selected_clearance_mm_per_side": horizontal_joint_clearance_selected,
        "selection_authority": "FULL_RING_PHYSICAL_TEST_ONLY",
        "print_items": [
            {
                "file_name": "horizontal_joint_arc_coupon_c050_phase3ha.stl",
                "quantity": 1,
                "candidate_clearance_mm_per_side": 0.5,
                "prerequisite": None,
                "selected_clearance": None,
                "print_status": "READY_FIRST",
                "assembly_use": "PRELIMINARY_INSERTION_AND_PRINTABILITY",
                "do_not_print_before": None,
            },
            {
                "file_name": "horizontal_joint_arc_coupon_c030_phase3ha.stl",
                "quantity": 1,
                "candidate_clearance_mm_per_side": 0.3,
                "prerequisite": "C050_ARC_TOO_LOOSE",
                "selected_clearance": None,
                "print_status": "CONDITIONAL_C050_TOO_LOOSE",
                "assembly_use": "PRELIMINARY_TIGHTER_CLEARANCE_CHECK",
                "do_not_print_before": "C050_ARC_RESULT",
            },
            {
                "file_name": "horizontal_joint_arc_coupon_c070_phase3ha.stl",
                "quantity": 1,
                "candidate_clearance_mm_per_side": 0.7,
                "prerequisite": "C050_ARC_TOO_TIGHT",
                "selected_clearance": None,
                "print_status": "CONDITIONAL_C050_TOO_TIGHT",
                "assembly_use": "PRELIMINARY_LOOSER_CLEARANCE_CHECK",
                "do_not_print_before": "C050_ARC_RESULT",
            },
            {
                "file_name": None,
                "quantity": 0,
                "candidate_clearance_mm_per_side": None,
                "prerequisite": "ARC_COUPON_PASS_AND_EXPLICIT_CLEARANCE",
                "selected_clearance": None,
                "print_status": "NOT_GENERATED_SELECTION_REQUIRED",
                "assembly_use": "FULL_RING_JOINT_PAIR_PHYSICAL_SELECTION",
                "do_not_print_before": "ARC_COUPON_PASS",
                "generator": "build_full_ring_joint_pair_phase3ha(clearance)",
                "reference_file_name":
                    "full_ring_joint_pair_c050_reference_phase3ha.step",
            },
            {
                "file_name": "horizontal_joint_compression_ring_phase3ha.stl",
                "quantity": 2,
                "candidate_clearance_mm_per_side": None,
                "prerequisite": "ARC_COUPON_PASS",
                "selected_clearance": None,
                "print_status": "PRINT_AFTER_ARC_PASS",
                "assembly_use": "TEST_FIXTURE_ONLY_COMMON_UPPER_LOWER",
                "do_not_print_before": "ARC_COUPON_PASS",
            },
        ],
        "reference_only_do_not_print": [
            "full_ring_joint_pair_c050_reference_phase3ha.step",
            "horizontal_joint_compression_assembly_reference_phase3ha.step",
            "temporary_test_membrane_reference_phase3ha.step",
        ],
        "production_fastener_selected": False,
        "final_module_generated": False,
    }
