"""Executable contract for the v0.9.6.37 dual-ejector service lane."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_p20653_14t_18025_f570_dual_ejector_service_v0_9_6_37.py"
spec = importlib.util.spec_from_file_location("dual_ejector_v09637", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("builder import")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

passed: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    passed.append(name)


result = m.verify()
report = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
geom = report["geometry"]
frozen = geom["frozen_parent"]
delta = geom["delta"]
rows = delta["access_rows"]
structural = geom["structural"]
repo = result["repository"]

check("repository_root", Path(repo["repository"]).resolve() == m.REPO_ROOT.resolve())
check("branch", repo["branch"] == m.EXPECTED_BRANCH)
check("head", repo["head"] == m.EXPECTED_HEAD)
check("staged_zero", repo["staged"] == [])
check("tracked_dirty_preserved", repo["tracked_dirty"] == m.TRACKED_DIRTY)
check("outside_untracked_preserved", tuple(repo["outside_untracked"]) == (m.BASE_OUTSIDE_COUNT, m.BASE_OUTSIDE_PATH_DIGEST))
check("authority_4", repo["authority_sha256"] == m.AUTHORITY_SHA256)
check("protected_lane_count", repo["protected_lanes"]["lane_count"] == 37)
check("protected_file_count", repo["protected_lanes"]["file_count"] == 1612)
check("protected_aggregate", repo["protected_lanes"]["aggregate_sha256"] == m.PROTECTED_AGGREGATE_SHA256)
check("parent_tree", repo["parent_tree"] == {"file_count": m.PARENT_TREE_COUNT, "tree_sha256": m.PARENT_TREE_SHA256})
check("source_sha", repo["source_sha256"] == m.SOURCE_SHA256)
check("exact_paths", result["path_count"] == m.EXPECTED_PATH_COUNT == 23)
check("manifest", (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == m.EXPECTED_FILES)
check("commit_paths", len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == 23)
check("sha_mismatch_zero", result["sha_mismatch_count"] == 0)

check("f570_exact", frozen["f570_pocket_d_mm"] == 57.00)
check("pitch_frozen", math.isclose(frozen["p20653_pitch_mm"], 20.6533333333, abs_tol=1e-10))
check("tooth_count_14", frozen["tooth_count"] == 14)
check("pitch_diameter", math.isclose(frozen["pitch_diameter_mm"], 92.8152374974, abs_tol=1e-9))
check("phase_frozen", math.isclose(frozen["phase_deg"], 360.0 / 14.0 / 2.0, abs_tol=1e-12))
check("spacing_frozen", math.isclose(frozen["spacing_deg"], 360.0 / 14.0, abs_tol=1e-12))
check("width_44", frozen["tooth_width_mm"] == 44.0)
check("pilot_24p10", frozen["center_pilot_d_mm"] == 24.10 and frozen["center_pilot_length_mm"] == 4.0)
check("relief_24p50", frozen["deep_relief_d_mm"] == 24.50)
check("pocket_depth_6p20", frozen["flange_pocket_depth_mm"] == 6.20)
check("vendor_flange_boss", frozen["hub_flange_od_mm"] == 56.8 and frozen["hub_boss_od_mm"] == 24.0)
check("pcd_m5", frozen["pcd_mm"] == 47.5 and frozen["m5_count"] == 6)
check("idler_unchanged", frozen["idler_tooth_count"] == 12 and frozen["idler_change_count"] == 0)

check("delta_subtractive_only", delta["operation"] == "SUBTRACT_TWO_CYLINDRICAL_SERVICE_ACCESS_PATHS_ONLY")
check("added_volume_zero", delta["added_volume_mm3"] == 0.0)
check("removed_volume_positive", delta["removed_volume_mm3"] > 0.0)
check("ejector_count", delta["ejector_count"] == 2 and len(rows) == 2)
check("ejector_diameter", delta["access_d_mm"] == 5.0)
check("ejector_radius", delta["radius_mm"] == 20.0)
check("ejector_angles", delta["angles_deg"] == [30.0, 210.0])
check("ejector_spacing", delta["angular_spacing_deg"] == 180.0)
check("tool_proxy", delta["tool_proxy_d_mm"] == 4.0)
check("tool_depth", math.isclose(delta["insertion_depth_mm"], 37.8, abs_tol=1e-12))

check("boss_clearance", min(row["deep_relief_boss_clearance_mm"] for row in rows) >= 5.25)
check("metal_boss_clearance", min(row["metal_boss_clearance_mm"] for row in rows) >= 5.5)
check("shaft_clearance", min(row["shaft_clearance_mm"] for row in rows) >= 12.25)
check("m5_clearance", min(row["m5_petg_hole_clearance_mm"] for row in rows) >= 6.6385)
check("counterbore_clearance", min(row["counterbore_clearance_mm"] for row in rows) >= 3.3885)
check("flange_edge", min(row["metal_flange_outer_edge_clearance_mm"] for row in rows) >= 5.9)
check("pocket_edge", min(row["f570_pocket_edge_clearance_mm"] for row in rows) >= 6.0)
check("root_clearance", min(row["tooth_root_clearance_mm"] for row in rows) >= 11.52)
check("tooth_intersection_zero", max(row["tooth_solid_intersection_max_mm3"] for row in rows) == 0.0)
check("drain_intersection_zero", max(row["drain_intersection_mm3"] for row in rows) == 0.0)
check("tool_petg_intersection_zero", max(row["tool_to_petg_intersection_mm3"] for row in rows) == 0.0)
check("tool_key_intersection_zero", max(row["tool_to_key_intersection_mm3"] for row in rows) == 0.0)
check("flange_contact", min(row["tool_to_metal_flange_contact_mm3"] for row in rows) > 0.0)
check("two_paths_usable", geom["service_access"]["two_holes_usable"] is True)
check("opposed_push", geom["service_access"]["opposed_push"] is True)

check("continuous_ring_uncut", structural["continuous_ring_cut_volume_mm3"] == 0.0)
check("continuous_ligament", structural["f570_to_continuous_ring_ligament_mm"] >= 5.0)
check("link_swept_clearance", structural["link_swept_clearance_mm"] >= 0.8)
check("link_swept_intersection_zero", structural["link_swept_intersection_mm3"] == 0.0)
check("frame_collision_zero", geom["placement"]["frame"]["intersection_mm3"] == 0.0)
check("roller_collision_zero", geom["placement"]["lower_rollers"]["intersection_mm3"] == 0.0)
check("crawler_collision_zero", geom["placement"]["crawler_straight_run"]["intersection_mm3"] == 0.0)

check("step_count", result["step_count"] == 2)
check("stl_count", result["stl_count"] == 1)
check("svg_count", result["svg_count"] == 5)
check("step_reload", all(row["reload"] == "PASS" and row["valid"] for row in result["step_import"].values()))
mesh = result["mesh"][m.FULL_STL]
check("stl_watertight", mesh["watertight"] is True)
check("stl_bad_edges", mesh["bad_edge_count"] == 0)
check("stl_degenerate", mesh["degenerate_triangle_count"] == 0)
check("stl_one_component", mesh["component_count"] == 1)

check("physical_f570", geom["physical_record"]["f570_physical_fit"] == "PASS")
check("hub_self_fallout_none", geom["physical_record"]["hub_self_fallout"] == "NONE")
check("identity_hold", geom["physical_record"]["actual_18025_identity"].startswith("HOLD"))
check("ejector_physical_not_yet", geom["physical_record"]["ejector_physical_pass"] == "NOT_YET")
check("single_print_approved", report["print_gate"]["FULL_14T_SINGLE_PRINT_APPROVED"] == "PASS")
check("powered_not_approved", report["checks"]["powered"] == "NOT_APPROVED")
check("no_fail_checks", all(value != "FAIL" for value in report["checks"].values()))

print(json.dumps({"contract": "PASS", "checks_passed": len(passed), "checks": passed}, indent=2))
