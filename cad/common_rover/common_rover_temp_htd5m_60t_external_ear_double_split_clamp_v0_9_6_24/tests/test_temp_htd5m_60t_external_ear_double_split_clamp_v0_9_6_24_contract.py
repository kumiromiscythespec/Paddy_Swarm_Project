#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract tests for the v0.9.6.24 fully external M4-ear candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


LANE = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "v0.9.6.24"
EXPECTED_CLASSIFICATION = "TEMP_HTD5M_60T_EXTERNAL_EAR_DOUBLE_SPLIT_CLAMP"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
EXPECTED_PATH_COUNT = 46
EXPECTED_TEST_COUNT = 130


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


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
    manifest = sorted((LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()) if (LANE / "MANIFEST.txt").exists() else []
    for index, rel in enumerate(manifest, 1):
        def check(self: Contract, item: str = rel) -> None:
            self.assertTrue((LANE / item).is_file(), item)
        setattr(Contract, f"test_{index:03d}_path_{safe_name(rel)}", check)


def add_sha_tests() -> None:
    start = EXPECTED_PATH_COUNT + 1
    sums_path = LANE / "SHA256SUMS.txt"
    rows = []
    if sums_path.exists():
        rows = [row.split("  ", 1)[1] for row in sums_path.read_text(encoding="utf-8").splitlines()]
    for offset, rel in enumerate(sorted(rows)):
        def check(self: Contract, item: str = rel) -> None:
            self.assertEqual(sha256(LANE / item), self.sums[item], item)
        setattr(Contract, f"test_{start + offset:03d}_sha_{safe_name(rel)}", check)


def core_tests() -> list[tuple[str, object]]:
    return [
        ("version", lambda s: s.assertEqual(s.report["version"], EXPECTED_VERSION)),
        ("classification", lambda s: s.assertEqual(s.report["classification"], EXPECTED_CLASSIFICATION)),
        ("status", lambda s: s.assertIn("FRONT_REAR_M4_HOLES_FULLY_EXTERNAL", s.report["status"])),
        ("repository", lambda s: s.assertEqual(s.report["repository"]["repository"], r"D:\Paddy_Swarm_Project")),
        ("branch_head", lambda s: (s.assertEqual(s.report["repository"]["branch"], EXPECTED_BRANCH), s.assertEqual(s.report["repository"]["head"], EXPECTED_HEAD))),
        ("staged", lambda s: s.assertEqual(s.report["repository"]["staged"], [])),
        ("tracked_dirty", lambda s: s.assertEqual(len(s.report["repository"]["tracked_dirty"]), 4)),
        ("outside", lambda s: s.assertEqual(s.report["repository"]["outside_untracked"][0], 2620)),
        ("authority", lambda s: s.assertTrue(s.report["repository"]["checks"]["authority_4_of_4"])),
        ("protected", lambda s: s.assertEqual(len(s.report["repository"]["protected_lanes"]), 10)),
        ("parent", lambda s: s.assertTrue(s.report["repository"]["checks"]["parent_files"])),
        ("source", lambda s: s.assertTrue(s.report["repository"]["checks"]["source"])),
        ("teeth_pitch_spacing", lambda s: (s.assertEqual(s.report["geometry"]["pulley"]["tooth_count"], 60), s.assertEqual(s.report["geometry"]["pulley"]["pitch_mm"], 5.0), s.assertEqual(s.report["geometry"]["pulley"]["spacing_deg"], 6.0))),
        ("face_flanges", lambda s: (s.assertEqual(s.report["geometry"]["pulley"]["tooth_face_width_mm"], 16.0), s.assertEqual(s.report["geometry"]["pulley"]["flange_count"], 2), s.assertEqual(s.report["geometry"]["pulley"]["flange_od_mm"], 102.0))),
        ("spokes_belt", lambda s: (s.assertEqual(s.report["geometry"]["pulley"]["spoke_count"], 6), s.assertEqual(s.report["geometry"]["pulley"]["belt_plane_mm"], 10.0))),
        ("freeze", lambda s: s.assertTrue(s.report["geometry"]["freeze_regression"]["hub_only_revision"])),
        ("bands", lambda s: s.assertEqual([s.report["geometry"]["hub"]["front_active_band_z_mm"], s.report["geometry"]["hub"]["neutral_band_z_mm"], s.report["geometry"]["hub"]["rear_active_band_z_mm"]], [[0.0, 10.0], [10.0, 16.0], [16.0, 26.0]])),
        ("hub", lambda s: (s.assertEqual(s.report["geometry"]["hub"]["od_mm"], 34.0), s.assertEqual(s.report["geometry"]["hub"]["width_mm"], 26.0))),
        ("split", lambda s: (s.assertEqual(s.report["geometry"]["hub"]["split_width_mm"], 1.3), s.assertGreater(s.report["geometry"]["hub"]["split_material_remaining_mm"], 12.0))),
        ("mirror", lambda s: (s.assertEqual(s.report["geometry"]["ear_symmetry"]["mirror_plane_z_mm"], 13.0), s.assertTrue(s.report["geometry"]["ear_symmetry"]["axial_mirror_pass"]))),
        ("projection", lambda s: (s.assertEqual(s.report["geometry"]["ear_symmetry"]["front_outward_projection_mm"], 18.0), s.assertEqual(s.report["geometry"]["ear_symmetry"]["rear_outward_projection_mm"], 18.0))),
        ("ear_root", lambda s: (s.assertGreaterEqual(s.report["geometry"]["ear_symmetry"]["root_fillet_front_mm"], 3.0), s.assertGreaterEqual(s.report["geometry"]["ear_symmetry"]["minimum_thickness_front_mm"], 5.0))),
        ("m4_counts", lambda s: (s.assertEqual(s.report["geometry"]["hardware_access"]["front_m4_count"], 2), s.assertEqual(s.report["geometry"]["hardware_access"]["rear_m4_count"], 2), s.assertEqual(s.report["geometry"]["hardware_access"]["total_m4_count"], 4))),
        ("center_offsets", lambda s: s.assertEqual(s.report["geometry"]["hardware_access"]["hole_center_outside_hub_face_mm"], 10.0)),
        ("hole_edge_clearance", lambda s: s.assertGreaterEqual(s.report["geometry"]["hardware_access"]["hole_edge_clearance_to_hub_face_mm"], 7.75)),
        ("access_diameter", lambda s: s.assertEqual(s.report["geometry"]["hardware_access"]["seat_and_tool_diameter_mm"], 14.0)),
        ("access_face_clearance", lambda s: s.assertGreaterEqual(s.report["geometry"]["hardware_access"]["seat_and_tool_clearance_to_hub_face_mm"], 3.0)),
        ("seat_coverage", lambda s: s.assertGreaterEqual(s.report["geometry"]["hardware_access"]["minimum_seat_coverage_ratio"], 0.999)),
        ("washer_tool_gaps", lambda s: (s.assertGreaterEqual(s.report["geometry"]["hardware_access"]["washer_pair_gap_mm"], 5.0), s.assertGreaterEqual(s.report["geometry"]["hardware_access"]["tool_pair_gap_mm"], 0.0))),
        ("external_access", lambda s: s.assertEqual(s.report["geometry"]["hardware_access"]["external_access_intersection_mm3"], 0)),
        ("all_external", lambda s: s.assertTrue(s.report["geometry"]["hardware_access"]["all_four_holes_fully_external"])),
        ("hardware_collision", lambda s: s.assertEqual(s.report["geometry"]["hardware_stack"]["hardware_envelope_intersection_mm3"], 0)),
        ("m4_length", lambda s: s.assertEqual(s.report["geometry"]["hardware_stack"]["threaded_length_mm"], 21.0)),
        ("m4_stack", lambda s: s.assertAlmostEqual(s.report["geometry"]["hardware_stack"]["stack_used_candidate_mm"], 19.6)),
        ("thread_pitches", lambda s: s.assertGreaterEqual(s.report["geometry"]["hardware_stack"]["visible_thread_pitch_candidate"], 2.0)),
        ("bores", lambda s: s.assertEqual(s.report["geometry"]["hub"]["bore_candidates_mm"], [10.1, 10.2, 10.3])),
        ("meshes", lambda s: s.assertTrue(all(m["watertight"] and m["bad_edge_count"] == 0 and m["degenerate_triangle_count"] == 0 for m in s.report["geometry"]["mesh"].values()))),
        ("steps", lambda s: s.assertTrue(all(m["valid"] for m in s.report["geometry"]["step_import"].values()))),
        ("holds_first_print", lambda s: (s.assertEqual(s.report["geometry"]["print"]["first_print"], "COUPONS_ONLY_FULL_60T_PROHIBITED_FIRST"), s.assertEqual(s.report["checks"]["physical_clamp"], "HOLD"), s.assertEqual(s.report["checks"]["powered"], "NOT_APPROVED"))),
    ]


add_path_tests()
add_sha_tests()
for offset, (label, func) in enumerate(core_tests(), 92):
    setattr(Contract, f"test_{offset:03d}_{label}", func)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    count = suite.countTestCases()
    if count != EXPECTED_TEST_COUNT:
        raise SystemExit(f"contract count {count} != {EXPECTED_TEST_COUNT}")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"CONTRACT_COUNT={count}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
