#!/usr/bin/env python3
"""Deterministic offline multi-field weed fleet scheduler for ST-010."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Callable, Iterable, Sequence


REPORT_VERSION = 1
PHASE = "ST-010"
PLAN_VERSION = 1
PLAN_ID = "ST010-MULTI-FIELD-WEED-DEMO"
GROUP_IDS = (
    "GROUP-HOME", "GROUP-OTHER-CONSIGNED", "GROUP-CONSIGNED",
    "GROUP-OWN-A", "GROUP-OWN-B",
)
GROUP_COUNTS = (9, 3, 2, 2, 3)
POLICIES = (
    "ONE_FIELD_CONCENTRATED", "TWO_FIELDS_EQUAL", "TWO_FIELDS_WEIGHTED",
    "FINISH_FIRST", "ROAD_SIDE_BATCHED",
)
SPEED_PROFILES = (
    ("CONSERVATIVE", 400), ("CURRENT_STANDARD", 700),
    ("CURRENT_IMPROVED", 1000),
)
DAILY_WINDOWS = (
    ("SHORT_WINDOW", 150), ("STANDARD_WINDOW", 300), ("FULL_DAY", 480),
)
OPERATOR_OPTIONS = (1, 2, 3)
VEHICLE_CAPACITIES = (6, 8, 10)
BATTERY_POOLS = (16, 24, 36)
ROVER_STATES = (
    "AT_DEPOT", "IN_MANUAL_TRANSPORT", "DEPLOYED", "WORKING",
    "BATTERY_SWAP", "BATTERY_WAIT", "MANUAL_RECOVERY", "MAINTENANCE",
    "DONE_FOR_DAY",
)
FIELD_STATUSES = ("WAITING", "IN_PROGRESS", "COMPLETED", "MANUAL_REQUIRED")
SCOUT_SOURCES = ("PRELOADED_MAP", "MANUAL_DRONE", "GROUND_SCOUT", "NO_SCOUT")
BOTTLENECK_ORDER = (
    "NONE", "WORKDAY_TOO_SHORT", "SPEED_INSUFFICIENT", "ROVER_COUNT_INSUFFICIENT",
    "VEHICLE_CAPACITY", "MANUAL_LOADING_TIME", "STATION_RELOCATION",
    "GROUP_TRANSFER", "BATTERY_POOL", "CHARGER_COUNT", "BATTERY_RUNTIME",
    "NO_MIDDAY_BATTERY_DELIVERY", "FIELD_GEOMETRY_ESTIMATED",
    "FIELD_AREA_MAPPING_UNRESOLVED",
)
RECOMMENDATION_ORDER = (
    "MEASURE_ACTUAL_19_FIELD_AREAS", "RESOLVE_R4_TO_CURRENT_FIELD_MAPPING",
    "MEASURE_ROVER_LOADING_CAPACITY", "MEASURE_ROVER_OPERATING_SPEED",
    "MEASURE_WEED_POWER_CONSUMPTION", "INCREASE_DAILY_WORK_WINDOW",
    "INCREASE_EFFECTIVE_SPEED", "INCREASE_WEED_ROVER_COUNT",
    "INCREASE_BATTERY_POOL", "INCREASE_CHARGER_COUNT",
    "REDUCE_FIELD_TRANSFER_FREQUENCY", "USE_ROAD_SIDE_BATCHED_OPERATION",
    "ADD_SECOND_MOBILE_STATION_FOR_PARALLEL_FIELDS",
    "CONSIDER_MIDDAY_BATTERY_SHUTTLE", "MANUAL_DRONE_SCOUT_SEPARATE_STUDY",
    "PHYSICAL_FIELD_VALIDATION_REQUIRED",
)
DIAGNOSTIC_CODES = (
    "MFW_INVALID_ARGUMENT", "MFW_REPOSITORY_ROOT_INVALID", "MFW_PLAN_INVALID",
    "MFW_REPORT_PATH_INSIDE_REPOSITORY", "MFW_REPORT_PARENT_INVALID",
    "MFW_ST008_LOAD_FAILED", "MFW_AREA_REFERENCE_INVALID",
    "MFW_OPERATIONAL_AREA_INVALID", "MFW_FIELD_COUNT_MISMATCH",
    "MFW_GROUP_COUNT_MISMATCH", "MFW_DISTANCE_CALCULATION_INVALID",
    "MFW_SEARCH_COUNT_MISMATCH", "MFW_SCHEDULE_FAILED",
    "MFW_TARGET_INCOMPLETE", "MFW_REQUIRED_SPEED_NOT_FOUND",
    "MFW_REQUIRED_ROVER_COUNT_NOT_FOUND", "MFW_BATTERY_SHORTFALL",
    "MFW_CHARGER_SHORTFALL", "MFW_TRANSFER_OVERHEAD_HIGH",
    "MFW_FIELD_MAPPING_UNRESOLVED", "MFW_GEOMETRY_ESTIMATED",
    "MFW_REPORT_WRITE_FAILED", "MFW_INTERNAL_ERROR",
)


class MfwFailure(RuntimeError):
    def __init__(self, code: str, component: str, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.component = component
        self.message = message
        self.exit_code = exit_code


@dataclass(frozen=True)
class SchedulerArguments:
    repository_root: Path
    plan: Path
    json_report: Path
    text_report: Path


@dataclass(frozen=True)
class SchedulerReport:
    document: dict[str, object]
    exit_code: int


@dataclass(frozen=True)
class Configuration:
    policy: str
    speed_profile: str
    speed_mm_per_min: int
    daily_window_minutes: int
    operator_count: int
    vehicle_rover_capacity: int
    battery_pool_count: int

    @property
    def configuration_id(self) -> str:
        return (
            f"CFG-{self.policy}-S{self.speed_mm_per_min:04d}"
            f"-D{self.daily_window_minutes:04d}-O{self.operator_count:02d}"
            f"-V{self.vehicle_rover_capacity:02d}-B{self.battery_pool_count:02d}"
        )


@dataclass
class FieldState:
    field_id: str
    group_id: str
    area_m2: int
    target_distance_mm: int
    remaining_distance_mm: int
    first_work_day: int = 0
    completion_day: int = 0
    interruption_count: int = 0
    deployment_count: int = 0
    battery_wait_minutes: int = 0


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise MfwFailure("MFW_INVALID_ARGUMENT", "cli", "Invalid command arguments.", 2)


def parse_arguments(argv: Sequence[str] | None = None) -> SchedulerArguments:
    parser = SafeArgumentParser()
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--json-report", required=True)
    parser.add_argument("--text-report", required=True)
    values = parser.parse_args(argv)
    return SchedulerArguments(
        Path(values.repository_root), Path(values.plan),
        Path(values.json_report), Path(values.text_report),
    )


def is_contained(candidate: Path, parent: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(parent.resolve(strict=True))
        return True
    except (OSError, ValueError):
        return False


def validate_arguments(arguments: SchedulerArguments) -> None:
    if not arguments.repository_root.is_dir():
        raise MfwFailure("MFW_REPOSITORY_ROOT_INVALID", "path", "Repository root is invalid.", 2)
    if not arguments.plan.is_file():
        raise MfwFailure("MFW_PLAN_INVALID", "path", "Plan file does not exist.", 2)
    if arguments.json_report.resolve(strict=False) == arguments.text_report.resolve(strict=False):
        raise MfwFailure("MFW_INVALID_ARGUMENT", "path", "Report paths must differ.", 2)
    for report in (arguments.json_report, arguments.text_report):
        if not report.parent.is_dir() or report.parent.is_file():
            raise MfwFailure("MFW_REPORT_PARENT_INVALID", "path", "Report parent is invalid.", 2)
        if is_contained(report, arguments.repository_root):
            raise MfwFailure(
                "MFW_REPORT_PATH_INSIDE_REPOSITORY", "path",
                "Report must be outside the repository.", 2,
            )


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise MfwFailure("MFW_PLAN_INVALID", "plan", "Duplicate JSON key.", 3)
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise MfwFailure("MFW_PLAN_INVALID", "plan", "Non-finite number is prohibited.", 3)


def _reject_null(value: object) -> None:
    if value is None:
        raise MfwFailure("MFW_PLAN_INVALID", "plan", "Null is prohibited.", 3)
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
    except MfwFailure:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise MfwFailure("MFW_PLAN_INVALID", "plan", "Plan is not strict JSON.", 3) from exc


def _exact(value: object, keys: tuple[str, ...], context: str) -> dict[str, object]:
    if type(value) is not dict or tuple(value.keys()) != keys:
        raise MfwFailure("MFW_PLAN_INVALID", "plan", f"{context} properties are invalid.", 3)
    return value


def _integer(value: object, minimum: int, maximum: int, context: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise MfwFailure("MFW_PLAN_INVALID", "plan", f"{context} is invalid.", 3)
    return value


def _boolean(value: object, context: str) -> bool:
    if type(value) is not bool:
        raise MfwFailure("MFW_PLAN_INVALID", "plan", f"{context} is invalid.", 3)
    return value


def _enum(value: object, choices: tuple[str, ...], context: str) -> str:
    if type(value) is not str or value not in choices:
        raise MfwFailure("MFW_PLAN_INVALID", "plan", f"{context} is invalid.", 3)
    return value


def canonical_json(value: object, *, sort_keys: bool = True) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=sort_keys,
        separators=(",", ":"), allow_nan=False,
    )


def sha256_canonical(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def ceil_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise MfwFailure("MFW_SCHEDULE_FAILED", "scheduler", "Invalid divisor.", 4)
    return (numerator + denominator - 1) // denominator


def basis_points(value: int, target: int) -> int:
    if target <= 0:
        return 0
    return min(10000, value * 10000 // target)


def round_half_up(value: Fraction) -> int:
    if value < 0:
        return -round_half_up(-value)
    return (value.numerator * 2 + value.denominator) // (value.denominator * 2)


def load_st008(repository_root: Path) -> ModuleType:
    path = repository_root / "software/station_control/station/seasonal_field_simulator.py"
    try:
        spec = importlib.util.spec_from_file_location("st010_reused_seasonal_field_simulator", path)
        if spec is None or spec.loader is None:
            raise ImportError
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        if module.PHASE != "ST-008":
            raise ImportError
        for name in ("ceil_div", "basis_points", "derive_geometry", "simulate_weed", "schedule_batteries"):
            if not callable(getattr(module, name, None)):
                raise ImportError
        return module
    except Exception as exc:
        raise MfwFailure("MFW_ST008_LOAD_FAILED", "reuse", "ST-008 could not be loaded.", 4) from exc


def validate_plan(value: object) -> dict[str, object]:
    root_keys = (
        "plan_version", "plan_id", "area_reference", "operational_field_model",
        "planning_model", "work_day_model", "fleet_model", "logistics_model",
        "battery_model", "scout_model", "future_features", "simulation_matrix",
    )
    plan = _exact(value, root_keys, "plan")
    if _integer(plan["plan_version"], 1, 1, "plan version") != PLAN_VERSION or plan["plan_id"] != PLAN_ID:
        raise MfwFailure("MFW_PLAN_INVALID", "plan", "Plan identity is invalid.", 3)
    area = _exact(plan["area_reference"], (
        "reference_id", "mapping_status", "r4_total_area_m2", "r4_parcel_count",
        "r4_rice_area_m2", "r4_rice_parcel_count", "r4_rice_parcel_areas_m2",
        "r4_grass_parcel_areas_m2", "r4_self_conservation_area_m2",
    ), "area reference")
    if area["reference_id"] != "R4_DECLARED_AREA_REFERENCE" or area["mapping_status"] != "UNRESOLVED":
        raise MfwFailure("MFW_AREA_REFERENCE_INVALID", "area", "Area reference identity is invalid.", 3)
    rice = area["r4_rice_parcel_areas_m2"]
    grass = area["r4_grass_parcel_areas_m2"]
    if type(rice) is not list or type(grass) is not list or len(rice) != 16 or len(grass) != 3:
        raise MfwFailure("MFW_AREA_REFERENCE_INVALID", "area", "Area reference parcel count is invalid.", 3)
    if any(type(item) is not int or item <= 0 for item in rice + grass):
        raise MfwFailure("MFW_AREA_REFERENCE_INVALID", "area", "Area reference parcel value is invalid.", 3)
    expected_area = (31950, 20, 22040, 16, 3130)
    actual_area = tuple(area[key] for key in (
        "r4_total_area_m2", "r4_parcel_count", "r4_rice_area_m2",
        "r4_rice_parcel_count", "r4_self_conservation_area_m2",
    ))
    if actual_area != expected_area or sum(rice) != 22040 or sum(grass) != 6780:
        raise MfwFailure("MFW_AREA_REFERENCE_INVALID", "area", "Area reference totals are invalid.", 3)
    operational = _exact(plan["operational_field_model"], (
        "field_model_id", "field_count", "total_area_m2", "area_source",
        "parcel_mapping_status", "geometry_estimated", "groups", "fields",
    ), "operational field model")
    if tuple(operational[key] for key in (
        "field_model_id", "field_count", "total_area_m2", "area_source",
        "parcel_mapping_status", "geometry_estimated",
    )) != ("CURRENT_OPERATIONAL_EQUALIZED_19", 19, 27000, "TOTAL_ONLY_EQUALIZED_ESTIMATE", "UNRESOLVED", True):
        raise MfwFailure("MFW_OPERATIONAL_AREA_INVALID", "field", "Operational field model is invalid.", 3)
    groups = operational["groups"]
    fields = operational["fields"]
    if type(groups) is not list or len(groups) != 5:
        raise MfwFailure("MFW_GROUP_COUNT_MISMATCH", "field", "Group count is invalid.", 3)
    for index, raw in enumerate(groups):
        group = _exact(raw, ("group_id", "field_count"), f"group {index}")
        if (group["group_id"], group["field_count"]) != (GROUP_IDS[index], GROUP_COUNTS[index]):
            raise MfwFailure("MFW_GROUP_COUNT_MISMATCH", "field", "Group definition is invalid.", 3)
    if type(fields) is not list or len(fields) != 19:
        raise MfwFailure("MFW_FIELD_COUNT_MISMATCH", "field", "Field count is invalid.", 3)
    seen: set[str] = set()
    counts = {group_id: 0 for group_id in GROUP_IDS}
    for index, raw in enumerate(fields):
        field = _exact(raw, ("field_id", "group_id", "area_m2", "area_estimated"), f"field {index}")
        if type(field["field_id"]) is not str or field["field_id"] in seen:
            raise MfwFailure("MFW_OPERATIONAL_AREA_INVALID", "field", "Field ID is invalid or duplicated.", 3)
        seen.add(field["field_id"])
        if field["group_id"] not in GROUP_IDS:
            raise MfwFailure("MFW_OPERATIONAL_AREA_INVALID", "field", "Field group is unknown.", 3)
        _integer(field["area_m2"], 1, 1000000, "field area")
        if field["area_estimated"] is not True:
            raise MfwFailure("MFW_OPERATIONAL_AREA_INVALID", "field", "Field estimate flag is invalid.", 3)
        counts[str(field["group_id"])] += 1
    if tuple(counts[group_id] for group_id in GROUP_IDS) != GROUP_COUNTS:
        raise MfwFailure("MFW_GROUP_COUNT_MISMATCH", "field", "Field group totals are invalid.", 3)
    areas = [int(field["area_m2"]) for field in fields]
    if sum(areas) != 27000 or areas.count(1422) != 1 or areas.count(1421) != 18:
        raise MfwFailure("MFW_OPERATIONAL_AREA_INVALID", "field", "Operational area total is invalid.", 3)
    planning = _exact(plan["planning_model"], (
        "reference_field_area_m2", "reference_full_pass_distance_mm",
        "area_level_target_distance_mm", "field_level_target_distance_mm",
        "target_id", "full_pass_only",
    ), "planning model")
    if tuple(planning.values()) != (
        780, 2990000, 103500000, 103500006,
        "FULL_PASS_ALL_19_WITHIN_10_WORK_DAYS", True,
    ):
        raise MfwFailure("MFW_DISTANCE_CALCULATION_INVALID", "distance", "Planning model is invalid.", 3)
    work = _exact(plan["work_day_model"], (
        "work_day_count", "availability_basis_points", "daily_windows",
    ), "work-day model")
    if work["work_day_count"] != 10 or work["availability_basis_points"] != 6000:
        raise MfwFailure("MFW_PLAN_INVALID", "plan", "Work-day model is invalid.", 3)
    windows = work["daily_windows"]
    if type(windows) is not list or [tuple(_exact(item, ("window_id", "scheduled_minutes_per_day"), "window").values()) for item in windows] != list(DAILY_WINDOWS):
        raise MfwFailure("MFW_PLAN_INVALID", "plan", "Daily windows are invalid.", 3)
    fleet = _exact(plan["fleet_model"], (
        "weed_rover_count", "maximum_simultaneous_fields", "rover_state_enum",
    ), "fleet model")
    if tuple(fleet.values()) != (12, 2, list(ROVER_STATES)):
        raise MfwFailure("MFW_PLAN_INVALID", "plan", "Fleet model is invalid.", 3)
    logistics = _exact(plan["logistics_model"], (
        "vehicle_count", "operator_count_options", "vehicle_rover_capacity_options",
        "vehicle_capacity_provisional_upper_bound", "loading_minutes_per_rover",
        "unloading_minutes_per_rover", "secure_and_safety_check_minutes_per_trip",
        "same_group_drive_minutes_per_trip", "cross_group_drive_minutes_per_trip",
        "station_pack_minutes", "station_setup_minutes", "station_requires_dedicated_trip",
        "maximum_group_changes_per_day", "morning_deployment_required",
        "daily_recovery_required", "battery_handling_minutes_per_battery",
    ), "logistics model")
    expected_logistics = (1, [1, 2, 3], [6, 8, 10], True, 4, 4, 10, 10, 20, 20, 25, True, 1, True, True, 1)
    if tuple(logistics.values()) != expected_logistics:
        raise MfwFailure("MFW_PLAN_INVALID", "plan", "Logistics model is invalid.", 3)
    battery = _exact(plan["battery_model"], (
        "battery_id", "battery_pool_options", "charger_count", "battery_runtime_minutes",
        "battery_swap_minutes", "charge_minutes", "overnight_charge_window_minutes",
        "service_windows", "midday_battery_shuttle_enabled", "mobile_charging_station_count",
    ), "battery model")
    expected_battery = (
        "BATTERY-DEMO-LIFEPO4-12V-10AH", [16, 24, 36], 4, 150, 3, 180,
        720, ["MORNING_DEPLOYMENT", "EVENING_RECOVERY"], False, 1,
    )
    if tuple(battery.values()) != expected_battery:
        raise MfwFailure("MFW_PLAN_INVALID", "battery", "Battery model is invalid.", 3)
    scout = _exact(plan["scout_model"], ("source", "priority_information_required"), "scout model")
    _enum(scout["source"], SCOUT_SOURCES, "scout source")
    _boolean(scout["priority_information_required"], "priority information")
    if tuple(scout.values()) != ("PRELOADED_MAP", False):
        raise MfwFailure("MFW_PLAN_INVALID", "scout", "Formal scout source is invalid.", 3)
    features = plan["future_features"]
    if type(features) is not list or len(features) != 2:
        raise MfwFailure("MFW_PLAN_INVALID", "safety", "Future features are invalid.", 3)
    expected_features = ("ADJACENT_FIELD_SELF_TRANSFER", "ROVER_SWARM_STATION_TRANSPORT")
    for index, raw in enumerate(features):
        feature = _exact(raw, ("feature_id", "enabled"), f"future feature {index}")
        if tuple(feature.values()) != (expected_features[index], False):
            raise MfwFailure("MFW_PLAN_INVALID", "safety", "Future feature must be disabled.", 3)
    matrix = _exact(plan["simulation_matrix"], (
        "allocation_policies", "speed_profiles", "raw_configuration_count",
        "all_configurations_evaluated", "random_sampling", "automatic_range_reduction",
    ), "simulation matrix")
    if matrix["allocation_policies"] != list(POLICIES):
        raise MfwFailure("MFW_SEARCH_COUNT_MISMATCH", "search", "Allocation policies are invalid.", 3)
    profiles = matrix["speed_profiles"]
    if type(profiles) is not list or [tuple(_exact(item, ("speed_profile", "speed_mm_per_min"), "speed").values()) for item in profiles] != list(SPEED_PROFILES):
        raise MfwFailure("MFW_SEARCH_COUNT_MISMATCH", "search", "Speed profiles are invalid.", 3)
    if tuple(matrix[key] for key in (
        "raw_configuration_count", "all_configurations_evaluated",
        "random_sampling", "automatic_range_reduction",
    )) != (1215, True, False, False):
        raise MfwFailure("MFW_SEARCH_COUNT_MISMATCH", "search", "Search matrix is invalid.", 3)
    return plan


def planning_distance_mm(area_m2: int, st008: ModuleType | None = None) -> int:
    if type(area_m2) is not int or area_m2 <= 0:
        raise MfwFailure("MFW_DISTANCE_CALCULATION_INVALID", "distance", "Field area is invalid.", 3)
    divide = st008.ceil_div if st008 is not None else ceil_div
    return int(divide(2990000 * area_m2, 780))


def configuration_generator() -> Iterable[Configuration]:
    for policy, speed, window, operators, capacity, batteries in itertools.product(
        POLICIES, SPEED_PROFILES, DAILY_WINDOWS, OPERATOR_OPTIONS,
        VEHICLE_CAPACITIES, BATTERY_POOLS,
    ):
        yield Configuration(policy, speed[0], speed[1], window[1], operators, capacity, batteries)


def transport_accounting(rover_count: int, capacity: int, operators: int, cross_group: bool) -> dict[str, int]:
    trips = ceil_div(rover_count, capacity)
    drive = 20 if cross_group else 10
    loading = ceil_div(rover_count * 4, operators)
    unloading = ceil_div(rover_count * 4, operators)
    rover_trip_minutes = trips * (10 + drive)
    station_trip_minutes = 10 + drive
    deployment = loading + unloading + rover_trip_minutes + station_trip_minutes + 25
    recovery = loading + unloading + rover_trip_minutes + station_trip_minutes + 20
    return {
        "rover_trip_count": trips,
        "station_trip_count": 1,
        "loading_minutes": loading,
        "unloading_minutes": unloading,
        "driving_minutes": (trips + 1) * drive,
        "station_handling_minutes": 45,
        "deployment_minutes": deployment,
        "recovery_minutes": recovery,
    }


def reallocation_accounting(
    rovers_transferred: int, capacity: int, operators: int,
    cross_group: bool, station_transferred: bool,
) -> dict[str, int]:
    trips = ceil_div(rovers_transferred, capacity) if rovers_transferred else 0
    drive = 20 if cross_group else 10
    loading = ceil_div(rovers_transferred * 4, operators) if rovers_transferred else 0
    unloading = ceil_div(rovers_transferred * 4, operators) if rovers_transferred else 0
    rover_minutes = trips * (10 + drive)
    station_trip = 1 if station_transferred else 0
    station_minutes = (20 + 10 + drive + 25) if station_transferred else 0
    return {
        "rover_trip_count": trips,
        "station_trip_count": station_trip,
        "loading_minutes": loading,
        "unloading_minutes": unloading,
        "driving_minutes": (trips + station_trip) * drive,
        "station_handling_minutes": 45 if station_transferred else 0,
        "total_minutes": loading + unloading + rover_minutes + station_minutes,
    }


def _incomplete_in_group(states: list[FieldState], group_id: str) -> list[FieldState]:
    return [state for state in states if state.group_id == group_id and state.remaining_distance_mm > 0]


def choose_group(states: list[FieldState], current_group: str = "") -> str:
    if current_group and _incomplete_in_group(states, current_group):
        return current_group
    for group_id in GROUP_IDS:
        if _incomplete_in_group(states, group_id):
            return group_id
    return ""


def choose_fields(states: list[FieldState], group_id: str, policy: str) -> list[FieldState]:
    candidates = _incomplete_in_group(states, group_id)
    if not candidates:
        return []
    if policy == "ROAD_SIDE_BATCHED":
        return sorted(candidates, key=lambda item: item.field_id)[:1]
    if policy == "FINISH_FIRST":
        return sorted(candidates, key=lambda item: (item.remaining_distance_mm, item.field_id))[:2]
    if policy == "TWO_FIELDS_WEIGHTED":
        return sorted(candidates, key=lambda item: (-item.remaining_distance_mm, item.field_id))[:2]
    ordered = sorted(candidates, key=lambda item: (item.remaining_distance_mm, item.field_id))
    return ordered[:2] if policy == "TWO_FIELDS_EQUAL" else ordered[:1]


def allocation_counts(policy: str, field_count: int, rover_count: int) -> tuple[int, ...]:
    if field_count <= 0:
        return ()
    if field_count == 1:
        return (rover_count,)
    if policy == "TWO_FIELDS_EQUAL":
        first = rover_count // 2
        return (first, rover_count - first)
    first = ceil_div(rover_count * 2, 3)
    return (first, rover_count - first)


def _ordered_unique(items: Iterable[str], order: tuple[str, ...]) -> list[str]:
    present = set(items)
    return [item for item in order if item in present]


def _simulate(
    fields: list[dict[str, object]], configuration: Configuration,
    rover_count: int = 12, battery_pool_override: int = 0,
    include_details: bool = True,
) -> dict[str, object]:
    states = [
        FieldState(
            str(field["field_id"]), str(field["group_id"]), int(field["area_m2"]),
            planning_distance_mm(int(field["area_m2"])),
            planning_distance_mm(int(field["area_m2"])),
        )
        for field in fields
    ]
    total_target = sum(state.target_distance_mm for state in states)
    battery_pool = battery_pool_override or configuration.battery_pool_count
    full_inventory = battery_pool
    minimum_inventory = battery_pool
    total_field_transfers = 0
    total_group_transfers = 0
    total_vehicle_trips = 0
    total_station_trips = 0
    total_swaps = 0
    total_waits = 0
    total_human = 0
    max_daily_human = 0
    daily_results: list[dict[str, object]] = []
    current_group = ""
    battery_shortfall_days = 0
    for day in range(1, 11):
        if all(state.remaining_distance_mm == 0 for state in states):
            break
        group_id = choose_group(states, current_group)
        if not group_id:
            break
        cross_deploy = bool(current_group and current_group != group_id)
        current_group = group_id
        transport = transport_accounting(rover_count, configuration.vehicle_rover_capacity, configuration.operator_count, cross_deploy)
        deployment = transport["deployment_minutes"]
        recovery = transport["recovery_minutes"]
        remaining_window = max(0, configuration.daily_window_minutes - deployment - recovery)
        minute_budget = remaining_window * 6000 // 10000
        day_vehicle_trips = (transport["rover_trip_count"] + 1) * 2
        day_station_trips = 2
        initial_fields = choose_fields(states, group_id, configuration.policy)
        counts = allocation_counts(configuration.policy, len(initial_fields), rover_count)
        allocations: list[FieldState] = []
        for state, count in zip(initial_fields, counts):
            allocations.extend([state] * count)
            state.deployment_count += 1
        primary_id = initial_fields[0].field_id if initial_fields else ""
        morning_full_inventory = full_inventory
        battery_remaining = [0 for _ in range(rover_count)]
        has_battery = [False for _ in range(rover_count)]
        assigned = min(rover_count, full_inventory)
        for index in range(assigned):
            has_battery[index] = True
            battery_remaining[index] = 150
        full_inventory -= assigned
        primary_spares = full_inventory
        secondary_spares = 0
        if len(initial_fields) == 2 and full_inventory:
            secondary_rovers = counts[1]
            secondary_spares = full_inventory * secondary_rovers // max(1, rover_count)
            primary_spares -= secondary_spares
        minimum_inventory = min(minimum_inventory, primary_spares + secondary_spares)
        charging_due: list[int] = []
        charge_queue = 0
        swap_delay = [0 for _ in range(rover_count)]
        day_processed = 0
        productive_minutes_actual = 0
        day_swaps = 0
        day_waits = 0
        completed_today: list[str] = []
        worked_fields: set[str] = set()
        group_changes = 0
        delay = 0
        transfer_human = 0
        allocation_peak: dict[str, int] = {}
        battery_sessions = assigned
        for minute in range(1, minute_budget + 1):
            completed_charges = sum(due == minute for due in charging_due)
            if completed_charges:
                primary_spares += completed_charges
                charging_due = [due for due in charging_due if due != minute]
            while charge_queue and len(charging_due) < 4:
                charge_queue -= 1
                charging_due.append(minute + 180)
            if delay:
                delay -= 1
                continue
            if not allocations:
                break
            processed_before_minute = day_processed
            per_field: dict[str, int] = {}
            for state in allocations:
                per_field[state.field_id] = per_field.get(state.field_id, 0) + 1
            for field_id, count in per_field.items():
                allocation_peak[field_id] = max(allocation_peak.get(field_id, 0), count)
            completed_during_minute: set[str] = set()
            for index, state in enumerate(allocations):
                if state.remaining_distance_mm <= 0:
                    continue
                if swap_delay[index] > 0:
                    swap_delay[index] -= 1
                    continue
                if not has_battery[index]:
                    primary = state.field_id == primary_id
                    if primary and primary_spares > 0:
                        primary_spares -= 1
                    elif not primary and secondary_spares > 0:
                        secondary_spares -= 1
                    else:
                        day_waits += 1
                        state.battery_wait_minutes += 1
                        continue
                    has_battery[index] = True
                    battery_remaining[index] = 150
                    swap_delay[index] = 3
                    day_swaps += 1
                    battery_sessions += 1
                    minimum_inventory = min(minimum_inventory, primary_spares + secondary_spares)
                    continue
                processed = min(configuration.speed_mm_per_min, state.remaining_distance_mm)
                if processed:
                    if state.first_work_day == 0:
                        state.first_work_day = day
                    worked_fields.add(state.field_id)
                    state.remaining_distance_mm -= processed
                    day_processed += processed
                    battery_remaining[index] -= 1
                if state.remaining_distance_mm == 0 and state.completion_day == 0:
                    state.completion_day = day
                    completed_during_minute.add(state.field_id)
                if battery_remaining[index] == 0:
                    has_battery[index] = False
                    if state.field_id == primary_id:
                        charge_queue += 1
            if day_processed > processed_before_minute:
                productive_minutes_actual += 1
            if completed_during_minute:
                for field_id in sorted(completed_during_minute):
                    if field_id not in completed_today:
                        completed_today.append(field_id)
                old_ids = {state.field_id for state in allocations}
                old_counts = {field_id: sum(state.field_id == field_id for state in allocations) for field_id in old_ids}
                cross_group = False
                if not _incomplete_in_group(states, current_group):
                    if group_changes >= 1:
                        allocations = []
                        continue
                    new_group = choose_group(states, "")
                    if not new_group:
                        allocations = []
                        continue
                    current_group = new_group
                    group_changes += 1
                    total_group_transfers += 1
                    cross_group = True
                new_fields = choose_fields(states, current_group, configuration.policy)
                new_counts = allocation_counts(configuration.policy, len(new_fields), rover_count)
                new_count_map = {state.field_id: count for state, count in zip(new_fields, new_counts)}
                retained = sum(min(old_counts.get(field_id, 0), count) for field_id, count in new_count_map.items())
                rovers_transferred = rover_count - retained
                new_primary_id = new_fields[0].field_id if new_fields else ""
                station_transferred = bool(new_primary_id and new_primary_id != primary_id)
                transfer = reallocation_accounting(
                    rovers_transferred, configuration.vehicle_rover_capacity,
                    configuration.operator_count, cross_group, station_transferred,
                )
                delay = transfer["total_minutes"]
                transfer_human += delay
                day_vehicle_trips += transfer["rover_trip_count"] + transfer["station_trip_count"]
                day_station_trips += transfer["station_trip_count"]
                allocations = []
                for state, count in zip(new_fields, new_counts):
                    allocations.extend([state] * count)
                    if state.field_id not in old_ids:
                        state.deployment_count += 1
                new_ids = {state.field_id for state in allocations}
                changed = len(new_ids - old_ids)
                if changed:
                    total_field_transfers += changed
                    for state in states:
                        if state.field_id in old_ids and state.remaining_distance_mm > 0:
                            state.interruption_count += 1
                primary_id = new_fields[0].field_id if new_fields else ""
        used_batteries = min(battery_pool, battery_sessions)
        remaining_full = primary_spares + secondary_spares
        evening_depleted = max(0, battery_pool - remaining_full)
        overnight_capacity = 4 * (720 // 180)
        overnight_charged = min(evening_depleted, overnight_capacity)
        full_inventory = min(battery_pool, remaining_full + overnight_charged)
        if assigned < rover_count or day_waits:
            battery_shortfall_days += 1
        battery_handling = used_batteries * 2
        daily_human = (
            transport["loading_minutes"] * 2 + transport["unloading_minutes"] * 2
            + transport["driving_minutes"] * 2 + transport["station_handling_minutes"]
            + transfer_human + battery_handling + day_swaps * 3
        )
        total_human += daily_human
        max_daily_human = max(max_daily_human, daily_human)
        total_swaps += day_swaps
        total_waits += day_waits
        total_vehicle_trips += day_vehicle_trips
        total_station_trips += day_station_trips
        daily_results.append({
            "day_index": day,
            "selected_group_ids": [group_id] if group_changes == 0 else [group_id, current_group],
            "selected_field_ids": sorted(worked_fields),
            "rover_allocations": [
                {"field_id": field_id, "rover_count": allocation_peak[field_id]}
                for field_id in sorted(allocation_peak)
            ],
            "morning_full_batteries": morning_full_inventory,
            "evening_depleted_batteries": evening_depleted,
            "overnight_charged_batteries": overnight_charged,
            "deployment_minutes": deployment,
            "productive_minutes": productive_minutes_actual,
            "recovery_minutes": recovery,
            "processed_distance_mm": day_processed,
            "completed_field_ids": sorted(completed_today),
            "group_change_count": group_changes,
            "vehicle_trip_count": day_vehicle_trips,
            "station_trip_count": day_station_trips,
            "battery_swap_count": day_swaps,
            "battery_wait_minutes": day_waits,
            "human_work_minutes": daily_human,
        })
    processed_total = total_target - sum(state.remaining_distance_mm for state in states)
    completed_states = [state for state in states if state.remaining_distance_mm == 0]
    completed_area = sum(state.area_m2 for state in completed_states)
    completed = len(completed_states) == 19 and processed_total >= total_target
    estimated_days = len(daily_results) if completed else (ceil_div(total_target * max(1, len(daily_results)), processed_total) if processed_total else 0)
    bottlenecks: list[str] = ["FIELD_GEOMETRY_ESTIMATED", "FIELD_AREA_MAPPING_UNRESOLVED"]
    if configuration.daily_window_minutes < 480:
        bottlenecks.append("WORKDAY_TOO_SHORT")
    if not completed:
        bottlenecks.extend(("SPEED_INSUFFICIENT", "ROVER_COUNT_INSUFFICIENT"))
    if configuration.vehicle_rover_capacity < 10:
        bottlenecks.append("VEHICLE_CAPACITY")
    if configuration.operator_count == 1:
        bottlenecks.append("MANUAL_LOADING_TIME")
    if total_group_transfers:
        bottlenecks.append("GROUP_TRANSFER")
    if battery_shortfall_days:
        bottlenecks.extend(("BATTERY_POOL", "NO_MIDDAY_BATTERY_DELIVERY"))
    recommendations = [
        "MEASURE_ACTUAL_19_FIELD_AREAS", "RESOLVE_R4_TO_CURRENT_FIELD_MAPPING",
        "MEASURE_ROVER_LOADING_CAPACITY", "MEASURE_ROVER_OPERATING_SPEED",
        "MEASURE_WEED_POWER_CONSUMPTION", "PHYSICAL_FIELD_VALIDATION_REQUIRED",
    ]
    if not completed:
        recommendations.extend(("INCREASE_DAILY_WORK_WINDOW", "INCREASE_EFFECTIVE_SPEED", "INCREASE_WEED_ROVER_COUNT"))
    if battery_shortfall_days:
        recommendations.extend(("INCREASE_BATTERY_POOL", "INCREASE_CHARGER_COUNT", "CONSIDER_MIDDAY_BATTERY_SHUTTLE"))
    if total_field_transfers:
        recommendations.append("REDUCE_FIELD_TRANSFER_FREQUENCY")
    if configuration.policy != "ROAD_SIDE_BATCHED":
        recommendations.append("USE_ROAD_SIDE_BATCHED_OPERATION")
    if configuration.policy in ("TWO_FIELDS_EQUAL", "TWO_FIELDS_WEIGHTED", "FINISH_FIRST"):
        recommendations.append("ADD_SECOND_MOBILE_STATION_FOR_PARALLEL_FIELDS")
    field_results = []
    if include_details:
        for state in sorted(states, key=lambda item: item.field_id):
            processed = state.target_distance_mm - state.remaining_distance_mm
            status = "COMPLETED" if state.remaining_distance_mm == 0 else ("IN_PROGRESS" if processed else "WAITING")
            field_results.append({
                "field_id": state.field_id,
                "group_id": state.group_id,
                "area_m2": state.area_m2,
                "area_estimated": True,
                "target_distance_mm": state.target_distance_mm,
                "processed_distance_mm": processed,
                "remaining_distance_mm": state.remaining_distance_mm,
                "completion_basis_points": basis_points(processed, state.target_distance_mm),
                "status": status,
                "first_work_day": state.first_work_day,
                "completion_day": state.completion_day,
                "interruption_count": state.interruption_count,
                "deployment_count": state.deployment_count,
                "battery_wait_minutes": state.battery_wait_minutes,
            })
    return {
        "completed": completed,
        "completed_field_count": len(completed_states),
        "completed_area_m2": completed_area,
        "incomplete_area_m2": 27000 - completed_area,
        "processed_distance_mm": processed_total,
        "target_distance_mm": total_target,
        "completion_basis_points": basis_points(processed_total, total_target),
        "days_used": len(daily_results),
        "estimated_days_required": estimated_days,
        "field_transfer_count": total_field_transfers,
        "group_transfer_count": total_group_transfers,
        "vehicle_trip_count": total_vehicle_trips,
        "station_trip_count": total_station_trips,
        "battery_swap_count": total_swaps,
        "battery_wait_minutes": total_waits,
        "minimum_charged_inventory": minimum_inventory,
        "human_work_minutes": total_human,
        "maximum_daily_human_work_minutes": max_daily_human,
        "field_results": field_results,
        "daily_results": daily_results if include_details else [],
        "bottlenecks": _ordered_unique(bottlenecks, BOTTLENECK_ORDER),
        "recommendations": _ordered_unique(recommendations, RECOMMENDATION_ORDER),
    }


def required_speed(fields: list[dict[str, object]], configuration: Configuration) -> tuple[bool, int, str]:
    low = 100
    high = 10000
    high_configuration = Configuration(
        configuration.policy, "TARGET_10_DAY", high, configuration.daily_window_minutes,
        configuration.operator_count, configuration.vehicle_rover_capacity,
        configuration.battery_pool_count,
    )
    if not _simulate(fields, high_configuration, include_details=False)["completed"]:
        return False, 0, "No completing speed was found in the formal range."
    while low < high:
        middle = (low + high) // 2
        candidate = Configuration(
            configuration.policy, "TARGET_10_DAY", middle,
            configuration.daily_window_minutes, configuration.operator_count,
            configuration.vehicle_rover_capacity, configuration.battery_pool_count,
        )
        if _simulate(fields, candidate, include_details=False)["completed"]:
            high = middle
        else:
            low = middle + 1
    verified = Configuration(
        configuration.policy, "TARGET_10_DAY", low, configuration.daily_window_minutes,
        configuration.operator_count, configuration.vehicle_rover_capacity,
        configuration.battery_pool_count,
    )
    if not _simulate(fields, verified, include_details=False)["completed"]:
        raise MfwFailure("MFW_SCHEDULE_FAILED", "required_speed", "Required speed verification failed.", 4)
    return True, low, "Formal scheduler completion verified."


def required_rover_count(fields: list[dict[str, object]]) -> tuple[bool, int, str]:
    for rover_count in range(1, 61):
        configuration = Configuration("ROAD_SIDE_BATCHED", "CURRENT_STANDARD", 700, 480, 2, 10, ceil_div(rover_count * 2, 1))
        result = _simulate(
            fields, configuration, rover_count=rover_count,
            battery_pool_override=ceil_div(rover_count * 2, 1), include_details=False,
        )
        if result["completed"]:
            return True, rover_count, "Formal scheduler completion verified."
    return False, 0, "No completing rover count was found with four chargers."


def _configuration_document(
    configuration: Configuration, result: dict[str, object],
    speed_found: bool, speed_value: int,
) -> dict[str, object]:
    return {
        "configuration_id": configuration.configuration_id,
        "policy": configuration.policy,
        "speed_profile": configuration.speed_profile,
        "speed_mm_per_min": configuration.speed_mm_per_min,
        "daily_window_minutes": configuration.daily_window_minutes,
        "operator_count": configuration.operator_count,
        "vehicle_rover_capacity": configuration.vehicle_rover_capacity,
        "battery_pool_count": configuration.battery_pool_count,
        "completed": result["completed"],
        "completed_field_count": result["completed_field_count"],
        "completed_area_m2": result["completed_area_m2"],
        "incomplete_area_m2": result["incomplete_area_m2"],
        "processed_distance_mm": result["processed_distance_mm"],
        "target_distance_mm": result["target_distance_mm"],
        "completion_basis_points": result["completion_basis_points"],
        "days_used": result["days_used"],
        "estimated_days_required": result["estimated_days_required"],
        "required_speed_found": speed_found,
        "required_speed_mm_per_min": speed_value,
        "field_transfer_count": result["field_transfer_count"],
        "group_transfer_count": result["group_transfer_count"],
        "vehicle_trip_count": result["vehicle_trip_count"],
        "station_trip_count": result["station_trip_count"],
        "battery_swap_count": result["battery_swap_count"],
        "battery_wait_minutes": result["battery_wait_minutes"],
        "minimum_charged_inventory": result["minimum_charged_inventory"],
        "human_work_minutes": result["human_work_minutes"],
        "maximum_daily_human_work_minutes": result["maximum_daily_human_work_minutes"],
        "field_results": result["field_results"],
        "daily_results": result["daily_results"],
        "bottlenecks": result["bottlenecks"],
        "recommendations": result["recommendations"],
    }


def _selection_documents(configurations: list[dict[str, object]], rover_found: bool, rover_count: int) -> list[dict[str, object]]:
    best = min(configurations, key=lambda item: (
        -int(item["completed_field_count"]), -int(item["completed_area_m2"]),
        -int(item["processed_distance_mm"]), int(item["battery_wait_minutes"]),
        int(item["human_work_minutes"]), int(item["field_transfer_count"]),
        str(item["configuration_id"]),
    ))
    completed = [item for item in configurations if item["completed"]]
    if completed:
        human = min(completed, key=lambda item: (
            int(item["human_work_minutes"]), int(item["field_transfer_count"]),
            int(item["battery_wait_minutes"]), str(item["configuration_id"]),
        ))
    else:
        human = min(configurations, key=lambda item: (
            int(item["incomplete_area_m2"]), int(item["human_work_minutes"]),
            str(item["configuration_id"]),
        ))
    transfer = min(configurations, key=lambda item: (
        int(item["group_transfer_count"]), int(item["field_transfer_count"]),
        -int(item["completed_area_m2"]), str(item["configuration_id"]),
    ))
    feasibility = min(configurations, key=lambda item: (
        0 if item["completed"] else 1,
        int(item["required_speed_mm_per_min"]) if item["required_speed_found"] else 10001,
        rover_count if rover_found else 61,
        int(item["human_work_minutes"]), str(item["configuration_id"]),
    ))
    return [
        {"selection_id": "BEST_COMPLETION", "configuration_id": best["configuration_id"]},
        {"selection_id": "MINIMUM_HUMAN_TIME", "configuration_id": human["configuration_id"]},
        {"selection_id": "MINIMUM_TRANSFER", "configuration_id": transfer["configuration_id"]},
        {"selection_id": "BEST_10_DAY_FEASIBILITY", "configuration_id": feasibility["configuration_id"]},
    ]


def safety_document() -> dict[str, object]:
    return {
        "offline_only": True,
        "network_access_performed": False,
        "random_used": False,
        "monte_carlo_used": False,
        "weather_probability_claimed": False,
        "gpio_access_performed": False,
        "serial_access_performed": False,
        "hardware_output_performed": False,
        "motor_control_performed": False,
        "pto_control_performed": False,
        "charging_control_performed": False,
        "bms_communication_performed": False,
        "rover_communication_performed": False,
        "actual_assignment_performed": False,
        "actual_arm_performed": False,
        "autonomous_interfield_transfer_performed": False,
        "autonomous_public_road_crossing_performed": False,
        "rover_carried_station_transfer_performed": False,
        "field_operation_approved": False,
        "unattended_operation_approved": False,
        "physical_estop_independent": True,
        "repository_modified": False,
    }


def _diagnostic(
    severity: str, code: str, component: str, message: str,
    configuration_id: str = "", field_id: str = "", day_index: int = 0,
) -> dict[str, object]:
    return {
        "severity": severity, "code": code, "component": component,
        "configuration_id": configuration_id, "field_id": field_id,
        "day_index": day_index, "message": message,
    }


def _sort_diagnostics(items: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(items, key=lambda item: (
        str(item["component"]), str(item["code"]), str(item["configuration_id"]),
        str(item["field_id"]), int(item["day_index"]), str(item["message"]),
    ))


def build_report(
    repository_root: Path, plan: dict[str, object],
    st008_loader: Callable[[Path], ModuleType] = load_st008,
    simulator: Callable[..., dict[str, object]] = _simulate,
) -> SchedulerReport:
    st008 = st008_loader(repository_root)
    operational = plan["operational_field_model"]
    assert isinstance(operational, dict)
    fields = operational["fields"]
    assert isinstance(fields, list)
    distances = [planning_distance_mm(int(field["area_m2"]), st008) for field in fields]
    if distances.count(5451000) != 1 or distances.count(5447167) != 18 or sum(distances) != 103500006:
        raise MfwFailure("MFW_DISTANCE_CALCULATION_INVALID", "distance", "Derived planning distance is invalid.", 4)
    speed_cache: dict[tuple[str, int, int, int, int], tuple[bool, int, str]] = {}
    configurations = sorted(configuration_generator(), key=lambda item: item.configuration_id)
    if len(configurations) != 1215:
        raise MfwFailure("MFW_SEARCH_COUNT_MISMATCH", "search", "Configuration count is invalid.", 4)
    configuration_results: list[dict[str, object]] = []
    required_speed_results: list[dict[str, object]] = []
    for configuration in configurations:
        key = (
            configuration.policy, configuration.daily_window_minutes,
            configuration.operator_count, configuration.vehicle_rover_capacity,
            configuration.battery_pool_count,
        )
        if key not in speed_cache:
            speed_cache[key] = required_speed(fields, configuration)
            found, speed_value, reason = speed_cache[key]
            required_speed_results.append({
                "policy": configuration.policy,
                "daily_window_minutes": configuration.daily_window_minutes,
                "operator_count": configuration.operator_count,
                "vehicle_rover_capacity": configuration.vehicle_rover_capacity,
                "battery_pool_count": configuration.battery_pool_count,
                "required_speed_found": found,
                "required_speed_mm_per_min": speed_value,
                "reason": reason,
            })
        found, speed_value, unused_reason = speed_cache[key]
        result = simulator(fields, configuration, include_details=True)
        configuration_results.append(_configuration_document(configuration, result, found, speed_value))
    if len(speed_cache) != 405:
        raise MfwFailure("MFW_SEARCH_COUNT_MISMATCH", "search", "Required-speed search count is invalid.", 4)
    rover_found, rover_count, rover_reason = required_rover_count(fields)
    selected = _selection_documents(configuration_results, rover_found, rover_count)
    by_id = {str(item["configuration_id"]): item for item in configuration_results}
    best = by_id[str(selected[0]["configuration_id"])]
    if best["completed"]:
        classification = "FEASIBLE"
    elif int(best["completion_basis_points"]) >= 9000:
        classification = "MARGINAL"
    else:
        classification = "INFEASIBLE"
    diagnostics = [
        _diagnostic("WARNING", "MFW_FIELD_MAPPING_UNRESOLVED", "area", "R4 parcels are not mapped to current operational fields."),
        _diagnostic("WARNING", "MFW_GEOMETRY_ESTIMATED", "field", "Operational field areas and geometry require measurement."),
    ]
    if not best["completed"]:
        diagnostics.append(_diagnostic(
            "WARNING", "MFW_TARGET_INCOMPLETE", "scheduler",
            "The ten-work-day full-pass target was not completed by the best configuration.",
            str(best["configuration_id"]),
        ))
    if not rover_found:
        diagnostics.append(_diagnostic("WARNING", "MFW_REQUIRED_ROVER_COUNT_NOT_FOUND", "required_rover", rover_reason))
    if not bool(best["required_speed_found"]):
        diagnostics.append(_diagnostic("WARNING", "MFW_REQUIRED_SPEED_NOT_FOUND", "required_speed", "No formal required speed was found."))
    if int(best["battery_wait_minutes"]):
        diagnostics.append(_diagnostic("WARNING", "MFW_BATTERY_SHORTFALL", "battery", "The best configuration includes battery wait.", str(best["configuration_id"])))
    normalized_fields = [
        {
            "field_id": field["field_id"], "group_id": field["group_id"],
            "area_m2": field["area_m2"], "target_distance_mm": distance,
        }
        for field, distance in zip(fields, distances)
    ]
    sorted_diagnostics = _sort_diagnostics(diagnostics)
    state = {
        "normalized_plan": plan,
        "normalized_field_definitions": normalized_fields,
        "normalized_group_definitions": operational["groups"],
        "simulation_matrix": plan["simulation_matrix"],
        "configuration_results": configuration_results,
        "selected_results": selected,
        "diagnostics": sorted_diagnostics,
    }
    report: dict[str, object] = {
        "report_version": REPORT_VERSION,
        "phase": PHASE,
        "plan_id": plan["plan_id"],
        "result": "PASS",
        "area_reference": plan["area_reference"],
        "operational_field_model": {
            "field_model_id": operational["field_model_id"],
            "field_count": operational["field_count"],
            "total_area_m2": operational["total_area_m2"],
            "area_source": operational["area_source"],
            "parcel_mapping_status": operational["parcel_mapping_status"],
            "field_area_estimated": True,
            "field_geometry_estimated": True,
            "actual_field_measurement_required": True,
            "area_level_target_distance_mm": 103500000,
            "field_level_target_distance_mm": 103500006,
            "groups": operational["groups"],
            "fields": normalized_fields,
        },
        "fleet_model": {
            "weed_rover_count": 12,
            "maximum_simultaneous_fields": 2,
            "manual_rover_transfer": True,
            "rover_states": list(ROVER_STATES),
        },
        "logistics_model": {
            "vehicle_count": 1,
            "operator_count_options": list(OPERATOR_OPTIONS),
            "vehicle_rover_capacity_options": list(VEHICLE_CAPACITIES),
            "vehicle_capacity_provisional_upper_bound": True,
            "manual_station_transfer": True,
            "station_requires_dedicated_trip": True,
            "maximum_group_changes_per_day": 1,
            "morning_deployment_required": True,
            "daily_recovery_required": True,
        },
        "battery_model": {
            "battery_id": "BATTERY-DEMO-LIFEPO4-12V-10AH",
            "battery_pool_options": list(BATTERY_POOLS),
            "charger_count": 4,
            "battery_runtime_minutes": 150,
            "battery_swap_minutes": 3,
            "charge_minutes": 180,
            "overnight_charge_window_minutes": 720,
            "maximum_overnight_sessions": 16,
            "service_windows": ["MORNING_DEPLOYMENT", "EVENING_RECOVERY"],
            "midday_battery_shuttle_enabled": False,
            "state_carried_across_days": True,
            "daily_battery_reset": False,
            "mobile_charging_station_count": 1,
        },
        "search_space": {
            "allocation_policy_count": 5,
            "speed_profile_count": 3,
            "daily_window_count": 3,
            "operator_count": 3,
            "vehicle_capacity_count": 3,
            "battery_pool_count": 3,
            "raw_configuration_count": 1215,
            "all_configurations_evaluated": True,
            "random_sampling": False,
            "automatic_range_reduction": False,
        },
        "configuration_results": configuration_results,
        "selected_results": selected,
        "required_capacity": {
            "required_speed_is_design_target": True,
            "actual_speed_measurement_required": True,
            "required_speed_results": required_speed_results,
            "representative_policy": "ROAD_SIDE_BATCHED",
            "representative_speed_mm_per_min": 700,
            "representative_daily_window_minutes": 480,
            "representative_operator_count": 2,
            "representative_vehicle_capacity": 10,
            "required_rover_count_found": rover_found,
            "required_rover_count": rover_count,
            "required_rover_reason": rover_reason,
        },
        "feasibility": {
            "target_id": "FULL_PASS_ALL_19_WITHIN_10_WORK_DAYS",
            "target_status": "COMPLETED" if best["completed"] else "INCOMPLETE",
            "classification": classification,
            "best_configuration_id": best["configuration_id"],
            "required_speed_is_design_target": True,
            "actual_speed_measurement_required": True,
            "actual_field_measurement_required": True,
        },
        "safety": safety_document(),
        "diagnostics": sorted_diagnostics,
        "canonical_plan_sha256": sha256_canonical(plan),
        "canonical_schedule_state_sha256": sha256_canonical(state),
        "exit_code": 0,
    }
    return SchedulerReport(report, 0)


def render_json_report(report: SchedulerReport) -> str:
    return json.dumps(report.document, ensure_ascii=True, indent=2, separators=(",", ": ")) + "\n"


def _text_value(value: object) -> str:
    return str(value).lower() if type(value) is bool else str(value)


def _percent(bp: int) -> str:
    return f"{bp // 100}.{(bp % 100) // 10}"


def render_text_report(report: SchedulerReport) -> str:
    document = report.document
    selected = document["selected_results"]
    configurations = document["configuration_results"]
    by_id = {item["configuration_id"]: item for item in configurations}
    best_id = selected[0]["configuration_id"] if selected else ""
    best = by_id.get(best_id, {})
    area = document["area_reference"]
    operational = document["operational_field_model"]
    required = document["required_capacity"]
    feasibility = document["feasibility"]
    bottlenecks = best.get("bottlenecks", ["NONE"])
    speed_values = [
        item["required_speed_mm_per_min"] for item in required.get("required_speed_results", [])
        if item["required_speed_found"]
    ]
    values = (
        ("report_version", document["report_version"]),
        ("phase", document["phase"]),
        ("plan_id", document["plan_id"]),
        ("result", document["result"]),
        ("operational_field_count", operational.get("field_count", 0)),
        ("operational_total_area_m2", operational.get("total_area_m2", 0)),
        ("r4_reference_parcel_count", area.get("r4_parcel_count", 0)),
        ("r4_reference_total_area_m2", area.get("r4_total_area_m2", 0)),
        ("r4_rice_area_m2", area.get("r4_rice_area_m2", 0)),
        ("parcel_mapping_status", area.get("mapping_status", "UNRESOLVED")),
        ("planning_target_distance_mm", operational.get("field_level_target_distance_mm", 0)),
        ("configuration_count", len(configurations)),
        ("best_configuration_id", best_id),
        ("best_completed", best.get("completed", False)),
        ("best_completed_field_count", best.get("completed_field_count", 0)),
        ("best_completed_area_m2", best.get("completed_area_m2", 0)),
        ("best_incomplete_area_m2", best.get("incomplete_area_m2", 27000)),
        ("best_completion_percent", _percent(int(best.get("completion_basis_points", 0)))),
        ("best_days_used", best.get("days_used", 0)),
        ("best_policy", best.get("policy", "")),
        ("best_speed_mm_per_min", best.get("speed_mm_per_min", 0)),
        ("best_daily_window_minutes", best.get("daily_window_minutes", 0)),
        ("best_operator_count", best.get("operator_count", 0)),
        ("best_vehicle_capacity", best.get("vehicle_rover_capacity", 0)),
        ("best_battery_pool_count", best.get("battery_pool_count", 0)),
        ("best_group_transfer_count", best.get("group_transfer_count", 0)),
        ("best_vehicle_trip_count", best.get("vehicle_trip_count", 0)),
        ("best_battery_wait_minutes", best.get("battery_wait_minutes", 0)),
        ("best_human_work_minutes", best.get("human_work_minutes", 0)),
        ("required_speed_mm_per_min", min(speed_values) if speed_values else 0),
        ("required_rover_count", required.get("required_rover_count", 0)),
        ("feasibility_classification", feasibility.get("classification", "NOT_EVALUATED")),
        ("primary_bottleneck", bottlenecks[0] if bottlenecks else "NONE"),
        ("canonical_plan_sha256", document["canonical_plan_sha256"]),
        ("canonical_schedule_state_sha256", document["canonical_schedule_state_sha256"]),
        ("offline_only", document["safety"]["offline_only"]),
        ("autonomous_public_road_crossing_performed", document["safety"]["autonomous_public_road_crossing_performed"]),
        ("field_operation_approved", document["safety"]["field_operation_approved"]),
        ("unattended_operation_approved", document["safety"]["unattended_operation_approved"]),
        ("diagnostic_count", len(document["diagnostics"])),
        ("exit_code", document["exit_code"]),
    )
    return "\n".join(f"{key}={_text_value(value)}" for key, value in values) + "\n"


def write_report(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _failure_report(failure: MfwFailure) -> SchedulerReport:
    document: dict[str, object] = {
        "report_version": REPORT_VERSION, "phase": PHASE, "plan_id": PLAN_ID,
        "result": "FAIL", "area_reference": {}, "operational_field_model": {},
        "fleet_model": {}, "logistics_model": {}, "battery_model": {},
        "search_space": {}, "configuration_results": [], "selected_results": [],
        "required_capacity": {}, "feasibility": {}, "safety": safety_document(),
        "diagnostics": _sort_diagnostics([_diagnostic("ERROR", failure.code, failure.component, failure.message)]),
        "canonical_plan_sha256": "0" * 64,
        "canonical_schedule_state_sha256": "0" * 64,
        "exit_code": failure.exit_code,
    }
    return SchedulerReport(document, failure.exit_code)


def run_scheduler(
    arguments: SchedulerArguments,
    builder: Callable[[Path, dict[str, object]], SchedulerReport] = build_report,
    write_reports: bool = True,
) -> SchedulerReport:
    try:
        validate_arguments(arguments)
        plan = validate_plan(load_strict_json(arguments.plan))
        report = builder(arguments.repository_root, plan)
        if write_reports:
            json_text = render_json_report(report)
            text_text = render_text_report(report)
            write_report(arguments.json_report, json_text)
            write_report(arguments.text_report, text_text)
        return report
    except MfwFailure as failure:
        return _failure_report(failure)
    except OSError:
        return _failure_report(MfwFailure("MFW_REPORT_WRITE_FAILED", "report", "Report could not be written.", 7))
    except Exception:
        return _failure_report(MfwFailure("MFW_INTERNAL_ERROR", "internal", "Unexpected internal failure.", 7))


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_arguments(argv)
    except MfwFailure as failure:
        report = _failure_report(failure)
        sys.stdout.write(render_text_report(report))
        return report.exit_code
    report = run_scheduler(arguments)
    sys.stdout.write(render_text_report(report))
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
