from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_reinforced_guard_reaction_yoke_v0_9_6_9.py"
spec = importlib.util.spec_from_file_location("reinforced_guard_reaction_yoke_v0969", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load builder: {BUILDER}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def main() -> None:
    checks = module.contract_checks(LANE, repo_checks=True)
    failures = []
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        if not ok:
            failures.append((name, detail))
    print(f"CONTRACT={len(checks) - len(failures)}/{len(checks)} {'PASS' if not failures else 'FAIL'}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
