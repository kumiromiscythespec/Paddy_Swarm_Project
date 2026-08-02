"""Generate and validate PS-MHT-V001 Phase 3A CAD artifacts."""

from __future__ import annotations

import argparse
import gc
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ps_mht_v001.assembly.port_exploded_phase3a import (
    build_port_exploded_phase3a,
    exploded_component_count,
)
from ps_mht_v001.assembly.port_service_sweeps_phase3a import (
    build_port_service_sweeps_phase3a,
    service_clearance_report,
)
from ps_mht_v001.assembly.root_zone_reference_phase3a import (
    SELECTED_PATTERN,
    compare_root_zone_candidates,
)
from ps_mht_v001.assembly.module_pair_phase2 import (
    key_alignment_intersection_volume,
    m4_axis_alignment_intersection_volume,
    minimum_noninterfering_lift,
    module_pair_interference_volume,
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
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.coupons.angled_port_print_coupon import (
    build_angled_port_print_coupon,
)
from ps_mht_v001.coupons.gasket_compression_leak_coupon import (
    COUPON_SOLID_COUNT as GASKET_COUPON_SOLIDS,
    GROOVE_DEPTHS,
    PRIMARY_GASKET,
    TEST_MODE,
    build_gasket_compression_leak_coupon,
)
from ps_mht_v001.coupons.index_key_fit_coupon import (
    COUPON_SOLID_COUNT as KEY_COUPON_SOLIDS,
    KEY_CLEARANCES,
    build_index_key_fit_coupon,
)
from ps_mht_v001.coupons.m4_cartridge_fit_coupon import (
    CARTRIDGE_CLEARANCES,
    COUPON_SOLID_COUNT as M4_COUPON_SOLIDS,
    build_m4_cartridge_fit_coupon,
)
from ps_mht_v001.coupons.netpot_adapter_coupon import (
    COUPON_SOLID_COUNT as NETPOT_COUPON_SOLIDS,
    NETPOT_CLEARANCES,
    build_netpot_adapter_coupon,
)
from ps_mht_v001.coupons.port_receiver_adapter_coupon import (
    ADAPTER_CLEARANCES,
    COUPON_SOLID_COUNT as RECEIVER_COUPON_SOLIDS,
    build_port_receiver_adapter_coupon,
)
from ps_mht_v001.parameters import (
    ASSUMPTION,
    CALIBRATION_ITEMS,
    CALIBRATION_PENDING,
    available_fastener_angles,
    m3_fastener_pitch_radius,
    netpot_body_bottom_outer_diameter,
    netpot_body_height,
    netpot_body_top_outer_diameter,
    netpot_fit_clearance,
    netpot_flange_outer_diameter,
    netpot_flange_thickness,
    netpot_insertion_clearance,
    netpot_lip_height,
    netpot_nominal_size,
    netpot_slot_count,
    netpot_slot_width,
    netpot_taper_angle,
    plant_port_angle,
    plant_port_center_z,
    plant_port_local_angles,
    port_adapter_fit_clearance,
    port_receiver_bore_diameter,
    port_saddle_blend_radius_target,
    port_service_sweep_length,
    selected_port_z_offset_pattern,
    tower_max_diameter,
    validate_parameters,
)
from ps_mht_v001.tower_module.blank_port_cap import build_blank_port_cap
from ps_mht_v001.tower_module.module_interface import (
    m4_boss_nominal_radial_wall,
)
from ps_mht_v001.tower_module.netpot_60_adapter import (
    build_netpot_60_adapter,
)
from ps_mht_v001.tower_module.netpot_reference import (
    NETPOT_REFERENCE_SOLID_COUNT_WITH_AXIS,
    REFERENCE_STATUS,
    build_netpot_reference_with_axis,
)
from ps_mht_v001.tower_module.planting_port import (
    DO_NOT_PRINT_STATUS,
    SELECTED_SADDLE_CONCEPT,
    build_continuous_shell_band_probe,
    build_m3_wall_probe_local,
    build_phase3a_m4_wall_probe,
    build_planting_module_with_ports_phase3a,
    build_planting_port_receiver,
    build_port_root_wall_probe_local,
    containment_ratio,
    directional_max_radius,
    maximum_radial_radius,
    port_center_heights,
    receiver_outward_radius_formula,
    receiver_pair_intersection_volumes,
    rotated_port_angles,
)
from ps_mht_v001.tower_module.planting_port_adapter import (
    build_planting_port_adapter,
    m3_nominal_surrounding_wall,
)
from ps_mht_v001.tower_module.port_adapter_gasket import (
    build_port_adapter_gasket,
)
from ps_mht_v001.tower_module.port_adapter_retainer import (
    build_port_adapter_retainer,
)
from ps_mht_v001.tower_module.root_sleeve_reference import (
    ROOT_REFERENCE_SOLID_COUNT,
    build_collapsed_root_sleeve_reference,
    build_expanded_root_sleeve_reference,
    expanded_root_overlap_volumes,
    expanded_root_volumes_liters,
)
from ps_mht_v001.tower_module.root_sleeve_retaining_ring import (
    build_root_sleeve_retaining_ring,
)
from ps_mht_v001.tower_module.root_stop_insert import build_root_stop_insert


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"


def _validation_subprocess(
    kind: str,
    path: Path,
    expected_solid_count: int = 1,
    printable: bool = False,
) -> dict[str, object]:
    """Isolate each OCCT/VTK re-read so native state cannot accumulate."""

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


def _export_printable(
    key: str,
    model,
    solid_count: int,
    step_dir: Path,
    stl_dir: Path,
) -> dict[str, Path]:
    stem = f"ps_mht_v001_{key}_phase3a"
    step_path = step_dir / f"{stem}.step"
    stl_path = stl_dir / f"{stem}.stl"
    if solid_count == 1:
        export_printable_step(model, step_path)
        export_printable_stl(model, stl_path)
    else:
        export_printable_set_step(model, step_path, solid_count)
        export_printable_set_stl(model, stl_path, solid_count)
    return {"step": step_path, "stl": stl_path}


def _make_delivery_zip(output_root: Path, zip_path: Path) -> Path:
    """Package source/docs/tests and Phase 3A outputs without caches."""

    excluded_parts = {"__pycache__", ".pytest_cache"}
    allowed_source_suffixes = {".py", ".md"}
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_ROOT.rglob("*")):
            if not path.is_file() or path == zip_path:
                continue
            relative = path.relative_to(PACKAGE_ROOT)
            if any(part in excluded_parts for part in relative.parts):
                continue
            if path.suffix.lower() in {".pyc", ".pyo", ".pyd"}:
                continue
            is_source = (
                path.suffix.lower() in allowed_source_suffixes
                or relative.as_posix() == ".gitignore"
            )
            is_phase3_output = (
                relative.parts
                and relative.parts[0] == "exports"
                and (
                    "phase3a" in path.name.lower()
                    or path.name == "phase3a_validation_report.json"
                )
            )
            if is_source or is_phase3_output:
                archive.write(path, f"ps_mht_v001/{relative.as_posix()}")
    return zip_path


def generate_phase3a(output_root: Path) -> dict[str, object]:
    """Build, export, re-import, mesh-check, and report Phase 3A."""

    validate_parameters()
    baseline_before = audit_baseline_hashes(output_root)
    if not all(item["unchanged"] for item in baseline_before.values()):
        raise RuntimeError("Phase 1/2 baseline hash changed before Phase 3A build")

    step_dir = output_root / "step"
    stl_dir = output_root / "stl"
    preview_dir = output_root / "preview"
    module = build_planting_module_with_ports_phase3a()
    receiver = build_planting_port_receiver()
    receiver_metrics = measure_shape(receiver)

    printable_models = {
        "three_port_module_DO_NOT_PRINT_UNTIL_CALIBRATION": (module, 1),
        "planting_port": (receiver, 1),
        "planting_port_adapter": (build_planting_port_adapter(), 1),
        "netpot_60_adapter": (build_netpot_60_adapter(), 1),
        "blank_port_cap": (build_blank_port_cap(), 1),
        "port_adapter_gasket": (build_port_adapter_gasket(), 1),
        "port_adapter_retainer": (build_port_adapter_retainer(), 1),
        "root_sleeve_retaining_ring": (
            build_root_sleeve_retaining_ring(),
            1,
        ),
        "root_stop_insert": (build_root_stop_insert(), 1),
        "index_key_fit_coupon": (
            build_index_key_fit_coupon(),
            KEY_COUPON_SOLIDS,
        ),
        "m4_cartridge_fit_coupon": (
            build_m4_cartridge_fit_coupon(),
            M4_COUPON_SOLIDS,
        ),
        "gasket_compression_leak_coupon": (
            build_gasket_compression_leak_coupon(),
            GASKET_COUPON_SOLIDS,
        ),
        "netpot_adapter_coupon": (
            build_netpot_adapter_coupon(),
            NETPOT_COUPON_SOLIDS,
        ),
        "port_receiver_adapter_coupon": (
            build_port_receiver_adapter_coupon(),
            RECEIVER_COUPON_SOLIDS,
        ),
        "angled_port_print_coupon": (
            build_angled_port_print_coupon(),
            1,
        ),
    }
    printable_paths = {
        key: _export_printable(
            key,
            model,
            solid_count,
            step_dir,
            stl_dir,
        )
        for key, (model, solid_count) in printable_models.items()
    }

    reference_models = {
        "netpot_reference_PURCHASED_PART": (
            build_netpot_reference_with_axis(),
            NETPOT_REFERENCE_SOLID_COUNT_WITH_AXIS,
        ),
        "root_sleeve_expanded_reference_PURCHASED_PART": (
            build_expanded_root_sleeve_reference(),
            ROOT_REFERENCE_SOLID_COUNT,
        ),
        "root_sleeve_collapsed_reference_PURCHASED_PART": (
            build_collapsed_root_sleeve_reference(),
            ROOT_REFERENCE_SOLID_COUNT,
        ),
        "port_exploded": (
            build_port_exploded_phase3a(),
            exploded_component_count(),
        ),
        "port_service_sweeps": (
            build_port_service_sweeps_phase3a(),
            42,
        ),
    }
    reference_paths = {
        key: export_reference_step(
            model,
            step_dir / f"ps_mht_v001_{key}_phase3a.step",
            solid_count,
        )
        for key, (model, solid_count) in reference_models.items()
    }
    printable_counts = {
        key: solid_count
        for key, (_, solid_count) in printable_models.items()
    }
    reference_counts = {
        key: solid_count
        for key, (_, solid_count) in reference_models.items()
    }
    del reference_models
    # Keep the cached module and receiver references, but release coupon and
    # assembly containers before native STEP/VTK audits.
    del printable_models
    gc.collect()

    preview_paths = {
        "front": export_svg_preview(
            module,
            preview_dir / "ps_mht_v001_three_port_module_front_phase3a.svg",
            (0.0, -1.0, 0.0),
        ),
        "isometric": export_svg_preview(
            module,
            preview_dir / "ps_mht_v001_three_port_module_isometric_phase3a.svg",
            (1.0, -1.0, 0.75),
        ),
    }

    step_round_trip: dict[str, dict[str, object]] = {}
    stl_mesh: dict[str, dict[str, object]] = {}
    for key, solid_count in printable_counts.items():
        step_round_trip[key] = _validation_subprocess(
            "step",
            printable_paths[key]["step"],
            solid_count,
            printable=solid_count == 1,
        )
        stl_mesh[key] = _validation_subprocess(
            "stl",
            printable_paths[key]["stl"],
        )
    for key, solid_count in reference_counts.items():
        step_round_trip[key] = _validation_subprocess(
            "step",
            reference_paths[key],
            solid_count,
        )

    root_wall_ratio = containment_ratio(
        receiver,
        build_port_root_wall_probe_local(),
    )
    m3_wall_ratios = tuple(
        containment_ratio(receiver, build_m3_wall_probe_local(y))
        for y in (-m3_fastener_pitch_radius, m3_fastener_pitch_radius)
    )
    m4_wall_ratios = tuple(
        containment_ratio(module, build_phase3a_m4_wall_probe(angle))
        for angle in available_fastener_angles
    )
    shell_band_ratios = {
        f"z{int(z)}": containment_ratio(
            module,
            build_continuous_shell_band_probe(z),
        )
        for z in (25.0, 143.0)
    }
    maximum_radius = maximum_radial_radius(module)
    baseline_after = audit_baseline_hashes(output_root)
    if not all(item["unchanged"] for item in baseline_after.values()):
        raise RuntimeError("Phase 1/2 baseline hash changed during Phase 3A build")

    report: dict[str, object] = {
        "model": "PS-MHT-V001",
        "phase": "3A",
        "status": "PASS",
        "full_module_status": DO_NOT_PRINT_STATUS,
        "baseline_hash_audit": baseline_after,
        "phase2_reinforcement": {
            "valid_rotations_degree": (0.0, 60.0),
            "invalid_rotations_degree": (30.0, 90.0),
            "interference_30deg_mm3":
                module_pair_interference_volume(30.0),
            "required_lift_30deg_mm": minimum_noninterfering_lift(30.0),
            "key_alignment_0deg_mm3":
                key_alignment_intersection_volume(0.0),
            "key_alignment_60deg_mm3":
                key_alignment_intersection_volume(60.0),
            "key_alignment_30deg_mm3":
                key_alignment_intersection_volume(30.0),
            "m4_alignment_0deg_mm3":
                m4_axis_alignment_intersection_volume(0.0),
            "m4_alignment_60deg_mm3":
                m4_axis_alignment_intersection_volume(60.0),
            "m4_alignment_30deg_mm3":
                m4_axis_alignment_intersection_volume(30.0),
            "phase2_m4_nominal_wall_mm": m4_boss_nominal_radial_wall(),
        },
        "planting_module": {
            "metrics": measure_shape(module).as_dict(),
            "physical_port_count": 3,
            "local_angles_degree": plant_port_local_angles,
            "odd_module_angles_degree": rotated_port_angles(0.0),
            "even_module_angles_degree": rotated_port_angles(60.0),
            "axis_up_angle_degree": plant_port_angle,
            "center_heights_mm": port_center_heights("A"),
            "selected_z_pattern": selected_port_z_offset_pattern,
            "analytic_receiver_outward_radius_mm":
                receiver_outward_radius_formula(),
            "directional_max_radius_mm": {
                f"{int(angle):03d}deg": directional_max_radius(module, angle)
                for angle in plant_port_local_angles
            },
            "actual_maximum_radial_radius_mm": maximum_radius,
            "actual_maximum_diameter_mm": 2.0 * maximum_radius,
            "allowed_maximum_diameter_mm": tower_max_diameter,
            "saddle_pair_intersection_mm3":
                receiver_pair_intersection_volumes(),
        },
        "wall_validation": {
            "receiver_metrics": receiver_metrics.as_dict(),
            "actual_port_root_required_mm": 4.0,
            "actual_port_root_probe_containment_ratio": root_wall_ratio,
            "actual_m3_target_mm": 5.0,
            "actual_m3_probe_containment_ratio": m3_wall_ratios,
            "m3_nominal_surrounding_wall_mm":
                m3_nominal_surrounding_wall(),
            "actual_phase3a_m4_required_mm": 6.0,
            "actual_phase3a_m4_probe_containment_ratio": m4_wall_ratios,
            "continuous_shell_band_containment_ratio": shell_band_ratios,
        },
        "netpot_assumptions": {
            "status": CALIBRATION_PENDING,
            "source": ASSUMPTION,
            "reference_status": REFERENCE_STATUS,
            "nominal_size_mm": netpot_nominal_size,
            "flange_outer_diameter_mm": netpot_flange_outer_diameter,
            "body_top_outer_diameter_mm":
                netpot_body_top_outer_diameter,
            "body_bottom_outer_diameter_mm":
                netpot_body_bottom_outer_diameter,
            "body_height_mm": netpot_body_height,
            "flange_thickness_mm": netpot_flange_thickness,
            "lip_height_mm": netpot_lip_height,
            "taper_angle_degree": netpot_taper_angle,
            "slot_width_mm": netpot_slot_width,
            "slot_count": netpot_slot_count,
            "fit_clearance_per_side_mm": netpot_fit_clearance,
            "insertion_clearance_mm": netpot_insertion_clearance,
        },
        "adapter": {
            "tower_common_receiver_bore_mm": port_receiver_bore_diameter,
            "common_adapter_fit_clearance_per_side_mm":
                port_adapter_fit_clearance,
            "retention": "TWO_M3_BOLTS_AND_REPLACEABLE_METAL_NUT_RETAINER",
            "anti_rotation": "SINGLE_ASYMMETRIC_KEY",
            "blank_cap_same_receiver": True,
            "m3_hardware_status": CALIBRATION_PENDING,
        },
        "saddle_decision": {
            "selected": SELECTED_SADDLE_CONCEPT,
            "blend_radius_target_mm": port_saddle_blend_radius_target,
            "integrated_A": {
                "support": "short vertical-print bridge; coupon required",
                "part_count": 0,
                "root_strength": "best continuous load path",
                "cleaning": "open through-bore, no sealed cavity",
                "maximum_diameter": "PASS",
                "material": "higher than opening-only shell",
                "risk": "angled underside quality calibration pending",
            },
            "separate_B": {
                "support": "separate part can print flat",
                "part_count": 3,
                "root_strength": "depends on M3 clamp/load transfer",
                "cleaning": "additional crevice",
                "maximum_diameter": "PASS",
                "material": "lower module, more hardware",
                "risk": "assembly and leak-path risk",
            },
        },
        "root_zone": {
            "selected_pattern": SELECTED_PATTERN,
            "expanded_volume_liter": expanded_root_volumes_liters(),
            "pair_overlap_mm3": expanded_root_overlap_volumes(),
            "candidate_comparison": compare_root_zone_candidates(),
            "primary_mesh": "PURCHASED_PP_OR_PE_FLEXIBLE_MESH",
            "printed_mesh_used": False,
        },
        "service_sweeps": {
            "outward_length_mm": port_service_sweep_length,
            "rotation_0deg": service_clearance_report(0.0),
            "rotation_60deg": service_clearance_report(60.0),
            "phase3a_main_hose_corridor": {
                "center_xy_mm": (0.0, 60.0),
                "status": "ASSUMPTION_PHASE5_PENDING",
                "reason":
                    "Phase 2 external (28,130) zone conflicts with 60-degree extraction",
            },
        },
        "coupons": {
            "index_key_fit_clearance_mm": KEY_CLEARANCES,
            "m4_cartridge_fit_clearance_mm": CARTRIDGE_CLEARANCES,
            "gasket_groove_depth_mm": GROOVE_DEPTHS,
            "gasket_test_mode": TEST_MODE,
            "gasket_primary_candidate": PRIMARY_GASKET,
            "netpot_clearance_mm": NETPOT_CLEARANCES,
            "receiver_adapter_clearance_mm": ADAPTER_CLEARANCES,
            "angled_port_real_shell_section": True,
        },
        "automated_tests": {
            "phase1_gate_count": 13,
            "pre_phase3_total_count": 41,
            "phase3a_new_test_count": 45,
            "total_count": 86,
            "expected_status_after_generation": "PASS",
        },
        "step_round_trip": step_round_trip,
        "stl_mesh": stl_mesh,
        "calibration_pending": {
            key: value
            for key, value in CALIBRATION_ITEMS.items()
            if value["status"] == CALIBRATION_PENDING
        },
        "recommended_print_order": (
            "index_key_fit_coupon",
            "m4_cartridge_fit_coupon",
            "gasket_compression_leak_coupon",
            "netpot_adapter_coupon",
            "port_receiver_adapter_coupon",
            "angled_port_print_coupon",
        ),
        "do_not_print": (
            "three_port_module_DO_NOT_PRINT_UNTIL_CALIBRATION",
            "netpot_reference_PURCHASED_PART",
            "root_sleeve_expanded_reference_PURCHASED_PART",
            "root_sleeve_collapsed_reference_PURCHASED_PART",
            "port_service_sweeps",
        ),
    }

    report_path = preview_dir / "phase3a_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    export_list = sorted(
        [
            str(path.relative_to(output_root).as_posix())
            for paths in printable_paths.values()
            for path in paths.values()
        ]
        + [
            str(path.relative_to(output_root).as_posix())
            for path in reference_paths.values()
        ]
        + [
            str(path.relative_to(output_root).as_posix())
            for path in preview_paths.values()
        ]
        + ["preview/phase3a_validation_report.json"]
    )
    report["exports"] = export_list
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    zip_path = output_root / "ps_mht_v001_phase3a_delivery.zip"
    _make_delivery_zip(output_root, zip_path)
    report["delivery_zip"] = str(zip_path.relative_to(output_root).as_posix())
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    # Rebuild once so the ZIP contains the final report including its own name.
    _make_delivery_zip(output_root, zip_path)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"artifact root (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    generate_phase3a(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
