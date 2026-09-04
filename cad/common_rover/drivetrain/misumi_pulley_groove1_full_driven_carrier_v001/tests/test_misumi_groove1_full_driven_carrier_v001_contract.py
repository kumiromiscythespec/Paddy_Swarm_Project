"""Contract for the MISUMI Groove-1 full driven-wheel carrier V001."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_misumi_groove1_full_driven_carrier_v001.py"
spec = importlib.util.spec_from_file_location("misumi_groove1_carrier", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("BUILDER_IMPORT_FAILED")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
checks: list[tuple[str, bool]] = []


def check(name: str, condition: bool):
    checks.append((name, bool(condition)))
    if not condition:
        raise AssertionError(name)


data = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
validation = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
geometry = validation["geometry"]
check("guard", all(m.guard(True)["checks"].values()))
check("version", data["version"] == m.VERSION)
check("authority_lane", data["authority"]["lane"] == m.AUTH_REL.as_posix())
check("authority_hash", data["authority"]["tree_sha256"] == m.PROTECTED[m.AUTH_REL.as_posix()][1])
check("vendor_part", data["authority"]["vendor_part"] == "PTPK28P5M150-A-N10-NFC")
check("source_step", data["authority"]["source_step_sha256"] == m.SOURCE_STEP_SHA256)
check("direct_import", data["authority"]["reuse_method"].startswith("DIRECT_IMPORT"))
check("no_reconstruction", "NO_RECONSTRUCTION" in data["authority"]["reuse_method"])
check("no_scaling", "NO_SCALING" in data["authority"]["reuse_method"])

physical = data["physical_result"]
check("groove1_fit", physical["pulley_groove_1_physical_fit"] == "PASS")
check("hand_removable", physical["hand_removable"])
check("repeat_pass", physical["repeated_insertion_removal"] == "PASS")
check("crack_none", physical["cracking"] == "NONE")
check("whitening_none", physical["whitening"] == "NONE")
check("ride_none", physical["tooth_ride_over"] == "NONE")
check("deformation_none", physical["permanent_deformation"] == "NONE")
check("initial_backlash", physical["initial_rotational_backlash"] == "SLIGHT_APPROX_0P1MM_VISUAL")
check("backlash_growth_none", physical["backlash_growth_after_staged_manual_static_torque"] == "NONE")
check("tooth_damage_none", physical["tooth_damage"] == "NONE")
check("static_torque_pass", physical["pulley_groove_1_static_torque_transfer"] == "PASS")
check("interface_authority", physical["interface_authority"] == "FULL_CARRIER_INTERFACE_AUTHORITY")
check("no_tightening", physical["tightening_to_remove_initial_play"] == "PROHIBITED")

groove = data["groove1"]
check("groove_code", groove["code"] == "C1")
check("groove_clearance", groove["clearance_radial_equivalent_mm"] == 0.15)
check("groove_source", groove["source"] == "AP203_EXACT_SECTION_NO_APPROXIMATION")
check("p5m_pitch", groove["pitch_mm"] == 5.0)
check("p5m_teeth", groove["tooth_count"] == 28)
check("tip_od", groove["tip_od_mm"] == 43.42)
check("root_od", groove["root_od_mm"] == 39.8)
check("metal_tooth_width", groove["metal_tooth_width_mm"] == 16.6)
check("torque_primary", groove["torque_function"] == "PRIMARY_ROTATIONAL_TORQUE_PATH")

carrier = data["carrier"]
check("outer_frozen", carrier["outer_geometry"] == "PROTECTED_P20653_14T")
check("outer_teeth", carrier["outer_tooth_count"] == 14)
check("outer_pitch", carrier["outer_pitch_mm"] == m.OUTER_PITCH)
check("outer_width", carrier["outer_width_mm"] == 44.0)
check("metal_center", carrier["metal_center_z_mm"] == 11.0)
check("rear_seat", carrier["rear_seat_z_mm"] == 0.5)
check("shaft_clearance", carrier["shaft_clearance_diameter_mm"] == 12.0)
check("carrier_print_ready", carrier["status"] == "FULL_DRIVEN_WHEEL_CARRIER_PRINT_READY_PHYSICAL_VALIDATION_PENDING")

keeper = data["keeper"]
check("keeper_arch", keeper["architecture"] == "REMOVABLE_FRONT_ANNULAR_PLATE")
check("keeper_od", keeper["od_mm"] == 66.0)
check("keeper_id", keeper["id_mm"] == 36.0)
check("keeper_t", keeper["thickness_mm"] == 3.5)
check("keeper_gap", keeper["axial_gap_mm"] == 0.5)
check("screw_count", keeper["screw_count"] == 4)
check("screw_pcd", keeper["screw_pcd_mm"] == 56.0)
check("hole_d", keeper["printed_clearance_hole_mm"] == 5.5)
check("m5_candidate", keeper["hardware_candidate"] == "M5_THROUGH_BOLT_LOCKNUT_CANDIDATE")
check("hardware_hold", keeper["hardware_status"] == "PHYSICAL_FASTENER_SELECTION_PENDING")
check("keeper_not_torque", not keeper["primary_torque_path"])
check("no_glue", not keeper["glue"])
check("no_press_only", not keeper["permanent_press_fit"])
check("no_destructive", not keeper["destructive_removal"])

check("service_order", data["service"]["sequence"] == ["REMOVE_KEEPER_FASTENERS", "REMOVE_KEEPER", "WITHDRAW_METAL_PULLEY_PLUS_Z", "INSPECT_OR_REPLACE_PRINTED_CARRIER", "REINSTALL_PULLEY", "REINSTALL_KEEPER"])
check("not_trapped", not data["service"]["pulley_trapped"])
check("no_metal_damage", not data["service"]["metal_damage_required_for_removal"])
check("pretest_cycles", data["pretest"]["cycles"] == 5)
check("pretest_coupon", data["pretest"]["carrier_coupon"] == m.STLS[2])
check("pretest_keeper", data["pretest"]["keeper"] == m.STLS[1])

check("source_hash_geometry", geometry["source_step_sha256"] == m.SOURCE_STEP_SHA256)
check("source_zip_geometry", geometry["source_zip_sha256"] == m.SOURCE_ZIP_SHA256)
check("source_teeth_geometry", geometry["source_tooth_count"] == 28)
check("source_pitch_geometry", geometry["source_pitch_mm"] == 5.0)
check("source_tip_geometry", geometry["source_tip_od_mm"] == 43.42)
check("source_root_geometry", geometry["source_root_od_mm"] == 39.8)
check("source_edges", geometry["source_wire_edges"] == 224)
check("source_method", geometry["source_geometry_method"] == "AP203_EXACT_SECTION_NO_APPROXIMATION")
check("geometry_c1", geometry["groove_code"] == "C1")
check("geometry_clearance", geometry["groove_clearance_radial_equivalent_mm"] == 0.15)
check("profile_axial_9", geometry["groove_profile_bbox_mm"][2] == 9.0)
check("profile_volume", geometry["groove_profile_volume_mm3"] > 0)
check("engagement_16p6", geometry["groove_engagement_mm"] == 16.6)
check("outer_14", geometry["outer_tooth_count"] == 14)
check("outer_width_44", geometry["outer_width_mm"] == 44.0)
check("carrier_valid", geometry["carrier_valid"] and geometry["carrier_solids"] == 1)
check("keeper_valid", geometry["keeper_valid"] and geometry["keeper_solids"] == 1)
check("pretest_valid", geometry["pretest_valid"] and geometry["pretest_solids"] == 1)
check("carrier_metal_zero", geometry["carrier_metal_intersection_mm3"] == 0)
check("keeper_metal_zero", geometry["keeper_metal_intersection_mm3"] == 0)
check("keeper_carrier_zero", geometry["keeper_carrier_intersection_mm3"] == 0)
check("pretest_metal_zero", geometry["pretest_metal_intersection_mm3"] == 0)
check("outer_removed_zero", geometry["outer_tooth_removed_mm3"] == 0)
check("outer_added_zero", geometry["outer_tooth_added_mm3"] == 0)
check("keeper_tooth_zero", geometry["keeper_to_outer_tooth_mm3"] == 0)
check("keeper_root_clear", geometry["keeper_outer_to_root_clearance_mm"] == 0.55)
check("screw_root_clear", geometry["screw_outer_to_root_clearance_mm"] == 2.8)
check("radial_backing", geometry["radial_backing_at_groove_tip_mm"] == 11.69)
check("rear_backing", geometry["rear_shoulder_backing_mm"] == 22.5)
check("axial_gap", geometry["axial_keeper_gap_mm"] == 0.5)
check("shaft_d", geometry["shaft_clearance_diameter_mm"] == 12.0)
check("assembly_width", geometry["assembly_axial_width_mm"] == 47.5)
check("withdraw_plus_z", geometry["service_withdrawal_direction"] == "+Z_AFTER_KEEPER_REMOVAL")
check("torque_path", "EXACT_GROOVE1" in geometry["torque_path"])
check("retention_path", geometry["retention_path"] == "REMOVABLE_KEEPER_ONLY_NOT_PRIMARY_TORQUE")

check("validation_all", validation["pass_count"] == validation["check_count"])
check("step_count", len(validation["steps"]) == len(m.STEPS) == 6)
check("step_valid", all(row["valid"] for row in validation["steps"]))
check("step_solids", all(row["solids"] >= 1 for row in validation["steps"]))
check("stl_count", len(validation["stls"]) == len(m.STLS) == 3)
for path, metrics in sorted(validation["stls"].items()):
    check(f"reload_{path}", metrics["reload"] == "PASS")
    check(f"watertight_{path}", metrics["watertight"])
    check(f"manifold_{path}", metrics["manifold"])
    check(f"edges_{path}", metrics["bad_edge_count"] == 0)
    check(f"degenerate_{path}", metrics["degenerate_triangle_count"] == 0)
check("repro", validation["reproducibility"]["status"] == "PASS")
check("repro_exact", validation["reproducibility"]["byte_identical"] == validation["reproducibility"]["compared"])
check("repro_zero", validation["reproducibility"]["mismatches"] == [])
check("authority_4", len(validation["repository"]["authority"]) == 4)
check("protected_5", len(validation["repository"]["protected"]) == 5)
check("branch", validation["repository"]["branch"] == m.BRANCH)
check("head", validation["repository"]["head"] == m.HEAD)
check("assumption", "exact hardware length" in validation["assumptions"][0])

gates = data["gates"]
check("cad_pass", gates["cad"] == "CAD_PASS")
check("contract_pass", gates["contract"] == "CONTRACT_TEST_PASS")
check("print_ready", gates["print"] == "GROOVE1_FULL_CARRIER_PRINT_READY")
check("powered_pending", gates["powered_torque"] == "POWERED_TORQUE_VALIDATION_PENDING")
check("dry_pending", gates["crawler_dry_run"] == "CRAWLER_DRY_RUN_PENDING")
check("continuous_pending", gates["continuous_run"] == "CONTINUOUS_RUN_PENDING")
check("mud_pending", gates["mud"] == "MUD_RESISTANCE_PENDING")
check("field_pending", gates["field"] == "FIELD_PENDING")
for forbidden in data["forbidden_claims"]:
    check(f"forbidden_{forbidden}", forbidden not in data["status"])

paths = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file())
check("exact_paths", paths == m.EXPECTED)
commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
check("commit_count", len(commit_paths) == len(m.EXPECTED))
check("commit_exact", commit_paths == [m.LANE_REL.as_posix() + "/" + path for path in m.EXPECTED])
check("manifest", f"EXACT_PATH_COUNT={len(m.EXPECTED)}" in (LANE / "MANIFEST.txt").read_text(encoding="utf-8"))
sha_lines = (LANE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
check("sha_count", len(sha_lines) == len(m.EXPECTED) - 1)
for line in sha_lines:
    digest, relative = line.split("  ", 1)
    check(f"sha_{relative}", digest == hashlib.sha256((LANE / relative).read_bytes()).hexdigest())

print(f"CONTRACT={len(checks)}/{len(checks)} PASS")
print(f"EXACT_PATHS={len(m.EXPECTED)}")
print("STEP_RELOAD=6/6 PASS")
print("STL_QUALITY=3/3 PASS")
print(f"REPRO={validation['reproducibility']['byte_identical']}/{validation['reproducibility']['compared']} PASS")
