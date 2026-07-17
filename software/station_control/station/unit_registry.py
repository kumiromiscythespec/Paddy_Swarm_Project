#!/usr/bin/env python3
"""Deterministic offline unit registry and compatibility-policy evaluator."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from typing import Callable, Sequence


REPORT_VERSION = 1
PHASE = "ST-007"
SESSION_VERSION = 1
SCHEMA_VERSION = "1"
MAX_UNITS = 128
MAX_HARDWARE_PERMISSIONS = 16
MAX_FIELD_PERMISSIONS = 64
MAX_OPERATIONS = 512
MAX_COMPATIBILITY_DECISIONS = 256
MAX_COMPATIBILITY_REASONS = 24
OPERATION_TYPES = (
    "REGISTER_UNIT", "REVISE_UNIT", "SET_UNIT_STATE", "MOUNT_UNIT",
    "UNMOUNT_UNIT", "EVALUATE_COMPATIBILITY", "VERIFY_INTEGRITY",
)
UNIT_TYPES = ("SCOUT_SENSOR", "PASSIVE_RAKE", "CARRIER", "TEST_ONLY")
REGISTRATION_STATES = ("PENDING", "REGISTERED", "SUSPENDED", "RETIRED")
ROVER_REGISTRATION_STATES = ("PENDING", "REGISTERED", "SUSPENDED", "REVOKED")
PTO_CONTRACTS = ("NONE", "DEPLOY_ASSIST_ONLY", "CONTINUOUS")
HARDWARE_CLASSES = ("COMMON_ROVER_V2", "SCOUT_VARIANT", "WORK_VARIANT", "TEST_FIXTURE")
REASON_CODES = (
    "UNIT_DISABLED", "UNIT_NOT_REGISTERED", "ROVER_DISABLED",
    "ROVER_NOT_REGISTERED", "HARDWARE_CLASS_NOT_ALLOWED", "FIELD_NOT_ALLOWED",
    "ACTIVE_FIELD_MISMATCH", "UNIT_MOUNTED_TO_OTHER_ROVER",
    "DUPLICATE_UNIT_TYPE_ON_ROVER", "OPERATOR_APPROVAL_REQUIRED",
    "ROVER_NOT_STOPPED", "MOTOR_OUTPUT_NOT_DISABLED", "PTO_OUTPUT_NOT_DISABLED",
    "CHARGING_TRANSITION_ACTIVE", "ACTIVE_MISSION_PRESENT",
    "PHYSICAL_ESTOP_STATE_UNKNOWN", "MAIN_POWER_NOT_ISOLATED",
    "MECHANICAL_LOCK_NOT_CONFIRMED", "COMPATIBLE",
)
VALID_TRANSITIONS = (
    ("PENDING", "REGISTERED"), ("PENDING", "RETIRED"),
    ("REGISTERED", "SUSPENDED"), ("REGISTERED", "RETIRED"),
    ("SUSPENDED", "REGISTERED"), ("SUSPENDED", "RETIRED"),
)
UNIT_ID_PATTERN = re.compile(r"^UNIT-DEMO-[A-Z0-9-]+$")
ROVER_ID_PATTERN = re.compile(r"^ROVER-DEMO-[0-9]{3}$")
FIELD_ID_PATTERN = re.compile(r"^FIELD-DEMO-[0-9]{3}$")
OPERATION_ID_PATTERN = re.compile(r"^OP-ST007-[0-9]{3}$")
COMPATIBILITY_ID_PATTERN = re.compile(r"^COMPAT-ST007-[0-9]{3}$")
SESSION_ID_PATTERN = re.compile(r"^SESSION-ST007-[A-Z0-9-]{1,40}$")
TABLE_DEFINITIONS = (
    ("unit_schema_metadata", ("metadata_key", "metadata_value")),
    ("unit_processed_operations", (
        "operation_id", "request_sha256", "operation_type", "logical_tick", "result_code",
    )),
    ("unit_registry", (
        "unit_id", "display_name", "unit_type", "registration_state", "enabled",
        "profile_revision", "pto_contract", "profile_json", "profile_sha256",
    )),
    ("unit_allowed_hardware_classes", ("unit_id", "hardware_class", "enabled")),
    ("unit_allowed_fields", ("unit_id", "field_id", "enabled")),
    ("unit_mount_state", (
        "unit_id", "mount_state", "mounted_rover_id", "mount_revision", "last_operation_id",
    )),
    ("unit_compatibility_decisions", (
        "compatibility_id", "operation_id", "unit_id", "rover_id", "requested_field_id",
        "logical_tick", "decision", "reason_codes_json", "context_json", "context_sha256",
        "direct_output_authority",
    )),
)


class UnitRegistryFailure(RuntimeError):
    def __init__(
        self, code: str, component: str, message: str, exit_code: int,
        operation_id: str = "",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.component = component
        self.message = message
        self.exit_code = exit_code
        self.operation_id = operation_id


class InjectedInterruption(RuntimeError):
    """Test-only interruption; never exposed by the CLI."""


@dataclass(frozen=True)
class UnitRegistryArguments:
    repository_root: Path
    database: Path
    session: Path
    json_report: Path
    text_report: Path


@dataclass(frozen=True)
class UnitRegistryReport:
    document: dict[str, object]
    exit_code: int


@dataclass(frozen=True)
class RuntimeConfiguration:
    foreign_keys: int
    journal_mode: str
    synchronous: int
    busy_timeout_ms: int


@dataclass(frozen=True)
class OperationDelta:
    units_created: int = 0
    units_revised: int = 0
    states_changed: int = 0
    hardware_created: int = 0
    fields_created: int = 0
    mounts_changed: int = 0
    decisions_created: int = 0


class DeterministicArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UnitRegistryFailure("UNIT_INVALID_ARGUMENT", "cli", "Invalid command arguments.", 2)


def parse_arguments(argv: Sequence[str] | None = None) -> UnitRegistryArguments:
    parser = DeterministicArgumentParser(add_help=True)
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--json-report", required=True)
    parser.add_argument("--text-report", required=True)
    values = parser.parse_args(argv)
    return UnitRegistryArguments(
        Path(values.repository_root), Path(values.database), Path(values.session),
        Path(values.json_report), Path(values.text_report),
    )


def is_path_contained(candidate: Path, parent: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(parent.resolve(strict=True))
        return True
    except (OSError, ValueError):
        return False


def validate_arguments(arguments: UnitRegistryArguments) -> None:
    if not arguments.repository_root.is_dir():
        raise UnitRegistryFailure(
            "UNIT_REPOSITORY_ROOT_INVALID", "path", "Repository root must be an existing directory.", 2,
        )
    if not arguments.session.is_file():
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "path", "Session file must exist.", 2)
    if arguments.database.parent.is_file() or not arguments.database.parent.is_dir():
        raise UnitRegistryFailure(
            "UNIT_DATABASE_PARENT_INVALID", "path", "Database parent must be an existing directory.", 2,
        )
    if is_path_contained(arguments.database, arguments.repository_root):
        raise UnitRegistryFailure(
            "UNIT_DATABASE_PATH_INSIDE_REPOSITORY", "path", "Database must be outside the repository.", 2,
        )
    if arguments.json_report == arguments.text_report:
        raise UnitRegistryFailure("UNIT_INVALID_ARGUMENT", "path", "Report paths must differ.", 2)
    for report in (arguments.json_report, arguments.text_report):
        if report.parent.is_file() or not report.parent.is_dir():
            raise UnitRegistryFailure(
                "UNIT_REPORT_PARENT_INVALID", "path", "Report parent must be an existing directory.", 2,
            )
        if is_path_contained(report, arguments.repository_root):
            raise UnitRegistryFailure(
                "UNIT_REPORT_PATH_INSIDE_REPOSITORY", "path", "Reports must be outside the repository.", 2,
            )


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", "Duplicate JSON key.", 3)
        result[key] = value
    return result


def _reject_constant(_value: str) -> object:
    raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", "Non-finite JSON number.", 3)


def load_strict_json(path: Path) -> object:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError
        return json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except UnitRegistryFailure:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", "Session is not strict JSON.", 3) from exc


def _exact(value: object, keys: tuple[str, ...], context: str) -> dict[str, object]:
    if type(value) is not dict or tuple(value.keys()) != keys:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", f"{context} properties are invalid.", 3)
    return value


def _text(value: object, context: str, maximum: int = 128) -> str:
    if type(value) is not str or not value or len(value) > maximum:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", f"{context} is invalid.", 3)
    lowered = value.lower()
    prohibited = (
        "password", "credential", "private key", "secret key", "access token",
        "mac address", "ip address", "board serial", "device serial",
        "latitude", "longitude", "exact coordinate",
    )
    if any(term in lowered for term in prohibited):
        raise UnitRegistryFailure("UNIT_PROFILE_INVALID", "session", f"{context} contains prohibited data.", 3)
    return value


def _integer(value: object, context: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", f"{context} is invalid.", 3)
    return value


def _boolean(value: object, context: str) -> bool:
    if type(value) is not bool:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", f"{context} is invalid.", 3)
    return value


def _pattern(value: object, pattern: re.Pattern[str], context: str) -> str:
    text = _text(value, context)
    if pattern.fullmatch(text) is None:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", f"{context} is invalid.", 3)
    return text


def _enum(value: object, values: tuple[str, ...], context: str) -> str:
    text = _text(value, context)
    if text not in values:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", f"{context} is invalid.", 3)
    return text


def _array(
    value: object, context: str, maximum: int,
    validator: Callable[[object, str], str],
) -> list[str]:
    if type(value) is not list or not value or len(value) > maximum:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", f"{context} is invalid.", 3)
    items = [validator(item, context) for item in value]
    if len(items) != len(set(items)):
        code = "UNIT_HARDWARE_PERMISSION_DUPLICATE" if "hardware" in context else "UNIT_FIELD_PERMISSION_DUPLICATE"
        raise UnitRegistryFailure(code, "session", f"{context} contains duplicates.", 3)
    return items


def _safe_flags(payload: dict[str, object], mount: bool) -> None:
    stopped_key = "rover_confirmed_stopped" if mount else "rover_reported_stopped"
    _boolean(payload["operator_approved"], "operator approval")
    _boolean(payload[stopped_key], "rover stopped")
    _boolean(payload["motor_output_disabled"], "motor output disabled")
    _boolean(payload["pto_output_disabled"], "PTO output disabled")
    _integer(payload["charging_transition_count"], "charging transition count", 0, 1024)
    _integer(payload["active_mission_count"], "active mission count", 0, 1024)
    _boolean(payload["physical_estop_state_known"], "ESTOP state known")
    _boolean(payload["main_power_isolated"], "main power isolated")
    _boolean(payload["mechanical_lock_confirmed"], "mechanical lock confirmed")


def validate_session(value: object) -> dict[str, object]:
    session = _exact(value, ("session_version", "session_id", "operations"), "session")
    if _integer(session["session_version"], "session version", 1, 1) != SESSION_VERSION:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", "Unsupported session version.", 3)
    _pattern(session["session_id"], SESSION_ID_PATTERN, "session ID")
    operations = session["operations"]
    if type(operations) is not list or not 1 <= len(operations) <= MAX_OPERATIONS:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", "Operation list is invalid.", 3)
    operation_ids: set[str] = set()
    previous_tick = -1
    compatibility_count = 0
    for index, raw in enumerate(operations):
        operation = _exact(raw, ("operation_id", "logical_tick", "operation_type", "payload"), f"operation {index}")
        operation_id = _pattern(operation["operation_id"], OPERATION_ID_PATTERN, "operation ID")
        if operation_id in operation_ids:
            raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", "Duplicate operation ID.", 3)
        operation_ids.add(operation_id)
        tick = _integer(operation["logical_tick"], "logical tick", 0, 2_147_483_647)
        if tick < previous_tick:
            raise UnitRegistryFailure("UNIT_SESSION_TICK_REVERSED", "session", "Logical tick reversed.", 3)
        previous_tick = tick
        operation_type = _enum(operation["operation_type"], OPERATION_TYPES, "operation type")
        _validate_payload(operation_type, operation["payload"], index)
        compatibility_count += operation_type == "EVALUATE_COMPATIBILITY"
    if compatibility_count > MAX_COMPATIBILITY_DECISIONS:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "session", "Too many compatibility decisions.", 3)
    return session


def _validate_payload(operation_type: str, value: object, index: int) -> None:
    register = (
        "unit_id", "display_name", "unit_type", "initial_state", "enabled",
        "profile_revision", "pto_contract", "allowed_hardware_classes", "allowed_fields",
    )
    revise = (
        "unit_id", "expected_revision", "new_revision", "display_name", "unit_type", "enabled",
        "pto_contract", "allowed_hardware_classes", "allowed_fields", "operator_approved",
        "unit_confirmed_unmounted", "pto_output_disabled", "main_power_isolated",
    )
    state = (
        "unit_id", "target_state", "operator_approved", "unit_confirmed_unmounted",
        "pto_output_disabled", "main_power_isolated", "reason",
    )
    mount = (
        "unit_id", "rover_id", "rover_hardware_class", "rover_registration_state", "rover_enabled",
        "operator_approved", "rover_confirmed_stopped", "motor_output_disabled",
        "pto_output_disabled", "charging_transition_count", "active_mission_count",
        "physical_estop_state_known", "main_power_isolated", "mechanical_lock_confirmed",
    )
    unmount = (
        "unit_id", "rover_id", "operator_approved", "rover_confirmed_stopped",
        "motor_output_disabled", "pto_output_disabled", "charging_transition_count",
        "active_mission_count", "physical_estop_state_known", "main_power_isolated",
        "mechanical_lock_confirmed",
    )
    compatibility = (
        "compatibility_id", "unit_id", "rover_id", "rover_hardware_class",
        "rover_registration_state", "rover_enabled", "active_field_id", "requested_field_id",
        "operator_approved", "rover_reported_stopped", "motor_output_disabled",
        "pto_output_disabled", "charging_transition_count", "active_mission_count",
        "physical_estop_state_known", "main_power_isolated", "mechanical_lock_confirmed",
    )
    keys = {
        "REGISTER_UNIT": register, "REVISE_UNIT": revise, "SET_UNIT_STATE": state,
        "MOUNT_UNIT": mount, "UNMOUNT_UNIT": unmount,
        "EVALUATE_COMPATIBILITY": compatibility, "VERIFY_INTEGRITY": (),
    }[operation_type]
    payload = _exact(value, keys, f"payload {index}")
    if operation_type == "VERIFY_INTEGRITY":
        return
    if "unit_id" in payload:
        _pattern(payload["unit_id"], UNIT_ID_PATTERN, "unit ID")
    if operation_type in ("REGISTER_UNIT", "REVISE_UNIT"):
        _text(payload["display_name"], "display name", 80)
        _enum(payload["unit_type"], UNIT_TYPES, "unit type")
        _boolean(payload["enabled"], "enabled")
        _enum(payload["pto_contract"], PTO_CONTRACTS, "PTO contract")
        _array(payload["allowed_hardware_classes"], "hardware permissions", MAX_HARDWARE_PERMISSIONS,
               lambda item, context: _enum(item, HARDWARE_CLASSES, context))
        _array(payload["allowed_fields"], "field permissions", MAX_FIELD_PERMISSIONS,
               lambda item, context: _pattern(item, FIELD_ID_PATTERN, context))
    if operation_type == "REGISTER_UNIT":
        if payload["initial_state"] != "PENDING" or type(payload["initial_state"]) is not str:
            raise UnitRegistryFailure("UNIT_PROFILE_INVALID", "session", "Initial state must be PENDING.", 3)
        if _integer(payload["profile_revision"], "profile revision", 1, 1) != 1:
            raise UnitRegistryFailure("UNIT_PROFILE_INVALID", "session", "Initial revision must be one.", 3)
    elif operation_type == "REVISE_UNIT":
        expected = _integer(payload["expected_revision"], "expected revision", 1, 2_147_483_646)
        new = _integer(payload["new_revision"], "new revision", 2, 2_147_483_647)
        if new != expected + 1:
            raise UnitRegistryFailure("UNIT_REVISION_SEQUENCE_INVALID", "session", "Revision must increment by one.", 3)
        for key in ("operator_approved", "unit_confirmed_unmounted", "pto_output_disabled", "main_power_isolated"):
            _boolean(payload[key], key)
    elif operation_type == "SET_UNIT_STATE":
        _enum(payload["target_state"], REGISTRATION_STATES, "target state")
        for key in ("operator_approved", "unit_confirmed_unmounted", "pto_output_disabled", "main_power_isolated"):
            _boolean(payload[key], key)
        _text(payload["reason"], "reason", 160)
    elif operation_type in ("MOUNT_UNIT", "UNMOUNT_UNIT"):
        _pattern(payload["rover_id"], ROVER_ID_PATTERN, "rover ID")
        if operation_type == "MOUNT_UNIT":
            _enum(payload["rover_hardware_class"], HARDWARE_CLASSES, "hardware class")
            _enum(payload["rover_registration_state"], ROVER_REGISTRATION_STATES, "rover registration state")
            _boolean(payload["rover_enabled"], "rover enabled")
        _safe_flags(payload, True)
    elif operation_type == "EVALUATE_COMPATIBILITY":
        _pattern(payload["compatibility_id"], COMPATIBILITY_ID_PATTERN, "compatibility ID")
        _pattern(payload["rover_id"], ROVER_ID_PATTERN, "rover ID")
        _enum(payload["rover_hardware_class"], HARDWARE_CLASSES, "hardware class")
        _enum(payload["rover_registration_state"], ROVER_REGISTRATION_STATES, "rover registration state")
        _boolean(payload["rover_enabled"], "rover enabled")
        _pattern(payload["active_field_id"], FIELD_ID_PATTERN, "active field ID")
        _pattern(payload["requested_field_id"], FIELD_ID_PATTERN, "requested field ID")
        _safe_flags(payload, False)


def canonical_json(value: object, *, sort_keys: bool = True) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=sort_keys, separators=(",", ":"), allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def operation_request_sha256(operation: dict[str, object]) -> str:
    return sha256_text(canonical_json(operation))


def open_database(path: Path) -> tuple[sqlite3.Connection, RuntimeConfiguration]:
    try:
        connection = sqlite3.connect(path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        journal_mode = str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]).lower()
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute("PRAGMA busy_timeout = 5000")
        configuration = RuntimeConfiguration(
            int(connection.execute("PRAGMA foreign_keys").fetchone()[0]), journal_mode,
            int(connection.execute("PRAGMA synchronous").fetchone()[0]),
            int(connection.execute("PRAGMA busy_timeout").fetchone()[0]),
        )
        if configuration != RuntimeConfiguration(1, "wal", 2, 5000):
            raise UnitRegistryFailure("UNIT_SCHEMA_INITIALIZATION_FAILED", "database", "SQLite runtime configuration failed.", 3)
        return connection, configuration
    except sqlite3.Error as exc:
        raise UnitRegistryFailure("UNIT_SCHEMA_INITIALIZATION_FAILED", "database", "Database could not be opened.", 3) from exc


def initialize_or_verify_schema(connection: sqlite3.Connection, schema_path: Path) -> bool:
    tables = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )]
    initialized = False
    if not tables:
        try:
            connection.executescript(schema_path.read_text(encoding="utf-8"))
            connection.execute("BEGIN IMMEDIATE")
            connection.executemany(
                "INSERT INTO unit_schema_metadata(metadata_key, metadata_value) VALUES(?, ?)",
                (("schema_version", SCHEMA_VERSION), ("application_phase", PHASE)),
            )
            connection.execute("COMMIT")
            initialized = True
        except (OSError, sqlite3.Error) as exc:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise UnitRegistryFailure("UNIT_SCHEMA_INITIALIZATION_FAILED", "schema", "Schema initialization failed.", 3) from exc
    verify_schema_version(connection)
    actual = tuple(row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ))
    expected = tuple(sorted(name for name, _columns in TABLE_DEFINITIONS))
    if actual != expected:
        raise UnitRegistryFailure("UNIT_SCHEMA_VERSION_UNSUPPORTED", "schema", "Database table inventory is unsupported.", 3)
    return initialized


def verify_schema_version(connection: sqlite3.Connection) -> None:
    try:
        metadata = dict(connection.execute(
            "SELECT metadata_key, metadata_value FROM unit_schema_metadata ORDER BY metadata_key"
        ))
    except sqlite3.Error as exc:
        raise UnitRegistryFailure("UNIT_SCHEMA_VERSION_UNSUPPORTED", "schema", "Schema metadata is unavailable.", 3) from exc
    if metadata != {"application_phase": PHASE, "schema_version": SCHEMA_VERSION}:
        raise UnitRegistryFailure("UNIT_SCHEMA_VERSION_UNSUPPORTED", "schema", "Schema version is unsupported.", 3)


def integrity_check(connection: sqlite3.Connection) -> str:
    try:
        value = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    except sqlite3.Error as exc:
        raise UnitRegistryFailure("UNIT_INTEGRITY_CHECK_FAILED", "integrity", "Integrity check failed.", 5) from exc
    if value.lower() != "ok":
        raise UnitRegistryFailure("UNIT_INTEGRITY_CHECK_FAILED", "integrity", "Integrity check failed.", 5)
    return "OK"


def canonical_database_state(connection: sqlite3.Connection) -> dict[str, object]:
    state: dict[str, object] = {}
    for table, columns in TABLE_DEFINITIONS:
        order = ", ".join(columns[:1] if table not in (
            "unit_allowed_hardware_classes", "unit_allowed_fields",
        ) else columns[:2])
        rows = connection.execute(f"SELECT {', '.join(columns)} FROM {table} ORDER BY {order}").fetchall()
        state[table] = [{column: row[column] for column in columns} for row in rows]
    return state


def empty_canonical_state() -> dict[str, object]:
    return {table: [] for table, _columns in TABLE_DEFINITIONS}


def canonical_state_sha256(state: dict[str, object]) -> str:
    return sha256_text(canonical_json(state))


def _profile(payload: dict[str, object], revision: int) -> dict[str, object]:
    return {
        "display_name": payload["display_name"], "unit_type": payload["unit_type"],
        "enabled": payload["enabled"], "profile_revision": revision,
        "pto_contract": payload["pto_contract"],
        "allowed_hardware_classes": payload["allowed_hardware_classes"],
        "allowed_fields": payload["allowed_fields"],
    }


def _gate(payload: dict[str, object], operation_id: str, stopped_key: str) -> None:
    checks = (
        ("operator_approved", True, "UNIT_OPERATOR_APPROVAL_REQUIRED", "Operator approval is required."),
        (stopped_key, True, "UNIT_ROVER_NOT_STOPPED", "Rover must be stopped."),
        ("motor_output_disabled", True, "UNIT_MOTOR_OUTPUT_ACTIVE", "Motor output must be disabled."),
        ("pto_output_disabled", True, "UNIT_PTO_OUTPUT_ACTIVE", "PTO output must be disabled."),
        ("charging_transition_count", 0, "UNIT_CHARGING_TRANSITION_ACTIVE", "Charging transition must be inactive."),
        ("active_mission_count", 0, "UNIT_ACTIVE_MISSION_PRESENT", "Active mission is not allowed."),
        ("physical_estop_state_known", True, "UNIT_ESTOP_STATE_UNKNOWN", "ESTOP state must be known."),
        ("main_power_isolated", True, "UNIT_MAIN_POWER_NOT_ISOLATED", "Main power must be isolated."),
        ("mechanical_lock_confirmed", True, "UNIT_MECHANICAL_LOCK_NOT_CONFIRMED", "Mechanical lock confirmation is required."),
    )
    for key, expected, code, message in checks:
        if payload[key] != expected:
            raise UnitRegistryFailure(code, "mount", message, 4, operation_id)


def _unit_row(connection: sqlite3.Connection, unit_id: str, operation_id: str) -> sqlite3.Row:
    row = connection.execute("SELECT * FROM unit_registry WHERE unit_id = ?", (unit_id,)).fetchone()
    if row is None:
        raise UnitRegistryFailure("UNIT_NOT_FOUND", "operation", "Unit was not found.", 4, operation_id)
    return row


def _register(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    payload = operation["payload"]
    assert isinstance(payload, dict)
    operation_id = str(operation["operation_id"])
    unit_id = str(payload["unit_id"])
    if connection.execute("SELECT 1 FROM unit_registry WHERE unit_id = ?", (unit_id,)).fetchone():
        raise UnitRegistryFailure("UNIT_ALREADY_EXISTS", "operation", "Unit already exists.", 4, operation_id)
    if int(connection.execute("SELECT COUNT(*) FROM unit_registry").fetchone()[0]) >= MAX_UNITS:
        raise UnitRegistryFailure("UNIT_PROFILE_INVALID", "operation", "Unit limit reached.", 4, operation_id)
    profile = _profile(payload, 1)
    profile_json = canonical_json(profile)
    connection.execute(
        "INSERT INTO unit_registry VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (unit_id, payload["display_name"], payload["unit_type"], "PENDING", int(payload["enabled"]),
         1, payload["pto_contract"], profile_json, sha256_text(profile_json)),
    )
    connection.executemany(
        "INSERT INTO unit_allowed_hardware_classes VALUES(?, ?, 1)",
        ((unit_id, item) for item in payload["allowed_hardware_classes"]),
    )
    connection.executemany(
        "INSERT INTO unit_allowed_fields VALUES(?, ?, 1)",
        ((unit_id, item) for item in payload["allowed_fields"]),
    )
    connection.execute("INSERT INTO unit_mount_state VALUES(?, 'UNMOUNTED', '', 0, ?)", (unit_id, operation_id))
    return OperationDelta(1, 0, 0, len(payload["allowed_hardware_classes"]), len(payload["allowed_fields"]), 0, 0)


def _revision_gate(payload: dict[str, object], operation_id: str) -> None:
    if not payload["operator_approved"]:
        raise UnitRegistryFailure("UNIT_OPERATOR_APPROVAL_REQUIRED", "revision", "Operator approval is required.", 4, operation_id)
    if not payload["unit_confirmed_unmounted"]:
        raise UnitRegistryFailure("UNIT_NOT_UNMOUNTED", "revision", "Unit must be confirmed unmounted.", 4, operation_id)
    if not payload["pto_output_disabled"]:
        raise UnitRegistryFailure("UNIT_PTO_OUTPUT_ACTIVE", "revision", "PTO output must be disabled.", 4, operation_id)
    if not payload["main_power_isolated"]:
        raise UnitRegistryFailure("UNIT_MAIN_POWER_NOT_ISOLATED", "revision", "Main power must be isolated.", 4, operation_id)


def _revise(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    payload = operation["payload"]
    assert isinstance(payload, dict)
    operation_id = str(operation["operation_id"])
    row = _unit_row(connection, str(payload["unit_id"]), operation_id)
    _revision_gate(payload, operation_id)
    mount = connection.execute("SELECT mount_state FROM unit_mount_state WHERE unit_id = ?", (row["unit_id"],)).fetchone()[0]
    if mount != "UNMOUNTED":
        raise UnitRegistryFailure("UNIT_NOT_UNMOUNTED", "revision", "Database mount state must be UNMOUNTED.", 4, operation_id)
    if row["registration_state"] == "RETIRED":
        raise UnitRegistryFailure("UNIT_STATE_TRANSITION_INVALID", "revision", "Retired unit cannot be revised.", 4, operation_id)
    if row["profile_revision"] != payload["expected_revision"]:
        raise UnitRegistryFailure("UNIT_REVISION_CONFLICT", "revision", "Expected revision does not match.", 4, operation_id)
    if payload["new_revision"] != payload["expected_revision"] + 1:
        raise UnitRegistryFailure("UNIT_REVISION_SEQUENCE_INVALID", "revision", "Revision sequence is invalid.", 4, operation_id)
    profile = _profile(payload, int(payload["new_revision"]))
    profile_json = canonical_json(profile)
    connection.execute(
        "UPDATE unit_registry SET display_name=?, unit_type=?, enabled=?, profile_revision=?, pto_contract=?, profile_json=?, profile_sha256=? WHERE unit_id=?",
        (payload["display_name"], payload["unit_type"], int(payload["enabled"]), payload["new_revision"],
         payload["pto_contract"], profile_json, sha256_text(profile_json), row["unit_id"]),
    )
    connection.execute("UPDATE unit_allowed_hardware_classes SET enabled=0 WHERE unit_id=?", (row["unit_id"],))
    connection.execute("UPDATE unit_allowed_fields SET enabled=0 WHERE unit_id=?", (row["unit_id"],))
    connection.executemany(
        "INSERT INTO unit_allowed_hardware_classes VALUES(?, ?, 1) ON CONFLICT(unit_id, hardware_class) DO UPDATE SET enabled=1",
        ((row["unit_id"], item) for item in payload["allowed_hardware_classes"]),
    )
    connection.executemany(
        "INSERT INTO unit_allowed_fields VALUES(?, ?, 1) ON CONFLICT(unit_id, field_id) DO UPDATE SET enabled=1",
        ((row["unit_id"], item) for item in payload["allowed_fields"]),
    )
    return OperationDelta(units_revised=1)


def _set_state(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    payload = operation["payload"]
    assert isinstance(payload, dict)
    operation_id = str(operation["operation_id"])
    row = _unit_row(connection, str(payload["unit_id"]), operation_id)
    _revision_gate(payload, operation_id)
    mount = connection.execute("SELECT mount_state FROM unit_mount_state WHERE unit_id=?", (row["unit_id"],)).fetchone()[0]
    if mount != "UNMOUNTED":
        raise UnitRegistryFailure("UNIT_NOT_UNMOUNTED", "state", "Unit must be unmounted.", 4, operation_id)
    target = str(payload["target_state"])
    if target == row["registration_state"]:
        return OperationDelta()
    if (row["registration_state"], target) not in VALID_TRANSITIONS:
        raise UnitRegistryFailure("UNIT_STATE_TRANSITION_INVALID", "state", "State transition is invalid.", 4, operation_id)
    connection.execute("UPDATE unit_registry SET registration_state=? WHERE unit_id=?", (target, row["unit_id"]))
    return OperationDelta(states_changed=1)


def _mount(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    payload = operation["payload"]
    assert isinstance(payload, dict)
    operation_id = str(operation["operation_id"])
    row = _unit_row(connection, str(payload["unit_id"]), operation_id)
    if not row["enabled"]:
        raise UnitRegistryFailure("UNIT_PROFILE_INVALID", "mount", "Unit is disabled.", 4, operation_id)
    if row["registration_state"] != "REGISTERED":
        raise UnitRegistryFailure("UNIT_STATE_TRANSITION_INVALID", "mount", "Unit is not registered.", 4, operation_id)
    mount = connection.execute("SELECT * FROM unit_mount_state WHERE unit_id=?", (row["unit_id"],)).fetchone()
    if mount["mount_state"] != "UNMOUNTED":
        raise UnitRegistryFailure("UNIT_ALREADY_MOUNTED", "mount", "Unit is already mounted.", 4, operation_id)
    if payload["rover_registration_state"] != "REGISTERED" or not payload["rover_enabled"]:
        raise UnitRegistryFailure("UNIT_STATE_TRANSITION_INVALID", "mount", "Rover is not registered and enabled.", 4, operation_id)
    allowed = connection.execute(
        "SELECT 1 FROM unit_allowed_hardware_classes WHERE unit_id=? AND hardware_class=? AND enabled=1",
        (row["unit_id"], payload["rover_hardware_class"]),
    ).fetchone()
    if not allowed:
        raise UnitRegistryFailure("UNIT_HARDWARE_CLASS_INCOMPATIBLE", "mount", "Hardware class is not allowed.", 4, operation_id)
    _gate(payload, operation_id, "rover_confirmed_stopped")
    duplicate = connection.execute(
        "SELECT 1 FROM unit_mount_state m JOIN unit_registry u ON u.unit_id=m.unit_id WHERE m.mount_state='MOUNTED' AND m.mounted_rover_id=? AND u.unit_type=? AND u.unit_id<>?",
        (payload["rover_id"], row["unit_type"], row["unit_id"]),
    ).fetchone()
    if duplicate:
        raise UnitRegistryFailure("UNIT_DUPLICATE_TYPE_ON_ROVER", "mount", "Duplicate unit type on rover.", 4, operation_id)
    connection.execute(
        "UPDATE unit_mount_state SET mount_state='MOUNTED', mounted_rover_id=?, mount_revision=mount_revision+1, last_operation_id=? WHERE unit_id=?",
        (payload["rover_id"], operation_id, row["unit_id"]),
    )
    return OperationDelta(mounts_changed=1)


def _unmount(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    payload = operation["payload"]
    assert isinstance(payload, dict)
    operation_id = str(operation["operation_id"])
    row = _unit_row(connection, str(payload["unit_id"]), operation_id)
    mount = connection.execute("SELECT * FROM unit_mount_state WHERE unit_id=?", (row["unit_id"],)).fetchone()
    if mount["mount_state"] != "MOUNTED":
        raise UnitRegistryFailure("UNIT_NOT_UNMOUNTED", "mount", "Unit is not mounted.", 4, operation_id)
    if mount["mounted_rover_id"] != payload["rover_id"]:
        raise UnitRegistryFailure("UNIT_MOUNT_ROVER_MISMATCH", "mount", "Mounted rover does not match.", 4, operation_id)
    _gate(payload, operation_id, "rover_confirmed_stopped")
    connection.execute(
        "UPDATE unit_mount_state SET mount_state='UNMOUNTED', mounted_rover_id='', mount_revision=mount_revision+1, last_operation_id=? WHERE unit_id=?",
        (operation_id, row["unit_id"]),
    )
    return OperationDelta(mounts_changed=1)


def evaluate_compatibility(connection: sqlite3.Connection, payload: dict[str, object]) -> tuple[str, list[str]]:
    row = connection.execute("SELECT * FROM unit_registry WHERE unit_id=?", (payload["unit_id"],)).fetchone()
    if row is None:
        raise UnitRegistryFailure("UNIT_NOT_FOUND", "compatibility", "Unit was not found.", 4)
    reasons: list[str] = []
    if not row["enabled"]:
        reasons.append("UNIT_DISABLED")
    if row["registration_state"] != "REGISTERED":
        reasons.append("UNIT_NOT_REGISTERED")
    if not payload["rover_enabled"]:
        reasons.append("ROVER_DISABLED")
    if payload["rover_registration_state"] != "REGISTERED":
        reasons.append("ROVER_NOT_REGISTERED")
    if not connection.execute(
        "SELECT 1 FROM unit_allowed_hardware_classes WHERE unit_id=? AND hardware_class=? AND enabled=1",
        (row["unit_id"], payload["rover_hardware_class"]),
    ).fetchone():
        reasons.append("HARDWARE_CLASS_NOT_ALLOWED")
    if not connection.execute(
        "SELECT 1 FROM unit_allowed_fields WHERE unit_id=? AND field_id=? AND enabled=1",
        (row["unit_id"], payload["requested_field_id"]),
    ).fetchone():
        reasons.append("FIELD_NOT_ALLOWED")
    if payload["active_field_id"] != payload["requested_field_id"]:
        reasons.append("ACTIVE_FIELD_MISMATCH")
    mount = connection.execute("SELECT * FROM unit_mount_state WHERE unit_id=?", (row["unit_id"],)).fetchone()
    if mount["mount_state"] == "MOUNTED" and mount["mounted_rover_id"] != payload["rover_id"]:
        reasons.append("UNIT_MOUNTED_TO_OTHER_ROVER")
    duplicate = connection.execute(
        "SELECT 1 FROM unit_mount_state m JOIN unit_registry u ON u.unit_id=m.unit_id WHERE m.mount_state='MOUNTED' AND m.mounted_rover_id=? AND u.unit_type=? AND u.unit_id<>?",
        (payload["rover_id"], row["unit_type"], row["unit_id"]),
    ).fetchone()
    if duplicate:
        reasons.append("DUPLICATE_UNIT_TYPE_ON_ROVER")
    checks = (
        (not payload["operator_approved"], "OPERATOR_APPROVAL_REQUIRED"),
        (not payload["rover_reported_stopped"], "ROVER_NOT_STOPPED"),
        (not payload["motor_output_disabled"], "MOTOR_OUTPUT_NOT_DISABLED"),
        (not payload["pto_output_disabled"], "PTO_OUTPUT_NOT_DISABLED"),
        (payload["charging_transition_count"] > 0, "CHARGING_TRANSITION_ACTIVE"),
        (payload["active_mission_count"] > 0, "ACTIVE_MISSION_PRESENT"),
        (not payload["physical_estop_state_known"], "PHYSICAL_ESTOP_STATE_UNKNOWN"),
        (not payload["main_power_isolated"], "MAIN_POWER_NOT_ISOLATED"),
        (not payload["mechanical_lock_confirmed"], "MECHANICAL_LOCK_NOT_CONFIRMED"),
    )
    reasons.extend(code for condition, code in checks if condition)
    if len(reasons) > MAX_COMPATIBILITY_REASONS:
        raise UnitRegistryFailure("UNIT_SESSION_INVALID", "compatibility", "Too many compatibility reasons.", 3)
    return ("INCOMPATIBLE", reasons) if reasons else ("COMPATIBLE", ["COMPATIBLE"])


def _compatibility(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    payload = operation["payload"]
    assert isinstance(payload, dict)
    operation_id = str(operation["operation_id"])
    if connection.execute("SELECT 1 FROM unit_compatibility_decisions WHERE compatibility_id=?", (payload["compatibility_id"],)).fetchone():
        raise UnitRegistryFailure("UNIT_COMPATIBILITY_ID_CONFLICT", "compatibility", "Compatibility ID already exists.", 4, operation_id)
    decision, reasons = evaluate_compatibility(connection, payload)
    context = {key: payload[key] for key in payload if key != "compatibility_id"}
    context_json = canonical_json(context)
    connection.execute(
        "INSERT INTO unit_compatibility_decisions VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
        (payload["compatibility_id"], operation_id, payload["unit_id"], payload["rover_id"],
         payload["requested_field_id"], operation["logical_tick"], decision,
         canonical_json(reasons), context_json, sha256_text(context_json)),
    )
    return OperationDelta(decisions_created=1)


def _insert_processed(connection: sqlite3.Connection, operation: dict[str, object], request_hash: str) -> None:
    connection.execute(
        "INSERT INTO unit_processed_operations VALUES(?, ?, ?, ?, 'APPLIED')",
        (operation["operation_id"], request_hash, operation["operation_type"], operation["logical_tick"]),
    )


def _process_operation(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    operation_type = str(operation["operation_type"])
    if operation_type == "REGISTER_UNIT":
        return _register(connection, operation)
    if operation_type == "REVISE_UNIT":
        return _revise(connection, operation)
    if operation_type == "SET_UNIT_STATE":
        return _set_state(connection, operation)
    if operation_type == "MOUNT_UNIT":
        return _mount(connection, operation)
    if operation_type == "UNMOUNT_UNIT":
        return _unmount(connection, operation)
    if operation_type == "EVALUATE_COMPATIBILITY":
        return _compatibility(connection, operation)
    if operation_type == "VERIFY_INTEGRITY":
        integrity_check(connection)
        return OperationDelta()
    raise UnitRegistryFailure("UNIT_OPERATION_UNKNOWN", "operation", "Unknown operation.", 4, str(operation["operation_id"]))


def _diagnostic(failure: UnitRegistryFailure) -> dict[str, object]:
    return {
        "severity": "ERROR", "code": failure.code, "component": failure.component,
        "operation_id": failure.operation_id, "message": failure.message,
    }


def _add_delta(left: OperationDelta, right: OperationDelta) -> OperationDelta:
    return OperationDelta(*(a + b for a, b in zip(left.__dict__.values(), right.__dict__.values())))


def _build_report(
    session_id: str, database_created: bool, reopened: bool,
    configuration: RuntimeConfiguration | None, begun: bool, committed: bool,
    rolled_back: bool, initialized: bool, input_count: int, processed_count: int,
    applied_count: int, duplicate_count: int, rejected_count: int, delta: OperationDelta,
    conflict_count: int, integrity_result: str, state: dict[str, object],
    diagnostics: list[dict[str, object]], exit_code: int,
) -> UnitRegistryReport:
    diagnostics.sort(key=lambda item: (
        str(item["component"]), str(item["code"]), str(item["operation_id"]), str(item["message"]),
    ))
    units = state["unit_registry"]
    hardware = state["unit_allowed_hardware_classes"]
    fields = state["unit_allowed_fields"]
    mounts = state["unit_mount_state"]
    decisions = state["unit_compatibility_decisions"]
    assert isinstance(units, list) and isinstance(hardware, list) and isinstance(fields, list)
    assert isinstance(mounts, list) and isinstance(decisions, list)
    counts = {table: len(rows) for table, rows in state.items() if isinstance(rows, list)}
    config = configuration or RuntimeConfiguration(0, "not_available", 0, 0)
    document: dict[str, object] = {
        "report_version": REPORT_VERSION,
        "phase": PHASE,
        "session_id": session_id,
        "result": "PASS" if exit_code == 0 else "FAIL",
        "database": {
            "created": database_created, "reopened": reopened,
            "database_outside_repository": True, "journal_mode": config.journal_mode,
            "synchronous": config.synchronous, "foreign_keys": config.foreign_keys,
            "busy_timeout_ms": config.busy_timeout_ms,
        },
        "transaction": {
            "atomic_session": True, "begun": begun, "committed": committed,
            "rolled_back": rolled_back,
        },
        "schema": {
            "schema_version": SCHEMA_VERSION, "supported": exit_code not in (3, 5),
            "initialized": initialized, "migration_performed": False,
        },
        "operations": {
            "input_count": input_count, "processed_count": processed_count,
            "applied_count": applied_count, "duplicate_noop_count": duplicate_count,
            "rejected_count": rejected_count,
        },
        "units": {
            "created_count": delta.units_created, "revised_count": delta.units_revised,
            "state_changed_count": delta.states_changed,
            "pending_count": sum(row["registration_state"] == "PENDING" for row in units),
            "registered_count": sum(row["registration_state"] == "REGISTERED" for row in units),
            "suspended_count": sum(row["registration_state"] == "SUSPENDED" for row in units),
            "retired_count": sum(row["registration_state"] == "RETIRED" for row in units),
            "enabled_count": sum(row["enabled"] == 1 for row in units),
            "disabled_count": sum(row["enabled"] == 0 for row in units),
            "total_count": len(units),
        },
        "hardware_permissions": {
            "created_count": delta.hardware_created, "total_count": len(hardware),
            "enabled_count": sum(row["enabled"] == 1 for row in hardware),
        },
        "field_permissions": {
            "created_count": delta.fields_created, "total_count": len(fields),
            "enabled_count": sum(row["enabled"] == 1 for row in fields),
        },
        "mounts": {
            "state_changed_count": delta.mounts_changed,
            "mounted_count": sum(row["mount_state"] == "MOUNTED" for row in mounts),
            "unmounted_count": sum(row["mount_state"] == "UNMOUNTED" for row in mounts),
            "total_count": len(mounts),
        },
        "compatibility_decisions": {
            "created_count": delta.decisions_created, "total_count": len(decisions),
            "compatible_count": sum(row["decision"] == "COMPATIBLE" for row in decisions),
            "incompatible_count": sum(row["decision"] == "INCOMPATIBLE" for row in decisions),
            "direct_output_authority": False,
        },
        "integrity": {"check_performed": integrity_result != "NOT_PERFORMED", "result": integrity_result},
        "idempotency": {
            "request_hash_algorithm": "SHA256_CANONICAL_JSON",
            "duplicate_noop_count": duplicate_count, "conflict_count": conflict_count,
        },
        "safety": {
            "offline_only": True, "network_access_performed": False,
            "gpio_access_performed": False, "serial_access_performed": False,
            "hardware_output_performed": False, "motor_control_performed": False,
            "pto_control_performed": False, "charging_control_performed": False,
            "rover_communication_performed": False, "physical_mount_performed": False,
            "physical_unmount_performed": False, "attachment_sensor_access_performed": False,
            "actual_assignment_performed": False, "actual_arm_performed": False,
            "automatic_registration_performed": False, "automatic_state_transition_performed": False,
            "direct_output_authority": False, "repository_modified": False,
            "physical_estop_independent": True,
        },
        "summary": {
            "table_count": 7, "row_count_total": sum(counts.values()),
            "diagnostic_count": len(diagnostics),
            "compatible_decision_count": sum(row["decision"] == "COMPATIBLE" for row in decisions),
            "incompatible_decision_count": sum(row["decision"] == "INCOMPATIBLE" for row in decisions),
            "next_phase_eligible": exit_code == 0,
        },
        "diagnostics": diagnostics,
        "canonical_state_sha256": canonical_state_sha256(state),
        "exit_code": exit_code,
    }
    return UnitRegistryReport(document, exit_code)


def run_unit_registry_session(
    arguments: UnitRegistryArguments, *, fail_after_operation_index: int | None = None,
    write_reports: bool = False,
    operation_processor: Callable[[sqlite3.Connection, dict[str, object]], OperationDelta] = _process_operation,
) -> UnitRegistryReport:
    validate_arguments(arguments)
    try:
        session = validate_session(load_strict_json(arguments.session))
    except UnitRegistryFailure as failure:
        report = _build_report(
            "SESSION-ST007-INVALID", False, False, None, False, False, False, False,
            0, 0, 0, 0, 1, OperationDelta(), 0, "NOT_PERFORMED",
            empty_canonical_state(), [_diagnostic(failure)], failure.exit_code,
        )
        return _write_requested_reports(report, arguments) if write_reports else report
    session_id = str(session["session_id"])
    operations = session["operations"]
    assert isinstance(operations, list)
    database_created = not arguments.database.exists()
    configuration: RuntimeConfiguration | None = None
    initialized = reopened = begun = committed = rolled_back = False
    processed = applied = duplicates = rejected = conflicts = 0
    integrity_result = "NOT_PERFORMED"
    exit_code = 0
    diagnostics: list[dict[str, object]] = []
    state = empty_canonical_state()
    delta = OperationDelta()
    connection: sqlite3.Connection | None = None
    schema_path = arguments.repository_root / "software" / "station_control" / "storage" / "unit_registry_schema_v1.sql"
    try:
        connection, configuration = open_database(arguments.database)
        initialized = initialize_or_verify_schema(connection, schema_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            begun = True
        except sqlite3.Error as exc:
            raise UnitRegistryFailure("UNIT_TRANSACTION_BEGIN_FAILED", "transaction", "Atomic transaction could not begin.", 4) from exc
        for index, operation in enumerate(operations):
            operation_id = str(operation["operation_id"])
            request_hash = operation_request_sha256(operation)
            existing = connection.execute(
                "SELECT request_sha256 FROM unit_processed_operations WHERE operation_id=?", (operation_id,),
            ).fetchone()
            if existing is not None:
                if existing[0] != request_hash:
                    conflicts = 1
                    raise UnitRegistryFailure("UNIT_IDEMPOTENCY_CONFLICT", "idempotency", "Operation ID content conflicts.", 4, operation_id)
                duplicates += 1
                processed += 1
            else:
                _insert_processed(connection, operation, request_hash)
                delta = _add_delta(delta, operation_processor(connection, operation))
                applied += 1
                processed += 1
            if fail_after_operation_index is not None and index == fail_after_operation_index:
                raise InjectedInterruption
        connection.execute("COMMIT")
        committed = True
    except InjectedInterruption:
        exit_code = 4
        rejected = 1
        if connection is not None and connection.in_transaction:
            connection.execute("ROLLBACK")
            rolled_back = True
        diagnostics.append(_diagnostic(UnitRegistryFailure("UNIT_TRANSACTION_ROLLED_BACK", "transaction", "Atomic session rolled back after test interruption.", 4)))
    except UnitRegistryFailure as failure:
        exit_code = failure.exit_code
        rejected = 1
        conflicts = int(failure.code == "UNIT_IDEMPOTENCY_CONFLICT")
        if connection is not None and connection.in_transaction:
            connection.execute("ROLLBACK")
            rolled_back = True
            diagnostics.append(_diagnostic(UnitRegistryFailure("UNIT_TRANSACTION_ROLLED_BACK", "transaction", "Atomic session rolled back without partial commit.", 4)))
        diagnostics.append(_diagnostic(failure))
    except sqlite3.Error:
        exit_code = 4
        rejected = 1
        if connection is not None and connection.in_transaction:
            connection.execute("ROLLBACK")
            rolled_back = True
        diagnostics.append(_diagnostic(UnitRegistryFailure("UNIT_TRANSACTION_ROLLED_BACK", "transaction", "Atomic session rolled back after SQLite failure.", 4)))
    except Exception:
        exit_code = 7
        rejected = 1
        if connection is not None and connection.in_transaction:
            connection.execute("ROLLBACK")
            rolled_back = True
        diagnostics.append(_diagnostic(UnitRegistryFailure("UNIT_INTERNAL_ERROR", "internal", "Unexpected internal failure.", 7)))
    finally:
        if connection is not None:
            connection.close()
    try:
        reopened_connection, reopened_configuration = open_database(arguments.database)
        try:
            verify_schema_version(reopened_connection)
            integrity_result = integrity_check(reopened_connection)
            state = canonical_database_state(reopened_connection)
            reopened = True
            configuration = reopened_configuration
        finally:
            reopened_connection.close()
    except UnitRegistryFailure as failure:
        if exit_code == 0:
            exit_code = failure.exit_code
            diagnostics.append(_diagnostic(failure))
    report = _build_report(
        session_id, database_created, reopened, configuration, begun, committed, rolled_back,
        initialized, len(operations), processed, applied, duplicates, rejected, delta,
        conflicts, integrity_result, state, diagnostics, exit_code,
    )
    return _write_requested_reports(report, arguments) if write_reports else report


def render_json_report(report: UnitRegistryReport) -> str:
    return json.dumps(report.document, ensure_ascii=True, indent=2, separators=(",", ": ")) + "\n"


def _text_value(value: object) -> str:
    return str(value).lower() if type(value) is bool else str(value)


def render_text_report(report: UnitRegistryReport) -> str:
    document = report.document
    values = (
        ("report_version", document["report_version"]), ("phase", document["phase"]),
        ("session_id", document["session_id"]), ("result", document["result"]),
        ("database_created", document["database"]["created"]),
        ("database_reopened", document["database"]["reopened"]),
        ("database_outside_repository", document["database"]["database_outside_repository"]),
        ("journal_mode", document["database"]["journal_mode"]),
        ("synchronous", document["database"]["synchronous"]),
        ("foreign_keys", document["database"]["foreign_keys"]),
        ("transaction_committed", document["transaction"]["committed"]),
        ("transaction_rolled_back", document["transaction"]["rolled_back"]),
        ("schema_version", document["schema"]["schema_version"]),
        ("operation_input_count", document["operations"]["input_count"]),
        ("operation_applied_count", document["operations"]["applied_count"]),
        ("duplicate_noop_count", document["operations"]["duplicate_noop_count"]),
        ("unit_total_count", document["units"]["total_count"]),
        ("unit_registered_count", document["units"]["registered_count"]),
        ("unit_suspended_count", document["units"]["suspended_count"]),
        ("unit_retired_count", document["units"]["retired_count"]),
        ("hardware_permission_total_count", document["hardware_permissions"]["total_count"]),
        ("field_permission_total_count", document["field_permissions"]["total_count"]),
        ("mounted_count", document["mounts"]["mounted_count"]),
        ("unmounted_count", document["mounts"]["unmounted_count"]),
        ("compatibility_total_count", document["compatibility_decisions"]["total_count"]),
        ("compatibility_compatible_count", document["compatibility_decisions"]["compatible_count"]),
        ("compatibility_incompatible_count", document["compatibility_decisions"]["incompatible_count"]),
        ("direct_output_authority", document["compatibility_decisions"]["direct_output_authority"]),
        ("integrity_result", document["integrity"]["result"]),
        ("canonical_state_sha256", document["canonical_state_sha256"]),
        ("offline_only", document["safety"]["offline_only"]),
        ("network_access_performed", document["safety"]["network_access_performed"]),
        ("gpio_access_performed", document["safety"]["gpio_access_performed"]),
        ("serial_access_performed", document["safety"]["serial_access_performed"]),
        ("hardware_output_performed", document["safety"]["hardware_output_performed"]),
        ("motor_control_performed", document["safety"]["motor_control_performed"]),
        ("pto_control_performed", document["safety"]["pto_control_performed"]),
        ("physical_mount_performed", document["safety"]["physical_mount_performed"]),
        ("physical_unmount_performed", document["safety"]["physical_unmount_performed"]),
        ("actual_assignment_performed", document["safety"]["actual_assignment_performed"]),
        ("actual_arm_performed", document["safety"]["actual_arm_performed"]),
        ("diagnostic_count", document["summary"]["diagnostic_count"]),
        ("exit_code", document["exit_code"]),
    )
    return "\n".join(f"{key}={_text_value(value)}" for key, value in values) + "\n"


def write_report(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_requested_reports(report: UnitRegistryReport, arguments: UnitRegistryArguments) -> UnitRegistryReport:
    try:
        write_report(arguments.json_report, render_json_report(report))
        write_report(arguments.text_report, render_text_report(report))
        return report
    except OSError:
        failure = UnitRegistryFailure("UNIT_REPORT_WRITE_FAILED", "report", "Report output failed.", 7)
        document = dict(report.document)
        diagnostics = list(document["diagnostics"])
        diagnostics.append(_diagnostic(failure))
        diagnostics.sort(key=lambda item: (str(item["component"]), str(item["code"]), str(item["operation_id"]), str(item["message"])))
        document["result"] = "FAIL"
        document["diagnostics"] = diagnostics
        document["summary"] = dict(document["summary"])
        document["summary"]["diagnostic_count"] = len(diagnostics)
        document["summary"]["next_phase_eligible"] = False
        document["exit_code"] = 7
        return UnitRegistryReport(document, 7)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_arguments(argv)
        report = run_unit_registry_session(arguments, write_reports=True)
        print(render_text_report(report), end="")
        return report.exit_code
    except UnitRegistryFailure as failure:
        print(f"ST-007 unit registry rejected: {failure.message}", file=sys.stderr)
        return failure.exit_code
    except Exception:
        print("UNIT_INTERNAL_ERROR: ST-007 unit registry failed unexpectedly.", file=sys.stderr)
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
