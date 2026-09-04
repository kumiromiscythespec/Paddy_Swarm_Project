#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract tests for the v0.9.6.27 rear-slide static-face seal coupon."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


LANE = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "v0.9.6.27"
EXPECTED_CLASSIFICATION = "BBOX_REAR_SLIDE_STATIC_FACE_SEAL_VALIDATION"
EXPECTED_BRANCH = "agent/organize-untracked-cad-assets-20260725"
EXPECTED_HEAD = "7c149a65053f2292bc4cc0ed06d8941c96852f2b"
EXPECTED_PATH_COUNT = 54
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
        ("status", lambda s: s.assertIn("STATIC_FACE_COMPRESSION_SEAL_ARCHITECTURE_COMPLETE", s.report["status"])),
        ("repository", lambda s: s.assertEqual(s.report["repository"]["repository"], r"D:\Paddy_Swarm_Project")),
        ("branch", lambda s: s.assertEqual(s.report["repository"]["branch"], EXPECTED_BRANCH)),
        ("head", lambda s: s.assertEqual(s.report["repository"]["head"], EXPECTED_HEAD)),
        ("staged", lambda s: s.assertEqual(s.report["repository"]["staged"], [])),
        ("tracked_dirty", lambda s: s.assertEqual(len(s.report["repository"]["tracked_dirty"]), 4)),
        ("outside_untracked", lambda s: s.assertEqual(s.report["repository"]["outside_untracked"][0], 2753)),
        ("authority", lambda s: s.assertTrue(s.report["repository"]["checks"]["authority_4_of_4"])),
        ("protected", lambda s: s.assertEqual(len(s.report["repository"]["protected_lanes"]), 25)),
        ("sources", lambda s: s.assertTrue(s.report["repository"]["checks"]["bbox_source_files"])),
        ("authority_discovery", lambda s: s.assertEqual(s.report["geometry"]["authority_discovery"]["status"], "PASS_UNAMBIGUOUS")),
        ("current_water_source", lambda s: s.assertEqual(s.report["geometry"]["authority_discovery"]["current_bbox_body_and_waterproof"], "common_rover_bbox_cbox_submerged_power_architecture_v0_9_6_0")),
        ("rear_service_source", lambda s: s.assertEqual(s.report["geometry"]["authority_discovery"]["rear_opening_service_concept"], "common_rover_bbox_cbox_printable_prototype_v0_9_5_0")),
        ("physical_source", lambda s: s.assertEqual(s.report["geometry"]["authority_discovery"]["latest_physical_measurement"], "common_rover_physical_measurement_closure_v0_9_5_2")),
        ("dry_source", lambda s: s.assertEqual(s.report["geometry"]["authority_discovery"]["dry_battery_tray_reference"], "common_rover_dry_drive_battery_tray_v0_9_6_3")),
        ("coupon_scale", lambda s: s.assertEqual(s.report["geometry"]["coupon"]["scale"], "FULL_SIZE_REAR_OPENING_CROSS_SECTION_SHORT_CASSETTE")),
        ("not_full_bbox", lambda s: s.assertFalse(s.report["geometry"]["coupon"]["full_bbox"])),
        ("opening", lambda s: s.assertEqual(s.report["geometry"]["coupon"]["rear_opening_mm"], [110.0, 104.0])),
        ("slide_direction", lambda s: s.assertEqual(s.report["geometry"]["slide"]["direction"], "REAR_MINUS_X")),
        ("rail_candidates", lambda s: s.assertEqual(s.report["geometry"]["slide"]["rail_clearance_candidates_per_side_mm"], [0.3, 0.5, 0.7])),
        ("rail_selected", lambda s: s.assertEqual(s.report["geometry"]["slide"]["selected_clearance_per_side_mm"], 0.5)),
        ("rail_penetration", lambda s: s.assertEqual(s.report["geometry"]["slide"]["through_wall_rail_fasteners"], 0)),
        ("mechanical_stop", lambda s: s.assertIn("FOUR_INTERCHANGEABLE", s.report["geometry"]["slide"]["mechanical_final_stop"])),
        ("gasket_static", lambda s: s.assertEqual(s.report["geometry"]["seal"]["type"], "STATIC_FACE_COMPRESSION")),
        ("dynamic_zero", lambda s: s.assertEqual(s.report["geometry"]["seal"]["dynamic_sliding_seal_count"], 0)),
        ("closed_loop", lambda s: (s.assertEqual(s.report["geometry"]["seal"]["closed_loop_count"], 1), s.assertTrue(s.report["geometry"]["seal"]["continuity"]))),
        ("gasket_thickness", lambda s: s.assertEqual(s.report["geometry"]["seal"]["nominal_thickness_mm"], 2.0)),
        ("compression_candidates", lambda s: s.assertEqual(s.report["geometry"]["seal"]["compression_candidates_percent"], [20.0, 22.5, 25.0])),
        ("selected_compression", lambda s: s.assertEqual(s.report["geometry"]["seal"]["selected_compression_percent"], 25.0)),
        ("closed_gap", lambda s: s.assertEqual(s.report["geometry"]["seal"]["selected_closed_gap_mm"], 1.5)),
        ("gasket_land", lambda s: s.assertEqual(s.report["geometry"]["seal"]["land_width_mm"], 8.0)),
        ("gasket_radii", lambda s: (s.assertEqual(s.report["geometry"]["seal"]["outer_corner_radius_mm"], 14.0), s.assertEqual(s.report["geometry"]["seal"]["inner_corner_radius_mm"], 8.0))),
        ("slide_contact", lambda s: s.assertEqual(s.report["geometry"]["seal"]["sliding_contact_before_final_seat_mm3"], 0)),
        ("seal_penetrations", lambda s: (s.assertEqual(s.report["geometry"]["seal"]["primary_line_penetrations"], 0), s.assertEqual(s.report["geometry"]["seal"]["fastener_to_gasket_intersection_mm3"], 0))),
        ("faceplate_candidates", lambda s: s.assertEqual(s.report["geometry"]["faceplate"]["thickness_candidates_mm"], [4.0, 5.0, 6.0])),
        ("faceplate_selected", lambda s: s.assertEqual(s.report["geometry"]["faceplate"]["selected_thickness_mm"], 6.0)),
        ("faceplate_ribs", lambda s: s.assertIn("CASSETTE_FLOOR", s.report["geometry"]["faceplate"]["ribs"])),
        ("closure_four", lambda s: s.assertEqual(s.report["geometry"]["faceplate"]["closure_points"], 4)),
        ("fastener_outside", lambda s: s.assertTrue(s.report["geometry"]["faceplate"]["fasteners_outside_gasket"])),
        ("stop_candidates", lambda s: s.assertEqual(s.report["geometry"]["compression_stops"]["candidate_lengths_mm"], [1.6, 1.55, 1.5])),
        ("gasket_not_stop", lambda s: s.assertFalse(s.report["geometry"]["compression_stops"]["gasket_is_motion_stop"])),
        ("mud_lip", lambda s: s.assertEqual(s.report["geometry"]["mud"]["classification"], "MUD_EXCLUSION_ONLY")),
        ("drain_zone", lambda s: (s.assertTrue(s.report["geometry"]["mud"]["drain_zone"]), s.assertEqual(s.report["geometry"]["mud"]["drain_notches"], 2))),
        ("sealed_drain_zero", lambda s: s.assertEqual(s.report["geometry"]["mud"]["drain_inside_sealed_perimeter"], 0)),
        ("battery_reference", lambda s: (s.assertEqual(s.report["geometry"]["battery"]["body_mm"], [150.9, 99.4, 92.5]), s.assertEqual(s.report["geometry"]["battery"]["mass_kg"], 1.2))),
        ("live_battery", lambda s: s.assertEqual(s.report["geometry"]["battery"]["live_battery"], "NOT_APPROVED")),
        ("feedthrough_zero", lambda s: s.assertEqual(s.report["geometry"]["electrical"]["feedthrough_count"], 0)),
        ("collision_zero", lambda s: s.assertTrue(all(value == 0 for value in s.report["geometry"]["intersections"].values()))),
        ("meshes", lambda s: s.assertTrue(all(row["watertight"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in s.report["mesh"].values()))),
        ("step_reload", lambda s: s.assertTrue(all(row["valid"] for row in s.report["step_import"].values()))),
        ("holds_and_gates", lambda s: (s.assertTrue(all(value == "PHYSICAL_HOLD" for key, value in s.report["checks"].items() if key in {"real_waterproofness", "petg_porosity", "real_gasket_pressure", "surface_roughness", "mud_sealing", "thermal_pumping", "long_term_compression_set"})), s.assertEqual(s.report["geometry"]["gates"]["live_battery"], "NOT_APPROVED"), s.assertEqual(s.report["geometry"]["gates"]["full_bbox_print"], "NOT_APPROVED"))),
    ]


add_path_tests()
add_sha_tests()
for offset, (label, func) in enumerate(core_tests(), 108):
    setattr(Contract, f"test_{offset:03d}_{label}", func)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    count = suite.countTestCases()
    if count != EXPECTED_TEST_COUNT:
        raise SystemExit(f"contract count {count} != {EXPECTED_TEST_COUNT}")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"CONTRACT_COUNT={count}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
