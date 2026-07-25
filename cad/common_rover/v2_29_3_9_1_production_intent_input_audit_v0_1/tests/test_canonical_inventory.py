from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from canonical_inventory import (
    ALGORITHM_IDENTIFIER,
    canonical_inventory_sha256,
    canonical_posix_path,
    canonicalize_record,
    canonicalize_records,
    replay_inventory,
    validate_inventory_bundle,
    write_inventory_bundle,
)


FIXTURE_EXPECTED_SHA256 = (
    "2ea8794ed54d3b851728ad7931b900e69fb12f05d83e7c4b17a2e5c2b596582d"
)


def _record(path: str, file_hash: str, size: int) -> dict:
    return {
        "path": path,
        "extension": Path(path.replace("\\", "/")).suffix.lower(),
        "bytes": size,
        "git_blob_sha1": f"{size:040x}",
        "sha256": file_hash,
    }


def _fixture_records() -> list[dict]:
    return [
        _record("日本/部品.stp", "C" * 64, 3),
        _record("zeta/part.stl", "A" * 64, 1),
        _record("alpha/part.step", "b" * 64, 2),
    ]


def _fixture_inventory() -> dict:
    records = canonicalize_records(_fixture_records())
    return {
        "schema": "PS_BASELINE_TRACKED_CAD_INVENTORY_V0_2",
        "repository": "synthetic",
        "base_head": "synthetic",
        "source": "test fixture",
        "TRACKED_STL_COUNT": 1,
        "TRACKED_STEP_STP_COUNT": 2,
        "TRACKED_CAD_TOTAL_COUNT": 3,
        "inventory_hash_algorithm": ALGORITHM_IDENTIFIER,
        "canonical_path_rule": "test fixture",
        "canonical_record_format": "test fixture",
        "inventory_sha256": FIXTURE_EXPECTED_SHA256,
        "first_canonical_path": records[0]["path"],
        "last_canonical_path": records[-1]["path"],
        "records": records,
    }


class CanonicalInventoryTests(unittest.TestCase):
    def test_fixture_hash_is_exact_and_independent_of_input_order(self):
        self.assertEqual(
            canonical_inventory_sha256(_fixture_records()),
            FIXTURE_EXPECTED_SHA256,
        )

    def test_reverse_input_has_same_inventory_hash(self):
        records = _fixture_records()
        self.assertEqual(
            canonical_inventory_sha256(records),
            canonical_inventory_sha256(list(reversed(records))),
        )

    def test_random_shuffle_has_same_inventory_hash(self):
        records = _fixture_records()
        shuffled = list(records)
        random.Random(391).shuffle(shuffled)
        self.assertEqual(
            canonical_inventory_sha256(records),
            canonical_inventory_sha256(shuffled),
        )

    def test_non_utf8_bytewise_record_order_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            inventory = _fixture_inventory()
            write_inventory_bundle(inventory, output)
            payload = json.loads(
                (output / "baseline_tracked_cad_inventory.json").read_text(
                    encoding="utf-8"
                )
            )
            payload["records"] = list(reversed(payload["records"]))
            (output / "baseline_tracked_cad_inventory.json").write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            with self.assertRaisesRegex(
                ValueError,
                "JSON_RECORDS_NOT_CANONICAL_ORDER_OR_FORM",
            ):
                validate_inventory_bundle(
                    output / "baseline_tracked_cad_inventory.json",
                    output / "baseline_tracked_cad_inventory.csv",
                    output / "baseline_tracked_cad_inventory.sha256",
                )

    def test_duplicate_canonical_path_is_rejected(self):
        records = [
            _record("same/path.stl", "a" * 64, 1),
            _record(r"same\path.stl", "b" * 64, 2),
        ]
        with self.assertRaisesRegex(
            ValueError,
            "DUPLICATE_CANONICAL_PATH",
        ):
            canonicalize_records(records)

    def test_backslash_path_is_normalized_to_posix(self):
        self.assertEqual(
            canonical_posix_path(r"folder\part.stl"),
            "folder/part.stl",
        )

    def test_leading_dot_slash_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "CANONICAL_PATH_LEADING_DOT_SLASH_FORBIDDEN",
        ):
            canonical_posix_path("./folder/part.stl")

    def test_uppercase_sha_is_lowercase_in_canonical_output(self):
        record = canonicalize_record(
            _record("folder/part.stl", "ABCDEF" * 10 + "ABCD", 1)
        )
        self.assertEqual(record["sha256"], record["sha256"].lower())
        self.assertNotRegex(record["sha256"], r"[A-F]")

    def test_malformed_sha_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "MALFORMED_FILE_SHA256"):
            canonicalize_record(
                _record("folder/part.stl", "not-a-sha256", 1)
            )

    def test_json_csv_order_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            inventory = _fixture_inventory()
            write_inventory_bundle(inventory, output)
            csv_path = output / "baseline_tracked_cad_inventory.csv"
            with csv_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = reader.fieldnames
                rows = list(reader)
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=fieldnames,
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerows(reversed(rows))
            with self.assertRaisesRegex(
                ValueError,
                "JSON_CSV_RECORD_ORDER_OR_CONTENT_MISMATCH",
            ):
                validate_inventory_bundle(
                    output / "baseline_tracked_cad_inventory.json",
                    csv_path,
                    output / "baseline_tracked_cad_inventory.sha256",
                )

    def test_inventory_sha_receipt_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            inventory = _fixture_inventory()
            write_inventory_bundle(inventory, output)
            (output / "baseline_tracked_cad_inventory.sha256").write_text(
                f'{"0" * 64}  baseline_tracked_cad_inventory.canonical\n',
                encoding="ascii",
                newline="\n",
            )
            with self.assertRaisesRegex(
                ValueError,
                "INVENTORY_SHA256_RECEIPT_MISMATCH",
            ):
                validate_inventory_bundle(
                    output / "baseline_tracked_cad_inventory.json",
                    output / "baseline_tracked_cad_inventory.csv",
                    output / "baseline_tracked_cad_inventory.sha256",
                )

    def test_independent_replay_script_matches_all_orders(self):
        module_dir = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_inventory_bundle(_fixture_inventory(), output)
            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(module_dir / "replay_canonical_inventory.py"),
                    "--artifact-dir",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
            )
            report = json.loads(completed.stdout)
            self.assertTrue(report["match"])
            self.assertTrue(report["shuffled_replay_match"])
            self.assertTrue(report["reversed_replay_match"])
            direct = replay_inventory(
                _fixture_records(),
                recorded_sha256=FIXTURE_EXPECTED_SHA256,
            )
            self.assertEqual(
                report["calculated_sha256"],
                direct["calculated_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
