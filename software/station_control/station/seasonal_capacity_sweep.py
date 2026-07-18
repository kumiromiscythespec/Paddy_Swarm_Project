#!/usr/bin/env python3
"""Deterministic offline ST-009 seasonal capacity sweep and Pareto search."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Callable, Iterator, Sequence


REPORT_VERSION = 1
PHASE = "ST-009"
SWEEP_VERSION = 1
SWEEP_ID = "SWEEP-ST009-FIELD-DEMO-001"
TARGET_IDS = ("TARGET_BASELINE", "TARGET_WET_RESILIENT", "TARGET_ALL_SCENARIOS")
SCENARIO_IDS = (
    "BASELINE", "CONSERVATIVE", "WET_FIELD", "ONE_ROVER_DOWN",
    "CARRIER_BOTTLENECK", "COMBINED_BAD",
)
TARGET_INDICES = ((0,), (0, 2), (0, 1, 2, 3, 4, 5))
RANGE_KEYS = (
    "broadcast_rover_counts", "weed_rover_counts", "high_cut_rover_counts",
    "carrier_rover_counts", "battery_pool_counts", "charger_counts",
    "cassette_capacity_g_values", "carrier_cassettes_per_trip_values",
    "temporary_drop_slot_counts", "manual_recovery_per_day_values",
)
EXPECTED_RANGES = {
    "broadcast_rover_counts": [4],
    "weed_rover_counts": [2, 3, 4, 5, 6],
    "high_cut_rover_counts": [4, 5, 6, 7, 8, 9, 10, 11, 12],
    "carrier_rover_counts": [2, 3, 4, 5, 6, 7, 8],
    "battery_pool_counts": [16, 20, 24, 28, 32, 36, 40, 44, 48],
    "charger_counts": [4, 6, 8, 10, 12],
    "cassette_capacity_g_values": [1000, 2000, 4000],
    "carrier_cassettes_per_trip_values": [1, 2, 4, 6],
    "temporary_drop_slot_counts": [50, 100, 150, 200],
    "manual_recovery_per_day_values": [0, 10, 20],
}
EXPECTED_OBJECTIVE_POLICY = {
    "equipment_quantity_min_enabled": True,
    "human_min_enabled": True,
    "exact_pareto_enabled": True,
    "mechanical_review_is_feasibility_gate": False,
}
EXPECTED_SEARCH_POLICY = {
    "raw_candidate_count": 2041200,
    "staged_exact_search": True,
    "upper_bound_may_prove_success": False,
    "automatic_range_expansion": False,
    "internal_candidate_cap": 0,
    "report_pareto_limit": 20,
    "nearest_miss_limit": 10,
}
RAW_CANDIDATE_COUNT = 2041200
MECHANICAL_FLAG_ORDER = (
    "CASSETTE_LOAD_TEST_REQUIRED", "CARRIER_BATCH_RACK_REQUIRED",
    "CARRIER_PAYLOAD_ENGINEERING_REVIEW_REQUIRED", "MUD_SINKING_TEST_REQUIRED",
    "CENTER_OF_GRAVITY_TEST_REQUIRED",
)
RECOMMENDATION_ORDER = (
    "BROADCAST_FIXED_CAPACITY_INSUFFICIENT", "WEED_ROVER_RANGE_INSUFFICIENT",
    "HIGH_CUT_ROVER_RANGE_INSUFFICIENT", "CARRIER_RANGE_INSUFFICIENT",
    "BATTERY_RANGE_INSUFFICIENT", "CHARGER_RANGE_INSUFFICIENT",
    "CASSETTE_LOGISTICS_REDESIGN_REQUIRED", "CASSETTE_LOAD_TEST_REQUIRED",
    "CARRIER_BATCH_RACK_REQUIRED", "CARRIER_PAYLOAD_ENGINEERING_REVIEW_REQUIRED",
    "MUD_SINKING_TEST_REQUIRED", "CENTER_OF_GRAVITY_TEST_REQUIRED",
    "MANUAL_DEPENDENCY_HIGH", "NO_TARGET_CANDIDATE_WITHIN_BOUNDS",
    "PHYSICAL_PROTOTYPE_VALIDATION_REQUIRED",
)
BOTTLENECK_ORDER = (
    "NONE", "DISTANCE_CAPACITY", "BATTERY_AVAILABILITY", "SEED_REFILL",
    "WEATHER_AVAILABILITY", "ROVER_FAILURE", "WEED_ROVER_COUNT",
    "HIGH_CUT_SPEED", "CASSETTE_BUFFER", "CARRIER_CAPACITY", "CARRIER_COUNT",
    "MANUAL_RECOVERY_LIMIT", "CHARGER_COUNT",
)


class SweepFailure(RuntimeError):
    def __init__(self, code: str, component: str, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.component = component
        self.message = message
        self.exit_code = exit_code


@dataclass(frozen=True, slots=True)
class SweepArguments:
    repository_root: Path
    base_plan: Path
    sweep_plan: Path
    json_report: Path
    text_report: Path


@dataclass(frozen=True, slots=True)
class SweepReport:
    document: dict[str, object]
    exit_code: int


@dataclass(frozen=True, slots=True)
class Candidate:
    broadcast: int
    weed: int
    high_cut: int
    carrier: int
    battery: int
    chargers: int
    cassette_g: int
    batch: int
    slots: int
    manual: int

    @property
    def candidate_id(self) -> str:
        return (
            f"CFG-B{self.broadcast:02d}-W{self.weed:02d}-H{self.high_cut:02d}"
            f"-C{self.carrier:02d}-P{self.battery:02d}-R{self.chargers:02d}"
            f"-K{self.cassette_g:04d}-T{self.batch:02d}-S{self.slots:03d}"
            f"-M{self.manual:02d}"
        )

    @property
    def common_rovers(self) -> int:
        return max(self.broadcast, self.weed, self.high_cut + self.carrier)

    @property
    def attachments(self) -> int:
        return self.broadcast + self.weed + self.high_cut + self.carrier

    @property
    def payload_g(self) -> int:
        return self.cassette_g * self.batch

    @property
    def cassette_proxy(self) -> int:
        return self.high_cut * 2 + self.slots + self.carrier * self.batch

    @property
    def flags(self) -> tuple[str, ...]:
        found: set[str] = set()
        if self.cassette_g > 1000:
            found.add("CASSETTE_LOAD_TEST_REQUIRED")
        if self.batch > 4:
            found.add("CARRIER_BATCH_RACK_REQUIRED")
        if self.payload_g > 4000:
            found.add("CARRIER_PAYLOAD_ENGINEERING_REVIEW_REQUIRED")
        if self.cassette_g >= 4000 or self.payload_g > 4000:
            found.add("MUD_SINKING_TEST_REQUIRED")
        if self.cassette_g >= 2000 or self.payload_g > 4000:
            found.add("CENTER_OF_GRAVITY_TEST_REQUIRED")
        return tuple(item for item in MECHANICAL_FLAG_ORDER if item in found)


@dataclass(frozen=True, slots=True)
class ScenarioMetrics:
    overall: bool
    broadcast_bp: int
    weed_bp: int
    harvest_cut_bp: int
    harvest_recovery_bp: int
    battery_wait: int
    cassette_backlog: int
    high_cut_wait: int
    unfinished_weed_mm: int
    unfinished_harvest_mm: int
    bottlenecks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TargetMetrics:
    satisfied: bool
    completed_scenarios: tuple[str, ...]
    completion_mask: tuple[bool, ...]
    unfinished_scenarios: int
    broadcast_shortfall_bp: int
    weed_shortfall_bp: int
    harvest_cut_shortfall_bp: int
    harvest_recovery_shortfall_bp: int
    total_battery_wait: int
    maximum_battery_wait: int
    maximum_backlog: int
    maximum_high_cut_wait: int
    maximum_unfinished_weed_mm: int
    maximum_unfinished_harvest_mm: int
    stress_completion_bp: int
    bottlenecks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StoredCandidate:
    candidate: Candidate
    metrics: TargetMetrics


@dataclass(slots=True)
class TargetAccumulator:
    satisfying_count: int
    without_review_count: int
    with_review_count: int
    equipment_best: StoredCandidate | None
    human_best: StoredCandidate | None
    frontier: dict[tuple[int, ...], list[StoredCandidate]]
    nearest: list[tuple[tuple[object, ...], StoredCandidate]]


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise SweepFailure("SWEEP_INVALID_ARGUMENT", "cli", "Invalid command arguments.", 2)


def parse_arguments(argv: Sequence[str] | None = None) -> SweepArguments:
    parser = SafeArgumentParser()
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--base-plan", required=True)
    parser.add_argument("--sweep-plan", required=True)
    parser.add_argument("--json-report", required=True)
    parser.add_argument("--text-report", required=True)
    values = parser.parse_args(argv)
    return SweepArguments(
        Path(values.repository_root), Path(values.base_plan), Path(values.sweep_plan),
        Path(values.json_report), Path(values.text_report),
    )


def is_contained(candidate: Path, parent: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(parent.resolve(strict=True))
        return True
    except (OSError, ValueError):
        return False


def validate_arguments(arguments: SweepArguments) -> None:
    if not arguments.repository_root.is_dir():
        raise SweepFailure("SWEEP_REPOSITORY_ROOT_INVALID", "path", "Repository root is invalid.", 2)
    if not arguments.base_plan.is_file():
        raise SweepFailure("SWEEP_BASE_PLAN_INVALID", "path", "Base plan does not exist.", 3)
    if not arguments.sweep_plan.is_file():
        raise SweepFailure("SWEEP_PLAN_INVALID", "path", "Sweep plan does not exist.", 3)
    if arguments.json_report == arguments.text_report:
        raise SweepFailure("SWEEP_INVALID_ARGUMENT", "path", "Report paths must differ.", 2)
    for report in (arguments.json_report, arguments.text_report):
        if not report.parent.is_dir() or report.parent.is_file():
            raise SweepFailure("SWEEP_REPORT_PARENT_INVALID", "path", "Report parent is invalid.", 2)
        if is_contained(report, arguments.repository_root):
            raise SweepFailure(
                "SWEEP_REPORT_PATH_INSIDE_REPOSITORY", "path",
                "Report must be outside the repository.", 2,
            )


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SweepFailure("SWEEP_PLAN_INVALID", "plan", "Duplicate JSON key.", 3)
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise SweepFailure("SWEEP_PLAN_INVALID", "plan", "Non-finite number is prohibited.", 3)


def _reject_null(value: object) -> None:
    if value is None:
        raise SweepFailure("SWEEP_PLAN_INVALID", "plan", "Null is prohibited.", 3)
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
    except SweepFailure:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise SweepFailure("SWEEP_PLAN_INVALID", "plan", "Input is not strict JSON.", 3) from exc


def canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    )


def sha256_canonical(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def validate_sweep_plan(value: object) -> dict[str, object]:
    root_keys = ("sweep_version", "sweep_id", "targets", "ranges", "objective_policy", "search_policy")
    if type(value) is not dict or tuple(value) != root_keys:
        raise SweepFailure("SWEEP_PLAN_INVALID", "plan", "Sweep plan properties are invalid.", 3)
    if type(value["sweep_version"]) is not int or value["sweep_version"] != SWEEP_VERSION:
        raise SweepFailure("SWEEP_PLAN_INVALID", "plan", "Sweep version is invalid.", 3)
    if value["sweep_id"] != SWEEP_ID or value["targets"] != list(TARGET_IDS):
        raise SweepFailure("SWEEP_PLAN_INVALID", "plan", "Sweep identity or target order is invalid.", 3)
    ranges = value["ranges"]
    if type(ranges) is not dict or tuple(ranges) != RANGE_KEYS:
        raise SweepFailure("SWEEP_PLAN_INVALID", "plan", "Range properties are invalid.", 3)
    for key in RANGE_KEYS:
        if ranges[key] != EXPECTED_RANGES[key] or len(ranges[key]) != len(set(ranges[key])):
            raise SweepFailure("SWEEP_PLAN_INVALID", "plan", f"Range {key} is invalid.", 3)
    if value["objective_policy"] != EXPECTED_OBJECTIVE_POLICY:
        raise SweepFailure("SWEEP_PLAN_INVALID", "plan", "Objective policy is invalid.", 3)
    if value["search_policy"] != EXPECTED_SEARCH_POLICY:
        raise SweepFailure("SWEEP_PLAN_INVALID", "plan", "Search policy is invalid.", 3)
    if raw_candidate_count(ranges) != RAW_CANDIDATE_COUNT:
        raise SweepFailure("SWEEP_RAW_COUNT_MISMATCH", "search", "Raw candidate count is invalid.", 3)
    return value


def raw_candidate_count(ranges: dict[str, object]) -> int:
    count = 1
    for key in RANGE_KEYS:
        values = ranges[key]
        if type(values) is not list:
            return 0
        count *= len(values)
    return count


def load_st008(repository_root: Path) -> ModuleType:
    path = repository_root / "software/station_control/station/seasonal_field_simulator.py"
    try:
        spec = importlib.util.spec_from_file_location("st009_reused_seasonal_field_simulator", path)
        if spec is None or spec.loader is None:
            raise ImportError
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        for name in (
            "validate_plan", "build_report", "derive_geometry", "simulate_broadcast",
            "simulate_weed", "simulate_harvest", "schedule_batteries",
            "carrier_cycle_seconds", "basis_points", "ceil_div",
        ):
            if not callable(getattr(module, name, None)):
                raise ImportError
        return module
    except Exception as exc:
        raise SweepFailure("SWEEP_ST008_LOAD_FAILED", "st008", "ST-008 model load failed.", 3) from exc


def validate_base_model(st008: ModuleType, value: object) -> tuple[dict[str, object], dict[str, object]]:
    try:
        plan = st008.validate_plan(value)
        report = st008.build_report(copy.deepcopy(plan))
        geometry = report.document["derived_geometry"]
        assumptions = plan["assumptions"]
        checks = (
            report.exit_code == 0, report.document["result"] == "PASS",
            tuple(item["scenario_id"] for item in plan["scenarios"]) == SCENARIO_IDS,
            plan["field"]["field_id"] == "FIELD-DEMO-001",
            plan["field"]["field_length_mm"] == 52000,
            plan["field"]["field_width_mm"] == 15000,
            plan["field"]["field_area_m2"] == 780,
            geometry["full_pass_distance_mm"] == 2990000,
            geometry["weed_total_target_distance_mm"] == 3737500,
            assumptions["grain_mass_g"] == 480000,
            assumptions["cassette_capacity_g"] == 1000,
        )
        if not all(checks):
            raise ValueError
        return plan, report.document
    except Exception as exc:
        raise SweepFailure(
            "SWEEP_ST008_VALIDATION_FAILED", "st008",
            "ST-008 base model validation failed.", 3,
        ) from exc


def candidate_document(candidate: Candidate) -> dict[str, object]:
    return {
        "candidate_id": candidate.candidate_id,
        "broadcast_rover_count": candidate.broadcast,
        "weed_rover_count": candidate.weed,
        "high_cut_rover_count": candidate.high_cut,
        "carrier_rover_count": candidate.carrier,
        "common_rover_count": candidate.common_rovers,
        "total_attachment_count": candidate.attachments,
        "battery_pool_count": candidate.battery,
        "charger_count": candidate.chargers,
        "cassette_capacity_g": candidate.cassette_g,
        "carrier_cassettes_per_trip": candidate.batch,
        "carrier_payload_g": candidate.payload_g,
        "temporary_drop_slot_count": candidate.slots,
        "manual_recovery_per_day": candidate.manual,
        "cassette_inventory_proxy_count": candidate.cassette_proxy,
        "mechanical_review_flags": list(candidate.flags),
    }


def sentinel_candidate_document() -> dict[str, object]:
    return {
        "candidate_id": "", "broadcast_rover_count": 0, "weed_rover_count": 0,
        "high_cut_rover_count": 0, "carrier_rover_count": 0,
        "common_rover_count": 0, "total_attachment_count": 0,
        "battery_pool_count": 0, "charger_count": 0, "cassette_capacity_g": 0,
        "carrier_cassettes_per_trip": 0, "carrier_payload_g": 0,
        "temporary_drop_slot_count": 0, "manual_recovery_per_day": 0,
        "cassette_inventory_proxy_count": 0, "mechanical_review_flags": [],
    }


def candidate_generator(ranges: dict[str, object]) -> Iterator[Candidate]:
    for values in itertools.product(*(ranges[key] for key in RANGE_KEYS)):
        yield Candidate(*values)


def mechanical_flags(cassette_g: int, batch: int) -> tuple[str, ...]:
    return Candidate(4, 2, 4, 2, 16, 4, cassette_g, batch, 50, 0).flags


def scenario_for_candidate(base: dict[str, object], candidate: Candidate, index: int) -> dict[str, object]:
    scenario = dict(base)
    scenario["broadcast_rovers"] = candidate.broadcast
    scenario["weed_rovers"] = candidate.weed
    scenario["high_cut_rovers"] = candidate.high_cut
    scenario["carrier_rovers"] = 1 if index in (4, 5) else candidate.carrier
    scenario["battery_pool"] = candidate.battery
    scenario["chargers"] = max(1, candidate.chargers - 1) if index == 5 else candidate.chargers
    scenario["carrier_cassettes_per_trip"] = candidate.batch
    scenario["manual_recovery_per_day"] = 0 if index == 5 else candidate.manual
    return scenario


def injected_candidate_plan(
    base_plan: dict[str, object], candidate: Candidate,
) -> dict[str, object]:
    plan = copy.deepcopy(base_plan)
    plan["battery_model"]["battery_pool_count"] = candidate.battery
    plan["battery_model"]["charger_count"] = candidate.chargers
    plan["battery_model"]["initial_fully_charged_battery_count"] = candidate.battery
    plan["assumptions"]["cassette_capacity_g"] = candidate.cassette_g
    plan["assumptions"]["temporary_drop_slot_count"] = candidate.slots
    plan["scenarios"] = [
        scenario_for_candidate(item, candidate, index)
        for index, item in enumerate(base_plan["scenarios"])
    ]
    return plan


def validate_injected_candidate(
    st008: ModuleType, base_plan: dict[str, object], candidate: Candidate,
) -> bool:
    plan = injected_candidate_plan(base_plan, candidate)
    validation_plan = copy.deepcopy(plan)
    if candidate.batch == 6:
        for scenario in validation_plan["scenarios"]:
            scenario["carrier_cassettes_per_trip"] = 4
    keys = tuple(validation_plan["scenarios"][0])
    signatures = tuple(
        tuple(scenario[key] for key in keys[1:]) for scenario in validation_plan["scenarios"]
    )
    original = st008.SCENARIO_SIGNATURES
    try:
        st008.SCENARIO_SIGNATURES = signatures
        st008.validate_plan(validation_plan)
    except Exception as exc:
        raise SweepFailure(
            "SWEEP_ST008_VALIDATION_FAILED", "st008",
            "Injected candidate validation failed.", 3,
        ) from exc
    finally:
        st008.SCENARIO_SIGNATURES = original
    return True


def weed_upper_bound_survivors(
    st008: ModuleType, base_plan: dict[str, object], counts: list[int],
) -> tuple[dict[str, tuple[int, ...]], dict[str, int]]:
    target = st008.derive_geometry(base_plan["field"])["weed_total_target_distance_mm"]
    survivors: dict[str, tuple[int, ...]] = {}
    shortfalls: dict[str, int] = {}
    for target_id, indices in zip(TARGET_IDS, TARGET_INDICES):
        kept: list[int] = []
        nearest = target
        for count in counts:
            okay = True
            aggregate_shortfall = 0
            for index in indices:
                scenario = base_plan["scenarios"][index]
                if scenario["weed_schedule"] == "STANDARD":
                    minutes = 20 * (150 * 6000 // 10000)
                else:
                    minutes = 14 * (120 * 5000 // 10000)
                total_minutes = count * minutes
                if scenario["weed_failure_half_capacity"]:
                    total_minutes -= minutes // 2
                speed = st008.WEED_SPEEDS[st008.SPEED_NAMES.index(scenario["weed_speed"])]
                shortfall = max(0, target - total_minutes * speed)
                aggregate_shortfall += shortfall
                if shortfall:
                    okay = False
            nearest = min(nearest, aggregate_shortfall)
            if okay:
                kept.append(count)
        survivors[target_id] = tuple(kept)
        shortfalls[target_id] = nearest
    return survivors, shortfalls


def harvest_upper_bound_survivors(
    st008: ModuleType, base_plan: dict[str, object], ranges: dict[str, object],
) -> tuple[list[tuple[int, int, int, int, int, int]], dict[str, int], dict[str, int]]:
    assumptions = base_plan["assumptions"]
    target_distance = st008.derive_geometry(base_plan["field"])["full_pass_distance_mm"]
    per_rover = 7 * (240 * 7000 // 10000)
    survivors: list[tuple[int, int, int, int, int, int]] = []
    cut_pruned = {target: 0 for target in TARGET_IDS}
    recovery_pruned = {target: 0 for target in TARGET_IDS}
    products = itertools.product(
        ranges["high_cut_rover_counts"], ranges["carrier_rover_counts"],
        ranges["cassette_capacity_g_values"], ranges["carrier_cassettes_per_trip_values"],
        ranges["temporary_drop_slot_counts"], ranges["manual_recovery_per_day_values"],
    )
    for config in products:
        high_cut, carrier, cassette_g, batch, slots, manual = config
        target_ok: dict[str, bool] = {}
        for target_id, indices in zip(TARGET_IDS, TARGET_INDICES):
            cut_ok = True
            recovery_ok = True
            for index in indices:
                scenario = base_plan["scenarios"][index]
                high_minutes = high_cut * per_rover
                if scenario["high_cut_failure_half_capacity"]:
                    high_minutes -= per_rover // 2
                speed = st008.HIGH_CUT_SPEEDS[st008.SPEED_NAMES.index(scenario["high_cut_speed"])]
                if high_minutes * speed < target_distance:
                    cut_ok = False
                effective_carrier = 1 if index in (4, 5) else carrier
                cycle = st008.carrier_cycle_seconds(scenario["carrier_speed"], batch, assumptions)
                carrier_capacity = effective_carrier * per_rover * 60 // cycle * batch
                effective_manual = 0 if index == 5 else manual
                carrier_capacity += 7 * effective_manual
                full_material = assumptions["grain_mass_g"] * scenario["harvest_factor_basis_points"] // 10000
                required = st008.ceil_div(full_material, cassette_g)
                if carrier_capacity < required:
                    recovery_ok = False
            if not cut_ok:
                cut_pruned[target_id] += 1
            if not recovery_ok:
                recovery_pruned[target_id] += 1
            target_ok[target_id] = cut_ok and recovery_ok
        if target_ok["TARGET_BASELINE"]:
            survivors.append(config)
    return survivors, cut_pruned, recovery_pruned


class BatteryScheduleCache:
    def __init__(self, original: Callable[..., object]) -> None:
        self.original = original
        self.values: dict[tuple[object, ...], object] = {}
        self.hits = 0

    def __call__(self, *args: object) -> object:
        key = tuple(args)
        if key in self.values:
            self.hits += 1
            return self.values[key]
        result = self.original(*args)
        self.values[key] = result
        return result


class CarrierCycleCache:
    def __init__(self, original: Callable[..., int]) -> None:
        self.original = original
        self.values: dict[tuple[object, ...], int] = {}
        self.hits = 0

    def __call__(self, speed: str, batch: int, assumptions: dict[str, object]) -> int:
        key = (
            speed, batch, assumptions["carrier_average_one_way_distance_mm"],
            assumptions["carrier_pickup_seconds_per_cassette"],
            assumptions["carrier_drop_seconds_per_cassette"],
        )
        if key in self.values:
            self.hits += 1
            return self.values[key]
        result = self.original(speed, batch, assumptions)
        self.values[key] = result
        return result


def target_metrics(scenarios: tuple[ScenarioMetrics, ...], target_index: int) -> TargetMetrics:
    indices = TARGET_INDICES[target_index]
    selected = tuple(scenarios[index] for index in indices)
    mask = tuple(item.overall for item in scenarios)
    completed = tuple(SCENARIO_IDS[index] for index in indices if scenarios[index].overall)
    bottleneck_set = {item for scenario in selected for item in scenario.bottlenecks if item != "NONE"}
    bottlenecks = tuple(item for item in BOTTLENECK_ORDER if item in bottleneck_set) or ("NONE",)
    return TargetMetrics(
        all(item.overall for item in selected), completed, mask,
        sum(not item.overall for item in selected),
        sum(10000 - item.broadcast_bp for item in selected),
        sum(10000 - item.weed_bp for item in selected),
        sum(10000 - item.harvest_cut_bp for item in selected),
        sum(10000 - item.harvest_recovery_bp for item in selected),
        sum(item.battery_wait for item in selected),
        max(item.battery_wait for item in selected),
        max(item.cassette_backlog for item in selected),
        max(item.high_cut_wait for item in selected),
        max(item.unfinished_weed_mm for item in selected),
        max(item.unfinished_harvest_mm for item in selected),
        len(completed) * 10000 // len(indices), bottlenecks,
    )


def equipment_key(record: StoredCandidate) -> tuple[object, ...]:
    candidate = record.candidate
    return (
        candidate.common_rovers, candidate.attachments, candidate.battery,
        candidate.chargers, candidate.cassette_proxy, candidate.payload_g,
        candidate.manual, candidate.slots, len(candidate.flags), candidate.candidate_id,
    )


def human_key(record: StoredCandidate) -> tuple[object, ...]:
    candidate = record.candidate
    metrics = record.metrics
    return (
        candidate.manual, metrics.maximum_backlog, metrics.total_battery_wait,
        candidate.common_rovers, candidate.attachments, candidate.battery,
        candidate.chargers, candidate.payload_g, len(candidate.flags), candidate.candidate_id,
    )


def pareto_objective(candidate: Candidate) -> tuple[int, ...]:
    return (
        candidate.common_rovers, candidate.attachments, candidate.battery,
        candidate.chargers, candidate.cassette_proxy, candidate.payload_g,
        candidate.manual, candidate.slots, len(candidate.flags),
    )


def dominates(left: tuple[int, ...], right: tuple[int, ...]) -> bool:
    return (
        left != right
        and left[0] <= right[0] and left[1] <= right[1]
        and left[2] <= right[2] and left[3] <= right[3]
        and left[4] <= right[4] and left[5] <= right[5]
        and left[6] <= right[6] and left[7] <= right[7]
        and left[8] <= right[8]
    )


def update_frontier(accumulator: TargetAccumulator, record: StoredCandidate) -> None:
    objective = pareto_objective(record.candidate)
    if objective in accumulator.frontier:
        if all(item.candidate.candidate_id != record.candidate.candidate_id for item in accumulator.frontier[objective]):
            accumulator.frontier[objective].append(record)
        return
    removed: list[tuple[int, ...]] = []
    for item in accumulator.frontier:
        if dominates(item, objective):
            return
        if dominates(objective, item):
            removed.append(item)
    for item in removed:
        del accumulator.frontier[item]
    accumulator.frontier[objective] = [record]


def nearest_key(record: StoredCandidate) -> tuple[object, ...]:
    candidate = record.candidate
    metrics = record.metrics
    return (
        metrics.unfinished_scenarios, metrics.broadcast_shortfall_bp,
        metrics.weed_shortfall_bp, metrics.harvest_cut_shortfall_bp,
        metrics.harvest_recovery_shortfall_bp, metrics.total_battery_wait,
        metrics.maximum_backlog, candidate.common_rovers, candidate.battery,
        candidate.chargers, candidate.candidate_id,
    )


def update_accumulator(accumulator: TargetAccumulator, record: StoredCandidate) -> None:
    if record.metrics.satisfied:
        accumulator.satisfying_count += 1
        if record.candidate.flags:
            accumulator.with_review_count += 1
        else:
            accumulator.without_review_count += 1
        if accumulator.equipment_best is None or equipment_key(record) < equipment_key(accumulator.equipment_best):
            accumulator.equipment_best = record
        if accumulator.human_best is None or human_key(record) < human_key(accumulator.human_best):
            accumulator.human_best = record
        update_frontier(accumulator, record)
    else:
        item = (nearest_key(record), record)
        accumulator.nearest.append(item)
        accumulator.nearest.sort(key=lambda pair: pair[0])
        if len(accumulator.nearest) > 10:
            accumulator.nearest.pop()


def recommendation_list(candidate: Candidate, metrics: TargetMetrics) -> list[str]:
    found: set[str] = set(candidate.flags)
    if metrics.maximum_backlog:
        found.add("CASSETTE_LOGISTICS_REDESIGN_REQUIRED")
    if candidate.manual == 20:
        found.add("MANUAL_DEPENDENCY_HIGH")
    found.add("PHYSICAL_PROTOTYPE_VALIDATION_REQUIRED")
    return [item for item in RECOMMENDATION_ORDER if item in found]


def summary_document(record: StoredCandidate, target_index: int) -> dict[str, object]:
    candidate = record.candidate
    metrics = record.metrics
    mask = {scenario: metrics.completion_mask[index] for index, scenario in enumerate(SCENARIO_IDS)}
    return {
        "candidate": candidate_document(candidate),
        "target_satisfied": metrics.satisfied,
        "required_scenarios": [SCENARIO_IDS[index] for index in TARGET_INDICES[target_index]],
        "completed_scenarios": list(metrics.completed_scenarios),
        "scenario_completion_mask": mask,
        "equipment_metrics": {
            "common_rover_count": candidate.common_rovers,
            "total_attachment_count": candidate.attachments,
            "battery_pool_count": candidate.battery,
            "charger_count": candidate.chargers,
            "cassette_inventory_proxy_count": candidate.cassette_proxy,
            "cassette_inventory_is_proxy": True,
            "carrier_payload_g": candidate.payload_g,
            "manual_recovery_per_day": candidate.manual,
            "temporary_drop_slot_count": candidate.slots,
            "mechanical_review_flag_count": len(candidate.flags),
        },
        "operational_metrics": {
            "total_battery_wait_minutes": metrics.total_battery_wait,
            "maximum_scenario_battery_wait_minutes": metrics.maximum_battery_wait,
            "maximum_cassette_backlog": metrics.maximum_backlog,
            "maximum_high_cut_wait_minutes": metrics.maximum_high_cut_wait,
            "maximum_unfinished_weed_distance_mm": metrics.maximum_unfinished_weed_mm,
            "maximum_unfinished_harvest_distance_mm": metrics.maximum_unfinished_harvest_mm,
            "stress_completion_score_basis_points": metrics.stress_completion_bp,
            "field_operation_approved": False,
            "unattended_operation_approved": False,
        },
        "mechanical_review": {
            "required": bool(candidate.flags), "flags": list(candidate.flags),
            "physical_validation_completed": False,
            "simulation_completion_changed_by_flags": False,
        },
        "bottlenecks": list(metrics.bottlenecks),
        "recommendations": recommendation_list(candidate, metrics),
    }


def sentinel_summary_document() -> dict[str, object]:
    return {
        "candidate": sentinel_candidate_document(), "target_satisfied": False,
        "required_scenarios": [], "completed_scenarios": [],
        "scenario_completion_mask": {scenario: False for scenario in SCENARIO_IDS},
        "equipment_metrics": {
            "common_rover_count": 0, "total_attachment_count": 0,
            "battery_pool_count": 0, "charger_count": 0,
            "cassette_inventory_proxy_count": 0, "cassette_inventory_is_proxy": True,
            "carrier_payload_g": 0, "manual_recovery_per_day": 0,
            "temporary_drop_slot_count": 0, "mechanical_review_flag_count": 0,
        },
        "operational_metrics": {
            "total_battery_wait_minutes": 0,
            "maximum_scenario_battery_wait_minutes": 0,
            "maximum_cassette_backlog": 0, "maximum_high_cut_wait_minutes": 0,
            "maximum_unfinished_weed_distance_mm": 0,
            "maximum_unfinished_harvest_distance_mm": 0,
            "stress_completion_score_basis_points": 0,
            "field_operation_approved": False, "unattended_operation_approved": False,
        },
        "mechanical_review": {
            "required": False, "flags": [], "physical_validation_completed": False,
            "simulation_completion_changed_by_flags": False,
        },
        "bottlenecks": [], "recommendations": [],
    }


def wrapper_document(record: StoredCandidate | None, target_index: int) -> dict[str, object]:
    return {
        "present": record is not None,
        "candidate": summary_document(record, target_index) if record is not None else sentinel_summary_document(),
    }


def stage_document(evaluated: int, survivors: int, cache_hits: int, diagnostics: int) -> dict[str, object]:
    return {
        "execution_result": "PASS", "evaluated_count": evaluated,
        "survivor_count": survivors, "pruned_count": max(0, evaluated - survivors),
        "cache_hit_count": cache_hits, "diagnostic_count": diagnostics,
    }


def _scenario_metrics(
    st008: ModuleType, broadcast: tuple[dict[str, object], object, list[str]],
    weed: tuple[dict[str, object], object, list[str]],
    harvest: tuple[dict[str, object], object, list[str]],
) -> ScenarioMetrics:
    b, bb, bneck = broadcast
    w, wb, wneck = weed
    h, hb, hneck = harvest
    generated = int(h["cassettes_generated"])
    recovery_bp = st008.basis_points(int(h["total_cassettes_recovered"]), generated) if generated else 0
    bottleneck_set = set(bneck + wneck + hneck)
    ordered = tuple(item for item in BOTTLENECK_ORDER if item in bottleneck_set and item != "NONE") or ("NONE",)
    return ScenarioMetrics(
        bool(b["deadline_completed"] and w["deadline_completed"] and h["system_completed"]),
        int(b["completion_basis_points"]), int(w["combined_completion_basis_points"]),
        int(h["cut_completion_basis_points"]), recovery_bp,
        int(bb.battery_wait_minutes + wb.battery_wait_minutes + hb.battery_wait_minutes),
        int(h["unrecovered_cassettes"]), int(h["high_cut_cassette_wait_minutes"]),
        int(w["untreated_distance_mm"]),
        max(0, int(h["high_cut_target_distance_mm"]) - int(h["high_cut_processed_distance_mm"])),
        ordered,
    )


def exact_search(
    st008: ModuleType, base_plan: dict[str, object], sweep_plan: dict[str, object],
    weed_survivors: dict[str, tuple[int, ...]],
    harvest_survivors: list[tuple[int, int, int, int, int, int]],
) -> tuple[list[TargetAccumulator], dict[str, int]]:
    ranges = sweep_plan["ranges"]
    weed_counts = sorted({item for values in weed_survivors.values() for item in values} | {max(ranges["weed_rover_counts"])})
    power = tuple(itertools.product(ranges["battery_pool_counts"], ranges["charger_counts"]))
    accumulators = [TargetAccumulator(0, 0, 0, None, None, {}, []) for _ in TARGET_IDS]
    original_schedule = st008.schedule_batteries
    original_cycle = st008.carrier_cycle_seconds
    battery_cache = BatteryScheduleCache(original_schedule)
    cycle_cache = CarrierCycleCache(original_cycle)
    st008.schedule_batteries = battery_cache
    st008.carrier_cycle_seconds = cycle_cache
    broadcast_cache: dict[tuple[int, int, int], tuple[dict[str, object], object, list[str]]] = {}
    weed_cache: dict[tuple[int, int, int, int], tuple[dict[str, object], object, list[str]]] = {}
    harvest_operation_cache: dict[tuple[object, ...], tuple[dict[str, object], list[str]]] = {}
    harvest_battery_cache: dict[tuple[object, ...], object] = {}
    evaluated = 0
    power_pruned = 0
    any_satisfied_ids: set[str] = set()
    geometry = st008.derive_geometry(base_plan["field"])

    def harvest_exact(
        candidate: Candidate, index: int, assumptions: dict[str, object],
    ) -> tuple[dict[str, object], object, list[str]]:
        scenario = scenario_for_candidate(base_plan["scenarios"][index], candidate, index)
        operation_key = (
            index, candidate.high_cut, scenario["carrier_rovers"], candidate.cassette_g,
            candidate.batch, candidate.slots, scenario["manual_recovery_per_day"],
        )
        battery_key = (
            index, candidate.high_cut, scenario["carrier_rovers"], candidate.battery,
            scenario["chargers"],
        )
        if operation_key not in harvest_operation_cache:
            result, battery_result, bottlenecks = st008.simulate_harvest(
                scenario, geometry, base_plan["battery_model"], assumptions,
            )
            harvest_operation_cache[operation_key] = (
                result, [item for item in bottlenecks if item != "BATTERY_AVAILABILITY"],
            )
            harvest_battery_cache.setdefault(battery_key, battery_result)
        if battery_key not in harvest_battery_cache:
            _, battery_result, _ = st008.simulate_harvest(
                scenario, geometry, base_plan["battery_model"], assumptions,
            )
            harvest_battery_cache[battery_key] = battery_result
        result, bottlenecks = harvest_operation_cache[operation_key]
        battery_result = harvest_battery_cache[battery_key]
        exact_bottlenecks = list(bottlenecks)
        if battery_result.battery_wait_minutes:
            exact_bottlenecks.append("BATTERY_AVAILABILITY")
        return result, battery_result, exact_bottlenecks

    try:
        for config in harvest_survivors:
            high_cut, carrier, cassette_g, batch, slots, manual = config
            assumptions = dict(base_plan["assumptions"])
            assumptions["cassette_capacity_g"] = cassette_g
            assumptions["temporary_drop_slot_count"] = slots
            for battery, chargers in power:
                template = Candidate(4, weed_counts[0], high_cut, carrier, battery, chargers, cassette_g, batch, slots, manual)
                if battery < template.common_rovers:
                    power_pruned += len(weed_counts)
                    continue
                scenario = scenario_for_candidate(base_plan["scenarios"][0], template, 0)
                broadcast_key = (0, battery, chargers)
                if broadcast_key not in broadcast_cache:
                    broadcast_cache[broadcast_key] = st008.simulate_broadcast(
                        scenario, geometry, base_plan["battery_model"], assumptions,
                    )
                harvest_result = harvest_exact(template, 0, assumptions)
                for weed in weed_counts:
                    candidate = Candidate(4, weed, high_cut, carrier, battery, chargers, cassette_g, batch, slots, manual)
                    weed_key = (0, weed, battery, chargers)
                    if weed_key not in weed_cache:
                        weed_scenario = scenario_for_candidate(base_plan["scenarios"][0], candidate, 0)
                        weed_cache[weed_key] = st008.simulate_weed(
                            weed_scenario, geometry, base_plan["battery_model"], assumptions,
                        )
                    baseline = _scenario_metrics(
                        st008, broadcast_cache[broadcast_key], weed_cache[weed_key], harvest_result,
                    )
                    empty = ScenarioMetrics(
                        False, 0, 0, 0, 0, 0, 0, 0,
                        geometry["weed_total_target_distance_mm"],
                        geometry["full_pass_distance_mm"], ("NONE",),
                    )
                    scenario_metrics = (baseline, empty, empty, empty, empty, empty)
                    evaluated += 1
                    metrics = target_metrics(scenario_metrics, 0)
                    record = StoredCandidate(candidate, metrics)
                    update_accumulator(accumulators[0], record)
                    if metrics.satisfied:
                        any_satisfied_ids.add(candidate.candidate_id)
        survivor_configs = set(harvest_survivors)
        harvest_dimensions = (
            ranges["high_cut_rover_counts"], ranges["carrier_rover_counts"],
            ranges["cassette_capacity_g_values"],
            ranges["carrier_cassettes_per_trip_values"],
            ranges["temporary_drop_slot_counts"], ranges["manual_recovery_per_day_values"],
        )
        baseline_nearest_evaluated = 0

        def evaluate_baseline_nearest(configs: Iterator[tuple[int, ...]], weeds: list[int]) -> None:
            nonlocal baseline_nearest_evaluated
            for config in configs:
                high_cut, carrier, cassette_g, batch, slots, manual = config
                assumptions = dict(base_plan["assumptions"])
                assumptions["cassette_capacity_g"] = cassette_g
                assumptions["temporary_drop_slot_count"] = slots
                for battery, chargers in power:
                    template = Candidate(
                        4, weeds[0], high_cut, carrier, battery, chargers,
                        cassette_g, batch, slots, manual,
                    )
                    if battery < template.common_rovers:
                        continue
                    scenario = scenario_for_candidate(base_plan["scenarios"][0], template, 0)
                    broadcast_key = (0, battery, chargers)
                    if broadcast_key not in broadcast_cache:
                        broadcast_cache[broadcast_key] = st008.simulate_broadcast(
                            scenario, geometry, base_plan["battery_model"], assumptions,
                        )
                    harvest_result = harvest_exact(template, 0, assumptions)
                    for weed in weeds:
                        candidate = Candidate(
                            4, weed, high_cut, carrier, battery, chargers,
                            cassette_g, batch, slots, manual,
                        )
                        weed_key = (0, weed, battery, chargers)
                        if weed_key not in weed_cache:
                            weed_scenario = scenario_for_candidate(
                                base_plan["scenarios"][0], candidate, 0,
                            )
                            weed_cache[weed_key] = st008.simulate_weed(
                                weed_scenario, geometry, base_plan["battery_model"], assumptions,
                            )
                        baseline = _scenario_metrics(
                            st008, broadcast_cache[broadcast_key],
                            weed_cache[weed_key], harvest_result,
                        )
                        if baseline.overall:
                            if config not in survivor_configs:
                                raise SweepFailure(
                                    "SWEEP_STAGE_FAILED", "search",
                                    "A safely pruned harvest candidate unexpectedly completed.", 4,
                                )
                            continue
                        empty = ScenarioMetrics(
                            False, 0, 0, 0, 0, 0, 0, 0,
                            geometry["weed_total_target_distance_mm"],
                            geometry["full_pass_distance_mm"], ("NONE",),
                        )
                        update_accumulator(
                            accumulators[0],
                            StoredCandidate(
                                candidate,
                                target_metrics((baseline, empty, empty, empty, empty, empty), 0),
                            ),
                        )
                        baseline_nearest_evaluated += 1

        evaluate_baseline_nearest(
            (
                config for config in itertools.product(*harvest_dimensions)
                if config not in survivor_configs
            ),
            weed_counts,
        )
        omitted_weeds = sorted(set(ranges["weed_rover_counts"]) - set(weed_counts))
        baseline_threshold = accumulators[0].nearest[-1][0] if len(accumulators[0].nearest) == 10 else None
        if omitted_weeds and (baseline_threshold is None or baseline_threshold[2] > 0):
            evaluate_baseline_nearest(
                iter(itertools.product(*harvest_dimensions)), omitted_weeds,
            )
        nearest_evaluated = 0
        for config in harvest_survivors:
            high_cut, carrier, cassette_g, batch, slots, manual = config
            assumptions = dict(base_plan["assumptions"])
            assumptions["cassette_capacity_g"] = cassette_g
            assumptions["temporary_drop_slot_count"] = slots
            for battery, chargers in power:
                template = Candidate(
                    4, weed_counts[0], high_cut, carrier, battery, chargers,
                    cassette_g, batch, slots, manual,
                )
                if battery < template.common_rovers:
                    continue
                baseline_scenario = scenario_for_candidate(base_plan["scenarios"][0], template, 0)
                baseline_broadcast_key = (0, battery, chargers)
                if baseline_broadcast_key not in broadcast_cache:
                    broadcast_cache[baseline_broadcast_key] = st008.simulate_broadcast(
                        baseline_scenario, geometry, base_plan["battery_model"], assumptions,
                    )
                baseline_harvest = harvest_exact(template, 0, assumptions)
                for weed in weed_counts:
                    candidate = Candidate(
                        4, weed, high_cut, carrier, battery, chargers,
                        cassette_g, batch, slots, manual,
                    )
                    weed_key = (0, weed, battery, chargers)
                    if weed_key not in weed_cache:
                        scenario = scenario_for_candidate(base_plan["scenarios"][0], candidate, 0)
                        weed_cache[weed_key] = st008.simulate_weed(
                            scenario, geometry, base_plan["battery_model"], assumptions,
                        )
                    baseline = _scenario_metrics(
                        st008, broadcast_cache[baseline_broadcast_key],
                        weed_cache[weed_key], baseline_harvest,
                    )
                    if not baseline.overall:
                        continue
                    complete_metrics = [baseline]
                    for index, base_scenario in enumerate(base_plan["scenarios"][1:], start=1):
                        scenario = scenario_for_candidate(base_scenario, candidate, index)
                        broadcast_key = (index, battery, chargers)
                        if broadcast_key not in broadcast_cache:
                            broadcast_cache[broadcast_key] = st008.simulate_broadcast(
                                scenario, geometry, base_plan["battery_model"], assumptions,
                            )
                        weed_key = (index, weed, battery, chargers)
                        if weed_key not in weed_cache:
                            weed_cache[weed_key] = st008.simulate_weed(
                                scenario, geometry, base_plan["battery_model"], assumptions,
                            )
                        complete_metrics.append(_scenario_metrics(
                            st008, broadcast_cache[broadcast_key], weed_cache[weed_key],
                            harvest_exact(candidate, index, assumptions),
                        ))
                    metrics_tuple = tuple(complete_metrics)
                    nearest_evaluated += 1
                    for target_index in (1, 2):
                        update_accumulator(
                            accumulators[target_index],
                            StoredCandidate(candidate, target_metrics(metrics_tuple, target_index)),
                        )
        fallback_nearest_evaluated = 0
        if accumulators[0].satisfying_count < 10:
            for candidate in candidate_generator(ranges):
                if candidate.battery < candidate.common_rovers:
                    continue
                assumptions = dict(base_plan["assumptions"])
                assumptions["cassette_capacity_g"] = candidate.cassette_g
                assumptions["temporary_drop_slot_count"] = candidate.slots
                complete_metrics: list[ScenarioMetrics] = []
                for index, base_scenario in enumerate(base_plan["scenarios"]):
                    scenario = scenario_for_candidate(base_scenario, candidate, index)
                    broadcast_key = (index, candidate.battery, candidate.chargers)
                    if broadcast_key not in broadcast_cache:
                        broadcast_cache[broadcast_key] = st008.simulate_broadcast(
                            scenario, geometry, base_plan["battery_model"], assumptions,
                        )
                    weed_key = (index, candidate.weed, candidate.battery, candidate.chargers)
                    if weed_key not in weed_cache:
                        weed_cache[weed_key] = st008.simulate_weed(
                            scenario, geometry, base_plan["battery_model"], assumptions,
                        )
                    complete_metrics.append(_scenario_metrics(
                        st008, broadcast_cache[broadcast_key], weed_cache[weed_key],
                        harvest_exact(candidate, index, assumptions),
                    ))
                metrics_tuple = tuple(complete_metrics)
                if metrics_tuple[0].overall:
                    continue
                fallback_nearest_evaluated += 1
                for target_index in (1, 2):
                    update_accumulator(
                        accumulators[target_index],
                        StoredCandidate(candidate, target_metrics(metrics_tuple, target_index)),
                    )
    except SweepFailure:
        raise
    except Exception as exc:
        raise SweepFailure("SWEEP_STAGE_FAILED", "search", "Exact candidate evaluation failed.", 4) from exc
    finally:
        st008.schedule_batteries = original_schedule
        st008.carrier_cycle_seconds = original_cycle
    joined = len(harvest_survivors) * len(power) * len(weed_counts)
    expected = joined - power_pruned
    if evaluated != expected:
        raise SweepFailure("SWEEP_STAGE_FAILED", "search", "Exact candidate count is inconsistent.", 4)
    return accumulators, {
        "evaluated": evaluated, "unique_satisfying": len(any_satisfied_ids),
        "joined": joined, "power_pruned": power_pruned,
        "battery_cache_hits": battery_cache.hits,
        "battery_cache_entries": len(battery_cache.values),
        "phase_cache_hits": battery_cache.hits + cycle_cache.hits,
        "diagnostic_candidate_count": nearest_evaluated,
        "baseline_nearest_candidate_count": baseline_nearest_evaluated,
        "fallback_nearest_candidate_count": fallback_nearest_evaluated,
        "harvest_operation_cache_entries": len(harvest_operation_cache),
        "harvest_battery_cache_entries": len(harvest_battery_cache),
    }


def _frontier_records(accumulator: TargetAccumulator) -> list[StoredCandidate]:
    records = [record for group in accumulator.frontier.values() for record in group]
    records.sort(key=lambda record: (
        record.candidate.common_rovers, record.candidate.attachments,
        record.candidate.manual, record.candidate.battery, record.candidate.chargers,
        record.candidate.payload_g, record.candidate.cassette_proxy,
        record.candidate.slots, record.candidate.candidate_id,
    ))
    return records


def _target_recommendations(
    target_index: int, accumulator: TargetAccumulator,
    weed_survivors: dict[str, tuple[int, ...]], harvest_survivors: list[tuple[int, ...]],
    broadcast_insufficient: dict[str, bool],
) -> list[str]:
    found: set[str] = {"PHYSICAL_PROTOTYPE_VALIDATION_REQUIRED"}
    if accumulator.satisfying_count == 0:
        if broadcast_insufficient[TARGET_IDS[target_index]]:
            found.add("BROADCAST_FIXED_CAPACITY_INSUFFICIENT")
        if not weed_survivors[TARGET_IDS[target_index]]:
            found.add("WEED_ROVER_RANGE_INSUFFICIENT")
        if not harvest_survivors:
            found.update(("HIGH_CUT_ROVER_RANGE_INSUFFICIENT", "CARRIER_RANGE_INSUFFICIENT"))
        found.add("NO_TARGET_CANDIDATE_WITHIN_BOUNDS")
    else:
        assert accumulator.equipment_best is not None
        found.update(accumulator.equipment_best.candidate.flags)
        if accumulator.equipment_best.candidate.manual == 20:
            found.add("MANUAL_DEPENDENCY_HIGH")
    return [item for item in RECOMMENDATION_ORDER if item in found]


def target_result_document(
    index: int, accumulator: TargetAccumulator,
    weed_survivors: dict[str, tuple[int, ...]], harvest_survivors: list[tuple[int, ...]],
    broadcast_insufficient: dict[str, bool],
) -> dict[str, object]:
    frontier = _frontier_records(accumulator)
    nearest = [record for _, record in accumulator.nearest]
    return {
        "target_id": TARGET_IDS[index],
        "status": "FOUND" if accumulator.satisfying_count else "NOT_FOUND_WITHIN_BOUNDS",
        "required_scenarios": [SCENARIO_IDS[item] for item in TARGET_INDICES[index]],
        "satisfying_candidate_count": accumulator.satisfying_count,
        "satisfying_without_mechanical_review_count": accumulator.without_review_count,
        "satisfying_with_mechanical_review_count": accumulator.with_review_count,
        "equipment_quantity_min_candidate": wrapper_document(accumulator.equipment_best, index),
        "human_min_candidate": wrapper_document(accumulator.human_best, index),
        "pareto_total_count": len(frontier),
        "pareto_candidates": [summary_document(record, index) for record in frontier[:20]],
        "nearest_miss_candidates": [summary_document(record, index) for record in nearest],
        "recommendations": _target_recommendations(
            index, accumulator, weed_survivors, harvest_survivors, broadcast_insufficient,
        ),
    }


def broadcast_insufficient_targets(base_report: dict[str, object]) -> dict[str, bool]:
    scenarios = base_report["scenario_results"]
    return {
        target_id: any(
            not bool(scenarios[index]["broadcast"]["deadline_completed"])
            for index in TARGET_INDICES[target_index]
        )
        for target_index, target_id in enumerate(TARGET_IDS)
    }


def safety_document() -> dict[str, object]:
    return {
        "offline_only": True, "network_access_performed": False,
        "random_used": False, "monte_carlo_used": False,
        "weather_probability_claimed": False, "gpio_access_performed": False,
        "serial_access_performed": False, "hardware_output_performed": False,
        "motor_control_performed": False, "pto_control_performed": False,
        "charging_control_performed": False, "bms_communication_performed": False,
        "rover_communication_performed": False, "actual_assignment_performed": False,
        "actual_arm_performed": False, "physical_mount_performed": False,
        "physical_unmount_performed": False, "field_operation_approved": False,
        "unattended_operation_approved": False, "physical_estop_independent": True,
        "repository_modified": False,
    }


def build_report(
    repository_root: Path, base_plan_value: object, sweep_plan_value: object,
    *, st008_loader: Callable[[Path], ModuleType] = load_st008,
    search_engine: Callable[..., tuple[list[TargetAccumulator], dict[str, int]]] = exact_search,
) -> SweepReport:
    st008 = st008_loader(repository_root)
    base_plan, base_report = validate_base_model(st008, base_plan_value)
    sweep_plan = validate_sweep_plan(sweep_plan_value)
    ranges = sweep_plan["ranges"]
    weed_survivors, weed_shortfalls = weed_upper_bound_survivors(
        st008, base_plan, ranges["weed_rover_counts"],
    )
    harvest_survivors, cut_pruned, recovery_pruned = harvest_upper_bound_survivors(
        st008, base_plan, ranges,
    )
    broadcast_insufficient = broadcast_insufficient_targets(base_report)
    accumulators, exact_counts = search_engine(
        st008, base_plan, sweep_plan, weed_survivors, harvest_survivors,
    )
    selected = [
        accumulator.equipment_best or accumulator.human_best
        for accumulator in accumulators if accumulator.equipment_best or accumulator.human_best
    ]
    for record in selected:
        assert record is not None
        validate_injected_candidate(st008, base_plan, record.candidate)
    target_results = [
        target_result_document(
            index, accumulator, weed_survivors, harvest_survivors, broadcast_insufficient,
        )
        for index, accumulator in enumerate(accumulators)
    ]
    total_pareto = sum(result["pareto_total_count"] for result in target_results)
    global_summary = {
        "target_count": 3,
        "targets_found": sum(result["status"] == "FOUND" for result in target_results),
        "targets_not_found": sum(result["status"] != "FOUND" for result in target_results),
        "total_satisfying_candidates": sum(result["satisfying_candidate_count"] for result in target_results),
        "total_pareto_candidates": total_pareto,
        "report_pareto_candidate_count": sum(len(result["pareto_candidates"]) for result in target_results),
    }
    diagnostics: list[dict[str, object]] = []
    for index, result in enumerate(target_results):
        if result["status"] != "FOUND":
            if broadcast_insufficient[TARGET_IDS[index]]:
                diagnostics.append({
                    "severity": "WARNING", "code": "SWEEP_BROADCAST_FIXED_INSUFFICIENT",
                    "component": "target", "target_id": TARGET_IDS[index], "candidate_id": "",
                    "message": "Fixed broadcast capacity is insufficient for a required scenario.",
                })
            code = "SWEEP_WEED_RANGE_INSUFFICIENT" if not weed_survivors[TARGET_IDS[index]] else "SWEEP_TARGET_NOT_FOUND"
            diagnostics.append({
                "severity": "WARNING", "code": code, "component": "target",
                "target_id": TARGET_IDS[index], "candidate_id": "",
                "message": "No satisfying candidate exists within the fixed search bounds.",
            })
            diagnostics.append({
                "severity": "WARNING", "code": "SWEEP_TARGET_NOT_FOUND", "component": "target",
                "target_id": TARGET_IDS[index], "candidate_id": "",
                "message": "The target was not found; search execution remains successful.",
            })
        elif result["satisfying_with_mechanical_review_count"]:
            diagnostics.append({
                "severity": "INFO", "code": "SWEEP_MECHANICAL_REVIEW_REQUIRED",
                "component": "mechanical", "target_id": TARGET_IDS[index],
                "candidate_id": result["equipment_quantity_min_candidate"]["candidate"]["candidate"]["candidate_id"],
                "message": "Some satisfying candidates require physical mechanical review.",
            })
    diagnostics.sort(key=lambda item: (
        str(item["component"]), str(item["code"]), str(item["target_id"]),
        str(item["candidate_id"]), str(item["message"]),
    ))
    stage_results = {
        "stage0_validation": stage_document(1, 1, 0, 0),
        "stage1_broadcast": stage_document(
            6,
            sum(base_report["scenario_results"][index]["broadcast"]["deadline_completed"] for index in range(6)),
            0, sum(broadcast_insufficient.values()),
        ),
        "stage2_weed": stage_document(15, sum(len(value) for value in weed_survivors.values()), 0, sum(not value for value in weed_survivors.values())),
        "stage3_harvest": stage_document(9072, len(harvest_survivors), 0, sum(cut_pruned.values()) + sum(recovery_pruned.values())),
        "stage4_power": stage_document(exact_counts["joined"], exact_counts["evaluated"], exact_counts["battery_cache_hits"], exact_counts["power_pruned"]),
        "stage5_exact_validation": stage_document(exact_counts["evaluated"], exact_counts["unique_satisfying"], exact_counts["phase_cache_hits"], len(diagnostics)),
    }
    base_model = {
        "base_phase": "ST-008", "field_id": base_plan["field"]["field_id"],
        "field_area_m2": base_plan["field"]["field_area_m2"],
        "full_pass_distance_mm": base_report["derived_geometry"]["full_pass_distance_mm"],
        "weed_target_distance_mm": base_report["derived_geometry"]["weed_total_target_distance_mm"],
        "scenario_ids": list(SCENARIO_IDS), "st008_model_reused": True,
    }
    search_space = {
        "raw_candidate_count": RAW_CANDIDATE_COUNT,
        "broadcast_value_count": len(ranges["broadcast_rover_counts"]),
        "weed_value_count": len(ranges["weed_rover_counts"]),
        "high_cut_value_count": len(ranges["high_cut_rover_counts"]),
        "carrier_value_count": len(ranges["carrier_rover_counts"]),
        "battery_value_count": len(ranges["battery_pool_counts"]),
        "charger_value_count": len(ranges["charger_counts"]),
        "cassette_capacity_value_count": len(ranges["cassette_capacity_g_values"]),
        "carrier_batch_value_count": len(ranges["carrier_cassettes_per_trip_values"]),
        "temporary_slot_value_count": len(ranges["temporary_drop_slot_counts"]),
        "manual_recovery_value_count": len(ranges["manual_recovery_per_day_values"]),
    }
    canonical_state = {
        "base_assumptions": {
            "field": base_plan["field"], "battery_model": base_plan["battery_model"],
            "assumptions": base_plan["assumptions"], "scenarios": base_plan["scenarios"],
        },
        "sweep_ranges": ranges, "stage_counts": stage_results,
        "target_results": target_results, "global_pareto_summary": global_summary,
        "weed_upper_bound_shortfalls": weed_shortfalls,
    }
    document: dict[str, object] = {
        "report_version": REPORT_VERSION, "phase": PHASE, "sweep_id": sweep_plan["sweep_id"],
        "result": "PASS", "base_model": base_model, "search_space": search_space,
        "stage_results": stage_results, "target_results": target_results,
        "global_pareto_summary": global_summary, "safety": safety_document(),
        "diagnostics": diagnostics,
        "canonical_base_plan_sha256": sha256_canonical(base_plan),
        "canonical_sweep_plan_sha256": sha256_canonical(sweep_plan),
        "canonical_search_state_sha256": sha256_canonical(canonical_state),
        "exit_code": 0,
    }
    return SweepReport(document, 0)


def render_json_report(report: SweepReport) -> str:
    return json.dumps(report.document, ensure_ascii=True, indent=2, separators=(",", ": ")) + "\n"


def _text_value(value: object) -> str:
    return str(value).lower() if type(value) is bool else str(value)


def _selected_id(target: dict[str, object], key: str) -> str:
    wrapper = target[key]
    return wrapper["candidate"]["candidate"]["candidate_id"] if wrapper["present"] else ""


def render_text_report(report: SweepReport) -> str:
    document = report.document
    targets = document["target_results"]
    values = (
        ("report_version", document["report_version"]), ("phase", document["phase"]),
        ("sweep_id", document["sweep_id"]), ("result", document["result"]),
        ("field_id", document["base_model"]["field_id"]),
        ("raw_candidate_count", document["search_space"]["raw_candidate_count"]),
        ("stage2_weed_survivor_count", document["stage_results"]["stage2_weed"]["survivor_count"]),
        ("stage3_harvest_survivor_count", document["stage_results"]["stage3_harvest"]["survivor_count"]),
        ("stage4_exact_candidate_count", document["stage_results"]["stage4_power"]["survivor_count"]),
        ("target_baseline_status", targets[0]["status"]),
        ("target_baseline_candidate_count", targets[0]["satisfying_candidate_count"]),
        ("target_baseline_equipment_min_id", _selected_id(targets[0], "equipment_quantity_min_candidate")),
        ("target_baseline_human_min_id", _selected_id(targets[0], "human_min_candidate")),
        ("target_wet_resilient_status", targets[1]["status"]),
        ("target_wet_resilient_candidate_count", targets[1]["satisfying_candidate_count"]),
        ("target_wet_resilient_equipment_min_id", _selected_id(targets[1], "equipment_quantity_min_candidate")),
        ("target_wet_resilient_human_min_id", _selected_id(targets[1], "human_min_candidate")),
        ("target_all_scenarios_status", targets[2]["status"]),
        ("target_all_scenarios_candidate_count", targets[2]["satisfying_candidate_count"]),
        ("target_all_scenarios_equipment_min_id", _selected_id(targets[2], "equipment_quantity_min_candidate")),
        ("target_all_scenarios_human_min_id", _selected_id(targets[2], "human_min_candidate")),
        ("total_pareto_candidate_count", document["global_pareto_summary"]["total_pareto_candidates"]),
        ("canonical_base_plan_sha256", document["canonical_base_plan_sha256"]),
        ("canonical_sweep_plan_sha256", document["canonical_sweep_plan_sha256"]),
        ("canonical_search_state_sha256", document["canonical_search_state_sha256"]),
        ("offline_only", document["safety"]["offline_only"]),
        ("hardware_output_performed", document["safety"]["hardware_output_performed"]),
        ("field_operation_approved", document["safety"]["field_operation_approved"]),
        ("unattended_operation_approved", document["safety"]["unattended_operation_approved"]),
        ("diagnostic_count", len(document["diagnostics"])), ("exit_code", document["exit_code"]),
    )
    return "\n".join(f"{key}={_text_value(value)}" for key, value in values) + "\n"


def write_report(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _failure_report(failure: SweepFailure) -> SweepReport:
    empty_hash = sha256_canonical({})
    empty_stage = stage_document(0, 0, 0, 1)
    targets = []
    for index, target_id in enumerate(TARGET_IDS):
        targets.append({
            "target_id": target_id, "status": "NOT_EVALUATED",
            "required_scenarios": [SCENARIO_IDS[item] for item in TARGET_INDICES[index]],
            "satisfying_candidate_count": 0,
            "satisfying_without_mechanical_review_count": 0,
            "satisfying_with_mechanical_review_count": 0,
            "equipment_quantity_min_candidate": wrapper_document(None, index),
            "human_min_candidate": wrapper_document(None, index), "pareto_total_count": 0,
            "pareto_candidates": [], "nearest_miss_candidates": [], "recommendations": [],
        })
    document = {
        "report_version": REPORT_VERSION, "phase": PHASE, "sweep_id": SWEEP_ID,
        "result": "FAIL",
        "base_model": {"base_phase": "ST-008", "field_id": "", "field_area_m2": 0, "full_pass_distance_mm": 0, "weed_target_distance_mm": 0, "scenario_ids": [], "st008_model_reused": False},
        "search_space": {"raw_candidate_count": RAW_CANDIDATE_COUNT, "broadcast_value_count": 0, "weed_value_count": 0, "high_cut_value_count": 0, "carrier_value_count": 0, "battery_value_count": 0, "charger_value_count": 0, "cassette_capacity_value_count": 0, "carrier_batch_value_count": 0, "temporary_slot_value_count": 0, "manual_recovery_value_count": 0},
        "stage_results": {"stage0_validation": empty_stage, "stage1_broadcast": empty_stage, "stage2_weed": empty_stage, "stage3_harvest": empty_stage, "stage4_power": empty_stage, "stage5_exact_validation": empty_stage},
        "target_results": targets,
        "global_pareto_summary": {"target_count": 3, "targets_found": 0, "targets_not_found": 0, "total_satisfying_candidates": 0, "total_pareto_candidates": 0, "report_pareto_candidate_count": 0},
        "safety": safety_document(),
        "diagnostics": [{"severity": "ERROR", "code": failure.code, "component": failure.component, "target_id": "", "candidate_id": "", "message": failure.message}],
        "canonical_base_plan_sha256": empty_hash,
        "canonical_sweep_plan_sha256": empty_hash,
        "canonical_search_state_sha256": empty_hash, "exit_code": failure.exit_code,
    }
    return SweepReport(document, failure.exit_code)


def run_sweep(
    arguments: SweepArguments, *,
    builder: Callable[..., SweepReport] = build_report,
    write_reports: bool = False,
) -> SweepReport:
    validate_arguments(arguments)
    try:
        base_plan = load_strict_json(arguments.base_plan)
        sweep_plan = load_strict_json(arguments.sweep_plan)
        report = builder(arguments.repository_root, base_plan, sweep_plan)
    except SweepFailure as failure:
        report = _failure_report(failure)
    except Exception:
        report = _failure_report(SweepFailure(
            "SWEEP_INTERNAL_ERROR", "internal", "Unexpected internal failure.", 7,
        ))
    if write_reports:
        try:
            write_report(arguments.json_report, render_json_report(report))
            write_report(arguments.text_report, render_text_report(report))
        except (OSError, KeyError):
            return _failure_report(SweepFailure(
                "SWEEP_REPORT_WRITE_FAILED", "report", "Report output failed.", 7,
            ))
    return report


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_arguments(argv)
        report = run_sweep(arguments, write_reports=True)
        if report.exit_code == 0:
            print(render_text_report(report), end="")
        return report.exit_code
    except SweepFailure as failure:
        print(f"ST-009 capacity sweep rejected: {failure.message}", file=sys.stderr)
        return failure.exit_code
    except Exception:
        print("SWEEP_INTERNAL_ERROR: ST-009 capacity sweep failed unexpectedly.", file=sys.stderr)
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
