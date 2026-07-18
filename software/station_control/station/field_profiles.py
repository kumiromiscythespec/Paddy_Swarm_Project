"""Offline-only field profile registry and active-field selection for ST-005."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import sys
from typing import Callable, Sequence


REPORT_VERSION = 1
PHASE = "ST-005"
SESSION_VERSION = 1
SCHEMA_VERSION = "1"
MAX_FIELDS = 64
MAX_REFERENCES = 32
MAX_ZONES = 32
MAX_BOUNDARY_REFERENCES = 64
MAX_OPERATIONS = 256
OPERATION_TYPES = ("REGISTER_FIELD", "REVISE_FIELD", "SET_ACTIVE_FIELD", "VERIFY_INTEGRITY")
REFERENCE_TYPES = ("ENTRY", "WATER_INLET", "WATER_OUTLET", "RECOVERY_POINT", "STATION_POINT")
REQUIRED_REFERENCE_TYPES = ("ENTRY", "WATER_INLET", "WATER_OUTLET", "RECOVERY_POINT")
REASON_CODES = (
    "DEEP_WATER", "SOFT_MUD", "DRAIN", "OBSTACLE", "CROP_PROTECTION",
    "MACHINERY_ROUTE", "HUMAN_REVIEW_REQUIRED",
)
IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{2,63}$")
SESSION_ID_PATTERN = re.compile(r"^SESSION-ST005-[A-Z0-9-]{1,40}$")
LOCAL_FRAME_PATTERN = re.compile(r"^LOCAL-FRAME-[A-Z0-9-]{1,48}$")
LOCATION_PATTERN = re.compile(r"^local-ref:[a-z0-9][a-z0-9-]{0,63}$")
ZONE_REFERENCE_PATTERN = re.compile(r"^local-zone-ref:[a-z0-9][a-z0-9-]{0,63}$")
TABLE_DEFINITIONS = (
    ("field_schema_metadata", ("metadata_key", "metadata_value"), "metadata_key"),
    (
        "field_processed_operations",
        ("operation_id", "request_sha256", "operation_type", "logical_tick", "result_code"),
        "operation_id",
    ),
    (
        "field_profiles",
        (
            "field_id", "display_name", "enabled", "profile_revision", "local_frame_id",
            "profile_json", "profile_sha256",
        ),
        "field_id",
    ),
    (
        "field_references",
        ("reference_id", "field_id", "reference_type", "label", "location_reference", "enabled"),
        "reference_id",
    ),
    (
        "field_no_go_zones",
        ("zone_id", "field_id", "label", "reason_code", "boundary_json", "boundary_sha256", "enabled"),
        "zone_id",
    ),
    (
        "field_active_state",
        ("state_key", "active_field_id", "selection_revision", "last_operation_id"),
        "state_key",
    ),
)


class FieldFailure(RuntimeError):
    """Expected fail-closed field profile error."""

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
    """Test-only interruption raised inside the atomic session."""


@dataclass(frozen=True)
class FieldArguments:
    repository_root: Path
    database: Path
    session: Path
    json_report: Path
    text_report: Path


@dataclass(frozen=True)
class FieldReport:
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
    fields_created: int = 0
    fields_revised: int = 0
    references_created: int = 0
    zones_created: int = 0
    active_changed: bool = False


class DeterministicArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def parse_arguments(argv: Sequence[str] | None = None) -> FieldArguments:
    parser = DeterministicArgumentParser(
        description="Run an offline ST-005 field profile session."
    )
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--json-report", required=True, type=Path)
    parser.add_argument("--text-report", required=True, type=Path)
    values = parser.parse_args(argv)
    return FieldArguments(
        values.repository_root,
        values.database,
        values.session,
        values.json_report,
        values.text_report,
    )


def is_path_contained(candidate: Path, parent: Path) -> bool:
    try:
        child = candidate.resolve(strict=False)
        root = parent.resolve(strict=False)
        common = os.path.commonpath((str(child), str(root)))
    except (OSError, ValueError):
        return False
    return os.path.normcase(common) == os.path.normcase(str(root))


def validate_arguments(arguments: FieldArguments) -> None:
    repository = arguments.repository_root
    if not repository.is_dir():
        raise FieldFailure(
            "FIELD_REPOSITORY_ROOT_INVALID", "arguments",
            "Repository root must be an existing directory.", 2,
        )
    schema_path = repository / "software" / "station_control" / "storage" / "field_profiles_schema_v1.sql"
    if not schema_path.is_file():
        raise FieldFailure(
            "FIELD_REPOSITORY_ROOT_INVALID", "arguments",
            "Repository root does not contain the ST-005 SQL schema.", 2,
        )
    if not arguments.session.is_file():
        raise FieldFailure(
            "FIELD_INVALID_ARGUMENT", "arguments", "Session must be an existing file.", 2,
        )
    if is_path_contained(arguments.database, repository):
        raise FieldFailure(
            "FIELD_DATABASE_PATH_INSIDE_REPOSITORY", "database",
            "Database path must be outside the repository.", 2,
        )
    if not arguments.database.parent.is_dir():
        raise FieldFailure(
            "FIELD_DATABASE_PARENT_INVALID", "database",
            "Database parent must be an existing directory.", 2,
        )
    for report_path in (arguments.json_report, arguments.text_report):
        if is_path_contained(report_path, repository):
            raise FieldFailure(
                "FIELD_REPORT_PATH_INSIDE_REPOSITORY", "report",
                "Report path must be outside the repository.", 2,
            )
        if not report_path.parent.is_dir():
            raise FieldFailure(
                "FIELD_REPORT_PARENT_INVALID", "report",
                "Report parent must be an existing directory.", 2,
            )
    paths = (
        arguments.database.resolve(strict=False),
        arguments.session.resolve(strict=False),
        arguments.json_report.resolve(strict=False),
        arguments.text_report.resolve(strict=False),
    )
    if len(set(paths)) != len(paths):
        raise FieldFailure(
            "FIELD_INVALID_ARGUMENT", "arguments",
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
        raise FieldFailure(
            "FIELD_SESSION_INVALID", "session", "Session is not readable strict JSON.", 3,
        ) from exc


def _exact_object(value: object, keys: tuple[str, ...], context: str) -> dict[str, object]:
    if type(value) is not dict or tuple(value) != keys:
        raise FieldFailure(
            "FIELD_SESSION_INVALID", "session",
            f"{context} properties or property order are invalid.", 3,
        )
    return value


def _identifier(value: object, context: str) -> str:
    if type(value) is not str or IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise FieldFailure(
            "FIELD_SESSION_INVALID", "session", f"{context} is not a demo identifier.", 3,
        )
    return value


def _bounded_string(value: object, context: str, maximum: int = 128) -> str:
    if type(value) is not str or not 1 <= len(value) <= maximum:
        raise FieldFailure(
            "FIELD_SESSION_INVALID", "session", f"{context} is not a bounded string.", 3,
        )
    lowered = value.lower()
    forbidden = ("latitude", "longitude", "gps", "gnss", "address", "credential", "secret", "token")
    if any(item in lowered for item in forbidden):
        raise FieldFailure(
            "FIELD_PROFILE_INVALID", "profile", f"{context} contains prohibited location or secret data.", 3,
        )
    return value


def _bounded_integer(value: object, context: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise FieldFailure(
            "FIELD_SESSION_INVALID", "session", f"{context} is outside its integer range.", 3,
        )
    return value


def _boolean(value: object, context: str) -> bool:
    if type(value) is not bool:
        raise FieldFailure(
            "FIELD_SESSION_INVALID", "session", f"{context} must be boolean.", 3,
        )
    return value


def _validate_reference(value: object, context: str) -> dict[str, object]:
    reference = _exact_object(
        value,
        ("reference_id", "reference_type", "label", "location_reference", "enabled"),
        context,
    )
    _identifier(reference["reference_id"], f"{context}.reference_id")
    if reference["reference_type"] not in REFERENCE_TYPES:
        raise FieldFailure(
            "FIELD_PROFILE_INVALID", "profile", "Reference type is unsupported.", 3,
        )
    _bounded_string(reference["label"], f"{context}.label")
    location = reference["location_reference"]
    if type(location) is not str or LOCATION_PATTERN.fullmatch(location) is None:
        raise FieldFailure(
            "FIELD_LOCATION_REFERENCE_INVALID", "profile",
            "Only abstract local-ref values are allowed.", 3,
        )
    _boolean(reference["enabled"], f"{context}.enabled")
    return reference


def _validate_zone(value: object, context: str) -> dict[str, object]:
    zone = _exact_object(value, ("zone_id", "label", "reason_code", "boundary", "enabled"), context)
    _identifier(zone["zone_id"], f"{context}.zone_id")
    _bounded_string(zone["label"], f"{context}.label")
    if zone["reason_code"] not in REASON_CODES:
        raise FieldFailure(
            "FIELD_PROFILE_INVALID", "profile", "No-go reason code is unsupported.", 3,
        )
    boundary = zone["boundary"]
    if type(boundary) is not list or not 3 <= len(boundary) <= MAX_BOUNDARY_REFERENCES:
        raise FieldFailure(
            "FIELD_ZONE_BOUNDARY_INVALID", "profile",
            "No-go boundary must contain 3 to 64 references.", 3,
        )
    if len(set(boundary)) != len(boundary):
        raise FieldFailure(
            "FIELD_ZONE_BOUNDARY_INVALID", "profile", "No-go boundary references must be unique.", 3,
        )
    if any(type(item) is not str or ZONE_REFERENCE_PATTERN.fullmatch(item) is None for item in boundary):
        raise FieldFailure(
            "FIELD_ZONE_BOUNDARY_INVALID", "profile",
            "No-go boundary must use abstract local-zone-ref values.", 3,
        )
    _boolean(zone["enabled"], f"{context}.enabled")
    return zone


def _validate_profile_collections(
    references_value: object,
    zones_value: object,
    context: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if type(references_value) is not list or not 1 <= len(references_value) <= MAX_REFERENCES:
        raise FieldFailure(
            "FIELD_PROFILE_INVALID", "profile", "Reference count must be between 1 and 32.", 3,
        )
    if type(zones_value) is not list or len(zones_value) > MAX_ZONES:
        raise FieldFailure(
            "FIELD_PROFILE_INVALID", "profile", "No-go zone count must be between 0 and 32.", 3,
        )
    references = [
        _validate_reference(item, f"{context}.references[{index}]")
        for index, item in enumerate(references_value)
    ]
    zones = [
        _validate_zone(item, f"{context}.no_go_zones[{index}]")
        for index, item in enumerate(zones_value)
    ]
    reference_ids = [str(item["reference_id"]) for item in references]
    zone_ids = [str(item["zone_id"]) for item in zones]
    if len(set(reference_ids)) != len(reference_ids):
        raise FieldFailure(
            "FIELD_REFERENCE_DUPLICATE", "profile", "Reference IDs must be unique.", 3,
        )
    if len(set(zone_ids)) != len(zone_ids):
        raise FieldFailure(
            "FIELD_ZONE_DUPLICATE", "profile", "No-go zone IDs must be unique.", 3,
        )
    enabled_types = {str(item["reference_type"]) for item in references if item["enabled"] is True}
    if not set(REQUIRED_REFERENCE_TYPES).issubset(enabled_types):
        raise FieldFailure(
            "FIELD_REFERENCE_REQUIRED_MISSING", "profile",
            "Enabled ENTRY, WATER_INLET, WATER_OUTLET, and RECOVERY_POINT references are required.", 3,
        )
    return references, zones


def _validate_profile_common(
    payload: dict[str, object],
    context: str,
    revision_key: str,
) -> None:
    _identifier(payload["field_id"], f"{context}.field_id")
    _bounded_string(payload["display_name"], f"{context}.display_name")
    _boolean(payload["enabled"], f"{context}.enabled")
    _bounded_integer(payload[revision_key], f"{context}.{revision_key}", 1, 2147483647)
    frame = payload["local_frame_id"]
    if type(frame) is not str or LOCAL_FRAME_PATTERN.fullmatch(frame) is None:
        raise FieldFailure(
            "FIELD_PROFILE_INVALID", "profile", "Local frame ID is invalid.", 3,
        )
    _validate_profile_collections(payload["references"], payload["no_go_zones"], context)


def validate_session(value: object) -> dict[str, object]:
    session = _exact_object(value, ("session_version", "session_id", "operations"), "session")
    if type(session["session_version"]) is not int or session["session_version"] != SESSION_VERSION:
        raise FieldFailure(
            "FIELD_SESSION_INVALID", "session", "Session version must be 1.", 3,
        )
    if type(session["session_id"]) is not str or SESSION_ID_PATTERN.fullmatch(session["session_id"]) is None:
        raise FieldFailure(
            "FIELD_SESSION_INVALID", "session", "Session ID must be an ST-005 demo ID.", 3,
        )
    operations = session["operations"]
    if type(operations) is not list or not 1 <= len(operations) <= MAX_OPERATIONS:
        raise FieldFailure(
            "FIELD_SESSION_INVALID", "session", "Operation count must be between 1 and 256.", 3,
        )
    previous_tick = -1
    for index, raw_operation in enumerate(operations):
        operation = _exact_object(
            raw_operation,
            ("operation_id", "logical_tick", "operation_type", "payload"),
            f"operations[{index}]",
        )
        operation_id = _identifier(operation["operation_id"], f"operations[{index}].operation_id")
        tick = _bounded_integer(operation["logical_tick"], "logical_tick", 0, 2147483647)
        if tick < previous_tick:
            raise FieldFailure(
                "FIELD_SESSION_TICK_REVERSED", "session",
                "Operation logical ticks must be nondecreasing.", 3, operation_id,
            )
        previous_tick = tick
        operation_type = operation["operation_type"]
        if operation_type not in OPERATION_TYPES:
            raise FieldFailure(
                "FIELD_OPERATION_UNKNOWN", "session", "Operation type is unknown.", 3, operation_id,
            )
        _validate_operation_payload(str(operation_type), operation["payload"], index)
    return session


def _validate_operation_payload(operation_type: str, value: object, index: int) -> None:
    context = f"operations[{index}].payload"
    if operation_type == "REGISTER_FIELD":
        payload = _exact_object(
            value,
            (
                "field_id", "display_name", "enabled", "profile_revision", "local_frame_id",
                "references", "no_go_zones",
            ),
            context,
        )
        _validate_profile_common(payload, context, "profile_revision")
        if payload["profile_revision"] != 1:
            raise FieldFailure(
                "FIELD_REVISION_SEQUENCE_INVALID", "profile", "Registration revision must be 1.", 3,
            )
    elif operation_type == "REVISE_FIELD":
        payload = _exact_object(
            value,
            (
                "field_id", "expected_revision", "new_revision", "display_name", "enabled",
                "local_frame_id", "references", "no_go_zones", "operator_approved",
                "all_rovers_stopped", "active_mission_count", "charging_transition_count",
            ),
            context,
        )
        _validate_profile_common(payload, context, "new_revision")
        expected = _bounded_integer(payload["expected_revision"], "expected_revision", 1, 2147483647)
        if payload["new_revision"] != expected + 1:
            raise FieldFailure(
                "FIELD_REVISION_SEQUENCE_INVALID", "profile",
                "New revision must equal expected revision plus one.", 3,
            )
        _boolean(payload["operator_approved"], "operator_approved")
        _boolean(payload["all_rovers_stopped"], "all_rovers_stopped")
        _bounded_integer(payload["active_mission_count"], "active_mission_count", 0, 2147483647)
        _bounded_integer(payload["charging_transition_count"], "charging_transition_count", 0, 2147483647)
    elif operation_type == "SET_ACTIVE_FIELD":
        payload = _exact_object(
            value,
            (
                "target_field_id", "operator_approved", "all_rovers_stopped",
                "active_mission_count", "charging_transition_count", "reason",
            ),
            context,
        )
        _identifier(payload["target_field_id"], "target_field_id")
        _boolean(payload["operator_approved"], "operator_approved")
        _boolean(payload["all_rovers_stopped"], "all_rovers_stopped")
        _bounded_integer(payload["active_mission_count"], "active_mission_count", 0, 2147483647)
        _bounded_integer(payload["charging_transition_count"], "charging_transition_count", 0, 2147483647)
        _bounded_string(payload["reason"], "reason", 256)
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
            "SELECT metadata_key, metadata_value FROM field_schema_metadata ORDER BY metadata_key"
        ).fetchall())
        if not rows:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.executemany(
                    "INSERT INTO field_schema_metadata(metadata_key, metadata_value) VALUES (?, ?)",
                    (("schema_version", SCHEMA_VERSION), ("application_phase", PHASE)),
                )
                connection.execute("COMMIT")
            except BaseException:
                connection.execute("ROLLBACK")
                raise
            return True
        if rows != {"application_phase": PHASE, "schema_version": SCHEMA_VERSION}:
            raise FieldFailure(
                "FIELD_SCHEMA_VERSION_UNSUPPORTED", "schema",
                "Database schema metadata is unsupported.", 3,
            )
        return False
    except FieldFailure:
        raise
    except (OSError, UnicodeError, sqlite3.Error) as exc:
        raise FieldFailure(
            "FIELD_SCHEMA_INITIALIZATION_FAILED", "schema",
            "Schema initialization or verification failed.", 3,
        ) from exc


def verify_schema_version(connection: sqlite3.Connection) -> None:
    try:
        rows = dict(connection.execute(
            "SELECT metadata_key, metadata_value FROM field_schema_metadata ORDER BY metadata_key"
        ).fetchall())
    except sqlite3.Error as exc:
        raise FieldFailure(
            "FIELD_SCHEMA_VERSION_UNSUPPORTED", "schema",
            "Schema metadata cannot be read after reopen.", 3,
        ) from exc
    if rows != {"application_phase": PHASE, "schema_version": SCHEMA_VERSION}:
        raise FieldFailure(
            "FIELD_SCHEMA_VERSION_UNSUPPORTED", "schema",
            "Schema metadata is unsupported after reopen.", 3,
        )


def integrity_check(connection: sqlite3.Connection) -> str:
    try:
        rows = connection.execute("PRAGMA integrity_check").fetchall()
    except sqlite3.Error as exc:
        raise FieldFailure(
            "FIELD_INTEGRITY_CHECK_FAILED", "integrity",
            "SQLite integrity check could not be executed.", 5,
        ) from exc
    if rows != [("ok",)]:
        raise FieldFailure(
            "FIELD_INTEGRITY_CHECK_FAILED", "integrity",
            "SQLite integrity check did not return OK.", 5,
        )
    return "OK"


def canonical_database_state(connection: sqlite3.Connection) -> dict[str, object]:
    state: dict[str, object] = {}
    for table_name, columns, primary_key in TABLE_DEFINITIONS:
        rows = connection.execute(
            f"SELECT {', '.join(columns)} FROM {table_name} ORDER BY {primary_key}"
        ).fetchall()
        state[table_name] = [dict(zip(columns, row, strict=True)) for row in rows]
    return state


def empty_canonical_state() -> dict[str, object]:
    return {table_name: [] for table_name, _columns, _key in TABLE_DEFINITIONS}


def canonical_state_sha256(state: dict[str, object]) -> str:
    return sha256_text(canonical_json(state, sort_keys=False))


def _profile_document(payload: dict[str, object], revision: int) -> dict[str, object]:
    return {
        "field_id": payload["field_id"],
        "display_name": payload["display_name"],
        "enabled": payload["enabled"],
        "profile_revision": revision,
        "local_frame_id": payload["local_frame_id"],
        "references": payload["references"],
        "no_go_zones": payload["no_go_zones"],
    }


def _insert_processed_operation(
    connection: sqlite3.Connection,
    operation: dict[str, object],
    request_hash: str,
) -> None:
    connection.execute(
        "INSERT INTO field_processed_operations(operation_id, request_sha256, operation_type, logical_tick, result_code) "
        "VALUES (?, ?, ?, ?, 'APPLIED')",
        (
            operation["operation_id"], request_hash, operation["operation_type"],
            operation["logical_tick"],
        ),
    )


def _insert_references(
    connection: sqlite3.Connection,
    field_id: object,
    references: list[dict[str, object]],
) -> None:
    connection.executemany(
        "INSERT INTO field_references(reference_id, field_id, reference_type, label, location_reference, enabled) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (
                item["reference_id"], field_id, item["reference_type"], item["label"],
                item["location_reference"], int(item["enabled"]),
            )
            for item in references
        ],
    )


def _insert_zones(
    connection: sqlite3.Connection,
    field_id: object,
    zones: list[dict[str, object]],
) -> None:
    rows = []
    for item in zones:
        boundary_json = canonical_json(item["boundary"], sort_keys=False)
        rows.append((
            item["zone_id"], field_id, item["label"], item["reason_code"], boundary_json,
            sha256_text(boundary_json), int(item["enabled"]),
        ))
    connection.executemany(
        "INSERT INTO field_no_go_zones(zone_id, field_id, label, reason_code, boundary_json, boundary_sha256, enabled) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )


def _register_field(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    payload = operation["payload"]
    field_id = payload["field_id"]
    if connection.execute("SELECT 1 FROM field_profiles WHERE field_id = ?", (field_id,)).fetchone():
        raise FieldFailure(
            "FIELD_ALREADY_EXISTS", "operation", "Field ID is already registered.", 4,
            str(operation["operation_id"]),
        )
    if int(connection.execute("SELECT COUNT(*) FROM field_profiles").fetchone()[0]) >= MAX_FIELDS:
        raise FieldFailure(
            "FIELD_PROFILE_INVALID", "operation", "Field catalog limit is reached.", 4,
            str(operation["operation_id"]),
        )
    profile = _profile_document(payload, 1)
    profile_json = canonical_json(profile, sort_keys=False)
    references = payload["references"]
    zones = payload["no_go_zones"]
    try:
        connection.execute(
            "INSERT INTO field_profiles(field_id, display_name, enabled, profile_revision, local_frame_id, "
            "profile_json, profile_sha256) VALUES (?, ?, ?, 1, ?, ?, ?)",
            (
                field_id, payload["display_name"], int(payload["enabled"]), payload["local_frame_id"],
                profile_json, sha256_text(profile_json),
            ),
        )
        _insert_references(connection, field_id, references)
        _insert_zones(connection, field_id, zones)
    except sqlite3.IntegrityError as exc:
        raise FieldFailure(
            "FIELD_REFERENCE_DUPLICATE", "operation",
            "Field, reference, or zone identity conflicts with committed state.", 4,
            str(operation["operation_id"]),
        ) from exc
    return OperationDelta(1, 0, len(references), len(zones), False)


def _required_references_present(connection: sqlite3.Connection, field_id: object) -> bool:
    rows = connection.execute(
        "SELECT reference_type FROM field_references WHERE field_id = ? AND enabled = 1",
        (field_id,),
    ).fetchall()
    return set(REQUIRED_REFERENCE_TYPES).issubset({str(row[0]) for row in rows})


def _safety_gate(payload: dict[str, object], operation_id: str) -> None:
    if payload["operator_approved"] is not True:
        raise FieldFailure(
            "FIELD_OPERATOR_APPROVAL_REQUIRED", "safety", "Operator approval is required.", 4,
            operation_id,
        )
    if payload["all_rovers_stopped"] is not True:
        raise FieldFailure(
            "FIELD_ROVERS_NOT_STOPPED", "safety", "All rovers must be stopped.", 4, operation_id,
        )
    if int(payload["active_mission_count"]) != 0:
        raise FieldFailure(
            "FIELD_ACTIVE_MISSION_PRESENT", "safety", "Active missions prevent this change.", 4,
            operation_id,
        )
    if int(payload["charging_transition_count"]) != 0:
        raise FieldFailure(
            "FIELD_CHARGING_TRANSITION_ACTIVE", "safety",
            "Charging transitions prevent this change.", 4, operation_id,
        )


def _revise_field(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    payload = operation["payload"]
    operation_id = str(operation["operation_id"])
    row = connection.execute(
        "SELECT profile_revision FROM field_profiles WHERE field_id = ?",
        (payload["field_id"],),
    ).fetchone()
    if row is None:
        raise FieldFailure(
            "FIELD_NOT_FOUND", "operation", "Field does not exist.", 4, operation_id,
        )
    if int(row[0]) != int(payload["expected_revision"]):
        raise FieldFailure(
            "FIELD_REVISION_CONFLICT", "operation", "Expected revision does not match.", 4,
            operation_id,
        )
    if payload["operator_approved"] is not True:
        raise FieldFailure(
            "FIELD_OPERATOR_APPROVAL_REQUIRED", "safety", "Revision requires operator approval.", 4,
            operation_id,
        )
    active = connection.execute(
        "SELECT active_field_id FROM field_active_state WHERE state_key = 'ACTIVE_FIELD'"
    ).fetchone()
    if active is not None and active[0] == payload["field_id"]:
        _safety_gate(payload, operation_id)
    references = payload["references"]
    zones = payload["no_go_zones"]
    existing_reference_ids = {
        str(row[0]) for row in connection.execute(
            "SELECT reference_id FROM field_references WHERE field_id = ?", (payload["field_id"],)
        ).fetchall()
    }
    existing_zone_ids = {
        str(row[0]) for row in connection.execute(
            "SELECT zone_id FROM field_no_go_zones WHERE field_id = ?", (payload["field_id"],)
        ).fetchall()
    }
    if existing_reference_ids != {str(item["reference_id"]) for item in references}:
        raise FieldFailure(
            "FIELD_PROFILE_INVALID", "operation",
            "Revision must preserve reference identities in schema version 1.", 4, operation_id,
        )
    if existing_zone_ids != {str(item["zone_id"]) for item in zones}:
        raise FieldFailure(
            "FIELD_PROFILE_INVALID", "operation",
            "Revision must preserve no-go zone identities in schema version 1.", 4, operation_id,
        )
    profile = _profile_document(payload, int(payload["new_revision"]))
    profile_json = canonical_json(profile, sort_keys=False)
    connection.execute(
        "UPDATE field_profiles SET display_name = ?, enabled = ?, profile_revision = ?, local_frame_id = ?, "
        "profile_json = ?, profile_sha256 = ? WHERE field_id = ?",
        (
            payload["display_name"], int(payload["enabled"]), payload["new_revision"],
            payload["local_frame_id"], profile_json, sha256_text(profile_json), payload["field_id"],
        ),
    )
    for item in references:
        connection.execute(
            "UPDATE field_references SET reference_type = ?, label = ?, location_reference = ?, enabled = ? "
            "WHERE reference_id = ? AND field_id = ?",
            (
                item["reference_type"], item["label"], item["location_reference"], int(item["enabled"]),
                item["reference_id"], payload["field_id"],
            ),
        )
    for item in zones:
        boundary_json = canonical_json(item["boundary"], sort_keys=False)
        connection.execute(
            "UPDATE field_no_go_zones SET label = ?, reason_code = ?, boundary_json = ?, "
            "boundary_sha256 = ?, enabled = ? WHERE zone_id = ? AND field_id = ?",
            (
                item["label"], item["reason_code"], boundary_json, sha256_text(boundary_json),
                int(item["enabled"]), item["zone_id"], payload["field_id"],
            ),
        )
    return OperationDelta(0, 1, 0, 0, False)


def _set_active_field(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    payload = operation["payload"]
    operation_id = str(operation["operation_id"])
    row = connection.execute(
        "SELECT enabled FROM field_profiles WHERE field_id = ?", (payload["target_field_id"],)
    ).fetchone()
    if row is None:
        raise FieldFailure(
            "FIELD_NOT_FOUND", "operation", "Target field does not exist.", 4, operation_id,
        )
    if int(row[0]) != 1:
        raise FieldFailure(
            "FIELD_DISABLED", "operation", "Target field is disabled.", 4, operation_id,
        )
    if not _required_references_present(connection, payload["target_field_id"]):
        raise FieldFailure(
            "FIELD_REFERENCE_REQUIRED_MISSING", "operation",
            "Target field does not have all required enabled references.", 4, operation_id,
        )
    _safety_gate(payload, operation_id)
    active = connection.execute(
        "SELECT active_field_id, selection_revision FROM field_active_state WHERE state_key = 'ACTIVE_FIELD'"
    ).fetchone()
    if active is not None and active[0] == payload["target_field_id"]:
        return OperationDelta()
    if active is None:
        connection.execute(
            "INSERT INTO field_active_state(state_key, active_field_id, selection_revision, last_operation_id) "
            "VALUES ('ACTIVE_FIELD', ?, 1, ?)",
            (payload["target_field_id"], operation_id),
        )
    else:
        connection.execute(
            "UPDATE field_active_state SET active_field_id = ?, selection_revision = selection_revision + 1, "
            "last_operation_id = ? WHERE state_key = 'ACTIVE_FIELD'",
            (payload["target_field_id"], operation_id),
        )
    return OperationDelta(active_changed=True)


def _process_operation(connection: sqlite3.Connection, operation: dict[str, object]) -> OperationDelta:
    operation_type = str(operation["operation_type"])
    if operation_type == "REGISTER_FIELD":
        return _register_field(connection, operation)
    if operation_type == "REVISE_FIELD":
        return _revise_field(connection, operation)
    if operation_type == "SET_ACTIVE_FIELD":
        return _set_active_field(connection, operation)
    if integrity_check(connection) != "OK":
        raise FieldFailure(
            "FIELD_INTEGRITY_CHECK_FAILED", "integrity", "Integrity verification failed.", 5,
            str(operation["operation_id"]),
        )
    return OperationDelta()


def _diagnostic(failure: FieldFailure) -> dict[str, object]:
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
) -> FieldReport:
    diagnostics = sorted(
        diagnostics,
        key=lambda item: (
            str(item["component"]), str(item["code"]), str(item["operation_id"]), str(item["message"]),
        ),
    )
    counts = {name: len(state[name]) for name, _columns, _key in TABLE_DEFINITIONS}
    profiles = state["field_profiles"]
    zones = state["field_no_go_zones"]
    active_rows = state["field_active_state"]
    active = active_rows[0] if active_rows else None
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
        "fields": {
            "created_count": delta.fields_created if committed else 0,
            "revised_count": delta.fields_revised if committed else 0,
            "enabled_count": sum(int(row["enabled"]) == 1 for row in profiles),
            "disabled_count": sum(int(row["enabled"]) == 0 for row in profiles),
            "total_count": counts["field_profiles"],
        },
        "references": {
            "created_count": delta.references_created if committed else 0,
            "total_count": counts["field_references"],
        },
        "no_go_zones": {
            "created_count": delta.zones_created if committed else 0,
            "total_count": counts["field_no_go_zones"],
            "enabled_count": sum(int(row["enabled"]) == 1 for row in zones),
        },
        "active_field": {
            "active_field_id": "" if active is None else active["active_field_id"],
            "selection_revision": 0 if active is None else active["selection_revision"],
            "changed": delta.active_changed if committed else False,
            "automatic_selection_performed": False,
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
            "field_navigation_performed": False,
            "automatic_field_selection_performed": False,
            "actual_water_control_performed": False,
            "repository_modified": False,
            "physical_estop_independent": True,
        },
        "summary": {
            "table_count": 6,
            "row_count_total": sum(counts.values()),
            "diagnostic_count": len(diagnostics),
            "next_phase_eligible": exit_code == 0,
        },
        "diagnostics": diagnostics,
        "canonical_state_sha256": canonical_state_sha256(state),
        "exit_code": exit_code,
    }
    return FieldReport(document, exit_code)


def run_field_profile_session(
    arguments: FieldArguments,
    *,
    fail_after_operation_index: int | None = None,
    write_reports: bool = False,
    operation_processor: Callable[[sqlite3.Connection, dict[str, object]], OperationDelta] = _process_operation,
) -> FieldReport:
    validate_arguments(arguments)
    try:
        session = validate_session(load_strict_json(arguments.session))
    except FieldFailure as failure:
        report = _build_report(
            "SESSION-ST005-INVALID", False, False, None, False, False, False, False,
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
    schema_path = arguments.repository_root / "software" / "station_control" / "storage" / "field_profiles_schema_v1.sql"

    try:
        connection, configuration = open_database(arguments.database)
        initialized = initialize_or_verify_schema(connection, schema_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            begun = True
        except sqlite3.Error as exc:
            raise FieldFailure(
                "FIELD_TRANSACTION_BEGIN_FAILED", "transaction",
                "Atomic field profile transaction could not begin.", 4,
            ) from exc
        for index, operation in enumerate(operations):
            operation_id = str(operation["operation_id"])
            request_hash = operation_request_sha256(operation)
            existing = connection.execute(
                "SELECT request_sha256 FROM field_processed_operations WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
            if existing is not None:
                if existing[0] != request_hash:
                    conflict_count = 1
                    raise FieldFailure(
                        "FIELD_IDEMPOTENCY_CONFLICT", "idempotency",
                        "Operation ID was previously committed with different content.", 4, operation_id,
                    )
                duplicate_count += 1
                processed_count += 1
            else:
                _insert_processed_operation(connection, operation, request_hash)
                item = operation_processor(connection, operation)
                delta = OperationDelta(
                    delta.fields_created + item.fields_created,
                    delta.fields_revised + item.fields_revised,
                    delta.references_created + item.references_created,
                    delta.zones_created + item.zones_created,
                    delta.active_changed or item.active_changed,
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
        diagnostics.append(_diagnostic(FieldFailure(
            "FIELD_TRANSACTION_ROLLED_BACK", "transaction",
            "Atomic field profile session rolled back after simulated interruption.", 4,
        )))
    except FieldFailure as failure:
        exit_code = failure.exit_code
        rejected_count = 1
        if failure.code == "FIELD_IDEMPOTENCY_CONFLICT":
            conflict_count = 1
        if connection is not None and begun and connection.in_transaction:
            connection.execute("ROLLBACK")
            rolled_back = True
            diagnostics.append(_diagnostic(FieldFailure(
                "FIELD_TRANSACTION_ROLLED_BACK", "transaction",
                "Atomic field profile session rolled back without partial commit.", 4,
            )))
        diagnostics.append(_diagnostic(failure))
    except sqlite3.Error:
        exit_code = 4
        rejected_count = 1
        if connection is not None and begun and connection.in_transaction:
            connection.execute("ROLLBACK")
            rolled_back = True
        diagnostics.append(_diagnostic(FieldFailure(
            "FIELD_TRANSACTION_ROLLED_BACK", "transaction",
            "Atomic field profile session rolled back after a SQLite failure.", 4,
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
    except FieldFailure as failure:
        if exit_code == 0:
            exit_code = failure.exit_code
            diagnostics.append(_diagnostic(failure))
    except sqlite3.Error:
        if exit_code == 0:
            exit_code = 5
            diagnostics.append(_diagnostic(FieldFailure(
                "FIELD_REOPEN_FAILED", "database", "Database could not be reopened.", 5,
            )))

    report = _build_report(
        session_id, database_created, reopened, configuration, begun, committed, rolled_back,
        initialized, len(operations), processed_count, applied_count, duplicate_count,
        rejected_count, delta, conflict_count, integrity_result, state, diagnostics, exit_code,
    )
    return _write_requested_reports(report, arguments) if write_reports else report


def render_json_report(report: FieldReport) -> str:
    return json.dumps(report.document, ensure_ascii=True, indent=2, separators=(",", ": ")) + "\n"


def _text_value(value: object) -> str:
    return str(value).lower() if type(value) is bool else str(value)


def render_text_report(report: FieldReport) -> str:
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
        ("busy_timeout_ms", document["database"]["busy_timeout_ms"]),
        ("transaction_committed", document["transaction"]["committed"]),
        ("transaction_rolled_back", document["transaction"]["rolled_back"]),
        ("schema_version", document["schema"]["schema_version"]),
        ("operation_input_count", document["operations"]["input_count"]),
        ("operation_applied_count", document["operations"]["applied_count"]),
        ("duplicate_noop_count", document["operations"]["duplicate_noop_count"]),
        ("field_total_count", document["fields"]["total_count"]),
        ("reference_total_count", document["references"]["total_count"]),
        ("no_go_zone_total_count", document["no_go_zones"]["total_count"]),
        ("active_field_id", document["active_field"]["active_field_id"]),
        ("selection_revision", document["active_field"]["selection_revision"]),
        ("automatic_selection_performed", document["active_field"]["automatic_selection_performed"]),
        ("integrity_result", document["integrity"]["result"]),
        ("canonical_state_sha256", document["canonical_state_sha256"]),
        ("offline_only", document["safety"]["offline_only"]),
        ("network_access_performed", document["safety"]["network_access_performed"]),
        ("gpio_access_performed", document["safety"]["gpio_access_performed"]),
        ("serial_access_performed", document["safety"]["serial_access_performed"]),
        ("hardware_output_performed", document["safety"]["hardware_output_performed"]),
        ("actual_water_control_performed", document["safety"]["actual_water_control_performed"]),
        ("diagnostic_count", document["summary"]["diagnostic_count"]),
        ("exit_code", document["exit_code"]),
    )
    return "\n".join(f"{key}={_text_value(value)}" for key, value in values) + "\n"


def write_report(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_requested_reports(report: FieldReport, arguments: FieldArguments) -> FieldReport:
    try:
        write_report(arguments.json_report, render_json_report(report))
        write_report(arguments.text_report, render_text_report(report))
        return report
    except OSError:
        failure = FieldFailure(
            "FIELD_REPORT_WRITE_FAILED", "report", "Report output failed.", 7,
        )
        document = dict(report.document)
        diagnostics = list(document["diagnostics"])
        diagnostics.append(_diagnostic(failure))
        diagnostics.sort(key=lambda item: (
            str(item["component"]), str(item["code"]), str(item["operation_id"]), str(item["message"]),
        ))
        document["result"] = "FAIL"
        document["diagnostics"] = diagnostics
        document["summary"] = dict(document["summary"])
        document["summary"]["diagnostic_count"] = len(diagnostics)
        document["summary"]["next_phase_eligible"] = False
        document["exit_code"] = 7
        return FieldReport(document, 7)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_arguments(argv)
        report = run_field_profile_session(arguments, write_reports=True)
        print(render_text_report(report), end="")
        return report.exit_code
    except FieldFailure as failure:
        print(f"ST-005 field profiles rejected: {failure.message}", file=sys.stderr)
        return failure.exit_code
    except ValueError:
        print("ST-005 field profiles rejected invalid CLI arguments.", file=sys.stderr)
        return 2
    except Exception:
        print(
            "FIELD_INTERNAL_ERROR: ST-005 field profiles failed because of an unexpected internal exception.",
            file=sys.stderr,
        )
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
