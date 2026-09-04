"""Phase 3I-B real annular sump-boundary tests (7)."""

import pytest

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ib import (
    CENTRAL_CLEAR_OPENING_DIAMETER_MM,
    INNER_DAM_MINIMUM_WALL_THICKNESS_MM,
    INNER_DAM_WALL_THICKNESS_MM,
    ROOT_FILLET_RADIUS_MM,
    SELECTED_INNER_DAM_TOP_Z_MM,
    SUMP_COUPON_HEIGHT_MM,
    SUMP_FLOOR_THICKNESS_MM,
    build_full_annular_sump_coupon_phase3ib,
    build_real_inner_dam_phase3ib,
    real_sump_boundary_audit_phase3ib,
)


def test_phase3ib_inner_dam_is_one_valid_solid() -> None:
    dam = build_real_inner_dam_phase3ib()
    assert len(dam.solids().vals()) == 1 and dam.val().isValid()


def test_phase3ib_inner_dam_is_360_degrees_continuous() -> None:
    audit = real_sump_boundary_audit_phase3ib()
    assert audit["architecture"] == "CONTINUOUS_ANNULAR_INNER_DAM"
    assert audit["continuous_angle_deg"] == 360.0


def test_phase3ib_inner_dam_wall_meets_minimum() -> None:
    assert INNER_DAM_WALL_THICKNESS_MM == pytest.approx(4.8)
    assert INNER_DAM_WALL_THICKNESS_MM >= INNER_DAM_MINIMUM_WALL_THICKNESS_MM >= 4.5


def test_phase3ib_central_opening_is_clear_100mm() -> None:
    audit = real_sump_boundary_audit_phase3ib()
    assert CENTRAL_CLEAR_OPENING_DIAMETER_MM == 100.0
    assert audit["inner_diameter_mm"] == 100.0


def test_phase3ib_floor_is_4mm_and_fused_to_dam() -> None:
    audit = real_sump_boundary_audit_phase3ib()
    assert SUMP_FLOOR_THICKNESS_MM == 4.0
    assert audit["floor_fusion_intersection_volume_mm3"] > 0.0


def test_phase3ib_inner_dam_has_r3_root_class() -> None:
    assert ROOT_FILLET_RADIUS_MM == 3.0
    assert real_sump_boundary_audit_phase3ib()["root_fillet_radius_mm"] == 3.0


def test_phase3ib_sump_coupon_reproduces_boundary_in_40mm_height() -> None:
    coupon = build_full_annular_sump_coupon_phase3ib()
    assert len(coupon.solids().vals()) == 1 and coupon.val().isValid()
    assert 35.0 <= SUMP_COUPON_HEIGHT_MM <= 45.0
    assert SELECTED_INNER_DAM_TOP_Z_MM < SUMP_COUPON_HEIGHT_MM

