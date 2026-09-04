"""Contract for DS3218 reusable physical-authority CAD."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE = ROOT / "cad/common/servo/ds3218_20kg_180deg_physical_authority_v001"
BUILDER = LANE / "build_ds3218_physical_authority_v001.py"
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
check("version", data["version"] == b.VERSION)
check("model", data["servo"]["model"] == "DS3218_20KG_DIGITAL_SERVO")
check("range", data["servo"]["operating_range_deg"] == 180)
check("case", data["servo"]["case_lwh_mm"] == [40.0, 20.4, 41.7])
check("case_status", data["servo"]["case_status"] == "PHYSICAL_AUTHORITY")
check("envelope", data["servo"]["mounting_envelope_length_mm"] == 54.5)
mount = data["mounting"]
check("pitch_x", mount["longitudinal_hole_pitch_mm"] == 49.1)
check("pitch_y", mount["short_axis_hole_pitch_mm"] == 10.0 and mount["short_axis_pitch_status"] == "PHYSICAL_CANDIDATE")
check("physical_hole", mount["servo_physical_hole_mm"] == 4.6)
check("printed_distinct", mount["printed_bracket_fastener_hole_candidate_mm"] == 5.0 and mount["printed_hole_status"] == "DESIGN_CLEARANCE_CANDIDATE")
check("hardware_pending", mount["hardware"] == "PHYSICAL_FASTENER_SELECTION_PENDING")
check("ear_hold", "PLACEHOLDER" in mount["ear_z_status"])
coord = data["coordinate_system"]
check("datum", coord["bottom_plane_z_mm"] == 0 and coord["near_case_end_x_mm"] == 0 and coord["one_case_side_y_mm"] == 0)
axis = data["output_axis"]
check("output_x", axis["x_mm"] == 10.1 and axis["x_status"] == "PHYSICAL_PRIMARY_DATUM")
check("opposite", axis["opposite_end_derived_mm"] == 29.9)
check("visual_not_averaged", axis["separate_visual_opposite_mm"] == 29.2 and axis["averaging_prohibited"])
check("output_y", axis["y_mm"] == 10.2 and "DERIVED" in axis["y_status"])
check("origin", axis["horn_axis_origin_mm"] == [10.1, 10.2, 46.2])
check("spline", axis["spline"] == "25T" and "PLACEHOLDER" in axis["spline_geometry_status"])
horn = data["horn"]
check("horn_radius", horn["selected_link_hole_radius_mm"] == 30.0)
check("old32", horn["prior_32mm_interpretation"] == "OVERALL_LENGTH_NOT_LINK_RADIUS")
check("horn_t", horn["thickness_mm"] == 2.4)
check("horn_bottom", horn["bottom_z_mm"] == 45.0 and "UNCERTAINTY" in horn["bottom_z_status"])
check("horn_plane", horn["rotation_plane_z_mm"] == 46.2 and horn["rotation_plane_status"] == "PHYSICAL_DERIVED")
check("max_h", horn["servo_with_horn_max_height_mm"] == 48.0 and horn["max_height_status"] == "PHYSICAL_MAX_ENVELOPE")
check("horn_hole_hold", horn["link_hole_diameter_status"] == "CAD_VISUAL_PLACEHOLDER")
keepouts = data["keepouts"]
check("nominal", keepouts["nominal"]["radius_mm"] == 30.0 and keepouts["nominal"]["sweep_deg"] == 180.0 and keepouts["nominal"]["plane_z_mm"] == 46.2)
check("conservative", keepouts["conservative"]["radius_mm"] == 30.0 and keepouts["conservative"]["sweep_deg"] == 360 and not keepouts["conservative"]["powered_360_claim"])
check("keepout_ratio", 0.49 <= geometry["keepout_volume_ratio"] <= 0.51)
cable = data["cable"]
check("cable_length", cable["length_mm_approx"] == 303.0)
check("cable_placeholder", "PLACEHOLDER" in cable["exit_center_status"])
check("bend_hold", cable["bend_radius"] == "CABLE_BEND_RADIUS_PHYSICAL_VALIDATION_PENDING")
check("no_bad_bend", not cable["hard_90deg_bend"] and not cable["clamp_at_root"])
check("fit", data["fit_coupons"]["total_clearances_mm"] == [0.3, 0.5, 0.7])
check("fit_pending", data["fit_coupons"]["selection"] == "PHYSICAL_VALIDATION_PENDING")
bracket = data["bracket"]
check("bracket_open", bracket["architecture"] == "OPEN_CRADLE_WITH_MOUNT_EAR_SHELVES")
check("bracket_service", bracket["servo_removable"] and not bracket["glue_primary"] and bracket["horn_removable"])
check("bracket_hold", bracket["status"] == "HOLD_PENDING_CASE_AND_HOLE_COUPON_PHYSICAL_VALIDATION")
load = data["load_note"]
check("torque", load["max_torque_kgf_cm_at_6p8v"] == 21.5)
check("force", load["endpoint_force_kgf"] == 7.167 and load["endpoint_force_n"] == 70.3)
check("load_class", load["classification"] == "THEORETICAL_MAX_FROM_PRODUCT_SPEC" and not load["bracket_structural_pass"])
check("status", "DS3218_PHYSICAL_AUTHORITY_MODEL_READY" in data["status"] and "FIT_COUPONS_PRINT_READY" in data["status"] and "MOUNT_PHYSICAL_VALIDATION_PENDING" in data["status"])
for forbidden in ("LOAD_PASS", "TORQUE_PASS", "FIELD_PASS", "DURABILITY_PASS"):
    check("forbidden_" + forbidden, forbidden in data["forbidden_claims"] and forbidden not in data["status"])
check("servo_valid", geometry["servo_valid"])
check("bracket_valid", geometry["bracket_valid"])
check("servo_bracket_zero", geometry["servo_bracket_intersection_mm3"] == 0)
check("nominal_clear", geometry["bracket_nominal_keepout_intersection_mm3"] == 0)
check("full_clear", geometry["bracket_conservative_keepout_intersection_mm3"] == 0)
check("centers", geometry["mount_hole_centers_mm"] == [[-4.55, 5.2], [-4.55, 15.2], [44.55, 5.2], [44.55, 15.2]])
check("axis_geometry", geometry["output_axis_mm"] == [10.1, 10.2])
check("a1", geometry["a1_envelope_pass"])
check("validation", validation["check_count"] == validation["pass_count"])
check("step_count", len(validation["steps"]) == len(b.STEPS))
check("steps", all(row["valid"] for row in validation["steps"]))
check("stl_count", len(validation["stls"]) == len(b.STLS))
check("stls", all(row["reload"] == "PASS" and row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in validation["stls"].values()))
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
check("protected", repo["checks"]["protected_5"])
check("outside", repo["checks"]["outside_preserved"])
check("cache", repo["checks"]["cache_zero"] and repo["checks"]["ignored_zero"])
print(f"CONTRACT_TEST_PASS {passed}/{passed}")
