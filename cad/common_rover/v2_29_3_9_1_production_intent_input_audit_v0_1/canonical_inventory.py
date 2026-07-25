from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import random
import re
import subprocess
from typing import Any, Iterable


ALGORITHM_IDENTIFIER = (
    "SHA256_OF_UTF8_BYTEWISE_SORTED_POSIX_PATH_RECORDS_V1"
)
RECEIPT_NAME = "baseline_tracked_cad_inventory.canonical"
CAD_SUFFIXES = {".stl", ".step", ".stp"}
SHA256_PATTERN = re.compile(r"[0-9A-Fa-f]{64}")
DRIVE_PREFIX_PATTERN = re.compile(r"[A-Za-z]:")
CSV_FIELDS = (
    "path",
    "extension",
    "bytes",
    "git_blob_sha1",
    "sha256",
)


def canonical_posix_path(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("CANONICAL_PATH_MUST_BE_NONEMPTY_STRING")
    normalized = value.replace("\\", "/")
    if normalized.startswith("./"):
        raise ValueError("CANONICAL_PATH_LEADING_DOT_SLASH_FORBIDDEN")
    if normalized.startswith("/") or DRIVE_PREFIX_PATTERN.match(normalized):
        raise ValueError("CANONICAL_PATH_MUST_BE_REPOSITORY_RELATIVE")
    if "\x00" in normalized or "\n" in normalized or "\r" in normalized:
        raise ValueError("CANONICAL_PATH_CONTROL_CHARACTER_FORBIDDEN")
    segments = normalized.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError("CANONICAL_PATH_NONCANONICAL_SEGMENT")
    normalized.encode("utf-8", errors="strict")
    return normalized


def canonical_sha256(value: str) -> str:
    if not isinstance(value, str) or not SHA256_PATTERN.fullmatch(value):
        raise ValueError("MALFORMED_FILE_SHA256")
    return value.lower()


def canonicalize_record(record: dict[str, Any]) -> dict[str, Any]:
    result = dict(record)
    result["path"] = canonical_posix_path(record["path"])
    result["sha256"] = canonical_sha256(record["sha256"])
    if "extension" in result:
        result["extension"] = str(result["extension"]).lower()
        if result["extension"] != Path(result["path"]).suffix.lower():
            raise ValueError("RECORD_EXTENSION_PATH_MISMATCH")
    if "bytes" in result:
        result["bytes"] = int(result["bytes"])
        if result["bytes"] < 0:
            raise ValueError("RECORD_BYTES_NEGATIVE")
    return result


def canonicalize_records(
    records: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    canonical = [canonicalize_record(record) for record in records]
    canonical.sort(key=lambda record: record["path"].encode("utf-8"))
    duplicates = [
        canonical[index]["path"]
        for index in range(1, len(canonical))
        if canonical[index - 1]["path"] == canonical[index]["path"]
    ]
    if duplicates:
        raise ValueError(
            "DUPLICATE_CANONICAL_PATH:" + ",".join(sorted(set(duplicates)))
        )
    return canonical


def canonical_inventory_payload(
    records: Iterable[dict[str, Any]],
) -> bytes:
    canonical = canonicalize_records(records)
    return b"".join(
        record["sha256"].encode("ascii")
        + b"  "
        + record["path"].encode("utf-8")
        + b"\n"
        for record in canonical
    )


def canonical_inventory_sha256(
    records: Iterable[dict[str, Any]],
) -> str:
    return hashlib.sha256(canonical_inventory_payload(records)).hexdigest()


def _base_tree_records(
    repository_root: Path,
    base_head: str,
) -> list[dict[str, Any]]:
    clean_check = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "diff",
            "--quiet",
            "--no-ext-diff",
            base_head,
            "--",
            "*.stl",
            "*.step",
            "*.stp",
        ],
        check=False,
    )
    if clean_check.returncode != 0:
        raise ValueError("BASELINE_TRACKED_CAD_DIFF_NOT_CLEAN")
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "ls-tree",
            "-r",
            "-z",
            "--long",
            base_head,
        ],
        check=True,
        capture_output=True,
    )
    records = []
    for entry in completed.stdout.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        _mode, object_type, blob_sha, _size = metadata.split()
        if object_type != b"blob":
            continue
        path = raw_path.decode("utf-8", errors="strict")
        extension = Path(path).suffix.lower()
        if extension not in CAD_SUFFIXES:
            continue
        canonical_path = canonical_posix_path(path)
        filesystem_path = repository_root / Path(canonical_path)
        if not filesystem_path.is_file():
            raise FileNotFoundError(
                f"BASELINE_TRACKED_CAD_MISSING:{canonical_path}"
            )
        content = filesystem_path.read_bytes()
        expected_blob = blob_sha.decode("ascii").lower()
        records.append(
            {
                "path": canonical_path,
                "extension": extension,
                "bytes": len(content),
                "git_blob_sha1": expected_blob,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return canonicalize_records(records)


def build_inventory(
    repository_root: Path,
    *,
    base_head: str,
) -> dict[str, Any]:
    root = repository_root.resolve()
    records = _base_tree_records(root, base_head)
    inventory_hash = canonical_inventory_sha256(records)
    return {
        "schema": "PS_BASELINE_TRACKED_CAD_INVENTORY_V0_2",
        "repository": str(root),
        "base_head": base_head,
        "source": (
            "git ls-tree at base_head; git diff clean-filter verification; "
            "SHA-256 and bytes from worktree file bytes"
        ),
        "TRACKED_STL_COUNT": sum(
            record["extension"] == ".stl" for record in records
        ),
        "TRACKED_STEP_STP_COUNT": sum(
            record["extension"] in {".step", ".stp"} for record in records
        ),
        "TRACKED_CAD_TOTAL_COUNT": len(records),
        "inventory_hash_algorithm": ALGORITHM_IDENTIFIER,
        "canonical_path_rule": (
            "repository-relative POSIX path; no leading ./; no backslash; "
            "UTF-8 bytewise ascending"
        ),
        "canonical_record_format": (
            "<lowercase_file_sha256><two ASCII spaces>"
            "<canonical_posix_path><LF>"
        ),
        "inventory_sha256": inventory_hash,
        "first_canonical_path": records[0]["path"] if records else None,
        "last_canonical_path": records[-1]["path"] if records else None,
        "records": records,
    }


def write_inventory_bundle(
    inventory: dict[str, Any],
    output_dir: Path,
) -> None:
    output = output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "baseline_tracked_cad_inventory.json"
    csv_path = output / "baseline_tracked_cad_inventory.csv"
    receipt_path = output / "baseline_tracked_cad_inventory.sha256"
    json_path.write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(CSV_FIELDS),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(
            {field: record[field] for field in CSV_FIELDS}
            for record in inventory["records"]
        )
    receipt_path.write_text(
        f'{inventory["inventory_sha256"]}  {RECEIPT_NAME}\n',
        encoding="ascii",
        newline="\n",
    )


def _csv_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise ValueError("INVENTORY_CSV_HEADER_MISMATCH")
        return [
            {
                "path": row["path"],
                "extension": row["extension"],
                "bytes": int(row["bytes"]),
                "git_blob_sha1": row["git_blob_sha1"],
                "sha256": row["sha256"],
            }
            for row in reader
        ]


def _receipt_hash(path: Path) -> str:
    content = path.read_text(encoding="ascii")
    match = re.fullmatch(
        rf"([0-9a-f]{{64}})  {re.escape(RECEIPT_NAME)}\n",
        content,
    )
    if not match:
        raise ValueError("INVENTORY_SHA256_RECEIPT_FORMAT_INVALID")
    return match.group(1)


def validate_inventory_bundle(
    json_path: Path,
    csv_path: Path,
    receipt_path: Path,
) -> dict[str, Any]:
    inventory = json.loads(json_path.read_text(encoding="utf-8"))
    if inventory.get("inventory_hash_algorithm") != ALGORITHM_IDENTIFIER:
        raise ValueError("INVENTORY_ALGORITHM_IDENTIFIER_MISMATCH")
    input_records = inventory.get("records", [])
    canonical_records = canonicalize_records(input_records)
    if input_records != canonical_records:
        raise ValueError("JSON_RECORDS_NOT_CANONICAL_ORDER_OR_FORM")
    calculated = canonical_inventory_sha256(canonical_records)
    if inventory.get("inventory_sha256") != calculated:
        raise ValueError("INVENTORY_JSON_SHA256_MISMATCH")
    csv_records = _csv_records(csv_path)
    if csv_records != canonical_records:
        raise ValueError("JSON_CSV_RECORD_ORDER_OR_CONTENT_MISMATCH")
    receipt = _receipt_hash(receipt_path)
    if receipt != calculated:
        raise ValueError("INVENTORY_SHA256_RECEIPT_MISMATCH")
    if inventory.get("TRACKED_CAD_TOTAL_COUNT") != len(canonical_records):
        raise ValueError("INVENTORY_TOTAL_COUNT_MISMATCH")
    return {
        "status": "PASS",
        "algorithm_identifier": ALGORITHM_IDENTIFIER,
        "record_count": len(canonical_records),
        "calculated_sha256": calculated,
        "recorded_sha256": inventory["inventory_sha256"],
        "json_csv_order_consistency": "PASS",
        "receipt_consistency": "PASS",
        "first_canonical_path": (
            canonical_records[0]["path"] if canonical_records else None
        ),
        "last_canonical_path": (
            canonical_records[-1]["path"] if canonical_records else None
        ),
    }


def replay_inventory(
    records: list[dict[str, Any]],
    *,
    recorded_sha256: str,
    shuffle_seed: int = 229391,
) -> dict[str, Any]:
    canonical = canonicalize_records(records)
    calculated = canonical_inventory_sha256(canonical)
    reversed_records = list(reversed(records))
    shuffled_records = list(records)
    random.Random(shuffle_seed).shuffle(shuffled_records)
    reversed_hash = canonical_inventory_sha256(reversed_records)
    shuffled_hash = canonical_inventory_sha256(shuffled_records)
    return {
        "schema": "PS_CANONICAL_INVENTORY_HASH_REPLAY_V0_1",
        "algorithm_identifier": ALGORITHM_IDENTIFIER,
        "input_record_count": len(records),
        "canonical_record_count": len(canonical),
        "duplicate_path_count": 0,
        "first_canonical_path": canonical[0]["path"] if canonical else None,
        "last_canonical_path": canonical[-1]["path"] if canonical else None,
        "calculated_sha256": calculated,
        "recorded_sha256": recorded_sha256,
        "match": calculated == recorded_sha256,
        "shuffle_seed": shuffle_seed,
        "shuffled_replay_sha256": shuffled_hash,
        "shuffled_replay_match": shuffled_hash == calculated,
        "reversed_replay_sha256": reversed_hash,
        "reversed_replay_match": reversed_hash == calculated,
    }


def replay_text(report: dict[str, Any]) -> str:
    keys = (
        "algorithm_identifier",
        "input_record_count",
        "canonical_record_count",
        "duplicate_path_count",
        "first_canonical_path",
        "last_canonical_path",
        "calculated_sha256",
        "recorded_sha256",
        "match",
        "shuffle_seed",
        "shuffled_replay_sha256",
        "shuffled_replay_match",
        "reversed_replay_sha256",
        "reversed_replay_match",
    )
    return "\n".join(f"{key} = {report[key]}" for key in keys) + "\n"
