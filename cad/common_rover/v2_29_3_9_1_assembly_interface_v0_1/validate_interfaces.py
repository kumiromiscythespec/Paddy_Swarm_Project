from __future__ import annotations

import argparse
import csv
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from assembly_sequence import (
    BATTERY_SEQUENCE,
    battery_reservation,
    build_assembly_steps,
    build_disassembly_steps,
    field_service_evaluation,
)
from authority_adapter import (
    AUTHORITY_RELATIVE,
    LANE_RELATIVE,
    SEED_RELATIVE,
    AuthorityContext,
    canonical_json,
    find_repository_root,
    load_context,
)
from coupon_geometry import (
    COMMON_MARKING_HANDLER,
    COUPON_EXPORT_ARTIFACTS,
    PART_NUMBERS,
    coupon_manifest_rows,
    filename_matches_part_number,
    replay_coupon_exports,
)
from interface_model import (
    REQUIRED_CONNECTION_MARKINGS,
    REQUIRED_COUPONS,
    REQUIRED_DIAGRAMS,
    REQUIRED_INTERFACE_IDS,
    REQUIRED_MARKINGS,
    REQUIRED_OPERATION_MARKINGS,
    build_interface_manifest,
)
from load_path_model import build_load_paths, validate_load_paths
from svg_renderer import render_all


BASE_HEAD = "eb1a6e4bb7c775a02a5de9a3016b288122c23753"
GENERATED_SUFFIXES = {".stl", ".svg", ".json"}
TIMESTAMP_PATTERN = re.compile(
    r"\b20\d{2}-\d{2}-\d{2}[T ][0-2]\d:[0-5]\d"
)


def build_complete_manifest(context: AuthorityContext) -> dict[str, Any]:
    manifest = build_interface_manifest(context)
    manifest["load_paths"] = build_load_paths()
    manifest["assembly_sequence"] = build_assembly_steps()
    manifest["disassembly_sequence"] = build_disassembly_steps()
    manifest["field_service_evaluation"] = field_service_evaluation()
    manifest["battery_cassette_reservation"] = battery_reservation()
    manifest["output_audit"] = {
        "exported_stl_files": list(REQUIRED_COUPONS),
        "repository_generated_output_present": False,
    }
    return manifest


def _interface_by_id(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in data.get("interfaces", []):
        interface_id = str(record.get("interface_id", ""))
        if interface_id not in result:
            result[interface_id] = record
    return result


def validate_printed_part_records(
    records: list[dict[str, Any]],
) -> list[str]:
    blockers: list[str] = []
    if len(records) != 5:
        blockers.append("PRINTED_PART_COUNT_NOT_FIVE")

    numbers = [str(record.get("part_number", "")) for record in records]
    nonblank_numbers = [number for number in numbers if number.strip()]
    if len(nonblank_numbers) != 5:
        blockers.append("PRINTED_PART_NUMBER_MISSING")
    if len(set(nonblank_numbers)) != len(nonblank_numbers):
        blockers.append("PRINTED_PART_NUMBER_DUPLICATE")
    if set(nonblank_numbers) != set(PART_NUMBERS):
        blockers.append("PRINTED_PART_NUMBER_SET_MISMATCH")

    for record in records:
        coupon_id = str(record.get("coupon_id", "")).strip()
        part_number = str(record.get("part_number", ""))
        geometry_part_number = str(record.get("geometry_part_number", ""))
        filename = str(record.get("filename", ""))
        if not part_number.strip():
            continue
        if not filename_matches_part_number(filename, part_number):
            blockers.append("PRINTED_PART_NUMBER_FILENAME_MISMATCH")
        if coupon_id != part_number or geometry_part_number != part_number:
            blockers.append("PRINTED_PART_NUMBER_GEOMETRY_MISMATCH")
        if (
            not geometry_part_number.strip()
            or record.get("marking_verified") is not True
        ):
            blockers.append("PRINTED_PART_NUMBER_METADATA_ONLY")
        if record.get("physical_marking") not in {"EMBOSSED", "ENGRAVED"}:
            blockers.append("PRINTED_PART_NUMBER_METADATA_ONLY")
        if (
            record.get("floating_part_number_solid_count") != 0
            or record.get("geometry_marking_connected", True) is not True
        ):
            blockers.append("PRINTED_PART_NUMBER_FLOATING")
        if (
            record.get("marking_surface_class")
            != "NON_FUNCTIONAL_PRINTABLE_EXTERIOR"
            or not str(record.get("marking_surface", "")).strip()
            or record.get("support_removal_exposure") is not False
        ):
            blockers.append("PRINTED_PART_NUMBER_MARKING_SURFACE_INVALID")
        if (
            record.get("common_marking_handler") != COMMON_MARKING_HANDLER
            or record.get("common_marking_handler_invoked") is not True
        ):
            blockers.extend(
                [
                    "PRINTED_PART_NUMBER_BUILDER_BYPASS",
                    "PRINTED_PART_NUMBER_METADATA_ONLY",
                ]
            )
        if record.get("contains_fit_test_only") is not True:
            blockers.append("FIT_TEST_ONLY_MARKING_MISSING")
        if (
            coupon_id == "COUPON-04"
            and record.get("contains_secondary_only") is not True
        ):
            blockers.append("SECONDARY_ONLY_MARKING_MISSING")
        if record.get("contains_candidate_values") is not True:
            blockers.append("COUPON_CANDIDATE_MARKING_MISSING")
    return sorted(set(blockers))


def validate_contract_data(data: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    interfaces = data.get("interfaces", [])
    ids = [str(record.get("interface_id", "")) for record in interfaces]
    if tuple(ids) != REQUIRED_INTERFACE_IDS:
        blockers.append("REQUIRED_INTERFACE_IDS_MISMATCH")
    if len(ids) != len(set(ids)):
        blockers.append("DUPLICATE_INTERFACE_ID")
    by_id = _interface_by_id(data)

    for required in REQUIRED_INTERFACE_IDS:
        record = by_id.get(required)
        if record is None:
            continue
        if not record.get("authority_source") or any(
            not str(source) for source in record.get("authority_source", [])
        ):
            blockers.append(f"INTERFACE_SOURCE_TRACEABILITY_MISSING:{required}")
        if not record.get("positive_stop") or str(
            record.get("positive_stop")
        ).upper() in {"NONE", "UNKNOWN"}:
            blockers.append(f"POSITIVE_STOP_MISSING:{required}")
        if not record.get("visible_confirmation_point") or (
            "HIDDEN"
            in str(record.get("visible_confirmation_point")).upper()
        ):
            blockers.append(f"VISIBLE_LOCK_STATE_MISSING:{required}")
        fastener = str(record.get("fastener_candidate", "")).upper()
        if "UNKNOWN" in fastener and not record.get("unresolved_values"):
            blockers.append(f"UNKNOWN_FASTENER_SILENTLY_ACCEPTED:{required}")

    ai02 = by_id.get("AI-02", {})
    ai02_fastener = str(ai02.get("fastener_candidate", "")).upper()
    if ai02.get("primary_secondary") != "PRIMARY" or (
        "SNAP" in ai02_fastener
        and "METAL" not in ai02_fastener
    ):
        blockers.append("CBOX_SNAP_HOOK_ONLY")

    ai03 = by_id.get("AI-03", {})
    if "INDEPENDENT" not in " ".join(
        str(value) for value in ai03.get("connected_components", [])
    ):
        blockers.append("BBOX_PRIMARY_SUPPORT_NOT_INDEPENDENT")

    ai07 = by_id.get("AI-07", {})
    pin_text = " ".join(
        str(ai07.get(key, ""))
        for key in (
            "fastener_candidate",
            "visible_confirmation_point",
            "human_intervention_method",
        )
    ).upper()
    if "R-PIN" not in pin_text:
        blockers.append("PIN_RETENTION_MISSING")
    if (
        ai07.get("primary_secondary") != "PRIMARY"
        or "METAL" not in pin_text
    ):
        blockers.append("FLOAT_THUMB_LATCH_ONLY")

    ai08 = by_id.get("AI-08", {})
    if (
        ai08.get("primary_secondary") != "SECONDARY"
        or "COVER" not in str(ai08.get("function_classification", "")).upper()
    ):
        blockers.append("THUMB_LATCH_NOT_SECONDARY_ONLY")

    slot_audit = data.get("slot_zone_audit", {})
    if slot_audit.get("direct_rail_holes_added") is not False:
        blockers.append("UNVALIDATED_DIRECT_RAIL_HOLE")
    if slot_audit.get("lower_adapter_slot_face") != "BOTTOM_SLOT":
        blockers.append("LOWER_ADAPTER_NOT_BOTTOM_SLOT")
    if slot_audit.get("lower_adapter_conflict_count") != 0:
        blockers.append("LOWER_ADAPTER_SLOT_ZONE_CONFLICT")
    if slot_audit.get("front_corner_conflict_count") != 0:
        blockers.append("FRONT_CORNER_BRACKET_CONFLICT")
    if slot_audit.get("new_anchor_count") != 0:
        blockers.append("UNVALIDATED_NEW_ANCHOR")

    markings = data.get("assembly_markings", {})
    if not set(REQUIRED_MARKINGS).issubset(markings.get("orientation", [])):
        blockers.append("MISSING_ORIENTATION_MARKING")
    if not set(REQUIRED_CONNECTION_MARKINGS).issubset(
        markings.get("connections", [])
    ):
        blockers.append("MISSING_CONNECTION_MARKING")
    if not set(REQUIRED_OPERATION_MARKINGS).issubset(
        markings.get("operations", [])
    ):
        blockers.append("MISSING_OPERATION_MARKING")
    if markings.get("left_right_keys_asymmetric") is not True:
        blockers.append("LEFT_RIGHT_KEY_REVERSAL_ALLOWED")
    if markings.get("front_rear_stops_asymmetric") is not True:
        blockers.append("FRONT_REAR_REVERSAL_ALLOWED")
    if markings.get("reverse_insertion_reaches_stop") is not False:
        blockers.append("REVERSE_INSERTION_REACHES_STOP")
    if markings.get("pin_alignment_only_at_positive_stop") is not True:
        blockers.append("PIN_ALIGNS_BEFORE_POSITIVE_STOP")
    if markings.get("lock_state_visible") is not True:
        blockers.append("HIDDEN_LOCK_STATE")
    if markings.get("hidden_fasteners_allowed") is not False:
        blockers.append("HIDDEN_FASTENER_ALLOWED")

    identification_policy = data.get(
        "printed_part_identification_policy", {}
    )
    expected_identification_policy = {
        "required": True,
        "filename_only_identification_allowed": False,
        "physical_marking_required": True,
        "missing_part_number_result": "FAIL",
        "duplicate_part_number_result": "FAIL",
        "part_number_geometry_mismatch_result": "FAIL",
    }
    if any(
        identification_policy.get(key) != expected
        for key, expected in expected_identification_policy.items()
    ):
        blockers.append("PRINTED_PART_IDENTIFICATION_POLICY_INVALID")
    blockers.extend(
        validate_printed_part_records(data.get("printed_parts", []))
    )

    widths = data.get("width_classification", {})
    authority_dimensions = data.get("dimensions_from_authority", {})
    if widths.get("bare_frame_width_mm") != authority_dimensions.get(
        "bare_frame_width_mm"
    ):
        blockers.append("BARE_FRAME_WIDTH_MISCLASSIFIED")
    if widths.get("registered_width_mm") != authority_dimensions.get(
        "registered_maximum_interface_width_mm"
    ):
        blockers.append("REGISTERED_WIDTH_MISCLASSIFIED")
    if widths.get("hard_limit_mm") != authority_dimensions.get(
        "operational_hard_limit_mm"
    ):
        blockers.append("HARD_LIMIT_MISCLASSIFIED")

    blockers.extend(validate_load_paths(data.get("load_paths", [])))
    if data.get("electrical_policy", {}).get(
        "connector_structural_load"
    ) is not False:
        blockers.append("CONNECTOR_USED_AS_STRUCTURAL_SUPPORT")

    thumb_policy = data.get("thumb_latch_policy", {})
    if thumb_policy.get("classification") != "SECONDARY_ONLY":
        blockers.append("THUMB_LATCH_NOT_SECONDARY_ONLY")

    unresolved = data.get("unresolved_dimension_policy", {})
    if unresolved.get("status") != "HOLD":
        blockers.append("UNRESOLVED_DIMENSION_HOLD_REMOVED")
    if unresolved.get("manufacturing_dimensions_created"):
        blockers.append("UNRESOLVED_CONVERTED_TO_MANUFACTURING_DIMENSION")

    steps = data.get("assembly_sequence", [])
    if len(steps) > 12 or [row.get("step") for row in steps] != list(
        range(1, len(steps) + 1)
    ):
        blockers.append("ASSEMBLY_SEQUENCE_INVALID")
    operation_text = " ".join(str(row.get("action", "")) for row in steps)
    for operation in ("INSERT", "SLIDE", "LOCK", "VERIFY"):
        if operation not in operation_text:
            blockers.append(f"ASSEMBLY_OPERATION_MISSING:{operation}")

    battery = data.get("battery_cassette_reservation", {})
    if tuple(battery.get("sequence", [])) != BATTERY_SEQUENCE:
        blockers.append("BATTERY_SEQUENCE_CHANGED")
    if battery.get("connector_structural_load") is not False:
        blockers.append("BATTERY_CONNECTOR_STRUCTURAL")
    if battery.get("manufacturing_geometry") is not False:
        blockers.append("BATTERY_MANUFACTURING_GEOMETRY_CREATED")

    if tuple(data.get("required_diagrams", [])) != REQUIRED_DIAGRAMS:
        blockers.append("REQUIRED_DIAGRAM_SET_MISMATCH")
    if tuple(data.get("required_coupons", [])) != REQUIRED_COUPONS:
        blockers.append("COUPON_SET_MISMATCH")
    if len(data.get("required_coupons", [])) != 5:
        blockers.append("COUPON_COUNT_NOT_FIVE")

    exported_stls = data.get("output_audit", {}).get(
        "exported_stl_files", []
    )
    if any(name not in REQUIRED_COUPONS for name in exported_stls):
        blockers.append("FULL_SIZE_STRUCTURAL_STL_EXPORTED")
    if data.get("output_audit", {}).get(
        "repository_generated_output_present"
    ) is not False:
        blockers.append("REPOSITORY_OUTPUT_POLLUTION")

    output_policy = data.get("output_policy", {})
    if output_policy.get("full_size_structural_stl_allowed") is not False:
        blockers.append("FULL_SIZE_STRUCTURAL_STL_ALLOWED")
    if output_policy.get(
        "repository_generated_files_allowed"
    ) is not False:
        blockers.append("REPOSITORY_OUTPUT_ALLOWED")

    expected_holds = {
        "ELECTRICAL_SAFETY_STATUS": "NOT_VALIDATED",
        "FIELD_DEPLOYMENT_STATUS": "NOT_APPROVED",
        "GITHUB_EXECUTABLE_CAD_RELEASE": "HOLD",
        "GITHUB_MANUFACTURING_RELEASE": "HOLD",
        "MANUFACTURING_STATUS": "NOT_APPROVED",
        "PURCHASE_STATUS": "NOT_APPROVED",
        "STRUCTURAL_STRENGTH_STATUS": "NOT_VALIDATED",
        "THERMAL_STATUS": "NOT_VALIDATED",
        "WATERPROOF_STATUS": "NOT_VALIDATED",
    }
    holds = data.get("release_holds", {})
    for key, expected in expected_holds.items():
        if holds.get(key) != expected:
            blockers.append(f"RELEASE_HOLD_REMOVED:{key}")
    return sorted(set(blockers))


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _source_and_repository_checks(
    context: AuthorityContext,
    blockers: list[str],
) -> dict[str, Any]:
    root = context.repository_root
    head = _run_git(root, "rev-parse", "HEAD").stdout.strip()
    if head != BASE_HEAD:
        blockers.append(f"BASE_HEAD_MISMATCH:{head}")
    authority_diff = _run_git(
        root, "diff", "--exit-code", BASE_HEAD, "--", AUTHORITY_RELATIVE.as_posix()
    )
    seed_diff = _run_git(
        root, "diff", "--exit-code", BASE_HEAD, "--", SEED_RELATIVE.as_posix()
    )
    if authority_diff.returncode != 0:
        blockers.append("AUTHORITY_LANE_CHANGED")
    if seed_diff.returncode != 0:
        blockers.append("EXECUTABLE_SEED_LANE_CHANGED")

    lane = root / LANE_RELATIVE
    bad_line_endings = []
    timestamp_files = []
    for path in sorted(lane.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() in {".py", ".md"}:
            payload = path.read_bytes()
            if b"\r\n" in payload or b"\r" in payload:
                bad_line_endings.append(path.relative_to(root).as_posix())
            text = payload.decode("utf-8")
            if TIMESTAMP_PATTERN.search(text):
                timestamp_files.append(path.relative_to(root).as_posix())
    if bad_line_endings:
        blockers.append("SOURCE_NOT_LF")
    if timestamp_files:
        blockers.append("TIMESTAMP_EMBEDDED_IN_SOURCE")

    generated = [
        path.relative_to(root).as_posix()
        for path in sorted(lane.rglob("*"))
        if path.is_file()
        and path.suffix.lower() in GENERATED_SUFFIXES
        and "__pycache__" not in path.parts
    ]
    if generated:
        blockers.append("GENERATED_OUTPUT_IN_SOURCE_LANE")
    return {
        "head": head,
        "authority_lane_diff_count": (
            0 if authority_diff.returncode == 0 else 1
        ),
        "seed_lane_diff_count": 0 if seed_diff.returncode == 0 else 1,
        "bad_line_ending_files": bad_line_endings,
        "timestamp_source_files": timestamp_files,
        "generated_source_lane_files": generated,
    }


def _output_checks(
    output_directory: Path | None,
    rendered: dict[str, bytes],
    manifest: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    report = {
        "output_checked": output_directory is not None,
        "missing_required_files": [],
        "unexpected_stl_files": [],
        "timestamp_output_files": [],
        "coupon_manifest_record_count": 0,
        "printed_part_number_audit_record_count": 0,
        "coupon_replay": {"status": "NOT_RUN", "files": []},
    }
    if output_directory is None:
        return report
    output = output_directory.resolve()
    required = {
        *REQUIRED_DIAGRAMS,
        *REQUIRED_COUPONS,
        "interface_manifest.json",
        "connection_matrix.csv",
        "assembly_steps.md",
        "unresolved_dimensions.md",
        "deterministic_replay_report.json",
        *COUPON_EXPORT_ARTIFACTS,
    }
    missing = sorted(name for name in required if not (output / name).is_file())
    if missing:
        blockers.append("REQUIRED_ARTIFACT_MISSING")
    report["missing_required_files"] = missing
    actual_stls = sorted(path.name for path in output.glob("*.stl"))
    unexpected_stls = sorted(
        name for name in actual_stls if name not in REQUIRED_COUPONS
    )
    if unexpected_stls:
        blockers.append("FULL_SIZE_STRUCTURAL_STL_EXPORTED")
    report["unexpected_stl_files"] = unexpected_stls
    if len(actual_stls) != 5:
        blockers.append("PRINTED_PART_COUNT_NOT_FIVE")

    artifact_manifest_path = output / "interface_manifest.json"
    if artifact_manifest_path.is_file():
        try:
            artifact_manifest = json.loads(
                artifact_manifest_path.read_text(encoding="utf-8")
            )
            if canonical_json(artifact_manifest) != canonical_json(manifest):
                blockers.append("INTERFACE_MANIFEST_SOURCE_MISMATCH")
        except (UnicodeDecodeError, json.JSONDecodeError):
            blockers.append("INTERFACE_MANIFEST_INVALID")

    csv_rows: list[dict[str, str]] = []
    coupon_csv_path = output / "coupon_manifest.csv"
    if coupon_csv_path.is_file():
        try:
            with coupon_csv_path.open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                csv_rows = list(csv.DictReader(handle))
        except (UnicodeDecodeError, csv.Error):
            blockers.append("COUPON_MANIFEST_INVALID")
    report["coupon_manifest_record_count"] = len(csv_rows)
    if len(csv_rows) != 5:
        blockers.append("PRINTED_PART_COUNT_NOT_FIVE")
    expected_csv = coupon_manifest_rows()
    for expected in expected_csv:
        actual = next(
            (
                row
                for row in csv_rows
                if row.get("coupon_id") == expected["coupon_id"]
            ),
            None,
        )
        if actual is None:
            blockers.append("PRINTED_PART_NUMBER_MISSING")
            continue
        for field in (
            "part_number",
            "filename",
            "physical_marking",
            "marking_surface",
            "marking_verified",
        ):
            if str(actual.get(field, "")) != str(expected[field]):
                blockers.append("PRINTED_PART_NUMBER_GEOMETRY_MISMATCH")

    audit_records: list[dict[str, Any]] = []
    audit_path = output / "printed_part_number_audit.json"
    if audit_path.is_file():
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            audit_records = audit.get("records", [])
            if (
                audit.get("exported_coupon_count") != 5
                or audit.get("part_number_count") != 5
                or audit.get("unique_part_number_count") != 5
                or audit.get("physically_marked_part_count") != 5
                or audit.get("floating_part_number_solid_count") != 0
            ):
                blockers.append("PRINTED_PART_NUMBER_GEOMETRY_MISMATCH")
        except (UnicodeDecodeError, json.JSONDecodeError):
            blockers.append("PRINTED_PART_NUMBER_AUDIT_INVALID")
    report["printed_part_number_audit_record_count"] = len(audit_records)
    blockers.extend(validate_printed_part_records(audit_records))

    manifest_by_id = {
        str(row.get("coupon_id", "")): row
        for row in manifest.get("printed_parts", [])
    }
    csv_by_id = {row.get("coupon_id", ""): row for row in csv_rows}
    for record in audit_records:
        coupon_id = str(record.get("coupon_id", ""))
        filename = str(record.get("filename", ""))
        stl_path = output / filename
        if stl_path.is_file():
            actual_hash = hashlib.sha256(stl_path.read_bytes()).hexdigest()
            if record.get("stl_sha256") != actual_hash:
                blockers.append("PRINTED_PART_NUMBER_GEOMETRY_MISMATCH")
        manifest_record = manifest_by_id.get(coupon_id)
        csv_record = csv_by_id.get(coupon_id)
        if manifest_record is None or csv_record is None:
            blockers.append("PRINTED_PART_NUMBER_METADATA_ONLY")
            continue
        for field in (
            "part_number",
            "filename",
            "physical_marking",
            "marking_surface",
        ):
            values = {
                str(record.get(field, "")),
                str(manifest_record.get(field, "")),
                str(csv_record.get(field, "")),
            }
            if len(values) != 1:
                blockers.append("PRINTED_PART_NUMBER_GEOMETRY_MISMATCH")

    map_path = output / "coupon_marking_map.csv"
    map_rows: list[dict[str, str]] = []
    if map_path.is_file():
        try:
            with map_path.open("r", encoding="utf-8", newline="") as handle:
                map_rows = list(csv.DictReader(handle))
        except (UnicodeDecodeError, csv.Error):
            blockers.append("COUPON_MARKING_MAP_INVALID")
    if len(map_rows) != 5:
        blockers.append("MARKING_SURFACE_TRACEABILITY_MISSING")
    else:
        for row in map_rows:
            if (
                not row.get("marking_surface", "").strip()
                or not row.get("print_orientation", "").strip()
                or row.get("marking_verified") != "true"
            ):
                blockers.append("MARKING_SURFACE_TRACEABILITY_MISSING")

    if not missing:
        try:
            replay = replay_coupon_exports(output)
            report["coupon_replay"] = replay
            if replay["status"] != "PASS":
                blockers.append("COUPON_REPLAY_MISMATCH")
        except Exception as exc:
            report["coupon_replay"] = {
                "status": "FAIL",
                "error": type(exc).__name__,
                "files": [],
            }
            blockers.append("COUPON_REPLAY_FAILED")

    timestamp_files = []
    for path in sorted(output.iterdir()):
        if path.is_file() and path.suffix.lower() in {
            ".svg",
            ".json",
            ".csv",
            ".md",
            ".txt",
        }:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if TIMESTAMP_PATTERN.search(text):
                timestamp_files.append(path.name)
    if timestamp_files:
        blockers.append("TIMESTAMP_EMBEDDED_IN_OUTPUT")
    report["timestamp_output_files"] = timestamp_files
    return report


def validate_full(
    context: AuthorityContext,
    manifest: dict[str, Any],
    first_render: dict[str, bytes],
    replay_render: dict[str, bytes],
    *,
    output_directory: Path | None = None,
) -> dict[str, Any]:
    blockers = validate_contract_data(manifest)
    checks: dict[str, Any] = {}
    if (
        context.authority_tree_expected_sha256
        != context.authority_tree_actual_sha256
    ):
        blockers.append("AUTHORITY_SOURCE_TREE_HASH_MISMATCH")
    checks["authority_source_tree_sha256"] = {
        "expected": context.authority_tree_expected_sha256,
        "actual": context.authority_tree_actual_sha256,
    }
    if context.seed_report.get("EXECUTABLE_CAD_SEED_STATUS") != "PASS_WITH_HOLD":
        blockers.append("EXECUTABLE_SEED_VALIDATION_FAILED")
    if tuple(context.seed_report.get("required_solid_ids", [])) != (
        "V22939-FPB-RAIL-L",
        "V22939-FPB-RAIL-R",
        "V22939-FPB-FRONT-XMEMBER",
        "V22939-CBOX",
        "V22939-BBOX",
        "V22939-BATTERY-CASSETTE",
    ):
        blockers.append("EXACT_SIX_SEED_SOLIDS_CHANGED")

    axes = context.coordinate["axes"]
    if not (
        axes["X"]["meaning"] == "lateral"
        and axes["X"]["positive"] == "left"
        and axes["Y"]["meaning"] == "longitudinal"
        and axes["Y"]["front"] == "negative"
        and axes["Z"]["meaning"] == "vertical"
        and axes["Z"]["positive"] == "up"
    ):
        blockers.append("COORDINATE_AXIS_MISMATCH")

    required_set = set(REQUIRED_DIAGRAMS)
    if set(first_render) != required_set:
        blockers.append("REQUIRED_DIAGRAM_SET_MISMATCH")
    deterministic_svg = first_render == replay_render
    if not deterministic_svg:
        blockers.append("SVG_REPLAY_MISMATCH")
    manifest_bytes = canonical_json(manifest).encode("utf-8")
    replay_manifest_bytes = canonical_json(deepcopy(manifest)).encode("utf-8")
    deterministic_json = manifest_bytes == replay_manifest_bytes
    if not deterministic_json:
        blockers.append("JSON_REPLAY_MISMATCH")
    for name, payload in first_render.items():
        text = payload.decode("utf-8")
        if "\r" in text:
            blockers.append(f"SVG_NOT_LF:{name}")
        for required_text in (
            "NOT MANUFACTURING APPROVED",
            "FRONT",
            "REAR",
            "LEFT",
            "RIGHT",
            "TOP",
            "BOTTOM",
        ):
            if required_text not in text:
                blockers.append(f"SVG_LABEL_MISSING:{name}:{required_text}")

    checks["source_repository"] = _source_and_repository_checks(
        context, blockers
    )
    checks["output"] = _output_checks(
        output_directory, first_render, manifest, blockers
    )
    blockers = sorted(set(blockers))
    status = "PASS_WITH_HOLD" if not blockers else "FAIL"
    printed_part_blockers = [
        blocker
        for blocker in blockers
        if blocker.startswith("PRINTED_PART_")
        or blocker.startswith("MARKING_SURFACE_")
        or blocker.startswith("COUPON_MARKING_")
        or blocker in {
            "COUPON_REPLAY_FAILED",
            "COUPON_REPLAY_MISMATCH",
            "FIT_TEST_ONLY_MARKING_MISSING",
            "SECONDARY_ONLY_MARKING_MISSING",
            "COUPON_CANDIDATE_MARKING_MISSING",
        }
    ]
    assembly_marking_blockers = [
        blocker
        for blocker in blockers
        if "MARKING" in blocker
        or blocker.startswith("PRINTED_PART_")
        or blocker in {"COUPON_REPLAY_FAILED", "COUPON_REPLAY_MISMATCH"}
    ]
    printed_parts = manifest.get("printed_parts", [])
    part_numbers = [
        str(record.get("part_number", ""))
        for record in printed_parts
        if str(record.get("part_number", "")).strip()
    ]
    physical_count = len(
        [
            record
            for record in printed_parts
            if record.get("marking_verified") is True
            and record.get("physical_marking") in {"EMBOSSED", "ENGRAVED"}
        ]
    )
    coupon_replay_pass = (
        checks["output"]["coupon_replay"]["status"] in {"NOT_RUN", "PASS"}
    )
    return {
        "schema": "PS_COMMON_ROVER_V229391_ASSEMBLY_INTERFACE_VALIDATION_V0_1",
        "checks": checks,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "DESIGN_ANALYSIS_PROCESS": status,
        "ASSEMBLY_INTERFACE_V0_1_STATUS": status,
        "AUTHORITY_SOURCE_STATUS": (
            "UNCHANGED"
            if "AUTHORITY_LANE_CHANGED" not in blockers
            and "AUTHORITY_SOURCE_TREE_HASH_MISMATCH" not in blockers
            else "FAIL"
        ),
        "EXECUTABLE_SEED_STATUS": (
            "UNCHANGED"
            if "EXECUTABLE_SEED_LANE_CHANGED" not in blockers
            and "EXECUTABLE_SEED_VALIDATION_FAILED" not in blockers
            else "FAIL"
        ),
        "SLOT_ZONE_CONFLICT_STATUS": (
            "PASS"
            if not any("SLOT" in blocker or "CORNER" in blocker for blocker in blockers)
            else "FAIL"
        ),
        "PRIMARY_LOAD_PATH_STATUS": "HOLD" if not blockers else "FAIL",
        "BOX_TO_FRAME_INTERFACE": (
            "CONCEPT_DEFINED" if not blockers else "FAIL"
        ),
        "FLOAT_TO_FRAME_INTERFACE": (
            "CONCEPT_DEFINED" if not blockers else "FAIL"
        ),
        "THUMB_LATCH_CLASSIFICATION": (
            "SECONDARY_ONLY"
            if "THUMB_LATCH_NOT_SECONDARY_ONLY" not in blockers
            else "FAIL"
        ),
        "ASSEMBLY_MARKING_STATUS": (
            "PASS" if not assembly_marking_blockers else "FAIL"
        ),
        "PRINTED_PART_IDENTIFICATION_POLICY": (
            "PASS" if not printed_part_blockers else "FAIL"
        ),
        "PRINTED_PART_COUNT": 5 if len(printed_parts) == 5 else "FAIL",
        "PHYSICALLY_MARKED_PART_COUNT": (
            5
            if physical_count == 5
            and not any(
                blocker
                in {
                    "PRINTED_PART_NUMBER_METADATA_ONLY",
                    "PRINTED_PART_NUMBER_GEOMETRY_MISMATCH",
                    "PRINTED_PART_NUMBER_FLOATING",
                    "PRINTED_PART_NUMBER_BUILDER_BYPASS",
                }
                for blocker in blockers
            )
            else "FAIL"
        ),
        "UNIQUE_PART_NUMBER_COUNT": (
            5 if len(part_numbers) == len(set(part_numbers)) == 5 else "FAIL"
        ),
        "FILENAME_ONLY_IDENTIFICATION": (
            "PROHIBITED"
            if manifest.get("printed_part_identification_policy", {}).get(
                "filename_only_identification_allowed"
            )
            is False
            else "FAIL"
        ),
        "METADATA_ONLY_IDENTIFICATION": (
            "PROHIBITED"
            if "PRINTED_PART_NUMBER_METADATA_ONLY" not in blockers
            else "FAIL"
        ),
        "PART_NUMBER_GEOMETRY_MATCH": (
            "PASS"
            if not any(
                blocker
                in {
                    "PRINTED_PART_NUMBER_MISSING",
                    "PRINTED_PART_NUMBER_METADATA_ONLY",
                    "PRINTED_PART_NUMBER_GEOMETRY_MISMATCH",
                    "PRINTED_PART_NUMBER_FILENAME_MISMATCH",
                    "PRINTED_PART_NUMBER_BUILDER_BYPASS",
                }
                for blocker in blockers
            )
            else "FAIL"
        ),
        "PART_NUMBER_FLOATING_GEOMETRY": (
            0 if "PRINTED_PART_NUMBER_FLOATING" not in blockers else "FAIL"
        ),
        "FIT_TEST_COUPON_COUNT": (
            5 if len(manifest.get("required_coupons", [])) == 5 else "FAIL"
        ),
        "DETERMINISTIC_REPLAY": (
            "PASS"
            if deterministic_svg and deterministic_json and coupon_replay_pass
            else "FAIL"
        ),
        "REPOSITORY_GENERATED_OUTPUT_STATUS": (
            "CLEAN"
            if not any(
                blocker
                in {
                    "GENERATED_OUTPUT_IN_SOURCE_LANE",
                    "REPOSITORY_OUTPUT_POLLUTION",
                }
                for blocker in blockers
            )
            else "FAIL"
        ),
        **{
            key: value
            for key, value in sorted(context.holds.items())
            if key != "version"
        },
        "FULL_DUMMY_PRINT": "HOLD",
        "ELECTRICAL_SAFETY_STATUS": "NOT_VALIDATED",
    }


def deterministic_replay_report(
    manifest: dict[str, Any],
    first_render: dict[str, bytes],
    replay_render: dict[str, bytes],
    coupon_replay: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = []
    for name in sorted(first_render):
        first_hash = hashlib.sha256(first_render[name]).hexdigest()
        replay_hash = hashlib.sha256(replay_render[name]).hexdigest()
        rows.append(
            {
                "filename": name,
                "first_sha256": first_hash,
                "replay_sha256": replay_hash,
                "match": first_hash == replay_hash,
            }
        )
    manifest_first = hashlib.sha256(
        canonical_json(manifest).encode("utf-8")
    ).hexdigest()
    manifest_replay = hashlib.sha256(
        canonical_json(deepcopy(manifest)).encode("utf-8")
    ).hexdigest()
    passed = all(row["match"] for row in rows) and (
        manifest_first == manifest_replay
    ) and (
        coupon_replay is None or coupon_replay.get("status") == "PASS"
    )
    return {
        "schema": "PS_COMMON_ROVER_V229391_ASSEMBLY_INTERFACE_REPLAY_V0_1",
        "status": "PASS" if passed else "FAIL",
        "timestamp_embedded": False,
        "svg_files": rows,
        "manifest_first_sha256": manifest_first,
        "manifest_replay_sha256": manifest_replay,
        "manifest_match": manifest_first == manifest_replay,
        "coupon_artifacts": coupon_replay
        if coupon_replay is not None
        else {"status": "NOT_RUN", "files": []},
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--artifact-dir", type=Path)
    return parser.parse_args(argv)


def _external(path: Path | None, root: Path) -> None:
    if path is None:
        return
    resolved = path.resolve()
    if resolved == root or root in resolved.parents:
        raise ValueError("VALIDATION_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = find_repository_root()
    _external(args.output, root)
    _external(args.artifact_dir, root)
    try:
        context = load_context(root)
        manifest = build_complete_manifest(context)
        first = render_all(
            manifest,
            manifest["load_paths"],
            manifest["assembly_sequence"],
            context,
        )
        replay = render_all(
            manifest,
            manifest["load_paths"],
            manifest["assembly_sequence"],
            context,
        )
        report = validate_full(
            context,
            manifest,
            first,
            replay,
            output_directory=args.artifact_dir,
        )
    except Exception as exc:
        report = {
            "schema": "PS_COMMON_ROVER_V229391_ASSEMBLY_INTERFACE_VALIDATION_V0_1",
            "blocker_count": 1,
            "blockers": [
                f"UNHANDLED_VALIDATION_EXCEPTION:{type(exc).__name__}"
            ],
            "DESIGN_ANALYSIS_PROCESS": "FAIL",
            "ASSEMBLY_INTERFACE_V0_1_STATUS": "FAIL",
        }
    payload = canonical_json(report)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    sys.stdout.write(payload)
    return (
        0
        if report.get("ASSEMBLY_INTERFACE_V0_1_STATUS") == "PASS_WITH_HOLD"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
