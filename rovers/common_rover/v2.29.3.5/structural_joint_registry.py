from __future__ import annotations
import json
from pathlib import Path

JOINT_TYPES = {
    "BUTT_FACE_CONTACT", "LAP_JOINT", "TAB_AND_SLOT",
    "TONGUE_AND_GROOVE", "BOLTED_ANGLE_BRACKET",
    "DOWEL_AND_BOLT", "WELDED_REFERENCE_ONLY",
    "UNDEFINED_MEASUREMENT_HOLD",
}

def load_structural_joint_registry(root=None):
    base = Path(root) if root else Path(__file__).resolve().parent
    rows = json.loads(
        (base / "structural_joint_registry.json").read_text(encoding="utf-8")
    )
    validate_joint_registry(rows)
    return rows

def validate_joint_registry(rows):
    errors = []
    identifiers = [row.get("joint_id") for row in rows]
    if len(identifiers) != len(set(identifiers)):
        errors.append("duplicate joint ID")
    required = {
        "joint_id", "component_a", "component_b", "joint_type",
        "expected_contact", "expected_overlap", "overlap_envelope",
        "fastener_groups", "locating_feature", "load_directions",
        "assembly_sequence", "removal_sequence", "geometry_authority",
        "measurement_status", "failure_consequence",
    }
    for row in rows:
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"{row.get('joint_id')}: missing {missing}")
        if row.get("joint_type") not in JOINT_TYPES:
            errors.append(f"{row.get('joint_id')}: invalid joint type")
        if not isinstance(row.get("overlap_envelope"), dict):
            errors.append(f"{row.get('joint_id')}: overlap envelope missing")
        if (
            row.get("joint_type") == "LAP_JOINT"
            and not isinstance(row.get("expected_overlap"), dict)
        ):
            errors.append(f"{row.get('joint_id')}: lap joint lacks overlap range")
        if (
            row.get("joint_type") == "UNDEFINED_MEASUREMENT_HOLD"
            and row.get("allows_overlap") is True
        ):
            errors.append(f"{row.get('joint_id')}: undefined joint allows overlap")
    return errors

def inspect_joint_policy(
    joint, actual_overlap_volume_mm3, actual_distance_mm,
    overlap_inside_envelope, contact_tolerance_mm=0.10,
):
    joint_type = joint["joint_type"]
    if joint_type == "UNDEFINED_MEASUREMENT_HOLD":
        return {
            "joint_id": joint["joint_id"], "status": "STRUCTURAL_JOINT_HOLD",
            "undefined_required_joint_count": 1,
            "unregistered_structural_overlap_count":
                int(actual_overlap_volume_mm3 > 0.001),
            "structural_overlap_outside_envelope_count": 0,
            "reason": "joint authority unresolved; overlap is not allowed",
        }
    if joint_type in {
        "BUTT_FACE_CONTACT", "BOLTED_ANGLE_BRACKET", "DOWEL_AND_BOLT",
    }:
        overlap_failure = actual_overlap_volume_mm3 > 0.001
        contact_failure = actual_distance_mm > float(contact_tolerance_mm)
        return {
            "joint_id": joint["joint_id"],
            "status": "FAIL" if overlap_failure or contact_failure else "PASS",
            "undefined_required_joint_count": 0,
            "unregistered_structural_overlap_count": int(overlap_failure),
            "structural_overlap_outside_envelope_count": 0,
            "required_contact_failure_count": int(contact_failure),
        }
    if joint_type == "LAP_JOINT":
        expected = joint.get("expected_overlap", {})
        minimum = expected.get("minimum_volume_mm3")
        maximum = expected.get("maximum_volume_mm3")
        authority_missing = minimum is None or maximum is None
        outside_volume = (
            authority_missing
            or not float(minimum) <= actual_overlap_volume_mm3 <= float(maximum)
        )
        outside_envelope = not overlap_inside_envelope
        return {
            "joint_id": joint["joint_id"],
            "status": "FAIL" if outside_volume or outside_envelope else "PASS",
            "undefined_required_joint_count": int(authority_missing),
            "unregistered_structural_overlap_count": int(outside_volume),
            "structural_overlap_outside_envelope_count":
                int(outside_envelope),
        }
    if joint_type == "TAB_AND_SLOT":
        return {
            "joint_id": joint["joint_id"],
            "status": "PASS" if overlap_inside_envelope else "FAIL",
            "undefined_required_joint_count": 0,
            "unregistered_structural_overlap_count": 0,
            "structural_overlap_outside_envelope_count":
                int(not overlap_inside_envelope),
        }
    return {
        "joint_id": joint["joint_id"], "status": "MEASUREMENT_HOLD",
        "undefined_required_joint_count": 1,
        "unregistered_structural_overlap_count": 0,
        "structural_overlap_outside_envelope_count": 0,
        "reason": f"{joint_type} inspection policy requires explicit authority",
    }
