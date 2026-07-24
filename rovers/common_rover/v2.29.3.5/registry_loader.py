from __future__ import annotations
import json
from pathlib import Path

REGISTRY_FILES = {
    "components": "component_registry.json",
    "interfaces": "interface_registry.json",
    "attachments": "attachment_registry.json",
    "fasteners": "fastener_registry.json",
    "openings": "opening_registry.json",
    "containments": "containment_registry.json",
    "pairs": "pair_classification_registry.json",
    "print_manifest": "print_manifest.json",
    "plate_manifest": "plate_manifest.json",
}

def load_registries(root=None):
    base = Path(root) if root else Path(__file__).resolve().parent
    values = {}
    for key, filename in REGISTRY_FILES.items():
        values[key] = json.loads((base / filename).read_text(encoding="utf-8"))
    validate_registries(values)
    return values

def validate_registries(registries):
    expected = {
        "components": 1601,
        "interfaces": 12,
        "attachments": 38,
        "openings": 383,
        "containments": 12,
        "pairs": 29403,
    }
    for key, count in expected.items():
        if len(registries[key]) != count:
            raise ValueError(f"{key}: expected {count}, got {len(registries[key])}")
    fasteners = registries["fasteners"]
    if len(fasteners["groups"]) != 38 or len(fasteners["instances"]) != 152:
        raise ValueError("fastener registry must contain 38 groups and 152 instances")
    ids = [component["part_id"] for component in registries["components"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate component part_id")
    opening_ids = [opening["opening_id"] for opening in registries["openings"]]
    if len(opening_ids) != len(set(opening_ids)):
        raise ValueError("duplicate opening_id")
    pair_ids = [pair["pair_id"] for pair in registries["pairs"]]
    if len(pair_ids) != len(set(pair_ids)):
        raise ValueError("duplicate pair_id")
    allowed_opening_classes = {
        "FUNCTIONAL_SUBTRACTIVE_OPENING",
        "SERVICE_KEEP_OUT_ONLY",
        "REFERENCE_ONLY",
        "MEASUREMENT_HOLD_OPENING",
    }
    unknown = {
        opening.get("execution_class")
        for opening in registries["openings"]
        if opening.get("execution_class") not in allowed_opening_classes
    }
    if unknown:
        raise ValueError(f"unknown opening execution classes: {sorted(unknown)}")
    if any(pair["classification"] == "PROXY_OVERLAP_REQUIRES_REVIEW" for pair in registries["pairs"]):
        raise ValueError("review-overlap entries were not resolved")
    return {
        "component_count": len(ids),
        "fastener_instance_count": len(fasteners["instances"]),
        "opening_count": len(opening_ids),
        "pair_count": len(pair_ids),
    }

def component_index(registries):
    return {item["part_id"]: item for item in registries["components"]}

def opening_index(registries):
    return {item["opening_id"]: item for item in registries["openings"]}

def fastener_index(registries):
    return {item["fastener_instance_id"]: item for item in registries["fasteners"]["instances"]}
