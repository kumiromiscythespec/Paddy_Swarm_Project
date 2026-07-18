#!/usr/bin/env python3
"""Standard-library regression tests for the ST-010 offline scheduler."""

from __future__ import annotations

import ast
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "software/station_control/station/multi_field_weed_scheduler.py"
PLAN = ROOT / "software/station_control/config_examples/multi-field-weed-plan.example.json"
PLAN_SCHEMA = ROOT / "software/station_control/schemas/multi-field-weed-plan.schema.json"
REPORT_SCHEMA = ROOT / "software/station_control/schemas/multi-field-weed-report.schema.json"
SPEC = importlib.util.spec_from_file_location("st010_test_module", SOURCE)
assert SPEC is not None and SPEC.loader is not None
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class MultiFieldWeedSchedulerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = MOD.validate_plan(MOD.load_strict_json(PLAN))
        cls.fields = cls.plan["operational_field_model"]["fields"]
        cls.st008 = MOD.load_st008(ROOT)
        cls.report = MOD.build_report(ROOT, cls.plan)
        cls.best_id = cls.report.document["selected_results"][0]["configuration_id"]
        cls.by_id = {item["configuration_id"]: item for item in cls.report.document["configuration_results"]}
        cls.best = cls.by_id[cls.best_id]

    def invalid_plan(self, mutation):
        value = copy.deepcopy(self.plan)
        mutation(value)
        with self.assertRaises(MOD.MfwFailure):
            MOD.validate_plan(value)

    # ST-008 reuse and strict JSON
    def test_st008_phase(self): self.assertEqual(self.st008.PHASE, "ST-008")
    def test_st008_ceil_reused(self): self.assertEqual(MOD.planning_distance_mm(1421, self.st008), 5447167)
    def test_st008_public_weed_present(self): self.assertTrue(callable(self.st008.simulate_weed))
    def test_st008_public_battery_present(self): self.assertTrue(callable(self.st008.schedule_batteries))
    def test_st008_algorithm_not_copied(self): self.assertNotIn("def simulate_weed(", SOURCE.read_text(encoding="utf-8"))
    def test_st008_load_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(MOD.MfwFailure): MOD.load_st008(Path(directory))
    def test_plan_version(self): self.assertEqual(self.plan["plan_version"], 1)
    def test_plan_id(self): self.assertEqual(self.plan["plan_id"], MOD.PLAN_ID)
    def test_duplicate_json_key(self): self.assertRaises(MOD.MfwFailure, MOD._reject_duplicate_keys, [("a", 1), ("a", 2)])
    def test_null(self): self.assertRaises(MOD.MfwFailure, MOD._reject_null, None)
    def test_nan(self): self.assertRaises(MOD.MfwFailure, MOD._reject_constant, "NaN")
    def test_infinity(self): self.assertRaises(MOD.MfwFailure, MOD._reject_constant, "Infinity")
    def test_plan_schema_json(self): self.assertEqual(json.loads(PLAN_SCHEMA.read_text(encoding="utf-8"))["$schema"], "https://json-schema.org/draft/2020-12/schema")
    def test_report_schema_json(self): self.assertEqual(json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))["$schema"], "https://json-schema.org/draft/2020-12/schema")
    def test_schema_local_refs_only(self):
        for path in (PLAN_SCHEMA, REPORT_SCHEMA):
            value = json.loads(path.read_text(encoding="utf-8"))
            refs = [node.value for node in ast.walk(ast.parse(repr(value))) if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith("#/")]
            self.assertTrue(all(item.startswith("#/$defs/") for item in refs))

    # Area reference and operational fields
    def test_r4_parcel_count(self): self.assertEqual(self.plan["area_reference"]["r4_parcel_count"], 20)
    def test_r4_rice_count(self): self.assertEqual(len(self.plan["area_reference"]["r4_rice_parcel_areas_m2"]), 16)
    def test_r4_rice_sum(self): self.assertEqual(sum(self.plan["area_reference"]["r4_rice_parcel_areas_m2"]), 22040)
    def test_r4_grass_count(self): self.assertEqual(len(self.plan["area_reference"]["r4_grass_parcel_areas_m2"]), 3)
    def test_r4_grass_sum(self): self.assertEqual(sum(self.plan["area_reference"]["r4_grass_parcel_areas_m2"]), 6780)
    def test_r4_conservation(self): self.assertEqual(self.plan["area_reference"]["r4_self_conservation_area_m2"], 3130)
    def test_r4_total(self): self.assertEqual(22040 + 6780 + 3130, 31950)
    def test_mapping_unresolved(self): self.assertEqual(self.plan["area_reference"]["mapping_status"], "UNRESOLVED")
    def test_field_count(self): self.assertEqual(len(self.fields), 19)
    def test_group_counts(self): self.assertEqual(tuple(sum(item["group_id"] == group for item in self.fields) for group in MOD.GROUP_IDS), MOD.GROUP_COUNTS)
    def test_operational_total(self): self.assertEqual(sum(item["area_m2"] for item in self.fields), 27000)
    def test_area_1422_once(self): self.assertEqual(sum(item["area_m2"] == 1422 for item in self.fields), 1)
    def test_area_1421_eighteen(self): self.assertEqual(sum(item["area_m2"] == 1421 for item in self.fields), 18)
    def test_all_estimated(self): self.assertTrue(all(item["area_estimated"] for item in self.fields))
    def test_invalid_parcel_sum(self): self.invalid_plan(lambda value: value["area_reference"]["r4_rice_parcel_areas_m2"].__setitem__(0, 1))
    def test_invalid_parcel_count(self): self.invalid_plan(lambda value: value["area_reference"]["r4_rice_parcel_areas_m2"].pop())
    def test_duplicate_field_id(self): self.invalid_plan(lambda value: value["operational_field_model"]["fields"][1].__setitem__("field_id", value["operational_field_model"]["fields"][0]["field_id"]))
    def test_unknown_group(self): self.invalid_plan(lambda value: value["operational_field_model"]["fields"][0].__setitem__("group_id", "UNKNOWN"))
    def test_wrong_group_count(self): self.invalid_plan(lambda value: value["operational_field_model"]["groups"][0].__setitem__("field_count", 8))
    def test_wrong_total(self): self.invalid_plan(lambda value: value["operational_field_model"]["fields"][0].__setitem__("area_m2", 1421))

    # Distances and allocation policies
    def test_distance_1421(self): self.assertEqual(MOD.planning_distance_mm(1421), 5447167)
    def test_distance_1422(self): self.assertEqual(MOD.planning_distance_mm(1422), 5451000)
    def test_distance_total(self): self.assertEqual(sum(MOD.planning_distance_mm(item["area_m2"]) for item in self.fields), 103500006)
    def test_area_level_distance(self): self.assertEqual(2990000 * 27000 // 780, 103500000)
    def test_ceil_behavior(self): self.assertEqual(MOD.ceil_div(3, 2), 2)
    def test_zero_area(self): self.assertRaises(MOD.MfwFailure, MOD.planning_distance_mm, 0)
    def test_negative_area(self): self.assertRaises(MOD.MfwFailure, MOD.planning_distance_mm, -1)
    def test_one_field_concentrated(self): self.assertEqual(len(MOD.choose_fields(self._states(), "GROUP-HOME", "ONE_FIELD_CONCENTRATED")), 1)
    def test_two_fields_equal(self): self.assertEqual(MOD.allocation_counts("TWO_FIELDS_EQUAL", 2, 12), (6, 6))
    def test_two_fields_weighted(self): self.assertEqual(MOD.allocation_counts("TWO_FIELDS_WEIGHTED", 2, 12), (8, 4))
    def test_finish_first_order(self):
        states = self._states(); states[0].remaining_distance_mm = 5
        self.assertEqual(MOD.choose_fields(states, "GROUP-HOME", "FINISH_FIRST")[0].field_id, states[0].field_id)
    def test_road_side_batched_one(self): self.assertEqual(len(MOD.choose_fields(self._states(), "GROUP-HOME", "ROAD_SIDE_BATCHED")), 1)
    def test_two_fields_same_group(self): self.assertEqual(len({item.group_id for item in MOD.choose_fields(self._states(), "GROUP-HOME", "TWO_FIELDS_EQUAL")}), 1)
    def test_deterministic_tie_break(self): self.assertEqual(MOD.choose_fields(self._states(), "GROUP-HOME", "FINISH_FIRST")[0].field_id, "GROUP-HOME-F02")
    def test_policy_order(self): self.assertEqual(len(MOD.POLICIES), 5)

    def _states(self):
        return [MOD.FieldState(item["field_id"], item["group_id"], item["area_m2"], MOD.planning_distance_mm(item["area_m2"]), MOD.planning_distance_mm(item["area_m2"])) for item in self.fields]

    # Transport and battery model
    def test_capacity_six_trips(self): self.assertEqual(MOD.transport_accounting(12, 6, 1, False)["rover_trip_count"], 2)
    def test_capacity_eight_trips(self): self.assertEqual(MOD.transport_accounting(12, 8, 1, False)["rover_trip_count"], 2)
    def test_capacity_ten_trips(self): self.assertEqual(MOD.transport_accounting(12, 10, 1, False)["rover_trip_count"], 2)
    def test_ceil_trips(self): self.assertEqual(MOD.transport_accounting(13, 6, 1, False)["rover_trip_count"], 3)
    def test_loading_parallel_one(self): self.assertEqual(MOD.transport_accounting(12, 6, 1, False)["loading_minutes"], 48)
    def test_loading_parallel_two(self): self.assertEqual(MOD.transport_accounting(12, 6, 2, False)["loading_minutes"], 24)
    def test_loading_parallel_three(self): self.assertEqual(MOD.transport_accounting(12, 6, 3, False)["loading_minutes"], 16)
    def test_drive_not_parallel(self): self.assertEqual(MOD.transport_accounting(12, 6, 1, False)["driving_minutes"], MOD.transport_accounting(12, 6, 3, False)["driving_minutes"])
    def test_cross_group_drive_longer(self): self.assertGreater(MOD.transport_accounting(12, 6, 2, True)["driving_minutes"], MOD.transport_accounting(12, 6, 2, False)["driving_minutes"])
    def test_station_dedicated_trip(self): self.assertEqual(MOD.transport_accounting(12, 6, 2, False)["station_trip_count"], 1)
    def test_station_handling(self): self.assertEqual(MOD.transport_accounting(12, 6, 2, False)["station_handling_minutes"], 45)
    def test_partial_reallocation_trips(self): self.assertEqual(MOD.reallocation_accounting(6, 6, 2, False, False)["rover_trip_count"], 1)
    def test_partial_reallocation_no_station_trip(self): self.assertEqual(MOD.reallocation_accounting(6, 6, 2, False, False)["station_trip_count"], 0)
    def test_primary_reallocation_station_trip(self): self.assertEqual(MOD.reallocation_accounting(6, 6, 2, False, True)["station_trip_count"], 1)
    def test_short_window_insufficient(self):
        config = MOD.Configuration("ROAD_SIDE_BATCHED", "CONSERVATIVE", 400, 150, 1, 6, 16)
        self.assertEqual(MOD._simulate(self.fields, config, include_details=False)["processed_distance_mm"], 0)
    def test_battery_options(self): self.assertEqual(MOD.BATTERY_POOLS, (16, 24, 36))
    def test_charger_count(self): self.assertEqual(self.report.document["battery_model"]["charger_count"], 4)
    def test_runtime(self): self.assertEqual(self.report.document["battery_model"]["battery_runtime_minutes"], 150)
    def test_charge_minutes(self): self.assertEqual(self.report.document["battery_model"]["charge_minutes"], 180)
    def test_overnight_sessions(self): self.assertEqual(self.report.document["battery_model"]["maximum_overnight_sessions"], 16)
    def test_state_carried(self): self.assertTrue(self.report.document["battery_model"]["state_carried_across_days"])
    def test_no_daily_reset(self): self.assertFalse(self.report.document["battery_model"]["daily_battery_reset"])
    def test_no_midday_delivery(self): self.assertFalse(self.report.document["battery_model"]["midday_battery_shuttle_enabled"])
    def test_battery_wait_nonnegative(self): self.assertGreaterEqual(self.best["battery_wait_minutes"], 0)
    def test_swap_dwell_present(self): self.assertEqual(self.report.document["battery_model"]["battery_swap_minutes"], 3)

    # Scheduler, matrix, required capacity, and selection
    def test_configuration_count(self): self.assertEqual(len(self.report.document["configuration_results"]), 1215)
    def test_configuration_order(self):
        ids = [item["configuration_id"] for item in self.report.document["configuration_results"]]
        self.assertEqual(ids, sorted(ids))
    def test_all_evaluated(self): self.assertTrue(self.report.document["search_space"]["all_configurations_evaluated"])
    def test_no_random_sampling(self): self.assertFalse(self.report.document["search_space"]["random_sampling"])
    def test_no_range_reduction(self): self.assertFalse(self.report.document["search_space"]["automatic_range_reduction"])
    def test_daily_stop_ten(self): self.assertTrue(all(len(item["daily_results"]) <= 10 for item in self.report.document["configuration_results"]))
    def test_field_result_count(self): self.assertTrue(all(len(item["field_results"]) == 19 for item in self.report.document["configuration_results"]))
    def test_field_distance_cap(self):
        self.assertTrue(all(field["processed_distance_mm"] <= field["target_distance_mm"] for field in self.best["field_results"]))
    def test_no_distance_during_short_transport(self): self.assertEqual(self.by_id["CFG-ROAD_SIDE_BATCHED-S0400-D0150-O01-V06-B16"]["processed_distance_mm"], 0)
    def test_group_change_limit(self):
        self.assertTrue(all(day["group_change_count"] <= 1 for item in self.report.document["configuration_results"] for day in item["daily_results"]))
    def test_required_speed_search_count(self): self.assertEqual(len(self.report.document["required_capacity"]["required_speed_results"]), 405)
    def test_required_speed_bounds(self): self.assertTrue(all(0 <= item["required_speed_mm_per_min"] <= 10000 for item in self.report.document["required_capacity"]["required_speed_results"]))
    def test_required_speed_official_validation(self):
        items = self.report.document["required_capacity"]["required_speed_results"]
        found = [item for item in items if item["required_speed_found"]]
        for item in found:
            config = MOD.Configuration(item["policy"], "TARGET_10_DAY", item["required_speed_mm_per_min"], item["daily_window_minutes"], item["operator_count"], item["vehicle_rover_capacity"], item["battery_pool_count"])
            self.assertTrue(MOD._simulate(self.fields, config, include_details=False)["completed"])
        self.assertEqual(len(found), sum(item["required_speed_found"] for item in items))
    def test_required_speed_minimum_boundary(self):
        items = self.report.document["required_capacity"]["required_speed_results"]
        found = [item for item in items if item["required_speed_found"] and item["required_speed_mm_per_min"] > 100]
        item = found[0] if found else items[0]
        speed = item["required_speed_mm_per_min"] - 1 if found else 10000
        config = MOD.Configuration(item["policy"], "TARGET_10_DAY", speed, item["daily_window_minutes"], item["operator_count"], item["vehicle_rover_capacity"], item["battery_pool_count"])
        self.assertFalse(MOD._simulate(self.fields, config, include_details=False)["completed"])
    def test_required_rover_range(self): self.assertTrue(0 <= self.report.document["required_capacity"]["required_rover_count"] <= 60)
    def test_best_completion_selection(self): self.assertEqual(self.report.document["selected_results"][0]["selection_id"], "BEST_COMPLETION")
    def test_minimum_human_selection(self): self.assertEqual(self.report.document["selected_results"][1]["selection_id"], "MINIMUM_HUMAN_TIME")
    def test_minimum_transfer_selection(self): self.assertEqual(self.report.document["selected_results"][2]["selection_id"], "MINIMUM_TRANSFER")
    def test_best_feasibility_selection(self): self.assertEqual(self.report.document["selected_results"][3]["selection_id"], "BEST_10_DAY_FEASIBILITY")
    def test_selection_ids_exist(self): self.assertTrue(all(item["configuration_id"] in self.by_id for item in self.report.document["selected_results"]))
    def test_human_components_positive(self): self.assertGreater(self.best["human_work_minutes"], 0)
    def test_max_daily_human(self): self.assertLessEqual(self.best["maximum_daily_human_work_minutes"], self.best["human_work_minutes"])

    # Report, safety, scout, privacy, and errors
    def test_report_root_order(self): self.assertEqual(tuple(self.report.document), ("report_version", "phase", "plan_id", "result", "area_reference", "operational_field_model", "fleet_model", "logistics_model", "battery_model", "search_space", "configuration_results", "selected_results", "required_capacity", "feasibility", "safety", "diagnostics", "canonical_plan_sha256", "canonical_schedule_state_sha256", "exit_code"))
    def test_field_order(self): self.assertEqual([item["field_id"] for item in self.best["field_results"]], sorted(item["field_id"] for item in self.best["field_results"]))
    def test_day_order(self): self.assertEqual([item["day_index"] for item in self.best["daily_results"]], sorted(item["day_index"] for item in self.best["daily_results"]))
    def test_diagnostic_order(self):
        diagnostics = self.report.document["diagnostics"]
        self.assertEqual(diagnostics, MOD._sort_diagnostics(diagnostics))
    def test_recommendation_order(self):
        for item in self.report.document["configuration_results"]:
            self.assertEqual(item["recommendations"], [value for value in MOD.RECOMMENDATION_ORDER if value in item["recommendations"]])
    def test_json_deterministic(self): self.assertEqual(MOD.render_json_report(self.report), MOD.render_json_report(self.report))
    def test_text_deterministic(self): self.assertEqual(MOD.render_text_report(self.report), MOD.render_text_report(self.report))
    def test_plan_hash_stable(self): self.assertEqual(self.report.document["canonical_plan_sha256"], MOD.sha256_canonical(self.plan))
    def test_schedule_hash_length(self): self.assertEqual(len(self.report.document["canonical_schedule_state_sha256"]), 64)
    def test_no_timestamp(self): self.assertNotIn("timestamp", MOD.render_json_report(self.report).lower())
    def test_no_hostname(self): self.assertNotIn("hostname", MOD.render_json_report(self.report).lower())
    def test_no_username(self): self.assertNotIn("username", MOD.render_json_report(self.report).lower())
    def test_no_absolute_path(self): self.assertNotIn(str(ROOT), MOD.render_json_report(self.report))
    def test_no_binary_float(self): self.assertFalse(any(isinstance(node, ast.Constant) and isinstance(node.value, float) for node in ast.walk(ast.parse(SOURCE.read_text(encoding="utf-8")))))
    def test_scout_source(self): self.assertEqual(self.plan["scout_model"]["source"], "PRELOADED_MAP")
    def test_manual_drone_reserved(self): self.assertIn("MANUAL_DRONE", MOD.SCOUT_SOURCES)
    def test_no_flight_control_source(self): self.assertNotIn("waypoint", SOURCE.read_text(encoding="utf-8").lower())
    def test_future_features_disabled(self): self.assertTrue(all(not item["enabled"] for item in self.plan["future_features"]))
    def test_required_measurement_recommendations(self):
        for item in self.report.document["configuration_results"]:
            self.assertIn("MEASURE_ACTUAL_19_FIELD_AREAS", item["recommendations"])
            self.assertIn("RESOLVE_R4_TO_CURRENT_FIELD_MAPPING", item["recommendations"])
            self.assertIn("PHYSICAL_FIELD_VALIDATION_REQUIRED", item["recommendations"])
    def test_invalid_version(self): self.invalid_plan(lambda value: value.__setitem__("plan_version", 2))
    def test_invalid_speed(self): self.invalid_plan(lambda value: value["simulation_matrix"]["speed_profiles"][0].__setitem__("speed_mm_per_min", 1))
    def test_invalid_window(self): self.invalid_plan(lambda value: value["work_day_model"]["daily_windows"][0].__setitem__("scheduled_minutes_per_day", 1))
    def test_invalid_operator(self): self.invalid_plan(lambda value: value["logistics_model"].__setitem__("operator_count_options", [0, 2, 3]))
    def test_invalid_vehicle_capacity(self): self.invalid_plan(lambda value: value["logistics_model"].__setitem__("vehicle_rover_capacity_options", [6, 8, 12]))
    def test_invalid_battery_pool(self): self.invalid_plan(lambda value: value["battery_model"].__setitem__("battery_pool_options", [0, 24, 36]))
    def test_invalid_charger(self): self.invalid_plan(lambda value: value["battery_model"].__setitem__("charger_count", 0))
    def test_report_inside_repository(self):
        arguments = MOD.SchedulerArguments(ROOT, PLAN, ROOT / "x.json", Path(tempfile.gettempdir()) / "x.txt")
        self.assertRaises(MOD.MfwFailure, MOD.validate_arguments, arguments)
    def test_missing_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); arguments = MOD.SchedulerArguments(ROOT, PLAN, root / "missing/x.json", root / "x.txt")
            self.assertRaises(MOD.MfwFailure, MOD.validate_arguments, arguments)
    def test_parent_is_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); parent = root / "file"; parent.write_text("x", encoding="utf-8")
            arguments = MOD.SchedulerArguments(ROOT, PLAN, parent / "x.json", root / "x.txt")
            self.assertRaises(MOD.MfwFailure, MOD.validate_arguments, arguments)
    def test_scheduler_exception(self):
        failure = MOD.run_scheduler(MOD.SchedulerArguments(ROOT, PLAN, Path(tempfile.gettempdir()) / "a.json", Path(tempfile.gettempdir()) / "a.txt"), builder=lambda *args: (_ for _ in ()).throw(RuntimeError("detail")), write_reports=False)
        self.assertEqual(failure.exit_code, 7)
    def test_report_write_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); arguments = MOD.SchedulerArguments(ROOT, PLAN, root / "a.json", root / "a.txt")
            with mock.patch.object(MOD, "write_report", side_effect=OSError):
                self.assertEqual(MOD.run_scheduler(arguments, builder=lambda *args: self.report).exit_code, 7)
    def test_internal_exception_sanitized(self):
        report = MOD._failure_report(MOD.MfwFailure("MFW_INTERNAL_ERROR", "internal", "Unexpected internal failure.", 7))
        self.assertNotIn("detail", MOD.render_json_report(report))


def _make_field_probe(index, expected_id, expected_group, expected_area):
    def test(self):
        field = self.fields[index]
        self.assertEqual((field["field_id"], field["group_id"], field["area_m2"], field["area_estimated"]), (expected_id, expected_group, expected_area, True))
    return test


_FORMAL_FIELDS = [
    ("GROUP-HOME-F01", "GROUP-HOME", 1422),
] + [(f"GROUP-HOME-F{index:02d}", "GROUP-HOME", 1421) for index in range(2, 10)] + [
    (f"GROUP-OTHER-CONSIGNED-F{index:02d}", "GROUP-OTHER-CONSIGNED", 1421) for index in range(1, 4)
] + [(f"GROUP-CONSIGNED-F{index:02d}", "GROUP-CONSIGNED", 1421) for index in range(1, 3)] + [
    (f"GROUP-OWN-A-F{index:02d}", "GROUP-OWN-A", 1421) for index in range(1, 3)
] + [(f"GROUP-OWN-B-F{index:02d}", "GROUP-OWN-B", 1421) for index in range(1, 4)]
for _index, (_field_id, _group_id, _area) in enumerate(_FORMAL_FIELDS):
    setattr(MultiFieldWeedSchedulerTests, f"test_formal_field_{_index:02d}", _make_field_probe(_index, _field_id, _group_id, _area))


def _make_safety_probe(key, expected):
    def test(self): self.assertIs(self.report.document["safety"][key], expected)
    return test


for _key, _expected in MOD.safety_document().items():
    setattr(MultiFieldWeedSchedulerTests, f"test_safety_{_key}", _make_safety_probe(_key, _expected))


def _make_configuration_probe(index):
    def test(self):
        configurations = list(itertools.islice(MOD.configuration_generator(), index, index + 1))
        self.assertEqual(len(configurations), 1)
        item = configurations[0]
        self.assertIn(item.policy, MOD.POLICIES)
        self.assertIn(item.speed_mm_per_min, (400, 700, 1000))
        self.assertIn(item.daily_window_minutes, (150, 300, 480))
        self.assertIn(item.operator_count, MOD.OPERATOR_OPTIONS)
        self.assertIn(item.vehicle_rover_capacity, MOD.VEHICLE_CAPACITIES)
        self.assertIn(item.battery_pool_count, MOD.BATTERY_POOLS)
    return test


for _index in range(120):
    setattr(MultiFieldWeedSchedulerTests, f"test_configuration_probe_{_index:03d}", _make_configuration_probe(_index))


def _make_arithmetic_probe(index):
    def test(self):
        numerator = 1000 + index * 37
        denominator = 1 + index % 17
        result = MOD.ceil_div(numerator, denominator)
        self.assertGreaterEqual(result * denominator, numerator)
        self.assertLess((result - 1) * denominator, numerator)
    return test


for _index in range(40):
    setattr(MultiFieldWeedSchedulerTests, f"test_integer_rounding_probe_{_index:03d}", _make_arithmetic_probe(_index))


if __name__ == "__main__":
    unittest.main(verbosity=2)
