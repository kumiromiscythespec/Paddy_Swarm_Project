"""Executable contract for Candidate-C/MISUMI keeperless V003."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_candidate_c_12t_misumi_groove1_keeperless_v003.py"
spec = importlib.util.spec_from_file_location("candidate_c_groove1_keeperless_v003_contract", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("BUILDER_IMPORT_FAIL")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

checks = module.contract_checks(LANE, repo_checks=True)
failed = []
for index, (name, passed, detail) in enumerate(checks, 1):
    print(f"test_{index:03d}_{name}: {'PASS' if passed else 'FAIL'} | {detail}")
    if not passed:
        failed.append(name)
print(f"RESULT={len(checks) - len(failed)}/{len(checks)} PASS")
if failed:
    raise SystemExit("FAILED: " + ", ".join(failed))
