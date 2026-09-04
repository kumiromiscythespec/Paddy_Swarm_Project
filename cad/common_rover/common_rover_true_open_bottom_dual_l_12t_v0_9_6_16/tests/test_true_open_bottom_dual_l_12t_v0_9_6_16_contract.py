from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


BUILDER = Path(__file__).resolve().parents[1] / "build_true_open_bottom_dual_l_12t_v0_9_6_16.py"
spec = importlib.util.spec_from_file_location("true_open_bottom_v09616", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load builder: {BUILDER}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

CHECKS = module.contract_checks(module.DEFAULT_LANE, True)


class TrueOpenBottomDualLContract(unittest.TestCase):
    maxDiff = None


def _make_test(name: str, ok: bool, detail: object):
    def test(self: TrueOpenBottomDualLContract) -> None:
        self.assertTrue(ok, json.dumps({"check": name, "detail": detail}, ensure_ascii=False, default=str))
    return test


for index, (name, ok, detail) in enumerate(CHECKS, 1):
    safe = "".join(character if character.isalnum() else "_" for character in name)
    setattr(TrueOpenBottomDualLContract, f"test_{index:03d}_{safe}", _make_test(name, ok, detail))


if __name__ == "__main__":
    unittest.main(verbosity=2)
