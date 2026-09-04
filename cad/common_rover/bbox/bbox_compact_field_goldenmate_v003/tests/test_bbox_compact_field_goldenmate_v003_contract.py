"""Executable contract for Compact Field BBOX V003."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


LANE = Path(__file__).resolve().parents[1]
BUILDER = LANE / "build_bbox_compact_field_goldenmate_v003.py"
spec = importlib.util.spec_from_file_location("bbox_v003", BUILDER)
assert spec and spec.loader
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def check(name: str, value: bool, results: dict[str, bool]):
    results[name] = bool(value)


def main() -> int:
    results: dict[str, bool] = {}
    verify = b.verify()
    params = json.loads((LANE / "design_parameters.json").read_text(encoding="utf-8"))
    validation = json.loads((LANE / "validation_report.json").read_text(encoding="utf-8"))
    manifest = json.loads((LANE / "manifest.json").read_text(encoding="utf-8"))
    contract = json.loads((LANE / "contract_test_report.json").read_text(encoding="utf-8"))

    check("builder_verify", verify["pass"], results)
    check("exact_path_count", verify["exact_paths"] == len(b.EXPECTED) == manifest["exact_path_count"], results)
    check("manifest_exact", manifest["paths"] == b.EXPECTED, results)
    check("correct_battery_plan", params["battery_authority"]["long_mm"] == 150.9 and params["battery_authority"]["width_mm"] == 65.5, results)
    check("correct_heights", params["battery_authority"]["body_height_mm"] == 92.5 and params["battery_authority"]["terminal_inclusive_height_mm"] == 99.4, results)
    check("old_axis_forbidden", params["old_99p4_as_plan_width"] is False, results)
    check("selected_B", params["selected"] == "COMPACT_B", results)
    check("internal_155_69_110", params["selected_dimensions"]["internal"] == [155.0, 69.0, 110.0], results)
    check("wall_floor", params["wall_selected_mm"] == 3.5 and params["floor_selected_mm"] == 3.5, results)
    check("clearances", validation["metrics"]["x_total_clearance_mm"] == 4.1 and validation["metrics"]["y_total_clearance_mm"] == 3.5, results)
    check("terminal_clearance", validation["metrics"]["terminal_to_rim_mm"] == 9.6 and validation["metrics"]["terminal_to_lid_inner_mm"] == 10.495, results)
    check("battery_shell_zero", validation["metrics"]["battery_shell_intersection_mm3"] == 0, results)
    check("vertical_removal_zero", validation["metrics"]["battery_removal_sweep_fixed_intersection_mm3"] == 0, results)
    check("lid_contact_zero", validation["metrics"]["battery_lid_contact_mm3"] == 0, results)
    check("lid_not_restraint", validation["checks"]["lid_not_restraint"], results)
    check("support_A", params["support_selected"].startswith("A_BODY_FLOOR"), results)
    check("strap_20", params["strap_selected_mm"] == 20.0 and params["strap_physical_fit"] == "PENDING", results)
    check("tpu_1_nonstructural", params["tpu_selected_mm"] == 1.0 and params["tpu_role"].startswith("NONSTRUCTURAL"), results)
    check("seal_inherited_principle", params["seal"]["source"] == "V002_REUSED_DESIGN_PRINCIPLE" and not params["seal"]["exact_v002_perimeter_reused"], results)
    check("seal_contract", params["seal"]["cord_mm"] == 1.8 and params["seal"]["path_continuous"] and params["seal"]["external_vertical_m4_count"] == 8, results)
    check("hardstop", params["seal"]["hardstop_gap_mm"] == 0.895, results)
    check("chimney_exact_local", params["chimney"]["local_wall_mm"] == 2.4 and params["chimney"]["pg9_hole_mm"] == 15.2, results)
    check("chimney_opposite_terminal", params["chimney"]["selected"] == "A_SELECTED_OPPOSITE_TERMINALS", results)
    check("cable_9p6", params["main_cable_od_mm"] == 9.6, results)
    check("temporary_source_unresolved", params["temporary_cad_source_audit"]["result"] == "UNRESOLVED", results)
    check("service_zone", params["service_reserved_volume_mm3"] == 6000.0, results)
    check("global_pending", params["global_vehicle_transform"] == "PHYSICAL_PENDING", results)
    check("front_reference_only", params["front_interface"].startswith("REFERENCE_ONLY"), results)
    check("no_body_lid_stl", not (LANE / "artifacts/compact_field_bbox_body_selected.stl").exists() and not (LANE / "artifacts/compact_field_bbox_lid_selected.stl").exists(), results)
    check("coupon_stls", all((LANE / p).exists() for p in b.STLS[1:]), results)
    check("step_reload_all", verify["step_reload_pass"] == verify["step_count"] == 15, results)
    check("stl_quality_all", verify["stl_quality_pass"] == verify["stl_count"] == 3, results)
    check("step_semantic_repro", verify["step_semantic_reproducibility"], results)
    check("byte_repro", verify["byte_reproducibility"], results)
    check("hash_index", verify["sha256sums"], results)
    check("protected_unchanged", verify["protected_unchanged"], results)
    check("contract_report", contract["result"] == "PASS", results)
    check("validation_report", validation["result"] == "PASS", results)
    check("full_print_hold", params["full_box_print"] == "HOLD_UNTIL_SEAL_COUPON_PHYSICAL_PASS", results)
    check("waterproof_pending", params["waterproof"] == "PHYSICAL_PENDING", results)
    check("status", params["status"] == b.STATUS, results)

    passed = sum(results.values())
    print(json.dumps({"result": "PASS" if passed == len(results) else "FAIL", "passed": passed, "total": len(results), "checks": results}, indent=2))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
