from __future__ import annotations
from cad_primitives import cylinder_along_axis, geometry_fingerprint, safe_boolean, shape_bbox, shape_volume, union_all
from registry_loader import component_index

def fastener_hole_cutter(instance, target):
    if target not in {"parent", "child"}:
        raise ValueError(target)
    diameter = float(instance["clearance_hole_candidate_mm"])
    length = max(float(instance["grip_length_candidate_mm"]) + 8.0, diameter * 2.0)
    return cylinder_along_axis(instance["axis_origin_xyz"], instance["axis_direction_xyz"], diameter, length)

def build_fastener_placeholder(instance):
    diameter = float(instance["hole_diameter_candidate_mm"])
    length = max(float(instance["grip_length_candidate_mm"]), diameter)
    axis = tuple(float(value) for value in instance["axis_direction_xyz"])
    origin = tuple(float(value) for value in instance["axis_origin_xyz"])
    def shifted(distance):
        return tuple(origin[index] + axis[index] * distance for index in range(3))
    head = instance["head_envelope"]
    washer = instance["washer_envelope"]
    nut = instance["nut_or_insert_envelope"]
    head_height = float(head["height_mm"])
    washer_thickness = float(washer["thickness_mm"])
    nut_height = float(nut["maximum_mm"]) * 0.6
    shaft = cylinder_along_axis(origin, axis, diameter, length)
    head_solid = cylinder_along_axis(
        shifted(-length / 2.0 - head_height / 2.0),
        axis,
        float(head["diameter_mm"]),
        head_height,
    )
    washer_solid = cylinder_along_axis(
        shifted(-length / 2.0 + washer_thickness / 2.0),
        axis,
        float(washer["od_mm"]),
        washer_thickness,
    )
    nut_solid = cylinder_along_axis(
        shifted(length / 2.0 + nut_height / 2.0),
        axis,
        float(nut["maximum_mm"]),
        nut_height,
    )
    return union_all([shaft, head_solid, washer_solid, nut_solid])

def bind_actual_faces(instance, parent, child, tolerance_mm=1.0):
    axis = tuple(float(value) for value in instance["axis_direction_xyz"])
    origin = tuple(float(value) for value in instance["axis_origin_xyz"])
    parent_box = shape_bbox(parent)
    child_box = shape_bbox(child)
    dominant = max(range(3), key=lambda index: abs(axis[index]))
    keys = (("xmin", "xmax"), ("ymin", "ymax"), ("zmin", "zmax"))[dominant]
    coordinate = origin[dominant]
    parent_distance = min(abs(coordinate - parent_box[key]) for key in keys)
    child_distance = min(abs(coordinate - child_box[key]) for key in keys)
    cutter = fastener_hole_cutter(instance, "parent")
    parent_intersection = shape_volume(parent.intersect(cutter))
    child_intersection = shape_volume(child.intersect(cutter))
    result = {
        "fastener_instance_id": instance["fastener_instance_id"],
        "binding_method": "BBOX_FACE_DISTANCE_AND_AXIS_INTERSECTION_PROXY",
        "parent_binding": "AXIS_INTERSECTION_AND_BBOX_FACE_DISTANCE",
        "child_binding": "AXIS_INTERSECTION_AND_BBOX_FACE_DISTANCE",
        "found_normal": axis,
        "planar_status": "BBOX_PROXY_NOT_CAD_FACE",
        "measurement_hold": instance.get("measurement_status", ""),
        "expected_face_normal": axis,
        "expected_face_center": origin,
        "parent_face_distance_mm": parent_distance,
        "child_face_distance_mm": child_distance,
        "axis_intersects_parent": parent_intersection > 0.0,
        "axis_intersects_child": child_intersection > 0.0,
        "parent_material_thickness_proxy_mm": parent_box[("xlen", "ylen", "zlen")[dominant]],
        "child_material_thickness_proxy_mm": child_box[("xlen", "ylen", "zlen")[dominant]],
    }
    result["status"] = (
        "BBOX_PROXY_PASS_CANDIDATE"
        if result["axis_intersects_parent"]
        and result["axis_intersects_child"]
        and parent_distance <= float(tolerance_mm)
        and child_distance <= float(tolerance_mm)
        else "FAIL"
    )
    return result

def apply_fastener_holes(parts, params, registries):
    updated = dict(parts)
    components = component_index(registries)
    hole_results = []
    face_results = []
    fastener_solids = {}
    for instance in registries["fasteners"]["instances"]:
        iid = instance["fastener_instance_id"]
        parent_id = instance["parent_component"]
        child_id = instance["child_component"]
        fastener_solids[f"FASTENER_SOLID_{iid}"] = build_fastener_placeholder(instance)
        if parent_id not in updated or child_id not in updated:
            hole_results.append({
                "fastener_instance_id": iid,
                "parent_component": parent_id,
                "child_component": child_id,
                "parent_hole": "HOST_NOT_IN_BUILD_SCOPE",
                "child_hole": "HOST_NOT_IN_BUILD_SCOPE",
            })
            continue
        parent = updated[parent_id]
        child = updated[child_id]
        face_results.append(bind_actual_faces(instance, parent, child, params["face_binding_tolerance_mm"]))
        parent_before = shape_volume(parent)
        child_before = shape_volume(child)
        parent_cutter = fastener_hole_cutter(instance, "parent")
        child_cutter = fastener_hole_cutter(instance, "child")
        parent_product = components.get(parent_id, {}).get("classification") in {"MECHANICAL_PLACEHOLDER", "SEALED_DRY_COMPONENT"}
        child_product = components.get(child_id, {}).get("classification") in {"MECHANICAL_PLACEHOLDER", "SEALED_DRY_COMPONENT"}
        parent_after = parent if parent_product else safe_boolean(parent, parent_cutter, "cut", f"{iid}:parent")
        child_after = child if child_product else safe_boolean(child, child_cutter, "cut", f"{iid}:child")
        parent_removed = parent_before - shape_volume(parent_after)
        child_removed = child_before - shape_volume(child_after)
        updated[parent_id] = parent_after
        updated[child_id] = child_after
        hole_results.append({
            "fastener_instance_id": iid,
            "parent_component": parent_id,
            "child_component": child_id,
            "axis_origin_xyz": instance["axis_origin_xyz"],
            "axis_direction_xyz": instance["axis_direction_xyz"],
            "parent_removed_volume_mm3": parent_removed,
            "child_removed_volume_mm3": child_removed,
            "parent_hole": "EXISTING_PRODUCT_PATTERN_MEASUREMENT_HOLD" if parent_product else "GENERATED" if parent_removed > 0.0 else "FAIL",
            "child_hole": "EXISTING_PRODUCT_PATTERN_MEASUREMENT_HOLD" if child_product else "GENERATED" if child_removed > 0.0 else "FAIL",
            "axis_source": instance["axis_source"],
            "center_to_center_dependency": instance["center_to_center_dependency"],
        })
    return updated, fastener_solids, hole_results, face_results


OPENING_FAILURE_STATUSES = {
    "CUTTER_DID_NOT_REACH_HOST", "HOST_NOT_FOUND", "INVALID_CUTTER",
    "CUT_FAILED", "FINAL_HOLE_NOT_DETECTED", "WRONG_HOST",
    "DUPLICATE_CUT", "REQUIRED_OPENING_NOT_EXECUTED",
}

def apply_required_rail_holes(
    rail_solid, routed_openings, fastener_instances,
    boolean_tolerance_mm3=0.001,
):
    instances = {
        item["fastener_instance_id"]: item for item in fastener_instances
    }
    result = rail_solid
    rows = []
    executed = set()
    required = [
        route for route in routed_openings
        if route.get("hard_failure_if_missing")
    ]
    for route in sorted(required, key=lambda item: item["opening_id"]):
        opening_id = route["opening_id"]
        instance_id = route.get("fastener_instance_id")
        if route.get("execution_owner") != "CAD_FASTENERS":
            rows.append({
                "opening_id": opening_id,
                "fastener_instance_id": instance_id,
                "status": "WRONG_HOST",
                "hard_failure": True,
            })
            continue
        if opening_id in executed:
            rows.append({
                "opening_id": opening_id,
                "fastener_instance_id": instance_id,
                "status": "DUPLICATE_CUT",
                "hard_failure": True,
            })
            continue
        instance = instances.get(instance_id)
        if instance is None:
            rows.append({
                "opening_id": opening_id,
                "fastener_instance_id": instance_id,
                "status": "HOST_NOT_FOUND",
                "hard_failure": True,
            })
            continue
        try:
            cutter = fastener_hole_cutter(
                instance,
                "parent"
                if instance["parent_component"] == "V2292-FPB-RAIL-L"
                else "child",
            )
            before = shape_volume(result)
            candidate = safe_boolean(
                result, cutter, "cut", f"required-rail-hole:{opening_id}"
            )
            after = shape_volume(candidate)
            removed = before - after
            if removed <= float(boolean_tolerance_mm3):
                status = "CUTTER_DID_NOT_REACH_HOST"
                hard = True
            else:
                result = candidate
                status = "GENERATED_REQUIRES_FINAL_HOLE_INSPECTION"
                hard = False
                executed.add(opening_id)
        except Exception as exc:
            removed = 0.0
            status = "INVALID_CUTTER" if isinstance(exc, ValueError) else "CUT_FAILED"
            hard = True
        rows.append({
            "opening_id": opening_id,
            "fastener_instance_id": instance_id,
            "status": status, "hard_failure": hard,
            "removed_volume_mm3": removed,
            "execution_owner": "CAD_FASTENERS",
        })
    for route in required:
        if route["opening_id"] not in {
            row["opening_id"] for row in rows
        }:
            rows.append({
                "opening_id": route["opening_id"],
                "fastener_instance_id": route.get("fastener_instance_id"),
                "status": "REQUIRED_OPENING_NOT_EXECUTED",
                "hard_failure": True,
            })
    return result, rows

def aggregate_required_hole_gate(rows, final_solid_valid):
    failed = sum(
        row.get("status") in OPENING_FAILURE_STATUSES
        or row.get("hard_failure")
        for row in rows
    )
    did_not_reach = sum(
        row.get("status") == "CUTTER_DID_NOT_REACH_HOST" for row in rows
    )
    invalid = int(not final_solid_valid)
    return {
        "status": "PASS" if not (failed or did_not_reach or invalid) else "FAIL",
        "required_rail_hole_execution_count": len(rows),
        "failed_required_rail_hole_count": failed,
        "cutter_did_not_reach_required_host_count": did_not_reach,
        "invalid_rail_after_cut_count": invalid,
    }
