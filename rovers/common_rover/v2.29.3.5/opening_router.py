from __future__ import annotations

from collections import Counter

from fastener_requirement_authority import (
    classify_fastener_requirements,
    validate_requirement_authority,
)
from opening_reachability import static_opening_reachability

ACTIVE_PART_ID = "V2292-FPB-RAIL-L"
AUTHORIZED_REQUIRED = {
    "REQUIRED_RAIL_THROUGH_HOLE",
    "REQUIRED_RAIL_BLIND_OR_TAPPED_HOLE",
    "REQUIRED_RAIL_SLOT_OR_NOTCH",
}


def _active_component(registries):
    return next(
        row
        for row in registries["components"]
        if row["part_id"] == ACTIVE_PART_ID
    )


def _openings_by_id(registries):
    return {
        row["opening_id"]: row
        for row in registries["openings"]
        if row.get("host_component") == ACTIVE_PART_ID
    }


def route_loop001_openings(registries):
    """Route after requirement authority; reachability never creates authority."""
    authority_rows = classify_fastener_requirements(registries)
    openings = _openings_by_id(registries)
    host = _active_component(registries)
    routed = []
    for authority in authority_rows:
        opening = openings.get(authority["opening_id"])
        reachability = (
            static_opening_reachability(opening, host) if opening else None
        )
        required = authority["requirement_status"] in AUTHORIZED_REQUIRED
        reachable = bool(
            reachability and reachability["intersects_host_bbox"]
        )
        if required and reachable:
            category = "AUTHORIZED_REQUIRED_RAIL_HOLE"
            owner = "CAD_FASTENERS"
            subtract = True
            status = "ROUTED_REQUIRED_HOLE_AFTER_AUTHORITY"
        elif required:
            category = "REQUIRED_HOLE_UNREACHABLE"
            owner = "CAD_FASTENERS"
            subtract = False
            status = "HARD_FAILURE_REQUIRED_HOLE_UNREACHABLE"
        else:
            category = "AUTHORITY_HOLD_NO_SUBTRACTION"
            owner = "MEASUREMENT_HOLD"
            subtract = False
            status = authority["requirement_status"]
        routed.append(
            {
                "opening_id": authority["opening_id"],
                "fastener_instance_id": authority["instance_id"],
                "fastener_group_id": authority["group_id"],
                "host_component": ACTIVE_PART_ID,
                "requirement_status": authority["requirement_status"],
                "requirement_authority": authority["requirement_authority"],
                "rail_hole_required": authority["rail_hole_required"],
                "routing_category": category,
                "execution_owner": owner,
                "subtract_from_host": subtract,
                "hard_failure_if_missing": required,
                "required_classified_before_reachability": True,
                "reachability_used_for_requirement": False,
                "intersects_host_bbox": reachable,
                "reachability_status": (
                    "REACHABLE"
                    if reachable
                    else "UNREACHABLE"
                    if reachability
                    else "NO_OPENING_RECORD"
                ),
                "source_center": authority["axis_origin_xyz"],
                "transformed_center": authority["axis_origin_xyz"],
                "transformed_axis": authority["axis_direction_xyz"],
                "coordinate_space": "ASSEMBLY_GLOBAL",
                "coordinate_relocated": False,
                "stale_auto_conversion": False,
                "duplicate_route_count": 1,
                "status": status,
                "reachability": reachability,
            }
        )
    return routed


def validate_routing(rows, expected_total=24):
    counts = Counter(row["routing_category"] for row in rows)
    errors = []
    if len(rows) != expected_total:
        errors.append("ROUTING_TOTAL_MISMATCH")
    if len({row["fastener_instance_id"] for row in rows}) != len(rows):
        errors.append("DOUBLE_ROUTED_INSTANCE")
    if any(row["duplicate_route_count"] != 1 for row in rows):
        errors.append("DOUBLE_ROUTED_OPENING")
    if any(not row["required_classified_before_reachability"] for row in rows):
        errors.append("REQUIREMENT_REACHABILITY_CYCLE")
    if any(row["reachability_used_for_requirement"] for row in rows):
        errors.append("REACHABILITY_USED_AS_REQUIREMENT_AUTHORITY")
    if any(row["stale_auto_conversion"] for row in rows):
        errors.append("UNREACHABLE_AUTO_CONVERTED_TO_STALE")
    if any(row["coordinate_relocated"] for row in rows):
        errors.append("UNAUTHORIZED_COORDINATE_RELOCATION")
    if any(
        row["routing_category"] == "REQUIRED_HOLE_UNREACHABLE"
        and row["status"] != "HARD_FAILURE_REQUIRED_HOLE_UNREACHABLE"
        for row in rows
    ):
        errors.append("REQUIRED_UNREACHABLE_NOT_HARD_FAILURE")
    if any(
        row["routing_category"] == "AUTHORITY_HOLD_NO_SUBTRACTION"
        and row["subtract_from_host"]
        for row in rows
    ):
        errors.append("HOLD_DIRECTLY_SUBTRACTED")
    if any(
        row["routing_category"] == "AUTHORIZED_REQUIRED_RAIL_HOLE"
        and (
            row["execution_owner"] != "CAD_FASTENERS"
            or row["subtract_from_host"] is not True
        )
        for row in rows
    ):
        errors.append("AUTHORIZED_HOLE_OWNER_MISMATCH")
    return {
        "status": "PASS" if not errors else "FAIL",
        "total_reviewed": len(rows),
        "counts": dict(counts),
        "required_hole_static_unreachable_count": counts[
            "REQUIRED_HOLE_UNREACHABLE"
        ],
        "stale_auto_conversion_count": sum(
            row["stale_auto_conversion"] for row in rows
        ),
        "double_routed_count": sum(
            row["duplicate_route_count"] != 1 for row in rows
        ),
        "errors": errors,
    }


def extract_loop001_fastener_instances(registries, routing_rows=None):
    """Compatibility export; authority rows are the source of responsibility."""
    rows = classify_fastener_requirements(registries)
    routed = {
        row["fastener_instance_id"]: row for row in (routing_rows or [])
    }
    return [
        {
            "fastener_instance_id": row["instance_id"],
            "fastener_group_id": row["group_id"],
            "mating_component": row["mating_component"],
            "rail_side_responsibility": row["requirement_status"],
            "expected_hole": row["opening_id"],
            "expected_axis": row["axis_direction_xyz"],
            "expected_center": row["axis_origin_xyz"],
            "expected_diameter_class": row[
                "clearance_hole_candidate_mm"
            ],
            "actual_subtractive": routed.get(
                row["instance_id"], {}
            ).get("subtract_from_host", False),
            "keep_out_only": False,
            "measurement_status": row["contradiction_status"],
            "coordinate_space": "ASSEMBLY_GLOBAL",
            "transformed_center": row["axis_origin_xyz"],
            "transformed_axis": row["axis_direction_xyz"],
            "mixed_coordinate_space": False,
        }
        for row in rows
    ]


def authority_and_routing_preflight(registries):
    authority = classify_fastener_requirements(registries)
    authority_gate = validate_requirement_authority(authority)
    routes = route_loop001_openings(registries)
    routing_gate = validate_routing(routes)
    return {
        "status": (
            "PASS_WITH_CONTRADICTION_HOLD"
            if not authority_gate["errors"] and routing_gate["status"] == "PASS"
            else "FAIL"
        ),
        "authority": authority,
        "authority_gate": authority_gate,
        "routes": routes,
        "routing_gate": routing_gate,
    }
