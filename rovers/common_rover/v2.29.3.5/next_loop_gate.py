from __future__ import annotations

def evaluate_next_loop_eligibility(
    receipt_validation, technical_gate_status,
    minimum_assembly_status, loop_001_status,
    unresolved_critical_issue_count=0,
):
    checks = {
        "receipt_validator_pass": receipt_validation.get("status") == "PASS",
        "receipt_decision_is_unconditional_pass":
            receipt_validation.get("overall_decision") == "PASS",
        "blocking_issue_count_zero":
            receipt_validation.get("blocking_issue_count") == 0,
        "required_reinspection_count_zero":
            receipt_validation.get("required_reinspection_count") == 0,
        "critical_not_visible_count_zero":
            receipt_validation.get("critical_not_visible_count") == 0,
        "reviewed_image_set_complete":
            receipt_validation.get("reviewed_image_set_complete") is True,
        "image_hashes_match":
            receipt_validation.get("image_hashes_match") is True,
        "source_fingerprint_match":
            receipt_validation.get("source_fingerprint_match") is True,
        "active_revision_match":
            receipt_validation.get("active_revision_match") is True,
        "technical_gate_pass": technical_gate_status == "PASS",
        "minimum_assembly_pass": minimum_assembly_status == "PASS",
        "loop_001_pass": loop_001_status == "PASS",
        "unresolved_critical_issue_count_zero":
            unresolved_critical_issue_count == 0,
    }
    eligible = all(checks.values())
    return {
        "next_loop_eligibility":
            "ELIGIBLE_FOR_LOOP_002" if eligible else "BLOCKED",
        "checks": checks,
        "failed_checks": [
            name for name, passed in checks.items() if not passed
        ],
        "conditional_receipt_can_unlock_next_loop": False,
    }

def validate_no_fixed_eligibility(record):
    if record.get("next_loop_eligibility") == "ELIGIBLE_FOR_LOOP_002":
        return [
            name for name, passed in record.get("checks", {}).items()
            if not passed
        ]
    return []
