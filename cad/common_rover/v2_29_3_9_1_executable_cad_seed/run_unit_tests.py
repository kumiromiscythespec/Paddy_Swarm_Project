from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import sys
import time
import unittest


MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the deterministic executable-seed unit tests."
    )
    parser.add_argument("--json", type=Path, help="Optional machine-readable summary.")
    parser.add_argument("--text", type=Path, help="Optional complete test output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    suite = unittest.defaultTestLoader.discover(
        str(MODULE_DIR / "tests"), pattern="test_*.py", top_level_dir=str(MODULE_DIR)
    )
    stream = io.StringIO()
    started = time.perf_counter()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    duration = time.perf_counter() - started
    text_output = stream.getvalue()
    sys.stdout.write(text_output)
    summary = {
        "schema": "PS_COMMON_ROVER_V229391_EXECUTABLE_CAD_SEED_TEST_SUMMARY_V1",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "successful": result.wasSuccessful(),
        "duration_seconds": round(duration, 6),
    }
    if args.text is not None:
        args.text.parent.mkdir(parents=True, exist_ok=True)
        args.text.write_text(text_output, encoding="utf-8", newline="\n")
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return 0 if result.wasSuccessful() else 1
if __name__ == "__main__":
    raise SystemExit(main())
