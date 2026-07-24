from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from validation import validate_seed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build and validate the six-solid Common Rover v2.29.3.9.1 "
            "minimum assembly seed."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON report path. No CAD exchange file is retained.",
    )
    parser.add_argument(
        "--no-step-roundtrip",
        action="store_true",
        help="Skip the verification-only STEP export/import in OS temporary storage.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = validate_seed(include_step_roundtrip=not args.no_step_roundtrip)
    rendered = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    sys.stdout.write(rendered)
    return 0 if report["EXECUTABLE_CAD_SEED_STATUS"] == "PASS_WITH_HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
