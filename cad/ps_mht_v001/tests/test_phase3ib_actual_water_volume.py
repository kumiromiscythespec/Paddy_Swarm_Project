"""Phase 3I-B actual retained-water tests (7)."""

import pytest

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ib import (
    OPERATING_WATER_DEPTH_CANDIDATES_MM,
    SELECTED_INNER_DAM_TOP_Z_MM,
    SELECTED_OPERATING_WATER_DEPTH_MM,
    SELECTED_WATER_SURFACE_Z_MM,
    WICK_ENTRY_MINIMUM_Z_MM,
    actual_water_volume_audit_phase3ib,
    build_actual_water_volume_phase3ib,
)


def test_phase3ib_water_depth_candidates_are_20_21_22mm() -> None:
    assert OPERATING_WATER_DEPTH_CANDIDATES_MM == (20.0, 21.0, 22.0)


def test_phase3ib_each_actual_water_candidate_is_valid_geometry() -> None:
    for depth in OPERATING_WATER_DEPTH_CANDIDATES_MM:
        water = build_actual_water_volume_phase3ib(depth)
        assert water.solids().size() >= 1
        assert all(solid.isValid() for solid in water.solids().vals())


def test_phase3ib_selected_depth_is_22mm_and_surface_z26() -> None:
    assert SELECTED_OPERATING_WATER_DEPTH_MM == 22.0
    assert SELECTED_WATER_SURFACE_Z_MM == 26.0


def test_phase3ib_selected_actual_volume_is_in_preferred_range() -> None:
    selected = actual_water_volume_audit_phase3ib()["candidates"]["d22"]
    assert 0.38 <= selected["actual_retained_volume_l"] <= 0.42
    assert selected["within_target_range"]


def test_phase3ib_volume_subtracts_complete_printed_intrusions() -> None:
    audit = actual_water_volume_audit_phase3ib()
    assert audit["method"] == "ANNULAR_CAVITY_MINUS_COMPLETE_PRINTED_PHASE3IB_SOLID"
    assert audit["virtual_phase3ia_volume_inherited"] is False
    assert all(item["printed_intrusions_subtracted"] for item in audit["candidates"].values())


def test_phase3ib_inner_dam_margin_is_at_least_4mm() -> None:
    selected = actual_water_volume_audit_phase3ib()["candidates"]["d22"]
    assert selected["inner_dam_top_margin_mm"] == pytest.approx(5.0)
    assert SELECTED_INNER_DAM_TOP_Z_MM - SELECTED_WATER_SURFACE_Z_MM >= 4.0


def test_phase3ib_wick_entry_is_at_least_2mm_above_water() -> None:
    selected = actual_water_volume_audit_phase3ib()["candidates"]["d22"]
    assert WICK_ENTRY_MINIMUM_Z_MM - SELECTED_WATER_SURFACE_Z_MM >= 2.0
    assert selected["wick_entry_margin_mm"] >= 2.0

