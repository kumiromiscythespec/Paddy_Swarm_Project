from __future__ import annotations

from collections import Counter

from hole_containment_inspector import AXIS_INDEX, AXIS_KEYS, axis_name, component_bbox


def inspect_hole_seat(
    authority_row,
    containment_row,
    rail_component,
    diameter_definitions,
    tolerance=1e-9,
):
    bbox = component_bbox(rail_component)
    center = [float(value) for value in authority_row["axis_origin_xyz"]]
    axis = axis_name(authority_row["axis_direction_xyz"])
    axis_index = AXIS_INDEX[axis]
    diameter_class = authority_row.get("diameter_class") or (
        "M4-class"
        if authority_row["clearance_hole_candidate_mm"] < 5.0
        else "M5-class"
    )
    definition = diameter_definitions[diameter_class]
    seat_outer_diameter = max(
        float(definition["head_d"]),
        float(definition["washer_od"]),
    )
    seat_radius = seat_outer_diameter / 2.0
    radial_distances = []
    for index in range(3):
        if index == axis_index:
            continue
        low_key, high_key = AXIS_KEYS[index]
        radial_distances.append(
            min(center[index] - bbox[low_key], bbox[high_key] - center[index])
        )
    seat_margin = min(radial_distances) - seat_radius
    planar_seat = not containment_row["center_outside_material"]
    supported = (
        planar_seat
        and containment_row["full_circle_contained"]
        and seat_margin >= -tolerance
    )
    required = authority_row["rail_hole_required"] is True
    return {
        "instance_id": authority_row["instance_id"],
        "group_id": authority_row["group_id"],
        "opening_id": authority_row.get("opening_id"),
        "rail_hole_required": required,
        "planar_seat_exists": planar_seat,
        "seat_outer_diameter_mm": seat_outer_diameter,
        "seat_margin_to_edge_mm": seat_margin,
        "hole_to_edge_material": containment_row[
            "measured_ligament_edge_distance_mm"
        ],
        "adjacent_wall_collision_static": seat_margin < -tolerance,
        "wrench_head_clearance_status": (
            "STATIC_RADIAL_ENVELOPE_PASS"
            if seat_margin >= -tolerance
            else "FAIL_EDGE_ENVELOPE"
        ),
        "local_material_continuity": containment_row[
            "material_continuity_static"
        ],
        "unsupported_half_seat": not supported,
        "seat_status": "PASS_STATIC_SEAT_PROXY" if supported else "HOLE_SEAT_FAILURE",
        "required_seat_failure": required and not supported,
        "actual_solid_validation": "NOT_RUN",
    }


def inspect_all_hole_seats(
    authority_rows,
    containment_rows,
    rail_component,
    diameter_definitions,
):
    containment = {row["instance_id"]: row for row in containment_rows}
    return [
        inspect_hole_seat(
            row,
            containment[row["instance_id"]],
            rail_component,
            diameter_definitions,
        )
        for row in authority_rows
    ]


def summarize_hole_seats(rows):
    counts = Counter(row["seat_status"] for row in rows)
    return {
        "total_candidate_count": len(rows),
        "hole_seat_failure_count": counts["HOLE_SEAT_FAILURE"],
        "required_hole_seat_failure_count": sum(
            row["required_seat_failure"] for row in rows
        ),
        "status": (
            "PASS_REQUIRED_HOLE_SEATS_WITH_NONREQUIRED_CONTRADICTIONS"
            if not any(row["required_seat_failure"] for row in rows)
            else "FAIL_REQUIRED_HOLE_SEAT"
        ),
    }
