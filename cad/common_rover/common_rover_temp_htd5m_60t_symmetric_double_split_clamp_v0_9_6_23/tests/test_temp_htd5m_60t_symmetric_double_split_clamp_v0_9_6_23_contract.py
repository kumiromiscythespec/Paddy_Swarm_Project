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
BUILDER = LANE / "build_temp_htd5m_60t_symmetric_double_split_clamp_v0_9_6_23.py"
spec = importlib.util.spec_from_file_location("paddy_v09623_builder", BUILDER)
if spec is None or spec.loader is None: raise RuntimeError("builder import")
b = importlib.util.module_from_spec(spec); sys.modules[spec.name] = b; spec.loader.exec_module(b)

def digest(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def sums() -> dict[str, str]:
    result = {}
    for row in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        value, rel = row.split("  ", 1); result[rel] = value
    return result
def report(): return json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
def params(): return json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))

class Contract(unittest.TestCase): maxDiff = None
def add(index: int, label: str, function) -> None: setattr(Contract, f"test_{index:03d}_{label}", function)

index = 0
for rel in b.EXPECTED_FILES:
    index += 1
    add(index, "path_" + rel.replace("/", "_").replace(".", "_"),
        lambda self, rel=rel: self.assertTrue((LANE / rel).is_file(), rel))
for rel in [x for x in b.EXPECTED_FILES if x != "SHA256SUMS.txt"]:
    index += 1
    add(index, "sha_" + rel.replace("/", "_").replace(".", "_"),
        lambda self, rel=rel: self.assertEqual(digest(LANE / rel), sums()[rel]))

core = [
    ("version", lambda s: s.assertEqual(report()["version"], "v0.9.6.23")),
    ("classification", lambda s: s.assertEqual(report()["classification"], b.CLASSIFICATION)),
    ("status", lambda s: s.assertEqual(report()["status"], b.STATUS)),
    ("branch", lambda s: s.assertEqual(report()["repository"]["branch"], b.EXPECTED_BRANCH)),
    ("head", lambda s: s.assertEqual(report()["repository"]["head"], b.EXPECTED_HEAD)),
    ("staged", lambda s: s.assertEqual(report()["repository"]["staged"], [])),
    ("authority", lambda s: s.assertEqual(report()["repository"]["authority_sha256"], b.AUTHORITY_SHA256)),
    ("protected", lambda s: s.assertTrue(report()["repository"]["checks"]["protected_lanes"])),
    ("parent", lambda s: s.assertEqual(params()["parent"]["files_sha256"], b.PARENT_FILES_SHA256)),
    ("reason", lambda s: s.assertTrue(report()["geometry"]["physical"]["axial_hand_pull_removal"])),
    ("teeth", lambda s: s.assertEqual(report()["geometry"]["pulley"]["tooth_count"], 60)),
    ("pitch", lambda s: s.assertEqual(report()["geometry"]["pulley"]["pitch_mm"], 5.0)),
    ("spacing", lambda s: s.assertEqual(report()["geometry"]["pulley"]["spacing_deg"], 6.0)),
    ("face", lambda s: s.assertEqual(report()["geometry"]["pulley"]["tooth_face_width_mm"], 16.0)),
    ("flanges", lambda s: s.assertEqual([report()["geometry"]["pulley"]["flange_count"], report()["geometry"]["pulley"]["flange_od_mm"]], [2, 102.0])),
    ("freeze", lambda s: s.assertTrue(report()["geometry"]["freeze_regression"]["hub_only_revision"])),
    ("spokes", lambda s: s.assertEqual([report()["geometry"]["pulley"]["spoke_count"], report()["geometry"]["pulley"]["spoke_width_mm"]], [6, 10.0])),
    ("belt_plane", lambda s: s.assertEqual(report()["geometry"]["pulley"]["belt_plane_mm"], 10.0)),
    ("bands", lambda s: s.assertEqual([report()["geometry"]["hub"]["front_active_band_z_mm"], report()["geometry"]["hub"]["neutral_band_z_mm"], report()["geometry"]["hub"]["rear_active_band_z_mm"]], [[0.0,10.0],[10.0,16.0],[16.0,26.0]])),
    ("hub", lambda s: s.assertEqual([report()["geometry"]["hub"]["od_mm"], report()["geometry"]["hub"]["width_mm"], report()["geometry"]["hub"]["neutral_od_mm"]], [34.0,26.0,28.0])),
    ("split", lambda s: s.assertEqual(report()["geometry"]["hub"]["split_width_mm"], 1.3)),
    ("external_ears", lambda s: s.assertTrue(report()["geometry"]["ear_symmetry"]["external_ear_not_internal_boss"])),
    ("front_projection", lambda s: s.assertEqual(report()["geometry"]["ear_symmetry"]["front_outward_projection_mm"], 6.2)),
    ("rear_projection", lambda s: s.assertEqual(report()["geometry"]["ear_symmetry"]["rear_outward_projection_mm"], 6.2)),
    ("projection_equal", lambda s: s.assertEqual(report()["geometry"]["ear_symmetry"]["projection_difference_mm"], 0.0)),
    ("stack_equal", lambda s: s.assertEqual(report()["geometry"]["ear_symmetry"]["stack_difference_mm"], 0.0)),
    ("m4_counts", lambda s: s.assertEqual([report()["geometry"]["hardware"]["front_m4_count"], report()["geometry"]["hardware"]["rear_m4_count"], report()["geometry"]["hardware"]["total_m4_count"]], [2,2,4])),
    ("m4_length", lambda s: s.assertEqual(report()["geometry"]["hardware"]["threaded_length_mm"], 21.0)),
    ("m4_stack", lambda s: s.assertEqual([report()["geometry"]["hardware"]["front_printed_stack_mm"], report()["geometry"]["hardware"]["rear_printed_stack_mm"]], [14.0,14.0])),
    ("threads", lambda s: s.assertEqual([report()["geometry"]["hardware"]["petg_tapped_thread_count"], report()["geometry"]["hardware"]["hidden_nut_ceiling"]], [0,False])),
    ("bores", lambda s: s.assertEqual(params()["hub"]["bore_candidates_mm"], [10.1,10.2,10.3])),
    ("collision", lambda s: s.assertEqual(report()["geometry"]["hardware"]["hardware_envelope_intersection_mm3"], 0)),
    ("holds", lambda s: s.assertEqual(report()["checks"]["powered"], "NOT_APPROVED")),
]
for label, function in core:
    index += 1; add(index, label, function)
if index != 120: raise RuntimeError(f"test count {index}")

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"CONTRACT_COUNT={suite.countTestCases()}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
