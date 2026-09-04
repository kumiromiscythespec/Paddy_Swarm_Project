"""Contract for PS-BBOX-LID-WIRING-CHIMNEY-V002 compact lane."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Paddy_Swarm_Project")
LANE = ROOT / "cad/common_rover/bbox_lid_wiring_chimney_v002_compact_50mm"
BUILDER = LANE / "build_bbox_lid_wiring_chimney_v002.py"

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
water = data["waterline"]

check("version", data["version"] == b.VERSION)
check("parent", data["parent"]["lane"] == b.V001_REL and data["parent"]["read_only"])
check("hole", data["physical_authority"]["gland_hole_authority_mm"] == 15.2)
check("fit", data["physical_authority"]["gland_hole_physical_fit"] == "PASS")
check("fit_not_water", data["physical_authority"]["waterproof_physical_validation"] == "NOT_PERFORMED")
check("thread", data["physical_authority"]["gland_male_thread_od_mm"] == 14.9)
check("cable", data["physical_authority"]["cable_od_mm"] == 9.6)
check("outer", data["chimney"]["external_xyz_mm"] == [50.0, 45.0, 50.0])
check("wall", data["chimney"]["wall_mm"] == 4.0)
check("internal", data["chimney"]["internal_xy_mm"] == [42.0, 37.0])
check("center", data["chimney"]["gland_center_above_lid_top_mm"] == 30.0)
check("direction", data["chimney"]["gland_direction"] == "CBOX_SIDE_POSITIVE_Y_HORIZONTAL")
check("integral", data["chimney"]["integral_with_lid"])
check("hood", data["chimney"]["rain_hood"]["retained"] and data["chimney"]["rain_hood"]["bottom_open"])
check("hood_compact", data["chimney"]["rain_hood"]["projection_mm"] == 8.0)
for key in ("gasket_loop_change", "seal_land_change", "lid_sealing_surface_change", "m4x8_pattern_change", "shell_interface_change", "fastening_geometry_change", "direction_change"):
    check("freeze_" + key, data["freeze"][key] == 0)
check("crawler_z", water["crawler_bottom_absolute_z_mm"] == 0.0)
check("frame_bottom", water["frame_bottom_absolute_z_mm"] == 64.0)
check("frame_top", water["frame_top_absolute_z_mm"] == 257.0)
check("lid_top", water["bbox_lid_top_absolute_z_mm"] == 257.0)
check("datum_class", "DERIVED_MOUNT_ASSUMPTION" in water["bbox_lid_top_datum_class"])
check("center_abs", water["gland_center_absolute_z_mm"] == 287.0)
check("center_margin150", water["gland_center_margin_to_z150_mm"] == 137.0)
check("effective", water["effective_waterline_z_mm"] == 210.0)
check("center_margin210", water["gland_center_margin_to_z210_mm"] == 77.0)
check("low", water["gland_hole_lowest_absolute_z_mm"] == 279.4)
check("low_margin150", water["gland_hole_lower_edge_margin_to_z150_mm"] == 129.4)
check("low_margin210", water["gland_hole_lower_edge_margin_to_z210_mm"] == 69.4)
check("no_field_claim", water["field_validation"] == "NOT_CLAIMED")
check("tool_hold", "HOLD" in data["tool_access"]["full_wrench_envelope"])
check("gland_remove", data["tool_access"]["gland_removal_without_lid_destruction"])
check("cable_pending", data["cable"]["routing_physical_dry_fit"] == "PENDING")
check("no_tpu", not data["tpu_future"]["cad_created"] and not data["tpu_future"]["sealing_boundary_integration"])
check("slicer_hold", "HOLD" in data["print"]["slicer"])
check("first_print", data["print"]["first_print"] == b.STLS[0])
check("status", data["status"] == "CAD_PASS/CONTRACT_TEST_PASS/COMPACT_CHIMNEY_LID_PRINT_READY/PHYSICAL_VALIDATION_PENDING")
for forbidden in ("WATERPROOF_PASS", "FIELD_PASS", "DROP_PASS", "TPU_PROTECTION_PASS"):
    check("forbidden_" + forbidden, forbidden in data["forbidden_claims"] and forbidden not in data["status"])
check("analysis_valid", validation["analysis"]["lid_valid"] and validation["analysis"]["lid_solids"] == 1)
check("seal_delta", validation["analysis"]["seal_land_delta_mm3"] == 0)
check("fastener_delta", validation["analysis"]["fastener_pattern_delta_mm3"] == 0)
check("clearance", validation["analysis"]["gland_diametral_clearance_mm"] == 0.3)
check("checks_all", validation["check_count"] == validation["pass_count"])
check("step_count", len(validation["steps"]) == len(b.STEPS))
check("steps_valid", all(row["valid"] for row in validation["steps"]))
check("stl_count", len(validation["stls"]) == len(b.STLS))
check("stl_quality", all(row["reload"] == "PASS" and row["watertight"] and row["manifold"] and row["bad_edge_count"] == 0 and row["degenerate_triangle_count"] == 0 for row in validation["stls"].values()))
check("repro", validation["reproducibility"]["status"] == "PASS" and not validation["reproducibility"]["mismatches"])
check("manifest_count", int(next(line.split("=", 1)[1] for line in (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() if line.startswith("EXACT_PATH_COUNT="))) == len(b.EXPECTED))
commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
check("commit_paths", commit_paths == [f"{b.LANE_REL.as_posix()}/{path}" for path in b.EXPECTED])
actual = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file())
check("exact_paths", actual == b.EXPECTED)
check("sha_file", all((LANE / line.split("  ", 1)[1]).exists() and hashlib.sha256((LANE / line.split("  ", 1)[1]).read_bytes()).hexdigest() == line.split("  ", 1)[0] for line in (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()))
repo = b.guard(True)
check("branch", repo["branch"] == b.BRANCH)
check("head", repo["head"] == b.HEAD)
check("staged", repo["staged"] == [])
check("dirty_preserved", repo["dirty"] == b.DIRTY)
check("authority", repo["checks"]["authority_4"])
check("protected", repo["checks"]["protected_7"])
check("outside", repo["checks"]["outside_preserved"])
check("cache", repo["checks"]["cache_zero"] and repo["checks"]["ignored_zero"])
print(f"CONTRACT_TEST_PASS {passed}/{passed}")
