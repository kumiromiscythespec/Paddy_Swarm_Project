#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_common_rover_crawler_link_anti_derail_guard_v0_9_6_17.py"
SPEC = importlib.util.spec_from_file_location("crawler_link_guard_v09617", BUILDER)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class CrawlerLinkGuardContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verify = mod.verify_lane()
        cls.params = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
        cls.report = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.source = cls.verify["source_metrics"]
        cls.final = cls.verify["final_metrics"]

    def test_001_repository_root(self): self.assertEqual(Path(self.verify["repository"]["repository"]).resolve(), mod.REPO_ROOT.resolve())
    def test_002_branch(self): self.assertEqual(self.verify["repository"]["branch"], mod.EXPECTED_BRANCH)
    def test_003_head(self): self.assertEqual(self.verify["repository"]["head"], mod.EXPECTED_HEAD)
    def test_004_staged_zero(self): self.assertEqual(self.verify["repository"]["staged_count"], 0)
    def test_005_tracked_dirty_exact(self): self.assertEqual(self.verify["repository"]["tracked_dirty_paths"], list(mod.AUTHORITY_SHA256))
    def test_006_existing_untracked_count(self): self.assertEqual(self.verify["repository"]["outside_untracked_count"], mod.BASELINE_UNTRACKED_COUNT)
    def test_007_existing_untracked_digest(self): self.assertEqual(self.verify["repository"]["outside_untracked_tree_sha256"], mod.BASELINE_UNTRACKED_TREE_SHA256)
    def test_008_authority_hashes(self): self.assertEqual(self.verify["repository"]["authority_sha256"], mod.AUTHORITY_SHA256)
    def test_009_protected_lanes(self): self.assertTrue(all(x["status"] == "UNCHANGED" for x in self.verify["repository"]["protected_lanes"].values()))
    def test_010_source_sha(self): self.assertEqual(mod.sha256_file(LANE / mod.SOURCE_COPY), mod.SOURCE_SHA256)
    def test_011_source_bounds(self):
        for actual_row, expected_row in zip(self.source["bounds_mm"], mod.SOURCE_EXPECTED_BOUNDS):
            for actual, expected in zip(actual_row, expected_row): self.assertAlmostEqual(actual, expected, places=5)
    def test_012_source_extents(self):
        for actual, expected in zip(self.source["extents_mm"], mod.SOURCE_EXPECTED_EXTENTS): self.assertAlmostEqual(actual, expected, places=5)
    def test_013_source_watertight(self): self.assertTrue(self.source["watertight"])
    def test_014_source_single_solid(self): self.assertEqual(self.source["connected_solid_count"], 1)
    def test_015_source_filename_alias_recorded(self): self.assertTrue(self.report["source_authority"]["repository_alias_verified_by_exact_sha"])
    def test_016_guard_identification(self): self.assertEqual(self.report["source_authority"]["guard_feature_identification"]["status"], "UNAMBIGUOUS")
    def test_017_stl_physical_datum_hold(self): self.assertEqual(self.report["datum"]["relationship"], "UNRESOLVED")
    def test_018_no_scale(self): self.assertFalse(self.report["datum"]["stl_scaled"])
    def test_019_old_guard_height(self): self.assertEqual(self.params["physical_authority"]["old_guard_height_mm"], 6.0)
    def test_020_connector_protrusion(self): self.assertEqual(self.params["physical_authority"]["connector_protrusion_mm"], 5.1)
    def test_021_old_margin(self): self.assertAlmostEqual(self.params["physical_authority"]["old_height_margin_mm"], 0.9)
    def test_022_old_root_failure(self): self.assertEqual(self.params["physical_authority"]["current_root_status"], "PHYSICAL_BREAKAGE_RECORDED")
    def test_023_lateral_shift(self): self.assertEqual(self.params["physical_authority"]["max_lateral_shift_mm"], 1.8)
    def test_024_frame_clearance_reference(self): self.assertEqual(self.params["physical_authority"]["frame_clearance_with_8mm_spacer_mm"], 4.4)
    def test_025_one_design(self): self.assertEqual(self.params["reinforced_design"]["design_count"], 1)
    def test_026_thick_root_only(self): self.assertEqual(self.params["reinforced_design"]["selection"], "THICK_ROOT_ONLY")
    def test_027_guard_height(self): self.assertEqual(self.params["reinforced_design"]["guard_height_mm"], 9.0)
    def test_028_upper_thickness(self): self.assertEqual(self.params["reinforced_design"]["upper_thickness_mm"], 5.0)
    def test_029_root_thickness(self): self.assertEqual(self.params["reinforced_design"]["root_min_thickness_mm"], 6.0)
    def test_030_root_fillet(self): self.assertEqual(self.params["reinforced_design"]["root_fillet_class_mm"], 3.0)
    def test_031_top_edge(self): self.assertEqual(self.params["reinforced_design"]["top_edge_class_mm"], 1.0)
    def test_032_nominal_margin(self): self.assertEqual(self.params["reinforced_design"]["nominal_connector_margin_mm"], 3.9)
    def test_033_frame_side_delta(self): self.assertEqual(self.params["reinforced_design"]["outboard_frame_side_delta_mm"], 0.0)
    def test_034_predicted_frame_clearance(self): self.assertGreaterEqual(self.params["reinforced_design"]["predicted_frame_clearance_mm"], 3.0)
    def test_035_removed_volume_zero(self): self.assertLessEqual(self.report["geometry"]["volumes"]["removed_volume_mm3"], 1e-6)
    def test_036_added_volume_positive(self): self.assertGreater(self.report["geometry"]["volumes"]["added_volume_mm3"], 0.0)
    def test_037_final_primary_mesh(self): self.assertTrue(self.final["watertight"])
    def test_038_final_single_solid(self): self.assertEqual(self.final["connected_solid_count"], 1)
    def test_039_final_width_preserved(self): self.assertAlmostEqual(self.final["extents_mm"][1], 54.0, places=6)
    def test_040_final_height(self): self.assertAlmostEqual(self.final["extents_mm"][2], 24.75, places=6)
    def test_041_step_hold(self): self.assertEqual(self.params["output"]["step_status"], "HOLD_SOURCE_IS_MESH")
    def test_042_step_count_zero(self): self.assertEqual(self.verify["step_count"], 0)
    def test_043_stl_count_one(self): self.assertEqual(self.verify["stl_count"], 1)
    def test_044_svg_count_seven(self): self.assertEqual(self.verify["svg_count"], 7)
    def test_045_drive_wheel_dependency_zero(self): self.assertEqual(self.verify["drive_wheel_geometry_dependency_count"], 0)
    def test_046_no_drive_lane_imports(self): self.assertEqual(mod.firewall_dependency_count(BUILDER), 0)
    def test_047_exact_path_count(self): self.assertEqual(self.verify["path_count"], mod.EXPECTED_PATH_COUNT)
    def test_048_manifest_exact(self): self.assertEqual((LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines(), mod.EXPECTED_FILES)
    def test_049_commit_paths_exact(self): self.assertEqual(len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()), mod.EXPECTED_PATH_COUNT)
    def test_050_sha_mismatch_zero(self): self.assertEqual(self.verify["sha_mismatch_count"], 0)
    def test_051_full_link_print_quantity_one(self): self.assertEqual(self.params["output"]["print_quantity"], 1)
    def test_052_material_petg(self): self.assertEqual(self.params["output"]["material"], "PETG")
    def test_053_printer_bambu_a1(self): self.assertEqual(self.params["output"]["printer"], "Bambu A1")
    def test_054_powered_not_approved(self): self.assertEqual(self.params["output"]["powered_rotation"], "NOT_APPROVED_BY_THIS_LANE")
    def test_055_status_complete(self): self.assertIn("CRAWLER_LINK_ANTI_DERAIL_GUARD_COMPLETE", self.report["status"])
    def test_056_no_fail_checks(self): self.assertFalse(any(v.startswith("FAIL") for v in self.report["checks"].values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
