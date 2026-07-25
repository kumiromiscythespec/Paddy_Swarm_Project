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
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    parser.add_argument("--text", type=Path)
    return parser.parse_args(argv)


def _require_external(path: Path | None) -> None:
    if path is None:
        return
    for candidate in (MODULE_DIR, *MODULE_DIR.parents):
        if (candidate / ".git").exists():
            root = candidate.resolve()
            break
    else:
        raise RuntimeError("REPOSITORY_ROOT_NOT_FOUND")
    resolved = path.resolve()
    if resolved == root or root in resolved.parents:
        raise ValueError("TEST_OUTPUT_MUST_BE_OUTSIDE_REPOSITORY")


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
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    duration = round(time.perf_counter() - started, 6)
    text_output = stream.getvalue()
    summary = {
        "schema": "PS_PRODUCTION_INPUT_AUDIT_TESTS_V0_1",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "successful": result.wasSuccessful(),
        "duration_seconds": duration,
    }
    sys.stdout.write(text_output)
    for path, content in (
        (args.text, text_output),
        (args.json, json.dumps(summary, indent=2, sort_keys=True) + "\n"),
    ):
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
