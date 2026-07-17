"""Standard-library tests for ST-005 offline field profile registry."""

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


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_PATH = ROOT / "station" / "field_profiles.py"
SQL_PATH = ROOT / "storage" / "field_profiles_schema_v1.sql"
SESSION_SCHEMA_PATH = ROOT / "schemas" / "field-profile-session.schema.json"
REPORT_SCHEMA_PATH = ROOT / "schemas" / "field-profile-report.schema.json"
EXAMPLE_PATH = ROOT / "config_examples" / "field-profile-session.example.json"

SPEC = importlib.util.spec_from_file_location("station_field_profiles", IMPLEMENTATION_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load field profiles module.")
FIELD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FIELD
SPEC.loader.exec_module(FIELD)


class FieldProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="st005-test-")
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.database_dir = self.root / "database"
        self.report_dir = self.root / "reports"
        self.session_dir = self.root / "sessions"
        for path in (self.repository, self.database_dir, self.report_dir, self.session_dir):
            path.mkdir()
        schema_copy = self.repository / "software" / "station_control" / "storage" / "field_profiles_schema_v1.sql"
        schema_copy.parent.mkdir(parents=True)
        shutil.copy2(SQL_PATH, schema_copy)
        self.example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        self.session_path = self.session_dir / "session.json"
        self.write_session(self.example)
        self.arguments = self.make_arguments("field_profiles.db", "report")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_arguments(self, database_name: str, report_stem: str):
        return FIELD.FieldArguments(
            self.repository,
            self.database_dir / database_name,
            self.session_path,
            self.report_dir / f"{report_stem}.json",
            self.report_dir / f"{report_stem}.txt",
        )

    def write_session(self, document: object, path: Path | None = None) -> Path:
        target = path or self.session_path
        target.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return target

    def run(self, result=None, arguments=None, **kwargs):
        if result is not None and not isinstance(result, FIELD.FieldArguments):
            return super().run(result)
        selected = result if isinstance(result, FIELD.FieldArguments) else arguments
        return FIELD.run_field_profile_session(selected or self.arguments, **kwargs)

    def query(self, sql: str, parameters: tuple[object, ...] = (), database: Path | None = None):
        connection = sqlite3.connect(database or self.arguments.database)
        try:
            return connection.execute(sql, parameters).fetchall()
        finally:
            connection.close()

    def canonical_hash(self, database: Path | None = None) -> str:
        connection, _configuration = FIELD.open_database(database or self.arguments.database)
        try:
            return FIELD.canonical_state_sha256(FIELD.canonical_database_state(connection))
        finally:
            connection.close()

    def row_counts(self, database: Path | None = None) -> tuple[int, ...]:
        connection = sqlite3.connect(database or self.arguments.database)
        try:
            return tuple(
                int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table, _columns, _key in FIELD.TABLE_DEFINITIONS
            )
        finally:
            connection.close()

    def codes(self, report) -> set[str]:
        return {item["code"] for item in report.document["diagnostics"]}

    def assert_validation_failure(self, document: object, code: str) -> None:
        with self.assertRaises(FIELD.FieldFailure) as caught:
            FIELD.validate_session(document)
        self.assertEqual(caught.exception.code, code)

    def single_session(self, operation: dict[str, object], suffix: str = "CUSTOM") -> dict[str, object]:
        return {"session_version": 1, "session_id": f"SESSION-ST005-{suffix}", "operations": [operation]}

    def switch_session(self, **changes: object) -> dict[str, object]:
        operation = {
            "operation_id": "OP-ST005-SWITCH-002",
            "logical_tick": 10,
            "operation_type": "SET_ACTIVE_FIELD",
            "payload": {
                "target_field_id": "FIELD-DEMO-002",
                "operator_approved": True,
                "all_rovers_stopped": True,
                "active_mission_count": 0,
                "charging_transition_count": 0,
                "reason": "operator selected second demo field",
            },
        }
        operation["payload"].update(changes)
        return self.single_session(operation, "SWITCH")

    def revision_session(self, field_index: int = 0, **changes: object) -> dict[str, object]:
        source = copy.deepcopy(self.example["operations"][field_index]["payload"])
        operation = {
            "operation_id": f"OP-ST005-REVISE-{field_index + 1:03d}",
            "logical_tick": 10,
            "operation_type": "REVISE_FIELD",
            "payload": {
                "field_id": source["field_id"],
                "expected_revision": 1,
                "new_revision": 2,
                "display_name": source["display_name"] + " revised",
                "enabled": source["enabled"],
                "local_frame_id": source["local_frame_id"],
                "references": source["references"],
                "no_go_zones": source["no_go_zones"],
                "operator_approved": True,
                "all_rovers_stopped": True,
                "active_mission_count": 0,
                "charging_transition_count": 0,
            },
        }
        operation["payload"].update(changes)
        return self.single_session(operation, "REVISE")

    def test_sql_schema_execute(self) -> None:
        connection = sqlite3.connect(":memory:")
        try:
            connection.executescript(SQL_PATH.read_text(encoding="utf-8"))
        finally:
            connection.close()

    def test_database_created(self) -> None:
        self.assertTrue(self.run().document["database"]["created"])

    def test_six_strict_tables(self) -> None:
        self.run()
        rows = self.query("PRAGMA table_list")
        strict = {row[1] for row in rows if row[2] == "table" and row[5] == 1 and not row[1].startswith("sqlite_")}
        self.assertEqual(strict, {item[0] for item in FIELD.TABLE_DEFINITIONS})

    def test_exact_table_count(self) -> None:
        self.run()
        self.assertEqual(len(self.query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")), 6)

    def test_schema_metadata_version(self) -> None:
        self.run()
        self.assertIn(("schema_version", "1"), self.query("SELECT * FROM field_schema_metadata"))

    def test_schema_metadata_phase(self) -> None:
        self.run()
        self.assertIn(("application_phase", "ST-005"), self.query("SELECT * FROM field_schema_metadata"))

    def test_wal(self) -> None:
        self.assertEqual(self.run().document["database"]["journal_mode"], "wal")

    def test_synchronous_full(self) -> None:
        self.assertEqual(self.run().document["database"]["synchronous"], "FULL")

    def test_foreign_keys(self) -> None:
        self.assertTrue(self.run().document["database"]["foreign_keys"])

    def test_busy_timeout(self) -> None:
        self.assertEqual(self.run().document["database"]["busy_timeout_ms"], 5000)

    def test_no_triggers(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT name FROM sqlite_master WHERE type='trigger'"), [])

    def test_no_views(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT name FROM sqlite_master WHERE type='view'"), [])

    def test_no_manual_indexes(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'"), [])

    def test_positive_session_parse(self) -> None:
        self.assertEqual(FIELD.validate_session(copy.deepcopy(self.example))["session_version"], 1)

    def test_operation_input_order(self) -> None:
        parsed = FIELD.validate_session(copy.deepcopy(self.example))
        self.assertEqual([item["operation_id"] for item in parsed["operations"]], [f"OP-ST005-00{i}" for i in range(1, 5)])

    def test_two_field_registration(self) -> None:
        self.assertEqual(self.run().document["fields"]["total_count"], 2)

    def test_eight_required_references(self) -> None:
        self.assertEqual(self.run().document["references"]["total_count"], 8)

    def test_two_no_go_zones(self) -> None:
        self.assertEqual(self.run().document["no_go_zones"]["total_count"], 2)

    def test_active_field_selection(self) -> None:
        self.assertEqual(self.run().document["active_field"]["active_field_id"], "FIELD-DEMO-001")

    def test_selection_revision_one(self) -> None:
        self.assertEqual(self.run().document["active_field"]["selection_revision"], 1)

    def test_integrity_ok(self) -> None:
        self.assertEqual(self.run().document["integrity"]["result"], "OK")

    def test_reopen(self) -> None:
        self.assertTrue(self.run().document["database"]["reopened"])

    def test_persistence(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT display_name FROM field_profiles ORDER BY field_id"), [("Field 1",), ("Field 2",)])

    def test_profile_json_canonical(self) -> None:
        self.run()
        value = self.query("SELECT profile_json FROM field_profiles WHERE field_id='FIELD-DEMO-001'")[0][0]
        self.assertNotIn(": ", value)
        self.assertNotIn(", ", value)

    def test_profile_sha256(self) -> None:
        self.run()
        value, digest = self.query("SELECT profile_json, profile_sha256 FROM field_profiles WHERE field_id='FIELD-DEMO-001'")[0]
        self.assertEqual(hashlib.sha256(value.encode()).hexdigest(), digest)

    def test_boundary_json_canonical(self) -> None:
        self.run()
        value = self.query("SELECT boundary_json FROM field_no_go_zones ORDER BY zone_id")[0][0]
        self.assertTrue(value.startswith('["local-zone-ref:'))

    def test_boundary_sha256(self) -> None:
        self.run()
        value, digest = self.query("SELECT boundary_json, boundary_sha256 FROM field_no_go_zones ORDER BY zone_id")[0]
        self.assertEqual(hashlib.sha256(value.encode()).hexdigest(), digest)

    def test_canonical_root_order(self) -> None:
        self.run()
        connection, _configuration = FIELD.open_database(self.arguments.database)
        try:
            self.assertEqual(tuple(FIELD.canonical_database_state(connection)), tuple(item[0] for item in FIELD.TABLE_DEFINITIONS))
        finally:
            connection.close()

    def test_canonical_row_order(self) -> None:
        self.run()
        connection, _configuration = FIELD.open_database(self.arguments.database)
        try:
            state = FIELD.canonical_database_state(connection)
        finally:
            connection.close()
        self.assertEqual([row["field_id"] for row in state["field_profiles"]], sorted(row["field_id"] for row in state["field_profiles"]))

    def test_canonical_sha256_format(self) -> None:
        self.assertRegex(self.run().document["canonical_state_sha256"], r"^[0-9a-f]{64}$")

    def test_report_root_order(self) -> None:
        expected = ("report_version", "phase", "session_id", "result", "database", "transaction", "schema", "operations", "fields", "references", "no_go_zones", "active_field", "integrity", "idempotency", "safety", "summary", "diagnostics", "canonical_state_sha256", "exit_code")
        self.assertEqual(tuple(self.run().document), expected)

    def test_database_nested_order(self) -> None:
        self.assertEqual(tuple(self.run().document["database"]), ("created", "reopened", "database_outside_repository", "journal_mode", "synchronous", "foreign_keys", "busy_timeout_ms"))

    def test_safety_nested_order(self) -> None:
        self.assertEqual(tuple(self.run().document["safety"])[0], "offline_only")

    def test_text_report_order(self) -> None:
        text = FIELD.render_text_report(self.run())
        self.assertTrue(text.startswith("report_version=1\nphase=ST-005\n"))

    def test_session_schema_shape(self) -> None:
        schema = json.loads(SESSION_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_report_schema_shape(self) -> None:
        schema = json.loads(REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])

    def test_fresh_json_byte_identical(self) -> None:
        a = self.run(arguments=self.make_arguments("a.db", "a"))
        b = self.run(arguments=self.make_arguments("b.db", "b"))
        self.assertEqual(FIELD.render_json_report(a), FIELD.render_json_report(b))

    def test_fresh_text_byte_identical(self) -> None:
        a = self.run(arguments=self.make_arguments("a.db", "a"))
        b = self.run(arguments=self.make_arguments("b.db", "b"))
        self.assertEqual(FIELD.render_text_report(a), FIELD.render_text_report(b))

    def test_fresh_canonical_hash_identical(self) -> None:
        a = self.run(arguments=self.make_arguments("a.db", "a"))
        b = self.run(arguments=self.make_arguments("b.db", "b"))
        self.assertEqual(a.document["canonical_state_sha256"], b.document["canonical_state_sha256"])

    def test_same_session_second_run_noop(self) -> None:
        self.run()
        second = self.run()
        self.assertEqual(second.document["operations"]["duplicate_noop_count"], 4)

    def test_second_run_applied_zero(self) -> None:
        self.run()
        self.assertEqual(self.run().document["operations"]["applied_count"], 0)

    def test_second_run_rows_unchanged(self) -> None:
        self.run()
        before = self.row_counts()
        self.run()
        self.assertEqual(self.row_counts(), before)

    def test_second_run_hash_unchanged(self) -> None:
        first = self.run().document["canonical_state_sha256"]
        second = self.run().document["canonical_state_sha256"]
        self.assertEqual(second, first)

    def test_same_target_noop(self) -> None:
        self.run()
        session = self.switch_session(target_field_id="FIELD-DEMO-001")
        self.write_session(session)
        report = self.run()
        self.assertEqual(report.document["active_field"]["selection_revision"], 1)

    def test_safe_field_two_switch(self) -> None:
        self.run()
        self.write_session(self.switch_session())
        report = self.run()
        self.assertEqual(report.document["active_field"]["active_field_id"], "FIELD-DEMO-002")

    def test_field_two_switch_revision_two(self) -> None:
        self.run()
        self.write_session(self.switch_session())
        self.assertEqual(self.run().document["active_field"]["selection_revision"], 2)

    def test_field_revision(self) -> None:
        self.run()
        self.write_session(self.revision_session(0))
        self.assertEqual(self.run().document["fields"]["revised_count"], 1)

    def test_inactive_field_revision(self) -> None:
        self.run()
        self.write_session(self.revision_session(1))
        self.assertEqual(self.run().exit_code, 0)

    def test_safe_active_field_revision(self) -> None:
        self.run()
        self.write_session(self.revision_session(0))
        self.assertEqual(self.run().exit_code, 0)

    def test_revision_persists(self) -> None:
        self.run()
        self.write_session(self.revision_session(0))
        self.run()
        self.assertEqual(self.query("SELECT profile_revision FROM field_profiles WHERE field_id='FIELD-DEMO-001'")[0][0], 2)

    def test_network_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["network_access_performed"])

    def test_gpio_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["gpio_access_performed"])

    def test_serial_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["serial_access_performed"])

    def test_hardware_output_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["hardware_output_performed"])

    def test_actual_water_control_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["actual_water_control_performed"])

    def test_no_automatic_field_selection(self) -> None:
        self.assertFalse(self.run().document["active_field"]["automatic_selection_performed"])

    def test_physical_estop_independent(self) -> None:
        self.assertTrue(self.run().document["safety"]["physical_estop_independent"])

    def test_database_outside_repository(self) -> None:
        self.assertTrue(self.run().document["database"]["database_outside_repository"])

    def test_repository_inventory_unchanged(self) -> None:
        before = sorted(path.relative_to(self.repository) for path in self.repository.rglob("*"))
        self.run()
        after = sorted(path.relative_to(self.repository) for path in self.repository.rglob("*"))
        self.assertEqual(after, before)

    def test_invalid_session_version(self) -> None:
        document = copy.deepcopy(self.example)
        document["session_version"] = 2
        self.assert_validation_failure(document, "FIELD_SESSION_INVALID")

    def test_duplicate_json_key(self) -> None:
        self.session_path.write_text('{"session_version":1,"session_version":1}', encoding="utf-8")
        self.assertEqual(self.run().exit_code, 3)

    def test_non_finite_json(self) -> None:
        self.session_path.write_text('{"session_version":NaN}', encoding="utf-8")
        self.assertEqual(self.run().exit_code, 3)

    def test_reversed_tick(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][1]["logical_tick"] = 0
        self.assert_validation_failure(document, "FIELD_SESSION_TICK_REVERSED")

    def test_unknown_operation(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["operation_type"] = "UNKNOWN"
        self.assert_validation_failure(document, "FIELD_OPERATION_UNKNOWN")

    def test_duplicate_field_id(self) -> None:
        self.run()
        operation = copy.deepcopy(self.example["operations"][0])
        operation["operation_id"] = "OP-ST005-OTHER-001"
        self.write_session(self.single_session(operation, "DUPLICATE-FIELD"))
        self.assertIn("FIELD_ALREADY_EXISTS", self.codes(self.run()))

    def test_missing_required_reference(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["references"] = document["operations"][0]["payload"]["references"][:-1]
        self.assert_validation_failure(document, "FIELD_REFERENCE_REQUIRED_MISSING")

    def test_duplicate_reference_id_in_profile(self) -> None:
        document = copy.deepcopy(self.example)
        refs = document["operations"][0]["payload"]["references"]
        refs[1]["reference_id"] = refs[0]["reference_id"]
        self.assert_validation_failure(document, "FIELD_REFERENCE_DUPLICATE")

    def test_duplicate_reference_id_database(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][1]["payload"]["references"][0]["reference_id"] = document["operations"][0]["payload"]["references"][0]["reference_id"]
        self.write_session(document)
        self.assertIn("FIELD_REFERENCE_DUPLICATE", self.codes(self.run()))

    def test_invalid_reference_type(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["references"][0]["reference_type"] = "GPS"
        self.assert_validation_failure(document, "FIELD_PROFILE_INVALID")

    def test_invalid_local_reference(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["references"][0]["location_reference"] = "field-1-entry"
        self.assert_validation_failure(document, "FIELD_LOCATION_REFERENCE_INVALID")

    def test_apparent_coordinate_value(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["references"][0]["location_reference"] = "35.000,139.000"
        self.assert_validation_failure(document, "FIELD_LOCATION_REFERENCE_INVALID")

    def test_duplicate_zone_id(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][1]["payload"]["no_go_zones"][0]["zone_id"] = document["operations"][0]["payload"]["no_go_zones"][0]["zone_id"]
        self.write_session(document)
        self.assertIn("FIELD_REFERENCE_DUPLICATE", self.codes(self.run()))

    def test_zone_boundary_fewer_than_three(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["no_go_zones"][0]["boundary"] = ["local-zone-ref:a", "local-zone-ref:b"]
        self.assert_validation_failure(document, "FIELD_ZONE_BOUNDARY_INVALID")

    def test_duplicate_boundary_reference(self) -> None:
        document = copy.deepcopy(self.example)
        boundary = document["operations"][0]["payload"]["no_go_zones"][0]["boundary"]
        boundary[1] = boundary[0]
        self.assert_validation_failure(document, "FIELD_ZONE_BOUNDARY_INVALID")

    def test_unknown_reason_code(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["no_go_zones"][0]["reason_code"] = "UNKNOWN"
        self.assert_validation_failure(document, "FIELD_PROFILE_INVALID")

    def test_field_count_limit_constant(self) -> None:
        self.run()
        connection = sqlite3.connect(self.arguments.database)
        try:
            for index in range(62):
                field_id = f"FIELD-LIMIT-{index:03d}"
                connection.execute(
                    "INSERT INTO field_profiles VALUES (?, ?, 1, 1, ?, '{}', ?)",
                    (field_id, "Limit field", f"LOCAL-FRAME-LIMIT-{index:03d}", "0" * 64),
                )
            connection.commit()
        finally:
            connection.close()
        operation = copy.deepcopy(self.example["operations"][0])
        operation["operation_id"] = "OP-ST005-FIELD-LIMIT"
        operation["payload"]["field_id"] = "FIELD-DEMO-LIMIT"
        self.write_session(self.single_session(operation, "FIELD-LIMIT"))
        self.assertIn("FIELD_PROFILE_INVALID", self.codes(self.run()))

    def test_reference_count_limit(self) -> None:
        document = copy.deepcopy(self.example)
        item = copy.deepcopy(document["operations"][0]["payload"]["references"][0])
        refs = []
        for index in range(33):
            candidate = copy.deepcopy(item)
            candidate["reference_id"] = f"REF-LIMIT-{index:03d}"
            refs.append(candidate)
        document["operations"][0]["payload"]["references"] = refs
        self.assert_validation_failure(document, "FIELD_PROFILE_INVALID")

    def test_zone_count_limit(self) -> None:
        document = copy.deepcopy(self.example)
        zone = copy.deepcopy(document["operations"][0]["payload"]["no_go_zones"][0])
        zones = []
        for index in range(33):
            candidate = copy.deepcopy(zone)
            candidate["zone_id"] = f"ZONE-LIMIT-{index:03d}"
            zones.append(candidate)
        document["operations"][0]["payload"]["no_go_zones"] = zones
        self.assert_validation_failure(document, "FIELD_PROFILE_INVALID")

    def test_boundary_count_limit(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["no_go_zones"][0]["boundary"] = [f"local-zone-ref:limit-{index}" for index in range(65)]
        self.assert_validation_failure(document, "FIELD_ZONE_BOUNDARY_INVALID")

    def test_operation_count_limit(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"] = [copy.deepcopy(document["operations"][3]) for _ in range(257)]
        self.assert_validation_failure(document, "FIELD_SESSION_INVALID")

    def test_revision_skip(self) -> None:
        document = self.revision_session(0, new_revision=3)
        self.assert_validation_failure(document, "FIELD_REVISION_SEQUENCE_INVALID")

    def test_expected_revision_conflict(self) -> None:
        self.run()
        self.write_session(self.revision_session(0, expected_revision=2, new_revision=3))
        self.assertIn("FIELD_REVISION_CONFLICT", self.codes(self.run()))

    def test_revision_without_approval(self) -> None:
        self.run()
        self.write_session(self.revision_session(0, operator_approved=False))
        self.assertIn("FIELD_OPERATOR_APPROVAL_REQUIRED", self.codes(self.run()))

    def test_active_revision_rover_running(self) -> None:
        self.run()
        self.write_session(self.revision_session(0, all_rovers_stopped=False))
        self.assertIn("FIELD_ROVERS_NOT_STOPPED", self.codes(self.run()))

    def test_active_revision_with_mission(self) -> None:
        self.run()
        self.write_session(self.revision_session(0, active_mission_count=1))
        self.assertIn("FIELD_ACTIVE_MISSION_PRESENT", self.codes(self.run()))

    def test_active_revision_during_charging(self) -> None:
        self.run()
        self.write_session(self.revision_session(0, charging_transition_count=1))
        self.assertIn("FIELD_CHARGING_TRANSITION_ACTIVE", self.codes(self.run()))

    def test_select_unknown_field(self) -> None:
        self.run()
        self.write_session(self.switch_session(target_field_id="FIELD-DEMO-999"))
        self.assertIn("FIELD_NOT_FOUND", self.codes(self.run()))

    def test_select_disabled_field(self) -> None:
        self.run()
        self.write_session(self.revision_session(1, enabled=False))
        self.run()
        self.write_session(self.switch_session())
        self.assertIn("FIELD_DISABLED", self.codes(self.run()))

    def test_select_without_approval(self) -> None:
        self.run()
        self.write_session(self.switch_session(operator_approved=False))
        self.assertIn("FIELD_OPERATOR_APPROVAL_REQUIRED", self.codes(self.run()))

    def test_select_rover_running(self) -> None:
        self.run()
        self.write_session(self.switch_session(all_rovers_stopped=False))
        self.assertIn("FIELD_ROVERS_NOT_STOPPED", self.codes(self.run()))

    def test_select_active_mission(self) -> None:
        self.run()
        self.write_session(self.switch_session(active_mission_count=1))
        self.assertIn("FIELD_ACTIVE_MISSION_PRESENT", self.codes(self.run()))

    def test_select_charging_transition(self) -> None:
        self.run()
        self.write_session(self.switch_session(charging_transition_count=1))
        self.assertIn("FIELD_CHARGING_TRANSITION_ACTIVE", self.codes(self.run()))

    def test_database_inside_repository(self) -> None:
        arguments = FIELD.FieldArguments(self.repository, self.repository / "field_profiles.db", self.session_path, self.arguments.json_report, self.arguments.text_report)
        with self.assertRaises(FIELD.FieldFailure) as caught:
            FIELD.validate_arguments(arguments)
        self.assertEqual(caught.exception.code, "FIELD_DATABASE_PATH_INSIDE_REPOSITORY")

    def test_report_inside_repository(self) -> None:
        arguments = FIELD.FieldArguments(self.repository, self.arguments.database, self.session_path, self.repository / "report.json", self.arguments.text_report)
        with self.assertRaises(FIELD.FieldFailure) as caught:
            FIELD.validate_arguments(arguments)
        self.assertEqual(caught.exception.code, "FIELD_REPORT_PATH_INSIDE_REPOSITORY")

    def test_missing_database_parent(self) -> None:
        arguments = FIELD.FieldArguments(self.repository, self.root / "missing" / "field_profiles.db", self.session_path, self.arguments.json_report, self.arguments.text_report)
        with self.assertRaises(FIELD.FieldFailure) as caught:
            FIELD.validate_arguments(arguments)
        self.assertEqual(caught.exception.code, "FIELD_DATABASE_PARENT_INVALID")

    def test_missing_report_parent(self) -> None:
        arguments = FIELD.FieldArguments(self.repository, self.arguments.database, self.session_path, self.root / "missing" / "report.json", self.arguments.text_report)
        with self.assertRaises(FIELD.FieldFailure) as caught:
            FIELD.validate_arguments(arguments)
        self.assertEqual(caught.exception.code, "FIELD_REPORT_PARENT_INVALID")

    def test_schema_version_two(self) -> None:
        connection, _configuration = FIELD.open_database(self.arguments.database)
        try:
            connection.executescript(SQL_PATH.read_text(encoding="utf-8"))
            connection.executemany("INSERT INTO field_schema_metadata VALUES (?, ?)", (("schema_version", "2"), ("application_phase", "ST-005")))
        finally:
            connection.close()
        self.assertIn("FIELD_SCHEMA_VERSION_UNSUPPORTED", self.codes(self.run()))

    def test_operation_id_changed_content(self) -> None:
        self.run()
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["display_name"] = "Changed"
        self.write_session(document)
        report = self.run()
        self.assertIn("FIELD_IDEMPOTENCY_CONFLICT", self.codes(report))

    def test_injected_failure_rollback(self) -> None:
        report = self.run(fail_after_operation_index=0)
        self.assertTrue(report.document["transaction"]["rolled_back"])

    def test_no_partial_profile(self) -> None:
        self.run(fail_after_operation_index=0)
        self.assertEqual(self.query("SELECT COUNT(*) FROM field_profiles")[0][0], 0)

    def test_no_partial_references(self) -> None:
        self.run(fail_after_operation_index=0)
        self.assertEqual(self.query("SELECT COUNT(*) FROM field_references")[0][0], 0)

    def test_no_partial_zones(self) -> None:
        self.run(fail_after_operation_index=0)
        self.assertEqual(self.query("SELECT COUNT(*) FROM field_no_go_zones")[0][0], 0)

    def test_active_state_unchanged_after_rollback(self) -> None:
        self.run()
        before = self.query("SELECT * FROM field_active_state")
        self.write_session(self.switch_session())
        self.run(fail_after_operation_index=0)
        self.assertEqual(self.query("SELECT * FROM field_active_state"), before)

    def test_prior_hash_unchanged_after_rollback(self) -> None:
        self.run()
        before = self.canonical_hash()
        self.write_session(self.switch_session())
        self.run(fail_after_operation_index=0)
        self.assertEqual(self.canonical_hash(), before)

    def test_integrity_after_rollback(self) -> None:
        self.run(fail_after_operation_index=0)
        connection, _configuration = FIELD.open_database(self.arguments.database)
        try:
            self.assertEqual(FIELD.integrity_check(connection), "OK")
        finally:
            connection.close()

    def test_report_write_failure(self) -> None:
        arguments = FIELD.FieldArguments(self.repository, self.arguments.database, self.session_path, self.report_dir, self.arguments.text_report)
        self.assertEqual(self.run(arguments=arguments, write_reports=True).exit_code, 7)

    def test_unexpected_internal_error(self) -> None:
        with mock.patch.object(FIELD, "run_field_profile_session", side_effect=RuntimeError("private")):
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                code = FIELD.main(["--repository-root", str(self.repository), "--database", str(self.arguments.database), "--session", str(self.session_path), "--json-report", str(self.arguments.json_report), "--text-report", str(self.arguments.text_report)])
        self.assertEqual(code, 7)
        self.assertNotIn("private", stderr.getvalue())

    def test_source_standard_library_only(self) -> None:
        tree = ast.parse(IMPLEMENTATION_PATH.read_text(encoding="utf-8"))
        imports = {node.names[0].name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)}
        imports |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        self.assertTrue(imports <= {"__future__", "argparse", "dataclasses", "hashlib", "json", "math", "os", "pathlib", "re", "sqlite3", "sys", "typing"})

    def test_forbidden_imports_absent(self) -> None:
        source = IMPLEMENTATION_PATH.read_text(encoding="utf-8")
        for name in ("socket", "requests", "urllib", "subprocess", "serial", "gpiod", "SQLAlchemy"):
            self.assertNotRegex(source, rf"(?m)^\s*(?:from|import)\s+{re.escape(name)}\b")

    def test_sql_forbidden_statements_absent(self) -> None:
        sql = SQL_PATH.read_text(encoding="utf-8").upper()
        for statement in ("DROP ", "VACUUM", "DELETE "):
            self.assertNotIn(statement, sql)

    def test_report_has_no_timestamp(self) -> None:
        self.assertNotIn("timestamp", FIELD.render_json_report(self.run()).lower())

    def test_report_has_no_absolute_path(self) -> None:
        self.assertNotIn(str(self.root), FIELD.render_json_report(self.run()))

    def test_diagnostic_sort_order(self) -> None:
        report = self.run(fail_after_operation_index=0)
        keys = [(item["component"], item["code"], item["operation_id"], item["message"]) for item in report.document["diagnostics"]]
        self.assertEqual(keys, sorted(keys))

    def test_boolean_not_integer(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["logical_tick"] = True
        self.assert_validation_failure(document, "FIELD_SESSION_INVALID")

    def test_profile_revision_must_be_one(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"][0]["payload"]["profile_revision"] = 2
        self.assert_validation_failure(document, "FIELD_REVISION_SEQUENCE_INVALID")

    def test_active_row_maximum_one(self) -> None:
        self.run()
        self.assertEqual(self.query("SELECT COUNT(*) FROM field_active_state")[0][0], 1)

    def test_active_field_not_auto_selected_without_set(self) -> None:
        document = copy.deepcopy(self.example)
        document["operations"] = document["operations"][:2]
        self.write_session(document)
        report = self.run()
        self.assertEqual(report.document["active_field"]["active_field_id"], "")

    def test_verify_integrity_operation_processed(self) -> None:
        self.assertEqual(self.run().document["operations"]["processed_count"], 4)

    def test_atomic_session_true(self) -> None:
        self.assertTrue(self.run().document["transaction"]["atomic_session"])

    def test_migration_false(self) -> None:
        self.assertFalse(self.run().document["schema"]["migration_performed"])

    def test_database_file_hash_not_reported(self) -> None:
        text = FIELD.render_json_report(self.run())
        self.assertNotIn("database_sha256", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
