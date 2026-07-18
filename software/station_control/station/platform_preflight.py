"""Deterministic, offline platform preflight for station control ST-002."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
import platform as platform_module
import shutil
import sqlite3
import sys
import tempfile
import time
from typing import Callable, Sequence


REPORT_VERSION = 1
PHASE = "ST-002"
PROFILES = ("development-host", "orange-pi-zero-512")
MINIMUM_PYTHON_VERSION = (3, 11)
MINIMUM_LOGICAL_CPU_COUNT = 1
MINIMUM_MEMORY_BYTES = 402653184
MINIMUM_FREE_BYTES = 536870912
PROBE_CONTENT = b"paddy-swarm-platform-preflight\n"


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    component: str
    message: str


@dataclass(frozen=True)
class RuntimeProbe:
    python_version: str
    python_implementation: str
    minimum_python_version: str
    python_requirement_satisfied: bool
    standard_library_only: bool


@dataclass(frozen=True)
class PlatformProbe:
    system: str
    release: str
    machine: str
    linux_required: bool
    linux_requirement_satisfied: bool
    orange_pi_hardware_validation: str


@dataclass(frozen=True)
class ResourceProbe:
    logical_cpu_count: int
    minimum_logical_cpu_count: int
    cpu_requirement_satisfied: bool
    total_memory_bytes: int
    minimum_memory_bytes: int
    memory_requirement_satisfied: bool | None
    filesystem_total_bytes: int
    minimum_free_bytes: int
    free_space_requirement_satisfied: bool


@dataclass(frozen=True)
class ClockProbe:
    monotonic_available: bool
    monotonic: bool
    adjustable: bool
    resolution_ns: int


@dataclass(frozen=True)
class StorageProbe:
    data_directory_outside_repository: bool
    write_test_performed: bool
    write_test_passed: bool
    readback_match: bool
    cleanup_passed: bool
    persistent_test_file_created: bool


@dataclass(frozen=True)
class SQLiteProbe:
    module_available: bool
    sqlite_version: str
    in_memory_check_passed: bool
    database_file_created: bool


@dataclass(frozen=True)
class TemperatureProbe:
    adapter: str
    status: str
    value_celsius: str
    hardware_access_performed: bool


@dataclass(frozen=True)
class PreflightReport:
    document: dict[str, object]
    exit_code: int


@dataclass(frozen=True)
class CliArguments:
    repository_root: Path
    data_directory: Path
    profile: str
    json_report: Path
    text_report: Path


class DeterministicArgumentParser(argparse.ArgumentParser):
    """Argument parser that reports errors without process-global exit."""

    def error(self, message: str) -> None:
        raise ValueError(message)


def parse_arguments(argv: Sequence[str] | None = None) -> CliArguments:
    parser = DeterministicArgumentParser(
        description="Run the offline ST-002 platform preflight."
    )
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--data-directory", required=True, type=Path)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--json-report", required=True, type=Path)
    parser.add_argument("--text-report", required=True, type=Path)
    values = parser.parse_args(argv)
    return CliArguments(
        repository_root=values.repository_root,
        data_directory=values.data_directory,
        profile=values.profile,
        json_report=values.json_report,
        text_report=values.text_report,
    )


def is_path_contained(candidate: Path, parent: Path) -> bool:
    try:
        candidate_resolved = candidate.resolve(strict=False)
        parent_resolved = parent.resolve(strict=False)
        common = os.path.commonpath((str(candidate_resolved), str(parent_resolved)))
    except (OSError, ValueError):
        return False
    return os.path.normcase(common) == os.path.normcase(str(parent_resolved))


def _diagnostic(severity: str, code: str, component: str, message: str) -> Diagnostic:
    return Diagnostic(severity, code, component, message)


def validate_arguments(arguments: CliArguments) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    repository_root = arguments.repository_root
    data_directory = arguments.data_directory

    if arguments.profile not in PROFILES:
        diagnostics.append(_diagnostic(
            "ERROR",
            "PREFLIGHT_INVALID_ARGUMENT",
            "arguments",
            "Profile is not supported.",
        ))
    if not repository_root.exists() or not repository_root.is_dir():
        diagnostics.append(_diagnostic(
            "ERROR",
            "PREFLIGHT_REPOSITORY_ROOT_INVALID",
            "arguments",
            "Repository root must be an existing directory.",
        ))
    if not data_directory.exists() or not data_directory.is_dir():
        diagnostics.append(_diagnostic(
            "ERROR",
            "PREFLIGHT_DATA_DIRECTORY_INVALID",
            "storage",
            "Data directory must be an existing directory.",
        ))
    elif repository_root.exists() and is_path_contained(data_directory, repository_root):
        diagnostics.append(_diagnostic(
            "ERROR",
            "PREFLIGHT_DATA_DIRECTORY_INSIDE_REPOSITORY",
            "storage",
            "Data directory must be outside the repository.",
        ))

    for report_path in (arguments.json_report, arguments.text_report):
        if repository_root.exists() and is_path_contained(report_path, repository_root):
            diagnostics.append(_diagnostic(
                "ERROR",
                "PREFLIGHT_REPORT_PATH_INSIDE_REPOSITORY",
                "report",
                "Report path must be outside the repository.",
            ))
        if not report_path.parent.exists() or not report_path.parent.is_dir():
            diagnostics.append(_diagnostic(
                "ERROR",
                "PREFLIGHT_REPORT_PARENT_INVALID",
                "report",
                "Report parent must be an existing directory.",
            ))

    if arguments.json_report.resolve(strict=False) == arguments.text_report.resolve(
        strict=False
    ):
        diagnostics.append(_diagnostic(
            "ERROR",
            "PREFLIGHT_INVALID_ARGUMENT",
            "arguments",
            "JSON and text reports must use different paths.",
        ))
    return tuple(sorted(diagnostics, key=_diagnostic_sort_key))


def collect_runtime(
    version_info: tuple[int, int, int] | None = None,
    implementation: str | None = None,
) -> tuple[RuntimeProbe, tuple[Diagnostic, ...]]:
    version = version_info or (
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
    )
    name = implementation or platform_module.python_implementation()
    satisfied = version[:2] >= MINIMUM_PYTHON_VERSION
    probe = RuntimeProbe(
        python_version=".".join(str(part) for part in version),
        python_implementation=name,
        minimum_python_version="3.11",
        python_requirement_satisfied=satisfied,
        standard_library_only=True,
    )
    diagnostics: list[Diagnostic] = []
    if not satisfied:
        diagnostics.append(_diagnostic(
            "ERROR",
            "PYTHON_VERSION_UNSUPPORTED",
            "runtime",
            "Python 3.11 or later is required.",
        ))
    return probe, tuple(diagnostics)


def collect_platform(
    profile: str,
    system: str | None = None,
    release: str | None = None,
    machine: str | None = None,
) -> tuple[PlatformProbe, tuple[Diagnostic, ...]]:
    observed_system = system if system is not None else platform_module.system()
    linux_required = profile == "orange-pi-zero-512"
    linux_satisfied = not linux_required or observed_system == "Linux"
    probe = PlatformProbe(
        system=observed_system,
        release=release if release is not None else platform_module.release(),
        machine=machine if machine is not None else platform_module.machine(),
        linux_required=linux_required,
        linux_requirement_satisfied=linux_satisfied,
        orange_pi_hardware_validation="NOT_PERFORMED",
    )
    diagnostics: list[Diagnostic] = []
    if not linux_satisfied:
        diagnostics.append(_diagnostic(
            "ERROR",
            "OPERATING_SYSTEM_UNSUPPORTED",
            "platform",
            "The Orange Pi profile requires Linux.",
        ))
    return probe, tuple(diagnostics)


def _read_linux_total_memory() -> int | None:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
            if line.startswith("MemTotal:"):
                fields = line.split()
                if len(fields) >= 2:
                    return int(fields[1]) * 1024
    except (OSError, UnicodeError, ValueError):
        return None
    return None


def _read_windows_total_memory() -> int | None:
    try:
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = (
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong),
                ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            )

        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None
        return int(status.total_physical)
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def get_total_memory_bytes(system: str) -> int | None:
    if system == "Linux":
        return _read_linux_total_memory()
    if system == "Windows":
        return _read_windows_total_memory()
    return None


def collect_resources(
    data_directory: Path,
    profile: str,
    system: str,
    cpu_count: int | None = None,
    total_memory_bytes: int | None = None,
    disk_usage: Callable[[Path], object] = shutil.disk_usage,
) -> tuple[ResourceProbe, tuple[Diagnostic, ...]]:
    observed_cpu = os.cpu_count() if cpu_count is None else cpu_count
    logical_cpu_count = int(observed_cpu or 0)
    cpu_satisfied = logical_cpu_count >= MINIMUM_LOGICAL_CPU_COUNT

    observed_memory = (
        get_total_memory_bytes(system)
        if total_memory_bytes is None
        else total_memory_bytes
    )
    memory_value = int(observed_memory or 0)
    if observed_memory is None and profile == "development-host":
        memory_satisfied: bool | None = None
    else:
        memory_satisfied = memory_value >= MINIMUM_MEMORY_BYTES

    try:
        usage = disk_usage(data_directory)
        filesystem_total_bytes = int(getattr(usage, "total"))
        free_bytes = int(getattr(usage, "free"))
    except (OSError, TypeError, ValueError, AttributeError):
        filesystem_total_bytes = 0
        free_bytes = 0
    disk_satisfied = free_bytes >= MINIMUM_FREE_BYTES

    diagnostics: list[Diagnostic] = []
    if not cpu_satisfied:
        diagnostics.append(_diagnostic(
            "ERROR",
            "LOGICAL_CPU_BELOW_MINIMUM",
            "resources",
            "Logical CPU count is below the minimum.",
        ))
    if observed_memory is None:
        severity = "WARNING" if profile == "development-host" else "ERROR"
        diagnostics.append(_diagnostic(
            severity,
            "MEMORY_UNAVAILABLE",
            "resources",
            "Total memory is unavailable through the permitted standard-library probe.",
        ))
    elif not memory_satisfied:
        diagnostics.append(_diagnostic(
            "ERROR",
            "MEMORY_BELOW_MINIMUM",
            "resources",
            "Total memory is below the minimum.",
        ))
    if not disk_satisfied:
        diagnostics.append(_diagnostic(
            "ERROR",
            "DISK_SPACE_BELOW_MINIMUM",
            "resources",
            "Free disk space is below the minimum.",
        ))
    probe = ResourceProbe(
        logical_cpu_count=logical_cpu_count,
        minimum_logical_cpu_count=MINIMUM_LOGICAL_CPU_COUNT,
        cpu_requirement_satisfied=cpu_satisfied,
        total_memory_bytes=memory_value,
        minimum_memory_bytes=MINIMUM_MEMORY_BYTES,
        memory_requirement_satisfied=memory_satisfied,
        filesystem_total_bytes=filesystem_total_bytes,
        minimum_free_bytes=MINIMUM_FREE_BYTES,
        free_space_requirement_satisfied=disk_satisfied,
    )
    return probe, tuple(sorted(diagnostics, key=_diagnostic_sort_key))


def check_monotonic_clock(
    clock_info: object | None = None,
) -> tuple[ClockProbe, tuple[Diagnostic, ...]]:
    try:
        info = clock_info if clock_info is not None else time.get_clock_info("monotonic")
        monotonic = bool(getattr(info, "monotonic"))
        adjustable = bool(getattr(info, "adjustable"))
        resolution_ns = max(0, int(round(float(getattr(info, "resolution")) * 1_000_000_000)))
        available = True
    except (AttributeError, OSError, TypeError, ValueError):
        available = False
        monotonic = False
        adjustable = True
        resolution_ns = 0
    diagnostics: list[Diagnostic] = []
    if not available or not monotonic:
        diagnostics.append(_diagnostic(
            "ERROR",
            "MONOTONIC_CLOCK_UNAVAILABLE",
            "clock",
            "A monotonic clock is unavailable.",
        ))
    return ClockProbe(available, monotonic, adjustable, resolution_ns), tuple(diagnostics)


def check_external_data_directory(
    repository_root: Path,
    data_directory: Path,
) -> tuple[StorageProbe, tuple[Diagnostic, ...]]:
    outside = not is_path_contained(data_directory, repository_root)
    path: Path | None = None
    write_performed = False
    write_passed = False
    readback_match = False
    cleanup_passed = True
    stage = "create"
    diagnostics: list[Diagnostic] = []
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b",
            prefix="platform-preflight-",
            suffix=".probe",
            dir=data_directory,
            delete=False,
        ) as stream:
            path = Path(stream.name)
            write_performed = True
            stage = "write"
            stream.write(PROBE_CONTENT)
            stream.flush()
            os.fsync(stream.fileno())
            write_passed = True
        stage = "readback"
        readback_match = path.read_bytes() == PROBE_CONTENT
        if not readback_match:
            diagnostics.append(_diagnostic(
                "ERROR",
                "DATA_DIRECTORY_READBACK_FAILED",
                "storage",
                "Data-directory probe readback did not match.",
            ))
    except OSError:
        code = (
            "DATA_DIRECTORY_READBACK_FAILED"
            if stage == "readback"
            else "DATA_DIRECTORY_WRITE_FAILED"
        )
        message = (
            "Data-directory probe readback failed."
            if stage == "readback"
            else "Data-directory write probe failed."
        )
        diagnostics.append(_diagnostic("ERROR", code, "storage", message))
    finally:
        if path is not None:
            try:
                path.unlink(missing_ok=True)
                cleanup_passed = not path.exists()
            except OSError:
                cleanup_passed = False
            if not cleanup_passed:
                diagnostics.append(_diagnostic(
                    "ERROR",
                    "DATA_DIRECTORY_CLEANUP_FAILED",
                    "storage",
                    "Data-directory probe cleanup failed.",
                ))
    persistent = path is not None and path.exists()
    probe = StorageProbe(
        data_directory_outside_repository=outside,
        write_test_performed=write_performed,
        write_test_passed=write_passed,
        readback_match=readback_match,
        cleanup_passed=cleanup_passed,
        persistent_test_file_created=persistent,
    )
    return probe, tuple(sorted(diagnostics, key=_diagnostic_sort_key))


def check_sqlite_in_memory(
    connect: Callable[[str], object] | None = sqlite3.connect,
) -> tuple[SQLiteProbe, tuple[Diagnostic, ...]]:
    if connect is None:
        diagnostic = _diagnostic(
            "ERROR",
            "SQLITE_MODULE_UNAVAILABLE",
            "sqlite",
            "The SQLite module is unavailable.",
        )
        return SQLiteProbe(False, "", False, False), (diagnostic,)

    connection = None
    passed = False
    diagnostics: list[Diagnostic] = []
    try:
        connection = connect(":memory:")
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE preflight_check (value INTEGER NOT NULL)")
        cursor.execute("INSERT INTO preflight_check (value) VALUES (1)")
        row = cursor.execute("SELECT value FROM preflight_check").fetchone()
        integrity = cursor.execute("PRAGMA integrity_check").fetchone()
        passed = row == (1,) and integrity == ("ok",)
        if not passed:
            raise sqlite3.DatabaseError("in-memory validation failed")
    except (sqlite3.Error, AttributeError, TypeError, ValueError):
        diagnostics.append(_diagnostic(
            "ERROR",
            "SQLITE_IN_MEMORY_CHECK_FAILED",
            "sqlite",
            "The SQLite in-memory check failed.",
        ))
    finally:
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error:
                passed = False
                if not diagnostics:
                    diagnostics.append(_diagnostic(
                        "ERROR",
                        "SQLITE_IN_MEMORY_CHECK_FAILED",
                        "sqlite",
                        "The SQLite in-memory connection did not close cleanly.",
                    ))
    probe = SQLiteProbe(True, sqlite3.sqlite_version, passed, False)
    return probe, tuple(sorted(diagnostics, key=_diagnostic_sort_key))


def read_temperature_stub() -> tuple[TemperatureProbe, tuple[Diagnostic, ...]]:
    probe = TemperatureProbe(
        adapter="stub",
        status="NOT_IMPLEMENTED",
        value_celsius="",
        hardware_access_performed=False,
    )
    diagnostic = _diagnostic(
        "WARNING",
        "TEMPERATURE_NOT_IMPLEMENTED",
        "temperature",
        "Temperature access is a hardware-free stub in ST-002.",
    )
    return probe, (diagnostic,)


def _diagnostic_sort_key(diagnostic: Diagnostic) -> tuple[str, str, str]:
    return diagnostic.component, diagnostic.code, diagnostic.message


def determine_exit_code(diagnostics: Sequence[Diagnostic]) -> int:
    error_codes = {item.code for item in diagnostics if item.severity == "ERROR"}
    if "INTERNAL_VALIDATOR_ERROR" in error_codes or "REPORT_WRITE_FAILED" in error_codes:
        return 7
    groups = (
        (2, {
            "PREFLIGHT_INVALID_ARGUMENT",
            "PREFLIGHT_REPOSITORY_ROOT_INVALID",
            "PREFLIGHT_DATA_DIRECTORY_INVALID",
            "PREFLIGHT_DATA_DIRECTORY_INSIDE_REPOSITORY",
            "PREFLIGHT_REPORT_PATH_INSIDE_REPOSITORY",
            "PREFLIGHT_REPORT_PARENT_INVALID",
        }),
        (3, {"PYTHON_VERSION_UNSUPPORTED", "OPERATING_SYSTEM_UNSUPPORTED"}),
        (4, {
            "LOGICAL_CPU_BELOW_MINIMUM",
            "MEMORY_UNAVAILABLE",
            "MEMORY_BELOW_MINIMUM",
            "DISK_SPACE_BELOW_MINIMUM",
            "DATA_DIRECTORY_WRITE_FAILED",
            "DATA_DIRECTORY_READBACK_FAILED",
            "DATA_DIRECTORY_CLEANUP_FAILED",
        }),
        (5, {
            "MONOTONIC_CLOCK_UNAVAILABLE",
            "SQLITE_MODULE_UNAVAILABLE",
            "SQLITE_IN_MEMORY_CHECK_FAILED",
        }),
    )
    for exit_code, codes in groups:
        if error_codes.intersection(codes):
            return exit_code
    return 0


def _runtime_document(probe: RuntimeProbe) -> dict[str, object]:
    return {
        "python_version": probe.python_version,
        "python_implementation": probe.python_implementation,
        "minimum_python_version": probe.minimum_python_version,
        "python_requirement_satisfied": probe.python_requirement_satisfied,
        "standard_library_only": probe.standard_library_only,
    }


def _platform_document(probe: PlatformProbe) -> dict[str, object]:
    return {
        "system": probe.system,
        "release": probe.release,
        "machine": probe.machine,
        "linux_required": probe.linux_required,
        "linux_requirement_satisfied": probe.linux_requirement_satisfied,
        "orange_pi_hardware_validation": probe.orange_pi_hardware_validation,
    }


def _resources_document(probe: ResourceProbe) -> dict[str, object]:
    return {
        "logical_cpu_count": probe.logical_cpu_count,
        "minimum_logical_cpu_count": probe.minimum_logical_cpu_count,
        "cpu_requirement_satisfied": probe.cpu_requirement_satisfied,
        "total_memory_bytes": probe.total_memory_bytes,
        "minimum_memory_bytes": probe.minimum_memory_bytes,
        "memory_requirement_satisfied": bool(probe.memory_requirement_satisfied),
        "filesystem_total_bytes": probe.filesystem_total_bytes,
        "minimum_free_bytes": probe.minimum_free_bytes,
        "free_space_requirement_satisfied": probe.free_space_requirement_satisfied,
    }


def _clock_document(probe: ClockProbe) -> dict[str, object]:
    return {
        "monotonic_available": probe.monotonic_available,
        "monotonic": probe.monotonic,
        "adjustable": probe.adjustable,
        "resolution_ns": probe.resolution_ns,
    }


def _storage_document(probe: StorageProbe) -> dict[str, object]:
    return {
        "data_directory_outside_repository": probe.data_directory_outside_repository,
        "write_test_performed": probe.write_test_performed,
        "write_test_passed": probe.write_test_passed,
        "readback_match": probe.readback_match,
        "cleanup_passed": probe.cleanup_passed,
        "persistent_test_file_created": probe.persistent_test_file_created,
    }


def _sqlite_document(probe: SQLiteProbe) -> dict[str, object]:
    return {
        "module_available": probe.module_available,
        "sqlite_version": probe.sqlite_version,
        "in_memory_check_passed": probe.in_memory_check_passed,
        "database_file_created": probe.database_file_created,
    }


def _temperature_document(probe: TemperatureProbe) -> dict[str, object]:
    return {
        "adapter": probe.adapter,
        "status": probe.status,
        "value_celsius": probe.value_celsius,
        "hardware_access_performed": probe.hardware_access_performed,
    }


def build_report(
    profile: str,
    runtime: RuntimeProbe,
    platform: PlatformProbe,
    resources: ResourceProbe,
    clock: ClockProbe,
    storage: StorageProbe,
    sqlite: SQLiteProbe,
    temperature: TemperatureProbe,
    diagnostics: Sequence[Diagnostic],
) -> PreflightReport:
    ordered_diagnostics = tuple(sorted(diagnostics, key=_diagnostic_sort_key))
    exit_code = determine_exit_code(ordered_diagnostics)
    result = "PASS" if exit_code == 0 else "FAIL"
    checks: tuple[bool | None, ...] = (
        runtime.python_requirement_satisfied,
        platform.linux_requirement_satisfied,
        resources.cpu_requirement_satisfied,
        resources.memory_requirement_satisfied,
        resources.free_space_requirement_satisfied,
        clock.monotonic_available and clock.monotonic,
        storage.write_test_passed
        and storage.readback_match
        and storage.cleanup_passed
        and not storage.persistent_test_file_created,
        sqlite.module_available and sqlite.in_memory_check_passed,
        None,
    )
    pass_count = sum(item is True for item in checks)
    fail_count = sum(item is False for item in checks)
    unavailable_count = sum(item is None for item in checks)
    document: dict[str, object] = {
        "report_version": REPORT_VERSION,
        "phase": PHASE,
        "profile": profile,
        "result": result,
        "runtime": _runtime_document(runtime),
        "platform": _platform_document(platform),
        "resources": _resources_document(resources),
        "clock": _clock_document(clock),
        "storage": _storage_document(storage),
        "sqlite": _sqlite_document(sqlite),
        "temperature": _temperature_document(temperature),
        "safety": {
            "network_access_performed": False,
            "gpio_access_performed": False,
            "hardware_output_performed": False,
            "motor_control_performed": False,
            "charging_control_performed": False,
            "repository_modified": False,
            "physical_estop_independent": True,
        },
        "summary": {
            "check_count": len(checks),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "unavailable_count": unavailable_count,
            "next_phase_eligible": result == "PASS",
        },
        "diagnostics": [
            {
                "severity": item.severity,
                "code": item.code,
                "component": item.component,
                "message": item.message,
            }
            for item in ordered_diagnostics
        ],
        "exit_code": exit_code,
    }
    return PreflightReport(document=document, exit_code=exit_code)


def render_json_report(report: PreflightReport) -> str:
    return json.dumps(
        report.document,
        ensure_ascii=True,
        indent=2,
        separators=(",", ": "),
    ) + "\n"


def _result_word(value: bool | None) -> str:
    if value is None:
        return "UNAVAILABLE"
    return "PASS" if value else "FAIL"


def render_text_report(report: PreflightReport) -> str:
    document = report.document
    runtime = document["runtime"]
    platform = document["platform"]
    resources = document["resources"]
    clock = document["clock"]
    storage = document["storage"]
    sqlite = document["sqlite"]
    temperature = document["temperature"]
    safety = document["safety"]
    diagnostics = document["diagnostics"]
    assert isinstance(runtime, dict)
    assert isinstance(platform, dict)
    assert isinstance(resources, dict)
    assert isinstance(clock, dict)
    assert isinstance(storage, dict)
    assert isinstance(sqlite, dict)
    assert isinstance(temperature, dict)
    assert isinstance(safety, dict)
    assert isinstance(diagnostics, list)
    data_pass = (
        bool(storage["write_test_passed"])
        and bool(storage["readback_match"])
        and bool(storage["cleanup_passed"])
        and not bool(storage["persistent_test_file_created"])
    )
    lines = (
        f"phase={document['phase']}",
        f"profile={document['profile']}",
        f"result={document['result']}",
        f"python_result={_result_word(bool(runtime['python_requirement_satisfied']))}",
        f"platform_result={_result_word(bool(platform['linux_requirement_satisfied']))}",
        f"cpu_result={_result_word(bool(resources['cpu_requirement_satisfied']))}",
        f"memory_result={_result_word(bool(resources['memory_requirement_satisfied']))}",
        f"disk_result={_result_word(bool(resources['free_space_requirement_satisfied']))}",
        f"monotonic_result={_result_word(bool(clock['monotonic_available']) and bool(clock['monotonic']))}",
        f"data_directory_result={_result_word(data_pass)}",
        f"sqlite_result={_result_word(bool(sqlite['module_available']) and bool(sqlite['in_memory_check_passed']))}",
        f"temperature_result={temperature['status']}",
        f"network_access_performed={str(bool(safety['network_access_performed'])).lower()}",
        f"gpio_access_performed={str(bool(safety['gpio_access_performed'])).lower()}",
        f"hardware_output_performed={str(bool(safety['hardware_output_performed'])).lower()}",
        f"diagnostic_count={len(diagnostics)}",
        f"exit_code={document['exit_code']}",
    )
    return "\n".join(lines) + "\n"


def write_external_report(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _default_probes(profile: str) -> tuple[
    RuntimeProbe,
    PlatformProbe,
    ResourceProbe,
    ClockProbe,
    StorageProbe,
    SQLiteProbe,
    TemperatureProbe,
]:
    runtime = RuntimeProbe(
        python_version=(
            f"{sys.version_info.major}.{sys.version_info.minor}."
            f"{sys.version_info.micro}"
        ),
        python_implementation="CPython",
        minimum_python_version="3.11",
        python_requirement_satisfied=sys.version_info[:2] >= MINIMUM_PYTHON_VERSION,
        standard_library_only=True,
    )
    safe_profile = profile if profile in PROFILES else "development-host"
    linux_required = safe_profile == "orange-pi-zero-512"
    platform = PlatformProbe(
        system="",
        release="",
        machine="",
        linux_required=linux_required,
        linux_requirement_satisfied=not linux_required,
        orange_pi_hardware_validation="NOT_PERFORMED",
    )
    resources = ResourceProbe(0, 1, False, 0, MINIMUM_MEMORY_BYTES, False, 0,
                              MINIMUM_FREE_BYTES, False)
    clock = ClockProbe(False, False, True, 0)
    storage = StorageProbe(False, False, False, False, True, False)
    sqlite_probe = SQLiteProbe(True, sqlite3.sqlite_version, False, False)
    temperature = TemperatureProbe("stub", "NOT_IMPLEMENTED", "", False)
    return runtime, platform, resources, clock, storage, sqlite_probe, temperature


def run_preflight(arguments: CliArguments, write_reports: bool = True) -> PreflightReport:
    argument_diagnostics = validate_arguments(arguments)
    if argument_diagnostics:
        probes = _default_probes(arguments.profile)
        return build_report(arguments.profile, *probes, argument_diagnostics)

    runtime, runtime_diagnostics = collect_runtime()
    platform, platform_diagnostics = collect_platform(arguments.profile)
    resources, resource_diagnostics = collect_resources(
        arguments.data_directory,
        arguments.profile,
        platform.system,
    )
    clock, clock_diagnostics = check_monotonic_clock()
    storage, storage_diagnostics = check_external_data_directory(
        arguments.repository_root,
        arguments.data_directory,
    )
    sqlite_probe, sqlite_diagnostics = check_sqlite_in_memory()
    temperature, temperature_diagnostics = read_temperature_stub()
    diagnostics = (
        runtime_diagnostics
        + platform_diagnostics
        + resource_diagnostics
        + clock_diagnostics
        + storage_diagnostics
        + sqlite_diagnostics
        + temperature_diagnostics
    )
    report = build_report(
        arguments.profile,
        runtime,
        platform,
        resources,
        clock,
        storage,
        sqlite_probe,
        temperature,
        diagnostics,
    )
    if not write_reports:
        return report

    try:
        write_external_report(arguments.json_report, render_json_report(report))
        write_external_report(arguments.text_report, render_text_report(report))
    except OSError:
        report_failure = _diagnostic(
            "ERROR",
            "REPORT_WRITE_FAILED",
            "report",
            "An external report could not be written.",
        )
        return build_report(
            arguments.profile,
            runtime,
            platform,
            resources,
            clock,
            storage,
            sqlite_probe,
            temperature,
            diagnostics + (report_failure,),
        )
    return report


def _internal_error_report(profile: str) -> PreflightReport:
    probes = _default_probes(profile)
    diagnostic = _diagnostic(
        "ERROR",
        "INTERNAL_VALIDATOR_ERROR",
        "validator",
        "An unexpected internal validator error occurred.",
    )
    return build_report(profile, *probes, (diagnostic,))


def main(argv: Sequence[str] | None = None) -> int:
    profile = "development-host"
    try:
        arguments = parse_arguments(argv)
        profile = arguments.profile
        report = run_preflight(arguments)
    except ValueError:
        probes = _default_probes(profile)
        diagnostic = _diagnostic(
            "ERROR",
            "PREFLIGHT_INVALID_ARGUMENT",
            "arguments",
            "Command-line arguments are invalid.",
        )
        report = build_report(profile, *probes, (diagnostic,))
    except Exception:
        report = _internal_error_report(profile)
    sys.stdout.write(render_text_report(report))
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
