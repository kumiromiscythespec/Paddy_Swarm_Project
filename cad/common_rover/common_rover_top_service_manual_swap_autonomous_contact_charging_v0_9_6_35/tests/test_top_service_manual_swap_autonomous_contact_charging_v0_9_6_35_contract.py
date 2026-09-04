"""Executable contract for the v0.9.6.35 architecture decision."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_top_service_manual_swap_autonomous_contact_charging_v0_9_6_35.py"
spec = importlib.util.spec_from_file_location("paddy_v09635", BUILDER)
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

check("standard_exact", p["architecture"]["current_standard"] == ["TOP_SERVICE_MANUAL_SWAP", "AUTONOMOUS_CONTACT_CHARGING"])
check("battery_remains_normally", not p["architecture"]["normal_battery_removal"])
check("manual_top_swap", p["architecture"]["manual_top_swap"])
check("automatic_swap_not_current", not p["architecture"]["automatic_cassette_swap_current"])
check("rear_slide_superseded", "SUPERSEDED_AS_PRIMARY_ARCHITECTURE" in p["architecture"]["rear_slide"])
check("rear_slide_preserved", "PRESERVED_FOR_RESEARCH" in p["architecture"]["rear_slide"])

conflicts = p["authority_conflicts"]
check("authority_conflict_recorded", conflicts["resolution"] == "AUTHORITY_CONFLICT_RECORDED_NO_SYNTHETIC_UNIFIED_DIMENSION")
check("v228_bbox", conflicts["fixed_core_v228"]["bbox_body_nominal_mm"] == [200.0, 150.0, 120.0])
check("v228_lid", conflicts["fixed_core_v228"]["lid_nominal_mm"] == [216.0, 166.0, 16.0])
check("v228_gasket", conflicts["fixed_core_v228"]["gasket_nominal_mm"] == [204.0, 154.0, 3.0])
check("v0960_bbox", conflicts["submerged_v0_9_6_0"]["bbox_lower_shell_mm"] == [200.0, 130.0, 97.0])
check("v0960_lid", conflicts["submerged_v0_9_6_0"]["lid_mm"] == [200.0, 130.0, 4.2])
check("v0960_cbox", conflicts["submerged_v0_9_6_0"]["cbox_external_mm"] == [180.0, 92.0, 45.0])
check("v09632_cbox", conflicts["cbox_v0_9_6_32"]["cbox_body_mm"] == [246.0, 150.0, 80.0])
check("v09632_z_hold", conflicts["cbox_v0_9_6_32"]["z_placement"].startswith("HOLD"))
check("no_unified_bbox", "unified_bbox_mm" not in p)

battery = p["battery_physical_reference"]
check("battery_voltage_12p8", battery["voltage_v"] == 12.8)
check("battery_lifepo4", "LiFePO4" in battery["product"])
check("battery_body", battery["body_mm"] == [150.9, 99.4, 92.5])
check("battery_mass", battery["mass_kg"] == 1.2)

cbox = p["cbox_service"]
check("cbox_lateral_first", cbox["first_candidate"] == "LATERAL_SERVICE_SLIDE")
check("cbox_hinge_secondary", cbox["secondary"] == "HINGE_UP")
check("slide_direction_hold", cbox["direction"] == "HOLD")
check("slide_stroke_hold", cbox["stroke_mm"] == "HOLD")
check("slide_rail_hold", cbox["rail"] == "HOLD")
check("slide_lock_hold", cbox["lock"] == "HOLD")
check("cable_loop_hold", cbox["cable_service_loop"] == "HOLD")
check("automatic_actuation_false", not cbox["automatic_actuation"])
check("display_offsets_symmetric", cbox["display_only_symmetric_offsets_mm"][0] == -cbox["display_only_symmetric_offsets_mm"][1])

check("geometry_transparent_only", p["concept_geometry"]["classification"] == m.DISPLAY_GEOMETRY_AUTHORITY)
check("battery_sweep_derived", p["concept_geometry"]["battery_sweep_display_height_mm"] == 212.5)
check("operation_modes_four", set(p["operation_modes"]) == {"A", "B", "C", "D"})
check("mode_a_contact", "AUTONOMOUS_CONTACT_CHARGING" in p["operation_modes"]["A"])
check("mode_b_manual_supplement", "MANUAL_TOP_SWAP_SUPPLEMENTAL" in p["operation_modes"]["B"])
check("mode_c_isolate", "ISOLATE" in p["operation_modes"]["C"])
check("mode_d_not_current", "NOT_CURRENT_BASELINE" in p["operation_modes"]["D"])
check("protected_principles_8", len(p["protected_principles"]) == 8)
for principle in m.PROTECTED_PRINCIPLES:
    check(f"principle_{principle}", principle in p["protected_principles"])

water = p["current_water_dummy_v001"]
check("water_dummy_cad_pass", "CAD_PASS" in water["status_reference"])
check("water_dummy_contract_pass", "CONTRACT_PASS" in water["status_reference"])
check("water_dummy_print_not_yet", "PRINT_NOT_YET" in water["status_reference"])
check("water_dummy_role", water["role"] == "PRINTED_SHELL_TOP_SEAL_DEVELOPMENT_REFERENCE")
check("water_dummy_not_rear_slide", not water["rear_slide_validation"])
check("water_dummy_unmodified", not water["modified"])

for hold in m.HOLDS:
    check(f"hold_{hold}", hold in p["holds"])
check("battery_connector_hold", "BATTERY_POWER_CONNECTOR" in p["holds"])
check("contact_hardware_hold", "CHARGING_CONTACT_HARDWARE" in p["holds"])
check("charging_current_hold", "CHARGING_VOLTAGE_CURRENT" in p["holds"])

check("step_count_6", verify["step"] == 6)
check("svg_count_6", verify["svg"] == 6)
check("exact_path_count", verify["paths"] == m.EXPECTED_PATH_COUNT)
check("manifest_exact", (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == m.EXPECTED_FILES)
check("commit_paths_exact", len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == m.EXPECTED_PATH_COUNT)
check("sha_mismatch_zero", verify["sha_mismatches"] == [])
check("validation_all_pass", all(value == "PASS" for value in report["checks"].values()))
check("architecture_decision_recorded", "ARCHITECTURE_DECISION_RECORDED" in report["status"])
check("top_service_selected", "TOP_SERVICE_MANUAL_SWAP_SELECTED" in report["status"])
check("contact_charging_selected", "AUTONOMOUS_CONTACT_CHARGING_SELECTED" in report["status"])
check("transporter_redefined", "BATTERY_TRANSPORTER_ROLE_REDEFINED" in report["status"])
check("final_exact", report["final"] == ["ARCHITECTURE_SELECTED", "CAD_CONCEPT_COMPLETE", "PHYSICAL_VALIDATION_PENDING"])
for forbidden in ("CBOX_SLIDE_PHYSICAL_PASS", "BATTERY_SWAP_PHYSICAL_PASS", "CHARGING_CONTACT_PASS", "AUTONOMOUS_DOCKING_PASS", "WATER_PASS", "FIELD_PASS", "DURABILITY_PASS"):
    check(f"forbidden_absent_{forbidden}", forbidden not in report["status"])

print(json.dumps({"result": "PASS", "tests": len(checks), "failed": 0}, ensure_ascii=False, indent=2))
