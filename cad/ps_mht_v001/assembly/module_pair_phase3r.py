"""Two-stage Phase 3R module-interface references at 0/60/30 degrees."""

from __future__ import annotations

import cadquery as cq

from ps_mht_v001.assembly.module_interface_phase3r import (
    interface_components_phase3r,
)
from ps_mht_v001.parameters import module_wall_thickness, tower_body_diameter
from ps_mht_v001.tower_module.module_alignment_ring_phase3r import (
    alignment_interference_volume,
)


MODULE_PAIR_SOLID_COUNT = 11


def _short_module_body(height: float = 30.0) -> cq.Workplane:
    outer_radius = 0.5 * tower_body_diameter
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(outer_radius - module_wall_thickness)
        .extrude(height)
    )


def build_module_pair_phase3r(rotation_deg: float) -> cq.Workplane:
    lower = _short_module_body()
    upper = _short_module_body().translate((0.0, 0.0, 55.0))
    interface = [
        component.model.translate((0.0, 0.0, 30.0))
        for component in interface_components_phase3r(rotation_deg)
    ]
    shapes = [lower.val(), upper.val(), *(model.val() for model in interface)]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(shapes)])


def module_pair_alignment_interference_phase3r(rotation_deg: float) -> float:
    return alignment_interference_volume(rotation_deg)


def build_module_pair_0deg_phase3r() -> cq.Workplane:
    return build_module_pair_phase3r(0.0)


def build_module_pair_60deg_phase3r() -> cq.Workplane:
    return build_module_pair_phase3r(60.0)


def build_module_pair_30deg_misassembly_phase3r() -> cq.Workplane:
    return build_module_pair_phase3r(30.0)
