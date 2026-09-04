"""Contract for selected v003 2.4 mm full-lid CAD."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE = ROOT / "cad/common_rover/bbox_lid_wiring_chimney_v003_full_lid_2p4_authority"
BUILDER = LANE / "build_bbox_lid_wiring_chimney_v003_full_lid_2p4.py"
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
geometry = validation["geometry"]
selection = data["physical_selection"]
check("version", data["version"] == b.VERSION)
check("parent", data["parent"]["lane"] == b.PARENT_REL and data["parent"]["read_only"])
check("hole_authority", selection["gland_hole_authority_mm"] == 15.2 and selection["gland_hole_physical_fit"] == "PASS")
check("selected", selection["selected_local_gland_wall_mm"] == 2.4)
check("coupon_fit", selection["coupon_gland_fit"] == "PASS")
check("coupon_thread", selection["coupon_locknut_thread_engagement"] == "PASS")
check("gasket_depth", selection["gasket_included_depth"] == "APPROPRIATE_OBSERVED")
check("no_thinner", not selection["thinner_wall_required"])
check("cad_authorized", selection["selection_authority"] == "FULL_LID_CAD_AUTHORIZED")
check("sealing_not_authorized", selection["full_lid_physical_sealing"] == "NOT_AUTHORIZED_BY_COUPON")
g = data["geometry"]
check("outer", g["chimney_outer_xyz_mm"] == [50.0, 45.0, 50.0])
check("internal", g["chimney_internal_xy_mm"] == [42.0, 37.0])
check("normal_wall", g["normal_wall_mm"] == 4.0)
check("stack", g["local_stack_mm"] == 9.0)
check("local_wall", g["selected_local_wall_mm"] == 2.4)
check("depth", g["counterbore_depth_mm"] == 6.6)
check("internal_only", g["recess_side"] == "INTERNAL_ONLY")
check("mouth", g["recess_entry_diameter_mm"] == 30.0)
check("seat", g["flat_seat_diameter_mm"] == 27.0)
check("transition", g["transition_r_mm"] == 1.5)
check("hole", g["gland_hole_mm"] == 15.2)
check("center", g["gland_center_above_lid_top_mm"] == 30.0)
check("direction", g["gland_direction"] == "CBOX_SIDE_POSITIVE_Y_HORIZONTAL")
check("hood", g["rain_hood_projection_mm"] == 8.0)
for key, value in data["protected"].items():
    check("protected_" + key, value == 0)
check("d40_not_blocker", not data["mechanical_access"]["generic_d40_proxy_design_blocker"])
check("tool_pending", data["mechanical_access"]["full_lid_tool_access"] == "PHYSICAL_VALIDATION_PENDING")
check("derived_waterline", data["waterline"]["authority_class"] == "DERIVED_PHYSICAL_DATUM_PENDING")
check("measurements", data["waterline"]["next_measurement_required"] == ["LID_TOP_Z", "GLAND_CENTER_Z", "GLAND_HOLE_LOWEST_Z", "CHIMNEY_TOP_Z"])
check("first_print", data["print"]["first_print"] == b.STL)
check("status", data["status"] == "CAD_PASS/CONTRACT_TEST_PASS/FULL_LID_2P4_PRINT_READY/SELECTED_LOCAL_GLAND_WALL_2P4/PHYSICAL_VALIDATION_PENDING")
for forbidden in ("WATERPROOF_PASS", "RAIN_PASS", "TILT_PASS", "DROP_PASS", "FIELD_PASS"):
    check("forbidden_" + forbidden, forbidden in data["forbidden_claims"] and forbidden not in data["status"])
check("measured_local", geometry["measured_local_wall_mm"] == 2.4)
check("measured_normal", geometry["measured_normal_wall_mm"] == 4.0)
check("measured_depth", geometry["counterbore_depth_mm"] == 6.6)
check("valid", geometry["valid"] and geometry["solids"] == 1)
check("bbox", geometry["bbox_mm"] == geometry["parent_bbox_mm"])
check("external_zero", geometry["external_sealing_face_delta_mm3"] == 0)
check("hood_zero", geometry["rain_hood_delta_mm3"] == 0)
check("seal_zero", geometry["seal_land_delta_mm3"] == 0)
check("fastener_zero", geometry["fastener_pattern_delta_mm3"] == 0)
check("gasket_zero", geometry["gasket_loop_change_count"] == 0)
check("outer_zero", geometry["lid_outer_geometry_change_count"] == 0)
check("no_added", geometry["added_volume_vs_v002_mm3"] == 0)
check("checks", validation["check_count"] == validation["pass_count"])
check("step", validation["step"]["valid"] and validation["step"]["solids"] == 1)
mesh = validation["stl"]
check("stl", mesh["reload"] == "PASS" and mesh["watertight"] and mesh["manifold"] and mesh["bad_edge_count"] == 0 and mesh["degenerate_triangle_count"] == 0)
check("repro", validation["reproducibility"]["status"] == "PASS" and not validation["reproducibility"]["mismatches"])
manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
check("manifest", int(next(line.split("=", 1)[1] for line in manifest if line.startswith("EXACT_PATH_COUNT="))) == len(b.EXPECTED))
commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
check("commit_paths", commit_paths == [f"{b.LANE_REL.as_posix()}/{path}" for path in b.EXPECTED])
actual = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file())
check("exact_paths", actual == b.EXPECTED)
check("sha", all((LANE / line.split("  ", 1)[1]).exists() and hashlib.sha256((LANE / line.split("  ", 1)[1]).read_bytes()).hexdigest() == line.split("  ", 1)[0] for line in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()))
repo = b.guard(True)
check("branch", repo["branch"] == b.BRANCH)
check("head", repo["head"] == b.HEAD)
check("staged", repo["staged"] == [])
check("dirty", repo["dirty"] == b.DIRTY)
check("authority", repo["checks"]["authority_4"])
check("protected", repo["checks"]["protected_9"])
check("outside", repo["checks"]["outside_preserved"])
check("cache", repo["checks"]["cache_zero"] and repo["checks"]["ignored_zero"])
print(f"CONTRACT_TEST_PASS {passed}/{passed}")
