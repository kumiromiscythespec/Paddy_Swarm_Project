from __future__ import annotations
import math

AXIS_INDEX = {"X": 0, "Y": 1, "Z": 2}
AXIS_KEYS = (
    ("xmin", "xmax"), ("ymin", "ymax"), ("zmin", "zmax"),
)

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

def _axis_token(direction):
    if isinstance(direction, str):
        token = direction.strip().upper()
        return token[0], -1.0 if token.endswith("-") else 1.0
    values = [float(value) for value in direction]
    dominant = max(range(3), key=lambda index: abs(values[index]))
    return "XYZ"[dominant], -1.0 if values[dominant] < 0 else 1.0

def _diameter_and_length(opening):
    dimensions = [float(value) for value in opening["dimensions_mm"]]
    axis, _ = _axis_token(opening["direction"])
    axis_index = AXIS_INDEX[axis]
    diameter = min(
        dimensions[index] for index in range(3) if index != axis_index
    )
    return axis_index, diameter, dimensions[axis_index]

def static_opening_reachability(opening, host_component, tolerance=1e-9):
    bbox = component_bbox(host_component)
    center = [float(value) for value in opening["center_xyz"]]
    axis_name, sign = _axis_token(opening["direction"])
    axis_index, diameter, length = _diameter_and_length(opening)
    radius = diameter / 2.0
    segment_min = center[axis_index] - length / 2.0
    segment_max = center[axis_index] + length / 2.0
    axis_keys = AXIS_KEYS[axis_index]
    axis_hit = (
        segment_max >= bbox[axis_keys[0]] - tolerance
        and segment_min <= bbox[axis_keys[1]] + tolerance
    )
    radial_hits = []
    radial_edge_distances = []
    for index in range(3):
        if index == axis_index:
            continue
        low_key, high_key = AXIS_KEYS[index]
        radial_hits.append(
            center[index] + radius >= bbox[low_key] - tolerance
            and center[index] - radius <= bbox[high_key] + tolerance
        )
        radial_edge_distances.append(min(
            center[index] - bbox[low_key],
            bbox[high_key] - center[index],
        ))
    intersects = axis_hit and all(radial_hits)
    expected_entry = list(center)
    expected_exit = list(center)
    expected_entry[axis_index] = (
        bbox[axis_keys[0]] if sign > 0 else bbox[axis_keys[1]]
    )
    expected_exit[axis_index] = (
        bbox[axis_keys[1]] if sign > 0 else bbox[axis_keys[0]]
    )
    center_inside_flange = all(
        bbox[AXIS_KEYS[index][0]] - tolerance
        <= center[index]
        <= bbox[AXIS_KEYS[index][1]] + tolerance
        for index in range(3) if index != axis_index
    )
    return {
        "opening_id": opening["opening_id"],
        "host_component": opening["host_component"],
        "rail_bbox": bbox,
        "axis": axis_name, "axis_sign": sign,
        "axis_line_origin": center,
        "cutter_segment_min": segment_min,
        "cutter_segment_max": segment_max,
        "cutter_diameter_mm": diameter,
        "expected_face": f"{axis_name}_{'MIN' if sign > 0 else 'MAX'}",
        "expected_entry_point": expected_entry,
        "expected_exit_point": expected_exit,
        "intersects_host_bbox": intersects,
        "center_inside_flange_candidate": center_inside_flange,
        "edge_distance_candidate_mm": min(radial_edge_distances),
        "reachability_method": "REGISTRY_AABB_AXIS_SEGMENT_AND_RADIAL_ENVELOPE",
    }

def transform_axis_record(instance, coordinate_space="ASSEMBLY_GLOBAL"):
    if coordinate_space not in {"PART_LOCAL", "ASSEMBLY_GLOBAL"}:
        raise ValueError(coordinate_space)
    origin = [float(value) for value in instance["axis_origin_xyz"]]
    axis = [float(value) for value in instance["axis_direction_xyz"]]
    if coordinate_space == "PART_LOCAL":
        raise ValueError(
            "PART_LOCAL requires an explicit non-identity assembly transform; "
            "the inherited registry provides assembly-global coordinates only"
        )
    return {
        "fastener_instance_id": instance["fastener_instance_id"],
        "coordinate_space": "ASSEMBLY_GLOBAL",
        "local_origin": None,
        "local_origin_status": "REPOSITORY_DEFINITION_MISSING_NOT_ASSUMED",
        "assembly_transform": "IDENTITY_GLOBAL_REGISTRY_COORDINATES",
        "transformed_center": origin,
        "transformed_axis": axis,
        "transform_applied": False,
        "mixed_coordinate_space": False,
    }
