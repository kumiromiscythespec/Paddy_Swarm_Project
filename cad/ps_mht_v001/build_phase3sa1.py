"""Generate Phase 3S-A.1 print-management artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ps_mht_v001.common.phase3sa1_nonregression import (
    audit_phase1_through_phase3sa,
)
from ps_mht_v001.common.validation import (
    export_printable_set_stl,
    export_printable_stl,
    measure_shape,
    validate_stl_mesh,
)
from ps_mht_v001.print_manifest_phase3sa1 import (
    ADDITIONAL_RING_FILE,
    build_print_manifest_phase3sa1,
)
from ps_mht_v001.print_plate_layout_phase3sa1 import (
    build_plate_01_sector_seam_coupons_phase3sa1,
    selected_plates_phase3sa1,
)
from ps_mht_v001.tower_module.sector_seam_phase3sa import (
    validate_seam_clearance_phase3sa,
)
from ps_mht_v001.tower_module.temporary_capture_ring_phase3sa import (
    build_temporary_panel_capture_ring_phase3sa,
)


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "exports"


def generate_phase3sa1(
    output_root: Path,
    selected_clearance: float | None = None,
) -> dict[str, object]:
    """Generate only selection-independent files unless clearance is explicit."""

    baseline_before = audit_phase1_through_phase3sa(output_root)
    if not all(item["unchanged"] for item in baseline_before.values()):
        raise RuntimeError("Phase 1 through Phase 3S-A baseline changed")

    stl_dir = output_root / "stl"
    preview_dir = output_root / "preview"
    stl_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    plate_01 = build_plate_01_sector_seam_coupons_phase3sa1()
    plate_01_path = (
        stl_dir / "plate_01_sector_seam_coupons_phase3sa1.stl"
    )
    export_printable_set_stl(plate_01, plate_01_path, 6)
    generated.append(plate_01_path)

    additional_ring = build_temporary_panel_capture_ring_phase3sa()
    additional_ring_path = stl_dir / ADDITIONAL_RING_FILE
    export_printable_stl(additional_ring, additional_ring_path)
    generated.append(additional_ring_path)

    selected = (
        None
        if selected_clearance is None
        else validate_seam_clearance_phase3sa(selected_clearance)
    )
    if selected is not None:
        for name, model, solid_count in selected_plates_phase3sa1(selected):
            path = stl_dir / f"{name}.stl"
            export_printable_set_stl(model, path, solid_count)
            generated.append(path)

    manifest = build_print_manifest_phase3sa1(selected)
    manifest_path = preview_dir / "print_manifest_phase3sa1.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    generated.append(manifest_path)

    baseline_after = audit_phase1_through_phase3sa(output_root)
    if not all(item["unchanged"] for item in baseline_after.values()):
        raise RuntimeError("Phase 1 through Phase 3S-A baseline changed")

    validation = {
        path.name: validate_stl_mesh(path).as_dict()
        for path in generated
        if path.suffix.lower() == ".stl"
    }
    return {
        "phase": "3S-A.1",
        "status": manifest["status"],
        "selected_clearance": selected,
        "generated_files": [
            path.relative_to(output_root).as_posix()
            for path in generated
        ],
        "plate_01_metrics": measure_shape(plate_01).as_dict(),
        "additional_ring_metrics": measure_shape(additional_ring).as_dict(),
        "stl_validation": validation,
        "non_regression": {
            phase: item["unchanged"]
            for phase, item in baseline_after.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--selected-clearance",
        type=float,
        choices=(0.4, 0.6, 0.8),
        default=None,
        help=(
            "Explicit physical-test result. If omitted, Plate 02 through "
            "Plate 04 are not generated."
        ),
    )
    args = parser.parse_args()
    result = generate_phase3sa1(
        args.output.resolve(),
        args.selected_clearance,
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
