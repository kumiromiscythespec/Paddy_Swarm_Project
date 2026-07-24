from __future__ import annotations
import math
from cad_primitives import safe_boolean, shape_bbox, shape_value, shape_volume
from structural_joint_registry import inspect_joint_policy

def _bbox_distance(left, right):
    a = shape_bbox(left); b = shape_bbox(right)
    gaps = [
        max(0.0, a["xmin"] - b["xmax"], b["xmin"] - a["xmax"]),
        max(0.0, a["ymin"] - b["ymax"], b["ymin"] - a["ymax"]),
        max(0.0, a["zmin"] - b["zmax"], b["zmin"] - a["zmax"]),
    ]
    return math.sqrt(sum(value * value for value in gaps))

def _shape_distance(left, right):
    first = shape_value(left); second = shape_value(right)
    try:
        return float(first.distance(second)), "ACTUAL_SHAPE_DISTANCE", True
    except Exception:
        try:
            return (
                float(first.distToShape(second)[0]),
                "ACTUAL_SHAPE_DIST_TO_SHAPE", True,
            )
        except Exception:
            return _bbox_distance(left, right), "BBOX_DISTANCE_PROXY", False

def inspect_minimum_assembly(
    assembly, manifest, joints, contact_tolerance_mm=0.10,
    boolean_tolerance_mm3=0.001,
):
    build_failures = assembly.get(
        "required_component_build_failure_count", 0
    )
    if build_failures or not assembly.get("complete"):
        return {
            "status": "FAIL_INCOMPLETE_REQUIRED_ASSEMBLY",
            "required_component_build_failure_count": max(build_failures, 1),
            "collision_inspection_executed": False,
            "forbidden_collision_failure_count": None,
            "required_contact_failure_count": None,
            "undefined_required_joint_count": None,
            "unregistered_structural_overlap_count": None,
            "structural_overlap_outside_envelope_count": None,
            "rows": [],
            "reason": "missing required components; collision-zero PASS forbidden",
        }
    solids = assembly["solids"]
    joint_pairs = {
        frozenset((joint["component_a"], joint["component_b"])): joint
        for joint in joints
    }
    rows = []
    undefined = unregistered = outside = contact_failures = forbidden = 0
    part_ids = sorted(solids)
    for index, left_id in enumerate(part_ids):
        for right_id in part_ids[index + 1:]:
            left = solids[left_id]; right = solids[right_id]
            common = safe_boolean(
                left, right, "intersect",
                f"minimum-assembly:{left_id}:{right_id}",
            )
            overlap = shape_volume(common)
            distance, distance_method, pass_eligible = _shape_distance(left, right)
            joint = joint_pairs.get(frozenset((left_id, right_id)))
            if joint:
                policy = inspect_joint_policy(
                    joint, overlap, distance, False,
                    contact_tolerance_mm,
                )
                undefined += policy.get("undefined_required_joint_count", 0)
                unregistered += policy.get(
                    "unregistered_structural_overlap_count", 0
                )
                outside += policy.get(
                    "structural_overlap_outside_envelope_count", 0
                )
                contact_failures += policy.get(
                    "required_contact_failure_count", 0
                )
                classification = "REGISTERED_STRUCTURAL_JOINT"
                status = policy["status"]
            else:
                collision = overlap > float(boolean_tolerance_mm3)
                forbidden += int(collision)
                classification = "FORBIDDEN_UNREGISTERED_PAIR"
                status = "FAIL_FORBIDDEN_COLLISION" if collision else "PASS"
            if not pass_eligible and status == "PASS":
                status = "CONDITIONAL_HOLD_DISTANCE_PROXY"
            rows.append({
                "component_a": left_id, "component_b": right_id,
                "intersection_volume_mm3": overlap,
                "distance_mm": distance,
                "distance_method": distance_method,
                "actual_distance_pass_eligible": pass_eligible,
                "classification": classification, "status": status,
            })
    if undefined:
        status = "BLOCKED_BY_UNDEFINED_STRUCTURAL_JOINT"
    elif forbidden or unregistered or outside or contact_failures:
        status = "FAIL"
    else:
        status = "PASS"
    return {
        "status": status,
        "required_component_build_failure_count": 0,
        "collision_inspection_executed": True,
        "forbidden_collision_failure_count": forbidden,
        "required_contact_failure_count": contact_failures,
        "undefined_required_joint_count": undefined,
        "unregistered_structural_overlap_count": unregistered,
        "structural_overlap_outside_envelope_count": outside,
        "rows": rows,
    }

def validate_minimum_assembly_claim(record):
    errors = []
    if record.get("status") == "PASS":
        if record.get("required_component_build_failure_count"):
            errors.append("PASS with required build failure")
        if not record.get("collision_inspection_executed"):
            errors.append("PASS without collision inspection")
        if not record.get("rows"):
            errors.append("empty/dictionary-only assembly cannot PASS")
        for key in (
            "forbidden_collision_failure_count",
            "required_contact_failure_count",
            "undefined_required_joint_count",
            "unregistered_structural_overlap_count",
            "structural_overlap_outside_envelope_count",
        ):
            if record.get(key):
                errors.append(f"PASS with {key}")
    return errors
