from __future__ import annotations
from cad_primitives import boxes_to_solid
from registry_loader import component_index

PLACEHOLDER_CLASSES = {"MECHANICAL_PLACEHOLDER", "SEALED_DRY_COMPONENT", "FASTENER_PLACEHOLDER"}

def build_placeholder(part_id, params, registries):
    component = component_index(registries).get(part_id)
    if component is None:
        raise KeyError(part_id)
    if component["classification"] not in PLACEHOLDER_CLASSES:
        raise ValueError(f"{part_id} is not a purchased or mechanical placeholder")
    if not component["boxes"]:
        raise ValueError(f"{part_id} has no registry geometry")
    return boxes_to_solid(component["boxes"])

def build_placeholder_parts(params, registries):
    return {
        component["part_id"]: build_placeholder(component["part_id"], params, registries)
        for component in registries["components"]
        if component["classification"] in PLACEHOLDER_CLASSES
    }
