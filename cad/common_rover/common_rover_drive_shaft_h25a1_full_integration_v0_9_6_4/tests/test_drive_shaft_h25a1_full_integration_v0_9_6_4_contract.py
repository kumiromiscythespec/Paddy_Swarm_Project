#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_drive_shaft_h25a1_full_integration_v0_9_6_4.py"
spec = importlib.util.spec_from_file_location("v0964_builder", BUILDER)
module = importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
CHECKS = module.contract_checks(LANE, repo_checks=True); assert len(CHECKS) == 60

class Contract(unittest.TestCase): maxDiff = None
def make_test(name, passed, detail):
    def test(self): self.assertTrue(passed, f"{name}: {detail}")
    return test
for i, (name, passed, detail) in enumerate(CHECKS, 1): setattr(Contract, f"test_{i:03d}_{name.replace('-', '_')}", make_test(name, passed, detail))
if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"CONTRACT_RESULT={passed}/{result.testsRun} PASS" if result.wasSuccessful() else "CONTRACT_RESULT=FAIL")
    sys.exit(0 if result.wasSuccessful() else 1)
