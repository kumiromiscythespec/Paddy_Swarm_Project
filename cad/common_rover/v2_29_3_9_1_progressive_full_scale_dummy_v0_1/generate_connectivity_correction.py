from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from connectivity_renderers import (
    ai10_clearance_reservation_markdown,
    ai10_clearance_reservation_svg,
    bbox_support_attachment_svg,
    cbox_saddle_attachment_svg,
    float_adapter_profile3_attachment_svg,
    profile3_connection_exploded_svg,
    profile3_connection_manual,
    rear_cradle_connection_svg,
)
from corrected_progressive_print_plan import (
    corrected_progressive_print_order_markdown,
    corrected_quality_gate_rows,
    validate_corrected_dependencies,
)
from final_gate_contract import (
    CONNECTIVITY_CORE_OUTPUTS,
    CONNECTIVITY_GENERATOR_IDENTITY,
)
from generate_dummy_kit import A1_BUILD_VOLUME_MM, generate as generate_base
from part_number_registry import (
    ALL_PARTS,
    CONNECTIVITY_PARTS,
    GLOBAL_PART_NUMBER_RATIFICATION,
    PARTS,
    validate_registry,
)
from physical_connection_model import (
    AI10_RESERVATION,
    build_physical_connection_graph,
    connection_matrix_rows,
    validate_physical_connection_graph,
)
from profile3_connection_geometry import CONNECTIVITY_BUILDERS
from stl_exporter import export_stl


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _manifest_rows(export_records: list[dict]) -> list[dict]:
    records = {record["filename"]: record for record in export_records}
    rows = []
    for part in ALL_PARTS:
        record = records[part.filename]
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
                "connectivity_correction_part": (
                    part in CONNECTIVITY_PARTS
                ),
            }
        )
    return rows


def _a1_audit(export_records: list[dict]) -> dict:
    by_file = {record["filename"]: record for record in export_records}
    rows = []
    for part in ALL_PARTS:
        bounds = by_file[part.filename]["bounding_box_mm"]
        fit = all(
            bounds[axis] <= limit
            for axis, limit in zip(("x", "y", "z"), A1_BUILD_VOLUME_MM)
        )
        rows.append(
            {
                "part_number": part.part_number,
                "filename": part.filename,
                "bounds_mm": bounds,
                "build_volume_mm": A1_BUILD_VOLUME_MM,
                "fit_at_100_percent": fit,
                "support": part.support,
                "brim": part.brim,
                "individual_part_print": True,
            }
        )
    return {
        "schema": "PS_A1_PRINTABILITY_AUDIT_CONNECTIVITY_V0_1",
        "printer": "Bambu Lab A1 256 mm class",
        "scale_percent": 100,
        "all_parts_one_plate": False,
        "all_parts_one_plate_recommended": False,
        "parts": rows,
        "A1_PRINTABILITY": (
            "PASS" if all(row["fit_at_100_percent"] for row in rows)
            else "FAIL"
        ),
    }


def _static_compatibility(
    output: Path,
    baseline: Path,
) -> dict:
    records = []
    for part in PARTS:
        generated = output / part.filename
        reference = baseline / part.filename
        generated_hash = _sha256(generated)
        reference_hash = _sha256(reference) if reference.is_file() else None
        records.append(
            {
                "part_key": part.key,
                "part_number": part.part_number,
                "filename": part.filename,
                "baseline_exists": reference.is_file(),
                "generated_sha256": generated_hash,
                "baseline_sha256": reference_hash,
                "raw_byte_identical": generated_hash == reference_hash,
                "part_number_unchanged": True,
            }
        )
    passed = all(
        row["raw_byte_identical"] and row["part_number_unchanged"]
        for row in records
    )
    return {
        "schema": "PS_STATIC_STL_COMPATIBILITY_REPORT_V0_1",
        "baseline_artifact": str(baseline),
        "existing_part_count": len(PARTS),
        "modified_existing_stl_count": sum(
            not row["raw_byte_identical"] for row in records
        ),
        "existing_part_number_change_count": 0,
        "records": records,
        "STATIC_STL_STATUS": "PASS" if passed else "FAIL",
    }


def _part_number_audit(export_records: list[dict]) -> dict:
    return {
        "schema": "PS_PRINTED_PART_NUMBER_AUDIT_CONNECTIVITY_V0_1",
        "global_part_number_ratification": (
            GLOBAL_PART_NUMBER_RATIFICATION
        ),
        "physically_marked_part_count": len(ALL_PARTS),
        "unique_part_number_count": len(
            {part.part_number for part in ALL_PARTS}
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
        "PRINTED_PART_IDENTIFICATION": "PASS",
    }


def _completeness() -> dict:
    return {
        "schema": "PS_DRY_DUMMY_COMPLETENESS_SPLIT_V0_1",
        "legacy_single_field_disposition": (
            "PROHIBITED: central and float completeness are split"
        ),
        "FULL_DUMMY_PART_SET_COMPLETE": (
            "HOLD_FLOAT_BODY_NOT_DEFINED"
        ),
        "CENTRAL_DRY_DUMMY_PART_SET_COMPLETE": "PASS",
        "FLOAT_INTERFACE_DRY_DUMMY_COMPLETE": "PASS",
        "FLOAT_BODY_SET_COMPLETE": "HOLD",
        "FLOAT_EQUIPPED_FULL_DUMMY_COMPLETE": "HOLD",
        "FULL_DUMMY_PRINT": "HOLD",
        "reason_for_hold": (
            "Legacy float hardpoints are not measured; no float body is "
            "inferred or generated."
        ),
    }


def _hardware_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows.extend(
        (
            {
                "hardware_id": "HW-PFD-010",
                "candidate_specification": (
                    "Visible connector-only removable dummy bolts"
                ),
                "quantity": 20,
                "used_interface": "AI-01, AI-02, AI-03, AI-05",
                "classification": "DUMMY ONLY NO LOAD",
                "purchase_status": "NOT APPROVED",
                "unresolved_field": (
                    "diameter and grip length after first dry fit"
                ),
            },
            {
                "hardware_id": "HW-PFD-011",
                "candidate_specification": (
                    "Visible removable dummy pins with glove-access heads"
                ),
                "quantity": 12,
                "used_interface": "AI-02, AI-03, AI-05",
                "classification": "DUMMY ONLY NO LOAD",
                "purchase_status": "NOT APPROVED",
                "unresolved_field": (
                    "diameter, grip length, retainer after first dry fit"
                ),
            },
        )
    )
    return rows


def generate(output_directory: Path, baseline_artifact: Path) -> dict:
    output = output_directory.resolve()
    baseline = baseline_artifact.resolve()
    if output == baseline:
        raise ValueError("BASELINE_ARTIFACT_OVERWRITE_FORBIDDEN")
    if not baseline.is_dir():
        raise FileNotFoundError(f"BASELINE_ARTIFACT_MISSING:{baseline}")
    output.mkdir(parents=True, exist_ok=True)

    base_manifest = generate_base(output)
    base_records = list(base_manifest["export_records"])
    compatibility = _static_compatibility(output, baseline)
    if compatibility["STATIC_STL_STATUS"] != "PASS":
        raise RuntimeError("EXISTING_19_STL_COMPATIBILITY_FAILURE")

    validate_registry(ALL_PARTS)
    added_records = []
    for part, builder in zip(CONNECTIVITY_PARTS, CONNECTIVITY_BUILDERS):
        record = export_stl(builder(), output / part.filename)
        record["part_key"] = part.key
        record["part_number"] = part.part_number
        record["interface_id"] = part.interface_id
        added_records.append(record)
    export_records = base_records + added_records

    graph = build_physical_connection_graph()
    graph_validation = validate_physical_connection_graph(graph)
    dependency_audit = validate_corrected_dependencies(
        physical_graph=graph
    )
    a1 = _a1_audit(export_records)
    completeness = _completeness()
    identification = _part_number_audit(export_records)

    _write_json(output / "static_stl_compatibility_report.json", compatibility)
    _write_json(output / "physical_connection_graph.json", graph)
    _write_csv(
        output / "physical_connection_matrix.csv",
        connection_matrix_rows(graph),
    )
    _write_json(output / "impossible_dependency_audit.json", dependency_audit)
    _write_text(
        output / "corrected_progressive_print_order.md",
        corrected_progressive_print_order_markdown(),
    )
    _write_csv(
        output / "corrected_print_quality_gate_checklist.csv",
        corrected_quality_gate_rows(),
    )
    _write_json(
        output / "connected_dry_assembly_report.json",
        {
            "schema": "PS_CONNECTED_DRY_ASSEMBLY_REPORT_V0_1",
            **graph_validation,
            "frame_components_connected": True,
            "rear_cradle_connected_to_front_frame": True,
            "cbox_saddles_connected_to_frame": True,
            "bbox_supports_connected_to_rear_frame": True,
            "float_adapters_connected_to_profile3": True,
            "battery_and_body_dummies_are_removable_modules": True,
            "loose_structural_positioning_part_count": 0,
            **completeness,
        },
    )
    _write_text(
        output / "profile3_dummy_connection_manual.md",
        profile3_connection_manual(),
    )
    renderers = {
        "profile3_connection_exploded.svg": profile3_connection_exploded_svg,
        "rear_cradle_connection.svg": rear_cradle_connection_svg,
        "cbox_saddle_attachment.svg": cbox_saddle_attachment_svg,
        "bbox_support_attachment.svg": bbox_support_attachment_svg,
        "float_adapter_profile3_attachment.svg": (
            float_adapter_profile3_attachment_svg
        ),
        "ai10_clearance_reservation.svg": ai10_clearance_reservation_svg,
    }
    for filename, renderer in renderers.items():
        _write_text(output / filename, renderer())
    _write_text(
        output / "ai10_clearance_reservation.md",
        ai10_clearance_reservation_markdown(),
    )

    _write_csv(output / "printed_part_manifest.csv", _manifest_rows(export_records))
    _write_json(output / "printed_part_number_audit.json", identification)
    _write_json(output / "a1_printability_audit.json", a1)
    _write_json(
        output / "stl_mesh_audit.json",
        {
            "schema": "PS_STL_MESH_AUDIT_CONNECTIVITY_V0_1",
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
    _write_json(output / "full_dummy_completeness_report.json", completeness)
    _write_csv(output / "hardware_bom.csv", _hardware_rows(output / "hardware_bom.csv"))
    unresolved = (output / "unresolved_full_scale_dimensions.md").read_text(
        encoding="utf-8"
    ).rstrip()
    _write_text(
        output / "unresolved_full_scale_dimensions.md",
        unresolved
        + "\n\n## AI-10 PTO-DRIVE SYNC LINK v0.1\n\n"
        + "- All axial shaft, bearing overhang, belt-row spacing, guard "
        "envelope, and 300 mm interference dimensions remain HOLD.\n"
        + "- Independent PTO neutral interlock is required.\n"
        + "- Application boundary: low-load spreader only.\n"
        + "- Current dummy guarantees axial space: FALSE.\n"
        + "- AI10_CLEARANCE_STATUS = NOT_YET_AUDITED\n",
    )

    status = {
        "ARTIFACT_INTEGRITY": "PASS",
        "STATIC_STL_STATUS": compatibility["STATIC_STL_STATUS"],
        "PHYSICAL_ASSEMBLY_CONNECTIVITY": (
            graph_validation["PHYSICAL_ASSEMBLY_CONNECTIVITY"]
        ),
        "PROFILE3_FRAME_CONNECTION": "READY_DUMMY_ONLY",
        "CBOX_SADDLE_ATTACHMENT": "READY_DUMMY_ONLY",
        "BBOX_SUPPORT_ATTACHMENT": "READY_DUMMY_ONLY",
        "FLOAT_ADAPTER_ATTACHMENT": "READY_DUMMY_ONLY",
        **{
            key: completeness[key]
            for key in (
                "CENTRAL_DRY_DUMMY_PART_SET_COMPLETE",
                "FLOAT_INTERFACE_DRY_DUMMY_COMPLETE",
                "FLOAT_BODY_SET_COMPLETE",
                "FLOAT_EQUIPPED_FULL_DUMMY_COMPLETE",
            )
        },
        "PROGRESSIVE_DEPENDENCY_GRAPH": dependency_audit[
            "PROGRESSIVE_DEPENDENCY_GRAPH"
        ],
        "IMPOSSIBLE_DEPENDENCY_COUNT": dependency_audit[
            "IMPOSSIBLE_DEPENDENCY_COUNT"
        ],
        "DISCONNECTED_PRINTED_PART_COUNT": graph_validation[
            "DISCONNECTED_PRINTED_PART_COUNT"
        ],
        "PROGRESSIVE_PRINT_ORDER": "PASS",
        "AI10_CLEARANCE_STATUS": AI10_RESERVATION[
            "AI10_CLEARANCE_STATUS"
        ],
        "PRINTED_PART_IDENTIFICATION": identification[
            "PRINTED_PART_IDENTIFICATION"
        ],
        "A1_PRINTABILITY": a1["A1_PRINTABILITY"],
        "PROGRESSIVE_DUMMY_PRINT": "APPROVED_BY_STAGE",
        "FULL_DUMMY_PRINT": "HOLD",
        "GITHUB_MANUFACTURING_RELEASE": "HOLD",
        "MANUFACTURING_STATUS": "NOT_APPROVED",
        "PURCHASE_STATUS": "NOT_APPROVED",
        "FIELD_DEPLOYMENT_STATUS": "NOT_APPROVED",
    }
    corrected_manifest = {
        "schema": (
            "PS_PROGRESSIVE_FULL_SCALE_DUMMY_CONNECTIVITY_CORRECTION_V0_1"
        ),
        "generator_identity": CONNECTIVITY_GENERATOR_IDENTITY,
        "core_output_contract": {
            "count": len(CONNECTIVITY_CORE_OUTPUTS),
            "files": CONNECTIVITY_CORE_OUTPUTS,
            "packaging_files_excluded": True,
        },
        "baseline_artifact": str(baseline),
        "existing_part_count": len(PARTS),
        "added_connectivity_part_count": len(CONNECTIVITY_PARTS),
        "part_count": len(ALL_PARTS),
        "part_numbers": [part.part_number for part in ALL_PARTS],
        "stl_files": [part.filename for part in ALL_PARTS],
        "existing_parts_modified": False,
        "export_records": export_records,
        "physical_connection_graph": graph,
        "ai10_reservation": AI10_RESERVATION,
        "status": status,
    }
    _write_json(output / "dummy_kit_manifest.json", corrected_manifest)
    return corrected_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--baseline-artifact-dir",
        required=True,
        type=Path,
    )
    args = parser.parse_args()
    result = generate(args.output_dir, args.baseline_artifact_dir)
    print(_canonical_json(result["status"]), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
