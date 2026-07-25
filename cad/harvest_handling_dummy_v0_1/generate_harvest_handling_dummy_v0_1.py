"""Generate all HHD-V001 printable parts, preview, and reports."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cadquery as cq

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harvest_handling_dummy_v0_1 import PROJECT_NAME, VERSION
from harvest_handling_dummy_v0_1.angle_gauge import build as build_angle_gauge
from harvest_handling_dummy_v0_1.assemblies.handling_dummy_standard import (
    StandardAssemblyPreview,
    build_standard_preview,
    projected_stem_crossings,
)
from harvest_handling_dummy_v0_1.cq_utils import (
    ShapeMetrics,
    export_preview_step,
    export_step,
    export_stl,
    measure_shape,
    relative_output_path,
    remove_known_outputs,
    validate_print_bounds,
    validate_step_round_trip,
)
from harvest_handling_dummy_v0_1.height_gauge import (
    PART_IDS as HEIGHT_PART_IDS,
    build as build_height_marker,
)
from harvest_handling_dummy_v0_1.interfaces import validate_all_interfaces
from harvest_handling_dummy_v0_1.layout_record_plate import (
    build as build_layout_plate,
)
from harvest_handling_dummy_v0_1.parameters import (
    BASE_SOCKET,
    HEIGHTS_MM,
    ROOT_BASE,
    ROOT_MOUNT,
    STEM_PLUG_IF,
)
from harvest_handling_dummy_v0_1.presets.layout_standard_v001 import (
    LAYOUT_STANDARD_V001,
    maximum_radial_diameter,
    minimum_center_spacing,
    radial_band_counts,
    rows_as_dicts,
    symmetry_matches,
)
from harvest_handling_dummy_v0_1.root_base import (
    build as build_base,
    minimum_m4_socket_wall,
    socket_edge_margin,
)
from harvest_handling_dummy_v0_1.root_base_mount import (
    build as build_mount,
    minimum_m6_m4_wall,
)
from harvest_handling_dummy_v0_1.socket_lock_coupon import (
    build as build_socket_coupon,
    candidate_receiver_diameters,
)
from harvest_handling_dummy_v0_1.stem_end_plug import (
    PRESET_DATA,
    build as build_stem_plug,
    material_sleeve_outer_diameter,
    params_for_preset as plug_params_for_preset,
)
from harvest_handling_dummy_v0_1.stem_plug_fit_coupon import (
    HOLE_DIAMETERS,
    build as build_stem_coupon,
)
from harvest_handling_dummy_v0_1.stem_socket import (
    SOCKET_PART_IDS,
    build as build_socket,
    measured_axis_angle_deg,
    params_for_angle,
)


@dataclass(frozen=True)
class PartDefinition:
    """One printable output and manifest/BOM metadata."""

    part_id: str
    filename_stem: str
    description: str
    material: str
    quantity: int
    preset: str
    module: str
    notes: str
    builder: Callable[[], cq.Workplane]
    printable: bool = True
    calibration_status: str = "CALIBRATION_PENDING"


PARTS: tuple[PartDefinition, ...] = (
    *tuple(
        PartDefinition(
            part_id=f"HU-H0-HHD-BAS-{module}",
            filename_stem=f"HU-H0-HHD-BAS-{module}_PETG",
            description=f"Six-socket fixed-root base module {module}",
            material="PETG",
            quantity=1,
            preset=f"module_{module.lower()}",
            module=module,
            notes="Mount-mediated locating pins; six BASE-SOCKET-IF-V001 receivers.",
            builder=lambda module=module: build_base(module),
        )
        for module in ("A", "B", "C", "D")
    ),
    *tuple(
        PartDefinition(
            part_id=f"HU-H0-HHD-MNT-{side}",
            filename_stem=f"HU-H0-HHD-MNT-{side}_PETG",
            description=f"Workbench mount half {side}",
            material="PETG",
            quantity=1,
            preset=f"side_{side.lower()}",
            module=side,
            notes="M6 workbench holes, M4 module holes, locating pins, seam tongue/pocket.",
            builder=lambda side=side: build_mount(side),
        )
        for side in ("L", "R")
    ),
    *tuple(
        PartDefinition(
            part_id=SOCKET_PART_IDS[angle],
            filename_stem=f"{SOCKET_PART_IDS[angle]}_PETG",
            description=f"Fixed {int(angle)} degree exchangeable stem socket",
            material="PETG",
            quantity={0.0: 8, 10.0: 8, 20.0: 6, 30.0: 2}[angle],
            preset=f"tilt_{int(angle):02d}",
            module="ALL",
            notes="Eight-direction octagon index; shallow split-bead retention candidate.",
            builder=lambda angle=angle: build_socket(params_for_angle(angle)),
        )
        for angle in (0.0, 10.0, 20.0, 30.0)
    ),
    *tuple(
        PartDefinition(
            part_id=PRESET_DATA[preset][0],
            filename_stem=f"{PRESET_DATA[preset][0]}_PETG",
            description=(
                f"Stem end plug {preset}; commercial material fit candidate"
            ),
            material="PETG",
            quantity=1,
            preset=preset,
            module="ALL",
            notes="Common 6 mm shank; material-side dimensions require calibration.",
            builder=lambda preset=preset: build_stem_plug(
                plug_params_for_preset(preset)
            ),
        )
        for preset in (
            "rod_od_2p0",
            "rod_od_3p0",
            "rod_od_4p0",
            "rod_od_5p0",
            "blank_custom",
        )
    ),
    PartDefinition(
        "HU-H0-HHD-CPN-SOCKET-LOCK",
        "HU-H0-HHD-CPN-SOCKET-LOCK_PETG",
        "Three-candidate BASE-SOCKET snap/fit coupon",
        "PETG",
        1,
        "snap_0p15_0p25_0p35",
        "CALIBRATION",
        "Print before any base/socket quantity.",
        build_socket_coupon,
    ),
    PartDefinition(
        "HU-H0-HHD-CPN-STEM-PLUG-FIT",
        "HU-H0-HHD-CPN-STEM-PLUG-FIT_PETG",
        "Five-hole 6 mm common plug fit coupon",
        "PETG",
        1,
        "holes_6p10_to_6p40",
        "CALIBRATION",
        "Print before selecting the 6 mm socket receiver fit.",
        build_stem_coupon,
    ),
    PartDefinition(
        "HU-H0-HHD-GAG-ANGLE",
        "HU-H0-HHD-GAG-ANGLE_PETG",
        "Flat 0/10/20/30 degree and eight-direction gauge",
        "PETG",
        1,
        "standard",
        "TOOLS",
        "Reference-only setup gauge.",
        build_angle_gauge,
    ),
    *tuple(
        PartDefinition(
            part_id=HEIGHT_PART_IDS[label],
            filename_stem=f"{HEIGHT_PART_IDS[label]}_PETG",
            description=f"Generic zip-tie height marker {label}",
            material="PETG",
            quantity=1,
            preset=label.lower(),
            module="TOOLS",
            notes="Attach to a purchased ruler or stick; not a printed tall gauge.",
            builder=lambda label=label: build_height_marker(label),
        )
        for label in ("BASE", "650", "750", "850")
    ),
    *tuple(
        PartDefinition(
            part_id=f"HU-H0-HHD-MAP-{module}",
            filename_stem=f"HU-H0-HHD-MAP-{module}_PETG",
            description=f"Removable socket layout record plate {module}",
            material="PETG",
            quantity=1,
            preset=f"layout_standard_v001_{module.lower()}",
            module=module,
            notes="Transfer aid only; CSV/JSON remain the design authority.",
            builder=lambda module=module: build_layout_plate(module),
        )
        for module in ("A", "B", "C", "D")
    ),
)


@dataclass(frozen=True)
class GeneratedPart:
    """Measured printable output record."""

    definition: PartDefinition
    metrics: ShapeMetrics
    step_path: Path
    stl_path: Path


@dataclass(frozen=True)
class GeneratedPreview:
    """Measured non-printable standard assembly record."""

    preview: StandardAssemblyPreview
    step_path: Path


def _canonical_output_relative_paths() -> tuple[str, ...]:
    """Return only code-owned paths eligible for replacement."""

    paths: list[str] = []
    for part in PARTS:
        paths.extend(
            (
                f"step/PETG/{part.filename_stem}.step",
                f"stl/PETG/{part.filename_stem}.stl",
            )
        )
    paths.append("preview/HU-H0-HHD_standard_fixed_root.step")
    # v0.1.0 wrote this development audit into the normal report set.  It is
    # removed once during regular generation and is never regenerated here.
    paths.append("reports/protected_dummy_panicle_hashes.json")
    return tuple(paths)


def _assert_no_3mf(output_root: Path) -> None:
    """Reject manual slicer project files inside the generated package."""

    files = list(output_root.rglob("*.3mf")) if output_root.exists() else []
    if files:
        raise RuntimeError(
            "manual 3MF files are prohibited in HHD generated out/: "
            + ", ".join(str(path) for path in files)
        )


def _write_layout_reports(reports_dir: Path) -> None:
    """Write authoritative fixed layout to CSV and JSON."""

    rows = rows_as_dicts()
    csv_path = reports_dir / "layout_standard_v001.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    json_path = reports_dir / "layout_standard_v001.json"
    json_path.write_text(
        json.dumps(
            {
                "project": PROJECT_NAME,
                "revision": VERSION,
                "authoritative": True,
                "randomized_at_runtime": False,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_dimensions_csv(records: list[GeneratedPart], output_path: Path) -> None:
    """Write measured printable bounding boxes and volumes."""

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
                "module",
                "size_x_mm",
                "size_y_mm",
                "size_z_mm",
                "solid_count",
                "volume_mm3",
                "a1_safe_240x240x220",
            )
        )
        for record in records:
            definition = record.definition
            metrics = record.metrics
            writer.writerow(
                (
                    definition.part_id,
                    definition.filename_stem,
                    definition.description,
                    definition.material,
                    definition.quantity,
                    definition.preset,
                    definition.module,
                    f"{metrics.size_x:.3f}",
                    f"{metrics.size_y:.3f}",
                    f"{metrics.size_z:.3f}",
                    metrics.solid_count,
                    f"{metrics.volume_mm3:.3f}",
                    "YES",
                )
            )


def _write_manifest(
    records: list[GeneratedPart],
    preview: GeneratedPreview,
    output_path: Path,
    output_root: Path,
) -> None:
    """Write one output-root-relative row per generated binary."""

    fields = (
        "part_id",
        "filename",
        "material",
        "quantity",
        "preset",
        "relative_path",
        "revision",
        "printable",
        "calibration_status",
        "module",
        "notes",
        "format",
        "bytes",
    )
    with output_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in records:
            definition = record.definition
            for path, file_format in (
                (record.step_path, "STEP"),
                (record.stl_path, "STL"),
            ):
                writer.writerow(
                    {
                        "part_id": definition.part_id,
                        "filename": path.name,
                        "material": definition.material,
                        "quantity": definition.quantity,
                        "preset": definition.preset,
                        "relative_path": relative_output_path(path, output_root),
                        "revision": VERSION,
                        "printable": "true",
                        "calibration_status": definition.calibration_status,
                        "module": definition.module,
                        "notes": definition.notes,
                        "format": file_format,
                        "bytes": path.stat().st_size,
                    }
                )
        writer.writerow(
            {
                "part_id": "HU-H0-HHD-STANDARD",
                "filename": preview.step_path.name,
                "material": "ASSEMBLY",
                "quantity": 1,
                "preset": "layout_standard_v001",
                "relative_path": relative_output_path(
                    preview.step_path,
                    output_root,
                ),
                "revision": VERSION,
                "printable": "false",
                "calibration_status": "CALIBRATION_PENDING",
                "module": "ASSEMBLY",
                "notes": "54-solid preview only; no STL and no full-machine hardware.",
                "format": "STEP",
                "bytes": preview.step_path.stat().st_size,
            }
        )


def _write_bom(output_path: Path) -> None:
    """Write printed and provisional purchased-item BOM."""

    fields = (
        "part_id",
        "description",
        "quantity",
        "material",
        "printed_or_purchased",
        "nominal_size",
        "calibration_required",
        "notes",
    )
    rows: list[dict[str, object]] = [
        {
            "part_id": part.part_id,
            "description": part.description,
            "quantity": part.quantity,
            "material": part.material,
            "printed_or_purchased": "PRINTED",
            "nominal_size": part.preset,
            "calibration_required": "YES",
            "notes": part.notes,
        }
        for part in PARTS
    ]
    rows.extend(
        (
            {
                "part_id": "PUR-M6-BOLT",
                "description": "Workbench fixing bolt candidate",
                "quantity": 4,
                "material": "METAL_UNASSIGNED",
                "printed_or_purchased": "PURCHASED",
                "nominal_size": "M6 length TBD",
                "calibration_required": "YES",
                "notes": "Select length for actual workbench thickness.",
            },
            {
                "part_id": "PUR-M4-BOLT",
                "description": "Base module fixing bolt candidate",
                "quantity": 16,
                "material": "METAL_UNASSIGNED",
                "printed_or_purchased": "PURCHASED",
                "nominal_size": "M4 length TBD",
                "calibration_required": "YES",
                "notes": "Four per base module.",
            },
            {
                "part_id": "PUR-M4-NUT",
                "description": "Base module fixing nut",
                "quantity": 16,
                "material": "METAL_UNASSIGNED",
                "printed_or_purchased": "PURCHASED",
                "nominal_size": "M4",
                "calibration_required": "NO",
                "notes": "Washers may be added after bench inspection.",
            },
            {
                "part_id": "PUR-HHD-STEM",
                "description": "Independent commercial simulated-stem material",
                "quantity": 24,
                "material": "UNASSIGNED",
                "printed_or_purchased": "PURCHASED",
                "nominal_size": "OD and material TBD; 650/750/850 mm virtual classes",
                "calibration_required": "YES",
                "notes": "Do not substitute dry rice straw without measured adapter data.",
            },
            {
                "part_id": "PUR-ZIP-TIE",
                "description": "Generic height-marker attachment tie",
                "quantity": 8,
                "material": "NYLON_CANDIDATE",
                "printed_or_purchased": "PURCHASED",
                "nominal_size": "width <= 4 mm candidate",
                "calibration_required": "YES",
                "notes": "Quantity and size depend on purchased ruler/stick.",
            },
        )
    )
    with output_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_interface_report(output_path: Path) -> None:
    """Write provisional mechanical interfaces and safety boundaries."""

    report = f"""# {PROJECT_NAME} Interface Report

Revision: `{VERSION}`.  All fits are `CALIBRATION_PENDING`; no printed
retention or durability result exists.

## BASE-SOCKET-IF-V001

- Socket shank / base receiver: {BASE_SOCKET.shank_diameter:.2f} /
  {BASE_SOCKET.receiver_diameter:.2f} mm.
- Socket index / receiver: {BASE_SOCKET.index_af:.2f} /
  {BASE_SOCKET.receiver_index_af:.2f} mm across flats, 8 directions, 3 mm deep.
- Insertion: {BASE_SOCKET.insertion_depth:.1f} mm.
- Snap candidates: 0.15 / 0.25 / 0.35 mm diametral difference; provisional
  standard {BASE_SOCKET.snap_interference:.2f} mm.
- Coupon receiver diameters for the standard bead:
  {', '.join(f'{value:.2f}' for value in candidate_receiver_diameters())} mm.

## HHD-STEM-PLUG-V001

- Common shank / socket receiver: {STEM_PLUG_IF.shank_diameter:.2f} /
  {STEM_PLUG_IF.receiver_diameter:.2f} mm.
- Common insertion: {STEM_PLUG_IF.shank_length:.1f} mm; entry chamfer
  {STEM_PLUG_IF.receiver_entry_chamfer:.1f}; split {STEM_PLUG_IF.receiver_slot_width:.1f}.
- Coupon receiver candidates:
  {', '.join(f'{value:.2f}' for value in HOLE_DIAMETERS)} mm.
- Rod-side presets 2/3/4/5 mm and a solid custom blank are calibration
  candidates.  No dry-rice-straw-specific adapter is included.

## Fixed-root limitation

There is no individual, group, or all-stem release mechanism.  There are no
leaves, panicles, guide, belt, roller, blade, motor, sensor, or control system.
Powered cutting is not authorized.
"""
    output_path.write_text(report, encoding="utf-8")


def _write_assembly_report(
    preview: GeneratedPreview,
    output_path: Path,
) -> None:
    """Write fixed layout, interference, and full preview results."""

    metrics = preview.preview.metrics
    rows = "\n".join(
        f"| {entry.socket_id} | {entry.base_module} | {entry.x_mm:.1f} | "
        f"{entry.y_mm:.1f} | {entry.tilt_angle_deg:.0f} | "
        f"{entry.tilt_direction_deg:.0f} | {entry.height_class} |"
        for entry in LAYOUT_STANDARD_V001
    )
    report = f"""# {PROJECT_NAME} Standard Assembly Report

## Fixed layout

- 24 unique independent sockets; six per module.
- Minimum centre spacing: {minimum_center_spacing():.3f} mm.
- Radial layout diameter: {maximum_radial_diameter():.3f} mm.
- Radial bands: {radial_band_counts()}.
- Forbidden symmetry checks: {symmetry_matches()}.
- Socket outer-surface minimum clearance:
  {preview.preview.minimum_socket_clearance_mm:.3f} mm.
- Projected upper-stem crossing pairs:
  {preview.preview.projected_stem_crossing_count}.

| Socket | Module | X | Y | Tilt | Direction | Height |
|---|---|---:|---:|---:|---:|---|
{rows}

## Preview

- Mount nominal plates are 105 x 210 x 6 mm.  The left seam tongue produces
  a 110 x 210 x 9 mm functional feature envelope and the locating pins produce
  a 105 x 210 x 9 mm right envelope; the joined footprint remains
  210 x 210 mm and both halves remain A1-safe.
- Bounding box: {metrics.size_x:.3f} x {metrics.size_y:.3f} x
  {metrics.size_z:.3f} mm.
- Component solids: {metrics.solid_count} =
  mount 2 + base 4 + socket 24 + virtual commercial stem 24.
- Heights: {preview.preview.height_counts}.
- Tilts: {preview.preview.tilt_counts}.
- Directions: {preview.preview.direction_counts}.
- File: `preview/{preview.step_path.name}`.
- `printable=false`; no preview STL is generated.
- PNG was not generated and no rendering dependency was added.

This is a fixed-root gathering/holding/transport handling dummy only.  It does
not authorize powered cutting.
"""
    output_path.write_text(report, encoding="utf-8")


def _write_print_assembly_guide(output_path: Path) -> None:
    """Write calibration-first print and assembly instructions."""

    guide = f"""# {PROJECT_NAME} Print and Assembly Guide

All connection values remain `CALIBRATION_PENDING`.

## Mandatory initial print order

1. `HU-H0-HHD-CPN-SOCKET-LOCK_PETG`
2. `HU-H0-HHD-CPN-STEM-PLUG-FIT_PETG`
3. `HU-H0-HHD-GAG-ANGLE_PETG`
4. `HU-H0-HHD-BAS-A_PETG`
5. One each of the 0/10/20/30-degree sockets
6. Two or three selected stem-plug presets
7. Six fixed roots using BASE-A only
8. BASE-B through D only after inspection
9. Remaining sockets only after calibration
10. Full 24-root standard layout

Do not batch-print 24 or more sockets before calibration.

## Assembly sequence

1. Slide the left mount tongues into the right mount pockets.
2. Fix the two-piece mount to the workbench through four M6 holes.
3. Locate BASE-A/B/C/D in their documented quadrants.
4. Engage each mount-mediated locating pin and install four M4 fixings per base.
5. Overlay the matching MAP-A/B/C/D record plate; transfer/check S01-S24.
6. Select the fixed socket angle from the authoritative CSV/JSON.
7. Rotate the octagonal index to the listed 0/45/.../315-degree direction.
8. Fit the selected 6 mm common-shank stem plug without forcing it.
9. Attach the purchased simulated stem to the material-side split sleeve.
10. Use a purchased ruler/stick and the 650/750/850 marker to set virtual length.
11. Check every physical socket ID against S01-S24.
12. Reconcile module, coordinate, angle, direction, and height with both layout files.
13. After the test, use the bottom push-out access and broad tooling; do not pry
    with a sharp blade.
14. Inspect bead wear, split cracks, looseness, mount keys, bolts, and stem damage.

There is no release mechanism.  This fixed-root bench dummy has no blade,
motor, belt, roller, guide, sensor, or powered-cutting authorization.
"""
    output_path.write_text(guide, encoding="utf-8")


def generate_all(
    output_root: str | Path,
) -> tuple[list[GeneratedPart], GeneratedPreview]:
    """Build, export, re-import, and report all HHD-V001 artifacts."""

    validate_all_interfaces()
    root = Path(output_root)
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    _assert_no_3mf(root)
    remove_known_outputs(root, _canonical_output_relative_paths())

    records: list[GeneratedPart] = []
    for definition in PARTS:
        shape = definition.builder()
        metrics = validate_print_bounds(shape, definition.filename_stem)
        step_path = export_step(
            shape,
            root / "step" / "PETG" / f"{definition.filename_stem}.step",
        )
        validate_step_round_trip(step_path)
        stl_path = export_stl(
            shape,
            root / "stl" / "PETG" / f"{definition.filename_stem}.stl",
        )
        records.append(GeneratedPart(definition, metrics, step_path, stl_path))
        print(
            f"OK {definition.filename_stem}: "
            f"{metrics.size_x:.3f} x {metrics.size_y:.3f} x "
            f"{metrics.size_z:.3f} mm, V={metrics.volume_mm3:.3f} mm3",
            flush=True,
        )

    preview_model = build_standard_preview()
    preview_path = export_preview_step(
        preview_model.shape,
        root / "preview" / "HU-H0-HHD_standard_fixed_root.step",
        preview_model.component_solid_count,
    )
    preview = GeneratedPreview(preview_model, preview_path)
    print(
        f"OK standard preview: {preview_model.metrics.size_x:.3f} x "
        f"{preview_model.metrics.size_y:.3f} x "
        f"{preview_model.metrics.size_z:.3f} mm, "
        f"{preview_model.component_solid_count} solids, printable=false",
        flush=True,
    )

    _write_layout_reports(reports_dir)
    _write_dimensions_csv(records, reports_dir / "dimensions.csv")
    _write_manifest(
        records,
        preview,
        reports_dir / "export_manifest.csv",
        root,
    )
    _write_bom(reports_dir / "bill_of_materials.csv")
    _write_interface_report(reports_dir / "interface_report.md")
    _write_assembly_report(preview, reports_dir / "assembly_report.md")
    _write_print_assembly_guide(reports_dir / "print_assembly_guide.md")
    _assert_no_3mf(root)
    return records, preview


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""

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
    records, preview = generate_all(args.out)
    print(
        f"Generated {len(records)} printable parts and one "
        f"{preview.preview.component_solid_count}-solid preview in {args.out}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
