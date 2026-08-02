"""Purchased net-pot reference, replaceable adapter, and blank-cap checks."""

from __future__ import annotations

from math import isclose

from ps_mht_v001.common.validation import measure_shape
from ps_mht_v001.parameters import (
    netpot_body_top_outer_diameter,
    netpot_flange_outer_diameter,
    port_adapter_flange_diameter,
    port_adapter_fit_clearance,
    port_receiver_bore_diameter,
)
from ps_mht_v001.tower_module.blank_port_cap import build_blank_port_cap
from ps_mht_v001.tower_module.netpot_60_adapter import (
    build_netpot_60_adapter,
    netpot_adapter_seat_diameter,
)
from ps_mht_v001.tower_module.netpot_reference import (
    build_netpot_insertion_sweep_local,
    build_netpot_reference,
)
from ps_mht_v001.tower_module.planting_port_adapter import (
    adapter_body_outer_diameter,
    build_planting_port_adapter,
    m3_nominal_surrounding_wall,
)


def test_purchased_netpot_reference_is_one_valid_solid() -> None:
    metrics = measure_shape(build_netpot_reference())
    assert metrics.solid_count == 1 and metrics.all_solids_valid
    assert metrics.size_x == netpot_flange_outer_diameter


def test_netpot_body_enters_selected_adapter_clearance() -> None:
    assert netpot_adapter_seat_diameter() > netpot_body_top_outer_diameter
    assert isclose(
        netpot_adapter_seat_diameter() - netpot_body_top_outer_diameter,
        0.70,
        abs_tol=1.0e-9,
    )


def test_netpot_flange_stops_on_adapter_seat() -> None:
    assert netpot_flange_outer_diameter > netpot_adapter_seat_diameter()
    assert netpot_flange_outer_diameter < 72.0
    assert measure_shape(build_netpot_60_adapter()).solid_count == 1


def test_common_adapter_and_blank_cap_use_same_receiver_fit() -> None:
    adapter = measure_shape(build_planting_port_adapter())
    cap = measure_shape(build_blank_port_cap())
    assert isclose(adapter.size_x, port_adapter_flange_diameter, abs_tol=1.0e-9)
    assert isclose(cap.size_x, port_adapter_flange_diameter, abs_tol=1.0e-9)
    assert isclose(
        adapter_body_outer_diameter(),
        port_receiver_bore_diameter - 2.0 * port_adapter_fit_clearance,
        abs_tol=1.0e-9,
    )


def test_netpot_has_130mm_external_withdrawal_sweep() -> None:
    assert measure_shape(build_netpot_insertion_sweep_local()).size_z == 130.0


def test_adapter_m3_holes_have_five_mm_surrounding_wall() -> None:
    assert m3_nominal_surrounding_wall() >= 5.0
