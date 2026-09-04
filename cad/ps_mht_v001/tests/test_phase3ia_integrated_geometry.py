"""Phase 3I-A integrated printable-geometry tests (10)."""

import pytest

from ps_mht_v001.reference.integrated_stage_references_phase3ia import (
    ASSEMBLY_REFERENCE_SOLID_COUNT,
    WATER_VOLUME_REFERENCE_SOLID_COUNT,
    build_integrated_stage_assembly_reference_phase3ia,
    build_integrated_stage_water_volume_reference_phase3ia,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
    CENTRAL_OPENING_DIAMETER_MM,
    CRADLE_BODY_PASSAGE_DIAMETER_MM,
    MODULE_HEIGHT_MM,
    NOMINAL_BODY_OUTER_DIAMETER_MM,
    PORT_ANGLES_DEG,
    PORT_AXIS_ANGLE_DEG,
    PORT_COUNT,
    SUMP_FLOOR_THICKNESS_MM,
    build_integrated_stage_full_phase3ia,
    build_integrated_stage_lower_60mm_coupon_phase3ia,
    stage_geometry_requirements_phase3ia,
)


def test_phase3ia_full_stage_is_one_valid_solid() -> None:
    solids = build_integrated_stage_full_phase3ia().solids().vals()
    assert len(solids) == 1 and solids[0].isValid()


def test_phase3ia_lower_coupon_is_one_valid_solid() -> None:
    solids = build_integrated_stage_lower_60mm_coupon_phase3ia().solids().vals()
    assert len(solids) == 1 and solids[0].isValid()


def test_phase3ia_fixed_height_and_nominal_body_diameter() -> None:
    requirements = stage_geometry_requirements_phase3ia()
    assert MODULE_HEIGHT_MM == 170.0
    assert NOMINAL_BODY_OUTER_DIAMETER_MM == 200.0
    assert requirements["full_envelope_mm"][2] == pytest.approx(170.0, abs=1e-5)


def test_phase3ia_printed_maximum_xy_is_at_most_238mm() -> None:
    assert stage_geometry_requirements_phase3ia()["full_maximum_radial_xy_mm"] <= 238.0


def test_phase3ia_three_ports_have_fixed_angles() -> None:
    assert PORT_COUNT == 3
    assert PORT_ANGLES_DEG == (0.0, 120.0, 240.0)


def test_phase3ia_port_axis_is_27_degrees() -> None:
    assert PORT_AXIS_ANGLE_DEG == 27.0


def test_phase3ia_port_body_passage_is_80_5mm() -> None:
    assert CRADLE_BODY_PASSAGE_DIAMETER_MM == 80.5


def test_phase3ia_floor_and_central_opening_match_specification() -> None:
    assert SUMP_FLOOR_THICKNESS_MM >= 4.0
    assert CENTRAL_OPENING_DIAMETER_MM == 100.0


def test_phase3ia_required_structural_walls_are_not_undersize() -> None:
    walls = stage_geometry_requirements_phase3ia()["walls_mm"]
    assert walls["upper_nominal"] >= walls["upper_minimum"] >= 3.2
    assert 4.5 <= walls["lower_structural"] <= 5.2
    assert walls["port_root"] >= 6.0
    assert walls["top_band"] >= 4.5


def test_phase3ia_reference_compounds_have_expected_parts() -> None:
    assert len(build_integrated_stage_assembly_reference_phase3ia().solids().vals()) == ASSEMBLY_REFERENCE_SOLID_COUNT
    assert len(build_integrated_stage_water_volume_reference_phase3ia().solids().vals()) == WATER_VOLUME_REFERENCE_SOLID_COUNT
