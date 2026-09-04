#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract tests for Common Rover P20653 14T / 18025 v0.9.6.30."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import unittest


LANE = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "v0.9.6.30"
EXPECTED_CLASSIFICATION = "P20653_14T_18025_FULL_WIDTH_THROUGH_BOLT_DRIVE"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
EXPECTED_PATH_COUNT = 69


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_")


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
        cls.sums = {}
        for row in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            digest, rel = row.split("  ", 1)
            cls.sums[rel] = digest
        cls.report = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.params = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
        cls.geom = cls.report["geometry"]


def add_path_tests() -> None:
    path = LANE / "MANIFEST.txt"
    rows = sorted(path.read_text(encoding="utf-8").splitlines()) if path.exists() else []
    for index, rel in enumerate(rows, 1):
        def check(self: Contract, item: str = rel) -> None:
            self.assertTrue((LANE / item).is_file(), item)
        setattr(Contract, f"test_{index:03d}_path_{safe_name(rel)}", check)


def add_sha_tests() -> None:
    path = LANE / "SHA256SUMS.txt"
    rows = [row.split("  ", 1)[1] for row in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
    for offset, rel in enumerate(sorted(rows), EXPECTED_PATH_COUNT + 1):
        def check(self: Contract, item: str = rel) -> None:
            self.assertEqual(sha256(LANE / item), self.sums[item], item)
        setattr(Contract, f"test_{offset:03d}_sha_{safe_name(rel)}", check)


def core_tests():
    return [
        ("version", lambda s: s.assertEqual(s.report["version"], EXPECTED_VERSION)),
        ("classification", lambda s: s.assertEqual(s.report["classification"], EXPECTED_CLASSIFICATION)),
        ("status_complete", lambda s: s.assertIn("P20653_14T_18025_FULL_WIDTH_THROUGH_BOLT_DRIVE_CAD_COMPLETE", s.report["status"])),
        ("repo", lambda s: s.assertEqual(s.report["repository"]["repository"], r"D:\Paddy_Swarm_Project")),
        ("branch", lambda s: s.assertEqual(s.report["repository"]["branch"], EXPECTED_BRANCH)),
        ("head", lambda s: s.assertEqual(s.report["repository"]["head"], EXPECTED_HEAD)),
        ("staged_zero", lambda s: s.assertEqual(s.report["repository"]["staged"], [])),
        ("dirty_four", lambda s: s.assertEqual(len(s.report["repository"]["tracked_dirty"]), 4)),
        ("outside_untracked", lambda s: s.assertEqual(s.report["repository"]["outside_untracked"][0], 2908)),
        ("ignored_recorded", lambda s: s.assertGreaterEqual(s.report["repository"]["ignored_repository_count"], 0)),
        ("authority", lambda s: s.assertTrue(s.report["repository"]["checks"]["authority_4_of_4"])),
        ("protected_count", lambda s: s.assertEqual(len(s.report["repository"]["protected_lanes"]), 35)),
        ("protected_unchanged", lambda s: s.assertTrue(all(row["status"] == "UNCHANGED" for row in s.report["repository"]["protected_lanes"].values()))),
        ("source_files", lambda s: s.assertTrue(s.report["repository"]["checks"]["source_files"])),
        ("lane_cache_zero", lambda s: s.assertTrue(s.report["repository"]["checks"]["lane_cache_zero"])),
        ("lane_ignored_zero", lambda s: s.assertTrue(s.report["repository"]["checks"]["lane_ignored_zero"])),
        ("forbidden_zero", lambda s: s.assertTrue(s.report["repository"]["checks"]["forbidden_zero"])),
        ("pitch", lambda s: s.assertEqual(s.geom["p20653"]["pitch_mm"], 20.6533333333)),
        ("source_d12", lambda s: s.assertEqual(s.geom["p20653"]["source_12t_pitch_diameter_mm"], 79.79835226236546)),
        ("target_d14", lambda s: s.assertAlmostEqual(s.geom["p20653"]["target_14t_pitch_diameter_mm"], 20.6533333333 / math.sin(math.pi / 14), places=12)),
        ("radial_increase", lambda s: s.assertAlmostEqual(s.geom["p20653"]["pitch_radius_increase_mm"], (s.geom["p20653"]["target_14t_pitch_diameter_mm"] - 79.79835226236546) / 2, places=12)),
        ("tooth_count", lambda s: s.assertEqual(s.geom["p20653"]["tooth_count"], 14)),
        ("spacing", lambda s: s.assertAlmostEqual(s.geom["p20653"]["spacing_deg"], 360 / 14, places=12)),
        ("phase", lambda s: s.assertAlmostEqual(s.geom["p20653"]["phase_deg"], 180 / 14, places=12)),
        ("phase_rule", lambda s: s.assertEqual(s.geom["p20653"]["phase_derivation"], "HALF_OF_TOOTH_SPACING")),
        ("width", lambda s: s.assertEqual(s.geom["p20653"]["tooth_width_mm"], 44.0)),
        ("chord", lambda s: s.assertAlmostEqual(s.geom["p20653"]["adjacent_pitch_chord_mm"], 20.6533333333, places=9)),
        ("scale_one", lambda s: s.assertEqual(s.geom["p20653"]["regression"]["scale_factor"], 1.0)),
        ("rigid_only", lambda s: s.assertEqual(s.geom["p20653"]["regression"]["operation"], "RIGID_ROTATION_PLUS_TRANSLATION_ONLY")),
        ("regression_14", lambda s: s.assertEqual(len(s.geom["p20653"]["regression"]["rows"]), 14)),
        ("regression_all", lambda s: s.assertTrue(s.geom["p20653"]["regression"]["all_14_pass"])),
        ("added_zero", lambda s: s.assertLessEqual(s.geom["p20653"]["regression"]["max_added_volume_mm3"], 1e-5)),
        ("removed_zero", lambda s: s.assertLessEqual(s.geom["p20653"]["regression"]["max_removed_volume_mm3"], 1e-5)),
        ("vendor_authority", lambda s: s.assertIn("VSTONE_VENDOR_DRAWING_AUTHORITY", s.geom["vendor_18025"]["authority"])),
        ("flange_od", lambda s: s.assertEqual(s.geom["vendor_18025"]["flange_od_mm"], 56.8)),
        ("boss_od", lambda s: s.assertEqual(s.geom["vendor_18025"]["boss_od_mm"], 24.0)),
        ("overall_width", lambda s: s.assertEqual(s.geom["vendor_18025"]["overall_width_mm"], 26.4)),
        ("flange_thickness", lambda s: s.assertEqual(s.geom["vendor_18025"]["flange_thickness_mm"], 6.0)),
        ("boss_projection", lambda s: s.assertEqual(s.geom["vendor_18025"]["derived_boss_projection_mm"], 20.4)),
        ("bore", lambda s: s.assertEqual(s.geom["vendor_18025"]["bore_mm"], 10.0)),
        ("bore_tol", lambda s: s.assertEqual(s.geom["vendor_18025"]["bore_tolerance_mm"], [0.0, 0.02])),
        ("pcd", lambda s: s.assertEqual(s.geom["vendor_18025"]["pcd_mm"], 47.5)),
        ("vendor_holes", lambda s: (s.assertEqual(s.geom["vendor_18025"]["mounting_holes"], 6), s.assertEqual(s.geom["vendor_18025"]["mounting_hole_mm"], 5.2))),
        ("keyway", lambda s: s.assertEqual(s.geom["vendor_18025"]["keyway_width_mm"], 3.0)),
        ("raw_11p4", lambda s: s.assertEqual(s.geom["vendor_18025"]["raw_11p4_dimension_mm"], 11.4)),
        ("derived_firewall", lambda s: s.assertEqual(s.geom["vendor_18025"]["derived_keyway_reference_authority"], "DERIVED_VENDOR_DRAWING_REFERENCE")),
        ("physical_not_yet", lambda s: s.assertEqual(s.geom["vendor_18025"]["physical_measured"], "NOT_YET")),
        ("set_screw_hold", lambda s: s.assertEqual(s.geom["vendor_18025"]["set_screw_exact_position"], "PHYSICAL_HOLD")),
        ("set_screw_prohibited", lambda s: s.assertEqual(s.geom["vendor_18025"]["set_screw_torque_path"], "PROHIBITED")),
        ("proxy_role", lambda s: s.assertEqual(s.geom["proxy_18009"]["role"], "18025_FLANGE_INTERFACE_PROXY_ONLY")),
        ("proxy_all_pass", lambda s: s.assertIn("ALL_HAND_INSERTION", s.geom["proxy_18009"]["P241_P242_P243"])),
        ("p241", lambda s: (s.assertEqual(s.geom["proxy_18009"]["selected_center_pilot"], "P241"), s.assertEqual(s.geom["proxy_18009"]["center_pilot_d_mm"], 24.1))),
        ("one_hub", lambda s: s.assertEqual(s.geom["architecture"]["hub_count_per_drive"], 1)),
        ("two_total", lambda s: s.assertEqual(s.geom["architecture"]["total_18025_required"], 2)),
        ("idler_no_hub", lambda s: s.assertEqual(s.geom["architecture"]["idler_18025_count"], 0)),
        ("sandwich_prohibited", lambda s: s.assertEqual(s.geom["architecture"]["dual_18025_sandwich"], "PROHIBITED")),
        ("fastener", lambda s: s.assertIn("METAL_LOCKNUT", s.geom["architecture"]["fastener"])),
        ("bolt_direction", lambda s: s.assertIn("HEAD_AT_18025", s.geom["architecture"]["bolt_direction"])),
        ("petg_tap_prohibited", lambda s: s.assertEqual(s.geom["architecture"]["petg_tapped_primary_thread"], "PROHIBITED")),
        ("pockets", lambda s: s.assertEqual(s.geom["recess"]["flange_pocket_candidates_mm"], {"F569": 56.9, "F570": 57.0, "F571": 57.1})),
        ("pocket_depth", lambda s: s.assertEqual(s.geom["recess"]["flange_pocket_depth_mm"], 6.2)),
        ("pilot_length", lambda s: s.assertEqual(s.geom["recess"]["center_pilot_length_mm"], 4.0)),
        ("deep_relief", lambda s: s.assertEqual(s.geom["recess"]["deep_relief_d_mm"], 24.5)),
        ("cavity_depth", lambda s: s.assertEqual(s.geom["recess"]["total_cavity_depth_mm"], 26.8)),
        ("flange_datum", lambda s: s.assertIn("FLANGE_SEAT", s.geom["recess"]["axial_datum"])),
        ("drain", lambda s: s.assertEqual(s.geom["recess"]["drain_d_mm"], 3.0)),
        ("support_type", lambda s: s.assertIn("CONTINUOUS_RING", s.geom["support"]["support_type"])),
        ("support_width", lambda s: s.assertEqual(s.geom["support"]["width_mm"], 44.0)),
        ("root_fillets", lambda s: s.assertGreaterEqual(s.geom["support"]["root_transition_fillet_mm"], 3.0)),
        ("link_source", lambda s: s.assertEqual(s.geom["support"]["link_source_sha256"], "eb21877913a281b17d080a178fbb5b916384c29504ba1e16a188e90c85f49c6a")),
        ("link_intersection_zero", lambda s: s.assertEqual(s.geom["support"]["noncontact_ring_intersection_max_mm3"], 0)),
        ("link_clearance_hard", lambda s: s.assertGreaterEqual(s.geom["support"]["noncontact_ring_clearance_mm"], 0.8)),
        ("link_target_honest", lambda s: s.assertEqual(s.geom["support"]["clearance_result"], "HARD_PASS_TARGET_MISS")),
        ("ring_ligament_hard", lambda s: s.assertGreaterEqual(s.geom["radial_margin"]["continuous_ring_ligament_mm"], 5.0)),
        ("margin_improved", lambda s: s.assertGreater(s.geom["radial_margin"]["v09630_14t_flange_to_tooth_root_mm"], s.geom["radial_margin"]["v09629_12t_flange_to_tooth_root_mm"])),
        ("idler_12", lambda s: s.assertEqual(s.geom["idler"]["tooth_count"], 12)),
        ("idler_change_zero", lambda s: s.assertEqual(s.geom["idler"]["change_count"], 0)),
        ("link_count", lambda s: s.assertEqual(s.geom["loop"]["current_link_count"], 40)),
        ("center_distance", lambda s: s.assertEqual(s.geom["loop"]["current_center_distance_mm"], 280.0)),
        ("stroke_candidate", lambda s: s.assertEqual(s.geom["loop"]["source_tension_stroke_candidate_mm"], 12.0)),
        ("real_stroke_hold", lambda s: s.assertIn("HOLD", s.geom["loop"]["physical_available_tensioner_stroke"])),
        ("loop_three", lambda s: s.assertEqual(len(s.geom["loop"]["rows"]), 3)),
        ("same_count_practical_candidate", lambda s: s.assertTrue(s.geom["loop"]["rows"][0]["practical_with_candidate_12mm_stroke"])),
        ("plus_one_not_practical", lambda s: s.assertFalse(s.geom["loop"]["rows"][1]["practical_with_candidate_12mm_stroke"])),
        ("plus_two_not_practical", lambda s: s.assertFalse(s.geom["loop"]["rows"][2]["practical_with_candidate_12mm_stroke"])),
        ("loop_print_hold", lambda s: s.assertIn("HOLD_REAL_AVAILABLE", s.geom["loop"]["print_gate"])),
        ("frame_hold", lambda s: s.assertIn("HOLD", s.geom["frame_clearance"]["result"])),
        ("roller_hold", lambda s: s.assertIn("HOLD", s.geom["roller_clearance"]["result"])),
        ("backing", lambda s: s.assertGreaterEqual(s.geom["hardware_stack"]["remaining_local_petg_backing_mm"], 10.0)),
        ("bolt_candidates", lambda s: s.assertEqual(s.geom["hardware_stack"]["bolt_candidates_mm"], [50, 55, 60])),
        ("hardware_hold", lambda s: s.assertEqual(s.geom["hardware_stack"]["final"], "PHYSICAL_HARDWARE_HOLD")),
        ("torque_reference", lambda s: s.assertAlmostEqual(s.geom["torque_reference"]["tangential_resultant_n"], 6.5 / 0.02375, places=12)),
        ("bolt_share", lambda s: s.assertAlmostEqual(s.geom["torque_reference"]["ideal_equal_share_per_fastener_n"], 6.5 / 0.02375 / 6, places=12)),
        ("speed_ratio", lambda s: s.assertAlmostEqual(s.geom["tradeoff"]["same_rpm_speed_ratio"], 14 / 12, places=12)),
        ("force_ratio", lambda s: s.assertAlmostEqual(s.geom["tradeoff"]["same_torque_ideal_force_ratio"], 12 / 14, places=12)),
        ("mesh_five", lambda s: s.assertEqual(len(s.report["mesh"]), 5)),
        ("mesh_all", lambda s: s.assertTrue(all(row["watertight"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 and row["reload"] == "PASS" for row in s.report["mesh"].values()))),
        ("step_two", lambda s: s.assertEqual(len(s.report["step_import"]), 2)),
        ("step_all", lambda s: s.assertTrue(all(row["valid"] and row["reload"] == "PASS" for row in s.report["step_import"].values()))),
        ("artifact_counts", lambda s: s.assertEqual(s.report["artifact_counts"], {"step": 2, "stl": 5, "svg": 16})),
        ("first_print", lambda s: s.assertIn("FIRST PRINT=`18025_flange_recess_triplet", (LANE / "PRINT_PLAN.md").read_text(encoding="utf-8"))),
        ("notch_rule", lambda s: (s.assertIn("F569=外周1 notch", (LANE / "MULTI_CANDIDATE_IDENTIFICATION_RULE.md").read_text(encoding="utf-8")), s.assertIn("F571=3 notch", (LANE / "MULTI_CANDIDATE_IDENTIFICATION_RULE.md").read_text(encoding="utf-8")))),
        ("cad_pass", lambda s: s.assertEqual(s.geom["state_matrix"]["CAD_PASS"], "PASS")),
        ("print_not_yet", lambda s: s.assertEqual(s.geom["state_matrix"]["PRINT_PASS"], "NOT_YET")),
        ("fit_not_yet", lambda s: s.assertIn("NOT_YET", s.geom["state_matrix"]["FIT_PASS"])),
        ("powered_not_yet", lambda s: s.assertEqual(s.geom["state_matrix"]["POWERED_PASS"], "NOT_YET")),
        ("field_not_yet", lambda s: s.assertEqual(s.geom["state_matrix"]["FIELD_PASS"], "NOT_YET")),
        ("physical_unknown", lambda s: s.assertEqual(s.report["physical_classification"], "UNKNOWN_REQUIRES_PHYSICAL_TEST")),
        ("commit_paths", lambda s: s.assertEqual(len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()), EXPECTED_PATH_COUNT)),
    ]


add_path_tests()
add_sha_tests()
CORE = core_tests()
for offset, (label, func) in enumerate(CORE, EXPECTED_PATH_COUNT * 2):
    setattr(Contract, f"test_{offset:03d}_{label}", func)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    expected = EXPECTED_PATH_COUNT + (EXPECTED_PATH_COUNT - 1) + len(CORE)
    count = suite.countTestCases()
    if count != expected:
        raise SystemExit(f"contract count {count} != {expected}")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"CONTRACT_COUNT={count}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
