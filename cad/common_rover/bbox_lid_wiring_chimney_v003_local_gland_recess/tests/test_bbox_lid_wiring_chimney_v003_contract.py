"""Contract for the v003 local internal gland recess lane."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE = ROOT / "cad/common_rover/bbox_lid_wiring_chimney_v003_local_gland_recess"
BUILDER = LANE / "build_bbox_lid_wiring_chimney_v003.py"
spec = importlib.util.spec_from_file_location("builder", BUILDER)
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
analysis = validation["analysis"]
candidates = data["candidates"]
metrics = analysis["candidates"]

check("version", data["version"] == b.VERSION)
check("parent", data["parent"]["lane"] == b.V002_REL and data["parent"]["read_only"])
check("hole", data["physical_authority"]["gland_hole_mm"] == 15.2)
check("hole_fit", data["physical_authority"]["gland_hole_physical_fit"] == "PASS")
check("cable", data["physical_authority"]["cable_od_mm"] == 9.6 and data["physical_authority"]["cable_routing"] == "PASS")
check("locknut_fail", data["physical_authority"]["locknut_thread_engagement"] == "FAIL")
check("cause", data["physical_authority"]["failure_cause"] == "LOCAL_WALL_TOO_THICK")
check("thread", data["physical_authority"]["male_thread_length_mm_approx"] == 9.4)
check("nut_t", data["physical_authority"]["locknut_thickness_mm_approx"] == 4.6)
check("nut_od", data["physical_authority"]["locknut_outer_envelope_mm_approx"] == 24.0)
freeze = data["v002_freeze"]
check("outer", freeze["chimney_outer_xyz_mm"] == [50.0, 45.0, 50.0])
check("wall", freeze["normal_wall_mm"] == 4.0)
check("internal", freeze["chimney_internal_xy_mm"] == [42.0, 37.0])
check("center", freeze["gland_center_above_lid_top_mm"] == 30.0)
check("direction", freeze["gland_direction"] == "CBOX_SIDE_POSITIVE_Y_HORIZONTAL")
check("hole_frozen", freeze["gland_hole_mm"] == 15.2)
check("hood", freeze["rain_hood_projection_mm"] == 8.0)
for key in ("lid_outer_change", "gasket_loop_change", "seal_land_change", "lid_sealing_surface_change", "m4x8_pattern_change", "shell_interface_change", "fastening_geometry_change", "cable_routing_architecture_change"):
    check("freeze_" + key, freeze[key] == 0)
recess = data["recess"]
check("internal_only", recess["side"] == "INTERNAL_ONLY")
check("diameter", recess["diameter_mm"] == 30.0)
check("floor_clear", recess["flat_floor_clear_diameter_mm"] == 27.0)
check("flat", recess["floor"] == "FLAT")
check("outer_face", recess["external_face"] == "FLAT_UNRECESSED_UNCHANGED")
check("fillet_target", recess["target_fillet_mm"] == 1.5)
check("actual_stack", recess["v002_actual_local_stack_mm"] == 9.0)
check("candidate_walls", [row["local_effective_wall_mm"] for row in candidates] == [2.0, 2.2, 2.4])
check("requested_depths", [row["requested_recess_depth_from_4mm_wall_mm"] for row in candidates] == [2.0, 1.8, 1.6])
check("actual_depths", [row["actual_counterbore_depth_from_v002_inner_face_mm"] for row in candidates] == [7.0, 6.8, 6.6])
check("residuals", [row["nominal_thread_residual_mm"] for row in candidates] == [2.8, 2.6, 2.4])
check("candidate_pending", all(row["authority"] == "PHYSICAL_VALIDATION_PENDING" for row in candidates))
check("primary", data["primary_candidate_mm"] == 2.2)
check("selection", data["selection_policy"] == "PREFER_2P4_IF_FULL_PASS_ELSE_2P2_ELSE_2P0_IF_REQUIRED")
check("full_generated", data["full_lid"]["generated"] and data["full_lid"]["candidate_wall_mm"] == 2.2)
check("full_hold", data["full_lid"]["status"] == "HOLD_PENDING_LOCAL_RECESS_PHYSICAL_VALIDATION")
check("first_order", data["print"]["first_print_order"] == [b.STLS[2], b.STLS[1], b.STLS[0]])
check("slicer_hold", "HOLD" in data["print"]["slicer"])
check("status", "LOCAL_RECESS_COUPONS_PRINT_READY" in data["status"] and "PHYSICAL_VALIDATION_PENDING" in data["status"] and "FULL_LID_HOLD" in data["status"])
for forbidden in ("LOCKNUT_PHYSICAL_PASS", "WATERPROOF_PASS", "DROP_PASS", "FIELD_PASS"):
    check("forbidden_" + forbidden, forbidden in data["forbidden_claims"] and forbidden not in data["status"])
check("metric_walls", [row["measured_floor_thickness_mm"] for row in metrics] == [2.0, 2.2, 2.4])
check("metric_normal", all(row["normal_wall_measured_mm"] == 4.0 for row in metrics))
check("fillets", all(row["fillet_status"] == "R1P5_PROFILE_APPLIED" and row["fillet_applied_mm"] == 1.5 for row in metrics))
check("fillet_clear", all(row["locknut_radial_clearance_after_fillet_mm"] >= 1.5 for row in metrics))
check("candidate_valid", all(row["valid"] and row["solids"] == 1 for row in metrics))
check("primary_valid", analysis["primary_valid"] and analysis["primary_solids"] == 1)
check("external_zero", analysis["external_sealing_face_delta_mm3"] == 0)
check("hood_zero", analysis["rain_hood_delta_mm3"] == 0)
check("seal_zero", analysis["seal_land_delta_mm3"] == 0)
check("fastener_zero", analysis["fastener_pattern_delta_mm3"] == 0)
check("gasket_zero", analysis["gasket_loop_change_count"] == 0)
check("center_zero", analysis["gland_center_change_mm"] == 0)
check("hole_zero", analysis["gland_hole_change_mm"] == 0)
check("height_zero", analysis["chimney_height_change_mm"] == 0)
check("a1", analysis["a1_envelope_pass"])
check("checks_all", validation["check_count"] == validation["pass_count"])
check("step_count", len(validation["steps"]) == len(b.STEPS))
check("steps", all(row["valid"] for row in validation["steps"]))
check("stl_count", len(validation["stls"]) == len(b.STLS))
check("stls", all(row["reload"] == "PASS" and row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in validation["stls"].values()))
check("repro", validation["reproducibility"]["status"] == "PASS" and not validation["reproducibility"]["mismatches"])
manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
check("manifest_count", int(next(line.split("=", 1)[1] for line in manifest if line.startswith("EXACT_PATH_COUNT="))) == len(b.EXPECTED))
commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
check("commit_paths", commit_paths == [f"{b.LANE_REL.as_posix()}/{path}" for path in b.EXPECTED])
actual = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file())
check("exact_paths", actual == b.EXPECTED)
check("sha_file", all((LANE / line.split("  ", 1)[1]).exists() and hashlib.sha256((LANE / line.split("  ", 1)[1]).read_bytes()).hexdigest() == line.split("  ", 1)[0] for line in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()))
repo = b.guard(True)
check("branch", repo["branch"] == b.BRANCH)
check("head", repo["head"] == b.HEAD)
check("staged", repo["staged"] == [])
check("dirty", repo["dirty"] == b.DIRTY)
check("authority", repo["checks"]["authority_4"])
check("protected", repo["checks"]["protected_8"])
check("outside", repo["checks"]["outside_preserved"])
check("cache", repo["checks"]["cache_zero"] and repo["checks"]["ignored_zero"])
print(f"CONTRACT_TEST_PASS {passed}/{passed}")
