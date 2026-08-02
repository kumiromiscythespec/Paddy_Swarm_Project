"""Material-saving print order for Phase 3P-A physical fit coupons."""

from __future__ import annotations

from ps_mht_v001.parameters import (
    netpot_body_passage_preferred_precalibration,
    netpot_body_passage_selected,
    phase3sa_seam_clearance_selected,
)


STATUS = "PHASE3PA_PHYSICAL_FIT_CALIBRATION_PENDING"


def build_print_manifest_phase3pa() -> dict[str, object]:
    return {
        "project": "PS-MHT-V001",
        "phase": "3P-A",
        "status": STATUS,
        "selected_passage_mm": netpot_body_passage_selected,
        "preferred_precalibration_mm":
            netpot_body_passage_preferred_precalibration,
        "phase3sa_seam_clearance_selected":
            phase3sa_seam_clearance_selected,
        "print_items": [
            {
                "file_name": "plate_01_netpot_fit_c805_phase3pa.stl",
                "quantity": 1,
                "print_status": "READY_FIRST",
                "prerequisite": None,
            },
            {
                "file_name": "plate_02_netpot_fit_c800_phase3pa.stl",
                "quantity": 1,
                "print_status": "CONDITIONAL",
                "prerequisite": "c805_too_loose",
            },
            {
                "file_name": "plate_03_netpot_fit_c810_phase3pa.stl",
                "quantity": 1,
                "print_status": "CONDITIONAL",
                "prerequisite": "c805_too_tight",
            },
        ],
        "recommended_order": ["c805", "c800_if_loose", "c810_if_tight"],
        "final_function_ring_included": False,
        "do_not_print": [
            "SIAWADEKY_REFERENCE_ENVELOPE",
            "FINAL_PORT_FUNCTION_RING",
            "FINAL_M4_EARS",
            "FINAL_PORT_BACKING_RING",
            "FINAL_NETPOT_LINER",
            "FINAL_120_DEGREE_PANEL_INTEGRATION",
            "FULL_170MM_MODULE",
            "THREE_PRODUCTION_PANELS",
            "FIVE_STAGE_TOWER",
        ],
    }
