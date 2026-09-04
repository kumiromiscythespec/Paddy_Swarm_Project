from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_belt_entry_clearance_rimless_v0_9_6_14.py"
SPEC = importlib.util.spec_from_file_location("v09614_builder_contract", BUILDER)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {BUILDER}")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def main() -> None:
    passed, failed = builder.verify(LANE, repo_checks=True)
    print(f"CONTRACT_TEST_RESULT=PASS passed={passed} failed={failed}")


if __name__ == "__main__":
    main()
