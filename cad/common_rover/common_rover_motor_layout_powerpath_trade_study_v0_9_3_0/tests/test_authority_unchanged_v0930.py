from __future__ import annotations

import json
import os
import sys
import unittest
import zipfile
from pathlib import Path, PurePosixPath

LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))
import build_motor_layout_powerpath_trade_study_v0930 as b


class AuthorityAndPackageContract(unittest.TestCase):
    def test_001_parent_ledgers_unchanged(self) -> None:
        audit = b.parent_protection_audit()
        self.assertEqual(audit["status"], "PASS")
        self.assertTrue(all(row["pass"] for row in audit["protected_lanes"]))

    def test_002_authority_pointers_unchanged(self) -> None:
        audit = b.parent_protection_audit()
        self.assertTrue(all(row["pass"] for row in audit["authority_pointers"]))

    def test_003_authority_update_prohibited(self) -> None:
        audit = json.loads((LANE / "common_rover_current_motor_layout_authority_audit_v0930.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["design_authority_update"], "PROHIBITED")
        decision = json.loads((LANE / "recommended_layout_decision_v0930.json").read_text(encoding="utf-8"))
        self.assertEqual(decision["DESIGN_AUTHORITY"], "UNCHANGED")

    def test_004_coordinate_difference_is_recorded(self) -> None:
        audit = json.loads((LANE / "common_rover_current_motor_layout_authority_audit_v0930.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["coordinate_authority"]["X"], "lateral +left")
        self.assertEqual(audit["legacy_v0921_difference"]["disposition"], "NOT_AUTOMATICALLY_ADOPTED")

    def test_005_manifest_exact_151(self) -> None:
        report = b.verify_manifest()
        self.assertEqual(report["entry_count"], 151)
        self.assertEqual(report["status"], "PASS")

    def test_006_sha256_ledger_exact(self) -> None:
        report = b.verify_hashes()
        self.assertEqual(report["verified_path_count"], 150)
        self.assertEqual(report["status"], "PASS")

    def test_007_no_cache_or_forbidden_formats(self) -> None:
        paths = b._lane_files()
        self.assertFalse(any("__pycache__" in path.lower() or path.lower().endswith((".pyc", ".pyo", ".fcstd", ".blend", ".tmp")) for path in paths))

    def test_008_commit_paths_are_intent_only(self) -> None:
        rows = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows), 151)
        self.assertTrue(all("common_rover_motor_layout_powerpath_trade_study_v0_9_3_0/" in row for row in rows))

    def test_009_handoff_zip_exists_and_is_scoped(self) -> None:
        requested = os.environ.get("V0930_TEST_ZIP")
        path = Path(requested) if requested else b.latest_handoff_zip()
        self.assertIsNotNone(path, "package phase must provide a handoff ZIP")
        self.assertTrue(path.is_file())
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            self.assertEqual(names, list(b.PACKAGE_PATHS))
            self.assertEqual(len(names), len(set(names)))
            self.assertFalse(any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name for name in names))

    def test_010_live_repository_guard_or_standalone(self) -> None:
        report = b.repository_audit()
        self.assertEqual(report["status"], "PASS")
        self.assertIn(report["mode"], ("LIVE_REPOSITORY", "STANDALONE_HANDOFF"))

    def test_011_release_prohibitions(self) -> None:
        text = (LANE / "NO_MANUFACTURING_RELEASE.txt").read_text(encoding="utf-8")
        for token in ("DESIGN_AUTHORITY_UPDATE=PROHIBITED", "PURCHASE_APPROVAL=NOT_APPROVED", "POWERED_TEST=NOT_APPROVED", "FIELD_DEPLOYMENT=NOT_APPROVED"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
