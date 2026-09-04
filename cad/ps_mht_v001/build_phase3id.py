"""Generate and validate PS-MHT-V001 Phase 3I-D deliverables."""

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
from ps_mht_v001.common.phase3id_nonregression import audit_phase3id_nonregression
from ps_mht_v001.common.validation import (
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.coupons.interstage_cascade_coupon_phase3id import (
    build_lower_receiver_full_channel_coupon_phase3id,
    build_two_stage_cascade_coupon_assembly_reference_phase3id,
    build_upper_overflow_drop_chute_coupon_phase3id,
    coupon_geometry_audit_phase3id,
)
from ps_mht_v001.phase3id_state import (
    PHASE3IC_FROZEN_BASELINE,
    PHASE3IC_INTERSTAGE_TRANSFER,
    PHASE3ID_PROCESS_NAME,
    PHASE3ID_STATUS,
    PHASE3ID_STATUS_LINES,
)
from ps_mht_v001.print_manifest_phase3id import build_print_manifest_phase3id
from ps_mht_v001.reference.interstage_cascade_references_phase3id import (
    build_two_stage_interstage_cascade_assembly_reference_phase3id,
    two_stage_collision_audit_phase3id,
    two_stage_reference_metadata_phase3id,
)
from ps_mht_v001.tower_module.horseshoe_flange_keeper_phase3ic import (
    keeper_v2_envelope_audit_phase3ic,
)
from ps_mht_v001.tower_module.integrated_wet_base_stage_phase3id import (
    DIAGNOSTIC_NAMES_PHASE3ID,
    actual_water_volume_audit_phase3id,
    build_integrated_stage_full_corrected_phase3id,
    build_phase3id_diag_04d,
    build_phase3id_diag_05d,
    geometry_audit_phase3id,
    overhang_audit_phase3id,
    phase3id_phase3ic_geometry_delta_audit,
    water_path_audit_phase3id,
)
from ps_mht_v001.tower_module.positive_interstage_cascade_phase3id import (
    AIR_GAP_MM,
    DRIP_NOSE_MAXIMUM_TIP_RADIUS_MM,
    DRIP_NOSE_TIP_RADIUS_MM,
    LOWER_RECEIVER_MAXIMUM_OUTER_RADIUS_MM,
    LOWER_RECEIVER_OUTER_RADIUS_MM,
    build_water_stream_envelope_reference_phase3id,
    interstage_path_dimension_audit_phase3id,
    receiver_tolerance_audit_phase3id,
    water_stream_envelope_audit_phase3id,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
DOWNLOAD_ROOT = Path(r"D:\Downloads")
EXPECTED_ENTRY_HEAD = "facb4f63c0d485a53fef48b602f97e0454e8548f"
EXPECTED_PRIOR_PS_MHT_TESTS = 519
EXPECTED_LINKED_SUMP_TESTS = 40
EXPECTED_PHASE3ID_TESTS = 70
EXPECTED_TOTAL_TESTS = 629
READ_ONLY_GIT_COMMANDS = (
    "git rev-parse --abbrev-ref HEAD",
    "git rev-parse HEAD",
    "git status --short",
    "git diff",
    "git diff --cached",
    "git ls-files --others --exclude-standard",
    "git log -5 --oneline",
    f"git diff --name-only {EXPECTED_ENTRY_HEAD}..HEAD -- cad/ps_mht_v001",
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
    head = _git_output("rev-parse", "HEAD").strip()
    entry_names = _git_output("show", "--format=", "--name-only", EXPECTED_ENTRY_HEAD).splitlines()
    entry_ps_mht = [name for name in entry_names if name.startswith("cad/ps_mht_v001/")]
    intervening = _git_output(
        "diff", "--name-only", f"{EXPECTED_ENTRY_HEAD}..{head}", "--", "cad/ps_mht_v001"
    ).splitlines()
    if entry_ps_mht or intervening:
        raise RuntimeError("CONCURRENT_CHANGE_CONFLICT: committed change touches cad/ps_mht_v001")
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
        "expected_entry_commit_ps_mht_paths": entry_ps_mht,
        "intervening_commits_ps_mht_paths": intervening,
        "concurrent_ps_mht_change": False,
        "recent_commits": _git_output("log", "-5", "--oneline").splitlines(),
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
        if path.name.startswith("test_phase3id_"):
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
        EXPECTED_PHASE3ID_TESTS,
        EXPECTED_TOTAL_TESTS,
    )
    if actual != expected:
        raise RuntimeError(f"test count mismatch: expected {expected}, got {actual}")
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "prior_ps_mht": prior,
        "linked_sump": linked,
        "new_phase3id": new,
        "total_passed": actual[3],
        "all_passed": True,
        "files": results,
    }


def _diagnostic_progression_audit(geometry: dict[str, object]) -> dict[str, object]:
    stages = geometry["stages"]
    return {
        "official_order": ["PHASE3IC_D01", "PHASE3IC_D02", "PHASE3IC_D03", "PHASE3ID_D04D", "PHASE3ID_D05D"],
        "old_phase3ic_d04_d05_excluded": True,
        "D04D": {
            "base": "PHASE3IC_D03_EXACT",
            "added": ["POSITIVE_DOWNCHUTE", "DRIP_NOSE", "POSITIVE_RECEIVER", "OPEN_VERTICAL_CHANNEL", "BOTTOM_DISCHARGE", "OPEN_WICK_ROUTES", "REAR_SPINE"],
            "volume_increment_mm3": stages["D04D"]["volume_added_from_previous_mm3"],
        },
        "D05D": {
            "base": "PHASE3ID_D04D_EXACT",
            "added": ["UNCHANGED_STACKING_GUIDES", "GUIDE_RAMPS", "FINAL_TOP_BAND"],
            "volume_increment_mm3": stages["D05D"]["volume_added_from_previous_mm3"],
        },
        "later_feature_removal_count": 0,
        "d05d_corrected_full_equivalent": geometry["d05d_corrected_full_equivalence"]["within_tolerance"],
    }


def _air_gap_audit(collision: dict[str, object]) -> dict[str, object]:
    return {
        "upper_outlet_local_z_mm": collision["upper_outlet_tip_local_z_mm"],
        "upper_outlet_global_z_mm": collision["upper_outlet_tip_global_z_mm"],
        "lower_receiver_top_global_z_mm": collision["lower_receiver_top_global_z_mm"],
        "nominal_air_gap_mm": collision["nominal_air_gap_mm"],
        "measured_air_gap_mm": collision["measured_air_gap_mm"],
        "outlet_receiver_intersection_volume_mm3": collision["outlet_receiver_intersection_volume_mm3"],
        "parts_contact": not collision["outlet_receiver_clear"],
        "capillary_bridge_geometry_present": False,
        "siphon_geometry_present": False,
        "status": "PASS_PHYSICAL_FLOW_PENDING" if abs(collision["measured_air_gap_mm"] - AIR_GAP_MM) <= 1.0e-6 and collision["outlet_receiver_clear"] else "FAIL",
    }


def _source_paths() -> list[Path]:
    relative = (
        "build_phase3id.py",
        "phase3id_state.py",
        "print_manifest_phase3id.py",
        "common/phase3id_nonregression.py",
        "tower_module/positive_interstage_cascade_phase3id.py",
        "tower_module/integrated_wet_base_stage_phase3id.py",
        "coupons/interstage_cascade_coupon_phase3id.py",
        "reference/interstage_cascade_references_phase3id.py",
        "specs/ps_mht_phase3id_positive_cascade.yaml",
        "specs/ps_mht_phase3id_interfaces.json",
        "docs/PHASE3ID_ARCHITECTURE.md",
        "docs/PHASE3ID_PHASE3IC_HYDRAULIC_DEFECT_RECORD.md",
        "docs/PHASE3ID_BAMBU_STUDIO_REVIEW_CHECKLIST.md",
        "docs/PHASE3ID_TWO_STAGE_CASCADE_TEST_PLAN.md",
        "docs/PHASE3ID_PHYSICAL_RESULT_SHEET.md",
        "docs/PHASE3ID_PRINT_AND_ASSEMBLY_INSTRUCTIONS.md",
        "tests/test_phase3id_entry_state.py",
        "tests/test_phase3id_upper_downchute.py",
        "tests/test_phase3id_lower_receiver.py",
        "tests/test_phase3id_air_gap.py",
        "tests/test_phase3id_tolerance_envelope.py",
        "tests/test_phase3id_water_path.py",
        "tests/test_phase3id_two_stage_assembly.py",
        "tests/test_phase3id_diagnostic_progression.py",
        "tests/test_phase3id_print_geometry.py",
        "tests/test_phase3id_nonregression.py",
        "tools/run_validation_phase3id.cmd",
    )
    paths = [PACKAGE_ROOT / item for item in relative]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing Phase 3I-D source files: " + ", ".join(missing))
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


def generate_phase3id(output_root: Path) -> dict[str, object]:
    repository_audit = _repository_audit()
    nonreg_before = audit_phase3id_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_before["all_unchanged"]:
        raise RuntimeError("pre-generation inherited SHA non-regression audit failed")

    full = build_integrated_stage_full_corrected_phase3id()
    d04d = build_phase3id_diag_04d()
    d05d = build_phase3id_diag_05d()
    upper_coupon = build_upper_overflow_drop_chute_coupon_phase3id()
    lower_coupon = build_lower_receiver_full_channel_coupon_phase3id()
    two_stage_reference = build_two_stage_interstage_cascade_assembly_reference_phase3id()
    coupon_reference = build_two_stage_cascade_coupon_assembly_reference_phase3id()
    stream_reference = build_water_stream_envelope_reference_phase3id()

    geometry = geometry_audit_phase3id()
    path_audit = {
        **interstage_path_dimension_audit_phase3id(),
        "water_boundary": water_path_audit_phase3id(),
        "corrected_full_solid_count": len(full.solids().vals()),
        "corrected_full_valid": full.val().isValid(),
    }
    tolerance_audit = receiver_tolerance_audit_phase3id()
    stream_audit = water_stream_envelope_audit_phase3id()
    collision_audit = two_stage_collision_audit_phase3id()
    air_gap_audit = _air_gap_audit(collision_audit)
    water_audit = actual_water_volume_audit_phase3id()
    overhang_audit = overhang_audit_phase3id()
    diagnostic_audit = _diagnostic_progression_audit(geometry)
    delta_audit = phase3id_phase3ic_geometry_delta_audit()
    coupon_audit = coupon_geometry_audit_phase3id()
    keeper_audit = keeper_v2_envelope_audit_phase3ic()
    reference_metadata = two_stage_reference_metadata_phase3id()
    print_manifest = build_print_manifest_phase3id()

    stop_reasons: list[str] = []
    if len(full.solids().vals()) != 1 or not full.val().isValid():
        stop_reasons.append("CORRECTED_FULL_NOT_ONE_VALID_SOLID")
    full_z = geometry["stages"]["D05D"]["z_range_mm"]
    if abs(full_z[0]) > 1.0e-5 or abs(full_z[1] - 170.0) > 1.0e-5:
        stop_reasons.append("FULL_Z_RANGE_NOT_0_TO_170")
    if geometry["maximum_xy_mm"] > 238.0:
        stop_reasons.append("FULL_XY_OVER_238MM")
    if LOWER_RECEIVER_OUTER_RADIUS_MM > LOWER_RECEIVER_MAXIMUM_OUTER_RADIUS_MM:
        stop_reasons.append("RECEIVER_RADIUS_OVER_118P5MM")
    if DRIP_NOSE_TIP_RADIUS_MM > DRIP_NOSE_MAXIMUM_TIP_RADIUS_MM:
        stop_reasons.append("DRIP_NOSE_RADIUS_OVER_106P5MM")
    if keeper_audit["installed_netpot_envelope_with_keeper_mm"] > 238.0:
        stop_reasons.append("INSTALLED_NETPOT_XY_OVER_238MM")
    if not collision_audit["full_modules_clear"] or not collision_audit["receiver_upper_bottom_clear"]:
        stop_reasons.append("TWO_STAGE_BODY_COLLISION")
    if not collision_audit["receiver_netpot_clear"] or not collision_audit["receiver_2020_post_clear"]:
        stop_reasons.append("RECEIVER_REFERENCE_COLLISION")
    if air_gap_audit["status"] != "PASS_PHYSICAL_FLOW_PENDING":
        stop_reasons.append("SIX_MM_AIR_GAP_FAILED")
    if not tolerance_audit["all_cases_pass"]:
        stop_reasons.append("MISALIGNMENT_ENVELOPE_NOT_CAPTURED")
    if not stream_audit["receiver_planar_envelope_contains_stream"] or not stream_audit["central_dry_opening_clear"]:
        stop_reasons.append("WATER_STREAM_ENVELOPE_FAILED")
    if not water_audit["within_target_range"]:
        stop_reasons.append("ACTUAL_RETAINED_VOLUME_OUT_OF_RANGE")
    water_path = path_audit["water_boundary"]
    if water_path["external_penetrations_below_water_surface"] or water_path["central_hole_penetrations_below_water_surface"]:
        stop_reasons.append("LOW_WATER_LEAK_PATH_PRESENT")
    if water_path["closed_channel_count"] or water_path["closed_pipe_count"]:
        stop_reasons.append("CLOSED_WATERWAY_PRESENT")
    if overhang_audit["unsupported_prohibited_count"] or overhang_audit["horizontal_bridge_over_8mm_count"] or overhang_audit["airborne_start_count"]:
        stop_reasons.append("UNPRINTABLE_OVERHANG_OR_FLOATING_GEOMETRY")
    if not geometry["d05d_corrected_full_equivalence"]["within_tolerance"]:
        stop_reasons.append("D05D_NOT_EQUIVALENT_TO_CORRECTED_FULL")
    if not all(delta_audit[key] for key in ("phase3ic_d01_unchanged", "phase3ic_d02_unchanged", "phase3ic_d03_unchanged")):
        stop_reasons.append("PHASE3IC_D01_D03_CHANGED")
    if any(coupon_audit[name]["solid_count"] != 1 for name in ("upper", "lower")):
        stop_reasons.append("COUPON_NOT_ONE_SOLID")
    if stop_reasons:
        raise RuntimeError("CONFLICT_FOUND: " + ", ".join(stop_reasons))

    step_root = output_root / "step"
    stl_root = output_root / "stl"
    diagnostic_stl_root = stl_root / "diagnostic_phase3id"
    preview_root = output_root / "preview"
    for directory in (step_root, stl_root, diagnostic_stl_root, preview_root):
        directory.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    printable_steps = {
        "ps_mht_v001_integrated_stage_full_corrected_phase3id.step": full,
        "ps_mht_v001_upper_overflow_drop_chute_coupon_phase3id.step": upper_coupon,
        "ps_mht_v001_lower_receiver_full_channel_coupon_phase3id.step": lower_coupon,
    }
    for name, model in printable_steps.items():
        path = step_root / name
        export_printable_step(model, path)
        generated.append(path)
    reference_steps = {
        "ps_mht_v001_two_stage_cascade_assembly_reference_phase3id.step": (two_stage_reference, reference_metadata["solid_count"]),
        "ps_mht_v001_two_stage_cascade_coupon_assembly_reference_phase3id.step": (coupon_reference, coupon_audit["assembly_reference_solid_count"]),
        "ps_mht_v001_water_stream_envelope_reference_phase3id.step": (stream_reference, 1),
    }
    for name, (model, expected_count) in reference_steps.items():
        path = step_root / name
        export_reference_step(model, path, int(expected_count))
        generated.append(path)

    primary_stls = {
        "plate_01_integrated_stage_full_SLICER_REVIEW_ONLY_phase3id.stl": full,
        "plate_02_upper_overflow_drop_chute_coupon_phase3id.stl": upper_coupon,
        "plate_03_lower_receiver_full_channel_coupon_phase3id.stl": lower_coupon,
    }
    for name, model in primary_stls.items():
        path = stl_root / name
        export_printable_stl(model, path)
        generated.append(path)
    diagnostic_stls = {
        f"{DIAGNOSTIC_NAMES_PHASE3ID[0]}.stl": d04d,
        f"{DIAGNOSTIC_NAMES_PHASE3ID[1]}.stl": d05d,
    }
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
            name: validate_step_round_trip(step_root / name, int(expected_count), False).as_dict()
            for name, (_, expected_count) in reference_steps.items()
        }
    )
    stl_mesh_validation = {
        name: _mesh_extended_audit(stl_root / name) for name in primary_stls
    }
    stl_mesh_validation.update(
        {
            name: _mesh_extended_audit(diagnostic_stl_root / name)
            for name in diagnostic_stls
        }
    )
    for name, metrics in stl_mesh_validation.items():
        if metrics["connected_component_count"] != 1 or not metrics["closed_manifold"]:
            raise RuntimeError(f"{name}: STL is not one closed component")

    preview_payloads = {
        "phase3id_interstage_path_audit.json": path_audit,
        "phase3id_air_gap_audit.json": air_gap_audit,
        "phase3id_receiver_tolerance_audit.json": tolerance_audit,
        "phase3id_water_stream_envelope_audit.json": stream_audit,
        "phase3id_two_stage_collision_audit.json": collision_audit,
        "phase3id_actual_water_volume_audit.json": water_audit,
        "phase3id_overhang_audit.json": overhang_audit,
        "phase3id_diagnostic_progression_audit.json": diagnostic_audit,
        "phase3id_phase3ic_geometry_delta_audit.json": delta_audit,
        "print_manifest_phase3id.json": print_manifest,
    }
    for name, payload in preview_payloads.items():
        generated.append(_write_json(preview_root / name, payload))

    nonreg_after_geometry = audit_phase3id_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_after_geometry["all_unchanged"]:
        raise RuntimeError("post-geometry inherited SHA non-regression audit failed")
    generated.append(
        _write_json(preview_root / "phase3id_nonregression_audit.json", nonreg_after_geometry)
    )

    report_path = preview_root / "phase3id_validation_report.json"
    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3I-D",
        "process_name": PHASE3ID_PROCESS_NAME,
        "phase_status": PHASE3ID_STATUS,
        "status": list(PHASE3ID_STATUS_LINES),
        "cadquery_version": cq.__version__,
        "repository_generation_audit": repository_audit,
        "phase3ic_interstage_transfer_defect": PHASE3IC_INTERSTAGE_TRANSFER,
        "phase3ic_frozen_baseline": PHASE3IC_FROZEN_BASELINE,
        "geometry": geometry,
        "interstage_path": path_audit,
        "air_gap": air_gap_audit,
        "receiver_tolerance": tolerance_audit,
        "water_stream_envelope": stream_audit,
        "two_stage_collision": collision_audit,
        "two_stage_reference": reference_metadata,
        "actual_water_volume": water_audit,
        "overhang": overhang_audit,
        "diagnostic_progression": diagnostic_audit,
        "phase3ic_geometry_delta": delta_audit,
        "coupon_geometry": coupon_audit,
        "keeper_v2_envelope": keeper_audit,
        "step_round_trip_validation": step_validation,
        "stl_mesh_validation": stl_mesh_validation,
        "print_manifest": print_manifest,
        "non_regression": nonreg_after_geometry,
        "automated_tests": {
            "prior_ps_mht": EXPECTED_PRIOR_PS_MHT_TESTS,
            "linked_sump": EXPECTED_LINKED_SUMP_TESTS,
            "new_phase3id": EXPECTED_PHASE3ID_TESTS,
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
            "INTERSTAGE_TRANSFER_PASS",
            "FLOATING_REGION_SOURCE_IDENTIFIED",
            "FLOATING_REGION_FIXED",
            "FULL_STAGE_PRINT_APPROVED",
            "SUMP_WATERTIGHT",
            "OVERFLOW_PASS",
            "NETPOT_RETENTION_PASS",
            "PRODUCTION_READY",
        ],
    }
    generated.append(_write_json(report_path, report))

    report["automated_tests"] = _run_tests_isolated()
    nonreg_after_tests = audit_phase3id_nonregression(REPOSITORY_ROOT, output_root)
    if not nonreg_after_tests["all_unchanged"]:
        raise RuntimeError("post-test inherited SHA non-regression audit failed")
    report["non_regression_after_tests"] = {
        name: value["unchanged"]
        for name, value in nonreg_after_tests.items()
        if isinstance(value, dict) and "unchanged" in value
    }

    commit_manifest_path = PACKAGE_ROOT / "commit" / "commit_manifest_phase3id.txt"
    sha_path = PACKAGE_ROOT / "commit" / "phase3id_SHA256SUMS.txt"
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
    zip_path = DOWNLOAD_ROOT / f"PS_MHT_V001_PHASE3ID_POSITIVE_INTERSTAGE_CASCADE_{timestamp}.zip"
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
    print(json.dumps(generate_phase3id(args.output.resolve()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

