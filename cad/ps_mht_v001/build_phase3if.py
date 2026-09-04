"""Generate and validate PS-MHT-V001 Phase 3I-F deliverables."""

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
from ps_mht_v001.common.phase3if_nonregression import audit_phase3if_nonregression
from ps_mht_v001.common.validation import (
    export_printable_set_step,
    export_printable_set_stl,
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.coupons.clocking_fit_coupon_phase3ie import clocking_fit_coupon_audit_phase3ie
from ps_mht_v001.fixtures.dry_core_frame_phase3if import (
    REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM,
    REFERENCE_MAST_CLEARANCE_MM,
    build_bottom_centering_puck_fit_coupons_phase3if,
    build_bottom_centering_puck_phase3if,
    build_dry_core_frame_architecture_reference_phase3if,
    build_removable_top_centering_cap_phase3if,
    dry_core_component_audit_phase3if,
)
from ps_mht_v001.fixtures.stack_clocking_gauge_30deg_phase3ie import clocking_gauge_30deg_audit_phase3ie
from ps_mht_v001.phase3if_state import PHASE3IF_PROCESS_NAME, PHASE3IF_STATUS, PHASE3IF_STATUS_LINES
from ps_mht_v001.print_manifest_phase3if import build_print_manifest_phase3if
from ps_mht_v001.reference.direct_drop_references_phase3ie import (
    correct_wrong_assembly_audit_phase3ie,
    drop_corridor_collision_audit_phase3ie,
)
from ps_mht_v001.reference.dry_core_frame_references_phase3if import (
    build_five_stage_30deg_direct_drop_with_dry_core_frame_reference_phase3if,
    five_stage_dry_core_collision_audit_phase3if,
    five_stage_reference_metadata_phase3if,
)
from ps_mht_v001.tower_module.direct_drop_standpipe_cascade_phase3ie import (
    blockage_dimension_audit_phase3ie,
    landing_zone_audit_phase3ie,
    rotation_rule_audit_phase3ie,
    standpipe_geometry_audit_phase3ie,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3ie import (
    actual_water_volume_audit_phase3ie,
    leak_path_audit_phase3ie,
    overhang_audit_phase3ie,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3if import (
    build_integrated_stage_full_direct_drop_phase3if,
    geometry_audit_phase3if,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
DOWNLOAD_ROOT = Path(r"D:\Downloads")
EXPECTED_ENTRY_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
EXPECTED_PRIOR_PS_MHT_TESTS = 589
EXPECTED_PHASE3IF_TESTS = 58
EXPECTED_LINKED_SUMP_TESTS = 40
EXPECTED_TOTAL_TESTS = 687


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
    intervening = _git_output("diff", "--name-only", f"{EXPECTED_ENTRY_HEAD}..{head}", "--", "cad/ps_mht_v001").splitlines()
    if intervening:
        raise RuntimeError("CONCURRENT_CHANGE_CONFLICT: committed change touches cad/ps_mht_v001")
    diff = _git_output("diff")
    cached = _git_output("diff", "--cached")
    large_files = []
    for path in REPOSITORY_ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        try:
            if path.is_file() and path.stat().st_size >= 95 * 1024 * 1024:
                large_files.append({"path": path.relative_to(REPOSITORY_ROOT).as_posix(), "bytes": path.stat().st_size})
        except (OSError, PermissionError):
            continue
    return {
        "branch": _git_output("rev-parse", "--abbrev-ref", "HEAD").strip(),
        "head": head,
        "expected_entry_head": EXPECTED_ENTRY_HEAD,
        "intervening_commits_ps_mht_paths": intervening,
        "status_short": _git_output("status", "--short").splitlines(),
        "working_tree_diff_bytes": len(diff.encode()),
        "working_tree_diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
        "staged_diff_bytes": len(cached.encode()),
        "staged_diff_sha256": hashlib.sha256(cached.encode()).hexdigest(),
        "staged_diff_empty": cached == "",
        "files_at_least_95mb": large_files,
        "git_mutation_operations_performed": False,
    }


def _mesh_extended_audit(path: Path) -> dict[str, object]:
    import vtk

    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.Update()
    tri = vtk.vtkTriangleFilter()
    tri.SetInputData(reader.GetOutput())
    tri.Update()
    mesh = tri.GetOutput()
    degenerate = 0
    minimum_double_area = math.inf
    for index in range(mesh.GetNumberOfCells()):
        cell = mesh.GetCell(index)
        p0, p1, p2 = (mesh.GetPoint(cell.GetPointId(i)) for i in range(3))
        ux, uy, uz = (p1[i] - p0[i] for i in range(3))
        vx, vy, vz = (p2[i] - p0[i] for i in range(3))
        cx, cy, cz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        double_area = math.sqrt(cx * cx + cy * cy + cz * cz)
        minimum_double_area = min(minimum_double_area, double_area)
        degenerate += int(double_area <= 1.0e-12)
    metrics = validate_stl_mesh(path).as_dict()
    metrics.update({"degenerate_triangle_count": degenerate, "minimum_triangle_double_area_mm2": minimum_double_area})
    if degenerate:
        raise RuntimeError(f"{path.name}: degenerate triangles")
    return metrics


def _run_pytest_file(path: Path, cwd: Path, python_paths: list[Path]) -> dict[str, object]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join([str(p) for p in python_paths] + ([environment["PYTHONPATH"]] if environment.get("PYTHONPATH") else []))
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
    results = []
    prior = new = linked = 0
    for path in sorted((PACKAGE_ROOT / "tests").glob("test_*.py")):
        item = _run_pytest_file(path, PACKAGE_ROOT, [PACKAGE_ROOT.parent])
        results.append(item)
        if path.name.startswith("test_phase3if_"):
            new += int(item["passed"])
        else:
            prior += int(item["passed"])
    linked_root = PACKAGE_ROOT / "indoor_test_rig/ps_mht_8t_linked_sump_v001"
    for path in sorted((linked_root / "tests").glob("test_*.py")):
        item = _run_pytest_file(path, PACKAGE_ROOT.parent, [PACKAGE_ROOT.parent])
        item["suite"] = "linked_sump"
        results.append(item)
        linked += int(item["passed"])
    actual = (prior, new, linked, prior + new + linked)
    expected = (EXPECTED_PRIOR_PS_MHT_TESTS, EXPECTED_PHASE3IF_TESTS, EXPECTED_LINKED_SUMP_TESTS, EXPECTED_TOTAL_TESTS)
    if actual != expected:
        raise RuntimeError(f"test count mismatch: expected {expected}, got {actual}")
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "prior_ps_mht": prior,
        "new_phase3if": new,
        "linked_sump": linked,
        "total_passed": actual[3],
        "all_passed": True,
        "files": results,
    }


def _source_paths() -> list[Path]:
    relative = [
        "build_phase3if.py", "phase3if_state.py", "print_manifest_phase3if.py",
        "common/phase3if_nonregression.py", "fixtures/dry_core_frame_phase3if.py",
        "fixtures/stack_clocking_gauge_30deg_phase3ie.py",
        "tower_module/direct_drop_standpipe_cascade_phase3ie.py",
        "tower_module/integrated_wet_base_stage_phase3ie.py",
        "tower_module/stack_clocking_datums_phase3ie.py",
        "tower_module/integrated_wet_base_stage_phase3if.py",
        "reference/direct_drop_references_phase3ie.py",
        "reference/dry_core_frame_references_phase3if.py",
        "coupons/clocking_fit_coupon_phase3ie.py",
        "coupons/standpipe_sump_coupon_phase3ie.py",
        "coupons/direct_drop_landing_coupon_phase3ie.py",
        "specs/ps_mht_phase3if_dry_core_frame.yaml", "specs/ps_mht_phase3if_interfaces.json",
        "docs/PHASE3IF_ARCHITECTURE.md", "docs/PHASE3IF_FRAME_CONFLICT_SUPERSESSION.md",
        "docs/PHASE3IF_PUCK_FIT_AND_MAST_MEASUREMENT.md", "docs/PHASE3IF_PRINT_AND_ASSEMBLY_INSTRUCTIONS.md",
        "docs/PHASE3IF_BAMBU_STUDIO_REVIEW_CHECKLIST.md", "docs/PHASE3IF_PHYSICAL_RESULT_SHEET.md",
        "tools/run_validation_phase3if.cmd",
    ]
    relative += [f"tests/{p.name}" for p in sorted((PACKAGE_ROOT / "tests").glob("test_phase3if_*.py"))]
    return [PACKAGE_ROOT / p for p in relative]


def _write_manifest(paths: list[Path], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [p.relative_to(REPOSITORY_ROOT).as_posix() for p in sorted(set(paths))]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def _write_sha256s(paths: list[Path], output: Path) -> Path:
    lines = [f"{file_sha256(p)}  {p.relative_to(REPOSITORY_ROOT).as_posix()}" for p in sorted(set(paths))]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def _make_zip(paths: list[Path], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(set(paths)):
            archive.write(path, path.relative_to(REPOSITORY_ROOT).as_posix())
    return output


def generate_phase3if(output_root: Path, run_tests: bool = True) -> dict[str, object]:
    repository = _repository_audit()
    nonreg = audit_phase3if_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg["all_unchanged"]:
        raise RuntimeError("inherited SHA non-regression failed")

    frame = dry_core_component_audit_phase3if()
    collision = five_stage_dry_core_collision_audit_phase3if()
    geometry = geometry_audit_phase3if()
    water = actual_water_volume_audit_phase3ie()
    if not collision["all_unintended_intersections_zero"]:
        raise RuntimeError("dry-core frame collision found")
    if collision["minimum_tolerance_radial_margin_to_frame_mm"] <= 0:
        raise RuntimeError("dry-core frame tolerance margin failed")
    if not water["within_target_range"]:
        raise RuntimeError("retained water below Phase 3I-F target")
    if geometry["maximum_xy_diameter_mm"] > 238.0 or geometry["solid_count"] != 1:
        raise RuntimeError("full module envelope or solid count failed")

    step_root, stl_root, preview_root = output_root / "step", output_root / "stl", output_root / "preview"
    for directory in (step_root, stl_root, preview_root):
        directory.mkdir(parents=True, exist_ok=True)

    architecture = build_dry_core_frame_architecture_reference_phase3if()
    fit = build_bottom_centering_puck_fit_coupons_phase3if()
    puck = build_bottom_centering_puck_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM)
    cap = build_removable_top_centering_cap_phase3if(REFERENCE_EXPORT_PUCK_OUTER_DIAMETER_MM, REFERENCE_MAST_CLEARANCE_MM)
    five = build_five_stage_30deg_direct_drop_with_dry_core_frame_reference_phase3if()
    full = build_integrated_stage_full_direct_drop_phase3if()

    generated: list[Path] = []
    reference_steps = {
        "ps_mht_v001_dry_core_frame_architecture_reference_phase3if.step": architecture,
        "ps_mht_v001_five_stage_30deg_dry_core_frame_reference_phase3if.step": five,
    }
    for name, model in reference_steps.items():
        path = step_root / name
        export_reference_step(model, path, len(model.solids().vals()))
        generated.append(path)
    set_step = step_root / "ps_mht_v001_bottom_centering_puck_fit_coupons_phase3if.step"
    export_printable_set_step(fit, set_step, 3)
    generated.append(set_step)
    printable_steps = {
        "ps_mht_v001_bottom_centering_puck_phase3if.step": puck,
        "ps_mht_v001_removable_top_centering_cap_phase3if.step": cap,
        "ps_mht_v001_integrated_stage_full_direct_drop_phase3if.step": full,
    }
    for name, model in printable_steps.items():
        path = step_root / name
        export_printable_step(model, path)
        generated.append(path)

    stls = {
        "plate_01_dry_core_puck_fit_coupons_phase3if.stl": (fit, 3),
        "plate_02_bottom_centering_puck_HOLD_phase3if.stl": (puck, 1),
        "plate_03_top_centering_cap_HOLD_phase3if.stl": (cap, 1),
        "plate_04_integrated_stage_full_SLICER_REVIEW_ONLY_phase3if.stl": (full, 1),
    }
    for name, (model, count) in stls.items():
        path = stl_root / name
        if count == 1:
            export_printable_stl(model, path)
        else:
            export_printable_set_stl(model, path, count)
        generated.append(path)

    step_validation = {}
    for name, model in reference_steps.items():
        step_validation[name] = validate_step_round_trip(step_root / name, len(model.solids().vals()), False).as_dict()
    step_validation[set_step.name] = validate_step_round_trip(set_step, 3, False).as_dict()
    for name in printable_steps:
        step_validation[name] = validate_step_round_trip(step_root / name, 1, True).as_dict()
    stl_validation = {name: _mesh_extended_audit(stl_root / name) for name in stls}
    for name, metrics in stl_validation.items():
        expected = stls[name][1]
        if metrics["connected_component_count"] != expected or not metrics["closed_manifold"]:
            raise RuntimeError(f"{name}: mesh validation failed")

    manifest = build_print_manifest_phase3if()
    audits = {
        "phase3if_dry_core_component_audit.json": frame,
        "phase3if_five_stage_collision_audit.json": collision,
        "phase3if_five_stage_reference_audit.json": five_stage_reference_metadata_phase3if(),
        "phase3if_thirty_degree_direct_drop_audit.json": {
            "rotation": rotation_rule_audit_phase3ie(),
            "standpipes": standpipe_geometry_audit_phase3ie(),
            "landings": landing_zone_audit_phase3ie(),
            "drop_corridors": drop_corridor_collision_audit_phase3ie(),
            "correct_wrong": correct_wrong_assembly_audit_phase3ie(),
            "blockage": blockage_dimension_audit_phase3ie(),
        },
        "phase3if_actual_water_volume_audit.json": water,
        "phase3if_leak_path_audit.json": leak_path_audit_phase3ie(),
        "phase3if_overhang_audit.json": overhang_audit_phase3ie(),
        "phase3if_clocking_gauge_reference_audit.json": {
            "gauge": clocking_gauge_30deg_audit_phase3ie(),
            "fit_coupon": clocking_fit_coupon_audit_phase3ie(),
        },
        "phase3if_frame_conflict_resolution_audit.json": {
            "previous_status": "FRAME_CLOCKING_CONFLICT",
            "legacy_fixing": "SUPERSEDED_BY_NON_ROTATING_DRY_CORE_FRAME",
            "per_stage_rear_brackets": False,
            "central_mast_non_rotating": True,
            "lower_and_upper_metal_links": True,
            "resolved_in_cad": collision["all_unintended_intersections_zero"],
            "physical_validation": "PENDING",
        },
        "print_manifest_phase3if.json": manifest,
    }
    for name, payload in audits.items():
        generated.append(_write_json(preview_root / name, payload))
    generated.append(_write_json(preview_root / "phase3if_nonregression_audit.json", nonreg))

    tests = _run_tests_isolated() if run_tests else {
        "status": "SKIPPED_BY_EXPLICIT_BUILD_FLAG",
        "expected_total": EXPECTED_TOTAL_TESTS,
        "all_passed": False,
    }
    report = {
        "project": "PS-MHT-V001", "phase": "3I-F", "process_name": PHASE3IF_PROCESS_NAME,
        "phase_status": PHASE3IF_STATUS, "status": list(PHASE3IF_STATUS_LINES),
        "cadquery_version": cq.__version__, "repository_audit": repository,
        "geometry": geometry, "dry_core_components": frame, "five_stage_collision": collision,
        "five_stage_reference": five_stage_reference_metadata_phase3if(), "actual_water_volume": water,
        "step_round_trip_validation": step_validation, "stl_mesh_validation": stl_validation,
        "print_manifest": manifest, "non_regression": nonreg, "automated_tests": tests,
        "physical_measurements_pending": ["MAST_WIDTH_X_Y", "MAST_CORNER_RADII", "MAST_TWIST", "MAST_STRAIGHTNESS", "MAST_LENGTH", "PRINTED_CENTRAL_OPENING", "SELECTED_PUCK_OD", "SELECTED_MAST_CLEARANCE"],
        "not_declared": ["FRAME_PHYSICAL_PASS", "MAST_STRENGTH_PASS", "CLOCKING_GUIDE_PHYSICAL_PASS", "DIRECT_DROP_CAPTURE_PASS", "FULL_STAGE_PRINT_APPROVED", "PRODUCTION_READY"],
        "git_mutation_operations_performed": False,
    }
    sources = _source_paths()
    missing = [str(p) for p in sources if not p.is_file()]
    if missing:
        raise RuntimeError(f"missing delivery sources: {missing}")
    commit_manifest = PACKAGE_ROOT / "commit/commit_manifest_phase3if.txt"
    sha_path = PACKAGE_ROOT / "commit/phase3if_SHA256SUMS.txt"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = DOWNLOAD_ROOT / f"PS_MHT_V001_PHASE3IF_DRY_CORE_FRAME_{timestamp}.zip"
    report_path = preview_root / "phase3if_validation_report.json"
    generated.append(report_path)
    report["generated_files"] = [p.relative_to(REPOSITORY_ROOT).as_posix() for p in sorted(generated + [commit_manifest, sha_path])]
    report["delivery_zip"] = str(zip_path)
    report["delivery_zip_sha256"] = "CALCULATED_AFTER_ARCHIVE_FINALIZATION_SEE_BUILD_STDOUT_AND_FINAL_REPORT"
    _write_json(report_path, report)
    _write_manifest(sources + generated + [sha_path], commit_manifest)
    delivery = sources + generated + [commit_manifest]
    _write_sha256s(delivery, sha_path)
    delivery.append(sha_path)
    _make_zip(delivery, zip_path)
    result = dict(report)
    result["delivery_zip_sha256"] = file_sha256(zip_path)
    result["delivery_zip_size_bytes"] = zip_path.stat().st_size
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    print(json.dumps(generate_phase3if(args.output.resolve(), not args.skip_tests), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
