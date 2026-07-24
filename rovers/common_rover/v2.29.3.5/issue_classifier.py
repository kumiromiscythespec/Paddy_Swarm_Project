from __future__ import annotations
from collections import Counter

HARD_CATEGORY_MAP = {
    "part_build_failure_count": "CODE_IMPLEMENTATION",
    "step_export_failure_count": "OPENCASCADE_OPERATION",
    "step_reimport_failure_count": "OPENCASCADE_OPERATION",
    "stl_export_failure_count": "CODE_IMPLEMENTATION",
    "stl_validation_failure_count": "CODE_IMPLEMENTATION",
    "bbox_hard_failure_count": "DIMENSION",
    "fixed_opening_failure_count": "DIMENSION",
    "fixed_hole_center_failure_count": "DIMENSION",
    "fixed_hole_diameter_failure_count": "DIMENSION",
    "renderer_failure_count": "CODE_IMPLEMENTATION",
    "invalid_png_count": "CODE_IMPLEMENTATION",
    "camera_authority_failure_count": "COORDINATE_SYSTEM",
    "image_duplicate_anomaly_count": "CODE_IMPLEMENTATION",
    "automated_image_qa_failure_count": "CODE_IMPLEMENTATION",
    "minimum_assembly_forbidden_collision_count": "PART_INTERFERENCE",
    "required_contact_failure_count": "ASSEMBLY",
    "service_sweep_obstruction_count": "ASSEMBLY",
    "confirmed_build_volume_failure_count": "PRINTABILITY",
    "unresolved_critical_issue_count": "DESIGN_CONTRADICTION",
}

def classify_gate_issues(loop_id, part_id, revision, hard_counts, hold_counts):
    issues = []
    for key, value in hard_counts.items():
        for occurrence in range(value):
            issues.append({
                "issue_id": f"ISSUE-HARD-{len(issues)+1:03d}", "loop_id": loop_id,
                "part_id": part_id, "revision": revision,
                "category": HARD_CATEGORY_MAP.get(key, "CODE_IMPLEMENTATION"),
                "detection_phase": key, "description": f"{key} active",
                "root_cause": "see inspection evidence", "affected_parts": [part_id],
                "affected_dimensions": [], "severity": "CRITICAL",
                "correction_method": "MINIMAL_CAUSE_LOCAL_CORRECTION_ONLY",
                "reinspection_scope": [key], "status": "OPEN",
            })
    for key, value in hold_counts.items():
        if not value:
            continue
        issues.append({
            "issue_id": f"HOLD-{len(issues)+1:03d}", "loop_id": loop_id,
            "part_id": part_id, "revision": revision,
            "category": "UNDEFINED_DIMENSION" if "tolerance" in key or "interface" in key else "STRUCTURAL_RISK",
            "detection_phase": key, "description": f"{key}: {value}",
            "root_cause": "measurement/analysis/external review pending",
            "affected_parts": [part_id], "affected_dimensions": [],
            "severity": "HOLD", "correction_method": "RESOLVE_AUTHORITY_OR_MEASUREMENT",
            "reinspection_scope": [key], "status": "OPEN",
        })
    return issues

def repeated_method_stop(attempts, method):
    failed = [row for row in attempts if row.get("method") == method and row.get("outcome") == "FAIL"]
    return {
        "stop": len(failed) >= 2, "failed_attempt_count": len(failed),
        "method": method,
        "action": "STOP_AND_RETURN_TO_PRIMITIVE_BASE" if len(failed) >= 2 else "MAY_ATTEMPT_MINIMAL_CORRECTION",
    }
