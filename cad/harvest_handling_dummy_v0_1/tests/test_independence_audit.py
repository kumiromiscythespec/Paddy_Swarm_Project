"""Independent generation and optional CUT-DUMMY audit tests."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

CAD_ROOT = Path(__file__).resolve().parents[2]
if str(CAD_ROOT) not in sys.path:
    sys.path.insert(0, str(CAD_ROOT))

from harvest_handling_dummy_v0_1.audit_protected_dummy import (
    ProtectedDummyAuditError,
    aggregate_file_hashes,
    audit_protected_dummy,
    compare_protected_dummy,
    protected_dummy_snapshot,
)
from harvest_handling_dummy_v0_1.generate_harvest_handling_dummy_v0_1 import (
    generate_all,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OptionalProtectedDummyAuditTests(unittest.TestCase):
    """CUT-DUMMY checks are explicit, per-file, and deterministic."""

    def test_missing_cut_dummy_fails_only_when_optional_audit_is_called(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "dummy_panicle_v0_1"
            with self.assertRaisesRegex(
                FileNotFoundError,
                "CUT-DUMMY audit root does not exist",
            ):
                protected_dummy_snapshot(missing)

    def test_optional_audit_detects_individual_file_change(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "dummy_panicle_v0_1"
            root.mkdir()
            source = root / "source.py"
            source.write_text("baseline\n", encoding="utf-8")
            baseline_path = Path(temporary) / "baseline.json"
            baseline_path.write_text(
                json.dumps(
                    {
                        "files": {
                            "source.py": _sha256(source),
                        }
                    }
                ),
                encoding="utf-8",
            )

            passed = audit_protected_dummy(root, baseline_path=baseline_path)
            self.assertTrue(passed["individual_file_match"])

            source.write_text("future CUT-DUMMY revision\n", encoding="utf-8")
            comparison = compare_protected_dummy(
                root,
                {"source.py": hashlib.sha256(b"baseline\n").hexdigest()},
            )
            self.assertFalse(comparison["individual_file_match"])
            self.assertEqual(
                [item["relative_path"] for item in comparison["modified_files"]],
                ["source.py"],
            )
            with self.assertRaisesRegex(
                ProtectedDummyAuditError,
                "individual file SHA-256",
            ):
                audit_protected_dummy(root, baseline_path=baseline_path)

    def test_snapshot_aggregate_is_independent_of_rglob_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "dummy_panicle_v0_1"
            (root / "nested").mkdir(parents=True)
            (root / "zeta.txt").write_text("z", encoding="utf-8")
            (root / "Alpha.txt").write_text("A", encoding="utf-8")
            (root / "alpha.txt").write_text("a", encoding="utf-8")
            (root / "nested" / "middle.txt").write_text("m", encoding="utf-8")

            expected = protected_dummy_snapshot(root)
            discovered = list(root.rglob("*"))
            with mock.patch.object(
                Path,
                "rglob",
                return_value=iter(reversed(discovered)),
            ):
                reversed_order = protected_dummy_snapshot(root)

            self.assertEqual(
                expected["aggregate_sha256"],
                reversed_order["aggregate_sha256"],
            )
            self.assertEqual(expected["files"], reversed_order["files"])

    def test_aggregate_is_diagnostic_not_the_primary_decision(self) -> None:
        file_hashes = {
            "B.txt": hashlib.sha256(b"B").hexdigest(),
            "a.txt": hashlib.sha256(b"a").hexdigest(),
        }
        self.assertEqual(
            aggregate_file_hashes(dict(reversed(tuple(file_hashes.items())))),
            aggregate_file_hashes(file_hashes),
        )


class NormalGenerationIndependenceTests(unittest.TestCase):
    """Normal generation never calls or reports the optional audit."""

    def test_changed_cut_dummy_does_not_block_normal_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            changed_dummy = root / "dummy_panicle_v0_1"
            changed_dummy.mkdir()
            changed_file = changed_dummy / "unexpected.txt"
            changed_file.write_text("future revision", encoding="utf-8")
            baseline = {
                "unexpected.txt": hashlib.sha256(b"old revision").hexdigest()
            }
            self.assertFalse(
                compare_protected_dummy(changed_dummy, baseline)[
                    "individual_file_match"
                ]
            )

            output = root / "hhd_output"
            records, preview = generate_all(output)
            self.assertEqual(len(records), 26)
            self.assertEqual(preview.preview.component_solid_count, 54)
            self.assertFalse(
                (output / "reports" / "protected_dummy_panicle_hashes.json").exists()
            )
            manifest = (
                output / "reports" / "export_manifest.csv"
            ).read_text(encoding="utf-8-sig")
            self.assertNotIn("dummy_panicle", manifest.casefold())
            self.assertNotIn("protected_dummy", manifest.casefold())


if __name__ == "__main__":
    unittest.main()
