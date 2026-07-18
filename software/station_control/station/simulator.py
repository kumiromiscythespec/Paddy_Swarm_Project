"""Deterministic, offline-only station simulator for phase ST-003."""

from __future__ import annotations

import argparse
import copy
import json
import os
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Sequence


REPORT_VERSION = 1
PHASE = "ST-003"
SCENARIO_VERSION = 1
BATTERY_RESERVE_MINIMUM = 20
COMMUNICATION_TIMEOUT_TICKS = 5
FIELD_IDS = ("FIELD-DEMO-001", "FIELD-DEMO-002")
ROVER_IDS = ("ROVER-DEMO-001", "ROVER-DEMO-002", "ROVER-DEMO-003")
MISSION_STATES = (
    "DRAFT", "WAITING_APPROVAL", "QUEUED", "ASSIGNED", "RUNNING", "PAUSED",
    "RETURNING", "CHARGING", "COMPLETED", "FAILED", "CANCELLED", "EXPIRED",
)
ROVER_STATES = ("STOPPED", "RUNNING", "RETURNING", "CHARGING")
EVENT_TYPES = (
    "BATTERY_SET", "BATTERY_DECREASE", "ROVER_SEEN", "COMMUNICATION_LOST",
    "COMMUNICATION_RESTORED", "FAULT_SET", "FAULT_CLEAR", "STOP_REQUEST",
    "RETURN_REQUEST", "MISSION_CREATE", "MISSION_APPROVE", "MISSION_ASSIGN",
    "MISSION_START", "MISSION_PAUSE", "MISSION_CANCEL", "CHARGE_START",
    "CHARGE_COMPLETE", "FIELD_SWITCH_REQUEST", "STATION_RESTART",
)
TERMINAL_MISSION_STATES = ("COMPLETED", "FAILED", "CANCELLED", "EXPIRED")
IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{2,63}$")


class ScenarioError(ValueError):
    """A deterministic scenario validation error."""


@dataclass(frozen=True)
class CliArguments:
    repository_root: Path
    scenario: Path
    json_report: Path
    text_report: Path


@dataclass(frozen=True)
class SimulationReport:
    document: dict[str, object]
    exit_code: int


class DeterministicArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def parse_arguments(argv: Sequence[str] | None = None) -> CliArguments:
    parser = DeterministicArgumentParser(
        description="Run the deterministic offline ST-003 station simulator."
    )
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--scenario", required=True, type=Path)
    parser.add_argument("--json-report", required=True, type=Path)
    parser.add_argument("--text-report", required=True, type=Path)
    values = parser.parse_args(argv)
    return CliArguments(
        repository_root=values.repository_root,
        scenario=values.scenario,
        json_report=values.json_report,
        text_report=values.text_report,
    )


def is_path_contained(candidate: Path, parent: Path) -> bool:
    try:
        child = candidate.resolve(strict=False)
        root = parent.resolve(strict=False)
        common = os.path.commonpath((str(child), str(root)))
    except (OSError, ValueError):
        return False
    return os.path.normcase(common) == os.path.normcase(str(root))


def validate_cli_arguments(arguments: CliArguments) -> tuple[str, ...]:
    errors: list[str] = []
    if not arguments.repository_root.is_dir():
        errors.append("Repository root must be an existing directory.")
    if not arguments.scenario.is_file():
        errors.append("Scenario must be an existing regular file.")
    for report in (arguments.json_report, arguments.text_report):
        if is_path_contained(report, arguments.repository_root):
            errors.append("Report paths must be outside the repository.")
        if not report.parent.is_dir():
            errors.append("Report parent must be an existing directory.")
    if arguments.json_report.resolve(strict=False) == arguments.text_report.resolve(
        strict=False
    ):
        errors.append("JSON and text reports must use different paths.")
    return tuple(sorted(set(errors)))


def _exact_keys(value: object, keys: set[str], context: str) -> dict[str, object]:
    if type(value) is not dict:
        raise ScenarioError(f"{context} must be an object.")
    actual = set(value)
    if actual != keys:
        raise ScenarioError(f"{context} properties are invalid.")
    return value


def _string(value: object, context: str) -> str:
    if type(value) is not str or not value:
        raise ScenarioError(f"{context} must be a non-empty string.")
    return value


def _identifier(value: object, context: str) -> str:
    result = _string(value, context)
    if not IDENTIFIER_PATTERN.fullmatch(result):
        raise ScenarioError(f"{context} is not a valid logical identifier.")
    return result


def _integer(value: object, minimum: int, maximum: int, context: str) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ScenarioError(f"{context} must be an integer from {minimum} to {maximum}.")
    return value


def _boolean(value: object, context: str) -> bool:
    if type(value) is not bool:
        raise ScenarioError(f"{context} must be a boolean.")
    return value


def _validate_payload(event_type: str, payload: object, context: str) -> dict[str, object]:
    keys_by_type = {
        "BATTERY_SET": {"battery_percentage"},
        "BATTERY_DECREASE": {"amount"},
        "ROVER_SEEN": set(),
        "COMMUNICATION_LOST": set(),
        "COMMUNICATION_RESTORED": set(),
        "FAULT_SET": {"fault"},
        "FAULT_CLEAR": set(),
        "STOP_REQUEST": {"reason"},
        "RETURN_REQUEST": {"reason"},
        "MISSION_CREATE": {"field_id", "unit_id"},
        "MISSION_APPROVE": {"operator_approved"},
        "MISSION_ASSIGN": {"rover_id"},
        "MISSION_START": set(),
        "MISSION_PAUSE": {"reason"},
        "MISSION_CANCEL": {"reason"},
        "CHARGE_START": set(),
        "CHARGE_COMPLETE": {"battery_percentage"},
        "FIELD_SWITCH_REQUEST": {"operator_confirmed"},
        "STATION_RESTART": set(),
    }
    result = _exact_keys(payload, keys_by_type[event_type], context)
    if event_type in ("BATTERY_SET", "CHARGE_COMPLETE"):
        _integer(result["battery_percentage"], 0, 100, f"{context}.battery_percentage")
    elif event_type == "BATTERY_DECREASE":
        _integer(result["amount"], 0, 100, f"{context}.amount")
    elif event_type == "FAULT_SET":
        _string(result["fault"], f"{context}.fault")
    elif event_type in ("STOP_REQUEST", "RETURN_REQUEST", "MISSION_PAUSE", "MISSION_CANCEL"):
        _string(result["reason"], f"{context}.reason")
    elif event_type == "MISSION_CREATE":
        _identifier(result["field_id"], f"{context}.field_id")
        _identifier(result["unit_id"], f"{context}.unit_id")
    elif event_type == "MISSION_APPROVE":
        if _boolean(result["operator_approved"], f"{context}.operator_approved") is not True:
            raise ScenarioError("Mission approval must be explicitly true.")
    elif event_type == "MISSION_ASSIGN":
        _identifier(result["rover_id"], f"{context}.rover_id")
    elif event_type == "FIELD_SWITCH_REQUEST":
        if _boolean(result["operator_confirmed"], f"{context}.operator_confirmed") is not True:
            raise ScenarioError("Field switch requires explicit operator confirmation.")
    return result


def validate_scenario(value: object) -> dict[str, object]:
    scenario = _exact_keys(
        value,
        {"scenario_version", "scenario_id", "active_field_id", "fields", "rovers", "events"},
        "scenario",
    )
    if type(scenario["scenario_version"]) is not int or scenario["scenario_version"] != 1:
        raise ScenarioError("Scenario version must be 1.")
    _identifier(scenario["scenario_id"], "scenario.scenario_id")
    active_field = _identifier(scenario["active_field_id"], "scenario.active_field_id")

    fields_value = scenario["fields"]
    if type(fields_value) is not list or len(fields_value) != 2:
        raise ScenarioError("Scenario must define exactly two fields.")
    seen_fields: set[str] = set()
    expected_names = {"FIELD-DEMO-001": "Field 1", "FIELD-DEMO-002": "Field 2"}
    for index, item in enumerate(fields_value):
        field = _exact_keys(item, {"field_id", "display_name", "boundary_reference"}, f"fields[{index}]")
        field_id = _identifier(field["field_id"], f"fields[{index}].field_id")
        if field_id in seen_fields:
            raise ScenarioError("Duplicate field ID.")
        seen_fields.add(field_id)
        if field_id not in expected_names or field["display_name"] != expected_names[field_id]:
            raise ScenarioError("Dummy field identity or display name is invalid.")
        boundary = _string(field["boundary_reference"], f"fields[{index}].boundary_reference")
        if not boundary.startswith("local-reference:") or re.search(r"[-+]?\d+\.\d+\s*[,/]\s*[-+]?\d+\.\d+", boundary):
            raise ScenarioError("Boundary must be an abstract local reference without coordinates.")
    if seen_fields != set(FIELD_IDS) or active_field not in seen_fields:
        raise ScenarioError("Field set or active field is invalid.")

    rovers_value = scenario["rovers"]
    if type(rovers_value) is not list or len(rovers_value) != 3:
        raise ScenarioError("Scenario must define exactly three rovers.")
    seen_rovers: set[str] = set()
    for index, item in enumerate(rovers_value):
        rover = _exact_keys(
            item,
            {"rover_id", "current_field_id", "current_unit_id", "official_state",
             "battery_percentage", "last_seen_tick", "fault", "active_mission_id",
             "communication_available"},
            f"rovers[{index}]",
        )
        rover_id = _identifier(rover["rover_id"], f"rovers[{index}].rover_id")
        if rover_id in seen_rovers:
            raise ScenarioError("Duplicate rover ID.")
        seen_rovers.add(rover_id)
        if rover["current_field_id"] not in seen_fields:
            raise ScenarioError("Rover references an unknown field.")
        _identifier(rover["current_unit_id"], f"rovers[{index}].current_unit_id")
        if rover["official_state"] not in ROVER_STATES:
            raise ScenarioError("Rover official state is invalid.")
        _integer(rover["battery_percentage"], 0, 100, f"rovers[{index}].battery_percentage")
        _integer(rover["last_seen_tick"], 0, 2147483647, f"rovers[{index}].last_seen_tick")
        if type(rover["fault"]) is not str or type(rover["active_mission_id"]) is not str:
            raise ScenarioError("Rover fault and active mission must be strings.")
        _boolean(rover["communication_available"], f"rovers[{index}].communication_available")
    if seen_rovers != set(ROVER_IDS):
        raise ScenarioError("Dummy rover set is invalid.")

    events_value = scenario["events"]
    if type(events_value) is not list:
        raise ScenarioError("Events must be an array.")
    previous_tick = -1
    for index, item in enumerate(events_value):
        event = _exact_keys(item, {"tick", "event_type", "target_id", "payload"}, f"events[{index}]")
        tick = _integer(event["tick"], 0, 2147483647, f"events[{index}].tick")
        if tick < previous_tick:
            raise ScenarioError("Event ticks must be nondecreasing.")
        previous_tick = tick
        event_type = _string(event["event_type"], f"events[{index}].event_type")
        if event_type not in EVENT_TYPES:
            raise ScenarioError("Event type is invalid.")
        target_id = _identifier(event["target_id"], f"events[{index}].target_id")
        if event_type in ("BATTERY_SET", "BATTERY_DECREASE", "ROVER_SEEN", "COMMUNICATION_LOST",
                          "COMMUNICATION_RESTORED", "FAULT_SET", "FAULT_CLEAR", "STOP_REQUEST",
                          "RETURN_REQUEST", "CHARGE_START", "CHARGE_COMPLETE") and target_id not in seen_rovers:
            raise ScenarioError("Event references an unknown rover.")
        if event_type == "FIELD_SWITCH_REQUEST" and target_id not in seen_fields:
            raise ScenarioError("Field switch references an unknown field.")
        _validate_payload(event_type, event["payload"], f"events[{index}].payload")
    return copy.deepcopy(scenario)


def load_scenario(path: Path) -> dict[str, object]:
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            value = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ScenarioError("Scenario is not readable strict JSON.") from exc
    return validate_scenario(value)


class Simulator:
    def __init__(self, scenario: dict[str, object]) -> None:
        self.scenario = scenario
        self.active_field_id = str(scenario["active_field_id"])
        self.fields = copy.deepcopy(scenario["fields"])
        self.rovers = {str(item["rover_id"]): copy.deepcopy(item) for item in scenario["rovers"]}
        self.missions: dict[str, dict[str, object]] = {}
        self.events_processed: list[dict[str, object]] = []
        self.requests: list[dict[str, object]] = []
        self.diagnostics: list[dict[str, object]] = []
        self.current_tick = 0

    def diagnostic(self, severity: str, code: str, target_id: str, message: str) -> None:
        self.diagnostics.append({
            "severity": severity,
            "code": code,
            "tick": self.current_tick,
            "target_id": target_id,
            "message": message,
        })

    def reject(self, code: str, target_id: str, message: str) -> str:
        self.diagnostic("ERROR", code, target_id, message)
        return message

    def pause_mission(self, rover: dict[str, object], code: str, message: str) -> None:
        mission_id = str(rover["active_mission_id"])
        if mission_id and mission_id in self.missions:
            mission = self.missions[mission_id]
            if mission["state"] in ("RUNNING", "RETURNING", "CHARGING"):
                mission["state"] = "PAUSED"
                rover["official_state"] = "STOPPED"
                self.diagnostic("WARNING", code, str(rover["rover_id"]), message)

    def apply_timeouts(self) -> None:
        for rover_id in sorted(self.rovers):
            rover = self.rovers[rover_id]
            if (rover["communication_available"] and
                    self.current_tick - int(rover["last_seen_tick"]) > COMMUNICATION_TIMEOUT_TICKS):
                rover["communication_available"] = False
                self.diagnostic(
                    "WARNING", "COMMUNICATION_TIMEOUT", rover_id,
                    "Communication timed out after more than 5 ticks.",
                )
                self.pause_mission(
                    rover, "MISSION_PAUSED_COMMUNICATION_TIMEOUT",
                    "Running mission paused after communication timeout.",
                )

    def mission(self, mission_id: str) -> dict[str, object] | None:
        mission = self.missions.get(mission_id)
        if mission is None:
            self.reject("MISSION_UNKNOWN", mission_id, "Mission does not exist.")
        return mission

    def record_request(self, request_type: str, target_id: str, accepted: bool, reason: str) -> None:
        self.requests.append({
            "tick": self.current_tick,
            "request_type": request_type,
            "target_id": target_id,
            "accepted": accepted,
            "reason": reason,
            "direct_output_authority": False,
        })

    def handle_rover_event(self, event_type: str, rover_id: str, payload: dict[str, object]) -> tuple[bool, str]:
        rover = self.rovers[rover_id]
        if event_type == "BATTERY_SET":
            rover["battery_percentage"] = payload["battery_percentage"]
        elif event_type == "BATTERY_DECREASE":
            rover["battery_percentage"] = max(0, int(rover["battery_percentage"]) - int(payload["amount"]))
        elif event_type == "ROVER_SEEN":
            rover["last_seen_tick"] = self.current_tick
            rover["communication_available"] = True
        elif event_type == "COMMUNICATION_LOST":
            rover["communication_available"] = False
            self.diagnostic("WARNING", "COMMUNICATION_LOST", rover_id, "Communication became unavailable.")
            self.pause_mission(rover, "MISSION_PAUSED_COMMUNICATION_LOSS", "Running mission paused after communication loss.")
        elif event_type == "COMMUNICATION_RESTORED":
            rover["communication_available"] = True
            rover["last_seen_tick"] = self.current_tick
            self.diagnostic("INFO", "COMMUNICATION_RESTORED_NO_AUTO_RESUME", rover_id, "Communication restored; mission remains paused.")
        elif event_type == "FAULT_SET":
            rover["fault"] = payload["fault"]
            self.pause_mission(rover, "MISSION_PAUSED_FAULT", "Active mission paused after a fault.")
        elif event_type == "FAULT_CLEAR":
            rover["fault"] = ""
        elif event_type == "STOP_REQUEST":
            self.record_request("STOP_REQUEST", rover_id, True, str(payload["reason"]))
            self.pause_mission(rover, "MISSION_PAUSED_STOP_REQUEST", "Mission paused by a recorded STOP state request.")
            rover["official_state"] = "STOPPED"
        elif event_type == "RETURN_REQUEST":
            accepted = bool(rover["communication_available"]) and not bool(rover["fault"])
            reason = str(payload["reason"]) if accepted else "Return request blocked by communication or fault state."
            self.record_request("RETURN_REQUEST", rover_id, accepted, reason)
            if not accepted:
                return False, self.reject("RETURN_REQUEST_REJECTED", rover_id, reason)
            rover["official_state"] = "RETURNING"
            mission_id = str(rover["active_mission_id"])
            if mission_id in self.missions:
                self.missions[mission_id]["state"] = "RETURNING"
        elif event_type == "CHARGE_START":
            if rover["official_state"] == "RUNNING":
                return False, self.reject("CHARGE_START_REJECTED", rover_id, "Charging simulation cannot start while rover is running.")
            rover["official_state"] = "CHARGING"
            mission_id = str(rover["active_mission_id"])
            if mission_id in self.missions:
                self.missions[mission_id]["state"] = "CHARGING"
        elif event_type == "CHARGE_COMPLETE":
            if rover["official_state"] != "CHARGING":
                return False, self.reject("CHARGE_COMPLETE_REJECTED", rover_id, "Rover is not in charging transition.")
            rover["battery_percentage"] = payload["battery_percentage"]
            rover["official_state"] = "STOPPED"
            mission_id = str(rover["active_mission_id"])
            if mission_id in self.missions:
                self.missions[mission_id]["state"] = "COMPLETED"
            rover["active_mission_id"] = ""
        self.apply_battery_policy(rover)
        return True, "accepted"

    def apply_battery_policy(self, rover: dict[str, object]) -> None:
        battery = int(rover["battery_percentage"])
        rover_id = str(rover["rover_id"])
        if battery == 0:
            rover["official_state"] = "STOPPED"
            self.pause_mission(rover, "MISSION_PAUSED_BATTERY_ZERO", "Active mission paused at zero battery.")
            self.diagnostic("ERROR", "BATTERY_ZERO_SAFE_STATE", rover_id, "Battery is zero; rover retained in safe stopped state.")
        elif battery < BATTERY_RESERVE_MINIMUM:
            self.diagnostic("WARNING", "BATTERY_BELOW_RESERVE", rover_id, "Battery is below reserve; RETURNING is a request candidate.")

    def handle_mission_event(self, event_type: str, mission_id: str, payload: dict[str, object]) -> tuple[bool, str]:
        if event_type == "MISSION_CREATE":
            if mission_id in self.missions:
                return False, self.reject("MISSION_DUPLICATE", mission_id, "Mission already exists.")
            if payload["field_id"] not in FIELD_IDS:
                return False, self.reject("MISSION_FIELD_UNKNOWN", mission_id, "Mission field is unknown.")
            self.missions[mission_id] = {
                "mission_id": mission_id,
                "field_id": payload["field_id"],
                "required_unit_id": payload["unit_id"],
                "assigned_rover_id": "",
                "state": "DRAFT",
                "operator_approved": False,
                "automatic_resume_allowed": False,
            }
            return True, "accepted"
        mission = self.mission(mission_id)
        if mission is None:
            return False, "Mission does not exist."
        if event_type == "MISSION_APPROVE":
            if mission["state"] not in ("DRAFT", "WAITING_APPROVAL"):
                return False, self.reject("MISSION_APPROVAL_REJECTED", mission_id, "Mission is not awaiting approval.")
            mission["operator_approved"] = True
            mission["state"] = "QUEUED"
        elif event_type == "MISSION_ASSIGN":
            rover_id = str(payload["rover_id"])
            if rover_id not in self.rovers:
                return False, self.reject("MISSION_ROVER_UNKNOWN", mission_id, "Assigned rover is unknown.")
            if mission["state"] not in ("DRAFT", "WAITING_APPROVAL", "QUEUED", "ASSIGNED"):
                return False, self.reject("MISSION_ASSIGN_REJECTED", mission_id, "Mission cannot be assigned in its current state.")
            old_id = str(mission["assigned_rover_id"])
            if old_id and self.rovers[old_id]["active_mission_id"] == mission_id:
                self.rovers[old_id]["active_mission_id"] = ""
            mission["assigned_rover_id"] = rover_id
            mission["state"] = "ASSIGNED"
            self.rovers[rover_id]["active_mission_id"] = mission_id
        elif event_type == "MISSION_START":
            reason = self.start_gate_reason(mission)
            if reason:
                return False, self.reject("MISSION_START_REJECTED", mission_id, reason)
            rover = self.rovers[str(mission["assigned_rover_id"])]
            mission["state"] = "RUNNING"
            rover["official_state"] = "RUNNING"
        elif event_type == "MISSION_PAUSE":
            if mission["state"] not in ("RUNNING", "RETURNING", "CHARGING"):
                return False, self.reject("MISSION_PAUSE_REJECTED", mission_id, "Mission is not active.")
            mission["state"] = "PAUSED"
            rover_id = str(mission["assigned_rover_id"])
            if rover_id:
                self.rovers[rover_id]["official_state"] = "STOPPED"
        elif event_type == "MISSION_CANCEL":
            if mission["state"] in TERMINAL_MISSION_STATES:
                return False, self.reject("MISSION_CANCEL_REJECTED", mission_id, "Mission is already terminal.")
            mission["state"] = "CANCELLED"
            rover_id = str(mission["assigned_rover_id"])
            if rover_id:
                self.rovers[rover_id]["official_state"] = "STOPPED"
                self.rovers[rover_id]["active_mission_id"] = ""
        return True, "accepted"

    def start_gate_reason(self, mission: dict[str, object]) -> str:
        if not mission["operator_approved"]:
            return "Operator approval is required."
        rover_id = str(mission["assigned_rover_id"])
        if not rover_id:
            return "Mission requires an assigned rover."
        rover = self.rovers[rover_id]
        if rover["fault"]:
            return "Mission cannot start while a fault is active."
        if int(rover["battery_percentage"]) < BATTERY_RESERVE_MINIMUM:
            return "Mission cannot start below the battery reserve minimum."
        if rover["current_unit_id"] != mission["required_unit_id"]:
            return "Mission unit does not match the rover unit."
        if mission["field_id"] != self.active_field_id:
            return "Mission field does not match the active field."
        if rover["current_field_id"] != self.active_field_id:
            return "Rover field does not match the active field."
        if not rover["communication_available"]:
            return "Mission requires available communication."
        return ""

    def handle_field_switch(self, field_id: str, payload: dict[str, object]) -> tuple[bool, str]:
        reason = "operator confirmed"
        if not payload["operator_confirmed"]:
            reason = "Operator confirmation is required."
        elif any(rover["official_state"] != "STOPPED" for rover in self.rovers.values()):
            reason = "All rovers must be stopped before field switching."
        elif any(rover["active_mission_id"] for rover in self.rovers.values()):
            reason = "Active missions block field switching."
        elif any(rover["official_state"] == "CHARGING" for rover in self.rovers.values()):
            reason = "Charging transition blocks field switching."
        accepted = reason == "operator confirmed"
        self.record_request("FIELD_SWITCH_REQUEST", field_id, accepted, reason)
        if not accepted:
            return False, self.reject("FIELD_SWITCH_REJECTED", field_id, reason)
        self.active_field_id = field_id
        return True, "accepted"

    def handle_restart(self) -> tuple[bool, str]:
        for rover in self.rovers.values():
            self.pause_mission(rover, "MISSION_PAUSED_STATION_RESTART", "Active mission paused after station restart simulation.")
            if rover["official_state"] == "RUNNING":
                rover["official_state"] = "STOPPED"
        self.diagnostic("INFO", "STATION_RESTART_NO_AUTO_RESUME", "STATION", "Station restart simulated; no mission was automatically resumed or armed.")
        return True, "accepted"

    def process_event(self, event: dict[str, object], input_order: int) -> None:
        self.current_tick = int(event["tick"])
        event_type = str(event["event_type"])
        target_id = str(event["target_id"])
        payload = event["payload"]
        accepted = True
        reason = "accepted"
        if event_type in ("BATTERY_SET", "BATTERY_DECREASE", "ROVER_SEEN", "COMMUNICATION_LOST",
                          "COMMUNICATION_RESTORED", "FAULT_SET", "FAULT_CLEAR", "STOP_REQUEST",
                          "RETURN_REQUEST", "CHARGE_START", "CHARGE_COMPLETE"):
            accepted, reason = self.handle_rover_event(event_type, target_id, payload)
        elif event_type.startswith("MISSION_"):
            accepted, reason = self.handle_mission_event(event_type, target_id, payload)
        elif event_type == "FIELD_SWITCH_REQUEST":
            accepted, reason = self.handle_field_switch(target_id, payload)
        elif event_type == "STATION_RESTART":
            accepted, reason = self.handle_restart()
        self.events_processed.append({
            "tick": self.current_tick,
            "input_order": input_order,
            "event_type": event_type,
            "target_id": target_id,
            "status": "ACCEPTED" if accepted else "REJECTED",
            "reason": reason,
        })

    def run(self) -> SimulationReport:
        previous_tick = -1
        for input_order, event in enumerate(self.scenario["events"]):
            event_tick = int(event["tick"])
            if event_tick != previous_tick:
                self.current_tick = event_tick
                self.apply_timeouts()
                previous_tick = event_tick
            self.process_event(event, input_order)
        diagnostics = sorted(
            self.diagnostics,
            key=lambda item: (int(item["tick"]), str(item["severity"]), str(item["code"]),
                              str(item["target_id"]), str(item["message"])),
        )
        has_error = any(item["severity"] == "ERROR" for item in diagnostics)
        result = "FAIL" if has_error else "PASS"
        missions = [copy.deepcopy(self.missions[key]) for key in sorted(self.missions)]
        rovers = [copy.deepcopy(self.rovers[key]) for key in sorted(self.rovers)]
        fields = sorted(copy.deepcopy(self.fields), key=lambda item: str(item["field_id"]))
        document: dict[str, object] = {
            "report_version": REPORT_VERSION,
            "phase": PHASE,
            "scenario_id": self.scenario["scenario_id"],
            "result": result,
            "tick_count": self.current_tick,
            "active_field_id": self.active_field_id,
            "fields": fields,
            "rovers": rovers,
            "missions": missions,
            "events_processed": self.events_processed,
            "requests": self.requests,
            "diagnostics": diagnostics,
            "safety": {
                "network_access_performed": False,
                "gpio_access_performed": False,
                "hardware_output_performed": False,
                "motor_control_performed": False,
                "charging_control_performed": False,
                "rover_output_authority": False,
                "physical_estop_independent": True,
                "automatic_resume_performed": False,
                "automatic_arm_performed": False,
            },
            "summary": {
                "field_count": len(fields),
                "rover_count": len(rovers),
                "mission_count": len(missions),
                "event_count": len(self.events_processed),
                "request_count": len(self.requests),
                "diagnostic_count": len(diagnostics),
                "rejected_event_count": sum(item["status"] == "REJECTED" for item in self.events_processed),
            },
            "exit_code": 2 if has_error else 0,
        }
        return SimulationReport(document, int(document["exit_code"]))


def run_scenario(scenario: dict[str, object]) -> SimulationReport:
    return Simulator(validate_scenario(scenario)).run()


def render_json_report(report: SimulationReport) -> str:
    return json.dumps(report.document, ensure_ascii=True, indent=2, separators=(",", ": ")) + "\n"


def render_text_report(report: SimulationReport) -> str:
    lines: list[str] = []
    for name, value in report.document.items():
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
        else:
            rendered = str(value).lower() if isinstance(value, bool) else str(value)
        lines.append(f"{name}={rendered}")
    return "\n".join(lines) + "\n"


def write_report(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def execute(arguments: CliArguments, write_reports: bool = True) -> SimulationReport:
    errors = validate_cli_arguments(arguments)
    if errors:
        raise ScenarioError(" ".join(errors))
    report = Simulator(load_scenario(arguments.scenario)).run()
    if write_reports:
        write_report(arguments.json_report, render_json_report(report))
        write_report(arguments.text_report, render_text_report(report))
    return report


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_arguments(argv)
        return execute(arguments, write_reports=True).exit_code
    except (ValueError, ScenarioError) as exc:
        print(f"ST-003 scenario rejected: {exc}", file=sys.stderr)
        return 2
    except Exception:
        print("ST-003 simulator failed because of an unexpected internal exception.", file=sys.stderr)
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
