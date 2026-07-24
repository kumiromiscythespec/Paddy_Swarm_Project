from __future__ import annotations

import argparse
import json
from pathlib import Path
import branch_probe
from authority_core import validate_all


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", default=str(Path(__file__).resolve().parent))
    args = parser.parse_args()
    branch_probe.reset()
    result = validate_all(args.lane)
    result["coverage"] = branch_probe.snapshot()
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "PASS_WITH_HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
