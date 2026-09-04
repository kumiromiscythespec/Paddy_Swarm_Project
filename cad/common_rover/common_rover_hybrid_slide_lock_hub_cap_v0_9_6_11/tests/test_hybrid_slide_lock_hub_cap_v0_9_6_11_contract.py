from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_hybrid_slide_lock_hub_cap_v0_9_6_11.py"
spec = importlib.util.spec_from_file_location("v09611_builder", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load builder: {BUILDER}")
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


def main() -> None:
    total, failures = builder.verify(LANE, True)
    if failures:
        raise SystemExit(1)
    print(f"CONTRACT={total}/{total} PASS")


if __name__ == "__main__":
    main()
