"""Executable contract for v0.9.6.36 initial-freeware architecture."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_manual_cbox_service_top_battery_swap_v0_9_6_36.py"
spec = importlib.util.spec_from_file_location("paddy_v09636", BUILDER)
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
p = report["parameters"]
guard = report["repository_guard"]

check("repository", guard["repository"].lower() == str(m.REPO_ROOT).lower())
check("branch", guard["branch"] == m.EXPECTED_BRANCH)
check("head", guard["head"] == m.EXPECTED_HEAD)
check("staged_zero", guard["staged"] == [])
check("tracked_dirty_preserved", guard["tracked_dirty"] == m.TRACKED_DIRTY)
check("authority_4", guard["authority_sha256"] == m.AUTHORITY_SHA256)
check("outside_untracked_preserved", tuple(guard["outside_untracked"]) == (m.BASE_OUTSIDE_COUNT, m.BASE_OUTSIDE_PATH_DIGEST))
check("protected_lane_count", guard["protected"]["lane_count"] == m.PROTECTED_LANE_COUNT)
check("protected_file_count", guard["protected"]["file_count"] == m.PROTECTED_FILE_COUNT)
check("protected_aggregate", guard["protected"]["aggregate_sha256"] == m.PROTECTED_AGGREGATE_SHA256)
for rel, expected in m.PROTECTED_TREES.items():
    actual = guard["protected"]["focus"][rel]
    check(f"protected_count_{rel}", actual["count"] == expected[0])
    check(f"protected_sha_{rel}", actual["tree_sha256"] == expected[1])
for rel, expected in m.SOURCE_SHA256.items():
    check(f"source_sha_{rel}", guard["source_sha256"][rel] == expected)

check("standard_manual_side", "MANUAL_CBOX_SIDE_PLACEMENT" in p["initial_freeware_standard"])
check("standard_cable_900", "CBOX_SERVICE_CABLE_900MM" in p["initial_freeware_standard"])
check("standard_manual_top", "MANUAL_TOP_BATTERY_SWAP" in p["initial_freeware_standard"])
check("standard_contact_charge", "AUTONOMOUS_CONTACT_CHARGING" in p["initial_freeware_standard"])

check("cbox_x_150", p["cbox_physical_mm"][0] == 150.0)
check("cbox_y_246", p["cbox_physical_mm"][1] == 246.0)
check("cbox_z_80", p["cbox_physical_mm"][2] == 80.0)
check("cbox_exact", p["cbox_physical_mm"] == [150.0, 246.0, 80.0])
check("cbox_order_not_reassigned", p["cbox_physical_dimension_order"] == "AS_REPORTED_NO_AXIS_REASSIGNMENT")
check("manual_method", p["cbox_service_method"] == "MANUAL_SIDE_PLACEMENT")
check("manual_feasible", p["cbox_manual_side_placement"] == "PHYSICALLY_FEASIBLE")

check("cable_exact_900", p["cbox_service_cable_mm"] == 900.0)
check("cable_physical_authority", p["cbox_service_cable_authority"] == "USER_PHYSICAL_PLACEMENT_REFERENCE")
check("battery_height_exact_98p9", p["battery_physical_height_mm"] == 98.9)
check("battery_caliper", p["battery_height_authority"] == "USER_CALIPER_MEASUREMENT")
check("battery_vertical_top", p["battery_extraction"] == "MANUAL_VERTICAL_TOP")
check("battery_vertical_feasible", p["battery_vertical_extraction"] == "PHYSICALLY_FEASIBLE")
check("minimum_travel_exact", p["minimum_physical_vertical_extraction_travel_reference_mm"] == 98.9)
check("frame_hand_access", p["frame_hand_access"] == "PHYSICALLY_CONFIRMED")
check("frame_remeasurement", p["frame_internal_dimensions"] == "REMEASUREMENT_REQUIRED")

check("slide_mechanism_false", not p["cbox_slide_mechanism_required"])
for key, expected in m.NOT_REQUIRED_MECHANISMS.items():
    check(f"not_required_{key}", p["not_required_mechanisms"][key] == expected)
check("no_slide_hold", "CBOX_LATERAL_SLIDE_DIRECTION" not in p["remaining_holds"])
check("no_stroke_hold", "CBOX_REQUIRED_SERVICE_STROKE" not in p["remaining_holds"])

check("autonomous_charge_preserved", p["autonomous_contact_charging"])
check("automatic_swap_false", not p["automatic_battery_swap"])
check("users_type_1_2", p["initial_freeware_primary_users"] == ["TYPE_1", "TYPE_2"])
for value in ("SELF_BUILD", "SELF_REPAIR", "USER_DISCRETION", "FIELD_ADJUSTMENT"):
    check(f"philosophy_{value}", value in p["user_philosophy"])
for value in m.SAFETY_MINIMUMS:
    check(f"safety_{value}", value in p["safety_minimums"])
check("self_service_safety_text", "SELF_SERVICE ≠ SAFETY_RELAXATION" in (LANE / "SAFETY_MINIMUMS.md").read_text(encoding="utf-8"))

for hold in m.HOLDS:
    check(f"hold_{hold}", hold in p["remaining_holds"])
check("priority_drivetrain_first", p["development_priority"][0] == "DRIVETRAIN_TORQUE_TRANSMISSION")
check("priority_crawler_second", p["development_priority"][1] == "CRAWLER_DRY_RUN")
check("priority_seal_third", p["development_priority"][2] == "SEALING_BOUNDARY")

check("step_zero", verify["step"] == 0)
check("stl_zero", verify["stl"] == 0)
check("svg_five", verify["svg"] == 5)
check("exact_path_count", verify["paths"] == m.EXPECTED_PATH_COUNT)
check("manifest_exact", (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == m.EXPECTED_FILES)
check("commit_paths_exact", len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == m.EXPECTED_PATH_COUNT)
check("sha_mismatch_zero", verify["sha_mismatches"] == [])
check("validation_all_pass", all(value == "PASS" for value in report["checks"].values()))
check("architecture_pass", "ARCHITECTURE_UPDATE_PASS" in report["status"])
check("cbox_feasibility_pass", "CBOX_MANUAL_SIDE_PLACEMENT_PHYSICAL_FEASIBILITY_PASS" in report["status"])
check("cable_recorded", "CBOX_900MM_SERVICE_CABLE_PHYSICAL_REFERENCE_RECORDED" in report["status"])
check("battery_recorded", "BATTERY_98P9MM_PHYSICAL_HEIGHT_RECORDED" in report["status"])
check("initial_scope", "INITIAL_FREEWARE_USER_SCOPE_SELECTED" in report["status"])
check("final_exact", report["final"] == ["ARCHITECTURE_SIMPLIFIED", "INITIAL_FREEWARE_BASELINE_SELECTED", "PHYSICAL_VALIDATION_CONTINUES"])
for forbidden in m.FORBIDDEN_PASSES:
    check(f"forbidden_absent_{forbidden}", forbidden not in report["status"])

print(json.dumps({"result": "PASS", "tests": len(checks), "failed": 0}, ensure_ascii=False, indent=2))
