"""Generate material-classified dummy panicle interface and head v0.1 files."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cadquery as cq

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dummy_panicle_v0_1 import VERSION
from dummy_panicle_v0_1.assemblies.panicle_assembly_preview import (
    PanicleAssemblyPreview,
    build_preview,
    export_preview_step,
)
from dummy_panicle_v0_1.cq_config import (
    DENSITY,
    EXPORT,
    PRINT,
    estimated_mass_g,
)
from dummy_panicle_v0_1.cq_utils import (
    ShapeMetrics,
    export_step,
    export_stl,
    validate_printable_shape,
    validate_step_round_trip,
)
from dummy_panicle_v0_1.cutting_cartridge_holder import (
    CuttingCartridgeHolderParams,
    build as build_cartridge_holder,
    build_tube_marking_gauge,
    stem_socket_depth,
)
from dummy_panicle_v0_1.interfaces import (
    CARTRIDGE,
    PANICLE_HEAD,
    PANICLE_TAB,
    STEM,
)
from dummy_panicle_v0_1.panicle_branch import (
    PanicleBranchParams,
    build as build_panicle_branch,
)
from dummy_panicle_v0_1.panicle_hub import (
    PanicleHubParams,
    build as build_panicle_hub,
    interference_clearances,
    params_for_preset as hub_params_for_preset,
    weight_pocket_volume_mm3,
)
from dummy_panicle_v0_1.panicle_slot_coupon import (
    PanicleSlotCouponParams,
    build as build_slot_coupon,
)
from dummy_panicle_v0_1.panicle_tab_coupon import build as build_tab_coupon
from dummy_panicle_v0_1.panicle_weight_cap import (
    PanicleWeightCapParams,
    build as build_weight_cap,
    retention_interference,
)
from dummy_panicle_v0_1.root_socket import build as build_root_socket
from dummy_panicle_v0_1.stem_clearance_coupon import (
    StemClearanceCouponParams,
    build as build_stem_coupon,
)
from dummy_panicle_v0_1.stem_end_plug import (
    build as build_stem_end_plug,
    params_for_preset as plug_params_for_preset,
)


@dataclass(frozen=True)
class PartDefinition:
    """One printable artifact and its manifest metadata."""

    part_id: str
    filename_stem: str
    description: str
    material: str
    quantity: int
    preset: str
    printable: bool
    calibration_status: str
    builder: Callable[[], cq.Workplane]


PARTS: tuple[PartDefinition, ...] = (
    PartDefinition(
        "CAL-STEM",
        "stem_clearance_coupon_PETG",
        "PETG five-hole STEM-NOMINAL-4 clearance coupon",
        "PETG",
        1,
        "five_hole_series",
        True,
        "CALIBRATION_PENDING",
        build_stem_coupon,
    ),
    PartDefinition(
        "CAL-PANICLE-TAB",
        "panicle_tab_coupon_TPU",
        "TPU PANICLE-TAB-V001 tab with handle",
        "TPU",
        1,
        "standard",
        True,
        "CALIBRATION_PENDING",
        build_tab_coupon,
    ),
    PartDefinition(
        "CAL-PANICLE-SLOT",
        "panicle_slot_coupon_PETG",
        "PETG five-slot PANICLE-TAB-V001 comparison coupon",
        "PETG",
        1,
        "five_slot_series",
        True,
        "CALIBRATION_PENDING",
        build_slot_coupon,
    ),
    PartDefinition(
        "DR-B01",
        "DR-B01_root_socket_PETG",
        "DR-B01 one-piece MEDIUM 0-degree root socket",
        "PETG",
        1,
        "medium_upright",
        True,
        "CALIBRATION_PENDING",
        build_root_socket,
    ),
    PartDefinition(
        "DR-S03",
        "DR-S03_stem_end_plug_tube_id_3p6_calibration_PETG",
        "DR-S03 unverified 3.6 mm tube-ID calibration plug",
        "PETG",
        1,
        "tube_id_3p6_calibration",
        True,
        "CALIBRATION_PENDING",
        lambda: build_stem_end_plug(
            plug_params_for_preset("tube_id_3p6_calibration")
        ),
    ),
    PartDefinition(
        "DR-C01-HOLDER",
        "DR-C01_cutting_cartridge_holder_PETG",
        "DR-C01 common upper/lower reusable cartridge holder",
        "PETG",
        2,
        "common",
        True,
        "CALIBRATION_PENDING",
        build_cartridge_holder,
    ),
    PartDefinition(
        "DR-C01-GAUGE",
        "DR-C01_tube_marking_gauge_PETG",
        "DR-C01 removable paper-tube marking gauge; non-cut use only",
        "PETG",
        1,
        "marking_only",
        True,
        "CALIBRATION_PENDING",
        build_tube_marking_gauge,
    ),
    PartDefinition(
        "DR-H01",
        "DR-H01_panicle_branch_standard_TPU",
        "DR-H01 flat 10-branch, 14-grain TPU panicle panel",
        "TPU",
        PANICLE_HEAD.branch_print_quantity,
        "standard",
        True,
        PANICLE_HEAD.calibration_status,
        build_panicle_branch,
    ),
    PartDefinition(
        "DR-H02",
        "DR-H02_panicle_hub_upright_PETG",
        "DR-H02 four-slot PETG panicle hub, fixed 0-degree interface",
        "PETG",
        1,
        "upright",
        True,
        PANICLE_HEAD.calibration_status,
        lambda: build_panicle_hub(hub_params_for_preset("upright")),
    ),
    PartDefinition(
        "DR-H02",
        "DR-H02_panicle_hub_droop20_PETG",
        "DR-H02 four-slot PETG panicle hub, fixed 20-degree interface",
        "PETG",
        1,
        "droop20",
        True,
        PANICLE_HEAD.calibration_status,
        lambda: build_panicle_hub(hub_params_for_preset("droop20")),
    ),
    PartDefinition(
        "DR-H03",
        "DR-H03_panicle_weight_cap_PETG",
        "DR-H03 removable PETG weight-pocket cap",
        "PETG",
        2,
        "standard",
        True,
        PANICLE_HEAD.calibration_status,
        build_weight_cap,
    ),
)


@dataclass(frozen=True)
class GeneratedPart:
    """Measured and exported printable-part record."""

    definition: PartDefinition
    metrics: ShapeMetrics
    estimated_mass_g: float
    step_path: Path
    stl_path: Path


@dataclass(frozen=True)
class GeneratedPreview:
    """Exported non-printable assembly record."""

    part_id: str
    preset: str
    preview: PanicleAssemblyPreview
    step_path: Path
    calibration_status: str = "CALIBRATION_PENDING"


LEGACY_FILENAME_STEMS: tuple[str, ...] = (
    "stem_clearance_coupon",
    "panicle_tab_coupon_TPU",
    "panicle_slot_coupon_PETG",
    "DR-B01_root_socket",
    "DR-S03_stem_end_plug_paper_tube",
    "DR-S03_stem_end_plug_tube_id_3p6_calibration",
    "DR-C01_cutting_cartridge_holder",
    "DR-C01_cut_zone_marker",
    "DR-C01_tube_marking_gauge",
)


def _remove_known_legacy_outputs(output_root: Path) -> None:
    """Remove only code-listed obsolete flat-path outputs."""

    for directory, suffix in (("step", ".step"), ("stl", ".stl")):
        for filename_stem in LEGACY_FILENAME_STEMS:
            legacy_path = output_root / directory / f"{filename_stem}{suffix}"
            if legacy_path.is_file():
                legacy_path.unlink()


def _density_for(material: str) -> float:
    """Return the provisional density used for a report row."""

    return {
        "PETG": DENSITY.petg_g_cm3,
        "TPU": DENSITY.tpu_95a_g_cm3,
    }[material]


def _write_dimensions_csv(records: list[GeneratedPart], output_path: Path) -> None:
    """Write geometry and explicitly provisional CAD mass estimates."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            (
                "part_id",
                "filename_stem",
                "description",
                "material",
                "quantity",
                "preset",
                "size_x_mm",
                "size_y_mm",
                "size_z_mm",
                "solid_count",
                "volume_mm3",
                "estimated_mass_each_g",
                "estimated_mass_quantity_g",
                "density_g_cm3",
                "density_status",
                "measured_mass_status",
                "a1_safe_240x240x220",
            )
        )
        for record in records:
            metrics = record.metrics
            definition = record.definition
            writer.writerow(
                (
                    definition.part_id,
                    definition.filename_stem,
                    definition.description,
                    definition.material,
                    definition.quantity,
                    definition.preset,
                    f"{metrics.size_x:.3f}",
                    f"{metrics.size_y:.3f}",
                    f"{metrics.size_z:.3f}",
                    metrics.solid_count,
                    f"{metrics.volume:.3f}",
                    f"{record.estimated_mass_g:.3f}",
                    f"{record.estimated_mass_g * definition.quantity:.3f}",
                    f"{_density_for(definition.material):.3f}",
                    DENSITY.status,
                    "NOT_MEASURED",
                    "YES",
                )
            )


def _write_manifest_csv(
    records: list[GeneratedPart],
    previews: list[GeneratedPreview],
    output_path: Path,
    output_root: Path,
) -> None:
    """Write one output-root-relative manifest row per artifact."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as stream:
        fieldnames = (
            "part_id",
            "filename",
            "material",
            "quantity",
            "preset",
            "relative_path",
            "revision",
            "printable",
            "calibration_status",
            "format",
            "bytes",
        )
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            for path, file_format in (
                (record.step_path, "STEP"),
                (record.stl_path, "STL"),
            ):
                definition = record.definition
                writer.writerow(
                    {
                        "part_id": definition.part_id,
                        "filename": path.name,
                        "material": definition.material,
                        "quantity": definition.quantity,
                        "preset": definition.preset,
                        "relative_path": path.relative_to(output_root).as_posix(),
                        "revision": VERSION,
                        "printable": "true",
                        "calibration_status": definition.calibration_status,
                        "format": file_format,
                        "bytes": path.stat().st_size,
                    }
                )
        for record in previews:
            writer.writerow(
                {
                    "part_id": record.part_id,
                    "filename": record.step_path.name,
                    "material": "ASSEMBLY",
                    "quantity": 1,
                    "preset": record.preset,
                    "relative_path": record.step_path.relative_to(output_root).as_posix(),
                    "revision": VERSION,
                    "printable": "false",
                    "calibration_status": record.calibration_status,
                    "format": "STEP",
                    "bytes": record.step_path.stat().st_size,
                }
            )


def _write_material_guide(output_path: Path) -> None:
    """Write filename-driven material and print-quantity guidance."""

    sections: list[str] = []
    for material in ("TPU", "PETG"):
        rows = "\n".join(
            f"- `{part.filename_stem}.stl` — print {part.quantity} — {part.description}"
            for part in PARTS
            if part.material == material
        )
        sections.append(f"## {material}\n\n{rows}")
    guide = f"""# Dummy Panicle {VERSION} Material Guide

Every printable filename ends in `_TPU` or `_PETG` and is stored in the
matching material folder.  Do not infer material from part shape.  All fits
remain `CALIBRATION_PENDING`.

{'\n\n'.join(sections)}

The two files in `out/preview/` are non-printable ASSEMBLY STEP compounds and
have no STL counterpart.  Powered cutting remains unauthorized.
"""
    output_path.write_text(guide, encoding="utf-8")


def _write_interface_report(output_path: Path) -> None:
    """Write shared interfaces, correction-only datums, and head caveats."""

    stem_params = StemClearanceCouponParams()
    slot_params = PanicleSlotCouponParams()
    holder_params = CuttingCartridgeHolderParams()
    stem_rows = "\n".join(
        f"| {index} | {diameter:.2f} |"
        for index, diameter in enumerate(stem_params.hole_diameters, start=1)
    )
    slot_rows = "\n".join(
        f"| {index} | {width:.1f} | {thickness:.1f} |"
        for index, (width, thickness) in enumerate(slot_params.slot_sizes, start=1)
    )
    report = f"""# Dummy Panicle {VERSION} Interface Report

All dimensions are millimetres.  No repository evidence of a successful
printed fit or measured mass was found, so all listed fit values remain
`CALIBRATION_PENDING`.  Powered cutting is not authorized by this revision.

## Shared interfaces

- `{STEM.name}`: 4.0 shaft, 4.3 provisional receiver, 20 insertion.
- `{PANICLE_TAB.name}`: TPU tab 8.0 x 2.0 x 14; provisional PETG slot
  8.4 x 2.4 x 12 deep.
- A1 conservative envelope: {PRINT.max_x:.0f} x {PRINT.max_y:.0f} x
  {PRINT.max_z:.0f}; nozzle {PRINT.nozzle_diameter:.1f}; standard layer
  {PRINT.layer_height:.2f}.
- PETG wall target {PRINT.petg_min_wall:.1f}; TPU minimum
  {PRINT.tpu_min_wall:.1f}.  DR-H03 uses its explicitly permitted 1.5 mm
  minimum flange thickness.

## Existing calibration coupon maps

| Stem label | Hole diameter |
|---:|---:|
{stem_rows}

| Slot label | Width | Thickness |
|---:|---:|---:|
{slot_rows}

## Existing interfaces retained

- DR-B01 remains the fixed 0-degree MEDIUM root socket.
- DR-S03 exports preset `tube_id_3p6_calibration`.  Its mating ID is unmeasured
  and it is not guaranteed to be the same material or stock as the DR-C01
  nominal 4.0 OD / 2.5 ID cartridge tube.
- DR-C01 uses two identical holders.  Its 4.10 cartridge bore and 4.30 stem
  bore are calibration candidates and do not guarantee retention.
- Cartridge equation: {CARTRIDGE.cartridge_length:.0f} =
  2 x {CARTRIDGE.holder_insertion_depth:.0f} +
  2 x {CARTRIDGE.holder_face_safety_distance:.0f} +
  {CARTRIDGE.cuttable_length:.0f}.
- The 30 mm datum begins at the cartridge-side PETG face nearest the nominal
  blade zone, not the outside/stem-side holder face.
- The removable PETG gauge is only for drawing lines directly on the paper
  tube or non-cutting bench visualization.  Remove it afterward.  It is
  prohibited near a blade and for powered cutting.

## Panicle head interfaces

- DR-H01: four 8.0 x 2.0 x 14 TPU tabs in service; print one first for fit,
  then print six including spares.
- DR-H02: four 8.4 x 2.4 x 12 top-entry slots at 90-degree intervals.
- DR-H02 nominal 24 mm OD did not satisfy the simultaneous 2 mm wall
  constraints.  Both fixed presets therefore use the permitted 30.0 mm OD.
- DR-H02 stem interface is fixed 0 degrees (`upright`) or fixed 20 degrees
  (`droop20`); there is no moving hinge.
- DR-H03 uses a 7.8 mm plug and 8.2 mm shallow bead in the uncalibrated
  8.0 mm pocket.  Its 0.20 mm diametral interference candidate does not
  guarantee retention.
- TPU branches must never contact a rotating blade.

## Export validation

- STL linear/angular tolerances: {EXPORT.tolerance:.2f} /
  {EXPORT.angular_tolerance:.2f}.
- Every printable STEP is re-imported as one valid positive-volume solid.
- Preview STEP compounds are re-imported with seven component solids and are
  explicitly non-printable.
- Compact DR-C01 outer-stem socket depth:
  {stem_socket_depth(holder_params):.1f}.
"""
    output_path.write_text(report, encoding="utf-8")


def _find_record(records: list[GeneratedPart], filename_stem: str) -> GeneratedPart:
    """Find one generated part record by canonical stem."""

    return next(
        record
        for record in records
        if record.definition.filename_stem == filename_stem
    )


def _write_panicle_head_report(
    records: list[GeneratedPart],
    previews: list[GeneratedPreview],
    output_path: Path,
) -> None:
    """Write geometry, interference, mass-estimate, and safety findings."""

    branch = _find_record(records, "DR-H01_panicle_branch_standard_TPU")
    upright = _find_record(records, "DR-H02_panicle_hub_upright_PETG")
    droop = _find_record(records, "DR-H02_panicle_hub_droop20_PETG")
    cap = _find_record(records, "DR-H03_panicle_weight_cap_PETG")
    branch_params = PanicleBranchParams()
    upright_params = hub_params_for_preset("upright")
    droop_params = hub_params_for_preset("droop20")
    cap_params = PanicleWeightCapParams()
    branch_box = build_panicle_branch(branch_params).val().BoundingBox()
    branch_max_half_width = max(abs(branch_box.xmin), abs(branch_box.xmax))

    def metrics_line(record: GeneratedPart) -> str:
        metrics = record.metrics
        return (
            f"{metrics.size_x:.3f} x {metrics.size_y:.3f} x "
            f"{metrics.size_z:.3f}; V={metrics.volume:.3f} mm3; "
            f"solids={metrics.solid_count}; estimate={record.estimated_mass_g:.3f} g"
        )

    upright_total = (
        4.0 * branch.estimated_mass_g
        + upright.estimated_mass_g
        + cap.estimated_mass_g
    )
    droop_total = (
        4.0 * branch.estimated_mass_g
        + droop.estimated_mass_g
        + cap.estimated_mass_g
    )
    preview_rows = "\n".join(
        f"- {record.preset}: {record.preview.metrics.size_x:.3f} x "
        f"{record.preview.metrics.size_y:.3f} x "
        f"{record.preview.metrics.size_z:.3f} mm; 7 solids; "
        f"`preview/{record.step_path.name}`"
        for record in previews
    )
    clearance_rows = "\n".join(
        f"| {name} | {interference_clearances(upright_params)[name]:.3f} | "
        f"{interference_clearances(droop_params)[name]:.3f} |"
        for name in interference_clearances(upright_params)
    )
    report = f"""# Panicle Head v0.1 Report ({VERSION})

Status: `CALIBRATION_PENDING`.  CAD geometry and export validation are
complete; printed fit, retention, durability, centre of gravity, and mass are
not measured.

## DR-H01 TPU panel

- {metrics_line(branch)}
- Length {branch_params.total_length:.1f}; measured maximum one-sided width
  {branch_max_half_width:.3f}; panel/neck minimum thickness
  {branch_params.thickness:.1f}/{branch_params.neck_thickness:.1f}.
- 10 deterministic lateral branches and 14 connected capsule grains.
- Standard assembly uses 4 panels (56 grains); recommended print quantity is
  6.  Print one panel first and calibrate the tab/slot fit.

## DR-H02 PETG hub

- Upright: {metrics_line(upright)}
- Droop20: {metrics_line(droop)}
- 30.0 OD x 28.0 high; four provisional 8.4 x 2.4 x 12 slots; provisional
  4.3 stem hole x 20; 1.2 split; 3.2 M3 through-hole and M3 nut trap.
- The requested 24 mm OD cannot preserve the required outer wall around the
  chamfered slot corners.  The calculated minimum is approximately 29.6 mm
  for both presets; the permitted rounded value 30.0 mm was adopted.
- Weight pocket: 8.0 diameter x 6.0 deep,
  {weight_pocket_volume_mm3(upright_params):.3f} mm3 nominal capacity.

| Conservative clearance | upright | droop20 |
|---|---:|---:|
{clearance_rows}

All reported cavity/wall clearances are at least 2.0 mm.  The 20-degree model
tilts the single stem interface, so the whole four-panel head droops together.

## DR-H03 PETG cap

- {metrics_line(cap)}
- 12.2 flange OD x 6.0 high; 7.8 plug; 8.2 shallow bead; diametral candidate
  interference {retention_interference(cap_params):.2f}.
- The cap is tool-removable through a shallow flange-edge notch.  Retention is
  not guaranteed before printed fit and shake tests.

## Panicle-only previews

{preview_rows}

Each preview contains DR-H01 x4, DR-H02 x1, DR-H03 x1, and one simple 4 mm
stem.  Panel orientations are 0/90/180/270 degrees, insertion is 12 mm, and
pairwise panel intersection is zero.  Preview STEP files are not printable
parts and no preview STL is generated.  PNG rendering was not executed because
the existing workflow does not provide a required renderer and no dependency
was added.

## Provisional CAD mass estimate

- Density settings: TPU 95A {DENSITY.tpu_95a_g_cm3:.3f} g/cm3; PETG
  {DENSITY.petg_g_cm3:.3f} g/cm3; status `{DENSITY.status}`.
- Head without simple preview stem or metal weights: upright
  {upright_total:.3f} g; droop20 {droop_total:.3f} g.
- Both estimates exceed the 4-6 g target.  The largest contribution is the
  DR-H02 hub, followed by four DR-H01 panels.  The pocket can only add measured
  metal mass; it cannot reduce the base mass.
- This is not a measured failure determination.  Slicer perimeter/infill
  behaviour, extrusion, and printed material density remain unknown.  No
  fit or mass acceptance may be claimed until real parts are printed and
  weighed; later lightweighting would require a separately reviewed geometry
  revision.

## Safety

Powered cutting is not authorized.  TPU panicle branches must never contact a
rotating blade.  Secure any metal pocket contents and verify cap retention
before hand-motion testing.  Avoid over-tightening the M3 clamp.
"""
    output_path.write_text(report, encoding="utf-8")


def generate_all(
    output_root: str | Path,
) -> tuple[list[GeneratedPart], list[GeneratedPreview]]:
    """Build, export, re-import, and report all retained and new artifacts."""

    root = Path(output_root)
    reports_dir = root / "reports"
    records: list[GeneratedPart] = []
    previews: list[GeneratedPreview] = []
    _remove_known_legacy_outputs(root)

    for definition in PARTS:
        shape = definition.builder()
        metrics = validate_printable_shape(shape, definition.filename_stem)
        step_path = export_step(
            shape,
            root / "step" / definition.material / f"{definition.filename_stem}.step",
        )
        validate_step_round_trip(step_path)
        stl_path = export_stl(
            shape,
            root / "stl" / definition.material / f"{definition.filename_stem}.stl",
        )
        record = GeneratedPart(
            definition,
            metrics,
            estimated_mass_g(metrics.volume, definition.material),
            step_path,
            stl_path,
        )
        records.append(record)
        print(
            f"OK {definition.filename_stem}: "
            f"{metrics.size_x:.3f} x {metrics.size_y:.3f} x "
            f"{metrics.size_z:.3f} mm, V={metrics.volume:.3f} mm3",
            flush=True,
        )

    for preset in ("upright", "droop20"):
        preview = build_preview(preset)
        step_path = export_preview_step(
            preview,
            root / "preview" / f"panicle_assembly_{preset}.step",
        )
        previews.append(
            GeneratedPreview(
                part_id="PANICLE-ASSEMBLY-PREVIEW",
                preset=preset,
                preview=preview,
                step_path=step_path,
            )
        )
        print(
            f"OK panicle_assembly_{preset}: "
            f"{preview.metrics.size_x:.3f} x {preview.metrics.size_y:.3f} x "
            f"{preview.metrics.size_z:.3f} mm, non-printable",
            flush=True,
        )

    _write_dimensions_csv(records, reports_dir / "dimensions.csv")
    _write_manifest_csv(
        records,
        previews,
        reports_dir / "export_manifest.csv",
        root,
    )
    _write_interface_report(reports_dir / "interface_report.md")
    _write_material_guide(reports_dir / "material_guide.md")
    _write_panicle_head_report(
        records,
        previews,
        reports_dir / "panicle_head_report.md",
    )
    return records, previews


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""

    default_output = Path(__file__).resolve().parent / "out"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=default_output,
        help=f"output root (default: {default_output})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    args = parse_args(argv)
    records, previews = generate_all(args.out)
    print(
        f"Generated {len(records)} printable parts and "
        f"{len(previews)} non-printable previews in {args.out}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
