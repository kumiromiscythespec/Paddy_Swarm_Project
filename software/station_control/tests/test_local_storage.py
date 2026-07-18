"""Standard-library tests for ST-004 transactional local storage."""

from __future__ import annotations

import ast
from contextlib import redirect_stderr, redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock


STATION_CONTROL_ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_PATH = STATION_CONTROL_ROOT / "station" / "local_storage.py"
SQL_PATH = STATION_CONTROL_ROOT / "storage" / "schema_v1.sql"
SESSION_SCHEMA_PATH = STATION_CONTROL_ROOT / "schemas" / "local-storage-session.schema.json"
REPORT_SCHEMA_PATH = STATION_CONTROL_ROOT / "schemas" / "local-storage-report.schema.json"
EXAMPLE_PATH = STATION_CONTROL_ROOT / "config_examples" / "local-storage-session.example.json"

SPEC = importlib.util.spec_from_file_location("station_local_storage", IMPLEMENTATION_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load local storage module.")
STORAGE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = STORAGE
SPEC.loader.exec_module(STORAGE)


class LocalStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="st004-test-")
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.database_dir = self.root / "database"
        self.report_dir = self.root / "reports"
        self.session_dir = self.root / "sessions"
        for path in (self.repository, self.database_dir, self.report_dir, self.session_dir):
            path.mkdir()
        schema_copy = self.repository / "software" / "station_control" / "storage" / "schema_v1.sql"
        schema_copy.parent.mkdir(parents=True)
        shutil.copy2(SQL_PATH, schema_copy)
        self.example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        self.session_path = self.session_dir / "session.json"
        self.write_session(self.example)
        self.arguments = self.make_arguments("station.db", "report")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_arguments(self, database_name: str, report_stem: str) -> object:
        return STORAGE.StorageArguments(
            repository_root=self.repository,
            database=self.database_dir / database_name,
            session=self.session_path,
            json_report=self.report_dir / f"{report_stem}.json",
            text_report=self.report_dir / f"{report_stem}.txt",
        )

    def write_session(self, document: object, path: Path | None = None) -> Path:
        target = path or self.session_path
        target.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        return target

    def run(self, result=None, arguments=None, **kwargs):
        if result is not None and not isinstance(result, STORAGE.StorageArguments):
            return super().run(result)
        selected = result if isinstance(result, STORAGE.StorageArguments) else arguments
        return STORAGE.run_storage_session(selected or self.arguments, **kwargs)

    def query(self, sql: str, parameters: tuple[object, ...] = ()) -> list[tuple[object, ...]]:
        connection = sqlite3.connect(self.arguments.database)
        try:
            return connection.execute(sql, parameters).fetchall()
        finally:
            connection.close()

    def row_counts(self, database: Path | None = None) -> tuple[int, int, int]:
        connection = sqlite3.connect(database or self.arguments.database)
        try:
            return tuple(
                int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in ("processed_operations", "event_log", "upload_outbox")
            )
        finally:
            connection.close()

    def canonical_hash(self, database: Path | None = None) -> str:
        connection, _configuration = STORAGE.open_database(database or self.arguments.database)
        try:
            return STORAGE.canonical_state_sha256(STORAGE.canonical_database_state(connection))
        finally:
            connection.close()

    def diagnostic_codes(self, report) -> set[str]:
        return {item["code"] for item in report.document["diagnostics"]}

    def two_store_session(self, conflict: str) -> dict[str, object]:
        document = copy.deepcopy(self.example)
        document["operations"] = document["operations"][:2]
        second = document["operations"][1]["payload"]
        first = document["operations"][0]["payload"]
        if conflict == "event":
            second["event_id"] = first["event_id"]
        elif conflict == "upload":
            second["upload_record_id"] = first["upload_record_id"]
        elif conflict == "idempotency":
            second["idempotency_key"] = first["idempotency_key"]
        return document

    def test_sql_schema_parses_and_executes(self) -> None:
        connection = sqlite3.connect(":memory:")
        try:
            connection.executescript(SQL_PATH.read_text(encoding="utf-8"))
        finally:
            connection.close()

    def test_database_initialization(self) -> None:
        self.assertTrue(self.run().document["database"]["created"])

    def test_schema_metadata_version_one(self) -> None:
        self.run()
        self.assertIn(("schema_version", "1"), self.query("SELECT * FROM schema_metadata"))

    def test_schema_metadata_phase(self) -> None:
        self.run()
        self.assertIn(("application_phase", "ST-004"), self.query("SELECT * FROM schema_metadata"))

    def test_wal_mode(self) -> None:
        self.assertEqual(self.run().document["database"]["journal_mode"], "wal")

    def test_synchronous_full(self) -> None:
        self.assertEqual(self.run().document["database"]["synchronous"], "FULL")

    def test_foreign_keys_on(self) -> None:
        self.assertTrue(self.run().document["database"]["foreign_keys"])

    def test_busy_timeout_5000(self) -> None:
        self.assertEqual(self.run().document["database"]["busy_timeout_ms"], 5000)

    def test_four_strict_tables(self) -> None:
        self.run()
        rows = self.query("PRAGMA table_list")
        strict = {row[1] for row in rows if row[2] == "table" and row[5] == 1 and not row[1].startswith("sqlite_")}
        self.assertEqual(strict, {"schema_metadata", "processed_operations", "event_log", "upload_outbox"})

    def test_exact_table_count(self) -> None:
        self.run()
        rows = self.query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        self.assertEqual(len(rows), 4)

    def test_no_triggers(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT name FROM sqlite_master WHERE type='trigger'"), [])

    def test_no_views(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT name FROM sqlite_master WHERE type='view'"), [])

    def test_no_manual_indexes(self) -> None:
        self.run()
        indexes = self.query("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'")
        self.assertEqual(indexes, [])

    def test_positive_session_parse(self) -> None:
        self.assertEqual(STORAGE.validate_session(copy.deepcopy(self.example))["session_version"], 1)

    def test_operation_input_order(self) -> None:
        parsed = STORAGE.validate_session(copy.deepcopy(self.example))
        self.assertEqual([item["operation_id"] for item in parsed["operations"]], [f"OP-ST004-00{i}" for i in range(1, 7)])

    def test_store_event(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT COUNT(*) FROM event_log")[0][0], 3)

    def test_event_payload_canonical_json(self) -> None:
        self.run()
        payload = self.query("SELECT payload_json FROM event_log WHERE event_id='EVENT-ST004-001'")[0][0]
        self.assertEqual(payload, '{"mission_state":"DRAFT","simulation":true}')

    def test_event_payload_sha256(self) -> None:
        self.run()
        payload, digest = self.query("SELECT payload_json, payload_sha256 FROM event_log WHERE event_id='EVENT-ST004-001'")[0]
        self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(), digest)

    def test_enqueue_upload(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT COUNT(*) FROM upload_outbox")[0][0], 2)

    def test_pending_outbox(self) -> None:
        self.assertEqual(self.run().document["outbox"]["pending_count"], 1)

    def test_record_upload_attempt(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT status FROM upload_outbox WHERE upload_record_id='UPLOAD-ST004-001'")[0][0], "ACKNOWLEDGED")

    def test_attempt_count_increment(self) -> None:
        self.assertEqual(self.run().document["outbox"]["attempt_count_total"], 1)

    def test_last_error_saved_before_acknowledgement(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"] = document["operations"][:3]
        self.write_session(document)
        self.run()
        self.assertEqual(self.query("SELECT last_error_code FROM upload_outbox WHERE upload_record_id='UPLOAD-ST004-001'")[0][0], "OFFLINE")

    def test_acknowledge_upload(self) -> None:
        self.assertEqual(self.run().document["outbox"]["acknowledged_count"], 1)

    def test_acknowledgement_saved(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT acknowledgement_id FROM upload_outbox WHERE upload_record_id='UPLOAD-ST004-001'")[0][0], "ACK-DEMO-ST004-001")

    def test_acknowledgement_clears_last_error(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT last_error_code FROM upload_outbox WHERE upload_record_id='UPLOAD-ST004-001'")[0][0], "")

    def test_event_without_upload(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT COUNT(*) FROM upload_outbox WHERE event_id='EVENT-ST004-003'")[0][0], 0)

    def test_integrity_check(self) -> None:
        self.assertEqual(self.run().document["integrity"]["result"], "OK")

    def test_transaction_commit(self) -> None:
        self.assertTrue(self.run().document["transaction"]["committed"])

    def test_atomic_session_true(self) -> None:
        self.assertTrue(self.run().document["transaction"]["atomic_session"])

    def test_connection_reopen(self) -> None:
        self.assertTrue(self.run().document["database"]["reopened"])

    def test_committed_data_persistence(self) -> None:
        self.run()
        self.assertEqual(self.row_counts(), (6, 3, 2))

    def test_canonical_state_property_order(self) -> None:
        self.run()
        connection = sqlite3.connect(self.arguments.database)
        try:
            state = STORAGE.canonical_database_state(connection)
        finally:
            connection.close()
        self.assertEqual(list(state), ["schema_metadata", "processed_operations", "event_log", "upload_outbox"])

    def test_canonical_processed_row_order(self) -> None:
        self.run()
        connection = sqlite3.connect(self.arguments.database)
        try:
            rows = STORAGE.canonical_database_state(connection)["processed_operations"]
        finally:
            connection.close()
        self.assertEqual([row["operation_id"] for row in rows], sorted(row["operation_id"] for row in rows))

    def test_canonical_state_sha256_format(self) -> None:
        digest = self.run().document["canonical_state_sha256"]
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_report_root_property_order(self) -> None:
        expected = ["report_version", "phase", "session_id", "result", "database", "transaction", "schema", "operations", "events", "outbox", "integrity", "idempotency", "safety", "summary", "diagnostics", "canonical_state_sha256", "exit_code"]
        self.assertEqual(list(self.run().document), expected)

    def test_database_property_order(self) -> None:
        self.assertEqual(list(self.run().document["database"]), ["created", "reopened", "database_outside_repository", "journal_mode", "synchronous", "foreign_keys", "busy_timeout_ms"])

    def test_transaction_property_order(self) -> None:
        self.assertEqual(list(self.run().document["transaction"]), ["atomic_session", "begun", "committed", "rolled_back"])

    def test_schema_property_order(self) -> None:
        self.assertEqual(list(self.run().document["schema"]), ["schema_version", "supported", "initialized", "migration_performed"])

    def test_operations_property_order(self) -> None:
        self.assertEqual(list(self.run().document["operations"]), ["input_count", "processed_count", "applied_count", "duplicate_noop_count", "rejected_count"])

    def test_events_property_order(self) -> None:
        self.assertEqual(list(self.run().document["events"]), ["stored_count", "total_count"])

    def test_outbox_property_order(self) -> None:
        self.assertEqual(list(self.run().document["outbox"]), ["created_count", "pending_count", "acknowledged_count", "dead_letter_count", "attempt_count_total"])

    def test_integrity_property_order(self) -> None:
        self.assertEqual(list(self.run().document["integrity"]), ["check_performed", "result"])

    def test_idempotency_property_order(self) -> None:
        self.assertEqual(list(self.run().document["idempotency"]), ["request_hash_algorithm", "duplicate_noop_count", "conflict_count"])

    def test_safety_property_order(self) -> None:
        expected = ["offline_only", "network_access_performed", "gpio_access_performed", "serial_access_performed", "hardware_output_performed", "motor_control_performed", "charging_control_performed", "rover_communication_performed", "actual_upload_performed", "repository_modified", "physical_estop_independent"]
        self.assertEqual(list(self.run().document["safety"]), expected)

    def test_summary_property_order(self) -> None:
        self.assertEqual(list(self.run().document["summary"]), ["table_count", "row_count_total", "diagnostic_count", "next_phase_eligible"])

    def test_text_property_order(self) -> None:
        keys = [line.split("=", 1)[0] for line in STORAGE.render_text_report(self.run()).splitlines()]
        self.assertEqual(keys[0:4], ["report_version", "phase", "session_id", "result"])
        self.assertEqual(keys[-2:], ["diagnostic_count", "exit_code"])

    def test_session_schema_conformance_shape(self) -> None:
        schema = json.loads(SESSION_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(self.example), set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])
        STORAGE.validate_session(copy.deepcopy(self.example))

    def test_report_schema_conformance_shape(self) -> None:
        schema = json.loads(REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(self.run().document), set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])

    def test_fresh_json_reports_byte_identical(self) -> None:
        first = self.run(self.make_arguments("fresh-a.db", "fresh-a"))
        second = self.run(self.make_arguments("fresh-b.db", "fresh-b"))
        self.assertEqual(STORAGE.render_json_report(first), STORAGE.render_json_report(second))

    def test_fresh_text_reports_byte_identical(self) -> None:
        first = self.run(self.make_arguments("fresh-a.db", "fresh-a"))
        second = self.run(self.make_arguments("fresh-b.db", "fresh-b"))
        self.assertEqual(STORAGE.render_text_report(first), STORAGE.render_text_report(second))

    def test_fresh_canonical_hash_identical(self) -> None:
        first = self.run(self.make_arguments("fresh-a.db", "fresh-a"))
        second = self.run(self.make_arguments("fresh-b.db", "fresh-b"))
        self.assertEqual(first.document["canonical_state_sha256"], second.document["canonical_state_sha256"])

    def test_same_session_second_run_passes(self) -> None:
        self.run()
        self.assertEqual(self.run().document["result"], "PASS")

    def test_second_run_duplicate_noop_count_six(self) -> None:
        self.run()
        self.assertEqual(self.run().document["operations"]["duplicate_noop_count"], 6)

    def test_second_run_row_counts_unchanged(self) -> None:
        self.run()
        before = self.row_counts()
        self.run()
        self.assertEqual(self.row_counts(), before)

    def test_second_run_canonical_hash_unchanged(self) -> None:
        first = self.run()
        second = self.run()
        self.assertEqual(first.document["canonical_state_sha256"], second.document["canonical_state_sha256"])

    def test_database_outside_repository(self) -> None:
        self.assertTrue(self.run().document["database"]["database_outside_repository"])

    def test_report_paths_outside_repository(self) -> None:
        self.run(write_reports=True)
        self.assertTrue(self.arguments.json_report.is_file() and self.arguments.text_report.is_file())

    def test_network_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["network_access_performed"])

    def test_gpio_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["gpio_access_performed"])

    def test_serial_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["serial_access_performed"])

    def test_hardware_output_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["hardware_output_performed"])

    def test_actual_upload_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["actual_upload_performed"])

    def test_physical_estop_independent(self) -> None:
        self.assertTrue(self.run().document["safety"]["physical_estop_independent"])

    def test_database_not_created_in_repository(self) -> None:
        self.run()
        self.assertFalse(any(self.repository.rglob("*.db")))

    def test_repository_inventory_unchanged(self) -> None:
        before = sorted(path.relative_to(self.repository) for path in self.repository.rglob("*"))
        self.run(write_reports=True)
        after = sorted(path.relative_to(self.repository) for path in self.repository.rglob("*"))
        self.assertEqual(before, after)

    def test_no_persistent_probe_file(self) -> None:
        self.run()
        self.assertFalse(any(path.name.startswith("storage-probe") for path in self.root.rglob("*")))

    def test_operation_request_hash_stable(self) -> None:
        operation = self.example["operations"][0]
        self.assertEqual(STORAGE.operation_request_sha256(operation), STORAGE.operation_request_sha256(copy.deepcopy(operation)))

    def test_canonical_json_unicode(self) -> None:
        self.assertEqual(STORAGE.canonical_json({"value": "水"}), '{"value":"水"}')

    def test_canonical_json_compact_sorted(self) -> None:
        self.assertEqual(STORAGE.canonical_json({"z": 1, "a": 2}), '{"a":2,"z":1}')

    def test_report_has_no_database_file_hash(self) -> None:
        self.assertNotIn("database_file_sha256", STORAGE.render_json_report(self.run()))

    def test_report_has_no_absolute_paths(self) -> None:
        rendered = STORAGE.render_json_report(self.run())
        self.assertNotIn(str(self.repository), rendered)
        self.assertNotIn(str(self.arguments.database), rendered)

    def test_report_has_no_timestamp(self) -> None:
        rendered = STORAGE.render_json_report(self.run()).casefold()
        self.assertNotIn("timestamp", rendered)
        self.assertNotIn("current_time", rendered)

    def test_source_imports_standard_library_only(self) -> None:
        tree = ast.parse(IMPLEMENTATION_PATH.read_text(encoding="utf-8"))
        imports = {node.names[0].name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)}
        imports |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module != "__future__"}
        self.assertEqual(imports, {"argparse", "hashlib", "json", "math", "os", "dataclasses", "pathlib", "re", "sqlite3", "sys", "typing"})

    def test_sql_has_no_forbidden_statements(self) -> None:
        sql = SQL_PATH.read_text(encoding="utf-8").upper()
        for keyword in ("DELETE", "DROP", "VACUUM", "CREATE TRIGGER", "CREATE VIEW", "CREATE INDEX"):
            self.assertNotIn(keyword, sql)

    def test_cli_stdout_uses_text_report(self) -> None:
        argv = ["--repository-root", str(self.repository), "--database", str(self.arguments.database), "--session", str(self.session_path), "--json-report", str(self.arguments.json_report), "--text-report", str(self.arguments.text_report)]
        with redirect_stdout(io.StringIO()) as output:
            code = STORAGE.main(argv)
        self.assertEqual(code, 0)
        self.assertEqual(output.getvalue(), self.arguments.text_report.read_text(encoding="utf-8"))

    def test_invalid_session_version(self) -> None:
        document = copy.deepcopy(self.example)
        document["session_version"] = 2
        self.write_session(document)
        self.assertEqual(self.run().exit_code, 3)

    def test_unknown_operation_type(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["operation_type"] = "ONLINE_UPLOAD"
        self.write_session(document)
        self.assertIn("STORAGE_OPERATION_UNKNOWN", self.diagnostic_codes(self.run()))

    def test_duplicate_json_key(self) -> None:
        self.session_path.write_text('{"session_version":1,"session_version":1,"session_id":"SESSION-ST004-X","operations":[]}', encoding="utf-8")
        self.assertIn("STORAGE_SESSION_INVALID", self.diagnostic_codes(self.run()))

    def test_reversed_logical_tick(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][1]["logical_tick"] = 0
        document["operations"][0]["logical_tick"] = 1
        self.write_session(document)
        self.assertIn("STORAGE_SESSION_TICK_REVERSED", self.diagnostic_codes(self.run()))

    def test_boolean_used_as_integer(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["logical_tick"] = True
        self.write_session(document)
        self.assertEqual(self.run().exit_code, 3)

    def test_invalid_source_type(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["source_type"] = "CLOUD"
        self.write_session(document)
        self.assertEqual(self.run().exit_code, 3)

    def test_invalid_enqueue_fields(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][4]["payload"]["upload_record_id"] = "UPLOAD-ST004-X"
        self.write_session(document)
        self.assertEqual(self.run().exit_code, 3)

    def test_missing_event_id(self) -> None:
        document = copy.deepcopy(self.example)
        del document["operations"][0]["payload"]["event_id"]
        self.write_session(document)
        self.assertEqual(self.run().exit_code, 3)

    def test_duplicate_event_id_from_different_operation(self) -> None:
        self.write_session(self.two_store_session("event"))
        self.assertIn("STORAGE_EVENT_CONFLICT", self.diagnostic_codes(self.run()))

    def test_duplicate_upload_record_id(self) -> None:
        self.write_session(self.two_store_session("upload"))
        self.assertEqual(self.run().exit_code, 4)

    def test_duplicate_idempotency_key(self) -> None:
        self.write_session(self.two_store_session("idempotency"))
        self.assertEqual(self.run().exit_code, 4)

    def test_unknown_upload_record(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"] = [document["operations"][2]]
        self.write_session(document)
        self.assertIn("STORAGE_OUTBOX_RECORD_NOT_FOUND", self.diagnostic_codes(self.run()))

    def test_acknowledge_unknown_record(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"] = [document["operations"][3]]
        self.write_session(document)
        self.assertIn("STORAGE_OUTBOX_RECORD_NOT_FOUND", self.diagnostic_codes(self.run()))

    def test_acknowledge_already_acknowledged_different_operation(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"].append({"operation_id": "OP-ST004-007", "logical_tick": 10, "operation_type": "ACKNOWLEDGE_UPLOAD", "payload": {"upload_record_id": "UPLOAD-ST004-001", "acknowledgement_id": "ACK-DEMO-ST004-001"}})
        self.write_session(document)
        self.assertIn("STORAGE_OUTBOX_STATE_CONFLICT", self.diagnostic_codes(self.run()))

    def test_attempt_on_acknowledged_record(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"].append({"operation_id": "OP-ST004-007", "logical_tick": 10, "operation_type": "RECORD_UPLOAD_ATTEMPT", "payload": {"upload_record_id": "UPLOAD-ST004-001", "error_code": "OFFLINE"}})
        self.write_session(document)
        self.assertIn("STORAGE_OUTBOX_STATE_CONFLICT", self.diagnostic_codes(self.run()))

    def test_same_operation_id_changed_payload(self) -> None:
        first = self.run()
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["event_payload"]["simulation"] = False
        self.write_session(document)
        second = self.run()
        self.assertIn("STORAGE_IDEMPOTENCY_CONFLICT", self.diagnostic_codes(second))
        self.assertEqual(first.document["canonical_state_sha256"], second.document["canonical_state_sha256"])

    def test_schema_version_two_rejected(self) -> None:
        connection = sqlite3.connect(self.arguments.database)
        connection.execute("CREATE TABLE schema_metadata(metadata_key TEXT PRIMARY KEY, metadata_value TEXT NOT NULL) STRICT")
        connection.executemany("INSERT INTO schema_metadata VALUES (?, ?)", (("schema_version", "2"), ("application_phase", "ST-004")))
        connection.commit()
        connection.close()
        self.assertIn("STORAGE_SCHEMA_VERSION_UNSUPPORTED", self.diagnostic_codes(self.run()))

    def test_database_path_inside_repository(self) -> None:
        arguments = STORAGE.StorageArguments(self.repository, self.repository / "station.db", self.session_path, self.arguments.json_report, self.arguments.text_report)
        with self.assertRaisesRegex(STORAGE.StorageFailure, "outside"):
            STORAGE.validate_arguments(arguments)

    def test_report_path_inside_repository(self) -> None:
        arguments = STORAGE.StorageArguments(self.repository, self.arguments.database, self.session_path, self.repository / "report.json", self.arguments.text_report)
        with self.assertRaisesRegex(STORAGE.StorageFailure, "outside"):
            STORAGE.validate_arguments(arguments)

    def test_missing_database_parent(self) -> None:
        arguments = STORAGE.StorageArguments(self.repository, self.root / "missing" / "station.db", self.session_path, self.arguments.json_report, self.arguments.text_report)
        with self.assertRaises(STORAGE.StorageFailure):
            STORAGE.validate_arguments(arguments)

    def test_missing_report_parent(self) -> None:
        arguments = STORAGE.StorageArguments(self.repository, self.arguments.database, self.session_path, self.root / "missing" / "report.json", self.arguments.text_report)
        with self.assertRaises(STORAGE.StorageFailure):
            STORAGE.validate_arguments(arguments)

    def test_database_parent_is_file(self) -> None:
        parent = self.root / "database-parent-file"
        parent.write_text("x", encoding="utf-8")
        arguments = STORAGE.StorageArguments(self.repository, parent / "station.db", self.session_path, self.arguments.json_report, self.arguments.text_report)
        with self.assertRaises(STORAGE.StorageFailure):
            STORAGE.validate_arguments(arguments)

    def test_report_parent_is_file(self) -> None:
        parent = self.root / "report-parent-file"
        parent.write_text("x", encoding="utf-8")
        arguments = STORAGE.StorageArguments(self.repository, self.arguments.database, self.session_path, parent / "report.json", self.arguments.text_report)
        with self.assertRaises(STORAGE.StorageFailure):
            STORAGE.validate_arguments(arguments)

    def test_transaction_injected_failure(self) -> None:
        report = self.run(fail_after_operation_index=2)
        self.assertEqual(report.exit_code, 4)
        self.assertTrue(report.document["transaction"]["rolled_back"])

    def test_no_partial_operation_after_injected_failure(self) -> None:
        self.run(fail_after_operation_index=2)
        self.assertEqual(self.row_counts()[0], 0)

    def test_no_partial_event_after_injected_failure(self) -> None:
        self.run(fail_after_operation_index=2)
        self.assertEqual(self.row_counts()[1], 0)

    def test_no_partial_outbox_after_injected_failure(self) -> None:
        self.run(fail_after_operation_index=2)
        self.assertEqual(self.row_counts()[2], 0)

    def test_previous_committed_state_after_rollback(self) -> None:
        first = self.run()
        document = copy.deepcopy(self.example)
        document["session_id"] = "SESSION-ST004-ROLLBACK"
        document["operations"][0]["operation_id"] = "OP-ST004-101"
        document["operations"][0]["payload"]["event_id"] = "EVENT-ST004-101"
        document["operations"][0]["payload"]["upload_record_id"] = "UPLOAD-ST004-101"
        document["operations"][0]["payload"]["idempotency_key"] = "IDEMPOTENCY-ST004-101"
        document["operations"] = document["operations"][:1]
        self.write_session(document)
        self.run(fail_after_operation_index=0)
        self.assertEqual(self.canonical_hash(), first.document["canonical_state_sha256"])

    def test_integrity_after_rollback(self) -> None:
        report = self.run(fail_after_operation_index=2)
        self.assertEqual(report.document["integrity"]["result"], "OK")

    def test_sqlite_exception_rolls_back(self) -> None:
        def failing_processor(_connection, _operation):
            raise sqlite3.OperationalError("expected test failure")
        report = self.run(operation_processor=failing_processor)
        self.assertTrue(report.document["transaction"]["rolled_back"])
        self.assertEqual(self.row_counts(), (0, 0, 0))

    def test_report_write_failure(self) -> None:
        with mock.patch.object(STORAGE, "write_report", side_effect=OSError):
            report = self.run(write_reports=True)
        self.assertEqual(report.exit_code, 7)
        self.assertIn("STORAGE_REPORT_WRITE_FAILED", self.diagnostic_codes(report))

    def test_unexpected_internal_exception(self) -> None:
        argv = ["--repository-root", str(self.repository), "--database", str(self.arguments.database), "--session", str(self.session_path), "--json-report", str(self.arguments.json_report), "--text-report", str(self.arguments.text_report)]
        with mock.patch.object(STORAGE, "run_storage_session", side_effect=RuntimeError("private detail")):
            with redirect_stderr(io.StringIO()) as output:
                code = STORAGE.main(argv)
        self.assertEqual(code, 7)
        self.assertNotIn("private detail", output.getvalue())

    def test_corrupted_schema_metadata_fails_closed(self) -> None:
        connection = sqlite3.connect(self.arguments.database)
        connection.execute("CREATE TABLE schema_metadata(metadata_key TEXT PRIMARY KEY, metadata_value TEXT NOT NULL) STRICT")
        connection.execute("INSERT INTO schema_metadata VALUES ('schema_version', '1')")
        connection.commit()
        connection.close()
        self.assertIn("STORAGE_SCHEMA_VERSION_UNSUPPORTED", self.diagnostic_codes(self.run()))

    def test_diagnostics_sort_order(self) -> None:
        report = self.run(fail_after_operation_index=0)
        diagnostics = report.document["diagnostics"]
        expected = sorted(diagnostics, key=lambda item: (item["component"], item["code"], item["operation_id"], item["message"]))
        self.assertEqual(diagnostics, expected)

    def test_non_finite_json_rejected(self) -> None:
        self.session_path.write_text('{"session_version":1,"session_id":"SESSION-ST004-X","operations":[{"operation_id":"OP-ST004-X","logical_tick":0,"operation_type":"VERIFY_INTEGRITY","payload":{"value":NaN}}]}', encoding="utf-8")
        self.assertEqual(self.run().exit_code, 3)

    def test_null_event_payload_value_rejected(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["event_payload"]["value"] = None
        self.write_session(document)
        self.assertEqual(self.run().exit_code, 3)

    def test_no_bytecode_created_by_contract(self) -> None:
        self.assertFalse(any(STATION_CONTROL_ROOT.rglob("__pycache__")))
        self.assertFalse(any(STATION_CONTROL_ROOT.rglob("*.pyc")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
