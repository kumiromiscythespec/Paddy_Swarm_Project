from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from generate_dummy_kit import generate
from tests._artifact import generated_artifact


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DeterminismTests(unittest.TestCase):
    def test_full_stl_svg_csv_json_and_manual_replay(self):
        first = generated_artifact()
        with tempfile.TemporaryDirectory(
            prefix="pfd_v01_replay_"
        ) as temporary:
            second = Path(temporary) / "artifact"
            generate(second)
            first_files = sorted(
                path.relative_to(first).as_posix()
                for path in first.rglob("*")
                if path.is_file()
            )
            second_files = sorted(
                path.relative_to(second).as_posix()
                for path in second.rglob("*")
                if path.is_file()
            )
            self.assertEqual(first_files, second_files)
            mismatches = [
                name
                for name in first_files
                if _hash(first / name) != _hash(second / name)
            ]
            self.assertEqual(mismatches, [])
            report_path = os.environ.get("PFD_DETERMINISM_REPORT")
            if report_path:
                suffix_counts = {}
                for name in first_files:
                    suffix = Path(name).suffix.lower() or "<none>"
                    suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1
                report = {
                    "schema": "PS_PROGRESSIVE_DUMMY_DETERMINISTIC_REPLAY_V0_1",
                    "file_count": len(first_files),
                    "suffix_counts": dict(sorted(suffix_counts.items())),
                    "first_file_sha256": {
                        name: _hash(first / name) for name in first_files
                    },
                    "second_file_sha256": {
                        name: _hash(second / name) for name in second_files
                    },
                    "mismatches": mismatches,
                    "stl_replay": (
                        "PASS"
                        if all(
                            _hash(first / name) == _hash(second / name)
                            for name in first_files
                            if name.endswith(".stl")
                        )
                        else "FAIL"
                    ),
                    "svg_csv_json_manual_replay": (
                        "PASS"
                        if all(
                            _hash(first / name) == _hash(second / name)
                            for name in first_files
                            if not name.endswith(".stl")
                        )
                        else "FAIL"
                    ),
                    "DETERMINISTIC_REPLAY": (
                        "PASS" if not mismatches else "FAIL"
                    ),
                }
                destination = Path(report_path).resolve()
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(
                    json.dumps(report, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                    newline="\n",
                )


if __name__ == "__main__":
    unittest.main()
