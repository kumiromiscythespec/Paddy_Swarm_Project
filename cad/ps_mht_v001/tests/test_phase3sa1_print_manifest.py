"""Phase 3S-A.1 quantity manifest and artifact gates."""

from __future__ import annotations

import json
from pathlib import Path

from ps_mht_v001.common.phase3sa1_nonregression import (
    audit_phase1_through_phase3sa,
)
from ps_mht_v001.common.validation import validate_stl_mesh
from ps_mht_v001.print_manifest_phase3sa1 import (
    ADDITIONAL_RING_FILE,
    build_print_manifest_phase3sa1,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def test_unselected_manifest_does_not_resolve_to_c060() -> None:
    manifest = build_print_manifest_phase3sa1()
    assert manifest["selected_clearance"] is None
    for item in manifest["print_items"]:
        if item["assembly_use"].startswith(
            ("CAPTURE_", "FULL_HEIGHT_", "THREE_IDENTICAL_")
        ):
            assert item["file_name"] is None
            assert item["print_status"] == (
                "NOT_GENERATED_CLEARANCE_SELECTION_REQUIRED"
            )


def test_manifest_candidate_names_cover_all_clearances() -> None:
    manifest = build_print_manifest_phase3sa1()
    for item in manifest["print_items"]:
        candidates = item.get("candidate_file_names")
        if candidates:
            assert len(candidates) == 3
            for token in ("c040", "c060", "c080"):
                assert sum(token in name for name in candidates) == 1


def test_explicit_manifest_uses_only_selected_token() -> None:
    manifest = build_print_manifest_phase3sa1(0.8)
    selected_items = [
        item for item in manifest["print_items"]
        if item.get("candidate_file_names")
    ]
    assert all(item["selected_clearance"] == 0.8 for item in selected_items)
    assert all("c080" in item["file_name"] for item in selected_items)


def test_two_capture_ring_quantities_are_reconciled() -> None:
    manifest = build_print_manifest_phase3sa1()
    quantities = manifest["temporary_capture_ring_quantity"]
    assert quantities == {
        "required_for_short_assembly": 2,
        "included_in_selected_plate_02": 1,
        "additional_single_stl": 1,
        "quantity_reconciled": True,
    }
    additional = next(
        item for item in manifest["print_items"]
        if item["file_name"] == ADDITIONAL_RING_FILE
    )
    assert additional["quantity"] == 1


def test_workflow_has_all_seven_required_gates() -> None:
    manifest = build_print_manifest_phase3sa1()
    assert manifest["recommended_workflow"] == [
        "1_PRINT_PLATE_01",
        "2_SELECT_SEAM_CLEARANCE",
        "3_REGENERATE_AND_PRINT_SELECTED_PLATE_02",
        "4_PRINT_SELECTED_PLATE_03_AFTER_PLATE_02_PASS",
        "5_PRINT_ONE_ADDITIONAL_CAPTURE_RING_AFTER_PLATE_03_PASS",
        "6_PRINT_SELECTED_PLATE_04",
        "7_BUILD_SHORT_THREE_PANEL_ASSEMBLY",
    ]


def test_written_manifest_matches_unselected_state() -> None:
    path = EXPORT_ROOT / "preview" / "print_manifest_phase3sa1.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["selected_clearance"] is None
    assert manifest["phase3sa_seam_clearance_selected_parameter"] is None


def test_phase3sa1_base_stls_are_closed() -> None:
    names = (
        "plate_01_sector_seam_coupons_phase3sa1.stl",
        ADDITIONAL_RING_FILE,
    )
    for name in names:
        assert validate_stl_mesh(EXPORT_ROOT / "stl" / name).closed_manifold


def test_phase1_through_phase3sa_artifact_hashes_are_unchanged() -> None:
    audit = audit_phase1_through_phase3sa(EXPORT_ROOT)
    assert all(item["unchanged"] for item in audit.values())
    assert len(audit["phase3sa"]["actual"]) == 24
