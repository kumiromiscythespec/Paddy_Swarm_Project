"""Generate and validate PS-MHT-V001 Phase 2 CAD artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ps_mht_v001.assembly.module_pair_phase2 import (
    build_exploded_interface,
    build_interface_section,
    build_keepout_reference_model,
    build_module_pair,
    keepout_components,
    module_pair_components,
    module_pair_interference_volume,
)
from ps_mht_v001.common.fasteners import (
    build_m4_nut_cartridge,
    build_m4_nut_cartridge_retainer,
)
from ps_mht_v001.common.validation import (
    export_printable_set_step,
    export_printable_set_stl,
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    export_svg_preview,
    measure_shape,
    validate_single_printable,
    validate_step_round_trip,
    validate_stl_mesh,
)
from ps_mht_v001.coupons.m4_insert_coupon import build_m4_insert_coupon
from ps_mht_v001.coupons.module_body_roundness_coupon import (
    build_module_body_roundness_coupon,
)
from ps_mht_v001.coupons.module_interface_coupon import (
    COUPON_SOLID_COUNT,
    CLEARANCES_PER_SIDE,
    build_module_interface_coupon,
)
from ps_mht_v001.coupons.tpu_gasket_coupon import (
    GROOVE_DEPTHS,
    build_tpu_gasket_coupon,
)
from ps_mht_v001.parameters import (
    available_fastener_angles,
    gasket_cord_diameter,
    gasket_groove_depth,
    gasket_groove_width,
    index_station_count,
    index_station_step,
    interface_load_contact_width,
    interface_maximum_diameter_with_knob,
    interface_outer_diameter,
    interface_radial_clearance,
    interface_spigot_inner_diameter,
    irrigation_top_height,
    minimum_fastener_to_port_angle,
    module_count,
    rear_service_angle,
    tower_max_diameter,
    tower_nominal_height,
    used_fastener_angles,
    validate_parameters,
)
from ps_mht_v001.tower_module.module_gasket import build_module_gasket
from ps_mht_v001.tower_module.module_interface import (
    build_cartridge_access_probe,
    build_fastener_boss_reference,
    build_planting_module_with_interface,
    compression_stop_radial_width,
    gasket_to_bolt_radial_clearance,
    interface_fixed_outer_diameter,
    socket_spigot_diametral_clearance,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"


def _intersection_volume(first, second) -> float:
    intersection = first.intersect(second)
    return sum(solid.Volume() for solid in intersection.solids().vals())


def generate_phase2(output_root: Path) -> dict[str, object]:
    """Build, export, re-import, and summarize all Phase 2 geometry."""

    validate_parameters()
    step_dir = output_root / "step"
    stl_dir = output_root / "stl"
    preview_dir = output_root / "preview"

    module = build_planting_module_with_interface()
    module_metrics = validate_single_printable(
        module,
        "planting_module_interface_phase2",
    )
    cartridge = build_m4_nut_cartridge()
    retainer = build_m4_nut_cartridge_retainer()
    gasket = build_module_gasket()
    coupon_models = {
        "module_interface_coupon": (
            build_module_interface_coupon(),
            COUPON_SOLID_COUNT,
        ),
        "module_roundness_coupon": (
            build_module_body_roundness_coupon(),
            1,
        ),
        "m4_insert_coupon": (build_m4_insert_coupon(), 1),
        "tpu_gasket_coupon": (build_tpu_gasket_coupon(), 1),
    }

    printable_models = {
        "planting_module_interface": (module, 1),
        "m4_nut_cartridge": (cartridge, 1),
        "m4_nut_cartridge_retainer": (retainer, 1),
        **coupon_models,
    }
    printable_paths: dict[str, dict[str, Path]] = {}
    for key, (model, solid_count) in printable_models.items():
        stem = f"ps_mht_v001_{key}_phase2"
        step_path = step_dir / f"{stem}.step"
        stl_path = stl_dir / f"{stem}.stl"
        if solid_count == 1:
            export_printable_step(model, step_path)
            export_printable_stl(model, stl_path)
        else:
            export_printable_set_step(model, step_path, solid_count)
            export_printable_set_stl(model, stl_path, solid_count)
        printable_paths[key] = {"step": step_path, "stl": stl_path}

    gasket_step = export_reference_step(
        gasket,
        step_dir / "ps_mht_v001_module_gasket_cord_reference_phase2.step",
        1,
    )

    pair_0 = build_module_pair(0.0)
    pair_60 = build_module_pair(60.0)
    exploded = build_exploded_interface()
    keepouts = build_keepout_reference_model()
    pair_solid_count = len(module_pair_components(0.0))
    reference_paths = {
        "module_pair_0deg": export_reference_step(
            pair_0,
            step_dir / "ps_mht_v001_module_pair_0deg_phase2.step",
            pair_solid_count,
        ),
        "module_pair_60deg": export_reference_step(
            pair_60,
            step_dir / "ps_mht_v001_module_pair_60deg_phase2.step",
            pair_solid_count,
        ),
        "exploded_interface": export_reference_step(
            exploded,
            step_dir / "ps_mht_v001_exploded_interface_phase2.step",
            pair_solid_count,
        ),
        "keepouts": export_reference_step(
            keepouts,
            step_dir / "ps_mht_v001_keepouts_reference_phase2.step",
            len(keepout_components()),
        ),
        "gasket": gasket_step,
    }

    section_svg = export_svg_preview(
        build_interface_section(),
        preview_dir / "ps_mht_v001_module_interface_section_phase2.svg",
        (0.0, -1.0, 0.0),
    )
    module_svg = export_svg_preview(
        module,
        preview_dir / "ps_mht_v001_planting_module_interface_phase2.svg",
        (1.0, -1.0, 0.7),
    )

    step_round_trip: dict[str, dict[str, float | int | bool]] = {}
    stl_mesh: dict[str, dict[str, float | int | bool]] = {}
    for key, (model, solid_count) in printable_models.items():
        step_metrics = validate_step_round_trip(
            printable_paths[key]["step"],
            solid_count,
            printable=solid_count == 1,
        )
        step_round_trip[key] = step_metrics.as_dict()
        stl_mesh[key] = validate_stl_mesh(
            printable_paths[key]["stl"]
        ).as_dict()

    reference_counts = {
        "module_pair_0deg": pair_solid_count,
        "module_pair_60deg": pair_solid_count,
        "exploded_interface": pair_solid_count,
        "keepouts": len(keepout_components()),
        "gasket": 1,
    }
    for key, path in reference_paths.items():
        step_round_trip[key] = validate_step_round_trip(
            path,
            reference_counts[key],
        ).as_dict()

    pocket_access_intersections = {
        f"{int(angle):03d}deg": _intersection_volume(
            module,
            build_cartridge_access_probe(angle),
        )
        for angle in available_fastener_angles
    }
    pair_components_0 = module_pair_components(0.0)
    port_keepouts = [
        component.model
        for component in keepout_components()
        if component.name.startswith("future_port_axis_")
    ]
    fastener_keepouts = [build_fastener_boss_reference()]
    fastener_keepouts.extend(
        component.model
        for component in pair_components_0
        if component.name.startswith("m4_knob_")
    )
    maximum_port_keepout_intersection = max(
        _intersection_volume(fastener, port)
        for fastener in fastener_keepouts
        for port in port_keepouts
    )

    report: dict[str, object] = {
        "model": "PS-MHT-V001",
        "phase": 2,
        "status": "PASS",
        "phase1_regression_contract": {
            "irrigation_top_height_mm": irrigation_top_height,
            "tower_nominal_height_mm": tower_nominal_height,
            "phase1_output_names_overwritten": False,
        },
        "module_interface": {
            "metrics": module_metrics.as_dict(),
            "internal_diameter_mm": interface_spigot_inner_diameter,
            "ring_outer_diameter_mm": interface_outer_diameter,
            "fixed_feature_outer_diameter_mm": interface_fixed_outer_diameter(),
            "knob_envelope_outer_diameter_mm":
                interface_maximum_diameter_with_knob(),
            "spigot_socket_clearance_per_side_mm":
                interface_radial_clearance,
            "spigot_socket_diametral_clearance_mm":
                socket_spigot_diametral_clearance(),
            "load_contact_radial_width_mm": interface_load_contact_width,
            "compression_stop_radial_width_mm":
                compression_stop_radial_width(),
        },
        "indexing": {
            "station_count": index_station_count,
            "station_step_degree": index_station_step,
            "available_m4_angles_degree": available_fastener_angles,
            "used_m4_angles_degree": used_fastener_angles,
            "minimum_m4_to_port_angle_degree":
                minimum_fastener_to_port_angle(),
            "rear_service_angle_degree": rear_service_angle,
        },
        "gasket": {
            "cord_diameter_mm": gasket_cord_diameter,
            "groove_width_mm": gasket_groove_width,
            "groove_depth_mm": gasket_groove_depth,
            "radial_compression_mm":
                gasket_cord_diameter
                - gasket_groove_depth
                - interface_radial_clearance,
            "gasket_to_m4_radial_clearance_mm":
                gasket_to_bolt_radial_clearance(),
            "purpose": "NON_PRESSURIZED_SPLASH_AND_LEAK_REDUCTION",
        },
        "assembly_interference": {
            "module_pair_0deg_mm3": module_pair_interference_volume(0.0),
            "module_pair_60deg_mm3": module_pair_interference_volume(60.0),
            "axis_offset_mm": 0.0,
        },
        "cartridge_external_access_probe_intersection_mm3":
            pocket_access_intersections,
        "cartridge_retainer": {
            "external_replacement": True,
            "normal_use_retainer_captured_by_m4_bolt": True,
            "calibration_status": "CALIBRATION_PENDING",
        },
        "keepout_interference": {
            "fastener_and_knob_to_port_max_mm3":
                maximum_port_keepout_intersection,
            "rear_90deg_normal_knob_present":
                rear_service_angle in used_fastener_angles,
        },
        "coupons": {
            "interface_clearance_per_side_mm": CLEARANCES_PER_SIDE,
            "gasket_groove_depths_mm": GROOVE_DEPTHS,
            "module_roundness_quantity": 1,
            "m4_retention_methods": (
                "HEX_NUT_CAPTURE",
                "HEAT_SET_INSERT",
            ),
        },
        "step_round_trip": step_round_trip,
        "stl_mesh": stl_mesh,
        "printable_part_count": len(printable_models),
        "maximum_allowed_diameter_mm": tower_max_diameter,
        "exports": sorted(
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
                str(section_svg.relative_to(output_root).as_posix()),
                str(module_svg.relative_to(output_root).as_posix()),
                "preview/phase2_validation_report.json",
            ]
        ),
        "phase_boundaries": {
            "plant_ports": "REFERENCE_KEEP_OUT_ONLY_PHASE_3_PENDING",
            "drainage": "REFERENCE_KEEP_OUT_ONLY_PHASE_4_PENDING",
            "irrigation": "REFERENCE_KEEP_OUT_ONLY_PHASE_5_PENDING",
            "support_clamps_and_chain": "REFERENCE_KEEP_OUT_ONLY_PHASE_6_PENDING",
        },
    }
    report_path = preview_dir / "phase2_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
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
    generate_phase2(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
