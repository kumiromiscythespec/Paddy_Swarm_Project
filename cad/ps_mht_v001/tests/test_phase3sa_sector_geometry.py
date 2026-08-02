"""Phase 3S-A identical-sector geometry and cyclic assembly gates."""

from __future__ import annotations

from math import isclose

import cadquery as cq

from ps_mht_v001.assembly.three_sector_full_height_reference_phase3sa import (
    full_height_panel_models_phase3sa,
    full_height_reference_component_policy_phase3sa,
)
from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    phase3sa_panel_height,
    phase3sa_sector_angle_deg,
    phase3sa_sector_count,
    phase3sa_shell_outer_radius,
    phase3sa_shell_wall,
)
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    PART_COUNT_PER_MODULE,
    PORT_COUNT_PER_PANEL,
    build_sector_panel_phase3sa,
)


def test_three_120_degree_panels_make_360_degrees() -> None:
    assert phase3sa_sector_count == 3
    assert phase3sa_sector_angle_deg * phase3sa_sector_count == 360.0


def test_one_identical_source_panel_is_instanced_three_times() -> None:
    panels = full_height_panel_models_phase3sa(0.6)
    volumes = [panel.val().Volume() for panel in panels]
    assert PART_COUNT_PER_MODULE == 3
    assert len(panels) == 3
    assert max(volumes) - min(volumes) < 1.0e-6
    assert full_height_reference_component_policy_phase3sa()[
        "panel_source_count"
    ] == 1


def test_port_and_seam_angles_follow_the_cyclic_contract() -> None:
    policy = full_height_reference_component_policy_phase3sa()
    assert policy["port_centers_deg"] == (0.0, 120.0, 240.0)
    assert policy["seam_centers_deg"] == (60.0, 180.0, 300.0)
    assert PORT_COUNT_PER_PANEL == 1


def test_full_height_panel_is_one_valid_170mm_solid() -> None:
    metrics = measure_shape(build_sector_panel_phase3sa(0.6))
    assert metrics.solid_count == 1 and metrics.all_solids_valid
    assert isclose(metrics.size_z, phase3sa_panel_height, abs_tol=1.0e-7)


def test_shell_radius_and_structural_wall_remain_nominal() -> None:
    assert phase3sa_shell_outer_radius == 100.0
    assert phase3sa_shell_wall >= 3.0


def test_three_panels_have_zero_prohibited_mutual_intersection() -> None:
    panels = full_height_panel_models_phase3sa(0.6)
    for first_index in range(3):
        for second_index in range(first_index + 1, 3):
            overlap = panels[first_index].intersect(panels[second_index])
            volume = sum(
                solid.Volume() for solid in overlap.solids().vals()
            )
            assert volume <= 1.0e-7


def test_cyclic_rotation_keeps_each_panel_a_single_solid() -> None:
    source = build_sector_panel_phase3sa(0.6)
    for angle in (0.0, 120.0, 240.0):
        rotated = source.rotate(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
            angle,
        )
        assert measure_shape(rotated).solid_count == 1
