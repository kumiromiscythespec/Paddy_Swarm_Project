"""Optional development audit for the external CUT-DUMMY tree.

This module is deliberately not imported by the normal HHD generator.  The
audit compares individual relative-path SHA-256 values as its decision basis;
the aggregate SHA-256 is diagnostic only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Mapping

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


DEFAULT_BASELINE_PATH = Path(__file__).with_name(
    "protected_dummy_baseline_v010.json"
)


class ProtectedDummyAuditError(RuntimeError):
    """CUT-DUMMY differs from the optional development baseline."""


def _path_sort_key(relative_path: str) -> tuple[str, str]:
    """Return a stable cross-platform order key for a POSIX relative path."""

    return relative_path.casefold(), relative_path


def aggregate_file_hashes(file_hashes: Mapping[str, str]) -> str:
    """Return a deterministic diagnostic aggregate for individual hashes."""

    canonical = "\n".join(
        f"{relative_path}\t{file_hashes[relative_path]}"
        for relative_path in sorted(file_hashes, key=_path_sort_key)
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def protected_dummy_snapshot(dummy_root: str | Path) -> dict[str, object]:
    """Hash CUT-DUMMY files in an OS-independent relative-path order."""

    root = Path(dummy_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"CUT-DUMMY audit root does not exist: {root}")

    paths = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: _path_sort_key(path.relative_to(root).as_posix()),
    )
    files = [
        {
            "relative_path": path.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in paths
    ]
    file_hashes = {
        str(item["relative_path"]): str(item["sha256"]) for item in files
    }
    return {
        "root": str(root),
        "file_count": len(files),
        "aggregate_sha256": aggregate_file_hashes(file_hashes),
        "files": files,
    }


def load_baseline(
    baseline_path: str | Path = DEFAULT_BASELINE_PATH,
) -> dict[str, str]:
    """Load the versioned per-file audit baseline."""

    path = Path(baseline_path)
    if not path.is_file():
        raise FileNotFoundError(f"CUT-DUMMY audit baseline does not exist: {path}")
    document = json.loads(path.read_text(encoding="utf-8"))
    files = document.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError(f"CUT-DUMMY audit baseline has no file hashes: {path}")
    result = {str(name): str(digest) for name, digest in files.items()}
    if any(len(digest) != 64 for digest in result.values()):
        raise ValueError(f"CUT-DUMMY audit baseline has an invalid SHA-256: {path}")
    return result


def compare_protected_dummy(
    dummy_root: str | Path,
    expected_file_hashes: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Compare individual files and return a non-raising audit report."""

    expected = dict(
        load_baseline()
        if expected_file_hashes is None
        else expected_file_hashes
    )
    snapshot = protected_dummy_snapshot(dummy_root)
    actual = {
        str(item["relative_path"]): str(item["sha256"])
        for item in snapshot["files"]
    }

    missing = sorted(set(expected) - set(actual), key=_path_sort_key)
    unexpected = sorted(set(actual) - set(expected), key=_path_sort_key)
    modified = [
        {
            "relative_path": relative_path,
            "expected_sha256": expected[relative_path],
            "actual_sha256": actual[relative_path],
        }
        for relative_path in sorted(set(expected) & set(actual), key=_path_sort_key)
        if expected[relative_path] != actual[relative_path]
    ]
    individual_file_match = not (missing or unexpected or modified)
    expected_aggregate = aggregate_file_hashes(expected)
    return {
        "audit": "optional_development_check",
        "decision_basis": "individual_file_sha256",
        "verified_unchanged": individual_file_match,
        "individual_file_match": individual_file_match,
        "expected_file_count": len(expected),
        "actual_file_count": snapshot["file_count"],
        "missing_files": missing,
        "unexpected_files": unexpected,
        "modified_files": modified,
        "expected_aggregate_sha256": expected_aggregate,
        "actual_aggregate_sha256": snapshot["aggregate_sha256"],
        "aggregate_match": expected_aggregate == snapshot["aggregate_sha256"],
        "aggregate_role": "diagnostic_only",
        "root": snapshot["root"],
        "files": snapshot["files"],
    }


def audit_protected_dummy(
    dummy_root: str | Path,
    *,
    baseline_path: str | Path = DEFAULT_BASELINE_PATH,
    report_path: str | Path | None = None,
) -> dict[str, object]:
    """Run the optional audit, optionally write a report, and fail on changes."""

    expected = load_baseline(baseline_path)
    report = compare_protected_dummy(dummy_root, expected)
    if report_path is not None:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if not report["individual_file_match"]:
        raise ProtectedDummyAuditError(
            "CUT-DUMMY optional audit failed by individual file SHA-256: "
            f"missing={len(report['missing_files'])}, "
            f"unexpected={len(report['unexpected_files'])}, "
            f"modified={len(report['modified_files'])}"
        )
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse optional development-audit CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dummy_root", type=Path, help="CUT-DUMMY directory")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help=f"per-file baseline JSON (default: {DEFAULT_BASELINE_PATH})",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="optional JSON report path, e.g. out/reports/audit/...",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the optional audit from the command line."""

    args = parse_args(argv)
    report = audit_protected_dummy(
        args.dummy_root,
        baseline_path=args.baseline,
        report_path=args.report,
    )
    print(
        "CUT-DUMMY optional audit passed: "
        f"{report['actual_file_count']} individual files; "
        f"aggregate={report['actual_aggregate_sha256']} (diagnostic only)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
