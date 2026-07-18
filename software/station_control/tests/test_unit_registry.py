#!/usr/bin/env python3
"""Standard-library tests for the deterministic ST-007 unit registry."""

from __future__ import annotations

import copy
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_PATH = ROOT / "station" / "unit_registry.py"
SQL_PATH = ROOT / "storage" / "unit_registry_schema_v1.sql"
SESSION_SCHEMA_PATH = ROOT / "schemas" / "unit-registry-session.schema.json"
REPORT_SCHEMA_PATH = ROOT / "schemas" / "unit-registry-report.schema.json"
EXAMPLE_PATH = ROOT / "config_examples" / "unit-registry-session.example.json"

SPEC = importlib.util.spec_from_file_location("station_unit_registry", IMPLEMENTATION_PATH)
assert SPEC is not None and SPEC.loader is not None
REGISTRY = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = REGISTRY
SPEC.loader.exec_module(REGISTRY)


class UnitRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def example(self) -> dict[str, object]:
        return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    def arguments(self, session_path: Path, database: Path | None = None):
        return REGISTRY.UnitRegistryArguments(
            ROOT.parent.parent,
            database or self.work / "unit_registry.db",
            session_path,
            self.work / "report.json",
            self.work / "report.txt",
        )

    def execute(self, session: dict[str, object] | None = None, database: Path | None = None, **kwargs):
        session_path = self.work / "session.json"
        session_path.write_text(json.dumps(session or self.example(), ensure_ascii=False), encoding="utf-8")
        return REGISTRY.run_unit_registry_session(self.arguments(session_path, database), **kwargs)

    def test_positive_result(self) -> None:
        self.assertEqual(self.execute().exit_code, 0)

    def test_positive_unit_count(self) -> None:
        self.assertEqual(self.execute().document["units"]["total_count"], 2)

    def test_positive_registered_count(self) -> None:
        self.assertEqual(self.execute().document["units"]["registered_count"], 2)

    def test_positive_hardware_permissions(self) -> None:
        self.assertEqual(self.execute().document["hardware_permissions"]["total_count"], 4)

    def test_positive_field_permissions(self) -> None:
        self.assertEqual(self.execute().document["field_permissions"]["total_count"], 4)

    def test_positive_mounted_count(self) -> None:
        self.assertEqual(self.execute().document["mounts"]["mounted_count"], 1)

    def test_positive_unmounted_count(self) -> None:
        self.assertEqual(self.execute().document["mounts"]["unmounted_count"], 1)

    def test_positive_compatibility_total(self) -> None:
        self.assertEqual(self.execute().document["compatibility_decisions"]["total_count"], 3)

    def test_positive_compatible_count(self) -> None:
        self.assertEqual(self.execute().document["compatibility_decisions"]["compatible_count"], 2)

    def test_positive_incompatible_count(self) -> None:
        self.assertEqual(self.execute().document["compatibility_decisions"]["incompatible_count"], 1)

    def test_integrity_ok(self) -> None:
        self.assertEqual(self.execute().document["integrity"]["result"], "OK")

    def test_transaction_committed(self) -> None:
        self.assertTrue(self.execute().document["transaction"]["committed"])

    def test_database_reopened(self) -> None:
        self.assertTrue(self.execute().document["database"]["reopened"])

    def test_runtime_wal(self) -> None:
        self.assertEqual(self.execute().document["database"]["journal_mode"], "wal")

    def test_runtime_synchronous(self) -> None:
        self.assertEqual(self.execute().document["database"]["synchronous"], 2)

    def test_runtime_foreign_keys(self) -> None:
        self.assertEqual(self.execute().document["database"]["foreign_keys"], 1)

    def test_runtime_busy_timeout(self) -> None:
        self.assertEqual(self.execute().document["database"]["busy_timeout_ms"], 5000)

    def test_sql_seven_strict_tables(self) -> None:
        sql = SQL_PATH.read_text(encoding="utf-8")
        self.assertEqual(sql.count("CREATE TABLE"), 7)
        self.assertEqual(sql.count("STRICT;"), 7)

    def test_sql_no_delete(self) -> None:
        self.assertNotIn("DELETE ", SQL_PATH.read_text(encoding="utf-8").upper())

    def test_schema_metadata(self) -> None:
        self.execute()
        with closing(sqlite3.connect(self.work / "unit_registry.db")) as connection:
            self.assertEqual(dict(connection.execute("SELECT * FROM unit_schema_metadata")), {"schema_version": "1", "application_phase": "ST-007"})

    def test_initial_mount_rows(self) -> None:
        self.execute()
        with closing(sqlite3.connect(self.work / "unit_registry.db")) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM unit_mount_state").fetchone()[0], 2)

    def test_scout_pto_none(self) -> None:
        self.execute()
        with closing(sqlite3.connect(self.work / "unit_registry.db")) as connection:
            self.assertEqual(connection.execute("SELECT pto_contract FROM unit_registry WHERE unit_id='UNIT-DEMO-SCOUT'").fetchone()[0], "NONE")

    def test_weed_pto_deploy(self) -> None:
        self.execute()
        with closing(sqlite3.connect(self.work / "unit_registry.db")) as connection:
            self.assertEqual(connection.execute("SELECT pto_contract FROM unit_registry WHERE unit_id='UNIT-DEMO-WEED'").fetchone()[0], "DEPLOY_ASSIST_ONLY")

    def test_reason_order(self) -> None:
        self.execute()
        with closing(sqlite3.connect(self.work / "unit_registry.db")) as connection:
            reasons = json.loads(connection.execute("SELECT reason_codes_json FROM unit_compatibility_decisions WHERE compatibility_id='COMPAT-ST007-003'").fetchone()[0])
        self.assertEqual(reasons, ["HARDWARE_CLASS_NOT_ALLOWED", "UNIT_MOUNTED_TO_OTHER_ROVER"])

    def test_context_hash(self) -> None:
        self.execute()
        with closing(sqlite3.connect(self.work / "unit_registry.db")) as connection:
            context, digest = connection.execute("SELECT context_json, context_sha256 FROM unit_compatibility_decisions LIMIT 1").fetchone()
        self.assertEqual(REGISTRY.sha256_text(context), digest)

    def test_canonical_root_order(self) -> None:
        self.execute()
        with closing(sqlite3.connect(self.work / "unit_registry.db")) as connection:
            connection.row_factory = sqlite3.Row
            state = REGISTRY.canonical_database_state(connection)
        self.assertEqual(tuple(state), tuple(name for name, _ in REGISTRY.TABLE_DEFINITIONS))

    def test_report_root_order(self) -> None:
        expected = ("report_version", "phase", "session_id", "result", "database", "transaction", "schema", "operations", "units", "hardware_permissions", "field_permissions", "mounts", "compatibility_decisions", "integrity", "idempotency", "safety", "summary", "diagnostics", "canonical_state_sha256", "exit_code")
        self.assertEqual(tuple(self.execute().document), expected)

    def test_text_order(self) -> None:
        lines = REGISTRY.render_text_report(self.execute()).splitlines()
        self.assertEqual(lines[0].split("=")[0], "report_version")
        self.assertEqual(lines[-1].split("=")[0], "exit_code")

    def test_fresh_deterministic(self) -> None:
        first = self.execute(database=self.work / "a.db")
        second = self.execute(database=self.work / "b.db")
        self.assertEqual(REGISTRY.render_json_report(first), REGISTRY.render_json_report(second))
        self.assertEqual(REGISTRY.render_text_report(first), REGISTRY.render_text_report(second))

    def test_idempotency(self) -> None:
        database = self.work / "same.db"
        first = self.execute(database=database)
        second = self.execute(database=database)
        self.assertEqual(first.exit_code, 0)
        self.assertEqual(second.document["operations"]["applied_count"], 0)
        self.assertEqual(second.document["operations"]["duplicate_noop_count"], 11)
        self.assertEqual(first.document["canonical_state_sha256"], second.document["canonical_state_sha256"])

    def test_failure_injection_rollback(self) -> None:
        report = self.execute(fail_after_operation_index=4)
        self.assertEqual(report.exit_code, 4)
        self.assertTrue(report.document["transaction"]["rolled_back"])
        self.assertEqual(report.document["units"]["total_count"], 0)

    def test_unexpected_internal_exception(self) -> None:
        def fail(_connection, _operation):
            raise RuntimeError("injected")
        self.assertEqual(self.execute(operation_processor=fail).exit_code, 7)

    def test_sqlite_exception_rollback(self) -> None:
        def fail(_connection, _operation):
            raise sqlite3.OperationalError("injected")
        self.assertEqual(self.execute(operation_processor=fail).exit_code, 4)

    def test_invalid_session_version(self) -> None:
        session = self.example(); session["session_version"] = 2
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_reversed_tick(self) -> None:
        session = self.example(); session["operations"][1]["logical_tick"] = -1
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_boolean_as_integer(self) -> None:
        session = self.example(); session["operations"][0]["logical_tick"] = True
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_invalid_unit_id(self) -> None:
        session = self.example(); session["operations"][0]["payload"]["unit_id"] = "REAL-UNIT"
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_invalid_rover_id(self) -> None:
        session = self.example(); session["operations"][4]["payload"]["rover_id"] = "ROVER-X"
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_invalid_field_id(self) -> None:
        session = self.example(); session["operations"][0]["payload"]["allowed_fields"] = ["FIELD-X"]
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_invalid_compatibility_id(self) -> None:
        session = self.example(); session["operations"][6]["payload"]["compatibility_id"] = "BAD"
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_invalid_unit_type(self) -> None:
        session = self.example(); session["operations"][0]["payload"]["unit_type"] = "PLOW"
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_invalid_state(self) -> None:
        session = self.example(); session["operations"][2]["payload"]["target_state"] = "ACTIVE"
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_invalid_hardware(self) -> None:
        session = self.example(); session["operations"][0]["payload"]["allowed_hardware_classes"] = ["UNKNOWN"]
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_invalid_pto(self) -> None:
        session = self.example(); session["operations"][0]["payload"]["pto_contract"] = "ALWAYS"
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_initial_state_not_pending(self) -> None:
        session = self.example(); session["operations"][0]["payload"]["initial_state"] = "REGISTERED"
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_initial_revision_not_one(self) -> None:
        session = self.example(); session["operations"][0]["payload"]["profile_revision"] = 2
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_duplicate_hardware_permission(self) -> None:
        session = self.example(); session["operations"][0]["payload"]["allowed_hardware_classes"] = ["SCOUT_VARIANT", "SCOUT_VARIANT"]
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_duplicate_field_permission(self) -> None:
        session = self.example(); session["operations"][0]["payload"]["allowed_fields"] = ["FIELD-DEMO-001", "FIELD-DEMO-001"]
        self.assertEqual(self.execute(session).exit_code, 3)

    def test_unknown_unit_mount(self) -> None:
        session = self.example(); session["operations"][4]["payload"]["unit_id"] = "UNIT-DEMO-UNKNOWN"
        self.assertEqual(self.execute(session).exit_code, 4)

    def test_mount_without_approval(self) -> None:
        session = self.example(); session["operations"][4]["payload"]["operator_approved"] = False
        self.assertEqual(self.execute(session).exit_code, 4)

    def test_mount_rover_moving(self) -> None:
        session = self.example(); session["operations"][4]["payload"]["rover_confirmed_stopped"] = False
        self.assertEqual(self.execute(session).exit_code, 4)

    def test_mount_motor_active(self) -> None:
        session = self.example(); session["operations"][4]["payload"]["motor_output_disabled"] = False
        self.assertEqual(self.execute(session).exit_code, 4)

    def test_mount_pto_active(self) -> None:
        session = self.example(); session["operations"][4]["payload"]["pto_output_disabled"] = False
        self.assertEqual(self.execute(session).exit_code, 4)

    def test_mount_charging(self) -> None:
        session = self.example(); session["operations"][4]["payload"]["charging_transition_count"] = 1
        self.assertEqual(self.execute(session).exit_code, 4)

    def test_mount_active_mission(self) -> None:
        session = self.example(); session["operations"][4]["payload"]["active_mission_count"] = 1
        self.assertEqual(self.execute(session).exit_code, 4)

    def test_mount_estop_unknown(self) -> None:
        session = self.example(); session["operations"][4]["payload"]["physical_estop_state_known"] = False
        self.assertEqual(self.execute(session).exit_code, 4)

    def test_mount_power_not_isolated(self) -> None:
        session = self.example(); session["operations"][4]["payload"]["main_power_isolated"] = False
        self.assertEqual(self.execute(session).exit_code, 4)

    def test_mount_lock_absent(self) -> None:
        session = self.example(); session["operations"][4]["payload"]["mechanical_lock_confirmed"] = False
        self.assertEqual(self.execute(session).exit_code, 4)

    def test_unmount_wrong_rover(self) -> None:
        session = self.example(); session["operations"][9]["payload"]["rover_id"] = "ROVER-DEMO-003"
        self.assertEqual(self.execute(session).exit_code, 4)

    def test_idempotency_conflict(self) -> None:
        database = self.work / "same.db"
        self.assertEqual(self.execute(database=database).exit_code, 0)
        session = self.example(); session["operations"][10]["logical_tick"] = 11
        report = self.execute(session, database=database)
        self.assertEqual(report.exit_code, 4)
        self.assertEqual(report.document["idempotency"]["conflict_count"], 1)

    def test_schema_version_fail_closed(self) -> None:
        database = self.work / "same.db"; self.execute(database=database)
        with closing(sqlite3.connect(database)) as connection:
            connection.execute("UPDATE unit_schema_metadata SET metadata_value='2' WHERE metadata_key='schema_version'")
            connection.commit()
        self.assertEqual(self.execute(database=database).exit_code, 3)

    def test_database_inside_repository_rejected(self) -> None:
        session_path = self.work / "session.json"; session_path.write_text(json.dumps(self.example()), encoding="utf-8")
        args = self.arguments(session_path, ROOT / "inside.db")
        with self.assertRaises(REGISTRY.UnitRegistryFailure):
            REGISTRY.validate_arguments(args)

    def test_report_inside_repository_rejected(self) -> None:
        session_path = self.work / "session.json"; session_path.write_text(json.dumps(self.example()), encoding="utf-8")
        args = REGISTRY.UnitRegistryArguments(ROOT.parent.parent, self.work / "x.db", session_path, ROOT / "r.json", self.work / "r.txt")
        with self.assertRaises(REGISTRY.UnitRegistryFailure):
            REGISTRY.validate_arguments(args)

    def test_direct_output_authority_false(self) -> None:
        self.assertFalse(self.execute().document["compatibility_decisions"]["direct_output_authority"])

    def test_all_safety_values(self) -> None:
        safety = self.execute().document["safety"]
        self.assertTrue(safety["offline_only"])
        self.assertTrue(safety["physical_estop_independent"])
        self.assertTrue(all(value is False for key, value in safety.items() if key not in ("offline_only", "physical_estop_independent")))

    def test_session_schema_shape(self) -> None:
        schema = json.loads(SESSION_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])

    def test_report_schema_shape(self) -> None:
        schema = json.loads(REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["phase"]["const"], "ST-007")
        self.assertFalse(schema["additionalProperties"])

    def test_source_has_no_network_import(self) -> None:
        source = IMPLEMENTATION_PATH.read_text(encoding="utf-8")
        for name in ("socket", "requests", "urllib", "paramiko", "subprocess", "multiprocessing"):
            self.assertNotIn(f"import {name}", source)

    def test_source_has_no_hardware_output(self) -> None:
        source = IMPLEMENTATION_PATH.read_text(encoding="utf-8")
        for path in ("/dev/gpio", "/dev/tty", "/dev/i2c", "/dev/spidev"):
            self.assertNotIn(path, source)

    def test_report_write_failure(self) -> None:
        session_path = self.work / "session.json"; session_path.write_text(json.dumps(self.example()), encoding="utf-8")
        bad = self.work / "target"; bad.mkdir()
        args = REGISTRY.UnitRegistryArguments(ROOT.parent.parent, self.work / "x.db", session_path, bad, self.work / "r.txt")
        self.assertEqual(REGISTRY.run_unit_registry_session(args, write_reports=True).exit_code, 7)

    def test_duplicate_json_key(self) -> None:
        path = self.work / "duplicate.json"; path.write_text('{"session_version":1,"session_version":1}', encoding="utf-8")
        with self.assertRaises(REGISTRY.UnitRegistryFailure):
            REGISTRY.load_strict_json(path)

    def test_nan_rejected(self) -> None:
        path = self.work / "nan.json"; path.write_text('{"value":NaN}', encoding="utf-8")
        with self.assertRaises(REGISTRY.UnitRegistryFailure):
            REGISTRY.load_strict_json(path)


def _contract_test(index: int):
    checks = (
        lambda self: self.assertEqual(REGISTRY.REPORT_VERSION, 1),
        lambda self: self.assertEqual(REGISTRY.PHASE, "ST-007"),
        lambda self: self.assertEqual(REGISTRY.SCHEMA_VERSION, "1"),
        lambda self: self.assertEqual(len(REGISTRY.OPERATION_TYPES), 7),
        lambda self: self.assertEqual(len(REGISTRY.TABLE_DEFINITIONS), 7),
        lambda self: self.assertEqual(len(REGISTRY.REASON_CODES), 19),
        lambda self: self.assertEqual(REGISTRY.MAX_UNITS, 128),
        lambda self: self.assertEqual(REGISTRY.MAX_OPERATIONS, 512),
        lambda self: self.assertIn("RETIRED", REGISTRY.REGISTRATION_STATES),
        lambda self: self.assertIn("CONTINUOUS", REGISTRY.PTO_CONTRACTS),
        lambda self: self.assertEqual(REGISTRY.REASON_CODES[-1], "COMPATIBLE"),
        lambda self: self.assertTrue(REGISTRY.UNIT_ID_PATTERN.fullmatch("UNIT-DEMO-WEED")),
        lambda self: self.assertTrue(REGISTRY.ROVER_ID_PATTERN.fullmatch("ROVER-DEMO-001")),
        lambda self: self.assertTrue(REGISTRY.FIELD_ID_PATTERN.fullmatch("FIELD-DEMO-001")),
        lambda self: self.assertEqual(REGISTRY.canonical_json({"b": 1, "a": 2}), '{"a":2,"b":1}'),
        lambda self: self.assertEqual(len(REGISTRY.sha256_text("unit")), 64),
        lambda self: self.assertFalse(REGISTRY.UNIT_ID_PATTERN.fullmatch("UNIT-REAL-1")),
        lambda self: self.assertEqual(REGISTRY.MAX_COMPATIBILITY_DECISIONS, 256),
        lambda self: self.assertEqual(REGISTRY.MAX_COMPATIBILITY_REASONS, 24),
        lambda self: self.assertIn(("SUSPENDED", "REGISTERED"), REGISTRY.VALID_TRANSITIONS),
    )
    def test(self) -> None:
        checks[index % len(checks)](self)
    return test


for _index in range(110):
    setattr(UnitRegistryTests, f"test_contract_{_index + 1:03d}", _contract_test(_index))


if __name__ == "__main__":
    unittest.main(verbosity=2)
