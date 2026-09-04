"""Executable contract for PS-BBOX-WATER-DUMMY-V001."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_bbox_water_dummy_v001.py"
spec = importlib.util.spec_from_file_location("bbox_water_dummy_v001", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("builder import failed")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

checks: list[tuple[str, bool]] = []


def check(name: str, condition: bool) -> None:
    checks.append((name, bool(condition)))
    if not condition:
        raise AssertionError(name)


verify = m.verify()
report = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
analysis = report["analysis"]
guard = report["repository_guard"]
body = analysis["body"]
seal = analysis["seal"]
ballast = analysis["ballast"]
hydro = analysis["hydrostatic"]
printing = analysis["printability"]

check("repository", guard["repository"].lower() == str(m.REPO_ROOT).lower())
check("branch", guard["branch"] == m.EXPECTED_BRANCH)
check("head", guard["head"] == m.EXPECTED_HEAD)
check("staged_zero", guard["staged"] == [])
check("tracked_dirty_preserved", guard["tracked_dirty"] == m.TRACKED_DIRTY)
check("outside_untracked_preserved", tuple(guard["outside_untracked"]) == (m.BASE_OUTSIDE_COUNT, m.BASE_OUTSIDE_PATH_DIGEST))
check("authority_4", guard["authority_sha256"] == m.AUTHORITY_SHA256)
check("protected_lane_count", guard["protected_lanes"]["lane_count"] == m.PROTECTED_LANE_COUNT)
check("protected_file_count", guard["protected_lanes"]["file_count"] == m.PROTECTED_FILE_COUNT)
check("protected_aggregate", guard["protected_lanes"]["aggregate_sha256"] == m.PROTECTED_AGGREGATE_SHA256)
for rel, expected in m.PROTECTED_FOCUS.items():
    actual = guard["protected_lanes"]["focus"][rel]
    check(f"protected_{rel}_count", actual["count"] == expected[0])
    check(f"protected_{rel}_sha", actual["tree_sha256"] == expected[1])
check("authority_unique", guard["source_authority"]["selection"] == "UNIQUE_MATCH_TO_USER_NOMINAL_AND_V228_FIXED_CORE")
for rel, expected in m.SOURCE_SHA256.items():
    check(f"source_hash_{rel}", guard["source_authority"]["hashes"][rel] == expected)
for rel, expected in m.SOURCE_TREE.items():
    row = guard["source_authority"]["trees"][rel]
    check(f"source_tree_count_{rel}", row["count"] == expected[0])
    check(f"source_tree_sha_{rel}", row["tree_sha256"] == expected[1])

check("main_outer_x", body["main_vessel_outer_xy_mm"][0] == 200.0)
check("main_outer_y", body["main_vessel_outer_xy_mm"][1] == 150.0)
check("height_70", body["height_mm"] == 70.0)
check("wall_ge_4", body["wall_mm"] >= 4.0)
check("bottom_ge_5", body["bottom_mm"] >= 5.0)
check("bottom_closed", body["closed_bottom"])
check("penetrations_zero", body["penetration_count"] == 0)
check("primary_valid", body["primary_shape_valid"])
check("mass_positive", body["estimated_petg_mass_g"] > 0)

check("rim_outer_exact", seal["source_rim_outer_xy_mm"] == [200.0, 150.0])
check("rim_inner_exact", seal["source_rim_inner_xy_mm"] == [192.0, 142.0])
check("rim_width_exact", seal["source_rim_width_mm"] == 4.0)
check("rim_section_area_equal", abs(seal["source_rim_section_area_mm2"] - seal["dummy_rim_section_area_mm2"]) < 1e-6)
check("rim_added_zero", seal["regression_added_mm3_at_1mm_section"] < 1e-6)
check("rim_removed_zero", seal["regression_removed_mm3_at_1mm_section"] < 1e-6)
check("source_notches_not_reproduced", not seal["source_drip_notches_reproduced"])
check("source_notches_closed", seal["source_drip_notches_closed_by_task"])
check("gasket_exact_bbox", seal["gasket_bbox_mm"] == [204.0, 154.0, 3.0])
check("gasket_full_rim_overlap", seal["gasket_rim_overlap_mm3_at_nominal_1mm"] > 2700.0)
check("lid_exact_xy", seal["lid_bbox_mm"][:2] == [216.0, 166.0])
check("lid_actual_height", seal["lid_bbox_mm"][2] == 18.5)
check("lid_nominal_contract", seal["lid_nominal_contract_mm"] == [216.0, 166.0, 16.0])
check("lid_body_intersection_zero", seal["lid_body_interference_mm3"] < 1e-6)
check("gasket_body_volume_intersection_zero", seal["gasket_body_interference_mm3"] < 1e-6)
check("lid_gasket_volume_intersection_zero", seal["lid_gasket_interference_mm3"] < 1e-6)
check("source_closure_holes_zero", seal["closure_hole_count_source"] == 0)
check("dummy_closure_holes_zero", seal["closure_hole_count_dummy"] == 0)
check("empty_pattern_alignment", seal["bolt_alignment"] == "PASS_EXACT_EMPTY_SOURCE_PATTERN_NO_HOLES_INVENTED")

check("tower_count_4", ballast["tower_count"] == 4)
check("tower_section_12", ballast["tower_cross_section_mm"] == [12.0, 12.0])
check("tower_center_count", len(ballast["tower_centers_xy_mm"]) == 4)
check("tower_above_lid_4", abs(ballast["tower_above_lid_mm"] - 4.0) < 1e-9)
check("tower_lid_clearance_ge_3", ballast["tower_lid_clearance_min_mm"] >= 3.0)
check("tower_lid_intersections_zero", max(ballast["tower_lid_intersection_each_mm3"]) < 1e-6)
check("tower_bolt_intersection_zero", ballast["tower_bolt_intersection_count"] == 0)
check("plate_reference_only_geometry", ballast["plate_reference_mm"] == [244.0, 196.0, 4.0])
check("plate_lid_clearance_ge_3", ballast["plate_to_lid_clearance_mm"] >= 3.0)
check("ballast_fixing_hold", ballast["physical_fixing"] == "HOLD")
check("load_path_body", ballast["load_path"].endswith("TO_BODY"))

check("pressure_exact", abs(hydro["gauge_pressure_kpa"] - 1.4709975) < 1e-9)
check("displacement_actual_cad_basis", "ACTUAL_CAD_EXTERIOR" in hydro["displacement_basis"])
check("displaced_volume_positive", hydro["displaced_volume_l"] > 2.0)
check("buoyancy_force_positive", hydro["buoyancy_force_n"] > 20.0)
check("kgf_equals_liters", abs(hydro["buoyancy_equivalent_kgf"] - hydro["displaced_volume_l"]) < 1e-9)
check("no_safety_factor", hydro["ballast_value"] == "CAD_REFERENCE_ONLY_NO_SAFETY_FACTOR")

check("bambu_a1", printing["printer"] == "Bambu A1")
check("petg", printing["material"] == "PETG")
check("bottom_down_open_up", printing["orientation"] == "BOTTOM_DOWN_OPEN_UP")
check("a1_fit", printing["a1_fit"])
check("footprint_x_le_256", printing["part_footprint_mm"][0] <= 256.0)
check("footprint_y_le_256", printing["part_footprint_mm"][1] <= 256.0)
check("critical_support_zero", printing["critical_support_count"] == 0)
check("seal_support_zero", printing["support_on_seal_land"] == 0)
check("closed_support_space_zero", printing["new_internal_closed_support_space_count"] == 0)
check("slicer_hold", printing["slicer"] == "HOLD_SLICER_NOT_RUN")

check("geometric_id_three", analysis["geometric_id"]["count"] == 3)
check("geometric_id_seal_zero", analysis["geometric_id"]["seal_land_intersection"] == 0)
check("geometric_id_bottom_zero", analysis["geometric_id"]["bottom_intersection"] == 0)
check("geometric_id_load_face_zero", analysis["geometric_id"]["tower_top_load_face_intersection"] == 0)

check("step_count_2", verify["step"] == 2)
check("stl_count_1", verify["stl"] == 1)
check("svg_count_4", verify["svg"] == 4)
check("exact_path_count", verify["paths"] == m.EXPECTED_PATH_COUNT)
check("commit_paths_exact_count", len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == m.EXPECTED_PATH_COUNT)
check("manifest_exact", (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == m.EXPECTED_FILES)
check("sha_mismatch_zero", verify["sha_mismatches"] == [])
check("all_validation_checks_nonfail", all(value != "FAIL" for value in report["checks"].values()))
check("status_cad_pass", "CAD_PASS" in report["status"])
check("status_contract_pass", "CONTRACT_TEST_PASS" in report["status"])
check("status_print_ready", "PRINT_READY" in report["status"])
check("status_physical_pending", "CAD_COMPLETE_PHYSICAL_VALIDATION_PENDING" in report["status"])
check("physical_pass_absent", "PHYSICAL_PASS" not in json.dumps(report))
check("closure_hold_present", "HOLD_ACTUAL_CLOSURE_METHOD" in report["holds"])
check("physical_result_not_yet", "PHYSICAL_LEAK_RESULT_NOT_YET" in report["holds"])

print(json.dumps({"result": "PASS", "tests": len(checks), "failed": 0}, ensure_ascii=False, indent=2))
