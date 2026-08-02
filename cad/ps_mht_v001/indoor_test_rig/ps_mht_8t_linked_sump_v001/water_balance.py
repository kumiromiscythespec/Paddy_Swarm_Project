"""Variable-preserving 4/6/8-tower water-balance calculations."""

from __future__ import annotations

from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.parameters import (
    local_sump_emergency_freeboard_l,
    local_sump_gross_capacity_l,
    local_sump_normal_volume_l,
    test_tower_counts,
    tower_buffer_per_tower_l,
    zone_target_flow_l_h,
    zone_target_flow_l_min,
)


def _range_scaled(values: tuple[float, float], count: int) -> list[float]:
    return [values[0] * count, values[1] * count]


def water_balance_for_tower_count(tower_count: int) -> dict[str, object]:
    if tower_count not in test_tower_counts:
        raise ValueError("tower_count must be 4, 6, or 8")
    local_normal = _range_scaled(local_sump_normal_volume_l, tower_count)
    local_gross = _range_scaled(local_sump_gross_capacity_l, tower_count)
    specified_freeboard = _range_scaled(
        local_sump_emergency_freeboard_l, tower_count
    )
    buffer_total = tower_buffer_per_tower_l * tower_count
    known_normal = [
        local_normal[0] + buffer_total,
        local_normal[1] + buffer_total,
    ]
    worst_geometric_headroom = (
        local_sump_gross_capacity_l[0] - local_sump_normal_volume_l[1]
    ) * tower_count
    return {
        "tower_count": tower_count,
        "local_sump_normal_total_l": local_normal,
        "tower_buffer_total_l": buffer_total,
        "known_normal_inventory_excluding_pipe_and_pump_well_l": known_normal,
        "normal_operating_total_formula_l": (
            f"{known_normal[0]:g}..{known_normal[1]:g} + V_pipe + V_pump_well"
        ),
        "local_sump_gross_total_l": local_gross,
        "specified_emergency_freeboard_total_l": specified_freeboard,
        "worst_case_geometric_empty_capacity_l": worst_geometric_headroom,
        "known_stop_return_from_tower_buffers_l": buffer_total,
        "stop_return_formula_l": f"{buffer_total:g} + V_pipe_return",
        "worst_case_headroom_after_known_tower_return_l": (
            worst_geometric_headroom - buffer_total
        ),
        "pipe_volume_l": "MEASUREMENT_PENDING",
        "pump_well_operating_volume_l": "MEASUREMENT_PENDING",
        "pump_well_required_volume_formula_l": (
            "V_minimum_submergence + V_operational_drawdown + "
            "max(0, V_stop_return + V_pipe_return - V_local_available) + "
            "V_abnormal_margin"
        ),
        "target_zone_flow_l_min": list(zone_target_flow_l_min[tower_count]),
        "target_zone_flow_l_h": list(zone_target_flow_l_h[tower_count]),
        "pump_capacity_qualified": False,
    }


def isolation_sensitivity(tower_count: int, isolated_count: int) -> dict[str, object]:
    if tower_count not in test_tower_counts:
        raise ValueError("tower_count must be 4, 6, or 8")
    if isolated_count not in (1, 2) or isolated_count >= tower_count:
        raise ValueError("isolated_count must be one or two active sumps")
    active = tower_count - isolated_count
    return {
        "tower_count": tower_count,
        "isolated_sump_count": isolated_count,
        "active_tower_count": active,
        "isolated_stable_local_volume_l": [
            5.0 * isolated_count,
            7.0 * isolated_count,
        ],
        "active_known_inventory_excluding_pipe_and_pump_well_l": [
            7.0 * active,
            9.0 * active,
        ],
        "downstream_active_sumps_disconnected": False,
        "isolation_requires_supply_closed_first": True,
    }


def emergency_supply_misopen_sensitivity() -> list[dict[str, object]]:
    return [
        {
            "detection_minutes": minutes,
            "receiver_required_before_margin_l": [0.5 * minutes, 1.0 * minutes],
            "formula": "Q_branch * t_detection + V_safety_margin",
        }
        for minutes in (5, 10, 15)
    ]


def build_water_balance_report() -> dict[str, object]:
    return {
        "status": "VARIABLE_BALANCE_COMPLETE_MEASUREMENTS_PENDING",
        "cases": {
            str(count): water_balance_for_tower_count(count)
            for count in test_tower_counts
        },
        "one_sump_isolated": {
            str(count): isolation_sensitivity(count, 1)
            for count in test_tower_counts
        },
        "two_sumps_isolated": {
            str(count): isolation_sensitivity(count, 2)
            for count in test_tower_counts
        },
        "four_unused_branches_at_four_towers": {
            "closed_branch_count": 4,
            "fluid_beyond_closed_valve_l": 0.0,
            "future_expansion_available": True,
        },
        "pump_stop": {
            "return_formula": "2 * N + V_pipe_return",
            "local_absorption_checked_before_pump_well": True,
        },
        "upper_supply_mistakenly_open_during_isolation": {
            "equalization_valve_state": "CLOSED",
            "route": "LOCAL_HIGH_OVERFLOW_TO_NON_CIRCULATING_RECEIVER",
            "sensitivity": emergency_supply_misopen_sensitivity(),
        },
        "unresolved_variables": [
            "V_pipe",
            "V_pipe_return",
            "V_pump_well",
            "V_minimum_submergence",
            "V_operational_drawdown",
            "V_abnormal_margin",
        ],
    }
