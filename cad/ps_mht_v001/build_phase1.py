"""Generate and validate PS-MHT-V001 Phase 1 CAD artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ps_mht_v001.assembly.full_tower_assembly import (
    build_frame_model,
    build_full_tower_model,
    build_tower_only_model,
    frame_components,
    tower_components,
)
from ps_mht_v001.common.validation import (
    export_printable_step,
    export_printable_stl,
    export_reference_step,
    export_svg_preview,
    measure_shape,
    validate_stl_mesh,
    validate_single_printable,
    validate_step_round_trip,
)
from ps_mht_v001.parameters import (
    module_count,
    module_placements,
    rear_post_front_clearance,
    rear_post_max_envelope_clearance,
    tower_max_diameter,
    validate_parameters,
)
from ps_mht_v001.tower_module.planting_module import build_planting_module


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"


def generate_phase1(output_root: Path) -> dict[str, object]:
    """Build, export, re-import, and summarize all Phase 1 geometry."""

    validate_parameters()
    step_dir = output_root / "step"
    stl_dir = output_root / "stl"
    preview_dir = output_root / "preview"

    planting_module = build_planting_module()
    frame = build_frame_model()
    tower = build_tower_only_model()
    full = build_full_tower_model()

    module_metrics = validate_single_printable(
        planting_module,
        "ps_mht_v001_planting_module_A",
    )
    module_step = export_printable_step(
        planting_module,
        step_dir / "ps_mht_v001_planting_module_A.step",
    )
    module_stl = export_printable_stl(
        planting_module,
        stl_dir / "ps_mht_v001_planting_module_A.stl",
    )
    module_stl_metrics = validate_stl_mesh(module_stl)
    frame_step = export_reference_step(
        frame,
        step_dir / "ps_mht_v001_aluminum_frame_phase1.step",
        len(frame_components()),
    )
    tower_step = export_reference_step(
        tower,
        step_dir / "ps_mht_v001_tower_5_module_phase1.step",
        len(tower_components()),
    )
    full_step = export_reference_step(
        full,
        step_dir / "ps_mht_v001_full_tower_assembly_phase1.step",
        len(frame_components()) + len(tower_components()),
    )

    export_svg_preview(
        planting_module,
        preview_dir / "ps_mht_v001_planting_module_A.svg",
        (1.0, -1.0, 0.7),
    )
    export_svg_preview(
        full,
        preview_dir / "ps_mht_v001_full_tower_assembly_phase1.svg",
        (1.0, -1.0, 0.45),
    )

    round_trips = {
        "planting_module": validate_step_round_trip(
            module_step,
            1,
            printable=True,
        ).as_dict(),
        "frame": validate_step_round_trip(
            frame_step,
            len(frame_components()),
        ).as_dict(),
        "tower": validate_step_round_trip(
            tower_step,
            len(tower_components()),
        ).as_dict(),
        "full_assembly": validate_step_round_trip(
            full_step,
            len(frame_components()) + len(tower_components()),
        ).as_dict(),
    }

    report: dict[str, object] = {
        "model": "PS-MHT-V001",
        "phase": 1,
        "status": "PASS",
        "cadquery_geometry": {
            "planting_module": module_metrics.as_dict(),
            "frame": measure_shape(frame).as_dict(),
            "tower": measure_shape(tower).as_dict(),
            "full_assembly": measure_shape(full).as_dict(),
        },
        "step_round_trip": round_trips,
        "stl_mesh": {
            "planting_module": module_stl_metrics.as_dict(),
        },
        "a1_print_envelope": {
            "status": "PASS",
            "printable_parts_checked": 1,
            "module_quantity": module_count,
            "module_bbox_mm": [
                module_metrics.size_x,
                module_metrics.size_y,
                module_metrics.size_z,
            ],
        },
        "tower_max_diameter": {
            "status": "PASS",
            "phase1_actual_mm": max(
                module_metrics.size_x,
                module_metrics.size_y,
            ),
            "limit_mm": tower_max_diameter,
            "note": "Plant-port protrusions are Phase 3 pending.",
        },
        "module_placements": [
            {
                "module_number": placement.module_number,
                "z_bottom_mm": placement.z_bottom,
                "rotation_deg": placement.rotation_deg,
            }
            for placement in module_placements()
        ],
        "frame_clearance": {
            "rear_post_to_body_clearance_mm": rear_post_front_clearance(),
            "rear_post_to_240mm_envelope_clearance_mm": (
                rear_post_max_envelope_clearance()
            ),
            "status": "PASS",
        },
        "exports": [
            str(path.relative_to(output_root).as_posix())
            for path in (
                module_step,
                module_stl,
                frame_step,
                tower_step,
                full_step,
                preview_dir / "ps_mht_v001_planting_module_A.svg",
                preview_dir / "ps_mht_v001_full_tower_assembly_phase1.svg",
            )
        ],
        "phase_boundaries": {
            "drain_base": "REFERENCE_ENVELOPE_ONLY_PHASE_4_PENDING",
            "irrigation_top": "REFERENCE_ENVELOPE_ONLY_PHASE_5_PENDING",
            "plant_ports": "PHASE_3_PENDING",
            "module_interface": "PHASE_2_PENDING",
        },
    }
    report_path = preview_dir / "phase1_validation_report.json"
    report["exports"].append("preview/phase1_validation_report.json")
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
    generate_phase1(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
