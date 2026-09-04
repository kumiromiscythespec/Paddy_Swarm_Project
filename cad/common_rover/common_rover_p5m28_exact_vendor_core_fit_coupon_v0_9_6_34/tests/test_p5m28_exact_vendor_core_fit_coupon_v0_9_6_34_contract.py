"""Executable contract for v0.9.6.34 exact-vendor P5M28 fit coupons."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_p5m28_exact_vendor_core_fit_coupon_v0_9_6_34.py"
spec = importlib.util.spec_from_file_location("paddy_v09634", BUILDER)
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
report = json.loads((LANE / "data/validation_report.json").read_text(encoding="utf-8"))
source = report["geometry"]["source_geometry"]
main = source["main_body"]
coupons = report["geometry"]["coupons"]
outer = report["geometry"]["p20653_outer"]
reference = report["geometry"]["exact_core_reference"]
guard = report["repository_guard"]

check("repository", guard["repository"].lower() == str(m.REPO_ROOT).lower())
check("branch", guard["branch"] == m.EXPECTED_BRANCH)
check("head", guard["head"] == m.EXPECTED_HEAD)
check("staged_zero", guard["staged"] == [])
check("tracked_dirty_preserved", guard["tracked_dirty"] == m.TRACKED_DIRTY)
check("outside_untracked_preserved", tuple(guard["outside_untracked"]) == (m.BASE_OUTSIDE_COUNT, m.BASE_OUTSIDE_PATH_DIGEST))
check("authority_4_count", len(guard["authority_sha256"]) == 4)
for rel, expected in m.AUTHORITY_SHA256.items():
    check(f"authority_{rel}", guard["authority_sha256"][rel] == expected)
check("protected_lane_count", guard["protected_lanes"]["lane_count"] == m.PROTECTED_LANE_COUNT)
check("protected_file_count", guard["protected_lanes"]["file_count"] == m.PROTECTED_FILE_COUNT)
check("protected_aggregate", guard["protected_lanes"]["aggregate_sha256"] == m.PROTECTED_AGGREGATE_SHA256)
for rel, expected in m.PROTECTED_FOCUS.items():
    actual = guard["protected_lanes"]["focus"][rel]
    check(f"protected_{rel}_count", actual["count"] == expected[0])
    check(f"protected_{rel}_sha", actual["tree_sha256"] == expected[1])

check("source_zip_sha", guard["source_authority"]["zip_sha256"] == m.SOURCE_ZIP_SHA256)
check("source_step_sha", guard["source_authority"]["step_sha256"] == m.SOURCE_STEP_SHA256)
check("source_ap203", guard["source_authority"]["file_description_ap203"])
check("source_schema", guard["source_authority"]["file_schema_config_control_design"])
check("source_zip_copy_exact", m.sha256(LANE / m.SOURCE_FILES[0]) == m.SOURCE_ZIP_SHA256)
check("source_step_copy_exact", m.sha256(LANE / m.SOURCE_FILES[1]) == m.SOURCE_STEP_SHA256)

check("vendor_solid_count_5", source["solid_count"] == 5)
classifications = [row["classification"] for row in source["solids"]]
check("unique_main_one", classifications.count("UNIQUE_LARGEST_MAIN_PULLEY_BODY") == 1)
check("separate_flange_two", classifications.count("SEPARATE_THIN_50MM_FLANGE_CANDIDATE") == 2)
check("accessory_two", classifications.count("SEPARATE_SMALL_ACCESSORY_SOLID_NAME_NOT_INFERRED") == 2)
check("accessory_not_named_set_screw", all("SET_SCREW" not in value for value in classifications))
check("main_volume", abs(main["volume_mm3"] - 25568.41453550105) < 1e-5)
check("main_bbox_x", abs(main["bbox_mm"][0] - 21.0000002) < 1e-5)
check("main_bbox_radial_y", abs(main["bbox_mm"][1] - 43.27328383275754) < 1e-5)
check("main_bbox_radial_z", abs(main["bbox_mm"][2] - 43.27328383275757) < 1e-5)
check("exact_tooth_count_28", main["tooth_count_detected"] == 28)
check("pitch_5", main["pitch_mm_order_authority"] == 5.0)
check("tooth_zone_width_16p6", abs(main["tooth_zone_width_mm"] - 16.6) < 1e-9)
check("exact_tip_od_43p42", abs(main["exact_tooth_tip_od_mm"] - 43.42) < 1e-6)
check("exact_root_diameter_39p8", abs(main["exact_root_envelope_diameter_mm"] - 39.8) < 1e-6)
check("periodicity_angle", abs(main["periodicity_angle_deg"] - 360 / 28) < 1e-12)
check("periodicity_added_zero", main["periodicity_added_mm3"] == 0)
check("periodicity_removed_zero", main["periodicity_removed_mm3"] == 0)
check("no_approximation", main["tooth_geometry_source"] == "AP203_EXACT_SECTION_NO_APPROXIMATION")
check("normal_offset_kernel", "PARALLEL_OFFSET" in main["normal_offset_kernel"])
check("global_scaling_zero", main["global_xyz_scaling"] == 0.0)

for code, clearance, notch in (("C1", 0.15, 1), ("C2", 0.25, 2), ("C3", 0.35, 3)):
    row = coupons[code]
    check(f"{code}_clearance", row["clearance_radial_equivalent_mm"] == clearance)
    check(f"{code}_notch", row["notch_count"] == notch)
    check(f"{code}_engagement", row["engagement_mm"] == 9.0)
    check(f"{code}_axial_excess_zero", row["axial_excess_clearance_mm"] == 0.0)
    check(f"{code}_scale_one", row["global_xyz_scale"] == [1.0, 1.0, 1.0])
    check(f"{code}_wall_ge_5", row["minimum_wall_at_id_notch_mm"] >= 5.0)
    check(f"{code}_mass_low", row["estimated_petg_mass_g"] < 30.0)
    check(f"{code}_push_access", row["finger_push_access_count"] == 2)

check("p20653_pitch_frozen", abs(outer["pitch_mm"] - 20.6533333333) < 1e-10)
check("p20653_teeth_frozen", outer["tooth_count"] == 14)
check("p20653_pd_frozen", abs(outer["pitch_diameter_mm"] - 92.8152374974) < 1e-8)
check("p20653_phase_frozen", abs(outer["phase_deg"] - 12.8571428571) < 1e-9)
check("p20653_width_frozen", outer["tooth_axial_width_mm"] == 44.0)
check("p20653_14_regression", outer["p20653_14_tooth_regression"]["all_14_pass"])
check("p20653_added_zero", outer["p20653_14_tooth_regression"]["max_added_volume_mm3"] == 0)
check("p20653_removed_zero", outer["p20653_14_tooth_regression"]["max_removed_volume_mm3"] == 0)
check("outside_hub_added_zero", outer["outside_hub_modification_added_mm3"] == 0)
check("outside_hub_removed_zero", outer["outside_hub_modification_removed_mm3"] == 0)

check("c2_reference_only", reference["clearance"] == "C2_REFERENCE_ONLY")
check("c2_not_selected", not reference["selected_winner"])
check("exact_axial_remaining_23", abs(reference["total_axial_remaining_mm"] - 23.0) < 1e-9)
check("ligament_hard", reference["minimum_continuous_ligament_mm"] >= 5.0)
check("ligament_target", reference["minimum_continuous_ligament_mm"] >= 6.0)
check("ligament_stretch", reference["minimum_continuous_ligament_mm"] >= 8.0)

check("step_count_6", verify["step"] == 6)
check("source_step_count_1", verify["source_step"] == 1)
check("stl_count_4", verify["stl"] == 4)
check("svg_count_6", verify["svg"] == 6)
check("exact_path_count", verify["paths"] == m.EXPECTED_PATH_COUNT)
check("commit_path_count", len((LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()) == m.EXPECTED_PATH_COUNT)
check("manifest_exact", (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines() == m.EXPECTED_FILES)
check("sha_mismatch_zero", verify["sha_mismatches"] == [])
check("all_step_reload", verify["checks"]["step_6_of_6"])
check("all_stl_quality", verify["checks"]["stl_4_of_4"])

check("fit_print_approved", "FIT_COUPONS_PRINT_APPROVED" in report["status"])
check("physical_core_not_received", "PHYSICAL_CORE_NOT_RECEIVED" in report["status"])
check("fit_winner_not_yet", "FIT_WINNER_NOT_YET" in report["status"])
check("retention_not_yet", "RETENTION_NOT_YET" in report["status"])
check("full_drive_hold", "FULL_DRIVE_PRINT_HOLD" in report["status"])
check("static_torque_hold", "STATIC_TORQUE_HOLD" in report["status"])
check("powered_not_approved", "POWERED_NOT_APPROVED" in report["status"])

print(json.dumps({"result": "PASS", "tests": len(checks), "failed": 0}, ensure_ascii=False, indent=2))
