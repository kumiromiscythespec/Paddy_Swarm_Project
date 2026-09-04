"""Contract for the V004 drainage-biased local angled gland mount."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE = ROOT / "cad/common_rover/bbox_lid_wiring_chimney_v004_drainage_biased_gland"
BUILDER = LANE / "build_bbox_lid_wiring_chimney_v004.py"
spec = importlib.util.spec_from_file_location("bbox_chimney_v004_builder", BUILDER)
assert spec and spec.loader
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

passed = 0


def check(name: str, condition: bool):
    global passed
    if not condition:
        raise AssertionError(name)
    passed += 1


data = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
validation = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
check("version", data["version"] == b.VERSION == validation["version"])
check("full_parent", data["parents"]["full_lid_2p4_authority"] == b.PARENT_FULL_REL)
check("local_parent", data["parents"]["local_gland_recess_authority"] == b.PARENT_LOCAL_REL)
check("parents_read_only", data["parents"]["read_only"])

baseline = data["physical_baseline"]
for key in ("above_water_gland_architecture", "bbox_upright_water_test", "tilt_front_10deg_plus", "tilt_rear_10deg_plus", "tilt_left_10deg_plus", "tilt_right_10deg_plus"):
    check("baseline_" + key, baseline[key] == "PHYSICAL_PASS" if key == "above_water_gland_architecture" else baseline[key] == "PASS")
check("ingress_none", baseline["internal_water_ingress"] == "NONE")
check("fallback_valid", baseline["vertical_v003_fallback_authority"] == "VALID")

architecture = data["architecture"]
check("purpose", architecture["purpose"] == "BASELINE_WATERPROOFING_PLUS_PASSIVE_DRAINAGE_FAIL_SAFE")
check("angles", architecture["candidate_angles_deg"] == [5.0, 7.0])
check("primary", architecture["primary_angle_deg"] == 7.0)
check("direction", architecture["axis_direction"] == "POSITIVE_Y_OUTWARD_AND_NEGATIVE_Z_DOWNWARD")
check("not_whole_chimney", not architecture["whole_chimney_angled"])
check("not_whole_lid", not architecture["whole_lid_angled"])
check("local_wedge", architecture["local_integrated_wedge_pad"])
check("gasket_seat", architecture["exterior_gasket_seat"] == "FLAT_PERPENDICULAR_TO_GLAND_AXIS")
check("locknut_seat", architecture["interior_locknut_seat"] == "FLAT_PARALLEL_TO_EXTERIOR_SEAT")

geometry = data["geometry"]
expected_geometry = {
    "chimney_outer_xyz_mm": [50.0, 45.0, 50.0],
    "chimney_internal_xy_mm": [42.0, 37.0],
    "normal_wall_mm": 4.0,
    "local_effective_wall_along_axis_mm": 2.4,
    "gland_hole_diameter_mm": 15.2,
    "recess_entry_diameter_mm": 30.0,
    "flat_locknut_seat_effective_diameter_mm": 27.0,
    "transition_r_class_mm": 1.5,
    "rain_hood_projection_mm": 8.0,
    "internal_gland_center_above_lid_top_mm": 30.0,
    "local_mount_cross_section_xz_mm": [30.0, 30.0],
    "cable_diameter_mm": 9.6,
}
for key, value in expected_geometry.items():
    check("geometry_" + key, geometry[key] == value)

for angle in (5, 7):
    metrics = data["candidates"][str(angle)]
    current = validation["candidates"][str(angle)]
    check(f"angle_{angle}", metrics["angle_deg"] == angle and current["angle_deg"] == angle)
    check(f"axis_x_{angle}", metrics["axis_vector_xyz"][0] == 0)
    check(f"axis_y_{angle}", metrics["axis_vector_xyz"][1] > 0)
    check(f"axis_z_{angle}", metrics["axis_vector_xyz"][2] < 0)
    check(f"internal_center_{angle}", metrics["internal_bore_center_xyz_mm"] == [0.0, 65.1, 38.0])
    expected_drop = 2.4 * math.sin(math.radians(angle))
    check(f"drop_{angle}", abs(metrics["vertical_drop_mm"] - expected_drop) < 1e-6)
    check(f"outward_{angle}", metrics["outward_run_mm"] > 2.3)
    check(f"wall_{angle}", metrics["measured_effective_wall_along_axis_mm"] == 2.4)
    check(f"gasket_perp_{angle}", metrics["gasket_seat_perpendicularity_error_deg"] == 0)
    check(f"locknut_perp_{angle}", metrics["locknut_seat_perpendicularity_error_deg"] == 0)
    check(f"parallel_{angle}", metrics["seat_parallelism_error_deg"] == 0)
    check(f"drain_angle_{angle}", metrics["mount_top_surface_outward_drop_deg"] == angle)
    check(f"no_shelf_{angle}", not metrics["mount_has_horizontal_dead_water_shelf"])
    check(f"hood_clear_{angle}", metrics["gland_body_to_hood_intersection_mm3"] == 0)
    check(f"body_clear_{angle}", metrics["gland_body_to_lid_intersection_mm3"] == 0)
    check(f"cable_clear_{angle}", metrics["cable_to_lid_intersection_mm3"] == 0)
    check(f"nut_clear_{angle}", metrics["locknut_to_lid_intersection_mm3"] == 0)
    check(f"roof_clear_{angle}", metrics["recess_top_to_roof_clearance_mm"] > 1.0)
    check(f"valid_{angle}", metrics["valid"] and metrics["solids"] == 1)
    check(f"coupon_valid_{angle}", metrics["coupon_valid"] and metrics["coupon_solids"] == 1)
    check(f"bbox_{angle}", metrics["bbox_mm"] == [240.0, 190.0, 58.0])

drainage = data["drainage"]
for key in ("top_local_surface_slopes_outward_downward",):
    check("drainage_" + key, drainage[key])
for key in ("cup_shaped_pocket", "reverse_lip", "horizontal_dead_water_shelf_immediately_above_gland", "inward_sloping_gasket_surround", "tiny_drip_edge_added"):
    check("drainage_not_" + key, not drainage[key])
check("water_flow_pending", drainage["physical_water_flow_validation"] == "PENDING_COUPON")

tool = data["tool_access"]
check("tool_nut_d", tool["locknut_reference_diameter_mm"] == 24.0)
check("tool_entry_d", tool["recess_entry_diameter_mm"] == 30.0)
check("tool_seat_d", tool["flat_seat_diameter_mm"] == 27.0)
check("tool_cad_clear", tool["cad_reference_intersection_zero"])
check("tool_finger_candidate", tool["finger_installation_candidate"])
check("tool_hold", tool["actual_tool_envelope"] == "HOLD_ACTUAL_TOOL_ENVELOPE_REQUIRED")

delta = validation["protected_delta"]
check("delta_nonzero", delta["total_local_revision_delta_mm3"] > 0)
check("delta_local", delta["total_local_revision_delta_mm3"] == delta["delta_inside_local_mask_mm3"])
for key in ("delta_outside_local_mask_mm3", "lid_outer_geometry_outside_local_change_mm3", "gasket_loop_change_mm3", "seal_land_change_mm3", "m4x8_pattern_change_mm3", "bbox_shell_interface_change_mm3", "chimney_footprint_change_mm3", "chimney_height_change_mm", "rain_hood_change_mm3", "rain_hood_projection_change_mm", "gland_hole_diameter_change_mm"):
    check("protected_" + key, delta[key] == 0)

water = data["waterline"]
check("water_angle", water["angle_deg"] == 7.0)
check("water_internal_model", water["model_internal_center_z_mm"] == 38.0)
check("water_external_lower", water["model_external_center_z_mm"] < water["model_internal_center_z_mm"])
check("water_lid_z", water["lid_top_absolute_z_mm"] == 257.0)
check("water_chimney_z", water["chimney_top_absolute_z_mm"] == 307.0)
check("water_low_margin_150", water["lowest_edge_margin_above_z150_mm"] > 129.0)
check("water_low_margin_210", water["lowest_edge_margin_above_z210_mm"] > 69.0)
check("water_z150_class", water["z150_class"] == "CAD_DESIGN_TARGET")
check("water_z210_class", water["z210_class"] == "DERIVED_DESIGN_SCENARIO_NOT_PHYSICAL_MUD_MEASUREMENT")
check("water_mount_class", water["absolute_mount_datum_class"] == "DERIVED_FROM_CAD_AND_TOP_INSERT_Z257_ASSUMPTION")
check("water_relative_class", water["relative_geometry_class"] == "CAD")
check("water_physical_class", water["physical_baseline_class"] == "PHYSICAL_PASS_SEPARATE_FROM_DERIVED_Z")

printing = data["print"]
check("printer", printing["printer"] == "Bambu Lab A1")
check("material", printing["material"] == "PETG")
check("first_print", printing["first_print"] == b.STLS[1])
check("second_print", printing["second_print_if_required"] == b.STLS[0])
check("full_lid_hold", printing["full_lid_status"] == "FULL_LID_HOLD_PENDING_ANGLED_GLAND_PHYSICAL_COUPON")
check("slicer_hold", printing["slicer"] == "HOLD_SLICER_NOT_RUN")
check("status", data["status"] == "CAD_PASS/CONTRACT_TEST_PASS/DRAINAGE_BIASED_GLAND_COUPONS_PRINT_READY/ANGLED_GLAND_PHYSICAL_VALIDATION_PENDING")
for forbidden in ("V004_WATERPROOF_PASS", "RAIN_PASS", "WET_CABLE_PASS", "FIELD_PASS"):
    check("forbidden_" + forbidden, forbidden in data["forbidden_claims"] and forbidden not in data["status"])

check("validation_all", validation["pass_count"] == validation["check_count"])
check("step_count", len(validation["step"]) == 4)
for item in validation["step"]:
    check("step_" + item["path"], item["reload"] == "PASS" and item["valid"] and item["solids"] >= 1)
check("stl_count", len(validation["stl"]) == 3)
for item in validation["stl"]:
    check("stl_" + item["path"], item["reload"] == "PASS" and item["watertight"] and item["manifold"] and item["bad_edge_count"] == 0 and item["degenerate_triangle_count"] == 0)
repro = validation["reproducibility"]
check("repro", repro["status"] == "PASS" and repro["compared"] == repro["byte_identical"] and not repro["mismatches"])

manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
check("manifest_count", int(next(line.split("=", 1)[1] for line in manifest if line.startswith("EXACT_PATH_COUNT="))) == len(b.EXPECTED))
check("manifest_steps", int(next(line.split("=", 1)[1] for line in manifest if line.startswith("STEP_COUNT="))) == 4)
check("manifest_stls", int(next(line.split("=", 1)[1] for line in manifest if line.startswith("STL_COUNT="))) == 3)
check("manifest_svgs", int(next(line.split("=", 1)[1] for line in manifest if line.startswith("SVG_COUNT="))) == 4)
commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
check("commit_paths", commit_paths == [f"{b.LANE_REL.as_posix()}/{path}" for path in b.EXPECTED])
actual = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file())
check("exact_paths", actual == b.EXPECTED)
checksums = (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
check("sha_count", len(checksums) == len(b.EXPECTED) - 1)
check("sha_valid", all((LANE / line.split("  ", 1)[1]).exists() and hashlib.sha256((LANE / line.split("  ", 1)[1]).read_bytes()).hexdigest() == line.split("  ", 1)[0] for line in checksums))

repo = b.guard(True)
check("repo_root", Path(repo["root"]) == ROOT)
check("repo_branch", repo["branch"] == b.BRANCH)
check("repo_head", repo["head"] == b.HEAD)
check("repo_staged", repo["staged"] == [])
check("repo_dirty", repo["dirty"] == b.DIRTY)
check("repo_authority", repo["checks"]["authority_4"])
check("repo_protected", repo["checks"]["protected_7"])
check("repo_outside", repo["checks"]["outside_preserved"])
check("repo_scope", repo["checks"]["scope"] and repo["checks"]["complete"])
check("repo_cache", repo["checks"]["cache_zero"] and repo["checks"]["ignored_zero"])

print(f"CONTRACT_TEST_PASS {passed}/{passed}")
