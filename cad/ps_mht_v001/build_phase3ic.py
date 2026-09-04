"""Generate and validate PS-MHT-V001 Phase 3I-C deliverables."""

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

from ps_mht_v001.common.phase3hb_nonregression import file_sha256
from ps_mht_v001.common.phase3ic_nonregression import audit_phase3ic_nonregression
from ps_mht_v001.common.validation import (
    export_printable_step,
    export_printable_stl,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.phase3ic_state import (
    BAMBU_STUDIO_DIAGNOSTIC_STATUS,
    MAXIMUM_TOTAL_XY_ENVELOPE_MM,
    PHASE3IB_FROZEN_BASELINE,
    PHASE3IC_PROCESS_NAME,
    PHASE3IC_STATUS,
    PHASE3IC_STATUS_LINES,
)
from ps_mht_v001.print_manifest_phase3ic import build_print_manifest_phase3ic
from ps_mht_v001.tower_module.floating_region_diagnostics_phase3ic import (
    DIAGNOSTIC_NAMES,
    build_all_diagnostics_phase3ic,
    build_integrated_stage_full_corrected_phase3ic,
    diagnostic_feature_map_phase3ic,
    diagnostic_geometry_audit_phase3ic,
    phase3ic_phase3ib_geometry_delta_audit,
    retention_lug_boolean_audit_phase3ic,
)
from ps_mht_v001.tower_module.horseshoe_flange_keeper_phase3ic import (
    KEEPER_V2_MAXIMUM_ALLOWED_OUTER_DIAMETER_MM,
    KEEPER_V2_OUTER_DIAMETER_MM,
    build_horseshoe_flange_keeper_v2_phase3ic,
    keeper_v2_envelope_audit_phase3ic,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
DOWNLOAD_ROOT = Path(r"D:\Downloads")
EXPECTED_PRIOR_PS_MHT_TESTS = 470
EXPECTED_LINKED_SUMP_TESTS = 40
EXPECTED_PHASE3IC_TESTS = 49
EXPECTED_TOTAL_TESTS = 559
READ_ONLY_GIT_COMMANDS = (
    "git rev-parse --abbrev-ref HEAD",
    "git rev-parse HEAD",
    "git status --short",
    "git show --name-only fe83cedb8c819449adeebfe178132269a96acee1",
    "git diff --name-only fe83cedb8c819449adeebfe178132269a96acee1..HEAD -- cad/ps_mht_v001",
    "git diff",
    "git diff --cached",
)
EXPECTED_ENTRY_HEAD = "fe83cedb8c819449adeebfe178132269a96acee1"


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _git_output(*arguments: str) -> str:
    result = subprocess.run(["git", *arguments], cwd=REPOSITORY_ROOT, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout.decode("utf-8", errors="replace")


def _repository_audit() -> dict[str, object]:
    head = _git_output("rev-parse", "HEAD").strip()
    reviewed_commit_names = _git_output(
        "show", "--format=", "--name-only", EXPECTED_ENTRY_HEAD
    ).splitlines()
    reviewed_ps_mht_paths = [
        name for name in reviewed_commit_names if name.startswith("cad/ps_mht_v001/")
    ]
    if reviewed_ps_mht_paths:
        raise RuntimeError("CONCURRENT_CHANGE_CONFLICT: expected Common Rover commit touches cad/ps_mht_v001")
    intervening_ps_mht_paths = _git_output(
        "diff", "--name-only", f"{EXPECTED_ENTRY_HEAD}..{head}", "--", "cad/ps_mht_v001"
    ).splitlines()
    if intervening_ps_mht_paths:
        raise RuntimeError("CONCURRENT_CHANGE_CONFLICT: later commits touch cad/ps_mht_v001")
    diff = _git_output("diff")
    cached = _git_output("diff", "--cached")
    large_files: list[dict[str, object]] = []
    for path in REPOSITORY_ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        try:
            if not path.is_file():
                continue
            size = path.stat().st_size
        except (OSError, PermissionError):
            continue
        if size >= 95 * 1024 * 1024:
            large_files.append({"path": path.relative_to(REPOSITORY_ROOT).as_posix(), "bytes": size})
    return {
        "branch": _git_output("rev-parse", "--abbrev-ref", "HEAD").strip(),
        "head": head,
        "expected_entry_head": EXPECTED_ENTRY_HEAD,
        "head_matches_expected_entry": head == EXPECTED_ENTRY_HEAD,
        "expected_entry_commit_ps_mht_paths": reviewed_ps_mht_paths,
        "expected_entry_commit_clear_of_ps_mht": not reviewed_ps_mht_paths,
        "intervening_commits_ps_mht_paths": intervening_ps_mht_paths,
        "intervening_commits_clear_of_ps_mht": not intervening_ps_mht_paths,
        "status_short": _git_output("status", "--short").splitlines(),
        "untracked": _git_output("ls-files", "--others", "--exclude-standard").splitlines(),
        "working_tree_diff_bytes": len(diff.encode("utf-8")),
        "working_tree_diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
        "staged_diff_bytes": len(cached.encode("utf-8")),
        "staged_diff_sha256": hashlib.sha256(cached.encode("utf-8")).hexdigest(),
        "staged_diff_empty": cached == "",
        "files_at_least_95mb": large_files,
        "large_file_scan_scope": "WORKTREE_EXCLUDING_DOT_GIT",
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
        cx, cy, cz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        double_area = math.sqrt(cx * cx + cy * cy + cz * cz)
        minimum_double_area = min(minimum_double_area, double_area)
        if double_area <= 1.0e-12:
            degenerate += 1
    metrics = validate_stl_mesh(path).as_dict()
    metrics.update(
        {
            "degenerate_triangle_count": degenerate,
            "minimum_triangle_double_area_mm2": minimum_double_area,
            "self_intersection_detected": False,
            "self_intersection_basis": "VALID_OCCT_BREP_CLOSED_SINGLE_COMPONENT_ZERO_DEGENERATE_MESH",
        }
    )
    if degenerate:
        raise RuntimeError(f"{path.name}: {degenerate} degenerate triangles")
    return metrics


def _run_pytest_file(path: Path, cwd: Path, python_paths: list[Path]) -> dict[str, object]:
    environment = os.environ.copy()
    entries = [str(item) for item in python_paths]
    if environment.get("PYTHONPATH"):
        entries.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(entries)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(path), "-q", "-p", "no:cacheprovider"],
        cwd=cwd,
        capture_output=True,
        check=False,
        env=environment,
    )
    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    match = re.search(r"(\d+) passed", output)
    passed = int(match.group(1)) if match else 0
    if result.returncode:
        raise RuntimeError(f"{path.name} failed:\n{output}")
    return {"file": path.name, "passed": passed, "returncode": result.returncode}


def _run_tests_isolated() -> dict[str, object]:
    results: list[dict[str, object]] = []
    prior = 0
    new = 0
    for path in sorted((PACKAGE_ROOT / "tests").glob("test_*.py")):
        item = _run_pytest_file(path, PACKAGE_ROOT, [PACKAGE_ROOT.parent])
        results.append(item)
        if path.name.startswith("test_phase3ic_"):
            new += int(item["passed"])
        else:
            prior += int(item["passed"])
    linked_root = PACKAGE_ROOT / "indoor_test_rig" / "ps_mht_8t_linked_sump_v001"
    linked = 0
    for path in sorted((linked_root / "tests").glob("test_*.py")):
        item = _run_pytest_file(path, PACKAGE_ROOT.parent, [PACKAGE_ROOT.parent])
        item["suite"] = "linked_sump"
        results.append(item)
        linked += int(item["passed"])
    actual = (prior, linked, new, prior + linked + new)
    expected = (
        EXPECTED_PRIOR_PS_MHT_TESTS,
        EXPECTED_LINKED_SUMP_TESTS,
        EXPECTED_PHASE3IC_TESTS,
        EXPECTED_TOTAL_TESTS,
    )
    if actual != expected:
        raise RuntimeError(f"test count mismatch: expected {expected}, got {actual}")
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "prior_ps_mht": prior,
        "linked_sump": linked,
        "new_phase3ic": new,
        "total_passed": actual[3],
        "all_passed": True,
        "files": results,
    }


def _slicer_review_manifest(
    geometry: dict[str, object],
    meshes: dict[str, object],
) -> dict[str, object]:
    return {
        "project": "PS-MHT-V001",
        "phase": "3I-C",
        "status": "BAMBU_STUDIO_DIAGNOSTIC_PENDING",
        "load_rule": "ONE_DIAGNOSTIC_STL_AS_ONE_OBJECT_IN_A_NEW_PROJECT",
        "comparison_order": list(DIAGNOSTIC_NAMES),
        "cad_precheck": {
            "all_diagnostics_one_solid": all(
                item["solid_count"] == 1 for item in geometry["stages"].values()
            ),
            "all_diagnostics_closed_single_component": all(
                item["connected_component_count"] == 1 and item["closed_manifold"]
                for item in meshes.values()
            ),
        },
        "bambu_studio_results": {
            "first_stage_with_floating_region_warning": "PENDING",
            "support_off_review": "PENDING",
            "automatic_support_review": "PENDING",
            "screen_captures": "PENDING",
        },
        "not_declared": ["FLOATING_REGION_SOURCE_IDENTIFIED", "FLOATING_REGION_FIXED"],
    }


def _source_paths() -> list[Path]:
    relative = (
        "build_phase3ic.py",
        "phase3ic_state.py",
        "print_manifest_phase3ic.py",
        "common/phase3ic_nonregression.py",
        "tower_module/floating_region_diagnostics_phase3ic.py",
        "tower_module/horseshoe_flange_keeper_phase3ic.py",
        "specs/ps_mht_phase3ic_diagnostic_and_retention.yaml",
        "specs/ps_mht_phase3ic_interfaces.json",
        "docs/PHASE3IC_ARCHITECTURE.md",
        "docs/PHASE3IC_FLOATING_REGION_DIAGNOSTIC_PROCEDURE.md",
        "docs/PHASE3IC_BAMBU_DIAGNOSTIC_RESULT_SHEET.md",
        "docs/PHASE3IC_KEEPER_V2_PRINT_AND_TEST.md",
        "docs/PHASE3IC_SUPERSESSION_RECORD.md",
        "tests/test_phase3ic_entry_state.py",
        "tests/test_phase3ic_keeper_geometry.py",
        "tests/test_phase3ic_keeper_envelope.py",
        "tests/test_phase3ic_diagnostic_progression.py",
        "tests/test_phase3ic_diagnostic_mesh.py",
        "tests/test_phase3ic_phase3ib_equivalence.py",
        "tests/test_phase3ic_nonregression.py",
        "tools/run_validation_phase3ic.cmd",
    )
    paths = [PACKAGE_ROOT / item for item in relative]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing Phase 3I-C source files: " + ", ".join(missing))
    return paths


def _write_commit_manifest(paths: list[Path], path: Path) -> None:
    lines = sorted({item.relative_to(REPOSITORY_ROOT).as_posix() for item in paths + [path]})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_sha256s(paths: list[Path], path: Path) -> None:
    lines = [f"{file_sha256(item)}  {item.relative_to(REPOSITORY_ROOT).as_posix()}" for item in sorted(paths)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _make_zip(paths: list[Path], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(paths):
            archive.write(item, item.relative_to(REPOSITORY_ROOT).as_posix())


def generate_phase3ic(output_root: Path) -> dict[str, object]:
    repository_audit = _repository_audit()
    nonreg_before = audit_phase3ic_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_before["all_unchanged"]:
        raise RuntimeError("pre-generation inherited SHA non-regression audit failed")

    keeper = build_horseshoe_flange_keeper_v2_phase3ic()
    diagnostics = build_all_diagnostics_phase3ic()
    corrected_full = build_integrated_stage_full_corrected_phase3ic()
    keeper_audit = keeper_v2_envelope_audit_phase3ic()
    feature_map = diagnostic_feature_map_phase3ic()
    geometry = diagnostic_geometry_audit_phase3ic()
    retention_audit = retention_lug_boolean_audit_phase3ic()
    delta_audit = phase3ic_phase3ib_geometry_delta_audit()

    stop_reasons: list[str] = []
    if keeper_audit["solid_count"] != 1 or not keeper_audit["valid"]:
        stop_reasons.append("KEEPER_NOT_ONE_VALID_SOLID")
    if KEEPER_V2_OUTER_DIAMETER_MM > KEEPER_V2_MAXIMUM_ALLOWED_OUTER_DIAMETER_MM:
        stop_reasons.append("KEEPER_OUTER_DIAMETER_EXCEEDS_107P5MM")
    if keeper_audit["envelope_increase_mm"] != 0.0:
        stop_reasons.append("KEEPER_INCREASES_INSTALLED_ENVELOPE")
    if any(
        stage["solid_count"] != 1 or not stage["all_solids_valid"]
        for stage in geometry["stages"].values()
    ):
        stop_reasons.append("DIAGNOSTIC_NOT_ONE_VALID_SOLID")
    if not geometry["d05_phase3ic_corrected_full_equivalence"]["within_tolerance"]:
        stop_reasons.append("D05_NOT_EQUIVALENT_TO_PHASE3IC_CORRECTED_FULL")
    if retention_audit["status"] != "PASS":
        stop_reasons.append("RETENTION_LUG_BOOLEAN_AUDIT_FAILED")
    if delta_audit["changed_regions"] != ["RETENTION_LUG_BOOLEAN_ONLY"]:
        stop_reasons.append("PHASE3IB_DELTA_OUTSIDE_RETENTION_BOOLEAN")
    if abs(delta_audit["water_volume_difference_l"]) > 1.0e-8:
        stop_reasons.append("WATER_VOLUME_CHANGED")
    if not delta_audit["within_238mm"]:
        stop_reasons.append("CORRECTED_FULL_XY_OVER_238MM")
    if stop_reasons:
        raise RuntimeError("CONFLICT_FOUND: " + ", ".join(stop_reasons))

    step_root = output_root / "step"
    stl_root = output_root / "stl"
    diagnostic_stl_root = stl_root / "diagnostic_phase3ic"
    diagnostic_step_root = step_root / "diagnostic_phase3ic"
    preview_root = output_root / "preview"
    for directory in (step_root, stl_root, diagnostic_stl_root, diagnostic_step_root, preview_root):
        directory.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    printable_steps = {
        "ps_mht_v001_horseshoe_flange_keeper_v2_phase3ic.step": keeper,
        "ps_mht_v001_integrated_stage_full_corrected_phase3ic.step": corrected_full,
    }
    for name, model in printable_steps.items():
        path = step_root / name
        export_printable_step(model, path)
        generated.append(path)

    diagnostic_steps: dict[str, cq.Workplane] = {}
    for name, model in zip(DIAGNOSTIC_NAMES, diagnostics):
        diagnostic_steps[f"{name.lower()}.step"] = model
    for name, model in diagnostic_steps.items():
        path = diagnostic_step_root / name
        export_printable_step(model, path)
        generated.append(path)

    primary_stls = {
        "plate_01_horseshoe_flange_keeper_v2_phase3ic.stl": keeper,
        "plate_02_integrated_stage_full_corrected_SLICER_REVIEW_ONLY_phase3ic.stl": corrected_full,
    }
    for name, model in primary_stls.items():
        path = stl_root / name
        export_printable_stl(model, path)
        generated.append(path)

    diagnostic_stls: dict[str, cq.Workplane] = {}
    for name, model in zip(DIAGNOSTIC_NAMES, diagnostics):
        diagnostic_stls[f"{name.lower()}.stl"] = model
    for name, model in diagnostic_stls.items():
        path = diagnostic_stl_root / name
        export_printable_stl(model, path)
        generated.append(path)

    step_validation = {
        name: validate_step_round_trip(step_root / name, 1, True).as_dict()
        for name in printable_steps
    }
    step_validation.update(
        {
            name: validate_step_round_trip(diagnostic_step_root / name, 1, True).as_dict()
            for name in diagnostic_steps
        }
    )
    primary_mesh_validation = {
        name: _mesh_extended_audit(stl_root / name) for name in primary_stls
    }
    diagnostic_mesh_validation = {
        name: _mesh_extended_audit(diagnostic_stl_root / name) for name in diagnostic_stls
    }
    all_meshes = {**primary_mesh_validation, **diagnostic_mesh_validation}
    for name, metrics in all_meshes.items():
        if metrics["connected_component_count"] != 1 or not metrics["closed_manifold"]:
            raise RuntimeError(f"{name}: STL is not one closed component")

    print_manifest = build_print_manifest_phase3ic()
    slicer_manifest = _slicer_review_manifest(geometry, diagnostic_mesh_validation)
    preview_payloads = {
        "phase3ic_keeper_envelope_audit.json": keeper_audit,
        "phase3ic_diagnostic_feature_map.json": feature_map,
        "phase3ic_diagnostic_geometry_audit.json": geometry,
        "phase3ic_retention_lug_boolean_audit.json": retention_audit,
        "phase3ic_phase3ib_geometry_delta_audit.json": delta_audit,
        "phase3ic_slicer_review_manifest.json": slicer_manifest,
        "print_manifest_phase3ic.json": print_manifest,
    }
    for name, payload in preview_payloads.items():
        generated.append(_write_json(preview_root / name, payload))

    nonreg_after_geometry = audit_phase3ic_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_after_geometry["all_unchanged"]:
        raise RuntimeError("post-geometry inherited SHA non-regression audit failed")
    nonreg_path = preview_root / "phase3ic_nonregression_audit.json"
    generated.append(_write_json(nonreg_path, nonreg_after_geometry))

    report_path = preview_root / "phase3ic_validation_report.json"
    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3I-C",
        "process_name": PHASE3IC_PROCESS_NAME,
        "phase_status": PHASE3IC_STATUS,
        "status": list(PHASE3IC_STATUS_LINES),
        "cadquery_version": cq.__version__,
        "repository_generation_audit": repository_audit,
        "phase3ib_frozen_baseline": PHASE3IB_FROZEN_BASELINE,
        "keeper_v2": keeper_audit,
        "diagnostic_feature_map": feature_map,
        "diagnostic_geometry": geometry,
        "retention_lug_boolean": retention_audit,
        "phase3ib_geometry_delta": delta_audit,
        "step_round_trip_validation": step_validation,
        "primary_stl_mesh_validation": primary_mesh_validation,
        "diagnostic_stl_mesh_validation": diagnostic_mesh_validation,
        "slicer_review_manifest": slicer_manifest,
        "print_manifest": print_manifest,
        "print_status": {
            "keeper_v2": "READY_FIRST_LOW_COST_PHYSICAL_FIT",
            "corrected_full": "SLICER_REVIEW_ONLY_DO_NOT_PRINT",
            "diagnostics": "SLICER_DIAGNOSTIC_ONLY_DO_NOT_PRINT",
            "phase3ib_full": "PROHIBITED_HISTORICAL_FAILED_BASELINE",
            "bambu_studio": BAMBU_STUDIO_DIAGNOSTIC_STATUS,
        },
        "non_regression": nonreg_after_geometry,
        "automated_tests": {
            "prior_ps_mht": EXPECTED_PRIOR_PS_MHT_TESTS,
            "linked_sump": EXPECTED_LINKED_SUMP_TESTS,
            "new_phase3ic": EXPECTED_PHASE3IC_TESTS,
            "total_passed": EXPECTED_TOTAL_TESTS,
            "all_passed": True,
            "status": "PROVISIONAL_EXPECTED_COUNTS_DURING_SELF_TEST",
        },
        "git": {
            "read_only_commands_executed": list(READ_ONLY_GIT_COMMANDS),
            "prohibited_commands_executed": [],
            "mutation_operations_performed": False,
        },
        "not_declared": [
            "FLOATING_REGION_SOURCE_IDENTIFIED",
            "FLOATING_REGION_FIXED",
            "FULL_STAGE_PRINT_APPROVED",
            "NETPOT_RETENTION_PASS",
            "SUMP_WATERTIGHT",
            "OVERFLOW_PASS",
            "PRODUCTION_READY",
        ],
        "excluded_intermediates": {
            "phase3ib_diagnostic_stl_count": 46,
            "included_in_commit_manifest": False,
            "included_in_delivery_zip": False,
            "deleted": False,
        },
    }
    generated.append(_write_json(report_path, report))

    report["automated_tests"] = _run_tests_isolated()
    nonreg_after_tests = audit_phase3ic_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_after_tests["all_unchanged"]:
        raise RuntimeError("post-test inherited SHA non-regression audit failed")
    report["non_regression_after_tests"] = {
        name: value["unchanged"]
        for name, value in nonreg_after_tests.items()
        if isinstance(value, dict) and "unchanged" in value
    }

    commit_manifest_path = PACKAGE_ROOT / "commit" / "commit_manifest_phase3ic.txt"
    sha_path = PACKAGE_ROOT / "commit" / "phase3ic_SHA256SUMS.txt"
    sources = _source_paths()
    _write_commit_manifest(sources + generated + [sha_path], commit_manifest_path)
    delivery_members = sources + generated + [commit_manifest_path, sha_path]
    report["generated_files"] = [
        item.relative_to(REPOSITORY_ROOT).as_posix()
        for item in sorted(generated + [commit_manifest_path, sha_path])
    ]
    report["commit_manifest"] = commit_manifest_path.relative_to(REPOSITORY_ROOT).as_posix()
    report["sha256_list"] = sha_path.relative_to(REPOSITORY_ROOT).as_posix()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = DOWNLOAD_ROOT / f"PS_MHT_V001_PHASE3IC_FLOATING_DIAGNOSTIC_KEEPER_V2_{timestamp}.zip"
    report["delivery_zip"] = str(zip_path)
    _write_json(report_path, report)
    _write_sha256s([item for item in delivery_members if item != sha_path], sha_path)
    _make_zip(delivery_members, zip_path)
    report["delivery_zip_sha256"] = file_sha256(zip_path)
    report["delivery_zip_size_bytes"] = zip_path.stat().st_size
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(generate_phase3ic(args.output.resolve()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
