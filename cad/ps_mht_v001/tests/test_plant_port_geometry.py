"""Phase 3A physical three-port geometry and wall/interference checks."""

from __future__ import annotations

from math import asin, degrees, isclose

from ps_mht_v001.assembly.module_pair_phase2 import module_pair_components
from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    available_fastener_angles,
    m3_fastener_pitch_radius,
    plant_port_angle,
    plant_port_center_z,
    plant_port_local_angles,
    tower_max_diameter,
)
from ps_mht_v001.tower_module.module_gasket import build_module_gasket
from ps_mht_v001.tower_module.module_interface import (
    build_fastener_boss_reference,
)
from ps_mht_v001.tower_module.planting_port import (
    build_m3_wall_probe_local,
    build_phase3a_m4_wall_probe,
    build_continuous_shell_band_probe,
    build_planting_module_with_ports_phase3a,
    build_planting_port_receiver,
    build_port_root_wall_probe_local,
    build_receiver_outer,
    build_receiver_void,
    containment_ratio,
    directional_max_radius,
    maximum_radial_radius,
    port_axis_vector,
    port_center_heights,
    receiver_pair_intersection_volumes,
    rotated_port_angles,
)


MODULE = build_planting_module_with_ports_phase3a()


def _volume(model) -> float:
    return sum(solid.Volume() for solid in model.solids().vals())


def test_exactly_three_physical_port_bores_are_open() -> None:
    for angle, center_z in zip(plant_port_local_angles, port_center_heights()):
        assert _volume(MODULE.intersect(build_receiver_void(angle, center_z))) <= 1.0e-7
    for angle in (60.0, 180.0, 300.0):
        assert _volume(
            MODULE.intersect(build_receiver_void(angle, plant_port_center_z))
        ) > 1000.0


def test_port_local_angles_are_0_120_240() -> None:
    assert plant_port_local_angles == (0.0, 120.0, 240.0)


def test_actual_port_axis_is_27_degrees_upward() -> None:
    for angle in plant_port_local_angles:
        axis = port_axis_vector(angle)
        assert isclose(degrees(asin(axis.z)), plant_port_angle, abs_tol=1.0e-9)
        assert isclose(axis.Length, 1.0, abs_tol=1.0e-9)


def test_port_centers_use_equal_85mm_candidate_a() -> None:
    assert port_center_heights("A") == (
        plant_port_center_z,
        plant_port_center_z,
        plant_port_center_z,
    )


def test_even_module_rotation_produces_60_180_300() -> None:
    assert rotated_port_angles(60.0) == (60.0, 180.0, 300.0)


def test_three_port_module_is_valid_and_within_240mm() -> None:
    metrics = measure_shape(MODULE)
    assert metrics.solid_count == 1 and metrics.all_solids_valid
    assert 2.0 * maximum_radial_radius(MODULE) <= tower_max_diameter
    for angle in plant_port_local_angles:
        assert directional_max_radius(MODULE, angle) <= 0.5 * tower_max_diameter


def test_three_saddles_do_not_intersect_each_other() -> None:
    assert max(receiver_pair_intersection_volumes()) <= 1.0e-8


def test_port_saddles_clear_m4_boss_knob_and_gasket_regions() -> None:
    receivers = [
        build_receiver_outer(angle, center_z)
        for angle, center_z in zip(plant_port_local_angles, port_center_heights())
    ]
    boss = build_fastener_boss_reference()
    knobs = [
        component.model
        for component in module_pair_components(0.0)
        if component.name.startswith("m4_knob_")
    ]
    gasket = build_module_gasket().translate((0.0, 0.0, 172.4))
    for receiver in receivers:
        assert _volume(receiver.intersect(boss)) <= 1.0e-8
        assert _volume(receiver.intersect(gasket)) <= 1.0e-8
        assert max(_volume(receiver.intersect(knob)) for knob in knobs) <= 1.0e-8


def test_actual_port_and_m3_wall_probes_are_fully_contained() -> None:
    receiver = build_planting_port_receiver()
    assert containment_ratio(receiver, build_port_root_wall_probe_local()) >= 0.999
    for y in (-m3_fastener_pitch_radius, m3_fastener_pitch_radius):
        assert containment_ratio(receiver, build_m3_wall_probe_local(y)) >= 0.999


def test_phase3a_m4_wall_and_shell_bands_are_actual_geometry() -> None:
    for angle in available_fastener_angles:
        probe = build_phase3a_m4_wall_probe(angle)
        assert containment_ratio(MODULE, probe) >= 0.999
    for z in (25.0, 143.0):
        band = build_continuous_shell_band_probe(z)
        assert containment_ratio(MODULE, band) >= 0.999
