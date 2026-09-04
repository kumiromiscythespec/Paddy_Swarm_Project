#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import cadquery as cq


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_common_rover_h25a1_fixture_v0944.py"
SPEC = importlib.util.spec_from_file_location("v0944_builder", BUILDER)
assert SPEC and SPEC.loader
B = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(B)


def load(name: str):
    return json.loads((LANE / name).read_text(encoding="utf-8"))


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dim = load("dimensions.json")
        cls.interfaces = load("interfaces.json")
        cls.hardware = load("hardware.json")
        cls.limits = load("test_limits.json")
        cls.ledger = load("measurement_ledger.json")
        cls.geom = load("geometry_manifest.json")
        cls.valid = load("validation_report.json")

    def test_001_exact_package(self):
        actual = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        self.assertEqual(B.PACKAGE_PATHS, actual)
        self.assertEqual(59, len(actual))

    def test_002_manifest(self):
        self.assertEqual(B.PACKAGE_PATHS, (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines())

    def test_003_collar(self):
        self.assertEqual(15.9, self.dim["collar_od_mm"])
        self.assertEqual(10.1, self.dim["collar_id_mm"])
        self.assertEqual(3.0, self.dim["collar_width_mm"])

    def test_004_set_screws(self):
        self.assertEqual(2, self.dim["set_screw_qty"])
        self.assertEqual(90.0, self.dim["set_screw_angle_deg"])
        self.assertEqual("M4", self.dim["set_screw_nominal"])
        self.assertEqual(3.8, self.dim["set_screw_major_od_measured_mm"])
        self.assertEqual(4.0, self.dim["set_screw_length_mm"])
        self.assertEqual(1.0, self.dim["set_screw_projection_mm"])

    def test_005_washer(self):
        self.assertEqual(8.8, self.dim["washer_max_od_mm"])
        self.assertEqual(1.8, self.dim["washer_stack_mm"])

    def test_006_head(self):
        self.assertEqual(6.8, self.dim["screw_head_max_od_mm"])
        self.assertEqual(2.8, self.dim["screw_head_height_mm"])

    def test_007_full_envelopes(self):
        self.assertEqual(20.0, self.dim["full_radial_envelope_mm"])
        self.assertEqual(8.8, self.dim["full_axial_width_mm"])

    def test_008_radial_margin(self):
        self.assertEqual(29.47, self.dim["protected_12t"]["root_radius_mm"])
        self.assertAlmostEqual(9.47, self.dim["protected_12t"]["root_radius_mm"] - self.dim["full_radial_envelope_mm"], places=9)
        self.assertEqual(9.47, self.dim["derived"]["hardware_to_root_theoretical_margin_mm"])

    def test_009_axial_margin(self):
        self.assertEqual(44.0, self.dim["protected_12t"]["axial_width_mm"])
        self.assertAlmostEqual(17.6, (44.0 - 8.8) / 2, places=9)
        self.assertEqual(17.6, self.dim["derived"]["centered_axial_margin_each_side_mm"])

    def test_010_washer_candidates(self):
        self.assertEqual([9.0, 9.2, 9.4], self.dim["derived"]["washer_relief_candidates_mm"])

    def test_011_radial_candidates(self):
        self.assertEqual([20.2, 20.4, 20.6], self.dim["derived"]["service_radial_candidates_mm"])

    def test_012_axial_candidates(self):
        self.assertEqual([9.0, 9.2, 9.4], self.dim["derived"]["service_axial_candidates_mm"])

    def test_013_reaction_candidates(self):
        self.assertEqual([4.1, 4.2, 4.3], self.dim["derived"]["reaction_shank_candidates_mm"])
        self.assertEqual(4.2, self.dim["derived"]["neutral_fixture"]["reaction_mm"])
        self.assertFalse(self.dim["derived"]["neutral_fixture"]["final"])

    def test_014_shaft_candidates(self):
        self.assertEqual([10.2, 10.3, 10.4], self.dim["derived"]["shaft_clearance_candidates_mm"])
        self.assertEqual(10.3, self.interfaces["fixture"]["neutral_mm"])
        self.assertFalse(self.interfaces["fixture"]["bearing_fit"])

    def test_015_minimum_wall(self):
        self.assertEqual(5.37, self.dim["derived"]["minimum_remaining_petg_wall_mm"])
        rows = self.geom["interference"]["wall_by_candidate"]
        self.assertEqual([5.77, 5.57, 5.37], [r["remaining_petg_wall_mm"] for r in rows])
        self.assertTrue(all(r["target_ge_3"] for r in rows))

    def test_016_link_width_blocker(self):
        self.assertEqual(53.6, self.dim["derived"]["link_width_reference_mm"])
        self.assertEqual(4.8, self.dim["derived"]["centered_link_side_protrusion_mm"])
        self.assertIn("BLOCKED", self.dim["derived"]["link_side_status"])

    def test_017_protected_geometry(self):
        p = self.dim["protected_12t"]
        self.assertEqual((12, 15.0, 30.0), (p["teeth"], p["phase_deg"], p["spacing_deg"]))
        self.assertEqual((33.07, 29.47), (p["tip_radius_mm"], p["root_radius_mm"]))
        self.assertEqual((7.5, 9.5), (p["tip_width_mm"], p["root_width_mm"]))
        self.assertEqual(76.3943726841, p["pitch_diameter_mm"])
        self.assertEqual(4.0, p["buried_root_overlap_mm"])

    def test_018_no_protected_change(self):
        p = self.dim["protected_12t"]
        self.assertEqual(0.0, p["external_geometry_delta_mm"])
        self.assertEqual(0, p["radial_tooth_root_access_holes"])
        self.assertFalse(self.geom["full_12t_sprocket_stl_generated"])

    def test_019_failure_inheritance(self):
        failures = self.hardware["failure_history"]
        self.assertIn("PHYSICAL_FAIL_SLIP", failures["H0"])
        self.assertIn("6P001", failures["H2.3"])
        self.assertIn("0P499080075", failures["H2.4"])

    def test_020_full_hardware_required(self):
        required = self.hardware["full_assembly_required"]
        self.assertEqual(7, len(required))
        self.assertIn("CAPTIVE_WASHER_X", required)
        self.assertIn("HEAD_Y", required)

    def test_021_washer_not_torque_path(self):
        self.assertFalse(self.interfaces["washer_primary_torque_path"])
        self.assertFalse(self.interfaces["cover_bolts_primary_torque_path"])

    def test_022_reaction_key_replaceable_and_spared(self):
        key = self.hardware["reaction_key"]
        self.assertTrue(key["replaceable"])
        self.assertEqual(1.0, key["spare_ratio"])
        self.assertFalse(key["neutral_final"])
        self.assertEqual(9.2, key["washer_relief_mm"])
        self.assertEqual(6.9, key["head_reaction_land_relief_mm"])
        self.assertEqual(17.8, key["body_width_mm"])

    def test_023_interference(self):
        report = self.geom["interference"]
        self.assertTrue(report["all_zero"])
        self.assertTrue(all(row["common_volume_mm3"] == 0.0 for row in report["rows"]))
        names = {row["check"] for row in report["rows"]}
        self.assertIn("FULL_HARDWARE_VS_INSTALLED_REACTION_KEYS", names)
        self.assertIn("INSTALLED_REACTION_KEYS_MUTUAL", names)
        self.assertIn("INSTALLED_REACTION_KEYS_VS_FIXTURE_BODY", names)
        self.assertEqual("USER_TEST_PENDING", report["physical_fit_status"])

    def test_024_printability(self):
        p = self.geom["printability"]
        self.assertEqual([256, 256], p["bed_mm"])
        self.assertTrue(p["all_fit"])
        self.assertTrue(all(row["fits_bambu_a1_xy"] for row in p["rows"].values()))
        self.assertEqual("USER_CONFIRM_REQUIRED", p["slicer_support_generation"])

    def test_025_step_reload(self):
        steps = [p for p in B.CAD if p.endswith(".step")]
        self.assertEqual(12, len(steps))
        for rel in steps:
            shape = cq.importers.importStep(str(LANE / rel)).val()
            self.assertTrue(shape.isValid(), rel)
            self.assertGreater(shape.Volume(), 0, rel)

    def test_026_stl_semantics(self):
        stls = [p for p in B.CAD if p.endswith(".stl")]
        self.assertEqual(8, len(stls))
        for rel in stls:
            row = B.stl_semantic(LANE / rel)
            self.assertGreater(row["triangles"], 0, rel)
            self.assertTrue(all(x > 0 for x in row["bounds_mm"]), rel)

    def test_027_svgs(self):
        self.assertEqual(9, len(B.DRAWINGS))
        for rel in B.DRAWINGS:
            root = ET.parse(LANE / rel).getroot()
            self.assertTrue(root.tag.endswith("svg"))
            self.assertIn("NO POWERED ROTATION", (LANE / rel).read_text(encoding="utf-8"))

    def test_028_torque_plan(self):
        self.assertEqual([0.25, 0.5, 0.75], self.limits["static_torque_nm"])
        self.assertTrue(self.limits["stop_on_first_failure"])
        self.assertIn("CANNOT_REMOVE_HARDWARE", self.limits["failure"])

    def test_029_creep(self):
        self.assertEqual(24, self.limits["creep_hours"])
        self.assertEqual("PHYSICAL_PENDING", self.valid["gates"]["24H_CREEP"])

    def test_030_physical_gates(self):
        gates = self.valid["gates"]
        self.assertEqual("COMPLETE", gates["FULL_HARDWARE_MEASUREMENTS"])
        self.assertEqual("PRINT_READY_CANDIDATE", gates["V2_FIT_COUPON"])
        self.assertEqual("PRINT_READY_CANDIDATE", gates["V2_STATIC_FIXTURE"])
        self.assertTrue(all(gates[f"STATIC_TORQUE_{x}"] == "PHYSICAL_PENDING" for x in ("025", "050", "075")))

    def test_031_release_gates(self):
        self.assertEqual("HOLD", self.valid["full_sprocket_manufacturing"])
        self.assertFalse(self.valid["physical_tests_complete"])
        self.assertFalse(self.valid["powered_rotation_approved"])
        self.assertFalse(self.valid["field_approved"])
        self.assertEqual(B.FINAL_STATUS, self.valid["final_status"])

    def test_032_nonblocking_missing(self):
        self.assertTrue(self.valid["fixture_inputs_complete"])
        missing = self.valid["missing_nonblocking_measurements"]
        self.assertIn("M4_THREAD_PITCH", missing)
        self.assertIn("EXACT_3D_WASHER_STACK_ASYMMETRY", missing)
        self.assertEqual(5, len(missing))

    def test_033_parent_protection(self):
        audit = B.parent_audit()
        self.assertEqual("CAD_PASS", audit["status"])
        self.assertEqual(66, audit["v0943"]["file_count"])
        self.assertEqual(57, audit["v0942"]["file_count"])

    def test_034_authority_protection(self):
        self.assertEqual("CAD_PASS", B.authority_audit()["status"])

    def test_035_repository_guard(self):
        guard = B.repository_guard(True)
        self.assertEqual(B.EXPECTED_BRANCH, guard["branch"])
        self.assertEqual(B.EXPECTED_HEAD, guard["head"])
        self.assertEqual(0, len(guard["staged"]))
        self.assertEqual(B.BASE_OUTSIDE_UNTRACKED, guard["outside_untracked"])

    def test_036_commit_paths(self):
        expected = [f"{B.LANE_REL}/{p}" for p in B.PACKAGE_PATHS]
        self.assertEqual(expected, (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines())

    def test_037_sha256sums(self):
        rows = (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        actual = {}
        for row in rows:
            digest, rel = row.split("  ", 1)
            actual[rel] = digest
            self.assertEqual(digest, hashlib.sha256((LANE / rel).read_bytes()).hexdigest(), rel)
        self.assertEqual(set(B.PACKAGE_PATHS) - {"SHA256SUMS.txt"}, set(actual))

    def test_038_result_form(self):
        text = (LANE / "PHYSICAL_RESULT_FORM.md").read_text(encoding="utf-8")
        for token in ("16.0", "16.1", "16.2", "4.1", "4.2", "4.3", "9.0", "9.2", "9.4", "0.25 N·m", "24 h"):
            self.assertIn(token, text)

    def test_039_no_git_mutation_source(self):
        source = BUILDER.read_text(encoding="utf-8").lower()
        self.assertFalse(any(token in source for token in ("git add", "git commit", "git push", "git checkout", "git switch", "git clean", "git reset")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
