from __future__ import annotations

import argparse
import io
import json
import unittest
from pathlib import Path
import branch_probe


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--text", required=True)
    args = parser.parse_args()
    branch_probe.reset()
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent / "tests"))
    ids = sorted(test.id() for test in flatten(suite))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    payload = {
        "count": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "successful": result.wasSuccessful(), "test_ids": ids,
        "coverage": branch_probe.snapshot(),
    }
    Path(args.json).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.text).write_text(stream.getvalue(), encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
