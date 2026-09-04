#!/usr/bin/env python3
"""Standalone contract tests for the PTO axial shim test set."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_pto_axial_shim_spacer_test_v001.py"
spec = importlib.util.spec_from_file_location("pto_axial_shim_builder", BUILDER)
assert spec and spec.loader
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)


class ShimContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guard = b.repository_guard()
        cls.params = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
        cls.report = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.collision = json.loads((LANE / "collision_report.json").read_text(encoding="utf-8"))

    def test_001_repository(self): self.assertEqual(b.REPO.resolve(), Path(r"D:\Paddy_Swarm_Project").resolve())
    def test_002_branch(self): self.assertEqual(self.guard["branch"], b.BRANCH)
    def test_003_head(self): self.assertEqual(self.guard["head"], b.HEAD)
    def test_004_staged_zero(self): self.assertEqual(self.guard["staged"], 0)
    def test_005_front_protected(self): self.assertEqual(b.tree_hash(b.FRONT_LANE), b.FRONT_TREE_SHA)
    def test_006_pto_protected(self): self.assertEqual(b.tree_hash(b.PTO_LANE), b.PTO_TREE_SHA)
    def test_007_spacer_source_protected(self): self.assertEqual(b.tree_hash(b.SPACER_SOURCE_LANE), b.SPACER_SOURCE_TREE_SHA)
    def test_008_source_exact(self): self.assertEqual(b.sha256(b.SPACER_SOURCE), b.SPACER_SOURCE_FILE_SHA)
    def test_009_authority_id(self): self.assertEqual(self.params["authority"]["selected_id_mm"], 10.2)
    def test_010_authority_od(self): self.assertEqual(self.params["authority"]["selected_od_mm"], 13.8)
    def test_011_no_conflict(self): self.assertFalse(self.params["authority"]["conflicting_current_dimensions"])
    def test_012_t0p5(self): self.assertEqual(b.ring(0.5).BoundingBox().zlen, 0.5)
    def test_013_t1p0(self): self.assertEqual(b.ring(1.0).BoundingBox().zlen, 1.0)
    def test_014_only_thickness_delta(self): self.assertTrue(math.isclose(b.ring(1.0).Volume(), 2 * b.ring(0.5).Volume(), rel_tol=1e-8))
    def test_015_single_solids(self): self.assertEqual([len(b.ring(t).Solids()) for t in b.THICKNESSES], [1, 1])
    def test_016_planar_square_edges(self): self.assertEqual(self.params["candidates"][0]["edge_break_mm"], 0.0)
    def test_017_features_absent(self): self.assertEqual(len(self.params["features_absent"]), 6)
    def test_018_six_test_copies(self): self.assertEqual(len(b.test_plate().Solids()), 6)
    def test_019_rotating_stack(self): self.assertIn("BEARING_INNER_RING", self.params["stack"]["contact"])
    def test_020_stationary_prohibited(self): self.assertEqual(len(self.params["stack"]["stationary_contacts_prohibited"]), 4)
    def test_021_contact_face_pending(self): self.assertEqual(self.params["stack"]["exact_contact_face"], "PHYSICAL_CONTACT_FACE_PENDING")
    def test_022_stationary_intersections_zero(self):
        for row in self.collision["checks"].values():
            self.assertEqual(row["bearing_outer_ring_intersection_mm3"], 0.0)
            self.assertEqual(row["kp000_housing_intersection_mm3"], 0.0)
            self.assertEqual(row["stationary_bracket_intersection_mm3"], 0.0)
            self.assertEqual(row["frame_intersection_mm3"], 0.0)
            self.assertEqual(row["crawler_intersection_mm3"], 0.0)
    def test_023_intended_faces_touch_without_volume_overlap(self):
        for row in self.collision["checks"].values():
            self.assertEqual(row["bearing_inner_ring_intersection_mm3"], 0.0)
            self.assertEqual(row["bearing_inner_ring_face_contact_distance_mm"], 0.0)
            self.assertEqual(row["pulley_intersection_mm3"], 0.0)
            self.assertEqual(row["pulley_face_contact_distance_mm"], 0.0)
    def test_024_shaft_path_clear(self):
        for row in self.collision["checks"].values():
            self.assertEqual(row["shaft_intersection_mm3"], 0.0)
            self.assertGreaterEqual(row["shaft_radial_clearance_mm"], 0.099)
    def test_025_petg_not_final(self): self.assertEqual(self.params["print"]["material_candidate"], "PETG_PROTOTYPE_ONLY")
    def test_026_flat_print(self): self.assertEqual(self.params["print"]["orientation"], "FLAT_ON_BUILD_PLATE_AXIS_VERTICAL")
    def test_027_elephant_foot_not_cad(self): self.assertEqual(self.params["print"]["cad_id_authority"], "UNCHANGED")
    def test_028_front_not_changed(self): self.assertFalse(self.params["stack"]["front_v002_changed"])
    def test_029_validation_all_pass(self): self.assertEqual(self.report["contract_fail_count"], 0)
    def test_030_status(self): self.assertEqual(self.report["status"], b.STATUS)
    def test_031_step_reload(self):
        self.assertEqual(len(self.report["quality"]["steps"]), 3)
        self.assertTrue(all(x["valid"] and x["solid_count"] > 0 for x in self.report["quality"]["steps"]))
    def test_032_stl_quality(self):
        self.assertEqual(len(self.report["quality"]["stls"]), 3)
        for row in self.report["quality"]["stls"]:
            self.assertTrue(row["watertight"] and row["manifold"])
            self.assertEqual(row["bad_edges"], 0)
            self.assertEqual(row["degenerate_triangles"], 0)
    def test_033_exact_paths(self):
        actual = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        self.assertEqual(actual, b.ALL_PATHS)
    def test_034_commit_paths(self):
        rows = [x for x in (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines() if x]
        self.assertEqual(len(rows), len(b.ALL_PATHS))
        self.assertEqual(len(rows), len(set(rows)))
    def test_035_holds(self): self.assertIn("PTO_SPACER_PHYSICAL_AUTHORITY_PENDING", self.params["holds"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
