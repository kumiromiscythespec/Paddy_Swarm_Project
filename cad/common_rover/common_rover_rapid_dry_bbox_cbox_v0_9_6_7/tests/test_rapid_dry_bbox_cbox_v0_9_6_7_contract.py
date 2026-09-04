from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path
LANE=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("v0967_builder",LANE/"build_rapid_dry_bbox_cbox_v0_9_6_7.py")
b=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(b)
CHECKS=b.contract_checks(LANE,repo_checks=True)
class Contract(unittest.TestCase): pass
def make_test(ok,detail):
    def test(self): self.assertTrue(ok,detail)
    return test
for i,(name,ok,detail) in enumerate(CHECKS,1): setattr(Contract,f"test_{i:03d}_{name.replace('-','_')}",make_test(ok,detail))
if __name__=="__main__":
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
    print(f"CONTRACT_RESULT={result.testsRun-len(result.failures)-len(result.errors)}/{result.testsRun} PASS" if result.wasSuccessful() else "CONTRACT_RESULT=FAIL")
    raise SystemExit(0 if result.wasSuccessful() else 1)
