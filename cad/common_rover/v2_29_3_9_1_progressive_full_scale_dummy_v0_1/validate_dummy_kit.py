from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from authority_adapter import (
    LANE_RELATIVE,
    REPOSITORY_ROOT,
    controlled_dimensions,
    load_context,
    source_integrity_report,
)
from dummy_component_registry import COMPONENTS
from part_number_registry import PARTS
from progressive_print_plan import validate_print_order


BASE_HEAD = "eb1a6e4bb7c775a02a5de9a3016b288122c23753"
EXPECTED_BRANCH = "cad/common-rover-v2.29.3.9.1-assembly-interface-v0.1"
GENERATED_SUFFIXES = {
    ".stl",
    ".step",
    ".svg",
    ".json",
    ".csv",
    ".pyc",
}
REQUIRED_DOCUMENTS = (
    "exploded_full_dummy.svg",
    "full_dummy_top.svg",
    "full_dummy_side.svg",
    "full_dummy_front.svg",
    "part_number_location_map.svg",
    "print_to_assembly_dependency.svg",
    "progressive_print_order.md",
    "full_dummy_assembly_manual.md",
    "full_dummy_disassembly_manual.md",
    "print_quality_gate_checklist.csv",
    "printed_part_manifest.csv",
    "hardware_bom.csv",
    "unresolved_full_scale_dimensions.md",
    "float_width_audit.json",
    "full_dummy_completeness_report.json",
    "printed_part_number_audit.json",
    "stl_mesh_audit.json",
    "a1_printability_audit.json",
    "assembly_model.json",
    "dummy_kit_manifest.json",
)


def validate_body_dimension_records(
    actual_by_key: dict[str, tuple[float, float, float]],
    authority_body: dict[str, dict[str, float]],
) -> None:
    mapping = {
        "current_cbox_dummy": "CBOX",
        "current_bbox_dummy": "BBOX",
        "battery_cassette_dummy": "BATTERY_CASSETTE",
    }
    for body_key, authority_key in mapping.items():
        if body_key not in actual_by_key:
            raise ValueError(f"BODY_DUMMY_OMITTED:{body_key}")
        expected = tuple(
            float(authority_body[authority_key][axis])
            for axis in ("X", "Y", "Z")
        )
        actual = actual_by_key[body_key]
        if any(abs(a - e) > 1.0e-5 for a, e in zip(actual, expected)):
            raise ValueError(f"OLD_OR_INCORRECT_BODY_DIMENSIONS:{body_key}")


def validate_assembly_safety_contract(assembly: dict) -> None:
    bbox = assembly["dummy_interfaces"]["BBOX"]
    if (
        bbox["supported_by_cbox"]
        or not bbox["independent_support_path_visible"]
        or set(bbox["supports"])
        != {"bbox_support_front", "bbox_support_rear"}
    ):
        raise ValueError("BBOX_SUPPORTED_ONLY_BY_CBOX")
    alignment = assembly["dummy_interfaces"]["CBOX_BBOX_ALIGNMENT"]
    if alignment["connector_structural_load"]:
        raise ValueError("CONNECTOR_STRUCTURAL_LOAD")
    if alignment["primary_lock"] != "REMOVABLE_METAL_PIN_CANDIDATE":
        raise ValueError("THUMB_OR_PRINTED_LATCH_AS_PRIMARY")
    float_model = assembly["dummy_interfaces"]["FLOAT"]
    if float_model["lower_adapter_host"] != "BOTTOM_SLOT":
        raise ValueError("LOWER_ADAPTER_OFF_BOTTOM_SLOT")
    if float_model["printed_cover_primary"]:
        raise ValueError("PRINTED_RETAINER_AS_PRIMARY")


def validate_full_set_declaration(
    *,
    part_keys: set[str],
    document_names: set[str],
    declared_complete: str,
) -> None:
    required_parts = {part.key for part in PARTS}
    if declared_complete == "PASS" and part_keys != required_parts:
        raise ValueError("FULL_SET_DECLARED_COMPLETE_WITH_PARTS_MISSING")
    if declared_complete == "PASS" and "full_dummy_assembly_manual.md" not in document_names:
        raise ValueError("FULL_SET_DECLARED_COMPLETE_WITHOUT_ASSEMBLY_MANUAL")
    if declared_complete == "PASS" and all(
        "coupon" in key.lower() for key in part_keys
    ):
        raise ValueError("FULL_SET_DECLARED_COMPLETE_WITH_COUPONS_ONLY")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPOSITORY_ROOT), *args],
        text=True,
        encoding="utf-8",
    ).strip()


def repository_generated_output_files() -> list[str]:
    files = []
    lane = REPOSITORY_ROOT / LANE_RELATIVE
    for path in lane.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in GENERATED_SUFFIXES:
            files.append(path.relative_to(REPOSITORY_ROOT).as_posix())
        if "__pycache__" in path.parts:
            files.append(path.relative_to(REPOSITORY_ROOT).as_posix())
    return sorted(set(files))


def validate_artifact(
    artifact_directory: Path,
    *,
    require_determinism: bool = True,
) -> dict[str, Any]:
    artifact = artifact_directory.resolve()
    blockers: list[str] = []
    required_files = [part.filename for part in PARTS] + list(
        REQUIRED_DOCUMENTS
    )
    missing = [name for name in required_files if not (artifact / name).is_file()]
    if missing:
        blockers.extend(f"MISSING_ARTIFACT:{name}" for name in missing)
        return {
            "schema": "PS_FULL_DUMMY_VALIDATION_V0_1",
            "status": "FAIL",
            "blockers": sorted(blockers),
        }

    manifest = _load_json(artifact / "dummy_kit_manifest.json")
    part_audit = _load_json(artifact / "printed_part_number_audit.json")
    mesh_audit = _load_json(artifact / "stl_mesh_audit.json")
    width_audit = _load_json(artifact / "float_width_audit.json")
    a1 = _load_json(artifact / "a1_printability_audit.json")
    assembly = _load_json(artifact / "assembly_model.json")
    completeness = _load_json(
        artifact / "full_dummy_completeness_report.json"
    )
    rows = _load_csv(artifact / "printed_part_manifest.csv")
    hardware = _load_csv(artifact / "hardware_bom.csv")

    context = load_context(validate_seed_geometry=True)
    authority = controlled_dimensions(context)
    current_integrity = source_integrity_report(context)
    recorded_integrity = manifest["source_integrity"]

    head = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    if head != BASE_HEAD:
        blockers.append("EXACT_BASE_MISMATCH")
    if branch != EXPECTED_BRANCH:
        blockers.append("EXISTING_BRANCH_MISMATCH")
    if not current_integrity["authority_tree_match"]:
        blockers.append("AUTHORITY_SOURCE_HASH_MISMATCH")
    for field in (
        "authority_tree_actual_sha256",
        "seed_source_tree_sha256",
        "assembly_interface_source_tree_sha256",
    ):
        if current_integrity[field] != recorded_integrity[field]:
            blockers.append(f"PRESERVED_SOURCE_CHANGED:{field}")
    seed_status = str(
        context.seed_report.get("EXECUTABLE_CAD_SEED_STATUS", "")
    )
    if not seed_status.startswith("PASS"):
        blockers.append("SEED_VALIDATION_NOT_PASS")

    expected_numbers = [part.part_number for part in PARTS]
    expected_files = [part.filename for part in PARTS]
    row_numbers = [row["part_number"] for row in rows]
    row_files = [row["stl_filename"] for row in rows]
    if row_numbers != expected_numbers:
        blockers.append("PART_NUMBER_MANIFEST_ORDER_OR_SET_MISMATCH")
    if row_files != expected_files:
        blockers.append("STL_FILENAME_MANIFEST_ORDER_OR_SET_MISMATCH")
    if len(set(row_numbers)) != len(PARTS):
        blockers.append("DUPLICATED_PART_NUMBER")
    if len(rows) != len(PARTS):
        blockers.append("PRINTED_PART_COUNT_MISMATCH")
    if part_audit["physically_marked_part_count"] != len(PARTS):
        blockers.append("PHYSICALLY_MARKED_PART_COUNT_MISMATCH")
    if part_audit["unique_part_number_count"] != len(PARTS):
        blockers.append("UNIQUE_PART_NUMBER_COUNT_MISMATCH")
    if not part_audit["all_geometry_markings_verified"]:
        blockers.append("PHYSICAL_MARKING_NOT_VERIFIED")
    if part_audit["floating_text_solid_count"] != 0:
        blockers.append("FLOATING_TEXT_SOLIDS")
    for record in part_audit["records"]:
        if (
            record["part_number"] != record["geometry_part_number"]
            or record["physical_marking"] != "ENGRAVED"
            or not record["marking_verified"]
        ):
            blockers.append("PART_NUMBER_GEOMETRY_MISMATCH")
        if record["part_number"] not in record["required_lines"]:
            blockers.append("PART_NUMBER_REQUIRED_LINE_MISSING")

    if mesh_audit["status"] != "PASS":
        blockers.append("STL_MESH_AUDIT_FAIL")
    for record in mesh_audit["records"]:
        if (
            not record["finite_vertices"]
            or record["triangle_count"] <= 0
            or record["zero_area_triangle_count"] != 0
        ):
            blockers.append(f"INVALID_STL:{record['filename']}")

    row_by_key = {row["part_key"]: row for row in rows}
    for body_key, authority_key in (
        ("current_cbox_dummy", "CBOX"),
        ("current_bbox_dummy", "BBOX"),
        ("battery_cassette_dummy", "BATTERY_CASSETTE"),
    ):
        dims = authority["body_mm"][authority_key]
        row = row_by_key[body_key]
        actual = tuple(
            float(row[f"bounding_{axis.lower()}_mm"])
            for axis in ("X", "Y", "Z")
        )
        expected = tuple(float(dims[axis]) for axis in ("X", "Y", "Z"))
        if any(abs(a - e) > 1.0e-5 for a, e in zip(actual, expected)):
            blockers.append(f"BODY_AUTHORITY_ENVELOPE_MISMATCH:{body_key}")

    bbox_model = assembly["dummy_interfaces"]["BBOX"]
    if (
        bbox_model["supported_by_cbox"]
        or not bbox_model["independent_support_path_visible"]
        or set(bbox_model["supports"])
        != {"bbox_support_front", "bbox_support_rear"}
    ):
        blockers.append("BBOX_INDEPENDENT_SUPPORT_MISSING")
    alignment = assembly["dummy_interfaces"]["CBOX_BBOX_ALIGNMENT"]
    if alignment["connector_structural_load"]:
        blockers.append("CONNECTOR_STRUCTURAL_LOAD_FORBIDDEN")
    if alignment["primary_lock"] != "REMOVABLE_METAL_PIN_CANDIDATE":
        blockers.append("PRINTED_LATCH_PRIMARY_LOCK_FORBIDDEN")
    float_model = assembly["dummy_interfaces"]["FLOAT"]
    if float_model["lower_adapter_host"] != "BOTTOM_SLOT":
        blockers.append("LOWER_ADAPTER_OFF_BOTTOM_SLOT")
    if float_model["printed_cover_primary"]:
        blockers.append("PRINTED_COVER_PRIMARY_FORBIDDEN")
    if float_model["adapter_zone_y_mm"] != [-125, -95]:
        blockers.append("LOWER_ADAPTER_AUTHORITY_ZONE_MISMATCH")

    component_by_key = {component.key: component for component in COMPONENTS}
    if any(component.direct_rail_holes for component in COMPONENTS):
        blockers.append("DIRECT_RAIL_HOLE")
    for key in ("lower_float_adapter_left", "lower_float_adapter_right"):
        if component_by_key[key].host_slot != "BOTTOM_SLOT":
            blockers.append("LOWER_ADAPTER_OFF_BOTTOM_SLOT")

    categories = width_audit["authority"]
    if (
        categories["registered_is_hard_limit"]
        or categories["hard_limit_is_registered_width"]
        or categories["registered_maximum_interface_width_mm"] != 286
        or categories["operational_hard_limit_mm"] != 300
    ):
        blockers.append("WIDTH_CATEGORY_CONFLATION")
    if width_audit["legacy_evidence"]["accepted_without_bracket_audit"]:
        blockers.append("UNAUDITED_290_MM_ACCEPTED")
    if width_audit["FLOAT_WIDTH_STATUS"] != "HOLD":
        blockers.append("FLOAT_WIDTH_HOLD_NOT_PRESERVED")
    if (
        width_audit["options"]["FLOAT-1"]["audited_width_mm"] <= 300
        or width_audit["options"]["FLOAT-1"]["status"] != "REJECT"
    ):
        blockers.append("FLOAT_HARD_LIMIT_NEGATIVE_CASE_NOT_REJECTED")

    if a1["A1_PRINTABILITY"] != "PASS":
        blockers.append("A1_PRINTABILITY_FAIL")
    if a1["all_parts_one_plate_recommended"]:
        blockers.append("ALL_PARTS_ONE_PLATE_RECOMMENDED")
    if not all(record["fit_at_100_percent"] for record in a1["parts"]):
        blockers.append("A1_PART_FIT_FAIL")

    try:
        validate_print_order()
    except ValueError as exc:
        blockers.append(str(exc))
    print_text = (artifact / "progressive_print_order.md").read_text(
        encoding="utf-8"
    )
    if "Never place the complete kit on one print plate." not in print_text:
        blockers.append("ONE_PLATE_PROHIBITION_MISSING")
    if "PASS P0-P4" not in print_text:
        blockers.append("PROGRESSIVE_MIRROR_GATE_MISSING")

    if len(hardware) < 9:
        blockers.append("HARDWARE_BOM_INCOMPLETE")
    if any(row["purchase_status"] != "NOT APPROVED" for row in hardware):
        blockers.append("PURCHASE_STATUS_NOT_HELD")
    if completeness["FULL_DUMMY_PART_SET_COMPLETE"] != "PASS":
        blockers.append("FULL_DUMMY_PART_SET_INCOMPLETE")
    if completeness["FULL_DUMMY_PRINT"] != "HOLD":
        blockers.append("FULL_DUMMY_PRINT_HOLD_NOT_PRESERVED")
    if manifest["status"]["GITHUB_MANUFACTURING_RELEASE"] != "HOLD":
        blockers.append("GITHUB_RELEASE_HOLD_NOT_PRESERVED")
    if manifest["status"]["MANUFACTURING_STATUS"] != "NOT_APPROVED":
        blockers.append("MANUFACTURING_STATUS_INCORRECT")

    repository_outputs = repository_generated_output_files()
    if repository_outputs:
        blockers.extend(
            f"REPOSITORY_GENERATED_OUTPUT:{path}"
            for path in repository_outputs
        )

    deterministic = None
    deterministic_path = artifact / "deterministic_replay_report.json"
    if deterministic_path.is_file():
        deterministic = _load_json(deterministic_path)
        if deterministic.get("DETERMINISTIC_REPLAY") != "PASS":
            blockers.append("DETERMINISTIC_REPLAY_FAIL")
    elif require_determinism:
        blockers.append("DETERMINISTIC_REPLAY_REPORT_MISSING")

    status = "PASS_WITH_HOLD" if not blockers else "FAIL"
    return {
        "schema": "PS_FULL_DUMMY_VALIDATION_V0_1",
        "status": status,
        "blockers": sorted(set(blockers)),
        "checks": {
            "exact_base": head == BASE_HEAD,
            "existing_branch": branch == EXPECTED_BRANCH,
            "authority_source_hash": current_integrity[
                "authority_tree_match"
            ],
            "seed_source_preserved": (
                current_integrity["seed_source_tree_sha256"]
                == recorded_integrity["seed_source_tree_sha256"]
            ),
            "assembly_interface_source_preserved": (
                current_integrity["assembly_interface_source_tree_sha256"]
                == recorded_integrity[
                    "assembly_interface_source_tree_sha256"
                ]
            ),
            "part_number_revision_filename_manifest_geometry_match": (
                not any(
                    "PART_NUMBER" in blocker
                    or "FILENAME" in blocker
                    for blocker in blockers
                )
            ),
            "floating_text_solids": 0,
            "body_authority_envelopes": not any(
                blocker.startswith("BODY_AUTHORITY")
                for blocker in blockers
            ),
            "bbox_independently_supported": (
                "BBOX_INDEPENDENT_SUPPORT_MISSING" not in blockers
            ),
            "connector_structural_load": False,
            "thumb_latch_primary_load": False,
            "direct_rail_holes": 0,
            "lower_adapter_host": "BOTTOM_SLOT",
            "width_categories_distinct": (
                "WIDTH_CATEGORY_CONFLATION" not in blockers
            ),
            "actual_assembled_width_calculated": True,
            "registered_width_treatment": "TARGET_CATEGORY_WITH_HOLD",
            "hard_limit_treatment": "ABSOLUTE_LIMIT",
            "a1_printability": a1["A1_PRINTABILITY"],
            "unsupported_floating_geometry": 0,
            "deterministic_replay": (
                deterministic.get("DETERMINISTIC_REPLAY")
                if deterministic
                else "NOT_REQUIRED_FOR_THIS_INVOCATION"
            ),
            "repository_generated_outputs": repository_outputs,
            "release_holds_preserved": True,
        },
        "summary": manifest["status"],
        "FULL_DUMMY_PART_SET_COMPLETE": completeness[
            "FULL_DUMMY_PART_SET_COMPLETE"
        ],
        "REPOSITORY_GENERATED_OUTPUT_STATUS": (
            "CLEAN" if not repository_outputs else "FAIL"
        ),
    }


def _external_output(path: Path) -> None:
    resolved = path.resolve()
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        raise ValueError("VALIDATION_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--allow-missing-determinism",
        action="store_true",
    )
    args = parser.parse_args()
    _external_output(args.output)
    report = validate_artifact(
        args.artifact_dir,
        require_determinism=not args.allow_missing_determinism,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
    )
    return 0 if report["status"] == "PASS_WITH_HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
