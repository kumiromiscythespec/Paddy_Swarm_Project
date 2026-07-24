from __future__ import annotations

from collections import Counter

AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}
AXIS_KEYS = (
    ("xmin", "xmax"),
    ("ymin", "ymax"),
    ("zmin", "zmax"),
)
EDGE_DISTANCE_CANDIDATE_MM = {
    "M3-class": 6.0,
    "M4-class": 8.0,
    "M5-class": 10.0,
}


def component_bbox(component):
    boxes = component["boxes"]
    return {
        "xmin": min(float(box[0]) for box in boxes),
        "xmax": max(float(box[1]) for box in boxes),
        "ymin": min(float(box[2]) for box in boxes),
        "ymax": max(float(box[3]) for box in boxes),
        "zmin": min(float(box[4]) for box in boxes),
        "zmax": max(float(box[5]) for box in boxes),
    }


def axis_name(direction):
    values = [float(value) for value in direction]
    index = max(range(3), key=lambda item: abs(values[item]))
    return "XYZ"[index]


def inspect_hole_containment(authority_row, rail_component, tolerance=1e-9):
    bbox = component_bbox(rail_component)
    center = [float(value) for value in authority_row["axis_origin_xyz"]]
    axis = axis_name(authority_row["axis_direction_xyz"])
    axis_index = AXIS_INDEX[axis]
    radius = float(authority_row["clearance_hole_candidate_mm"]) / 2.0
    radial_center_distances = []
    outside_distances = []
    breakout_directions = []
    for index in range(3):
        if index == axis_index:
            continue
        low_key, high_key = AXIS_KEYS[index]
        low_distance = center[index] - bbox[low_key]
        high_distance = bbox[high_key] - center[index]
        radial_center_distances.append(min(low_distance, high_distance))
        outside_distances.append(max(-low_distance, -high_distance, 0.0))
        if low_distance < radius - tolerance:
            breakout_directions.append(f"{'XYZ'[index]}_MIN")
        if high_distance < radius - tolerance:
            breakout_directions.append(f"{'XYZ'[index]}_MAX")
    center_edge_distance = min(radial_center_distances)
    ligament = center_edge_distance - radius
    center_outside = max(outside_distances) > tolerance
    full_circle = not center_outside and ligament >= -tolerance
    if center_outside:
        candidate_class = "RAIL_EXTERIOR_OR_CONTRADICTION"
    elif not full_circle:
        candidate_class = "EDGE_BREAKOUT"
    else:
        candidate_class = "FULLY_INTERIOR"
    diameter_class = authority_row.get("diameter_class") or (
        "M4-class"
        if authority_row["clearance_hole_candidate_mm"] < 5.0
        else "M5-class"
    )
    edge_requirement = EDGE_DISTANCE_CANDIDATE_MM[diameter_class]
    return {
        "instance_id": authority_row["instance_id"],
        "group_id": authority_row["group_id"],
        "opening_id": authority_row.get("opening_id"),
        "requirement_status": authority_row["requirement_status"],
        "rail_hole_required": authority_row["rail_hole_required"],
        "axis": axis,
        "hole_center": center,
        "hole_radius_mm": radius,
        "material_face_boundary": bbox,
        "measured_center_to_edge_mm": center_edge_distance,
        "measured_ligament_edge_distance_mm": ligament,
        "required_edge_distance_candidate_mm": edge_requirement,
        "edge_distance_deficit_mm": max(edge_requirement - ligament, 0.0),
        "full_circle_contained": full_circle,
        "center_outside_material": center_outside,
        "breakout": not full_circle,
        "breakout_direction": "|".join(breakout_directions) or "NONE",
        "candidate_class": candidate_class,
        "material_continuity_static": full_circle,
        "result": (
            "PASS_FULL_CIRCLE_STATIC"
            if full_circle
            else "DESIGN_ERROR_EDGE_BREAKOUT"
            if candidate_class == "EDGE_BREAKOUT"
            else "DESIGN_CONTRADICTION_RAIL_EXTERIOR"
        ),
        "strength_approval": "NOT_GRANTED_STATIC_LAYOUT_PROXY_ONLY",
    }


def inspect_all_hole_candidates(authority_rows, rail_component):
    return [
        inspect_hole_containment(row, rail_component)
        for row in authority_rows
    ]


def summarize_containment(rows):
    counts = Counter(row["candidate_class"] for row in rows)
    required = [row for row in rows if row["rail_hole_required"] is True]
    return {
        "total_candidate_count": len(rows),
        "fully_interior_hole_candidate_count": counts["FULLY_INTERIOR"],
        "edge_breakout_hole_candidate_count": counts["EDGE_BREAKOUT"],
        "rail_exterior_hole_candidate_count": counts[
            "RAIL_EXTERIOR_OR_CONTRADICTION"
        ],
        "required_hole_static_unreachable_count": sum(
            row["center_outside_material"] for row in required
        ),
        "required_hole_edge_breakout_count": sum(
            row["breakout"] for row in required
        ),
        "required_hole_material_continuity_failure_count": sum(
            not row["material_continuity_static"] for row in required
        ),
        "known_boundary_candidate_ids": [
            row["opening_id"]
            for row in rows
            if row["candidate_class"] == "EDGE_BREAKOUT"
        ],
        "status": (
            "PASS_REQUIRED_HOLES_WITH_NONREQUIRED_CONTRADICTIONS"
            if all(row["full_circle_contained"] for row in required)
            else "FAIL_REQUIRED_HOLE_GEOMETRY"
        ),
    }
