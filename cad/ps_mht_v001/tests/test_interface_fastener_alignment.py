"""Phase 2 M4 station, knob, cartridge, and future-port checks."""

from __future__ import annotations

from math import isclose

from ps_mht_v001.assembly.module_pair_phase2 import (
    keepout_components,
    module_pair_components,
)
from ps_mht_v001.common.fasteners import (
    build_m4_nut_cartridge,
    build_m4_nut_cartridge_retainer,
)
from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    available_fastener_angles,
    future_plant_port_angles,
    interface_maximum_diameter_with_knob,
    minimum_fastener_to_port_angle,
    rear_service_angle,
    tower_max_diameter,
    used_fastener_angles,
)
from ps_mht_v001.tower_module.module_interface import (
    build_cartridge_access_probe,
    build_fastener_boss_reference,
    build_planting_module_with_interface,
)


def _rotated_set(rotation_deg: float) -> set[float]:
    return {
        (angle + rotation_deg) % 360.0
        for angle in available_fastener_angles
    }


def _intersection_volume(first, second) -> float:
    intersection = first.intersect(second)
    return sum(solid.Volume() for solid in intersection.solids().vals())


def test_six_m4_holes_align_at_zero_and_sixty_degrees() -> None:
    reference = set(available_fastener_angles)
    assert _rotated_set(0.0) == reference
    assert _rotated_set(60.0) == reference


def test_three_used_fasteners_are_120_degrees_apart() -> None:
    assert len(used_fastener_angles) == 3
    ordered = sorted(used_fastener_angles)
    gaps = (
        ordered[1] - ordered[0],
        ordered[2] - ordered[1],
        360.0 + ordered[0] - ordered[2],
    )
    assert gaps == (120.0, 120.0, 120.0)


def test_fasteners_are_midway_between_future_ports() -> None:
    assert set(future_plant_port_angles) == {
        0.0,
        60.0,
        120.0,
        180.0,
        240.0,
        300.0,
    }
    assert isclose(minimum_fastener_to_port_angle(), 30.0)


def test_rear_service_station_has_no_normal_knob() -> None:
    assert rear_service_angle == 90.0
    assert rear_service_angle not in used_fastener_angles


def test_knob_envelope_remains_inside_240mm() -> None:
    assert interface_maximum_diameter_with_knob() == 238.0
    assert interface_maximum_diameter_with_knob() <= tower_max_diameter


def test_cartridge_and_retainer_are_valid_replaceable_solids() -> None:
    cartridge = measure_shape(build_m4_nut_cartridge())
    retainer = measure_shape(build_m4_nut_cartridge_retainer())
    assert cartridge.solid_count == 1 and cartridge.all_solids_valid
    assert retainer.solid_count == 1 and retainer.all_solids_valid
    assert build_m4_nut_cartridge_retainer().faces("%Cylinder").size() >= 1


def test_all_cartridge_pockets_have_open_external_access() -> None:
    module = build_planting_module_with_interface()
    for angle in available_fastener_angles:
        assert _intersection_volume(
            module,
            build_cartridge_access_probe(angle),
        ) <= 1.0e-8


def test_installed_cartridges_retainers_and_bolts_have_clearance() -> None:
    components = module_pair_components(0.0)
    upper = next(
        component.model
        for component in components
        if component.name == "module_upper"
    )
    for angle in (30, 150, 270):
        knob = next(
            component.model
            for component in components
            if component.name == f"m4_knob_{angle:03d}"
        )
        cartridge = next(
            component.model
            for component in components
            if component.name == f"m4_nut_cartridge_{angle:03d}"
        )
        retainer = next(
            component.model
            for component in components
            if component.name == f"m4_cartridge_retainer_{angle:03d}"
        )
        assert _intersection_volume(upper, cartridge) <= 1.0e-8
        assert _intersection_volume(upper, retainer) <= 1.0e-8
        assert _intersection_volume(knob, cartridge) <= 1.0e-8
        assert _intersection_volume(knob, retainer) <= 1.0e-8


def test_fastener_hardware_does_not_intersect_port_keepouts() -> None:
    port_keepouts = [
        component.model
        for component in keepout_components()
        if component.name.startswith("future_port_axis_")
    ]
    fastener_models = [build_fastener_boss_reference()]
    fastener_models.extend(
        component.model
        for component in module_pair_components(0.0)
        if component.name.startswith("m4_knob_")
    )
    for fastener in fastener_models:
        for port in port_keepouts:
            assert _intersection_volume(fastener, port) <= 1.0e-8
