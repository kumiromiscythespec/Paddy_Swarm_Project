from __future__ import annotations
from cad_openings import opening_cutter
from cad_primitives import boxes_to_solid, intersect_volume, safe_boolean, shape_bbox, shape_volume
from registry_loader import component_index, opening_index

def run_collision_checks(parts, registries, tolerance_mm3=0.001):
    results = []
    errors = []
    for pair in registries["pairs"]:
        part_a = parts.get(pair["object_a"])
        part_b = parts.get(pair["object_b"])
        if part_a is None or part_b is None:
            results.append({
                "pair_id": pair["pair_id"],
                "object_a": pair["object_a"],
                "object_b": pair["object_b"],
                "classification": pair["classification"],
                "status": "NON_SOLID_OR_OUT_OF_BUILD_SCOPE",
                "intersection_volume_mm3": 0.0,
            })
            continue
        try:
            volume, exceeds = intersect_volume(part_a, part_b, tolerance_mm3)
            classification = pair["classification"]
            failure = classification in {
                "SEPARATED_REQUIRED",
                "FORBIDDEN_COLLISION",
                "REMOVAL_SWEEP_MUST_BE_CLEAR",
                "TOOL_SWEEP_MUST_BE_CLEAR",
            } and exceeds
            status = "FAIL_COLLISION" if failure else "CLASSIFIED_SOLID_RESULT"
            results.append({
                "pair_id": pair["pair_id"],
                "object_a": pair["object_a"],
                "object_b": pair["object_b"],
                "classification": classification,
                "status": status,
                "intersection_volume_mm3": volume,
            })
        except Exception as exc:
            errors.append({
                "pair_id": pair["pair_id"],
                "object_a": pair["object_a"],
                "object_b": pair["object_b"],
                "error": str(exc),
            })
            results.append({
                "pair_id": pair["pair_id"],
                "object_a": pair["object_a"],
                "object_b": pair["object_b"],
                "classification": pair["classification"],
                "status": "BOOLEAN_OPERATION_ERROR",
                "intersection_volume_mm3": "NOT_AVAILABLE",
            })
    return results, errors

def run_containment_checks(parts, registries, tolerance_mm3=0.001):
    results = []
    for entry in registries["containments"]:
        cover = entry["cover_component"]
        cover_shape = parts.get(cover)
        for contained_id in entry["contained_components"]:
            contained = parts.get(contained_id)
            if cover_shape is None or contained is None:
                results.append({
                    "cover_component": cover,
                    "contained_component": contained_id,
                    "status": "NON_SOLID_OR_OUT_OF_BUILD_SCOPE",
                    "wall_intersection_volume_mm3": "NOT_AVAILABLE",
                })
                continue
            volume, intersects = intersect_volume(cover_shape, contained, tolerance_mm3)
            results.append({
                "cover_component": cover,
                "contained_component": contained_id,
                "status": "FAIL_WALL_INTERSECTION" if intersects else "PASS_SOLID",
                "wall_intersection_volume_mm3": volume,
            })
    return results

def run_penetration_checks(parts, registries, tolerance_mm3=0.001):
    openings = opening_index(registries)
    results = []
    for pair in registries["pairs"]:
        if pair["classification"] not in {
            "FASTENER_PENETRATION_ALLOWED",
            "SHAFT_PENETRATION_ALLOWED",
            "CABLE_PASSAGE_ALLOWED",
            "DRAIN_PASSAGE_ALLOWED",
        }:
            continue
        left = parts.get(pair["object_a"])
        right = parts.get(pair["object_b"])
        opening_id = pair.get("opening_id", "")
        if left is None or right is None or opening_id not in openings:
            results.append({
                "pair_id": pair["pair_id"],
                "opening_id": opening_id,
                "status": "UNDECLARED_PENETRATION" if not opening_id else "NON_SOLID_OR_OUT_OF_BUILD_SCOPE",
                "residual_volume_mm3": "NOT_AVAILABLE",
            })
            continue
        common = safe_boolean(left, right, "intersect", f"{pair['pair_id']}:penetration")
        residual = safe_boolean(common, opening_cutter(openings[opening_id]), "cut", f"{pair['pair_id']}:registered_opening")
        residual_volume = shape_volume(residual)
        results.append({
            "pair_id": pair["pair_id"],
            "opening_id": opening_id,
            "status": "UNDECLARED_PENETRATION" if residual_volume > tolerance_mm3 else "PASS_REGISTERED_OPENING",
            "residual_volume_mm3": residual_volume,
        })
    return results

def run_service_sweep_checks(parts, registries, tolerance_mm3=0.001):
    service_roles = {
        "service_sweep", "tool_keepout", "fastener_tool", "fastener_removal",
        "fastener_insertion", "battery_extraction", "human_press_envelope",
    }
    components = component_index(registries)
    fastener_by_id = {
        item["fastener_instance_id"]: item
        for item in registries["fasteners"]["instances"]
    }
    results = []
    for sweep in registries["components"]:
        if sweep["classification"] != "KEEP_OUT" or sweep["role"] not in service_roles:
            continue
        sweep_shape = boxes_to_solid(sweep["boxes"])
        sweep_box = shape_bbox(sweep_shape)
        allowed = set()
        for instance_id, instance in fastener_by_id.items():
            if instance_id in sweep["part_id"]:
                allowed.update({instance["parent_component"], instance["child_component"]})
        if "BATTERY" in sweep["part_id"]:
            allowed.update({"BATTERY_PLACEHOLDER", "BATTERY_CASSETTE_ENVELOPE"})
        for part_id, part in parts.items():
            if part_id in allowed or part_id not in components:
                continue
            part_box = shape_bbox(part)
            separated = (
                sweep_box["xmax"] <= part_box["xmin"] or part_box["xmax"] <= sweep_box["xmin"]
                or sweep_box["ymax"] <= part_box["ymin"] or part_box["ymax"] <= sweep_box["ymin"]
                or sweep_box["zmax"] <= part_box["zmin"] or part_box["zmax"] <= sweep_box["zmin"]
            )
            if separated:
                continue
            volume, intersects = intersect_volume(sweep_shape, part, tolerance_mm3)
            results.append({
                "sweep_id": sweep["part_id"],
                "part_id": part_id,
                "sweep_role": sweep["role"],
                "intersection_volume_mm3": volume,
                "status": "FAIL_SWEEP_OBSTRUCTION" if intersects else "PASS_CLEAR",
            })
    return results

def resolve_review_overlaps(collision_results, registries):
    collision_by_id = {item["pair_id"]: item for item in collision_results}
    resolutions = []
    for pair in registries["pairs"]:
        if pair.get("v229_3_classification") != "PROXY_OVERLAP_REQUIRES_REVIEW":
            continue
        solid = collision_by_id.get(pair["pair_id"])
        status = "MEASUREMENT_CONDITIONAL"
        if solid and solid["status"] == "BOOLEAN_OPERATION_ERROR":
            status = "HOLD_BOOLEAN_FAILURE"
        elif solid and float(solid.get("intersection_volume_mm3", 0.0)) <= 0.001:
            status = "RESOLVED_SEPARATED_AFTER_REAL_GEOMETRY"
        elif pair.get("opening_id"):
            status = "RESOLVED_REGISTERED_PENETRATION"
        resolutions.append({
            "pair_id": pair["pair_id"],
            "object_a": pair["object_a"],
            "object_b": pair["object_b"],
            "resolution": status,
            "measurement_item": pair.get("measurement_item", ""),
            "failure_consequence": pair.get("failure_consequence", ""),
        })
    return resolutions
