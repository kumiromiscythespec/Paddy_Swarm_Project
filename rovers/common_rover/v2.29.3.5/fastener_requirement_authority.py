from __future__ import annotations

from collections import Counter

ACTIVE_PART_ID = "V2292-FPB-RAIL-L"

REQUIREMENT_STATUSES = {
    "REQUIRED_RAIL_THROUGH_HOLE",
    "REQUIRED_RAIL_BLIND_OR_TAPPED_HOLE",
    "REQUIRED_RAIL_SLOT_OR_NOTCH",
    "REQUIRED_EXTERNAL_CLAMP_NO_RAIL_HOLE",
    "REQUIRED_BRACKET_HOLE_NOT_RAIL",
    "REFERENCE_ONLY",
    "STALE_REGISTRY_CONFIRMED",
    "MEASUREMENT_HOLD",
    "DESIGN_CONTRADICTION",
}

# Authority is deliberately group-level and is evaluated before any geometric
# reachability result. Unknown geometry is retained as a hold or contradiction.
GROUP_AUTHORITY = {
    "FG-002": {
        "requirement_status": "MEASUREMENT_HOLD",
        "group_status": "DESIGN_CONTRADICTION_OR_MEASUREMENT_HOLD",
        "authority": (
            "ATT-002 + JOINT-LOOP001-RAIL-LOWER-ADAPTER; DOWEL_AND_BOLT "
            "load path exists, but no authoritative rail-side hole pattern"
        ),
        "reason": (
            "All four registered axes are outside the rail section. Direct "
            "rail drilling, external clamp, or intermediate bracket is unresolved."
        ),
        "rail_hole_required": None,
        "mating_part_hole_required": None,
        "bracket_hole_required": None,
        "measurement_hold": True,
    },
    "FG-004": {
        "requirement_status": "MEASUREMENT_HOLD",
        "group_status": "JOINT_TYPE_UNDEFINED",
        "authority": (
            "ATT-004 + JOINT-LOOP001-RAIL-FRONT-XMEMBER "
            "UNDEFINED_MEASUREMENT_HOLD"
        ),
        "reason": (
            "Butt/lap/tab/welded/angle-bracket construction is not defined; "
            "the fastener method cannot be separated from the joint authority."
        ),
        "rail_hole_required": None,
        "mating_part_hole_required": None,
        "bracket_hole_required": None,
        "measurement_hold": True,
    },
    "FG-006": {
        "requirement_status": "REQUIRED_RAIL_THROUGH_HOLE",
        "group_status": "RAIL_HOLE_PATTERN_VALID",
        "authority": (
            "ATT-006 BOLTED_BRACKET + JOINT-LOOP001-RAIL-MOTOR-BRACKET; "
            "rail is parent and carries the registered through-hole pattern"
        ),
        "reason": (
            "Four M4-class axes are explicit rail-parent attachment axes. "
            "Geometry checks follow but do not create the requirement."
        ),
        "rail_hole_required": True,
        "mating_part_hole_required": True,
        "bracket_hole_required": True,
        "measurement_hold": False,
    },
    "FG-008": {
        "requirement_status": "DESIGN_CONTRADICTION",
        "group_status": "HOLE_PATTERN_DESIGN_CONTRADICTION",
        "authority": "ATT-008 SLOT_AND_BOLT structural attachment",
        "reason": (
            "Two axes break out at X=73 and two are exterior at X=97; no "
            "slot width/depth, retention, or assembly-direction authority exists."
        ),
        "rail_hole_required": None,
        "mating_part_hole_required": True,
        "bracket_hole_required": None,
        "measurement_hold": True,
    },
    "FG-009": {
        "requirement_status": "DESIGN_CONTRADICTION",
        "group_status": "HOLE_PATTERN_DESIGN_CONTRADICTION",
        "authority": "ATT-009 BOLTED_FLANGE structural attachment",
        "reason": (
            "One boundary axis and three exterior axes cannot establish a "
            "four-fastener rail-side load path; no alternate bracket is registered."
        ),
        "rail_hole_required": None,
        "mating_part_hole_required": True,
        "bracket_hole_required": None,
        "measurement_hold": True,
    },
    "FG-020": {
        "requirement_status": "DESIGN_CONTRADICTION",
        "group_status": "HOLE_PATTERN_DESIGN_CONTRADICTION",
        "authority": "ATT-020 BOLTED_FLANGE structural attachment",
        "reason": (
            "Two boundary axes and two Z=24 exterior axes are registered to "
            "rail-L. A left/right rail responsibility split is not authoritative."
        ),
        "rail_hole_required": None,
        "mating_part_hole_required": True,
        "bracket_hole_required": None,
        "measurement_hold": True,
    },
}


def _active_instances(registries):
    return sorted(
        (
            row
            for row in registries["fasteners"]["instances"]
            if ACTIVE_PART_ID in {
                row["parent_component"],
                row["child_component"],
            }
        ),
        key=lambda row: row["fastener_instance_id"],
    )


def _opening_by_center(registries):
    result = {}
    for opening in registries["openings"]:
        if (
            opening.get("host_component") == ACTIVE_PART_ID
            and opening.get("type") == "FASTENER_ACCESS_OPENING"
        ):
            center = tuple(float(value) for value in opening["center_xyz"])
            result.setdefault(center, []).append(opening["opening_id"])
    return result


def classify_fastener_requirements(registries):
    """Classify all rail-referencing instances without using reachability."""
    openings = _opening_by_center(registries)
    rows = []
    for instance in _active_instances(registries):
        group_id = instance["fastener_group_id"]
        policy = GROUP_AUTHORITY.get(group_id)
        if policy is None:
            policy = {
                "requirement_status": "MEASUREMENT_HOLD",
                "group_status": "MEASUREMENT_REQUIRED",
                "authority": "NO_GROUP_AUTHORITY_REGISTERED",
                "reason": "Rail responsibility requires explicit engineering authority.",
                "rail_hole_required": None,
                "mating_part_hole_required": None,
                "bracket_hole_required": None,
                "measurement_hold": True,
            }
        center = [float(value) for value in instance["axis_origin_xyz"]]
        matches = openings.get(tuple(center), [])
        rail_is_parent = instance["parent_component"] == ACTIVE_PART_ID
        mating = (
            instance["child_component"]
            if rail_is_parent
            else instance["parent_component"]
        )
        rows.append(
            {
                "instance_id": instance["fastener_instance_id"],
                "group_id": group_id,
                "rail_referenced": True,
                "rail_role": "PARENT" if rail_is_parent else "CHILD",
                "mating_component": mating,
                "requirement_status": policy["requirement_status"],
                "requirement_authority": policy["authority"],
                "rail_hole_required": policy["rail_hole_required"],
                "mating_part_hole_required": policy["mating_part_hole_required"],
                "bracket_hole_required": policy["bracket_hole_required"],
                "clamp_or_external_fastener": (
                    policy["requirement_status"]
                    == "REQUIRED_EXTERNAL_CLAMP_NO_RAIL_HOLE"
                ),
                "nonpenetrating_attachment": (
                    policy["requirement_status"]
                    in {
                        "REQUIRED_EXTERNAL_CLAMP_NO_RAIL_HOLE",
                        "REQUIRED_BRACKET_HOLE_NOT_RAIL",
                    }
                ),
                "measurement_hold": policy["measurement_hold"],
                "contradiction_status": (
                    "DESIGN_CONTRADICTION"
                    if policy["requirement_status"] == "DESIGN_CONTRADICTION"
                    else (
                        "MEASUREMENT_HOLD"
                        if policy["requirement_status"] == "MEASUREMENT_HOLD"
                        else "NONE"
                    )
                ),
                "contradiction_reason": policy["reason"],
                "group_status": policy["group_status"],
                "opening_id": matches[0] if len(matches) == 1 else None,
                "opening_match_count": len(matches),
                "axis_origin_xyz": center,
                "axis_direction_xyz": [
                    float(value) for value in instance["axis_direction_xyz"]
                ],
                "diameter_class": instance.get("diameter_class"),
                "clearance_hole_candidate_mm": float(
                    instance["clearance_hole_candidate_mm"]
                ),
                "classification_order": (
                    "AUTHORITY_BEFORE_REACHABILITY_AND_GEOMETRY"
                ),
                "reachability_used_for_requirement": False,
                "coordinate_relocated": False,
            }
        )
    return rows


def summarize_requirement_authority(rows):
    counts = Counter(row["requirement_status"] for row in rows)
    return {
        "total_rail_referencing_instances": len(rows),
        "required_rail_through_hole_count": counts[
            "REQUIRED_RAIL_THROUGH_HOLE"
        ],
        "required_rail_slot_or_notch_count": counts[
            "REQUIRED_RAIL_SLOT_OR_NOTCH"
        ],
        "external_clamp_no_rail_hole_count": counts[
            "REQUIRED_EXTERNAL_CLAMP_NO_RAIL_HOLE"
        ],
        "bracket_hole_not_rail_count": counts[
            "REQUIRED_BRACKET_HOLE_NOT_RAIL"
        ],
        "stale_registry_confirmed_count": counts["STALE_REGISTRY_CONFIRMED"],
        "measurement_hold_count": counts["MEASUREMENT_HOLD"],
        "design_contradiction_count": counts["DESIGN_CONTRADICTION"],
    }


def validate_requirement_authority(rows, expected_total=24):
    summary = summarize_requirement_authority(rows)
    accounting = (
        summary["required_rail_through_hole_count"]
        + summary["required_rail_slot_or_notch_count"]
        + summary["external_clamp_no_rail_hole_count"]
        + summary["bracket_hole_not_rail_count"]
        + summary["stale_registry_confirmed_count"]
        + summary["measurement_hold_count"]
        + summary["design_contradiction_count"]
    )
    errors = []
    if len(rows) != expected_total or accounting != expected_total:
        errors.append("FASTENER_AUTHORITY_ACCOUNTING_MISMATCH")
    if len({row["instance_id"] for row in rows}) != len(rows):
        errors.append("DUPLICATE_FASTENER_INSTANCE")
    if any(row["requirement_status"] not in REQUIREMENT_STATUSES for row in rows):
        errors.append("UNKNOWN_REQUIREMENT_STATUS")
    if any(row["reachability_used_for_requirement"] for row in rows):
        errors.append("REQUIREMENT_REACHABILITY_CYCLE")
    if any(row["coordinate_relocated"] for row in rows):
        errors.append("UNAUTHORIZED_COORDINATE_RELOCATION")
    if any(
        row["requirement_status"] == "STALE_REGISTRY_CONFIRMED"
        and not row["requirement_authority"].startswith("CONFIRMED_STALE")
        for row in rows
    ):
        errors.append("UNREACHABLE_AUTO_CONVERTED_TO_STALE")
    if any(
        row["group_id"] in GROUP_AUTHORITY
        and row["requirement_status"]
        != GROUP_AUTHORITY[row["group_id"]]["requirement_status"]
        for row in rows
    ):
        errors.append("GROUP_AUTHORITY_CLASSIFICATION_CHANGED")
    status = (
        "PASS"
        if not errors
        and not summary["measurement_hold_count"]
        and not summary["design_contradiction_count"]
        else "CONTRADICTION"
        if not errors and summary["design_contradiction_count"]
        else "INCOMPLETE"
        if not errors
        else "FAIL"
    )
    return {
        **summary,
        "authority_accounting_total": accounting,
        "authority_accounting_result": (
            "PASS_24_OF_24" if accounting == expected_total else "FAIL"
        ),
        "required_hole_authority_undefined_count": sum(
            row["requirement_status"] not in REQUIREMENT_STATUSES for row in rows
        ),
        "status": status,
        "errors": errors,
    }
