"""Phase 3I-C horseshoe keeper V2 geometry and artifact tests (7)."""

from pathlib import Path

from ps_mht_v001.common.validation import validate_step_round_trip, validate_stl_mesh
from ps_mht_v001.tower_module.horseshoe_flange_keeper_phase3ic import (
    KEEPER_V2_INNER_DIAMETER_MM,
    KEEPER_V2_OUTER_DIAMETER_MM,
    KEEPER_V2_RADIAL_CONTACT_WIDTH_MM,
    KEEPER_V2_RETAINED_ARC_DEG,
    KEEPER_V2_THICKNESS_MM,
    ROPE_NOTCH_COUNT,
    ROPE_NOTCH_DEPTH_MM,
    ROPE_NOTCH_EDGE_RADIUS_MM,
    ROPE_NOTCH_NOMINAL_WIDTH_MM,
    build_horseshoe_flange_keeper_v2_phase3ic,
)


PACKAGE_ROOT = Path(__file__).parents[1]
EXPORT_ROOT = PACKAGE_ROOT / "exports"


def test_phase3ic_keeper_is_one_valid_solid() -> None:
    keeper = build_horseshoe_flange_keeper_v2_phase3ic()
    assert len(keeper.solids().vals()) == 1 and keeper.val().isValid()


def test_phase3ic_keeper_selected_diameters() -> None:
    assert KEEPER_V2_OUTER_DIAMETER_MM == 107.0
    assert KEEPER_V2_INNER_DIAMETER_MM == 90.0


def test_phase3ic_keeper_thickness_and_arc() -> None:
    assert KEEPER_V2_THICKNESS_MM == 5.0
    assert KEEPER_V2_RETAINED_ARC_DEG == 180.0


def test_phase3ic_keeper_contact_width_is_8_5mm() -> None:
    assert KEEPER_V2_RADIAL_CONTACT_WIDTH_MM == 8.5


def test_phase3ic_keeper_has_two_open_5_6mm_notches() -> None:
    assert ROPE_NOTCH_COUNT == 2
    assert ROPE_NOTCH_NOMINAL_WIDTH_MM == 5.6
    assert 3.0 <= ROPE_NOTCH_DEPTH_MM <= 5.0
    assert ROPE_NOTCH_EDGE_RADIUS_MM >= 1.0


def test_phase3ic_keeper_step_round_trip_valid() -> None:
    path = EXPORT_ROOT / "step" / "ps_mht_v001_horseshoe_flange_keeper_v2_phase3ic.step"
    assert validate_step_round_trip(path, 1, True).all_solids_valid


def test_phase3ic_keeper_stl_is_closed_single_component() -> None:
    path = EXPORT_ROOT / "stl" / "plate_01_horseshoe_flange_keeper_v2_phase3ic.stl"
    metrics = validate_stl_mesh(path)
    assert metrics.closed_manifold
    assert metrics.connected_component_count == 1
    assert metrics.boundary_or_nonmanifold_edge_count == 0

