"""Flat planting-port ring, backing, liner, and root-ring gates."""

from __future__ import annotations

from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    netpot_siawadeky_body_diameter_pending,
    netpot_siawadeky_flange_diameter_assumed,
    netpot_siawadeky_height_assumed,
    port_function_ring_inner_diameter,
    root_mesh_initial_length,
)
from ps_mht_v001.tower_module.netpot_seat_ring_phase3r import (
    STATUS as NETPOT_STATUS,
    build_netpot_seat_ring_phase3r,
    netpot_body_passage_diameter,
)
from ps_mht_v001.tower_module.port_backing_ring_phase3r import (
    NUT_POCKET_COUNT,
    build_backing_ring_drain_service_probe_phase3r,
    build_backing_ring_root_passage_probe_phase3r,
    build_port_backing_ring_phase3r,
)
from ps_mht_v001.tower_module.port_function_ring_phase3r import (
    ROUNDNESS_DATUM,
    build_port_function_ring_phase3r,
    port_function_ring_minimum_hole_surround,
)
from ps_mht_v001.tower_module.root_sleeve_ring_phase3r import (
    LOAD_TESTS_PENDING_G,
    RETENTION,
    build_root_sleeve_ring_phase3r,
)


def _volume(model) -> float:
    return sum(solid.Volume() for solid in model.solids().vals())


def test_port_roundness_datum_is_a_valid_flat_ring() -> None:
    metrics = measure_shape(build_port_function_ring_phase3r())
    assert metrics.solid_count == 1 and metrics.all_solids_valid
    assert metrics.size_z == 8.0
    assert ROUNDNESS_DATUM == "GENERATED_IN_FLAT_XY_PLANE"


def test_port_function_ring_small_hole_surround_exceeds_3mm() -> None:
    assert port_function_ring_minimum_hole_surround() >= 3.0


def test_siawadeky_flange_seats_while_body_value_remains_pending() -> None:
    passage = netpot_body_passage_diameter()
    assert passage < netpot_siawadeky_flange_diameter_assumed
    assert port_function_ring_inner_diameter > passage
    assert netpot_siawadeky_body_diameter_pending is None
    assert netpot_siawadeky_height_assumed == 70.0
    assert NETPOT_STATUS == "REFERENCE_PRELIMINARY_CALIBRATION_PENDING"


def test_netpot_liner_and_function_ring_assemble_without_overlap() -> None:
    function_ring = build_port_function_ring_phase3r()
    liner = build_netpot_seat_ring_phase3r()
    assert _volume(function_ring.intersect(liner)) <= 1.0e-8


def test_backing_ring_clears_root_and_drain_service_probes() -> None:
    backing = build_port_backing_ring_phase3r()
    assert _volume(
        backing.intersect(build_backing_ring_root_passage_probe_phase3r())
    ) <= 1.0e-8
    assert _volume(
        backing.intersect(build_backing_ring_drain_service_probe_phase3r())
    ) <= 1.0e-8
    assert NUT_POCKET_COUNT == 2


def test_root_sleeve_ring_is_large_continuous_flat_part() -> None:
    metrics = measure_shape(build_root_sleeve_ring_phase3r())
    assert metrics.solid_count == 1 and metrics.all_solids_valid
    assert min(metrics.size_x, metrics.size_y) >= 80.0
    assert "NO_POSITIVE_SNAP" in RETENTION


def test_root_mesh_length_and_load_gates_are_recorded() -> None:
    assert 120.0 <= root_mesh_initial_length <= 150.0
    assert LOAD_TESTS_PENDING_G == (500, 1000)
