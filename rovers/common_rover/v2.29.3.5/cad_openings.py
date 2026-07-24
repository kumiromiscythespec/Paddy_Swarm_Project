from __future__ import annotations
from collections import defaultdict
from cad_primitives import box_from_center, cylinder_along_axis, safe_boolean, shape_volume
from registry_loader import component_index

CIRCULAR_TYPES = {
    "FASTENER_ACCESS_OPENING",
    "BEARING_SEAT",
    "SHAFT_PASSAGE",
    "DRAIN_OPENING",
    "CONNECTOR_OPENING",
    "CABLE_GLAND_OPENING",
    "HINGE_CLEARANCE",
    "LATCH_CLEARANCE",
}

def opening_cutter(opening):
    dimensions = [float(value) for value in opening["dimensions_mm"]]
    if len(dimensions) != 3 or min(dimensions) <= 0:
        raise ValueError(f"{opening['opening_id']} has invalid dimensions")
    if opening["type"] in CIRCULAR_TYPES:
        direction = opening["direction"]
        axis_index = {"X": 0, "Y": 1, "Z": 2}[direction[0].upper()]
        length = dimensions[axis_index] + 4.0
        diameter = min(dimensions[index] for index in range(3) if index != axis_index)
        return cylinder_along_axis(opening["center_xyz"], direction, diameter, length)
    return box_from_center(opening["center_xyz"], [value + 2.0 for value in dimensions])

def build_bearing_seat(opening):
    if opening["type"] != "BEARING_SEAT":
        raise ValueError("bearing seat builder received another opening type")
    return opening_cutter(opening)

def build_shaft_passage(opening):
    if opening["type"] != "SHAFT_PASSAGE":
        raise ValueError("shaft passage builder received another opening type")
    return opening_cutter(opening)

def build_belt_cavity(opening):
    if opening["type"] not in {"BELT_CLEARANCE", "PULLEY_CLEARANCE"}:
        raise ValueError("belt cavity builder received another opening type")
    return opening_cutter(opening)

def build_drain_opening(opening):
    if opening["type"] != "DRAIN_OPENING":
        raise ValueError("drain builder received another opening type")
    return opening_cutter(opening)

def build_tool_opening(opening):
    if opening["type"] != "TOOL_ACCESS_OPENING":
        raise ValueError("tool-opening builder received another opening type")
    if opening["execution_class"] != "FUNCTIONAL_SUBTRACTIVE_OPENING":
        raise ValueError("service keep-out must not be subtracted")
    return opening_cutter(opening)

def apply_functional_openings(parts, params, registries, allow_measurement_candidates=True):
    by_host = defaultdict(list)
    components = component_index(registries)
    for opening in registries["openings"]:
        by_host[opening["host_component"]].append(opening)
    results = []
    updated = dict(parts)
    for host_id, openings in sorted(by_host.items()):
        if host_id not in updated:
            for opening in openings:
                results.append({
                    "opening_id": opening["opening_id"],
                    "host_component": host_id,
                    "status": "HOST_NOT_IN_BUILD_SCOPE",
                    "execution_class": opening["execution_class"],
                })
            continue
        host = updated[host_id]
        for opening in openings:
            category = opening["execution_class"]
            host_class = components.get(host_id, {}).get("classification", "")
            should_cut = category == "FUNCTIONAL_SUBTRACTIVE_OPENING" or (
                allow_measurement_candidates and category == "MEASUREMENT_HOLD_OPENING"
            )
            delegated_fastener_hole = opening["type"] == "FASTENER_ACCESS_OPENING"
            if delegated_fastener_hole:
                should_cut = False
            product_pattern_hold = host_class in {"MECHANICAL_PLACEHOLDER", "SEALED_DRY_COMPONENT"}
            if product_pattern_hold:
                should_cut = False
            before = shape_volume(host)
            if should_cut:
                cutter = opening_cutter(opening)
                cutter_volume = shape_volume(cutter)
                after_shape = safe_boolean(host, cutter, "cut", opening["opening_id"])
                after = shape_volume(after_shape)
                success = after < before - params["boolean_volume_tolerance_mm3"]
                host = after_shape
                status = "SUBTRACTED" if success else "CUTTER_DID_NOT_REACH_HOST"
            else:
                cutter_volume = 0.0
                after = before
                success = category in {"SERVICE_KEEP_OUT_ONLY", "REFERENCE_ONLY"} or product_pattern_hold or delegated_fastener_hole
                status = (
                    "DELEGATED_TO_FASTENER_HOLE_ENGINE"
                    if delegated_fastener_hole and not product_pattern_hold
                    else "PRODUCT_PATTERN_MEASUREMENT_HOLD"
                    if product_pattern_hold
                    else "NON_SUBTRACTIVE_POLICY_CONFIRMED"
                )
            results.append({
                "opening_id": opening["opening_id"],
                "host_component": host_id,
                "execution_class": category,
                "host_before_volume_mm3": before,
                "cutter_volume_mm3": cutter_volume,
                "host_after_volume_mm3": after,
                "successful_subtraction": success,
                "status": status,
            })
        updated[host_id] = host
    return updated, results


def apply_routed_functional_openings(host_solid, routed_openings, boolean_tolerance_mm3=0.001):
    result = host_solid
    rows = []
    for route in sorted(routed_openings, key=lambda item: item["opening_id"]):
        if route.get("execution_owner") != "CAD_OPENINGS":
            if route.get("subtract_from_host"):
                raise RuntimeError(
                    f"direct-cut owner violation: {route['opening_id']}"
                )
            rows.append({
                "opening_id": route["opening_id"],
                "status": "NOT_OWNED_BY_CAD_OPENINGS_NO_MUTATION",
                "execution_owner": route.get("execution_owner"),
                "subtract_from_host": False,
            })
            continue
        if route.get("execution_class") != "FUNCTIONAL_SUBTRACTIVE":
            raise RuntimeError(
                f"CAD_OPENINGS received non-functional route: {route['opening_id']}"
            )
        before = shape_volume(result)
        cutter = opening_cutter(route["source_opening"])
        candidate = safe_boolean(
            result, cutter, "cut", f"functional:{route['opening_id']}"
        )
        after = shape_volume(candidate)
        if before - after <= float(boolean_tolerance_mm3):
            raise RuntimeError(
                f"CUTTER_DID_NOT_REACH_HOST:{route['opening_id']}"
            )
        result = candidate
        rows.append({
            "opening_id": route["opening_id"], "status": "SUBTRACTED",
            "execution_owner": "CAD_OPENINGS",
            "removed_volume_mm3": before - after,
        })
    return result, rows
