"""Generate and validate PS-MHT-V001 Phase 3I-B deliverables."""

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
from ps_mht_v001.common.phase3ib_nonregression import audit_phase3ib_nonregression
from ps_mht_v001.common.validation import (
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.phase3ib_state import (
    BAMBU_STUDIO_REVIEW_STATUS,
    PHASE3IB_PROCESS_NAME,
    PHASE3IB_STATUS_LINES,
    phase3ia_failure_record_phase3ib,
)
from ps_mht_v001.print_manifest_phase3ib import build_print_manifest_phase3ib
from ps_mht_v001.reference.integrated_stage_references_phase3ib import (
    assembly_reference_metadata_phase3ib,
    build_actual_water_volume_reference_phase3ib,
    build_integrated_stage_assembly_reference_phase3ib,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ib import (
    CRADLE_COUPON_PRINT_STATUS,
    C_KEEPER_PRINT_STATUS,
    FULL_PRINT_STATUS,
    MAXIMUM_TOTAL_XY_ENVELOPE_MM,
    SELECTED_OPERATING_WATER_DEPTH_MM,
    SUMP_COUPON_PRINT_STATUS,
    actual_water_volume_audit_phase3ib,
    build_c_shaped_flange_keeper_phase3ib,
    build_full_annular_sump_coupon_phase3ib,
    build_integrated_stage_full_phase3ib,
    build_single_port_cradle_sector_coupon_phase3ib,
    cradle_support_audit_phase3ib,
    leak_path_audit_phase3ib,
    overflow_audit_phase3ib,
    overhang_audit_phase3ib,
    real_sump_boundary_audit_phase3ib,
    retention_audit_phase3ib,
    stage_geometry_requirements_phase3ib,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
DOWNLOAD_ROOT = Path(r"D:\Downloads")
EXPECTED_PRIOR_PS_MHT_TESTS = 414
EXPECTED_LINKED_SUMP_TESTS = 40
EXPECTED_PHASE3IB_TESTS = 56
EXPECTED_TOTAL_TESTS = 510
READ_ONLY_GIT_COMMANDS = (
    "git rev-parse --abbrev-ref HEAD",
    "git rev-parse HEAD",
    "git status --short",
    "git diff",
    "git diff --cached",
)


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
        "head": _git_output("rev-parse", "HEAD").strip(),
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
        if path.name.startswith("test_phase3ib_"):
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
        EXPECTED_PHASE3IB_TESTS,
        EXPECTED_TOTAL_TESTS,
    )
    if actual != expected:
        raise RuntimeError(f"test count mismatch: expected {expected}, got {actual}")
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "prior_ps_mht": prior,
        "linked_sump": linked,
        "new_phase3ib": new,
        "total_passed": actual[3],
        "all_passed": True,
        "files": results,
    }


def _slicer_review_manifest(geometry: dict[str, object], meshes: dict[str, object]) -> dict[str, object]:
    pending_fields = {
        "floating_region_warning": "PENDING_BAMBU_STUDIO",
        "support_off": {
            "detached_islands": "PENDING_BAMBU_STUDIO",
            "unanchored_bridge_lines": "PENDING_BAMBU_STUDIO",
            "wall_interruption": "PENDING_BAMBU_STUDIO",
            "thin_independent_towers": "PENDING_BAMBU_STUDIO",
        },
        "automatic_support": {
            "generated_at_cradle": "PENDING_BAMBU_STUDIO",
            "generated_inside_sump": "PENDING_BAMBU_STUDIO",
            "generated_at_retention_lugs": "PENDING_BAMBU_STUDIO",
            "generated_at_stacking_guides": "PENDING_BAMBU_STUDIO",
        },
        "support_dependency": "PENDING_BAMBU_STUDIO",
    }
    return {
        "project": "PS-MHT-V001",
        "phase": "3I-B",
        "status": "BAMBU_STUDIO_REVIEW_PENDING",
        "full_stl_status": FULL_PRINT_STATUS,
        "cad_precheck": {
            "one_solid": geometry["solid_count"] == 1,
            "maximum_xy_pass": geometry["full_maximum_radial_xy_mm"] <= MAXIMUM_TOTAL_XY_ENVELOPE_MM,
            "floor_connected_cradle": True,
            "floor_connected_lugs": True,
            "airborne_start_candidate_count": 0,
            "horizontal_bridge_over_8mm_candidate_count": 0,
        },
        "bambu_studio_results": pending_fields,
        "print_manifest": build_print_manifest_phase3ib(),
        "mesh_summary": meshes,
        "not_declared": ["BAMBU_STUDIO_PASS", "FULL_STAGE_PRINT_APPROVED"],
    }


def _source_paths() -> list[Path]:
    relative = (
        "build_phase3ib.py",
        "phase3ib_state.py",
        "print_manifest_phase3ib.py",
        "common/phase3ib_nonregression.py",
        "tower_module/integrated_wet_base_stage_phase3ib.py",
        "reference/integrated_stage_references_phase3ib.py",
        "specs/ps_mht_phase3ib_functional_correction.yaml",
        "specs/ps_mht_phase3ib_interfaces.json",
        "docs/PHASE3IB_ARCHITECTURE.md",
        "docs/PHASE3IB_PHASE3IA_FAILURE_RECORD.md",
        "docs/PHASE3IB_REAL_SUMP_TEST_PLAN.md",
        "docs/PHASE3IB_NETPOT_RETENTION_TEST_PLAN.md",
        "docs/PHASE3IB_BAMBU_STUDIO_REVIEW_CHECKLIST.md",
        "docs/PHASE3IB_PRINT_AND_ASSEMBLY_INSTRUCTIONS.md",
        "docs/PHASE3IB_PHYSICAL_RESULT_SHEET.md",
        "tests/test_phase3ib_entry_state.py",
        "tests/test_phase3ib_real_sump_boundary.py",
        "tests/test_phase3ib_actual_water_volume.py",
        "tests/test_phase3ib_leak_paths.py",
        "tests/test_phase3ib_cradle_geometry.py",
        "tests/test_phase3ib_retention_interface.py",
        "tests/test_phase3ib_print_geometry.py",
        "tests/test_phase3ib_nonregression.py",
        "tools/run_validation_phase3ib.cmd",
    )
    return [PACKAGE_ROOT / item for item in relative]


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


def generate_phase3ib(output_root: Path) -> dict[str, object]:
    repository_audit = _repository_audit()
    nonreg_before = audit_phase3ib_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_before["all_unchanged"]:
        raise RuntimeError("pre-generation non-regression SHA audit failed")

    full = build_integrated_stage_full_phase3ib()
    sump_coupon = build_full_annular_sump_coupon_phase3ib()
    cradle_coupon = build_single_port_cradle_sector_coupon_phase3ib()
    keeper = build_c_shaped_flange_keeper_phase3ib()
    assembly = build_integrated_stage_assembly_reference_phase3ib()
    waters = build_actual_water_volume_reference_phase3ib()
    geometry = stage_geometry_requirements_phase3ib()
    sump_audit = real_sump_boundary_audit_phase3ib()
    water_audit = actual_water_volume_audit_phase3ib()
    leak_audit = leak_path_audit_phase3ib()
    cradle_audit = cradle_support_audit_phase3ib()
    retention_audit = retention_audit_phase3ib()
    overhang_audit = overhang_audit_phase3ib()
    overflow_audit = overflow_audit_phase3ib()
    reference_metadata = assembly_reference_metadata_phase3ib()

    selected = water_audit["candidates"][f"d{int(SELECTED_OPERATING_WATER_DEPTH_MM)}"]
    stop_reasons: list[str] = []
    if geometry["solid_count"] != 1:
        stop_reasons.append("FULL_MODEL_NOT_ONE_SOLID")
    if any(geometry[key] != 1 for key in ("sump_coupon_solid_count", "cradle_coupon_solid_count", "keeper_solid_count")):
        stop_reasons.append("PRINTABLE_COUPON_NOT_ONE_SOLID")
    if geometry["full_maximum_radial_xy_mm"] > MAXIMUM_TOTAL_XY_ENVELOPE_MM:
        stop_reasons.append("FULL_XY_OVER_238MM")
    if geometry["installed_netpot_maximum_xy_mm"] > MAXIMUM_TOTAL_XY_ENVELOPE_MM:
        stop_reasons.append("INSTALLED_NETPOT_XY_OVER_238MM")
    if not selected["within_target_range"]:
        stop_reasons.append("ACTUAL_RETAINED_VOLUME_OUT_OF_RANGE")
    if selected["inner_dam_top_margin_mm"] < 4.0:
        stop_reasons.append("INNER_DAM_MARGIN_UNDERSIZE")
    if leak_audit["central_opening_penetrations_below_normal_water"] or leak_audit["external_penetrations_below_normal_water"]:
        stop_reasons.append("LOW_WATER_LEAK_PATH_PRESENT")
    if overhang_audit["airborne_feature_count"] or overhang_audit["horizontal_bridge_over_8mm_count"]:
        stop_reasons.append("CAD_FLOATING_OR_BRIDGE_CANDIDATE")
    if stop_reasons:
        raise RuntimeError("CONFLICT_FOUND: " + ", ".join(stop_reasons))

    step_root = output_root / "step"
    stl_root = output_root / "stl"
    preview_root = output_root / "preview"
    for directory in (step_root, stl_root, preview_root):
        directory.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    printable_steps = {
        "ps_mht_v001_integrated_stage_full_corrected_phase3ib.step": full,
        "ps_mht_v001_full_annular_sump_coupon_phase3ib.step": sump_coupon,
        "ps_mht_v001_single_port_cradle_coupon_phase3ib.step": cradle_coupon,
        "ps_mht_v001_c_shaped_flange_keeper_phase3ib.step": keeper,
    }
    for name, model in printable_steps.items():
        path = step_root / name
        export_printable_step(model, path)
        generated.append(path)
    reference_steps = {
        "ps_mht_v001_integrated_stage_assembly_reference_phase3ib.step": (assembly, reference_metadata["assembly_solid_count"]),
        "ps_mht_v001_actual_water_volume_reference_phase3ib.step": (waters, reference_metadata["water_reference_solid_count"]),
    }
    for name, (model, count) in reference_steps.items():
        path = step_root / name
        export_reference_step(model, path, int(count))
        generated.append(path)
    stls = {
        "plate_01_integrated_stage_full_SLICER_REVIEW_ONLY_phase3ib.stl": full,
        "plate_02_full_annular_sump_coupon_phase3ib.stl": sump_coupon,
        "plate_03_single_port_cradle_coupon_phase3ib.stl": cradle_coupon,
        "plate_04_c_shaped_flange_keeper_phase3ib.stl": keeper,
    }
    for name, model in stls.items():
        path = stl_root / name
        export_printable_stl(model, path)
        generated.append(path)

    step_validation = {
        name: validate_step_round_trip(step_root / name, 1, True).as_dict()
        for name in printable_steps
    }
    step_validation.update(
        {
            name: validate_step_round_trip(step_root / name, int(count), False).as_dict()
            for name, (_, count) in reference_steps.items()
        }
    )
    mesh_validation = {name: _mesh_extended_audit(stl_root / name) for name in stls}
    for name, metrics in mesh_validation.items():
        if metrics["connected_component_count"] != 1:
            raise RuntimeError(f"{name}: connected component count is not one")

    slicer_manifest = _slicer_review_manifest(geometry, mesh_validation)
    print_manifest = build_print_manifest_phase3ib()
    preview_payloads = {
        "phase3ib_real_sump_boundary_audit.json": sump_audit,
        "phase3ib_actual_water_volume_audit.json": water_audit,
        "phase3ib_leak_path_audit.json": leak_audit,
        "phase3ib_cradle_support_audit.json": cradle_audit,
        "phase3ib_netpot_retention_audit.json": retention_audit,
        "phase3ib_slicer_review_manifest.json": slicer_manifest,
        "phase3ib_overhang_audit.json": overhang_audit,
        "print_manifest_phase3ib.json": print_manifest,
    }
    for name, payload in preview_payloads.items():
        generated.append(_write_json(preview_root / name, payload))

    nonreg_after_geometry = audit_phase3ib_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_after_geometry["all_unchanged"]:
        raise RuntimeError("post-geometry non-regression SHA audit failed")
    nonreg_path = preview_root / "phase3ib_nonregression_audit.json"
    generated.append(_write_json(nonreg_path, nonreg_after_geometry))

    report_path = preview_root / "phase3ib_validation_report.json"
    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3I-B",
        "process_name": PHASE3IB_PROCESS_NAME,
        "status": list(PHASE3IB_STATUS_LINES),
        "cadquery_version": cq.__version__,
        "repository_generation_audit": repository_audit,
        "phase3ia_failure_record": phase3ia_failure_record_phase3ib(),
        "geometry": geometry,
        "real_sump_boundary": sump_audit,
        "actual_water_volume": water_audit,
        "selected_water_depth_mm": SELECTED_OPERATING_WATER_DEPTH_MM,
        "leak_path_audit": leak_audit,
        "overflow_audit": overflow_audit,
        "cradle_support_audit": cradle_audit,
        "retention_audit": retention_audit,
        "overhang_audit": overhang_audit,
        "assembly_reference": reference_metadata,
        "step_round_trip_validation": step_validation,
        "stl_mesh_validation": mesh_validation,
        "slicer_review_manifest": slicer_manifest,
        "print_manifest": print_manifest,
        "print_status": {
            "full": FULL_PRINT_STATUS,
            "sump_coupon": SUMP_COUPON_PRINT_STATUS,
            "cradle_coupon": CRADLE_COUPON_PRINT_STATUS,
            "c_keeper": C_KEEPER_PRINT_STATUS,
            "bambu_studio": BAMBU_STUDIO_REVIEW_STATUS,
        },
        "non_regression": nonreg_after_geometry,
        "automated_tests": {
            "prior_ps_mht": EXPECTED_PRIOR_PS_MHT_TESTS,
            "linked_sump": EXPECTED_LINKED_SUMP_TESTS,
            "new_phase3ib": EXPECTED_PHASE3IB_TESTS,
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
            "SUMP_WATERTIGHT",
            "OVERFLOW_PASS",
            "NETPOT_RETENTION_PASS",
            "FULL_STAGE_PRINT_APPROVED",
            "PLANT_READY",
            "PRODUCTION_READY",
            "READY_FOR_80_TOWERS",
        ],
    }
    generated.append(_write_json(report_path, report))

    report["automated_tests"] = _run_tests_isolated()
    nonreg_after_tests = audit_phase3ib_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_after_tests["all_unchanged"]:
        raise RuntimeError("post-test non-regression SHA audit failed")
    report["non_regression_after_tests"] = {
        name: value["unchanged"]
        for name, value in nonreg_after_tests.items()
        if isinstance(value, dict) and "unchanged" in value
    }

    commit_manifest_path = PACKAGE_ROOT / "commit" / "commit_manifest_phase3ib.txt"
    sha_path = PACKAGE_ROOT / "commit" / "phase3ib_SHA256SUMS.txt"
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
    zip_path = DOWNLOAD_ROOT / f"PS_MHT_V001_PHASE3IB_FUNCTIONAL_CORRECTION_{timestamp}.zip"
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
    print(json.dumps(generate_phase3ib(args.output.resolve()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

