#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest


LANE = Path(__file__).resolve().parents[1]
BUILDER_PATH = LANE / "build_temp_htd5m_60t_double_split_clamp_v0_9_6_22.py"
spec = importlib.util.spec_from_file_location("paddy_v09622_builder", BUILDER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("builder import")
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sums() -> dict[str, str]:
    result: dict[str, str] = {}
    for row in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        value, rel = row.split("  ", 1)
        result[rel] = value
    return result


class Contract(unittest.TestCase):
    maxDiff = None


def add_test(index: int, label: str, function) -> None:
    setattr(Contract, f"test_{index:03d}_{label}", function)


index = 0
for rel in b.EXPECTED_FILES:
    index += 1
    add_test(index, "path_" + rel.replace("/", "_").replace(".", "_"),
             lambda self, rel=rel: self.assertTrue((LANE / rel).is_file(), rel))

for rel in [item for item in b.EXPECTED_FILES if item != "SHA256SUMS.txt"]:
    index += 1
    add_test(index, "sha_" + rel.replace("/", "_").replace(".", "_"),
             lambda self, rel=rel: self.assertEqual(digest(LANE / rel), sums()[rel]))


def report():
    return json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))


def params():
    return json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))


core = [
    ("version", lambda self: self.assertEqual(report()["version"], "v0.9.6.22")),
    ("classification", lambda self: self.assertEqual(report()["classification"], b.CLASSIFICATION)),
    ("status", lambda self: self.assertEqual(report()["status"], b.STATUS)),
    ("repository_branch", lambda self: self.assertEqual(report()["repository"]["branch"], b.EXPECTED_BRANCH)),
    ("repository_head", lambda self: self.assertEqual(report()["repository"]["head"], b.EXPECTED_HEAD)),
    ("staged_zero", lambda self: self.assertEqual(report()["repository"]["staged"], [])),
    ("authority", lambda self: self.assertEqual(report()["repository"]["authority_sha256"], b.AUTHORITY_SHA256)),
    ("protected", lambda self: self.assertTrue(report()["repository"]["checks"]["protected_lanes"])),
    ("parent_sha", lambda self: self.assertEqual(params()["parent"]["files_sha256"], b.PARENT_FILES_SHA256)),
    ("original_source_sha", lambda self: self.assertEqual(params()["original_60t_authority"]["sha256"], b.SOURCE_SHA256)),
    ("physical_shortfall", lambda self: self.assertTrue(report()["geometry"]["physical_evidence"]["axial_hand_pull_removal"])),
    ("teeth_60", lambda self: self.assertEqual(report()["geometry"]["pulley"]["tooth_count"], 60)),
    ("pitch_htd5m", lambda self: self.assertEqual(report()["geometry"]["pulley"]["pitch_family"], "HTD5M")),
    ("spacing_6", lambda self: self.assertEqual(report()["geometry"]["pulley"]["spacing_deg"], 6.0)),
    ("face_16", lambda self: self.assertEqual(report()["geometry"]["pulley"]["tooth_face_width_mm"], 16.0)),
    ("flange_frozen", lambda self: self.assertEqual(report()["geometry"]["freeze_regression"]["flange_change"], 0)),
    ("rim_frozen", lambda self: self.assertEqual(report()["geometry"]["freeze_regression"]["rim_change"], 0)),
    ("spokes_frozen", lambda self: self.assertEqual(
        [report()["geometry"]["freeze_regression"]["spoke_change_outside_envelope"],
         report()["geometry"]["freeze_regression"]["spoke_source_primitive_reused_from_parent_builder"]], [0, True])),
    ("outside_envelope", lambda self: self.assertTrue(report()["geometry"]["freeze_regression"]["hub_only_revision"])),
    ("belt_plane", lambda self: self.assertEqual(report()["geometry"]["pulley"]["belt_plane_mm"], 10.0)),
    ("hub_od", lambda self: self.assertEqual(report()["geometry"]["hub"]["od_mm"], 34.0)),
    ("hub_width", lambda self: self.assertEqual(report()["geometry"]["hub"]["width_mm"], 26.0)),
    ("bands", lambda self: self.assertEqual([report()["geometry"]["hub"][key] for key in
                                              ("front_active_band_width_mm", "neutral_band_width_mm", "rear_active_band_width_mm")],
                                             [10.0, 6.0, 10.0])),
    ("split", lambda self: self.assertEqual(report()["geometry"]["hub"]["split_width_mm"], 1.3)),
    ("front_m4", lambda self: self.assertEqual(report()["geometry"]["hardware"]["front_m4_count"], 2)),
    ("rear_m4", lambda self: self.assertEqual(report()["geometry"]["hardware"]["rear_m4_count"], 2)),
    ("total_m4", lambda self: self.assertEqual(report()["geometry"]["hardware"]["total_m4_count"], 4)),
    ("thread_21", lambda self: self.assertEqual(report()["geometry"]["hardware"]["threaded_length_physical_authority_mm"], 21.0)),
    ("stack_14", lambda self: self.assertEqual(report()["geometry"]["hardware"]["printed_stack_mm"], 14.0)),
    ("petg_threads_zero", lambda self: self.assertEqual(report()["geometry"]["hardware"]["petg_tapped_thread_count"], 0)),
    ("coupons_three", lambda self: self.assertEqual(params()["hub"]["bore_candidates_mm"], [10.1, 10.2, 10.3])),
    ("hardware_collision_zero", lambda self: self.assertEqual(report()["geometry"]["hardware"]["hardware_envelope_intersection_mm3"], 0)),
    ("physical_holds", lambda self: self.assertTrue(all(value != "PASS" for key, value in report()["checks"].items()
                                                        if key in {"real_clamp_friction", "axial_pullout", "torque_capacity", "petg_creep"}))),
]

for label, function in core:
    index += 1
    add_test(index, label, function)

if index != 120:
    raise RuntimeError(f"contract count construction: {index}")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"CONTRACT_COUNT={suite.countTestCases()}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
