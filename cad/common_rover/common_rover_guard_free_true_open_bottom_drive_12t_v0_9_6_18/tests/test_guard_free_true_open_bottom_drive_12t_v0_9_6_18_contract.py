from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_guard_free_true_open_bottom_drive_12t_v0_9_6_18.py"
SPEC = importlib.util.spec_from_file_location("v09618_contract_subject", BUILDER)
assert SPEC is not None and SPEC.loader is not None
subject = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = subject
SPEC.loader.exec_module(subject)


def test_all_contracts() -> None:
    checks = subject.contract_checks(LANE, repo_checks=False)
    failures = [(name, detail) for name, ok, detail in checks if not ok]
    assert not failures, failures
