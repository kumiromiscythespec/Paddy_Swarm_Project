"""Temporary capture-ring, short assembly, and circularity gates."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.assembly.three_sector_full_height_reference_phase3sa import (
    build_three_sector_full_height_reference_phase3sa,
)
from ps_mht_v001.assembly.three_sector_short_assembly_phase3sa import (
    build_three_sector_short_assembly_phase3sa,
    short_assembly_components_phase3sa,
)
from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    phase3sa_panel_capture_depth,
    tower_max_diameter,
)
from ps_mht_v001.tower_module.planting_port import maximum_radial_radius
from ps_mht_v001.tower_module.temporary_capture_ring_phase3sa import (
    REFERENCE_EXTERNAL_BAND,
    build_temporary_panel_capture_ring_phase3sa,
    capture_ring_dimensions_phase3sa,
)


def test_temporary_ring_is_one_flat_a1_safe_part() -> None:
    metrics = measure_shape(build_temporary_panel_capture_ring_phase3sa())
    assert metrics.solid_count == 1 and metrics.all_solids_valid
    assert metrics.size_x <= 245.0 and metrics.size_y <= 245.0
    assert metrics.size_z <= 240.0


def test_upper_and_lower_rings_use_the_same_source_geometry() -> None:
    components = short_assembly_components_phase3sa(0.6)
    rings = components[3:5]
    assert rings[0].source_model == rings[1].source_model
    assert abs(
        rings[0].model.val().Volume() - rings[1].model.val().Volume()
    ) < 1.0e-6


def test_ring_grooves_capture_panels_without_solid_interference() -> None:
    components = short_assembly_components_phase3sa(0.6)
    for panel in components[:3]:
        for ring in components[3:5]:
            overlap = panel.model.intersect(ring.model)
            assert sum(
                solid.Volume() for solid in overlap.solids().vals()
            ) <= 1.0e-7


def test_capture_depth_is_within_future_reference_range() -> None:
    assert 10.0 <= phase3sa_panel_capture_depth <= 15.0
    assert capture_ring_dimensions_phase3sa()[
        "capture_depth_mm"
    ] == phase3sa_panel_capture_depth


def test_short_assembly_is_inside_240mm_diameter() -> None:
    assembly = build_three_sector_short_assembly_phase3sa(0.6)
    assert 2.0 * maximum_radial_radius(assembly) <= tower_max_diameter


def test_full_height_reference_is_inside_240mm_diameter() -> None:
    assembly = build_three_sector_full_height_reference_phase3sa(0.6)
    assert 2.0 * maximum_radial_radius(assembly) <= tower_max_diameter


def test_external_band_is_a_purchased_reference_not_a_printed_part() -> None:
    components = short_assembly_components_phase3sa(0.6)
    band = components[-1]
    assert band.source_model == REFERENCE_EXTERNAL_BAND
    assert band.category == "PURCHASED_REFERENCE_NOT_PRINTED"
