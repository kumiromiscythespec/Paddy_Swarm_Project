"""Generate and validate Phase 3P-A physical fit and envelope-audit outputs."""

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

from ps_mht_v001.audit.port_fastener_envelope_audit_phase3pa import (
    port_fastener_envelope_audit_phase3pa,
)
from ps_mht_v001.audit.port_function_ring_audit_phase3pa import (
    port_function_ring_audit_phase3pa,
)
from ps_mht_v001.audit.port_maximum_diameter_audit_phase3pa import (
    maximum_diameter_audit_phase3pa,
    ring_candidate_comparison_phase3pa,
)
from ps_mht_v001.common.phase3pa_nonregression import (
    audit_phase1_through_phase3sa2,
)
from ps_mht_v001.common.validation import (
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    export_svg_preview,
    measure_shape,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.coupons.netpot_fit_print_plate_phase3pa import (
    OPTIONAL_THREE_UP_MINIMUM_WIDTH_MM,
    OPTIONAL_THREE_UP_STATUS,
    phase3pa_individual_plates,
)
from ps_mht_v001.coupons.netpot_seat_fit_coupon_phase3pa import (
    build_netpot_seat_fit_coupon_phase3pa,
    coupon_feature_policy_phase3pa,
    fit_theory_phase3pa,
    passage_token_phase3pa,
)
from ps_mht_v001.parameters import (
    netpot_body_passage_candidates,
    netpot_body_passage_preferred_precalibration,
    netpot_body_passage_selected,
    phase3sa_seam_clearance_selected,
    print_bed_x,
    print_bed_y,
    print_bed_z,
)
from ps_mht_v001.print_manifest_phase3pa import (
    build_print_manifest_phase3pa,
)
from ps_mht_v001.reference.siawadeky_netpot_measurements_phase3pa import (
    siawadeky_measurements_phase3pa,
)
from ps_mht_v001.reference.siawadeky_netpot_reference_envelope_phase3pa import (
    build_siawadeky_netpot_reference_envelope_phase3pa,
    reference_envelope_metadata_phase3pa,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
EXPECTED_EXISTING_TEST_COUNT = 260
EXPECTED_PHASE3PA_TEST_COUNT = 46
EXPECTED_TEST_COUNT = EXPECTED_EXISTING_TEST_COUNT + EXPECTED_PHASE3PA_TEST_COUNT


def _make_zip(files: list[Path], path: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(files):
            archive.write(item, item.relative_to(path.parent).as_posix())


def _write_json(path: Path, payload: dict[str, object]) -> Path:
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


def _starting_state() -> dict[str, object]:
    return {
        "repository_root": _git_read_only("rev-parse", "--show-toplevel"),
        "branch": _git_read_only("branch", "--show-current"),
        "head": _git_read_only("rev-parse", "HEAD"),
        "cadquery_version": cq.__version__,
        "git_status_short": _git_read_only("status", "--short").splitlines(),
        "tracked_diff_files": _git_read_only("diff", "--name-only").splitlines(),
        "staged_diff_files": _git_read_only(
            "diff", "--cached", "--name-only"
        ).splitlines(),
        "a1_build_envelope_mm": [print_bed_x, print_bed_y, print_bed_z],
    }


def _run_tests_isolated() -> dict[str, object]:
    environment = os.environ.copy()
    python_path = str(PACKAGE_ROOT.parent)
    if environment.get("PYTHONPATH"):
        python_path += os.pathsep + environment["PYTHONPATH"]
    environment["PYTHONPATH"] = python_path
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    total = 0
    phase3pa_total = 0
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
        if test_path.name.startswith("test_phase3pa_"):
            phase3pa_total += passed
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
        raise RuntimeError(f"expected {EXPECTED_TEST_COUNT} tests, got {total}")
    if phase3pa_total != EXPECTED_PHASE3PA_TEST_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_PHASE3PA_TEST_COUNT} Phase 3P-A tests, "
            f"got {phase3pa_total}"
        )
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "existing_phase1_through_phase3sa2": EXPECTED_EXISTING_TEST_COUNT,
        "new_phase3pa": phase3pa_total,
        "total_passed": total,
        "all_passed": True,
        "files": results,
    }


def _physical_test_procedure() -> dict[str, object]:
    return {
        "A_INSERTION": [
            "VERTICAL_TOOL_FREE_INSERTION",
            "NO_STRONG_DEFORMATION_OR_RIB_CATCH",
            "BODY_PASSES_FULL_DEPTH_AND_FLANGE_SEATS",
        ],
        "B_SEATING": [
            "FULL_CIRCUMFERENCE_CONTACT",
            "NO_ONE_SIDED_LIFT_OR_LARGE_FLANGE_WARP",
            "NATURAL_CENTERING",
        ],
        "C_PLAY": [
            "RECORD_BODY_LATERAL_PLAY",
            "RECORD_ROTATIONAL_PLAY",
            "REJECT_EXCESSIVE_PRACTICAL_WOBBLE",
        ],
        "D_TWENTY_CYCLES": [
            "TWENTY_TOOL_FREE_INSERTION_REMOVAL_CYCLES",
            "CHECK_POT_WHITENING_CRACK_AND_RIB_DAMAGE",
            "CHECK_RING_CHIP_AND_CRACK",
            "RECORD_INVERTED_RETENTION",
        ],
        "E_27_DEGREE": [
            "TEST_EMPTY_POT",
            "TEST_WET_SPONGE_EQUIVALENT",
            "TEST_500G_REFERENCE_LOAD",
            "NO_NATURAL_SLIDE_OR_FLANGE_OVERRUN",
        ],
    }


def generate_phase3pa(output_root: Path) -> dict[str, object]:
    start = _starting_state()
    baseline_before = audit_phase1_through_phase3sa2(output_root)
    if not all(item["unchanged"] for item in baseline_before.values()):
        raise RuntimeError("Phase 1 through Phase 3S-A.2 baseline changed")
    if phase3sa_seam_clearance_selected is not None:
        raise RuntimeError("Phase 3S-A seam selection must remain None")
    if netpot_body_passage_selected is not None:
        raise RuntimeError("net-pot passage selection must remain None")

    step_dir = output_root / "step"
    stl_dir = output_root / "stl"
    preview_dir = output_root / "preview"
    for directory in (step_dir, stl_dir, preview_dir):
        directory.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    expected_steps: dict[Path, int] = {}
    expected_stls: dict[Path, int] = {}
    shape_metrics: dict[str, dict[str, object]] = {}

    envelope = build_siawadeky_netpot_reference_envelope_phase3pa()
    envelope_path = (
        step_dir
        / "ps_mht_v001_siawadeky_netpot_reference_envelope_phase3pa.step"
    )
    export_reference_step(envelope, envelope_path, 1)
    generated.append(envelope_path)
    expected_steps[envelope_path] = 1
    shape_metrics[envelope_path.stem] = measure_shape(envelope).as_dict()

    coupons: dict[float, cq.Workplane] = {}
    for passage in netpot_body_passage_candidates:
        token = passage_token_phase3pa(passage)
        model = build_netpot_seat_fit_coupon_phase3pa(passage)
        coupons[passage] = model
        stem = f"ps_mht_v001_netpot_seat_fit_coupon_{token}_phase3pa"
        step_path = step_dir / f"{stem}.step"
        stl_path = stl_dir / f"{stem}.stl"
        export_printable_step(model, step_path)
        export_printable_stl(model, stl_path)
        generated.extend((step_path, stl_path))
        expected_steps[step_path] = 1
        expected_stls[stl_path] = 1
        shape_metrics[stem] = measure_shape(model).as_dict()

    plate_metrics: dict[str, dict[str, object]] = {}
    for name, model in phase3pa_individual_plates():
        path = stl_dir / f"{name}.stl"
        export_printable_stl(model, path)
        generated.append(path)
        expected_stls[path] = 1
        plate_metrics[name] = measure_shape(model).as_dict()

    function_ring_audit = port_function_ring_audit_phase3pa()
    fastener_audit = port_fastener_envelope_audit_phase3pa()
    ring_comparison = ring_candidate_comparison_phase3pa()
    maximum_audit = maximum_diameter_audit_phase3pa()
    audit_outputs = {
        "phase3pa_existing_port_function_ring_audit.json":
            function_ring_audit,
        "phase3pa_m4_fastener_envelope_audit.json": fastener_audit,
        "phase3pa_ring_outer_diameter_comparison.json": ring_comparison,
        "phase3pa_maximum_diameter_audit.json": maximum_audit,
    }
    for name, payload in audit_outputs.items():
        generated.append(_write_json(preview_dir / name, payload))

    section_path = (
        preview_dir / "ps_mht_v001_netpot_fit_section_phase3pa.svg"
    )
    iso_path = (
        preview_dir / "ps_mht_v001_netpot_fit_isometric_phase3pa.svg"
    )
    preview_model = envelope.union(coupons[80.5].translate((130.0, 0.0, 0.0)))
    export_svg_preview(preview_model, section_path, (0.0, -1.0, 0.0))
    export_svg_preview(preview_model, iso_path, (1.0, -1.0, 0.7))
    generated.extend((section_path, iso_path))

    manifest = build_print_manifest_phase3pa()
    manifest_path = preview_dir / "print_manifest_phase3pa.json"
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
                f"{path.name}: expected {expected_components} components, "
                f"got {actual}"
            )

    baseline_after = audit_phase1_through_phase3sa2(output_root)
    if not all(item["unchanged"] for item in baseline_after.values()):
        raise RuntimeError("Phase 1 through Phase 3S-A.2 baseline changed")

    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3P-A",
        "status": "PHYSICAL_FIT_CALIBRATION_PENDING",
        "starting_state": start,
        "phase3sa2_state": {
            "selected_clearance": phase3sa_seam_clearance_selected,
            "test_count": EXPECTED_EXISTING_TEST_COUNT,
            "independent_from_phase3pa": True,
        },
        "measurements": siawadeky_measurements_phase3pa(),
        "deprecated_assumptions": {
            "flange_78_5": "REJECTED_BY_PHYSICAL_MEASUREMENT",
            "body_72_0": "REJECTED_BY_PHYSICAL_MEASUREMENT",
            "phase3r1_bore_84_0": "NOT_FINAL_EXCESS_CLEARANCE",
        },
        "selected_passage_mm": netpot_body_passage_selected,
        "preferred_precalibration_mm":
            netpot_body_passage_preferred_precalibration,
        "reference_envelope": {
            **reference_envelope_metadata_phase3pa(),
            "file_name": envelope_path.name,
            "shape_metrics": shape_metrics[envelope_path.stem],
        },
        "coupon_feature_policy": coupon_feature_policy_phase3pa(),
        "fit_candidates": {
            passage_token_phase3pa(passage): fit_theory_phase3pa(passage)
            for passage in netpot_body_passage_candidates
        },
        "coupon_shape_metrics": {
            name: value
            for name, value in shape_metrics.items()
            if "coupon" in name
        },
        "individual_plates": plate_metrics,
        "optional_three_up_plate": {
            "generated": False,
            "minimum_width_with_15mm_spacing_mm":
                OPTIONAL_THREE_UP_MINIMUM_WIDTH_MM,
            "status": OPTIONAL_THREE_UP_STATUS,
        },
        "physical_test_procedure": _physical_test_procedure(),
        "selection_rule": {
            "c805": "FIRST_CANDIDATE_NOT_FINAL_SELECTION",
            "c800": "TEST_ONLY_IF_C805_TOO_LOOSE",
            "c810": "TEST_ONLY_IF_C805_TOO_TIGHT",
            "selected_until_physical_test": None,
        },
        "existing_port_function_ring_audit": function_ring_audit,
        "m4_fastener_envelope_audit": fastener_audit,
        "ring_outer_diameter_comparison": ring_comparison,
        "maximum_diameter_audit": maximum_audit,
        "step_round_trip_validation": step_validation,
        "stl_mesh_validation": stl_validation,
        "print_manifest": manifest,
        "non_regression": {
            phase: item["unchanged"]
            for phase, item in baseline_after.items()
        },
        "non_regression_artifact_count": sum(
            len(item["expected"]) for item in baseline_after.values()
        ),
        "automated_tests": {"status": "RUNNING"},
        "not_generated": [
            "FINAL_PORT_FUNCTION_RING",
            "FINAL_M4_EARS",
            "FINAL_PORT_BACKING_RING",
            "FINAL_NETPOT_LINER",
            "FINAL_120_DEGREE_PANEL_PORT_INTEGRATION",
            "PHASE3SA1_PLATE_02_TO_04",
            "FULL_170MM_MODULE",
            "FULL_TOWER",
        ],
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
                "branch_creation",
                "pull_request_creation",
            ],
        },
    }
    report_path = preview_dir / "phase3pa_validation_report.json"
    generated.append(report_path)
    zip_path = output_root / "ps_mht_v001_phase3pa_delivery.zip"
    _write_json(report_path, report)
    _make_zip(generated, zip_path)

    report["automated_tests"] = _run_tests_isolated()
    report["non_regression_after_tests"] = {
        phase: item["unchanged"]
        for phase, item in audit_phase1_through_phase3sa2(output_root).items()
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
    report = generate_phase3pa(args.output.resolve())
    print(
        json.dumps(
            {
                "phase": report["phase"],
                "status": report["status"],
                "selected_passage_mm": report["selected_passage_mm"],
                "tests": report["automated_tests"]["total_passed"],
                "existing_ring": report[
                    "existing_port_function_ring_audit"
                ]["status"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
