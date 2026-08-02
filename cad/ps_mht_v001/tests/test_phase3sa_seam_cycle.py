"""Phase 3S-A asymmetric seam calibration and repeatability gates."""

from __future__ import annotations

import inspect

import pytest

from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.coupons.sector_seam_pair_coupon_phase3sa import (
    IDENTIFICATION,
    TEST_PROTOCOL,
    build_sector_seam_pair_coupon_phase3sa,
    seam_pair_assembly_pieces_phase3sa,
)
from ps_mht_v001.parameters import (
    phase3sa_seam_clearance_candidates,
    phase3sa_seam_root_radius,
    phase3sa_seam_root_thickness,
    phase3sa_water_return_height,
    phase3sa_water_return_thickness,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    FORBIDDEN_FEATURES,
    LEAD_CHAMFER_MM,
    SEAM_POLICY,
    seam_has_direct_radial_sightline_phase3sa,
    seam_minimum_features_phase3sa,
    validate_seam_clearance_phase3sa,
)


def test_three_explicit_seam_clearance_candidates_exist() -> None:
    assert phase3sa_seam_clearance_candidates == (0.4, 0.6, 0.8)
    for value in phase3sa_seam_clearance_candidates:
        assert validate_seam_clearance_phase3sa(value) == value
    with pytest.raises(ValueError):
        validate_seam_clearance_phase3sa(0.5)


def test_seam_coupon_requires_an_explicit_candidate() -> None:
    parameter = inspect.signature(
        build_sector_seam_pair_coupon_phase3sa
    ).parameters["seam_clearance"]
    assert parameter.default is inspect.Parameter.empty


def test_each_seam_pair_has_two_valid_noninterfering_parts() -> None:
    for clearance in phase3sa_seam_clearance_candidates:
        cover, receiver = seam_pair_assembly_pieces_phase3sa(clearance)
        assert measure_shape(cover).solid_count == 1
        assert measure_shape(receiver).solid_count == 1
        assert sum(
            solid.Volume()
            for solid in cover.intersect(receiver).solids().vals()
        ) <= 1.0e-7
        assert measure_shape(
            build_sector_seam_pair_coupon_phase3sa(clearance)
        ).solid_count == 2


def test_seam_root_and_chamfer_meet_minimums() -> None:
    features = seam_minimum_features_phase3sa()
    assert phase3sa_seam_root_thickness >= 4.0
    assert phase3sa_seam_root_radius >= 3.0
    assert features["lead_chamfer_mm"] == LEAD_CHAMFER_MM
    assert 0.8 <= LEAD_CHAMFER_MM <= 1.2


def test_inner_water_return_meets_minimums() -> None:
    assert 3.0 <= phase3sa_water_return_height <= 5.0
    assert phase3sa_water_return_thickness >= 3.0


def test_two_stage_labyrinth_has_no_direct_radial_sightline() -> None:
    assert SEAM_POLICY == "LEFT_OUTER_COVER_RIGHT_INNER_RECEIVER"
    assert not seam_has_direct_radial_sightline_phase3sa()


def test_no_snap_undercut_gate_or_cartridge_is_part_of_the_seam() -> None:
    assert set(FORBIDDEN_FEATURES) == {
        "UNDERCUT",
        "SNAP",
        "THIN_TONGUE",
        "CANTILEVER_GATE",
        "CARTRIDGE",
        "VERTICAL_GASKET",
    }


def test_large_dimple_and_ten_cycle_physical_protocol_is_declared() -> None:
    assert "ONE_TWO_THREE_LARGE_DIMPLES" in IDENTIFICATION
    assert "10_CYCLES" in TEST_PROTOCOL
    assert "500ML" in TEST_PROTOCOL
