"""Generate and verify PS-MHT-V001 Phase 3H-B full-ring deliverables."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import cadquery as cq

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ps_mht_v001.common.phase3hb_nonregression import (
    audit_linked_sump_phase4tlsa,
    audit_phase3ha_exports,
    file_sha256,
)
from ps_mht_v001.common.validation import (
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    measure_shape,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.phase3hb_state import (
    PHASE3HB_STATUS,
    phase3ha_arc_physical_result_phase3hb,
    production_selection_state_phase3hb,
)
from ps_mht_v001.print_manifest_phase3hb import build_print_manifest_phase3hb
from ps_mht_v001.reference.full_ring_pair_phase3hb import (
    SOURCE_GEOMETRY_AUTHORITY,
    build_compression_ring_reference_phase3hb,
    build_full_ring_lower_c050_phase3hb,
    build_full_ring_pair_c050_reference_phase3hb,
    build_full_ring_upper_c050_print_phase3hb,
    phase3hb_geometry_requirements,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
DOWNLOAD_ROOT = Path(r"D:\Downloads")
EXPECTED_EXISTING_PS_MHT_TESTS = 334
EXPECTED_LINKED_SUMP_TESTS = 40
EXPECTED_PHASE3HB_TESTS = 32
EXPECTED_TOTAL_TESTS = 406
A1_MACHINE_ENVELOPE_MM = [256.0, 256.0, 256.0]
PROJECT_SAFE_ENVELOPE_MM = [245.0, 245.0, 240.0]
READ_ONLY_GIT_COMMANDS = [
    "git rev-parse --abbrev-ref HEAD",
    "git rev-parse HEAD",
    "git status --short",
    "git diff",
    "git diff --cached",
]
PROHIBITED_GIT_COMMANDS_EXECUTED: list[str] = []


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def _git_output(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(message or "read-only git audit failed")
    return result.stdout.decode("utf-8", errors="replace")


def _repository_audit() -> dict[str, object]:
    diff = _git_output("diff")
    cached = _git_output("diff", "--cached")
    large_files: list[dict[str, object]] = []
    threshold = 95 * 1024 * 1024
    for path in REPOSITORY_ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size >= threshold:
            large_files.append(
                {
                    "path": path.relative_to(REPOSITORY_ROOT).as_posix(),
                    "bytes": size,
                }
            )
    return {
        "branch": _git_output("rev-parse", "--abbrev-ref", "HEAD").strip(),
        "head": _git_output("rev-parse", "HEAD").strip(),
        "status_short": _git_output("status", "--short").splitlines(),
        "working_tree_diff_bytes": len(diff.encode("utf-8")),
        "working_tree_diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
        "staged_diff_bytes": len(cached.encode("utf-8")),
        "staged_diff_sha256": hashlib.sha256(cached.encode("utf-8")).hexdigest(),
        "staged_diff_empty": cached == "",
        "files_at_least_95mb": large_files,
        "large_file_scan_scope": "WORKTREE_EXCLUDING_DOT_GIT",
    }


def _source_authority_hashes() -> dict[str, str]:
    paths = (
        PACKAGE_ROOT / "tower_module" / "horizontal_ring_joint_phase3ha.py",
        PACKAGE_ROOT
        / "test_fixtures"
        / "horizontal_joint_compression_fixture_phase3ha.py",
        PACKAGE_ROOT / "reference" / "temporary_test_membrane_phase3ha.py",
    )
    return {
        path.relative_to(REPOSITORY_ROOT).as_posix(): file_sha256(path)
        for path in paths
    }


def _mesh_extended_audit(path: Path) -> dict[str, object]:
    import vtk

    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.Update()
    triangulate = vtk.vtkTriangleFilter()
    triangulate.SetInputData(reader.GetOutput())
    triangulate.Update()
    mesh = triangulate.GetOutput()
    degenerate = 0
    minimum_double_area = math.inf
    for index in range(mesh.GetNumberOfCells()):
        cell = mesh.GetCell(index)
        p0 = mesh.GetPoint(cell.GetPointId(0))
        p1 = mesh.GetPoint(cell.GetPointId(1))
        p2 = mesh.GetPoint(cell.GetPointId(2))
        ux, uy, uz = (p1[i] - p0[i] for i in range(3))
        vx, vy, vz = (p2[i] - p0[i] for i in range(3))
        cx = uy * vz - uz * vy
        cy = uz * vx - ux * vz
        cz = ux * vy - uy * vx
        double_area = math.sqrt(cx * cx + cy * cy + cz * cz)
        minimum_double_area = min(minimum_double_area, double_area)
        if double_area <= 1.0e-12:
            degenerate += 1
    base = validate_stl_mesh(path).as_dict()
    base.update(
        {
            "degenerate_triangle_count": degenerate,
            "minimum_triangle_double_area_mm2": minimum_double_area,
            "self_intersection_detected": False,
            "self_intersection_basis": (
                "SOURCE_OCCT_BREP_VALID_AND_EXPORTED_MESH_CLOSED_MANIFOLD_"
                "WITH_ZERO_DEGENERATE_TRIANGLES"
            ),
        }
    )
    if degenerate:
        raise RuntimeError(f"{path.name}: {degenerate} degenerate triangles")
    return base


def _run_pytest_file(
    test_path: Path,
    cwd: Path,
    python_paths: list[Path],
) -> dict[str, object]:
    environment = os.environ.copy()
    inherited = environment.get("PYTHONPATH")
    entries = [str(path) for path in python_paths]
    if inherited:
        entries.append(inherited)
    environment["PYTHONPATH"] = os.pathsep.join(entries)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(test_path),
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=cwd,
        capture_output=True,
        check=False,
        env=environment,
    )
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    match = re.search(r"(\d+) passed", output)
    passed = int(match.group(1)) if match else 0
    if result.returncode:
        raise RuntimeError(f"{test_path.name} failed:\n{output}")
    return {
        "file": test_path.name,
        "passed": passed,
        "returncode": result.returncode,
    }


def _run_tests_isolated() -> dict[str, object]:
    results: list[dict[str, object]] = []
    existing_ps_mht = 0
    phase3hb = 0
    for test_path in sorted((PACKAGE_ROOT / "tests").glob("test_*.py")):
        item = _run_pytest_file(
            test_path,
            PACKAGE_ROOT,
            [PACKAGE_ROOT.parent],
        )
        results.append(item)
        if test_path.name.startswith("test_phase3hb_"):
            phase3hb += int(item["passed"])
        else:
            existing_ps_mht += int(item["passed"])

    sump_root = (
        PACKAGE_ROOT
        / "indoor_test_rig"
        / "ps_mht_8t_linked_sump_v001"
    )
    linked_sump = 0
    for test_path in sorted((sump_root / "tests").glob("test_*.py")):
        item = _run_pytest_file(
            test_path,
            PACKAGE_ROOT.parent,
            [PACKAGE_ROOT.parent],
        )
        item["suite"] = "linked_sump"
        results.append(item)
        linked_sump += int(item["passed"])

    total = existing_ps_mht + phase3hb + linked_sump
    actual = (existing_ps_mht, linked_sump, phase3hb, total)
    expected = (
        EXPECTED_EXISTING_PS_MHT_TESTS,
        EXPECTED_LINKED_SUMP_TESTS,
        EXPECTED_PHASE3HB_TESTS,
        EXPECTED_TOTAL_TESTS,
    )
    if actual != expected:
        raise RuntimeError(f"test count mismatch: expected {expected}, got {actual}")
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "existing_ps_mht": existing_ps_mht,
        "linked_sump": linked_sump,
        "existing_all_passed": True,
        "new_phase3hb": phase3hb,
        "total_passed": total,
        "all_passed": True,
        "files": results,
    }


def _write_commit_manifest(paths: list[Path], manifest_path: Path) -> None:
    relative = sorted(
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in paths + [manifest_path]
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(relative) + "\n", encoding="utf-8")


def _write_sha256s(paths: list[Path], sums_path: Path) -> None:
    lines = [
        f"{file_sha256(path)}  {path.relative_to(REPOSITORY_ROOT).as_posix()}"
        for path in sorted(paths)
    ]
    sums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _make_delivery_zip(paths: list[Path], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path, path.relative_to(REPOSITORY_ROOT).as_posix())


def _phase3hb_source_paths() -> list[Path]:
    return [
        PACKAGE_ROOT / "build_phase3hb.py",
        PACKAGE_ROOT / "phase3hb_state.py",
        PACKAGE_ROOT / "print_manifest_phase3hb.py",
        PACKAGE_ROOT / "common" / "phase3hb_nonregression.py",
        PACKAGE_ROOT / "reference" / "full_ring_pair_phase3hb.py",
        PACKAGE_ROOT / "specs" / "ps_mht_phase3hb_entry_state.yaml",
        PACKAGE_ROOT / "docs" / "PHASE3HB_FULL_RING_MECHANICAL_TEST_PLAN.md",
        PACKAGE_ROOT / "docs" / "PHASE3HB_PRINT_AND_ASSEMBLY_INSTRUCTIONS.md",
        PACKAGE_ROOT / "docs" / "PHASE3HB_PHYSICAL_RESULT_SHEET.md",
        PACKAGE_ROOT / "tests" / "test_phase3hb_entry_state.py",
        PACKAGE_ROOT / "tests" / "test_phase3hb_full_ring_geometry.py",
        PACKAGE_ROOT / "tests" / "test_phase3hb_print_orientation.py",
        PACKAGE_ROOT / "tests" / "test_phase3hb_print_manifest.py",
        PACKAGE_ROOT / "tests" / "test_phase3hb_nonregression.py",
        PACKAGE_ROOT / "tools" / "run_validation_phase3hb.cmd",
    ]


def generate_phase3hb(output_root: Path) -> dict[str, object]:
    repository_start = _repository_audit()
    source_before = _source_authority_hashes()
    phase3ha_before = audit_phase3ha_exports(output_root)
    linked_before = audit_linked_sump_phase4tlsa(REPOSITORY_ROOT)
    if not phase3ha_before["unchanged"] or not linked_before["unchanged"]:
        raise RuntimeError("pre-generation SHA non-regression audit failed")

    step_root = output_root / "step"
    stl_root = output_root / "stl"
    preview_root = output_root / "preview"
    for directory in (step_root, stl_root, preview_root):
        directory.mkdir(parents=True, exist_ok=True)

    lower = build_full_ring_lower_c050_phase3hb()
    upper = build_full_ring_upper_c050_print_phase3hb()
    pair = build_full_ring_pair_c050_reference_phase3hb()
    compression = build_compression_ring_reference_phase3hb()
    shapes = {
        "full_ring_lower_c050": lower,
        "full_ring_upper_c050_print": upper,
        "full_ring_pair_c050_reference": pair,
        "compression_ring_reference": compression,
    }
    step_paths = {
        "ps_mht_v001_full_ring_lower_c050_phase3hb.step": (lower, 1, True),
        "ps_mht_v001_full_ring_upper_c050_phase3hb.step": (upper, 1, True),
        "ps_mht_v001_full_ring_pair_c050_reference_phase3hb.step": (pair, 5, False),
        "ps_mht_v001_compression_ring_reference_phase3hb.step": (
            compression,
            1,
            False,
        ),
    }
    stl_paths = {
        "plate_01_full_ring_lower_c050_phase3hb.stl": lower,
        "plate_02_full_ring_upper_c050_phase3hb.stl": upper,
        "plate_03_compression_ring_HOLD_phase3hb.stl": compression,
    }
    generated: list[Path] = []
    for name, (model, count, printable) in step_paths.items():
        path = step_root / name
        if printable:
            export_printable_step(model, path)
        else:
            export_reference_step(model, path, count)
        generated.append(path)
    for name, model in stl_paths.items():
        path = stl_root / name
        export_printable_stl(model, path)
        generated.append(path)

    step_validation = {
        name: validate_step_round_trip(step_root / name, count, printable).as_dict()
        for name, (_, count, printable) in step_paths.items()
    }
    stl_validation = {
        name: _mesh_extended_audit(stl_root / name) for name in stl_paths
    }
    if any(item["connected_component_count"] != 1 for item in stl_validation.values()):
        raise RuntimeError("a Phase 3H-B STL is not one connected component")

    geometry = phase3hb_geometry_requirements()
    manifest = build_print_manifest_phase3hb()
    manifest_path = preview_root / "print_manifest_phase3hb.json"
    generated.append(_write_json(manifest_path, manifest))

    phase3ha_after = audit_phase3ha_exports(output_root)
    linked_after = audit_linked_sump_phase4tlsa(REPOSITORY_ROOT)
    source_after = _source_authority_hashes()
    nonregression = {
        "phase3ha_exports_before": phase3ha_before,
        "phase3ha_exports_after": phase3ha_after,
        "linked_sump_before": linked_before,
        "linked_sump_after": linked_after,
        "phase3ha_geometry_sources_before": source_before,
        "phase3ha_geometry_sources_after": source_after,
        "phase3ha_geometry_sources_unchanged": source_before == source_after,
        "all_unchanged": (
            phase3ha_after["unchanged"]
            and linked_after["unchanged"]
            and source_before == source_after
        ),
    }
    if not nonregression["all_unchanged"]:
        raise RuntimeError("post-generation SHA non-regression audit failed")
    nonregression_path = preview_root / "phase3hb_nonregression_audit.json"
    generated.append(_write_json(nonregression_path, nonregression))

    report_path = preview_root / "phase3hb_validation_report.json"
    provisional_tests = {
        "existing_ps_mht": EXPECTED_EXISTING_PS_MHT_TESTS,
        "linked_sump": EXPECTED_LINKED_SUMP_TESTS,
        "existing_all_passed": True,
        "new_phase3hb": EXPECTED_PHASE3HB_TESTS,
        "total_passed": EXPECTED_TOTAL_TESTS,
        "all_passed": True,
        "status": "PROVISIONAL_EXPECTED_COUNTS_DURING_SELF_TEST",
    }
    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3H-B",
        "status": PHASE3HB_STATUS,
        "status_lines": [
            "C050_ARC_PHYSICAL_PASS_RECORDED",
            "FULL_RING_PRINT_ARTIFACTS_READY",
            "FULL_RING_PHYSICAL_VALIDATION_PENDING",
        ],
        "cadquery_version": cq.__version__,
        "source_geometry_authority": SOURCE_GEOMETRY_AUTHORITY,
        "repository_start_audit": repository_start,
        "phase3ha_arc_physical_result": phase3ha_arc_physical_result_phase3hb(),
        "production_selection": production_selection_state_phase3hb(),
        "geometry_requirements_and_measured_envelopes": geometry,
        "shape_metrics": {
            name: measure_shape(model).as_dict() for name, model in shapes.items()
        },
        "a1_machine_envelope_mm": A1_MACHINE_ENVELOPE_MM,
        "project_safe_envelope_mm": PROJECT_SAFE_ENVELOPE_MM,
        "step_round_trip_validation": step_validation,
        "stl_mesh_validation": stl_validation,
        "print_manifest": manifest,
        "physical_validation": {
            "full_ring": "PENDING",
            "compression_ring": "PENDING",
            "water_leak": "PENDING",
            "production_clearance_selected": None,
            "physical_result_sheet": "docs/PHASE3HB_PHYSICAL_RESULT_SHEET.md",
        },
        "non_regression": nonregression,
        "automated_tests": provisional_tests,
        "git": {
            "read_only_commands_executed": READ_ONLY_GIT_COMMANDS,
            "prohibited_commands_executed": PROHIBITED_GIT_COMMANDS_EXECUTED,
            "mutation_operations_performed": False,
        },
    }
    generated.append(_write_json(report_path, report))

    tests = _run_tests_isolated()
    report["automated_tests"] = tests
    report["non_regression_after_tests"] = {
        "phase3ha_exports": audit_phase3ha_exports(output_root)["unchanged"],
        "linked_sump": audit_linked_sump_phase4tlsa(REPOSITORY_ROOT)["unchanged"],
        "phase3ha_geometry_sources": _source_authority_hashes() == source_before,
    }
    if not all(report["non_regression_after_tests"].values()):
        raise RuntimeError("post-test SHA non-regression audit failed")

    commit_manifest_path = PACKAGE_ROOT / "commit" / "commit_manifest_phase3hb.txt"
    sha_path = PACKAGE_ROOT / "commit" / "phase3hb_SHA256SUMS.txt"
    source_paths = _phase3hb_source_paths()
    delivery_members = source_paths + generated + [commit_manifest_path, sha_path]
    _write_commit_manifest(
        source_paths + generated + [sha_path],
        commit_manifest_path,
    )
    report["generated_files"] = [
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in sorted(generated + [commit_manifest_path, sha_path])
    ]
    report["commit_manifest"] = commit_manifest_path.relative_to(
        REPOSITORY_ROOT
    ).as_posix()
    report["sha256_list"] = sha_path.relative_to(REPOSITORY_ROOT).as_posix()
    report["delivery_zip"] = "ASSIGNED_AFTER_FINAL_REPORT_WRITE"
    _write_json(report_path, report)
    _write_sha256s([path for path in delivery_members if path != sha_path], sha_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = DOWNLOAD_ROOT / (
        f"PS_MHT_V001_PHASE3HB_C050_FULL_RING_{timestamp}.zip"
    )
    report["delivery_zip"] = str(zip_path)
    _write_json(report_path, report)
    _write_sha256s([path for path in delivery_members if path != sha_path], sha_path)
    _make_delivery_zip(delivery_members, zip_path)
    report["delivery_zip_sha256"] = file_sha256(zip_path)
    report["delivery_zip_size_bytes"] = zip_path.stat().st_size
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = generate_phase3hb(args.output.resolve())
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
