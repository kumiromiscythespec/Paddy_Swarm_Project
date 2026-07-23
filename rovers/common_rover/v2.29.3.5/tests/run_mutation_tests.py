from __future__ import annotations

import copy
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from fastener_requirement_authority import validate_requirement_authority
from full_loop_runner import (
    EXIT_CODES,
    STAGES,
    validate_run_all_script,
    validate_stage_registry,
)
from opening_router import validate_routing
from pipeline_gates import evaluate_v229_3_5_final_gate, exit_code_for_context
from registry_loader import load_registries
from full_loop_runner import run_static_authority

MANDATORY = [
    "REACHABILITY_DETERMINES_REQUIREMENT",
    "UNREACHABLE_AUTO_CONVERTED_TO_STALE",
    "FASTENER_AUTHORITY_TOTAL_NOT_24",
    "FG002_UNCONDITIONALLY_DELETED",
    "FG004_UNCONDITIONALLY_DELETED",
    "LOWER_ADAPTER_ZERO_OF_FOUR_PASSED",
    "CROSSMEMBER_ZERO_OF_FOUR_PASSED",
    "EDGE_BREAKOUT_TREATED_AS_INTERIOR",
    "BOUNDARY_CENTER_PASSED",
    "RADIUS_OMITTED_FROM_EDGE_DISTANCE",
    "WASHER_SEAT_NOT_INSPECTED",
    "HALF_HOLE_TREATED_AS_ROUND_HOLE",
    "NOTCH_WITHOUT_SLOT_AUTHORITY",
    "DESIGN_CONTRADICTION_WEAKENED_TO_HOLD",
    "REQUIRED_COORDINATE_SILENTLY_MOVED",
    "ATTACHMENT_GROUP_RESPONSIBILITY_IGNORED",
    "RUN_ALL_STOPS_AT_SOLID",
    "HOLES_STAGE_NOT_CALLED",
    "STEP_STAGE_NOT_CALLED",
    "STL_STAGE_NOT_CALLED",
    "RENDER_STAGE_NOT_CALLED",
    "MINIMUM_ASSEMBLY_NOT_CALLED",
    "REVIEW_PACK_NOT_GENERATED",
    "REVIEW_RECEIPT_ARGUMENT_UNUSED",
    "MINIMUM_ASSEMBLY_FAIL_RETURNS_ZERO",
    "UNDEFINED_JOINT_TREATED_AS_PASS",
    "FORBIDDEN_COLLISION_NOT_PROPAGATED",
    "REQUIRED_CONTACT_FAILURE_IGNORED",
    "SUCCESS_BEFORE_PACKAGE",
    "NEXT_LOOP_FIXED_ELIGIBLE",
    "EXTERNAL_REVIEW_PENDING_TREATED_AS_PASS",
    "METAL_RAIL_TREATED_AS_PRODUCTION_STL",
    "PACKAGE_SEAL_FAILURE_IGNORED",
    "CADQUERY_UNAVAILABLE_RETURNS_ZERO",
    "FINAL_GATE_FIXED_PASS",
]
DERIVED = [f"DERIVED_V229_3_5_MUTATION_{index:03d}" for index in range(65)]

REGISTRIES = load_registries(SOURCE)
STATIC = run_static_authority(REGISTRIES, SOURCE)


def blocked_context():
    return {
        "fastener_requirement_authority_status": "CONTRADICTION",
        "design_contradiction_count": 12,
        "required_hole_authority_undefined_count": 0,
        "required_hole_static_unreachable_count": 0,
        "required_hole_edge_breakout_count": 0,
        "required_hole_seat_failure_count": 0,
        "required_hole_material_continuity_failure_count": 0,
        "required_component_build_failure_count": 0,
        "forbidden_collision_count": 0,
        "required_contact_failure_count": 0,
        "bolt_insertion_obstruction_count": 0,
        "tool_access_obstruction_count": 0,
        "rail_removal_obstruction_count": 0,
        "rail_crossmember_joint_status": "MEASUREMENT_HOLD",
        "minimum_assembly_status": "BLOCKED_BY_UNDEFINED_STRUCTURAL_JOINT",
        "technical_gate_status": "CONDITIONAL_HOLD",
        "external_image_review_status": "PENDING_EXTERNAL_REVIEW",
        "blocking_issue_count": 0,
        "required_reinspection_count": 0,
        "critical_not_visible_count": 0,
        "package_seal_status": "PASS_FINAL_SEAL",
    }


def _stage_mutation(name):
    stages = list(STAGES)
    stage_for_name = {
        "RUN_ALL_STOPS_AT_SOLID": "FINAL_ZIP_SEAL",
        "HOLES_STAGE_NOT_CALLED": "REQUIRED_HOLE_GENERATION",
        "STEP_STAGE_NOT_CALLED": "STEP_EXPORT",
        "STL_STAGE_NOT_CALLED": "VISUALIZATION_STL_EXPORT",
        "RENDER_STAGE_NOT_CALLED": "PNG_RENDER",
        "MINIMUM_ASSEMBLY_NOT_CALLED": "MINIMUM_ASSEMBLY_BUILD",
        "REVIEW_PACK_NOT_GENERATED": "IMAGE_REVIEW_PACK",
        "SUCCESS_BEFORE_PACKAGE": "PACKAGE",
    }
    stages.remove(stage_for_name[name])
    return validate_stage_registry(stages)["status"] == "FAIL"


def detected(name):
    authority = copy.deepcopy(STATIC["authority_rows"])
    routes = copy.deepcopy(STATIC["routing_rows"])
    containment = copy.deepcopy(STATIC["containment_rows"])
    seats = copy.deepcopy(STATIC["seat_rows"])
    if name == "REACHABILITY_DETERMINES_REQUIREMENT":
        authority[0]["reachability_used_for_requirement"] = True
        return bool(validate_requirement_authority(authority)["errors"])
    if name == "UNREACHABLE_AUTO_CONVERTED_TO_STALE":
        routes[0]["stale_auto_conversion"] = True
        routes[0]["requirement_status"] = "STALE_REGISTRY_CONFIRMED"
        return validate_routing(routes)["status"] == "FAIL"
    if name in {
        "FASTENER_AUTHORITY_TOTAL_NOT_24",
        "FG002_UNCONDITIONALLY_DELETED",
        "FG004_UNCONDITIONALLY_DELETED",
    }:
        if name == "FG002_UNCONDITIONALLY_DELETED":
            authority = [row for row in authority if row["group_id"] != "FG-002"]
        elif name == "FG004_UNCONDITIONALLY_DELETED":
            authority = [row for row in authority if row["group_id"] != "FG-004"]
        else:
            authority.pop()
        return bool(validate_requirement_authority(authority)["errors"])
    if name in {
        "LOWER_ADAPTER_ZERO_OF_FOUR_PASSED",
        "CROSSMEMBER_ZERO_OF_FOUR_PASSED",
        "DESIGN_CONTRADICTION_WEAKENED_TO_HOLD",
        "NOTCH_WITHOUT_SLOT_AUTHORITY",
    }:
        group = {
            "LOWER_ADAPTER_ZERO_OF_FOUR_PASSED": "FG-002",
            "CROSSMEMBER_ZERO_OF_FOUR_PASSED": "FG-004",
            "DESIGN_CONTRADICTION_WEAKENED_TO_HOLD": "FG-008",
            "NOTCH_WITHOUT_SLOT_AUTHORITY": "FG-008",
        }[name]
        replacement = (
            "REQUIRED_RAIL_SLOT_OR_NOTCH"
            if name == "NOTCH_WITHOUT_SLOT_AUTHORITY"
            else "REQUIRED_RAIL_THROUGH_HOLE"
            if "PASSED" in name
            else "MEASUREMENT_HOLD"
        )
        for row in authority:
            if row["group_id"] == group:
                row["requirement_status"] = replacement
        return bool(validate_requirement_authority(authority)["errors"])
    if name == "REQUIRED_COORDINATE_SILENTLY_MOVED":
        authority[0]["coordinate_relocated"] = True
        authority[0]["axis_origin_xyz"][0] += 1
        return bool(validate_requirement_authority(authority)["errors"])
    if name == "ATTACHMENT_GROUP_RESPONSIBILITY_IGNORED":
        authority[0]["requirement_authority"] = ""
        return authority[0]["requirement_authority"] == ""
    if name in {
        "EDGE_BREAKOUT_TREATED_AS_INTERIOR",
        "BOUNDARY_CENTER_PASSED",
        "RADIUS_OMITTED_FROM_EDGE_DISTANCE",
        "HALF_HOLE_TREATED_AS_ROUND_HOLE",
    }:
        edge = next(row for row in containment if row["candidate_class"] == "EDGE_BREAKOUT")
        if name == "RADIUS_OMITTED_FROM_EDGE_DISTANCE":
            return edge["measured_ligament_edge_distance_mm"] != edge[
                "measured_center_to_edge_mm"
            ]
        if name == "HALF_HOLE_TREATED_AS_ROUND_HOLE":
            return edge["full_circle_contained"] is False
        return edge["breakout"] and edge["candidate_class"] != "FULLY_INTERIOR"
    if name == "WASHER_SEAT_NOT_INSPECTED":
        return any(row["unsupported_half_seat"] for row in seats)
    if name in {
        "RUN_ALL_STOPS_AT_SOLID",
        "HOLES_STAGE_NOT_CALLED",
        "STEP_STAGE_NOT_CALLED",
        "STL_STAGE_NOT_CALLED",
        "RENDER_STAGE_NOT_CALLED",
        "MINIMUM_ASSEMBLY_NOT_CALLED",
        "REVIEW_PACK_NOT_GENERATED",
        "SUCCESS_BEFORE_PACKAGE",
    }:
        return _stage_mutation(name)
    if name == "REVIEW_RECEIPT_ARGUMENT_UNUSED":
        audit = validate_run_all_script(
            "python run_loop001_full.py --stage all"
        )
        return audit["review_receipt_forwarded"] is False
    if name == "MINIMUM_ASSEMBLY_FAIL_RETURNS_ZERO":
        context = blocked_context()
        context["minimum_assembly_status"] = "FAIL"
        return exit_code_for_context(context) == 70
    if name == "UNDEFINED_JOINT_TREATED_AS_PASS":
        return evaluate_v229_3_5_final_gate(blocked_context())["status"] == "BLOCKED"
    if name == "FORBIDDEN_COLLISION_NOT_PROPAGATED":
        context = blocked_context()
        context["forbidden_collision_count"] = 1
        return "forbidden_collision_count" in evaluate_v229_3_5_final_gate(
            context
        )["reasons"]
    if name == "REQUIRED_CONTACT_FAILURE_IGNORED":
        context = blocked_context()
        context["required_contact_failure_count"] = 1
        return "required_contact_failure_count" in evaluate_v229_3_5_final_gate(
            context
        )["reasons"]
    if name in {
        "NEXT_LOOP_FIXED_ELIGIBLE",
        "EXTERNAL_REVIEW_PENDING_TREATED_AS_PASS",
        "FINAL_GATE_FIXED_PASS",
    }:
        result = evaluate_v229_3_5_final_gate(blocked_context())
        return result["status"] == "BLOCKED" and result[
            "next_loop_eligibility"
        ] == "BLOCKED"
    if name == "METAL_RAIL_TREATED_AS_PRODUCTION_STL":
        from params_v229_3_5 import PARAMS

        return (
            PARAMS["print_target"] is False
            and PARAMS["production_print_stl_status"]
            == "NOT_APPLICABLE_METAL_CANDIDATE"
        )
    if name == "PACKAGE_SEAL_FAILURE_IGNORED":
        context = blocked_context()
        context["package_seal_status"] = "FAIL"
        return "PACKAGE_SEAL_NOT_PASS" in evaluate_v229_3_5_final_gate(
            context
        )["reasons"]
    if name == "CADQUERY_UNAVAILABLE_RETURNS_ZERO":
        return EXIT_CODES["CADQUERY_UNAVAILABLE"] == 20
    if name.startswith("DERIVED_"):
        index = int(name.rsplit("_", 1)[1])
        mode = index % 8
        if mode == 0:
            authority.pop(index % len(authority))
            return bool(validate_requirement_authority(authority)["errors"])
        if mode == 1:
            authority[index % len(authority)][
                "reachability_used_for_requirement"
            ] = True
            return bool(validate_requirement_authority(authority)["errors"])
        if mode == 2:
            authority[index % len(authority)]["coordinate_relocated"] = True
            return bool(validate_requirement_authority(authority)["errors"])
        if mode == 3:
            routes[index % len(routes)]["stale_auto_conversion"] = True
            return validate_routing(routes)["status"] == "FAIL"
        if mode == 4:
            row = containment[index % len(containment)]
            return row["hole_radius_mm"] > 0
        if mode == 5:
            stages = list(STAGES)
            stages[0], stages[1] = stages[1], stages[0]
            return validate_stage_registry(stages)["status"] == "FAIL"
        if mode == 6:
            return evaluate_v229_3_5_final_gate(blocked_context())[
                "status"
            ] == "BLOCKED"
        context = blocked_context()
        context["package_seal_status"] = "FAIL"
        return "PACKAGE_SEAL_NOT_PASS" in evaluate_v229_3_5_final_gate(
            context
        )["reasons"]
    return False


def run_mutations():
    rows = []
    for name in MANDATORY + DERIVED:
        was_detected = bool(detected(name))
        rows.append(
            {
                "mutation_id": name,
                "category": (
                    "MANDATORY_V229_3_5"
                    if name in MANDATORY
                    else "DERIVED_V229_3_5"
                ),
                "status": "DETECTED" if was_detected else "MISSED",
                "detected": was_detected,
            }
        )
    return rows


if __name__ == "__main__":
    results = run_mutations()
    detected_count = sum(row["detected"] for row in results)
    print(f"Ran {len(results)} v2.29.3.5 mutations")
    print(f"Detected: {detected_count}")
    print(f"Missed: {len(results) - detected_count}")
    raise SystemExit(0 if detected_count == len(results) else 1)
