from __future__ import annotations
import hashlib
import json
import os
import re
import zipfile
from collections import Counter
from pathlib import Path

EXTERNAL_SIDECARS = {
    "completion_report.md", "package_receipt.json",
    "final_zip_seal_report.json", "result_bundle.zip",
    "result_bundle.zip.sha256",
}
INTERNAL_MANIFEST = "SHA256SUMS.txt"
INTERNAL_REPORT = "zip_content_validation_report.json"

def sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()

def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _secret_candidate(name):
    lowered = name.lower()
    return (
        lowered.endswith((".pem", ".key", ".p12", ".pfx"))
        or lowered in {".env", "credentials.json", "secrets.json"}
    )

def collect_internal_payload(root):
    base = Path(root)
    rows = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(base).as_posix()
        if path.name in EXTERNAL_SIDECARS | {INTERNAL_MANIFEST}:
            continue
        if relative.endswith(".zip"):
            continue
        rows.append(path)
    return rows

def write_internal_manifest(root):
    base = Path(root)
    report_path = base / INTERNAL_REPORT
    initial = [
        path for path in collect_internal_payload(base)
        if path.name != INTERNAL_REPORT
    ]
    expected = sorted(
        [path.relative_to(base).as_posix() for path in initial]
        + [INTERNAL_REPORT]
    )
    initial_hashes = {
        path.relative_to(base).as_posix(): sha256_file(path)
        for path in initial
    }
    report = {
        "status": "PASS_PREZIP_CANONICAL_PAYLOAD",
        "expected_entries_excluding_manifest": expected,
        "expected_entry_count_excluding_manifest": len(expected),
        "internal_manifest_name": INTERNAL_MANIFEST,
        "external_sidecars_excluded": sorted(EXTERNAL_SIDECARS),
        "external_sidecar_internal_reference_count": 0,
        "internal_hashes_excluding_self": initial_hashes,
        "self_hash_recorded": False,
    }
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    payload = collect_internal_payload(base)
    rows = [
        {
            "path": path.relative_to(base).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in payload
    ]
    manifest_path = base / INTERNAL_MANIFEST
    manifest_path.write_text(
        "".join(f"{row['sha256']}  {row['path']}\n" for row in rows),
        encoding="utf-8",
    )
    return rows

def parse_internal_manifest(payload):
    rows = []
    for line in payload.decode("utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        rows.append({"path": name, "sha256": digest})
    return rows

def validate_internal_manifest_policy(manifest_rows, internal_entry_names):
    targets = [row["path"] for row in manifest_rows]
    names = set(internal_entry_names)
    errors = []
    external = sorted(set(targets) & EXTERNAL_SIDECARS)
    if external:
        errors.append(f"external sidecar referenced internally: {external}")
    missing = sorted(set(targets) - names)
    if missing:
        errors.append(f"missing internal hash targets: {missing}")
    duplicates = [
        name for name, count in Counter(targets).items() if count > 1
    ]
    if duplicates:
        errors.append(f"duplicate internal hash targets: {duplicates}")
    return errors

def build_and_seal_package(root, zip_path):
    base = Path(root)
    destination = Path(zip_path)
    rows = write_internal_manifest(base)
    targets = {row["path"]: row["sha256"] for row in rows}
    internal_files = collect_internal_payload(base)
    internal_files.append(base / INTERNAL_MANIFEST)
    internal_files = sorted(
        internal_files, key=lambda path: path.relative_to(base).as_posix()
    )
    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in internal_files:
            relative = path.relative_to(base).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(2026, 7, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(destination, "r") as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        duplicate_count = len(names) - len(set(names))
        case_collision_count = len(names) - len({name.casefold() for name in names})
        absolute = [
            name for name in names
            if name.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", name)
        ]
        traversal = [
            name for name in names if ".." in Path(name).parts or "\\" in name
        ]
        nested_zip = [name for name in names if name.lower().endswith(".zip")]
        pycache = [name for name in names if "__pycache__" in Path(name).parts]
        secrets = [name for name in names if _secret_candidate(Path(name).name)]
        symlinks = [
            item.filename for item in infos
            if (item.external_attr >> 16) & 0o170000 == 0o120000
        ]
        undeclared_executable = [
            item.filename for item in infos
            if ((item.external_attr >> 16) & 0o111)
            and not item.filename.lower().endswith((".ps1", ".py"))
        ]
        manifest_rows = parse_internal_manifest(
            archive.read(INTERNAL_MANIFEST)
        )
        manifest_targets = {
            row["path"]: row["sha256"] for row in manifest_rows
        }
        sidecar_refs = sorted(set(manifest_targets) & EXTERNAL_SIDECARS)
        missing = [
            name for name in manifest_targets if name not in names
        ]
        mismatches = [
            name for name, expected in manifest_targets.items()
            if name in names and sha256_bytes(archive.read(name)) != expected
        ]
        unexpected = sorted(
            set(names) - set(manifest_targets) - {INTERNAL_MANIFEST}
        )
        corrupt = archive.testzip()
    hard_failure_count = sum((
        duplicate_count, case_collision_count, len(absolute), len(traversal),
        len(nested_zip), len(pycache), len(secrets), len(symlinks),
        len(undeclared_executable), len(sidecar_refs), len(missing),
        len(mismatches), len(unexpected), int(corrupt is not None),
    ))
    return {
        "zip_path": str(destination),
        "zip_size": destination.stat().st_size,
        "zip_sha256": sha256_file(destination),
        "entry_count": len(names),
        "internal_hash_target_count": len(manifest_targets),
        "duplicate_entry_count": duplicate_count,
        "case_collision_count": case_collision_count,
        "absolute_path_count": len(absolute),
        "path_traversal_count": len(traversal),
        "nested_zip_count": len(nested_zip),
        "pycache_count": len(pycache),
        "secret_candidate_count": len(secrets),
        "symlink_count": len(symlinks),
        "undeclared_executable_count": len(undeclared_executable),
        "external_sidecar_internal_reference_count": len(sidecar_refs),
        "missing_internal_hash_target_count": len(missing),
        "internal_hash_mismatch_count": len(mismatches),
        "unexpected_entry_count": len(unexpected),
        "corrupt_member": corrupt,
        "final_status":
            "PASS_FINAL_SEAL" if hard_failure_count == 0
            else "FAIL_FINAL_SEAL",
    }

def validate_final_seal_claim(record):
    errors = []
    if record.get("final_status") == "PASS_FINAL_SEAL":
        for key in (
            "duplicate_entry_count", "case_collision_count",
            "absolute_path_count", "path_traversal_count",
            "nested_zip_count", "pycache_count", "secret_candidate_count",
            "symlink_count", "undeclared_executable_count",
            "external_sidecar_internal_reference_count",
            "missing_internal_hash_target_count",
            "internal_hash_mismatch_count", "unexpected_entry_count",
        ):
            if record.get(key):
                errors.append(f"final seal PASS with {key}")
        if record.get("corrupt_member") is not None:
            errors.append("final seal PASS without successful reopen/CRC")
    if record.get("final_status") == "PLANNED_PRESEAL_VALIDATION":
        errors.append("preseal status cannot be final PASS")
    return errors
