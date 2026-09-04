#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import unittest

LANE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("temp60_v09621", LANE / "build_temp_htd5m_60t_split_clamp_pulley_v0_9_6_21.py")
b = importlib.util.module_from_spec(spec); sys.modules[spec.name] = b; spec.loader.exec_module(b)

def close(a, c, tol=1e-6): return abs(a-c) <= tol

class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verify = b.verify(); cls.v = json.loads((LANE/"validation_report.json").read_text(encoding="utf-8")); cls.p = json.loads((LANE/"design_parameters.json").read_text(encoding="utf-8"))

C = [
    ("repository", lambda s: s.verify["repository"]["checks"]["repository"]),
    ("branch", lambda s: s.verify["repository"]["branch"] == b.EXPECTED_BRANCH),
    ("head", lambda s: s.verify["repository"]["head"] == b.EXPECTED_HEAD),
    ("staged", lambda s: not s.verify["repository"]["staged"]),
    ("dirty", lambda s: s.verify["repository"]["tracked_dirty"] == b.TRACKED_DIRTY),
    ("outside", lambda s: tuple(s.verify["repository"]["outside_untracked"]) == (b.BASE_OUTSIDE_COUNT,b.BASE_OUTSIDE_DIGEST)),
    ("authority", lambda s: s.verify["repository"]["authority_sha256"] == b.AUTHORITY_SHA256),
    ("protected_count", lambda s: len(s.verify["repository"]["protected_lanes"]) == 7),
    ("protected_all", lambda s: all(x["status"] == "UNCHANGED" for x in s.verify["repository"]["protected_lanes"].values())),
    ("source_sha", lambda s: s.verify["repository"]["source_sha256"] == b.SOURCE_FILES_SHA256),
    ("cache", lambda s: not s.verify["repository"]["cache"]),
    ("forbidden", lambda s: not s.verify["repository"]["forbidden"]),
    ("class", lambda s: s.p["classification"] == b.CLASSIFICATION),
    ("source_lane", lambda s: s.p["source"]["lane"] == b.SOURCE_LANE_REL.as_posix()),
    ("source_builder", lambda s: s.p["source"]["builder"].endswith("v0951.py")),
    ("source_artifact", lambda s: s.p["source"]["artifact"].endswith("60t_reference.step")),
    ("source_artifact_sha", lambda s: s.p["source"]["sha256"]["cad/drive_htd5m_60t_reference.step"] == "bc3e00bca0db5fe4c3975b5904ad4f72faa2b3fe6822057522c12df16ec0d256"),
    ("profile_sha", lambda s: s.p["source"]["sha256"]["source_reuse_snapshot/htd5m_profile.py"] == "77f3e18eb14e2956213eddfc84529264585451c2014d0a8325229e368ede54e1"),
    ("teeth", lambda s: s.v["geometry"]["pulley"]["tooth_count"] == 60),
    ("pitch_family", lambda s: s.v["geometry"]["pulley"]["pitch_family"] == "HTD5M"),
    ("pitch", lambda s: s.v["geometry"]["pulley"]["pitch_mm"] == 5.0),
    ("spacing", lambda s: s.v["geometry"]["pulley"]["angular_spacing_deg"] == 6.0),
    ("face_width", lambda s: s.v["geometry"]["pulley"]["tooth_face_width_mm"] == 16.0),
    ("profile_revision", lambda s: s.v["geometry"]["tooth_preservation"]["profile_modification_count"] == 0),
    ("tooth_removed", lambda s: s.v["geometry"]["tooth_preservation"]["removed_volume_mm3"] == 0),
    ("tooth_added", lambda s: s.v["geometry"]["tooth_preservation"]["added_volume_mm3"] == 0),
    ("source_tip60", lambda s: s.v["geometry"]["tooth_preservation"]["source_tip_faces"]["count"] == 60),
    ("final_tip60", lambda s: s.v["geometry"]["tooth_preservation"]["final_tip_faces"]["count"] == 60),
    ("tip_spacing_min", lambda s: s.v["geometry"]["tooth_preservation"]["final_tip_faces"]["spacing_min_deg"] == 6.0),
    ("tip_spacing_max", lambda s: s.v["geometry"]["tooth_preservation"]["final_tip_faces"]["spacing_max_deg"] == 6.0),
    ("exact_reuse", lambda s: s.v["geometry"]["tooth_preservation"]["exact_reuse_pass"] is True),
    ("architecture", lambda s: s.v["geometry"]["pulley"]["architecture"].startswith("ONE_PIECE")),
    ("pulley_valid", lambda s: s.v["geometry"]["pulley"]["valid"] is True),
    ("pulley_single", lambda s: s.v["geometry"]["pulley"]["solid_count"] == 1),
    ("overall_od", lambda s: close(s.v["geometry"]["pulley"]["overall_dimensions_mm"][0],102.0)),
    ("overall_od_y", lambda s: close(s.v["geometry"]["pulley"]["overall_dimensions_mm"][1],102.0)),
    ("overall_height", lambda s: close(s.v["geometry"]["pulley"]["overall_dimensions_mm"][2],34.0)),
    ("hub_od", lambda s: s.v["geometry"]["clamp"]["hub_od_mm"] == 34.0),
    ("hub_width", lambda s: s.v["geometry"]["clamp"]["hub_width_mm"] == 26.0),
    ("shaft", lambda s: s.v["geometry"]["clamp"]["shaft_nominal_mm"] == 10.0),
    ("bore_primary", lambda s: s.v["geometry"]["clamp"]["bore_primary_candidate_mm"] == 10.2),
    ("bore_candidates", lambda s: s.p["clamp"]["bore_candidates_mm"] == [10.1,10.2,10.3]),
    ("coupons", lambda s: len([x for x in b.CAD if "coupon_b" in x]) == 3),
    ("split", lambda s: s.v["geometry"]["clamp"]["split_exists"] is True),
    ("split_width", lambda s: s.v["geometry"]["clamp"]["split_width_mm"] == 1.3),
    ("split_hold", lambda s: s.v["geometry"]["clamp"]["split_gap_physical_closure"] == "PHYSICAL_HOLD"),
    ("m4_count", lambda s: s.v["geometry"]["clamp"]["m4_count"] == 2),
    ("m4_holes", lambda s: s.v["geometry"]["clamp"]["m4_clearance_hole_mm"] == 4.5),
    ("metal_hardware", lambda s: "METAL_M4_NUT" in s.v["geometry"]["clamp"]["hardware"]),
    ("washers", lambda s: s.p["clamp"]["metal_washer_min_count"] == 4),
    ("petg_threads_zero", lambda s: s.v["geometry"]["clamp"]["petg_tapped_thread_count"] == 0),
    ("no_nut_pocket", lambda s: s.v["geometry"]["clamp"]["captured_nut_pocket"].startswith("NOT_USED")),
    ("wall", lambda s: s.v["geometry"]["clamp"]["hub_nominal_wall_mm"] >= 11.8),
    ("bore_m4_wall", lambda s: s.v["geometry"]["clamp"]["bore_to_m4_min_mm"] >= 3.0),
    ("ear_min", lambda s: s.v["geometry"]["clamp"]["clamp_ear_min_mm"] >= 4.0),
    ("ear_fillet", lambda s: s.v["geometry"]["clamp"]["ear_corner_fillet_mm"] == 3.0),
    ("spokes", lambda s: s.v["geometry"]["structure"]["spoke_count"] == 6),
    ("spoke_width", lambda s: 8 <= s.v["geometry"]["structure"]["spoke_width_mm"] <= 12),
    ("lightening_zero", lambda s: s.v["geometry"]["structure"]["decorative_lightening_hole_count"] == 0),
    ("rim", lambda s: 8 <= s.v["geometry"]["pulley"]["rim_min_radial_mm"] <= 10),
    ("flanges", lambda s: s.v["geometry"]["pulley"]["flange_count"] == 2),
    ("flange_od", lambda s: s.v["geometry"]["pulley"]["flange_od_mm"] == 102),
    ("belt_plane", lambda s: s.v["geometry"]["belt_alignment"]["belt_plane_error_mm"] == 0),
    ("belt_width", lambda s: s.v["geometry"]["belt_alignment"]["nominal_belt_width_mm"] == 15),
    ("belt_hold", lambda s: s.v["geometry"]["belt_alignment"]["exact_successful_belt_solid"].startswith("HOLD")),
    ("local_collision", lambda s: s.v["geometry"]["clearance"]["local_non_intended_intersection_count"] == 0),
    ("global_hold", lambda s: s.v["geometry"]["clearance"]["global_non_intended_intersection"].startswith("HOLD")),
    ("tool_clearance", lambda s: s.v["geometry"]["clearance"]["tool_to_flange_axial_clearance_mm"] >= 2.0),
    ("tool_hold", lambda s: "HOLD_ACTUAL" in s.v["geometry"]["clearance"]["tool_access"]),
    ("printer", lambda s: s.v["geometry"]["print"]["printer"] == "Bambu Lab A1"),
    ("petg", lambda s: s.v["geometry"]["print"]["material"] == "PETG"),
    ("orientation", lambda s: s.v["geometry"]["print"]["axis"] == "Z" and s.v["geometry"]["print"]["flat_on_bed"]),
    ("support_hold", lambda s: "HOLD_SLICER" in s.v["geometry"]["print"]["support"]),
    ("walls", lambda s: s.v["geometry"]["print"]["walls_min"] >= 6),
    ("p20653_zero", lambda s: s.p["scope"]["p20653_modification_count"] == 0),
    ("guard_zero", lambda s: s.p["scope"]["crawler_guard_modification_count"] == 0),
    ("20t_zero", lambda s: s.p["scope"]["drive_20t_modification_count"] == 0),
    ("belt_redesign_zero", lambda s: s.p["scope"]["belt_redesign_count"] == 0),
    ("frame_zero", lambda s: s.p["scope"]["frame_redesign_count"] == 0),
    ("paths", lambda s: s.verify["path_count"] == 40),
    ("steps", lambda s: s.verify["step_count"] == 2),
    ("stls", lambda s: s.verify["stl_count"] == 5),
    ("svgs", lambda s: s.verify["svg_count"] == 6),
    ("step_valid", lambda s: all(x["valid"] for x in s.v["geometry"]["step_import"].values())),
    ("mesh_count", lambda s: len(s.v["geometry"]["mesh"]) == 5),
    ("mesh_water", lambda s: all(x["watertight"] for x in s.v["geometry"]["mesh"].values())),
    ("mesh_edges", lambda s: all(x["bad_edge_count"] == 0 for x in s.v["geometry"]["mesh"].values())),
    ("mesh_degenerate", lambda s: all(x["degenerate_triangle_count"] == 0 for x in s.v["geometry"]["mesh"].values())),
    ("main_component", lambda s: s.v["geometry"]["mesh"][b.CAD[1]]["component_count"] == 1),
    ("coupon_components", lambda s: all(s.v["geometry"]["mesh"][x]["component_count"] == 1 for x in b.CAD[2:5])),
    ("plate_components", lambda s: s.v["geometry"]["mesh"][b.CAD[5]]["component_count"] == 3),
    ("bore_meshes", lambda s: all("bore_mesh" in s.v["geometry"]["mesh"][x] for x in [b.CAD[1],*b.CAD[2:5]])),
    ("bore_targets", lambda s: [s.v["geometry"]["mesh"][x]["bore_mesh"]["target_mm"] for x in b.CAD[2:5]] == [10.1,10.2,10.3]),
    ("mesh_split", lambda s: all(close(s.v["geometry"]["mesh"][x]["bore_mesh"]["split_gap_mm"],1.3,0.01) for x in [b.CAD[1],*b.CAD[2:5]])),
    ("commit_paths", lambda s: len((LANE/"COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == 40),
    ("first_print", lambda s: s.p["gates"]["first_print"] == "COUPONS_ONLY"),
    ("full_after_coupon", lambda s: s.p["gates"]["full_pulley_print"] == "AFTER_COUPON_SELECTION"),
    ("full_torque", lambda s: s.p["gates"]["full_torque"] == "NOT_APPROVED"),
    ("status", lambda s: "EXACT_WORKING_60T_TOOTH_GEOMETRY_REUSED" in s.verify["status"] and "COMMIT_READY_NOT_STAGED" in s.verify["status"]),
]

def make_test(name, fn):
    def test(self): self.assertTrue(fn(self), name)
    return test
for index,(name,fn) in enumerate(C,1): setattr(Contract,f"test_{index:03d}_{name}",make_test(name,fn))

if __name__ == "__main__":
    print(f"CONTRACT_COUNT={len(C)}")
    unittest.main(verbosity=2)
