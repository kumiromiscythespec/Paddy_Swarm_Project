"""Executable contract for the v0.9.6.32 modular waterproof CBOX lane."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_cbox_246x150x80_modular_waterproof_control_box_v0_9_6_32.py"
spec = importlib.util.spec_from_file_location("paddy_v09632_contract", BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import builder")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def main() -> int:
    passed: list[str] = []
    failed: list[str] = []

    def check(name: str, condition: bool) -> None:
        (passed if condition else failed).append(name)

    result = b.verify()
    report = json.loads((LANE / "data/validation_report.json").read_text(encoding="utf-8"))
    geom = report["geometry"]
    repo = result["repository"]
    shell = geom["shell"]
    printable = geom["print"]
    gasket = geom["gasket"]
    lid = geom["lid"]
    carrier = geom["carrier"]
    seal = geom["seal_firewall"]
    electrical = geom["electrical"]
    placement = geom["placement"]

    check("repository", Path(repo["repository"]).resolve() == b.REPO_ROOT.resolve())
    check("branch", repo["branch"] == b.EXPECTED_BRANCH)
    check("head", repo["head"] == b.EXPECTED_HEAD)
    check("staged_zero", repo["staged"] == [])
    check("tracked_dirty_exact", repo["tracked_dirty"] == b.TRACKED_DIRTY)
    check("outside_snapshot", tuple(repo["outside_untracked"]) == (b.BASE_OUTSIDE_COUNT, b.BASE_OUTSIDE_PATH_DIGEST))
    check("lane_complete", repo["lane_files"] == b.EXPECTED_PATH_COUNT)
    check("lane_cache_zero", repo["cache"] == [])
    check("lane_forbidden_zero", repo["forbidden"] == [])
    check("lane_ignored_zero", repo["ignored_lane"] == [])

    for rel, expected in b.AUTHORITY_SHA256.items():
        check(f"authority_{rel}", repo["authority_sha256"][rel] == expected)
    for rel, expected in b.SOURCE_SHA256.items():
        check(f"source_{rel}", repo["source_sha256"][rel] == expected)
    for rel, expected in b.PROTECTED_LANES.items():
        row = repo["protected_lanes"][rel]
        check(f"protected_count_{rel}", row["count"] == expected[0])
        check(f"protected_sha_{rel}", row["tree_sha256"] == expected[1])
        check(f"protected_status_{rel}", row["status"] == "UNCHANGED")

    actual = sorted(path.relative_to(LANE).as_posix() for path in LANE.rglob("*") if path.is_file())
    manifest = (LANE / "MANIFEST.txt").read_text(encoding="utf-8").splitlines()
    commit_paths = (LANE / "COMMIT_PATHS.txt").read_text(encoding="utf-8").splitlines()
    check("path_count_28", len(actual) == 28)
    check("files_exact", actual == b.EXPECTED_FILES)
    check("manifest_exact", manifest == b.EXPECTED_FILES)
    check("commit_count_28", len(commit_paths) == 28)
    check("commit_exact", commit_paths == [f"{b.LANE_REL.as_posix()}/{rel}" for rel in b.EXPECTED_FILES])
    for rel in b.EXPECTED_FILES:
        check(f"manifest_member_{rel}", rel in manifest)

    check("version", report["version"] == "v0.9.6.32")
    check("classification", report["classification"] == b.CLASSIFICATION)
    check("status", report["status"] == b.STATUS)
    check("body_outer", shell["body_outer_mm"] == [246.0, 150.0, 80.0])
    check("shell_print_bbox", shell["total_print_bbox_mm"] == [246.0, 152.0, 80.0])
    check("main_cavity", shell["main_cavity_mm"] == [238.0, 142.0, 67.0])
    check("throat", shell["removal_throat_mm"] == [220.0, 126.0])
    check("wall", shell["wall_min_mm"] >= 4.0)
    check("floor", shell["floor_min_mm"] >= 5.0)
    check("corner", shell["corner_radius_mm"] == 12.0)
    check("shell_valid", shell["valid"] is True)
    check("shell_solid_one", shell["solid_count"] == 1)
    check("shell_open_top", shell["bottom_closed_top_open"] is True)
    check("floor_penetration_zero", shell["floor_penetration_count"] == 0)
    check("gland_hole_zero", shell["gland_through_hole_count"] == 0)
    check("gland_field_8", shell["gland_field_local_wall_mm"] == 8.0)

    check("a1_model", printable["printer"] == "Bambu Lab A1")
    check("a1_area", printable["build_area_mm"] == [256.0, 256.0])
    check("hard_contract", printable["hard_contract_mm"] == [248.0, 152.0])
    check("shell_margin", printable["shell_margin_total_mm"] == [10.0, 104.0])
    check("shell_hard_x", shell["total_print_bbox_mm"][0] <= 248.0)
    check("shell_hard_y", shell["total_print_bbox_mm"][1] <= 152.0)
    check("carrier_hard", max(carrier["bbox_mm"][:2]) <= 248.0)
    check("lid_hard", lid["bbox_mm"][0] <= 248.0 and lid["bbox_mm"][1] <= 152.0)
    check("shell_unsplit", printable["shell_no_split"] is True)
    check("seam_zero", printable["waterproof_glued_seam_count"] == 0)

    check("gasket_type", gasket["type"] == "CLOSED_LOOP_SOLID_SILICONE_CANDIDATE")
    check("gasket_thickness", gasket["nominal_thickness_mm"] == 2.0)
    check("gasket_compression_options", gasket["compression_candidates_percent"] == [20.0, 22.5, 25.0])
    check("gasket_reference", gasket["reference_compression_percent"] == 22.5)
    check("gasket_land", gasket["land_minimum_width_mm"] >= 8.0)
    check("gasket_width", gasket["radial_width_mm"] == 3.0)
    check("gasket_closed", gasket["solid_count"] == 1)
    check("fastener_gasket_zero", gasket["fastener_intersection_mm3"] == 0.0)
    check("fastener_gasket_separation", gasket["fastener_minimum_separation_mm"] >= 3.0)
    check("fastener_rows_8", len(gasket["fastener_rows"]) == 8)
    for row in gasket["fastener_rows"]:
        check(f"fastener_intersection_{row['index']}", row["intersection_mm3"] == 0.0)
        check(f"fastener_separation_{row['index']}", row["minimum_separation_mm"] >= 3.0)

    check("lid_fasteners", lid["fastening_points_candidate"] == 8)
    check("lid_electrical_penetration_zero", lid["electrical_penetration_count"] == 0)
    check("lid_no_cable", lid["cable_attached"] is False)
    check("lid_no_estop", lid["estop_mounted"] is False)
    check("lid_stop_reserve", "METAL_STOP" in lid["compression_stop_geometry"])
    check("lid_print_hold", lid["print_gate"] == "HOLD_AFTER_SHELL_CARRIER_PHYSICAL_LAYOUT")

    check("carrier_bbox", carrier["bbox_mm"] == [208.0, 112.0, 4.0])
    check("carrier_bottom_z", carrier["installed_bottom_z_mm"] == 11.0)
    check("carrier_bottom_clearance", carrier["bottom_clearance_mm"] >= 6.0)
    check("routing_corridor", carrier["routing_corridor_each_side_mm"] == [15.0, 15.0])
    check("throat_margin", carrier["throat_removal_margin_each_side_mm"] == [6.0, 7.0])
    check("carrier_shell_zero", carrier["carrier_vs_shell_installed_mm3"] == 0.0)
    check("boss_floor_zero", carrier["blind_boss_hole_vs_floor_mm3"] == 0.0)
    check("boss_count", carrier["mounting_boss_count"] == 6)
    check("carrier_universal", carrier["architecture"] == "REMOVABLE_UNIVERSAL_GRID_SLOTS_ZIP_TIE_SLOTS")
    check("no_specific_holes", carrier["component_specific_hole_release"] is False)

    check("blind_fastener_cavity_zero", seal["blind_fastener_vs_wet_cavity_mm3"] == 0.0)
    check("seal_floor_zero", seal["floor_penetration_count"] == 0)
    check("seal_gland_zero", seal["gland_through_hole_count"] == 0)
    check("seal_lid_zero", seal["lid_electrical_penetration_count"] == 0)

    check("interface_count", electrical["bbox_to_cbox_conductor_count"] == 2)
    check("interface_exact", electrical["bbox_to_cbox_conductors"] == ["+12.8V", "GND"])
    check("bbox_battery", "LiFePO4_12.8V_BATTERY" in electrical["bbox_roles"])
    check("bbox_fuse", "MAIN_FUSE_AT_BATTERY_POSITIVE" in electrical["bbox_roles"])
    check("cbox_md10_l", "MD10C_L" in electrical["cbox_roles"])
    check("cbox_md10_r", "MD10C_R" in electrical["cbox_roles"])
    check("power_logic_split", electrical["power_logic_corridors_separate"] is True)
    check("driver_gap_target", electrical["md10c_driver_gap_target_mm"] == 20.0)
    check("estop_relay", electrical["estop_current_path"] == "ESTOP_CONTACT_TO_RELAY_COIL_ONLY")
    check("estop_no_main_current", electrical["motor_main_current_through_estop"] is False)
    check("thermal_hold", electrical["thermal"] == "CBOX_THERMAL_VALIDATION_PENDING")

    check("z_hold", placement["cbox_z_placement"].startswith("HOLD_"))
    check("stack_gap", placement["local_stack_gap_mm"] == 8.0)
    check("bbox_contact_zero", placement["bbox_to_cbox_nominal_contact_mm3"] == 0.0)
    check("bbox_distance_8", math.isclose(placement["bbox_to_cbox_minimum_distance_mm"], 8.0, abs_tol=1e-6))
    check("bbox_extract_zero", placement["bbox_extraction_envelope_vs_cbox_mm3"] == 0.0)
    check("bbox_lid_structural_zero", placement["bbox_structural_lid_penetration_count"] == 0)
    check("frame_plan_ref", placement["frame_plan_envelope"].startswith("PASS_REFERENCE"))
    check("frame_hold", placement["frame_collision"] == "HOLD_CBOX_Z_PLACEMENT")
    check("crawler_hold", placement["crawler_collision"].startswith("UNKNOWN_HOLD"))
    check("motor_hold", placement["motor_transmission_collision"].startswith("UNKNOWN_HOLD"))
    check("pto_hold", placement["pto_collision"].startswith("UNKNOWN_HOLD"))
    check("turtle_hold", placement["turtle_shell_collision"].startswith("UNKNOWN_HOLD"))
    check("no_frame_holes", placement["upper_bridge_mount"] == "HOLD_NO_NEW_FRAME_HOLES")

    check("step_count", result["step_count"] == 4)
    check("stl_count", result["stl_count"] == 2)
    check("svg_count", result["svg_count"] == 6)
    for rel, row in result["step_import"].items():
        check(f"step_valid_{rel}", row["valid"] is True)
        check(f"step_reload_{rel}", row["reload"] == "PASS")
    for rel, row in result["mesh"].items():
        check(f"stl_watertight_{rel}", row["watertight"] is True)
        check(f"stl_bad_edges_{rel}", row["bad_edge_count"] == 0)
        check(f"stl_degenerate_{rel}", row["degenerate_triangle_count"] == 0)
        check(f"stl_components_{rel}", row["component_count"] == 1)
        check(f"stl_reload_{rel}", row["reload"] == "PASS")

    for name, value in report["checks"].items():
        check(f"validation_not_fail_{name}", value != "FAIL")
    check("shell_print_gate", report["print_gate"]["shell"] == "APPROVED_X1")
    check("carrier_print_gate", report["print_gate"]["carrier"] == "APPROVED_X1")
    check("lid_gate", report["print_gate"]["lid"] == "HOLD")
    check("water_not_yet", report["checks"]["water"] == "NOT_YET")
    check("powered_not_yet", report["checks"]["dual_driver_powered"] == "NOT_YET")
    check("field_not_yet", report["checks"]["field"] == "NOT_YET")

    readme = (LANE / "docs/README.md").read_text(encoding="utf-8")
    print_gate = (LANE / "docs/PRINT_GATE.md").read_text(encoding="utf-8")
    authority = (LANE / "docs/DESIGN_AUTHORITY.md").read_text(encoding="utf-8")
    check("readme_shell", "cbox_shell_v0_9_6_32.stl" in readme)
    check("readme_carrier", "electronics_carrier_v0_9_6_32.stl" in readme)
    check("print_shell", "SHELL_SINGLE_PRINT_APPROVED" in print_gate)
    check("print_lid_hold", "PRINT_HOLD" in print_gate)
    check("authority_z_hold", "CBOX_Z_PLACEMENT" in authority and "HOLD" in authority)

    if failed:
        raise AssertionError(json.dumps({"failed": failed, "passed": len(passed)}, ensure_ascii=False, indent=2))
    print(json.dumps({"tests": len(passed), "passed": len(passed), "failed": 0, "status": "PASS"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
