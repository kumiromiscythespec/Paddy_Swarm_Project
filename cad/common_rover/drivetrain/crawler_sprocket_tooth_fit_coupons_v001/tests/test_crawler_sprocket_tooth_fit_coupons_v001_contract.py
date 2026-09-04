"""Contract for crawler sprocket single-tooth physical-fit coupons V001."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE = ROOT / "cad/common_rover/drivetrain/crawler_sprocket_tooth_fit_coupons_v001"
BUILDER = LANE / "build_crawler_sprocket_tooth_fit_coupons_v001.py"
spec = importlib.util.spec_from_file_location("crawler_tooth_fit_builder", BUILDER)
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

sources = data["sources"]
check("link_path", sources["crawler_link"]["path"] == b.LINK_STL_REL)
check("link_sha", sources["crawler_link"]["sha256"] == b.LINK_STL_SHA == hashlib.sha256(b.LINK_STL.read_bytes()).hexdigest())
check("link_scale", sources["crawler_link"]["scale"] == 1.0)
check("link_mesh", sources["crawler_link"]["watertight"] and sources["crawler_link"]["manifold"])
check("link_extents", sources["crawler_link"]["extents_mm"] == [31.99696, 54.0, 24.75])
check("carrier_path", sources["current_carrier"]["path"] == b.CARRIER_STL_REL)
check("carrier_sha", sources["current_carrier"]["sha256"] == b.CARRIER_STL_SHA == hashlib.sha256(b.CARRIER_STL.read_bytes()).hexdigest())
check("carrier_mesh", sources["current_carrier"]["watertight"] and sources["current_carrier"]["manifold"])
check("carrier_authority", sources["current_carrier"]["authority_outer_geometry"] == "PROTECTED_P20653_14T")
check("carrier_count", sources["current_carrier"]["authority_outer_tooth_count"] == 14)
check("carrier_width", sources["current_carrier"]["authority_outer_width_mm"] == 44.0)

failure = data["physical_failure"]
check("failure_status", failure["classification"] == "SPROCKET_TO_CRAWLER_TOOTH_GEOMETRY_PHYSICAL_FAIL")
check("not_groove", failure["not_a_groove1_failure"])
check("reported_height", failure["current_tooth_radial_height_mm_approx"] == 8.3)
check("reported_tip", failure["current_tooth_tip_tangential_width_mm_approx_range"] == [7.6, 8.2])
check("reported_axial", failure["current_tooth_axial_width_mm"] == 44.0)
check("diagnosis", "HINGE_BRIDGE" in failure["diagnosis"])

protected = data["protected_drivetrain"]
for key in ("pulley_groove1_physical_fit", "pulley_groove1_static_torque_transfer", "shaft_key_manual_rotation", "full_carrier_manual_forward_reverse"):
    check("preserved_" + key, protected[key] == "PASS")
for key, value in protected.items():
    if key.endswith("_change"):
        check("zero_" + key, value == 0)

coordinates = data["coordinate_contract"]
check("axis_x", coordinates["crawler_travel_tangential_axis"] == "X")
check("axis_y", coordinates["crawler_shaft_axial_axis"] == "Y")
check("axis_z", coordinates["tooth_radial_insertion_axis"] == "+Z")
check("source_pose", coordinates["link_pose_source_coordinates"])
check("root_pose", coordinates["root_plane_engaged_z_mm"] == 3.5)
check("bridge_z", coordinates["central_bridge_underside_z_mm"] == 9.0)
check("assembly", coordinates["assembly_method"] == "STRAIGHT_PLUS_Z_SINGLE_TOOTH_INSERTION_WITH_OPEN_SIDE_ACCESS")

expected = {"A": [4.0, 5.5, 18.0], "B": [4.25, 6.0, 20.0], "C": [4.5, 6.5, 22.0]}
for code, dims in expected.items():
    item = data["candidates"][code]
    current = validation["candidates"][code]
    check("id_" + code, item["candidate_id"] == code)
    check("height_" + code, item["radial_height_mm"] == dims[0])
    check("tip_" + code, item["tip_tangential_width_mm"] == dims[1])
    check("tip_measured_" + code, item["tip_tangential_width_measured_mm"] == dims[1])
    check("axial_" + code, item["axial_width_mm"] == dims[2])
    check("axial_measured_" + code, item["axial_width_measured_at_tip_mm"] == dims[2])
    check("root_r_" + code, item["root_transition_radius_mm"] == 1.25)
    check("root_wider_" + code, item["root_total_tangential_width_mm"] > dims[1])
    check("root_pose_" + code, item["root_plane_engaged_z_mm"] == 3.5)
    check("tip_pose_" + code, item["tip_engaged_z_mm"] == 3.5 + dims[0])
    check("bridge_" + code, item["central_bridge_underside_z_mm"] == 9.0)
    check("radial_clear_" + code, item["radial_clearance_to_bridge_mm"] >= 1.0)
    check("global_clear_" + code, item["minimum_global_clearance_mm"] >= 1.0)
    check("side_clear_" + code, item["minimum_anti_derail_side_clearance_mm"] >= 5.0)
    check("pivot_clear_" + code, item["minimum_pivot_region_clearance_mm"] >= 2.5)
    check("whole_zero_" + code, item["maximum_interference_volume_mm3"] == 0)
    check("coupon_zero_" + code, item["coupon_interference_volume_mm3"] == 0)
    check("hinge_zero_" + code, item["hinge_bridge_interference_mm3"] == 0)
    check("pivot_zero_" + code, item["pivot_screw_region_interference_mm3"] == 0)
    check("guard_zero_" + code, item["anti_derail_interference_mm3"] == 0)
    for pose, volume in item["approach_path_interference_mm3"].items():
        check(f"approach_{code}_{pose}", volume == 0)
    check("depth_" + code, item["achievable_insertion_depth_mm"] == dims[0])
    check("full_depth_" + code, item["full_depth_seating_cad"])
    check("no_contact_" + code, item["local_contact_surfaces"] == "NONE_AT_INTENDED_POSE")
    check("nearest_" + code, item["nearest_surfaces"] == "TOOTH_TIP_TO_CENTRAL_HINGE_BRIDGE_UNDERSIDE")
    check("valid_" + code, item["candidate_valid"] and item["candidate_solids"] == 1)
    check("coupon_valid_" + code, item["coupon_valid"] and item["coupon_solids"] == 1)
    check("physical_pending_" + code, item["physical_fit"] == "PENDING")
    check("validation_match_" + code, item == current)

selection = data["selection"]
check("cad_primary", selection["cad_primary"] == "B")
check("physical_order", selection["physical_order"] == ["A", "B", "C"])
check("largest_not_auto", "LARGEST" in selection["rule"] and "NO_FORCE" in selection["rule"])
check("mud_margin", selection["mud_clearance_priority"])

pitch = data["pitch_hold"]
check("future_12", pitch["future_requested_tooth_count"] == 12)
check("reference_14", pitch["current_reference_carrier_tooth_count"] == 14)
check("conflict_disposition", pitch["conflict_disposition"] == "NO_PATTERN_GENERATED_SINGLE_TOOTH_ONLY_FUTURE_12T_REMAINS_HOLD")
check("pitch_hold", pitch["crawler_pitch_authority"] == "HOLD")
check("pd_hold", pitch["sprocket_pitch_diameter"] == "HOLD")
check("angular_zero", pitch["existing_angular_center_reference_change"] == 0)
check("three_tooth_hold", pitch["three_tooth_sector"] == "NOT_GENERATED_PITCH_AUTHORITY_HOLD")
check("no_full", pitch["full_sprocket"] == "NOT_GENERATED")

printing = data["print"]
check("printer", printing["printer"] == "Bambu Lab A1")
check("material", printing["material"] == "PETG")
check("first_print", printing["first_print"] == b.STLS[0])
check("test_order", printing["test_order"] == ["A", "B", "C"])
check("combined", printing["combined_plate"] == b.STLS[3])
check("slicer_hold", printing["slicer"] == "HOLD_SLICER_NOT_RUN")
check("status", data["status"] == "CAD_PASS/CONTRACT_TEST_PASS/CRAWLER_TOOTH_FIT_COUPONS_PRINT_READY/CRAWLER_TOOTH_GEOMETRY_PHYSICAL_VALIDATION_PENDING")
for hold in ("CRAWLER_TOOTH_GEOMETRY_PHYSICAL_VALIDATION_PENDING", "CRAWLER_PITCH_PENDING", "POWERED_CRAWLER_TEST_HOLD"):
    check("hold_" + hold, hold in data["holds"])
for forbidden in ("CRAWLER_DRIVE_PASS", "POWERED_TORQUE_PASS", "DRY_RUN_PASS", "MUD_PASS", "FIELD_PASS"):
    check("forbidden_" + forbidden, forbidden in data["forbidden_claims"] and forbidden not in data["status"])

check("validation_all", validation["pass_count"] == validation["check_count"])
check("step_not_generated", len(validation["step"]) == 0 and b.STEPS == [])
check("stl_count", len(validation["stl"]) == 4)
for item in validation["stl"]:
    check("stl_" + item["path"], item["reload"] == "PASS" and item["watertight"] and item["manifold"] and item["bad_edge_count"] == 0 and item["degenerate_triangle_count"] == 0 and item["component_count"] == 1)
repro = validation["reproducibility"]
check("repro", repro["status"] == "PASS" and repro["compared"] == repro["byte_identical"] and not repro["mismatches"])

manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
check("manifest_count", int(next(line.split("=", 1)[1] for line in manifest if line.startswith("EXACT_PATH_COUNT="))) == len(b.EXPECTED))
check("manifest_steps", int(next(line.split("=", 1)[1] for line in manifest if line.startswith("STEP_COUNT="))) == 0)
check("manifest_stls", int(next(line.split("=", 1)[1] for line in manifest if line.startswith("STL_COUNT="))) == 4)
check("manifest_svgs", int(next(line.split("=", 1)[1] for line in manifest if line.startswith("SVG_COUNT="))) == 3)
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
check("repo_protected", repo["checks"]["protected_5"])
check("repo_inputs", repo["checks"]["input_sha"])
check("repo_outside", repo["checks"]["outside_preserved"])
check("repo_scope", repo["checks"]["scope"] and repo["checks"]["complete"])
check("repo_cache", repo["checks"]["cache_zero"] and repo["checks"]["ignored_zero"])

print(f"CONTRACT_TEST_PASS {passed}/{passed}")
