#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract tests for the v0.9.6.25 compact external-ear TEMP 60T clamp."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


LANE = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "v0.9.6.25"
EXPECTED_CLASSIFICATION = "TEMP_HTD5M_60T_COMPACT_EXTERNAL_EAR_DOUBLE_SPLIT_CLAMP"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
EXPECTED_PATH_COUNT = 42
EXPECTED_TEST_COUNT = 128


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
        ("status", lambda s: s.assertIn("SHORTEST_PASSING_PROJECTION_SELECTED", s.report["status"])),
        ("repository", lambda s: s.assertEqual(s.report["repository"]["repository"], r"D:\Paddy_Swarm_Project")),
        ("branch_head", lambda s: (s.assertEqual(s.report["repository"]["branch"], EXPECTED_BRANCH), s.assertEqual(s.report["repository"]["head"], EXPECTED_HEAD))),
        ("staged", lambda s: s.assertEqual(s.report["repository"]["staged"], [])),
        ("tracked_dirty", lambda s: s.assertEqual(len(s.report["repository"]["tracked_dirty"]), 4)),
        ("outside_untracked", lambda s: s.assertEqual(s.report["repository"]["outside_untracked"][0], 2666)),
        ("authority", lambda s: s.assertTrue(s.report["repository"]["checks"]["authority_4_of_4"])),
        ("protected", lambda s: s.assertEqual(len(s.report["repository"]["protected_lanes"]), 11)),
        ("parent", lambda s: s.assertTrue(s.report["repository"]["checks"]["parent_files"])),
        ("source", lambda s: s.assertTrue(s.report["repository"]["checks"]["source"])),
        ("candidate_count", lambda s: s.assertEqual(s.report["geometry"]["projection_study"]["candidate_count"], 17)),
        ("range", lambda s: s.assertEqual(s.report["geometry"]["projection_study"]["allowed_range_mm"], [8.8, 16.8])),
        ("ideal", lambda s: s.assertEqual(s.report["geometry"]["projection_study"]["ideal_mm"], 8.8)),
        ("ideal_evaluated", lambda s: s.assertEqual(s.report["geometry"]["projection_study"]["candidates"][0]["projection_mm"], 8.8)),
        ("ideal_failed", lambda s: s.assertEqual(s.report["geometry"]["projection_study"]["candidates"][0]["overall"], "FAIL")),
        ("selected", lambda s: s.assertEqual(s.report["geometry"]["projection_study"]["selected_projection_mm"], 15.3)),
        ("shortest_pass", lambda s: s.assertEqual(s.report["geometry"]["projection_study"]["shortest_passing_projection_mm"], 15.3)),
        ("previous_failed", lambda s: s.assertEqual(next(row for row in s.report["geometry"]["projection_study"]["candidates"] if row["projection_mm"] == 14.8)["overall"], "FAIL")),
        ("projection_symmetry", lambda s: (s.assertEqual(s.report["geometry"]["ear"]["front_projection_mm"], 15.3), s.assertEqual(s.report["geometry"]["ear"]["rear_projection_mm"], 15.3), s.assertEqual(s.report["geometry"]["ear"]["symmetry_error_mm"], 0))),
        ("datum", lambda s: s.assertIn("HUB_END_FACE", s.report["geometry"]["ear"]["projection_datum"])),
        ("m4_positions", lambda s: (s.assertEqual(s.report["geometry"]["hardware_access"]["front_centers_mm"][0][2], -8.0), s.assertEqual(s.report["geometry"]["hardware_access"]["rear_centers_mm"][0][2], 34.0))),
        ("m4_counts", lambda s: (s.assertEqual(s.report["geometry"]["hardware_access"]["front_m4_count"], 2), s.assertEqual(s.report["geometry"]["hardware_access"]["rear_m4_count"], 2), s.assertEqual(s.report["geometry"]["hardware_access"]["total_m4_count"], 4))),
        ("head_clearance", lambda s: (s.assertEqual(s.report["geometry"]["hardware_access"]["integrated_head_envelope_mm"], 12.0), s.assertGreaterEqual(s.report["geometry"]["hardware_access"]["integrated_head_clearance_to_frozen_mm"], 2.0))),
        ("service_clearance", lambda s: (s.assertEqual(s.report["geometry"]["hardware_access"]["service_envelope_mm"], 14.0), s.assertGreaterEqual(s.report["geometry"]["hardware_access"]["service_clearance_to_frozen_mm"], 1.0))),
        ("seat_coverage", lambda s: s.assertGreaterEqual(s.report["geometry"]["hardware_access"]["minimum_seat_coverage_ratio"], 0.999)),
        ("edge_ligament", lambda s: s.assertGreaterEqual(s.report["geometry"]["ear"]["minimum_hole_to_free_edge_ligament_mm"], 5.0)),
        ("bore_ligament", lambda s: s.assertGreaterEqual(s.report["geometry"]["ear"]["bore_to_m4_minimum_ligament_mm"], 5.0)),
        ("ear_thickness", lambda s: s.assertGreaterEqual(s.report["geometry"]["ear"]["minimum_thickness_mm"], 5.0)),
        ("root_fillet", lambda s: s.assertGreaterEqual(s.report["geometry"]["ear"]["root_fillet_mm"], 4.0)),
        ("root_section", lambda s: s.assertGreaterEqual(s.report["geometry"]["ear"]["root_min_load_section_mm2"], 88.0)),
        ("split", lambda s: (s.assertEqual(s.report["geometry"]["hub"]["split_width_mm"], 1.3), s.assertTrue(s.report["geometry"]["hub"]["continuous_radial_split"]), s.assertTrue(s.report["geometry"]["hub"]["front_rear_independent"]))),
        ("closure", lambda s: (s.assertEqual(s.report["geometry"]["hub"]["split_closure_reference_mm"], 0.6), s.assertGreater(s.report["geometry"]["hub"]["split_remaining_at_reference_mm"], 0))),
        ("stack", lambda s: (s.assertEqual(s.report["geometry"]["hardware_stack"]["threaded_length_mm"], 21.0), s.assertAlmostEqual(s.report["geometry"]["hardware_stack"]["total_candidate_mm"], 19.6), s.assertGreaterEqual(s.report["geometry"]["hardware_stack"]["visible_thread_count"], 2.0))),
        ("hardware_access", lambda s: (s.assertTrue(s.report["geometry"]["hardware_access"]["all_four_holes_fully_external"]), s.assertEqual(s.report["geometry"]["hardware_access"]["hardware_insertion_path_intersection_mm3"], 0))),
        ("tool", lambda s: s.assertEqual(s.report["geometry"]["hardware_access"]["tool_access"], "PASS")),
        ("bores", lambda s: (s.assertEqual(s.report["geometry"]["hub"]["shaft_nominal_mm"], 10.0), s.assertEqual(s.report["geometry"]["hub"]["bore_candidates_mm"], [10.1, 10.2, 10.3]))),
        ("frozen_authority", lambda s: (s.assertEqual(s.report["geometry"]["pulley"]["tooth_count"], 60), s.assertEqual(s.report["geometry"]["pulley"]["pitch_mm"], 5.0), s.assertEqual(s.report["geometry"]["pulley"]["spacing_deg"], 6.0))),
        ("freeze", lambda s: s.assertTrue(s.report["geometry"]["freeze_regression"]["hub_only_revision"])),
        ("meshes", lambda s: s.assertTrue(all(row["watertight"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in s.report["geometry"]["mesh"].values()))),
        ("steps", lambda s: s.assertTrue(all(row["valid"] for row in s.report["geometry"]["step_import"].values()))),
        ("support", lambda s: (s.assertGreater(s.report["geometry"]["print"]["projection_reduction_vs_v09624_percent"], 0), s.assertIn("SLICER_NOT_RUN", s.report["geometry"]["print"]["support_burden"]))),
        ("no_false_fea", lambda s: (s.assertFalse(s.report["geometry"]["analysis"]["trusted_fea_tooling_found"]), s.assertEqual(s.report["geometry"]["analysis"]["fea_result"], "NOT_RUN_NO_TRUSTED_TOOLING"))),
        ("holds", lambda s: (s.assertEqual(s.report["checks"]["physical_break_strength"], "PHYSICAL_HOLD"), s.assertEqual(s.report["checks"]["torque"], "PHYSICAL_HOLD"), s.assertEqual(s.report["checks"]["clamp_force"], "PHYSICAL_HOLD"), s.assertEqual(s.report["checks"]["powered"], "NOT_APPROVED"), s.assertEqual(s.report["geometry"]["hardware_stack"]["petg_tapped_primary_thread_count"], 0))),
    ]


add_path_tests()
add_sha_tests()
for offset, (label, func) in enumerate(core_tests(), 84):
    setattr(Contract, f"test_{offset:03d}_{label}", func)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    count = suite.countTestCases()
    if count != EXPECTED_TEST_COUNT:
        raise SystemExit(f"contract count {count} != {EXPECTED_TEST_COUNT}")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"CONTRACT_COUNT={count}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
