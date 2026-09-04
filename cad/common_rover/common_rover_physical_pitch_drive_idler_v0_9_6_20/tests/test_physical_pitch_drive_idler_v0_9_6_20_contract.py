#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_physical_pitch_drive_idler_v0_9_6_20.py"
spec = importlib.util.spec_from_file_location("pitch_drive_idler_v09620", BUILDER)
if spec is None or spec.loader is None: raise RuntimeError("builder import")
b = importlib.util.module_from_spec(spec); sys.modules[spec.name] = b; spec.loader.exec_module(b)


def close(a, c, tol=1e-6): return math.isclose(float(a), float(c), abs_tol=tol, rel_tol=0.0)


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verify = b.verify_lane(); cls.p = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
        cls.v = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
        cls.w = json.loads((LANE / "wrap_analysis.json").read_text(encoding="utf-8"))
        cls.i = json.loads((LANE / "idler_source_audit.json").read_text(encoding="utf-8"))


C = [
    ("repository", lambda s: Path(s.verify["repository"]["repository"]).resolve() == b.REPO_ROOT.resolve()),
    ("branch", lambda s: s.verify["repository"]["branch"] == b.EXPECTED_BRANCH),
    ("head", lambda s: s.verify["repository"]["head"] == b.EXPECTED_HEAD),
    ("staged_zero", lambda s: s.verify["repository"]["staged_count"] == 0),
    ("dirty_exact", lambda s: s.verify["repository"]["tracked_dirty_paths"] == b.TRACKED_DIRTY),
    ("authority_4", lambda s: s.verify["repository"]["authority_sha256"] == b.AUTHORITY_SHA256),
    ("protected_count", lambda s: len(s.verify["repository"]["protected_lanes"]) == 5),
    ("protected_v16", lambda s: s.verify["repository"]["protected_lanes"]["cad/common_rover/common_rover_true_open_bottom_dual_l_12t_v0_9_6_16"]["count"] == 36),
    ("protected_v17", lambda s: s.verify["repository"]["protected_lanes"]["cad/common_rover/common_rover_crawler_link_anti_derail_guard_v0_9_6_17"]["count"] == 33),
    ("protected_v18", lambda s: s.verify["repository"]["protected_lanes"]["cad/common_rover/common_rover_guard_free_true_open_bottom_drive_12t_v0_9_6_18"]["count"] == 39),
    ("protected_y3v19", lambda s: s.verify["repository"]["protected_lanes"]["cad/common_rover/common_rover_y3_reaction_shoe_v0_9_6_19"]["count"] == 34),
    ("protected_rollerv19", lambda s: s.verify["repository"]["protected_lanes"]["cad/common_rover/common_rover_drive_entry_top_hold_down_roller_v0_9_6_19"]["count"] == 39),
    ("m1", lambda s: s.p["measurement"]["five_pitch_mm"][0] == 103.6),
    ("m2", lambda s: s.p["measurement"]["five_pitch_mm"][1] == 103.2),
    ("m3", lambda s: s.p["measurement"]["five_pitch_mm"][2] == 103.0),
    ("pitch_values", lambda s: s.p["measurement"]["derived_individual_pitch_mm"] == [20.72, 20.64, 20.6]),
    ("mean_five", lambda s: close(s.p["measurement"]["mean_five_pitch_mm"], 103.2666666667)),
    ("mean_pitch", lambda s: close(s.p["measurement"]["mean_pitch_mm"], 20.6533333333)),
    ("pitch_range", lambda s: s.p["measurement"]["range_mm"] == [20.6, 20.72]),
    ("spread", lambda s: s.p["measurement"]["spread_mm_per_pitch"] == 0.12),
    ("measurement_class", lambda s: s.p["measurement"]["status"] == "PHYSICAL_MAX_EXTENSION_PITCH_REFERENCE"),
    ("operating_hold", lambda s: s.p["measurement"]["final_nominal_operating_pitch"] == "HOLD"),
    ("old104", lambda s: s.p["measurement"]["initial_104mm"] == "SUPERSEDED_COARSE_MEASUREMENT"),
    ("current_diameter", lambda s: close(s.p["drive"]["current_pitch_diameter_mm"], 76.3943726841)),
    ("current_chord", lambda s: close(s.p["drive"]["current_adjacent_chord_mm"], 19.7723185893)),
    ("current_status", lambda s: s.p["drive"]["status"] == "PHYSICAL_PHASE_MISMATCH_SUSPECTED"),
    ("candidate_keys", lambda s: set(s.p["drive"]["candidates"]) == {"P2060", "P20653", "P2072"}),
    ("p2060_pitch", lambda s: s.p["drive"]["candidates"]["P2060"]["pitch_mm"] == 20.6),
    ("p20653_pitch", lambda s: close(s.p["drive"]["candidates"]["P20653"]["pitch_mm"], 20.6533333333)),
    ("p2072_pitch", lambda s: s.p["drive"]["candidates"]["P2072"]["pitch_mm"] == 20.72),
    ("p2060_d", lambda s: close(s.p["drive"]["candidates"]["P2060"]["diameter_mm"], 79.5922880862)),
    ("p20653_d", lambda s: close(s.p["drive"]["candidates"]["P20653"]["diameter_mm"], 79.7983522624)),
    ("p2072_d", lambda s: close(s.p["drive"]["candidates"]["P2072"]["diameter_mm"], 80.0559324828)),
    ("primary", lambda s: s.p["drive"]["candidates"]["P20653"]["role"] == "PRIMARY_PHYSICAL_TEST_CANDIDATE"),
    ("comparisons", lambda s: s.p["drive"]["candidates"]["P2060"]["role"] == s.p["drive"]["candidates"]["P2072"]["role"] == "COMPARISON_ONLY"),
    ("profile_revision", lambda s: s.p["drive"]["tooth_profile_shape_revision_count"] == 0),
    ("teeth", lambda s: s.p["drive"]["teeth"] == 12),
    ("spacing", lambda s: s.p["drive"]["spacing_deg"] == 30.0),
    ("phase", lambda s: s.p["drive"]["phase_deg"] == 15.0),
    ("profile_source", lambda s: s.v["geometry"]["tooth_profile"]["tip_root_shape"] == "EXACT_V09618_SOLIDS_TRANSLATED_RADIALLY"),
    ("profile_widths", lambda s: s.v["geometry"]["tooth_profile"]["tip_width_mm"] == 7.5 and s.v["geometry"]["tooth_profile"]["root_width_mm"] == 9.5),
    ("root_bridges", lambda s: s.v["geometry"]["tooth_profile"]["local_root_bridge_count"] == 12 and s.v["geometry"]["tooth_profile"]["local_root_bridge_width_mm"] == 9.5),
    ("no_ring_added", lambda s: s.v["geometry"]["tooth_profile"]["continuous_ring_added"] is False),
    ("hub_rebuild_missing", lambda s: s.v["geometry"]["current_drive"]["v18_rebuild_missing_mm3"] == 0),
    ("hub_rebuild_added", lambda s: s.v["geometry"]["current_drive"]["v18_rebuild_added_mm3"] == 0),
    ("drive_rows", lambda s: len(s.v["geometry"]["candidate_rows"]) == 3),
    ("drive_valid", lambda s: all(r["drive_valid"] and r["drive_solids"] == 1 for r in s.v["geometry"]["candidate_rows"])),
    ("idler_valid", lambda s: all(r["idler_valid"] and r["idler_solids"] == 1 for r in s.v["geometry"]["candidate_rows"])),
    ("chords", lambda s: all(close(r["pitch_mm"], r["actual_chord_mm"]) for r in s.v["geometry"]["candidate_rows"])),
    ("idler_identified", lambda s: s.i["exact_source_located"] is True),
    ("idler_classified", lambda s: s.i["type_classified"] is True and s.i["type"] == "TOOTHED"),
    ("idler_not_fabricated", lambda s: s.i["no_fabricated_idler"] is True),
    ("idler_sha", lambda s: s.i["sha256"] == b.SOURCE_SHA256[b.IDLER_STL_REL.as_posix()]),
    ("idler_teeth", lambda s: s.i["tooth_count"] == 12),
    ("idler_width", lambda s: s.i["width_mm"] == 44.0),
    ("idler_bearing", lambda s: s.i["bearing"] == "6000-2RS"),
    ("idler_seat", lambda s: s.i["bearing_seat_mm"] == 26.2 and s.i["bearing_depth_mm"] == 8.2),
    ("idler_relief", lambda s: s.i["bore_center_relief_mm"] == 12.0),
    ("idler_transform_hold", lambda s: s.i["current_transform"] == "HOLD_EXACT_CURRENT_XYZ"),
    ("link_source_sha", lambda s: s.w["link_geometry"]["sha256"] == b.SOURCE_SHA256[b.LINK_STL_REL.as_posix()]),
    ("links_eight", lambda s: s.w["link_geometry"]["actual_source_stl_instances"] == 8),
    ("links_unscaled", lambda s: s.w["link_geometry"]["source_geometry_scaled"] is False),
    ("hinge_axes", lambda s: s.w["link_geometry"]["source_hinge_centers_mm"] == [-10.0, 10.0]),
    ("joint_extension", lambda s: close(s.w["link_geometry"]["joint_extension_relative_to_source_mm"], 0.6533333333)),
    ("link_overlap_zero", lambda s: max(s.w["drive"]["adjacent_actual_link_body_intersection_mm3"]) == 0),
    ("engagement_five", lambda s: s.w["drive"]["simultaneous_reference_links"] == 5),
    ("engagement_min3", lambda s: s.w["drive"]["simultaneous_reference_links"] >= 3),
    ("current_engagement_one", lambda s: s.w["drive"]["phase_rows"][0]["kinematic_usable_engagements"] == 1),
    ("candidate_engagement_five", lambda s: all(r["kinematic_usable_engagements"] == 5 for r in s.w["drive"]["phase_rows"][1:])),
    ("primary_phase_zero", lambda s: close(next(r for r in s.w["drive"]["phase_rows"] if r["candidate"] == "P20653")["phase_error_first_to_fifth_mm"], 0)),
    ("current_phase", lambda s: close(s.w["drive"]["phase_rows"][0]["phase_error_first_to_fifth_mm"], 3.524058976)),
    ("idler_wrap_type", lambda s: s.w["idler"]["type"] == "TOOTHED" and s.w["idler"]["same_pitch_set_as_drive"] is True),
    ("idler_no_forced_bend", lambda s: s.w["idler"]["forced_bending"] is False),
    ("source_loop", lambda s: s.w["track"]["source_nominal_path_mm"] == 800.0),
    ("physical_loop", lambda s: close(s.w["track"]["physical_max_extension_reference_path_mm"], 826.133333332)),
    ("track_rows", lambda s: len(s.w["track"]["candidate_rows"]) == 3),
    ("primary_path_increase", lambda s: close(s.w["track"]["candidate_rows"][1]["paired_wheel_path_increase_mm"], 10.6939172360)),
    ("primary_center_shift", lambda s: close(s.w["track"]["candidate_rows"][1]["required_idler_center_inward_shift_mm"], 5.3469586180)),
    ("stroke_candidate", lambda s: all(r["source_candidate_available_inward_stroke_mm"] == 12.0 for r in s.w["track"]["candidate_rows"])),
    ("stroke_remaining_positive", lambda s: all(r["remaining_candidate_stroke_mm"] > 6.0 for r in s.w["track"]["candidate_rows"])),
    ("physical_stroke_hold", lambda s: s.w["track"]["physical_available_stroke"] == "HOLD_VERIFY_CURRENT_SLOT_AND_POSITION"),
    ("excess_tension", lambda s: s.w["track"]["excessive_tension"] == "NOT_APPROVED"),
    ("guard_zero", lambda s: s.p["scope"]["crawler_guard_modification_count"] == s.p["scope"]["anti_derail_redesign_count"] == 0),
    ("top_roller_zero", lambda s: s.p["scope"]["top_hold_down_roller_artifact_count"] == 0),
    ("top_roller_deferred", lambda s: s.p["scope"]["top_hold_down_status"] == "DEFERRED_AFTER_PITCH_TEST"),
    ("paths", lambda s: s.verify["path_count"] == 55),
    ("steps", lambda s: s.verify["step_count"] == 7),
    ("stls", lambda s: s.verify["stl_count"] == 8),
    ("svgs", lambda s: s.verify["svg_count"] == 8),
    ("meshes", lambda s: s.verify["all_stl_watertight"] is True),
    ("six_mesh_pitch_refs", lambda s: sum("tooth_pitch_reference" in m for m in s.v["mesh"].values()) == 6),
    ("mesh_ref_positions", lambda s: all(m["tooth_pitch_reference"]["positions"] == 12 for m in s.v["mesh"].values() if "tooth_pitch_reference" in m)),
    ("mesh_pitch_error", lambda s: all(m["tooth_pitch_reference"]["absolute_error_mm"] <= 0.001 for m in s.v["mesh"].values() if "tooth_pitch_reference" in m)),
    ("marks_cut", lambda s: all(r["identification_mark_removed_volume_mm3"] > 0 for r in s.v["geometry"]["candidate_rows"])),
    ("step_imports", lambda s: len(s.v["step_import"]) == 7 and all(x["valid"] for x in s.v["step_import"].values())),
    ("wrap_meshes", lambda s: all(s.v["mesh"][f"artifacts/{wheel}_wrap_8links_p20653_v0_9_6_20.stl"]["watertight"] for wheel in ("drive", "idler"))),
    ("commit_paths", lambda s: len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == 55),
    ("first_print", lambda s: s.p["gates"]["printing"] == "P20653_DRIVE_FIRST"),
    ("powered", lambda s: s.p["gates"]["powered_rotation"] == "NOT_APPROVED"),
    ("final_status", lambda s: "P20653_PRIMARY_PHYSICAL_CANDIDATE" in s.verify["status"] and "COMMIT_READY_NOT_STAGED" in s.verify["status"]),
]


def make_test(name, fn):
    def test(self): self.assertTrue(fn(self), name)
    return test


for index, (name, fn) in enumerate(C, 1): setattr(Contract, f"test_{index:03d}_{name}", make_test(name, fn))

if __name__ == "__main__":
    print(f"CONTRACT_COUNT={len(C)}")
    unittest.main(verbosity=2)
