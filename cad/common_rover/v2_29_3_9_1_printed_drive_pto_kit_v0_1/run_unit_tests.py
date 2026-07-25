from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import unittest

from generate_drive_pto_kit import finalize_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    arguments = parser.parse_args()
    artifact = arguments.artifact_dir.resolve()
    os.environ["PS_DRIVE_PTO_ARTIFACT_DIR"] = str(artifact)
    suite = unittest.defaultTestLoader.discover(
        str(Path(__file__).resolve().parent / "tests"),
        pattern="test_*.py",
    )
    stream = io.StringIO()
    result = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
    ).run(suite)
    text = stream.getvalue()
    report = {
        "schema": "PS_DRIVE_PTO_UNIT_TEST_RESULTS_V0_1",
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun,
        "failures": [
            {"test": str(test), "traceback": traceback}
            for test, traceback in result.failures
        ],
        "errors": [
            {"test": str(test), "traceback": traceback}
            for test, traceback in result.errors
        ],
        "skipped": [
            {"test": str(test), "reason": reason}
            for test, reason in result.skipped
        ],
    }
    (artifact / "unit_test_results.txt").write_text(
        text, encoding="utf-8", newline="\n"
    )
    (artifact / "unit_test_results.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    completion_path = artifact / "completion_status.json"
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    completion["UNIT_TESTS"] = report["status"]
    completion_path.write_text(
        json.dumps(completion, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    finalize_bundle(artifact)
    print(text, end="")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
