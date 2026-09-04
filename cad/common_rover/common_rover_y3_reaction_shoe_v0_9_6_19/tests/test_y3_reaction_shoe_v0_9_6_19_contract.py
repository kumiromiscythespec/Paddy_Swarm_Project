#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import unittest

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_y3_reaction_shoe_v0_9_6_19.py"
SPEC = importlib.util.spec_from_file_location("y3_reaction_shoe_v09619", BUILDER)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = mod; SPEC.loader.exec_module(mod)

class Y3ReactionShoeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = mod.verify_lane(); cls.p = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8")); cls.r = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8")); cls.g = cls.r["geometry"]
    def test_001_root(self): self.assertEqual(Path(self.v["repository"]["repository"]).resolve(), mod.REPO_ROOT.resolve())
    def test_002_branch(self): self.assertEqual(self.v["repository"]["branch"], mod.EXPECTED_BRANCH)
    def test_003_head(self): self.assertEqual(self.v["repository"]["head"], mod.EXPECTED_HEAD)
    def test_004_staged(self): self.assertEqual(self.v["repository"]["staged_count"], 0)
    def test_005_dirty(self): self.assertEqual(self.v["repository"]["tracked_dirty_paths"], mod.TRACKED_DIRTY)
    def test_006_outside_count(self): self.assertEqual(self.v["repository"]["outside_untracked_count"], mod.BASE_OUTSIDE_COUNT)
    def test_007_outside_digest(self): self.assertEqual(self.v["repository"]["outside_untracked_tree_sha256"], mod.BASE_OUTSIDE_DIGEST)
    def test_008_authority(self): self.assertEqual(self.v["repository"]["authority_sha256"], mod.AUTHORITY_SHA256)
    def test_009_protected(self): self.assertTrue(all(x["status"] == "UNCHANGED" for x in self.v["repository"]["protected_lanes"].values()))
    def test_010_source_hashes(self): self.assertEqual(self.v["repository"]["source_hashes"], mod.SOURCE_HASHES)
    def test_011_exact_source(self): self.assertEqual(self.p["source_geometry"]["status"], "EXACT_PROTECTED_SOURCE")
    def test_012_not_guessed(self): self.assertFalse(self.p["source_geometry"]["guessed_reconstruction"])
    def test_013_source_function(self): self.assertEqual(self.p["source_geometry"]["generating_function"], "reaction_yoke(3.7)")
    def test_014_bounds(self): self.assertEqual(self.g["source"]["bounds_mm"], [15.0, 15.2, 12.0])
    def test_015_volume(self): self.assertEqual(self.g["source"]["volume_mm3"], 2212.752)
    def test_016_count(self): self.assertEqual(self.p["reaction_shoe"]["quantity_per_sprocket"], 2)
    def test_017_identical(self): self.assertTrue(self.p["reaction_shoe"]["left_right_geometry_identical"])
    def test_018_rotation(self): self.assertEqual(self.p["reaction_shoe"]["installed_rotation_difference_deg"], 90.0)
    def test_019_height(self): self.assertEqual(self.p["reaction_shoe"]["height_mm"], 3.7)
    def test_020_shoe_width(self): self.assertEqual(self.p["reaction_shoe"]["receiver_facing_nominal_width_mm"], 15.2)
    def test_021_receiver(self): self.assertEqual(self.p["receiver"]["name"], "YW30")
    def test_022_receiver_width(self): self.assertEqual(self.p["receiver"]["width_mm"], 15.5)
    def test_023_clearance(self): self.assertEqual(self.p["receiver"]["nominal_total_clearance_mm"], 0.3)
    def test_024_head_top(self): self.assertEqual(self.p["head_clearance"]["m4_head_top_mm"], 4.3)
    def test_025_vertical_margin(self): self.assertEqual(self.p["head_clearance"]["vertical_margin_mm"], 0.6)
    def test_026_positive_stop(self): self.assertTrue(self.p["reaction_shoe"]["positive_stop"])
    def test_027_shoulders(self): self.assertTrue(self.p["reaction_shoe"]["broad_shoulders"])
    def test_028_not_roof_only(self): self.assertTrue(self.p["reaction_shoe"]["primary_torque_reaction_component"])
    def test_029_service_notch(self): self.assertTrue(self.p["reaction_shoe"]["service_notch"])
    def test_030_cap_removal(self): self.assertTrue(self.p["receiver"]["cap_removal_required"])
    def test_031_insertion_samples(self): self.assertEqual(len(self.g["insertion"]["rows"]), 110)
    def test_032_insertion_pass(self): self.assertTrue(self.g["insertion"]["pass"])
    def test_033_insertion_collision(self): self.assertEqual(self.g["insertion"]["max_unintended_intersection_mm3"], 0.0)
    def test_034_final_collision(self): self.assertEqual(self.g["final_installed_max_unintended_intersection_mm3"], 0.0)
    def test_035_main_collision(self): self.assertTrue(all(row["main_mm3"] == 0 for row in self.g["final_installed_collision_rows"]))
    def test_036_m4_collision(self): self.assertTrue(all(row["headed_m4_mm3"] == 0 for row in self.g["final_installed_collision_rows"]))
    def test_037_collar_collision(self): self.assertTrue(all(row["collar_mm3"] == 0 for row in self.g["final_installed_collision_rows"]))
    def test_038_shaft_collision(self): self.assertTrue(all(row["shaft_mm3"] == 0 for row in self.g["final_installed_collision_rows"]))
    def test_039_cap_collision(self): self.assertTrue(all(row["cap_and_dual_l_hooks_mm3"] == 0 for row in self.g["final_installed_collision_rows"]))
    def test_040_key_collision(self): self.assertTrue(all(row["stop_key_mm3"] == 0 for row in self.g["final_installed_collision_rows"]))
    def test_041_shoe_collision(self): self.assertTrue(all(row["other_shoe_mm3"] == 0 for row in self.g["final_installed_collision_rows"]))
    def test_042_single_step(self): self.assertTrue((LANE / mod.CAD[0]).is_file())
    def test_043_single_stl(self): self.assertTrue((LANE / mod.CAD[1]).is_file())
    def test_044_pair_stl(self): self.assertTrue((LANE / mod.CAD[2]).is_file())
    def test_045_assembly_step(self): self.assertTrue((LANE / mod.CAD[3]).is_file())
    def test_046_single_watertight(self): self.assertTrue(self.v["single_mesh"]["watertight"])
    def test_047_single_solid(self): self.assertEqual(self.v["single_mesh"]["connected_solid_count"], 1)
    def test_048_pair_watertight(self): self.assertTrue(self.v["pair_mesh"]["watertight"])
    def test_049_pair_two_solids(self): self.assertEqual(self.v["pair_mesh"]["connected_solid_count"], 2)
    def test_050_no_runner(self): self.assertEqual(self.p["print"]["runner"], "NONE")
    def test_051_first_print_one(self): self.assertEqual(self.p["print"]["first_print_quantity"], 1)
    def test_052_v18_preserved(self): self.assertTrue(self.v["v09618_preserved"])
    def test_053_crawler_dependency(self): self.assertEqual(self.v["crawler_guard_geometry_dependency_count"], 0)
    def test_054_step_count(self): self.assertEqual(self.v["step_count"], 2)
    def test_055_stl_count(self): self.assertEqual(self.v["stl_count"], 2)
    def test_056_svg_count(self): self.assertEqual(self.v["svg_count"], 6)
    def test_057_path_count(self): self.assertEqual(self.v["path_count"], 34)
    def test_058_powered(self): self.assertEqual(self.p["powered_rotation"], "NOT_APPROVED")

if __name__ == "__main__": unittest.main(verbosity=2)
