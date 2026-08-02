"""Phase 2 parameter regression and calibration-coupon envelope tests."""

from __future__ import annotations

import inspect
from math import isclose

from ps_mht_v001 import parameters as p
from ps_mht_v001.assembly import full_tower_assembly
from ps_mht_v001.common.validation import validate_printable_set
from ps_mht_v001.coupons.m4_insert_coupon import build_m4_insert_coupon
from ps_mht_v001.coupons.module_body_roundness_coupon import (
    build_module_body_roundness_coupon,
)
from ps_mht_v001.coupons.module_interface_coupon import (
    COUPON_SOLID_COUNT,
    CLEARANCES_PER_SIDE,
    build_module_interface_coupon,
)
from ps_mht_v001.coupons.tpu_gasket_coupon import (
    GROOVE_DEPTHS,
    build_tpu_gasket_coupon,
)


def test_irrigation_top_height_is_independent_parameter() -> None:
    assert p.irrigation_top_height == 100.0
    assert isclose(
        p.tower_nominal_height,
        p.drain_base_height
        + p.module_count * p.module_height
        + p.irrigation_top_height,
    )


def test_height_calculation_has_no_hardcoded_100_literal() -> None:
    parameter_source = inspect.getsource(p.validate_parameters)
    assembly_source = inspect.getsource(full_tower_assembly.tower_components)
    assert "100.0" not in parameter_source
    assert "100.0" not in assembly_source
    assert "irrigation_top_height" in parameter_source
    assert "irrigation_top_height" in assembly_source


def test_module_interface_coupon_three_clearances_and_a1_fit() -> None:
    assert CLEARANCES_PER_SIDE == (0.30, 0.40, 0.50)
    metrics = validate_printable_set(
        build_module_interface_coupon(),
        "module_interface_coupon",
        COUPON_SOLID_COUNT,
    )
    assert metrics.size_x <= 245.0
    assert metrics.size_y <= 245.0
    assert metrics.size_z <= 240.0


def test_roundness_coupon_a1_fit() -> None:
    metrics = validate_printable_set(
        build_module_body_roundness_coupon(),
        "module_body_roundness_coupon",
        1,
    )
    assert isclose(metrics.size_x, 200.0, abs_tol=1.0e-6)
    assert isclose(metrics.size_y, 200.0, abs_tol=1.0e-6)
    assert 25.0 <= metrics.size_z <= 30.0


def test_m4_insert_coupon_a1_fit() -> None:
    metrics = validate_printable_set(
        build_m4_insert_coupon(),
        "m4_insert_coupon",
        1,
    )
    assert metrics.size_x <= 245.0
    assert metrics.size_y <= 245.0
    assert metrics.size_z <= 240.0


def test_tpu_gasket_coupon_three_depths_and_a1_fit() -> None:
    assert GROOVE_DEPTHS == (2.0, 2.2, 2.4)
    metrics = validate_printable_set(
        build_tpu_gasket_coupon(),
        "tpu_gasket_coupon",
        1,
    )
    assert metrics.size_x <= 245.0
    assert metrics.size_y <= 245.0
    assert metrics.size_z <= 240.0

