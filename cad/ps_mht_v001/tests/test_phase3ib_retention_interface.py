"""Phase 3I-B commercial-rope and optional keeper tests (7)."""

from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ib import (
    C_KEEPER_OUTER_DIAMETER_MM,
    NETPOT_FLANGE_OUTER_DIAMETER_MM,
    RETENTION_LUG_COUNT_PER_PORT,
    RETENTION_LUG_ROOT_THICKNESS_MM,
    ROPE_NOMINAL_DIAMETER_MM,
    SELECTED_C_KEEPER_ARC_DEG,
    SELECTED_C_KEEPER_INNER_DIAMETER_MM,
    SELECTED_ROPE_HOLE_WIDTH_MM,
    build_c_shaped_flange_keeper_phase3ib,
    build_retention_lugs_phase3ib,
    retention_audit_phase3ib,
)


def test_phase3ib_has_two_retention_lugs_per_port() -> None:
    assert RETENTION_LUG_COUNT_PER_PORT == 2
    assert retention_audit_phase3ib()["lug_count_per_port"] == 2


def test_phase3ib_retention_lug_roots_are_large_and_connected() -> None:
    audit = retention_audit_phase3ib()
    assert RETENTION_LUG_ROOT_THICKNESS_MM >= 10.0
    assert audit["lug_floor_connected"]
    assert audit["lug_main_wall_or_side_buttress_connected"]


def test_phase3ib_rope_interface_matches_commercial_5mm_cord() -> None:
    audit = retention_audit_phase3ib()
    assert ROPE_NOMINAL_DIAMETER_MM == 5.0
    assert SELECTED_ROPE_HOLE_WIDTH_MM in audit["rope_hole_candidates_mm"]


def test_phase3ib_rope_hole_is_self_supporting_and_under_6mm() -> None:
    audit = retention_audit_phase3ib()
    assert audit["rope_hole_shape"] == "SELF_SUPPORTING_TEARDROP"
    assert audit["maximum_horizontal_unsupported_span_mm"] <= 6.0


def test_phase3ib_rope_path_avoids_plant_center() -> None:
    audit = retention_audit_phase3ib()
    assert audit["rope_path_crosses_plant_center"] is False
    assert audit["rope_path_local_flange_offset_mm"] > 0.0


def test_phase3ib_keeper_is_flat_optional_and_within_flange() -> None:
    keeper = build_c_shaped_flange_keeper_phase3ib()
    assert len(keeper.solids().vals()) == 1 and keeper.val().isValid()
    assert C_KEEPER_OUTER_DIAMETER_MM <= NETPOT_FLANGE_OUTER_DIAMETER_MM
    assert SELECTED_C_KEEPER_INNER_DIAMETER_MM == 90.0
    assert SELECTED_C_KEEPER_ARC_DEG == 165.0


def test_phase3ib_cord_alone_remains_primary_retention() -> None:
    audit = retention_audit_phase3ib()
    assert audit["positive_retention"] == "COMMERCIAL_5MM_VINYL_ROPE"
    assert audit["cord_alone_retains_pot"] is True
    assert audit["keeper_optional"] is True
    assert all(build_retention_lugs_phase3ib(angle).val().isValid() for angle in (0.0, 120.0, 240.0))

