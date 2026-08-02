"""Phase 3R print-result-driven minimum feature gates."""

from __future__ import annotations

from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    module_clamping_ring_inner_diameter,
    module_clamping_ring_outer_diameter,
    module_gasket_ring_inner_diameter,
    module_gasket_ring_outer_diameter,
    module_nut_ring_inner_diameter,
    module_nut_ring_outer_diameter,
    phase3r_max_cantilever,
    phase3r_min_independent_width,
    phase3r_min_isolated_footprint,
    phase3r_min_rib_width,
    phase3r_min_root_thickness,
    phase3r_min_structural_wall,
    phase3r_preferred_root_fillet,
    port_backing_ring_width,
    port_function_ring_inner_diameter,
    port_function_ring_outer_diameter,
    root_sleeve_ring_inner_diameter_phase3r,
    root_sleeve_ring_outer_diameter_phase3r,
    vertical_thin_plate_allowed,
    wave_amplitude,
    wave_ring_base_radius,
    wave_ring_inner_diameter,
)
from ps_mht_v001.print_plate_layout_phase3r import phase3r_plate_parts


def _bottom_contact_area(model) -> float:
    return sum(face.Area() for face in model.faces("<Z").vals())


def test_phase3r_minimum_parameter_contract() -> None:
    assert phase3r_min_isolated_footprint >= 200.0
    assert phase3r_min_independent_width >= 15.0
    assert phase3r_min_structural_wall >= 3.0
    assert phase3r_min_root_thickness >= 4.0
    assert phase3r_min_rib_width >= 5.0
    assert phase3r_preferred_root_fillet >= 3.0
    assert phase3r_max_cantilever <= 10.0
    assert vertical_thin_plate_allowed is False


def test_all_phase3r_independent_parts_have_large_contact_area() -> None:
    for name, model in phase3r_plate_parts():
        assert _bottom_contact_area(model) >= phase3r_min_isolated_footprint, name


def test_all_phase3r_primary_parts_are_valid_solids() -> None:
    for name, model in phase3r_plate_parts():
        metrics = measure_shape(model)
        assert metrics.solid_count == 1, name
        assert metrics.all_solids_valid, name


def test_all_phase3r_ring_radial_widths_are_at_least_15mm() -> None:
    widths = (
        wave_ring_base_radius
        - wave_amplitude
        - 0.5 * wave_ring_inner_diameter,
        0.5 * (
            module_nut_ring_outer_diameter
            - module_nut_ring_inner_diameter
        ),
        0.5 * (
            module_clamping_ring_outer_diameter
            - module_clamping_ring_inner_diameter
        ),
        0.5 * (
            module_gasket_ring_outer_diameter
            - module_gasket_ring_inner_diameter
        ),
        0.5 * (
            port_function_ring_outer_diameter
            - port_function_ring_inner_diameter
        ),
        port_backing_ring_width,
        0.5 * (
            root_sleeve_ring_outer_diameter_phase3r
            - root_sleeve_ring_inner_diameter_phase3r
        ),
    )
    assert min(widths) >= phase3r_min_independent_width


def test_no_phase3r_primary_part_is_a_thin_vertical_plate() -> None:
    for name, model in phase3r_plate_parts():
        box = model.val().BoundingBox()
        if "shell" not in name:
            assert box.zlen <= 12.0, name
