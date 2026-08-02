"""Phase 3S-A output, mesh, plate, and SHA non-regression gates."""

from __future__ import annotations

from pathlib import Path

from ps_mht_v001.common.phase3sa_nonregression import (
    audit_phase1_through_phase3r1,
)
from ps_mht_v001.common.validation import (
    validate_printable_set,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.print_plate_layout_phase3sa import (
    PART_SPACING_MM,
    phase3sa_individual_plates,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def test_phase3sa_expected_steps_reload_valid() -> None:
    expected = {
        "ps_mht_v001_sector_seam_coupon_c040_phase3sa.step": 2,
        "ps_mht_v001_sector_seam_coupon_c060_phase3sa.step": 2,
        "ps_mht_v001_sector_seam_coupon_c080_phase3sa.step": 2,
        "ps_mht_v001_sector_panel_single_phase3sa.step": 1,
        "ps_mht_v001_temporary_panel_capture_ring_phase3sa.step": 1,
        "ps_mht_v001_panel_capture_ring_coupon_phase3sa.step": 2,
        "ps_mht_v001_three_sector_short_assembly_phase3sa.step": 6,
        "ps_mht_v001_three_sector_full_height_reference_phase3sa.step": 6,
        "ps_mht_v001_three_sector_exploded_phase3sa.step": 6,
    }
    for name, count in expected.items():
        metrics = validate_step_round_trip(
            EXPORT_ROOT / "step" / name,
            count,
        )
        assert metrics.all_solids_valid


def test_phase3sa_all_printed_stls_are_closed_manifolds() -> None:
    paths = sorted((EXPORT_ROOT / "stl").glob("*phase3sa.stl"))
    assert len(paths) == 11
    for path in paths:
        assert validate_stl_mesh(path).closed_manifold


def test_phase3sa_single_part_stls_have_one_connected_component() -> None:
    names = (
        "ps_mht_v001_sector_panel_single_phase3sa.stl",
        "ps_mht_v001_sector_panel_single_print_orientation_phase3sa.stl",
        "ps_mht_v001_temporary_panel_capture_ring_phase3sa.stl",
        "plate_03_sector_panel_single_phase3sa.stl",
    )
    for name in names:
        assert validate_stl_mesh(
            EXPORT_ROOT / "stl" / name
        ).connected_component_count == 1


def test_all_four_individual_plates_fit_a1() -> None:
    expected_names = (
        "plate_01_sector_seam_coupons_phase3sa",
        "plate_02_panel_capture_coupon_phase3sa",
        "plate_03_sector_panel_single_phase3sa",
        "plate_04_three_sector_short_parts_phase3sa",
    )
    plates = phase3sa_individual_plates()
    assert tuple(name for name, _, _ in plates) == expected_names
    for name, model, count in plates:
        validate_printable_set(model, name, count)


def test_plate_part_spacing_contract_is_at_least_15mm() -> None:
    assert PART_SPACING_MM >= 15.0


def test_phase1_through_phase3r1_artifact_hashes_are_unchanged() -> None:
    audit = audit_phase1_through_phase3r1(EXPORT_ROOT)
    assert {
        phase: len(item["expected"]) for phase, item in audit.items()
    } == {
        "phase1": 7,
        "phase2": 22,
        "phase3a": 39,
        "phase3a1": 22,
        "phase3r": 40,
        "phase3r1": 13,
    }
    assert all(item["unchanged"] for item in audit.values())


def test_no_giant_multi_plate_phase3sa_stl_exists() -> None:
    assert not list(
        (EXPORT_ROOT / "stl").glob("*multi_plate*phase3sa.stl")
    )
