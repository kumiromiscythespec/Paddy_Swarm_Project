"""Machine-readable Phase 3S-A.1 print quantities and gates."""

from __future__ import annotations

from ps_mht_v001.parameters import (
    phase3sa_seam_clearance_candidates,
    phase3sa_seam_clearance_selected,
)
from ps_mht_v001.print_plate_layout_phase3sa1 import (
    selected_plate_file_names_phase3sa1,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    validate_seam_clearance_phase3sa,
)


STATUS = "PHASE3SA1_SELECTED_SEAM_PLATES_NOT_GENERATED_BEFORE_SELECTION"
ADDITIONAL_RING_FILE = (
    "ps_mht_v001_temporary_panel_capture_ring_additional_phase3sa1.stl"
)


def _candidate_file_names(plate_number: int) -> list[str]:
    return [
        selected_plate_file_names_phase3sa1(value)[plate_number - 2]
        for value in phase3sa_seam_clearance_candidates
    ]


def build_print_manifest_phase3sa1(
    selected_clearance: float | None = None,
) -> dict[str, object]:
    """Return a gated manifest; None never resolves to 0.6 mm."""

    selected = (
        None
        if selected_clearance is None
        else validate_seam_clearance_phase3sa(selected_clearance)
    )
    selected_names = (
        None
        if selected is None
        else selected_plate_file_names_phase3sa1(selected)
    )

    def selected_item(
        plate_number: int,
        prerequisite: str,
        print_status: str,
        assembly_use: str,
        do_not_print_before: str,
    ) -> dict[str, object]:
        return {
            "file_name": (
                None
                if selected_names is None
                else selected_names[plate_number - 2]
            ),
            "quantity": 1,
            "prerequisite": prerequisite,
            "selected_clearance": selected,
            "print_status": (
                "NOT_GENERATED_CLEARANCE_SELECTION_REQUIRED"
                if selected is None
                else print_status
            ),
            "assembly_use": assembly_use,
            "do_not_print_before": do_not_print_before,
            "candidate_file_names": _candidate_file_names(plate_number),
        }

    items = [
        {
            "file_name": "plate_01_sector_seam_coupons_phase3sa1.stl",
            "quantity": 1,
            "prerequisite": None,
            "selected_clearance": None,
            "print_status": "READY_TO_PRINT_FIRST",
            "assembly_use": "SELECT_VERTICAL_SEAM_CLEARANCE",
            "do_not_print_before": None,
        },
        selected_item(
            2,
            "PLATE_01_PASS_AND_SEAM_CLEARANCE_SELECTED",
            "GENERATE_AND_PRINT_SELECTED_CLEARANCE_ONLY",
            "CAPTURE_FIT_COUPON_AND_FIRST_OF_TWO_CAPTURE_RINGS",
            "SEAM_CLEARANCE_SELECTED",
        ),
        selected_item(
            3,
            "SELECTED_PLATE_02_PASS",
            "PRINT_AFTER_SELECTED_PLATE_02_PASS",
            "FULL_HEIGHT_SINGLE_PANEL_PRINT_GATE",
            "SELECTED_PLATE_02_PASS",
        ),
        {
            "file_name": ADDITIONAL_RING_FILE,
            "quantity": 1,
            "prerequisite": "SELECTED_PLATE_03_PASS",
            "selected_clearance": selected,
            "print_status": "GENERATED_HOLD_UNTIL_PLATE_03_PASS",
            "assembly_use": "SECOND_OF_TWO_CAPTURE_RINGS",
            "do_not_print_before": "SELECTED_PLATE_03_PASS",
            "clearance_dependency": False,
        },
        selected_item(
            4,
            "SELECTED_PLATE_03_PASS_AND_SECOND_RING_AVAILABLE",
            "PRINT_AFTER_PLATE_03_PASS_AND_SECOND_RING",
            "THREE_IDENTICAL_SHORT_CALIBRATION_PANELS",
            "SELECTED_PLATE_03_PASS_AND_SECOND_RING_AVAILABLE",
        ),
    ]
    return {
        "project": "PS-MHT-V001",
        "phase": "3S-A.1",
        "status": STATUS,
        "phase3sa_seam_clearance_selected_parameter":
            phase3sa_seam_clearance_selected,
        "selected_clearance": selected,
        "selection_policy":
            "EXPLICIT_0.4_0.6_OR_0.8_REQUIRED_NO_DEFAULT",
        "print_items": items,
        "temporary_capture_ring_quantity": {
            "required_for_short_assembly": 2,
            "included_in_selected_plate_02": 1,
            "additional_single_stl": 1,
            "quantity_reconciled": True,
        },
        "recommended_workflow": [
            "1_PRINT_PLATE_01",
            "2_SELECT_SEAM_CLEARANCE",
            "3_REGENERATE_AND_PRINT_SELECTED_PLATE_02",
            "4_PRINT_SELECTED_PLATE_03_AFTER_PLATE_02_PASS",
            "5_PRINT_ONE_ADDITIONAL_CAPTURE_RING_AFTER_PLATE_03_PASS",
            "6_PRINT_SELECTED_PLATE_04",
            "7_BUILD_SHORT_THREE_PANEL_ASSEMBLY",
        ],
    }
