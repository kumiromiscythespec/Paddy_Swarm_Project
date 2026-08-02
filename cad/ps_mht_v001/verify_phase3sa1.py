"""Run the complete PS-MHT test suite with one fresh OCCT process per file."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
EXPECTED_TEST_COUNT = 242


def main() -> None:
    environment = os.environ.copy()
    python_path = str(PACKAGE_ROOT.parent)
    if environment.get("PYTHONPATH"):
        python_path += os.pathsep + environment["PYTHONPATH"]
    environment["PYTHONPATH"] = python_path
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    total = 0
    results: list[dict[str, object]] = []
    for test_path in sorted((PACKAGE_ROOT / "tests").glob("test_*.py")):
        if test_path.name.startswith(
            ("test_phase3sa2_", "test_phase3pa_")
        ):
            continue
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(test_path),
                "-q",
                "-o",
                f"cache_dir={PACKAGE_ROOT / '.pytest_cache'}",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
        summary = result.stdout + result.stderr
        match = re.search(r"(\d+) passed", summary)
        passed = int(match.group(1)) if match else 0
        total += passed
        results.append(
            {
                "file": test_path.name,
                "passed": passed,
                "returncode": result.returncode,
            }
        )
        print(
            json.dumps(results[-1], ensure_ascii=False),
            flush=True,
        )
        if result.returncode:
            print(summary, flush=True)
            raise SystemExit(result.returncode)

    if total != EXPECTED_TEST_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_TEST_COUNT} tests, got {total}"
        )
    print(
        json.dumps(
            {
                "phase": "3S-A.1",
                "total_passed": total,
                "files": len(results),
                "all_passed": True,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
