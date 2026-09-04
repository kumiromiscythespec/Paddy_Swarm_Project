"""Phase 3I-A generated artifact, SHA, test, and no-Git tests (6)."""

import json
from pathlib import Path

from ps_mht_v001.common.phase3ia_nonregression import audit_phase3ia_nonregression
from ps_mht_v001.common.validation import validate_step_round_trip, validate_stl_mesh


PACKAGE_ROOT = Path(__file__).parents[1]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def _report() -> dict[str, object]:
    return json.loads((EXPORT_ROOT / "preview" / "phase3ia_validation_report.json").read_text(encoding="utf-8"))


def test_phase3ia_all_steps_round_trip_valid() -> None:
    expected = {
        "ps_mht_v001_integrated_stage_full_reference_phase3ia.step": 1,
        "ps_mht_v001_integrated_stage_lower_60mm_coupon_phase3ia.step": 1,
        "ps_mht_v001_integrated_stage_assembly_reference_phase3ia.step": 9,
        "ps_mht_v001_integrated_stage_water_volume_reference_phase3ia.step": 4,
    }
    for name, count in expected.items():
        assert validate_step_round_trip(EXPORT_ROOT / "step" / name, count).all_solids_valid


def test_phase3ia_print_stls_are_closed_single_component_meshes() -> None:
    for name in (
        "plate_01_integrated_stage_full_SLICER_REVIEW_ONLY_phase3ia.stl",
        "plate_02_integrated_stage_lower_60mm_coupon_phase3ia.stl",
    ):
        metrics = validate_stl_mesh(EXPORT_ROOT / "stl" / name)
        assert metrics.closed_manifold
        assert metrics.boundary_or_nonmanifold_edge_count == 0
        assert metrics.connected_component_count == 1


def test_phase3ia_phase3h_and_netpot_calibration_sha_are_unchanged() -> None:
    audit = audit_phase3ia_nonregression(REPOSITORY_ROOT, EXPORT_ROOT)
    assert audit["phase3h_exports"]["unchanged"]
    assert audit["phase3pa_netpot_calibration_exports"]["unchanged"]
    assert audit["authoritative_sources"]["unchanged"]


def test_phase3ia_linked_sump_sha_is_unchanged() -> None:
    assert audit_phase3ia_nonregression(REPOSITORY_ROOT, EXPORT_ROOT)["linked_sump"]["unchanged"]


def test_phase3ia_report_records_existing_and_new_tests_passed() -> None:
    tests = _report()["automated_tests"]
    assert tests["existing_ps_mht"] == 366
    assert tests["linked_sump"] == 40
    assert tests["new_phase3ia"] == 48
    assert tests["total_passed"] == 454
    assert tests["all_passed"] is True


def test_phase3ia_report_records_no_git_mutation() -> None:
    git = _report()["git"]
    assert git["mutation_operations_performed"] is False
    assert git["prohibited_commands_executed"] == []
