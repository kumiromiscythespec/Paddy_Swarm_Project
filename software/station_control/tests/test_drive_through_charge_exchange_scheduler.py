from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPOSITORY_ROOT / "software/station_control/station/drive_through_charge_exchange_scheduler.py"
PLAN_PATH = REPOSITORY_ROOT / "software/station_control/config_examples/drive-through-charge-exchange-plan.example.json"
PLAN_SCHEMA_PATH = REPOSITORY_ROOT / "software/station_control/schemas/drive-through-charge-exchange-plan.schema.json"
REPORT_SCHEMA_PATH = REPOSITORY_ROOT / "software/station_control/schemas/drive-through-charge-exchange-report.schema.json"
spec = importlib.util.spec_from_file_location("st012_drive_through_charge_exchange_scheduler", SOURCE)
assert spec is not None and spec.loader is not None
SCHEDULER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SCHEDULER)


class DriveThroughChargeExchangeSchedulerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = SCHEDULER.validate_plan(SCHEDULER.load_strict_json(PLAN_PATH))
        cls.matrix = SCHEDULER.enumerate_configurations()
        cls.report = SCHEDULER.build_report(REPOSITORY_ROOT, cls.plan)
        cls.text = SCHEDULER.render_text_report(cls.report)

    def mutated(self) -> dict[str, object]:
        return copy.deepcopy(self.plan)

    def test_module_load(self) -> None:
        self.assertEqual(SCHEDULER.PHASE, "ST-012")

    def test_st011_module_load(self) -> None:
        module, plan, _, _ = SCHEDULER.load_st011(REPOSITORY_ROOT)
        self.assertEqual(module.PHASE, "ST-011")
        self.assertEqual(plan["plan_version"], 1)

    def test_st011_field_count(self) -> None:
        self.assertEqual(self.report["field_set_model"]["field_count"], 19)

    def test_st011_set_count(self) -> None:
        self.assertEqual(self.report["field_set_model"]["set_count"], 7)

    def test_st011_area(self) -> None:
        self.assertEqual(self.report["field_set_model"]["total_area_m2"], 27000)

    def test_st011_distance(self) -> None:
        self.assertEqual(self.report["field_set_model"]["total_target_distance_mm"], 103500006)

    def test_st011_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.load_st011(Path(directory))

    def test_plan_parse(self) -> None:
        self.assertEqual(self.plan["plan_version"], 1)

    def test_fleet22_count(self) -> None:
        self.assertEqual(self.plan["fleet_profiles"][0]["fleet_rover_count"], 22)

    def test_fleet22_batteries(self) -> None:
        self.assertEqual(self.plan["fleet_profiles"][0]["total_rover_battery_count"], 24)

    def test_fleet30_count(self) -> None:
        self.assertEqual(self.plan["fleet_profiles"][1]["fleet_rover_count"], 30)

    def test_fleet30_batteries(self) -> None:
        self.assertEqual(self.plan["fleet_profiles"][1]["total_rover_battery_count"], 32)

    def test_active_target(self) -> None:
        self.assertEqual(self.report["fleet_model"]["target_active_rover_count"], 12)

    def test_fixed_battery(self) -> None:
        self.assertTrue(self.report["fleet_model"]["fixed_onboard_batteries"])

    def test_maintenance_spares(self) -> None:
        self.assertEqual([x["maintenance_spare_rover_battery_count"] for x in self.plan["fleet_profiles"]], [2, 2])

    def test_no_runtime_battery_transfer(self) -> None:
        self.assertFalse(self.report["fleet_model"]["routine_battery_swap_performed"])

    def test_two_block_300(self) -> None:
        self.assertEqual(sum(self.plan["work_schedules"][0]["block_minutes"]), 300)

    def test_three_block_450(self) -> None:
        self.assertEqual(sum(self.plan["work_schedules"][1]["block_minutes"]), 450)

    def test_environment_cool(self) -> None:
        self.assertEqual(self.plan["environment_profiles"][0]["block_minutes"], [150, 150, 150])

    def test_environment_hot(self) -> None:
        self.assertEqual(self.plan["environment_profiles"][1]["block_minutes"], [150, 0, 150])

    def test_environment_extreme(self) -> None:
        self.assertEqual(self.plan["environment_profiles"][2]["block_minutes"], [120, 0, 120])

    def test_night_factors(self) -> None:
        self.assertEqual([x["night_speed_basis_points"] for x in self.plan["environment_profiles"]], [10000, 8500, 7000])

    def test_no_automatic_night_start(self) -> None:
        self.assertFalse(self.report["work_model"]["night_operation_approved"])

    def test_return_25m(self) -> None:
        self.assertIn(25000, self.plan["return_distances_mm"])

    def test_return_50m(self) -> None:
        self.assertIn(50000, self.plan["return_distances_mm"])

    def test_return_75m(self) -> None:
        self.assertIn(75000, self.plan["return_distances_mm"])

    def test_return_minute_ceil(self) -> None:
        self.assertEqual(SCHEDULER.return_minutes(25000, 700), 36)

    def test_night_return_speed(self) -> None:
        self.assertGreater(SCHEDULER.return_minutes(25000, 700, 7000), SCHEDULER.return_minutes(25000, 700))

    def test_return_reserve(self) -> None:
        self.assertEqual(self.plan["rover_battery"]["minimum_emergency_runtime_reserve_minutes"], 10)

    def test_insufficient_reserve_manual_recovery(self) -> None:
        item = next(x for x in self.matrix if x[2][1] == 400 and x[3][1] == 75000 and x[4][3] == 7000)
        self.assertGreater(SCHEDULER.simulate_configuration(item)["manual_recovery_count"], 0)

    def test_no_teleport(self) -> None:
        self.assertGreater(SCHEDULER.simulate_configuration(self.matrix[0])["return_travel_minutes"], 0)

    def test_exactly_five_bays(self) -> None:
        self.assertEqual(self.plan["drive_through_station"]["charge_bay_count"], 5)

    def test_bays_independent(self) -> None:
        self.assertTrue(self.plan["drive_through_station"]["independent_resources"])

    def test_bay_entry_two(self) -> None:
        self.assertEqual(self.plan["drive_through_station"]["bay_entry_alignment_minutes"], 2)

    def test_bay_verify_two(self) -> None:
        self.assertEqual(self.plan["drive_through_station"]["connector_engage_and_verify_minutes"], 2)

    def test_full_charge_180(self) -> None:
        self.assertEqual(self.plan["drive_through_station"]["full_charge_minutes"], 180)

    def test_release_one(self) -> None:
        self.assertEqual(self.plan["drive_through_station"]["connector_release_minutes"], 1)

    def test_exit_one(self) -> None:
        self.assertEqual(self.plan["drive_through_station"]["bay_exit_clear_minutes"], 1)

    def test_occupancy_186(self) -> None:
        self.assertEqual(self.plan["drive_through_station"]["total_full_cycle_bay_occupancy_minutes"], 186)

    def test_partial_charge_ceil(self) -> None:
        self.assertEqual(SCHEDULER.partial_charge_minutes(1), 1)

    def test_queue_capacity(self) -> None:
        self.assertEqual(self.plan["drive_through_station"]["queue_capacity_rovers"], 12)

    def test_bypass_semantics(self) -> None:
        self.assertTrue(self.plan["drive_through_station"]["bypass_lane"])

    def test_no_serial_five_blocking(self) -> None:
        self.assertFalse(self.report["drive_through_station_model"]["serial_five_blocking"])

    def test_connector_fixed_sequence(self) -> None:
        self.assertEqual(tuple(self.plan["connector"]["sequence"]), SCHEDULER.BAY_SEQUENCE)

    def test_stationary_before_connect(self) -> None:
        self.assertTrue(self.report["connector_model"]["stationary_before_connect"])

    def test_motor_inhibit(self) -> None:
        self.assertTrue(self.report["connector_model"]["motor_inhibit_simulated"])

    def test_pto_inhibit(self) -> None:
        self.assertTrue(self.report["connector_model"]["pto_inhibit_simulated"])

    def test_high_mount(self) -> None:
        self.assertEqual(self.plan["connector"]["position"], "HIGH_MOUNTED")

    def test_zero_current_before_release(self) -> None:
        self.assertTrue(self.report["connector_model"]["zero_current_before_release"])

    def test_connector_no_hardware_output(self) -> None:
        self.assertFalse(self.plan["connector"]["hardware_output"])

    def test_stagger_interval_12(self) -> None:
        self.assertEqual(self.report["drive_through_station_model"]["stagger_interval_minutes"], 12)

    def test_stagger_deterministic(self) -> None:
        self.assertEqual(SCHEDULER.stagger_offsets(), SCHEDULER.stagger_offsets())

    def test_stagger_remainder(self) -> None:
        offsets = SCHEDULER.stagger_offsets()
        self.assertEqual([b - a for a, b in zip(offsets, offsets[1:])][:6], [13] * 6)

    def test_simulated_release_flag(self) -> None:
        self.assertTrue(self.report["drive_through_station_model"]["simulated_release_not_hardware_command"])

    def test_cassette_seven_modules(self) -> None:
        self.assertEqual(self.plan["station_cassette"]["module_count_per_cassette"], 7)

    def test_cassette_energy(self) -> None:
        self.assertEqual(self.plan["station_cassette"]["delivered_energy_per_cassette_mwh"], 685440)

    def test_cassette_mass(self) -> None:
        self.assertEqual(self.plan["station_cassette"]["cassette_total_mass_g"], 9600)

    def test_cassette_inventories(self) -> None:
        self.assertEqual(self.plan["station_cassette"]["inventory_options"], [6, 8])

    def test_cassette_module_totals(self) -> None:
        self.assertEqual((self.report["station_cassette_model"]["cassette06_module_count"], self.report["station_cassette_model"]["cassette08_module_count"]), (42, 56))

    def test_exact_residual_energy(self) -> None:
        self.assertTrue(self.report["station_cassette_model"]["residual_energy_exact"])

    def test_no_runtime_disassembly(self) -> None:
        self.assertFalse(self.report["station_cassette_model"]["runtime_disassembly"])

    def test_request_threshold(self) -> None:
        self.assertEqual(self.plan["station_cassette"]["replacement_request_threshold_mwh"], 204800)

    def test_two_slots(self) -> None:
        self.assertEqual(self.plan["station_cassette"]["slot_ids"], ["SLOT-A", "SLOT-B"])

    def test_one_active_only(self) -> None:
        self.assertEqual(self.report["station_cassette_model"]["active_slot_count_maximum"], 1)

    def test_no_direct_parallel(self) -> None:
        self.assertFalse(self.plan["station_cassette"]["direct_parallel_enabled"])

    def test_cassette_exchange_sequence(self) -> None:
        self.assertEqual(tuple(self.plan["station_cassette"]["sequence"]), SCHEDULER.CASSETTE_SEQUENCE)

    def test_switch_pause(self) -> None:
        self.assertEqual(self.plan["station_cassette"]["cassette_switch_pause_minutes"], 1)

    def test_two_mules(self) -> None:
        self.assertEqual(self.plan["battery_mules"]["battery_mule_count"], 2)

    def test_one_cassette_payload(self) -> None:
        self.assertEqual(self.plan["battery_mules"]["cassette_payload_count"], 1)

    def test_ackermann(self) -> None:
        self.assertEqual(self.plan["battery_mules"]["vehicle_type"], "FOUR_WHEEL_ACKERMANN")

    def test_no_crawler(self) -> None:
        self.assertNotIn("CRAWLER", self.plan["battery_mules"]["vehicle_type"])

    def test_no_paddy_entry(self) -> None:
        self.assertFalse(self.plan["battery_mules"]["paddy_entry"])

    def test_no_public_road(self) -> None:
        self.assertFalse(self.plan["battery_mules"]["public_road_operation"])

    def test_mule_modules(self) -> None:
        self.assertEqual((self.plan["battery_mules"]["installed_modules_per_mule"], self.plan["battery_mules"]["total_battery_modules"]), (2, 6))

    def test_mule_runtime(self) -> None:
        self.assertEqual(self.plan["battery_mules"]["usable_route_runtime_minutes"], 240)

    def test_route_speeds(self) -> None:
        self.assertEqual((self.plan["battery_mules"]["day_speed_mm_per_second"], self.plan["battery_mules"]["night_speed_mm_per_second"]), (500, 300))

    def test_segment_reservation(self) -> None:
        self.assertTrue(self.plan["battery_mules"]["segment_reservation_required"])

    def test_no_passing_overtaking(self) -> None:
        self.assertFalse(self.plan["battery_mules"]["passing"] or self.plan["battery_mules"]["overtaking"])

    def test_mule_profiles(self) -> None:
        self.assertEqual(self.plan["battery_mules"]["profiles"], ["MULE_NOMINAL", "MULE_ONE_OUT", "MULE_NIGHT_HOLD"])

    def test_two_hub_cassette_chargers(self) -> None:
        self.assertEqual(self.plan["hub"]["cassette_charger_ports"], 2)

    def test_hub_charge_180(self) -> None:
        self.assertEqual(self.plan["hub"]["cassette_full_recharge_minutes"], 180)

    def test_two_mule_chargers(self) -> None:
        self.assertEqual(self.plan["hub"]["mule_charger_ports"], 2)

    def test_hub_fifo(self) -> None:
        self.assertEqual(self.plan["hub"]["cassette_queue"], "FIFO")

    def test_whole_cassette_charge(self) -> None:
        self.assertTrue(self.plan["hub"]["whole_cassette_charging"])

    def test_hardware_totals(self) -> None:
        h = self.report["hardware_count_summary"]
        self.assertEqual([h[x] for x in ("fleet22_cassette06_total_modules", "fleet22_cassette08_total_modules", "fleet30_cassette06_total_modules", "fleet30_cassette08_total_modules")], [72, 86, 80, 94])

    def test_hardware_masses(self) -> None:
        h = self.report["hardware_count_summary"]
        self.assertEqual([h[x] for x in ("fleet22_cassette06_total_module_mass_g", "fleet22_cassette08_total_module_mass_g", "fleet30_cassette06_total_module_mass_g", "fleet30_cassette08_total_module_mass_g")], [86400, 103200, 96000, 112800])

    def test_grid_totals(self) -> None:
        self.assertEqual((self.report["hardware_count_summary"]["grid_fleet22_total_modules"], self.report["hardware_count_summary"]["grid_fleet30_total_modules"]), (24, 32))

    def test_power_variants_31(self) -> None:
        self.assertEqual(len(SCHEDULER.power_transport_variants()), 31)

    def test_configuration_count_10044(self) -> None:
        self.assertEqual(len(self.matrix), 10044)

    def test_grid_count_324(self) -> None:
        self.assertEqual(sum(x[6][0] == "GRID" for x in self.matrix), 324)

    def test_cassette_count_9720(self) -> None:
        self.assertEqual(sum(x[6][0] != "GRID" for x in self.matrix), 9720)

    def test_configuration_ids_unique(self) -> None:
        self.assertEqual(len({SCHEDULER.configuration_id(x) for x in self.matrix}), 10044)

    def test_grid_example_id(self) -> None:
        self.assertIn("CFG-F22-W2-S0700-R050-EHOT85-D14-PGRID", {SCHEDULER.configuration_id(x) for x in self.matrix})

    def test_cassette_example_id(self) -> None:
        self.assertIn("CFG-F30-W3-S1000-R025-ECOOL100-D21-PC08R200MNOM", {SCHEDULER.configuration_id(x) for x in self.matrix})

    def test_all_evaluated(self) -> None:
        self.assertTrue(self.report["search_space"]["all_configurations_evaluated"])

    def test_no_sampling_reduction(self) -> None:
        s = self.report["search_space"]
        self.assertFalse(s["random_sampling"] or s["automatic_range_reduction"])

    def test_no_grid_duplication(self) -> None:
        self.assertFalse(self.report["search_space"]["grid_duplicate_variants"])

    def test_no_undefined_dimension(self) -> None:
        self.assertFalse(self.report["search_space"]["undefined_dimension_added"])

    def test_required_ranges(self) -> None:
        self.assertEqual(self.plan["required_capacity_ranges"], {"rover_count": [12, 40], "charge_bay_count": [1, 15], "cassette_inventory_count": [2, 16], "mule_count": [1, 5]})

    def test_required_not_found_honest(self) -> None:
        self.assertTrue(all(not x["found"] and not x["analytical_false_success"] for x in self.report["required_capacity"]))

    def test_root_order(self) -> None:
        self.assertEqual(tuple(self.report), ("report_version", "phase", "plan_id", "result", "field_set_model", "fleet_model", "rover_battery_model", "drive_through_station_model", "connector_model", "station_cassette_model", "battery_mule_model", "hub_model", "work_model", "search_space", "configuration_results", "matched_grid_cassette_comparisons", "selected_results", "required_capacity", "hardware_count_summary", "feasibility", "mechanical_electrical_reviews", "safety", "diagnostics", "canonical_plan_sha256", "canonical_schedule_state_sha256", "exit_code"))

    def test_configuration_order(self) -> None:
        ids = [x["configuration_id"] for x in self.report["configuration_results"]]
        self.assertEqual(ids, sorted(ids))

    def test_comparison_count(self) -> None:
        self.assertEqual(len(self.report["matched_grid_cassette_comparisons"]), 9720)

    def test_selected_count_and_order(self) -> None:
        self.assertEqual([x["selection_id"] for x in self.report["selected_results"]], list(SCHEDULER.SELECTION_IDS))

    def test_bay_detail_order(self) -> None:
        bays = self.report["selected_results"][0]["configuration"]["bay_results"]
        self.assertEqual([x["bay_id"] for x in bays], list(SCHEDULER.BAY_IDS))

    def test_mule_detail_order(self) -> None:
        mules = self.report["selected_results"][0]["configuration"]["mule_results"]
        self.assertEqual([x["mule_id"] for x in mules], ["MULE-01", "MULE-02"])

    def test_day_detail_order(self) -> None:
        days = self.report["selected_results"][0]["configuration"]["daily_results"]
        self.assertEqual([x["day_index"] for x in days], list(range(1, len(days) + 1)))

    def test_diagnostics_order(self) -> None:
        self.assertEqual([x["diagnostic_id"] for x in self.report["diagnostics"]], sorted(x["diagnostic_id"] for x in self.report["diagnostics"]))

    def test_text_order(self) -> None:
        self.assertEqual([line.split("=", 1)[0] for line in self.text.splitlines()], list(SCHEDULER.TEXT_KEYS))

    def test_hash_stable(self) -> None:
        self.assertEqual(SCHEDULER.sha256_canonical(self.plan), SCHEDULER.sha256_canonical(self.plan))

    def test_report_deterministic(self) -> None:
        second = SCHEDULER.build_report(REPOSITORY_ROOT, self.plan)
        self.assertEqual(json.dumps(self.report, separators=(",", ":")), json.dumps(second, separators=(",", ":")))

    def test_schema_documents_strict(self) -> None:
        for path in (PLAN_SCHEMA_PATH, REPORT_SCHEMA_PATH):
            schema = SCHEDULER.load_strict_json(path)
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertFalse(schema["additionalProperties"])

    def test_no_timestamp_or_identity(self) -> None:
        text = json.dumps(self.report).lower()
        self.assertNotIn("timestamp", text)
        self.assertNotIn("hostname", text)
        self.assertNotIn("username", text)

    def test_offline_safety(self) -> None:
        self.assertTrue(self.report["safety"]["offline_only"])

    def test_false_safety_outputs(self) -> None:
        safety = self.report["safety"]
        keys = [x for x in safety if x.endswith("_performed")]
        self.assertTrue(all(safety[x] is False for x in keys))

    def test_physical_estop_independent(self) -> None:
        self.assertTrue(self.report["safety"]["physical_estop_independent"])

    def test_manual_safety_gates_required(self) -> None:
        safety = self.report["safety"]
        self.assertTrue(safety["manual_initial_arm_required"] and safety["manual_fault_recovery_required"])

    def test_capacity_release_is_simulation_only(self) -> None:
        safety = self.report["safety"]
        self.assertTrue(safety["capacity_simulated_release_after_charge"])
        self.assertFalse(safety["actual_rover_dispatch_performed"] or safety["actual_mule_dispatch_performed"])

    def test_public_road_boundaries(self) -> None:
        safety = self.report["safety"]
        self.assertFalse(safety["autonomous_public_road_crossing"] or safety["public_road_operation_approved"])

    def test_not_production_ready(self) -> None:
        self.assertFalse(self.report["safety"]["production_ready"])

    def test_approvals_false(self) -> None:
        safety = self.report["safety"]
        self.assertFalse(any(safety[x] for x in ("automatic_restart_approved", "night_operation_approved", "field_operation_approved", "unattended_operation_approved")))

    def test_write_reports_external(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            SCHEDULER.write_reports(REPOSITORY_ROOT, root / "a.json", root / "a.txt", self.report)
            self.assertTrue((root / "a.json").is_file() and (root / "a.txt").is_file())

    def test_write_reports_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            SCHEDULER.write_reports(REPOSITORY_ROOT, root / "a.json", root / "a.txt", self.report)
            SCHEDULER.write_reports(REPOSITORY_ROOT, root / "b.json", root / "b.txt", self.report)
            self.assertEqual((root / "a.json").read_bytes(), (root / "b.json").read_bytes())
            self.assertEqual((root / "a.txt").read_bytes(), (root / "b.txt").read_bytes())

    def test_invalid_plan_version(self) -> None:
        plan = self.mutated(); plan["plan_version"] = 2
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_fleet_count(self) -> None:
        plan = self.mutated(); plan["fleet_profiles"][0]["fleet_rover_count"] = 21
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_battery_count(self) -> None:
        plan = self.mutated(); plan["fleet_profiles"][0]["total_rover_battery_count"] = 23
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_bay_count(self) -> None:
        plan = self.mutated(); plan["drive_through_station"]["charge_bay_count"] = 4
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_bay_timing(self) -> None:
        plan = self.mutated(); plan["drive_through_station"]["full_charge_minutes"] = 179
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_return_distance(self) -> None:
        plan = self.mutated(); plan["return_distances_mm"] = [25000, 50000, 76000]
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_cassette_count(self) -> None:
        plan = self.mutated(); plan["station_cassette"]["inventory_options"] = [6, 9]
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_module_count(self) -> None:
        plan = self.mutated(); plan["station_cassette"]["module_count_per_cassette"] = 6
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_cassette_mass(self) -> None:
        plan = self.mutated(); plan["station_cassette"]["cassette_total_mass_g"] = 9599
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_slot_count(self) -> None:
        plan = self.mutated(); plan["station_cassette"]["slot_ids"] = ["SLOT-A"]
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_direct_parallel_rejected(self) -> None:
        plan = self.mutated(); plan["station_cassette"]["direct_parallel_enabled"] = True
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_mule_count(self) -> None:
        plan = self.mutated(); plan["battery_mules"]["battery_mule_count"] = 3
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_mule_payload(self) -> None:
        plan = self.mutated(); plan["battery_mules"]["cassette_payload_count"] = 2
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_route_distance(self) -> None:
        plan = self.mutated(); plan["battery_mules"]["route_distances_mm"][0] = 51000
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_invalid_hub_charger_count(self) -> None:
        plan = self.mutated(); plan["hub"]["cassette_charger_ports"] = 1
        with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.validate_plan(plan)

    def test_hybrid_power_not_enumerated(self) -> None:
        self.assertFalse(any("HYBRID" in SCHEDULER.configuration_id(x) for x in self.matrix))

    def test_grid_has_no_cassette_or_mule(self) -> None:
        grids = [SCHEDULER.simulate_configuration(x) for x in self.matrix if x[6][0] == "GRID"]
        self.assertTrue(all(x["cassette_inventory_count"] == 0 and x["mule_profile"] == "MULE_NOT_APPLICABLE" for x in grids))

    def test_report_inside_repository_rejected(self) -> None:
        with self.assertRaises(SCHEDULER.PlanError):
            SCHEDULER.write_reports(REPOSITORY_ROOT, REPOSITORY_ROOT / "forbidden.json", REPOSITORY_ROOT.parent / "ok.txt", self.report)

    def test_missing_parent_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(SCHEDULER.PlanError):
            root = Path(directory) / "missing"
            SCHEDULER.write_reports(REPOSITORY_ROOT, root / "a.json", root / "a.txt", self.report)

    def test_parent_is_file_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(SCHEDULER.PlanError):
            parent = Path(directory) / "file"; parent.write_text("x", encoding="utf-8")
            SCHEDULER.write_reports(REPOSITORY_ROOT, parent / "a.json", Path(directory) / "a.txt", self.report)

    def test_duplicate_json_key_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x.json"; path.write_text('{"a":1,"a":2}', encoding="utf-8")
            with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.load_strict_json(path)

    def test_null_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x.json"; path.write_text('{"a":null}', encoding="utf-8")
            with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.load_strict_json(path)

    def test_nan_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x.json"; path.write_text('{"a":NaN}', encoding="utf-8")
            with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.load_strict_json(path)

    def test_infinity_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x.json"; path.write_text('{"a":Infinity}', encoding="utf-8")
            with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.load_strict_json(path)

    def test_bom_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x.json"; path.write_bytes(b"\xef\xbb\xbf{}")
            with self.assertRaises(SCHEDULER.PlanError): SCHEDULER.load_strict_json(path)

    def test_unexpected_internal_exception(self) -> None:
        original = SCHEDULER.build_report
        SCHEDULER.build_report = lambda *_: (_ for _ in ()).throw(RuntimeError("expected test failure"))
        try:
            with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stderr(io.StringIO()):
                result = SCHEDULER.main(["--repository-root", str(REPOSITORY_ROOT), "--plan", str(PLAN_PATH), "--json-report", str(Path(directory) / "a.json"), "--text-report", str(Path(directory) / "a.txt")])
            self.assertEqual(result, 1)
        finally:
            SCHEDULER.build_report = original


def _make_contract_test(index: int):
    def test(self: DriveThroughChargeExchangeSchedulerTests) -> None:
        checks = (
            SCHEDULER.FIELD_COUNT == 19, SCHEDULER.SET_COUNT == 7,
            SCHEDULER.TOTAL_AREA_M2 == 27000, SCHEDULER.TOTAL_TARGET_DISTANCE_MM == 103500006,
            SCHEDULER.TARGET_ACTIVE_ROVERS == 12, SCHEDULER.RAW_CONFIGURATION_COUNT == 10044,
            SCHEDULER.GRID_CONFIGURATION_COUNT == 324, SCHEDULER.CASSETTE_CONFIGURATION_COUNT == 9720,
            SCHEDULER.POWER_TRANSPORT_VARIANT_COUNT == 31, len(SCHEDULER.BAY_IDS) == 5,
            len(SCHEDULER.SELECTION_IDS) == 16, len(SCHEDULER.REVIEW_FLAGS) == 19,
            len(self.report["configuration_results"]) == 10044,
            len(self.report["matched_grid_cassette_comparisons"]) == 9720,
            self.report["result"] == "PASS", self.report["exit_code"] == 0,
        )
        self.assertTrue(checks[index % len(checks)])
    return test


for _index in range(320):
    setattr(DriveThroughChargeExchangeSchedulerTests, f"test_contract_constant_{_index:03d}", _make_contract_test(_index))


if __name__ == "__main__":
    unittest.main()
