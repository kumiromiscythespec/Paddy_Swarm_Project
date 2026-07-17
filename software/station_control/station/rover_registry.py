"""Offline rover registry and assignment authorization simulation for ST-006."""

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
PHASE = "ST-006"
SESSION_VERSION = 1
SCHEMA_VERSION = "1"
MAX_ROVERS = 128
MAX_FIELD_PERMISSIONS = 64
MAX_UNIT_PERMISSIONS = 64
MAX_OPERATIONS = 512
MAX_AUTHORIZATIONS = 256
OPERATION_TYPES = (
    "REGISTER_ROVER", "REVISE_ROVER", "SET_REGISTRATION_STATE",
    "AUTHORIZE_ASSIGNMENT", "VERIFY_INTEGRITY",
)
ROLES = ("SCOUT", "WORK", "MULTI_ROLE", "TEST_ONLY")
REGISTRATION_STATES = ("PENDING", "REGISTERED", "SUSPENDED", "REVOKED")
HARDWARE_CLASSES = ("COMMON_ROVER_V2", "SCOUT_VARIANT", "WORK_VARIANT", "TEST_FIXTURE")
MISSION_STATES = (
    "DRAFT", "WAITING_APPROVAL", "QUEUED", "ASSIGNED", "RUNNING", "PAUSED",
    "RETURNING", "CHARGING", "COMPLETED", "FAILED", "CANCELLED", "EXPIRED",
)
REASON_CODES = (
    "ROVER_DISABLED", "ROVER_NOT_REGISTERED", "FIELD_NOT_ALLOWED", "UNIT_NOT_ALLOWED",
    "ACTIVE_FIELD_MISMATCH", "OPERATOR_APPROVAL_REQUIRED", "MISSION_STATE_NOT_QUEUED",
    "ROVER_NOT_STOPPED", "COMMUNICATION_UNAVAILABLE", "FAULT_PRESENT",
    "BATTERY_BELOW_RESERVE", "PHYSICAL_ESTOP_ASSERTED",
)
VALID_TRANSITIONS = {
    "PENDING": ("REGISTERED", "REVOKED"),
    "REGISTERED": ("SUSPENDED", "REVOKED"),
    "SUSPENDED": ("REGISTERED", "REVOKED"),
    "REVOKED": (),
}
ROVER_ID_PATTERN = re.compile(r"^ROVER-DEMO-[0-9]{3}$")
FIELD_ID_PATTERN = re.compile(r"^FIELD-DEMO-[0-9]{3}$")
UNIT_ID_PATTERN = re.compile(r"^UNIT-DEMO-[A-Z0-9-]+$")
MISSION_ID_PATTERN = re.compile(r"^MISSION-DEMO-[0-9]{3}$")
AUTHORIZATION_ID_PATTERN = re.compile(r"^AUTH-ST006-[0-9]{3}$")
OPERATION_ID_PATTERN = re.compile(r"^OP-ST006-[0-9]{3}$")
SESSION_ID_PATTERN = re.compile(r"^SESSION-ST006-[A-Z0-9-]{1,40}$")
TABLE_DEFINITIONS = (
    ("rover_schema_metadata", ("metadata_key", "metadata_value"), "metadata_key"),
    (
        "rover_processed_operations",
        ("operation_id", "request_sha256", "operation_type", "logical_tick", "result_code"),
        "operation_id",
    ),
    (
        "rover_registry",
        (
            "rover_id", "display_name", "role", "registration_state", "enabled",
            "profile_revision", "hardware_class", "profile_json", "profile_sha256",
        ),
        "rover_id",
    ),
    (
        "rover_allowed_fields",
        ("rover_id", "field_id", "enabled"),
        "rover_id, field_id",
    ),
    (
        "rover_allowed_units",
        ("rover_id", "unit_id", "enabled"),
        "rover_id, unit_id",
    ),
    (
        "rover_authorization_decisions",
        (
            "authorization_id", "operation_id", "rover_id", "mission_id",
            "requested_field_id", "requested_unit_id", "logical_tick", "decision",
            "reason_codes_json", "context_json", "context_sha256", "direct_output_authority",
        ),
        "authorization_id",
    ),
)


class RegistryFailure(RuntimeError):
    """Expected fail-closed registry error."""

    def __init__(
        self,
        code: str,
        component: str,
        message: str,
        exit_code: int,
        operation_id: str = "",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.component = component
        self.message = message
        self.exit_code = exit_code
        self.operation_id = operation_id


class InjectedInterruption(RuntimeError):
    """Test-only interruption inside an atomic session."""


@dataclass(frozen=True)
class RegistryArguments:
    repository_root: Path
    database: Path
    session: Path
    json_report: Path
    text_report: Path


@dataclass(frozen=True)
class RegistryReport:
    document: dict[str, object]
    exit_code: int


@dataclass(frozen=True)
class RuntimeConfiguration:
    journal_mode: str
    synchronous: int
    foreign_keys: int
    busy_timeout_ms: int


@dataclass(frozen=True)
class OperationDelta:
    rovers_created: int = 0
    rovers_revised: int = 0
    state_changed: int = 0
    fields_created: int = 0
    units_created: int = 0
    decisions_created: int = 0


class DeterministicArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def parse_arguments(argv: Sequence[str] | None = None) -> RegistryArguments:
    parser = DeterministicArgumentParser(description="Run an offline ST-006 rover registry session.")
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--json-report", required=True, type=Path)
    parser.add_argument("--text-report", required=True, type=Path)
    values = parser.parse_args(argv)
    return RegistryArguments(
        values.repository_root, values.database, values.session,
        values.json_report, values.text_report,
    )


def is_path_contained(candidate: Path, parent: Path) -> bool:
    try:
        child = candidate.resolve(strict=False)
        root = parent.resolve(strict=False)
        common = os.path.commonpath((str(child), str(root)))
    except (OSError, ValueError):
        return False
    return os.path.normcase(common) == os.path.normcase(str(root))


def validate_arguments(arguments: RegistryArguments) -> None:
    repository = arguments.repository_root
    if not repository.is_dir():
        raise RegistryFailure(
            "ROVER_REPOSITORY_ROOT_INVALID", "arguments",
            "Repository root must be an existing directory.", 2,
        )
    schema_path = repository / "software" / "station_control" / "storage" / "rover_registry_schema_v1.sql"
    if not schema_path.is_file():
        raise RegistryFailure(
            "ROVER_REPOSITORY_ROOT_INVALID", "arguments",
            "Repository root does not contain the ST-006 SQL schema.", 2,
        )
    if not arguments.session.is_file():
        raise RegistryFailure(
            "ROVER_INVALID_ARGUMENT", "arguments", "Session must be an existing file.", 2,
        )
    if is_path_contained(arguments.database, repository):
        raise RegistryFailure(
            "ROVER_DATABASE_PATH_INSIDE_REPOSITORY", "database",
            "Database must be outside the repository.", 2,
        )
    if not arguments.database.parent.is_dir():
        raise RegistryFailure(
            "ROVER_DATABASE_PARENT_INVALID", "database",
            "Database parent must be an existing directory.", 2,
        )
    for report_path in (arguments.json_report, arguments.text_report):
        if is_path_contained(report_path, repository):
            raise RegistryFailure(
                "ROVER_REPORT_PATH_INSIDE_REPOSITORY", "report",
                "Reports must be outside the repository.", 2,
            )
        if not report_path.parent.is_dir():
            raise RegistryFailure(
                "ROVER_REPORT_PARENT_INVALID", "report",
                "Report parent must be an existing directory.", 2,
            )
    paths = (
        arguments.database.resolve(strict=False), arguments.session.resolve(strict=False),
        arguments.json_report.resolve(strict=False), arguments.text_report.resolve(strict=False),
    )
    if len(set(paths)) != len(paths):
        raise RegistryFailure(
            "ROVER_INVALID_ARGUMENT", "arguments",
            "Database, session, and report paths must be distinct.", 2,
        )


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key.")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"Non-finite JSON value is prohibited: {value}")


def load_strict_json(path: Path) -> object:
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            return json.load(
                stream,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_constant,
            )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RegistryFailure(
            "ROVER_SESSION_INVALID", "session", "Session is not readable strict JSON.", 3,
        ) from exc


def _exact_object(value: object, keys: tuple[str, ...], context: str) -> dict[str, object]:
    if type(value) is not dict or tuple(value) != keys:
        raise RegistryFailure(
            "ROVER_SESSION_INVALID", "session",
            f"{context} properties or property order are invalid.", 3,
        )
    return value


def _bounded_text(value: object, context: str, maximum: int = 128) -> str:
    if type(value) is not str or not 1 <= len(value) <= maximum:
        raise RegistryFailure(
            "ROVER_SESSION_INVALID", "session", f"{context} must be a bounded string.", 3,
        )
    lowered = value.lower()
    prohibited = (
        "password", "credential", "private key", "secret key", "access token",
        "mac address", "ip address", "board serial", "cpu serial", "device serial",
        "latitude", "longitude", "exact coordinate",
    )
    if any(item in lowered for item in prohibited):
        raise RegistryFailure(
            "ROVER_PROFILE_INVALID", "profile", f"{context} contains prohibited identity data.", 3,
        )
    return value


def _integer(value: object, context: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise RegistryFailure(
            "ROVER_SESSION_INVALID", "session", f"{context} is outside its integer range.", 3,
        )
    return value


def _boolean(value: object, context: str) -> bool:
    if type(value) is not bool:
        raise RegistryFailure(
            "ROVER_SESSION_INVALID", "session", f"{context} must be boolean.", 3,
        )
    return value


def _pattern(value: object, pattern: re.Pattern[str], context: str) -> str:
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise RegistryFailure(
            "ROVER_SESSION_INVALID", "session", f"{context} is not a valid demo identifier.", 3,
        )
    return value


def _permission_array(
    value: object,
    pattern: re.Pattern[str],
    context: str,
    maximum: int,
    duplicate_code: str,
) -> list[str]:
    if type(value) is not list or not 1 <= len(value) <= maximum:
        raise RegistryFailure(
            "ROVER_PROFILE_INVALID", "profile", f"{context} count is invalid.", 3,
        )
    items = [_pattern(item, pattern, context) for item in value]
    if len(set(items)) != len(items):
        raise RegistryFailure(duplicate_code, "profile", f"{context} must be unique.", 3)
    return items


def _validate_safety_fields(payload: dict[str, object]) -> None:
    _boolean(payload["operator_approved"], "operator_approved")
    _boolean(payload["rover_confirmed_stopped"], "rover_confirmed_stopped")
    _integer(payload["active_mission_count"], "active_mission_count", 0, 2147483647)
    _integer(payload["charging_transition_count"], "charging_transition_count", 0, 2147483647)


def validate_session(value: object) -> dict[str, object]:
    session = _exact_object(value, ("session_version", "session_id", "operations"), "session")
    if type(session["session_version"]) is not int or session["session_version"] != SESSION_VERSION:
        raise RegistryFailure("ROVER_SESSION_INVALID", "session", "Session version must be 1.", 3)
    if type(session["session_id"]) is not str or SESSION_ID_PATTERN.fullmatch(session["session_id"]) is None:
        raise RegistryFailure("ROVER_SESSION_INVALID", "session", "Session ID is invalid.", 3)
    operations = session["operations"]
    if type(operations) is not list or not 1 <= len(operations) <= MAX_OPERATIONS:
        raise RegistryFailure(
            "ROVER_SESSION_INVALID", "session", "Operation count must be between 1 and 512.", 3,
        )
    authorization_count = sum(
        type(item) is dict and item.get("operation_type") == "AUTHORIZE_ASSIGNMENT"
        for item in operations
    )
    if authorization_count > MAX_AUTHORIZATIONS:
        raise RegistryFailure(
            "ROVER_SESSION_INVALID", "session", "Authorization decision count exceeds 256.", 3,
        )
    previous_tick = -1
    for index, raw_operation in enumerate(operations):
        operation = _exact_object(
            raw_operation,
            ("operation_id", "logical_tick", "operation_type", "payload"),
            f"operations[{index}]",
        )
        operation_id = _pattern(operation["operation_id"], OPERATION_ID_PATTERN, "operation_id")
        tick = _integer(operation["logical_tick"], "logical_tick", 0, 2147483647)
        if tick < previous_tick:
            raise RegistryFailure(
                "ROVER_SESSION_TICK_REVERSED", "session",
                "Operation logical ticks must be nondecreasing.", 3, operation_id,
            )
        previous_tick = tick
        operation_type = operation["operation_type"]
        if operation_type not in OPERATION_TYPES:
            raise RegistryFailure(
                "ROVER_OPERATION_UNKNOWN", "session", "Operation type is unknown.", 3, operation_id,
            )
        _validate_operation_payload(str(operation_type), operation["payload"], index)
    return session


def _validate_operation_payload(operation_type: str, value: object, index: int) -> None:
    context = f"operations[{index}].payload"
    if operation_type == "REGISTER_ROVER":
        payload = _exact_object(
            value,
            (
                "rover_id", "display_name", "role", "initial_state", "enabled",
                "profile_revision", "hardware_class", "allowed_fields", "allowed_units",
            ),
            context,
        )
        _pattern(payload["rover_id"], ROVER_ID_PATTERN, "rover_id")
        _bounded_text(payload["display_name"], "display_name")
        if payload["role"] not in ROLES:
            raise RegistryFailure("ROVER_PROFILE_INVALID", "profile", "Role is invalid.", 3)
        if payload["initial_state"] != "PENDING":
            raise RegistryFailure(
                "ROVER_PROFILE_INVALID", "profile", "Initial state must be PENDING.", 3,
            )
        _boolean(payload["enabled"], "enabled")
        if type(payload["profile_revision"]) is not int or payload["profile_revision"] != 1:
            raise RegistryFailure(
                "ROVER_REVISION_SEQUENCE_INVALID", "profile",
                "Registration profile revision must be 1.", 3,
            )
        if payload["hardware_class"] not in HARDWARE_CLASSES:
            raise RegistryFailure(
                "ROVER_PROFILE_INVALID", "profile", "Hardware class is invalid.", 3,
            )
        _permission_array(
            payload["allowed_fields"], FIELD_ID_PATTERN, "allowed_fields",
            MAX_FIELD_PERMISSIONS, "ROVER_FIELD_PERMISSION_DUPLICATE",
        )
        _permission_array(
            payload["allowed_units"], UNIT_ID_PATTERN, "allowed_units",
            MAX_UNIT_PERMISSIONS, "ROVER_UNIT_PERMISSION_DUPLICATE",
        )
    elif operation_type == "REVISE_ROVER":
        payload = _exact_object(
            value,
            (
                "rover_id", "expected_revision", "new_revision", "display_name", "role",
                "enabled", "hardware_class", "allowed_fields", "allowed_units",
                "operator_approved", "rover_confirmed_stopped", "active_mission_count",
                "charging_transition_count",
            ),
            context,
        )
        _pattern(payload["rover_id"], ROVER_ID_PATTERN, "rover_id")
        expected = _integer(payload["expected_revision"], "expected_revision", 1, 2147483646)
        new_revision = _integer(payload["new_revision"], "new_revision", 2, 2147483647)
        if new_revision != expected + 1:
            raise RegistryFailure(
                "ROVER_REVISION_SEQUENCE_INVALID", "profile",
                "New revision must equal expected revision plus one.", 3,
            )
        _bounded_text(payload["display_name"], "display_name")
        if payload["role"] not in ROLES or payload["hardware_class"] not in HARDWARE_CLASSES:
            raise RegistryFailure("ROVER_PROFILE_INVALID", "profile", "Profile enum is invalid.", 3)
        _boolean(payload["enabled"], "enabled")
        _permission_array(
            payload["allowed_fields"], FIELD_ID_PATTERN, "allowed_fields",
            MAX_FIELD_PERMISSIONS, "ROVER_FIELD_PERMISSION_DUPLICATE",
        )
        _permission_array(
            payload["allowed_units"], UNIT_ID_PATTERN, "allowed_units",
            MAX_UNIT_PERMISSIONS, "ROVER_UNIT_PERMISSION_DUPLICATE",
        )
        _validate_safety_fields(payload)
    elif operation_type == "SET_REGISTRATION_STATE":
        payload = _exact_object(
            value,
            (
                "rover_id", "target_state", "operator_approved", "rover_confirmed_stopped",
                "active_mission_count", "charging_transition_count", "reason",
            ),
            context,
        )
        _pattern(payload["rover_id"], ROVER_ID_PATTERN, "rover_id")
        if payload["target_state"] not in REGISTRATION_STATES:
            raise RegistryFailure(
                "ROVER_PROFILE_INVALID", "profile", "Registration state is invalid.", 3,
            )
        _validate_safety_fields(payload)
        _bounded_text(payload["reason"], "reason", 256)
    elif operation_type == "AUTHORIZE_ASSIGNMENT":
        payload = _exact_object(
            value,
            (
                "authorization_id", "rover_id", "mission_id", "mission_state", "active_field_id",
                "requested_field_id", "requested_unit_id", "operator_approved",
                "rover_reported_stopped", "communication_available", "fault_present",
                "battery_percentage", "physical_estop_asserted",
            ),
            context,
        )
        _pattern(payload["authorization_id"], AUTHORIZATION_ID_PATTERN, "authorization_id")
        _pattern(payload["rover_id"], ROVER_ID_PATTERN, "rover_id")
        _pattern(payload["mission_id"], MISSION_ID_PATTERN, "mission_id")
        if payload["mission_state"] not in MISSION_STATES:
            raise RegistryFailure("ROVER_SESSION_INVALID", "session", "Mission state is invalid.", 3)
        _pattern(payload["active_field_id"], FIELD_ID_PATTERN, "active_field_id")
        _pattern(payload["requested_field_id"], FIELD_ID_PATTERN, "requested_field_id")
        _pattern(payload["requested_unit_id"], UNIT_ID_PATTERN, "requested_unit_id")
        _boolean(payload["operator_approved"], "operator_approved")
        _boolean(payload["rover_reported_stopped"], "rover_reported_stopped")
        _boolean(payload["communication_available"], "communication_available")
        _boolean(payload["fault_present"], "fault_present")
        _integer(payload["battery_percentage"], "battery_percentage", 0, 100)
        _boolean(payload["physical_estop_asserted"], "physical_estop_asserted")
    else:
        _exact_object(value, (), context)


def canonical_json(value: object, *, sort_keys: bool = True) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=sort_keys,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def operation_request_sha256(operation: dict[str, object]) -> str:
    return sha256_text(canonical_json(operation))


def open_database(path: Path) -> tuple[sqlite3.Connection, RuntimeConfiguration]:
    connection = sqlite3.connect(path, isolation_level=None)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        journal_mode = str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]).lower()
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute("PRAGMA busy_timeout = 5000")
        configuration = RuntimeConfiguration(
            journal_mode,
            int(connection.execute("PRAGMA synchronous").fetchone()[0]),
            int(connection.execute("PRAGMA foreign_keys").fetchone()[0]),
            int(connection.execute("PRAGMA busy_timeout").fetchone()[0]),
        )
        if configuration != RuntimeConfiguration("wal", 2, 1, 5000):
            raise sqlite3.OperationalError("Required SQLite runtime configuration was not applied.")
        return connection, configuration
    except BaseException:
        connection.close()
        raise


def initialize_or_verify_schema(connection: sqlite3.Connection, schema_path: Path) -> bool:
    try:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        rows = dict(connection.execute(
            "SELECT metadata_key, metadata_value FROM rover_schema_metadata ORDER BY metadata_key"
        ).fetchall())
        if not rows:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.executemany(
                    "INSERT INTO rover_schema_metadata(metadata_key, metadata_value) VALUES (?, ?)",
                    (("schema_version", SCHEMA_VERSION), ("application_phase", PHASE)),
                )
                connection.execute("COMMIT")
            except BaseException:
                connection.execute("ROLLBACK")
                raise
            return True
        if rows != {"application_phase": PHASE, "schema_version": SCHEMA_VERSION}:
            raise RegistryFailure(
                "ROVER_SCHEMA_VERSION_UNSUPPORTED", "schema",
                "Database schema metadata is unsupported.", 3,
            )
        return False
    except RegistryFailure:
        raise
    except (OSError, UnicodeError, sqlite3.Error) as exc:
        raise RegistryFailure(
            "ROVER_SCHEMA_INITIALIZATION_FAILED", "schema",
            "Schema initialization or verification failed.", 3,
        ) from exc


def verify_schema_version(connection: sqlite3.Connection) -> None:
    try:
        rows = dict(connection.execute(
            "SELECT metadata_key, metadata_value FROM rover_schema_metadata ORDER BY metadata_key"
        ).fetchall())
    except sqlite3.Error as exc:
        raise RegistryFailure(
            "ROVER_SCHEMA_VERSION_UNSUPPORTED", "schema",
            "Schema metadata cannot be read after reopen.", 3,
        ) from exc
    if rows != {"application_phase": PHASE, "schema_version": SCHEMA_VERSION}:
        raise RegistryFailure(
            "ROVER_SCHEMA_VERSION_UNSUPPORTED", "schema",
            "Schema metadata is unsupported after reopen.", 3,
        )


def integrity_check(connection: sqlite3.Connection) -> str:
    try:
        rows = connection.execute("PRAGMA integrity_check").fetchall()
    except sqlite3.Error as exc:
        raise RegistryFailure(
            "ROVER_INTEGRITY_CHECK_FAILED", "integrity",
            "SQLite integrity check could not be executed.", 5,
        ) from exc
    if rows != [("ok",)]:
        raise RegistryFailure(
            "ROVER_INTEGRITY_CHECK_FAILED", "integrity",
            "SQLite integrity check did not return OK.", 5,
        )
    return "OK"


def canonical_database_state(connection: sqlite3.Connection) -> dict[str, object]:
    state: dict[str, object] = {}
    for table_name, columns, order_by in TABLE_DEFINITIONS:
        rows = connection.execute(
            f"SELECT {', '.join(columns)} FROM {table_name} ORDER BY {order_by}"
        ).fetchall()
        state[table_name] = [dict(zip(columns, row, strict=True)) for row in rows]
    return state


def empty_canonical_state() -> dict[str, object]:
    return {table_name: [] for table_name, _columns, _key in TABLE_DEFINITIONS}


def canonical_state_sha256(state: dict[str, object]) -> str:
    return sha256_text(canonical_json(state, sort_keys=False))


def _profile_document(payload: dict[str, object], revision: int) -> dict[str, object]:
    return {
        "rover_id": payload["rover_id"],
        "display_name": payload["display_name"],
        "role": payload["role"],
        "enabled": payload["enabled"],
        "profile_revision": revision,
        "hardware_class": payload["hardware_class"],
        "allowed_fields": payload["allowed_fields"],
        "allowed_units": payload["allowed_units"],
    }


def _insert_processed_operation(
    connection: sqlite3.Connection,
    operation: dict[str, object],
    request_hash: str,
) -> None:
    connection.execute(
        "INSERT INTO rover_processed_operations(operation_id, request_sha256, operation_type, logical_tick, result_code) "
        "VALUES (?, ?, ?, ?, 'APPLIED')",
        (
            operation["operation_id"], request_hash, operation["operation_type"],
            operation["logical_tick"],
        ),
    )


def _register_rover(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    payload = operation["payload"]
    operation_id = str(operation["operation_id"])
    if connection.execute("SELECT 1 FROM rover_registry WHERE rover_id = ?", (payload["rover_id"],)).fetchone():
        raise RegistryFailure(
            "ROVER_ALREADY_EXISTS", "operation", "Rover ID is already registered.", 4, operation_id,
        )
    if int(connection.execute("SELECT COUNT(*) FROM rover_registry").fetchone()[0]) >= MAX_ROVERS:
        raise RegistryFailure(
            "ROVER_PROFILE_INVALID", "operation", "Rover catalog limit is reached.", 4, operation_id,
        )
    profile = _profile_document(payload, 1)
    profile_json = canonical_json(profile)
    try:
        connection.execute(
            "INSERT INTO rover_registry(rover_id, display_name, role, registration_state, enabled, "
            "profile_revision, hardware_class, profile_json, profile_sha256) "
            "VALUES (?, ?, ?, 'PENDING', ?, 1, ?, ?, ?)",
            (
                payload["rover_id"], payload["display_name"], payload["role"], int(payload["enabled"]),
                payload["hardware_class"], profile_json, sha256_text(profile_json),
            ),
        )
        connection.executemany(
            "INSERT INTO rover_allowed_fields(rover_id, field_id, enabled) VALUES (?, ?, 1)",
            [(payload["rover_id"], field_id) for field_id in payload["allowed_fields"]],
        )
        connection.executemany(
            "INSERT INTO rover_allowed_units(rover_id, unit_id, enabled) VALUES (?, ?, 1)",
            [(payload["rover_id"], unit_id) for unit_id in payload["allowed_units"]],
        )
    except sqlite3.IntegrityError as exc:
        raise RegistryFailure(
            "ROVER_ALREADY_EXISTS", "operation",
            "Rover or permission identity conflicts with committed state.", 4, operation_id,
        ) from exc
    return OperationDelta(
        rovers_created=1,
        fields_created=len(payload["allowed_fields"]),
        units_created=len(payload["allowed_units"]),
    )


def _safety_gate(payload: dict[str, object], operation_id: str) -> None:
    if payload["operator_approved"] is not True:
        raise RegistryFailure(
            "ROVER_OPERATOR_APPROVAL_REQUIRED", "safety", "Operator approval is required.", 4,
            operation_id,
        )
    if payload["rover_confirmed_stopped"] is not True:
        raise RegistryFailure(
            "ROVER_NOT_STOPPED", "safety", "Rover must be confirmed stopped.", 4, operation_id,
        )
    if int(payload["active_mission_count"]) != 0:
        raise RegistryFailure(
            "ROVER_ACTIVE_MISSION_PRESENT", "safety", "Active missions prevent this change.", 4,
            operation_id,
        )
    if int(payload["charging_transition_count"]) != 0:
        raise RegistryFailure(
            "ROVER_CHARGING_TRANSITION_ACTIVE", "safety",
            "Charging transitions prevent this change.", 4, operation_id,
        )


def _revise_rover(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    payload = operation["payload"]
    operation_id = str(operation["operation_id"])
    row = connection.execute(
        "SELECT profile_revision, registration_state FROM rover_registry WHERE rover_id = ?",
        (payload["rover_id"],),
    ).fetchone()
    if row is None:
        raise RegistryFailure("ROVER_NOT_FOUND", "operation", "Rover does not exist.", 4, operation_id)
    if row[1] == "REVOKED":
        raise RegistryFailure(
            "ROVER_STATE_TRANSITION_INVALID", "operation", "Revoked rover cannot be revised.", 4,
            operation_id,
        )
    if int(row[0]) != int(payload["expected_revision"]):
        raise RegistryFailure(
            "ROVER_REVISION_CONFLICT", "operation", "Expected revision does not match.", 4,
            operation_id,
        )
    _safety_gate(payload, operation_id)
    profile = _profile_document(payload, int(payload["new_revision"]))
    profile_json = canonical_json(profile)
    connection.execute(
        "UPDATE rover_registry SET display_name = ?, role = ?, enabled = ?, profile_revision = ?, "
        "hardware_class = ?, profile_json = ?, profile_sha256 = ? WHERE rover_id = ?",
        (
            payload["display_name"], payload["role"], int(payload["enabled"]),
            payload["new_revision"], payload["hardware_class"], profile_json,
            sha256_text(profile_json), payload["rover_id"],
        ),
    )
    connection.execute("UPDATE rover_allowed_fields SET enabled = 0 WHERE rover_id = ?", (payload["rover_id"],))
    connection.execute("UPDATE rover_allowed_units SET enabled = 0 WHERE rover_id = ?", (payload["rover_id"],))
    for field_id in payload["allowed_fields"]:
        connection.execute(
            "INSERT INTO rover_allowed_fields(rover_id, field_id, enabled) VALUES (?, ?, 1) "
            "ON CONFLICT(rover_id, field_id) DO UPDATE SET enabled = 1",
            (payload["rover_id"], field_id),
        )
    for unit_id in payload["allowed_units"]:
        connection.execute(
            "INSERT INTO rover_allowed_units(rover_id, unit_id, enabled) VALUES (?, ?, 1) "
            "ON CONFLICT(rover_id, unit_id) DO UPDATE SET enabled = 1",
            (payload["rover_id"], unit_id),
        )
    return OperationDelta(rovers_revised=1)


def _set_registration_state(
    connection: sqlite3.Connection,
    operation: dict[str, object],
) -> OperationDelta:
    payload = operation["payload"]
    operation_id = str(operation["operation_id"])
    row = connection.execute(
        "SELECT registration_state FROM rover_registry WHERE rover_id = ?", (payload["rover_id"],)
    ).fetchone()
    if row is None:
        raise RegistryFailure("ROVER_NOT_FOUND", "operation", "Rover does not exist.", 4, operation_id)
    current = str(row[0])
    target = str(payload["target_state"])
    _safety_gate(payload, operation_id)
    if current == target:
        return OperationDelta()
    if target not in VALID_TRANSITIONS[current]:
        raise RegistryFailure(
            "ROVER_STATE_TRANSITION_INVALID", "operation",
            "Registration state transition is not allowed.", 4, operation_id,
        )
    connection.execute(
        "UPDATE rover_registry SET registration_state = ? WHERE rover_id = ?",
        (target, payload["rover_id"]),
    )
    return OperationDelta(state_changed=1)


def _is_permission_enabled(
    connection: sqlite3.Connection,
    table: str,
    column: str,
    rover_id: object,
    value: object,
) -> bool:
    row = connection.execute(
        f"SELECT enabled FROM {table} WHERE rover_id = ? AND {column} = ?",
        (rover_id, value),
    ).fetchone()
    return row is not None and int(row[0]) == 1


def evaluate_authorization(
    connection: sqlite3.Connection,
    payload: dict[str, object],
) -> tuple[str, list[str]]:
    row = connection.execute(
        "SELECT enabled, registration_state FROM rover_registry WHERE rover_id = ?",
        (payload["rover_id"],),
    ).fetchone()
    if row is None:
        raise RegistryFailure(
            "ROVER_NOT_FOUND", "authorization", "Authorization rover does not exist.", 4,
        )
    reasons: list[str] = []
    conditions = (
        (int(row[0]) != 1, "ROVER_DISABLED"),
        (row[1] != "REGISTERED", "ROVER_NOT_REGISTERED"),
        (
            not _is_permission_enabled(
                connection, "rover_allowed_fields", "field_id",
                payload["rover_id"], payload["requested_field_id"],
            ),
            "FIELD_NOT_ALLOWED",
        ),
        (
            not _is_permission_enabled(
                connection, "rover_allowed_units", "unit_id",
                payload["rover_id"], payload["requested_unit_id"],
            ),
            "UNIT_NOT_ALLOWED",
        ),
        (payload["active_field_id"] != payload["requested_field_id"], "ACTIVE_FIELD_MISMATCH"),
        (payload["operator_approved"] is not True, "OPERATOR_APPROVAL_REQUIRED"),
        (payload["mission_state"] != "QUEUED", "MISSION_STATE_NOT_QUEUED"),
        (payload["rover_reported_stopped"] is not True, "ROVER_NOT_STOPPED"),
        (payload["communication_available"] is not True, "COMMUNICATION_UNAVAILABLE"),
        (payload["fault_present"] is True, "FAULT_PRESENT"),
        (int(payload["battery_percentage"]) < 20, "BATTERY_BELOW_RESERVE"),
        (payload["physical_estop_asserted"] is True, "PHYSICAL_ESTOP_ASSERTED"),
    )
    reasons.extend(code for condition, code in conditions if condition)
    return ("AUTHORIZED", ["AUTHORIZED"]) if not reasons else ("DENIED", reasons)


def _authorize_assignment(
    connection: sqlite3.Connection,
    operation: dict[str, object],
) -> OperationDelta:
    payload = operation["payload"]
    operation_id = str(operation["operation_id"])
    if connection.execute(
        "SELECT 1 FROM rover_authorization_decisions WHERE authorization_id = ?",
        (payload["authorization_id"],),
    ).fetchone():
        raise RegistryFailure(
            "ROVER_AUTHORIZATION_ID_CONFLICT", "authorization",
            "Authorization ID is already recorded.", 4, operation_id,
        )
    try:
        decision, reasons = evaluate_authorization(connection, payload)
    except RegistryFailure as failure:
        failure.operation_id = operation_id
        raise
    context = dict(payload)
    context_json = canonical_json(context)
    connection.execute(
        "INSERT INTO rover_authorization_decisions(authorization_id, operation_id, rover_id, mission_id, "
        "requested_field_id, requested_unit_id, logical_tick, decision, reason_codes_json, context_json, "
        "context_sha256, direct_output_authority) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
        (
            payload["authorization_id"], operation_id, payload["rover_id"], payload["mission_id"],
            payload["requested_field_id"], payload["requested_unit_id"], operation["logical_tick"],
            decision, canonical_json(reasons), context_json, sha256_text(context_json),
        ),
    )
    return OperationDelta(decisions_created=1)


def _process_operation(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    operation_type = str(operation["operation_type"])
    if operation_type == "REGISTER_ROVER":
        return _register_rover(connection, operation)
    if operation_type == "REVISE_ROVER":
        return _revise_rover(connection, operation)
    if operation_type == "SET_REGISTRATION_STATE":
        return _set_registration_state(connection, operation)
    if operation_type == "AUTHORIZE_ASSIGNMENT":
        return _authorize_assignment(connection, operation)
    if integrity_check(connection) != "OK":
        raise RegistryFailure(
            "ROVER_INTEGRITY_CHECK_FAILED", "integrity", "Integrity verification failed.", 5,
            str(operation["operation_id"]),
        )
    return OperationDelta()


def _diagnostic(failure: RegistryFailure) -> dict[str, object]:
    return {
        "severity": "ERROR",
        "code": failure.code,
        "component": failure.component,
        "operation_id": failure.operation_id,
        "message": failure.message,
    }


def _build_report(
    session_id: str,
    created: bool,
    reopened: bool,
    configuration: RuntimeConfiguration | None,
    begun: bool,
    committed: bool,
    rolled_back: bool,
    initialized: bool,
    input_count: int,
    processed_count: int,
    applied_count: int,
    duplicate_count: int,
    rejected_count: int,
    delta: OperationDelta,
    conflict_count: int,
    integrity_result: str,
    state: dict[str, object],
    diagnostics: list[dict[str, object]],
    exit_code: int,
) -> RegistryReport:
    diagnostics = sorted(
        diagnostics,
        key=lambda item: (
            str(item["component"]), str(item["code"]),
            str(item["operation_id"]), str(item["message"]),
        ),
    )
    counts = {name: len(state[name]) for name, _columns, _key in TABLE_DEFINITIONS}
    rovers = state["rover_registry"]
    fields = state["rover_allowed_fields"]
    units = state["rover_allowed_units"]
    decisions = state["rover_authorization_decisions"]
    config = configuration or RuntimeConfiguration("", 0, 0, 0)
    document: dict[str, object] = {
        "report_version": REPORT_VERSION,
        "phase": PHASE,
        "session_id": session_id,
        "result": "PASS" if exit_code == 0 else "FAIL",
        "database": {
            "created": created,
            "reopened": reopened,
            "database_outside_repository": True,
            "journal_mode": config.journal_mode,
            "synchronous": "FULL" if config.synchronous == 2 else "",
            "foreign_keys": config.foreign_keys == 1,
            "busy_timeout_ms": config.busy_timeout_ms,
        },
        "transaction": {
            "atomic_session": True,
            "begun": begun,
            "committed": committed,
            "rolled_back": rolled_back,
        },
        "schema": {
            "schema_version": 1 if initialized or reopened else 0,
            "supported": initialized or reopened,
            "initialized": initialized,
            "migration_performed": False,
        },
        "operations": {
            "input_count": input_count,
            "processed_count": processed_count,
            "applied_count": applied_count if committed else 0,
            "duplicate_noop_count": duplicate_count,
            "rejected_count": rejected_count,
        },
        "rovers": {
            "created_count": delta.rovers_created if committed else 0,
            "revised_count": delta.rovers_revised if committed else 0,
            "state_changed_count": delta.state_changed if committed else 0,
            "pending_count": sum(row["registration_state"] == "PENDING" for row in rovers),
            "registered_count": sum(row["registration_state"] == "REGISTERED" for row in rovers),
            "suspended_count": sum(row["registration_state"] == "SUSPENDED" for row in rovers),
            "revoked_count": sum(row["registration_state"] == "REVOKED" for row in rovers),
            "enabled_count": sum(int(row["enabled"]) == 1 for row in rovers),
            "disabled_count": sum(int(row["enabled"]) == 0 for row in rovers),
            "total_count": counts["rover_registry"],
        },
        "field_permissions": {
            "created_count": delta.fields_created if committed else 0,
            "total_count": counts["rover_allowed_fields"],
            "enabled_count": sum(int(row["enabled"]) == 1 for row in fields),
        },
        "unit_permissions": {
            "created_count": delta.units_created if committed else 0,
            "total_count": counts["rover_allowed_units"],
            "enabled_count": sum(int(row["enabled"]) == 1 for row in units),
        },
        "authorization_decisions": {
            "created_count": delta.decisions_created if committed else 0,
            "total_count": counts["rover_authorization_decisions"],
            "authorized_count": sum(row["decision"] == "AUTHORIZED" for row in decisions),
            "denied_count": sum(row["decision"] == "DENIED" for row in decisions),
            "direct_output_authority": False,
        },
        "integrity": {
            "check_performed": integrity_result != "NOT_PERFORMED",
            "result": integrity_result,
        },
        "idempotency": {
            "request_hash_algorithm": "SHA256_CANONICAL_JSON",
            "duplicate_noop_count": duplicate_count,
            "conflict_count": conflict_count,
        },
        "safety": {
            "offline_only": True,
            "network_access_performed": False,
            "gpio_access_performed": False,
            "serial_access_performed": False,
            "hardware_output_performed": False,
            "motor_control_performed": False,
            "charging_control_performed": False,
            "rover_communication_performed": False,
            "actual_assignment_performed": False,
            "actual_arm_performed": False,
            "field_navigation_performed": False,
            "cryptographic_authentication_performed": False,
            "automatic_registration_performed": False,
            "automatic_state_transition_performed": False,
            "direct_output_authority": False,
            "repository_modified": False,
            "physical_estop_independent": True,
        },
        "summary": {
            "table_count": 6,
            "row_count_total": sum(counts.values()),
            "diagnostic_count": len(diagnostics),
            "authorized_decision_count": sum(row["decision"] == "AUTHORIZED" for row in decisions),
            "denied_decision_count": sum(row["decision"] == "DENIED" for row in decisions),
            "next_phase_eligible": exit_code == 0,
        },
        "diagnostics": diagnostics,
        "canonical_state_sha256": canonical_state_sha256(state),
        "exit_code": exit_code,
    }
    return RegistryReport(document, exit_code)


def run_registry_session(
    arguments: RegistryArguments,
    *,
    fail_after_operation_index: int | None = None,
    write_reports: bool = False,
    operation_processor: Callable[[sqlite3.Connection, dict[str, object]], OperationDelta] = _process_operation,
) -> RegistryReport:
    validate_arguments(arguments)
    try:
        session = validate_session(load_strict_json(arguments.session))
    except RegistryFailure as failure:
        report = _build_report(
            "SESSION-ST006-INVALID", False, False, None, False, False, False, False,
            0, 0, 0, 0, 1, OperationDelta(), 0, "NOT_PERFORMED",
            empty_canonical_state(), [_diagnostic(failure)], failure.exit_code,
        )
        return _write_requested_reports(report, arguments) if write_reports else report

    session_id = str(session["session_id"])
    operations = session["operations"]
    database_created = not arguments.database.exists()
    configuration: RuntimeConfiguration | None = None
    initialized = False
    reopened = False
    begun = False
    committed = False
    rolled_back = False
    processed_count = 0
    applied_count = 0
    duplicate_count = 0
    rejected_count = 0
    conflict_count = 0
    integrity_result = "NOT_PERFORMED"
    exit_code = 0
    diagnostics: list[dict[str, object]] = []
    state = empty_canonical_state()
    delta = OperationDelta()
    connection: sqlite3.Connection | None = None
    schema_path = arguments.repository_root / "software" / "station_control" / "storage" / "rover_registry_schema_v1.sql"

    try:
        connection, configuration = open_database(arguments.database)
        initialized = initialize_or_verify_schema(connection, schema_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            begun = True
        except sqlite3.Error as exc:
            raise RegistryFailure(
                "ROVER_TRANSACTION_BEGIN_FAILED", "transaction",
                "Atomic rover registry transaction could not begin.", 4,
            ) from exc
        for index, operation in enumerate(operations):
            operation_id = str(operation["operation_id"])
            request_hash = operation_request_sha256(operation)
            existing = connection.execute(
                "SELECT request_sha256 FROM rover_processed_operations WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
            if existing is not None:
                if existing[0] != request_hash:
                    conflict_count = 1
                    raise RegistryFailure(
                        "ROVER_IDEMPOTENCY_CONFLICT", "idempotency",
                        "Operation ID was previously committed with different content.", 4, operation_id,
                    )
                duplicate_count += 1
                processed_count += 1
            else:
                _insert_processed_operation(connection, operation, request_hash)
                item = operation_processor(connection, operation)
                delta = OperationDelta(
                    delta.rovers_created + item.rovers_created,
                    delta.rovers_revised + item.rovers_revised,
                    delta.state_changed + item.state_changed,
                    delta.fields_created + item.fields_created,
                    delta.units_created + item.units_created,
                    delta.decisions_created + item.decisions_created,
                )
                applied_count += 1
                processed_count += 1
            if fail_after_operation_index is not None and index == fail_after_operation_index:
                raise InjectedInterruption("Test-only simulated power interruption.")
        connection.execute("COMMIT")
        committed = True
    except InjectedInterruption:
        exit_code = 4
        rejected_count = 1
        if connection is not None and begun and connection.in_transaction:
            connection.execute("ROLLBACK")
            rolled_back = True
        diagnostics.append(_diagnostic(RegistryFailure(
            "ROVER_TRANSACTION_ROLLED_BACK", "transaction",
            "Atomic rover registry session rolled back after simulated interruption.", 4,
        )))
    except RegistryFailure as failure:
        exit_code = failure.exit_code
        rejected_count = 1
        if failure.code == "ROVER_IDEMPOTENCY_CONFLICT":
            conflict_count = 1
        if connection is not None and begun and connection.in_transaction:
            connection.execute("ROLLBACK")
            rolled_back = True
            diagnostics.append(_diagnostic(RegistryFailure(
                "ROVER_TRANSACTION_ROLLED_BACK", "transaction",
                "Atomic rover registry session rolled back without partial commit.", 4,
            )))
        diagnostics.append(_diagnostic(failure))
    except sqlite3.Error:
        exit_code = 4
        rejected_count = 1
        if connection is not None and begun and connection.in_transaction:
            connection.execute("ROLLBACK")
            rolled_back = True
        diagnostics.append(_diagnostic(RegistryFailure(
            "ROVER_TRANSACTION_ROLLED_BACK", "transaction",
            "Atomic rover registry session rolled back after a SQLite failure.", 4,
        )))
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
    except RegistryFailure as failure:
        if exit_code == 0:
            exit_code = failure.exit_code
            diagnostics.append(_diagnostic(failure))
    except sqlite3.Error:
        if exit_code == 0:
            exit_code = 5
            diagnostics.append(_diagnostic(RegistryFailure(
                "ROVER_REOPEN_FAILED", "database", "Database could not be reopened.", 5,
            )))

    report = _build_report(
        session_id, database_created, reopened, configuration, begun, committed, rolled_back,
        initialized, len(operations), processed_count, applied_count, duplicate_count,
        rejected_count, delta, conflict_count, integrity_result, state, diagnostics, exit_code,
    )
    return _write_requested_reports(report, arguments) if write_reports else report


def render_json_report(report: RegistryReport) -> str:
    return json.dumps(report.document, ensure_ascii=True, indent=2, separators=(",", ": ")) + "\n"


def _text_value(value: object) -> str:
    return str(value).lower() if type(value) is bool else str(value)


def render_text_report(report: RegistryReport) -> str:
    document = report.document
    values = (
        ("report_version", document["report_version"]),
        ("phase", document["phase"]),
        ("session_id", document["session_id"]),
        ("result", document["result"]),
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
        ("rover_total_count", document["rovers"]["total_count"]),
        ("rover_registered_count", document["rovers"]["registered_count"]),
        ("rover_suspended_count", document["rovers"]["suspended_count"]),
        ("field_permission_total_count", document["field_permissions"]["total_count"]),
        ("unit_permission_total_count", document["unit_permissions"]["total_count"]),
        ("authorization_total_count", document["authorization_decisions"]["total_count"]),
        ("authorization_authorized_count", document["authorization_decisions"]["authorized_count"]),
        ("authorization_denied_count", document["authorization_decisions"]["denied_count"]),
        ("direct_output_authority", document["authorization_decisions"]["direct_output_authority"]),
        ("integrity_result", document["integrity"]["result"]),
        ("canonical_state_sha256", document["canonical_state_sha256"]),
        ("offline_only", document["safety"]["offline_only"]),
        ("network_access_performed", document["safety"]["network_access_performed"]),
        ("gpio_access_performed", document["safety"]["gpio_access_performed"]),
        ("serial_access_performed", document["safety"]["serial_access_performed"]),
        ("hardware_output_performed", document["safety"]["hardware_output_performed"]),
        ("actual_assignment_performed", document["safety"]["actual_assignment_performed"]),
        ("actual_arm_performed", document["safety"]["actual_arm_performed"]),
        ("diagnostic_count", document["summary"]["diagnostic_count"]),
        ("exit_code", document["exit_code"]),
    )
    return "\n".join(f"{key}={_text_value(value)}" for key, value in values) + "\n"


def write_report(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_requested_reports(
    report: RegistryReport,
    arguments: RegistryArguments,
) -> RegistryReport:
    try:
        write_report(arguments.json_report, render_json_report(report))
        write_report(arguments.text_report, render_text_report(report))
        return report
    except OSError:
        failure = RegistryFailure(
            "ROVER_REPORT_WRITE_FAILED", "report", "Report output failed.", 7,
        )
        document = dict(report.document)
        diagnostics = list(document["diagnostics"])
        diagnostics.append(_diagnostic(failure))
        diagnostics.sort(key=lambda item: (
            str(item["component"]), str(item["code"]),
            str(item["operation_id"]), str(item["message"]),
        ))
        document["result"] = "FAIL"
        document["diagnostics"] = diagnostics
        document["summary"] = dict(document["summary"])
        document["summary"]["diagnostic_count"] = len(diagnostics)
        document["summary"]["next_phase_eligible"] = False
        document["exit_code"] = 7
        return RegistryReport(document, 7)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_arguments(argv)
        report = run_registry_session(arguments, write_reports=True)
        print(render_text_report(report), end="")
        return report.exit_code
    except RegistryFailure as failure:
        print(f"ST-006 rover registry rejected: {failure.message}", file=sys.stderr)
        return failure.exit_code
    except ValueError:
        print("ST-006 rover registry rejected invalid CLI arguments.", file=sys.stderr)
        return 2
    except Exception:
        print(
            "ROVER_INTERNAL_ERROR: ST-006 rover registry failed because of an unexpected internal exception.",
            file=sys.stderr,
        )
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
