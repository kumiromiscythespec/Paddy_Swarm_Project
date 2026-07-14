from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


sys.dont_write_bytecode = True
REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
IMPLEMENTATION = REPOSITORY_ROOT / "software/rover_control/protocol/v0/test_vectors/offline_validator/phase1.py"
SPEC = importlib.util.spec_from_file_location("paddy_phase1_under_test", IMPLEMENTATION)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load Phase 1 implementation")
PHASE1 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PHASE1
SPEC.loader.exec_module(PHASE1)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Phase1TestCase(unittest.TestCase):
    maxDiff = None

    @contextlib.contextmanager
    def temporary_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(REPOSITORY_ROOT / "software", root / "software")
            yield root

    def manifest_path(self, root: Path) -> Path:
        return root / PHASE1.DEFAULT_MANIFEST

    def load_manifest(self, root: Path) -> dict:
        return json.loads(self.manifest_path(root).read_text(encoding="utf-8"))

    def save_manifest(self, root: Path, data: dict) -> None:
        self.manifest_path(root).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )

    def run_temp(self, root: Path):
        return PHASE1.run_phase1(root)

    def update_first_vector_measurement(self, root: Path, raw: bytes) -> None:
        self.update_vector_measurement(root, 0, raw)

    def update_vector_measurement(self, root: Path, index: int, raw: bytes) -> None:
        manifest = self.load_manifest(root)
        row = manifest["vectors"][index]
        path = root / row["path"]
        path.write_bytes(raw)
        row["sha256"] = digest(path)
        row["size_bytes"] = len(raw)
        self.save_manifest(root, manifest)

    def mutate_first_vector_json(self, root: Path, mutation) -> None:
        self.mutate_vector_json(root, 0, mutation)

    def mutate_vector_json(self, root: Path, index: int, mutation) -> None:
        manifest = self.load_manifest(root)
        row = manifest["vectors"][index]
        path = root / row["path"]
        data = json.loads(path.read_text(encoding="utf-8"))
        mutation(data)
        raw = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self.update_vector_measurement(root, index, raw)

    def result_counts(self, report):
        return {
            "layer0_pass": sum(item.layer0_result == "PASS" for item in report.vectors),
            "layer0_fail": sum(item.layer0_result == "FAIL" for item in report.vectors),
            "schema_pass": sum(item.schema_result == "PASS" for item in report.vectors),
            "schema_fail": sum(item.schema_result == "FAIL" for item in report.vectors),
            "schema_not_run": sum(item.schema_result == "NOT_RUN" for item in report.vectors),
        }

    def assert_exit(self, root: Path, code: int, family: str | None = None, diagnostic: str | None = None):
        report = self.run_temp(root)
        self.assertEqual(code, report.exit_code, PHASE1.render_json_report(report))
        if family is not None:
            self.assertIn(family, {item.family for item in report.diagnostics})
        if diagnostic is not None:
            self.assertIn(diagnostic, {item.code for item in report.diagnostics})
        return report

    def test_positive_formal_repository(self):
        report = PHASE1.run_phase1(REPOSITORY_ROOT)
        self.assertEqual(0, report.exit_code)
        self.assertEqual("PASS", report.phase1_result)

    def test_positive_manifest_entry_count(self):
        report = PHASE1.run_phase1(REPOSITORY_ROOT)
        self.assertEqual(38, report.manifest["vector_entry_count"])

    def test_positive_vector_hash_and_size_preflight(self):
        report = PHASE1.run_phase1(REPOSITORY_ROOT)
        self.assertEqual("PASS", report.manifest["result"])
        self.assertEqual([], report.diagnostics)

    def test_positive_layer0_all_vectors(self):
        report = PHASE1.run_phase1(REPOSITORY_ROOT)
        self.assertEqual(38, sum(item.layer0_result == "PASS" for item in report.vectors))

    def test_positive_schema_all_vectors(self):
        report = PHASE1.run_phase1(REPOSITORY_ROOT)
        self.assertEqual(38, sum(item.schema_result == "PASS" for item in report.vectors))

    def test_positive_phase_boundary(self):
        data = PHASE1.run_phase1(REPOSITORY_ROOT).report_dict()
        self.assertEqual("NOT_AVAILABLE", data["full_validator_result"])
        self.assertEqual("NOT_RUN", data["summary"]["semantic_result"])
        self.assertEqual("LAYER2_NOT_IMPLEMENTED_IN_PHASE1", data["summary"]["semantic_reason"])

    def test_positive_json_report_is_byte_identical(self):
        first = PHASE1.render_json_report(PHASE1.run_phase1(REPOSITORY_ROOT))
        second = PHASE1.render_json_report(PHASE1.run_phase1(REPOSITORY_ROOT))
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))

    def test_positive_text_summary_fields(self):
        text = PHASE1.render_text_report(PHASE1.run_phase1(REPOSITORY_ROOT))
        for field in (
            "phase1_result", "full_validator_result", "manifest_result",
            "schema_artifact_result", "vector_count", "layer0_pass_count",
            "layer0_fail_count", "schema_pass_count", "schema_fail_count",
            "semantic_result", "diagnostic_count", "exit_code",
        ):
            self.assertIn(field + "=", text)

    def test_positive_json_report_has_no_nondeterministic_metadata(self):
        report = PHASE1.render_json_report(PHASE1.run_phase1(REPOSITORY_ROOT))
        self.assertNotIn("timestamp", report.lower())
        self.assertNotIn(str(REPOSITORY_ROOT), report)
        self.assertNotIn("toolchain_marker_path", report)

    def test_positive_repository_is_not_modified(self):
        files = [path for path in (REPOSITORY_ROOT / "software").rglob("*") if path.is_file()]
        before = {path: digest(path) for path in files}
        PHASE1.run_phase1(REPOSITORY_ROOT)
        after = {path: digest(path) for path in files}
        self.assertEqual(before, after)

    def test_positive_marker_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "marker.txt"
            marker.write_text("ready\n", encoding="utf-8", newline="\n")
            report = PHASE1.run_phase1(REPOSITORY_ROOT, marker=marker, marker_sha256=digest(marker))
            self.assertEqual(0, report.exit_code)
            self.assertEqual("PASS", report.toolchain["toolchain_marker_result"])

    def test_positive_report_inside_repository_is_rejected(self):
        with self.assertRaises(ValueError):
            PHASE1._write_external_report(REPOSITORY_ROOT, REPOSITORY_ROOT / "forbidden-report.json", "{}\n")

    def test_layer0_failure_does_not_skip_schema_for_other_vectors(self):
        with self.temporary_repository() as root:
            manifest = self.load_manifest(root)
            failed_path = root / manifest["vectors"][0]["path"]
            self.update_vector_measurement(root, 0, b"\xef\xbb\xbf" + failed_path.read_bytes())
            report = self.assert_exit(root, 3, "LAYER0", "BOM_FORBIDDEN")
        self.assertEqual(
            {"layer0_pass": 37, "layer0_fail": 1, "schema_pass": 37, "schema_fail": 0, "schema_not_run": 1},
            self.result_counts(report),
        )
        self.assertEqual(("FAIL", "NOT_RUN"), (report.vectors[0].layer0_result, report.vectors[0].schema_result))
        self.assertTrue(all(item.layer0_result == "PASS" and item.schema_result == "PASS" for item in report.vectors[1:]))
        self.assertEqual({"LAYER0"}, {item.family for item in report.diagnostics})

    def test_layer0_and_schema_failures_are_both_reported(self):
        with self.temporary_repository() as root:
            manifest = self.load_manifest(root)
            failed_path = root / manifest["vectors"][0]["path"]
            self.update_vector_measurement(root, 0, b"\xef\xbb\xbf" + failed_path.read_bytes())
            self.mutate_vector_json(
                root, 1,
                lambda data: data["profile_and_capability"].__setitem__("real_motor_output_enabled", True),
            )
            report = self.assert_exit(root, 3)
        self.assertEqual(
            {"layer0_pass": 37, "layer0_fail": 1, "schema_pass": 36, "schema_fail": 1, "schema_not_run": 1},
            self.result_counts(report),
        )
        self.assertEqual(("FAIL", "NOT_RUN"), (report.vectors[0].layer0_result, report.vectors[0].schema_result))
        self.assertEqual(("PASS", "FAIL"), (report.vectors[1].layer0_result, report.vectors[1].schema_result))
        self.assertTrue(all(item.layer0_result == "PASS" and item.schema_result == "PASS" for item in report.vectors[2:]))
        self.assertEqual({"LAYER0", "SCHEMA"}, {item.family for item in report.diagnostics})

    def test_manifest_negative_missing_and_symlink(self):
        with self.temporary_repository() as root:
            self.manifest_path(root).unlink()
            self.assert_exit(root, 2, "MANIFEST", "MANIFEST_NOT_FOUND")
        with self.temporary_repository() as root:
            target = self.manifest_path(root)
            with mock.patch.object(PHASE1, "path_is_symlink", side_effect=lambda path: path == target):
                self.assert_exit(root, 2, "MANIFEST", "MANIFEST_SYMLINK_FORBIDDEN")

    def test_manifest_negative_raw_encoding_and_line_endings(self):
        mutations = {
            "bom": lambda raw: b"\xef\xbb\xbf" + raw,
            "cr": lambda raw: raw.replace(b"\n", b"\r\n", 1),
            "missing_lf": lambda raw: raw.rstrip(b"\n"),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), self.temporary_repository() as root:
                path = self.manifest_path(root); path.write_bytes(mutation(path.read_bytes()))
                self.assert_exit(root, 2, "MANIFEST", "MANIFEST_PARSE_ERROR")

    def test_manifest_negative_duplicate_key(self):
        with self.temporary_repository() as root:
            path = self.manifest_path(root)
            path.write_bytes(path.read_bytes().replace(b"{\n", b'{\n  "manifest_version": 1,\n', 1))
            self.assert_exit(root, 2, "MANIFEST", "MANIFEST_DUPLICATE_KEY")

    def test_manifest_negative_root_model_and_order(self):
        for name in ("unknown", "order"):
            with self.subTest(name=name), self.temporary_repository() as root:
                manifest = self.load_manifest(root)
                if name == "unknown": manifest["unknown"] = True
                else:
                    value = manifest.pop("manifest_version"); manifest["manifest_version"] = value
                self.save_manifest(root, manifest)
                self.assert_exit(root, 2, "MANIFEST", "MANIFEST_UNKNOWN_PROPERTY")

    def test_manifest_negative_entry_order_and_duplicates(self):
        for name in ("entry_order", "duplicate_id", "duplicate_path"):
            with self.subTest(name=name), self.temporary_repository() as root:
                manifest = self.load_manifest(root)
                if name == "entry_order": manifest["vectors"][0], manifest["vectors"][1] = manifest["vectors"][1], manifest["vectors"][0]
                elif name == "duplicate_id": manifest["vectors"][1]["vector_id"] = manifest["vectors"][0]["vector_id"]
                else: manifest["vectors"][1]["path"] = manifest["vectors"][0]["path"]
                self.save_manifest(root, manifest)
                self.assert_exit(root, 2, "MANIFEST")

    def test_manifest_negative_path_missing_hash_and_size(self):
        for name in ("traversal", "missing", "hash", "size"):
            with self.subTest(name=name), self.temporary_repository() as root:
                manifest = self.load_manifest(root); row = manifest["vectors"][0]
                if name == "traversal": row["path"] = "../escape.json"
                elif name == "missing": (root / row["path"]).unlink()
                elif name == "hash": row["sha256"] = "0" * 64
                else: row["size_bytes"] += 1
                self.save_manifest(root, manifest)
                self.assert_exit(root, 2, "MANIFEST")

    def test_manifest_negative_source_schema_and_coverage(self):
        for name in ("schema_hash", "source_hash", "accepted", "profile"):
            with self.subTest(name=name), self.temporary_repository() as root:
                manifest = self.load_manifest(root)
                if name == "schema_hash": manifest["vector_schema"]["sha256"] = "0" * 64
                elif name == "source_hash": manifest["source_documents"]["case_catalog"]["sha256"] = "0" * 64
                elif name == "accepted": manifest["vectors"][0]["accepted_command_sequence_updated"] = False
                else: manifest["vectors"][0]["profile"] = "drive_pto_split_fixture"
                self.save_manifest(root, manifest)
                self.assert_exit(root, 2, "MANIFEST")

    def test_manifest_negative_schema_artifact_hash(self):
        with self.temporary_repository() as root:
            manifest = self.load_manifest(root)
            schema = root / manifest["vector_schema"]["path"]
            schema.write_bytes(schema.read_bytes() + b" ")
            self.assert_exit(root, 2, "MANIFEST", "MANIFEST_SCHEMA_HASH_MISMATCH")

    def test_layer0_negative_utf8_bom_and_cr(self):
        mutations = {
            "utf8": lambda raw: raw[:-1] + b"\xff\n",
            "bom": lambda raw: b"\xef\xbb\xbf" + raw,
            "cr": lambda raw: raw.replace(b"\n", b"\r\n", 1),
        }
        self._run_layer0_raw_cases(mutations)

    def test_layer0_negative_newlines_and_whitespace(self):
        mutations = {
            "missing_lf": lambda raw: raw.rstrip(b"\n"),
            "multiple_lf": lambda raw: raw + b"\n",
            "trailing_space": lambda raw: raw.replace(b"{\n", b"{ \n", 1),
        }
        self._run_layer0_raw_cases(mutations)

    def test_layer0_negative_duplicate_and_root_array(self):
        mutations = {
            "duplicate": lambda raw: raw.replace(b"{\n", b'{\n  "identity": {},\n', 1),
            "root_array": lambda raw: b"[]\n",
        }
        self._run_layer0_raw_cases(mutations)

    def test_layer0_negative_number_formats(self):
        mutations = {
            "decimal": lambda raw: raw.replace(b'"schema_version": 1', b'"schema_version": 1.0', 1),
            "exponent": lambda raw: raw.replace(b'"schema_version": 1', b'"schema_version": 1e0', 1),
            "leading_plus": lambda raw: raw.replace(b'"schema_version": 1', b'"schema_version": +1', 1),
            "leading_zero": lambda raw: raw.replace(b'"schema_version": 1', b'"schema_version": 01', 1),
            "negative": lambda raw: raw.replace(b'"schema_version": 1', b'"schema_version": -1', 1),
            "safe_range": lambda raw: raw.replace(b'"monotonic_time_ms": 10000', b'"monotonic_time_ms": 9007199254740992', 1),
        }
        self._run_layer0_raw_cases(mutations)

    def test_layer0_negative_null_and_stage_order(self):
        with self.temporary_repository() as root:
            manifest = self.load_manifest(root); path = root / manifest["vectors"][0]["path"]
            raw = path.read_bytes().replace(b'"schema_version": 1', b'"schema_version": null', 1)
            self.update_first_vector_measurement(root, raw)
            self.assert_exit(root, 3, "LAYER0", "JSON_PARSE_ERROR")
        with self.temporary_repository() as root:
            manifest = self.load_manifest(root); path = root / manifest["vectors"][0]["path"]
            raw = b'[[[[[[[[[[[[[[[[[1.0]]]]]]]]]]]]]]]]]\n'
            self.update_first_vector_measurement(root, raw)
            report = self.assert_exit(root, 3, "LAYER0", "NESTING_DEPTH_EXCEEDED")
            self.assertEqual("L0-10", report.diagnostics[0].stage)

    def test_layer0_negative_container_limits(self):
        def mutate(name, data):
            if name == "depth": data["deep"] = [[[[[[[[[[[[[[[[[0]]]]]]]]]]]]]]]]]
            elif name == "nodes": data["bulk"] = [[0] * 20 for _ in range(20)]
            else: data["wide"] = {f"k{i}": i for i in range(33)}
        for name in ("depth", "nodes", "members"):
            with self.subTest(name=name), self.temporary_repository() as root:
                self.mutate_first_vector_json(root, lambda data, n=name: mutate(n, data))
                self.assert_exit(root, 3, "LAYER0")

    def test_layer0_negative_string_length(self):
        with self.temporary_repository() as root:
            self.mutate_first_vector_json(root, lambda data: data["identity"].__setitem__("title", "x" * 1025))
            self.assert_exit(root, 3, "LAYER0", "STRING_LENGTH_EXCEEDED")

    def _run_layer0_raw_cases(self, mutations):
        for name, mutation in mutations.items():
            with self.subTest(name=name), self.temporary_repository() as root:
                manifest = self.load_manifest(root); path = root / manifest["vectors"][0]["path"]
                self.update_first_vector_measurement(root, mutation(path.read_bytes()))
                self.assert_exit(root, 3, "LAYER0")

    def test_schema_negative_unknown_root(self):
        self._run_schema_case(lambda data: data.__setitem__("unknown", True))

    def test_schema_negative_required_group_missing(self):
        self._run_schema_case(lambda data: data.pop("observability"))

    def test_schema_negative_vector_id_enum(self):
        self._run_schema_case(lambda data: data["identity"].__setitem__("vector_id", "PV0-VAL-999"))

    def test_schema_negative_official_state_enum(self):
        self._run_schema_case(lambda data: data["initial_fixture"].__setitem__("official_state", "INVALID_STATE"))

    def test_schema_negative_scenario_specific_constraint(self):
        self._run_schema_case(lambda data: data["profile_and_capability"].__setitem__("real_motor_output_enabled", True))

    def test_schema_negative_external_ref(self):
        with self.temporary_repository() as root:
            manifest = self.load_manifest(root)
            path = root / manifest["vector_schema"]["path"]
            path.write_text(
                json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "$ref": "https://example.invalid/schema.json"}, indent=2) + "\n",
                encoding="utf-8", newline="\n",
            )
            manifest["vector_schema"]["sha256"] = digest(path)
            _, _, diagnostics = PHASE1.validate_schema_artifact(root, manifest)
            self.assertEqual({"SCHEMA_EXTERNAL_REF_FORBIDDEN"}, {item.code for item in diagnostics})

    def test_schema_negative_meta_validation(self):
        with self.temporary_repository() as root:
            manifest = self.load_manifest(root)
            path = root / manifest["vector_schema"]["path"]
            path.write_text(json.dumps({"type": 1}, indent=2) + "\n", encoding="utf-8", newline="\n")
            manifest["vector_schema"]["sha256"] = digest(path)
            _, _, diagnostics = PHASE1.validate_schema_artifact(root, manifest)
            self.assertEqual({"SCHEMA_META_VALIDATION_FAILED"}, {item.code for item in diagnostics})

    def _run_schema_case(self, mutation):
        with self.temporary_repository() as root:
            self.mutate_first_vector_json(root, mutation)
            report = self.assert_exit(root, 4, "SCHEMA", "SCHEMA_VALIDATION_FAILED")
            self.assertEqual(38, sum(item.layer0_result == "PASS" for item in report.vectors))

    def test_internal_error_is_not_disguised(self):
        with mock.patch.object(PHASE1, "validate_manifest_raw", side_effect=RuntimeError("forced-internal")):
            report = PHASE1.run_phase1(REPOSITORY_ROOT)
        self.assertEqual(7, report.exit_code)
        self.assertEqual("FAIL", report.phase1_result)
        self.assertEqual({"INTERNAL"}, {item.family for item in report.diagnostics})


if __name__ == "__main__":
    unittest.main(verbosity=2)
