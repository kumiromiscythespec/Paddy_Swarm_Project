#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import cadquery as cq


LANE = Path(__file__).resolve().parents[1]
REPO = Path(r"D:\Paddy_Swarm_Project")
BUILDER = LANE / "build_common_rover_service_servo_clutch_v0943.py"
SPEC = importlib.util.spec_from_file_location("v0943_builder", BUILDER)
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
        cls.motion = load("service_motions.json")
        cls.limits = load("test_limits.json")
        cls.ledger = load("measurement_ledger.json")
        cls.geom = load("geometry_manifest.json")
        cls.valid = load("validation_report.json")

    def test_001_exact_package(self):
        actual = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        self.assertEqual(B.PACKAGE_PATHS, actual)
        self.assertEqual(66, len(actual))

    def test_002_manifest(self):
        self.assertEqual(B.PACKAGE_PATHS, (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines())

    def test_003_frame_baseline(self):
        f = self.dim["frame"]
        self.assertEqual(150.0, f["structural_height_mm"])
        self.assertEqual([540.0, 181.0], f["upper_outer_mm"])
        self.assertEqual([442.0, 181.0], f["lower_outer_mm"])
        self.assertEqual("ALTERNATIVE_HOLD", f["frame_190"])

    def test_004_battery(self):
        self.assertEqual((150.9, 99.4, 92.5), tuple(self.dim["battery"][k] for k in ("x_mm", "y_mm", "z_mm")))
        self.assertEqual(1.2, self.dim["battery"]["mass_kg"])
        self.assertEqual(108.0, self.dim["battery"]["insertion_clear_height_mm"])

    def test_005_bbox_motion(self):
        bbox = self.dim["bbox"]
        self.assertEqual("BBOX_PITCH_AND_SLIDE_SERVICE_MOTION", bbox["service_motion"])
        self.assertFalse(bbox["straight_x_only"])
        self.assertEqual([0.0, 2.0, 4.0, 6.0], bbox["reference_pitch_deg"])
        self.assertEqual("PHYSICAL_TEST_REQUIRED", bbox["final_pitch"])

    def test_006_waterproof_lid_not_wear_surface(self):
        self.assertFalse(self.dim["bbox"]["waterproof_lid_as_wear_surface"])
        self.assertFalse(self.interfaces["bbox"]["lid_wear_contact"])
        self.assertIn("REPLACEABLE_WEAR_PAD", self.dim["bbox"]["top_guide"])

    def test_007_bottom_grip(self):
        self.assertEqual("RECESSED_BOTTOM_GRIP", self.dim["bbox"]["bottom_grip"])
        self.assertEqual([15.0, 20.0], self.dim["bbox"]["pull_lip_depth_class_mm"])
        self.assertEqual("REFERENCE_ONLY", self.dim["bbox"]["pull_lip_dimension_classification"])

    def test_008_service_test_grid(self):
        grid = self.motion["bbox"]["test_grid"]
        self.assertEqual({"103", "105", "107"}, set(grid))
        for tests in grid.values():
            self.assertIn("PITCH_AND_SLIDE", tests)
            self.assertIn("FRAME_SCRATCH", tests)
            self.assertIn("SERVICE_EFFORT", tests)

    def test_009_h25_known_dimensions(self):
        h = self.dim["h25a1"]
        self.assertEqual({"od_mm": 15.9, "id_mm": 10.1, "width_mm": 3.0, "classification": "MEASURED"}, h["collar"])
        self.assertEqual(2, h["set_screws"]["quantity"])
        self.assertEqual(90.0, h["set_screws"]["angle_deg"])
        self.assertEqual(4.0, h["set_screws"]["length_mm"])
        self.assertEqual(1.0, h["set_screws"]["projection_mm"])

    def test_010_captive_washer(self):
        h = self.dim["h25a1"]
        self.assertTrue(h["captive_washer_required"])
        self.assertTrue(all(v is None for v in h["unknowns"].values()))
        self.assertEqual("HOLD", h["full_hardware_dimensions"])

    def test_011_coupon_classification(self):
        h = self.dim["h25a1"]
        self.assertEqual([4.1, 4.2, 4.3], h["existing_shank_coupons_mm"])
        self.assertEqual("SCREW_SHANK_CLEARANCE_COUPONS", h["existing_shank_classification"])
        self.assertEqual([16.0, 16.1, 16.2], h["existing_collar_coupons_mm"])

    def test_012_no_final_v2_fixture_stl(self):
        stls = [p.lower() for p in B.CAD if p.endswith(".stl")]
        self.assertFalse(any("fixture" in p or "full_hardware" in p for p in stls))
        self.assertEqual("BLOCKED_MEASUREMENT_REQUIRED", self.dim["h25a1"]["v2_print"])
        self.assertFalse(self.geom["full_hardware"]["final_v2_fixture_stl_generated"])

    def test_013_protected_12t(self):
        sprocket = self.dim["protected_12t"]
        self.assertEqual(12, sprocket["teeth"])
        self.assertEqual(15.0, sprocket["phase_deg"])
        self.assertEqual(0.0, sprocket["external_geometry_delta_mm"])
        self.assertFalse(sprocket["radial_access_holes"])

    def test_014_servo_candidate(self):
        servo = self.dim["servo"]
        self.assertEqual(2, servo["count_candidate"])
        self.assertIsNone(servo["final_model"])
        self.assertEqual("SERVO_BRIDGE_2020", servo["bridge"])
        self.assertFalse(servo["petg_sole_reaction_mount"])

    def test_015_servo_measurements_hold(self):
        servo = self.hardware["servo"]
        self.assertTrue(all(value is None for value in servo.values()))

    def test_016_slide_axis_source_resolution(self):
        clutch = self.dim["clutch"]
        self.assertEqual("Y", clutch["slide_axis"])
        self.assertIn("V0941_PTO_AXIS_Y", clutch["axis_basis"])
        self.assertEqual("NOT_SELECTED_FOR_PARENT_CONSISTENCY", clutch["x_axis_comparison"])
        self.assertEqual("HOLD_PHYSICAL_MEASUREMENT", clutch["coordinate_and_stroke"])

    def test_017_three_positions(self):
        clutch = self.dim["clutch"]
        self.assertEqual(["DRIVE", "NEUTRAL", "PTO"], clutch["positions"])
        self.assertEqual("MECHANICALLY_PROHIBITED", clutch["simultaneous_drive_pto"])

    def test_018_guides_carriage_shoes(self):
        clutch = self.dim["clutch"]
        self.assertEqual(2, clutch["contact_lines"])
        self.assertEqual("METAL_PRIMARY_STRUCTURE", clutch["carriage"])
        self.assertEqual("REPLACEABLE_POLYMER", clutch["shoes"])

    def test_019_servo_does_not_hold_belt_load(self):
        clutch = self.dim["clutch"]
        self.assertFalse(clutch["servo_continuous_belt_load_holding"])
        self.assertEqual("MECHANICAL_STOP_TO_FRAME", clutch["operating_reaction"])
        self.assertFalse(self.interfaces["servo"]["continuous_belt_reaction"])

    def test_020_linkage_sensor(self):
        clutch = self.dim["clutch"]
        self.assertIn("ADJUSTABLE_ROD", clutch["linkage"])
        self.assertIn("HALL_PLUS_MAGNET", clutch["sensor_reservation"])
        self.assertEqual("HOLD_FORCE_STROKE_HORN", clutch["servo_torque"])

    def test_021_pto_compatibility(self):
        pto = self.dim["pto"]
        self.assertEqual((20, 20, 1.0), (pto["driver_teeth"], pto["driven_teeth"], pto["ratio"]))
        self.assertEqual("KP000_DOUBLE_SUPPORT", pto["support"])
        self.assertFalse(pto["powered"])

    def test_022_interference_reference(self):
        self.assertTrue(self.geom["interference"]["all_zero"])
        self.assertTrue(all(row["common_volume_mm3"] == 0.0 for row in self.geom["interference"]["rows"]))
        self.assertIn("HOLD", self.geom["interference"]["physical_transform_status"])

    def test_023_step_reload(self):
        steps = [p for p in B.CAD if p.endswith(".step")]
        self.assertEqual(16, len(steps))
        for rel in steps:
            shape = cq.importers.importStep(str(LANE / rel)).val()
            self.assertTrue(shape.isValid(), rel)
            self.assertGreater(shape.Volume(), 0, rel)

    def test_024_stl_semantics(self):
        stls = [p for p in B.CAD if p.endswith(".stl")]
        self.assertEqual(3, len(stls))
        for rel in stls:
            row = B.stl_semantic(LANE / rel)
            self.assertGreater(row["triangles"], 0)
            self.assertTrue(all(x > 0 for x in row["bounds_mm"]))

    def test_025_svg_documents(self):
        self.assertEqual(10, len(B.DRAWINGS))
        for rel in B.DRAWINGS:
            root = ET.parse(LANE / rel).getroot()
            self.assertTrue(root.tag.endswith("svg"))
            self.assertIn("NOT FOR MANUFACTURING", (LANE / rel).read_text(encoding="utf-8"))

    def test_026_parent_protection(self):
        audit = B.parent_audit()
        self.assertEqual("CAD_PASS", audit["status"])
        self.assertIn("24_PASS", audit["v0942_baseline_verify"])

    def test_027_authority_protection(self):
        self.assertEqual("CAD_PASS", B.authority_audit()["status"])

    def test_028_repository_guard(self):
        guard = B.repository_guard(True)
        self.assertEqual(B.EXPECTED_BRANCH, guard["branch"])
        self.assertEqual(B.EXPECTED_HEAD, guard["head"])
        self.assertEqual(0, len(guard["staged"]))
        self.assertEqual(B.BASE_OUTSIDE_UNTRACKED, guard["outside_untracked"])

    def test_029_commit_paths(self):
        expected = [f"{B.LANE_REL}/{p}" for p in B.PACKAGE_PATHS]
        self.assertEqual(expected, (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines())

    def test_030_sha256sums(self):
        rows = (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        actual = {}
        for row in rows:
            digest, rel = row.split("  ", 1)
            actual[rel] = digest
            self.assertEqual(digest, hashlib.sha256((LANE / rel).read_bytes()).hexdigest(), rel)
        self.assertEqual(set(B.PACKAGE_PATHS) - {"SHA256SUMS.txt"}, set(actual))

    def test_031_measurement_holds(self):
        holds = [row for row in self.ledger["rows"] if row["classification"].startswith("HOLD")]
        self.assertGreaterEqual(len(holds), 18)
        self.assertTrue(all(row["value"] is None for row in holds))

    def test_032_release_gates(self):
        self.assertEqual("HOLD", self.valid["release"])
        self.assertFalse(self.valid["manufacturing_inputs_complete"])
        self.assertFalse(self.valid["powered_rotation_approved"])
        self.assertFalse(self.valid["field_approved"])
        self.assertEqual(B.FINAL_STATUS, self.valid["final_status"])

    def test_033_source_trace(self):
        text = (LANE / "SOURCE_TRACE.md").read_text(encoding="utf-8")
        self.assertIn("v0.9.4.1 records PTO axis Y", text)
        self.assertIn("v0.9.3.0 Candidate A's X-axis", text)

    def test_034_no_git_mutation_in_source(self):
        source = BUILDER.read_text(encoding="utf-8")
        forbidden = ["git add", "git commit", "git push", "git checkout", "git switch", "git clean", "git reset"]
        self.assertFalse(any(token in source.lower() for token in forbidden))


if __name__ == "__main__":
    unittest.main(verbosity=2)
