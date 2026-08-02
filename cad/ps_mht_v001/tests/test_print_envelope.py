"""Bambu Lab A1 and Phase 1 module-shell tests."""

from __future__ import annotations

from math import isclose

from ps_mht_v001.common.validation import (
    measure_shape,
    validate_single_printable,
)
from ps_mht_v001.parameters import (
    module_height,
    module_wall_thickness,
    plant_port_wall_thickness,
    tower_body_diameter,
    tower_max_diameter,
)
from ps_mht_v001.tower_module.planting_module import (
    build_planting_module,
    minimum_wall_at_phase1_datum,
)


def test_planting_module_is_one_valid_solid() -> None:
    metrics = validate_single_printable(
        build_planting_module(),
        "planting_module",
    )
    assert metrics.solid_count == 1
    assert metrics.all_solids_valid
    assert metrics.volume_mm3 > 0.0


def test_planting_module_phase1_bbox() -> None:
    metrics = measure_shape(build_planting_module())
    assert isclose(metrics.size_x, tower_body_diameter, abs_tol=1.0e-6)
    assert isclose(metrics.size_y, tower_body_diameter, abs_tol=1.0e-6)
    assert isclose(metrics.size_z, module_height, abs_tol=1.0e-6)
    assert max(metrics.size_x, metrics.size_y) <= tower_max_diameter


def test_phase1_shell_wall_targets() -> None:
    assert 2.4 <= module_wall_thickness <= 3.2
    assert minimum_wall_at_phase1_datum() >= 2.4
    assert plant_port_wall_thickness >= 4.0

