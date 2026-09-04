from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import unittest
import zipfile
from pathlib import Path, PurePosixPath

import cadquery as cq


LANE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v0935_builder", LANE / "build_crawler_tracking_retention_patch_v0935.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot import v0.9.3.5 builder")
B = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = B
SPEC.loader.exec_module(B)


class V0935Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.params = json.loads((LANE / "crawler_tracking_patch_parameters_v0935.json").read_text(encoding="utf-8"))
        cls.analysis = cls.params["analysis"]

    def test_001_identity_and_exact_paths(self) -> None:
        self.assertEqual(B.DOCUMENT_ID, "PS-CR-V0935-CRAWLER-TRACKING-RETENTION-PATCH")
        self.assertEqual(B.VERSION, "0.9.3.5")
        self.assertEqual(len(B.PACKAGE_PATHS), 34)
        self.assertEqual((len(B.STEP_FILES), len(B.STL_FILES), len(B.SVG_FILES)), (5, 6, 8))

    def test_002_repository_guard(self) -> None:
        self.assertEqual(B.repository_audit(require_complete=True)["status"], "PASS")

    def test_003_parent_lanes_unchanged(self) -> None:
        audit = B.parent_audit()
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(len(audit["lanes"]), 10)

    def test_004_selected_source_unchanged(self) -> None:
        audit = B.source_audit()
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["selected"], B.SOURCE_LANE_REL)

    def test_005_source_selection_evidence(self) -> None:
        selected = [row for row in self.params["source_candidates"] if row["selection"] == "SELECTED"]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["candidate"], "CRAWLER_H1_PRETEST_V0_1")
        self.assertIn("12T/20mm/10.3mm", selected[0]["evidence"])

    def test_006_physical_result(self) -> None:
        result = self.params["physical_result"]
        self.assertTrue(result["full_loop_assembled"])
        self.assertEqual(result["hand_rotations_approx"], 20)
        self.assertEqual(result["complete_derailment"], 0)
        self.assertEqual(result["right_turn_event"], "INNER_LINK_TOOTH_CLIMBED_GUIDE")

    def test_007_tooth_pitch_od_preserved(self) -> None:
        preserved = self.params["preserved"]
        self.assertEqual(preserved["tooth_count"], 12)
        self.assertEqual(preserved["link_pitch_mm"], 20.0)
        self.assertEqual(preserved["sprocket_od_mm"], 66.14)
        self.assertAlmostEqual(preserved["pitch_diameter_mm"], 240.0 / 3.141592653589793)

    def test_008_link_count_and_loop_preserved(self) -> None:
        preserved = self.params["preserved"]
        self.assertEqual(preserved["link_count_source_candidate"], 40)
        self.assertEqual(preserved["loop_nominal_length_mm"], 800.0)

    def test_009_axle_bore_classification(self) -> None:
        bores = self.params["bore_classification"]
        self.assertEqual(bores["drive_sprocket_center"]["class"], "ROTATING_CLEARANCE_BORE")
        self.assertTrue(bores["drive_sprocket_center"]["apply_10p1"])
        self.assertFalse(bores["idler_bearing_inner_race"]["apply_10p1"])
        self.assertFalse(bores["idler_center_relief"]["apply_10p1"])

    def test_010_corrected_main_bore_exact_10p1(self) -> None:
        self.assertEqual(B.S.corrected_drive_bore_mm, 10.1)
        shape = cq.importers.importStep(str(LANE / B.CORRECTED_FILES[0])).val()
        diameters = []
        for edge in shape.Edges():
            if edge.geomType() == "CIRCLE":
                try:
                    diameters.append(2.0 * edge.radius())
                except Exception:
                    pass
        self.assertTrue(any(abs(value - 10.1) < 1e-6 for value in diameters), diameters)

    def test_011_axle_axis_concentricity_unchanged(self) -> None:
        self.assertEqual(self.analysis["preservation"]["axis_unchanged"], [0.0, 0.0])
        self.assertTrue(self.analysis["preservation"]["bolt_pattern_unchanged"])

    def test_012_idler_bearing_interface_unchanged(self) -> None:
        bores = self.params["bore_classification"]
        self.assertEqual(bores["idler_bearing_inner_race"]["nominal_mm"], 10.0)
        self.assertEqual(bores["idler_center_relief"]["cad_mm"], 12.0)
        self.assertEqual(bores["bearing_seat"]["cad_mm"], 26.2)
        self.assertEqual(bores["bearing_seat"]["change"], "HOLD_PENDING_COUPON")

    def test_013_axle_coupon_candidates_and_markings(self) -> None:
        coupon = self.params["axle_coupon"]
        self.assertEqual(coupon["cad_nominal_diameters_mm"], [10.0, 10.1, 10.2])
        self.assertEqual(coupon["main_design_mm"], 10.1)
        self.assertEqual(coupon["markings"], ["AXLE 10.0", "AXLE 10.1", "AXLE 10.2", "FIT TEST ONLY"])

    def test_014_original_guide_geometry_recorded(self) -> None:
        original = self.params["guide"]["original"]
        self.assertEqual((original["height_mm"], original["thickness_mm"], original["top_width_mm"]), (3.0, 2.5, 2.5))
        self.assertEqual(original["classification"], "VERTICAL_WALL_WITH_BROAD_FLAT_TOP")

    def test_015_retention_and_recovery_zone_percentages(self) -> None:
        corrected = self.params["guide"]["corrected"]
        self.assertGreaterEqual(corrected["lower_percent"], 60.0)
        self.assertLessEqual(corrected["lower_percent"], 70.0)
        self.assertGreaterEqual(corrected["upper_percent"], 30.0)
        self.assertLessEqual(corrected["upper_percent"], 40.0)
        self.assertEqual((corrected["lower_retention_height_mm"], corrected["upper_recovery_height_mm"]), (2.0, 1.0))

    def test_016_guide_angle_candidates(self) -> None:
        corrected = self.params["guide"]["corrected"]
        self.assertEqual(corrected["angle_candidates_deg"], [35.0, 40.0, 45.0])
        self.assertEqual(corrected["angle_definition"], "DEGREES_FROM_VERTICAL")
        self.assertEqual(corrected["recommended_provisional_angle_deg"], 40.0)

    def test_017_apex_radius(self) -> None:
        radius = self.params["guide"]["corrected"]["apex_radius_mm"]
        self.assertGreaterEqual(radius, 0.5)
        self.assertLessEqual(radius, 1.0)
        self.assertEqual(radius, 0.75)

    def test_018_clearance_candidates(self) -> None:
        corrected = self.params["guide"]["corrected"]
        self.assertEqual(corrected["clearance_candidates_per_side_mm"], [0.3, 0.4, 0.5])
        self.assertEqual(corrected["recommended_clearance_per_side_mm"], 0.4)

    def test_019_centered_link_collision_zero(self) -> None:
        self.assertLessEqual(self.analysis["guide"]["centered_tooth_collision_mm3"], 1e-6)
        self.assertLessEqual(self.analysis["guide"]["sprocket_tooth_collision_mm3"], 1e-6)
        self.assertEqual(self.analysis["guide"]["roller_envelope_od_mm"], 50.0)
        self.assertEqual(self.analysis["guide"]["roller_envelope_axial_width_mm"], 44.0)
        self.assertLessEqual(self.analysis["guide"]["roller_collision_mm3"], 1e-6)
        self.assertLessEqual(self.analysis["guide"]["screw_collision_mm3"], 1e-6)

    def test_020_displaced_link_contacts_recovery_face(self) -> None:
        self.assertGreater(self.analysis["guide"]["displaced_tooth_contact_mm3"], 0.0)

    def test_021_left_right_symmetry(self) -> None:
        self.assertTrue(self.analysis["guide"]["left_right_symmetric"])
        self.assertEqual(self.params["guide"]["corrected"]["left_right"], "SYMMETRIC")

    def test_022_forward_reverse_equivalence(self) -> None:
        self.assertTrue(self.analysis["guide"]["forward_reverse_equivalent"])
        self.assertEqual(self.params["guide"]["corrected"]["forward_reverse"], "EQUIVALENT")

    def test_023_recommended_surface_normal_is_lateral_primary(self) -> None:
        row = next(item for item in self.analysis["guide"]["angle_rows"] if item["recommended"])
        self.assertGreater(row["lateral_normal_fraction"], row["vertical_normal_fraction"])

    def test_024_bearing_measurements_recorded(self) -> None:
        bearing = self.params["bearing"]
        self.assertEqual(bearing["measured_outer_diameter_mm_approx"], 25.9)
        self.assertEqual(bearing["printed_seat_diameter_mm_approx"], [26.1, 26.2])
        self.assertEqual(bearing["source_seat_cad_mm"], 26.2)

    def test_025_bearing_coupon_candidates_separate_cad_and_print(self) -> None:
        bearing = self.params["bearing"]
        self.assertEqual(bearing["target_as_printed_bores_mm"], [25.7, 25.8, 25.9, 26.0])
        self.assertEqual(bearing["coupon_cad_commands_mm"], [25.7, 25.8, 25.9, 26.0])
        self.assertIn("NOT_AS_PRINTED_RESULT", bearing["coupon_warning"])

    def test_026_retainer_clear_of_inner_race_shield_and_shaft(self) -> None:
        result = self.analysis["retainer"]
        self.assertLessEqual(result["inner_race_collision_mm3"], 1e-6)
        self.assertLessEqual(result["shield_proxy_collision_mm3"], 1e-6)
        self.assertLessEqual(result["shaft_collision_mm3"], 1e-6)

    def test_027_retainer_remains_physical_hold(self) -> None:
        retainer = self.params["bearing"]["retainer"]
        self.assertEqual(retainer["type"], "REMOVABLE_OUTER_RACE_ONLY")
        self.assertEqual(retainer["m3_count_candidate"], 3)
        self.assertFalse(retainer["adhesive_primary"])
        self.assertEqual(retainer["actual_shield_od"], "MEASUREMENT_HOLD")
        self.assertEqual(retainer["status"], "PHYSICAL_COUPON_REQUIRED")

    def test_028_no_new_thin_wall(self) -> None:
        self.assertGreaterEqual(self.analysis["bore"]["radial_hub_to_nearest_bolt_wall_mm"], 4.0)

    def test_029_no_floating_part_solids(self) -> None:
        self.assertTrue(all(value == 1 for value in self.analysis["floating"].values()))

    def test_030_step_reload(self) -> None:
        report = B.verify_steps()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["pass_count"], report["count"]), (5, 5))

    def test_031_stl_manifold(self) -> None:
        report = B.verify_stls()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["pass_count"], report["count"]), (6, 6))
        self.assertTrue(all(row["watertight"] and row["components"] == 1 for row in report["rows"]))

    def test_032_svg_parse(self) -> None:
        report = B.verify_svgs()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["pass_count"], report["count"]), (8, 8))

    def test_033_no_power_or_manufacturing_approval(self) -> None:
        approval = self.params["approval"]
        for key in ("belt_tension", "powered_rotation", "torque_load", "mud_test", "water_test", "field_deployment", "manufacturing", "authority_update"):
            self.assertEqual(approval[key], "NOT_APPROVED")
        text = (LANE / "NO_POWER_NO_LOAD_ONLY.txt").read_text(encoding="utf-8")
        self.assertIn("POWERED_ROTATION=NOT_APPROVED", text)

    def test_034_commit_paths_exact_new_lane(self) -> None:
        values = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
        prefix = "cad/common_rover/common_rover_crawler_tracking_retention_patch_v0_9_3_5/"
        self.assertEqual(len(values), 34)
        self.assertTrue(all(value.startswith(prefix) for value in values))
        self.assertEqual([value[len(prefix):] for value in values], list(B.PACKAGE_PATHS))

    def test_035_manifest_and_hashes(self) -> None:
        manifest, hashes = B.verify_manifest(), B.verify_hashes()
        self.assertEqual(manifest["status"], "PASS")
        self.assertEqual(manifest["entry_count"], 34)
        self.assertEqual(hashes["status"], "PASS")
        self.assertEqual(hashes["verified"], 33)

    def test_036_machine_evidence(self) -> None:
        self.assertEqual(B.verify_evidence()["status"], "PASS")

    def test_037_builder_verify(self) -> None:
        report = B.verify()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["formal_paths"], 34)

    def test_038_physical_test_plan_contract(self) -> None:
        text = (LANE / "physical_test_plan_v0935.md").read_text(encoding="utf-8")
        self.assertIn("Forward 100 and reverse 100", text)
        self.assertIn("Forward 20 and reverse 20", text)
        self.assertIn("Right turn 10 passes and left turn 10", text)
        self.assertIn("one to two link pitches", text)

    def test_039_remaining_measurements_not_fabricated(self) -> None:
        text = (LANE / "remaining_measurements_v0935.md").read_text(encoding="utf-8")
        self.assertIn("Exact physical link count", text)
        self.assertIn("Bearing shield/seal outside diameter", text)
        self.assertIn("As-printed 10.0/10.1/10.2", text)

    def test_040_zip_contract_when_requested(self) -> None:
        value = os.environ.get("V0935_TEST_ZIP")
        if not value:
            self.skipTest("V0935_TEST_ZIP not set")
        path = Path(value)
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            self.assertEqual(names, list(B.PACKAGE_PATHS))
            self.assertEqual(len(names), len(set(names)))
            self.assertFalse(any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name for name in names))
            self.assertFalse(any("AUTHORITY" in name.upper() and "crawler_tracking" not in name.lower() for name in names))
            values = {}
            for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
                if line.strip():
                    expected, rel = line.split("  ", 1)
                    values[rel] = expected
            self.assertEqual(set(values), set(B.PACKAGE_PATHS) - {"SHA256SUMS.txt"})
            self.assertTrue(all(hashlib.sha256(archive.read(rel)).hexdigest() == expected for rel, expected in values.items()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
