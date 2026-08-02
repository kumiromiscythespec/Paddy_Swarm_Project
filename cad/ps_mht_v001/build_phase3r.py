"""Generate and validate PS-MHT-V001 Phase 3R refactoring artifacts."""

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
from cadquery import exporters

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ps_mht_v001.assembly.full_module_reference_phase3r import (
    PRINT_STATUS,
    build_full_module_reference_phase3r,
)
from ps_mht_v001.assembly.module_pair_phase3r import (
    MODULE_PAIR_SOLID_COUNT,
    build_module_pair_0deg_phase3r,
    build_module_pair_30deg_misassembly_phase3r,
    build_module_pair_60deg_phase3r,
    module_pair_alignment_interference_phase3r,
)
from ps_mht_v001.assembly.planting_port_phase3r import (
    build_planting_port_phase3r,
    port_components_phase3r,
)
from ps_mht_v001.assembly.port_exploded_phase3r import (
    build_port_exploded_phase3r,
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
    validate_multi_solid,
    validate_printable_set,
    validate_single_printable,
)
from ps_mht_v001.coupons.annular_nut_ring_coupon_phase3r import (
    build_annular_nut_ring_coupon_phase3r,
)
from ps_mht_v001.coupons.large_index_ring_coupon_phase3r import (
    COUPON_SOLID_COUNT as INDEX_COUPON_SOLIDS,
    LARGE_INDEX_CLEARANCES,
    build_large_index_ring_coupon_phase3r,
)
from ps_mht_v001.coupons.port_function_ring_coupon_phase3r import (
    BODY_CLEARANCE_CANDIDATES,
    COUPON_SOLID_COUNT as PORT_COUPON_SOLIDS,
    build_port_function_ring_coupon_phase3r,
)
from ps_mht_v001.coupons.self_supporting_port_shell_coupon_phase3r import (
    COUPON_SOLID_COUNT as SHELL_COUPON_SOLIDS,
    build_self_supporting_port_shell_coupon_set_phase3r,
)
from ps_mht_v001.parameters import (
    CALIBRATION_ITEMS,
    index_design_type,
    large_ring_selected_clearance,
    module_gasket_ring_inner_diameter,
    module_gasket_ring_outer_diameter,
    module_nut_pocket_clearance_candidates,
    netpot_siawadeky_body_diameter_pending,
    netpot_siawadeky_body_diameter_preliminary,
    netpot_siawadeky_flange_diameter_assumed,
    netpot_siawadeky_height_assumed,
    phase3r_min_independent_width,
    phase3r_gasket_groove_depth_candidates,
    phase3r_min_isolated_footprint,
    phase3r_min_root_thickness,
    phase3r_min_structural_wall,
    port_shell_max_overhang_angle,
    root_mesh_foldover_length,
    root_mesh_initial_length,
    tower_max_diameter,
    validate_parameters,
    wave_amplitude,
    wave_lobe_count,
    wave_ring_base_radius,
    wave_ring_inner_diameter,
)
from ps_mht_v001.print_plate_layout_phase3r import (
    PRINT_PLATE_SOLID_COUNT,
    STATUS as PRINT_PLATE_STATUS,
    build_print_plate_layout_phase3r,
    phase3r_plate_positions,
)
from ps_mht_v001.tower_module.module_alignment_ring_phase3r import (
    build_module_alignment_ring_phase3r,
    minimum_wave_curvature_radius,
)
from ps_mht_v001.tower_module.module_clamping_ring_phase3r import (
    build_module_clamping_ring_phase3r,
)
from ps_mht_v001.tower_module.module_gasket_ring_phase3r import (
    GASKET_MATERIAL,
    build_module_gasket_groove_void_phase3r,
    build_module_gasket_m4_hole_voids_phase3r,
    build_module_gasket_ring_phase3r,
)
from ps_mht_v001.tower_module.module_nut_ring_phase3r import (
    NUT_POCKET_COUNT as MODULE_NUT_POCKET_COUNT,
    RETAINER as MODULE_NUT_RETAINER,
    build_module_nut_ring_phase3r,
)
from ps_mht_v001.tower_module.planting_port import maximum_radial_radius
from ps_mht_v001.tower_module.port_backing_ring_phase3r import (
    NUT_POCKET_COUNT as PORT_NUT_POCKET_COUNT,
    SERVICE_POLICY as PORT_SERVICE_POLICY,
    build_port_backing_ring_phase3r,
)
from ps_mht_v001.tower_module.port_function_ring_phase3r import (
    ROUNDNESS_DATUM,
    build_port_function_ring_phase3r,
)
from ps_mht_v001.tower_module.root_sleeve_ring_phase3r import (
    LOAD_TESTS_PENDING_G,
    RETENTION as ROOT_RETENTION,
    build_root_sleeve_ring_phase3r,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
EXISTING_TEST_COUNT = 114
PHASE3R_TEST_COUNT = 40
EXPECTED_TEST_COUNT = EXISTING_TEST_COUNT + PHASE3R_TEST_COUNT


def _validation_subprocess(
    kind: str,
    path: Path,
    expected_solid_count: int = 1,
    printable: bool = False,
) -> dict[str, object]:
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
            raise RuntimeError(f"pytest failed for {test_path.name}:\n{summary}")
    if passed_total != EXPECTED_TEST_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_TEST_COUNT} passing tests, got {passed_total}"
        )
    return {
        "execution_mode": "ONE_TEST_FILE_PER_FRESH_OCCT_PROCESS",
        "existing_phase1_through_phase3a1": EXISTING_TEST_COUNT,
        "new_phase3r": PHASE3R_TEST_COUNT,
        "total_passed": passed_total,
        "all_passed": True,
        "files": results,
    }


def _export_pair(
    model: cq.Workplane,
    stem: str,
    step_dir: Path,
    stl_dir: Path,
    solid_count: int,
    a1_required: bool = True,
) -> tuple[Path, Path, dict[str, object]]:
    step_path = step_dir / f"{stem}.step"
    stl_path = stl_dir / f"{stem}.stl"
    if solid_count == 1 and a1_required:
        metrics = validate_single_printable(model, stem).as_dict()
        export_printable_step(model, step_path)
        export_printable_stl(model, stl_path)
    elif a1_required:
        metrics = validate_printable_set(model, stem, solid_count).as_dict()
        export_printable_set_step(model, step_path, solid_count)
        export_printable_set_stl(model, stl_path, solid_count)
    else:
        metrics = validate_multi_solid(model, stem, solid_count).as_dict()
        export_reference_step(model, step_path, solid_count)
        exporters.export(model, str(stl_path), exportType="STL")
    return step_path, stl_path, metrics


def _section_model() -> cq.Workplane:
    model = build_full_module_reference_phase3r()
    cutter = (
        cq.Workplane("XY")
        .box(260.0, 1.0, 190.0, centered=(True, True, False))
        .translate((0.0, 0.0, -10.0))
    )
    solids: list[cq.Shape] = []
    for solid in model.solids().vals():
        section = cq.Workplane("XY").newObject([solid]).intersect(cutter)
        solids.extend(section.solids().vals())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def _make_delivery_zip(
    generated_paths: list[Path],
    zip_path: Path,
) -> None:
    excluded = {"__pycache__", ".pytest_cache"}
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_ROOT.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(PACKAGE_ROOT)
            if any(part in excluded for part in relative.parts):
                continue
            if relative.parts and relative.parts[0] == "exports":
                continue
            if path.suffix.lower() not in {".py", ".md", ".json"}:
                continue
            archive.write(path, f"ps_mht_v001/{relative.as_posix()}")
        for path in sorted(generated_paths):
            relative = path.relative_to(PACKAGE_ROOT)
            archive.write(path, f"ps_mht_v001/{relative.as_posix()}")


def generate_phase3r(output_root: Path) -> dict[str, object]:
    validate_parameters()
    baseline_before = audit_baseline_hashes(output_root)
    if not all(item["unchanged"] for item in baseline_before.values()):
        raise RuntimeError("Phase 1 through Phase 3A.1 baseline changed")

    step_dir = output_root / "step"
    stl_dir = output_root / "stl"
    preview_dir = output_root / "preview"
    for directory in (step_dir, stl_dir, preview_dir):
        directory.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    metrics: dict[str, object] = {}
    expected_steps: dict[Path, int] = {}
    expected_stls: list[Path] = []

    primary_specs: tuple[
        tuple[str, Callable[[], cq.Workplane], int], ...
    ] = (
        (
            "ps_mht_v001_module_alignment_ring_phase3r",
            build_module_alignment_ring_phase3r,
            1,
        ),
        (
            "ps_mht_v001_module_nut_ring_phase3r",
            build_module_nut_ring_phase3r,
            1,
        ),
        (
            "ps_mht_v001_module_clamping_ring_phase3r",
            build_module_clamping_ring_phase3r,
            1,
        ),
        (
            "ps_mht_v001_module_gasket_ring_phase3r",
            build_module_gasket_ring_phase3r,
            1,
        ),
        (
            "ps_mht_v001_port_function_ring_phase3r",
            build_port_function_ring_phase3r,
            1,
        ),
        (
            "ps_mht_v001_port_backing_ring_phase3r",
            build_port_backing_ring_phase3r,
            1,
        ),
        (
            "ps_mht_v001_root_sleeve_ring_phase3r",
            build_root_sleeve_ring_phase3r,
            1,
        ),
    )
    for stem, factory, count in primary_specs:
        model = factory()
        step_path, stl_path, shape_metrics = _export_pair(
            model, stem, step_dir, stl_dir, count
        )
        metrics[stem] = shape_metrics
        generated.extend((step_path, stl_path))
        expected_steps[step_path] = count
        expected_stls.append(stl_path)
        del model
        gc.collect()

    coupon_specs: list[
        tuple[str, Callable[[], cq.Workplane], int]
    ] = [
        (
            "ps_mht_v001_large_index_ring_coupon_phase3r",
            lambda: build_large_index_ring_coupon_phase3r(
                large_ring_selected_clearance
            ),
            INDEX_COUPON_SOLIDS,
        ),
        (
            "ps_mht_v001_annular_nut_ring_coupon_phase3r",
            build_annular_nut_ring_coupon_phase3r,
            1,
        ),
        (
            "ps_mht_v001_port_function_ring_coupon_phase3r",
            lambda: build_port_function_ring_coupon_phase3r(0.50),
            PORT_COUPON_SOLIDS,
        ),
        (
            "ps_mht_v001_self_supporting_port_shell_coupon_phase3r",
            build_self_supporting_port_shell_coupon_set_phase3r,
            SHELL_COUPON_SOLIDS,
        ),
    ]
    for clearance in LARGE_INDEX_CLEARANCES:
        if clearance == large_ring_selected_clearance:
            continue
        token = f"{int(round(clearance * 100)):03d}"
        coupon_specs.append(
            (
                f"ps_mht_v001_large_index_ring_coupon_c{token}_phase3r",
                lambda c=clearance: build_large_index_ring_coupon_phase3r(c),
                INDEX_COUPON_SOLIDS,
            )
        )
    for clearance in BODY_CLEARANCE_CANDIDATES:
        if clearance == 0.50:
            continue
        token = f"{int(round(clearance * 100)):03d}"
        coupon_specs.append(
            (
                f"ps_mht_v001_port_function_ring_coupon_c{token}_phase3r",
                lambda c=clearance: build_port_function_ring_coupon_phase3r(c),
                PORT_COUPON_SOLIDS,
            )
        )
    for stem, factory, count in coupon_specs:
        model = factory()
        step_path, stl_path, shape_metrics = _export_pair(
            model, stem, step_dir, stl_dir, count
        )
        metrics[stem] = shape_metrics
        generated.extend((step_path, stl_path))
        expected_steps[step_path] = count
        expected_stls.append(stl_path)
        del model
        gc.collect()

    reference_specs: tuple[
        tuple[str, Callable[[], cq.Workplane], int], ...
    ] = (
        (
            "ps_mht_v001_module_pair_0deg_phase3r",
            build_module_pair_0deg_phase3r,
            MODULE_PAIR_SOLID_COUNT,
        ),
        (
            "ps_mht_v001_module_pair_60deg_phase3r",
            build_module_pair_60deg_phase3r,
            MODULE_PAIR_SOLID_COUNT,
        ),
        (
            "ps_mht_v001_module_pair_30deg_misassembly_phase3r",
            build_module_pair_30deg_misassembly_phase3r,
            MODULE_PAIR_SOLID_COUNT,
        ),
        (
            "ps_mht_v001_port_exploded_phase3r",
            build_port_exploded_phase3r,
            12,
        ),
    )
    for stem, factory, count in reference_specs:
        model = factory()
        path = step_dir / f"{stem}.step"
        metrics[stem] = measure_shape(model).as_dict()
        export_reference_step(model, path, count)
        generated.append(path)
        expected_steps[path] = count
        del model
        gc.collect()

    plate = build_print_plate_layout_phase3r()
    plate_step, plate_stl, plate_metrics = _export_pair(
        plate,
        "ps_mht_v001_print_plate_layout_phase3r",
        step_dir,
        stl_dir,
        PRINT_PLATE_SOLID_COUNT,
        a1_required=False,
    )
    metrics["ps_mht_v001_print_plate_layout_phase3r"] = plate_metrics
    generated.extend((plate_step, plate_stl))
    expected_steps[plate_step] = PRINT_PLATE_SOLID_COUNT
    expected_stls.append(plate_stl)

    section_path = preview_dir / "ps_mht_v001_phase3r_section.svg"
    iso_path = preview_dir / "ps_mht_v001_phase3r_isometric.svg"
    export_svg_preview(_section_model(), section_path, (0.0, -1.0, 0.0))
    export_svg_preview(
        build_full_module_reference_phase3r(),
        iso_path,
        (1.0, -1.0, 0.75),
    )
    generated.extend((section_path, iso_path))

    step_validation = {
        path.name: _validation_subprocess("step", path, count)
        for path, count in expected_steps.items()
    }
    stl_validation = {
        path.name: _validation_subprocess("stl", path)
        for path in expected_stls
    }

    full_module = build_full_module_reference_phase3r()
    maximum_diameter = 2.0 * maximum_radial_radius(full_module)
    interface_names = {
        "module_alignment_ring",
        "module_nut_ring",
        "module_clamping_ring",
        "module_gasket_ring",
    }
    port_names = {component.name for component in port_components_phase3r()}
    test_results = _run_tests_isolated()
    baseline_after = audit_baseline_hashes(output_root)
    if not all(item["unchanged"] for item in baseline_after.values()):
        raise RuntimeError("Phase 1 through Phase 3A.1 baseline changed")

    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3R",
        "status": "PHASE3R_CAD_COMPLETE_PHYSICAL_CALIBRATION_PENDING",
        "full_module_print_status": PRINT_STATUS,
        "baseline_before": baseline_before,
        "baseline_after": baseline_after,
        "physical_print_results": {
            "printer": "Bambu Lab A1",
            "material": "WHITE_PETG",
            "nozzle_mm": 0.4,
            "index_key_fit_coupon": {
                "result": "FAIL",
                "failure_mode": "KEY_ROOT_FRACTURE",
            },
            "m4_cartridge_fit_coupon": {
                "result": "FAIL_WITH_ONE_SURVIVOR",
                "decision": "REJECT_SMALL_GATE_AND_CARTRIDGE",
            },
            "angled_port_print_coupon": {
                "result": "FAIL",
                "decision": "REJECT_INTEGRATED_ANGLED_CIRCULAR_DATUM",
            },
            "successful_family": "LARGE_CIRCULAR_ANNULAR_ARC_PARTS",
        },
        "deprecated_after_print_failure": [
            "m4_nut_cartridge",
            "m4_nut_cartridge_retainer",
            "m3_port_nut_cartridge",
            "m3_port_nut_cartridge_retainer",
            "small_L_gate",
            "thin_six_keys",
            "integrated_angled_circular_receiver",
        ],
        "index_design": {
            "selected": index_design_type,
            "lobe_count": wave_lobe_count,
            "amplitude_mm": wave_amplitude,
            "minimum_continuous_radial_root_mm":
                wave_ring_base_radius
                - wave_amplitude
                - 0.5 * wave_ring_inner_diameter,
            "minimum_analytic_curvature_radius_mm":
                minimum_wave_curvature_radius(),
            "selected_clearance_mm": large_ring_selected_clearance,
            "interference_mm3": {
                "0deg": module_pair_alignment_interference_phase3r(0.0),
                "60deg": module_pair_alignment_interference_phase3r(60.0),
                "30deg": module_pair_alignment_interference_phase3r(30.0),
            },
        },
        "annular_m4_interface": {
            "nut_pocket_count": MODULE_NUT_POCKET_COUNT,
            "pocket_clearances_mm":
                list(module_nut_pocket_clearance_candidates),
            "retainer": MODULE_NUT_RETAINER,
            "load_path": "BROAD_ANNULAR_CONTACT_NOT_M4_ALONE",
            "gasket_material": GASKET_MATERIAL,
            "gasket_groove_depth_candidates_mm":
                list(phase3r_gasket_groove_depth_candidates),
            "gasket_to_m4_intersection_mm3": sum(
                solid.Volume()
                for solid in build_module_gasket_groove_void_phase3r()
                .intersect(build_module_gasket_m4_hole_voids_phase3r())
                .solids()
                .vals()
            ),
            "gasket_ring_radial_width_mm": 0.5
            * (
                module_gasket_ring_outer_diameter
                - module_gasket_ring_inner_diameter
            ),
        },
        "split_planting_port": {
            "roundness_datum": ROUNDNESS_DATUM,
            "shell_max_overhang_deg": port_shell_max_overhang_angle,
            "backing_nut_count": PORT_NUT_POCKET_COUNT,
            "backing_service_policy": PORT_SERVICE_POLICY,
            "assembly_components": sorted(port_names),
            "contains_deprecated_small_parts": any(
                "cartridge" in name.lower() or "gate" in name.lower()
                for name in port_names
            ),
        },
        "siawadeky_reference": {
            "flange_diameter_assumed_mm":
                netpot_siawadeky_flange_diameter_assumed,
            "height_assumed_mm": netpot_siawadeky_height_assumed,
            "body_diameter_pending": netpot_siawadeky_body_diameter_pending,
            "body_diameter_preliminary_mm":
                netpot_siawadeky_body_diameter_preliminary,
            "status": "REFERENCE_PRELIMINARY_CALIBRATION_PENDING",
        },
        "root_mesh": {
            "initial_length_mm": root_mesh_initial_length,
            "foldover_length_mm": root_mesh_foldover_length,
            "retention": ROOT_RETENTION,
            "load_tests_pending_g": list(LOAD_TESTS_PENDING_G),
        },
        "minimum_design_rules": {
            "isolated_footprint_mm2": phase3r_min_isolated_footprint,
            "independent_width_mm": phase3r_min_independent_width,
            "structural_wall_mm": phase3r_min_structural_wall,
            "root_thickness_mm": phase3r_min_root_thickness,
        },
        "part_reduction": {
            "removed_independent_small_parts_per_typical_module": 10,
            "removed_thin_key_features_per_interface": 6,
            "phase3r_printed_small_gate_or_cartridge_count": 0,
            "phase3r_interface_large_ring_functions": sorted(interface_names),
        },
        "module_envelope": {
            "actual_maximum_diameter_mm": maximum_diameter,
            "limit_mm": tower_max_diameter,
            "within_limit": maximum_diameter <= tower_max_diameter,
        },
        "print_layout": {
            "status": PRINT_PLATE_STATUS,
            "virtual_zones": phase3r_plate_positions(),
        },
        "shape_metrics": metrics,
        "step_round_trip_validation": step_validation,
        "stl_mesh_validation": stl_validation,
        "automated_tests": test_results,
        "calibration": CALIBRATION_ITEMS,
        "remaining_physical_validation": [
            "Print three large-index clearances and perform ten cycles.",
            "Verify 30-degree rejection on the printed wave rings.",
            "Measure actual M4 nuts, washers, and metal retention plate.",
            "Print the self-supporting shell coupon without support.",
            "Measure the delivered Siawadeky body, flange, taper, and ribs.",
            "Regenerate the preliminary port liner after pot measurement.",
            "Load-test the folded mesh ring at 500 g and 1 kg.",
            "Verify purchased EPDM is a solid 3 mm round section.",
            "Do not print the full module before all coupon gates pass.",
        ],
    }
    report_path = preview_dir / "phase3r_validation_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    generated.append(report_path)

    zip_path = output_root / "ps_mht_v001_phase3r_delivery.zip"
    _make_delivery_zip(generated, zip_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = generate_phase3r(args.output.resolve())
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
