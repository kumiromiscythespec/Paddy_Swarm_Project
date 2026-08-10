#!/usr/bin/env python3
"""Contract tests for Common Rover DRIVE HTD5M TPU trial belt v0.9.5.1."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_common_rover_drive_htd5m_tpu_trial_belt_v0951.py"
spec = importlib.util.spec_from_file_location("v0951_builder", BUILDER)
assert spec and spec.loader
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dim = json.loads((LANE / "dimensions.json").read_text(encoding="utf-8"))
        cls.belt = json.loads((LANE / "belt_geometry.json").read_text(encoding="utf-8"))
        cls.pulley = json.loads((LANE / "pulley_geometry.json").read_text(encoding="utf-8"))
        cls.measurements = json.loads((LANE / "measurement_ledger.json").read_text(encoding="utf-8"))
        cls.geometry = json.loads((LANE / "geometry_manifest.json").read_text(encoding="utf-8"))
        cls.validation = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))

    def test_001_repository_guard(self):
        self.assertEqual(b.repository_guard(True)["status"], "PASS")

    def test_002_authority_unchanged(self):
        self.assertEqual(b.authority_audit()["hashes"], b.AUTHORITY_HASHES)

    def test_003_parent_v0950_unchanged(self):
        self.assertEqual(b.tree_digest(b.PARENT_V0950), b.PARENT_V0950_TREE)

    def test_004_source_hashes(self):
        self.assertEqual(b.source_audit()["status"], "PASS")
        for name, digest in b.SOURCE_HASHES.items():
            self.assertEqual(b.sha(b.SNAPSHOT_DIR / name), digest)

    def test_005_profile_pitch(self):
        self.assertEqual(self.dim["profile"], "HTD5M")
        self.assertEqual(self.dim["profile_variant"], "STANDARD")
        self.assertEqual(self.dim["pitch_mm"], 5.0)

    def test_006_pulley_teeth(self):
        self.assertEqual((self.dim["small_pulley_teeth"], self.dim["large_pulley_teeth"]), (20, 60))

    def test_007_measured_center(self):
        self.assertEqual(self.dim["center_distance_measured_mm"], 180.0)
        self.assertEqual(self.dim["center_distance_classification"], "MEASURED / USER_REPORTED")

    def test_008_string_discrepancy_preserved(self):
        self.assertEqual(self.dim["string_loop_user_reported_mm"], 583.0)
        self.assertEqual(self.dim["string_measurement_conflict"], "PHYSICAL_BELT_TEST_REQUIRED")
        self.assertEqual(583.0 - 565.0, 18.0)

    def test_009_primary_exact(self):
        self.assertEqual(self.dim["primary_belt_teeth"], 113)
        self.assertEqual(self.dim["primary_belt_pitch_length_mm"], 565.0)

    def test_010_secondary_exact(self):
        self.assertEqual((self.dim["secondary_long_teeth"], self.dim["secondary_long_length_mm"]), (114, 570.0))
        self.assertEqual((self.dim["secondary_short_teeth"], self.dim["secondary_short_length_mm"]), (112, 560.0))

    def test_011_theoretical_path(self):
        self.assertTrue(math.isclose(self.dim["calculations"]["theoretical_pitch_length_at_c180_mm"], 565.643763262217, abs_tol=1e-9))

    def test_012_derived_center(self):
        self.assertTrue(math.isclose(self.dim["calculations"]["derived_center_distance_mm"]["113"], 179.67295461860886, abs_tol=1e-9))

    def test_013_belt_width_source_authority(self):
        self.assertEqual(self.dim["belt_width_mm"], 15.0)
        self.assertEqual(self.dim["tooth_face_width_mm"], 16.0)
        self.assertEqual(self.pulley["nominal_belt_width_mm"], 15.0)
        self.assertEqual(self.dim["backing_mm"], 2.2)
        self.assertEqual(self.dim["backing_authority"], "REUSED_BELT_FAMILY_SOURCE")
        self.assertFalse(self.dim["fallback_backing_comparisons_used"])

    def test_014_profile_reuse_direct(self):
        reuse = self.geometry["profile_reuse"]
        self.assertEqual(reuse["sha256"], b.SOURCE_HASHES["htd5m_profile.py"])
        self.assertEqual(reuse["direct_function_reuse"], ["belt_tooth_solids", "belt_family._straight_tooth"])
        self.assertEqual(reuse["source_backing_thickness_mm"], 2.2)
        self.assertFalse(reuse["constants_copied_into_builder"])

    def test_015_coupon_contract(self):
        coupon = self.belt["coupon"]
        self.assertEqual((coupon["teeth"], coupon["pitch_length_mm"]), (12, 60.0))
        self.assertTrue(coupon["open_strip"])
        self.assertEqual(coupon["solid_count"], 1)

    def test_016_tooth_closure(self):
        for teeth, length in ((112, 560.0), (113, 565.0), (114, 570.0)):
            row = self.belt["variants"][str(teeth)]
            self.assertEqual(row["teeth"], teeth)
            self.assertEqual(row["pitch_length_mm"], length)
            self.assertEqual(row["closure_phase_error_deg"], 0.0)

    def test_017_single_solids(self):
        self.assertTrue(all(row["solid_count"] == 1 for row in self.belt["variants"].values()))

    def test_018_bambu_a1_fit(self):
        self.assertTrue(all(row["bambu_a1_fit"] for row in self.belt["variants"].values()))
        self.assertLessEqual(self.belt["variants"]["114"]["max_xy_mm"], 256.0)

    def test_019_witness_and_datum(self):
        row = self.belt["variants"]["113"]
        self.assertEqual(row["witness_interval_nominal_mm"], 50.0)
        self.assertEqual(row["datum_tooth"], 1)
        self.assertEqual(row["label"], "113-565")

    def test_020_no_tensile_cord(self):
        self.assertEqual(self.dim["tensile_cord"], "NONE")
        self.assertEqual(self.belt["tensile_cord"], "NONE")

    def test_021_nominal_scale(self):
        self.assertEqual(self.belt["nominal_scale"], 1.0)
        self.assertFalse(self.belt["xy_compensation_applied"])

    def test_022_pulley_reference_hashes(self):
        for rel, (_source, digest) in b.PULLEY_STEP_SOURCES.items():
            self.assertEqual(b.sha(LANE / rel), digest)

    def test_023_mating_phase(self):
        for row in self.geometry["contact_analysis"].values():
            self.assertTrue(row["half_pitch_is_lower_overlap"])
            self.assertGreater(row["tooth_common_volume_half_pitch_mm3"], 0.0)
            self.assertEqual(row["classification"], "EXPECTED_MATING_CONTACT / HOLD_PHYSICAL_COUPON")

    def test_024_no_flange_collision(self):
        for row in self.geometry["contact_analysis"].values():
            self.assertFalse(row["flange_collision"])
            self.assertEqual(row["flange_axial_clearance_each_side_mm"], 0.5)

    def test_025_open_belt_path(self):
        assembly = self.geometry["assembly"]
        self.assertEqual(assembly["center_distance_mm"], 180.0)
        self.assertEqual(assembly["installed_tooth_count"], 113)
        self.assertTrue(math.isclose(assembly["installed_tooth_pitch_mm"], 5.005697020019619, abs_tol=1e-12))
        self.assertFalse(assembly["crossed_belt"])
        self.assertFalse(assembly["belt_path_self_intersection"])

    def test_026_stl_watertight(self):
        for rel in b.CAD:
            if rel.endswith(".stl"):
                row = b.stl_semantic(LANE / rel)
                self.assertTrue(row["watertight"], rel)
                self.assertGreater(row["triangles"], 0)

    def test_027_step_reload(self):
        for rel in b.CAD:
            if rel.endswith(".step"):
                shape = b.cq.importers.importStep(str(LANE / rel)).val()
                self.assertTrue(shape.isValid(), rel)
                self.assertGreater(shape.Volume(), 0.0, rel)

    def test_028_documents_and_svg(self):
        self.assertEqual(len(b.DOCS), 16)
        self.assertEqual(len(b.DRAWINGS), 7)
        for rel in b.DOCS + b.DRAWINGS:
            self.assertTrue((LANE / rel).is_file(), rel)

    def test_029_machine_readable(self):
        self.assertEqual(len(b.JSONS), 7)
        self.assertTrue(all((LANE / rel).is_file() for rel in b.JSONS))

    def test_030_release_prohibitions(self):
        self.assertFalse(self.dim["powered_rotation"])
        self.assertFalse(self.dim["motor_test"])
        self.assertFalse(self.dim["load_test"])
        self.assertFalse(self.dim["field"])
        self.assertEqual(self.validation["commercial_belt"], "HOLD")

    def test_031_manifest_commit_paths_hashes(self):
        self.assertEqual(b.verify_files()["status"], "PASS")

    def test_032_runtime_not_authority(self):
        for rel in b.AUTHORITY_HASHES:
            data = (b.REPO_ROOT / rel).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), b.AUTHORITY_HASHES[rel])


if __name__ == "__main__":
    unittest.main(verbosity=2)
