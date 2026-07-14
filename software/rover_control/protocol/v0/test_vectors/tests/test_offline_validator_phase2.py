from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
IMPLEMENTATION = REPOSITORY_ROOT / "software/rover_control/protocol/v0/test_vectors/offline_validator/phase2.py"
MARKER = Path(r"C:\Paddy_Swarm_Project_work\tooling\jsonschema_draft202012\TOOLCHAIN_READY.txt")
MARKER_SHA256 = "f6c3314d3355d3ab56736198af5a247487fac2ca9d1395f784a53ea60b50de16"
TABLE_RELATIVE = Path("software/rover_control/protocol/v0/test_vectors/case_rules/protocol-v0-case-rules.json")
MANIFEST_RELATIVE = Path("software/rover_control/protocol/v0/test_vectors/manifest/test-vector-manifest.json")
VECTOR_DIRECTORY = Path("software/rover_control/protocol/v0/test_vectors/vectors")
PHASE1_IMPLEMENTATION = REPOSITORY_ROOT / "software/rover_control/protocol/v0/test_vectors/offline_validator/phase1.py"


def load_phase2_module():
    spec = importlib.util.spec_from_file_location("paddy_phase2_under_test", IMPLEMENTATION)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Phase 2 implementation")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


PHASE2 = load_phase2_module()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


class Phase2TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository_hashes_before = {
            path.relative_to(REPOSITORY_ROOT).as_posix(): digest(path)
            for path in (REPOSITORY_ROOT / "software/rover_control").rglob("*")
            if path.is_file()
        }
        cls.positive = cls.run_validator(REPOSITORY_ROOT)
        cls.positive_actuals = []
        for path in sorted((REPOSITORY_ROOT / VECTOR_DIRECTORY).glob("*.json")):
            data = load_json(path)
            actual = PHASE2.derive_vector_core_expectation(data)
            actual["relations"] = PHASE2.derive_relations(data)
            actual["filename_match"] = path.stem == actual["vector_id"]
            cls.positive_actuals.append(actual)

    @staticmethod
    def run_validator(root: Path, table_sha256: str = PHASE2.EXPECTED_CASE_RULE_TABLE_SHA256):
        return PHASE2.run_phase2(
            root,
            marker=MARKER,
            marker_sha256=MARKER_SHA256,
            case_rule_table_sha256=table_sha256,
        )

    @contextmanager
    def copied_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repository"
            destination = root / "software/rover_control"
            destination.parent.mkdir(parents=True)
            shutil.copytree(REPOSITORY_ROOT / "software/rover_control", destination)
            yield root

    def table_path(self, root: Path) -> Path:
        return root / TABLE_RELATIVE

    def manifest_path(self, root: Path) -> Path:
        return root / MANIFEST_RELATIVE

    def vector_path(self, root: Path, vector_id: str) -> Path:
        return root / VECTOR_DIRECTORY / f"{vector_id}.json"

    def refresh_manifest_vector(self, root: Path, vector_id: str) -> None:
        manifest_path = self.manifest_path(root)
        manifest = load_json(manifest_path)
        vector_path = self.vector_path(root, vector_id)
        row = next(item for item in manifest["vectors"] if item["vector_id"] == vector_id)
        row["sha256"] = digest(vector_path)
        row["size_bytes"] = vector_path.stat().st_size
        save_json(manifest_path, manifest)

    def refresh_table_manifest_source(self, root: Path) -> str:
        path = self.table_path(root)
        table = load_json(path)
        table["source_documents"]["manifest"]["sha256"] = digest(self.manifest_path(root))
        save_json(path, table)
        return digest(path)

    def mutate_rule_table(self, mutation) -> object:
        with self.copied_repository() as root:
            path = self.table_path(root)
            table = load_json(path)
            mutation(table)
            save_json(path, table)
            return self.run_validator(root, digest(path))

    def mutate_rule_table_raw(self, mutation, refresh_hash: bool = True) -> object:
        with self.copied_repository() as root:
            path = self.table_path(root)
            path.write_bytes(mutation(path.read_bytes()))
            expected = digest(path) if refresh_hash else PHASE2.EXPECTED_CASE_RULE_TABLE_SHA256
            return self.run_validator(root, expected)

    def mutate_vector(self, vector_id: str, mutation) -> object:
        with self.copied_repository() as root:
            path = self.vector_path(root, vector_id)
            data = load_json(path)
            mutation(data)
            save_json(path, data)
            self.refresh_manifest_vector(root, vector_id)
            table_hash = self.refresh_table_manifest_source(root)
            report = self.run_validator(root, table_hash)
            self.assertEqual("PASS", report.phase1_result, [(item.family, item.code, item.message) for item in report.diagnostics])
            return report

    def replace_vector_from_donor(self, vector_id: str, donor_id: str) -> object:
        with self.copied_repository() as root:
            donor = load_json(self.vector_path(root, donor_id))
            save_json(self.vector_path(root, vector_id), donor)
            self.refresh_manifest_vector(root, vector_id)
            report = self.run_validator(root, self.refresh_table_manifest_source(root))
            self.assertEqual("PASS", report.phase1_result, [(item.family, item.code, item.message) for item in report.diagnostics])
            return report

    def assert_code(self, report, code: str, expected_exit: int = 5) -> None:
        self.assertEqual(expected_exit, report.exit_code)
        self.assertIn(code, {item.code for item in report.diagnostics})

    def test_positive_full_run(self):
        data = self.positive.report_dict()
        self.assertEqual(0, self.positive.exit_code)
        self.assertEqual("PASS", data["phase1_result"])
        self.assertEqual("PASS", data["full_validator_result"])
        self.assertEqual("PASS", data["manifest"]["result"])
        self.assertEqual("PASS", data["schema"]["result"])
        self.assertEqual("PASS", data["case_rule_table"]["result"])

    def test_positive_all_38_semantics_pass(self):
        summary = self.positive.report_dict()["summary"]
        self.assertEqual(38, summary["semantic_pass_count"])
        self.assertEqual(0, summary["semantic_fail_count"])
        self.assertEqual(0, summary["semantic_not_run_count"])

    def test_positive_aggregate_coverage_passes(self):
        self.assertEqual("PASS", self.positive.coverage_result)

    def test_positive_rule_table_hash(self):
        self.assertEqual(PHASE2.EXPECTED_CASE_RULE_TABLE_SHA256, digest(REPOSITORY_ROOT / TABLE_RELATIVE))

    def test_positive_rule_and_source_counts(self):
        case = self.positive.case_rule_table
        self.assertEqual(38, case["rule_count"])
        self.assertEqual(9, case["source_hash_match_count"])

    def test_positive_report_root_order(self):
        self.assertEqual(
            [
                "report_version", "protocol_version", "phase", "phase1_result",
                "full_validator_result", "toolchain", "manifest", "schema",
                "case_rule_table", "vectors", "summary", "diagnostics", "exit_code",
            ],
            list(self.positive.report_dict()),
        )

    def test_positive_json_report_is_deterministic(self):
        first = PHASE2.render_json_report(self.run_validator(REPOSITORY_ROOT))
        second = PHASE2.render_json_report(self.run_validator(REPOSITORY_ROOT))
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))

    def test_positive_text_report_is_deterministic(self):
        first = PHASE2.render_text_report(self.run_validator(REPOSITORY_ROOT))
        second = PHASE2.render_text_report(self.run_validator(REPOSITORY_ROOT))
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))

    def test_positive_report_has_no_absolute_or_nondeterministic_metadata(self):
        rendered = PHASE2.render_json_report(self.positive)
        lowered = rendered.lower()
        self.assertNotIn(str(REPOSITORY_ROOT).lower(), lowered)
        self.assertNotIn(str(MARKER).lower(), lowered)
        self.assertNotIn("timestamp", lowered)
        self.assertNotIn("username", lowered)
        self.assertNotIn("machine_name", lowered)

    def test_positive_phase1_json_hash_is_preserved(self):
        phase1 = PHASE2.PHASE1._run_phase1(REPOSITORY_ROOT, PHASE2.DEFAULT_MANIFEST, MARKER, MARKER_SHA256)
        rendered = PHASE2.PHASE1.render_json_report(phase1).encode("utf-8")
        self.assertEqual("0e4b82369c23a84c7b63131c541cb9fa3d022883f078e07ef400f900e03166e8", hashlib.sha256(rendered).hexdigest())

    def test_phase1_global_toolchain_fatal_stops_s0(self):
        report = PHASE2.run_phase2(REPOSITORY_ROOT, marker=MARKER, marker_sha256="0" * 64)
        self.assertEqual(2, report.exit_code)
        self.assertEqual("NOT_RUN", report.case_rule_table["result"])

    def test_s0_missing_rule_table(self):
        with self.copied_repository() as root:
            self.table_path(root).unlink()
            report = self.run_validator(root)
            self.assert_code(report, "SEMANTIC_RULE_TABLE_NOT_FOUND")

    def test_s0_rule_table_symlink(self):
        with self.copied_repository() as root:
            path = self.table_path(root)
            original = PHASE2.path_is_symlink
            with mock.patch.object(PHASE2, "path_is_symlink", side_effect=lambda candidate: candidate == path or original(candidate)):
                report = self.run_validator(root)
            self.assert_code(report, "SEMANTIC_RULE_TABLE_SYMLINK_FORBIDDEN")

    def test_s0_hash_mismatch(self):
        report = self.mutate_rule_table_raw(lambda raw: raw.replace(b'"protocol_version": "v0"', b'"protocol_version": "x0"'), refresh_hash=False)
        self.assert_code(report, "SEMANTIC_RULE_TABLE_HASH_MISMATCH")

    def test_s0_bom(self):
        report = self.mutate_rule_table_raw(lambda raw: b"\xef\xbb\xbf" + raw)
        self.assert_code(report, "SEMANTIC_RULE_TABLE_FORMAT_ERROR")

    def test_s0_cr(self):
        report = self.mutate_rule_table_raw(lambda raw: raw.replace(b"\n", b"\r\n", 1))
        self.assert_code(report, "SEMANTIC_RULE_TABLE_FORMAT_ERROR")

    def test_s0_missing_trailing_lf(self):
        report = self.mutate_rule_table_raw(lambda raw: raw.rstrip(b"\n"))
        self.assert_code(report, "SEMANTIC_RULE_TABLE_FORMAT_ERROR")

    def test_s0_duplicate_key(self):
        report = self.mutate_rule_table_raw(lambda raw: raw.replace(b"{\n", b'{\n  "rule_table_version": 1,\n', 1))
        self.assert_code(report, "SEMANTIC_RULE_TABLE_DUPLICATE_KEY")

    def test_s0_unknown_root_property(self):
        report = self.mutate_rule_table(lambda table: table.__setitem__("unknown", True))
        self.assert_code(report, "SEMANTIC_RULE_TABLE_MODEL_MISMATCH")

    def test_s0_root_property_order(self):
        def mutation(table):
            value = table.pop("rule_table_version")
            table["rule_table_version"] = value
        report = self.mutate_rule_table(mutation)
        self.assert_code(report, "SEMANTIC_RULE_TABLE_ORDER_MISMATCH")

    def test_s0_source_hash_mismatch(self):
        with self.copied_repository() as root:
            path = root / "software/rover_control/safety/SAFETY_REQUIREMENTS.md"
            path.write_bytes(path.read_bytes() + b"\n")
            report = self.run_validator(root)
            self.assert_code(report, "SEMANTIC_RULE_TABLE_SOURCE_HASH_MISMATCH")

    def test_s0_duplicate_rule_id(self):
        report = self.mutate_rule_table(lambda table: table["rules"][1].__setitem__("vector_id", table["rules"][0]["vector_id"]))
        self.assert_code(report, "SEMANTIC_RULE_TABLE_DUPLICATE_ID")

    def test_s0_rule_order_mismatch(self):
        def mutation(table):
            table["rules"][0], table["rules"][1] = table["rules"][1], table["rules"][0]
        report = self.mutate_rule_table(mutation)
        self.assert_code(report, "SEMANTIC_RULE_TABLE_ORDER_MISMATCH")

    def test_s0_relation_property_missing(self):
        report = self.mutate_rule_table(lambda table: table["rules"][0]["relations"].pop("watchdog"))
        self.assert_code(report, "SEMANTIC_RULE_TABLE_RELATION_MODEL_MISMATCH")

    def test_s0_relation_enum_invalid(self):
        report = self.mutate_rule_table(lambda table: table["rules"][0]["relations"].__setitem__("sequence", "UNKNOWN"))
        self.assert_code(report, "SEMANTIC_RULE_TABLE_RELATION_MODEL_MISMATCH")

    def test_s0_aggregate_set_mismatch(self):
        report = self.mutate_rule_table(lambda table: table["aggregate_expectations"]["temporal_ids"].pop())
        self.assert_code(report, "SEMANTIC_RULE_TABLE_COVERAGE_MISMATCH")

    def test_semantic_source_scenario_mismatch(self):
        report = self.mutate_vector("PV0-VAL-001A", lambda data: data["source"].__setitem__("source_scenario", 2))
        self.assert_code(report, "SEMANTIC_SOURCE_MISMATCH")

    def test_semantic_profile_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-001B")
        self.assert_code(report, "SEMANTIC_PROFILE_MISMATCH")

    def test_semantic_initial_state_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-002")
        self.assert_code(report, "SEMANTIC_STATE_MISMATCH")

    def test_semantic_trigger_mismatch(self):
        report = self.mutate_vector("PV0-VAL-001A", lambda data: data["stimulus"]["message"].__setitem__("command_type", "STOP"))
        self.assert_code(report, "SEMANTIC_TRIGGER_MISMATCH")

    def test_semantic_terminal_step_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-006")
        self.assert_code(report, "SEMANTIC_TERMINAL_STEP_MISMATCH")

    def test_semantic_disposition_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-006")
        self.assert_code(report, "SEMANTIC_DISPOSITION_MISMATCH")

    def test_semantic_defensive_action_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-020")
        self.assert_code(report, "SEMANTIC_DEFENSIVE_ACTION_MISMATCH")

    def test_semantic_message_handling_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-009")
        self.assert_code(report, "SEMANTIC_MESSAGE_HANDLING_MISMATCH")

    def test_semantic_result_source_mismatch(self):
        report = self.mutate_vector("PV0-VAL-006", lambda data: data["validation_expectation"].__setitem__("result_source", "NONE"))
        self.assert_code(report, "SEMANTIC_RESULT_SOURCE_MISMATCH")

    def test_semantic_rejection_reason_mismatch(self):
        report = self.mutate_vector("PV0-VAL-006", lambda data: data["validation_expectation"].__setitem__("rejection_reason", "invalid_session"))
        self.assert_code(report, "SEMANTIC_REJECTION_REASON_MISMATCH")

    def test_semantic_state_event_mismatch(self):
        report = self.mutate_vector("PV0-VAL-001A", lambda data: data["validation_expectation"].__setitem__("state_machine_event", "MOVE_FORWARD"))
        self.assert_code(report, "SEMANTIC_STATE_EVENT_MISMATCH")

    def test_semantic_accepted_sequence_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-006")
        self.assert_code(report, "SEMANTIC_SEQUENCE_POLICY_MISMATCH")

    def test_semantic_liveness_mismatch(self):
        report = self.mutate_vector("PV0-VAL-001A", lambda data: data["validation_expectation"].__setitem__("control_liveness_updated", True))
        self.assert_code(report, "SEMANTIC_LIVENESS_MISMATCH")

    def test_semantic_output_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-002")
        self.assert_code(report, "SEMANTIC_OUTPUT_MISMATCH")

    def test_semantic_armed_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-004")
        self.assert_code(report, "SEMANTIC_ARMED_MISMATCH")

    def test_semantic_operation_mismatch(self):
        report = self.mutate_vector("PV0-VAL-001A", lambda data: data["immediate_expectation"].__setitem__("operation_id", "new"))
        self.assert_code(report, "SEMANTIC_OPERATION_MISMATCH")

    def test_semantic_final_state_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-002")
        self.assert_code(report, "SEMANTIC_STATE_MISMATCH")

    def test_semantic_safety_latch_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-004")
        self.assert_code(report, "SEMANTIC_LATCH_MISMATCH")

    def test_semantic_temporal_mismatch(self):
        report = self.replace_vector_from_donor("PV0-VAL-001A", "PV0-VAL-004")
        self.assert_code(report, "SEMANTIC_TEMPORAL_MISMATCH")

    def test_semantic_sequence_relation_mismatch(self):
        report = self.mutate_vector("PV0-VAL-011", lambda data: data["stimulus"]["message"].__setitem__("sequence", 2000))
        self.assert_code(report, "SEMANTIC_RELATION_MISMATCH")

    def test_semantic_session_relation_mismatch(self):
        def mutation(data):
            data["stimulus"]["message"]["session_id"] = data["initial_fixture"]["session_id"]
        report = self.mutate_vector("PV0-VAL-007", mutation)
        self.assert_code(report, "SEMANTIC_RELATION_MISMATCH")

    def test_semantic_cached_identity_relation_mismatch(self):
        def mutation(data):
            data["stimulus"]["message"]["message_id"] = data["initial_fixture"]["cached_command_result"]["message_id"]
        report = self.mutate_vector("PV0-VAL-010", mutation)
        self.assert_code(report, "SEMANTIC_RELATION_MISMATCH")

    def test_semantic_first_failure_relation_mismatch(self):
        report = self.mutate_vector("PV0-VAL-015", lambda data: data["identity"].__setitem__("vector_id", "PV0-VAL-016"))
        self.assert_code(report, "SEMANTIC_RELATION_MISMATCH")

    def test_cross_vector_single_semantic_failure_continues(self):
        report = self.mutate_vector("PV0-VAL-001A", lambda data: data["source"].__setitem__("source_scenario", 2))
        summary = report.report_dict()["summary"]
        self.assertEqual(37, summary["semantic_pass_count"])
        self.assertEqual(1, summary["semantic_fail_count"])
        self.assertEqual(0, summary["semantic_not_run_count"])
        self.assertEqual(5, report.exit_code)

    def test_cross_vector_layer0_and_semantic_failures_continue(self):
        with self.copied_repository() as root:
            layer0_path = self.vector_path(root, "PV0-VAL-002")
            layer0_path.write_bytes(b"\xef\xbb\xbf" + layer0_path.read_bytes())
            semantic_path = self.vector_path(root, "PV0-VAL-001A")
            semantic = load_json(semantic_path)
            semantic["source"]["source_scenario"] = 2
            save_json(semantic_path, semantic)
            self.refresh_manifest_vector(root, "PV0-VAL-001A")
            self.refresh_manifest_vector(root, "PV0-VAL-002")
            report = self.run_validator(root, self.refresh_table_manifest_source(root))
            summary = report.report_dict()["summary"]
            self.assertEqual(3, report.exit_code)
            self.assertEqual(36, summary["semantic_pass_count"])
            self.assertEqual(1, summary["semantic_fail_count"])
            self.assertEqual(1, summary["semantic_not_run_count"])
            self.assertEqual("NOT_RUN", summary["coverage_result"])
            self.assertIn("LAYER0", {item.family for item in report.diagnostics})
            self.assertIn("SEMANTIC", {item.family for item in report.diagnostics})

    def test_cross_vector_schema_and_semantic_failures_continue(self):
        with self.copied_repository() as root:
            schema_path = self.vector_path(root, "PV0-VAL-002")
            schema = load_json(schema_path)
            schema["identity"]["schema_version"] = 2
            save_json(schema_path, schema)
            semantic_path = self.vector_path(root, "PV0-VAL-001A")
            semantic = load_json(semantic_path)
            semantic["source"]["source_scenario"] = 2
            save_json(semantic_path, semantic)
            self.refresh_manifest_vector(root, "PV0-VAL-001A")
            self.refresh_manifest_vector(root, "PV0-VAL-002")
            report = self.run_validator(root, self.refresh_table_manifest_source(root))
            summary = report.report_dict()["summary"]
            self.assertEqual(4, report.exit_code)
            self.assertEqual(36, summary["semantic_pass_count"])
            self.assertEqual(1, summary["semantic_fail_count"])
            self.assertEqual(1, summary["semantic_not_run_count"])
            self.assertEqual("NOT_RUN", summary["coverage_result"])
            self.assertIn("SCHEMA", {item.family for item in report.diagnostics})
            self.assertIn("SEMANTIC", {item.family for item in report.diagnostics})

    def test_a0_accepted_sequence_set_mismatch(self):
        actuals = copy.deepcopy(self.positive_actuals)
        actuals[0]["accepted_command_sequence_updated"] = False
        result, diagnostics = PHASE2.validate_aggregate_coverage(actuals)
        self.assertEqual("FAIL", result)
        self.assertIn("COVERAGE_ACCEPTED_SEQUENCE_SET_MISMATCH", {item.code for item in diagnostics})

    def test_a0_temporal_set_mismatch(self):
        actuals = copy.deepcopy(self.positive_actuals)
        next(item for item in actuals if item["vector_id"] == "PV0-VAL-004")["temporal_required"] = False
        result, diagnostics = PHASE2.validate_aggregate_coverage(actuals)
        self.assertEqual("FAIL", result)
        self.assertIn("COVERAGE_TEMPORAL_SET_MISMATCH", {item.code for item in diagnostics})

    def test_a0_split_profile_set_mismatch(self):
        actuals = copy.deepcopy(self.positive_actuals)
        actuals[1]["profile"] = "one_side_test"
        result, diagnostics = PHASE2.validate_aggregate_coverage(actuals)
        self.assertEqual("FAIL", result)
        self.assertIn("COVERAGE_PROFILE_SET_MISMATCH", {item.code for item in diagnostics})

    def test_a0_duplicate_id(self):
        actuals = copy.deepcopy(self.positive_actuals)
        actuals[1]["vector_id"] = actuals[0]["vector_id"]
        result, diagnostics = PHASE2.validate_aggregate_coverage(actuals)
        self.assertEqual("FAIL", result)
        self.assertIn("COVERAGE_VECTOR_ID_MISMATCH", {item.code for item in diagnostics})

    def test_a0_real_motor_output_true(self):
        actuals = copy.deepcopy(self.positive_actuals)
        actuals[0]["real_motor_output_enabled"] = True
        result, diagnostics = PHASE2.validate_aggregate_coverage(actuals)
        self.assertEqual("FAIL", result)
        self.assertIn("COVERAGE_REAL_MOTOR_OUTPUT_VIOLATION", {item.code for item in diagnostics})

    def test_a0_only_failure_returns_exit_6(self):
        diagnostic = PHASE2.Diagnostic("COVERAGE", "COVERAGE_VECTOR_COUNT_MISMATCH", "A0", message="injected aggregate mismatch")
        with mock.patch.object(PHASE2, "validate_aggregate_coverage", return_value=("FAIL", [diagnostic])):
            report = self.run_validator(REPOSITORY_ROOT)
        self.assertEqual(6, report.exit_code)
        self.assertEqual("FAIL", report.coverage_result)

    def test_internal_error_is_not_disguised(self):
        with mock.patch.object(PHASE2, "validate_rule_table_raw", side_effect=RuntimeError("injected")):
            report = self.run_validator(REPOSITORY_ROOT)
        self.assertEqual(7, report.exit_code)
        self.assertEqual("FAIL", report.report_dict()["full_validator_result"])
        self.assertIn("INTERNAL", {item.family for item in report.diagnostics})

    def test_report_path_inside_repository_is_rejected(self):
        with self.copied_repository() as root:
            output = root / "forbidden-report.json"
            arguments = [
                "--repository-root", str(root),
                "--toolchain-marker", str(MARKER),
                "--toolchain-marker-sha256", MARKER_SHA256,
                "--json-report", str(output),
            ]
            with redirect_stdout(io.StringIO()):
                exit_code = PHASE2.main(arguments)
            self.assertEqual(7, exit_code)
            self.assertFalse(output.exists())

    def test_z_repository_files_are_unchanged_and_no_bytecode_exists(self):
        hashes_after = {
            path.relative_to(REPOSITORY_ROOT).as_posix(): digest(path)
            for path in (REPOSITORY_ROOT / "software/rover_control").rglob("*")
            if path.is_file()
        }
        self.assertEqual(self.repository_hashes_before, hashes_after)
        self.assertFalse(any((REPOSITORY_ROOT / "software/rover_control").rglob("*.pyc")))
        self.assertFalse(any((REPOSITORY_ROOT / "software/rover_control").rglob("__pycache__")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
