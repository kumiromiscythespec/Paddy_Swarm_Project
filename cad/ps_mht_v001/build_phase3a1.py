"""Generate and validate PS-MHT-V001 Phase 3A.1 correction artifacts."""

from __future__ import annotations

import argparse
import gc
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Callable

import cadquery as cq

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ps_mht_v001.assembly.complete_port_assembly_phase3a1 import (
    COMPLETE_ASSEMBLY_SOLID_COUNT,
    COMPLETE_PASSAGE_DIAMETER,
    ROOT_RING_RETENTION_METHOD,
    build_complete_port_assembly_phase3a1,
    build_complete_port_exploded_phase3a1,
    build_complete_port_passage_probe,
    build_complete_port_section_phase3a1,
    complete_port_interference_report,
    netpot_bottom_z,
    passage_interference_report,
)
from ps_mht_v001.common.phase_baseline import audit_baseline_hashes
from ps_mht_v001.common.validation import (
    export_printable_set_step,
    export_printable_set_stl,
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    export_svg_preview,
    measure_shape,
    validate_printable_set,
    validate_single_printable,
)
from ps_mht_v001.coupons.complete_port_passage_coupon import (
    COUPON_SOLID_COUNT as COMPLETE_PASSAGE_COUPON_SOLIDS,
    build_complete_port_passage_coupon,
)
from ps_mht_v001.coupons.m3_port_cartridge_fit_coupon import (
    COUPON_SOLID_COUNT as M3_COUPON_SOLIDS,
    M3_CARTRIDGE_CLEARANCES,
    build_m3_port_cartridge_fit_coupon,
)
from ps_mht_v001.coupons.port_receiver_adapter_coupon_phase3a1 import (
    ADAPTER_CLEARANCES,
    COUPON_SOLID_COUNT as RECEIVER_COUPON_SOLIDS,
    build_port_receiver_adapter_coupon_phase3a1,
)
from ps_mht_v001.coupons.root_ring_passage_coupon import (
    COUPON_SOLID_COUNT as ROOT_RING_COUPON_SOLIDS,
    ROOT_RING_CLEARANCES,
    build_root_ring_passage_coupon,
)
from ps_mht_v001.parameters import (
    CALIBRATION_ITEMS,
    m3_clearance_diameter,
    m3_fastener_boss_radius,
    m3_fastener_pitch_radius,
    m3_metal_nut_across_flats,
    m3_port_cartridge_clearance,
    m3_port_retainer_arm_thickness,
    port_adapter_inner_diameter,
    root_ring_passage_clearance,
    tower_max_diameter,
    validate_parameters,
)
from ps_mht_v001.tower_module.m3_port_nut_cartridge import (
    CARTRIDGE_STATUS,
    PRINT_ORIENTATION as M3_PRINT_ORIENTATION,
    RETAINER_STATUS,
    build_m3_port_nut_cartridge,
    build_m3_port_nut_cartridge_retainer,
    m3_cartridge_slot_side_wall,
)
from ps_mht_v001.tower_module.netpot_60_adapter import (
    OPERATION as NETPOT_ADAPTER_OPERATION,
    REMOVAL as NETPOT_ADAPTER_REMOVAL,
    RETENTION_POLICY as NETPOT_ADAPTER_RETENTION,
    ROTATION_POLICY as NETPOT_ADAPTER_ROTATION,
)
from ps_mht_v001.tower_module.planting_port import (
    DO_NOT_PRINT_STATUS,
    build_m3_slot_side_wall_probe_local,
    build_m3_wall_probe_local,
    build_planting_module_with_ports_phase3a,
    build_planting_port_receiver,
    containment_ratio,
    maximum_radial_radius,
)
from ps_mht_v001.tower_module.planting_port_adapter import (
    build_common_adapter_full_length_passage_probe,
    build_planting_port_adapter,
)
from ps_mht_v001.tower_module.port_adapter_retainer import (
    STATUS as OLD_RETAINER_STATUS,
)
from ps_mht_v001.tower_module.root_sleeve_retaining_ring import (
    build_root_sleeve_retaining_ring,
    root_ring_actual_maximum_diameter,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
EXISTING_TEST_COUNT = 86
PHASE3A1_TEST_COUNT = 28
EXPECTED_TEST_COUNT = EXISTING_TEST_COUNT + PHASE3A1_TEST_COUNT


def _validation_subprocess(
    kind: str,
    path: Path,
    expected_solid_count: int = 1,
    printable: bool = False,
) -> dict[str, object]:
    """Validate each export in fresh native state."""

    script = (
        "import json,sys;"
        "from pathlib import Path;"
        "from ps_mht_v001.common.validation import "
        "validate_step_round_trip,validate_stl_mesh;"
        "p=Path(sys.argv[2]);"
        "m=(validate_step_round_trip(p,int(sys.argv[3]),"
        "printable=sys.argv[4]=='1') if sys.argv[1]=='step' "
        "else validate_stl_mesh(p));"
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
            kind,
            str(path),
            str(expected_solid_count),
            "1" if printable else "0",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{kind} validation failed for {path.name}: {result.stderr}"
        )
    return json.loads(result.stdout.strip().splitlines()[-1])


def _run_tests_isolated() -> dict[str, object]:
    """Run every test file in fresh OCCT state and aggregate the result."""

    environment = os.environ.copy()
    python_path = str(PACKAGE_ROOT.parent)
    if environment.get("PYTHONPATH"):
        python_path += os.pathsep + environment["PYTHONPATH"]
    environment["PYTHONPATH"] = python_path
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    results: list[dict[str, object]] = []
    passed_total = 0
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
            check=False,
            capture_output=True,
            text=True,
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
        if result.returncode != 0:
            raise RuntimeError(
                f"pytest failed for {test_path.name}:\n{summary}"
            )
    if passed_total != EXPECTED_TEST_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_TEST_COUNT} passing tests, got {passed_total}"
        )
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "existing_phase1_through_phase3a": EXISTING_TEST_COUNT,
        "new_phase3a1": PHASE3A1_TEST_COUNT,
        "total_passed": passed_total,
        "expected_total": EXPECTED_TEST_COUNT,
        "all_passed": True,
        "files": results,
    }


def _export_printable_pair(
    model: cq.Workplane,
    stem: str,
    step_dir: Path,
    stl_dir: Path,
    solid_count: int = 1,
) -> tuple[Path, Path, dict[str, object]]:
    step_path = step_dir / f"{stem}.step"
    stl_path = stl_dir / f"{stem}.stl"
    if solid_count == 1:
        metrics = validate_single_printable(model, stem).as_dict()
        export_printable_step(model, step_path)
        export_printable_stl(model, stl_path)
    else:
        metrics = validate_printable_set(
            model, stem, solid_count
        ).as_dict()
        export_printable_set_step(model, step_path, solid_count)
        export_printable_set_stl(model, stl_path, solid_count)
    return step_path, stl_path, metrics


def _make_delivery_zip(
    output_root: Path,
    generated_paths: list[Path],
    zip_path: Path,
) -> Path:
    """Package source/docs/tests and Phase 3A.1 outputs only."""

    excluded_parts = {"__pycache__", ".pytest_cache"}
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_ROOT.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(PACKAGE_ROOT)
            if any(part in excluded_parts for part in relative.parts):
                continue
            if path.suffix.lower() not in {".py", ".md", ".json"}:
                continue
            if relative.parts and relative.parts[0] == "exports":
                continue
            archive.write(path, f"ps_mht_v001/{relative.as_posix()}")
        for path in sorted(generated_paths):
            if path == zip_path:
                continue
            relative = path.relative_to(PACKAGE_ROOT)
            archive.write(path, f"ps_mht_v001/{relative.as_posix()}")
    return zip_path


def generate_phase3a1(output_root: Path) -> dict[str, object]:
    """Build, export, re-import, mesh-check, test, report, and package."""

    validate_parameters()
    baseline_before = audit_baseline_hashes(output_root)
    if not all(item["unchanged"] for item in baseline_before.values()):
        raise RuntimeError(
            "Phase 1/2/3A baseline hash changed before Phase 3A.1 build"
        )

    step_dir = output_root / "step"
    stl_dir = output_root / "stl"
    preview_dir = output_root / "preview"
    for directory in (step_dir, stl_dir, preview_dir):
        directory.mkdir(parents=True, exist_ok=True)

    generated_paths: list[Path] = []
    source_metrics: dict[str, object] = {}
    step_validation: dict[str, object] = {}
    stl_validation: dict[str, object] = {}

    printable_specs: tuple[
        tuple[str, Callable[[], cq.Workplane], int], ...
    ] = (
        (
            "ps_mht_v001_planting_port_adapter_phase3a1",
            build_planting_port_adapter,
            1,
        ),
        (
            "ps_mht_v001_m3_port_nut_cartridge_phase3a1",
            build_m3_port_nut_cartridge,
            1,
        ),
        (
            "ps_mht_v001_m3_port_nut_cartridge_retainer_phase3a1",
            build_m3_port_nut_cartridge_retainer,
            1,
        ),
        (
            "ps_mht_v001_root_sleeve_retaining_ring_phase3a1",
            build_root_sleeve_retaining_ring,
            1,
        ),
        (
            "ps_mht_v001_port_receiver_adapter_coupon_phase3a1",
            build_port_receiver_adapter_coupon_phase3a1,
            RECEIVER_COUPON_SOLIDS,
        ),
        (
            "ps_mht_v001_m3_port_cartridge_fit_coupon_phase3a1",
            build_m3_port_cartridge_fit_coupon,
            M3_COUPON_SOLIDS,
        ),
        (
            "ps_mht_v001_complete_port_passage_coupon_phase3a1",
            build_complete_port_passage_coupon,
            COMPLETE_PASSAGE_COUPON_SOLIDS,
        ),
        (
            "ps_mht_v001_root_ring_passage_coupon_phase3a1",
            build_root_ring_passage_coupon,
            ROOT_RING_COUPON_SOLIDS,
        ),
    )
    for stem, factory, solid_count in printable_specs:
        model = factory()
        step_path, stl_path, metrics = _export_printable_pair(
            model,
            stem,
            step_dir,
            stl_dir,
            solid_count,
        )
        source_metrics[stem] = metrics
        generated_paths.extend((step_path, stl_path))
        del model
        gc.collect()

    reference_specs: tuple[
        tuple[str, Callable[[], cq.Workplane], int], ...
    ] = (
        (
            "ps_mht_v001_complete_port_assembly_phase3a1",
            build_complete_port_assembly_phase3a1,
            COMPLETE_ASSEMBLY_SOLID_COUNT,
        ),
        (
            "ps_mht_v001_complete_port_exploded_phase3a1",
            build_complete_port_exploded_phase3a1,
            COMPLETE_ASSEMBLY_SOLID_COUNT,
        ),
        (
            "ps_mht_v001_complete_port_passage_probe_phase3a1",
            build_complete_port_passage_probe,
            1,
        ),
    )
    for stem, factory, solid_count in reference_specs:
        model = factory()
        path = step_dir / f"{stem}.step"
        source_metrics[stem] = measure_shape(model).as_dict()
        export_reference_step(model, path, solid_count)
        generated_paths.append(path)
        del model
        gc.collect()

    section_path = (
        preview_dir / "ps_mht_v001_complete_port_section_phase3a1.svg"
    )
    export_svg_preview(
        build_complete_port_section_phase3a1(),
        section_path,
        (0.0, -1.0, 0.0),
    )
    generated_paths.append(section_path)

    for path in generated_paths:
        if path.suffix.lower() == ".step":
            expected = next(
                count
                for stem, _, count in printable_specs + reference_specs
                if path.stem == stem
            )
            step_validation[path.name] = _validation_subprocess(
                "step",
                path,
                expected,
                printable=expected == 1
                and "assembly" not in path.stem
                and "exploded" not in path.stem
                and "passage_probe" not in path.stem,
            )
        elif path.suffix.lower() == ".stl":
            stl_validation[path.name] = _validation_subprocess("stl", path)

    receiver = build_planting_port_receiver()
    common_adapter_probe_intersection = sum(
        solid.Volume()
        for solid in build_planting_port_adapter()
        .intersect(build_common_adapter_full_length_passage_probe())
        .solids()
        .vals()
    )
    m3_boss_probe_ratios = {
        f"side_{side:+d}": containment_ratio(
            receiver,
            build_m3_wall_probe_local(side * m3_fastener_pitch_radius),
        )
        for side in (-1, 1)
    }
    m3_slot_probe_ratios = {
        f"side_{side:+d}": containment_ratio(
            receiver,
            build_m3_slot_side_wall_probe_local(side),
        )
        for side in (-1, 1)
    }
    corrected_module_diameter = 2.0 * maximum_radial_radius(
        build_planting_module_with_ports_phase3a()
    )
    ring_results = {
        f"{clearance:.2f}": {
            "actual_maximum_diameter_mm":
                root_ring_actual_maximum_diameter(clearance),
            "actual_radial_clearance_mm": 0.5
            * (
                port_adapter_inner_diameter
                - root_ring_actual_maximum_diameter(clearance)
            ),
        }
        for clearance in ROOT_RING_CLEARANCES
    }
    test_results = _run_tests_isolated()
    baseline_after = audit_baseline_hashes(output_root)
    if not all(item["unchanged"] for item in baseline_after.values()):
        raise RuntimeError(
            "Phase 1/2/3A baseline hash changed during Phase 3A.1 build"
        )

    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3A.1",
        "status": "CORRECTION_CAD_COMPLETE_CALIBRATION_PENDING",
        "full_module_print_status": DO_NOT_PRINT_STATUS,
        "baseline_audit_before": baseline_before,
        "baseline_audit_after": baseline_after,
        "complete_passage": {
            "probe_diameter_mm": COMPLETE_PASSAGE_DIAMETER,
            "common_adapter_inner_diameter_mm":
                port_adapter_inner_diameter,
            "common_adapter_full_length_probe_diameter_mm":
                port_adapter_inner_diameter,
            "common_adapter_full_length_probe_intersection_mm3":
                common_adapter_probe_intersection,
            "component_intersections_mm3": passage_interference_report(),
            "all_structural_intersections_zero": all(
                volume <= 1.0e-8
                for volume in passage_interference_report().values()
            ),
            "netpot_bottom_z_mm": netpot_bottom_z(),
            "root_ring_position": "COMMON_ADAPTER_INNER_END_DATUM",
            "root_ring_retention": ROOT_RING_RETENTION_METHOD,
            "solid_seat_inside_bore": False,
            "debris_shelf": False,
        },
        "complete_assembly": {
            "solid_count": COMPLETE_ASSEMBLY_SOLID_COUNT,
            "prohibited_intersections_mm3":
                complete_port_interference_report(),
            "all_prohibited_intersections_zero": all(
                volume <= 1.0e-8
                for volume in complete_port_interference_report().values()
            ),
        },
        "m3_external_cartridge": {
            "cartridge_status": CARTRIDGE_STATUS,
            "retainer_status": RETAINER_STATUS,
            "old_annular_retainer_status": OLD_RETAINER_STATUS,
            "metal_nut_assumed_across_flats_mm":
                m3_metal_nut_across_flats,
            "selected_clearance_per_side_mm":
                m3_port_cartridge_clearance,
            "coupon_clearances_per_side_mm":
                list(M3_CARTRIDGE_CLEARANCES),
            "nominal_boss_radial_wall_mm":
                m3_fastener_boss_radius - 0.5 * m3_clearance_diameter,
            "required_boss_wall_mm": 5.0,
            "actual_boss_probe_containment_ratio":
                m3_boss_probe_ratios,
            "nominal_slot_side_wall_at_selected_mm":
                m3_cartridge_slot_side_wall(m3_port_cartridge_clearance),
            "nominal_slot_side_wall_at_worst_coupon_mm":
                m3_cartridge_slot_side_wall(
                    max(M3_CARTRIDGE_CLEARANCES)
                ),
            "required_slot_outer_wall_mm": 3.0,
            "actual_slot_wall_probe_containment_ratio":
                m3_slot_probe_ratios,
            "gate_minimum_thickness_mm":
                m3_port_retainer_arm_thickness,
            "required_gate_minimum_thickness_mm": 2.4,
            "print_orientation": M3_PRINT_ORIENTATION,
        },
        "root_ring_passage": {
            "selected_clearance_per_side_mm":
                root_ring_passage_clearance,
            "candidate_results": ring_results,
            "tab_inclusive_measurement": True,
            "tabs": "THREE_ROUNDED_TABS_NO_SHARP_CORNERS",
            "externally_removable": True,
            "retention_method": ROOT_RING_RETENTION_METHOD,
        },
        "netpot_adapter": {
            "operation": NETPOT_ADAPTER_OPERATION,
            "removal": NETPOT_ADAPTER_REMOVAL,
            "rotation_policy": NETPOT_ADAPTER_ROTATION,
            "retention_policy": NETPOT_ADAPTER_RETENTION,
        },
        "module_envelope": {
            "actual_maximum_diameter_mm": corrected_module_diameter,
            "limit_mm": tower_max_diameter,
            "within_limit": corrected_module_diameter
            <= tower_max_diameter,
        },
        "coupon_matrix": {
            "receiver_adapter_clearance_mm":
                list(ADAPTER_CLEARANCES),
            "m3_cartridge_clearance_mm":
                list(M3_CARTRIDGE_CLEARANCES),
            "complete_passage": [
                "REAL_RECEIVER",
                "REAL_COMMON_ADAPTER",
                "REAL_NETPOT_ADAPTER",
                "REAL_ROOT_RING",
                "D60_NETPOT_AXIS_GAUGE",
                "D48_FOLDED_ROOT_GAUGE",
            ],
            "root_ring_radial_clearance_mm":
                list(ROOT_RING_CLEARANCES),
        },
        "source_shape_metrics": source_metrics,
        "step_round_trip_validation": step_validation,
        "stl_mesh_validation": stl_validation,
        "automated_tests": test_results,
        "calibration": CALIBRATION_ITEMS,
        "remaining_physical_validation": [
            "Measure actual purchased M3 nut across flats and thickness.",
            "Print the M3 cartridge coupon and select insertion/removal force.",
            "Print the root-ring passage coupon and select washable fit.",
            "Validate sleeve-fold axial retention at the inner-end datum; "
            "a positive solid seat is intentionally absent to preserve "
            "the full φ66 adapter passage.",
            "Measure purchased netpot and verify liner insertion/removal force.",
            "Leak-test the corrected receiver, gasket, and common adapter stack.",
            "Do not print the full module until all prior coupon gates pass.",
        ],
    }
    report_path = preview_dir / "phase3a1_validation_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    generated_paths.append(report_path)

    zip_path = output_root / "ps_mht_v001_phase3a1_delivery.zip"
    _make_delivery_zip(output_root, generated_paths, zip_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    args = parser.parse_args()
    report = generate_phase3a1(args.output.resolve())
    print(
        json.dumps(
            {
                "phase": report["phase"],
                "status": report["status"],
                "tests": report["automated_tests"]["total_passed"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
