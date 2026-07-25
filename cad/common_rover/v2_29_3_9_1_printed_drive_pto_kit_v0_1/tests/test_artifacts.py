from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from validate_drive_pto_kit import (
    reject_bytecode_paths,
    reject_duplicate_stls,
    reject_untracked_cad_outside_lane,
)


def _artifact_directory() -> Path:
    raw = os.environ.get("PS_DRIVE_PTO_ARTIFACT_DIR")
    if not raw:
        raise RuntimeError("PS_DRIVE_PTO_ARTIFACT_DIR_REQUIRED")
    return Path(raw).resolve()


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = _artifact_directory()
        cls.report = json.loads(
            (cls.artifact / "geometry_validation.json").read_text(
                encoding="utf-8"
            )
        )
        cls.parts = cls.report["parts"]

    def test_geometry_validation_passes(self) -> None:
        self.assertEqual(self.report["status"], "PASS")

    def test_all_stls_watertight(self) -> None:
        self.assertTrue(
            all(part["mesh"]["watertight"] for part in self.parts)
        )

    def test_no_degenerate_faces(self) -> None:
        self.assertTrue(
            all(part["mesh"]["degenerate_face_count"] == 0 for part in self.parts)
        )

    def test_every_stl_single_component(self) -> None:
        self.assertTrue(
            all(
                part["mesh"]["connected_component_count"] == 1
                and part["solid_count"] == 1
                for part in self.parts
            )
        )

    def test_part_number_geometry_connected(self) -> None:
        self.assertTrue(
            all(
                part["shape_checks"]["marking_connected"]
                and part["shape_checks"]["part_number_matches"]
                for part in self.parts
            )
        )

    def test_20t_and_60t_single_component(self) -> None:
        pulleys = [part for part in self.parts if part["family"] == "pulley"]
        self.assertEqual(sum(p["metadata"]["teeth"] == 20 for p in pulleys), 4)
        self.assertEqual(sum(p["metadata"]["teeth"] == 60 for p in pulleys), 4)
        self.assertTrue(all(p["solid_count"] == 1 for p in pulleys))

    def test_continuous_belts_closed_and_90_teeth(self) -> None:
        belts = [
            part
            for part in self.parts
            if part["metadata"].get("form") == "CONTINUOUS_CLOSED_LOOP"
        ]
        self.assertEqual(len(belts), 3)
        self.assertTrue(
            all(
                belt["metadata"]["closed_loop"]
                and belt["metadata"]["tooth_count"] == 90
                and belt["metadata"]["belt_width_mm"] == 15.0
                for belt in belts
            )
        )

    def test_flange_clearance(self) -> None:
        pulleys = [part for part in self.parts if part["family"] == "pulley"]
        self.assertTrue(
            all(
                part["metadata"]["flange_radius_mm"]
                > part["metadata"]["pitch_diameter_mm"] / 2.0
                for part in pulleys
            )
        )

    def test_hub_pcd(self) -> None:
        selected = [
            part
            for part in self.parts
            if part["family"] == "pulley"
            and part["metadata"]["pcd24_4xm4"]
        ]
        self.assertTrue(selected)
        self.assertTrue(
            all(part["metadata"]["hub_pcd_mm"] == 24.0 for part in selected)
        )

    def test_guard_clearance(self) -> None:
        guards = [
            part
            for part in self.parts
            if part["metadata"].get("part_type") == "TEMPORARY_BELT_GUARD"
        ]
        self.assertEqual(len(guards), 4)
        self.assertTrue(
            all(
                guard["metadata"]["minimum_guard_clearance_mm"] >= 8.0
                for guard in guards
            )
        )

    def test_bambu_a1_build_plate_fit(self) -> None:
        self.assertEqual(self.report["build_plate"]["status"], "PASS")
        self.assertTrue(
            all(part["shape_checks"]["build_plate_fit"] for part in self.parts)
        )

    def test_duplicate_stl_rejection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ps_duplicate_stl_") as raw:
            directory = Path(raw)
            first = directory / "first.stl"
            second = directory / "second.stl"
            first.write_bytes(b"same")
            second.write_bytes(b"same")
            with self.assertRaisesRegex(ValueError, "DUPLICATE_STL_REJECTED"):
                reject_duplicate_stls((first, second))

    def test_untracked_cad_outside_lane_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "OUTSIDE_NEW_LANE"):
            reject_untracked_cad_outside_lane(("cad/unrelated/new_part.py",))

    def test_target_worktree_bytecode_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "BYTECODE_REJECTED"):
            reject_bytecode_paths(("cad/new_lane/__pycache__/bad.pyc",))

    def test_repository_cad_baseline_unchanged(self) -> None:
        repository = self.report["repository"]
        self.assertEqual(repository["tracked_baseline_changes"], [])
        self.assertEqual(repository["staged_changes"], [])
        self.assertEqual(repository["status"], "PASS")

    def test_pto_final_belts_not_generated(self) -> None:
        manifest = (self.artifact / "belt_manifest.csv").read_text(
            encoding="utf-8"
        )
        self.assertIn("PS-BLT-PA-XXX-R00", manifest)
        self.assertIn("PS-BLT-PB-XXX-R00", manifest)
        self.assertGreaterEqual(manifest.count("NOT_GENERATED"), 2)

    def test_joiner_never_powered(self) -> None:
        joiner = next(
            part
            for part in self.parts
            if part["part_number"] == "PS-BLT-JOIN-R00"
        )
        self.assertEqual(joiner["metadata"]["powered_status"], "NEVER_POWERED")

    def test_measurements_are_pending_not_zero_filled(self) -> None:
        sheet = (
            self.artifact / "first_article_measurement_sheet.csv"
        ).read_text(encoding="utf-8")
        self.assertIn("CALIBRATION_PENDING", sheet)
        for line in sheet.splitlines()[1:]:
            measured = line.split(",")[4]
            self.assertEqual(measured, "CALIBRATION_PENDING")

    def test_required_external_artifacts_exist(self) -> None:
        required = {
            "drive_pto_contract.json",
            "part_number_registry.csv",
            "pulley_manifest.csv",
            "belt_manifest.csv",
            "coupon_manifest.csv",
            "additional_missing_parts_audit.csv",
            "print_target_manifest.csv",
            "print_order.md",
            "assembly_order.md",
            "first_article_measurement_sheet.csv",
            "powered_test_gate.md",
            "unresolved_inputs.md",
            "geometry_validation.json",
            "source.patch",
        }
        missing = sorted(
            name for name in required if not (self.artifact / name).is_file()
        )
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
