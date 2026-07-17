"""Standard-library tests for ST-006 offline rover registry."""

from __future__ import annotations

import ast
import copy
from contextlib import redirect_stderr
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
IMPLEMENTATION_PATH = ROOT / "station" / "rover_registry.py"
SQL_PATH = ROOT / "storage" / "rover_registry_schema_v1.sql"
SESSION_SCHEMA_PATH = ROOT / "schemas" / "rover-registry-session.schema.json"
REPORT_SCHEMA_PATH = ROOT / "schemas" / "rover-registry-report.schema.json"
EXAMPLE_PATH = ROOT / "config_examples" / "rover-registry-session.example.json"

SPEC = importlib.util.spec_from_file_location("station_rover_registry", IMPLEMENTATION_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load rover registry module.")
REGISTRY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REGISTRY
SPEC.loader.exec_module(REGISTRY)


class RoverRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="st006-test-")
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.database_dir = self.root / "database"
        self.report_dir = self.root / "reports"
        self.session_dir = self.root / "sessions"
        for path in (self.repository, self.database_dir, self.report_dir, self.session_dir):
            path.mkdir()
        schema_copy = self.repository / "software" / "station_control" / "storage" / "rover_registry_schema_v1.sql"
        schema_copy.parent.mkdir(parents=True)
        shutil.copy2(SQL_PATH, schema_copy)
        self.example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        self.session_path = self.session_dir / "session.json"
        self.write_session(self.example)
        self.arguments = self.make_arguments("rover_registry.db", "report")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_arguments(self, database_name: str, report_stem: str):
        return REGISTRY.RegistryArguments(
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
        if result is not None and not isinstance(result, REGISTRY.RegistryArguments):
            return super().run(result)
        selected = result if isinstance(result, REGISTRY.RegistryArguments) else arguments
        return REGISTRY.run_registry_session(selected or self.arguments, **kwargs)

    def query(self, sql: str, parameters: tuple[object, ...] = (), database: Path | None = None):
        connection = sqlite3.connect(database or self.arguments.database)
        try:
            return connection.execute(sql, parameters).fetchall()
        finally:
            connection.close()

    def row_counts(self, database: Path | None = None) -> tuple[int, ...]:
        connection = sqlite3.connect(database or self.arguments.database)
        try:
            return tuple(
                int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table, _columns, _key in REGISTRY.TABLE_DEFINITIONS
            )
        finally:
            connection.close()

    def canonical_hash(self, database: Path | None = None) -> str:
        connection, _configuration = REGISTRY.open_database(database or self.arguments.database)
        try:
            return REGISTRY.canonical_state_sha256(REGISTRY.canonical_database_state(connection))
        finally:
            connection.close()

    def codes(self, report) -> set[str]:
        return {item["code"] for item in report.document["diagnostics"]}

    def assert_validation_failure(self, document: object, code: str) -> None:
        with self.assertRaises(REGISTRY.RegistryFailure) as caught:
            REGISTRY.validate_session(document)
        self.assertEqual(caught.exception.code, code)

    def single_session(self, operation: dict[str, object], suffix: str = "CUSTOM") -> dict[str, object]:
        return {"session_version": 1, "session_id": f"SESSION-ST006-{suffix}", "operations": [operation]}

    def state_session(self, rover_id: str, target: str, number: int = 101, **changes: object):
        operation = {
            "operation_id": f"OP-ST006-{number:03d}",
            "logical_tick": 20,
            "operation_type": "SET_REGISTRATION_STATE",
            "payload": {
                "rover_id": rover_id,
                "target_state": target,
                "operator_approved": True,
                "rover_confirmed_stopped": True,
                "active_mission_count": 0,
                "charging_transition_count": 0,
                "reason": "operator state test",
            },
        }
        operation["payload"].update(changes)
        return self.single_session(operation, "STATE")

    def revision_session(self, rover_index: int = 1, number: int = 110, **changes: object):
        source = copy.deepcopy(self.example["operations"][rover_index]["payload"])
        operation = {
            "operation_id": f"OP-ST006-{number:03d}",
            "logical_tick": 20,
            "operation_type": "REVISE_ROVER",
            "payload": {
                "rover_id": source["rover_id"],
                "expected_revision": 1,
                "new_revision": 2,
                "display_name": source["display_name"] + " revised",
                "role": source["role"],
                "enabled": source["enabled"],
                "hardware_class": source["hardware_class"],
                "allowed_fields": source["allowed_fields"],
                "allowed_units": source["allowed_units"],
                "operator_approved": True,
                "rover_confirmed_stopped": True,
                "active_mission_count": 0,
                "charging_transition_count": 0,
            },
        }
        operation["payload"].update(changes)
        return self.single_session(operation, "REVISION")

    def authorization_session(self, number: int = 120, rover_index: int = 0, **changes: object):
        base = copy.deepcopy(self.example["operations"][7]["payload"])
        if rover_index == 1:
            base.update({"rover_id": "ROVER-DEMO-002", "requested_unit_id": "UNIT-DEMO-WEED"})
        elif rover_index == 2:
            base.update({"rover_id": "ROVER-DEMO-003", "active_field_id": "FIELD-DEMO-002", "requested_field_id": "FIELD-DEMO-002", "requested_unit_id": "UNIT-DEMO-WEED"})
        base["authorization_id"] = f"AUTH-ST006-{number:03d}"
        base["mission_id"] = f"MISSION-DEMO-{number:03d}"
        base.update(changes)
        operation = {
            "operation_id": f"OP-ST006-{number:03d}",
            "logical_tick": 20,
            "operation_type": "AUTHORIZE_ASSIGNMENT",
            "payload": base,
        }
        return self.single_session(operation, "AUTHORIZATION")

    def denial(self, expected: str, rover_index: int = 0, **changes: object) -> list[str]:
        self.run()
        self.write_session(self.authorization_session(120, rover_index, **changes))
        report = self.run()
        self.assertEqual(report.exit_code, 0)
        row = self.query("SELECT decision, reason_codes_json FROM rover_authorization_decisions WHERE authorization_id='AUTH-ST006-120'")[0]
        self.assertEqual(row[0], "DENIED")
        reasons = json.loads(row[1])
        self.assertIn(expected, reasons)
        return reasons

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
        self.assertEqual(strict, {item[0] for item in REGISTRY.TABLE_DEFINITIONS})

    def test_exact_table_count(self) -> None:
        self.run()
        self.assertEqual(len(self.query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")), 6)

    def test_schema_metadata_version(self) -> None:
        self.run()
        self.assertIn(("schema_version", "1"), self.query("SELECT * FROM rover_schema_metadata"))

    def test_application_phase(self) -> None:
        self.run()
        self.assertIn(("application_phase", "ST-006"), self.query("SELECT * FROM rover_schema_metadata"))

    def test_wal(self) -> None:
        self.assertEqual(self.run().document["database"]["journal_mode"], "wal")

    def test_synchronous_full(self) -> None:
        self.assertEqual(self.run().document["database"]["synchronous"], "FULL")

    def test_foreign_keys(self) -> None:
        self.assertTrue(self.run().document["database"]["foreign_keys"])

    def test_busy_timeout(self) -> None:
        self.assertEqual(self.run().document["database"]["busy_timeout_ms"], 5000)

    def test_no_triggers(self) -> None:
        self.run(); self.assertEqual(self.query("SELECT name FROM sqlite_master WHERE type='trigger'"), [])

    def test_no_views(self) -> None:
        self.run(); self.assertEqual(self.query("SELECT name FROM sqlite_master WHERE type='view'"), [])

    def test_no_manual_indexes(self) -> None:
        self.run(); self.assertEqual(self.query("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex_%'"), [])

    def test_positive_session_parse(self) -> None:
        self.assertEqual(REGISTRY.validate_session(copy.deepcopy(self.example))["session_version"], 1)

    def test_ten_operation_input_order(self) -> None:
        parsed = REGISTRY.validate_session(copy.deepcopy(self.example))
        self.assertEqual([item["operation_id"] for item in parsed["operations"]], [f"OP-ST006-{i:03d}" for i in range(1, 11)])

    def test_three_rover_registration(self) -> None:
        self.assertEqual(self.run().document["rovers"]["total_count"], 3)

    def test_initial_pending_state(self) -> None:
        document = copy.deepcopy(self.example); document["operations"] = document["operations"][:3]; self.write_session(document)
        self.assertEqual(self.run().document["rovers"]["pending_count"], 3)

    def test_two_registered_rovers(self) -> None:
        self.assertEqual(self.run().document["rovers"]["registered_count"], 2)

    def test_one_suspended_rover(self) -> None:
        self.assertEqual(self.run().document["rovers"]["suspended_count"], 1)

    def test_four_field_permissions(self) -> None:
        self.assertEqual(self.run().document["field_permissions"]["total_count"], 4)

    def test_three_unit_permissions(self) -> None:
        self.assertEqual(self.run().document["unit_permissions"]["total_count"], 3)

    def test_valid_authorization(self) -> None:
        self.assertEqual(self.run().document["authorization_decisions"]["authorized_count"], 1)

    def test_suspended_authorization_denied(self) -> None:
        self.assertEqual(self.run().document["authorization_decisions"]["denied_count"], 1)

    def test_authorized_reason(self) -> None:
        self.run(); self.assertEqual(self.query("SELECT reason_codes_json FROM rover_authorization_decisions WHERE authorization_id='AUTH-ST006-001'")[0][0], '["AUTHORIZED"]')

    def test_suspended_reason(self) -> None:
        self.run(); self.assertEqual(json.loads(self.query("SELECT reason_codes_json FROM rover_authorization_decisions WHERE authorization_id='AUTH-ST006-002'")[0][0]), ["ROVER_NOT_REGISTERED"])

    def test_context_canonical_json(self) -> None:
        self.run(); value = self.query("SELECT context_json FROM rover_authorization_decisions ORDER BY authorization_id")[0][0]; self.assertNotIn(": ", value)

    def test_context_sha256(self) -> None:
        self.run(); value, digest = self.query("SELECT context_json, context_sha256 FROM rover_authorization_decisions ORDER BY authorization_id")[0]; self.assertEqual(hashlib.sha256(value.encode()).hexdigest(), digest)

    def test_profile_canonical_json(self) -> None:
        self.run(); value = self.query("SELECT profile_json FROM rover_registry ORDER BY rover_id")[0][0]; self.assertNotIn(": ", value)

    def test_profile_sha256(self) -> None:
        self.run(); value, digest = self.query("SELECT profile_json, profile_sha256 FROM rover_registry ORDER BY rover_id")[0]; self.assertEqual(hashlib.sha256(value.encode()).hexdigest(), digest)

    def test_direct_output_authority_false(self) -> None:
        self.assertFalse(self.run().document["authorization_decisions"]["direct_output_authority"])

    def test_decision_rows_direct_authority_zero(self) -> None:
        self.run(); self.assertEqual(self.query("SELECT DISTINCT direct_output_authority FROM rover_authorization_decisions"), [(0,)])

    def test_integrity_ok(self) -> None:
        self.assertEqual(self.run().document["integrity"]["result"], "OK")

    def test_transaction_commit(self) -> None:
        self.assertTrue(self.run().document["transaction"]["committed"])

    def test_reopen(self) -> None:
        self.assertTrue(self.run().document["database"]["reopened"])

    def test_persistence(self) -> None:
        self.run(); self.assertEqual(len(self.query("SELECT rover_id FROM rover_registry")), 3)

    def test_canonical_root_order(self) -> None:
        self.run(); connection, _ = REGISTRY.open_database(self.arguments.database)
        try: self.assertEqual(tuple(REGISTRY.canonical_database_state(connection)), tuple(item[0] for item in REGISTRY.TABLE_DEFINITIONS))
        finally: connection.close()

    def test_canonical_rover_row_order(self) -> None:
        self.run(); connection, _ = REGISTRY.open_database(self.arguments.database)
        try: rows = REGISTRY.canonical_database_state(connection)["rover_registry"]
        finally: connection.close()
        self.assertEqual([row["rover_id"] for row in rows], sorted(row["rover_id"] for row in rows))

    def test_canonical_permission_row_order(self) -> None:
        self.run(); connection, _ = REGISTRY.open_database(self.arguments.database)
        try: rows = REGISTRY.canonical_database_state(connection)["rover_allowed_fields"]
        finally: connection.close()
        keys = [(row["rover_id"], row["field_id"]) for row in rows]; self.assertEqual(keys, sorted(keys))

    def test_canonical_sha256_format(self) -> None:
        self.assertRegex(self.run().document["canonical_state_sha256"], r"^[0-9a-f]{64}$")

    def test_report_root_order(self) -> None:
        expected = ("report_version", "phase", "session_id", "result", "database", "transaction", "schema", "operations", "rovers", "field_permissions", "unit_permissions", "authorization_decisions", "integrity", "idempotency", "safety", "summary", "diagnostics", "canonical_state_sha256", "exit_code")
        self.assertEqual(tuple(self.run().document), expected)

    def test_rover_nested_order(self) -> None:
        self.assertEqual(tuple(self.run().document["rovers"]), ("created_count", "revised_count", "state_changed_count", "pending_count", "registered_count", "suspended_count", "revoked_count", "enabled_count", "disabled_count", "total_count"))

    def test_safety_nested_order(self) -> None:
        self.assertEqual(tuple(self.run().document["safety"])[0], "offline_only")

    def test_text_property_order(self) -> None:
        self.assertTrue(REGISTRY.render_text_report(self.run()).startswith("report_version=1\nphase=ST-006\n"))

    def test_session_schema_draft(self) -> None:
        self.assertEqual(json.loads(SESSION_SCHEMA_PATH.read_text(encoding="utf-8"))["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_report_schema_draft(self) -> None:
        self.assertEqual(json.loads(REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_fresh_json_identical(self) -> None:
        a = self.run(arguments=self.make_arguments("a.db", "a")); b = self.run(arguments=self.make_arguments("b.db", "b")); self.assertEqual(REGISTRY.render_json_report(a), REGISTRY.render_json_report(b))

    def test_fresh_text_identical(self) -> None:
        a = self.run(arguments=self.make_arguments("a.db", "a")); b = self.run(arguments=self.make_arguments("b.db", "b")); self.assertEqual(REGISTRY.render_text_report(a), REGISTRY.render_text_report(b))

    def test_fresh_canonical_identical(self) -> None:
        a = self.run(arguments=self.make_arguments("a.db", "a")); b = self.run(arguments=self.make_arguments("b.db", "b")); self.assertEqual(a.document["canonical_state_sha256"], b.document["canonical_state_sha256"])

    def test_same_session_second_pass(self) -> None:
        self.run(); self.assertEqual(self.run().exit_code, 0)

    def test_second_run_applied_zero(self) -> None:
        self.run(); self.assertEqual(self.run().document["operations"]["applied_count"], 0)

    def test_second_run_duplicate_ten(self) -> None:
        self.run(); self.assertEqual(self.run().document["operations"]["duplicate_noop_count"], 10)

    def test_second_run_rows_unchanged(self) -> None:
        self.run(); before = self.row_counts(); self.run(); self.assertEqual(self.row_counts(), before)

    def test_second_run_hash_unchanged(self) -> None:
        first = self.run().document["canonical_state_sha256"]; second = self.run().document["canonical_state_sha256"]; self.assertEqual(second, first)

    def test_safe_revision(self) -> None:
        self.run(); self.write_session(self.revision_session(1)); self.assertEqual(self.run().document["rovers"]["revised_count"], 1)

    def test_revision_two_persisted(self) -> None:
        self.run(); self.write_session(self.revision_session(1)); self.run(); self.assertEqual(self.query("SELECT profile_revision FROM rover_registry WHERE rover_id='ROVER-DEMO-002'")[0][0], 2)

    def test_revision_permission_replacement(self) -> None:
        self.run(); self.write_session(self.revision_session(1, allowed_fields=["FIELD-DEMO-002"], allowed_units=["UNIT-DEMO-SCOUT"])); self.run(); self.assertEqual(self.query("SELECT field_id FROM rover_allowed_fields WHERE rover_id='ROVER-DEMO-002' AND enabled=1"), [("FIELD-DEMO-002",)])

    def test_safe_state_transition(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-003", "REGISTERED")); self.assertEqual(self.run().document["rovers"]["registered_count"], 3)

    def test_same_state_noop(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-001", "REGISTERED")); report = self.run(); self.assertEqual(report.document["rovers"]["state_changed_count"], 0)

    def test_suspended_to_registered(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-003", "REGISTERED")); self.run(); self.assertEqual(self.query("SELECT registration_state FROM rover_registry WHERE rover_id='ROVER-DEMO-003'")[0][0], "REGISTERED")

    def test_registered_to_suspended(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-002", "SUSPENDED")); self.run(); self.assertEqual(self.query("SELECT registration_state FROM rover_registry WHERE rover_id='ROVER-DEMO-002'")[0][0], "SUSPENDED")

    def test_revoke_terminal(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-002", "REVOKED")); self.run(); self.write_session(self.state_session("ROVER-DEMO-002", "REGISTERED", 102)); self.assertIn("ROVER_STATE_TRANSITION_INVALID", self.codes(self.run()))

    def test_denial_rover_disabled(self) -> None:
        self.run(); self.write_session(self.revision_session(1, enabled=False)); self.run(); self.write_session(self.authorization_session(120, 1)); report = self.run(); self.assertEqual(json.loads(self.query("SELECT reason_codes_json FROM rover_authorization_decisions WHERE authorization_id='AUTH-ST006-120'")[0][0]), ["ROVER_DISABLED"])

    def test_denial_pending(self) -> None:
        document = copy.deepcopy(self.example); document["operations"] = document["operations"][:1]; self.write_session(document); self.run(); self.write_session(self.authorization_session(120)); self.assertIn("ROVER_NOT_REGISTERED", json.loads(self.query_after_run_reason()))

    def query_after_run_reason(self) -> str:
        self.run(); return self.query("SELECT reason_codes_json FROM rover_authorization_decisions WHERE authorization_id='AUTH-ST006-120'")[0][0]

    def test_denial_suspended(self) -> None:
        self.assertEqual(self.denial("ROVER_NOT_REGISTERED", 2), ["ROVER_NOT_REGISTERED"])

    def test_denial_revoked(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-002", "REVOKED")); self.run(); self.write_session(self.authorization_session(120, 1)); self.assertIn("ROVER_NOT_REGISTERED", json.loads(self.query_after_run_reason()))

    def test_denial_field_not_allowed(self) -> None:
        self.assertIn("FIELD_NOT_ALLOWED", self.denial("FIELD_NOT_ALLOWED", 1, active_field_id="FIELD-DEMO-002", requested_field_id="FIELD-DEMO-002"))

    def test_denial_unit_not_allowed(self) -> None:
        self.assertEqual(self.denial("UNIT_NOT_ALLOWED", 1, requested_unit_id="UNIT-DEMO-SCOUT"), ["UNIT_NOT_ALLOWED"])

    def test_denial_active_field_mismatch(self) -> None:
        self.assertEqual(self.denial("ACTIVE_FIELD_MISMATCH", 1, active_field_id="FIELD-DEMO-002"), ["ACTIVE_FIELD_MISMATCH"])

    def test_denial_operator_approval(self) -> None:
        self.assertEqual(self.denial("OPERATOR_APPROVAL_REQUIRED", operator_approved=False), ["OPERATOR_APPROVAL_REQUIRED"])

    def test_denial_mission_state(self) -> None:
        self.assertEqual(self.denial("MISSION_STATE_NOT_QUEUED", mission_state="DRAFT"), ["MISSION_STATE_NOT_QUEUED"])

    def test_denial_rover_not_stopped(self) -> None:
        self.assertEqual(self.denial("ROVER_NOT_STOPPED", rover_reported_stopped=False), ["ROVER_NOT_STOPPED"])

    def test_denial_communication(self) -> None:
        self.assertEqual(self.denial("COMMUNICATION_UNAVAILABLE", communication_available=False), ["COMMUNICATION_UNAVAILABLE"])

    def test_denial_fault(self) -> None:
        self.assertEqual(self.denial("FAULT_PRESENT", fault_present=True), ["FAULT_PRESENT"])

    def test_denial_battery_19(self) -> None:
        self.assertEqual(self.denial("BATTERY_BELOW_RESERVE", battery_percentage=19), ["BATTERY_BELOW_RESERVE"])

    def test_denial_battery_zero(self) -> None:
        self.assertEqual(self.denial("BATTERY_BELOW_RESERVE", battery_percentage=0), ["BATTERY_BELOW_RESERVE"])

    def test_denial_estop(self) -> None:
        self.assertEqual(self.denial("PHYSICAL_ESTOP_ASSERTED", physical_estop_asserted=True), ["PHYSICAL_ESTOP_ASSERTED"])

    def test_multiple_denial_reasons(self) -> None:
        reasons = self.denial("OPERATOR_APPROVAL_REQUIRED", operator_approved=False, communication_available=False, battery_percentage=0); self.assertEqual(len(reasons), 3)

    def test_denial_reason_ordering(self) -> None:
        reasons = self.denial("ACTIVE_FIELD_MISMATCH", active_field_id="FIELD-DEMO-002", operator_approved=False, communication_available=False, battery_percentage=0); self.assertEqual(reasons, ["ACTIVE_FIELD_MISMATCH", "OPERATOR_APPROVAL_REQUIRED", "COMMUNICATION_UNAVAILABLE", "BATTERY_BELOW_RESERVE"])

    def test_denial_no_direct_output(self) -> None:
        self.denial("FAULT_PRESENT", fault_present=True); self.assertEqual(self.query("SELECT direct_output_authority FROM rover_authorization_decisions WHERE authorization_id='AUTH-ST006-120'")[0][0], 0)

    def test_denial_no_assignment(self) -> None:
        report_reasons = self.denial("FAULT_PRESENT", fault_present=True); self.assertIn("FAULT_PRESENT", report_reasons)

    def test_denial_no_arm(self) -> None:
        self.denial("PHYSICAL_ESTOP_ASSERTED", physical_estop_asserted=True); self.assertFalse(self.run().document["safety"]["actual_arm_performed"])

    def test_network_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["network_access_performed"])

    def test_gpio_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["gpio_access_performed"])

    def test_serial_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["serial_access_performed"])

    def test_hardware_output_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["hardware_output_performed"])

    def test_actual_assignment_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["actual_assignment_performed"])

    def test_actual_arm_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["actual_arm_performed"])

    def test_crypto_auth_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["cryptographic_authentication_performed"])

    def test_automatic_registration_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["automatic_registration_performed"])

    def test_automatic_state_transition_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["automatic_state_transition_performed"])

    def test_physical_estop_independent(self) -> None:
        self.assertTrue(self.run().document["safety"]["physical_estop_independent"])

    def test_repository_inventory_unchanged(self) -> None:
        before = sorted(path.relative_to(self.repository) for path in self.repository.rglob("*")); self.run(); after = sorted(path.relative_to(self.repository) for path in self.repository.rglob("*")); self.assertEqual(after, before)

    def test_repository_database_absent(self) -> None:
        self.run(); self.assertFalse(any(path.suffix == ".db" for path in self.repository.rglob("*")))

    def test_no_persistent_probe_file(self) -> None:
        self.run(); self.assertEqual([path for path in self.repository.rglob("*") if path.is_file()], [self.repository / "software/station_control/storage/rover_registry_schema_v1.sql"])

    def test_invalid_session_version(self) -> None:
        document = copy.deepcopy(self.example); document["session_version"] = 2; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_duplicate_json_key(self) -> None:
        self.session_path.write_text('{"session_version":1,"session_version":1}', encoding="utf-8"); self.assertEqual(self.run().exit_code, 3)

    def test_reversed_logical_tick(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][1]["logical_tick"] = -1; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_unknown_operation(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["operation_type"] = "UNKNOWN"; self.assert_validation_failure(document, "ROVER_OPERATION_UNKNOWN")

    def test_boolean_used_as_integer(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["logical_tick"] = True; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_invalid_rover_id(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["rover_id"] = "REAL-001"; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_invalid_field_id(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["allowed_fields"] = ["FIELD-REAL-001"]; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_invalid_unit_id(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["allowed_units"] = ["UNIT-REAL"]; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_invalid_mission_id(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][7]["payload"]["mission_id"] = "MISSION-REAL-001"; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_invalid_authorization_id(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][7]["payload"]["authorization_id"] = "AUTH-REAL-001"; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_invalid_operation_id(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["operation_id"] = "OP-REAL-001"; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_invalid_role(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["role"] = "ADMIN"; self.assert_validation_failure(document, "ROVER_PROFILE_INVALID")

    def test_invalid_state(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][3]["payload"]["target_state"] = "ACTIVE"; self.assert_validation_failure(document, "ROVER_PROFILE_INVALID")

    def test_invalid_hardware_class(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["hardware_class"] = "REAL"; self.assert_validation_failure(document, "ROVER_PROFILE_INVALID")

    def test_initial_state_not_pending(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["initial_state"] = "REGISTERED"; self.assert_validation_failure(document, "ROVER_PROFILE_INVALID")

    def test_profile_revision_not_one(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["profile_revision"] = 2; self.assert_validation_failure(document, "ROVER_REVISION_SEQUENCE_INVALID")

    def test_no_allowed_field(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["allowed_fields"] = []; self.assert_validation_failure(document, "ROVER_PROFILE_INVALID")

    def test_no_allowed_unit(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["allowed_units"] = []; self.assert_validation_failure(document, "ROVER_PROFILE_INVALID")

    def test_duplicate_field_permission(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["allowed_fields"] = ["FIELD-DEMO-001", "FIELD-DEMO-001"]; self.assert_validation_failure(document, "ROVER_FIELD_PERMISSION_DUPLICATE")

    def test_duplicate_unit_permission(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["allowed_units"] = ["UNIT-DEMO-SCOUT", "UNIT-DEMO-SCOUT"]; self.assert_validation_failure(document, "ROVER_UNIT_PERMISSION_DUPLICATE")

    def test_rover_count_limit(self) -> None:
        self.assertEqual(REGISTRY.MAX_ROVERS, 128)

    def test_field_permission_limit(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["allowed_fields"] = [f"FIELD-DEMO-{i:03d}" for i in range(65)]; self.assert_validation_failure(document, "ROVER_PROFILE_INVALID")

    def test_unit_permission_limit(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][0]["payload"]["allowed_units"] = [f"UNIT-DEMO-{i:03d}" for i in range(65)]; self.assert_validation_failure(document, "ROVER_PROFILE_INVALID")

    def test_operation_count_limit(self) -> None:
        document = copy.deepcopy(self.example); document["operations"] = [copy.deepcopy(document["operations"][9]) for _ in range(513)]; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_authorization_count_limit(self) -> None:
        document = copy.deepcopy(self.example); operation = copy.deepcopy(document["operations"][7]); document["operations"] = [copy.deepcopy(operation) for _ in range(257)]; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_duplicate_rover_different_operation(self) -> None:
        self.run(); operation = copy.deepcopy(self.example["operations"][0]); operation["operation_id"] = "OP-ST006-111"; self.write_session(self.single_session(operation, "DUPLICATE")); self.assertIn("ROVER_ALREADY_EXISTS", self.codes(self.run()))

    def test_revision_skip(self) -> None:
        self.assert_validation_failure(self.revision_session(1, new_revision=3), "ROVER_REVISION_SEQUENCE_INVALID")

    def test_expected_revision_conflict(self) -> None:
        self.run(); self.write_session(self.revision_session(1, expected_revision=2, new_revision=3)); self.assertIn("ROVER_REVISION_CONFLICT", self.codes(self.run()))

    def test_revision_without_approval(self) -> None:
        self.run(); self.write_session(self.revision_session(1, operator_approved=False)); self.assertIn("ROVER_OPERATOR_APPROVAL_REQUIRED", self.codes(self.run()))

    def test_revision_rover_not_stopped(self) -> None:
        self.run(); self.write_session(self.revision_session(1, rover_confirmed_stopped=False)); self.assertIn("ROVER_NOT_STOPPED", self.codes(self.run()))

    def test_revision_active_mission(self) -> None:
        self.run(); self.write_session(self.revision_session(1, active_mission_count=1)); self.assertIn("ROVER_ACTIVE_MISSION_PRESENT", self.codes(self.run()))

    def test_revision_charging_transition(self) -> None:
        self.run(); self.write_session(self.revision_session(1, charging_transition_count=1)); self.assertIn("ROVER_CHARGING_TRANSITION_ACTIVE", self.codes(self.run()))

    def test_invalid_state_transition(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-001", "PENDING")); self.assertIn("ROVER_STATE_TRANSITION_INVALID", self.codes(self.run()))

    def test_revoked_recovery_attempt(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-002", "REVOKED")); self.run(); self.write_session(self.state_session("ROVER-DEMO-002", "REGISTERED", 102)); self.assertIn("ROVER_STATE_TRANSITION_INVALID", self.codes(self.run()))

    def test_state_change_without_approval(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-002", "SUSPENDED", operator_approved=False)); self.assertIn("ROVER_OPERATOR_APPROVAL_REQUIRED", self.codes(self.run()))

    def test_state_change_while_moving(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-002", "SUSPENDED", rover_confirmed_stopped=False)); self.assertIn("ROVER_NOT_STOPPED", self.codes(self.run()))

    def test_state_change_active_mission(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-002", "SUSPENDED", active_mission_count=1)); self.assertIn("ROVER_ACTIVE_MISSION_PRESENT", self.codes(self.run()))

    def test_state_change_charging(self) -> None:
        self.run(); self.write_session(self.state_session("ROVER-DEMO-002", "SUSPENDED", charging_transition_count=1)); self.assertIn("ROVER_CHARGING_TRANSITION_ACTIVE", self.codes(self.run()))

    def test_unknown_rover_authorization(self) -> None:
        self.run(); self.write_session(self.authorization_session(120, rover_id="ROVER-DEMO-999")); self.assertIn("ROVER_NOT_FOUND", self.codes(self.run()))

    def test_duplicate_authorization_id(self) -> None:
        self.run(); self.write_session(self.authorization_session(120, authorization_id="AUTH-ST006-001")); self.assertIn("ROVER_AUTHORIZATION_ID_CONFLICT", self.codes(self.run()))

    def test_same_operation_changed_content(self) -> None:
        self.run(); document = copy.deepcopy(self.example); document["operations"][0]["payload"]["display_name"] = "Changed"; self.write_session(document); report = self.run(); self.assertIn("ROVER_IDEMPOTENCY_CONFLICT", self.codes(report))

    def test_schema_version_two(self) -> None:
        connection, _ = REGISTRY.open_database(self.arguments.database)
        try: connection.executescript(SQL_PATH.read_text(encoding="utf-8")); connection.executemany("INSERT INTO rover_schema_metadata VALUES (?, ?)", (("schema_version", "2"), ("application_phase", "ST-006")))
        finally: connection.close()
        self.assertIn("ROVER_SCHEMA_VERSION_UNSUPPORTED", self.codes(self.run()))

    def test_database_inside_repository(self) -> None:
        arguments = REGISTRY.RegistryArguments(self.repository, self.repository / "x.db", self.session_path, self.arguments.json_report, self.arguments.text_report)
        with self.assertRaises(REGISTRY.RegistryFailure) as caught: REGISTRY.validate_arguments(arguments)
        self.assertEqual(caught.exception.code, "ROVER_DATABASE_PATH_INSIDE_REPOSITORY")

    def test_report_inside_repository(self) -> None:
        arguments = REGISTRY.RegistryArguments(self.repository, self.arguments.database, self.session_path, self.repository / "x.json", self.arguments.text_report)
        with self.assertRaises(REGISTRY.RegistryFailure) as caught: REGISTRY.validate_arguments(arguments)
        self.assertEqual(caught.exception.code, "ROVER_REPORT_PATH_INSIDE_REPOSITORY")

    def test_missing_database_parent(self) -> None:
        arguments = REGISTRY.RegistryArguments(self.repository, self.root / "missing/x.db", self.session_path, self.arguments.json_report, self.arguments.text_report)
        with self.assertRaises(REGISTRY.RegistryFailure) as caught: REGISTRY.validate_arguments(arguments)
        self.assertEqual(caught.exception.code, "ROVER_DATABASE_PARENT_INVALID")

    def test_missing_report_parent(self) -> None:
        arguments = REGISTRY.RegistryArguments(self.repository, self.arguments.database, self.session_path, self.root / "missing/x.json", self.arguments.text_report)
        with self.assertRaises(REGISTRY.RegistryFailure) as caught: REGISTRY.validate_arguments(arguments)
        self.assertEqual(caught.exception.code, "ROVER_REPORT_PARENT_INVALID")

    def test_parent_is_file(self) -> None:
        parent = self.root / "parent-file"; parent.write_text("x", encoding="utf-8"); arguments = REGISTRY.RegistryArguments(self.repository, parent / "x.db", self.session_path, self.arguments.json_report, self.arguments.text_report)
        with self.assertRaises(REGISTRY.RegistryFailure): REGISTRY.validate_arguments(arguments)

    def test_failure_injection_rollback(self) -> None:
        self.assertTrue(self.run(fail_after_operation_index=0).document["transaction"]["rolled_back"])

    def test_no_partial_rover(self) -> None:
        self.run(fail_after_operation_index=0); self.assertEqual(self.query("SELECT COUNT(*) FROM rover_registry")[0][0], 0)

    def test_no_partial_field_permissions(self) -> None:
        self.run(fail_after_operation_index=0); self.assertEqual(self.query("SELECT COUNT(*) FROM rover_allowed_fields")[0][0], 0)

    def test_no_partial_unit_permissions(self) -> None:
        self.run(fail_after_operation_index=0); self.assertEqual(self.query("SELECT COUNT(*) FROM rover_allowed_units")[0][0], 0)

    def test_no_partial_decision(self) -> None:
        self.run(fail_after_operation_index=8); self.assertEqual(self.query("SELECT COUNT(*) FROM rover_authorization_decisions")[0][0], 0)

    def test_previous_state_maintained(self) -> None:
        self.run(); before = self.row_counts(); self.write_session(self.revision_session(1)); self.run(fail_after_operation_index=0); self.assertEqual(self.row_counts(), before)

    def test_hash_maintained_after_rollback(self) -> None:
        self.run(); before = self.canonical_hash(); self.write_session(self.revision_session(1)); self.run(fail_after_operation_index=0); self.assertEqual(self.canonical_hash(), before)

    def test_integrity_after_rollback(self) -> None:
        self.run(fail_after_operation_index=0); connection, _ = REGISTRY.open_database(self.arguments.database)
        try: self.assertEqual(REGISTRY.integrity_check(connection), "OK")
        finally: connection.close()

    def test_sqlite_exception_rollback(self) -> None:
        def fail(_connection, _operation): raise sqlite3.OperationalError("test")
        self.assertTrue(self.run(operation_processor=fail).document["transaction"]["rolled_back"])

    def test_report_write_failure(self) -> None:
        arguments = REGISTRY.RegistryArguments(self.repository, self.arguments.database, self.session_path, self.report_dir, self.arguments.text_report); self.assertEqual(self.run(arguments=arguments, write_reports=True).exit_code, 7)

    def test_unexpected_internal_exception(self) -> None:
        with mock.patch.object(REGISTRY, "run_registry_session", side_effect=RuntimeError("private")):
            stderr = io.StringIO()
            with redirect_stderr(stderr): code = REGISTRY.main(["--repository-root", str(self.repository), "--database", str(self.arguments.database), "--session", str(self.session_path), "--json-report", str(self.arguments.json_report), "--text-report", str(self.arguments.text_report)])
        self.assertEqual(code, 7); self.assertNotIn("private", stderr.getvalue())

    def test_corrupted_metadata_fail_closed(self) -> None:
        self.run(); connection = sqlite3.connect(self.arguments.database); connection.execute("UPDATE rover_schema_metadata SET metadata_value='BROKEN' WHERE metadata_key='schema_version'"); connection.commit(); connection.close(); self.assertIn("ROVER_SCHEMA_VERSION_UNSUPPORTED", self.codes(self.run()))

    def test_source_standard_library_only(self) -> None:
        tree = ast.parse(IMPLEMENTATION_PATH.read_text(encoding="utf-8")); imports = {node.names[0].name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)}; imports |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}; self.assertTrue(imports <= {"__future__", "argparse", "dataclasses", "hashlib", "json", "os", "pathlib", "re", "sqlite3", "sys", "typing"})

    def test_forbidden_imports_absent(self) -> None:
        source = IMPLEMENTATION_PATH.read_text(encoding="utf-8"); self.assertIsNone(re.search(r"(?m)^\s*(?:from|import)\s+(?:socket|requests|urllib|subprocess|multiprocessing|serial|gpiod|ctypes)\b", source))

    def test_sql_forbidden_statements_absent(self) -> None:
        sql = SQL_PATH.read_text(encoding="utf-8").upper(); self.assertTrue(all(item not in sql for item in ("DROP ", "VACUUM", "DELETE ")))

    def test_report_no_timestamp(self) -> None:
        self.assertNotIn("timestamp", REGISTRY.render_json_report(self.run()).lower())

    def test_report_no_absolute_path(self) -> None:
        self.assertNotIn(str(self.root), REGISTRY.render_json_report(self.run()))

    def test_diagnostic_sort_order(self) -> None:
        report = self.run(fail_after_operation_index=0); keys = [(x["component"], x["code"], x["operation_id"], x["message"]) for x in report.document["diagnostics"]]; self.assertEqual(keys, sorted(keys))

    def test_operation_request_hash_stable(self) -> None:
        operation = copy.deepcopy(self.example["operations"][0]); self.assertEqual(REGISTRY.operation_request_sha256(operation), REGISTRY.operation_request_sha256(copy.deepcopy(operation)))

    def test_canonical_json_unicode(self) -> None:
        self.assertEqual(REGISTRY.canonical_json({"label": "田"}), '{"label":"田"}')

    def test_canonical_json_sorted_keys(self) -> None:
        self.assertEqual(REGISTRY.canonical_json({"b": 1, "a": 2}), '{"a":2,"b":1}')

    def test_rover_id_pattern(self) -> None:
        self.assertIsNotNone(REGISTRY.ROVER_ID_PATTERN.fullmatch("ROVER-DEMO-001"))

    def test_field_id_pattern(self) -> None:
        self.assertIsNotNone(REGISTRY.FIELD_ID_PATTERN.fullmatch("FIELD-DEMO-001"))

    def test_unit_id_pattern(self) -> None:
        self.assertIsNotNone(REGISTRY.UNIT_ID_PATTERN.fullmatch("UNIT-DEMO-WEED"))

    def test_mission_id_pattern(self) -> None:
        self.assertIsNotNone(REGISTRY.MISSION_ID_PATTERN.fullmatch("MISSION-DEMO-001"))

    def test_authorization_id_pattern(self) -> None:
        self.assertIsNotNone(REGISTRY.AUTHORIZATION_ID_PATTERN.fullmatch("AUTH-ST006-001"))

    def test_operation_id_pattern(self) -> None:
        self.assertIsNotNone(REGISTRY.OPERATION_ID_PATTERN.fullmatch("OP-ST006-001"))

    def test_role_exact_set(self) -> None:
        self.assertEqual(REGISTRY.ROLES, ("SCOUT", "WORK", "MULTI_ROLE", "TEST_ONLY"))

    def test_registration_state_exact_set(self) -> None:
        self.assertEqual(REGISTRY.REGISTRATION_STATES, ("PENDING", "REGISTERED", "SUSPENDED", "REVOKED"))

    def test_hardware_class_exact_set(self) -> None:
        self.assertEqual(len(REGISTRY.HARDWARE_CLASSES), 4)

    def test_mission_state_exact_set(self) -> None:
        self.assertEqual(len(REGISTRY.MISSION_STATES), 12)

    def test_reason_code_contract_count(self) -> None:
        self.assertEqual(len(REGISTRY.REASON_CODES), 12)

    def test_battery_reserve_boundary_authorized(self) -> None:
        self.run(); self.write_session(self.authorization_session(120, battery_percentage=20)); self.assertEqual(self.run().document["authorization_decisions"]["authorized_count"], 2)

    def test_battery_100_authorized(self) -> None:
        self.run(); self.write_session(self.authorization_session(120, battery_percentage=100)); self.assertEqual(self.run().exit_code, 0)

    def test_invalid_battery_negative(self) -> None:
        document = self.authorization_session(120, battery_percentage=-1); self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_invalid_battery_over_100(self) -> None:
        document = self.authorization_session(120, battery_percentage=101); self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_invalid_battery_boolean(self) -> None:
        document = self.authorization_session(120, battery_percentage=True); self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_verify_integrity_payload_exact(self) -> None:
        document = copy.deepcopy(self.example); document["operations"][9]["payload"] = {"extra": True}; self.assert_validation_failure(document, "ROVER_SESSION_INVALID")

    def test_schema_migration_false(self) -> None:
        self.assertFalse(self.run().document["schema"]["migration_performed"])

    def test_atomic_session_true(self) -> None:
        self.assertTrue(self.run().document["transaction"]["atomic_session"])

    def test_table_count_six_report(self) -> None:
        self.assertEqual(self.run().document["summary"]["table_count"], 6)

    def test_authorized_summary_count(self) -> None:
        self.assertEqual(self.run().document["summary"]["authorized_decision_count"], 1)

    def test_denied_summary_count(self) -> None:
        self.assertEqual(self.run().document["summary"]["denied_decision_count"], 1)

    def test_next_phase_eligible(self) -> None:
        self.assertTrue(self.run().document["summary"]["next_phase_eligible"])

    def test_database_file_hash_not_reported(self) -> None:
        self.assertNotIn("database_sha256", REGISTRY.render_json_report(self.run()))

    def test_authorization_policy_only(self) -> None:
        report = self.run(); self.assertFalse(report.document["safety"]["direct_output_authority"])

    def test_field_navigation_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["field_navigation_performed"])

    def test_rover_communication_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["rover_communication_performed"])

    def test_motor_control_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["motor_control_performed"])

    def test_charging_control_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["charging_control_performed"])

    def test_repository_modified_false(self) -> None:
        self.assertFalse(self.run().document["safety"]["repository_modified"])

    def test_offline_only_true(self) -> None:
        self.assertTrue(self.run().document["safety"]["offline_only"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
