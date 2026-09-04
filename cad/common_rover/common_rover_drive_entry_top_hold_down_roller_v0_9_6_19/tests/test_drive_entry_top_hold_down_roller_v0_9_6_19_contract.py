#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract tests for the isolated DRIVE-entry hold-down roller lane."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_drive_entry_top_hold_down_roller_v0_9_6_19.py"
spec = importlib.util.spec_from_file_location("drive_hold_down_v09619", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("builder import failed")
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.verify = b.verify_lane()
        cls.p = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
        cls.i = json.loads((LANE / "interference_report.json").read_text(encoding="utf-8"))
        cls.v = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.g = cls.v["geometry"]
        cls.rows = cls.g["roller"]["push_rows"]


def _all_row_zero(rows: list[dict[str, object]], keys: list[str]) -> bool:
    return all(float(row[key]) == 0.0 for row in rows for key in keys)


ZERO_KEYS_A = [
    "roller_vs_central_protrusion_mm3", "roller_vs_protected_12t_mm3",
    "carriage_vs_link_flats_mm3", "carriage_vs_central_protrusion_mm3",
    "carriage_vs_protected_12t_mm3",
]
ZERO_KEYS_B = [
    "auxiliary_vs_dual_l_cap_mm3", "auxiliary_vs_stop_key_mm3",
    "auxiliary_vs_belt_entry_corridor_mm3", "auxiliary_vs_open_bottom_keepout_mm3",
    "axle_vs_roller_material_mm3",
]


CONDITIONS = [
    ("repository", lambda s: Path(s.verify["repository"]["repository"]).resolve() == b.REPO_ROOT.resolve()),
    ("branch", lambda s: s.verify["repository"]["branch"] == b.EXPECTED_BRANCH),
    ("head", lambda s: s.verify["repository"]["head"] == b.EXPECTED_HEAD),
    ("staged_zero", lambda s: s.verify["repository"]["staged_count"] == 0),
    ("tracked_dirty_exact", lambda s: s.verify["repository"]["tracked_dirty_paths"] == b.TRACKED_DIRTY),
    ("authority_root", lambda s: s.verify["repository"]["authority_sha256"]["CURRENT_COMMON_ROVER_AUTHORITY.md"] == b.AUTHORITY_SHA256["CURRENT_COMMON_ROVER_AUTHORITY.md"]),
    ("authority_readme", lambda s: s.verify["repository"]["authority_sha256"]["README.md"] == b.AUTHORITY_SHA256["README.md"]),
    ("authority_docs", lambda s: s.verify["repository"]["authority_sha256"]["docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md"] == b.AUTHORITY_SHA256["docs/design_authority/CURRENT_COMMON_ROVER_AUTHORITY.md"]),
    ("authority_rovers", lambda s: s.verify["repository"]["authority_sha256"]["rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md"] == b.AUTHORITY_SHA256["rovers/common_rover/CURRENT_COMMON_ROVER_AUTHORITY.md"]),
    ("protected_v16", lambda s: s.verify["repository"]["protected_lanes"]["cad/common_rover/common_rover_true_open_bottom_dual_l_12t_v0_9_6_16"]["count"] == 36),
    ("protected_v17", lambda s: s.verify["repository"]["protected_lanes"]["cad/common_rover/common_rover_crawler_link_anti_derail_guard_v0_9_6_17"]["count"] == 33),
    ("protected_v18", lambda s: s.verify["repository"]["protected_lanes"]["cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18"]["count"] == 39),
    ("scope_drive", lambda s: s.p["scope"]["drive_entry_hold_down_only"] is True),
    ("scope_crawler_zero", lambda s: s.p["scope"]["crawler_guard_geometry_dependency_count"] == 0),
    ("scope_parent_unmodified", lambda s: s.p["scope"]["v09618_body_modified"] is False),
    ("authority_distance", lambda s: s.p["physical_authority"]["link_to_nearest_frame_face_mm"] == 60.0),
    ("authority_flat", lambda s: s.p["physical_authority"]["link_flat_width_each_mm"] == 10.0),
    ("authority_press", lambda s: s.p["physical_authority"]["manual_top_press_improved_engagement"] is True),
    ("frame_profile", lambda s: s.p["frame"]["profile"] == "2020"),
    ("frame_cut", lambda s: s.p["frame"]["vertical_cut_length_mm"] == 110.0),
    ("frame_cut_hold", lambda s: s.p["frame"]["cut_gate"] == "HOLD_VERIFY_ACTUAL_UPPER_LOWER_FACE_GAP"),
    ("frame_mount", lambda s: "L_SPLICE" in s.p["frame"]["mount"]),
    ("roller_architecture", lambda s: s.p["roller"]["architecture"] == "LEFT_RIGHT_SPLIT_PLAIN_ROLLER"),
    ("roller_quantity", lambda s: s.p["roller"]["quantity"] == 2),
    ("roller_od", lambda s: s.p["roller"]["od_mm"] == 16.0),
    ("roller_width", lambda s: s.p["roller"]["width_each_mm"] == 8.0),
    ("roller_bore", lambda s: s.p["roller"]["bore_mm"] == 4.3),
    ("roller_axis", lambda s: s.p["roller"]["axis"] == "M4x20_TWO_INDEPENDENT_AXLES"),
    ("roller_bearing", lambda s: s.p["roller"]["bearing"] == "NONE_DRY_TEST_PLAIN_BORE"),
    ("roller_flat_margin", lambda s: s.p["roller"]["flat_margin_each_mm"] == 2.0),
    ("push_range", lambda s: s.p["adjustment"]["push_range_mm"] == [0.0, 3.0]),
    ("cad_samples", lambda s: s.p["adjustment"]["cad_samples_mm"] == [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]),
    ("physical_samples", lambda s: s.p["adjustment"]["physical_test_mm"] == [0.0, 0.5, 1.0, 1.5, 2.0]),
    ("slot_length", lambda s: s.p["adjustment"]["vertical_slot_length_mm"] == 8.5),
    ("slot_width", lambda s: s.p["adjustment"]["vertical_slot_width_mm"] == 5.5),
    ("upstream", lambda s: s.p["adjustment"]["upstream_mm"] == 10.0),
    ("upstream_range", lambda s: s.p["adjustment"]["allowed_upstream_mm"] == [5.0, 15.0]),
    ("layout_distance", lambda s: s.g["layout"]["link_to_frame_face_mm"] == 60.0),
    ("layout_upstream", lambda s: s.g["layout"]["roller_upstream_mm"] == 10.0),
    ("post_bounds", lambda s: s.g["frame"]["vertical_2020_bounds_mm"] == [20.0, 20.0, 110.0]),
    ("lower_mount_bounds", lambda s: s.g["frame"]["lower_mount_bounds_mm"] == [36.0, 20.0, 58.0]),
    ("upper_mount_bounds", lambda s: s.g["frame"]["upper_mount_bounds_mm"] == [36.0, 20.0, 58.0]),
    ("post_carriage_clear", lambda s: s.g["frame"]["post_vs_carriage_mm3"] == 0.0),
    ("frame_parent_clear", lambda s: s.g["frame"]["frame_vs_parent_12t_mm3"] == 0.0),
    ("push_row_count", lambda s: len(s.rows) == 7),
    ("unintended_max", lambda s: s.g["roller"]["max_unintended_intersection_mm3"] == 0.0),
    ("contact_monotonic", lambda s: s.g["roller"]["intended_contact_monotonic"] is True),
    ("row_zero_group_a", lambda s: _all_row_zero(s.rows, ZERO_KEYS_A)),
    ("row_zero_group_b", lambda s: _all_row_zero(s.rows, ZERO_KEYS_B)),
    ("zero_baseline_contact", lambda s: s.rows[0]["left_flat_intended_contact_mm3"] == s.rows[0]["right_flat_intended_contact_mm3"] == 0.0),
    ("positive_push_contact", lambda s: all(row["left_flat_intended_contact_mm3"] > 0 and row["right_flat_intended_contact_mm3"] > 0 for row in s.rows[1:])),
    ("belt_corridor", lambda s: s.g["service"]["belt_side_entry_intersection_max_mm3"] == 0.0),
    ("open_bottom", lambda s: s.g["service"]["open_bottom_intersection_max_mm3"] == 0.0),
    ("carriage_removable", lambda s: s.g["service"]["roller_carriage_removable"] is True),
    ("parent_hash", lambda s: s.g["protected_12t"]["artifact_sha256"] == b.V18_ARTIFACT_SHA256[b.V18_MAIN_REL]),
    ("parent_volume", lambda s: math_isclose(s.g["protected_12t"]["source_volume_mm3"], s.g["protected_12t"]["placed_volume_mm3"])),
    ("parent_missing_zero", lambda s: s.g["protected_12t"]["missing_volume_mm3"] == 0.0),
    ("step_count", lambda s: s.verify["step_count"] == 6),
    ("stl_count", lambda s: s.verify["stl_count"] == 5),
    ("svg_count", lambda s: s.verify["svg_count"] == 4),
    ("path_count", lambda s: s.verify["path_count"] == 39),
    ("commit_paths", lambda s: len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == 39),
    ("pair_two_solids", lambda s: s.verify["mesh"][b.CAD[8]]["connected_solid_count"] == 2),
    ("mesh_all_watertight", lambda s: all(row["watertight"] and row["bad_edge_count"] == 0 for row in s.verify["mesh"].values())),
    ("final_status", lambda s: "FULL_POWER_NOT_APPROVED" in s.verify["status"] and s.p["gates"]["powered"] == "NOT_APPROVED"),
]


def math_isclose(a: float, b_value: float) -> bool:
    return abs(float(a) - float(b_value)) <= 1e-6


def _make_test(name: str, predicate):
    def test(self):
        self.assertTrue(predicate(self), name)
    return test


for index, (name, predicate) in enumerate(CONDITIONS, 1):
    setattr(Contract, f"test_{index:03d}_{name}", _make_test(name, predicate))


if len(CONDITIONS) != 65:
    raise RuntimeError(f"expected 65 contracts, got {len(CONDITIONS)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
