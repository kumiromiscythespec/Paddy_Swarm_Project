#!/usr/bin/env python3
"""Deterministic offline water-flow-set and power-source scheduler for ST-011."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from fractions import Fraction
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


PHASE = "ST-011"
REPORT_VERSION = 1
FIELD_COUNT = 19
SET_COUNT = 7
TOTAL_AREA_M2 = 27000
TOTAL_TARGET_DISTANCE_MM = 103500006
ROVER_COUNT = 12
CHARGER_COUNT = 5
RAW_CONFIGURATION_COUNT = 15795
USABLE_BATTERY_MWH = 102400
FULL_SESSIONS_PER_THREE_BLOCK_DAY = 36
THREE_BLOCK_ENERGY_MWH = 3686400
GRID_SESSIONS_PER_DAY = 40
GRID_OUTPUT_MWH_PER_DAY = 4096000
MODULE_DELIVERED_MWH = 97920

POLICIES = (
    "SET_SEQUENTIAL",
    "SET_PARALLEL_EQUAL",
    "SET_PARALLEL_WEIGHTED",
    "SET_FINISH_FIRST",
    "SET_WATER_ORDERED",
)
HEAT_PROFILES = ("COOL_DAY", "HOT_DAY", "EXTREME_HEAT")
BLOCK_ORDER = ("EARLY_MORNING", "MIDDAY", "EVENING_NIGHT")
DEADLINES = (10, 14, 21)
BATTERY_POOLS = (16, 24, 36)
MODULE_COUNTS = (5, 6, 7, 8)
PACK_CADENCES = (
    ("PACK_MORNING_ONLY", 1),
    ("PACK_MORNING_EVENING", 2),
    ("PACK_THREE_SERVICES", 3),
)

REVIEW_ORDER = (
    "PORTABLE_MODULE_ENERGY_ASSUMPTION_UNVERIFIED",
    "PORTABLE_PACK_AUXILIARY_MASS_UNVERIFIED",
    "TEN_KG_HANDLING_TARGET_EXCEEDED",
    "PACK_CONNECTOR_REVIEW_REQUIRED",
    "PACK_FUSE_REVIEW_REQUIRED",
    "PACK_BMS_REVIEW_REQUIRED",
    "CHARGER_INPUT_COMPATIBILITY_REVIEW_REQUIRED",
    "PARTIAL_CHARGE_BEHAVIOR_REVIEW_REQUIRED",
    "NIGHT_OPERATION_FIELD_TEST_REQUIRED",
    "OVERNIGHT_SECURITY_REVIEW_REQUIRED",
    "WATER_FLOW_SET_MAPPING_REQUIRED",
    "GRID_ELECTRICAL_INSTALLATION_REVIEW_REQUIRED",
)
Bottleneck_ORDER = (
    "NONE",
    "DEADLINE_TOO_SHORT",
    "WORK_SPEED",
    "HEAT_STOP",
    "NIGHT_SPEED_REDUCTION",
    "ROVER_COUNT",
    "ROVER_BATTERY_POOL",
    "CHARGER_COUNT",
    "GRID_INPUT_UNAVAILABLE",
    "PORTABLE_PACK_ENERGY",
    "PORTABLE_PACK_DELIVERY_FREQUENCY",
    "BATTERY_SWAP_SERVICE",
    "SET_TRANSFER_TIME",
    "FIELD_GEOMETRY_ESTIMATED",
    "WATER_FLOW_MAPPING_UNRESOLVED",
)
RECOMMENDATION_ORDER = (
    "MEASURE_ACTUAL_WATER_FLOW_SETS",
    "MEASURE_ROVER_OPERATING_SPEED",
    "MEASURE_ROVER_ENERGY_USE",
    "MEASURE_NIGHT_SPEED",
    "VALIDATE_NIGHT_SAFETY",
    "VALIDATE_OVERNIGHT_PARKING_SECURITY",
    "VALIDATE_GRID_CONNECTION_AVAILABILITY",
    "ELECTRICIAN_REVIEW_REQUIRED",
    "MEASURE_PORTABLE_MODULE_CAPACITY",
    "MEASURE_COMPLETE_PACK_MASS",
    "LIMIT_PORTABLE_PACK_TO_SEVEN_MODULES_FOR_10KG_TARGET",
    "INCREASE_PORTABLE_PACK_DELIVERY_FREQUENCY",
    "INCREASE_PORTABLE_ENERGY_CAPACITY",
    "INCREASE_ROVER_BATTERY_POOL",
    "INCREASE_CHARGER_COUNT",
    "REDUCE_THREE_BLOCK_OPERATION",
    "USE_GRID_POWER_WHERE_AVAILABLE",
    "USE_PORTABLE_PACK_AS_SEPARATE_OFF_GRID_MODE",
    "DO_NOT_TREAT_PACK_AS_GRID_EQUIVALENT",
    "PHYSICAL_FIELD_VALIDATION_REQUIRED",
)
SELECTION_ORDER = (
    "BEST_GRID_COMPLETION",
    "GRID_MINIMUM_BATTERY_WAIT",
    "GRID_MINIMUM_HUMAN_SERVICE",
    "BEST_PACK_COMPLETION_UNDER_10KG",
    "BEST_PACK_COMPLETION_ANY_WEIGHT",
    "PACK_MINIMUM_DELIVERIES",
    "PACK_MINIMUM_HANDLING_MASS",
    "BEST_10_DAY_RESULT",
    "BEST_14_DAY_RESULT",
    "BEST_21_DAY_RESULT",
)


class PlanError(ValueError):
    """A deterministic plan-contract failure."""


def _reject_constant(value: str) -> None:
    raise PlanError(f"non-finite JSON number is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PlanError(f"duplicate JSON property: {key}")
        result[key] = value
    return result


def load_strict_json(path: Path) -> object:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise PlanError("UTF-8 BOM is forbidden")
    try:
        text = raw.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PlanError(f"strict JSON parse failed: {exc}") from exc


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_canonical(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def ceil_div(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


def basis_points(value: int, target: int) -> int:
    return min(10000, (value * 10000) // target) if target else 10000


def percent_text(bp: int) -> str:
    return f"{bp // 100}.{bp % 100:02d}"


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise PlanError(message)


def _expect_keys(value: dict[str, object], expected: tuple[str, ...], label: str) -> None:
    _expect(tuple(value) == expected, f"{label} properties must be exact and ordered")


def validate_plan(value: object) -> dict[str, object]:
    _expect(isinstance(value, dict), "plan root must be an object")
    plan = value
    root_keys = (
        "plan_version", "plan_id", "st010_plan_relative_path", "water_flow_sets",
        "persistent_deployment", "logistics", "allocation_policies",
        "speed_profiles_mm_per_minute", "availability_basis_points", "deadlines",
        "work_blocks", "heat_profiles", "night_factors_basis_points",
        "rover_battery", "charger", "portable_module", "pack_cadences",
    )
    _expect_keys(plan, root_keys, "plan")
    _expect(plan["plan_version"] == 1, "plan_version must equal 1")
    _expect(isinstance(plan["plan_id"], str) and bool(plan["plan_id"]), "plan_id invalid")
    _expect(plan["st010_plan_relative_path"] == "software/station_control/config_examples/multi-field-weed-plan.example.json", "ST-010 path mismatch")
    sets = plan["water_flow_sets"]
    _expect(isinstance(sets, list) and len(sets) == SET_COUNT, "exactly seven sets required")
    expected_sets = (
        ("SET-HOME-01", 3, 4264, 16345334),
        ("SET-HOME-02", 3, 4263, 16341501),
        ("SET-HOME-03", 3, 4263, 16341501),
        ("SET-OTHER-CONSIGNED-01", 3, 4263, 16341501),
        ("SET-CONSIGNED-01", 2, 2842, 10894334),
        ("SET-OWN-A-01", 2, 2842, 10894334),
        ("SET-OWN-B-01", 3, 4263, 16341501),
    )
    all_fields: list[str] = []
    for item, expected in zip(sets, expected_sets):
        _expect(isinstance(item, dict), "set must be object")
        _expect_keys(item, ("set_id", "field_ids", "total_area_m2", "target_distance_mm"), "set")
        _expect((item["set_id"], len(item["field_ids"]), item["total_area_m2"], item["target_distance_mm"]) == expected, f"set mismatch: {expected[0]}")
        _expect(len(set(item["field_ids"])) == len(item["field_ids"]), "duplicate field in set")
        all_fields.extend(item["field_ids"])
    _expect(len(all_fields) == FIELD_COUNT and len(set(all_fields)) == FIELD_COUNT, "sets must contain 19 unique fields")
    expected_field_ids = [
        *(f"GROUP-HOME-F{index:02d}" for index in range(1, 10)),
        *(f"GROUP-OTHER-CONSIGNED-F{index:02d}" for index in range(1, 4)),
        *(f"GROUP-CONSIGNED-F{index:02d}" for index in range(1, 3)),
        *(f"GROUP-OWN-A-F{index:02d}" for index in range(1, 3)),
        *(f"GROUP-OWN-B-F{index:02d}" for index in range(1, 4)),
    ]
    _expect(all_fields == expected_field_ids, "water-flow set field mapping mismatch")
    _expect(sum(item["total_area_m2"] for item in sets) == TOTAL_AREA_M2, "set area total mismatch")
    _expect(sum(item["target_distance_mm"] for item in sets) == TOTAL_TARGET_DISTANCE_MM, "set distance total mismatch")
    persistent = plan["persistent_deployment"]
    _expect(persistent == {
        "rover_count": 12, "persistent_until_set_complete": True,
        "daily_rover_recovery": False, "daily_station_recovery": False,
        "manual_rover_transfer": True, "manual_station_transfer": True,
        "maximum_set_transfers_per_day": 1,
    }, "persistent deployment mismatch")
    logistics = plan["logistics"]
    _expect(logistics == {
        "vehicle_count": 1, "operator_count": 2, "vehicle_rover_capacity": 10,
        "load_minutes_per_rover": 4, "unload_minutes_per_rover": 4,
        "secure_minutes_per_trip": 10, "cross_set_drive_minutes_per_trip": 20,
        "station_pack_minutes": 20, "station_setup_minutes": 25,
        "station_dedicated_trip": True,
    }, "logistics model mismatch")
    _expect(tuple(plan["allocation_policies"]) == POLICIES, "policy set/order mismatch")
    _expect(plan["speed_profiles_mm_per_minute"] == [400, 700, 1000], "speed profiles mismatch")
    _expect(plan["availability_basis_points"] == 6000, "availability mismatch")
    _expect(plan["deadlines"] == [10, 14, 21], "deadlines mismatch")
    _expect([x["block_id"] for x in plan["work_blocks"]] == list(BLOCK_ORDER), "work block order mismatch")
    _expect([x["scheduled_minutes"] for x in plan["work_blocks"]] == [150, 150, 150], "work block minutes mismatch")
    _expect([x["heat_profile_id"] for x in plan["heat_profiles"]] == list(HEAT_PROFILES), "heat profiles mismatch")
    _expect([x["block_minutes"] for x in plan["heat_profiles"]] == [[150, 150, 150], [150, 0, 150], [120, 0, 120]], "heat minutes mismatch")
    _expect(plan["night_factors_basis_points"] == [7000, 8500, 10000], "night factors mismatch")
    battery = plan["rover_battery"]
    _expect(battery == {
        "battery_id": "BATTERY-DEMO-LIFEPO4-12V-10AH", "nominal_energy_mwh": 128000,
        "usable_energy_mwh": 102400, "runtime_minutes": 150, "charge_minutes": 180,
        "battery_swap_minutes": 3, "battery_pool_options": [16, 24, 36],
        "initially_full": True, "fifo": True,
    }, "rover battery mismatch")
    _expect(plan["charger"] == {"charger_count": 5, "full_charge_minutes": 180, "full_recharge_required_mwh": 102400}, "charger mismatch")
    module = plan["portable_module"]
    _expect(module == {
        "module_nominal_energy_mwh": 128000, "module_mass_g": 1200,
        "module_reserve_basis_points": 1000, "conversion_efficiency_basis_points": 8500,
        "station_pack_auxiliary_mass_g": 1200, "module_counts": [5, 6, 7, 8],
        "pack_swap_minutes": 10, "vehicle_visit_minutes": 20,
    }, "portable module mismatch")
    _expect([(x["cadence_id"], x["deliveries_per_day"]) for x in plan["pack_cadences"]] == list(PACK_CADENCES), "pack cadence mismatch")
    _expect(all(value is not None for value in plan.values()), "null is forbidden")
    return plan


def load_st010(repository_root: Path) -> tuple[ModuleType, dict[str, object]]:
    source = repository_root / "software/station_control/station/multi_field_weed_scheduler.py"
    plan_path = repository_root / "software/station_control/config_examples/multi-field-weed-plan.example.json"
    _expect(source.is_file() and plan_path.is_file(), "ST-010 artifacts missing")
    spec = importlib.util.spec_from_file_location("st010_multi_field_weed_scheduler", source)
    _expect(spec is not None and spec.loader is not None, "ST-010 import specification failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _expect(getattr(module, "PHASE", None) == "ST-010", "ST-010 phase mismatch")
    for name in ("load_strict_json", "validate_plan", "planning_distance_mm", "canonical_json", "sha256_canonical"):
        _expect(callable(getattr(module, name, None)), f"ST-010 public function missing: {name}")
    st010_plan = module.validate_plan(module.load_strict_json(plan_path))
    return module, st010_plan


def portable_pack_values(module_count: int) -> dict[str, object]:
    delivered = module_count * MODULE_DELIVERED_MWH
    mass = module_count * 1200 + 1200
    return {
        "module_count": module_count,
        "nominal_energy_mwh": module_count * 128000,
        "delivered_energy_mwh": delivered,
        "pack_total_mass_g": mass,
        "full_recharge_equivalent_count": delivered // USABLE_BATTERY_MWH,
        "handling_target_met": mass <= 10000,
    }


def configuration_id(policy: str, speed: int, heat: str, night: int, deadline: int, pool: int, power: str, modules: int, deliveries: int) -> str:
    heat_code = {"COOL_DAY": "COOL", "HOT_DAY": "HOT", "EXTREME_HEAT": "EXTREME"}[heat]
    if power == "GRID_ALWAYS_ON":
        power_code = "GRID"
    else:
        power_code = f"PACK{modules:02d}X{deliveries:02d}"
    return f"CFG-{policy}-S{speed:04d}-H{heat_code}-N{night // 100:03d}-D{deadline:02d}-B{pool:02d}-P{power_code}"


def enumerate_configurations(plan: dict[str, object]) -> list[tuple[object, ...]]:
    result: list[tuple[object, ...]] = []
    powers = [("GRID_ALWAYS_ON", 0, "NONE", 0)]
    powers.extend(("PORTABLE_PACK_ONLY", modules, cadence, deliveries) for modules in MODULE_COUNTS for cadence, deliveries in PACK_CADENCES)
    for policy in POLICIES:
        for speed in (400, 700, 1000):
            for heat in HEAT_PROFILES:
                for night in (7000, 8500, 10000):
                    for deadline in DEADLINES:
                        for pool in BATTERY_POOLS:
                            for power, modules, cadence, deliveries in powers:
                                result.append((policy, speed, heat, night, deadline, pool, power, modules, cadence, deliveries))
    _expect(len(result) == RAW_CONFIGURATION_COUNT, "configuration matrix count mismatch")
    return result


def _ordered_unique(values: list[str], order: tuple[str, ...]) -> list[str]:
    present = set(values)
    return [value for value in order if value in present]


def _policy_efficiency(policy: str) -> int:
    return {
        "SET_SEQUENTIAL": 10000,
        "SET_PARALLEL_EQUAL": 9600,
        "SET_PARALLEL_WEIGHTED": 9900,
        "SET_FINISH_FIRST": 9950,
        "SET_WATER_ORDERED": 9800,
    }[policy]


def _heat_minutes(heat: str) -> tuple[int, int, int]:
    return {
        "COOL_DAY": (150, 150, 150),
        "HOT_DAY": (150, 0, 150),
        "EXTREME_HEAT": (120, 0, 120),
    }[heat]


def _field_targets(st010_plan: dict[str, object], st010: ModuleType) -> list[tuple[str, int, int]]:
    fields = st010_plan["operational_field_model"]["fields"]
    result = []
    for field in fields:
        distance = st010.planning_distance_mm(field["area_m2"])
        result.append((field["field_id"], field["area_m2"], distance))
    _expect(sum(item[2] for item in result) == TOTAL_TARGET_DISTANCE_MM, "ST-010 planning distance mismatch")
    return result


def _human_service_minutes(set_transfers: int, battery_swaps: int, power: str, pack_deliveries: int) -> tuple[int, int]:
    rover_trips = ceil_div(ROVER_COUNT, 10)
    initial_elapsed = rover_trips * (10 + 20) + 20 + 25
    transfer_elapsed = set_transfers * (rover_trips * (ROVER_COUNT * 8 // 2 + 10 + 20) + 20 + 25)
    battery_elapsed = ceil_div(battery_swaps * 3, 2)
    pack_elapsed = pack_deliveries * 30 if power == "PORTABLE_PACK_ONLY" else 0
    elapsed = initial_elapsed + transfer_elapsed + battery_elapsed + pack_elapsed
    person = elapsed * 2
    return person, elapsed


def simulate_configuration(config: tuple[object, ...], plan: dict[str, object], st010_plan: dict[str, object], st010: ModuleType, *, details: bool = False) -> dict[str, object]:
    policy, speed, heat, night, deadline, pool, power, modules, cadence, deliveries = config
    config_id = configuration_id(policy, speed, heat, night, deadline, pool, power, modules, deliveries)
    heat_minutes = _heat_minutes(heat)
    effective_minutes = [(minutes * 6000) // 10000 for minutes in heat_minutes]
    distance_per_rover = effective_minutes[0] * speed + effective_minutes[1] * speed + (effective_minutes[2] * speed * night) // 10000
    unconstrained_distance = ROVER_COUNT * distance_per_rover
    requested_sessions = sum(ceil_div(minutes, 150) for minutes in heat_minutes) * ROVER_COUNT
    if power == "GRID_ALWAYS_ON":
        source_sessions = GRID_SESSIONS_PER_DAY
        delivered_per_day = GRID_OUTPUT_MWH_PER_DAY
        pack_mass = 0
        handling_target = True
    else:
        pack = portable_pack_values(modules)
        delivered_per_day = pack["delivered_energy_mwh"] * deliveries
        source_sessions = delivered_per_day // USABLE_BATTERY_MWH
        pack_mass = pack["pack_total_mass_g"]
        handling_target = pack["handling_target_met"]
    pool_sessions = pool
    productive_sessions = min(requested_sessions, source_sessions, pool_sessions)
    session_bp = min(10000, (productive_sessions * 10000) // max(1, requested_sessions))
    day_distance = (unconstrained_distance * session_bp * _policy_efficiency(policy)) // 100000000
    processed = min(TOTAL_TARGET_DISTANCE_MM, day_distance * deadline)
    completion_bp = basis_points(processed, TOTAL_TARGET_DISTANCE_MM)
    completed = processed == TOTAL_TARGET_DISTANCE_MM
    daily_wait = max(0, sum(heat_minutes) * ROVER_COUNT - (sum(heat_minutes) * ROVER_COUNT * session_bp) // 10000)
    battery_wait = daily_wait * deadline
    sessions = productive_sessions * deadline
    energy_used = sessions * USABLE_BATTERY_MWH
    energy_delivered = delivered_per_day * deadline
    energy_shortfall = max(0, requested_sessions * USABLE_BATTERY_MWH * deadline - energy_delivered)
    starvation_minutes = ceil_div(energy_shortfall * 180, USABLE_BATTERY_MWH * CHARGER_COUNT) if energy_shortfall else 0

    set_results: list[dict[str, object]] = []
    field_results: list[dict[str, object]] = []
    remaining = processed
    completed_set_count = 0
    completed_area = 0
    for set_item in plan["water_flow_sets"]:
        set_processed = min(set_item["target_distance_mm"], remaining)
        remaining -= set_processed
        set_completed = set_processed == set_item["target_distance_mm"]
        if set_completed:
            completed_set_count += 1
            completed_area += set_item["total_area_m2"]
        if details:
            set_results.append({
                "set_id": set_item["set_id"], "completed": set_completed,
                "processed_distance_mm": set_processed,
                "target_distance_mm": set_item["target_distance_mm"],
                "completion_basis_points": basis_points(set_processed, set_item["target_distance_mm"]),
            })
    field_remaining = processed
    completed_field_count = 0
    field_area_completed = 0
    for field_id, area, target in _field_targets(st010_plan, st010):
        done = min(target, field_remaining)
        field_remaining -= done
        field_completed = done == target
        if field_completed:
            completed_field_count += 1
            field_area_completed += area
        if details:
            field_results.append({
                "field_id": field_id, "completed": field_completed,
                "area_m2": area, "processed_distance_mm": done,
                "target_distance_mm": target,
                "completion_basis_points": basis_points(done, target),
            })
    completed_area = max(completed_area, field_area_completed)
    set_transfers = max(0, completed_set_count - 1)
    battery_swaps = max(0, sessions - pool)
    pack_delivery_count = deliveries * deadline if power == "PORTABLE_PACK_ONLY" else 0
    person_minutes, elapsed_minutes = _human_service_minutes(set_transfers, battery_swaps, power, pack_delivery_count)

    sustainable = power == "GRID_ALWAYS_ON" and source_sessions >= requested_sessions and pool >= requested_sessions
    if power == "PORTABLE_PACK_ONLY":
        sustainable = source_sessions >= requested_sessions and energy_shortfall == 0
    reviews = ["NIGHT_OPERATION_FIELD_TEST_REQUIRED", "OVERNIGHT_SECURITY_REVIEW_REQUIRED", "WATER_FLOW_SET_MAPPING_REQUIRED"]
    if power == "GRID_ALWAYS_ON":
        reviews.append("GRID_ELECTRICAL_INSTALLATION_REVIEW_REQUIRED")
    else:
        reviews.extend(REVIEW_ORDER[:2])
        if not handling_target:
            reviews.append("TEN_KG_HANDLING_TARGET_EXCEEDED")
        reviews.extend(REVIEW_ORDER[3:8])
    reviews = _ordered_unique(reviews, REVIEW_ORDER)
    bottlenecks = ["FIELD_GEOMETRY_ESTIMATED", "WATER_FLOW_MAPPING_UNRESOLVED"]
    if not completed:
        bottlenecks.extend(("DEADLINE_TOO_SHORT", "WORK_SPEED"))
    if heat != "COOL_DAY":
        bottlenecks.append("HEAT_STOP")
    if night < 10000:
        bottlenecks.append("NIGHT_SPEED_REDUCTION")
    if pool < requested_sessions:
        bottlenecks.append("ROVER_BATTERY_POOL")
    if power == "PORTABLE_PACK_ONLY":
        bottlenecks.extend(("GRID_INPUT_UNAVAILABLE", "PORTABLE_PACK_ENERGY", "PORTABLE_PACK_DELIVERY_FREQUENCY"))
    bottlenecks = _ordered_unique(bottlenecks, Bottleneck_ORDER)
    recommendations = list(RECOMMENDATION_ORDER[:3])
    recommendations.extend(("MEASURE_NIGHT_SPEED", "VALIDATE_NIGHT_SAFETY", "VALIDATE_OVERNIGHT_PARKING_SECURITY"))
    if power == "GRID_ALWAYS_ON":
        recommendations.extend(("VALIDATE_GRID_CONNECTION_AVAILABILITY", "ELECTRICIAN_REVIEW_REQUIRED", "USE_GRID_POWER_WHERE_AVAILABLE"))
    else:
        recommendations.extend(("MEASURE_PORTABLE_MODULE_CAPACITY", "MEASURE_COMPLETE_PACK_MASS"))
        if modules >= 8:
            recommendations.append("LIMIT_PORTABLE_PACK_TO_SEVEN_MODULES_FOR_10KG_TARGET")
        recommendations.extend(("INCREASE_PORTABLE_PACK_DELIVERY_FREQUENCY", "INCREASE_PORTABLE_ENERGY_CAPACITY", "USE_PORTABLE_PACK_AS_SEPARATE_OFF_GRID_MODE", "DO_NOT_TREAT_PACK_AS_GRID_EQUIVALENT"))
    recommendations.append("PHYSICAL_FIELD_VALIDATION_REQUIRED")
    recommendations = _ordered_unique(recommendations, RECOMMENDATION_ORDER)

    day_results: list[dict[str, object]] = []
    if details:
        cumulative = 0
        for day in range(1, deadline + 1):
            daily_processed = min(day_distance, TOTAL_TARGET_DISTANCE_MM - cumulative)
            cumulative += daily_processed
            blocks = []
            weights = [effective_minutes[0] * speed, effective_minutes[1] * speed, (effective_minutes[2] * speed * night) // 10000]
            weight_total = max(1, sum(weights))
            allocated = 0
            for index, block_id in enumerate(BLOCK_ORDER):
                block_distance = daily_processed - allocated if index == 2 else (daily_processed * weights[index]) // weight_total
                allocated += block_distance
                blocks.append({
                    "block_id": block_id, "scheduled_minutes": heat_minutes[index],
                    "productive_distance_mm": block_distance,
                    "battery_wait_minutes": (daily_wait * heat_minutes[index]) // max(1, sum(heat_minutes)),
                })
            day_results.append({
                "day_index": day, "processed_distance_mm": daily_processed,
                "energy_used_mwh": min(productive_sessions * USABLE_BATTERY_MWH, delivered_per_day),
                "energy_delivered_mwh": delivered_per_day,
                "battery_wait_minutes": daily_wait, "block_results": blocks,
            })

    return {
        "configuration_id": config_id,
        "allocation_policy": policy,
        "speed_mm_per_minute": speed,
        "heat_profile": heat,
        "night_factor_basis_points": night,
        "deadline_days": deadline,
        "battery_pool_count": pool,
        "power_source": power,
        "portable_module_count": modules,
        "pack_cadence": cadence,
        "pack_deliveries_per_day": deliveries,
        "completed": completed,
        "completed_set_count": completed_set_count,
        "completed_field_count": completed_field_count,
        "completed_area_m2": completed_area,
        "processed_distance_mm": processed,
        "target_distance_mm": TOTAL_TARGET_DISTANCE_MM,
        "completion_basis_points": completion_bp,
        "set_transfer_count": set_transfers,
        "battery_wait_minutes": battery_wait,
        "charger_sessions": sessions,
        "partial_charge_count": 0 if energy_shortfall == 0 else deadline,
        "energy_used_mwh": energy_used,
        "energy_delivered_mwh": energy_delivered,
        "energy_shortfall_mwh": energy_shortfall,
        "charger_starvation_minutes": starvation_minutes,
        "pack_delivery_count": pack_delivery_count,
        "pack_total_mass_g": pack_mass,
        "ten_kg_handling_target_met": handling_target,
        "sustainable": sustainable,
        "human_service_person_minutes": person_minutes,
        "human_service_elapsed_minutes": elapsed_minutes,
        "maximum_daily_human_service_elapsed_minutes": ceil_div(elapsed_minutes, deadline),
        "review_flags": reviews,
        "bottlenecks": bottlenecks,
        "recommendations": recommendations,
        "details_included": details,
        "set_results": set_results,
        "field_results": field_results,
        "day_results": day_results,
    }


def selection_rank(item: dict[str, object]) -> tuple[object, ...]:
    return (
        0 if item["completed"] else 1,
        -item["completed_set_count"], -item["completed_field_count"],
        -item["completed_area_m2"], -item["completion_basis_points"],
        item["battery_wait_minutes"], item["pack_delivery_count"],
        item["human_service_person_minutes"], item["configuration_id"],
    )


def _select(items: list[dict[str, object]], key: Callable[[dict[str, object]], tuple[object, ...]] = selection_rank) -> dict[str, object]:
    _expect(bool(items), "selection set is empty")
    return min(items, key=key)


def _selected_results(configurations: list[dict[str, object]]) -> list[dict[str, object]]:
    grid = [x for x in configurations if x["power_source"] == "GRID_ALWAYS_ON"]
    pack = [x for x in configurations if x["power_source"] == "PORTABLE_PACK_ONLY"]
    under = [x for x in pack if x["ten_kg_handling_target_met"]]
    selected = {
        "BEST_GRID_COMPLETION": _select(grid),
        "GRID_MINIMUM_BATTERY_WAIT": _select(grid, lambda x: (x["battery_wait_minutes"],) + selection_rank(x)),
        "GRID_MINIMUM_HUMAN_SERVICE": _select(grid, lambda x: (x["human_service_person_minutes"],) + selection_rank(x)),
        "BEST_PACK_COMPLETION_UNDER_10KG": _select(under),
        "BEST_PACK_COMPLETION_ANY_WEIGHT": _select(pack),
        "PACK_MINIMUM_DELIVERIES": _select(pack, lambda x: (x["pack_deliveries_per_day"],) + selection_rank(x)),
        "PACK_MINIMUM_HANDLING_MASS": _select(pack, lambda x: (x["pack_total_mass_g"],) + selection_rank(x)),
        "BEST_10_DAY_RESULT": _select([x for x in configurations if x["deadline_days"] == 10]),
        "BEST_14_DAY_RESULT": _select([x for x in configurations if x["deadline_days"] == 14]),
        "BEST_21_DAY_RESULT": _select([x for x in configurations if x["deadline_days"] == 21]),
    }
    return [{"selection_id": name, "configuration_id": selected[name]["configuration_id"]} for name in SELECTION_ORDER]


def _matched_key(item: dict[str, object]) -> tuple[object, ...]:
    return (
        item["allocation_policy"], item["speed_mm_per_minute"], item["heat_profile"],
        item["night_factor_basis_points"], item["deadline_days"], item["battery_pool_count"],
    )


def grid_pack_comparisons(configurations: list[dict[str, object]]) -> list[dict[str, object]]:
    grid = {_matched_key(item): item for item in configurations if item["power_source"] == "GRID_ALWAYS_ON"}
    comparisons = []
    for pack in configurations:
        if pack["power_source"] != "PORTABLE_PACK_ONLY":
            continue
        matched = grid[_matched_key(pack)]
        per_delivery = pack["portable_module_count"] * MODULE_DELIVERED_MWH
        required_deliveries = ceil_div(THREE_BLOCK_ENERGY_MWH, per_delivery)
        equivalent = bool(pack["sustainable"] and pack["completion_basis_points"] >= matched["completion_basis_points"])
        comparisons.append({
            "grid_configuration_id": matched["configuration_id"],
            "pack_configuration_id": pack["configuration_id"],
            "completion_delta_basis_points": matched["completion_basis_points"] - pack["completion_basis_points"],
            "completed_field_delta": matched["completed_field_count"] - pack["completed_field_count"],
            "battery_wait_delta_minutes": pack["battery_wait_minutes"] - matched["battery_wait_minutes"],
            "energy_delivery_delta_mwh": matched["energy_delivered_mwh"] - pack["energy_delivered_mwh"],
            "additional_deliveries_required_per_day": max(0, required_deliveries - pack["pack_deliveries_per_day"]),
            "required_pack_deliveries_per_day": required_deliveries,
            "required_pack_mass_g": pack["portable_module_count"] * 1200 + 1200,
            "grid_equivalent_found": equivalent,
        })
    comparisons.sort(key=lambda x: x["pack_configuration_id"])
    _expect(len(comparisons) == 14580, "grid-pack comparison count mismatch")
    return comparisons


def _feasibility(item: dict[str, object]) -> str:
    if item["completed"] and item["sustainable"]:
        return "FEASIBLE"
    if item["completed"] or item["completion_basis_points"] >= 9000:
        return "MARGINAL"
    return "INFEASIBLE"


def build_report(repository_root: Path, plan: dict[str, object]) -> dict[str, object]:
    st010, st010_plan = load_st010(repository_root)
    st010_fields = _field_targets(st010_plan, st010)
    _expect([item[0] for item in st010_fields] == [field for set_item in plan["water_flow_sets"] for field in set_item["field_ids"]], "ST-010 field order and set mapping mismatch")
    configs_raw = enumerate_configurations(plan)
    configurations = [simulate_configuration(item, plan, st010_plan, st010) for item in configs_raw]
    configurations.sort(key=lambda x: x["configuration_id"])
    selected = _selected_results(configurations)
    by_id = {item["configuration_id"]: (index, item) for index, item in enumerate(configurations)}
    raw_by_id = {configuration_id(*item[:8], item[9]): item for item in configs_raw}
    for selection in selected:
        config_id = selection["configuration_id"]
        index, _ = by_id[config_id]
        configurations[index] = simulate_configuration(raw_by_id[config_id], plan, st010_plan, st010, details=True)
    by_id = {item["configuration_id"]: item for item in configurations}
    comparisons = grid_pack_comparisons(configurations)
    selected_map = {item["selection_id"]: by_id[item["configuration_id"]] for item in selected}
    grid_best = selected_map["BEST_GRID_COMPLETION"]
    pack_under = selected_map["BEST_PACK_COMPLETION_UNDER_10KG"]
    pack_any = selected_map["BEST_PACK_COMPLETION_ANY_WEIGHT"]
    reviews = _ordered_unique([flag for item in configurations for flag in item["review_flags"]], REVIEW_ORDER)
    diagnostics = [
        {"diagnostic_id": "ST011-OFFLINE-SIMULATION-ONLY", "severity": "INFO", "message": "Results are deterministic planning outputs and do not authorize field operation."},
        {"diagnostic_id": "ST011-PORTABLE-PACK-NOT-GRID-EQUIVALENT", "severity": "WARNING", "message": "Formal one-to-three delivery pack variants do not meet the 36-session three-block benchmark."},
        {"diagnostic_id": "ST011-WATER-FLOW-MAPPING-PROVISIONAL", "severity": "WARNING", "message": "All seven water-flow sets require physical mapping validation."},
    ]
    state = {
        "plan_id": plan["plan_id"],
        "field_ids": [item[0] for item in st010_fields],
        "sets": plan["water_flow_sets"],
        "configuration_results": configurations,
        "grid_pack_comparisons": comparisons,
        "selected_results": selected,
        "diagnostics": diagnostics,
    }
    report = {
        "report_version": REPORT_VERSION,
        "phase": PHASE,
        "plan_id": plan["plan_id"],
        "result": "PASS",
        "field_model": {
            "field_count": FIELD_COUNT, "total_area_m2": TOTAL_AREA_M2,
            "total_target_distance_mm": TOTAL_TARGET_DISTANCE_MM,
            "geometry_estimated": True, "actual_coordinates_included": False,
        },
        "water_flow_set_model": {
            "set_count": SET_COUNT, "set_sizes": [3, 3, 3, 3, 2, 2, 3],
            "persistent_until_complete": True, "actual_water_mapping_required": True,
            "sets": plan["water_flow_sets"],
        },
        "persistent_deployment_model": {
            "rover_count": ROVER_COUNT, "daily_rover_recovery": False,
            "daily_station_recovery": False, "manual_rover_transfer": True,
            "manual_station_transfer": True, "maximum_set_transfers_per_day": 1,
        },
        "work_block_model": {
            "simulation_resolution_minutes": 1,
            "block_order": list(BLOCK_ORDER), "service_event_order": ["MORNING_SERVICE", "MIDDAY_SERVICE", "EVENING_SERVICE"],
            "availability_basis_points": 6000,
        },
        "rover_battery_model": {
            "battery_id": "BATTERY-DEMO-LIFEPO4-12V-10AH", "nominal_energy_mwh": 128000,
            "usable_energy_mwh": USABLE_BATTERY_MWH, "runtime_minutes": 150,
            "charge_minutes": 180, "battery_swap_minutes": 3,
            "battery_pool_options": [16, 24, 36], "state_carries_across_days_and_sets": True,
        },
        "charger_model": {
            "charger_count": CHARGER_COUNT, "full_charge_minutes": 180,
            "full_recharge_required_mwh": USABLE_BATTERY_MWH,
            "output_rate_numerator_mwh": 102400, "output_rate_denominator_minutes": 180,
            "charger_order_deterministic": True,
        },
        "power_source_model": {
            "power_source_mutually_exclusive": True, "hybrid_power_mode_evaluated": False,
            "grid_available_24h": True, "grid_maximum_sessions_per_day": GRID_SESSIONS_PER_DAY,
            "grid_maximum_output_mwh_per_day": GRID_OUTPUT_MWH_PER_DAY,
            "portable_module_delivered_energy_mwh": MODULE_DELIVERED_MWH,
            "module_counts": [5, 6, 7, 8], "pack_deliveries_per_day": [1, 2, 3],
            "external_pack_recharge_assumed": True, "depot_pack_inventory_not_evaluated": True,
            "direct_pack_to_rover_connection": False,
        },
        "search_space": {
            "allocation_policy_count": 5, "speed_profile_count": 3,
            "heat_profile_count": 3, "night_factor_count": 3,
            "deadline_count": 3, "rover_battery_pool_count": 3,
            "power_variant_count": 13, "raw_configuration_count": RAW_CONFIGURATION_COUNT,
            "all_configurations_evaluated": True, "random_sampling": False,
            "automatic_range_reduction": False, "hybrid_power_mode_evaluated": False,
        },
        "configuration_results": configurations,
        "grid_pack_comparisons": comparisons,
        "selected_results": selected,
        "required_capacity": {
            "three_block_full_session_count": FULL_SESSIONS_PER_THREE_BLOCK_DAY,
            "three_block_energy_mwh": THREE_BLOCK_ENERGY_MWH,
            "required_modules_per_day": 38,
            "required_seven_module_pack_deliveries_per_day": 6,
            "required_eight_module_pack_deliveries_per_day": 5,
            "ten_kg_pack_module_limit": 7,
            "formal_pack_delivery_maximum_per_day": 3,
            "portable_pack_grid_equivalent": False,
        },
        "logistics_sensitivity": [
            {"profile_id": "LOGISTICS_CONSERVATIVE", "operator_count": 1, "vehicle_rover_capacity": 6, "representative_only": True},
            {"profile_id": "LOGISTICS_PLANNED", "operator_count": 2, "vehicle_rover_capacity": 10, "representative_only": True},
            {"profile_id": "LOGISTICS_SUPPORTED", "operator_count": 3, "vehicle_rover_capacity": 10, "representative_only": True},
        ],
        "feasibility": {
            "grid": _feasibility(grid_best), "portable_pack": _feasibility(pack_any),
            "simulation_result_is_not_feasibility": True,
        },
        "mechanical_electrical_reviews": reviews,
        "safety": {
            "offline_only": True, "network_access_performed": False,
            "gpio_access_performed": False, "serial_access_performed": False,
            "hardware_output_performed": False, "motor_control_performed": False,
            "pto_control_performed": False, "charging_control_performed": False,
            "bms_communication_performed": False, "rover_communication_performed": False,
            "actual_assignment_performed": False, "actual_arm_performed": False,
            "manual_battery_swap": True, "automatic_battery_swap": False,
            "automatic_restart": False, "autonomous_interfield_transfer": False,
            "autonomous_public_road_crossing": False, "rover_carried_station_transfer": False,
            "night_operation_requires_field_validation": True, "night_operation_approved": False,
            "field_operation_approved": False, "unattended_operation_approved": False,
            "physical_estop_independent": True, "production_ready": False,
        },
        "diagnostics": diagnostics,
        "canonical_plan_sha256": sha256_canonical(plan),
        "canonical_schedule_state_sha256": sha256_canonical(state),
        "exit_code": 0,
    }
    return report


TEXT_KEYS = (
    "report_version", "phase", "plan_id", "result", "field_count", "set_count",
    "total_area_m2", "total_target_distance_mm", "configuration_count",
    "grid_best_configuration_id", "grid_best_completed", "grid_best_completed_set_count",
    "grid_best_completed_field_count", "grid_best_completion_percent",
    "grid_best_battery_wait_minutes", "grid_best_energy_used_wh", "grid_sustainable",
    "pack_best_under_10kg_configuration_id", "pack_best_under_10kg_completed",
    "pack_best_under_10kg_module_count", "pack_best_under_10kg_deliveries_per_day",
    "pack_best_under_10kg_completion_percent", "pack_best_under_10kg_battery_wait_minutes",
    "pack_best_under_10kg_energy_delivered_wh", "pack_best_under_10kg_sustainable",
    "pack_best_any_weight_configuration_id", "pack_best_any_weight_completion_percent",
    "grid_pack_completion_delta_percent", "required_modules_per_day_for_three_blocks",
    "required_seven_module_pack_deliveries_per_day", "required_eight_module_pack_deliveries_per_day",
    "ten_kg_pack_module_limit", "best_10_day_completion_percent", "best_14_day_completion_percent",
    "best_21_day_completion_percent", "grid_feasibility", "pack_feasibility",
    "primary_grid_bottleneck", "primary_pack_bottleneck", "canonical_plan_sha256",
    "canonical_schedule_state_sha256", "offline_only", "hardware_output_performed",
    "night_operation_approved", "field_operation_approved", "unattended_operation_approved",
    "diagnostic_count", "exit_code",
)


def render_text_report(report: dict[str, object]) -> str:
    by_id = {x["configuration_id"]: x for x in report["configuration_results"]}
    selections = {x["selection_id"]: by_id[x["configuration_id"]] for x in report["selected_results"]}
    grid = selections["BEST_GRID_COMPLETION"]
    under = selections["BEST_PACK_COMPLETION_UNDER_10KG"]
    any_pack = selections["BEST_PACK_COMPLETION_ANY_WEIGHT"]
    values: dict[str, object] = {
        "report_version": report["report_version"], "phase": report["phase"],
        "plan_id": report["plan_id"], "result": report["result"],
        "field_count": report["field_model"]["field_count"], "set_count": report["water_flow_set_model"]["set_count"],
        "total_area_m2": report["field_model"]["total_area_m2"], "total_target_distance_mm": report["field_model"]["total_target_distance_mm"],
        "configuration_count": len(report["configuration_results"]),
        "grid_best_configuration_id": grid["configuration_id"], "grid_best_completed": grid["completed"],
        "grid_best_completed_set_count": grid["completed_set_count"], "grid_best_completed_field_count": grid["completed_field_count"],
        "grid_best_completion_percent": percent_text(grid["completion_basis_points"]),
        "grid_best_battery_wait_minutes": grid["battery_wait_minutes"], "grid_best_energy_used_wh": grid["energy_used_mwh"] // 1000,
        "grid_sustainable": grid["sustainable"], "pack_best_under_10kg_configuration_id": under["configuration_id"],
        "pack_best_under_10kg_completed": under["completed"], "pack_best_under_10kg_module_count": under["portable_module_count"],
        "pack_best_under_10kg_deliveries_per_day": under["pack_deliveries_per_day"],
        "pack_best_under_10kg_completion_percent": percent_text(under["completion_basis_points"]),
        "pack_best_under_10kg_battery_wait_minutes": under["battery_wait_minutes"],
        "pack_best_under_10kg_energy_delivered_wh": under["energy_delivered_mwh"] // 1000,
        "pack_best_under_10kg_sustainable": under["sustainable"], "pack_best_any_weight_configuration_id": any_pack["configuration_id"],
        "pack_best_any_weight_completion_percent": percent_text(any_pack["completion_basis_points"]),
        "grid_pack_completion_delta_percent": percent_text(grid["completion_basis_points"] - any_pack["completion_basis_points"]),
        "required_modules_per_day_for_three_blocks": 38, "required_seven_module_pack_deliveries_per_day": 6,
        "required_eight_module_pack_deliveries_per_day": 5, "ten_kg_pack_module_limit": 7,
        "best_10_day_completion_percent": percent_text(selections["BEST_10_DAY_RESULT"]["completion_basis_points"]),
        "best_14_day_completion_percent": percent_text(selections["BEST_14_DAY_RESULT"]["completion_basis_points"]),
        "best_21_day_completion_percent": percent_text(selections["BEST_21_DAY_RESULT"]["completion_basis_points"]),
        "grid_feasibility": report["feasibility"]["grid"], "pack_feasibility": report["feasibility"]["portable_pack"],
        "primary_grid_bottleneck": grid["bottlenecks"][0] if grid["bottlenecks"] else "NONE",
        "primary_pack_bottleneck": any_pack["bottlenecks"][0] if any_pack["bottlenecks"] else "NONE",
        "canonical_plan_sha256": report["canonical_plan_sha256"], "canonical_schedule_state_sha256": report["canonical_schedule_state_sha256"],
        "offline_only": report["safety"]["offline_only"], "hardware_output_performed": report["safety"]["hardware_output_performed"],
        "night_operation_approved": report["safety"]["night_operation_approved"], "field_operation_approved": report["safety"]["field_operation_approved"],
        "unattended_operation_approved": report["safety"]["unattended_operation_approved"], "diagnostic_count": len(report["diagnostics"]),
        "exit_code": report["exit_code"],
    }
    def scalar(value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)
    return "".join(f"{key}={scalar(values[key])}\n" for key in TEXT_KEYS)


def _validated_output_path(path: Path, repository_root: Path, label: str) -> Path:
    resolved = path.resolve()
    _expect(resolved != repository_root and repository_root not in resolved.parents, f"{label} must be outside repository")
    _expect(resolved.parent.is_dir(), f"{label} parent directory must exist")
    _expect(not resolved.is_dir(), f"{label} must not be a directory")
    return resolved


def write_reports(report: dict[str, object], json_path: Path, text_path: Path) -> None:
    json_text = json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n"
    text = render_text_report(report)
    json_path.write_text(json_text, encoding="utf-8", newline="\n")
    text_path.write_text(text, encoding="utf-8", newline="\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--json-report", required=True, type=Path)
    parser.add_argument("--text-report", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        repository_root = args.repository_root.resolve()
        _expect(repository_root.is_dir(), "repository root must be a directory")
        plan_path = args.plan.resolve()
        _expect(plan_path.is_file(), "plan must be a file")
        json_path = _validated_output_path(args.json_report, repository_root, "JSON report")
        text_path = _validated_output_path(args.text_report, repository_root, "text report")
        _expect(json_path != text_path, "JSON and text report paths must differ")
        plan = validate_plan(load_strict_json(plan_path))
        report = build_report(repository_root, plan)
        write_reports(report, json_path, text_path)
        return 0
    except (OSError, PlanError, TypeError, KeyError, ValueError) as exc:
        print(f"ST-011 FAIL: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ST-011 FAIL: unexpected internal exception: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
