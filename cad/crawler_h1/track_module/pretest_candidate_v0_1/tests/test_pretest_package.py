from pathlib import Path
import hashlib
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PretestPackageTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(
            (ROOT / "manifest/pretest_candidate_contract.json").read_text(encoding="utf-8")
        )

    def test_exactly_five_candidate_stls(self):
        self.assertEqual(len(self.contract["candidate_parts"]), 5)
        stls = list(ROOT.glob("stl/**/*.stl"))
        self.assertEqual(len(stls), 5)

    def test_candidate_hashes(self):
        for part in self.contract["candidate_parts"]:
            path = ROOT / part["dest_path"]
            self.assertTrue(path.is_file(), path)
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(actual, part["sha256"], path)

    def test_mesh_audit_was_single_component_watertight(self):
        for part in self.contract["candidate_parts"]:
            self.assertTrue(part["mesh"]["watertight"], part["role"])
            self.assertEqual(part["mesh"]["connected_components"], 1, part["role"])

    def test_no_bytecode(self):
        self.assertFalse(list(ROOT.rglob("*.pyc")))
        self.assertFalse(list(ROOT.rglob("*.pyo")))
        self.assertFalse([p for p in ROOT.rglob("__pycache__") if p.is_dir()])

if __name__ == "__main__":
    unittest.main()
