"""Generate all individual calibration STEP/STL files and optional STEP plates."""

from __future__ import annotations

import argparse
from pathlib import Path

import cadquery as cq

from bore_gauges import build_all_bore_gauges
from parameters import (
    BORE_GAUGES,
    COUPONS,
    EXPORT_DIR,
    STL_ANGULAR_TOLERANCE_RAD,
    STL_LINEAR_TOLERANCE_MM,
)
from tooth_fit_coupons import build_all_tooth_fit_coupons


def export_model(model: cq.Workplane, destination_stem: Path) -> tuple[Path, Path]:
    step_path = destination_stem.with_suffix(".step")
    stl_path = destination_stem.with_suffix(".stl")
    cq.exporters.export(model, str(step_path))
    cq.exporters.export(
        model,
        str(stl_path),
        tolerance=STL_LINEAR_TOLERANCE_MM,
        angularTolerance=STL_ANGULAR_TOLERANCE_RAD,
    )
    return step_path, stl_path


def _compound_packed(
    models: list[cq.Workplane],
    gap_mm: float = 8.0,
    maximum_row_width_mm: float = 230.0,
) -> cq.Compound:
    shapes: list[cq.Shape] = []
    cursor_x = 0.0
    cursor_y = 0.0
    row_height = 0.0
    for model in models:
        shape = model.val()
        box = shape.BoundingBox()
        if cursor_x > 0.0 and cursor_x + box.xlen > maximum_row_width_mm:
            cursor_x = 0.0
            cursor_y += row_height + gap_mm
            row_height = 0.0
        shift_x = cursor_x - box.xmin
        shift_y = cursor_y - box.ymin
        shapes.append(shape.translate(cq.Vector(shift_x, shift_y, 0.0)))
        cursor_x += box.xlen + gap_mm
        row_height = max(row_height, box.ylen)
    return cq.Compound.makeCompound(shapes)


def build_models() -> dict[str, cq.Workplane]:
    models = {}
    models.update(build_all_bore_gauges())
    models.update(build_all_tooth_fit_coupons())
    return models


def build_and_export(include_combined_steps: bool = True) -> dict[str, cq.Workplane]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    models = build_models()
    for name, model in models.items():
        export_model(model, EXPORT_DIR / name)

    if include_combined_steps:
        gauge_models = [models[spec.key] for spec in BORE_GAUGES]
        coupon_models = [models[spec.key] for spec in COUPONS]
        cq.exporters.export(
            _compound_packed(gauge_models),
            str(EXPORT_DIR / "htd5m_bore_gauges_plate_v0_1.step"),
        )
        cq.exporters.export(
            _compound_packed(coupon_models),
            str(EXPORT_DIR / "htd5m_tooth_coupons_plate_v0_1.step"),
        )
        cq.exporters.export(
            _compound_packed(gauge_models + coupon_models),
            str(EXPORT_DIR / "htd5m_calibration_all_plate_v0_1.step"),
        )
    return models


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-combined",
        action="store_true",
        help="Skip the three optional disconnected STEP presentation plates.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation after export.",
    )
    args = parser.parse_args()
    build_and_export(include_combined_steps=not args.no_combined)
    if args.validate:
        from validation import validate_all

        validate_all()


if __name__ == "__main__":
    main()
