from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from audit_contract import (
    LANE_RELATIVE,
    merge_profile_supplier_inputs,
    validate_production_part_number,
)
from repository_guard import (
    compare_baseline_to_files,
    ensure_external_output,
    scan_repository_bytecode,
    scan_source_lane,
    scan_untracked_cad,
)


def _record(path: str, content: bytes) -> dict:
    return {
        "path": path,
        "extension": Path(path).suffix.lower(),
        "bytes": len(content),
        "git_blob_sha1": "synthetic-test-record",
        "sha256": hashlib.sha256(content).hexdigest(),
    }


class CorrectedBaselineNegativeTests(unittest.TestCase):
    def test_existing_tracked_stl_alone_is_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            content = b"sealed-stl"
            relative = "legacy/allowed.stl"
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(content)
            report = compare_baseline_to_files(
                root,
                [_record(relative, content)],
                {relative},
            )
            self.assertEqual(
                report["BASELINE_TRACKED_CAD_INVENTORY_MATCH"],
                "PASS",
            )

    def test_existing_tracked_step_and_stp_alone_are_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pairs = {
                "legacy/allowed.step": b"sealed-step",
                "legacy/allowed.stp": b"sealed-stp",
            }
            for relative, content in pairs.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            report = compare_baseline_to_files(
                root,
                [_record(path, content) for path, content in pairs.items()],
                set(pairs),
            )
            self.assertEqual(
                report["BASELINE_TRACKED_CAD_INVENTORY_MATCH"],
                "PASS",
            )

    def test_modified_baseline_stl_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "legacy/part.stl"
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(b"modified")
            report = compare_baseline_to_files(
                root,
                [_record(relative, b"baseline")],
                {relative},
            )
            self.assertEqual(report["MODIFIED_TRACKED_CAD_OUTPUT_COUNT"], 1)
            self.assertEqual(
                report["BASELINE_TRACKED_CAD_INVENTORY_MATCH"],
                "FAIL",
            )

    def test_deleted_baseline_step_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = "legacy/deleted.step"
            report = compare_baseline_to_files(
                root,
                [_record(relative, b"baseline")],
                set(),
            )
            self.assertEqual(report["DELETED_TRACKED_CAD_OUTPUT_COUNT"], 1)
            self.assertEqual(
                report["BASELINE_TRACKED_CAD_INVENTORY_MATCH"],
                "FAIL",
            )

    def test_new_tracked_stl_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = compare_baseline_to_files(
                root,
                [],
                {"new/production.stl"},
            )
            self.assertEqual(report["ADDED_TRACKED_CAD_OUTPUT_COUNT"], 1)
            self.assertEqual(
                report["BASELINE_TRACKED_CAD_INVENTORY_MATCH"],
                "FAIL",
            )

    def test_untracked_stl_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "untracked.stl"
            path.write_bytes(b"mesh")
            report = scan_untracked_cad(root, set())
            self.assertEqual(report["UNTRACKED_CAD_OUTPUT_COUNT"], 1)
            self.assertEqual(report["status"], "FAIL")

    def test_gitignored_untracked_step_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".gitignore").write_text("*.step\n", encoding="utf-8")
            (root / "hidden.step").write_bytes(b"hidden-by-ignore")
            report = scan_untracked_cad(root, set())
            self.assertEqual(report["UNTRACKED_CAD_OUTPUT_COUNT"], 1)
            self.assertEqual(
                report["untracked_cad_outputs"][0]["path"],
                "hidden.step",
            )

    def test_generated_artifact_in_source_lane_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lane = root / LANE_RELATIVE
            lane.mkdir(parents=True)
            (lane / "production_input_audit.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            report = scan_source_lane(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(
                any(
                    item.startswith("GENERATED_ARTIFACT_IN_SOURCE_LANE:")
                    for item in report["findings"]
                )
            )

    def test_untracked_pyc_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / "__pycache__"
            cache.mkdir()
            (cache / "audit.cpython-313.pyc").write_bytes(b"bytecode")
            report = scan_repository_bytecode(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertFalse(report["untracked_bytecode_allowed"])

    def test_dummy_part_number_auto_reuse_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "DUMMY_PART_NUMBER_PRODUCTION_REUSE_FORBIDDEN",
        ):
            validate_production_part_number(
                "PS-PR-A0-MNT-001-R00",
                dummy_part_numbers={"PS-PR-A0-MNT-001-R00"},
            )

    def test_generic_profile_value_fill_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "GENERIC_PROFILE_VALUE_INFERENCE_FORBIDDEN",
        ):
            merge_profile_supplier_inputs(
                {},
                generic_defaults={"slot_opening_width": 6.0},
            )

    def test_production_stl_generation_during_audit_is_rejected(self):
        with tempfile.TemporaryDirectory() as repository:
            root = Path(repository)
            outside = root.parent / "forbidden_production_part.stl"
            with self.assertRaisesRegex(
                ValueError,
                "PRODUCTION_CAD_OUTPUT_FORBIDDEN_DURING_AUDIT",
            ):
                ensure_external_output(
                    outside,
                    root,
                    allowed_names={outside.name},
                )


if __name__ == "__main__":
    unittest.main()
