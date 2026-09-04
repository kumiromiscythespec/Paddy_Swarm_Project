#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract tests for v0.9.6.26 dual shaft-collar TEMP HTD5M 60T."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


LANE = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "v0.9.6.26"
EXPECTED_CLASSIFICATION = "TEMP_HTD5M_60T_DUAL_SHAFT_COLLAR_EMBEDDED_M4"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
EXPECTED_PATH_COUNT = 45
EXPECTED_TEST_COUNT = 140


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
        ("status", lambda s: s.assertIn("DUAL_METAL_SHAFT_COLLAR_ARCHITECTURE_COMPLETE", s.report["status"])),
        ("repository", lambda s: s.assertEqual(s.report["repository"]["repository"], r"D:\Paddy_Swarm_Project")),
        ("branch", lambda s: s.assertEqual(s.report["repository"]["branch"], EXPECTED_BRANCH)),
        ("head", lambda s: s.assertEqual(s.report["repository"]["head"], EXPECTED_HEAD)),
        ("staged", lambda s: s.assertEqual(s.report["repository"]["staged"], [])),
        ("tracked_dirty", lambda s: s.assertEqual(len(s.report["repository"]["tracked_dirty"]), 4)),
        ("outside_untracked", lambda s: s.assertEqual(s.report["repository"]["outside_untracked"][0], 2708)),
        ("authority", lambda s: s.assertTrue(s.report["repository"]["checks"]["authority_4_of_4"])),
        ("protected", lambda s: s.assertEqual(len(s.report["repository"]["protected_lanes"]), 12)),
        ("parent_v25", lambda s: s.assertTrue(s.report["repository"]["checks"]["parent_v09625"])),
        ("source", lambda s: s.assertEqual(s.report["repository"]["source_sha256"], "bc3e00bca0db5fe4c3975b5904ad4f72faa2b3fe6822057522c12df16ec0d256")),
        ("collar_od", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["collar_od_mm"], 15.8)),
        ("collar_width", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["collar_width_mm"], 5.8)),
        ("m4_head_od", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["m4_head_od_mm"], 8.8)),
        ("m4_projection", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["max_radial_projection_from_collar_outer_to_head_top_mm"], 11.0)),
        ("shaft", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["shaft_nominal_mm"], 10.0)),
        ("collar_count", lambda s: s.assertEqual(s.report["geometry"]["architecture"]["metal_shaft_collars"], 2)),
        ("m4_each", lambda s: s.assertEqual(s.report["geometry"]["architecture"]["m4_per_collar"], 2)),
        ("m4_total", lambda s: s.assertEqual(s.report["geometry"]["architecture"]["total_m4"], 4)),
        ("cover_zero", lambda s: s.assertEqual(s.report["geometry"]["architecture"]["cover"], 0)),
        ("shoe_zero", lambda s: s.assertEqual(s.report["geometry"]["architecture"]["reaction_shoe"], 0)),
        ("split_zero", lambda s: (s.assertEqual(s.report["geometry"]["architecture"]["petg_split_clamp"], 0), s.assertEqual(s.report["geometry"]["architecture"]["continuous_1_3mm_split"], 0))),
        ("ear_zero", lambda s: s.assertEqual(s.report["geometry"]["architecture"]["external_petg_clamp_ears"], 0)),
        ("pocket_candidates", lambda s: s.assertEqual(s.report["geometry"]["hub"]["collar_pocket_candidates_mm"], [16.0, 16.2, 16.4])),
        ("primary_pocket", lambda s: s.assertEqual(s.report["geometry"]["hub"]["primary_collar_pocket_mm"], 16.2)),
        ("pocket_depth", lambda s: s.assertEqual(s.report["geometry"]["hub"]["collar_pocket_depth_mm"], 5.5)),
        ("proud", lambda s: s.assertEqual(s.report["geometry"]["hub"]["collar_proud_mm"], 0.3)),
        ("guide_candidates", lambda s: s.assertEqual(s.report["geometry"]["hub"]["guide_bore_candidates_mm"], [10.1, 10.2, 10.3])),
        ("guide_primary", lambda s: s.assertEqual(s.report["geometry"]["hub"]["primary_guide_bore_mm"], 10.2)),
        ("head_pocket", lambda s: (s.assertEqual(s.report["geometry"]["reaction"]["head_pocket_width_mm"], 9.5), s.assertEqual(s.report["geometry"]["reaction"]["head_radial_clearance_mm"], 0.35))),
        ("service", lambda s: (s.assertEqual(s.report["geometry"]["reaction"]["hardware_radial_envelope_mm"], 18.9), s.assertEqual(s.report["geometry"]["reaction"]["service_radial_envelope_mm"], 20.0))),
        ("hub_od", lambda s: s.assertEqual(s.report["geometry"]["hub"]["od_mm"], 50.0)),
        ("outer_ligament", lambda s: s.assertGreaterEqual(s.report["geometry"]["reaction"]["outer_ligament_mm"], 5.0)),
        ("shoulder", lambda s: s.assertGreaterEqual(s.report["geometry"]["reaction"]["reaction_shoulder_minimum_mm"], 5.0)),
        ("left_backlash", lambda s: s.assertLess(s.report["geometry"]["reaction"]["left_angular_backlash_estimate_deg"], 3.0)),
        ("right_backlash", lambda s: s.assertLess(s.report["geometry"]["reaction"]["right_angular_backlash_estimate_deg"], 3.0)),
        ("combined_backlash", lambda s: s.assertLess(s.report["geometry"]["reaction"]["combined_first_contact_estimate_deg"], 3.0)),
        ("differential", lambda s: s.assertLess(s.report["geometry"]["reaction"]["combined_worst_differential_phase_deg"], 6.0)),
        ("axial", lambda s: (s.assertEqual(s.report["geometry"]["axial_sandwich"]["cad_reference_axial_play_mm"], 0.0), s.assertIn("HOLD", s.report["geometry"]["axial_sandwich"]["preload"]))),
        ("torque_path", lambda s: (s.assertIn("M4_HEAD_REACTION_POCKETS", s.report["geometry"]["torque_path"]), s.assertIn("D10_STEEL_SHAFT", s.report["geometry"]["torque_path"]))),
        ("freeze", lambda s: s.assertTrue(s.report["geometry"]["freeze_regression"]["hub_only_revision"])),
        ("pulley_frozen", lambda s: (s.assertEqual(s.report["geometry"]["pulley"]["tooth_count"], 60), s.assertEqual(s.report["geometry"]["pulley"]["pitch_mm"], 5.0), s.assertEqual(s.report["geometry"]["pulley"]["spacing_deg"], 6.0), s.assertEqual(s.report["geometry"]["pulley"]["flange_od_mm"], 102.0), s.assertEqual(s.report["geometry"]["pulley"]["spoke_count"], 6))),
        ("meshes", lambda s: s.assertTrue(all(row["watertight"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in s.report["geometry"]["mesh"].values()))),
        ("steps", lambda s: s.assertTrue(all(row["valid"] for row in s.report["geometry"]["step_import"].values()))),
        ("hardware_collision", lambda s: s.assertEqual(s.report["geometry"]["reaction"]["m4_envelope_intersection_mm3"], 0)),
        ("coupons", lambda s: (s.assertTrue((LANE / "artifacts/collar_fit_cp160_v0_9_6_26.stl").is_file()), s.assertTrue((LANE / "artifacts/collar_fit_cp162_v0_9_6_26.stl").is_file()), s.assertTrue((LANE / "artifacts/collar_fit_cp164_v0_9_6_26.stl").is_file()))),
        ("print_hold", lambda s: (s.assertIn("CP160", s.report["geometry"]["print"]["first_print"]), s.assertEqual(s.report["geometry"]["print"]["slicer"], "HOLD_SLICER_NOT_RUN"))),
        ("false_passes", lambda s: s.assertTrue(all(value == "PHYSICAL_HOLD" for key, value in s.report["geometry"]["physical_holds"].items() if key != "powered"))),
        ("scope_firewall", lambda s: (s.assertNotIn("P20653", " ".join(s.manifest)), s.assertNotIn("crawler", " ".join(s.manifest).lower()), s.assertEqual(s.report["geometry"]["physical_holds"]["powered"], "NOT_APPROVED"))),
    ]


add_path_tests()
add_sha_tests()
for offset, (label, func) in enumerate(core_tests(), 90):
    setattr(Contract, f"test_{offset:03d}_{label}", func)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    count = suite.countTestCases()
    if count != EXPECTED_TEST_COUNT:
        raise SystemExit(f"contract count {count} != {EXPECTED_TEST_COUNT}")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"CONTRACT_COUNT={count}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
