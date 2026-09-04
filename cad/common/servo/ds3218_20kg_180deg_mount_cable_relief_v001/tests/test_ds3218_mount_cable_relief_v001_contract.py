"""Contract for the DS3218 local cable-exit relief revision."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
LANE = HERE.parents[1]
BUILDER = LANE / "build_ds3218_mount_cable_relief_v001.py"
spec = importlib.util.spec_from_file_location("ds3218_cable_relief_builder", BUILDER)
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

check("repository_guard", all(m.guard(True)["checks"].values()))
check("version", data["version"] == m.VERSION)
check("parent_lane", data["parent"]["lane"] == m.PARENT_REL.as_posix())
check("parent_read_only", data["parent"]["status"] == "READ_ONLY_PHYSICAL_CAD_AUTHORITY")
check("parent_hash", data["parent"]["tree_sha256"] == m.PROTECTED[m.PARENT_REL.as_posix()][1])
check("case_fit_pass", data["physical_results"]["servo_case_fit"] == "PASS")
check("mount_pattern_pass", data["physical_results"]["mount_pattern_physical_fit"] == "PASS")
check("case_dimensions", data["servo_authority_unchanged"]["case_lwh_mm"] == [40.0, 20.4, 41.7])
check("mount_envelope", data["servo_authority_unchanged"]["mounting_envelope_length_mm"] == 54.5)
check("pitch_xy", data["servo_authority_unchanged"]["mount_pitch_xy_mm"] == [49.1, 10.0])
check("servo_hole", data["servo_authority_unchanged"]["servo_physical_hole_diameter_mm"] == 4.6)
check("output_axis", data["servo_authority_unchanged"]["output_axis_xy_mm"] == [10.1, 10.2])
check("horn_radius", data["servo_authority_unchanged"]["horn_link_radius_mm"] == 30.0)
check("horn_thickness", data["servo_authority_unchanged"]["horn_thickness_mm"] == 2.4)
check("horn_plane", data["servo_authority_unchanged"]["horn_rotation_plane_z_mm"] == 46.2)
check("max_height", data["servo_authority_unchanged"]["servo_with_horn_max_height_mm"] == 48.0)
check("narrow_pattern_identified", data["fastener"]["narrower_coupon_pattern_identity_mm"] == 4.6)
check("bracket_hole_preserved", data["fastener"]["full_bracket_hole_in_this_revision_mm"] == 5.0)
check("hardware_pending", data["fastener"]["hardware_standard"] == "PHYSICAL_FASTENER_SELECTION_PENDING")
check("no_fastener_promotion", data["fastener"]["promotion"].startswith("NOT_PROMOTED"))
check("cable_width", data["cable"]["bundle_width_at_servo_exit_mm"] == 4.4)
check("cable_width_physical", data["cable"]["width_status"] == "PHYSICAL_AUTHORITY")
check("cable_z_approx", data["cable"]["vertical_start"] == "APPROX_SERVO_BOTTOM_PLUS_4MM")
check("exact_exit_hold", data["cable"]["exact_exit_xyz_status"].startswith("HOLD"))
check("architecture", data["relief"]["architecture"] == "OPEN_BOTTOM_U_SHAPED_LOCAL_SLOT")
check("widths", data["relief"]["candidate_clear_widths_mm"] == [6.0, 6.5, 7.0])
check("primary", data["relief"]["primary_width_mm"] == 6.5)
check("height", data["relief"]["height_mm"] == 8.0)
check("clear_6p0", data["relief"]["clearance_per_side_mm"]["6.0"] == 0.8)
check("clear_6p5", data["relief"]["clearance_per_side_mm"]["6.5"] == 1.05)
check("clear_7p0", data["relief"]["clearance_per_side_mm"]["7.0"] == 1.3)
check("local_cavity_only", not data["relief"]["global_cavity_change"])
check("no_mount_shift", not data["relief"]["mount_location_change"])
check("no_cable_retention_load", not data["relief"]["retention_load_on_cable"])
check("coupon_order", data["print"]["coupon_order"] == m.STLS[:3])
check("coupon_ready", data["print"]["coupon_status"] == "CABLE_RELIEF_COUPONS_PRINT_READY")
check("full_bracket_hold", data["print"]["full_bracket_status"] == "HOLD_PENDING_CABLE_RELIEF_PHYSICAL_VALIDATION")
check("slicer_hold", data["print"]["slicer"] == "HOLD_SLICER_NOT_RUN")

geometry = validation["geometry"]
check("parent_valid", geometry["parent_valid"])
check("revised_valid", geometry["revised_valid"])
check("parent_one_solid", geometry["parent_solids"] == 1)
check("revised_one_solid", geometry["revised_solids"] == 1)
check("material_removed", geometry["removed_volume_mm3"] > 0)
check("material_added_zero", geometry["added_volume_mm3"] == 0)
check("local_only", geometry["local_only"])
check("parent_interference_reproduced", geometry["parent_cable_keepout_intersection_mm3"] > 0)
check("revised_intersection_zero", geometry["revised_cable_keepout_intersection_mm3"] == 0)
check("geometry_widths", geometry["relief_widths_mm"] == [6.0, 6.5, 7.0])
check("geometry_primary", geometry["primary_relief_width_mm"] == 6.5)
check("geometry_height", geometry["relief_height_mm"] == 8.0)
check("edge_range", 1.0 <= geometry["entry_chamfer_equivalent_mm"] <= 1.5)
check("coupon_valid_3", len(geometry["coupon_valid"]) == 3 and all(geometry["coupon_valid"].values()))
check("combined_valid", geometry["combined_valid"])
check("body_dimensions_geometry", geometry["body_fit_dimensions_mm"] == [40.0, 20.4, 41.7])
check("mount_centers", geometry["mount_hole_centers_mm"] == [[-4.55, 5.2], [-4.55, 15.2], [44.55, 5.2], [44.55, 15.2]])
check("output_geometry", geometry["output_axis_mm"] == [10.1, 10.2])
check("horn_geometry", geometry["horn_keepout_mm"] == [30.0, 2.4, 46.2])
check("wall_unchanged", geometry["minimum_existing_wall_mm"] >= 2.5)
check("ligament_safe", geometry["minimum_remaining_base_ligament_each_side_mm"] >= 10.0)

check("validation_all", validation["pass_count"] == validation["check_count"])
check("step_count", len(validation["steps"]) == len(m.STEPS) == 5)
check("step_valid", all(row["valid"] for row in validation["steps"]))
check("step_reload_solids", all(row["solids"] >= 1 for row in validation["steps"]))
check("stl_count", len(validation["stls"]) == len(m.STLS) == 5)
for path, metrics in sorted(validation["stls"].items()):
    check(f"stl_reload_{path}", metrics["reload"] == "PASS")
    check(f"stl_watertight_{path}", metrics["watertight"])
    check(f"stl_manifold_{path}", metrics["manifold"])
    check(f"stl_edges_{path}", metrics["bad_edge_count"] == 0)
    check(f"stl_degenerate_{path}", metrics["degenerate_triangle_count"] == 0)
check("repro_status", validation["reproducibility"]["status"] == "PASS")
check("repro_exact", validation["reproducibility"]["byte_identical"] == validation["reproducibility"]["compared"])
check("repro_mismatch_zero", validation["reproducibility"]["mismatches"] == [])
check("authority_4", len(validation["repository"]["authority"]) == 4)
check("protected_6", len(validation["repository"]["protected"]) == 6)
check("branch", validation["repository"]["branch"] == m.BRANCH)
check("head", validation["repository"]["head"] == m.HEAD)
check("assumption_recorded", "+X end" in validation["assumptions"][0])
check("status_cad", "CAD_PASS" in data["status"])
check("status_contract", "CONTRACT_TEST_PASS" in data["status"])
check("status_coupon", "CABLE_RELIEF_COUPONS_PRINT_READY" in data["status"])
check("status_pending", "CABLE_RELIEF_PHYSICAL_VALIDATION_PENDING" in data["status"])
check("status_bracket_hold", "FULL_BRACKET_HOLD_PENDING_CABLE_RELIEF_PHYSICAL_VALIDATION" in data["status"])
for forbidden in data["forbidden_claims"]:
    check(f"forbidden_{forbidden}", forbidden not in data["status"])

expected = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file())
check("exact_paths", expected == m.EXPECTED)
commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
check("commit_path_count", len(commit_paths) == len(m.EXPECTED))
check("commit_path_exact", commit_paths == [m.LANE_REL.as_posix() + "/" + path for path in m.EXPECTED])
check("manifest_count", f"EXACT_PATH_COUNT={len(m.EXPECTED)}" in (LANE / "MANIFEST.txt").read_text(encoding="utf-8"))
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
