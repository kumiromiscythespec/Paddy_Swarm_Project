"""Generate and validate PS-MHT-V001 Phase 3S-A artifacts."""

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

from ps_mht_v001.assembly.sector_print_orientation_phase3sa import (
    COORDINATE_TRANSFORM,
    orient_sector_for_print_phase3sa,
    print_stability_metrics_phase3sa,
)
from ps_mht_v001.assembly.three_sector_full_height_reference_phase3sa import (
    STATUS as FULL_REFERENCE_STATUS,
    build_three_sector_full_height_reference_phase3sa,
    full_height_panel_models_phase3sa,
    full_height_reference_component_policy_phase3sa,
)
from ps_mht_v001.assembly.three_sector_short_assembly_phase3sa import (
    STATUS as SHORT_ASSEMBLY_STATUS,
    build_three_sector_short_assembly_phase3sa,
    build_three_sector_short_exploded_phase3sa,
    short_assembly_components_phase3sa,
)
from ps_mht_v001.common.phase3sa_nonregression import (
    audit_phase1_through_phase3r1,
    phase3r2_generated_artifacts,
)
from ps_mht_v001.common.validation import (
    export_printable_set_step,
    export_printable_set_stl,
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    export_svg_preview,
    measure_shape,
)
from ps_mht_v001.coupons.panel_capture_ring_coupon_phase3sa import (
    build_panel_capture_ring_coupon_phase3sa,
)
from ps_mht_v001.coupons.sector_seam_pair_coupon_phase3sa import (
    IDENTIFICATION,
    TEST_PROTOCOL,
    build_sector_seam_pair_coupon_phase3sa,
)
from ps_mht_v001.parameters import (
    CALIBRATION_PENDING,
    netpot_siawadeky_body_diameter_pending,
    netpot_siawadeky_flange_diameter_assumed,
    netpot_siawadeky_height_assumed,
    phase3sa_chord_length,
    phase3sa_max_print_overhang,
    phase3sa_panel_capture_depth,
    phase3sa_panel_height,
    phase3sa_port_axis_angle,
    phase3sa_print_height_audit_limit,
    phase3sa_print_height_target,
    phase3sa_sagitta,
    phase3sa_seam_clearance_candidates,
    phase3sa_seam_clearance_selected,
    phase3sa_seam_overlap,
    phase3sa_seam_rail_min_contact_area,
    phase3sa_seam_rail_target_contact_area,
    phase3sa_seam_rail_width,
    phase3sa_seam_root_radius,
    phase3sa_seam_root_thickness,
    phase3sa_sector_angle_deg,
    phase3sa_sector_count,
    phase3sa_shell_outer_radius,
    phase3sa_shell_wall,
    phase3sa_short_panel_height,
    phase3sa_temporary_ring_clearance,
    phase3sa_water_return_height,
    phase3sa_water_return_thickness,
    print_bed_x,
    print_bed_y,
    print_bed_z,
    tower_max_diameter,
)
from ps_mht_v001.print_plate_layout_phase3sa import (
    PART_SPACING_MM,
    SELECTED_PRECALIBRATION_CANDIDATE_MM,
    phase3sa_individual_plates,
)
from ps_mht_v001.tower_module.planting_port import maximum_radial_radius
from ps_mht_v001.tower_module.sector_panel_phase3sa import (
    END_DATUM_POLICY,
    IMPLEMENTED_DRAIN_OR_IRRIGATION_FEATURES,
    IMPLEMENTED_HARDWARE,
    IMPLEMENTED_SMALL_PART_COUNT,
    REFERENCE_DRAIN_ZONE,
    build_sector_panel_phase3sa,
)
from ps_mht_v001.tower_module.sector_port_opening_phase3sa import (
    NETPOT_FINAL_FIT,
    ROUNDNESS_OWNER,
    port_printability_phase3sa,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    FORBIDDEN_FEATURES,
    LEAD_CHAMFER_MM,
    RAIL_CHORD_PLANE_X,
    SEAM_POLICY,
    WATERTIGHTNESS,
    rail_contact_area_phase3sa,
    seam_has_direct_radial_sightline_phase3sa,
)
from ps_mht_v001.tower_module.temporary_capture_ring_phase3sa import (
    REFERENCE_EXTERNAL_BAND,
    build_temporary_panel_capture_ring_phase3sa,
    capture_ring_dimensions_phase3sa,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"
EXISTING_TEST_COUNT = 176
PHASE3SA_TEST_COUNT = 52
EXPECTED_TEST_COUNT = EXISTING_TEST_COUNT + PHASE3SA_TEST_COUNT


def _validation_subprocess(
    kind: str,
    path: Path,
    expected_solid_count: int = 1,
) -> dict[str, object]:
    script = (
        "import json,sys;"
        "from pathlib import Path;"
        "from ps_mht_v001.common.validation import "
        "validate_step_round_trip,validate_stl_mesh;"
        "p=Path(sys.argv[2]);"
        "m=(validate_step_round_trip(p,int(sys.argv[3])) "
        "if sys.argv[1]=='step' else validate_stl_mesh(p));"
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
        ],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    if result.returncode:
        raise RuntimeError(
            f"{kind} validation failed for {path.name}:\n{result.stderr}"
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
        if test_path.name.startswith(
            ("test_phase3sa1_", "test_phase3sa2_", "test_phase3pa_")
        ):
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
        "preserved_phase1_through_phase3r1": EXISTING_TEST_COUNT,
        "new_phase3sa": PHASE3SA_TEST_COUNT,
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
) -> tuple[Path, Path]:
    step_path = step_dir / f"{stem}.step"
    stl_path = stl_dir / f"{stem}.stl"
    if solid_count == 1:
        export_printable_step(model, step_path)
        export_printable_stl(model, stl_path)
    else:
        export_printable_set_step(model, step_path, solid_count)
        export_printable_set_stl(model, stl_path, solid_count)
    return step_path, stl_path


def _pairwise_intersections(
    models: tuple[cq.Workplane, ...],
) -> dict[str, float]:
    result: dict[str, float] = {}
    for first in range(len(models)):
        for second in range(first + 1, len(models)):
            result[f"{first + 1}-{second + 1}"] = sum(
                solid.Volume()
                for solid in models[first]
                .intersect(models[second])
                .solids()
                .vals()
            )
    return result


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


def generate_phase3sa(output_root: Path) -> dict[str, object]:
    step_dir = output_root / "step"
    stl_dir = output_root / "stl"
    preview_dir = output_root / "preview"
    step_dir.mkdir(parents=True, exist_ok=True)
    stl_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    baseline_before = audit_phase1_through_phase3r1(output_root)
    if not all(item["unchanged"] for item in baseline_before.values()):
        raise RuntimeError("Phase 1 through Phase 3R.1 baseline changed")
    if phase3r2_generated_artifacts(output_root):
        raise RuntimeError("Phase 3R.2 must not have generated artifacts")

    generated: list[Path] = []
    expected_steps: dict[Path, int] = {}
    expected_stls: dict[Path, int] = {}
    shape_metrics: dict[str, dict[str, object]] = {}

    for clearance in phase3sa_seam_clearance_candidates:
        token = f"{int(round(clearance * 100)):03d}"
        stem = f"ps_mht_v001_sector_seam_coupon_c{token}_phase3sa"
        model = build_sector_seam_pair_coupon_phase3sa(clearance)
        step_path, stl_path = _export_pair(
            model,
            stem,
            step_dir,
            stl_dir,
            2,
        )
        shape_metrics[stem] = measure_shape(model).as_dict()
        generated.extend((step_path, stl_path))
        expected_steps[step_path] = 2
        expected_stls[stl_path] = 2

    panel = build_sector_panel_phase3sa(
        SELECTED_PRECALIBRATION_CANDIDATE_MM
    )
    panel_stem = "ps_mht_v001_sector_panel_single_phase3sa"
    panel_step, panel_stl = _export_pair(
        panel,
        panel_stem,
        step_dir,
        stl_dir,
        1,
    )
    shape_metrics[panel_stem] = measure_shape(panel).as_dict()
    generated.extend((panel_step, panel_stl))
    expected_steps[panel_step] = 1
    expected_stls[panel_stl] = 1

    printed_panel = orient_sector_for_print_phase3sa(panel)
    print_stem = (
        "ps_mht_v001_sector_panel_single_print_orientation_phase3sa"
    )
    print_stl = stl_dir / f"{print_stem}.stl"
    export_printable_stl(printed_panel, print_stl)
    shape_metrics[print_stem] = measure_shape(printed_panel).as_dict()
    generated.append(print_stl)
    expected_stls[print_stl] = 1

    ring = build_temporary_panel_capture_ring_phase3sa()
    ring_stem = "ps_mht_v001_temporary_panel_capture_ring_phase3sa"
    ring_step, ring_stl = _export_pair(
        ring,
        ring_stem,
        step_dir,
        stl_dir,
        1,
    )
    shape_metrics[ring_stem] = measure_shape(ring).as_dict()
    generated.extend((ring_step, ring_stl))
    expected_steps[ring_step] = 1
    expected_stls[ring_stl] = 1

    capture_coupon = build_panel_capture_ring_coupon_phase3sa()
    capture_stem = "ps_mht_v001_panel_capture_ring_coupon_phase3sa"
    capture_step, capture_stl = _export_pair(
        capture_coupon,
        capture_stem,
        step_dir,
        stl_dir,
        2,
    )
    shape_metrics[capture_stem] = measure_shape(
        capture_coupon
    ).as_dict()
    generated.extend((capture_step, capture_stl))
    expected_steps[capture_step] = 2
    expected_stls[capture_stl] = 2

    short_assembly = build_three_sector_short_assembly_phase3sa(
        SELECTED_PRECALIBRATION_CANDIDATE_MM
    )
    full_reference = build_three_sector_full_height_reference_phase3sa(
        SELECTED_PRECALIBRATION_CANDIDATE_MM
    )
    exploded = build_three_sector_short_exploded_phase3sa(
        SELECTED_PRECALIBRATION_CANDIDATE_MM
    )
    references = (
        (
            "ps_mht_v001_three_sector_short_assembly_phase3sa",
            short_assembly,
        ),
        (
            "ps_mht_v001_three_sector_full_height_reference_phase3sa",
            full_reference,
        ),
        (
            "ps_mht_v001_three_sector_exploded_phase3sa",
            exploded,
        ),
    )
    for stem, model in references:
        path = step_dir / f"{stem}.step"
        export_reference_step(model, path, 6)
        shape_metrics[stem] = measure_shape(model).as_dict()
        generated.append(path)
        expected_steps[path] = 6

    plate_metrics: dict[str, dict[str, object]] = {}
    for name, model, solid_count in phase3sa_individual_plates():
        path = stl_dir / f"{name}.stl"
        export_printable_set_stl(model, path, solid_count)
        metrics = measure_shape(model).as_dict()
        plate_metrics[name] = {
            **metrics,
            "part_spacing_minimum_mm": PART_SPACING_MM,
            "a1_within_245x245x240": True,
        }
        generated.append(path)
        expected_stls[path] = solid_count

    section_model = full_reference.intersect(
        cq.Workplane("XY")
        .box(300.0, 150.0, 220.0)
        .translate((0.0, -75.0, 88.0))
    )
    section_path = preview_dir / "ps_mht_v001_phase3sa_section.svg"
    iso_path = preview_dir / "ps_mht_v001_phase3sa_isometric.svg"
    export_svg_preview(section_model, section_path, (0.0, -1.0, 0.0))
    export_svg_preview(full_reference, iso_path, (1.0, -1.0, 0.75))
    generated.extend((section_path, iso_path))

    step_validation = {
        path.name: _validation_subprocess("step", path, count)
        for path, count in expected_steps.items()
    }
    stl_validation = {
        path.name: _validation_subprocess("stl", path)
        for path in expected_stls
    }
    for path, expected_components in expected_stls.items():
        actual_components = stl_validation[path.name][
            "connected_component_count"
        ]
        if actual_components != expected_components:
            raise RuntimeError(
                f"{path.name}: expected {expected_components} STL "
                f"components, got {actual_components}"
            )

    stability = print_stability_metrics_phase3sa(panel)
    if stability["size_z_mm"] > phase3sa_print_height_audit_limit:
        raise RuntimeError("full panel exceeds 110 mm print-height stop gate")
    panels = full_height_panel_models_phase3sa(
        SELECTED_PRECALIBRATION_CANDIDATE_MM
    )
    panel_intersections = _pairwise_intersections(panels)
    if any(value > 1.0e-7 for value in panel_intersections.values()):
        raise RuntimeError("three panel instances have prohibited overlap")

    short_diameter = 2.0 * maximum_radial_radius(short_assembly)
    full_diameter = 2.0 * maximum_radial_radius(full_reference)
    if max(short_diameter, full_diameter) > tower_max_diameter:
        raise RuntimeError("Phase 3S-A assembly exceeds 240 mm diameter")

    test_results = _run_tests_isolated()
    baseline_after = audit_phase1_through_phase3r1(output_root)
    if not all(item["unchanged"] for item in baseline_after.values()):
        raise RuntimeError("Phase 1 through Phase 3R.1 baseline changed")

    report: dict[str, object] = {
        "project": "PS-MHT-V001",
        "phase": "3S-A",
        "status": "PHASE3SA_CAD_COMPLETE_PHYSICAL_CALIBRATION_PENDING",
        "scope": "PRINTABILITY_SEAM_AND_CIRCULARITY_CALIBRATION_ONLY",
        "start_audit": {
            "repository_root": str(PACKAGE_ROOT.parents[1]),
            "cadquery_version": cq.__version__,
            "existing_test_count": EXISTING_TEST_COUNT,
            "module_nominal_mm": {
                "diameter": 2.0 * phase3sa_shell_outer_radius,
                "height": phase3sa_panel_height,
            },
            "a1_envelope_mm": [print_bed_x, print_bed_y, print_bed_z],
            "phase3r2_status": "ABORTED_BY_REQUIREMENT_CONFLICT",
            "phase3r2_superseded_by":
                "PHASE_3S_THREE_SECTOR_SPLIT_SHELL",
        },
        "non_regression": {
            "baseline_before": baseline_before,
            "baseline_after": baseline_after,
            "all_unchanged": all(
                item["unchanged"] for item in baseline_after.values()
            ),
            "phase3r2_generated_artifacts":
                list(phase3r2_generated_artifacts(output_root)),
        },
        "integrated_cylinder_retirement": {
            "inherited": True,
            "phase3r2_status": "ABORTED_BY_REQUIREMENT_CONFLICT",
            "replacement": "THREE_IDENTICAL_120_DEGREE_SECTORS",
        },
        "sector_panel": {
            "count": phase3sa_sector_count,
            "angle_deg": phase3sa_sector_angle_deg,
            "assembled_degrees": (
                phase3sa_sector_count * phase3sa_sector_angle_deg
            ),
            "height_mm": phase3sa_panel_height,
            "outer_radius_mm": phase3sa_shell_outer_radius,
            "wall_mm": phase3sa_shell_wall,
            "chord_length_mm": phase3sa_chord_length,
            "sagitta_mm": phase3sa_sagitta,
            "port_count_each": 1,
            "component_count": 1,
            "identical_source_policy":
                full_height_reference_component_policy_phase3sa(),
        },
        "print_orientation": {
            "coordinate_transform": COORDINATE_TRANSFORM,
            "rail_datum_assembly_x_mm": RAIL_CHORD_PLANE_X,
            "measured_envelope_mm": stability,
            "target_height_mm": phase3sa_print_height_target,
            "stop_audit_height_mm": phase3sa_print_height_audit_limit,
            "support_policy": "SUPPORT_FREE_FIRST_CANDIDATE",
        },
        "contact_rails": {
            "count": 2,
            "width_each_mm": phase3sa_seam_rail_width,
            "continuous_length_each_mm": phase3sa_panel_height,
            "root_radius_mm": phase3sa_seam_root_radius,
            "contact_area_mm2": rail_contact_area_phase3sa(),
            "minimum_mm2": phase3sa_seam_rail_min_contact_area,
            "target_mm2": phase3sa_seam_rail_target_contact_area,
            "target_margin_mm2": (
                rail_contact_area_phase3sa()
                - phase3sa_seam_rail_target_contact_area
            ),
            "old_integrated_coupon_contact_area_mm2": 1856.0,
            "permanent_not_sacrificial": True,
        },
        "stability": {
            "center_projection_inside_support_polygon":
                stability["center_projection_inside_support_polygon"],
            "support_polygon_margin_mm":
                stability["support_polygon_margin_mm"],
            "tip_stability_index": stability["tip_stability_index"],
            "old_integrated_coupon_tip_stability_index": 100.0 / 70.0,
            "improved": stability["tip_stability_index"] > 100.0 / 70.0,
        },
        "vertical_seam": {
            "policy": SEAM_POLICY,
            "overlap_mm": phase3sa_seam_overlap,
            "clearance_candidates_mm":
                list(phase3sa_seam_clearance_candidates),
            "selected_clearance_mm": phase3sa_seam_clearance_selected,
            "export_reference_candidate_mm":
                SELECTED_PRECALIBRATION_CANDIDATE_MM,
            "root_thickness_mm": phase3sa_seam_root_thickness,
            "root_radius_mm": phase3sa_seam_root_radius,
            "lead_chamfer_mm": LEAD_CHAMFER_MM,
            "water_return_height_mm": phase3sa_water_return_height,
            "water_return_thickness_mm":
                phase3sa_water_return_thickness,
            "direct_radial_sightline":
                seam_has_direct_radial_sightline_phase3sa(),
            "watertightness": WATERTIGHTNESS,
            "forbidden_features": list(FORBIDDEN_FEATURES),
            "identification": IDENTIFICATION,
            "physical_test_protocol": TEST_PROTOCOL,
            "panel_pair_intersections_mm3": panel_intersections,
        },
        "planting_port": {
            **port_printability_phase3sa(),
            "roundness_owner": ROUNDNESS_OWNER,
            "netpot_final_fit": NETPOT_FINAL_FIT,
            "siawadeky_confirmed_mm": {
                "flange_maximum": netpot_siawadeky_flange_diameter_assumed,
                "height": netpot_siawadeky_height_assumed,
            },
            "siawadeky_body_diameter": 
                netpot_siawadeky_body_diameter_pending,
        },
        "panel_end_datums": {
            "policy": END_DATUM_POLICY,
            "capture_depth_mm": phase3sa_panel_capture_depth,
            "top_and_bottom_same_section": True,
            "thin_claws": False,
            "closed_water_pocket": False,
        },
        "temporary_capture_ring": {
            **capture_ring_dimensions_phase3sa(),
            "status": CALIBRATION_PENDING,
            "upper_and_lower_same_part": True,
            "final_wave_interface": False,
            "final_m4_nut_system": False,
            "external_band": REFERENCE_EXTERNAL_BAND,
            "temporary_ring_clearance_mm":
                phase3sa_temporary_ring_clearance,
        },
        "short_assembly": {
            "status": SHORT_ASSEMBLY_STATUS,
            "panel_height_mm": phase3sa_short_panel_height,
            "blank_panel_status":
                "COUPON_ONLY_NOT_A_PRODUCTION_PANEL",
            "solid_count": measure_shape(short_assembly).solid_count,
            "maximum_diameter_mm": short_diameter,
        },
        "full_height_reference": {
            "status": FULL_REFERENCE_STATUS,
            "solid_count": measure_shape(full_reference).solid_count,
            "maximum_diameter_mm": full_diameter,
            "panel_mutual_intersections_mm3": panel_intersections,
        },
        "minimum_features": {
            "structural_wall_mm": phase3sa_shell_wall,
            "seam_root_thickness_mm": phase3sa_seam_root_thickness,
            "seam_root_radius_mm": phase3sa_seam_root_radius,
            "port_surround_mm": 4.0,
            "port_root_target": "R4_CLASS_CALIBRATION_PENDING",
        },
        "scope_fences": {
            "small_part_count": IMPLEMENTED_SMALL_PART_COUNT,
            "implemented_hardware": list(IMPLEMENTED_HARDWARE),
            "drain_or_irrigation_features":
                list(IMPLEMENTED_DRAIN_OR_IRRIGATION_FEATURES),
            "drain_zone": REFERENCE_DRAIN_ZONE,
            "full_five_stage_tower": False,
        },
        "automated_tests": test_results,
        "step_round_trip_validation": step_validation,
        "stl_mesh_validation": stl_validation,
        "individual_a1_plates": plate_metrics,
        "recommended_print_order": [
            "plate_01_sector_seam_coupons_phase3sa.stl",
            "plate_02_panel_capture_coupon_phase3sa.stl",
            "plate_03_sector_panel_single_phase3sa.stl",
            "plate_04_three_sector_short_parts_phase3sa.stl",
        ],
        "do_not_print": [
            "ps_mht_v001_three_sector_short_assembly_phase3sa.step",
            "ps_mht_v001_three_sector_full_height_reference_phase3sa.step",
            "ps_mht_v001_three_sector_exploded_phase3sa.step",
            "REFERENCE_EXTERNAL_BAND",
            "FULL_FIVE_STAGE_TOWER",
        ],
        "calibration_pending": [
            "Select 0.4, 0.6, or 0.8 mm vertical-seam clearance.",
            "Verify ten seam assembly cycles without whitening or cracks.",
            "Perform the 500 mL inward drip and direct-outflow test.",
            "Measure temporary-ring fit, lower/upper diameter, and roundness.",
            "Confirm the single full-height panel prints without support.",
            "Measure the delivered Siawadeky body, taper, ribs, and flange.",
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
                "pull_request",
            ],
        },
        "shape_metrics": shape_metrics,
    }

    report_path = preview_dir / "phase3sa_validation_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    generated.append(report_path)

    zip_path = output_root / "ps_mht_v001_phase3sa_delivery.zip"
    _make_delivery_zip(generated, zip_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = generate_phase3sa(args.output.resolve())
    print(
        json.dumps(
            {
                "phase": report["phase"],
                "status": report["status"],
                "tests": report["automated_tests"]["total_passed"],
                "print_height_mm":
                    report["print_orientation"][
                        "measured_envelope_mm"
                    ]["size_z_mm"],
                "full_reference_maximum_diameter_mm":
                    report["full_height_reference"][
                        "maximum_diameter_mm"
                    ],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
