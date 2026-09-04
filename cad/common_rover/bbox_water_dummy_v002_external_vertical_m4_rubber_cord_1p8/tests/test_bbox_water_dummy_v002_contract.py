"""Executable contract for PS-BBOX-WATER-DUMMY-V002."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_bbox_water_dummy_v002.py"
spec = importlib.util.spec_from_file_location("bbox_water_dummy_v002", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("builder import")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
passed: list[str] = []

def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    passed.append(name)

result = m.verify(); report = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
a = report["analysis"]; repo = result["repository"]

# Repository and protected references.
check("repository", Path(repo["repository"]).resolve() == m.REPO_ROOT.resolve())
check("branch", repo["branch"] == m.EXPECTED_BRANCH)
check("head", repo["head"] == m.EXPECTED_HEAD)
check("staged_zero", repo["staged"] == [])
check("dirty_preserved", repo["tracked_dirty"] == m.TRACKED_DIRTY)
check("outside_preserved", tuple(repo["outside_untracked"]) == (m.BASE_OUTSIDE_COUNT, m.BASE_OUTSIDE_PATH_DIGEST))
check("authority_4", repo["authority_sha256"] == m.AUTHORITY_SHA256)
check("protected_count", len(repo["protected_trees"]) == 4)
check("v001_protected", repo["protected_trees"]["cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test"]["tree_sha256"] == m.PROTECTED_TREES["cad/common_rover/bbox_water_dummy_v001_full_size_seal_submersion_test"][1])
check("v37_protected", repo["protected_trees"]["cad/common_rover/common_rover_top_insert_bbox_v0_9_6_37"]["tree_sha256"] == m.PROTECTED_TREES["cad/common_rover/common_rover_top_insert_bbox_v0_9_6_37"][1])
check("all_protected", all(repo["protected_trees"][rel]["tree_sha256"] == row[1] for rel, row in m.PROTECTED_TREES.items()))
check("exact_paths", result["path_count"] == m.EXPECTED_PATH_COUNT == 37)
check("manifest", (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == m.EXPECTED_FILES)
check("commit_paths", len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == 37)
check("sha_zero", result["sha_mismatch_count"] == 0)

# Formal V001 physical failure record.
failure = a["physical_failure_record"]
check("v001_body_pass", failure["V001_BODY_PRINT"] == "PASS")
check("cord_install_feasible", failure["V001_RUBBER_CORD_INSTALLATION"] == "PHYSICALLY_FEASIBLE")
check("v001_water_path_fail", failure["V001_THROUGH_HOLE_WATER_PATH"] == "FAIL")
check("v001_side_m4_fail", failure["V001_SIDE_M4_RETENTION"] == "FAIL")
check("v001_config_rejected", failure["V001_WATER_TEST_CONFIGURATION"] == "REJECTED")

# Physical cord authority and calculations.
cord = a["rubber_cord"]
check("cord_source", cord["source"] == "PVC_TOWER_RUBBER_CORD")
check("cord_diameter", cord["physical_diameter_mm"] == 1.8)
check("cord_measurement_authority", cord["measurement_authority"] == "USER_IMAGE_PHYSICAL_MEASUREMENT")
check("cord_hardness_hold", cord["material_hardness"] == "HOLD")
check("cord_joint_hold", cord["end_joint"] == "PHYSICAL_HOLD")
check("compression_percent", cord["compression_percent_target"] == [20.0, 25.0])
check("compressed_height", cord["compressed_height_target_mm"] == [1.35, 1.44])
check("twenty_percent_math", round(1.8 * 0.80, 2) == 1.44)
check("twenty_five_percent_math", round(1.8 * 0.75, 2) == 1.35)

study = a["gasket_study"]; rows = {row["candidate"]: row for row in study["candidates"]}
check("three_candidates", set(rows) == {"G18-A", "G18-B", "G18-C"})
check("a_geometry", rows["G18-A"]["width_mm"] == 2.0 and rows["G18-A"]["depth_mm"] == 0.4)
check("b_geometry", rows["G18-B"]["width_mm"] == 2.1 and rows["G18-B"]["depth_mm"] == 0.5)
check("c_geometry", rows["G18-C"]["width_mm"] == 2.2 and rows["G18-C"]["depth_mm"] == 0.6)
check("a_id", rows["G18-A"]["notch_count"] == 1)
check("b_id", rows["G18-B"]["notch_count"] == 2)
check("c_id", rows["G18-C"]["notch_count"] == 3)
check("a_gap", rows["G18-A"]["hard_stop_gap_range_mm"] == [0.95, 1.04])
check("b_gap", rows["G18-B"]["hard_stop_gap_range_mm"] == [0.85, 0.94])
check("c_gap", rows["G18-C"]["hard_stop_gap_range_mm"] == [0.75, 0.84])
check("a_nominal", rows["G18-A"]["hard_stop_gap_nominal_mm"] == 0.995)
check("b_nominal", rows["G18-B"]["hard_stop_gap_nominal_mm"] == 0.895)
check("c_nominal", rows["G18-C"]["hard_stop_gap_nominal_mm"] == 0.795)
check("nominal_total", all(row["compressed_total_at_nominal_mm"] == 1.395 for row in rows.values()))
check("provisional_b", study["full_dummy_provisional_candidate"] == "G18-B")
check("compression_hold", study["final_gasket_compression"] == "PHYSICAL_HOLD")
check("closed_loop", study["closed_loop"] is True)
check("discontinuity_zero", study["discontinuity_count"] == 0)
check("groove_cavity_zero", study["groove_cavity_intersection_mm3"] == 0)
check("groove_m4_zero", study["groove_m4_intersection_mm3"] == 0)
check("hard_stop_groove_zero", study["hard_stop_groove_intersection_mm3"] == 0)
check("coupon_three", set(study["coupon_geometry"]) == {"G18-A", "G18-B", "G18-C"})
check("coupon_valid", all(row["valid"] for row in study["coupon_geometry"].values()))
check("coupon_bbox", all(row["bbox_mm"] == [48.0, 34.0, 5.0] for row in study["coupon_geometry"].values()))

# Sealed body firewall.
body = a["sealed_body"]
check("v001_envelope", body["core_outer_xyz_mm"] == [200.0, 150.0, 70.0])
check("body_inner", body["inner_xyz_mm"] == [192.0, 142.0, 65.0])
check("wall", body["wall_mm"] == 4.0)
check("bottom", body["bottom_mm"] == 5.0)
check("flange", body["top_flange_xy_mm"] == [208.0, 158.0])
check("body_valid", body["primary_valid"] is True)
check("bottom_closed", body["bottom_closed"] is True)
check("four_walls", body["continuous_walls"] == 4)
check("top_only", body["top_only_open"] is True)
check("drain_zero", body["drain_count"] == 0)
check("pin_zero", body["pin_hole_count"] == 0)
check("locator_zero", body["locator_hole_count"] == 0)
check("insert_pilot_zero", body["insert_pilot_hole_count"] == 0)
check("internal_penetration_zero", body["sealed_internal_hole_penetration_count"] == 0)
check("m4_cavity_zero", body["m4_hole_cavity_intersection_mm3"] == 0)
check("body_a1", max(body["external_bbox_mm"]) < 256.0)

# External vertical fasteners.
fastener = a["external_fastener"]
check("architecture", fastener["architecture"] == "EXTERNAL_VERTICAL_M4_THROUGH_BOLT")
check("vertical", fastener["orientation"] == "VERTICAL_Z")
check("horizontal_zero", fastener["horizontal_fastener_count"] == 0)
check("m4_count", fastener["m4_count"] == 8)
check("pattern", fastener["pattern"] == "CORNER_4_PLUS_EDGE_MID_4")
check("positions_eight", len(fastener["positions_xy_mm"]) == 8 and len({tuple(row) for row in fastener["positions_xy_mm"]}) == 8)
check("hole_d", fastener["clearance_hole_d_mm"] == 4.5)
check("bolt_candidate", fastener["bolt_length_candidate_mm"] == 30.0)
check("stack", fastener["stack"] == ["M4_BOLT", "LID_EXTERNAL_EAR", "OPEN_GAP", "BODY_EXTERNAL_LUG", "FLAT_WASHER", "M4_NYLOC_NUT"])
check("ligament_exact", fastener["minimum_structural_ligament_mm"] == 5.75)
check("ligament_hard", fastener["minimum_structural_ligament_mm"] >= fastener["ligament_hard_min_mm"])
check("ligament_target", fastener["minimum_structural_ligament_mm"] >= fastener["ligament_target_mm"])
check("tool_proxy", fastener["tool_access_proxy_od_mm"] == 12.0)
check("tool_access", fastener["tool_access_body_intersection_mm3"] == 0)
check("eight_better_than_six", fastener["eight_point_max_projected_span_mm"] < fastener["six_point_max_projected_span_mm"])
check("eight_selection", fastener["selection"] == "M4_X8_SELECTED_FOR_LOWER_MAXIMUM_COMPRESSION_SPAN")

# Lid, compression assembly, print gates.
lid = a["lid"]
check("lid_core", lid["core_xyz_mm"] == [208.0, 158.0, 8.0])
check("lid_valid", lid["primary_valid"] is True)
check("lid_flat", lid["flat_sealing_underside"] is True)
check("lid_seal_coverage", lid["sealing_band_coverage_ratio"] == 1.0)
check("lid_internal_penetration_zero", lid["internal_penetration_count"] == 0)
check("lid_body_intersection_zero", lid["placed_body_intersection_mm3"] == 0)
check("gasket_lid_intersection_zero", lid["placed_gasket_lid_intersection_mm3"] == 0)
check("gasket_body_intersection_zero", lid["placed_gasket_body_intersection_mm3"] == 0)
check("lid_a1", max(lid["external_bbox_mm"]) < 256.0)

printing = a["printability"]
check("a1", printing["build_volume_mm"] == [256.0, 256.0, 256.0])
check("a1_all", printing["all_parts_within_a1"] is True)
check("body_orientation", printing["body_orientation"] == "BOTTOM_DOWN_TOP_OPEN_SUPPORT_OFF_PREFERRED")
check("lid_orientation", printing["lid_orientation"] == "FLAT_SEALING_FACE_DOWN_SUPPORT_OFF_PREFERRED")
check("coupon_orientation", printing["coupon_orientation"] == "FUNCTIONAL_GROOVE_UP_SUPPORT_OFF")
check("slicer_hold", printing["slicer"] == "HOLD_SLICER_NOT_RUN")

# Artifact and physical firewall.
check("step_count", result["step_count"] == 6)
check("stl_count", result["stl_count"] == 5)
check("svg_count", result["svg_count"] == 9)
steps = result["artifacts"]["step"]; stls = result["artifacts"]["stl"]
check("steps_six", len(steps) == 6)
check("step_reload", all(row["reload"] == "PASS" and row["valid"] for row in steps.values()))
check("step_solids", all(row["solid_count"] >= 1 for row in steps.values()))
check("stls_five", len(stls) == 5)
check("stl_reload", all(row["reload"] == "PASS" for row in stls.values()))
check("stl_watertight", all(row["watertight"] for row in stls.values()))
check("stl_manifold", all(row["manifold"] for row in stls.values()))
check("stl_bad_edge_zero", all(row["bad_edge_count"] == 0 for row in stls.values()))
check("stl_degenerate_zero", all(row["degenerate_triangle_count"] == 0 for row in stls.values()))

release = a["release"]
check("first_print_three", release["first_print"] == ["artifacts/gasket_g18_a.stl", "artifacts/gasket_g18_b.stl", "artifacts/gasket_g18_c.stl"])
check("second_body", release["second_print"] == "artifacts/bbox_water_dummy_v002_body.stl")
check("third_lid", release["third_print"] == "artifacts/bbox_water_dummy_v002_lid.stl")
check("allowed_labels", release["allowed"] == ["CAD_PASS", "CONTRACT_TEST_PASS", "GASKET_COUPON_PRINT_READY", "V002_REFERENCE_COMPLETE"])
check("physical_labels_prohibited", all(label in release["prohibited"] for label in ["GASKET_FIT_PASS", "WATER_PASS", "POWERED_PASS", "FIELD_PASS"]))
check("no_fail", all(value != "FAIL" for value in report["checks"].values()))
check("water_not_yet", report["checks"]["water"] == "NOT_YET")
check("powered_prohibited", report["checks"]["powered"] == "PROHIBITED")
check("status", "GASKET_COUPON_PRINT_READY" in report["status"] and "SEALED_INTERNAL_PENETRATION_ZERO" in report["status"])

print(json.dumps({"contract": "PASS", "checks_passed": len(passed), "checks": passed}, indent=2))
