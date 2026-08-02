"""Body passage, printable geometry, and candidate identity checks."""

import pytest
from pathlib import Path

from ps_mht_v001.common.validation import (
    measure_shape,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.coupons.netpot_seat_fit_coupon_phase3pa import (
    M4_HOLE_COUNT,
    SMALL_CLAW_COUNT,
    SMALL_GATE_COUNT,
    SNAP_COUNT,
    build_netpot_seat_fit_coupon_phase3pa,
    candidate_index_phase3pa,
    coupon_feature_policy_phase3pa,
)
from ps_mht_v001.parameters import (
    netpot_body_passage_preferred_precalibration,
    netpot_body_passage_selected,
)


@pytest.mark.parametrize("diameter", [80.0, 80.5, 81.0])
def test_phase3pa_coupon_is_one_valid_a1_solid(diameter: float) -> None:
    metrics = measure_shape(build_netpot_seat_fit_coupon_phase3pa(diameter))
    assert metrics.solid_count == 1
    assert metrics.all_solids_valid
    assert metrics.size_x <= 245.0
    assert metrics.size_y <= 245.0
    assert metrics.size_z <= 240.0


def test_phase3pa_coupon_nominal_envelope() -> None:
    policy = coupon_feature_policy_phase3pa()
    assert policy["outer_diameter_mm"] == 116.0
    assert policy["thickness_mm"] == 8.0


def test_phase3pa_coupon_forbidden_small_features_are_absent() -> None:
    assert (SMALL_CLAW_COUNT, SNAP_COUNT, SMALL_GATE_COUNT, M4_HOLE_COUNT) == (
        0,
        0,
        0,
        0,
    )


def test_phase3pa_dimple_identification_is_one_two_three() -> None:
    assert [candidate_index_phase3pa(value) for value in (80.0, 80.5, 81.0)] == [
        1,
        2,
        3,
    ]


def test_phase3pa_c805_passage_is_physically_selected() -> None:
    assert netpot_body_passage_selected == 80.5
    assert netpot_body_passage_preferred_precalibration == 80.5


def test_phase3pa_non_candidate_passage_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_netpot_seat_fit_coupon_phase3pa(80.25)


def test_phase3pa_generated_steps_round_trip_valid() -> None:
    root = Path(__file__).parents[1] / "exports" / "step"
    paths = [
        root / "ps_mht_v001_siawadeky_netpot_reference_envelope_phase3pa.step",
        *[
            root / f"ps_mht_v001_netpot_seat_fit_coupon_{token}_phase3pa.step"
            for token in ("c800", "c805", "c810")
        ],
    ]
    for path in paths:
        metrics = validate_step_round_trip(path, 1)
        assert metrics.solid_count == 1
        assert metrics.all_solids_valid


def test_phase3pa_generated_stls_are_closed_single_components() -> None:
    root = Path(__file__).parents[1] / "exports" / "stl"
    names = [
        *[
            f"ps_mht_v001_netpot_seat_fit_coupon_{token}_phase3pa.stl"
            for token in ("c800", "c805", "c810")
        ],
        "plate_01_netpot_fit_c805_phase3pa.stl",
        "plate_02_netpot_fit_c800_phase3pa.stl",
        "plate_03_netpot_fit_c810_phase3pa.stl",
    ]
    for name in names:
        metrics = validate_stl_mesh(root / name)
        assert metrics.closed_manifold
        assert metrics.connected_component_count == 1


def test_phase3pa_reference_envelope_has_no_stl_output() -> None:
    path = (
        Path(__file__).parents[1]
        / "exports"
        / "stl"
        / "ps_mht_v001_siawadeky_netpot_reference_envelope_phase3pa.stl"
    )
    assert not path.exists()


def test_phase3pa_required_individual_plate_files_exist() -> None:
    root = Path(__file__).parents[1] / "exports" / "stl"
    for name in (
        "plate_01_netpot_fit_c805_phase3pa.stl",
        "plate_02_netpot_fit_c800_phase3pa.stl",
        "plate_03_netpot_fit_c810_phase3pa.stl",
    ):
        assert (root / name).is_file()
