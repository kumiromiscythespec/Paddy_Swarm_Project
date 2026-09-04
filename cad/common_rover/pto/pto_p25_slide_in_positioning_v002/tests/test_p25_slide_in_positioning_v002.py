"""Fail-closed contract for P25 Slide-In Positioning Block V002."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import time
import unittest


LANE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("p25_slide_builder", LANE / "build_p25_slide_in_positioning_v002.py")
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = b.audit()
        cls.quality = b.inspect(LANE)
        cls.validation = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.parameters = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))

    def test_001_repository(self): self.assertEqual(Path(self.audit["repository"]), b.ROOT)
    def test_002_branch(self): self.assertEqual(self.audit["branch"], b.BRANCH)
    def test_003_head(self): self.assertEqual(self.audit["head"], b.HEAD)
    def test_004_staged_zero(self): self.assertEqual(self.audit["staged_count"], 0)
    def test_005_dirty_preserved(self): self.assertEqual(self.audit["tracked_dirty_count"], 4)
    def test_006_outside_untracked_preserved(self): self.assertEqual(self.audit["outside_untracked_count"], 4406)
    def test_007_protected_zero_change(self): self.assertEqual(self.audit["protected_source_changed_count"], 0)
    def test_008_parent_protected(self): self.assertIn(b.PARENT_REL, self.audit["protected"])
    def test_009_parent_file_count(self): self.assertEqual(self.audit["protected"][b.PARENT_REL]["files"], 51)
    def test_010_exact_paths(self):
        current = sorted(p.relative_to(LANE).as_posix() for p in LANE.rglob("*") if p.is_file())
        finalize_outputs = {"COMMIT_PATHS.txt", "SHA256SUMS.txt", "contract_test_report.json",
                            "repository_audit.json", "manifest.json"}
        self.assertIn(current, [b.EXPECTED, sorted(set(b.EXPECTED) - finalize_outputs)])
    def test_011_exact_path_count(self): self.assertEqual(len(b.EXPECTED), 36)
    def test_012_slot_entrance(self): self.assertAlmostEqual(b.SLOT["entrance_width_mm"], 6.4, 9)
    def test_013_slot_internal(self): self.assertAlmostEqual(b.SLOT["maximum_internal_width_mm"], 10.8, 9)
    def test_014_slot_depth(self): self.assertAlmostEqual(b.SLOT["surface_to_bottom_depth_mm"], 6.4, 9)
    def test_015_slot_class(self): self.assertEqual(b.SLOT["measurement_class"], "PHYSICAL_DIRECT")
    def test_016_lip_partial(self): self.assertEqual(b.SLOT["lip_profile"], "PHYSICAL_PARTIAL")
    def test_017_head_thickness(self): self.assertAlmostEqual(b.HEAD_THICKNESS, 2.0, 9)
    def test_018_lead_in(self): self.assertAlmostEqual(b.LEAD_IN, 0.4, 9)
    def test_019_coupon_length(self): self.assertTrue(20 <= b.COUPON_LENGTH <= 30)
    def test_020_p25_exact(self): self.assertAlmostEqual(self.quality["actual_geometry"]["P25"]["working_dimension_mm"], 25.0, 6)
    def test_021_p25_datums(self): self.assertEqual(self.quality["actual_geometry"]["P25"]["datum_x_mm"], [0.0, 25.0])
    def test_022_p25_parallel(self): self.assertTrue(self.quality["actual_geometry"]["P25"]["parallel"])
    def test_023_p25_planar(self): self.assertTrue(self.quality["actual_geometry"]["P25"]["planar"])
    def test_024_provisional_b(self): self.assertEqual(self.parameters["geometry"]["p25"]["tongue_variant"], "B_PROVISIONAL")
    def test_025_p25_tongue_full_length(self): self.assertAlmostEqual(self.quality["actual_geometry"]["P25"]["engagement_length_mm"], 25.0, 6)
    def test_026_structural_pending(self): self.assertEqual(self.parameters["classification"]["structural_load_authority"], "PENDING")
    def test_027_primary_function(self): self.assertEqual(self.parameters["classification"]["primary_function"], "POSITIONING_ASSEMBLY_GAUGE")
    def test_028_fit_pending(self): self.assertEqual(self.parameters["physical_fit"], "PENDING")
    def test_029_powered_not_approved(self): self.assertEqual(self.parameters["powered"], "NOT_APPROVED")
    def test_030_support_off(self): self.assertEqual(self.parameters["geometry"]["print"]["support"], "OFF")
    def test_031_petg(self): self.assertEqual(self.parameters["geometry"]["print"]["material"], "PETG")
    def test_032_bambu_a1(self): self.assertEqual(self.parameters["geometry"]["print"]["printer"], "BAMBU_A1")
    def test_033_critical_xy(self): self.assertEqual(self.parameters["geometry"]["print"]["critical_dimensions"], "XY")
    def test_034_slicer_hold(self): self.assertEqual(self.parameters["geometry"]["print"]["slicer"], "HOLD_SLICER_NOT_RUN")
    def test_035_no_combined_plate(self): self.assertFalse(self.parameters["geometry"]["combined_plate_generated"])
    def test_036_step_count(self): self.assertEqual(len(self.quality["step"]), 6)
    def test_037_stl_count(self): self.assertEqual(len(self.quality["stl"]), 4)
    def test_038_svg_count(self): self.assertEqual(len(b.SVGS), 7)
    def test_039_drift_rows(self): self.assertEqual(len(self.validation["systematic_drift_regression"]), 3)
    def test_040_drift_rejected(self): self.assertTrue(all(r["systematic_plus_0p10_mm_rejected"] for r in self.validation["systematic_drift_regression"]))
    def test_041_repro_count(self): self.assertEqual(self.validation["reproducibility"]["count"], 17)
    def test_042_repro_pass(self): self.assertTrue(self.validation["reproducibility"]["pass"])
    def test_043_parent_selection(self): self.assertEqual(self.parameters["source"]["p25_selection"], "CURRENT_SELECTED_CANDIDATE")
    def test_044_p25_physical_spacing(self): self.assertEqual(self.parameters["source"]["physical_observations"]["p25_kp000_to_60t_edge_spacing_mm_approx"], 9.0)
    def test_045_p20_comparison(self): self.assertEqual(self.parameters["source"]["physical_observations"]["p20_kp000_to_60t_edge_spacing_mm_approx"], 4.0)
    def test_046_p25_gain(self): self.assertEqual(self.parameters["source"]["physical_observations"]["p25_additional_spacing_vs_p20_mm_approx"], 5.0)
    def test_047_pulley_physical(self): self.assertEqual(self.parameters["source"]["physical_observations"]["60t_rotating_max_mm"], [100.1, 100.2])
    def test_048_pto_axis_datum(self): self.assertEqual(self.parameters["source"]["physical_observations"]["pto_axis_from_local_member_end_mm"], 34.0)


def _make_variant_test(letter, field, expected, index):
    def test(self):
        self.assertAlmostEqual(self.quality["actual_geometry"][letter][field], expected, places=6)
    test.__name__ = f"test_{index:03d}_{letter.lower()}_{field}"
    return test


counter = 49
for candidate, values in b.VARIANTS.items():
    for field, key in [("stem_width_mm", "stem_width_mm"),
                       ("head_width_mm", "head_width_mm"),
                       ("total_insertion_depth_mm", "depth_mm")]:
        setattr(Contract, f"test_{counter:03d}_{candidate.lower()}_{field}",
                _make_variant_test(candidate, field, values[key], counter))
        counter += 1


def _make_clearance_test(letter, field, expected, index):
    def test(self): self.assertAlmostEqual(b.clearances(letter)[field], expected, places=6)
    return test


for candidate, bottom in [("A", 0.6), ("B", 0.5), ("C", 0.4)]:
    setattr(Contract, f"test_{counter:03d}_{candidate.lower()}_bottom_clearance",
            _make_clearance_test(candidate, "bottom_clearance_mm", bottom, counter)); counter += 1
    setattr(Contract, f"test_{counter:03d}_{candidate.lower()}_capture",
            _make_clearance_test(candidate, "vertical_capture_overhang_per_side_mm", 2.1, counter)); counter += 1


def _make_step_test(path, index):
    def test(self): self.assertEqual(self.quality["step"][path]["reload"], "PASS")
    return test


for path in b.STEPS:
    setattr(Contract, f"test_{counter:03d}_step_{Path(path).stem}", _make_step_test(path, counter)); counter += 1


def _make_stl_test(path, field, index):
    def test(self): self.assertTrue(self.quality["stl"][path][field])
    return test


for path in b.STLS:
    for field in ("watertight", "manifold", "pass"):
        setattr(Contract, f"test_{counter:03d}_{Path(path).stem}_{field}", _make_stl_test(path, field, counter)); counter += 1


if __name__ == "__main__":
    started = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "pass": result.wasSuccessful(), "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "duration_seconds": round(time.perf_counter() - started, 3),
        "status": b.STATUS if result.wasSuccessful() else "CONTRACT_FAIL",
    }
    print(json.dumps(report, indent=2))
    if result.wasSuccessful():
        b.finalize(report)
    raise SystemExit(0 if result.wasSuccessful() else 1)
