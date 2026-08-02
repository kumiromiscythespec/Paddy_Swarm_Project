"""Phase 2 radial cord-gasket and hard-stop tests."""

from __future__ import annotations

from math import isclose

from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    gasket_cord_diameter,
    gasket_diameter,
    gasket_groove_depth,
    gasket_groove_width,
    interface_radial_clearance,
)
from ps_mht_v001.tower_module.module_gasket import build_module_gasket
from ps_mht_v001.tower_module.module_interface import (
    compression_stop_radial_width,
    gasket_to_bolt_radial_clearance,
)


def test_gasket_alias_and_groove_dimensions() -> None:
    assert gasket_cord_diameter == 3.0
    assert gasket_diameter == gasket_cord_diameter
    assert gasket_groove_width == 3.6
    assert gasket_groove_depth == 2.2


def test_gasket_reference_is_one_valid_solid() -> None:
    metrics = measure_shape(build_module_gasket())
    assert metrics.solid_count == 1
    assert metrics.all_solids_valid
    assert isclose(metrics.size_z, gasket_cord_diameter, abs_tol=1.0e-6)


def test_gasket_has_controlled_radial_compression() -> None:
    protrusion = gasket_cord_diameter - gasket_groove_depth
    compression = protrusion - interface_radial_clearance
    assert isclose(protrusion, 0.8, abs_tol=1.0e-6)
    assert isclose(compression, 0.4, abs_tol=1.0e-6)
    assert compression > 0.0


def test_gasket_groove_does_not_cross_m4_bores() -> None:
    assert gasket_to_bolt_radial_clearance() >= 4.0


def test_hard_compression_stop_exists() -> None:
    assert compression_stop_radial_width() >= 6.0

