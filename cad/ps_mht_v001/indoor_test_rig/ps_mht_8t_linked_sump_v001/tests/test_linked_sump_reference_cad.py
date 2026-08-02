"""REFERENCE CAD, STEP, zero-STL and non-regression tests (6)."""

import json
from pathlib import Path

from ps_mht_v001.common.validation import measure_shape, validate_step_round_trip
from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.reference_cad import (
    build_central_pump_well_reference,
    build_isolation_flow_reference_assembly,
    build_local_sump_reference_envelope,
    build_parallel_equalization_zone_4tower_reference,
    build_parallel_equalization_zone_8tower_reference,
    build_tower_support_deck_reference,
    local_sump_reference_metadata,
)


ROOT = Path(__file__).parents[1]
STEP_ROOT = ROOT / "exports" / "step"
PREVIEW_ROOT = ROOT / "exports" / "preview"


def test_all_six_reference_cad_builders_return_valid_solids() -> None:
    builders = (
        build_local_sump_reference_envelope,
        build_tower_support_deck_reference,
        build_parallel_equalization_zone_4tower_reference,
        build_parallel_equalization_zone_8tower_reference,
        build_central_pump_well_reference,
        build_isolation_flow_reference_assembly,
    )
    for builder in builders:
        metrics = measure_shape(builder())
        assert metrics.solid_count >= 1
        assert metrics.all_solids_valid


def test_local_sump_is_one_open_reference_envelope_at_420_320_120() -> None:
    metrics = measure_shape(build_local_sump_reference_envelope())
    assert metrics.solid_count == 1
    assert [metrics.size_x, metrics.size_y, metrics.size_z] == [420.0, 320.0, 120.0]
    metadata = local_sump_reference_metadata()
    assert metadata["open_skeletal_non_watertight_geometry"] is True
    assert metadata["bulkhead_hole_diameter_mm"] is None


def test_reference_component_counts_are_reported() -> None:
    report = json.loads(
        (PREVIEW_ROOT / "phase4tlsa_validation_report.json").read_text(encoding="utf-8")
    )
    assert len(report["reference_cad_metrics"]) == 6
    assert all(item["solid_count"] >= 1 for item in report["reference_cad_metrics"].values())


def test_all_six_reference_steps_round_trip_valid() -> None:
    report = json.loads(
        (PREVIEW_ROOT / "phase4tlsa_validation_report.json").read_text(encoding="utf-8")
    )
    for name, metrics in report["step_round_trip"].items():
        reread = validate_step_round_trip(STEP_ROOT / name, metrics["solid_count"])
        assert reread.all_solids_valid


def test_zero_stl_and_no_ready_first_print_item() -> None:
    assert not list((ROOT / "exports").rglob("*.stl"))
    manifest = json.loads(
        (PREVIEW_ROOT / "print_manifest_phase4tlsa.json").read_text(encoding="utf-8")
    )
    assert manifest["stl_output_count"] == 0
    assert all(item["print_status"] != "READY_FIRST" for item in manifest["items"])


def test_existing_sha_unchanged_and_no_git_mutation() -> None:
    report = json.loads(
        (PREVIEW_ROOT / "phase4tlsa_validation_report.json").read_text(encoding="utf-8")
    )
    assert report["non_regression"]["all_unchanged"] is True
    assert report["non_regression"]["artifact_count"] == 226
    assert report["git"]["mutation_operations_performed"] is False
