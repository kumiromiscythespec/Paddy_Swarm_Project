"""Phase 3S-A.1 explicit seam-clearance plate API gates."""

from __future__ import annotations

import inspect

import pytest

from ps_mht_v001.common.validation import validate_printable_set
from ps_mht_v001.parameters import phase3sa_seam_clearance_selected
from ps_mht_v001.print_plate_layout_phase3sa1 import (
    build_plate_02_panel_capture_coupon_phase3sa1,
    build_plate_03_sector_panel_single_phase3sa1,
    build_plate_04_three_sector_short_parts_phase3sa1,
    selected_plate_file_names_phase3sa1,
)


BUILDERS = (
    build_plate_02_panel_capture_coupon_phase3sa1,
    build_plate_03_sector_panel_single_phase3sa1,
    build_plate_04_three_sector_short_parts_phase3sa1,
)


def test_selected_clearance_remains_none_before_physical_test() -> None:
    assert phase3sa_seam_clearance_selected is None


def test_selected_plate_builders_have_one_required_argument() -> None:
    for builder in BUILDERS:
        parameters = tuple(inspect.signature(builder).parameters.values())
        assert len(parameters) == 1
        assert parameters[0].default is inspect.Parameter.empty


def test_selected_plate_builders_reject_missing_argument() -> None:
    for builder in BUILDERS:
        with pytest.raises(TypeError):
            builder()


def test_selected_plate_builders_reject_non_candidate() -> None:
    for builder in BUILDERS:
        with pytest.raises(ValueError):
            builder(0.5)


def test_selected_plate_names_include_explicit_candidate_token() -> None:
    for clearance, token in ((0.4, "c040"), (0.6, "c060"), (0.8, "c080")):
        names = selected_plate_file_names_phase3sa1(clearance)
        assert len(names) == 3
        assert all(token in name for name in names)
        assert all("phase3sa1" in name for name in names)


def test_explicit_c040_plate_set_fits_a1() -> None:
    validate_printable_set(
        build_plate_02_panel_capture_coupon_phase3sa1(0.4),
        "plate_02_c040_phase3sa1",
        3,
    )
    validate_printable_set(
        build_plate_03_sector_panel_single_phase3sa1(0.4),
        "plate_03_c040_phase3sa1",
        1,
    )
    validate_printable_set(
        build_plate_04_three_sector_short_parts_phase3sa1(0.4),
        "plate_04_c040_phase3sa1",
        3,
    )
