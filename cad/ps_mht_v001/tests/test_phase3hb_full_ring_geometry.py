"""Phase 3H-B geometry and generated artifact tests (7)."""

from pathlib import Path

import pytest

from ps_mht_v001.common.validation import (
    measure_shape,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.reference.full_ring_pair_phase3hb import (
    build_full_ring_lower_c050_phase3hb,
    build_full_ring_pair_c050_reference_phase3hb,
    build_full_ring_upper_c050_print_phase3hb,
    phase3hb_geometry_requirements,
)


PACKAGE_ROOT = Path(__file__).parents[1]
STEP_ROOT = PACKAGE_ROOT / "exports" / "step"
STL_ROOT = PACKAGE_ROOT / "exports" / "stl"


def test_phase3hb_lower_ring_is_one_valid_solid() -> None:
    metrics = measure_shape(build_full_ring_lower_c050_phase3hb())
    assert metrics.solid_count == 1 and metrics.all_solids_valid


def test_phase3hb_upper_ring_is_one_valid_solid() -> None:
    metrics = measure_shape(build_full_ring_upper_c050_print_phase3hb())
    assert metrics.solid_count == 1 and metrics.all_solids_valid


def test_phase3hb_clearance_tokens_have_verified_fit_direction() -> None:
    candidates = phase3hb_geometry_requirements()["candidate_dimensions"]
    assert candidates["c030"]["skirt_outer_diameter_mm"] == pytest.approx(193.4)
    assert candidates["c050"]["skirt_outer_diameter_mm"] == pytest.approx(193.0)
    assert candidates["c070"]["skirt_outer_diameter_mm"] == pytest.approx(192.6)
    assert candidates["c030"]["relative_fit"] == "TIGHTEST_OF_THREE"
    assert candidates["c070"]["relative_fit"] == "LOOSEST_OF_THREE"


def test_phase3hb_pair_reference_preserves_overlap_height_and_m4_envelopes() -> None:
    requirements = phase3hb_geometry_requirements()
    assert measure_shape(build_full_ring_pair_c050_reference_phase3hb()).solid_count == 5
    assert requirements["skirt_overlap_mm"] == pytest.approx(10.0)
    assert requirements["assembled_height_mm"] == pytest.approx(80.0)
    assert requirements["m4_envelope_count"] == 3
    assert not requirements["hole_1_feature_added"]


def test_phase3hb_generated_steps_round_trip_valid() -> None:
    expected = {
        "ps_mht_v001_full_ring_lower_c050_phase3hb.step": 1,
        "ps_mht_v001_full_ring_upper_c050_phase3hb.step": 1,
        "ps_mht_v001_full_ring_pair_c050_reference_phase3hb.step": 5,
        "ps_mht_v001_compression_ring_reference_phase3hb.step": 1,
    }
    for name, count in expected.items():
        assert validate_step_round_trip(STEP_ROOT / name, count).all_solids_valid


def test_phase3hb_print_stls_are_watertight_single_components() -> None:
    for name in (
        "plate_01_full_ring_lower_c050_phase3hb.stl",
        "plate_02_full_ring_upper_c050_phase3hb.stl",
        "plate_03_compression_ring_HOLD_phase3hb.stl",
    ):
        metrics = validate_stl_mesh(STL_ROOT / name)
        assert metrics.closed_manifold
        assert metrics.boundary_or_nonmanifold_edge_count == 0
        assert metrics.connected_component_count == 1


def test_phase3hb_full_ring_print_envelopes_fit_a1() -> None:
    requirements = phase3hb_geometry_requirements()
    for key in ("lower_print_envelope_mm", "upper_print_envelope_mm"):
        size_x, size_y, size_z = requirements[key]
        assert size_x <= 256.0 and size_y <= 256.0 and size_z <= 256.0
