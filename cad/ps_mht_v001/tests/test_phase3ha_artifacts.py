"""Generated artifact, non-regression and no-Git tests (5)."""

import json
from pathlib import Path

from ps_mht_v001.common.phase3ha_nonregression import (
    audit_existing_before_phase3ha,
)
from ps_mht_v001.common.validation import (
    validate_step_round_trip,
    validate_stl_mesh,
)


PACKAGE_ROOT = Path(__file__).parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"
STEP_ROOT = EXPORT_ROOT / "step"
STL_ROOT = EXPORT_ROOT / "stl"
PREVIEW_ROOT = EXPORT_ROOT / "preview"


def test_phase3ha_all_generated_steps_round_trip_valid() -> None:
    expected = {
        "horizontal_joint_arc_coupon_c030_phase3ha.step": 2,
        "horizontal_joint_arc_coupon_c050_phase3ha.step": 2,
        "horizontal_joint_arc_coupon_c070_phase3ha.step": 2,
        "full_ring_joint_pair_c050_reference_phase3ha.step": 2,
        "horizontal_joint_compression_ring_phase3ha.step": 1,
        "horizontal_joint_compression_assembly_reference_phase3ha.step": 19,
        "temporary_test_membrane_reference_phase3ha.step": 1,
    }
    for name, solid_count in expected.items():
        metrics = validate_step_round_trip(STEP_ROOT / name, solid_count)
        assert metrics.all_solids_valid


def test_phase3ha_all_print_stls_are_closed_manifold() -> None:
    for name in (
        "horizontal_joint_arc_coupon_c030_phase3ha.stl",
        "horizontal_joint_arc_coupon_c050_phase3ha.stl",
        "horizontal_joint_arc_coupon_c070_phase3ha.stl",
        "horizontal_joint_compression_ring_phase3ha.stl",
    ):
        assert validate_stl_mesh(STL_ROOT / name).closed_manifold


def test_phase3ha_stl_connected_component_counts_match_parts() -> None:
    expected = {
        "horizontal_joint_arc_coupon_c030_phase3ha.stl": 2,
        "horizontal_joint_arc_coupon_c050_phase3ha.stl": 2,
        "horizontal_joint_arc_coupon_c070_phase3ha.stl": 2,
        "horizontal_joint_compression_ring_phase3ha.stl": 1,
    }
    for name, component_count in expected.items():
        assert (
            validate_stl_mesh(STL_ROOT / name).connected_component_count
            == component_count
        )


def test_phase3ha_existing_artifact_sha_is_unchanged() -> None:
    report = audit_existing_before_phase3ha(EXPORT_ROOT, PACKAGE_ROOT)
    assert all(item["unchanged"] for item in report.values())
    assert sum(
        len(item["expected"])
        for name, item in report.items()
        if name != "phase3cb0_sources"
    ) == 207


def test_phase3ha_report_records_no_git_operation() -> None:
    report = json.loads(
        (PREVIEW_ROOT / "phase3ha_validation_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["git"]["commands_executed"] == []
    assert report["git"]["mutation_operations_performed"] is False
