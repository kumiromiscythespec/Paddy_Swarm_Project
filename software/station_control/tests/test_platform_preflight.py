"""Standard-library tests for the ST-002 platform preflight."""

from __future__ import annotations

import ast
from contextlib import redirect_stdout
import getpass
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sqlite3
import sys
import tempfile
import types
import unittest
from unittest import mock


STATION_CONTROL_ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_PATH = STATION_CONTROL_ROOT / "station" / "platform_preflight.py"
SCHEMA_PATH = STATION_CONTROL_ROOT / "schemas" / "platform-preflight-report.schema.json"
GITATTRIBUTES_PATH = STATION_CONTROL_ROOT / ".gitattributes"

SPEC = importlib.util.spec_from_file_location("station_platform_preflight", IMPLEMENTATION_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load the platform preflight module.")
PREFLIGHT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PREFLIGHT
SPEC.loader.exec_module(PREFLIGHT)


class PlatformPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="st002-test-")
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.data = self.root / "data"
        self.reports = self.root / "reports"
        self.repository.mkdir()
        self.data.mkdir()
        self.reports.mkdir()
        self.arguments = PREFLIGHT.CliArguments(
            repository_root=self.repository,
            data_directory=self.data,
            profile="development-host",
            json_report=self.reports / "platform-preflight.json",
            text_report=self.reports / "platform-preflight.txt",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _positive_report(self) -> object:
        return PREFLIGHT.run_preflight(self.arguments, write_reports=False)

    def _diagnostic_codes(self, diagnostics: tuple[object, ...]) -> set[str]:
        return {item.code for item in diagnostics}

    def test_development_host_positive_result(self) -> None:
        report = self._positive_report()
        self.assertEqual(report.document["result"], "PASS")

    def test_positive_exit_code_zero(self) -> None:
        self.assertEqual(self._positive_report().exit_code, 0)

    def test_root_property_order(self) -> None:
        self.assertEqual(
            list(self._positive_report().document),
            [
                "report_version", "phase", "profile", "result", "runtime",
                "platform", "resources", "clock", "storage", "sqlite",
                "temperature", "safety", "summary", "diagnostics", "exit_code",
            ],
        )

    def test_nested_property_order(self) -> None:
        document = self._positive_report().document
        expected = {
            "runtime": [
                "python_version", "python_implementation", "minimum_python_version",
                "python_requirement_satisfied", "standard_library_only",
            ],
            "platform": [
                "system", "release", "machine", "linux_required",
                "linux_requirement_satisfied", "orange_pi_hardware_validation",
            ],
            "resources": [
                "logical_cpu_count", "minimum_logical_cpu_count",
                "cpu_requirement_satisfied", "total_memory_bytes",
                "minimum_memory_bytes", "memory_requirement_satisfied",
                "filesystem_total_bytes", "minimum_free_bytes",
                "free_space_requirement_satisfied",
            ],
            "clock": ["monotonic_available", "monotonic", "adjustable", "resolution_ns"],
            "storage": [
                "data_directory_outside_repository", "write_test_performed",
                "write_test_passed", "readback_match", "cleanup_passed",
                "persistent_test_file_created",
            ],
            "sqlite": [
                "module_available", "sqlite_version", "in_memory_check_passed",
                "database_file_created",
            ],
            "temperature": [
                "adapter", "status", "value_celsius", "hardware_access_performed",
            ],
            "safety": [
                "network_access_performed", "gpio_access_performed",
                "hardware_output_performed", "motor_control_performed",
                "charging_control_performed", "repository_modified",
                "physical_estop_independent",
            ],
            "summary": [
                "check_count", "pass_count", "fail_count", "unavailable_count",
                "next_phase_eligible",
            ],
        }
        for name, keys in expected.items():
            self.assertEqual(list(document[name]), keys)

    def test_positive_report_conforms_to_declared_schema_shape(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        document = self._positive_report().document
        self.assertEqual(set(document), set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])
        for name in (
            "runtime", "platform", "resources", "clock", "storage", "sqlite",
            "temperature", "safety", "summary",
        ):
            definition = schema["$defs"][name]
            self.assertEqual(set(document[name]), set(definition["required"]))
            self.assertFalse(definition["additionalProperties"])

    def test_json_report_is_byte_identical(self) -> None:
        report = self._positive_report()
        self.assertEqual(
            PREFLIGHT.render_json_report(report).encode("utf-8"),
            PREFLIGHT.render_json_report(report).encode("utf-8"),
        )

    def test_text_report_is_byte_identical(self) -> None:
        report = self._positive_report()
        self.assertEqual(
            PREFLIGHT.render_text_report(report).encode("utf-8"),
            PREFLIGHT.render_text_report(report).encode("utf-8"),
        )

    def test_report_has_no_absolute_input_path(self) -> None:
        rendered = PREFLIGHT.render_json_report(self._positive_report())
        self.assertNotIn(str(self.repository), rendered)
        self.assertNotIn(str(self.data), rendered)

    def test_report_has_no_timestamp_field(self) -> None:
        rendered = PREFLIGHT.render_json_report(self._positive_report()).casefold()
        self.assertNotIn("timestamp", rendered)
        self.assertNotIn("current_time", rendered)

    def test_report_has_no_hostname(self) -> None:
        hostname = platform.node()
        rendered = PREFLIGHT.render_json_report(self._positive_report())
        if hostname:
            self.assertNotIn(hostname, rendered)

    def test_report_has_no_username(self) -> None:
        username = getpass.getuser()
        rendered = PREFLIGHT.render_json_report(self._positive_report())
        if username:
            self.assertNotIn(username, rendered)

    def test_network_access_is_false(self) -> None:
        safety = self._positive_report().document["safety"]
        self.assertFalse(safety["network_access_performed"])

    def test_gpio_access_is_false(self) -> None:
        safety = self._positive_report().document["safety"]
        self.assertFalse(safety["gpio_access_performed"])

    def test_hardware_output_is_false(self) -> None:
        safety = self._positive_report().document["safety"]
        self.assertFalse(safety["hardware_output_performed"])

    def test_sqlite_in_memory_passes(self) -> None:
        probe, diagnostics = PREFLIGHT.check_sqlite_in_memory()
        self.assertTrue(probe.module_available)
        self.assertTrue(probe.in_memory_check_passed)
        self.assertEqual(diagnostics, ())

    def test_sqlite_creates_no_database_file(self) -> None:
        before = sorted(path.name for path in self.data.iterdir())
        probe, _ = PREFLIGHT.check_sqlite_in_memory()
        after = sorted(path.name for path in self.data.iterdir())
        self.assertFalse(probe.database_file_created)
        self.assertEqual(before, after)

    def test_data_directory_write_read_delete_passes(self) -> None:
        probe, diagnostics = PREFLIGHT.check_external_data_directory(
            self.repository, self.data
        )
        self.assertTrue(probe.write_test_passed)
        self.assertTrue(probe.readback_match)
        self.assertTrue(probe.cleanup_passed)
        self.assertEqual(diagnostics, ())

    def test_data_directory_leaves_no_probe_file(self) -> None:
        PREFLIGHT.check_external_data_directory(self.repository, self.data)
        self.assertEqual(list(self.data.iterdir()), [])

    def test_temperature_is_not_implemented_stub(self) -> None:
        probe, diagnostics = PREFLIGHT.read_temperature_stub()
        self.assertEqual(probe.adapter, "stub")
        self.assertEqual(probe.status, "NOT_IMPLEMENTED")
        self.assertEqual(probe.value_celsius, "")
        self.assertFalse(probe.hardware_access_performed)
        self.assertEqual(diagnostics[0].severity, "WARNING")

    def test_orange_pi_hardware_validation_not_performed(self) -> None:
        probe, _ = PREFLIGHT.collect_platform("orange-pi-zero-512", system="Linux")
        self.assertEqual(probe.orange_pi_hardware_validation, "NOT_PERFORMED")

    def test_repository_inventory_unchanged_by_positive_run(self) -> None:
        before = sorted(path.relative_to(self.repository) for path in self.repository.rglob("*"))
        PREFLIGHT.run_preflight(self.arguments, write_reports=True)
        after = sorted(path.relative_to(self.repository) for path in self.repository.rglob("*"))
        self.assertEqual(before, after)

    def test_gitattributes_exact(self) -> None:
        expected = (
            "*.md text eol=lf\n"
            "*.toml text eol=lf\n"
            "*.py text eol=lf\n"
            "*.json text eol=lf\n"
            "*.jsonl text eol=lf\n"
            "*.sql text eol=lf\n"
            "*.txt text eol=lf\n"
        )
        self.assertEqual(GITATTRIBUTES_PATH.read_text(encoding="utf-8"), expected)

    def test_invalid_profile(self) -> None:
        arguments = PREFLIGHT.CliArguments(
            self.repository, self.data, "invalid-profile",
            self.arguments.json_report, self.arguments.text_report,
        )
        codes = self._diagnostic_codes(PREFLIGHT.validate_arguments(arguments))
        self.assertIn("PREFLIGHT_INVALID_ARGUMENT", codes)

    def test_missing_repository_root(self) -> None:
        arguments = PREFLIGHT.CliArguments(
            self.root / "missing", self.data, "development-host",
            self.arguments.json_report, self.arguments.text_report,
        )
        codes = self._diagnostic_codes(PREFLIGHT.validate_arguments(arguments))
        self.assertIn("PREFLIGHT_REPOSITORY_ROOT_INVALID", codes)

    def test_repository_root_file_is_invalid(self) -> None:
        root_file = self.root / "root-file"
        root_file.write_text("x", encoding="utf-8")
        arguments = PREFLIGHT.CliArguments(
            root_file, self.data, "development-host",
            self.arguments.json_report, self.arguments.text_report,
        )
        codes = self._diagnostic_codes(PREFLIGHT.validate_arguments(arguments))
        self.assertIn("PREFLIGHT_REPOSITORY_ROOT_INVALID", codes)

    def test_missing_data_directory(self) -> None:
        arguments = PREFLIGHT.CliArguments(
            self.repository, self.root / "missing-data", "development-host",
            self.arguments.json_report, self.arguments.text_report,
        )
        codes = self._diagnostic_codes(PREFLIGHT.validate_arguments(arguments))
        self.assertIn("PREFLIGHT_DATA_DIRECTORY_INVALID", codes)

    def test_data_directory_file_is_invalid(self) -> None:
        data_file = self.root / "data-file"
        data_file.write_text("x", encoding="utf-8")
        arguments = PREFLIGHT.CliArguments(
            self.repository, data_file, "development-host",
            self.arguments.json_report, self.arguments.text_report,
        )
        codes = self._diagnostic_codes(PREFLIGHT.validate_arguments(arguments))
        self.assertIn("PREFLIGHT_DATA_DIRECTORY_INVALID", codes)

    def test_data_directory_inside_repository_is_invalid(self) -> None:
        inside = self.repository / "data"
        inside.mkdir()
        arguments = PREFLIGHT.CliArguments(
            self.repository, inside, "development-host",
            self.arguments.json_report, self.arguments.text_report,
        )
        codes = self._diagnostic_codes(PREFLIGHT.validate_arguments(arguments))
        self.assertIn("PREFLIGHT_DATA_DIRECTORY_INSIDE_REPOSITORY", codes)

    def test_json_report_inside_repository_is_invalid(self) -> None:
        arguments = PREFLIGHT.CliArguments(
            self.repository, self.data, "development-host",
            self.repository / "report.json", self.arguments.text_report,
        )
        codes = self._diagnostic_codes(PREFLIGHT.validate_arguments(arguments))
        self.assertIn("PREFLIGHT_REPORT_PATH_INSIDE_REPOSITORY", codes)

    def test_text_report_inside_repository_is_invalid(self) -> None:
        arguments = PREFLIGHT.CliArguments(
            self.repository, self.data, "development-host",
            self.arguments.json_report, self.repository / "report.txt",
        )
        codes = self._diagnostic_codes(PREFLIGHT.validate_arguments(arguments))
        self.assertIn("PREFLIGHT_REPORT_PATH_INSIDE_REPOSITORY", codes)

    def test_report_parent_missing_is_invalid(self) -> None:
        missing_parent = self.root / "missing-reports"
        arguments = PREFLIGHT.CliArguments(
            self.repository, self.data, "development-host",
            missing_parent / "report.json", missing_parent / "report.txt",
        )
        codes = self._diagnostic_codes(PREFLIGHT.validate_arguments(arguments))
        self.assertIn("PREFLIGHT_REPORT_PARENT_INVALID", codes)

    def test_python_version_below_minimum(self) -> None:
        probe, diagnostics = PREFLIGHT.collect_runtime((3, 10, 9), "CPython")
        self.assertFalse(probe.python_requirement_satisfied)
        self.assertIn("PYTHON_VERSION_UNSUPPORTED", self._diagnostic_codes(diagnostics))

    def test_orange_pi_profile_rejects_non_linux(self) -> None:
        probe, diagnostics = PREFLIGHT.collect_platform(
            "orange-pi-zero-512", system="Windows", release="test", machine="test"
        )
        self.assertFalse(probe.linux_requirement_satisfied)
        self.assertIn("OPERATING_SYSTEM_UNSUPPORTED", self._diagnostic_codes(diagnostics))

    def test_cpu_count_zero_fails(self) -> None:
        usage = types.SimpleNamespace(total=1000000000, free=600000000)
        probe, diagnostics = PREFLIGHT.collect_resources(
            self.data, "development-host", "test", cpu_count=0,
            total_memory_bytes=500000000, disk_usage=lambda _: usage,
        )
        self.assertFalse(probe.cpu_requirement_satisfied)
        self.assertIn("LOGICAL_CPU_BELOW_MINIMUM", self._diagnostic_codes(diagnostics))

    def test_memory_below_minimum_fails(self) -> None:
        usage = types.SimpleNamespace(total=1000000000, free=600000000)
        probe, diagnostics = PREFLIGHT.collect_resources(
            self.data, "development-host", "test", cpu_count=1,
            total_memory_bytes=1, disk_usage=lambda _: usage,
        )
        self.assertFalse(probe.memory_requirement_satisfied)
        self.assertIn("MEMORY_BELOW_MINIMUM", self._diagnostic_codes(diagnostics))

    def test_orange_pi_memory_unavailable_fails(self) -> None:
        usage = types.SimpleNamespace(total=1000000000, free=600000000)
        with mock.patch.object(PREFLIGHT, "get_total_memory_bytes", return_value=None):
            probe, diagnostics = PREFLIGHT.collect_resources(
                self.data, "orange-pi-zero-512", "Linux", cpu_count=1,
                disk_usage=lambda _: usage,
            )
        self.assertFalse(probe.memory_requirement_satisfied)
        diagnostic = next(item for item in diagnostics if item.code == "MEMORY_UNAVAILABLE")
        self.assertEqual(diagnostic.severity, "ERROR")

    def test_development_memory_unavailable_is_warning(self) -> None:
        usage = types.SimpleNamespace(total=1000000000, free=600000000)
        with mock.patch.object(PREFLIGHT, "get_total_memory_bytes", return_value=None):
            probe, diagnostics = PREFLIGHT.collect_resources(
                self.data, "development-host", "test", cpu_count=1,
                disk_usage=lambda _: usage,
            )
        self.assertIsNone(probe.memory_requirement_satisfied)
        diagnostic = next(item for item in diagnostics if item.code == "MEMORY_UNAVAILABLE")
        self.assertEqual(diagnostic.severity, "WARNING")

    def test_disk_free_below_minimum_fails(self) -> None:
        usage = types.SimpleNamespace(total=1000000000, free=1)
        probe, diagnostics = PREFLIGHT.collect_resources(
            self.data, "development-host", "test", cpu_count=1,
            total_memory_bytes=500000000, disk_usage=lambda _: usage,
        )
        self.assertFalse(probe.free_space_requirement_satisfied)
        self.assertIn("DISK_SPACE_BELOW_MINIMUM", self._diagnostic_codes(diagnostics))

    def test_monotonic_unavailable_fails(self) -> None:
        probe, diagnostics = PREFLIGHT.check_monotonic_clock(object())
        self.assertFalse(probe.monotonic_available)
        self.assertIn("MONOTONIC_CLOCK_UNAVAILABLE", self._diagnostic_codes(diagnostics))

    def test_data_directory_write_failure(self) -> None:
        with mock.patch.object(PREFLIGHT.tempfile, "NamedTemporaryFile", side_effect=OSError):
            probe, diagnostics = PREFLIGHT.check_external_data_directory(
                self.repository, self.data
            )
        self.assertFalse(probe.write_test_passed)
        self.assertIn("DATA_DIRECTORY_WRITE_FAILED", self._diagnostic_codes(diagnostics))

    def test_data_directory_readback_mismatch(self) -> None:
        with mock.patch.object(Path, "read_bytes", return_value=b"mismatch"):
            probe, diagnostics = PREFLIGHT.check_external_data_directory(
                self.repository, self.data
            )
        self.assertFalse(probe.readback_match)
        self.assertIn("DATA_DIRECTORY_READBACK_FAILED", self._diagnostic_codes(diagnostics))

    def test_data_directory_cleanup_failure(self) -> None:
        with mock.patch.object(Path, "unlink", side_effect=OSError):
            probe, diagnostics = PREFLIGHT.check_external_data_directory(
                self.repository, self.data
            )
        self.assertFalse(probe.cleanup_passed)
        self.assertTrue(probe.persistent_test_file_created)
        self.assertIn("DATA_DIRECTORY_CLEANUP_FAILED", self._diagnostic_codes(diagnostics))
        for path in self.data.iterdir():
            os.remove(path)

    def test_sqlite_unavailable(self) -> None:
        probe, diagnostics = PREFLIGHT.check_sqlite_in_memory(connect=None)
        self.assertFalse(probe.module_available)
        self.assertIn("SQLITE_MODULE_UNAVAILABLE", self._diagnostic_codes(diagnostics))

    def test_sqlite_in_memory_failure(self) -> None:
        def failing_connect(_: str) -> object:
            raise sqlite3.OperationalError("expected test failure")

        probe, diagnostics = PREFLIGHT.check_sqlite_in_memory(connect=failing_connect)
        self.assertFalse(probe.in_memory_check_passed)
        self.assertIn("SQLITE_IN_MEMORY_CHECK_FAILED", self._diagnostic_codes(diagnostics))

    def test_report_write_failure(self) -> None:
        with mock.patch.object(PREFLIGHT, "write_external_report", side_effect=OSError):
            report = PREFLIGHT.run_preflight(self.arguments, write_reports=True)
        self.assertEqual(report.exit_code, 7)
        codes = {item["code"] for item in report.document["diagnostics"]}
        self.assertIn("REPORT_WRITE_FAILED", codes)

    def test_unexpected_internal_exception_returns_seven(self) -> None:
        argv = [
            "--repository-root", str(self.repository),
            "--data-directory", str(self.data),
            "--profile", "development-host",
            "--json-report", str(self.arguments.json_report),
            "--text-report", str(self.arguments.text_report),
        ]
        output = io.StringIO()
        with mock.patch.object(PREFLIGHT, "collect_runtime", side_effect=RuntimeError):
            with redirect_stdout(output):
                exit_code = PREFLIGHT.main(argv)
        self.assertEqual(exit_code, 7)
        self.assertIn("result=FAIL", output.getvalue())

    def test_temperature_warning_does_not_fail(self) -> None:
        report = self._positive_report()
        codes = {item["code"] for item in report.document["diagnostics"]}
        self.assertIn("TEMPERATURE_NOT_IMPLEMENTED", codes)
        self.assertEqual(report.exit_code, 0)

    def test_exit_code_priority_path_before_resource(self) -> None:
        diagnostics = (
            PREFLIGHT.Diagnostic("ERROR", "MEMORY_BELOW_MINIMUM", "resources", "x"),
            PREFLIGHT.Diagnostic("ERROR", "PREFLIGHT_INVALID_ARGUMENT", "arguments", "x"),
        )
        self.assertEqual(PREFLIGHT.determine_exit_code(diagnostics), 2)

    def test_exit_code_platform_is_three(self) -> None:
        diagnostics = (
            PREFLIGHT.Diagnostic("ERROR", "OPERATING_SYSTEM_UNSUPPORTED", "platform", "x"),
        )
        self.assertEqual(PREFLIGHT.determine_exit_code(diagnostics), 3)

    def test_exit_code_resource_is_four(self) -> None:
        diagnostics = (
            PREFLIGHT.Diagnostic("ERROR", "MEMORY_BELOW_MINIMUM", "resources", "x"),
        )
        self.assertEqual(PREFLIGHT.determine_exit_code(diagnostics), 4)

    def test_exit_code_clock_sqlite_is_five(self) -> None:
        diagnostics = (
            PREFLIGHT.Diagnostic("ERROR", "SQLITE_IN_MEMORY_CHECK_FAILED", "sqlite", "x"),
        )
        self.assertEqual(PREFLIGHT.determine_exit_code(diagnostics), 5)

    def test_internal_error_always_returns_seven(self) -> None:
        diagnostics = (
            PREFLIGHT.Diagnostic("ERROR", "PREFLIGHT_INVALID_ARGUMENT", "arguments", "x"),
            PREFLIGHT.Diagnostic("ERROR", "INTERNAL_VALIDATOR_ERROR", "validator", "x"),
        )
        self.assertEqual(PREFLIGHT.determine_exit_code(diagnostics), 7)

    def test_diagnostics_are_sorted(self) -> None:
        report = self._positive_report().document
        keys = [
            (item["component"], item["code"], item["message"])
            for item in report["diagnostics"]
        ]
        self.assertEqual(keys, sorted(keys))

    def test_text_report_property_order(self) -> None:
        keys = [
            line.split("=", 1)[0]
            for line in PREFLIGHT.render_text_report(self._positive_report()).splitlines()
        ]
        self.assertEqual(
            keys,
            [
                "phase", "profile", "result", "python_result", "platform_result",
                "cpu_result", "memory_result", "disk_result", "monotonic_result",
                "data_directory_result", "sqlite_result", "temperature_result",
                "network_access_performed", "gpio_access_performed",
                "hardware_output_performed", "diagnostic_count", "exit_code",
            ],
        )

    def test_implementation_has_no_prohibited_import(self) -> None:
        tree = ast.parse(IMPLEMENTATION_PATH.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        prohibited = {
            "socket", "requests", "urllib", "http.client", "aiohttp", "paramiko",
            "serial", "RPi.GPIO", "OPi.GPIO", "gpiod", "smbus", "spidev",
            "subprocess",
        }
        self.assertFalse(imports.intersection(prohibited))

    def test_implementation_has_no_hardware_device_path(self) -> None:
        source = IMPLEMENTATION_PATH.read_text(encoding="utf-8")
        for path in (
            "/sys/class/gpio", "/sys/class/thermal", "/dev/gpiochip", "/dev/i2c",
            "/dev/tty", "/dev/spidev",
        ):
            self.assertNotIn(path, source)

    def test_no_bytecode_created_by_module_contract(self) -> None:
        self.assertFalse(any(STATION_CONTROL_ROOT.rglob("__pycache__")))
        self.assertFalse(any(STATION_CONTROL_ROOT.rglob("*.pyc")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
