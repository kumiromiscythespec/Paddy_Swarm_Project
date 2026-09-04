"""Phase 3I-D two-stage collision and reference tests (7)."""

from ps_mht_v001.reference.interstage_cascade_references_phase3id import (
    build_two_stage_interstage_cascade_assembly_reference_phase3id,
    two_stage_collision_audit_phase3id,
    two_stage_reference_metadata_phase3id,
)


def _audit() -> dict[str, object]:
    return two_stage_collision_audit_phase3id()


def test_phase3id_full_stacked_modules_have_zero_volume_intersection() -> None:
    assert _audit()["full_modules_clear"]
    assert _audit()["lower_upper_full_intersection_volume_mm3"] == 0


def test_phase3id_receiver_clears_all_three_netpots() -> None:
    assert _audit()["receiver_netpot_clear"]
    assert _audit()["receiver_netpot_intersection_volumes_mm3"] == [0, 0, 0]


def test_phase3id_receiver_clears_rear_2020_post() -> None:
    assert _audit()["receiver_2020_post_clear"]


def test_phase3id_two_stage_stream_is_captured_and_central_hole_is_dry() -> None:
    assert _audit()["stream_envelope_captured"]
    assert _audit()["central_dry_opening_clear"]


def test_phase3id_two_stage_reference_contains_seven_solids() -> None:
    reference = build_two_stage_interstage_cascade_assembly_reference_phase3id()
    assert len(reference.solids().vals()) == two_stage_reference_metadata_phase3id()["solid_count"] == 7


def test_phase3id_full_stage_is_within_238mm() -> None:
    assert _audit()["within_238mm"]
    assert _audit()["maximum_xy_mm"] <= 238.0


def test_phase3id_receiver_and_drip_nose_radii_are_bounded() -> None:
    assert _audit()["receiver_outer_radius_mm"] <= 118.5
    assert _audit()["drip_nose_centerline_radius_mm"] <= 106.5

