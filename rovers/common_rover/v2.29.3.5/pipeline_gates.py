from __future__ import annotations

HARD_FAILURE_KEYS = (
    "unrouted_opening_count", "double_routed_opening_count",
    "keepout_subtracted_as_hole_count",
    "required_fastener_hole_static_unreachable_count",
    "failed_required_rail_hole_count",
    "cutter_did_not_reach_required_host_count",
    "invalid_rail_after_cut_count",
    "minimum_assembly_required_component_build_failure_count",
    "undefined_required_joint_count",
    "unregistered_structural_overlap_count",
    "structural_overlap_outside_envelope_count",
    "forbidden_collision_failure_count",
    "required_contact_failure_count",
    "bolt_insertion_obstruction_count",
    "tool_access_obstruction_count",
    "rail_removal_obstruction_count",
    "invalid_review_receipt_count",
    "next_loop_gate_violation_count",
    "package_internal_hash_missing_count",
    "final_zip_seal_failure_count",
)
HOLD_KEYS = (
    "stale_or_wrong_host_review_count",
    "coordinate_space_review_count",
    "joint_measurement_hold_count",
    "visualization_stl_hold_count",
    "image_external_review_pending_count",
    "critical_not_visible_count",
    "required_reinspection_count",
    "shared_flange_spacing_hold_count",
    "lower_interface_hold_count",
)
OPENING_FAILURE_STATUSES = {
    "CUTTER_DID_NOT_REACH_HOST", "HOST_NOT_FOUND", "INVALID_CUTTER",
    "CUT_FAILED", "FINAL_HOLE_NOT_DETECTED", "WRONG_HOST",
    "DUPLICATE_CUT", "REQUIRED_OPENING_NOT_EXECUTED",
}
EXIT_CODES = {
    "PASS": 0, "PREFLIGHT_FAILURE": 10, "CADQUERY_UNAVAILABLE": 20,
    "ROUTING_FAILURE": 30, "REQUIRED_HOLE_FAILURE": 40,
    "STRUCTURAL_JOINT_OR_ASSEMBLY_FAILURE": 50,
    "IMAGE_REVIEW_FAILURE": 60, "PACKAGE_SEAL_FAILURE": 70,
}

def _validate_counts(counts, required):
    missing = [key for key in required if key not in counts]
    invalid = [
        key for key in required
        if key in counts and (
            not isinstance(counts[key], int) or counts[key] < 0
        )
    ]
    if missing or invalid:
        raise ValueError({"missing": missing, "invalid": invalid})

def evaluate_static_preflight(hard_counts, hold_counts):
    _validate_counts(hard_counts, HARD_FAILURE_KEYS)
    _validate_counts(hold_counts, HOLD_KEYS)
    active_hard = {
        key: hard_counts[key] for key in HARD_FAILURE_KEYS
        if hard_counts[key] > 0
    }
    active_holds = {
        key: hold_counts[key] for key in HOLD_KEYS
        if hold_counts[key] > 0
    }
    static_hard_keys = {
        "unrouted_opening_count", "double_routed_opening_count",
        "keepout_subtracted_as_hole_count",
        "required_fastener_hole_static_unreachable_count",
        "package_internal_hash_missing_count",
        "final_zip_seal_failure_count",
    }
    static_hard = {
        key: value for key, value in active_hard.items()
        if key in static_hard_keys
    }
    return {
        "status": "FAIL" if static_hard else "PASS_WITH_HOLD"
            if active_holds else "PASS",
        "active_static_hard_failures": static_hard,
        "active_holds": active_holds,
        "all_hard_counts": dict(hard_counts),
        "all_hold_counts": dict(hold_counts),
    }

def aggregate_opening_failures(rows):
    failures = [
        row for row in rows
        if row.get("status") in OPENING_FAILURE_STATUSES
        and (
            row.get("required") is True
            or not row.get("pre_registered_measurement_hold")
        )
    ]
    return {
        "failed_required_rail_hole_count": len(failures),
        "cutter_did_not_reach_required_host_count": sum(
            row.get("status") == "CUTTER_DID_NOT_REACH_HOST"
            for row in failures
        ),
        "failure_rows": failures,
    }

def determine_loop_status(
    cadquery_available, hard_counts, joint_status,
    technical_gate_status, review_status, minimum_assembly_status,
):
    if not cadquery_available:
        return "SOURCE_REPAIRED_AWAITING_CADQUERY_EXECUTION"
    if any(hard_counts.values()):
        return "FAIL"
    if joint_status == "MEASUREMENT_HOLD":
        return "BLOCKED_BY_UNDEFINED_DIMENSION"
    if technical_gate_status != "PASS":
        return "FAIL"
    if review_status in {
        "PENDING_EXTERNAL_REVIEW", "CONDITIONAL_EXTERNAL_RECEIPT",
    }:
        return "CONDITIONAL_PASS"
    if (
        review_status == "PASS_EXTERNAL_RECEIPT"
        and minimum_assembly_status == "PASS"
    ):
        return "PASS"
    return "FAIL"


V229_3_5_FINAL_HARD_KEYS = (
    "required_hole_authority_undefined_count",
    "required_hole_static_unreachable_count",
    "required_hole_edge_breakout_count",
    "required_hole_seat_failure_count",
    "required_hole_material_continuity_failure_count",
    "required_component_build_failure_count",
    "forbidden_collision_count",
    "required_contact_failure_count",
    "bolt_insertion_obstruction_count",
    "tool_access_obstruction_count",
    "rail_removal_obstruction_count",
)


def evaluate_v229_3_5_final_gate(context):
    """Aggregate technical, assembly, review, and package state once."""
    hard_failures = {
        key: int(context.get(key, 0) or 0)
        for key in V229_3_5_FINAL_HARD_KEYS
    }
    reasons = [key for key, value in hard_failures.items() if value]
    if context.get("fastener_requirement_authority_status") not in {
        "PASS",
        "CONTRADICTION",
    }:
        reasons.append("FASTENER_REQUIREMENT_AUTHORITY_INCOMPLETE")
    if int(context.get("design_contradiction_count", 0) or 0):
        reasons.append("FASTENER_AUTHORITY_DESIGN_CONTRADICTION")
    if context.get("rail_crossmember_joint_status") != "DEFINED":
        reasons.append("RAIL_CROSSMEMBER_JOINT_UNDEFINED")
    if context.get("minimum_assembly_status") != "PASS":
        reasons.append("MINIMUM_ASSEMBLY_NOT_PASS")
    if context.get("technical_gate_status") != "PASS":
        reasons.append("TECHNICAL_GATE_NOT_PASS")
    if context.get("external_image_review_status") != "PASS":
        reasons.append("EXTERNAL_IMAGE_REVIEW_NOT_PASS")
    if int(context.get("blocking_issue_count", 0) or 0):
        reasons.append("BLOCKING_IMAGE_REVIEW_ISSUES")
    if int(context.get("required_reinspection_count", 0) or 0):
        reasons.append("IMAGE_REINSPECTION_REQUIRED")
    if int(context.get("critical_not_visible_count", 0) or 0):
        reasons.append("CRITICAL_FEATURE_NOT_VISIBLE")
    if context.get("package_seal_status") != "PASS_FINAL_SEAL":
        reasons.append("PACKAGE_SEAL_NOT_PASS")
    eligible = not reasons
    return {
        "status": "PASS" if eligible else "BLOCKED",
        "next_loop_eligibility": (
            "ELIGIBLE_FOR_LOOP_002" if eligible else "BLOCKED"
        ),
        "hard_failure_counts": hard_failures,
        "reasons": reasons,
    }


def exit_code_for_context(context):
    if context.get("preflight_status") == "FAIL":
        return 10
    if context.get("cadquery_import_status") == "UNAVAILABLE":
        return 20
    if context.get("rail_solid_status") == "FAIL":
        return 30
    if context.get("required_hole_gate_status") == "FAIL":
        return 40
    if context.get("export_gate_status") == "FAIL":
        return 50
    if context.get("render_gate_status") == "FAIL":
        return 60
    if context.get("minimum_assembly_status") == "FAIL":
        return 70
    if context.get("minimum_assembly_status") in {
        "BLOCKED_BY_UNDEFINED_STRUCTURAL_JOINT",
        "BLOCKED_BY_UNDEFINED_DIMENSION",
    }:
        return 71
    if context.get("receipt_status") == "INVALID":
        return 80
    if context.get("final_loop_gate_status") == "FAIL":
        return 90
    if context.get("package_seal_status") == "FAIL":
        return 100
    return 0
