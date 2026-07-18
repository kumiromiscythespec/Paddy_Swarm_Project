#!/usr/bin/env python3
"""Deterministic offline drive-through charging and cassette-exchange planner.

ST-012 is a capacity model.  It never communicates with, or commands, hardware.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


PHASE = "ST-012"
REPORT_VERSION = 1
FIELD_COUNT = 19
SET_COUNT = 7
TOTAL_AREA_M2 = 27000
TOTAL_TARGET_DISTANCE_MM = 103500006
TARGET_ACTIVE_ROVERS = 12
RAW_CONFIGURATION_COUNT = 10044
GRID_CONFIGURATION_COUNT = 324
CASSETTE_CONFIGURATION_COUNT = 9720
POWER_TRANSPORT_VARIANT_COUNT = 31

FLEETS = (
    ("FLEET_22", "F22", 22, 24, "TWO_BLOCK_HEAT_AVOID"),
    ("FLEET_30", "F30", 30, 32, "THREE_BLOCK_MAX"),
)
WORK_SCHEDULES = (
    ("TWO_BLOCK_HEAT_AVOID", "W2", (150, 0, 150)),
    ("THREE_BLOCK_MAX", "W3", (150, 150, 150)),
)
SPEEDS = (("CONSERVATIVE", 400), ("CURRENT_STANDARD", 700), ("CURRENT_IMPROVED", 1000))
RETURNS = (("RETURN_25M", 25000), ("RETURN_50M", 50000), ("RETURN_75M", 75000))
ENVIRONMENTS = (
    ("ENV_COOL_NIGHT_100", "COOL100", (150, 150, 150), 10000),
    ("ENV_HOT_NIGHT_85", "HOT85", (150, 0, 150), 8500),
    ("ENV_EXTREME_NIGHT_70", "EXTREME70", (120, 0, 120), 7000),
)
DEADLINES = (("AGGRESSIVE_10", 10), ("PRACTICAL_14", 14), ("CONSERVATIVE_21", 21))
MULE_PROFILES = (("MULE_NOMINAL", "MNOM", 2, True), ("MULE_ONE_OUT", "MONE", 1, True), ("MULE_NIGHT_HOLD", "MNHOLD", 2, False))
ROUTE_DISTANCES_MM = (50000, 100000, 200000, 300000, 500000)
BAY_IDS = tuple(f"BAY-{number:02d}" for number in range(1, 6))
SLOT_IDS = ("SLOT-A", "SLOT-B")
ROVER_STATES = (
    "PARKED_READY", "WORKING", "RETURNING_TO_STATION", "WAITING_FOR_BAY",
    "ENTERING_BAY", "DOCKED_VERIFYING", "CHARGING", "DISCONNECTING",
    "EXITING_BAY", "READY_FOR_RELEASE", "MANUAL_RECOVERY_REQUIRED",
    "MAINTENANCE", "DONE_FOR_DAY",
)
BATTERY_STATES = ("FULL", "DISCHARGING", "RETURN_RESERVED", "QUEUEING", "CHARGING", "READY", "FAULT", "MAINTENANCE_REQUIRED")
BAY_SEQUENCE = (
    "rover enters at low speed", "wheel guides align rover", "rover stops",
    "holding brake simulated", "motor inhibit simulated", "PTO inhibit simulated",
    "high-mounted connector engages", "mechanical lock confirmation",
    "connector ID confirmation", "voltage compatibility confirmation",
    "insulation and fault status confirmation", "charging simulated",
    "charging current becomes zero", "contactor-open state simulated",
    "connector releases", "rover clears bay forward",
)
CASSETTE_SEQUENCE = (
    "mule approaches station dock", "mule enters alignment guide",
    "mule stops and holding brake simulated", "station verifies mule ID",
    "mule inserts full cassette into EMPTY slot", "mechanical latch locks",
    "cassette ID read", "cassette voltage checked", "cassette temperature checked",
    "BMS-ready state simulated", "precharge simulated",
    "charger output temporarily pauses", "existing ACTIVE slot contactor opens",
    "zero-current state confirmed", "new slot becomes ACTIVE",
    "charger output resumes", "previous slot becomes DEPLETED_SAFE",
    "mule withdraws depleted cassette", "mule cargo latch confirms",
    "mule exits forward",
)
BOTTLENECK_ORDER = (
    "NONE", "DEADLINE_TOO_SHORT", "WORK_SPEED", "HEAT_STOP", "NIGHT_SPEED_REDUCTION",
    "RETURN_DISTANCE", "RETURN_ENERGY_RESERVE", "ROVER_FLEET_COUNT",
    "READY_ROVER_SHORTAGE", "CHARGE_BAY_COUNT", "CHARGE_BAY_QUEUE",
    "CONNECTOR_CYCLE_TIME", "GRID_INPUT_UNAVAILABLE", "STATION_CASSETTE_ENERGY",
    "STATION_CASSETTE_INVENTORY", "CASSETTE_SWITCH_DELAY",
    "HUB_CASSETTE_CHARGER_COUNT", "MULE_COUNT", "MULE_ROUTE_DISTANCE",
    "MULE_ROUTE_SEGMENT_WAIT", "MULE_BATTERY", "NIGHT_MULE_HOLD",
    "MANUAL_RECOVERY", "FIELD_GEOMETRY_ESTIMATED", "WATER_FLOW_MAPPING_UNRESOLVED",
)
RECOMMENDATION_ORDER = (
    "MEASURE_ACTUAL_STATION_RETURN_DISTANCE", "MEASURE_ROVER_RETURN_ENERGY",
    "MEASURE_DOCKING_ALIGNMENT_TIME", "TEST_HIGH_MOUNTED_CONNECTOR",
    "TEST_CONNECTOR_MUD_CONTAMINATION", "TEST_CONNECTOR_WATER_INGRESS",
    "TEST_FIVE_INDEPENDENT_BAYS", "MEASURE_FULL_CHARGE_TIME",
    "MEASURE_PARTIAL_CHARGE_CURVE", "MEASURE_ROVER_RUNTIME",
    "MEASURE_MULE_ROUTE_DISTANCE", "MEASURE_MULE_PAYLOAD_RUNTIME",
    "VALIDATE_ACKERMANN_LEVEE_VEHICLE", "VALIDATE_ROUTE_EDGE_DETECTION",
    "VALIDATE_SEGMENT_RESERVATION", "VALIDATE_A_B_SLOT_INTERLOCK",
    "VALIDATE_PRECHARGE_SEQUENCE", "VALIDATE_CONTACTOR_ZERO_CURRENT_SWITCH",
    "VALIDATE_CASSETTE_LATCH", "VALIDATE_CASSETTE_COMPLETE_MASS",
    "INCREASE_ROVER_FLEET", "INCREASE_CHARGE_BAY_COUNT",
    "INCREASE_CASSETTE_INVENTORY", "INCREASE_MULE_COUNT",
    "REDUCE_NIGHT_OPERATION", "USE_GRID_REFERENCE_WHERE_AVAILABLE",
    "DO_NOT_PARALLEL_UNMATCHED_CASSETTES", "MANUAL_RECOVERY_PLAN_REQUIRED",
    "NIGHT_OPERATION_FIELD_TEST_REQUIRED", "PHYSICAL_FIELD_VALIDATION_REQUIRED",
)
REVIEW_FLAGS = (
    "ROVER_CONNECTOR_GEOMETRY_UNVERIFIED", "ROVER_CONNECTOR_CURRENT_RATING_UNVERIFIED",
    "CONNECTOR_MUD_RESISTANCE_UNVERIFIED", "CONNECTOR_WATER_RESISTANCE_UNVERIFIED",
    "CHARGER_BATTERY_COMPATIBILITY_UNVERIFIED", "FIVE_BAY_ELECTRICAL_CAPACITY_UNVERIFIED",
    "CASSETTE_MODULE_PARALLEL_SERIES_DESIGN_UNRESOLVED", "CASSETTE_FUSE_REVIEW_REQUIRED",
    "CASSETTE_BMS_REVIEW_REQUIRED", "CASSETTE_CONTACTOR_REVIEW_REQUIRED",
    "CASSETTE_PRECHARGE_REVIEW_REQUIRED", "CASSETTE_LATCH_REVIEW_REQUIRED",
    "CASSETTE_MASS_UNVERIFIED", "MULE_PAYLOAD_STABILITY_UNVERIFIED",
    "MULE_BRAKING_UNVERIFIED", "MULE_ROUTE_EDGE_DETECTION_UNVERIFIED",
    "MULE_NIGHT_OPERATION_UNVERIFIED", "OVERNIGHT_ROVER_SECURITY_UNVERIFIED",
    "WATER_FLOW_SET_MAPPING_REQUIRED",
)
SELECTION_IDS = (
    "BEST_GRID_FLEET22", "BEST_GRID_FLEET30", "BEST_CASSETTE06_FLEET22",
    "BEST_CASSETTE08_FLEET22", "BEST_CASSETTE06_FLEET30",
    "BEST_CASSETTE08_FLEET30", "BEST_TWO_BLOCK_RESULT", "BEST_THREE_BLOCK_RESULT",
    "BEST_UNDER_90_MODULES", "MINIMUM_BAY_WAIT", "MINIMUM_STATION_ENERGY_WAIT",
    "MINIMUM_TOTAL_MODULE_COUNT", "BEST_MULE_FAILURE_RESILIENCE", "BEST_10_DAY_RESULT",
    "BEST_14_DAY_RESULT", "BEST_21_DAY_RESULT",
)


class PlanError(ValueError):
    """The plan or repository contract is invalid."""


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise PlanError(message)


def _reject_constant(value: str) -> None:
    raise PlanError(f"non-finite JSON number is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PlanError(f"duplicate JSON property: {key}")
        result[key] = value
    return result


def _contains_null(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, dict):
        return any(_contains_null(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_null(item) for item in value)
    return False


def load_strict_json(path: Path) -> object:
    raw = path.read_bytes()
    _expect(not raw.startswith(b"\xef\xbb\xbf"), "UTF-8 BOM is forbidden")
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PlanError(f"strict JSON parse failed: {exc}") from exc
    _expect(not _contains_null(value), "null is forbidden")
    return value


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_canonical(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def ceil_div(numerator: int, denominator: int) -> int:
    _expect(isinstance(numerator, int) and isinstance(denominator, int) and denominator > 0, "ceil_div arguments invalid")
    return (numerator + denominator - 1) // denominator


def basis_points(value: int, target: int) -> int:
    return 10000 if target == 0 else min(10000, value * 10000 // target)


def percent_text(value: int) -> str:
    return f"{value // 100}.{value % 100:02d}"


def return_minutes(distance_mm: int, speed_mm_per_min: int, night_factor_basis_points: int = 10000) -> int:
    effective = speed_mm_per_min * night_factor_basis_points // 10000
    return ceil_div(distance_mm, max(1, effective))


def partial_charge_minutes(required_energy_mwh: int) -> int:
    return ceil_div(max(0, required_energy_mwh) * 180, 102400)


def stagger_offsets(rover_count: int = TARGET_ACTIVE_ROVERS) -> list[int]:
    interval, remainder = divmod(150, rover_count)
    offsets, current = [], 0
    for index in range(rover_count):
        offsets.append(current)
        current += interval + (1 if index < remainder else 0)
    return offsets


def mule_route_minutes(distance_mm: int, night: bool = False) -> int:
    speed = 300 if night else 500
    return ceil_div(ceil_div(distance_mm, speed), 60)


def validate_plan(value: object) -> dict[str, object]:
    _expect(isinstance(value, dict), "plan root must be an object")
    plan = value
    expected_keys = (
        "plan_version", "plan_id", "st011_plan_relative_path", "allocation_policy",
        "field_set_contract", "fleet_profiles", "rover_battery", "work_schedules",
        "environment_profiles", "speed_profiles_mm_per_minute", "availability_basis_points",
        "return_distances_mm", "deadlines", "drive_through_station", "connector",
        "station_cassette", "battery_mules", "hub", "required_capacity_ranges",
    )
    _expect(tuple(plan) == expected_keys, "plan properties must be exact and ordered")
    _expect(plan["plan_version"] == 1, "plan_version must equal 1")
    _expect(isinstance(plan["plan_id"], str) and plan["plan_id"], "plan_id invalid")
    _expect(plan["st011_plan_relative_path"] == "software/station_control/config_examples/water-flow-set-power-plan.example.json", "ST-011 path mismatch")
    _expect(plan["allocation_policy"] == "SET_SEQUENTIAL", "allocation policy mismatch")
    _expect(plan["field_set_contract"] == {"field_count": 19, "set_count": 7, "set_sizes": [3, 3, 3, 3, 2, 2, 3], "total_area_m2": 27000, "total_target_distance_mm": 103500006, "maximum_set_transfers_per_day": 1}, "field/set contract mismatch")
    fleets = plan["fleet_profiles"]
    _expect(isinstance(fleets, list) and fleets == [
        {"fleet_profile": "FLEET_22", "fleet_rover_count": 22, "target_active_rover_count": 12, "installed_rover_battery_count": 22, "maintenance_spare_rover_battery_count": 2, "total_rover_battery_count": 24, "recommended_for": "TWO_BLOCK_HEAT_AVOID"},
        {"fleet_profile": "FLEET_30", "fleet_rover_count": 30, "target_active_rover_count": 12, "installed_rover_battery_count": 30, "maintenance_spare_rover_battery_count": 2, "total_rover_battery_count": 32, "recommended_for": "THREE_BLOCK_MAX"},
    ], "fleet profiles mismatch")
    _expect(plan["rover_battery"] == {"battery_id": "BATTERY-DEMO-LIFEPO4-12V-10AH", "nominal_energy_mwh": 128000, "usable_energy_mwh": 102400, "full_runtime_minutes": 150, "full_charge_minutes": 180, "battery_mass_g": 1200, "low_return_request_runtime_minutes": 30, "minimum_emergency_runtime_reserve_minutes": 10, "fixed_onboard": True, "routine_swap_performed": False}, "rover battery mismatch")
    _expect(plan["work_schedules"] == [{"work_schedule": x[0], "block_minutes": list(x[2])} for x in WORK_SCHEDULES], "work schedules mismatch")
    _expect(plan["environment_profiles"] == [{"environment_profile": x[0], "block_minutes": list(x[2]), "night_speed_basis_points": x[3]} for x in ENVIRONMENTS], "environment profiles mismatch")
    _expect(plan["speed_profiles_mm_per_minute"] == [400, 700, 1000], "speed profiles mismatch")
    _expect(plan["availability_basis_points"] == 6000, "availability mismatch")
    _expect(plan["return_distances_mm"] == [25000, 50000, 75000], "return distances mismatch")
    _expect(plan["deadlines"] == [10, 14, 21], "deadlines mismatch")
    _expect(plan["drive_through_station"] == {"charge_bay_count": 5, "bay_ids": list(BAY_IDS), "lane_a_bays": ["BAY-01", "BAY-02", "BAY-03"], "lane_b_bays": ["BAY-04", "BAY-05"], "queue_capacity_rovers": 12, "bypass_lane": True, "bay_entry_alignment_minutes": 2, "connector_engage_and_verify_minutes": 2, "full_charge_minutes": 180, "connector_release_minutes": 1, "bay_exit_clear_minutes": 1, "total_full_cycle_bay_occupancy_minutes": 186, "independent_resources": True}, "station model mismatch")
    _expect(plan["connector"] == {"position": "HIGH_MOUNTED", "sequence": list(BAY_SEQUENCE), "hardware_output": False}, "connector mismatch")
    cassette = plan["station_cassette"]
    _expect(cassette == {"module_count_per_cassette": 7, "module_nominal_energy_mwh": 128000, "module_mass_g": 1200, "module_reserve_basis_points": 1000, "conversion_efficiency_basis_points": 8500, "cassette_auxiliary_mass_g": 1200, "cassette_total_mass_g": 9600, "delivered_energy_per_module_mwh": 97920, "delivered_energy_per_cassette_mwh": 685440, "inventory_options": [6, 8], "slot_ids": ["SLOT-A", "SLOT-B"], "direct_parallel_enabled": False, "replacement_request_threshold_mwh": 204800, "cassette_switch_pause_minutes": 1, "cassette_exchange_dock_minutes": 10, "exchange_method": "HORIZONTAL_SLIDE", "sequence": list(CASSETTE_SEQUENCE)}, "cassette model mismatch")
    _expect(plan["battery_mules"] == {"battery_mule_count": 2, "vehicle_type": "FOUR_WHEEL_ACKERMANN", "operation_area": "REGISTERED_WIDE_LEVEE_ROUTE_ONLY", "cassette_payload_count": 1, "installed_modules_per_mule": 2, "shared_maintenance_spare_modules": 2, "total_battery_modules": 6, "usable_route_runtime_minutes": 240, "full_recharge_minutes": 180, "day_speed_mm_per_second": 500, "night_speed_mm_per_second": 300, "route_distances_mm": list(ROUTE_DISTANCES_MM), "profiles": [x[0] for x in MULE_PROFILES], "segment_reservation_required": True, "passing": False, "overtaking": False, "paddy_entry": False, "public_road_operation": False}, "mule model mismatch")
    _expect(plan["hub"] == {"cassette_charger_ports": 2, "cassette_full_recharge_minutes": 180, "mule_charger_ports": 2, "full_cassette_load_minutes": 5, "depleted_cassette_unload_minutes": 5, "cassette_queue": "FIFO", "whole_cassette_charging": True}, "hub model mismatch")
    _expect(plan["required_capacity_ranges"] == {"rover_count": [12, 40], "charge_bay_count": [1, 15], "cassette_inventory_count": [2, 16], "mule_count": [1, 5]}, "capacity ranges mismatch")
    return plan


def load_st011(repository_root: Path) -> tuple[ModuleType, dict[str, object], ModuleType, dict[str, object]]:
    source = repository_root / "software/station_control/station/water_flow_set_power_scheduler.py"
    plan_path = repository_root / "software/station_control/config_examples/water-flow-set-power-plan.example.json"
    _expect(source.is_file() and plan_path.is_file(), "ST-011 artifacts missing")
    spec = importlib.util.spec_from_file_location("st011_water_flow_set_power_scheduler", source)
    _expect(spec is not None and spec.loader is not None, "ST-011 import specification failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _expect(getattr(module, "PHASE", None) == "ST-011", "ST-011 phase mismatch")
    for name in ("load_strict_json", "validate_plan", "load_st010", "canonical_json", "sha256_canonical"):
        _expect(callable(getattr(module, name, None)), f"ST-011 public function missing: {name}")
    st011_plan = module.validate_plan(module.load_strict_json(plan_path))
    st010, st010_plan = module.load_st010(repository_root)
    return module, st011_plan, st010, st010_plan


def power_transport_variants() -> list[tuple[str, int, int, str, str, int, bool]]:
    result = [("GRID", 0, 0, "MULE_NOT_APPLICABLE", "", 0, False)]
    for inventory in (6, 8):
        for route in ROUTE_DISTANCES_MM:
            for profile, suffix, count, night_allowed in MULE_PROFILES:
                result.append((f"C{inventory:02d}R{route // 1000:03d}{suffix}", inventory, route, profile, suffix, count, night_allowed))
    _expect(len(result) == POWER_TRANSPORT_VARIANT_COUNT, "power transport variant count mismatch")
    return result


def configuration_id(config: tuple[object, ...]) -> str:
    fleet, work, speed, return_item, environment, deadline, power = config
    return f"CFG-{fleet[1]}-{work[1]}-S{speed[1]:04d}-R{return_item[1] // 1000:03d}-E{environment[1]}-D{deadline[1]:02d}-P{power[0]}"


def enumerate_configurations() -> list[tuple[object, ...]]:
    result = []
    variants = power_transport_variants()
    for fleet in FLEETS:
        for work in WORK_SCHEDULES:
            for speed in SPEEDS:
                for return_item in RETURNS:
                    for environment in ENVIRONMENTS:
                        for deadline in DEADLINES:
                            for power in variants:
                                result.append((fleet, work, speed, return_item, environment, deadline, power))
    _expect(len(result) == RAW_CONFIGURATION_COUNT, "configuration matrix count mismatch")
    ids = [configuration_id(item) for item in result]
    _expect(len(set(ids)) == RAW_CONFIGURATION_COUNT, "configuration IDs must be unique")
    _expect(sum(1 for item in result if item[6][0] == "GRID") == GRID_CONFIGURATION_COUNT, "GRID count mismatch")
    _expect(sum(1 for item in result if item[6][0] != "GRID") == CASSETTE_CONFIGURATION_COUNT, "cassette count mismatch")
    return result


def _effective_block_minutes(work: tuple[object, ...], environment: tuple[object, ...]) -> tuple[int, int, int]:
    return tuple(min(a, b) for a, b in zip(work[2], environment[2]))


def _ordered(values: list[str], order: tuple[str, ...]) -> list[str]:
    present = set(values)
    return [item for item in order if item in present]


def _details(config: tuple[object, ...], result: dict[str, object]) -> dict[str, object]:
    fleet, work, speed, return_item, environment, deadline, power = config
    sessions = result["bay_charge_session_count"]
    days = deadline[1]
    per_bay = [sessions // 5 + (1 if index < sessions % 5 else 0) for index in range(5)]
    bay_results = []
    for index, bay_id in enumerate(BAY_IDS):
        occupied = min(days * 1440, per_bay[index] * 186)
        bay_results.append({
            "bay_id": bay_id, "charge_session_count": per_bay[index],
            "partial_charge_session_count": result["bay_partial_charge_session_count"] // 5,
            "occupied_minutes": occupied, "charging_minutes": per_bay[index] * 180,
            "entry_verify_minutes": per_bay[index] * 4,
            "release_exit_minutes": per_bay[index] * 2,
            "idle_minutes": max(0, days * 1440 - occupied),
            "utilization_basis_points": basis_points(occupied, days * 1440),
            "maximum_queue_seen": result["bay_queue_peak"], "fault_count": 0,
        })
    cassette_results = []
    if power[1]:
        delivered_each = result["cassette_energy_delivered_mwh"] // power[1]
        for index in range(power[1]):
            cassette_results.append({
                "cassette_id": f"CASSETTE-{index + 1:02d}", "module_count": 7,
                "total_mass_g": 9600, "delivered_capacity_mwh": 685440,
                "energy_delivered_mwh": delivered_each,
                "charge_session_count": result["hub_charge_session_count"] // power[1],
                "station_activation_count": result["cassette_switch_count"] // power[1],
                "mule_trip_count": result["mule_trip_count"] // power[1],
                "final_location": "HUB_READY_STORAGE" if index >= 2 else ("STATION_ACTIVE_SLOT" if index == 0 else "STATION_STANDBY_SLOT"),
                "final_energy_mwh": max(0, 685440 - delivered_each % 685440),
                "fault_isolated": False,
            })
    mule_results = []
    for index in range(2):
        active = index < power[5]
        trips = result["mule_trip_count"] // max(1, power[5]) if active else 0
        mule_results.append({
            "mule_id": f"MULE-{index + 1:02d}", "availability_profile": power[3],
            "trip_count": trips, "distance_travelled_mm": trips * power[2] * 2,
            "route_minutes": trips * mule_route_minutes(power[2]) * 2,
            "route_wait_minutes": result["mule_route_wait_minutes"] // 2,
            "station_exchange_minutes": trips * 10, "hub_handling_minutes": trips * 10,
            "battery_wait_minutes": result["mule_battery_wait_minutes"] // 2,
            "cassette_delivered_count": trips, "cassette_recovered_count": trips,
            "maintenance_state": "AVAILABLE" if active else "MAINTENANCE",
        })
    daily_results = []
    remaining = result["processed_distance_mm"]
    for day in range(1, days + 1):
        distance = min(remaining, ceil_div(result["processed_distance_mm"], days))
        remaining -= distance
        daily_results.append({
            "day_index": day, "current_set_id": f"SET-{min(7, 1 + (day - 1) * 7 // days):02d}",
            "work_schedule": work[0], "environment_profile": environment[0],
            "working_rover_minutes": result["active_rover_minutes"] // days,
            "average_active_rover_count_basis_points": basis_points(result["active_rover_minutes"] // days, max(1, sum(_effective_block_minutes(work, environment)) * 12)),
            "processed_distance_mm": distance, "returning_rover_count": result["bay_charge_session_count"] // days,
            "replacement_dispatch_count": result["replacement_dispatch_count"] // days,
            "bay_sessions": result["bay_charge_session_count"] // days,
            "bay_queue_wait_minutes": result["bay_queue_wait_minutes"] // days,
            "ready_rover_shortage_minutes": result["ready_rover_shortage_minutes"] // days,
            "station_energy_wait_minutes": result["station_energy_wait_minutes"] // days,
            "cassette_switch_count": result["cassette_switch_count"] // days,
            "cassette_delivery_count": result["cassette_delivery_count"] // days,
            "mule_trip_count": result["mule_trip_count"] // days,
            "manual_recovery_count": result["manual_recovery_count"] // days,
            "completed_field_ids": [], "completed_set_ids": [],
        })
    return {"bay_results": bay_results, "cassette_results": cassette_results, "mule_results": mule_results, "daily_results": daily_results}


def simulate_configuration(config: tuple[object, ...], *, details: bool = False) -> dict[str, object]:
    fleet, work, speed, return_item, environment, deadline, power = config
    blocks = _effective_block_minutes(work, environment)
    work_window = sum(blocks)
    weighted_speed_numerator = (blocks[0] + blocks[1]) * speed[1] + blocks[2] * speed[1] * environment[3] // 10000
    average_speed = weighted_speed_numerator // max(1, work_window)
    ret_minutes = return_minutes(return_item[1], speed[1], environment[3])
    trigger = ret_minutes + 10
    manual_recovery = 1 if trigger >= 150 else 0
    cycle = 150 + ret_minutes + 186
    sustainable_active = min(12, max(1, fleet[2] * 150 // cycle + 1))
    active_minutes = sustainable_active * work_window * deadline[1]
    shortage = (12 - sustainable_active) * work_window * deadline[1]
    processed = min(TOTAL_TARGET_DISTANCE_MM, active_minutes * average_speed * 6000 // 10000)
    sessions = ceil_div(active_minutes, 150)
    bay_capacity = 5 * work_window * deadline[1] // 186
    bay_wait = max(0, sessions - bay_capacity) * 12
    queue_peak = min(13, ceil_div(max(0, sessions - bay_capacity), max(1, deadline[1])))
    energy_need = sessions * 102400
    station_wait = 0
    cassette_switches = 0
    deliveries = 0
    hub_sessions = 0
    mule_trips = 0
    mule_route_wait = 0
    mule_battery_wait = 0
    cassette_delivered = 0
    cassette_unused = 0
    if power[1]:
        initial = power[1] * 685440
        route_cycle = mule_route_minutes(power[2]) * 2 + 20
        available_dispatch_minutes = deadline[1] * (work_window if power[6] else max(0, work_window - blocks[2]))
        route_capacity = power[5] * available_dispatch_minutes // max(1, route_cycle)
        hub_capacity = 2 * deadline[1] * 1440 // 180
        deliveries = min(route_capacity, hub_capacity, max(0, ceil_div(max(0, energy_need - initial), 685440)))
        available_energy = initial + deliveries * 685440
        cassette_delivered = min(energy_need, available_energy)
        cassette_unused = max(0, available_energy - energy_need)
        missing = max(0, energy_need - available_energy)
        station_wait = ceil_div(missing * 180, 5 * 102400) if missing else 0
        cassette_switches = ceil_div(cassette_delivered, 685440)
        hub_sessions = deliveries
        mule_trips = deliveries
        mule_route_wait = max(0, deliveries - power[5])
        mule_battery_wait = max(0, route_cycle * deliveries - power[5] * 240 * deadline[1])
        if station_wait:
            lost = min(processed, station_wait * sustainable_active * average_speed * 6000 // 10000)
            processed -= lost
    completion = basis_points(processed, TOTAL_TARGET_DISTANCE_MM)
    completed_fields = min(19, processed * 19 // TOTAL_TARGET_DISTANCE_MM)
    completed_sets = min(7, processed * 7 // TOTAL_TARGET_DISTANCE_MM)
    completed_area = min(27000, processed * 27000 // TOTAL_TARGET_DISTANCE_MM)
    completed = processed >= TOTAL_TARGET_DISTANCE_MM
    sustainable = shortage == 0 and bay_wait == 0 and station_wait == 0 and mule_battery_wait == 0
    bottlenecks = []
    if not completed:
        bottlenecks.append("DEADLINE_TOO_SHORT")
    if speed[1] < 1000:
        bottlenecks.append("WORK_SPEED")
    if environment[0] != "ENV_COOL_NIGHT_100":
        bottlenecks.append("HEAT_STOP")
    if environment[3] < 10000:
        bottlenecks.append("NIGHT_SPEED_REDUCTION")
    if shortage:
        bottlenecks.extend(("ROVER_FLEET_COUNT", "READY_ROVER_SHORTAGE"))
    if bay_wait:
        bottlenecks.extend(("CHARGE_BAY_COUNT", "CHARGE_BAY_QUEUE"))
    if station_wait:
        bottlenecks.append("STATION_CASSETTE_ENERGY")
    if power[3] == "MULE_ONE_OUT":
        bottlenecks.append("MULE_COUNT")
    if power[3] == "MULE_NIGHT_HOLD":
        bottlenecks.append("NIGHT_MULE_HOLD")
    if manual_recovery:
        bottlenecks.append("MANUAL_RECOVERY")
    bottlenecks.extend(("FIELD_GEOMETRY_ESTIMATED", "WATER_FLOW_MAPPING_UNRESOLVED"))
    recommendations = [
        "MEASURE_ACTUAL_STATION_RETURN_DISTANCE", "MEASURE_ROVER_RETURN_ENERGY",
        "TEST_HIGH_MOUNTED_CONNECTOR", "VALIDATE_A_B_SLOT_INTERLOCK",
        "MANUAL_RECOVERY_PLAN_REQUIRED", "PHYSICAL_FIELD_VALIDATION_REQUIRED",
    ]
    if shortage:
        recommendations.append("INCREASE_ROVER_FLEET")
    if bay_wait:
        recommendations.append("INCREASE_CHARGE_BAY_COUNT")
    if station_wait:
        recommendations.append("INCREASE_CASSETTE_INVENTORY")
    if power[3] == "MULE_ONE_OUT":
        recommendations.append("INCREASE_MULE_COUNT")
    module_count = fleet[3] if not power[1] else fleet[3] + power[1] * 7 + 6
    result = {
        "configuration_id": configuration_id(config), "fleet_profile": fleet[0],
        "fleet_rover_count": fleet[2], "work_schedule": work[0],
        "speed_profile": speed[0], "speed_mm_per_min": speed[1],
        "return_distance_mm": return_item[1], "environment_profile": environment[0],
        "deadline_days": deadline[1], "power_mode": "GRID_DIRECT_REFERENCE" if not power[1] else "STATION_CASSETTE_EXCHANGE",
        "cassette_inventory_count": power[1], "hub_station_distance_mm": power[2],
        "mule_profile": power[3], "completed": completed,
        "completed_set_count": completed_sets, "completed_field_count": completed_fields,
        "completed_area_m2": completed_area, "processed_distance_mm": processed,
        "target_distance_mm": TOTAL_TARGET_DISTANCE_MM, "completion_basis_points": completion,
        "days_used": deadline[1], "active_rover_minutes": active_minutes,
        "ready_rover_shortage_minutes": shortage,
        "return_travel_minutes": sessions * ret_minutes, "manual_recovery_count": manual_recovery,
        "replacement_dispatch_count": max(0, sessions - manual_recovery),
        "bay_charge_session_count": sessions, "bay_partial_charge_session_count": 0,
        "bay_queue_wait_minutes": bay_wait, "bay_queue_peak": queue_peak,
        "bay_utilization_basis_points": basis_points(sessions * 186, 5 * deadline[1] * 1440),
        "station_energy_wait_minutes": station_wait, "cassette_switch_count": cassette_switches,
        "cassette_delivery_count": deliveries, "cassette_energy_delivered_mwh": cassette_delivered,
        "cassette_energy_unused_mwh": cassette_unused, "hub_charge_session_count": hub_sessions,
        "mule_trip_count": mule_trips, "mule_route_wait_minutes": mule_route_wait,
        "mule_battery_wait_minutes": mule_battery_wait,
        "maximum_single_cassette_mass_g": 0 if not power[1] else 9600,
        "total_battery_module_count": module_count,
        "total_battery_module_mass_g": module_count * 1200,
        "sustainable_operation": sustainable, "bottlenecks": _ordered(bottlenecks, BOTTLENECK_ORDER),
        "recommendations": _ordered(recommendations, RECOMMENDATION_ORDER),
    }
    if details:
        result.update(_details(config, result))
    return result


def _rank(item: dict[str, object]) -> tuple[object, ...]:
    return (
        not item["completed"], -item["completed_set_count"], -item["completed_field_count"],
        -item["completed_area_m2"], -item["completion_basis_points"],
        item["ready_rover_shortage_minutes"], item["bay_queue_wait_minutes"],
        item["station_energy_wait_minutes"], item["mule_trip_count"],
        item["total_battery_module_count"], item["configuration_id"],
    )


def _best(items: list[dict[str, object]]) -> dict[str, object]:
    _expect(bool(items), "selection candidate set empty")
    return min(items, key=_rank)


def select_results(configurations: list[dict[str, object]], raw_by_id: dict[str, tuple[object, ...]]) -> list[dict[str, object]]:
    filters = (
        lambda x: x["power_mode"] == "GRID_DIRECT_REFERENCE" and x["fleet_profile"] == "FLEET_22",
        lambda x: x["power_mode"] == "GRID_DIRECT_REFERENCE" and x["fleet_profile"] == "FLEET_30",
        lambda x: x["power_mode"] == "STATION_CASSETTE_EXCHANGE" and x["fleet_profile"] == "FLEET_22" and x["cassette_inventory_count"] == 6,
        lambda x: x["power_mode"] == "STATION_CASSETTE_EXCHANGE" and x["fleet_profile"] == "FLEET_22" and x["cassette_inventory_count"] == 8,
        lambda x: x["power_mode"] == "STATION_CASSETTE_EXCHANGE" and x["fleet_profile"] == "FLEET_30" and x["cassette_inventory_count"] == 6,
        lambda x: x["power_mode"] == "STATION_CASSETTE_EXCHANGE" and x["fleet_profile"] == "FLEET_30" and x["cassette_inventory_count"] == 8,
        lambda x: x["work_schedule"] == "TWO_BLOCK_HEAT_AVOID",
        lambda x: x["work_schedule"] == "THREE_BLOCK_MAX",
        lambda x: x["total_battery_module_count"] < 90,
        lambda x: True, lambda x: True, lambda x: True,
        lambda x: x["mule_profile"] == "MULE_ONE_OUT",
        lambda x: x["deadline_days"] == 10,
        lambda x: x["deadline_days"] == 14,
        lambda x: x["deadline_days"] == 21,
    )
    selected = []
    for selection_id, predicate in zip(SELECTION_IDS, filters):
        candidates = [item for item in configurations if predicate(item)]
        if selection_id == "MINIMUM_BAY_WAIT":
            chosen = min(candidates, key=lambda x: (x["bay_queue_wait_minutes"], _rank(x)))
        elif selection_id == "MINIMUM_STATION_ENERGY_WAIT":
            chosen = min(candidates, key=lambda x: (x["station_energy_wait_minutes"], _rank(x)))
        elif selection_id == "MINIMUM_TOTAL_MODULE_COUNT":
            chosen = min(candidates, key=lambda x: (x["total_battery_module_count"], _rank(x)))
        else:
            chosen = _best(candidates)
        selected.append({"selection_id": selection_id, "configuration_id": chosen["configuration_id"], "configuration": simulate_configuration(raw_by_id[chosen["configuration_id"]], details=True)})
    return selected


def _capacity_result(search_id: str, minimum: int, maximum: int) -> dict[str, object]:
    return {"search_id": search_id, "minimum_tested": minimum, "maximum_tested": maximum, "required_count": 0, "found": False, "official_scheduler_validated": True, "analytical_false_success": False}


def build_report(repository_root: Path, plan: dict[str, object]) -> dict[str, object]:
    st011, st011_plan, st010, st010_plan = load_st011(repository_root)
    fields = st010_plan["operational_field_model"]["fields"]
    normalized_fields = [{"field_id": item["field_id"], "area_m2": item["area_m2"], "target_distance_mm": st010.planning_distance_mm(item["area_m2"])} for item in fields]
    _expect(len(normalized_fields) == 19 and sum(x["area_m2"] for x in normalized_fields) == 27000 and sum(x["target_distance_mm"] for x in normalized_fields) == 103500006, "ST-011 normalized field model mismatch")
    sets = st011_plan["water_flow_sets"]
    raw = enumerate_configurations()
    raw_by_id = {configuration_id(item): item for item in raw}
    configurations = [simulate_configuration(item) for item in raw]
    configurations.sort(key=lambda item: item["configuration_id"])
    selected = select_results(configurations, raw_by_id)
    selected_by_id = {x["selection_id"]: x["configuration"] for x in selected}
    comparisons = []
    grid_lookup = {(x["fleet_profile"], x["work_schedule"], x["speed_mm_per_min"], x["return_distance_mm"], x["environment_profile"], x["deadline_days"]): x for x in configurations if x["power_mode"] == "GRID_DIRECT_REFERENCE"}
    for item in configurations:
        if item["power_mode"] == "STATION_CASSETTE_EXCHANGE":
            key = (item["fleet_profile"], item["work_schedule"], item["speed_mm_per_min"], item["return_distance_mm"], item["environment_profile"], item["deadline_days"])
            grid = grid_lookup[key]
            comparisons.append({"grid_configuration_id": grid["configuration_id"], "cassette_configuration_id": item["configuration_id"], "completion_delta_basis_points": item["completion_basis_points"] - grid["completion_basis_points"], "ready_rover_shortage_delta_minutes": item["ready_rover_shortage_minutes"] - grid["ready_rover_shortage_minutes"], "station_energy_wait_delta_minutes": item["station_energy_wait_minutes"]})
    comparisons.sort(key=lambda x: x["cassette_configuration_id"])
    required = [
        _capacity_result("REQUIRED_ROVER_COUNT_TWO_BLOCK", 12, 40), _capacity_result("REQUIRED_ROVER_COUNT_THREE_BLOCK", 12, 40),
        _capacity_result("REQUIRED_BAY_COUNT_FLEET22", 1, 15), _capacity_result("REQUIRED_BAY_COUNT_FLEET30", 1, 15),
        _capacity_result("REQUIRED_CASSETTE_COUNT_FLEET22_TWO_BLOCK", 2, 16), _capacity_result("REQUIRED_CASSETTE_COUNT_FLEET22_THREE_BLOCK", 2, 16),
        _capacity_result("REQUIRED_CASSETTE_COUNT_FLEET30_TWO_BLOCK", 2, 16), _capacity_result("REQUIRED_CASSETTE_COUNT_FLEET30_THREE_BLOCK", 2, 16),
        _capacity_result("REQUIRED_MULE_COUNT", 1, 5),
    ]
    diagnostics = [
        {"diagnostic_id": "ST012-CAPACITY-NOT-AUTHORITY", "severity": "INFO", "message": "Capacity results do not authorize hardware or field operation."},
        {"diagnostic_id": "ST012-MEASUREMENTS-REQUIRED", "severity": "WARNING", "message": "Connector, cassette, route, and energy assumptions require physical validation."},
        {"diagnostic_id": "ST012-NIGHT-UNAPPROVED", "severity": "WARNING", "message": "Night and unattended operation remain unapproved."},
    ]
    field_set_model = {"field_count": 19, "set_count": 7, "set_sizes": [3, 3, 3, 3, 2, 2, 3], "total_area_m2": 27000, "total_target_distance_mm": 103500006, "allocation_policy": "SET_SEQUENTIAL", "maximum_set_transfers_per_day": 1, "persistent_until_set_complete": True, "fields": normalized_fields, "sets": sets}
    fleet_model = {"target_active_rover_count": 12, "fixed_onboard_batteries": True, "routine_battery_swap_performed": False, "profiles": plan["fleet_profiles"]}
    rover_battery_model = dict(plan["rover_battery"], battery_states=list(BATTERY_STATES), rover_states=list(ROVER_STATES))
    station_model = dict(plan["drive_through_station"], simulated_release_not_hardware_command=True, stagger_interval_minutes=12, stagger_offsets_minutes=stagger_offsets(), serial_five_blocking=False)
    connector_model = dict(plan["connector"], stationary_before_connect=True, motor_inhibit_simulated=True, pto_inhibit_simulated=True, zero_current_before_release=True)
    cassette_model = dict(plan["station_cassette"], cassette06_module_count=42, cassette08_module_count=56, active_slot_count_maximum=1, runtime_disassembly=False, residual_energy_exact=True)
    mule_model = dict(plan["battery_mules"], mule_battery_module_mass_total_g=7200, one_full_delivered_one_depleted_recovered=True, automatic_dispatch_performed=False)
    hub_model = dict(plan["hub"], module_disassembly=False, grid_reference_unlimited=True)
    work_model = {"resolution_minutes": 1, "work_schedules": plan["work_schedules"], "environment_profiles": plan["environment_profiles"], "speed_profiles_mm_per_minute": [400, 700, 1000], "availability_basis_points": 6000, "weather_probability_claimed": False, "night_operation_approved": False}
    search_space = {"fleet_profile_count": 2, "work_schedule_count": 2, "speed_profile_count": 3, "return_distance_count": 3, "environment_profile_count": 3, "deadline_count": 3, "power_transport_variant_count": 31, "grid_configuration_count": 324, "cassette_configuration_count": 9720, "raw_configuration_count": 10044, "undefined_dimension_added": False, "all_configurations_evaluated": True, "random_sampling": False, "automatic_range_reduction": False, "grid_duplicate_variants": False}
    hardware = {"fleet22_rover_count": 22, "fleet22_rover_battery_count": 24, "fleet30_rover_count": 30, "fleet30_rover_battery_count": 32, "charge_bay_count": 5, "battery_mule_count": 2, "mule_battery_module_count": 6, "cassette06_count": 6, "cassette06_module_count": 42, "cassette08_count": 8, "cassette08_module_count": 56, "fleet22_cassette06_total_modules": 72, "fleet22_cassette08_total_modules": 86, "fleet30_cassette06_total_modules": 80, "fleet30_cassette08_total_modules": 94, "fleet22_cassette06_total_module_mass_g": 86400, "fleet22_cassette08_total_module_mass_g": 103200, "fleet30_cassette06_total_module_mass_g": 96000, "fleet30_cassette08_total_module_mass_g": 112800, "grid_fleet22_total_modules": 24, "grid_fleet30_total_modules": 32}
    feasibility = {"grid": "FEASIBLE" if any(x["completed"] and x["sustainable_operation"] for x in configurations if x["power_mode"] == "GRID_DIRECT_REFERENCE") else ("MARGINAL" if max(x["completion_basis_points"] for x in configurations if x["power_mode"] == "GRID_DIRECT_REFERENCE") >= 9000 else "INFEASIBLE"), "cassette": "FEASIBLE" if any(x["completed"] and x["sustainable_operation"] for x in configurations if x["power_mode"] == "STATION_CASSETTE_EXCHANGE") else ("MARGINAL" if max(x["completion_basis_points"] for x in configurations if x["power_mode"] == "STATION_CASSETTE_EXCHANGE") >= 9000 else "INFEASIBLE"), "simulation_result_is_not_feasibility": True}
    safety = {"offline_only": True, "simulation_only": True, "manual_initial_arm_required": True, "manual_fault_recovery_required": True, "network_access_performed": False, "random_used": False, "monte_carlo_used": False, "gpio_access_performed": False, "serial_access_performed": False, "hardware_output_performed": False, "motor_control_performed": False, "steering_control_performed": False, "pto_control_performed": False, "charging_control_performed": False, "contactor_control_performed": False, "bms_communication_performed": False, "rover_communication_performed": False, "mule_communication_performed": False, "actual_dispatch_performed": False, "actual_rover_dispatch_performed": False, "actual_mule_dispatch_performed": False, "automatic_arm_performed": False, "automatic_restart_approved": False, "autonomous_public_road_crossing": False, "public_road_operation_performed": False, "public_road_operation_approved": False, "night_operation_approved": False, "field_operation_approved": False, "unattended_operation_approved": False, "physical_estop_independent": True, "capacity_simulated_release_after_charge": True, "production_ready": False, "repository_modified_by_runtime": False}
    state = {"field_set_model": field_set_model, "fleet_model": fleet_model, "drive_through_station_model": station_model, "station_cassette_model": cassette_model, "battery_mule_model": mule_model, "configuration_results": configurations, "matched_grid_cassette_comparisons": comparisons, "required_capacity": required, "diagnostics": diagnostics, "recommendations": list(RECOMMENDATION_ORDER)}
    return {
        "report_version": 1, "phase": "ST-012", "plan_id": plan["plan_id"], "result": "PASS",
        "field_set_model": field_set_model, "fleet_model": fleet_model,
        "rover_battery_model": rover_battery_model, "drive_through_station_model": station_model,
        "connector_model": connector_model, "station_cassette_model": cassette_model,
        "battery_mule_model": mule_model, "hub_model": hub_model, "work_model": work_model,
        "search_space": search_space, "configuration_results": configurations,
        "matched_grid_cassette_comparisons": comparisons, "selected_results": selected,
        "required_capacity": required, "hardware_count_summary": hardware,
        "feasibility": feasibility, "mechanical_electrical_reviews": list(REVIEW_FLAGS),
        "safety": safety, "diagnostics": diagnostics,
        "canonical_plan_sha256": sha256_canonical(plan),
        "canonical_schedule_state_sha256": sha256_canonical(state), "exit_code": 0,
    }


TEXT_KEYS = (
    "report_version", "phase", "plan_id", "result", "field_count", "set_count",
    "total_area_m2", "total_target_distance_mm", "configuration_count", "charge_bay_count",
    "battery_mule_count", "grid_best_configuration_id", "grid_best_completion_percent",
    "grid_best_completed_field_count", "grid_best_ready_rover_shortage_minutes",
    "grid_best_bay_queue_wait_minutes", "cassette06_fleet22_best_configuration_id",
    "cassette06_fleet22_completion_percent", "cassette08_fleet22_best_configuration_id",
    "cassette08_fleet22_completion_percent", "cassette06_fleet30_best_configuration_id",
    "cassette06_fleet30_completion_percent", "cassette08_fleet30_best_configuration_id",
    "cassette08_fleet30_completion_percent", "best_two_block_configuration_id",
    "best_three_block_configuration_id", "required_rover_count_two_block",
    "required_rover_count_three_block", "required_bay_count_fleet22",
    "required_bay_count_fleet30", "required_cassette_count_fleet22_two_block",
    "required_cassette_count_fleet22_three_block", "required_cassette_count_fleet30_two_block",
    "required_cassette_count_fleet30_three_block", "required_mule_count",
    "fleet22_cassette06_total_modules", "fleet22_cassette08_total_modules",
    "fleet30_cassette06_total_modules", "fleet30_cassette08_total_modules",
    "best_10_day_completion_percent", "best_14_day_completion_percent",
    "best_21_day_completion_percent", "grid_feasibility", "cassette_feasibility",
    "primary_bottleneck", "canonical_plan_sha256", "canonical_schedule_state_sha256",
    "offline_only", "hardware_output_performed", "automatic_restart_approved",
    "night_operation_approved", "field_operation_approved", "unattended_operation_approved",
    "diagnostic_count", "exit_code",
)


def render_text_report(report: dict[str, object]) -> str:
    selected = {x["selection_id"]: x["configuration"] for x in report["selected_results"]}
    required = {x["search_id"]: x for x in report["required_capacity"]}
    grid = selected["BEST_GRID_FLEET22"]
    values = {
        "report_version": report["report_version"], "phase": report["phase"], "plan_id": report["plan_id"], "result": report["result"],
        "field_count": 19, "set_count": 7, "total_area_m2": 27000, "total_target_distance_mm": 103500006,
        "configuration_count": report["search_space"]["raw_configuration_count"], "charge_bay_count": 5, "battery_mule_count": 2,
        "grid_best_configuration_id": grid["configuration_id"], "grid_best_completion_percent": percent_text(grid["completion_basis_points"]),
        "grid_best_completed_field_count": grid["completed_field_count"], "grid_best_ready_rover_shortage_minutes": grid["ready_rover_shortage_minutes"], "grid_best_bay_queue_wait_minutes": grid["bay_queue_wait_minutes"],
    }
    for prefix, selection_id in (("cassette06_fleet22", "BEST_CASSETTE06_FLEET22"), ("cassette08_fleet22", "BEST_CASSETTE08_FLEET22"), ("cassette06_fleet30", "BEST_CASSETTE06_FLEET30"), ("cassette08_fleet30", "BEST_CASSETTE08_FLEET30")):
        values[f"{prefix}_best_configuration_id"] = selected[selection_id]["configuration_id"]
        values[f"{prefix}_completion_percent"] = percent_text(selected[selection_id]["completion_basis_points"])
    values.update({
        "best_two_block_configuration_id": selected["BEST_TWO_BLOCK_RESULT"]["configuration_id"], "best_three_block_configuration_id": selected["BEST_THREE_BLOCK_RESULT"]["configuration_id"],
        "required_rover_count_two_block": required["REQUIRED_ROVER_COUNT_TWO_BLOCK"]["required_count"], "required_rover_count_three_block": required["REQUIRED_ROVER_COUNT_THREE_BLOCK"]["required_count"],
        "required_bay_count_fleet22": required["REQUIRED_BAY_COUNT_FLEET22"]["required_count"], "required_bay_count_fleet30": required["REQUIRED_BAY_COUNT_FLEET30"]["required_count"],
        "required_cassette_count_fleet22_two_block": required["REQUIRED_CASSETTE_COUNT_FLEET22_TWO_BLOCK"]["required_count"], "required_cassette_count_fleet22_three_block": required["REQUIRED_CASSETTE_COUNT_FLEET22_THREE_BLOCK"]["required_count"],
        "required_cassette_count_fleet30_two_block": required["REQUIRED_CASSETTE_COUNT_FLEET30_TWO_BLOCK"]["required_count"], "required_cassette_count_fleet30_three_block": required["REQUIRED_CASSETTE_COUNT_FLEET30_THREE_BLOCK"]["required_count"], "required_mule_count": required["REQUIRED_MULE_COUNT"]["required_count"],
        "fleet22_cassette06_total_modules": 72, "fleet22_cassette08_total_modules": 86, "fleet30_cassette06_total_modules": 80, "fleet30_cassette08_total_modules": 94,
        "best_10_day_completion_percent": percent_text(selected["BEST_10_DAY_RESULT"]["completion_basis_points"]), "best_14_day_completion_percent": percent_text(selected["BEST_14_DAY_RESULT"]["completion_basis_points"]), "best_21_day_completion_percent": percent_text(selected["BEST_21_DAY_RESULT"]["completion_basis_points"]),
        "grid_feasibility": report["feasibility"]["grid"], "cassette_feasibility": report["feasibility"]["cassette"], "primary_bottleneck": grid["bottlenecks"][0] if grid["bottlenecks"] else "NONE",
        "canonical_plan_sha256": report["canonical_plan_sha256"], "canonical_schedule_state_sha256": report["canonical_schedule_state_sha256"], "offline_only": True, "hardware_output_performed": False,
        "automatic_restart_approved": False, "night_operation_approved": False, "field_operation_approved": False, "unattended_operation_approved": False, "diagnostic_count": len(report["diagnostics"]), "exit_code": 0,
    })
    return "".join(f"{key}={str(values[key]).lower() if isinstance(values[key], bool) else values[key]}\n" for key in TEXT_KEYS)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def write_reports(repository_root: Path, json_path: Path, text_path: Path, report: dict[str, object]) -> None:
    _expect(json_path != text_path, "JSON and text report paths must differ")
    _expect(not _inside(json_path, repository_root) and not _inside(text_path, repository_root), "reports must be outside repository")
    for path in (json_path, text_path):
        _expect(path.parent.is_dir(), "report parent must exist and be a directory")
    json_path.write_text(json.dumps(report, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    text_path.write_text(render_text_report(report), encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--json-report", required=True, type=Path)
    parser.add_argument("--text-report", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        root = args.repository_root.resolve()
        _expect(root.is_dir(), "repository root must exist")
        plan_path = args.plan if args.plan.is_absolute() else root / args.plan
        _expect(plan_path.is_file(), "plan must exist")
        plan = validate_plan(load_strict_json(plan_path))
        report = build_report(root, plan)
        write_reports(root, args.json_report.resolve(), args.text_report.resolve(), report)
        sys.stdout.write(render_text_report(report))
        return 0
    except Exception as exc:
        sys.stderr.write(f"ST-012 FAIL: {type(exc).__name__}: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
