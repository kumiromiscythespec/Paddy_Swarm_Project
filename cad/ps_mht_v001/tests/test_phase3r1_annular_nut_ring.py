"""Phase 3R.1 production/calibration M4 nut-ring separation gates."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from ps_mht_v001.assembly.module_interface_phase3r1 import (
    ASSEMBLY_POLICY,
    interface_components_phase3r1,
)
from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.coupons.annular_nut_ring_coupon_phase3r1 import (
    CALIBRATION_ONLY,
    NUT_POCKET_CLEARANCES,
    PHYSICAL_ID_SCHEME,
    build_annular_nut_ring_coupon_phase3r1,
)
from ps_mht_v001.parameters import (
    CALIBRATION_PENDING,
    module_nut_pocket_clearance_candidates,
)
from ps_mht_v001.tower_module.module_nut_ring_phase3r1 import (
    CALIBRATION_STATUS,
    SELECTED_NUT_POCKET_CLEARANCE,
    build_module_nut_ring_phase3r1,
    production_pocket_clearances_phase3r1,
)


EXPORT_ROOT = Path(__file__).resolve().parents[1] / "exports"


def test_phase3r1_production_ring_requires_explicit_clearance() -> None:
    parameter = inspect.signature(
        build_module_nut_ring_phase3r1
    ).parameters["nut_pocket_clearance"]
    assert parameter.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        build_module_nut_ring_phase3r1()  # type: ignore[call-arg]


def test_phase3r1_production_ring_has_three_identical_clearances() -> None:
    for candidate in module_nut_pocket_clearance_candidates:
        assert production_pocket_clearances_phase3r1(candidate) == (
            candidate,
            candidate,
            candidate,
        )
        metrics = measure_shape(build_module_nut_ring_phase3r1(candidate))
        assert metrics.solid_count == 1 and metrics.all_solids_valid


def test_phase3r1_only_calibration_coupon_contains_three_candidates() -> None:
    assert CALIBRATION_ONLY
    assert NUT_POCKET_CLEARANCES == (0.15, 0.25, 0.35)
    assert len(set(NUT_POCKET_CLEARANCES)) == 3
    assert "ONE_TWO_THREE" in PHYSICAL_ID_SCHEME
    assert measure_shape(
        build_annular_nut_ring_coupon_phase3r1()
    ).solid_count == 1


def test_phase3r1_selected_nut_clearance_is_pending() -> None:
    assert SELECTED_NUT_POCKET_CLEARANCE is None
    assert CALIBRATION_STATUS == CALIBRATION_PENDING


def test_phase3r1_assembly_never_uses_mixed_or_calibration_ring() -> None:
    components = interface_components_phase3r1(0.25)
    nut_components = [
        component for component in components
        if component.nut_pocket_clearances
    ]
    assert len(nut_components) == 1
    assert nut_components[0].nut_pocket_clearances == (0.25, 0.25, 0.25)
    assert len(set(nut_components[0].nut_pocket_clearances)) == 1
    assert all("coupon" not in component.name for component in components)
    assert "NO_CALIBRATION_COUPON" in ASSEMBLY_POLICY


def test_phase3r1_candidate_output_name_contains_clearance() -> None:
    expected = (
        EXPORT_ROOT
        / "step"
        / "ps_mht_v001_module_nut_ring_candidate_c025_phase3r1.step"
    )
    assert expected.is_file()
