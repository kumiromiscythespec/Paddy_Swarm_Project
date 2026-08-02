"""Independent M3 nut-cartridge, slot, wall, and service tests."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.assembly.complete_port_assembly_phase3a1 import (
    complete_port_interference_report,
)
from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    m3_clearance_diameter,
    m3_fastener_pitch_radius,
    m3_port_cartridge_fastener_x,
    m3_port_retainer_arm_thickness,
    tower_max_diameter,
)
from ps_mht_v001.tower_module.m3_port_nut_cartridge import (
    build_m3_port_cartridge_removal_sweep,
    build_m3_port_nut_cartridge,
    build_m3_port_nut_cartridge_retainer,
    m3_cartridge_slot_side_wall,
    place_m3_port_nut_cartridge,
)
from ps_mht_v001.tower_module.planting_port import (
    build_m3_slot_side_wall_probe_local,
    build_m3_wall_probe_local,
    build_planting_module_with_ports_phase3a,
    build_planting_port_receiver,
    containment_ratio,
    maximum_radial_radius,
)


INTERFERENCE = complete_port_interference_report()


def _volume(model) -> float:
    return sum(solid.Volume() for solid in model.solids().vals())


def test_m3_cartridge_and_gate_are_independent_valid_parts() -> None:
    cartridge = measure_shape(build_m3_port_nut_cartridge())
    gate = measure_shape(build_m3_port_nut_cartridge_retainer())
    assert cartridge.solid_count == 1 and cartridge.all_solids_valid
    assert gate.solid_count == 1 and gate.all_solids_valid


def test_both_m3_cartridges_have_clear_external_removal_sweeps() -> None:
    for side in (-1, 1):
        assert INTERFERENCE[
            f"cartridge_removal_{side:+d}_to_receiver_mm3"
        ] <= 1.0e-8


def test_installed_m3_cartridges_are_inside_external_insertion_sweeps() -> None:
    for side in (-1, 1):
        cartridge = place_m3_port_nut_cartridge(
            build_m3_port_nut_cartridge(),
            side,
        )
        sweep = build_m3_port_cartridge_removal_sweep(side)
        assert containment_ratio(sweep, cartridge) >= 0.999


def test_m3_nut_cannot_drop_through_root_side_floor() -> None:
    nut_drop = (
        cq.Workplane("XY")
        .center(m3_port_cartridge_fastener_x, 0.0)
        .circle(3.2)
        .extrude(2.0)
        .translate((0.0, 0.0, -0.8))
    )
    assert _volume(build_m3_port_nut_cartridge().intersect(nut_drop)) > 1.0


def test_normal_m3_axis_passes_gate_arm_capture_hole() -> None:
    gate = build_m3_port_nut_cartridge_retainer()
    bolt = (
        cq.Workplane("XY")
        .center(-7.2, 0.0)
        .circle(0.5 * m3_clearance_diameter)
        .extrude(3.0)
        .translate((0.0, 0.0, 6.8))
    )
    assert _volume(gate.intersect(bolt)) <= 1.0e-8
    assert gate.faces("%Cylinder").size() >= 1


def test_m3_cartridges_clear_netpot_removal_envelope() -> None:
    for side in (-1, 1):
        assert INTERFERENCE[
            f"cartridge_{side:+d}_to_netpot_sweep_mm3"
        ] <= 1.0e-8


def test_m3_cartridges_clear_collapsed_root_sleeve() -> None:
    for side in (-1, 1):
        assert INTERFERENCE[
            f"cartridge_{side:+d}_to_root_sleeve_mm3"
        ] <= 1.0e-8


def test_actual_m3_boss_wall_is_at_least_five_mm() -> None:
    receiver = build_planting_port_receiver()
    for y in (-m3_fastener_pitch_radius, m3_fastener_pitch_radius):
        assert containment_ratio(receiver, build_m3_wall_probe_local(y)) >= 0.999


def test_actual_cartridge_slot_lateral_walls_are_three_mm() -> None:
    receiver = build_planting_port_receiver()
    assert m3_cartridge_slot_side_wall(0.40) >= 4.8
    for side in (-1, 1):
        assert containment_ratio(
            receiver,
            build_m3_slot_side_wall_probe_local(side),
        ) >= 0.999


def test_rigid_gate_minimum_thickness_is_2_4mm() -> None:
    assert m3_port_retainer_arm_thickness >= 2.4


def test_corrected_module_remains_inside_240mm_diameter() -> None:
    module = build_planting_module_with_ports_phase3a()
    assert 2.0 * maximum_radial_radius(module) <= tower_max_diameter
