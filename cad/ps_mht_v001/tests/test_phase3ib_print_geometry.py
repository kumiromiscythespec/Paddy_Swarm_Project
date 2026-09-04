"""Phase 3I-B printable STEP/STL, envelope, and gating tests (7)."""

import json
from pathlib import Path

import pytest

from ps_mht_v001.common.validation import validate_step_round_trip, validate_stl_mesh
from ps_mht_v001.print_manifest_phase3ib import build_print_manifest_phase3ib
from ps_mht_v001.reference.integrated_stage_references_phase3ib import assembly_reference_metadata_phase3ib
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ib import (
    MODULE_HEIGHT_MM,
    NOMINAL_BODY_OUTER_DIAMETER_MM,
    PORT_ANGLES_DEG,
    PORT_AXIS_ANGLE_DEG,
    PORT_COUNT,
    build_integrated_stage_full_phase3ib,
    overhang_audit_phase3ib,
    stage_geometry_requirements_phase3ib,
)


PACKAGE_ROOT = Path(__file__).parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def test_phase3ib_full_model_is_one_valid_solid() -> None:
    model = build_integrated_stage_full_phase3ib()
    assert len(model.solids().vals()) == 1 and model.val().isValid()


def test_phase3ib_fixed_full_dimensions_and_ports() -> None:
    geometry = stage_geometry_requirements_phase3ib()
    assert MODULE_HEIGHT_MM == 170.0
    assert NOMINAL_BODY_OUTER_DIAMETER_MM == 200.0
    assert geometry["full_envelope_bbox_mm"][2] == pytest.approx(170.0, abs=1e-5)
    assert PORT_COUNT == 3 and PORT_ANGLES_DEG == (0.0, 120.0, 240.0)
    assert PORT_AXIS_ANGLE_DEG == 27.0


def test_phase3ib_printed_and_installed_envelopes_are_at_most_238mm() -> None:
    geometry = stage_geometry_requirements_phase3ib()
    assert geometry["full_maximum_radial_xy_mm"] <= 238.0
    assert geometry["installed_netpot_maximum_xy_mm"] <= 238.0


def test_phase3ib_all_printable_steps_round_trip_valid() -> None:
    names = (
        "ps_mht_v001_integrated_stage_full_corrected_phase3ib.step",
        "ps_mht_v001_full_annular_sump_coupon_phase3ib.step",
        "ps_mht_v001_single_port_cradle_coupon_phase3ib.step",
        "ps_mht_v001_c_shaped_flange_keeper_phase3ib.step",
    )
    for name in names:
        assert validate_step_round_trip(EXPORT_ROOT / "step" / name, 1, True).all_solids_valid


def test_phase3ib_reference_steps_round_trip_valid() -> None:
    metadata = assembly_reference_metadata_phase3ib()
    expected = {
        "ps_mht_v001_integrated_stage_assembly_reference_phase3ib.step": metadata["assembly_solid_count"],
        "ps_mht_v001_actual_water_volume_reference_phase3ib.step": metadata["water_reference_solid_count"],
    }
    for name, count in expected.items():
        assert validate_step_round_trip(EXPORT_ROOT / "step" / name, count).all_solids_valid


def test_phase3ib_all_stls_are_closed_single_component_and_a1_sized() -> None:
    for path in sorted((EXPORT_ROOT / "stl").glob("*phase3ib.stl")):
        metrics = validate_stl_mesh(path)
        assert metrics.closed_manifold
        assert metrics.connected_component_count == 1
        assert metrics.boundary_or_nonmanifold_edge_count == 0
        assert metrics.size_x <= 245.0 and metrics.size_y <= 245.0 and metrics.size_z <= 240.0


def test_phase3ib_print_gates_and_cad_overhang_audit_are_conservative() -> None:
    manifest = build_print_manifest_phase3ib()
    assert manifest["items"][0]["status"] == "SLICER_REVIEW_ONLY_DO_NOT_PRINT"
    assert manifest["items"][1]["status"] == "READY_FIRST_AFTER_BAMBU_REVIEW"
    assert manifest["bambu_studio_review"] == "PENDING"
    overhang = overhang_audit_phase3ib()
    assert overhang["airborne_feature_count"] == 0
    assert overhang["horizontal_bridge_over_8mm_count"] == 0
    report = json.loads((EXPORT_ROOT / "preview" / "phase3ib_validation_report.json").read_text(encoding="utf-8"))
    assert all(item["degenerate_triangle_count"] == 0 for item in report["stl_mesh_validation"].values())

