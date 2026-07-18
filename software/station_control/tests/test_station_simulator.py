"""Standard-library tests for the deterministic ST-003 station simulator."""

from __future__ import annotations

import ast
from contextlib import redirect_stderr
import copy
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock


STATION_CONTROL_ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_PATH = STATION_CONTROL_ROOT / "station" / "simulator.py"
SCENARIO_SCHEMA_PATH = STATION_CONTROL_ROOT / "schemas" / "station-simulator-scenario.schema.json"
REPORT_SCHEMA_PATH = STATION_CONTROL_ROOT / "schemas" / "station-simulator-report.schema.json"
EXAMPLE_PATH = STATION_CONTROL_ROOT / "config_examples" / "simulator-scenario.example.json"

SPEC = importlib.util.spec_from_file_location("station_simulator", IMPLEMENTATION_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load station simulator module.")
SIMULATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SIMULATOR
SPEC.loader.exec_module(SIMULATOR)


class MiniSchemaError(AssertionError):
    pass


def validate_instance(instance: object, schema: dict[str, object], root: dict[str, object] | None = None) -> None:
    """Validate the schema keywords used by the two ST-003 schemas."""
    root = schema if root is None else root
    if "$ref" in schema:
        reference = str(schema["$ref"])
        if not reference.startswith("#/$defs/"):
            raise MiniSchemaError("remote reference")
        validate_instance(instance, root["$defs"][reference.split("/")[-1]], root)
        return
    if "const" in schema and instance != schema["const"]:
        raise MiniSchemaError("const")
    if "enum" in schema and instance not in schema["enum"]:
        raise MiniSchemaError("enum")
    expected_type = schema.get("type")
    if expected_type == "object":
        if type(instance) is not dict:
            raise MiniSchemaError("object")
        required = schema.get("required", [])
        if not set(required).issubset(instance):
            raise MiniSchemaError("required")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False and not set(instance).issubset(properties):
            raise MiniSchemaError("additionalProperties")
        if "maxProperties" in schema and len(instance) > schema["maxProperties"]:
            raise MiniSchemaError("maxProperties")
        for name, value in instance.items():
            if name in properties:
                validate_instance(value, properties[name], root)
    elif expected_type == "array":
        if type(instance) is not list:
            raise MiniSchemaError("array")
        if len(instance) < schema.get("minItems", 0) or len(instance) > schema.get("maxItems", sys.maxsize):
            raise MiniSchemaError("items length")
        for value in instance:
            validate_instance(value, schema["items"], root)
    elif expected_type == "string":
        if type(instance) is not str:
            raise MiniSchemaError("string")
        if len(instance) < schema.get("minLength", 0) or len(instance) > schema.get("maxLength", sys.maxsize):
            raise MiniSchemaError("string length")
        if "pattern" in schema and re.fullmatch(str(schema["pattern"]), instance) is None:
            raise MiniSchemaError("pattern")
    elif expected_type == "integer":
        if type(instance) is not int:
            raise MiniSchemaError("integer")
        if instance < schema.get("minimum", -sys.maxsize) or instance > schema.get("maximum", sys.maxsize):
            raise MiniSchemaError("integer range")
    elif expected_type == "boolean" and type(instance) is not bool:
        raise MiniSchemaError("boolean")
    if expected_type != "object" and type(instance) is dict:
        required = schema.get("required", [])
        if not set(required).issubset(instance):
            raise MiniSchemaError("required")
        for name, child_schema in schema.get("properties", {}).items():
            if name in instance:
                validate_instance(instance[name], child_schema, root)
    if "contains" in schema:
        if type(instance) is not list:
            raise MiniSchemaError("contains array")
        match_count = 0
        for value in instance:
            try:
                validate_instance(value, schema["contains"], root)
            except MiniSchemaError:
                continue
            match_count += 1
        if match_count < schema.get("minContains", 1) or match_count > schema.get("maxContains", sys.maxsize):
            raise MiniSchemaError("contains")
    if "allOf" in schema:
        for subschema in schema["allOf"]:
            validate_instance(instance, subschema, root)
    if "if" in schema:
        try:
            validate_instance(instance, schema["if"], root)
        except MiniSchemaError:
            if "else" in schema:
                validate_instance(instance, schema["else"], root)
        else:
            if "then" in schema:
                validate_instance(instance, schema["then"], root)


class StationSimulatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        self.scenario_schema = json.loads(SCENARIO_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.report_schema = json.loads(REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.temporary = tempfile.TemporaryDirectory(prefix="st003-test-")
        self.temp_root = Path(self.temporary.name)
        self.repository = self.temp_root / "repository"
        self.reports = self.temp_root / "reports"
        self.repository.mkdir()
        self.reports.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_events(self, events: list[dict[str, object]], mutate=None):
        scenario = copy.deepcopy(self.example)
        scenario["events"] = events
        if mutate is not None:
            mutate(scenario)
        return SIMULATOR.run_scenario(scenario)

    def mission_flow(self, final_event: str = "MISSION_START") -> list[dict[str, object]]:
        events = [
            {"tick": 0, "event_type": "MISSION_CREATE", "target_id": "MISSION-TEST-001",
             "payload": {"field_id": "FIELD-DEMO-001", "unit_id": "UNIT-DEMO-001"}},
        ]
        if final_event == "MISSION_CREATE":
            return events
        events.append({"tick": 1, "event_type": "MISSION_APPROVE", "target_id": "MISSION-TEST-001",
                       "payload": {"operator_approved": True}})
        if final_event == "MISSION_APPROVE":
            return events
        events.append({"tick": 2, "event_type": "MISSION_ASSIGN", "target_id": "MISSION-TEST-001",
                       "payload": {"rover_id": "ROVER-DEMO-001"}})
        if final_event == "MISSION_ASSIGN":
            return events
        events.append({"tick": 3, "event_type": "MISSION_START", "target_id": "MISSION-TEST-001", "payload": {}})
        return events

    def diagnostic_codes(self, report) -> set[str]:
        return {item["code"] for item in report.document["diagnostics"]}

    def test_scenario_parse(self) -> None:
        self.assertEqual(SIMULATOR.validate_scenario(self.example)["scenario_version"], 1)

    def test_scenario_schema_accepts_example(self) -> None:
        validate_instance(self.example, self.scenario_schema)

    def test_scenario_schema_rejects_duplicate_field_identity(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["fields"][1] = copy.deepcopy(scenario["fields"][0])
        with self.assertRaises(MiniSchemaError):
            validate_instance(scenario, self.scenario_schema)

    def test_scenario_schema_rejects_duplicate_rover_identity(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["rovers"][1] = copy.deepcopy(scenario["rovers"][0])
        with self.assertRaises(MiniSchemaError):
            validate_instance(scenario, self.scenario_schema)

    def test_example_has_two_fields(self) -> None:
        self.assertEqual(len(self.example["fields"]), 2)

    def test_example_has_three_rovers(self) -> None:
        self.assertEqual(len(self.example["rovers"]), 3)

    def test_fixed_field_ids(self) -> None:
        self.assertEqual({item["field_id"] for item in self.example["fields"]}, set(SIMULATOR.FIELD_IDS))

    def test_fixed_rover_ids(self) -> None:
        self.assertEqual({item["rover_id"] for item in self.example["rovers"]}, set(SIMULATOR.ROVER_IDS))

    def test_deterministic_event_processing(self) -> None:
        report = SIMULATOR.run_scenario(self.example)
        self.assertEqual([item["input_order"] for item in report.document["events_processed"]], list(range(11)))

    def test_same_tick_preserves_input_order(self) -> None:
        events = [
            {"tick": 1, "event_type": "BATTERY_SET", "target_id": "ROVER-DEMO-001", "payload": {"battery_percentage": 50}},
            {"tick": 1, "event_type": "BATTERY_DECREASE", "target_id": "ROVER-DEMO-001", "payload": {"amount": 5}},
        ]
        report = self.run_events(events)
        self.assertEqual(report.document["rovers"][0]["battery_percentage"], 45)

    def test_battery_update(self) -> None:
        event = [{"tick": 1, "event_type": "BATTERY_SET", "target_id": "ROVER-DEMO-001", "payload": {"battery_percentage": 55}}]
        self.assertEqual(self.run_events(event).document["rovers"][0]["battery_percentage"], 55)

    def test_battery_decrease(self) -> None:
        event = [{"tick": 1, "event_type": "BATTERY_DECREASE", "target_id": "ROVER-DEMO-001", "payload": {"amount": 15}}]
        self.assertEqual(self.run_events(event).document["rovers"][0]["battery_percentage"], 65)

    def test_rover_seen(self) -> None:
        event = [{"tick": 4, "event_type": "ROVER_SEEN", "target_id": "ROVER-DEMO-001", "payload": {}}]
        rover = self.run_events(event).document["rovers"][0]
        self.assertEqual(rover["last_seen_tick"], 4)
        self.assertTrue(rover["communication_available"])

    def test_mission_create(self) -> None:
        mission = self.run_events(self.mission_flow("MISSION_CREATE")).document["missions"][0]
        self.assertEqual(mission["state"], "DRAFT")

    def test_mission_approval(self) -> None:
        mission = self.run_events(self.mission_flow("MISSION_APPROVE")).document["missions"][0]
        self.assertTrue(mission["operator_approved"])
        self.assertEqual(mission["state"], "QUEUED")

    def test_mission_assignment(self) -> None:
        mission = self.run_events(self.mission_flow("MISSION_ASSIGN")).document["missions"][0]
        self.assertEqual(mission["assigned_rover_id"], "ROVER-DEMO-001")
        self.assertEqual(mission["state"], "ASSIGNED")

    def test_mission_start(self) -> None:
        report = self.run_events(self.mission_flow())
        self.assertEqual(report.document["missions"][0]["state"], "RUNNING")
        self.assertEqual(report.document["rovers"][0]["official_state"], "RUNNING")

    def test_mission_pause(self) -> None:
        events = self.mission_flow() + [
            {"tick": 4, "event_type": "MISSION_PAUSE", "target_id": "MISSION-TEST-001", "payload": {"reason": "operator review"}}
        ]
        self.assertEqual(self.run_events(events).document["missions"][0]["state"], "PAUSED")

    def test_mission_cancel(self) -> None:
        events = self.mission_flow() + [
            {"tick": 4, "event_type": "MISSION_CANCEL", "target_id": "MISSION-TEST-001", "payload": {"reason": "operator cancel"}}
        ]
        report = self.run_events(events)
        self.assertEqual(report.document["missions"][0]["state"], "CANCELLED")
        self.assertEqual(report.document["rovers"][0]["active_mission_id"], "")

    def test_return_request(self) -> None:
        event = [{"tick": 1, "event_type": "RETURN_REQUEST", "target_id": "ROVER-DEMO-001", "payload": {"reason": "operator return"}}]
        report = self.run_events(event)
        self.assertEqual(report.document["rovers"][0]["official_state"], "RETURNING")
        self.assertFalse(report.document["requests"][0]["direct_output_authority"])

    def test_stop_request_is_state_request(self) -> None:
        event = [{"tick": 1, "event_type": "STOP_REQUEST", "target_id": "ROVER-DEMO-001", "payload": {"reason": "operator stop"}}]
        report = self.run_events(event)
        self.assertEqual(report.document["rovers"][0]["official_state"], "STOPPED")
        self.assertEqual(report.document["requests"][0]["request_type"], "STOP_REQUEST")

    def test_charge_start(self) -> None:
        event = [{"tick": 1, "event_type": "CHARGE_START", "target_id": "ROVER-DEMO-001", "payload": {}}]
        self.assertEqual(self.run_events(event).document["rovers"][0]["official_state"], "CHARGING")

    def test_charge_complete(self) -> None:
        events = [
            {"tick": 1, "event_type": "CHARGE_START", "target_id": "ROVER-DEMO-001", "payload": {}},
            {"tick": 2, "event_type": "CHARGE_COMPLETE", "target_id": "ROVER-DEMO-001", "payload": {"battery_percentage": 95}},
        ]
        rover = self.run_events(events).document["rovers"][0]
        self.assertEqual((rover["official_state"], rover["battery_percentage"]), ("STOPPED", 95))

    def test_valid_field_switch(self) -> None:
        event = [{"tick": 1, "event_type": "FIELD_SWITCH_REQUEST", "target_id": "FIELD-DEMO-002", "payload": {"operator_confirmed": True}}]
        self.assertEqual(self.run_events(event).document["active_field_id"], "FIELD-DEMO-002")

    def test_json_property_order(self) -> None:
        expected = ["report_version", "phase", "scenario_id", "result", "tick_count", "active_field_id", "fields", "rovers", "missions", "events_processed", "requests", "diagnostics", "safety", "summary", "exit_code"]
        self.assertEqual(list(SIMULATOR.run_scenario(self.example).document), expected)

    def test_text_property_order(self) -> None:
        report = SIMULATOR.run_scenario(self.example)
        keys = [line.split("=", 1)[0] for line in SIMULATOR.render_text_report(report).splitlines()]
        self.assertEqual(keys, list(report.document))

    def test_report_schema_accepts_positive_report(self) -> None:
        validate_instance(SIMULATOR.run_scenario(self.example).document, self.report_schema)

    def test_two_runs_json_byte_identical(self) -> None:
        first = SIMULATOR.render_json_report(SIMULATOR.run_scenario(copy.deepcopy(self.example)))
        second = SIMULATOR.render_json_report(SIMULATOR.run_scenario(copy.deepcopy(self.example)))
        self.assertEqual(first.encode(), second.encode())

    def test_two_runs_text_byte_identical(self) -> None:
        first = SIMULATOR.render_text_report(SIMULATOR.run_scenario(copy.deepcopy(self.example)))
        second = SIMULATOR.render_text_report(SIMULATOR.run_scenario(copy.deepcopy(self.example)))
        self.assertEqual(first.encode(), second.encode())

    def test_network_false(self) -> None:
        self.assertFalse(SIMULATOR.run_scenario(self.example).document["safety"]["network_access_performed"])

    def test_gpio_false(self) -> None:
        self.assertFalse(SIMULATOR.run_scenario(self.example).document["safety"]["gpio_access_performed"])

    def test_hardware_output_false(self) -> None:
        self.assertFalse(SIMULATOR.run_scenario(self.example).document["safety"]["hardware_output_performed"])

    def test_motor_control_false(self) -> None:
        self.assertFalse(SIMULATOR.run_scenario(self.example).document["safety"]["motor_control_performed"])

    def test_charging_control_false(self) -> None:
        self.assertFalse(SIMULATOR.run_scenario(self.example).document["safety"]["charging_control_performed"])

    def test_rover_output_authority_false(self) -> None:
        self.assertFalse(SIMULATOR.run_scenario(self.example).document["safety"]["rover_output_authority"])

    def test_physical_estop_independent(self) -> None:
        self.assertTrue(SIMULATOR.run_scenario(self.example).document["safety"]["physical_estop_independent"])

    def test_automatic_resume_false(self) -> None:
        self.assertFalse(SIMULATOR.run_scenario(self.example).document["safety"]["automatic_resume_performed"])

    def test_automatic_arm_false(self) -> None:
        self.assertFalse(SIMULATOR.run_scenario(self.example).document["safety"]["automatic_arm_performed"])

    def test_invalid_scenario_version(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["scenario_version"] = 2
        with self.assertRaises(SIMULATOR.ScenarioError):
            SIMULATOR.validate_scenario(scenario)

    def test_duplicate_field_id(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["fields"][1]["field_id"] = "FIELD-DEMO-001"
        with self.assertRaisesRegex(SIMULATOR.ScenarioError, "Duplicate field"):
            SIMULATOR.validate_scenario(scenario)

    def test_duplicate_rover_id(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["rovers"][1]["rover_id"] = "ROVER-DEMO-001"
        with self.assertRaisesRegex(SIMULATOR.ScenarioError, "Duplicate rover"):
            SIMULATOR.validate_scenario(scenario)

    def test_unknown_field(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["rovers"][0]["current_field_id"] = "FIELD-UNKNOWN-001"
        with self.assertRaisesRegex(SIMULATOR.ScenarioError, "unknown field"):
            SIMULATOR.validate_scenario(scenario)

    def test_unknown_rover(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["events"][4]["target_id"] = "ROVER-UNKNOWN-001"
        with self.assertRaisesRegex(SIMULATOR.ScenarioError, "unknown rover"):
            SIMULATOR.validate_scenario(scenario)

    def test_invalid_battery(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["rovers"][0]["battery_percentage"] = 101
        with self.assertRaises(SIMULATOR.ScenarioError):
            SIMULATOR.validate_scenario(scenario)

    def test_invalid_mission_state(self) -> None:
        report = SIMULATOR.run_scenario(self.example).document
        report["missions"][0]["state"] = "AUTO_RESUMED"
        with self.assertRaises(MiniSchemaError):
            validate_instance(report, self.report_schema)

    def test_mission_state_exact_set(self) -> None:
        expected = ("DRAFT", "WAITING_APPROVAL", "QUEUED", "ASSIGNED", "RUNNING", "PAUSED", "RETURNING", "CHARGING", "COMPLETED", "FAILED", "CANCELLED", "EXPIRED")
        self.assertEqual(SIMULATOR.MISSION_STATES, expected)

    def test_invalid_event_type(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["events"][0]["event_type"] = "AUTO_ARM"
        with self.assertRaisesRegex(SIMULATOR.ScenarioError, "Event type"):
            SIMULATOR.validate_scenario(scenario)

    def test_event_tick_reverse(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["events"][2]["tick"] = 0
        with self.assertRaisesRegex(SIMULATOR.ScenarioError, "nondecreasing"):
            SIMULATOR.validate_scenario(scenario)

    def test_start_without_approval(self) -> None:
        events = [self.mission_flow("MISSION_CREATE")[0],
                  {"tick": 1, "event_type": "MISSION_ASSIGN", "target_id": "MISSION-TEST-001", "payload": {"rover_id": "ROVER-DEMO-001"}},
                  {"tick": 2, "event_type": "MISSION_START", "target_id": "MISSION-TEST-001", "payload": {}}]
        self.assertIn("MISSION_START_REJECTED", self.diagnostic_codes(self.run_events(events)))

    def test_start_with_fault(self) -> None:
        def mutate(scenario):
            scenario["rovers"][0]["fault"] = "SIMULATED_FAULT"
        self.assertIn("MISSION_START_REJECTED", self.diagnostic_codes(self.run_events(self.mission_flow(), mutate)))

    def test_start_with_battery_below_reserve(self) -> None:
        def mutate(scenario):
            scenario["rovers"][0]["battery_percentage"] = 19
        report = self.run_events(self.mission_flow(), mutate)
        self.assertIn("MISSION_START_REJECTED", self.diagnostic_codes(report))

    def test_start_with_unit_mismatch(self) -> None:
        def mutate(scenario):
            scenario["rovers"][0]["current_unit_id"] = "UNIT-DEMO-999"
        self.assertIn("MISSION_START_REJECTED", self.diagnostic_codes(self.run_events(self.mission_flow(), mutate)))

    def test_start_on_wrong_field(self) -> None:
        events = self.mission_flow()
        events[0]["payload"]["field_id"] = "FIELD-DEMO-002"
        self.assertIn("MISSION_START_REJECTED", self.diagnostic_codes(self.run_events(events)))

    def test_field_switch_while_running(self) -> None:
        events = self.mission_flow() + [{"tick": 4, "event_type": "FIELD_SWITCH_REQUEST", "target_id": "FIELD-DEMO-002", "payload": {"operator_confirmed": True}}]
        self.assertIn("FIELD_SWITCH_REJECTED", self.diagnostic_codes(self.run_events(events)))

    def test_field_switch_while_charging(self) -> None:
        events = [{"tick": 1, "event_type": "CHARGE_START", "target_id": "ROVER-DEMO-001", "payload": {}},
                  {"tick": 2, "event_type": "FIELD_SWITCH_REQUEST", "target_id": "FIELD-DEMO-002", "payload": {"operator_confirmed": True}}]
        self.assertIn("FIELD_SWITCH_REJECTED", self.diagnostic_codes(self.run_events(events)))

    def test_field_switch_with_paused_active_mission(self) -> None:
        events = self.mission_flow() + [
            {"tick": 4, "event_type": "MISSION_PAUSE", "target_id": "MISSION-TEST-001", "payload": {"reason": "review"}},
            {"tick": 5, "event_type": "FIELD_SWITCH_REQUEST", "target_id": "FIELD-DEMO-002", "payload": {"operator_confirmed": True}},
        ]
        self.assertIn("FIELD_SWITCH_REJECTED", self.diagnostic_codes(self.run_events(events)))

    def test_communication_loss_pauses_mission(self) -> None:
        events = self.mission_flow() + [{"tick": 4, "event_type": "COMMUNICATION_LOST", "target_id": "ROVER-DEMO-001", "payload": {}}]
        self.assertEqual(self.run_events(events).document["missions"][0]["state"], "PAUSED")

    def test_restore_does_not_auto_resume(self) -> None:
        events = self.mission_flow() + [
            {"tick": 4, "event_type": "COMMUNICATION_LOST", "target_id": "ROVER-DEMO-001", "payload": {}},
            {"tick": 5, "event_type": "COMMUNICATION_RESTORED", "target_id": "ROVER-DEMO-001", "payload": {}},
        ]
        self.assertEqual(self.run_events(events).document["missions"][0]["state"], "PAUSED")

    def test_station_restart_does_not_auto_resume(self) -> None:
        events = self.mission_flow() + [{"tick": 4, "event_type": "STATION_RESTART", "target_id": "STATION", "payload": {}}]
        report = self.run_events(events)
        self.assertEqual(report.document["missions"][0]["state"], "PAUSED")
        self.assertIn("STATION_RESTART_NO_AUTO_RESUME", self.diagnostic_codes(report))

    def test_timeout_pauses_mission(self) -> None:
        events = self.mission_flow() + [{"tick": 9, "event_type": "BATTERY_SET", "target_id": "ROVER-DEMO-002", "payload": {"battery_percentage": 70}}]
        report = self.run_events(events)
        self.assertEqual(report.document["missions"][0]["state"], "PAUSED")
        self.assertIn("COMMUNICATION_TIMEOUT", self.diagnostic_codes(report))

    def test_timeout_boundary_five_does_not_timeout(self) -> None:
        event = [{"tick": 5, "event_type": "BATTERY_SET", "target_id": "ROVER-DEMO-001", "payload": {"battery_percentage": 70}}]
        self.assertNotIn("COMMUNICATION_TIMEOUT", self.diagnostic_codes(self.run_events(event)))

    def test_battery_zero_handling(self) -> None:
        events = self.mission_flow() + [{"tick": 4, "event_type": "BATTERY_SET", "target_id": "ROVER-DEMO-001", "payload": {"battery_percentage": 0}}]
        report = self.run_events(events)
        self.assertEqual(report.document["rovers"][0]["official_state"], "STOPPED")
        self.assertEqual(report.document["missions"][0]["state"], "PAUSED")

    def test_battery_below_reserve_diagnostic(self) -> None:
        event = [{"tick": 1, "event_type": "BATTERY_SET", "target_id": "ROVER-DEMO-001", "payload": {"battery_percentage": 19}}]
        self.assertIn("BATTERY_BELOW_RESERVE", self.diagnostic_codes(self.run_events(event)))

    def test_repository_report_path_rejected(self) -> None:
        arguments = SIMULATOR.CliArguments(self.repository, EXAMPLE_PATH, self.repository / "report.json", self.reports / "report.txt")
        self.assertIn("Report paths must be outside", " ".join(SIMULATOR.validate_cli_arguments(arguments)))

    def test_unexpected_internal_exception(self) -> None:
        arguments = ["--repository-root", str(self.repository), "--scenario", str(EXAMPLE_PATH),
                     "--json-report", str(self.reports / "report.json"), "--text-report", str(self.reports / "report.txt")]
        with mock.patch.object(SIMULATOR, "execute", side_effect=RuntimeError("private detail")):
            with redirect_stderr(io.StringIO()) as output:
                code = SIMULATOR.main(arguments)
        self.assertEqual(code, 7)
        self.assertNotIn("private detail", output.getvalue())

    def test_strict_json_rejects_unknown_root_property(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["unexpected"] = True
        with self.assertRaises(SIMULATOR.ScenarioError):
            SIMULATOR.validate_scenario(scenario)

    def test_strict_json_rejects_unknown_payload_property(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["events"][3]["payload"]["automatic_arm"] = True
        with self.assertRaises(SIMULATOR.ScenarioError):
            SIMULATOR.validate_scenario(scenario)

    def test_boolean_is_not_integer_battery(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["rovers"][0]["battery_percentage"] = True
        with self.assertRaises(SIMULATOR.ScenarioError):
            SIMULATOR.validate_scenario(scenario)

    def test_boundary_coordinate_rejected(self) -> None:
        scenario = copy.deepcopy(self.example)
        scenario["fields"][0]["boundary_reference"] = "local-reference:35.1,139.2"
        with self.assertRaises(SIMULATOR.ScenarioError):
            SIMULATOR.validate_scenario(scenario)

    def test_reports_contain_no_null(self) -> None:
        rendered = SIMULATOR.render_json_report(SIMULATOR.run_scenario(self.example))
        self.assertNotIn("null", rendered)

    def test_reports_contain_no_timestamp(self) -> None:
        rendered = SIMULATOR.render_json_report(SIMULATOR.run_scenario(self.example)).casefold()
        self.assertNotIn("timestamp", rendered)
        self.assertNotIn("current_time", rendered)

    def test_reports_contain_no_absolute_path(self) -> None:
        rendered = SIMULATOR.render_json_report(SIMULATOR.run_scenario(self.example))
        self.assertNotIn(str(STATION_CONTROL_ROOT), rendered)

    def test_diagnostics_have_fixed_sort_order(self) -> None:
        diagnostics = SIMULATOR.run_scenario(self.example).document["diagnostics"]
        expected = sorted(diagnostics, key=lambda item: (item["tick"], item["severity"], item["code"], item["target_id"], item["message"]))
        self.assertEqual(diagnostics, expected)

    def test_formal_positive_result_pass(self) -> None:
        self.assertEqual(SIMULATOR.run_scenario(self.example).document["result"], "PASS")

    def test_formal_positive_field_switches(self) -> None:
        self.assertEqual(SIMULATOR.run_scenario(self.example).document["active_field_id"], "FIELD-DEMO-002")

    def test_formal_positive_mission_completes(self) -> None:
        self.assertEqual(SIMULATOR.run_scenario(self.example).document["missions"][0]["state"], "COMPLETED")

    def test_formal_positive_includes_paused_trace(self) -> None:
        codes = self.diagnostic_codes(SIMULATOR.run_scenario(self.example))
        self.assertIn("MISSION_PAUSED_COMMUNICATION_LOSS", codes)

    def test_source_uses_only_allowed_standard_library_imports(self) -> None:
        tree = ast.parse(IMPLEMENTATION_PATH.read_text(encoding="utf-8"))
        imports = {node.names[0].name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)}
        imports |= {str(node.module).split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module != "__future__"}
        self.assertEqual(imports, {"argparse", "copy", "json", "os", "dataclasses", "pathlib", "re", "sys", "typing"})

    def test_source_has_no_forbidden_runtime_calls(self) -> None:
        tree = ast.parse(IMPLEMENTATION_PATH.read_text(encoding="utf-8"))
        identifiers = {node.id.casefold() for node in ast.walk(tree) if isinstance(node, ast.Name)}
        attributes = {node.attr.casefold() for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        forbidden = {"socket", "mqtt", "gpio", "serial", "subprocess", "sqlite3", "random", "datetime"}
        self.assertTrue(forbidden.isdisjoint(identifiers | attributes))

    def test_schema_refs_are_local_only(self) -> None:
        for schema in (self.scenario_schema, self.report_schema):
            refs: list[str] = []
            def visit(value):
                if isinstance(value, dict):
                    if "$ref" in value:
                        refs.append(value["$ref"])
                    for child in value.values():
                        visit(child)
                elif isinstance(value, list):
                    for child in value:
                        visit(child)
            visit(schema)
            self.assertTrue(all(item.startswith("#/$defs/") for item in refs))

    def test_schema_roots_disallow_additional_properties(self) -> None:
        self.assertFalse(self.scenario_schema["additionalProperties"])
        self.assertFalse(self.report_schema["additionalProperties"])

    def test_report_write_is_external_and_utf8(self) -> None:
        scenario_path = self.temp_root / "scenario.json"
        scenario_path.write_text(json.dumps(self.example), encoding="utf-8")
        arguments = SIMULATOR.CliArguments(self.repository, scenario_path, self.reports / "report.json", self.reports / "report.txt")
        report = SIMULATOR.execute(arguments)
        self.assertEqual((self.reports / "report.json").read_text(encoding="utf-8"), SIMULATOR.render_json_report(report))


if __name__ == "__main__":
    unittest.main(verbosity=2)
