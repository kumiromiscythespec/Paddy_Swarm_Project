"""Odd/even module removal envelopes against neighboring services."""

from __future__ import annotations

from ps_mht_v001.assembly.port_service_sweeps_phase3a import (
    service_clearance_report,
    service_sweep_components,
)


def test_each_rotation_has_six_sweeps_for_each_of_three_ports() -> None:
    assert len(service_sweep_components(0.0)) == 18
    assert len(service_sweep_components(60.0)) == 18


def test_odd_module_sweeps_clear_neighbor_ports() -> None:
    assert service_clearance_report(0.0)["neighbor_max_mm3"] <= 1.0e-8


def test_even_module_sweeps_clear_neighbor_ports() -> None:
    assert service_clearance_report(60.0)["neighbor_max_mm3"] <= 1.0e-8


def test_odd_module_sweeps_clear_hardware_post_hose_and_interfaces() -> None:
    report = service_clearance_report(0.0)
    assert max(report.values()) <= 1.0e-8


def test_even_module_sweeps_clear_hardware_post_hose_and_interfaces() -> None:
    report = service_clearance_report(60.0)
    assert max(report.values()) <= 1.0e-8

