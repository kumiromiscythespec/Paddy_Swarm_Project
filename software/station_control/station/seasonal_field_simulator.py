#!/usr/bin/env python3
"""Deterministic offline seasonal field-operations simulator for ST-008."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Callable, Sequence


REPORT_VERSION = 1
PHASE = "ST-008"
PLAN_VERSION = 1
SCENARIO_IDS = (
    "BASELINE", "CONSERVATIVE", "WET_FIELD", "ONE_ROVER_DOWN",
    "CARRIER_BOTTLENECK", "COMBINED_BAD",
)
SPEED_NAMES = ("LOW", "STANDARD", "IMPROVED")
WEED_SCHEDULES = ("STANDARD", "BAD_WEATHER")
BOTTLENECK_ORDER = (
    "NONE", "DISTANCE_CAPACITY", "BATTERY_AVAILABILITY", "SEED_REFILL",
    "WEATHER_AVAILABILITY", "ROVER_FAILURE", "WEED_ROVER_COUNT",
    "HIGH_CUT_SPEED", "CASSETTE_BUFFER", "CARRIER_CAPACITY", "CARRIER_COUNT",
    "MANUAL_RECOVERY_LIMIT", "CHARGER_COUNT",
)
RECOMMENDATION_ORDER = (
    "BROADCAST_ADD_WORK_DAY_OR_SPEED", "WEED_THIRD_ROVER_COMPARISON_REQUIRED",
    "WEED_PRIORITY_MANUAL_INTERVENTION_REQUIRED", "HIGH_CUT_CAPACITY_INSUFFICIENT",
    "CASSETTE_LOGISTICS_REDESIGN_REQUIRED", "CARRIER_BATCH_RACK_REQUIRED",
    "MANUAL_RECOVERY_TARGET_UNREALISTIC", "BATTERY_OR_CHARGER_CAPACITY_INSUFFICIENT",
    "BATTERY_SPARE_MARGIN_ZERO", "ONE_KG_CASSETTE_COUNT_HIGH",
    "ONE_KG_CASSETTE_FULL_FIELD_CRITICAL",
)
BROADCAST_SPEEDS = (600, 900, 1200)
WEED_SPEEDS = (400, 700, 1000)
HIGH_CUT_SPEEDS = (350, 600, 900)
CARRIER_EMPTY_SPEEDS = (800, 1200, 1600)
CARRIER_LOADED_FACTORS = (6000, 7000, 8000)
UNIT_ID = "FIELD-DEMO-001"
PLAN_ID_PATTERN = re.compile(r"^PLAN-ST008-[A-Z0-9-]{1,40}$")
SCENARIO_SIGNATURES = (
    ("STANDARD", 3250, "STANDARD", "STANDARD", "STANDARD", "STANDARD", 20000, 2, 10, 4, 2, 4, 2, 16, 4, 180, 10000, False, False, False),
    ("LOW", 3500, "STANDARD", "LOW", "LOW", "LOW", 22000, 1, 10, 4, 2, 4, 2, 16, 4, 210, 9000, False, False, False),
    ("LOW", 3500, "BAD_WEATHER", "LOW", "LOW", "LOW", 25000, 1, 10, 4, 2, 4, 2, 16, 4, 210, 8500, False, False, False),
    ("STANDARD", 3250, "STANDARD", "STANDARD", "STANDARD", "STANDARD", 20000, 2, 10, 4, 2, 4, 2, 16, 4, 180, 10000, True, True, True),
    ("STANDARD", 3250, "STANDARD", "STANDARD", "STANDARD", "STANDARD", 20000, 1, 10, 4, 2, 4, 1, 16, 4, 180, 10000, False, False, False),
    ("LOW", 3500, "BAD_WEATHER", "LOW", "LOW", "LOW", 25000, 1, 0, 4, 2, 4, 1, 16, 3, 240, 8500, True, True, True),
)


class SeasonFailure(RuntimeError):
    def __init__(self, code: str, component: str, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.component = component
        self.message = message
        self.exit_code = exit_code


@dataclass(frozen=True)
class SimulatorArguments:
    repository_root: Path
    plan: Path
    json_report: Path
    text_report: Path


@dataclass(frozen=True)
class SimulationReport:
    document: dict[str, object]
    exit_code: int


@dataclass(frozen=True)
class BatteryResult:
    sessions_started: int
    swaps: int
    charger_sessions: int
    charger_utilization_basis_points: int
    battery_wait_minutes: int
    minimum_charged_inventory: int
    peak_in_use: int
    pool_sufficient: bool
    work_minutes_completed: int


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise SeasonFailure("SEASON_INVALID_ARGUMENT", "cli", "Invalid command arguments.", 2)


def parse_arguments(argv: Sequence[str] | None = None) -> SimulatorArguments:
    parser = SafeArgumentParser()
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--json-report", required=True)
    parser.add_argument("--text-report", required=True)
    values = parser.parse_args(argv)
    return SimulatorArguments(
        Path(values.repository_root), Path(values.plan),
        Path(values.json_report), Path(values.text_report),
    )


def is_contained(candidate: Path, parent: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(parent.resolve(strict=True))
        return True
    except (OSError, ValueError):
        return False


def validate_arguments(arguments: SimulatorArguments) -> None:
    if not arguments.repository_root.is_dir():
        raise SeasonFailure("SEASON_REPOSITORY_ROOT_INVALID", "path", "Repository root is invalid.", 2)
    if not arguments.plan.is_file():
        raise SeasonFailure("SEASON_PLAN_PATH_INVALID", "path", "Plan file does not exist.", 2)
    if arguments.json_report == arguments.text_report:
        raise SeasonFailure("SEASON_INVALID_ARGUMENT", "path", "Report paths must differ.", 2)
    for report in (arguments.json_report, arguments.text_report):
        if not report.parent.is_dir() or report.parent.is_file():
            raise SeasonFailure("SEASON_REPORT_PARENT_INVALID", "path", "Report parent is invalid.", 2)
        if is_contained(report, arguments.repository_root):
            raise SeasonFailure(
                "SEASON_REPORT_PATH_INSIDE_REPOSITORY", "path",
                "Report must be outside the repository.", 2,
            )


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SeasonFailure("SEASON_PLAN_INVALID", "plan", "Duplicate JSON key.", 3)
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise SeasonFailure("SEASON_PLAN_INVALID", "plan", "Non-finite number is prohibited.", 3)


def _reject_null(value: object) -> None:
    if value is None:
        raise SeasonFailure("SEASON_PLAN_INVALID", "plan", "Null is prohibited.", 3)
    if type(value) is dict:
        for item in value.values():
            _reject_null(item)
    elif type(value) is list:
        for item in value:
            _reject_null(item)


def load_strict_json(path: Path) -> object:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
        _reject_null(value)
        return value
    except SeasonFailure:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise SeasonFailure("SEASON_PLAN_INVALID", "plan", "Plan is not strict JSON.", 3) from exc


def _exact(value: object, keys: tuple[str, ...], context: str) -> dict[str, object]:
    if type(value) is not dict or tuple(value.keys()) != keys:
        raise SeasonFailure("SEASON_PLAN_INVALID", "plan", f"{context} properties are invalid.", 3)
    return value


def _integer(value: object, minimum: int, maximum: int, context: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise SeasonFailure("SEASON_PLAN_INVALID", "plan", f"{context} is invalid.", 3)
    return value


def _boolean(value: object, context: str) -> bool:
    if type(value) is not bool:
        raise SeasonFailure("SEASON_PLAN_INVALID", "plan", f"{context} is invalid.", 3)
    return value


def _enum(value: object, choices: tuple[str, ...], context: str) -> str:
    if type(value) is not str or value not in choices:
        raise SeasonFailure("SEASON_PLAN_INVALID", "plan", f"{context} is invalid.", 3)
    return value


def ceil_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise SeasonFailure("SEASON_SIMULATION_FAILED", "model", "Invalid divisor.", 4)
    return (numerator + denominator - 1) // denominator


def round_half_up(value: Fraction) -> int:
    if value < 0:
        return -round_half_up(-value)
    return (value.numerator * 2 + value.denominator) // (value.denominator * 2)


def basis_points(value: int, target: int) -> int:
    if target <= 0:
        return 0
    return min(10000, (value * 10000) // target)


def canonical_json(value: object, *, sort_keys: bool = True) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=sort_keys,
        separators=(",", ":"), allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_plan(value: object) -> dict[str, object]:
    root_keys = ("plan_version", "plan_id", "field", "battery_model", "assumptions", "scenarios")
    plan = _exact(value, root_keys, "plan")
    if _integer(plan["plan_version"], 1, 1, "plan version") != PLAN_VERSION:
        raise SeasonFailure("SEASON_PLAN_INVALID", "plan", "Unsupported plan version.", 3)
    if type(plan["plan_id"]) is not str or PLAN_ID_PATTERN.fullmatch(plan["plan_id"]) is None:
        raise SeasonFailure("SEASON_PLAN_INVALID", "plan", "Plan ID is invalid.", 3)
    field = _exact(plan["field"], (
        "field_id", "field_length_mm", "field_width_mm", "field_area_m2",
        "work_width_mm", "turn_alignment_overhead_basis_points",
        "weed_priority_treatment_basis_points",
    ), "field")
    if field["field_id"] != UNIT_ID:
        raise SeasonFailure("SEASON_FIELD_GEOMETRY_INVALID", "geometry", "Field ID is invalid.", 3)
    length = _integer(field["field_length_mm"], 1, 1_000_000, "field length")
    width = _integer(field["field_width_mm"], 1, 1_000_000, "field width")
    area = _integer(field["field_area_m2"], 1, 1_000_000, "field area")
    work_width = _integer(field["work_width_mm"], 1, width, "work width")
    _integer(field["turn_alignment_overhead_basis_points"], 0, 10000, "overhead")
    _integer(field["weed_priority_treatment_basis_points"], 0, 10000, "priority treatment")
    if length * width != area * 1_000_000:
        raise SeasonFailure("SEASON_FIELD_AREA_MISMATCH", "geometry", "Field area does not match dimensions.", 3)
    if work_width <= 0:
        raise SeasonFailure("SEASON_WORK_WIDTH_INVALID", "geometry", "Work width is invalid.", 3)
    battery = _exact(plan["battery_model"], (
        "battery_id", "nominal_voltage_mv", "capacity_mah", "nominal_energy_mwh",
        "reserve_basis_points", "usable_energy_mwh", "battery_pool_count", "charger_count",
        "planned_charge_minutes", "initial_fully_charged_battery_count",
        "broadcast_runtime_minutes", "weed_runtime_minutes", "high_cut_runtime_minutes",
        "carrier_runtime_minutes",
    ), "battery model")
    if battery["battery_id"] != "BATTERY-DEMO-LIFEPO4-12V-10AH":
        raise SeasonFailure("SEASON_BATTERY_MODEL_INVALID", "battery", "Battery ID is invalid.", 3)
    for key in battery:
        if key != "battery_id":
            _integer(battery[key], 1 if key not in ("reserve_basis_points",) else 0, 10_000_000, key)
    if battery["nominal_voltage_mv"] * battery["capacity_mah"] // 1000 != battery["nominal_energy_mwh"]:
        raise SeasonFailure("SEASON_BATTERY_MODEL_INVALID", "battery", "Nominal energy is inconsistent.", 3)
    usable = battery["nominal_energy_mwh"] * (10000 - battery["reserve_basis_points"]) // 10000
    if usable != battery["usable_energy_mwh"]:
        raise SeasonFailure("SEASON_BATTERY_MODEL_INVALID", "battery", "Usable energy is inconsistent.", 3)
    assumptions = _exact(plan["assumptions"], (
        "battery_swap_minutes", "seed_refill_minutes", "high_cut_cassette_swap_minutes",
        "carrier_pickup_seconds_per_cassette", "carrier_drop_seconds_per_cassette",
        "grain_mass_g", "cassette_capacity_g", "active_cassette_count_per_rover",
        "spare_cassette_count_per_rover", "in_field_temporary_drop_allowed",
        "single_side_collection_hub", "collection_side", "temporary_drop_slot_count",
        "carrier_average_one_way_distance_mm",
    ), "assumptions")
    for key in assumptions:
        if key in ("in_field_temporary_drop_allowed", "single_side_collection_hub"):
            _boolean(assumptions[key], key)
        elif key == "collection_side":
            if assumptions[key] != "SHORT_SIDE_A":
                raise SeasonFailure("SEASON_PLAN_INVALID", "plan", "Collection side is invalid.", 3)
        else:
            _integer(assumptions[key], 1, 10_000_000, key)
    scenarios = plan["scenarios"]
    if type(scenarios) is not list or len(scenarios) != 6:
        raise SeasonFailure("SEASON_SCENARIO_INVALID", "scenario", "Exactly six scenarios are required.", 3)
    seen: set[str] = set()
    scenario_keys = (
        "scenario_id", "broadcast_speed", "broadcast_seed_mass_g", "weed_schedule",
        "weed_speed", "high_cut_speed", "carrier_speed", "harvest_factor_basis_points",
        "carrier_cassettes_per_trip", "manual_recovery_per_day", "broadcast_rovers",
        "weed_rovers", "high_cut_rovers", "carrier_rovers", "battery_pool", "chargers",
        "charge_minutes", "battery_runtime_factor_basis_points", "broadcast_failure_half_capacity",
        "weed_failure_half_capacity", "high_cut_failure_half_capacity",
    )
    for index, raw in enumerate(scenarios):
        scenario = _exact(raw, scenario_keys, f"scenario {index}")
        scenario_id = _enum(scenario["scenario_id"], SCENARIO_IDS, "scenario ID")
        if scenario_id in seen:
            raise SeasonFailure("SEASON_SCENARIO_DUPLICATE", "scenario", "Scenario ID is duplicated.", 3)
        seen.add(scenario_id)
        if scenario_id != SCENARIO_IDS[index]:
            raise SeasonFailure("SEASON_SCENARIO_INVALID", "scenario", "Scenario order is invalid.", 3)
        _enum(scenario["broadcast_speed"], SPEED_NAMES, "broadcast speed")
        _integer(scenario["broadcast_seed_mass_g"], 3000, 3500, "seed mass")
        _enum(scenario["weed_schedule"], WEED_SCHEDULES, "weed schedule")
        _enum(scenario["weed_speed"], SPEED_NAMES, "weed speed")
        _enum(scenario["high_cut_speed"], SPEED_NAMES, "high-cut speed")
        _enum(scenario["carrier_speed"], SPEED_NAMES, "carrier speed")
        _integer(scenario["harvest_factor_basis_points"], 10000, 30000, "harvest factor")
        if scenario["carrier_cassettes_per_trip"] not in (1, 2, 4):
            raise SeasonFailure("SEASON_SCENARIO_INVALID", "scenario", "Carrier capacity is invalid.", 3)
        if scenario["manual_recovery_per_day"] not in (0, 10, 20):
            raise SeasonFailure("SEASON_SCENARIO_INVALID", "scenario", "Manual recovery is invalid.", 3)
        for key in ("broadcast_rovers", "weed_rovers", "high_cut_rovers", "carrier_rovers", "battery_pool", "chargers", "charge_minutes", "battery_runtime_factor_basis_points"):
            _integer(scenario[key], 1, 10000, key)
        for key in ("broadcast_failure_half_capacity", "weed_failure_half_capacity", "high_cut_failure_half_capacity"):
            _boolean(scenario[key], key)
        if tuple(scenario[key] for key in scenario_keys[1:]) != SCENARIO_SIGNATURES[index]:
            raise SeasonFailure("SEASON_SCENARIO_INVALID", "scenario", "Fixed scenario values are invalid.", 3)
    return plan


def derive_geometry(field: dict[str, object]) -> dict[str, int]:
    length = int(field["field_length_mm"])
    width = int(field["field_width_mm"])
    work_width = int(field["work_width_mm"])
    lanes = ceil_div(width, work_width)
    pure = lanes * length
    full = pure * (10000 + int(field["turn_alignment_overhead_basis_points"])) // 10000
    priority = full * int(field["weed_priority_treatment_basis_points"]) // 10000
    return {
        "lane_count": lanes, "pure_full_pass_distance_mm": pure,
        "full_pass_distance_mm": full, "weed_priority_distance_mm": priority,
        "weed_total_target_distance_mm": full + priority,
    }


def _speed(name: str, values: tuple[int, int, int]) -> int:
    return values[SPEED_NAMES.index(name)]


def _effective_minutes(days: int, scheduled: int, availability: int) -> int:
    return days * (scheduled * availability // 10000)


def schedule_batteries(
    work_quotas: tuple[int, ...], runtimes: tuple[int, ...], pool_count: int,
    charger_count: int, charge_minutes: int, swap_minutes: int,
) -> BatteryResult:
    if len(work_quotas) != len(runtimes) or not work_quotas:
        raise SeasonFailure("SEASON_BATTERY_MODEL_INVALID", "battery", "Battery schedule input is invalid.", 4)
    rover_count = len(work_quotas)
    charged = pool_count - rover_count
    if charged < 0:
        charged = 0
    remaining = list(work_quotas)
    battery_remaining = list(runtimes)
    has_battery = [index < pool_count for index in range(rover_count)]
    swap_delay = [0 for _ in range(rover_count)]
    queue: list[int] = []
    charging: list[int] = []
    sessions = sum(has_battery)
    swaps = 0
    charger_sessions = 0
    waits = 0
    minimum_charged = charged
    peak_in_use = sum(has_battery)
    charger_busy_minutes = 0
    completed_work = 0
    minute = 0
    maximum_minutes = sum(work_quotas) + charge_minutes * (sum(work_quotas) // max(1, min(runtimes)) + rover_count + 2)
    while any(value > 0 for value in remaining):
        minute += 1
        if minute > maximum_minutes:
            raise SeasonFailure("SEASON_SIMULATION_FAILED", "battery", "Battery scheduler did not converge.", 4)
        completed = sum(value == minute for value in charging)
        if completed:
            charged += completed
            charging = [value for value in charging if value != minute]
        while queue and len(charging) < charger_count:
            queue.pop(0)
            charging.append(minute + charge_minutes)
            charger_sessions += 1
        charger_busy_minutes += len(charging)
        for index in range(rover_count):
            if remaining[index] <= 0:
                continue
            if swap_delay[index] > 0:
                swap_delay[index] -= 1
                continue
            if not has_battery[index]:
                if charged > 0:
                    charged -= 1
                    has_battery[index] = True
                    battery_remaining[index] = runtimes[index]
                    sessions += 1
                    swaps += 1
                    swap_delay[index] = swap_minutes
                    minimum_charged = min(minimum_charged, charged)
                else:
                    waits += 1
                continue
            remaining[index] -= 1
            completed_work += 1
            battery_remaining[index] -= 1
            if battery_remaining[index] == 0 and remaining[index] > 0:
                has_battery[index] = False
                queue.append(minute)
        peak_in_use = max(peak_in_use, sum(has_battery))
    utilization_denominator = max(1, minute * charger_count)
    utilization = min(10000, charger_busy_minutes * 10000 // utilization_denominator)
    return BatteryResult(
        sessions, swaps, charger_sessions,
        utilization, waits, minimum_charged, peak_in_use, waits == 0, completed_work,
    )


def _failure_quotas(rover_count: int, per_rover_minutes: int, failure: bool) -> tuple[int, ...]:
    quotas = [per_rover_minutes for _ in range(rover_count)]
    if failure and quotas:
        quotas[0] //= 2
    return tuple(quotas)


def _battery_runtime(base: int, factor: int) -> int:
    return max(1, base * factor // 10000)


def simulate_broadcast(
    scenario: dict[str, object], geometry: dict[str, int], battery: dict[str, object],
    assumptions: dict[str, object],
) -> tuple[dict[str, object], BatteryResult, list[str]]:
    per_rover = _effective_minutes(5, 300, 7500)
    rover_count = int(scenario["broadcast_rovers"])
    quotas = _failure_quotas(rover_count, per_rover, bool(scenario["broadcast_failure_half_capacity"]))
    runtime = _battery_runtime(int(battery["broadcast_runtime_minutes"]), int(scenario["battery_runtime_factor_basis_points"]))
    battery_result = schedule_batteries(
        quotas, tuple(runtime for _ in quotas), int(scenario["battery_pool"]),
        int(scenario["chargers"]), int(scenario["charge_minutes"]),
        int(assumptions["battery_swap_minutes"]),
    )
    seed = int(scenario["broadcast_seed_mass_g"])
    loads = ceil_div(seed, 800)
    refill_events = max(0, loads - min(rover_count, loads))
    service_minutes = refill_events * int(assumptions["seed_refill_minutes"])
    productive = max(0, battery_result.work_minutes_completed - service_minutes)
    target = geometry["full_pass_distance_mm"]
    possible = productive * _speed(str(scenario["broadcast_speed"]), BROADCAST_SPEEDS)
    processed = min(target, possible)
    seed_dispensed = seed if productive >= service_minutes else min(seed, loads * 800)
    completed = processed >= target and seed_dispensed >= seed
    shortfall = max(0, target - processed)
    bottlenecks: list[str] = []
    if shortfall:
        bottlenecks.append("DISTANCE_CAPACITY")
    if battery_result.battery_wait_minutes:
        bottlenecks.append("BATTERY_AVAILABILITY")
    if refill_events:
        bottlenecks.append("SEED_REFILL")
    if scenario["broadcast_failure_half_capacity"]:
        bottlenecks.append("ROVER_FAILURE")
    result = {
        "rover_count": rover_count,
        "available_rover_minutes": sum(quotas),
        "processed_distance_mm": processed,
        "target_distance_mm": target,
        "completion_basis_points": basis_points(processed, target),
        "shortfall_distance_mm": shortfall,
        "shortfall_area_dm2": ceil_div(shortfall * 78000, target),
        "required_extra_rover_minutes": ceil_div(shortfall, _speed(str(scenario["broadcast_speed"]), BROADCAST_SPEEDS)),
        "seed_required_g": seed,
        "seed_dispensed_g": seed_dispensed,
        "tank_load_count": loads,
        "refill_event_count": refill_events,
        "battery_swap_count": battery_result.swaps,
        "battery_wait_minutes": battery_result.battery_wait_minutes,
        "deadline_completed": completed,
    }
    return result, battery_result, bottlenecks


def simulate_weed(
    scenario: dict[str, object], geometry: dict[str, int], battery: dict[str, object],
    assumptions: dict[str, object],
) -> tuple[dict[str, object], BatteryResult, list[str]]:
    if scenario["weed_schedule"] == "STANDARD":
        days, scheduled, availability = 20, 150, 6000
    else:
        days, scheduled, availability = 14, 120, 5000
    per_rover = _effective_minutes(days, scheduled, availability)
    rover_count = int(scenario["weed_rovers"])
    quotas = _failure_quotas(rover_count, per_rover, bool(scenario["weed_failure_half_capacity"]))
    runtime = _battery_runtime(int(battery["weed_runtime_minutes"]), int(scenario["battery_runtime_factor_basis_points"]))
    battery_result = schedule_batteries(
        quotas, tuple(runtime for _ in quotas), int(scenario["battery_pool"]),
        int(scenario["chargers"]), int(scenario["charge_minutes"]),
        int(assumptions["battery_swap_minutes"]),
    )
    speed = _speed(str(scenario["weed_speed"]), WEED_SPEEDS)
    capacity = battery_result.work_minutes_completed * speed
    priority_target = geometry["weed_priority_distance_mm"]
    full_target = geometry["full_pass_distance_mm"]
    priority = min(priority_target, capacity)
    full = min(full_target, max(0, capacity - priority))
    combined = priority + full
    target = priority_target + full_target
    third_capacity = (sum(quotas) + per_rover) * speed
    third_processed = min(target, third_capacity)
    improvement = max(0, basis_points(third_processed, target) - basis_points(combined, target))
    untreated = target - combined
    bottlenecks: list[str] = []
    if untreated:
        bottlenecks.extend(("DISTANCE_CAPACITY", "WEED_ROVER_COUNT"))
    if scenario["weed_schedule"] == "BAD_WEATHER":
        bottlenecks.append("WEATHER_AVAILABILITY")
    if scenario["weed_failure_half_capacity"]:
        bottlenecks.append("ROVER_FAILURE")
    if battery_result.battery_wait_minutes:
        bottlenecks.append("BATTERY_AVAILABILITY")
    result = {
        "rover_count": rover_count,
        "available_rover_minutes": sum(quotas),
        "priority_target_distance_mm": priority_target,
        "priority_processed_distance_mm": priority,
        "priority_completion_basis_points": basis_points(priority, priority_target),
        "full_pass_target_distance_mm": full_target,
        "full_pass_processed_distance_mm": full,
        "full_pass_completion_basis_points": basis_points(full, full_target),
        "combined_completion_basis_points": basis_points(combined, target),
        "untreated_distance_mm": untreated,
        "estimated_untreated_area_dm2": ceil_div(untreated * 78000, target),
        "manual_intervention_distance_mm": max(0, priority_target - priority),
        "required_third_rover_minutes": ceil_div(untreated, speed),
        "third_rover_improvement_basis_points": improvement,
        "one_rover_down_impact_basis_points": basis_points(combined, target) - basis_points(min(target, per_rover * speed), target),
        "battery_swap_count": battery_result.swaps,
        "battery_wait_minutes": battery_result.battery_wait_minutes,
        "priority_intervention_completed": priority >= priority_target,
        "deadline_completed": priority >= priority_target and full >= full_target,
    }
    return result, battery_result, bottlenecks


def carrier_cycle_seconds(speed_name: str, cassettes_per_trip: int, assumptions: dict[str, object]) -> int:
    empty = _speed(speed_name, CARRIER_EMPTY_SPEEDS)
    factor = CARRIER_LOADED_FACTORS[SPEED_NAMES.index(speed_name)]
    loaded = empty * factor // 10000
    distance = int(assumptions["carrier_average_one_way_distance_mm"])
    empty_seconds = ceil_div(distance * 60, empty)
    loaded_seconds = ceil_div(distance * 60, loaded)
    handling = cassettes_per_trip * (
        int(assumptions["carrier_pickup_seconds_per_cassette"])
        + int(assumptions["carrier_drop_seconds_per_cassette"])
    )
    return empty_seconds + loaded_seconds + handling


def simulate_harvest(
    scenario: dict[str, object], geometry: dict[str, int], battery: dict[str, object],
    assumptions: dict[str, object],
) -> tuple[dict[str, object], BatteryResult, list[str]]:
    per_rover = _effective_minutes(7, 240, 7000)
    high_count = int(scenario["high_cut_rovers"])
    carrier_count = int(scenario["carrier_rovers"])
    high_quotas = _failure_quotas(high_count, per_rover, bool(scenario["high_cut_failure_half_capacity"]))
    carrier_quotas = tuple(per_rover for _ in range(carrier_count))
    high_runtime = _battery_runtime(int(battery["high_cut_runtime_minutes"]), int(scenario["battery_runtime_factor_basis_points"]))
    carrier_runtime = _battery_runtime(int(battery["carrier_runtime_minutes"]), int(scenario["battery_runtime_factor_basis_points"]))
    quotas = high_quotas + carrier_quotas
    runtimes = tuple(high_runtime for _ in high_quotas) + tuple(carrier_runtime for _ in carrier_quotas)
    battery_result = schedule_batteries(
        quotas, runtimes, int(scenario["battery_pool"]), int(scenario["chargers"]),
        int(scenario["charge_minutes"]), int(assumptions["battery_swap_minutes"]),
    )
    total_quota = max(1, sum(quotas))
    high_work = battery_result.work_minutes_completed * sum(high_quotas) // total_quota
    carrier_work = battery_result.work_minutes_completed - high_work
    target = geometry["full_pass_distance_mm"]
    raw_cut = min(target, high_work * _speed(str(scenario["high_cut_speed"]), HIGH_CUT_SPEEDS))
    grain = int(assumptions["grain_mass_g"])
    factor = int(scenario["harvest_factor_basis_points"])
    full_material = grain * factor // 10000
    raw_material = ceil_div(full_material * raw_cut, target) if raw_cut else 0
    raw_cassettes = ceil_div(raw_material, int(assumptions["cassette_capacity_g"])) if raw_material else 0
    per_trip = int(scenario["carrier_cassettes_per_trip"])
    cycle = carrier_cycle_seconds(str(scenario["carrier_speed"]), per_trip, assumptions)
    trips_capacity = carrier_work * 60 // cycle
    carrier_capacity = trips_capacity * per_trip
    manual_capacity = 7 * int(scenario["manual_recovery_per_day"])
    buffer_slots = int(assumptions["temporary_drop_slot_count"])
    onboard = high_count * (
        int(assumptions["active_cassette_count_per_rover"])
        + int(assumptions["spare_cassette_count_per_rover"])
    )
    generation_limit = carrier_capacity + manual_capacity + buffer_slots + onboard
    if raw_cassettes > generation_limit:
        allowed_material = generation_limit * int(assumptions["cassette_capacity_g"])
        cut = min(raw_cut, allowed_material * target // max(1, full_material))
    else:
        cut = raw_cut
    material = ceil_div(full_material * cut, target) if cut else 0
    generated = ceil_div(material, int(assumptions["cassette_capacity_g"])) if material else 0
    carrier_recovered = min(generated, carrier_capacity)
    human_recovered = min(generated - carrier_recovered, manual_capacity)
    recovered = carrier_recovered + human_recovered
    backlog = generated - recovered
    trips = ceil_div(carrier_recovered, per_trip) if carrier_recovered else 0
    cut_complete = cut >= target
    recovery_complete = backlog == 0 and cut_complete
    raw_cut_minutes = ceil_div(raw_cut, _speed(str(scenario["high_cut_speed"]), HIGH_CUT_SPEEDS)) if raw_cut else 0
    actual_cut_minutes = ceil_div(cut, _speed(str(scenario["high_cut_speed"]), HIGH_CUT_SPEEDS)) if cut else 0
    high_wait = max(0, raw_cut_minutes - actual_cut_minutes)
    required_per_trip = 0
    if carrier_count and carrier_work:
        for candidate in range(1, 101):
            candidate_cycle = carrier_cycle_seconds(str(scenario["carrier_speed"]), candidate, assumptions)
            candidate_capacity = carrier_work * 60 // candidate_cycle * candidate
            if candidate_capacity + manual_capacity >= ceil_div(full_material, int(assumptions["cassette_capacity_g"])):
                required_per_trip = candidate
                break
    required_manual = ceil_div(max(0, generated - carrier_capacity), 7)
    bottlenecks: list[str] = []
    if not cut_complete:
        bottlenecks.append("HIGH_CUT_SPEED")
    if high_wait:
        bottlenecks.append("CASSETTE_BUFFER")
    if backlog:
        bottlenecks.extend(("CARRIER_CAPACITY", "MANUAL_RECOVERY_LIMIT"))
    if carrier_count < 2:
        bottlenecks.append("CARRIER_COUNT")
    if scenario["high_cut_failure_half_capacity"]:
        bottlenecks.append("ROVER_FAILURE")
    if battery_result.battery_wait_minutes:
        bottlenecks.append("BATTERY_AVAILABILITY")
    result = {
        "high_cut_rover_count": high_count,
        "carrier_rover_count": carrier_count,
        "high_cut_processed_distance_mm": cut,
        "high_cut_target_distance_mm": target,
        "cut_completion_basis_points": basis_points(cut, target),
        "assumed_harvested_material_factor_basis_points": factor,
        "grain_mass_g": grain,
        "generated_material_g": material,
        "cassette_capacity_g": int(assumptions["cassette_capacity_g"]),
        "cassettes_generated": generated,
        "carrier_cassettes_recovered": carrier_recovered,
        "human_cassettes_recovered": human_recovered,
        "total_cassettes_recovered": recovered,
        "unrecovered_cassettes": backlog,
        "peak_in_field_cassettes": min(buffer_slots, backlog),
        "cassette_buffer_full_minutes": high_wait,
        "high_cut_cassette_wait_minutes": high_wait,
        "carrier_trip_count": trips,
        "carrier_cassettes_per_trip": per_trip,
        "average_carrier_cycle_seconds": cycle,
        "carrier_wait_or_idle_minutes": max(0, carrier_work - ceil_div(trips * cycle, 60)),
        "required_cassettes_per_trip_for_deadline": required_per_trip,
        "required_manual_recovery_per_day": required_manual,
        "cut_completed": cut_complete,
        "recovery_completed": recovery_complete,
        "system_completed": cut_complete and recovery_complete,
    }
    return result, battery_result, bottlenecks


def _battery_document(results: tuple[BatteryResult, BatteryResult, BatteryResult], scenario: dict[str, object]) -> dict[str, object]:
    sessions = sum(item.sessions_started for item in results)
    swaps = sum(item.swaps for item in results)
    waits = sum(item.battery_wait_minutes for item in results)
    return {
        "pool_count": int(scenario["battery_pool"]),
        "charger_count": int(scenario["chargers"]),
        "charge_minutes": int(scenario["charge_minutes"]),
        "sessions_started": sessions,
        "swaps": swaps,
        "charger_sessions": sum(item.charger_sessions for item in results),
        "charger_utilization_basis_points": max(item.charger_utilization_basis_points for item in results),
        "battery_wait_minutes": waits,
        "minimum_charged_inventory": min(item.minimum_charged_inventory for item in results),
        "peak_in_use": max(item.peak_in_use for item in results),
        "pool_sufficient": waits == 0,
        "recommended_spare_battery_count": 1 if min(item.minimum_charged_inventory for item in results) == 0 else 0,
    }


def _ordered_bottlenecks(items: list[str]) -> list[str]:
    unique = [item for item in BOTTLENECK_ORDER if item in items and item != "NONE"]
    return unique or ["NONE"]


def simulate_scenario(
    scenario: dict[str, object], geometry: dict[str, int], battery: dict[str, object],
    assumptions: dict[str, object],
) -> dict[str, object]:
    broadcast, broadcast_battery, broadcast_bottlenecks = simulate_broadcast(scenario, geometry, battery, assumptions)
    weed, weed_battery, weed_bottlenecks = simulate_weed(scenario, geometry, battery, assumptions)
    harvest, harvest_battery, harvest_bottlenecks = simulate_harvest(scenario, geometry, battery, assumptions)
    battery_document = _battery_document((broadcast_battery, weed_battery, harvest_battery), scenario)
    bottlenecks = _ordered_bottlenecks(broadcast_bottlenecks + weed_bottlenecks + harvest_bottlenecks)
    overall = bool(broadcast["deadline_completed"] and weed["deadline_completed"] and harvest["system_completed"])
    return {
        "scenario_id": scenario["scenario_id"],
        "execution_result": "PASS",
        "broadcast": broadcast,
        "weed": weed,
        "harvest": harvest,
        "battery": battery_document,
        "human_intervention": {
            "manual_recovery_per_day": scenario["manual_recovery_per_day"],
            "manual_recovery_capacity": int(scenario["manual_recovery_per_day"]) * 7,
            "manually_recovered": harvest["human_cassettes_recovered"],
            "manual_interventions": int(harvest["human_cassettes_recovered"] > 0),
        },
        "bottlenecks": bottlenecks,
        "overall_completed": overall,
    }


def _score(results: list[dict[str, object]], predicate: Callable[[dict[str, object]], bool]) -> dict[str, int]:
    completed = sum(predicate(item) for item in results)
    return {"completed_scenarios": completed, "total_scenarios": 6, "basis_points": completed * 10000 // 6}


def completion_scores(results: list[dict[str, object]]) -> dict[str, object]:
    return {
        "broadcast": _score(results, lambda item: bool(item["broadcast"]["deadline_completed"])),
        "weed_priority": _score(results, lambda item: bool(item["weed"]["priority_intervention_completed"])),
        "weed_full_phase": _score(results, lambda item: bool(item["weed"]["deadline_completed"])),
        "harvest_cut": _score(results, lambda item: bool(item["harvest"]["cut_completed"])),
        "harvest_system": _score(results, lambda item: bool(item["harvest"]["system_completed"])),
        "overall": _score(results, lambda item: bool(item["overall_completed"])),
    }


def classify_feasibility(results: list[dict[str, object]], scores: dict[str, object]) -> dict[str, object]:
    baseline = results[0]
    baseline_complete = bool(baseline["overall_completed"])
    phase_basis = (
        int(baseline["broadcast"]["completion_basis_points"]),
        int(baseline["weed"]["combined_completion_basis_points"]),
        min(int(baseline["harvest"]["cut_completion_basis_points"]), basis_points(
            int(baseline["harvest"]["total_cassettes_recovered"]),
            max(1, int(baseline["harvest"]["cassettes_generated"])),
        )),
    )
    shortfall = 10000 - min(phase_basis)
    overall_score = int(scores["overall"]["basis_points"])
    if baseline_complete and overall_score >= 5000:
        classification = "FEASIBLE"
    elif baseline_complete or shortfall <= 1000:
        classification = "MARGINAL"
    else:
        classification = "INFEASIBLE"
    return {
        "classification": classification,
        "baseline_completed": baseline_complete,
        "baseline_shortfall_basis_points": shortfall,
        "stress_scenario_completion_score_basis_points": overall_score,
        "field_operation_approved": False,
    }


def recommendations(results: list[dict[str, object]]) -> list[str]:
    found: set[str] = set()
    baseline = results[0]
    if not baseline["broadcast"]["deadline_completed"]:
        found.add("BROADCAST_ADD_WORK_DAY_OR_SPEED")
    if any(not item["weed"]["deadline_completed"] for item in results):
        found.add("WEED_THIRD_ROVER_COMPARISON_REQUIRED")
    if any(not item["weed"]["priority_intervention_completed"] for item in results):
        found.add("WEED_PRIORITY_MANUAL_INTERVENTION_REQUIRED")
    if any(not item["harvest"]["cut_completed"] for item in results):
        found.add("HIGH_CUT_CAPACITY_INSUFFICIENT")
    if any(int(item["harvest"]["unrecovered_cassettes"]) > 0 for item in results):
        found.add("CASSETTE_LOGISTICS_REDESIGN_REQUIRED")
    if any(int(item["harvest"]["required_cassettes_per_trip_for_deadline"]) > 4 for item in results):
        found.add("CARRIER_BATCH_RACK_REQUIRED")
    if any(int(item["harvest"]["required_manual_recovery_per_day"]) > 20 for item in results):
        found.add("MANUAL_RECOVERY_TARGET_UNREALISTIC")
    if any(int(item["battery"]["battery_wait_minutes"]) > 0 for item in results):
        found.add("BATTERY_OR_CHARGER_CAPACITY_INSUFFICIENT")
    if any(int(item["battery"]["recommended_spare_battery_count"]) > 0 for item in results):
        found.add("BATTERY_SPARE_MARGIN_ZERO")
    if any(int(item["harvest"]["cassettes_generated"]) > 500 for item in results):
        found.add("ONE_KG_CASSETTE_COUNT_HIGH")
    if any(int(item["harvest"]["cassettes_generated"]) > 1000 for item in results):
        found.add("ONE_KG_CASSETTE_FULL_FIELD_CRITICAL")
    return [item for item in RECOMMENDATION_ORDER if item in found]


def _diagnostics(results: list[dict[str, object]]) -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    for result in results:
        scenario = str(result["scenario_id"])
        checks = (
            (not result["broadcast"]["deadline_completed"], "SEASON_BROADCAST_INCOMPLETE", "broadcast", "Broadcast phase is incomplete."),
            (not result["weed"]["priority_intervention_completed"], "SEASON_WEED_PRIORITY_INCOMPLETE", "weed", "Weed priority treatment is incomplete."),
            (not result["weed"]["deadline_completed"], "SEASON_WEED_FULL_PASS_INCOMPLETE", "weed", "Weed full phase is incomplete."),
            (not result["harvest"]["cut_completed"], "SEASON_HIGH_CUT_INCOMPLETE", "harvest", "High-cut distance is incomplete."),
            (int(result["harvest"]["unrecovered_cassettes"]) > 0, "SEASON_CASSETTE_BACKLOG", "harvest", "Cassette backlog remains."),
            (int(result["harvest"]["cassette_buffer_full_minutes"]) > 0, "SEASON_CASSETTE_BUFFER_SATURATED", "harvest", "Cassette buffer reached its limit."),
            (int(result["harvest"]["unrecovered_cassettes"]) > 0, "SEASON_CARRIER_CAPACITY_INSUFFICIENT", "harvest", "Carrier capacity is insufficient."),
            (int(result["harvest"]["required_manual_recovery_per_day"]) > int(result["human_intervention"]["manual_recovery_per_day"]), "SEASON_MANUAL_RECOVERY_LIMIT", "harvest", "Manual recovery capacity is insufficient."),
            (int(result["battery"]["battery_wait_minutes"]) > 0, "SEASON_BATTERY_WAIT", "battery", "Battery waiting occurred."),
            (int(result["battery"]["battery_wait_minutes"]) > 0, "SEASON_CHARGER_CAPACITY_INSUFFICIENT", "battery", "Charger capacity is insufficient."),
        )
        for condition, code, component, message in checks:
            if condition:
                diagnostics.append({
                    "severity": "WARNING", "code": code, "component": component,
                    "scenario_id": scenario, "message": message,
                })
    diagnostics.sort(key=lambda item: (
        str(item["component"]), str(item["code"]),
        str(item["scenario_id"]), str(item["message"]),
    ))
    return diagnostics


def build_report(plan: dict[str, object]) -> SimulationReport:
    field = plan["field"]
    battery = plan["battery_model"]
    assumptions = plan["assumptions"]
    scenarios = plan["scenarios"]
    assert isinstance(field, dict) and isinstance(battery, dict)
    assert isinstance(assumptions, dict) and isinstance(scenarios, list)
    geometry = derive_geometry(field)
    results = [simulate_scenario(item, geometry, battery, assumptions) for item in scenarios]
    scores = completion_scores(results)
    feasibility = classify_feasibility(results, scores)
    all_bottlenecks = _ordered_bottlenecks([
        item for result in results for item in result["bottlenecks"] if item != "NONE"
    ])
    diagnostics = _diagnostics(results)
    plan_hash = sha256_text(canonical_json(plan))
    simulation_state = {
        "field": field, "derived_geometry": geometry,
        "operational_assumptions": {"battery_model": battery, "assumptions": assumptions},
        "scenarios": scenarios, "scenario_results": results, "summary_score": scores,
    }
    simulation_hash = sha256_text(canonical_json(simulation_state))
    document: dict[str, object] = {
        "report_version": REPORT_VERSION,
        "phase": PHASE,
        "plan_id": plan["plan_id"],
        "result": "PASS",
        "field": field,
        "derived_geometry": geometry,
        "assumptions": {
            "simulation_resolution_minutes": 1,
            "grain_mass_g": assumptions["grain_mass_g"],
            "cassette_capacity_g": assumptions["cassette_capacity_g"],
            "temporary_drop_slot_count": assumptions["temporary_drop_slot_count"],
            "single_side_collection_hub": assumptions["single_side_collection_hub"],
            "biomass_factor_engineering_assumption": True,
            "measured_crop_conversion": False,
            "field_measurement_required": True,
            "agronomic_certification": False,
        },
        "battery_model": battery,
        "scenario_results": results,
        "completion_scores": scores,
        "feasibility": feasibility,
        "bottlenecks": all_bottlenecks,
        "recommendations": recommendations(results),
        "safety": {
            "offline_only": True, "network_access_performed": False,
            "gpio_access_performed": False, "serial_access_performed": False,
            "hardware_output_performed": False, "motor_control_performed": False,
            "pto_control_performed": False, "charging_control_performed": False,
            "bms_communication_performed": False, "rover_communication_performed": False,
            "actual_assignment_performed": False, "actual_arm_performed": False,
            "automatic_decision_performed": False, "field_operation_approved": False,
            "unattended_operation_approved": False, "repository_modified": False,
            "physical_estop_independent": True,
        },
        "diagnostics": diagnostics,
        "canonical_plan_sha256": plan_hash,
        "canonical_simulation_state_sha256": simulation_hash,
        "exit_code": 0,
    }
    return SimulationReport(document, 0)


def render_json_report(report: SimulationReport) -> str:
    return json.dumps(report.document, ensure_ascii=True, indent=2, separators=(",", ": ")) + "\n"


def _percent(bp: int) -> str:
    return f"{bp // 100}.{(bp % 100) // 10}"


def _text_value(value: object) -> str:
    return str(value).lower() if type(value) is bool else str(value)


def render_text_report(report: SimulationReport) -> str:
    document = report.document
    baseline = document["scenario_results"][0]
    scores = document["completion_scores"]
    values = (
        ("report_version", document["report_version"]), ("phase", document["phase"]),
        ("plan_id", document["plan_id"]), ("result", document["result"]),
        ("field_id", document["field"]["field_id"]), ("field_area_m2", document["field"]["field_area_m2"]),
        ("lane_count", document["derived_geometry"]["lane_count"]),
        ("full_pass_distance_m", document["derived_geometry"]["full_pass_distance_mm"] // 1000),
        ("weed_total_target_distance_m", document["derived_geometry"]["weed_total_target_distance_mm"] // 1000),
        ("scenario_count", len(document["scenario_results"])),
        ("baseline_broadcast_completion_percent", _percent(baseline["broadcast"]["completion_basis_points"])),
        ("baseline_weed_priority_completion_percent", _percent(baseline["weed"]["priority_completion_basis_points"])),
        ("baseline_weed_full_pass_completion_percent", _percent(baseline["weed"]["full_pass_completion_basis_points"])),
        ("baseline_harvest_cut_completion_percent", _percent(baseline["harvest"]["cut_completion_basis_points"])),
        ("baseline_harvest_recovery_completion_percent", _percent(basis_points(baseline["harvest"]["total_cassettes_recovered"], max(1, baseline["harvest"]["cassettes_generated"])))),
        ("baseline_cassettes_generated", baseline["harvest"]["cassettes_generated"]),
        ("baseline_cassettes_recovered", baseline["harvest"]["total_cassettes_recovered"]),
        ("baseline_cassette_backlog", baseline["harvest"]["unrecovered_cassettes"]),
        ("baseline_battery_wait_minutes", baseline["battery"]["battery_wait_minutes"]),
        ("broadcast_completed_scenarios", scores["broadcast"]["completed_scenarios"]),
        ("weed_completed_scenarios", scores["weed_full_phase"]["completed_scenarios"]),
        ("harvest_cut_completed_scenarios", scores["harvest_cut"]["completed_scenarios"]),
        ("harvest_system_completed_scenarios", scores["harvest_system"]["completed_scenarios"]),
        ("overall_completed_scenarios", scores["overall"]["completed_scenarios"]),
        ("stress_scenario_completion_percent", _percent(scores["overall"]["basis_points"])),
        ("feasibility_classification", document["feasibility"]["classification"]),
        ("primary_bottleneck", document["bottlenecks"][0]),
        ("canonical_plan_sha256", document["canonical_plan_sha256"]),
        ("canonical_simulation_state_sha256", document["canonical_simulation_state_sha256"]),
        ("offline_only", document["safety"]["offline_only"]),
        ("hardware_output_performed", document["safety"]["hardware_output_performed"]),
        ("actual_assignment_performed", document["safety"]["actual_assignment_performed"]),
        ("field_operation_approved", document["safety"]["field_operation_approved"]),
        ("unattended_operation_approved", document["safety"]["unattended_operation_approved"]),
        ("diagnostic_count", len(document["diagnostics"])), ("exit_code", document["exit_code"]),
    )
    return "\n".join(f"{key}={_text_value(value)}" for key, value in values) + "\n"


def write_report(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _failure_report(plan_id: str, failure: SeasonFailure) -> SimulationReport:
    empty_hash = sha256_text(canonical_json({}))
    document = {
        "report_version": REPORT_VERSION, "phase": PHASE, "plan_id": plan_id,
        "result": "FAIL", "field": {}, "derived_geometry": {}, "assumptions": {},
        "battery_model": {}, "scenario_results": [], "completion_scores": {},
        "feasibility": {"classification": "NOT_EVALUATED"}, "bottlenecks": [],
        "recommendations": [], "safety": {
            "offline_only": True, "network_access_performed": False,
            "gpio_access_performed": False, "serial_access_performed": False,
            "hardware_output_performed": False, "motor_control_performed": False,
            "pto_control_performed": False, "charging_control_performed": False,
            "bms_communication_performed": False, "rover_communication_performed": False,
            "actual_assignment_performed": False, "actual_arm_performed": False,
            "automatic_decision_performed": False, "field_operation_approved": False,
            "unattended_operation_approved": False, "repository_modified": False,
            "physical_estop_independent": True,
        }, "diagnostics": [{
            "severity": "ERROR", "code": failure.code, "component": failure.component,
            "scenario_id": "", "message": failure.message,
        }], "canonical_plan_sha256": empty_hash,
        "canonical_simulation_state_sha256": empty_hash, "exit_code": failure.exit_code,
    }
    return SimulationReport(document, failure.exit_code)


def run_simulation(
    arguments: SimulatorArguments, *, simulator: Callable[[dict[str, object]], SimulationReport] = build_report,
    write_reports: bool = False,
) -> SimulationReport:
    validate_arguments(arguments)
    try:
        plan = validate_plan(load_strict_json(arguments.plan))
        report = simulator(plan)
    except SeasonFailure as failure:
        report = _failure_report("PLAN-ST008-INVALID", failure)
    except Exception:
        report = _failure_report("PLAN-ST008-INTERNAL", SeasonFailure(
            "SEASON_INTERNAL_ERROR", "internal", "Unexpected internal failure.", 7,
        ))
    if write_reports:
        try:
            write_report(arguments.json_report, render_json_report(report))
            write_report(arguments.text_report, render_text_report(report))
        except (OSError, KeyError):
            return _failure_report(str(report.document["plan_id"]), SeasonFailure(
                "SEASON_REPORT_WRITE_FAILED", "report", "Report output failed.", 7,
            ))
    return report


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_arguments(argv)
        report = run_simulation(arguments, write_reports=True)
        if report.exit_code == 0:
            print(render_text_report(report), end="")
        return report.exit_code
    except SeasonFailure as failure:
        print(f"ST-008 seasonal simulator rejected: {failure.message}", file=sys.stderr)
        return failure.exit_code
    except Exception:
        print("SEASON_INTERNAL_ERROR: ST-008 seasonal simulator failed unexpectedly.", file=sys.stderr)
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
