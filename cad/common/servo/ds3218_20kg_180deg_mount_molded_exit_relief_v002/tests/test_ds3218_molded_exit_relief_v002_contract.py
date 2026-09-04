"""Contract for the DS3218 two-stage molded-root relief V002."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_ds3218_molded_exit_relief_v002.py"
spec = importlib.util.spec_from_file_location("ds3218_molded_exit_v002", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("BUILDER_IMPORT_FAILED")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

checks: list[tuple[str, bool]] = []


def check(name: str, condition: bool):
    checks.append((name, bool(condition)))
    if not condition:
        raise AssertionError(name)


data = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
validation = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
check("guard", all(m.guard(True)["checks"].values()))
check("version", data["version"] == m.VERSION)
check("parent_lane", data["parent"]["lane"] == m.PARENT_REL.as_posix())
check("parent_read_only", data["parent"]["status"] == "READ_ONLY_V001_AUTHORITY")
check("parent_hash", data["parent"]["tree_sha256"] == m.PROTECTED[m.PARENT_REL.as_posix()][1])

authority = data["protected_servo_authority"]
check("case", authority["case_lwh_mm"] == [40.0, 20.4, 41.7])
check("mount_envelope", authority["mounting_envelope_mm"] == 54.5)
check("pitch", authority["mount_pitch_xy_mm"] == [49.1, 10.0])
check("servo_hole", authority["servo_hole_diameter_mm"] == 4.6)
check("output", authority["output_axis_xy_mm"] == [10.1, 10.2])
check("horn_radius", authority["horn_radius_mm"] == 30.0)
check("horn_plane", authority["horn_rotation_plane_z_mm"] == 46.2)
check("servo_not_moved", not authority["servo_mount_position_changed"])

physical = data["physical_result"]
check("flex_width", physical["flexible_cable_width_mm"] == 4.4)
check("flex_slot_authority", physical["flexible_cable_slot_authority_mm"] == 6.0)
check("flex_pass", physical["flexible_cable_slot_result"] == "PHYSICAL_PASS")
check("root_width", physical["molded_exit_root_width_mm"] == 6.4)
check("root_top_z", physical["molded_exit_root_top_z_from_servo_bottom_mm"] == 8.6)
check("root_protrusion", physical["molded_exit_root_protrusion_from_case_face_mm"] == 5.1)
check("root_physical_fail", physical["molded_exit_root_interference"] == "PHYSICAL_FAIL")

stage_a = data["two_stage_relief"]["stage_a"]
stage_b = data["two_stage_relief"]["stage_b"]
check("stage_a_name", stage_a["name"] == "FLEXIBLE_CABLE_SLOT")
check("stage_a_width", stage_a["clear_width_mm"] == 6.0)
check("stage_a_preserved", stage_a["status"] == "PHYSICAL_AUTHORITY_PRESERVED")
check("stage_b_name", stage_b["name"] == "MOLDED_ROOT_LOCAL_POCKET")
check("pocket_widths", stage_b["candidate_widths_mm"] == [7.5, 8.0, 8.5])
check("primary_width", stage_b["primary_width_mm"] == 8.0)
check("pocket_height", stage_b["height_mm"] == 10.0)
check("outward_clearance", stage_b["outward_clearance_mm"] == 6.5)
check("vertical_clearance", stage_b["vertical_clearance_mm"] == 1.4)
check("outward_margin", stage_b["outward_margin_mm"] == 1.4)
check("margin_7p5", stage_b["lateral_margin_per_side_mm"]["7.5"] == 0.55)
check("margin_8p0", stage_b["lateral_margin_per_side_mm"]["8.0"] == 0.8)
check("margin_8p5", stage_b["lateral_margin_per_side_mm"]["8.5"] == 1.05)
check("open_shape", stage_b["shape"] == "OPEN_DOWNWARD_AND_OUTWARD_ROUNDED_LOCAL_POCKET")
check("radius", 1.0 <= stage_b["edge_radius_mm"] <= 1.5)
check("xy_approx", data["exit_placement"]["status"] == "MOLDED_EXIT_XY_APPROXIMATED_FROM_EXISTING_MODEL")
check("xy_hold", data["exit_placement"]["hold"] == "DIRECT_XY_PHYSICAL_MEASUREMENT_PENDING")

geometry = validation["geometry"]
check("stage_a_valid", geometry["stage_a_valid"])
check("revised_valid", geometry["revised_valid"])
check("stage_a_one_solid", geometry["stage_a_solids"] == 1)
check("revised_one_solid", geometry["revised_solids"] == 1)
check("removed_positive", geometry["root_pocket_removed_volume_mm3"] > 0)
check("added_zero", geometry["added_volume_mm3"] == 0)
check("outside_delta_zero", geometry["delta_outside_root_pocket_mm3"] == 0)
check("local_subtractive", geometry["local_subtractive_only"])
check("stage_a_interference", geometry["stage_a_root_service_intersection_mm3"] > 0)
check("revised_clear", geometry["revised_root_service_intersection_mm3"] == 0)
check("geometry_flex_slot", geometry["flex_slot_width_mm"] == 6.0)
check("geometry_pocket_widths", geometry["root_pocket_widths_mm"] == [7.5, 8.0, 8.5])
check("geometry_primary", geometry["primary_root_pocket_width_mm"] == 8.0)
check("geometry_height", geometry["root_pocket_height_mm"] == 10.0)
check("geometry_outward", geometry["root_pocket_outward_clearance_mm"] == 6.5)
check("geometry_vertical_margin", geometry["root_vertical_clearance_mm"] == 1.4)
check("geometry_outward_margin", geometry["root_outward_margin_mm"] == 1.4)
check("geometry_lateral_7p5", geometry["lateral_margin_per_side_mm"]["7.5"] == 0.55)
check("geometry_lateral_8p0", geometry["lateral_margin_per_side_mm"]["8.0"] == 0.8)
check("geometry_lateral_8p5", geometry["lateral_margin_per_side_mm"]["8.5"] == 1.05)
check("coupon_valid", len(geometry["coupon_valid"]) == 3 and all(geometry["coupon_valid"].values()))
check("coupon_one_solid", all(value == 1 for value in geometry["coupon_solids"].values()))
check("combined_valid", geometry["combined_valid"])
check("body_unchanged", geometry["body_fit_dimensions_mm"] == [40.0, 20.4, 41.7])
check("mount_centers", geometry["mount_hole_centers_mm"] == [[-4.55, 5.2], [-4.55, 15.2], [44.55, 5.2], [44.55, 15.2]])
check("output_unchanged", geometry["output_axis_mm"] == [10.1, 10.2])
check("horn_unchanged", geometry["horn_keepout_mm"] == [30.0, 2.4, 46.2])
check("wall_safe", geometry["minimum_existing_wall_mm"] >= 2.5)
check("ligament_safe", geometry["minimum_remaining_base_ligament_each_side_mm"] >= 10.0)

check("validation_all", validation["pass_count"] == validation["check_count"])
check("step_count", len(validation["steps"]) == len(m.STEPS) == 5)
check("step_valid", all(row["valid"] for row in validation["steps"]))
check("step_solids", all(row["solids"] >= 1 for row in validation["steps"]))
check("stl_count", len(validation["stls"]) == len(m.STLS) == 5)
for path, metrics in sorted(validation["stls"].items()):
    check(f"reload_{path}", metrics["reload"] == "PASS")
    check(f"watertight_{path}", metrics["watertight"])
    check(f"manifold_{path}", metrics["manifold"])
    check(f"edges_{path}", metrics["bad_edge_count"] == 0)
    check(f"degenerate_{path}", metrics["degenerate_triangle_count"] == 0)
check("repro", validation["reproducibility"]["status"] == "PASS")
check("repro_exact", validation["reproducibility"]["byte_identical"] == validation["reproducibility"]["compared"])
check("repro_mismatch_zero", validation["reproducibility"]["mismatches"] == [])
check("authority_4", len(validation["repository"]["authority"]) == 4)
check("protected_7", len(validation["repository"]["protected"]) == 7)
check("branch", validation["repository"]["branch"] == m.BRANCH)
check("head", validation["repository"]["head"] == m.HEAD)
check("assumption", "Y=10.2" in validation["assumptions"][0])

print_data = data["print"]
check("coupon_order", print_data["coupon_order"] == m.STLS[:3])
check("coupon_status", print_data["coupon_status"] == "MOLDED_EXIT_ROOT_COUPONS_PRINT_READY")
check("full_hold", print_data["full_bracket_status"] == "FULL_BRACKET_HOLD_PENDING_MOLDED_EXIT_ROOT_PHYSICAL_VALIDATION")
check("slicer_hold", print_data["slicer"] == "HOLD_SLICER_NOT_RUN")
check("status_cad", "CAD_PASS" in data["status"])
check("status_contract", "CONTRACT_TEST_PASS" in data["status"])
check("status_coupon", "MOLDED_EXIT_ROOT_COUPONS_PRINT_READY" in data["status"])
check("status_pending", "MOLDED_EXIT_ROOT_PHYSICAL_VALIDATION_PENDING" in data["status"])
check("status_full_hold", "FULL_BRACKET_HOLD" in data["status"])
for forbidden in data["forbidden_claims"]:
    check(f"forbidden_{forbidden}", forbidden not in data["status"])

paths = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file())
check("exact_paths", paths == m.EXPECTED)
commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
check("commit_count", len(commit_paths) == len(m.EXPECTED))
check("commit_exact", commit_paths == [m.LANE_REL.as_posix() + "/" + path for path in m.EXPECTED])
check("manifest", f"EXACT_PATH_COUNT={len(m.EXPECTED)}" in (LANE / "MANIFEST.txt").read_text(encoding="utf-8"))
sha_lines = (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
check("sha_count", len(sha_lines) == len(m.EXPECTED) - 1)
for line in sha_lines:
    digest, relative = line.split("  ", 1)
    check(f"sha_{relative}", digest == hashlib.sha256((LANE / relative).read_bytes()).hexdigest())

print(f"CONTRACT={len(checks)}/{len(checks)} PASS")
print(f"EXACT_PATHS={len(m.EXPECTED)}")
print("STEP_RELOAD=5/5 PASS")
print("STL_QUALITY=5/5 PASS")
print(f"REPRO={validation['reproducibility']['byte_identical']}/{validation['reproducibility']['compared']} PASS")
