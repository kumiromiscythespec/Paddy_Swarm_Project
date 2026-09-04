#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract tests for the v0.9.6.29 P20653 / 18025 keyed-hub DRIVE lane."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import unittest


LANE = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "v0.9.6.29"
EXPECTED_CLASSIFICATION = "P20653_18025_KEYED_HUB_DRIVE"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
EXPECTED_PATH_COUNT = 55
EXPECTED_TEST_COUNT = 180


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
            value, rel = row.split("  ", 1)
            cls.sums[rel] = value
        cls.report = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.params = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))


def add_path_tests() -> None:
    path = LANE / "MANIFEST.txt"
    manifest = sorted(path.read_text(encoding="utf-8").splitlines()) if path.exists() else []
    for index, rel in enumerate(manifest, 1):
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


def core_tests() -> list[tuple[str, object]]:
    return [
        ("version", lambda s: s.assertEqual(s.report["version"], EXPECTED_VERSION)),
        ("classification", lambda s: s.assertEqual(s.report["classification"], EXPECTED_CLASSIFICATION)),
        ("status", lambda s: s.assertIn("P20653_18025_KEYED_HUB_DRIVE_CAD_COMPLETE", s.report["status"])),
        ("repository", lambda s: s.assertEqual(s.report["repository"]["repository"], r"D:\Paddy_Swarm_Project")),
        ("branch", lambda s: s.assertEqual(s.report["repository"]["branch"], EXPECTED_BRANCH)),
        ("head", lambda s: s.assertEqual(s.report["repository"]["head"], EXPECTED_HEAD)),
        ("staged", lambda s: s.assertEqual(s.report["repository"]["staged"], [])),
        ("tracked_dirty", lambda s: s.assertEqual(len(s.report["repository"]["tracked_dirty"]), 4)),
        ("outside_untracked", lambda s: s.assertEqual(s.report["repository"]["outside_untracked"][0], 2853)),
        ("authority", lambda s: s.assertTrue(s.report["repository"]["checks"]["authority_4_of_4"])),
        ("protected", lambda s: s.assertEqual(len(s.report["repository"]["protected_lanes"]), 28)),
        ("sources", lambda s: s.assertTrue(s.report["repository"]["checks"]["source_files"])),
        ("blocker", lambda s: s.assertEqual(s.report["geometry"]["development"]["target_blocker"], "BLOCKER_1_DRIVETRAIN_TORQUE_TRANSMISSION")),
        ("not_reopened", lambda s: s.assertEqual(len(s.report["geometry"]["development"]["not_reopened"]), 2)),
        ("dflat_rejected", lambda s: s.assertEqual(s.report["geometry"]["development"]["d_flat_set_screw_production_architecture"], "REJECTED")),
        ("p20653_class", lambda s: s.assertEqual(s.report["geometry"]["p20653"]["classification"], "P20653_PHYSICALLY_SUPPORTED_PRIMARY_CANDIDATE")),
        ("running_pitch_unknown", lambda s: s.assertEqual(s.report["geometry"]["p20653"]["running_pitch_final"], "UNKNOWN_REQUIRES_PHYSICAL_TEST")),
        ("pitch", lambda s: s.assertEqual(s.report["geometry"]["p20653"]["freeze"]["pitch_mm"], 20.6533333333)),
        ("pitch_diameter", lambda s: s.assertEqual(s.report["geometry"]["p20653"]["freeze"]["pitch_diameter_mm"], 79.79835226236546)),
        ("tooth_count", lambda s: s.assertEqual(s.report["geometry"]["p20653"]["freeze"]["tooth_count"], 12)),
        ("phase", lambda s: s.assertEqual(s.report["geometry"]["p20653"]["freeze"]["phase_deg"], 15.0)),
        ("spacing", lambda s: s.assertEqual(s.report["geometry"]["p20653"]["freeze"]["spacing_deg"], 30.0)),
        ("tooth_width", lambda s: s.assertEqual(s.report["geometry"]["p20653"]["freeze"]["tooth_axial_width_mm"], 44.0)),
        ("tooth_added_zero", lambda s: s.assertEqual(s.report["geometry"]["p20653"]["freeze"]["tooth_added_volume_mm3"], 0)),
        ("tooth_removed_zero", lambda s: s.assertEqual(s.report["geometry"]["p20653"]["freeze"]["tooth_removed_volume_mm3"], 0)),
        ("exact_outside", lambda s: s.assertTrue(s.report["geometry"]["p20653"]["freeze"]["exact_outside_envelope"])),
        ("axial_plane", lambda s: s.assertAlmostEqual(s.report["geometry"]["p20653"]["freeze"]["axial_center_shift_mm"], 0.0, places=6)),
        ("idler_files", lambda s: s.assertEqual(s.report["geometry"]["idler"]["modified_files"], 0)),
        ("idler_bearing", lambda s: s.assertEqual(s.report["geometry"]["idler"]["bearing"], "6000-2RS")),
        ("idler_duplicate", lambda s: s.assertEqual(s.report["geometry"]["idler"]["artifact_duplication"], 0)),
        ("vendor_authority", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["authority"], "VENDOR_DRAWING_AUTHORITY")),
        ("vendor_delivery", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["order_delivery"], "PENDING")),
        ("vendor_physical_fit", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["physical_fit"], "NOT_YET")),
        ("vendor_bore", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["bore_mm"], 10.0)),
        ("vendor_keyway", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["keyway_width_mm_class"], 3.0)),
        ("vendor_flange", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["flange_od_mm"], 56.8)),
        ("vendor_pcd", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["pcd_mm"], 47.5)),
        ("vendor_hole_count", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["hole_count"], 6)),
        ("vendor_hole_diameter", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["hole_diameter_mm_class"], 5.2)),
        ("vendor_boss", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["boss_od_mm_class"], 24.0)),
        ("vendor_width", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["overall_width_mm_class"], 26.4)),
        ("vendor_flange_thickness", lambda s: s.assertEqual(s.report["geometry"]["vendor_18025"]["flange_thickness_mm_class"], 6.0)),
        ("proxy_status", lambda s: s.assertEqual(s.report["geometry"]["proxy_18009"]["status"], "18025_FLANGE_INTERFACE_PROXY_ONLY")),
        ("proxy_flange", lambda s: s.assertEqual(s.report["geometry"]["proxy_18009"]["vendor_common_interface"]["flange_od_mm"], 56.8)),
        ("proxy_pcd", lambda s: s.assertEqual(s.report["geometry"]["proxy_18009"]["vendor_common_interface"]["pcd_mm"], 47.5)),
        ("proxy_forbidden", lambda s: s.assertIn("KEYED_DRIVETRAIN_TORQUE_PASS", s.report["geometry"]["proxy_18009"]["forbidden"])),
        ("pilots", lambda s: s.assertEqual(list(s.report["geometry"]["interface"]["pilot_candidates_mm"].values()), [24.1, 24.2, 24.3])),
        ("primary_pilot", lambda s: s.assertEqual(s.report["geometry"]["interface"]["provisional_primary_pilot_mm"], 24.2)),
        ("petg_hole", lambda s: s.assertEqual(s.report["geometry"]["interface"]["petg_hole_diameter_mm"], 5.5)),
        ("six_centers", lambda s: s.assertEqual(len(s.report["geometry"]["interface"]["hole_centers"]), 6)),
        ("angular_spacing", lambda s: s.assertEqual(s.report["geometry"]["interface"]["angular_spacing_deg"], 60.0)),
        ("center_radii", lambda s: [s.assertAlmostEqual(math.hypot(row["x_mm"], row["y_mm"]), 23.75, places=9) for row in s.report["geometry"]["interface"]["hole_centers"]]),
        ("washer_land", lambda s: s.assertGreaterEqual(s.report["geometry"]["interface"]["washer_seat_diameter_mm"], 10.0)),
        ("web_candidates", lambda s: s.assertEqual(s.report["geometry"]["web"]["thickness_candidates_mm"], [8.0, 9.0, 10.0])),
        ("web_selected", lambda s: s.assertEqual(s.report["geometry"]["web"]["selected_provisional_thickness_mm"], 10.0)),
        ("ligament", lambda s: s.assertGreaterEqual(s.report["geometry"]["web"]["minimum_hole_free_edge_ligament_mm"], 5.0)),
        ("root_fillet", lambda s: s.assertGreaterEqual(s.report["geometry"]["web"]["root_transition_fillet_mm"], 3.0)),
        ("continuous_web", lambda s: (s.assertTrue(s.report["geometry"]["web"]["continuous_web"]), s.assertEqual(s.report["geometry"]["web"]["isolated_bolt_tabs"], 0))),
        ("old_counts", lambda s: (s.assertEqual(s.report["geometry"]["architecture"]["reaction_shoe_count"], 0), s.assertEqual(s.report["geometry"]["architecture"]["shaft_collar_torque_receiver_count"], 0), s.assertEqual(s.report["geometry"]["architecture"]["petg_shaft_clamp_count"], 0))),
        ("torque_path", lambda s: (s.assertIn("SIX_FLANGE_BOLTS", s.report["geometry"]["architecture"]["torque_path"]), s.assertIn("3MM_KEY", s.report["geometry"]["architecture"]["torque_path"]))),
        ("collar_axial_only", lambda s: s.assertEqual(s.report["geometry"]["architecture"]["shaft_collars_future_role"], "AXIAL_POSITIONING_ONLY")),
        ("torque_resultant", lambda s: s.assertAlmostEqual(s.report["geometry"]["torque_reference"]["tangential_resultant_n"], 6.5 / 0.02375, places=12)),
        ("bolt_share", lambda s: s.assertAlmostEqual(s.report["geometry"]["torque_reference"]["ideal_equal_share_per_fastener_n"], 6.5 / 0.02375 / 6.0, places=12)),
        ("meshes", lambda s: s.assertTrue(all(row["watertight"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 and row["reload"] == "PASS" for row in s.report["mesh"].values()))),
        ("steps", lambda s: s.assertTrue(all(row["valid"] and row["reload"] == "PASS" for row in s.report["step_import"].values()))),
        ("cad_state", lambda s: s.assertEqual(s.report["geometry"]["state_matrix"]["CAD_PASS"], "PASS")),
        ("fit_not_yet", lambda s: s.assertEqual(s.report["geometry"]["state_matrix"]["FIT_PASS"], "NOT_YET")),
        ("field_not_yet", lambda s: s.assertEqual(s.report["geometry"]["state_matrix"]["FIELD_PASS"], "NOT_YET")),
        ("purchase_candidates", lambda s: (s.assertIn("PURCHASE_CANDIDATE", s.report["geometry"]["purchase_candidates"]["shaft"]), s.assertIn("PURCHASE_CANDIDATE", s.report["geometry"]["purchase_candidates"]["key"]))),
        ("first_print", lambda s: s.assertIn("FIRST PRINT=coupon", (LANE / "PRINT_PLAN.md").read_text(encoding="utf-8"))),
        ("final_status", lambda s: (s.assertIn("18025_PHYSICAL_FIT_NOT_YET", s.report["status"]), s.assertIn("POWERED_KEYED_DRIVE_NOT_APPROVED", s.report["status"]))),
    ]


add_path_tests()
add_sha_tests()
for offset, (label, func) in enumerate(core_tests(), 110):
    setattr(Contract, f"test_{offset:03d}_{label}", func)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    count = suite.countTestCases()
    if count != EXPECTED_TEST_COUNT:
        raise SystemExit(f"contract count {count} != {EXPECTED_TEST_COUNT}")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"CONTRACT_COUNT={count}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
