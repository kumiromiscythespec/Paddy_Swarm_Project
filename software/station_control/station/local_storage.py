"""Transactional, offline-only SQLite local storage for phase ST-004."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
import sys
from typing import Callable, Sequence


REPORT_VERSION = 1
PHASE = "ST-004"
SESSION_VERSION = 1
SCHEMA_VERSION = "1"
OPERATION_TYPES = (
    "STORE_EVENT",
    "RECORD_UPLOAD_ATTEMPT",
    "ACKNOWLEDGE_UPLOAD",
    "VERIFY_INTEGRITY",
)
SOURCE_TYPES = ("STATION", "ROVER", "UNIT", "MISSION", "SYSTEM")
OUTBOX_STATUSES = ("PENDING", "ACKNOWLEDGED", "DEAD_LETTER")
ATTEMPT_ERROR_CODES = ("OFFLINE", "CONNECTION_UNAVAILABLE", "REMOTE_NOT_CONFIGURED")
IDENTIFIER_PATTERN = re.compile(r"^[A-Z][A-Z0-9-]{2,63}$")
EVENT_TYPE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
SESSION_ID_PATTERN = re.compile(r"^SESSION-ST004-[A-Z0-9-]{1,40}$")
TABLE_DEFINITIONS = (
    ("schema_metadata", ("metadata_key", "metadata_value"), "metadata_key"),
    (
        "processed_operations",
        ("operation_id", "request_sha256", "operation_type", "logical_tick", "result_code"),
        "operation_id",
    ),
    (
        "event_log",
        (
            "event_id", "operation_id", "event_type", "source_type", "source_id",
            "logical_tick", "payload_json", "payload_sha256",
        ),
        "event_id",
    ),
    (
        "upload_outbox",
        (
            "upload_record_id", "event_id", "idempotency_key", "payload_json",
            "payload_sha256", "status", "attempt_count", "last_error_code",
            "acknowledgement_id",
        ),
        "upload_record_id",
    ),
)


class StorageFailure(RuntimeError):
    """Expected fail-closed storage error."""

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
    """Test-only interruption raised after an operation and before commit."""


@dataclass(frozen=True)
class StorageArguments:
    repository_root: Path
    database: Path
    session: Path
    json_report: Path
    text_report: Path


@dataclass(frozen=True)
class StorageReport:
    document: dict[str, object]
    exit_code: int


@dataclass(frozen=True)
class RuntimeConfiguration:
    journal_mode: str
    synchronous: int
    foreign_keys: int
    busy_timeout_ms: int


class DeterministicArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def parse_arguments(argv: Sequence[str] | None = None) -> StorageArguments:
    parser = DeterministicArgumentParser(
        description="Run the transactional offline ST-004 local storage session."
    )
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--json-report", required=True, type=Path)
    parser.add_argument("--text-report", required=True, type=Path)
    values = parser.parse_args(argv)
    return StorageArguments(
        repository_root=values.repository_root,
        database=values.database,
        session=values.session,
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


def validate_arguments(arguments: StorageArguments) -> None:
    repository = arguments.repository_root
    if not repository.is_dir():
        raise StorageFailure(
            "STORAGE_REPOSITORY_ROOT_INVALID", "arguments",
            "Repository root must be an existing directory.", 2,
        )
    schema_path = repository / "software" / "station_control" / "storage" / "schema_v1.sql"
    if not schema_path.is_file():
        raise StorageFailure(
            "STORAGE_REPOSITORY_ROOT_INVALID", "arguments",
            "Repository root does not contain the ST-004 SQL schema.", 2,
        )
    if not arguments.session.is_file():
        raise StorageFailure(
            "STORAGE_INVALID_ARGUMENT", "arguments",
            "Session must be an existing regular file.", 2,
        )
    if is_path_contained(arguments.database, repository):
        raise StorageFailure(
            "STORAGE_DATABASE_PATH_INSIDE_REPOSITORY", "database",
            "Database path must be outside the repository.", 2,
        )
    if not arguments.database.parent.is_dir():
        raise StorageFailure(
            "STORAGE_DATABASE_PARENT_INVALID", "database",
            "Database parent must be an existing directory.", 2,
        )
    for report_path in (arguments.json_report, arguments.text_report):
        if is_path_contained(report_path, repository):
            raise StorageFailure(
                "STORAGE_REPORT_PATH_INSIDE_REPOSITORY", "report",
                "Report path must be outside the repository.", 2,
            )
        if not report_path.parent.is_dir():
            raise StorageFailure(
                "STORAGE_REPORT_PARENT_INVALID", "report",
                "Report parent must be an existing directory.", 2,
            )
    resolved = (
        arguments.database.resolve(strict=False),
        arguments.session.resolve(strict=False),
        arguments.json_report.resolve(strict=False),
        arguments.text_report.resolve(strict=False),
    )
    if len(set(resolved)) != len(resolved):
        raise StorageFailure(
            "STORAGE_INVALID_ARGUMENT", "arguments",
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
        raise StorageFailure(
            "STORAGE_SESSION_INVALID", "session",
            "Session is not readable strict JSON.", 3,
        ) from exc


def _exact_object(value: object, keys: tuple[str, ...], context: str) -> dict[str, object]:
    if type(value) is not dict or tuple(value) != keys:
        raise StorageFailure(
            "STORAGE_SESSION_INVALID", "session",
            f"{context} properties or property order are invalid.", 3,
        )
    return value


def _identifier(value: object, context: str, allow_empty: bool = False) -> str:
    if allow_empty and value == "":
        return ""
    if type(value) is not str or IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise StorageFailure(
            "STORAGE_SESSION_INVALID", "session",
            f"{context} must be a demo logical identifier.", 3,
        )
    return value


def _logical_tick(value: object, context: str) -> int:
    if type(value) is not int or not 0 <= value <= 2147483647:
        raise StorageFailure(
            "STORAGE_SESSION_INVALID", "session",
            f"{context} must be a non-negative integer.", 3,
        )
    return value


def _validate_json_value(value: object, context: str) -> None:
    if value is None:
        raise StorageFailure(
            "STORAGE_SESSION_INVALID", "session", f"{context} cannot contain null.", 3,
        )
    if type(value) is float and not math.isfinite(value):
        raise StorageFailure(
            "STORAGE_SESSION_INVALID", "session", f"{context} must be finite.", 3,
        )
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise StorageFailure(
                    "STORAGE_SESSION_INVALID", "session", f"{context} keys must be strings.", 3,
                )
            _validate_json_value(child, context)
    elif type(value) is list:
        for child in value:
            _validate_json_value(child, context)
    elif type(value) not in (str, int, float, bool):
        raise StorageFailure(
            "STORAGE_SESSION_INVALID", "session", f"{context} contains an invalid JSON value.", 3,
        )


def validate_session(value: object) -> dict[str, object]:
    session = _exact_object(value, ("session_version", "session_id", "operations"), "session")
    if type(session["session_version"]) is not int or session["session_version"] != SESSION_VERSION:
        raise StorageFailure(
            "STORAGE_SESSION_INVALID", "session", "Session version must be 1.", 3,
        )
    session_id = session["session_id"]
    if type(session_id) is not str or SESSION_ID_PATTERN.fullmatch(session_id) is None:
        raise StorageFailure(
            "STORAGE_SESSION_INVALID", "session", "Session ID must be an ST-004 demo ID.", 3,
        )
    operations = session["operations"]
    if type(operations) is not list or not 1 <= len(operations) <= 1000:
        raise StorageFailure(
            "STORAGE_SESSION_INVALID", "session", "Operations must be a bounded non-empty array.", 3,
        )
    previous_tick = -1
    for index, raw_operation in enumerate(operations):
        operation = _exact_object(
            raw_operation, ("operation_id", "logical_tick", "operation_type", "payload"),
            f"operations[{index}]",
        )
        _identifier(operation["operation_id"], f"operations[{index}].operation_id")
        tick = _logical_tick(operation["logical_tick"], f"operations[{index}].logical_tick")
        if tick < previous_tick:
            raise StorageFailure(
                "STORAGE_SESSION_TICK_REVERSED", "session",
                "Operation logical ticks must be nondecreasing.", 3,
                str(operation["operation_id"]),
            )
        previous_tick = tick
        operation_type = operation["operation_type"]
        if operation_type not in OPERATION_TYPES:
            raise StorageFailure(
                "STORAGE_OPERATION_UNKNOWN", "session", "Operation type is unknown.", 3,
                str(operation["operation_id"]),
            )
        _validate_operation_payload(operation_type, operation["payload"], index)
    return session


def _validate_operation_payload(operation_type: object, value: object, index: int) -> None:
    context = f"operations[{index}].payload"
    if operation_type == "STORE_EVENT":
        payload = _exact_object(
            value,
            (
                "event_id", "event_type", "source_type", "source_id", "event_payload",
                "enqueue_upload", "upload_record_id", "idempotency_key",
            ),
            context,
        )
        _identifier(payload["event_id"], f"{context}.event_id")
        if type(payload["event_type"]) is not str or EVENT_TYPE_PATTERN.fullmatch(payload["event_type"]) is None:
            raise StorageFailure(
                "STORAGE_SESSION_INVALID", "session", "Event type is invalid.", 3,
            )
        if payload["source_type"] not in SOURCE_TYPES:
            raise StorageFailure(
                "STORAGE_SESSION_INVALID", "session", "Source type is invalid.", 3,
            )
        _identifier(payload["source_id"], f"{context}.source_id")
        if type(payload["event_payload"]) is not dict:
            raise StorageFailure(
                "STORAGE_SESSION_INVALID", "session", "Event payload must be an object.", 3,
            )
        _validate_json_value(payload["event_payload"], f"{context}.event_payload")
        if type(payload["enqueue_upload"]) is not bool:
            raise StorageFailure(
                "STORAGE_SESSION_INVALID", "session", "enqueue_upload must be a boolean.", 3,
            )
        if payload["enqueue_upload"]:
            _identifier(payload["upload_record_id"], f"{context}.upload_record_id")
            _identifier(payload["idempotency_key"], f"{context}.idempotency_key")
        elif payload["upload_record_id"] != "" or payload["idempotency_key"] != "":
            raise StorageFailure(
                "STORAGE_SESSION_INVALID", "session",
                "Disabled upload enqueue requires empty upload identifiers.", 3,
            )
    elif operation_type == "RECORD_UPLOAD_ATTEMPT":
        payload = _exact_object(value, ("upload_record_id", "error_code"), context)
        _identifier(payload["upload_record_id"], f"{context}.upload_record_id")
        if payload["error_code"] not in ATTEMPT_ERROR_CODES:
            raise StorageFailure(
                "STORAGE_SESSION_INVALID", "session", "Upload attempt error code is invalid.", 3,
            )
    elif operation_type == "ACKNOWLEDGE_UPLOAD":
        payload = _exact_object(value, ("upload_record_id", "acknowledgement_id"), context)
        _identifier(payload["upload_record_id"], f"{context}.upload_record_id")
        _identifier(payload["acknowledgement_id"], f"{context}.acknowledgement_id")
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
        synchronous = int(connection.execute("PRAGMA synchronous").fetchone()[0])
        foreign_keys = int(connection.execute("PRAGMA foreign_keys").fetchone()[0])
        busy_timeout = int(connection.execute("PRAGMA busy_timeout").fetchone()[0])
        configuration = RuntimeConfiguration(
            journal_mode=journal_mode,
            synchronous=synchronous,
            foreign_keys=foreign_keys,
            busy_timeout_ms=busy_timeout,
        )
        if configuration != RuntimeConfiguration("wal", 2, 1, 5000):
            raise sqlite3.OperationalError("Required SQLite runtime configuration was not applied.")
        return connection, configuration
    except BaseException:
        connection.close()
        raise


def initialize_or_verify_schema(connection: sqlite3.Connection, schema_path: Path) -> bool:
    try:
        sql = schema_path.read_text(encoding="utf-8")
        connection.executescript(sql)
        rows = dict(connection.execute(
            "SELECT metadata_key, metadata_value FROM schema_metadata ORDER BY metadata_key"
        ).fetchall())
        if not rows:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.executemany(
                    "INSERT INTO schema_metadata(metadata_key, metadata_value) VALUES (?, ?)",
                    (("schema_version", SCHEMA_VERSION), ("application_phase", PHASE)),
                )
                connection.execute("COMMIT")
            except BaseException:
                connection.execute("ROLLBACK")
                raise
            return True
        if rows != {"application_phase": PHASE, "schema_version": SCHEMA_VERSION}:
            raise StorageFailure(
                "STORAGE_SCHEMA_VERSION_UNSUPPORTED", "schema",
                "Database schema metadata is unsupported.", 3,
            )
        return False
    except StorageFailure:
        raise
    except (OSError, UnicodeError, sqlite3.Error) as exc:
        raise StorageFailure(
            "STORAGE_SCHEMA_INITIALIZATION_FAILED", "schema",
            "Schema initialization or verification failed.", 3,
        ) from exc


def verify_schema_version(connection: sqlite3.Connection) -> None:
    try:
        rows = dict(connection.execute(
            "SELECT metadata_key, metadata_value FROM schema_metadata ORDER BY metadata_key"
        ).fetchall())
    except sqlite3.Error as exc:
        raise StorageFailure(
            "STORAGE_SCHEMA_VERSION_UNSUPPORTED", "schema",
            "Schema metadata cannot be read after reopen.", 3,
        ) from exc
    if rows != {"application_phase": PHASE, "schema_version": SCHEMA_VERSION}:
        raise StorageFailure(
            "STORAGE_SCHEMA_VERSION_UNSUPPORTED", "schema",
            "Schema metadata is unsupported after reopen.", 3,
        )


def integrity_check(connection: sqlite3.Connection) -> str:
    try:
        rows = connection.execute("PRAGMA integrity_check").fetchall()
    except sqlite3.Error as exc:
        raise StorageFailure(
            "STORAGE_INTEGRITY_CHECK_FAILED", "integrity",
            "SQLite integrity check could not be executed.", 5,
        ) from exc
    if rows != [("ok",)]:
        raise StorageFailure(
            "STORAGE_INTEGRITY_CHECK_FAILED", "integrity",
            "SQLite integrity check did not return OK.", 5,
        )
    return "OK"


def canonical_database_state(connection: sqlite3.Connection) -> dict[str, object]:
    state: dict[str, object] = {}
    for table_name, columns, primary_key in TABLE_DEFINITIONS:
        quoted_columns = ", ".join(columns)
        query = f"SELECT {quoted_columns} FROM {table_name} ORDER BY {primary_key}"
        rows = connection.execute(query).fetchall()
        state[table_name] = [dict(zip(columns, row, strict=True)) for row in rows]
    return state


def empty_canonical_state() -> dict[str, object]:
    return {table_name: [] for table_name, _columns, _key in TABLE_DEFINITIONS}


def canonical_state_sha256(state: dict[str, object]) -> str:
    return sha256_text(canonical_json(state, sort_keys=False))


def _insert_processed_operation(
    connection: sqlite3.Connection, operation: dict[str, object], request_hash: str
) -> None:
    connection.execute(
        "INSERT INTO processed_operations(operation_id, request_sha256, operation_type, logical_tick, result_code) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            operation["operation_id"], request_hash, operation["operation_type"],
            operation["logical_tick"], "APPLIED",
        ),
    )


def _store_event(connection: sqlite3.Connection, operation: dict[str, object]) -> tuple[int, int]:
    payload = operation["payload"]
    event_payload_json = canonical_json(payload["event_payload"])
    event_payload_hash = sha256_text(event_payload_json)
    try:
        connection.execute(
            "INSERT INTO event_log(event_id, operation_id, event_type, source_type, source_id, "
            "logical_tick, payload_json, payload_sha256) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                payload["event_id"], operation["operation_id"], payload["event_type"],
                payload["source_type"], payload["source_id"], operation["logical_tick"],
                event_payload_json, event_payload_hash,
            ),
        )
        created = 0
        if payload["enqueue_upload"]:
            connection.execute(
                "INSERT INTO upload_outbox(upload_record_id, event_id, idempotency_key, payload_json, "
                "payload_sha256, status, attempt_count, last_error_code, acknowledgement_id) "
                "VALUES (?, ?, ?, ?, ?, 'PENDING', 0, '', '')",
                (
                    payload["upload_record_id"], payload["event_id"], payload["idempotency_key"],
                    event_payload_json, event_payload_hash,
                ),
            )
            created = 1
        return 1, created
    except sqlite3.IntegrityError as exc:
        raise StorageFailure(
            "STORAGE_EVENT_CONFLICT", "operation",
            "Event or upload identity conflicts with committed state.", 4,
            str(operation["operation_id"]),
        ) from exc


def _outbox_row(connection: sqlite3.Connection, upload_record_id: object) -> tuple[object, ...]:
    row = connection.execute(
        "SELECT status, attempt_count, last_error_code, acknowledgement_id "
        "FROM upload_outbox WHERE upload_record_id = ?",
        (upload_record_id,),
    ).fetchone()
    if row is None:
        raise StorageFailure(
            "STORAGE_OUTBOX_RECORD_NOT_FOUND", "operation",
            "Upload outbox record does not exist.", 4,
        )
    return row


def _record_upload_attempt(connection: sqlite3.Connection, operation: dict[str, object]) -> None:
    payload = operation["payload"]
    status, _attempt_count, _last_error, _acknowledgement = _outbox_row(
        connection, payload["upload_record_id"]
    )
    if status != "PENDING":
        raise StorageFailure(
            "STORAGE_OUTBOX_STATE_CONFLICT", "operation",
            "Upload attempt requires a PENDING record.", 4,
            str(operation["operation_id"]),
        )
    connection.execute(
        "UPDATE upload_outbox SET attempt_count = attempt_count + 1, last_error_code = ? "
        "WHERE upload_record_id = ?",
        (payload["error_code"], payload["upload_record_id"]),
    )


def _acknowledge_upload(connection: sqlite3.Connection, operation: dict[str, object]) -> None:
    payload = operation["payload"]
    status, _attempt_count, _last_error, _acknowledgement = _outbox_row(
        connection, payload["upload_record_id"]
    )
    if status != "PENDING":
        raise StorageFailure(
            "STORAGE_OUTBOX_STATE_CONFLICT", "operation",
            "Acknowledgement simulation requires a PENDING record.", 4,
            str(operation["operation_id"]),
        )
    connection.execute(
        "UPDATE upload_outbox SET status = 'ACKNOWLEDGED', acknowledgement_id = ?, "
        "last_error_code = '' WHERE upload_record_id = ?",
        (payload["acknowledgement_id"], payload["upload_record_id"]),
    )


def _process_operation(connection: sqlite3.Connection, operation: dict[str, object]) -> tuple[int, int]:
    operation_type = str(operation["operation_type"])
    if operation_type == "STORE_EVENT":
        return _store_event(connection, operation)
    if operation_type == "RECORD_UPLOAD_ATTEMPT":
        _record_upload_attempt(connection, operation)
        return 0, 0
    if operation_type == "ACKNOWLEDGE_UPLOAD":
        _acknowledge_upload(connection, operation)
        return 0, 0
    if integrity_check(connection) != "OK":
        raise StorageFailure(
            "STORAGE_INTEGRITY_CHECK_FAILED", "integrity", "Integrity verification failed.", 5,
            str(operation["operation_id"]),
        )
    return 0, 0


def _diagnostic(failure: StorageFailure) -> dict[str, object]:
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
    transaction_begun: bool,
    committed: bool,
    rolled_back: bool,
    initialized: bool,
    input_count: int,
    processed_count: int,
    applied_count: int,
    duplicate_count: int,
    rejected_count: int,
    stored_count: int,
    outbox_created_count: int,
    conflict_count: int,
    integrity_result: str,
    state: dict[str, object],
    diagnostics: list[dict[str, object]],
    exit_code: int,
) -> StorageReport:
    ordered_diagnostics = sorted(
        diagnostics,
        key=lambda item: (
            str(item["component"]), str(item["code"]), str(item["operation_id"]),
            str(item["message"]),
        ),
    )
    row_counts = {name: len(state[name]) for name, _columns, _key in TABLE_DEFINITIONS}
    outbox_rows = state["upload_outbox"]
    pending = sum(row["status"] == "PENDING" for row in outbox_rows)
    acknowledged = sum(row["status"] == "ACKNOWLEDGED" for row in outbox_rows)
    dead_letter = sum(row["status"] == "DEAD_LETTER" for row in outbox_rows)
    attempts = sum(int(row["attempt_count"]) for row in outbox_rows)
    config = configuration or RuntimeConfiguration("", 0, 0, 0)
    result = "PASS" if exit_code == 0 else "FAIL"
    document: dict[str, object] = {
        "report_version": REPORT_VERSION,
        "phase": PHASE,
        "session_id": session_id,
        "result": result,
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
            "begun": transaction_begun,
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
        "events": {
            "stored_count": stored_count if committed else 0,
            "total_count": row_counts["event_log"],
        },
        "outbox": {
            "created_count": outbox_created_count if committed else 0,
            "pending_count": pending,
            "acknowledged_count": acknowledged,
            "dead_letter_count": dead_letter,
            "attempt_count_total": attempts,
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
            "actual_upload_performed": False,
            "repository_modified": False,
            "physical_estop_independent": True,
        },
        "summary": {
            "table_count": 4,
            "row_count_total": sum(row_counts.values()),
            "diagnostic_count": len(ordered_diagnostics),
            "next_phase_eligible": exit_code == 0,
        },
        "diagnostics": ordered_diagnostics,
        "canonical_state_sha256": canonical_state_sha256(state),
        "exit_code": exit_code,
    }
    return StorageReport(document, exit_code)


def run_storage_session(
    arguments: StorageArguments,
    *,
    fail_after_operation_index: int | None = None,
    write_reports: bool = False,
    operation_processor: Callable[[sqlite3.Connection, dict[str, object]], tuple[int, int]] = _process_operation,
) -> StorageReport:
    validate_arguments(arguments)
    try:
        session = validate_session(load_strict_json(arguments.session))
    except StorageFailure as failure:
        report = _build_report(
            "SESSION-ST004-INVALID", False, False, None, False, False, False, False,
            0, 0, 0, 0, 1, 0, 0, 0, "NOT_PERFORMED", empty_canonical_state(),
            [_diagnostic(failure)], failure.exit_code,
        )
        return _write_requested_reports(report, arguments) if write_reports else report

    session_id = str(session["session_id"])
    operations = session["operations"]
    input_count = len(operations)
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
    stored_count = 0
    outbox_created_count = 0
    conflict_count = 0
    integrity_result = "NOT_PERFORMED"
    exit_code = 0
    diagnostics: list[dict[str, object]] = []
    state = empty_canonical_state()
    connection: sqlite3.Connection | None = None
    schema_path = arguments.repository_root / "software" / "station_control" / "storage" / "schema_v1.sql"

    try:
        connection, configuration = open_database(arguments.database)
        initialized = initialize_or_verify_schema(connection, schema_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            begun = True
        except sqlite3.Error as exc:
            raise StorageFailure(
                "STORAGE_TRANSACTION_BEGIN_FAILED", "transaction",
                "Atomic session transaction could not begin.", 4,
            ) from exc
        for index, operation in enumerate(operations):
            operation_id = str(operation["operation_id"])
            request_hash = operation_request_sha256(operation)
            existing = connection.execute(
                "SELECT request_sha256 FROM processed_operations WHERE operation_id = ?",
                (operation_id,),
            ).fetchone()
            if existing is not None:
                if existing[0] != request_hash:
                    conflict_count += 1
                    raise StorageFailure(
                        "STORAGE_IDEMPOTENCY_CONFLICT", "idempotency",
                        "Operation ID was previously committed with different content.", 4,
                        operation_id,
                    )
                duplicate_count += 1
                processed_count += 1
            else:
                _insert_processed_operation(connection, operation, request_hash)
                event_delta, outbox_delta = operation_processor(connection, operation)
                stored_count += event_delta
                outbox_created_count += outbox_delta
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
        diagnostics.extend((
            _diagnostic(StorageFailure(
                "STORAGE_TRANSACTION_ROLLED_BACK", "transaction",
                "Atomic session was rolled back after a simulated interruption.", 4,
            )),
        ))
    except StorageFailure as failure:
        exit_code = failure.exit_code
        rejected_count = 1
        if failure.code == "STORAGE_IDEMPOTENCY_CONFLICT":
            conflict_count = max(conflict_count, 1)
        if connection is not None and begun and connection.in_transaction:
            connection.execute("ROLLBACK")
            rolled_back = True
            diagnostics.append(_diagnostic(StorageFailure(
                "STORAGE_TRANSACTION_ROLLED_BACK", "transaction",
                "Atomic session was rolled back without partial commit.", 4,
            )))
        diagnostics.append(_diagnostic(failure))
    except sqlite3.Error:
        exit_code = 4
        rejected_count = 1
        if connection is not None and begun and connection.in_transaction:
            connection.execute("ROLLBACK")
            rolled_back = True
        diagnostics.extend((
            _diagnostic(StorageFailure(
                "STORAGE_TRANSACTION_ROLLED_BACK", "transaction",
                "Atomic session was rolled back after a SQLite operation failure.", 4,
            )),
        ))
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
    except StorageFailure as failure:
        if exit_code == 0:
            exit_code = failure.exit_code
            diagnostics.append(_diagnostic(failure))
    except sqlite3.Error:
        if exit_code == 0:
            exit_code = 5
            diagnostics.append(_diagnostic(StorageFailure(
                "STORAGE_REOPEN_FAILED", "database",
                "Database could not be reopened and verified.", 5,
            )))

    report = _build_report(
        session_id, database_created, reopened, configuration, begun, committed, rolled_back,
        initialized, input_count, processed_count, applied_count, duplicate_count,
        rejected_count, stored_count, outbox_created_count, conflict_count, integrity_result,
        state, diagnostics, exit_code,
    )
    return _write_requested_reports(report, arguments) if write_reports else report


def render_json_report(report: StorageReport) -> str:
    return json.dumps(report.document, ensure_ascii=True, indent=2, separators=(",", ": ")) + "\n"


def _text_value(value: object) -> str:
    if type(value) is bool:
        return str(value).lower()
    return str(value)


def render_text_report(report: StorageReport) -> str:
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
        ("event_total_count", document["events"]["total_count"]),
        ("outbox_pending_count", document["outbox"]["pending_count"]),
        ("outbox_acknowledged_count", document["outbox"]["acknowledged_count"]),
        ("integrity_result", document["integrity"]["result"]),
        ("idempotency_conflict_count", document["idempotency"]["conflict_count"]),
        ("canonical_state_sha256", document["canonical_state_sha256"]),
        ("offline_only", document["safety"]["offline_only"]),
        ("network_access_performed", document["safety"]["network_access_performed"]),
        ("gpio_access_performed", document["safety"]["gpio_access_performed"]),
        ("hardware_output_performed", document["safety"]["hardware_output_performed"]),
        ("actual_upload_performed", document["safety"]["actual_upload_performed"]),
        ("diagnostic_count", document["summary"]["diagnostic_count"]),
        ("exit_code", document["exit_code"]),
    )
    return "\n".join(f"{key}={_text_value(value)}" for key, value in values) + "\n"


def write_report(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_requested_reports(report: StorageReport, arguments: StorageArguments) -> StorageReport:
    try:
        write_report(arguments.json_report, render_json_report(report))
        write_report(arguments.text_report, render_text_report(report))
        return report
    except OSError:
        failure = StorageFailure(
            "STORAGE_REPORT_WRITE_FAILED", "report", "Report output failed.", 7,
        )
        document = dict(report.document)
        diagnostics = list(document["diagnostics"])
        diagnostics.append(_diagnostic(failure))
        diagnostics.sort(key=lambda item: (
            str(item["component"]), str(item["code"]), str(item["operation_id"]),
            str(item["message"]),
        ))
        document["result"] = "FAIL"
        document["diagnostics"] = diagnostics
        document["summary"] = dict(document["summary"])
        document["summary"]["diagnostic_count"] = len(diagnostics)
        document["summary"]["next_phase_eligible"] = False
        document["exit_code"] = 7
        return StorageReport(document, 7)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_arguments(argv)
        report = run_storage_session(arguments, write_reports=True)
        print(render_text_report(report), end="")
        return report.exit_code
    except StorageFailure as failure:
        print(f"ST-004 storage rejected: {failure.message}", file=sys.stderr)
        return failure.exit_code
    except ValueError:
        print("ST-004 storage rejected invalid CLI arguments.", file=sys.stderr)
        return 2
    except Exception:
        print(
            "STORAGE_INTERNAL_ERROR: ST-004 storage failed because of an "
            "unexpected internal exception.",
            file=sys.stderr,
        )
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
