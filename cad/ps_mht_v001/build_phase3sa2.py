"""Generate and validate Phase 3S-A.2 full-length seam artifacts."""

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

from ps_mht_v001.assembly.full_length_seam_calibration_reference_phase3sa2 import (
    ASSEMBLY_SOLID_COUNT,
    build_full_length_seam_calibration_reference_phase3sa2,
)
from ps_mht_v001.common.phase3sa2_nonregression import (
    audit_phase1_through_phase3sa1,
)
from ps_mht_v001.common.validation import (
    export_printable_set_step,
    export_printable_set_stl,
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    measure_shape,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.coupons.full_length_seam_pair_phase3sa2 import (
    build_full_length_seam_pair_phase3sa2,
    full_length_seam_requirements_phase3sa2,
)
from ps_mht_v001.parameters import (
    phase3sa2_seam_clearance_candidates,
    phase3sa_seam_clearance_selected,
)
from ps_mht_v001.print_manifest_phase3sa2 import (
    build_print_manifest_phase3sa2,
)
from ps_mht_v001.print_plate_layout_phase3sa2 import (
    PART_SPACING_MM,
    build_optional_combined_c040_c060_plate_phase3sa2,
    phase3sa2_required_plates,
)
from ps_mht_v001.tower_module.full_length_seam_capture_fixture_phase3sa2 import (
    build_full_length_seam_capture_fixture_phase3sa2,
    fixture_requirements_phase3sa2,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
EXPECTED_TEST_COUNT = 260


def _make_zip(files: list[Path], path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(files):
            archive.write(
                item,
                item.relative_to(path.parent).as_posix(),
            )


def _run_tests_isolated() -> dict[str, object]:
    environment = os.environ.copy()
    python_path = str(PACKAGE_ROOT.parent)
    if environment.get("PYTHONPATH"):
        python_path += os.pathsep + environment["PYTHONPATH"]
    environment["PYTHONPATH"] = python_path
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    total = 0
    results: list[dict[str, object]] = []
    for test_path in sorted((PACKAGE_ROOT / "tests").glob("test_*.py")):
        if test_path.name.startswith("test_phase3pa_"):
            continue
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
        output = result.stdout + result.stderr
        match = re.search(r"(\d+) passed", output)
        passed = int(match.group(1)) if match else 0
        total += passed
        results.append(
            {
                "file": test_path.name,
                "passed": passed,
                "returncode": result.returncode,
            }
        )
        if result.returncode:
            raise RuntimeError(f"{test_path.name} failed:\n{output}")
    if total != EXPECTED_TEST_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_TEST_COUNT} tests, got {total}"
        )
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "preserved_through_phase3sa1": 242,
        "new_phase3sa2": EXPECTED_TEST_COUNT - 242,
        "total_passed": total,
        "all_passed": True,
        "files": results,
    }


def generate_phase3sa2(output_root: Path) -> dict[str, object]:
    baseline_before = audit_phase1_through_phase3sa1(output_root)
    if not all(item["unchanged"] for item in baseline_before.values()):
        raise RuntimeError("Phase 1 through Phase 3S-A.1 baseline changed")
    if phase3sa_seam_clearance_selected is not None:
        raise RuntimeError("selected clearance must remain None")

    step_dir = output_root / "step"
    stl_dir = output_root / "stl"
    preview_dir = output_root / "preview"
    for directory in (step_dir, stl_dir, preview_dir):
        directory.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    expected_steps: dict[Path, int] = {}
    expected_stls: dict[Path, int] = {}
    shape_metrics: dict[str, dict[str, object]] = {}

    for clearance in phase3sa2_seam_clearance_candidates:
        token = f"c{int(round(clearance * 100)):03d}"
        stem = f"ps_mht_v001_full_length_seam_pair_{token}_phase3sa2"
        model = build_full_length_seam_pair_phase3sa2(clearance)
        step_path = step_dir / f"{stem}.step"
        stl_path = stl_dir / f"{stem}.stl"
        export_printable_set_step(model, step_path, 2)
        export_printable_set_stl(model, stl_path, 2)
        generated.extend((step_path, stl_path))
        expected_steps[step_path] = 2
        expected_stls[stl_path] = 2
        shape_metrics[stem] = measure_shape(model).as_dict()

    fixture = build_full_length_seam_capture_fixture_phase3sa2()
    fixture_stem = (
        "ps_mht_v001_full_length_seam_capture_fixture_phase3sa2"
    )
    fixture_step = step_dir / f"{fixture_stem}.step"
    fixture_stl = stl_dir / f"{fixture_stem}.stl"
    export_printable_step(fixture, fixture_step)
    export_printable_stl(fixture, fixture_stl)
    generated.extend((fixture_step, fixture_stl))
    expected_steps[fixture_step] = 1
    expected_stls[fixture_stl] = 1
    shape_metrics[fixture_stem] = measure_shape(fixture).as_dict()

    plate_metrics: dict[str, dict[str, object]] = {}
    for name, model, count in phase3sa2_required_plates():
        path = stl_dir / f"{name}.stl"
        export_printable_set_stl(model, path, count)
        generated.append(path)
        expected_stls[path] = count
        plate_metrics[name] = {
            **measure_shape(model).as_dict(),
            "part_spacing_minimum_mm": PART_SPACING_MM,
        }

    combined = build_optional_combined_c040_c060_plate_phase3sa2()
    combined_metrics = measure_shape(combined)
    combined_fits_a1 = (
        combined_metrics.size_x <= 245.0
        and combined_metrics.size_y <= 245.0
        and combined_metrics.size_z <= 240.0
    )
    combined_path = (
        stl_dir
        / "plate_optional_full_length_seam_c040_c060_phase3sa2.stl"
    )
    if combined_fits_a1:
        export_printable_set_stl(combined, combined_path, 4)
        generated.append(combined_path)
        expected_stls[combined_path] = 4

    assembly = build_full_length_seam_calibration_reference_phase3sa2()
    assembly_path = (
        step_dir
        / "ps_mht_v001_full_length_seam_assembly_reference_"
        "c040_c060_phase3sa2.step"
    )
    export_reference_step(assembly, assembly_path, ASSEMBLY_SOLID_COUNT)
    generated.append(assembly_path)
    expected_steps[assembly_path] = ASSEMBLY_SOLID_COUNT

    manifest = build_print_manifest_phase3sa2()
    manifest_path = preview_dir / "print_manifest_phase3sa2.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    generated.append(manifest_path)

    step_validation = {
        path.name: validate_step_round_trip(path, count).as_dict()
        for path, count in expected_steps.items()
    }
    stl_validation = {
        path.name: validate_stl_mesh(path).as_dict()
        for path in expected_stls
    }
    for path, expected_components in expected_stls.items():
        actual = stl_validation[path.name]["connected_component_count"]
        if actual != expected_components:
            raise RuntimeError(
                f"{path.name}: expected {expected_components} components, "
                f"got {actual}"
            )

    baseline_after = audit_phase1_through_phase3sa1(output_root)
    if not all(item["unchanged"] for item in baseline_after.values()):
        raise RuntimeError("Phase 1 through Phase 3S-A.1 baseline changed")

    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3S-A.2",
        "status": "FULL_LENGTH_PHYSICAL_CALIBRATION_PENDING",
        "selected_clearance": phase3sa_seam_clearance_selected,
        "short_coupon_physical_results": {
            "c040": {
                "leak_test":
                    "PASS_ON_SHORT_COUPON_WHEN_MANUALLY_SEATED",
                "assembly_force": "UNRESOLVED",
                "stress_whitening": "UNRESOLVED",
                "full_length_behavior": "CALIBRATION_PENDING",
            },
            "c060": {
                "leak_test":
                    "PASS_ON_SHORT_COUPON_WHEN_MANUALLY_SEATED",
                "assembly_force": "UNRESOLVED",
                "stress_whitening": "UNRESOLVED",
                "full_length_behavior": "CALIBRATION_PENDING",
            },
            "c080": {
                "leak_test": "FAIL",
                "failure_mode": "WATER_LEAK_WHEN_SEATED",
                "selection_status": "REJECTED",
            },
        },
        "full_length_pairs": {
            f"c{int(round(value * 100)):03d}":
                full_length_seam_requirements_phase3sa2(value)
            for value in phase3sa2_seam_clearance_candidates
        },
        "fixture": fixture_requirements_phase3sa2(),
        "shape_metrics": shape_metrics,
        "individual_plates": plate_metrics,
        "optional_combined_plate": {
            **combined_metrics.as_dict(),
            "a1_fit": combined_fits_a1,
            "generated": combined_fits_a1,
            "part_spacing_minimum_mm": PART_SPACING_MM,
        },
        "assembly_reference": {
            **measure_shape(assembly).as_dict(),
            "print_status": "REFERENCE_ONLY_DO_NOT_PRINT_AS_ASSEMBLY",
        },
        "step_round_trip_validation": step_validation,
        "stl_mesh_validation": stl_validation,
        "non_regression": {
            phase: item["unchanged"]
            for phase, item in baseline_after.items()
        },
        "automated_tests": {"status": "RUNNING"},
        "git": {
            "mutation_operations_performed": False,
            "prohibited_operations": [
                "checkout",
                "pull",
                "add",
                "commit",
                "push",
                "merge",
                "rebase",
                "reset",
            ],
        },
    }
    report_path = preview_dir / "phase3sa2_validation_report.json"
    generated.append(report_path)
    zip_path = output_root / "ps_mht_v001_phase3sa2_delivery.zip"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _make_zip(generated, zip_path)

    report["automated_tests"] = _run_tests_isolated()
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _make_zip(generated, zip_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = generate_phase3sa2(args.output.resolve())
    print(
        json.dumps(
            {
                "phase": report["phase"],
                "status": report["status"],
                "selected_clearance": report["selected_clearance"],
                "tests": report["automated_tests"]["total_passed"],
                "optional_combined_plate":
                    report["optional_combined_plate"]["generated"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
