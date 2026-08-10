#!/usr/bin/env python3
"""Contract tests for Common Rover BBOX/CBOX v0.9.5.0."""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

import cadquery as cq

LANE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bbox_cbox_v0950", LANE / "build_common_rover_bbox_cbox_prototype_v0950.py")
B = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(B)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dim = json.loads((LANE / "dimensions.json").read_text(encoding="utf-8"))
        cls.interfaces = json.loads((LANE / "interfaces.json").read_text(encoding="utf-8"))
        cls.hardware = json.loads((LANE / "hardware.json").read_text(encoding="utf-8"))
        cls.motion = json.loads((LANE / "service_motions.json").read_text(encoding="utf-8"))
        cls.geom = json.loads((LANE / "geometry_manifest.json").read_text(encoding="utf-8"))
        cls.valid = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))

    def test_001_exact_package(self):
        files = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        self.assertEqual(B.PACKAGE_PATHS, files)

    def test_002_manifest(self):
        self.assertEqual(B.PACKAGE_PATHS, (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines())

    def test_003_frame_outer(self):
        f = self.dim["frame"]
        self.assertEqual([540.0, 181.0], f["upper_outer_mm"])
        self.assertEqual([442.0, 181.0], f["lower_outer_mm"])
        self.assertEqual(150.0, f["structural_height_mm"])

    def test_004_frame_clear(self):
        f = self.dim["frame"]
        self.assertEqual([500.0, 100.0], f["upper_clear_mm"])
        self.assertEqual([400.0, 140.0], f["lower_clear_mm"])
        self.assertEqual(110.0, f["vertical_2020_mm"])

    def test_005_battery(self):
        b = self.dim["battery"]
        self.assertEqual([150.9, 99.4, 92.5], [b["x_mm"], b["y_mm"], b["z_mm"]])
        self.assertEqual(1.2, b["mass_kg"])

    def test_006_battery_passage(self):
        self.assertEqual(108.0, self.dim["battery"]["insertion_clear_height_mm"])
        self.assertEqual("PHYSICAL_PASS_USER_REPORTED", self.dim["battery"]["terminal_equipped_frame_pass"])

    def test_007_terminal(self):
        t = self.dim["terminal"]
        self.assertEqual(29.5, t["pair_outer_span_mm"])
        self.assertEqual(20.0, t["inner_gap_mm"])
        self.assertIsNone(t["individual_width_mm"])

    def test_008_terminal_candidates(self):
        t = self.dim["terminal"]
        self.assertEqual([33.5, 34.5, 35.5], t["opening_candidates_mm"])
        self.assertEqual(34.5, t["preferred_candidate_mm"])
        self.assertIsNone(t["exact_x_mm"])

    def test_009_bbox_envelope(self):
        b = self.dim["bbox"]
        self.assertEqual([180.0, 114.0, 103.0], [b["outer_x_mm"], b["outer_y_mm"], b["service_envelope_z_mm"]])
        self.assertLessEqual(b["service_envelope_z_mm"], 103)

    def test_010_bbox_split(self):
        b = self.dim["bbox"]
        self.assertEqual(103.0, b["lower_body_height_mm"] + b["service_ring_height_mm"] + b["wear_pad_thickness_mm"])

    def test_011_bbox_cavity(self):
        b = self.dim["bbox"]
        self.assertEqual(107.6, b["inner_y_nominal_mm"])
        self.assertEqual(8.2, b["battery_y_clear_total_mm"])
        self.assertEqual(4.1, b["battery_y_clear_each_mm"])

    def test_012_bbox_motion(self):
        b = self.dim["bbox"]
        self.assertEqual("-X", b["removal_direction"])
        self.assertEqual("PITCH_AND_SLIDE", b["service_motion"])
        self.assertFalse(b["idler_support"])

    def test_013_bbox_modularity(self):
        b = self.dim["bbox"]
        self.assertTrue(b["wear_pad_replaceable"])
        self.assertFalse(b["final_terminal_cap_manufacturing"])
        self.assertFalse(b["final_waterproof"])

    def test_014_bbox_rail_candidates(self):
        self.assertEqual([130.0, 132.0, 134.0], self.dim["bbox"]["rail_width_candidates_mm"])

    def test_015_cbox_envelope(self):
        c = self.dim["cbox"]
        self.assertEqual(180.0, c["outer_x_mm"])
        self.assertEqual([90.0, 92.0, 94.0], c["width_candidates_mm"])
        self.assertEqual(92.0, c["selected_y_mm"])
        self.assertEqual(45.0, c["total_z_mm"])

    def test_016_cbox_width_table(self):
        rows = self.dim["cbox_width_comparison"]
        self.assertEqual([5.0, 4.0, 3.0], [r["nominal_clearance_each_mm"] for r in rows])
        self.assertEqual([4.5, 3.5, 2.5], [r["clearance_each_at_minus_1mm_frame_mm"] for r in rows])
        self.assertEqual(1, sum(r["selected"] for r in rows))

    def test_017_cbox_independence(self):
        c = self.dim["cbox"]
        self.assertFalse(c["on_bbox"])
        self.assertTrue(c["independent_support"])
        self.assertTrue(c["tray_removable"])
        self.assertTrue(c["connector_panel_replaceable"])

    def test_018_cbox_lid_pattern(self):
        c = self.dim["cbox"]
        self.assertEqual(16, c["bolt_count"])
        self.assertEqual(36.0, c["max_unsupported_gasket_span_mm"])
        self.assertEqual(45.0, c["body_height_mm"] + c["compressed_gasket_reference_mm"] + c["lid_thickness_mm"])

    def test_019_layout(self):
        layout = self.dim["layout"]
        self.assertEqual([-190, -10], layout["bbox_x_interval_mm"])
        self.assertEqual([10, 190], layout["cbox_x_interval_mm"])
        self.assertEqual(20, layout["gap_mm"])

    def test_020_interfaces(self):
        self.assertFalse(self.interfaces["bbox"]["idler_support"])
        self.assertEqual("REJECT", self.interfaces["bbox"]["friction_only_lock"])
        self.assertTrue(self.interfaces["cbox"]["independent_of_bbox"])
        self.assertEqual("REJECT", self.interfaces["cbox"]["petg_cantilever_primary_support"])

    def test_021_separation(self):
        s = self.interfaces["separation"]
        self.assertFalse(s["shared_lid"])
        self.assertFalse(s["cbox_load_through_bbox"])
        self.assertTrue(s["bbox_removal_without_opening_cbox"])

    def test_022_pitch_sweep(self):
        b = self.motion["bbox"]
        self.assertEqual([0, 2, 4, 6], b["angles_deg"])
        self.assertEqual([0, 125, 195, 220], b["reference_translation_minus_x_mm"])
        self.assertEqual("PHYSICAL_TEST_REQUIRED", b["actual_pitch"])

    def test_023_cbox_lid_service(self):
        self.assertTrue(self.motion["cbox"]["fixed_during_bbox_service"])
        self.assertFalse(self.motion["cbox"]["bbox_removal_required_for_lid"])

    def test_024_interference_all_zero(self):
        report = self.geom["interference"]
        self.assertTrue(report["all_zero_reference"])
        self.assertTrue(all(r["common_volume_mm3"] == 0 for r in report["rows"]))

    def test_025_interference_required_names(self):
        names = {r["check"] for r in self.geom["interference"]["rows"]}
        required = {"BATTERY_VS_BBOX_SHELL", "BATTERY_VS_RESTRAINT_PADS", "TERMINAL_W345_VS_SERVICE_RING",
                    "BBOX_INSTALLED_VS_FRAME", "BBOX_PITCH_SWEEP_VS_CBOX", "BBOX_PITCH_SWEEP_VS_CBOX_SUPPORT",
                    "BBOX_GRIP_VS_FRAME", "CBOX_VS_FRAME", "CBOX_LID_SERVICE_VS_FRAME"}
        self.assertTrue(required.issubset(names))

    def test_026_transform_holds(self):
        rows = self.geom["interference"]["rows"]
        self.assertEqual(6, sum("HOLD_ACTUAL_TRANSFORMS" in r["status"] for r in rows))

    def test_027_printability(self):
        p = self.geom["printability"]
        self.assertEqual([256, 256], p["bed_mm"])
        self.assertTrue(p["all_fit"])
        self.assertTrue(p["plate_components_clear"])
        self.assertTrue(all(value == 0 for value in p["plate_component_common_volume_mm3"].values()))
        self.assertFalse(p["sealing_face_support_contact"])
        self.assertEqual("USER_REQUIRED", p["slicer_confirmation"])

    def test_028_step_reload(self):
        steps = [p for p in B.CAD if p.endswith(".step")]
        self.assertEqual(26, len(steps))
        for rel in steps:
            shape = cq.importers.importStep(str(LANE / rel)).val()
            self.assertTrue(shape.isValid(), rel)
            self.assertGreater(shape.Volume(), 0, rel)

    def test_029_stl_semantics(self):
        stls = [p for p in B.CAD if p.endswith(".stl")]
        self.assertEqual(14, len(stls))
        for rel in stls:
            row = B.stl_semantic(LANE / rel)
            self.assertGreater(row["triangles"], 0, rel)
            self.assertTrue(all(value > 0 for value in row["bounds_mm"]), rel)

    def test_030_svg_parse(self):
        self.assertEqual(17, len(B.DRAWINGS))
        for rel in B.DRAWINGS:
            ET.parse(LANE / rel)

    def test_031_no_terminal_cap_stl(self):
        self.assertNotIn("cad/bbox_terminal_cap_reference.stl", B.CAD)

    def test_032_parent_protection(self):
        self.assertEqual("CAD_PASS", self.geom["parents"]["status"])
        self.assertEqual(5, len(self.geom["parents"]["parents"]))

    def test_033_authority_protection(self):
        self.assertEqual("CAD_PASS", B.authority_audit()["status"])

    def test_034_repository_guard(self):
        self.assertEqual("CAD_PASS", B.repository_guard(True)["status"])

    def test_035_commit_paths(self):
        lines = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual([f"{B.LANE_REL}/{p}" for p in B.PACKAGE_PATHS], lines)

    def test_036_sha256sums(self):
        lines = (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(B.PACKAGE_PATHS) - 1, len(lines))
        for line in lines:
            digest, rel = line.split("  ", 1)
            self.assertEqual(digest, B.sha(LANE / rel), rel)

    def test_037_release_gates(self):
        self.assertEqual("HOLD", self.valid["gates"]["BBOX_TERMINAL_CAP"])
        self.assertEqual("HOLD", self.valid["gates"]["CBOX_FINAL_ELECTRONICS"])
        self.assertFalse(self.valid["waterproof_pass"])

    def test_038_no_operational_approval(self):
        self.assertFalse(self.valid["battery_operational_approved"])
        self.assertFalse(self.valid["electronics_operational_approved"])
        self.assertFalse(self.valid["powered_rotation_approved"])
        self.assertFalse(self.valid["field_approved"])

    def test_039_missing_measurements(self):
        missing = self.valid["missing_nonblocking"]
        self.assertIn("TERMINAL_EXACT_X", missing)
        self.assertIn("CABLE_BEND_RADIUS", missing)
        self.assertIn("CBOX_HEAT_GENERATION", missing)

    def test_040_result_forms(self):
        bbox = (LANE / "BBOX_PHYSICAL_RESULT_FORM.md").read_text(encoding="utf-8")
        cbox = (LANE / "CBOX_PHYSICAL_RESULT_FORM.md").read_text(encoding="utf-8")
        self.assertIn("10 cycles", bbox)
        self.assertIn("water test NOT_TESTED/PASS/FAIL", cbox)

    def test_041_water_test_stages(self):
        limits = json.loads((LANE / "test_limits.json").read_text(encoding="utf-8"))
        self.assertEqual(5, len(limits["bbox"]["water_stages"]))
        self.assertEqual("PHYSICAL_TEST_REQUIRED", limits["cbox"]["waterproof"])

    def test_042_no_destructive_git_source(self):
        source = (LANE / B.SOURCE[0]).read_text(encoding="utf-8")
        for token in ('"checkout"', '"switch"', '"pull"', '"fetch"', '"reset"', '"restore"',
                      '"stash"', '"merge"', '"rebase"', '"cherry-pick"', '"clean"', '"add"', '"commit"', '"push"'):
            self.assertNotIn(token, source)

    def test_043_final_status(self):
        self.assertIn("PRINTABLE_PROTOTYPES_COMPLETE", self.valid["final_status"])
        self.assertIn("PHYSICAL_FIT_AND_SEAL_TEST_PENDING", self.valid["final_status"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
