from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest


MODULE_DIR = Path(__file__).resolve().parent
AUDIT_LANE = MODULE_DIR.parent / (
    "v2_29_3_9_1_production_intent_input_audit_v0_1"
)
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))


def _repository_root() -> Path:
    for path in (MODULE_DIR, *MODULE_DIR.parents):
        if (path / ".git").exists():
            return path.resolve()
    raise RuntimeError("REPOSITORY_ROOT_NOT_FOUND")


def _require_external(path: Path | None) -> None:
    if path is None:
        return
    root = _repository_root()
    resolved = path.resolve()
    if resolved == root or root in resolved.parents:
        raise ValueError("TEST_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")


def _inherited_suite() -> tuple[int, int, int, bool, str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(AUDIT_LANE / "run_unit_tests.py"),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    output = completed.stdout + completed.stderr
    count_match = re.search(r"Ran (\d+) tests?", output)
    count = int(count_match.group(1)) if count_match else 0
    failures_match = re.search(r"failures=(\d+)", output)
    errors_match = re.search(r"errors=(\d+)", output)
    failures = int(failures_match.group(1)) if failures_match else 0
    errors = int(errors_match.group(1)) if errors_match else 0
    if completed.returncode != 0 and not (failures or errors):
        errors = 1
    return count, failures, errors, completed.returncode == 0, output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    parser.add_argument("--text", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _require_external(args.json)
    _require_external(args.text)
    suite = unittest.defaultTestLoader.discover(
        str(MODULE_DIR / "tests"),
        pattern="test_*.py",
        top_level_dir=str(MODULE_DIR),
    )
    stream = io.StringIO()
    started = time.perf_counter()
    current = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    inherited_count, inherited_failures, inherited_errors, inherited_ok, (
        inherited_output
    ) = _inherited_suite()
    duration = round(time.perf_counter() - started, 6)
    current_output = stream.getvalue()
    combined_output = (
        "CURRENT REAL-PROFILE REGISTRATION TESTS\n"
        + current_output
        + "\nINHERITED PRODUCTION-INPUT AUDIT TESTS\n"
        + inherited_output
    )
    successful = current.wasSuccessful() and inherited_ok
    summary = {
        "schema": "PS_REAL_PROFILE_REGISTRATION_TESTS_V0_1",
        "tests_run": current.testsRun + inherited_count,
        "current_tests_run": current.testsRun,
        "inherited_tests_run": inherited_count,
        "failures": len(current.failures) + inherited_failures,
        "errors": len(current.errors) + inherited_errors,
        "skipped": len(current.skipped),
        "successful": successful,
        "duration_seconds": duration,
    }
    sys.stdout.write(combined_output)
    for path, content in (
        (args.text, combined_output),
        (args.json, json.dumps(summary, indent=2, sort_keys=True) + "\n"),
    ):
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
