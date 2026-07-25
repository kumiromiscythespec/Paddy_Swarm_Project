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


def _external(path: Path | None) -> None:
    if path is None:
        return
    resolved = path.resolve()
    for parent in (MODULE_DIR, *MODULE_DIR.parents):
        if (parent / ".git").exists():
            root = parent.resolve()
            break
    else:
        raise RuntimeError("REPOSITORY_ROOT_NOT_FOUND")
    if resolved == root or root in resolved.parents:
        raise ValueError("TEST_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    parser.add_argument("--text", type=Path)
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    _external(args.json)
    _external(args.text)
    suite = unittest.defaultTestLoader.discover(
        str(MODULE_DIR / "tests"),
        pattern="test_*.py",
        top_level_dir=str(MODULE_DIR),
    )
    stream = io.StringIO()
    started = time.perf_counter()
    result = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
    ).run(suite)
    duration = round(time.perf_counter() - started, 6)
    run_id = args.run_id or "UNSPECIFIED_DEVELOPMENT_RUN"
    text_output = f"run_id={run_id}\n" + stream.getvalue()
    summary = {
        "schema": "PS_PROGRESSIVE_FULL_SCALE_DUMMY_TESTS_V0_1",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "successful": result.wasSuccessful(),
        "duration_seconds": duration,
        "run_id": run_id,
    }
    sys.stdout.write(text_output)
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
