from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from corrected_progressive_print_plan import validate_corrected_dependencies
from part_number_registry import ALL_PARTS, CONNECTIVITY_PARTS, PARTS
from physical_connection_model import validate_physical_connection_graph
from stl_exporter import audit_stl


REQUIRED_NEW_ARTIFACTS = (
    "physical_connection_graph.json",
    "physical_connection_matrix.csv",
    "impossible_dependency_audit.json",
    "corrected_progressive_print_order.md",
    "corrected_print_quality_gate_checklist.csv",
    "connected_dry_assembly_report.json",
    "profile3_dummy_connection_manual.md",
    "profile3_connection_exploded.svg",
    "rear_cradle_connection.svg",
    "cbox_saddle_attachment.svg",
    "bbox_support_attachment.svg",
    "float_adapter_profile3_attachment.svg",
    "ai10_clearance_reservation.md",
    "static_stl_compatibility_report.json",
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_completeness_status(report: dict) -> list[str]:
    blockers = []
    expected = {
        "CENTRAL_DRY_DUMMY_PART_SET_COMPLETE": "PASS",
        "FLOAT_INTERFACE_DRY_DUMMY_COMPLETE": "PASS",
        "FLOAT_BODY_SET_COMPLETE": "HOLD",
        "FLOAT_EQUIPPED_FULL_DUMMY_COMPLETE": "HOLD",
        "FULL_DUMMY_PRINT": "HOLD",
    }
    for field, value in expected.items():
        if report.get(field) != value:
            blockers.append(f"INVALID_COMPLETENESS_STATUS:{field}")
    if (
        report.get("FULL_DUMMY_PART_SET_COMPLETE") == "PASS"
        and report.get("FLOAT_BODY_SET_COMPLETE") == "HOLD"
    ):
        blockers.append("FULL_DUMMY_PASS_WHILE_FLOAT_BODY_HOLD")
    return blockers


def validate_artifact(artifact_directory: Path) -> dict:
    artifact = artifact_directory.resolve()
    blockers: list[str] = []
    if not artifact.is_dir():
        raise FileNotFoundError(f"ARTIFACT_DIRECTORY_MISSING:{artifact}")

    required = tuple(part.filename for part in ALL_PARTS) + (
        "printed_part_manifest.csv",
        "printed_part_number_audit.json",
        "stl_mesh_audit.json",
        "a1_printability_audit.json",
        "full_dummy_completeness_report.json",
        "dummy_kit_manifest.json",
        *REQUIRED_NEW_ARTIFACTS,
    )
    missing = sorted(
        filename
        for filename in required
        if not (artifact / filename).is_file()
    )
    blockers.extend(f"MISSING_ARTIFACT:{name}" for name in missing)
    if missing:
        return {
            "schema": "PS_CONNECTIVITY_CORRECTION_VALIDATION_V0_1",
            "status": "FAIL",
            "blockers": blockers,
            "artifact_directory": str(artifact),
        }

    graph = _load_json(artifact / "physical_connection_graph.json")
    graph_validation = validate_physical_connection_graph(graph)
    blockers.extend(graph_validation["blockers"])
    dependency = validate_corrected_dependencies(physical_graph=graph)
    blockers.extend(dependency["blockers"])

    compatibility = _load_json(
        artifact / "static_stl_compatibility_report.json"
    )
    if compatibility.get("STATIC_STL_STATUS") != "PASS":
        blockers.append("STATIC_STL_STATUS_NOT_PASS")
    if compatibility.get("existing_part_count") != len(PARTS):
        blockers.append("STATIC_STL_PART_COUNT_MISMATCH")
    if compatibility.get("modified_existing_stl_count") != 0:
        blockers.append("EXISTING_STL_MODIFIED")

    manifest_rows = _load_csv(artifact / "printed_part_manifest.csv")
    if len(manifest_rows) != len(ALL_PARTS):
        blockers.append("PRINTED_MANIFEST_COUNT_MISMATCH")
    if {row["part_number"] for row in manifest_rows} != {
        part.part_number for part in ALL_PARTS
    }:
        blockers.append("PRINTED_MANIFEST_PART_NUMBER_SET_MISMATCH")
    if any(row["marking_verified"] != "True" for row in manifest_rows):
        blockers.append("UNVERIFIED_PHYSICAL_MARKING")
    for part in CONNECTIVITY_PARTS:
        row = next(
            (
                candidate
                for candidate in manifest_rows
                if candidate["part_number"] == part.part_number
            ),
            {},
        )
        marking = row.get("classification_marking", "")
        for token in (
            "DUMMY ONLY",
            "NO LOAD",
            "NOT STRUCTURAL",
            "PROFILE-3 ONLY",
        ):
            if token not in marking:
                blockers.append(
                    f"CONNECTIVITY_MARKING_MISSING:{part.part_number}:{token}"
                )
    float_parts = {
        "PS-PR-A1-FLT-305-R00",
        "PS-PR-A1-FLT-306-R00",
        "PS-PR-A1-FLT-307-R00",
        "PS-PR-A1-FLT-308-R00",
    }
    if any(
        "REMOVE FOR REAL ALUMINUM"
        not in row.get("classification_marking", "")
        for row in manifest_rows
        if row.get("part_number") in float_parts
    ):
        blockers.append("AI05_REMOVE_FOR_REAL_ALUMINUM_MARKING_MISSING")

    identification = _load_json(
        artifact / "printed_part_number_audit.json"
    )
    if identification.get("physically_marked_part_count") != len(ALL_PARTS):
        blockers.append("PHYSICALLY_MARKED_PART_COUNT_MISMATCH")
    if identification.get("unique_part_number_count") != len(ALL_PARTS):
        blockers.append("UNIQUE_PART_NUMBER_COUNT_MISMATCH")
    if identification.get("floating_text_solid_count") != 0:
        blockers.append("FLOATING_TEXT_PRESENT")

    mesh_failures = []
    for part in ALL_PARTS:
        result = audit_stl(artifact / part.filename)
        if result["status"] != "PASS":
            mesh_failures.append(part.filename)
    blockers.extend(f"STL_MESH_FAILURE:{name}" for name in mesh_failures)

    a1 = _load_json(artifact / "a1_printability_audit.json")
    if a1.get("A1_PRINTABILITY") != "PASS":
        blockers.append("A1_PRINTABILITY_NOT_PASS")
    if a1.get("all_parts_one_plate") is not False:
        blockers.append("ALL_PARTS_ONE_PLATE_FORBIDDEN")

    completeness = _load_json(
        artifact / "full_dummy_completeness_report.json"
    )
    blockers.extend(validate_completeness_status(completeness))

    kit = _load_json(artifact / "dummy_kit_manifest.json")
    status = kit.get("status", {})
    expected_status = {
        "STATIC_STL_STATUS": "PASS",
        "PHYSICAL_ASSEMBLY_CONNECTIVITY": "PASS_WITH_HOLD",
        "PROFILE3_FRAME_CONNECTION": "READY_DUMMY_ONLY",
        "CBOX_SADDLE_ATTACHMENT": "READY_DUMMY_ONLY",
        "BBOX_SUPPORT_ATTACHMENT": "READY_DUMMY_ONLY",
        "FLOAT_ADAPTER_ATTACHMENT": "READY_DUMMY_ONLY",
        "CENTRAL_DRY_DUMMY_PART_SET_COMPLETE": "PASS",
        "FLOAT_INTERFACE_DRY_DUMMY_COMPLETE": "PASS",
        "FLOAT_BODY_SET_COMPLETE": "HOLD",
        "FLOAT_EQUIPPED_FULL_DUMMY_COMPLETE": "HOLD",
        "PROGRESSIVE_DEPENDENCY_GRAPH": "PASS",
        "IMPOSSIBLE_DEPENDENCY_COUNT": 0,
        "DISCONNECTED_PRINTED_PART_COUNT": 0,
        "PROGRESSIVE_PRINT_ORDER": "PASS",
        "AI10_CLEARANCE_STATUS": "NOT_YET_AUDITED",
        "PRINTED_PART_IDENTIFICATION": "PASS",
        "PROGRESSIVE_DUMMY_PRINT": "APPROVED_BY_STAGE",
        "FULL_DUMMY_PRINT": "HOLD",
    }
    for field, expected in expected_status.items():
        if status.get(field) != expected:
            blockers.append(f"INVALID_MANIFEST_STATUS:{field}")

    matrix = _load_csv(artifact / "physical_connection_matrix.csv")
    if len(matrix) != graph_validation["edge_count"]:
        blockers.append("CONNECTION_MATRIX_EDGE_COUNT_MISMATCH")
    gate_rows = _load_csv(
        artifact / "corrected_print_quality_gate_checklist.csv"
    )
    if len(gate_rows) != len(ALL_PARTS) * 5:
        blockers.append("QUALITY_GATE_ROW_COUNT_MISMATCH")

    unique_blockers = sorted(set(blockers))
    passed = not unique_blockers
    return {
        "schema": "PS_CONNECTIVITY_CORRECTION_VALIDATION_V0_1",
        "artifact_directory": str(artifact),
        "status": "PASS_WITH_HOLD" if passed else "FAIL",
        "blockers": unique_blockers,
        "required_artifact_count": len(required),
        "printed_part_count": len(ALL_PARTS),
        "added_connectivity_part_count": len(CONNECTIVITY_PARTS),
        "mesh_audited_part_count": len(ALL_PARTS),
        "connection_edge_count": graph_validation.get("edge_count"),
        "ARTIFACT_INTEGRITY": "PASS" if passed else "FAIL",
        "STATIC_STL_STATUS": compatibility.get("STATIC_STL_STATUS"),
        "PHYSICAL_ASSEMBLY_CONNECTIVITY": (
            graph_validation["PHYSICAL_ASSEMBLY_CONNECTIVITY"]
        ),
        "PROGRESSIVE_DEPENDENCY_GRAPH": dependency[
            "PROGRESSIVE_DEPENDENCY_GRAPH"
        ],
        "IMPOSSIBLE_DEPENDENCY_COUNT": dependency[
            "IMPOSSIBLE_DEPENDENCY_COUNT"
        ],
        "DISCONNECTED_PRINTED_PART_COUNT": graph_validation[
            "DISCONNECTED_PRINTED_PART_COUNT"
        ],
        "PRINTED_PART_IDENTIFICATION": (
            "PASS"
            if identification.get("physically_marked_part_count")
            == len(ALL_PARTS)
            and identification.get("floating_text_solid_count") == 0
            else "FAIL"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate_artifact(args.artifact_dir)
    text = json.dumps(
        result,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0 if result["status"] == "PASS_WITH_HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
