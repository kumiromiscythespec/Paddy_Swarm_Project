from __future__ import annotations

from copy import deepcopy
from typing import Any


HEAVY_COMPONENTS = (
    "FLOAT",
    "CBOX",
    "BBOX",
    "BATTERY_CASSETTE",
)


def _node(
    name: str,
    material: str,
    role: str,
    *,
    source: str,
    status: str = "DEFINED",
) -> dict[str, str]:
    return {
        "name": name,
        "material": material,
        "role": role,
        "authority_source": source,
        "status": status,
    }


def build_load_paths() -> list[dict[str, Any]]:
    authority = "rovers/common_rover/v2.29.3.9.1"
    lane = "cad/common_rover/v2_29_3_9_1_assembly_interface_v0_1"
    return [
        {
            "component": "FLOAT",
            "status": "CONCEPT_DEFINED",
            "nodes": [
                _node("FLOAT MODULE", "MIXED", "APPLIED LOAD", source=lane),
                _node(
                    "SLIDE RECEIVER",
                    "PRINTED",
                    "POSITIONING + SACRIFICIAL BEARING",
                    source=lane,
                ),
                _node(
                    "REMOVABLE PIN",
                    "METAL",
                    "PRIMARY SEPARATION LOCK",
                    source=lane,
                ),
                _node(
                    "LOWER ADAPTER",
                    "PRINTED + METAL",
                    "BEARING TRANSFER TO T-NUT",
                    source=f"{authority}/slot_zone_authority.json",
                ),
                _node(
                    "T-NUT / METAL BOLT",
                    "METAL",
                    "PRIMARY STRUCTURAL FASTENER",
                    source=f"{authority}/slot_cross_registry_mapping.json",
                ),
                _node(
                    "FPB RAIL BOTTOM_SLOT",
                    "ALUMINUM",
                    "PRIMARY FRAME",
                    source=f"{authority}/body_frame_authority.json",
                ),
            ],
            "connector_structural": False,
            "independent_of": ["THUMB LATCH"],
            "unresolved": [
                "Printed bearing strength and metal pin specification remain HOLD"
            ],
        },
        {
            "component": "CBOX",
            "status": "CONCEPT_DEFINED_WITH_HOLD",
            "nodes": [
                _node(
                    "CBOX",
                    "ASSEMBLY",
                    "APPLIED MASS + OPERATION LOAD",
                    source=f"{authority}/fixed_body_dimension_authority.json",
                ),
                _node(
                    "PRINTED CBOX SADDLE",
                    "PRINTED",
                    "POSITIONING + SACRIFICIAL WEAR",
                    source=lane,
                ),
                _node(
                    "METAL CLAMP",
                    "METAL",
                    "PRIMARY ANTI-SEPARATION",
                    source=lane,
                    status="HOLD_SPECIFICATION",
                ),
                _node(
                    "LOWER-FRAME CRADLE",
                    "METAL",
                    "PRIMARY STRUCTURAL MEMBER",
                    source=lane,
                    status="HOLD_ATTACHMENT_AUTHORITY",
                ),
                _node(
                    "VALIDATED COMMON STRUCTURAL FRAME",
                    "ALUMINUM / METAL",
                    "PRIMARY FRAME",
                    source=f"{authority}/body_frame_authority.json",
                    status="HOLD_CRADLE_CONNECTION",
                ),
            ],
            "connector_structural": False,
            "independent_of": ["SNAP HOOK", "THUMB LATCH"],
            "unresolved": [
                "Cradle-to-authority connection remains HOLD; no manufacturing shape"
            ],
        },
        {
            "component": "BBOX",
            "status": "HOLD_REAR_SUPPORT_AUTHORITY",
            "nodes": [
                _node(
                    "BBOX",
                    "ASSEMBLY",
                    "APPLIED MASS + BATTERY LOAD",
                    source=f"{authority}/fixed_body_dimension_authority.json",
                ),
                _node(
                    "PRINTED BBOX SADDLE",
                    "PRINTED",
                    "POSITIONING + SACRIFICIAL WEAR",
                    source=lane,
                ),
                _node(
                    "METAL CLAMP",
                    "METAL",
                    "PRIMARY ANTI-SEPARATION",
                    source=lane,
                    status="HOLD_SPECIFICATION",
                ),
                _node(
                    "INDEPENDENT REAR SUPPORT BRIDGE",
                    "METAL",
                    "PRIMARY STRUCTURAL MEMBER",
                    source=lane,
                    status="HOLD_ATTACHMENT_AUTHORITY",
                ),
                _node(
                    "VALIDATED LOWER / COMMON FRAME",
                    "ALUMINUM / METAL",
                    "PRIMARY FRAME",
                    source=f"{authority}/body_frame_authority.json",
                    status="HOLD_REAR_EXTENSION",
                ),
            ],
            "connector_structural": False,
            "independent_of": [
                "CBOX VERTICAL SUPPORT",
                "ELECTRICAL CONNECTOR",
                "THUMB LATCH",
            ],
            "unresolved": [
                "Rear support hardpoints, section, and stiffness are authority HOLD"
            ],
        },
        {
            "component": "BATTERY_CASSETTE",
            "status": "SEQUENCE_RESERVED_WITH_HOLD",
            "nodes": [
                _node(
                    "BATTERY CASSETTE",
                    "ASSEMBLY",
                    "APPLIED MASS",
                    source=f"{authority}/fixed_body_dimension_authority.json",
                ),
                _node(
                    "MECHANICAL SEAT + GUIDE",
                    "PRINTED + METAL",
                    "POSITIONING / BEARING",
                    source=lane,
                    status="HOLD_GEOMETRY",
                ),
                _node(
                    "PRIMARY MECHANICAL LATCH",
                    "METAL",
                    "PRIMARY ANTI-SEPARATION",
                    source=lane,
                    status="HOLD_GEOMETRY",
                ),
                _node(
                    "SAFETY LATCH",
                    "METAL OR PRINTED SECONDARY",
                    "SECONDARY RETENTION",
                    source=lane,
                    status="HOLD_GEOMETRY",
                ),
                _node(
                    "BBOX FRAME",
                    "METAL / STRUCTURAL",
                    "PRIMARY FRAME",
                    source=f"{authority}/hardware_envelope_registry.json",
                    status="HOLD_HARDPOINT",
                ),
            ],
            "connector_structural": False,
            "independent_of": ["ELECTRICAL CONNECTOR"],
            "unresolved": [
                "Seat, latch, sensor, and BBOX hardpoints remain HOLD"
            ],
        },
    ]


def validate_load_paths(paths: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    by_component: dict[str, list[dict[str, Any]]] = {}
    for path in paths:
        component = str(path.get("component", ""))
        by_component.setdefault(component, []).append(path)
    for component in HEAVY_COMPONENTS:
        records = by_component.get(component, [])
        if len(records) != 1:
            blockers.append(f"LOAD_PATH_COUNT:{component}:{len(records)}")
            continue
        record = records[0]
        nodes = record.get("nodes", [])
        roles = " ".join(str(node.get("role", "")) for node in nodes)
        materials = " ".join(
            str(node.get("material", "")) for node in nodes
        )
        if "PRIMARY" not in roles or "METAL" not in materials:
            blockers.append(f"PRIMARY_METAL_LOAD_PATH_MISSING:{component}")
        if not all(node.get("authority_source") for node in nodes):
            blockers.append(f"LOAD_PATH_SOURCE_MISSING:{component}")
        if record.get("connector_structural") is not False:
            blockers.append(f"CONNECTOR_STRUCTURAL_LOAD:{component}")
    bbox = by_component.get("BBOX", [{}])[0]
    bbox_nodes = " ".join(
        str(node.get("name", "")) for node in bbox.get("nodes", [])
    )
    if "INDEPENDENT REAR SUPPORT BRIDGE" not in bbox_nodes:
        blockers.append("BBOX_CANTILEVERED_FROM_CBOX")
    return sorted(set(blockers))


def clone_load_paths(paths: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return deepcopy(paths)
