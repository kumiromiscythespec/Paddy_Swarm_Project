"""Executable contract for the v0.9.6.31 F570 full 14T print lane."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_p20653_14t_18025_f570_full_drive_print_candidate_v0_9_6_31.py"
spec = importlib.util.spec_from_file_location("paddy_v09631_contract", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import builder")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def main() -> int:
    passed: list[str] = []
    failed: list[str] = []

    def check(name: str, condition: bool) -> None:
        (passed if condition else failed).append(name)

    result = b.verify()
    report = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
    geom = report["geometry"]
    repo = result["repository"]
    support = geom["support"]
    placement = geom["placement"]
    frozen = geom["frozen_parent"]
    selected = geom["selected_flange"]
    tensioner = geom["tensioner"]

    check("repository", Path(repo["repository"]).resolve() == b.REPO_ROOT.resolve())
    check("branch", repo["branch"] == b.EXPECTED_BRANCH)
    check("head", repo["head"] == b.EXPECTED_HEAD)
    check("staged_zero", repo["staged"] == [])
    check("tracked_dirty_exact", repo["tracked_dirty"] == b.TRACKED_DIRTY)
    check("outside_snapshot", tuple(repo["outside_untracked"]) == (b.BASE_OUTSIDE_COUNT, b.BASE_OUTSIDE_PATH_DIGEST))
    check("lane_complete", repo["lane_files"] == b.EXPECTED_PATH_COUNT)
    check("lane_cache_zero", repo["cache"] == [])
    check("lane_forbidden_zero", repo["forbidden"] == [])
    check("lane_ignored_zero", repo["ignored_lane"] == [])

    for rel, expected in b.AUTHORITY_SHA256.items():
        check(f"authority_{rel}", repo["authority_sha256"][rel] == expected)
    for rel, expected in b.SOURCE_SHA256.items():
        check(f"source_{rel}", repo["source_sha256"][rel] == expected)
    for rel, expected in b.PROTECTED_LANES.items():
        row = repo["protected_lanes"][rel]
        check(f"protected_count_{rel}", row["count"] == expected[0])
        check(f"protected_sha_{rel}", row["tree_sha256"] == expected[1])
        check(f"protected_status_{rel}", row["status"] == "UNCHANGED")

    actual_files = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file())
    manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    commits = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    check("path_count_20", len(actual_files) == 20)
    check("files_exact", actual_files == b.EXPECTED_FILES)
    check("manifest_exact", manifest == b.EXPECTED_FILES)
    check("commit_paths_count", len(commits) == 20)
    check("commit_paths_exact", commits == [f"{b.LANE_REL.as_posix()}/{rel}" for rel in b.EXPECTED_FILES])
    for rel in b.EXPECTED_FILES:
        check(f"manifest_member_{rel}", rel in manifest)

    check("version", report["version"] == "v0.9.6.31")
    check("classification", report["classification"] == b.CLASSIFICATION)
    check("status", report["status"] == b.STATUS)
    check("f570_candidate", selected["candidate"] == "F570")
    check("f570_diameter", math.isclose(selected["pocket_diameter_mm"], 57.0, abs_tol=1e-12))
    check("pocket_depth", selected["pocket_depth_mm"] == 6.2)
    check("f569_tight", selected["physical_proxy_results"]["F569"]["result"] == "FAIL_TIGHT")
    check("f570_pass", selected["physical_proxy_results"]["F570"]["result"] == "PASS_SELECTED")
    check("f571_loose", selected["physical_proxy_results"]["F571"]["result"] == "FAIL_LOOSE")
    check("actual_18025_hold", selected["actual_18025_fit"] == "NOT_YET_PART_NOT_RECEIVED")

    check("tooth_count_14", frozen["tooth_count"] == 14)
    check("pitch", math.isclose(frozen["pitch_mm"], 20.6533333333, abs_tol=1e-10))
    check("pitch_diameter", math.isclose(frozen["pitch_diameter_mm"], 92.8152374974, abs_tol=1e-9))
    check("phase", math.isclose(frozen["phase_deg"], 12.857142857142858, abs_tol=1e-12))
    check("spacing", math.isclose(frozen["spacing_deg"], 25.714285714285715, abs_tol=1e-12))
    check("tooth_width", frozen["tooth_width_mm"] == 44.0)
    check("idler_12", frozen["idler_tooth_count"] == 12)
    check("tooth_regression", frozen["tooth_regression"]["all_14_pass"] is True)
    check("tooth_added_zero", frozen["tooth_regression"]["max_added_volume_mm3"] == 0.0)
    check("tooth_removed_zero", frozen["tooth_regression"]["max_removed_volume_mm3"] == 0.0)

    check("support_width", support["width_mm"] == 44.0)
    check("link_intersection_zero", support["link_swept_intersection_max_mm3"] == 0.0)
    check("link_clearance_hard", support["link_swept_clearance_mm"] >= 0.8)
    check("link_clearance_value", math.isclose(support["link_swept_clearance_mm"], 0.8772255106742008, abs_tol=1e-9))
    check("link_target_miss", support["link_swept_clearance_mm"] < 1.0)
    check("ligament_hard", support["f570_pocket_to_continuous_ring_ligament_mm"] >= 5.0)
    check("ligament_target_miss", support["f570_pocket_to_continuous_ring_ligament_mm"] < 6.0)
    check("vendor_flange_root", math.isclose(support["vendor_flange_to_tooth_root_mm"], 5.620730891077322, abs_tol=1e-9))

    check("tension_available", tensioner["available_inward_mm"] >= 10.0)
    check("tension_required", math.isclose(tensioner["required_inward_mm"], 2.5801, abs_tol=1e-12))
    check("tension_service", tensioner["service_margin_mm"] == 2.0)
    check("tension_total", math.isclose(tensioner["required_with_margin_mm"], 4.5801, abs_tol=1e-12))
    check("tension_residual", tensioner["residual_mm"] >= 5.4199)
    check("tension_gate", tensioner["physical_gate"] == "PASS")

    check("frame_zero", placement["frame"]["intersection_mm3"] == 0.0)
    check("frame_positive_distance", placement["frame"]["minimum_distance_mm"] > 0.0)
    check("lower_roller_zero", placement["lower_rollers"]["intersection_mm3"] == 0.0)
    check("lower_roller_positive_distance", placement["lower_rollers"]["minimum_distance_mm"] > 0.0)
    check("lower_station_hold", placement["lower_rollers"]["station_registration"] == "HOLD_ACTUAL_LOWER_ROLLER_STATIONS")
    check("hold_down_zero", placement["hold_down_roller"]["max_unintended_intersection_mm3"] == 0.0)
    for row in placement["hold_down_roller"]["rows"]:
        check(f"hold_roller_zero_{row['push_mm']}", row["drive_vs_rollers_mm3"] == 0.0)
        check(f"hold_carriage_zero_{row['push_mm']}", row["drive_vs_carriage_mm3"] == 0.0)
        check(f"hold_roller_distance_{row['push_mm']}", row["drive_to_rollers_distance_mm"] > 0.0)
        check(f"hold_carriage_distance_{row['push_mm']}", row["drive_to_carriage_distance_mm"] > 0.0)
    check("straight_run_zero", placement["crawler_straight_run"]["intersection_mm3"] == 0.0)
    check("straight_run_entry", placement["crawler_straight_run"]["keepout_end_x_mm"] == -26.0)
    check("straight_wrap_intended", placement["crawler_straight_run"]["wrap_sector_contract"] == "INTENDED_MESH_CHECKED_BY_EXACT_LINK_SWEEP")
    check("idler_range_zero", placement["idler_adjustment_range"]["max_intersection_mm3"] == 0.0)
    check("idler_range", placement["idler_adjustment_range"]["screened_center_distance_range_mm"] == [270.0, 280.0])
    for row in placement["idler_adjustment_range"]["rows"]:
        check(f"idler_zero_{row['center_distance_mm']}", row["drive_vs_12t_idler_mm3"] == 0.0)
        check(f"idler_distance_{row['center_distance_mm']}", row["drive_to_12t_idler_distance_mm"] > 0.0)
    check("physical_screen", placement["physical_observation"] == "USER_CONFIRMED_LARGE_PLACEMENT_MARGIN_SCREEN_PASS")
    check("final_physical_hold", placement["final_physical_clearance"] == "NOT_YET_ACTUAL_ASSEMBLY_RETEST_REQUIRED")

    m5 = geom["m5"]
    check("m5_count", m5["count"] == 6)
    check("m5_pcd", m5["pcd_mm"] == 47.5)
    check("m5_petg_hole", m5["petg_clearance_mm"] == 5.5)
    check("m5_head_side", m5["head_side"] == "18025_METAL_FLANGE_SIDE")
    check("m5_locknut_side", m5["opposite_side"] == "METAL_FLAT_WASHER_PLUS_METAL_LOCKNUT")
    check("m5_no_petg_tap", m5["petg_tap"] == "PROHIBITED")
    check("m5_no_captive", m5["captive_nut"] == "PROHIBITED")
    check("m5_access", m5["cad_access"] == "PASS_OPEN_COUNTERBORE")

    check("step_count", result["step_count"] == 2)
    check("stl_count", result["stl_count"] == 1)
    check("svg_count", result["svg_count"] == 3)
    for rel, row in result["step_import"].items():
        check(f"step_valid_{rel}", row["valid"] is True)
        check(f"step_reload_{rel}", row["reload"] == "PASS")
    for rel, row in result["mesh"].items():
        check(f"stl_watertight_{rel}", row["watertight"] is True)
        check(f"stl_bad_edge_{rel}", row["bad_edge_count"] == 0)
        check(f"stl_degenerate_{rel}", row["degenerate_triangle_count"] == 0)
        check(f"stl_component_{rel}", row["component_count"] == 1)
        check(f"stl_reload_{rel}", row["reload"] == "PASS")

    for name, value in report["checks"].items():
        check(f"validation_not_fail_{name}", value != "FAIL")
    check("print_gate", report["print_gate"]["FULL_14T_PRINT_GATE"] == "PASS")
    check("single_print", report["print_gate"]["FULL_14T_SINGLE_PART_PRINT"] == "APPROVED")
    check("print_quantity", report["print_gate"]["quantity"] == 1)
    check("first_print", report["print_gate"]["first_print"] == b.FULL_STL)
    check("powered_not_approved", report["checks"]["powered"] == "NOT_APPROVED")
    check("static_hold", report["checks"]["static_6p5nm"] == "NOT_YET")
    check("field_hold", report["checks"]["field"] == "NOT_YET")

    if failed:
        raise AssertionError(json.dumps({"failed": failed, "passed": len(passed)}, ensure_ascii=False, indent=2))
    print(json.dumps({"tests": len(passed), "passed": len(passed), "failed": 0, "status": "PASS"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
