"""Phase 3S-A.2 artifacts, manifest and non-regression gates."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from ps_mht_v001.common.phase3sa2_nonregression import (
    audit_phase1_through_phase3sa1,
)
from ps_mht_v001.common.validation import (
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.print_manifest_phase3sa2 import (
    build_print_manifest_phase3sa2,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def test_phase3sa2_steps_reload_valid() -> None:
    expected = {
        "ps_mht_v001_full_length_seam_pair_c040_phase3sa2.step": 2,
        "ps_mht_v001_full_length_seam_pair_c060_phase3sa2.step": 2,
        "ps_mht_v001_full_length_seam_capture_fixture_phase3sa2.step": 1,
        (
            "ps_mht_v001_full_length_seam_assembly_reference_"
            "c040_c060_phase3sa2.step"
        ): 8,
    }
    for name, count in expected.items():
        assert validate_step_round_trip(
            EXPORT_ROOT / "step" / name,
            count,
        ).all_solids_valid


def test_phase3sa2_stls_are_closed_with_expected_components() -> None:
    expected = {
        "ps_mht_v001_full_length_seam_pair_c040_phase3sa2.stl": 2,
        "ps_mht_v001_full_length_seam_pair_c060_phase3sa2.stl": 2,
        "ps_mht_v001_full_length_seam_capture_fixture_phase3sa2.stl": 1,
        "plate_01_full_length_seam_c040_phase3sa2.stl": 2,
        "plate_02_full_length_seam_c060_phase3sa2.stl": 2,
        "plate_03_full_length_seam_capture_fixtures_phase3sa2.stl": 2,
        "plate_optional_full_length_seam_c040_c060_phase3sa2.stl": 4,
    }
    for name, count in expected.items():
        metrics = validate_stl_mesh(EXPORT_ROOT / "stl" / name)
        assert metrics.closed_manifold
        assert metrics.connected_component_count == count


def test_manifest_keeps_selection_none_and_rejects_c080() -> None:
    manifest = build_print_manifest_phase3sa2()
    assert manifest["selected_clearance"] is None
    assert manifest["rejected_clearance"] == 0.8
    assert manifest["decision_rule"]["c080"] == "REJECTED_NO_RETEST"


def test_manifest_fixture_quantities_are_explicit() -> None:
    quantities = build_print_manifest_phase3sa2()["fixture_quantity"]
    assert quantities["sequential_reuse_total"] == 2
    assert quantities["simultaneous_c040_c060_total"] == 4
    assert quantities["fixtures_per_plate_03"] == 2


def test_phase1_through_phase3sa1_hashes_are_unchanged() -> None:
    audit = audit_phase1_through_phase3sa1(EXPORT_ROOT)
    assert all(item["unchanged"] for item in audit.values())
    assert len(audit["phase3sa1"]["actual"]) == 5


def test_delivery_zip_contains_manifest_report_and_print_plates() -> None:
    path = EXPORT_ROOT / "ps_mht_v001_phase3sa2_delivery.zip"
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
    assert "preview/print_manifest_phase3sa2.json" in names
    assert "preview/phase3sa2_validation_report.json" in names
    assert "stl/plate_01_full_length_seam_c040_phase3sa2.stl" in names
    assert "stl/plate_02_full_length_seam_c060_phase3sa2.stl" in names


def test_all_generated_phase3sa2_artifact_names_include_phase_token() -> None:
    paths = [
        path for path in EXPORT_ROOT.rglob("*phase3sa2*")
        if path.is_file()
    ]
    assert paths
    assert all("phase3sa2" in path.name for path in paths)
