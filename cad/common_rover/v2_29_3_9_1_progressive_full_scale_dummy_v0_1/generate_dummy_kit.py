from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from html import escape
import json
from pathlib import Path
from typing import Iterable

from assembly_bom import (
    assembly_sequence_records,
    hardware_bom_records,
    printed_bom_records,
)
from authority_adapter import (
    controlled_dimensions,
    load_context,
    profile_input_audit,
    rear_support_input_audit,
    source_integrity_report,
    validate_rear_support_audit,
)
from dummy_component_registry import (
    COMPONENTS,
    load_builder,
    validate_component_registry,
)
from float_width_audit import build_float_width_audit
from final_gate_contract import (
    BASE_CORE_OUTPUTS,
    BASE_GENERATOR_IDENTITY,
)
from part_number_registry import (
    GLOBAL_PART_NUMBER_RATIFICATION,
    PARTS,
    PART_BY_KEY,
    validate_registry,
)
from progressive_print_plan import (
    PRINT_STEPS,
    progressive_print_markdown,
    quality_gate_rows,
    validate_print_order,
)
from stl_exporter import export_stl


A1_BUILD_VOLUME_MM = (256.0, 256.0, 256.0)


def _canonical_json(value: object) -> str:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_json(path: Path, value: object) -> None:
    _write_text(path, _canonical_json(value))


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"EMPTY_CSV:{path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _part_manifest_rows(export_records: list[dict]) -> list[dict]:
    export_by_file = {record["filename"]: record for record in export_records}
    rows = []
    for part in PARTS:
        record = export_by_file[part.filename]
        bounds = record["bounding_box_mm"]
        rows.append(
            {
                "part_number": part.part_number,
                "revision": "R00",
                "part_key": part.key,
                "title": part.title,
                "stl_filename": part.filename,
                "quantity": 1,
                "interface_id": part.interface_id,
                "orientation_marking": part.orientation_marking,
                "classification_marking": part.classification_marking,
                "physical_marking": record["marking"]["physical_marking"],
                "marking_surface": part.marking_surface,
                "marking_verified": record["marking"]["marking_verified"],
                "floating_text_solids": record["marking"][
                    "floating_text_solid_count"
                ],
                "scale_percent": 100,
                "material": part.material,
                "print_orientation": part.print_orientation,
                "support": part.support,
                "brim": part.brim,
                "bounding_x_mm": bounds["x"],
                "bounding_y_mm": bounds["y"],
                "bounding_z_mm": bounds["z"],
                "a1_printable": all(
                    bounds[axis] <= limit
                    for axis, limit in zip(
                        ("x", "y", "z"), A1_BUILD_VOLUME_MM
                    )
                ),
                "stl_sha256": record["stl_sha256"],
                "optional_profile_dummy": part.optional_dummy,
            }
        )
    return rows


def _a1_audit(export_records: list[dict]) -> dict:
    records = []
    for part, record in zip(PARTS, export_records):
        bounds = record["bounding_box_mm"]
        fit = all(
            bounds[axis] <= limit
            for axis, limit in zip(("x", "y", "z"), A1_BUILD_VOLUME_MM)
        )
        long_rail = part.key.startswith("fpb_rail_")
        records.append(
            {
                "part_number": part.part_number,
                "filename": part.filename,
                "bounds_mm": bounds,
                "build_volume_mm": A1_BUILD_VOLUME_MM,
                "fit_at_100_percent": fit,
                "support": part.support,
                "brim": part.brim,
                "warping_risk": "HIGH" if long_rail else (
                    "HIGH" if max(bounds.values()) >= 180.0 else "MEDIUM"
                ),
                "bed_clearance_note": (
                    "232 mm length leaves 24 mm nominal class margin; use 8 mm "
                    "brim only after slicer confirms placement"
                    if long_rail
                    else "standard individual-part placement"
                ),
            }
        )
    return {
        "schema": "PS_A1_PRINTABILITY_AUDIT_V0_1",
        "printer": "Bambu Lab A1 256 mm class",
        "scale_percent": 100,
        "all_parts_one_plate": False,
        "all_parts_one_plate_recommended": False,
        "parts": records,
        "A1_PRINTABILITY": (
            "PASS" if all(row["fit_at_100_percent"] for row in records)
            else "FAIL"
        ),
    }


def _assembly_model() -> dict:
    context = load_context(validate_seed_geometry=False)
    authority = controlled_dimensions(context)
    components = []
    for envelope in context.parameters.components:
        components.append(
            {
                "component_id": envelope.component_id,
                "minimum_xyz_mm": envelope.minimum,
                "maximum_xyz_mm": envelope.maximum,
                "dimensions_xyz_mm": envelope.dimensions,
                "source": envelope.source_path,
            }
        )
    return {
        "schema": "PS_FULL_DUMMY_ASSEMBLY_MODEL_V0_1",
        "coordinate_system": authority["coordinate"],
        "authority_components": components,
        "dummy_interfaces": {
            "CBOX": {
                "supports": [
                    "cbox_saddle_left",
                    "cbox_saddle_right",
                    "rear_cradle_dummy_part_1",
                    "rear_cradle_dummy_part_2",
                ],
                "primary_structural_claim": False,
            },
            "BBOX": {
                "supports": [
                    "bbox_support_front",
                    "bbox_support_rear",
                ],
                "supported_by_cbox": False,
                "independent_support_path_visible": True,
                "primary_structural_claim": False,
            },
            "CBOX_BBOX_ALIGNMENT": {
                "parts": [
                    "core_alignment_key",
                    "anti_separation_lock_carrier",
                ],
                "connector_structural_load": False,
                "primary_lock": "REMOVABLE_METAL_PIN_CANDIDATE",
            },
            "FLOAT": {
                "lower_adapter_host": "BOTTOM_SLOT",
                "adapter_zone_y_mm": authority["lower_adapter_left"][
                    "zone_interval"
                ],
                "receiver_positive_stop": True,
                "pin_alignment_window": True,
                "printed_cover_primary": False,
            },
        },
        "reserved_authority": {
            "upper_torque_mount": authority["upper_torque_mount"][
                "zone_id"
            ],
            "output_zone_left_y_mm": authority["output_bridge_left"][
                "zone_interval"
            ],
            "output_zone_right_y_mm": authority["output_bridge_right"][
                "zone_interval"
            ],
            "front_corner_reserved_y_mm": authority[
                "front_joint_reserved_interval_y_mm"
            ],
            "direct_rail_hole_policy": authority[
                "direct_rail_hole_policy"
            ],
        },
    }


def _manual() -> str:
    printed = printed_bom_records()
    hardware = hardware_bom_records()
    sequence = assembly_sequence_records()
    lines = [
        "# Full-scale assembly dummy manual",
        "",
        "Classification: visual/placement/fit dummy only. No load, waterproof, "
        "electrical, mobility, field, or manufacturing approval is implied.",
        "",
        "## Holds before assembly",
        "",
        "- Use printed PROFILE-3 envelope rails only; supplier T-slot geometry is HOLD.",
        "- Rear BBOX supports are independent visual paths marked NOT STRUCTURAL.",
        "- Use no real battery and carry no structural load in a box connector.",
        "- FLOAT-2 is a visual overlap; operational width remains HOLD.",
        "- Printed retainer cover is SECONDARY ONLY; a metal pin is the candidate primary lock.",
        "",
        "## Printed parts",
        "",
        "| Part number | Qty | File | Interface | Orientation |",
        "|---|---:|---|---|---|",
    ]
    for row in printed:
        lines.append(
            f"| {row['part_number']} | {row['quantity']} | "
            f"`{row['filename']}` | {row['interface_id']} | "
            f"{row['orientation_marking']} |"
        )
    lines.extend(
        (
            "",
            "## Hardware candidates",
            "",
            "| Hardware ID | Qty | Candidate | Interface | Class | Status |",
            "|---|---:|---|---|---|---|",
        )
    )
    for row in hardware:
        lines.append(
            f"| {row['hardware_id']} | {row['quantity']} | "
            f"{row['candidate_specification']} | {row['used_interface']} | "
            f"{row['classification']} | {row['purchase_status']} |"
        )
    lines.extend(("", "## Assembly steps", ""))
    for row in sequence:
        parts = [
            PART_BY_KEY[key.strip()]
            for key in row["part_keys"].split(",")
        ]
        part_numbers = ", ".join(part.part_number for part in parts)
        lines.extend(
            (
                f"### Step {row['step']} — {part_numbers}",
                "",
                f"- Part number(s): {part_numbers}",
                f"- Quantity: {row['quantity']}",
                f"- Orientation: {row['orientation']}",
                f"- Interface ID: {row['interface_id']}",
                f"- Insertion direction: {row['insertion_direction']}",
                f"- Fastener: {row['fastener']}",
                f"- Visible verification point: {row['visible_verification']}",
                "",
            )
        )
    lines.extend(
        (
            "## Final dry-assembly gate",
            "",
            "Confirm every complete part number remains visible, the BBOX has a "
            "support path independent of CBOX, lower adapters are under the "
            "BOTTOM_SLOT zones, pin states remain visible, and the legacy float "
            "visual arrangement is not represented as operationally validated.",
            "",
        )
    )
    return "\n".join(lines)


def _disassembly_manual() -> str:
    sequence = list(reversed(assembly_sequence_records()))
    lines = [
        "# Full-scale assembly dummy disassembly manual",
        "",
        "Unload the dummy completely. No person may support, sit on, energize, "
        "or tow it. Preserve accepted printed parts for reuse.",
        "",
    ]
    for index, row in enumerate(sequence, start=1):
        parts = [
            PART_BY_KEY[key.strip()]
            for key in row["part_keys"].split(",")
        ]
        part_numbers = ", ".join(part.part_number for part in parts)
        if "pin_retainer_cover" in row["part_keys"]:
            action = (
                "Remove the SECONDARY ONLY cover first; then remove the R-pin "
                "and primary metal-pin candidate while its window is visible."
            )
        elif row["interface_id"] in ("AI-04", "AI-06"):
            action = (
                "Expose and remove metal-pin candidates before withdrawing the "
                "printed positioning parts opposite the insertion direction."
            )
        else:
            action = (
                "Remove temporary fasteners, support the lightweight dummy by "
                "hand, and withdraw opposite the documented insertion direction."
            )
        lines.extend(
            (
                f"## Disassembly {index:02d} — {part_numbers}",
                "",
                f"- Quantity: {row['quantity']}",
                f"- Interface ID: {row['interface_id']}",
                f"- Orientation reference: {row['orientation']}",
                f"- Action: {action}",
                f"- Verification: {row['visible_verification']}",
                "- Storage: retain the accepted final-use part with its marking visible.",
                "",
            )
        )
    lines.extend(
        (
            "After disassembly, inspect for cracks, permanent warp, unreadable "
            "markings, enlarged bores, or lost positive stops. A failed part "
            "locks all dependent reprints until corrected.",
            "",
        )
    )
    return "\n".join(lines)


def _unresolved_dimensions_markdown(
    profile: dict, rear: dict, float_audit: dict
) -> str:
    return "\n".join(
        (
            "# Unresolved full-scale dimensions",
            "",
            "Unresolved values are not silently converted into manufacturing "
            "dimensions. This kit remains a full-scale visual/fit dummy.",
            "",
            "## Aluminum profile — HOLD",
            "",
            *(
                f"- {field}"
                for field in profile["missing_supplier_fields"]
            ),
            "- Exact supplier/manufacturer and SKU",
            "- T-nut engagement and tolerance",
            "- Bolt grade, length, torque, locking, and corrosion system",
            "",
            "## Rear BBOX support — HOLD",
            "",
            *(f"- {field}" for field in rear["unresolved_fields"]),
            "",
            "## Float operational width — HOLD",
            "",
            "- Bracket production thickness",
            "- Slide production clearance",
            "- Mud clearance",
            "- Left/right operating inclination",
            "- Manufacturing tolerance distribution",
            "- Printed wall production tolerance",
            "- Legacy float hardpoint measurement",
            f"- Selected visual option: {float_audit['selected_option']}",
            "",
            "## Fit candidates — verify progressively",
            "",
            "- CBOX dummy-corner saddle clearance: 0.40 mm candidate",
            "- Float slide clearance: 0.40 mm candidate",
            "- Removable metal-pin bore: 6.30 mm candidate for a 6 mm-class pin",
            "- Alignment-key edge distances and box hardpoints",
            "- Glove-access clearance with selected real fasteners",
            "",
            "## Release holds",
            "",
            "- GLOBAL_PART_NUMBER_RATIFICATION = HOLD",
            "- FLOAT_FULL_SCALE_PRINT = HOLD",
            "- FULL_DUMMY_PRINT = HOLD",
            "- GITHUB_MANUFACTURING_RELEASE = HOLD",
            "- PURCHASE_STATUS = NOT_APPROVED",
            "- STRUCTURAL_STRENGTH_STATUS = NOT_VALIDATED",
            "",
        )
    )


def _svg_document(
    title: str,
    width: int,
    height: int,
    body: Iterable[str],
) -> str:
    return "\n".join(
        (
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
            "<style>",
            "text{font-family:Arial,sans-serif;fill:#17212b}"
            ".title{font-size:28px;font-weight:700}"
            ".label{font-size:15px;font-weight:600}"
            ".small{font-size:12px}"
            ".frame{fill:#aeb8c2;stroke:#35424e;stroke-width:2}"
            ".cbox{fill:#72b7b2;stroke:#215b57;stroke-width:2}"
            ".bbox{fill:#e5b567;stroke:#79521c;stroke-width:2}"
            ".battery{fill:#d18b9b;stroke:#743645;stroke-width:2}"
            ".printed{fill:#f2df54;stroke:#716400;stroke-width:2}"
            ".float{fill:#76a9dc;stroke:#245682;stroke-width:2}"
            ".hold{fill:#fff3cd;stroke:#9a7200;stroke-width:2;stroke-dasharray:8 5}"
            ".arrow{stroke:#313b44;stroke-width:2;fill:none;marker-end:url(#arrow)}",
            "</style>",
            '<defs><marker id="arrow" markerWidth="10" markerHeight="7" '
            'refX="9" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" '
            'fill="#313b44"/></marker></defs>',
            f'<text x="30" y="42" class="title">{escape(title)}</text>',
            *body,
            "</svg>",
            "",
        )
    )


def _full_dummy_top_svg(authority: dict, float_audit: dict) -> str:
    # Exact authority X/Y placement is drawn at 1.4 px/mm around a fixed origin.
    ox, oy, scale = 500.0, 400.0, 1.4

    def rect(x1, y1, x2, y2, cls, label):
        px = ox - x2 * scale
        py = oy - y2 * scale
        w = (x2 - x1) * scale
        h = (y2 - y1) * scale
        return (
            f'<rect x="{px:.1f}" y="{py:.1f}" width="{w:.1f}" '
            f'height="{h:.1f}" class="{cls}"/>'
            f'<text x="{px + 6:.1f}" y="{py + 18:.1f}" '
            f'class="small">{escape(label)}</text>'
        )

    body = [
        rect(69, -232, 89, 0, "frame", "RAIL L"),
        rect(-89, -232, -69, 0, "frame", "RAIL R"),
        rect(-69, -232, 69, -212, "frame", "FRONT XMEMBER"),
        rect(-65, -140, 65, 0, "cbox", "CBOX 130x140"),
        rect(-75, 0, 75, 220, "bbox", "BBOX 150x220"),
        rect(-62.5, 20, 62.5, 200, "battery", "BATTERY 125x180 envelope"),
        '<rect x="346" y="228" width="308" height="18" class="printed"/>',
        '<text x="356" y="242" class="small">INDEPENDENT BBOX SUPPORT PATH</text>',
        '<rect x="268" y="528" width="66" height="90" class="float"/>',
        '<rect x="666" y="528" width="66" height="90" class="float"/>',
        '<text x="250" y="640" class="small">FLOAT-2 visual overlap; width HOLD</text>',
        f'<text x="30" y="675" class="label">Audited width: '
        f'{float_audit["options"]["FLOAT-2"]["audited_width_mm"]} mm; '
        f'registered {authority["registered_width_mm"]} mm; hard '
        f'{authority["hard_limit_width_mm"]} mm</text>',
    ]
    return _svg_document("Full dummy top view — authority placement", 1000, 700, body)


def _full_dummy_side_svg(context) -> str:
    ox, oy, scale = 300.0, 610.0, 1.35
    styles = {
        "V22939-CBOX": "cbox",
        "V22939-BBOX": "bbox",
        "V22939-BATTERY-CASSETTE": "battery",
    }
    body = []
    for component in context.parameters.components:
        if component.component_id.startswith("V22939-FPB"):
            cls = "frame"
        else:
            cls = styles.get(component.component_id, "printed")
        y1, z1 = component.minimum[1], component.minimum[2]
        y2, z2 = component.maximum[1], component.maximum[2]
        x = ox + y1 * scale
        y = oy - z2 * scale
        w = (y2 - y1) * scale
        h = (z2 - z1) * scale
        body.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
            f'height="{h:.1f}" class="{cls}"/>'
        )
        body.append(
            f'<text x="{x + 5:.1f}" y="{y + 17:.1f}" class="small">'
            f'{escape(component.component_id)}</text>'
        )
    body.extend(
        (
            '<rect x="596" y="570" width="300" height="22" class="hold"/>',
            '<text x="606" y="586" class="small">BBOX independent dummy support — NO LOAD</text>',
            '<text x="30" y="670" class="label">-Y FRONT ← longitudinal → +Y REAR; +Z UP</text>',
        )
    )
    return _svg_document("Full dummy side view", 1000, 700, body)


def _full_dummy_front_svg(authority: dict) -> str:
    frame_width = authority["bare_frame_width_mm"]
    registered = authority["registered_width_mm"]
    hard = authority["hard_limit_width_mm"]
    body = [
        '<line x1="500" y1="80" x2="500" y2="620" stroke="#999" stroke-dasharray="6 4"/>',
        '<rect x="233" y="500" width="534" height="60" class="frame"/>',
        '<text x="405" y="535" class="label">BARE FRAME 178 mm</text>',
        '<rect x="305" y="250" width="390" height="250" class="bbox"/>',
        '<text x="425" y="280" class="label">BBOX 150 mm</text>',
        '<rect x="331" y="360" width="338" height="140" class="cbox"/>',
        '<text x="430" y="390" class="label">CBOX 130 mm</text>',
        '<rect x="220" y="510" width="70" height="100" class="float"/>',
        '<rect x="710" y="510" width="70" height="100" class="float"/>',
        f'<text x="40" y="650" class="small">frame={frame_width} mm; '
        f'registered={registered} mm (target category); hard={hard} mm '
        f'(different category)</text>',
    ]
    return _svg_document("Full dummy front view — width categories", 1000, 700, body)


def _exploded_svg() -> str:
    body = [
        '<rect x="110" y="500" width="700" height="30" class="frame"/>',
        '<text x="125" y="520" class="label">PROFILE-3 FRAME DUMMIES</text>',
        '<rect x="210" y="410" width="500" height="35" class="printed"/>',
        '<text x="225" y="433" class="label">CBOX SADDLES + REAR CRADLE</text>',
        '<rect x="290" y="300" width="340" height="75" class="cbox"/>',
        '<text x="305" y="330" class="label">PS-PR-A1-BOX-301-R00 CBOX</text>',
        '<rect x="180" y="215" width="560" height="35" class="printed"/>',
        '<text x="195" y="238" class="label">INDEPENDENT FRONT/REAR BBOX SUPPORTS</text>',
        '<rect x="260" y="95" width="400" height="85" class="bbox"/>',
        '<text x="275" y="128" class="label">PS-PR-A1-BOX-302-R00 BBOX</text>',
        '<path d="M460 495 L460 452" class="arrow"/>',
        '<path d="M460 405 L460 380" class="arrow"/>',
        '<path d="M460 295 L460 255" class="arrow"/>',
        '<path d="M460 210 L460 185" class="arrow"/>',
        '<rect x="35" y="360" width="130" height="65" class="float"/>',
        '<rect x="755" y="360" width="130" height="65" class="float"/>',
        '<text x="32" y="450" class="small">FLOAT INTERFACE L</text>',
        '<text x="752" y="450" class="small">FLOAT INTERFACE R</text>',
        '<text x="40" y="650" class="label">Arrows are assembly direction only; no structural/load approval.</text>',
    ]
    return _svg_document("Exploded progressive full dummy", 920, 680, body)


def _part_number_map_svg() -> str:
    body = []
    for index, part in enumerate(PARTS):
        column = index % 3
        row = index // 3
        x = 30 + column * 510
        y = 70 + row * 130
        body.extend(
            (
                f'<rect x="{x}" y="{y}" width="470" height="105" '
                'rx="8" class="printed"/>',
                f'<text x="{x + 14}" y="{y + 27}" class="label">'
                f'{escape(part.part_number)}</text>',
                f'<text x="{x + 14}" y="{y + 50}" class="small">'
                f'{escape(part.filename)}</text>',
                f'<text x="{x + 14}" y="{y + 70}" class="small">'
                f'{escape(part.marking_surface)}</text>',
                f'<text x="{x + 14}" y="{y + 90}" class="small">'
                f'{escape(part.orientation_marking)} | '
                f'{escape(part.interface_id)}</text>',
            )
        )
    return _svg_document("Physical part-number location map", 1560, 1020, body)


def _dependency_svg() -> str:
    body = []
    for index, step in enumerate(PRINT_STEPS):
        row = index
        x = 70 if row % 2 == 0 else 820
        y = 75 + row * 64
        part = PART_BY_KEY[step.part_key]
        body.extend(
            (
                f'<rect x="{x}" y="{y}" width="650" height="44" '
                'rx="8" class="printed"/>',
                f'<text x="{x + 12}" y="{y + 19}" class="small">'
                f'PRINT {step.print_number:02d} {escape(part.part_number)}</text>',
                f'<text x="{x + 12}" y="{y + 36}" class="small">'
                f'PASS P0-P4 → {escape(step.next_part_unlocked)}</text>',
            )
        )
        if index < len(PRINT_STEPS) - 1:
            nx = 70 if (row + 1) % 2 == 0 else 820
            ny = 75 + (row + 1) * 64
            body.append(
                f'<path d="M{x + 325} {y + 44} L{nx + 325} {ny}" '
                'class="arrow"/>'
            )
    body.append(
        '<text x="40" y="1335" class="label">FAIL stops every downstream print. Mirror parts require first-side PASS.</text>'
    )
    return _svg_document(
        "Print-to-assembly dependency — one final-use part per step",
        1540,
        1370,
        body,
    )


def _completeness_report(
    export_records: list[dict],
    a1: dict,
    float_audit: dict,
) -> dict:
    checks = {
        "structural_frame_representation": all(
            key in {part.key for part in PARTS}
            for key in (
                "fpb_rail_left_dummy",
                "fpb_rail_right_dummy",
                "fpb_front_crossmember_dummy",
                "rear_cradle_dummy_part_1",
                "rear_cradle_dummy_part_2",
            )
        ),
        "cbox_dummy": "current_cbox_dummy" in PART_BY_KEY,
        "bbox_dummy": "current_bbox_dummy" in PART_BY_KEY,
        "battery_cassette_dummy": "battery_cassette_dummy" in PART_BY_KEY,
        "cbox_positioning_parts": all(
            key in PART_BY_KEY
            for key in ("cbox_saddle_left", "cbox_saddle_right")
        ),
        "bbox_independent_support_representation": all(
            key in PART_BY_KEY
            for key in ("bbox_support_front", "bbox_support_rear")
        ),
        "cbox_bbox_alignment": all(
            key in PART_BY_KEY
            for key in (
                "core_alignment_key",
                "anti_separation_lock_carrier",
            )
        ),
        "float_adapter": all(
            key in PART_BY_KEY
            for key in (
                "lower_float_adapter_left",
                "lower_float_adapter_right",
            )
        ),
        "float_receiver": all(
            key in PART_BY_KEY
            for key in (
                "float_slide_receiver_left",
                "float_slide_receiver_right",
            )
        ),
        "pin_lock_representation": "pin_retainer_cover" in PART_BY_KEY,
        "visible_assembly_marks": all(
            record["marking"]["marking_verified"]
            for record in export_records
        ),
        "physical_part_numbers": len(export_records) == len(PARTS),
        "full_bom": bool(hardware_bom_records()),
        "assembly_manual": True,
        "progressive_print_order": validate_print_order()["status"] == "PASS",
        "all_required_fastener_candidates": len(
            hardware_bom_records()
        ) >= 9,
        "width_audit": float_audit["FLOAT_WIDTH_STATUS"] == "HOLD",
        "a1_printability_audit": a1["A1_PRINTABILITY"] == "PASS",
        "not_coupon_only": len(PARTS) == 19,
    }
    complete = all(checks.values())
    return {
        "schema": "PS_FULL_DUMMY_COMPLETENESS_REPORT_V0_1",
        "checks": checks,
        "printed_part_count": len(PARTS),
        "FULL_DUMMY_PART_SET_COMPLETE": "PASS" if complete else "FAIL",
        "FULL_DUMMY_PRINT": "HOLD",
        "reason_for_hold": (
            "Part set is complete as a dummy kit, but supplier profile, "
            "structural rear support, float operational width, and hardware "
            "selection remain unresolved."
        ),
    }


def generate(output_directory: Path) -> dict:
    output = output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    context = load_context(validate_seed_geometry=True)
    authority = controlled_dimensions(context)
    source_report = source_integrity_report(context)
    profile = profile_input_audit(context)
    rear = rear_support_input_audit()
    float_audit = build_float_width_audit()

    validate_registry()
    validate_component_registry()
    validate_print_order()
    validate_rear_support_audit(rear)

    export_records = []
    for component in COMPONENTS:
        geometry = load_builder(component)()
        record = export_stl(geometry, output / component.part.filename)
        record["part_key"] = component.key
        record["part_number"] = component.part.part_number
        record["interface_id"] = component.part.interface_id
        export_records.append(record)

    manifest_rows = _part_manifest_rows(export_records)
    a1 = _a1_audit(export_records)
    assembly_model = _assembly_model()
    completeness = _completeness_report(export_records, a1, float_audit)

    _write_csv(output / "printed_part_manifest.csv", manifest_rows)
    _write_csv(output / "hardware_bom.csv", hardware_bom_records())
    _write_csv(
        output / "print_quality_gate_checklist.csv",
        quality_gate_rows(),
    )
    _write_text(
        output / "progressive_print_order.md",
        progressive_print_markdown(),
    )
    _write_text(output / "full_dummy_assembly_manual.md", _manual())
    _write_text(
        output / "full_dummy_disassembly_manual.md",
        _disassembly_manual(),
    )
    _write_text(
        output / "unresolved_full_scale_dimensions.md",
        _unresolved_dimensions_markdown(profile, rear, float_audit),
    )

    part_audit = {
        "schema": "PS_PRINTED_PART_NUMBER_AUDIT_V0_1",
        "format_source": "docs/3d_print_pack_README.md",
        "global_part_number_ratification": (
            GLOBAL_PART_NUMBER_RATIFICATION
        ),
        "physically_marked_part_count": len(PARTS),
        "unique_part_number_count": len(
            {part.part_number for part in PARTS}
        ),
        "all_geometry_markings_verified": all(
            record["marking"]["marking_verified"]
            for record in export_records
        ),
        "floating_text_solid_count": sum(
            record["marking"]["floating_text_solid_count"]
            for record in export_records
        ),
        "records": [
            {
                "part_key": record["part_key"],
                "part_number": record["part_number"],
                "filename": record["filename"],
                **record["marking"],
                "stl_sha256": record["stl_sha256"],
            }
            for record in export_records
        ],
    }
    _write_json(output / "printed_part_number_audit.json", part_audit)
    _write_json(output / "float_width_audit.json", float_audit)
    _write_json(output / "profile_input_audit.json", profile)
    _write_json(output / "rear_bbox_support_audit.json", rear)
    _write_json(output / "a1_printability_audit.json", a1)
    _write_json(output / "assembly_model.json", assembly_model)
    _write_json(
        output / "stl_mesh_audit.json",
        {
            "schema": "PS_STL_MESH_AUDIT_V0_1",
            "status": (
                "PASS"
                if all(
                    record["mesh_audit"]["status"] == "PASS"
                    for record in export_records
                )
                else "FAIL"
            ),
            "records": [
                {
                    "filename": record["filename"],
                    "part_number": record["part_number"],
                    **record["mesh_audit"],
                }
                for record in export_records
            ],
        },
    )
    _write_json(
        output / "full_dummy_completeness_report.json",
        completeness,
    )
    _write_json(
        output / "source_integrity_report.json",
        source_report,
    )

    _write_text(
        output / "exploded_full_dummy.svg",
        _exploded_svg(),
    )
    _write_text(
        output / "full_dummy_top.svg",
        _full_dummy_top_svg(authority, float_audit),
    )
    _write_text(
        output / "full_dummy_side.svg",
        _full_dummy_side_svg(context),
    )
    _write_text(
        output / "full_dummy_front.svg",
        _full_dummy_front_svg(authority),
    )
    _write_text(
        output / "part_number_location_map.svg",
        _part_number_map_svg(),
    )
    _write_text(
        output / "print_to_assembly_dependency.svg",
        _dependency_svg(),
    )

    kit_manifest = {
        "schema": "PS_PROGRESSIVE_FULL_SCALE_DUMMY_KIT_V0_1",
        "generator_identity": BASE_GENERATOR_IDENTITY,
        "core_output_contract": {
            "count": len(BASE_CORE_OUTPUTS),
            "files": BASE_CORE_OUTPUTS,
            "packaging_files_excluded": True,
        },
        "source_integrity": source_report,
        "authority_dimensions": authority,
        "architecture": {
            "profile": "PROFILE-3_DUMMY_ENVELOPE_ONLY",
            "bbox_support": "INDEPENDENT_FRONT_REAR_DUMMY_SUPPORTS",
            "float": "LEGACY_COMPATIBLE_ADAPTER_KIT_FLOAT2_VISUAL_HOLD",
            "connector_structural_load": False,
            "thumb_latch_primary": False,
            "direct_rail_holes": False,
        },
        "part_count": len(PARTS),
        "part_numbers": [part.part_number for part in PARTS],
        "stl_files": [part.filename for part in PARTS],
        "export_records": export_records,
        "status": {
            "DESIGN_ANALYSIS_PROCESS": "PASS_WITH_HOLD",
            "PROGRESSIVE_FULL_SCALE_DUMMY_STATUS": "PASS_WITH_HOLD",
            "FULL_DUMMY_PART_SET_COMPLETE": completeness[
                "FULL_DUMMY_PART_SET_COMPLETE"
            ],
            "CURRENT_CBOX_DUMMY": "READY",
            "CURRENT_BBOX_DUMMY": "READY",
            "BATTERY_CASSETTE_DUMMY": "READY",
            "CBOX_SADDLE_SET": "READY",
            "BBOX_SUPPORT_SET": "READY",
            "FLOAT_INTERFACE_SET": "READY",
            "FLOAT_WIDTH_STATUS": "HOLD",
            "FRAME_PROFILE_STATUS": "DUMMY_ENVELOPE_ONLY",
            "PHYSICALLY_MARKED_PART_COUNT": len(PARTS),
            "UNIQUE_PART_NUMBER_COUNT": len(
                {part.part_number for part in PARTS}
            ),
            "PROGRESSIVE_PRINT_ORDER": "PASS",
            "A1_PRINTABILITY": a1["A1_PRINTABILITY"],
            "PROGRESSIVE_DUMMY_PRINT": "APPROVED_BY_STAGE",
            "FULL_DUMMY_PRINT": "HOLD",
            "GITHUB_MANUFACTURING_RELEASE": "HOLD",
            "MANUFACTURING_STATUS": "NOT_APPROVED",
            "PURCHASE_STATUS": "NOT_APPROVED",
            "FIELD_DEPLOYMENT_STATUS": "NOT_APPROVED",
            "WATERPROOF_STATUS": "NOT_VALIDATED",
            "STRUCTURAL_STRENGTH_STATUS": "NOT_VALIDATED",
        },
    }
    _write_json(output / "dummy_kit_manifest.json", kit_manifest)
    return kit_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    result = generate(args.output_dir)
    print(_canonical_json(result["status"]), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
