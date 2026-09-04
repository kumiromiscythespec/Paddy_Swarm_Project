"""Phase 3I-D generated STEP/STL and print-status tests (7)."""

import json
from pathlib import Path

from ps_mht_v001.common.validation import validate_step_round_trip, validate_stl_mesh
from ps_mht_v001.coupons.interstage_cascade_coupon_phase3id import coupon_geometry_audit_phase3id
from ps_mht_v001.print_manifest_phase3id import build_print_manifest_phase3id


PACKAGE_ROOT = Path(__file__).parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def test_phase3id_corrected_full_step_round_trip_is_valid() -> None:
    path = EXPORT_ROOT / "step" / "ps_mht_v001_integrated_stage_full_corrected_phase3id.step"
    assert validate_step_round_trip(path, 1, True).all_solids_valid


def test_phase3id_corrected_full_stl_is_one_closed_component() -> None:
    path = EXPORT_ROOT / "stl" / "plate_01_integrated_stage_full_SLICER_REVIEW_ONLY_phase3id.stl"
    metrics = validate_stl_mesh(path)
    assert metrics.closed_manifold and metrics.connected_component_count == 1


def test_phase3id_both_coupon_steps_round_trip_valid() -> None:
    names = (
        "ps_mht_v001_upper_overflow_drop_chute_coupon_phase3id.step",
        "ps_mht_v001_lower_receiver_full_channel_coupon_phase3id.step",
    )
    assert all(validate_step_round_trip(EXPORT_ROOT / "step" / name, 1, True).all_solids_valid for name in names)
    assert coupon_geometry_audit_phase3id()["lower"]["dry_alignment_guide_count"] == 2


def test_phase3id_both_coupon_stls_are_closed_manifold() -> None:
    names = (
        "plate_02_upper_overflow_drop_chute_coupon_phase3id.stl",
        "plate_03_lower_receiver_full_channel_coupon_phase3id.stl",
    )
    assert all(validate_stl_mesh(EXPORT_ROOT / "stl" / name).closed_manifold for name in names)


def test_phase3id_d04d_d05d_meshes_are_closed_single_components() -> None:
    paths = sorted((EXPORT_ROOT / "stl" / "diagnostic_phase3id").glob("phase3id_diag_*.stl"))
    assert len(paths) == 2
    assert all(validate_stl_mesh(path).closed_manifold and validate_stl_mesh(path).connected_component_count == 1 for path in paths)


def test_phase3id_meshes_have_zero_bad_edges_and_degenerate_triangles() -> None:
    report = json.loads((EXPORT_ROOT / "preview" / "phase3id_validation_report.json").read_text(encoding="utf-8"))
    meshes = list(report["stl_mesh_validation"].values())
    assert all(item["boundary_or_nonmanifold_edge_count"] == 0 and item["degenerate_triangle_count"] == 0 for item in meshes)


def test_phase3id_full_and_diagnostics_remain_do_not_print() -> None:
    manifest = build_print_manifest_phase3id()
    assert manifest["full_stage"]["status"] == "SLICER_REVIEW_ONLY_DO_NOT_PRINT"
    assert all(not item["print"] for item in manifest["diagnostics"])
    assert manifest["bambu_studio_result"] == "PENDING"
