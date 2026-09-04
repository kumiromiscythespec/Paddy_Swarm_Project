#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_cbox_drive_electrical_physical_integration_v0_9_6_2.py"
spec = importlib.util.spec_from_file_location("v0962_builder", BUILDER)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
CHECKS = module.contract_checks(LANE, repo_checks=True)
assert len(CHECKS) == 50

class Contract(unittest.TestCase):
    maxDiff = None

def make_test(index, name, passed, detail):
    def test(self):
        self.assertTrue(passed, f"{name}: {detail}")
    test.__name__ = f"test_{index + 1:03d}_{name.lower().replace('-', '_').replace(' ', '_')}"
    return test

for i, (name, passed, detail) in enumerate(CHECKS):
    setattr(Contract, f"test_{i + 1:03d}", make_test(i, name, passed, detail))

if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
    print(f"CONTRACT_RESULT={result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} PASS" if result.wasSuccessful() else "CONTRACT_RESULT=FAIL")
    sys.exit(0 if result.wasSuccessful() else 1)
