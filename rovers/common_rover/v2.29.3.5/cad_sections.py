from __future__ import annotations
from cad_primitives import box_from_bounds, safe_boolean, shape_bbox, shape_volume

SECTION_SPECS = [
    {"section_id": "center_longitudinal", "axis": "X", "coordinate": 0.0, "keep_side": "POSITIVE", "margin": 30.0, "included_component_classes": ["STRUCTURAL", "MECHANICAL_PLACEHOLDER", "NONSTRUCTURAL_PROTECTIVE", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"], "excluded_component_classes": [], "expected_purpose": "center longitudinal inspection"},
    {"section_id": "left_motor_input", "axis": "X", "coordinate": 70.0, "keep_side": "POSITIVE", "margin": 30.0, "included_component_classes": ["STRUCTURAL", "MECHANICAL_PLACEHOLDER", "NONSTRUCTURAL_PROTECTIVE", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"], "excluded_component_classes": [], "expected_purpose": "left motor and input cartridge"},
    {"section_id": "right_motor_input", "axis": "X", "coordinate": -70.0, "keep_side": "NEGATIVE", "margin": 30.0, "included_component_classes": ["STRUCTURAL", "MECHANICAL_PLACEHOLDER", "NONSTRUCTURAL_PROTECTIVE", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"], "excluded_component_classes": [], "expected_purpose": "right motor and input cartridge"},
    {"section_id": "left_output_PTO", "axis": "X", "coordinate": 90.0, "keep_side": "POSITIVE", "margin": 30.0, "included_component_classes": ["STRUCTURAL", "MECHANICAL_PLACEHOLDER", "NONSTRUCTURAL_PROTECTIVE", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"], "excluded_component_classes": [], "expected_purpose": "left output and PTO"},
    {"section_id": "right_output_PTO", "axis": "X", "coordinate": -90.0, "keep_side": "NEGATIVE", "margin": 30.0, "included_component_classes": ["STRUCTURAL", "MECHANICAL_PLACEHOLDER", "NONSTRUCTURAL_PROTECTIVE", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"], "excluded_component_classes": [], "expected_purpose": "right output and PTO"},
    {"section_id": "servo_cam_transverse", "axis": "Y", "coordinate": -205.0, "keep_side": "NEGATIVE", "margin": 30.0, "included_component_classes": ["STRUCTURAL", "MECHANICAL_PLACEHOLDER", "NONSTRUCTURAL_PROTECTIVE", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"], "excluded_component_classes": [], "expected_purpose": "servo and cam transverse inspection"},
    {"section_id": "E_stop_battery", "axis": "Y", "coordinate": 95.0, "keep_side": "POSITIVE", "margin": 30.0, "included_component_classes": ["STRUCTURAL", "MECHANICAL_PLACEHOLDER", "NONSTRUCTURAL_PROTECTIVE", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"], "excluded_component_classes": [], "expected_purpose": "E-stop and battery inspection"},
    {"section_id": "CBOX_lid_portal", "axis": "Y", "coordinate": -65.0, "keep_side": "NEGATIVE", "margin": 30.0, "included_component_classes": ["STRUCTURAL", "MECHANICAL_PLACEHOLDER", "NONSTRUCTURAL_PROTECTIVE", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"], "excluded_component_classes": [], "expected_purpose": "CBOX lid and portal inspection"},
    {"section_id": "hitch_front_shell", "axis": "Y", "coordinate": -235.0, "keep_side": "NEGATIVE", "margin": 30.0, "included_component_classes": ["STRUCTURAL", "MECHANICAL_PLACEHOLDER", "NONSTRUCTURAL_PROTECTIVE", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"], "excluded_component_classes": [], "expected_purpose": "hitch and front shell inspection"},
]

AXIS_BOUNDS = {"X": ("xmin", "xmax"), "Y": ("ymin", "ymax"), "Z": ("zmin", "zmax")}
AXIS_INDEX = {"X": (0, 1), "Y": (2, 3), "Z": (4, 5)}

def classify_bbox_for_section(bbox, specification, tolerance=0.01):
    low_key, high_key = AXIS_BOUNDS[specification["axis"]]
    low, high = float(bbox[low_key]), float(bbox[high_key])
    coordinate = float(specification["coordinate"])
    side = specification["keep_side"]
    if abs(low - coordinate) <= tolerance or abs(high - coordinate) <= tolerance:
        return "TOUCHES_SECTION_WITHIN_TOLERANCE"
    if side == "POSITIVE":
        if low > coordinate + tolerance:
            return "FULLY_KEPT"
        if high < coordinate - tolerance:
            return "FULLY_REMOVED"
        return "CROSSES_SECTION"
    if side == "NEGATIVE":
        if high < coordinate - tolerance:
            return "FULLY_KEPT"
        if low > coordinate + tolerance:
            return "FULLY_REMOVED"
        return "CROSSES_SECTION"
    thickness = float(specification.get("slab_thickness", 2.0))
    slab_low, slab_high = coordinate - thickness / 2.0, coordinate + thickness / 2.0
    overlaps = high >= slab_low - tolerance and low <= slab_high + tolerance
    if side == "CENTER_SLAB":
        if low >= slab_low + tolerance and high <= slab_high - tolerance:
            return "FULLY_KEPT"
        if not overlaps:
            return "FULLY_REMOVED"
        return "CROSSES_SECTION"
    if side == "OUTSIDE_SLAB":
        if not overlaps:
            return "FULLY_KEPT"
        if low >= slab_low + tolerance and high <= slab_high - tolerance:
            return "FULLY_REMOVED"
        return "CROSSES_SECTION"
    raise ValueError(f"unsupported keep_side {side}")

def global_bbox(parts):
    boxes = [shape_bbox(shape) for shape in parts.values()]
    if not boxes:
        raise ValueError("no parts for section global bbox")
    return {
        "xmin": min(item["xmin"] for item in boxes), "xmax": max(item["xmax"] for item in boxes),
        "ymin": min(item["ymin"] for item in boxes), "ymax": max(item["ymax"] for item in boxes),
        "zmin": min(item["zmin"] for item in boxes), "zmax": max(item["zmax"] for item in boxes),
    }

def global_cutter_bounds(assembly_bbox, specification):
    margin = float(specification.get("margin", 30.0))
    result = [
        assembly_bbox["xmin"] - margin, assembly_bbox["xmax"] + margin,
        assembly_bbox["ymin"] - margin, assembly_bbox["ymax"] + margin,
        assembly_bbox["zmin"] - margin, assembly_bbox["zmax"] + margin,
    ]
    lower, upper = AXIS_INDEX[specification["axis"]]
    coordinate = float(specification["coordinate"])
    side = specification["keep_side"]
    if side == "POSITIVE":
        result[lower] = max(coordinate, result[lower])
    elif side == "NEGATIVE":
        result[upper] = min(coordinate, result[upper])
    elif side == "CENTER_SLAB":
        thickness = float(specification.get("slab_thickness", 2.0))
        result[lower], result[upper] = coordinate - thickness / 2.0, coordinate + thickness / 2.0
    else:
        raise ValueError("OUTSIDE_SLAB requires two cutters and is not a single cutter")
    if any(result[index + 1] <= result[index] for index in (0, 2, 4)):
        return None
    return result

def build_global_section_cutter(assembly_bbox, specification):
    cutter_bounds = global_cutter_bounds(assembly_bbox, specification)
    if cutter_bounds is None:
        return None
    return box_from_bounds(cutter_bounds)

def build_global_section_cutters(assembly_bbox, specification):
    if specification["keep_side"] != "OUTSIDE_SLAB":
        cutter = build_global_section_cutter(assembly_bbox, specification)
        return [] if cutter is None else [cutter]
    thickness = float(specification.get("slab_thickness", 2.0))
    coordinate = float(specification["coordinate"])
    negative = dict(specification, keep_side="NEGATIVE", coordinate=coordinate - thickness / 2.0)
    positive = dict(specification, keep_side="POSITIVE", coordinate=coordinate + thickness / 2.0)
    return [
        cutter for cutter in (
            build_global_section_cutter(assembly_bbox, negative),
            build_global_section_cutter(assembly_bbox, positive),
        ) if cutter is not None
    ]

def resolve_touch_policy(bbox, specification):
    low_key, high_key = AXIS_BOUNDS[specification["axis"]]
    low, high = float(bbox[low_key]), float(bbox[high_key])
    coordinate = float(specification["coordinate"])
    if specification["keep_side"] == "POSITIVE":
        return "KEEP_SOURCE" if high > coordinate else "OMIT"
    if specification["keep_side"] == "NEGATIVE":
        return "KEEP_SOURCE" if low < coordinate else "OMIT"
    return "BOOLEAN"

def build_sectioned_parts(parts, registries, specifications=None, tolerance=0.01):
    specifications = specifications or SECTION_SPECS
    component_classes = {item["part_id"]: item["classification"] for item in registries["components"]}
    assembly_bbox = global_bbox(parts)
    all_sections, records = {}, []
    for specification in specifications:
        section_id = specification["section_id"]
        cutters = build_global_section_cutters(assembly_bbox, specification)
        section_parts = {}
        for part_id, shape in sorted(parts.items()):
            classification_name = component_classes.get(part_id, "FASTENER_PLACEHOLDER")
            if classification_name not in set(specification["included_component_classes"]) or classification_name in set(specification["excluded_component_classes"]):
                continue
            source_bbox = shape_bbox(shape)
            classification = classify_bbox_for_section(source_bbox, specification, tolerance)
            source_volume = shape_volume(shape)
            boolean_executed = False
            omitted = False
            result_shape = None
            error = ""
            status = "NOT_REQUIRED"
            try:
                if classification == "FULLY_KEPT":
                    result_shape = shape
                elif classification == "FULLY_REMOVED":
                    omitted = True
                elif classification == "TOUCHES_SECTION_WITHIN_TOLERANCE" and resolve_touch_policy(source_bbox, specification) == "KEEP_SOURCE":
                    result_shape = shape
                    status = "TOLERANCE_KEEP_SOURCE"
                elif classification == "TOUCHES_SECTION_WITHIN_TOLERANCE" and resolve_touch_policy(source_bbox, specification) == "OMIT":
                    omitted = True
                    status = "TOLERANCE_OMIT"
                elif not cutters:
                    omitted = True
                    status = "EMPTY_GLOBAL_HALF_SPACE"
                else:
                    boolean_executed = True
                    results = [
                        safe_boolean(shape, cutter, "intersect", f"section:{section_id}:{part_id}:{index}")
                        for index, cutter in enumerate(cutters)
                    ]
                    if len(results) == 1:
                        result_shape = results[0]
                    else:
                        from cad_primitives import union_all
                        result_shape = union_all(results)
                    if shape_volume(result_shape) <= 0.0:
                        result_shape = None
                        omitted = True
                        status = "EMPTY_RESULT_RECORDED"
                    else:
                        status = "BOOLEAN_OK"
                if result_shape is not None:
                    section_parts[f"{section_id}::{part_id}"] = result_shape
                records.append({
                    "section_id": section_id, "source_part_id": part_id,
                    "sectioned_part_id": f"{section_id}::{part_id}" if result_shape is not None else "",
                    "classification": classification, "source_volume_mm3": source_volume,
                    "result_volume_mm3": shape_volume(result_shape) if result_shape is not None else 0.0,
                    "source_bbox": source_bbox, "result_bbox": shape_bbox(result_shape) if result_shape is not None else {},
                    "boolean_executed": boolean_executed, "boolean_status": status,
                    "omitted": omitted, "error": error,
                })
            except Exception as exc:
                records.append({
                    "section_id": section_id, "source_part_id": part_id, "sectioned_part_id": "",
                    "classification": classification, "source_volume_mm3": source_volume,
                    "result_volume_mm3": 0.0, "source_bbox": source_bbox, "result_bbox": {},
                    "boolean_executed": boolean_executed, "boolean_status": "BOOLEAN_ERROR",
                    "omitted": True, "error": str(exc),
                })
        all_sections[section_id] = section_parts
    return all_sections, records

def layout_sectioned_review_parts(section_sets, spacing_mm=500.0):
    laid_out = {}
    for index, (section_id, parts) in enumerate(sorted(section_sets.items())):
        offset = (index * spacing_mm, 0.0, 0.0)
        for sectioned_id, shape in parts.items():
            laid_out[sectioned_id] = shape.translate(offset)
    return laid_out
