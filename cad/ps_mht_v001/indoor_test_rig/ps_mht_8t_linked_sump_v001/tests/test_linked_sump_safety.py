"""Hydraulic safety, commercial boundary and energy tests (7)."""

import json
from pathlib import Path

from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001 import parameters as p


ROOT = Path(__file__).parents[1]


def test_eight_independent_emergency_overflows_exist() -> None:
    assert p.emergency_overflow_count == 8


def test_emergency_overflow_never_reconnects_circulation() -> None:
    assert p.emergency_overflow_destination == "NON_CIRCULATING_EMERGENCY_RECEIVER"
    assert p.emergency_overflow_reconnects_circulation is False


def test_branch_and_trunk_minimum_inner_diameters() -> None:
    assert p.local_sump_branch_inner_diameter_mm[0] >= 25.0
    assert p.common_trunk_inner_diameter_mm[0] >= 32.0


def test_common_pump_well_exists_near_trunk_midpoint() -> None:
    assert p.common_pump_well_present is True
    assert p.common_pump_well_location == "NEAR_TRUNK_MIDPOINT"


def test_discharge_bypass_is_always_available() -> None:
    assert p.pump_bypass_always_available is True


def test_energy_meter_boundary_is_circulation_pump_only() -> None:
    assert p.circulation_energy_measurement_name == "CIRCULATION_PUMP_ONLY_Wh"
    assert p.circulation_energy_includes_fresh_water_equipment is False
    assert p.circulation_energy_includes_sensors is False
    assert p.circulation_energy_includes_timer_standby is False


def test_commercial_interfaces_are_measurement_pending_and_printed_valves_forbidden() -> None:
    interfaces = json.loads(
        (ROOT / "specs" / "ps_mht_8t_linked_sump_interfaces.json").read_text(
            encoding="utf-8"
        )
    )
    assert interfaces["equalization_interface"]["final_hole_diameter_mm"] is None
    assert p.commercial_valve_status == "PHYSICAL_MEASUREMENT_PENDING"
    assert p.commercial_bulkhead_status == "PHYSICAL_MEASUREMENT_PENDING"
    assert p.printed_sliding_valve_allowed is False
    assert p.printed_thread_only_watertight_joint_allowed is False
