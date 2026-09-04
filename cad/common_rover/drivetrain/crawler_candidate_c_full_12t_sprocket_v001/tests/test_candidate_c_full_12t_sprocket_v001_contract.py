from __future__ import annotations
import importlib.util
from pathlib import Path
import sys

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_candidate_c_full_12t_sprocket_v001.py"
spec = importlib.util.spec_from_file_location("candidate_c_full12_contract_builder", BUILDER)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

checks = module.contract_checks(LANE, repo_checks=True)
failed = []
for index, (name, passed, detail) in enumerate(checks, 1):
    print(f"test_{index:03d}_{name}: {'PASS' if passed else 'FAIL'} | {detail}")
    if not passed:
        failed.append(name)
print(f"RESULT={len(checks)-len(failed)}/{len(checks)} PASS")
if failed:
    raise SystemExit("FAILED: " + ", ".join(failed))
