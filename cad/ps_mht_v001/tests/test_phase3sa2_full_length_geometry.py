"""Phase 3S-A.2 full-length seam and local-fixture geometry gates."""

from __future__ import annotations

import pytest

from ps_mht_v001.assembly.full_length_seam_calibration_reference_phase3sa2 import (
    ASSEMBLY_SOLID_COUNT,
    build_full_length_seam_calibration_reference_phase3sa2,
)
from ps_mht_v001.common.validation import (
    measure_shape,
    validate_multi_solid,
    validate_printable_set,
    validate_single_printable,
)
from ps_mht_v001.coupons.full_length_seam_pair_phase3sa2 import (
    PART_SPACING_MM,
    build_full_length_seam_pair_phase3sa2,
    full_length_seam_print_pieces_phase3sa2,
    full_length_seam_requirements_phase3sa2,
    validate_phase3sa2_clearance,
)
from ps_mht_v001.parameters import (
    phase3sa2_effective_seam_length,
    phase3sa2_panel_remaining_width,
    phase3sa2_seam_clearance_candidates,
    phase3sa_seam_clearance_selected,
    phase3sa_seam_overlap,
    phase3sa_water_return_height,
    phase3sa_water_return_thickness,
)
from ps_mht_v001.print_plate_layout_phase3sa2 import (
    build_optional_combined_c040_c060_plate_phase3sa2,
    phase3sa2_required_plates,
)
from ps_mht_v001.tower_module.full_length_seam_capture_fixture_phase3sa2 import (
    FIXTURES_FOR_SIMULTANEOUS_C040_C060,
    FIXTURES_PER_CANDIDATE,
    build_full_length_seam_capture_fixture_phase3sa2,
    fixture_requirements_phase3sa2,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    FORBIDDEN_FEATURES,
)


def test_only_c040_and_c060_are_retested_and_selection_is_none() -> None:
    assert phase3sa2_seam_clearance_candidates == (0.4, 0.6)
    assert phase3sa_seam_clearance_selected is None
    with pytest.raises(ValueError):
        validate_phase3sa2_clearance(0.8)


def test_full_length_pieces_preserve_170mm_effective_length() -> None:
    for clearance in phase3sa2_seam_clearance_candidates:
        pieces = full_length_seam_print_pieces_phase3sa2(clearance)
        assert len(pieces) == 2
        for index, piece in enumerate(pieces):
            metrics = validate_single_printable(
                piece,
                f"c{clearance}_{index}",
            )
            assert abs(metrics.size_y - phase3sa2_effective_seam_length) < 0.01


def test_each_candidate_pair_is_two_valid_a1_solids() -> None:
    for clearance in phase3sa2_seam_clearance_candidates:
        validate_printable_set(
            build_full_length_seam_pair_phase3sa2(clearance),
            f"full_length_pair_{clearance}",
            2,
        )


def test_pair_contract_preserves_actual_seam_features() -> None:
    for clearance in phase3sa2_seam_clearance_candidates:
        contract = full_length_seam_requirements_phase3sa2(clearance)
        assert contract["actual_curvature"]
        assert contract["actual_left_cover"]
        assert contract["actual_right_receiver"]
        assert contract["actual_contact_rail_section"]
        assert contract["actual_top_bottom_datums"]
        assert not contract["small_snap_claw_gate"]
    assert phase3sa_seam_overlap == 12.0
    assert phase3sa_water_return_height == 4.0
    assert phase3sa_water_return_thickness == 3.0


def test_panel_remaining_width_and_spacing_are_in_range() -> None:
    assert 35.0 <= phase3sa2_panel_remaining_width <= 50.0
    assert PART_SPACING_MM >= 15.0


def test_local_fixture_is_one_flat_reusable_solid() -> None:
    fixture = build_full_length_seam_capture_fixture_phase3sa2()
    validate_single_printable(fixture, "full_length_seam_fixture")
    contract = fixture_requirements_phase3sa2()
    assert contract["capture_depth_mm"] == 12.0
    assert contract["same_upper_and_lower_part"]
    assert not contract["fixture_contacts_seam_face"]
    assert not contract["small_snap"]
    assert contract["reusable"]


def test_fixture_quantities_match_sequential_and_simultaneous_tests() -> None:
    assert FIXTURES_PER_CANDIDATE == 2
    assert FIXTURES_FOR_SIMULTANEOUS_C040_C060 == 4


def test_all_required_plates_fit_a1_with_expected_components() -> None:
    plates = phase3sa2_required_plates()
    assert len(plates) == 3
    for name, model, count in plates:
        validate_printable_set(model, name, count)


def test_optional_combined_c040_c060_plate_fits_a1() -> None:
    validate_printable_set(
        build_optional_combined_c040_c060_plate_phase3sa2(),
        "combined_c040_c060_phase3sa2",
        4,
    )


def test_assembly_reference_has_two_pairs_and_four_fixtures() -> None:
    validate_multi_solid(
        build_full_length_seam_calibration_reference_phase3sa2(),
        "full_length_reference_phase3sa2",
        ASSEMBLY_SOLID_COUNT,
    )
    assert ASSEMBLY_SOLID_COUNT == 8


def test_phase3sa2_scope_has_no_snap_claw_or_gate() -> None:
    assert "SNAP" in FORBIDDEN_FEATURES
    assert "THIN_TONGUE" in FORBIDDEN_FEATURES
    assert "CANTILEVER_GATE" in FORBIDDEN_FEATURES
