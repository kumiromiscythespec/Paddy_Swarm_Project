from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable

from audit_contract import BASE_HEAD, LANE_RELATIVE


CAD_SUFFIXES = {".stl", ".step", ".stp"}
BYTECODE_SUFFIXES = {".pyc", ".pyo"}
FORBIDDEN_SOURCE_SUFFIXES = CAD_SUFFIXES | {
    ".svg",
    ".csv",
    ".zip",
    ".sha256",
    ".pyc",
    ".pyo",
}
GENERATED_REPORT_NAMES = {
    "production_input_audit.json",
    "real_profile_input_audit.json",
    "cbox_structural_input_audit.json",
    "bbox_structural_input_audit.json",
    "fastener_input_audit.json",
    "printed_part_manufacturing_input_audit.json",
    "float_production_width_audit.json",
    "ai10_production_input_audit.json",
    "production_part_number_proposal.md",
    "unresolved_production_inputs.md",
    "production_readiness_matrix.csv",
    "required_measurements_checklist.csv",
    "required_purchase_specifications.csv",
    "next_cad_lane_recommendation.md",
    "baseline_cad_output_diff_report.json",
    "untracked_cad_output_scan.json",
    "repository_bytecode_audit.json",
}


def _run_git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tracked_cad_paths(root: Path) -> set[str]:
    output = _run_git(
        root,
        "ls-files",
        "-z",
        "--",
        "*.stl",
        "*.step",
        "*.stp",
    )
    return {
        item.replace("\\", "/")
        for item in output.split("\0")
        if item
    }


def compare_baseline_to_files(
    root: Path,
    baseline_records: Iterable[dict[str, Any]],
    current_tracked_paths: set[str],
) -> dict[str, Any]:
    baseline = {item["path"]: item for item in baseline_records}
    modified = []
    deleted = []
    for relative, record in sorted(baseline.items()):
        path = root / Path(relative)
        if relative not in current_tracked_paths or not path.is_file():
            deleted.append(relative)
            continue
        actual_sha = sha256_file(path)
        if (
            actual_sha != record["sha256"]
            or path.stat().st_size != record["bytes"]
        ):
            modified.append(
                {
                    "path": relative,
                    "baseline_sha256": record["sha256"],
                    "current_sha256": actual_sha,
                    "baseline_bytes": record["bytes"],
                    "current_bytes": path.stat().st_size,
                }
            )
    added = sorted(current_tracked_paths - set(baseline))
    status = "PASS" if not (modified or deleted or added) else "FAIL"
    return {
        "BASELINE_TRACKED_CAD_INVENTORY_MATCH": status,
        "ADDED_TRACKED_CAD_OUTPUT_COUNT": len(added),
        "MODIFIED_TRACKED_CAD_OUTPUT_COUNT": len(modified),
        "DELETED_TRACKED_CAD_OUTPUT_COUNT": len(deleted),
        "added_tracked_cad_outputs": added,
        "modified_tracked_cad_outputs": modified,
        "deleted_tracked_cad_outputs": deleted,
    }


def git_cad_diff(root: Path, base: str = BASE_HEAD) -> list[dict[str, str]]:
    output = _run_git(
        root,
        "diff",
        "--name-status",
        "--no-renames",
        base,
        "--",
        "*.stl",
        "*.step",
        "*.stp",
    )
    records = []
    for line in output.splitlines():
        if not line.strip():
            continue
        status, path = line.split("\t", 1)
        records.append({"status": status, "path": path.replace("\\", "/")})
    return records


def build_cad_diff_report(
    root: Path,
    baseline_inventory: dict[str, Any],
) -> dict[str, Any]:
    current = tracked_cad_paths(root)
    report = compare_baseline_to_files(
        root,
        baseline_inventory["records"],
        current,
    )
    report.update(
        {
            "schema": "PS_BASELINE_CAD_OUTPUT_DIFF_REPORT_V0_1",
            "base_head": BASE_HEAD,
            "baseline_inventory_sha256": baseline_inventory[
                "inventory_sha256"
            ],
            "baseline_tracked_stl_count": sum(
                item["extension"].lower() == ".stl"
                for item in baseline_inventory["records"]
            ),
            "baseline_tracked_step_stp_count": sum(
                item["extension"].lower() in {".step", ".stp"}
                for item in baseline_inventory["records"]
            ),
            "git_diff_records": git_cad_diff(root),
        }
    )
    return report


def scan_untracked_cad(
    root: Path,
    current_tracked_paths: set[str] | None = None,
) -> dict[str, Any]:
    tracked = current_tracked_paths
    if tracked is None:
        tracked = tracked_cad_paths(root)
    untracked = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in CAD_SUFFIXES:
            continue
        relative = path.relative_to(root).as_posix()
        if relative not in tracked:
            untracked.append(
                {
                    "path": relative,
                    "extension": path.suffix.lower(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    untracked.sort(key=lambda item: item["path"])
    return {
        "schema": "PS_UNTRACKED_CAD_OUTPUT_SCAN_V0_1",
        "method": (
            "filesystem scan compared with git ls-files; gitignore does not "
            "suppress findings"
        ),
        "UNTRACKED_CAD_OUTPUT_COUNT": len(untracked),
        "status": "PASS" if not untracked else "FAIL",
        "untracked_cad_outputs": untracked,
    }


def scan_repository_bytecode(root: Path) -> dict[str, Any]:
    files = []
    directories = []
    for path in root.rglob("*"):
        if path.is_dir() and path.name == "__pycache__":
            directories.append(path.relative_to(root).as_posix())
        elif path.is_file() and path.suffix.lower() in BYTECODE_SUFFIXES:
            files.append(path.relative_to(root).as_posix())
    files.sort()
    directories.sort()
    count = len(files) + len(directories)
    return {
        "schema": "PS_REPOSITORY_BYTECODE_AUDIT_V0_1",
        "status": "PASS" if count == 0 else "FAIL",
        "repository_bytecode_count": len(files),
        "repository_pycache_directory_count": len(directories),
        "bytecode_files": files,
        "pycache_directories": directories,
        "untracked_bytecode_allowed": False,
    }


def scan_source_lane(root: Path) -> dict[str, Any]:
    lane = root / LANE_RELATIVE
    findings = []
    if not lane.exists():
        return {
            "status": "FAIL",
            "findings": ["SOURCE_LANE_MISSING"],
        }
    for path in lane.rglob("*"):
        if path.is_dir():
            if path.name == "__pycache__":
                findings.append(
                    f"FORBIDDEN_PYCACHE:{path.relative_to(root).as_posix()}"
                )
            continue
        relative = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        if suffix in FORBIDDEN_SOURCE_SUFFIXES:
            findings.append(f"FORBIDDEN_SUFFIX:{relative}")
        if path.name in GENERATED_REPORT_NAMES:
            findings.append(f"GENERATED_ARTIFACT_IN_SOURCE_LANE:{relative}")
        if suffix == ".json" and not (
            path.name.endswith(".schema.json")
            or path.name.endswith(".contract.json")
        ):
            findings.append(f"NON_SOURCE_JSON_IN_SOURCE_LANE:{relative}")
        if suffix == ".md" and path.name != "README.md":
            findings.append(f"GENERATED_MARKDOWN_IN_SOURCE_LANE:{relative}")
    return {
        "status": "PASS" if not findings else "FAIL",
        "findings": sorted(findings),
    }


def ensure_external_output(
    output_path: Path,
    repository: Path,
    *,
    allowed_names: set[str],
) -> None:
    resolved = output_path.resolve()
    root = repository.resolve()
    if resolved == root or root in resolved.parents:
        raise ValueError("AUDIT_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")
    if resolved.name not in allowed_names:
        raise ValueError(f"UNAPPROVED_AUDIT_ARTIFACT_NAME:{resolved.name}")
    if resolved.suffix.lower() in CAD_SUFFIXES:
        raise ValueError("PRODUCTION_CAD_OUTPUT_FORBIDDEN_DURING_AUDIT")


def load_baseline_inventory(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("base_head") != BASE_HEAD:
        raise ValueError("BASELINE_HEAD_MISMATCH")
    return result
