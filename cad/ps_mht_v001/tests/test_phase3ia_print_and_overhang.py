"""Phase 3I-A print gate, overhang, and reference tests (8)."""

from ps_mht_v001 import phase3ia_state as state
from ps_mht_v001.print_manifest_phase3ia import build_print_manifest_phase3ia
from ps_mht_v001.reference.integrated_stage_references_phase3ia import (
    assembly_reference_metadata_phase3ia,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
    FULL_PRINT_STATUS,
    overhang_audit_phase3ia,
    stage_geometry_requirements_phase3ia,
)


def test_phase3ia_full_stl_is_slicer_review_only() -> None:
    assert FULL_PRINT_STATUS == "SLICER_REVIEW_ONLY_DO_NOT_PRINT"
    assert build_print_manifest_phase3ia()["items"][0]["status"] == FULL_PRINT_STATUS


def test_phase3ia_coupon_waits_for_slicer_review() -> None:
    item = build_print_manifest_phase3ia()["items"][1]
    assert item["status"] == "READY_FIRST_AFTER_SLICER_REVIEW"
    assert item["do_not_print_before"] == "BAMBU_STUDIO_REVIEW_PASS"


def test_phase3ia_vertical_orientation_is_fixed() -> None:
    assert state.PRINT_ORIENTATION == "MODULE_AXIS_VERTICAL_Z_SUMP_FLOOR_ON_BUILD_PLATE"


def test_phase3ia_sideways_tilt_and_segmentation_are_prohibited() -> None:
    assert not state.SIDEWAYS_PRINTING_ALLOWED
    assert not state.TILTED_PRINTING_ALLOWED
    assert not state.SEGMENTATION_ALLOWED


def test_phase3ia_automatic_support_dependency_is_prohibited() -> None:
    assert not state.AUTOMATIC_SUPPORT_DEPENDENCY_ALLOWED
    assert overhang_audit_phase3ia()["automatic_support_dependency"] is False


def test_phase3ia_overhang_audit_has_no_prohibited_feature() -> None:
    audit = overhang_audit_phase3ia()
    assert audit["unsupported_prohibited_count"] == 0
    assert set(audit["features"].values()) <= {"SELF_SUPPORTING_45_OR_LESS", "SHORT_BRIDGE_8MM_OR_LESS", "SLICER_REVIEW_REQUIRED"}


def test_phase3ia_reference_mass_is_preferred_and_below_review_threshold() -> None:
    mass = stage_geometry_requirements_phase3ia()["petg_reference_mass_g"]
    assert 650.0 <= mass <= 800.0
    assert mass < 900.0


def test_phase3ia_assembly_reference_records_coordinate_conversion() -> None:
    metadata = assembly_reference_metadata_phase3ia()
    assert metadata["reference_only"]
    assert metadata["coordinate_conversion"]["phase3ia_rear_service_direction"] == "-X"
    assert metadata["coordinate_conversion"]["rotation_about_z_deg"] == 90.0
