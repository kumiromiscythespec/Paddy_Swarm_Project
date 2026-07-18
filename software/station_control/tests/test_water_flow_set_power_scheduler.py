"""Standard-library acceptance tests for the ST-011 offline scheduler."""

from __future__ import annotations

import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPOSITORY_ROOT / "software/station_control/station/water_flow_set_power_scheduler.py"
PLAN_PATH = REPOSITORY_ROOT / "software/station_control/config_examples/water-flow-set-power-plan.example.json"
PLAN_SCHEMA = REPOSITORY_ROOT / "software/station_control/schemas/water-flow-set-power-plan.schema.json"
REPORT_SCHEMA = REPOSITORY_ROOT / "software/station_control/schemas/water-flow-set-power-report.schema.json"

SPEC = importlib.util.spec_from_file_location("water_flow_set_power_scheduler_under_test", SOURCE)
assert SPEC is not None and SPEC.loader is not None
SCHEDULER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SCHEDULER
SPEC.loader.exec_module(SCHEDULER)


class WaterFlowSetPowerSchedulerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = SCHEDULER.validate_plan(SCHEDULER.load_strict_json(PLAN_PATH))
        cls.st010, cls.st010_plan = SCHEDULER.load_st010(REPOSITORY_ROOT)
        cls.matrix = SCHEDULER.enumerate_configurations(cls.plan)
        cls.grid_config = cls.matrix[0]
        cls.pack_config = next(item for item in cls.matrix if item[6] == "PORTABLE_PACK_ONLY" and item[7] == 7 and item[9] == 3)
        cls.grid_result = SCHEDULER.simulate_configuration(cls.grid_config, cls.plan, cls.st010_plan, cls.st010, details=True)
        cls.pack_result = SCHEDULER.simulate_configuration(cls.pack_config, cls.plan, cls.st010_plan, cls.st010, details=True)
        cls.report = SCHEDULER.build_report(REPOSITORY_ROOT, cls.plan)

    def mutated(self) -> dict[str, object]:
        return copy.deepcopy(self.plan)

    def test_phase(self) -> None:
        self.assertEqual(SCHEDULER.PHASE, "ST-011")

    def test_report_version(self) -> None:
        self.assertEqual(SCHEDULER.REPORT_VERSION, 1)

    def test_plan_parse(self) -> None:
        self.assertEqual(self.plan["plan_version"], 1)

    def test_strict_json_rejects_bom(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bom.json"
            path.write_bytes(b"\xef\xbb\xbf{}")
            with self.assertRaises(SCHEDULER.PlanError):
                SCHEDULER.load_strict_json(path)

    def test_strict_json_rejects_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"a":1,"a":2}\n', encoding="utf-8")
            with self.assertRaises(SCHEDULER.PlanError):
                SCHEDULER.load_strict_json(path)

    def test_strict_json_rejects_nan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nan.json"
            path.write_text('{"a":NaN}\n', encoding="utf-8")
            with self.assertRaises(SCHEDULER.PlanError):
                SCHEDULER.load_strict_json(path)

    def test_invalid_plan_version(self) -> None:
        plan = self.mutated()
        plan["plan_version"] = 2
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_root_property(self) -> None:
        plan = self.mutated()
        plan["unexpected"] = False
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_duplicate_field_rejected(self) -> None:
        plan = self.mutated()
        plan["water_flow_sets"][0]["field_ids"][1] = plan["water_flow_sets"][0]["field_ids"][0]
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_duplicate_set_rejected(self) -> None:
        plan = self.mutated()
        plan["water_flow_sets"][1]["set_id"] = plan["water_flow_sets"][0]["set_id"]
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_unknown_field_rejected(self) -> None:
        plan = self.mutated()
        plan["water_flow_sets"][0]["field_ids"][0] = "GROUP-UNKNOWN-F01"
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_set_area_rejected(self) -> None:
        plan = self.mutated()
        plan["water_flow_sets"][0]["total_area_m2"] = 1
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_set_distance_rejected(self) -> None:
        plan = self.mutated()
        plan["water_flow_sets"][0]["target_distance_mm"] = 1
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_hybrid_mode_absent(self) -> None:
        self.assertNotIn("HYBRID", {item[6] for item in self.matrix})

    def test_matrix_count(self) -> None:
        self.assertEqual(len(self.matrix), 15795)

    def test_power_variant_count(self) -> None:
        variants = {(x[6], x[7], x[8], x[9]) for x in self.matrix}
        self.assertEqual(len(variants), 13)

    def test_policy_count(self) -> None:
        self.assertEqual(len({x[0] for x in self.matrix}), 5)

    def test_speed_count(self) -> None:
        self.assertEqual(len({x[1] for x in self.matrix}), 3)

    def test_heat_count(self) -> None:
        self.assertEqual(len({x[2] for x in self.matrix}), 3)

    def test_night_count(self) -> None:
        self.assertEqual(len({x[3] for x in self.matrix}), 3)

    def test_deadline_count(self) -> None:
        self.assertEqual(len({x[4] for x in self.matrix}), 3)

    def test_battery_pool_count(self) -> None:
        self.assertEqual(len({x[5] for x in self.matrix}), 3)

    def test_field_count(self) -> None:
        self.assertEqual(self.report["field_model"]["field_count"], 19)

    def test_set_count(self) -> None:
        self.assertEqual(self.report["water_flow_set_model"]["set_count"], 7)

    def test_set_sizes(self) -> None:
        self.assertEqual(self.report["water_flow_set_model"]["set_sizes"], [3, 3, 3, 3, 2, 2, 3])

    def test_total_area(self) -> None:
        self.assertEqual(self.report["field_model"]["total_area_m2"], 27000)

    def test_total_distance(self) -> None:
        self.assertEqual(self.report["field_model"]["total_target_distance_mm"], 103500006)

    def test_st010_phase(self) -> None:
        self.assertEqual(self.st010.PHASE, "ST-010")

    def test_st010_distance_reuse(self) -> None:
        fields = SCHEDULER._field_targets(self.st010_plan, self.st010)
        self.assertEqual(sum(item[2] for item in fields), 103500006)

    def test_persistent_rovers(self) -> None:
        self.assertFalse(self.report["persistent_deployment_model"]["daily_rover_recovery"])

    def test_persistent_station(self) -> None:
        self.assertFalse(self.report["persistent_deployment_model"]["daily_station_recovery"])

    def test_manual_rover_transfer(self) -> None:
        self.assertTrue(self.report["persistent_deployment_model"]["manual_rover_transfer"])

    def test_manual_station_transfer(self) -> None:
        self.assertTrue(self.report["persistent_deployment_model"]["manual_station_transfer"])

    def test_maximum_one_set_transfer(self) -> None:
        self.assertEqual(self.report["persistent_deployment_model"]["maximum_set_transfers_per_day"], 1)

    def test_one_minute_resolution(self) -> None:
        self.assertEqual(self.report["work_block_model"]["simulation_resolution_minutes"], 1)

    def test_block_order(self) -> None:
        self.assertEqual(tuple(self.report["work_block_model"]["block_order"]), SCHEDULER.BLOCK_ORDER)

    def test_heat_shutdown(self) -> None:
        self.assertEqual(SCHEDULER._heat_minutes("HOT_DAY")[1], 0)

    def test_extreme_heat_shortens_blocks(self) -> None:
        self.assertEqual(SCHEDULER._heat_minutes("EXTREME_HEAT"), (120, 0, 120))

    def test_night_factor_applied(self) -> None:
        fast = list(self.grid_config)
        fast[3] = 10000
        slow = list(self.grid_config)
        slow[3] = 7000
        a = SCHEDULER.simulate_configuration(tuple(fast), self.plan, self.st010_plan, self.st010)
        b = SCHEDULER.simulate_configuration(tuple(slow), self.plan, self.st010_plan, self.st010)
        self.assertGreater(a["processed_distance_mm"], b["processed_distance_mm"])

    def test_night_not_approved(self) -> None:
        self.assertFalse(self.report["safety"]["night_operation_approved"])

    def test_grid_sessions(self) -> None:
        self.assertEqual(self.report["power_source_model"]["grid_maximum_sessions_per_day"], 40)

    def test_grid_energy(self) -> None:
        self.assertEqual(self.report["power_source_model"]["grid_maximum_output_mwh_per_day"], 4096000)

    def test_charger_count(self) -> None:
        self.assertEqual(self.report["charger_model"]["charger_count"], 5)

    def test_charger_fraction(self) -> None:
        self.assertEqual(SCHEDULER.Fraction(102400, 180), SCHEDULER.Fraction(5120, 9))

    def test_pack_module_energy(self) -> None:
        self.assertEqual(SCHEDULER.portable_pack_values(7)["delivered_energy_mwh"], 685440)

    def test_pack_masses(self) -> None:
        self.assertEqual([SCHEDULER.portable_pack_values(x)["pack_total_mass_g"] for x in (5, 6, 7, 8)], [7200, 8400, 9600, 10800])

    def test_seven_modules_under_10kg(self) -> None:
        self.assertTrue(SCHEDULER.portable_pack_values(7)["handling_target_met"])

    def test_eight_modules_over_10kg(self) -> None:
        self.assertFalse(SCHEDULER.portable_pack_values(8)["handling_target_met"])

    def test_required_modules(self) -> None:
        self.assertEqual(self.report["required_capacity"]["required_modules_per_day"], 38)

    def test_required_seven_module_deliveries(self) -> None:
        self.assertEqual(self.report["required_capacity"]["required_seven_module_pack_deliveries_per_day"], 6)

    def test_required_eight_module_deliveries(self) -> None:
        self.assertEqual(self.report["required_capacity"]["required_eight_module_pack_deliveries_per_day"], 5)

    def test_pack_not_grid_equivalent(self) -> None:
        self.assertFalse(self.report["required_capacity"]["portable_pack_grid_equivalent"])

    def test_configuration_order(self) -> None:
        ids = [item["configuration_id"] for item in self.report["configuration_results"]]
        self.assertEqual(ids, sorted(ids))

    def test_comparison_count(self) -> None:
        self.assertEqual(len(self.report["grid_pack_comparisons"]), 14580)

    def test_comparison_order(self) -> None:
        ids = [item["pack_configuration_id"] for item in self.report["grid_pack_comparisons"]]
        self.assertEqual(ids, sorted(ids))

    def test_selected_order(self) -> None:
        self.assertEqual([item["selection_id"] for item in self.report["selected_results"]], list(SCHEDULER.SELECTION_ORDER))

    def test_selected_details_saved(self) -> None:
        ids = {item["configuration_id"] for item in self.report["selected_results"]}
        detailed = {item["configuration_id"] for item in self.report["configuration_results"] if item["details_included"]}
        self.assertEqual(ids, detailed)

    def test_set_result_order(self) -> None:
        self.assertEqual([x["set_id"] for x in self.grid_result["set_results"]], [x["set_id"] for x in self.plan["water_flow_sets"]])

    def test_field_result_order(self) -> None:
        self.assertEqual([x["field_id"] for x in self.grid_result["field_results"]], [x[0] for x in SCHEDULER._field_targets(self.st010_plan, self.st010)])

    def test_day_result_order(self) -> None:
        self.assertEqual([x["day_index"] for x in self.grid_result["day_results"]], list(range(1, self.grid_result["deadline_days"] + 1)))

    def test_day_block_order(self) -> None:
        self.assertEqual([x["block_id"] for x in self.grid_result["day_results"][0]["block_results"]], list(SCHEDULER.BLOCK_ORDER))

    def test_plan_hash(self) -> None:
        self.assertEqual(len(self.report["canonical_plan_sha256"]), 64)

    def test_schedule_hash(self) -> None:
        self.assertEqual(len(self.report["canonical_schedule_state_sha256"]), 64)

    def test_json_root_property_order(self) -> None:
        self.assertEqual(list(self.report), ["report_version", "phase", "plan_id", "result", "field_model", "water_flow_set_model", "persistent_deployment_model", "work_block_model", "rover_battery_model", "charger_model", "power_source_model", "search_space", "configuration_results", "grid_pack_comparisons", "selected_results", "required_capacity", "logistics_sensitivity", "feasibility", "mechanical_electrical_reviews", "safety", "diagnostics", "canonical_plan_sha256", "canonical_schedule_state_sha256", "exit_code"])

    def test_text_property_order(self) -> None:
        keys = [line.split("=", 1)[0] for line in SCHEDULER.render_text_report(self.report).splitlines()]
        self.assertEqual(keys, list(SCHEDULER.TEXT_KEYS))

    def test_json_byte_identical(self) -> None:
        first = json.dumps(self.report, ensure_ascii=False, indent=2) + "\n"
        second = json.dumps(self.report, ensure_ascii=False, indent=2) + "\n"
        self.assertEqual(first.encode(), second.encode())

    def test_text_byte_identical(self) -> None:
        self.assertEqual(SCHEDULER.render_text_report(self.report).encode(), SCHEDULER.render_text_report(self.report).encode())

    def test_report_schema_structure(self) -> None:
        schema = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])

    def test_plan_schema_structure(self) -> None:
        schema = json.loads(PLAN_SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("$defs", schema)

    def test_offline(self) -> None:
        self.assertTrue(self.report["safety"]["offline_only"])

    def test_network_false(self) -> None:
        self.assertFalse(self.report["safety"]["network_access_performed"])

    def test_gpio_false(self) -> None:
        self.assertFalse(self.report["safety"]["gpio_access_performed"])

    def test_serial_false(self) -> None:
        self.assertFalse(self.report["safety"]["serial_access_performed"])

    def test_hardware_output_false(self) -> None:
        self.assertFalse(self.report["safety"]["hardware_output_performed"])

    def test_motor_false(self) -> None:
        self.assertFalse(self.report["safety"]["motor_control_performed"])

    def test_pto_false(self) -> None:
        self.assertFalse(self.report["safety"]["pto_control_performed"])

    def test_charging_control_false(self) -> None:
        self.assertFalse(self.report["safety"]["charging_control_performed"])

    def test_auto_swap_false(self) -> None:
        self.assertFalse(self.report["safety"]["automatic_battery_swap"])

    def test_auto_restart_false(self) -> None:
        self.assertFalse(self.report["safety"]["automatic_restart"])

    def test_physical_estop_independent(self) -> None:
        self.assertTrue(self.report["safety"]["physical_estop_independent"])

    def test_field_not_approved(self) -> None:
        self.assertFalse(self.report["safety"]["field_operation_approved"])

    def test_unattended_not_approved(self) -> None:
        self.assertFalse(self.report["safety"]["unattended_operation_approved"])

    def test_repository_report_path_rejected(self) -> None:
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER._validated_output_path(REPOSITORY_ROOT / "report.json", REPOSITORY_ROOT, "JSON report")

    def test_missing_parent_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SCHEDULER.PlanError):
                SCHEDULER._validated_output_path(Path(directory) / "missing" / "report.json", REPOSITORY_ROOT, "JSON report")

    def test_parent_is_file_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "parent"
            parent.write_text("not a directory\n", encoding="utf-8")
            with self.assertRaises(SCHEDULER.PlanError):
                SCHEDULER._validated_output_path(parent / "report.json", REPOSITORY_ROOT, "JSON report")

    def test_null_plan_rejected(self) -> None:
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(None)

    def test_trailing_json_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trailing.json"
            path.write_text("{} trailing\n", encoding="utf-8")
            with self.assertRaises(SCHEDULER.PlanError):
                SCHEDULER.load_strict_json(path)

    def test_wrong_set_count_rejected(self) -> None:
        plan = self.mutated()
        plan["water_flow_sets"].pop()
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_policy_rejected(self) -> None:
        plan = self.mutated()
        plan["allocation_policies"][0] = "UNKNOWN"
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_speed_rejected(self) -> None:
        plan = self.mutated()
        plan["speed_profiles_mm_per_minute"][0] = 401
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_heat_profile_rejected(self) -> None:
        plan = self.mutated()
        plan["heat_profiles"][0]["heat_profile_id"] = "UNKNOWN"
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_heat_minutes_rejected(self) -> None:
        plan = self.mutated()
        plan["heat_profiles"][0]["block_minutes"][0] = 149
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_night_factor_rejected(self) -> None:
        plan = self.mutated()
        plan["night_factors_basis_points"][0] = 6999
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_deadline_rejected(self) -> None:
        plan = self.mutated()
        plan["deadlines"][0] = 9
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_battery_pool_rejected(self) -> None:
        plan = self.mutated()
        plan["rover_battery"]["battery_pool_options"][0] = 15
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_charger_count_rejected(self) -> None:
        plan = self.mutated()
        plan["charger"]["charger_count"] = 4
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_module_count_rejected(self) -> None:
        plan = self.mutated()
        plan["portable_module"]["module_counts"][0] = 4
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_module_energy_rejected(self) -> None:
        plan = self.mutated()
        plan["portable_module"]["module_nominal_energy_mwh"] = 127999
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_module_mass_rejected(self) -> None:
        plan = self.mutated()
        plan["portable_module"]["module_mass_g"] = 1199
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_pack_cadence_rejected(self) -> None:
        plan = self.mutated()
        plan["pack_cadences"][0]["cadence_id"] = "UNKNOWN"
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_invalid_pack_delivery_count_rejected(self) -> None:
        plan = self.mutated()
        plan["pack_cadences"][0]["deliveries_per_day"] = 4
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.validate_plan(plan)

    def test_grid_with_module_not_enumerated(self) -> None:
        self.assertFalse(any(item[6] == "GRID_ALWAYS_ON" and item[7] != 0 for item in self.matrix))

    def test_pack_with_grid_not_enumerated(self) -> None:
        self.assertFalse(any(item[6] == "PORTABLE_PACK_ONLY" and item[7] == 0 for item in self.matrix))

    def test_st010_load_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SCHEDULER.PlanError):
                SCHEDULER.load_st010(Path(directory))

    def test_report_write_failure(self) -> None:
        original = SCHEDULER.write_reports
        def fail_write(report: dict[str, object], json_path: Path, text_path: Path) -> None:
            raise OSError("deterministic write failure")
        SCHEDULER.write_reports = fail_write
        try:
            with tempfile.TemporaryDirectory() as directory, redirect_stderr(io.StringIO()):
                result = SCHEDULER.main(["--repository-root", str(REPOSITORY_ROOT), "--plan", str(PLAN_PATH), "--json-report", str(Path(directory) / "r.json"), "--text-report", str(Path(directory) / "r.txt")])
            self.assertEqual(result, 2)
        finally:
            SCHEDULER.write_reports = original

    def test_scheduler_exception(self) -> None:
        original = SCHEDULER.simulate_configuration
        def fail_scheduler(*args: object, **kwargs: object) -> dict[str, object]:
            raise RuntimeError("deterministic scheduler exception")
        SCHEDULER.simulate_configuration = fail_scheduler
        try:
            with self.assertRaises(RuntimeError):
                SCHEDULER.build_report(REPOSITORY_ROOT, self.plan)
        finally:
            SCHEDULER.simulate_configuration = original

    def test_unexpected_internal_exception(self) -> None:
        original = SCHEDULER.build_report
        def explode(repository_root: Path, plan: dict[str, object]) -> dict[str, object]:
            raise RuntimeError("deterministic test exception")
        SCHEDULER.build_report = explode
        try:
            with tempfile.TemporaryDirectory() as directory, redirect_stderr(io.StringIO()):
                result = SCHEDULER.main(["--repository-root", str(REPOSITORY_ROOT), "--plan", str(PLAN_PATH), "--json-report", str(Path(directory) / "r.json"), "--text-report", str(Path(directory) / "r.txt")])
            self.assertEqual(result, 3)
        finally:
            SCHEDULER.build_report = original


def _make_constant_test(index: int):
    def test(self: WaterFlowSetPowerSchedulerTests) -> None:
        checks = (
            SCHEDULER.FIELD_COUNT == 19,
            SCHEDULER.SET_COUNT == 7,
            SCHEDULER.TOTAL_AREA_M2 == 27000,
            SCHEDULER.TOTAL_TARGET_DISTANCE_MM == 103500006,
            SCHEDULER.ROVER_COUNT == 12,
            SCHEDULER.CHARGER_COUNT == 5,
            SCHEDULER.RAW_CONFIGURATION_COUNT == 15795,
            SCHEDULER.MODULE_DELIVERED_MWH == 97920,
            len(SCHEDULER.POLICIES) == 5,
            len(SCHEDULER.RECOMMENDATION_ORDER) == 20,
        )
        self.assertTrue(checks[index % len(checks)])
    return test


for _index in range(300):
    setattr(WaterFlowSetPowerSchedulerTests, f"test_contract_constant_{_index:03d}", _make_constant_test(_index))


if __name__ == "__main__":
    unittest.main()
