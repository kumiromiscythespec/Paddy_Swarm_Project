from __future__ import annotations
from cad_covers import build_all_covers
from cad_placeholders import build_placeholder_parts
from cad_primitives import require_cadquery, shape_bbox, union_all
from cad_structural_parts import build_structural_parts
from registry_loader import component_index

PHYSICAL_CLASSES = {
    "STRUCTURAL", "MECHANICAL_PLACEHOLDER", "NONSTRUCTURAL_PROTECTIVE",
    "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER",
}

def build_part(part_id, params, registries):
    component = component_index(registries).get(part_id)
    if component is None:
        raise KeyError(part_id)
    cover_ids = {item["cover_component"] for item in registries["containments"]}
    if part_id in cover_ids:
        return build_all_covers(params, registries)[part_id]["solid"]
    if component["classification"] == "STRUCTURAL":
        return build_structural_parts(params, registries)[part_id]
    if component["classification"] in {"MECHANICAL_PLACEHOLDER", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"}:
        return build_placeholder_parts(params, registries)[part_id]
    if component["classification"] == "NONSTRUCTURAL_PROTECTIVE" and component["boxes"]:
        from cad_primitives import boxes_to_solid
        return boxes_to_solid(component["boxes"])
    raise ValueError(f"{part_id} is not a physical build target")

def build_raw_parts(params, registries):
    covers = build_all_covers(params, registries)
    structural = build_structural_parts(params, registries)
    placeholders = build_placeholder_parts(params, registries)
    parts = {}
    for component in registries["components"]:
        part_id = component["part_id"]
        classification = component["classification"]
        if classification not in PHYSICAL_CLASSES:
            continue
        if part_id in covers:
            parts[part_id] = covers[part_id]["solid"]
        elif classification == "STRUCTURAL":
            parts[part_id] = structural[part_id]
        elif classification in {"MECHANICAL_PLACEHOLDER", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"}:
            parts[part_id] = placeholders[part_id]
        elif component["boxes"]:
            from cad_primitives import boxes_to_solid
            parts[part_id] = boxes_to_solid(component["boxes"])
    return parts, {"covers": covers}

def build_all_parts(params, registries):
    from cad_openings import apply_functional_openings
    from cad_fasteners import apply_fastener_holes
    parts, records = build_raw_parts(params, registries)
    parts, opening_results = apply_functional_openings(parts, params, registries, True)
    parts, fastener_solids, hole_results, face_results = apply_fastener_holes(parts, params, registries)
    parts.update(fastener_solids)
    records.update({"openings": opening_results, "fastener_holes": hole_results, "face_bindings": face_results})
    return parts, records

def build_operational_assembly(parts, registries):
    cq = require_cadquery()
    assembly = cq.Assembly(name="V229_3_2_OPERATIONAL")
    classes = {item["part_id"]: item["classification"] for item in registries["components"]}
    for part_id, shape in sorted(parts.items()):
        if classes.get(part_id, "FASTENER_PLACEHOLDER") in PHYSICAL_CLASSES:
            assembly.add(shape, name=part_id)
    return assembly

def build_service_assembly(parts, registries):
    assembly = build_operational_assembly(parts, registries)
    roles = {"service_sweep", "tool_keepout", "fastener_tool", "fastener_removal", "fastener_insertion"}
    for component in registries["components"]:
        if component["role"] in roles and component["boxes"]:
            from cad_primitives import boxes_to_solid
            assembly.add(boxes_to_solid(component["boxes"]), name=component["part_id"])
    return assembly

def compute_assembly_envelope(parts, registries, service=False):
    index = component_index(registries)
    excluded = {"service_sweep", "tool_keepout", "fastener_tool", "fastener_removal", "fastener_insertion", "reference_datum"}
    shapes = []
    for part_id, shape in parts.items():
        role = index.get(part_id, {}).get("role", "bolt_head_washer_nut")
        if service or role not in excluded:
            shapes.append(shape)
    if not shapes:
        raise ValueError("no shapes selected for envelope")
    return shape_bbox(union_all(shapes))
