"""Generate and verify PS-MHT-V001 Phase 3H-A calibration deliverables."""

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

from ps_mht_v001.common.phase3ha_nonregression import (
    audit_existing_before_phase3ha,
)
from ps_mht_v001.common.validation import (
    export_printable_set_step,
    export_printable_set_stl,
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    export_svg_preview,
    measure_shape,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.coupons.horizontal_joint_arc_coupon_phase3ha import (
    arc_coupon_requirements_phase3ha,
    build_horizontal_joint_arc_coupon_phase3ha,
)
from ps_mht_v001.parameters import (
    final_port_assembly,
    horizontal_joint_clearance_candidates,
    horizontal_joint_clearance_selected,
    module_buffer_0_4L_status,
    module_buffer_0_6L_status,
    module_buffer_0_8L_status,
    netpot_20_cycle_test,
    netpot_27deg_retention_test,
    netpot_500g_load_test,
    netpot_body_passage_observed_lateral_play_mm,
    netpot_body_passage_observed_play_measurement_method,
    netpot_body_passage_selected,
    netpot_body_passage_selection_status,
    netpot_c800_status,
    netpot_c810_status,
    netpot_wet_media_test,
    phase3cb0_audit_status,
    phase3cb0_cad_generation,
    print_bed_x,
    print_bed_y,
    print_bed_z,
    scoped_next_phase_cad,
)
from ps_mht_v001.print_manifest_phase3ha import build_print_manifest_phase3ha
from ps_mht_v001.reference.temporary_test_membrane_phase3ha import (
    build_temporary_test_membrane_reference_phase3ha,
    temporary_test_membrane_requirements_phase3ha,
)
from ps_mht_v001.test_fixtures.horizontal_joint_compression_fixture_phase3ha import (
    build_horizontal_joint_compression_assembly_reference_phase3ha,
    build_horizontal_joint_compression_ring_phase3ha,
    compression_fixture_requirements_phase3ha,
)
from ps_mht_v001.tower_module.horizontal_ring_joint_phase3ha import (
    build_full_ring_joint_pair_phase3ha,
    build_lower_full_ring_phase3ha,
    build_upper_full_ring_print_phase3ha,
    clearance_token_phase3ha,
    horizontal_joint_requirements_phase3ha,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
EXPECTED_EXISTING_TEST_COUNT = 306
EXPECTED_PHASE3HA_TEST_COUNT = 28
EXPECTED_TOTAL_TEST_COUNT = (
    EXPECTED_EXISTING_TEST_COUNT + EXPECTED_PHASE3HA_TEST_COUNT
)
EXPECTED_NONREGRESSION_OUTPUT_COUNT = 207


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def _make_zip(files: list[Path], path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(files):
            archive.write(item, item.relative_to(path.parent).as_posix())


def _all_nonregression_unchanged(
    report: dict[str, dict[str, object]],
) -> bool:
    return all(bool(item["unchanged"]) for item in report.values())


def _nonregression_output_count(
    report: dict[str, dict[str, object]],
) -> int:
    return sum(
        len(item["expected"])
        for name, item in report.items()
        if name != "phase3cb0_sources"
    )


def _run_tests_isolated() -> dict[str, object]:
    environment = os.environ.copy()
    python_path = str(PACKAGE_ROOT.parent)
    if environment.get("PYTHONPATH"):
        python_path += os.pathsep + environment["PYTHONPATH"]
    environment["PYTHONPATH"] = python_path
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    total = 0
    phase3ha_total = 0
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
        output = result.stdout + result.stderr
        match = re.search(r"(\d+) passed", output)
        passed = int(match.group(1)) if match else 0
        total += passed
        if test_path.name.startswith("test_phase3ha_"):
            phase3ha_total += passed
        results.append(
            {
                "file": test_path.name,
                "passed": passed,
                "returncode": result.returncode,
            }
        )
        if result.returncode:
            raise RuntimeError(f"{test_path.name} failed:\n{output}")
    if total != EXPECTED_TOTAL_TEST_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_TOTAL_TEST_COUNT} tests, got {total}"
        )
    if phase3ha_total != EXPECTED_PHASE3HA_TEST_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_PHASE3HA_TEST_COUNT} Phase 3H-A tests, "
            f"got {phase3ha_total}"
        )
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "existing_phase1_through_phase3pa": EXPECTED_EXISTING_TEST_COUNT,
        "new_phase3ha": phase3ha_total,
        "total_passed": total,
        "all_passed": True,
        "files": results,
    }


def _physical_test_procedure() -> dict[str, object]:
    return {
        "arc_sequence": [
            "C050_READY_FIRST",
            "C030_ONLY_IF_C050_TOO_LOOSE",
            "C070_ONLY_IF_C050_TOO_TIGHT",
        ],
        "arc_selection_authority": False,
        "full_ring": {
            "assembly": [
                "TOOL_FREE_NO_IMPACT",
                "FULL_CIRCUMFERENCE_HARD_STOP_SEATING",
                "RECORD_AXIAL_RADIAL_PLAY_AND_TIME",
            ],
            "compression": [
                "THREE_M4_REFERENCES_TIGHTEN_EVENLY",
                "STOP_AT_HARD_STOP",
                "DO_NOT_CRUSH_PETG",
                "MEASURE_HEIGHT_BEFORE_AFTER",
            ],
            "repetition_cycles": 10,
            "static_leak": {
                "head_above_joint_mm": 20,
                "duration_hours": 12,
                "maximum_leakage_ml_per_joint": 5,
                "continuous_jet_allowed": False,
            },
            "flow_down": {
                "volume_l": 2.0,
                "target_flow_l_per_min": 1.0,
            },
            "compression_hold_hours": 24,
        },
        "selection_rule": {
            "c050": "FIRST_FULL_RING_CANDIDATE_AFTER_ARC_PASS",
            "c030": "IF_C050_LEAKS_OR_HAS_EXCESSIVE_PLAY",
            "c070": "IF_C050_CANNOT_ASSEMBLE_OR_WHITENS",
            "selected_before_full_ring_test": None,
        },
    }


def generate_phase3ha(output_root: Path) -> dict[str, object]:
    baseline_before = audit_existing_before_phase3ha(output_root, PACKAGE_ROOT)
    if not _all_nonregression_unchanged(baseline_before):
        raise RuntimeError("pre-Phase 3H-A baseline SHA mismatch")
    if _nonregression_output_count(baseline_before) != EXPECTED_NONREGRESSION_OUTPUT_COUNT:
        raise RuntimeError("unexpected pre-Phase 3H-A output count")
    if horizontal_joint_clearance_selected is not None:
        raise RuntimeError("joint clearance must remain unselected")

    step_dir = output_root / "step"
    stl_dir = output_root / "stl"
    preview_dir = output_root / "preview"
    for directory in (step_dir, stl_dir, preview_dir):
        directory.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    expected_steps: dict[Path, int] = {}
    expected_stls: dict[Path, int] = {}
    shape_metrics: dict[str, dict[str, object]] = {}

    for clearance in horizontal_joint_clearance_candidates:
        token = clearance_token_phase3ha(clearance)
        model = build_horizontal_joint_arc_coupon_phase3ha(clearance)
        stem = f"horizontal_joint_arc_coupon_{token}_phase3ha"
        step_path = step_dir / f"{stem}.step"
        stl_path = stl_dir / f"{stem}.stl"
        export_printable_set_step(model, step_path, 2)
        export_printable_set_stl(model, stl_path, 2)
        generated.extend((step_path, stl_path))
        expected_steps[step_path] = 2
        expected_stls[stl_path] = 2
        shape_metrics[stem] = measure_shape(model).as_dict()

    c050_reference = build_full_ring_joint_pair_phase3ha(0.5)
    c050_reference_path = (
        step_dir / "full_ring_joint_pair_c050_reference_phase3ha.step"
    )
    export_reference_step(c050_reference, c050_reference_path, 2)
    generated.append(c050_reference_path)
    expected_steps[c050_reference_path] = 2
    shape_metrics[c050_reference_path.stem] = measure_shape(
        c050_reference
    ).as_dict()

    compression_ring = build_horizontal_joint_compression_ring_phase3ha()
    compression_step = step_dir / "horizontal_joint_compression_ring_phase3ha.step"
    compression_stl = stl_dir / "horizontal_joint_compression_ring_phase3ha.stl"
    export_printable_step(compression_ring, compression_step)
    export_printable_stl(compression_ring, compression_stl)
    generated.extend((compression_step, compression_stl))
    expected_steps[compression_step] = 1
    expected_stls[compression_stl] = 1
    shape_metrics[compression_step.stem] = measure_shape(compression_ring).as_dict()

    compression_assembly = (
        build_horizontal_joint_compression_assembly_reference_phase3ha(0.5)
    )
    compression_assembly_path = (
        step_dir / "horizontal_joint_compression_assembly_reference_phase3ha.step"
    )
    export_reference_step(compression_assembly, compression_assembly_path, 19)
    generated.append(compression_assembly_path)
    expected_steps[compression_assembly_path] = 19
    shape_metrics[compression_assembly_path.stem] = measure_shape(
        compression_assembly
    ).as_dict()

    membrane = build_temporary_test_membrane_reference_phase3ha()
    membrane_path = step_dir / "temporary_test_membrane_reference_phase3ha.step"
    export_reference_step(membrane, membrane_path, 1)
    generated.append(membrane_path)
    expected_steps[membrane_path] = 1
    shape_metrics[membrane_path.stem] = measure_shape(membrane).as_dict()

    section_path = preview_dir / "horizontal_joint_section_phase3ha.svg"
    isometric_path = preview_dir / "horizontal_joint_isometric_phase3ha.svg"
    export_svg_preview(c050_reference, section_path, (0.0, -1.0, 0.0))
    export_svg_preview(c050_reference, isometric_path, (1.0, -1.0, 0.7))
    generated.extend((section_path, isometric_path))

    manifest = build_print_manifest_phase3ha()
    manifest_path = preview_dir / "print_manifest_phase3ha.json"
    generated.append(_write_json(manifest_path, manifest))

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
                f"{path.name}: expected {expected_components} STL components, "
                f"got {actual}"
            )

    baseline_after_geometry = audit_existing_before_phase3ha(
        output_root, PACKAGE_ROOT
    )
    if not _all_nonregression_unchanged(baseline_after_geometry):
        raise RuntimeError("pre-existing artifact SHA changed during generation")

    lower_metrics = measure_shape(build_lower_full_ring_phase3ha()).as_dict()
    upper_metrics = {
        clearance_token_phase3ha(clearance): measure_shape(
            build_upper_full_ring_print_phase3ha(clearance)
        ).as_dict()
        for clearance in horizontal_joint_clearance_candidates
    }
    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3H-A",
        "status": "CAD_COMPLETE_PHYSICAL_CALIBRATION_PENDING",
        "cadquery_version": cq.__version__,
        "a1_build_envelope_mm": [print_bed_x, print_bed_y, print_bed_z],
        "physical_c805_body_passage_result": {
            "selected_mm": netpot_body_passage_selected,
            "selection_status": netpot_body_passage_selection_status,
            "pots_tested": 3,
            "tool_free": True,
            "rib_catching": False,
            "full_flange_seating": True,
            "visible_tilt": False,
            "observed_lateral_play": netpot_body_passage_observed_lateral_play_mm,
            "play_measurement_method": netpot_body_passage_observed_play_measurement_method,
            "c800_status": netpot_c800_status,
            "c810_status": netpot_c810_status,
            "twenty_cycle_test": netpot_20_cycle_test,
            "retention_27deg": netpot_27deg_retention_test,
            "wet_media": netpot_wet_media_test,
            "load_500g": netpot_500g_load_test,
            "final_port_assembly": final_port_assembly,
            "complete_port_approval": False,
        },
        "phase3cb0_history": {
            "audit_status": phase3cb0_audit_status,
            "cad_generation": phase3cb0_cad_generation,
            "scoped_next_phase_cad": scoped_next_phase_cad,
        },
        "buffer_targets": {
            "0.4_L": module_buffer_0_4L_status,
            "0.6_L": module_buffer_0_6L_status,
            "0.8_L": module_buffer_0_8L_status,
            "geometry_generated": False,
        },
        "horizontal_joint": {
            "selected_clearance_mm_per_side": horizontal_joint_clearance_selected,
            "requirements_by_candidate": {
                clearance_token_phase3ha(clearance):
                    horizontal_joint_requirements_phase3ha(clearance)
                for clearance in horizontal_joint_clearance_candidates
            },
            "lower_print_metrics": lower_metrics,
            "upper_print_metrics": upper_metrics,
            "arc_coupon_requirements": {
                clearance_token_phase3ha(clearance):
                    arc_coupon_requirements_phase3ha(clearance)
                for clearance in horizontal_joint_clearance_candidates
            },
        },
        "compression_fixture": compression_fixture_requirements_phase3ha(),
        "temporary_test_membrane": temporary_test_membrane_requirements_phase3ha(),
        "shape_metrics": shape_metrics,
        "step_round_trip_validation": step_validation,
        "stl_mesh_validation": stl_validation,
        "print_manifest": manifest,
        "physical_test_procedure": _physical_test_procedure(),
        "not_generated": [
            "FULL_RING_PRINT_STL_BEFORE_SELECTION",
            "PLANTING_PORT",
            "NETPOT_SEAT",
            "CAPILLARY_BUFFER",
            "OVERFLOW",
            "DRAIN",
            "WICK",
            "ROOT_ZONE_RING",
            "PRODUCTION_M4_ROUTE",
            "FIVE_BAND_170MM_MODULE",
            "WATER_SYSTEM",
            "FIVE_STAGE_TOWER",
        ],
        "non_regression": {
            "artifact_count": EXPECTED_NONREGRESSION_OUTPUT_COUNT,
            "source_count": 8,
            "results": {
                name: item["unchanged"]
                for name, item in baseline_after_geometry.items()
            },
        },
        "automated_tests": {"status": "RUNNING"},
        "git": {
            "commands_executed": [],
            "mutation_operations_performed": False,
        },
    }
    report_path = preview_dir / "phase3ha_validation_report.json"
    generated.append(report_path)
    zip_path = output_root / "ps_mht_v001_phase3ha_delivery.zip"
    _write_json(report_path, report)
    _make_zip(generated, zip_path)

    report["automated_tests"] = _run_tests_isolated()
    baseline_after_tests = audit_existing_before_phase3ha(
        output_root, PACKAGE_ROOT
    )
    if not _all_nonregression_unchanged(baseline_after_tests):
        raise RuntimeError("pre-existing artifact SHA changed during tests")
    report["non_regression_after_tests"] = {
        name: item["unchanged"]
        for name, item in baseline_after_tests.items()
    }
    report["generated_files"] = [
        path.relative_to(output_root).as_posix()
        for path in sorted(generated)
    ]
    _write_json(report_path, report)
    _make_zip(generated, zip_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = generate_phase3ha(args.output.resolve())
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
