#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract tests for v0.9.6.28 D-cut shaft-collar torque screen."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import unittest


LANE = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "v0.9.6.28"
EXPECTED_CLASSIFICATION = "D_CUT_SHAFT_COLLAR_TORQUE_SCREEN"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
EXPECTED_PATH_COUNT = 46
EXPECTED_TEST_COUNT = 160


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
            value, rel = row.split("  ", 1); cls.sums[rel] = value
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
        ("status", lambda s: s.assertIn("2NM_TORQUE_FIXTURE_READY", s.report["status"])),
        ("repository", lambda s: s.assertEqual(s.report["repository"]["repository"], r"D:\Paddy_Swarm_Project")),
        ("branch", lambda s: s.assertEqual(s.report["repository"]["branch"], EXPECTED_BRANCH)),
        ("head", lambda s: s.assertEqual(s.report["repository"]["head"], EXPECTED_HEAD)),
        ("staged", lambda s: s.assertEqual(s.report["repository"]["staged"], [])),
        ("tracked_dirty", lambda s: s.assertEqual(len(s.report["repository"]["tracked_dirty"]), 4)),
        ("outside_untracked", lambda s: s.assertEqual(s.report["repository"]["outside_untracked"][0], 2807)),
        ("authority", lambda s: s.assertTrue(s.report["repository"]["checks"]["authority_4_of_4"])),
        ("protected", lambda s: s.assertEqual(len(s.report["repository"]["protected_lanes"]), 27)),
        ("sources", lambda s: s.assertTrue(s.report["repository"]["checks"]["source_files"])),
        ("source_discovery", lambda s: s.assertEqual(s.report["geometry"]["source_discovery"]["status"], "PASS_UNAMBIGUOUS")),
        ("no_dflat_measurement", lambda s: s.assertFalse(s.report["geometry"]["source_discovery"]["existing_dflat_physical_measurement"])),
        ("failure_status", lambda s: s.assertEqual(s.report["geometry"]["development"]["latest_status"], "FAIL_SHAFT_COLLAR_TORQUE_RETENTION_SUSPECTED")),
        ("failure_confidence", lambda s: s.assertEqual(s.report["geometry"]["development"]["failure_interface"], "UNKNOWN_REQUIRES_PHYSICAL_TEST")),
        ("blocker", lambda s: s.assertEqual(s.report["geometry"]["development"]["target_blocker"], "BLOCKER_1_DRIVETRAIN_TORQUE_TRANSMISSION")),
        ("shaft", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["shaft_nominal_mm"], 10.0)),
        ("collar_od", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["collar_od_mm"], 15.8)),
        ("collar_width", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["collar_width_mm"], 5.8)),
        ("m4_count", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["m4_per_collar"], 2)),
        ("m4_head", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["m4_head_od_mm"], 8.8)),
        ("m4_projection", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["max_radial_projection_from_collar_outer_to_head_top_mm"], 11.0)),
        ("m4_tip_hold", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["m4_tip_geometry"], "PHYSICAL_HOLD")),
        ("m4_torque_hold", lambda s: s.assertEqual(s.report["geometry"]["physical_collar_authority"]["m4_tightening_torque"], "PHYSICAL_HOLD")),
        ("candidate_count", lambda s: s.assertEqual(s.report["geometry"]["d_flat"]["candidate_count"], 3)),
        ("d03", lambda s: s.assertEqual(s.report["geometry"]["d_flat"]["candidates"]["D03"]["depth_mm"], 0.3)),
        ("d05", lambda s: s.assertEqual(s.report["geometry"]["d_flat"]["candidates"]["D05"]["depth_mm"], 0.5)),
        ("d07", lambda s: s.assertEqual(s.report["geometry"]["d_flat"]["candidates"]["D07"]["depth_mm"], 0.7)),
        ("theoretical_widths", lambda s: [s.assertAlmostEqual(s.report["geometry"]["d_flat"]["candidates"][key]["theoretical_width_mm"], 2 * math.sqrt(2 * 5.0 * depth - depth * depth), places=6) for key, depth in (("D03", 0.3), ("D05", 0.5), ("D07", 0.7))]),
        ("caliper_refs", lambda s: s.assertEqual([s.report["geometry"]["d_flat"]["candidates"][key]["opposite_surface_caliper_mm"] for key in ("D03", "D05", "D07")], [9.7, 9.5, 9.3])),
        ("axial_length", lambda s: s.assertEqual(s.report["geometry"]["d_flat"]["axial_length_target_mm"], 10.0)),
        ("axial_margin", lambda s: s.assertEqual(s.report["geometry"]["d_flat"]["axial_margin_target_each_end_mm"], 1.0)),
        ("primary_orientation", lambda s: s.assertIn("NORMAL_TO_FLAT", s.report["geometry"]["d_flat"]["primary_screw"])),
        ("secondary_orientation", lambda s: s.assertIn("ROUND_CONTACT", s.report["geometry"]["d_flat"]["secondary_screw"])),
        ("selection_rule", lambda s: s.assertIn("D03_THEN_D05_THEN_D07", s.report["geometry"]["d_flat"]["selection_rule"])),
        ("fixture_architecture", lambda s: s.assertIn("M4_HEAD_REACTION", s.report["geometry"]["fixture"]["architecture"])),
        ("torque_path", lambda s: (s.assertIn("ACTUAL_METAL_COLLAR", s.report["geometry"]["fixture"]["torque_path"]), s.assertIn("EXTERNAL_SHAFT_RESTRAINT", s.report["geometry"]["fixture"]["torque_path"]))),
        ("shaft_guide", lambda s: s.assertEqual(s.report["geometry"]["fixture"]["shaft_guide_diameter_mm"], 10.8)),
        ("shaft_clearance", lambda s: s.assertEqual(s.report["geometry"]["fixture"]["shaft_radial_clearance_mm"], 0.4)),
        ("no_shaft_clamp", lambda s: s.assertEqual(s.report["geometry"]["fixture"]["shaft_clamping_feature_count"], 0)),
        ("collar_pocket", lambda s: s.assertEqual(s.report["geometry"]["fixture"]["collar_service_pocket_mm"], 16.6)),
        ("collar_clearance", lambda s: s.assertEqual(s.report["geometry"]["fixture"]["collar_radial_clearance_mm"], 0.4)),
        ("head_slot", lambda s: s.assertEqual(s.report["geometry"]["fixture"]["head_slot_width_mm"], 9.6)),
        ("head_clearance", lambda s: s.assertEqual(s.report["geometry"]["fixture"]["head_clearance_each_side_mm"], 0.4)),
        ("head_reactions", lambda s: s.assertEqual(s.report["geometry"]["fixture"]["head_reaction_locations"], 2)),
        ("reaction_thickness", lambda s: s.assertGreaterEqual(s.report["geometry"]["fixture"]["minimum_reaction_thickness_mm"], 4.25)),
        ("tangential_shoulder", lambda s: s.assertGreaterEqual(s.report["geometry"]["fixture"]["tangential_reaction_shoulder_mm"], 5.0)),
        ("arm_root_width", lambda s: s.assertGreaterEqual(s.report["geometry"]["fixture"]["arm_root_width_mm"], 24.0)),
        ("arm_thickness", lambda s: s.assertGreaterEqual(s.report["geometry"]["fixture"]["arm_thickness_mm"], 10.0)),
        ("root_fillet", lambda s: s.assertGreater(s.report["geometry"]["fixture"]["root_fillet_mm"], 0)),
        ("load_holes", lambda s: s.assertEqual(s.report["geometry"]["fixture"]["load_hole_centers_mm"], [100.0, 150.0, 200.0])),
        ("primary_radius", lambda s: s.assertEqual(s.report["geometry"]["fixture"]["primary_load_radius_mm"], 200.0)),
        ("a1_fit", lambda s: s.assertTrue(s.report["geometry"]["fixture"]["fits_bambu_a1_without_scaling"])),
        ("flat_print", lambda s: s.assertTrue(s.report["geometry"]["fixture"]["flat_print_xy"])),
        ("torque_contract", lambda s: s.assertEqual(s.report["geometry"]["torque"]["contract_nm"], 2.0)),
        ("gravity", lambda s: s.assertEqual(s.report["geometry"]["torque"]["gravity_m_s2"], 9.80665)),
        ("reference_masses", lambda s: [s.assertAlmostEqual(s.report["geometry"]["torque"]["reference_masses"][f"R{int(r)}"]["mass_kg"], 2.0 / (9.80665 * r / 1000.0), places=6) for r in (100.0, 150.0, 200.0)]),
        ("torque_stages", lambda s: s.assertEqual(s.report["geometry"]["torque"]["stages_nm"], [0.5, 1.0, 1.5, 2.0])),
        ("hold_direction_cycles", lambda s: (s.assertEqual(s.report["geometry"]["torque"]["hold_seconds"], 10), s.assertEqual(s.report["geometry"]["torque"]["directions"], ["CW", "CCW"]), s.assertEqual(s.report["geometry"]["torque"]["cycles_at_2nm_each_direction"], 3))),
        ("impact_prohibited", lambda s: s.assertEqual(s.report["geometry"]["torque"]["impact_loading"], "PROHIBITED")),
        ("fixture_fail_class", lambda s: s.assertEqual(s.report["geometry"]["fixture"]["fixture_failure_class"], "FAIL_TEST_FIXTURE")),
        ("meshes", lambda s: s.assertTrue(all(row["watertight"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in s.report["mesh"].values()))),
        ("step_reload", lambda s: s.assertTrue(all(row["valid"] for row in s.report["step_import"].values()))),
        ("print_volume", lambda s: (s.assertGreater(s.report["geometry"]["print"]["fixture_volume_mm3"], 0), s.assertGreater(s.report["geometry"]["print"]["fixture_solid_equivalent_petg_g"], 0))),
        ("state_matrix", lambda s: (s.assertEqual(s.report["geometry"]["state_matrix"]["CAD_PASS"], "PASS"), s.assertEqual(s.report["geometry"]["state_matrix"]["TORQUE_PASS"], "NOT_YET"), s.assertEqual(s.report["geometry"]["state_matrix"]["FIELD_PASS"], "NOT_YET"))),
        ("firewalls", lambda s: (s.assertEqual(s.report["geometry"]["firewalls"]["crawler_geometry_changes"], 0), s.assertEqual(s.report["geometry"]["firewalls"]["bbox_geometry_changes"], 0), s.assertEqual(s.report["geometry"]["firewalls"]["full_60t_print"], "HOLD"))),
        ("physical_holds", lambda s: s.assertIn("ACTUAL_D_FLAT_TORQUE_CAPACITY", s.report["geometry"]["physical_holds"])),
        ("scope_and_final", lambda s: (s.assertFalse(any("60t" in rel.lower() or "bbox" in rel.lower() for rel in s.manifest)), s.assertIn("TORQUE_PASS_NOT_YET_GRANTED", s.report["status"]))),
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
