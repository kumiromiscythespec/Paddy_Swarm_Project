from __future__ import annotations
from cad_primitives import boxes_to_solid
from registry_loader import component_index

STRUCTURAL_CLASSES = {"STRUCTURAL"}

def build_structural_part(part_id, params, registries):
    component = component_index(registries).get(part_id)
    if component is None:
        raise KeyError(part_id)
    if component["classification"] not in STRUCTURAL_CLASSES:
        raise ValueError(f"{part_id} is not structural")
    if not component["boxes"]:
        raise ValueError(f"{part_id} has no registry geometry")
    return boxes_to_solid(component["boxes"])

def build_structural_parts(params, registries):
    return {
        component["part_id"]: build_structural_part(component["part_id"], params, registries)
        for component in registries["components"]
        if component["classification"] in STRUCTURAL_CLASSES
    }
