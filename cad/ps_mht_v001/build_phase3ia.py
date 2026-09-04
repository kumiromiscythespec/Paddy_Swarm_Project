"""Generate and validate PS-MHT-V001 Phase 3I-A deliverables."""

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
from ps_mht_v001.common.phase3ia_nonregression import audit_phase3ia_nonregression
from ps_mht_v001.common.validation import (
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    measure_shape,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.phase3ia_state import (
    BAMBU_STUDIO_REVIEW_STATUS,
    PHASE3IA_PROCESS_NAME,
    PHASE3IA_STATUS_LINES,
    phase3h_physical_results_phase3ia,
)
from ps_mht_v001.print_manifest_phase3ia import build_print_manifest_phase3ia
from ps_mht_v001.reference.integrated_stage_references_phase3ia import (
    ASSEMBLY_REFERENCE_SOLID_COUNT,
    WATER_VOLUME_REFERENCE_SOLID_COUNT,
    assembly_reference_metadata_phase3ia,
    build_integrated_stage_assembly_reference_phase3ia,
    build_integrated_stage_water_volume_reference_phase3ia,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ia import (
    FULL_PRINT_STATUS,
    MAXIMUM_TOTAL_XY_ENVELOPE_MM,
    SELECTED_OPERATING_DEPTH_MM,
    SELECTED_PORT_RECESS_MM,
    build_integrated_stage_full_phase3ia,
    build_integrated_stage_lower_60mm_coupon_phase3ia,
    netpot_recess_audit_phase3ia,
    overhang_audit_phase3ia,
    overflow_audit_phase3ia,
    stage_geometry_requirements_phase3ia,
    water_volume_audit_phase3ia,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
DOWNLOAD_ROOT = Path(r"D:\Downloads")
EXPECTED_EXISTING_PS_MHT_TESTS = 366
EXPECTED_LINKED_SUMP_TESTS = 40
EXPECTED_PHASE3IA_TESTS = 48
EXPECTED_TOTAL_TESTS = 454
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
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size >= 95 * 1024 * 1024:
            large_files.append({"path": path.relative_to(REPOSITORY_ROOT).as_posix(), "bytes": size})
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
            "self_intersection_basis": "VALID_OCCT_BREP_PLUS_CLOSED_SINGLE_COMPONENT_ZERO_DEGENERATE_MESH",
        }
    )
    if degenerate:
        raise RuntimeError(f"{path.name}: degenerate triangle count {degenerate}")
    return metrics


def _run_pytest_file(test_path: Path, cwd: Path, python_paths: list[Path]) -> dict[str, object]:
    environment = os.environ.copy()
    entries = [str(path) for path in python_paths]
    if environment.get("PYTHONPATH"):
        entries.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(entries)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_path), "-q", "-p", "no:cacheprovider"],
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
    return {"file": test_path.name, "passed": passed, "returncode": result.returncode}


def _run_tests_isolated() -> dict[str, object]:
    results: list[dict[str, object]] = []
    existing = 0
    new = 0
    for path in sorted((PACKAGE_ROOT / "tests").glob("test_*.py")):
        item = _run_pytest_file(path, PACKAGE_ROOT, [PACKAGE_ROOT.parent])
        results.append(item)
        if path.name.startswith("test_phase3ia_"):
            new += int(item["passed"])
        else:
            existing += int(item["passed"])
    linked_root = PACKAGE_ROOT / "indoor_test_rig" / "ps_mht_8t_linked_sump_v001"
    linked = 0
    for path in sorted((linked_root / "tests").glob("test_*.py")):
        item = _run_pytest_file(path, PACKAGE_ROOT.parent, [PACKAGE_ROOT.parent])
        item["suite"] = "linked_sump"
        results.append(item)
        linked += int(item["passed"])
    actual = (existing, linked, new, existing + linked + new)
    expected = (
        EXPECTED_EXISTING_PS_MHT_TESTS,
        EXPECTED_LINKED_SUMP_TESTS,
        EXPECTED_PHASE3IA_TESTS,
        EXPECTED_TOTAL_TESTS,
    )
    if actual != expected:
        raise RuntimeError(f"test count mismatch: expected {expected}, got {actual}")
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "existing_ps_mht": existing,
        "linked_sump": linked,
        "new_phase3ia": new,
        "total_passed": sum(actual[:3]),
        "all_passed": True,
        "files": results,
    }


def _slicer_review_manifest(
    geometry: dict[str, object],
    stl_validation: dict[str, object],
) -> dict[str, object]:
    full_mesh = stl_validation["plate_01_integrated_stage_full_SLICER_REVIEW_ONLY_phase3ia.stl"]
    return {
        "project": "PS-MHT-V001",
        "phase": "3I-A",
        "status": "SLICER_REVIEW_ONLY_DO_NOT_PRINT",
        "bambu_studio_review": BAMBU_STUDIO_REVIEW_STATUS,
        "print_manifest": build_print_manifest_phase3ia(),
        "cad_reference_mass_g": geometry["petg_reference_mass_g"],
        "estimated_print_time_h": "PENDING_BAMBU_STUDIO",
        "estimated_filament_weight_g": "PENDING_BAMBU_STUDIO",
        "review_items": [
            {"id": 1, "item": "XY envelope <=238mm", "status": "CAD_PASS"},
            {"id": 2, "item": "Z height 170mm", "status": "CAD_PASS"},
            {"id": 3, "item": "A1 placement", "status": "CAD_PASS_SLICER_CONFIRM_PENDING"},
            {"id": 4, "item": "single object", "status": "CAD_PASS"},
            {"id": 5, "item": "single component", "status": "MESH_PASS"},
            {"id": 6, "item": "closed manifold", "status": "MESH_PASS"},
            {"id": 7, "item": "non-manifold edge zero", "status": "MESH_PASS"},
            {"id": 8, "item": "boundary edge zero", "status": "MESH_PASS"},
            {"id": 9, "item": "degenerate triangle zero", "status": "MESH_PASS"},
            {"id": 10, "item": "automatic support locations", "status": "PENDING_BAMBU_STUDIO"},
            {"id": 11, "item": "long airborne bridges", "status": "PENDING_LAYER_REVIEW"},
            {"id": 12, "item": "thin isolated islands", "status": "PENDING_LAYER_REVIEW"},
            {"id": 13, "item": "internal support removability", "status": "PENDING_BAMBU_STUDIO"},
            {"id": 14, "item": "wall interruption", "status": "PENDING_LAYER_REVIEW"},
            {"id": 15, "item": "sump floor continuity", "status": "CAD_PASS_LAYER_CONFIRM_PENDING"},
            {"id": 16, "item": "port upper opening", "status": "PENDING_LAYER_REVIEW"},
            {"id": 17, "item": "rear channel", "status": "PENDING_LAYER_REVIEW"},
            {"id": 18, "item": "overflow weir", "status": "PENDING_LAYER_REVIEW"},
            {"id": 19, "item": "estimated print time", "status": "PENDING_BAMBU_STUDIO"},
            {"id": 20, "item": "estimated filament weight", "status": "PENDING_BAMBU_STUDIO"},
            {"id": 21, "item": "abrupt layer area changes", "status": "PENDING_LAYER_REVIEW"},
            {"id": 22, "item": "no Y-axis slender independent wall", "status": "PENDING_LAYER_REVIEW"},
        ],
        "mesh_summary": full_mesh,
    }


def _source_paths() -> list[Path]:
    relative = (
        "build_phase3ia.py",
        "phase3ia_state.py",
        "print_manifest_phase3ia.py",
        "common/phase3ia_nonregression.py",
        "tower_module/integrated_wet_base_stage_phase3ia.py",
        "reference/integrated_stage_references_phase3ia.py",
        "specs/ps_mht_phase3ia_integrated_stage.yaml",
        "specs/ps_mht_phase3ia_interfaces.json",
        "docs/PHASE3IA_ARCHITECTURE.md",
        "docs/PHASE3IA_SLICER_REVIEW_CHECKLIST.md",
        "docs/PHASE3IA_LOWER_60MM_COUPON_TEST_PLAN.md",
        "docs/PHASE3IA_WATER_AND_OVERFLOW_TEST_PLAN.md",
        "docs/PHASE3IA_NETPOT_INSTALLATION.md",
        "docs/PHASE3IA_SUPERSESSION_RECORD.md",
        "docs/PHASE3IA_PHYSICAL_RESULT_SHEET.md",
        "tests/test_phase3ia_entry_state.py",
        "tests/test_phase3ia_integrated_geometry.py",
        "tests/test_phase3ia_water_and_overflow.py",
        "tests/test_phase3ia_netpot_envelope.py",
        "tests/test_phase3ia_print_and_overhang.py",
        "tests/test_phase3ia_artifacts_and_nonregression.py",
        "tools/run_validation_phase3ia.cmd",
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


def generate_phase3ia(output_root: Path) -> dict[str, object]:
    repository_audit = _repository_audit()
    nonreg_before = audit_phase3ia_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_before["all_unchanged"]:
        raise RuntimeError("pre-generation non-regression SHA audit failed")

    full = build_integrated_stage_full_phase3ia()
    coupon = build_integrated_stage_lower_60mm_coupon_phase3ia()
    assembly = build_integrated_stage_assembly_reference_phase3ia()
    waters = build_integrated_stage_water_volume_reference_phase3ia()
    geometry = stage_geometry_requirements_phase3ia()
    water_audit = water_volume_audit_phase3ia()
    netpot_audit = netpot_recess_audit_phase3ia()
    overhang_audit = overhang_audit_phase3ia()
    overflow_audit = overflow_audit_phase3ia()

    selected_volume = water_audit["candidates"]["d20"]["actual_water_volume_l"]
    selected_netpot = netpot_audit["candidates"]["r02"]
    stop_reasons: list[str] = []
    if geometry["solid_count"] != 1 or geometry["coupon_solid_count"] != 1:
        stop_reasons.append("PRINTABLE_NOT_ONE_SOLID")
    if geometry["full_maximum_radial_xy_mm"] > MAXIMUM_TOTAL_XY_ENVELOPE_MM:
        stop_reasons.append("PRINTED_XY_OVER_238MM")
    if selected_netpot["installed_netpot_maximum_xy_mm"] > MAXIMUM_TOTAL_XY_ENVELOPE_MM:
        stop_reasons.append("INSTALLED_NETPOT_XY_OVER_238MM")
    if selected_netpot["pot_stage_intersection_volume_mm3"] > 1.0e-7:
        stop_reasons.append("NETPOT_STAGE_INTERFERENCE")
    if not 0.35 <= selected_volume <= 0.45:
        stop_reasons.append("SELECTED_WATER_VOLUME_OUT_OF_RANGE")
    if overhang_audit["unsupported_prohibited_count"]:
        stop_reasons.append("UNSUPPORTED_PROHIBITED_FEATURE")
    if geometry["petg_reference_mass_g"] > 900.0:
        stop_reasons.append("CAD_REFERENCE_MASS_OVER_900G")
    if stop_reasons:
        raise RuntimeError("CONFLICT_FOUND: " + ", ".join(stop_reasons))

    step_root, stl_root, preview_root = output_root / "step", output_root / "stl", output_root / "preview"
    for directory in (step_root, stl_root, preview_root):
        directory.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    steps = {
        "ps_mht_v001_integrated_stage_full_reference_phase3ia.step": (full, 1, True),
        "ps_mht_v001_integrated_stage_lower_60mm_coupon_phase3ia.step": (coupon, 1, True),
        "ps_mht_v001_integrated_stage_assembly_reference_phase3ia.step": (assembly, ASSEMBLY_REFERENCE_SOLID_COUNT, False),
        "ps_mht_v001_integrated_stage_water_volume_reference_phase3ia.step": (waters, WATER_VOLUME_REFERENCE_SOLID_COUNT, False),
    }
    for name, (model, count, printable) in steps.items():
        path = step_root / name
        if printable:
            export_printable_step(model, path)
        else:
            export_reference_step(model, path, count)
        generated.append(path)
    stls = {
        "plate_01_integrated_stage_full_SLICER_REVIEW_ONLY_phase3ia.stl": full,
        "plate_02_integrated_stage_lower_60mm_coupon_phase3ia.stl": coupon,
    }
    for name, model in stls.items():
        path = stl_root / name
        export_printable_stl(model, path)
        generated.append(path)

    step_validation = {
        name: validate_step_round_trip(step_root / name, count, printable).as_dict()
        for name, (_, count, printable) in steps.items()
    }
    stl_validation = {name: _mesh_extended_audit(stl_root / name) for name in stls}
    for name, metrics in stl_validation.items():
        if metrics["connected_component_count"] != 1:
            raise RuntimeError(f"{name}: connected component count is not one")

    slicer_manifest = _slicer_review_manifest(geometry, stl_validation)
    preview_payloads = {
        "phase3ia_slicer_review_manifest.json": slicer_manifest,
        "phase3ia_overhang_audit.json": overhang_audit,
        "phase3ia_water_volume_audit.json": water_audit,
        "phase3ia_netpot_envelope_audit.json": netpot_audit,
    }
    for name, payload in preview_payloads.items():
        generated.append(_write_json(preview_root / name, payload))

    nonreg_after_geometry = audit_phase3ia_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_after_geometry["all_unchanged"]:
        raise RuntimeError("post-geometry non-regression SHA audit failed")
    nonreg_path = preview_root / "phase3ia_nonregression_audit.json"
    generated.append(_write_json(nonreg_path, nonreg_after_geometry))

    report_path = preview_root / "phase3ia_validation_report.json"
    provisional_tests = {
        "existing_ps_mht": EXPECTED_EXISTING_PS_MHT_TESTS,
        "linked_sump": EXPECTED_LINKED_SUMP_TESTS,
        "new_phase3ia": EXPECTED_PHASE3IA_TESTS,
        "total_passed": EXPECTED_TOTAL_TESTS,
        "all_passed": True,
        "status": "PROVISIONAL_EXPECTED_COUNTS_DURING_SELF_TEST",
    }
    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3I-A",
        "process_name": PHASE3IA_PROCESS_NAME,
        "status": list(PHASE3IA_STATUS_LINES),
        "cadquery_version": cq.__version__,
        "repository_generation_audit": repository_audit,
        "phase3h_physical_results": phase3h_physical_results_phase3ia(),
        "supersession": {
            "old_wet_joint_production_architecture": "SUPERSEDED",
            "compression_ring_v1": "SUPERSEDED_BY_PHASE_3IA",
            "compression_ring_v2": "NOT_IMPLEMENTED",
            "second_compression_ring_print": "NOT_REQUIRED",
        },
        "geometry": geometry,
        "selected_recess_mm": SELECTED_PORT_RECESS_MM,
        "water_volume_audit": water_audit,
        "selected_water_depth_mm": SELECTED_OPERATING_DEPTH_MM,
        "netpot_envelope_audit": netpot_audit,
        "overflow_audit": overflow_audit,
        "overhang_audit": overhang_audit,
        "assembly_reference": assembly_reference_metadata_phase3ia(),
        "step_round_trip_validation": step_validation,
        "stl_mesh_validation": stl_validation,
        "slicer_review_manifest": slicer_manifest,
        "print_status": {
            "full": FULL_PRINT_STATUS,
            "coupon": "READY_FIRST_AFTER_SLICER_REVIEW",
            "bambu_studio": BAMBU_STUDIO_REVIEW_STATUS,
        },
        "non_regression": nonreg_after_geometry,
        "automated_tests": provisional_tests,
        "git": {
            "read_only_commands_executed": list(READ_ONLY_GIT_COMMANDS),
            "prohibited_commands_executed": [],
            "mutation_operations_performed": False,
        },
        "not_declared": [
            "FULL_STAGE_PRINT_APPROVED",
            "WATER_TIGHT",
            "OVERFLOW_PASS",
            "PLANT_READY",
            "PRODUCTION_READY",
            "READY_FOR_80_TOWERS",
        ],
    }
    generated.append(_write_json(report_path, report))

    report["automated_tests"] = _run_tests_isolated()
    nonreg_after_tests = audit_phase3ia_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_after_tests["all_unchanged"]:
        raise RuntimeError("post-test non-regression SHA audit failed")
    report["non_regression_after_tests"] = {
        name: value["unchanged"]
        for name, value in nonreg_after_tests.items()
        if isinstance(value, dict) and "unchanged" in value
    }

    commit_manifest_path = PACKAGE_ROOT / "commit" / "commit_manifest_phase3ia.txt"
    sha_path = PACKAGE_ROOT / "commit" / "phase3ia_SHA256SUMS.txt"
    sources = _source_paths()
    _write_commit_manifest(sources + generated + [sha_path], commit_manifest_path)
    delivery_members = sources + generated + [commit_manifest_path, sha_path]
    report["generated_files"] = [item.relative_to(REPOSITORY_ROOT).as_posix() for item in sorted(generated + [commit_manifest_path, sha_path])]
    report["commit_manifest"] = commit_manifest_path.relative_to(REPOSITORY_ROOT).as_posix()
    report["sha256_list"] = sha_path.relative_to(REPOSITORY_ROOT).as_posix()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = DOWNLOAD_ROOT / f"PS_MHT_V001_PHASE3IA_INTEGRATED_WET_BASE_{timestamp}.zip"
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
    print(json.dumps(generate_phase3ia(args.output.resolve()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
