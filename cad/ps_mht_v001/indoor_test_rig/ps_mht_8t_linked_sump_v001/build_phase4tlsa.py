"""Build and validate the Phase 4T-LS-A reference-only delivery."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq
import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ps_mht_v001.common.validation import (
    export_reference_step,
    measure_shape,
    validate_step_round_trip,
)
from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.diagrams import (
    write_phase4tlsa_diagrams,
)
from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.parameters import (
    STATUS,
    branch_identifiers,
    commercial_bulkhead_status,
    commercial_valve_status,
    common_pump_well_location,
    common_trunk_inner_diameter_mm,
    common_trunk_slope_candidates,
    common_trunk_slope_selected,
    emergency_overflow_destination,
    emergency_overflow_inner_diameter_mm,
    fresh_water_system_separate_from_circulation,
    hydraulic_connection,
    initial_indoor_tower_count,
    local_sump_branch_inner_diameter_mm,
    local_sump_measurement_status,
    maximum_tower_count,
    minimum_ceiling_clearance_mm,
    minimum_human_aisle_width_mm,
    pump_eight_tower_capacity_status,
    pump_model_reference,
    room_ceiling_height_mm,
    room_length_mm,
    room_width_mm,
    upper_tank_maximum_top_elevation_mm,
)
from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.reference_cad import (
    build_central_pump_well_reference,
    build_isolation_flow_reference_assembly,
    build_local_sump_reference_envelope,
    build_parallel_equalization_zone_4tower_reference,
    build_parallel_equalization_zone_8tower_reference,
    build_tower_support_deck_reference,
    isolation_reference_metadata,
    local_sump_reference_metadata,
    parallel_zone_metadata,
    pump_well_reference_metadata,
    support_deck_reference_metadata,
)
from ps_mht_v001.indoor_test_rig.ps_mht_8t_linked_sump_v001.water_balance import (
    build_water_balance_report,
)


TARGET_ROOT = Path(__file__).resolve().parent
PS_MHT_ROOT = TARGET_ROOT.parents[1]
REPOSITORY_ROOT = TARGET_ROOT.parents[3]
EXISTING_EXPORT_ROOT = PS_MHT_ROOT / "exports"
EXPORT_ROOT = TARGET_ROOT / "exports"
STEP_ROOT = EXPORT_ROOT / "step"
PREVIEW_ROOT = EXPORT_ROOT / "preview"
COMMIT_ROOT = TARGET_ROOT / "commit"
DOWNLOADS_ROOT = Path(r"D:\Downloads")

EXPECTED_EXISTING_TEST_COUNT = 334
EXPECTED_NEW_TEST_COUNT = 40
EXPECTED_EXISTING_EXPORT_COUNT = 226
INITIAL_PS_MHT_FILE_COUNT = 631
INITIAL_PS_MHT_TOTAL_BYTES = 131_364_879
PHASE_RELATIVE_PREFIX = (
    "cad/ps_mht_v001/indoor_test_rig/ps_mht_8t_linked_sump_v001/"
)
INDOOR_RIG_PREFIX = "cad/ps_mht_v001/indoor_test_rig/"

REFERENCE_BUILDERS = {
    "ps_mht_8t_linked_sump_local_sump_reference.step":
        build_local_sump_reference_envelope,
    "ps_mht_8t_linked_sump_support_deck_reference.step":
        build_tower_support_deck_reference,
    "ps_mht_8t_linked_sump_4tower_zone_reference.step":
        build_parallel_equalization_zone_4tower_reference,
    "ps_mht_8t_linked_sump_8tower_zone_reference.step":
        build_parallel_equalization_zone_8tower_reference,
    "ps_mht_8t_linked_sump_pump_well_reference.step":
        build_central_pump_well_reference,
    "ps_mht_8t_linked_sump_isolation_reference.step":
        build_isolation_flow_reference_assembly,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _snapshot(directory: Path) -> dict[str, str]:
    return {
        path.relative_to(directory).as_posix(): _sha256(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def _git_read_only(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _starting_repository_state() -> dict[str, object]:
    all_untracked = _git_read_only(
        "ls-files", "--others", "--exclude-standard"
    ).splitlines()
    original_untracked = [
        item for item in all_untracked if not item.startswith(INDOOR_RIG_PREFIX)
    ]
    existing_files = [
        path
        for path in PS_MHT_ROOT.rglob("*")
        if path.is_file()
        and "indoor_test_rig" not in path.relative_to(PS_MHT_ROOT).parts
    ]
    large_files: list[dict[str, object]] = []
    for current_root, directories, files in os.walk(REPOSITORY_ROOT):
        directories[:] = [
            name
            for name in directories
            if name not in {".git", "__pycache__", ".pytest_cache"}
        ]
        for name in files:
            path = Path(current_root) / name
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size >= 95 * 1024 * 1024:
                large_files.append(
                    {
                        "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
                        "bytes": size,
                    }
                )
    return {
        "repository_root": str(REPOSITORY_ROOT),
        "branch": _git_read_only("branch", "--show-current"),
        "head": _git_read_only("rev-parse", "HEAD"),
        "status_short": _git_read_only("status", "--short").splitlines(),
        "tracked_diff_files": _git_read_only("diff", "--name-only").splitlines(),
        "tracked_diff_stat": _git_read_only("diff", "--stat").splitlines(),
        "staged_diff_files": _git_read_only(
            "diff", "--cached", "--name-only"
        ).splitlines(),
        "staged_diff_stat": _git_read_only(
            "diff", "--cached", "--stat"
        ).splitlines(),
        "untracked_files_before_phase": original_untracked,
        "untracked_file_count_before_phase": len(original_untracked),
        "ps_mht_file_count_before_phase": len(existing_files),
        "ps_mht_total_bytes_before_phase": sum(
            path.stat().st_size for path in existing_files
        ),
        "files_at_least_95mb": large_files,
        "read_only_git_commands": [
            "branch --show-current",
            "rev-parse HEAD",
            "status --short",
            "diff --name-only",
            "diff --stat",
            "diff --cached --name-only",
            "diff --cached --stat",
            "ls-files --others --exclude-standard",
        ],
        "git_mutation_commands": [],
    }


def _run_test_files(paths: list[Path], expected_total: int) -> dict[str, object]:
    environment = os.environ.copy()
    python_path = str(PS_MHT_ROOT.parent)
    if environment.get("PYTHONPATH"):
        python_path += os.pathsep + environment["PYTHONPATH"]
    environment["PYTHONPATH"] = python_path
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    total = 0
    results: list[dict[str, object]] = []
    for path in paths:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(path),
                "-q",
                "-o",
                f"cache_dir={PS_MHT_ROOT / '.pytest_cache'}",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
        output = result.stdout + result.stderr
        match = re.search(r"(\d+) passed", output)
        passed = int(match.group(1)) if match else 0
        total += passed
        results.append(
            {"file": path.name, "passed": passed, "returncode": result.returncode}
        )
        if result.returncode:
            raise RuntimeError(f"{path.name} failed:\n{output}")
    if total != expected_total:
        raise RuntimeError(f"expected {expected_total} tests, got {total}")
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_PROCESS",
        "passed": total,
        "expected": expected_total,
        "all_passed": True,
        "files": results,
    }


def _build_print_manifest() -> dict[str, object]:
    return {
        "project": "PS-MHT-8T-LINKED-SUMP-V001",
        "phase": "4T-LS-A",
        "ready_first_count": 0,
        "stl_output_count": 0,
        "items": [
            {
                "file_name": name,
                "format": "STEP",
                "print_status": (
                    "NOT_PRINTABLE_MEASUREMENT_PENDING"
                    if key in {"local_sump", "support_deck", "pump_well"}
                    else "REFERENCE_ONLY"
                ),
                "print_target": False,
                "measurement_pending": True,
            }
            for key, name in (
                ("local_sump", "ps_mht_8t_linked_sump_local_sump_reference.step"),
                ("support_deck", "ps_mht_8t_linked_sump_support_deck_reference.step"),
                ("zone4", "ps_mht_8t_linked_sump_4tower_zone_reference.step"),
                ("zone8", "ps_mht_8t_linked_sump_8tower_zone_reference.step"),
                ("pump_well", "ps_mht_8t_linked_sump_pump_well_reference.step"),
                ("isolation", "ps_mht_8t_linked_sump_isolation_reference.step"),
            )
        ],
    }


def _interface_audit(interface_spec: dict[str, object]) -> dict[str, object]:
    branches = interface_spec["branches"]
    return {
        "status": "REFERENCE_INTERFACES_COMPLETE_MEASUREMENTS_PENDING",
        "topology": hydraulic_connection,
        "branch_ids": list(branch_identifiers),
        "branch_count": len(branches),
        "active_initial_branches": sum(
            item["initial_use"] == "ACTIVE_4T" for item in branches
        ),
        "closed_future_branches": sum(
            item["initial_use"] == "CLOSED_FUTURE" for item in branches
        ),
        "branch_id_mm": {
            "minimum": local_sump_branch_inner_diameter_mm[0],
            "preferred": local_sump_branch_inner_diameter_mm[1],
        },
        "trunk_id_mm": {
            "minimum": common_trunk_inner_diameter_mm[0],
            "preferred": common_trunk_inner_diameter_mm[1],
        },
        "trunk_slope_candidates": list(common_trunk_slope_candidates),
        "trunk_slope_selected": common_trunk_slope_selected,
        "bulkhead": commercial_bulkhead_status,
        "valve": commercial_valve_status,
        "final_bulkhead_hole_mm": None,
        "overflow_destination": emergency_overflow_destination,
        "overflow_id_mm": {
            "minimum": emergency_overflow_inner_diameter_mm[0],
            "preferred": emergency_overflow_inner_diameter_mm[1],
        },
    }


def _room_layout_audit() -> dict[str, object]:
    return {
        "status": "REFERENCE_LAYOUT_ONLY_ROOM_PLAN_MEASUREMENT_PENDING",
        "room_ceiling_height_mm": room_ceiling_height_mm,
        "room_length_mm": room_length_mm,
        "room_width_mm": room_width_mm,
        "upper_tank_maximum_top_elevation_mm": upper_tank_maximum_top_elevation_mm,
        "ceiling_clearance_mm": (
            room_ceiling_height_mm - upper_tank_maximum_top_elevation_mm
        ),
        "minimum_ceiling_clearance_mm": minimum_ceiling_clearance_mm,
        "ceiling_clearance_pass": (
            room_ceiling_height_mm - upper_tank_maximum_top_elevation_mm
            >= minimum_ceiling_clearance_mm
        ),
        "minimum_human_aisle_width_mm": minimum_human_aisle_width_mm,
        "trunk_route": "PROTECTED_REAR_SERVICE_ROUTE",
        "crosses_human_aisle": False,
        "four_tower_reference": parallel_zone_metadata(4),
        "eight_position_reference": parallel_zone_metadata(8),
        "fresh_water_separate": fresh_water_system_separate_from_circulation,
    }


def _baseline_commit_paths() -> list[str]:
    allowed_suffixes = {
        ".py", ".md", ".yaml", ".yml", ".json", ".step", ".stl",
        ".svg", ".3mf", ".cmd", ".gitignore",
    }
    paths: list[str] = []
    for path in PS_MHT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative_ps = path.relative_to(PS_MHT_ROOT)
        if "indoor_test_rig" in relative_ps.parts:
            continue
        if any(part in {"__pycache__", ".pytest_cache"} for part in relative_ps.parts):
            continue
        if path.suffix.lower() not in allowed_suffixes and path.name != ".gitignore":
            continue
        if path.suffix.lower() == ".zip":
            continue
        paths.append(path.relative_to(REPOSITORY_ROOT).as_posix())
    return sorted(set(paths))


def _phase_commit_paths(include_sha_sums: bool = True) -> list[str]:
    paths: list[str] = []
    parent_init = PS_MHT_ROOT / "indoor_test_rig" / "__init__.py"
    if parent_init.is_file():
        paths.append(parent_init.relative_to(REPOSITORY_ROOT).as_posix())
    for path in TARGET_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(TARGET_ROOT)
        if any(part in {"__pycache__", ".pytest_cache"} for part in relative.parts):
            continue
        if path.suffix.lower() == ".pyc":
            continue
        paths.append(path.relative_to(REPOSITORY_ROOT).as_posix())
    mandatory = (
        COMMIT_ROOT / "repository_commit_audit.json",
        COMMIT_ROOT / "baseline_sha256_before_phase4tlsa.json",
        COMMIT_ROOT / "commit_manifest_ps_mht_baseline_before_linked_sump.txt",
        COMMIT_ROOT / "commit_manifest_linked_sump_phase4tlsa.txt",
        COMMIT_ROOT / "commit_manifest_combined.txt",
    )
    paths.extend(path.relative_to(REPOSITORY_ROOT).as_posix() for path in mandatory)
    if include_sha_sums:
        paths.append((TARGET_ROOT / "SHA256SUMS.txt").relative_to(REPOSITORY_ROOT).as_posix())
    return sorted(set(paths))


def _write_path_manifest(path: Path, title: str, paths: list[str]) -> Path:
    content = [f"# {title}", ""] + paths
    path.write_text("\n".join(content) + "\n", encoding="utf-8")
    return path


def _build_commit_audit(
    starting_state: dict[str, object],
    phase_paths: list[str],
) -> dict[str, object]:
    review_large_steps = [
        path
        for path in phase_paths
        if path.endswith(".step")
        and (REPOSITORY_ROOT / path).is_file()
        and (REPOSITORY_ROOT / path).stat().st_size >= 20 * 1024 * 1024
    ]
    return {
        "project": "PS-MHT-8T-LINKED-SUMP-V001",
        "phase": "4T-LS-A",
        "starting_repository_state": starting_state,
        "classification": {
            "COMMIT_RECOMMENDED": phase_paths,
            "DELIVERY_ONLY": [
                "D:/Downloads/PS_MHT_8T_LINKED_SUMP_V001_PHASE4TLSA_<timestamp>.zip"
            ],
            "EXCLUDE": [
                "**/__pycache__/**",
                "**/*.pyc",
                "**/.pytest_cache/**",
                "**/temporary_logs/**",
                "**/temporary_extract/**",
            ],
            "REVIEW_BEFORE_COMMIT": [
                *review_large_steps,
                "cad/ps_mht_v001/exports/*delivery.zip",
                "DUPLICATE_ARTIFACTS_IF_ANY",
                "EXTERNAL_LIBRARY_GENERATED_FILES_IF_ANY",
            ],
        },
        "root_readme_included": False,
        "rover_authority_documents_included": False,
        "files_at_least_95mb": starting_state["files_at_least_95mb"],
        "git": {
            "read_only_inspection_performed": True,
            "mutation_operations_performed": False,
            "mutation_commands": [],
        },
    }


def _write_sha_sums(paths: list[Path], destination: Path) -> Path:
    records = []
    for path in sorted(paths):
        if path == destination or not path.is_file():
            continue
        records.append(
            f"{_sha256(path)}  {path.relative_to(REPOSITORY_ROOT).as_posix()}"
        )
    destination.write_text("\n".join(records) + "\n", encoding="utf-8")
    return destination


def _create_delivery_zip(paths: list[Path]) -> tuple[Path, str]:
    DOWNLOADS_ROOT.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = (
        DOWNLOADS_ROOT
        / f"PS_MHT_8T_LINKED_SUMP_V001_PHASE4TLSA_{timestamp}.zip"
    )
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(paths)):
            if not path.is_file():
                continue
            archive.write(path, path.relative_to(REPOSITORY_ROOT).as_posix())
    return destination, _sha256(destination)


def generate_phase4tlsa() -> dict[str, object]:
    starting_state = _starting_repository_state()
    if starting_state["ps_mht_file_count_before_phase"] != INITIAL_PS_MHT_FILE_COUNT:
        raise RuntimeError("starting PS-MHT file-count audit does not match")
    if starting_state["ps_mht_total_bytes_before_phase"] != INITIAL_PS_MHT_TOTAL_BYTES:
        raise RuntimeError("starting PS-MHT byte-count audit does not match")

    baseline_before = _snapshot(EXISTING_EXPORT_ROOT)
    if len(baseline_before) != EXPECTED_EXISTING_EXPORT_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_EXISTING_EXPORT_COUNT} existing exports, "
            f"got {len(baseline_before)}"
        )
    for directory in (STEP_ROOT, PREVIEW_ROOT, COMMIT_ROOT):
        directory.mkdir(parents=True, exist_ok=True)

    reference_metrics: dict[str, dict[str, object]] = {}
    expected_step_counts: dict[str, int] = {}
    for name, builder in REFERENCE_BUILDERS.items():
        model = builder()
        metrics = measure_shape(model)
        path = STEP_ROOT / name
        export_reference_step(model, path, metrics.solid_count)
        reference_metrics[name] = metrics.as_dict()
        expected_step_counts[name] = metrics.solid_count

    step_round_trip = {
        name: validate_step_round_trip(STEP_ROOT / name, count).as_dict()
        for name, count in expected_step_counts.items()
    }
    diagram_paths = write_phase4tlsa_diagrams(PREVIEW_ROOT)

    spec = yaml.safe_load(
        (TARGET_ROOT / "specs" / "ps_mht_8t_linked_sump_v001.yaml").read_text(
            encoding="utf-8"
        )
    )
    interface_spec = json.loads(
        (
            TARGET_ROOT
            / "specs"
            / "ps_mht_8t_linked_sump_interfaces.json"
        ).read_text(encoding="utf-8")
    )
    if spec["zone"]["maximum_towers"] != maximum_tower_count:
        raise RuntimeError("YAML/Python maximum tower mismatch")
    if interface_spec["topology"] != hydraulic_connection:
        raise RuntimeError("JSON/Python topology mismatch")

    water_balance = build_water_balance_report()
    interface_audit = _interface_audit(interface_spec)
    room_audit = _room_layout_audit()
    print_manifest = _build_print_manifest()
    _write_json(PREVIEW_ROOT / "phase4tlsa_water_balance.json", water_balance)
    _write_json(PREVIEW_ROOT / "phase4tlsa_interface_audit.json", interface_audit)
    _write_json(PREVIEW_ROOT / "phase4tlsa_room_layout_audit.json", room_audit)
    _write_json(PREVIEW_ROOT / "print_manifest_phase4tlsa.json", print_manifest)

    baseline_sha_path = COMMIT_ROOT / "baseline_sha256_before_phase4tlsa.json"
    _write_json(
        baseline_sha_path,
        {
            "artifact_root": str(EXISTING_EXPORT_ROOT),
            "artifact_count": len(baseline_before),
            "sha256": baseline_before,
        },
    )

    baseline_manifest_path = (
        COMMIT_ROOT / "commit_manifest_ps_mht_baseline_before_linked_sump.txt"
    )
    phase_manifest_path = (
        COMMIT_ROOT / "commit_manifest_linked_sump_phase4tlsa.txt"
    )
    combined_manifest_path = COMMIT_ROOT / "commit_manifest_combined.txt"
    baseline_paths = _baseline_commit_paths()
    _write_path_manifest(
        baseline_manifest_path,
        "PS-MHT-V001 baseline before linked sump",
        baseline_paths,
    )

    preliminary_phase_paths = _phase_commit_paths()
    commit_audit = _build_commit_audit(starting_state, preliminary_phase_paths)
    commit_audit_path = COMMIT_ROOT / "repository_commit_audit.json"
    _write_json(commit_audit_path, commit_audit)
    _write_json(PREVIEW_ROOT / "phase4tlsa_commit_audit.json", commit_audit)

    baseline_after_geometry = _snapshot(EXISTING_EXPORT_ROOT)
    if baseline_after_geometry != baseline_before:
        raise RuntimeError("existing Phase 1 through Phase 3H-A SHA changed")
    stl_paths = list(EXPORT_ROOT.rglob("*.stl"))
    if stl_paths:
        raise RuntimeError("Phase 4T-LS-A generated an unauthorized STL")

    report: dict[str, object] = {
        "project": "PS-MHT-8T-LINKED-SUMP-V001",
        "phase": "4T-LS-A",
        "status": STATUS,
        "cadquery_version": cq.__version__,
        "starting_state": starting_state,
        "architecture": {
            "maximum_tower_count": maximum_tower_count,
            "initial_indoor_tower_count": initial_indoor_tower_count,
            "circulation_pump_count": 1,
            "topology": hydraulic_connection,
            "serial_daisy_chain": False,
            "common_pump_well_location": common_pump_well_location,
            "pump_reference": pump_model_reference,
            "eight_tower_capacity": pump_eight_tower_capacity_status,
        },
        "local_sump": local_sump_reference_metadata(),
        "support_deck": support_deck_reference_metadata(),
        "pump_well": pump_well_reference_metadata(),
        "isolation_reference": isolation_reference_metadata(),
        "water_balance": water_balance,
        "interface_audit": interface_audit,
        "room_layout_audit": room_audit,
        "reference_cad_metrics": reference_metrics,
        "step_round_trip": step_round_trip,
        "svg_files": [path.name for path in diagram_paths],
        "yaml_valid": True,
        "json_valid": True,
        "stl_output_count": 0,
        "print_manifest": print_manifest,
        "non_regression": {
            "artifact_count": len(baseline_before),
            "all_unchanged": True,
        },
        "automated_tests": {"status": "RUNNING"},
        "git": {
            "read_only_inspection_performed": True,
            "mutation_operations_performed": False,
            "mutation_commands": [],
        },
        "measurements_pending": [
            "LOCAL_SUMP_DIMENSIONS_MATERIAL_AND_SAFE_FLATS",
            "BULKHEAD_BODY_HOLE_THREAD_GASKET_AND_FLAT_WIDTH",
            "BALL_VALVE_BODY_UNION_HANDLE_SWEEP_AND_CONNECTION",
            "HOSE_AND_TRUNK_ACTUAL_ID_OD_BEND_AND_CLAMP_RANGE",
            "PUMP_BODY_INTAKE_SUBMERGENCE_NIPPLE_AND_HEAD_FLOW",
            "ROOM_LENGTH_WIDTH_EGRESS_AND_SERVICE_ROUTE",
            "ACTUAL_TOWER_MASS_AND_STABILITY",
        ],
    }
    validation_path = PREVIEW_ROOT / "phase4tlsa_validation_report.json"
    _write_json(validation_path, report)

    existing_tests = _run_test_files(
        sorted((PS_MHT_ROOT / "tests").glob("test_*.py")),
        EXPECTED_EXISTING_TEST_COUNT,
    )
    new_tests = _run_test_files(
        sorted((TARGET_ROOT / "tests").glob("test_*.py")),
        EXPECTED_NEW_TEST_COUNT,
    )
    baseline_after_tests = _snapshot(EXISTING_EXPORT_ROOT)
    if baseline_after_tests != baseline_before:
        raise RuntimeError("existing artifact SHA changed during validation")
    report["automated_tests"] = {
        "existing_ps_mht": existing_tests,
        "new_phase4tlsa": new_tests,
        "total_passed": existing_tests["passed"] + new_tests["passed"],
        "all_passed": True,
    }
    report["non_regression_after_tests"] = {
        "artifact_count": len(baseline_after_tests),
        "all_unchanged": baseline_after_tests == baseline_before,
    }
    report["generated_reference_steps"] = sorted(expected_step_counts)
    report["generated_preview_files"] = sorted(
        path.name for path in PREVIEW_ROOT.glob("*") if path.is_file()
    )
    _write_json(validation_path, report)

    phase_paths = _phase_commit_paths()
    commit_audit = _build_commit_audit(starting_state, phase_paths)
    commit_audit["automated_tests"] = {
        "existing": existing_tests["passed"],
        "new": new_tests["passed"],
        "all_passed": True,
    }
    _write_json(commit_audit_path, commit_audit)
    _write_json(PREVIEW_ROOT / "phase4tlsa_commit_audit.json", commit_audit)

    phase_paths = _phase_commit_paths()
    _write_path_manifest(
        phase_manifest_path,
        "Phase 4T-LS-A new and changed files",
        phase_paths,
    )
    combined_paths = sorted(set(baseline_paths) | set(phase_paths))
    _write_path_manifest(
        combined_manifest_path,
        "PS-MHT baseline plus Phase 4T-LS-A",
        combined_paths,
    )

    sha_path = TARGET_ROOT / "SHA256SUMS.txt"
    phase_files = [
        REPOSITORY_ROOT / relative
        for relative in _phase_commit_paths(include_sha_sums=False)
    ]
    _write_sha_sums(phase_files, sha_path)
    delivery_files = [
        REPOSITORY_ROOT / relative for relative in _phase_commit_paths()
    ]
    delivery_path, delivery_sha = _create_delivery_zip(delivery_files)

    return {
        "status": report["status"],
        "existing_tests_passed": existing_tests["passed"],
        "new_tests_passed": new_tests["passed"],
        "existing_artifacts_unchanged": True,
        "reference_step_count": len(expected_step_counts),
        "stl_count": 0,
        "delivery_zip": str(delivery_path),
        "delivery_zip_sha256": delivery_sha,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    result = generate_phase4tlsa()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
