#!/usr/bin/env python3
"""Contract tests for Common Rover guide clearance retest v0.9.3.6."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import sys
import unittest
import zipfile
from pathlib import Path, PurePosixPath


LANE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v0936_builder", LANE / "build_crawler_guide_clearance_retest_v0936.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("builder import failed")
B = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = B
SPEC.loader.exec_module(B)


class V0936Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.params = json.loads((LANE / "guide_retest_parameters_v0936.json").read_text(encoding="utf-8"))
        cls.rows = cls.params["analysis"]["stations"]

    def test_001_identity_and_exact_paths(self) -> None:
        self.assertEqual(B.DOCUMENT_ID, "PS-CR-V0936-GUIDE-CLEARANCE-RETEST")
        self.assertEqual(len(B.PACKAGE_PATHS), 30)
        self.assertEqual(B.lane_files(), sorted(B.PACKAGE_PATHS))

    def test_002_repository_guard(self) -> None:
        self.assertEqual(B.repository_audit(require_complete=True)["status"], "PASS")

    def test_003_parent_v0935_unchanged(self) -> None:
        result = B.parent_audit()
        self.assertEqual(result["status"], "PASS")
        if B.live_repository():
            self.assertEqual((result["file_count"], result["ledger_sha256"]), B.PARENT_SNAPSHOT)

    def test_004_selected_source_unchanged(self) -> None:
        result = B.source_audit()
        self.assertEqual(result["status"], "PASS")
        if B.live_repository():
            self.assertTrue(result["tracked"])
            self.assertEqual((result["file_count"], result["ledger_sha256"]), B.SOURCE_SNAPSHOT)

    def test_005_physical_width_and_guide_width(self) -> None:
        basis = self.params["physical_basis"]
        self.assertEqual(basis["link_maximum_width_mm"], 53.6)
        self.assertEqual(basis["guide_body_width_per_side_mm"], 4.0)

    def test_006_source_width_comparison_hold(self) -> None:
        comparison = self.params["source_comparison"]
        self.assertEqual(comparison["source_cad_link_max_width_mm"], 54.0)
        self.assertEqual(comparison["physical_link_max_width_mm"], 53.6)
        self.assertAlmostEqual(comparison["physical_minus_source_mm"], -0.4)
        self.assertEqual(comparison["link_geometry_change"], "PROHIBITED_NOT_CHANGED")
        self.assertIn("HOLD", comparison["status"])

    def test_007_old_coupon_supersession(self) -> None:
        superseded = self.params["superseded"]
        self.assertEqual(superseded["49.4"], "REJECT_TOO_NARROW")
        self.assertEqual(superseded["49.6"], "REJECT_TOO_NARROW")
        self.assertEqual(superseded["49.8"], "INVALID_AS_FULL_LINK_WIDTH_REFERENCE")
        self.assertEqual(superseded["50.4_50.6_50.8"], "SUPERSEDED_BEFORE_GENERATION")
        generated = "\n".join(B.STEP_FILES + B.STL_FILES + B.SVG_FILES)
        for token in ("49P4", "49P6", "49P8", "50P4", "50P6", "50P8"):
            self.assertNotIn(token, generated)

    def test_008_preserved_architecture(self) -> None:
        p = self.params["preserved"]
        self.assertEqual(p["link_pitch_mm"], 20.0)
        self.assertEqual(p["sprocket_tooth_count"], 12)
        self.assertEqual(p["sprocket_od_mm"], 66.14)
        self.assertEqual(p["pitch_diameter_mm"], 76.3943726841)
        self.assertEqual(p["drive_axle_bore_mm_reference"], 10.1)
        self.assertTrue(all(value == "UNCHANGED" for key, value in p.items() if key in ("link_geometry", "sprocket_geometry", "bearing_and_retainer", "roller_geometry", "crawler_loop_and_frame")))

    def test_009_exact_three_stl_outputs(self) -> None:
        self.assertEqual(len(B.STL_FILES), 3)
        self.assertTrue(all((LANE / path).is_file() for path in B.STL_FILES))

    def test_010_three_plates_nine_stations(self) -> None:
        self.assertEqual(self.params["analysis"]["plate_count"], 3)
        self.assertEqual(self.params["analysis"]["station_count"], 9)
        self.assertEqual(len(self.rows), 9)

    def test_011_exact_spacing_values(self) -> None:
        self.assertEqual(sorted({row["lower_zone_inner_spacing_mm"] for row in self.rows}), [54.2, 54.4, 54.6])

    def test_012_each_plate_has_exact_three_angles(self) -> None:
        for code in ("W54P2", "W54P4", "W54P6"):
            rows = [row for row in self.rows if row["spacing_code"] == code]
            self.assertEqual(sorted(row["angle_deg_from_vertical"] for row in rows), [35.0, 40.0, 45.0])

    def test_013_w54p2_only_54p2(self) -> None:
        self.assertEqual({row["lower_zone_inner_spacing_mm"] for row in self.rows if row["spacing_code"] == "W54P2"}, {54.2})

    def test_014_w54p4_only_54p4(self) -> None:
        self.assertEqual({row["lower_zone_inner_spacing_mm"] for row in self.rows if row["spacing_code"] == "W54P4"}, {54.4})

    def test_015_w54p6_only_54p6(self) -> None:
        self.assertEqual({row["lower_zone_inner_spacing_mm"] for row in self.rows if row["spacing_code"] == "W54P6"}, {54.6})

    def test_016_exact_guide_widths(self) -> None:
        self.assertTrue(all(row["left_guide_body_width_mm"] == 4.0 and row["right_guide_body_width_mm"] == 4.0 for row in self.rows))

    def test_017_outer_spans(self) -> None:
        expected = {"W54P2": 62.2, "W54P4": 62.4, "W54P6": 62.6}
        for row in self.rows:
            self.assertAlmostEqual(row["outer_guide_span_mm"], expected[row["spacing_code"]], places=6)

    def test_018_nominal_clearances(self) -> None:
        expected = {"W54P2": 0.3, "W54P4": 0.4, "W54P6": 0.5}
        for row in self.rows:
            self.assertAlmostEqual(row["nominal_clearance_per_side_mm"], expected[row["spacing_code"]], places=6)

    def test_019_measurement_planes_recorded(self) -> None:
        for row in self.rows:
            self.assertEqual(row["lower_zone_inner_spacing_mm"], row["slope_start_inner_spacing_mm"])
            self.assertEqual(row["lower_zone_inner_spacing_mm"], row["centered_reference_spacing_mm"])
            self.assertGreater(row["apex_zone_min_spacing_mm"], row["slope_start_inner_spacing_mm"])

    def test_020_guide_section_contract(self) -> None:
        guide = self.params["guide"]
        self.assertEqual(guide["height_mm"], 3.0)
        self.assertEqual(guide["lower_zone_height_mm"], 2.0)
        self.assertAlmostEqual(guide["lower_zone_ratio_percent"], 66.6666666667)
        self.assertEqual(guide["upper_zone_height_mm"], 1.0)
        self.assertAlmostEqual(guide["upper_zone_ratio_percent"], 33.3333333333)
        self.assertEqual(guide["length_mm"], 8.0)
        self.assertTrue(all(abs(row["finished_exposed_guide_height_mm"] - 3.0) <= 1e-6 for row in self.rows))

    def test_021_apex_radius_and_no_shelf(self) -> None:
        self.assertEqual(self.params["guide"]["apex_radius_mm"], 0.75)
        self.assertTrue(all(row["horizontal_apex_shelf_edges"] == 0 for row in self.rows))

    def test_022_centered_proxy_collision_zero(self) -> None:
        self.assertTrue(all(row["physical_link_width_mm"] == 53.6 for row in self.rows))
        self.assertTrue(all(row["centered_proxy_collision_mm3"] <= 1e-6 for row in self.rows))

    def test_023_symmetry_and_direction_equivalence(self) -> None:
        self.assertTrue(all(row["left_right_symmetric"] for row in self.rows))
        self.assertTrue(all(row["forward_reverse_equivalent"] for row in self.rows))

    def test_024_no_disconnected_guides_or_floating_markings(self) -> None:
        self.assertTrue(all(item["solid_count"] == 1 for item in self.params["analysis"]["plates"].values()))
        self.assertGreater(self.params["analysis"]["marking_zone_min_abs_y_mm"], self.params["analysis"]["functional_guide_outer_max_abs_y_mm"])

    def test_025_markings_match_geometry(self) -> None:
        marks = self.params["markings"]
        self.assertEqual(marks["plate"], ["W54.2", "W54.4", "W54.6"])
        self.assertEqual(marks["station"], ["A35", "A40", "A45"])
        self.assertGreaterEqual(marks["height_mm"], 3.0)
        self.assertGreaterEqual(marks["emboss_mm"], 0.5)
        self.assertFalse(marks["functional_surface_intersection"])
        for token in ("LINK MAX 53.6", "GUIDE 4.0", "FIT TEST ONLY", "NO POWER", "NO LOAD"):
            self.assertIn(token, marks["common"])

    def test_026_dimension_csv_exact(self) -> None:
        with (LANE / "guide_retest_dimension_report_v0936.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 9)
        self.assertEqual({row["station_id"] for row in rows}, {row["station_id"] for row in self.rows})

    def test_027_source_comparison_csv(self) -> None:
        text = (LANE / "guide_retest_source_comparison_v0936.csv").read_text(encoding="utf-8")
        self.assertIn("54.0,53.6", text)
        self.assertIn("PHYSICAL_53P6_PRECEDENCE", text)

    def test_028_step_reload(self) -> None:
        report = B.verify_steps()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["pass_count"], report["count"]), (5, 5))

    def test_029_stl_watertight_single_component(self) -> None:
        report = B.verify_stls()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["pass_count"], report["count"]), (3, 3))
        self.assertTrue(all(row["watertight"] and row["components"] == 1 and row["volume_mm3"] > 0 for row in report["rows"]))

    def test_030_svg_parse(self) -> None:
        report = B.verify_svgs()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual((report["pass_count"], report["count"]), (6, 6))

    def test_031_manifest_and_hashes(self) -> None:
        manifest, hashes = B.verify_manifest(), B.verify_hashes()
        self.assertEqual(manifest["status"], "PASS")
        self.assertEqual(manifest["entry_count"], 30)
        self.assertEqual(hashes["status"], "PASS")
        self.assertEqual(hashes["verified"], 29)

    def test_032_commit_paths_exact_new_lane(self) -> None:
        values = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
        prefix = B.LANE_REL + "/"
        self.assertEqual(len(values), 30)
        self.assertTrue(all(value.startswith(prefix) for value in values))
        self.assertEqual([value[len(prefix):] for value in values], list(B.PACKAGE_PATHS))

    def test_033_builder_verify(self) -> None:
        report = B.verify()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["geometry_stations"], "9/9 PASS")

    def test_034_no_power_manufacturing_or_authority_approval(self) -> None:
        approval = self.params["approval"]
        self.assertEqual(approval["final_guide_selection"], "HOLD")
        self.assertEqual(approval["full_crawler_part_release"], "HOLD")
        for key in ("powered_rotation", "torque_load", "mud_test", "water_test", "field_deployment", "authority_update", "manufacturing"):
            self.assertEqual(approval[key], "NOT_APPROVED")

    def test_035_provisional_first_test_only(self) -> None:
        self.assertEqual(self.params["guide"]["provisional_first_test"], "W54P4_A40")
        self.assertEqual(B.PROVISIONAL_FIRST_TEST, "W54P4_A40")

    def test_036_zip_contract_when_requested(self) -> None:
        value = os.environ.get("V0936_TEST_ZIP")
        if not value:
            self.skipTest("V0936_TEST_ZIP not set")
        path = Path(value)
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            self.assertEqual(names, list(B.PACKAGE_PATHS))
            self.assertEqual(len(names), len(set(names)))
            self.assertFalse(any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name for name in names))
            self.assertFalse(any(name.startswith("cad/") or "AUTHORITY" in name.upper() for name in names))
            values = {}
            for line in archive.read("SHA256SUMS.txt").decode("utf-8").splitlines():
                if line.strip():
                    expected, rel = line.split("  ", 1)
                    values[rel] = expected
            self.assertEqual(set(values), set(B.PACKAGE_PATHS) - {"SHA256SUMS.txt"})
            self.assertTrue(all(hashlib.sha256(archive.read(rel)).hexdigest() == expected for rel, expected in values.items()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
