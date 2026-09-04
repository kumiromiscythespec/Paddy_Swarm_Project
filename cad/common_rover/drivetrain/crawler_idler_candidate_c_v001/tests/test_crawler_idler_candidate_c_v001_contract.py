"""Contract tests for Candidate-C crawler idler V001."""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_crawler_idler_candidate_c_v001.py"
spec = importlib.util.spec_from_file_location("crawler_idler_candidate_c_v001", BUILDER)
assert spec and spec.loader
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validation = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.parameters = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
        cls.generated = b.contract_checks(LANE, repo_checks=False)

    def test_001_repository_guard(self):
        report = b.guard(True)
        self.assertTrue(all(report["checks"].values()), report)

    def test_002_exact_paths(self):
        actual = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
        self.assertEqual(actual, b.EXPECTED)

    def test_003_commit_paths_exact(self):
        rows = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(rows, [f"{b.LANE_REL.as_posix()}/{path}" for path in b.EXPECTED])

    def test_004_source_hashes(self):
        self.assertEqual({path: b.sha(b.ROOT / path) for path in b.INPUT_SHA}, b.INPUT_SHA)

    def test_005_authority_hashes(self):
        self.assertEqual({path: b.sha(b.ROOT / path) for path in b.AUTHORITY}, b.AUTHORITY)

    def test_006_protected_trees(self):
        self.assertEqual({path: b.tree(b.ROOT / path) for path in b.PROTECTED}, b.PROTECTED)

    def test_007_status(self):
        self.assertEqual(self.parameters["status"], b.STATUS)

    def test_008_no_drive_architecture(self):
        legacy = self.parameters["forbidden_drive_architecture"]
        self.assertEqual(legacy["MISUMI_GROOVE1_DRIVE_INTERFACE"], "ABSENT")
        self.assertEqual(legacy["KEYED_TORQUE_PATH"], "ABSENT")
        self.assertEqual(legacy["OLD_SHAFT_COLLAR_DRIVE_PATH"], "ABSENT")

    def test_009_idler_bearing_architecture(self):
        legacy = self.parameters["forbidden_drive_architecture"]
        self.assertEqual(legacy["IDLER_ROTATION_ARCHITECTURE"], "EXISTING_BEARING_BASED_AUTHORITY")

    def test_010_reproducibility(self):
        report = self.validation["reproducibility"]
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["compared"], report["byte_identical"])


def _add_generated(index: int, name: str, passed: bool, detail: object) -> None:
    def test(self):
        self.assertTrue(passed, f"{name}: {detail}")
    setattr(Contract, f"test_{index:03d}_{name.replace('-', '_')}", test)


# Each builder contract is also exposed as an individually counted unittest.
for _offset, (_name, _passed, _detail) in enumerate(b.contract_checks(LANE, repo_checks=False), start=11):
    _add_generated(_offset, _name, _passed, _detail)


if __name__ == "__main__":
    unittest.main(verbosity=2)
