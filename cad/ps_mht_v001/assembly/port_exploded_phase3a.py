"""Exploded Phase 3A planting-port assembly."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.assembly.planting_module_ports_phase3a import (
    port_assembly_components,
)


def build_port_exploded_phase3a() -> cq.Workplane:
    components = port_assembly_components(exploded_gap=8.0)
    return cq.Workplane("XY").newObject(
        [cq.Compound.makeCompound([component.model.val() for component in components])]
    )


def exploded_component_count() -> int:
    return len(port_assembly_components(exploded_gap=8.0))

