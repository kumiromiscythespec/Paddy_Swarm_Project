from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from incoming_inspection_contract import (
    build_inspection_contract,
    validate_inspection_contract,
)
from profile_input_contract import (
    AUDIT_LANE_RELATIVE,
    CANONICAL_INVENTORY_ALGORITHM,
    CANONICAL_INVENTORY_SHA256,
    EXTERNAL_ARTIFACT_NAMES,
    EXPECTED_TRACKED_STEP_STP_COUNT,
    EXPECTED_TRACKED_STL_COUNT,
    LANE_RELATIVE,
    PROHIBITED_REPOSITORY_SUFFIXES,
    repository_root,
)
from profile_role_candidate_matrix import (
    build_role_matrix,
    validate_role_matrix,
)
from supplier_profile_registry import build_registry, validate_registry
from update_production_input_audit import build_production_audit_update


MODULE_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = repository_root(MODULE_DIR)
AUDIT_LANE = REPOSITORY_ROOT / AUDIT_LANE_RELATIVE
if str(AUDIT_LANE) not in sys.path:
    sys.path.insert(0, str(AUDIT_LANE))

from repository_guard import (  # noqa: E402
    build_cad_diff_report,
    load_baseline_inventory,
    scan_repository_bytecode,
    scan_untracked_cad,
)


GENERATED_SOURCE_NAMES = set(EXTERNAL_ARTIFACT_NAMES)


def scan_profile_source_lane(root: Path) -> dict[str, Any]:
    lane = root / LANE_RELATIVE
    findings = []
    if not lane.is_dir():
        return {"status": "FAIL", "findings": ["SOURCE_LANE_MISSING"]}
    for path in lane.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            if path.name == "__pycache__":
                findings.append(f"FORBIDDEN_PYCACHE:{relative}")
            continue
        suffix = path.suffix.lower()
        if suffix in PROHIBITED_REPOSITORY_SUFFIXES:
            findings.append(f"FORBIDDEN_SOURCE_SUFFIX:{relative}")
        if path.name in GENERATED_SOURCE_NAMES:
            findings.append(f"GENERATED_ARTIFACT_IN_SOURCE:{relative}")
        if suffix in {".json", ".csv"}:
            findings.append(f"GENERATED_DATA_IN_SOURCE:{relative}")
        if suffix == ".md" and path.name != "README.md":
            findings.append(f"GENERATED_MARKDOWN_IN_SOURCE:{relative}")
    return {
        "status": "PASS" if not findings else "FAIL",
        "findings": sorted(findings),
    }


def _bytecode_report(root: Path) -> dict[str, Any]:
    base = scan_repository_bytecode(root)
    pyc = []
    pyo = []
    pycache = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() == ".pyc":
            pyc.append(path.relative_to(root).as_posix())
        elif path.is_file() and path.suffix.lower() == ".pyo":
            pyo.append(path.relative_to(root).as_posix())
        elif path.is_dir() and path.name == "__pycache__":
            pycache.append(path.relative_to(root).as_posix())
    result = dict(base)
    result.update(
        {
            "REPOSITORY_PYC_COUNT": len(pyc),
            "REPOSITORY_PYO_COUNT": len(pyo),
            "REPOSITORY_PYCACHE_DIRECTORY_COUNT": len(pycache),
            "pyc_files": sorted(pyc),
            "pyo_files": sorted(pyo),
            "pycache_directories": sorted(pycache),
        }
    )
    return result


def build_repository_gate_reports(
    root: Path,
    baseline_path: Path,
) -> dict[str, Any]:
    root = root.resolve()
    baseline = load_baseline_inventory(baseline_path.resolve())
    if (
        baseline["inventory_hash_algorithm"]
        != CANONICAL_INVENTORY_ALGORITHM
    ):
        raise ValueError("CANONICAL_INVENTORY_ALGORITHM_MISMATCH")
    if baseline["inventory_sha256"] != CANONICAL_INVENTORY_SHA256:
        raise ValueError("CANONICAL_INVENTORY_SHA256_MISMATCH")
    if baseline["TRACKED_STL_COUNT"] != EXPECTED_TRACKED_STL_COUNT:
        raise ValueError("TRACKED_STL_BASELINE_COUNT_MISMATCH")
    if (
        baseline["TRACKED_STEP_STP_COUNT"]
        != EXPECTED_TRACKED_STEP_STP_COUNT
    ):
        raise ValueError("TRACKED_STEP_STP_BASELINE_COUNT_MISMATCH")
    return {
        "cad_diff": build_cad_diff_report(root, baseline),
        "untracked_cad": scan_untracked_cad(root),
        "bytecode": _bytecode_report(root),
        "source_lane": scan_profile_source_lane(root),
    }


def _validate_update(update: dict[str, Any]) -> list[str]:
    blockers = []
    expected = {
        "PROFILE_REGISTRATION": "PASS_WITH_HOLD",
        "PROFILE_01_ORDER_INPUT": "COMPLETE",
        "PROFILE_02_ORDER_INPUT": "COMPLETE",
        "REAL_PROFILE_MANUFACTURER_STATUS": "COMPLETE",
        "REAL_PROFILE_ORDERED_MODEL_STATUS": "COMPLETE",
        "REAL_PROFILE_NOMINAL_SECTION_STATUS": "COMPLETE",
        "REAL_PROFILE_LENGTH_QUANTITY_STATUS": "COMPLETE",
        "REAL_PROFILE_ARRIVAL_STATUS": "PENDING",
        "REAL_PROFILE_MEASUREMENT_STATUS": "INCOMPLETE",
        "REAL_PROFILE_SECTION_AUTHORITY_STATUS": "INCOMPLETE",
        "REAL_PROFILE_ACCESSORY_STATUS": "INCOMPLETE",
        "REAL_PROFILE_ROLE_ASSIGNMENT_STATUS": "HOLD",
        "REAL_PROFILE_FIT_VALIDATION_STATUS": "HOLD",
        "REAL_PROFILE_INPUT_STATUS": "INCOMPLETE",
        "PRODUCTION_STL_GENERATION": "HOLD",
        "PRINT_STAGE": "NOT_REACHED",
    }
    for key, value in expected.items():
        if update.get(key) != value:
            blockers.append(f"PRODUCTION_AUDIT_STATUS_MISMATCH:{key}")
    return blockers


def _validate_artifacts(directory: Path) -> list[str]:
    blockers = []
    for name in EXTERNAL_ARTIFACT_NAMES:
        if not (directory / name).is_file():
            blockers.append(f"REQUIRED_ARTIFACT_MISSING:{name}")
    cad = [
        path.name
        for path in directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".stl", ".step", ".stp"}
    ]
    blockers.extend(f"CAD_ARTIFACT_FORBIDDEN:{name}" for name in cad)
    if blockers:
        return blockers
    registration = json.loads(
        (directory / "supplier_profile_registration_audit.json").read_text(
            encoding="utf-8"
        )
    )
    if registration.get("status") != "PASS_WITH_HOLD":
        blockers.append("REGISTRATION_ARTIFACT_STATUS_INVALID")
    artifact_update = json.loads(
        (directory / "production_audit_profile_update.json").read_text(
            encoding="utf-8"
        )
    )
    blockers.extend(_validate_update(artifact_update))
    tests = json.loads(
        (directory / "unit_test_results.json").read_text(encoding="utf-8")
    )
    if not tests.get("successful"):
        blockers.append("UNIT_TEST_ARTIFACT_FAILED")
    return blockers


def validate_all(
    *,
    root: Path,
    baseline_path: Path,
    artifact_dir: Path | None = None,
) -> dict[str, Any]:
    blockers = []
    registry = build_registry()
    roles = build_role_matrix()
    inspection = build_inspection_contract()
    update = build_production_audit_update()
    for validator, payload in (
        (validate_registry, registry),
        (validate_role_matrix, roles),
        (validate_inspection_contract, inspection),
    ):
        try:
            validator(payload)
        except ValueError as error:
            blockers.append(str(error))
    blockers.extend(_validate_update(update))
    try:
        gates = build_repository_gate_reports(root, baseline_path)
    except (ValueError, FileNotFoundError) as error:
        blockers.append(str(error))
        gates = {}
    if gates:
        diff = gates["cad_diff"]
        if diff["BASELINE_TRACKED_CAD_INVENTORY_MATCH"] != "PASS":
            blockers.append("BASELINE_TRACKED_CAD_INVENTORY_MISMATCH")
        for key in (
            "ADDED_TRACKED_CAD_OUTPUT_COUNT",
            "MODIFIED_TRACKED_CAD_OUTPUT_COUNT",
            "DELETED_TRACKED_CAD_OUTPUT_COUNT",
        ):
            if diff[key] != 0:
                blockers.append(f"{key}_NONZERO")
        if gates["untracked_cad"]["UNTRACKED_CAD_OUTPUT_COUNT"] != 0:
            blockers.append("UNTRACKED_CAD_OUTPUT_COUNT_NONZERO")
        if gates["bytecode"]["status"] != "PASS":
            blockers.append("REPOSITORY_BYTECODE_PRESENT")
        if gates["source_lane"]["status"] != "PASS":
            blockers.extend(gates["source_lane"]["findings"])
    if artifact_dir is not None:
        resolved = artifact_dir.resolve()
        if resolved == root.resolve() or root.resolve() in resolved.parents:
            blockers.append("ARTIFACT_DIRECTORY_INSIDE_REPOSITORY")
        elif not resolved.is_dir():
            blockers.append("ARTIFACT_DIRECTORY_MISSING")
        else:
            blockers.extend(_validate_artifacts(resolved))
    return {
        "schema": "PS_REAL_PROFILE_REGISTRATION_VALIDATION_V0_1",
        "status": "PASS" if not blockers else "FAIL",
        "PROFILE_REGISTRATION": (
            "PASS_WITH_HOLD" if not blockers else "FAIL"
        ),
        "blockers": blockers,
        "canonical_inventory_algorithm": CANONICAL_INVENTORY_ALGORITHM,
        "canonical_inventory_sha256": CANONICAL_INVENTORY_SHA256,
        "repository_gates": gates,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--baseline-inventory", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = validate_all(
        root=repository_root(args.repository_root),
        baseline_path=args.baseline_inventory,
        artifact_dir=args.artifact_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
