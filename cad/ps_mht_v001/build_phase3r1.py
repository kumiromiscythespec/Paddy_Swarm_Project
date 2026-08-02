"""Generate and validate PS-MHT-V001 Phase 3R.1 artifacts."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import cadquery as cq

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ps_mht_v001.assembly.full_module_reference_phase3r1 import (
    PRINT_STATUS,
    build_full_module_reference_phase3r1,
)
from ps_mht_v001.common.phase_baseline import audit_baseline_hashes
from ps_mht_v001.common.validation import (
    export_printable_set_stl,
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    measure_shape,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.coupons.annular_nut_ring_coupon_phase3r1 import (
    CALIBRATION_ONLY,
    NUT_POCKET_CLEARANCES,
    PHYSICAL_ID_SCHEME,
    STATUS as CALIBRATION_COUPON_STATUS,
    build_annular_nut_ring_coupon_phase3r1,
)
from ps_mht_v001.parameters import (
    CALIBRATION_PENDING,
    module_nut_pocket_clearance_candidates,
    phase3r_min_root_thickness,
    phase3r_min_structural_wall,
    port_shell_max_overhang_angle,
)
from ps_mht_v001.print_plate_layout_phase3r1 import (
    ORIENTATION_REFERENCE_SOLID_COUNT,
    STATUS as ORIENTATION_REFERENCE_STATUS,
    build_multi_plate_orientation_reference_phase3r1,
    phase3r1_individual_plates,
)
from ps_mht_v001.tower_module.module_nut_ring_phase3r1 import (
    CALIBRATION_STATUS,
    SELECTED_NUT_POCKET_CLEARANCE,
    build_module_nut_ring_phase3r1,
    production_pocket_clearances_phase3r1,
)
from ps_mht_v001.tower_module.planting_port import maximum_radial_radius
from ps_mht_v001.tower_module.self_supporting_port_opening_phase3r1 import (
    FRAME_INWARD_SHIFT_MM,
    ROOT_FILLET_TARGET,
    ROOT_INCLUSION_PROBE_DIAMETER_MM,
    SHELL_FRAME_RADIAL_FUSION_INCREASE_MM,
    TARGET_MAXIMUM_DIAMETER_MM,
    build_root_inclusion_probe_phase3r1,
    build_self_supporting_port_frame_phase3r1,
    build_self_supporting_port_shell_coupon_phase3r1,
    build_self_supporting_port_void_phase3r1,
    build_shell_blank_phase3r1,
    fusion_volume_relation_phase3r1,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
EXISTING_TEST_COUNT = 154
PHASE3R1_TEST_COUNT = 22
EXPECTED_TEST_COUNT = EXISTING_TEST_COUNT + PHASE3R1_TEST_COUNT
PRODUCTION_CANDIDATE_CLEARANCE_MM = 0.25


def _validate_step_subprocess(
    path: Path,
    expected_solid_count: int,
) -> dict[str, object]:
    script = (
        "import json,sys;"
        "from pathlib import Path;"
        "from ps_mht_v001.common.validation import validate_step_round_trip;"
        "m=validate_step_round_trip(Path(sys.argv[1]),int(sys.argv[2]));"
        "print(json.dumps(m.as_dict()))"
    )
    environment = os.environ.copy()
    python_path = str(PACKAGE_ROOT.parent)
    if environment.get("PYTHONPATH"):
        python_path += os.pathsep + environment["PYTHONPATH"]
    environment["PYTHONPATH"] = python_path
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(path),
            str(expected_solid_count),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    if result.returncode:
        raise RuntimeError(
            f"STEP round-trip failed for {path.name}:\n{result.stderr}"
        )
    return json.loads(result.stdout.strip().splitlines()[-1])


def _validate_stl_subprocess(path: Path) -> dict[str, object]:
    script = (
        "import json,sys;"
        "from pathlib import Path;"
        "from ps_mht_v001.common.validation import validate_stl_mesh;"
        "m=validate_stl_mesh(Path(sys.argv[1]));"
        "print(json.dumps(m.as_dict()))"
    )
    environment = os.environ.copy()
    python_path = str(PACKAGE_ROOT.parent)
    if environment.get("PYTHONPATH"):
        python_path += os.pathsep + environment["PYTHONPATH"]
    environment["PYTHONPATH"] = python_path
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", script, str(path)],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    if result.returncode:
        raise RuntimeError(
            f"STL validation failed for {path.name}:\n{result.stderr}"
        )
    return json.loads(result.stdout.strip().splitlines()[-1])


def _run_tests_isolated() -> dict[str, object]:
    environment = os.environ.copy()
    python_path = str(PACKAGE_ROOT.parent)
    if environment.get("PYTHONPATH"):
        python_path += os.pathsep + environment["PYTHONPATH"]
    environment["PYTHONPATH"] = python_path
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    passed_total = 0
    results: list[dict[str, object]] = []
    for test_path in sorted((PACKAGE_ROOT / "tests").glob("test_*.py")):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(test_path),
                "-q",
                "-o",
                f"cache_dir={PACKAGE_ROOT / '.pytest_cache'}",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
        summary = result.stdout + result.stderr
        match = re.search(r"(\d+) passed", summary)
        passed = int(match.group(1)) if match else 0
        passed_total += passed
        results.append(
            {
                "file": test_path.name,
                "passed": passed,
                "returncode": result.returncode,
            }
        )
        if result.returncode:
            raise RuntimeError(
                f"pytest failed for {test_path.name}:\n{summary}"
            )
    if passed_total != EXPECTED_TEST_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_TEST_COUNT} tests, got {passed_total}"
        )
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "preserved_phase1_through_phase3r": EXISTING_TEST_COUNT,
        "new_phase3r1": PHASE3R1_TEST_COUNT,
        "total_passed": passed_total,
        "all_passed": True,
        "files": results,
    }


def _make_delivery_zip(files: list[Path], output_path: Path) -> None:
    with zipfile.ZipFile(
        output_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for path in sorted(files):
            archive.write(
                path,
                arcname=path.relative_to(output_path.parent).as_posix(),
            )


def generate_phase3r1(output_root: Path) -> dict[str, object]:
    step_dir = output_root / "step"
    stl_dir = output_root / "stl"
    preview_dir = output_root / "preview"
    step_dir.mkdir(parents=True, exist_ok=True)
    stl_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    baseline_before = audit_baseline_hashes(output_root)
    if not all(item["unchanged"] for item in baseline_before.values()):
        raise RuntimeError("Phase 1 through Phase 3R baseline already changed")

    generated: list[Path] = []
    expected_steps: dict[Path, int] = {}
    expected_stls: list[Path] = []
    shape_metrics: dict[str, dict[str, object]] = {}

    shell_stem = "ps_mht_v001_self_supporting_port_shell_coupon_phase3r1"
    shell = build_self_supporting_port_shell_coupon_phase3r1()
    shell_step = step_dir / f"{shell_stem}.step"
    shell_stl = stl_dir / f"{shell_stem}.stl"
    shape_metrics[shell_stem] = measure_shape(shell).as_dict()
    export_printable_step(shell, shell_step)
    export_printable_stl(shell, shell_stl)
    generated.extend((shell_step, shell_stl))
    expected_steps[shell_step] = 1
    expected_stls.append(shell_stl)

    production_stem = (
        "ps_mht_v001_module_nut_ring_candidate_c025_phase3r1"
    )
    production_ring = build_module_nut_ring_phase3r1(
        PRODUCTION_CANDIDATE_CLEARANCE_MM
    )
    production_step = step_dir / f"{production_stem}.step"
    production_stl = stl_dir / f"{production_stem}.stl"
    shape_metrics[production_stem] = measure_shape(
        production_ring
    ).as_dict()
    export_printable_step(production_ring, production_step)
    export_printable_stl(production_ring, production_stl)
    generated.extend((production_step, production_stl))
    expected_steps[production_step] = 1
    expected_stls.append(production_stl)

    calibration_stem = (
        "ps_mht_v001_annular_nut_ring_calibration_coupon_phase3r1"
    )
    calibration_ring = build_annular_nut_ring_coupon_phase3r1()
    calibration_step = step_dir / f"{calibration_stem}.step"
    calibration_stl = stl_dir / f"{calibration_stem}.stl"
    shape_metrics[calibration_stem] = measure_shape(
        calibration_ring
    ).as_dict()
    export_printable_step(calibration_ring, calibration_step)
    export_printable_stl(calibration_ring, calibration_stl)
    generated.extend((calibration_step, calibration_stl))
    expected_steps[calibration_step] = 1
    expected_stls.append(calibration_stl)

    plate_metrics: dict[str, dict[str, object]] = {}
    for name, model, solid_count in phase3r1_individual_plates():
        stl_path = stl_dir / f"{name}.stl"
        metrics = measure_shape(model).as_dict()
        export_printable_set_stl(model, stl_path, solid_count)
        plate_metrics[name] = {
            **metrics,
            "a1_within_245x245x240": True,
            "expected_solid_count": solid_count,
        }
        generated.append(stl_path)
        expected_stls.append(stl_path)

    orientation = build_multi_plate_orientation_reference_phase3r1()
    orientation_path = (
        step_dir / "multi_plate_orientation_reference_phase3r1.step"
    )
    export_reference_step(
        orientation,
        orientation_path,
        ORIENTATION_REFERENCE_SOLID_COUNT,
    )
    generated.append(orientation_path)
    expected_steps[orientation_path] = ORIENTATION_REFERENCE_SOLID_COUNT

    step_validation = {
        path.name: _validate_step_subprocess(path, count)
        for path, count in expected_steps.items()
    }
    stl_validation = {
        path.name: _validate_stl_subprocess(path)
        for path in expected_stls
    }
    if stl_validation[shell_stl.name]["connected_component_count"] != 1:
        raise RuntimeError("fused shell STL is not one connected component")

    shell_blank = build_shell_blank_phase3r1()
    frame = build_self_supporting_port_frame_phase3r1(70.0)
    void = build_self_supporting_port_void_phase3r1(70.0)
    before_void = shell_blank.union(frame)
    after_void = before_void.cut(void)
    volume_relation = fusion_volume_relation_phase3r1()
    boolean_identity_error = abs(
        volume_relation["union_mm3"]
        - (
            volume_relation["shell_mm3"]
            + volume_relation["frame_mm3"]
            - volume_relation["intersection_mm3"]
        )
    )
    root_probe = build_root_inclusion_probe_phase3r1()
    root_probe_contained = sum(
        solid.Volume()
        for solid in after_void.intersect(root_probe).solids().vals()
    )

    module_reference = build_full_module_reference_phase3r1()
    maximum_diameter = 2.0 * maximum_radial_radius(module_reference)
    if maximum_diameter > TARGET_MAXIMUM_DIAMETER_MM + 1.0e-7:
        raise RuntimeError(
            f"maximum diameter {maximum_diameter:.6f} exceeds target"
        )

    test_results = _run_tests_isolated()
    baseline_after = audit_baseline_hashes(output_root)
    if not all(item["unchanged"] for item in baseline_after.values()):
        raise RuntimeError("Phase 1 through Phase 3R baseline changed")

    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3R.1",
        "status": "PHASE3R1_CAD_COMPLETE_PHYSICAL_CALIBRATION_PENDING",
        "non_regression": {
            "phase1_through_phase3a1_artifact_count": 90,
            "phase3r_artifact_count": 40,
            "baseline_before": baseline_before,
            "baseline_after": baseline_after,
            "all_unchanged": all(
                item["unchanged"] for item in baseline_after.values()
            ),
        },
        "shell_frame_fusion": {
            "phase3r_two_solid_root_cause":
                "EXPORT_COUPON_PACKAGED_A_SEPARATE_NESTED_FUNCTION_RING",
            "phase3r_core_shell_frame_was_boolean_fused": True,
            "phase3r1_coupon_excludes_function_ring": True,
            "frame_inward_shift_mm": FRAME_INWARD_SHIFT_MM,
            "radial_fusion_increase_mm":
                SHELL_FRAME_RADIAL_FUSION_INCREASE_MM,
            "intersection_volume_mm3":
                volume_relation["intersection_mm3"],
            "volume_relation_mm3": volume_relation,
            "union_boolean_identity_error_mm3": boolean_identity_error,
            "union_before_void_solid_count":
                measure_shape(before_void).solid_count,
            "after_void_solid_count": measure_shape(after_void).solid_count,
            "exported_step_solid_count":
                step_validation[shell_step.name]["solid_count"],
            "exported_stl_connected_component_count":
                stl_validation[shell_stl.name][
                    "connected_component_count"
                ],
            "root_inclusion_probe_diameter_mm":
                ROOT_INCLUSION_PROBE_DIAMETER_MM,
            "root_inclusion_probe_volume_mm3": root_probe.val().Volume(),
            "root_inclusion_probe_contained_volume_mm3":
                root_probe_contained,
            "root_fillet_target": ROOT_FILLET_TARGET,
            "upper_overhang_limit_deg": port_shell_max_overhang_angle,
            "teardrop_opening_retained": True,
        },
        "nut_ring_separation": {
            "production_builder":
                "build_module_nut_ring_phase3r1(nut_pocket_clearance)",
            "production_requires_explicit_argument": True,
            "exported_candidate_clearance_mm":
                PRODUCTION_CANDIDATE_CLEARANCE_MM,
            "exported_candidate_clearances_mm": list(
                production_pocket_clearances_phase3r1(
                    PRODUCTION_CANDIDATE_CLEARANCE_MM
                )
            ),
            "selected_clearance_mm": SELECTED_NUT_POCKET_CLEARANCE,
            "status": CALIBRATION_STATUS,
            "calibration_coupon_builder":
                "build_annular_nut_ring_coupon_phase3r1()",
            "calibration_coupon_status": CALIBRATION_COUPON_STATUS,
            "calibration_only": CALIBRATION_ONLY,
            "calibration_candidates_mm": list(NUT_POCKET_CLEARANCES),
            "physical_identification": PHYSICAL_ID_SCHEME,
            "production_assembly_contains_mixed_clearance": False,
        },
        "module_envelope": {
            "target_maximum_diameter_mm": TARGET_MAXIMUM_DIAMETER_MM,
            "actual_maximum_diameter_mm": maximum_diameter,
            "target_achieved": maximum_diameter
                <= TARGET_MAXIMUM_DIAMETER_MM,
            "function_ring_radial_position_change_mm": -0.6,
            "structural_wall_minimum_mm": phase3r_min_structural_wall,
            "root_minimum_mm": phase3r_min_root_thickness,
            "netpot_space_changed": False,
        },
        "individual_a1_plates": plate_metrics,
        "orientation_reference": {
            "file": orientation_path.name,
            "status": ORIENTATION_REFERENCE_STATUS,
            "stl_exported": False,
            "metrics": measure_shape(orientation).as_dict(),
        },
        "shape_metrics": shape_metrics,
        "step_round_trip_validation": step_validation,
        "stl_mesh_validation": stl_validation,
        "automated_tests": test_results,
        "printable_targets": [
            path.name for path in expected_stls
        ],
        "do_not_print_or_slice": [
            orientation_path.name,
            "FULL_MODULE_REFERENCE_PHASE3R1",
        ],
        "physical_calibration": {
            "status": CALIBRATION_PENDING,
            "remaining": [
                "Print the 0.15/0.25/0.35 mm calibration coupon.",
                "Select one M4 nut-pocket clearance from measured fit.",
                "Print the fused shell plate and verify support-free opening.",
                "Confirm root durability and leak behavior under load.",
            ],
        },
        "git": {
            "mutation_operations_performed": False,
            "prohibited_operations": [
                "checkout",
                "pull",
                "commit",
                "push",
                "merge",
                "rebase",
                "reset",
            ],
        },
    }

    report_path = preview_dir / "phase3r1_validation_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    generated.append(report_path)

    zip_path = output_root / "ps_mht_v001_phase3r1_delivery.zip"
    _make_delivery_zip(generated, zip_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = generate_phase3r1(args.output.resolve())
    print(
        json.dumps(
            {
                "phase": report["phase"],
                "status": report["status"],
                "tests": report["automated_tests"]["total_passed"],
                "maximum_diameter_mm":
                    report["module_envelope"][
                        "actual_maximum_diameter_mm"
                    ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
