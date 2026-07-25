from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from audit_contract import (
    BASE_HEAD,
    EXPECTED_TRACKED_STEP_STP_COUNT,
    EXPECTED_TRACKED_STL_COUNT,
    REQUIRED_EXTERNAL_ARTIFACTS,
    repository_root,
)
from repository_guard import (
    CAD_SUFFIXES,
    build_cad_diff_report,
    load_baseline_inventory,
    scan_repository_bytecode,
    scan_source_lane,
    scan_untracked_cad,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    return parser.parse_args(argv)


def validate(
    *,
    root: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    root = root.resolve()
    artifacts = artifact_dir.resolve()
    blockers = []
    if artifacts == root or root in artifacts.parents:
        blockers.append("ARTIFACT_DIRECTORY_INSIDE_REPOSITORY")
    missing = [
        name
        for name in REQUIRED_EXTERNAL_ARTIFACTS
        if not (artifacts / name).is_file()
    ]
    blockers.extend(f"MISSING_ARTIFACT:{name}" for name in missing)
    unexpected_cad = sorted(
        path.name
        for path in artifacts.iterdir()
        if path.is_file() and path.suffix.lower() in CAD_SUFFIXES
    )
    blockers.extend(f"CAD_ARTIFACT_FORBIDDEN:{name}" for name in unexpected_cad)
    if missing:
        return {
            "schema": "PS_PRODUCTION_INPUT_AUDIT_VALIDATION_V0_1",
            "status": "FAIL",
            "blockers": blockers,
        }

    baseline = load_baseline_inventory(
        artifacts / "baseline_tracked_cad_inventory.json"
    )
    diff = build_cad_diff_report(root, baseline)
    untracked = scan_untracked_cad(root)
    bytecode = scan_repository_bytecode(root)
    source = scan_source_lane(root)
    overall = json.loads(
        (artifacts / "production_input_audit.json").read_text(
            encoding="utf-8"
        )
    )

    if baseline["TRACKED_STL_COUNT"] != EXPECTED_TRACKED_STL_COUNT:
        blockers.append("BASELINE_TRACKED_STL_COUNT_MISMATCH")
    if (
        baseline["TRACKED_STEP_STP_COUNT"]
        != EXPECTED_TRACKED_STEP_STP_COUNT
    ):
        blockers.append("BASELINE_TRACKED_STEP_STP_COUNT_MISMATCH")
    if baseline["base_head"] != BASE_HEAD:
        blockers.append("BASE_HEAD_MISMATCH")
    if diff["BASELINE_TRACKED_CAD_INVENTORY_MATCH"] != "PASS":
        blockers.append("BASELINE_TRACKED_CAD_INVENTORY_MISMATCH")
    for name in (
        "ADDED_TRACKED_CAD_OUTPUT_COUNT",
        "MODIFIED_TRACKED_CAD_OUTPUT_COUNT",
        "DELETED_TRACKED_CAD_OUTPUT_COUNT",
    ):
        if diff[name] != 0:
            blockers.append(f"{name}_NONZERO")
    if untracked["UNTRACKED_CAD_OUTPUT_COUNT"] != 0:
        blockers.append("UNTRACKED_CAD_OUTPUT_COUNT_NONZERO")
    if bytecode["status"] != "PASS":
        blockers.append("REPOSITORY_BYTECODE_PRESENT")
    if source["status"] != "PASS":
        blockers.extend(source["findings"])
    if overall.get("audit_status") != "PASS_WITH_HOLD":
        blockers.append("PRODUCTION_INPUT_AUDIT_STATUS_INVALID")
    gate = overall.get("completion_gate", {})
    if gate.get("production_stl_generation") != "HOLD":
        blockers.append("PRODUCTION_STL_GENERATION_NOT_HELD")
    if gate.get("dummy_stl_print") != "NOT_SELECTED":
        blockers.append("DUMMY_STL_PRINT_SELECTED")
    for key in (
        "manufacturing_status",
        "purchase_status",
        "field_deployment_status",
    ):
        if gate.get(key) != "NOT_APPROVED":
            blockers.append(f"{key.upper()}_IMPROPERLY_APPROVED")
    expected_domains = {
        "REAL_PROFILE_INPUT_STATUS": "INCOMPLETE",
        "CBOX_STRUCTURAL_INPUT_STATUS": "INCOMPLETE",
        "BBOX_STRUCTURAL_INPUT_STATUS": "INCOMPLETE",
        "FASTENER_INPUT_STATUS": "INCOMPLETE",
        "PRINTED_PART_INPUT_STATUS": "INCOMPLETE",
        "FLOAT_PRODUCTION_WIDTH_STATUS": "HOLD",
        "AI10_PRODUCTION_INPUT_STATUS": "INCOMPLETE",
        "PRODUCTION_PART_NUMBER_STATUS": "HOLD",
    }
    for key, value in expected_domains.items():
        if overall.get("domain_statuses", {}).get(key) != value:
            blockers.append(f"DOMAIN_STATUS_MISMATCH:{key}")

    return {
        "schema": "PS_PRODUCTION_INPUT_AUDIT_VALIDATION_V0_1",
        "status": "PASS" if not blockers else "FAIL",
        "blockers": blockers,
        "required_artifact_count": len(REQUIRED_EXTERNAL_ARTIFACTS),
        "baseline_inventory_sha256": baseline["inventory_sha256"],
        "baseline_cad_diff": {
            key: diff[key]
            for key in (
                "BASELINE_TRACKED_CAD_INVENTORY_MATCH",
                "ADDED_TRACKED_CAD_OUTPUT_COUNT",
                "MODIFIED_TRACKED_CAD_OUTPUT_COUNT",
                "DELETED_TRACKED_CAD_OUTPUT_COUNT",
            )
        },
        "untracked_cad_output_count": untracked[
            "UNTRACKED_CAD_OUTPUT_COUNT"
        ],
        "repository_bytecode_status": bytecode["status"],
        "source_lane_status": source["status"],
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate(
        root=repository_root(args.repository_root),
        artifact_dir=args.artifact_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
