"""Executable production contract for the v0.9.6.37 top-insert BBOX."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_top_insert_bbox_v0_9_6_37.py"
spec = importlib.util.spec_from_file_location("top_insert_bbox_v09637", BUILDER)
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
a = report["analysis"]
repo = result["repository"]

# Repository and immutable input contract.
check("repository", Path(repo["repository"]).resolve() == m.REPO_ROOT.resolve())
check("branch", repo["branch"] == m.EXPECTED_BRANCH)
check("head", repo["head"] == m.EXPECTED_HEAD)
check("staged_zero", repo["staged"] == [])
check("dirty_preserved", repo["tracked_dirty"] == m.TRACKED_DIRTY)
check("outside_preserved", tuple(repo["outside_untracked"]) == (m.BASE_OUTSIDE_COUNT, m.BASE_OUTSIDE_PATH_DIGEST))
check("authority_4", repo["authority_sha256"] == m.AUTHORITY_SHA256)
check("protected_lane_count", repo["protected_lanes"]["lane_count"] == m.PROTECTED_LANE_COUNT)
check("protected_file_count", repo["protected_lanes"]["file_count"] == m.PROTECTED_FILE_COUNT)
check("protected_aggregate", repo["protected_lanes"]["aggregate_sha256"] == m.PROTECTED_AGGREGATE_SHA256)
check("focus_trees", all(repo["focus_trees"][rel]["tree_sha256"] == row[1] for rel, row in m.FOCUS_TREES.items()))
check("source_sha", repo["source_sha256"] == m.SOURCE_SHA256)
check("exact_path_count", result["path_count"] == m.EXPECTED_PATH_COUNT == 38)
check("manifest_exact", (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == m.EXPECTED_FILES)
check("commit_paths_exact", len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == 38)
check("sha_zero", result["sha_mismatch_count"] == 0)

# Physical authority, including the explicit arithmetic audit.
measure = a["measurement_authority"]
check("plan_raw", measure["frame_plan_raw_unordered_mm"] == [124.0, 125.0])
check("height_131", measure["frame_internal_height_mm"] == 131.0)
check("idler_height_24", measure["rear_idler_interference_height_mm"] == 24.0)
check("user_effective_109", measure["user_effective_height_mm"] == 109.0)
check("arithmetic_107", measure["arithmetic_131_minus_24_mm"] == 107.0)
check("discrepancy_recorded", measure["arithmetic_discrepancy_mm"] == 2.0)
check("governing_109", measure["governing_cad_height_mm"] == 109.0)
check("axis_neutral", measure["axis_mapping"] == "Z_131_CONFIRMED_XY_ORDER_NEUTRALIZED_BY_SQUARE_PLAN")
check("cable_od", measure["cable_od_mm"] == 9.6)

# Production body and rear relief.
body = a["body"]
check("outer_dims", body["outer_xyz_mm"] == [122.0, 122.0, 109.0])
check("square_plan", body["outer_xyz_mm"][0] == body["outer_xyz_mm"][1])
check("inner_upper", body["inner_upper_xyz_mm"] == [116.0, 116.0, 75.0])
check("top_opening", body["top_opening_xy_mm"] == [110.0, 110.0])
check("wall_3", body["wall_mm"] == 3.0)
check("floor_4", body["front_floor_mm"] == 4.0)
check("frame_clearance", body["frame_clearance_per_side_mm"] == [1.0, 1.5])
check("body_valid", body["primary_valid"] is True)
check("body_bbox", body["bbox_mm"] == [122.0, 122.0, 109.0])
relief = body["rear_relief"]
check("relief_height", relief["height_mm"] == 24.0)
check("relief_depth", relief["depth_mm"] == 10.0)
check("relief_roof", relief["roof_mm"] == 4.0)
check("relief_self_support", relief["form"] == "SELF_SUPPORTING_TRIANGULAR_REAR_BOTTOM_RELIEF")
check("relief_cut_complete", relief["body_intersection_mm3"] == 0)

# Battery top insertion and clearance contract.
battery = a["battery"]
check("historic_reference_preserved", battery["nominal_repository_reference_mm"] == [150.9, 99.4, 92.5])
check("production_keepout", battery["production_keepout_xyz_mm"] == [102.0, 99.4, 99.0])
check("battery_height_99", battery["physical_height_mm"] == 99.0)
check("terminal_top", battery["terminal_side"] == "TOP")
check("dummy_fit", battery["dummy_fit"] == "PHYSICAL_PASS")
check("top_insert", battery["insertion_direction"] == "+Z_TOP")
check("battery_collision_zero", battery["body_collision_mm3"] == 0)
check("sweep_six", len(battery["sweep_collision_mm3"]) == 6)
check("sweep_zero", max(battery["sweep_collision_mm3"]) == 0)
check("z_clearance_6", battery["height_clearance_mm"] == 6.0)
check("lower_x_clearance", battery["lower_cavity_clearance_x_per_side_mm"] == 7.0)
check("lower_y_positive", min(battery["lower_cavity_clearance_y_front_rear_mm"]) > 0)
check("top_open_x_clearance", battery["top_opening_clearance_x_per_side_mm"] == 4.0)
check("top_open_y_positive", min(battery["top_opening_clearance_y_front_rear_mm"]) > 0)

# Lid, gasket, closure and top cable service.
seal = a["lid_gasket_cable"]
check("lid_plate", seal["lid_plate_mm"] == 7.0)
check("lid_bbox", seal["lid_bbox_mm"] == [122.0, 122.0, 11.0])
check("gasket_closed", seal["gasket_closed_loop"] is True)
check("gasket_dims", seal["gasket_xyz_mm"] == [118.0, 118.0, 3.0])
check("compression_range", seal["gasket_compression_percent"] == [20.0, 25.0])
check("groove", seal["groove_depth_mm"] == 2.3)
check("hard_stop_compression", seal["nominal_compression_percent_at_hard_stop"] == 23.333)
check("seal_land_hard_min", seal["seal_land_mm"] == 6.0)
check("m4_candidate", seal["fastener"] == "M4_HEAT_SET_INSERT_PATTERN_CANDIDATE")
check("m4_count", seal["fastener_count"] == 8)
check("fastener_outside_gasket", seal["fastener_gasket_intersection_mm3"] == 0)
check("lid_body_intersection_zero", seal["lid_body_intersection_mm3"] == 0)
check("compressed_gasket_lid_intersection_zero", seal["compressed_gasket_lid_intersection_mm3"] == 0)
check("compressed_gasket_body_intersection_zero", seal["compressed_gasket_body_intersection_mm3"] == 0)
check("cable_od_9p6", seal["cable_od_mm"] == 9.6)
check("cable_channel_12", seal["channel_width_mm"] == 12.0)
check("cable_clearance", abs(seal["channel_lateral_clearance_per_side_mm"] - 1.2) < 1e-9)
check("gland_pad", seal["gland_pad_od_mm"] == 24.0)
check("no_unreleased_penetration", seal["waterproof_penetration_d_mm"] == 0.0)

# CAD/mesh/reload outputs.
check("step_count", result["step_count"] == 6)
check("stl_count", result["stl_count"] == 3)
check("svg_count", result["svg_count"] == 9)
check("production_steps_exist", all((LANE / rel).exists() for rel in m.PRODUCTION_CAD if rel.endswith(".step")))
check("production_stls_exist", all((LANE / rel).exists() for rel in m.PRODUCTION_CAD if rel.endswith(".stl")))
steps = result["artifacts"]["step"]
meshes = result["artifacts"]["stl"]
check("step_six", len(steps) == 6)
check("step_reload", all(row["reload"] == "PASS" and row["valid"] for row in steps.values()))
check("step_solids", all(row["solid_count"] >= 1 for row in steps.values()))
check("mesh_three", len(meshes) == 3)
check("mesh_reload", all(row["reload"] == "PASS" for row in meshes.values()))
check("mesh_watertight", all(row["watertight"] for row in meshes.values()))
check("mesh_manifold", all(row["manifold"] for row in meshes.values()))
check("mesh_bad_edge_zero", all(row["bad_edge_count"] == 0 for row in meshes.values()))
check("mesh_degenerate_zero", all(row["degenerate_triangle_count"] == 0 for row in meshes.values()))
check("mesh_single_component", all(row["component_count"] == 1 for row in meshes.values()))

printing = a["printability"]
check("a1", printing["build_volume_mm"] == [256.0, 256.0, 256.0])
check("a1_fit", printing["all_parts_within_build_volume"] is True)
check("bottom_down", printing["body_orientation"] == "BOTTOM_DOWN_TOP_OPEN")
check("support_off", printing["body_support"] == "OFF_PREFERRED")
check("self_supporting_relief", printing["rear_relief_overhang"] == "45_DEG_SELF_SUPPORTING_CANDIDATE")
check("slicer_hold", printing["slicer"] == "HOLD_SLICER_NOT_RUN")

release = a["release"]
check("production_step_complete", release["production_step"] == "COMPLETE_3")
check("production_stl_complete", release["production_stl"] == "COMPLETE_3")
check("first_print_body", release["first_print_filename"] == "artifacts/bbox_top_insert_body.stl")
check("first_print_ready", release["first_print_status"] == "READY_FOR_PHYSICAL_FIRST_PRINT")
check("holds_minimal", len(release["holds"]) == 6)
check("no_fail_checks", all(value != "FAIL" for value in report["checks"].values()))
check("production_status", "PRODUCTION_STEP_STL_COMPLETE" in report["status"])
check("first_print_status", "FIRST_BODY_PRINT_READY" in report["status"])
check("powered_water_prohibited", report["checks"]["powered_water"] == "PROHIBITED")

print(json.dumps({"contract": "PASS", "checks_passed": len(passed), "checks": passed}, indent=2))
